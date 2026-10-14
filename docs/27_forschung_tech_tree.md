# 🔬 Forschung & Tech-Tree

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das Forschungs-System: Forschungs-Punkte verdienen, Tech-Tree durchlaufen, Gebäude und Einheiten freischalten.

---

## 🎯 Ziele

1. **Forschungs-Fortschritt** - Durch Gebäude und Aktionen Punkte verdienen
2. **Tech-Tree Struktur** - Logische Abhängigkeiten zwischen Technologien
3. **Freischaltungen** - Neue Gebäude, Einheiten, Ressourcen verfügbar machen
4. **Forschungs-Gebäude** - Universität, Labor als Forschungszentren

---

## 🏗️ Tech-Tree Architektur

### Technologiestufen

```
Steinzeit (Tech-Level 0-10)
    ├── Holzfäller, Steinmetz
    ├── Einfache Farmen
    └── Siedlung (Stadt Level 0)
        ↓
Bronzezeit (Tech-Level 10-30)
    ├── Weberei, Sägewerk
    ├── Getreidefarm, Kartoffelfarm
    └── Kaserne (einfache Einheiten)
        ↓
Eisenzeit (Tech-Level 30-60)
    ├── Stahlproduktion
    ├── Fort, Festung
    └── Schwerere Einheiten
        ↓
Industrie (Tech-Level 60-100)
    ├── Fabriken, Kraftwerke
    ├── Universität (Forschung beschleunigen)
    └── Moderne Waffen
        ↓
Moderne Ära (Tech-Level 100+)
    ├── Flughafen, Leuchtturm
    ├── Hochtechnologie
    └── Spezial-Einheiten
```

---

## 📊 Datenbank-Schema für Forschung

### Technologie-Tabelle

