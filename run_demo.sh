#!/usr/bin/env bash
set -e

echo "==============================================================================="
echo "Cross-Team Incident Memory Agent for Payment Infrastructure"
echo "HackwithHyderabad 3.0 Entry Runner"
echo "==============================================================================="

if [ ! -f .env ]; then
    echo "[ERROR] .env file not found. Please copy .env.example to .env and configure your keys."
    exit 1
fi

echo "[1/3] Running headless verification test suite (4/4 Scenarios)..."
python test_scenarios.py

echo "[2/3] Launching Incident Command Center on http://localhost:8501..."
python -m streamlit run app.py --server.port=8501
