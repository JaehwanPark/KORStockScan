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

_PROMOTE_COUNTER: dict[str, int] = {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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
    min_confidence = float(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE", 0.0) or 0.0)
    result = {
        "lifecycle_matrix_enabled": enabled,
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
    }
    if not enabled:
        return result
    matrix_path = _latest_matrix_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_payload(matrix_path)
    if not payload:
        result["lifecycle_matrix_runtime_reason"] = "policy_missing"
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
        return result
    policy = _policy_for_stage(payload, stage_name)
    if not policy:
        result["lifecycle_matrix_runtime_reason"] = "stage_policy_missing"
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
        return result
    if selected_action == "NO_CHANGE":
        result["lifecycle_matrix_runtime_reason"] = "policy_no_change"
        return result
    if stage_name == "entry":
        if selected_action == "BUY_DEFENSIVE" and original not in {"BUY", "BUY_NOW", "BUY_DEFENSIVE"}:
            if not bool(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED", False)):
                result["lifecycle_matrix_runtime_reason"] = "promote_disabled"
                return result
            if not bool(policy.get("promote_ready")):
                result["lifecycle_matrix_runtime_reason"] = "promote_not_ready"
                return result
            key = _counter_key(current_dt)
            current_count = int(_PROMOTE_COUNTER.get(key, 0))
            cap = int(getattr(TRADING_RULES, "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY", 3) or 3)
            if current_count >= cap:
                result["lifecycle_matrix_runtime_reason"] = "promote_cap_exhausted"
                result["lifecycle_matrix_promote_counter"] = current_count
                return result
            _PROMOTE_COUNTER[key] = current_count + 1
            result.update(
                {
                    "lifecycle_matrix_runtime_effect": "promote_buy_defensive",
                    "lifecycle_matrix_runtime_reason": "bounded_promote_buy_defensive",
                    "lifecycle_matrix_promote_counter": _PROMOTE_COUNTER[key],
                }
            )
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
            return result
    if stage_name == "submit" and selected_action == "ALLOW_SUBMIT":
        result.update(
            {
                "lifecycle_matrix_runtime_effect": "allow_submit_observe",
                "lifecycle_matrix_runtime_reason": "bounded_submit_allow",
            }
        )
        return result
    if stage_name == "scale_in" and selected_action in {"AVG_DOWN_BIAS", "PYRAMID_BIAS"}:
        result.update(
            {
                "lifecycle_matrix_runtime_effect": selected_action.lower(),
                "lifecycle_matrix_runtime_reason": "bounded_scale_in_bias",
            }
        )
        return result
    result["lifecycle_matrix_runtime_reason"] = "policy_action_not_applicable"
    return result


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
