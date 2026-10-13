# 📊 Monitoring, Logging & Error Tracking

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Strategie für:
- **Logging** - Zentrales Logging aller Anwendungen
- **Monitoring** - Health Checks und Metriken
- **Error Tracking** - Erfassung und Benachrichtigung bei Fehlern

---

## 📝 Logging Strategy

### Log-Level

| Level | Verwendung | Beispiel |
|-------|------------|----------|
| DEBUG | Entwicklungs-Debugging | SQL Queries, Variable States |
| INFO | Normale Betriebsereignisse | Server Start, User Login |
| WARNING | Ungewöhnliche aber erwartete Events | Rate Limiting, Deprecated API |
| ERROR | Fehler die behandelt wurden | 500 Internal Server Error |
| CRITICAL | Kritische Systemfehler | Datenbank Verbindung verloren |

### Log-Format (JSON)

```json
{
  "timestamp": "2026-10-14T10:30:00Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Server started on port 8011",
  "extra": {
    "port": 8011,
    "host": "0.0.0.0"
  }
}
```

### Implementierung in FastAPI

```python
# app/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger("wasteland")
    logger.setLevel(logging.INFO)
    
    # JSON Handler für Production
    json_handler = logging.StreamHandler(sys.stdout)
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    json_handler.setFormatter(json_formatter)
    
    # Text Handler für Development
    text_handler = logging.StreamHandler(sys.stdout)
    text_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    text_handler.setFormatter(text_formatter)
    
    # Environment bestimmen
    import os
    if os.getenv("ENVIRONMENT") == "production":
        logger.addHandler(json_handler)
    else:
        logger.addHandler(text_handler)
    
    return logger

# In main.py
from app.logging_config import setup_logging
logger = setup_logging()
```

### Log-Rotation (Logrotate)

```bash
# /etc/logrotate.d/wasteland
/opt/wasteland/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 wasteland wasteland
    postrotate
        systemctl reload wasteland
    endscript
}
```

---

## 🏥 Health Checks

### Liveness Probe (Überlebt der Prozess?)

```python
# app/main.py - Health Endpoint
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

@app.get("/health")
async def health_check():
    """Liveness Probe - Prüft ob Server läuft"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.6"
    }

@app.get("/health/ready")
async def readiness_check():
    """Readiness Probe - Prüft ob alle Dependencies verfügbar sind"""
    try:
        # Datenbank Verbindung testen
        session = get_session()
        session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        session.close()
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, 503
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health/ready')" || exit 1
```

### nginx Health Check

```nginx
# /etc/nginx/conf.d/health.conf
server {
    listen 8080;
    
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

## 📈 Monitoring & Metriken

### Prometheus Metrics (optional)

```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Requests Counter
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Response Time Histogram
RESPONSE_TIME = Histogram(
    'http_response_duration_seconds',
    'HTTP response duration',
    ['endpoint']
)

# Active Users Gauge
ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users'
)

# In FastAPI Middleware verwenden
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        endpoint = request.url.path
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        RESPONSE_TIME.labels(endpoint=endpoint).observe(duration)
        
        return response

# In main.py hinzufügen
app.add_middleware(MetricsMiddleware)
```

### Prometheus Scrap Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'wasteland'
    static_configs:
      - targets: ['wasteland:8011']
    metrics_path: '/metrics'
```

### Grafana Dashboard (optional)

JSON Dashboard Export für Grafana:
- HTTP Request Rate
- Response Time P95/P99
- Error Rate (4xx, 5xx)
- Active Users
- Database Connection Pool

---

## 🚨 Error Tracking (Sentry)

### Sentry Integration

```python
# app/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SQLAlchemyIntegration

def init_sentry(dsn: str):
    sentry_sdk.init(
        dsn=dsn,
        environment="production",  # oder "development"
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        integrations=[
            FastApiIntegration(),
            SQLAlchemyIntegration(),
        ],
    )

# In main.py
import os
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    init_sentry(SENTRY_DSN)
```

### Custom Error Handler

```python
# app/error_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import sentry_sdk

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fängt alle nicht behandelten Exceptions"""
    # Error in Sentry reporten
    sentry_sdk.capture_exception(exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error_id": sentry_sdk.get_last_event_id()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Fängt HTTP Exceptions (4xx)"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### Error Benachrichtigung (Webhook)

```python
# Bei kritischen Fehlern: Slack/Teams Webhook
import requests

def notify_slack(error_message: str, error_id: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "text": f"🚨 Critical Error in Wasteland\n{error_message}\nError ID: {error_id}"
    }
    
    requests.post(webhook_url, json=payload)

# In global_exception_handler verwenden
if isinstance(exc, (DatabaseError, ConnectionError)):
    notify_slack(str(exc), sentry_sdk.get_last_event_id())
```

---

## 📊 Monitoring Stack Zusammenfassung

| Tool | Zweck | Status |
|------|-------|--------|
| **Python logging** | Application Logs | ✅ Implementiert |
| **Logrotate** | Log Rotation | ✅ Konfiguriert |
| **FastAPI /health** | Liveness Probe | ✅ Implementiert |
| **FastAPI /health/ready** | Readiness Probe | ✅ Implementiert |
| **Docker HEALTHCHECK** | Container Health | ✅ Konfiguriert |
| **Prometheus** | Metriken Sammeln | ⚠️ Optional |
| **Grafana** | Metriken Visualisierung | ⚠️ Optional |
| **Sentry** | Error Tracking | ⚠️ Optional |

---

## 🎯 Best Practices

1. **IMMER Logs schreiben** - Keine Exceptions still schlucken
2. **Strukturierte Logs** - JSON Format für bessere Analyse
3. **Log-Rotation** - Verhindert volle Festplatten
4. **Health Checks** - Regelmäßige Prüfungen aller Dependencies
5. **Error Tracking** - Proaktive Fehlererkennung bevor User betroffen sind
6. **Alerting** - Kritische Errors sofort melden (Slack, Email)

---

**Monitoring und Logging sind essentiell für einen stabilen Production-Betrieb!**
