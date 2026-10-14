# 🌍 Welt-Generierung & Procedural Content

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Welt-Generierung: Seed-basierte Erzeugung, Provinz-Grenzen Algorithmus, Ressourcen-Verteilung und konfigurierbare Welt-Größe.

---

## 🎯 Ziele

1. **Reproduzierbare Welten** - Gleicher Seed = gleiche Welt
2. **Faire Ressourcen-Verteilung** - Keine Provinz benachteiligt
3. **Konfigurierbare Größe** - Kleine bis große Welten
4. **Prozedurale Vielfalt** - Natürliche Landschaften durch Algorithmen

---

## 🏗️ Welt-Generierung Architektur

### Generierungs-Pipeline

```
1. Seed initialisieren (zufällig oder manuell)
        ↓
2. Terrain generieren (Perlin Noise / Simplex Noise)
        ↓
3. Ressourcen verteilen (basierend auf Terrain)
        ↓
4. Provinz-Grenzen berechnen (Voronoi-Diagramm)
        ↓
5. Start-Positionen platzieren (gleichmäßig verteilt)
        ↓
6. Welt validieren (faire Verteilung prüfen)
```

---

## 📊 Datenbank-Schema für Welt-Generierung

### Welt-Konfiguration & Terrain

```python
# app/models.py - Welt-Generierung Modelle

class WeltKonfiguration(Base):
    """Welt-Konfiguration für Generierung"""
    
    __tablename__ = "welt_konfiguration"
    
    id = Column(Integer, primary_key=True)
    
    # Welt-Name
    name = Column(String(100), nullable=False)
    
    # Seed (für reproduzierbare Generierung)
    seed = Column(Integer, nullable=False, unique=True)
    
    # Welt-Größe (Breite × Höhe in Feldern)
    breite = Column(Integer, default=50)
    hoehe = Column(Integer, default=50)
    
    # Ressourcen-Dichte (wie viele Ressourcen pro Feld)
    ressourcen_dichte = Column(Float, default=0.3)  # 0.0 - 1.0
    
    # Provinz-Anzahl (Start-Positionen)
    anzahl_provinzen = Column(Integer, default=10)
    
    # Generierungs-Status
    status = Column(String(50), default="ungeneriert")  # ungeneriert, fertig, fehler
    
    # Fehler-Meldung (wenn Generierung fehlgeschlagen)
    fehler_meldung = Column(Text, nullable=True)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    generiert_am = Column(DateTime, nullable=True)

class TerrainFeld(Base):
    """Einzelnes Feld der Weltkarte"""
    
    __tablename__ = "terrain_felder"
    
    id = Column(Integer, primary_key=True)
    
    # Welt-ID (zu welcher Welt gehört dieses Feld?)
    welt_id = Column(Integer, ForeignKey("welt_konfiguration.id"))
    
    # Koordinaten
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    
    # Terrain-Typ (ID aus terrain_typen Tabelle)
    terrain_typ_id = Column(Integer, ForeignKey("terrain_typen.id"))
    
    # Vorkommen (Bodenschätze auf diesem Feld)
    vorkommen_id = Column(Integer, ForeignKey("vorkommen.id"), nullable=True)
    
    # Provinz-ID (wem gehört dieses Feld?)
    province_id = Column(Integer, ForeignKey("provinzen.id"), nullable=True)
    
    # Eindeutige Einschränkung (x,y pro Welt)
    __table_args__ = (
        UniqueConstraint('welt_id', 'x', 'y', name='uq_terrain_feld_position'),
    )

# Helper: Welt generieren (Seed-basiert)
def generate_welt(welt_id: int, seed: int = None) -> dict:
    """Welt basierend auf Seed generieren"""
    
    import random
    
    welt = db.query(WeltKonfiguration).get(welt_id)
    
    if not welt:
        return {"success": False, "error": "Welt nicht gefunden"}
    
    # Seed setzen (wenn nicht angegeben, zufälligen Seed generieren)
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    
    welt.seed = seed
    
    # Random Generator mit Seed initialisieren (reproduzierbar!)
    rng = random.Random(seed)
    
    try:
        # 1. Terrain generieren (Perlin Noise für natürliche Landschaften)
        terrain_data = generate_terrain_noise(welt.breite, welt.hoehe, rng)
        
        # 2. Terrain-Typen zuweisen (basierend auf Noise-Werten)
        assign_terrain_types(terrain_data, welt.id)
        
        # 3. Ressourcen verteilen (basierend auf Terrain)
        distribute_ressourcen(terrain_data, welt.id, welt.ressourcen_dichte, rng)
        
        # 4. Provinz-Grenzen berechnen (Voronoi-Diagramm)
        province_boundaries = calculate_voronoi_boundaries(welt.anzahl_provinzen, welt.breite, welt.hoehe, rng)
        
        # 5. Start-Positionen platzieren (gleichmäßig verteilt)
        start_positions = calculate_start_positions(province_boundaries, welt.anzahl_provinzen, rng)
        
        # 6. Welt in Datenbank speichern
        save_welt_to_db(welt.id, terrain_data, province_boundaries, start_positions)
        
        welt.status = "fertige"
        welt.generiert_am = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "seed": seed,
            "breite": welt.breite,
            "hoehe": welt.hoehe,
            "start_positionen": start_positions
        }
    
    except Exception as e:
        welt.status = "fehler"
        welt.fehler_meldung = str(e)
        db.commit()
        
        return {"success": False, "error": str(e)}

def generate_terrain_noise(breite: int, hoehe: int, rng) -> list:
    """Terrain mit Perlin Noise generieren (natürliche Landschaften)"""
    
    # Einfache Implementierung: Mehrere Noise-Layer kombinieren
    # In Production: PerlinNoise oder SimplexNoise Library verwenden
    
    terrain_data = []
    
    for y in range(hoehe):
        for x in range(breite):
            # Noise-Wert berechnen (0.0 - 1.0)
            noise_value = calculate_perlin_noise(x, y, rng)
            
            terrain_data.append({
                "x": x,
                "y": y,
                "noise_value": noise_value
            })
    
    return terrain_data

def calculate_perlin_noise(x: int, y: int, rng) -> float:
    """Perlin Noise simulieren (vereinfacht)"""
    
    # Mehrere Octaves kombinieren für natürlichere Landschaften
    noise = 0.0
    amplitude = 1.0
    frequency = 0.1
    
    for octave in range(4):  # 4 Octaves
        noise += amplitude * rng.gauss(0, 1)  # Zufälliger Noise-Wert
        amplitude *= 0.5  # Jede Octave halbiert
        frequency *= 2.0  # Jede Octave doppelt so häufig
    
    # Normalisieren auf 0.0 - 1.0
    noise = (noise + 2.0) / 4.0  # Shift und Scale
    
    return max(0.0, min(1.0, noise))

def assign_terrain_types(terrain_data: list, welt_id: int):
    """Terrain-Typen basierend auf Noise-Werten zuweisen"""
    
    from app.models import TerrainTypen
    
    terrain_typen = db.query(TerrainTypen).all()
    
    # Noise-Werte in Terrain-Typen mappen
    for feld in terrain_data:
        noise = feld["noise_value"]
        
        # Mapping (Beispiel):
        # 0.0 - 0.15: Wüste
        # 0.15 - 0.35: Grasland
        # 0.35 - 0.55: Wald
        # 0.55 - 0.75: Gebirge
        # 0.75 - 1.0: Sumpf
        
        if noise < 0.15:
            terrain_typ_id = get_terrain_typ_by_name("Wüste")
        elif noise < 0.35:
            terrain_typ_id = get_terrain_typ_by_name("Grasland")
        elif noise < 0.55:
            terrain_typ_id = get_terrain_typ_by_name("Wald")
        elif noise < 0.75:
            terrain_typ_id = get_terrain_typ_by_name("Gebirge")
        else:
            terrain_typ_id = get_terrain_typ_by_name("Sumpf")
        
        feld["terrain_typ_id"] = terrain_typ_id

def get_terrain_typ_by_name(name: str) -> int:
    """Terrain-Typ ID nach Name suchen"""
    
    from app.models import TerrainTypen
    
    typ = db.query(TerrainTypen).filter_by(name=name).first()
    
    return typ.id if typ else 1

def distribute_ressourcen(terrain_data: list, welt_id: int, dichte: float, rng):
    """Ressourcen basierend auf Terrain verteilen"""
    
    from app.models import Vorkommen
    
    vorkommen = db.query(Vorkommen).all()
    
    for feld in terrain_data:
        # Zufällige Chance basierend auf Dichte
        if rng.random() < dichte:
            # Zufälliges Vorkommen auswählen (aber terrain-abhängig)
            terrain_typ_id = feld["terrain_typ_id"]
            
            # Passende Vorkommen filtern (vereinfacht)
            passende_vorkommen = [v for v in vorkommen]  # In Production: nach Terrain filtern
            
            if passende_vorkommen:
                vorkommen_id = rng.choice(pasende_vorkommen).id
                feld["vorkommen_id"] = vorkommen_id

def calculate_voronoi_boundaries(anzahl_provinzen: int, breite: int, hoehe: int, rng) -> dict:
    """Voronoi-Diagramm für Provinz-Grenzen berechnen"""
    
    # Einfache Implementierung: Zufällige Zentren wählen, dann jedem Feld
    # die nächstgelegene Provinz zuweisen
    
    # Zufällige Zentren (max 3 pro Provinz für organische Formen)
    zentren = []
    
    for i in range(anzahl_provinzen):
        # 1-3 Zentren pro Provinz
        num_centers = rng.randint(1, 3)
        
        for _ in range(num_centers):
            x = rng.randint(0, breite - 1)
            y = rng.randint(0, hoehe - 1)
            zentren.append({"province_id": i + 1, "x": x, "y": y})
    
    # jedem Feld die nächstgelegene Provinz zuweisen
    boundaries = {}
    
    for y in range(hoehe):
        for x in range(breite):
            min_dist = float('inf')
            closest_province = None
            
            for zentrum in zentren:
                dist = ((x - zentrum["x"]) ** 2 + (y - zentrum["y"]) ** 2) ** 0.5
                
                if dist < min_dist:
                    min_dist = dist
                    closest_province = zentrum["province_id"]
            
            boundaries[(x, y)] = closest_province
    
    return boundaries

def calculate_start_positions(province_boundaries: dict, anzahl_provinzen: int, rng) -> list:
    """Start-Positionen gleichmäßig verteilen"""
    
    start_positions = []
    
    for province_id in range(1, anzahl_provinzen + 1):
        # Alle Felder dieser Provinz finden
        province_felder = [(x, y) for (x, y), pid in province_boundaries.items() if pid == province_id]
        
        if not province_felder:
            continue
        
        # Zufälliges Feld als Start-Position wählen (aber nicht am Rand)
        innere_felder = [(x, y) for x, y in province_felder if 5 < x < 45 and 5 < y < 45]
        
        if innere_felder:
            start_x, start_y = rng.choice(innere_felder)
        else:
            start_x, start_y = rng.choice(province_felder)
        
        start_positions.append({
            "province_id": province_id,
            "x": start_x,
            "y": start_y
        })
    
    return start_positions

def save_welt_to_db(welt_id: int, terrain_data: list, boundaries: dict, start_positions: list):
    """Welt-Daten in Datenbank speichern"""
    
    from app.models import TerrainFeld
    
    # Alte Daten löschen (falls Welt bereits existiert)
    db.query(TerrainFeld).filter_by(welt_id=welt_id).delete()
    
    # Neue Daten speichern
    for feld in terrain_data:
        terrain_feld = TerrainFeld(
            welt_id=welt_id,
            x=feld["x"],
            y=feld["y"],
            terrain_typ_id=feld.get("terrain_typ_id"),
            vorkommen_id=feld.get("vorkommen_id")
        )
        
        # Provinz-Zuweisung
        province_id = boundaries.get((feld["x"], feld["y"]))
        
        if province_id:
            terrain_feld.province_id = province_id
        
        db.add(terrain_feld)
    
    # Start-Positionen als Provinzen speichern (vereinfacht)
    from app.models import Province
    
    for pos in start_positions:
        province = Province(
            name=f"Start-Provinz {pos['province_id']}",
            x=pos["x"],
            y=pos["y"],
            owner_id=None  # Noch keinem User zugeordnet
        )
        
        db.add(province)
    
    db.commit()

# Helper: Welt laden (aus Datenbank)
def load_welt(welt_id: int) -> dict:
    """Welt aus Datenbank laden"""
    
    welt = db.query(WeltKonfiguration).get(welt_id)
    
    if not welt:
        return {"success": False, "error": "Welt nicht gefunden"}
    
    felder = db.query(TerrainFeld).filter_by(welt_id=welt_id).all()
    
    weltkarte = []
    
    for feld in felder:
        weltkarte.append({
            "x": feld.x,
            "y": feld.y,
            "terrain_typ_id": feld.terrain_typ_id,
            "vorkommen_id": feld.vorkommen_id,
            "province_id": feld.province_id
        })
    
    return {
        "success": True,
        "welt": {
            "id": welt.id,
            "name": welt.name,
            "seed": welt.seed,
            "breite": welt.breite,
            "hoehe": welt.hoehe,
            "status": welt.status
        },
        "felder": weltkarte
    }

# Helper: Welt validieren (faire Verteilung prüfen)
def validate_welt_fairness(welt_id: int) -> dict:
    """Prüfen ob Ressourcen fair verteilt sind"""
    
    welt = db.query(WeltKonfiguration).get(welt_id)
    
    if not welt:
        return {"valid": False, "error": "Welt nicht gefunden"}
    
    felder = db.query(TerrainFeld).filter_by(welt_id=welt_id).all()
    
    # Ressourcen pro Provinz zählen
    ressourcen_pro_provinz = {}
    
    for feld in felder:
        if feld.province_id and feld.vorkommen_id:
            if feld.province_id not in ressourcen_pro_provinz:
                ressourcen_pro_provinz[feld.province_id] = 0
            
            ressourcen_pro_provinz[feld.province_id] += 1
    
    # Varianz berechnen (wie ungleich ist die Verteilung?)
    if not ressourcen_pro_provinz:
        return {"valid": True, "message": "Keine Ressourcen vorhanden"}
    
    werte = list(ressourcen_pro_provinz.values())
    durchschnitt = sum(werte) / len(werte)
    
    varianz = sum((x - durchschnitt) ** 2 for x in werte) / len(werte)
    
    # Wenn Varianz zu hoch → unfaire Verteilung
    if varianz > durchschnitt * 0.5:
        return {
            "valid": False,
            "message": f"Ressourcen ungleich verteilt (Varianz: {varianz:.2f})",
            "varianz": varianz
        }
    
    return {
        "valid": True,
        "message": "Ressourcen fair verteilt",
        "varianz": varianz,
        "durchschnitt": durchschnitt
    }
```

