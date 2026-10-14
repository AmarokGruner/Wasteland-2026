# 🔄 Multiplayer-Synchronisation

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Synchronisation des Spiel-States zwischen Server und mehreren Clients: State-Sync, Konfliktlösung, Latenz-Behandlung und Offline-Modus.

---

## 🎯 Ziele

1. **Echtzeit-Synchronisation** - Alle Spieler sehen gleichen Spielstand
2. **Konfliktlösung** - Gleichzeitige Aktionen werden gelöst (nicht ignoriert)
3. **Latenz-Toleranz** - Spieler mit hoher Ping werden nicht benachteiligt
4. **Offline-Support** - Spiel läuft weiter wenn Connection verloren geht

---

## 🏗️ Synchronisations-Architektur

### Server-Centric Design

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client 1   │────▶│               │     │             │
│   (Browser)  │     │               │     │  SQLite     │
├─────────────┤     │               │     │  Database   │
│   Client 2   │────▶│   Server      │◀────│             │
│   (Browser)  │     │   (FastAPI)   │     │             │
├─────────────┤     │               │     └─────────────┘
│   Client N   │────▶│               │           ▲
└─────────────┘     └──────────────┘           │
        ▲                    │              Tick-Loop
        │                    ▼           (60s Interval)
        └────────── WebSocket Broadcast ◀─┘
```

---

## 📊 State-Sync Mechanismen

### Vollständiger State vs. Delta Updates

```python
# app/services/state_sync.py

class StateSyncService:
    async def sync_client_state(self, user_id: int, client_tick: int) -> dict:
        """Client-State mit Server synchronisieren"""
        
        server_tick = tick_manager.current_tick
        
        # Wenn Client veraltet (> 5 Ticks) → Vollständigen State senden
        if server_tick - client_tick > 5:
            return await self.get_full_state(user_id)
        
        # Sonst nur Delta (Änderungen seit letztem Tick)
        return await self.get_delta_state(user_id, client_tick)
    
    async def get_full_state(self, user_id: int) -> dict:
        """Vollständigen Spiel-State für User abrufen"""
        
        from app.models import Province, Building, Unit
        
        user = db.query(User).get(user_id)
        
        state = {
            "tick": tick_manager.current_tick,
            "world_time": tick_manager.get_current_world_time().isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "level": user.level
            },
            "provinces": []
        }
        
        # Alle Provinzen des Users
        provinces = db.query(Province).filter_by(owner_id=user.id).all()
        
        for province in provinces:
            province_data = {
                "id": province.id,
                "name": province.name,
                "x": province.x,
                "y": province.y,
                "terrain_typ_id": province.terrain_typ_id,
                "buildings": [],
                "units": [],
                "resources": {}
            }
            
            # Gebäude der Provinz
            buildings = db.query(Building).filter_by(province_id=province.id).all()
            
            for building in buildings:
                province_data["buildings"].append({
                    "id": building.id,
                    "name": building.typ.name if building.typ else "Unbekannt",
                    "status": building.bau_status,
                    "fortschritt": building.bau_fortschritt,
                    "stufe": building.stufe,
                    "x": building.x,
                    "y": building.y
                })
            
            # Einheiten der Provinz
            units = db.query(Unit).filter_by(province_id=province.id).all()
            
            for unit in units:
                province_data["units"].append({
                    "id": unit.id,
                    "typ": unit.typ.name if unit.typ else "Unbekannt",
                    "status": unit.bewegungs_status,
                    "fortschritt": unit.bewegung_fortschritt,
                    "verluste_prozent": unit.verluste_prozent
                })
            
            # Ressourcen der Provinz
            storage = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
            
            if storage:
                province_data["resources"] = {
                    "food": storage.resources_food,
                    "water": storage.resources_water,
                    "energy": storage.resources_energy,
                    "mips": storage.resources_mips
                }
            
            state["provinces"].append(province_data)
        
        return state
    
    async def get_delta_state(self, user_id: int, since_tick: int) -> dict:
        """Nur Änderungen seit bestimmtem Tick zurückgeben"""
        
        # Game Logs durchsuchen (ab since_tick)
        logs = db.query(GameLog).filter(
            GameLog.tick >= since_tick,
            GameLog.user_id == user_id
        ).order_by(GameLog.tick).all()
        
        deltas = []
        
        for log in logs:
            deltas.append({
                "tick": log.tick,
                "event": log.event_type,
                "data": json.loads(log.data) if log.data else {}
            })
        
        return {
            "tick": tick_manager.current_tick,
            "world_time": tick_manager.get_current_world_time().isoformat(),
            "deltas": deltas
        }

