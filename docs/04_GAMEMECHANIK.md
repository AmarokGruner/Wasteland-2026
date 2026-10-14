# Spielmechaniken

**Wasteland Game Mechanics | Version 1.6**

---

## 🎮 Kernmechaniken

Das Spiel basiert auf folgenden Hauptmechaniken:

1. **Gebäudebau** - 209 verschiedene Gebäude
2. **Ressourcen-Management** - 153 Ressourcen-Arten
3. **Terrains & Weltkarte** - 42 Landschaftstypen, 50x50 Karte
4. **Militär & Kampf** - 63 Einheitentypen
5. **Handel & Wirtschaft** - Marktplätze, Kontore, Spieler-Handel
6. **Regierung & Kultur** - 7 Staatsformen mit Boni
7. **Siedler & Kolonisierung** - Neue Provinzen gründen
8. **Server-Tick** - Automatische Rundenmechanik

---

## 🏗️ 1. Gebäudebau-System

### Grundprinzip
- Gebäude können NUR an Straßen angebaut werden
- Jedes Gebäude hat ein **Tech-Level** (Voraussetzung)
- Bau kostet **MIPS** + **Rohstoffe**
- Gebäude bieten: Wohnraum, Lagerraum, Produktion

### Gebäude-Kategorien

| Kategorie | Beispiele | Funktion |
|-----------|-----------|----------|
| **Start** | Bunker | Start-Gebäude, einmalig |
| **Farm** | Kartoffelfarm, Getreidefarm | Nahrung produzieren |
| **Industrie** | Weberei, Sägewerk | Rohstoffe verarbeiten |
| **Bildung** | Universität, Schule | Tech-Fortschritt |
| **Militär** | Kaserne, Fort | Einheiten ausbilden |
| **Spezial** | Flughafen, Leuchtturm | Spezielle Boni |

### Gebäude-Typen (bautyp)
- **Land:** Auf freiem Feld baubar (Farmen, Gruben)
- **Stadt:** In Städten baubar (Fabriken, Verwaltung)
- **Stadtausbau:** Erweiterung bestehender Städte
- **Weg/Wegkreuzung:** Straßennetz

### Ausbaubarkeit
- Manche Gebäude sind **ausbaubar** (bis zu 10 Stufen)
- Jede Stufe erhöht Produktion/effektivität
- Ausbau kostet MIPS + Rohstoffe

### Einmalige Gebäude (unique)
- Pro Provinz nur **einmal** baubar
- Beispiele: Bunker, Universität, Flughafen

---

## 📦 2. Ressourcen-Management

### Ressourcen-Typen

| Typ | Beispiele | Verwendung |
|-----|-----------|------------|
| **Nahrung** | Kartoffeln, Reis, Mais | Bevölkerung ernähren |
| **Getränk** | Wasser, Tee, Alkohol | Moral, Gesundheit |
| **Baurohstoff** | Stein, Holz, Aluminium | Gebäudebau |
| **Luxusgut** | Stoffe, Möbel, Schmuck | Handel, Kultur |

### Produktion
- Gebäude produzieren Ressourcen pro **24 Stunden Intervall** (in Echtzeit ablaufend)
- **Terrain-Effektivität** beeinflusst Produktion (50-100%)
- Beispiel: Kartoffelfarm auf Grasland = 100%, auf Ödland = 25%
- **Echtzeit-Spiel:** Jede Minute Echtzeit = +1 Minute Spul-Guthaben (Spielzeit)
- Nach 24 Stunden Echtzeit = 24 Stunden Spielzeit verfügbar (1 Tick)

### Lagerung
- Jedes Gebäude bietet **Lagerraum** (z.B. Bunker: 20.000)
- Lagerkapazität begrenzt produzierbare Menge
- Überproduktion geht verloren

### Handel
- **Marktplatz** gibt Marktpunkte (1 Punkt = 1 Verkauf)
- Spieler können untereinander handeln
- **Kontore** ermöglichen automatischen Handel

---

## 🗺️ 3. Terrains & Weltkarte

### Weltkarte
- **50x50 Felder** = 2.500 Zellen
- Jede Zelle hat einen **Terrain-Typ**
- Provinzen beanspruchen mehrere Felder

### Terrain-Typen (42)
| Kategorie | Beispiele |
|-----------|-----------|
| **Land** | Grasland, Steppe, Savanne |
| **Gebirge** | Felsgebirge, Grüngebirge |
| **Wüste** | Sanddünen, Wüste |
| **Wald** | Wald, Regenwald, Dschungel |
| **Sumpf** | Sumpfland, Tropensumpf |

### Terrain-Effektivität
- Gebäude haben **Terrain-Boni** (50%, 75%, 100%)
- Beispiel: Getreidefarm auf Grasland = 100% Produktion
- Auf Ödland oft nur 25%

### Vorkommen (Bodenschätze)
- **24 verschiedene Vorkommen**
- Suche kostet MIPS (Suchkosten)
- Findwahrscheinlichkeit hängt vom Terrain ab
- Beispiel: Kalkstein auf Felsgebirge = 90%

---

## ⚔️ 4. Militär & Kampf

### Einheiten (63 Typen)
| Einheit | Stärke | Spezialität |
|---------|--------|-------------|
| **Rekrut** | Niedrig | Basis-Infanterie |
| **Bogenschütze** | Mittel | Fernkampf |
| **Schwertkämpfer** | Hoch | Nahkampf |
| **Beritten** | Variabel | Schnelle Bewegung |

### Kampfsystem
- **Auslöser:** Armee betritt feindliche Provinz
- **Berechnung:** Stärke vs. Panzerung (Nah/Fern)
- **Verlierer:** Verliert Einheiten, Provinz wechselt Besitzer