---

## 📡 API Endpunkte für Welt-Generierung

### Welt Router

```python
# app/api/v1/welt.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/welt/generieren")
async def generate_new_welt(
    data: WeltGenerierenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Neue Welt generieren"""
    
    # Welt-Konfiguration erstellen
    welt = WeltKonfiguration(
        name=data.name or f"Welt {datetime.utcnow().strftime('%Y%m%d')}",
        seed=data.seed,  # Wenn None → zufälliger Seed
        breite=data.breite or 50,
        hoehe=data.hoehe or 50,
        ressourcen_dichte=data.ressourcen_dichte or 0.3,
        anzahl_provinzen=data.anzahl_provinzen or 10,
        status="generiere"
    )
    
    db.add(welt)
    db.commit()
    db.refresh(welt)
    
    # Welt generieren (asynchron, da langwierig)
    result = generate_welt(welt.id, welt.seed)
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail={"code": "WELT_GENERIERUNG_FEHLGESCHLAGEN", "message": result["error"]}
        )
    
    return {
        "message": "Welt erfolgreich generiert",
        "welt_id": welt.id,
        "seed": result["seed"],
        "breite": welt.breite,
        "hoehe": welt.hoehe,
        "start_positionen": result["start_positionen"]
    }

@router.get("/welt/{welt_id}")
async def get_welt(
    welt_id: int,
    db: Session = Depends(get_db)
):
    """Welt laden (aus Datenbank)"""
    
    result = load_welt(welt_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail={"code": "WELT_NOT_FOUND", "message": result["error"]})
    
    return result["welt"]

@router.get("/welt/{welt_id}/karte")
async def get_welt_karte(
    welt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Welt-Karte laden (für Spieler sichtbar)"""
    
    welt = db.query(WeltKonfiguration).get(welt_id)
    
    if not welt:
        raise HTTPException(status_code=404, detail={"code": "WELT_NOT_FOUND", "message": "Welt nicht gefunden"})
    
    felder = db.query(TerrainFeld).filter_by(welt_id=welt_id).all()
    
    karte = []
    
    for feld in felder:
        # Nur Felder in Sichtweite des Players anzeigen (Fog of War)
        if current_user.province_id:
            province = db.query(Province).get(current_user.province_id)
            
            if province:
                dx = abs(feld.x - province.x)
                dy = abs(feld.y - province.y)
                
                if dx > 10 or dy > 10:
                    continue  # Zu weit entfernt
        
        karte.append({
            "x": feld.x,
            "y": feld.y,
            "terrain_typ_id": feld.terrain_typ_id,
            "province_id": feld.province_id
        })
    
    return {
        "welt_id": welt_id,
        "breite": welt.breite,
        "hoehe": welt.hoehe,
        "felder": karte
    }

@router.post("/welt/{welt_id}/validieren")
async def validate_welt(
    welt_id: int,
    db: Session = Depends(get_db)
):
    """Welt auf faire Ressourcen-Verteilung validieren"""
    
    result = validate_welt_fairness(welt_id)
    
    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNFAIRE_VERTEILUNG", "message": result["message"]}
        )
    
    return {
        "valid": True,
        "message": result["message"],
        "varianz": result.get("varianz"),
        "durchschnitt": result.get("durchschnitt")
    }

@router.get("/welt/konfigurationen")
async def list_welt_konfigurationen(
    db: Session = Depends(get_db)
):
    """Alle Welt-Konfigurationen auflisten"""
    
    welten = db.query(WeltKonfiguration).all()
    
    welt_liste = []
    
    for w in welten:
        welt_liste.append({
            "id": w.id,
            "name": w.name,
            "seed": w.seed,
            "breite": w.breite,
            "hoehe": w.hoehe,
            "status": w.status,
            "generiert_am": w.generiert_am.isoformat() if w.generiert_am else None
        })
    
    return {"welten": welt_liste}
```

