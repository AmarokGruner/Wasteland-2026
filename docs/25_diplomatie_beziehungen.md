# 🤝 Diplomatie & Provinz-Beziehungen

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das Diplomatie-System für Beziehungen zwischen Provinzen: Allianzen, Kriege, Verträge und neutrale Beziehungen.

---

## 🎯 Ziele

1. **Dynamische Beziehungen** - Provinzen können sich anfreunden oder bekriegen
2. **Vertragssystem** - Formelle Abkommen zwischen Provinzen
3. **Konfliktlösung** - Friedliche und militärische Lösungen
4. **Diplomatie-API** - Vollständige REST-Schnittstelle

---

## 🏗️ Diplomatie-Status

### Mögliche Beziehungen

```
Neutral (Standard)
    │
    ├──→ Allianz (Freundschaft, gemeinsame Verteidigung)
    │       │
    │       └──→ Militärbündnis (Gemeinsame Angriffe erlaubt)
    │
    ├──→ Spannungen (Handels-Sanktionen, Grenzkonflikte)
    │       │
    │       └──→ Krieg (Offensive erlaubt)
    │
    └──→ Vasallität (Unterordnung unter stärkere Provinz)
```

### Status-Übersicht

| Status | ID | Beschreibung | Aktionen Erlaubt |
|--------|----|--------------|------------------|
| **Neutral** | 0 | Keine besondere Beziehung | Handel, Migration |
| **Freundschaft** | 1 | Positive Beziehung | Gemeinsame Forschung, Handel |
| **Allianz** | 2 | Formelles Bündnis | Gemeinsame Verteidigung |
| **Militärbündnis** | 3 | Vollständiges Bündnis | Gemeinsame Angriffe, Truppenstationierung |
| **Spannungen** | -1 | Negative Beziehung | Keine besonderen Aktionen |
| **Krieg** | -2 | Offener Konflikt | Angriffe, Belagerungen |
| **Vasall** | -3 | Unterordnung | Keine eigenständigen Aktionen |

---

## 📊 Datenbank-Schema

### Diplomatie Tabelle

```python
# app/models.py - Diplomatie Modell

class Diplomatie(Base):
    """Diplomatische Beziehung zwischen zwei Provinzen"""
    
    __tablename__ = "diplomatie"
    
    id = Column(Integer, primary_key=True)
    
    # Provinz ID (initiiert die Beziehung)
    von_provinz_id = Column(Integer, ForeignKey("provinzen.id"), nullable=False)
    
    # Zielprovinz ID (Beziehung gilt für diese Provinz)
    ziel_provinz_id = Column(Integer, ForeignKey("provinzen.id"), nullable=False)
    
    # Status der Beziehung (-3 bis 3)
    status = Column(Integer, default=0, nullable=False)
    
    # Beziehungswert (0-100, höher = besser)
    beziehungswert = Column(Integer, default=50)
    
    # Verträge (JSON)
    vertraege = Column(Text, default="[]")
    
    # Letzter Austausch (Timestamp)
    letzter_austausch = Column(DateTime, default=datetime.utcnow)
    
    # Erstellt am
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Aktualisiert am
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Eindeutige Einschränkung (jede Provinz-Paarung nur einmal)
    __table_args__ = (
        UniqueConstraint('von_provinz_id', 'ziel_provinz_id', name='uq_diplomatie_pair'),
    )

# Enum für Diplomatie-Status (optional, als Integer gespeichert)
class DiplomatieStatus:
    VASALL = -3
    KRIEG = -2
    SPANNUNGEN = -1
    NEUTRAL = 0
    FREUNDSCHAFT = 1
    ALLIANZ = 2
    MILITAER_BUENDNIS = 3

# Helper-Funktion: Status-Name aus ID
def get_diplomatie_status_name(status_id: int) -> str:
    """Diplomatie-Status ID in lesbaren Namen umwandeln"""
    
    status_map = {
        -3: "Vasall",
        -2: "Krieg",
        -1: "Spannungen",
        0: "Neutral",
        1: "Freundschaft",
        2: "Allianz",
        3: "Militärbündnis"
    }
    
    return status_map.get(status_id, "Unbekannt")

# Helper-Funktion: Erlaubte Aktionen basierend auf Status
def get_erlaubte_aktionen(status_id: int) -> list:
    """Liste erlaubter Aktionen für Diplomatie-Status"""
    
    aktionen_map = {
        -3: ["keine"],  # Vasall kann keine eigenständigen Aktionen
        -2: ["angreifen", "belagern"],  # Krieg: Offensive erlaubt
        -1: ["handels_sanktion", "grenzkonflikt"],  # Spannungen
        0: ["handeln", "migrieren"],  # Neutral: Basis-Aktionen
        1: ["handeln", "migrieren", "gemeinsame_forschung"],  # Freundschaft
        2: ["handeln", "migrieren", "gemeinsame_verteidigung"],  # Allianz
        3: ["handeln", "migrieren", "gemeinsame_verteidigung", "gemeinsamer_angriff", "truppen_stationieren"]  # Militärbündnis
    }
    
    return aktionen_map.get(status_id, [])
```

