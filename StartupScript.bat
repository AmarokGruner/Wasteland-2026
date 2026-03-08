@echo off
title Verbrannte Zone - Startup
echo ==========================================
echo    🔥 Verbrannte Zone - Spielstart 🔥
echo ==========================================
echo.

echo [1/3] Initialisiere Spieldaten (Gebaeude, Ressourcen, etc.)...
python seed_main.py

echo [2/3] Erstelle Benutzerkonten...
python setup_users.py

echo [3/3] Starte den Webserver...
echo.
echo >>> Das Spiel ist gleich unter http://localhost:8000 erreichbar.
echo.
python main.py

pause
