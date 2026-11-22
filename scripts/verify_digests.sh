#!/bin/bash
# verify_digests.sh — verify every file listed in SHA256SUMS.
# Usage: bash scripts/verify_digests.sh
# Exits non-zero if any file is missing or its digest differs.
set -u
PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PACK_ROOT"
if [ ! -f SHA256SUMS ]; then
  echo "SHA256SUMS not found; run bash scripts/make_sha256sums.sh first" >&2
  exit 1
fi
sha256sum -c SHA256SUMS
