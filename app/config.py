import os

SECRET_KEY = os.environ.get("SECRET_KEY", "wasteland_ultra_secure_secret_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

DB_PATH = "verbrannte_zone.db"