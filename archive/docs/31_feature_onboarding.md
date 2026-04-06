# Feature: Onboarding & Startsequenz

## Ziel
Neue Spieler sollen nicht in einem leeren UI landen, sondern automatisch ihre erste Provinz zugewiesen bekommen und durch ein Mini-Tutorial geführt werden.

## 1. Automatische Startprovinz-Suche
Sobald ein Spieler sich das erste Mal einloggt (oder "Spiel starten" klickt):
- Backend-Logic `assign_start_province(player_id)`:
  1. Suche in `world_map_cells` nach einer Zelle mit einem Terrain, das `startgebiet == True` hat (z.B. Grasland, Wald).
  2. Zelle muss `owner_id IS NULL` sein.
  3. Zelle sollte (optional) einen Mindestabstand zu bereits aktiven Spielern haben (um sofortige Spawn-Kills zu vermeiden).
  4. Setze `owner_id = player_id`.
  5. Initialisiere das Lager der Provinz mit Startressourcen (500 Nahrung, 500 Wasser, 200 Holz, 100 Stein).
  6. Platziere automatisch ein Basis-Gebäude (z.B. "Zeltlager" oder "Hauptquartier") auf Grid (15,15).

## 2. Frontend: Onboarding-UI
- Wenn `player.provinzen.length == 0`: Zeige Welcome-Screen "Willkommen in der Verbrannten Zone".
- Button: "Welt betreten". Ruft `POST /player/{id}/spawn` auf.
- Nach Spawn: Redirect auf die Provinz-Ansicht.
- **Tutorial-Overlay:** Ein kleines Modal unten rechts führt durch die ersten Klicks:
  1. "Das ist deine erste Provinz. Baue eine Wasserstelle." (Highlight auf Karte)
  2. "Gut! Jetzt öffne das Lager, um deine Bestände zu prüfen."
  (Tutorial-Fortschritt in DB `users.tutorial_step` speichern).

## 3. Schutz vor Abuse
- Spieler dürfen nur genau EINE Startprovinz generieren.
- Wenn die Startprovinz revoltiert oder erobert wird -> Account gilt als "zerstört" -> Option "Neu anfangen" (Reset Account & Spawn neu).
