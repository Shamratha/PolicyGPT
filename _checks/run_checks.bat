@echo off
REM PolicyGPT automated checks - writes results into C:\policyGPT\_checks\
cd /d "%~dp0.."
set ROOT=%cd%
set OUT=%ROOT%\_checks
del /q "%OUT%\*.txt" 2>nul
echo started %date% %time% > "%OUT%\status.txt"

echo [1/4] Backend tests...
cd /d "%ROOT%\backend"
"%ROOT%\.venv\Scripts\python.exe" -m pytest tests -v -p no:cacheprovider > "%OUT%\backend_tests.txt" 2>&1
echo backend_tests_exit=%errorlevel% >> "%OUT%\status.txt"

cd /d "%ROOT%\frontend"
echo [1b] Applying safe security updates (npm audit fix, no --force)...
call npm audit fix > "%OUT%\npm_audit_fix.txt" 2>&1
call npm audit > "%OUT%\npm_audit.txt" 2>&1
echo npm_audit_exit=%errorlevel% >> "%OUT%\status.txt"
echo [2/4] TypeScript check...
call npx tsc --noEmit > "%OUT%\tsc.txt" 2>&1
echo tsc_exit=%errorlevel% >> "%OUT%\status.txt"

echo [3/4] Lint...
call npx eslint src > "%OUT%\eslint.txt" 2>&1
echo eslint_exit=%errorlevel% >> "%OUT%\status.txt"

echo [4/4] Production build...
call npm run build > "%OUT%\build.txt" 2>&1
echo build_exit=%errorlevel% >> "%OUT%\status.txt"

node --version > "%OUT%\versions.txt" 2>&1
"%ROOT%\.venv\Scripts\python.exe" --version >> "%OUT%\versions.txt" 2>&1
echo finished %date% %time% >> "%OUT%\status.txt"
echo DONE >> "%OUT%\status.txt"
echo All checks finished. This window will close.
timeout /t 5 >nul
