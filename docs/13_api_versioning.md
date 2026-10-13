# 🔌 API Versioning & Backward Compatibility

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Strategie für API-Versionierung, Backward Compatibility und Deprecation Policies.

---

## 🎯 Warum API Versioning?

1. **Backward Compatibility:** Bestehende Clients funktionieren weiter
2. **Graduelle Migration:** Neue Features ohne Breaking Changes
3. **Multi-Version Support:** Alte und neue Versionen parallel betreiben
4. **Predictable Updates:** Clients wissen, welche API sie nutzen können

---

## 📐 Versionierungs-Strategien

### 1. URL Path Versioning (Empfohlen für Wasteland)

```
v1: /api/v1/province/
v2: /api/v2/province/
```

**Vorteile:**
- Klar und explizit
- Einfach zu routen
- Browser-caching friendly

**Nachteile:**
- URLs werden länger
- Mehrere Versionen müssen gepflegt werden

### 2. Header Versioning (Alternative)

```http
GET /api/province/
Accept: application/vnd.wasteland.v1+json
```

**Vorteile:**
- Saubere URLs
- Standardisiert (RFC 7231)

**Nachteile:**
- Schwerer zu debuggen
- Nicht browser-friendly

### 3. Query Parameter Versioning (Nicht empfohlen)

```
/api/province/?version=1
```

❌ **Nicht verwenden** - Verwirrend und schwer zu routen.

---

## 🏗️ Implementation in FastAPI

### Router-Struktur

```python
# app/api/v1/__init__.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])

from . import province, buildings, resources
```

```python
# app/api/v2/__init__.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v2", tags=["v2"])

from . import province, buildings, resources
```

### Haupt-Application

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router

app = FastAPI(
    title="Wasteland API",
    version="1.6.0",
    description="Post-apocalyptic browser strategy game"
)

# Alle Versionen mounten
app.include_router(v1_router)
app.include_router(v2_router)

# Default Redirect (optional)
@app.get("/api/")
async def api_root():
    return {
        "message": "Wasteland API",
        "version": "1.6.0",
        "available_versions": ["v1", "v2"],
        "docs": {
            "v1": "/api/v1/docs",
            "v2": "/api/v2/docs"
        }
    }
```

---

## 📝 Beispiel: Province API v1 vs v2

### v1 - Einfache Struktur

```python
# app/api/v1/province.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class ProvinceResponseV1(BaseModel):
    id: int
    name: str
    mips: int
    population: int

@router.get("/{province_id}", response_model=ProvinceResponseV1)
async def get_province(province_id: int):
    province = db.query(Province).get(province_id)
    return ProvinceResponseV1(
        id=province.id,
        name=province.name,
        mips=province.mips,
        population=province.population
    )
```

### v2 - Erweiterte Struktur

```python
# app/api/v2/province.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class BuildingSummary(BaseModel):
    id: int
    name: str
    level: int

class ResourceStockpile(BaseModel):
    resource_id: int
    name: str
    quantity: int

class ProvinceResponseV2(BaseModel):
    id: int
    name: str
    mips: int
    population: int
    
    # Neue Felder in v2
    buildings: List[BuildingSummary] = []
    resources: List[ResourceStockpile] = []
    terrain_type: str
    climate: Optional[str]
    last_tick: str
    
    # Metadaten
    can_build: bool = True
    max_population: int

@router.get("/{province_id}", response_model=ProvinceResponseV2)
async def get_province(province_id: int):
    province = db.query(Province).get(province_id)
    
    # Erweiterte Daten laden
    buildings = db.query(Building).filter_by(province_id=province.id).all()
    resources = db.query(ResourceStockpile).filter_by(province_id=province.id).all()
    
    return ProvinceResponseV2(
        id=province.id,
        name=province.name,
        mips=province.mips,
        population=province.population,
        buildings=[BuildingSummary(id=b.id, name=b.name, level=b.level) for b in buildings],
        resources=[ResourceStockpile(r.resource_id, r.name, r.quantity) for r in resources],
        terrain_type=province.terrain.type,
        climate=province.climate,
        last_tick=province.last_tick.isoformat() if province.last_tick else None
    )
```

---

## 🔄 Migration Guide: v1 → v2

### Schritt 1: Neue Endpunkte in v2 erstellen
- Alle v1 Endpunkte unverändert lassen
- Neue, erweiterte Version in v2 implementieren

### Schritt 2: Deprecation Header setzen
```python
from fastapi import Response

@router.get("/{province_id}", response_model=ProvinceResponseV1)
async def get_province_v1(province_id: int, response: Response):
    # Deprecation Warning setzen
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2027-01-01T00:00:00Z"
    response.headers["Link"] = '<http://localhost:8011/api/v2/province/{province_id}>; rel="successor-version"'
    
    province = db.query(Province).get(province_id)
    return ProvinceResponseV1(...)
```

### Schritt 3: Clients migrieren lassen
- Dokumentation bereitstellen (Migration Guide)
- Parallelbetrieb für 6-12 Monate
- Nach Sunset-Datum v1 deprecated

---

## 📋 Deprecation Policy

### Version Lifecycle

| Phase | Dauer | Status |
|-------|-------|--------|
| **Active** | Unbegrenzt | Voll unterstützt, neue Features |
| **Maintenance** | 6 Monate nach Sunset | Nur Bugfixes, keine neuen Features |
| **Deprecated** | 3 Monate nach Sunset | Nur kritische Security Fixes |
| **Retired** | Nach Sunset + 9 Monate | Endgültig abgeschaltet |

### Beispiel Timeline für v1:

```
2026-10-14: v2 released (parallel zu v1)
2027-04-14: v1 deprecate (6 Monate nach v2 Release)
            → Deprecation Header setzen
            → Migration Guide veröffentlichen
