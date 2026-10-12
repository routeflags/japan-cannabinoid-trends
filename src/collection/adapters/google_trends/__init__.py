"""Google Trends adapter package (MCP transport).  See ``adapter`` module."""

from collection.adapters.google_trends.adapter import (
    GoogleTrendsMcpAdapter,
    RecordedResponseTransport,
    SessionMcpTransport,
    build_adapter,
)

__all__ = [
    "GoogleTrendsMcpAdapter",
    "RecordedResponseTransport",
    "SessionMcpTransport",
    "build_adapter",
]
