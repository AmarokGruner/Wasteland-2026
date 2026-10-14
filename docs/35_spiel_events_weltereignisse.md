# 🎉 Spiel-Events & Welt-Ereignisse

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt automatische Welt-Ereignisse: Natürliche Katastrophen, Handels-Booms/Crashes, Entdeckungen und Admin-managed Events.

---

## 🎯 Ziele

1. **Automatische Events** - Zufällige Welt-Ereignisse pro Tick
2. **Admin-Events** - Geplante Events für besondere Anlässe
3. **Event-Wahrscheinlichkeiten** - Unterschiedliche Häufigkeiten
4. **Event-Nachwirkungen** - Langfristige Effekte auf Spielwelt

---

## 🏗️ Event-System Architektur

### Event-Typen & Wahrscheinlichkeiten

```
Häufige Events (5% pro Tick):
    ├── Dürre (-50% Farm-Produktion, 3 Ticks)
    ├── Überschwemmung (Küsten-Gebäude beschädigt)
    └── Handels-Boom (+50% Luxusgut-Preise, 5 Ticks)

Seltene Events (1% pro Tick):
    ├── Seuchen-Ausbruch (Gesundheit -30)
    ├── Ressourcen-Entdeckung (neue Vorkommen)
    └── Migration-Welle (+20% Siedler-Zuwachs)

Sehr seltene Events (0.1% pro Tick):
    ├── Weltkatastrophe (große Regionen beschädigt)
    ├── Technologischer Durchbruch (-20% Forschung-Kosten)
    └── Goldene Ära (+30% Produktion, 10 Ticks)
```

---

## 📊 Datenbank-Schema für Events

### Event-Records & Trigger

