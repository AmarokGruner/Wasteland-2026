# Deployment & Setup

**Wasteland Deployment Guide | Version 1.6**

---

## 🚀 Schnellstart (5 Minuten)

### Voraussetzungen
- Python 3.13+
- SQLite (in Python enthalten)
- Git

### Installation
```bash
# 1. Repository klonen
git clone https://github.com/AmarokGruner/Wasteland-2026.git
cd Wasteland

# 2. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Datenbank initialisieren
python seeds/seed_main.py

# 5. Server starten
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

### Zugriff
- **Frontend:** http://localhost:8011
- **Admin:** http://localhost:8011/admin
- **API Docs:** http://localhost:8011/docs (Swagger UI)

---

## 📦 Detaillierte Installation

### 1. Python Environment
```bash
# Empfohlen: Python 3.13 oder höher
python3 --version

# Virtual Environment (isoliert vom System-Python)
python3 -m venv wasteland_venv
source wasteland_venv/bin/activate

# Aktivierung prüfen
which python  # Sollte auf venv zeigen
```

### 2. Python Abhängigkeiten
```bash
# Hauptabhängigkeiten
pip install fastapi uvicorn sqlalchemy pydantic bcrypt

# Optional: Monitoring
pip install prometheus-client

# Alle aus requirements.txt
pip install -r requirements.txt
```

### 3. Datenbank initialisieren
```bash
# Seed-Daten laden (Gebäude, Ressourcen, Terrains)
python seeds/seed_main.py

# Datenbank-Datei wird erstellt: verbrannte_zone.db
```

### 4. Server starten (Development)
```bash
# Mit Auto-Reload bei Code-Änderungen
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload

# Ohne Reload (produktionsnäher)
uvicorn app.main:app --host 0.0.0.0 --port 8011
```

---

## 🐳 Docker Deployment

### Dockerfile erstellen
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Datenbank initialisieren
RUN python seeds/seed_main.py

# Port expose
EXPOSE 8011

# Server starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  wasteland:
    build: .
    ports:
      - "8011:8011"
    volumes:
      - ./verbrannte_zone.db:/app/verbrannte_zone.db
    environment:
      - SECRET_KEY=your_secret_key_here
      - DATABASE_URL=sqlite:///./verbrannte_zone.db

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - wasteland
```

### Docker starten
```bash
docker-compose up -d
```

---

## 🌐 nginx Reverse Proxy (Production)

### Konfiguration
```nginx
# /etc/nginx/sites-available/wasteland
server {
    listen 443 ssl;
    server_name wasteland.example.com;

    # SSL Zertifikate (Let's Encrypt empfohlen)
    ssl_certificate /etc/ssl/certs/wasteland.crt;
    ssl_certificate_key /etc/ssl/private/wasteland.key;

    # Proxy zum FastAPI Backend
    location / {
        proxy_pass http://127.0.0.1:8011;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Health Check
    location /health {
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
```

### Aktivieren
```bash
sudo ln -s /etc/nginx/sites-available/wasteland /etc/nginx/sites-enabled/
sudo nginx -t  # Konfiguration testen
sudo systemctl reload nginx
```

---

## 🔄 Systemd Service (Autostart)

### Service-Datei erstellen
```ini
# /etc/systemd/system/wasteland.service
[Unit]
Description=Wasteland Browser Game Server
After=network.target

[Service]
Type=simple
User=fabian
Group=fabian
WorkingDirectory=/home/fabian/Wasteland
Environment="PATH=/home/fabian/Wasteland/venv/bin"
ExecStart=/home/fabian/Wasteland/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8011
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Service verwalten
```bash
# Aktivieren und starten
sudo systemctl enable wasteland
sudo systemctl start wasteland

# Status prüfen
sudo systemctl status wasteland

# Logs ansehen
sudo journalctl -u wasteline -f
```

---

## 🔑 SSL Zertifikate (Let's Encrypt)

### Certbot installieren
```bash
sudo apt install certbot python3-certbot-nginx
```

### Zertifikat holen
```bash
sudo certbot --nginx -d wasteland.example.com
```

### Auto-Renewal
Certbot richtet automatische Erneuerung ein (alle 90 Tage).

---

## 📊 Monitoring & Logging

### Prometheus Metrics
- **Endpoint:** `http://localhost:8011/metrics`
- **Grafana Dashboard** für Visualisierung

### Log-Dateien
| Datei | Inhalt |
|-------|--------|
| `logs/wasteland.log` | Server-Logs |
| `logs/error.log` | Fehler-Logs |
| `verbrannte_zone.db` | SQLite Datenbank |

### Log-Rotation
```bash
# /etc/logrotate.d/wasteland
/home/fabian/Wasteland/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## 🔄 Updates & Migrationen

### Code aktualisieren
```bash
cd /home/fabian/Wasteland
git pull origin main

# Abhängigkeiten aktualisieren
pip install -r requirements.txt

# Datenbank migrieren (falls nötig)
python scripts/db_migration.py

# Server neu starten
sudo systemctl restart wasteline
```

### Backup erstellen
```bash
# Datenbank backupen
cp verbrannte_zone.db verbrannte_zone.db.backup.$(date +%Y%m%d)

# Komplettes Projekt backupen
tar -czf wasteland_backup_$(date +%Y%m%d).tar.gz \
    app/ seeds/ js/ admin.html index.html requirements.txt
```

---

## 🧪 Testing

### Unit Tests
```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v --cov=app
```

### Linting
```bash
pip install flake8 mypy
flake8 app/
mypy app/
```

---

## 📝 Troubleshooting

### Häufige Probleme

**1. Port 8011 bereits belegt**
```bash
lsof -i :8011  # Prozess finden
sudo kill <PID>  # Prozess töten
```

**2. Datenbank-Fehler**
```bash
# Datenbank reparieren
sqlite3 verbrannte_zone.db "PRAGMA integrity_check;"

# Neu initialisieren (ACHTUNG: Datenverlust!)
rm verbrannte_zone.db
python seeds/seed_main.py
```

**3. Import-Fehler**
```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Abhängigkeiten neu installieren
pip install -r requirements.txt --force-reinstall
```

---

## ✅ Deployment Checklist

- [ ] Python 3.13+ installiert
- [ ] Virtual Environment erstellt
- [ ] requirements.txt installiert
- [ ] Datenbank initialisiert (seed_main.py)
- [ ] Server läuft auf Port 8011
- [ ] HTTPS konfiguriert (SSL Zertifikat)
- [ ] nginx Reverse Proxy eingerichtet
- [ ] Systemd Service aktiviert
- [ ] Backups eingerichtet
- [ ] Monitoring konfiguriert
- [ ] Tests bestanden

---

**Letzte Aktualisierung:** 2026-10-14  
**Empfohlene Python-Version:** 3.13+
