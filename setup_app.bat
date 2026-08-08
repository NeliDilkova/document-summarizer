@echo off
cd /d "%~dp0"

docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop ist nicht installiert oder laeuft nicht.
    echo Bitte installiere Docker Desktop und starte es, bevor du dieses Skript erneut ausfuehrst.
    pause
    exit /b
)

echo Einmaliges Setup wird gestartet. Dies kann je nach Internetverbindung mehrere Minuten dauern...
docker compose build --no-cache

echo Setup abgeschlossen. Du kannst die App jetzt jederzeit mit start_app.bat starten.
pause