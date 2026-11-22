# Citations

Pinned primary sources. "Live" means probed 2026-11-22 17:28–17:40 UTC;
"pinned" means the file at the stated commit, verified with `grep -n`
against a local clone.

## Repositories

- postfiatd — `https://github.com/postfiatorg/postfiatd`,
  commit `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50
  merge, v1.0.9).
- postfiatl1v2 — `https://github.com/postfiatorg/postfiatl1v2`,
  commit `071b6dc461efc7a9105b2d3cac6acd3686901e7d` (2026-11-22 01:41 UTC).
  `main` advanced after this pin; the pin is the assessed revision.

## Live endpoints (probed)

- `https://rpc.testnet.postfiat.org/` — postfiatd 1.0.9, network_id 2025.
- `https://vhs.testnet.postfiat.org/v1/` — Validator History Service.
- `https://explorer.testnet.postfiat.org/api/v1/` — explorer metrics
  (health endpoint returns HTTP 500 `rippled unreachable`).
- `https://postfiat.org/` and `https://postfiat.org/whitepaper/` (Sept 2026).
- `https://postfiat.org/testnet_vl.json` — validator list, VL v2, blob
  sequence 30, effective 2026-11-17T20:10:08Z, expiration 2028-03-31T16:14:53Z.
- `https://docs.postfiat.org` — Notion JavaScript shell; no retrievable content.

## postfiatd source (pinned)

- `src/xrpld/app/misc/detail/ValidatorList.cpp:1845-1933` — quorum formula
  (67% testnet, revert to 80% for mainnet).
- `src/xrpld/consensus/ConsensusParms.h:51,59,66,69,72,79,82-99,126,146-156,160`
  — validation lifetimes, proposal freshness, consensus thresholds, timing bounds.
- `src/xrpld/consensus/Consensus.h:496,507,543,1169,1252,1367` — consensus phases.
- `src/xrpld/consensus/LedgerTiming.h:35-50` — close-time resolutions.
- `src/xrpld/app/misc/detail/AmendmentTable.cpp:326-342,368-372,886-918` —
  majority threshold and activation.
- `include/xrpl/protocol/SystemParameters.h:44-45,83,85,88` — INITIAL_XRP,
  amendment thresholds, 2-week majority time.
- `include/xrpl/protocol/detail/features.macro:45-46,104` — PF amendments,
  AmendmentMajorityCalc fix.
- `src/xrpld/app/ledger/Ledger.cpp:169-256` — genesis ledger construction.
- `src/xrpld/app/main/Application.cpp:1286-1292` — amendment table wiring.
- `cfg/postfiatd-testnet-full.cfg:1464-1468` and
  `cfg/postfiatd-mainnet-full.cfg:1459-1460` — network_id and the 3-day
  amendment-majority override (testnet only).

## postfiatl1v2 source (pinned)

- `crates/ordering_fast/src/lib.rs:338-356,2286-2300` — BFT quorum/fault
  formulas and their test (n=1..64).
- `docs/architecture/finality.md:3-22,44-50` — finality modes, commit rule,
  view change.
- `docs/architecture/consensus-signing-rounds.md:5-9` — durable round floor.
- `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:27,105-108,110-142,143-178,179-202,301-316`
  — genesis registry, identity bridge, trust graph, ratification, launch gates.
- `docs/architecture/launch-topology-thresholds.md:11-13,18-24` — launch
  thresholds (proposal only).
- `docs/architecture/genesis-external-lanes.md:61,165-180` — faucet, governed
  lane amendments.
- `docs/architecture/pft-token-on-base.md:14,41` — 100B supply, slice open,
  nothing on Base mainnet.
- `docs/status/network-status.md:11-14,26,48-49,55-56` — devnet facts,
  quorum 5 of 6, blocks on demand.
- `docs/security/index.md:9` — no external audit recorded.
- `docs/status/release-gate-inventory.md` — 21 gates: 4 DONE, 16 OPEN,
  1 UNKNOWN.
- `crates/types/src/shielded_bridge_governance.rs:2011-2034,51-61` —
  GovernanceAmendment object and per-kind activation semantics.
- `docs/whitepaper.md:215` (§1.3) — quorum cross-check at n=35; supply partition.

## External

- Analysis of the XRP Ledger Consensus Protocol (arXiv:1802.07242), Theorem 8
  — cited in the postfiatd quorum comment (`ValidatorList.cpp:1902-1914`).
- Founder statement, #validator-ops, 2026-09-18: mainnet ordering undecided,
  leaning toward the "painful option", likely option 2 (mainnet on
  postfiatl1v2 with inherited validator governance after a
  multi-million-dollar audit). The "painful option" was never explicitly
  named as option 2; that link is an inference, not a quotation.
