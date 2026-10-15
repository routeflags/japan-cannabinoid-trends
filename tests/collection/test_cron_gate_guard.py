"""The retired teiten cron route must stay fail closed (ISS-20261015-COL-019).

Background: ``cron_gate.sh`` gated hourly probabilistic collection into the
undocumented ``projects/`` side channel (which does not exist in this
repository), and the ``fetch_tiktok.sh`` / ``fetch_instagram.sh`` callees
created that directory via ``mkdir -p``.  The route is retired: the default
is refusal (exit 2, nothing created, no network), and even an explicit
``TEITEN_OUTDIR`` may never point at this repository's ``datasets/`` or
``projects/`` trees.

Scope: only the refusal paths and the guard ordering are exercised.  The
permissive path is deliberately taken only as far as the credential check —
this test never provides a token, so past the ``APIFY_TOKEN`` error the
scripts cannot call the Apify API (spending money and collecting real data).
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRON = REPO_ROOT / "src/collection/cron_gate.sh"
TIKTOK = REPO_ROOT / "src/collection/tiktok/fetch_tiktok.sh"
INSTAGRAM = REPO_ROOT / "src/collection/instagram/fetch_instagram.sh"

ISOLATED_ENV = {"PATH": "/usr/bin:/bin"}


def _run(script: Path, *args: str, env: dict | None = None):
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env if env is not None else dict(ISOLATED_ENV),
    )


def test_cron_gate_is_retired_and_writes_nothing() -> None:
    completed = _run(CRON)
    assert completed.returncode == 2, completed.stderr
    assert "retired" in completed.stderr
    assert "ISS-20261015-COL-019" in completed.stderr
    assert "adopt" in completed.stderr
    assert completed.stdout == ""
    assert not (REPO_ROOT / "projects").exists()


@pytest.mark.parametrize("script", [TIKTOK, INSTAGRAM], ids=["tiktok", "instagram"])
def test_fetch_default_output_is_refused_before_any_work(script: Path) -> None:
    completed = _run(script)
    assert completed.returncode == 2, completed.stderr
    assert "retired" in completed.stderr
    assert "TEITEN_OUTDIR" in completed.stderr
    assert "adopt" in completed.stderr
    assert completed.stdout == ""
    # refused before any directory creation, credential or network use
    assert "APIFY_TOKEN" not in completed.stderr
    assert not (REPO_ROOT / "projects").exists()


@pytest.mark.parametrize(
    "outdir",
    [
        "datasets/probe/run",
        "datasets",
        "projects/teiten_probe",
        "projects",
        "./datasets/probe/run",
        "sub/../datasets/probe/run",
    ],
    ids=[
        "datasets-relative",
        "datasets-itself",
        "projects-relative",
        "projects-itself",
        "dot-relative-datasets",
        "nested-dotdot-datasets",
    ],
)
@pytest.mark.parametrize("script", [TIKTOK, INSTAGRAM], ids=["tiktok", "instagram"])
def test_repo_tree_outputs_are_refused_even_when_explicit(script: Path, outdir: str) -> None:
    completed = _run(script, env={**ISOLATED_ENV, "TEITEN_OUTDIR": outdir})
    assert completed.returncode == 2, completed.stderr
    assert "adopt" in completed.stderr
    assert "APIFY_TOKEN" not in completed.stderr
    assert not (REPO_ROOT / "projects").exists()


@pytest.mark.parametrize("script", [TIKTOK, INSTAGRAM], ids=["tiktok", "instagram"])
def test_absolute_repo_tree_output_is_refused(script: Path) -> None:
    completed = _run(
        script,
        env={**ISOLATED_ENV, "TEITEN_OUTDIR": str(REPO_ROOT / "datasets" / "probe")},
    )
    assert completed.returncode == 2, completed.stderr


@pytest.mark.parametrize("script", [TIKTOK, INSTAGRAM], ids=["tiktok", "instagram"])
def test_explicit_scratch_output_reaches_only_the_credential_check(
    script: Path, tmp_path: Path
) -> None:
    """An explicit caller-owned outdir passes the guard — and stops at the
    credential check, before any network use (no token is provided here)."""
    scratch = tmp_path / "scratch-out"
    completed = _run(script, env={**ISOLATED_ENV, "TEITEN_OUTDIR": str(scratch)})
    assert completed.returncode == 1, completed.stderr
    assert "APIFY_TOKEN" in completed.stderr
    assert not (REPO_ROOT / "projects").exists()
