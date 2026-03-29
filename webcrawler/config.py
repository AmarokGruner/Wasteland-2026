# Webcrawler Configuration
import os
from pathlib import Path

# Base directory (webcrawler folder)
BASE_DIR = Path(__file__).parent.resolve()

# Project root (parent of webcrawler)
PROJECT_ROOT = BASE_DIR.parent

# Database path
DB_PATH = PROJECT_ROOT / "verbrannte_zone.db"

# Website configuration
BASE_URL = "https://v3.verbranntezone.ch/"
LOGIN_URL = BASE_URL + "index.php"  # Login form is on index.php

# List URLs for each category
LIST_URLS = {
    "rohstoffe": BASE_URL + "rohstoffelist.php",
    "gebaeude": BASE_URL + "gebaeudelist.php",
    "vorkommen": BASE_URL + "vorkommenlist.php",
    "terrains": BASE_URL + "terrainlist.php",
    "lebewesen": BASE_URL + "lebewesenlist.php",
    "artikel": BASE_URL + "artikellist.php",
    "einheiten": BASE_URL + "einheitenlist.php",
    "regierungen": BASE_URL + "regierungenlist.php",
}

# Detail URL patterns (will be formatted with ID)
DETAIL_URLS = {
    "rohstoffe": BASE_URL + "rohstoffevorschau.php?id={id}",
    "gebaeude": BASE_URL + "gebaeudevorschau.php?id={id}",
    "vorkommen": BASE_URL + "vorkommenvorschau.php?id={id}",
    "terrains": BASE_URL + "terrainvorschau.php?id={id}",
    "lebewesen": BASE_URL + "tiervorschau.php?id={id}",
    "artikel": BASE_URL + "artikelvorschau.php?id={id}",
    "einheiten": BASE_URL + "einheitenvorschau.php?id={id}",
    "regierungen": BASE_URL + "regierungenvorschau.php?id={id}",
}

# Request settings
REQUEST_TIMEOUT = 10  # seconds
REQUEST_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3

# Cache and logs directories
CACHE_DIR = BASE_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Category to parser module mapping
PARSER_MODULES = {
    "gebaeude": ("parsers.gebaeude_parser", "parse_gebaeude", "parse_gebaeude_list"),
    "rohstoffe": ("parsers.rohstoffe_parser", "parse_rohstoffe", "parse_rohstoffe_list"),
    "vorkommen": ("parsers.vorkommen_parser", "parse_vorkommen", "parse_vorkommen_list"),
    "terrains": ("parsers.terrain_parser", "parse_terrain", "parse_terrain_list"),
    "lebewesen": ("parsers.lebewesen_parser", "parse_lebewesen", "parse_lebewesen_list"),
    "artikel": ("parsers.artikel_parser", "parse_artikel", "parse_artikel_list"),
    "einheiten": ("parsers.einheiten_parser", "parse_einheiten", "parse_einheiten_list"),
    "regierungen": ("parsers.regierungen_parser", "parse_regierung", "parse_regierung_list"),
}

# Category to DB model mapping (for sync)
DB_MODELS = {
    "gebaeude": ("app.models", "BuildingType"),
    "rohstoffe": ("app.models", "Resource"),
    "vorkommen": ("app.models", "Vorkommen"),
    "terrains": ("app.models", "TerrainType"),
    "lebewesen": ("app.models", "AnimalTemplate"),
    "artikel": ("app.models", "Article"),
    "einheiten": ("app.models", "UnitType"),
    "regierungen": ("app.models", "Regierungsform"),
}

# Environment variables (with defaults)
def get_credentials():
    """Load credentials from environment or .env file"""
    username = os.getenv("VZ_USERNAME", "Dargoamarok")
    password = os.getenv("VZ_PASSWORD", "katerfelix")
    return {"username": username, "password": password}
