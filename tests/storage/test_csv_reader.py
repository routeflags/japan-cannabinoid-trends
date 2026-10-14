"""CSV record reader contract (ART-009 / d.md §8).

The fixture is synthetic (``dataset_export_synthetic.csv``, labelled
``synthetic-*``) because a real dataset export carries third-party video
metadata and cannot be committed.  The encoding edge cases the reader fixes -
UTF-8 BOM, CRLF records, quoted fields with embedded newlines / commas /
doubled quotes, blank physical lines - are constructed in the tests so the
bytes are explicit rather than invisible in a fixture.
"""

import hashlib
import json
from pathlib import Path

import pytest

from storage.contracts import ArtifactDescriptor, ReaderError, UnsupportedRead
from storage.readers import get_reader
from storage.registry import ArtifactRegistry
from validation.storage_contract import check_artifact_registry, check_manifest_storage_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
SYNTHETIC = FIXTURES / "dataset_export_synthetic.csv"
REGISTRY_PATH = REPO_ROOT / "metadata" / "artifacts" / "artifact-registry.json"


def _reader():
    reader = get_reader("csv-record-reader")
    assert reader is not None
    return reader


def _descriptor(path, **overrides) -> ArtifactDescriptor:
    values = {
        "artifact_id": "test-artifact",
        "artifact_type": "raw_records",
        "format": "csv",
        "schema_id": "youtube-dataset-csv-v1",
        "path": str(path),
    }
    values.update(overrides)
    return ArtifactDescriptor(**values)


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# identity / registration
# ---------------------------------------------------------------------------


def test_csv_reader_is_registered_and_declares_its_contract():
    reader = _reader()
    assert reader.reader_id == "csv-record-reader"
    assert reader.reader_version == "1.0.0"
    assert reader.formats == ("csv",)
    assert reader.artifact_types == ("raw_records",)
    assert reader.read_modes == ("records",)


def test_registry_registers_the_csv_schema_for_an_implemented_reader():
    document = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry = ArtifactRegistry(document)
    assert check_artifact_registry(document) == []
    schema = registry.schema_entry("youtube-dataset-csv-v1")
    assert schema == {
        "schema_id": "youtube-dataset-csv-v1",
        "format": "csv",
        "artifact_types": ["raw_records"],
        "reader_id": "csv-record-reader",
        "record_count_mode": "data_rows",
    }
    assert registry.reader_is_active("csv-record-reader")
    assert get_reader("csv-record-reader") is not None


# ---------------------------------------------------------------------------
# happy path - the synthetic fixture
# ---------------------------------------------------------------------------


def test_synthetic_fixture_reads_as_records():
    reader = _reader()
    assert reader.validate(_descriptor(SYNTHETIC)) == []
    assert reader.count(_descriptor(SYNTHETIC)) == 3

    records = list(reader.read(_descriptor(SYNTHETIC)))
    assert [entry["record_index"] for entry in records] == [0, 1, 2]
    first = records[0]["record"]
    assert first["id"] == "synthetic-0001"
    assert first["input"] == "test keyword"
    assert records[2]["record"]["date"] == ""  # empty fields survive


def test_read_limit_yields_only_the_first_records():
    reader = _reader()
    records = list(reader.read(_descriptor(SYNTHETIC), limit=2))
    assert [entry["record_index"] for entry in records] == [0, 1]


def test_unknown_read_mode_is_refused():
    reader = _reader()
    with pytest.raises(UnsupportedRead):
        list(reader.read(_descriptor(SYNTHETIC), mode="points"))


# ---------------------------------------------------------------------------
# encoding semantics fixed by tests (BOM / CRLF / quoting / blank lines)
# ---------------------------------------------------------------------------

_HEADER = b"id,title,description,input"


def test_bom_crlf_and_quoted_fields(tmp_path):
    """The shape the Apify exports actually have: BOM + CRLF + quoted
    multiline fields with commas and doubled quotes."""
    body = (
        b"\xef\xbb\xbf" + _HEADER + b"\r\n"
        + b'synthetic-0001,"title one","line one\r\nline two, with comma and ""quotes""","A"\r\n'
        + b"\r\n"  # a blank physical line between records is not a record
        + b'synthetic-0002,"title two","plain","B"\r\n'
    )
    path = _write(tmp_path / "export.csv", body)

    reader = _reader()
    assert reader.validate(_descriptor(path)) == []
    assert reader.count(_descriptor(path)) == 2
    records = list(reader.read(_descriptor(path)))
    assert records[0]["record"]["id"] == "synthetic-0001"  # BOM stripped
    assert records[0]["record"]["description"] == 'line one\r\nline two, with comma and "quotes"'
    assert records[1]["record"]["description"] == "plain"


def test_count_is_records_not_physical_lines(tmp_path):
    """A single record whose quoted field wraps over many physical lines
    must count as one record, not as the line count."""
    multiline = "line\n" * 40
    body = f'id,note\nsynthetic-0001,"{multiline.strip()}"\n'
    path = _write(tmp_path / "wrapped.csv", body.encode("utf-8"))

    assert _reader().count(_descriptor(path)) == 1
    assert path.read_bytes().count(b"\n") > 1  # physical lines >> records


def test_lf_only_and_cr_only_and_no_final_newline(tmp_path):
    reader = _reader()
    for name, body in (
        ("lf.csv", b"id,note\n1,a\n2,b"),
        ("cr.csv", b"id,note\r1,a\r2,b\r"),
    ):
        path = _write(tmp_path / name, body)
        assert reader.validate(_descriptor(path)) == []
        assert reader.count(_descriptor(path)) == 2


