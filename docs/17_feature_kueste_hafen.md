# Feature: Küstengebäude, Hafen & Schiffe

## Source (FAQ 2.2, 3.2.10, seed_gebaeude.py nurkueste=1)
- Küstengebäude (nurkueste=1): only buildable in outermost land ring adjacent to ocean
- Province must border ocean tile on world map
- Hafen (H1): enables boats; Großhafen (H2): enables ships
- Ships as unit type: higher transport capacity, sea travel only
- Entsalzungsanlage: requires coast → produces Wasser from seawater

## Data Models
```python
Province: ..., has_ocean_border(bool), coast_field_ids[list[int]]
# coast_field_ids = outer ring fields touching ocean

EinheitenTyp: ..., fortbewegung("Boden"/"See"/"Luft"/"Untersee")
ProvinceBuilding: ..., is_coastal(bool)  # derived from template.nurkueste
```

## Core Logic
```
COASTAL BUILD CHECK:
  if template.nurkueste == 1:
    if not province.has_ocean_border: reject "NO_OCEAN_BORDER"
    if field_id not in province.coast_field_ids: reject "NOT_COASTAL_FIELD"
    → allow build

HAFEN UNLOCK:
  if Hafen built: province.sea_access = "boats"   # H1
  if Großhafen:   province.sea_access = "ships"    # H2
  Trade routes can use See-Einheiten if sea_access active

SEA TRAVEL (trade routes):
  if route uses sea path AND destination reachable by sea:
    use See-Einheit geschwindigkeit
    platzbedarf_see limits unit count per ship

ENTSALZUNGSANLAGE:
  produces Wasser without Grundwasserspiegel dependency
  rate from seed terraineffektivitaet (coast terrain)
  requires has_ocean_border = True
```

## Endpoints
```
GET  /province/{id}/coast → {has_ocean_border, coast_field_ids, sea_access}
GET  /province/{id}/fields/buildable/{field_id}
     → includes coastal restriction check in response
POST /province/{id}/build  # existing endpoint, coastal check added to validation
```

## Validation
- nurkueste=1 buildings: field must be in coast_field_ids
- Sea units: require Hafen/Großhafen in origin province
- Entsalzungsanlage: has_ocean_border required