```python
# app/models.py - Event Modelle

class WeltEvent(Base):
    """Welt-Ereignis (automatisch oder admin-managed)"""
    
    __tablename__ = "welt_events"
    
    id = Column(Integer, primary_key=True)
    
    # Event-Typ
    event_typ = Column(String(100), nullable=False)  # drought, flood, trade_boom, etc.
    
    # Beschreibung
    beschreibung = Column(Text)
    
    # Ausgelöst von (System oder Admin ID)
    ausgelöst_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # System-Event? (True = automatisch, False = admin-manual)
    system_event = Column(Boolean, default=True)
    
    # Betroffene Provinzen (JSON Array)
    betroffene_provinzen = Column(Text, default="[]")
    
    # Start-Tick
    start_tick = Column(Integer, nullable=False)
    
    # Dauer in Ticks (None = permanent)
    dauer_ticks = Column(Integer, nullable=True)
    
    # Effekte (JSON: was ändert sich?)
    effekte = Column(Text, default="{}")
    
    # Aktiv?
    aktiv = Column(Boolean, default=True)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)

class EventTrigger(Base):
    """Event-Trigger (Wahrscheinlichkeiten konfigurieren)"""
    
    __tablename__ = "event_triggers"
    
    id = Column(Integer, primary_key=True)
    
    # Event-Typ
    event_typ = Column(String(100), nullable=False, unique=True)
    
    # Wahrscheinlichkeit pro Tick (0.0 - 1.0)
    wahrscheinlichkeit = Column(Float, default=0.05)
    
    # Beschreibung
    beschreibung = Column(Text)
    
    # Standard-Dauer in Ticks
    standard_dauer_ticks = Column(Integer, default=5)
    
    # Standard-Effekte (JSON)
    standard_effekte = Column(Text, default="{}")

# Helper: Welt-Ereignisse pro Tick prüfen
def check_world_events_per_tick():
    """Zufällige Welt-Ereignisse pro Tick prüfen"""
    
    import random
    
    # Alle Event-Triggers laden
    triggers = db.query(EventTrigger).all()
    
    for trigger in triggers:
        # Zufallszahl generieren
        if random.random() < trigger.wahrscheinlichkeit:
            # Event auslösen!
            trigger_world_event(
                event_typ=trigger.event_typ,
                dauer_ticks=trigger.standard_dauer_ticks,
                effekte=json.loads(trigger.standard_effekte) if trigger.standard_effekte else {}
            )

def trigger_world_event(event_typ: str, dauer_ticks: int = None, effekte: dict = None, affected_provinzen: list = None):
    """Welt-Ereignis auslösen"""
    
    from app.models import WeltEvent, Province
    
    # Event in Datenbank speichern
    event = WeltEvent(
        event_typ=event_typ,
        beschreibung=get_event_beschreibung(event_typ),
        ausgelöst_von_id=None,  # System-Event
        system_event=True,
        betroffene_provinzen=json.dumps(affected_provinzen) if affected_provinzen else "[]",
        start_tick=tick_manager.current_tick,
        dauer_ticks=dauer_ticks,
        effekte=json.dumps(effekte) if effekte else {}
    )
    
    db.add(event)
    db.commit()
    
    # Event-Effekte anwenden
    apply_event_effects(event_typ, effekte, affected_provinzen)
    
    # An alle Clients broadcasten (WebSocket)
    broadcast_world_event(event_typ, get_event_beschreibung(event_typ))

def apply_event_effects(event_typ: str, effekte: dict, affected_provinzen: list):
    """Event-Effekte auf Spielwelt anwenden"""
    
    from app.models import Province, Building, ProvinceStorage
    
    if event_typ == "drought":
        # Dürre: Farm-Produktion -50% für 3 Ticks
        provinsen = db.query(Province).all() if not affected_provinzen else [db.query(Province).get(pid) for pid in affected_provinzen]
        
        for province in provinsen:
            if not province:
                continue
            
            gebaeude = db.query(Building).filter_by(province_id=province.id, typ_in=["kartoffelfarm", "getreidefarm"]).all()
            
            for gebaeude in gebaeude:
                # Produktion temporär reduzieren (in Event-Record tracken)
                pass
    
    elif event_typ == "flood":
        # Überschwemmung: Küsten-Gebäude beschädigt
        provinsen = db.query(Province).all() if not affected_provinzen else [db.query(Province).get(pid) for pid in affected_provinzen]
        
        for province in provinsen:
            if not province:
                continue
            
            # Gebäude an Küste finden (terrain_typ_id = Küste)
            gebaeude = db.query(Building).filter_by(
                province_id=province.id,
                nur_kueste=True
            ).all()
            
            for gebaeude in gebaeude:
                # Gebäude beschädigen (Stufe reduzieren)
                if gebaeude.stufe > 1:
                    gebaeude.stufe -= 1
    
    elif event_typ == "trade_boom":
        # Handels-Boom: Preise für Luxusgüter +50% für 5 Ticks
        # In Production: Marktpreise temporär erhöhen
        
        pass
    
    elif event_typ == "discovery":
        # Neue Ressource entdeckt (Vorkommen auf zufälligen Feldern)
        pass
    
    elif event_typ == "golden_era":
        # Goldene Ära: +30% Produktion für 10 Ticks
        provinsen = db.query(Province).all() if not affected_provinzen else [db.query(Province).get(pid) for pid in affected_provinzen]
        
        for province in provinsen:
            if not province:
                continue
            
            gebaeude = db.query(Building).filter_by(province_id=province.id, aktiv=True).all()
            
            for gebaeude in gebaeude:
                # Temporärer Produktions-Bonus (in Event tracken)
                pass

def get_event_beschreibung(event_typ: str) -> str:
    """Event-Beschreibung zurückgeben"""
    
    beschreibungen = {
        "drought": "🌵 Eine schwere Dürre trifft mehrere Provinzen! Farm-Produktion reduziert.",
        "flood": "🌊 Überschwemmungen beschädigen Küsten-Gebäude!",
        "trade_boom": "📈 Handels-Boom! Luxusgut-Preise steigen für kurze Zeit.",
        "seuche": "🦠 Seuchen-Ausbruch! Gesundheit und Moral leiden.",
        "discovery": "🔍 Neue Ressourcen wurden in einer Region entdeckt!",
        "migration_wave": "🚶 Migration-Welle! Mehr Siedler kommen in stabile Provinzen.",
        "world_disaster": "💥 Weltkatastrophe! Große Regionen wurden beschädigt.",
        "tech_breakthrough": "🔬 Technologischer Durchbruch! Forschung-Kosten reduziert.",
        "golden_era": "✨ Goldene Ära! Produktion für alle Provinzen erhöht."
    }
    
    return beschreibungen.get(event_typ, "Welt-Ereignis eingetreten")

def broadcast_world_event(event_typ: str, beschreibung: str):
    """Welt-Ereignis an alle WebSocket Clients broadcasten"""
    
    import json
    
    message = {
        "type": "world_event",
        "event_typ": event_typ,
        "beschreibung": beschreibung,
        "tick": tick_manager.current_tick
    }
    
    # An alle Clients senden (über Redis Pub/Sub)
    redis_client.publish(
        "wasteland:websocket",
        json.dumps(message)
    )

# Helper: Admin-Event auslösen
def admin_trigger_event(admin_id: int, event_typ: str, affected_provinzen: list = None) -> dict:
    """Admin-managed Event auslösen"""
    
    # Event in Datenbank speichern
    event = WeltEvent(
        event_typ=event_typ,
        beschreibung=get_event_beschreibung(event_typ),
        ausgelöst_von_id=admin_id,
        system_event=False,
        betroffene_provinzen=json.dumps(affected_provinzen) if affected_provinzen else "[]",
        start_tick=tick_manager.current_tick,
        dauer_ticks=5,  # Standard-Dauer für Admin-Events
        effekte="{}"
    )
    
    db.add(event)
    db.commit()
    
    # Effekte anwenden
    apply_event_effects(event_typ, {}, affected_provinzen)
    
    # Broadcast
    broadcast_world_event(event_typ, get_event_beschreibung(event_typ))
    
    return {"success": True, "message": f"Event '{event_typ}' ausgelöst"}

# Helper: Aktive Events auflisten
def get_active_events() -> list:
    """Alle aktiven Welt-Ereignisse auflisten"""
    
    events = db.query(WeltEvent).filter_by(aktiv=True).order_by(WeltEvent.start_tick.desc()).all()
    
    result = []
    
    for event in events:
        admin_user = db.query(User).get(event.ausgelöst_von_id) if event.ausgelöst_von_id else None
        
        result.append({
            "id": event.id,
            "event_typ": event.event_typ,
            "beschreibung": event.beschreibung,
            "system_event": event.system_event,
            "admin": admin_user.username if admin_user else "System",
            "start_tick": event.start_tick,
            "dauer_ticks": event.dauer_ticks,
            "aktive_ticks": tick_manager.current_tick - event.start_tick,
            "verbleibende_ticks": event.dauer_ticks - (tick_manager.current_tick - event.start_tick) if event.dauer_ticks else None,
            "erstellt_am": event.erstellt_am.isoformat()
        })
    
    return result

# Helper: Event-Triggers konfigurieren
def configure_event_trigger(event_typ: str, wahrscheinlichkeit: float, standard_dauer_ticks: int = None) -> dict:
    """Event-Trigger Wahrscheinlichkeit konfigurieren"""
    
    trigger = db.query(EventTrigger).filter_by(event_typ=event_typ).first()
    
    if not trigger:
        # Neuer Trigger
        trigger = EventTrigger(
            event_typ=event_typ,
            wahrscheinlichkeit=wahrscheinlichkeit,
            standard_dauer_ticks=standard_dauer_ticks or 5
        )
        
        db.add(trigger)
    else:
        trigger.wahrscheinlichkeit = wahrscheinlichkeit
        
        if standard_dauer_ticks:
            trigger.standard_dauer_ticks = standard_dauer_ticks
    
    db.commit()
    
    return {"success": True, "message": f"Event-Trigger '{event_typ}' konfiguriert (Wahrscheinlichkeit: {wahrscheinlichkeit})"}

# Helper: Event-Statistiken abrufen
def get_event_statistics() -> dict:
    """Event-Statistiken (Häufigkeit, Typen)"""
    
    events = db.query(WeltEvent).all()
    
    typ_count = {}
    
    for event in events:
        typ = event.event_typ
        
        if typ not in typ_count:
            typ_count[typ] = 0
        
        typ_count[typ] += 1
    
    return {
        "total_events": len(events),
        "events_by_type": typ_count,
        "system_events": sum(1 for e in events if e.system_event),
        "admin_events": sum(1 for e in events if not e.system_event)
    }

# Helper: Event ablaufen lassen (Tick-Integration)
def process_event_expiration():
    """Ablaufende Events verarbeiten (wenn Dauer erreicht)"""
    
    events = db.query(WeltEvent).filter_by(aktiv=True).all()
    
    for event in events:
        if event.dauer_ticks:
            aktive_ticks = tick_manager.current_tick - event.start_tick
            
            if aktive_ticks >= event.dauer_ticks:
                # Event ablaufen lassen
                event.aktiv = False
                
                print(f"✅ Event '{event.event_typ}' abgelaufen nach {aktive_ticks} Ticks")

# Helper: Tick-Integration (in tick_manager)
def execute_tick_with_events(self):
    """Tick mit Event-Prüfung ausführen"""
    
    # ... bestehende Logik ...
    
    # Welt-Ereignisse prüfen (zufällig)
    check_world_events_per_tick()
    
    # Event-Abläufe verarbeiten
    process_event_expiration()

# Helper: Event-Trigger Liste abrufen
def list_event_triggers() -> list:
    """Alle Event-Triggers auflisten"""
    
    triggers = db.query(EventTrigger).all()
    
    result = []
    
    for t in triggers:
        result.append({
            "event_typ": t.event_typ,
            "wahrscheinlichkeit": t.wahrscheinlichkeit,
            "beschreibung": t.beschreibung,
            "standard_dauer_ticks": t.standard_dauer_ticks,
            "standard_effekte": json.loads(t.standard_effekte) if t.standard_effekte else {}
        })
    
    return result

# Helper: Event-Trigger Standardwerte setzen
def initialize_default_event_triggers():
    """Standard Event-Triggers initialisieren (einmalig)"""
    
    default_triggers = [
        {"event_typ": "drought", "wahrscheinlichkeit": 0.05, "beschreibung": "Dürre (häufig)", "standard_dauer_ticks": 3},
        {"event_typ": "flood", "wahrscheinlichkeit": 0.03, "beschreibung": "Überschwemmung (häufig)", "standard_dauer_ticks": 2},
        {"event_typ": "trade_boom", "wahrscheinlichkeit": 0.04, "beschreibung": "Handels-Boom (häufig)", "standard_dauer_ticks": 5},
        {"event_typ": "seuche", "wahrscheinlichkeit": 0.01, "beschreibung": "Seuchen-Ausbruch (selten)", "standard_dauer_ticks": 10},
        {"event_typ": "discovery", "wahrscheinlichkeit": 0.01, "beschreibung": "Ressourcen-Entdeckung (selten)", "standard_dauer_ticks": None},
        {"event_typ": "migration_wave", "wahrscheinlichkeit": 0.005, "beschreibung": "Migration-Welle (sehr selten)", "standard_dauer_ticks": 3},
        {"event_typ": "world_disaster", "wahrscheinlichkeit": 0.001, "beschreibung": "Weltkatastrophe (extrem selten)", "standard_dauer_ticks": 5},
        {"event_typ": "tech_breakthrough", "wahrscheinlichkeit": 0.002, "beschreibung": "Technologischer Durchbruch (extrem selten)", "standard_dauer_ticks": 20},
        {"event_typ": "golden_era", "wahrscheinlichkeit": 0.001, "beschreibung": "Goldene Ära (extrem selten)", "standard_dauer_ticks": 10}
    ]
    
    for trigger_data in default_triggers:
        existing = db.query(EventTrigger).filter_by(event_typ=trigger_data["event_typ"]).first()
        
        if not existing:
            trigger = EventTrigger(
                event_typ=trigger_data["event_typ"],
                wahrscheinlichkeit=trigger_data["wahrscheinlichkeit"],
                beschreibung=trigger_data["beschreibung"],
                standard_dauer_ticks=trigger_data["standard_dauer_ticks"]
            )
            
            db.add(trigger)
    
    db.commit()

# In main.py beim Start:
"""
@app.on_event("startup")
async def startup():
    initialize_default_event_triggers()
"""
```

