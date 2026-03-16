#!/usr/bin/env python3
import requests
import json

# Test World Map API
try:
    r = requests.get('http://localhost:8000/api/world/map', timeout=5)
    print(f'World Map Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'  Size: {data.get("size")}')
        print(f'  Grid cells: {len(data.get("cells", []))}')
        print(f'  Province IDs: {len(data.get("province_ids", []))}')
    else:
        print(f'  Error: {r.text[:300]}')
except Exception as e:
    print(f'  Exception: {e}')

# Test Terrains API
try:
    r = requests.get('http://localhost:8000/api/world/terrains', timeout=5)
    print(f'\nTerrains Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'  Terrains count: {len(data)}')
    else:
        print(f'  Error: {r.text[:300]}')
except Exception as e:
    print(f'  Exception: {e}')