2027-07-14: v1 sunset (3 Monate nach Deprecation)
            → Keine neuen Requests mehr akzeptiert
            → 410 Gone zurückgeben
```

---

## 🔍 Client Version Detection

### Header-basiert (empfohlen)

```python
# app/middleware/version_detection.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class APIVersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Version aus Header extrahieren
        api_version = request.headers.get("X-API-Version", "v1")
        
        # Validieren
        if api_version not in ["v1", "v2"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {api_version}. Supported: v1, v2"
            )
        
        # In Request State speichern (für Router)
        request.state.api_version = api_version
        
        response = await call_next(request)
        
        # Version im Response Header setzen
        response.headers["X-API-Version"] = api_version
        
        return response

# In main.py
app.add_middleware(APIVersionMiddleware)
```

### URL-basiert (automatisch durch Router Prefix)

```python
# /api/v1/province/ → v1
# /api/v2/province/ → v2
```

---

## 📊 Breaking vs Non-Breaking Changes

### ✅ Non-Breaking (keine neue Version nötig)
- Neue Endpunkte hinzufügen
- Neue Query Parameter hinzufügen
- Neue Response Felder hinzufügen
- Error Messages verbessern

### ❌ Breaking (neue Version nötig)
- Bestehende Endpunkte umbenennen/entfernen
- Request/Response Schema ändern (Felder entfernen/umbenennen)
- Authentication Method ändern
- Rate Limits drastisch reduzieren

---

## 🧪 Testing API Versionen

### Parallel Tests für v1 und v2

```python
# tests/api/test_versioning.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_v1_province_endpoint(client):
    """Testet v1 Province Endpoint"""
    response = client.get("/api/v1/province/1")
    assert response.status_code == 200
    
    data = response.json()
    # v1 hat nur Grundfelder
    assert "id" in data
    assert "name" in data
    assert "mips" in data
    
    # v1 hat KEINE erweiterten Felder
    assert "buildings" not in data
    assert "resources" not in data

def test_v2_province_endpoint(client):
    """Testet v2 Province Endpoint"""
    response = client.get("/api/v2/province/1")
    assert response.status_code == 200
    
    data = response.json()
    # v2 hat alle v1 Felder + erweiterte
    assert "id" in data
    assert "name" in data
    assert "buildings" in data  # Neu in v2
    assert "resources" in data  # Neu in v2

def test_deprecation_header_v1(client):
    """Testet Deprecation Header auf v1"""
    response = client.get("/api/v1/province/1")
    
    # v1 sollte Deprecation Header haben (wenn deprecated)
    assert "Deprecation" in response.headers or response.status_code == 200

def test_unsupported_version(client):
    """Testet unsupported API Version"""
    response = client.get("/api/v99/province/1")
    assert response.status_code == 400
    assert "Unsupported API version" in response.json()["detail"]
```

---

## 📚 Dokumentation

### API Docs pro Version

Jede Version hat eigene Swagger/OpenAPI Docs:
- v1: http://localhost:8011/api/v1/docs
- v2: http://localhost:8011/api/v2/docs

### Migration Guide Dokument erstellen

```markdown
# docs/API_MIGRATION_v1_to_v2.md

## Zusammenfassung
v2 erweitert Province Endpoint um Gebäude und Ressourcen Daten.

## Änderungen v1 → v2

### Response Schema
- NEU: `buildings` - Liste aller Gebäude in der Provinz
- NEU: `resources` - Aktuelle Ressourcen-Vorräte
- NEU: `terrain_type` - Terrain-Typ der Provinz
- NEU: `climate` - Klima-Boni

### Breaking Changes
- Keine! v2 ist backward compatible zu v1 (alle v1 Felder vorhanden)

## Migration Steps
1. Ersetze `/api/v1/province/` mit `/api/v2/province/`
2. Verwende neue Felder `buildings` und `resources` statt separater API Calls
3. Optional: Verwende `can_build` Feld für UI-Feedback

## Sunset Datum
v1 wird am 2027-07-14 abgeschaltet. Bis dahin parallel betreiben.
```

---

## 🎯 Best Practices

1. **IMMER backward compatible bleiben** - Alte Clients nicht brechen
2. **Deprecation Header setzen** - Clients wissen, dass sie migrieren sollen
3. **Parallelbetrieb 6-12 Monate** - Genug Zeit für Migration
4. **Dokumentation aktualisieren** - Migration Guide bereitstellen
5. **Automated Testing** - Alle Versionen parallel testen
6. **Monitoring** - API Usage pro Version tracken

---

## 📊 API Usage Monitoring

```python
# app/middleware/api_usage_tracking.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

class APIUsageTracking(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Version extrahieren (aus URL oder Header)
        api_version = "unknown"
        if "/api/v1/" in request.url.path:
            api_version = "v1"
        elif "/api/v2/" in request.url.path:
            api_version = "v2"
        
        # Usage tracken (in Datenbank oder Logging)
        logger.info(f"API: {request.method} {api_version} {request.url.path} "
                   f"{response.status_code} {duration:.3f}s")
        
        return response

app.add_middleware(APIUsageTracking)
```

---

**API Versioning stellt sicher, dass neue Features eingeführt werden können, ohne bestehende Clients zu brechen!**
