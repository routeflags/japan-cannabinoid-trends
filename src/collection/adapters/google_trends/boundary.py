"""Google Trends boundary-measurement capture support (ISS-20261015-GT-001).

Contract: ``docs/specs/gt-boundary-verification.md`` (execution protocol and
promotion rule).  This module is the *instrument* side of that protocol, not a
general per-source staging driver (that remains ISS-20261015-COL-017):

- :func:`parse_tool_result` - interpret one verbatim ``google-trends-mcp``
  ``interest_over_time`` tool result under the documented label rules.  The
  repository's recorded convention shape (``{keyword, geo, timeframe,
  collected_at, data:[{date, value}]}``) is the *output*; the raw transport
  result is the input.  Anything the documented rules do not cover is refused
  (no guessed dates) and the verbatim result is preserved so an interpretation
  can be redone without re-collecting.
- :func:`verify_capture_manifest` - validate a capture manifest and parse every
  capture.  The protocol requires this pass on the first live capture before
  the measurement matrix runs (format verification).
- :func:`stage_capture` - turn one capture into a staged run through
  :func:`collection.core.pipeline.stage_run` (``.staging/<run-id>/``).  It does
  not decide adoption; ``collection.core.cli adopt`` (``adopt_staged``) runs
  L1 and moves the run to the catalog or quarantine.

Nothing here executes live collection: captures are produced by an approved MCP
session (the repository never runs live collection on its own).  No network,
no credentials.

CLI::

    python -m collection.adapters.google_trends.boundary verify --manifest <f>
    python -m collection.adapters.google_trends.boundary stage  --manifest <f>

Exit codes match the collection core CLI (0 ok / 1 refused / 2 configuration /
3 I/O).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from collection.adapters.google_trends.adapter import (
    SUPPORTED_TIMEFRAMES,
    TOOL_INTEREST_OVER_TIME,
)
from collection.core.pipeline import (
    CollectedArtifact,
    PipelineResult,
    stage_run,
    staging_artifact_id,
)
from collection.core.registry import load_registries
from validation.boundary import MEASUREMENT_PROTOCOL_ID, RAW_ARTIFACT_NAME
from validation.windows import format_datetime, parse_datetime, resolve_relative_timeframe

__all__ = [
    "CAPTURE_MANIFEST_VERSION",
    "CAPTURE_TIMEZONE",
    "MEASUREMENT_STUDY_ID",
    "BoundaryCaptureError",
    "Capture",
    "ParsedPoint",
    "ParsedSeries",
    "load_capture_manifest",
    "main",
    "parse_tool_result",
    "stage_capture",
    "verify_capture_manifest",
]

CAPTURE_MANIFEST_VERSION = "1.0.0"

#: The study the protocol's runs land in (spec §4.2).
MEASUREMENT_STUDY_ID = "cbx-search-trends"

#: Timezone the nominal resolution is computed on (window-registry convention;
#: the ``google-trends-mcp`` request itself does not state a timezone).
CAPTURE_TIMEZONE = "Asia/Tokyo"

#: Protocol-pinned run id shape (spec §4.2).
_RUN_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{6}Z-google-trends-boundary-[a-z0-9]+$")
_GEO_PATTERN = re.compile(r"^[A-Z]{2}$")

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

#: Label shapes the parser accepts (spec §4.4).  Anything else is refused.
#: Ranges come in two observed shapes: same month (``Oct 12 – 18, 2025``) and
#: cross month (``Sep 28 – Oct 4, 2025`` / ``Dec 28 – Jan 3, 2026``).
_RANGE_LABEL = re.compile(
    r"^(?P<month1>[A-Za-z]{3})\s+(?P<day1>\d{1,2})\s*[-\u2013\u2014]\s*"
    r"(?:(?P<month2>[A-Za-z]{3})\s+)?(?P<day2>\d{1,2}),\s*(?P<year>\d{4})$"
)
_SINGLE_LABEL = re.compile(
    r"^(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})$"
)
_ISO_LABEL = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$")


class BoundaryCaptureError(ValueError):
    """A capture cannot be used; ``codes`` are stable reason codes."""

    def __init__(self, codes, message):
        if isinstance(codes, str):
            codes = [codes]
        self.codes = list(codes)
        super().__init__(message)


@dataclass(frozen=True)
class ParsedPoint:
    date: str  # ISO 8601 date of the weekly bucket label (bucket start)
    value: int


@dataclass(frozen=True)
class ParsedSeries:
    """The recorded-convention series derived from one tool result."""

    terms: tuple
    geo: str
    timeframe: str
    points: tuple  # of ParsedPoint

    def records_document(self, collected_at: str) -> dict:
        """The repository's recorded response shape (one term per capture)."""
        return {
            "keyword": self.terms[0],
            "geo": self.geo,
            "timeframe": self.timeframe,
            "collected_at": collected_at,
            "data": [{"date": point.date, "value": point.value} for point in self.points],
        }


