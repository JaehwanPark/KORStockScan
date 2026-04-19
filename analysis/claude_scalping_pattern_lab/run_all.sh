#!/usr/bin/env bash
# run_all.sh — 데이터 준비 → 분석 → payload 생성 일괄 실행
# 실행 위치: KORStockScan 프로젝트 루트 또는 analysis/claude_scalping_pattern_lab/
# 사용법: bash analysis/claude_scalping_pattern_lab/run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] .venv/bin/python not found at $PROJECT_ROOT/.venv"
    echo "        프로젝트 루트에서 실행하거나 .venv를 먼저 구성하세요."
    exit 1
fi

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

START_TS=$(date +%s)
echo "================================================"
echo " KORStockScan Scalping Pattern Lab"
echo " 실행 시각: $(date '+%Y-%m-%d %H:%M:%S')"
echo " 프로젝트 루트: $PROJECT_ROOT"
echo "================================================"
echo ""

# ── Step 1: 데이터 준비 ──────────────────────────────────────────────────────
echo "[Step 1/3] prepare_dataset.py"
"$PYTHON" "$SCRIPT_DIR/prepare_dataset.py"
echo ""

# ── Step 2: EV 패턴 분석 ─────────────────────────────────────────────────────
echo "[Step 2/3] analyze_ev_patterns.py"
"$PYTHON" "$SCRIPT_DIR/analyze_ev_patterns.py"
echo ""

# ── Step 3: Claude payload 빌드 ──────────────────────────────────────────────
echo "[Step 3/3] build_claude_payload.py"
"$PYTHON" "$SCRIPT_DIR/build_claude_payload.py"
echo ""

# ── 산출물 목록 ──────────────────────────────────────────────────────────────
END_TS=$(date +%s)
ELAPSED=$(( END_TS - START_TS ))

echo "================================================"
echo " 완료 — 소요: ${ELAPSED}초"
echo " 산출물 위치: $SCRIPT_DIR/outputs/"
echo "================================================"
echo ""
ls -lh "$SCRIPT_DIR/outputs/" 2>/dev/null || echo "(outputs 디렉토리 없음)"
