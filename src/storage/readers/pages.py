"""JSON page reader (d.md §11 pagination).

Accepts two page shapes observed in the repository:

- a response wrapper object with an ``items`` array (yearly / monthly page
  files, ``youtube#searchListResponse`` shape);
- a plain JSON array (checkpoint ``pages/page_NNNN.json`` files).

A page file is *not* merged with its siblings here: merging belongs to the
interim layer (d.md §11 "統合処理は interim に出力する").  Absent pages are a
reporting concern (``storage.inventory``) - never a zero-read.
"""

from __future__ import annotations

from storage.contracts import (
    ArtifactDescriptor,
    ReaderError,
    StorageReader,
    UnsupportedRead,
)
from storage.readers._json import load_json

__all__ = ["JsonPageReader"]


def _page_items(document):
    """Return the item list for a page document, or None when not a page."""
    if isinstance(document, list):
        return document
    if isinstance(document, dict) and isinstance(document.get("items"), list):
        return document["items"]
    return None


class JsonPageReader(StorageReader):
    reader_id = "json-page-reader"
    reader_version = "1.0.0"
    formats = ("json",)
    artifact_types = ("page",)
    read_modes = ("page_items",)

    def validate(self, artifact: ArtifactDescriptor) -> list[str]:
        path = artifact.resolve()
        if not path.is_file():
            return ["file does not exist"]
        try:
            document = load_json(path)
        except ReaderError as error:
            return [str(error)]
        if _page_items(document) is None:
            return [
                "expected a JSON array or an object with an 'items' array "
                "(d.md §11)"
            ]
        return []

    def read(self, artifact: ArtifactDescriptor, *, mode: str | None = None, limit: int | None = None):
        if mode not in (None, "page_items"):
            raise UnsupportedRead(
                f"{self.reader_id} does not implement read mode {mode!r}"
            )
        document = load_json(artifact.resolve())
        items = _page_items(document)
        if items is None:
            raise ReaderError("not a page document")
        for index, record in enumerate(items):
            if limit is not None and index >= limit:
                break
            yield {"record_index": index, "record": record}

    def count(self, artifact: ArtifactDescriptor) -> int | None:
        try:
            items = _page_items(load_json(artifact.resolve()))
        except ReaderError:
            return None
        if items is None:
            return None
        return len(items)

    def meta(self, artifact: ArtifactDescriptor) -> dict:
        """Page-level facts recorded by the page itself (no guessing).

        ``total_results`` / ``results_per_page`` come from a
        ``pageInfo``-style block when the page carries one; a plain array
        page has no such evidence (None).
        """
        document = load_json(artifact.resolve())
        meta = {"items_key": "items" if isinstance(document, dict) else "array"}
        page_info = document.get("pageInfo") if isinstance(document, dict) else None
        if isinstance(page_info, dict):
            for key in ("totalResults", "resultsPerPage"):
                if isinstance(page_info.get(key), int):
                    meta["total_results" if key == "totalResults" else "results_per_page"] = page_info[key]
        return meta
