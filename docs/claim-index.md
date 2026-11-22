# Claim-to-Evidence Index

Every substantive claim in this pack, its status, and the evidence behind it.
Statuses: **VERIFIED** (measured live and/or confirmed in pinned code),
**SPECIFIED** (stated in the pinned l1v2 design with a file:line citation,
not observed live), **UNVERIFIED** (no evidence on either side, or the
specification defines no value — never inferred).

Counts are computed from the table below: 30 claims — 12 VERIFIED,
10 SPECIFIED, 8 UNVERIFIED. (Recomputed by script; see `docs/methodology.md`.)

Boundary note: the reordered-validation vote-replay work is out of scope for
this pack and is not analyzed here.

## Quorum

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| C01 | postfiatd validation quorum is max(ceil(0.67×effective UNL), ceil(0.60×UNL)); live UNL 25 → 17 | VERIFIED | `ValidatorList.cpp:1845-1933`; live `validation_quorum`=17, `outputs/derived/validators.json` |
| C02 | l1v2 quorum is q = floor(2n/3)+1, f = floor((n-1)/3) | SPECIFIED | `crates/ordering_fast/src/lib.rs:338-356`; `docs/architecture/finality.md:5-6`; test verifies n=1..64 |
| C03 | The two quorum formulas agree at n=25 (17) and first diverge at n=103 (70 vs 69) | VERIFIED | Computed over n=1..200, `outputs/derived/differential-probes.json` D01–D02 |
| C04 | l1v2 genesis ratification quorum is q_S = ceil(4n_S/5), 10 of 12 at the launch minimum | SPECIFIED | `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:148-149,166-167` |
| C05 | postfiatd mainnet quorum should revert to 80% per the code comment; no 80% quorum has ever run on this network | SPECIFIED | `ValidatorList.cpp:1898-1901` comment; no live 80% measurement exists |
| C06 | The l1v2 launch topology thresholds (2-seat provider cap, country caps, n_S ≥ 12) are adopted | UNVERIFIED | `docs/architecture/launch-topology-thresholds.md:11-13` — "This document decides nothing"; awaiting operator confirmation |

## Validation and ledger close

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| C07 | postfiatd validation lifetimes: 5 min wall, 3 min local, 3 min early; proposals fresh 20 s, re-proposed every 12 s | VERIFIED | `src/xrpld/consensus/ConsensusParms.h:51,59,66,69,72` |
| C08 | Live postfiatd close cadence: mean 3.046 s over 197 ledgers; last close converged in 2001 ms with 24 proposers | VERIFIED | `outputs/cadence-run1.jsonl`; `outputs/derived/cadence.json`, `live-testnet-snapshot.json` |
| C09 | l1v2 commits only on a precommit QC of q votes after a prepare QC of q votes becomes the durable lock | SPECIFIED | `docs/architecture/finality.md:7-22`; `docs/architecture/consensus-signing-rounds.md:5-9` |
| C10 | l1v2 makes blocks only when transactions are pending; height does not advance with wall-clock time | SPECIFIED | `docs/status/network-status.md:55-56`; devnet height 1513 at 2026-11-19 observation |
| C11 | l1v2 ledger close-time resolution | UNVERIFIED | No close-time resolution is specified in the surveyed l1v2 docs or code |
| C12 | l1v2 validation/vote lifetime (wall-clock expiry) | UNVERIFIED | No numeric lifetime is specified; votes persist under the durable round floor |
| C13 | postfiatd close-time agreement needs 75% of nodes; avalanche cutoffs 50/65/70/95% | VERIFIED | `src/xrpld/consensus/ConsensusParms.h:146-156,160` |

