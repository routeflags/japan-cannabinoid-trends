"""G3 temporal window contract primitives (Temporal Contract / Window Compiler).

Contract sources
----------------
- G3 §4 (Temporal Contract), §5 (period specification types), §6 (Window
  Compiler), §7 (Python conversion sample), §9 (coverage vocabulary), §10
  (bucket generation reference), §13 (schema + semantic split):
  ``docs/plans/20261013c.md``.
- Rollout notes and the adopted interpretation of the §4.2/§13 divergence are
  recorded in ``validation.schemas.temporal`` and the G3 slice plan
  (``docs/plans/g3-temporal-contract-plan.md``).

Scope
-----
Shared, *source-agnostic* temporal contract helpers used by the validation
layer (coverage, audits, comparability) and by the per-source window
compilers (which live under ``src/collection/adapters/<source>/``):

- half-open interval conversion with explicit timezone (P2/P3, c.md §7);
- nominal resolution of the registered relative timeframe vocabulary
  (``today 1-m`` / ``3-m`` / ``12-m`` / ``5-y``) at a required reference time
  (P1/P6, c.md §6.3);
- bounded window matching (one weekly-bucket tolerance, documented below);
- month bucket generation (c.md §10, minimal adaptation);
- the :class:`CompiledWindow` output type + compiler shape check (c.md §6.1);
- plan window vs window-registry consistency (fail closed when the registry
  is present and the plan claims a registered ``window_id``).

The relative vocabulary models are *nominal*.  Google Trends resolves
``today ...`` at request time on its own boundaries; the models exist so the
system can reason deterministically, and every compiled window keeps
``exact=False`` / ``boundary_semantics="unverified"`` until a live
verification records real boundary behavior.  They are never treated as the
study's canonical window (P1: the canonical window is the absolute one).
"""

from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation.reporting import Issue, join_pointer

__all__ = [
    "RELATIVE_TIMEFRAME_MODELS",
    "WINDOW_MATCH_TOLERANCE",
    "CompiledWindow",
    "WindowCompiler",
    "WindowCompilationError",
    "check_plan_window_registry",
    "check_window_compiler",
    "check_window_registry_files",
    "find_window",
    "format_datetime",
    "load_window_documents",
    "local_window_to_utc",
    "month_buckets",
    "parse_datetime",
    "resolve_relative_timeframe",
    "subtract_calendar_months",
    "within_window_tolerance",
]

#: Nominal duration models for the registered relative timeframe vocabulary.
#: Only ``today 12-m`` and ``today 5-y`` have recorded run evidence in this
#: repository; the others are the documented MCP tool vocabulary (adapter
#: allow-list).  The models are nominal (calendar months/years for the
#: European-style labels, fixed days for the day-window labels) and are not
#: verified API behavior.
RELATIVE_TIMEFRAME_MODELS: dict[str, dict] = {
    "today 1-m": {"days": 30},
    "today 3-m": {"days": 90},
    "today 12-m": {"months": 12},
    "today 5-y": {"years": 5},
}

#: Matching tolerance for compiled windows: one weekly bucket (7 days).
#: Rationale: weekly-bucket series quantize both ends of a rolling window to
#: the bucket grid (<= 6 days offset), and calendar month/year arithmetic
#: differs from fixed nominal durations by at most a few days (leap years).
#: The tolerance is deliberately coarse and *never* upgraded to an exactness
#: claim; it only decides "the collector parameter family can stand in for
#: this window" vs "refuse" (P6).
WINDOW_MATCH_TOLERANCE = timedelta(days=7)

_UTC = timezone.utc


# ---------------------------------------------------------------------------
# datetime helpers
# ---------------------------------------------------------------------------


def parse_datetime(value) -> datetime:
    """Parse an ISO 8601 datetime; the result must be timezone-aware.

    Raises :class:`ValueError` for non-strings, unparseable values and naive
    datetimes (P3: datetimes carry an explicit timezone).
    """
    if not isinstance(value, str) or not value:
        raise ValueError("datetime must be a non-empty ISO 8601 string")
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"not an ISO 8601 datetime: {value!r}") from error
    if moment.tzinfo is None:
        raise ValueError("datetime is missing a timezone offset")
    return moment


