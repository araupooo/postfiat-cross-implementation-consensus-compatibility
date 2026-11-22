#!/bin/bash
# probe_all.sh — re-probe every live public endpoint used by this pack and
# retain the unedited responses under outputs/.
#
# Usage: bash scripts/probe_all.sh [OUTPUT_DIR]
#   OUTPUT_DIR defaults to outputs/ relative to the pack root.
# No credentials, sessions, or accounts are used. All endpoints are public.
# Each output file's full SHA-256 is printed to the probe log so a reader can
# verify that the shipped files are the files this script produced.
#
# Boundary note: the reordered-validation vote-replay work is out of scope
# for this pack, so this script performs no fetch related to it.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$PACK_ROOT/outputs}"
mkdir -p "$OUT"
LOG="$OUT/probe-run.log"
: > "$LOG"
log() { echo "$*" | tee -a "$LOG"; }
sha() { sha256sum "$1" | awk '{print $1}'; }

log "probe_all.sh run start: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
log "pack root: $PACK_ROOT"

RPC="https://rpc.testnet.postfiat.org/"
post() { # $1 outfile $2 method-json
  curl -s -m 30 -X POST "$RPC" -H 'Content-Type: application/json' -d "$2" \
    -o "$OUT/$1" -w "%{http_code} %{time_total}s" > "$OUT/$1.http" 2>&1
  log "$1 -> $(cat "$OUT/$1.http") sha256=$(sha "$OUT/$1")"
  rm -f "$OUT/$1.http"
}
get() { # $1 url $2 outfile
  curl -s -m 30 "$1" -o "$OUT/$2" -w "%{http_code} %{time_total}s %{size_download}B" > "$OUT/$2.http" 2>&1
  log "$2 -> $(cat "$OUT/$2.http") sha256=$(sha "$OUT/$2")"
  rm -f "$OUT/$2.http"
}

# --- postfiatd JSON-RPC (public proxy) ---
post server_info.json '{"method":"server_info","params":[{}]}'
# The `ledger` method with ledger_index "validated" returns only the current
# index through this proxy; fetch the validated ledger by number instead so
# the full header (total_coins, close_time_resolution) is retained.
VALIDATED_SEQ="$(python3 -c "import json;print(json.load(open('$OUT/server_info.json'))['result']['info']['validated_ledger']['seq'])")"
log "validated seq for numeric ledger fetch: $VALIDATED_SEQ"
post ledger_current.json "{\"method\":\"ledger\",\"params\":[{\"ledger_index\":$VALIDATED_SEQ,\"transactions\":false,\"expand\":false}]}"
post ledger_closed.json '{"method":"ledger_closed","params":[{}]}'
post fee.json '{"method":"fee","params":[{}]}'
post feature_list.json '{"method":"feature","params":[{}]}'
post server_state.json '{"method":"server_state","params":[{}]}'
# Protocol genesis / root accounts (public ledger accounts, not user records).
post account_info_pftl_genesis.json '{"method":"account_info","params":[{"account":"r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA","ledger_index":"validated"}]}'
post account_info_xrpl_genesis.json '{"method":"account_info","params":[{"account":"r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59","ledger_index":"validated"}]}'
post account_info_xrpl_root.json '{"method":"account_info","params":[{"account":"rrrrrrrrrrrrrrrrrrrrBZbvji","ledger_index":"validated"}]}'
# Admin-gated methods: the public proxy is expected to refuse these; the
# refusal body itself is the evidence and is kept unedited.
post validators.json '{"method":"validators","params":[{}]}'
post peers.json '{"method":"peers","params":[{}]}'
post invalid_method.json '{"method":"no_such_method","params":[{}]}'

# --- Validator History Service ---
get https://vhs.testnet.postfiat.org/v1/network/validators vhs_validators.json
get https://vhs.testnet.postfiat.org/v1/network/validators?unl=true vhs_validators_unl.json
get https://vhs.testnet.postfiat.org/v1/network/topology/nodes vhs_topology_nodes.json
get https://vhs.testnet.postfiat.org/v1/network/topology vhs_topology.json
get https://vhs.testnet.postfiat.org/v1/network/networks vhs_networks.json
get https://vhs.testnet.postfiat.org/v1/health vhs_health.json
get https://vhs.testnet.postfiat.org/v1/network/amendments vhs_amendments.json
get https://vhs.testnet.postfiat.org/v1/network/amendments/info vhs_amendments_info.json
get https://vhs.testnet.postfiat.org/v1/network/amendments/vote/test vhs_amendments_vote_test.json

# --- Explorer ---
get https://explorer.testnet.postfiat.org/api/v1/metrics explorer_metrics.json
get https://explorer.testnet.postfiat.org/api/v1/health explorer_health.json

# --- Published pages ---
get https://postfiat.org/ postfiat_org.html
get https://postfiat.org/whitepaper/ postfiat_whitepaper.html
get https://docs.postfiat.org docs_postfiat_org.html
get https://postfiat.org/testnet_vl.json unl_testnet_vl.json

# --- WebSocket upgrade probe (curl) ---
{
  echo "== wss://rpc.testnet.postfiat.org:443 =="
  timeout 20 curl -s -i -m 15 --http1.1 -H "Connection: Upgrade" -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Version: 13" \
    https://rpc.testnet.postfiat.org/ | head -12 || echo "curl exit $?"
  echo "== wss://rpc.testnet.postfiat.org:6005 =="
  timeout 20 curl -s -i -m 15 --http1.1 -H "Connection: Upgrade" -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" -H "Sec-WebSocket-Version: 13" \
    https://rpc.testnet.postfiat.org:6005/ | head -12 || echo "curl exit $? (no response within timeout)"
} > "$OUT/ws_upgrade_probe.txt" 2>&1
log "ws_upgrade_probe.txt sha256=$(sha "$OUT/ws_upgrade_probe.txt")"

# --- Whitepaper plain text (derived, for keyword search; HTML is the source) ---
python3 - "$OUT/postfiat_whitepaper.html" "$OUT/whitepaper.txt" <<'PYEOF'
import re, html, sys
s = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
s = re.sub(r"<script.*?</script>", "", s, flags=re.S | re.I)
s = re.sub(r"<style.*?</style>", "", s, flags=re.S | re.I)
s = re.sub(r"<[^>]+>", " ", s)
s = html.unescape(s)
s = re.sub(r"\s+", " ", s)
open(sys.argv[2], "w").write(s)
print("whitepaper.txt chars=%d" % len(s))
PYEOF
log "whitepaper.txt sha256=$(sha "$OUT/whitepaper.txt")"
log "probe_all.sh run end: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
