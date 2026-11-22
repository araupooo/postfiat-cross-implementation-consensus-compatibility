# Methodology

## How each number was produced

- **Live testnet probes.** `scripts/probe_all.sh` re-probes every public
  endpoint and keeps the unedited responses under `outputs/`. Each file's
  full SHA-256 is printed to `outputs/probe-run.log`. No credentials,
  sessions, accounts, or signing are used. The `ledger` method with
  `ledger_index: "validated"` returns only the current index through the
  public proxy, so the script fetches the validated ledger by number (the
  sequence read from `server_info`) to retain the full header
  (`total_coins`, `close_time_resolution`).
- **Cadence.** `scripts/cadence.py` polls `server_info` 21 times at 30 s
  intervals (10 minutes) and records the validated sequence each time;
  the mean close interval is 30 s × intervals / ledgers advanced. The
  shipped run: 197 ledgers in 601.3 s, mean 3.046 s
  (`outputs/cadence-run1.log`). A shorter 21-sample × 3 s run taken earlier
  the same night gave 3.050 s, corroborating the figure.
- **Derived numbers.** `scripts/analyze.py` reads only `outputs/` and
  `fixtures/` and writes `outputs/derived/*.json`, `findings.json`, and
  `run-manifest.json`, printing the full SHA-256 of every input. No number
  is hand-typed into a derived file; the findings' embedded figures are
  formatted from the derived values in the same run.
- **Differential probes.** `scripts/differential_probes.py` reads the
  derived files and `fixtures/l1v2-expectations.json` and computes each
  scenario from those values (quorum arithmetic is recomputed, never
  hand-typed). Statuses: PASS (agrees), DIVERGENT (disagrees or different
  rules), UNVERIFIED (spec-only or missing in l1v2 — never inferred).
- **Source pinning.** Both repositories were cloned locally; every cited
  line number was verified with `grep -n` against the pinned revisions
  (postfiatd `0085a1ff…`, postfiatl1v2 `071b6dc4…`). Pinned excerpts are in
  `fixtures/source-excerpts/`; full SHA-256 of every cited source file is
  in `fixtures/source-hashes.json`. Fetched web pages were never used for
  line numbers.
- **Counts.** Every count in this pack is recomputed from the list it
  summarizes: findings by severity/status from `findings.json`, claims by
  status from the `docs/claim-index.md` table (30 claims: 12 VERIFIED,
  10 SPECIFIED, 8 UNVERIFIED), risks by category/severity from the
  `docs/risk-register.md` table (16 risks: 7 blockers, 3 benign, 6 unknowns),
  scenarios by status/area from `outputs/derived/differential-probes.json`
  (15 scenarios: 1 PASS, 8 DIVERGENT, 6 UNVERIFIED). The counts were
  verified with a script against the tables before the pack was finalized.

## Limitations

- **postfiatl1v2 has no public network.** Its side is specified (docs and
  code at the pinned revision), not observed. The only running l1v2 network
  is the controlled devnet `postfiat-wan-devnet-2` (6 Foundation validators,
  no public RPC). Every l1v2 behavior that cannot be observed is marked
  UNVERIFIED.
- **The public RPC proxy blocks admin methods.** `validators` and `peers`
  return HTTP 403 (`Forbidden`); peer count and quorum come from
  `server_info` only. The VHS `/v1/network/amendments` endpoint returns a
  service index, not amendment data; the vote data comes from
  `/v1/network/amendments/vote/test`.
- **The VHS `?unl=true` parameter is ignored.** `vhs_validators_unl.json`
  is byte-identical to `vhs_validators.json`; the UNL is filtered from the
  full list by the `unl` flag in the analysis.
- **Explorer health is failing.** `/api/v1/health` returns HTTP 500
  `{"message":"rippled unreachable"}` while `/api/v1/metrics` works.
- **docs.postfiat.org returns a Notion JavaScript shell** with no
  retrievable content (`outputs/docs_postfiat_org.html`); nothing about
  quorum, validation, amendment, or genesis is claimed from it.
- **The whitepaper and docs were read as shipped.** The `docs/status/`
  dated logs, `docs/listings/`, `docs/plans/`, `docs/handoffs/` and
  `lane-mainnet/` trees were sampled by grep, not read exhaustively; a
  mainnet-date statement could in principle sit in an unreviewed status
  note, though the authoritative pages (README, STATUS, network-status,
  testnet genesis spec) all state the contrary.
- **The l1v2 pin is a point in time.** `main` advanced after the pin was
  taken (newer commits exist); the pin is the revision this pack assesses,
  not current `main`.
- **No second implementation was run.** The l1v2 code was read, not built
  or executed; no l1v2 node was run and no l1v2 block was observed.
- **Boundary.** The reordered-validation vote-replay work is out of scope
  for this pack and is not analyzed here.

## Privacy

No sensitive data is in this pack. Probe outputs contain no per-user
records: no account IDs, wallet addresses, handles, or display names. The
only account strings are protocol accounts (the PFTL genesis account and
the XRPL genesis/root accounts, which return `actNotFound`) and validator
public keys / domain names from the public validator list — public network
infrastructure identifiers, retained as the measured subject. No keys,
tokens, credentials, or personal data appear anywhere; the pack was scanned
for identifiers before finalizing.
