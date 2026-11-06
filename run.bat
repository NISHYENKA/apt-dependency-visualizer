@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m src.apt_graph.main %*
) else (
    python -m src.apt_graph.main %*
)
exit /b %errorlevel%
