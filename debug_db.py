#!/usr/bin/env python3
"""Debug database queries"""
from app.models import SessionLocal, Province, MapCell, TerrainType

db = SessionLocal()

print("Testing Province query...")
try:
    provinces = db.query(Province).limit(1).all()
    print(f"  [OK] Found {len(provinces)} provinces")
    if provinces:
        p = provinces[0]
        print(f"    Province: id={p.id}, name={p.name}, player_id={p.player_id}")
except Exception as e:
    print(f"  [ERROR] Error: {e}")

print("\nTesting MapCell query...")
try:
    cells = db.query(MapCell).limit(5).all()
    print(f"  ✓ Found {len(cells)} cells")
    for c in cells:
        print(f"    Cell: x={c.x}, y={c.y}, terrain_id={c.terrain_id}")
except Exception as e:
    print(f"  [ERROR] Error: {e}")

print("\nTesting TerrainType query...")
try:
    terrains = db.query(TerrainType).limit(5).all()
    print(f"  ✓ Found {len(terrains)} terrains")
    for t in terrains:
        print(f"    Terrain: id={t.id}, name={t.name}")
except Exception as e:
    print(f"  [ERROR] Error: {e}")

print("\nTesting MapCell with terrain relationship...")
try:
    cell = db.query(MapCell).filter(MapCell.terrain_id.isnot(None)).first()
    if cell:
        print(f"  Cell: x={cell.x}, y={cell.y}")
        print(f"  Terrain: {cell.terrain.name if cell.terrain else 'None'}")
except Exception as e:
    print(f"  [ERROR] Error: {e}")

db.close()
