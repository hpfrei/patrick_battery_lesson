@echo off
REM Starts the battery server. Leave this window open while you use the client.
cd /d "%~dp0"
py -3 server.py
pause
