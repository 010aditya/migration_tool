# scripts/init.sh

#!/bin/bash

# Ensure virtual environment and dependencies are set
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up directories
mkdir -p logs/fix_history logs/build_logs output/fixed_codebase output/test_cases

# Run indexer
python -m agents.embedding_indexer

# Reminder
echo "✅ Environment initialized. You can now run:"
echo "   python scripts/run_all_agents.py --migrate-all"
