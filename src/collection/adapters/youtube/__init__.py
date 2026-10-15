"""YouTube adapter package (Apify CSV handover + limited dateFilter compiler)."""

from collection.adapters.youtube.apify_csv import (
    DATE_FILTERS,
    YouTubeApifyCsvAdapter,
    YouTubeApifyCsvError,
    build_adapter,
    build_csv_run,
    build_declaration,
    collector_identity,
    stage_csv,
)
from collection.adapters.youtube.compiler import YouTubeApifyWindowCompiler
from collection.adapters.youtube.request import (
    ACTOR_ID,
    SORTING_ORDERS,
    YouTubeApifyRequestError,
    build_actor_input,
    plan_actor_input,
)

__all__ = [
    "ACTOR_ID",
    "DATE_FILTERS",
    "SORTING_ORDERS",
    "YouTubeApifyCsvAdapter",
    "YouTubeApifyCsvError",
    "YouTubeApifyRequestError",
    "YouTubeApifyWindowCompiler",
    "build_actor_input",
    "build_adapter",
    "build_csv_run",
    "build_declaration",
    "collector_identity",
    "plan_actor_input",
    "stage_csv",
]