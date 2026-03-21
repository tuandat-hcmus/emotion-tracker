@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker CLI was not found on PATH.
  echo Install Docker Desktop and make sure the "docker" command is available in PowerShell or Command Prompt.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop does not appear to be running.
  echo Start Docker Desktop, wait for it to finish starting, then run this file again.
  pause
  exit /b 1
)

echo Starting Emotion backend and PostgreSQL with Docker Compose...
docker compose up --build
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
  echo.
  echo docker compose exited with code %exit_code%.
  pause
)

exit /b %exit_code%
