#!/usr/bin/env python3
"""Publish a release archive to Zenodo under the dataset's concept series.

Why this exists
---------------
Two defects shipped in v1.13.1 (ISS-20261015-REL-015 / REL-016):

1. every release created a *new* Zenodo record family, so the "series"
   concept DOI changed on every release while the archive cited a different
   (older) DOI;
2. the `related_identifiers` GitHub Release URL kept the literal
   ``${VERSION}`` placeholder because the JSON payload was built inside a
   single-quoted shell string.

This script replaces the inline shell implementation.  It:

- builds the deposition metadata with ``json`` (no escaping defects);
- maintains series continuity: when ``ZENODO_CONCEPT_RECORD_ID`` is set, it
  creates a *new version* of that record (same concept DOI), otherwise it
  creates a new record family;
- verifies after publishing that ``related_identifiers`` contains the exact
  expanded GitHub Release URL and exits 1 when it does not.

Environment:
  ZENODO_API_KEY           required unless --skip-upload
  ZENODO_CONCEPT_RECORD_ID optional; anchor the release to the series record

Exit codes: 0 success/skipped, 1 verification or Zenodo failure,
2 configuration error, 3 I/O error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ZENODO_API = "https://zenodo.org/api"
USER_AGENT = "japan-cannabinoid-trends-release"

TITLE = (
    "Japan Cannabinoid Platform Trends Dataset 2026: "
    "Google Trends and YouTube Evidence from Japan"
)
DESCRIPTION = (
    "A dataset release slice for comparing domestic cannabinoid trend "
    "observations across Google Trends and YouTube in Japan. Source-specific "
    "units are preserved rather than converted to one common scale. "
    "X (Twitter) is excluded from this release scope.\n\n"
    "日本国内における各カンナビノイド成分の国内トレンドと、Google Trends / "
    "YouTube で観測できる差異を記録するデータセット。source-specific units "
    "を維持する。X はこのリリーススコープから除外する。"
)
CREATORS = [
    {
        "name": "KATO, Kyoji",
        "orcid": "0009-0007-5131-0374",
        "affiliation": "Routeflags Co., Ltd.",
    }
]
KEYWORDS = [
    "cannabinoid", "CBD", "CBG", "CBN", "CBX", "CRDH", "CRDP", "H4CBH",
    "HHBD", "Google Trends", "YouTube", "Japan", "platform trends",
    "search interest", "longitudinal data",
]


class PublishError(RuntimeError):
    """Zenodo rejected the operation or returned an unusable response."""


def _request(method: str, url: str, *, api_key: str | None = None,
             data: bytes | None = None, content_type: str | None = None) -> tuple[int, dict | str]:
    headers = {"User-Agent": USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
            return response.status, body
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        return error.code, body


def _json(body: str, context: str) -> dict:
    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise PublishError(f"{context}: response is not JSON ({error}): {body[:400]}") from error


def build_metadata(version: str, github_release_url: str, title: str = TITLE,
                   description: str = DESCRIPTION) -> dict:
    """Zenodo deposition metadata; related_identifiers use fully expanded URLs."""
    return {
        "title": title,
        "upload_type": "dataset",
        "description": description,
        "creators": CREATORS,
        "keywords": KEYWORDS,
        "license": "cc-by-4.0",
        "version": version,
        "related_identifiers": [
            {
                "identifier": "https://www.thch-vape.shop/guide/substance/what-is-cbx",
                "relation": "isDescribedBy",
                "resource_type": "publication",
                "scheme": "url",
            },
            {
                "identifier": github_release_url,
                "relation": "isSupplementTo",
                "resource_type": "dataset",
                "scheme": "url",
            },
        ],
    }


def publish(archive_path: str, version: str, github_release_url: str,
             api_key: str, concept_record_id: str | None = None,
             expect_concept_doi: str | None = None) -> dict:
    """Create (or version) the deposition, upload, publish, verify.

    Returns the published record as a dict.  Raises :class:`PublishError`.
    """
    metadata = build_metadata(version, github_release_url)

    if concept_record_id:
        # Series continuity: new version of the existing concept record.
        status, body = _request(
            "GET",
            f"{ZENODO_API}/records/{concept_record_id}",
            api_key=api_key,
        )
        record = _json(body, f"GET /records/{concept_record_id}")
        if status != 200:
            raise PublishError(
                f"concept record {concept_record_id} not found (HTTP {status})"
            )
        # The documented endpoint is /deposit/depositions/<latest record
        # id>/actions/newversion, so resolve the latest published record id
        # first instead of guessing from the concept URL.
        latest_id = str(record.get("id") or concept_record_id)
        if latest_id == str(concept_record_id):
            status, body = _request(
                "GET",
                f"{ZENODO_API}/records/{concept_record_id}/versions"
                "?sort=mostrecent&size=1",
                api_key=api_key,
            )
            versions = _json(body, "GET versions")
            hits = (versions.get("hits") or {}).get("hits") or []
            if status != 200 or not hits:
                raise PublishError(
                    f"cannot resolve the latest version of concept record "
                    f"{concept_record_id} (HTTP {status})"
                )
            latest_id = str(hits[0]["id"])
        status, body = _request(
            "POST",
            f"{ZENODO_API}/deposit/depositions/{latest_id}/actions/newversion",
            api_key=api_key,
        )
        if status not in (200, 201, 202):
            raise PublishError(
                f"newversion of concept record {concept_record_id} failed "
                f"(HTTP {status}): {body[:400]}"
            )
        draft = _json(body, "POST newversion")
        deposition_id = str(draft["id"])
    else:
        status, body = _request(
            "POST",
            f"{ZENODO_API}/deposit/depositions",
            api_key=api_key,
            data=json.dumps({"metadata": metadata}).encode("utf-8"),
            content_type="application/json",
        )
        if status not in (200, 201, 202):
            raise PublishError(f"create deposition failed (HTTP {status}): {body[:400]}")
        deposition = _json(body, "create deposition")
        deposition_id = str(deposition["id"])

    # A newversion draft inherits the previous version's files.  A release
    # version must contain its own archive only, so remove everything the
    # draft inherited before uploading (REL-015 follow-up: v1.13.2 initially
    # shipped with the v1.13.1 archive alongside its own).
    status, body = _request(
        "GET",
        f"{ZENODO_API}/deposit/depositions/{deposition_id}/files",
        api_key=api_key,
    )
    if status == 200:
        for existing in _json(body, "GET draft files"):
            file_id = str(existing.get("id") or "")
            if not file_id:
                continue
            dstatus, _dbody = _request(
                "DELETE",
                f"{ZENODO_API}/deposit/depositions/{deposition_id}/files/{file_id}",
                api_key=api_key,
            )
            if dstatus not in (200, 202, 204):
                raise PublishError(
                    f"cannot remove inherited file {existing.get('key')!r} "
                    f"from draft {deposition_id} (HTTP {dstatus})"
                )

    # Upload the archive (multipart/form-data).
    with open(archive_path, "rb") as handle:
        payload = handle.read()
    boundary = "----jctreleaseboundary"
    filename = archive_path.rsplit("/", 1)[-1]
    body_bytes = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8") + payload + f"\r\n--{boundary}--\r\n".encode("utf-8")
    status, body = _request(
        "POST",
        f"{ZENODO_API}/deposit/depositions/{deposition_id}/files",
        api_key=api_key,
        data=body_bytes,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    if status not in (200, 201, 202):
        raise PublishError(f"file upload failed (HTTP {status}): {body[:400]}")

    # Update the metadata on the draft (the newversion draft inherits it, but
    # the version tag changes per release, so we set it explicitly).
    status, body = _request(
        "PUT",
        f"{ZENODO_API}/deposit/depositions/{deposition_id}",
        api_key=api_key,
        data=json.dumps({"metadata": metadata}).encode("utf-8"),
        content_type="application/json",
    )
    if status not in (200, 201, 202):
        raise PublishError(f"metadata update failed (HTTP {status}): {body[:400]}")

    # Publish.
    status, body = _request(
        "POST",
        f"{ZENODO_API}/deposit/depositions/{deposition_id}/actions/publish",
        api_key=api_key,
    )
    # Zenodo answers 202 Accepted when the publish action is processed
    # asynchronously; the response body already carries the published record.
    if status not in (200, 201, 202):
        raise PublishError(f"publish failed (HTTP {status}): {body[:400]}")
    published = _json(body, "publish")

    # Series verification: the published record must sit in the concept
    # family the archive cites (REL-015).  A fallback that creates a new
    # record family therefore fails loudly instead of shipping a release
    # whose archive points at a DOI Zenodo does not know.
    if expect_concept_doi:
        actual_concept = published.get("conceptdoi") or ""
        if actual_concept != expect_concept_doi:
            raise PublishError(
                f"published concept DOI {actual_concept!r} does not match the "
                f"DOI cited by the release archive {expect_concept_doi!r}; "
                "set ZENODO_CONCEPT_RECORD_ID to the series record"
            )

    # Permanent-fix verification: the stored related_identifiers must contain
    # the expanded GitHub Release URL (REL-016).  A placeholder such as
    # "${VERSION}" must fail the release rather than ship broken metadata.
    related = [
        entry.get("identifier", "")
        for entry in published.get("metadata", {}).get("related_identifiers", [])
    ]
    if github_release_url not in related:
        raise PublishError(
            "published record does not contain the expected GitHub Release URL "
            f"in related_identifiers: expected {github_release_url}, got {related}"
        )
    return published


def repair_record(record_id: str, keep_pattern: str, api_key: str) -> dict:
    """Delete every file of a published/editable record that does not match.

    Zenodo allows file edits on a record within 30 days of publication, which
    is exactly the window in which an inherited file from a newversion draft
    must be removed (v1.13.2 shipped alongside the inherited v1.13.1 archive).
    """
    status, body = _request(
        "GET",
        f"{ZENODO_API}/deposit/depositions/{record_id}/files",
        api_key=api_key,
    )
    if status != 200:
        raise PublishError(
            f"cannot list files of record {record_id} (HTTP {status}); "
            "the record may be older than 30 days or not editable"
        )
    files = _json(body, "GET files")
    kept, removed = [], []
    for entry in files:
        file_id = str(entry.get("id") or "")
        key = str(entry.get("key") or entry.get("filename") or "")
        if not file_id:
            continue
        if keep_pattern in key:
            kept.append(key)
            continue
        dstatus, _dbody = _request(
            "DELETE",
            f"{ZENODO_API}/deposit/depositions/{record_id}/files/{file_id}",
            api_key=api_key,
        )
        if dstatus not in (200, 202, 204):
            raise PublishError(
                f"cannot delete {key!r} from record {record_id} (HTTP {dstatus})"
            )
        removed.append(key)
    return {"record_id": record_id, "kept": kept, "removed": removed}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", required=True)
    parser.add_argument("--version", required=True, help="release tag, e.g. v1.13.2")
    parser.add_argument(
        "--github-release-url",
        help="https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/<tag>; "
        "derived from --version when omitted",
    )
    parser.add_argument(
        "--concept-record-id",
        help="Zenodo record id to version (series anchor); derived from the "
        "concept DOI suffix by the workflow",
    )
    parser.add_argument(
        "--expect-concept-doi",
        help="fail unless the published record sits in this concept family "
        "(derived from CITATION.cff concept DOI by the workflow)",
    )
    parser.add_argument(
        "--repair-record",
        help="repair mode: delete files not matching --keep-pattern from this record",
    )
    parser.add_argument(
        "--keep-pattern",
        default="",
        help="substring; files whose key does not contain it are deleted in repair mode",
    )
    parser.add_argument("--skip-upload", action="store_true", help="do not contact Zenodo")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    version = args.version
    tag = version if version.startswith("v") else f"v{version}"
    github_release_url = args.github_release_url or (
        "https://github.com/routeflags/japan-cannabinoid-trends/releases/tag/" + tag
    )
    api_key = os.environ.get("ZENODO_API_KEY", "")
    concept_record_id = args.concept_record_id or os.environ.get(
        "ZENODO_CONCEPT_RECORD_ID"
    ) or None

    if args.repair_record:
        if not api_key:
            print("ZENODO_API_KEY is not set; cannot repair", file=sys.stderr)
            return 2
        if not args.keep_pattern:
            print("--repair-record requires --keep-pattern", file=sys.stderr)
            return 2
        try:
            result = repair_record(args.repair_record, args.keep_pattern, api_key)
        except PublishError as error:
            print(f"zenodo repair failed: {error}", file=sys.stderr)
            print(json.dumps({"status": "failed", "record_id": args.repair_record, "error": str(error)}))
            return 1
        result["status"] = "success"
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.skip_upload:
        # Dry run: report what would be published.
        metadata = build_metadata(tag, github_release_url)
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "version": tag,
                    "github_release_url": github_release_url,
                    "concept_record_id": concept_record_id,
                    "metadata_title": metadata["title"],
                    "related_identifiers": [
                        entry["identifier"]
                        for entry in metadata["related_identifiers"]
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if not api_key:
        print("ZENODO_API_KEY is not set; skipping Zenodo upload", file=sys.stderr)
        print(json.dumps({"status": "skipped", "version": tag}))
        return 0

    try:
        published = publish(
            args.archive,
            tag,
            github_release_url,
            api_key,
            concept_record_id,
            args.expect_concept_doi,
        )
    except PublishError as error:
        print(f"zenodo publish failed: {error}", file=sys.stderr)
        print(json.dumps({"status": "failed", "version": tag, "error": str(error)}))
        return 1
    except OSError as error:
        print(f"zenodo publish failed: {error}", file=sys.stderr)
        print(json.dumps({"status": "failed", "version": tag, "error": str(error)}))
        return 3

    doi = published.get("doi", "")
    concept_doi = published.get("conceptdoi", "")
    result = {
        "status": "success",
        "version": tag,
        "doi": doi,
        "concept_doi": concept_doi,
        "record_id": published.get("id"),
        "url": f"https://doi.org/{doi}" if doi else "",
    }
    print(json.dumps(result, ensure_ascii=False))
    # GitHub Actions output file support.
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as handle:
            handle.write(f"zenodo_status=success\n")
            handle.write(f"doi={doi}\n")
            handle.write(f"concept_doi={concept_doi}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
