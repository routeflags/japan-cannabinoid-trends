"""Freshness of every committed audit report under ``docs/audits/``.

Why this exists: the reports are the evidence a reviewer or citation consumer reads
when asking "is this study registered?", "what is tracked?", "where are the private
boundaries?".  Four of them had freshness tests and five did not, so two of them
were shipping stale facts: ``g7-study-inventory.json`` reported 7 of 9 studies as
``registered: false`` and ``g6-git-tracking-inventory.json`` had lost a tracked file.
A rule that only some reports follow is the same failure mode as a rule with no
execution at all, so the rule is now one registry covering all of them:

1. every committed ``docs/audits/*.json`` must be registered here, and
2. a registered *snapshot* must equal its own regenerated output, while
3. a registered *invocation record* must still describe the artifact it names
   and, when its review inputs are committed (``metadata/publication/``),
   reproduce from them as well.

Adding a new report therefore fails the suite until its regeneration command is
recorded, which is the point: the next report cannot silently become a snapshot
nobody re-derives.

The hand-written ``.md`` companions in the same directory are dated narratives, not
generated output, and are deliberately not part of this check (for example
``g7-study-inventory.md`` states "本スライスは 2 study", which was true on its date).
Other tests additionally assert semantic properties of individual reports (for
example ``test_storage_inventory_audit.py``); those are kept, and this module owns
the freshness question alone.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDITS_DIR = REPO_ROOT / "docs" / "audits"

SNAPSHOT = "snapshot"
INVOCATION_RECORD = "invocation_record"


@dataclass(frozen=True)
class Report:
    """One committed audit report and how to hold it to account."""

    path: str
    #: ``python -m`` argv prefix that regenerates the file (``--output`` appended).
    generator: tuple[str, ...] = ()
    kind: str = SNAPSHOT
    normalizer: str = "identity"
    #: For an invocation record: the artifact the recorded verdict was about.
    artifact_path: str = ""
    #: For an invocation record whose artifact was withdrawn: the committed review
    #: envelope that keeps the hash the verdict reviewed.  The artifact file is
    #: deliberately absent, so the hash is checked against the envelope instead of
    #: the disk (ISS-20261015-PUB-035).
    envelope: str = ""
    notes: str = ""


def _identity(document: dict) -> dict:
    return document


def _tracked_only(document: dict) -> dict:
    """Keep only the repository-derived part of the git tracking inventory.

    ``state_summary`` / ``extra_count`` / ``count`` mix in local-disk facts (an
    ``ignored`` or ``absent`` path depends on what exists in a given checkout, e.g.
    ``.venv`` or a gitignored ``docs/plans`` file), so they cannot be equal on two
    machines.  Whether a path is *tracked* is a repository fact, and that is what is
    verified.
    """

    return {
        "target_root": document.get("target_root"),
        "include_private": document.get("include_private"),
        "entries": [entry for entry in document.get("entries", []) if entry.get("tracked")],
    }


NORMALIZERS = {
    "identity": _identity,
    "tracked_only": _tracked_only,
}

REPORTS: tuple[Report, ...] = (
    Report("docs/audits/contract-ledger.json", ("validation.cli", "contract-ledger")),
    Report("docs/audits/g2-query-inventory.json", ("validation.cli", "audit-queries")),
    Report("docs/audits/gt-summary.json", ("processing.cli", "gt-summary")),
    Report("docs/audits/publication-contract.json", ("validation.cli", "audit-publication")),
    Report("docs/audits/g3-temporal-inventory.json", ("validation.cli", "audit-temporal")),
    Report("docs/audits/g4-storage-inventory.json", ("validation.cli", "audit-artifacts")),
    Report("docs/audits/g5-legacy-runs.json", ("validation.cli", "audit-legacy")),
    Report(
        "docs/audits/g5-provenance-assessment.json",
        ("validation.cli", "audit-provenance"),
    ),
    Report(
        "docs/audits/g6-git-tracking-inventory.json",
        ("validation.cli", "audit-git-tracking"),
        normalizer="tracked_only",
    ),
    Report(
        "docs/audits/g6-private-catalog.json",
        ("validation.cli", "audit-private-catalog"),
    ),
    Report(
        "docs/audits/g7-study-inventory.json",
        (
            "research.cli",
            "--repo-root",
            ".",
            "--datasets-root",
            "datasets",
            "audit-studies",
        ),
    ),
    Report(
        "docs/audits/g6-publication-eligibility.json",
        (
            "validation.cli",
            "gate-publication",
            "--artifact",
            "metadata/publication/x-cbx-202608-summary-anonymized/artifact.json",
            "--decision",
            "metadata/publication/x-cbx-202608-summary-anonymized/decision.json",
            "--evidence",
            "metadata/publication/x-cbx-202608-summary-anonymized/evidence.json",
        ),
        kind=INVOCATION_RECORD,
        artifact_path=(
            "datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv"
        ),
        envelope="metadata/publication/x-cbx-202608-summary-anonymized",
        notes=(
            "Records one G6 §10.2 publication gate invocation.  The review envelope "
            "(artifact descriptor / evidence / decision) is committed under "
            "metadata/publication/x-cbx-202608-summary-anonymized/, so the recorded "
            "verdict is checked both against the artifact hash it approves and "
            "against a re-run from its own inputs.  The artifact itself was "
            "withdrawn on 2026-10-15 (per-post X data is not published even "
            "anonymized), so the hash is checked against the envelope and the "
            "absence of the file is asserted."
        ),
    ),
    Report(
        "docs/audits/g6-youtube-hhbd-publication-eligibility.json",
        (
            "validation.cli",
            "gate-publication",
            "--artifact",
            "metadata/publication/youtube-hhbd-liquid-monthly-counts/artifact.json",
            "--decision",
            "metadata/publication/youtube-hhbd-liquid-monthly-counts/decision.json",
            "--evidence",
            "metadata/publication/youtube-hhbd-liquid-monthly-counts/evidence.json",
        ),
        kind=INVOCATION_RECORD,
        artifact_path=(
            "datasets/cannabinoid-raw-collection/data/processed/"
            "youtube_monthly_counts.csv"
        ),
        notes=(
            "Owner-approved, hash-pinned publication review for the HHBD liquid "
            "YouTube monthly aggregate only; the source raw is excluded."
        ),
    ),
)

_BY_KIND = {
    kind: tuple(r for r in REPORTS if r.kind == kind) for kind in (SNAPSHOT, INVOCATION_RECORD)
}


def _load(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def _regenerate(report: Report, output: Path) -> dict:
    argv = [sys.executable, "-m", *report.generator, "--output", str(output)]
    completed = subprocess.run(argv, cwd=REPO_ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, (
        f"regenerating {report.path} failed ({completed.returncode}): "
        f"{' '.join(argv)}\n{completed.stderr.strip()}"
    )
    assert output.is_file(), f"{report.path}: generator wrote no file"
    return json.loads(output.read_text(encoding="utf-8"))


def test_every_committed_report_is_registered() -> None:
    """A new report must be registered before it can be committed."""

    committed = {p.name for p in AUDITS_DIR.glob("*.json")}
    registered = {Path(r.path).name for r in REPORTS}
    assert committed == registered, (
        f"unregistered report(s): {sorted(committed - registered)}; "
        f"registered but absent: {sorted(registered - committed)}"
    )


@pytest.mark.parametrize(
    "report", _BY_KIND[SNAPSHOT], ids=[Path(r.path).stem for r in _BY_KIND[SNAPSHOT]]
)
def test_snapshot_regenerates_into_the_committed_file(report: Report, tmp_path: Path) -> None:
    normalizer = NORMALIZERS[report.normalizer]
    regenerated = normalizer(_regenerate(report, tmp_path / Path(report.path).name))
    committed = normalizer(_load(report.path))

    assert regenerated == committed, (
        f"{report.path} is stale: regenerate it with "
        f"`python -m {' '.join(report.generator)} --output {report.path}`"
    )


@pytest.mark.parametrize(
    "report",
    _BY_KIND[INVOCATION_RECORD],
    ids=[Path(r.path).stem for r in _BY_KIND[INVOCATION_RECORD]],
)
def test_invocation_record_still_describes_its_artifact(report: Report) -> None:
    """A recorded verdict must not survive the artifact it judged."""

    assert report.artifact_path, f"{report.path}: register the artifact it judged"
    recorded = _load(report.path)
    if report.envelope:
        # Withdrawn artifact: the file is gone by decision, so the reviewed hash is
        # pinned to the committed descriptor and the absence is asserted.
        descriptor = json.loads(
            (REPO_ROOT / report.envelope / "artifact.json").read_text(encoding="utf-8")
        )
        assert recorded["artifact_sha256"] == descriptor["sha256"], (
            f"{report.path} records sha256 {recorded['artifact_sha256']} but "
            f"{report.envelope}/artifact.json records {descriptor['sha256']}"
        )
        assert not (REPO_ROOT / report.artifact_path).exists(), (
            f"{report.artifact_path} is withdrawn but present; re-run gate-publication"
        )
        return
    current = hashlib.sha256((REPO_ROOT / report.artifact_path).read_bytes()).hexdigest()
    assert recorded["artifact_sha256"] == current, (
        f"{report.path} records sha256 {recorded['artifact_sha256']} but "
        f"{report.artifact_path} is now {current}; re-run gate-publication"
    )


@pytest.mark.parametrize(
    "report",
    _BY_KIND[INVOCATION_RECORD],
    ids=[Path(r.path).stem for r in _BY_KIND[INVOCATION_RECORD]],
)
def test_invocation_record_reproduces_from_its_committed_inputs(
    report: Report, tmp_path: Path
) -> None:
    """An invocation whose review inputs are committed must not have drifted."""

    if not report.generator:
        pytest.skip(f"{report.path}: inputs are not committed; nothing to re-run")
    regenerated = _regenerate(report, tmp_path / Path(report.path).name)
    assert regenerated == _load(report.path), (
        f"{report.path} no longer matches a re-run from its committed inputs: "
        f"`python -m {' '.join(report.generator)} --output {report.path}`"
    )


def test_tracked_only_normalizer_drops_local_state() -> None:
    """The one normalizer must only remove facts that vary between checkouts."""

    document = {
        "target_root": "datasets",
        "include_private": False,
        "count": 3,
        "extra_count": 2,
        "state_summary": {"tracked": 1, "ignored": 1, "absent": 1},
        "entries": [
            {"path": "datasets/a.json", "tracked": True, "state": "tracked"},
            {"path": "tmp", "tracked": False, "state": "ignored"},
            {"path": "gone", "tracked": False, "state": "absent"},
        ],
    }
    normalized = _tracked_only(document)
    assert normalized == {
        "target_root": "datasets",
        "include_private": False,
        "entries": [{"path": "datasets/a.json", "tracked": True, "state": "tracked"}],
    }


def test_report_kinds_are_known() -> None:
    for report in REPORTS:
        assert report.kind in _BY_KIND, report.path
        assert report.normalizer in NORMALIZERS, report.path
        if report.kind == SNAPSHOT:
            assert report.generator, f"{report.path}: a snapshot needs a generator"
        else:
            # An invocation record must say what it judged; when its inputs are
            # committed it carries a generator too, and the re-run is checked.
            assert report.notes and report.artifact_path, report.path
