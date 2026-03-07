# Wasteland FAQ Knowledge Base

Dieses Dokument fasst Kernkonzepte, Architekturen und Schnittstellen des Wasteland-Projekts zusammen und dient als Nachschlagewerk für Entwickler und Betreiber.

## 1. Grundkonzepte
- Provinz: künstlerisch simulierte Spielregion mit Zeit, Ressourcen, Bevölkerung, Gebäuden.
- Spulen (Zeitvorlauf): 24 Stunden pro Spulvorgang; erzeugt Produktion, Bevölkerung und Ereignisse.
- Vorschau: Prognose der nächsten 24 Stunden; dient der Planung vor dem Spulen.
- Stadtaufbau (Stadtausbau): Mehr Stadtfelder durch Freischaltungen; Camp, Dorf, Ort, Stadt sind Stufen der Expansion.
- Stadtfelder vs. Landfelder: Stadtfelder können mit Stadtgebäuden belegt werden; Landfelder bleiben ggf. unurbanisiert oder tragen Landnutzung.

## 2. Stadtausbau – Option A (robust, 4 Stufen)
- Stage 1 – Camp: 5 Felder in Kreuzform (Zentrum + 4 Nachbarn)
- Stage 2 – Dorf: 4 Felder diagonale um das Zentrum
- Stage 3 – Ort: 4 Felder als Fortsetzung des Startkreuzes
- Stage 4 – Stadt: 8 Felder Erweiterung; formt ein kräftigeres Kreuz um den Kern
- Gesamt Felder Stage 1–4: 5 + 4 + 4 + 8 = 21
- Randzone bleibt unurbanisiert (x) als Puffer

Hinweis: Diese Version priorisiert eine robuste, deterministische Expansion mit klarer Zentralität. Sie ist bewusst einfach und wiederholbar, ideal für Prototyping und Testing.

## 3. Rendering der Stadtfelder
- Rendering-Ansatz: Die Koordinatenlisten pro Stage bestimmen, welche Felder als Stadtfelder gelten.
- Stadtfelder werden grafisch als grau gemustertes Muster (gepflastert frei) dargestellt.
- Frontend-Logik: CityTiles-Koordinaten werden bei Rendering berücksichtigt und Felder außerhalb der Koordinaten bleiben Land/Leer.

## 4. Datenmodell (robust & erweiterbar)
- Neue Mapping-Tabelle provinzen_stadt_tile_coords
  - id: PK
  - provinzen_id: Integer (FK zu Provinzen)
  - stadtausbau_id: Integer (Referenz zu Stadtausbau-Art)
  - stage: Integer (1..4)
  - coords: TEXT (JSON-Array der Koordinaten [[x,y], ...])
  - UNIQUE(provinzen_id, stadtausbau_id, stage)

- Seed-Ansatz: Idempotentes Seed-Skript erzeugt Stage 1–4 Koordinaten (Stage 1 Camp Kreuz, Stage 2 diagonale, Stage 3 Ort, Stage 4 Kreuz-Verstärkung).

- API-Endpunkt (konzise): GET /province/{pid}/citytiles liefert citytiles fuer eine Provinz.

## 5. Seed & API-Integration (Kern-APIs)
- seed_citytiles.py: eigenständiges Seed-Skript, erzeugt provinzen_stadt_tile_coords und befüllt Stage 1–4.
- main.py: neuer Endpunkt province/{pid}/citytiles zur Abfrage der Koordinaten.
- seed_buildings.py: optionaler Platz für Seed-Erweiterungen, z.B. CityTiles in denselben Seed-Lauf integrieren.

## 6. Tests & Validation
- Health-Check-Route (/health) recommended.
- Simple API-Tests (curl/pytest) für CityTiles-Endpunkt.
- Validierung, dass Stage-Koordinaten nicht außerhalb der Provinz liegen und keine Überschneidungen mit bestehenden Feldern verursachen.

## 7. Betrieb & Deployment
- Port-Verwaltung: Standard 8000; optional per PORT-Umgebungsvariable anpassbar.
- Logging für CityTiles-API: Audit-Logging der Endpunkte.
- Migration: Bei Änderungen am Schema -> Migration-Strategie definieren.

## 8. Referenz-Variablen & Patch-Plan
- Patch A (Seed CityTiles + CityTiles Endpunkt) vorgesehen; Patch-Bedarf optional für erweiterte Stufen.

## 9. Hinweise
- Die Koordinatenbasierte Rendering-Logik ist eng mit der Prototyp-UI verbunden. Falls du eine UI-Komponente wünschst, kann ich eine einfache Canvas-/SVG-Variante vorschlagen.

Hinweis: Dieses Dokument ist eine lebendige Wissensdatenbank. Aktualisiere es, wenn neue Stadtausbau-Stufen, Koordinaten-Logiken oder Rendering-Details festgelegt werden.
