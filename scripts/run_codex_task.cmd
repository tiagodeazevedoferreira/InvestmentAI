@echo off
setlocal
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

if "%~1"=="" (
  echo Uso: scripts\run_codex_task.cmd docs\codex\tasks\001-runner-smoke-test.md
  exit /b 2
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\run_codex_task.ps1" -TaskFile "%~1"
exit /b %ERRORLEVEL%
