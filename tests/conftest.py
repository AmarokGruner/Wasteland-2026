"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests.
"""

import pytest
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models from the main application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import Base, BuildingType, Resource, Vorkommen, TerrainType


# Test database path
TEST_DB_PATH = Path(__file__).parent / "test.db"


@pytest.fixture(scope="session")
def test_db_engine():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine


@pytest.fixture
def db_session(test_db_engine):
    """Create a database session for testing"""
    SessionLocal = sessionmaker(bind=test_db_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return the path to the fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def html_fixtures_dir(fixtures_dir):
    """Return the path to the HTML fixtures directory"""
    return fixtures_dir / "html"


@pytest.fixture
def sample_gebaeude_html():
    """Sample HTML for a building detail page (real website format)"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Bunker - Verbrannte Zone</title></head>
    <body>
        <div class='title'>Bunker <i>(ID: 1)</i></div>
        <table>
            <tr><td class='boxfarbe4'>Gebäudesymbol </td><td class='boxfarbe9'><img src='./gebpics/1/bunker.png'></td></tr>
            <tr><td class='boxfarbe4'>Gebäudebild</td><td class='boxfarbe9'><img src='/geb/1/g1_0r.png'></td></tr>
            <tr><td class='boxfarbe4'>Kategorie</td><td class='boxfarbe9'>Start</td></tr>
            <tr><td class='boxfarbe4'>Bautyp</td><td class='boxfarbe9'>Vorgabe(nicht Baubar)</td></tr>
            <tr><td class='boxfarbe4'>Ausbaubar</td><td class='boxfarbe9'>NEIN</td></tr>
            <tr><td class='boxfarbe4'>Unique(einmalig)</td><td class='boxfarbe9'>JA (einmal pro Spieler)</td></tr>
            <tr><td class='boxfarbe4'>Nur an Küste</td><td class='boxfarbe9'>NEIN</td></tr>
            <tr><td class='boxfarbe4'>ist Feld</td><td class='boxfarbe9'>NEIN</td></tr>
            <tr><td class='boxfarbe4'>Benötigtes Techlevel</td><td class='boxfarbe9'>0</td></tr>
            <tr><td class='boxfarbe4'>Baukosten in Mips</td><td class='boxfarbe9'>0</td></tr>
            <tr><td class='boxfarbe4'>Arbeiter</td><td class='boxfarbe9'>10</td></tr>
            <tr><td class='boxfarbe4'>Wohnraum</td><td class='boxfarbe9'>10</td></tr>
            <tr><td class='boxfarbe4'>Lagerraumkapazität</td><td class='boxfarbe9'>20000</td></tr>
            <tr><td class='boxfarbe4'>Beschreibung</td><td class='boxfarbe9'>Der Bunker ist dein erstes Gebäude.</td></tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_rohstoffe_html():
    """Sample HTML for a resource detail page (real website format)"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Wasser - Verbrannte Zone</title></head>
    <body>
        <div class='title'>Wasser <i>(ID: 1)</i></div>
        <table>
            <tr><td class='boxfarbe4'>Typ</td><td class='boxfarbe9'>Getränk</td></tr>
            <tr><td class='boxfarbe4'>Produktionswert</td><td class='boxfarbe9'>21</td></tr>
            <tr><td class='boxfarbe4'>Beschreibung</td><td class='boxfarbe9'>Wasser ist das Hauptgetränk.</td></tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_list_html():
    """Sample HTML for a list page (real website format)"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Gebäude Liste - Verbrannte Zone</title></head>
    <body>
        <div class='title'>Gebäude Liste</div>
        <table>
            <tr><td><a href="gebaeudevorschau.php?id=1">Bunker</a></td><td>Bunker</td></tr>
            <tr><td><a href="gebaeudevorschau.php?id=2">Kartoffelfarm</a></td><td>Kartoffelfarm</td></tr>
            <tr><td><a href="gebaeudevorschau.php?id=3">Erdnussfarm</a></td><td>Erdnussfarm</td></tr>
        </table>
    </body>
    </html>
    """
