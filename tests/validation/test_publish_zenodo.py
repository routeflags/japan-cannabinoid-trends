"""Zenodo publish flow (ISS-20261015-REL-015 / REL-016).

The release workflow must (a) never send a literal ``${VERSION}`` placeholder in
``related_identifiers`` and (b) never publish a version whose file set includes
an archive inherited from the previous version.  Both are checked here against a
stubbed HTTP layer, because the real calls need a Zenodo API key.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "release" / "publish-zenodo.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("publish_zenodo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def zenodo(monkeypatch):
    module = _load_module()
    calls: list[tuple[str, str, bytes | None]] = []

    def fake_request(method, url, *, api_key=None, data=None, content_type=None):
        calls.append((method, url, data))
        if url.endswith("/records/9999999"):
            return 200, json.dumps({"id": 9999999, "links": {"latest": "x"}})
        if url.endswith("/records/9999999/versions?sort=mostrecent&size=1"):
            return 200, json.dumps({"hits": {"hits": [{"id": 8888888}]}})
        if url.endswith("/actions/newversion"):
            return 202, json.dumps({"id": 7777777})
        if url.endswith("/depositions/7777777/files") and method == "GET":
            return 200, json.dumps(
                [
                    {"id": "inherit-1", "key": "japan-cannabinoid-trends-v1.13.1-clean.zip"},
                ]
            )
        if method == "DELETE":
            return 204, ""
        if url.endswith("/files") and method == "POST":
            return 201, json.dumps({"id": "new-1"})
        if url.endswith("/actions/publish"):
            return 202, json.dumps(
                {
                    "id": 7777777,
                    "doi": "10.5281/zenodo.7777777",
                    "conceptdoi": "10.5281/zenodo.9999999",
                    "metadata": {
                        "related_identifiers": [
                            {
                                "identifier": "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2",
                                "relation": "isSupplementTo",
                            }
                        ]
                    },
                }
            )
        return 200, "{}"

    monkeypatch.setattr(module, "_request", fake_request)
    return module, calls


def test_inherited_draft_files_are_deleted_before_upload(tmp_path, zenodo) -> None:
    module, calls = zenodo
    archive = tmp_path / "japan-cannabinoid-trends-v1.13.2-clean.zip"
    archive.write_bytes(b"zip")

    published = module.publish(
        str(archive),
        "v1.13.2",
        "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2",
        "key",
        "9999999",
        "10.5281/zenodo.9999999",
    )

    deletes = [c for c in calls if c[0] == "DELETE"]
    assert deletes, "inherited draft files must be deleted before upload"
    assert any("inherit-1" in c[1] for c in deletes)
    # The upload must happen after the deletion.
    methods = [c[0] for c in calls]
    assert methods.index("DELETE") < max(
        i for i, (m, u, _d) in enumerate(calls) if m == "POST" and u.endswith("/files")
    )
    assert published["conceptdoi"] == "10.5281/zenodo.9999999"


def test_publish_accepts_202(tmp_path, zenodo) -> None:
    """Zenodo answers 202 for the asynchronous publish action."""
    module, _calls = zenodo
    archive = tmp_path / "a.zip"
    archive.write_bytes(b"zip")
    module.publish(
        str(archive),
        "v1.13.2",
        "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2",
        "key",
        "9999999",
        "10.5281/zenodo.9999999",
    )


def test_metadata_url_is_fully_expanded(zenodo) -> None:
    module, _calls = zenodo
    metadata = module.build_metadata(
        "v1.13.2",
        "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2",
    )
    identifiers = [entry["identifier"] for entry in metadata["related_identifiers"]]
    assert "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2" in identifiers
    assert all("${VERSION}" not in value for value in identifiers)


def test_wrong_concept_family_fails_publish(tmp_path, zenodo) -> None:
    module, _calls = zenodo
    archive = tmp_path / "a.zip"
    archive.write_bytes(b"zip")
    with pytest.raises(module.PublishError, match="does not match"):
        module.publish(
            str(archive),
            "v1.13.2",
            "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/v1.13.2",
            "key",
            "9999999",
            "10.5281/zenodo.1111111",
        )