# Singleton
state_sync = StateSyncService()
```

---

## 🌐 WebSocket Implementation

### Game WebSocket Endpoint

```python
# app/api/v1/ws_game.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/game")
async def game_websocket(websocket: WebSocket):
    """Haupt-WebSocket für Echtzeit-Spielkommunikation"""
    
    await websocket.accept()
    
    # User ID aus Token extrahieren (vereinfacht)
    user_id = await self.extract_user_from_websocket(websocket)
    
    if not user_id:
        await websocket.close(code=4001, reason="Ungültiges Token")
        return
    
    # Client registrieren (in Redis tracken)
    await redis_client.hset("active_clients", str(user_id), websocket.client.host)
    
    try:
        while True:
            # Nachrichten vom Client empfangen
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "state_request":
                # Client fragt nach aktuellem State
                client_tick = data.get("client_tick", 0)
                
                state = await state_sync.sync_client_state(user_id, client_tick)
                
                await websocket.send_json(state)
            
            elif message_type == "action":
                # Spieler-Aktion (Bauen, Angreifen, etc.)
                action = data.get("action")
                payload = data.get("payload", {})
                
                # Aktion verarbeiten (über API Router)
                result = await self.execute_player_action(user_id, action, payload)
                
                await websocket.send_json({
                    "type": "action_result",
                    **result
                })
            
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "server_tick": tick_manager.current_tick,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        # Client getrennt
        await redis_client.hdel("active_clients", str(user_id))
        
        # Offline-State speichern
        await failure_recovery.handle_client_disconnect(user_id)
        
        print(f"❌ Client {user_id} getrennt")
    
    except Exception as e:
        print(f"❌ WebSocket Error für User {user_id}: {e}")
        await websocket.close(code=4000, reason=str(e))

async def execute_player_action(self, user_id: int, action: str, payload: dict):
    """Spieler-Aktion über WebSocket ausführen"""
    
    # Action routing (vereinfacht)
    action_handlers = {
        "build": self.handle_build_action,
        "attack": self.handle_attack_action,
        "move_unit": self.handle_move_unit_action,
        "trade": self.handle_trade_action
    }
    
    handler = action_handlers.get(action)
    
    if not handler:
        return {
            "success": False,
            "error": {"code": "UNKNOWN_ACTION", "message": f"Unbekannte Aktion: {action}"}
        }
    
    return await handler(user_id, payload)

async def handle_build_action(self, user_id: int, payload: dict):
    """Bau-Aktion verarbeiten"""
    
    province_id = payload.get("province_id")
    gebaeude_typ_id = payload.get("gebaeude_typ_id")
    x = payload.get("x")
    y = payload.get("y")
    
    # Validierung (gleiche Logik wie API)
    province = db.query(Province).filter_by(id=province_id, owner_id=user_id).first()
    
    if not province:
        return {"success": False, "error": {"code": "NOT_OWNER", "message": "Nicht Owner"}}
    
    # Bau-Aktion ausführen (vereinfacht)
    # ... (gleiche Logik wie in API Endpoint)
    
    return {"success": True, "message": "Gebäude gebaut"}

async def handle_attack_action(self, user_id: int, payload: dict):
    """Angriff-Aktion verarbeiten"""
    
    von_provinz_id = payload.get("von_provinz_id")
    ziel_provinz_id = payload.get("ziel_provinz_id")
    
    # Validierung (gleiche Logik wie API)
    # ...
    
    return {"success": True, "message": "Angriff ausgeführt"}

async def handle_move_unit_action(self, user_id: int, payload: dict):
    """Einheiten-Bewegung verarbeiten"""
    
    unit_id = payload.get("unit_id")
    ziel_provinz_id = payload.get("ziel_provinz_id")
    
    # Validierung (gleiche Logik wie API)
    # ...
    
    return {"success": True, "message": "Einheit bewegt"}

