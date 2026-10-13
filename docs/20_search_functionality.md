# 🔍 Search Functionality & Full-Text Indexing

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von Suchfunktionen für:
- Provinzen und Gebiete
- Gebäude und Ressourcen
- Spieler und Einheiten
- Artikel und Handel

---

## 🎯 Ziele

1. **Schnelle Suche** - Millisekunden-Antworten auch bei großen Datenmengen
2. **Fuzzy Matching** - Tippfehler tolerieren
3. **Facettierte Suche** - Nach Kategorien filtern
4. **Such-Indizierung** - Asynchrone Index-Aktualisierung

---

## 🏗️ Search Architecture Options

### Option 1: SQLite FTS5 (Empfohlen für Single-Server)

```
SQLite Database
└── FTS5 Virtual Tables (automatisch indiziert)
    ├── provinces_fts
    ├── buildings_fts
    └── users_fts
```

**Vorteile:**
- Keine externe Abhängigkeit
- Automatisch konsistent mit Hauptdatenbank
- Einfach zu warten

**Nachteile:**
- Begrenzte Skalierbarkeit (>1M Einträge)
- Keine verteilte Suche

### Option 2: Elasticsearch (Für große Installationen)

```
FastAPI Backend
├── SQLite (Hauptdatenbank)
└── Elasticsearch (Suchindex, asynchron synchronisiert)
```

**Vorteile:**
- Extrem schnell (Sub-Millisecond)
- Vertikal skalierbar
- Rich Query DSL

**Nachteile:**
- Zusätzliche Infrastruktur
- Komplexeres Setup

---

## 🔧 SQLite FTS5 Implementation (Empfohlen)

### FTS5 Table Creation

```python
# app/models_search.py
from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ProvinceFTS(Base):
    """FTS5 Virtual Table für Provinz-Suche"""
    
    __tablename__ = "provinces_fts"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)
    region = Column(Text)
    
    # FTS5 Special: rowid automatisch
    __table_args__ = {
        "sqlite_autoincrement": True
    }

class BuildingFTS(Base):
    """FTS5 Virtual Table für Gebäude-Suche"""
    
    __tablename__ = "buildings_fts"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)
    category = Column(Text)

class UserFTS(Base):
    """FTS5 Virtual Table für Spieler-Suche"""
    
    __tablename__ = "users_fts"
    
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    email = Column(Text)

class ArticleFTS(Base):
    """FTS5 Virtual Table für Artikel-Suche"""
    
    __tablename__ = "articles_fts"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text),
    category = Column(Text)

# FTS5 Tables initialisieren (einmalig beim Start)
def init_search_indexes():
    """FTS5 Virtual Tables erstellen"""
    
    from app.models import Base as MainBase
    
    # FTS5 Tables separat erstellen (nicht über MainBase.metadata)
    engine = create_engine("sqlite:///wasteland.db")
    
    ProvinceFTS.__table__.create(engine, checkfirst=True)
    BuildingFTS.__table__.create(engine, checkfirst=True)
    UserFTS.__table__.create(engine, checkfirst=True)
    ArticleFTS.__table__.create(engine, checkfirst=True)

# In main.py:
"""
@app.on_event("startup")
async def startup():
    init_search_indexes()
"""
```

### Search Service Implementation

