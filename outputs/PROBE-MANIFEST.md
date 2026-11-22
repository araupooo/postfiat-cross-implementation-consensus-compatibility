# Probe manifest

Probe batch: 2026-11-22T17:28:56Z to 2026-11-22T17:29:29Z (UTC). All probes run live by scripts/probe_all.sh; nothing copied from any earlier pack.
Cadence: 21 samples x 30 s, 17:29-17:40 UTC 2026-11-22 (see cadence-run1.log).
Read-only public endpoints only; no spending, signing, accounts, or credentials.
Redaction: none needed — no per-user records in any output (no account IDs, wallet addresses, handles, or display names).
The only account strings are protocol accounts (PFTL genesis; XRPL genesis/root, both actNotFound) and validator public keys/domains from the public validator list.

## Files

- `account_info_pftl_genesis.json` — POST https://rpc.testnet.postfiat.org/ method account_info r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA. Headline: genesis account balance 96999999999999880 drops. sha256=e4452dfc1420fd4a1ad7a9ded93161369c27826c9dec1afe736d4e066011f212
- `account_info_xrpl_genesis.json` — POST https://rpc.testnet.postfiat.org/ method account_info r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59. Headline: actNotFound — XRPL genesis account does not exist on this network. sha256=ab45d561e07e052b1d42e37159ca3e9ca13d283530a43719191e9d852b0ac459
- `account_info_xrpl_root.json` — POST https://rpc.testnet.postfiat.org/ method account_info rrrrrrrrrrrrrrrrrrrrBZbvji. Headline: actNotFound — XRPL root account does not exist on this network. sha256=62633e0f57099c180a2b380992fd584392801ca240515f1f8febe3ce2e34fd1b
- `cadence-run1.jsonl` — python3 scripts/cadence.py --samples 21 --interval 30. Headline: 21 samples, seq 8275839 -> 8276036, 197 ledgers, mean close 3.046 s. sha256=907dee360fe7edc03ed6b386416f603687fe2556dfb5450ced9e3ae8178c637a
- `cadence-3s-corroboration.log` — python3 scripts/cadence.py --samples 21 --interval 3 (earlier the same night, 17:24-17:25 UTC). Headline: 21 samples, seq 8275726 -> 8275746, 20 ledgers, 61.0 s, mean close 3.050 s — corroborates cadence-run1.log (3.046 s). sha256=5a428c6fa6e396704a623e0274e25846de95fe1b00c12f9374d39b6a4219988f
- `cadence-run1.log` — cadence.py log (same run). Headline: CADENCE SUMMARY line + per-sample rows. sha256=e89d18487d696bd68952dbf966568a4f18dfc86d9218a08f5628a42eab9fff47
- `docs_postfiat_org.html` — GET https://docs.postfiat.org. Headline: Notion JavaScript shell, 23,388 bytes — no retrievable content. sha256=db060138e62e61386c1ad1f67a0eec926b67b7f87f71b6a49973e50b8b1797ab
- `explorer_health.json` — GET https://explorer.testnet.postfiat.org/api/v1/health. Headline: HTTP 500 {"message":"rippled unreachable"}. sha256=de52b25e91c4558119b2a577b3d20a808e2bbca0f33b2caf63f5e81325a6a3ab
- `explorer_metrics.json` — GET https://explorer.testnet.postfiat.org/api/v1/metrics. Headline: base_fee 0.00001, txn_sec 0.09, ledger_interval 3.022. sha256=cafd29dba250425da17962b777c6efc6a2c10a27bb3058b44eeebffeb7991287
- `feature_list.json` — POST https://rpc.testnet.postfiat.org/ method feature. Headline: 101 known amendments, 64 enabled; PF_* none enabled; fixAmendmentMajorityCalc enabled. sha256=70585f308ab55dfdc84093e95a21c3859099dcbf1c5b04f1f00cea3a6785984f
- `fee.json` — POST https://rpc.testnet.postfiat.org/ method fee. Headline: base 10 drops, median 5000, queue 0/2000. sha256=c147c392e41d89b9975176bf51821412b0a2461357385c67521a79daf5de8df4
- `invalid_method.json` — POST https://rpc.testnet.postfiat.org/ method no_such_method. Headline: unknown method error (control probe). sha256=e7b21b8092a7192fb17ab985ff2ebd3de10df4b395311385249fdea2acd17540
- `ledger_closed.json` — POST https://rpc.testnet.postfiat.org/ method ledger_closed. Headline: ledger_index 8275824, matches server_info validated seq. sha256=06388746107364663c383f6bafa608e396dcf1f64b43bad8152c048315401e3c
- `ledger_current.json` — POST https://rpc.testnet.postfiat.org/ method ledger (validated seq by number). Headline: full header: total_coins 99999999966551796 drops, close_time_resolution 10. sha256=944bab33924aeb1eec40e162ce2f04e87bff03bf88cde5363c03eb7aeca46c3a
- `peers.json` — POST https://rpc.testnet.postfiat.org/ method peers. Headline: HTTP 403 Forbidden (11-byte body) — admin method blocked by the public proxy. sha256=91268711f43361e9d094089486492db986d6413020b6763903eb4c3b473216b4
- `postfiat_org.html` — GET https://postfiat.org/. Headline: homepage HTML. sha256=c1decdf1556b8adb5b11dd0f18240ee55d47b3d65d26970d3900e41c57b4c8dc
- `postfiat_whitepaper.html` — GET https://postfiat.org/whitepaper/. Headline: whitepaper HTML (Sept 2026). sha256=33b15b1a28f5ebdad68ccb3eeb719fc0e4738b8fe3e8ce89a5317143e7ba472c
- `probe-run.log` — scripts/probe_all.sh log. Headline: HTTP status + full SHA-256 of every output file. sha256=5dc11f55369118726b176b77c479c6528f1fdddfd7fcdd216070c95a701d5c1d
- `server_info.json` — POST https://rpc.testnet.postfiat.org/ method server_info. Headline: build 1.0.9, network_id 2025, state full, peers 21, validation_quorum 17, validated seq 8275824. sha256=ae4b223e0142cc7b194a85d139ad56a2afb77cfef2ec7d1620721f766ed1eb52
- `server_state.json` — POST https://rpc.testnet.postfiat.org/ method server_state. Headline: last_close converge_time 2001 ms, proposers 24. sha256=08728bdb0085fcc09ab3489c8292f99b7e2fadc0099dad85cbfe199e50b72728
- `unl_testnet_vl.json` — GET https://postfiat.org/testnet_vl.json. Headline: VL v2, blob sequence 30, effective 2026-11-17, expiration 2028-03-31, 25 validators. sha256=5d4f5a18a18fead4105e5dc00cf7e11a71b9be4bc140357d1b4ea12116df59e7
- `validators.json` — POST https://rpc.testnet.postfiat.org/ method validators. Headline: HTTP 403 Forbidden (11-byte body) — admin method blocked by the public proxy. sha256=91268711f43361e9d094089486492db986d6413020b6763903eb4c3b473216b4
- `vhs_amendments.json` — GET https://vhs.testnet.postfiat.org/v1/network/amendments. Headline: service index only, no amendment data. sha256=0f61e791be3d0147af69cbe50f573c2794b01d8b842f7f2985785f462d94a188
- `vhs_amendments_info.json` — GET https://vhs.testnet.postfiat.org/v1/network/amendments/info. Headline: amendment info listing. sha256=6ab7eb9eb0a734db532827cb4cc9049dd090506739ab6f2adbe76824438f6fd9
- `vhs_amendments_vote_test.json` — GET https://vhs.testnet.postfiat.org/v1/network/amendments/vote/test. Headline: 64 enabled amendments with names, ledger 86785, 2026-02-09. sha256=421f09131189d2be03040602d948fb6626d4adff425328479e140ae2a22b3682
- `vhs_health.json` — GET https://vhs.testnet.postfiat.org/v1/health. Headline: {"count":"9"} — a count, not a health status. sha256=6d563996f36ea750126863496012066a256f8230a1499abe735da048dc76662c
- `vhs_networks.json` — GET https://vhs.testnet.postfiat.org/v1/network/networks. Headline: includes 2 webhook.site test entries alongside the real test network. sha256=7818218a1d2bebf1a9c3cf6edbbb6e70666036d54ccdc796b3c7c52899e3c514
- `vhs_topology.json` — GET https://vhs.testnet.postfiat.org/v1/network/topology. Headline: node_count 72, link_count 0 (contradicts per-node inbound/outbound sums 690/701). sha256=44d86e52a1c6cf9edb6f91ba4801ac1e3023fa85fe81047b815553f00fc44f33
- `vhs_topology_nodes.json` — GET https://vhs.testnet.postfiat.org/v1/network/topology/nodes. Headline: 72 nodes. sha256=f0d87551d0dbc843e6ba73cd37f68c1acb7358282b59dda1b65e7582ebca74c5
- `vhs_validators.json` — GET https://vhs.testnet.postfiat.org/v1/network/validators. Headline: 66 validators, 25 UNL. sha256=2b66b88b167859100f7bbdcc835dbd1cf4dc4160f338977541829f431334ce32
- `vhs_validators_unl.json` — GET https://vhs.testnet.postfiat.org/v1/network/validators?unl=true. Headline: byte-identical to vhs_validators.json — the ?unl=true parameter is ignored. sha256=2b66b88b167859100f7bbdcc835dbd1cf4dc4160f338977541829f431334ce32
- `whitepaper.txt` — derived from postfiat_whitepaper.html (tags stripped). Headline: plain text for keyword search; HTML is the source. sha256=656238f6a11bfa179bdb27da68a6e9ad69a8ca9aa1f41c56b8b8d7b35c1b87a7
- `ws_upgrade_probe.txt` — curl WebSocket upgrade probe, wss://rpc.testnet.postfiat.org:443 and :6005. Headline: see file; public monitoring depends on HTTP polling. sha256=68cef8518055aa74f46d5799e3426bc3cda53a53b9f71734d147f127d4d5b4db

## Notes

- `validators.json` and `peers.json` have identical SHA-256: both are the same 11-byte `Forbidden` body.
- `vhs_validators.json` and `vhs_validators_unl.json` have identical SHA-256: the `?unl=true` parameter is ignored by the service.
- `ledger_current.json` was fetched by numeric ledger index (the validated sequence from `server_info.json`); the `ledger` method with `ledger_index: "validated"` returns only the current index through the public proxy.
- `docs_postfiat_org.html` is a Notion JavaScript shell; no quorum/validation/amendment/genesis content is retrievable from it without a JS-capable browser. Nothing is claimed from it.
