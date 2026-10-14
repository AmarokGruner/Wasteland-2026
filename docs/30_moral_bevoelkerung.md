# 👥 Moralsystem & Bevölkerung

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das Moralsystem: Moral-Wert, Gesundheit/Seuchen, Wanderung zwischen Provinzen, Geburtenrate und Bevölkerungswachstum.

---

## 🎯 Ziele

1. **Moral-System** - Zufriedenheit der Bevölkerung beeinflusst Produktion
2. **Gesundheit/Seuchen** - Krankheiten können Provinzen treffen
3. **Bevölkerungsdynamik** - Geburten, Sterbefälle, Wanderung
4. **Flucht-Mechanik** - Bei schlechten Bedingungen wandern Siedler ab

---

## 🏗️ Moralsystem Architektur

### Moral-Faktoren

```
Moral = Basis (50) 
       + Nahrung-Überschuss (+20 wenn > 1000)
       - Nahrung-Mangel (-30 wenn < 100)
       + Wohnraum-Verfügbarkeit (+15 wenn > Bevölkerung)
       - Überbelegung (-20 wenn < Bevölkerung)
       + Gesundheits-Zustand (+10 wenn keine Seuche)
       - Seuchen-Ausbruch (-40)
       + Kultur-Gebäude (+5 pro Universität/Schule)
       - Krieg-Schock (-25 wenn angegriffen)
```

### Moral-Faktoren im Detail (mit konkreten Werten)

| Faktor | Bedingung | Moral-Änderung | Beispiel |
|--------|-----------|----------------|----------|
| **Basis-Moral** | Startwert | +50 | Jede Provinz startet mit 50 |
| **Nahrung-Überschuss** | > 1.000 Nahrung | +20 | 1.500 Kartoffeln → +20 Moral |
| **Nahrung-Mangel** | < 100 Nahrung | -30 | Nur 50 Kartoffeln → -30 Moral |
| **Nahrung-Kritisch** | < 10 Nahrung | -50 | Hungersnot → -50 Moral |
| **Wohnraum-Verfügbarkeit** | > Bevölkerung | +15 | 200 Plätze, 150 Siedler → +15 Moral |
| **Überbelegung** | < Bevölkerung | -20 | 100 Plätze, 150 Siedler → -20 Moral |
| **Gesundheit (keine Seuche)** | Gesundheit > 70 | +10 | Gute Hygiene → +10 Moral |
| **Gesundheit (leicht krank)** | Gesundheit 40-70 | +5 | Leichte Erkältung → +5 Moral |
| **Gesundheit (schwer krank)** | Gesundheit < 40 | -10 | Schwere Krankheit → -10 Moral |
| **Seuchen-Ausbruch** | Seuche aktiv | -40 | Pest → -40 Moral |
| **Kultur-Gebäude** | Pro Universität/Schule | +5 | 2 Schulen → +10 Moral |
| **Krieg-Schock** | Provinz angegriffen | -25 | Angriff → -25 Moral |
| **Feiertag/Fest** | Sonderereignis | +10 | Erntedank → +10 Moral |
| **Naturkatastrophe** | Dürre/Flut/Erdbeben | -30 | Dürre → -30 Moral |

### Moral-Berechnung (Python-Code)