## Amendment activation

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| C14 | postfiatd amendment threshold is 67% after fixAmendmentMajorityCalc (79.6875% before it); the fix is enabled live | VERIFIED | `SystemParameters.h:83,85`; `AmendmentTable.cpp:326-342,368-372`; `outputs/derived/amendments.json` |
| C15 | postfiatd amendment majority hold: 3 days on this testnet, 2-week code default | VERIFIED | `cfg/postfiatd-testnet-full.cfg:1467-1468`; `SystemParameters.h:88`; `AmendmentTable.cpp:886-918` |
| C16 | l1v2 governance amendments are per-kind, height-based (latest-wins for fee/memo gates; earliest-unpaused-wins for recipient format) | SPECIFIED | `crates/types/src/shielded_bridge_governance.rs:2011-2034,51-61` |
| C17 | l1v2 lane amendments (release cap, committee epoch) use the registry threshold floor(2n/3)+1 at a named activation height; cap raises apply 7 windows later | SPECIFIED | `docs/architecture/genesis-external-lanes.md:165-180` |
| C18 | l1v2 veto procedure (who can veto, how) | UNVERIFIED | Only a `veto_until_height` field exists; no doc describes the procedure |
| C19 | PF_ValidatorVoteTracking and PF_AccountExclusion exist in postfiatd code but are NOT enabled on the live network | VERIFIED | `features.macro:45-46`; `outputs/derived/amendments.json` |
| C20 | 64 enabled amendments, all at one bulk enablement point (ledger 86785, 2026-02-09T14:31:12Z), agreeing across RPC `feature` and the VHS vote endpoint | VERIFIED | `outputs/derived/amendments.json`; `vhs_amendments_vote_test.json` |

## Genesis construction

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| C21 | postfiatd genesis is a single-account fresh ledger: seq 1, 100B PFT in r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA; live reconciliation closes exactly | VERIFIED | `src/xrpld/app/ledger/Ledger.cpp:169-256`; `SystemParameters.h:44-45`; `outputs/derived/live-testnet-snapshot.json` |
| C22 | l1v2 genesis is a ratified registry: G0 = Selected ∩ Receipted, ML-DSA-65 identity receipts, certificate of >= q_S signatures | SPECIFIED | `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:105-108,110-142,143-178,179-202` |
| C23 | Total supply is 100 billion PFT in both systems | VERIFIED | postfiatd `INITIAL_XRP` (SystemParameters.h:44); l1v2 "fixed, decided 2026-10-28" (`pft-token-on-base.md:14`) |
| C24 | The ERC-20 slice size of the 100B supply (`reserved_atoms` for mainnet) | UNVERIFIED | `pft-token-on-base.md:14` — "the slice size is open" |
| C25 | A 1:1 testnet-to-mainnet conversion mechanism exists | UNVERIFIED | No mechanism in either codebase; the only specified one-for-one path is ERC-20-on-Base → native at mainnet genesis via lanes |
| C26 | An official mainnet/TGE date exists | UNVERIFIED | None published in the surveyed sources; "TGE" appears 0 times in l1v2 docs/whitepaper/roadmap |
| C27 | An external audit is recorded for either codebase | UNVERIFIED | l1v2 `docs/security/index.md:9` — none recorded; none recorded for postfiatd either |
| C28 | The only running l1v2 network is postfiat-wan-devnet-2: 6 Foundation validators, quorum 5 of 6, height 1513 at 2026-11-19, no public RPC | SPECIFIED | `docs/status/network-status.md:11-14,26,48-49` |
| C29 | A shared validator must complete the ML-DSA identity bridge before it can vote on both implementations | SPECIFIED | `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:110-142` |
| C30 | One UNL member (paymuslam.top) is stale: 0.00000 24h agreement, ~95,848 ledgers behind at probe time | VERIFIED | `outputs/derived/validators.json` (stale_unl_members); VHS validators endpoint |

## Count check

- Total claims: 30
- VERIFIED: 12 (C01, C03, C07, C08, C13, C14, C15, C19, C20, C21, C23, C30)
- SPECIFIED: 10 (C02, C04, C05, C09, C10, C16, C17, C22, C28, C29)
- UNVERIFIED: 8 (C06, C11, C12, C18, C24, C25, C26, C27)
- 12 + 10 + 8 = 30. Every claim in the table above is counted exactly once.
