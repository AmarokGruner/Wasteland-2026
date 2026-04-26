# Wastelands Building System v3 - Admin-Configurable City Grid

## Admin-Driven Field Unlocking (15x15 Grid)

**Konzept**: Admin definiert per GUI **exakt welche Felder** pro Stadtausbau-Stufe (1-8) freigeschaltet werden. Spieler kann nur **nächste Stufe** bauen.

## Data Models (SQLite)
```python
ProvinceField: id(0-224), province_id, type("land"/"city"), 
  city_unlock_level(0=land, 1-8=stadtfeld), occupied_building_id=None

CityExpansionConfig: level(1-8), unlocked_fields[list[int]]  # Admin-defined

Province: ..., current_city_level(0-8), next_required_building(template_id)

## Admin GUI Workflow

1. /admin/city-config → 15x15 Canvas Grid
2. Admin clicks fields per level (1=Camp → 8=Metropole)
3. Save → CityExpansionConfig populated
4. Visual: city_unlock_level ≥ current_city_level → "city" (concrete texture)

## Build/Upgrade Rules

BUILD(template_id, field_id):
1. field.city_unlock_level ≤ province.current_city_level OR field.type="land"
2. bautyp=="Land" → ANY land field (0-224, unlock_level=0)
3. bautyp=="Stadt" → ANY city field (unlock_level ≤ current_level)
4. bautyp=="Stadtausbau" → ONLY if template_id == next_required_building:
   - Build → current_city_level +=1
   - Convert ALL fields with city_unlock_level == new_level to "city"
   - prev Stadtausbau auto-demolish (partial refund)

DEMOLISH(field_id):
- Refund 50% mips/resources
- field.type reset to original (land/city)
- field.occupied_building_id = NULL

## FastAPI Endpoints

# PLAYER
GET  /province/{id}/fields → 15x15 grid JSON + buildable options/field
POST /province/{id}/build {"template_id":int, "field_id":int}
POST /province/{id}/demolish/{field_id}
GET  /province/{id}/city-status → {"current_level":3, "next_building":"Dorf"}

# ADMIN (SHA256 token)
GET  /admin/city-config → editable 15x15 grid + current config
POST /admin/city-config → save level→fields mapping

## Field State Visual

JSON Response per Field:
{"id":42, "type":"city", "unlock_level":3, "occupied":"Kartoffelfarm", 
 "texture":"concrete", "buildable":["Stadt","Wohnhaus"]}

## Frontend Canvas (Vanilla JS)

// 15x15 canvas, concrete pattern for city fields
ctx.fillStyle = field.type=="city" ? "concretePattern" : "grassPattern"
ctx.drawImage(field.occupied ? buildingIcon[field.name] : null, x, y)

## Implementation Requirements

COMPLETE code delivery:
- SQLite + seed loader
- Admin canvas editor (HTML Canvas + drag-select fields/level)
- Progressive city unlocks (no skipping levels)
- Auto-demolish prev Stadtausbau
- Partial demolish refunds
- Concrete texture generator (CSS/JS Canvas)
- Config Storage: JSON in CityExpansionConfig table, editable via admin GUI.