```python
async def berechne_moral(provinz_id: int):
    """Moral einer Provinz berechnen (pro 24h Tick)"""
    
    province = db.query(Province).get(provinz_id)
    siedler = db.query(Siedler).filter_by(province_id=province.id).first()
    
    if not siedler:
        return 50  # Default Moral
    
    moral = 50  # Basis-Moral
    
    # Nahrung-Überschuss/Mangel prüfen
    storage = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
    if storage:
        nahrung = getattr(storage, "resources_13", 0) or 0  # ID 13 = Kartoffeln
        
        if nahrung > 1000:
            moral += 20  # Nahrung-Überschuss
        elif nahrung < 100:
            moral -= 30  # Nahrung-Mangel
        elif nahrung < 10:
            moral -= 50  # Hungersnot
    
    # Wohnraum prüfen
    gebaeude = db.query(Building).filter_by(province_id=province.id, aktiv=True).all()
    gesamt_wohnraum = sum(g.typ.wohnraum for g in gebaeude)
    
    if gesamt_wohnraum > siedler.anzahl:
        moral += 15  # Genug Wohnraum
    elif gesamt_wohnraum < siedler.anzahl:
        moral -= 20  # Überbelegung
    
    # Gesundheit/Seuche prüfen
    if siedler.seuche_aktiv:
        moral -= 40  # Seuchen-Ausbruch
    elif siedler.gesundheit > 70:
        moral += 10  # Gute Gesundheit
    elif siedler.gesundheit < 40:
        moral -= 10  # Schlechte Gesundheit
    
    # Kultur-Gebäude zählen
    kultur_gebaeude = [g for g in gebaeude if g.typ.kultur_boni > 0]
    moral += len(kultur_gebaeude) * 5  # +5 pro Kultur-Gebäude
    
    # Krieg-Schock prüfen (wenn Provinz angegriffen)
    if province.angegriffen:
        moral -= 25
    
    # Moral auf 0-100 begrenzen
    moral = max(0, min(100, moral))
    
    siedler.moral = moral
    db.commit()
    
    return moral
```

### Moral-Effekte auf Bevölkerung (pro 24h Tick)

| Moral-Bereich | Geburtenrate | Sterbefälle | Wanderung | Beschreibung |
|---------------|--------------|-------------|-----------|--------------|
| **0-10** | -5% | +15% | -20% | Hungersnot, Flucht |
| **10-30** | -2% | +8% | -10% | Schlechte Bedingungen |
| **30-50** | 0% | +3% | -2% | Unterdurchschnittlich |
| **50-70** | +2% | +1% | 0% | Normal |
| **70-90** | +5% | -1% | +3% | Gut |
| **90-100** | +10% | -3% | +5% | Exzellent, Zuzug |

### Bevölkerungsberechnung (Python-Code)

```python
async def aktualisiere_bevoelkerung(provinz_id: int):
    """Bevölkerung pro Tick aktualisieren (24h Intervall)"""
    
    province = db.query(Province).get(provinz_id)
    siedler = db.query(Siedler).filter_by(province_id=province.id).first()
    
    if not siedler:
        return
    
    moral = siedler.moral
    
    # Geburtenrate (prozentual, pro 24h)
    if moral >= 90:
        geburten_rate = 0.10  # +10% pro Tag
    elif moral >= 70:
        geburten_rate = 0.05  # +5% pro Tag
    elif moral >= 50:
        geburten_rate = 0.02  # +2% pro Tag
    elif moral >= 30:
        geburten_rate = 0.0   # Keine Geburten
    elif moral >= 10:
        geburten_rate = -0.02  # -2% (Abwanderung)
    else:
        geburten_rate = -0.05  # -5% (Flucht)
    
    # Sterbefälle (prozentual, pro 24h)
    if siedler.gesundheit >= 80:
        sterberate = -0.03  # -3% (natürliches Altern)
    elif siedler.gesundheit >= 60:
        sterberate = +0.01  # +1% (leichte Krankheiten)
    elif siedler.gesundheit >= 40:
        sterberate = +0.03  # +3% (Krankheiten)
    elif siedler.gesundheit >= 20:
        sterberate = +0.08  # +8% (schwere Epidemie)
    else:
        sterberate = +0.15  # +15% (Massensterben)
    
    # Seuche beschleunigt Sterberate
    if siedler.seuche_aktiv:
        sterberate += 0.10  # +10% durch Seuche
    
    # Wanderung (netto, pro 24h)
    if moral >= 90:
        wanderung = int(siedler.anzahl * 0.05)  # +5% Zuzug
    elif moral >= 70:
        wanderung = int(siedler.anzahl * 0.03)  # +3% Zuzug
    elif moral >= 50:
        wanderung = 0  # Keine Wanderung
    elif moral >= 30:
        wanderung = -int(siedler.anzahl * 0.02)  # -2% Abwanderung
    elif moral >= 10:
        wanderung = -int(siedler.anzahl * 0.10)  # -10% Abwanderung
    else:
        wanderung = -int(siedler.anzahl * 0.20)  # -20% Flucht
    
    # Bevölkerung aktualisieren
    neue_geburten = int(siedler.anzahl * geburten_rate)
    neue_todesfaelle = int(siedler.anzahl * sterberate)
    
    siedler.anzahl += neue_geburten - neue_todesfaelle + wanderung
    
    # Mindestens 1 Siedler lassen (keine vollständige Auslöschung)
    siedler.anzahl = max(1, siedler.anzahl)
    
    print(f"👥 Provinz {province.id}: {siedler.anzahl} Siedler "
          f"(Geburten: +{neue_geburten}, Tode: -{neue_todesfaelle}, "
          f"Wanderung: {wanderung})")
    
    db.commit()
```

