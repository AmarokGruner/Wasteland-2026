# Feature: Hilfe & In-Game Wiki

## Ziel
Ein vollumfängliches, In-Game Wiki- und Hilfesystem basierend auf den Menüpunkten des klassischen Spiels. Es soll neuen Spielern den Einstieg erleichtern (FAQ, "erste Schritte") und fortgeschrittenen Spielern als Nachschlagewerk dienen (Gebäude-Info, Terrain-Boni, etc.).

## 1. Menüstruktur (Sidebar / Modal)
Das Hilfe-Menü soll folgende Navigationspunkte umfassen:
- **FAQ** (Häufig gestellte Fragen)
- **Admins, das Team** (Auflistung des Server-Teams)
- **Memberinfo** (Informationen zur Community/Regeln)
- **erste Schritte** (Tutorial für Einsteiger)
- **Rohstoff-Info** (Details zu allen abbaubaren/produzierbaren Ressourcen)
- **Gebäude-Info** (Alle Gebäude, Kosten, Voraussetzungen, Produktion)
- **Vorkommen-Info** (Wo findet man Kohle, Erdöl, Diamanten?)
- **Terrain-Info** (Boni/Mali, Regenwahrscheinlichkeiten der 42 Geländearten)
- **Lebewesen-Info** (Tiere, Monster, Kampfwert, Zuchtbedingungen)
- **Artikel-Info** (Produktionsgüter und Verbrauchsgegenstände)
- **Einheiten-Info** (Militärische Truppen, Stärke, Kosten)
- **Regierungsformen** (Vor- und Nachteile von Despotismus, Demokratie etc.)

## 2. Dynamische Wiki-Seiten (Backend & Frontend)
Anstatt die Daten statisch in HTML zu schreiben, sollen die Info-Seiten (z.B. `Gebäude-Info`, `Terrain-Info`) direkt über die bestehenden Backend-APIs generiert werden.
- **Vorteil:** Wenn Admins via `admin.html` die Werte für ein Gebäude oder Terrain ändern, ist das Wiki sofort aktuell.
- **Tech-Level-Filter:** Die Gebäude-Info zeigt standardmäßig alle Gebäude an, aber Spieler können optional nach "bereits freigeschaltet (Tech-Level X)" filtern.

### Beispiel: Gebäude-Info (UI-Design)
- Filter-Leiste: [Nahrung] [Ressourcen] [Industrie] [Militär]
- Tabelle oder Karten-Grid:
  - Name: Kartoffelfarm
  - Icon: 🥔
  - Baukosten: 50 Holz, 20 Eisen
  - Produziert: 10 Nahrung / Stunde
  - Bebaubar auf: Grasland, Steppe ... (Hover zeigt Terrain-Boni)

## 3. Statische Seiten (FAQ & Erste Schritte)
Diese Seiten werden per Markdown oder im Backend als statische JSON-Objekte gepflegt.

### FAQ (Beispiele)
- *Wie bekomme ich mehr Einwohner?* -> "Baue Wohnraum und sorge für ausreichend Nahrung und Wasser."
- *Meine Leute verhungern, obwohl Nahrung im Lager ist!* -> "Achte auf die Notfall-Reserve. Wenn das Lager leerläuft, kann es zu Transport-Engpässen kommen."
- *Wie kann ich neue Provinzen besiedeln?* -> "Rekrutiere Siedler im Militär-Tab und sende sie auf unbesetztes Terrain."

### Erste Schritte (Tutorial-Guide)
1. **Wasser & Nahrung:** Ohne Auffangbecken und eine erste Farm (z.B. Kartoffeln) stirbt deine Bevölkerung.
2. **Materialien:** Baue einen Holzfäller und Lehm/Steingruben für erste Baumaterialien.
3. **Wachstum:** Sorge für Wohnraum. Je höher die Zufriedenheit, desto mehr Leute ziehen zu dir.
4. **Forschung:** Baue eine Schule, um Tech-Punkte zu generieren und neue Gebäude freizuschalten.

## 4. API Endpoints
- `GET /wiki/faq` -> Liefert Liste von Fragen/Antworten.
- `GET /wiki/erste-schritte` -> Liefert den Beginner-Guide.
- Die restlichen Menüpunkte nutzen die bestehenden APIs:
  - `GET /terrains`
  - `GET /buildings/all`
  - `GET /resources`
  - `GET /units`

## 5. UI-Integration & Usability
- Das Wiki öffnet sich als großes **Modal-Overlay** (Popup) über dem Spiel, damit man nicht die Ansicht der aktuellen Provinz verliert.
- Oben rechts: Ein globales Suchfeld ("Wiki durchsuchen..."). Wenn ein Spieler "Öl" eintippt, zeigt es Ergebnisse aus "Ressourcen", "Vorkommen" und "Gebäude" (Raffinerie).
- Innerhalb des Spiels (z.B. in der Bau-Ansicht) gibt es kleine `[?]` Icons neben Gebäuden, die direkt die entsprechende Wiki-Seite im Modal öffnen.