```python
# app/models.py - Forschung Modelle

class Technologie(Base):
    """Technologien im Tech-Tree"""
    
    __tablename__ = "technologien"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Tech-Level (Freischaltungsschwelle)
    tech_level = Column(Integer, nullable=False)
    
    # Beschreibung
    beschreibung = Column(Text)
    
    # Kategorie (Gebäude, Einheit, Ressource, Spezial)
    kategorie = Column(String(50), nullable=False)
    
    # Freigeschaltete Dinge (JSON)
    freischaltungen = Column(Text, default="[]")  
    # Beispiel: [{"typ": "gebaeude", "id": 15}, {"typ": "einheit", "id": 23}]
    
    # Voraussetzungen (JSON: IDs anderer Technologien)
    voraussetzungen = Column(Text, default="[]")
    # Beispiel: "[1, 5]" bedeutet Tech ID 1 und 5 müssen erforscht sein
    
    # Forschungs-Kosten (in Forschungs-Punkten)
    forschungskosten = Column(Integer, default=100)
    
    # Effekt (JSON: Boni oder Änderungen)
    effekt = Column(Text, default="{}")
    # Beispiel: {"produktions_bonus": 10, "baukosten_reduzierung": 5}
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)

class ForschungStatus(Base):
    """Forschungs-Fortschritt eines Users/Provinz"""
    
    __tablename__ = "forschung_status"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    province_id = Column(Integer, ForeignKey("provinzen.id"), nullable=True)
    
    # Erforschte Technologien (JSON Array von IDs)
    erforschte_technologien = Column(Text, default="[]")
    
    # Aktuelle Forschung (ID der Technologie die gerade erforscht wird)
    aktuelle_forschung_id = Column(Integer, nullable=True)
    
    # Forschungs-Fortschritt (0-100%)
    forschung_fortschritt = Column(Integer, default=0)
    
    # Forschungs-Punkte pro Tick (abhängig von Gebäuden)
    forschung_pro_tick = Column(Integer, default=10)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Helper: Tech-Tree Struktur laden
def get_tech_tree() -> list:
    """Gesamten Tech-Tree als Baumstruktur zurückgeben"""
    
    technologien = db.query(Technologie).all()
    
    # Nach Tech-Level sortieren
    technologien.sort(key=lambda t: t.tech_level)
    
    tree = []
    
    for tech in technologien:
        node = {
            "id": tech.id,
            "name": tech.name,
            "tech_level": tech.tech_level,
            "kategorie": tech.kategorie,
            "beschreibung": tech.beschreibung,
            "voraussetzungen": json.loads(tech.voraussetzungen) if tech.voraussetzungen else [],
            "freischaltungen": json.loads(tech.freischaltungen) if tech.freischaltungen else [],
            "forschungskosten": tech.forschungskosten,
            "effekt": json.loads(tech.effekt) if tech.effekt else {},
            "erforscht": False,  # Wird pro User gesetzt
            "verfügbar": len(json.loads(tech.voraussetzungen) if tech.voraussetzungen else []) == 0  # Keine Voraussetzungen = verfügbar
        }
        
        tree.append(node)
    
    return tree

# Helper: Prüfen ob Technologie erforschbar ist
def is_technologie_verfügbar(tech_id: int, user_id: int) -> bool:
    """Prüfen ob eine Technologie erforscht werden kann"""
    
    tech = db.query(Technologie).get(tech_id)
    
    if not tech:
        return False
    
    # Tech-Level des Users prüfen (über höchste erforschte Technologie)
    forschung = db.query(ForschungStatus).filter_by(user_id=user_id).first()
    
    if not forschung:
        return tech.tech_level == 0  # Nur Tech-Level 0 am Anfang
    
    erforschte = json.loads(forschung.erforschte_technologien) if forschung.erforschte_technologien else []
    
    # Alle Voraussetzungen müssen erfüllt sein
    voraussetzungen = json.loads(tech.voraussetzungen) if tech.voraussetzungen else []
    
    for req_id in voraussetzungen:
        if req_id not in erforschte:
            return False
    
    # Tech-Level darf nicht überschritten werden (max 2 Stufen voraus)
    max_erforscht_level = max([t.tech_level for t in db.query(Technologie).filter(Technologie.id.in_(erforschte)).all()], default=0)
    
    if tech.tech_level > max_erforscht_level + 20:
        return False
    
    return True

# Helper: Forschungs-Punkte pro Tick berechnen
def calculate_forschung_pro_tick(user_id: int) -> int:
    """Forschungs-Punkte pro Tick basierend auf Gebäuden berechnen"""
    
    forschung = db.query(ForschungStatus).filter_by(user_id=user_id).first()
    
    if not forschung:
        return 10  # Basis-Forschung
    
    province_id = forschung.province_id
    
    if not province_id:
        return 10
    
    # Forschungs-Gebäude zählen (Universität, Labor)
    from app.models import Building
    
    gebaeude = db.query(Building).filter_by(
        province_id=province_id,
        typ_id_in=[100, 101]  # Universität (100), Labor (101)
    ).all()
    
    forschung_bonus = 0
    
    for gebaeude in gebaeude:
        # Bonus aus Gebäude-Typ
        bonus = gebaeude.typ.spezial_eigenschaften.get("forschung_bonus", 0)
        forschung_bonus += bonus * gebaeude.stufe
    
    return 10 + forschung_bonus  # Basis + Bonus

# Helper: Technologie erforschen
def erforsche_technologie(user_id: int, tech_id: int) -> dict:
    """Technologie erforschen (startet Forschungs-Prozess)"""
    
    # Prüfen ob verfügbar
    if not is_technologie_verfügbar(tech_id, user_id):
        return {"success": False, "error": "Technologie nicht verfügbar"}
    
    tech = db.query(Technologie).get(tech_id)
    
    if not tech:
        return {"success": False, "error": "Technologie nicht gefunden"}
    
    # Forschung starten/aktualisieren
    forschung = db.query(ForschungStatus).filter_by(user_id=user_id).first()
    
    if not forschung:
        forschung = ForschungStatus(
            user_id=user_id,
            aktuelle_forschung_id=tech_id,
            forschung_pro_tick=calculate_forschung_pro_tick(user_id)
        )
        db.add(forschung)
    else:
        forschung.aktuelle_forschung_id = tech_id
    
    db.commit()
    
    return {"success": True, "message": f"Forschung von '{tech.name}' gestartet"}
```

---

## 📡 API Endpunkte für Forschung

### Forschung Router

