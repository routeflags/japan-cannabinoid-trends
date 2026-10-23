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
from validation.windows import RELATIVE_TIMEFRAME_MODELS, format_datetime

__all__ = [
    "GoogleTrendsMcpAdapter",
    "RecordedResponseTransport",
    "SessionMcpTransport",
    "build_adapter",
    "term_slug",
]

TOOL_INTEREST_OVER_TIME = "interest_over_time"
#: The multi-term tool. ``compare_terms`` measures several terms on one shared
#: scale, which is the only measurement the repository can compare compounds
#: with (a single-term series is normalized to its own peak).
TOOL_COMPARE_TERMS = "compare_terms"
#: Google Trends accepts at most five terms in one comparison request.
MAX_COMPARE_TERMS = 5

#: Timeframes observed in the recorded runs and documented in the
#: research-google-trends skill.  Derived from the shared G3 timeframe models
#: (``validation.windows``) so the compiler and the adapter allow-list can
#: never drift.  Unknown timeframes are refused (fail closed).
SUPPORTED_TIMEFRAMES = tuple(RELATIVE_TIMEFRAME_MODELS)

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
    #: The payload is the verbatim MCP tool result (preserved as produced); the
    #: parsed weekly series is written beside it by :meth:`derived_artifacts`.
    payload_schema_id = "google-trends-mcp-tool-result-v1"
    #: Schema of the parsed series (the shape every recorded run uses).
    series_schema_id = "google-trends-interest-over-time-v1"
    #: Schema of a shared-scale comparison document (multi-term run).
    comparison_schema_id = "google-trends-comparison-v1"

    def __init__(self, transport, capabilities=None):
        self._transport = transport
        self._capabilities = dict(capabilities or {})
        #: tool this instance last requested (set by ``collect``)
        self._tool = TOOL_INTEREST_OVER_TIME

    def capabilities(self) -> dict:
        return dict(self._capabilities)

    def _plan_terms(self, plan: dict) -> list:
        """The terms a plan asks for: ``query.terms`` (comparison) or
        ``query.text`` (single term)."""

        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        terms = query.get("terms")
        if isinstance(terms, list):
            return [term for term in terms if isinstance(term, str) and term]
        text = query.get("text")
        return [text] if isinstance(text, str) and text else []

    def validate_plan(self, plan: dict) -> list:
        violations: list[str] = []
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        terms = self._plan_terms(plan)
        if not terms:
            violations.append("query.text (or query.terms) is required")
        if isinstance(query.get("terms"), list) and not 2 <= len(terms) <= MAX_COMPARE_TERMS:
            violations.append(
                f"query.terms must name 2..{MAX_COMPARE_TERMS} terms "
                f"(got {len(terms)})"
            )
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
            "terms": self._plan_terms(plan),
            "geo": query.get("geo", ""),
            "timeframe": query.get("timeframe"),
        }

    def collect(self, plan: dict) -> CollectionResult:
        params = self._request_params(plan)
        self._tool = (
            TOOL_COMPARE_TERMS if len(params["terms"]) > 1 else TOOL_INTEREST_OVER_TIME
        )
        try:
            raw = self._transport.call(self._tool, params)
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

        try:
            observations = self.extract_observations(raw)
        except ValueError as error:
            # The server answered, but the answer is not a series the
            # documented rules cover: Google Trends reports a term below its
            # volume threshold as an error result / plain sentence rather
            # than an empty table.  The verbatim response is kept as the
            # payload - what the server said is the only evidence of *why*
            # there is no series, and a discarded answer cannot be re-read.
            # It is still a failed collection: missing, never zero
            # observations (AGENTS.md).
            reason_codes = list(getattr(error, "codes", []) or [])
            # ``no_data`` means the source answered "below the volume
            # threshold" - a different state from a broken capture, so it gets
            # its own code (AGENTS.md: missing is not collection_failed).
            code = "NO_DATA" if "no_data" in reason_codes else "PARSE_FAILED"
            return CollectionResult(
                raw=raw,
                payload_schema_id=self.payload_schema_id,
                status="failed",
                errors=[
                    {
                        "code": code,
                        "message": str(error) or error.__class__.__name__,
                        "reason_codes": reason_codes,
                    }
                ],
                returned_count=0,
                pagination_exhausted=None,
                completeness="missing",
                submitted_parameters={
                    "tool": self._tool,
                    **params,
                },
            )
        observed_min, observed_max = _observed_bounds(observations)
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
            submitted_parameters={"tool": self._tool, **params},
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
                # G3 P5: the observed bounds are the bucket labels present in
                # the response (date-precision, UTC); a label range is not a
                # completeness claim for the requested window.
                "observed_min_timestamp": observed_min,
                "observed_max_timestamp": observed_max,
            },
        )

    def extract_observations(self, raw) -> list:
        """Parse the source response into observations.

        Single-term responses become ``{date, value}`` points; a comparison
        response becomes ``{date, <term>: value, ...}`` rows on one shared
        scale.  Two shapes reach this method per tool:

        - the **verbatim MCP tool result** (``content`` text table) - what a
          live session returns and what the raw artifact keeps;
        - the **recorded series document** (``data``) - the replay fixture and
          the derived artifact.

        The text table is parsed by the instrument's verified parser
        (``boundary.parse_tool_result`` / ``parse_comparison_tool_result``,
        spec §4.4); the import is local because that module imports this one.
        """

        if not isinstance(raw, dict):
            return []
        data = raw.get("data")
        if isinstance(data, list):
            observations = []
            for point in data:
                if (
                    isinstance(point, dict)
                    and isinstance(point.get("date"), str)
                    and isinstance(point.get("value"), int)
                ):
                    observations.append({"date": point["date"], "value": point["value"]})
            return observations
        if "content" in raw:
            from collection.adapters.google_trends.boundary import (
                parse_comparison_tool_result,
                parse_tool_result,
            )

            if self._tool == TOOL_COMPARE_TERMS:
                parsed = parse_comparison_tool_result(raw)
                return [
                    {"date": point.date, **point.values} for point in parsed.points
                ]
            parsed = parse_tool_result(raw)
            return [{"date": point.date, "value": point.value} for point in parsed.points]
        return []

    def describe_execution(self) -> dict:
        description = {
            "tool": self._tool,
            "package": "google-trends-mcp",
            "version": self.version,
        }
        description.update(self._transport.describe())
        return description

    # -- optional pipeline hook (see collection/core/contracts.py) -----------

    def derived_artifacts(self, plan: dict, result, observations, collected_at) -> list:
        """The parsed weekly series, written beside the verbatim payload.

        The raw artifact stays the server's response; this file is the same
        run's readable series (``records_<term>.json``), so a consumer (the
        publication summary, a reader, a reviewer) does not have to re-parse
        the tool result.  Nothing is invented: it holds exactly the
        observations this adapter already extracted.
        """

        points = [point for point in (observations or []) if isinstance(point, dict)]
        if not points:
            return []
        query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
        if len(self._plan_terms(plan)) > 1:
            # A comparison run's readable form is the shared-scale document
            # (``google-trends-comparison-v1``): the terms, their average
            # scores and the weekly rows, exactly as the tool printed them.
            document = {
                "terms": self._plan_terms(plan),
                "geo": query.get("geo", ""),
                "timeframe": query.get("timeframe"),
                "collected_at": _iso_moment(collected_at),
                "average_interest": _comparison_averages(result.raw, self._tool),
                "data": [dict(point) for point in points],
            }
            slug = "-".join(term_slug(term) for term in self._plan_terms(plan))
            return [
                {
                    "path": f"comparison_{slug}.json",
                    "artifact_type": "comparison",
                    "format": "json",
                    "schema_id": self.comparison_schema_id,
                    "document": document,
                    "record_count": len(points),
                }
            ]
        document = {
            "keyword": query.get("text"),
            "geo": query.get("geo", ""),
            "timeframe": query.get("timeframe"),
            "collected_at": _iso_moment(collected_at),
            "data": [
                {"date": point.get("date"), "value": point.get("value")}
                for point in points
            ],
        }
        return [
            {
                "path": f"records_{term_slug(str(query.get('text', 'term'))) }.json",
                "artifact_type": "timeseries",
                "format": "json",
                "schema_id": self.series_schema_id,
                "document": document,
                "record_count": len(points),
            }
        ]


