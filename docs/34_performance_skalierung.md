# ⚡ Performance & Skalierung

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt Performance-Ziele, Skalierungsgrenzen und Optimierungsstrategien für das Spiel.

---

## 🎯 Ziele

1. **Performance-Ziele** - API Response Time < 100ms, Datenbank-Queries < 50ms
2. **Skalierungsgrenzen** - Max Spieler, Provinzen, Gebäude pro Welt
3. **Optimierung** - Database Indexing, Caching, Query-Optimierung
4. **Monitoring** - Performance-Metriken tracken

---

## 📊 Performance-Ziele & Benchmarks

### API Response Times

| Endpoint-Typ | Ziel (P50) | Ziel (P95) | Limit (P99) |
|--------------|-----------|-----------|------------|
| **GET (Lesen)** | < 50ms | < 100ms | < 200ms |
| **POST (Schreiben)** | < 100ms | < 200ms | < 500ms |
| **WebSocket Broadcast** | < 10ms | < 50ms | < 100ms |
| **Suche (FTS5)** | < 30ms | < 100ms | < 200ms |

### Datenbank Performance

| Operation | Ziel (P50) | Ziel (P95) |
|-----------|-----------|-----------|
| **Simple SELECT** | < 5ms | < 20ms |
| **JOIN Query** | < 20ms | < 50ms |
| **INSERT/UPDATE** | < 10ms | < 30ms |
| **Full Table Scan** | < 100ms | < 500ms |

### Server Ressourcen

| Metrik | Ziel | Warnung | Kritisch |
|--------|------|---------|----------|
| **CPU Usage** | < 50% | > 70% | > 90% |
| **Memory Usage** | < 512 MB | > 768 MB | > 1024 MB |
| **Database Size** | < 500 MB | > 1 GB | > 2 GB |
| **Active Connections** | < 50 | > 100 | > 200 |

---

## 🏗️ Skalierungsgrenzen

### Welt-Größen Limits

```python
# app/config.py

class ScalingLimits:
    # Max Spieler pro Welt
    MAX_SPIELER_PRO_WELT = 100
    
    # Max Provinzen pro Welt
    MAX_PROVINZEN_PRO_WELT = 50
    
    # Max Gebäude pro Provinz
    MAX_GEBAEUDE_PRO_PROVINZ = 100
    
    # Max Einheiten pro Provinz
    MAX_EINHEITEN_PRO_PROVINZ = 50
    
    # Max API Requests pro Minute (pro User)
    MAX_API_REQUESTS_PRO_MINUTE = 60
    
    # Max WebSocket Connections pro Server
    MAX_WEBSOCKET_CONNECTIONS = 200
    
    # Max Datenbank-Größe (MB)
    MAX_DATABASE_SIZE_MB = 1024
    
    # Max File Upload Size (MB)
    MAX_UPLOAD_SIZE_MB = 10

scaling_limits = ScalingLimits()
```

### Performance-Checks pro Tick

