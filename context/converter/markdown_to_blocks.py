#!/usr/bin/env python3
"""
Minimal Markdown to Blocks converter (MVP)
This script demonstrates the skeleton for converting old context notes
into the v2.2.0 block format. It does not implement a full parser yet.
Usage: python3 converter/markdown_to_blocks.py --input path/to/context.md
"""
import argparse
import pathlib
from textwrap import dedent

def parse_markdown(md_text: str):
    # Simple placeholder: split into top-level sections by h2-like markers (##)
    blocks = []
    # Very naive: every line starting with '##' becomes a new block title
    lines = md_text.splitlines()
    current = None
    for line in lines:
        if line.strip().startswith("## "):
            title = line.strip().lstrip("## ")
            current = {
                "id": f"b-{title.lower().replace(' ', '-')}-auto",
                "type": "context",
                "title": title,
                "domain": "misc",
                "summary": title,
                "details": "",
                "sources": [],
                "related_codes": [],
                "created_at": "2026-02-28T00:00:00Z",
                "updated_at": "2026-02-28T00:00:00Z",
                "status": "open",
                "tokens_estimate": 50,
            }
            blocks.append(current)
    return blocks

def main():
    p = argparse.ArgumentParser(description="Convert Markdown to v2.2.0 context blocks (MVP)")
    p.add_argument("--input", required=True, help="Input Markdown file with context notes")
    p.add_argument("--out-dir", default="context/v2.2.0/blocks", help="Output directory for block YAML files")
    args = p.parse_args()
    md = pathlib.Path(args.input).read_text(encoding="utf-8")
    blocks = parse_markdown(md)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, b in enumerate(blocks):
        fname = out_dir / f"{b['id']}.yaml"
        # naive YAML dump
        with open(fname, "w", encoding="utf-8") as f:
            for k, v in b.items():
                if isinstance(v, list):
                    f.write(f"{k}: {v}\n")
                else:
                    f.write(f"{k}: {v}\n")
    # Simple update to index.yaml could be added here in a fuller implementation
    print(f"Wrote {len(blocks)} blocks to {out_dir}")

if __name__ == "__main__":
    main()