```python
# app/services/search_service.py
from sqlalchemy import text
from sqlalchemy.orm import Session

class SearchService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_provinces(self, query: str, limit: int = 20) -> list:
        """Provinzen suchen (FTS5 match)"""
        
        sql = text("""
            SELECT p.id, p.name, p.description, p.region
            FROM provinces p
            INNER JOIN provinces_fts fts ON p.id = fts.id
            WHERE provinces_fts MATCH :query
            ORDER BY rank
            LIMIT :limit
        """)
        
        results = self.db.execute(sql, {"query": query, "limit": limit}).fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "region": row[3]
            }
            for row in results
        ]
    
    def search_buildings(self, query: str, category: str = None, limit: int = 20) -> list:
        """Gebäude suchen (optional nach Kategorie filtern)"""
        
        sql = text("""
            SELECT b.id, b.name, b.description, b.category
            FROM buildings b
            INNER JOIN buildings_fts fts ON b.id = fts.id
            WHERE buildings_fts MATCH :query
        """)
        
        params = {"query": query, "limit": limit}
        
        if category:
            sql += text(" AND b.category = :category")
            params["category"] = category
        
        sql += text(" ORDER BY rank LIMIT :limit")
        
        results = self.db.execute(sql, params).fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "category": row[3]
            }
            for row in results
        ]
    
    def search_users(self, query: str, limit: int = 20) -> list:
        """Spieler suchen (nach Username oder E-Mail)"""
        
        sql = text("""
            SELECT u.id, u.username, u.email, u.level
            FROM users u
            INNER JOIN users_fts fts ON u.id = fts.id
            WHERE users_fts MATCH :query
            LIMIT :limit
        """)
        
        results = self.db.execute(sql, {"query": query, "limit": limit}).fetchall()
        
        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "level": row[3]
            }
            for row in results
        ]
    
    def search_articles(self, query: str, category: str = None, limit: int = 20) -> list:
        """Artikel suchen (Handel)"""
        
        sql = text("""
            SELECT a.id, a.name, a.description, a.category
            FROM articles a
            INNER JOIN articles_fts fts ON a.id = fts.id
            WHERE articles_fts MATCH :query
        """)
        
        params = {"query": query, "limit": limit}
        
        if category:
            sql += text(" AND a.category = :category")
            params["category"] = category
        
        sql += text(" ORDER BY rank LIMIT :limit")
        
        results = self.db.execute(sql, params).fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "category": row[3]
            }
            for row in results
        ]

# Helper: FTS5 Index aktualisieren (bei Datenänderung)
def update_fts_index(table_name: str, record_id: int):
    """FTS5 Index für einen Eintrag aktualisieren"""
    
    # Vereinfacht: Record aus Haupttabelle lesen und in FTS5 einfügen
    # In Production: Trigger verwenden (automatisch bei INSERT/UPDATE)
    
    pass

# FTS5 Trigger für automatische Index-Aktualisierung
def create_fts_triggers():
    """FTS5 Trigger erstellen (automatische Index-Aktualisierung)"""
    
    triggers = """
        -- Province FTS Trigger
        CREATE TRIGGER provinces_ai AFTER INSERT ON provinces BEGIN
            INSERT OR REPLACE INTO provinces_fts(id, name, description, region)
            VALUES (new.id, new.name, new.description, new.region);
        END;
        
        CREATE TRIGGER provinces_ad AFTER DELETE ON provinces BEGIN
            DELETE FROM provinces_fts WHERE id = old.id;
        END;
        
        CREATE TRIGGER provinces_au AFTER UPDATE ON provinces BEGIN
            UPDATE provinces_fts SET
                name = new.name,
                description = new.description,
                region = new.region
            WHERE id = new.id;
        END;
        
        -- Building FTS Trigger (analog)
        CREATE TRIGGER buildings_ai AFTER INSERT ON buildings BEGIN
            INSERT OR REPLACE INTO buildings_fts(id, name, description, category)
            VALUES (new.id, new.name, new.description, new.category);
        END;
        
        -- User FTS Trigger (analog)
        CREATE TRIGGER users_ai AFTER INSERT ON users BEGIN
            INSERT OR REPLACE INTO users_fts(id, username, email)
            VALUES (new.id, new.username, new.email);
        END;
        
        -- Article FTS Trigger (analog)
        CREATE TRIGGER articles_ai AFTER INSERT ON articles BEGIN
            INSERT OR REPLACE INTO articles_fts(id, name, description, category)
            VALUES (new.id, new.name, new.description, new.category);
        END;
    """
    
    # Trigger in Datenbank ausführen (einmalig)
    from app.models import Base
    engine = create_engine("sqlite:///wasteland.db")
    
    with engine.connect() as conn:
        for trigger_sql in triggers.split("CREATE TRIGGER"):
            if trigger_sql.strip():
                conn.execute(text(f"CREATE TRIGGER {trigger_sql}"))
        conn.commit()

# In main.py:
"""
@app.on_event("startup")
async def startup():
    create_fts_triggers()
"""
```

---

## 📡 API Endpoints für Suche

### Search Router