---

## 📡 API Endpunkte für Diplomatie

### Diplomatie Router

```python
# app/api/v1/diplomatie.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/diplomatie/")
async def list_diplomacy_relations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alle Diplomatie-Beziehungen des Spielers auflisten"""
    
    # Alle Provinzen des Users
    provinces = db.query(Province).filter_by(owner_id=current_user.id).all()
    
    relations = []
    
    for province in provinces:
        # Alle Beziehungen dieser Provinz laden
        diplomacies = db.query(Diplomatie).filter_by(von_provinz_id=province.id).all()
        
        for dip in diplomacies:
            ziel_provinz = db.query(Province).get(dip.ziel_provinz_id)
            
            if ziel_provinz:
                relations.append({
                    "id": dip.id,
                    "von_provinz": {
                        "id": province.id,
                        "name": province.name
                    },
                    "ziel_provinz": {
                        "id": ziel_provinz.id,
                        "name": ziel_provinz.name,
                        "owner_id": ziel_provinz.owner_id
                    },
                    "status": dip.status,
                    "status_name": get_diplomatie_status_name(dip.status),
                    "beziehungswert": dip.beziehungswert,
                    "vertraege": json.loads(dip.vertraege) if dip.vertraege else [],
                    "erlaubte_aktionen": get_erlaubte_aktionen(dip.status)
                })
    
    return {"relations": relations}

@router.get("/diplomatie/{von_provinz_id}/{ziel_provinz_id}")
async def get_diplomacy_relation(
    von_provinz_id: int,
    ziel_provinz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Einzelne Diplomatie-Beziehung abrufen"""
    
    # Prüfen ob User Owner von von_provinz_id ist
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "Sie sind nicht Owner dieser Provinz"}
        )
    
    # Beziehung laden
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        # Keine Beziehung existiert → Neutral (Standard)
        return {
            "von_provinz_id": von_provinz_id,
            "ziel_provinz_id": ziel_provinz_id,
            "status": 0,
            "status_name": "Neutral",
            "beziehungswert": 50,
            "vertraege": [],
            "erlaubte_aktionen": ["handeln", "migrieren"]
        }
    
    ziel_provinz = db.query(Province).get(relation.ziel_provinz_id)
    
    return {
        "id": relation.id,
        "von_provinz": {"id": von_provinz_id, "name": province.name},
        "ziel_provinz": {"id": ziel_provinz.id, "name": ziel_provinz.name} if ziel_provinz else None,
        "status": relation.status,
        "status_name": get_diplomatie_status_name(relation.status),
        "beziehungswert": relation.beziehungswert,
        "vertraege": json.loads(relation.vertraege) if relation.vertraege else [],
        "erlaubte_aktionen": get_erlaubte_aktionen(relation.status)
    }

@router.post("/diplomatie/{von_provinz_id}/initiiere")
async def initiate_diplomacy(
    von_provinz_id: int,
    data: DiplomatieInitiieren,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Diplomatie-Beziehung initiieren (Freundschaft vorschlagen)"""
    
    # Prüfen ob User Owner von von_provinz_id ist
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "Sie sind nicht Owner dieser Provinz"}
        )
    
    ziel_provinz = db.query(Province).get(data.ziel_provinz_id)
    
    if not ziel_provinz:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROVINZ_NOT_FOUND", "message": "Ziel-Provinz nicht gefunden"}
        )
    
    # Prüfen ob bereits Beziehung existiert
    existing = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=data.ziel_provinz_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "RELATION_EXISTS", "message": "Beziehung existiert bereits"}
        )
    
    # Neue Beziehung erstellen (Neutral, wird vom Ziel bestätigt)
    new_relation = Diplomatie(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=data.ziel_provinz_id,
        status=1,  # Freundschaftsvorschlag
        beziehungswert=50,
        vertraege="[]"
    )
    
    db.add(new_relation)
    db.commit()
    
    # Nachricht an Ziel-Provinz senden (WebSocket/Email)
    await send_diplomacy_notification(
        ziel_provinz.owner_id,
        f"{province.name} hat Ihnen Freundschaft angeboten."
    )
    
    return {
        "message": "Freundschaftsvorschlag gesendet",
        "relation_id": new_relation.id,
        "status": "wartet_auf_bestaetigung"
    }

@router.post("/diplomatie/{von_provinz_id}/{ziel_provinz_id}/bestaetigen")
async def confirm_diplomacy(
    von_provinz_id: int,
    ziel_provinz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Diplomatie-Vorschlag bestätigen (vom Ziel-Provinz Owner)"""
    
    # Prüfen ob User Owner von ziel_provinz_id ist
    province = db.query(Province).filter_by(id=ziel_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "Sie sind nicht Owner dieser Provinz"}
        )
    
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_RELATION", "message": "Kein Diplomatie-Vorschlag gefunden"}
        )
    
    # Bestätigen (Freundschaft)
    relation.status = 1  # Freundschaft
    relation.beziehungswert = min(relation.beziehungswert + 20, 100)
    relation.letzter_austausch = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Freundschaft bestätigt", "status": "Freundschaft"}

@router.post("/diplomatie/{von_provinz_id}/{ziel_provinz_id}/allianz")
async def form_alliance(
    von_provinz_id: int,
    ziel_provinz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allianz bilden (erfordert bestehende Freundschaft)"""
    
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail={"code": "NO_RELATION", "message": "Keine Beziehung"})
    
    # Erfordert Freundschaft oder besser
    if relation.status < 1:
        raise HTTPException(
            status_code=400,
            detail={"code": "INSUFFICIENT_RELATION", "message": "Benötigt mindestens Freundschaft"}
        )
    
    # Allianz bilden
    relation.status = 2  # Allianz
    relation.beziehungswert = min(relation.beziehungswert + 15, 100)
    
    # Allianz-Vertrag hinzufügen
    vertraege = json.loads(relation.vertraege) if relation.vertraege else []
    vertraege.append({
        "typ": "allianz",
        "erstellt_am": datetime.utcnow().isoformat(),
        "bedingungen": {
            "gemeinsame_verteidigung": True,
            "handelsvorzug": True
        }
    })
    relation.vertraege = json.dumps(vertraege)
    
    db.commit()
    
    return {"message": "Allianz gebildet", "status": "Allianz"}

@router.post("/diplomatie/{von_provinz_id}/{ziel_provinz_id}/kriegserklaerung")
async def declare_war(
    von_provinz_id: int,
    ziel_provinz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kriegserklärung abgeben"""
    
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        # Keine Beziehung → automatisch Krieg
        relation = Diplomatie(
            von_provinz_id=von_provinz_id,
            ziel_provinz_id=ziel_provinz_id,
            status=-2,  # Krieg
            beziehungswert=0
        )
        db.add(relation)
    else:
        # Bestehende Beziehung auf Krieg setzen
        relation.status = -2  # Krieg
        relation.beziehungswert = max(relation.beziehungswert - 50, 0)
    
    relation.letzter_austausch = datetime.utcnow()
    
    # Alle Verträge kündigen
    relation.vertraege = "[]"
    
    db.commit()
    
    # Ziel-Provinz Owner benachrichtigen
    ziel_provinz = db.query(Province).get(ziel_provinz_id)
    
    if ziel_provinz and ziel_provinz.owner_id:
        await send_diplomacy_notification(
            ziel_provinz.owner_id,
            f"{province.name} hat Ihnen den Krieg erklärt!"
        )
    
    return {"message": "Krieg erklärt", "status": "Krieg"}

@router.post("/diplomatie/{von_provinz_id}/{ziel_provinz_id}/friedensvertrag")
async def sign_peace_treaty(
    von_provinz_id: int,
    ziel_provinz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Friedensvertrag schließen (Krieg beenden)"""
    
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail={"code": "NO_RELATION", "message": "Keine Beziehung"})
    
    if relation.status != -2:  # Nicht Krieg
        raise HTTPException(
            status_code=400,
            detail={"code": "NOT_AT_WAR", "message": "Kein aktiver Krieg"}
        )
    
    # Frieden schließen → zurück zu Neutral oder Freundschaft
    relation.status = 0  # Neutral (oder 1 für Freundschaft)
    relation.beziehungswert = max(relation.beziehungswert + 10, 30)
    
    vertraege = json.loads(relation.vertraege) if relation.vertraege else []
    vertraege.append({
        "typ": "friedensvertrag",
        "erstellt_am": datetime.utcnow().isoformat()
    })
    relation.vertraege = json.dumps(vertraege)
    
    db.commit()
    
    return {"message": "Friedensvertrag geschlossen", "status": "Neutral"}

@router.post("/diplomatie/{von_provinz_id}/{ziel_provinz_id}/vertraeg")
async def add_treaty(
    von_provinz_id: int,
    ziel_provinz_id: int,
    treaty_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Neuen Vertrag zu bestehender Beziehung hinzufügen"""
    
    province = db.query(Province).filter_by(id=von_provinz_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    relation = db.query(Diplomatie).filter_by(
        von_provinz_id=von_provinz_id,
        ziel_provinz_id=ziel_provinz_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail={"code": "NO_RELATION", "message": "Keine Beziehung"})
    
    # Vertrag hinzufügen
    vertraege = json.loads(relation.vertraege) if relation.vertraege else []
    vertraege.append({
        "typ": treaty_data.get("typ"),
        "erstellt_am": datetime.utcnow().isoformat(),
        "bedingungen": treaty_data.get("bedingungen", {})
    })
    
    relation.vertraege = json.dumps(vertraege)
    relation.beziehungswert = min(relation.beziehungswert + 10, 100)
    
    db.commit()
    
    return {"message": "Vertrag hinzugefügt", "vertraege": vertraege}
```

