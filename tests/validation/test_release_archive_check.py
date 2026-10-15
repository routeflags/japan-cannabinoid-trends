"""Release archive identity checks (ISS-20261015-REL-015).

A clean archive is immutable once published, so its embedded CITATION /
datapackage / README must already agree with the release it ships in.  The
check runs before upload; this module proves it rejects the two defects that
shipped in v1.13.0 / v1.13.1 (stale DOI, placeholder paths).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from validation.release_archive_check import check_archive

CONCEPT_DOI = "10.5281/zenodo.99999999"
STALE_DOI = "10.5281/zenodo.23253840"


def _archive(tmp_path: Path, *, version: str = "1.13.2",
             citation_doi: str = CONCEPT_DOI, extra: dict[str, str] | None = None,
             omit: tuple[str, ...] = ()) -> Path:
    path = tmp_path / "release.zip"
    files = {
        "CITATION.cff": (
            "cff-version: 1.2.0\n"
            f'version: "{version}"\n'
            "identifiers:\n"
            f'  - type: doi\n    value: "{citation_doi}"\n'
            "preferred-citation:\n"
            f'  version: "{version}"\n'
            f'  doi: "{citation_doi}"\n'
        ),
        "metadata/datapackage.json": __import__("json").dumps(
            {"version": version, "doi": citation_doi, "citation": f"Version {version}. DOI: {citation_doi}"}
        ),
        "README.md": f"[![DOI](https://zenodo.org/badge/1.svg)](https://doi.org/{citation_doi})",
    }
    for name, body in (extra or {}).items():
        files[name] = body
    with zipfile.ZipFile(path, "w") as zf:
        for name, body in files.items():
            if name not in omit:
                zf.writestr(name, body)
    return path


def test_consistent_archive_passes(tmp_path: Path) -> None:
    assert check_archive(str(_archive(tmp_path)), "1.13.2", CONCEPT_DOI) == []


def test_stale_doi_is_rejected(tmp_path: Path) -> None:
    """v1.13.1 shipped the previous DOI inside the archive (REL-015)."""
    archive = _archive(tmp_path, citation_doi=STALE_DOI)
    problems = check_archive(str(archive), "1.13.2", CONCEPT_DOI)
    assert any("CITATION.cff does not cite the expected concept DOI" in p for p in problems)
    assert any("datapackage.json does not cite" in p for p in problems)
    assert any("README.md badge" in p for p in problems)


def test_version_mismatch_is_rejected(tmp_path: Path) -> None:
    archive = _archive(tmp_path, version="1.12.0")
    problems = check_archive(str(archive), "1.13.2", CONCEPT_DOI)
    assert any("CITATION.cff version" in p for p in problems)
    assert any("datapackage.json version" in p for p in problems)


def test_disallowed_paths_are_rejected(tmp_path: Path) -> None:
    archive = _archive(
        tmp_path,
        extra={
            "datasets/youtube-consistency/data/raw/youtube/x.csv": "post",
            ".github/workflows/x.yml": "x",
            "agent.md": "x",
        },
    )
    problems = check_archive(str(archive), "1.13.2", CONCEPT_DOI)
    assert any("datasets/youtube-consistency/" in p for p in problems)
    assert any(".github/" in p for p in problems)
    assert any("agent.md" in p for p in problems)


def test_metadata_artifacts_path_is_legitimate(tmp_path: Path) -> None:
    """metadata/artifacts/ must not be mistaken for the removed artifacts/ dir."""
    archive = _archive(
        tmp_path, extra={"metadata/artifacts/artifact-registry.json": "{}"}
    )
    assert check_archive(str(archive), "1.13.2", CONCEPT_DOI) == []
