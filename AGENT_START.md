# 🎮 Wasteland - Verbrannte Zone

**Ein postapokalyptisches Browser-Strategiespiel mit FastAPI Backend und SQLite Datenbank.**

---

## 🚀 Schnellstart für KI-Agenten

Dieses Projekt kann von einem KI-Agenten komplett neu aufgesetzt und entwickelt werden. Alle notwendigen Informationen sind in diesem Repository enthalten.

### 1. Projektübersicht

| Komponente | Technologie | Beschreibung |
|------------|-------------|--------------|
| **Backend** | FastAPI (Python 3.13) | REST API mit SQLite |
| **Frontend** | Vanilla JS + HTML/CSS | Kein Framework |
| **Datenbank** | SQLite | Relationale Datenbank mit SQLAlchemy ORM |
| **Authentifizierung** | JWT Tokens | Session-basiert |
| **Deployment** | Docker / Systemd | Uvicorn ASGI Server |

### 2. Verzeichnisstruktur

```
Wasteland_neu/
├── app/                    # FastAPI Backend
│   ├── main.py            # Hauptanwendung, Router-Mounting
│   ├── config.py          # Konfiguration (PORT, HOST, SECRET_KEY)
│   ├── database.py        # SQLAlchemy Engine & Session
│   └── models.py          # Alle Datenbankmodelle (30+ Tabellen)
├── seeds/                 # Datenbank-Initialisierung
│   ├── db_config.py       # Verbindung zur Datenbank
│   ├── seed_gebaeude.py   # 209 Gebäude-Typen
│   ├── seed_ressourcen.py # 153 Ressourcen
│   └── seed_terrains.py   # 42 Terrain-Typen
├── js/                    # Frontend JavaScript (21 Module)
│   ├── app.js             # Hauptanwendung
│   ├── province.js        # Provinz-Management
│   ├── buildings-data.js  # Gebäudedaten
│   └── ...               # Weitere Module
├── admin/                 # Admin UI HTML
│   └── resources.html     # Ressourcen-Verwaltung
├── admin.html             # Haupt-Admin-Oberfläche
├── index.html             # Spieler-Oberfläche
├── docs/                  # Vollständige Dokumentation (26 Dateien)
│   ├── 00_meta_prompt_engineer.md    # KI-Agent Anweisungen
│   ├── 00_session_start.md           # Session-Start Guide
│   ├── COMPLETE_CLEAN_BUILD_GUIDE.md # Kompletter Aufbau
│   └── ...                          # Feature-Dokumentationen
├── .gitignore             # Ignorierte Dateien
└── requirements.txt       # Python Abhängigkeiten
```

### 3. Datenbank-Schema (Kern-Tabellen)

| Tabelle | Beschreibung | Wichtige Felder |
|---------|--------------|-----------------|
| `gebaeude_typen` | 209 Gebäude-Typen | id, name, kategorie, tech_level, baukosten_mips |
| `ressourcen` | 153 Ressourcen | id, name, typ, wert |
| `vorkommen` | 24 Vorkommensarten | id, name, typ, tech, suchkosten |
| `terrain_typen` | 42 Terrain-Typen | id, name, farbe, effektivitaet |
| `provinzen` | Spieler-Provinzen | id, name, besitzer_id, mips, bevölkerung |
| `provinz_gebaeude` | Gebäude in Provinzen | provinz_id, gebaeude_typ_id, x, y, level |
| `einheiten_typen` | 63 Einheitentypen | id, name, kosten, staerke |
| `lebewesen` | 8 Tierarten | id, name, typ, aggressivitaet |
| `artikel` | 15 Artikel | id, name, typ, wert |
| `regierungsformen` | 7 Regierungsformen | id, name, bonusse |

### 4. API Endpunkte (Hauptkategorien)

```
Auth:
  POST /auth/register
  POST /auth/login
  GET  /auth/me

Provinz:
  GET    /province/
  POST   /province/
  GET    /province/{id}
  PUT    /province/{id}
  POST   /province/{id}/build           # Gebäude bauen
  POST   /province/{id}/demolish        # Gebäude abreißen
  GET    /province/{id}/buildings       # Alle Gebäude

Admin:
  GET    /admin/dashboard
  POST   /admin/gebaeude_typen          # Gebäude verwalten
  POST   /admin/ressourcen              # Ressourcen verwalten
  GET    /admin/provinzen              # Provinzen verwalten

Welt:
  GET    /world/map                    # Weltkarte
  GET    /world/terrains               # Terrains
```

### 5. Wichtige Spielmechaniken

