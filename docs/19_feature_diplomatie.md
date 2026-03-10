# Feature: Diplomatie-System

## Source (FAQ 2.6, 2.2)
- Relations per player pair: Verbündet / Freund / Neutral / Unerwünscht / Feind/Krieg
- Default: Neutral for unlisted players
- Freund/Verbündet: access to friends-only Kontor listings
- Feind/Unerwünscht: trade blocked; armies auto-attack on encounter
- Verbündet: armies do NOT auto-attack; border crossing allowed
- krieg_moeglich=0 (Regierungsform) blocks war declaration

## Data Models
```python
DiplomacyRelation: id, player_id, target_player_id,
                   status("verbündet"/"freund"/"neutral"/"unerwünscht"/"feind"),
                   updated_at
# Asymmetric: each player sets own relation independently
```

## Core Logic
```
GET EFFECTIVE RELATION(player_a, player_b):
  rel_a = DiplomacyRelation.get(player_a, player_b) or "neutral"
  rel_b = DiplomacyRelation.get(player_b, player_a) or "neutral"
  # Worst-case wins for hostile checks:
  if "feind" in [rel_a, rel_b]: return "feind"
  if "unerwünscht" in [rel_a, rel_b]: return "unerwünscht"
  # Best-case for friendly checks:
  if rel_a == "verbündet" AND rel_b == "verbündet": return "verbündet"
  if "freund" in [rel_a, rel_b]: return "freund"
  return "neutral"

TRADE BLOCK:
  if effective_relation in ["feind","unerwünscht"]: block all Kontor trade

AUTO-ATTACK (combat trigger):
  if army enters province AND effective_relation == "feind": trigger combat

BORDER CROSSING:
  if unit enters foreign province AND relation != "verbündet": trigger warning
  if relation == "feind": trigger auto-attack

WAR DECLARATION:
  require player.regierungsform.krieg_moeglich == 1
  set relation = "feind"
  → GameLog: "WAR_DECLARED: {player} vs {target}"

MORAL EFFECT:
  foreign culture in province (from 09_kulturpunkte):
    malus only if fremdkultur_verlust == 1 (Regierungsform)
```

## Endpoints
```
GET  /player/{id}/diplomacy → all relations list
POST /player/{id}/diplomacy {"target_player_id":int, "status":str}
GET  /player/{id}/diplomacy/{target_id} → effective bilateral relation
GET  /player/{id}/diplomacy/enemies → all feind/unerwünscht for quick combat lookup
```

## Validation
- krieg_moeglich=0 → reject war declaration "GOVERNMENT_NO_WAR"
- Cannot set own diplomacy to self
- Status must be one of 5 valid values