```python
# app/api/v1/forschung.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/forschung/tech-tree")
async def get_tech_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gesamten Tech-Tree mit individuellem Status abrufen"""
    
    tree = get_tech_tree()
    
    # Individuellen Status setzen (erforscht, verfügbar)
    forschung = db.query(ForschungStatus).filter_by(user_id=current_user.id).first()
    
    erforschte = json.loads(forschung.erforschte_technologien) if forschung else []
    
    for node in tree:
        node["erforscht"] = node["id"] in erforschte
        
        if not node["erforscht"]:
            node["verfügbar"] = is_technologie_verfügbar(node["id"], current_user.id)
    
    return {"tech_tree": tree}

@router.get("/forschung/status")
async def get_forschung_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktuellen Forschungs-Fortschritt abrufen"""
    
    forschung = db.query(ForschungStatus).filter_by(user_id=current_user.id).first()
    
    if not forschung:
        return {
            "erforschte_technologien": [],
            "aktuelle_forschung": None,
            "forschung_fortschritt": 0,
            "forschung_pro_tick": 10
        }
    
    erforschte = json.loads(forschung.erforschte_technologien) if forschung.erforschte_technologien else []
    aktuelle_id = forschung.aktuelle_forschung_id
    
    aktuelle_tech = None
    if aktuelle_id:
        tech = db.query(Technologie).get(aktuelle_id)
        if tech:
            aktuelle_tech = {
                "id": tech.id,
                "name": tech.name,
                "forschungskosten": tech.forschungskosten
            }
    
    return {
        "erforschte_technologien": erforschte,
        "aktuelle_forschung": aktuelle_tech,
        "forschung_fortschritt": forschung.forschung_fortschritt,
        "forschung_pro_tick": forschung.forschung_pro_tick
    }

@router.post("/forschung/start")
async def start_forschung(
    data: ForschungStarten,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Forschung einer Technologie starten"""
    
    result = erforsche_technologie(current_user.id, data.tech_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "FORSCHUNG_START_FAILED", "message": result["error"]}
        )
    
    return {"message": result["message"]}

@router.get("/forschung/verfügbare")
async def get_verfügbare_technologien(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alle verfügbaren (aber noch nicht erforschten) Technologien auflisten"""
    
    tree = get_tech_tree()
    
    forschung = db.query(ForschungStatus).filter_by(user_id=current_user.id).first()
    erforschte = json.loads(forschung.erforschte_technologien) if forschung else []
    
    verfügbare = []
    
    for node in tree:
        if not node["erforscht"] and is_technologie_verfügbar(node["id"], current_user.id):
            verfügbare.append({
                "id": node["id"],
                "name": node["name"],
                "tech_level": node["tech_level"],
                "kategorie": node["kategorie"],
                "forschungskosten": node["forschungskosten"],
                "freischaltungen": node["freischaltungen"]
            })
    
    return {"verfügbare_technologien": verfügbare}

@router.post("/province/{province_id}/forschung/beschleunigen")
async def beschleunige_forschung(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Forschung beschleunigen (mit Ressourcen)"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    forschung = db.query(ForschungStatus).filter_by(user_id=current_user.id).first()
    
    if not forschung or not forschung.aktuelle_forschung_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_ACTIVE_RESEARCH", "message": "Keine aktive Forschung"}
        )
    
    # Beschleunigung kostet Ressourcen (z.B. 100 MIPS)
    if province.resources_mips < 100:
        raise HTTPException(
            status_code=400,
            detail={"code": "INSUFFICIENT_RESOURCES", "message": "Nicht genug MIPS"}
        )
    
    # 50% des aktuellen Fortschritts hinzufügen
    forschung.forschung_fortschritt = min(forschung.forschung_fortschritt + 50, 100)
    province.resources_mips -= 100
    
    db.commit()
    
    return {"message": "Forschung beschleunigt (+50% Fortschritt)"}
```

---

## ⏱️ Tick-Integration: Forschung pro Tick

### Forschungs-Fortschritt im Server-Tick