### Seuchen-System (Beispiele)

| Seuche-Typ | Ausbreitungsgeschwindigkeit | Sterberate | Moral-Effekt | Dauer (Tage) | Heilung |
|------------|---------------------------|------------|--------------|--------------|---------|
| **Erkältung** | Langsam (1-2 Tage) | +1% | -5 | 3-7 | Apotheken |
| **Grippe** | Mittel (2-4 Tage) | +3% | -10 | 5-10 | Krankenhäuser |
| **Cholera** | Schnell (1-3 Tage) | +8% | -20 | 7-14 | Sauberes Wasser |
| **Pest** | Sehr schnell (1-2 Tage) | +15% | -40 | 10-21 | Quarantäne |
| **Kriegsverletzungen** | Sofort | +5% | -15 | 3-7 | Lazarette |

---

## 📊 Datenbank-Schema für Bevölkerung

### Siedler & Moral

```python
# app/models.py - Bevölkerung Modelle

class Siedler(Base):
    """Siedler/Bevölkerung einer Provinz"""
    
    __tablename__ = "siedler"
    
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey("provinzen.id"))
    
    # Anzahl Siedler
    anzahl = Column(Integer, default=100)
    
    # Moral (0-100)
    moral = Column(Integer, default=50)
    
    # Gesundheit (0-100)
    gesundheit = Column(Integer, default=80)
    
    # Seuche aktiv?
    seuche_aktiv = Column(Boolean, default=False)
    
    # Seuche-Typ (wenn aktiv)
    seuche_typ = Column(String(50), nullable=True)
    
    # Geburten pro Tick (berechnet)
    geburten_pro_tick = Column(Integer, default=0)
    
    # Sterbefälle pro Tick (berechnet)
    sterbefaelle_pro_tick = Column(Integer, default=0)
    
    # Wanderung (netto pro Tick)
    wanderung_netto = Column(Integer, default=0)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Seuche(Base):
    """Seuchen/Ausbrüche"""
    
    __tablename__ = "seuchen"
    
    id = Column(Integer, primary_key=True)
    
    name = Column(String(100), nullable=False)  # z.B. "Pest", "Grippe"
    
    beschreibung = Column(Text)
    
    # Übertragungsrate (0-1, wie schnell sich ausbreitet)
    uebertragungs_rate = Column(Float, default=0.3)
    
    # Sterblichkeitsrate (0-1)
    sterblichkeits_rate = Column(Float, default=0.1)
    
    # Dauer in Ticks
    dauer_ticks = Column(Integer, default=20)
    
    # Auswirkungen auf Moral (-20 bis -50)
    moral_auswirkung = Column(Integer, default=-30)
    
    # Auswirkungen auf Produktion (-10% bis -50%)
    produktion_auswirkung = Column(Integer, default=-20)

# Helper: Moral berechnen
def calculate_moral(province_id: int) -> int:
    """Moral einer Provinz berechnen"""
    
    from app.models import Province, Building, ProvinceStorage
    
    province = db.query(Province).get(province_id)
    
    if not province:
        return 50
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return 50
    
    moral = 50  # Basis-Moral
    
    # Nahrung-Überschuss/Mangel
    lager = db.query(ProvinceStorage).filter_by(province_id=province_id).first()
    
    if lager:
        nahrung = lager.resources_food or 0
        
        if nahrung > 1000:
            moral += 20  # Überschuss → gute Moral
        elif nahrung < 100:
            moral -= 30  # Mangel → schlechte Moral
    
    # Wohnraum (Gebäude bieten Wohnraum)
    gebaeude = db.query(Building).filter_by(province_id=province_id, aktiv=True).all()
    
    gesamt_wohnraum = 0
    for gebaeude in gebaeude:
        wohnraum = gebaeude.typ.wohnraum or 0
        gesamt_wohnraum += wohnraum * gebaeude.stufe
    
    bevoelkerung = siedler.anzahl
    
    if gesamt_wohnraum > bevoelkerung:
        moral += 15  # Genug Wohnraum
    elif gesamt_wohnraum < bevoelkerung:
        moral -= 20  # Überbelegung
    
    # Gesundheit/Seuchen
    if siedler.seuche_aktiv:
        moral += siedler.moral_auswirkung  # Negativ durch Seuche
    
    if siedler.gesundheit < 50:
        moral -= 10  # Schlechte Gesundheit
    
    # Kultur-Gebäude (positive Wirkung)
    kultur_gebaeude = db.query(Building).filter_by(
        province_id=province_id,
        typ_in=["universitaet", "schule", "tempel"]
    ).all()
    
    moral += len(kultur_gebaeude) * 5
    
    # Krieg-Schock (wenn Provinz angegriffen wurde)
    letzte_kämpfe = db.query(KampfLog).filter_by(
        verteidiger_provinz_id=province_id
    ).order_by(KampfLog.tick.desc()).limit(1).first()
    
    if letzte_kämpfe and tick_manager.current_tick - letzte_kämpfe.tick < 3:
        moral -= 25  # Krieg-Schock
    
    # Moral auf 0-100 begrenzen
    moral = max(0, min(moral, 100))
    
    return moral

# Helper: Geburtenrate berechnen
def calculate_geburten_rate(province_id: int) -> int:
    """Geburten pro Tick berechnen"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return 0
    
    moral = siedler.moral
    
    # Geburtenrate: Moral × 0.1 (prozentual)
    geburten = int(siedler.anzahl * moral * 0.001)
    
    return max(0, geburten)

# Helper: Sterbefälle berechnen
def calculate_sterbefaelle(province_id: int) -> int:
    """Sterbefälle pro Tick berechnen"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return 0
    
    sterbefaelle = int(siedler.anzahl * 0.001)  # Basis: 0.1%
    
    # Gesundheit reduziert Sterbefälle
    if siedler.gesundheit > 80:
        sterbefaelle = int(sterbefaelle * 0.5)
    
    # Seuche erhöht Sterbefälle stark
    if siedler.seuche_aktiv:
        seuche = db.query(Seuche).get(siedler.seuche_typ)
        
        if seuche:
            sterbefaelle += int(siedler.anzahl * seuche.sterblichkeits_rate)
    
    return max(0, sterbefaelle)

# Helper: Wanderung berechnen
def calculate_wanderung(province_id: int) -> int:
    """Wanderung (netto) pro Tick berechnen"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return 0
    
    moral = siedler.moral
    
    wanderung = 0
    
    # Bei schlechter Moral (< 30) wandern Siedler ab
    if moral < 30:
        wanderung -= int(siedler.anzahl * 0.05)  # 5% wandern ab
    
    # Bei guter Moral (> 70) kommen Siedler aus Nachbar-Provinzen
    elif moral > 70:
        wanderung += int(siedler.anzahl * 0.02)  # 2% kommen hinzu
    
    return wanderung

# Helper: Seuchen-Ausbruch prüfen
def check_seuchen_ausbruch(province_id: int):
    """Zufälliger Seuchen-Ausbruch prüfen"""
    
    import random
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler or siedler.seuche_aktiv:
        return
    
    # 2% Chance pro Tick für Seuchen-Ausbruch
    if random.random() < 0.02:
        # Zufällige Seuche auswählen
        seuchen = db.query(Seuche).all()
        
        if seuchen:
            seuche = random.choice(seuchen)
            
            siedler.seuche_aktiv = True
            siedler.seuche_typ = seuche.name
            siedler.gesundheit = max(siedler.gesundheit - 30, 0)
            
            print(f"🦠 Seuchen-Ausbruch in Provinz {province_id}: {seuche.name}")

# Helper: Bevölkerung pro Tick aktualisieren
def update_bevoelkerung_pro_tick():
    """Bevölkerungs-Dynamik pro Tick berechnen und anwenden"""
    
    siedler_liste = db.query(Siedler).all()
    
    for siedler in siedler_liste:
        province_id = siedler.province_id
        
        # Moral berechnen und aktualisieren
        moral = calculate_moral(province_id)
        siedler.moral = moral
        
        # Gesundheit aktualisieren (langsame Erholung oder Verschlechterung)
        if siedler.seuche_aktiv:
            # Seuche breitet sich aus oder klingt ab
            siedler.gesundheit = max(siedler.gesundheit - 5, 0)
            
            # Seuche kann abklingen (nach 20 Ticks)
            # In Production: Seuche-Dauer tracken
            
        else:
            # Keine Seuche → langsame Genesung
            siedler.gesundheit = min(siedler.gesundheit + 2, 100)
        
        # Geburten und Sterbefälle berechnen
        geburten = calculate_geburten_rate(province_id)
        sterbefaelle = calculate_sterbefaelle(province_id)
        
        # Wanderung berechnen
        wanderung = calculate_wanderung(province_id)
        
        # Bevölkerung aktualisieren
        siedler.anzahl += geburten - sterbefaelle + wanderung
        
        # Mindestens 1 Siedler muss bleiben
        siedler.anzahl = max(siedler.anzahl, 1)
        
        # Pro Tick Werte speichern (für UI)
        siedler.geburten_pro_tick = geburten
        siedler.sterbefaelle_pro_tick = sterbefaelle
        siedler.wanderung_netto = wanderung
        
        db.commit()

# Helper: Seuche auf benachbarte Provinzen ausbreiten
def breite_seuche_aus(province_id: int):
    """Seuche auf angrenzende Provinzen ausbreiten"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler or not siedler.seuche_aktiv:
        return
    
    seuche = db.query(Seuche).get(siedler.seuche_typ)
    
    if not seuche:
        return
    
    # Benachbarte Provinzen finden
    benachbarte = get_benachbarte_provinzen(province_id)
    
    for benachbarte_id in benachbarte:
        benachbarte_siedler = db.query(Siedler).filter_by(province_id=benachbarte_id).first()
        
        if benachbarte_siedler and not benachbarte_siedler.seuche_aktiv:
            # Übertragungs-Chance
            if random.random() < seuche.uebertragungs_rate:
                benachbarte_siedler.seuche_aktiv = True
                benachbarte_siedler.seuche_typ = seuche.name
                benachbarte_siedler.gesundheit = max(benachbarte_siedler.gesundheit - 20, 0)
                
                print(f"🦠 Seuche breitet sich aus: Provinz {benachbarte_id} infiziert")

def get_benachbarte_provinzen(province_id: int) -> list:
    """Benachbarte Provinzen finden (nach Koordinaten)"""
    
    from app.models import Province
    
    province = db.query(Province).get(province_id)
    
    if not province:
        return []
    
    benachbarte = []
    
    alle_provinzen = db.query(Province).all()
    
    for p in alle_provinzen:
        if p.id == province_id:
            continue
        
        dx = abs(p.x - province.x)
        dy = abs(p.y - province.y)
        
        if dx <= 1 and dy <= 1 and (dx + dy) > 0:
            benachbarte.append(p.id)
    
    return benachbarte
```