def test_header_only_file_is_an_observed_zero(tmp_path):
    path = _write(tmp_path / "header_only.csv", b"id,note\n")
    reader = _reader()
    assert reader.validate(_descriptor(path)) == []
    assert reader.count(_descriptor(path)) == 0
    assert list(reader.read(_descriptor(path))) == []


def test_record_with_only_empty_fields_is_still_a_record(tmp_path):
    path = _write(tmp_path / "empty_fields.csv", b"id,note\n,\n")
    reader = _reader()
    assert reader.validate(_descriptor(path)) == []
    assert reader.count(_descriptor(path)) == 1
    assert list(reader.read(_descriptor(path)))[0]["record"] == {"id": "", "note": ""}


# ---------------------------------------------------------------------------
# refusals - fail closed, never repaired
# ---------------------------------------------------------------------------


def test_empty_file_is_refused_with_no_count(tmp_path):
    path = _write(tmp_path / "empty.csv", b"")
    reader = _reader()
    assert reader.validate(_descriptor(path)) == ["CSV file has no header record"]
    assert reader.count(_descriptor(path)) is None  # not an observed zero


def test_non_utf8_bytes_are_refused(tmp_path):
    path = _write(tmp_path / "bad_encoding.csv", b"id,note\n1,\xff\xfe2\n")
    reader = _reader()
    assert reader.validate(_descriptor(path)) != []
    assert reader.count(_descriptor(path)) is None


def test_duplicate_header_names_are_refused(tmp_path):
    path = _write(tmp_path / "duplicate.csv", b"id,id\n1,2\n")
    reader = _reader()
    violations = reader.validate(_descriptor(path))
    assert violations and "duplicate column names" in violations[0]
    with pytest.raises(ReaderError):
        list(reader.read(_descriptor(path)))


def test_ragged_record_is_refused(tmp_path):
    reader = _reader()
    short = _write(tmp_path / "short.csv", b"id,note\n1\n")
    long = _write(tmp_path / "long.csv", b"id,note\n1,2,3\n")
    for path in (short, long):
        violations = reader.validate(_descriptor(path))
        assert violations and "header declares" in violations[0]


def test_unclosed_quote_is_refused_as_ragged(tmp_path):
    """The csv module is lenient about unclosed quotes; the ragged check
    is what catches the resulting mis-parse."""
    path = _write(tmp_path / "unclosed.csv", b'id,note\n"1,a\n')
    violations = _reader().validate(_descriptor(path))
    assert violations != []


def test_missing_file_is_reported_not_crashed(tmp_path):
    reader = _reader()
    descriptor = _descriptor(tmp_path / "absent.csv")
    assert reader.validate(descriptor) == ["file does not exist"]
    assert reader.count(descriptor) is None
    with pytest.raises(ReaderError):
        list(reader.read(descriptor))


def test_reader_never_modifies_the_file():
    before = hashlib.sha256(SYNTHETIC.read_bytes()).hexdigest()
    reader = _reader()
    reader.validate(_descriptor(SYNTHETIC))
    reader.count(_descriptor(SYNTHETIC))
    list(reader.read(_descriptor(SYNTHETIC)))
    assert hashlib.sha256(SYNTHETIC.read_bytes()).hexdigest() == before


# ---------------------------------------------------------------------------
# storage contract integration (S6 / S7 / S8 / S9 on a declared csv artifact)
# ---------------------------------------------------------------------------


def _manifest(record_count):
    return {
        "schema_version": "1.0.0",
        "run_id": "20261010T135024Z-youtube-youtube-consistency",
        "artifacts": [
            {
                "artifact_id": "run-records",
                "path": SYNTHETIC.name,
                "artifact_type": "raw_records",
                "format": "csv",
                "schema_id": "youtube-dataset-csv-v1",
                "record_count": record_count,
                "layer": "raw",
                "completeness": "complete",
            }
        ],
    }


def _codes(issues):
    return [issue.code for issue in issues]


def test_declared_csv_artifact_passes_the_storage_contract():
    registry = ArtifactRegistry.load(REGISTRY_PATH)
    issues = check_manifest_storage_contract(
        _manifest(3), base_dir=FIXTURES, artifact_registry=registry
    )
    assert issues == []


def test_artifact_format_mismatch_is_detected():
    registry = ArtifactRegistry.load(REGISTRY_PATH)
    manifest = _manifest(3)
    manifest["artifacts"][0]["format"] = "json"
    issues = check_manifest_storage_contract(
        manifest, base_dir=FIXTURES, artifact_registry=registry
    )
    assert "ARTIFACT_FORMAT_MISMATCH" in _codes(issues)  # S6 is not vacuous


def test_record_count_mismatch_is_detected():
    registry = ArtifactRegistry.load(REGISTRY_PATH)
    issues = check_manifest_storage_contract(
        _manifest(4), base_dir=FIXTURES, artifact_registry=registry
    )
    assert "ARTIFACT_RECORD_COUNT_MISMATCH" in _codes(issues)  # S8 is not vacuous


def test_unregistered_schema_is_refused():
    registry = ArtifactRegistry.load(REGISTRY_PATH)
    manifest = _manifest(3)
    manifest["artifacts"][0]["schema_id"] = "no-such-schema-v1"
    issues = check_manifest_storage_contract(
        manifest, base_dir=FIXTURES, artifact_registry=registry
    )
    assert "ARTIFACT_READER_UNREGISTERED" in _codes(issues)  # S9 is not vacuous
