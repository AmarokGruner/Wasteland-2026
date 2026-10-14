# 🛡️ Admin-Tools & Cheat-Prevention

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt Admin-Werkzeuge: Admin-Befehle, Bann-System, Audit-Log, Anti-Cheat und World-Events.

---

## 🎯 Ziele

1. **Admin-Befehle** - Welt-Management für Administratoren
2. **Bann-System** - Temporäre/permanente Sperren
3. **Audit-Log** - Alle Admin-Aktionen protokollieren
4. **Anti-Cheat** - Ungewöhnliche Aktivitäten erkennen

---

## 🏗️ Admin-System Architektur

### Admin-Rollen

```
SuperAdmin (vollständiger Zugriff)
    ├── WorldAdmin (Welt-Management)
    │   ├── Welt-Ereignisse verwalten
    │   ├── Provinzen verschieben/löschen
    │   └── Ressourcen verteilen
    │
    ├── UserAdmin (Benutzer-Management)
    │   ├── Bannen/Entbannen
    │   ├── Ressourcen geben/nehmen
    │   └── Profile bearbeiten
    │
    └── Moderator (Eingeschränkt)
        ├── Warnungen aussprechen
        ├── Temporär bannen (max 7 Tage)
        └── Chat moderieren
```

---

## 📊 Datenbank-Schema für Admin-System

### Admin-Tabellen

