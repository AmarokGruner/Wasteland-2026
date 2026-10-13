# 💾 Backup Strategy & Disaster Recovery

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Backup-Strategie für:
- **Datenbank-Backups** - Regelmäßige Sicherung der SQLite Datenbank
- **Konfigurations-Backups** - Server Config, Environment Variables
- **Disaster Recovery** - Wiederherstellung nach Ausfall

---

## 🗄️ Datenbank-Backups

### Automatisierte Backups (Cronjob)

```bash
#!/bin/bash
# /opt/wasteland/scripts/backup_database.sh

BACKUP_DIR="/opt/wasteland/backups"
DB_PATH="/opt/wasteland/data/verbrannte_zone.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.db"

# Backup erstellen
cp "$DB_PATH" "$BACKUP_FILE"

# Komprimieren
gzip "$BACKUP_FILE"

# Backup Permissions setzen
chmod 600 "$BACKUP_FILE.gz"

# Alte Backups löschen (älter als 30 Tage)
find "$BACKUP_DIR" -name "backup_*.db.gz" -mtime +30 -delete

# Backup Log
echo "$(date): Backup erstellt - $BACKUP_FILE.gz" >> "$BACKUP_DIR/backup.log"

# Optional: Backup auf externen Storage kopieren
# rsync -avz "$BACKUP_FILE.gz" backup@external-server:/backups/wasteland/
```

### Cronjob Konfiguration

```bash
# Tägliche Backups um 03:00 Uhr
crontab -e

# Eintrag hinzufügen:
0 3 * * * /opt/wasteland/scripts/backup_database.sh >> /var/log/wasteland_backup.log 2>&1
```

### Backup Verzeichnis Struktur

```
/opt/wasteland/backups/
├── backup_20261014_030000.db.gz    # Heute
├── backup_20261013_030000.db.gz    # Gestern
├── backup_20261012_030000.db.gz    # Vorgestern
├── ...
└── backup.log                      # Backup Protokoll
```

### Offsite Backups (Optional)

```bash
#!/bin/bash
# /opt/wasteland/scripts/backup_offsite.sh

BACKUP_DIR="/opt/wasteland/backups"
REMOTE_USER="backup"
REMOTE_HOST="backup.example.com"
REMOTE_DIR="/backups/wasteland"

# Neuestes Backup finden
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.db.gz | head -1)

# Auf externen Server kopieren
rsync -avz "$LATEST_BACKUP" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

# Lokale Backups nach erfolgreichem Offsite-Transfer löschen (älter als 7 Tage)
find "$BACKUP_DIR" -name "backup_*.db.gz" -mtime +7 -delete
```

---

## ⚙️ Konfigurations-Backups

### Environment Variables Backup

```bash
#!/bin/bash
# /opt/wasteland/scripts/backup_config.sh

CONFIG_DIR="/opt/wasteland/config"
BACKUP_DIR="/opt/wasteland/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Environment Variables exportieren
env > "$BACKUP_DIR/env_backup_$TIMESTAMP.txt"

# nginx Config sichern
cp /etc/nginx/sites-available/wasteland "$BACKUP_DIR/nginx_wasteland_$TIMESTAMP.conf"

# Systemd Service Config sichern
systemctl cat wasteland > "$BACKUP_DIR/wasteland_service_$TIMESTAMP.txt"

# SSL Zertifikate sichern (falls vorhanden)
if [ -d /etc/letsencrypt/live/wasteland.local ]; then
    cp -r /etc/letsencrypt/live/wasteland.local "$BACKUP_DIR/ssl_$TIMESTAMP/"
fi

# Backup Log
echo "$(date): Config Backup erstellt" >> "$BACKUP_DIR/config_backup.log"
```

### Git Repository als Konfig-Backup

```bash
# Alle Configs in Git Versionierung
cd /opt/wasteland/config
git add .
git commit -m "config: Auto-backup $(date +%Y-%m-%d)"
git push origin master
```

---

## 🔄 Disaster Recovery Procedure

### Szenario 1: Datenbank verloren/gekappt

**Schritte:**
```bash
# 1. Neuestes Backup finden
ls -lt /opt/wasteland/backups/backup_*.db.gz | head -1

# 2. Backup entkomprimieren
gunzip /opt/wasteland/backups/backup_20261014_030000.db.gz

# 3. Datenbank wiederherstellen
cp /opt/wasteland/backups/backup_20261014_030000.db /opt/wasteland/data/verbrannte_zone.db

# 4. Permissions setzen
chown wasteland:wasteland /opt/wasteland/data/verbrannte_zone.db
chmod 600 /opt/wasteland/data/verbrannte_zone.db

# 5. Server neu starten
systemctl restart wasteland

# 6. Recovery verifizieren
curl http://localhost:8011/health/ready
```

