# File-and-Line Divergence Map: postfiatd vs postfiatl1v2

Pinned revisions: postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55`
(2026-10-10, PR #50 merge, v1.0.9); postfiatl1v2
`071b6dc461efc7a9105b2d3cac6acd3686901e7d` (2026-11-22). Every line number
below was verified with `grep -n` against local clones of those revisions.
Full SHA-256 of every cited source file: `fixtures/source-hashes.json`.
Pinned excerpts: `fixtures/source-excerpts/`.

Measured values are from the live postfiatd testnet (network 2025), probed
2026-11-22 17:28–17:40 UTC (see `outputs/probe-run.log`,
`outputs/cadence-run1.log`). postfiatl1v2 has no public network; its side is
specified, not measured. Anything marked UNVERIFIED is spec-only or missing
and is never inferred.

Boundary note: the reordered-validation vote-replay work is out of scope for
this pack and is not analyzed here.

## 0. The two systems at a glance

| | postfiatd (live testnet) | postfiatl1v2 (Consensus v2 design) |
| --- | --- | --- |
| Kind | XRPL-derived ledger daemon | Rust workspace: prepare/precommit BFT + Cobalt registry governance |
| Network | PFTL testnet, network_id 2025, 21 peers, state `full` | One controlled devnet only: `postfiat-wan-devnet-2`, 6 Foundation validators, no public RPC, no public testnet |
| Validators | 66 known, 25 UNL, all 1.0.9 on the UNL | 6 on the devnet; 12 is a reviewed testnet launch *minimum*, not a mainnet size |
| Commit rule | Trusted validations on one ledger hash reach the validation quorum | Prepare QC then precommit QC, each q distinct votes |
| Keys | secp256k1, manifests, publisher validator list (VL v2) | ML-DSA-65, bridged by dual-signed identity receipts |
| Genesis | Single-account fresh ledger, 100B PFT in one account | Ratified registry G0 = Selected ∩ Receipted, faucet holds supply minus lanes |
| Upgrades | Validator vote over feature flags (amendments) | Per-kind height-based governance amendments + operator releases |

## 1. Quorum

### 1.1 postfiatd: 67% of the UNL, revert to 80% for mainnet

- `src/xrpld/app/misc/detail/ValidatorList.cpp:1845-1933` —
  `ValidatorList::calculateQuorum(unlSize, effectiveUnlSize, seenSize)`:
  lines 1898-1901 carry the comment: "Use a 67% quorum to balance fork
  safety, liveness, and required UNL overlap. Note: Original XRPL uses 80%,
  but this fork uses 67% for devnet/testnet. For mainnet, this should be
  reverted to 80%." The return (line 1932-1933) is
  `max(ceil(effectiveUnlSize * 0.67), ceil(unlSize * 0.6))` — the 60% term is
  the AbsoluteMinimumQuorum floor from the negative-UNL protocol.
- `src/xrpld/app/misc/ValidatorList.h:492-508` — `quorum()` returns the
  stored quorum value; lines 680-689 — `getQuorumKeys()` returns
  `{quorum_, trustedSigningKeys_}`.
- `src/xrpld/app/consensus/RCLConsensus.cpp:1083-1086` —
  `RCLConsensus::Adaptor::getQuorumKeys()` delegates to the validator list.
- `src/xrpld/consensus/Consensus.h:1252` — consensus reads
  `[quorum, trustedKeys] = adaptor_.getQuorumKeys()` when deciding whether
  to pause for laggards; lines 1284-1291 — phase thresholds progress from
  the minimum quorum (67%) to 100% across 5 pause phases.
- `src/xrpld/consensus/ConsensusParms.h:79` — `minCONSENSUS_PCT = 67`.
- Live measurement: UNL 25 → ceil(25×0.67) = 17, ceil(25×0.60) = 15,
  reported `validation_quorum` = 17
  (`outputs/derived/validators.json`, `quorum_check.matches_67pct_formula:
  true`).

### 1.2 postfiatl1v2: q = floor(2n/3) + 1, f = floor((n-1)/3)

- `crates/ordering_fast/src/lib.rs:338-344` — `bft_fault_tolerance` returns
  `(validator_count - 1) / 3`; lines 345-356 — `bft_quorum_threshold`
  returns `(2 * validator_count / 3) + 1`. The test at lines 2286-2300
  (`computes_supermajority_quorum_thresholds`) verifies both formulas for
  n = 1..=64.
- `docs/architecture/finality.md:5-6` — "For `n` active validators,
  `f = floor((n - 1) / 3)` and `q = floor(2n / 3) + 1`."
- `docs/status/network-status.md:26` — live devnet: "Quorum | 5 of 6
  (`q = floor(2n/3) + 1`; tolerates `f = 1` faulty validator)".
- Whitepaper cross-check at n = 35: q = 24
  (`docs/whitepaper.md:215`).

### 1.3 A third quorum: genesis ratification q_S = ceil(4n_S/5)

- `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:148-149` —
  template trust graph: `q_S = ceil(4 * n_S / 5)`,
  `t_S = min(ceil(n_S / 5), floor((q_S - 1) / 2), 2*q_S - n_S - 1)`.
  At the launch minimum n_S = 12: q_S = 10, t_S = 3 (lines 166-167).
- `docs/architecture/launch-topology-thresholds.md:18-24` — same arithmetic;
  the document states it "decides nothing" (lines 11-13): every number is a
  proposal awaiting the operator's confirmation.

### 1.4 Divergence

| n | postfiatd max(ceil(.67n), ceil(.60n)) | l1v2 floor(2n/3)+1 | l1v2 genesis q_S = ceil(4n/5) |
| --- | --- | --- | --- |
| 6 (devnet) | 5 | 5 | 5 |
| 12 (launch min) | 9 | 9 | 10 |
| 25 (live UNL) | 17 | 17 | 20 |
| 103 (first split) | 70 | 69 | 83 |

- At n = 25 the two consensus formulas agree (17) by arithmetic coincidence;
  they are different functions and first diverge at n = 103 (verified by
  computation over n = 1..200 in `scripts/differential_probes.py`, D02).
- The launch ratification quorum (4/5) is a third, stricter rule that applies
  to genesis and registry evolution, not to block consensus.
- The postfiatd mainnet rule (80%, per the code comment) matches neither
  l1v2 rule at any n: at n = 25, 80% needs 20 validations.
- **Verdict: DIVERGENT.** Three quorum rules (67% testnet / 80% mainnet fork /
  floor(2n/3)+1 Consensus v2) plus a fourth (4/5 genesis ratification) govern
  different phases. No single value satisfies all four. See D01–D03, F01, F04.

## 2. Validation and ledger close

### 2.1 postfiatd: validations, proposals, avalanche, close-time agreement

- Validation lifetimes — `src/xrpld/consensus/ConsensusParms.h:51`
  `validationVALID_WALL = 5 min`; line 59 `validationVALID_LOCAL = 3 min`;
  line 66 `validationVALID_EARLY = 3 min` pre-close.
- Proposals — line 69 `proposeFRESHNESS = 20 s`; line 72
  `proposeINTERVAL = 12 s`.
- Consensus thresholds — line 79 `minCONSENSUS_PCT = 67`; line 160
  `avCT_CONSENSUS_PCT = 75` (percentage of nodes required to agree on ledger
  close time).
- Timing bounds — line 82-83 `ledgerIDLE_INTERVAL = 15 s`; lines 86-87
  `ledgerMIN_CONSENSUS = 1950 ms`; lines 95-96 `ledgerMAX_CONSENSUS = 15 s`;
  line 99 `ledgerMIN_CLOSE = 2 s`; line 126 `avMIN_CONSENSUS_TIME = 5 s`.
- Avalanche cutoffs — lines 146-156: init 50%, mid 65% (after 50% of prior
  round time), late 70% (after 85%), stuck 95% (after 2x).
- Consensus phases — `src/xrpld/consensus/Consensus.h:496` `phaseOpen`,
  line 507 `phaseEstablish`, line 543 `haveConsensus`; lines 1169 and 1367
  are the implementations.
- Close-time resolution — `src/xrpld/consensus/LedgerTiming.h:35-41`
  possible resolutions {10, 20, 30, 60, 90, 120} s; line 44 default 30 s;
  line 47 genesis 10 s; line 50 resolution increases every 8 ledgers.
- Live measurement: mean close interval 3.046 s over 197 ledgers (21 samples
  × 30 s); last close converge time 2001 ms with 24 proposers; ledger
  close_time_resolution 10 s (`outputs/derived/cadence.json`,
  `outputs/derived/live-testnet-snapshot.json`). 3.046 s is inside the
  postfiatd bounds (2 s min close, 15 s idle/max consensus).

### 2.2 postfiatl1v2: prepare / precommit / timeout, on-demand blocks

- `docs/architecture/finality.md:3-6` — two versioned finality modes: a
  genesis omitting `consensus_v2_activation_height` keeps the legacy
  single-view direct-certificate rule; a committed activation height uses
  the legacy rule below the boundary and Consensus v2 at and above it.
  "Consensus v2 is an explicit prepare/precommit protocol; it is not chained
  HotStuff."
- `docs/architecture/finality.md:7-22` — per height: deterministic proposer
  for (height, view); validators verify deterministic execution, persist
  their highest prepare round, sign a prepare vote; q prepare votes form a
  prepare QC (the durable lock); validators persist the lock/high-QC and
  precommit round, then sign; q precommit votes for the same non-nil block
  form the only commit QC. "A lone prepare QC and the legacy direct
  certificate have no commit authority after activation."
- `docs/architecture/consensus-signing-rounds.md:5-9` — one durable round
  floor: a signature at round r requires r >= max(r_P, r_C, r_T), the
  prepare/precommit/timeout high-water marks. Implementation:
  `require_consensus_v2_monotone_round` in
  `crates/ordering_fast/src/consensus_v2.rs`.
- View change — `docs/architecture/finality.md:44-50`: after activation, view
  V+1 requires a signed timeout certificate for the same height at view V; a
  later-view proposal must carry that timeout ID and, if locked, repropose
  the certified block.
- Blocks on demand — `docs/status/network-status.md:55-56`: "The chain makes
  blocks only when there are transactions to order, so height does not
  advance with wall-clock time. A height that has not moved for days is
  normal on this devnet." Devnet height 1513 at the 2026-11-19 observation
  (lines 48-49).
- No XRPL-style validation message exists: votes are prepare/precommit/
  timeout votes bound to height, view, parent, payload and state root
  (`docs/architecture/finality.md:10-14`). No close-time agreement round,
  no dispute phase, no fixed block interval, slot time, or view-timeout
  duration is specified anywhere in the surveyed docs or code.

### 2.3 Divergence

- One validation message per validator per ledger (postfiatd) vs two QC
  phases with durable locks and timeout-certificate view changes (l1v2). A
  ledger validated under one rule is not validated under the other. See D12.
- postfiatd validations expire after minutes (5 min wall, 3 min local);
  l1v2 votes persist under the durable round floor until superseded by a
  higher round. Replay/retention across the boundary is undefined. See D11.
- postfiatd measures a ~3 s close cadence; l1v2 specifies no cadence and its
  only network makes blocks on demand. There is no agreed liveness metric
  for a converged network. See D04–D06, F06.
- Close-time agreement (75% of nodes, postfiatd) has no l1v2 counterpart:
  the only l1v2 "close time" is the fork-ledger close time used as the sole
  time reference for pre-genesis identity-receipt expiry
  (`docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:139`).
- **Verdict: DIVERGENT** on the commit rule and vote lifetimes;
  **UNVERIFIED** on cadence, close-time resolution, and converge-time bounds
  (no l1v2 values exist to compare against).

## 3. Amendment activation

### 3.1 postfiatd: validator vote, 67% for two weeks (3 days on testnet)

- Threshold — `include/xrpl/protocol/SystemParameters.h:83`
  `preFixAmendmentMajorityCalcThreshold = ratio<204, 256>` (79.6875%);
  line 85 `postFixAmendmentMajorityCalcThreshold = ratio<67, 100>` (67%);
  line 88 `defaultAmendmentMajorityTime = 2 weeks`.
- Computation — `src/xrpld/app/misc/detail/AmendmentTable.cpp:326-342`
  `AmendmentSet::computeThreshold`; lines 368-372 `passes()`: strictly
  greater than the threshold after the fix (except single-validator case).
- Activation — lines 886-918: an amendment activates when it holds a
  majority and `majorityTime + majorityTime_ <= closeTime`, i.e. after the
  majority has held for the full majority time.
- Wiring — `src/xrpld/app/main/Application.cpp:1286-1292` builds the table
  with `config().AMENDMENT_MAJORITY_TIME`; `src/xrpld/core/Config.h:248`
  defaults it to `defaultAmendmentMajorityTime`.
- Testnet override — `cfg/postfiatd-testnet-full.cfg:1467-1468`
  `[amendment_majority_time] 3 days`; the mainnet config
  (`cfg/postfiatd-mainnet-full.cfg:1459-1460`, network_id 2026) carries no
  override, so mainnet amendments would take 2 weeks.
- Feature registry — `include/xrpl/protocol/detail/features.macro:45-46`
  `PF_AccountExclusion` and `PF_ValidatorVoteTracking` (both Supported::yes,
  DefaultNo); line 104 `AmendmentMajorityCalc` fix (DefaultYes).
- Live measurement: 101 known amendments, 64 enabled, 0 PF amendments
  enabled; `fixAmendmentMajorityCalc` enabled, so the 67% threshold is
  active; all 64 enabled amendments share one enablement point, ledger
  86785, 2026-02-09T14:31:12Z (`outputs/derived/amendments.json`).

### 3.2 postfiatl1v2: GovernanceAmendment object, per-kind height-based activation

- `crates/types/src/shielded_bridge_governance.rs:2011-2034` —
  `GovernanceAmendment` fields: `amendment_id`, `chain_id`, `genesis_hash`,
  `protocol_version`, `validators`, `quorum`, `kind`, `value`,
  `activation_height`, `veto_until_height`, `paused`, `support`, `votes`,
  `signed_authorizations`. Activation/supersession/rollback records exist
  (lines 2119, 2137, 2153).
- Kinds — `crates/consensus_cobalt/src/internal_validation.rs:1698`
  `validate_amendment_kind`; kinds include external-lane kinds, storage
  commitments, FastPay recovery, FastSwap bootstrap, Asset-Orchard egress
  policy, vault-bridge routes, and activation-height kinds for feature gates
  (`rejected_tx_fee_activation_height`, `require_memo_activation_height`,
  `recipient_format_activation_height` and `*_v2_*` successors).
- Activation semantics are per-kind and height-based: for fee and
  require-memo gates the latest committed amendment wins; for
  recipient-format the earliest unpaused height wins
  (`crates/types/src/shielded_bridge_governance.rs:51-61`).
- Registry transitions — `docs/governance/validator-registry.md:18-24`:
  proposed as governance state, bound to chain/registry/epoch/operation/
  proposal slot/activation height/expiry/payload, authorized by the required
  distinct keys from the old registry, ordered by consensus, activated at a
  valid height, replayable from ordered lifecycle records.
- Lane amendments (most precisely specified) —
  `docs/architecture/genesis-external-lanes.md:165-180`: two kinds,
  `external_lane_release_cap_v1:<lane_id>` and
  `external_lane_committee_epoch_v1:<lane_id>:<binding>`; authorized by the
  registry threshold floor(2n/3)+1 (5 of 6 on the devnet); the amendment's
  `activation_height` must equal the proposal slot it is signed for; a cap
  below the one in force applies from that height; a cap raise applies seven
  windows later (`EXTERNAL_LANE_RELEASE_CAP_RAISE_DELAY_WINDOWS`); a
  committee move holds from the block after it commits.
- Consensus v2 activation itself is a genesis-committed height
  (`docs/architecture/finality.md:3-6`).
- No veto procedure is specified beyond the `veto_until_height` field.
- No single global majority threshold and no time-based supermajority rule
  (e.g. 80% over two weeks) exists anywhere in the spec or code.

### 3.3 Divergence

- Uniform validator vote at 67% held for 2 weeks (3 days on testnet) vs
  per-amendment quorum/support with per-kind height-based activation. The
  postfiatd rule is one number for all amendments; the l1v2 rule is one
  quorum per amendment, carried in the amendment itself. See D07–D08.
- The two PF-native amendments (`PF_ValidatorVoteTracking`,
  `PF_AccountExclusion`) exist in postfiatd code but are not enabled on the
  live network and have no l1v2 counterpart of any kind.
- **Verdict: DIVERGENT.** Every live postfiatd amendment needs an explicit
  l1v2 disposition (re-implement as a governance kind, drop, or replace)
  before convergence. See F02.

## 4. Genesis construction

### 4.1 postfiatd: single-account fresh ledger

- `src/xrpld/app/ledger/Ledger.cpp:169-256` —
  `Ledger::Ledger(create_genesis_t, ...)`: `info_.seq = 1`,
  `info_.drops = INITIAL_XRP`, `info_.closeTimeResolution =
  ledgerGenesisTimeResolution` (10 s). Lines 183-197: the genesis account is
  `r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA` on networks 2025/2026 (PostFiat
  production networks); other networks derive from "masterpassphrase". The
  whole supply goes into that one account (lines 210-218); amendments, if
  any, are written into the genesis ledger (lines 220-226); fee settings
  follow (lines 228-256).
- `include/xrpl/protocol/SystemParameters.h:44-45` —
  `INITIAL_XRP = 100,000,000,000 * DROPS_PER_XRP`, i.e. 10^17 drops;
  `static_assert(INITIAL_XRP.drops() == 100'000'000'000'000'000)`.
- Live measurement: genesis account holds 96,999,999,999.99988 PFT; other
  accounts hold 2,999,999,966.5516 PFT; 33.4486 PFT burned in fees; the sum
  closes exactly at 100,000,000,000 PFT
  (`outputs/derived/live-testnet-snapshot.json`). The XRPL genesis account
  (`r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59`) and root account
  (`rrrrrrrrrrrrrrrrrrrrBZbvji`) do not exist on this network
  (`actNotFound`).

### 4.2 postfiatl1v2: ratified registry, faucet, external lanes

- `docs/architecture/l1v2-testnet-genesis-and-launch-spec.md:105-107` —
  genesis membership `G0 = Selected ∩ Receipted` from a frozen Dynamic UNL
  round on the fork; "No unselected operator may be inserted or used as a
  backfill."
- Section 3.2 (lines 110-142) — identity bridge: each selected operator
  generates a fresh ML-DSA-65 key and submits an `IdentityReceiptV1`
  binding the fork secp256k1 key to it, with fork-key and ML-DSA
  counter-signatures; the receipt deadline is a finalized fork ledger hash
  and sequence, and "Local clocks are not consulted" (line 139).
- Section 3.3 (lines 143-178) — template trust graph `T0`: one essential
  subset S = G0, `q_S = ceil(4 * n_S / 5)`, `t_S` as in §1.3 above.
- Section 3.4 (lines 179-202) — ratification: each G0 operator independently replays the
  round, recomputes G0, runs the pinned checker, and signs the genesis
  payload hash; the certificate is valid only with >= q_S distinct
  signatures. "Changing the payload or certificate produces a different
  genesis envelope and therefore a fork, not an in-chain governance action."
  (line 202).
- Launch gates L1–L6 (section 5): L2 requires n_S >= 12 valid receipts; L3
  independence (no correlated group reaches q_S or the blocking threshold
  n_S - q_S + 1); L4 two consecutive scheduled weekly transitions; L6 an
  explicit signed launch decision.
- Supply — `docs/architecture/pft-token-on-base.md`: total supply 100
  billion PFT, fixed, decided 2026-10-28; the Base ERC-20 is a slice of it,
  not additional supply; the slice size is open. Whitepaper §1.3 partitions
  authorized supply: s_native + s_shielded + s_external + s_in-flight =
  s_authorized.
- Faucet — `docs/architecture/genesis-external-lanes.md:61`: "At genesis the
  faucet receives the native supply minus the sum of the lanes." No genesis
  accounts or per-account distribution table is specified for mainnet.
- The recorded devnet genesis (`postfiat-wan-devnet-2`, hash `ce22ca8c…`)
  has no external lane; the 2026-11-06 rehearsal released 1 PFT on a local
  six-validator fleet with a stand-in finality verifier.
- Mainnet genesis is explicitly out of scope of the testnet genesis spec
  (section 1): "Out of scope: mainnet, token migration or coexistence
  economics."

### 4.3 Divergence

- A single-account fresh ledger (postfiatd) vs a ratified validator registry
  with an identity bridge (l1v2). The two constructions share nothing
  except the 100B supply figure — and even the split differs: postfiatd
  puts the whole supply in one account; l1v2 partitions it into native /
  shielded / external / in-flight claims with a faucet and reserved lanes.
  See D09–D10.
- The l1v2 mainnet genesis does not exist as a specification: the locked
  genesis spec covers the public testnet only. The ERC-20 slice size is
  undecided, nothing is deployed on Base mainnet, and no 1:1
  testnet-to-mainnet conversion mechanism exists in either codebase.
- **Verdict: DIVERGENT** on construction; **UNVERIFIED** on the l1v2 supply
  reconciliation (no live l1v2 network, open slice size). See F03, F11.

## 5. What is NOT divergent (benign or agreed)

- Total supply: 100 billion PFT in both systems (postfiatd `INITIAL_XRP`;
  l1v2 total supply decided 2026-10-28). The figure agrees; the split and
  the genesis construction do not.
- Quorum arithmetic at n = 25 (17) and n = 6 (5) coincides — but the rules
  differ, so this is agreement of values, not of rules. See D01.
- Fees burn in both systems; no validator reward exists in either
  (l1v2 whitepaper §1.3; postfiatd fee burn measured live at 33.4486 PFT).
- The native currency code: postfiatd source still returns "XRP"
  (`SystemParameters.h` `systemCurrencyCode()`); l1v2 uses PFT throughout.
  Cosmetic only (F13).