---

## 📡 API Endpunkte für Events

### Event Router

```python
# app/api/v1/events.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/welt/events/active")
async def get_active_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktive Welt-Ereignisse auflisten"""
    
    events = get_active_events()
    
    return {"events": events}

@router.get("/welt/events/triggers")
async def get_event_triggers(
    db: Session = Depends(get_db)
):
    """Event-Trigger (Wahrscheinlichkeiten) auflisten"""
    
    triggers = list_event_triggers()
    
    return {"triggers": triggers}

@router.post("/admin/event/trigger")
async def admin_trigger_event_endpoint(
    data: EventAuslösen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin-managed Event auslösen"""
    
    result = admin_trigger_event(
        admin_id=current_user.id,
        event_typ=data.event_typ,
        affected_provinzen=data.affected_provinzen
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "EVENT_FAILED", "message": result["error"]})
    
    return result

@router.put("/admin/event/trigger/configure")
async def configure_event_trigger_endpoint(
    data: EventTriggerKonfigurieren,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Event-Trigger Wahrscheinlichkeit konfigurieren"""
    
    result = configure_event_trigger(
        event_typ=data.event_typ,
        wahrscheinlichkeit=data.wahrscheinlichkeit,
        standard_dauer_ticks=data.standard_dauer_ticks
    )
    
    return result

@router.get("/admin/events/statistics")
async def get_event_statistics_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Event-Statistiken abrufen"""
    
    stats = get_event_statistics()
    
    return stats

@router.get("/welt/events/history")
async def get_event_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Event-Historie abrufen"""
    
    events = db.query(WeltEvent).order_by(WeltEvent.erstellt_am.desc()).limit(limit).all()
    
    result = []
    
    for event in events:
        admin_user = db.query(User).get(event.ausgelöst_von_id) if event.ausgelöst_von_id else None
        
        result.append({
            "id": event.id,
            "event_typ": event.event_typ,
            "beschreibung": event.beschreibung,
            "system_event": event.system_event,
            "admin": admin_user.username if admin_user else "System",
            "start_tick": event.start_tick,
            "erstellt_am": event.erstellt_am.isoformat()
        })
    
    return {"history": result}
```

