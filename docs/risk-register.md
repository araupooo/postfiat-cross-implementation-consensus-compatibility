# Convergence Risk Register

Severity-scored risks for converging postfiatd (live testnet, network 2025)
and postfiatl1v2 (Consensus v2 design) into one network. Counts are computed
from the table below: 16 risks — 7 blockers, 3 benign differences,
6 unknowns. (Recomputed by script; see `docs/methodology.md`.)

Severity scale: CRITICAL = convergence cannot proceed as specified;
HIGH = a decision and re-proof are required before convergence;
MEDIUM = a precondition to clear before freezing a shared validator set;
LOW = a known gap with a bounded fix; INFO = a verified healthy fact.

Boundary note: the reordered-validation vote-replay work is out of scope for
this pack and is not analyzed here.

## Blockers

| ID | Risk | Severity | Finding | Evidence |
| --- | --- | --- | --- | --- |
| R01 | Different commit rules: single-round validation quorum vs two-phase prepare/precommit QCs | CRITICAL | F01 | `docs/divergence-map.md` §1–2; D12 |
| R02 | No shared amendment mechanism: 67%-for-2-weeks vote vs per-kind height-based governance | CRITICAL | F02 | `docs/divergence-map.md` §3; D07–D08 |
| R03 | Incompatible genesis: single-account fresh ledger vs ratified registry with identity bridge | HIGH | F03 | `docs/divergence-map.md` §4; D09–D10 |
| R04 | Three quorum rules in play (67% testnet / 80% mainnet fork / floor(2n/3)+1 v2, plus 4/5 ratification) | HIGH | F04 | `docs/divergence-map.md` §1.4; D01–D03 |
| R05 | No external audit of either codebase; l1v2 release gates 4/21 DONE | HIGH | F05 | `docs/security/index.md:9`; release-gate inventory 4 DONE / 16 OPEN / 1 UNKNOWN |
| R06 | No 1:1 testnet-to-mainnet conversion; ERC-20 slice size open; nothing on Base mainnet | LOW | F11 | `docs/architecture/pft-token-on-base.md:14,41` |
| R07 | No mainnet date; l1v2 launch gates L1–L6 unmet; mainnet ordering undecided | LOW | F12 | Founder statement 2026-09-18; launch spec §5 |

## Benign differences

| ID | Risk | Severity | Finding | Evidence |
| --- | --- | --- | --- | --- |
| R08 | Quorum arithmetic agrees at n=25 (17) and n=6 (5) — values agree, rules differ | INFO | F01 | D01; agreement is arithmetic coincidence, not a shared rule |
| R09 | Total supply agrees: 100B PFT in both systems | INFO | F03 | `SystemParameters.h:44`; `pft-token-on-base.md:14` |
| R10 | Native currency code "XRP" in postfiatd source vs PFT in l1v2 — cosmetic only | LOW | F13 | `SystemParameters.h` `systemCurrencyCode()` |

## Unknowns

| ID | Risk | Severity | Finding | Evidence |
| --- | --- | --- | --- | --- |
| R11 | l1v2 ledger-close cadence is unspecified; no liveness metric exists for a converged network | HIGH | F06 | `docs/status/network-status.md:55-56` (blocks on demand); D04–D06 |
| R12 | l1v2 vote/validation lifetimes are unspecified; replay/retention across the boundary is undefined | MEDIUM | F07 | `ConsensusParms.h:51,59,66`; no l1v2 lifetime specified; D11 |
| R13 | l1v2 veto procedure is unspecified beyond a `veto_until_height` field | MEDIUM | F02 | `shielded_bridge_governance.rs:2011-2034`; claim C18 |
| R14 | l1v2 launch topology thresholds are a proposal only, awaiting operator confirmation | MEDIUM | F05 | `launch-topology-thresholds.md:11-13`; claim C06 |
| R15 | One UNL member stale (paymuslam.top, 0.00000 24h agreement); l1v2 launch requires all seats preflight-READY | MEDIUM | F08 | `outputs/derived/validators.json`; claim C30 |
| R16 | Validator identity bridge untested at scale: no shared validator has completed it on a public network | MEDIUM | F09 | Launch spec §3.2; claim C29 |

## Count check

- Total risks: 16
- Blockers: 7 (R01–R07)
- Benign differences: 3 (R08–R10)
- Unknowns: 6 (R11–R16)
- 7 + 3 + 6 = 16. By severity: CRITICAL 2, HIGH 4, MEDIUM 5, LOW 3, INFO 2
  (R01–R02 CRITICAL; R03–R05, R11 HIGH; R12–R16 MEDIUM; R06, R07, R10 LOW;
  R08, R09 INFO) — 2 + 4 + 5 + 3 + 2 = 16.