def format_datetime(moment: datetime) -> str:
    """Render a datetime as second/microsecond ISO 8601 UTC (``...Z``)."""
    if not isinstance(moment, datetime) or moment.tzinfo is None:
        raise ValueError("format_datetime requires a timezone-aware datetime")
    return moment.astimezone(_UTC).isoformat().replace("+00:00", "Z")


def _known_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"unknown IANA timezone: {name!r}") from error


def local_window_to_utc(start_local: datetime, end_local: datetime, timezone_name: str):
    """Convert a local calendar half-open window to UTC (c.md §7 sample).

    - naive inputs get ``timezone_name`` attached (the calendar is stated);
    - timezone-aware inputs are converted as-is and never overwritten with
      ``replace()`` (c.md §7 last paragraph: ambiguous / nonexistent local
      times must not be silently rewritten);
    - ``start >= end`` raises :class:`ValueError` (P2 half-open ordering).
    """
    tz = _known_timezone(timezone_name)
    start = start_local if start_local.tzinfo is not None else start_local.replace(tzinfo=tz)
    end = end_local if end_local.tzinfo is not None else end_local.replace(tzinfo=tz)
    if start >= end:
        raise ValueError("invalid temporal window: start must be earlier than end")
    return {
        "start": format_datetime(start),
        "end_exclusive": format_datetime(end),
    }


def subtract_calendar_months(moment: datetime, months: int, timezone_name: str) -> datetime:
    """Subtract calendar months on the named calendar, clamping the day.

    The wall-clock time-of-day is preserved on the ``timezone_name`` calendar
    (so DST transitions are handled by the calendar, not by a fixed
    duration); month-end clamping applies (e.g. Mar 31 - 1 month =
    Feb 28/29; Jan 31 - 1 month = Dec 31).
    """
    tz = _known_timezone(timezone_name)
    local = moment.astimezone(tz)
    total = local.year * 12 + (local.month - 1) - months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(local.day, calendar.monthrange(year, month)[1])
    shifted = local.replace(year=year, month=month, day=day)
    return shifted


def resolve_relative_timeframe(
    timeframe: str, reference: datetime, timezone_name: str = "UTC"
) -> tuple[datetime, datetime]:
    """Resolve a registered relative timeframe at ``reference`` (nominal).

    Returns ``(start, end_exclusive)`` as UTC-aware datetimes where
    ``end_exclusive`` equals ``reference``.  A missing/unusable reference is
    an error (G3-T07: a relative period must record its reference time; it is
    never resolved against an implicit "now" here).
    """
    if reference is None:
        raise ValueError("relative timeframe resolution requires a reference time")
    if not isinstance(reference, datetime):
        reference = parse_datetime(reference)
    if reference.tzinfo is None:
        raise ValueError("reference time must be timezone-aware")
    try:
        model = RELATIVE_TIMEFRAME_MODELS[timeframe]
    except KeyError:
        raise ValueError(f"unregistered relative timeframe: {timeframe!r}") from None

    end = reference.astimezone(_UTC)
    months = model.get("months", 0) + model.get("years", 0) * 12
    if months:
        start = subtract_calendar_months(end, months, timezone_name).astimezone(_UTC)
    else:
        start = end - timedelta(days=model["days"])
    if start >= end:  # pragma: no cover - models are positive durations
        raise ValueError("relative timeframe resolves to an empty interval")
    return start, end


def within_window_tolerance(
    first: tuple[datetime, datetime],
    second: tuple[datetime, datetime],
    tolerance: timedelta = WINDOW_MATCH_TOLERANCE,
) -> bool:
    """True when both ends of two half-open windows are within ``tolerance``."""
    return abs(first[0] - second[0]) <= tolerance and abs(first[1] - second[1]) <= tolerance


