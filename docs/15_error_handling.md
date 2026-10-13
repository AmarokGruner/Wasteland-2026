# 🛡️ Error Handling Patterns & Custom Exceptions

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Strategie für Error Handling, Custom Exceptions und User-friendly Error Messages im Wasteland Backend.

---

## 🎯 Ziele

1. **Konsistente Error Responses** - Immer gleiches Format
2. **User-friendly Messages** - Klare Fehlermeldungen für Spieler
3. **Detailed Logging** - Technische Details für Debugging
4. **Security** - Keine sensiblen Informationen leaken
5. **Graceful Degradation** - System bleibt stabil bei Fehlern

---

## 📐 Error Response Format

### Standardisiertes Error Schema

```json
{
  "error": {
    "code": "BUILDING_COST_INSUFFICIENT",
    "message": "Nicht genug MIPS zum Bauen dieses Gebäudes",
    "details": {
      "required": 150,
      "available": 100,
      "building_id": 42
    },
    "timestamp": "2026-10-14T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### HTTP Status Codes

| Code | Verwendung | Beispiel |
|------|------------|----------|
| 400 | Bad Request | Ungültige Eingabedaten |
| 401 | Unauthorized | Nicht authentifiziert |
| 403 | Forbidden | Keine Berechtigung |
| 404 | Not Found | Ressource existiert nicht |
| 409 | Conflict | Ressourcen-Konflikt (z.B. Gebäude existiert bereits) |
| 422 | Validation Error | Pydantic Validierungsfehler |
| 429 | Too Many Requests | Rate Limiting aktiv |
| 500 | Internal Server Error | Unvorhergesehener Fehler |

---

## 🏗️ Custom Exception Hierarchy

### Exception Classes

```python
# app/exceptions/base.py
from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class WastelandException(HTTPException):
    """Basis-Klasse für alle Wasteland Exceptions"""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": self.details
            }
        )

class WastelandClientError(WastelandException):
    """Basis für Client-Fehler (4xx)"""
    
    def __init__(self, code: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class WastelandServerError(WastelandException):
    """Basis für Server-Fehler (5xx)"""
    
    def __init__(self, code: str, message: str = "Interner Serverfehler", details: Optional[Dict] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )
```

### Spezifische Exceptions

```python
# app/exceptions/game_exceptions.py
from app.exceptions.base import WastelandClientError, WastelandServerError

# === Client Errors (4xx) ===

class InsufficientResourcesError(WastelandClientError):
    """Nicht genug Ressourcen für Aktion"""
    
    def __init__(self, resource_name: str, required: int, available: int):
        super().__init__(
            code="INSUFFICIENT_RESOURCES",
            message=f"Nicht genug {resource_name} verfügbar",
            details={
                "resource": resource_name,
                "required": required,
                "available": available,
                "deficit": required - available
            }
        )

class BuildingCostInsufficientError(WastelandClientError):
    """Nicht genug MIPS für Gebäude-Bau"""
    
    def __init__(self, building_name: str, required: int, available: int):
        super().__init__(
            code="BUILDING_COST_INSUFFICIENT",
            message=f"Nicht genug MIPS zum Bauen von {building_name}",
            details={
                "building": building_name,
                "required": required,
                "available": available
            }
        )

class ProvinceNotFoundError(WastelandClientError):
    """Provinz nicht gefunden"""
    
    def __init__(self, province_id: int):
        super().__init__(
            code="PROVINCE_NOT_FOUND",
            message=f"Provinz mit ID {province_id} nicht gefunden",
            details={"province_id": province_id}
        )

class BuildingAlreadyExistsError(WastelandClientError):
    """Gebäude existiert bereits in Provinz"""
    
    def __init__(self, building_name: str, province_id: int):
        super().__init__(
            code="BUILDING_ALREADY_EXISTS",
            message=f"Gebäude '{building_name}' existiert bereits in dieser Provinz",
            details={
                "building": building_name,
                "province_id": province_id
            }
        )

class InvalidBuildingTypeError(WastelandClientError):
    """Ungültiger Gebäude-Typ"""
    
    def __init__(self, building_type: str):
        super().__init__(
            code="INVALID_BUILDING_TYPE",
            message=f"Ungültiger Gebäude-Typ: {building_type}",
            details={"building_type": building_type}
        )

class PlayerNotAuthorizedError(WastelandClientError):
    """Spieler nicht berechtigt für Aktion"""
    
    def __init__(self, action: str, province_id: int):
        super().__init__(
            code="PLAYER_NOT_AUTHORIZED",
            message=f"Nicht berechtigt für {action} in Provinz {province_id}",
            details={
                "action": action,
                "province_id": province_id
            }
        )

class ResourceStockpileFullError(WastelandClientError):
    """Lagerkapazität erreicht"""
    
    def __init__(self, resource_name: str, capacity: int, current: int):
        super().__init__(
            code="STOCKPILE_FULL",
            message=f"Lager für {resource_name} ist voll",
            details={
                "resource": resource_name,
                "capacity": capacity,
                "current": current
            }
        )

class TickInProgressError(WastelandClientError):
    """Server-Tick läuft bereits"""
    
    def __init__(self):
        super().__init__(
            code="TICK_IN_PROGRESS",
            message="Server-Tick läuft bereits, bitte warten"
        )

# === Server Errors (5xx) ===

class DatabaseConnectionError(WastelandServerError):
    """Datenbank-Verbindungsfehler"""
    
    def __init__(self):
        super().__init__(
            code="DATABASE_CONNECTION_ERROR",
            message="Datenbank-Verbindung fehlgeschlagen"
        )

class ExternalServiceError(WastelandServerError):
    """Externer Dienst nicht erreichbar"""
    
    def __init__(self, service_name: str):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=f"Dienst '{service_name}' nicht erreichbar"
        )

