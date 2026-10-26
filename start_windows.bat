@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo First run: follow the Python setup commands in README.md.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
pause
