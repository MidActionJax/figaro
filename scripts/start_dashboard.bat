@echo off
REM Starts the Figaro dashboard silently, unless something is already listening
REM on its port. This exists specifically because a real bug (2026-08-20) showed
REM two dashboard processes can end up bound to the same port simultaneously on
REM Windows, causing requests to route unpredictably between old and new code -
REM this check prevents that from ever happening via the startup mechanism.

netstat -ano | findstr :5151 | findstr LISTENING >nul
if %errorlevel%==0 (
    exit /b 0
)

powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath 'C:\Users\jaxon\AppData\Local\Programs\Python\Python310\pythonw.exe' -ArgumentList 'dashboard\server.py' -WorkingDirectory 'C:\Users\jaxon\OneDrive\Desktop\Github\figaro' -WindowStyle Hidden"
