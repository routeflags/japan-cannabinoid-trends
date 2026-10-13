"""Shared JSON loading helper for the readers (read-only).

Every reader opens its target with ``encoding="utf-8"`` and never writes;
a malformed file raises :class:`ReaderError` instead of being repaired.
"""

from __future__ import annotations

import json
from pathlib import Path

from storage.contracts import ReaderError

__all__ = ["load_json"]


def load_json(path) -> object:
    """Parse a UTF-8 JSON document, raising ReaderError on any failure."""
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReaderError(
            f"JSON document cannot be read ({error.__class__.__name__})"
        ) from error
