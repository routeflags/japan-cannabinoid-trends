"""JSON documents in this repository must not contain duplicate keys.

Why: ``json.load`` silently keeps the last of a repeated key, so the second one is
data loss that no parser reports and no consumer can see.  It happened here —
``metadata/taxonomy/compound-taxonomy.skos.jsonld`` declared 24 English
``skos:prefLabel`` values as a *second* ``skos:prefLabel`` key per concept, so every
English preferred label was discarded when the file was read.  The published
exports (``exports/taxonomy/compound-taxonomy.ttl``) therefore carried **0** English
``prefLabel`` values while the source claimed 24, and the export-sync check in CI
could not notice because the exporters use plain ``json.load`` as well: they
reproduced the same loss faithfully.

That is the failure mode this module exists to make loud.  Multi-valued
language-tagged literals belong in an array, which is what the SKOS JSON-LD form
wants anyway:

.. code-block:: json

    "skos:prefLabel": [
      {"@value": "Major Phytocannabinoids", "@language": "en"},
      {"@value": "主要フィトカンナビノイド", "@language": "ja"}
    ]

The scan is read-only and reports the key, its multiplicity, and the enclosing
``skos:notation``/``@id`` when the containing object carries one, so a finding
points at a concept rather than at a line number nobody can act on.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["DUPLICATE_CONTEXT_KEYS", "find_duplicate_keys", "scan_json_text"]

#: Keys used to name the object a duplicate was found in.
DUPLICATE_CONTEXT_KEYS = ("skos:notation", "@id", "name")


def scan_json_text(text: str, *, origin: str = "") -> list[dict]:
    """Return one finding per duplicated key in ``text``.

    A finding is ``{"origin", "context", "key", "count"}``.  ``origin`` is echoed
    back so callers can attribute the finding to a file.  Raises
    :class:`json.JSONDecodeError` when the text is not valid JSON.
    """

    findings: list[dict] = []

    def hook(pairs):
        mapping = dict(pairs)
        seen: dict[str, int] = {}
        for key, _ in pairs:
            seen[key] = seen.get(key, 0) + 1
        duplicated = {key: count for key, count in seen.items() if count > 1}
        if duplicated:
            context = next(
                (
                    str(mapping[key])
                    for key in DUPLICATE_CONTEXT_KEYS
                    if key in mapping and not isinstance(mapping[key], (dict, list))
                ),
                "",
            )
            for key, count in sorted(duplicated.items()):
                findings.append(
                    {"origin": origin, "context": context, "key": key, "count": count}
                )
        return mapping

    json.loads(text, object_pairs_hook=hook)
    return findings


def find_duplicate_keys(path: str | Path) -> list[dict]:
    """Return duplicate-key findings for one JSON/JSON-LD file."""

    resolved = Path(path)
    return scan_json_text(resolved.read_text(encoding="utf-8"), origin=str(resolved))