class UnexpectedError(WastelandServerError):
    """Unvorhergesehener Fehler"""
    
    def __init__(self, original_exception: Exception):
        super().__init__(
            code="UNEXPECTED_ERROR",
            message="Ein unerwarteter Fehler ist aufgetreten"
        )
```

---

## 🔧 Global Exception Handler

### FastAPI Exception Handlers

```python
# app/exception_handlers.py
from fastapi import Request, HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
import traceback
import uuid
import logging

logger = logging.getLogger("wasteland")

async def wasteland_exception_handler(request: Request, exc: Exception):
    """Globaler Exception Handler für Wasteland Exceptions"""
    
    # Request ID generieren (für Tracking)
    request_id = str(uuid.uuid4())
    
    # Exception classifizieren
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_code = exc.detail.get("code", "UNKNOWN_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR"
        error_message = exc.detail.get("message", str(exc)) if isinstance(exc.detail, dict) else str(exc)
        error_details = exc.detail.get("details", {}) if isinstance(exc.detail, dict) else {}
        
        # Client Errors (4xx) loggen als warning
        if 400 <= status_code < 500:
            logger.warning(
                f"Client Error [{request_id}]: {error_code} - {error_message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": self.client_host(request) if hasattr(self, 'client_host') else None
                }
            )
        # Server Errors (5xx) loggen als error mit Stacktrace
        else:
            logger.error(
                f"Server Error [{request_id}]: {error_code} - {error_message}",
                exc_info=exc,
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
    
    else:
        # Unhandled Exception
        status_code = 500
        error_code = "UNEXPECTED_ERROR"
        error_message = "Interner Serverfehler"
        error_details = {}
        
        logger.error(
            f"Unhandled Exception [{request_id}]: {type(exc).__name__}: {str(exc)}",
            exc_info=exc,
            extra={
                "path": request.url.path,
                "method": request.method
            }
        )
    
    # User-friendly Response zurückgeben (keine sensiblen Details)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": error_message,
                "details": error_details if status_code < 500 else {},  # Keine Details bei 5xx
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        headers={
            "X-Request-ID": request_id
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler für Pydantic Validation Errors"""
    
    request_id = str(uuid.uuid4())
    
    # Validation Errors extrahieren
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation Error [{request_id}]: {len(errors)} Felder ungültig",
        extra={"path": request.url.path}
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Ungültige Eingabedaten",
                "details": {
                    "errors": errors
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        headers={
            "X-Request-ID": request_id
        }
    )

# In main.py registrieren:
from fastapi import FastAPI
app = FastAPI()

app.add_exception_handler(Exception, wasteland_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

---

## 📝 Exception Usage in Endpoints

### Beispiel: Building Endpoint

```python
# app/api/v1/buildings.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/{province_id}/build")
async def build_building(
    province_id: int,
    building_type: str,
    db: Session = Depends(get_db),
    current_user: Player = Depends(get_current_player)
):
    """Gebäude in Provinz bauen"""
    
    # 1. Provinz existiert?
    province = db.query(Province).get(province_id)
    if not province:
        raise ProvinceNotFoundError(province_id)
    
    # 2. Spieler Besitzer der Provinz?
    if province.owner_id != current_user.id:
        raise PlayerNotAuthorizedError("building", province_id)
    
    # 3. Gebäude-Typ gültig?
    building_type_obj = db.query(BuildingType).filter_by(name=building_type).first()
    if not building_type_obj:
        raise InvalidBuildingTypeError(building_type)
    
    # 4. MIPS ausreichend?
    if province.mips < building_type_obj.baukosten_mips:
        raise BuildingCostInsufficientError(
            building_name=building_type_obj.name,
            required=building_type_obj.baukosten_mips,
            available=province.mips
        )
    
    # 5. Gebäude existiert bereits? (einmalige Gebäude)
    if building_type_obj.unique_gebaeude:
        existing = db.query(BuildingInstance).filter_by(
            province_id=province_id,
            gebaeude_typ_id=building_type_obj.id
        ).first()
        if existing:
            raise BuildingAlreadyExistsError(building_type_obj.name, province_id)
    
    # 6. Gebäude bauen
    new_building = BuildingInstance(
        province_id=province_id,
        gebaeude_typ_id=building_type_obj.id,
        level=1
    )
    db.add(new_building)
    
    # MIPS abziehen
    province.mips -= building_type_obj.baukosten_mips
    
    db.commit()
    
    return {
        "message": f"{building_type_obj.name} erfolgreich gebaut",
        "building_id": new_building.id,
        "remaining_mips": province.mips
    }
```

---

## 🧪 Testing Exception Handling

### Unit Tests für Exceptions

```python
# tests/test_exceptions.py
import pytest
from app.exceptions.game_exceptions import (
    InsufficientResourcesError,
    BuildingCostInsufficientError,
    ProvinceNotFoundError
)

def test_insufficient_resources_error():
    """Testet InsufficientResourcesError"""
    exc = InsufficientResourcesError("wood", required=100, available=50)
    
    assert exc.code == "INSUFFICIENT_RESOURCES"
    assert exc.status_code == 400
    assert "Nicht genug wood verfügbar" in exc.detail["message"]
    assert exc.detail["details"]["required"] == 100
    assert exc.detail["details"]["available"] == 50

def test_building_cost_insufficient_error():
    """Testet BuildingCostInsufficientError"""
    exc = BuildingCostInsufficientError("Farm", required=150, available=100)
    
    assert exc.code == "BUILDING_COST_INSUFFICIENT"
    assert exc.status_code == 400
    assert "Nicht genug MIPS" in exc.detail["message"]

def test_province_not_found_error():
    """Testet ProvinceNotFoundError"""
    exc = ProvinceNotFoundError(province_id=999)
    
    assert exc.code == "PROVINCE_NOT_FOUND"
    assert exc.status_code == 404
    assert "999" in exc.detail["message"]

def test_error_details_not_exposed_for_5xx():
    """Testet dass Details bei 5xx nicht exposed werden"""
    from app.exceptions.game_exceptions import DatabaseConnectionError
    
    exc = DatabaseConnectionError()
    
    assert exc.status_code == 500
    # Details sollten leer sein bei Server Errors
    assert exc.detail["details"] == {}
```

### Integration Tests für Exception Handler

```python
# tests/api/test_exception_handling.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_province_not_found(client):
    """Testet 404 für nicht existierende Provinz"""
    response = client.get("/api/v1/province/9999")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "PROVINCE_NOT_FOUND"
    assert "request_id" in data["error"]
    
    # Request ID im Header
    assert "X-Request-ID" in response.headers

def test_validation_error(client):
    """Testet 422 für ungültige Eingabedaten"""
    response = client.post(
        "/api/v1/province/1/build",
        json={"building_type": "invalid_type_xyz"}
    )
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]["errors"]) > 0

def test_server_error_no_details(client):
    """Testet dass Server Errors keine Details exposed"""
    # Simuliere Server Error (z.B. durch falsche Config)
    response = client.get("/api/v1/province/1")  # Angenommen, das löst 500 aus
    
    if response.status_code == 500:
        data = response.json()
        
        # Keine sensiblen Details bei 5xx
        assert data["error"]["details"] == {}
```

---

## 📊 Error Monitoring & Alerting

### Error Metrics (Prometheus)

```python
# app/middleware/error_tracking.py
from prometheus_client import Counter, Histogram
import time

ERROR_COUNT = Counter(
    'wasteland_errors_total',
    'Total number of errors',
    ['code', 'endpoint', 'method']
)

ERROR_DURATION = Histogram(
    'wasteland_error_duration_seconds',
    'Duration of error handling',
    ['code']
)

class ErrorTrackingMiddleware:
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Error tracken
        if response.status_code >= 400:
            error_code = "unknown"
            
            # Error Code aus Response extrahieren
            if response.status_code == 422:
                error_code = "validation"
            elif 400 <= response.status_code < 500:
                error_code = "client"
            else:
                error_code = "server"
            
            ERROR_COUNT.labels(
                code=error_code,
                endpoint=request.url.path,
                method=request.method
            ).inc()
            
            duration = time.time() - start_time
            ERROR_DURATION.labels(code=error_code).observe(duration)
        
        return response

app.add_middleware(ErrorTrackingMiddleware)
```

---

## 🎯 Best Practices

1. **IMMER Request ID zurückgeben** - Für Tracking und Debugging
2. **Keine sensiblen Details bei 5xx** - Security first
3. **Client Errors loggen als warning** - Normaler Betrieb
4. **Server Errors mit Stacktrace loggen** - Für Debugging
5. **User-friendly Messages** - Klare Fehlermeldungen für Spieler
6. **Consistent Error Format** - Immer gleiches JSON Schema

---

**Robustes Error Handling stellt sicher, dass Fehler klar kommuniziert werden und das System stabil bleibt!**