```python
# app/models.py - Admin Modelle

class AdminRole(Base):
    """Admin-Rolle eines Benutzers"""
    
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Rolle (superadmin, worldadmin, useradmin, moderator)
    rolle = Column(String(50), nullable=False)
    
    # Berechtigungen (JSON Array)
    berechtigungen = Column(Text, default="[]")
    
    # Aktiv?
    aktiv = Column(Boolean, default=True)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)

class AdminAuditLog(Base):
    """Audit-Log für alle Admin-Aktionen"""
    
    __tablename__ = "admin_audit_log"
    
    id = Column(Integer, primary_key=True)
    
    # Welcher Admin hat die Aktion ausgeführt?
    admin_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Ziel (welcher User/Provinz wurde betroffen?)
    ziel_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ziel_provinz_id = Column(Integer, ForeignKey("provinzen.id"), nullable=True)
    
    # Aktionstyp
    aktion_typ = Column(String(100), nullable=False)  # z.B. "ban_user", "give_resources"
    
    # Details (JSON)
    details = Column(Text)  # JSON: was genau wurde getan
    
    # Timestamp
    erstellt_am = Column(DateTime, default=datetime.utcnow)

class BanRecord(Base):
    """Bann-Record eines Benutzers"""
    
    __tablename__ = "ban_records"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Bann-Typ (temporär, permanent)
    bann_typ = Column(String(50), nullable=False)  # temporär, permanent
    
    # Grund
    grund = Column(Text, nullable=False)
    
    # Ausgestellt von (Admin ID)
    ausgestellt_von_id = Column(Integer, ForeignKey("users.id"))
    
    # Startdatum
    start_datum = Column(DateTime, nullable=False)
    
    # Enddatum (bei temporären Banns)
    end_datum = Column(DateTime, nullable=True)
    
    # Aktiv?
    aktiv = Column(Boolean, default=True)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)

# Helper: Admin-Befehle
class AdminCommands:
    @staticmethod
    def ban_user(db, admin_id: int, target_user_id: int, grund: str, dauer_tage: int = None) -> dict:
        """Benutzer bannen"""
        
        from app.models import User, BanRecord
        
        target_user = db.query(User).get(target_user_id)
        
        if not target_user:
            return {"success": False, "error": "Benutzer nicht gefunden"}
        
        # Bann erstellen
        bann = BanRecord(
            user_id=target_user_id,
            bann_typ="temporär" if dauer_tage else "permanent",
            grund=grund,
            ausgestellt_von_id=admin_id,
            start_datum=datetime.utcnow(),
            end_datum=datetime.utcnow().days + dauer_tage if dauer_tage else None,
            aktiv=True
        )
        
        db.add(bann)
        
        # User deaktivieren
        target_user.aktiv = False
        
        # Audit-Log erstellen
        admin_audit = AdminAuditLog(
            admin_user_id=admin_id,
            ziel_user_id=target_user_id,
            aktion_typ="ban_user",
            details=json.dumps({
                "grund": grund,
                "dauer_tage": dauer_tage,
                "bann_typ": bann.bann_typ
            })
        )
        
        db.add(admin_audit)
        db.commit()
        
        return {"success": True, "message": f"Benutzer {target_user.username} gebannt"}
    
    @staticmethod
    def unban_user(db, admin_id: int, target_user_id: int) -> dict:
        """Benutzer entbannen"""
        
        from app.models import User, BanRecord
        
        bann = db.query(BanRecord).filter_by(user_id=target_user_id, aktiv=True).first()
        
        if not bann:
            return {"success": False, "error": "Kein aktiver Bann gefunden"}
        
        bann.aktiv = False
        
        # User wieder aktivieren
        target_user = db.query(User).get(target_user_id)
        
        if target_user:
            target_user.aktiv = True
        
        # Audit-Log
        admin_audit = AdminAuditLog(
            admin_user_id=admin_id,
            ziel_user_id=target_user_id,
            aktion_typ="unban_user",
            details=json.dumps({"grund": "Bann aufgehoben"})
        )
        
        db.add(admin_audit)
        db.commit()
        
        return {"success": True, "message": f"Benutzer {target_user.username} entbannt"}
    
    @staticmethod
    def give_resources(db, admin_id: int, target_provinz_id: int, ressourcen: dict) -> dict:
        """Ressourcen zu einer Provinz hinzufügen"""
        
        from app.models import Province, ProvinceStorage
        
        province = db.query(Province).get(target_provinz_id)
        
        if not province:
            return {"success": False, "error": "Provinz nicht gefunden"}
        
        # Lager finden oder erstellen
        lager = db.query(ProvinceStorage).filter_by(province_id=target_provinz_id).first()
        
        if not lager:
            lager = ProvinceStorage(province_id=target_provinz_id)
            db.add(lager)
        
        # Ressourcen hinzufügen
        for res_name, menge in ressourcen.items():
            res_key = f"resources_{res_name}"
            
            aktuelle_menge = getattr(lager, res_key, 0) or 0
            setattr(lager, res_key, aktuelle_menge + menge)
        
        # Audit-Log
        admin_audit = AdminAuditLog(
            admin_user_id=admin_id,
            ziel_provinz_id=target_provinz_id,
            aktion_typ="give_resources",
            details=json.dumps({"ressourcen": ressourcen})
        )
        
        db.add(admin_audit)
        db.commit()
        
        return {"success": True, "message": f"Ressourcen zu Provinz {target_provinz_id} hinzugefügt"}
    
    @staticmethod
    def move_province(db, admin_id: int, province_id: int, new_x: int, new_y: int) -> dict:
        """Provinz verschieben"""
        
        from app.models import Province
        
        province = db.query(Province).get(province_id)
        
        if not province:
            return {"success": False, "error": "Provinz nicht gefunden"}
        
        old_x, old_y = province.x, province.y
        province.x = new_x
        province.y = new_y
        
        # Audit-Log
        admin_audit = AdminAuditLog(
            admin_user_id=admin_id,
            ziel_provinz_id=province_id,
            aktion_typ="move_province",
            details=json.dumps({"old_position": [old_x, old_y], "new_position": [new_x, new_y]})
        )
        
        db.add(admin_audit)
        db.commit()
        
        return {"success": True, "message": f"Provinz von ({old_x},{old_y}) nach ({new_x},{new_y}) verschoben"}
    
    @staticmethod
    def trigger_world_event(db, admin_id: int, event_type: str, affected_provinzen: list = None) -> dict:
        """Welt-Ereignis auslösen"""
        
        from app.models import Province
        
        event_data = {
            "type": event_type,
            "triggered_by_admin": admin_id,
            "affected_provinzen": affected_provinzen or []
        }
        
        # Welt-Ereignis verarbeiten (gleiche Logik wie zufällige Events)
        # In Production: tick_manager.trigger_world_event() aufrufen
        
        # Audit-Log
        admin_audit = AdminAuditLog(
            admin_user_id=admin_id,
            aktion_typ="trigger_world_event",
            details=json.dumps(event_data)
        )
        
        db.add(admin_audit)
        db.commit()
        
        return {"success": True, "message": f"Welt-Ereignis '{event_type}' ausgelöst"}

# Helper: Anti-Cheat prüfen
def check_anti_cheat(user_id: int) -> dict:
    """Ungewöhnliche Aktivitäten erkennen (Anti-Cheat)"""
    
    from app.models import User, Province, ProvinceStorage, Handelslog
    
    user = db.query(User).get(user_id)
    
    if not user:
        return {"cheat_detected": False}
    
    province = db.query(Province).filter_by(owner_id=user_id).first()
    
    if not province:
        return {"cheat_detected": False}
    
    lager = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
    
    if not lager:
        return {"cheat_detected": False}
    
    warnings = []
    
    # 1. Ressourcen-Explosion (plötzlicher enormer Anstieg)
    letzte_handel = db.query(Handelslog).filter_by(von_provinz_id=province.id).order_by(Handelslog.tick.desc()).limit(5).all()
    
    if letzte_handel:
        letzter_tick = letzte_handel[0].tick
        
        # Ressourcen die seit letztem Tick hinzugekommen sind
        nahrung = lager.resources_food or 0
        
        # Wenn Nahrung > 10000 in einem Tick → möglicher Cheat
        if nahrung > 10000:
            warnings.append({
                "type": "resource_explosion",
                "message": f"Extrem hohe Nahrungsmenge: {nahrung}",
                "severity": "high"
            })
    
    # 2. Schneller Ressourcen-Aufbau (mehr als möglich)
    gebaeude = db.query(Building).filter_by(province_id=province.id).all()
    
    gesamt_produktion = 0
    
    for gebaeude in gebaeude:
        produktion = gebaeude.typ.produktion  # JSON
        if produktion:
            gesamt_produktion += sum(produktion.values()) * gebaeude.stufe
    
    # Wenn Produktion > 1000 pro Tick → unmöglich ohne viele Gebäude
    if gesamt_produktion > 1000 and len(gebaeude) < 10:
        warnings.append({
            "type": "impossible_production",
            "message": f"Hohe Produktion ({gesamt_produktion}) bei wenigen Gebäuden ({len(gebaeude)})",
            "severity": "medium"
        })
    
    # 3. Schneller Level-Aufstieg
    if user.level > 50 and tick_manager.current_tick < 1000:
        warnings.append({
            "type": "rapid_level_up",
            "message": f"Level {user.level} in nur {tick_manager.current_tick} Ticks",
            "severity": "high"
        })
    
    return {
        "cheat_detected": len(warnings) > 0,
        "warnings": warnings,
        "user_id": user_id,
        "province_id": province.id
    }

# Helper: Audit-Log abrufen
def get_admin_audit_log(admin_id: int = None, limit: int = 50) -> list:
    """Admin-Audit-Log abrufen"""
    
    query = db.query(AdminAuditLog)
    
    if admin_id:
        query = query.filter_by(admin_user_id=admin_id)
    
    logs = query.order_by(AdminAuditLog.erstellt_am.desc()).limit(limit).all()
    
    result = []
    
    for log in logs:
        admin_user = db.query(User).get(log.admin_user_id) if log.admin_user_id else None
        ziel_user = db.query(User).get(log.ziel_user_id) if log.ziel_user_id else None
        ziel_provinz = db.query(Province).get(log.ziel_provinz_id) if log.ziel_provinz_id else None
        
        result.append({
            "id": log.id,
            "admin": admin_user.username if admin_user else "Unbekannt",
            "ziel_user": ziel_user.username if ziel_user else None,
            "ziel_provinz": ziel_provinz.name if ziel_provinz else None,
            "aktion_typ": log.aktion_typ,
            "details": json.loads(log.details) if log.details else {},
            "erstellt_am": log.erstellt_am.isoformat()
        })
    
    return result

# Helper: Aktive Banns auflisten
def get_active_bans() -> list:
    """Alle aktiven Banns auflisten"""
    
    banns = db.query(BanRecord).filter_by(aktiv=True).all()
    
    result = []
    
    for b in banns:
        user = db.query(User).get(b.user_id)
        admin = db.query(User).get(b.ausgestellt_von_id) if b.ausgestellt_von_id else None
        
        result.append({
            "user_id": b.user_id,
            "username": user.username if user else "Unbekannt",
            "bann_typ": b.bann_typ,
            "grund": b.grund,
            "ausgestellt_von": admin.username if admin else "Unbekannt",
            "start_datum": b.start_datum.isoformat(),
            "end_datum": b.end_datum.isoformat() if b.end_datum else None
        })
    
    return result

# Helper: User Login prüfen (Bann-Check)
def check_user_ban(user_id: int) -> dict:
    """Prüfen ob User gebannt ist"""
    
    bann = db.query(BanRecord).filter_by(user_id=user_id, aktiv=True).first()
    
    if not bann:
        return {"banned": False}
    
    # Temporärer Bann abgelaufen?
    if bann.bann_typ == "temporär" and bann.end_datum and datetime.utcnow() > bann.end_datum:
        # Bann automatisch aufheben
        bann.aktiv = False
        
        user = db.query(User).get(user_id)
        
        if user:
            user.aktiv = True
        
        db.commit()
        
        return {"banned": False, "message": "Bann abgelaufen"}
    
    return {
        "banned": True,
        "bann_typ": bann.bann_typ,
        "grund": bann.grund,
        "end_datum": bann.end_datum.isoformat() if bann.end_datum else None
    }
```

