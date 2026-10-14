# ⚔️ Kampfsystem & Kriegsführung

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das Kampfsystem: Einheiten-Kämpfe, Belagerungen, Verluste und Kriegsführung zwischen Provinzen.

---

## 🎯 Ziele

1. **Realistische Kampfberechnung** - Einheiten vs. Verteidigung mit Faktoren
2. **Belagerungsmechanik** - Provinzen können erobert werden
3. **Verluste & Nachschub** - Einheiten können zerstört oder verwundet werden
4. **Kriegsführung** - Kriegserklärung, Frieden, Eroberung

---

## 🏗️ Kampfsystem Architektur

### Kampf-Phasen

```
1. Angriff starten (Player Action)
        ↓
2. Kampfberechnung (Server)
   - Angreifer-Stärke vs. Verteidiger-Stärke
   - Terrain-Boni/-Malus
   - Zufallsfaktor (±10%)
        ↓
3. Ergebnisse berechnen
   - Verluste Angreifer
   - Verluste Verteidiger
        ↓
4. Ergebnis anwenden
   - Gebäude zerstört?
   - Provinz erobert?
        ↓
5. State an alle Clients broadcasten (WebSocket)
```

---

## 📊 Datenbank-Schema für Kampf

### Einheiten & Kampf-Logs

```python
# app/models.py - Kampf-relevante Modelle

class Einheit(Base):
    """Militärische Einheit"""
    
    __tablename__ = "einheiten"
    
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey("provinzen.id"))
    typ_id = Column(Integer, ForeignKey("einheiten_typen.id"))
    
    # Status
    status = Column(String(50), default="stationiert")  # stationiert, unterwegs, im_kampf
    stufe = Column(Integer, default=1)
    
    # Stärke (basierend auf Typ + Stufe)
    angreifer_staerke = Column(Integer, default=0)
    verteidiger_staerke = Column(Integer, default=0)
    
    # Verluste (0-100%)
    verluste_prozent = Column(Integer, default=0)
    
    # Bewegung (wenn unterwegs)
    ziel_provinz_id = Column(Integer, ForeignKey("provinzen.id"))
    fortschritt = Column(Integer, default=0)  # 0-100%
    
    # Kampf-Historie
    kaelte_resistenz = Column(Integer, default=0)  # Spezial-Boni
    
class KampfLog(Base):
    """Kampf-Historie"""
    
    __tablename__ = "kampf_logs"
    
    id = Column(Integer, primary_key=True)
    tick = Column(Integer, nullable=False)  # Welcher Tick
    
    angreifer_provinz_id = Column(Integer, ForeignKey("provinzen.id"))
    verteidiger_provinz_id = Column(Integer, ForeignKey("provinzen.id"))
    
    # Kampf-Ergebnis
    ergebnis = Column(String(50))  # angreifer_sieg, verteidiger_sieg, unentschieden
    
    # Verluste
    angreifer_verluste = Column(Integer, default=0)  # Prozent
    verteidiger_verluste = Column(Integer, default=0)  # Prozent
    
    # Details (JSON)
    details = Column(Text)  # JSON: welche Einheiten wie viele Verluste
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)

class ProvinzVerteidigung(Base):
    """Verteidigungs-Werte einer Provinz"""
    
    __tablename__ = "provinz_verteidigung"
    
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey("provinzen.id"), unique=True)
    
    # Gebäude-basierte Verteidigung
    festung_stärke = Column(Integer, default=0)  # Festungen bieten Verteidigung
    
    # Einheit-basierte Verteidigung
    einheiten_verteidigung = Column(Integer, default=0)
    
    # Terrain-Boni
    terrain_verteidigungs_bonus = Column(Integer, default=0)  # z.B. Gebirge: +20%
    
    # Gesamte Verteidigung (berechnet)
    gesamt_verteidigung = Column(Integer, default=0)

# Helper: Kampf-Stärke berechnen
def calculate_kampf_staerke(einheiten_liste: list) -> dict:
    """Gesamte Kampf-Stärke einer Einheiten-Liste berechnen"""
    
    gesamt_angriff = 0
    gesamt_verteidigung = 0
    
    for einheit in einheiten_liste:
        typ = einheit.typ
        
        # Basis-Stärke aus Typ
        basis_angriff = typ.angreifer_staerke or 0
        basis_verteidigung = typ.verteidiger_staerke or 0
        
        # Stufe multiplizieren
        stufe_faktor = 1 + (einheit.stufe - 1) * 0.2  # +20% pro Stufe
        
        gesamt_angriff += basis_angriff * stufe_faktor
        gesamt_verteidigung += basis_verteidigung * stufe_faktor
    
    return {
        "angriff": int(gesamt_angriff),
        "verteidigung": int(gesamt_verteidigung)
    }

# Helper: Kampf-Ergebnis berechnen
def calculate_kampf_ergebnis(angreifer_staerke: dict, verteidiger_staerke: dict, terrain_bonus: int = 0) -> dict:
    """Kampf-Ergebnis berechnen (deterministisch mit Zufallsfaktor)"""
    
    import random
    
    # Angreifer hat kleinen Nachteil (Verteidiger-Boni)
    angreifer_effektiv = angreifer_staerke["angriff"] * 0.9
    
    # Verteidiger Terrain-Boni
    verteidiger_effektiv = (verteidiger_staerke["verteidigung"] + verteidiger_staerke.get("festung", 0)) * (1 + terrain_bonus / 100.0)
    
    # Zufallsfaktor (±10%)
    zufall_faktor = 0.9 + random.random() * 0.2
    
    angreifer_final = angreifer_effektiv * zufall_faktor
    verteidiger_final = verteidiger_effektiv
    
    # Verhältnis bestimmen
    if angreifer_final > verteidiger_final * 1.5:
        # Deutlicher Sieg Angreifer
        ergebnis = "angreifer_sieg"
        angreifer_verluste = random.randint(5, 20)
        verteidiger_verluste = random.randint(40, 80)
    
    elif angreifer_final > verteidiger_final:
        # Knapper Sieg Angreifer
        ergebnis = "angreifer_sieg"
        angreifer_verluste = random.randint(15, 35)
        verteidiger_verluste = random.randint(20, 50)
    
    elif angreifer_final > verteidiger_final * 0.7:
        # Unentschieden / Pyrrhussieg
        ergebnis = "unentschieden"
        angreifer_verluste = random.randint(25, 45)
        verteidiger_verluste = random.randint(25, 45)
    
    else:
        # Sieg Verteidiger
        ergebnis = "verteidiger_sieg"
        angreifer_verluste = random.randint(30, 60)
        verteidiger_verluste = random.randint(5, 20)
    
    return {
        "ergebnis": ergebnis,
        "angreifer_verluste": angreifer_verluste,
        "verteidiger_verluste": verteidiger_verluste,
        "angreifer_final": int(angreifer_final),
        "verteidiger_final": int(verteidiger_final)
    }
```

