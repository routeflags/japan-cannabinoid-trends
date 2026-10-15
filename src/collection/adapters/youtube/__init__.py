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

__all__ = [
    "DATE_FILTERS",
    "YouTubeApifyCsvAdapter",
    "YouTubeApifyCsvError",
    "YouTubeApifyWindowCompiler",
    "build_adapter",
    "build_csv_run",
    "build_declaration",
    "collector_identity",
    "stage_csv",
]