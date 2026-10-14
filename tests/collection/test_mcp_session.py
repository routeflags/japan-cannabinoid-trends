"""The live MCP session must carry requests and return the server's answer.

No test may start the real collector: the live path is exercised against a stub
process that speaks the same newline-delimited JSON-RPC, so the framing, the
verbatim result and the failure modes are covered without a network call.  The
pipeline's contract with a live session is covered separately (adapter +
`build_adapter(live=...)`), which is also where the "no session, refuse" rule
lives.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from collection.adapters import (
    AdapterUnavailable,
    get_live_session,
    start_live_session,
)
from collection.adapters.google_trends.adapter import build_adapter
from collection.adapters.google_trends.mcp_session import McpSessionError, McpStdioSession

#: A stub MCP server: banner line, initialize, tools/list, tools/call.
STUB = r'''
import json, sys

print("stub server starting", flush=True)  # not JSON: must be skipped

def send(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    request = json.loads(line)
    method = request.get("method")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": request["id"], "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "stub-trends", "version": "9.9.9"},
        }})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": request["id"], "result": {
            "tools": [{"name": "interest_over_time"}],
        }})
    elif method == "tools/call":
        params = request["params"]
        send({"jsonrpc": "2.0", "id": request["id"], "result": {
            "content": [{"type": "text", "text": "Interest over time for: " + params["arguments"]["terms"][0]}],
            "isError": False,
            "echo": params["arguments"],
        }})

pytest_should_not_get_here = None
'''


def _stub_session(**kwargs) -> McpStdioSession:
    return McpStdioSession(command=[sys.executable, "-u", "-c", STUB], **kwargs)


def test_session_initializes_and_calls_a_tool() -> None:
    with _stub_session() as session:
        assert session.server_info == {"name": "stub-trends", "version": "9.9.9"}
        assert [tool["name"] for tool in session.list_tools()] == ["interest_over_time"]
        result = session.call(
            "interest_over_time", {"terms": ["THCH"], "geo": "JP", "timeframe": "today 5-y"}
        )

    # Verbatim: the pipeline stores exactly this document as the raw payload.
    assert result["isError"] is False
    assert result["echo"] == {"terms": ["THCH"], "geo": "JP", "timeframe": "today 5-y"}
    assert "THCH" in result["content"][0]["text"]


def test_describe_records_the_collector_and_transport() -> None:
    with _stub_session() as session:
        description = session.describe()

    assert description["collection_mode"] == "live"
    assert description["transport"] == "mcp_stdio"
    assert description["server_version"] == "0.1.1"


def test_a_server_that_dies_is_an_error_not_an_empty_result() -> None:
    session = McpStdioSession(command=[sys.executable, "-c", "import sys; sys.stdin.readline()"])

    with pytest.raises(McpSessionError):
        session.start()


def test_a_command_that_cannot_start_is_an_error() -> None:
    session = McpStdioSession(command=["definitely-not-a-real-binary-xyz"])

    with pytest.raises(McpSessionError):
        session.start()


def test_live_sessions_are_opt_in_per_source() -> None:
    assert isinstance(get_live_session("google-trends"), McpStdioSession)
    with pytest.raises(AdapterUnavailable):
        get_live_session("x")


def test_no_session_means_a_recorded_failure_not_data() -> None:
    """The default stays fail-closed: without a session the call is refused.

    The refusal is *failure evidence* recorded in the result (status failed,
    zero returned), never zero observations (AGENTS.md).
    """

    adapter = build_adapter(fixture=None, capabilities={})
    result = adapter.collect(
        {
            "query": {"text": "THCH", "geo": "JP", "timeframe": "today 5-y"},
            "window": {
                "start": "2021-10-10T00:00:00Z",
                "end_exclusive": "2026-10-12T00:00:00Z",
            },
        }
    )

    assert result.status == "failed"
    assert result.returned_count == 0
    assert result.completeness == "missing"
    assert result.observations == []
    assert [error["code"] for error in result.errors] == ["TRANSPORT_ERROR"]
    assert "no MCP session is bound" in str(result.raw)


def test_a_live_session_is_used_when_the_caller_supplies_one() -> None:
    """``build_adapter(live=...)`` is the only way a call reaches a server."""

    calls = []

    def _call(tool, params):
        calls.append((tool, params))
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Interest over time for: THCH\n"
                        "Geo: JP | Timeframe: today 5-y\n\n"
                        "Date\tTHCH\n"
                        "Jan 4 – 10, 2026\t50\n"
                    ),
                }
            ]
        }

    adapter = build_adapter(fixture=None, capabilities={}, live=_call)
    result = adapter.collect(
        {
            "query": {"text": "THCH", "geo": "JP", "timeframe": "today 5-y"},
            "window": {
                "start": "2021-10-10T00:00:00Z",
                "end_exclusive": "2026-10-12T00:00:00Z",
            },
        }
    )

    assert calls == [
        ("interest_over_time", {"terms": ["THCH"], "geo": "JP", "timeframe": "today 5-y"})
    ]
    assert result.status == "success"
    assert result.observations == [{"date": "2026-01-04", "value": 50}]
    assert result.payload_schema_id == "google-trends-mcp-tool-result-v1"