```python
# app/services/performance_monitor.py

class PerformanceMonitor:
    def __init__(self):
        self.query_times = []
        self.api_response_times = []
    
    def check_world_limits(self) -> dict:
        """Prüfen ob Welt-Grenzen erreicht sind"""
        
        from app.models import User, Province, Building, Unit
        
        spieler_anzahl = db.query(User).count()
        provinz_anzahl = db.query(Province).count()
        
        gebaeude_pro_provinz = {}
        einheiten_pro_provinz = {}
        
        # Gebäude pro Provinz zählen
        gebaeude = db.query(Building).all()
        
        for gebaeude in gebaeude:
            pid = gebaeude.province_id
            
            if pid not in gebaeude_pro_provinz:
                gebaeude_pro_provinz[pid] = 0
            
            gebaeude_pro_provinz[pid] += 1
        
        # Einheiten pro Provinz zählen
        einheiten = db.query(Unit).all()
        
        for einheit in einheiten:
            pid = einheit.province_id
            
            if pid not in einheiten_pro_provinz:
                einheiten_pro_provinz[pid] = 0
            
            einheiten_pro_provinz[pid] += 1
        
        warnings = []
        
        # Grenzen prüfen
        if spieler_anzahl >= scaling_limits.MAX_SPIELER_PRO_WELT * 0.8:
            warnings.append({
                "type": "spieler_nahe_grenze",
                "message": f"Spieler-Anzahl: {spieler_anzahl}/{scaling_limits.MAX_SPIELER_PRO_WELT}",
                "severity": "warning"
            })
        
        if provinz_anzahl >= scaling_limits.MAX_PROVINZEN_PRO_WELT * 0.8:
            warnings.append({
                "type": "provinzen_nahe_grenze",
                "message": f"Provinz-Anzahl: {provinz_anzahl}/{scaling_limits.MAX_PROVINZEN_PRO_WELT}",
                "severity": "warning"
            })
        
        # Gebäude pro Provinz prüfen
        for pid, count in gebaeude_pro_provinz.items():
            if count >= scaling_limits.MAX_GEBAEUDE_PRO_PROVINZ * 0.8:
                warnings.append({
                    "type": "gebaeude_nahe_grenze",
                    "province_id": pid,
                    "message": f"Gebäude in Provinz {pid}: {count}/{scaling_limits.MAX_GEBAEUDE_PRO_PROVINZ}",
                    "severity": "warning"
                })
        
        # Einheiten pro Provinz prüfen
        for pid, count in einheiten_pro_provinz.items():
            if count >= scaling_limits.MAX_EINHEITEN_PRO_PROVINZ * 0.8:
                warnings.append({
                    "type": "einheiten_nahe_grenze",
                    "province_id": pid,
                    "message": f"Einheiten in Provinz {pid}: {count}/{scaling_limits.MAX_EINHEITEN_PRO_PROVINZ}",
                    "severity": "warning"
                })
        
        return {
            "spieler_anzahl": spieler_anzahl,
            "provinz_anzahl": provinz_anzahl,
            "warnings": warnings,
            "limits_reached": len([w for w in warnings if w["severity"] == "critical"]) > 0
        }
    
    def check_database_size(self) -> dict:
        """Datenbank-Größe prüfen"""
        
        import os
        
        db_path = "verbrannte_zone.db"
        
        if not os.path.exists(db_path):
            return {"error": "Datenbank nicht gefunden"}
        
        groesse_mb = os.path.getsize(db_path) / (1024 * 1024)
        
        warnings = []
        
        if groesse_mb >= scaling_limits.MAX_DATABASE_SIZE_MB * 0.8:
            warnings.append({
                "type": "datenbank_gross",
                "message": f"Datenbank-Größe: {groesse_mb:.2f} MB",
                "severity": "warning"
            })
        
        return {
            "groesse_mb": groesse_mb,
            "max_mb": scaling_limits.MAX_DATABASE_SIZE_MB,
            "warnings": warnings
        }
    
    def check_server_resources(self) -> dict:
        """Server-Ressourcen prüfen"""
        
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        warnings = []
        
        if cpu_percent >= 90:
            warnings.append({
                "type": "cpu_kritisch",
                "message": f"CPU Usage: {cpu_percent}%",
                "severity": "critical"
            })
        elif cpu_percent >= 70:
            warnings.append({
                "type": "cpu_warnung",
                "message": f"CPU Usage: {cpu_percent}%",
                "severity": "warning"
            })
        
        memory_mb = memory.used / (1024 * 1024)
        
        if memory_mb >= 1024:
            warnings.append({
                "type": "memory_kritisch",
                "message": f"Memory Usage: {memory_mb:.2f} MB",
                "severity": "critical"
            })
        elif memory_mb >= 768:
            warnings.append({
                "type": "memory_warnung",
                "message": f"Memory Usage: {memory_mb:.2f} MB",
                "severity": "warning"
            })
        
        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "memory_total_mb": memory.total / (1024 * 1024),
            "warnings": warnings
        }

# Singleton
performance_monitor = PerformanceMonitor()
```

---

## 🔧 Database Optimization

### Indexing Strategy

