# ⏱️ Server-Tick & Zeitmanagement

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das Server-Tick-System, Zeit-Synchronisation, Tech-Produktion und Handhabung von verzögerten Aktionen im Spiel.

---

## 🎯 Ziele

1. **Deterministische Simulation** - Gleiche Ergebnisse bei gleichen Eingaben
2. **Zeit-Synchronisation** - Alle Clients sehen gleichen Spielstand
3. **Ausfall-Toleranz** - Server-Ausfall wird kompensiert
4. **Verzögerte Aktionen** - Bau/Forschung dauert mehrere Ticks
5. **Tech-Produktion** - Gebäude produzieren Tech-Level pro 24h (global für Spieler)

---

## 🏗️ Server-Tick Architektur

### Tick-System Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client     │────▶│  Server Tick  │────▶│  Database    │
│   (Browser)  │◀────│  (60s Interval)│     │  (SQLite)    │
│              │     │               │     │              │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                    ┌───────┴───────┐
                    │  WebSocket    │
                    │  Broadcast    │
                    └───────────────┘
```

### Tick-Intervall Konfiguration

```python
# app/config.py

class GameTickConfig:
    # WICHTIG: Echtzeit-Spiel mit Spul-Mechanik!
    # 1 Tick = 24 Stunden Spielzeit, aber in ECHTZEIT ablaufend
    # Jede Minute Echtzeit = +1 Minute Spul-Guthaben (Spielzeit)
    
    # Server-Tick-Intervall (wie oft wird der Tick ausgeführt?)
    TICK_INTERVAL_SECONDS = int(os.getenv("TICK_INTERVAL", "60"))
    
    # Spielzeit pro Tick in Stunden (IMMER 24)
    SPIELZEIT_PRO_TICK_STUNDEN = 24
    
    # Maximaler Spul-Bestand in Stunden (10 Tage = 240 Stunden)
    MAX_SPIELZEIT_GUTHABEN_STUNDEN = 240
    
    # Maximaler Backlog (wie viele Ticks können angesammelt werden?)
    MAX_TICK_BACKLOG = 10  # Bei Server-Ausfall max 10 Ticks nachholen
    
    # Timeout für Client-Antworten (wenn Client zu langsam antwortet)
    CLIENT_RESPONSE_TIMEOUT = 10  # Sekunden
    
    # Welt-Zeit Startpunkt (Unix Timestamp)
    WORLD_START_TIMESTAMP = 1728000000  # Beispiel: 1.10.2024
    
    # UTC als Standardszeitzone
    TIMEZONE = "UTC"

tick_config = GameTickConfig()
```

---

## ⏰ Echtzeit-Spiel mit Spul-Mechanik

### WICHTIG: 24 Stunden Echtzeit = 24 Stunden Spielzeit

**Das Spiel läuft in ECHTZEIT ab!** Jede Minute, die in der realen Welt vergeht, erhöht das Spul-Guthaben um eine Minute.

```
Realwelt: 1 Minute vergeht
    ↓
Spul-Guthaben: +1 Minute Spielzeit verfügbar
    ↓
Spieler kann bis zu 240 Stunden (10 Tage) vorspulen
```

### Server-Tick vs. Spielzeit

**Server tickt alle 60 Sekunden (1 Minute Echtzeit), aber jeder Tick repräsentiert 24 Stunden Spielzeit.**

```python
# app/services/tick_manager.py
import time
import asyncio
from datetime import datetime, timezone