---

## 📡 API Endpunkte für Admin-System

### Admin Router

```python
# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/admin/ban")
async def ban_user(
    data: BanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Nur Admins
):
    """Benutzer bannen"""
    
    result = AdminCommands.ban_user(
        db=db,
        admin_id=current_user.id,
        target_user_id=data.user_id,
        grund=data.grund,
        dauer_tage=data.dauer_tage
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "BAN_FAILED", "message": result["error"]})
    
    return {"message": result["message"]}

@router.post("/admin/unban")
async def unban_user(
    data: UnbanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Benutzer entbannen"""
    
    result = AdminCommands.unban_user(
        db=db,
        admin_id=current_user.id,
        target_user_id=data.user_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "UNBAN_FAILED", "message": result["error"]})
    
    return {"message": result["message"]}

@router.get("/admin/bans")
async def list_active_bans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Alle aktiven Banns auflisten"""
    
    banns = get_active_bans()
    
    return {"bans": banns}

@router.post("/admin/resources")
async def give_resources(
    data: RessourcenGeben,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Ressourcen zu Provinz hinzufügen"""
    
    result = AdminCommands.give_resources(
        db=db,
        admin_id=current_user.id,
        target_provinz_id=data.provinz_id,
        ressourcen=data.ressourcen
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "RESOURCES_FAILED", "message": result["error"]})
    
    return {"message": result["message"]}

@router.post("/admin/move_province")
async def move_province(
    data: ProvinzVerschieben,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Provinz verschieben"""
    
    result = AdminCommands.move_province(
        db=db,
        admin_id=current_user.id,
        province_id=data.provinz_id,
        new_x=data.x,
        new_y=data.y
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "MOVE_FAILED", "message": result["error"]})
    
    return {"message": result["message"]}

@router.post("/admin/world_event")
async def trigger_world_event(
    data: WeltEventAuslösen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Welt-Ereignis auslösen"""
    
    result = AdminCommands.trigger_world_event(
        db=db,
        admin_id=current_user.id,
        event_type=data.event_type,
        affected_provinzen=data.affected_provinzen
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "EVENT_FAILED", "message": result["error"]})
    
    return {"message": result["message"]}

@router.get("/admin/audit_log")
async def get_audit_log(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin-Audit-Log abrufen"""
    
    logs = get_admin_audit_log(limit=limit)
    
    return {"audit_log": logs}

@router.get("/admin/anti_cheat/check/{user_id}")
async def check_anti_cheat(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Anti-Cheat Check für Benutzer durchführen"""
    
    result = check_anti_cheat(user_id)
    
    return result

@router.get("/admin/users")
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Alle Benutzer auflisten (Admin-Übersicht)"""
    
    users = db.query(User).all()
    
    user_liste = []
    
    for user in users:
        ban_info = check_user_ban(user.id)
        
        user_liste.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "level": user.level,
            "aktiv": user.aktiv,
            "gebannt": ban_info["banned"],
            "created_at": user.created_at.isoformat()
        })
    
    return {"users": user_liste}
```

