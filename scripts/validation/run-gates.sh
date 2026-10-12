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
#   0 = pass / proceed       1 = fail -> do not adopt / do not start
#   2 = schema or configuration error   3 = file I/O error
#
# "run" verifies structure + semantics + the referenced artifact manifest
# (--verify-artifacts).  A non-zero exit means the collected data must be
# quarantined (kept raw, not promoted to the catalog) - the script never
# moves or rewrites raw data itself (P6-2).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -x "${ROOT}/.venv/bin/python" ]; then
  PYTHON="${ROOT}/.venv/bin/python"
else
  PYTHON="python3"
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
    exec "${PYTHON}" -m validation.cli validate \
      --schema collection-run-v1 \
      --verify-artifacts \
      --file "${run_file}" "$@"
    ;;
  *)
    echo "usage: run-gates.sh {registries|plan <plan.json>|run <run_metadata.json>}" >&2
    exit 2
    ;;
esac
