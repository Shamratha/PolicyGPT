@echo off
REM Resets PolicyGPT's local database to fresh demo data.
REM Removes every user, profile, survey, application and any scheme you added yourself.
cd /d "%~dp0backend"
echo.
echo This deletes ALL local PolicyGPT data (users, surveys, applications, added schemes)
echo and recreates the original demo data the next time the backend starts.
echo.
echo First CLOSE the "PolicyGPT backend" window, otherwise Windows keeps the files locked.
echo.
choice /M "Reset the database now"
if errorlevel 2 goto :eof
if exist policygpt.db del /q policygpt.db
if exist chroma_db rmdir /s /q chroma_db
if exist policygpt.db (
  echo Could not delete policygpt.db - is the backend still running? Close it and try again.
) else (
  echo Done. Start the app again with start_policygpt.bat to load fresh demo data.
)
pause
