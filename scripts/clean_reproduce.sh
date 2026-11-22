#!/bin/bash
# clean_reproduce.sh — fresh-environment reproduction.
#
# Copies this pack to a throwaway directory, re-runs the probes, a short
# cadence (5 samples x 30 s), the analysis and the differential probes there,
# then compares the fresh derived numbers against the shipped ones with
# scripts/compare_reproduce.py. Exits 0 only if every comparison check passes.
#
# Usage: bash scripts/clean_reproduce.sh [WORKDIR]
#   WORKDIR defaults to a fresh mktemp directory; the path is printed so the
#   run can be inspected afterwards.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-$(mktemp -d /tmp/pftl-compat-repro.XXXXXX)}"
echo "clean_reproduce.sh workdir: $WORK"
rm -rf "$WORK/pack"
cp -r "$PACK_ROOT" "$WORK/pack"
cd "$WORK/pack"
# Drop shipped probe outputs so nothing is reused; keep configs/fixtures/docs.
rm -f outputs/*.json outputs/*.jsonl outputs/*.log outputs/*.html outputs/*.txt \
      outputs/*.http outputs/derived/*.json
rm -f findings.json run-manifest.json
# Fresh probes (short cadence: 5 samples keeps the check near 2.5 minutes).
bash scripts/probe_all.sh
python3 scripts/cadence.py --samples 5 --interval 30 \
  --out-prefix outputs/cadence-run1 > outputs/cadence-run1.log 2>&1
python3 scripts/analyze.py > "$WORK/repro-analyze.log" 2>&1
python3 scripts/differential_probes.py > "$WORK/repro-differential.log" 2>&1
# Compare fresh derived numbers with the shipped ones.
python3 scripts/compare_reproduce.py \
  "$PACK_ROOT/outputs/derived" "$WORK/pack/outputs/derived" \
  | tee "$WORK/repro-compare.log"
COMPARE_EXIT="${PIPESTATUS[0]}"
# Keep the fresh probe set as evidence, prefixed fresh-clone-.
mkdir -p "$PACK_ROOT/outputs"
for f in outputs/*.json outputs/*.jsonl outputs/*.log outputs/*.html outputs/*.txt; do
  base="$(basename "$f")"
  case "$base" in
    probe-run.log|cadence-run1.log) cp "$f" "$PACK_ROOT/outputs/fresh-clone-$base" ;;
    *.json|*.jsonl|*.html|*.txt) cp "$f" "$PACK_ROOT/outputs/fresh-clone-$base" ;;
  esac
done
cp "$WORK/repro-compare.log" "$PACK_ROOT/outputs/fresh-clone-compare.log"
cp "$WORK/repro-analyze.log" "$PACK_ROOT/outputs/fresh-clone-analyze.log"
cp "$WORK/repro-differential.log" "$PACK_ROOT/outputs/fresh-clone-differential.log"
echo "fresh-clone outputs copied to $PACK_ROOT/outputs/fresh-clone-*"
echo "workdir kept at: $WORK"
if [ "$COMPARE_EXIT" -ne 0 ]; then
  echo "clean_reproduce.sh: COMPARISON FAILED (exit $COMPARE_EXIT)"
  exit "$COMPARE_EXIT"
fi
echo "clean_reproduce.sh: ALL CHECKS PASSED"
