"""Registry loading and lookup for the collection core (G1 §6 / §7).

Loading semantics are deliberately shared with the validation CLI
(``validation.cli.load_registries``): a missing registry file disables the
corresponding checks, a malformed one is a configuration error.  This keeps
one implementation of "where the registries live and what they mean".

The core only reads registries; it never writes them (G1 P2).
"""

from __future__ import annotations

from pathlib import Path

from validation.cli import ConfigError, load_registries as _load_registries
from validation.semantic import Registries

__all__ = [
    "ConfigError",
    "collectors_for_source",
    "find_collector",
    "find_source",
    "load_registries",
]


def load_registries(config_dir="config", metadata_dir="metadata") -> Registries:
    """Load source / collector (and other) registries from the given roots.

    Thin wrapper over the validation CLI loader (single implementation); accepts
    ``str`` or ``Path`` like the rest of this package.
    """
    return _load_registries(Path(config_dir), Path(metadata_dir))


def find_source(registries: Registries, source_id):
    """Return the source entry for ``source_id`` or ``None``."""
    for source in registries.sources:
        if isinstance(source, dict) and source.get("source_id") == source_id:
            return source
    return None


def collectors_for_source(registries: Registries, source_id) -> list:
    """Return every registered collector of ``source_id`` (any status)."""
    return [
        collector
        for collector in registries.collectors
        if isinstance(collector, dict) and collector.get("source_id") == source_id
    ]


def find_collector(registries: Registries, source_id, collector_id):
    """Return the collector entry for ``(source_id, collector_id)`` or
    ``None``.  A collector registered under a different source never matches
    (mis-wiring is reported by the capability gate)."""
    for collector in collectors_for_source(registries, source_id):
        if collector.get("collector_id") == collector_id:
            return collector
    return None