---

## 🖥️ Client-Side Event UI (JavaScript)

### Event Manager

```javascript
// js/game/event-manager.js

classEventManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Aktive Events laden
    async loadActiveEvents() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/welt/events/active`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderEvents(data.events);
            }
        } catch (error) {
            console.error('Active Events Load Error:', error);
        }
    }

    // Events im UI rendern
    renderEvents(events) {
        const container = document.getElementById('active-events-panel');
        
        if (!container) return;

        let html = '<h3>🌍 Aktive Welt-Ereignisse</h3>';
        
        if (events.length === 0) {
            html += '<p class="no-events">Keine aktiven Welt-Ereignisse.</p>';
        } else {
            html += '<div class="events-list">';
            
            for (const event of events) {
                const icon = this.getEventIcon(event.event_typ);
                const remaining = event.verbleibende_ticks;
                
                html += `
                    <div class="event-card">
                        <div class="event-icon">${icon}</div>
                        <div class="event-info">
                            <p><strong>${this.getEventName(event.event_typ)}</strong></p>
                            <p>${event.beschreibung}</p>
                            ${remaining !== null ? `<p class="event-timer">Verbleibend: ${remaining} Ticks</p>` : '<p class="event-permanent">Permanent</p>'}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    getEventIcon(event_typ) {
        const icons = {
            'drought': '🌵',
            'flood': '🌊',
            'trade_boom': '📈',
            'seuche': '🦠',
            'discovery': '🔍',
            'migration_wave': '🚶',
            'world_disaster': '💥',
            'tech_breakthrough': '🔬',
            'golden_era': '✨'
        };
        
        return icons[event_typ] || '⚠️';
    }

    getEventName(event_typ) {
        const names = {
            'drought': 'Dürre',
            'flood': 'Überschwemmung',
            'trade_boom': 'Handels-Boom',
            'seuche': 'Seuche',
            'discovery': 'Ressourcen-Entdeckung',
            'migration_wave': 'Migration-Welle',
            'world_disaster': 'Weltkatastrophe',
            'tech_breakthrough': 'Technologischer Durchbruch',
            'golden_era': 'Goldene Ära'
        };
        
        return names[event_typ] || event_typ;
    }

    // Event Notification (WebSocket)
    handleWorldEventNotification(event_data) {
        const notification = document.createElement('div');
        notification.className = 'world-event-notification';
        
        const icon = this.getEventIcon(event_data.event_typ);
        
        notification.innerHTML = `
            <div class="event-icon">${icon}</div>
            <div class="event-message">
                <strong>${this.getEventName(event_data.event_typ)}</strong>
                <p>${event_data.beschreibung}</p>
            </div>
        `;
        
        document.getElementById('notifications').appendChild(notification);
        
        // Nach 15 Sekunden automatisch entfernen
        setTimeout(() => {
            notification.remove();
        }, 15000);
        
        // Events neu laden
        this.loadActiveEvents();
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `event-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren (WebSocket für Event-Broadcasts)
    init() {
        this.loadActiveEvents();
        
        // WebSocket für Event-Broadcasts verbinden
        const wsUrl = `ws://${window.location.host}/ws/game`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'world_event') {
                this.handleWorldEventNotification(data);
            }
        };
        
        // Periodisch Events aktualisieren (alle 60s)
        setInterval(() => {
            this.loadActiveEvents();
        }, 60000);
    }
}

