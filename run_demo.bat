@echo off
echo ===============================================================================
echo Cross-Team Incident Memory Agent for Payment Infrastructure
echo HackwithHyderabad 3.0 Entry Runner
echo ===============================================================================

echo [1/3] Checking environment configuration...
if not exist .env (
    echo [ERROR] .env file not found. Copy .env.example to .env and insert API keys.
    exit /b 1
)

echo [2/3] Running headless verification test suite (4/4 Scenarios)...
python test_scenarios.py
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Test suite reported failures.
)

echo [3/3] Launching Incident Command Center on http://localhost:8501...
python -m streamlit run app.py --server.port=8501
