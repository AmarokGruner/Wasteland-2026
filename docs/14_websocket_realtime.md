# 🔄 WebSocket & Real-time Communication

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von Echtzeit-Kommunikation zwischen Client und Server für:
- Live-Spielupdates (Server-Tick Ergebnisse)
- Chat/Nachrichten zwischen Spielern
- Event-Benachrichtigungen (Gebäude fertig, Invasionen)
- Multi-Player Interaktionen (Handel, Diplomatie)

---

## 🎯 Warum Real-time?

1. **Sofortiges Feedback** - Spieler sehen Änderungen sofort
2. **Reduzierte Polling-Last** - Server pushet Updates statt Client fragt ab
3. **Bessere UX** - Kein manuelles Aktualisieren nötig
4. **Multi-Player Koordination** - Echtzeit-Kommunikation

---

## 🏗️ Architektur-Entscheidung

### Option 1: WebSockets (Empfohlen)
```
Client ←→ WebSocket Server ←→ FastAPI Backend
```

**Vorteile:**
- Bidirektionale Kommunikation
- Persistent Connection
- Low Latency
- Standardisiert (RFC 6455)

**Nachteile:**
- Stateful Connection Management
- Skalierung komplexer (Session Affinity)

### Option 2: Server-Sent Events (SSE)
```
Client ←── SSE Stream ←── FastAPI Backend
```

**Vorteile:**
- Einfacher zu implementieren
- HTTP Standard (kein Protokollwechsel)
- Auto-Reconnect

**Nachteile:**
- Nur Server → Client (kein Client → Server)
- Keine bidirektionale Kommunikation

### Option 3: Long Polling (Fallback)
```
Client → HTTP Request → Server wartet auf Event → Response
```

**Vorteile:**
- Funktioniert in allen Browsern/Netzwerken
- Kein WebSocket Support nötig

**Nachteile:**
- Höhere Latency
- Mehr Overhead

### ✅ Empfohlen: WebSockets mit SSE Fallback

---

## 🔌 WebSocket Implementation in FastAPI

### Installation

```bash
pip install websockets uvicorn[standard]
```

### WebSocket Endpoint

```python
# app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

router = APIRouter()

# Aktive WebSocket Connections tracken
class ConnectionManager:
    def __init__(self):
        # province_id → Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, province_id: int):
        await websocket.accept()
        
        if province_id not in self.active_connections:
            self.active_connections[province_id] = set()
        
        self.active_connections[province_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, province_id: int):
        if province_id in self.active_connections:
            self.active_connections[province_id].discard(websocket)
            
            # Letzten Connection entfernen wenn keine mehr da
            if not self.active_connections[province_id]:
                del self.active_connections[province_id]
    
    async def send_to_province(self, province_id: int, message: str):
        """Sende Nachricht an alle Connections einer Provinz"""
        if province_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[province_id]:
                try:
                    await connection.send_text(message)
                except WebSocketDisconnect:
                    disconnected.add(connection)
            
            # Disconnected Connections entfernen
            for conn in disconnected:
                self.disconnect(conn, province_id)
    
    async def send_to_all(self, message: str):
        """Sende Nachricht an alle Connections"""
        for province_id in list(self.active_connections.keys()):
            await self.send_to_province(province_id, message)

manager = ConnectionManager()

@router.websocket("/ws/province/{province_id}")
async def websocket_province(websocket: WebSocket, province_id: int):
    """WebSocket Endpoint für Provinz-Updates"""
    await manager.connect(websocket, province_id)
    
    try:
        # Initial State senden
        initial_state = await get_province_state(province_id)
        await websocket.send_json({
            "type": "initial_state",
            "data": initial_state
        })
        
        # Auf Nachrichten vom Client warten
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Client Nachricht verarbeiten
            if message["type"] == "chat":
                await handle_chat_message(province_id, message)
            elif message["type"] == "action":
                await handle_player_action(province_id, message)
            elif message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, province_id)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        manager.disconnect(websocket, province_id)

async def get_province_state(province_id: int) -> dict:
    """Aktuellen Provinz-State abrufen"""
    # Aus Datenbank laden
    province = db.query(Province).get(province_id)
    return {
        "id": province.id,
        "name": province.name,
        "mips": province.mips,
        "population": province.population,
        "buildings_count": len(province.buildings),
        "last_tick": province.last_tick.isoformat() if province.last_tick else None
    }

async def handle_chat_message(province_id: int, message: dict):
    """Chat-Nachricht verarbeiten und an alle senden"""
    chat_message = {
        "type": "chat",
        "province_id": province_id,
        "player_id": message["player_id"],
        "player_name": message["player_name"],
        "text": message["text"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # In Datenbank speichern
    db_chat = PlayerMessage(**chat_message)
    db.add(db_chat)
    db.commit()
    
    # An alle in der Provinz senden
    await manager.send_to_province(province_id, json.dumps(chat_message))

async def handle_player_action(province_id: int, message: dict):
    """Spieler-Aktion verarbeiten und Updates senden"""
    # Aktion ausführen (z.B. Gebäude bauen)
    result = await execute_building_action(province_id, message["building_type"])
    
    # Update an alle in der Provinz senden
    await manager.send_to_province(province_id, json.dumps({
        "type": "building_built",
        "province_id": province_id,
        "building_type": message["building_type"],
        "result": result
    }))

@router.websocket("/ws/global")
async def websocket_global(websocket: WebSocket):
    """Globaler WebSocket für alle Spieler (Events, News)"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            # Globale Events empfangen/verarbeiten
            pass
    except WebSocketDisconnect:
        pass

@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """Admin WebSocket für Echtzeit-Admin-Dashboard"""
    await websocket.accept()
    
    # Nur Admins dürfen connecten
    token = websocket.query_params.get("token")
    if not is_admin(token):
        await websocket.close(code=4001, reason="Admin access required")
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            # Admin Commands verarbeiten
            pass
    except WebSocketDisconnect:
        pass
```