```python
# app/services/tick_manager.py - Erweitert um Forschung

async def execute_tick(self):
    """Einzelnen Tick verarbeiten (erweitert)"""
    
    # ... bestehende Logik ...
    
    # 6. Forschungs-Fortschritt aktualisieren
    await self.update_forschung_progress()

async def update_forschung_progress(self):
    """Forschungs-Fortschritt pro Tick berechnen"""
    
    forschungen = db.query(ForschungStatus).filter_by(aktuelle_forschung_id != None).all()
    
    for forschung in forschungen:
        tech = db.query(Technologie).get(forschung.aktuelle_forschung_id)
        
        if not tech:
            continue
        
        # Fortschritt erhöhen (Forschung pro Tick)
        forschung.forschung_fortschritt += forschung.forschung_pro_tick
        
        # Prüfen ob Forschung abgeschlossen
        if forschung.forschung_fortschritt >= tech.forschungskosten:
            # Forschung abgeschlossen!
            self.abschließen_forschung(forschung, tech)
        else:
            db.commit()

def abschließen_forschung(self, forschung: ForschungStatus, tech: Technologie):
    """Forschung abschließen und Freischaltungen anwenden"""
    
    # Technologie zu erforschten hinzufügen
    erforschte = json.loads(forschung.erforschte_technologien) if forschung.erforschte_technologien else []
    erforschte.append(tech.id)
    forschung.erforschte_technologien = json.dumps(erforschte)
    
    # Fortschritt zurücksetzen
    forschung.forschung_fortschritt = 0
    
    # Freischaltungen anwenden
    freischaltungen = json.loads(tech.freischaltungen) if tech.freischaltungen else []
    
    for fs in freischaltungen:
        typ = fs.get("typ")
        id = fs.get("id")
        
        if typ == "gebaeude":
            # Neues Gebäude freischalten (in Datenbank markieren als baubar)
            self.mark_gebaeude_babar(id, True)
        
        elif typ == "einheit":
            # Neue Einheit freischalten
            self.mark_einheit_verfügbar(id, True)
        
        elif typ == "ressource":
            # Neue Ressource verfügbar machen
            self.mark_ressource_verfügbar(id, True)
    
    # Effekt anwenden (z.B. Produktions-Boni)
    effekt = json.loads(tech.effekt) if tech.effekt else {}
    
    if "forschung_bonus" in effekt:
        # Forschungs-Gebäude Bonus erhöhen
        self.increase_forschung_bonus(effekt["forschung_bonus"])
    
    # Nachricht an User senden (WebSocket)
    self.broadcast_forschung_abgeschlossen(forschung.user_id, tech.name)

def broadcast_forschung_abgeschlossen(self, user_id: int, tech_name: str):
    """WebSocket Nachricht: Forschung abgeschlossen"""
    
    import json
    
    message = {
        "type": "forschung_abgeschlossen",
        "tech_name": tech_name,
        "tick": tick_manager.current_tick
    }
    
    # An User senden (über Redis Pub/Sub)
    redis_client.publish(
        f"wasteland:user:{user_id}",
        json.dumps(message)
    )
```

---

## 🖥️ Client-Side Forschung UI (JavaScript)

### Forschung Manager

```javascript
// js/game/forschung-manager.js

class ForschungManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Tech-Tree laden
    async loadTechTree() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/forschung/tech-tree`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderTechTree(data.tech_tree);
            }
        } catch (error) {
            console.error('Tech Tree Load Error:', error);
        }
    }

    // Tech-Tree im UI rendern (visueller Baum)
    renderTechTree(tree) {
        const container = document.getElementById('tech-tree-panel');
        
        if (!container) return;

        let html = '<h3>🔬 Tech-Tree</h3>';
        
        // Nach Tech-Level gruppieren
        const groups = {};
        
        for (const tech of tree) {
            const levelGroup = Math.floor(tech.tech_level / 20) * 20;
            
            if (!groups[levelGroup]) {
                groups[levelGroup] = [];
            }
            
            groups[levelGroup].push(tech);
        }
        
        // Gruppen rendern
        for (const [level, technologies] of Object.entries(groups)) {
            html += `<div class="tech-level" data-level="${level}">`;
            html += `<h4>Tech-Level ${level}-${parseInt(level) + 19}</h4>`;
            
            for (const tech of technologies) {
                const statusClass = tech.erforscht ? 'erforscht' : 
                                   tech.verfügbar ? 'verfügbar' : 'gesperrt';
                
                html += `
                    <div class="tech-node ${statusClass}" data-tech-id="${tech.id}">
                        <div class="tech-name">${tech.name}</div>
                        
                        ${!tech.erforscht ? `
                            <div class="tech-info">
                                <span>Kosten: ${tech.forschungskosten} FP</span>
                                ${tech.voraussetzungen.length > 0 ? `<br><small>Vorraussetzung: ${tech.voraussetzungen.length} Techs</small>` : ''}
                            </div>
                        ` : '<div class="erforscht-badge">✅ Erforscht</div>'}
                        
                        ${tech.verfügbar && !tech.erforscht ? `
                            <button onclick="forschung.starten(${tech.id})">Forschen</button>
                        ` : ''}
                    </div>
                `;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // Forschung starten
    async starten(techId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/forschung/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ tech_id: techId })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(data.message);
                await this.loadTechTree();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Start Forschung Error:', error);
        }
    }

    // Forschungs-Fortschritt anzeigen
    async loadForschungStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/forschung/status`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderForschungStatus(data);
            }
        } catch (error) {
            console.error('Forschung Status Error:', error);
        }
    }

    renderForschungStatus(data) {
        const container = document.getElementById('forschung-status');
        
        if (!container) return;

        let html = '<h4>📊 Aktueller Forschungs-Fortschritt</h4>';
        
        if (data.aktuelle_forschung) {
            const tech = data.aktuelle_forschung;
            
            html += `
                <div class="forschung-progress">
                    <p><strong>${tech.name}</strong></p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.forschung_fortschritt}%"></div>
                    </div>
                    <p>${data.forschung_fortschritt}% (${tech.forschungskosten} FP benötigt)</p>
                    <p>Forschung pro Tick: ${data.forschung_pro_tick} FP</p>
                </div>
            `;
        } else {
            html += '<p class="no-research">Keine aktive Forschung.</p>';
        }

        container.innerHTML = html;
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `forschung-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        this.loadTechTree();
        this.loadForschungStatus();
        
        // Periodisch aktualisieren (alle 60s = pro Tick)
        setInterval(() => {
            this.loadTechTree();
            this.loadForschungStatus();
        }, 60000);
    }
}

