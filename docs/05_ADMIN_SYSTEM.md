# Admin-System

**Wasteland Administration | Version 1.6**

---

## 👨‍💼 Admin-Übersicht

Das Admin-System ermöglicht Server-Administratoren, das Spiel zu verwalten, Spieler zu kontrollieren und Spielelemente anzupassen.

### Admin-Zugang
- **URL:** `https://your-domain.com/admin`
- **Berechtigung:** Admin-Rolle im Benutzerkonto
- **Authentifizierung:** JWT Token erforderlich

---

## 🔧 Admin-Funktionen

### 1. Dashboard
| Funktion | Beschreibung |
|----------|--------------|
| **Übersicht** | Alle Spieler, Provinzen, Aktivitäten |
| **Statistiken** | Server-Last, Datenbank-Größe, Logs |
| **Schnellaktionen** | Broadcast, Backup, Cleanup |

### 2. Benutzer-Verwaltung
| Aktion | Endpunkt | Beschreibung |
|--------|----------|--------------|
| Liste | `GET /admin/users` | Alle Benutzer anzeigen |
| Erstellen | `POST /admin/users` | Neuen Admin erstellen |
| Bearbeiten | `PUT /admin/users/{id}` | Rolle/Status ändern |
| Löschen | `DELETE /admin/users/{id}` | Benutzer entfernen |

**Benutzer-Rollen:**
- `player` - Normaler Spieler
- `moderator` - Mit Admin-Rechten (eingeschränkt)
- `admin` - Vollzugriff

### 3. Provinz-Verwaltung
| Aktion | Endpunkt | Beschreibung |
|--------|----------|--------------|
| Liste | `GET /admin/provinzen` | Alle Provinzen |
| Details | `GET /admin/provinzen/{id}` | Provinz-Details |
| Bearbeiten | `PUT /admin/provinzen/{id}` | Name/Besitzer ändern |
| Löschen | `DELETE /admin/provinzen/{id}` | Provinz entfernen |

### 4. Gebäude-Verwaltung
| Aktion | Endpunkt | Beschreibung |
|--------|----------|--------------|
| Liste | `GET /admin/gebaeude_typen` | Alle 209 Gebäude-Typen |
| Erstellen | `POST /admin/gebaeude_typen` | Neuen Typ hinzufügen |
| Bearbeiten | `PUT /admin/gebaeude_typen/{id}` | Eigenschaften ändern |
| Löschen | `DELETE /admin/gebaeude_typen/{id}` | Typ entfernen (Vorsicht!) |

### 5. Ressourcen-Verwaltung
| Aktion | Endpunkt | Beschreibung |
|--------|----------|--------------|
| Liste | `GET /admin/ressourcen` | Alle 153 Ressourcen |
| Erstellen | `POST /admin/ressourcen` | Neue Ressource |
| Bearbeiten | `PUT /admin/ressourcen/{id}` | Wert/Typ ändern |

### 6. Weltkarte-Editor
| Funktion | Beschreibung |
|----------|--------------|
| **Visueller Editor** | Terrain ändern, Vorkommen setzen |
| **Provinzen verwalten** | Grenzen ziehen, Felder zuweisen |
| **Gebäude platzieren** | Vorgegebene Gebäude setzen |

### 7. Spiel-Logbuch (Gamelog)
| Funktion | Beschreibung |
|----------|--------------|
| **Alle Events** | Gebäude, Kämpfe, Handel, Naturereignisse |
| **Filtern** | Nach Datum, Typ, Provinz filtern |
| **Exportieren** | Logs als JSON/CSV exportieren |

### 8. Broadcast-Nachrichten
| Funktion | Beschreibung |
|----------|--------------|
| **Alle Spieler** | Systemweite Nachricht senden |
| **Bestimmte Provinz** | Nachricht an eine Provinz |
| **Scheduled** | Nachrichten zeitgesteuert senden |

---

## 🏗️ Admin-Oberfläche (admin.html)

### Struktur
Die Admin-Oberfläche ist in **Tabs** unterteilt:

1. **Dashboard** - Übersicht und Statistiken
2. **Benutzer** - CRUD für Benutzerkonten
3. **Provinzen** - Provinz-Verwaltung
4. **Gebäude** - Gebäude-Typen verwalten
5. **Ressourcen** - Ressourcen-Verwaltung
6. **Weltkarte** - Visueller Editor
7. **Gamelog** - Spielereignisse
8. **Broadcast** - Nachrichten senden

### Navigation
- **Sidebar** links mit allen Sektionen
- **Hauptbereich** zeigt aktuelle Sektion
- **Suchfunktion** für schnelle Suche

---

## 🔐 Sicherheitsrichtlinien

### Admin-Berechtigungen
```python
# Beispiel: Gebäude erstellen
@router.post("/admin/gebaeude_typen")
async def create_building(
    building_data: BuildingCreate,
    current_user: User = Depends(get_current_admin)  # Nur Admins!
):
    ...
```

### Wichtige Regeln
1. **Nur Admins** können Gebäude/Ressourcen löschen
2. **Moderatoren** dürfen nur lesen und bearbeiten (kein Löschen)
3. **Alle Änderungen** werden im Admin-Logbuch protokolliert
4. **Kritische Aktionen** (Benutzer löschen) erfordern Bestätigung

### Admin-Logbuch
Jede Admin-Aktion wird gespeichert:
```json
{
  "timestamp": "2026-10-14T10:30:00",
  "admin_id": 1,
  "action": "building_created",
  "target_id": 210,
  "details": {"name": "NeuesGebäude"}
}
```

---

## 🛠️ Wartungsfunktionen

### Datenbank-Backup
```bash
# Manuelles Backup
cp verbrannte_zone.db verbrannte_zone.db.backup.$(date +%Y%m%d)

# Über Admin-UI
POST /admin/backup
```

### Cleanup-Routinen
| Funktion | Beschreibung | Intervall |
|----------|--------------|-----------|
| **Log-Archivierung** | Alte Logs komprimieren | Täglich |
| **Inaktive Provinzen** | Löschen nach 30 Tagen Inaktivität | Wöchentlich |
| **Datenbank-Optimierung** | VACUUM, Index-Reparatur | Monatlich |

### Server-Status
| Check | Beschreibung |
|-------|--------------|
| **Health** | API verfügbar? |
| **Database** | Verbindung OK? Größe? |
| **Memory** | RAM-Nutzung |
| **Uptime** | Server-Laufzeit |

---

## 📊 Admin-Statistiken

### Wichtige Metriken
| Metric | Beschreibung |
|--------|--------------|
| **Aktive Spieler** | Online in letzter Stunde |
| **Provinzen gesamt** | Alle erstellten Provinzen |
| **Gebäude gesamt** | Alle gebauten Gebäude |
| **MIPS im Umlauf** | Gesamte Währungsmenge |
| **Durchschnittliche Spielzeit** | Minuten pro Session |

---

## 🔧 Troubleshooting

### Häufige Probleme
1. **Admin kann nicht einloggen**
   - Prüfe: Benutzerrolle in Datenbank
   - Lösung: `UPDATE users SET role='admin' WHERE username='...'`

2. **Gebäude werden nicht angezeigt**
   - Prüfe: seed_gebaeude.py läuft?
   - Lösung: `python seeds/seed_main.py`

3. **Weltkarte zeigt falsche Terrains**
   - Prüfe: world_map_cells Tabelle
   - Lösung: Admin-Editor öffnen, Terrain neu setzen

---

**Letzte Aktualisierung:** 2026-10-14  
**Admin-Dokumentation:** `admin.html` + API Endpunkte