@dataclass
class Capture:
    """One validated capture and its parse outcome."""

    run_id: str
    request: dict
    started_at: str
    finished_at: str
    result: object
    notes: str | None = None
    #: filled by :func:`verify_capture_manifest`
    status: str = "unverified"  # parsed | collection_failed | format_mismatch
    parsed: ParsedSeries | None = None
    error: BoundaryCaptureError | None = None
    #: execution context recorded by the CLI (manifest basename / index).
    context: dict = field(default_factory=dict)

    @property
    def timeframe(self) -> str:
        params = self.request.get("params") if isinstance(self.request, dict) else None
        params = params if isinstance(params, dict) else {}
        return str(params.get("timeframe", ""))

    @property
    def term(self) -> str:
        params = self.request.get("params") if isinstance(self.request, dict) else None
        params = params if isinstance(params, dict) else {}
        terms = params.get("terms")
        return terms[0] if isinstance(terms, list) and terms else ""


def _month_number(name: str) -> int:
    try:
        return _MONTHS[name.lower()[:3]]
    except KeyError:
        raise BoundaryCaptureError(
            "label_format_unknown", f"unknown month abbreviation: {name!r}"
        ) from None


def _range_start(match: "re.Match[str]") -> str:
    """Start date of a ranged week label.

    The trailing year belongs to the range *end*; when the range names two
    months and crosses the year boundary (``Dec 28 - Jan 3, 2026``) the start
    therefore lies in the previous year (documented rule, spec §4.4).
    """
    year = int(match.group("year"))
    month1 = _month_number(match.group("month1"))
    month2 = match.group("month2")
    if month2 is not None and month1 > _month_number(month2):
        year -= 1
    return f"{year:04d}-{month1:02d}-{int(match.group('day1')):02d}"


def _label_to_date(label: str) -> str:
    """Map one accepted tool-output label to the bucket-start ISO date."""
    match = _RANGE_LABEL.match(label)
    if match:
        return _range_start(match)
    match = _SINGLE_LABEL.match(label)
    if match:
        month = _month_number(match.group("month"))
        return f"{int(match.group('year')):04d}-{month:02d}-{int(match.group('day')):02d}"
    match = _ISO_LABEL.match(label)
    if match:
        return label
    raise BoundaryCaptureError(
        "label_format_unknown",
        "label does not match a documented shape (range / single date / ISO): "
        f"{label!r}",
    )


