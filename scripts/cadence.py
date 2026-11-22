#!/usr/bin/env python3
"""cadence.py — poll server_info every 30 s and record validated-ledger progress.

Usage: python3 scripts/cadence.py [--samples N] [--interval S] [--out-prefix NAME]
Defaults: 21 samples, 30 s interval (10 minutes, ~200 ledgers at ~3 s/close).
Writes <prefix>.jsonl (one JSON object per sample) and <prefix>.log (same rows
plus a summary line) into outputs/.

The reproduce run uses --samples 5 to keep the fresh-environment check short;
the shipped cadence is the 21-sample run.
"""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone

RPC = "https://rpc.testnet.postfiat.org/"


def poll_once():
    p = subprocess.run(
        ["curl", "-s", "-m", "30", "-X", "POST", RPC,
         "-H", "Content-Type: application/json",
         "-d", '{"method":"server_info","params":[{}]}'],
        capture_output=True, text=True)
    return p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=21)
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--out-prefix", default="outputs/cadence-run1")
    args = ap.parse_args()

    rows = []
    t0 = time.time()
    log_lines = []
    for i in range(args.samples):
        t = datetime.now(timezone.utc).isoformat()
        raw = poll_once()
        try:
            info = json.loads(raw)["result"]["info"]
            vl = info["validated_ledger"]
            lc = info.get("last_close") or {}
            rows.append({
                "sample": i + 1, "utc": t, "seq": vl["seq"], "hash": vl["hash"],
                "converge_time_s": lc.get("converge_time_s"),
                "peers": info.get("peers"), "state": info.get("server_state"),
                "uptime": info.get("uptime"),
            })
        except Exception as e:  # noqa: BLE001 - record the failure, keep going
            rows.append({"sample": i + 1, "utc": t, "error": str(e),
                         "raw": raw[:200]})
        line = json.dumps(rows[-1])
        print(line, flush=True)
        log_lines.append(line)
        if i < args.samples - 1:
            time.sleep(max(0, args.interval - (time.time() - t0 - i * args.interval)))

    with open(args.out_prefix + ".jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    seqs = [r["seq"] for r in rows if "seq" in r]
    if len(seqs) >= 2:
        summary = ("CADENCE SUMMARY samples=%d seq_first=%d seq_last=%d "
                   "ledgers=%d elapsed=%.1fs mean_close_interval=%.3fs" % (
                       len(rows), seqs[0], seqs[-1], seqs[-1] - seqs[0],
                       time.time() - t0,
                       (len(seqs) - 1) * args.interval / (seqs[-1] - seqs[0])))
    else:
        summary = "CADENCE SUMMARY samples=%d no usable sequence data" % len(rows)
    print(summary, flush=True)
    log_lines.append(summary)
    with open(args.out_prefix + ".log", "w") as f:
        f.write("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()
