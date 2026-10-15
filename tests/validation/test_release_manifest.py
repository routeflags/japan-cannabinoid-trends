"""Contract + behavior tests for the G6 release-manifest slice (ISS-20261015-REL-014).

All archives are synthetic zip fixtures in ``tmp_path``; no test touches
``release-archives/``, the network, or Zenodo.  The slice is validation-only:
several tests assert the inputs are byte-identical after the run.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from validation.cli import EXIT_CONFIG, EXIT_DATA, EXIT_IO, EXIT_OK, main
from validation.core import validate_document
from validation.release_archive_check import check_archive
from validation.release_manifest import (
    SCHEMA_ID,
    check_release_manifest,
    default_manifest,
    structural_problems,
)
from validation.schema_registry import get_schema, get_schema_version
from validation.schemas.release import RELEASE_MANIFEST_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_MANIFEST = REPO_ROOT / "scripts" / "release" / "make-release-manifest.py"

VERSION = "1.13.2"
CONCEPT_DOI = "10.5281/zenodo.23390594"
STALE_DOI = "10.5281/zenodo.23253840"

IN_SCOPE_EXTRA = {
    "src/validation/release_manifest.py": "x",
    "datasets/cannabinoid-platform-trends/data/processed/trend_observations.csv": "a,b\n1,2\n",
    "metadata/artifacts/artifact-registry.json": "{}",
    "tests/validation/test_release_manifest.py": "x",
    "publication/guide_cbx_rewrite.html": "x",
}


def _identity_files(*, version: str = VERSION, doi: str = CONCEPT_DOI) -> dict[str, str]:
    return {
        "CITATION.cff": (
            "cff-version: 1.2.0\n"
            f'version: "{version}"\n'
            "identifiers:\n"
            f'  - type: doi\n    value: "{doi}"\n'
            "preferred-citation:\n"
            f'  version: "{version}"\n'
            f'  doi: "{doi}"\n'
        ),
        "metadata/datapackage.json": json.dumps(
            {"version": version, "doi": doi, "citation": f"Version {version}. DOI: {doi}"}
        ),
        "README.md": f"[![DOI](https://zenodo.org/badge/1.svg)](https://doi.org/{doi})",
    }


def _zip(tmp_path: Path, files: dict[str, str], name: str = "release.zip") -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        for entry, body in files.items():
            zf.writestr(entry, body)
    return path


def _manifest_for(archive: Path) -> dict:
    return default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path=str(archive))


def _write_manifest(tmp_path: Path, manifest: dict, name: str = "manifest.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Schema registration + structure (AC1)
# ---------------------------------------------------------------------------


def test_schema_is_registered_under_its_id():
    assert get_schema("release-manifest-v1") is RELEASE_MANIFEST_SCHEMA
    assert SCHEMA_ID == "release-manifest-v1"
    assert get_schema_version("release-manifest-v1") == "1.0.0"


def test_default_manifest_passes_structure():
    manifest = default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path="x.zip")
    assert validate_document(manifest, RELEASE_MANIFEST_SCHEMA).valid is True
    assert structural_problems(manifest) == []


def test_make_release_manifest_script_emits_a_valid_manifest(tmp_path: Path):
    output = tmp_path / "generated.json"
    result = subprocess.run(
        [sys.executable, str(MAKE_MANIFEST), "--version", VERSION,
         "--concept-doi", CONCEPT_DOI, "--archive", "x.zip", "--output", str(output)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert validate_document(manifest, RELEASE_MANIFEST_SCHEMA).valid is True
    assert structural_problems(manifest) == []


def test_make_release_manifest_script_rejects_malformed_doi():
    result = subprocess.run(
        [sys.executable, str(MAKE_MANIFEST), "--version", VERSION,
         "--concept-doi", "not-a-doi", "--archive", "x.zip"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# Archive-vs-manifest behavior (AC2-AC5)
# ---------------------------------------------------------------------------


def test_valid_manifest_and_archive_pass(tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    assert check_release_manifest(_manifest_for(archive)) == []


def test_missing_required_path_fails(tmp_path: Path):
    files = {**_identity_files(), **IN_SCOPE_EXTRA}
    del files["metadata/datapackage.json"]
    archive = _zip(tmp_path, files)
    problems = check_release_manifest(_manifest_for(archive))
    assert any(
        "required path missing from archive: metadata/datapackage.json" in problem
        for problem in problems
    )


def test_disallowed_paths_fail(tmp_path: Path):
    archive = _zip(tmp_path, {
        **_identity_files(),
        **IN_SCOPE_EXTRA,
        ".github/workflows/release-zenodo.yml": "x",
        "datasets/cbx-social-trends/data/raw/x/records.json": "[]",
    })
    problems = check_release_manifest(_manifest_for(archive))
    assert any(".github/workflows/release-zenodo.yml" in problem for problem in problems)
    assert any("datasets/cbx-social-trends/" in problem for problem in problems)


def test_paths_outside_include_roots_fail(tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA, "unexpected/file.txt": "x"})
    problems = check_release_manifest(_manifest_for(archive))
    assert problems == ["archive path outside declared include roots: unexpected/file.txt"]


def test_stale_doi_and_version_mismatch_fail(tmp_path: Path):
    stale = _zip(tmp_path, {**_identity_files(doi=STALE_DOI), **IN_SCOPE_EXTRA}, name="stale.zip")
    problems = check_release_manifest(_manifest_for(stale))
    assert any("does not cite the expected concept DOI" in problem for problem in problems)
    old = _zip(tmp_path, {**_identity_files(version="1.12.0"), **IN_SCOPE_EXTRA}, name="old.zip")
    old_problems = check_release_manifest(_manifest_for(old))
    assert any("CITATION.cff version" in problem for problem in old_problems)
    assert any("datapackage.json version" in problem for problem in old_problems)


def test_manifest_check_delegates_to_the_archive_identity_check(tmp_path: Path):
    """The manifest gate is at least as strict as ``check_archive`` (REL-015).

    The workflow keeps both steps; this pins the new command to the existing
    rule instead of a divergent reimplementation.
    """
    archive = _zip(tmp_path, {
        **_identity_files(doi=STALE_DOI), **IN_SCOPE_EXTRA,
        ".github/workflows/x.yml": "x",
        "agent.md": "x",
    })
    baseline = check_archive(str(archive), VERSION, CONCEPT_DOI)
    assert baseline, "fixture must trip the existing identity check"
    problems = check_release_manifest(_manifest_for(archive))
    assert set(baseline) <= set(problems)


def test_metadata_artifacts_path_is_not_falsely_rejected(tmp_path: Path):
    """``metadata/artifacts/`` is legitimate; only top-level ``artifacts/`` is banned."""
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    assert check_release_manifest(_manifest_for(archive)) == []


def test_manifest_omitting_canonical_disallowed_prefix_is_structural(tmp_path: Path):
    manifest = _manifest_for(tmp_path / "release.zip")
    manifest["archive"]["disallowed_prefixes"].remove(".github/")
    assert structural_problems(manifest) == ["manifest omits canonical disallowed prefix: .github/"]


def test_malformed_manifest_is_structural():
    manifest = default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path="x.zip")
    del manifest["release"]
    assert any(problem.startswith("manifest schema:") for problem in structural_problems(manifest))

    bad_doi = default_manifest(version=VERSION, concept_doi="not-a-doi", archive_path="x.zip")
    assert any("concept_doi" in problem for problem in structural_problems(bad_doi))

    bad_version = default_manifest(version="1.13", concept_doi=CONCEPT_DOI, archive_path="x.zip")
    assert any("version" in problem for problem in structural_problems(bad_version))

    mistagged = default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path="x.zip")
    mistagged["release"]["tag"] = "v9.9.9"
    assert structural_problems(mistagged) == [f"manifest release.tag 'v9.9.9' != 'v' + version '{VERSION}'"]

    assert structural_problems(["not", "an", "object"]) == ["manifest is not a JSON object"]

    future = default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path="x.zip")
    future["schema_version"] = "2.0.0"
    assert any("contract version" in problem for problem in structural_problems(future))


def test_missing_archive_file_is_reported(tmp_path: Path):
    manifest = _manifest_for(tmp_path / "absent.zip")
    assert check_release_manifest(manifest) == [f"archive not found: {tmp_path / 'absent.zip'}"]


def test_archive_override_wins_over_manifest_path(tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    manifest = _manifest_for(tmp_path / "elsewhere.zip")
    assert check_release_manifest(manifest, archive=archive) == []


def test_check_is_deterministic_and_non_destructive(tmp_path: Path):
    archive = _zip(tmp_path, {
        **_identity_files(), **IN_SCOPE_EXTRA,
        ".github/workflows/release-zenodo.yml": "x",
        "unexpected/file.txt": "x",
    })
    manifest = _manifest_for(archive)
    before_zip, before_manifest = archive.read_bytes(), json.loads(json.dumps(manifest))
    first, second = check_release_manifest(manifest), check_release_manifest(manifest)
    assert first == second
    assert archive.read_bytes() == before_zip
    assert manifest == before_manifest


# ---------------------------------------------------------------------------
# CLI (AC6): exit codes, JSON report, --output, read-only
# ---------------------------------------------------------------------------


def test_cli_valid_manifest_exit_0_json(capsys, tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    manifest_path = _write_manifest(tmp_path, _manifest_for(archive))
    before = archive.read_bytes()
    code = main(["validate-release-manifest", "--file", str(manifest_path), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_OK
    assert report["schema_id"] == "release-manifest-v1"
    assert report["valid"] is True and report["problems"] == []
    assert report["archive"] == str(archive)
    assert "OK release-manifest-v1" in captured.err
    assert archive.read_bytes() == before  # read-only: the zip is untouched


def test_cli_text_mode_emits_no_stdout(capsys, tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    manifest_path = _write_manifest(tmp_path, _manifest_for(archive))
    code = main(["validate-release-manifest", "--file", str(manifest_path)])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert captured.out == ""
    assert "OK release-manifest-v1" in captured.err


def test_cli_content_failure_exit_1(capsys, tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA, "unexpected/file.txt": "x"})
    manifest_path = _write_manifest(tmp_path, _manifest_for(archive))
    code = main(["validate-release-manifest", "--file", str(manifest_path), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_DATA
    assert report["valid"] is False
    assert report["problems"] == ["archive path outside declared include roots: unexpected/file.txt"]
    assert "FAIL release-manifest-v1" in captured.err


def test_cli_malformed_manifest_exit_2(capsys, tmp_path: Path):
    manifest = default_manifest(version=VERSION, concept_doi=CONCEPT_DOI, archive_path="x.zip")
    del manifest["archive"]["required_paths"]
    manifest_path = _write_manifest(tmp_path, manifest)
    code = main(["validate-release-manifest", "--file", str(manifest_path), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == EXIT_CONFIG
    assert report["valid"] is False
    assert any(problem.startswith("manifest schema:") for problem in report["problems"])


def test_cli_missing_manifest_exit_3(capsys, tmp_path: Path):
    code = main(["validate-release-manifest", "--file", str(tmp_path / "absent.json")])
    captured = capsys.readouterr()
    assert code == EXIT_IO
    assert "cannot read manifest file" in captured.err


def test_cli_missing_archive_exit_3(capsys, tmp_path: Path):
    manifest_path = _write_manifest(tmp_path, _manifest_for(tmp_path / "absent.zip"))
    code = main(["validate-release-manifest", "--file", str(manifest_path)])
    captured = capsys.readouterr()
    assert code == EXIT_IO
    assert "cannot read archive file" in captured.err


def test_cli_output_file_and_determinism(capsys, tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    manifest_path = _write_manifest(tmp_path, _manifest_for(archive))
    output = tmp_path / "reports" / "manifest-report.json"
    first = main([
        "validate-release-manifest", "--file", str(manifest_path),
        "--format", "json", "--output", str(output),
    ])
    capsys.readouterr()
    second = main([
        "validate-release-manifest", "--file", str(manifest_path),
        "--format", "json", "--output", str(output),
    ])
    captured = capsys.readouterr()
    assert (first, second) == (EXIT_OK, EXIT_OK)
    assert captured.out == ""  # --output takes the JSON off stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["valid"] is True


def test_cli_archive_override(capsys, tmp_path: Path):
    archive = _zip(tmp_path, {**_identity_files(), **IN_SCOPE_EXTRA})
    manifest_path = _write_manifest(tmp_path, _manifest_for(tmp_path / "elsewhere.zip"))
    code = main([
        "validate-release-manifest", "--file", str(manifest_path),
        "--archive", str(archive), "--format", "json",
    ])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert json.loads(captured.out)["archive"] == str(archive)
