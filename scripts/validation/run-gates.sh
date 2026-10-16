#!/usr/bin/env bash
# Validation gates for collection workflows (rollout plan P6-5).
#
# Single entry point so collection scripts never call validation internals
# directly (h.md §6: do not scatter the validation logic).  All commands are
# read-only with respect to raw data.
#
# Usage:
#   scripts/validation/run-gates.sh registries [--config-dir DIR --metadata-dir DIR]
#   scripts/validation/run-gates.sh plan <plan.json> [extra validate args]
#   scripts/validation/run-gates.sh run <run_metadata.json> [extra validate args]
#
# Exit codes (as defined for the CLI, h.md §13):
#   0 = pass / proceed / catalog    1 = fail -> do not adopt / do not start
#   2 = schema or configuration error   3 = file I/O error
#
# "run" is the post-collection L1 gate (structure + semantics + missingness +
# artifact integrity): exit 0 means the run is adoptable (catalog), a non-zero
# exit means it must be quarantined (kept raw, not promoted to the catalog).
# The script never moves or rewrites raw data itself (P6-2); staging /
# quarantine moves are done by the collection core
# (`python -m collection.core.cli collect|adopt`).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Local development runs through .venv (see docs/specs/validation-framework.md
# §2).  Fail fast with setup guidance when the interpreter is absent instead of
# falling back to system Python, which surfaces a misleading ModuleNotFoundError.
PYTHON="${ROOT}/.venv/bin/python"
if [ ! -x "${PYTHON}" ]; then
  echo "missing ${PYTHON}" >&2
  echo "Run:" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/python -m pip install -e \".[dev]\"" >&2
  echo "Then retry scripts/validation/run-gates.sh." >&2
  exit 2
fi

command="${1:-}"
shift || true

case "${command}" in
  registries)
    exec "${PYTHON}" -m validation.cli validate-registries "$@"
    ;;
  plan)
    plan_file="${1:?usage: run-gates.sh plan <plan.json> [extra args]}"
    shift
    exec "${PYTHON}" -m validation.cli gate-plan --file "${plan_file}" "$@"
    ;;
  run)
    run_file="${1:?usage: run-gates.sh run <run_metadata.json> [extra args]}"
    shift
    exec "${PYTHON}" -m validation.cli gate-run --file "${run_file}" "$@"
    ;;
  *)
    echo "usage: run-gates.sh {registries|plan <plan.json>|run <run_metadata.json>}" >&2
    exit 2
    ;;
esac

