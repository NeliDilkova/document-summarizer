@echo off
start /min cmd /c "docker compose up --build"
timeout /t 8 /nobreak
start http://localhost:8050