---

## 📡 API Endpunkte für Kampf

### Kampf Router

```python
# app/api/v1/kampf.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/province/{province_id}/angreifen")
async def angreifen(
    province_id: int,
    data: AngriffRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provinz angreifen (militärischer Angriff)"""
    
    # Angreifer-Provinz prüfen
    angreifer_provinz = db.query(Province).filter_by(id=data.von_provinz_id, owner_id=current_user.id).first()
    
    if not angreifer_provinz:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Sie sind nicht Owner dieser Provinz"})
    
    # Ziel-Provinz prüfen
    ziel_provinz = db.query(Province).get(province_id)
    
    if not ziel_provinz:
        raise HTTPException(status_code=404, detail={"code": "PROVINZ_NOT_FOUND", "message": "Ziel-Provinz nicht gefunden"})
    
    # Diplomatie prüfen (Krieg erforderlich)
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=data.von_provinz_id,
        ziel_provinz_id=province_id
    ).first()
    
    if not relation or relation.status != -2:  # Nicht Krieg
        raise HTTPException(
            status_code=400,
            detail={"code": "NOT_AT_WAR", "message": "Kein aktiver Krieg mit dieser Provinz"}
        )
    
    # Einheiten der Angreifer-Provinz laden
    einheiten = db.query(Einheit).filter_by(province_id=data.von_provinz_id, status="stationiert").all()
    
    if not einheiten:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_UNITS", "message": "Keine Einheiten verfügbar"}
        )
    
    # Einheiten zur Ziel-Provinz bewegen (simuliert Angriff)
    for einheit in einheiten:
        einheit.status = "im_kampf"
        einheit.ziel_provinz_id = province_id
        einheit.fortschritt = 100  # Sofortiger Angriff
    
    db.commit()
    
    # Kampf berechnen (Server-side)
    kampf_ergebnis = await execute_kampf(data.von_provinz_id, province_id, einheiten, db)
    
    # Kampf-Log erstellen
    kampf_log = KampfLog(
        tick=tick_manager.current_tick,
        angreifer_provinz_id=data.von_provinz_id,
        verteidiger_provinz_id=province_id,
        ergebnis=kampf_ergebnis["ergebnis"],
        angreifer_verluste=kampf_ergebnis["angreifer_verluste"],
        verteidiger_verluste=kampf_ergebnis["verteidiger_verluste"],
        details=json.dumps(kampf_ergebnis.get("details", {}))
    )
    
    db.add(kampf_log)
    db.commit()
    
    # Ergebnisse anwenden (Verluste, eventuelle Eroberung)
    await apply_kampf_ergebnisse(kampf_ergebnis, data.von_provinz_id, province_id, einheiten, db)
    
    return {
        "message": "Angriff ausgeführt",
        "ergebnis": kampf_ergebnis["ergebnis"],
        "angreifer_verluste": kampf_ergebnis["angreifer_verluste"],
        "verteidiger_verluste": kampf_ergebnis["verteidiger_verluste"]
    }

@router.post("/province/{province_id}/belagern")
async def belagern(
    province_id: int,
    data: BelagerungRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provinz belagern (langfristige Einschließung)"""
    
    angreifer_provinz = db.query(Province).filter_by(id=data.von_provinz_id, owner_id=current_user.id).first()
    
    if not angreifer_provinz:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    ziel_provinz = db.query(Province).get(province_id)
    
    if not ziel_provinz:
        raise HTTPException(status_code=404, detail={"code": "PROVINZ_NOT_FOUND", "message": "Nicht gefunden"})
    
    # Belagerung erfordert Krieg + angrenzende Provinz
    if not is_provinz_angrenzend(data.von_provinz_id, province_id):
        raise HTTPException(
            status_code=400,
            detail={"code": "NOT_ADJACENT", "message": "Provinzen sind nicht angrenzend"}
        )
    
    # Belagerung starten (Ressourcen-Verbrauch pro Tick)
    belagerung = Belagerung(
        angreifer_provinz_id=data.von_provinz_id,
        ziel_provinz_id=province_id,
        start_tick=tick_manager.current_tick,
        fortgeschrittene_ticks=0
    )
    
    db.add(belagerung)
    db.commit()
    
    return {"message": "Belagerung gestartet", "belagerung_id": belagerung.id}

@router.get("/province/{province_id}/kampf_status")
async def get_kampf_status(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktueller Kampf-Status einer Provinz abrufen"""
    
    # Aktive Belagerungen
    belagerungen = db.query(Belagerung).filter_by(ziel_provinz_id=province_id, status="aktiv").all()
    
    # Letzte Kämpfe
    letzte_kämpfe = db.query(KampfLog).filter_by(verteidiger_provinz_id=province_id).order_by(KampfLog.tick.desc()).limit(10).all()
    
    # Einheiten in der Provinz
    einheiten = db.query(Einheit).filter_by(province_id=province_id).all()
    
    return {
        "belagerungen": [{
            "id": b.id,
            "angreifer_provinz_id": b.angreifer_provinz_id,
            "fortgeschrittene_ticks": b.fortgeschrittene_ticks
        } for b in belagerungen],
        "letzte_kämpfe": [{
            "tick": k.tick,
            "ergebnis": k.ergebnis,
            "angreifer_verluste": k.angreifer_verluste,
            "verteidiger_verluste": k.verteidiger_verluste
        } for k in letzte_kämpfe],
        "einheiten": [{
            "id": e.id,
            "typ": e.typ.name if e.typ else None,
            "status": e.status,
            "verluste_prozent": e.verluste_prozent
        } for e in einheiten]
    }
```

