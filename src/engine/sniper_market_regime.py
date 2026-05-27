"""Market regime utilities for the sniper engine."""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error


MARKET_REGIME = None


def _format_market_regime_block_reason(snap) -> str:
    debug = getattr(snap, "debug", {}) or {}
    component_scores = debug.get("component_scores", {}) or {}
    threshold = int(debug.get("legacy_recovery_gate_threshold", debug.get("score_threshold", 70)) or 70)
    legacy_score = int(getattr(snap, "swing_entry_recovery_gate_score", getattr(snap, "swing_score", 0)) or 0)
    deficit = max(0, threshold - legacy_score)
    continuous_label = str(getattr(snap, "market_regime_continuous_label", "") or "UNKNOWN")
    continuous_score = float(getattr(snap, "market_regime_continuous_score", 0.0) or 0.0)
    risk_context = "confirmed" if debug.get("confirmed_risk_block") else "not_confirmed"
    reason_prefix = "시장환경 confirmed risk" if risk_context == "confirmed" else "시장환경 prior"

    missing_signals = []
    if component_scores.get("vix", 0) <= 0:
        missing_signals.append(
            f"VIX미충족(vix_extreme={snap.vix_extreme}, two_day_down={snap.vix_two_day_down}, peak_passed={snap.vix_peak_passed})"
        )
    if component_scores.get("oil", 0) <= 0:
        missing_signals.append(
            f"원유미충족(oil_reversal={snap.oil_reversal}, wti_dead_cross={snap.wti_dead_cross}, from_high={snap.wti_from_recent_high_pct:.2f}%)"
        )
    if component_scores.get("fng", 0) == 0:
        missing_signals.append(
            f"FNG중립(fng={snap.fng_value:.2f}, prev={snap.fng_prev:.2f}, recovery={snap.fng_recovery}, extreme_fear={snap.fng_extreme_fear})"
        )

    reasons = ",".join(snap.reasons) if snap.reasons else "없음"
    missing = " / ".join(missing_signals) if missing_signals else "없음"
    return (
        f"{reason_prefix} | "
        f"risk={snap.risk_state}, "
        f"legacy_recovery_gate_score={legacy_score}/{threshold}, "
        f"continuous_label={continuous_label}, "
        f"continuous_score={continuous_score:.4f}, "
        f"risk_context={risk_context}, "
        f"deficit={deficit}, "
        f"components=vix:{component_scores.get('vix', 0)},oil:{component_scores.get('oil', 0)},fng:{component_scores.get('fng', 0)},local_breadth:{component_scores.get('local_breadth', 0)}, "
        f"VIX={snap.vix_close:.2f}, "
        f"WTI_RSI={snap.wti_rsi:.2f}, "
        f"oil_reversal={snap.oil_reversal}, "
        f"FNG={snap.fng_value:.2f}, "
        f"fng_recovery={snap.fng_recovery}, "
        f"reasons={reasons}, "
        f"missing={missing}"
    )


