#!/usr/bin/env python3
"""compare_reproduce.py — compare shipped derived numbers against a fresh probe run.

Usage: python3 scripts/compare_reproduce.py <shipped-derived-dir> <fresh-derived-dir>
Exits 0 only if every check passes. Tolerances are explicit: ledger sequence
must advance (fresh > shipped), counts that move slowly must agree within a
band, and structural facts (network id, version, quorum formula, amendment
agreement) must match exactly.

Checks:
  network_id == 2025, build_version == 1.0.9 (both runs)
  fresh validated seq > shipped validated seq
  fresh seq within 200,000 of shipped seq (sanity: no wild jump)
  peers 15..30, validation_quorum == max(ceil(0.67*UNL), ceil(0.60*UNL))
  UNL count 20..30, validators total 50..90
  enabled amendments 60..70 and RPC/VHS agreement in both runs
  PF amendments still disabled in both runs
  cadence mean close interval 2.5..4.0 s in both runs
  supply reconciliation still closes in both runs
  differential-probe status counts identical (1 PASS, 8 DIVERGENT, 6 UNVERIFIED)
  explorer metrics base_fee identical

Out of scope by design: the reordered-validation vote-replay work is not
checked here (it belongs to a separate task and is excluded from this pack).
"""
import json
import os
import sys
from collections import Counter


def load(d, name):
    with open(os.path.join(d, name)) as f:
        return json.load(f)


def check(results, name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (" | " + detail if detail else ""))


def main():
    shipped_dir, fresh_dir = sys.argv[1], sys.argv[2]
    # shipped derived files live in outputs/derived/; fresh ones likewise.
    s_snap = load(shipped_dir, "live-testnet-snapshot.json")
    f_snap = load(fresh_dir, "live-testnet-snapshot.json")
    s_val = load(shipped_dir, "validators.json")
    f_val = load(fresh_dir, "validators.json")
    s_amd = load(shipped_dir, "amendments.json")
    f_amd = load(fresh_dir, "amendments.json")
    s_cad = load(shipped_dir, "cadence.json")
    f_cad = load(fresh_dir, "cadence.json")
    s_diff = load(shipped_dir, "differential-probes.json")
    f_diff = load(fresh_dir, "differential-probes.json")
    results = []

    check(results, "network_id 2025 both runs",
          s_snap["network_id"] == 2025 and f_snap["network_id"] == 2025,
          "shipped=%s fresh=%s" % (s_snap["network_id"], f_snap["network_id"]))
    check(results, "build_version 1.0.9 both runs",
          s_snap["build_version"] == "1.0.9" and f_snap["build_version"] == "1.0.9",
          "shipped=%s fresh=%s" % (s_snap["build_version"], f_snap["build_version"]))
    check(results, "validated seq advances",
          f_snap["validated_ledger_seq"] > s_snap["validated_ledger_seq"],
          "shipped=%d fresh=%d" % (s_snap["validated_ledger_seq"],
                                    f_snap["validated_ledger_seq"]))
    check(results, "validated seq within 200000 (sanity)",
          abs(f_snap["validated_ledger_seq"] - s_snap["validated_ledger_seq"]) < 200000,
          "delta=%d" % (f_snap["validated_ledger_seq"] - s_snap["validated_ledger_seq"]))
    check(results, "peers in 15..30 both runs",
          15 <= s_snap["peers"] <= 30 and 15 <= f_snap["peers"] <= 30,
          "shipped=%s fresh=%s" % (s_snap["peers"], f_snap["peers"]))
    check(results, "quorum formula holds both runs",
          s_val["quorum_check"]["matches_67pct_formula"]
          and f_val["quorum_check"]["matches_67pct_formula"],
          "shipped quorum=%s fresh quorum=%s UNL=%d/%d" % (
              s_snap["validation_quorum"], f_snap["validation_quorum"],
              s_val["unl_count"], f_val["unl_count"]))
    check(results, "UNL count 20..30 both runs",
          20 <= s_val["unl_count"] <= 30 and 20 <= f_val["unl_count"] <= 30,
          "shipped=%d fresh=%d" % (s_val["unl_count"], f_val["unl_count"]))
    check(results, "validators total 50..90 both runs",
          50 <= s_val["validators_total"] <= 90
          and 50 <= f_val["validators_total"] <= 90,
          "shipped=%d fresh=%d" % (s_val["validators_total"],
                                    f_val["validators_total"]))
    check(results, "enabled amendments 60..70 both runs",
          60 <= s_amd["enabled_rpc"] <= 70 and 60 <= f_amd["enabled_rpc"] <= 70,
          "shipped=%d fresh=%d" % (s_amd["enabled_rpc"], f_amd["enabled_rpc"]))
    check(results, "RPC/VHS amendment agreement both runs",
          s_amd["rpc_enabled_equals_vhs_vote_count"]
          and s_amd["rpc_enabled_names_equal_vhs_vote_names"]
          and f_amd["rpc_enabled_equals_vhs_vote_count"]
          and f_amd["rpc_enabled_names_equal_vhs_vote_names"],
          "shipped=%s fresh=%s" % (
              s_amd["rpc_enabled_names_equal_vhs_vote_names"],
              f_amd["rpc_enabled_names_equal_vhs_vote_names"]))
    check(results, "PF native amendments still disabled both runs",
          all(not v["enabled"] for v in s_amd["postfiat_native_amendments"].values())
          and all(not v["enabled"] for v in f_amd["postfiat_native_amendments"].values()),
          "shipped=%s fresh=%s" % (s_amd["postfiat_native_amendments"],
                                    f_amd["postfiat_native_amendments"]))
    check(results, "cadence mean close interval 2.5..4.0 s both runs",
          2.5 <= s_cad["mean_close_interval_s"] <= 4.0
          and 2.5 <= f_cad["mean_close_interval_s"] <= 4.0,
          "shipped=%.3f fresh=%.3f" % (s_cad["mean_close_interval_s"],
                                        f_cad["mean_close_interval_s"]))
    check(results, "supply reconciliation closes both runs",
          s_snap["supply_reconciliation"]["closes"]
          and f_snap["supply_reconciliation"]["closes"],
          "shipped burned=%.6f PFT fresh burned=%.6f PFT" % (
              s_snap["supply_reconciliation"]["burned_by_fees_pft"],
              f_snap["supply_reconciliation"]["burned_by_fees_pft"]))
    s_counts = Counter(s["status"] for s in s_diff["scenarios"])
    f_counts = Counter(s["status"] for s in f_diff["scenarios"])
    check(results, "differential-probe status counts identical",
          s_counts == f_counts,
          "shipped=%s fresh=%s" % (dict(s_counts), dict(f_counts)))
    check(results, "explorer base_fee identical",
          s_val["explorer_metrics"]["base_fee"] == f_val["explorer_metrics"]["base_fee"],
          "base_fee=%s" % s_val["explorer_metrics"]["base_fee"])

    failed = [r for r in results if not r[1]]
    print("")
    if failed:
        print("COMPARISON: %d CHECK(S) FAILED" % len(failed))
        sys.exit(1)
    print("COMPARISON: ALL CHECKS PASSED (%d checks)" % len(results))


if __name__ == "__main__":
    main()
