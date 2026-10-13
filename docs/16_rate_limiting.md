# 🔒 Rate Limiting & API Security

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Strategie für API-Ratenbegrenzung, Schutz vor Missbrauch und DDoS-Prävention.

---

## 🎯 Ziele

1. **Missbrauch verhindern** - Automatisierte Angriffe blockieren
2. **Server schützen** - Ressourcen schonen bei hoher Last
3. **Fair Use garantieren** - Alle Spieler gleich behandelt
4. **Legitime Nutzung ermöglichen** - Keine unnötigen Limits

---

## 📐 Rate Limiting Strategies

### 1. Per-User Rate Limiting (Empfohlen)

```python
# app/middleware/rate_limiter.py
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

class UserRateLimiter:
    def __init__(self):
        # user_id → [(timestamp, endpoint), ...]
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int, endpoint: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Prüft ob User noch Requests senden darf"""
        now = time.time()
        
        # Alte Einträge entfernen (> window_seconds)
        self.requests[user_id] = [
            (ts, ep) for ts, ep in self.requests[user_id]
            if now - ts < window_seconds
        ]
        
        # Zählen pro Endpoint
        endpoint_requests = sum(1 for ts, ep in self.requests[user_id] if ep == endpoint)
        
        if endpoint_requests >= max_requests:
            return False
        
        # Neuen Request tracken
        self.requests[user_id].append((now, endpoint))
        return True
    
    def get_remaining(self, user_id: int, endpoint: str) -> int:
        """Verbleibende Requests zählen"""
        now = time.time()
        endpoint_requests = sum(
            1 for ts, ep in self.requests[user_id]
            if now - ts < 60 and ep == endpoint
        )
        return max(0, 60 - endpoint_requests)

rate_limiter = UserRateLimiter()
```

### 2. Per-IP Rate Limiting (Fallback)

```python
class IPRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        now = time.time()
        
        self.requests[ip] = [
            ts for ts in self.requests[ip]
            if now - ts < window_seconds
        ]
        
        if len(self.requests[ip]) >= max_requests:
            return False
        
        self.requests[ip].append(now)
        return True

ip_rate_limiter = IPRateLimiter()
```

---

## 🔧 Implementation in FastAPI

### Rate Limit Middleware

```python
# app/middleware/rate_limiting.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # User ID aus Token extrahieren (wenn authentifiziert)
        user_id = None
        ip_address = self.get_client_ip(request)
        
        # Authorization Header prüfen
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Token decodieren (vereinfacht)
                user_id = self.extract_user_from_token(token)
            except:
                pass
        
        # Rate Limit prüfen
        endpoint = request.url.path
        
        if user_id:
            # Authentifizierte User: Striktere Limits pro Endpoint
            allowed = rate_limiter.is_allowed(user_id, endpoint)
            remaining = rate_limiter.get_remaining(user_id, endpoint)
        else:
            # Anonyme User: Weniger strikte Limits (globale IP-Limits)
            allowed = ip_rate_limiter.is_allowed(ip_address)
            remaining = max(0, 100 - len(ip_rate_limiter.requests.get(ip_address, [])))
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Zu viele Anfragen, bitte warten Sie einen Moment",
                    "retry_after": 60  # Sekunden
                }
            )
        
        response = await call_next(request)
        
        # Rate Limit Headers setzen
        if user_id:
            response.headers["X-RateLimit-Limit"] = "60"
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        else:
            response.headers["X-RateLimit-Limit"] = "100"
            response.headers["X-RateLimit-Remaining"] = str(max(0, 100 - len(ip_rate_limiter.requests.get(ip_address, []))))
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Client IP extrahieren (berücksichtigt Proxy)"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
    
    def extract_user_from_token(self, token: str) -> int:
        """User ID aus JWT Token extrahieren"""
        # Vereinfacht - in Production: pyjwt verwenden
        import jwt
        from app.config import SECRET_KEY
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")  # sub = user_id

app.add_middleware(RateLimitMiddleware)
```

---

## 📊 Verschiedene Limits pro Endpoint

### Endpoint-spezifische Konfiguration

