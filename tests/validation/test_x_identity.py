"""X identity exposure gate tests.

Contract sources: ``docs/specs/sns-redistribution-assessment.md`` (the policy the
gate enforces), ``docs/data-dictionary.md`` section 1.1, AGENTS.md section on
social data, ``metadata/privacy/x-identity-denylist.json``, and the 2026-10-15
decision that per-post X data is not published even anonymized
(``ISS-20261015-COL-030`` 4.1).

The decisive test is :func:`test_repository_has_no_x_identity_exposure`: the gate
must pass on the real tracked tree - including the ``per_post_dataset`` rule, so a
post-level table cannot be tracked again without a finding.  The rest use a
synthetic denylist so that no real account handle is ever written into the test
suite.
"""

import json
from pathlib import Path

import pytest

from validation import x_identity
from validation.x_identity import audit_x_identity, digest_token

REPO_ROOT = Path(__file__).resolve().parents[2]

#: X handles are limited to letters, digits and underscore (max 15), so the
#: synthetic fixtures must be too or the tokenizer would split them.
SYNTHETIC_HANDLE = "syntheticaccount"
OTHER_HANDLE = "anotherflagger"


@pytest.fixture
def denylist(tmp_path: Path) -> Path:
    """A denylist of fictitious handles, with no real account in the suite."""

    salt = "test-salt/v1"
    document = {
        "schema_version": "1.0.0",
        "salt": salt,
        "account_count": 1,
        "digests": [digest_token(SYNTHETIC_HANDLE, salt)],
    }
    target = tmp_path / "denylist.json"
    target.write_text(json.dumps(document), encoding="utf-8")
    return target


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _audit(root: Path, denylist: Path, files: list[str]) -> dict:
    return audit_x_identity(root, denylist_path=denylist, files=files)


# ---------------------------------------------------------------------------
# the real repository
# ---------------------------------------------------------------------------


def test_repository_has_no_x_identity_exposure() -> None:
    report = audit_x_identity(REPO_ROOT)
    assert report["findings"] == []
    assert report["failures"] == []
    assert report["stale_acknowledgements"] == []
    assert report["account_count"] == 55
    # every tracked file is either scanned or reported as skipped
    assert report["scanned_count"] + len(report["skipped"]) > 0
    assert report["scanned_count"] >= 500


def test_the_withdrawn_per_post_summary_is_recorded_and_gone() -> None:
    """The file the gate used to point at is what the 2026-10-15 decision removed.

    Anonymization answered the identity rule but not the unit question: 147
    pseudonymized rows are still 147 posts, so the artifact is withdrawn
    (``ISS-20261015-PUB-035``) and no per-post representation replaces it.
    """

    from processing.reproduce import WITHDRAWN

    path = (
        "datasets/cbx-social-trends/data/processed/"
        "x_cbx_202608_summary_anonymized.csv"
    )
    assert path in WITHDRAWN
    assert WITHDRAWN[path].withdrawn_on == "2026-10-15"
    assert not (REPO_ROOT / path).exists()


# ---------------------------------------------------------------------------
# identity columns
# ---------------------------------------------------------------------------


def test_identity_column_is_flagged(tmp_path: Path, denylist: Path) -> None:
    _write(tmp_path, "data/out.csv", "tweet_id,username,text\n1,someone,hello\n")
    report = _audit(tmp_path, denylist, ["data/out.csv"])
    kinds = {f["kind"] for f in report["findings"]}
    assert "identity_column" in kinds
    assert "data/out.csv" in report["failures"]


def test_pseudonymised_post_payload_is_not_an_identity_column(tmp_path: Path, denylist: Path) -> None:
    """Pseudonymization answers the identity rule; it does not change the unit.

    The per-post rule is separate and is tested below.
    """

    _write(tmp_path, "data/out.csv", "tweet_id_hash,author_id,text_length\n1,author_001,7\n")
    report = _audit(tmp_path, denylist, ["data/out.csv"])
    assert report["findings"] == []


# ---------------------------------------------------------------------------
# per-post datasets (2026-10-15 decision)
# ---------------------------------------------------------------------------

PER_POST_HEADER = "tweet_id_hash,createdAt,author_id,week,views,likes,text_length"


def test_a_per_post_dataset_under_datasets_is_flagged(tmp_path: Path, denylist: Path) -> None:
    """Three or more post-record columns is a post-level table, anonymized or not."""

    relative = "datasets/stub-study/data/processed/out.csv"
    _write(
        tmp_path,
        relative,
        PER_POST_HEADER + "\n1,2026-08-03,author_001,W1,10,1,7\n",
    )

    report = _audit(tmp_path, denylist, [relative])

    assert [f["kind"] for f in report["findings"]] == ["per_post_dataset"]
    assert "tweet_id_hash" in report["findings"][0]["detail"]
    # containment, not equality: scanning one synthetic file leaves the real
    # repository's acknowledgements unmatched, which is reported as stale
    assert relative in report["failures"]


def test_json_post_records_are_flagged_by_their_keys(tmp_path: Path, denylist: Path) -> None:
    relative = "datasets/stub-study/data/raw/x/run/records.json"
    _write(
        tmp_path,
        relative,
        json.dumps([{"tweet_id": "1", "createdAt": "2026-08-03", "author_id": "a", "text_length": 7}]),
    )

    report = _audit(tmp_path, denylist, [relative])

    assert [f["kind"] for f in report["findings"]] == ["per_post_dataset"]


def test_an_aggregate_dataset_under_datasets_is_not_flagged(tmp_path: Path, denylist: Path) -> None:
    """The rule is about the unit: a weekly aggregate stays publishable."""

    relative = "datasets/stub-study/data/processed/weekly.csv"
    _write(tmp_path, relative, "week,topic_id,count\nW1,ingredient,12\n")

    assert _audit(tmp_path, denylist, [relative])["findings"] == []


