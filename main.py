# Wasteland - Verbrannte Zone
# Main Entry Point
#
# Das Projekt wurde modularisiert. Die API-Endpoints befinden sich in:
# - app/api/auth.py        → Auth-Endpoints (Login, Logout, Token)
# - app/api/admin/         → Admin-Endpoints
# - app/main.py            → FastAPI App-Setup mit Scheduler

from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)