@echo off
REM One-time setup: creates batteries.db with sample data.
cd /d "%~dp0"
py -3 seed_db.py
echo.
pause