---

## 🧮 Kampf-Berechnung (Server-Side)

### Execute Kampf Logic

```python
# app/services/kampf_service.py

async def execute_kampf(angreifer_provinz_id: int, verteidiger_provinz_id: int, angreifer_einheiten: list, db) -> dict:
    """Kampf zwischen zwei Provinzen berechnen"""
    
    # Verteidiger-Einheiten laden
    verteidiger_einheiten = db.query(Einheit).filter_by(province_id=verteidiger_provinz_id, status="stationiert").all()
    
    # Angreifer-Stärke berechnen
    angreifer_staerke = calculate_kampf_staerke(angreifer_einheiten)
    
    # Verteidiger-Stärke berechnen (inkl. Festungen, Terrain)
    verteidiger_staerke = calculate_kampf_staerke(verteidiger_einheiten)
    
    # Verteidigungs-Gebäude der Provinz
    verteidigung = db.query(ProvinzVerteidigung).filter_by(province_id=verteidiger_provinz_id).first()
    
    if verteidigung:
        verteidiger_staerke["festung"] = verteidigung.gesamt_verteidigung
    
    # Terrain-Boni für Verteidiger
    ziel_provinz = db.query(Province).get(verteidiger_provinz_id)
    terrain_bonus = get_terrain_verteidigungs_bonus(ziel_provinz.terrain_typ_id)
    
    # Kampf-Ergebnis berechnen
    ergebnis = calculate_kampf_ergebnis(angreifer_staerke, verteidiger_staerke, terrain_bonus)
    
    # Details: Welche Einheiten wie viele Verluste
    details = calculate_einheiten_verluste(angreifer_einheiten, verteidiger_einheiten, ergebnis)
    ergebnis["details"] = details
    
    return ergebnis

async def apply_kampf_ergebnisse(ergebnis: dict, angreifer_provinz_id: int, verteidiger_provinz_id: int, angreifer_einheiten: list, db):
    """Kampf-Ergebnisse auf Datenbank anwenden"""
    
    # Angreifer-Verluste anwenden
    for i, einheit in enumerate(angreifer_einheiten):
        verlust_prozent = ergebnis["details"]["angreifer"].get(str(einheit.id), 0)
        einheit.verluste_prozent = min(einheit.verluste_prozent + verlust_prozent, 100)
        
        # Wenn Einheit vollständig zerstört → löschen
        if einheit.verluste_prozent >= 100:
            db.delete(einheit)
        else:
            # Verwundete Einheiten zurück zur Heimat-Provinz
            einheit.status = "stationiert"
            einheit.ziel_provinz_id = None
    
    # Verteidiger-Verluste anwenden
    verteidiger_einheiten = db.query(Einheit).filter_by(province_id=verteidiger_provinz_id, status="stationiert").all()
    
    for einheit in verteidiger_einheiten:
        verlust_prozent = ergebnis["details"]["verteidiger"].get(str(einheit.id), 0)
        einheit.verluste_prozent = min(einheit.verluste_prozent + verlust_prozent, 100)
        
        if einheit.verluste_prozent >= 100:
            db.delete(einheit)
    
    # Wenn Angreifer gewonnen → Provinz kann erobert werden
    if ergebnis["ergebnis"] == "angreifer_sieg" and ergebnis["verteidiger_verluste"] > 60:
        # Provinz wechseln (Owner wird Angreifer)
        ziel_provinz = db.query(Province).get(verteidiger_provinz_id)
        
        # Optional: Eroberung nur wenn alle Verteidiger-Einheiten zerstört
        if all(e.verluste_prozent >= 100 for e in verteidiger_einheiten):
            ziel_provinz.owner_id = db.query(Einheit).first().province_id  # Vereinfacht: Erster Angreifer
            
            # Diplomatie zurücksetzen
            relation = db.query(Diplomatie).filter_by(
                von_provinz_id=angreifer_provinz_id,
                ziel_provinz_id=verteidiger_provinz_id
            ).first()
            
            if relation:
                relation.status = 0  # Neutral nach Eroberung
    
    db.commit()

def calculate_einheiten_verluste(angreifer: list, verteidiger: list, ergebnis: dict) -> dict:
    """Verluste pro Einheit berechnen"""
    
    details = {"angreifer": {}, "verteidiger": {}}
    
    # Angreifer-Verluste verteilen (random auf Einheiten)
    angreifer_gesamt = ergebnis["angreifer_verluste"]
    
    for einheit in angreifer:
        anteil = random.randint(5, 30)  # 5-30% pro Einheit
        details["angreifer"][str(einheit.id)] = anteil
    
    # Verteidiger-Verluste verteilen
    verteidiger_gesamt = ergebnis["verteidiger_verluste"]
    
    for einheit in verteidiger:
        anteil = random.randint(5, 40)
        details["verteidiger"][str(einheit.id)] = anteil
    
    return details

def get_terrain_verteidigungs_bonus(terrain_typ_id: int) -> int:
    """Terrain-spezifischer Verteidigungs-Boni"""
    
    terrain_boni = {
        1: 0,     # Grasland: Kein Bonus
        2: 10,    # Steppe: +10%
        3: 20,    # Gebirge: +20%
        4: 15,    # Wald: +15%
        5: 25,    # Sumpf: +25% (schwer zu durchqueren)
        6: 5,     # Wüste: +5%
    }
    
    return terrain_boni.get(terrain_typ_id, 0)

def is_provinz_angrenzend(provinz_a_id: int, provinz_b_id: int) -> bool:
    """Prüfen ob zwei Provinzen angrenzen"""
    
    # Koordinaten der Provinzen laden
    provinz_a = db.query(Province).get(provinz_a_id)
    provinz_b = db.query(Province).get(provinz_b_id)
    
    if not provinz_a or not provinz_b:
        return False
    
    # Einfache Distanz-Berechnung (x,y Koordinaten)
    dx = abs(provinz_a.x - provinz_b.x)
    dy = abs(provinz_a.y - provinz_b.y)
    
    # Angrenzend wenn Distanz <= 1 (nachbarn)
    return dx <= 1 and dy <= 1 and (dx + dy) > 0
```