---

## 🖥️ Client-Side Diplomatie UI (JavaScript)

### Diplomacy Manager

```javascript
// js/game/diplomacy-manager.js

class DiplomacyManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Alle Diplomatie-Beziehungen laden
    async loadDiplomacyRelations() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/diplomatie/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderRelations(data.relations);
                return data.relations;
            }
        } catch (error) {
            console.error('Diplomacy Load Error:', error);
        }

        return [];
    }

    // Beziehungen im UI rendern
    renderRelations(relations) {
        const container = document.getElementById('diplomacy-panel');
        
        if (!container) return;

        let html = '<h3>🤝 Diplomatie</h3>';
        
        if (relations.length === 0) {
            html += '<p class="no-relations">Noch keine diplomatischen Beziehungen.</p>';
        } else {
            html += '<div class="relations-list">';
            
            for (const rel of relations) {
                const statusColor = this.getStatusColor(rel.status);
                
                html += `
                    <div class="relation-card" data-provinz-id="${rel.ziel_provinz.id}">
                        <div class="relation-header">
                            <span class="province-name">${rel.ziel_provinz.name}</span>
                            <span class="status-badge" style="background-color: ${statusColor}">
                                ${rel.status_name}
                            </span>
                        </div>
                        
                        <div class="beziehungswert-bar">
                            <div class="bar-fill" style="width: ${rel.beziehungswert}%"></div>
                        </div>
                        
                        <div class="relation-actions">
                            ${this.getActionButtons(rel)}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // Status-Farbe ermitteln
    getStatusColor(status) {
        const colors = {
            -3: '#8b0000',  // Vasall (dunkelrot)
            -2: '#ff0000',  // Krieg (rot)
            -1: '#ff8c00',  // Spannungen (orange)
            0: '#808080',   // Neutral (grau)
            1: '#4caf50',   // Freundschaft (grün)
            2: '#2196f3',   // Allianz (blau)
            3: '#9c27b0'    // Militärbündnis (lila)
        };
        
        return colors[status] || '#808080';
    }

    // Aktionen basierend auf Status rendern
    getActionButtons(rel) {
        let buttons = '';
        
        if (rel.status === 0 || rel.status === -1) {
            buttons += `<button onclick="diplomacy.initiateFriendship(${rel.von_provinz.id}, ${rel.ziel_provinz.id})">Freundschaft</button>`;
        }
        
        if (rel.status >= 1) {
            buttons += `<button onclick="diplomacy.formAlliance(${rel.von_provinz.id}, ${rel.ziel_provinz.id})">Allianz</button>`;
        }
        
        if (rel.status >= 2) {
            buttons += `<button onclick="diplomacy.formMilitaryAlliance(${rel.von_provinz.id}, ${rel.ziel_provinz.id})">Militärbündnis</button>`;
        }
        
        if (rel.status !== -2) {
            buttons += `<button onclick="diplomacy.declareWar(${rel.von_provinz.id}, ${rel.ziel_provinz.id})" class="war-btn">Krieg</button>`;
        }
        
        if (rel.status === -2) {
            buttons += `<button onclick="diplomacy.signPeaceTreaty(${rel.von_provinz.id}, ${rel.ziel_provinz.id})">Frieden</button>`;
        }
        
        return buttons;
    }

    // Freundschaft initiieren
    async initiateFriendship(vonProvinzId, zielProvinzId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/diplomatie/${vonProvinzId}/initiiere`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ ziel_provinz_id: zielProvinzId })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Freundschaftsvorschlag an ${data.provinz_name} gesendet!`);
                await this.loadDiplomacyRelations();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Initiate Friendship Error:', error);
        }
    }

    // Krieg erklären
    async declareWar(vonProvinzId, zielProvinzId) {
        if (!confirm('Wirklich Krieg erklären? Dies kann nicht rückgängig gemacht werden!')) {
            return;
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/v1/diplomatie/${vonProvinzId}/${zielProvinzId}/kriegserklaerung`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Krieg gegen ${data.ziel_provinz_name} erklärt!`, 'war');
                await this.loadDiplomacyRelations();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Declare War Error:', error);
        }
    }

    // Friedensvertrag schließen
    async signPeaceTreaty(vonProvinzId, zielProvinzId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/diplomatie/${vonProvinzId}/${zielProvinzId}/friedensvertrag`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Friedensvertrag mit ${data.ziel_provinz_name} geschlossen!`);
                await this.loadDiplomacyRelations();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Peace Treaty Error:', error);
        }
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `diplomacy-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        this.loadDiplomacyRelations();
        
        // Periodisch aktualisieren (alle 60s = pro Tick)
        setInterval(() => {
            this.loadDiplomacyRelations();
        }, 60000);
    }
}

// Singleton
const diplomacy = new DiplomacyManager();

export default diplomacy;
```