```python
# app/config.py

class RateLimitConfig:
    # Anonyme User (nicht authentifiziert)
    ANONYMOUS_GLOBAL_LIMIT = 100      # Requests pro Minute global
    ANONYMOUS_LOGIN_LIMIT = 5         # Login-Versuche pro Minute
    
    # Authentifizierte User
    USER_GLOBAL_LIMIT = 60            # Requests pro Minute global
    USER_API_WRITE_LIMIT = 30         # Schreib-Operationen (POST/PUT/DELETE)
    USER_API_READ_LIMIT = 120         # Lese-Operationen (GET)
    
    # Spezielle Endpoints
    ENDPOINT_LIMITS = {
        "/auth/login": {"limit": 5, "window": 60},      # Login: Streng
        "/auth/register": {"limit": 3, "window": 300},   # Registration: Sehr streng
        "/province/build": {"limit": 10, "window": 60},  # Gebäude bauen: Moderat
        "/world/map": {"limit": 30, "window": 60},       # Weltkarte: Höher
    }

rate_limit_config = RateLimitConfig()
```

---

## 🛡️ Additional Security Measures

### Login Rate Limiting (Brute Force Protection)

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter()

# Login Versuch tracken
login_attempts = {}  # ip → [(timestamp, success), ...]

@router.post("/login")
async def login(request: Request, credentials: LoginRequest):
    ip_address = rate_limiter.get_client_ip(request)
    
    # Login-Versuche tracken (max 5 pro Minute)
    now = time.time()
    login_attempts[ip_address] = [
        (ts, success) for ts, success in login_attempts.get(ip_address, [])
        if now - ts < 60
    ]
    
    failed_attempts = sum(1 for ts, success in login_attempts[ip_address] if not success)
    
    if failed_attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "TOO_MANY_LOGIN_ATTEMPTS",
                "message": "Zu viele fehlgeschlagene Login-Versuche, bitte in 5 Minuten erneut versuchen",
                "retry_after": 300
            }
        )
    
    # Login versuchen
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        # Fehlgeschlagener Versuch tracken
        login_attempts[ip_address].append((now, False))
        
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Ungültige Zugangsdaten"}
        )
    
    # Erfolgreicher Login: Versuche zurücksetzen
    login_attempts[ip_address] = [(now, True)]
    
    # Token generieren
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(request: Request, user_data: UserCreate):
    ip_address = rate_limiter.get_client_ip(request)
    
    # Registration: Max 3 pro 5 Minuten pro IP
    now = time.time()
    register_attempts[ip_address] = [
        ts for ts in register_attempts.get(ip_address, [])
        if now - ts < 300
    ]
    
    if len(register_attempts[ip_address]) >= 3:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "TOO_MANY_REGISTRATION_ATTEMPTS",
                "message": "Zu viele Registrierungsversuche von dieser IP"
            }
        )
    
    # Registration durchführen...
```

### Request Size Limits (Prevent Large Payloads)

```python
# app/middleware/request_size_limiter.py
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimiter(BaseHTTPMiddleware):
    MAX_BODY_SIZE = 1024 * 1024  # 1 MB
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Anfrage zu groß (max {self.MAX_BODY_SIZE} Bytes)"
                }
            )
        
        response = await call_next(request)
        return response

app.add_middleware(RequestSizeLimiter)
```

---

## 🧪 Testing Rate Limiting

### Unit Tests

```python
# tests/test_rate_limiter.py
import pytest
from app.middleware.rate_limiter import UserRateLimiter

@pytest.fixture
def rate_limiter():
    return UserRateLimiter()

def test_rate_limit_allows_requests(rate_limiter):
    """Testet dass Requests innerhalb des Limits erlaubt sind"""
    user_id = 1
    endpoint = "/province/1"
    
    # 50 Requests sollten erlaubt sein (Limit: 60)
    for i in range(50):
        assert rate_limiter.is_allowed(user_id, endpoint) is True