#### Gebäude-System
- **209 verschiedene Gebäude** mit unterschiedlichen Funktionen
- Kategorien: Farm, Industrie, Bildung, Militär, Spezial
- Tech-Level erforderlich für Bau
- MIPS-Kosten + Rohstoffbedarf
- Ausbaubar (bis zu 10 Stufen) bei einigen Gebäuden
- Einmalige Gebäude (pro Provinz nur einmal)

#### Ressourcen-Management
- **153 verschiedene Ressourcen**
- Typen: Nahrung, Getränk, Baurohstoff, Luxus, etc.
- Produktion durch Gebäude
- Lagerkapazität begrenzt
- Handel zwischen Provinzen

#### Terrains & Weltkarte
- **42 Terrain-Typen** mit verschiedenen Effektivitäten
- 50x50 Weltkarte (2500 Zellen)
- Gebäude haben Terrain-Boni
- Vorkommen auf bestimmten Terrains

#### Runden-System (Ticks)
- Server Tick alle 60 Sekunden
- Berechnet: Produktion, Verbrauch, Wachstum
- Gamelog für Events
- Automatische Cleanup-Routinen

### 6. Sicherheitsvorgaben

#### Authentifizierung
- JWT Tokens mit 24h Ablauf
- Password Hashing mit bcrypt
- Rate Limiting für Login-Versuche

#### Autorisierung
- Admin-Rollen für Verwaltungsfunktionen
- Provinz-Besitzprüfung bei Aktionen
- API Token Validierung

#### Datenvalidierung
- Pydantic Models für alle Requests
- SQL-Injection Schutz durch SQLAlchemy ORM
- Input Sanitization

### 7. Entwicklungsumgebung aufsetzen

```bash
# 1. Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Datenbank initialisieren
python seeds/seed_main.py

# 4. Server starten
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

### 8. Wichtige Dateien für KI-Agenten

**Zum Starten des Projekts lesen:**
1. `docs/00_meta_prompt_engineer.md` - KI-Agent Konfiguration
2. `docs/00_session_start.md` - Session-Start Checkliste
3. `docs/COMPLETE_CLEAN_BUILD_GUIDE.md` - Kompletter Aufbau-Guide
4. `docs/SETUP_AND_CLEAN_BUILD.md` - Schnelleinrichtung

**Für Feature-Entwicklung:**
- `docs/01_feature_einheiten.md` - Militärsystem
- `docs/03_feature_ruinen.md` - Ruinen-Mechanik
- `docs/08_feature_markt_handel.md` - Handelssystem
- `docs/24_feature_weltgenerierung.md` - Weltkarte
- `docs/29_feature_auth_system.md` - Authentifizierung

**Für Datenbank-Änderungen:**
- `docs/27_weltkarte_db_migration.md` - Migrationen
- `app/models.py` - Alle Modelle

### 9. Testing

```bash
# Unit Tests
pytest tests/

# Integration Tests
pytest tests/integration/

# Linting
flake8 app/
mypy app/
```

### 10. Deployment

#### Docker
```bash
docker build -t wasteland .
docker run -p 8011:8011 wasteland
```

#### Systemd Service
```bash
sudo cp wasteland.service /etc/systemd/system/
sudo systemctl enable wasteland
sudo systemctl start wasteland
```

#### nginx Reverse Proxy (Port 443)
```nginx
server {
    listen 443 ssl;
    server_name wasteland.local;
    
    location / {
        proxy_pass http://127.0.0.1:8011;
    }
}
```

---

## 📚 Vollständige Dokumentation

Alle 26 Dokumentationsdateien im `docs/` Verzeichnis beschreiben:
- ✅ Datenbank-Schema und Migrationen
- ✅ API Schnittstellen (REST)
- ✅ Spielmechaniken (37 Features)
- ✅ Sicherheitskonzepte
- ✅ Admin-Oberfläche
- ✅ UI/UX Design
- ✅ Fehlerbehebung und Audit

---

## 🎯 Nächste Schritte für KI-Agenten

1. **Lies** `docs/00_meta_prompt_engineer.md` für Agenten-Konfiguration
2. **Folge** `docs/00_session_start.md` für Session-Setup
3. **Setze auf** mit `docs/COMPLETE_CLEAN_BUILD_GUIDE.md`
4. **Entwickle** Feature für Feature basierend auf `docs/XX_feature_*.md`

---

**Projektstatus:** v1.6 - Voll funktionsfähig  
**Letztes Update:** 2026-10-13  
**GitHub:** https://github.com/AmarokGruner/Wasteland-2026
