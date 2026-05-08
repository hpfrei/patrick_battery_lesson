@echo off
REM Starts the battery web server. A browser tab opens automatically.
REM On first run, the SQLite DB is seeded with sample data.
cd /d "%~dp0"
py -3 server.py
pause
