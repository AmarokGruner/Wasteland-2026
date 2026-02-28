#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd)
SRC="context/v2.2.0"
DST="context"
SRC_BLOCKS="$SRC/blocks"
DST_BLOCKS="$DST/blocks"
SRC_INDEX="$SRC/index.yaml"
SRC_INDEX_JSON="$SRC/index.json"
DST_INDEX="$DST/index.yaml"
DST_INDEX_JSON="$DST/index.json"

echo "Moving blocks from $SRC/blocks to $DST/blocks..."
mkdir -p "$DST_BLOCKS"
if [ -d "$SRC_BLOCKS" ]; then
  mv -f "$SRC_BLOCKS"/* "$DST_BLOCKS/" 2>/dev/null || true
fi
if [ -f "$SRC_INDEX" ]; then
  mv "$SRC_INDEX" "$DST_INDEX"
fi
if [ -f "$SRC_INDEX_JSON" ]; then
  mv "$SRC_INDEX_JSON" "$DST_INDEX_JSON"
fi
if [ -d "$SRC" ] && [ -z "$(ls -A "$SRC")" ]; then
  rmdir "$SRC"
fi
echo "Move complete. Root now at $DST and $SRC removed if empty."
