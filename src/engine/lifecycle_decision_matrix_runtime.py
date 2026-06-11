"""Runtime resolver for lifecycle decision matrix policies."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES


MATRIX_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
MATRIX_FILE_RE = re.compile(r"lifecycle_decision_matrix_(\d{4}-\d{2}-\d{2})\.json$")
PANIC_SELL_DEFENSE_DIR = DATA_DIR / "report" / "panic_sell_defense"
PANIC_BUYING_DIR = DATA_DIR / "report" / "panic_buying"
MARKET_PANIC_BREADTH_DIR = DATA_DIR / "report" / "market_panic_breadth"

_PROMOTE_COUNTER: dict[str, int] = {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _session_cutoff_source_date(now: datetime) -> date:
    if now.hour >= 16:
        return now.date()
    return now.date() - timedelta(days=1)


def _latest_matrix_path_on_or_before(target_date: date) -> Path | None:
    explicit = str(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_POLICY_FILE", "") or "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
    best_date: date | None = None
    best_path: Path | None = None
    if not MATRIX_DIR.exists():
        return None
    for path in MATRIX_DIR.glob("lifecycle_decision_matrix_*.json"):
        match = MATRIX_FILE_RE.match(path.name)
        if not match:
            continue
        try:
            current_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if current_date > target_date:
            continue
        if best_date is None or current_date > best_date:
            best_date = current_date
            best_path = path
    return best_path


def _read_payload(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _payload_target_date(payload: dict[str, Any]) -> date | None:
    for key in ("target_date", "date", "trading_date"):
        value = payload.get(key)
        if not value:
            continue
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            continue
    generated_at = _parse_datetime(payload.get("generated_at") or payload.get("as_of"))
    return generated_at.date() if generated_at else None


def _freshness_status(payload: dict[str, Any], *, target_date: date, now: datetime, max_age_sec: int) -> tuple[bool, str]:
    payload_date = _payload_target_date(payload)
    if payload_date != target_date:
        return False, "wrong_target_date"
    generated_at = _parse_datetime(payload.get("generated_at") or payload.get("as_of"))
    if generated_at is None:
        return False, "missing_generated_at"
    if generated_at.tzinfo is not None and now.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=None)
    elif generated_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    age_sec = (now - generated_at).total_seconds()
    if age_sec < -60:
        return False, "future_generated_at"
    if age_sec > float(max_age_sec):
        return False, "stale"
    return True, "ok"


def _panic_report_path(target_date: date) -> Path:
    return PANIC_SELL_DEFENSE_DIR / f"panic_sell_defense_{target_date.isoformat()}.json"


def _panic_buying_report_path(target_date: date) -> Path:
    return PANIC_BUYING_DIR / f"panic_buying_{target_date.isoformat()}.json"


def _breadth_report_path(target_date: date) -> Path:
    return MARKET_PANIC_BREADTH_DIR / f"market_panic_breadth_{target_date.isoformat()}.json"


def _panic_epoch_id(target_date: date, panic_state: str, regime: str, level: int, generated_at: Any) -> str:
    generated = _parse_datetime(generated_at)
    if generated is None:
        bucket = "unknown"
    else:
        minute = (generated.minute // 5) * 5
        bucket = f"{generated.hour:02d}{minute:02d}"
    return f"{target_date.isoformat()}|{panic_state or 'UNKNOWN'}|{regime or 'UNKNOWN'}|L{level}|{bucket}"


def _euphoria_epoch_id(target_date: date, panic_buy_state: str, regime: str, level: int, generated_at: Any) -> str:
    generated = _parse_datetime(generated_at)
    if generated is None:
        bucket = "unknown"
    else:
        minute = (generated.minute // 2) * 2
        bucket = f"{generated.hour:02d}{minute:02d}"
    return f"{target_date.isoformat()}|{panic_buy_state or 'UNKNOWN'}|{regime or 'UNKNOWN'}|E{level}|{bucket}"


def _resolve_panic_level(panic_payload: dict[str, Any], breadth_payload: dict[str, Any]) -> tuple[int, str]:
    micro = panic_payload.get("microstructure_market_context")
    if not isinstance(micro, dict):
        micro = {}
    detector = panic_payload.get("microstructure_detector")
    if not isinstance(detector, dict):
        detector = {}
    panic_metrics = panic_payload.get("panic_metrics")
    if not isinstance(panic_metrics, dict):
        panic_metrics = {}
    panic_state = str(panic_payload.get("panic_state") or "").upper()
    regime = str(panic_payload.get("panic_regime_mode") or "").upper()
    market_state = str(micro.get("market_risk_state") or "").upper()
    liquidity_state = str(micro.get("liquidity_state") or panic_payload.get("liquidity_state") or "").upper()
    breadth_risk_off = bool(
        micro.get("market_panic_breadth_risk_off_advisory")
        or breadth_payload.get("risk_off_advisory")
    )
    single_market_risk_off = bool(
        micro.get("market_panic_breadth_single_market_risk_off_advisory")
        or breadth_payload.get("single_market_risk_off_advisory")
    )
    confirmed_micro = bool(micro.get("confirmed_micro_risk_off_advisory"))
    micro_risk_off_count = _safe_int(micro.get("risk_off_advisory_count"), 0)
    detector_risk_off_count = _safe_int(detector.get("risk_off_advisory_count"), 0)
    detector_panic_signal_count = _safe_int(detector.get("panic_signal_count"), 0)
    current_stop_loss_count = _safe_int(panic_metrics.get("current_30m_stop_loss_exit_count"), 0)
    strict_micro_confirmed = (
        confirmed_micro
        or micro_risk_off_count > 0
        or detector_risk_off_count > 0
        or detector_panic_signal_count > 0
    )
    hard_stop_cluster = current_stop_loss_count >= 3
    if liquidity_state in {"BROKEN", "LIQUIDITY_BROKEN", "THIN_BROKEN"}:
        return 3, "liquidity_broken"
    if panic_state == "PANIC_SELL" and (strict_micro_confirmed or hard_stop_cluster):
        return 2, "confirmed_panic_sell"
    if strict_micro_confirmed and (breadth_risk_off or single_market_risk_off or market_state == "RISK_OFF"):
        return 2, "confirmed_risk_off"
    if breadth_risk_off or single_market_risk_off or market_state == "RISK_OFF" or regime == "STABILIZING":
        return 1, "breadth_risk_off_watch"
    if panic_state == "PANIC_SELL":
        return 1, "panic_sell_unconfirmed_watch"
    return 0, "normal"


def resolve_panic_risk_regime_context(
    *,
    now: datetime | None = None,
    target_date: date | None = None,
    max_age_sec: int | None = None,
) -> dict[str, Any]:
    """Resolve same-day panic reports into lifecycle risk-regime context.

    Non-OK freshness statuses deliberately return level 0 so stale or partial
    reports cannot mutate sim state.
    """
    current_dt = now or datetime.now()
    resolved_date = target_date or current_dt.date()
    age_limit = int(
        max_age_sec
        if max_age_sec is not None
        else getattr(TRADING_RULES, "SCALP_SIM_PANIC_CONTEXT_MAX_AGE_SEC", 600) or 600
    )
    panic_path = _panic_report_path(resolved_date)
    breadth_path = _breadth_report_path(resolved_date)
    source_files = {
        "panic_sell_defense": str(panic_path),
        "market_panic_breadth": str(breadth_path),
    }
    status = "OK"
    warnings: list[str] = []
    if not panic_path.exists() or not breadth_path.exists():
        status = "MISSING" if not panic_path.exists() and not breadth_path.exists() else "PARTIAL"
        warnings.append("missing_source_file")
    panic_payload = _read_payload(panic_path)
    breadth_payload = _read_payload(breadth_path)
    if status != "MISSING":
        if panic_path.exists() and not panic_payload:
            status = "PARSE_ERROR"
            warnings.append("panic_sell_defense_parse_error")
        if breadth_path.exists() and not breadth_payload:
            status = "PARSE_ERROR" if status == "OK" else status
            warnings.append("market_panic_breadth_parse_error")
    if status == "OK":
        for label, payload in (("panic_sell_defense", panic_payload), ("market_panic_breadth", breadth_payload)):
            fresh, reason = _freshness_status(payload, target_date=resolved_date, now=current_dt, max_age_sec=age_limit)
            if not fresh:
                status = "STALE"
                warnings.append(f"{label}:{reason}")
                break
    if status != "OK":
        return {
            "panic_context_status": status,
            "panic_level": 0,
            "panic_level_reason": "context_not_ok",
            "panic_epoch_id": _panic_epoch_id(resolved_date, "NORMAL", "NORMAL", 0, None),
            "market_risk_state": "UNKNOWN",
            "breadth_risk_off": False,
            "single_market_risk_off": False,
            "confirmed_risk_off": False,
            "liquidity_state": "UNKNOWN",
            "risk_off_components": {},
            "panic_source_files": source_files,
            "decision_confidence": 0.0,
            "warnings": warnings,
        }
    micro = panic_payload.get("microstructure_market_context")
    if not isinstance(micro, dict):
        micro = {}
    detector = panic_payload.get("microstructure_detector")
    if not isinstance(detector, dict):
        detector = {}
    panic_metrics = panic_payload.get("panic_metrics")
    if not isinstance(panic_metrics, dict):
        panic_metrics = {}
    level, reason = _resolve_panic_level(panic_payload, breadth_payload)
    panic_state = str(panic_payload.get("panic_state") or "NORMAL")
    regime = str(panic_payload.get("panic_regime_mode") or "NORMAL")
    liquidity_state = str(micro.get("liquidity_state") or panic_payload.get("liquidity_state") or "NORMAL")
    breadth_risk_off = bool(
        micro.get("market_panic_breadth_risk_off_advisory")
        or breadth_payload.get("risk_off_advisory")
    )
    single_market_risk_off = bool(
        micro.get("market_panic_breadth_single_market_risk_off_advisory")
        or breadth_payload.get("single_market_risk_off_advisory")
    )
    confirmed = bool(micro.get("confirmed_risk_off_advisory"))
    components = {
        "breadth_risk_off": breadth_risk_off,
        "single_market_risk_off": single_market_risk_off,
        "confirmed_risk_off": confirmed,
        "confirmed_micro_risk_off": bool(micro.get("confirmed_micro_risk_off_advisory")),
        "market_confirms_risk_off": bool(micro.get("market_confirms_risk_off")),
        "breadth_confirms_risk_off": bool(micro.get("breadth_confirms_risk_off")),
        "micro_risk_off_count": _safe_int(micro.get("risk_off_advisory_count"), 0),
        "detector_risk_off_count": _safe_int(detector.get("risk_off_advisory_count"), 0),
        "detector_panic_signal_count": _safe_int(detector.get("panic_signal_count"), 0),
        "current_30m_stop_loss_exit_count": _safe_int(
            panic_metrics.get("current_30m_stop_loss_exit_count"), 0
        ),
    }
    return {
        "panic_context_status": "OK",
        "panic_level": level,
        "panic_level_reason": reason,
        "panic_epoch_id": _panic_epoch_id(
            resolved_date,
            panic_state,
            regime,
            level,
            panic_payload.get("generated_at") or panic_payload.get("as_of"),
        ),
        "market_risk_state": str(micro.get("market_risk_state") or "UNKNOWN"),
        "breadth_risk_off": breadth_risk_off,
        "single_market_risk_off": single_market_risk_off,
        "confirmed_risk_off": confirmed,
        "liquidity_state": liquidity_state,
        "risk_off_components": components,
        "panic_source_files": source_files,
        "decision_confidence": 1.0 if level >= 2 else 0.7 if level == 1 else 0.5,
        "panic_state": panic_state,
        "panic_regime_mode": regime,
        "generated_at": panic_payload.get("generated_at"),
        "as_of": panic_payload.get("as_of"),
        "warnings": warnings,
    }


def _resolve_euphoria_level(panic_buy_payload: dict[str, Any]) -> tuple[int, str, str]:
    mode = str(panic_buy_payload.get("panic_buy_regime_mode") or "NORMAL").upper()
    state = str(panic_buy_payload.get("panic_buy_state") or "NORMAL").upper()
    if mode in {"PANIC_BUY_EXHAUSTION", "COOLDOWN"} or state in {"BUYING_EXHAUSTED", "EXHAUSTION_WATCH"}:
        return 3, mode.lower(), "exhaustion_reversal"
    if mode == "PANIC_BUY_CONTINUATION" or state == "PANIC_BUY":
        return 2, "confirmed_panic_buying", "risk_on_euphoria"
    if mode == "PANIC_BUY_DETECTED" or state == "PANIC_BUY_WATCH":
        return 1, "momentum_risk_on", "risk_on_euphoria"
    return 0, "normal", "risk_on_euphoria"


def _euphoria_source_quality_blockers(panic_buy_payload: dict[str, Any]) -> list[str]:
    micro = panic_buy_payload.get("microstructure_detector")
    if not isinstance(micro, dict):
        micro = {}
    market = panic_buy_payload.get("market_breadth_context")
    if not isinstance(market, dict):
        market = {}
    blockers: list[str] = []
    signal_count = _safe_int(micro.get("panic_buy_signal_count"), 0)
    if signal_count > 0 and not bool(market.get("market_wide_panic_buy_confirmed")):
        blockers.append("panic_buy_local_unconfirmed_by_market_breadth")
    if _safe_int(micro.get("missing_orderbook_count"), 0) > 0:
        blockers.append("panic_buy_orderbook_collector_coverage_gap")
    if _safe_int(micro.get("missing_trade_aggressor_count"), 0) > 0:
        blockers.append("panic_buy_trade_aggressor_coverage_gap")
    return blockers


def resolve_euphoria_risk_context(
    *,
    now: datetime | None = None,
    target_date: date | None = None,
    max_age_sec: int | None = None,
) -> dict[str, Any]:
    """Resolve panic-buying reports into sim-only euphoria lifecycle context."""
    current_dt = now or datetime.now()
    resolved_date = target_date or current_dt.date()
    age_limit = int(
        max_age_sec
        if max_age_sec is not None
        else getattr(TRADING_RULES, "SCALP_SIM_EUPHORIA_CONTEXT_MAX_AGE_SEC", 180) or 180
    )
    report_path = _panic_buying_report_path(resolved_date)
    source_files = {"panic_buying": str(report_path)}
    warnings: list[str] = []
    status = "OK"
    if not report_path.exists():
        status = "MISSING"
        warnings.append("missing_source_file")
    payload = _read_payload(report_path)
    if status != "MISSING" and not payload:
        status = "PARSE_ERROR"
        warnings.append("panic_buying_parse_error")
    if status == "OK":
        fresh, reason = _freshness_status(payload, target_date=resolved_date, now=current_dt, max_age_sec=age_limit)
        if not fresh:
            status = "STALE"
            warnings.append(f"panic_buying:{reason}")
    level, reason, direction = _resolve_euphoria_level(payload) if payload else (0, "context_not_ok", "risk_on_euphoria")
    blockers = _euphoria_source_quality_blockers(payload) if status == "OK" else []
    source_quality_status = "OK" if not blockers else "BLOCKED"
    if status == "OK" and blockers:
        status = "SOURCE_QUALITY_BLOCKED"
        warnings.extend(blockers)
    state = str(payload.get("panic_buy_state") or "NORMAL") if payload else "NORMAL"
    mode = str(payload.get("panic_buy_regime_mode") or "NORMAL") if payload else "NORMAL"
    epoch_id = _euphoria_epoch_id(
        resolved_date,
        state,
        mode,
        level,
        payload.get("generated_at") or payload.get("as_of") if payload else None,
    )
    market = payload.get("market_breadth_context") if isinstance(payload.get("market_breadth_context"), dict) else {}
    micro = payload.get("microstructure_detector") if isinstance(payload.get("microstructure_detector"), dict) else {}
    return {
        "euphoria_context_status": status,
        "euphoria_risk_level": level,
        "euphoria_level_reason": reason if status == "OK" else "context_not_ok",
        "euphoria_risk_mode": mode,
        "euphoria_epoch_id": epoch_id,
        "euphoria_source_quality": source_quality_status,
        "source_quality_blockers": blockers,
        "risk_context_owner": "euphoria",
        "risk_direction": direction,
        "action_namespace": "euphoria_lifecycle",
        "panic_buy_state": state,
        "panic_buy_regime_mode": mode,
        "market_wide_panic_buy_confirmed": bool(market.get("market_wide_panic_buy_confirmed")),
        "market_breadth_risk_on_advisory": bool(market.get("market_panic_breadth_risk_on_advisory")),
        "panic_buy_signal_count": _safe_int(micro.get("panic_buy_signal_count"), 0),
        "missing_orderbook_count": _safe_int(micro.get("missing_orderbook_count"), 0),
        "missing_trade_aggressor_count": _safe_int(micro.get("missing_trade_aggressor_count"), 0),
        "euphoria_source_files": source_files,
        "decision_confidence": 1.0 if status == "OK" and level >= 2 else 0.7 if status == "OK" and level == 1 else 0.0,
        "generated_at": payload.get("generated_at") if payload else None,
        "as_of": payload.get("as_of") if payload else None,
        "warnings": warnings,
    }


def _policy_for_stage(payload: dict[str, Any], stage: str) -> dict[str, Any]:
    entries = payload.get("policy_entries") if isinstance(payload.get("policy_entries"), list) else []
    for entry in entries:
        if isinstance(entry, dict) and str(entry.get("stage") or "") == stage:
            return entry
    return {}


def _has_hard_safety_veto(context: dict[str, Any]) -> bool:
    for key in (
        "hard_safety_veto",
        "safety_veto",
        "broker_guard_block",
        "broker_submit_blocked",
        "stale_quote_submit_block",
        "price_freshness_block",
        "hard_stop",
        "protect_stop",
        "emergency_stop",
        "account_guard_block",
        "order_guard_block",
        "cooldown_guard_block",
        "qty_guard_block",
    ):
        if bool(context.get(key)):
            return True
    reason = str(context.get("blocked_reason") or context.get("source_quality_block_reason") or "").lower()
    return any(token in reason for token in ("hard_stop", "emergency", "broker", "receipt_missing"))


def _counter_key(now: datetime) -> str:
    version = str(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION", "") or "-")
    return f"{now.date().isoformat()}|{version}"


def reset_lifecycle_decision_matrix_promote_counter() -> None:
    _PROMOTE_COUNTER.clear()


def resolve_lifecycle_decision(
    *,
    stage: str,
    original_action: str,
    context: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_dt = now or datetime.now()
    stage_name = str(stage or "").strip().lower()
    original = str(original_action or "").upper()
    ctx = dict(context or {})
    enabled = bool(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_ENABLED", False))
    runtime_effect_enabled = bool(
        getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED", True)
    )
    min_confidence = float(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE", 0.0) or 0.0)
    result = {
        "lifecycle_matrix_enabled": enabled,
        "lifecycle_matrix_runtime_effect_enabled": runtime_effect_enabled,
        "lifecycle_matrix_stage": stage_name or "-",
        "lifecycle_matrix_policy_version": "-",
        "lifecycle_matrix_policy_file": "-",
        "lifecycle_matrix_policy_key": "-",
        "lifecycle_matrix_confidence": 0.0,
        "lifecycle_matrix_selected_action": "NO_CHANGE",
        "lifecycle_matrix_original_action": original or "-",
        "lifecycle_matrix_runtime_effect": "none",
        "lifecycle_matrix_runtime_reason": "disabled",
        "lifecycle_matrix_fixed_threshold_role": "baseline_prior",
        "lifecycle_matrix_safety_passthrough": False,
        "lifecycle_matrix_promote_counter": 0,
        "risk_regime_context": ctx.get("risk_regime_context") if isinstance(ctx.get("risk_regime_context"), dict) else {},
    }
    if not result["risk_regime_context"]:
        result["risk_regime_context"] = resolve_panic_risk_regime_context(now=current_dt)
    if not enabled:
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_not_applicable_matrix_disabled"
        return result
    matrix_path = _latest_matrix_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_payload(matrix_path)
    if not payload:
        result["lifecycle_matrix_runtime_reason"] = "policy_missing"
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_not_applicable_matrix_missing"
        return result
    result["lifecycle_matrix_policy_version"] = str(payload.get("matrix_version") or "-")
    result["lifecycle_matrix_policy_file"] = str(matrix_path or "-")
    if _has_hard_safety_veto(ctx):
        result.update(
            {
                "lifecycle_matrix_runtime_reason": "hard_safety_passthrough",
                "lifecycle_matrix_fixed_threshold_role": "hard_safety",
                "lifecycle_matrix_safety_passthrough": True,
            }
        )
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_not_applicable_hard_safety_passthrough"
        return result
    policy = _policy_for_stage(payload, stage_name)
    if not policy:
        result["lifecycle_matrix_runtime_reason"] = "stage_policy_missing"
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_not_applicable_matrix_missing"
        return result
    confidence = _safe_float(policy.get("confidence"), 0.0)
    selected_action = str(policy.get("selected_action") or "NO_CHANGE").upper()
    result.update(
        {
            "lifecycle_matrix_policy_key": str(policy.get("policy_key") or "-"),
            "lifecycle_matrix_confidence": confidence,
            "lifecycle_matrix_selected_action": selected_action,
            "lifecycle_matrix_fixed_threshold_role": "bounded_tunable"
            if str(policy.get("source_quality_gate") or "") == "pass"
            else "baseline_prior",
        }
    )
    if confidence < min_confidence:
        result["lifecycle_matrix_runtime_reason"] = "confidence_below_min_stage_confidence"
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
        return result
    if selected_action == "NO_CHANGE":
        result["lifecycle_matrix_runtime_reason"] = "policy_no_change"
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
        return result
    if not runtime_effect_enabled:
        result["lifecycle_matrix_runtime_reason"] = "runtime_effect_disabled_context_only"
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
        return result
    if stage_name == "entry":
        if selected_action == "BUY_DEFENSIVE" and original not in {"BUY", "BUY_NOW", "BUY_DEFENSIVE"}:
            if not bool(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED", False)):
                result["lifecycle_matrix_runtime_reason"] = "promote_disabled"
                result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
                return result
            if not bool(policy.get("promote_ready")):
                result["lifecycle_matrix_runtime_reason"] = "promote_not_ready"
                result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
                return result
            key = _counter_key(current_dt)
            current_count = int(_PROMOTE_COUNTER.get(key, 0))
            cap = int(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY", 3) or 3)
            if current_count >= cap:
                result["lifecycle_matrix_runtime_reason"] = "promote_cap_exhausted"
                result["lifecycle_matrix_promote_counter"] = current_count
                result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
                return result
            _PROMOTE_COUNTER[key] = current_count + 1
            result.update(
                {
                    "lifecycle_matrix_runtime_effect": "promote_buy_defensive",
                    "lifecycle_matrix_runtime_reason": "bounded_promote_buy_defensive",
                    "lifecycle_matrix_promote_counter": _PROMOTE_COUNTER[key],
                }
            )
            result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
            return result
        if original in {"BUY", "BUY_NOW", "BUY_DEFENSIVE"} and selected_action in {"WAIT_REQUOTE", "DROP"}:
            result.update(
                {
                    "lifecycle_matrix_runtime_effect": "demote_wait"
                    if selected_action == "WAIT_REQUOTE"
                    else "demote_drop",
                    "lifecycle_matrix_runtime_reason": "bounded_entry_demote",
                }
            )
            result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
            return result
    if stage_name in {"holding", "exit"} and selected_action in {"HOLD", "EXIT"}:
        if selected_action != original:
            result.update(
                {
                    "lifecycle_matrix_runtime_effect": "force_hold"
                    if selected_action == "HOLD"
                    else "force_exit",
                    "lifecycle_matrix_runtime_reason": "bounded_holding_exit_bias",
                }
            )
            result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
            return result
    if stage_name == "submit" and selected_action == "ALLOW_SUBMIT":
        result.update(
            {
                "lifecycle_matrix_runtime_effect": "allow_submit_observe",
                "lifecycle_matrix_runtime_reason": "bounded_submit_allow",
            }
        )
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
        return result
    if stage_name == "scale_in" and selected_action in {"AVG_DOWN_BIAS", "PYRAMID_BIAS"}:
        result.update(
            {
                "lifecycle_matrix_runtime_effect": selected_action.lower(),
                "lifecycle_matrix_runtime_reason": "bounded_scale_in_bias",
            }
        )
        result["lifecycle_matrix_policy_key_gap_classification"] = "policy_key_provided"
        return result
    result["lifecycle_matrix_runtime_reason"] = "policy_action_not_applicable"
    result["lifecycle_matrix_policy_key_gap_classification"] = _classify_policy_key_gap(result, ctx)
    return result


def _classify_policy_key_gap(result: dict[str, Any], ctx: dict[str, Any]) -> str:
    policy_key = str(result.get("lifecycle_matrix_policy_key") or "-")
    if policy_key != "-":
        return "policy_key_provided"
    if result.get("lifecycle_matrix_safety_passthrough"):
        return "policy_key_not_applicable_hard_safety_passthrough"
    if not result.get("lifecycle_matrix_enabled"):
        return "policy_key_not_applicable_matrix_disabled"
    reason = str(result.get("lifecycle_matrix_runtime_reason") or "")
    if reason in ("policy_missing", "stage_policy_missing", "disabled"):
        return "policy_key_not_applicable_matrix_missing"
    ctx_actual_order = _truthy(ctx.get("actual_order_submitted"))
    ctx_broker_forbidden = _truthy(ctx.get("broker_order_forbidden"))
    ctx_sim = ctx.get("simulation_book") or ctx.get("simulation_owner") or False
    ctx_probe = ctx.get("probe_id") or ctx.get("probe_origin_stage") or False
    ctx_virtual = _truthy(ctx.get("simulated_order")) or _truthy(ctx.get("virtual_pending"))
    if (
        ctx_sim
        or ctx_probe
        or ctx_virtual
        or (ctx_broker_forbidden and not ctx_actual_order)
    ):
        return "policy_key_not_required_context_row"
    if not result.get("lifecycle_matrix_runtime_effect_enabled"):
        return "policy_key_not_required_effect_disabled"
    stage = str(result.get("lifecycle_matrix_stage") or "")
    if stage not in ("entry", "submit", "holding", "scale_in", "exit"):
        return "policy_key_not_required_non_actionable_stage"
    return "policy_key_required_missing"


def apply_lifecycle_decision_to_payload(payload: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload or {})
    selected = str(decision.get("lifecycle_matrix_selected_action") or "").upper()
    effect = str(decision.get("lifecycle_matrix_runtime_effect") or "")
    if effect == "promote_buy_defensive":
        result["action"] = "BUY"
        result["action_v2"] = "BUY"
        result["lifecycle_matrix_buy_variant"] = "BUY_DEFENSIVE"
    elif effect == "demote_wait":
        result["action"] = "WAIT"
        if "action_v2" in result:
            result["action_v2"] = "WAIT"
    elif effect == "demote_drop":
        result["action"] = "DROP"
        if "action_v2" in result:
            result["action_v2"] = "DROP"
    elif effect in {"force_hold", "force_exit"} and selected in {"HOLD", "EXIT"}:
        result["action"] = selected
        if "action_v2" in result:
            result["action_v2"] = selected
    result.update(decision)
    return result