---

## 📡 Server-Sent Events (SSE) Fallback

### SSE Endpoint

```python
# app/api/sse.py
from fastapi import APIRouter, Response
from starlette.responses import StreamingResponse
import asyncio
import json

router = APIRouter()

async def province_event_stream(province_id: int):
    """Generator für SSE Events"""
    while True:
        try:
            # Provinz-State abrufen
            state = await get_province_state(province_id)
            
            # Event formatieren
            event_data = json.dumps({
                "event": "province_update",
                "data": state
            })
            
            yield f"data: {event_data}\n\n"
            
            # 5 Sekunden warten bis nächstes Event
            await asyncio.sleep(5)
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(1)

@router.get("/sse/province/{province_id}")
async def sse_province(province_id: int):
    """SSE Endpoint für Provinz-Updates"""
    return StreamingResponse(
        province_event_stream(province_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # nginx Buffer deaktivieren
        }
    )

@router.get("/sse/global")
async def sse_global():
    """Globale SSE Events (News, Events)"""
    async def global_event_stream():
        while True:
            events = await get_global_events()
            
            for event in events:
                yield f"event: global_event\ndata: {json.dumps(event)}\n\n"
            
            await asyncio.sleep(10)
    
    return StreamingResponse(
        global_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

---

## 🌐 Client-Side Implementation (JavaScript)

### WebSocket Manager

```javascript
// js/websocket-manager.js

class WebSocketManager {
    constructor(baseUrl = 'ws://localhost:8011') {
        this.baseUrl = baseUrl;
        this.connections = {};
        this.reconnectAttempts = {};
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Event Handler registrieren
        this.eventHandlers = {};
    }

    connect(provinceId) {
        const wsUrl = `${this.baseUrl}/ws/province/${provinceId}`;
        
        // Bestehende Connection schließen
        if (this.connections[provinceId]) {
            this.disconnect(provinceId);
        }

        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`WebSocket connected to province ${provinceId}`);
            this.reconnectAttempts[provinceId] = 0;
            