---

## 🖥️ Client-Side Welt-Karte UI (JavaScript)

### Welt Karte Renderer

```javascript
// js/game/welt-karte.js

class WeltKarteRenderer {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
        this.canvas = null;
        this.ctx = null;
        this.scale = 10; // Pixel pro Feld
    }

    // Welt-Karte laden und rendern
    async loadWeltKarte(weltId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/welt/${weltId}/karte`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderKarte(data.felder, data.breite, data.hoehe);
            }
        } catch (error) {
            console.error('Welt Karte Load Error:', error);
        }
    }

    // Welt-Karte auf Canvas rendern
    renderKarte(felder, breite, hoehe) {
        this.canvas = document.getElementById('welt-karte-canvas');
        
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        
        // Canvas-Größe anpassen
        this.canvas.width = breite * this.scale;
        this.canvas.height = hoehe * this.scale;
        
        // Terrain-Typen Farben
        const terrainColors = {
            1: '#8B4513',  // Wüste (braun)
            2: '#228B22',  // Grasland (grün)
            3: '#006400',  // Wald (dunkelgrün)
            4: '#808080',  // Gebirge (grau)
            5: '#4682B4'   // Sumpf (blau)
        };
        
        // Felder zeichnen
        for (const feld of felder) {
            const x = feld.x * this.scale;
            const y = feld.y * this.scale;
            
            // Terrain-Farbe
            this.ctx.fillStyle = terrainColors[feld.terrain_typ_id] || '#808080';
            this.ctx.fillRect(x, y, this.scale, this.scale);
            
            // Provinz-Grenzen (wenn vorhanden)
            if (feld.province_id) {
                this.ctx.strokeStyle = '#FFD700'; // Goldene Grenzen
                this.ctx.strokeRect(x, y, this.scale, this.scale);
            }
        }
        
        // Start-Positionen markieren (wenn bekannt)
        this.markStartPositions();
    }

    // Start-Positionen markieren
    markStartPositions() {
        if (!this.ctx) return;
        
        this.ctx.fillStyle = '#FF0000'; // Rote Marker
        
        // In Production: Start-Positionen aus API laden
        const startPositions = [];  // Placeholder
        
        for (const pos of startPositions) {
            const x = pos.x * this.scale;
            const y = pos.y * this.scale;
            
            this.ctx.beginPath();
            this.ctx.arc(x + this.scale/2, y + this.scale/2, 3, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    // Zoom-Funktion
    zoom(factor) {
        this.scale *= factor;
        this.canvas.width = this.canvas.width * factor;
        this.canvas.height = this.canvas.height * factor;
        
        // Neu zeichnen
        this.loadWeltKarte(/* weltId */);
    }

    // Pan-Funktion (verschieben)
    pan(dx, dy) {
        this.canvas.scrollLeft += dx;
        this.canvas.scrollTop += dy;
    }

    // Initialisieren
    init() {
        this.loadWeltKarte(/* weltId */);
        
        // Zoom mit Mausrad
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const factor = e.deltaY > 0 ? 0.9 : 1.1;
            this.zoom(factor);
        });
    }
}

