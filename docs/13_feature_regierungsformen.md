# Feature: Regierungsformen

## Status: ✅ IMPLEMENTIERT (v1.0)

### Änderungen:
- `models.py`: Regierungsform-Modell erweitert mit `ausbauwert_regierungssitz`
- `regierungsform_logic.py`: NEU - Alle Berechnungsfunktionen
- `kultur_bildung_logic.py`: Refaktoriert, delegiert an regierungsform_logic
- `tick_logic.py`: Transition und tägliche Effekte integriert (Mitternacht)
- `api/player.py`: Endpoints erweitert

---

## Source (seed_regierungsformen-3.py)
Fields: id, name, formtyp, techlevel, ausbauwert_regierungssitz, kulturverbreitung,
grundmoral, forschungsfortschritt, produktivitaet, wachstum, finanzen, sicherheit,
moralmalus_armee_aussen, entfernungsmalus, lebensmittelbedarf, verbrauchsgutbedarf,
streikbereitschaft, auswanderbereitschaft, milizen, fremdkultur_verlust, aufstand,
krieg_moeglich, provinzanzahl_bis_malus, malus_beschreibung, boni, voraussetzungen

Known forms: Stamm (id=1, start), Anarchie (id=2, transition state, 5 ticks)

## Data Models
```python
Regierungsform: id, name, ...all seed fields...  # from seed
Player: ..., regierungsform_id, regierungsform_transition_ticks_remaining(0=done)
```

## Core Logic (applied in roundlogic per 24h tick)
```
ACTIVE MODIFIERS (multiply base values):
  produktivitaet → mips_available *= reg.produktivitaet
  wachstum       → birth_rate    *= reg.wachstum
  sicherheit     → security_calc *= reg.sicherheit
  finanzen       → tax_income    *= reg.finanzen
  forschungsfortschritt → tech_production *= reg.forschungsfortschritt
  kulturverbreitung → daily_kultur *= reg.kulturverbreitung
  lebensmittelbedarf → food/drink_demand *= reg.lebensmittelbedarf
  verbrauchsgutbedarf → verbrauchsgut_demand *= reg.verbrauchsgutbedarf

MORAL BASE:
  moral_base = reg.grundmoral  # replaces hardcoded 50

PROVINCE COUNT MALUS:
  extra = max(0, len(player.provinces) - reg.provinzanzahl_bis_malus)
  all_provinces.moral -= extra * 16  # from malus_beschreibung "16 Moral weniger"

ARMY OUTSIDE MALUS:
  if player has units outside own provinces:
    all_provinces.moral -= reg.moralmalus_armee_aussen

FREMDKULTUR:
  if reg.fremdkultur_verlust == 1:
    for each foreign_culture_influence in province:
      moral -= foreign_kultur_points * 0.1

AUSWANDERUNG:
  if reg.auswanderbereitschaft > 0 AND moral < 60:
    emigration = population * reg.auswanderbereitschaft * (60-moral)/100

ANARCHIE (transition, 5 ticks):
  forschungsfortschritt = 0 → tech frozen
  produktivitaet = 0.9
  grundmoral = 30
  aufstand = 1 → revolt_threshold raised

CHANGE REGIERUNGSFORM:
  1. set regierungsform_transition_ticks_remaining = 5
  2. apply Anarchie modifiers for 5 ticks
  3. after tick 5: set new regierungsform_id

VORAUSSETZUNGEN CHECK:
  reg.techlevel <= player.tech_level
  reg.ausbauwert_regierungssitz <= province.regierungssitz_level
```

## Endpoints (IMPLEMENTED)
```
GET  /player/{id}/regierungsform                    → current form + all modifiers active
GET  /player/{id}/regierungsformen                   → all available forms + player eligibility  
POST /player/{id}/regierungsform                     → {"form_id": int} - starts transition
GET  /player/{id}/regierungsform/preview?form_id=    → diff of all modifiers vs current form
```

## Validation (IMPLEMENTED)
- Cannot change during Anarchie transition (`regierungsform_transition_ticks_remaining > 0`)
- Requires Regierungssitz building (ausbauwert_regierungssitz check) - via `check_regierungsform_voraussetzungen()`
- krieg_moeglich=0 → muss noch in diplomacy endpoint blockiert werden (nicht implementiert)