### Gebäude für Militär
- **Kaserne:** Rekruten ausbilden
- **Ausbildungscamp:** 2 Rekruten/24h pro Gebäude
- **Fort/Festung:** Verteidigungsbonus

---

## 💰 5. Handel & Wirtschaft

### Währung: MIPS
- Hauptwährung des Spiels
- Verdient durch: Produktion, Handel, Steuern
- Ausgaben für: Gebäudebau, Suche, Militär

### Marktplatz
- Gibt **Marktpunkte** (z.B. 25 Punkte)
- Pro Punkt: 1 Gut an Bevölkerung verkaufen
- Markt kauft Güter zu festem Preis

### Kontore
- Automatische Handelsposten
- Verbinden Provinzen mit Routen
- Generieren kontinuierlich MIPS

### Spieler-Handel
- Direkter Handel zwischen Provinzen
- Verhandelte Preise möglich
- Transportkosten je nach Distanz

---

## 🏛️ 6. Regierung & Kultur

### Regierungsformen (7)
| Form | Bonus | Beschreibung |
|------|-------|--------------|
| **Demokratie** | +Kulturpunkte | Freiheitsbonus |
| **Diktatur** | +Militär | Schnelle Entscheidungen |
| **Theokratie** | +Bildung | Religiöser Einfluss |
| ... | ... | ... |

### Kulturpunkte
- **1 Punkt** pro Provinz-Größe (size_level)
- Zusätzliche Punkte durch Gebäude (Glockenturm, etc.)
- Benötigt für: Regierungsform wechseln, Tech-Fortschritt

### Bildung
- **Universität:** +15 Techproduktion pro Tick
- **Schule:** Grundlegende Bildung
- Tech-Level bestimmt: Welche Gebäude baubar sind

---

## 👥 7. Siedler & Kolonisierung

### Siedler (Einheit ID 21)
- **Zivilist**, Geschwindigkeit: 1.0
- Bewegung: zu Fuß (Boden)
- Alter: 4-5 Jahre (20-25 Jahre alt)

### Provinz gründen
1. **Leeres Feld** auf Weltkarte finden
2. **Siedler** dorthin bewegen
3. **Bunker** als Start-Gebäude errichten
4. **Siedlung** wird zur neuen Provinz

### Provinz-Größen (size_level 0-8)
| Level | Name | Beschreibung |
|-------|------|--------------|
| 0 | Siedlung | Start-Zustand |
| 1 | Dorf | Kleine Gemeinschaft |
| 2-3 | Ort/Kleinstadt | Wachsende Siedlung |
| 4-5 | Stadt/Großstadt | Mittelgroß |
| 6-8 | Metropole | Große Stadt |

---

## ⏱️ 8. Server-Tick (Echtzeit-Spiel mit Spul-Mechanik)

### WICHTIG: 24 Stunden Echtzeit = 24 Stunden Spielzeit

**Das Spiel läuft in ECHTZEIT ab!** Jede Minute, die in der realen Welt vergeht, erhöht das Spul-Guthaben um eine Minute.

### Tick-Intervall
- **Server tickt alle 60 Sekunden** (Echtzeit-Intervall)
- **Jeder Tick repräsentiert 24 Stunden Spielzeit** (in Echtzeit ablaufend)
- Nach 24 Stunden Echtzeit = 1 Tick (24h Spielzeit) verfügbar
- Maximal **240 Stunden** (10 Tage) Spul-Guthaben speicherbar

### Was passiert pro Tick?
- Ressourcen-Produktion (24h Intervall, in Echtzeit)
- Nahrungsaufnahme der Bevölkerung
- Bevölkerungswachstum (pro 24h)
- Gebäude-Wartung (10% MIPS pro Woche)

### Spul-Mechanik
- Spieler können Zeit vorspulen (bis zu 240 Stunden / 10 Tage)
- Spul-Guthaben wächst mit Echtzeit (+1h pro Stunde)
- Gebäude sind SOFORT da, wenn errichtet (kein Bau-Fortschritt!)

### Gamelog
- Alle Ereignisse werden protokolliert:
  - Gebäude gebaut/abgerissen (sofort verfügbar)
  - Kämpfe gewonnen/verloren
  - Handel abgeschlossen
  - Naturereignisse (Dürre, Flut)

### Cleanup-Routinen
- Alte Logs werden archiviert
- Inaktive Provinzen können gelöscht werden
- Datenbank-Optimierung

---

## 🎯 Fortschritt & Ziele

### Tech-Level System
- Beginnt bei 0 (Bunker)
- Steigt durch: Bildung, Forschung, Kultur
- Bestimmt: Welche Gebäude baubar sind

### Provinz-Entwicklung
```
Siedlung → Dorf → Ort → Kleinstadt → Stadt → Großstadt → Metropole
```

### Wirtschaftlicher Kreislauf
```
Rohstoffe → Gebäude → Produktion → MIPS → Handel → Mehr MIPS
```

---

## 📊 Zahlen & Fakten

| Kategorie | Anzahl |
|-----------|--------|
| Gebäude-Typen | 209 |
| Ressourcen-Arten | 153 |
| Terrain-Typen | 42 |
| Einheiten-Typen | 63 |
| Tierarten | 8 |
| Vorkommen-Arten | 24 |
| Regierungsformen | 7 |
| Weltkarte-Felder | 2.500 (50x50) |

---

**Letzte Aktualisierung:** 2026-10-14  
**Quellen:** FAQ, seed_gebaeude.py, seed_ressourcen.py
