# Migration Decision Memo: postfiatd → postfiatl1v2 Convergence

## Decision

**Do not converge. The two implementations are NOT COMPATIBLE as specified.**

Convergence as currently specified is not a migration; it is a re-founding.
The two systems share a supply figure (100B PFT) and a name, and little else:
different commit rules, different quorum rules, different amendment
mechanisms, and different genesis constructions. Any convergence must pick
one rule per area, re-prove fork safety under it, and rebuild genesis —
there is no path that carries the live testnet's state, validator set, or
amendment history into the l1v2 design unchanged.

This memo is an assessment only. No cutover or convergence was performed, no
mainnet was touched, no funds were spent, nothing was signed.

## What is true

- The live postfiatd testnet is healthy: postfiatd 1.0.9, network 2025,
  state `full`, 21 peers, validated ledger 8,275,824 at probe time, mean
  close interval 3.046 s over 197 ledgers, fee queue empty, genesis supply
  reconciles exactly at 100B PFT, amendment state agrees across the RPC
  `feature` endpoint and the VHS vote endpoint (64 enabled of 101 known).
  See `findings.json` F14 and `outputs/derived/`.
- The l1v2 design is specified and implemented in code, but it has no public
  network: the only running network is the controlled devnet
  `postfiat-wan-devnet-2` (6 Foundation validators, quorum 5 of 6, height
  1513 at the 2026-11-19 observation). Its behavior is specified, not
  observed.
- The quorum numbers coincide at the sizes that matter today (17 of 25 live;
  5 of 6 on the devnet) but the rules differ, and they diverge at n = 103.
- The 100B supply figure agrees; the split does not (one account vs
  native/shielded/external/in-flight partition with a faucet and lanes).

## What blocks convergence

1. **Commit rule (F01, CRITICAL).** Single-round validation quorum vs
   two-phase prepare/precommit quorum certificates with durable locks and
   timeout-certificate view changes. A ledger validated under one rule is
   not validated under the other. Pick one commit rule and re-derive the
   fork-safety argument (postfiatd cites Theorem 8 of arXiv:1802.07242;
   l1v2 gives a fixed-height safety argument in
   `consensus-signing-rounds.md`).
2. **Amendment mechanism (F02, CRITICAL).** Uniform 67%-for-2-weeks
   validator vote vs per-kind height-based governance amendments with
   per-amendment quorum/support. Every live postfiatd amendment (101 known,
   64 enabled) needs an explicit l1v2 disposition.
3. **Genesis (F03, HIGH).** Single-account fresh ledger vs ratified
   registry with ML-DSA identity bridge. A converged network needs one
   genesis; the postfiatd genesis cannot be replayed into the l1v2
   construction without a new chain ID and a new genesis payload.
4. **Quorum (F04, HIGH).** 67% testnet / 80% mainnet fork / floor(2n/3)+1
   Consensus v2 / 4/5 genesis ratification. Pick one rule per phase.
5. **Audit (F05, HIGH).** No external audit of either codebase; l1v2
   release gates 4 DONE / 16 OPEN / 1 UNKNOWN; gate 8 (migration, rollback,
   canary) OPEN. The founder's multi-million-dollar audit is a statement,
   not a scoped engagement.
6. **Conversion (F11, LOW) and schedule (F12, LOW).** No 1:1
   testnet-to-mainnet mechanism, open ERC-20 slice size, nothing on Base
   mainnet, no mainnet date, l1v2 launch gates L1–L6 unmet.

## What would change the verdict

Each item is independently checkable; the verdict changes only when all of
them close:

1. One commit rule is chosen, specified with its quorum, and its fork-safety
   proof is published and reviewed.
2. One quorum rule per phase is chosen (genesis ratification, block
   consensus, registry evolution) and measured live at the production
   validator-set size.
3. Every live postfiatd amendment has a written l1v2 disposition, and the
   l1v2 governance-amendment kinds needed for the converged network exist
   and are exercised on a public testnet.
4. One genesis construction is chosen and built; the ERC-20 slice size is
   fixed; the Base mainnet token and lock are deployed and verified.
5. An external audit scope covering both consensus implementations and the
   genesis/registry machinery is published, with auditor, scope, and date.
6. A 1:1 conversion or explicit no-carryover decision is published, and a
   mainnet date exists.
7. The l1v2 close/view timing is specified (or explicitly stated to not
   exist) with a liveness metric, and a public l1v2 testnet satisfies launch
   gates L1–L6.

## Recommended sequence (if convergence is ever pursued)

1. Decide the commit rule and quorum rules first — they determine everything
   downstream (validator set, genesis, amendment dispositions).
2. Build the public l1v2 testnet to launch-gate L2 (genesis registry,
   n_S ≥ 12, identity bridge completed by every validator) before any
   mainnet discussion.
3. Exercise the governance-amendment kinds and the lane-amendment rounds on
   that testnet; close the L3 independence verifier (still to be built).
4. Fix the ERC-20 slice, deploy on Base mainnet, and rehearse the lock →
   release path end-to-end with a production finality verifier (the 2026-11-06
   rehearsal used a stand-in verifier that always reverts).
5. Commission the audit; only then set a mainnet date.
6. Publish the conversion/no-carryover decision before any balance is
   promised anything.

## What this pack does not do

- It does not perform a cutover or convergence, touch mainnet, spend funds,
  or sign anything.
- It does not analyze the reordered-validation vote-replay work (out of
  scope; see the boundary note in `docs/divergence-map.md`).
- It does not claim l1v2 behavior that is only specified; every spec-only or
  missing behavior is marked UNVERIFIED in `docs/claim-index.md` (8 of 30
  claims) and in `outputs/derived/differential-probes.json` (6 of 15
  scenarios).

## Key logs (raw, for direct verification)

Repository: `postfiat-cross-implementation-consensus-compatibility`
(expected public repository name; raw URLs resolve once the repository is
created):

- Probe run log (full SHA-256 of every output):
  `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/probe-run.log`
- Cadence log (21 samples × 30 s, 197 ledgers, mean close 3.046 s):
  `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/cadence-run1.log`
- Fresh-clone comparison log (reproduce check):
  `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/fresh-clone-compare.log`
- Differential probes (15 scenarios):
  `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/outputs/derived/differential-probes.json`
- Findings (14, by severity):
  `https://raw.githubusercontent.com/araupooo/postfiat-cross-implementation-consensus-compatibility/main/findings.json`
