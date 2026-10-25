#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Virtual environment not detected. Initializing setup..."
    python -m venv venv
fi

source venv/bin/activate

echo "Verifying core dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Launching Mahlabahlasele Execution Engine..."
exec uvicorn main:app --host 127.0.0.1 --port 8000 --reload

