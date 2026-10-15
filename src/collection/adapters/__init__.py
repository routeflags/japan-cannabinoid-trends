"""Per-source collection adapters (G1 §4).

Each subpackage implements the common contract from
``collection.core.contracts`` for exactly one source.  This is the only
place where platform names are allowed (P1: the core stays source
agnostic).

The platform-name -> adapter factory mapping lives here so the core and the
CLI never import a vendor module directly.
"""

from __future__ import annotations

from collection.adapters.google_trends.adapter import build_adapter as _build_google_trends
from collection.adapters.google_trends.compiler import (
    GoogleTrendsWindowCompiler as _google_trends_window_compiler,
)
from collection.adapters.google_trends.mcp_session import (
    McpStdioSession as _google_trends_live_session,
)
from collection.adapters.youtube.compiler import (
    YouTubeApifyWindowCompiler as _youtube_apify_window_compiler,
)

__all__ = [
    "AdapterUnavailable",
    "get_adapter_factory",
    "get_live_session",
    "get_window_compiler",
    "registered_sources",
    "start_live_session",
]


class AdapterUnavailable(Exception):
    """The requested source has no adapter available in this environment."""


#: source_id -> factory(fixture=None, capabilities=None) -> adapter
_FACTORIES = {
    "google-trends": _build_google_trends,
}

#: collector_id -> window compiler class (G3 §6; one per collector, and only
#: where an implementation has actually been written — the resolver never
#: falls back to another collector's compiler).
_WINDOW_COMPILERS = {
    "google-trends-mcp": _google_trends_window_compiler,
    "youtube-apify-scraper": _youtube_apify_window_compiler,
}

#: source_id -> live MCP session class.  Live collection is opt-in (the CLI's
#: ``collect --live``); the session is built here so the core CLI never imports
#: a vendor module (P1).
_LIVE_SESSIONS = {
    "google-trends": _google_trends_live_session,
}


def get_live_session(source_id: str):
    """Return a live MCP session for ``source_id``, or raise.

    The caller starts it (``with session:``) and passes ``session.call`` to the
    adapter factory.  Collectors without a live session keep the fail-closed
    behaviour: the pipeline records a failed run, never fabricated data.
    """

    factory = _LIVE_SESSIONS.get(source_id)
    if factory is None:
        raise AdapterUnavailable(
            f"no live session is registered for source {source_id!r} "
            f"(available: {', '.join(sorted(_LIVE_SESSIONS)) or 'none'})"
        )
    return factory()


def registered_sources() -> list:
    """Source ids that have an adapter implementation."""
    return sorted(_FACTORIES)


def start_live_session(source_id: str):
    """Build *and start* a live MCP session for ``source_id``, or raise.

    Starting is part of this layer so the core CLI never imports a vendor
    module or its exception types (P1).  The session's own failure is surfaced
    as :class:`AdapterUnavailable`, because from the pipeline's point of view a
    collector that cannot be reached is simply unavailable - and the run must
    stop rather than continue with a transport that answers nothing.
    """

    session = get_live_session(source_id)
    try:
        session.start()
    except Exception as error:  # vendor edge: re-raised with context
        raise AdapterUnavailable(
            f"live session for {source_id!r} could not start: "
            f"{error.__class__.__name__}: {error}"
        ) from error
    return session


def get_window_compiler(collector_id):
    """Return a window compiler instance for ``collector_id`` or ``None``.

    Collectors without a registered compiler keep the pre-G3 behaviour
    (their adapters are responsible for their own period parameters).
    """
    factory = _WINDOW_COMPILERS.get(collector_id)
    return factory() if factory else None


def get_adapter_factory(source_id: str):
    """Return the adapter factory for ``source_id``.

    Raises :class:`AdapterUnavailable` when no adapter implementation exists
    yet - the collection must stop rather than simulate a collection.
    """
    try:
        return _FACTORIES[source_id]
    except KeyError:
        raise AdapterUnavailable(
            f"no adapter implementation is registered for source {source_id!r} "
            f"(available: {', '.join(registered_sources()) or 'none'})"
        ) from None
