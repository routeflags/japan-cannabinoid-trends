"""YouTube Apify ``dateFilter`` window compiler (WIN-002 MVP).

This compiler is intentionally narrower than the collector's documented
vocabulary.  The repository has adoption evidence for ``dateFilter=year`` from
COL-033, but not enough measured boundary evidence to compile ``month``,
``week``, ``today``, ``hour`` or ``all`` without guessing.  Those windows fail
closed until they have their own evidence.

The compiled parameter is the request filter only.  The observed video
publish-date range in a CSV handover remains a separate fact and must not be
treated as the API search condition.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation.windows import (
    CompiledWindow,
    WindowCompilationError,
    format_datetime,
    parse_datetime,
)

__all__ = ["COLLECTOR_ID", "YouTubeApifyWindowCompiler"]

COLLECTOR_ID = "youtube-apify-scraper"

_YEAR_FILTER = "year"
_YEAR_WINDOW_DAYS = 365
_DAILY_LABEL_TOLERANCE = timedelta(days=1)


class YouTubeApifyWindowCompiler:
    """Compiler for the measured YouTube Apify ``dateFilter=year`` case."""

    collector_id = COLLECTOR_ID

    def compile(
        self, window: dict, *, reference_time, capabilities=None
    ) -> CompiledWindow:
        """Compile a measured trailing-year window to ``dateFilter=year``.

        ``reference_time`` is required: the actor's filter is relative to the
        run time, not an absolute date range.  The output is inexact because the
        boundary evidence is adoption-level and daily-label tolerant, not a live
        two-pass boundary verification.
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
            tz = ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise WindowCompilationError(
                "timezone_unknown", f"unknown IANA timezone: {timezone_name!r}"
            ) from error

        if reference_time is None:
            raise WindowCompilationError(
                "reference_time_missing",
                "YouTube dateFilter is relative and requires the collection "
                "reference time",
            )
        if not isinstance(reference_time, datetime):
            try:
                reference_time = parse_datetime(reference_time)
            except ValueError as error:
                raise WindowCompilationError("reference_time_invalid", str(error)) from error
        if reference_time.tzinfo is None:
            raise WindowCompilationError(
                "reference_time_invalid", "reference time must be timezone-aware"
            )

        capabilities = capabilities if isinstance(capabilities, dict) else {}
        if capabilities.get("absolute_date_range") == "supported":
            raise WindowCompilationError(
                "absolute_path_not_implemented",
                "the registry records absolute_date_range=supported but this "
                "compiler build only has measured relative dateFilter=year "
                "evidence; refusing to fall back silently",
            )
        if capabilities.get("relative_date_range") == "unsupported":
            raise WindowCompilationError(
                "relative_date_filter_unsupported",
                "the registry records relative_date_range=unsupported for "
                "youtube-apify-scraper",
            )

        resolved_start, resolved_end = _resolve_year_filter(reference_time, tz)
        if (
            abs(start - resolved_start) > _DAILY_LABEL_TOLERANCE
            or abs(end - resolved_end) > _DAILY_LABEL_TOLERANCE
        ):
            raise WindowCompilationError(
                "no_verified_date_filter_matches",
                "only the measured YouTube Apify dateFilter=year rolling window "
                "is implemented; the requested window does not match its "
                "daily-label-tolerant trailing-365-day model",
            )

        limitations = (
            "dateFilter=year is a measured relative request parameter, not an "
            "absolute date range; exact boundaries are not verified",
            "window.start/end_exclusive remain the declared observed video "
            "publish-date range and must not be treated as the API search condition",
            "dateFilter values all/month/week/today/hour are intentionally not "
            "compiled until separately measured",
        )
        return CompiledWindow(
            collector_id=self.collector_id,
            window_id=window.get("window_id"),
            collector_window_type="relative_duration",
            parameters={"dateFilter": _YEAR_FILTER},
            boundary_semantics="observed_range_consistent_with_measured_year_filter",
            exact=False,
            limitations=limitations,
            reference_time=format_datetime(reference_time),
            resolved_start=format_datetime(resolved_start),
            resolved_end_exclusive=format_datetime(resolved_end),
            requested_start=window.get("start"),
            requested_end_exclusive=window.get("end_exclusive"),
        )


def _resolve_year_filter(
    reference_time: datetime, tz: ZoneInfo
) -> tuple[datetime, datetime]:
    local_reference = reference_time.astimezone(tz)
    local_end = datetime(
        local_reference.year,
        local_reference.month,
        local_reference.day,
        tzinfo=tz,
    )
    local_start = local_end - timedelta(days=_YEAR_WINDOW_DAYS)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)
