# Verbrannte Zone - Wasteland Browsergame

Ein rundenbasiertes Strategie-Browsergame mit Postapokalypse-Setting.

## 📁 Projektstruktur

```
verbrannte_zone_project/
├── main.py                 # FastAPI Backend
├── index.html             # Haupt-HTML (minimalistisch)
├── css/
│   └── style.css         # Alle Styles
├── js/
│   ├── app.js            # Hauptlogik & Initialisierung
│   ├── worldmap.js       # Weltkarten-Generierung & -Rendering
│   └── province.js       # Provinz-Ansicht (30x30 Felder)
├── terrains/              # 30x30px PNG Terrain-Grafiken
│   └── README.md         # Anleitung zum Erstellen
└── data/
    └── worldmap.json     # Feste Weltkarten-Konfiguration
```

## 🚀 Installation & Start

### Voraussetzungen
```bash
pip install fastapi uvicorn
```

### Server starten
```bash
python main.py
```

Server läuft auf: `http://localhost:8000`

## 🎮 Spielfunktionen

### Weltkarte (50x50)
- Feste, generierte Karte mit 2 Hauptinseln
- Ozean (nicht betretbar)
- Landterrains: Wüste, Grasland
- Spieler-Startprovinz markiert

### Provinz-Ansicht (30x30)
- Detailansicht einzelner Provinzen
- Platzhalter für Gebäude-System
- Terrain-basierte Ressourcenproduktion (geplant)

### Ressourcen
- ⚙️ Eisen
- 🔩 Stahl
- ⛽ Treibstoff

### Rundenbasiert
- Ressourcenproduktion pro Runde
- Gebäude-Bau (in Entwicklung)
- Einheiten-Training (geplant)

## 🔧 Entwicklung

### Module bearbeiten

**Styles ändern:**
```bash
css/style.css
```

**Weltkarten-Logik:**
```bash
js/worldmap.js
```

**Provinz-System:**
```bash
js/province.js
```

**Hauptlogik:**
```bash
js/app.js
```

### API-Endpunkte

- `GET /player/{id}` - Spielerdaten abrufen
- `POST /player` - Neuen Spieler erstellen
- `POST /player/{id}/resources/produce` - Runde abschließen
- `GET /player/{id}/buildings` - Gebäude abrufen
- `POST /player/{id}/buildings` - Gebäude bauen

## 📝 TODO

- [ ] Terrain-Bilder erstellen (30x30 PNG)
- [ ] Gebäude-Platzierungssystem
- [ ] Einheiten-System
- [ ] Kampf-Mechanik
- [ ] Multiplayer-Funktionen
- [ ] Persistente Weltkarte im Backend

## 🛠️ Technologie-Stack

- **Backend:** Python 3, FastAPI, SQLite
- **Frontend:** Vanilla JavaScript (ES6+)
- **Styling:** CSS3 mit CSS-Variablen
- **Deployment:** Raspberry Pi 3B+ ready

## 📄 Lizenz

Internes Projekt - Verbrannte Zone Team
