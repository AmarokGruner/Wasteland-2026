# Wasteland - Verbrannte Zone

**Postapokalyptisches Browser-Strategiespiel | Version 1.6**

---

## 📖 Projektbeschreibung

Wasteland ist ein browserbasiertes Echtzeit-Strategiespiel im postapokalyptischen Setting. Spieler gründen Provinzen in einer zerstörten Welt, verwalten Ressourcen, bauen Gebäude, handeln mit anderen Spielern und kämpfen um Territorium.

### Kernkonzept
- **Setting:** Verbrannte Zone nach einer Katastrophe
- **Gameplay:** Provinzverwaltung, Ressourcenmanagement, Expansion
- **Multiplayer:** Spieler können mit anderen handeln oder kämpfen
- **Progression:** Von einfacher Siedlung zur Großstadt

---

## 🛠️ Technologie-Stack

| Schicht | Technologie | Version |
|---------|-------------|---------|
| **Backend** | FastAPI (Python) | 3.13+ |
| **Datenbank** | SQLite + SQLAlchemy ORM | - |
| **Frontend** | Vanilla JavaScript + HTML5/CSS3 | ES6+ |
| **Authentifizierung** | JWT Tokens | - |
| **Server** | Uvicorn ASGI | - |

### Architektur
```
Client (Browser)
    ↓ HTTP/REST
FastAPI Backend (Port 8011)
    ↓ SQLAlchemy
SQLite Datenbank
```

---

## 📁 Verzeichnisstruktur

```
Wasteland/
├── app/                        # FastAPI Backend
│   ├── main.py                # Hauptanwendung, Router-Mounting
│   ├── config.py              # Konfiguration (PORT, HOST, SECRET_KEY)
│   ├── database.py            # SQLAlchemy Engine & Session
│   └── models.py              # Alle Datenbankmodelle (30+ Tabellen)
├── seeds/                    # Datenbank-Initialisierung
│   ├── db_config.py           # Verbindung zur Datenbank
│   ├── seed_gebaeude.py       # 209 Gebäude-Typen
│   ├── seed_ressourcen.py     # 153 Ressourcen
│   └── seed_terrains.py       # 42 Terrain-Typen
├── js/                       # Frontend JavaScript (21 Module)
│   ├── app.js                 # Hauptanwendung
│   ├── province.js            # Provinz-Management
│   └── ...                   # Weitere Module (21 Dateien)
├── admin/                    # Admin UI HTML
│   └── resources.html         # Ressourcen-Verwaltung
├── admin.html                # Haupt-Admin-Oberfläche
├── index.html                # Spieler-Oberfläche
├── docs/                     # Dokumentation (8 Dateien)
│   ├── 01_PROJEKTUEBERSICHT.md    # Diese Datei
│   ├── 02_DATENBANK.md            # Datenbank-Schema
│   ├── 03_API.md                  # API Endpunkte
│   ├── 04_GAMEMECHANIK.md         # Spielmechaniken
│   ├── 05_ADMIN_SYSTEM.md         # Admin-Funktionen
│   ├── 06_SICHERHEIT.md           # Sicherheit & Audit
│   ├── 07_DEPLOYMENT.md           # Setup & Deployment
│   └── 08_ENTWICKLUNG.md          # Testing & CI/CD
├── .gitignore               # Ignorierte Dateien
└── requirements.txt         # Python Abhängigkeiten
```

---

## 📊 Datenbank-Übersicht

| Tabelle | Anzahl | Beschreibung |
|---------|--------|--------------|
| `gebaeude_typen` | 209 | Gebäude-Typen |
| `ressourcen` | 153 | Ressourcen-Arten |
| `vorkommen` | 24 | Bodenschätze/Vorkommen |
| `terrain_typen` | 42 | Landschaftstypen |
| `provinzen` | - | Spieler-Provinzen |
| `provinz_gebaeude` | - | Gebäude in Provinzen |
| `einheiten_typen` | 63 | Militäreinheiten |
| `lebewesen` | 8 | Tierarten |
| `artikel` | 15 | Handelsartikel |
| `regierungsformen` | 7 | Staatsformen |

---

## 🎮 Spielmechaniken (Übersicht)

1. **Gebäudebau** - 209 verschiedene Gebäude mit Tech-Level
2. **Ressourcen-Management** - 153 Ressourcen, Produktion & Lagerung
3. **Terrains** - 42 Landschaftstypen mit Effektivitäts-Boni
4. **Militär** - 63 Einheitentypen, Kämpfe & Belagerungen
5. **Handel** - Marktplätze, Spieler-Handel, Kontore
6. **Regierung** - 7 Staatsformen mit Boni
7. **Weltkarte** - 50x50 Felder, Weltgenerierung
8. **Server-Tick** - Automatische Rundenmechanik

---

## 🔐 Sicherheit

- JWT-basierte Authentifizierung (24h Token)
- bcrypt Password Hashing
- Rate Limiting für Login-Versuche
- SQLAlchemy ORM (SQL-Injection Schutz)
- Pydantic Models für Input Validierung

---

## 🚀 Schnellstart

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank initialisieren
python seeds/seed_main.py

# Server starten
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

---

## 📚 Weitere Dokumentation

- **Datenbank-Schema:** `02_DATENBANK.md`
- **API Endpunkte:** `03_API.md`
- **Spielmechaniken:** `04_GAMEMECHANIK.md`
- **Admin-System:** `05_ADMIN_SYSTEM.md`
- **Sicherheit:** `06_SICHERHEIT.md`
- **Deployment:** `07_DEPLOYMENT.md`
- **Entwicklung:** `08_ENTWICKLUNG.md`

---

**Letzte Aktualisierung:** 2026-10-14  
**GitHub:** https://github.com/AmarokGruner/Wasteland-2026