```python
# app/models.py - Datenbank Indizes

# Wichtige Indizes für Performance
def create_database_indexes():
    """Performance-optimierte Indizes erstellen"""
    
    from sqlalchemy import index
    
    # Häufig abgefragte Spalten indizieren
    indexes = [
        # User-Tabellen
        index("idx_users_email", "users", "email"),
        index("idx_users_username", "users", "username"),
        
        # Province-Tabellen
        index("idx_provinzen_owner", "provinzen", "owner_id"),
        index("idx_provinzen_coords", "provinzen", "x", "y"),
        
        # Building-Tabellen
        index("idx_gebaeude_provinz", "provinz_gebaeude", "province_id"),
        index("idx_gebaeude_typ", "provinz_gebaeude", "gebaeude_typ_id"),
        
        # Unit-Tabellen
        index("idx_einheiten_provinz", "provinz_einheiten", "province_id"),
        index("idx_einheiten_typ", "provinz_einheiten", "einheit_typ_id"),
        
        # Handel-Tabellen
        index("idx_handel_von", "handels_routen", "von_provinz_id"),
        index("idx_handel_ziel", "handels_routen", "ziel_provinz_id"),
        
        # Diplomatie-Tabellen
        index("idx_diplomatie_von", "diplomatie", "von_provinz_id"),
        index("idx_diplomatie_ziel", "diplomatie", "ziel_provinz_id"),
        
        # Kampf-Tabellen
        index("idx_kampf_angreifer", "kampf_logs", "angreifer_provinz_id"),
        index("idx_kampf_verteidiger", "kampf_logs", "verteidiger_provinz_id"),
    ]
    
    # Indizes erstellen (einmalig beim Start)
    engine = create_engine("sqlite:///verbrannte_zone.db")
    
    with engine.connect() as conn:
        for idx in indexes:
            try:
                conn.execute(idx.create())
            except Exception as e:
                print(f"Index creation warning: {e}")
        
        conn.commit()

# In main.py:
"""
@app.on_event("startup")
async def startup():
    create_database_indexes()
"""

# Helper: Query-Performance prüfen
def analyze_query_performance(query_string: str, params: dict = None) -> dict:
    """SQL-Query Performance analysieren (EXPLAIN QUERY PLAN)"""
    
    from sqlalchemy import text
    
    try:
        result = db.execute(text(f"EXPLAIN QUERY PLAN {query_string}"), params or {})
        
        plan = result.fetchall()
        
        # Scan-Typen prüfen (INDEX vs. SCAN)
        uses_index = any("INDEX" in str(row) for row in plan)
        
        return {
            "uses_index": uses_index,
            "plan": [str(row) for row in plan],
            "warning": "Kein Index verwendet!" if not uses_index else None
        }
    
    except Exception as e:
        return {"error": str(e)}

# Helper: Langsame Queries identifizieren
def identify_slow_queries(threshold_ms: int = 50) -> list:
    """Langsame Datenbank-Queries identifizieren"""
    
    # SQLite Query Time Tracking (vereinfacht)
    # In Production: Slow-Query-Log aktivieren
    
    slow_queries = []
    
    # Häufige langsame Patterns erkennen
    patterns = [
        "SELECT * FROM gebaeude_typen",  # Full Table Scan
        "SELECT * FROM ressourcen",       # Full Table Scan
        "JOIN ohne WHERE"                # Cartesian Product
    ]
    
    return slow_queries

# Helper: Datenbank aufräumen (VACUUM)
def vacuum_database():
    """SQLite VACUUM ausführen (Fragmentierung reduzieren)"""
    
    from sqlalchemy import text
    
    db.execute(text("VACUUM"))
    db.commit()
    
    print("✅ Datenbank optimiert (VACUUM)")

# Helper: Statistiken aktualisieren
def update_database_statistics():
    """SQLite Statistiken aktualisieren (ANALYZE)"""
    
    from sqlalchemy import text
    
    db.execute(text("ANALYZE"))
    db.commit()
    
    print("✅ Datenbank-Statistiken aktualisiert (ANALYZE)")
```

---

## 📡 API Endpunkte für Performance-Monitoring

### Performance Router

```python
# app/api/v1/performance.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/admin/performance/world-limits")
async def get_world_limits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Welt-Grenzen Status abrufen"""
    
    result = performance_monitor.check_world_limits()
    
    return result

@router.get("/admin/performance/database")
async def get_database_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Datenbank-Status abrufen"""
    
    result = performance_monitor.check_database_size()
    
    return result

@router.get("/admin/performance/server")
async def get_server_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Server-Ressourcen abrufen"""
    
    result = performance_monitor.check_server_resources()
    
    return result

@router.post("/admin/performance/vacuum")
async def vacuum_database_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Datenbank aufräumen (VACUUM)"""
    
    vacuum_database()
    
    return {"message": "Datenbank optimiert (VACUUM durchgeführt)"}

@router.post("/admin/performance/analyze")
async def analyze_database_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Datenbank-Statistiken aktualisieren (ANALYZE)"""
    
    update_database_statistics()
    
    return {"message": "Datenbank-Statistiken aktualisiert (ANALYZE durchgeführt)"}

@router.get("/admin/performance/query-plan")
async def analyze_query_plan(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Query-Plan analysieren"""
    
    result = analyze_query_performance(query)
    
    return result

@router.get("/admin/performance/summary")
async def get_performance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Gesamt-Performance-Zusammenfassung"""
    
    world_limits = performance_monitor.check_world_limits()
    database_status = performance_monitor.check_database_size()
    server_resources = performance_monitor.check_server_resources()
    
    return {
        "world_limits": world_limits,
        "database": database_status,
        "server": server_resources,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 🖥️ Client-Side Performance UI (JavaScript)

### Performance Dashboard

```javascript
// js/admin/performance-dashboard.js

