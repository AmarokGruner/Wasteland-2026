#!/usr/bin/env python3
"""Migrate old CONTEXT_*.md files into the v2.2.0 Blocks structure.
This is a best-effort MVP: it parses markdown headings and turns them into
context blocks under context/v2.2.0/blocks, updates context/v2.2.0/index.yaml,
and (optionally) deletes the original CONTEXT_*.md files.
Usage:
  python3 tools/migrate_context_to_v2_2.py --apply  # apply changes (delete sources)
  python3 tools/migrate_context_to_v2_2.py --dry-run  # show what would be done
"""
import argparse
import re
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # project root (Wasteland)
CTX_ROOT = ROOT  # look for CONTEXT_*.md in root and subdirs
BLOCKS_DIR = ROOT / 'context' / 'v2.2.0' / 'blocks'
INDEX_FILE = ROOT / 'context' / 'v2.2.0' / 'index.yaml'

REQUIRED_TOP = re.compile(r'^(?:#|##)\s*(.*)')

def slugify(s: str) -> str:
    s = s.lower()
    # best-effort ASCII-normalization to produce safer slugs
    try:
        s = s.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        pass
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def extract_blocks_from_text(txt: str, source_path: str):
    blocks = []
    # split into top-level headings (levels 1 and 2)
    lines = txt.splitlines()
    current_title = None
    current_content = []
    for line in lines:
        m = re.match(r'^(#{1,2})\s+(.*)$', line)
        if m:
            lvl, title = len(m.group(1)), m.group(2).strip()
            if lvl == 2:
                if current_title is not None:
                    blocks.append((current_title, "\n".join(current_content).strip(), source_path))
                current_title = title
                current_content = []
            elif lvl == 1:
                # skip top-level title, start new after finishing previous block
                if current_title is not None:
                    blocks.append((current_title, "\n".join(current_content).strip(), source_path))
                current_title = None
                current_content = []
        else:
            current_content.append(line)
    if current_title is not None:
        blocks.append((current_title, "\n".join(current_content).strip(), source_path))
    return blocks

def migrate_one_md(md_path: Path) -> list:
    text = md_path.read_text(encoding='utf-8')
    blocks = extract_blocks_from_text(text, str(md_path))
    created = []
    for title, content, source in blocks:
        if not title:
            continue
        slug = slugify(title)
        block_id = f"b-{slug}"
        out_path = BLOCKS_DIR / f"{block_id}.yaml"
        if out_path.exists():
            continue
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        content_lines = ("  " + l for l in content.splitlines())
        details_block = "\n".join(content_lines)
        yaml = (
            f'id: "{block_id}"\n'
            f'type: "context"\n'
            f'title: "{title}"\n'
            f'domain: "misc"\n'
            f'summary: "{title}"\n'
            f'details: |\n{details_block}\n'
            f'sources:\n  - "{source}"\n'
            f'related_codes:\n  - "{source}"\n'
            f'created_at: "{now}"\n'
            f'updated_at: "{now}"\n'
            f'status: "open"\n'
            f'tokens_estimate: 60\n'
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml, encoding='utf-8')
        created.append(block_id)
    return created

def append_to_index(block_ids):
    if not block_ids:
        return
    text = INDEX_FILE.read_text(encoding='utf-8') if INDEX_FILE.exists() else ''
    if not text:
        text = 'version: "v2.2.0"\ncreated_at: "2026-02-28T12:00:00Z"\nblocks:\n'
    with open(INDEX_FILE, 'a', encoding='utf-8') as f:
        for bid in block_ids:
            f.write(f"- id: \"{bid}\"\n  path: \"blocks/{bid}.yaml\"\n")
    # Also try to update the JSON index if present
    json_index = ROOT / 'context' / 'v2.2.0' / 'index.json'
    if json_index.exists():
        try:
            import json as _json
            data = json.loads(json_index.read_text(encoding='utf-8'))
            blocks = data.get('blocks', [])
            existing_ids = {b.get('id') for b in blocks}
            for bid in block_ids:
                if bid not in existing_ids:
                    blocks.append({"id": bid, "path": f"blocks/{bid}.yaml"})
            data['blocks'] = blocks
            json_index.write_text(_json.dumps(data, indent=2), encoding='utf-8')
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description='Migrate CONTEXT_*.md into v2.2.0 blocks (MVP)')
    parser.add_argument('--apply', action='store_true', help='Apply changes (write files and delete sources)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run only (no file deletions)')
    args = parser.parse_args()

    # collect CONTEXT_*.md files at root and subdirs
    md_files = [p for p in Path('.').rglob('CONTEXT*.md') if p.is_file()]
    md_files += [p for p in Path('.').rglob('CONTEXT_*.md') if p.is_file()]
    created_total = []
    for mf in md_files:
        created = migrate_one_md(mf)
        created_total.extend(created)

    append_to_index(created_total)
    if created_total:
        print(f"Migrated blocks: {created_total}")
        if args.apply:
            # delete originals after migration
            for mf in md_files:
                try:
                    mf.unlink()
                except Exception:
                    pass
            print("Original CONTEXT_*.md files deleted.")
        else:
            print("Dry-run: Originals not deleted. Run with --apply to remove.")
    else:
        print("No CONTEXT_*.md files found or already migrated.")

if __name__ == '__main__':
    main()
