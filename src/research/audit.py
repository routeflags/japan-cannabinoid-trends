"""G7 \u00a716 existing-study audit (non-destructive).

Contract source: ``docs/plans/20261013g.md`` \u00a716.

- Study boundaries are never altered: no directory is moved, merged or
  edited, and no raw file or old metadata file is written (P7).
- Every run hashes all files under ``datasets/*/data/raw`` before and after
  the read-only scan and reports ``raw_modified`` (always expected false).
- Facts come from observed files only: README/methodology text, run files,
  and the research catalog.  Research questions are quoted from READMEs;
  studies without a registered entry are reported as unregistered, never
  auto-registered.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from research import catalog as _catalog
from research import comparability as _gate
from validation.integrity import sha256_file
from validation.semantic import canonical_study_id

__all__ = ["AUDIT_VERSION", "build_study_inventory"]

AUDIT_VERSION = "1.0.0"


def _sha256_file(path: Path) -> str:
    return sha256_file(path)


def _raw_snapshot(datasets: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if datasets.is_dir():
        for path in sorted(p for p in datasets.rglob("*") if p.is_file()):
            posix = path.as_posix()
            # ``data/private`` is excluded by name, not by accident: the
            # ``data/raw`` prefix test below would otherwise admit a future
            # ``data/raw/private`` directory (AGENTS.md private data).
            if "private" in path.parts:
                continue
            if "data/raw" not in posix and "data\raw" not in posix:
                continue
            try:
                snapshot[str(path.relative_to(datasets.parent))] = _sha256_file(path)
            except OSError:
                continue
    return snapshot


def _readme_facts(study_dir: Path) -> dict:
    facts: dict = {"has_readme": False, "has_methodology": False, "title": None, "questions": []}
    readme = study_dir / "README.md"
    if readme.is_file():
        facts["has_readme"] = True
        try:
            text = readme.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and facts["title"] is None:
                facts["title"] = stripped[2:].strip()
            if stripped.startswith(">") and ("?" in stripped or "？" in stripped):
                facts["questions"].append(stripped.lstrip("> ").strip())
    if (study_dir / "methodology.md").is_file():
        facts["has_methodology"] = True
    return facts


def build_study_inventory(datasets_root, *, repo_root=None) -> dict:
    """Survey every study directory without modifying anything."""
    datasets = Path(datasets_root)
    root = Path(repo_root) if repo_root is not None else datasets.parent
    before = _raw_snapshot(datasets)

    catalog = _catalog.build_catalog(datasets, repo_root=root)
    registry = _registered(root)
    by_study: dict[str, list[dict]] = {}
    for entry in catalog["entries"]:
        if isinstance(entry, dict):
            # Raw records keep the study id they were collected under, so a
            # renamed study is still cited by its previous id there.  Group by
            # the id that is registered *now*.
            key = canonical_study_id(registry, str(entry.get("study_id")))
            by_study.setdefault(key, []).append(entry)

    studies: list[dict] = []
    study_dirs = sorted(p for p in datasets.iterdir() if p.is_dir()) if datasets.is_dir() else []
    for study_dir in study_dirs:
        study_id = study_dir.name
        entries = by_study.get(study_id, [])
        facts = _readme_facts(study_dir)
        run_files = sorted(study_dir.rglob("run_metadata.json"))
        # ``private`` is excluded by name, not by accident: it is gitignored, so
        # its contents are local-disk facts that differ between checkouts, and a
        # committed snapshot must be re-derivable from tracked files alone
        # (ISS-20261015-AUD-028).  The boundary itself is inventoried by
        # ``audit-private-catalog`` (existence only, contents never counted).
        data_files = [
            p
            for p in study_dir.rglob("*")
            if p.is_file() and "/data/" in p.as_posix() and "private" not in p.parts
        ]
        raw_dir = study_dir / "data" / "raw"
        raw_files = [p for p in raw_dir.rglob("*") if p.is_file()] if raw_dir.is_dir() else []
        has_manifest = any((p.parent / "artifact-manifest.json").is_file() for p in run_files)
        studies.append(
            {
                "study_id": study_id,
                "registered": study_id in {s.get("study_id") for s in registry},
                "title": facts["title"],
                "has_readme": facts["has_readme"],
                "has_methodology": facts["has_methodology"],
                "research_questions_quoted": facts["questions"],
                "run_count": len(run_files),
                "catalog_entry_count": len(entries),
                "layout": sorted(p.name for p in study_dir.iterdir()),
                "data_file_count": len(data_files),
                "has_data_raw": (study_dir / "data" / "raw").is_dir(),
                "data_raw_file_count": len(raw_files),
                "sources": sorted({str(e.get("source_id")) for e in entries}),
                "compound_ids": sorted({c for e in entries for c in (e.get("compound_ids") or [])}),
                "query_ids": sorted({q for e in entries for q in (e.get("query_ids") or [])}),
                "timeframes": sorted({str(e.get("timeframe")) for e in entries if e.get("timeframe")}),
                "measurement_ids": sorted({str(e.get("measurement_id")) for e in entries if e.get("measurement_id")}),
                "window_ids": sorted({str(e.get("window_id")) for e in entries if e.get("window_id")}),
                "has_artifact_manifest": has_manifest,
                "coverage": "unevidenced",
                "publication_status": "private_by_default",
            }
        )

    # Overlaps: compounds witnessed in more than one study (discovery-level).
    compound_studies: dict[str, list[str]] = {}
    for study in studies:
        for compound in study["compound_ids"]:
            compound_studies.setdefault(compound, []).append(study["study_id"])
    overlaps = [
        {"compound_id": compound, "study_ids": sorted(ids)}
        for compound, ids in sorted(compound_studies.items())
        if len(set(ids)) > 1
    ]

    # Comparability: gate the representative pair of each overlapping pair.
    pair_verdicts: list[dict] = []
    for overlap in overlaps:
        ids = overlap["study_ids"]
        for pos, left_id in enumerate(ids):
            for right_id in ids[pos + 1:]:
                left = _representative(by_study.get(left_id, []), overlap["compound_id"])
                right = _representative(by_study.get(right_id, []), overlap["compound_id"])
                if left is None or right is None:
                    continue
                verdict = _gate.check_cross_study_comparability(left, right)
                pair_verdicts.append(
                    {
                        "compound_id": overlap["compound_id"],
                        "left": left["catalog_entry_id"],
                        "right": right["catalog_entry_id"],
                        "status": verdict["status"],
                        "reasons": verdict["reasons"],
                    }
                )
    pair_verdicts.sort(key=lambda p: (p["compound_id"], p["left"], p["right"]))

    after = _raw_snapshot(datasets)
    combined = hashlib.sha256("".join(f"{k}={v}" for k, v in sorted(after.items())).encode()).hexdigest()
    return {
        "audit_version": AUDIT_VERSION,
        "study_count": len(studies),
        "studies": studies,
        "cross_study_compound_overlaps": overlaps,
        "representative_pair_verdicts": pair_verdicts,
        "raw_file_count": len(after),
        "raw_modified": before != after,
        "raw_combined_sha256": combined,
        "note": "non-destructive: study boundaries intact, raw and old metadata only read",
    }


def _registered(root: Path) -> list[dict]:
    try:
        import json

        document = json.loads((Path(root) / "metadata" / "studies" / "study-registry.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    studies = document.get("studies")
    return studies if isinstance(studies, list) else []


def _representative(entries: list[dict], compound_id: str) -> dict | None:
    for entry in sorted(entries, key=lambda e: str(e.get("run_id"))):
        if compound_id in (entry.get("compound_ids") or []):
            return entry
    return None
