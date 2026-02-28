#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/.." >/dev/null 2>&1 && pwd)
OUT="$REPO_ROOT/wasteland-local.bundle"
git bundle create "$OUT" --all
echo "Bundle created at $OUT"
