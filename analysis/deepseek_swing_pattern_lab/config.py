import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
PROMPT_DIR = BASE_DIR / "prompts"

START_DATE = os.getenv("ANALYSIS_START_DATE", "2026-05-01").strip()
END_DATE = os.getenv("ANALYSIS_END_DATE", "2026-05-09").strip()
MIN_VALID_SAMPLES = 3

REPORT_DIR = DATA_DIR / "report"
SWING_LIFECYCLE_AUDIT_DIR = REPORT_DIR / "swing_lifecycle_audit"
SWING_SELECTION_FUNNEL_DIR = REPORT_DIR / "swing_selection_funnel"
SWING_IMPROVEMENT_AUTOMATION_DIR = REPORT_DIR / "swing_improvement_automation"
SWING_THRESHOLD_AI_REVIEW_DIR = REPORT_DIR / "swing_threshold_ai_review"
THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"
CODE_IMPROVEMENT_WORKORDER_DIR = REPORT_DIR / "code_improvement_workorder"
SWING_LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "swing_lifecycle_decision_matrix"
SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR = REPORT_DIR / "swing_lifecycle_bucket_discovery"
SWING_STRATEGY_DISCOVERY_EV_DIR = REPORT_DIR / "swing_strategy_discovery_ev"

RECO_PATH = DATA_DIR / "daily_recommendations_v2.csv"
RECO_DIAGNOSTIC_JSON_PATH = DATA_DIR / "daily_recommendations_v2_diagnostics.json"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"

POSTGRES_URL = os.getenv(
    "POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/korstockscan"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROMPT_DIR, exist_ok=True)