async def handle_trade_action(self, user_id: int, payload: dict):
    """Handel-Aktion verarbeiten"""
    
    von_provinz_id = payload.get("von_provinz_id")
    ziel_provinz_id = payload.get("ziel_provinz_id")
    artikel_id = payload.get("artikel_id")
    menge = payload.get("menge")
    
    # Validierung (gleiche Logik wie API)
    # ...
    
    return {"success": True, "message": "Handel durchgeführt"}

async def extract_user_from_websocket(self, websocket: WebSocket) -> int:
    """User ID aus WebSocket Connection extrahieren"""
    
    # Token aus Query Parameter oder Header
    query_params = websocket.query_params
    
    token = query_params.get("token")
    
    if not token:
        return None
    
    # Token decodieren (vereinfacht)
    import jwt
    from app.config import SECRET_KEY
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return int(payload.get("sub"))  # sub = user_id
    
    except Exception:
        return None
```

---

## ⚡ Latenz-Behandlung (Prediction & Interpolation)

### Client-Side Prediction

```javascript
// js/game/latency-handler.js

class LatencyHandler {
    constructor() {
        this.serverTick = 0;
        this.clientActions = [];  // Ausstehende Aktionen (warten auf Bestätigung)
        this.lastServerTime = null;
        this.roundTripTime = 0;  // RTT in ms
    }

    // Server-Ping messen (RTT)
    async measurePing() {
        const startTime = Date.now();
        
        try {
            const response = await fetch('/api/v1/game/ping', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.roundTripTime = Date.now() - startTime;
                this.serverTick = data.tick;
                this.lastServerTime = data.timestamp;
                
                return { rtt: this.roundTripTime, tick: data.tick };
            }
        } catch (error) {
            console.error('Ping Error:', error);
        }
        
        return null;
    }

