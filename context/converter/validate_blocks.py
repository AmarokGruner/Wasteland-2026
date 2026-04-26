#!/usr/bin/env python3
"""Minimal validator for v2.2.0 blocks (MVP).
Checks for presence of required keys in each YAML block.
Note: This is a lightweight heuristic; a full YAML parser would be preferred.
"""
import os
from pathlib import Path

REQUIRED_KEYS = ["id", "type", "title", "domain", "summary", "created_at"]

def check_file(path: Path) -> list[str]:
    issues = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        issues.append(f"ERR: cannot read {path}: {e}")
        return issues
    for key in REQUIRED_KEYS:
        if f"{key}:" not in text:
            issues.append(f"MISSING: {path} -> {key} not found")
    return issues

def main():
    base = Path(__file__).resolve().parents[1]  # context/v2.2.0
    blocks_dir = base / "blocks"
    all_issues = []
    for p in blocks_dir.glob("*.yaml"):
        all_issues.extend(check_file(p))
    if all_issues:
        print("Context Block Validation Issues:")
        for it in all_issues:
            print("-", it)
        raise SystemExit(2)
    else:
        print("OK: All blocks contain required keys.")

if __name__ == "__main__":
    main()
