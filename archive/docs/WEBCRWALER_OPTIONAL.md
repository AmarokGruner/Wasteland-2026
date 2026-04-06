# Webcrawler - Optionale Erweiterungen

Dieses Dokument beschreibt die umgesetzten optionalen Erweiterungen sowie weitere mögliche Erweiterungen.

---

## ✅ Umgesetzte Optionale Erweiterungen

### 1. Export-Funktion (CSV & JSON)

**API Endpunkte:**
- `GET /api/admin/crawler/export/csv` - Export aller pending changes als CSV
- `GET /api/admin/crawler/export/json` - Export aller pending changes als JSON
- `GET /api/admin/crawler/export/category/{category}` - Filtern nach Kategorie

**UI Integration:**
- Export-Buttons in der Pending-Changes-Tabelle
- Automatische Dateinamen mit Timestamp
- Download als Blob

**Beispiel-CSV-Output:**
```csv
ID,Session,Kategorie,Aktion,Record_ID,Tabelle,Geänderte_Felder,Erstellt
1,42,gebaeude,INSERT,999,gebaeude_typen,"name,kosten_mips",2026-04-04T20:00:00
```

### 2. Kategorie-Filter in UI

**Merkmale:**
- Dropdown-Filter mit allen 8 Kategorien
- Live-Filterung der Tabelle
- „Alle" Option für Reset
- Kombination mit Suchfunktion möglich

**Implementierung:**
```javascript
function applyCategoryFilter() {
    const filter = document.getElementById('categoryFilter').value;
    // Filterung der Tabellenzeilen
}
```

---

## 🔧 Weitere Mögliche Erweiterungen

### 3. Scheduled Crawls

**Anforderung:**
- Automatisierte Crawls zu festgelegten Zeiten
- Cron-ähnliche Planung (täglich, stündlich, wöchentlich)
- E-Mail/Bridge-Notifications bei neuen Änderungen

**Implementierungsoptionen:**
- **APScheduler** Integration in FastAPI
- **Celery** Tasks für langlaufende Crawls
- **SQLite**-basierte Job-Queue

**Beispiel-Endpoint:**
```python
@router.post("/schedule")
async def schedule_crawl(crontab: str, categories: List[str]):
    """Erstelle geplanten Crawl (z.B. '0 2 * * *' für 02:00 Uhr täglich)"""
    ...
```

### 4. Webhook-Integration

**Anforderung:**
- Webhooks für Events: `crawl.completed`, `changes.detected`, `session.failed`
- Konfigurierbare Webhook-URLs im Admin-Setting
- Retry-Logik mit Exponential Backoff

**Datenstruktur:**
```json
{
  "event": "changes.detected",
  "session_id": 42,
  "total_changes": 15,
  "categories": ["gebaeude", "rohstoffe"],
  "timestamp": "2026-04-04T20:30:00Z"
}
```

### 5. Differenzierte Diff-Ansicht

**Aktueller Zustand:** JSON-Preview
**Verbesserungspotenzial:**
- Side-by-side Diff mit Farbcodierung
- Feld-für-Feld Vergleich
- Historie der Änderungen pro Record

### 6. Bulk-Actions

**Mögliche Features:**
- Checkbox-Selektion mehrerer Änderungen
- "Alle dieser Kategorie freigeben/ablehnen"
- Massenspeicherung mit Bestätigung

### 7. Crawler-Statistiken

**Metriken:**
- Durchschnittliche Crawl-Dauer
- Änderungen pro Kategorie (Trend)
- Freigabe-Rate (%)
- Session-Historie mit Erfolgsquote

---

## Status

| Feature | Status |
|---------|--------|
| Export CSV/JSON | ✅ Implementiert |
| Kategorie-Filter | ✅ Implementiert |
| Scheduled Crawls | ⚪ Nicht implementiert |
| Webhooks | ⚪ Nicht implementiert |
| Diff-Verbesserung | ⚪ Nicht implementiert |
| Bulk-Actions | ⚪ Nicht implementiert |
| Statistiken | ⚪ Nicht implementiert |

---

**Dokument erstellt:** 2026-04-04  
**Nächste Wartung prüfen:** Bei Erweiterungsbedarf