---

## 📡 API Endpunkte für Bevölkerung

### Bevölkerung Router

```python
# app/api/v1/bevoelkerung.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/province/{province_id}/bevoelkerung")
async def get_bevoelkerungsdaten(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bevölkerungsdaten einer Provinz abrufen"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        # Siedler erstellen wenn nicht vorhanden
        siedler = Siedler(
            province_id=province_id,
            anzahl=100,
            moral=50,
            gesundheit=80
        )
        db.add(siedler)
        db.commit()
    
    moral = calculate_moral(province_id)
    geburten = calculate_geburten_rate(province_id)
    sterbefaelle = calculate_sterbefaelle(province_id)
    wanderung = calculate_wanderung(province_id)
    
    return {
        "province_id": province_id,
        "bevoelkerung": siedler.anzahl,
        "moral": moral,
        "gesundheit": siedler.gesundheit,
        "seuche_aktiv": siedler.seuche_aktiv,
        "seuche_typ": siedler.seuche_typ if siedler.seuche_aktiv else None,
        "geburten_pro_tick": geburten,
        "sterbefaelle_pro_tick": sterbefaelle,
        "wanderung_netto": wanderung,
        "netto_wachstum": geburten - sterbefaelle + wanderung
    }

@router.get("/province/{province_id}/seuchen")
async def get_seuchen_info(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seuchen-Informationen abrufen"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return {"seuche_aktiv": False}
    
    if not siedler.seuche_aktiv:
        return {"seuche_aktiv": False}
    
    seuche = db.query(Seuche).get(siedler.seuche_typ)
    
    if not seuche:
        return {"seuche_aktiv": False}
    
    return {
        "seuche_aktiv": True,
        "name": seuche.name,
        "beschreibung": seuche.beschreibung,
        "uebertragungs_rate": seuche.uebertragungs_rate,
        "sterblichkeits_rate": seuche.sterblichkeits_rate,
        "moral_auswirkung": seuche.moral_auswirkung,
        "produktion_auswirkung": seuche.produktion_auswirkung
    }

@router.post("/province/{province_id}/massnahme/gesundheit")
async def massnahme_gesundheit(
    province_id: int,
    data: MassnahmeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gesundheits-Massnahme ergreifen (Arzt, Quarantäne)"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        raise HTTPException(status_code=404, detail={"code": "NO_SIEDLER", "message": "Keine Siedler"})
    
    massnahme_typ = data.massnahme_typ
    
    if massnahme_typ == "arzt":
        # Arzt kostet 100 MIPS, erhöht Gesundheit um 20
        lager = db.query(ProvinceStorage).filter_by(province_id=province_id).first()
        
        if not lager or lager.resources_mips < 100:
            raise HTTPException(
                status_code=400,
                detail={"code": "INSUFFICIENT_MIPS", "message": "Nicht genug MIPS (100 benötigt)"}
            )
        
        siedler.gesundheit = min(siedler.gesundheit + 20, 100)
        lager.resources_mips -= 100
        
        db.commit()
        
        return {"message": "Arzt eingesetzt, Gesundheit +20"}
    
    elif massnahme_typ == "quarantäne":
        # Quarantäne kostet 200 MIPS, reduziert Seuchen-Ausbreitung
        lager = db.query(ProvinceStorage).filter_by(province_id=province_id).first()
        
        if not lager or lager.resources_mips < 200:
            raise HTTPException(
                status_code=400,
                detail={"code": "INSUFFICIENT_MIPS", "message": "Nicht genug MIPS (200 benötigt)"}
            )
        
        # Seuche aktiv? Dann Quarantäne effektiv
        if siedler.seuche_aktiv:
            siedler.gesundheit = min(siedler.gesundheit + 30, 100)
            siedler.seuche_aktiv = False  # Quarantäne stoppt Seuche
            
            lager.resources_mips -= 200
            db.commit()
            
            return {"message": "Quarantäne erfolgreich, Seuche gestoppt"}
        else:
            raise HTTPException(
                status_code=400,
                detail={"code": "NO_SEUCHE", "message": "Keine aktive Seuche"}
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_MASSNAHME", "message": "Ungültige Massnahme"}
        )

@router.get("/seuchen")
async def list_all_seuchen(
    db: Session = Depends(get_db)
):
    """Alle verfügbaren Seuchen auflisten"""
    
    seuchen = db.query(Seuche).all()
    
    seuchen_liste = []
    
    for s in seuchen:
        seuchen_liste.append({
            "id": s.id,
            "name": s.name,
            "beschreibung": s.beschreibung,
            "uebertragungs_rate": s.uebertragungs_rate,
            "sterblichkeits_rate": s.sterblichkeits_rate,
            "dauer_ticks": s.dauer_ticks,
            "moral_auswirkung": s.moral_auswirkung,
            "produktion_auswirkung": s.produktion_auswirkung
        })
    
    return {"seuchen": seuchen_liste}
```

