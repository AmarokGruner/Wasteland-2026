# 💰 Wirtschaft & Preis-System

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt das dynamische Wirtschaftssystem: Preis-Fluktuation, automatische Kontore (KI-Händler), Inflation/Deflation und Steuer-System.

---

## 🎯 Ziele

1. **Dynamische Preise** - Angebot und Nachfrage beeinflussen Preise
2. **KI-Händler (Kontore)** - Automatischer Handel ohne Player-Interaktion
3. **Wirtschaftszyklen** - Inflation/Deflation über Zeit
4. **Steuer-System** - Provinzen können Steuern festlegen

---

## 🏗️ Wirtschaftssystem Architektur

### Preis-Berechnung

```
Preis = Basiswert × (Nachfrage / Angebot) × Zeitfaktor × Zufall
```

### Komponenten

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Produktion  │────▶│   Angebot     │────▶│             │
│   (Gebäude)   │     │   (Lager)     │     │             │
└─────────────┘     └──────────────┘     │             │
                                         │  Preis-    │
┌─────────────┐     ┌──────────────┐     │  Engine    │
│   Nachfrage   │────▶│   Handel      │     │             │
│   (Player)   │     │   (Markt)     │     └─────────────┘
└─────────────┘     └──────────────┘              │
                                                   ▼
                                          ┌──────────────┐
                                          │   KI-Händler  │
                                          │   (Kontore)   │
                                          └──────────────┘
```

---

## 📊 Datenbank-Schema für Wirtschaft

### Marktpreise & Kontore

```python
# app/models.py - Wirtschaft Modelle