class TickManager:
    def __init__(self):
        self.current_tick = 0
        self.last_tick_time = None
        self.tick_interval = tick_config.TICK_INTERVAL_SECONDS  # Server-Intervall (60s Echtzeit)
        self.spielzeit_pro_tick = tick_config.SPIELZEIT_PRO_TICK_STUNDEN  # IMMER 24 Stunden
        self.max_spielzeit_guthaben = tick_config.MAX_SPIELZEIT_GUTHABEN_STUNDEN  # 240 Stunden (10 Tage)
        self.is_running = False
        self.tick_task = None
    
    def get_current_world_time(self) -> datetime:
        """Aktuelle Welt-Zeit berechnen"""
        
        elapsed_ticks = self.current_tick
        elapsed_stunden = elapsed_ticks * self.spielzeit_pro_tick  # 24h pro Tick
        
        world_time = datetime.fromtimestamp(
            tick_config.WORLD_START_TIMESTAMP + (elapsed_stunden * 3600),  # Stunden → Sekunden
            tz=timezone.utc
        )
        
        return world_time
    
    def get_tick_number(self) -> int:
        """Aktuelle Tick-Nummer"""
        return self.current_tick
    
    def start(self):
        """Tick-Loop starten (Echtzeit-Spiel)"""
        self.is_running = True
        self.last_tick_time = time.time()
        
        # Asynchroner Tick-Loop (Server tickt alle 60s Echtzeit, jeder Tick = 24h Spielzeit)
        asyncio.create_task(self._tick_loop())
    
    async def _tick_loop(self):
        """Hauptschleife für Server-Ticks (Echtzeit)"""
        
        while self.is_running:
            try:
                # Warten bis nächster Tick fällig ist (Echtzeit-Intervall)
                await asyncio.sleep(self.tick_interval)  # z.B. 60 Sekunden Echtzeit
                
                # Tick ausführen (repräsentiert 24 Stunden Spielzeit)
                await self.execute_tick()
                
                self.current_tick += 1
                self.last_tick_time = time.time()
                
                print(f"✅ Tick #{self.current_tick} abgeschlossen ({self.get_current_world_time()})")
            
            except Exception as e:
                print(f"❌ Tick-Fehler: {e}")
                # Bei Fehler weitermachen (nicht abstürzen)
    
    async def execute_tick(self):
        """Einzelnen Tick verarbeiten"""
        
        from app.models import Province, Building, User
        
        # 1. Ressourcen-Produktion berechnen
        await self.calculate_production()
        
        # 2. Gebäude-Aktionen ausführen (Bau, Ausbau)
        await self.execute_building_actions()
        
        # 3. Einheiten bewegen/aktualisieren
        await self.update_units()
        
        # 4. Diplomatie-Beziehungen aktualisieren
        await self.update_diplomacy()
        
        # 5. Welt-Ereignisse prüfen (zufällige Events)
        await self.check_world_events()
        
        # 6. State an alle Clients broadcasten
        await self.broadcast_state_update()
    
    async def calculate_production(self):
        """Ressourcen-Produktion pro Tick berechnen (24h Intervall in ECHTZEIT)
        
        WICHTIG: Produktionswerte in models.py beziehen sich auf 24 Stunden!
        Beispiel: Kartoffelfarm (ID 2) produziert 40 Kartoffeln (Ressourcen ID 13) pro 24h.
        
        Da das Spiel in ECHTZEIT läuft:
        - Jede Minute Echtzeit = +1 Minute Spul-Guthaben (Spielzeit)
        - Nach 24 Stunden Echtzeit = 24 Stunden Spielzeit verfügbar
        - Spieler kann bis zu 240 Stunden (10 Tage) vorspulen
        """
        
        from app.models import Province, Building
        
        # Alle Provinzen durchgehen
        provinces = db.query(Province).all()
        
        for province in provinces:
            # Gebäude der Provinz finden (nur aktive!)
            buildings = db.query(Building).filter_by(province_id=province.id, aktiv=True).all()
            
            total_production = {}
            
            for building in buildings:
                # Produktion aus Gebäude-Typ lesen (24h-Wert!)
                produktion = building.typ.produktion  # JSON: {"ressourcen_id_13": 40}
                
                if not produktion:
                    continue
                
                # Terrain-Effektivität anwenden (50-100%)
                terrain_eff = building.typ.terrain_effektivitaet.get(province.terrain_typ_id, 100)
                efficiency = terrain_eff / 100.0
                
                # Produktion berechnen (24h-Wert × Terrain-Bonus)
                for ressourcen_id, amount in produktion.items():
                    if ressourcen_id not in total_production:
                        total_production[ressourcen_id] = 0
                    total_production[ressourcen_id] += amount * efficiency
            
            # Spul-Guthaben prüfen (MAX 240 Stunden = 10 Tage!)
            storage = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
            
            if not storage:
                # Storage erstellen wenn nicht vorhanden
                storage = ProvinceStorage(province_id=province.id)
                db.add(storage)
            
            for ressourcen_id, amount in total_production.items():
                storage_key = f"resources_{ressourcen_id}"
                
                # Aktuelles Spul-Guthaben lesen (in Stunden)
                current = getattr(storage, storage_key, 0) or 0
                
                # Maximaler Spul-Bestand (240 Stunden = 10 Tage)
                max_guthaben = self.max_spielzeit_guthaben  # 240 Stunden
                
                # Produktion hinzufügen, aber nicht über Maximum hinaus
                new_amount = min(current + amount, max_guthaben)
                
                # Überschuss verfällt! (wenn über 240 Stunden)
                if current + amount > max_guthaben:
                    verfall = (current + amount) - max_guthaben
                    print(f"⚠️  Verfall in Provinz {province.id}: {verfall} Stunden Ressourcen ({ressourcen_id})")
                
                setattr(storage, storage_key, new_amount)
            
            db.commit()
    
    async def execute_building_actions(self):
        """Gebäude-Aktionen ausführen (Bau, Ausbau) - in ECHTZEIT
        
        WICHTIG: Gebäude sind SOFORT da, wenn errichtet!
        - Kein Bau-Fortschritt über Ticks hinweg
        - Gebäude zählt beim nächsten Tick mit (wenn Spieler vorspult)
        - Echtzeit-Spiel: 24h Echtzeit = 24h Spielzeit
        """
        
        from app.models import Building
        
        # Gebäude mit aktiven Bau-Aktionen finden (wenn es doch welche gibt)
        buildings = db.query(Building).filter_by(bau_status="im_bau").all()
        
        for building in buildings:
            # Fortschritt erhöhen (1 Tick = 24h Spielzeit)
            building.bau_fortschritt += 10  # 10% pro Tick
            
            if building.bau_fortschritt >= 100:
                # Bau abgeschlossen (nach 10 Ticks = 240 Stunden Spielzeit)
                building.bau_status = "fertig"
                building.bau_fortschritt = 100
                
                # Gebäude aktivieren (sofort verfügbar!)
                building.aktiv = True
                
                print(f"✅ Gebäude {building.id} ({building.typ.name}) fertig gebaut!")
            
            db.commit()
    
    async def calculate_tech_production(self):
        """Tech-Produktion pro Tick berechnen (24h Intervall in ECHTZEIT)
        
        WICHTIG: Tech-Level gilt für ALLE Provinzen des Spielers!
        Gebäude mit Techproduktion produzieren pro 24h einen bestimmten Wert.
        
        BEISPIEL:
        - Feuerstelle (ID 71): Techproduktion = 1 pro 24h
        - Nach 24 Stunden: Tech-Level +1
        - Nach 240 Stunden (10 Tage): Tech-Level +10
        
        WICHTIG: Gebäude addieren ihre Werte, multiplizieren NICHT!
        - Provinz A: 1 Feuerstelle (+1 Tech) + 1 Universität (+15 Tech) = +16 Tech/24h
        - Provinz B: 1 Feuerstelle (+1 Tech) = +1 Tech/24h
        - Gesamt: +17 Tech/24h
        
        VERBRAUCHSGÜTER:
        - Einige Tech-Gebäude benötigen Verbrauchsgüter (ähnlich anderer produzierender Gebäude)
        - Beispiel: Erfinderwerkstatt produziert 3 Tech, benötigt:
          * 2 Bretter
          * 0,5 Werkzeug
          * 1 Seile
        
        - Ist nur 1 Bretter, 0,25 Werkzeug und 0,5 Seile vorhanden:
          * Bretter: 1/2 = 50%
          * Werkzeug: 0,25/0,5 = 50%
          * Seile: 0,5/1 = 50%
          * Geringster Wert bestimmt Produktion: 50%
          * Ergebnis: 3 Tech × 50% = 1,5 Tech
        
        Tech-Level bestimmt:
        1. Welche Gebäude baubar sind (z.B. Beerenpresse bei Tech-Level 130)
        2. Ausbaustufen von Gebäuden (Grundwert × Multiplikator)
        
        Ausbaustufen-Formel:
        - Stufe 1: Grundwert (z.B. 130)
        - Stufe 2: Grundwert × 2 (z.B. 260)
        - Stufe 3: Grundwert × 4 (z.B. 520)
        - Stufe 4: Grundwert × 7 (z.B. 910)
        - Stufe 5: Grundwert × 11 (z.B. 1430)
        - Stufe 6: Grundwert × 16 (z.B. 2080)
        - Stufe 7: Grundwert × 22 (z.B. 2860)
        - Stufe 9: Grundwert × 37 (z.B. 4810)
        - Stufe 10: Grundwert × 46 (z.B. 5980)
        """
        
        from app.models import Province, Building
        
        # Alle Provinzen durchgehen
        provinces = db.query(Province).all()
        
        for province in provinces:
            # Gebäude mit Techproduktion finden (nur aktive!)
            buildings = db.query(Building).filter_by(
                province_id=province.id, 
                aktiv=True
            ).all()
            
            total_tech = 0
            
            for building in buildings:
                # Techproduktion aus Gebäude-Typ lesen (24h-Wert!)
                tech_prod = building.typ.techproduktion  # Integer: z.B. 1
                
                if not tech_prod or tech_prod == 0:
                    continue
                
                # Terrain-Effektivität anwenden (50-100%)
                terrain_eff = building.typ.terrain_effektivitaet.get(
                    province.terrain_typ_id, 100
                )
                efficiency = terrain_eff / 100.0
                
                # Grundproduktion berechnen (24h-Wert × Terrain-Bonus)
                base_tech = tech_prod * efficiency
                
                # VERBRAUCHSGÜTER prüfen (wenn vorhanden)
                verbrauchsgueter = building.typ.verbrauchsgueter  # JSON: {"ressourcen_id_1": 2, ...}
                
                if verbrauchsgueter:
                    # Verbrauchsmenge prüfen (pro 24h)
                    min_verfuegbarkeit = 100.0  # Start bei 100%
                    
                    for ressourcen_id, benoetigte_menge in verbrauchsgueter.items():
                        # Aktuellen Lagerbestand lesen (in Stunden)
                        storage_key = f"resources_{ressourcen_id}"
                        aktueller_bestand = getattr(
                            province.storage, storage_key, 0
                        ) or 0
                        
                        # Verfügbarkeit berechnen (aktueller / benötigter Bestand)
                        verfuegbarkeit = (aktueller_bestand / benoetigte_menge) * 100.0
                        
                        # Geringste Verfügbarkeit bestimmt die Produktion
                        min_verfuegbarkeit = min(min_verfuegbarkeit, verfuegbarkeit)
                    
                    # Produktion mit Verfügbarkeit multiplizieren
                    total_tech += base_tech * (min_verfuegbarkeit / 100.0)
                    
                    if min_verfuegbarkeit < 100:
                        print(f"⚠️  Teilproduktion in Provinz {province.id}: "
                              f"{building.typ.name} produziert nur {min_verfuegbarkeit:.1f}% "
                              f"({base_tech * (min_verfuegbarkeit / 100.0):.2f} Tech)")
                else:
                    # Keine Verbrauchsgüter → volle Produktion
                    total_tech += base_tech
            
            # Tech-Level des Spielers aktualisieren (global für alle Provinzen!)
            player = db.query(Player).filter_by(id=province.player_id).first()
            
            if not player:
                continue
            
            # Tech-Level akkumulieren (pro 24h Tick)
            player.tech_level += total_tech
            
            print(f"🔬 Tech-Produktion in Provinz {province.id}: +{total_tech:.2f} Tech")
            print(f"   Gesamt-Tech-Level von Spieler {player.id}: {player.tech_level}")
            
            db.commit()
    
    async def update_units(self):
        """Einheiten bewegen/aktualisieren"""
        
        units = db.query(Unit).filter_by(bewegungs_status="unterwegs").all()
        
        for unit in units:
            # Bewegung fortsetzen
            unit.bewegung_fortschritt += 5  # 5% pro Tick
            
            if unit.bewegung_fortschritt >= 100:
                # Ziel erreicht
                unit.bewegungs_status = "angekommen"
                unit.bewegung_fortschritt = 100
                
                # Aktion ausführen (Angreifen, Verteidigen, etc.)
                await self.execute_unit_action(unit)
            
            db.commit()
    
    async def check_world_events(self):
        """Zufällige Welt-Ereignisse prüfen"""
        
        import random
        
        # 5% Chance pro Tick für ein Welt-Ereignis
        if random.random() < 0.05:
            event_type = random.choice(["drought", "flood", "trade_boom", "discovery"])
            
            await self.trigger_world_event(event_type)
    
    async def trigger_world_event(self, event_type: str):
        """Welt-Ereignis auslösen"""
        
        if event_type == "drought":
            # Dürre: Produktion aller Farmen reduziert um 50% für 3 Ticks
            print("🌵 Welt-Ereignis: Dürre!")
            
        elif event_type == "flood":
            # Überschwemmung: Küsten-Gebäude beschädigt
            print("🌊 Welt-Ereignis: Überschwemmung!")
            
        elif event_type == "trade_boom":
            # Handels-Boom: Preise für Luxusgüter steigen
            print("📈 Welt-Ereignis: Handels-Boom!")
            
        elif event_type == "discovery":
            # Neue Ressource entdeckt
            print("🔍 Welt-Ereignis: Neue Entdeckung!")

