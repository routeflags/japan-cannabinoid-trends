"""Structural validation framework for the G1-G7 research data contracts.

Cerberus is used for structural validation only (required fields, types,
ranges, allowed values, nested structures, unknown fields). Registry
references, temporal ordering, hashes, lineage and git policy are handled by
dedicated validators in later implementation phases (docs/plans/20261013h.md
§2 and §20).

The public entry point is ``validation.core.validate_document``; schemas are
addressed by stable IDs through ``validation.schema_registry``.
"""

__version__ = "0.1.0"