class Marktpreis(Base):
    """Aktuelle Marktpreise für Ressourcen/Artikel"""
    
    __tablename__ = "marktpreise"
    
    id = Column(Integer, primary_key=True)
    artikel_id = Column(Integer, ForeignKey("artikel.id"), unique=True)
    
    # Aktueller Preis (in MIPS)
    aktueller_preis = Column(Integer, default=100)
    
    # Basispreis (unverändert seit Spielstart)
    basispreis = Column(Integer, default=100)
    
    # Angebot (verfügbare Menge auf dem Markt)
    angebot_menge = Column(Integer, default=0)
    
    # Nachfrage (gewünschte Menge von Spielern)
    nachfrage_menge = Column(Integer, default=0)
    
    # Preis-Verlauf (JSON: letzte 100 Ticks)
    preis_verlauf = Column(Text, default="[]")
    
    # Letzte Preis-Änderung
    letzte_änderung = Column(DateTime, default=datetime.utcnow)
    
    # Preis-Änderung pro Tick (automatisch durch KI-Händler)
    ki_handel_menge = Column(Integer, default=0)  # KI kauft/verkauft pro Tick
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Kontor(Base):
    """Automatischer KI-Händler (Kontor)"""
    
    __tablename__ = "kontore"
    
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey("provinzen.id"))
    
    # Gehört zu welcher Provinz
    owner_provinz_id = Column(Integer, ForeignKey("provinzen.id"))
    
    # Handelt mit welchen Artikel-IDs (JSON Array)
    gehandelte_artikel = Column(Text, default="[]")
    
    # Handels-Volumen pro Tick (wie viele Einheiten)
    handels_volumen = Column(Integer, default=10)
    
    # Max Lager-Menge pro Artikel (JSON)
    max_lager = Column(Text, default="{}")
    
    # KI-Strategie (aggressiv, neutral, konservativ)
    ki_strategie = Column(String(50), default="neutral")
    
    # Profit seit Erstellung (JSON: kumuliert)
    kumulierter_profit = Column(Integer, default=0)
    
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Helper: Preis berechnen (Angebot/Nachfrage)
def calculate_marktpreis(artikel_id: int, angebot: int, nachfrage: int) -> int:
    """Marktpreis basierend auf Angebot und Nachfrage berechnen"""
    
    from app.models import Artikel
    
    artikel = db.query(Artikel).get(artikel_id)
    
    if not artikel:
        return 100  # Default Preis
    
    basispreis = artikel.wert or 100
    
    # Verhältnis berechnen
    if angebot == 0 and nachfrage == 0:
        # Kein Handel → Basispreis
        return basispreis
    
    if angebot == 0:
        # Kein Angebot → Preis explodiert (sehr hoch)
        return basispreis * 10
    
    if nachfrage == 0:
        # Keine Nachfrage → Preis fällt (sehr niedrig)
        return max(basispreis // 10, 1)
    
    # Verhältnis: Nachfrage / Angebot
    verhältnis = nachfrage / angebot
    
    # Preis anpassen (nicht linear, sondern exponentiell für Realismus)
    if verhältnis > 1:
        # Nachfrage > Angebot → Preis steigt
        preisanstieg = verhältnis ** 1.5  # Exponent für stärkere Reaktion
        neuer_preis = int(basispreis * preisanstieg)
    else:
        # Angebot > Nachfrage → Preis fällt
        preisfall = verhältnis ** 0.8  # Sanfterer Fall
        neuer_preis = int(basispreis * preisfall)
    
    # Grenzen setzen (nicht zu extrem)
    neuer_preis = max(1, min(neuer_preis, basispreis * 20))
    
    return neuer_preis

# Helper: KI-Händler Logik
def ki_handel_logik(kontor: Kontor, artikel_id: int, aktueller_preis: int) -> dict:
    """KI-Handelsentscheidung treffen"""
    
    from app.models import Marktpreis
    
    marktpreis = db.query(Marktpreis).get(artikel_id)
    
    if not marktpreis:
        return {"aktion": "keine", "menge": 0}
    
    strategie = kontor.ki_strategie
    
    if strategie == "aggressiv":
        # KI kauft bei niedrigen Preisen, verkauft bei hohen
        if aktueller_preis < marktpreis.basispreis * 0.8:
            return {"aktion": "kaufen", "menge": kontor.handels_volumen}
        elif aktueller_preis > marktpreis.basispreis * 1.3:
            return {"aktion": "verkaufen", "menge": kontor.handels_volumen}
        else:
            return {"aktion": "halten", "menge": 0}
    
    elif strategie == "konservativ":
        # KI handelt nur bei starken Preisschwankungen
        if aktueller_preis < marktpreis.basispreis * 0.6:
            return {"aktion": "kaufen", "menge": kontor.handels_volumen // 2}
        elif aktueller_preis > marktpreis.basispreis * 1.5:
            return {"aktion": "verkaufen", "menge": kontor.handels_volumen // 2}
        else:
            return {"aktion": "halten", "menge": 0}
    
    else:  # neutral
        # KI gleicht Angebot/Nachfrage aus
        if marktpreis.angebot_menge > marktpreis.nachfrage_menge * 1.5:
            return {"aktion": "kaufen", "menge": kontor.handels_volumen}
        elif marktpreis.nachfrage_menge > marktpreis.angebot_menge * 1.5:
            return {"aktion": "verkaufen", "menge": kontor.handels_volumen}
        else:
            return {"aktion": "halten", "menge": 0}

# Helper: Preis-Update pro Tick
def update_marktpreise_pro_tick():
    """Alle Marktpreise pro Tick aktualisieren"""
    
    marktpreise = db.query(Marktpreis).all()
    
    for mp in marktpreise:
        # Angebot und Nachfrage berechnen
        angebot = calculate_total_angebot(mp.artikel_id)
        nachfrage = calculate_total_nachfrage(mp.artikel_id)
        
        # Neuen Preis berechnen
        neuer_preis = calculate_marktpreis(mp.artikel_id, angebot, nachfrage)
        
        # Preis-Verlauf aktualisieren (letzte 100 Ticks)
        verlauf = json.loads(mp.preis_verlauf) if mp.preis_verlauf else []
        verlauf.append(neuer_preis)
        
        if len(verlauf) > 100:
            verlauf = verlauf[-100:]
        
        mp.preis_verlauf = json.dumps(verlauf)
        mp.aktueller_preis = neuer_preis
        mp.angebot_menge = angebot
        mp.nachfrage_menge = nachfrage
        mp.letzte_änderung = datetime.utcnow()
        
        # KI-Händler Aktionen ausführen
        kontore = db.query(Kontor).filter_by(gehandelte_artikel=f'"{mp.artikel_id}"').all()
        
        for kontor in kontore:
            ki_entscheidung = ki_handel_logik(kontor, mp.artikel_id, neuer_preis)
            
            if ki_entscheidung["aktion"] == "kaufen":
                # KI kauft vom Markt (erhöht Nachfrage)
                mp.nachfrage_menge += ki_entscheidung["menge"]
            
            elif ki_entscheidung["aktion"] == "verkaufen":
                # KI verkauft auf den Markt (erhöht Angebot)
                mp.angebot_menge += ki_entscheidung["menge"]

def calculate_total_angebot(artikel_id: int) -> int:
    """Gesamtes Angebot einer Ressource auf allen Märkten berechnen"""
    
    # Lagerbestände aller Provinzen
    lager = db.query(ProvinceStorage).all()
    
    gesamt_angebot = 0
    
    for lager in lager:
        res_key = f"resources_artikel_{artikel_id}"
        menge = getattr(lager, res_key, 0)
        gesamt_angebot += menge
    
    return gesamt_angebot

def calculate_total_nachfrage(artikel_id: int) -> int:
    """Gesamte Nachfrage einer Ressource berechnen"""
    
    # Nachfrage kommt von Player-Handelsaktionen (letzte Ticks)
    handelaktionen = db.query(Handelslog).filter_by(artikel_id=artikel_id).order_by(Handelslog.tick.desc()).limit(10).all()
    
    gesamt_nachfrage = 0
    
    for aktion in handelaktionen:
        gesamt_nachfrage += aktion.menge
    
    return gesamt_nachfrage

# Helper: Inflation/Deflation berechnen
def calculate_inflation_rate() -> float:
    """Inflationsrate über alle Preise berechnen"""
    
    marktpreise = db.query(Marktpreis).all()
    
    if not marktpreise:
        return 0.0
    
    gesamt_preisänderung = 0
    
    for mp in marktpreise:
        verlauf = json.loads(mp.preis_verlauf) if mp.preis_verlauf else []
        
        if len(verlauf) >= 10:
            # Veränderung der letzten 10 Ticks
            alter_preis = verlauf[0]
            neuer_preis = verlauf[-1]
            
            if alter_preis > 0:
                anteil = (neuer_preis - alter_preis) / alter_preis
                gesamt_preisänderung += anteil
    
    # Durchschnittliche Preisänderung
    inflationsrate = gesamt_preisänderung / len(marktpreise)
    
    return round(inflationsrate * 100, 2)  # In Prozent

# Helper: Steuern berechnen
def calculate_provinz_steuern(province_id: int) -> int:
    """Steuereinnahmen einer Provinz berechnen"""
    
    from app.models import Province
    
    province = db.query(Province).get(province_id)
    
    if not province:
        return 0
    
    # Steuerquote (0-20%, default 10%)
    steuer_quote = province.steuer_quote or 10
    
    # Wirtschaftsleistung der Provinz (Summe aller Gebäude-Produktion)
    gebaeude = db.query(Building).filter_by(province_id=province_id, aktiv=True).all()
    
    wertschöpfung = 0
    
    for gebaeude in gebaeude:
        produktion = gebaeude.typ.produktion  # JSON
        wertschöpfung += sum(produktion.values()) if produktion else 0
    
    # Steuern = Wertschöpfung × Steuerquote
    steuern = int(wertschöpfung * steuer_quote / 100)
    
    return steuern
```

---

## 📡 API Endpunkte für Wirtschaft

### Markt Router

```python
# app/api/v1/markt.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/markt/preise")
async def get_all_marktpreise(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alle aktuellen Marktpreise abrufen"""
    
    marktpreise = db.query(Marktpreis).all()
    
    preise = []
    
    for mp in marktpreise:
        artikel = db.query(Artikel).get(mp.artikel_id)
        
        preise.append({
            "id": mp.artikel_id,
            "name": artikel.name if artikel else "Unbekannt",
            "aktueller_preis": mp.aktueller_preis,
            "basispreis": mp.basispreis,
            "angebot_menge": mp.angebot_menge,
            "nachfrage_menge": mp.nachfrage_menge,
            "preis_trend": get_preistrend(mp.preis_verlauf) if mp.preis_verlauf else "neutral"
        })
    
    # Inflationsrate hinzufügen
    inflationsrate = calculate_inflation_rate()
    
    return {
        "preise": preise,
        "inflationsrate": f"{inflationsrate}%"
    }

@router.get("/markt/{artikel_id}")
async def get_artikel_preis(
    artikel_id: int,
    db: Session = Depends(get_db)
):
    """Einzelnen Artikel-Preis abrufen"""
    
    marktpreis = db.query(Marktpreis).get(artikel_id)
    
    if not marktpreis:
        raise HTTPException(status_code=404, detail={"code": "ARTIKEL_NOT_FOUND", "message": "Artikel nicht gefunden"})
    
    artikel = db.query(Artikel).get(artikel_id)
    
    return {
        "id": artikel_id,
        "name": artikel.name if artikel else "Unbekannt",
        "aktueller_preis": marktpreis.aktueller_preis,
        "basispreis": marktpreis.basispreis,
        "angebot": marktpreis.angebot_menge,
        "nachfrage": marktpreis.nachfrage_menge,
        "preis_verlauf": json.loads(marktpreis.preis_verlauf) if marktpreis.preis_verlauf else []
    }

@router.post("/markt/handeln")
async def handeln(
    data: HandelsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handelsaktion zwischen Provinzen"""
    
    von_provinz = db.query(Province).filter_by(id=data.von_provinz_id, owner_id=current_user.id).first()
    
    if not von_provinz:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    ziel_provinz = db.query(Province).get(data.ziel_provinz_id)
    
    if not ziel_provinz:
        raise HTTPException(status_code=404, detail={"code": "PROVINZ_NOT_FOUND", "message": "Nicht gefunden"})
    
    # Marktpreis abrufen
    marktpreis = db.query(Marktpreis).get(data.artikel_id)
    
    if not marktpreis:
        raise HTTPException(status_code=404, detail={"code": "ARTIKEL_NOT_FOUND", "message": "Artikel nicht gefunden"})
    
    # Lagerbestände prüfen
    lager_von = db.query(ProvinceStorage).filter_by(province_id=data.von_provinz_id).first()
    
    res_key = f"resources_artikel_{data.artikel_id}"
    verfuegbare_menge = getattr(lager_von, res_key, 0)
    
    if verfuegbare_menge < data.menge:
        raise HTTPException(
            status_code=400,
            detail={"code": "INSUFFICIENT_STOCK", "message": "Nicht genug Lagerbestand"}
        )
    
    # Transaktionsbetrag berechnen
    transaktionsbetrag = marktpreis.aktueller_preis * data.menge
    
    # Ressourcen transferieren
    setattr(lager_von, res_key, verfuegbare_menge - data.menge)
    
    lager_ziel = db.query(ProvinceStorage).filter_by(province_id=data.ziel_provinz_id).first()
    ziel_menge = getattr(lager_ziel, res_key, 0)
    setattr(lager_ziel, res_key, ziel_menge + data.menge)
    
    # MIPS transferieren (Käufer zahlt)
    mips_ziel = lager_ziel.resources_mips
    lager_ziel.resources_mips = mips_ziel + transaktionsbetrag
    
    mips_von = lager_von.resources_mips
    lager_von.resources_mips = mips_von - transaktionsbetrag
    
    # Handelslog erstellen
    handelslog = Handelslog(
        tick=tick_manager.current_tick,
        von_provinz_id=data.von_provinz_id,
        ziel_provinz_id=data.ziel_provinz_id,
        artikel_id=data.artikel_id,
        menge=data.menge,
        preis_pro_einheit=marktpreis.aktueller_preis,
        gesamtpreis=transaktionsbetrag
    )
    
    db.add(handelslog)
    db.commit()
    
    return {
        "message": "Handel erfolgreich",
        "artikel": artikel.name,
        "menge": data.menge,
        "preis_pro_einheit": marktpreis.aktueller_preis,
        "gesamtpreis": transaktionsbetrag
    }

@router.get("/markt/kontore")
async def get_all_kontore(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alle KI-Kontore auflisten"""
    
    kontore = db.query(Kontor).all()
    
    kontore_liste = []
    
    for k in kontore:
        province = db.query(Province).get(k.owner_provinz_id)
        
        kontore_liste.append({
            "id": k.id,
            "province_id": k.owner_provinz_id,
            "province_name": province.name if province else "Unbekannt",
            "gehandelte_artikel": json.loads(k.gehandelte_artikel) if k.gehandelte_artikel else [],
            "handels_volumen": k.handels_volumen,
            "ki_strategie": k.ki_strategie,
            "kumulierter_profit": k.kumulierter_profit
        })
    
    return {"kontore": kontore_liste}

@router.post("/province/{province_id}/kontor/erstellen")
async def erstellen_kontor(
    province_id: int,
    data: KontorErstellen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Neues KI-Kontor erstellen"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    # Kontor erstellen
    kontor = Kontor(
        province_id=province_id,
        owner_provinz_id=province_id,
        gehandelte_artikel=json.dumps(data.artikel_ids),
        handels_volumen=data.handels_volumen or 10,
        ki_strategie=data.ki_strategie or "neutral",
        max_lager=json.dumps({aid: 100 for aid in data.artikel_ids})
    )
    
    db.add(kontor)
    db.commit()
    
    return {"message": "Kontor erstellt", "kontor_id": kontor.id}

@router.get("/province/{province_id}/steuern")
async def get_provinz_steuern(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Steuereinnahmen einer Provinz abrufen"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    steuern = calculate_provinz_steuern(province_id)
    
    return {
        "province_id": province_id,
        "steuer_quote": province.steuer_quote or 10,
        "steuern_einnahmen_pro_tick": steuern,
        "wertschöpfung": calculate_wertschöpfung(province_id)
    }

@router.put("/province/{province_id}/steuer_quote")
async def aktualisiere_steuern(
    province_id: int,
    data: SteuerQuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Steuerquote einer Provinz ändern"""
    
    province = db.query(Province).filter_by(id=province_id, owner_id=current_user.id).first()
    
    if not province:
        raise HTTPException(status_code=403, detail={"code": "NOT_OWNER", "message": "Nicht Owner"})
    
    # Steuerquote validieren (0-20%)
    if data.steuer_quote < 0 or data.steuer_quote > 20:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_QUOTE", "message": "Steuerquote muss zwischen 0 und 20% liegen"}
        )
    
    province.steuer_quote = data.steuer_quote
    db.commit()
    
    return {"message": f"Steuerquote auf {data.steuer_quote}% geändert"}
```

---

## ⏱️ Tick-Integration: Wirtschaft pro Tick

### Wirtschafts-Update im Server-Tick

```python
# app/services/tick_manager.py - Erweitert um Wirtschaft

async def execute_tick(self):
    """Einzelnen Tick verarbeiten (erweitert)"""
    
    # ... bestehende Logik ...
    
    # 7. Wirtschaft aktualisieren (Preise, KI-Händler)
    await self.update_wirtschaft()

async def update_wirtschaft(self):
    """Wirtschaft pro Tick aktualisieren"""
    
    # Marktpreise aktualisieren
    update_marktpreise_pro_tick()
    
    # KI-Händler Aktionen ausführen (automatischer Kauf/Verkauf)
    await self.execute_ki_handel()
    
    # Steuereinnahmen berechnen und gutschreiben
    await self.gutschrift_steuern()

async def execute_ki_handel(self):
    """KI-Händler (Kontore) Aktionen ausführen"""
    
    kontore = db.query(Kontor).all()
    
    for kontor in kontore:
        gehandelte_artikel = json.loads(kontor.gehandelte_artikel) if kontor.gehandelte_artikel else []
        
        for artikel_id in gehandelte_artikel:
            marktpreis = db.query(Marktpreis).get(artikel_id)
            
            if not marktpreis:
                continue
            
            # KI-Entscheidung treffen
            ki_entscheidung = ki_handel_logik(kontor, artikel_id, marktpreis.aktueller_preis)
            
            if ki_entscheidung["aktion"] == "kaufen":
                # KI kauft vom Markt (erhöht Nachfrage)
                marktpreis.nachfrage_menge += kontor.handels_volumen
                
                # KI zahlt Preis (MIPS von Owner-Provinz)
                owner_provinz = db.query(Province).get(kontor.owner_provinz_id)
                
                if owner_provinz:
                    lager = db.query(ProvinceStorage).filter_by(province_id=kontor.owner_provinz_id).first()
                    
                    if lager:
                        mips = lager.resources_mips
                        kosten = marktpreis.aktueller_preis * kontor.handels_volumen
                        
                        if mips >= kosten:
                            lager.resources_mips = mips - kosten
                            
                            # Artikel zum Lager hinzufügen
                            res_key = f"resources_artikel_{artikel_id}"
                            aktuelle_menge = getattr(lager, res_key, 0)
                            
                            max_lager_dict = json.loads(kontor.max_lager) if kontor.max_lager else {}
                            max_menge = max_lager_dict.get(str(artikel_id), 100)
                            
                            neue_menge = min(aktuelle_menge + kontor.handels_volumen, max_menge)
                            setattr(lager, res_key, neue_menge)
                            
                            # Profit berechnen (Differenz zum Basispreis)
                            if marktpreis.aktueller_preis < marktpreis.basispreis:
                                kontor.kumulierter_profit += (marktpreis.basispreis - marktpreis.aktueller_preis) * kontor.handels_volumen
            
            elif ki_entscheidung["aktion"] == "verkaufen":
                # KI verkauft auf den Markt (erhöht Angebot)
                marktpreis.angebot_menge += kontor.handels_volumen
                
                # KI erhält Preis (MIPS an Owner-Provinz)
                owner_provinz = db.query(Province).get(kontor.owner_provinz_id)
                
                if owner_provinz:
                    lager = db.query(ProvinceStorage).filter_by(province_id=kontor.owner_provinz_id).first()
                    
                    if lager:
                        res_key = f"resources_artikel_{artikel_id}"
                        aktuelle_menge = getattr(lager, res_key, 0)
                        
                        if aktuelle_menge >= kontor.handels_volumen:
                            setattr(lager, res_key, aktuelle_menge - kontor.handels_volumen)
                            
                            mips = lager.resources_mips
                            erlös = marktpreis.aktueller_preis * kontor.handels_volumen
                            lager.resources_mips = mips + erlös
                            
                            # Profit berechnen
                            if marktpreis.aktueller_preis > marktpreis.basispreis:
                                kontor.kumulierter_profit += (marktpreis.aktueller_preis - marktpreis.basispreis) * kontor.handels_volumen

async def gutschrift_steuern(self):
    """Steuereinnahmen pro Tick gutschreiben"""
    
    provinsen = db.query(Province).all()
    
    for province in provinsen:
        steuern = calculate_provinz_steuern(province.id)
        
        if steuern > 0:
            lager = db.query(ProvinceStorage).filter_by(province_id=province.id).first()
            
            if lager:
                mips = lager.resources_mips
                lager.resources_mips = mips + steuern

# Helper: Preis-Trend ermitteln
def get_preistrend(preis_verlauf_json: str) -> str:
    """Preis-Trend aus Verlauf ermitteln"""
    
    verlauf = json.loads(preis_verlauf_json) if preis_verlauf_json else []
    
    if len(verlauf) < 10:
        return "neutral"
    
    letztes_drittel = verlauf[-3:]
    erstes_drittel = verlauf[:3]
    
    avg_start = sum(erstes_drittel) / len(erstes_drittel)
    avg_ende = sum(letztes_drittel) / len(letztes_drittel)
    
    if avg_ende > avg_start * 1.05:
        return "steigend"
    elif avg_ende < avg_start * 0.95:
        return "fallend"
    else:
        return "neutral"

def calculate_wertschöpfung(province_id: int) -> int:
    """Wertschöpfung einer Provinz berechnen (Summe aller Produktion)"""
    
    gebaeude = db.query(Building).filter_by(province_id=province_id, aktiv=True).all()
    
    wertschöpfung = 0
    
    for gebaeude in gebaeude:
        produktion = gebaeude.typ.produktion  # JSON
        if produktion:
            wertschöpfung += sum(produktion.values())
    
    return wertschöpfung
```

---

## 🖥️ Client-Side Wirtschaft UI (JavaScript)

### Markt Manager

```javascript
// js/game/markt-manager.js

class MarktManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Alle Marktpreise laden
    async loadMarktpreise() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/markt/preise`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderPreise(data.preise, data.inflationsrate);
            }
        } catch (error) {
            console.error('Marktpreise Load Error:', error);
        }
    }

    // Preise im UI rendern (Tabelle mit Trends)
    renderPreise(preise, inflationsrate) {
        const container = document.getElementById('markt-tabelle');
        
        if (!container) return;

        let html = '<h3>📊 Marktpreise</h3>';
        
        // Inflationsrate anzeigen
        const inflColor = parseFloat(inflationsrate) > 0 ? '#ff8c00' : 
                         parseFloat(inflationsrate) < 0 ? '#4caf50' : '#808080';
        
        html += `<p class="inflationsrate" style="color: ${inflColor}">Inflation: ${inflationsrate}</p>`;
        
        html += '<table class="preise-tabelle">';
        html += '<thead><tr><th>Artikel</th><th>Preis</th><th>Angebot</th><th>Nachfrage</th><th>Trend</th></tr></thead>';
        html += '<tbody>';
        
        for (const preis of preise) {
            const trendIcon = preis.preis_trend === 'steigend' ? '📈' : 
                             preis.preis_trend === 'fallend' ? '📉' : '➡️';
            
            const trendColor = preis.preis_trend === 'steigend' ? '#ff8c00' : 
                              preis.preis_trend === 'fallend' ? '#4caf50' : '#808080';
            
            html += `
                <tr>
                    <td>${preis.name}</td>
                    <td>${preis.aktueller_preis} MIPS</td>
                    <td>${preis.anbot_menge}</td>
                    <td>${preis.nachfrage_menge}</td>
                    <td style="color: ${trendColor}">${trendIcon} ${preis.preis_trend}</td>
                </tr>
            `;
        }
        
        html += '</tbody></table>';

        container.innerHTML = html;
    }

    // Einzelnen Artikel-Preis laden
    async loadArtikelPreis(artikelId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/markt/${artikelId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderArtikelDetail(data);
            }
        } catch (error) {
            console.error('Artikel Preis Error:', error);
        }
    }

    renderArtikelDetail(data) {
        const container = document.getElementById('artikel-detail');
        
        if (!container) return;

        let html = `<h4>${data.name}</h4>`;
        
        // Preis-Chart (einfache ASCII-Darstellung)
        if (data.preis_verlauf && data.preis_verlauf.length > 0) {
            html += '<div class="preis-chart">';
            html += '<p>Preis-Verlauf (letzte 100 Ticks):</p>';
            
            const maxPreis = Math.max(...data.preis_verlauf);
            const minPreis = Math.min(...data.preis_verlauf);
            
            for (let i = 0; i < data.preis_verlauf.length; i += 10) {
                const preis = data.preis_verlauf[i];
                const barLength = ((preis - minPreis) / (maxPreis - minPreis)) * 30;
                const bar = '█'.repeat(Math.max(1, Math.floor(barLength)));
                
                html += `<div class="chart-bar"><span>${preis}</span> ${bar}</div>`;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // KI-Kontore auflisten
    async loadKontore() {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/markt/kontore`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderKontore(data.kontore);
            }
        } catch (error) {
            console.error('Kontore Load Error:', error);
        }
    }

    renderKontore(kontore) {
        const container = document.getElementById('kontore-liste');
        
        if (!container) return;

        let html = '<h3>🤖 KI-Kontore</h3>';
        
        if (kontore.length === 0) {
            html += '<p class="no-kontore">Keine KI-Kontore vorhanden.</p>';
        } else {
            html += '<div class="kontore-grid">';
            
            for (const k of kontore) {
                html += `
                    <div class="kontor-card">
                        <h4>${k.province_name}</h4>
                        <p>Strategie: ${k.ki_strategie}</p>
                        <p>Volumen: ${k.handels_volumen} Einheiten/Tick</p>
                        <p>Profit: ${k.kumulierter_profit} MIPS</p>
                    </div>
                `;
            }
            
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // Handel durchführen
    async durchfuehreHandel(vonProvinzId, zielProvinzId, artikelId, menge) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/markt/handeln`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    von_provinz_id: vonProvinzId,
                    ziel_provinz_id: zielProvinzId,
                    artikel_id: artikelId,
                    menge: menge
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Handel erfolgreich: ${data.menge}x ${data.artikel} für ${data.gesamtpreis} MIPS`);
                await this.loadMarktpreise(); // Preise aktualisieren
            } else {
                const error = await response.json();
                this.showNotification(error.detail.message, 'error');
            }
        } catch (error) {
            console.error('Handeln Error:', error);
        }
    }

    // Notification anzeigen
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `markt-notification ${type}`;
        notification.textContent = message;
        
        document.getElementById('notifications').appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Initialisieren
    init() {
        this.loadMarktpreise();
        this.loadKontore();
        
        // Periodisch aktualisieren (alle 60s = pro Tick)
        setInterval(() => {
            this.loadMarktpreise();
            this.loadKontore();
        }, 60000);
    }
}

