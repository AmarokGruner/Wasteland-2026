#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../../.." >/dev/null 2>&1 && pwd)
BLOCKS_DIR="$ROOT_DIR/context/v2.2.0/blocks"

REQUIRED=(id: title: domain: summary: created_at:)
MISSING=0

for f in "$BLOCKS_DIR"/*.yaml; do
  for key in id: title: domain: summary: created_at:; do
    if ! grep -q "^$key" "$f"; then
      echo "MISSING: $f -> $key";
      MISSING=1
    fi
  done
done

if [ "$MISSING" -eq 0 ]; then
  echo "OK: All blocks contain required keys"
  exit 0
else
  echo "Block validation finished with issues" >&2
  exit 1
fi
