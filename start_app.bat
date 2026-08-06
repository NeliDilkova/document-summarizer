@echo off
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop ist nicht installiert oder laeuft nicht.
    echo Bitte installiere Docker Desktop und starte es, bevor du dieses Skript erneut ausfuehrst.
    pause
    exit /b
)
start /min cmd /c "docker compose up --build"
timeout /t 20 /nobreak
start http://localhost:8050