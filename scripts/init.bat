@echo off

REM scripts/init.bat

REM Set up virtual environment
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt

REM Create necessary directories
mkdir logs\fix_history
mkdir logs\build_logs
mkdir output\fixed_codebase
mkdir output\test_cases

REM Run embedding indexer
python -m agents.embedding_indexer

ECHO ✅ Environment initialized. You can now run:
ECHO    python scripts\run_all_agents.py --migrate-all
