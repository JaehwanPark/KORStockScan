"""Pure decision helper for rising-missed one-share SCALPING entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FORCED_ENTRY_REASON = "rising_missed_one_share_entry"
BLOCK_FEATURE_DISABLED = "feature_disabled"
BLOCK_NOT_CANDIDATE = "not_rising_missed_candidate"
BLOCK_CLASS_NOT_ELIGIBLE = "rising_missed_class_not_one_share_eligible"
BLOCK_OPEN_PENDING = "open_pending_entry_order"
BLOCK_ALREADY_HOLDING = "already_holding"
BLOCK_PRICE_ABOVE_CAP = "price_above_one_share_entry_cap"
MAX_ONE_SHARE_ENTRY_PRICE_KRW = 1_000_000
RISING_MISSED_CLASS_NOT_RISING = "not_rising_missed"
RISING_MISSED_CLASS_SUBMITTED_RESOLVED = "submitted_resolved"
RISING_MISSED_CLASS_RAW = "rising_missed_raw"
RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED = "source_quality_excluded"
RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED = "intended_guard_preserved"
RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE = "runtime_backpressure_observation"
RISING_MISSED_CLASS_STRATEGY_REJECT = "strategy_reject_missed"
RISING_MISSED_CLASS_ACTIONABLE_MAJOR = "actionable_major_missed"
RISING_MISSED_ONE_SHARE_ELIGIBLE_CLASSES = {
    RISING_MISSED_CLASS_RAW,
    RISING_MISSED_CLASS_ACTIONABLE_MAJOR,
}


@dataclass(frozen=True)
class RisingMissedOneShareDecision:
    allowed: bool
    reason: str
    forced_qty: int = 0
    positive_delta_pct: float = 0.0
    log_fields: dict[str, Any] | None = None


@dataclass(frozen=True)
class RisingMissedClassification:
    rising_missed: bool
    rising_missed_class: str
    one_share_eligible: bool
    reason: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return int(default)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip().upper()


def _field_present(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return bool(text) and text not in {"0", "false", "no", "n", "off", "none", "null", "-"}


def _positive_delta_pct(stock: dict[str, Any], explicit_delta_pct: Any = None) -> float:
    values = [
        explicit_delta_pct,
        stock.get("price_delta_since_first_seen_pct"),
        stock.get("scanner_positive_delta_pct"),
        stock.get("comparable_flu_delta_since_first_seen"),
        stock.get("max_price_delta_since_first_seen_pct"),
    ]
    return max(0.0, *(_safe_float(value, 0.0) for value in values))


def classify_rising_missed_candidate(
    *,
    max_delta_pct: Any,
    real_submit_count: Any = 0,
    min_delta_pct: float = 1.0,
    source_quality_excluded: bool = False,
    intended_guard_preserved: bool = False,
    runtime_backpressure_observation: bool = False,
    strategy_reject_missed: bool = False,
    actionable_major_missed: bool = False,
) -> RisingMissedClassification:
    delta = _safe_float(max_delta_pct, 0.0)
    submit_count = _safe_int(real_submit_count, 0)
    threshold = max(0.0, float(min_delta_pct))
    if delta < threshold:
        return RisingMissedClassification(
            rising_missed=False,
            rising_missed_class=RISING_MISSED_CLASS_NOT_RISING,
            one_share_eligible=False,
            reason="below_rising_missed_threshold",
        )
    if submit_count > 0:
        return RisingMissedClassification(
            rising_missed=False,
            rising_missed_class=RISING_MISSED_CLASS_SUBMITTED_RESOLVED,
            one_share_eligible=False,
            reason="real_submit_observed",
        )
    if source_quality_excluded:
        klass = RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED
        reason = "source_quality_excluded"
    elif intended_guard_preserved:
        klass = RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED
        reason = "intended_guard_preserved"
    elif runtime_backpressure_observation:
        klass = RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE
        reason = "runtime_backpressure_observation"
    elif strategy_reject_missed:
        klass = RISING_MISSED_CLASS_STRATEGY_REJECT
        reason = "strategy_reject_missed"
    elif actionable_major_missed:
        klass = RISING_MISSED_CLASS_ACTIONABLE_MAJOR
        reason = "actionable_major_missed"
    else:
        klass = RISING_MISSED_CLASS_RAW
        reason = "rising_missed_raw"
    return RisingMissedClassification(
        rising_missed=True,
        rising_missed_class=klass,
        one_share_eligible=klass in RISING_MISSED_ONE_SHARE_ELIGIBLE_CLASSES,
        reason=reason,
    )


def _looks_like_scanner_rising_missed_candidate(
    stock: dict[str, Any],
    *,
    strategy: str,
    position_tag: str,
    positive_delta_pct: float,
    min_delta_pct: float,
) -> bool:
    if _normalized_text(strategy) != "SCALPING":
        return False
    if _normalized_text(position_tag) != "SCANNER":
        return False
    if positive_delta_pct < max(0.0, float(min_delta_pct)):
        return False
    return bool(
        _field_present(stock.get("scanner_promotion_id"))
        or _field_present(stock.get("scanner_promotion_reason"))
        or _field_present(stock.get("entry_armed_at_epoch"))
        or _field_present(stock.get("_scanner_rising_entry_relief_reason"))
        or _field_present(stock.get("rising_missed_buy"))
        or _field_present(stock.get("rising_entry_relief_eligible"))
    )


def evaluate_rising_missed_one_share_entry(
    stock: dict[str, Any] | None,
    *,
    strategy: str,
    position_tag: str,
    feature_enabled: bool,
    has_open_pending: bool,
    already_holding: bool,
    positive_delta_pct: Any = None,
    min_delta_pct: float = 1.0,
    current_price: Any = None,
    max_entry_price_krw: int = MAX_ONE_SHARE_ENTRY_PRICE_KRW,
) -> RisingMissedOneShareDecision:
    stock = stock if isinstance(stock, dict) else {}
    delta_pct = _positive_delta_pct(stock, explicit_delta_pct=positive_delta_pct)
    entry_price = _safe_int(current_price, 0) or _safe_int(stock.get("target_buy_price"), 0) or _safe_int(
        stock.get("curr_price"), 0
    )
    price_cap = max(0, _safe_int(max_entry_price_krw, MAX_ONE_SHARE_ENTRY_PRICE_KRW))
    base_fields = {
        "rising_missed_one_share_entry_enabled": bool(feature_enabled),
        "rising_missed_one_share_entry_positive_delta_pct": f"{delta_pct:.4f}",
        "rising_missed_one_share_entry_min_delta_pct": f"{float(min_delta_pct):.4f}",
        "rising_missed_one_share_entry_strategy": _normalized_text(strategy) or "-",
        "rising_missed_one_share_entry_position_tag": _normalized_text(position_tag) or "-",
        "rising_missed_one_share_entry_forced_qty": 1,
        "rising_missed_one_share_entry_price": entry_price,
        "rising_missed_one_share_entry_price_cap_krw": price_cap,
    }
    classification = classify_rising_missed_candidate(
        max_delta_pct=delta_pct,
        real_submit_count=stock.get("real_submit_count") or stock.get("actual_order_submit_count") or 0,
        min_delta_pct=min_delta_pct,
        source_quality_excluded=stock.get("rising_missed_class") == RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
        intended_guard_preserved=stock.get("rising_missed_class") == RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED,
        runtime_backpressure_observation=stock.get("rising_missed_class") == RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE,
        strategy_reject_missed=stock.get("rising_missed_class") == RISING_MISSED_CLASS_STRATEGY_REJECT,
        actionable_major_missed=stock.get("rising_missed_class") == RISING_MISSED_CLASS_ACTIONABLE_MAJOR,
    )
    base_fields.update(
        {
            "rising_missed_class": classification.rising_missed_class,
            "rising_missed_class_reason": classification.reason,
            "rising_missed_one_share_eligible": classification.one_share_eligible,
        }
    )
    if not feature_enabled:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_FEATURE_DISABLED,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if (
        classification.rising_missed_class == RISING_MISSED_CLASS_SUBMITTED_RESOLVED
        or (classification.rising_missed and not classification.one_share_eligible)
    ):
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_CLASS_NOT_ELIGIBLE,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if not _looks_like_scanner_rising_missed_candidate(
        stock,
        strategy=strategy,
        position_tag=position_tag,
        positive_delta_pct=delta_pct,
        min_delta_pct=min_delta_pct,
    ):
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_NOT_CANDIDATE,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if has_open_pending:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_OPEN_PENDING,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if already_holding:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_ALREADY_HOLDING,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if price_cap > 0 and entry_price > price_cap:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_PRICE_ABOVE_CAP,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    return RisingMissedOneShareDecision(
        allowed=True,
        reason=FORCED_ENTRY_REASON,
        forced_qty=1,
        positive_delta_pct=delta_pct,
        log_fields=base_fields,
    )


def is_forced_rising_missed_one_share_entry(stock: dict[str, Any] | None, runtime: dict[str, Any] | None) -> bool:
    stock = stock if isinstance(stock, dict) else {}
    runtime = runtime if isinstance(runtime, dict) else {}
    return (
        bool(stock.get("rising_missed_one_share_entry_forced"))
        and _safe_int(stock.get("forced_entry_qty"), 0) == 1
        and str(stock.get("forced_entry_reason") or runtime.get("forced_entry_reason") or "").strip()
        == FORCED_ENTRY_REASON
    )


def collapse_to_one_share_order(planned_orders: list[dict[str, Any]] | None, *, fallback_price: int) -> list[dict[str, Any]]:
    base = dict((planned_orders or [{}])[0] or {})
    price = _safe_int(base.get("price"), 0) or _safe_int(fallback_price, 0)
    base.update(
        {
            "tag": FORCED_ENTRY_REASON,
            "qty": 1,
            "price": price,
            "tif": base.get("tif") or "DAY",
        }
    )
    base["rising_missed_one_share_entry_forced"] = True
    return [base]