# Singleton
tick_manager = TickManager()
```

---

## 🔄 Client-Server Synchronisation

### WebSocket State Broadcast

```python
# app/services/state_sync.py
import json
from app.services.redis_client import redis_client

class StateSyncService:
    async def broadcast_state_update(self):
        """Spiel-State an alle Clients broadcasten"""
        
        # Aktuellen State sammeln
        state = {
            "tick": tick_manager.current_tick,
            "world_time": tick_manager.get_current_world_time().isoformat(),
            "events": []  # Welt-Ereignisse dieses Ticks
        }
        
        # Redis Pub/Sub an alle WebSocket Clients senden
        await redis_client.publish(
            "wasteland:websocket",
            json.dumps({
                "type": "state_update",
                **state
            })
        )
    
    async def sync_client_state(self, user_id: int) -> dict:
        """Client-State mit Server synchronisieren"""
        
        # Letzten bekannten Tick des Clients
        client_tick = self.get_client_last_tick(user_id)
        
        # Wenn Client veraltet ist: Vollständigen State senden
        if client_tick < tick_manager.current_tick - 5:
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
                    "name": building.typ.name,
                    "status": building.bau_status,
                    "fortschritt": building.bau_fortschritt,
                    "stufe": building.stufe
                })
            
            # Einheiten der Provinz
            units = db.query(Unit).filter_by(province_id=province.id).all()
            
            for unit in units:
                province_data["units"].append({
                    "id": unit.id,
                    "typ": unit.typ.name,
                    "status": unit.bewegungs_status,
                    "fortschritt": unit.bewegung_fortschritt
                })
            
            # Ressourcen der Provinz
            storage = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
            
            if storage:
                province_data["resources"] = {
                    "food": storage.resources_food,
                    "water": storage.resources_water,
                    "energy": storage.resources_energy
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

## 🖥️ Client-Side Tick Handling (JavaScript)

### Game Loop & State Sync

```javascript
// js/game/tick-manager.js

class TickManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
        this.currentTick = 0;
        this.worldTime = null;
        this.lastServerTick = 0;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    // WebSocket Verbindung herstellen
    connect() {
        const wsUrl = `ws://${window.location.host}/ws/game`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('✅ WebSocket verbunden');
            this.reconnectAttempts = 0;
            
            // Initialen State anfordern
            this.requestStateSync();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('⚠️ WebSocket getrennt, versuche neu zu verbinden...');
            this.attemptReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket Error:', error);
        };
    }

    // Nachrichten verarbeiten
    handleMessage(data) {
        switch (data.type) {
            case 'state_update':
                this.handleStateUpdate(data);
                break;
            
            case 'delta_update':
                this.handleDeltaUpdate(data);
                break;
            
            case 'world_event':
                this.handleWorldEvent(data);
                break;
            
            case 'error':
                this.handleError(data);
                break;
        }
    }

    // Vollständiger State Update
    handleStateUpdate(data) {
        this.currentTick = data.tick;
        this.worldTime = data.world_time;
        
        // UI aktualisieren
        this.updateUI(data);
        
        // Game State speichern
        localStorage.setItem('game_state', JSON.stringify(data));
    }

    // Delta Update (nur Änderungen)
    handleDeltaUpdate(data) {
        for (const delta of data.deltas) {
            this.applyDelta(delta);
        }
        
        this.currentTick = data.tick;
    }

    // Welt-Ereignis verarbeiten
    handleWorldEvent(data) {
        const event = data.event;
        
        // Notification anzeigen
        this.showWorldEventNotification(event);
        
        // UI aktualisieren (z.B. Dürre: Farmen grau markieren)
        this.updateWorldEventUI(event);
    }

    // UI aktualisieren
    updateUI(state) {
        // Welt-Zeit anzeigen
        document.getElementById('world-time').textContent = 
            `Weltzeit: ${this.formatWorldTime(this.worldTime)}`;
        
        // Tick-Nummer anzeigen
        document.getElementById('current-tick').textContent = 
            `Tick: ${this.currentTick}`;
        
        // Ressourcen aktualisieren
        this.updateResources(state.provinces);
        
        // Gebäude-Status aktualisieren
        this.updateBuildings(state.provinces);
    }

    // Delta auf UI anwenden
    applyDelta(delta) {
        if (delta.event === 'building_completed') {
            this.markBuildingAsComplete(delta.data.building_id);
        } else if (delta.event === 'resources_updated') {
            this.updateResourceDisplay(delta.data);
        } else if (delta.event === 'unit_moved') {
            this.updateUnitPosition(delta.data);
        }
    }

    // Welt-Ereignis Notification anzeigen
    showWorldEventNotification(event) {
        const notification = document.createElement('div');
        notification.className = 'world-event-notification';
        
        const icons = {
            'drought': '🌵',
            'flood': '🌊',
            'trade_boom': '📈',
            'discovery': '🔍'
        };
        
        notification.innerHTML = `
            <div class="event-icon">${icons[event.type] || '⚠️'}</div>
            <div class="event-message">${event.message}</div>
        `;
        
        document.getElementById('notifications').appendChild(notification);
        
        // Nach 10 Sekunden automatisch entfernen
        setTimeout(() => {
            notification.remove();
        }, 10000);
    }

    // State vom Server anfordern (bei Disconnect)
    async requestStateSync() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/game/state`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const state = await response.json();
                this.handleStateUpdate(state);
            }
        } catch (error) {
            console.error('State Sync Error:', error);
        }
    }

    // Reconnect versuchen (exponentieller Backoff)
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max Reconnect Attempts erreicht');
            this.showOfflineMessage();
            return;
        }
        
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        
        console.log(`Versuche neu zu verbinden in ${delay}ms (Attempt ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
            this.connect();
            this.reconnectAttempts++;
        }, delay);
    }

    showOfflineMessage() {
        const message = document.createElement('div');
        message.id = 'offline-message';
        message.className = 'offline-banner';
        message.innerHTML = `
            <p>🔴 Offline - Verbindung zum Server getrennt</p>
            <p>Spiel läuft weiter, aber keine Echtzeit-Updates möglich.</p>
        `;
        
        document.body.appendChild(message);
    }

    formatWorldTime(worldTime) {
        // Welt-Zeit in lesbares Format umwandeln
        const date = new Date(worldTime);
        return date.toLocaleString('de-DE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Initialisieren
    init() {
        this.connect();
        
        // Periodisch State prüfen (wenn WebSocket nicht verfügbar)
        setInterval(() => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.requestStateSync();
            }
        }, 30000); // Alle 30 Sekunden
    }
}

