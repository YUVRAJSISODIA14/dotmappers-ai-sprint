@echo off
echo Starting the Support Ticket AI System...

start "API Server" cmd /k "call venv\Scripts\activate && uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

call venv\Scripts\activate && streamlit run app/ui.py