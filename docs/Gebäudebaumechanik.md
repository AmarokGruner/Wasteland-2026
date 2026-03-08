Verstanden! Lass uns die Spielmechanik für den Ausbau von Gebäuden mit Python, FastAPI und SQLite umsetzen. Hier ist eine vollständige Anleitung:

1. **Backend Setup**
2. **Datenbankmodell**
3. **API-Endpunkt**
4. **Frontend (HTML/JavaScript)**

### 1. Backend Setup

Erstelle eine neue Python-Datei, z.B. `main.py`, und füge den folgenden Code ein:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Datenbankverbindung herstellen oder erstellen
conn = sqlite3.connect('buildings.db')
cursor = conn.cursor()

# Tabelle für Gebäude erstellen, falls sie noch nicht existiert
cursor.execute('''
CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    upgradable BOOLEAN DEFAULT TRUE
)
''')
conn.commit()

class Building(BaseModel):
    id: int
    name: str
    level: int
    upgradable: bool

# Funktion zum Ausbauen eines Gebäudes
def upgrade_building(building_id: int):
    cursor.execute('SELECT * FROM buildings WHERE id = ?', (building_id,))
    building = cursor.fetchone()
    
    if not building:
        raise HTTPException(status_code=404, detail="Gebäude nicht gefunden")
    
    if not building[3]:
        raise HTTPException(status_code=400, detail="Gebäude kann nicht weiter ausgebaut werden")
    
    new_level = building[2] + 1
    cursor.execute('UPDATE buildings SET level = ?, upgradable = ? WHERE id = ?', (new_level, False, building_id))
    conn.commit()

# API-Endpunkt zum Ausbauen eines Gebäudes
@app.post("/buildings/{building_id}/upgrade")
def upgrade(building_id: int):
    try:
        upgrade_building(building_id)
        return {"message": "Gebäude erfolgreich ausgebaut"}
    except HTTPException as e:
        raise e

# API-Endpunkt zum Abrufen aller Gebäude
@app.get("/buildings/")
def get_buildings():
    cursor.execute('SELECT * FROM buildings')
    buildings = cursor.fetchall()
    return [Building(id=building[0], name=building[1], level=building[2], upgradable=building[3]) for building in buildings]

# Server starten
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```


### 2. Datenbankmodell

Die Tabelle `buildings` enthält die folgenden Spalten:
- `id`: Die eindeutige ID des Gebäudes
- `name`: Der Name des Gebäudes
- `level`: Die aktuelle Stufe des Gebäudes (Standardwert ist 1)
- `upgradable`: Ein boolescher Wert, der angibt, ob das Gebäude weiter ausgebaut werden kann (Standardwert ist `TRUE`)

### 3. API-Endpunkt

Es gibt zwei Hauptendpunkte:
- `/buildings/{building_id}/upgrade`: Dieser Endpunkt wird aufgerufen, um ein Gebäude zu einem bestimmten Index auszubauen.
- `/buildings/`: Dieser Endpunkt gibt eine Liste aller Gebäude zurück.

### 4. Frontend (HTML/JavaScript)

Erstelle eine HTML-Datei, z.B. `index.html`, und füge den folgenden Code hinzu:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Building Upgrades</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
</head>
<body>
    <h1>Gebäude Ausbau</h1>
    <div id="buildings-list"></div>

    <script>
        $(document).ready(function() {
            // Gebäudedaten abrufen
            $.get("/buildings/", function(data) {
                var buildingsList = $("#buildings-list");
                data.forEach(function(building) {
                    var buildingDiv = $("<div></div>").addClass("building");
                    buildingDiv.append("<h2>" + building.name + "</h2>");
                    buildingDiv.append("<p>Stufe: " + building.level + "</p>");
                    if (building.upgradable) {
                        var upgradeButton = $("<button></button>").text("Ausbauen").click(function() {
                            $.post("/buildings/" + building.id + "/upgrade", function(response) {
                                alert(response.message);
                                location.reload();
                            });
                        });
                        buildingDiv.append(upgradeButton);
                    } else {
                        buildingDiv.append("<p>Gebäude ist nicht mehr ausbaubar</p>");
                    }
                    buildingsList.append(buildingDiv);
                });
            });
        });
    </script>
</body>
</html>
```


### Anleitung

1. **Backend starten**: Führe den Backend-Code in IntelliJ IDEA aus, um den Server zu starten.
2. **Frontend öffnen**: Öffne die `index.html` Datei in einem Webbrowser, um das Frontend zu sehen.
3. **Gebäude ausbauen**: Klicke auf den "Ausbauen"-Button neben den Gebäuden, um sie zu upgraden.

### Erklärung

- **Backend**:
    - Der Server bietet Endpunkte zur Abruf und Aktualisierung von Gebäude-Daten.
    - Die Datenbankfeld `ausbaubar` bestimmt, ob ein Gebäude weiter ausgebaut werden kann.

- **Frontend**:
    - Die Seite listet alle Gebäude auf und zeigt ihre aktuellen Stufen an.
    - Wenn ein Gebäude noch ausbaubar ist, wird ein "Ausbauen"-Button angezeigt.
    - Durch Klicken auf den Button wird der Ausbau des Gebäudes über einen POST-Request an den Server durchgeführt.

Diese Spielmechanik bietet eine einfache Möglichkeit, Gebäude in einer Anwendung zu upgraden und ermöglicht es Benutzern, ihre Gebäude progressiv zu verbessern.