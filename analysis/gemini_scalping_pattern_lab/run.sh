#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] .venv/bin/python not found at $PROJECT_ROOT/.venv"
    exit 1
fi

cd "$SCRIPT_DIR"
export PYTHONPATH="$PROJECT_ROOT"

echo "=== Gemini Scalping Pattern Lab ==="
echo "1. Building Datasets..."
"$PYTHON" build_dataset.py

echo "2. Analyzing Patterns..."
"$PYTHON" analyze_patterns.py

echo "3. Building LLM Payload..."
"$PYTHON" build_llm_payload.py

echo "4. Generating Final Reports..."
"$PYTHON" generate_final_report.py

echo "=== Done. Check 'outputs/' directory. ==="
