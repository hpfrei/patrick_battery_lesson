@echo off
REM Starts the GUI client. Run setup.bat once and run_server.bat first.
cd /d "%~dp0"
py -3 client.py
