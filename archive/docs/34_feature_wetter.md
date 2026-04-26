# Feature: Globales Wetter & Jahreszeiten

## Ziel
Statt statischem Regen (X%) soll das Wetter dynamisch sein. Saisons beeinflussen die Produktion von Nahrung und Wasser global.

## 1. Global State (DB)
- Neue Tabelle `world_state`: `id=1`, `current_season` (Enum: Spring, Summer, Autumn, Winter), `season_ticks_left` (Int), `active_event` (String/Null).

## 2. Saison-Mechanik
- Ein Ingame-Jahr hat z.B. 28 Tage (7 Tage pro Saison).
- Der Server-Tick reduziert `season_ticks_left`. Bei 0 -> Wechsel zur nächsten Saison.
- **Modifikatoren:**
  - **Sommer:** `regen_pct` auf allen Terrains -20%. Wasserproduktion sinkt.
  - **Herbst:** Ernte-Bonus! Farmen produzieren +25% Nahrung.
  - **Winter:** Heizbedarf! Basis-Treibstoff-Verbrauch der Bevölkerung steigt. Farmen -50%.
  - **Frühling:** `regen_pct` +20%.

## 3. Frontend-UI
- Topbar: Zeigt neben dem Zeitguthaben ein Saison-Icon (🌸 ☀️ 🍂 ❄️).
- Tooltip beim Hover: "Aktuell: Sommer (Noch 3 Tage). Erhöhter Wasserbedarf!"
- Provinz-Ansicht -> Gebäude-Details: Zeigt den saisonalen Malus/Bonus transparent an (z.B. "Kartoffelfarm: 10/h (-5 durch Winter)").

## 4. Admin-Tool
- Admin-Dashboard: Dropdown zum sofortigen Wechseln der Jahreszeit (für Testing oder Events).
