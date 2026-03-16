# Feature: Küstengebäude, Hafen & Schiffe

## Source (FAQ 2.2, 3.2.10, seed_gebaeude.py nurkueste=1)
- Küstengebäude (nurkueste=1): only buildable in outermost land ring adjacent to ocean
- Province must border ocean tile on world map
- Hafen (H1): enables boats; Großhafen (H2): enables ships
- Ships as unit type: higher transport capacity, sea travel only
- Entsalzungsanlage: requires coast → produces Wasser from seawater

## Implementation Status: ✓ IMPLEMENTED (2026-03-15)

### Changes Made
1. **Model Extension** (`app/models.py`):
   - Added `sea_access` field to Province (None/"boats"/"ships")
   
2. **Coast Endpoint** (`app/api/province.py:32-55`):
   - GET `/province/{id}/coast` returns:
     - `has_ocean_border`: bool (derived from terrain)
     - `sea_access`: current access level
     - `coast_field_count`: number of coastal fields
     - `coast_fields`: list of {x,y} positions (max 20)

3. **Coastal Building Check** (`app/building_logic.py:82-86`):
   - Uses existing `is_coastal_position()` from road_logic.py
   - Validates nurkueste=1 buildings on outer ring only

4. **Hafen Unlock** (`app/building_logic.py:122-129`):
   - On building "Hafen": sets `sea_access = "boats"`
   - On building "Großhafen": sets `sea_access = "ships"`

5. **Entsalzungsanlage Production** (`app/round_logic.py:52-66`):
   - Added `is_building_coastal_only()` check
   - Buildings with `spezial_eigenschaften["kueste_only"]=true` produce only when:
     - Province has ocean border (terrain contains "Ozean" or "Wasser")
   - Water production works without Grundwasserspiegel

## Data Models
```python
Province:
  - sea_access: Column(String)  # None/"boats"/"ships"
  # has_ocean_border derived from terrain field

BuildingType:
  - nur_kueste: int (1 = coastal only)
  - spezial_eigenschaften JSON: {"kueste_only": bool}
```

## Core Logic (Implemented)
```
COASTAL BUILD CHECK (app/building_logic.py:82-86):
  if template.nur_kueste == 1:
    is_coastal = is_coastal_position(db, province_id, x, y)
    if not is_coastal: reject "Dieses Gebäude darf nur auf Küsten-Feldern gebaut werden"

HAFEN UNLOCK (app/building_logic.py:122-129):
  if "Großhafen" in template.name:
    province.sea_access = "ships"
  elif "Hafen" in template.name:
    if province.sea_access != "ships":
      province.sea_access = "boats"

COAST PRODUCTION (app/round_logic.py:57-66):
  if is_building_coastal_only(building):
    terrain = province.terrain or ""
    if "Ozean" not in terrain and "Wasser" not in terrain:
      skip production (no ocean border)
```

## Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/province/{id}/coast` | GET | Coast info + sea_access |
| `/province/{id}/build` | POST | Builds (coastal check integrated) |

## Validation Errors
| Error | Cause |
|-------|-------|
| "Dieses Gebäude darf nur auf Küsten-Feldern gebaut werden" | nur_kueste=1 but not coastal position |
| KONTOR_REQUIRED | Kontor building required (see feature 16) |

## Notes
- Sea travel / See-Einheiten still requires additional implementation in trade_route_logic.py
- The `has_ocean_border` is derived from province.terrain field (simplified)
- Full world_map integration would require checking neighboring cells