---

## 🧪 Testing Diplomatie-System

### Unit Tests

```python
# tests/api/test_diplomacy.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_list_diplomacy_relations(client, auth_token):
    """Testet Auflistung aller Diplomatie-Beziehungen"""
    
    response = client.get("/diplomatie/", headers={"Authorization": f"Bearer {auth_token}"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "relations" in data

def test_initiate_friendship(client, auth_token):
    """Testet Freundschaftsvorschlag"""
    
    response = client.post(
        "/diplomatie/1/initiiere",
        json={"ziel_provinz_id": 2},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "Freundschaftsvorschlag gesendet" in data["message"]

def test_declare_war(client, auth_token):
    """Testet Kriegserklärung"""
    
    response = client.post(
        "/diplomatie/1/2/kriegserklaerung",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "Krieg"

def test_sign_peace_treaty(client, auth_token):
    """Testet Friedensvertrag"""
    
    # Zuerst Krieg erklären
    client.post(
        "/diplomatie/1/2/kriegserklaerung",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Dann Frieden schließen
    response = client.post(
        "/diplomatie/1/2/friedensvertrag",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "Neutral"

def test_alliance_requires_friendship(client, auth_token):
    """Testet dass Allianz Freundschaft erfordert"""
    
    # Keine Beziehung → sollte fehlschlagen
    response = client.post(
        "/diplomatie/1/2/allianz",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404  # Keine Beziehung

def test_get_diplomacy_status_name():
    """Testet Status-Namen Mapping"""
    
    from app.models import get_diplomatie_status_name
    
    assert get_diplomatie_status_name(0) == "Neutral"
    assert get_diplomatie_status_name(1) == "Freundschaft"
    assert get_diplomatie_status_name(-2) == "Krieg"

def test_erlaubte_aktionen_mapping():
    """Testet erlaubte Aktionen pro Status"""
    
    from app.models import get_erlaubte_aktionen
    
    neutral_aktionen = get_erlaubte_aktionen(0)
    assert "handeln" in neutral_aktionen
    
    krieg_aktionen = get_erlaubte_aktionen(-2)
    assert "angreifen" in krieg_aktionen
    
    vasall_aktionen = get_erlaubte_aktionen(-3)
    assert vasall_aktionen == ["keine"]
```

---

## 🎯 Best Practices

1. **Beziehungswert 0-100** - Numerische Skala für objektive Bewertung
2. **Verträge als JSON** - Flexible Vertragsbedingungen
3. **Status-Übergänge validieren** - Nicht jeder Übergang ist erlaubt (z.B. Neutral → Militärbündnis nicht direkt)
4. **Benachrichtigungen senden** - Ziel-Provinz Owner informieren
5. **Audit-Log führen** - Alle Diplomatie-Änderungen protokollieren

---

**Diplomatie-System ermöglicht dynamische Beziehungen zwischen Provinzen mit Verträgen, Allianzen und Kriegen!**
