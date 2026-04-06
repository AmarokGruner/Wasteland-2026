# Feature: Notfall-Reserve (Lager-Minimum)

## Ziel
Verhindern, dass automatische Produktionsketten oder Handelsrouten überlebenswichtige Ressourcen (Nahrung, Wasser) komplett leersaugen und die Bevölkerung im nächsten Tick verhungert.

## 1. Datenbank-Erweiterung (`lager`)
- Neue Spalte: `notfall_reserve` (Integer, Default 0).

## 2. Backend-Logik
- Bei allen Abbuchungen aus dem Lager (Bauen, Transport, Handel, Produktion-Verbrauch):
  - `verfuegbare_menge = menge - notfall_reserve`
  - Wenn angeforderte Menge > `verfuegbare_menge` -> Blockiere Aktion mit Fehler "Notfallreserve erreicht".
- **Ausnahme:** Der Bevölkerungs-Verbrauch (Server-Tick für Essen/Trinken) ignoriert die Reserve! Wenn die Leute hungern, essen sie die Reserve.

## 3. Frontend-UI (Provinz-Tab: Lager)
- In der Lager-Tabelle neben jeder Ressource ein Input-Feld für die Reserve.
- Klick auf "Speichern" -> `PATCH /provinzen/{id}/lager/{res_id}/reserve { amount: 100 }`.
- Visuelle Darstellung: Kapazitätsbalken hat eine kleine rote Markierung bei der Reserve-Grenze. "150 / 1000 (100 gesperrt)".

## 4. Auto-Reserve (Optionales QoL)
- Checkbox in Provinz-Einstellungen: "Automatisch 2 Tagesrationen Nahrung/Wasser sperren".
- Backend berechnet beim Speichern den Bedarf von 48h und setzt die Reserve entsprechend.
