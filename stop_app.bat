@echo off
cd /d "%~dp0"
docker compose down
echo Die Anwendung wurde gestoppt.
pause