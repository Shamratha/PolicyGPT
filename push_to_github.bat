@echo off
REM Pushes this project to https://github.com/Shamratha/PolicyGPT
REM The old project currently on that repo's main branch is first saved to a branch called "old-version".
cd /d "%~dp0"
set REPO=https://github.com/Shamratha/PolicyGPT.git

where git >nul 2>nul || (echo Git is not installed. Install it from https://git-scm.com and run this again. & pause & exit /b 1)

echo.
echo This will:
echo   1. save the current main branch of %REPO% as branch "old-version"
echo   2. replace main with this PolicyGPT project
echo.
choice /M "Continue"
if errorlevel 2 exit /b 0

git remote get-url mine >nul 2>nul || git remote add mine %REPO%
echo.
echo [1/4] Downloading the current GitHub version (a sign-in window may open)...
git fetch mine || (echo Could not reach GitHub. Check your internet and GitHub sign-in. & pause & exit /b 1)

echo [2/4] Backing up the old project to branch "old-version"...
git ls-remote --exit-code --heads mine old-version >nul 2>nul
if errorlevel 1 (
  git push mine refs/remotes/mine/main:refs/heads/old-version || (echo Backup failed - nothing was changed. & pause & exit /b 1)
) else (
  echo     old-version already exists - keeping it.
)

echo [3/4] Saving your changes...
git rm -r --cached --ignore-unmatch -q PolicyGPT >nul 2>nul
git add -A
git commit -m "PolicyGPT: fixes, validation, tests, light redesign, add-scheme feature, 21 schemes, deployment config" || echo     (nothing new to commit)

echo [4/4] Uploading to GitHub...
git push mine HEAD:main --force || (echo Upload failed. & pause & exit /b 1)

echo.
echo Done! Your code is on https://github.com/Shamratha/PolicyGPT
echo Next: follow DEPLOY.md (Render for the backend, Vercel for the website).
pause
