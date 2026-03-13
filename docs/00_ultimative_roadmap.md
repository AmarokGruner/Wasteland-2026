# Ultimative Implementierungs-Roadmap (39 Prompts)

Diese Roadmap enthält alle generierten Prompts (01-28), die geplanten Prompts (29-36) sowie die drei speziellen Mechanik-Dokumente (`Gebaudebaumechanik.md`, `Rundenmechanik.md`, `gebaeude_admin_grid.md`).

## Werkzeug-Einsatzstrategie

*   **AG-Flash** (Antigravity Gemini 3 Flash): Für kurze Skripte, CRUD-Operationen, isolierte DB-Anpassungen. Sehr günstig im Token-Verbrauch.
*   **AG-Pro** (Antigravity Gemini 3.1 Pro): Für schwere Logik, komplexe Mathe-Formeln (z.B. Kampf, Rundenmechanik). Verbraucht mehr Quota, liefert aber tieferes Reasoning.
*   **AG-Claude** (Antigravity Claude Sonnet 4.6): Für UI-Architektur und UX-Entscheidungen von Grund auf. Quota schonen!
*   **Junie** (JetBrains IDE): Exzellent für das Überarbeiten *bestehender* Code-Basen über mehrere Dateien hinweg (z.B. UI-Overhaul, Refactoring der `app.js` und `admin.html`).

---

## 🛠️ PHASE 1: Fundament & Kernschleife (Woche 1)
*Bevor irgendetwas im Spiel passiert, muss die Welt existieren, Spieler müssen sich einloggen können und die Zeit (Ticks) muss laufen.*

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
//| `27_weltkarte_db_migration.md` | **AG-Pro** - Map-Datenbank aufsetzen |
//| `24_feature_weltgenerierung.md` | **AG-Pro** - Logik zur Terrain-Platzierung |
//| `29_feature_auth_system.md` | **AG-Flash** - Login, Tokens, Sicherheit |
//| `31_feature_onboarding.md` | **AG-Claude** - Spieler-Einstieg & erste Provinz |
//| `Rundenmechanik.md` | **AG-Pro** - Kern-Logik der Spielzyklen |
//| `30_feature_server_tick.md` | **AG-Pro** - Cronjob/Task-Runner für die Rundenmechanik |

## 🏗️ PHASE 2: Bauen & Ressourcen (Woche 2)
*Die Spieler sind im Spiel. Nun müssen sie bauen und Ressourcen fördern können.*

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
| `Gebaudebaumechanik.md` | **AG-Pro** - Herzstück des Bausystems |
| `07_feature_demolish.md` & `25_feature_abriss_check.md` | **AG-Flash** - Gebäude wieder abreißen |
| `23_feature_schnellbau.md` | **AG-Claude** - UI/UX für flüssiges Bauen |
| `05_feature_wege_arbeit.md` | **AG-Pro** - Wege-Netzwerk und Arbeitskraft-Verteilung |
| `06_feature_vorkommen_regen.md` | **AG-Pro** - Basis-Ressourcen aus der Umwelt |
| `12_feature_vorkommen.md` | **AG-Flash** - Generierung von Bodenschätzen |
| `10_feature_jagen_sammeln.md` | **AG-Flash** - Basis-Nahrungsbeschaffung |
| `14_feature_tierzucht.md` | **AG-Flash** - Erweiterte Nahrung |

## ⚖️ PHASE 3: Wirtschaft, Handel & Steuern (Woche 3)
*Ressourcen werden in Wertschöpfungsketten umgewandelt und gehandelt.*

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
| `04_feature_steuern_geld.md` | **AG-Pro** - Ökonomie-Grundlage (Münzen) |
| `15_feature_handelskarren.md` | **AG-Flash** - Logistik-Kapazitäten |
| `08_feature_markt_handel.md` | **AG-Pro** - Der globale/lokale Spielermarkt |
| `16_feature_kontor.md` | **AG-Flash** - Automatisierter Handel |
| `17_feature_kueste_hafen.md` | **AG-Flash** - Schiffsrouten |

## ⚔️ PHASE 4: Bevölkerung, Diplomatie & Konflikt (Woche 4)
*Das Spiel wird zum Multiplayer-Erlebnis. Bevölkerung wächst, Grenzen stoßen aneinander.*

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
| `11_feature_altersstruktur.md` | **AG-Pro** - Demografie & Bevölkerungs-Ticks |
| `09_feature_kultur_bildung.md` | **AG-Flash** - Tech-Voraussetzungen & Moral-Boni |
| `13_feature_regierungsformen.md`| **AG-Flash** - Fraktions-Buffs/Debuffs |
| `21_feature_siedler.md` | **AG-Pro** - Neue Provinzen gründen |
| `19_feature_diplomatie.md` | **AG-Pro** - Allianzen, Handelssperren, Kriegserklärung |
| `01_feature_einheiten.md` | **AG-Flash** - Truppen ausheben |
| `20_feature_kampf.md` | **AG-Pro** - Kampf-Algorithmus & Verluste |
| `18_feature_bunker.md` | **AG-Flash** - Verteidigungsanlagen |

## 🖥️ PHASE 5: Admin & UI-Refactoring (Woche 5)
*Alles funktioniert im Backend. Jetzt wird die UI für Spieler und Admins perfektioniert. **Hier ist Junie am stärksten.***

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
| `28_ui_ueberarbeitung.md` | **Junie** - Komplettes Spieler-Frontend-Refactoring |
| `22_feature_gamelog_nachrichten.md`| **Junie** / AG-Claude - In-Game Kommunikation & Logs UI |
| `26_admin_overhaul.md` | **Junie** - Das 80k-Zeichen HTML-Monster modernisieren |
| `gebaeude_admin_grid.md` | **Junie** - Integration des Gebäude-Grids ins Admin-Panel |

## ✨ PHASE 6: Polish, Events & Ausnahmezustände (Woche 6)
*Spieltiefe, Langzeitmotivation und System-Stabilität.*

| Datei | Fokus / Tool-Empfehlung |
| :--- | :--- |
| `02_feature_events.md` | **AG-Pro** - Zufällige Weltereignisse |
| `34_feature_wetter.md` | **AG-Pro** - Jahreszeiten statt Zufallsregen |
| `03_feature_ruinen.md` | **AG-Flash** - Aufgeben / Zerstörung von Provinzen |
| `33_feature_cleanup.md` | **AG-Flash** - Automatischer Ruinen-Verfall bei Inaktivität |
| `32_feature_notfallreserve.md` | **AG-Flash** - Lager-Sperre für Krisenzeiten |
| `35_feature_prov_tags.md` | **AG-Flash** - Admin-Spezialboni für Provinzen |
| `36_feature_offline_mode.md` | **Junie** - Graceful Degradation im JS bei Verbindungsabbruch |