def _comparison_averages(raw, tool: str) -> dict:
    """The shared-scale average scores printed in a comparison response.

    A live response carries them; a replayed ``data`` document may not, and a
    missing average is recorded as an empty map rather than invented.
    """

    if tool != TOOL_COMPARE_TERMS or not isinstance(raw, dict):
        return {}
    if "content" not in raw:
        return {}
    from collection.adapters.google_trends.boundary import parse_comparison_tool_result

    try:
        return dict(parse_comparison_tool_result(raw).averages)
    except ValueError:
        return {}


def _iso_moment(value):
    """ISO 8601 UTC string for a datetime (or the value unchanged if a string)."""

    if hasattr(value, "isoformat"):
        return format_datetime(value)
    return value


def term_slug(term: str) -> str:
    """Filename-safe form of a query term (``H4CBH`` -> ``h4cbh``).

    One implementation: the collection pipeline and the boundary instrument both
    name the parsed series file with it.
    """

    slug = "".join(
        character if character.isalnum() else "-" for character in str(term).lower()
    ).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "term"


def _observed_range_label(observations) -> str:
    dates = [point["date"] for point in observations if isinstance(point.get("date"), str)]
    if not dates:
        return "empty (no data points returned)"
    return f"{dates[0]}..{dates[-1]}"


def _observed_bounds(observations) -> tuple:
    """First/last bucket-label dates of the response series (UTC, date
    precision).  ``(None, None)`` for an empty series: no observed period is
    known, and nothing is fabricated (G3 P7)."""
    labels = sorted(
        point["date"] for point in observations if isinstance(point.get("date"), str)
    )
    if not labels:
        return None, None
    return f"{labels[0]}T00:00:00Z", f"{labels[-1]}T00:00:00Z"


def build_adapter(fixture=None, capabilities=None, live=None) -> GoogleTrendsMcpAdapter:
    """Build the adapter for the collection CLI.

    ``live`` is an MCP session callable (``mcp_session.McpStdioSession.call``),
    supplied by ``collection.adapters.get_live_session`` when the caller asks
    for live collection (``collect --live``).  Without a fixture and without
    ``live`` the transport refuses every call, and the pipeline records a failed
    run rather than fabricated data.  Tests and the demo pass ``fixture=`` to
    use the recorded replay transport.
    """
    if fixture is not None:
        transport = RecordedResponseTransport(fixture)
    else:
        transport = SessionMcpTransport(live)
    return GoogleTrendsMcpAdapter(transport, capabilities=capabilities)
