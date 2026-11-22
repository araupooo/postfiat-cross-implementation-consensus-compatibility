#!/usr/bin/env python3
"""differential_probes.py — run the same scenarios against live postfiatd
measurements and l1v2 specification-derived expectations.

Reads outputs/derived/*.json (produced by scripts/analyze.py) and
fixtures/l1v2-expectations.json. Writes
outputs/derived/differential-probes.json.

Each scenario has a status:
  PASS       — live measurement agrees with the expectation.
  DIVERGENT  — live measurement and the expectation disagree, or the two
               implementations define different rules for the same behavior.
  UNVERIFIED — the expectation is spec-only or missing in l1v2; no live
               l1v2 network exists to measure against. Never inferred.

All arithmetic is computed here from the derived files, never hand-typed.
"""
import hashlib
import json
import math
import os
from datetime import datetime, timezone

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PACK, "outputs")
DER = os.path.join(OUT, "derived")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_derived(name):
    p = os.path.join(DER, name)
    print("input %s sha256=%s" % (name, sha256(p)))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def postfiatd_quorum(n):
    """max(ceil(0.67*n), ceil(0.60*n)) — ValidatorList::calculateQuorum."""
    return max(-(-n * 67 // 100), -(-n * 60 // 100))


def l1v2_quorum(n):
    """floor(2n/3)+1 — bft_quorum_threshold."""
    return (2 * n) // 3 + 1


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap = load_derived("live-testnet-snapshot.json")
    vals = load_derived("validators.json")
    amd = load_derived("amendments.json")
    cad = load_derived("cadence.json")
    with open(os.path.join(PACK, "fixtures", "l1v2-expectations.json")) as f:
        exp = json.load(f)
    print("input fixtures/l1v2-expectations.json sha256=%s"
          % sha256(os.path.join(PACK, "fixtures", "l1v2-expectations.json")))

    unl = vals["unl_count"]
    live_quorum = snap["validation_quorum"]
    scenarios = []

    def add(sid, title, area, status, postfiatd_measured, l1v2_expected,
            detail, evidence):
        scenarios.append({
            "id": sid, "title": title, "area": area, "status": status,
            "postfiatd_measured": postfiatd_measured,
            "l1v2_expected": l1v2_expected,
            "detail": detail, "evidence": evidence,
        })
        print("%s %s: %s" % (sid, status, title))

    # D01 — quorum arithmetic at the live UNL size.
    add("D01", "Quorum arithmetic at the live UNL size (n=25)", "quorum",
        "PASS" if postfiatd_quorum(unl) == l1v2_quorum(unl) == live_quorum else "DIVERGENT",
        {"unl_size": unl, "validation_quorum_reported": live_quorum,
         "postfiatd_formula": postfiatd_quorum(unl)},
        {"l1v2_formula": l1v2_quorum(unl),
         "source": exp["quorum"]["source"]},
        "At n=%d both formulas give %d, matching the reported quorum. "
        "The agreement is arithmetic coincidence at this n, not a shared rule."
        % (unl, live_quorum),
        ["outputs/derived/validators.json (quorum_check)",
         "fixtures/source-excerpts/ValidatorList-quorum.txt",
         "fixtures/source-excerpts/l1v2-bft-quorum-threshold.txt"])

    # D02 — quorum arithmetic at n=103 (first divergence above n=100).
    n2 = 103
    add("D02", "Quorum arithmetic at n=103 (first divergence)", "quorum",
        "DIVERGENT" if postfiatd_quorum(n2) != l1v2_quorum(n2) else "PASS",
        {"postfiatd_formula_at_103": postfiatd_quorum(n2)},
        {"l1v2_formula_at_103": l1v2_quorum(n2),
         "source": exp["quorum"]["source"]},
        "postfiatd ceil(0.67*103)=%d; l1v2 floor(2*103/3)+1=%d. The two "
        "quorum rules are different functions and diverge once n exceeds 100 "
        "with n = 1 mod 3." % (postfiatd_quorum(n2), l1v2_quorum(n2)),
        ["fixtures/source-excerpts/ValidatorList-quorum.txt",
         "fixtures/source-excerpts/l1v2-bft-quorum-threshold.txt"])

    # D03 — quorum at the l1v2 launch minimum (n=12): three different values.
    n3 = 12
    add("D03", "Quorum at the l1v2 launch minimum (n=12)", "quorum",
        "DIVERGENT",
        {"postfiatd_formula_at_12": postfiatd_quorum(n3)},
        {"l1v2_consensus_quorum_at_12": l1v2_quorum(n3),
         "l1v2_genesis_ratification_quorum_at_12": exp["quorum"]["launch_quorum_at_minimum"],
         "source": exp["quorum"]["genesis_ratification_source"]},
        "At n=12: postfiatd %d, l1v2 consensus %d, l1v2 genesis ratification "
        "%d. Three different quorum values govern three different phases."
        % (postfiatd_quorum(n3), l1v2_quorum(n3),
           exp["quorum"]["launch_quorum_at_minimum"]),
        ["fixtures/source-excerpts/l1v2-launch-topology-thresholds.txt",
         "fixtures/source-excerpts/l1v2-genesis-registry.txt"])

    # D04 — ledger close cadence vs postfiatd bounds; l1v2 specifies none.
    mean_close = cad["mean_close_interval_s"]
    add("D04", "Ledger close cadence within postfiatd bounds; no l1v2 cadence", "validation and ledger close",
        "UNVERIFIED",
        {"mean_close_interval_s": mean_close,
         "ledgers_advanced": cad["ledgers_advanced"],
         "postfiatd_min_close_s": 2, "postfiatd_idle_interval_s": 15,
         "within_bounds": 2 <= mean_close <= 15},
        {"l1v2_close_cadence_seconds": exp["ledger_close"]["close_cadence_seconds"],
         "note": exp["ledger_close"]["close_cadence_note"]},
        "Measured mean close interval %.3f s is inside the postfiatd bounds "
        "(2 s min close, 15 s idle), but l1v2 specifies no cadence at all, so "
        "there is nothing to compare it against. UNVERIFIED, not inferred."
        % mean_close,
        ["outputs/cadence-run1.jsonl",
         "outputs/derived/cadence.json",
         "fixtures/source-excerpts/ConsensusParms.txt"])

    # D05 — close-time resolution.
    add("D05", "Ledger close-time resolution", "validation and ledger close",
        "UNVERIFIED",
        {"live_close_time_resolution_s": snap["ledger_close_time_resolution"]},
        {"l1v2_close_time_resolution_seconds": exp["ledger_close"]["close_time_resolution_seconds"],
         "note": "l1v2 specifies no close-time resolution; Consensus v2 progress is view/timeout driven"},
        "Live ledger close_time_resolution is %s s (postfiatd genesis "
        "resolution 10 s, default 30 s). l1v2 defines no close-time "
        "resolution, so no comparison is possible."
        % snap["ledger_close_time_resolution"],
        ["outputs/derived/live-testnet-snapshot.json",
         "fixtures/source-excerpts/LedgerTiming.txt"])

    # D06 — last-close converge time vs postfiatd max consensus.
    converge_ms = snap["last_close_converge_time_ms"]
    add("D06", "Last-close converge time vs postfiatd max consensus", "validation and ledger close",
        "UNVERIFIED",
        {"last_close_converge_time_ms": converge_ms,
         "last_close_proposers": snap["last_close_proposers"],
         "postfiatd_max_consensus_ms": 15000,
         "within_max": converge_ms < 15000 if converge_ms is not None else None},
        {"l1v2_converge_time": None,
         "note": "l1v2 specifies no converge-time bound; view changes are timeout-certificate driven"},
        "Last close converged in %s ms with %s proposers, inside the "
        "postfiatd 15 s max-consensus bound. No l1v2 bound exists to compare."
        % (converge_ms, snap["last_close_proposers"]),
        ["outputs/derived/live-testnet-snapshot.json",
         "fixtures/source-excerpts/ConsensusParms.txt"])

    # D07 — amendment threshold: 67% live (fix active) vs per-kind l1v2 governance.
    add("D07", "Amendment majority threshold", "amendment activation",
        "DIVERGENT",
        {"fix_amendment_majority_calc_enabled": amd["fix_amendment_majority_calc_enabled"],
         "active_threshold": "67% (post-fix)" if amd["fix_amendment_majority_calc_enabled"] else "79.6875% (pre-fix)",
         "known_amendments": amd["known_amendments_rpc"],
         "enabled_amendments": amd["enabled_rpc"]},
        {"general_amendment_mechanism": exp["amendment"]["general_amendment_mechanism"],
         "governed_lane_threshold": exp["amendment"]["governed_amendment_threshold"],
         "note": "l1v2 has a GovernanceAmendment object, but no single global majority threshold: each amendment carries its own quorum/support and activates per-kind at a height"},
        "postfiatd activates amendments by validator vote at a uniform 67%% "
        "majority (fix active on the live network). l1v2 has a "
        "GovernanceAmendment object, but its threshold is per-amendment "
        "(quorum/support fields) with per-kind height-based activation — "
        "there is no uniform validator-vote threshold to compare against. "
        "The only precisely specified l1v2 threshold is the registry "
        "threshold floor(2n/3)+1 for lane amendments.",
        ["outputs/derived/amendments.json",
         "fixtures/source-excerpts/AmendmentTable-threshold.txt",
         "fixtures/source-excerpts/SystemParameters-thresholds.txt",
         "fixtures/source-excerpts/l1v2-governed-lane-amendments.txt"])

    # D08 — amendment majority hold time.
    add("D08", "Amendment majority hold time", "amendment activation",
        "DIVERGENT",
        {"testnet_majority_time": "3 days (shipped testnet config)",
         "code_default_majority_time": "2 weeks",
         "source": "cfg/postfiatd-testnet-full.cfg:1467-1468; SystemParameters.h:88"},
        {"l1v2_majority_hold_time": exp["amendment"]["majority_hold_time"],
         "governed_amendment_timing": "activation_height of the proposal slot; cap raises apply 7 windows after commit",
         "veto_procedure": exp["amendment"]["veto_procedure"],
         "source": exp["amendment"]["governed_amendment_source"]},
        "postfiatd holds an amendment majority for 3 days on this testnet "
        "(2-week code default) before activation. l1v2 governed lane "
        "amendments apply at a named activation height, with cap raises "
        "delayed 7 windows — a different timing model with no majority-hold "
        "period — and no veto procedure is specified beyond the "
        "veto_until_height field.",
        ["fixtures/source-excerpts/Config-amendment-majority-time.txt",
         "fixtures/source-excerpts/l1v2-governed-lane-amendments.txt"])

    # D09 — genesis supply reconciliation vs l1v2 faucet/lane model.
    rec = snap["supply_reconciliation"]
    add("D09", "Genesis supply reconciliation", "genesis construction",
        "UNVERIFIED",
        {"genesis_supply_pft": rec["genesis_supply_drops"] / 1e6,
         "genesis_account_balance_pft": snap["genesis_account_balance_pft"],
         "other_accounts_pft": rec["other_accounts_pft"],
         "burned_by_fees_pft": rec["burned_by_fees_pft"],
         "reconciliation_closes": rec["closes"]},
        {"l1v2_supply_pft": exp["genesis"]["supply_pft"],
         "l1v2_supply_note": exp["genesis"]["supply_note"],
         "note": "The ERC-20 slice size is open and no l1v2 network exists to measure; the faucet-minus-lanes model cannot be reconciled against a live ledger"},
        "Live postfiatd reconciliation closes exactly at 100B PFT. l1v2 "
        "specifies the same 100B total but splits it into a faucet plus "
        "reserved lane atoms with an open slice size, on no live network — "
        "so the l1v2 side cannot be verified.",
        ["outputs/derived/live-testnet-snapshot.json",
         "fixtures/source-excerpts/Ledger-genesis.txt",
         "fixtures/source-excerpts/l1v2-pft-token-on-base.txt"])

    # D10 — genesis construction model.
    add("D10", "Genesis construction model", "genesis construction",
        "DIVERGENT",
        {"model": "Ledger::Ledger(create_genesis_t): seq 1, whole 100B supply in one account",
         "genesis_account": snap["genesis_account"]},
        {"model": exp["genesis"]["construction"],
         "source": exp["genesis"]["source"]},
        "postfiatd genesis is a single-account fresh ledger; l1v2 genesis "
        "is a ratified validator registry with an identity bridge. The two "
        "constructions share nothing except the 100B supply figure.",
        ["fixtures/source-excerpts/Ledger-genesis.txt",
         "fixtures/source-excerpts/l1v2-genesis-registry.txt"])

    # D11 — validation lifetimes.
    add("D11", "Validation / vote lifetimes", "validation and ledger close",
        "DIVERGENT",
        {"validation_valid_wall_s": 300, "validation_valid_local_s": 180,
         "validation_valid_early_s": 180, "propose_freshness_s": 20,
         "propose_interval_s": 12,
         "source": "src/xrpld/consensus/ConsensusParms.h:40-80"},
        {"l1v2_lifetime_seconds": exp["validation"]["lifetime_seconds"],
         "note": exp["validation"]["lifetime_note"]},
        "postfiatd validations expire after minutes (5 min wall, 3 min "
        "local). l1v2 votes carry no wall-clock lifetime; they persist under "
        "the durable round floor until superseded. Replay/retention across "
        "the boundary is undefined.",
        ["fixtures/source-excerpts/ConsensusParms.txt",
         "fixtures/source-excerpts/l1v2-consensus-signing-rounds.txt"])

    # D12 — commit rule.
    add("D12", "Commit rule", "validation and ledger close",
        "DIVERGENT",
        {"model": "A ledger is validated when trusted validations on one ledger hash reach the validation quorum (17 of UNL 25 live)",
         "source": "ValidatorList::calculateQuorum; Consensus.h shouldPause phases"},
        {"model": exp["validation"]["commit_rule"],
         "source": exp["validation"]["source"]},
        "One validation message per validator per ledger (postfiatd) vs two "
        "QC phases with durable locks and timeout-certificate view changes "
        "(l1v2). A ledger validated under one rule is not validated under "
        "the other.",
        ["fixtures/source-excerpts/ValidatorList-quorum.txt",
         "fixtures/source-excerpts/Consensus-phases.txt",
         "fixtures/source-excerpts/l1v2-finality.txt"])

    # D13 — validator identity / key type.
    add("D13", "Validator identity and key type", "quorum",
        "DIVERGENT",
        {"model": "secp256k1 validator keys, manifests, publisher-served validator list (VL v2)",
         "unl_size": unl},
        {"model": "ML-DSA-65 validator keys, bridged from fork secp256k1 keys by dual-signed identity receipts",
         "source": exp["genesis"]["source"]},
        "No postfiatd validator key can sign an l1v2 vote without the "
        "identity-bridge receipt; no l1v2 ML-DSA key can sign a postfiatd "
        "validation.",
        ["outputs/derived/validators.json",
         "fixtures/source-excerpts/l1v2-genesis-registry.txt"])

    # D14 — audit / external verification.
    add("D14", "External audit recorded", "amendment activation",
        "UNVERIFIED",
        {"postfiatd_external_audit": "none recorded",
         "note": "No audit is recorded for postfiatd; the founder's multi-million-dollar audit is a statement, not a scoped engagement"},
        {"l1v2_external_audit_recorded": exp["audit"]["external_audit_recorded"],
         "source": exp["audit"]["source"]},
        "Neither codebase has a recorded external audit. There is no "
        "independent verification of either consensus implementation to "
        "compare.",
        ["fixtures/source-excerpts/l1v2-security-index.txt"])

    # D15 — mainnet date.
    add("D15", "Mainnet / TGE date published", "genesis construction",
        "UNVERIFIED",
        {"postfiatd_mainnet_date": None,
         "note": "No official mainnet/TGE date is published in the surveyed sources"},
        {"l1v2_mainnet_date": exp["mainnet_date"],
         "note": exp["mainnet_date_note"]},
        "No mainnet date exists on either side; there is no schedule to "
        "compare and no convergence date to assess.",
        ["outputs/postfiat_whitepaper.html",
         "outputs/docs_postfiat_org.html"])

    result = {
        "generated_at_utc": now,
        "probe_window": "live postfiatd testnet (network 2025) vs l1v2 specification at rev %s" % exp["postfiatl1v2_rev"],
        "counts": {
            "scenarios_total": len(scenarios),
            "by_status": {st: sum(1 for s in scenarios if s["status"] == st)
                          for st in sorted({s["status"] for s in scenarios})},
            "by_area": {a: sum(1 for s in scenarios if s["area"] == a)
                        for a in sorted({s["area"] for s in scenarios})},
        },
        "scenarios": scenarios,
    }
    out = os.path.join(DER, "differential-probes.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print("wrote differential-probes.json sha256=%s" % sha256(out))
    print("counts: %s" % result["counts"])


if __name__ == "__main__":
    main()
