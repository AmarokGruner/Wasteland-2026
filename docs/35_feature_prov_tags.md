# Feature: Provinz-Spezialisierungen (Admin-Tags)

## Ziel
Admins sollen bestimmten Provinzen global besondere Eigenschaften (Tags) zuweisen können, um strategische Knotenpunkte (Choke Points, Handelszentren) auf der Karte zu schaffen.

## 1. Datenbank-Erweiterung
- Neue Tabelle `province_tags`: `id`, `name`, `description`, `bonus_type`, `bonus_value`.
  (z.B. "Handelsknoten", "Handelskapazität +50%").
- Mapping-Tabelle `province_has_tags`: `province_id`, `tag_id`.

## 2. Backend-Logik
- Beim Server-Tick oder bei API-Requests werden die Tags der Provinz geladen.
- Wenn Tag `bonus_type == 'production_iron'`, multipliziere Eisen-Ausbeute mit `bonus_value`.
- Wenn Tag `bonus_type == 'defense'`, addiere x% auf den Verteidigungswert im Kampf.

## 3. Admin-UI
- In der Weltkarten-Ansicht (Admin): Klick auf Provinz -> "Tag hinzufügen".
- Dropdown mit allen verfügbaren Tags.
- Tags können farblich auf der Karte markiert werden (z.B. goldener Rahmen für Handelsknoten).

## 4. Spieler-UI
- Klickt ein Spieler auf der Weltkarte auf diese Provinz, steht im Tooltip:
  "👑 Besondere Provinz: Handelsknoten (+50% Karren)".
- Gibt Anreiz für PvP, um diese wertvollen Kacheln zu erobern.
