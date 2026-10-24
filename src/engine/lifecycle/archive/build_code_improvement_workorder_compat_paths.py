"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]


REPORT_DIR = PROJECT_ROOT / "data" / "report"


SWING_IMPROVEMENT_AUTOMATION_DIR = REPORT_DIR / "swing_improvement_automation"


SWING_PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "swing_pattern_lab_automation"


SWING_STRATEGY_DISCOVERY_EV_DIR = REPORT_DIR / "swing_strategy_discovery_ev"


SWING_LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "swing_lifecycle_decision_matrix"


SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR = REPORT_DIR / "swing_lifecycle_bucket_discovery"


PATTERN_LAB_AI_REVIEW_DIR = REPORT_DIR / "pattern_lab_ai_review"


THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"


LIFECYCLE_DECISION_MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"


PATTERN_LAB_CURRENTNESS_AUDIT_DIR = REPORT_DIR / "pattern_lab_currentness_audit"


BUY_FUNNEL_SENTINEL_DIR = REPORT_DIR / "buy_funnel_sentinel"


ENTRY_HURDLE_BACKTEST_DIR = REPORT_DIR / "entry_hurdle_backtest"


PRODUCER_GAP_DISCOVERY_DIR = REPORT_DIR / "producer_gap_discovery"


STAGE_HOOK_WORKORDER_DISCOVERY_DIR = REPORT_DIR / "stage_hook_workorder_discovery"


STAGE_HOOK_RUNTIME_SCAFFOLD_DIR = REPORT_DIR / "stage_hook_runtime_scaffold"


CONVERSION_LANE_DIR = REPORT_DIR / "conversion_lane"


INTRADAY_ENTRY_BLOCKER_DIAGNOSTICS_DIR = (
    REPORT_DIR / "intraday_entry_blocker_diagnostics"
)


INTRADAY_WS_FRESHNESS_MONITOR_DIR = REPORT_DIR / "intraday_ws_freshness_monitor"


RISING_MISSED_CLASSIFIER_PRIOR_DIR = REPORT_DIR / "rising_missed_classifier_prior"


MICROSTRUCTURE_REACTION_CONTEXT_DIR = REPORT_DIR / "microstructure_reaction_context"


CODE_IMPROVEMENT_WORKORDER_DIR = PROJECT_ROOT / "docs" / "code-improvement-workorders"


CODE_IMPROVEMENT_WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"


def conversion_lane_report_path(target_date: str) -> Path:
    return CONVERSION_LANE_DIR / f"conversion_lane_{target_date}.json"


def intraday_entry_blocker_diagnostics_report_path(target_date: str) -> Path:
    return (
        INTRADAY_ENTRY_BLOCKER_DIAGNOSTICS_DIR
        / f"intraday_entry_blocker_diagnostics_{target_date}.json"
    )


def intraday_ws_freshness_monitor_report_path(target_date: str) -> Path:
    return (
        INTRADAY_WS_FRESHNESS_MONITOR_DIR
        / f"intraday_ws_freshness_monitor_{target_date}.json"
    )


def entry_hurdle_backtest_report_path(target_date: str) -> Path:
    return ENTRY_HURDLE_BACKTEST_DIR / f"entry_hurdle_backtest_{target_date}.json"


def rising_missed_classifier_prior_report_path(target_date: str) -> Path:
    return (
        RISING_MISSED_CLASSIFIER_PRIOR_DIR
        / f"rising_missed_classifier_prior_{target_date}.json"
    )


def microstructure_reaction_context_report_path(target_date: str) -> Path:
    return (
        MICROSTRUCTURE_REACTION_CONTEXT_DIR
        / f"microstructure_reaction_context_{target_date}.json"
    )


def swing_automation_report_path(target_date: str) -> Path:
    return (
        SWING_IMPROVEMENT_AUTOMATION_DIR
        / f"swing_improvement_automation_{target_date}.json"
    )


def swing_pattern_lab_automation_report_path(target_date: str) -> Path:
    return (
        SWING_PATTERN_LAB_AUTOMATION_DIR
        / f"swing_pattern_lab_automation_{target_date}.json"
    )


def threshold_ev_report_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_EV_DIR / f"threshold_cycle_ev_{target_date}.json"


def lifecycle_decision_matrix_report_path(target_date: str) -> Path:
    return (
        LIFECYCLE_DECISION_MATRIX_DIR / f"lifecycle_decision_matrix_{target_date}.json"
    )


def swing_strategy_discovery_ev_report_path(target_date: str) -> Path:
    return (
        SWING_STRATEGY_DISCOVERY_EV_DIR
        / f"swing_strategy_discovery_ev_{target_date}.json"
    )


def swing_lifecycle_decision_matrix_report_path(target_date: str) -> Path:
    return (
        SWING_LIFECYCLE_DECISION_MATRIX_DIR
        / f"swing_lifecycle_decision_matrix_{target_date}.json"
    )


def swing_lifecycle_bucket_discovery_report_path(target_date: str) -> Path:
    return (
        SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR
        / f"swing_lifecycle_bucket_discovery_{target_date}.json"
    )


def code_improvement_workorder_paths(target_date: str) -> tuple[Path, Path]:
    base = f"code_improvement_workorder_{target_date}"
    return (
        CODE_IMPROVEMENT_WORKORDER_REPORT_DIR / f"{base}.json",
        CODE_IMPROVEMENT_WORKORDER_DIR / f"{base}.md",
    )


def pattern_lab_currentness_audit_report_path(target_date: str) -> Path:
    return (
        PATTERN_LAB_CURRENTNESS_AUDIT_DIR
        / f"pattern_lab_currentness_audit_{target_date}.json"
    )


def pattern_lab_ai_review_report_path(target_date: str) -> Path:
    return PATTERN_LAB_AI_REVIEW_DIR / f"pattern_lab_ai_review_{target_date}.json"


def buy_funnel_sentinel_report_path(target_date: str) -> Path:
    return BUY_FUNNEL_SENTINEL_DIR / f"buy_funnel_sentinel_{target_date}.json"


def producer_gap_discovery_report_path(target_date: str) -> Path:
    return PRODUCER_GAP_DISCOVERY_DIR / f"producer_gap_discovery_{target_date}.json"


def stage_hook_workorder_discovery_report_path(target_date: str) -> Path:
    return (
        STAGE_HOOK_WORKORDER_DISCOVERY_DIR
        / f"stage_hook_workorder_discovery_{target_date}.json"
    )


def stage_hook_runtime_scaffold_report_path(target_date: str) -> Path:
    return (
        STAGE_HOOK_RUNTIME_SCAFFOLD_DIR
        / f"stage_hook_runtime_scaffold_{target_date}.json"
    )
