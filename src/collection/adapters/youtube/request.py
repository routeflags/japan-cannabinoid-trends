"""YouTube Apify actor input planner (COL-016 safe slice).

Builds the actor input a live YouTube collection *would* send to the
``youtube-apify-scraper`` actor -- and stops there.  This module performs no
I/O: no HTTP, no credentials (it never reads the environment), no response
handling, no per-video rows.  Actor identity and the request vocabulary come
from in-repo evidence only:

- actor ``h7sDV53CddomktSi5`` (streamers/youtube-scraper):
  ``config/collectors.json`` ``youtube-apify-scraper.external_id`` and
  ``.github/skills/apify-youtube-scraper/SKILL.md``;
- ``dateFilter`` vocabulary (``all`` / ``hour`` / ``today`` / ``week`` /
  ``month`` / ``year``): :mod:`collection.adapters.youtube.apify_csv`
  ``DATE_FILTERS`` (single source of truth; reused here, never duplicated);
- ``sortingOrder`` values and ``maxResults`` / ``maxResultsShorts`` /
  ``maxResultStreams`` parameters: the skill's input schema table
  (``relevance`` / ``rating`` / ``date`` / ``views``; ``0`` excludes
  Shorts / streams in the skill's examples).

Fail-closed rules (one rule, applied uniformly):

- request facts (query text, ``date_filter``) are caller-declared, never
  inferred from a payload or a window.  The plan's absolute window is the
  *observed* publish-date range and is ignored for the input -- keyword
  search + absolute date range is impossible with this actor (skill:
  ``startUrls`` overrides ``searchQueries``; ``oldestPostDate`` is
  channel-URL-only), so absolute bounds must never leak into the input;
- ``date_filter="all"`` (the declaration vocabulary for the unbounded
  request, used by five of the six adopted COL-033 runs) maps to *omitting*
  ``dateFilter`` from the actor input -- the actor has no ``all`` value and
  the skill's filter-less example is the unbounded shape.  Emitting
  ``dateFilter="all"`` would invent actor behavior;
- ``max_results`` / Shorts / streams counts, when given, are passed through
  as integers only -- count limits belong to the still-blocked live-request
  control (COL-032), so no limit is enforced or implied here;
- channel-URL mode (``startUrls`` / ``oldestPostDate`` / ``sortVideosBy``)
  is never emitted: this planner is keyword-search-only.

Sending is out of scope: no token, no run start, no dataset fetch.  Live
transport stays fail-closed (``LIVE_TRANSPORT_UNIMPLEMENTED`` in
:mod:`collection.adapters.youtube.apify_csv`) until Apify cloud evidence
(PRV-013: actor input / run / dataset corroboration), an owner-supplied
token, and the live-request control (COL-032) are all present with explicit
approval.
"""

from __future__ import annotations

from collection.adapters.youtube.apify_csv import DATE_FILTERS

__all__ = [
    "ACTOR_ID",
    "SORTING_ORDERS",
    "YouTubeApifyRequestError",
    "build_actor_input",
    "plan_actor_input",
]

#: Apify actor for the adopted YouTube pattern (registry external_id + skill).
ACTOR_ID = "h7sDV53CddomktSi5"

#: ``sortingOrder`` vocabulary from the skill's input schema table.
#: Sorting *semantics* are unverified (no live measurement); values outside
#: this list fail closed instead of being passed through.
SORTING_ORDERS = ("relevance", "rating", "date", "views")


class YouTubeApifyRequestError(ValueError):
    """A planned YouTube actor input cannot be built (fail closed, nothing is sent)."""


def _require_query_text(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise YouTubeApifyRequestError(
            "query_text is required: the search query is declared by the "
            "caller and never inferred from a payload or a window"
        )
    return value


def _require_date_filter(value) -> str:
    if value not in DATE_FILTERS:
        raise YouTubeApifyRequestError(
            f"date_filter {value!r} is not in the evidenced request "
            f"vocabulary {list(DATE_FILTERS)}; unmeasured filter values "
            "fail closed (nothing was planned)"
        )
    return value


def _require_max_results(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise YouTubeApifyRequestError(
            f"max_results must be a positive integer or be omitted "
            f"(got {value!r}; count limits are unverified and belong to the "
            "blocked live-request control, not this planner)"
        )
    return value


def _require_non_negative(name: str, value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise YouTubeApifyRequestError(
            f"{name} must be a non-negative integer or be omitted "
            f"(got {value!r}; 0 excludes, per the skill's examples)"
        )
    return value


def _require_sorting_order(value):
    if value is None:
        return None
    if value not in SORTING_ORDERS:
        raise YouTubeApifyRequestError(
            f"sorting_order {value!r} is not one of {list(SORTING_ORDERS)} "
            "(nothing was planned)"
        )
    return value


def build_actor_input(
    *,
    query_text: str,
    date_filter: str,
    max_results: int | None = None,
    max_results_shorts: int | None = None,
    max_result_streams: int | None = None,
    sorting_order: str | None = None,
) -> dict:
    """Plan one ``youtube-apify-scraper`` actor input (nothing is sent).

    Returns ``{"actor_id", "input"}`` where ``input`` holds only
    request-side facts: ``searchQueries`` (single-element, one run is one
    query) plus ``dateFilter`` / ``maxResults`` / ``maxResultsShorts`` /
    ``maxResultStreams`` / ``sortingOrder`` when declared.  ``date_filter``
    ``"all"`` omits ``dateFilter`` (unbounded shape).  No credentials, no
    channel-URL parameters, no absolute bounds, no per-video rows -- the
    output is safe to keep as request-only evidence.
    """
    query = _require_query_text(query_text)
    date_filter = _require_date_filter(date_filter)
    limit = _require_max_results(max_results)
    shorts = _require_non_negative("max_results_shorts", max_results_shorts)
    streams = _require_non_negative("max_result_streams", max_result_streams)
    sorting = _require_sorting_order(sorting_order)
    actor_input: dict = {"searchQueries": [query]}
    if date_filter != "all":
        actor_input["dateFilter"] = date_filter
    if limit is not None:
        actor_input["maxResults"] = limit
    if shorts is not None:
        actor_input["maxResultsShorts"] = shorts
    if streams is not None:
        actor_input["maxResultStreams"] = streams
    if sorting is not None:
        actor_input["sortingOrder"] = sorting
    return {"actor_id": ACTOR_ID, "input": actor_input}


def plan_actor_input(
    plan: dict,
    *,
    date_filter: str,
    max_results: int | None = None,
    max_results_shorts: int | None = None,
    max_result_streams: int | None = None,
    sorting_order: str | None = None,
) -> dict:
    """Plan the actor input for a collection ``plan`` (dry run, nothing sent).

    The query text comes from ``plan["query"]["text"]`` -- the plan's own
    declared fact.  ``date_filter`` is an explicit caller argument, never
    derived from ``plan["window"]`` or a payload: the window is the observed
    publish-date range and must not be treated as the API search condition
    (owner direction 2026-10-15).  A plan without a declared query fails
    closed; a plan without a window still plans (windows are not inputs).
    """
    if not isinstance(plan, dict):
        raise YouTubeApifyRequestError("plan must be a mapping")
    query = plan.get("query") if isinstance(plan.get("query"), dict) else {}
    return build_actor_input(
        query_text=query.get("text"),
        date_filter=date_filter,
        max_results=max_results,
        max_results_shorts=max_results_shorts,
        max_result_streams=max_result_streams,
        sorting_order=sorting_order,
    )