---

## ⏱️ Tick-Integration: Bevölkerung pro Tick

### Bevölkerungs-Update im Server-Tick

```python
# app/services/tick_manager.py - Erweitert um Bevölkerung

async def execute_tick(self):
    """Einzelnen Tick verarbeiten (erweitert)"""
    
    # ... bestehende Logik ...
    
    # 8. Bevölkerung aktualisieren (Moral, Geburten, Seuchen)
    await self.update_bevoelkerung()

async def update_bevoelkerung(self):
    """Bevölkerungs-Dynamik pro Tick berechnen"""
    
    # Bevölkerung aktualisieren
    update_bevoelkerung_pro_tick()
    
    # Seuchen auf benachbarte Provinzen ausbreiten
    siedler_liste = db.query(Siedler).filter_by(seuche_aktiv=True).all()
    
    for siedler in siedler_liste:
        breite_seuche_aus(siedler.province_id)

# Helper: Moral-Bonus auf Produktion anwenden
def apply_moral_produktions_bonus(province_id: int) -> float:
    """Moral-Bonus auf Ressourcen-Produktion anwenden"""
    
    siedler = db.query(Siedler).filter_by(province_id=province_id).first()
    
    if not siedler:
        return 1.0
    
    moral = siedler.moral
    
    # Moral 100 = 100% Produktion
    # Moral 50 = 75% Produktion
    # Moral 0 = 50% Produktion
    
    produktions_bonus = 0.5 + (moral / 200.0)  # 0.5 bis 1.0
    
    return produktions_bonus
```

