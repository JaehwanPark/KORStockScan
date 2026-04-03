"""Manual shadow feedback evaluation runner.

Usage:
    python3 src/tests/test_strength_shadow_feedback.py
    python3 src/tests/test_strength_shadow_feedback.py --date 2026-04-03
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.engine.sniper_strength_shadow_feedback import (
    evaluate_shadow_candidates,
    format_shadow_feedback_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate dynamic VPW shadow candidates.")
    parser.add_argument("--date", default=None, help="Target date in YYYY-MM-DD format")
    args = parser.parse_args()

    if args.date:
        target_date = args.date
    else:
        from datetime import datetime

        target_date = datetime.now().strftime("%Y-%m-%d")

    summary = evaluate_shadow_candidates(target_date=target_date)
    print(format_shadow_feedback_summary(summary))


if __name__ == "__main__":
    main()
