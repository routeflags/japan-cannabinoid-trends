#!/bin/bash
# COL-019 (2026-10-15): retired teiten cron route — fail closed.
#
# Former behavior (retired): an hourly probabilistic gate (1/TEITEN_DENOM)
# that invoked fetch_tiktok.sh / fetch_instagram.sh, writing to
# `$ROOT/projects/automation/Apify/data/teiten_YYYYMMDD/`.
#
# Why retired (evidence recorded in ISS-20261015-COL-019):
# - `projects/` does not exist in this repository (0 tracked files, no
#   .gitignore entry); the fetch scripts would create it via `mkdir -p`,
#   producing raw outside the stage/adopt pipeline;
# - the callees moved: `$DIR/fetch_tiktok.sh` / `$DIR/fetch_instagram.sh`
#   do not exist (they live in `tiktok/` / `instagram/` subdirectories), so a
#   passing gate errored instead of collecting;
# - no schedule references this script (no crontab, no CI workflow);
# - the Instagram teiten observation was abolished 2026-10-01
#   (docs/reports/20261015c-publication-refresh-plan.md P7).
#
# External payloads now enter through the documented pipeline only:
#   make stage DECLARATION=<staging-declaration-v1> && make adopt-all
# (docs/specs/collection-pipeline.md). This stub writes nothing and exits
# non-zero so a stale cron entry fails loudly instead of scattering raw.
set -uo pipefail

echo "cron_gate.sh: disabled — the teiten cron route is retired (ISS-20261015-COL-019)." >&2
echo "  External payloads enter only via the stage/adopt pipeline:" >&2
echo "    make stage DECLARATION=<staging-declaration-v1 json>" >&2
echo "    make adopt-all" >&2
exit 2