class PerformanceDashboard {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Performance-Zusammenfassung laden
    async loadPerformanceSummary() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/performance/summary`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderSummary(data);
            }
        } catch (error) {
            console.error('Performance Summary Load Error:', error);
        }
    }

    // Performance-Dashboard rendern
    renderSummary(data) {
        const container = document.getElementById('performance-dashboard');
        
        if (!container) return;

        let html = '<h3>⚡ Performance-Monitoring</h3>';
        
        // Welt-Grenzen
        html += '<div class="world-limits">';
        html += '<h4>🌍 Welt-Grenzen</h4>';
        
        html += `<p>Spieler: ${data.world_limits.spieler_anzahl}</p>`;
        html += `<p>Provinzen: ${data.world_limits.provinz_anzahl}</p>`;
        
        if (data.world_limits.warnings.length > 0) {
            html += '<div class="warnings">';
            
            for (const warning of data.world_limits.warnings) {
                const color = warning.severity === 'critical' ? '#ff0000' : '#ff8c00';
                html += `<p style="color: ${color}">⚠️ ${warning.message}</p>`;
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        
        // Datenbank-Status
        html += '<div class="database-status">';
        html += '<h4>💾 Datenbank</h4>';
        
        html += `<p>Größe: ${data.database.groesse_mb.toFixed(2)} MB / ${data.database.max_mb} MB</p>`;
        
        if (data.database.warnings.length > 0) {
            html += '<div class="warnings">';
            
            for (const warning of data.database.warnings) {
                html += `<p style="color: #ff8c00">⚠️ ${warning.message}</p>`;
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        
        // Server-Ressourcen
        html += '<div class="server-resources">';
        html += '<h4>🖥️ Server-Ressourcen</h4>';
        
        html += `<p>CPU: ${data.server.cpu_percent}%</p>`;
        html += `<p>Memory: ${data.server.memory_mb.toFixed(2)} MB / ${data.server.memory_total_mb.toFixed(0)} MB</p>`;
        
        if (data.server.warnings.length > 0) {
            html += '<div class="warnings">';
            
            for (const warning of data.server.warnings) {
                const color = warning.severity === 'critical' ? '#ff0000' : '#ff8c00';
                html += `<p style="color: ${color}">⚠️ ${warning.message}</p>`;
            }
            
            html += '</div>';
        }
        
        html += '</div>';

        container.innerHTML = html;
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `performance-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        this.loadPerformanceSummary();
        
        // Periodisch aktualisieren (alle 60s)
        setInterval(() => {
            this.loadPerformanceSummary();
        }, 60000);
    }
}

// Singleton
const performance = new PerformanceDashboard();

export default performance;
```

---

## 🧪 Testing Performance-Monitoring

### Unit Tests

```python
# tests/services/test_performance_monitor.py
import pytest

def test_check_world_limits():
    """Testet Welt-Grenzen Prüfung"""
    
    from app.services.performance_monitor import performance_monitor
    
    result = performance_monitor.check_world_limits()
    
    assert "spieler_anzahl" in result
    assert "warnings" in result

def test_check_database_size():
    """Testet Datenbank-Größen Prüfung"""
    
    from app.services.performance_monitor import performance_monitor
    
    result = performance_monitor.check_database_size()
    
    assert "groesse_mb" in result

def test_check_server_resources():
    """Testet Server-Ressourcen Prüfung"""
    
    from app.services.performance_monitor import performance_monitor
    
    result = performance_monitor.check_server_resources()
    
    assert "cpu_percent" in result
    assert "memory_mb" in result

def test_analyze_query_performance():
    """Testet Query-Performance Analyse"""
    
    from app.services.performance_monitor import analyze_query_performance
    
    result = analyze_query_performance("SELECT * FROM users WHERE email = ?", {"email": "test@example.com"})
    
    assert "uses_index" in result

def test_vacuum_database():
    """Testet Datenbank VACUUM"""
    
    from app.services.performance_monitor import vacuum_database
    
    # Sollte keine Fehler werfen
    vacuum_database()

def test_update_statistics():
    """Testet Datenbank ANALYZE"""
    
    from app.services.performance_monitor import update_database_statistics
    
    # Sollte keine Fehler werfen
    update_database_statistics()

def test_scaling_limits_config():
    """Testet Skalierungsgrenzen Konfiguration"""
    
    from app.config import scaling_limits
    
    assert scaling_limits.MAX_SPIELER_PRO_WELT == 100
    assert scaling_limits.MAX_PROVINZEN_PRO_WELT == 50

def test_performance_summary():
    """Testet Performance-Zusammenfassung"""
    
    from app.api.v1.performance import get_performance_summary
    
    # Integrationstest mit TestClient
    pass
```

---

## 🎯 Best Practices

1. **Indizes setzen** - Häufig abgefragte Spalten indizieren
2. **VACUUM/ANALYZE** - Regelmäßig Datenbank optimieren
3. **Monitoring aktivieren** - CPU, Memory, DB-Größe tracken
4. **Grenzen warnen** - Bei 80% der Grenze warnen
5. **Query-Plans prüfen** - Langsame Queries identifizieren

---

**Performance-Monitoring ermöglicht Welt-Größen-Kontrolle, Datenbank-Optimierung und Server-Monitoring!**
