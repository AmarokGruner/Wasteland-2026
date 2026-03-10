# Feature: Weltgenerierung & Admin-Tools

## Source (FAQ 2.1, 3.2.1, admin.html)
- World map: grid of provinces, each with terrain type
- Admin places starting provinces (with Bunker slots) and Ruinen-Provinzen
- Account reset: once per 24h, restores player to start state
- Admin can force-build, force-transfer, set tech/mips, trigger events

## Data Models
```python
WorldMap: id, name, width(int), height(int), created_at
WorldProvince: id, world_id, x, y, terrain_id, owner_id=None,
               is_ruin_province(bool), preset_buildings[JSON],
               has_ocean_border(bool), kultureinfluss{player_id: value}

AdminLog: id, admin_id, action, target_type, target_id, payload(JSON), timestamp
```

## World Generation Logic
```
GENERATE WORLD (admin trigger):
  create WorldMap(width, height)
  for each cell (x,y):
    terrain_id = noise_function(x,y) OR admin_assignment
    has_ocean = (x==0 OR x==width-1 OR y==0 OR y==height-1)  # border = ocean
    create WorldProvince(terrain, has_ocean)

PLACE RUINS (admin):
  select province → set is_ruin_province=True
  assign preset_buildings from seed (baubar=0 Vorgabe types)

OCEAN BORDER DETECTION:
  province.has_ocean_border = any adjacent province is ocean tile
  province.coast_field_ids = outer ring fields facing ocean direction
```

## Admin Tool Endpoints
```
# World Management
POST /admin/world/generate {"width":int, "height":int, "seed":int}
POST /admin/world/province/{id}/terrain {"terrain_id": int}
POST /admin/world/province/{id}/ruins {"building_ids": [int]}
POST /admin/world/province/{id}/assign-owner {"player_id": int}

# Player Management
POST /admin/player/{id}/reset  # account reset (once per 24h enforced)
POST /admin/player/{id}/tech {"tech_level": int}
POST /admin/player/{id}/mips {"amount": float, "province_id": int}

# Province Override
POST /admin/province/{id}/build {"template_id":int, "field_id":int}  # bypass checks
POST /admin/province/{id}/event {"type":str, "payload":{}}

# Logs
GET  /admin/log?action=&player=&limit=100
```

## Validation
- All admin endpoints require role=="admin" (SHA256 token check)
- Account reset: timestamp check (max once per 24h per player)
- World generate: width/height min 10, max 200
- All admin actions logged to AdminLog