---

## 🖥️ Client-Side Admin UI (JavaScript)

### Admin Dashboard

```javascript
// js/admin/admin-dashboard.js

class AdminDashboard {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Alle Benutzer laden
    async loadUsers() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/users`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderUsers(data.users);
            }
        } catch (error) {
            console.error('Users Load Error:', error);
        }
    }

    // Benutzer-Tabelle rendern
    renderUsers(users) {
        const container = document.getElementById('admin-users-table');
        
        if (!container) return;

        let html = '<h3>👥 Benutzer-Verwaltung</h3>';
        html += '<table class="users-table">';
        html += '<thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Level</th><th>Status</th><th>Aktionen</th></tr></thead>';
        html += '<tbody>';

        for (const user of users) {
            const statusClass = user.aktiv ? 'aktiv' : 'inaktiv';
            const banBadge = user.gebannt ? '<span class="badge-banned">🚫 Gebannt</span>' : '';

            html += `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.level}</td>
                    <td><span class="status ${statusClass}">${user.aktiv ? 'Aktiv' : 'Inaktiv'}</span> ${banBadge}</td>
                    <td>
                        <button onclick="admin.banUser(${user.id})">Bannen</button>
                        <button onclick="admin.unbanUser(${user.id})">Entbannen</button>
                        <button onclick="admin.checkAntiCheat(${user.id})">Anti-Cheat</button>
                    </td>
                </tr>
            `;
        }

        html += '</tbody></table>';

        container.innerHTML = html;
    }

    // Benutzer bannen
    async banUser(userId) {
        const grund = prompt('Grund für den Bann:');
        
        if (!grund) return;

        const dauerTage = prompt('Dauer in Tagen (leer für permanent):');
        const dauer = dauerTage ? parseInt(dauerTage) : null;

        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/ban`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ user_id: userId, grund: grund, dauer_tage: dauer })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(data.message);
                await this.loadUsers();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Ban Error:', error);
        }
    }

    // Benutzer entbannen
    async unbanUser(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/unban`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ user_id: userId })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(data.message);
                await this.loadUsers();
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Unban Error:', error);
        }
    }

    // Anti-Cheat Check durchführen
    async checkAntiCheat(userId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/anti_cheat/check/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                if (data.cheat_detected) {
                    this.showCheatWarnings(data.warnings);
                } else {
                    this.showNotification('Keine Cheat-Anzeichen gefunden');
                }
            }
        } catch (error) {
            console.error('Anti-Cheat Error:', error);
        }
    }

    showCheatWarnings(warnings) {
        const modal = document.getElementById('cheat-warnings-modal');
        
        if (!modal) return;

        let html = '<h3>⚠️ Anti-Cheat Warnungen</h3>';
        
        for (const warning of warnings) {
            const severityColor = warning.severity === 'high' ? '#ff0000' : '#ff8c00';
            
            html += `
                <div class="warning-item" style="border-left: 4px solid ${severityColor}; padding: 10px; margin: 10px 0;">
                    <p><strong>${warning.type}</strong></p>
                    <p>${warning.message}</p>
                </div>
            `;
        }

        modal.innerHTML = html;
        modal.style.display = 'block';
    }

    // Audit-Log laden
    async loadAuditLog() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/admin/audit_log?limit=50`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderAuditLog(data.audit_log);
            }
        } catch (error) {
            console.error('Audit Log Load Error:', error);
        }
    }

    renderAuditLog(logs) {
        const container = document.getElementById('admin-audit-log');
        
        if (!container) return;

        let html = '<h3>📋 Admin-Audit-Log</h3>';
        html += '<table class="audit-table">';
        html += '<thead><tr><th>Zeit</th><th>Admin</th><th>Ziel</th><th>Aktion</th><th>Details</th></tr></thead>';
        html += '<tbody>';

        for (const log of logs) {
            html += `
                <tr>
                    <td>${log.erstellt_am}</td>
                    <td>${log.admin}</td>
                    <td>${log.ziel_user || log.ziel_provinz || '-'}</td>
                    <td>${log.aktion_typ}</td>
                    <td><pre>${JSON.stringify(log.details, null, 2)}</pre></td>
                </tr>
            `;
        }

        html += '</tbody></table>';

        container.innerHTML = html;
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `admin-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        this.loadUsers();
        this.loadAuditLog();
        
        // Periodisch aktualisieren (alle 60s)
        setInterval(() => {
            this.loadUsers();
        }, 60000);
    }
}