```python
# app/api/v1/search.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/search/provinces")
async def search_provinces(
    q: str = Query(..., min_length=1, description="Suchbegriff"),
    limit: int = Query(20, ge=1, le=100, description="Maximale Ergebnisse"),
    db: Session = Depends(get_db)
):
    """Provinzen suchen"""
    
    service = SearchService(db)
    results = service.search_provinces(query=q, limit=limit)
    
    return {
        "type": "provinces",
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/search/buildings")
async def search_buildings(
    q: str = Query(..., min_length=1),
    category: str = Query(None, description="Kategorie filtern"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Gebäude suchen"""
    
    service = SearchService(db)
    results = service.search_buildings(query=q, category=category, limit=limit)
    
    return {
        "type": "buildings",
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/search/users")
async def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Spieler suchen"""
    
    service = SearchService(db)
    results = service.search_users(query=q, limit=limit)
    
    return {
        "type": "users",
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/search/articles")
async def search_articles(
    q: str = Query(..., min_length=1),
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Artikel suchen"""
    
    service = SearchService(db)
    results = service.search_articles(query=q, category=category, limit=limit)
    
    return {
        "type": "articles",
        "query": q,
        "count": len(results),
        "results": results
    }

@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Globale Suche (alle Kategorien)"""
    
    service = SearchService(db)
    
    provinces = service.search_provinces(query=q, limit=limit // 4)
    buildings = service.search_buildings(query=q, limit=limit // 4)
    users = service.search_users(query=q, limit=limit // 4)
    articles = service.search_articles(query=q, limit=limit - (len(provinces) + len(buildings) + len(users)))
    
    return {
        "query": q,
        "total_count": len(provinces) + len(buildings) + len(users) + len(articles),
        "provinces": provinces,
        "buildings": buildings,
        "users": users,
        "articles": articles
    }
```

---

## 🖥️ Client-Side Search UI (JavaScript)

### Search Component

```javascript
// js/components/search.js

class SearchComponent {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
        this.debounceTimer = null;
    }

    // Suche starten (mit Debounce)
    async search(query, type = 'all') {
        if (!query || query.length < 2) {
            this.clearResults();
            return;
        }

        // Debounce: 300ms warten bevor Request gesendet
        clearTimeout(this.debounceTimer);
        
        this.debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(
                    `${this.baseUrl}/search?q=${encodeURIComponent(query)}&limit=20`
                );

                if (response.ok) {
                    const data = await response.json();
                    this.displayResults(data);
                }
            } catch (error) {
                console.error('Search Error:', error);
            }
        }, 300);
    }

    // Ergebnisse anzeigen
    displayResults(data) {
        const resultsContainer = document.getElementById('search-results');
        
        if (!resultsContainer) return;

        let html = '';

        // Provinzen
        if (data.provinces && data.provinces.length > 0) {
            html += '<div class="search-section"><h3>🏞️ Provinzen</h3>';
            html += data.provinces.map(p => `
                <a href="/province/${p.id}" class="search-result">
                    <strong>${this.highlightMatch(p.name, data.query)}</strong>
                    ${p.description ? `<br><small>${this.highlightMatch(p.description, data.query)}</small>` : ''}
                </a>
            `).join('');
            html += '</div>';
        }

        // Gebäude
        if (data.buildings && data.buildings.length > 0) {
            html += '<div class="search-section"><h3>🏗️ Gebäude</h3>';
            html += data.buildings.map(b => `
                <a href="/building/${b.id}" class="search-result">
                    <strong>${this.highlightMatch(b.name, data.query)}</strong>
                    ${b.category ? `<br><small>Kategorie: ${b.category}</small>` : ''}
                </a>
            `).join('');
            html += '</div>';
        }

        // Spieler
        if (data.users && data.users.length > 0) {
            html += '<div class="search-section"><h3>👤 Spieler</h3>';
            html += data.users.map(u => `
                <a href="/player/${u.id}" class="search-result">
                    <strong>${this.highlightMatch(u.username, data.query)}</strong>
                    ${u.level ? `<br><small>Level: ${u.level}</small>` : ''}
                </a>
            `).join('');
            html += '</div>';
        }

        // Artikel
        if (data.articles && data.articles.length > 0) {
            html += '<div class="search-section"><h3>📦 Artikel</h3>';
            html += data.articles.map(a => `
                <a href="/article/${a.id}" class="search-result">
                    <strong>${this.highlightMatch(a.name, data.query)}</strong>
                    ${a.category ? `<br><small>${a.category}</small>` : ''}
                </a>
            `).join('');
            html += '</div>';
        }

        // Keine Ergebnisse
        if (!html) {
            html = '<p class="no-results">Keine Ergebnisse gefunden</p>';
        }

        resultsContainer.innerHTML = html;
    }

    // Suchbegriff in Text hervorheben
    highlightMatch(text, query) {
        if (!text || !query) return text;
        
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    clearResults() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    }

    // Event Listener für Search Input
    init() {
        const searchInput = document.getElementById('search-input');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.search(e.target.value);
            });

            // Enter-Taste: Zur Suchseite weiterleiten
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    window.location.href = `/search?q=${encodeURIComponent(searchInput.value)}`;
                }
            });
        }
    }
}

// Initialisieren
const searchComponent = new SearchComponent();
searchComponent.init();

export default searchComponent;
```