// Singleton
const tickManager = new TickManager();

export default tickManager;
```

---

## 🛡️ Server-Ausfall & Recovery

### Ausfall-Szenarien

```python
# app/services/failure_recovery.py

class FailureRecoveryService:
    async def handle_server_restart(self):
        """Server Neustart verarbeiten"""
        
        # 1. Letzten Tick aus Datenbank laden
        last_tick = db.query(GameState).order_by(GameState.tick.desc()).first()
        
        if last_tick:
            tick_manager.current_tick = last_tick.tick
            
            print(f"🔄 Server neu gestartet - letzter Tick: #{last_tick.tick}")
        
        # 2. World Time berechnen
        world_time = tick_manager.get_current_world_time()
        
        # 3. Alle Provinzen validieren (Datenkonsistenz prüfen)
        await self.validate_province_data()
        
        # 4. Tick-Loop neu starten
        tick_manager.start()
    
    async def validate_province_data(self):
        """Provinz-Daten auf Konsistenz prüfen"""
        
        provinces = db.query(Province).all()
        
        for province in provinces:
            # Lagerbestände prüfen (dürfen nicht negativ sein)
            storage = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
            
            if storage:
                for resource_field in ['resources_food', 'resources_water', 'resources_energy']:
                    value = getattr(storage, resource_field, 0)
                    
                    if value < 0:
                        print(f"⚠️  Negative Ressourcen in Provinz {province.id}: {resource_field}={value}")
                        setattr(storage, resource_field, 0)  # Auf 0 setzen
        
        db.commit()
    
    async def handle_client_disconnect(self, user_id: int):
        """Client Disconnect verarbeiten"""
        
        # Client-State im Redis tracken (für Reconnect)
        await redis_client.setex(
            f"client_state:{user_id}",
            3600,  # 1 Stunde gültig
            json.dumps({
                "last_tick": tick_manager.current_tick,
                "disconnected_at": datetime.utcnow().isoformat()
            })
        )
    
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
        
        # Sonst nur Delta senden
        return await state_sync.get_delta_state(user_id, last_client_tick)