---

## 🖥️ Client-Side Kampf UI (JavaScript)

### Kampf Manager

```javascript
// js/game/kampf-manager.js

class KampfManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Angriff starten
    async angreifen(vonProvinzId, zielProvinzId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/province/${zielProvinzId}/angreifen`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ von_provinz_id: vonProvinzId })
            });

            if (response.ok) {
                const data = await response.json();
                this.showKampfResult(data);
                await this.loadKampfStatus(zielProvinzId);
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Angreifen Error:', error);
        }
    }

    // Kampf-Ergebnis anzeigen
    showKampfResult(data) {
        const modal = document.getElementById('kampf-result-modal');
        
        if (!modal) return;

        const ergebnisIcons = {
            'angreifer_sieg': '🏆',
            'verteidiger_sieg': '🛡️',
            'unentschieden': '⚖️'
        };

        modal.innerHTML = `
            <h3>Kampf Ergebnis</h3>
            <div class="ergebnis-icon">${ergebnisIcons[data.ergebnis] || '⚔️'}</div>
            <p class="ergebnis-text">${this.getErgebnisText(data.ergebnis)}</p>
            
            <div class="verluste">
                <p>🔴 Ihre Verluste: ${data.angreifer_verluste}%</p>
                <p>🔵 Gegner Verluste: ${data.verteidiger_verluste}%</p>
            </div>
            
            <button onclick="document.getElementById('kampf-result-modal').style.display='none'">Schließen</button>
        `;

        modal.style.display = 'block';
    }

    getErgebnisText(ergebnis) {
        const texts = {
            'angreifer_sieg': 'Sieg! Ihre Truppen haben gewonnen.',
            'verteidiger_sieg': 'Niederlage! Ihre Truppen wurden zurückgeschlagen.',
            'unentschieden': 'Unentschieden! Beide Seiten haben schwere Verluste erlitten.'
        };
        
        return texts[ergebnis] || 'Kampf unentschieden';
    }

    // Kampf-Status laden
    async loadKampfStatus(provinzId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/province/${provinzId}/kampf_status`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderKampfStatus(data);
            }
        } catch (error) {
            console.error('Kampf Status Error:', error);
        }
    }

    renderKampfStatus(data) {
        const container = document.getElementById('kampf-panel');
        
        if (!container) return;

        let html = '<h3>⚔️ Kampf-Status</h3>';
        
        // Belagerungen
        if (data.belagerungen && data.belagerungen.length > 0) {
            html += '<div class="belagerung-list">';
            html += '<h4>🏰 Aktive Belagerungen</h4>';
            
            for (const bel of data.belagerungen) {
                html += `<p>Belagerung von Provinz ${bel.angreifer_provinz_id}: ${bel.fortgeschrittene_ticks} Ticks</p>`;
            }
            
            html += '</div>';
        }

        // Letzte Kämpfe
        if (data.letzte_kämpfe && data.letzte_kämpfe.length > 0) {
            html += '<div class="kampf-historie">';
            html += '<h4>📜 Letzte Kämpfe</h4>';
            
            for (const kampf of data.letzte_kämpfe) {
                const icon = kampf.ergebnis === 'angreifer_sieg' ? '🏆' : 
                            kampf.ergebnis === 'verteidiger_sieg' ? '🛡️' : '⚖️';
                
                html += `
                    <div class="kampf-eintrag">
                        <span>${icon}</span> Tick #${kampf.tick} - 
                        Verluste: ${kampf.angreifer_verluste}% / ${kampf.verteidiger_verluste}%
                    </div>
                `;
            }
            
            html += '</div>';
        }

        // Einheiten
        if (data.einheiten && data.einheiten.length > 0) {
            html += '<div class="einheiten-list">';
            html += '<h4>👥 Einheiten in Provinz</h4>';
            
            for (const einheit of data.einheiten) {
                const verlustColor = einheit.verluste_prozent > 50 ? '#ff0000' : 
                                    einheit.verluste_prozent > 20 ? '#ff8c00' : '#4caf50';
                
                html += `
                    <div class="einheit-eintrag">
                        ${einheit.typ || 'Unbekannt'} - Status: ${einheit.status} 
                        <span style="color: ${verlustColor}">(${einheit.verluste_prozent}% Verlust)</span>
                    </div>
                `;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `kampf-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        // Kampf-Status pro Tick aktualisieren (WebSocket oder Polling)
        setInterval(() => {
            this.loadKampfStatus(/* aktuelle Provinz */);
        }, 60000); // Alle 60s
    }
}