---

## 🖥️ Client-Side Bevölkerung UI (JavaScript)

### Bevölkerung Manager

```javascript
// js/game/bevoelkerung-manager.js

class BevoelkerungManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Bevölkerungsdaten laden
    async loadBevoelkerung(provinzId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/province/${provinzId}/bevoelkerung`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderBevoelkerung(data);
            }
        } catch (error) {
            console.error('Bevölkerung Load Error:', error);
        }
    }

    // Bevölkerungsdaten im UI rendern
    renderBevoelkerung(data) {
        const container = document.getElementById('bevoelkerung-panel');
        
        if (!container) return;

        let html = '<h3>👥 Bevölkerung</h3>';
        
        // Siedler-Anzahl
        html += `<div class="bevoelkerung-anzahl"><strong>${data.bevoelkerung}</strong> Siedler</div>`;
        
        // Moral-Balken
        const moralColor = data.moral > 70 ? '#4caf50' : 
                          data.moral > 40 ? '#ff8c00' : '#ff0000';
        
        html += `
            <div class="moral-bar">
                <p>Moral: ${data.moral}%</p>
                <div class="bar-container">
                    <div class="bar-fill" style="width: ${data.moral}%; background-color: ${moralColor}"></div>
                </div>
            </div>
        `;
        
        // Gesundheit/Seuche
        if (data.seuche_aktiv) {
            html += `
                <div class="seuche-warning">
                    <p>🦠 Seuche: ${data.seuche_typ}</p>
                    <p>Gesundheit: ${data.gesundheit}%</p>
                </div>
            `;
        } else {
            html += `<p class="gesundheit">Gesundheit: ${data.gesundheit}%</p>`;
        }
        
        // Demografie (Geburten, Sterbefälle, Wanderung)
        html += '<div class="demografie">';
        html += `<p>👶 Geburten: +${data.geburten_pro_tick}/Tick</p>`;
        html += `<p>💀 Sterbefälle: -${data.sterbefaelle_pro_tick}/Tick</p>`;
        html += `<p>🚶 Wanderung: ${data.wanderung_netto >= 0 ? '+' : ''}${data.wanderung_netto}/Tick</p>`;
        html += `<p><strong>Netto: ${data.netto_wachstum >= 0 ? '+' : ''}${data.netto_wachstum}</strong></p>`;
        html += '</div>';

        container.innerHTML = html;
    }

    // Gesundheits-Massnahme ergreifen
    async ergreifeMassnahme(provinzId, massnahmeTyp) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/province/${provinzId}/massnahme/gesundheit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ massnahme_typ: massnahmeTyp })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(data.message);
                await this.loadBevoelkerung(provinzId);
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Massnahme Error:', error);
        }
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `bevoelkerung-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        // Periodisch aktualisieren (alle 60s = pro Tick)
        setInterval(() => {
            this.loadBevoelkerung(/* aktuelle Provinz */);
        }, 60000);
    }
}

// Singleton
const bevoelkerung = new BevoelkerungManager();

export default bevoelkerung;
```

