# Abgleich Original-Spiel vs. Lokale Datenbank - Abschluss

**Datum:** 2026-10-13  
**Quelle:** https://v3.verbranntezone.ch/

## Zusammenfassung

| Kategorie | Original | Lokal DB | Geändert |
|---|---|---|---|
| Gebäude | 208 | 209 | **+6 neu** |
| Ressourcen | 143 | 153 | **+1 neu** |
| Vorkommen | 7 | 24 | OK |
| Terrains | ~42 | 42 | Unverändert |
| Einheiten | ~61 | 63 | OK |
| Lebewesen | ~8 | 8 | OK |
| Artikel | 15 | 15 | OK |

## Neue Gebäude (6)

| ID | Name | Kategorie | Tech-Level | Baukosten | Besonderheiten |
|----|------|-----------|------------|-----------|----------------|
| 21 | Baumwollplantage | Farm | 1100 | 56.000 MIPS | - |
| 41 | Weberei | Industrie | 1000 | 20.000 MIPS | Ausbaubar |
| 56 | Salpetermine | Grube | 1000 | 120.000 MIPS | - |
| 141 | Universität | Bildung | 1000 | 45.000 MIPS | Einmalig/pro Provinz, Ausbaubar |
| 154 | Entsalzungsanlage | Küste | 980 | 20.000 MIPS | Nur an Küste |
| 347 | Flughafen | Speziell | 1000 | 100.000 MIPS | Einmalig/pro Provinz, Lagerraum 10.000 |

## Neue Ressource (1)

| ID | Name | Typ | Wert |
|----|------|-----|------|
| 91 | Aluminium | Baurohstoff | 1200 |

## Geprüfte Kategorien ohne Neuerungen

### Einheiten (63)
- Keine neuen Einheiten im Original gefunden
- DB enthält 63 Einheitentypen (ID 1-1298, mit Kombinationen)

### Lebewesen (8)
- Keine neuen Lebewesen im Original gefunden
- DB enthält 8 Tierarten:
  - ID 1: Rote Scorpione
  - ID 2: Bukhts
  - ID 3: Pferd
  - ID 4: Huhn
  - ID 5: Schaf
  - ID 6: Ödlandwolf
  - ID 7: Riesenechse
  - ID 8: Käferkolonie

## Durchgeführte Aktualisierungen

1. ✅ **6 neue Gebäude** in `gebaeude_typen` eingefügt
2. ✅ **1 neue Ressource** (Aluminium) in `ressourcen` eingefügt
3. ✅ **Vorkommen ID 13** (Kalkstein) war bereits aktuell

## Aktuelle Datenbank-Stände

- **Gebäude:** 209 Typen
- **Ressourcen:** 153 Arten
- **Vorkommen:** 24 Typen
- **Terrains:** 42 Typen
- **Einheiten:** 63 Typen
- **Lebewesen:** 8 Arten
- **Artikel:** 15 Typen

## Empfohlene nächste Schritte

- [ ] Webcrawler für Terrains, Einheiten, Lebewesen ausführen (falls gewünscht)
- [ ] Gebäude-Bilder für neue Gebäude herunterladen
- [ ] Rohstoff-Produktionen für Aluminium definieren
- [ ] Spiel neu starten um Änderungen zu testen

## Gespeicherte Dateien

- `/home/fabian/Wasteland/GEBAEUDE_ABGLEICH_2026-10-13.md` - Detaillierter Gebäudebericht
- `/home/fabian/Wasteland/ABGLEICH_ABSCHLIESSEND_2026-10-13.md` - Dieser Abschlussbericht
- `/home/fabian/Wasteland/webcrawler/cache/gebaeude_list_live.html` - Live-Gebäude-Liste
- `/tmp/neue_gebaeude_detailliert.json` - Alle Gebäude-Details
- `/tmp/neue_ressource_91.json` - Aluminium-Details