// Singleton
const kampf = new KampfManager();

export default kampf;
```

---

## 🧪 Testing Kampfsystem

### Unit Tests

```python
# tests/services/test_kampf_service.py
import pytest

@pytest.fixture
def kampf_service():
    from app.services.kampf_service import KampfService
    
    return KampfService()

def test_calculate_kampf_staerke():
    """Testet Kampf-Stärke Berechnung"""
    
    from app.services.kampf_service import calculate_kampf_staerke
    
    # Mock Einheiten
    einheiten = [
        mocker.Mock(stufe=1, typ=mocker.Mock(angreifer_staerke=100, verteidiger_staerke=50)),
        mocker.Mock(stufe=2, typ=mocker.Mock(angreifer_staerke=100, verteidiger_staerke=50))
    ]
    
    staerke = calculate_kampf_staerke(einheiten)
    
    assert staerke["angriff"] > 0
    assert staerke["verteidigung"] > 0

def test_calculate_kampf_ergebnis_sieg():
    """Testet Kampf-Ergebnis bei klarem Sieg"""
    
    from app.services.kampf_service import calculate_kampf_ergebnis
    
    ergebnis = calculate_kampf_ergebnis(
        angreifer_staerke={"angriff": 200, "verteidigung": 50},
        verteidiger_staerke={"verteidigung": 50, "festung": 0}
    )
    
    assert ergebnis["ergebnis"] in ["angreifer_sieg", "unentschieden"]
    assert 0 <= ergebnis["angreifer_verluste"] <= 50
    assert 0 <= ergebnis["verteidiger_verluste"] <= 80

