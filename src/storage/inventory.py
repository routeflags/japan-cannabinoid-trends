"""G4 §16 legacy artifact inventory (non-destructive).

Read-only walk over every artifact file under a datasets root:

- content-first identification via ``storage.sniff`` (a file name never
decides meaning);
- SHA-256 recorded for every artifact and re-checked after the scan
  (``raw_modified`` must stay ``false`` - the legacy raw data is only read);
- missing manifests are recorded as missing; nothing is reconstructed (P8);
- page sequences are summarised with *expected* pages (from run metadata
  periods when available) so that a missing page (取得失敗/未収集) is never
  reported as ``observed_zero`` (d.md §11, AGENTS.md missing-data rules).

The inventory covers files under ``*/data/**`` (all layers).  Run markers
(``run_metadata.json`` / ``artifact-manifest.json`` /
``quarantine-reason.json``) are read for context but are not artifacts; they
are hashed and listed as run facts instead.

Privacy: directories named ``private`` (anonymization mappings etc., see
AGENTS.md) are excluded unless ``include_private=True`` is requested
(``audit-artifacts --include-private``).  Only paths, sizes, hashes and
structural evidence are recorded - never record values.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from storage.registry import ArtifactRegistry
from storage.sniff import sniff_path
from validation.integrity import sha256_file

__all__ = ["INVENTORY_VERSION", "build_artifact_inventory"]

INVENTORY_VERSION = "1.0.0"

#: Files that are structure, not artifacts.
RUN_MARKER_NAMES = (
    "run_metadata.json",
    "artifact-manifest.json",
    "quarantine-reason.json",
)
EXCLUDED_FILE_NAMES = (".gitkeep", ".gitignore")
DEFAULT_EXCLUDED_DIRS = ("private",)

_MONTHLY_PAGE_RE = re.compile(r"^records_(\d{4})-(\d{2})\.json$")
_NUMBERED_PAGE_RE = re.compile(r"^page_(\d{4})\.json$")
#: Canonical weekly page name (``W01_2026-03-19.json``); variant files such as
#: ``W16_detail.json`` / ``W17_W20_full.json`` are separate artifacts, not
#: pages of the sequence.
_WEEKLY_PAGE_RE = re.compile(r"^W(\d{2})_\d{4}-\d{2}-\d{2}\.json$")
#: Yearly paginated searches: ``records_2016.json`` (page 1) and
#: ``records_2016_page2.json`` (continuations).
_YEARLY_PAGE_RE = re.compile(r"^records_(\d{4})(?:_page(\d+))?\.json$")
_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _display_path(path: Path, root: Path) -> str:
    """Repository-relative display path (same convention as the G3 audit)."""
    for base in (root.parent, root):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _iter_files(root: Path, include_private: bool) -> list[Path]:
    """Artifact scope: files under a ``data`` directory (all layers).

    README / methodology / journal documents outside ``data/`` are not
    storage artifacts and stay out of the inventory (d.md §16 covers stored
    artifacts; the study documents are curated by the librarian process).
    """
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FILE_NAMES:
            continue
        relative_parts = path.relative_to(root).parts
        if "data" not in relative_parts:
            continue
        if not include_private and any(
            part in DEFAULT_EXCLUDED_DIRS for part in relative_parts
        ):
            continue
        files.append(path)
    return files


def _resolve_reader(sniff, registry: ArtifactRegistry | None):
    """Return (reader_id, reader_registered) for a sniff result.

    ``reader_registered`` is None when there is nothing to resolve (no schema
    and no artifact type), and False when a schema/type is known but no active
    reader covers it.  The type-only fallback resolves uniquely or not at all
    (never to a guess - P3).
    """
    if registry is None:
        return None, None
    if sniff.schema_id:
        reader_id = registry.reader_for(
            schema_id=sniff.schema_id,
            artifact_type=sniff.artifact_type,
            format=sniff.format,
        )
    elif sniff.artifact_type:
        reader_id = registry.reader_for(
            artifact_type=sniff.artifact_type, format=sniff.format
        )
    else:
        return None, None
    if reader_id is None:
        return None, False
    registered = registry.reader_is_active(reader_id) and registry.reader_is_implemented(
        reader_id
    )
    return reader_id, registered


def _judgment(
    sniff,
    *,
    reader_registered,
    manifest_state: str,
    metadata_state: str,
) -> str:
    """d.md §16 judgment vocabulary (precedence documented in the audit md)."""
    if sniff.state == "unknown" or sniff.format == "unknown":
        return "unknown_format"
    if sniff.state == "ambiguous":
        return "ambiguous"
    if sniff.schema_id and reader_registered:
        return "recognized"
    if manifest_state == "missing" and metadata_state == "missing":
        return "missing_metadata"
    return "partially_recognized"


def _month_range(start_value, end_value) -> list[str] | None:
    start = _MONTH_RE.match(str(start_value)) if start_value else None
    end = _MONTH_RE.match(str(end_value)) if end_value else None
    if not start or not end:
        return None
    start_year, start_month = int(start.group(1)), int(start.group(2))
    end_year, end_month = int(end.group(1)), int(end.group(2))
    if (end_year, end_month) < (start_year, start_month):
        return None
    months = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return months


def _contiguous(indexes: list[int]) -> list[int] | None:
    if not indexes:
        return None
    low, high = min(indexes), max(indexes)
    return list(range(low, high + 1))


def _page_family(name: str):
    """Return (family, index) for a page-like file name, or None."""
    match = _MONTHLY_PAGE_RE.match(name)
    if match:
        return "monthly_pages", f"{match.group(1)}-{match.group(2)}"
    match = _NUMBERED_PAGE_RE.match(name)
    if match:
        return "numbered_pages", int(match.group(1))
    match = _WEEKLY_PAGE_RE.match(name)
    if match:
        return "weekly_pages", int(match.group(1))
    match = _YEARLY_PAGE_RE.match(name)
    if match:
        page = int(match.group(2) or 1)
        return "yearly_pages", f"{match.group(1)}-{page:03d}"
    return None


def _build_groups(file_entries: list[dict], run_documents: dict, root: Path) -> list[dict]:
    """Group page-like files per directory and evaluate completeness.

    ``missing`` is an absent-but-expected page (取得失敗/未収集): it is never
    folded into ``observed_zero``, which is a *present* page with zero items
    (d.md §11, AGENTS.md: zero observations and missing observations are
    different states).  A sequence without a known total is never reported
    ``complete`` (``expected_pages=null`` case).
    """
    families: dict[tuple[str, str], list[dict]] = {}
    for entry in file_entries:
        family = _page_family(Path(entry["path"]).name)
        if family is None:
            continue
        directory = str(Path(entry["path"]).parent)
        families.setdefault((directory, family[0]), []).append({**entry, "index": family[1]})

    groups = []
    for (directory, family), entries in sorted(families.items()):
        entries = sorted(entries, key=lambda item: item["index"])
        indexes = [item["index"] for item in entries]
        run_key = entries[0].get("run_directory")
        document = run_documents.get(run_key) or {}
        start = document.get("start_date") or document.get("period")
        end = document.get("end_date")
        expected = None
        basis = None
        if family == "monthly_pages":
            months = _month_range(start, end)
            if months:
                expected, basis = months, "run_metadata_period"
            else:
                contiguous = [f"{y:04d}-{m:02d}" for y, m in _sortable_months(indexes)]
                expected, basis = contiguous, "observed_range"
        elif family == "yearly_pages":
            # Per year, pages must run contiguously from page 1 to the
            # highest observed page.  A year with no file at all is *not*
            # flagged: annual coverage is not evidenced by the directory
            # alone (P8 - nothing is assumed about unobserved years).
            per_year: dict[str, list[int]] = {}
            for value in indexes:
                year, _, page = value.partition("-")
                per_year.setdefault(year, []).append(int(page))
            expected = [
                f"{year}-{page:03d}"
                for year in sorted(per_year)
                for page in range(1, max(per_year[year]) + 1)
            ]
            basis = "observed_range"
        else:
            contiguous = _contiguous(indexes)
            if contiguous and min(contiguous) == 1:
                expected, basis = contiguous, "observed_range"

        present = set(indexes)
        duplicate_indexes = sorted(
            value for value in present if indexes.count(value) > 1
        )
        missing = [index for index in (expected or []) if index not in present]
        zero_pages = [
            item["index"] for item in entries if item.get("record_count") in (0,)
        ]
        if duplicate_indexes:
            state = "partial"
            note = (
                "more than one file claims the same page index; the sequence "
                "is not a clean page set"
            )
        elif missing:
            state = "partial"
            note = (
                "missing pages are absent-but-expected (取得失敗/未収集), not "
                "observed zero; the sequence is never reported complete"
            )
        elif expected is not None and basis == "run_metadata_period":
            state = "complete"
            note = "expected pages derived from the run metadata period; none missing"
        else:
            state = "unverified"
            note = (
                "the expected total is unknown (no run period evidence); the "
                "observed sequence is contiguous but completeness is not claimed "
                "(d.md §11: expected_pages=null)"
            )
        groups.append(
            {
                "group_id": f"{directory}::{family}",
                "family": family,
                "directory": directory,
                "run_id": entries[0].get("run_id"),
                "expected_pages": len(expected) if expected is not None else None,
                "expected_basis": basis,
                "collected_pages": len(entries),
                "missing_pages": missing,
                "duplicate_pages": duplicate_indexes,
                "observed_zero_pages": zero_pages,
                "pagination_exhausted": None,
                "completeness_state": state,
                "note": note,
                "pages": [
                    {
                        "index": item["index"],
                        "path": item["path"],
                        "state": "observed_zero"
                        if item.get("record_count") == 0
                        else "observed_nonzero",
                        "item_count": item.get("record_count"),
                    }
                    for item in entries
                ],
            }
        )
    return groups


def _sortable_months(indexes: list[str]):
    months = []
    for value in indexes:
        match = _MONTH_RE.match(value)
        if match:
            months.append((int(match.group(1)), int(match.group(2))))
    return sorted(months)


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------


def build_artifact_inventory(
    datasets_root,
    *,
    artifact_registry: ArtifactRegistry | None = None,
    include_private: bool = False,
) -> dict:
    """Build the non-destructive artifact inventory for ``datasets_root``."""
    root = Path(datasets_root)
    files = _iter_files(root, include_private)
    marker_files = [path for path in files if path.name in RUN_MARKER_NAMES]
    artifact_files = [path for path in files if path.name not in RUN_MARKER_NAMES]

    run_dirs = {path.parent for path in marker_files if path.name == "run_metadata.json"}
    run_documents = {
        str(run_dir): (_load_json(run_dir / "run_metadata.json") or {}) for run_dir in run_dirs
    }
    #: Stable, location-independent key for every run directory (the audit
    #: must be reproducible from any checkout location; absolute paths are
    #: never recorded).
    run_display = {str(run_dir): _display_path(run_dir, root) for run_dir in run_dirs}

    def _run_context(path: Path):
        for parent in path.parents:
            if parent in run_dirs:
                return parent
            if parent == root:
                break
        return None

    # before-hashes cover every file the scan reads (artifacts + run markers).
    files_to_guard = artifact_files + marker_files
    hashes_before = {path: sha256_file(path) for path in files_to_guard}

    file_entries = []
    for path in artifact_files:
        sniff = sniff_path(path)
        run_dir = _run_context(path)
        document = run_documents.get(str(run_dir)) if run_dir is not None else {}
        manifest_state = "missing"
        metadata_state = "missing"
        run_id = None
        source_id = None
        if run_dir is not None:
            metadata_state = "present"
            manifest_state = (
                "present"
                if (run_dir / "artifact-manifest.json").is_file()
                else "missing"
            )
            run_id = document.get("run_id") or run_dir.name
            source_id = document.get("source_id") or document.get("source")
        reader_id, reader_registered = _resolve_reader(sniff, artifact_registry)
        notes = [f"content:{evidence}" for evidence in sniff.evidence]
        if ".bak" in path.name:
            notes.append("file:backup-copy")
        if sniff.declared_data_points is not None:
            notes.append(
                "summary:declares "
                f"data_points={sniff.declared_data_points}; no per-bucket values "
                "(never reconstructed - P8)"
            )
        if manifest_state == "missing":
            notes.append("legacy:no-manifest")
            notes.append("lineage:unknown")
        if reader_registered is False and sniff.schema_id:
            notes.append("reader:unregistered-or-inactive")
        file_entries.append(
            {
                "path": _display_path(path, root),
                "bytes": path.stat().st_size,
                "sha256": hashes_before[path],
                "format": sniff.format if sniff.format != "unknown" else None,
                "sniff_state": sniff.state,
                "artifact_type": sniff.artifact_type,
                "schema_id": sniff.schema_id,
                "contains_full_timeseries": sniff.contains_full_timeseries,
                "record_count": sniff.record_count,
                "declared_data_points": sniff.declared_data_points,
                "reader_id": reader_id,
                "reader_registered": reader_registered,
                "study_id": document.get("study_id"),
                "run_id": run_id,
                "source_id": source_id,
                "run_directory": run_display.get(str(run_dir)) if run_dir is not None else None,
                "metadata_state": metadata_state,
                "manifest_state": manifest_state,
                # P8: without a manifest there is nothing to verify against;
                # the state is recorded, never replaced by a fabricated hash.
                "verification": (
                    "manifest_present"
                    if manifest_state == "present"
                    else "unverifiable_no_manifest"
                ),
                "judgment": _judgment(
                    sniff,
                    reader_registered=reader_registered,
                    manifest_state=manifest_state,
                    metadata_state=metadata_state,
                ),
                "notes": notes,
            }
        )

    groups = _build_groups(
        file_entries,
        {run_display[key]: value for key, value in run_documents.items()},
        root,
    )

    run_entries = []
    for run_dir in sorted(run_dirs):
        document = run_documents.get(str(run_dir)) or {}
        directory = run_display[str(run_dir)]
        run_files = [
            entry
            for entry in file_entries
            if entry["run_directory"] == directory
        ]
        run_entries.append(
            {
                "run_id": document.get("run_id") or run_dir.name,
                "path": directory,
                "study_id": document.get("study_id")
                or (Path(directory).parts[1] if len(Path(directory).parts) > 1 else None),
                "source_id": document.get("source_id") or document.get("source"),
                "metadata_state": "present",
                "manifest_state": "present"
                if (run_dir / "artifact-manifest.json").is_file()
                else "missing",
                "verification": "manifest_present"
                if (run_dir / "artifact-manifest.json").is_file()
                else "unverifiable_no_manifest",
                "artifact_count": len(run_files),
                "sha256": hashes_before.get(run_dir / "run_metadata.json"),
                "lineage_note": "unknown: legacy run has no artifact manifest "
                "(P8: never reconstructed)"
                if not (run_dir / "artifact-manifest.json").is_file()
                else None,
            }
        )

    raw_modified = False
    for path in files_to_guard:
        if sha256_file(path) != hashes_before[path]:
            raw_modified = True

    def _count(entries, key):
        summary: dict[str, int] = {}
        for entry in entries:
            value = entry.get(key)
            if value is None:
                value = "none"
            summary[value] = summary.get(value, 0) + 1
        return dict(sorted(summary.items()))

    return {
        "audit_version": INVENTORY_VERSION,
        "profile": "g4_artifact_inventory",
        "spec": "docs/plans/20261013d.md \u00a716 (local plan; not tracked)",
        "target_root": _display_path(root, root),
        "scope": "datasets/**/data/** artifact files (run markers excluded)",
        "exclusions": {
            "file_names": list(EXCLUDED_FILE_NAMES),
            "run_markers": list(RUN_MARKER_NAMES),
            "directories": [] if include_private else list(DEFAULT_EXCLUDED_DIRS),
            "include_private": include_private,
        },
        "run_count": len(run_entries),
        "count": len(file_entries),
        "raw_modified": raw_modified,
        "judgment_summary": _count(file_entries, "judgment"),
        "format_summary": _count(file_entries, "format"),
        "artifact_type_summary": _count(file_entries, "artifact_type"),
        "manifest_summary": _count(file_entries, "manifest_state"),
        "sqlite_present": any(entry["format"] == "sqlite" for entry in file_entries),
        "sqlite_note": "SQLite stores are local-only in this repository (see "
        "docs/specs/validation-framework.md G4 section); absence in the audit "
        "scope is recorded as not-present, never as zero content",
        "groups": groups,
        "runs": run_entries,
        "files": file_entries,
    }
