# Feature: Belagerung & Kampfsystem

## Source (FAQ 2.2, seed_einheiten.py)
- Combat triggered when army enters enemy province
- Unit stats from seed: nahkampf_staerke, nahkampf_panzerung, fernkampf_panzerung
- Palisadenwall (festung=1, schlachtfeld: Palisade 100): defense bonus
- Ruine-Festung: sicherheitsbonus=30 + ausbildung=2
- Belagerung: Landweg (crossed swords) or Seeweg (sword+pistol)
- Bunker province: +30% defense multiplier
- Kampf reduces fitness; dead units removed from PopulationCohort

## Data Models
```python
Army: id, owner_id, province_id, units[{einheiten_typ_id, count, training, fitness}],
      status("stationed"/"marching"/"besieging"/"in_combat")

CombatLog: id, attacker_army_id, defender_army_id, province_id,
           rounds[JSON], attacker_losses, defender_losses,
           outcome("attacker_wins"/"defender_wins"/"ongoing"), resolved_at
```

## Core Logic
```
COMBAT TRIGGER:
  army enters foreign province AND diplomacy == "feind"
  → create CombatLog, status = "in_combat"

COMBAT ROUND (per 24h tick while in_combat):
  # Attacker power
  atk_power = sum(unit.count * unit.nahkampf_staerke * (unit.training/100) * (unit.fitness/100))

  # Defender power (province garrison + buildings)
  def_garrison = province.stationed_armies
  def_power = sum(unit.count * unit.nahkampf_staerke * training * fitness)

  # Defense bonuses
  if province.has_palisade: def_power *= 1.2   # festung=1
  if province.is_bunker_province: def_power *= 1.3
  def_power += province.sicherheitsbonus * 0.5  # from buildings

  # Losses (proportional)
  atk_losses = floor(def_power / 10 * random.uniform(0.8, 1.2))
  def_losses = floor(atk_power / 10 * random.uniform(0.8, 1.2))

  # Apply losses
  distribute_losses(attacker_army, atk_losses)
  distribute_losses(defender_armies, def_losses)

  # Fitness drain
  all_combatants.fitness -= 5 per round

OUTCOME:
  if attacker army.total_count <= 0: "defender_wins", attacker retreats
  if defender army.total_count <= 0: "attacker_wins"
    → province.owner = attacker.owner
    → if province.has_bunker: destroy bunker
    → moral of conquered province = 10

SIEGE (Belagerung):
  attacker surrounds province (no supply in/out)
  province.lager stops receiving trade routes
  hunger_timer accelerated (supply cut)
```

## Endpoints
```
POST /army/{id}/move {"target_province_id": int}
GET  /province/{id}/combat/status → active combat + current round
GET  /army/{id}/status → units, fitness, training, location
POST /army/{id}/retreat  # manual retreat, ends combat
GET  /player/{id}/armies → all armies + positions
```

## Validation
- Move requires path connectivity (adjacent provinces)
- Cannot attack Verbündet province
- Retreat possible only if fitness > 0
- Dead units removed from PopulationCohort (tick_age preserved for survivors)
