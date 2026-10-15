from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from collection.adapters.google_trends.live_guard import (
    CLASS_DEPENDENCY,
    CLASS_INVALID_CONFIG,
    CLASS_NETWORK,
    CLASS_SUCCESS,
    CLASS_TIMEOUT,
    classify_process,
    probe_mcp_tools,
    run_bounded_command,
)


STUB_MCP = r'''
import json
import sys

def send(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": request["id"], "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "stub-google-trends", "version": "0.0.0"},
        }})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": request["id"], "result": {
            "tools": [{"name": "interest_over_time"}],
        }})
'''


def test_probe_lists_tools_and_writes_reviewable_logs_without_raw_write(tmp_path: Path) -> None:
    result = probe_mcp_tools(
        [sys.executable, "-u", "-c", STUB_MCP],
        timeout_seconds=2,
        log_root=tmp_path / ".staging" / "tooling_logs",
        run_id="probe-success",
    )

    assert result.classification == CLASS_SUCCESS
    assert result.detail
    assert result.detail["tools"] == [{"name": "interest_over_time"}]
    assert Path(result.report_path).is_file()
    assert Path(result.stdout_log).is_file()
    assert Path(result.stderr_log).is_file()

    report = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
    assert report["classification"] == CLASS_SUCCESS
    assert not (tmp_path / "datasets").exists()


def test_hanging_probe_is_killed_and_classified_as_timeout(tmp_path: Path) -> None:
    started = time.monotonic()
    result = probe_mcp_tools(
        [sys.executable, "-u", "-c", "import time; time.sleep(60)"],
        timeout_seconds=0.2,
        log_root=tmp_path / ".staging" / "tooling_logs",
        run_id="probe-timeout",
    )

    assert time.monotonic() - started < 5
    assert result.classification == CLASS_TIMEOUT
    assert result.timed_out is True
    assert "timeout" in (result.message or "").lower()
    assert not (tmp_path / "datasets" / "study" / "data" / "raw").exists()


def test_probe_that_exits_before_tools_list_is_not_success(tmp_path: Path) -> None:
    result = probe_mcp_tools(
        [sys.executable, "-c", "print('not json')"],
        timeout_seconds=2,
        log_root=tmp_path / ".staging" / "tooling_logs",
        run_id="probe-protocol-failure",
    )

    assert result.classification != CLASS_SUCCESS
    assert "tools/list" in (result.message or "")


def test_bounded_command_timeout_kills_child_and_keeps_logs(tmp_path: Path) -> None:
    result = run_bounded_command(
        [sys.executable, "-c", "import time; print('started', flush=True); time.sleep(60)"],
        timeout_seconds=0.2,
        log_root=tmp_path / ".staging" / "tooling_logs",
        run_id="command-timeout",
    )

    assert result.classification == CLASS_TIMEOUT
    assert result.timed_out is True
    assert "started" in Path(result.stdout_log).read_text(encoding="utf-8")


def test_failure_classification_examples() -> None:
    assert (
        classify_process(
            exit_code=None,
            timed_out=False,
            stdout="",
            stderr="FileNotFoundError: [Errno 2] No such file or directory: 'npx'",
        )
        == CLASS_DEPENDENCY
    )
    assert (
        classify_process(
            exit_code=1,
            timed_out=False,
            stdout="",
            stderr="npm ERR! network ETIMEDOUT while fetching package",
        )
        == CLASS_NETWORK
    )
    assert (
        classify_process(
            exit_code=2,
            timed_out=False,
            stdout="",
            stderr="usage: collect --plan PLAN\nmissing required option",
        )
        == CLASS_INVALID_CONFIG
    )
