# 💾 Caching Strategy & Redis Integration

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von Caching mit Redis für:
- API Response Caching (häufig angefragte Daten)
- Session Storage
- Rate Limiting State
- WebSocket Broadcast State

---

## 🎯 Ziele

1. **Performance verbessern** - Häufige Anfragen nicht zur Datenbank
2. **Skalierbarkeit ermöglichen** - Redis als zentraler Cache
3. **Session Management** - Serverless Sessions (Redis-basiert)
4. **Real-time State** - WebSocket Broadcast über Redis Pub/Sub

---

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI    │────▶│   Redis      │────▶│   SQLite     │
│   Backend    │◀────│   Cache      │     │   Database   │
│              │     │              │     │              │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                    ┌───────┴───────┐
                    │  Pub/Sub      │
                    │ (WebSocket)   │
                    └───────────────┘
```

---

## 🔧 Installation & Configuration

### Dependencies

```bash
pip install redis aioredis fastapi-redis-cache
```

### Redis Configuration

```python
# app/config.py

class RedisConfig:
    # Redis Connection (lokal oder Cloud)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Cache TTL (Time To Live) in Sekunden
    CACHE_TTL_API_RESPONSE = 300        # API Responses: 5 Minuten
    CACHE_TTL_WORLD_MAP = 60            # Weltkarte: 1 Minute (oft aktualisiert)
    CACHE_TTL_USER_PROFILE = 600        # User Profile: 10 Minuten
    CACHE_TTL_PROVINCE_DATA = 120       # Provinz-Daten: 2 Minuten
    
    # Session TTL
    SESSION_TTL = 86400                 # 24 Stunden
    
    # Pub/Sub Channel Prefix
    PUBSUB_CHANNEL_PREFIX = "wasteland:"

redis_config = RedisConfig()
```

---

## 🔧 Redis Client Setup

### Async Redis Connection

```python
# app/services/redis_client.py
import redis.asyncio as aioredis
from app.config import redis_config

class RedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Redis Connection herstellen"""
        try:
            self.redis = aioredis.from_url(
                redis_config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Verbindung testen
            await self.redis.ping()
            print("✅ Redis verbunden")
        
        except Exception as e:
            print(f"⚠️  Redis Verbindung fehlgeschlagen: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Redis Connection schließen"""
        if self.redis:
            await self.redis.close()
    
    def get(self):
        """Sync Redis Client (für nicht-async Code)"""
        if not self.redis:
            raise RuntimeError("Redis nicht verbunden")
        return self.redis

# Singleton Instance
redis_client = RedisClient()

# In main.py beim Start verbinden/trennen:
"""
@app.on_event("startup")
async def startup():
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_client.disconnect()
"""
```

---

## 📦 API Response Caching

### Cache Decorator für FastAPI Endpoints

```python
# app/middleware/response_caching.py
from functools import wraps
import hashlib
import json
from fastapi import Request, Response
from app.services.redis_client import redis_client

def cache_response(ttl: int = 300):
    """Cache Decorator für API Endpoints"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Request aus kwargs extrahieren
            request = kwargs.get("request") or (args[1] if len(args) > 1 else None)
            
            if not request:
                return await func(*args, **kwargs)
            
            # Cache Key generieren (aus URL + Query Params)
            cache_key = self.generate_cache_key(request)
            
            # Aus Redis lesen
            redis = redis_client.get()
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                # Cache Hit - Return cached Response
                return Response(
                    content=cached_data,
                    media_type="application/json"
                )
            
            # Cache Miss - Request ausführen
            response = await func(*args, **kwargs)
            
            # Response Body serialisieren und cache'n
            if hasattr(response, 'body'):
                body = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
                
                # Nur GET Requests cache'n (safe Operations)
                if request.method == "GET":
                    await redis.setex(cache_key, ttl, body)
            
            return response
        
        return wrapper
    
    return decorator

def generate_cache_key(request: Request) -> str:
    """Cache Key aus URL und Query Params generieren"""
    key_parts = [request.url.path]
    
    # Query Params sortiert hinzufügen (für konsistenten Key)
    query_params = sorted(request.query_params.items())
    if query_params:
        key_parts.append("&".join(f"{k}={v}" for k, v in query_params))
    
    cache_key = "cache:" + hashlib.md5(":".join(key_parts).encode()).hexdigest()
    return cache_key

# Verwendung:
"""
@router.get("/api/v1/province/{province_id}")
@cache_response(ttl=120)  # 2 Minuten cache'n
async def get_province(province_id: int, request: Request):
    province = db.query(Province).get(province_id)
    return province
