# PostFiat Cross-Implementation Consensus Compatibility Assessment — Evidence Pack

**Verdict: NOT COMPATIBLE as specified.** 2 CRITICAL + 4 HIGH findings,
8 of 30 claims explicitly unresolved, 6 of 15 differential scenarios
UNVERIFIED. The live testnet itself is healthy — the implementations are
not compatible.

## Headline numbers (measured 2026-11-22, live testnet, network 2025)

| Measurement | Value |
| --- | --- |
| Build / network / state | postfiatd 1.0.9, network_id 2025, `full`, 21 peers |
| Validated ledger | seq 8,275,824 (probe), complete 8,200,054–8,275,824 |
| Ledger cadence | 197 ledgers / 601.3 s, mean close interval 3.046 s |
| Validation quorum | 17 of UNL 25 (67% formula; code says revert to 80% for mainnet) |
| l1v2 quorum for the same n | floor(2×25/3)+1 = 17 (agrees at n=25; diverges at n=103: 70 vs 69) |
| Validators / UNL | 66 validators, 25 UNL (all 1.0.9, all domains verified) |
| Stale UNL member | 1 of 25 at 0.00000 24h agreement (~95,848 ledgers behind) |
| Genesis supply reconciliation | 100B PFT = 96,999,999,999.99988 (genesis) + 2,999,999,966.551556 (other accounts) + 33.448564 burned — closes exactly |
| Amendments | 101 known, 64 enabled (RPC `feature` == VHS vote endpoint, exact name match); all 64 enabled at ledger 86785, 2026-02-09 |
| PostFiat-native amendments | `PF_ValidatorVoteTracking` and `PF_AccountExclusion` NOT enabled |
| Fees | base 10 drops, median 5000, queue 0/2000 |
| l1v2 network | None public. Only devnet `postfiat-wan-devnet-2`: 6 Foundation validators, quorum 5 of 6, height 1513 (2026-11-19) |
| External audit | none recorded for either codebase |
| 1:1 conversion | no mechanism for the live testnet; the only documented path (ERC-20 PFT on Base) is an l1v2 design, nothing on Base mainnet |
| Mainnet date | none published anywhere |

## What this pack is

An assessment of whether the postfiatd implementation (live testnet) and the
postfiatl1v2 design (Consensus v2) are compatible, built from live probes of
the running testnet and pinned primary sources. It performs no cutover or
convergence, touches no mainnet, spends no funds, and signs nothing.

Two systems are kept apart throughout: the **live testnet** (postfiatd, an
XRPL fork, network 2025 — measured) and the **l1v2 design** (postfiatl1v2,
Consensus v2 — specified, not observed live). Conflating them is the most
common error in compatibility claims.

Boundary note: the reordered-validation vote-replay work is out of scope for
this pack and is not analyzed here.

## Contents

- `docs/divergence-map.md` — file-and-line divergence map for quorum,
  validation and ledger close, amendment activation, and genesis
  construction, each divergence traced to exact file and line in both
  codebases.
- `docs/decision-memo.md` — the verdict, what is true, what blocks
  convergence, and what would change the verdict.
- `docs/risk-register.md` — 16 severity-scored convergence risks: 7
  blockers, 3 benign differences, 6 unknowns.
- `docs/claim-index.md` — 30 claims with status: 12 verified, 10
  specified, 8 explicitly unresolved.
- `docs/methodology.md` — how each number was produced, and limitations.
- `docs/citations.md` — every pinned primary source (live endpoints and
  repo commits).
- `docs/evidence-index.md` — every claim traced to an unedited output.
- `docs/index.html` — results page (GitHub Pages: serve `docs/`).
- `findings.json` — 14 findings by severity (2 CRITICAL, 4 HIGH,
  4 MEDIUM, 3 LOW, 1 INFO).
- `run-manifest.json` — probe window, environment, repo pins, verdict.
- `configs/` — shipped mainnet + testnet configs and the config diff
  (mainnet differs from testnet only in network_id, seeds, and the
  amendment-majority override).
- `fixtures/` — pinned source excerpts with verified line numbers, full
  SHA-256 of every cited source file (`source-hashes.json`), and the
  l1v2 specification-derived expectations (`l1v2-expectations.json`).
- `outputs/` — unedited probe outputs (RPC, VHS, explorer, pages,
  cadence, WebSocket probe) and derived numbers (`outputs/derived/`).
- `scripts/` — the probe, cadence, analysis, differential-probe,
  comparison, and digest scripts. `src/ws_probe.py` is the stdlib
  WebSocket client.

## Reproduce

```
bash scripts/run_all.sh          # fresh probes + 21-sample cadence + analysis + differential probes
bash scripts/verify_digests.sh   # SHA256SUMS check (must pass)
bash scripts/clean_reproduce.sh  # fresh-environment run in a temp dir;
                                 # exits 0 only if all comparison checks pass
```

`clean_reproduce.sh` prints its workdir (e.g. `/tmp/pftl-compat-repro.XXXXXXXX`) and copies the fresh probe set into `outputs/fresh-clone-*` with
`outputs/fresh-clone-compare.log`. The
fresh-clone files are intentionally excluded from `SHA256SUMS` (they are
generated after the digest is made) and are verified by the comparison
log instead.

## Requirements

`curl`, `git`, `python3` (standard library only). No credentials, no
accounts, no signing. All endpoints are public.
