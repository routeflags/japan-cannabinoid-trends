"""X API v2 search request planner (COL-016 safe slice, COL-030 request-only).

Builds the request a live X collection *would* send — and stops there.  This
module performs no I/O: no HTTP, no credentials (it never reads the
environment), no response handling.  Endpoint and method come from the
maintainer's in-repo specification (``ISS-20261015-COL-030`` §3.2:
``GET https://api.x.com/2/tweets/search/all`` with ``query`` /
``start_time`` / ``end_time``); nothing here re-derives API semantics from
outside the repository.

Fail-closed rules (one rule, applied uniformly):

- request facts (query text, absolute bounds) are caller-declared, never
  inferred from a payload;
- bounds must be explicit timezone-aware UTC instants with ``start < end``
  (naive or non-UTC values are refused, not converted);
- ``max_results``, when given, is passed through as a positive integer only —
  page-size bounds are unverified and sampling policy belongs to
  ``ISS-20261015-COL-032``;
- field selection (``tweet.fields``) is intentionally absent: which fields a
  future live collection may request is a product decision for ``COL-031``,
  and response fields must never leak into request-only evidence.
"""

from __future__ import annotations

from datetime import timedelta

from validation.windows import format_datetime, parse_datetime

__all__ = [
    "ENDPOINT",
    "METHOD",
    "XRequestError",
    "build_search_request",
    "plan_search_request",
]

#: X API v2 full-archive search (COL-030 §3.2, in-repo specification).
ENDPOINT = "https://api.x.com/2/tweets/search/all"
METHOD = "GET"

_ZERO_OFFSET = timedelta(0)


class XRequestError(ValueError):
    """A planned X request cannot be built (fail closed, nothing is sent)."""


def _require_query_text(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise XRequestError(
            "query_text is required: the search query is declared by the "
            "caller and never inferred from a payload"
        )
    return value


def _require_utc_instant(name: str, value) -> str:
    """Parse ``value`` and return it normalized to UTC ``...Z``.

    Naive datetimes are refused (a missing offset is not assumed to be UTC)
    and non-UTC offsets are refused (silently shifting a bound would move the
    requested period).
    """
    try:
        moment = parse_datetime(value)
    except ValueError as error:
        raise XRequestError(f"{name} must be an ISO 8601 datetime: {error}") from error
    if moment.utcoffset() != _ZERO_OFFSET:
        raise XRequestError(
            f"{name} must carry an explicit UTC offset (got {value!r}); "
            "non-UTC bounds fail closed instead of being converted"
        )
    return format_datetime(moment)


def _require_max_results(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise XRequestError(
            f"max_results must be a positive integer or be omitted "
            f"(got {value!r}; page-size bounds are unverified)"
        )
    return value


def build_search_request(
    *,
    query_text: str,
    start_time,
    end_time,
    max_results: int | None = None,
) -> dict:
    """Plan one X API v2 full-archive search request (nothing is sent).

    Returns ``{"endpoint", "method", "params"}`` where ``params`` holds
    only request-side facts: ``query`` / ``start_time`` / ``end_time`` (UTC
    ``...Z``) plus ``max_results`` when given.  No credentials, no response
    fields, no per-post records — the output is safe to keep as
    request-only evidence.
    """
    query = _require_query_text(query_text)
    start = _require_utc_instant("start_time", start_time)
    end = _require_utc_instant("end_time", end_time)
    if start >= end:
        raise XRequestError(
            "start_time must be earlier than end_time "
            f"(got {start_time!r} .. {end_time!r})"
        )
    params: dict = {"query": query, "start_time": start, "end_time": end}
    limit = _require_max_results(max_results)
    if limit is not None:
        params["max_results"] = limit
    return {"endpoint": ENDPOINT, "method": METHOD, "params": params}


def plan_search_request(plan: dict, *, max_results: int | None = None) -> dict:
    """Plan the X request for a collection ``plan`` (dry run, nothing sent).

    The query text comes from ``plan["query"]["text"]`` and the absolute
    bounds from ``plan["window"]["start" / "end_exclusive"]`` — both are
    the plan's own declared facts.  Anything missing fails closed.
    """
    if not isinstance(plan, dict):
        raise XRequestError("plan must be a mapping")
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    window = plan.get("window") if isinstance(plan.get("window"), dict) else {}
    return build_search_request(
        query_text=query.get("text"),
        start_time=window.get("start"),
        end_time=window.get("end_exclusive"),
        max_results=max_results,
    )
