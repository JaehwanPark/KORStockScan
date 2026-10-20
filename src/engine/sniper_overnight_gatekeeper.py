"""Permanent retirement boundary for the historical overnight entrypoint."""

from src.utils.constants import TRADING_RULES
from src.utils.logger import log_info


def _eod_label() -> str:
    raw = str(
        getattr(TRADING_RULES, "SCALPING_OVERNIGHT_DECISION_TIME", "15:10:00")
        or "15:10:00"
    )
    return raw[:5] if len(raw) >= 5 else "15:10"


def _overnight_gatekeeper_enabled() -> bool:
    # Permanently retired by scalping_overnight_retirement_20260906.  Keep the
    # compatibility module importable for historical tests and audit tooling,
    # but never let an environment/config override restore real-order authority.
    return False


def run_scalping_overnight_gatekeeper(ai_engine=None):
    """Retired compatibility entrypoint; it never evaluates or submits orders."""
    log_info(
        f"ℹ️ [{_eod_label()} EOD] 실 runtime 오버나이트 gatekeeper 비활성화: "
        "KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=false"
    )
    return False
