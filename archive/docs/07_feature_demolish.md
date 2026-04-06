# Feature: Demolish / Abriss

## Source (FAQ 3.2.3)
- Demolish returns 50% of rohstoffbedarfbau resources (NO mips refund)
- Cannot demolish individual upgrade levels – whole building only
- Demolish costs Arbeitspunkte (same as build)
- Ruin demolish: 25% refund only
- Stadtausbau buildings: cannot be demolished normally (auto-replaced on upgrade)
- Land→City converted fields: field stays city type after demolish

## Core Logic
```
REFUND:
  normal building: refund = rohstoffbedarfbau * 0.5 per resource
  ruin building:   refund = rohstoffbedarfbau * 0.25

LAGER CHECK:
  refund resources only up to lagerkapazitaet_total; overflow lost

FIELD STATE AFTER DEMOLISH:
  if field was converted from Land to City: stays City (not reverted)
  field.occupied_building_id = NULL
  field.is_available = True

ARBEITSPUNKTE:
  deduct same AP as original build cost
```

## Endpoint
```
POST /province/{id}/demolish/{instance_id}
→ {"refunded_resources": {...}, "ap_cost": int, "field_id": int}
```

## Validation
- Cannot demolish Stadtausbau (Camp/Siedlung etc.)
- Cannot demolish if AP insufficient
- Cannot demolish min_soldiers buildings (Bunker)