            // Initial State empfangen
            this.onInitialState(provinceId);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(provinceId, message);
        };

        ws.onclose = (event) => {
            console.log(`WebSocket disconnected from province ${provinceId}`, event.code);
            
            // Auto-Reconnect (wenn nicht manuell geschlossen)
            if (!event.wasClean && this.reconnectAttempts[provinceId] < this.maxReconnectAttempts) {
                this.reconnectAttempts[provinceId]++;
                const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts[provinceId] - 1);
                
                console.log(`Reconnecting to province ${provinceId} in ${delay}ms (attempt ${this.reconnectAttempts[provinceId]})`);
                
                setTimeout(() => this.connect(provinceId), delay);
            }
        };

        ws.onerror = (error) => {
            console.error(`WebSocket error for province ${provinceId}:`, error);
        };

        this.connections[provinceId] = ws;
    }

    disconnect(provinceId) {
        if (this.connections[provinceId]) {
            this.connections[provinceId].close();
            delete this.connections[provinceId];
            this.reconnectAttempts[provinceId] = 0;
        }
    }

    handleMessage(provinceId, message) {
        // Globale Event Handler
        if (this.eventHandlers[message.type]) {
            this.eventHandlers[message.type](message);
        }

        // Provinz-spezifische Handler
        if (this.eventHandlers[`province_${provinceId}_${message.type}`]) {
            this.eventHandlers[`province_${provinceId}_${message.type}`](message);
        }

        // Update UI basierend auf Message Type
        switch (message.type) {
            case 'initial_state':
                this.updateProvinceUI(provinceId, message.data);
                break;
            case 'building_built':
                this.showBuildingNotification(provinceId, message.building_type);
                break;
            case 'chat':
                this.addChatMessage(provinceId, message);
                break;
            case 'tick_complete':
                this.updateTickResults(provinceId, message.data);
                break;
            case 'event':
                this.showEventNotification(message.data);
                break;
        }
    }

    send(provinceId, message) {
        if (this.connections[provinceId] && this.connections[provinceId].readyState === WebSocket.OPEN) {
            this.connections[provinceId].send(JSON.stringify(message));
        } else {
            console.warn(`WebSocket not open for province ${provinceId}`);
        }
    }

    on(type, handler) {
        this.eventHandlers[type] = handler;
    }

    updateProvinceUI(provinceId, state) {
        // UI aktualisieren (MIPS, Bevölkerung, Gebäude)
        document.getElementById(`mips-${provinceId}`).textContent = state.mips;
        document.getElementById(`population-${provinceId}`).textContent = state.population;
    }

    showBuildingNotification(provinceId, buildingType) {
        // Toast Notification anzeigen
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = `Neues Gebäude gebaut: ${buildingType}`;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }

    addChatMessage(provinceId, message) {
        const chatContainer = document.getElementById(`chat-${provinceId}`);
        const messageEl = document.createElement('div');
        messageEl.className = 'chat-message';
        messageEl.innerHTML = `
            <strong>${message.player_name}:</strong> ${message.text}
            <span class="timestamp">${new Date(message.timestamp).toLocaleTimeString()}</span>
        `;
        chatContainer.appendChild(messageEl);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    updateTickResults(provinceId, data) {
        // Server-Tick Ergebnisse anzeigen (Produktion, Verbrauch, Wachstum)
        console.log(`Tick results for province ${provinceId}:`, data);
    }

    showEventNotification(eventData) {
        // Event Notification anzeigen (z.B. "Invasion approaching!")
        console.log('Global event:', eventData);
    }
}

// Singleton Instance
const wsManager = new WebSocketManager();

export default wsManager;
```

### SSE Fallback Manager

```javascript
// js/sse-fallback.js

class SSEManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
        this.eventSources = {};
    }

    connect(provinceId) {
        const url = `${this.baseUrl}/sse/province/${provinceId}`;
        
        // Bestehende Source schließen
        if (this.eventSources[provinceId]) {
            this.disconnect(provinceId);
        }

        const eventSource = new EventSource(url);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.error) {
                console.error('SSE Error:', data.error);
                return;
            }
            
            // UI aktualisieren
            if (data.event === 'province_update') {
                this.updateProvinceUI(provinceId, data.data);
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            // Fallback zu Polling wenn SSE nicht funktioniert
            this.startPolling(provinceId);
        };

        this.eventSources[provinceId] = eventSource;
    }

    disconnect(provinceId) {
        if (this.eventSources[provinceId]) {
            this.eventSources[provinceId].close();
            delete this.eventSources[provinceId];
        }
    }

    updateProvinceUI(provinceId, state) {
        // Ähnlich wie WebSocket Manager
        document.getElementById(`mips-${provinceId}`).textContent = state.mips;
    }

    startPolling(provinceId) {
        console.warn('SSE not available, falling back to polling');
        
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/province/${provinceId}`);
                const state = await response.json();
                this.updateProvinceUI(provinceId, state);
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 5000);
        
        // Polling stoppen wenn SSE wieder funktioniert
        this.eventSources[provinceId]?.addEventListener('open', () => {
            clearInterval(pollInterval);
        });
    }
}

const sseManager = new SSEManager();

export default sseManager;
```

---

## 🧪 Testing WebSocket & SSE

### WebSocket Integration Tests

```python
# tests/api/test_websocket.py
import pytest
from fastapi.testclient import TestClient, WebSocket
import json

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

@pytest.mark.asyncio
async def test_websocket_connection(client):
    """Testet WebSocket Verbindung zu Provinz"""
    async with client.websocket_connect("/ws/province/1") as websocket:
        # Initial State empfangen
        data = await websocket.receive_json()
        assert data["type"] == "initial_state"
        assert "id" in data["data"]
        assert "mips" in data["data"]

@pytest.mark.asyncio
async def test_websocket_chat(client):
    """Testet Chat über WebSocket"""
    async with client.websocket_connect("/ws/province/1") as websocket:
        # Chat Nachricht senden
        await websocket.send_json({
            "type": "chat",
            "player_id": 1,
            "player_name": "TestPlayer",
            "text": "Hallo Welt!"
        })
        
        # Nachricht sollte an Connection gesendet werden
        data = await websocket.receive_json()
        assert data["type"] == "chat"
        assert data["text"] == "Hallo Welt!"

@pytest.mark.asyncio
async def test_sse_province(client):
    """Testet SSE Endpoint für Provinz-Updates"""
    response = client.get("/sse/province/1", stream=True)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # Events sollten kommen
    events = []
    for line in response.iter_lines():
        if line:
            events.append(line.decode('utf-8'))
            if len(events) >= 2:  # Mindestens 2 Events
                break
    
    assert len(events) >= 1
    assert events[0].startswith("data: ")

@pytest.mark.asyncio
async def test_websocket_unauthorized(client):
    """Testet unauthorized WebSocket Connection"""
    with pytest.raises(Exception):  # Should raise WebSocketException
        async with client.websocket_connect("/ws/admin"):
            pass
```

---

## 📊 Performance & Skalierung

### Connection Limits

```python
# app/config.py

class WebSocketConfig:
    MAX_CONNECTIONS_PER_PROVINCE = 100  # Max Connections pro Provinz
    MAX_TOTAL_CONNECTIONS = 10000       # Max Gesamt-Connections
    HEARTBEAT_INTERVAL = 30             # Sekunden zwischen Pings
    CONNECTION_TIMEOUT = 120            # Sekunden bis Timeout
```

### Redis als Message Broker (für Multi-Server Setup)

```python
# app/websocket/redis_broker.py
import redis
import json

class RedisWebSocketBroker:
    """Message Broker für WebSocket Connections über mehrere Server"""
    
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
    
    async def publish_to_province(self, province_id: int, message: str):
        """Nachricht an alle Server für eine Provinz publishen"""
        channel = f"ws:province:{province_id}"
        self.redis.publish(channel, message)
    
    async def subscribe_to_province(self, province_id: int):
        """Channel für Provinz subscriben"""
        pubsub = self.redis.pubsub()
        channel = f"ws:province:{province_id}"
        pubsub.subscribe(channel)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
```

---

## 🎯 Best Practices

1. **Auto-Reconnect implementieren** - Verbindungen instabil sein können
2. **Heartbeat/Ping-Pong** - Dead Connections erkennen
3. **Rate Limiting pro Connection** - Missbrauch verhindern
4. **Message Queue für Events** - Bei hoher Last puffern
5. **Fallback zu SSE/Polling** - Für ältere Browser/Netzwerke
6. **Connection Monitoring** - Aktive Connections tracken

---

**WebSocket & SSE stellen sicher, dass Spieler sofortiges Feedback erhalten und das Spiel sich lebendig anfühlt!**