"""
```

### Cache Invalidation (bei Änderungen)

```python
# app/middleware/cache_invalidator.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CacheInvalidator(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Bei Write Operations (POST/PUT/DELETE): Cache invalidieren
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            await self.invalidate_related_caches(request.url.path)
        
        return response
    
    async def invalidate_related_caches(self, endpoint: str):
        """Verwandte Cache Keys invalidieren"""
        redis = redis_client.get()
        
        # Pattern für Cache Keys (z.B. "cache:province:*")
        patterns = {
            "/api/v1/province/": "cache:province:*",
            "/api/v1/building/": "cache:building:*",
            "/api/v1/resource/": "cache:resource:*",
        }
        
        for path_prefix, pattern in patterns.items():
            if endpoint.startswith(path_prefix):
                # Alle Keys mit Pattern löschen
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)

app.add_middleware(CacheInvalidator)
```

---

## 📝 Session Storage (Redis-basiert)

### FastAPI Session mit Redis

```python
# app/middleware/session_storage.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

class RedisSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            # Neuen Session ID generieren
            import secrets
            session_id = secrets.token_urlsafe(32)
        
        # Session aus Redis laden
        redis = redis_client.get()
        session_data = await redis.get(f"session:{session_id}")
        
        if session_data:
            request.state.session = json.loads(session_data)
        else:
            request.state.session = {}
        
        # Request verarbeiten
        response = await call_next(request)
        
        # Session in Redis speichern (mit TTL)
        await redis.setex(
            f"session:{session_id}",
            86400,  # 24 Stunden TTL
            json.dumps(request.state.session)
        )
        
        # Session Cookie setzen
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400
        )
        
        return response

app.add_middleware(RedisSessionMiddleware)
```

---

## 📡 WebSocket Broadcast mit Redis Pub/Sub

### Redis Pub/Sub für Multi-Server Setup

```python
# app/services/websocket_pubsub.py
import json
import redis.asyncio as aioredis

class WebSocketPubSub:
    def __init__(self):
        self.redis = None
        self.pubsub = None
    
    async def connect(self):
        """Redis Pub/Sub Connection herstellen"""
        self.redis = aioredis.from_url(
            "redis://localhost:6379/0",
            encoding="utf-8",
            decode_responses=True
        )
        
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe("wasteland:websocket")
        
        print("✅ Redis Pub/Sub verbunden (WebSocket Broadcast)")
    
    async def publish_message(self, channel: str, message: dict):
        """Nachricht an alle WebSocket Clients broadcasten"""
        
        payload = json.dumps({
            "channel": channel,
            **message
        })
        
        await self.redis.publish("wasteland:websocket", payload)
    
    async def listen(self):
        """Pub/Sub Messages empfangen und an WebSocket Clients weiterleiten"""
        
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                
                channel = data.get("channel")
                event_type = data.get("event")
                payload = data.get("payload")
                
                # An alle Clients im Channel broadcasten
                await self.broadcast_to_channel(channel, {
                    "event": event_type,
                    "payload": payload
                })
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Nachricht an alle Clients in einem Channel senden"""
        
        # Vereinfacht: Alle aktiven WebSocket Connections tracken
        # In Production: Redis Hash mit client_id → connection mapping
        
        active_connections = await self.get_active_connections(channel)
        
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"WebSocket Send Error: {e}")
    
    async def get_active_connections(self, channel: str):
        """Aktive WebSocket Connections für Channel abrufen"""
        
        # In Production: Redis Hash "wasteland:connections:{channel}" tracken
        # Hier vereinfacht als leere Liste (nur lokaler Server)
        return []

