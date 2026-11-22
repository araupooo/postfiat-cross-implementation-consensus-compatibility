#!/usr/bin/env python3
"""ws_probe.py — minimal stdlib-only WebSocket client.

Attempts a `subscribe` to the `ledger` stream on a wss endpoint and records
how many ledger closes arrive in the window.

Known environment limitation (recorded, not hidden): on this VM the direct
TLS socket fails for every target — including the XRPL public-testnet control
(`wss://s.altnet.rippletest.net:51233`) — with
`SSLError: WRONG_VERSION_NUMBER`, because outbound traffic goes through the
environment's egress proxy. The curl-based upgrade probe in
`scripts/probe_all.sh` (ws-upgrade-probe.txt) is therefore the authoritative
WebSocket result in this pack: `wss://rpc.testnet.postfiat.org:443` answers
the upgrade with HTTP 401 "Invalid protocol.", and `:6005` gives no response
within 15 s. This script is retained so the attempt itself is reproducible.
"""
import base64
import json
import os
import socket
import ssl
import struct
import sys
import time


def ws_connect(host, port, path="/", timeout=10):
    ctx = ssl.create_default_context()
    raw = socket.create_connection((host, port), timeout=timeout)
    ss = ctx.wrap_socket(raw, server_hostname=host)
    key = base64.b64encode(os.urandom(16)).decode()
    req = ("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
           "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
           "Sec-WebSocket-Version: 13\r\nOrigin: https://localhost\r\n\r\n"
           % (path, host, port, key))
    ss.sendall(req.encode())
    resp = b""
    ss.settimeout(timeout)
    while b"\r\n\r\n" not in resp:
        chunk = ss.recv(4096)
        if not chunk:
            break
        resp += chunk
    return ss, resp.decode(errors="replace")


def ws_send(ss, payload: str):
    data = payload.encode()
    header = bytearray([0x81])
    n = len(data)
    mask = os.urandom(4)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", n)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", n)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    ss.sendall(bytes(header) + masked)


def ws_recv_msgs(ss, seconds):
    ss.settimeout(1.0)
    buf = b""
    msgs = []
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            chunk = ss.recv(65536)
        except socket.timeout:
            continue
        except Exception as e:  # noqa: BLE001
            msgs.append({"error": str(e)})
            break
        if not chunk:
            msgs.append({"error": "connection closed by peer"})
            break
        buf += chunk
        while len(buf) >= 2:
            b1, b2 = buf[0], buf[1]
            opcode = b1 & 0x0F
            ln = b2 & 0x7F
            off = 2
            if ln == 126:
                ln = struct.unpack(">H", buf[2:4])[0]
                off = 4
            elif ln == 127:
                ln = struct.unpack(">Q", buf[2:10])[0]
                off = 10
            if b2 & 0x80:
                off += 4
            if len(buf) < off + ln:
                break
            payload = buf[off:off + ln]
            if opcode == 1:
                msgs.append(json.loads(payload.decode(errors="replace")))
            elif opcode == 8:
                msgs.append({"close": list(payload[:2]) if len(payload) >= 2 else []})
            buf = buf[off + ln:]
    return msgs


def probe(host, port, label, seconds=20):
    out = {"target": "wss://%s:%d" % (host, port), "label": label,
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        ss, resp = ws_connect(host, port)
        out["upgrade_response"] = resp.split("\r\n")[0]
        if "101" not in resp.split("\r\n")[0]:
            out["result"] = "upgrade rejected"
            out["full_response_head"] = resp[:500]
            ss.close()
        else:
            ws_send(ss, json.dumps({"id": 1, "command": "subscribe",
                                    "streams": ["ledger"]}))
            msgs = ws_recv_msgs(ss, seconds)
            out["messages_received"] = len(msgs)
            out["ledger_closes"] = sum(
                1 for m in msgs
                if isinstance(m, dict) and m.get("type") == "ledgerClosed")
            out["messages"] = msgs[:3]
            out["result"] = ("subscribed" if out["ledger_closes"]
                             else "no ledger closes in window")
            ss.close()
    except Exception as e:  # noqa: BLE001
        out["result"] = "error"
        out["error"] = repr(e)
    print(json.dumps(out, indent=1))
    with open("ws-%s.json" % label, "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    probe("rpc.testnet.postfiat.org", 443, "ledger-443", seconds)
    probe("rpc.testnet.postfiat.org", 6005, "ledger-6005", seconds)
    probe("s.altnet.rippletest.net", 51233, "control-xrpl", seconds)