def _tool_text(result) -> str:
    """Extract the text block of an MCP tool result (envelope or plain text)."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, list):
            for item in content:
                if (
                    isinstance(item, dict)
                    and item.get("type") == "text"
                    and isinstance(item.get("text"), str)
                ):
                    return item["text"]
        message = result.get("error") if isinstance(result.get("error"), dict) else None
        if message and isinstance(message.get("message"), str):
            raise BoundaryCaptureError("collection_failed", message["message"])
    raise BoundaryCaptureError(
        "result_shape_unknown",
        "tool result carries no text content block and no error message",
    )


def parse_tool_result(result) -> ParsedSeries:
    """Parse one verbatim ``interest_over_time`` tool result.

    Raises :class:`BoundaryCaptureError` with ``collection_failed`` for error
    results and with format codes for anything the documented rules do not
    cover.  Never returns a partially parsed series.
    """
    if isinstance(result, dict) and result.get("isError") is True:
        text = ""
        try:
            text = _tool_text(result)
        except BoundaryCaptureError:
            text = ""
        raise BoundaryCaptureError(
            "collection_failed", (text or "MCP tool reported isError=true").strip()
        )

    text = _tool_text(result)
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("Error:"):
        raise BoundaryCaptureError("collection_failed", lines[0].strip())

    header_terms = None
    geo = ""
    timeframe = ""
    points = []
    for line in lines:
        if line.startswith("Interest over time for: "):
            header_terms = [part.strip() for part in line[len("Interest over time for: "):].split(",")]
            continue
        if line.startswith("Geo: "):
            body = line[len("Geo: "):]
            geo, _, remainder = body.partition(" | Timeframe: ")
            geo = geo.strip()
            timeframe = remainder.strip() if remainder else ""
            continue
        if line.startswith("Date\t"):
            continue
        if not line.strip() or line.startswith("Averages:"):
            continue
        if "\t" not in line or header_terms is None:
            raise BoundaryCaptureError(
                "text_line_unknown", f"unrecognized response line: {line!r}"
            )
        label, _, raw_value = line.partition("\t")
        try:
            value = int(raw_value.split("\t")[0])
        except ValueError:
            raise BoundaryCaptureError(
                "value_not_integer", f"non-integer value for label {label!r}: {raw_value!r}"
            ) from None
        points.append(ParsedPoint(date=_label_to_date(label.strip()), value=value))

    if not points:
        raise BoundaryCaptureError(
            "empty_series",
            "response carries no data rows (a no-data response is not observed "
            "zero and cannot anchor a boundary measurement)",
        )
    if not header_terms or not geo or not timeframe:
        raise BoundaryCaptureError(
            "header_missing",
            "response does not carry the documented header (terms / geo / timeframe)",
        )
    if len(header_terms) != 1:
        # The measurement protocol is single-term; a comparison table would
        # silently reduce to its first column, so it is refused instead.
        raise BoundaryCaptureError(
            "multi_term_unsupported",
            f"the measurement protocol is single-term ({len(header_terms)} terms in response)",
        )
    return ParsedSeries(
        terms=tuple(header_terms),
        geo=geo,
        timeframe=timeframe,
        points=tuple(points),
    )


def load_capture_manifest(document) -> list[Capture]:
    """Validate a capture manifest and return its captures (spec §4.3).

    Raises :class:`BoundaryCaptureError` for structural problems; per-capture
    parse outcomes are filled by :func:`verify_capture_manifest`.
    """
    if not isinstance(document, dict):
        raise BoundaryCaptureError("manifest_invalid", "manifest must be a JSON object")
    if document.get("capture_version") != CAPTURE_MANIFEST_VERSION:
        raise BoundaryCaptureError(
            "manifest_version_unknown",
            f"capture_version must be {CAPTURE_MANIFEST_VERSION!r}",
        )
    instrument = document.get("instrument")
    if not isinstance(instrument, dict) or not isinstance(instrument.get("kind"), str):
        raise BoundaryCaptureError(
            "manifest_invalid", "instrument.kind is required (who produced the captures)"
        )
    raw_captures = document.get("captures")
    if not isinstance(raw_captures, list) or not raw_captures:
        raise BoundaryCaptureError("manifest_invalid", "captures must be a non-empty list")

    captures: list[Capture] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(raw_captures):
        prefix = f"captures[{index}]"
        if not isinstance(item, dict):
            raise BoundaryCaptureError("manifest_invalid", f"{prefix} must be an object")
        run_id = item.get("run_id")
        if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id):
            raise BoundaryCaptureError(
                "run_id_unconventional",
                f"{prefix}.run_id must match the protocol shape "
                "<YYYYMMDDTHHMMSSZ>-google-trends-boundary-<timeframe slug>: {run_id!r}",
            )
        if run_id in seen_ids:
            raise BoundaryCaptureError(
                "run_id_duplicate", f"{prefix}.run_id is declared twice: {run_id}"
            )
        seen_ids.add(run_id)

        request = item.get("request")
        params = request.get("params") if isinstance(request, dict) else None
        if (
            not isinstance(request, dict)
            or request.get("tool") != TOOL_INTEREST_OVER_TIME
            or not isinstance(params, dict)
        ):
            raise BoundaryCaptureError(
                "request_invalid",
                f"{prefix}.request must name the {TOOL_INTEREST_OVER_TIME!r} tool with params",
            )
        terms = params.get("terms")
        if not isinstance(terms, list) or len(terms) != 1 or not isinstance(terms[0], str) or not terms[0]:
            raise BoundaryCaptureError(
                "request_invalid",
                f"{prefix}: the measurement protocol is single-term (terms must hold one name)",
            )
        geo = params.get("geo", "")
        if geo and not (isinstance(geo, str) and _GEO_PATTERN.fullmatch(geo)):
            raise BoundaryCaptureError(
                "request_invalid", f"{prefix}.request.params.geo must be an ISO alpha-2 code or empty"
            )
        if params.get("timeframe") not in SUPPORTED_TIMEFRAMES:
            raise BoundaryCaptureError(
                "request_invalid",
                f"{prefix}.request.params.timeframe must be one of "
                + ", ".join(SUPPORTED_TIMEFRAMES),
            )

        started = item.get("started_at")
        finished = item.get("finished_at")
        try:
            started_moment = parse_datetime(started)
            finished_moment = parse_datetime(finished)
        except ValueError as error:
            raise BoundaryCaptureError("timestamp_invalid", f"{prefix}: {error}") from error
        if finished_moment < started_moment:
            raise BoundaryCaptureError(
                "timestamp_order", f"{prefix}: the call cannot finish before it started"
            )
        if "result" not in item:
            raise BoundaryCaptureError(
                "manifest_invalid", f"{prefix}.result is required (the verbatim tool result)"
            )
        notes = item.get("notes")
        captures.append(
            Capture(
                run_id=run_id,
                request=dict(request),
                started_at=started,
                finished_at=finished,
                result=item["result"],
                notes=notes if isinstance(notes, str) else None,
            )
        )
    return captures


def verify_capture_manifest(document) -> list[Capture]:
    """Load + parse every capture; fill ``status`` / ``parsed`` / ``error``.

    Per-capture outcomes are recorded, not raised: the caller decides whether
    a ``collection_failed`` capture is retried.  The protocol's format
    verification reads the ``status`` of the first capture (spec §4.4).
    """
    captures = load_capture_manifest(document)
    for capture in captures:
        try:
            capture.parsed = parse_tool_result(capture.result)
        except BoundaryCaptureError as error:
            capture.error = error
            capture.status = (
                "collection_failed" if "collection_failed" in error.codes else "format_mismatch"
            )
            continue
        if capture.parsed.timeframe != capture.timeframe:
            capture.error = BoundaryCaptureError(
                "echo_mismatch",
                "response echo describes a different request "
                f"({capture.parsed.timeframe!r} != {capture.timeframe!r})",
            )
            capture.status = "format_mismatch"
            continue
        expected_geo = str(capture.request["params"].get("geo", ""))
        if capture.parsed.geo != expected_geo:
            capture.error = BoundaryCaptureError(
                "echo_mismatch",
                f"response geo does not match the request ({capture.parsed.geo!r} != {expected_geo!r})",
            )
            capture.status = "format_mismatch"
            continue
        capture.status = "parsed"
    return captures


def _timeframe_slug(timeframe: str) -> str:
    return re.sub(r"[^a-z0-9]", "", timeframe.split(" ", 1)[-1].lower()) or "window"


def _term_slug(term: str) -> str:
    slug = "".join(
        character if character.isalnum() else "-" for character in term.lower()
    ).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "term"


def _resolve_registered_query(registries, term: str) -> dict:
    matches = [
        entry
        for entry in registries.queries
        if isinstance(entry, dict) and entry.get("canonical_text") == term
    ]
    if len(matches) != 1:
        raise BoundaryCaptureError(
            "query_unregistered",
            f"term {term!r} matches {len(matches)} registered queries; the measurement "
            "term must name exactly one registered query (metadata/queries)",
        )
    return matches[0]


def stage_capture(
    capture: Capture,
    *,
    workspace_root,
    datasets_root,
    registries=None,
    study_id: str = MEASUREMENT_STUDY_ID,
) -> PipelineResult:
    """Stage one capture as a run (``.staging/<run-id>/``), without judging it.

    ``capture`` must have passed :func:`verify_capture_manifest`.  A parsed
    capture stages the verbatim result plus the recorded-convention series; a
    ``collection_failed`` capture stages the verbatim error result only
    (failure evidence - never converted into an empty series).
    """
    if capture.status == "unverified":  # not run through verify_capture_manifest
        try:
            capture.parsed = parse_tool_result(capture.result)
            capture.status = "parsed"
        except BoundaryCaptureError as error:
            capture.error = error
            capture.status = (
                "collection_failed" if "collection_failed" in error.codes else "format_mismatch"
            )
    if capture.status == "format_mismatch":
        raise BoundaryCaptureError(
            capture.error.codes if capture.error else "format_mismatch",
            str(capture.error) if capture.error else "capture format mismatch",
        )
    if registries is None:
        registries = load_registries("config", "metadata")

    term = capture.term
    query_entry = _resolve_registered_query(registries, term)
    started = parse_datetime(capture.started_at)
    finished = parse_datetime(capture.finished_at)
    timeframe = capture.timeframe
    nominal_start, nominal_end = resolve_relative_timeframe(
        timeframe, started, CAPTURE_TIMEZONE
    )

    plan = {
        "plan_id": f"boundary-measurement-{_timeframe_slug(timeframe)}-{capture.run_id}",
        "study_id": study_id,
        "source_id": "google-trends",
        "collector_id": "google-trends-mcp",
        "query_id": query_entry.get("query_id"),
        "query": {
            "text": term,
            "geo": capture.request["params"].get("geo", ""),
            "timeframe": timeframe,
        },
        "required_capabilities": ["relative_date_range"],
        "window": {
            # The collector resolves the relative request at its own request
            # time; the nominal resolution is the model value this protocol
            # measures against.  It is deliberately NOT declared as a
            # registered window_id (it is not a study window).
            "start": format_datetime(nominal_start),
            "end_exclusive": format_datetime(nominal_end),
            "granularity": "week",
            "week_start": "sunday",
            "timezone": CAPTURE_TIMEZONE,
        },
        "purpose": (
            "GT boundary measurement probe ("
            f"{timeframe} @ {format_datetime(started)}; "
            "docs/specs/gt-boundary-verification.md)"
        ),
    }
    if query_entry.get("compound_id"):
        plan["query"]["compound_id"] = query_entry["compound_id"]
    if query_entry.get("intent_id"):
        plan["query"]["intent_id"] = query_entry["intent_id"]
    if query_entry.get("language"):
        plan["query"]["language"] = query_entry["language"]

    environment = {
        "measurement": {
            "protocol": MEASUREMENT_PROTOCOL_ID,
            "instrument": dict(capture.context.get("instrument") or {}),
        }
    }
    if capture.context.get("manifest"):
        environment["measurement"]["capture_manifest"] = capture.context["manifest"]
    if capture.context.get("index") is not None:
        environment["measurement"]["capture_index"] = capture.context["index"]
    if capture.notes:
        environment["measurement"]["notes"] = capture.notes

    submitted = {"tool": TOOL_INTEREST_OVER_TIME, **capture.request["params"]}
    limitations = (
        "requested_start/end_exclusive record the nominal resolution of the "
        f"relative request {timeframe!r} at the reference time; they are not a "
        "study-requested absolute window (P5)",
        "the collector resolves the relative timeframe at request time; this "
        "run measures the observed boundaries (spec: gt-boundary-verification)",
        "weekly buckets (Sunday start) quantize both boundaries to at most one "
        "bucket; exact calendar-day equality is not claimable",
    )

    with tempfile.TemporaryDirectory(prefix="gt-boundary-capture-") as scratch:
        scratch_path = Path(scratch)
        raw_path = scratch_path / RAW_ARTIFACT_NAME
        raw_path.write_text(
            json.dumps(capture.result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        artifacts = [
            CollectedArtifact(
                source=str(raw_path),
                path=RAW_ARTIFACT_NAME,
                artifact_type="raw_response",
                format="json",
                schema_id="google-trends-mcp-tool-result-v1",
                completeness="complete" if capture.status == "parsed" else "missing",
            )
        ]

        if capture.status == "parsed":
            assert capture.parsed is not None
            observed_first = capture.parsed.points[0].date
            observed_last = capture.parsed.points[-1].date
            dates = sorted(point.date for point in capture.parsed.points)
            series_name = f"records_{_term_slug(term)}.json"
            series_path = scratch_path / series_name
            series_path.write_text(
                json.dumps(
                    capture.parsed.records_document(format_datetime(finished)),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            artifacts.append(
                CollectedArtifact(
                    source=str(series_path),
                    path=series_name,
                    artifact_type="timeseries",
                    format="json",
                    schema_id="google-trends-interest-over-time-v1",
                    completeness="complete",
                    record_count=len(capture.parsed.points),
                    derived_from=[staging_artifact_id(capture.run_id, RAW_ARTIFACT_NAME)],
                )
            )
            execution = {
                "status": "success",
                "returned_count": len(capture.parsed.points),
                "errors": [],
                "pagination_exhausted": True,
            }
            temporal = {
                "granularity": "week",
                "week_start": "sunday",
                "collector_window_type": "relative_duration",
                "exact_window_match": False,
                "boundary_semantics": (
                    "relative timeframe resolved by the collector at request time; "
                    f"weekly buckets (Sunday start); observed range "
                    f"{observed_first}..{observed_last}"
                ),
                "observed_min_timestamp": f"{dates[0]}T00:00:00Z",
                "observed_max_timestamp": f"{dates[-1]}T00:00:00Z",
                "reference_time": format_datetime(started),
                "limitations": list(limitations),
            }
        else:
            message = str(capture.error) if capture.error else "collection failed"
            execution = {
                "status": "failed",
                "returned_count": 0,
                "errors": [{"code": "COLLECTION_FAILED", "message": message}],
            }
            temporal = {
                "granularity": "week",
                "week_start": "sunday",
                "collector_window_type": "relative_duration",
                "exact_window_match": False,
                "boundary_semantics": f"collection failed; no series observed ({message})",
                "reference_time": format_datetime(started),
                "limitations": list(limitations)
                + ["collection failed; a failed collection is not an observed zero"],
            }

        return stage_run(
            plan,
            artifacts=artifacts,
            execution=execution,
            started_at=started,
            finished_at=finished,
            workspace_root=workspace_root,
            datasets_root=datasets_root,
            registries=registries,
            temporal=temporal,
            submitted_parameters=submitted,
            environment=environment,
            run_id=capture.run_id,
        )


def _emit(document: dict, *, fmt: str, output: str | None) -> None:
    if fmt == "json":
        text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        if output:
            target = Path(output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        else:
            print(text, end="")


def cmd_verify(args) -> int:
    from collection.core.cli import EXIT_GATE, EXIT_IO, EXIT_OK

    manifest_path = Path(args.manifest)
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print(f"cannot read capture manifest: {manifest_path}", file=sys.stderr)
        return EXIT_IO
    try:
        captures = verify_capture_manifest(document)
    except BoundaryCaptureError as error:
        print(f"manifest refused ({', '.join(error.codes)}): {error}", file=sys.stderr)
        return EXIT_GATE

    refused = any(capture.status == "format_mismatch" for capture in captures)
    report = {
        "command": "verify-capture-manifest",
        "capture_version": CAPTURE_MANIFEST_VERSION,
        "manifest": manifest_path.name,
        "capture_count": len(captures),
        "format_verified": not refused,
        "refused": refused,
        "captures": [],
    }
    for capture in captures:
        entry = {
            "run_id": capture.run_id,
            "timeframe": capture.timeframe,
            "status": capture.status,
        }
        if capture.status == "parsed" and capture.parsed is not None:
            points = capture.parsed.points
            entry["point_count"] = len(points)
            entry["observed_first"] = min(point.date for point in points)
            entry["observed_last"] = max(point.date for point in points)
        if capture.error is not None:
            entry["reason_codes"] = list(capture.error.codes)
            entry["message"] = str(capture.error)
        report["captures"].append(entry)
    _emit(report, fmt=args.format, output=args.output)
    for entry in report["captures"]:
        print(
            f"{entry['status'].upper()} run_id={entry['run_id']} "
            f"timeframe={entry['timeframe']}"
            + (f" points={entry['point_count']}" if "point_count" in entry else "")
            + (f" [{', '.join(entry.get('reason_codes', []))}] {entry.get('message', '')}" if "message" in entry else ""),
            file=sys.stderr,
        )
    if refused:
        print(
            "format verification failed: parser and observed output disagree; "
            "stop the matrix, record the real format and update the parser "
            "(spec §4.4)",
            file=sys.stderr,
        )
        return EXIT_GATE
    return EXIT_OK


def cmd_stage(args) -> int:
    from collection.core.cli import EXIT_CONFIG, EXIT_GATE, EXIT_IO, EXIT_OK
    from collection.core.registry import ConfigError

    manifest_path = Path(args.manifest)
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print(f"cannot read capture manifest: {manifest_path}", file=sys.stderr)
        return EXIT_IO
    try:
        captures = verify_capture_manifest(document)
    except BoundaryCaptureError as error:
        print(f"manifest refused ({', '.join(error.codes)}): {error}", file=sys.stderr)
        return EXIT_GATE

    try:
        registries = load_registries(args.config_dir, args.metadata_dir)
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return EXIT_CONFIG

    instrument = dict(document.get("instrument") or {})
    results = []
    failed = False
    for index, capture in enumerate(captures):
        capture.context = {"instrument": instrument, "manifest": manifest_path.name, "index": index}
        try:
            result = stage_capture(
                capture,
                workspace_root=args.workspace,
                datasets_root=args.datasets_root,
                registries=registries,
                study_id=args.study,
            )
        except BoundaryCaptureError as error:
            results.append(
                {
                    "run_id": capture.run_id,
                    "action": "stopped",
                    "reason_codes": list(error.codes),
                    "message": str(error),
                }
            )
            failed = True
            continue
        results.append(result.to_dict())
        if result.action != "staged":
            failed = True

    report = {
        "command": "stage-capture-manifest",
        "manifest": manifest_path.name,
        "study_id": args.study,
        "capture_count": len(captures),
        "staged_count": sum(1 for entry in results if entry.get("action") == "staged"),
        "stopped_count": sum(1 for entry in results if entry.get("action") == "stopped"),
        "results": results,
    }
    _emit(report, fmt=args.format, output=args.output)
    for entry in results:
        print(
            f"{str(entry.get('action', '?')).upper()} run_id={entry.get('run_id')} "
            f"{entry.get('staging_dir') or ''}".rstrip(),
            file=sys.stderr,
        )
        for issue in entry.get("issues") or []:
            print(f"  [{issue['code']}] {issue['path']}: {issue['message']}", file=sys.stderr)
    return EXIT_GATE if failed else EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m collection.adapters.google_trends.boundary",
        description=(
            "Google Trends boundary-measurement capture tooling "
            "(docs/specs/gt-boundary-verification.md). Offline: it parses and "
            "stages captures produced by an approved MCP session; it never "
            "collects live data itself."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser(
        "verify", help="validate a capture manifest and parse every capture (format check)"
    )
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--format", choices=("text", "json"), default="text")
    verify.add_argument("--output")
    verify.set_defaults(handler=cmd_verify)

    stage = sub.add_parser("stage", help="stage captures as runs (no adoption decision)")
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--workspace", default=".")
    stage.add_argument("--datasets-root", default="datasets")
    stage.add_argument("--config-dir", default="config")
    stage.add_argument("--metadata-dir", default="metadata")
    stage.add_argument("--study", default=MEASUREMENT_STUDY_ID)
    stage.add_argument("--format", choices=("text", "json"), default="text")
    stage.add_argument("--output")
    stage.set_defaults(handler=cmd_stage)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
