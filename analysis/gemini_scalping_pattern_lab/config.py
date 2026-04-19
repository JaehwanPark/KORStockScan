import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TMP_DIR = PROJECT_ROOT / "tmp"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_DIR = BASE_DIR / "prompt_templates"

# Analysis Parameters
START_DATE = "2026-04-01"
END_DATE = "2026-04-17"
MIN_VALID_SAMPLES = 30

# Data sources
LOCAL_REPORT_DIR = DATA_DIR / "report"
LOCAL_POST_SELL_EVAL_DIR = DATA_DIR / "post_sell"
LOCAL_PIPELINE_DIR = DATA_DIR / "pipeline_events"
REMOTE_BASE_DIR = TMP_DIR

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