// Singleton
const events = new EventManager();

export default events;
```

---

## 🧪 Testing Event-System

### Unit Tests

```python
# tests/services/test_event_service.py
import pytest

def test_trigger_world_event():
    """Testet Welt-Ereignis auslösen"""
    
    from app.models import trigger_world_event
    
    result = trigger_world_event("drought", dauer_ticks=3)
    
    # Event sollte in Datenbank gespeichert sein
    pass  # Integrationstest

def test_get_event_beschreibung():
    """Testet Event-Beschreibungen"""
    
    from app.models import get_event_beschreibung
    
    beschreibung = get_event_beschreibung("drought")
    
    assert "Dürre" in beschreibung

def test_get_active_events():
    """Testet Aktive Events auflisten"""
    
    from app.models import get_active_events
    
    events = get_active_events()
    
    assert isinstance(events, list)

def test_get_event_statistics():
    """Testet Event-Statistiken"""
    
    from app.models import get_event_statistics
    
    stats = get_event_statistics()
    
    assert "total_events" in stats

def test_initialize_default_triggers():
    """Testet Standard Event-Triggers initialisieren"""
    
    from app.models import initialize_default_event_triggers
    
    # Sollte keine Fehler werfen
    initialize_default_event_triggers()

def test_configure_event_trigger():
    """Testet Event-Trigger konfigurieren"""
    
    from app.models import configure_event_trigger
    
    result = configure_event_trigger("drought", 0.1)
    
    assert result["success"] is True

