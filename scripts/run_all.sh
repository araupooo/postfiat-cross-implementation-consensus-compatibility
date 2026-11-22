#!/bin/bash
# run_all.sh — full pack build: fresh probes + 21-sample cadence + analysis
# + differential probes. Run from the pack root.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PACK_ROOT"
bash scripts/probe_all.sh
python3 scripts/cadence.py --samples 21 --interval 30 \
  --out-prefix outputs/cadence-run1 > outputs/cadence-run1.log 2>&1
python3 scripts/analyze.py
python3 scripts/differential_probes.py
bash scripts/make_sha256sums.sh
bash scripts/verify_digests.sh
echo "run_all.sh: done"