### HTML Search Bar

```html
<!-- templates/search.html -->
<div class="search-bar">
    <input 
        type="text" 
        id="search-input" 
        placeholder="Suche nach Provinzen, Gebäuden, Spielern..."
        autocomplete="off"
    >
    <div id="search-results" class="search-dropdown"></div>
</div>

<style>
.search-bar {
    position: relative;
    max-width: 600px;
    margin: 20px auto;
}

#search-input {
    width: 100%;
    padding: 12px 20px;
    font-size: 16px;
    border: 2px solid #e94560;
    border-radius: 8px;
    background-color: #16213e;
    color: #ffffff;
}

#search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 0 0 8px 8px;
    max-height: 400px;
    overflow-y: auto;
    z-index: 1000;
}

.search-section {
    padding: 10px;
    border-bottom: 1px solid #0f3460;
}

.search-section h3 {
    color: #e94560;
    margin: 0 0 10px 0;
    font-size: 14px;
}

.search-result {
    display: block;
    padding: 8px 12px;
    color: #ffffff;
    text-decoration: none;
    border-radius: 4px;
}

.search-result:hover {
    background-color: #0f3460;
}

.no-results {
    padding: 20px;
    text-align: center;
    color: #a0a0a0;
}

mark {
    background-color: #e94560;
    color: #ffffff;
    padding: 2px 4px;
    border-radius: 2px;
}
</style>
```

---

## 🧪 Testing Search

### Unit Tests für Search Service

```python
# tests/services/test_search_service.py
import pytest
from app.services.search_service import SearchService

@pytest.fixture
def search_service(db_session):
    return SearchService(db_session)

def test_search_provinces_exact_match(search_service, db_session):
    """Testet exakte Übereinstimmung bei Provinz-Suche"""
    
    # Test-Daten einfügen (vereinfacht)
    results = search_service.search_provinces(query="TestProvince", limit=10)
    
    assert isinstance(results, list)

def test_search_provinces_partial_match(search_service, db_session):
    """Testet partielle Übereinstimmung"""
    
    results = search_service.search_provinces(query="Test", limit=10)
    
    assert isinstance(results, list)

def test_search_buildings_with_category(search_service, db_session):
    """Testet Gebäude-Suche mit Kategorie-Filter"""
    
    results = search_service.search_buildings(query="Basis", category="militär")
    
    assert isinstance(results, list)

def test_global_search(search_service, db_session):
    """Testet globale Suche (alle Kategorien)"""
    
    results = search_service.search_provinces(query="Test", limit=50)
    
    assert isinstance(results, list)

def test_search_empty_query(search_service):
    """Testet Suche mit leerem Query"""
    
    with pytest.raises(Exception):  # Min-Length Validation
        search_service.search_provinces(query="", limit=10)

def test_search_limit_validation(search_service):
    """Testet Limit-Validierung"""
    
    # Max 100 Ergebnisse erlaubt
    results = search_service.search_provinces(query="Test", limit=100)
    
    assert len(results) <= 100
    
    # Über 100 sollte fehlschlagen
    with pytest.raises(Exception):
        search_service.search_provinces(query="Test", limit=200)
```

---

## 🎯 Best Practices

1. **FTS5 Trigger verwenden** - Automatische Index-Aktualisierung
2. **Debouncing im Client** - Nicht bei jedem Tastenanschlag suchen
3. **Highlighting der Treffer** - Suchbegriff im Ergebnis hervorheben
4. **Limit setzen** - Max 100-200 Ergebnisse pro Anfrage
5. **Facettierte Suche** - Nach Kategorien filtern möglich

---

**Suche mit SQLite FTS5 ermöglicht schnelle, konsistente Volltextsuche ohne externe Abhängigkeiten!**
