"""Google Trends adapter (MCP transport), G1 vertical slice.

Contract: ``collection.core.contracts`` / ``docs/specs/collection-pipeline.md``.

Collection means (registry: ``config/collectors.json`` -> ``google-trends-mcp``):

- ``google-trends-mcp`` (npm, MIT, no API key) through an MCP session's
  ``interest_over_time`` tool; recorded response shape:
  ``{keyword, geo, timeframe, collected_at, data:[{date, value}]}``
  (weekly buckets, Sunday start; value = relative index 0-100).

Transports:

- :class:`RecordedResponseTransport` - offline replay of a recorded fixture,
  used by contract tests and the staged demo.  It refuses to answer a request
  the fixture does not describe (no fabricated responses);
- :class:`SessionMcpTransport` - the live path.  It only works when an
  approved MCP session callable is injected; this repository does not execute
  live collection on its own (cost / rate limits / credentials).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from collection.core.contracts import CollectionResult, TransportError

__all__ = [
    "GoogleTrendsMcpAdapter",
    "RecordedResponseTransport",
    "SessionMcpTransport",
    "build_adapter",
]

TOOL_INTEREST_OVER_TIME = "interest_over_time"

#: Timeframes observed in the 29 recorded runs and documented in the
#: research-google-trends skill.  Unknown timeframes are refused (fail
#: closed; promoting one requires a capability verification).
SUPPORTED_TIMEFRAMES = (
    "today 1-m",
    "today 3-m",
    "today 12-m",
    "today 5-y",
)

_GEO_PATTERN = re.compile(r"^[A-Z]{2}$")


class RecordedResponseTransport:
    """Replays one recorded MCP tool response (offline).

    The fixture carries the request it answers; a mismatching request is
    refused so a replay can never masquerade as a different collection.
    """

    mode = "recorded_replay"

    def __init__(self, fixture_path):
        self.fixture_path = Path(fixture_path)

    def describe(self) -> dict:
        return {
            "collection_mode": self.mode,
            "fixture": str(self.fixture_path),
        }

    def call(self, tool: str, params: dict):
        try:
            fixture = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransportError(
                f"recorded fixture cannot be read: {error.__class__.__name__}"
            ) from error
        request = fixture.get("request")
        if (
            not isinstance(request, dict)
            or request.get("tool") != tool
            or request.get("params") != params
        ):
            raise TransportError(
                "recorded fixture describes a different request; refusing to "
                "replay unrelated data"
            )
        return fixture.get("response")


class SessionMcpTransport:
    """Live MCP transport bound to an approved session callable.

    ``call`` must be the MCP session's tool invocation (supplied by the agent
    session that holds the ``google-trends`` MCP server).  Without it, the
    transport refuses: it never fabricates a response and this repository
    does not run live collection automatically.
    """

    mode = "live"

    def __init__(self, call=None):
        self._call = call

    def describe(self) -> dict:
        return {"collection_mode": self.mode, "transport": "mcp"}

    def call(self, tool: str, params: dict):
        if self._call is None:
            raise TransportError(
                "no MCP session is bound; live collection must run through an "
                "approved MCP session (not executed by this environment)"
            )
        return self._call(tool, params)


class GoogleTrendsMcpAdapter:
    """Adapter for the recorded ``google-trends-mcp`` response shape.

    ``capabilities`` are supplied from the collector registry entry by the
    caller: the registry is the record of truth and the adapter only reports
    what was verified (it never upgrades ``unknown``).
    """

    adapter_id = "google-trends-mcp@1"
    source_id = "google-trends"
    collector_id = "google-trends-mcp"
    version = "0.1.1"
    payload_schema_id = "google-trends-interest-over-time-v1"

    def __init__(self, transport, capabilities=None):
        self._transport = transport
        self._capabilities = dict(capabilities or {})

    def capabilities(self) -> dict:
        return dict(self._capabilities)

    def validate_plan(self, plan: dict) -> list:
        violations: list[str] = []
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        text = query.get("text")
        if not isinstance(text, str) or not text:
            violations.append("query.text is required")
        geo = query.get("geo", "")
        if geo and (not isinstance(geo, str) or not _GEO_PATTERN.fullmatch(geo)):
            violations.append(
                "query.geo must be an ISO 3166-1 alpha-2 code (or empty for "
                "worldwide)"
            )
        timeframe = query.get("timeframe")
        if timeframe not in SUPPORTED_TIMEFRAMES:
            violations.append(
                "query.timeframe must be one of the verified timeframes: "
                + ", ".join(SUPPORTED_TIMEFRAMES)
            )
        window = plan.get("window")
        if (
            not isinstance(window, dict)
            or not window.get("start")
            or not window.get("end_exclusive")
        ):
            violations.append("window.start and window.end_exclusive are required")
        return violations

    def _request_params(self, plan: dict) -> dict:
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        return {
            "terms": [query.get("text")],
            "geo": query.get("geo", ""),
            "timeframe": query.get("timeframe"),
        }

    def collect(self, plan: dict) -> CollectionResult:
        params = self._request_params(plan)
        try:
            raw = self._transport.call(TOOL_INTEREST_OVER_TIME, params)
        except TransportError as error:
            # A failed collection is recorded as failure evidence - it is
            # never converted into zero observations (AGENTS.md).
            return CollectionResult(
                raw={
                    "tool": TOOL_INTEREST_OVER_TIME,
                    "request": params,
                    "error": {"message": str(error)},
                },
                payload_schema_id=self.payload_schema_id,
                status="failed",
                errors=[{"code": "TRANSPORT_ERROR", "message": str(error)}],
                returned_count=0,
                pagination_exhausted=None,
                completeness="missing",
                submitted_parameters={
                    "tool": TOOL_INTEREST_OVER_TIME,
                    **params,
                },
            )

        observations = self.extract_observations(raw)
        return CollectionResult(
            raw=raw,
            payload_schema_id=self.payload_schema_id,
            status="success",
            returned_count=len(observations),
            errors=[],
            # interest_over_time returns the whole series in one response;
            # there is no second page to fetch.
            pagination_exhausted=True,
            completeness="complete",
            observations=observations,
            submitted_parameters={"tool": TOOL_INTEREST_OVER_TIME, **params},
            temporal={
                "granularity": "week",
                "week_start": "sunday",
                "collector_window_type": "relative_duration",
                "exact_window_match": False,
                "boundary_semantics": (
                    "relative timeframe resolved by the collector at request "
                    "time; weekly buckets (Sunday start) label the series; "
                    "observed range "
                    + _observed_range_label(observations)
                ),
                "observed_min_timestamp": None,
                "observed_max_timestamp": None,
            },
        )

    def extract_observations(self, raw) -> list:
        if not isinstance(raw, dict):
            return []
        data = raw.get("data")
        if not isinstance(data, list):
            return []
        observations = []
        for point in data:
            if (
                isinstance(point, dict)
                and isinstance(point.get("date"), str)
                and isinstance(point.get("value"), int)
            ):
                observations.append({"date": point["date"], "value": point["value"]})
        return observations

    def describe_execution(self) -> dict:
        description = {
            "tool": TOOL_INTEREST_OVER_TIME,
            "package": "google-trends-mcp",
            "version": self.version,
        }
        description.update(self._transport.describe())
        return description


def _observed_range_label(observations) -> str:
    dates = [point["date"] for point in observations if isinstance(point.get("date"), str)]
    if not dates:
        return "empty (no data points returned)"
    return f"{dates[0]}..{dates[-1]}"


def build_adapter(fixture=None, capabilities=None) -> GoogleTrendsMcpAdapter:
    """Build the adapter for the collection CLI.

    Without a fixture no live session is available in this repository, so the
    adapter is built on :class:`SessionMcpTransport` with no callable: any
    ``collect`` attempt fails closed and is recorded as a failed run (never
    fabricated data).  Tests and the demo pass ``fixture=`` to use the
    recorded replay transport.
    """
    if fixture is not None:
        transport = RecordedResponseTransport(fixture)
    else:
        transport = SessionMcpTransport()
    return GoogleTrendsMcpAdapter(transport, capabilities=capabilities)