// Singleton
const markt = new MarktManager();

export default markt;
```

---

## 🧪 Testing Wirtschaftssystem

### Unit Tests

```python
# tests/services/test_wirtschaft_service.py
import pytest

def test_calculate_marktpreis():
    """Testet Preis-Berechnung (Angebot/Nachfrage)"""
    
    from app.models import calculate_marktpreis
    
    # Gleiches Angebot/Nachfrage → Basispreis
    preis = calculate_marktpreis(1, 100, 100)
    
    assert preis == 100  # Annahme: Basispreis = 100
    
    # Hohe Nachfrage, niedriges Angebot → Preis steigt
    preis_hoch = calculate_marktpreis(1, 10, 200)
    
    assert preis_hoch > 100
    
    # Hohes Angebot, niedrige Nachfrage → Preis fällt
    preis_niedrig = calculate_marktpreis(1, 200, 10)
    
    assert preis_niedrig < 100

def test_ki_handel_logik_aggressiv():
    """Testet KI-Handelslogik (aggressiv)"""
    
    from app.models import ki_handel_logik, Kontor, Marktpreis
    
    kontor = mocker.Mock(ki_strategie="aggressiv", handels_volumen=10)
    marktpreis = mocker.Mock(basispreis=100, aktueller_preis=80)
    
    entscheidung = ki_handel_logik(kontor, 1, marktpreis.aktueller_preis)
    
    assert entscheidung["aktion"] == "kaufen"  # Unter Basispreis → kaufen