# Singleton
websocket_pubsub = WebSocketPubSub()
```

---

## 📊 Rate Limiting State (Redis)

### Redis-basiertes Rate Limiting

```python
# app/middleware/rate_limit_redis.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class RedisRateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = self.extract_user_id(request)
        endpoint = request.url.path
        
        if not user_id:
            return await call_next(request)
        
        redis = redis_client.get()
        
        # Redis Lua Script für atomisches Rate Limiting
        lua_script = """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            
            -- Zähler erhöhen
            local count = redis.call('INCR', key)
            
            -- Bei erstem Request TTL setzen
            if count == 1 then
                redis.call('EXPIRE', key, window)
            end
            
            -- Limit erreicht?
            if count > limit then
                return redis.call('TTL', key)
            end
            
            return 0
        """
        
        register_key = f"ratelimit:{user_id}:{endpoint}"
        ttl_result = await redis.eval(
            lua_script,
            1,
            register_key,
            60,    # Limit: 60 requests
            60     # Window: 60 seconds
        )
        
        if ttl_result > 0:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Zu viele Anfragen",
                    "retry_after": int(ttl_result)
                }
            )
        
        response = await call_next(request)
        
        # Rate Limit Headers setzen
        remaining = 60 - (await redis.get(register_key) or 0)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response

app.add_middleware(RedisRateLimiter)
```

---

## 🧪 Testing Caching

### Unit Tests für Redis Cache

```python
# tests/services/test_redis_cache.py
import pytest
from app.services.redis_client import redis_client

@pytest.fixture
async def redis():
    client = redis_client.get()
    yield client
    await client.flushdb()  # Test Cleanup

@pytest.mark.asyncio
async def test_set_get(redis):
    """Testet Set/Get Operationen"""
    await redis.set("test:key", "test_value")
    value = await redis.get("test:key")
    
    assert value == "test_value"

@pytest.mark.asyncio
async def test_setex_ttl(redis):
    """Testet Set mit TTL (Time To Live)"""
    await redis.setex("test:ttl", 10, "expires_in_10s")
    
    value = await redis.get("test:ttl")
    assert value == "expires_in_10s"

@pytest.mark.asyncio
async def test_delete(redis):
    """Testet Delete Operation"""
    await redis.set("test:delete", "value")
    await redis.delete("test:delete")
    
    value = await redis.get("test:delete")
    assert value is None

@pytest.mark.asyncio
async def test_cache_decorator(redis):
    """Testet Cache Decorator"""
    from app.middleware.response_caching import cache_response
    
    call_count = 0
    
    @cache_response(ttl=60)
    async def expensive_operation():
        nonlocal call_count
        call_count += 1
        return {"data": "result"}
    
    # Erster Aufruf: Cache Miss
    result1 = await expensive_operation()
    assert call_count == 1
    
    # Zweiter Aufruf: Cache Hit (sollte nicht erhöhen)
    result2 = await expensive_operation()
    assert call_count == 1  # Keine weitere Execution

@pytest.mark.asyncio
async def test_cache_invalidation(redis):
    """Testet Cache Invalidation bei Write Operations"""
    # Cache setzen
    await redis.set("cache:province:123", '{"id": 1, "name": "Test"}')
    
    # Cache invalidieren
    await redis.delete("cache:province:*")  # Pattern Delete
    
    value = await redis.get("cache:province:123")
    assert value is None  # Gelöscht
```

---

## 📊 Monitoring Redis Performance

### Prometheus Metrics für Redis

```python
from prometheus_client import Counter, Histogram

CACHE_HITS = Counter(
    'wasteland_cache_hits_total',
    'Total number of cache hits'
)

CACHE_MISSES = Counter(
    'wasteland_cache_misses_total',
    'Total number of cache misses'
)

CACHE_OPERATION_DURATION = Histogram(
    'wasteland_cache_operation_duration_seconds',
    'Duration of Redis cache operations'
)

# In Cache Decorator tracken:
"""
if cached_data:
    CACHE_HITS.inc()
else:
    CACHE_MISSES.inc()

with CACHE_OPERATION_DURATION.time():
    await redis.get(cache_key)
"""
```

---

## 🎯 Best Practices

1. **TTL immer setzen** - Verhindert Memory Leaks
2. **Cache Keys strukturieren** - "cache:resource:id" Pattern
3. **Invalidation bei Write Operations** - Konsistenz gewährleisten
4. **Redis als Fallback** - Wenn Redis ausfällt, direkt zur Datenbank
5. **Monitoring aktivieren** - Cache Hit/Miss Ratio tracken

---

**Caching mit Redis verbessert Performance und ermöglicht skalierbare Architektur!**
