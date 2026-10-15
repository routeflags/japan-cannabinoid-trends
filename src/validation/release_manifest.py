"""Validate a clean release archive against a ``release-manifest-v1`` document.

Why this exists
---------------
ISS-20261015-REL-014: the release workflow knew *how* to build a clean
archive (``scripts/release/create-clean-archive.sh``) but nothing checked
*what* the archive contains before it goes to Zenodo.  Two X-identity
archives had already shipped (``10.5281/zenodo.23253840`` /
``10.5281/zenodo.23095153``), so the pre-upload gate must be mechanical.

What this answers (read-only; it never creates, publishes, or uploads):

1. What release identity is intended? (``release.version`` / ``tag`` /
   ``concept_doi``.)
2. Which archive is evaluated? (``archive.path``, overridable per call.)
3. Are the required paths present?
4. Are forbidden paths absent (manifest declaration *and* the canonical
   release policy)?
5. Is every archive entry inside the declared include roots?
6. Do the embedded CITATION / datapackage / README agree with the release
   identity?  Delegated to ``validation.release_archive_check.check_archive``
   (ISS-20261015-REL-015) -- the DOI/version/disallowed rules live there,
   not here.

Failure classes (for the CLI exit-code mapping):

- structural manifest defects -> caller treats as schema/config errors;
- archive content defects -> caller treats as data validation failures;
- an unreadable archive file -> reported as a single problem naming the
  path (the CLI maps a *missing* archive file to I/O before calling here).
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from validation.core import validate_document
from validation.release_archive_check import (
    DISALLOWED_EXACT,
    DISALLOWED_PREFIXES,
    check_archive,
)
from validation.schema_registry import get_schema_version
from validation.schemas.release import RELEASE_MANIFEST_SCHEMA

SCHEMA_ID = "release-manifest-v1"

#: Paths every clean archive must carry (the release-identity files read by
#: ``check_archive``).
DEFAULT_REQUIRED_PATHS = ("CITATION.cff", "README.md", "metadata/datapackage.json")

#: Mirror of ``INCLUDE_PATHS`` in ``scripts/release/create-clean-archive.sh``
#: and ``.github/workflows/release-zenodo.yml`` (v1.13 Study-scoped release:
#: ``cannabinoid-platform-trends`` only; legacy X studies stay out).  The
#: workflow owns the copy list; this tuple is the validation-side default used
#: by :func:`default_manifest`.  If the workflow ever widens its copy list,
#: validation fails closed (unexpected content) until the manifest default is
#: extended alongside it.
DEFAULT_INCLUDE_ROOTS = (
    "datasets/cannabinoid-platform-trends",
    "docs/audits/gt-summary.json",
    "docs/specs",
    "docs/acceptance-criteria.md",
    "docs/migration-plan.md",
    "publication",
    "src",
    "tests",
    "pyproject.toml",
    "metadata",
    "LICENSE",
    "CITATION.cff",
    "CHANGELOG.md",
    "README.md",
    "methodology.md",
)


def default_manifest(*, version: str, concept_doi: str, archive_path: str) -> dict:
    """Build the canonical manifest for a release (validation input only)."""
    return {
        "schema_version": get_schema_version(SCHEMA_ID),
        "release": {
            "version": version,
            "tag": f"v{version}",
            "concept_doi": concept_doi,
        },
        "archive": {
            "path": archive_path,
            "required_paths": list(DEFAULT_REQUIRED_PATHS),
            "include_roots": list(DEFAULT_INCLUDE_ROOTS),
            "disallowed_prefixes": list(DISALLOWED_PREFIXES),
            "disallowed_exact": sorted(DISALLOWED_EXACT),
        },
    }


def _flatten(errors: Any, prefix: str, out: list[str]) -> None:
    """Render nested Cerberus errors as deterministic ``path: message`` lines."""
    if isinstance(errors, dict):
        for key in sorted(errors, key=str):
            path = f"{prefix}.{key}" if prefix else str(key)
            _flatten(errors[key], path, out)
        return
    if isinstance(errors, list):
        for item in errors:
            if isinstance(item, (dict, list)):
                _flatten(item, prefix, out)
            else:
                out.append(f"{prefix}: {item}" if prefix else str(item))
        return
    out.append(f"{prefix}: {errors}" if prefix else str(errors))


def structural_problems(manifest: Any) -> list[str]:
    """Return structural defects of ``manifest``; empty list == well formed."""
    if not isinstance(manifest, dict):
        return ["manifest is not a JSON object"]
    problems: list[str] = []
    result = validate_document(manifest, RELEASE_MANIFEST_SCHEMA)
    if not result.valid:
        flattened: list[str] = []
        _flatten(result.errors, "", flattened)
        problems.extend(f"manifest schema: {line}" for line in flattened)
    try:
        expected_version = get_schema_version(SCHEMA_ID)
    except ValueError:  # pragma: no cover - registry always has this ID
        expected_version = ""
    if "schema_version" in manifest and manifest["schema_version"] != expected_version:
        problems.append(
            "manifest schema_version "
            f"{manifest['schema_version']!r} != contract version {expected_version!r}"
        )
    release = manifest.get("release")
    if isinstance(release, dict):
        version, tag = release.get("version"), release.get("tag")
        if (
            isinstance(version, str)
            and isinstance(tag, str)
            and tag != f"v{version}"
        ):
            problems.append(
                f"manifest release.tag {tag!r} != 'v' + version {version!r}"
            )
    archive = manifest.get("archive")
    if isinstance(archive, dict):
        declared_prefixes = archive.get("disallowed_prefixes") or []
        declared_exact = archive.get("disallowed_exact") or []
        if isinstance(declared_prefixes, list) and isinstance(declared_exact, list):
            for prefix in DISALLOWED_PREFIXES:
                if prefix not in declared_prefixes:
                    problems.append(
                        f"manifest omits canonical disallowed prefix: {prefix}"
                    )
            for exact in sorted(DISALLOWED_EXACT):
                if exact not in declared_exact:
                    problems.append(
                        f"manifest omits canonical disallowed path: {exact}"
                    )
    return sorted(problems)


def _normalize(name: str) -> str:
    """Strip the ``./`` prefix some zippers store (``zip -r out.zip .``)."""
    while name.startswith("./"):
        name = name[2:]
    return name


def _in_scope(entry: str, roots: list[str]) -> bool:
    """An entry is in scope when it equals a root or sits below one."""
    for root in roots:
        cleaned = root.strip().rstrip("/")
        if not cleaned or cleaned == ".":
            return True  # a repository-wide root covers everything
        if entry == cleaned or entry.startswith(cleaned + "/"):
            return True
    return False


def check_release_manifest(
    manifest: dict,
    *,
    archive: str | Path | None = None,
) -> list[str]:
    """Check the archive named by ``manifest`` (or ``archive``) read-only.

    Returns the sorted problem list; empty list == the archive matches the
    manifest and the existing release-identity rules.  Manifest structural
    defects are included so direct callers see one deterministic list; the
    CLI reports them with config/schema exit semantics instead.
    """
    problems = structural_problems(manifest)
    if not isinstance(manifest, dict):
        return problems
    release = manifest.get("release") if isinstance(manifest.get("release"), dict) else {}
    archive_block = manifest.get("archive") if isinstance(manifest.get("archive"), dict) else {}
    version = release.get("version")
    concept_doi = release.get("concept_doi")

    archive_path = Path(archive) if archive is not None else Path(archive_block.get("path", ""))
    try:
        with zipfile.ZipFile(archive_path) as zf:
            raw_names = zf.namelist()
    except FileNotFoundError:
        return sorted(problems + [f"archive not found: {archive_path}"])
    except (zipfile.BadZipFile, OSError) as error:
        return sorted(problems + [f"archive is not a readable zip: {archive_path} ({error.__class__.__name__})"])
    names = [_normalize(name) for name in raw_names]
    # Directory entries (trailing "/") carry no content; scope and policy
    # apply to the file entries they contain.
    files = [name for name in names if name and not name.endswith("/")]
    file_set = set(files)

    required = archive_block.get("required_paths") or []
    if isinstance(required, list):
        for path in sorted(set(map(str, required))):
            if path not in file_set:
                problems.append(f"required path missing from archive: {path}")

    declared_prefixes = archive_block.get("disallowed_prefixes") or []
    declared_exact = archive_block.get("disallowed_exact") or []
    if isinstance(declared_prefixes, list) and isinstance(declared_exact, list):
        prefix_tuple = tuple(str(prefix) for prefix in declared_prefixes)
        exact_set = {str(exact) for exact in declared_exact}
        for name in sorted(file_set):
            if name in exact_set or (prefix_tuple and name.startswith(prefix_tuple)):
                problems.append(f"disallowed path in archive: {name}")

    roots = archive_block.get("include_roots") or []
    if isinstance(roots, list) and all(isinstance(root, str) for root in roots):
        for name in sorted(file_set):
            if not _in_scope(name, roots):
                problems.append(f"archive path outside declared include roots: {name}")

    if isinstance(version, str) and isinstance(concept_doi, str):
        problems.extend(check_archive(str(archive_path), version, concept_doi))

    return sorted(set(problems))
