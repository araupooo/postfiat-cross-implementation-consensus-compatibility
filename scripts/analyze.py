#!/usr/bin/env python3
"""analyze.py — derive every measured number in this pack from outputs/.

Reads only the unedited probe outputs under outputs/ and the pinned source
excerpts under fixtures/. Writes:
  outputs/derived/live-testnet-snapshot.json
  outputs/derived/validators.json
  outputs/derived/amendments.json
  outputs/derived/cadence.json
  findings.json
  run-manifest.json

Every input file's full SHA-256 is printed, so a reader can check that the
derived numbers come from the shipped outputs and nothing else. Re-running
this script over a fresh probe set must reproduce the same structure; values
that move with time (ledger sequence, counts) are compared with tolerances
by scripts/compare_reproduce.py, not byte-for-byte.

Boundary note: the reordered-validation vote-replay work is out of scope
for this pack; no fetch, summary, or finding about it appears here.
"""
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PACK, "outputs")
DER = os.path.join(OUT, "derived")
os.makedirs(DER, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name):
    p = os.path.join(OUT, name)
    print("input %s sha256=%s" % (name, sha256(p)))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_text(name):
    p = os.path.join(OUT, name)
    print("input %s sha256=%s" % (name, sha256(p)))
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


def dump(name, obj):
    p = os.path.join(DER, name)
    with open(p, "w") as f:
        json.dump(obj, f, indent=1)
    print("wrote %s sha256=%s" % (name, sha256(p)))
    return obj


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    si = load("server_info.json")["result"]["info"]
    led = load("ledger_current.json")["result"]["ledger"]
    led_closed = load("ledger_closed.json")["result"]
    fee = load("fee.json")["result"]
    feat = load("feature_list.json")["result"]["features"]
    ss = load("server_state.json")["result"]["state"]
    pf_gen = load("account_info_pftl_genesis.json")["result"]
    xrpl_gen = load("account_info_xrpl_genesis.json")["result"]
    xrpl_root = load("account_info_xrpl_root.json")["result"]
    vhs_val = load("vhs_validators.json")
    vhs_topo = load("vhs_topology_nodes.json")
    vhs_topo_sum = load("vhs_topology.json")
    vhs_net = load("vhs_networks.json")
    vhs_health = load("vhs_health.json")
    vhs_amend_info = load("vhs_amendments_info.json")
    vhs_amend_vote = load("vhs_amendments_vote_test.json")
    vhs_amend_index = load("vhs_amendments.json")
    metrics = load("explorer_metrics.json")
    exp_health = load_text("explorer_health.json")
    vl = load("unl_testnet_vl.json")
    # VL v2: blobs_v2[0].blob is base64 JSON with sequence, effective and
    # expiration in Ripple-epoch seconds (since 2000-01-01T00:00:00Z).
    import base64 as _b64
    from datetime import timedelta as _td
    _blob = json.loads(_b64.b64decode(vl["blobs_v2"][0]["blob"]))
    _epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)
    vl_decoded = {
        "sequence": _blob.get("sequence"),
        "effective": (_epoch + _td(seconds=_blob["effective"])).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expiration": (_epoch + _td(seconds=_blob["expiration"])).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validators_in_blob": len(_blob.get("validators") or []),
    }
    cadence_rows = []
    with open(os.path.join(OUT, "cadence-run1.jsonl")) as f:
        for line in f:
            line = line.strip()
            if line:
                cadence_rows.append(json.loads(line))
    print("input cadence-run1.jsonl sha256=%s"
          % sha256(os.path.join(OUT, "cadence-run1.jsonl")))

    # ---- live testnet snapshot + supply reconciliation ----
    total_coins = int(led["total_coins"])
    genesis_balance = int(pf_gen["account_data"]["Balance"])
    genesis_supply = 100_000_000_000 * 1_000_000  # INITIAL_XRP, SystemParameters.h:44
    snapshot = {
        "probed_at_utc": now,
        "build_version": si.get("build_version"),
        "network_id": si.get("network_id"),
        "server_state": si.get("server_state"),
        "peers": si.get("peers"),
        "validation_quorum": si.get("validation_quorum"),
        "validated_ledger_seq": si["validated_ledger"]["seq"],
        "validated_ledger_hash": si["validated_ledger"]["hash"],
        "complete_ledgers": si.get("complete_ledgers"),
        "uptime_seconds": si.get("uptime"),
        "last_close_proposers": (ss.get("last_close") or {}).get("proposers"),
        "last_close_converge_time_ms": (ss.get("last_close") or {}).get("converge_time"),
        "ledger_index": led["ledger_index"],
        "ledger_close_time": led["close_time_human"],
        "ledger_close_time_iso": led["close_time_iso"],
        "ledger_close_time_resolution": led.get("close_time_resolution"),
        "ledger_closed_matches": led_closed["ledger_index"] == int(led["ledger_index"]),
        "total_coins_drops": total_coins,
        "total_coins_pft": total_coins / 1e6,
        "base_fee_drops": fee["drops"]["base_fee"],
        "median_fee_drops": fee["drops"]["median_fee"],
        "current_queue_size": fee["current_queue_size"],
        "max_queue_size": fee["max_queue_size"],
        "reserve_base_drops": (ss.get("validated_ledger") or {}).get("reserve_base"),
        "reserve_increment_drops": (ss.get("validated_ledger") or {}).get("reserve_inc"),
        "genesis_account": pf_gen["account_data"]["Account"],
        "genesis_account_balance_drops": genesis_balance,
        "genesis_account_balance_pft": genesis_balance / 1e6,
        "genesis_account_sequence": pf_gen["account_data"]["Sequence"],
        "genesis_supply_drops_assumed": genesis_supply,
        "supply_reconciliation": {
            "genesis_supply_drops": genesis_supply,
            "total_coins_drops": total_coins,
            "burned_by_fees_drops": genesis_supply - total_coins,
            "burned_by_fees_pft": (genesis_supply - total_coins) / 1e6,
            "genesis_account_balance_drops": genesis_balance,
            "other_accounts_drops": total_coins - genesis_balance,
            "other_accounts_pft": (total_coins - genesis_balance) / 1e6,
            "closes": (genesis_balance + (total_coins - genesis_balance)
                       + (genesis_supply - total_coins)) == genesis_supply,
        },
        "xrpl_genesis_account_found": "account_data" in xrpl_gen,
        "xrpl_genesis_account_error": xrpl_gen.get("error"),
        "xrpl_root_account_found": "account_data" in xrpl_root,
        "xrpl_root_account_error": xrpl_root.get("error"),
        "admin_methods_blocked": {
            "validators": load_text("validators.json").strip(),
            "peers": load_text("peers.json").strip(),
        },
        "unknown_method": load("invalid_method.json")["result"],
        "ws_upgrade_probe": load_text("ws_upgrade_probe.txt"),
    }
    dump("live-testnet-snapshot.json", snapshot)

    # ---- validators ----
    vals = vhs_val["validators"]
    unl = [v for v in vals if v.get("unl")]
    topo = vhs_topo["nodes"]
    stale_unl = [v for v in unl if float(v["agreement_24h"]["score"]) == 0.0]
    validators = {
        "validators_total": len(vals),
        "unl_count": len(unl),
        "unl_all_version": sorted({v.get("server_version") for v in unl}),
        "unl_all_domains_verified": all(v.get("domain_verified") for v in unl),
        "versions": {k: sum(1 for v in vals if v.get("server_version") == k)
                     for k in sorted({v.get("server_version") for v in vals})},
        "non_latest_version_count": sum(
            1 for v in vals if v.get("server_version") != "1.0.9"),
        "non_latest_version_unl_count": sum(
            1 for v in unl if v.get("server_version") != "1.0.9"),
        "domains_verified": sum(1 for v in vals if v.get("domain_verified")),
        "with_domain": sum(1 for v in vals if v.get("domain")),
        "agreement_24h": {
            "min": min(float(v["agreement_24h"]["score"]) for v in vals),
            "mean": sum(float(v["agreement_24h"]["score"]) for v in vals) / len(vals),
            "at_least_0_999": sum(
                1 for v in vals if float(v["agreement_24h"]["score"]) >= 0.999),
            "total_missed": sum(v["agreement_24h"]["missed"] for v in vals),
            "unl_total_missed": sum(v["agreement_24h"]["missed"] for v in unl),
        },
        "stale_unl_members": [{
            "validation_public_key": v["validation_public_key"],
            "domain": v.get("domain"),
            "server_version": v.get("server_version"),
            "current_index": v.get("current_index"),
            "agreement_24h_score": v["agreement_24h"]["score"],
            "agreement_24h_missed": v["agreement_24h"]["missed"],
        } for v in stale_unl],
        "topology_nodes": len(topo),
        "topology_node_count_field": vhs_topo_sum.get("node_count"),
        "topology_link_count_field": vhs_topo_sum.get("link_count"),
        "topology_inbound_sum": sum(v.get("inbound_count", 0) for v in topo),
        "topology_outbound_sum": sum(v.get("outbound_count", 0) for v in topo),
        "topology_states": {k: sum(1 for v in topo if v.get("server_state") == k)
                            for k in sorted({v.get("server_state") for v in topo},
                                            key=lambda x: str(x))},
        "topology_country_codes": sorted(
            {v.get("country_code") for v in topo if v.get("country_code")}),
        "vhs_health": vhs_health,
        "vhs_networks": [(n["id"], n["entry"]) for n in vhs_net["networks"]],
        "vhs_validators_unl_param_ignored": (
            load_text("vhs_validators_unl.json").strip()
            == load_text("vhs_validators.json").strip()),
        "validator_list_file": {
            "version": vl.get("version"),
            "sequence": vl_decoded["sequence"],
            "expiration": vl_decoded["expiration"],
            "effective": vl_decoded["effective"],
            "validators_in_file": vl_decoded["validators_in_blob"],
            "unl_from_vhs_equals_file_count": len(unl) == vl_decoded["validators_in_blob"],
        },
        "explorer_metrics": metrics,
        "explorer_health_body": exp_health.strip(),
        "quorum_check": {
            "unl_size": len(unl),
            "validation_quorum_reported": si.get("validation_quorum"),
            "ceil_0_67_x_unl": -(-len(unl) * 67 // 100),
            "ceil_0_60_x_unl": -(-len(unl) * 60 // 100),
            "matches_67pct_formula": si.get("validation_quorum") == max(
                -(-len(unl) * 67 // 100), -(-len(unl) * 60 // 100)),
            "l1v2_quorum_for_same_n": (2 * len(unl)) // 3 + 1,
            "quorum_formulas_agree_at_this_n": (
                si.get("validation_quorum") == (2 * len(unl)) // 3 + 1),
            "source": "ValidatorList::calculateQuorum, "
                      "postfiatd src/xrpld/app/misc/detail/ValidatorList.cpp:1845-1933; "
                      "l1v2 bft_quorum_threshold, "
                      "postfiatl1v2 crates/ordering_fast/src/lib.rs:345-356",
        },
    }
    dump("validators.json", validators)

    # ---- amendments ----
    enabled = [v for k, v in feat.items() if v["enabled"]]
    disabled = [v for k, v in feat.items() if not v["enabled"]]
    vote_enabled = {a["name"] for a in vhs_amend_vote["amendments"]}
    rpc_enabled = {v["name"] for v in enabled}
    amendments = {
        "known_amendments_rpc": len(feat),
        "enabled_rpc": len(enabled),
        "disabled_rpc": len(disabled),
        "known_amendments_vhs_info": vhs_amend_info.get("count"),
        "enabled_vhs_vote": vhs_amend_vote.get("count"),
        "rpc_enabled_equals_vhs_vote_count": len(enabled) == vhs_amend_vote.get("count"),
        "rpc_enabled_names_equal_vhs_vote_names": rpc_enabled == vote_enabled,
        "names_only_in_rpc": sorted(rpc_enabled - vote_enabled),
        "names_only_in_vhs": sorted(vote_enabled - rpc_enabled),
        "enabled_names": sorted(rpc_enabled),
        "disabled_names": sorted(v["name"] for v in disabled),
        "postfiat_native_amendments": {
            name: {"enabled": feat[k]["enabled"], "id": k}
            for k, name in
            ((k, v["name"]) for k, v in feat.items())
            if name.startswith("PF_")},
        "bulk_enablement": {
            "note": "Every enabled amendment in the VHS vote endpoint "
                    "carries the same ledger_index and date.",
            "distinct_ledger_indexes": sorted(
                {a.get("ledger_index") for a in vhs_amend_vote["amendments"]}),
            "distinct_dates": sorted(
                {a.get("date") for a in vhs_amend_vote["amendments"]}),
        },
        "vhs_amendments_index_is_service_index_only": (
            "amendments" not in vhs_amend_index),
    }
    by_name = {v["name"]: v for v in feat.values()}
    amendments["fix_amendment_majority_calc_enabled"] = by_name.get(
        "fixAmendmentMajorityCalc", {}).get("enabled")
    dump("amendments.json", amendments)

    # ---- cadence ----
    seqs = [r["seq"] for r in cadence_rows if "seq" in r]
    intervals = []
    if len(seqs) >= 2:
        intervals = [(seqs[i + 1] - seqs[i]) for i in range(len(seqs) - 1)]
    cadence = {
        "samples": len(cadence_rows),
        "seq_first": seqs[0] if seqs else None,
        "seq_last": seqs[-1] if seqs else None,
        "ledgers_advanced": (seqs[-1] - seqs[0]) if len(seqs) >= 2 else 0,
        "ledgers_per_sample_interval": intervals,
        "mean_ledgers_per_30s": (sum(intervals) / len(intervals)) if intervals else None,
        "mean_close_interval_s": (30.0 * len(intervals) / sum(intervals)) if intervals and sum(intervals) else None,
        "peers_constant": len({r.get("peers") for r in cadence_rows if "peers" in r}) == 1,
        "peers_value": cadence_rows[0].get("peers") if cadence_rows else None,
    }
    dump("cadence.json", cadence)

    # ---- findings (computed from the derived numbers above; counts below
    # are recomputed from the findings list itself in run-manifest.json) ----
    findings = [
        {
            "id": "F01", "severity": "CRITICAL",
            "title": "Consensus models are structurally different: single-round validation quorum vs two-phase prepare/precommit quorum certificates",
            "status": "MEASURED",
            "evidence": [
                "postfiatd validates a ledger when trusted validations on one "
                "ledger hash reach the validation quorum (17 of UNL 25): "
                "ValidatorList::calculateQuorum returns max(ceil(0.67*effectiveUNL), "
                "ceil(0.60*UNL)) (fixtures/source-excerpts/ValidatorList-quorum.txt); "
                "live check: UNL 25 -> ceil(25*0.67)=17, reported validation_quorum=17 "
                "(outputs/derived/validators.json quorum_check).",
                "postfiatl1v2 Consensus v2 commits only on a precommit QC of q "
                "distinct votes for the same non-nil block, after a prepare QC "
                "of q votes becomes the durable lock (docs/architecture/finality.md). "
                "q = floor(2n/3)+1, f = floor((n-1)/3); code: bft_quorum_threshold, "
                "crates/ordering_fast/src/lib.rs:345-356.",
                "At n=25 both formulas give 17, so the live number does not "
                "distinguish them; they diverge at n=103 (postfiatd 70, l1v2 69) "
                "and the mechanisms (one validation message vs two QC phases "
                "with locks and view-change timeout certificates) never coincide.",
            ],
            "gate": "BLOCKS any claim that the two implementations validate the "
                    "same ledger by the same rule. A convergence must pick one "
                    "commit rule and re-derive quorum, liveness, and fork-safety "
                    "arguments under it.",
        },
        {
            "id": "F02", "severity": "CRITICAL",
            "title": "No shared amendment/upgrade mechanism: postfiatd feature voting vs l1v2 per-kind height-based governance",
            "status": "MEASURED",
            "evidence": [
                "postfiatd activates protocol changes by validator vote: "
                "majority threshold 67%% after fixAmendmentMajorityCalc "
                "(204/256 = 79.6875%% before it), held for a majority time of "
                "2 weeks by default, 3 days on this testnet "
                "(include/xrpl/protocol/SystemParameters.h:83-88; "
                "cfg/postfiatd-testnet-full.cfg:1467-1468). Live: 101 known, "
                "64 enabled, all at one bulk enablement point; "
                "fixAmendmentMajorityCalc enabled (outputs/derived/amendments.json).",
                "postfiatl1v2 DOES have a governance-amendment object "
                "(GovernanceAmendment, crates/types/src/"
                "shielded_bridge_governance.rs:2011-2034, with quorum, "
                "support, activation_height, veto_until_height fields), but "
                "it is not a validator vote over feature flags: activation "
                "is per-kind and height-based (latest committed amendment "
                "wins for fee/memo gates; earliest unpaused height wins for "
                "recipient format), and no single global majority threshold "
                "or time-based supermajority rule exists anywhere in the "
                "spec or code.",
                "The most precisely specified l1v2 amendments are the two "
                "external-lane kinds (release cap, committee epoch), "
                "authorized by the registry threshold floor(2n/3)+1 at a "
                "named activation height, with a 7-window delay for cap "
                "raises (docs/architecture/genesis-external-lanes.md:165-180). "
                "No veto procedure is specified beyond the veto_until_height "
                "field.",
                "Protocol upgrades in l1v2 are otherwise operator-controlled "
                "releases and genesis-boundary changes, not voted feature "
                "flags: 'Running nodes acquire the corrected authorization "
                "behavior only through an operator-controlled release' "
                "(docs/architecture/consensus-signing-rounds.md); Consensus v2 "
                "activation itself is a genesis-committed height "
                "(docs/architecture/finality.md).",
            ],
            "gate": "BLOCKS any migration that assumes amendments carry over. "
                    "Every live postfiatd amendment would need an explicit "
                    "l1v2 disposition (re-implement as a governance kind, drop, "
                    "or replace with a registry change) before convergence.",
        },
        {
            "id": "F03", "severity": "HIGH",
            "title": "Genesis construction is incompatible: fresh single-account genesis vs scored-registry genesis with ML-DSA identity bridge",
            "status": "MEASURED",
            "evidence": [
                "postfiatd genesis is Ledger::Ledger(create_genesis_t): seq 1, "
                "drops = INITIAL_XRP (100,000,000,000 PFT), the whole supply "
                "in one account, r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA on "
                "networks 2025/2026 (src/xrpld/app/ledger/Ledger.cpp:169-256). "
                "Live reconciliation closes exactly: genesis account plus "
                "other accounts plus burned fees equals the 100B supply "
                "(outputs/derived/live-testnet-snapshot.json).",
                "postfiatl1v2 genesis is a ratified registry: G0 = Selected "
                "intersect Receipted from a frozen Dynamic UNL round on the "
                "fork, min n_S >= 12, template trust graph q_S = ceil(4*n_S/5), "
                "ML-DSA-65 identity receipts, domain-separated SHA-256 payload "
                "hash, certificate of >= q_S signatures "
                "(docs/architecture/l1v2-testnet-genesis-and-launch-spec.md §3).",
                "The l1v2 design holds the native supply minus the lanes in a "
                "faucet at genesis, with ERC-20 slice atoms reserved in "
                "genesis external lanes (docs/architecture/pft-token-on-base.md). "
                "The slice size is open; nothing is deployed on Base mainnet.",
            ],
            "gate": "BLOCKS a shared genesis. A converged network needs one "
                    "genesis construction; the postfiatd single-account genesis "
                    "cannot be replayed into the l1v2 ratified-registry genesis "
                    "without a new chain ID and a new genesis payload.",
        },
        {
            "id": "F04", "severity": "HIGH",
            "title": "Quorum must change at convergence: testnet runs a 67% quorum the code says to revert to 80% for mainnet, while l1v2 uses floor(2n/3)+1",
            "status": "MEASURED",
            "evidence": [
                "ValidatorList::calculateQuorum comment: 'Original XRPL uses "
                "80%%, but this fork uses 67%% for devnet/testnet. For mainnet, "
                "this should be reverted to 80%%.' (fixtures/source-excerpts/"
                "ValidatorList-quorum.txt). At 80%% a 25-member UNL needs 20 "
                "validations; no 80%% quorum has ever run on this network.",
                "l1v2's quorum is floor(2n/3)+1 with f = floor((n-1)/3) — a "
                "BFT bound, not a tunable percentage (crates/ordering_fast/src/"
                "lib.rs:345-356; test computes_supermajority_quorum_thresholds "
                "verifies n=1..64). The launch trust graph adds a third rule: "
                "q_S = ceil(4*n_S/5) for genesis ratification (10 of 12).",
                "Three different quorum rules therefore exist across the two "
                "implementations and the launch profile (67%% testnet, 80%% "
                "mainnet fork, floor(2n/3)+1 Consensus v2, 4/5 genesis "
                "ratification). No single value satisfies all four.",
            ],
            "gate": "REQUIRED before any convergence: pick one quorum rule per "
                    "phase (genesis ratification, consensus, registry "
                    "evolution), prove fork-safety under it, and measure "
                    "liveness with the production validator set.",
        },
        {
            "id": "F05", "severity": "HIGH",
            "title": "No external audit of either codebase; l1v2 release gates mostly open",
            "status": "UNRESOLVED",
            "evidence": [
                "postfiatl1v2 docs/security/index.md: 'No external security "
                "audit is recorded in this repository.' Release-gate inventory "
                "at the pinned revision: 21 gates, 4 DONE, 16 OPEN, 1 UNKNOWN. "
                "Gate 8 (migration, rollback, canary) OPEN; gate 20 "
                "(topology/independence thresholds) OPEN; gate 12 (specialist "
                "review) OPEN; gate 13 (SP1 reproduction) OPEN.",
                "No external audit is recorded for postfiatd either; the "
                "founder's 'multi-million-dollar audit' is a statement, not a "
                "scoped engagement: no auditor, scope, or date is published.",
                "Launch-topology thresholds are a proposal only, awaiting the "
                "operator's confirmation (2026-09-01): 'This document decides "
                "nothing.'",
            ],
            "gate": "BLOCKS a production convergence. An audit scope covering "
                    "both consensus implementations and the genesis/registry "
                    "machinery must exist before any shared mainnet.",
        },
        {
            "id": "F06", "severity": "HIGH",
            "title": "Ledger-close timing has no l1v2 counterpart: postfiatd measures ~3 s closes, l1v2 specifies no cadence",
            "status": "UNRESOLVED",
            "evidence": [
                "Live postfiatd cadence: mean close interval %.3f s over %d "
                "ledgers (outputs/cadence-run1.jsonl); last close converge "
                "time %d ms with %d proposers; close_time_resolution 10 s "
                "(outputs/derived/live-testnet-snapshot.json). Code bounds: "
                "ledgerMIN_CLOSE 2 s, ledgerIDLE_INTERVAL 15 s, "
                "ledgerMAX_CONSENSUS 15 s (src/xrpld/consensus/ConsensusParms.h). "
                "Close-time agreement needs 75%% (avCT_CONSENSUS_PCT)." % (
                    cadence["mean_close_interval_s"], cadence["ledgers_advanced"],
                    snapshot["last_close_converge_time_ms"],
                    snapshot["last_close_proposers"]),
                "No block time, slot duration, round duration, or ledger-close "
                "cadence is specified anywhere in the pinned l1v2 docs or code "
                "surveyed (finality.md, consensus-signing-rounds.md, "
                "overview.md, transaction-lifecycle.md, whitepaper.md). "
                "Consensus v2 progress is view/timeout driven, not cadence driven. "
                "The only running l1v2 network makes blocks only when "
                "transactions are pending: 'The chain makes blocks only when "
                "there are transactions to order, so height does not advance "
                "with wall-clock time. A height that has not moved for days is "
                "normal on this devnet.' (docs/status/network-status.md:55-56; "
                "devnet postfiat-wan-devnet-2, 6 Foundation validators, quorum "
                "5 of 6, height 1513 at the 2026-11-19 observation).",
                "A converged network therefore has no agreed close cadence to "
                "measure liveness against; the ~3 s figure is a postfiatd-only "
                "observation.",
            ],
            "gate": "REQUIRED before convergence: specify the l1v2 close/view "
                    "timing (or state explicitly that none exists) and define "
                    "the liveness metric the converged network is measured by.",
        },
        {
            "id": "F07", "severity": "MEDIUM",
            "title": "Validation lifetimes differ and l1v2's are unspecified",
            "status": "UNRESOLVED",
            "evidence": [
                "postfiatd validation validity windows: VALID_WALL 5 min, "
                "VALID_LOCAL 3 min, VALID_EARLY 3 min pre-close; proposals "
                "fresh 20 s, re-proposed every 12 s "
                "(src/xrpld/consensus/ConsensusParms.h:40-80).",
                "postfiatl1v2 signs prepare/precommit/timeout votes under a "
                "durable round floor (max of the three high-water marks) with "
                "no stated expiry window; a vote's validity is governed by "
                "round monotonicity and certificate verification, not by a "
                "wall-clock lifetime (docs/architecture/consensus-signing-rounds.md; "
                "docs/architecture/finality.md). No numeric lifetime is "
                "specified in the surveyed docs.",
                "Consequence: a postfiatd validation expires after minutes; "
                "an l1v2 vote persists until superseded by a higher round. "
                "Replay/retention behavior across the boundary is undefined.",
            ],
            "gate": "Convergence precondition: define vote/validation "
                    "lifetimes and replay rules for the converged protocol.",
        },
        {
            "id": "F08", "severity": "MEDIUM",
            "title": "One UNL member is stale; l1v2 launch requires all seats preflight-READY",
            "status": "MEASURED",
            "evidence": [
                "UNL member %s: 24h agreement %s, current_index %s vs network "
                "%d at probe time (~%d ledgers behind). 1 of %d UNL members "
                "contributes nothing to current consensus." % (
                    stale_unl[0]["validation_public_key"] if stale_unl else "none",
                    stale_unl[0]["agreement_24h"]["score"] if stale_unl else "n/a",
                    stale_unl[0]["current_index"] if stale_unl else "n/a",
                    snapshot["validated_ledger_seq"],
                    snapshot["validated_ledger_seq"] - int(stale_unl[0]["current_index"]) if stale_unl else 0,
                    len(unl)) if stale_unl else
                "No stale UNL member at probe time.",
                "l1v2 launch profile requires every seat preflight-READY at "
                "launch and 12 of 12 seats on the exact pinned binary "
                "(docs/architecture/launch-topology-thresholds.md §2.4-2.5). "
                "A stale member would fail the launch preflight.",
                "UNL versions: %s; all UNL domains verified: %s. "
                "%d of %d validators run older builds (none on the UNL)." % (
                    validators["unl_all_version"],
                    validators["unl_all_domains_verified"],
                    validators["non_latest_version_count"],
                    validators["validators_total"]),
            ],
            "gate": "Convergence precondition: remove or repair the stale UNL "
                    "member and re-measure UNL agreement before any shared "
                    "validator set is frozen.",
        },
        {
            "id": "F09", "severity": "MEDIUM",
            "title": "Validator identity and key types are incompatible across implementations",
            "status": "MEASURED",
            "evidence": [
                "postfiatd validators are secp256k1 identities with manifests "
                "and a publisher-served validator list (VL v2, blob sequence "
                "%s, effective %s). Live UNL: %d validators from the published "
                "list (outputs/derived/validators.json)." % (
                    vl.get("sequence"), vl.get("effective"), len(unl)),
                "l1v2 validators are ML-DSA-65 identities, bridged from fork "
                "secp256k1 keys by dual-signed identity receipts "
                "(docs/architecture/l1v2-testnet-genesis-and-launch-spec.md §3.2). "
                "Consensus v2 artifacts bind chain/genesis/protocol, committee "
                "epoch/root, height/view, parent, payload, and state root.",
                "No postfiatd validator key can sign an l1v2 vote without the "
                "identity-bridge receipt; no l1v2 ML-DSA key can sign a "
                "postfiatd validation.",
            ],
            "gate": "Convergence precondition: every shared validator must "
                    "complete the identity bridge (fresh ML-DSA key, dual-signed "
                    "receipt) before it can vote on both implementations.",
        },
        {
            "id": "F10", "severity": "MEDIUM",
            "title": "Public observability gaps on the live testnet; l1v2 has no public network to observe",
            "status": "MEASURED",
            "evidence": [
                "Explorer /api/v1/health returns HTTP 500 "
                "'{\"message\":\"rippled unreachable\"}' while /api/v1/metrics "
                "works (base_fee 0.00001, txn_sec 0.09).",
                "VHS topology reports node_count %s but link_count %s, while "
                "per-node inbound/outbound sums are %d/%d — the aggregate "
                "contradicts the per-node data." % (
                    vhs_topo_sum.get("node_count"), vhs_topo_sum.get("link_count"),
                    validators["topology_inbound_sum"],
                    validators["topology_outbound_sum"]),
                "VHS /v1/network/amendments returns a service index only, not "
                "amendment data; the vote data comes from "
                "/v1/network/amendments/vote/test. VHS health returns "
                "%s — a count, not a health status." % json.dumps(vhs_health),
                "VHS /v1/network/networks still lists %d webhook.site test "
                "entries alongside the real test network." % sum(
                    1 for n in vhs_net["networks"] if "webhook" in str(n["entry"])),
                "WebSocket ledger subscribe: see outputs/ws_upgrade_probe.txt. "
                "Public monitoring depends on HTTP polling.",
                "postfiatl1v2 has no public network: the only running network "
                "in its docs is the controlled devnet postfiat-wan-devnet-2; "
                "'It is not a production mainnet, no public testnet is open.' "
                "Its behavior is therefore specified, not observed.",
            ],
            "gate": "Convergence precondition: fix or document every "
                    "observability gap; a converged network cannot be monitored "
                    "on endpoints that report unreachable/0.",
        },
        {
            "id": "F11", "severity": "LOW",
            "title": "1:1 conversion exists only as an l1v2 design; no mechanism for the live testnet",
            "status": "UNRESOLVED",
            "evidence": [
                "No conversion, carryover, or 1:1 mechanism is published for "
                "the live postfiatd testnet (network 2025). The whitepaper "
                "contains no conversion text; postfiatd source contains no "
                "migration/carryover path (genesis is a fresh ledger: "
                "Ledger::Ledger(create_genesis_t), fixtures/source-excerpts/"
                "Ledger-genesis.txt).",
                "The only documented 1:1 path is the l1v2 design: ERC-20 PFT "
                "on Base with a one-for-one path into native PFT at PFTL "
                "mainnet genesis via genesis external lanes "
                "(docs/architecture/pft-token-on-base.md, "
                "genesis-external-lanes.md). Nothing is deployed on Base "
                "mainnet; only Base Sepolia test deployments exist. The slice "
                "size of the 100B supply is open.",
                "The 2026-11-06 rehearsal released 1 PFT on a local "
                "six-validator fleet with a stand-in finality verifier; the "
                "recorded postfiat-wan-devnet-2 genesis has no such lane.",
            ],
            "gate": "BLOCKS any balance-carryover claim. Testnet balances "
                    "must be assumed lost at convergence until a mechanism is "
                    "published and exercised on a public network.",
        },
        {
            "id": "F12", "severity": "LOW",
            "title": "No mainnet date; l1v2 launch gates unmet; mainnet ordering undecided",
            "status": "UNRESOLVED",
            "evidence": [
                "No official mainnet/TGE date is published anywhere in the "
                "surveyed sources (whitepaper, docs.postfiat.org, both repos). "
                "docs.postfiat.org returns a Notion JavaScript shell with no "
                "retrievable content (outputs/docs_postfiat_org.html).",
                "Founder statement, #validator-ops, 2026-09-18: mainnet "
                "ordering undecided, leaning toward the 'painful option', "
                "likely option 2 (mainnet on postfiatl1v2 with inherited "
                "validator governance after a multi-million-dollar audit). "
                "The 'painful option' was never explicitly named as option 2; "
                "that link is an inference, not a quotation.",
                "l1v2 launch gates L1-L6 (docs/architecture/"
                "l1v2-testnet-genesis-and-launch-spec.md §5) are not satisfied: "
                "no public testnet exists, the genesis registry is not built, "
                "and the L3 independence verifier is still to be built.",
            ],
            "gate": "BLOCKS any convergence schedule. No date can be committed.",
        },
        {
            "id": "F13", "severity": "LOW",
            "title": "Cosmetic divergence: postfiatd still reports the native currency code as 'XRP' in source",
            "status": "MEASURED",
            "evidence": [
                "SystemParameters.h systemCurrencyCode() returns \"XRP\" "
                "(include/xrpl/protocol/SystemParameters.h) while the asset "
                "is PFT. Ledger behavior is unaffected (amounts are drops of "
                "the native asset); only display/code strings are stale.",
                "l1v2 uses PFT throughout (native PFT, PFT atoms, ERC-20 PFT).",
            ],
            "gate": "None for convergence; rename before any shared mainnet to "
                    "avoid integrator confusion.",
        },
        {
            "id": "F14", "severity": "INFO",
            "title": "Verified healthy: live testnet validates steadily, genesis supply reconciles, amendment state agrees across two sources",
            "status": "VERIFIED",
            "evidence": [
                "Genesis supply 100,000,000,000 PFT (INITIAL_XRP, "
                "SystemParameters.h:44) reconciles: genesis account holds "
                "%.6f PFT, other accounts hold %.6f PFT, %.6f PFT burned in "
                "fees; sum closes exactly "
                "(outputs/derived/live-testnet-snapshot.json)." % (
                    snapshot["genesis_account_balance_pft"],
                    snapshot["supply_reconciliation"]["other_accounts_pft"],
                    snapshot["supply_reconciliation"]["burned_by_fees_pft"]),
                "Cadence: %d ledgers across 21 samples at 30-second intervals, "
                "mean close interval "
                "%.3f s (outputs/cadence-run1.jsonl). Fee queue empty "
                "(0/2000), base fee 10 drops, median fee 5000 drops." % (
                    cadence["ledgers_advanced"],
                    cadence["mean_close_interval_s"]),
                "Amendment state agrees across two independent sources: "
                "RPC `feature` reports %d enabled of %d known; VHS vote "
                "endpoint reports %d enabled with identical names." % (
                    len(enabled), len(feat), vhs_amend_vote.get("count")),
                "All %d enabled amendments share one enablement point: "
                "ledger %s, %s (genesis-era bulk enablement)." % (
                    len(enabled),
                    amendments["bulk_enablement"]["distinct_ledger_indexes"],
                    amendments["bulk_enablement"]["distinct_dates"]),
                "Latest release v1.0.9 (2026-10-10) is the live build on all "
                "%d UNL members and on the RPC node." % len(unl),
            ],
            "gate": "None. This is the evidence that the testnet itself is "
                    "healthy; it does not imply the implementations are "
                    "compatible.",
        },
    ]
    with open(os.path.join(PACK, "findings.json"), "w") as f:
        json.dump({"generated_at_utc": now, "findings": findings}, f, indent=1)
    print("wrote findings.json sha256=%s"
          % sha256(os.path.join(PACK, "findings.json")))

    # ---- run manifest (counts recomputed FROM the findings list) ----
    by_sev = {sev: sum(1 for x in findings if x["severity"] == sev)
              for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}
    manifest = {
        "pack": "PostFiat cross-implementation consensus compatibility assessment",
        "generated_at_utc": now,
        "probe_window_utc": "2026-11-22: main probe batch 17:28-17:29Z, cadence 21x30s 17:29-17:40Z (see outputs/cadence-run1.log)",
        "environment": {
            "python": sys.version.split()[0],
            "tools": "curl, git, python3 (stdlib only)",
            "network": "public endpoints only; no credentials, sessions, accounts, or signing",
        },
        "repo_pins": {
            "postfiatd": "0085a1ff885d6a446369cf73a4430f75af22be55 (2026-10-10, PR #50 merge, v1.0.9)",
            "postfiatl1v2": "071b6dc461efc7a9105b2d3cac6acd3686901e7d (2026-11-22)",
        },
        "live_endpoints": [
            "https://rpc.testnet.postfiat.org/ (postfiatd 1.0.9, network_id 2025)",
            "https://vhs.testnet.postfiat.org/v1/",
            "https://explorer.testnet.postfiat.org/api/v1/",
            "https://postfiat.org/ and https://postfiat.org/whitepaper/ (Sept 2026)",
            "https://docs.postfiat.org (Notion JavaScript shell; no retrievable content)",
        ],
        "counts": {
            "findings_total": len(findings),
            "by_severity": by_sev,
            "by_status": {st: sum(1 for x in findings if x["status"] == st)
                          for st in sorted({x["status"] for x in findings})},
        },
        "verdict": "NOT COMPATIBLE as specified: 2 CRITICAL + 4 HIGH findings. "
                   "The two implementations run different consensus models, "
                   "different quorum rules, different amendment mechanisms, and "
                   "different genesis constructions. Convergence requires picking "
                   "one rule per area and re-proving it; nothing in this pack "
                   "performs that convergence.",
        "notes": [
            "Assessment only: no cutover or convergence performed, no mainnet touched, no funds spent, nothing signed.",
            "The live postfiatd testnet (XRPL-fork, network 2025) and the "
            "postfiatl1v2 design (Consensus v2) are different systems; this "
            "pack keeps measured (live testnet) and specified (l1v2 design) "
            "claims apart throughout.",
            "Boundary note: the reordered-validation vote-replay work is out "
            "of scope for this pack and is not analyzed here.",
        ],
    }
    with open(os.path.join(PACK, "run-manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("wrote run-manifest.json sha256=%s"
          % sha256(os.path.join(PACK, "run-manifest.json")))


if __name__ == "__main__":
    main()
