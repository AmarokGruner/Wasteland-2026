# Verbrannte Zone - Admin Handbuch
> **Admin-UI Features, APIs & Workflows**

## Inhalt
1. Admin-UI Überblick
2. Webcrawler-Integration  
3. API Endpunkte
4. Building System
5. Finanzen & Handel
6. Troubleshooting

## Admin-UI Überblick
URL: http://localhost:8011/admin.html
Login: admin / admin

### Module (11 Tabs)
- Dashboard, Spieler, Weltkarte, Gamelog, Broadcast, Ticks, Webcrawler, Daten-Editoren

### Modularisierung
- Jeder Tab lädt JavaScript separat
- Services: /admin/js/services/*.js

## Webcrawler-Integration
Workflow: Start → Scrape → Review → Approve → Sync

### Kategorien (8): Gebäude, Rohstoffe, Vorkommen, Terrains, Lebewesen, Artikel, Einheiten, Regierungen

### API Endpunkte
POST /api/admin/crawler/start
GET /api/admin/crawler/status
GET /api/admin/crawler/results
POST /api/admin/crawler/approve/{id}
POST /api/admin/crawler/reject/{id}
GET /api/admin/crawler/export/csv
GET /api/admin/crawler/export/json

## Building System
15x15 Grid, Level-Unlocks 1-8

## Finanzen
4-Konten-System: Spielerkonto, Betriebskonto, Staatskonto, PKV-Konto

## Troubleshooting
Siehe ARCHITECTURE.md und FAIL_LOG.md

---
**Version:** 3.5 | **Update:** 2026-04-05
