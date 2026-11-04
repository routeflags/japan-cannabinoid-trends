"""Release history and DOI identity (ISS-20261105-REL-036).

Why this exists
---------------
Zenodo mints a DOI per uploaded version and keeps a concept DOI for the series.
The workflow returns the version DOI in its log, but the repository recorded
only the concept DOI, so "which DOI pins v1.14.3?" could only be answered by
reading a CI log that ages out.  ``metadata/releases.json`` is the committed
answer; this module is the one rule that keeps it honest.

The distinction the schema cannot express
-----------------------------------------
Cerberus checks the shape (both fields are DOIs).  These rules need two
documents and history, so they live here and reuse ``validate_document`` for the
structural part:

- a version DOI is not the concept DOI (a release pinned to the series DOI
  would silently resolve to whatever is latest);
- ``tag`` is ``v<version>`` and the versions are unique and increasing;
- every released version has a CHANGELOG entry;
- the declared version is not older than the newest release, and when it equals
  the newest release the recorded version DOI is that release's DOI.

A repository preparing the next release is a normal state: the declared version
is newer than the newest registry entry, and no DOI is recorded for it yet.
"""

from __future__ import annotations

from validation.core import validate_document
from validation.schemas.release import RELEASE_REGISTRY_SCHEMA


def _issue(code: str, pointer: str, detail: str) -> dict:
    return {"code": code, "pointer": pointer, "detail": detail}


def _as_tuple(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def check_release_registry(
    document,
    *,
    citation_version: str,
    datapackage_version: str,
    declared_concept_doi: str,
    changelog_versions: set[str],
) -> list[dict]:
    """Validate one release registry against the documents that declare it."""

    result = validate_document(document, RELEASE_REGISTRY_SCHEMA)
    issues = [
        _issue("RELEASE_REGISTRY_INVALID", pointer, detail)
        for pointer, messages in sorted(result.errors.items())
        for detail in messages
    ]
    if not result.valid:
        return issues

    if citation_version != datapackage_version:
        issues.append(
            _issue(
                "RELEASE_VERSION_DISAGREES",
                "/release",
                f"CITATION.cff says {citation_version}, "
                f"metadata/datapackage.json says {datapackage_version}",
            )
        )

    concept_doi = document["concept_doi"]
    if concept_doi != declared_concept_doi:
        issues.append(
            _issue(
                "RELEASE_CONCEPT_DOI_DISAGREES",
                "/concept_doi",
                f"registry says {concept_doi}, the dataset declares "
                f"{declared_concept_doi}",
            )
        )

    releases = document["releases"]
    seen: set[str] = set()
    previous = None
    for index, entry in enumerate(releases):
        pointer = f"/releases/{index}"
        version = entry["version"]
        if entry["version_doi"] == concept_doi:
            issues.append(
                _issue(
                    "RELEASE_VERSION_DOI_IS_CONCEPT",
                    pointer + "/version_doi",
                    f"{version} records the concept DOI {concept_doi}; a version "
                    "DOI must pin the upload",
                )
            )
        if entry["tag"] != f"v{version}":
            issues.append(
                _issue(
                    "RELEASE_TAG_MISMATCH",
                    pointer + "/tag",
                    f"tag {entry['tag']!r} does not match version {version}",
                )
            )
        if version in seen:
            issues.append(
                _issue("RELEASE_VERSION_DUPLICATE", pointer + "/version", version)
            )
        seen.add(version)
        if previous is not None and _as_tuple(version) <= _as_tuple(previous):
            issues.append(
                _issue(
                    "RELEASE_ORDER_INVALID",
                    pointer + "/version",
                    f"{version} does not follow {previous}",
                )
            )
        previous = version
        if changelog_versions and version not in changelog_versions:
            issues.append(
                _issue(
                    "RELEASE_NOT_IN_CHANGELOG",
                    pointer + "/version",
                    f"CHANGELOG has no [{version}] entry",
                )
            )

    newest = releases[-1]["version"]
    if _as_tuple(newest) > _as_tuple(citation_version):
        issues.append(
            _issue(
                "RELEASE_AHEAD_OF_DECLARATION",
                "/releases",
                f"newest release {newest} is newer than the declared "
                f"version {citation_version}",
            )
        )
    return issues
