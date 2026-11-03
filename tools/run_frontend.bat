@echo off
REM Runs the PolicyGPT website and restarts it automatically if it ever stops unexpectedly.
title PolicyGPT frontend
cd /d "%~dp0..\frontend"
set NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
if not exist node_modules\.bin\next.cmd (
  echo Installing frontend packages - the first run takes 2-5 minutes...
  call npm install
)
:loop
echo [%date% %time%] Starting PolicyGPT website on http://localhost:3000 ...
call npm run dev
echo.
echo [%date% %time%] Website stopped (exit code %errorlevel%). Restarting in 5 seconds - close this window to stop it.
timeout /t 5 /nobreak >nul
goto loop
