"""G6 release manifest schema (ISS-20261015-REL-014).

Contract sources
----------------
- ``docs/plans/dev/20261015-release-manifest-validation-plan.md`` (AC1): the
  validation-only ``release-manifest-v1`` vertical slice.
- ``scripts/release/create-clean-archive.sh`` and
  ``.github/workflows/release-zenodo.yml`` ``INCLUDE_PATHS``: the release
  scope this manifest declares (a release is Study-scoped for
  ``cannabinoid-platform-trends`` since v1.13; X is outside the scope).
- ``validation.release_archive_check`` (ISS-20261015-REL-015): the canonical
  release-identity / disallowed-path rules.  This schema only declares the
  manifest *shape*; enforcement reuses that module
  (``validation.release_manifest``), so the rules exist in exactly one place.

Scope
-----
Structural validation only.  Not covered here:

- whether the declared paths exist in the archive ->
  ``validation.release_manifest.check_release_manifest``;
- release identity (version / concept DOI agreement) ->
  ``validation.release_archive_check.check_archive`` (reused, not repeated);
- publication approval -> ``validation.storage_policy`` (G6) / publication gate.

Interpretations recorded for review
------------------------------------
- ``release.tag`` is optional but, when present, must be ``v<version>`` (the
  GitHub Release tag convention used by ``release-zenodo.yml``).
- ``archive.include_roots`` accepts both directory scopes
  (``datasets/cannabinoid-platform-trends``) and single files (``LICENSE``):
  an archive entry is in scope when it equals a root or sits below one.
- ``archive.disallowed_prefixes`` / ``disallowed_exact`` are the manifest's
  own declaration of the forbidden scope.  ``validation.release_manifest``
  additionally requires the manifest to cover the canonical
  ``DISALLOWED_*`` constants, so a manifest cannot silently narrow the
  release policy.
"""

from __future__ import annotations

DOI_PATTERN = r"^10\.5281/zenodo\.[0-9]+$"
VERSION_PATTERN = r"^[0-9]+\.[0-9]+\.[0-9]+$"
TAG_PATTERN = r"^v[0-9]+\.[0-9]+\.[0-9]+$"

_PATH_LIST = {
    "type": "list",
    "schema": {
        "type": "string",
        "empty": False,
    },
}

RELEASE_MANIFEST_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "release": {
        "type": "dict",
        "required": True,
        "schema": {
            "version": {
                "type": "string",
                "required": True,
                "regex": VERSION_PATTERN,
            },
            "tag": {
                "type": "string",
                "regex": TAG_PATTERN,
            },
            "concept_doi": {
                "type": "string",
                "required": True,
                "regex": DOI_PATTERN,
            },
        },
    },
    "archive": {
        "type": "dict",
        "required": True,
        "schema": {
            "path": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "required_paths": {
                "type": "list",
                "required": True,
                "minlength": 1,
                "schema": {
                    "type": "string",
                    "empty": False,
                },
            },
            "include_roots": {
                "type": "list",
                "required": True,
                "minlength": 1,
                "schema": {
                    "type": "string",
                    "empty": False,
                },
            },
            "disallowed_prefixes": _PATH_LIST,
            "disallowed_exact": _PATH_LIST,
        },
    },
}