// Singleton
const admin = new AdminDashboard();

export default admin;
```

---

## 🧪 Testing Admin-System

### Unit Tests

```python
# tests/api/test_admin.py
import pytest

def test_ban_user(admin_client):
    """Testet Bannen eines Benutzers"""
    
    response = admin_client.post(
        "/admin/ban",
        json={"user_id": 2, "grund": "Spam", "dauer_tage": 7},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200

def test_unban_user(admin_client):
    """Testet Entbannen eines Benutzers"""
    
    response = admin_client.post(
        "/admin/unban",
        json={"user_id": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200

def test_give_resources(admin_client):
    """Testet Ressourcen geben"""
    
    response = admin_client.post(
        "/admin/resources",
        json={"provinz_id": 1, "ressourcen": {"food": 1000, "water": 500}},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200

def test_move_province(admin_client):
    """Testet Provinz verschieben"""
    
    response = admin_client.post(
        "/admin/move_province",
        json={"provinz_id": 1, "x": 25, "y": 25},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200

def test_audit_log(admin_client):
    """Testet Audit-Log Abruf"""
    
    response = admin_client.get("/admin/audit_log", headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "audit_log" in data

def test_anti_cheat_check(admin_client):
    """Testet Anti-Cheat Check"""
    
    response = admin_client.get("/admin/anti_cheat/check/1", headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "cheat_detected" in data

def test_check_user_ban():
    """Testet Bann-Prüfung"""
    
    from app.models import check_user_ban
    
    result = check_user_ban(1)
    
    assert "banned" in result

def test_active_bans_list():
    """Testet Liste aktiver Banns"""
    
    from app.models import get_active_bans
    
    banns = get_active_bans()
    
    assert isinstance(banns, list)
```

---

## 🎯 Best Practices

1. **Audit-Log immer führen** - Jede Admin-Aktion protokollieren
2. **Anti-Cheat pro Tick** - Ungewöhnliche Aktivitäten erkennen
3. **Bann-Gründe dokumentieren** - Transparent für betroffene User
4. **Temporäre Bände mit Ablauf** - Automatische Aufhebung nach Zeit
5. **Admin-Rollen hierarchisch** - Moderatoren nur eingeschränkte Rechte

---

**Admin-System ermöglicht Welt-Management mit Bann-System, Audit-Log und Anti-Cheat!**