def test_process_event_expiration():
    """Testet Event-Ablauf"""
    
    from app.models import process_event_expiration
    
    # Sollte keine Fehler werfen
    process_event_expiration()

def test_list_event_triggers():
    """Testet Event-Trigger Liste"""
    
    from app.models import list_event_triggers
    
    triggers = list_event_triggers()
    
    assert isinstance(triggers, list)

def test_admin_trigger_event():
    """Testet Admin-Event auslösen"""
    
    from app.models import admin_trigger_event
    
    result = admin_trigger_event(1, "drought", [1, 2])
    
    assert result["success"] is True

def test_check_world_events_per_tick():
    """Testet Welt-Ereignisse pro Tick prüfen"""
    
    from app.models import check_world_events_per_tick
    
    # Sollte keine Fehler werfen (zufällige Events)
    check_world_events_per_tick()
```

---

## 🎯 Best Practices

1. **Wahrscheinlichkeiten konfigurierbar** - Admin kann Events anpassen
2. **Dauer tracken** - Events automatisch ablaufen lassen
3. **WebSocket Broadcast** - Sofortige Benachrichtigung an alle Spieler
4. **Event-Historie speichern** - Für Statistiken und Audit-Log
5. **System vs Admin Events trennen** - Automatisch vs. manuell

---

**Spiel-Events ermöglichen dynamische Welt-Ereignisse mit automatischen und admin-managed Events!**