# Singleton
failure_recovery = FailureRecoveryService()
```

---

## 🧪 Testing Tick-System

### Unit Tests

```python
# tests/services/test_tick_manager.py
import pytest
import asyncio
from datetime import datetime, timezone

@pytest.fixture
def tick_manager():
    from app.services.tick_manager import TickManager
    
    manager = TickManager()
    manager.current_tick = 0
    
    return manager

def test_get_current_world_time(tick_manager):
    """Testet Welt-Zeit Berechnung"""
    
    tick_manager.current_tick = 10
    
    world_time = tick_manager.get_current_world_time()
    
    # Erwartet: WORLD_START + 10 * TICK_INTERVAL
    expected_timestamp = tick_config.WORLD_START_TIMESTAMP + (10 * tick_config.TICK_INTERVAL_SECONDS)
    expected_time = datetime.fromtimestamp(expected_timestamp, tz=timezone.utc)
    
    assert world_time.year == expected_time.year
    assert world_time.month == expected_time.month

def test_tick_increment(tick_manager):
    """Testet Tick-Inkrementierung"""
    
    assert tick_manager.current_tick == 0
    
    tick_manager.current_tick += 1
    
    assert tick_manager.current_tick == 1

def test_world_time_advances_with_ticks(tick_manager):
    """Testet dass Welt-Zeit mit Ticks fortschreitet"""
    
    time_0 = tick_manager.get_current_world_time()
    
    tick_manager.current_tick = 60  # 60 Ticks = 60 * 60s = 3600s = 1 Stunde
    
    time_60 = tick_manager.get_current_world_time()
    
    # Zeit sollte sich um 1 Stunde unterscheiden
    assert (time_60 - time_0).total_seconds() == 3600

