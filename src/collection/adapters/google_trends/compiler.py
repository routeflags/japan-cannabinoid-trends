"""Google Trends window compiler (G3 §6.3).

Contract sources
----------------
- G3 §6 (Window Compiler: interface, X example, Google Trends rules):
  ``docs/plans/20261013c.md``.
- G1 §9 capability gate / collector registry (the registry is the record of
  truth; unknown capabilities are never upgraded): ``docs/plans/20261013a.md``.

Rules
-----
- The compiler maps an absolute, half-open UTC window onto the collector's
  registered relative timeframe vocabulary (``today 1-m`` / ``3-m`` /
  ``12-m`` / ``5-y``).  The matching is nominal: a timeframe is usable when
  its resolution at the reference time matches both window bounds within one
  weekly bucket (``WINDOW_MATCH_TOLERANCE``, see ``validation.windows``).
- No silent fallback (P6): when no registered timeframe represents the
  window, or the match is ambiguous, or the registry claims absolute support
  that this build has not implemented, the compilation is *refused* with
  stable reason codes.
- ``exact`` is always ``False`` today: the collector resolves ``today ...``
  at request time on its own boundaries and the boundary semantics are
  unverified (registry: ``absolute_date_range`` unknown; no live verification
  has been performed).  The compilation records its limitations explicitly.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation.windows import (
    RELATIVE_TIMEFRAME_MODELS,
    CompiledWindow,
    WindowCompilationError,
    format_datetime,
    parse_datetime,
    resolve_relative_timeframe,
    within_window_tolerance,
)

__all__ = ["COLLECTOR_ID", "GoogleTrendsWindowCompiler"]

COLLECTOR_ID = "google-trends-mcp"


class GoogleTrendsWindowCompiler:
    """Window compiler for the registered ``google-trends-mcp`` collector."""

    collector_id = COLLECTOR_ID

    def compile(self, window: dict, *, reference_time, capabilities=None) -> CompiledWindow:
        """Compile an absolute window into the MCP tool parameters.

        ``reference_time`` is the collection instant the relative timeframe
        is resolved against; it is required (G3-T07: a relative period is
        never resolved against an implicit "now").

        Raises :class:`WindowCompilationError` with reason codes when the
        window cannot be represented (fail closed).
        """
        if not isinstance(window, dict):
            raise WindowCompilationError("window_invalid", "window must be a mapping")
        try:
            start = parse_datetime(window.get("start"))
            end = parse_datetime(window.get("end_exclusive"))
        except ValueError as error:
            raise WindowCompilationError("window_invalid", str(error)) from error
        if start >= end:
            raise WindowCompilationError(
                "window_invalid", "window start must be earlier than end_exclusive"
            )

        timezone_name = window.get("timezone") or "UTC"
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise WindowCompilationError(
                "timezone_unknown", f"unknown IANA timezone: {timezone_name!r}"
            ) from error

        if reference_time is None:
            raise WindowCompilationError(
                "reference_time_missing",
                "a relative timeframe requires the reference (collection) time",
            )
        if not isinstance(reference_time, datetime):
            try:
                reference_time = parse_datetime(reference_time)
            except ValueError as error:
                raise WindowCompilationError(
                    "reference_time_invalid", str(error)
                ) from error
        if reference_time.tzinfo is None:
            raise WindowCompilationError(
                "reference_time_invalid", "reference time must be timezone-aware"
            )

        capabilities = capabilities if isinstance(capabilities, dict) else {}
        if capabilities.get("absolute_date_range") == "supported":
            # The registry is the record of truth: if it ever records
            # absolute support, switching to (or inventing) relative
            # parameters anyway would be a silent fallback (P6).
            raise WindowCompilationError(
                "absolute_path_not_implemented",
                "the registry records absolute_date_range=supported but this "
                "compiler build has no verified absolute implementation; "
                "refusing to fall back to a relative window silently",
            )

        candidates = []
        for timeframe in RELATIVE_TIMEFRAME_MODELS:
            resolved = resolve_relative_timeframe(timeframe, reference_time, timezone_name)
            if within_window_tolerance((start, end), resolved):
                candidates.append((timeframe, resolved))
        if not candidates:
            raise WindowCompilationError(
                "no_registered_timeframe_matches",
                "no registered relative timeframe represents the requested "
                f"window ({window.get('start')} .. {window.get('end_exclusive')}) "
                f"at reference {format_datetime(reference_time)}; the collection "
                "must not silently fetch a different period (c.md §6.3, P6)",
            )
        if len(candidates) > 1:
            names = ", ".join(name for name, _ in candidates)
            raise WindowCompilationError(
                "ambiguous_timeframe_match",
                f"multiple registered timeframes match the window within "
                f"tolerance: {names}; refusing to guess",
            )

        timeframe, resolved = candidates[0]
        limitations = (
            "collector window type is relative_duration; the absolute requested "
            "window cannot be expressed exactly (boundary semantics unverified, "
            "c.md §6.2)",
            f"'{timeframe}' is resolved nominally at the recorded reference time; "
            "Google Trends resolves it at request time and the actual boundaries "
            "are unverified (c.md §6.3)",
            "coverage is recorded as partial/unknown until boundary verification "
            "(c.md §9)",
        )
        return CompiledWindow(
            collector_id=self.collector_id,
            window_id=window.get("window_id"),
            collector_window_type="relative_duration",
            parameters={"timeframe": timeframe},
            boundary_semantics="unverified",
            exact=False,
            limitations=limitations,
            reference_time=format_datetime(reference_time),
            resolved_start=format_datetime(resolved[0]),
            resolved_end_exclusive=format_datetime(resolved[1]),
            requested_start=window.get("start"),
            requested_end_exclusive=window.get("end_exclusive"),
        )