    // Aktion senden mit Prediction (sofortiges UI-Feedback)
    async sendActionWithPrediction(actionType, payload) {
        // 1. Sofort UI aktualisieren (Prediction)
        this.predictAction(actionType, payload);
        
        // 2. Aktion an Server senden
        const ws = this.getWebSocket();
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'action',
                action: actionType,
                payload: payload
            }));
            
            // Aktion in pending queue speichern (warten auf Bestätigung)
            this.clientActions.push({
                type: actionType,
                payload: payload,
                timestamp: Date.now(),
                confirmed: false
            });
        } else {
            // Kein WebSocket → HTTP Fallback (langsamer)
            await this.sendActionHTTP(actionType, payload);
        }
    }

    // Prediction: UI sofort aktualisieren (ohne Server-Bestätigung)
    predictAction(actionType, payload) {
        switch (actionType) {
            case 'build':
                this.addBuildingToUI(payload.province_id, payload.gebaeude_typ_id, payload.x, payload.y);
                break;
            
            case 'move_unit':
                this.moveUnitOnUI(payload.unit_id, payload.ziel_provinz_id);
                break;
            
            case 'attack':
                this.startAttackOnUI(payload.von_provinz_id, payload.ziel_provinz_id);
                break;
        }
    }

    // Server-Antwort verarbeiten (Bestätigung oder Ablehnung)
    handleServerResponse(response) {
        if (!response.confirmed) {
            // Server hat Aktion abgelehnt → Prediction zurücksetzen
            this.revertPrediction(response.actionType, response.payload);
            
            this.showNotification(`Aktion abgelehnt: ${response.error.message}`, 'error');
        } else {
            // Aktion bestätigt → aus pending queue entfernen
            this.confirmAction(response.actionType, response.payload);
        }
    }

    // Prediction zurücksetzen (wenn Server ablehnt)
    revertPrediction(actionType, payload) {
        switch (actionType) {
            case 'build':
                this.removeBuildingFromUI(payload.x, payload.y);
                break;
            
            case 'move_unit':
                this.undoUnitMovementOnUI(payload.unit_id);
                break;
        }
    }

    // Aktion bestätigen (aus pending queue entfernen)
    confirmAction(actionType, payload) {
        const index = this.clientActions.findIndex(
            a => a.type === actionType && 
                 JSON.stringify(a.payload) === JSON.stringify(payload)
        );
        
        if (index !== -1) {
            this.clientActions.splice(index, 1);
        }
    }

    // Ausstehende Aktionen prüfen (timeout nach 5 Sekunden)
    checkPendingActions() {
        const now = Date.now();
        
        for (let i = this.clientActions.length - 1; i >= 0; i--) {
            const action = this.clientActions[i];
            
            if (now - action.timestamp > 5000) {
                // Timeout → Prediction zurücksetzen und HTTP-Fallback versuchen
                this.revertPrediction(action.type, action.payload);
                
                console.warn(`Aktion timeout: ${action.type} - versuche HTTP-Fallback`);
                
                this.sendActionHTTP(action.type, action.payload)
                    .then(result => {
                        if (result.success) {
                            this.predictAction(action.type, action.payload);
                        }
                    });
                
                this.clientActions.splice(i, 1);
            }
        }
    }

    // HTTP-Fallback (langsamer, aber zuverlässiger)
    async sendActionHTTP(actionType, payload) {
        try {
            const response = await fetch(`/api/v1/game/action/${actionType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // UI aktualisieren mit Server-Response
                this.updateUIFromServer(actionType, data);
                
                return { success: true };
            } else {
                const error = await response.json();
                
                this.revertPrediction(actionType, payload);
                this.showNotification(error.detail.message, 'error');
                
                return { success: false };
            }
        } catch (error) {
            console.error('HTTP Action Error:', error);
            return { success: false };
        }
    }

    // WebSocket Connection verwalten
    getWebSocket() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.connectWebSocket();
        }
        
        return this.ws;
    }

    connectWebSocket() {
        const token = localStorage.getItem('access_token');
        const wsUrl = `ws://${window.location.host}/ws/game?token=${token}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'action_result') {
                this.handleServerResponse(data);
            } else if (data.type === 'state_update') {
                this.handleStateUpdate(data);
            } else if (data.type === 'pong') {
                this.serverTick = data.server_tick;
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket getrennt');
            
            // Auto-Reconnect mit Backoff
            setTimeout(() => {
                this.connectWebSocket();
            }, 2000);
        };
    }

    // State Update verarbeiten (von Server Broadcast)
    handleStateUpdate(data) {
        this.serverTick = data.tick;
        
        // UI mit Server-State synchronisieren (nur wenn nicht gerade Prediction aktiv)
        if (this.clientActions.length === 0) {
            this.updateUIFromServerState(data);
        }
    }

    // UI von Server-State aktualisieren
    updateUIFromServerState(state) {
        // Gebäude rendern
        for (const province of state.provinces) {
            this.renderBuildings(province.id, province.buildings);
            this.renderUnits(province.id, province.units);
            this.renderResources(province.id, province.resources);
        }
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `latency-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Hilfsfunktionen für UI (müssen implementiert werden)
    addBuildingToUI(provinceId, gebaeudeTypId, x, y) {}
    removeBuildingFromUI(x, y) {}
    moveUnitOnUI(unitId, zielProvinzId) {}
    undoUnitMovementOnUI(unitId) {}
    startAttackOnUI(vonProvinzId, zielProvinzId) {}
    renderBuildings(provinceId, buildings) {}
    renderUnits(provinceId, units) {}
    renderResources(provinceId, resources) {}
    updateUIFromServer(actionType, data) {}

    // Initialisieren
    init() {
        this.connectWebSocket();
        
        // Ping messen (alle 30s)
        setInterval(() => {
            this.measurePing();
        }, 30000);
        
        // Ausstehende Aktionen prüfen (alle 5s)
        setInterval(() => {
            this.checkPendingActions();
        }, 5000);
    }
}

// Singleton
const latencyHandler = new LatencyHandler();

export default latencyHandler;
```

---

## 📴 Offline-Modus & Reconnect

### Offline-State Management

```python
# app/services/offline_handler.py

class OfflineHandler:
    async def handle_client_disconnect(self, user_id: int):
        """Client Disconnect verarbeiten"""
        
        # Client-State im Redis speichern (für Reconnect)
        await redis_client.setex(
            f"client_state:{user_id}",
            3600,  # 1 Stunde gültig
            json.dumps({
                "last_tick": tick_manager.current_tick,
                "disconnected_at": datetime.utcnow().isoformat(),
                "last_known_state": await self.get_last_known_state(user_id)
            })
        )
        
        print(f"⚠️  Client {user_id} offline - State gespeichert")
    
    async def handle_client_reconnect(self, user_id: int) -> dict:
        """Client Reconnect verarbeiten"""
        
        # Letzten Client-State laden
        client_state_json = await redis_client.get(f"client_state:{user_id}")
        
        if not client_state_json:
            # Kein State gefunden → Vollständigen State senden
            return await state_sync.get_full_state(user_id)
        
        client_state = json.loads(client_state_json)
        last_client_tick = client_state["last_tick"]
        
        # Wenn Client veraltet (> 5 Ticks) → Vollständiger State
        if tick_manager.current_tick - last_client_tick > 5:
            return await state_sync.get_full_state(user_id)
        
        # Sonst nur Delta senden (effizienter)
        return await state_sync.get_delta_state(user_id, last_client_tick)
    
    async def get_last_known_state(self, user_id: int) -> dict:
        """Letzten bekannten State serialisieren"""
        
        # Vereinfacht: aktuellen DB-State zurückgeben
        return await state_sync.get_full_state(user_id)

# Singleton
offline_handler = OfflineHandler()
```

---

## 🧪 Testing Synchronisation

### Unit Tests

```python
# tests/services/test_state_sync.py
import pytest
import asyncio

@pytest.fixture
def state_sync_service():
    from app.services.state_sync import StateSyncService
    
    return StateSyncService()

@pytest.mark.asyncio
async def test_full_state_contains_provinces(state_sync_service):
    """Testet dass Full State Provinzen enthält"""
    
    state = await state_sync_service.get_full_state(1)
    
    assert "provinces" in state
    assert isinstance(state["provinces"], list)

@pytest.mark.asyncio
async def test_delta_state_contains_deltas(state_sync_service):
    """Testet dass Delta State Änderungen enthält"""
    
    delta = await state_sync_service.get_delta_state(1, 0)
    
    assert "deltas" in delta
    assert isinstance(delta["deltas"], list)

@pytest.mark.asyncio
async def test_sync_uses_full_for_old_clients(state_sync_service):
    """Testet dass veraltete Clients Full State erhalten"""
    
    # Client ist 10 Ticks veraltet (> 5)
    client_tick = tick_manager.current_tick - 10
    
    state = await state_sync_service.sync_client_state(1, client_tick)
    
    assert "provinces" in state  # Full State hat provinces

@pytest.mark.asyncio
async def test_sync_uses_delta_for_recent_clients(state_sync_service):
    """Testet dass aktuelle Clients Delta State erhalten"""
    
    # Client ist 2 Ticks veraltet (< 5)
    client_tick = tick_manager.current_tick - 2
    
    state = await state_sync_service.sync_client_state(1, client_tick)
    
    assert "deltas" in state  # Delta State hat deltas

def test_latency_prediction():
    """Testet Client-Side Prediction Logik"""
    
    from js.game.latency_handler import LatencyHandler
    
    handler = LatencyHandler()
    
    # Prediction sollte UI sofort aktualisieren (ohne Server)
    handler.predictAction("build", {"province_id": 1, "x": 10, "y": 10})
    
    # UI sollte Gebäude enthalten (mock)
    # In Production: Integrationstest mit tatsächlichem UI

def test_reconnect_full_vs_delta():
    """Testet Reconnect Logik (Full vs Delta)"""
    
    from app.services.offline_handler import OfflineHandler
    
    handler = OfflineHandler()
    
    # Client 10 Ticks offline → Full State
    # Client 2 Ticks offline → Delta State
    
    # Mock Redis State
    pass  # Integrationstest erforderlich
```

---

## 🎯 Best Practices

1. **WebSocket优先** - Echtzeit-Kommunikation über WebSocket, HTTP als Fallback
2. **Client-Side Prediction** - UI sofort aktualisieren, Server-Bestätigung abwarten
3. **Delta Updates** - Nur Änderungen senden wenn Client aktuell
4. **Full State bei Reconnect** - Bei Disconnect > 5 Ticks → kompletten State senden
5. **Heartbeat/Ping** - Verbindung alive halten (alle 30s)
6. **Auto-Reconnect mit Backoff** - Exponentiell verzögerte Wiederholungsversuche

---

**Multiplayer-Synchronisation ermöglicht Echtzeit-Spielgefühl mit Latenz-Toleranz und Offline-Support!**