def test_rate_limit_blocks_excessive_requests(rate_limiter):
    """Testet dass zu viele Requests blockiert werden"""
    user_id = 1
    endpoint = "/province/1"
    
    # 60 Requests (Limit) sollten erlaubt sein
    for i in range(60):
        assert rate_limiter.is_allowed(user_id, endpoint) is True
    
    # 61. Request sollte blockiert werden
    assert rate_limiter.is_allowed(user_id, endpoint) is False

def test_rate_limit_resets_after_window(rate_limiter):
    """Testet dass Limit nach Window-Zeit zurückgesetzt wird"""
    user_id = 1
    endpoint = "/province/1"
    
    # Limit ausschöpfen
    for i in range(60):
        rate_limiter.is_allowed(user_id, endpoint)
    
    assert rate_limiter.is_allowed(user_id, endpoint) is False
    
    # Nach 61 Sekunden sollte wieder erlaubt sein
    import time
    time.sleep(61)  # In Production: Mock time.time()
    
    assert rate_limiter.is_allowed(user_id, endpoint) is True

def test_remaining_requests_count(rate_limiter):
    """Testet dass remaining Requests korrekt gezählt werden"""
    user_id = 1
    endpoint = "/province/1"
    
    # 10 Requests senden
    for i in range(10):
        rate_limiter.is_allowed(user_id, endpoint)
    
    remaining = rate_limiter.get_remaining(user_id, endpoint)
    assert remaining == 50  # 60 - 10 = 50
```

### Integration Tests

```python
# tests/api/test_rate_limiting.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_rate_limit_headers_present(client):
    """Testet dass Rate Limit Headers in Response gesetzt sind"""
    response = client.get("/api/v1/province/1")
    
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers

def test_429_after_excessive_requests(client):
    """Testet 429 Too Many Requests nach zu vielen Anfragen"""
    # 70 schnelle Requests senden (Limit: 60)
    for i in range(70):
        response = client.get("/api/v1/province/1")
    
    # Letzter Request sollte 429 zurückgeben
    assert response.status_code == 429
    data = response.json()
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

def test_login_rate_limit(client):
    """Testet Login Rate Limiting (Brute Force Protection)"""
    # 6 fehlgeschlagene Login-Versuche
    for i in range(6):
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "wrongpass"
        })
    
    # 6. Versuch sollte 429 zurückgeben
    assert response.status_code == 429
    data = response.json()
    assert "TOO_MANY_LOGIN_ATTEMPTS" in data["error"]["code"]

def test_anonymous_vs_authenticated_limits(client):
    """Testet dass authentifizierte User andere Limits haben"""
    # Anonym: Höhere globale Limit, aber striktere Login-Limits
    
    # Authentifiziert: Striktere Endpoint-Limits
    token = "fake_token"  # In Production: Echten Token verwenden
    
    response = client.get("/api/v1/province/1", headers={"Authorization": f"Bearer {token}"})
    assert "X-RateLimit-Limit" in response.headers
```

---

## 📊 Monitoring & Alerting

### Rate Limit Metrics (Prometheus)

```python
from prometheus_client import Counter, Gauge

RATE_LIMITED_COUNT = Counter(
    'wasteland_rate_limited_total',
    'Total number of rate-limited requests',
    ['endpoint', 'user_type']  # user_type: authenticated, anonymous
)

ACTIVE_CONNECTIONS = Gauge(
    'wasteland_active_connections',
    'Number of active WebSocket connections'
)

# In Middleware tracken:
if not allowed:
    RATE_LIMITED_COUNT.labels(
        endpoint=endpoint,
        user_type="authenticated" if user_id else "anonymous"
    ).inc()
```

---

## 🎯 Best Practices

1. **Per-User Limits bevorzugen** - Fairer als IP-basiert
2. **Striktere Limits für Write-Operations** - POST/PUT/DELETE weniger als GET
3. **Login/Register stark limitieren** - Brute Force verhindern
4. **Rate Limit Headers setzen** - Clients wissen wie viele Requests übrig
5. **Retry-After Header bei 429** - Clients wissen wann sie es erneut versuchen können
6. **Monitoring aktivieren** - Rate Limiting Events tracken

---

**Rate Limiting schützt das System vor Missbrauch und gewährleistet faire Nutzung für alle Spieler!**
