# Evidence Index

Every claim traces to an unedited output or a pinned source file. Raw log
URLs (repository `postfiat-cross-implementation-consensus-compatibility`,
expected public repository name; raw URLs resolve once the repository is
created):

- `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/probe-run.log`
- `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/cadence-run1.log`
- `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/fresh-clone-compare.log`

## Findings → evidence

| Finding | Severity | Evidence |
| --- | --- | --- |
| F01 commit-rule divergence | CRITICAL | `fixtures/source-excerpts/ValidatorList-quorum.txt`; `l1v2-finality.txt`; D12 |
| F02 amendment-mechanism divergence | CRITICAL | `fixtures/source-excerpts/AmendmentTable-threshold.txt`; `l1v2-governed-lane-amendments.txt`; `l1v2-governance-amendment.txt`; D07–D08 |
| F03 genesis incompatibility | HIGH | `fixtures/source-excerpts/Ledger-genesis.txt`; `l1v2-genesis-registry.txt`; D09–D10 |
| F04 quorum must change | HIGH | `ValidatorList-quorum.txt`; `l1v2-bft-quorum-threshold.txt`; D01–D03 |
| F05 no audit; gates open | HIGH | `l1v2-security-index.txt`; release-gate inventory (4 DONE / 16 OPEN / 1 UNKNOWN) |
| F06 no l1v2 close cadence | HIGH | `outputs/cadence-run1.jsonl`; `l1v2-network-status.txt`; D04–D06 |
| F07 validation lifetimes differ | MEDIUM | `ConsensusParms.txt`; `l1v2-consensus-signing-rounds.txt`; D11 |
| F08 stale UNL member | MEDIUM | `outputs/derived/validators.json` (stale_unl_members) |
| F09 identity/key incompatibility | MEDIUM | `outputs/derived/validators.json`; `l1v2-genesis-registry.txt`; D13 |
| F10 observability gaps | MEDIUM | `outputs/explorer_health.json` (HTTP 500); `outputs/vhs_topology.json`; `outputs/ws_upgrade_probe.txt` |
| F11 no 1:1 conversion | LOW | `l1v2-pft-token-on-base.txt`; `Ledger-genesis.txt`; D09 |
| F12 no mainnet date | LOW | `l1v2-network-status.txt`; `outputs/docs_postfiat_org.html`; D15 |
| F13 cosmetic "XRP" code | LOW | `include/xrpl/protocol/SystemParameters.h` (see `fixtures/source-hashes.json`) |
| F14 verified healthy | INFO | `outputs/derived/live-testnet-snapshot.json`; `outputs/derived/cadence.json`; `outputs/derived/amendments.json` |

## Claims → evidence

See `docs/claim-index.md` (30 claims: 12 VERIFIED, 10 SPECIFIED,
8 UNVERIFIED). Each claim row cites its evidence file.

## Scenarios → evidence

See `outputs/derived/differential-probes.json` (15 scenarios: 1 PASS,
8 DIVERGENT, 6 UNVERIFIED). Each scenario lists its evidence files.

## Probe outputs → endpoints

See `outputs/PROBE-MANIFEST.md` (per-file endpoint, collection time, and
full SHA-256).
