"""
분석 설정 — 경로, 기간, 서버, 샘플링 옵션.
운영 코드와 완전히 분리된 독립 설정 모듈.
"""
from pathlib import Path
from datetime import date

# ── 프로젝트 루트 ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── 분석 기간 ──────────────────────────────────────────────────────────────────
ANALYSIS_START = date(2026, 4, 1)
ANALYSIS_END   = date(2026, 4, 17)

# ── 입력 경로 ──────────────────────────────────────────────────────────────────
SNAPSHOT_DIR       = PROJECT_ROOT / "data" / "report" / "monitor_snapshots"
PIPELINE_EVENT_DIR = PROJECT_ROOT / "data" / "pipeline_events"

# 원격 스냅샷 (fetch_remote_scalping_logs로 수집된 경로)
REMOTE_SNAPSHOT_DIR = PROJECT_ROOT / "tmp"

# ── 출력 경로 ──────────────────────────────────────────────────────────────────
LAB_DIR    = Path(__file__).resolve().parent
OUTPUT_DIR = LAB_DIR / "outputs"

# ── 서버 레이블 ────────────────────────────────────────────────────────────────
SERVER_LOCAL  = "local"
SERVER_REMOTE = "remote"

# ── 코호트 분류 기준 ───────────────────────────────────────────────────────────
# position_rebased_after_fill 이벤트 수가 이 값 이상이면 split-entry로 분류
SPLIT_ENTRY_REBASE_THRESHOLD = 2

# ── 퍼널 blocker 키 매핑 ──────────────────────────────────────────────────────
FUNNEL_METRIC_MAP = {
    "latency_block_events":     "latency_block_events",
    "liquidity_block_events":   "liquidity_block_events",   # 없으면 0
    "ai_threshold_block_events":"ai_overlap_blocked_events",
    "overbought_block_events":  "ai_overlap_overbought_blocked_events",
    "submitted_events":         "order_bundle_submitted_events",
    "budget_pass_events":       "budget_pass_events",
}

# ── EV 패턴 분석 옵션 ──────────────────────────────────────────────────────────
TOP_N_PATTERNS = 5
MIN_VALID_PROFIT_SAMPLES = 30   # 서버별 최소 표본 — 이 미만이면 "표본 부족" 명시

# ── pipeline_events 스트리밍 옵션 ─────────────────────────────────────────────
# sequence_fact 수집 대상 stage 화이트리스트
SEQUENCE_STAGES = {
    "holding_started",
    "position_rebased_after_fill",
    "exit_signal",
    "sell_completed",
    "sell_order_failed",
}

# ── 손익 판단 기준 ─────────────────────────────────────────────────────────────
PROFIT_THRESHOLD  =  0.0   # profit_rate > 0 → 수익
LOSS_THRESHOLD    =  0.0   # profit_rate <= 0 → 손실
SOFT_STOP_RULES   = {"scalp_soft_stop_pct", "scalp_hard_stop_pct",
                     "scalp_preset_hard_stop_pct", "scalp_open_reclaim_never_green"}
TRAILING_TP_RULES = {"scalp_trailing_take_profit", "scalp_preset_protect_profit",
                     "protect_trailing_stop"}