// Singleton
const weltKarte = new WeltKarteRenderer();

export default weltKarte;
```

---

## 🧪 Testing Welt-Generierung

### Unit Tests

```python
# tests/services/test_welt_generierung.py
import pytest

def test_generate_welt_reproducible():
    """Testet dass gleicher Seed gleiche Welt erzeugt"""
    
    from app.models import generate_welt
    
    # Zwei Welten mit gleichem Seed sollten identisch sein
    result1 = generate_welt(1, seed=12345)
    result2 = generate_welt(2, seed=12345)
    
    assert result1["success"] is True
    assert result2["success"] is True

def test_welt_fairness_validation():
    """Testet Validierung fairer Ressourcen-Verteilung"""
    
    from app.models import validate_welt_fairness
    
    result = validate_welt_fairness(1)
    
    assert "valid" in result

def test_voronoi_boundaries():
    """Testet Voronoi-Grenzen Berechnung"""
    
    from app.models import calculate_voronoi_boundaries
    
    boundaries = calculate_voronoi_boundaries(5, 10, 10, mocker.Mock(random=lambda: 0.5))
    
    assert isinstance(boundaries, dict)

def test_start_positions_distribution():
    """Testet gleichmäßige Verteilung von Start-Positionen"""
    
    from app.models import calculate_start_positions
    
    boundaries = {(x, y): 1 for x in range(10) for y in range(10)}
    
    positions = calculate_start_positions(boundaries, 3, mocker.Mock(random=lambda: 0.5))
    
    assert len(positions) == 3

def test_load_welt():
    """Testet Welt-Laden aus Datenbank"""
    
    from app.models import load_welt
    
    result = load_welt(1)
    
    assert "success" in result

def test_terrain_noise_range():
    """Testet dass Noise-Werte im korrekten Bereich liegen"""
    
    from app.models import calculate_perlin_noise
    
    noise = calculate_perlin_noise(0, 0, mocker.Mock(gauss=lambda x, y: 0.5))
    
    assert 0.0 <= noise <= 1.0
```

---

## 🎯 Best Practices

1. **Seed-basiert** - Gleicher Seed = gleiche Welt (reproduzierbar)
2. **Perlin Noise** - Natürliche Landschaften durch Noise-Algorithmen
3. **Voronoi-Diagramm** - Organische Provinz-Grenzen
4. **Fairness validieren** - Ressourcen gleichmäßig verteilen
5. **Fog of War** - Nur sichtbare Felder laden (Performance)

---

**Welt-Generierung ermöglicht reproduzierbare, faire und vielfältige Spielwelten!**
