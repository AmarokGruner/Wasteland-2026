# Note: Gebäude Abreißen

## Status
Already defined in: **07_feature_demolish.md**

## Summary (reference)
- POST /province/{id}/demolish/{instance_id}
- Refund: 50% rohstoffbedarfbau resources (NO mips)
- Ruin buildings: 25% refund only
- Whole building only (no partial level demolish)
- Costs same Arbeitspunkte as build
- Cannot demolish: Stadtausbau, Bunker, buildings with AP insufficient
- Field stays City type after demolish (not reverted to Land)

## If not yet implemented → use 07_feature_demolish.md as prompt
