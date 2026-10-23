"""G7 research CLI tests (\u00a713 target interface)."""

import json
from pathlib import Path

from research.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(*argv) -> int:
    return main(["--repo-root", str(REPO_ROOT), "--datasets-root", "datasets", *argv])


def test_catalog_find_command(capsys):
    assert _run("catalog-find", "--source", "google-trends") == 0
    out = capsys.readouterr().out
    assert "match(es)" in out


def test_compare_command(capsys):
    assert (
        _run(
            "compare",
            "--entry-a",
            "cannabinoid-raw-collection:20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m",
            "--entry-b",
            "cannabinoid-raw-collection:20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m",
        )
        == 0
    )
    assert "conditional" in capsys.readouterr().out


def test_compare_unknown_entry_is_config_error():
    assert _run("compare", "--entry-a", "nope", "--entry-b", "nope") == 2


def test_audit_studies_command_is_non_destructive(tmp_path):
    output = tmp_path / "inventory.json"
    assert _run("audit-studies", "--output", str(output)) == 0
    inventory = json.loads(output.read_text(encoding="utf-8"))
    assert inventory["study_count"] == 10
    assert inventory["raw_modified"] is False