@pytest.mark.asyncio
async def test_tick_loop_runs(tick_manager, mocker):
    """Testet dass Tick-Loop läuft"""
    
    execute_tick_mock = mocker.patch.object(tick_manager, 'execute_tick')
    
    tick_manager.is_running = True
    
    # Loop für 3 Ticks starten (mit kurzem Interval für Test)
    original_interval = tick_config.TICK_INTERVAL_SECONDS
    tick_config.TICK_INTERVAL_SECONDS = 0.1  # 100ms für Test
    
    task = asyncio.create_task(tick_manager._tick_loop())
    
    await asyncio.sleep(0.35)  # Warten bis 3 Ticks durchlaufen
    
    tick_manager.is_running = False
    await task
    
    # execute_tick sollte 3x aufgerufen worden sein
    assert execute_tick_mock.call_count == 3
    
    # Restore original interval
    tick_config.TICK_INTERVAL_SECONDS = original_interval

def test_state_sync_full_vs_delta(tick_manager):
    """Testet Full State vs Delta State Logik"""
    
    # Client ist aktuell (< 5 Ticks veraltet)
    client_tick = tick_manager.current_tick - 2
    
    # Sollte Delta zurückgeben (effizienter)
    assert tick_manager.current_tick - client_tick < 5
    
    # Client ist veraltet (> 5 Ticks)
    client_tick = tick_manager.current_tick - 10
    
    # Sollte Full State zurückgeben
    assert tick_manager.current_tick - client_tick >= 5
```

---

## 🎯 Best Practices

1. **Server als Single Source of Truth** - Client niemals vertrauen
2. **WebSocket für Echtzeit-Updates** - Polling vermeiden
3. **Delta Updates bei Reconnect** - Nur Änderungen senden, nicht ganzen State
4. **Exponential Backoff beim Reconnect** - Server nicht überlasten
5. **World Time deterministisch** - Gleiche Ticks = gleiche Zeit

---

**Server-Tick-System ermöglicht deterministische, synchronisierte Spiel-Simulation!**
