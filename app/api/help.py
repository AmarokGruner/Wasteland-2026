from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import get_db, BuildingType, Resource, TerrainType
from typing import List, Dict

router = APIRouter(prefix="/help", tags=["help"])

@router.get("/faq")
def get_faq():
    """Returns the player FAQ"""
    return [
        {
            "question": "Was sind Arbeitspunkte (AP)?",
            "answer": "Arbeitspunkte (AP) werden jede Stunde (Tick) generiert und für Aktionen wie Bauen, Upgraden oder Spezialaktionen (Jagen/Sammeln) benötigt. Die maximale Kapazität und Generierungsrate hängen von deinem Straßennetz und der Bevölkerung ab."
        },
        {
            "question": "Wie funktioniert die Rundenmechanik?",
            "answer": "Das Spiel läuft in Ticks (stündlich) und Runden (täglich/24 Ticks). In jedem Tick werden Ressourcen produziert, Steuern erhoben und AP generiert. Ein 'Spulvorgang' berechnet 24 Stunden im Voraus."
        },
        {
            "question": "Was ist der Unterschied zwischen Land- und Stadtfeldern?",
            "answer": "Deine Provinz ist in ein 15x15 Grid unterteilt. Nur auf freigeschalteten Stadtfeldern (grau markiert) können Stadtgebäude errichtet werden. Landfelder dienen der Rohstoffgewinnung oder bleiben Natur."
        },
        {
            "question": "Wie erweitere ich meine Stadt?",
            "answer": "Über das Admin-Grid-System kannst du deine Stadt in 8 Stufen ausbauen. Jede Stufe schaltet neue Felder im 15x15 Grid frei, erfordert aber bestimmte Voraussetzungen wie Gebäude-Upgrades oder Ressourcen."
        },
        {
            "question": "Wie funktioniert das 4-Konten-System?",
            "answer": "Deine Finanzen sind getrennt in: Provinzkonto (Infrastruktur), Volk konto (Steuern der Bürger), Handelskonto (Markterlöse) und Staatskonto (Zentrales Konto des Spielers). Du kannst Gelder zwischen diesen Konten transferieren."
        },
        {
            "question": "Was beeinflusst die Moral meiner Bevölkerung?",
            "answer": "Steuersätze, Nahrungsversorgung (Marktstände), die Gesundheit (PKV-System) und spezielle Ereignisse beeinflussen die Moral. Eine hohe Moral steigert die Produktivität."
        },
        {
            "question": "Was bringt mir das Straßennetz?",
            "answer": "Ein gut ausgebautes Straßennetz verbindet deine Gebäude mit dem Zentrum. Gebäude ohne Straßenanbindung produzieren weniger oder gar nicht. Zudem erhöht das Straßennetz deine maximalen Arbeitspunkte."
        },
        {
            "question": "Was ist das Bunker-System?",
            "answer": "Jeder Spieler startet in einer Bunker-Provinz. Der Bunker bietet Schutz bei Angriffen und dient als erste Basis für Ressourcen."
        }
    ]

@router.get("/buildings")
def get_buildings_info(db: Session = Depends(get_db)):
    """Returns info about all building types"""
    buildings = db.query(BuildingType).filter(BuildingType.baubar == 1).all()
    result = []
    for b in buildings:
        import json
        result.append({
            "id": b.id,
            "name": b.name,
            "kategorie": b.kategorie,
            "bautyp": b.bautyp,
            "baukosten_mips": b.baukosten_mips,
            "beschreibung": b.spezial_eigenschaften, # Often stored here
            "produktion": json.loads(b.produktion) if b.produktion else [],
            "verbrauch": json.loads(b.rohstoffverbrauch) if b.rohstoffverbrauch else [],
            "arbeiter": b.arbeiter,
            "wohnraum": b.wohnraum
        })
    return result

@router.get("/resources")
def get_resources_info(db: Session = Depends(get_db)):
    """Returns info about all resources"""
    resources = db.query(Resource).all()
    return [{"id": r.id, "name": r.name, "typ": r.typ, "wert": r.wert} for r in resources]

@router.get("/terrains")
def get_terrains_info(db: Session = Depends(get_db)):
    """Returns info about terrain types"""
    terrains = db.query(TerrainType).all()
    return [{
        "name": t.name,
        "beschreibung": t.beschreibung,
        "holz_yield": t.holz_yield,
        "stein_yield": t.stein_yield,
        "eisen_yield": t.eisen_yield,
        "mips_kosten": t.mips_kosten
    } for t in terrains]
