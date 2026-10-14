"""The contract ledger must stay complete without being maintained by hand.

The ledger exists because the term 契約 covered five kinds of declaration and
nothing listed them (``docs/specs/contracts.md``).  A dependency on hand
editing would reproduce the problem it solves, so the properties below are
checked mechanically:

- every registered schema contract is in the ledger, with an owner context and
  a Cerberus group (adding a schema therefore forces the ownership decision);
- every contract names a declaration that exists in this checkout, so moving a
  declaration fails here instead of silently orphaning the entry;
- the document list covers the registry files ``validate-registries`` knows;
- gaps are derived from the declarations (an undeclared version is exactly the
  set of entries whose version is ``None``), never typed by hand.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validation.cli import METADATA_REGISTRY_FILES, REGISTRY_FILES
from validation.contract_ledger import (
    CONTEXTS,
    GAP_KINDS,
    GATE_CONTRACTS,
    KIND_GATE,
    KIND_INTERFACE,
    KIND_SCHEMA,
    _interface_contracts,
    build_contract_ledger,
)
from validation.schema_registry import SCHEMA_REGISTRY, SCHEMA_VERSIONS

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def ledger() -> dict:
    return build_contract_ledger(REPO_ROOT)


def test_every_registered_schema_contract_is_listed(ledger: dict) -> None:
    listed = {
        entry["contract_id"]
        for entry in ledger["contracts"]
        if entry["kind"] == KIND_SCHEMA
    }

    assert listed == set(SCHEMA_REGISTRY)


def test_every_contract_declares_owner_and_group(ledger: dict) -> None:
    """A new contract cannot be added without deciding who owns it."""

    for entry in ledger["contracts"]:
        assert entry["owner"] in CONTEXTS, entry
        assert entry["group"], entry
        assert entry["enforced_by"], entry
        assert entry["test"]


def test_schema_contracts_carry_the_registry_version(ledger: dict) -> None:
    for entry in ledger["contracts"]:
        if entry["kind"] == KIND_SCHEMA:
            assert entry["version"] == SCHEMA_VERSIONS[entry["contract_id"]]


def test_every_declaration_exists(ledger: dict) -> None:
    missing = [
        entry["declared_at"]
        for entry in ledger["contracts"]
        if not (REPO_ROOT / entry["declared_at"]).exists()
    ]

    assert missing == []


def test_every_contract_kind_is_present(ledger: dict) -> None:
    """Non-vacuity: an empty or mis-built ledger must not pass."""

    kinds = {entry["kind"] for entry in ledger["contracts"]}
    by_kind = {
        kind: [e for e in ledger["contracts"] if e["kind"] == kind]
        for kind in (KIND_SCHEMA, KIND_INTERFACE, KIND_GATE)
    }

    assert kinds == {KIND_SCHEMA, KIND_INTERFACE, KIND_GATE}
    assert len(by_kind[KIND_SCHEMA]) == len(SCHEMA_REGISTRY)
    assert len(by_kind[KIND_INTERFACE]) == len(_interface_contracts())
    assert len(by_kind[KIND_GATE]) == len(GATE_CONTRACTS)


def test_documents_cover_the_validated_registry_files(ledger: dict) -> None:
    covered = {
        document["path"]
        for document in ledger["documents"]
        if document["kind"] == "registry_document"
    }

    for relative, _schema_id in REGISTRY_FILES:
        assert f"config/{relative}" in covered
    for relative, _schema_id in METADATA_REGISTRY_FILES:
        assert f"metadata/{relative}" in covered


def test_gaps_are_derived_from_the_declarations(ledger: dict) -> None:
    """Gaps must follow from a declaration, not from a hand-written list."""

    undeclared_versions = {
        entry["contract_id"]
        for entry in ledger["contracts"]
        if entry["version"] is None
    }
    reported = {
        gap["contract_id"]
        for gap in ledger["gaps"]
        if gap["kind"] == "version_undeclared"
    }

    assert reported == undeclared_versions
    assert {gap["kind"] for gap in ledger["gaps"]} <= GAP_KINDS
    assert ledger["summary"]["gap_count"] == len(ledger["gaps"])


def test_summary_counts_match_the_entries(ledger: dict) -> None:
    summary = ledger["summary"]

    assert summary["contract_count"] == len(ledger["contracts"])
    assert summary["document_count"] == len(ledger["documents"])
    assert sum(summary["by_kind"].values()) == summary["contract_count"]
    assert sum(summary["by_owner"].values()) == summary["contract_count"]
