@echo off
REM ============================================================
REM  PolicyGPT - one-click local start (Windows)
REM  Backend  : http://localhost:8000  (API docs at /docs)
REM  Frontend : http://localhost:3000  (opens in Microsoft Edge)
REM  Both servers restart automatically if they ever stop.
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3.12 -m venv .venv || python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
)

start "PolicyGPT backend" cmd /k "%~dp0tools\run_backend.bat"
start "PolicyGPT frontend" cmd /k "%~dp0tools\run_frontend.bat"

echo Waiting for the website to start...
powershell -NoProfile -Command "$u='http://localhost:3000'; for($i=0;$i -lt 150;$i++){ try { Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 5 | Out-Null; break } catch { Start-Sleep 2 } }"
start "" msedge http://localhost:3000
