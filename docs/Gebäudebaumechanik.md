# Wastelands Building System - Complete FastAPI/Python Implementation

## Objective
Full building construction/upgrade system from `seed_gebaeude.py`. Handles **bautyp** (Land/Stadt/Stadtausbau), costs (baukostenmips/ausbaukostenmips), prerequisites, unique/terrain restrictions, city expansion.

## Core Data Models (SQLite)
```python
Province: id, player_id, terrain_id, kulturpunkte, size_level(1-7), fields_total, fields_city

Player: id, mips_total, tech_level

BuildingTemplate (from seed_gebaeude.py): 
  id, name, kategorie, bautyp(Land/Stadt/Stadtausbau), baubar, ausbaubar, 
  uniquegebaeude, nurkueste, istfeld, techlevel, baukostenmips, ausbaukostenmips, 
  rohstoffbedarfbau{dict}, spezialeigenschaften{provinzgroesse,kulturpunkte}

BuildingInstance: province_id, template_id, position(field_id), level(1-10), built_at

## Building Rules

PREREQUISITES CHECK (before build/upgrade):
1. player.tech_level ≥ template.techlevel
2. player.mps ≥ baukostenmips (deduct on build)
3. resources ≥ rohstoffbedarfbau (deduct)
4. bautyp=="Land" → position on Land field (istfeld=1)
5. bautyp=="Stadt" → position on City field
6. bautyp=="Stadtausbau" → ONLY ONE per province, upgrades size_level
7. uniquegebaeude=1 → max 1 instance province-wide
8. nurkueste=1 → terrain/coast restriction
9. ausbaubar=1 ∧ level < 10 → upgrade possible

CITY EXPANSION (bautyp=="Stadtausbau"):
- Camp (size=1, kultur=1) → Siedlung (size=2, kultur=2) → Dorf(3) → ... → Metropole(7)
- Each upgrade: fields_city += provinzgroesse_delta, kulturpunkte += delta
- Costs scale: ausbaukostenmips × size_level multiplier

## Core Logic: Build/Upgrade

def can_build(template_id, province_id, position):
  # All prerequisite checks above
  return True/False, error_msg

def build_building(template_id, province_id, position):
  if not can_build(): raise HTTPError
  deduct mips + resources
  insert BuildingInstance
  if bautyp=="Stadtausbau": upgrade_province_size()

def upgrade_building(instance_id):
  instance = get_instance(instance_id)
  template = get_template(instance.template_id)
  if not template.ausbaubar or instance.level >= 10: raise Error
  deduct ausbaukostenmips + upgrade_resources
  instance.level += 1

## FastAPI Endpoints

GET  /province/{province_id}/buildable?position={field_id} 
→ {"can_build": [{template_id, name, costs, missing_prereqs}], "city_status": "Siedlung (size:2/7)"}

POST /province/{province_id}/build 
Body: {"template_id": int, "position": int}
→ {"success": true, "new_instance": {...}}

POST /province/{province_id}/upgrade/{instance_id}
→ {"success": true, "new_level": 3}

GET  /buildings/templates → full seed_gebaeude.py lookup

## Validation & Province Updates

ON BUILD:
- uniquegebaeude → check count==0
- Stadtausbau → auto-remove previous + upgrade size/kultur
- istfeld=1 → convert Land field to building slot

ON UPGRADE:
- level-limited (max 10)
- zusatzarbeiterprostufe, zusatzwohnraumprostufe scale linearly

REJECT REASONS:
- "insufficient_mips", "missing_resources", "tech_too_low", "wrong_field_type", "unique_already_exists"

## Implementation Requirements

Deliver COMPLETE code:
- SQLite init + seed_gebaeude.py loader
- Pydantic models, SQLAlchemy ORM
- core_logic(can_build(), build(), upgrade())
- Full API + auth dependency (SHA256 token)
- Error responses with German messages
- CORS for vanilla JS frontend
