"""Platform-agnostic collection core (G1 §4, §8, §9, §10, §13).

Modules:

- ``contracts``   adapter contract + result types
- ``registry``    source / collector registry loading (read-only)
- ``selection``   capability / selection gate (fail closed)
- ``provenance``  run manifest / artifact manifest building
- ``integrity``   L1 assembly for a staged run (catalog vs quarantine)
- ``pipeline``    collect / adopt orchestration + staging / quarantine moves
- ``cli``         ``python -m collection.core.cli collect|adopt``
"""
