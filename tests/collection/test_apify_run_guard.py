"""The live Apify collector must not write raw data into ``datasets/``.

Background: ``apify_run.sh`` writes to whatever ``<out_base>`` the caller passes,
with no registry lookup, run identity or provenance, so a bypassing collection
could land in the dataset tree.  The framework-side rule lives in
``validation/new_runs.py`` (CI fails on a run that cannot satisfy the contract);
this test covers the collector-side half, which fails closed before doing any
work.

Scope: only the refusal path is exercised.  That check runs before the token check
and before any HTTP request, so the test cannot cause a live collection.  The
permissive path is deliberately not executed, because past the token check the
script calls the Apify API and a checkout with a real ``.env.d/apify.env`` would
spend money and collect real data.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "src/collection/apify_run.sh"


@pytest.mark.parametrize(
    "out_base",
    [
        "datasets/probe/run",
        "datasets/x",
        "./datasets/probe/run",
        "datasets/../datasets/probe/run",
        "sub/../datasets/probe/run",
        "datasets",
    ],
    ids=[
        "relative",
        "shallow",
        "dot-relative",
        "dotdot-escape",
        "nested-dotdot",
        "the-directory-itself",
    ],
)
def test_datasets_output_is_refused(out_base: str) -> None:
    completed = subprocess.run(
        ["bash", str(SCRIPT), "ACTOR_ID", "{}", out_base],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2, completed.stderr
    assert "datasets/" in completed.stderr
    assert "adopt --staged" in completed.stderr
    # refused before any credential or network use
    assert "APIFY_TOKEN" not in completed.stderr


def test_absolute_path_into_datasets_is_refused() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "ACTOR_ID",
            "{}",
            str(REPO_ROOT / "datasets" / "probe" / "run"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2, completed.stderr


def test_a_datasets_directory_outside_the_repository_is_allowed() -> None:
    """The guard is about this repository's dataset tree, not the word.

    ``/tmp/datasets/x`` must reach the credential check rather than being refused,
    or the guard would break unrelated scratch usage.  The refusal check exits
    before any credential or network use, so reaching the token error is as far as
    this deliberately goes.
    """

    completed = subprocess.run(
        ["bash", str(SCRIPT), "ACTOR_ID", "{}", "/tmp/datasets/x"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert completed.returncode == 1, completed.stderr
    assert "APIFY_TOKEN" in completed.stderr
    assert "adopt --staged" not in completed.stderr


def test_refusal_names_the_reason_and_the_way_forward() -> None:
    completed = subprocess.run(
        ["bash", str(SCRIPT), "ACTOR_ID", "{}", "datasets/probe/run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert "契約を満たせません" in completed.stderr
    assert completed.stdout == ""
