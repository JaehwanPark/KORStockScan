#!/bin/bash

# Exit on any error
set -e

# Navigate to script directory
cd "$(dirname "$0")"

echo "=== Gemini Scalping Pattern Lab ==="
echo "1. Building Datasets..."
python3 build_dataset.py

echo "2. Analyzing Patterns..."
python3 analyze_patterns.py

echo "3. Building LLM Payload..."
python3 build_llm_payload.py

echo "4. Generating Final Reports..."
python3 generate_final_report.py

echo "=== Done. Check 'outputs/' directory. ==="
