"""Reproducible processing stage (RAW -> PROCESSED) for this repository.

AGENTS.md requires derived data to be traceable through an executable
transformation rather than a manual spreadsheet step, and requires zero
observations to be distinguishable from missing ones.  The modules here hold the
transformations that produced the committed ``datasets/*/data/processed/``
artifacts, together with the audit that refuses to let an artifact exist without
either a verified re-derivation or an explicit non-reproducibility declaration.

- :mod:`processing.rulespec`  reads the content-classifier specification
- :mod:`processing.classify`  rule-based content classification (SKOS notations)
- :mod:`processing.anonymize` X summary -> anonymized summary derivation
- :mod:`processing.reproduce` re-derivation audit over ``data/processed/**``
- :mod:`processing.cli`       ``python -m processing.cli``

The legacy one-off scripts (``create_*_tables.py``, ``import_*_data.py``) remain
script-style and are not part of this package's public surface.
"""

__all__: list[str] = []
