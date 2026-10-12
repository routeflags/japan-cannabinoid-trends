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

__all__ = [
    "AdapterUnavailable",
    "get_adapter_factory",
    "get_window_compiler",
    "registered_sources",
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
}


def registered_sources() -> list:
    """Source ids that have an adapter implementation."""
    return sorted(_FACTORIES)


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
