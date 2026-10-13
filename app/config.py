import os
from pathlib import Path

# Versuche .env Datei zu laden (optional)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        pass  # python-dotenv nicht installiert, ignoriere

# === Required Security Settings ===
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is required! "
        "Set it in .env or as env var. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_DAYS", "7"))

# === Database ===
DB_PATH = os.environ.get("DB_PATH", "verbrannte_zone.db")

# === Server Configuration ===
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# === Logging ===
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# === Optional: Prometheus Metrics ===
PROMETHEUS_ENABLED = os.environ.get("PROMETHEUS_ENABLED", "false").lower() == "true"
PROMETHEUS_PORT = int(os.environ.get("PROMETHEUS_PORT", "9090"))

# === Optional: Rate Limiting ===
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))

# === Optional: CORS (für externe Frontends) ===
CORS_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
