#!/usr/bin/env python3
"""
Simple validator for the canonical bundle (v2.2.0).
Checks basic consistency between bundle.json and core/data_contracts.json.
"""
import json
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    base = Path(__file__).parents[2]  # context/v2.2.0/.. -> context
    bundle_path = base / "bundle.json"
    data_contracts_path = base / "core" / "data_contracts.json"

    if not bundle_path.exists():
        print(f"ERROR: bundle.json not found at {bundle_path}")
        return 2
    if not data_contracts_path.exists():
        print(f"ERROR: data_contracts.json not found at {data_contracts_path}")
        return 2

    bundle = load_json(bundle_path)
    contracts = load_json(data_contracts_path)

    endpoints_in_bundle = { (e.get("path"), e.get("method")) for e in bundle.get("endpoints", []) }
    endpoints_in_contracts = set()
    for e in contracts.get("endpoints", []):
        endpoints_in_contracts.add((e.get("path"), e.get("method")))

    missing = endpoints_in_bundle - endpoints_in_contracts
    extra = endpoints_in_contracts - endpoints_in_bundle

    ok = True
    if missing:
        ok = False
        print("WARN: Endpoints in bundle.json not found in contracts:")
        for p, m in sorted(missing):
            print(f"  - {m} {p}")
    if extra:
        ok = False
        print("WARN: Endpoints in contracts not represented in bundle.json:")
        for p, m in sorted(extra):
            print(f"  - {m} {p}")

    if ok:
        print("OK: bundle.json endpoints are aligned with data_contracts.json")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
