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
    explicit = str(
        getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_POLICY_FILE", "") or ""
    ).strip()
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


def _freshness_status(
    payload: dict[str, Any], *, target_date: date, now: datetime, max_age_sec: int
) -> tuple[bool, str]:
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


def _breadth_report_path(target_date: date) -> Path:
    return (
        MARKET_PANIC_BREADTH_DIR
        / f"market_panic_breadth_{target_date.isoformat()}.json"
    )


def _panic_epoch_id(
    target_date: date, panic_state: str, regime: str, level: int, generated_at: Any
) -> str:
    generated = _parse_datetime(generated_at)
    if generated is None:
        bucket = "unknown"
    else:
        minute = (generated.minute // 5) * 5
        bucket = f"{generated.hour:02d}{minute:02d}"
    return f"{target_date.isoformat()}|{panic_state or 'UNKNOWN'}|{regime or 'UNKNOWN'}|L{level}|{bucket}"


def _resolve_panic_level(
    panic_payload: dict[str, Any], breadth_payload: dict[str, Any]
) -> tuple[int, str]:
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
    liquidity_state = str(
        micro.get("liquidity_state") or panic_payload.get("liquidity_state") or ""
    ).upper()
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
    current_stop_loss_count = _safe_int(
        panic_metrics.get("current_30m_stop_loss_exit_count"), 0
    )
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
    if strict_micro_confirmed and (
        breadth_risk_off or single_market_risk_off or market_state == "RISK_OFF"
    ):
        return 2, "confirmed_risk_off"
    if (
        breadth_risk_off
        or single_market_risk_off
        or market_state == "RISK_OFF"
        or regime == "STABILIZING"
    ):
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
        status = (
            "MISSING"
            if not panic_path.exists() and not breadth_path.exists()
            else "PARTIAL"
        )
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
        for label, payload in (
            ("panic_sell_defense", panic_payload),
            ("market_panic_breadth", breadth_payload),
        ):
            fresh, reason = _freshness_status(
                payload,
                target_date=resolved_date,
                now=current_dt,
                max_age_sec=age_limit,
            )
            if not fresh:
                status = "STALE"
                warnings.append(f"{label}:{reason}")
                break
    if status != "OK":
        return {
            "panic_context_status": status,
            "panic_level": 0,
            "panic_level_reason": "context_not_ok",
            "panic_epoch_id": _panic_epoch_id(
                resolved_date, "NORMAL", "NORMAL", 0, None
            ),
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
    liquidity_state = str(
        micro.get("liquidity_state") or panic_payload.get("liquidity_state") or "NORMAL"
    )
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
        "confirmed_micro_risk_off": bool(
            micro.get("confirmed_micro_risk_off_advisory")
        ),
        "market_confirms_risk_off": bool(micro.get("market_confirms_risk_off")),
        "breadth_confirms_risk_off": bool(micro.get("breadth_confirms_risk_off")),
        "micro_risk_off_count": _safe_int(micro.get("risk_off_advisory_count"), 0),
        "detector_risk_off_count": _safe_int(
            detector.get("risk_off_advisory_count"), 0
        ),
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


def _policy_for_stage(payload: dict[str, Any], stage: str) -> dict[str, Any]:
    entries = (
        payload.get("policy_entries")
        if isinstance(payload.get("policy_entries"), list)
        else []
    )
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
    reason = str(
        context.get("blocked_reason")
        or context.get("source_quality_block_reason")
        or ""
    ).lower()
    return any(
        token in reason
        for token in ("hard_stop", "emergency", "broker", "receipt_missing")
    )


def _counter_key(now: datetime) -> str:
    version = str(
        getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION", "") or "-"
    )
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
    return {
        "lifecycle_matrix_enabled": False,
        "lifecycle_matrix_runtime_effect_enabled": False,
        "lifecycle_matrix_stage": str(stage or "-"),
        "lifecycle_matrix_policy_version": "-",
        "lifecycle_matrix_policy_file": "-",
        "lifecycle_matrix_policy_key": "-",
        "lifecycle_matrix_confidence": 0.0,
        "lifecycle_matrix_selected_action": "NO_CHANGE",
        "lifecycle_matrix_original_action": str(original_action or "-"),
        "lifecycle_matrix_runtime_effect": "none",
        "lifecycle_matrix_runtime_reason": "retired",
        "lifecycle_matrix_fixed_threshold_role": "baseline_prior",
        "lifecycle_matrix_safety_passthrough": False,
        "lifecycle_matrix_promote_counter": 0,
        "lifecycle_matrix_policy_key_gap_classification": "policy_key_not_applicable_matrix_disabled",
        "risk_regime_context": (context or {}).get("risk_regime_context") or {},
    }


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
    ctx_virtual = _truthy(ctx.get("simulated_order")) or _truthy(
        ctx.get("virtual_pending")
    )
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


def apply_lifecycle_decision_to_payload(
    payload: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    result = dict(payload or {})
    result.update(
        resolve_lifecycle_decision(
            stage=str((decision or {}).get("lifecycle_matrix_stage") or ""),
            original_action=str(result.get("action_v2") or result.get("action") or ""),
        )
    )
    return result
