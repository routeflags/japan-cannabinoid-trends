"""Collection core and adapters (G1 vertical slice).

This package holds the platform-agnostic collection pipeline (``core``) and
the per-source adapters (``adapters``).  The core never embeds a platform
name (G1 P1: source agnostic); source-specific request logic lives in the
adapter packages and is addressed through the adapter contract in
``collection.core.contracts``.

Contracts and operating notes: ``docs/specs/collection-pipeline.md``.
"""
