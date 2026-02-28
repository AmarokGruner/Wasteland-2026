#!/usr/bin/env python3
"""Validate v2.2.0 blocks now in root context/blocks.
Check required keys in YAML blocks.
"""
import os
import sys
import yaml
from pathlib import Path

ROOT = Path('context/blocks')
REQUIRED = ["id","type","title","domain","summary","details","sources","created_at","updated_at","status","tokens_estimate"]

def check_file(p):
    with p.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return [f"{p} is not a YAML mapping"]
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        return [f"{p}: missing keys: {', '.join(missing)}"]
    return []

def main():
    issues = []
    for f in ROOT.glob('*.yaml'):
        issues += check_file(f)
    if issues:
        print("BLOCK VALIDATION ISSUES:")
        for i in issues:
            print("- ", i)
        sys.exit(2)
    print("OK: All blocks contain required keys.")

if __name__ == '__main__':
    main()
