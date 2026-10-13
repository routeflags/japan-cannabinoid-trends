"""Artifact registry loading and resolution (d.md §7).

The registry document (``metadata/artifacts/artifact-registry.json``) maps
``schema_id`` / ``artifact_type`` / ``format`` to a ``reader_id``.  Loading
follows the repository convention for registries: a missing file disables
the corresponding checks (``None``), a malformed file is an error
(``ValueError``).

Resolution is fail closed: a named ``schema_id`` resolves only to its
explicit entry - it is never silently matched to a 'similar' schema, and a
reader that is not ``active`` or not implemented in ``storage.readers`` does
not resolve at all.
"""

from __future__ import annotations

import json
from pathlib import Path

from storage.readers import get_reader

__all__ = ["ArtifactRegistry"]


class ArtifactRegistry:
    """In-memory view of one ``artifact-registry-v1`` document."""

    def __init__(self, document: dict):
        self.version = document.get("schema_version") if isinstance(document, dict) else None
        readers = document.get("readers") if isinstance(document, dict) else None
        schemas = document.get("artifact_schemas") if isinstance(document, dict) else None
        self.readers = tuple(item for item in (readers or ()) if isinstance(item, dict))
        self.schemas = tuple(item for item in (schemas or ()) if isinstance(item, dict))
        self._reader_index = {
            item.get("reader_id"): item for item in self.readers if item.get("reader_id")
        }
        self._schema_index = {
            item.get("schema_id"): item for item in self.schemas if item.get("schema_id")
        }

    @classmethod
    def load(cls, path) -> "ArtifactRegistry | None":
        """Load the registry; missing -> None, malformed -> ValueError."""
        registry_path = Path(path)
        if not registry_path.is_file():
            return None
        try:
            document = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError(
                f"artifact registry cannot be read as JSON: {registry_path}"
            ) from error
        return cls(document)

    # -- lookups -----------------------------------------------------------

    def reader_entry(self, reader_id) -> dict | None:
        return self._reader_index.get(reader_id)

    def schema_entry(self, schema_id) -> dict | None:
        return self._schema_index.get(schema_id)

    def reader_is_active(self, reader_id) -> bool:
        entry = self.reader_entry(reader_id)
        return bool(entry) and entry.get("status") == "active"

    def reader_is_implemented(self, reader_id) -> bool:
        return get_reader(reader_id) is not None

    def reader_for(
        self,
        *,
        schema_id: str | None = None,
        artifact_type: str | None = None,
        format: str | None = None,
    ) -> str | None:
        """Resolve a reader_id, or None when the combination is not registered.

        A named ``schema_id`` must match its own entry (format / artifact_type
        must be covered by that entry).  Without a schema, the search falls
        back to the readers list and requires an explicit ``artifact_type``;
        the fallback resolves only when **exactly one** reader covers the
        (format, artifact_type) pair - an ambiguous type (e.g. ``raw_response``
        is covered by two readers) resolves to None rather than to a guess
        (d.md P3).
        """
        if schema_id is not None:
            entry = self.schema_entry(schema_id)
            if entry is None:
                return None
            if format is not None and entry.get("format") != format:
                return None
            types = entry.get("artifact_types") or ()
            if artifact_type is not None and artifact_type not in types:
                return None
            return entry.get("reader_id")
        if artifact_type is None:
            return None
        matches = []
        for reader in self.readers:
            if format is not None and format not in (reader.get("formats") or ()):
                continue
            if artifact_type not in (reader.get("artifact_types") or ()):
                continue
            matches.append(reader.get("reader_id"))
        if len(matches) != 1:
            return None
        return matches[0]
