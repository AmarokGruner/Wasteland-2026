#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/.." >/dev/null 2>&1 && pwd)
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-bundle>" >&2
  exit 1
fi
git fetch "$1" -f master || true
git fetch "$1" -f --all
echo "Imported bundle from $1"