def _json_payload(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _truthy_flag(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _load_confirmed_risk_context() -> dict:
    target_date = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    panic = _json_payload(DATA_DIR / "report" / "panic_sell_defense" / f"panic_sell_defense_{target_date}.json")
    breadth = _json_payload(DATA_DIR / "report" / "market_panic_breadth" / f"market_panic_breadth_{target_date}.json")
    panic_metrics = panic.get("panic_metrics") if isinstance(panic.get("panic_metrics"), dict) else {}
    micro_context = (
        panic.get("microstructure_market_context")
        if isinstance(panic.get("microstructure_market_context"), dict)
        else {}
    )
    panic_breadth = breadth.get("panic_breadth") if isinstance(breadth.get("panic_breadth"), dict) else {}

    panic_state = str(panic.get("panic_state") or "NORMAL").upper()
    confirmed_risk_off = bool(
        _truthy_flag(panic_metrics.get("confirmed_risk_off_advisory"))
        or _truthy_flag(micro_context.get("confirmed_risk_off_advisory"))
        or _truthy_flag(micro_context.get("confirmed_micro_risk_off_advisory"))
    )
    broad_risk_off = bool(
        _truthy_flag(panic_breadth.get("risk_off_advisory"))
        or _truthy_flag(micro_context.get("market_panic_breadth_risk_off_advisory"))
    )
    single_market_risk_off = bool(
        _truthy_flag(panic_breadth.get("single_market_risk_off_advisory"))
        or _truthy_flag(micro_context.get("market_panic_breadth_single_market_risk_off_advisory"))
    )

    return {
        "panic_state": panic_state,
        "confirmed_risk_off_advisory": confirmed_risk_off,
        "risk_off_advisory": broad_risk_off,
        "single_market_risk_off_advisory": single_market_risk_off,
        "confirmed_risk_block": panic_state != "NORMAL" or confirmed_risk_off or broad_risk_off,
    }


def bind_market_regime_dependencies(*, market_regime=None):
    global MARKET_REGIME
    if market_regime is not None:
        MARKET_REGIME = market_regime

def init_market_regime_service():
    global MARKET_REGIME
    try:
        snap = MARKET_REGIME.refresh_if_needed(force=True)
        print(
            f"🌍 [시장환경 초기화] "
            f"risk={snap.risk_state}, "
            f"VIX={snap.vix_close:.2f}, "
            f"WTI_RSI={snap.wti_rsi:.2f}, "
            f"allow_swing={snap.allow_swing_entry}, "
            f"vol_mode={snap.volatility_mode}"
        )
    except Exception as e:
        log_error(f"🚨 시장환경 초기화 실패: {e}")

def should_block_swing_entry_by_market_regime(strategy: str):
    """
    스윙 전략(KOSPI_ML / KOSDAQ_ML / MAIN)에만 적용되는
    시장환경 필터. 스캘핑 전략에는 적용하지 않는다.
    """
    global MARKET_REGIME

    try:
        snap = MARKET_REGIME.refresh_if_needed()
        normalized = str(strategy or "").upper()

        # 스윙 전략만 적용
        if normalized not in ["KOSPI_ML", "KOSDAQ_ML", "MAIN"]:
            return False, ""

        sensitivity = str(os.getenv("KORSTOCKSCAN_SWING_MARKET_REGIME_SENSITIVITY", "") or "").strip().lower()
        dry_run_enabled = bool(getattr(TRADING_RULES, "SWING_LIVE_ORDER_DRY_RUN_ENABLED", True))
        risk_context = _load_confirmed_risk_context()
        debug = getattr(snap, "debug", {}) or {}
        component_scores = debug.get("component_scores", {}) or {}
        legacy_score = int(getattr(snap, "swing_entry_recovery_gate_score", getattr(snap, "swing_score", 0)) or 0)
        legacy_threshold = int(debug.get("legacy_recovery_gate_threshold", debug.get("score_threshold", 70)) or 70)
        oil_only_prior = bool(
            getattr(snap, "oil_only_recovery_prior", False)
            or (
                int(component_scores.get("oil", 0) or 0) > 0
                and int(component_scores.get("vix", 0) or 0) == 0
                and int(component_scores.get("fng", 0) or 0) == 0
                and int(component_scores.get("local_breadth", 0) or 0) == 0
            )
        )
        base_meta = {
            **risk_context,
            "market_regime": getattr(snap, "risk_state", ""),
            "allow_swing_entry": bool(getattr(snap, "allow_swing_entry", False)),
            "swing_score": int(getattr(snap, "swing_score", 0) or 0),
            "legacy_recovery_gate_score": legacy_score,
            "legacy_recovery_gate_threshold": legacy_threshold,
            "recovery_gate_state": getattr(snap, "recovery_gate_state", debug.get("legacy_recovery_gate_label", "")),
            "swing_recovery_gate_label": getattr(snap, "swing_recovery_gate_label", debug.get("legacy_recovery_gate_label", "")),
            "recovery_gate_reason": getattr(snap, "recovery_gate_reason", debug.get("legacy_recovery_gate_reason", "")),
            "oil_only_recovery_prior": oil_only_prior,
            "market_regime_continuous_score": float(getattr(snap, "market_regime_continuous_score", 0.0) or 0.0),
            "market_regime_continuous_label": getattr(snap, "market_regime_continuous_label", ""),
            "market_regime_source_quality": getattr(snap, "market_regime_source_quality", ""),
            "risk_context": "confirmed" if risk_context.get("confirmed_risk_block") else "not_confirmed",
            "market_regime_prior_observed": False,
        }

        if risk_context.get("confirmed_risk_block"):
            snap.debug["confirmed_risk_block"] = True
            return True, _format_market_regime_block_reason(snap), {
                **base_meta,
                "market_regime_block_reason": "confirmed_risk_context",
            }

        if not snap.allow_swing_entry and sensitivity == "relaxed_entry_observe" and dry_run_enabled:
            return False, "시장환경 dry-run approval relaxed_entry_observe", {
                **base_meta,
                "market_regime_prior_observed": True,
                "market_regime_prior_reason": "relaxed_entry_observe",
            }

        if not snap.allow_swing_entry:
            if risk_context.get("single_market_risk_off_advisory"):
                prior_reason = "single_market_risk_off_advisory"
            elif oil_only_prior:
                prior_reason = "oil_only_recovery_signal_insufficient"
            else:
                prior_reason = "recovery_gate_signal_insufficient"
            return False, _format_market_regime_block_reason(snap), {
                **base_meta,
                "market_regime_prior_observed": True,
                "market_regime_prior_reason": prior_reason,
            }

        return False, "", base_meta

    except Exception as e:
        # 시장환경 서비스 장애가 주문엔진 장애가 되면 안 됨
        return False, f"시장환경 조회 실패(보수적 미차단): {e}", {
            "market_regime_prior_observed": False,
            "confirmed_risk_block": False,
        }