// Singleton
const forschung = new ForschungManager();

export default forschung;
```

---

## 🧪 Testing Forschungs-System

### Unit Tests

```python
# tests/services/test_forschung_service.py
import pytest

def test_get_tech_tree():
    """Testet Tech-Tree Struktur"""
    
    from app.models import get_tech_tree
    
    tree = get_tech_tree()
    
    assert isinstance(tree, list)
    assert len(tree) > 0
    
    # Nach Tech-Level sortiert
    levels = [t.tech_level for t in tree]
    assert levels == sorted(levels)

def test_is_technologie_verfügbar():
    """Testet Verfügbarkeit einer Technologie"""
    
    from app.models import is_technologie_verfügbar
    
    # Tech-Level 0 sollte immer verfügbar sein
    assert is_technologie_verfügbar(1, 1) is True  # Annahme: ID 1 = Tech-Level 0

def test_calculate_forschung_pro_tick():
    """Testet Forschungs-Punkte pro Tick Berechnung"""
    
    from app.models import calculate_forschung_pro_tick
    
    # Basis-Forschung sollte >= 10 sein
    punkte = calculate_forschung_pro_tick(1)
    
    assert punkte >= 10

def test_erforsche_technologie():
    """Testet Forschungs-Start"""
    
    from app.models import erforsche_technologie
    
    result = erforsche_technologie(1, 1)
    
    assert result["success"] is True

def test_forschung_abschließen():
    """Testet Forschungs-Abschluss"""
    
    from app.services.tick_manager import TickManager
    
    tick_mgr = TickManager()
    
    # Mock Forschung und Technologie
    forschung = mocker.Mock(user_id=1, forschung_fortschritt=100)
    tech = mocker.Mock(id=1, name="TestTech", freischaltungen="[]", effekt="{}")
    
    # Abschließen sollte keine Fehler werfen
    tick_mgr.abschließen_forschung(forschung, tech)
```

---

## 🎯 Best Practices

1. **Tech-Tree hierarchisch** - Niedrige Levels zuerst, hohe Level später
2. **Voraussetzungen prüfen** - Nicht alle Techs gleichzeitig verfügbar
3. **Forschungs-Gebäude nutzen** - Universität/Labor beschleunigen Forschung
4. **Beschleunigung mit Ressourcen** - Schneller forschen kostet MIPS
5. **WebSocket Benachrichtigung** - User sofort informieren wenn Forschung abgeschlossen

---

**Forschungs-System ermöglicht progressiven Tech-Fortschritt mit Freischaltungen für Gebäude, Einheiten und Ressourcen!**