def test_get_terrain_verteidigungs_bonus():
    """Testet Terrain-Verteidigungs-Boni"""
    
    from app.services.kampf_service import get_terrain_verteidigungs_bonus
    
    assert get_terrain_verteidigungs_bonus(1) == 0   # Grasland
    assert get_terrain_verteidigungs_bonus(3) == 20  # Gebirge
    assert get_terrain_verteidigungs_bonus(5) == 25  # Sumpf

def test_is_provinz_angrenzend():
    """Testet Provinz-Nachbarschaftsprüfung"""
    
    from app.services.kampf_service import is_provinz_angrenzend
    
    # Mock Provinzen mit benachbarten Koordinaten
    provinz_a = mocker.Mock(x=10, y=10)
    provinz_b = mocker.Mock(x=11, y=10)  # Direkt rechts
    
    assert is_provinz_angrenzend(provinz_a, provinz_b) is True
    
    # Nicht benachbart
    provinz_c = mocker.Mock(x=20, y=20)
    
    assert is_provinz_angrenzend(provinz_a, provinz_c) is False
```

---

## 🎯 Best Practices

1. **Server-Side Berechnung** - Client niemals Vertrauen (Anti-Cheat)
2. **Deterministisch + Zufall** - Gleiche Bedingungen = ähnliches Ergebnis (±10%)
3. **Verluste pro Einheit** - Nicht pauschal, sondern individuell
4. **Kampf-Historie speichern** - Für Statistiken und Audit-Log
5. **Belagerung langsam** - Keine sofortige Eroberung, sondern Prozess

---

**Kampfsystem ermöglicht realistische Kämpfe mit Verlusten, Belagerungen und Eroberungen!**