def test_naming_the_post_fields_outside_datasets_is_not_a_dataset(tmp_path: Path, denylist: Path) -> None:
    """A document that names the fields is not a post-level dataset."""

    _write(tmp_path, "docs/notes.csv", PER_POST_HEADER + "\n")

    assert _audit(tmp_path, denylist, ["docs/notes.csv"])["findings"] == []


# ---------------------------------------------------------------------------
# post permalinks
# ---------------------------------------------------------------------------


def test_post_permalink_is_flagged(tmp_path: Path, denylist: Path) -> None:
    """A redistributed post permalink must be flagged, not just an identity column."""

    # Assembled at runtime so this test does not itself contain a permalink: the
    # gate scans the whole tracked tree, including this file, and a literal here
    # would (correctly) be reported.
    permalink = "https://x.com/" + "syntheticposter" + "/status/1234567890"
    _write(tmp_path, "notes.md", f"see {permalink}\n")
    report = _audit(tmp_path, denylist, ["notes.md"])
    assert [f["kind"] for f in report["findings"]] == ["post_permalink"]


def test_documentation_placeholder_permalink_is_allowed(tmp_path: Path, denylist: Path) -> None:
    _write(tmp_path, "schema.jsonld", '{"example": "https://x.com/user/status/1234567890"}')
    report = _audit(tmp_path, denylist, ["schema.jsonld"])
    assert report["findings"] == []


# ---------------------------------------------------------------------------
# known handles, acknowledgements and staleness
# ---------------------------------------------------------------------------


def test_known_handle_is_flagged(tmp_path: Path, denylist: Path) -> None:
    _write(tmp_path, "page.html", f"<td>{SYNTHETIC_HANDLE}</td>")
    report = _audit(tmp_path, denylist, ["page.html"])
    assert [f["kind"] for f in report["findings"]] == ["known_handle"]
    # the handle itself must not appear in the report
    assert SYNTHETIC_HANDLE not in json.dumps(report)


def test_at_prefixed_handle_is_flagged(tmp_path: Path, denylist: Path) -> None:
    _write(tmp_path, "notes.md", f"thanks @{SYNTHETIC_HANDLE}")
    report = _audit(tmp_path, denylist, ["notes.md"])
    assert [f["kind"] for f in report["findings"]] == ["known_handle"]


def test_unknown_handle_is_not_flagged(tmp_path: Path, denylist: Path) -> None:
    _write(tmp_path, "notes.md", f"mention @{OTHER_HANDLE}")
    report = _audit(tmp_path, denylist, ["notes.md"])
    assert report["findings"] == []


def test_acknowledgement_suppresses_a_justified_occurrence(
    tmp_path: Path, denylist: Path, monkeypatch
) -> None:
    salt = json.loads(denylist.read_text(encoding="utf-8"))["salt"]
    _write(tmp_path, "video.csv", f'"title {SYNTHETIC_HANDLE} review"')
    monkeypatch.setattr(
        x_identity,
        "ACKNOWLEDGED",
        {
            ("video.csv", digest_token(SYNTHETIC_HANDLE, salt)): (
                "YouTube video title, permitted by the redistribution assessment"
            )
        },
    )
    report = _audit(tmp_path, denylist, ["video.csv"])
    assert report["findings"] == []
    assert len(report["acknowledged"]) == 1
    assert report["stale_acknowledgements"] == []
    assert report["failures"] == []


def test_stale_acknowledgement_fails(tmp_path: Path, denylist: Path, monkeypatch) -> None:
    """An acknowledgement that no longer matches anything is itself wrong."""

    salt = json.loads(denylist.read_text(encoding="utf-8"))["salt"]
    _write(tmp_path, "video.csv", "no handle here")
    monkeypatch.setattr(
        x_identity,
        "ACKNOWLEDGED",
        {("video.csv", digest_token(SYNTHETIC_HANDLE, salt)): "stale by test"},
    )
    report = _audit(tmp_path, denylist, ["video.csv"])
    assert report["findings"] == []
    assert len(report["stale_acknowledgements"]) == 1
    assert report["failures"] == ["video.csv"]


# ---------------------------------------------------------------------------
# scanning surface
# ---------------------------------------------------------------------------


def test_suffixless_text_file_is_scanned(tmp_path: Path, denylist: Path) -> None:
    """A handle must not hide in a file with no extension (e.g. .gitignore)."""

    _write(tmp_path, ".gitignore", f"# {SYNTHETIC_HANDLE}\n")
    report = _audit(tmp_path, denylist, [".gitignore"])
    assert [f["kind"] for f in report["findings"]] == ["known_handle"]


def test_binary_file_is_reported_as_skipped(tmp_path: Path, denylist: Path) -> None:
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")
    report = _audit(tmp_path, denylist, ["blob.bin"])
    assert report["skipped"] == ["blob.bin"]
    assert report["scanned_count"] == 0


def test_digest_is_salted_case_insensitive() -> None:
    assert digest_token("SomeHandle", "s") == digest_token("somehandle", "s")
    assert digest_token("SomeHandle", "s") != digest_token("SomeHandle", "t")


def test_real_denylist_holds_digests_only() -> None:
    """The gate's own denylist must not carry plaintext handles."""

    document = json.loads(
        (REPO_ROOT / "metadata/privacy/x-identity-denylist.json").read_text(encoding="utf-8")
    )
    assert document["account_count"] == len(document["digests"]) == 55
    assert all(len(d) == 64 and set(d) <= set("0123456789abcdef") for d in document["digests"])
    assert "display names" in document["excluded"]
