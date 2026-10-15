"""X API v2 absolute-window compiler (WIN-002 safe slice).

Compiles an explicit absolute UTC window into X API v2 request parameters
(``start_time`` / ``end_time``) only.  The endpoint takes absolute bounds —
documented in the maintainer's in-repo specification (``ISS-20261015-COL-030``
§3.2) — so this mapping is a documented-safe passthrough, not a measurement:
no live request is issued, implied, or required.

Request vs observed separation (owner direction 2026-10-15): the compiled
``start_time`` / ``end_time`` are the *request* bounds.  The observed range is
unknown until a collection runs and must be recorded separately — never
treated as the search condition.

``exact`` stays ``False``: the string mapping is exact, but boundary
inclusivity and result availability have no live verification.

Not registered in ``collection.adapters._WINDOW_COMPILERS``: the
``x-api-v2`` collector is not in ``config/collectors.json`` (registering it
is ``ISS-20261015-COL-031`` with ``validate-registries`` green).  Build this
compiler explicitly; ``compile-window`` CLI dispatch stays closed until then.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation.windows import (
    CompiledWindow,
    WindowCompilationError,
    format_datetime,
    parse_datetime,
)

__all__ = ["COLLECTOR_ID", "XApiWindowCompiler"]

#: Planned collector id (COL-031).  Not present in ``config/collectors.json``.
COLLECTOR_ID = "x-api-v2"


class XApiWindowCompiler:
    """Compiler mapping absolute windows onto X API v2 request bounds."""

    collector_id = COLLECTOR_ID

    def compile(
        self, window: dict, *, reference_time=None, capabilities=None
    ) -> CompiledWindow:
        """Compile an absolute window to ``start_time`` / ``end_time``.

        ``reference_time`` is optional: absolute bounds need no reference.  A
        provided reference must still be timezone-aware and is recorded, never
        used to shift the bounds.  Anything unrepresentable fails closed.
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

        recorded_reference = None
        if reference_time is not None:
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
            recorded_reference = format_datetime(reference_time)

        capabilities = capabilities if isinstance(capabilities, dict) else {}
        if capabilities.get("absolute_date_range") == "unsupported":
            raise WindowCompilationError(
                "absolute_window_unsupported",
                "the registry records absolute_date_range=unsupported for "
                f"{self.collector_id}",
            )

        limitations = (
            "start_time/end_time are the API request bounds; the observed "
            "range is unknown until a collection runs and must be recorded "
            "separately, never treated as the search condition "
            "(owner direction 2026-10-15)",
            "boundary inclusivity and result availability are unverified: no "
            "live request has been issued (exact=false)",
            "query text, field selection and pagination are not compiled "
            "here; they come from the plan (COL-031)",
        )
        return CompiledWindow(
            collector_id=self.collector_id,
            window_id=window.get("window_id"),
            collector_window_type="absolute_datetime",
            parameters={
                "start_time": format_datetime(start),
                "end_time": format_datetime(end),
            },
            boundary_semantics="request_bounds_only_no_observed_range",
            exact=False,
            limitations=limitations,
            reference_time=recorded_reference,
            resolved_start=format_datetime(start),
            resolved_end_exclusive=format_datetime(end),
            requested_start=window.get("start"),
            requested_end_exclusive=window.get("end_exclusive"),
        )