---

## 🧪 Testing Moralsystem

### Unit Tests

```python
# tests/services/test_bevoelkerung_service.py
import pytest

def test_calculate_moral():
    """Testet Moral-Berechnung"""
    
    from app.models import calculate_moral
    
    # Mock Provinz mit guter Nahrung → hohe Moral
    pass  # Integrationstest erforderlich
    
    # Annahme: Basis-Moral = 50
    assert calculate_moral(1) >= 0
    assert calculate_moral(1) <= 100

def test_calculate_geburten_rate():
    """Testet Geburtenraten-Berechnung"""
    
    from app.models import calculate_geburten_rate
    
    # Bei Moral 100 und 100 Siedlern: 100 × 100 × 0.001 = 10 Geburten
    pass  # Integrationstest

def test_calculate_sterbefaelle():
    """Testet Sterbefälle-Berechnung"""
    
    from app.models import calculate_sterbefaelle
    
    # Basis: 0.1% der Bevölkerung
    pass  # Integrationstest

def test_calculate_wanderung():
    """Testet Wanderungs-Berechnung"""
    
    from app.models import calculate_wanderung
    
    # Bei Moral < 30: -5% wandern ab
    # Bei Moral > 70: +2% kommen hinzu
    pass  # Integrationstest

def test_check_seuchen_ausbruch():
    """Testet Seuchen-Ausbruch (Zufall)"""
    
    from app.models import check_seuchen_ausbruch
    
    # 2% Chance pro Tick
    pass  # Integrationstest

def test_update_bevoelkerung_pro_tick():
    """Testet Bevölkerungs-Update pro Tick"""
    
    from app.models import update_bevoelkerung_pro_tick
    
    # Siedler-Anzahl sollte sich ändern (Geburten/Sterbefälle)
    pass  # Integrationstest

def test_apply_moral_produktions_bonus():
    """Testet Moral-Bonus auf Produktion"""
    
    from app.models import apply_moral_produktions_bonus
    
    bonus = apply_moral_produktions_bonus(1)
    
    assert 0.5 <= bonus <= 1.0  # 50% bis 100%
```

---

## 🎯 Best Practices

1. **Moral beeinflusst Produktion** - Zufriedene Bevölkerung produziert mehr
2. **Seuchen realistisch** - Übertragung auf Nachbarn, Gesundheits-Massnahmen
3. **Wanderung dynamisch** - Bei schlechter Moral wandern Siedler ab
4. **Geburtenrate proportional** - Mehr Siedler = mehr Geburten
5. **Massnahmen kostspielig** - Arzt/Quarantäne kosten MIPS

---

**Moralsystem ermöglicht Bevölkerungsdynamik mit Moral, Gesundheit, Seuchen und Wanderung!**