# ---------------------------------------------------------------------------
# bucket generation (c.md §10, minimal adaptation)
# ---------------------------------------------------------------------------


def month_buckets(start: datetime, end: datetime, timezone_name: str = "UTC"):
    """Yield half-open calendar-month buckets on the named calendar.

    The first bucket starts at ``start`` itself (partial months are kept, not
    padded: G3-T13 "自动ゼロ補完禁止"), buckets break at local month
    boundaries, and the last bucket is clamped to ``end``.  Both inputs must
    be timezone-aware; the result uses UTC instants.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("month_buckets requires timezone-aware datetimes")
    if start >= end:
        raise ValueError("invalid temporal window: start must be earlier than end")
    tz = _known_timezone(timezone_name)
    current = start.astimezone(tz)
    end_local = end.astimezone(tz)
    while current < end_local:
        year = current.year + (current.month == 12)
        month = 1 if current.month == 12 else current.month + 1
        boundary = current.replace(
            year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        bucket_end = min(boundary, end_local)
        if bucket_end <= current:  # pragma: no cover - guarded by loop condition
            break
        yield {
            "start": format_datetime(current),
            "end_exclusive": format_datetime(bucket_end),
        }
        current = bucket_end


# ---------------------------------------------------------------------------
# compiled window contract (c.md §6.1)
# ---------------------------------------------------------------------------


class WindowCompilationError(ValueError):
    """A window cannot be represented for a collector (fail closed, P6).

    ``codes`` is a list of stable reason codes (e.g.
    ``no_registered_timeframe_matches``); callers translate them into issues
    and never fall back to a different period silently.
    """

    def __init__(self, codes, message):
        if isinstance(codes, str):
            codes = [codes]
        self.codes = list(codes)
        super().__init__(message)


@dataclass(frozen=True)
class CompiledWindow:
    """Output of a window compiler (c.md §6.1 ``CompiledWindow``).

    ``exact`` stays ``False`` until the collector's boundary behavior has
    been verified; ``limitations`` explains why.  ``resolved_start`` /
    ``resolved_end_exclusive`` are the collector specification's *nominal*
    resolution at ``reference_time`` (UTC ISO 8601), recorded for provenance
    and coverage — never as the study's canonical window.
    """

    collector_id: str
    window_id: str | None
    collector_window_type: str
    parameters: dict
    boundary_semantics: str
    exact: bool
    limitations: tuple = ()
    reference_time: str | None = None
    resolved_start: str | None = None
    resolved_end_exclusive: str | None = None
    requested_start: str | None = None
    requested_end_exclusive: str | None = None

    def to_dict(self) -> dict:
        return {
            "collector_id": self.collector_id,
            "window_id": self.window_id,
            "collector_window_type": self.collector_window_type,
            "parameters": dict(self.parameters),
            "boundary_semantics": self.boundary_semantics,
            "exact": self.exact,
            "limitations": list(self.limitations),
            "reference_time": self.reference_time,
            "resolved_start": self.resolved_start,
            "resolved_end_exclusive": self.resolved_end_exclusive,
            "requested_start": self.requested_start,
            "requested_end_exclusive": self.requested_end_exclusive,
        }


@runtime_checkable
class WindowCompiler(Protocol):
    """The common window-compiler contract (c.md §6.1, Python shape)."""

    collector_id: str

    def compile(self, window: dict, *, reference_time, capabilities=None) -> CompiledWindow:
        """Compile an absolute window for this collector (fail closed)."""
        ...


def check_window_compiler(compiler) -> list[str]:
    """Mechanically verify the compiler shape (contract-test helper).

    Returns violations; an empty list means the compiler satisfies the
    interface shape.  ``compile`` output semantics are checked by the
    contract tests of each compiler.
    """
    violations: list[str] = []
    if not isinstance(getattr(compiler, "collector_id", None), str) or not compiler.collector_id:
        violations.append("missing or empty attribute: collector_id")
    if not callable(getattr(compiler, "compile", None)):
        violations.append("missing method: compile")
    return violations


# ---------------------------------------------------------------------------
# window registry (metadata/windows/*.json)
# ---------------------------------------------------------------------------


def load_window_documents(directory) -> list[dict]:
    """Read ``metadata/windows/*.json`` window documents.

    A missing directory yields an empty list (the repo-wide convention: a
    missing registry disables the corresponding checks).  A malformed file
    raises :class:`ValueError` so the caller can map it to a configuration
    error; nothing is written.
    """
    path = Path(directory)
    if not path.is_dir():
        return []
    documents = []
    for file in sorted(path.glob("*.json")):
        try:
            documents.append(json.loads(file.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError(f"window document cannot be read as JSON: {file}") from error
    return documents


def find_window(windows, window_id) -> dict | None:
    """Return the window document registered under ``window_id`` or ``None``."""
    for window in windows or ():
        if isinstance(window, dict) and window.get("window_id") == window_id:
            return window
    return None


def check_window_registry_files(items: list[tuple[Path, dict]]) -> dict[str, list[Issue]]:
    """Cross-file checks for the window registry (per-path issue lists).

    - ``WINDOW_ID_DUPLICATE``: two files declare the same ``window_id``
      (reported on the later file; ``window_id`` is the lookup key and must
      be unique);
    - ``WINDOW_FILE_STEM_MISMATCH``: ``<stem>.json`` does not equal the
      document's ``window_id`` (discoverability rule documented in
      docs/specs/validation-framework.md §10.1).
    """
    results: dict[str, list[Issue]] = {str(path): [] for path, _ in items}
    seen: dict[str, str] = {}
    for path, document in items:
        key = str(path)
        if not isinstance(document, dict):
            continue
        window_id = document.get("window_id")
        if not isinstance(window_id, str) or not window_id:
            continue
        if window_id in seen:
            results[key].append(
                Issue(
                    code="WINDOW_ID_DUPLICATE",
                    path="/window_id",
                    severity="error",
                    message=f"window_id is already declared by {seen[window_id]}",
                    rule="window_registry",
                )
            )
        else:
            seen[window_id] = key
        if path.stem != window_id:
            results[key].append(
                Issue(
                    code="WINDOW_FILE_STEM_MISMATCH",
                    path="/window_id",
                    severity="error",
                    message="window file name must equal window_id"
                    f" (expected {window_id}.json)",
                    rule="window_registry",
                )
            )
    return results


_WINDOW_CHECK_FIELDS = ("start", "end_exclusive", "timezone", "granularity", "week_start")


def check_plan_window_registry(window: dict, windows) -> list[Issue]:
    """P1 consistency: a plan window must match its registered window.

    Only runs when the plan declares a ``window_id`` *and* the window
    registry is present (missing registry = check disabled, per repository
    convention).  The comparison is exact on the stored UTC bounds and the
    calendar fields: a plan is the study's own statement, not an estimate.
    """
    issues: list[Issue] = []
    if not isinstance(window, dict):
        return issues
    window_id = window.get("window_id")
    if not isinstance(window_id, str) or not window_id:
        return issues
    registered = find_window(windows, window_id)
    if registered is None:
        issues.append(
            Issue(
                code="WINDOW_UNREGISTERED",
                path="/window/window_id",
                severity="error",
                message="window_id is not registered in metadata/windows "
                "(the absolute window must exist in the window registry)",
                rule="window_registry",
            )
        )
        return issues
    for field_name in _WINDOW_CHECK_FIELDS:
        if window.get(field_name) != registered.get(field_name):
            issues.append(
                Issue(
                    code="WINDOW_REGISTRY_MISMATCH",
                    path=join_pointer("/window", field_name),
                    severity="error",
                    message="plan window does not match the registered window "
                    f"{window_id!r} ({field_name})",
                    rule="window_registry",
                )
            )
    return issues