def test_ki_handel_logik_neutral():
    """Testet KI-Handelslogik (neutral)"""
    
    from app.models import ki_handel_logik, Kontor, Marktpreis
    
    kontor = mocker.Mock(ki_strategie="neutral", handels_volumen=10)
    marktpreis = mocker.Mock(angebot_menge=200, nachfrage_menge=50)
    
    entscheidung = ki_handel_logik(kontor, 1, 100)
    
    assert entscheidung["aktion"] == "kaufen"  # Überangebot → KI kauft

def test_calculate_inflation_rate():
    """Testet Inflationsraten-Berechnung"""
    
    from app.models import calculate_inflation_rate
    
    # Mock Marktpreise mit steigenden Preisen
    pass  # Integrationstest erforderlich

def test_calculate_provinz_steuern():
    """Testet Steuer-Berechnung"""
    
    from app.models import calculate_provinz_steuern
    
    # Mock Provinz mit Wertschöpfung
    pass  # Integrationstest erforderlich

def test_get_preistrend():
    """Testet Preis-Trend-Ermittlung"""
    
    from app.models import get_preistrend
    
    # Steigender Trend
    verlauf_steigend = json.dumps([100, 105, 110, 115, 120])
    assert get_preistrend(verlauf_steigend) == "steigend"
    
    # Fallender Trend
    verlauf_fallend = json.dumps([120, 115, 110, 105, 100])
    assert get_preistrend(verlauf_fallend) == "fallend"
    
    # Neutraler Trend
    verlauf_neutral = json.dumps([100, 100, 100, 100, 100])
    assert get_preistrend(verlauf_neutral) == "neutral"
```

---

## 🎯 Best Practices

1. **Angebot/Nachfrage-Prinzip** - Preise dynamisch anpassen
2. **KI-Händler als Stabilisator** - Kontore gleichen Extreme aus
3. **Preis-Grenzen setzen** - Nicht zu extrem (max 20x Basispreis)
4. **Inflation tracken** - Gesamte Preisentwicklung im Auge behalten
5. **Steuer-System flexibel** - Spieler können Quote 0-20% wählen

---

**Wirtschaftssystem ermöglicht dynamische Preise mit KI-Händlern, Inflation und Steuer-System!**
