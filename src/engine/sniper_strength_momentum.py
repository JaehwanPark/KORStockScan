"""Dynamic strength momentum gate for scalping entry observation."""

from __future__ import annotations

import time

from src.utils.constants import TRADING_RULES


def _to_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except Exception:
        return default


def _to_int(value, default=0):
    try:
        return int(float(str(value).replace(",", "").replace("+", "").strip()))
    except Exception:
        return default


def _safe_positive_delta(end_value: int | float, start_value: int | float) -> int:
    try:
        return max(0, int(float(end_value) - float(start_value)))
    except Exception:
        return 0


def _normalized_tag_set(raw_tags) -> set[str]:
    return {
        str(tag).strip().upper()
        for tag in (raw_tags or ())
        if str(tag).strip()
    }


def _try_dynamic_strength_canary(
    *,
    result: dict,
    reason: str,
    profile_tag: str,
    threshold_profile: str,
    min_base: float,
    current_vpw: float,
    min_buy_value: int,
    window_buy_value: int,
    min_buy_ratio: float,
    buy_ratio: float,
    min_exec_buy_ratio: float,
    exec_buy_ratio: float,
) -> bool:
    if not bool(getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED", False)):
        return False

    allow_tags = _normalized_tag_set(getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_TAGS", ()))
    if allow_tags and str(profile_tag or "").upper() not in allow_tags:
        return False

    allowed_reasons = _normalized_tag_set(getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_ALLOWED_REASONS", ()))
    if allowed_reasons and str(reason or "").upper() not in allowed_reasons:
        return False

    min_buy_value_ratio = float(getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_MIN_BUY_VALUE_RATIO", 0.85) or 0.85)
    buy_ratio_tol = float(getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_BUY_RATIO_TOL", 0.03) or 0.03)
    exec_buy_ratio_tol = float(
        getattr(TRADING_RULES, "SCALP_DYNAMIC_STRENGTH_CANARY_EXEC_BUY_RATIO_TOL", 0.03) or 0.03
    )
    min_base_floor = max(min_base - 1.5, 0.0)

    reason_key = str(reason or "").strip().lower()
    passed = False
    if reason_key == "below_exec_buy_ratio":
        passed = (
            exec_buy_ratio >= (min_exec_buy_ratio - exec_buy_ratio_tol)
            and buy_ratio >= (min_buy_ratio - buy_ratio_tol)
            and window_buy_value >= int(min_buy_value * min_buy_value_ratio)
            and current_vpw >= min_base_floor
        )
    elif reason_key == "below_buy_ratio":
        passed = (
            buy_ratio >= (min_buy_ratio - buy_ratio_tol)
            and exec_buy_ratio >= (min_exec_buy_ratio - exec_buy_ratio_tol)
            and window_buy_value >= int(min_buy_value * min_buy_value_ratio)
            and current_vpw >= min_base_floor
        )
    elif reason_key == "below_window_buy_value":
        passed = (
            window_buy_value >= int(min_buy_value * min_buy_value_ratio)
            and buy_ratio >= (min_buy_ratio - buy_ratio_tol)
            and exec_buy_ratio >= (min_exec_buy_ratio - exec_buy_ratio_tol)
            and current_vpw >= min_base_floor
        )
    if not passed:
        return False

    result["allowed"] = True
    result["canary_applied"] = True
    result["canary_origin_reason"] = reason_key
    result["canary_reason"] = "dynamic_strength_canary"
    result["reason"] = f"canary_relaxed_{reason_key}"
    result["threshold_profile"] = f"{threshold_profile}+canary"
    return True


def evaluate_scalping_strength_momentum(ws_data: dict, *, now_ts: float | None = None) -> dict:
    ws_data = ws_data or {}
    window_sec = int(getattr(TRADING_RULES, "SCALP_VPW_WINDOW_SECONDS", 5) or 5)
    min_base = float(getattr(TRADING_RULES, "SCALP_VPW_MIN_BASE", 95.0) or 95.0)
    raw_target_delta = getattr(TRADING_RULES, "SCALP_VPW_TARGET_DELTA", 10.0)
    target_delta = float(10.0 if raw_target_delta is None else raw_target_delta)
    min_buy_value = int(getattr(TRADING_RULES, "SCALP_VPW_MIN_BUY_VALUE", 20_000) or 20_000)
    min_buy_ratio = float(getattr(TRADING_RULES, "SCALP_VPW_MIN_BUY_RATIO", 0.60) or 0.60)
    min_exec_buy_ratio = float(getattr(TRADING_RULES, "SCALP_VPW_MIN_EXEC_BUY_RATIO", 0.56) or 0.56)
    min_net_buy_qty = int(getattr(TRADING_RULES, "SCALP_VPW_MIN_NET_BUY_QTY", 1) or 1)
    strong_absolute = float(getattr(TRADING_RULES, "SCALP_VPW_STRONG_ABSOLUTE", 115.0) or 115.0)
    strong_buy_value = int(getattr(TRADING_RULES, "SCALP_VPW_STRONG_BUY_VALUE", 40_000) or 40_000)
    profile_tag = str(ws_data.get("position_tag") or ws_data.get("_position_tag") or "").strip().upper()
    relaxed_tags = {
        str(tag).strip().upper()
        for tag in (getattr(TRADING_RULES, "SCALP_VPW_RELAX_TAGS", ()) or ())
        if str(tag).strip()
    }
    if profile_tag and profile_tag in relaxed_tags:
        min_base = float(getattr(TRADING_RULES, "SCALP_VPW_RELAX_MIN_BASE", min_base) or min_base)
        min_buy_value = int(getattr(TRADING_RULES, "SCALP_VPW_RELAX_MIN_BUY_VALUE", min_buy_value) or min_buy_value)
        min_buy_ratio = float(getattr(TRADING_RULES, "SCALP_VPW_RELAX_MIN_BUY_RATIO", min_buy_ratio) or min_buy_ratio)
        min_exec_buy_ratio = float(
            getattr(TRADING_RULES, "SCALP_VPW_RELAX_MIN_EXEC_BUY_RATIO", min_exec_buy_ratio) or min_exec_buy_ratio
        )
        threshold_profile = "relaxed"
    else:
        threshold_profile = "default"

    result = {
        "enabled": bool(getattr(TRADING_RULES, "SCALP_DYNAMIC_VPW_ENABLED", True)),
        "allowed": False,
        "reason": "disabled",
        "position_tag": profile_tag or "-",
        "threshold_profile": threshold_profile,
        "window_sec": window_sec,
        "elapsed_sec": 0.0,
        "base_vpw": 0.0,
        "current_vpw": _to_float(ws_data.get("v_pw"), 0.0),
        "vpw_delta": 0.0,
        "slope_per_sec": 0.0,
        "window_total_value": 0,
        "window_buy_value": 0,
        "window_sell_value": 0,
        "window_buy_ratio": 0.0,
        "window_buy_qty": 0,
        "window_sell_qty": 0,
        "window_net_buy_qty": 0,
        "window_exec_buy_ratio": 0.0,
        "window_avg_buy_ratio": 0.0,
        "market_session_state": str(ws_data.get("market_session_state", "") or ""),
        "canary_applied": False,
        "canary_reason": "",
        "canary_origin_reason": "",
    }

    if not result["enabled"]:
        return result

    history = ws_data.get("strength_momentum_history") or []
    if not history:
        result["reason"] = "insufficient_history"
        return result

    normalized = []
    for item in history:
        if not isinstance(item, dict):
            continue
        ts = _to_float(item.get("ts"), 0.0)
        if ts <= 0:
            continue
        normalized.append({
            "ts": ts,
            "v_pw": _to_float(item.get("v_pw"), 0.0),
            "tick_value": abs(_to_int(item.get("tick_value"), 0)),
            "buy_tick_value": abs(_to_int(item.get("buy_tick_value"), 0)),
            "sell_tick_value": abs(_to_int(item.get("sell_tick_value"), 0)),
            "buy_qty": abs(_to_int(item.get("buy_qty"), 0)),
            "sell_qty": abs(_to_int(item.get("sell_qty"), 0)),
            "buy_exec_qty_cum": abs(_to_int(item.get("buy_exec_qty_cum", item.get("buy_qty")), 0)),
            "sell_exec_qty_cum": abs(_to_int(item.get("sell_exec_qty_cum", item.get("sell_qty")), 0)),
            "buy_ratio": _to_float(item.get("buy_ratio"), 0.0),
        })

    if not normalized:
        result["reason"] = "insufficient_history"
        return result

    normalized.sort(key=lambda item: item["ts"])
    current_ts = float(now_ts if now_ts is not None else normalized[-1]["ts"] or time.time())
    window_start_ts = current_ts - window_sec

    base_sample = None
    for item in normalized:
        if item["ts"] <= window_start_ts:
            base_sample = item
        else:
            break
    if base_sample is None:
        base_sample = normalized[0]

    elapsed_sec = max(0.0, current_ts - float(base_sample["ts"]))
    result["elapsed_sec"] = round(elapsed_sec, 3)
    result["base_vpw"] = float(base_sample["v_pw"])

    if elapsed_sec < max(1.0, window_sec * 0.6):
        result["reason"] = "insufficient_history"
        return result

    window_samples = [item for item in normalized if item["ts"] >= base_sample["ts"]]
    window_total_value = sum(item["tick_value"] for item in window_samples)
    window_buy_value = sum(item["buy_tick_value"] for item in window_samples)
    window_sell_value = sum(item["sell_tick_value"] for item in window_samples)
    end_sample = window_samples[-1]
    base_buy_qty_cum = int(base_sample.get("buy_exec_qty_cum", 0) or 0)
    base_sell_qty_cum = int(base_sample.get("sell_exec_qty_cum", 0) or 0)
    end_buy_qty_cum = int(end_sample.get("buy_exec_qty_cum", 0) or 0)
    end_sell_qty_cum = int(end_sample.get("sell_exec_qty_cum", 0) or 0)
    window_buy_qty = _safe_positive_delta(end_buy_qty_cum, base_buy_qty_cum)
    window_sell_qty = _safe_positive_delta(end_sell_qty_cum, base_sell_qty_cum)
    window_net_buy_qty = window_buy_qty - window_sell_qty
    buy_ratio = (window_buy_value / window_total_value) if window_total_value > 0 else 0.0
    exec_total_qty = window_buy_qty + window_sell_qty
    exec_buy_ratio = (window_buy_qty / exec_total_qty) if exec_total_qty > 0 else 0.0
    avg_buy_ratio = (
        sum(item["buy_ratio"] for item in window_samples) / len(window_samples)
        if window_samples else 0.0
    )

    current_vpw = result["current_vpw"]
    vpw_delta = current_vpw - result["base_vpw"]
    slope_per_sec = (vpw_delta / elapsed_sec) if elapsed_sec > 0 else 0.0

    result["vpw_delta"] = round(vpw_delta, 3)
    result["slope_per_sec"] = round(slope_per_sec, 3)
    result["window_total_value"] = int(window_total_value)
    result["window_buy_value"] = int(window_buy_value)
    result["window_sell_value"] = int(window_sell_value)
    result["window_buy_ratio"] = round(buy_ratio, 4)
    result["window_buy_qty"] = int(window_buy_qty)
    result["window_sell_qty"] = int(window_sell_qty)
    result["window_net_buy_qty"] = int(window_net_buy_qty)
    result["window_exec_buy_ratio"] = round(exec_buy_ratio, 4)
    result["window_avg_buy_ratio"] = round(avg_buy_ratio, 2)

    if current_vpw < min_base:
        result["reason"] = "below_strength_base"
        return result
    if window_buy_value < min_buy_value:
        result["reason"] = "below_window_buy_value"
        if _try_dynamic_strength_canary(
            result=result,
            reason=result["reason"],
            profile_tag=profile_tag,
            threshold_profile=threshold_profile,
            min_base=min_base,
            current_vpw=current_vpw,
            min_buy_value=min_buy_value,
            window_buy_value=window_buy_value,
            min_buy_ratio=min_buy_ratio,
            buy_ratio=buy_ratio,
            min_exec_buy_ratio=min_exec_buy_ratio,
            exec_buy_ratio=exec_buy_ratio,
        ):
            return result
        return result
    if buy_ratio < min_buy_ratio:
        result["reason"] = "below_buy_ratio"
        if _try_dynamic_strength_canary(
            result=result,
            reason=result["reason"],
            profile_tag=profile_tag,
            threshold_profile=threshold_profile,
            min_base=min_base,
            current_vpw=current_vpw,
            min_buy_value=min_buy_value,
            window_buy_value=window_buy_value,
            min_buy_ratio=min_buy_ratio,
            buy_ratio=buy_ratio,
            min_exec_buy_ratio=min_exec_buy_ratio,
            exec_buy_ratio=exec_buy_ratio,
        ):
            return result
        return result
    if exec_buy_ratio < min_exec_buy_ratio:
        result["reason"] = "below_exec_buy_ratio"
        if _try_dynamic_strength_canary(
            result=result,
            reason=result["reason"],
            profile_tag=profile_tag,
            threshold_profile=threshold_profile,
            min_base=min_base,
            current_vpw=current_vpw,
            min_buy_value=min_buy_value,
            window_buy_value=window_buy_value,
            min_buy_ratio=min_buy_ratio,
            buy_ratio=buy_ratio,
            min_exec_buy_ratio=min_exec_buy_ratio,
            exec_buy_ratio=exec_buy_ratio,
        ):
            return result
        return result
    if window_net_buy_qty < min_net_buy_qty:
        result["reason"] = "below_net_buy_qty"
        return result
    if current_vpw >= strong_absolute and window_buy_value >= min_buy_value and exec_buy_ratio >= min_exec_buy_ratio:
        result["allowed"] = True
        result["reason"] = "strong_absolute_override"
        return result
    if window_buy_value >= strong_buy_value and buy_ratio >= min_buy_ratio and window_net_buy_qty > 0:
        result["allowed"] = True
        result["reason"] = "buy_value_override"
        return result

    result["allowed"] = True
    result["reason"] = "momentum_ok"
    return result
