#!/usr/bin/env python3
"""
Move the v2.2.0 blocks from context/v2.2.0/blocks to context/blocks
and lift index.yaml/index.json to the root context as context/index.yaml/json.
This fully removes the intermediate v2.2.0 layer.
Usage: python tools/move_v22_to_root.py
Note: This script performs a real filesystem move. Ensure you have backups.
"""
import os
import shutil
from pathlib import Path
SRC_BASE = Path('context') / 'v2.2.0'
DST_BASE = Path('context')
SRC_BLOCKS = SRC_BASE / 'blocks'
DST_BLOCKS = DST_BASE / 'blocks'
SRC_INDEX = SRC_BASE / 'index.yaml'
SRC_INDEX_JSON = SRC_BASE / 'index.json'
DST_INDEX = DST_BASE / 'index.yaml'
DST_INDEX_JSON = DST_BASE / 'index.json'

def move_block_files():
    if not SRC_BLOCKS.exists():
        print('No blocks to move at', SRC_BLOCKS)
        return []
    DST_BLOCKS.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in SRC_BLOCKS.glob('*.yaml'):
        dst = DST_BLOCKS / p.name
        if dst.exists():
            print('Skip existing block', dst)
            continue
        shutil.move(str(p), str(dst))
        moved.append(dst)
    return moved

def move_indices():
    moved = []
    if SRC_INDEX.exists():
        shutil.move(str(SRC_INDEX), str(DST_INDEX))
        moved.append(DST_INDEX)
    if SRC_INDEX_JSON.exists():
        shutil.move(str(SRC_INDEX_JSON), str(DST_INDEX_JSON))
        moved.append(DST_INDEX_JSON)
    return moved

def cleanup_src_dirs():
    # remove empty directories
    try:
        if SRC_BLOCKS.exists() and not any(SRC_BLOCKS.iterdir()):
            SRC_BLOCKS.rmdir()
    except Exception:
        pass
    try:
        if SRC_BASE.exists() and not any(SRC_BASE.iterdir()):
            SRC_BASE.rmdir()
    except Exception:
        pass

def main():
    moved_blocks = move_block_files()
    moved_indices = move_indices()
    cleanup_src_dirs()
    print('Moved blocks to:', DST_BLOCKS)
    print('Moved index files:', (DST_INDEX, DST_INDEX_JSON))

if __name__ == '__main__':
    main()