### Szenario 2: Server Ausfall (neuer Server)

**Schritte:**
```bash
# 1. Neuen Server vorbereiten (Debian, Python 3.13)
# 2. Git Repository klonen
git clone https://github.com/AmarokGruner/Wasteland-2026.git /opt/wasteland
cd /opt/wasteland

# 3. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Datenbank aus Backup wiederherstellen
gunzip /pfad/zum/backup/backup_20261014_030000.db.gz
cp /pfad/zum/backup/backup_20261014_030000.db /opt/wasteland/data/verbrannte_zone.db

# 5. Environment Variables setzen
cp /opt/wasteland/config/.env.example /opt/wasteland/data/.env
# .env bearbeiten mit echten Werten

# 6. Systemd Service erstellen
sudo cp /opt/wasteland/wasteland.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wasteland
sudo systemctl start wasteland

# 7. nginx konfigurieren (falls HTTPS gewünscht)
sudo cp /opt/wasteland/nginx.conf /etc/nginx/sites-available/wasteland
sudo ln -s /etc/nginx/sites-available/wasteland /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. Server starten
uvicorn app.main:app --host 0.0.0.0 --port 8011
```

### Szenario 3: Datenkorruption (inkonsistente Datenbank)

**Schritte:**
```bash
# 1. Datenbank Integrität prüfen
sqlite3 /opt/wasteland/data/verbrannte_zone.db "PRAGMA integrity_check;"

# 2. Falls korrupt: Backup wiederherstellen
gunzip /opt/wasteland/backups/backup_20261013_030000.db.gz
cp /opt/wasteland/backups/backup_20261013_030000.db /opt/wasteland/data/verbrannte_zone.db

# 3. Datenbank reparieren (falls möglich)
sqlite3 /opt/wasteland/data/verbrannte_zone.db ".recover" | sqlite3 /tmp/repaired.db
cp /tmp/repaired.db /opt/wasteland/data/verbrannte_zone.db

# 4. Server neu starten
systemctl restart wasteland
```

---

## 📊 Backup Status Monitoring

### Backup Check Script

```bash
#!/bin/bash
# /opt/wasteland/scripts/check_backups.sh

BACKUP_DIR="/opt/wasteland/backups"
MAX_AGE_HOURS=25  # Backup sollte jünger als 25 Stunden sein

# Neuestes Backup finden
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.db.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ KEIN BACKUP GEFUNDEN!"
    exit 1
fi

# Alter des Backups prüfen
BACKUP_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")))
BACKUP_AGE_HOURS=$((BACKUP_AGE / 3600))

if [ $BACKUP_AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo "❌ BACKUP ZU ALT: $(date -d @$BACKUP_AGE +%Y-%m-%d %H:%M)"
    exit 1
fi

echo "✅ Letztes Backup: $(date -d @$BACKUP_AGE +%Y-%m-%d %H:%M) ($(du -h "$LATEST_BACKUP" | cut -f1))"

# Backup Integrität prüfen
gunzip -t "$LATEST_BACKUP" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup Integrität OK"
else
    echo "❌ Backup KORRUPT!"
    exit 1
fi

exit 0
```

### Cronjob für Backup Checks

```bash
# Täglich um 06:00 Uhr Backup Status prüfen
0 6 * * * /opt/wasteland/scripts/check_backups.sh >> /var/log/wasteland_backup_check.log 2>&1
```

---

## 📋 Backup Richtlinien

| Typ | Häufigkeit | Aufbewahrung | Storage |
|-----|------------|--------------|---------|
| **Datenbank** | Täglich (03:00) | 30 Tage | Lokal + Offsite |
| **Konfiguration** | Wöchentlich | 90 Tage | Git Repository |
| **SSL Zertifikate** | Bei Erneuerung | Bis Ablauf | Lokal + Offsite |

---

## 🎯 Best Practices

1. **IMMER Backups testen** - Regelmäßig Wiederherstellung üben
2. **Offsite Backups** - Mindestens 1 Backup extern speichern
3. **Backup Verschlüsselung** - Sensible Daten verschlüsseln
4. **Automatisierung** - Backups ohne manuelles Eingreifen
5. **Monitoring** - Backup Status überwachen und alerten

---

**Backups sind die letzte Verteidigungslinie gegen Datenverlust!**
