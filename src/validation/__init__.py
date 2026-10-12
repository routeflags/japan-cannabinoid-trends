"""Structural and semantic validation framework for the G1-G7 research
contracts.

Cerberus is used for structural validation only (required fields, types,
ranges, allowed values, nested structures, unknown fields) and is imported
exclusively by ``validation.core``.  The semantic layer (registry
references, temporal ordering, execution consistency, integrity / lineage,
comparability, publication, secret scanning) lives in dedicated modules and
only runs after structural validation succeeds.

Entry points:

- ``validation.core.validate_document`` - structural validation only;
- ``validation.pipeline.validate_full`` - structural + semantic + report;
- ``python -m validation.cli`` - CLI (validate / validate-study /
  validate-registries / validate-all / gate-plan / audit-legacy).

See ``docs/specs/validation-framework.md`` for the operating contract
(docs/plans/20261013h.md §2 and §20 for the original instructions).
"""

__version__ = "0.1.0"
