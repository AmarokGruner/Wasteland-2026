# 📋 Session-Start Checkliste

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## ✅ Pre-Session Checklist (VOR Session-Start)

### 1. Status prüfen
- [ ] `SESSION_LOG.md` lesen - Letzte Session analysieren
- [ ] Offene Aufgaben identifizieren
- [ ] Bekannte Probleme nachlesen

### 2. Repository Status
- [ ] `git status` - Uncommitted Changes prüfen
- [ ] `git log --oneline -5` - Letzte Commits ansehen
- [ ] Auf `master` Branch sein (`git checkout master`)

### 3. Entwicklungsumgebung
- [ ] Virtual Environment aktivieren: `source venv/bin/activate`
- [ ] Python Version prüfen: `python --version` (sollte 3.13+ sein)
- [ ] Abhängigkeiten aktuell: `pip list | grep -E "fastapi|sqlalchemy|uvicorn"`

### 4. Datenbank Status
- [ ] Datenbank existiert: `ls -la verbrannte_zone.db`
- [ ] Tabellen korrekt: `sqlite3 verbrannte_zone.db ".tables"`
- [ ] Einträge vorhanden: Mindestens 300+ Einträge (42 Terrain, 122 Gebäude, etc.)

### 5. Server Status
- [ ] Kein laufender Server auf Port 8011: `lsof -i :8011`
- [ ] Falls ja: Prozess beenden oder anderen Port wählen

---

## 🚀 Session-Start Commands

```bash
# 1. Ins Projektverzeichnis wechseln
cd /home/fabian/Wasteland_neu

# 2. Virtual Environment aktivieren
source venv/bin/activate

# 3. Git Status prüfen
git status
git log --oneline -5

# 4. SESSION_LOG.md lesen (WICHTIG!)
cat SESSION_LOG.md

# 5. Datenbank prüfen
ls -la verbrannte_zone.db
sqlite3 verbrannte_zone.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

# 6. Server starten (falls noch nicht läuft)
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

---

## 📝 Session-End Checklist (NACH Session-Beendigung)

### 1. Code Committen
- [ ] Alle Änderungen staged: `git add .`
- [ ] Sinnvolle Commit Message: `git commit -m "feat/description..."`
- [ ] Auf master Branch: `git checkout master`

### 2. Pushen (optional)
- [ ] Änderungen pushen: `git push origin master`

### 3. SESSION_LOG.md aktualisieren
- [ ] Aktuelle Session dokumentieren (Datum, Agent, Status)
- [ ] Erledigte Aufgaben eintragen
- [ ] Offene Aufgaben aktualisieren
- [ ] Bekannte Probleme notieren
- [ ] Nächste Schritte planen

### 4. Server stoppen (falls gestartet)
```bash
# PID finden
lsof -i :8011

# Prozess beenden
kill <PID>
```

---

## 🔍 Troubleshooting

### Häufige Probleme beim Session-Start:

**Problem 1: Port 8011 bereits belegt**
```bash
# Lösung: Prozess finden und beenden
lsof -i :8011
kill -9 <PID>

# Oder anderen Port verwenden
uvicorn app.main:app --port 8012
```

**Problem 2: ModuleNotFoundError**
```bash
# Lösung: Virtual Environment aktivieren
source venv/bin/activate

# Oder Abhängigkeiten neu installieren
pip install -r requirements.txt
```

**Problem 3: Datenbank nicht gefunden**
```bash
# Lösung: Datenbank initialisieren
python seeds/seed_main.py

# Oder Datenbank kopieren vom Original
cp /home/fabian/Wasteland/verbrannte_zone.db .
```

**Problem 4: Git Remote nicht konfiguriert**
```bash
# Lösung: Remote hinzufügen
git remote add origin https://github.com/AmarokGruner/Wasteland-2026.git
git push -u origin master
```

---

## 📊 Wichtige Dateipfade

| Datei | Pfad | Beschreibung |
|-------|------|--------------|
| Hauptanwendung | `app/main.py` | FastAPI Application |
| Datenbankmodelle | `app/models.py` | SQLAlchemy Models |
| Server Config | `app/config.py` | PORT, HOST, SECRET_KEY |
| Datenbank-Seed | `seeds/seed_main.py` | Initialisierungsskript |
| Session Log | `SESSION_LOG.md` | Entwicklungs-Log |
| Projektübersicht | `AGENT_START.md` | Komplette Übersicht |

---

## 🎯 Session-Ziele definieren

Vor jeder Session klare Ziele setzen:

```markdown
## Session-Ziele [Datum]
- [ ] Ziel 1 (z.B. Neues Feature implementieren)
- [ ] Ziel 2 (z.B. Bugfix durchführen)
- [ ] Ziel 3 (z.B. Dokumentation aktualisieren)

## Erwarteter Output
- Datei 1 geändert/erstellt
- Datei 2 geändert/erstellt
- Tests bestanden
- Dokumentation aktualisiert
```

---

**Diese Checkliste MUSS vor jeder Session durchgegangen werden!**  
**Ohne korrekten Session-Start keine konsistente Entwicklung!**
