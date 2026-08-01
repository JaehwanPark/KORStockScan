#!/usr/bin/env bash
# run_all.sh — 데이터 준비 → 분석 → payload 생성 일괄 실행
# 실행 위치: KORStockScan 프로젝트 루트 또는 analysis/claude_scalping_pattern_lab/
# 사용법:
#   ANALYSIS_START_DATE=2026-06-05 ANALYSIS_END_DATE=2026-07-31 bash analysis/claude_scalping_pattern_lab/run_all.sh
#   bash analysis/claude_scalping_pattern_lab/run_all.sh 2026-07-31

set -euo pipefail

TARGET_DATE="${1:-${ANALYSIS_END_DATE:-}}"
if [[ -z "$TARGET_DATE" ]]; then
    echo "[ERROR] target date is required; pass YYYY-MM-DD or ANALYSIS_END_DATE" >&2
    exit 2
fi
if [[ ! "$TARGET_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "[ERROR] invalid target date: $TARGET_DATE" >&2
    exit 2
fi
export ANALYSIS_END_DATE="$TARGET_DATE"
export ANALYSIS_START_DATE="${ANALYSIS_START_DATE:-${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-05}}"

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
echo " 분석 기간: $ANALYSIS_START_DATE ~ $ANALYSIS_END_DATE"
echo "================================================"
echo ""

echo "[Health] analytics source check"
if ! "$PYTHON" - <<'PY'
from analysis.claude_scalping_pattern_lab import config
from src.engine.tuning_duckdb_repository import TuningDuckDBRepository

if not config.USE_DUCKDB_PRIMARY:
    print("[INFO] USE_DUCKDB_PRIMARY=false, jsonl-first mode")
    raise SystemExit(0)

with TuningDuckDBRepository(read_only=False) as repo:
    repo.register_parquet_dataset("pipeline_events")
    rows = repo.query("SELECT COUNT(*) AS cnt FROM v_pipeline_events").iloc[0]["cnt"]
print(f"[OK] duckdb/pipeline_events rows={int(rows)}")
PY
then
    echo "[WARN] DuckDB health check failed; prepare_dataset.py will continue with jsonl/db fallback."
fi
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
