# Entwicklung & Testing

**Wasteland Development Guide | Version 1.6**

---

## 🛠️ Entwicklungsumgebung einrichten

### Voraussetzungen
- Python 3.13+
- Git
- Editor/IDE (VS Code, PyCharm, etc.)

### Setup-Schritte
```bash
# 1. Repository klonen
git clone https://github.com/AmarokGruner/Wasteland-2026.git
cd Wasteland

# 2. Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Development Dependencies installieren
pip install -r requirements.txt
pip install pytest pytest-asyncio flake8 mypy black

# 4. Pre-commit Hooks installieren (optional)
pip install pre-commit
pre-commit install
```

---

## 📁 Projektstruktur

```
Wasteland/
├── app/                    # FastAPI Backend
│   ├── main.py            # Hauptanwendung
│   ├── config.py          # Konfiguration
│   ├── database.py        # Datenbank-Verbindung
│   ├── models.py          # SQLAlchemy Modelle
│   └── api/              # API Endpunkte
│       ├── auth.py       # Authentifizierung
│       ├── province.py   # Provinz-Management
│       ├── market.py     # Handel
│       └── admin/        # Admin-API
├── seeds/                # Datenbank-Initialisierung
│   ├── seed_gebaeude.py  # Gebäude-Daten
│   ├── seed_ressourcen.py# Ressourcen-Daten
│   └── seed_main.py      # Haupt-Seed-Skript
├── js/                   # Frontend JavaScript
│   ├── app.js           # Hauptanwendung
│   ├── province.js      # Provinz-UI
│   └── ...             # Weitere Module
├── admin/               # Admin HTML
├── tests/               # Test-Suite
│   ├── test_auth.py    # Auth-Tests
│   ├── test_province.py# Provinz-Tests
│   └── integration/    # Integration Tests
├── docs/               # Dokumentation (8 Dateien)
└── requirements.txt    # Python Abhängigkeiten
```

---

## 🧪 Testing

### Test-Struktur
```
tests/
├── conftest.py              # Test-Konfiguration
├── test_auth.py             # Authentifizierungstests
├── test_province.py          # Provinz-Tests
├── test_buildings.py         # Gebäude-Tests
├── test_resources.py         # Ressourcen-Tests
└── integration/              # Integration Tests
    ├── test_api.py          # API-End-to-End
    └── test_database.py     # Datenbank-Tests
```

### Tests ausführen
```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage Report
pytest tests/ --cov=app --cov-report=html

# Nur schnelle Tests
pytest tests/ -m "not slow"

# Specific Test File
pytest tests/test_auth.py -v
```

### Beispiel-Test
```python
import pytest
from app.database import get_db
from app.models import Province

def test_create_province(client, db_session):
    """Test: Neue Provinz erstellen"""
    response = client.post(
        "/api/province/",
        json={"name": "Test Provinz"},
        headers={"Authorization": "Bearer <token>"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Provinz"
    assert db_session.query(Province).count() == 1
```

---

## 🔍 Code Quality

### Linting mit Flake8
```bash
# Alle Python Dateien prüfen
flake8 app/ seeds/ tests/

# Mit Konfiguration (.flake8)
[flake8]
max-line-length = 120
exclude = venv, .git, __pycache__
ignore = E203, W503
```

### Type Checking mit mypy
```bash
# Typ-Checks durchführen
mypy app/ --ignore-missing-imports

# Mit Konfiguration (mypy.ini)
[mypy]
python_version = 3.13
warn_return_any = True
strict_optional = True
```

### Code Formatting mit black
```bash
# Code automatisch formatieren
black app/ seeds/ tests/

# Nur prüfen (ohne ändern)
black --check app/
```

---

## 🔄 Git Workflow

### Branching Strategy
```
main              # Produktionscode
├── feature/auth  # Feature-Branches
├── bugfix/login  # Bugfix-Branches
└── release/v1.7  # Release-Branches
```

### Commit Messages
```bash
# Format: type: description

# Types:
feat:     Neues Feature
fix:       Bugfix
docs:      Dokumentation
style:     Code-Stil (kein Funktionschange)
refactor:  Refactoring
test:      Tests
chore:     Build/Tooling

# Beispiele:
git commit -m "feat: Add building demolition system"
git commit -m "fix: Resolve province creation race condition"
git commit -m "docs: Update API documentation for v1.6"
```

### Pull Request Template
```markdown
## Beschreibung
Was wurde geändert?

## Typ
- [ ] Feature
- [ ] Bugfix
- [ ] Documentation
- [ ] Refactoring

## Tests
- [ ] Unit Tests bestanden
- [ ] Integration Tests bestanden
- [ ] Manuell getestet

## Screenshots (falls UI Änderungen)
[Hier einfügen]
```

---

## 📝 Entwicklungstipps

### 1. Database First Design
```python
# Immer zuerst Model definieren, dann API
class Province(Base):
    __tablename__ = 'provinzen'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # ... weitere Felder

# Dann API Endpoint schreiben
@router.post("/province/")
async def create_province(province: ProvinceCreate):
    ...
```

### 2. Error Handling
```python
# Immer spezifische Exceptions werfen
from fastapi import HTTPException

@router.get("/province/{id}")
async def get_province(id: int):
    province = db.query(Province).get(id)
    if not province:
        raise HTTPException(status_code=404, detail="Province nicht gefunden")
    return province
```

### 3. Validation mit Pydantic
```python
from pydantic import BaseModel, Field

class BuildingCreate(BaseModel):
    gebaeude_typ_id: int = Field(..., ge=1, le=209)
    x: int = Field(..., ge=0, lt=50)
    y: int = Field(..., ge=0, lt=50)
```

### 4. Logging
```python
import logging

logger = logging.getLogger(__name__)

def create_building(province_id: int, building_data: dict):
    logger.info(f"Building created in province {province_id}")
    # ... Logik
    
    logger.error(f"Failed to create building: {error}")
```

---

## 🚀 Debugging

### Server Logs ansehen
```bash
# Development Mode (mit Reload)
uvicorn app.main:app --reload --log-level debug

# Production Mode
sudo journalctl -u wasteline -f
```

### Database Queries debuggen
```python
# SQLAlchemy Query Logging aktivieren
import sqlalchemy
sqlalchemy.event.listen(sqlalchemy.engine, 'before_cursor_execute', 
                       lambda conn, cursor, statement, parameters, context, executemany:
                       print(f"QUERY: {statement} {parameters}"))
```

### Frontend Debugging
- **Browser DevTools:** Network Tab für API Calls
- **Console:** JavaScript Errors
- **Sources:** Breakpoints setzen

---

## 📊 CI/CD (Optional)

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: pytest tests/ -v
    
    - name: Check linting
      run: flake8 app/
```

---

## 📚 Nützliche Ressourcen

### FastAPI Documentation
- https://fastapi.tiangolo.com/

### SQLAlchemy Documentation
- https://docs.sqlalchemy.org/

### Pytest Documentation
- https://docs.pytest.org/

---

**Letzte Aktualisierung:** 2026-10-14  
**Empfohlene Python-Version:** 3.13+
