"""Build a report-only action decision matrix for scalping entries."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = DATA_DIR / "report"
ADM_REPORT_DIR = REPORT_DIR / "scalp_entry_action_decision_matrix"
PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENT_DIR = DATA_DIR / "threshold_cycle"
THRESHOLD_SNAPSHOT_DIR = THRESHOLD_EVENT_DIR / "snapshots"
POST_SELL_DIR = DATA_DIR / "post_sell"

REPORT_SCHEMA_VERSION = 1
MATRIX_VERSION_PREFIX = "scalp_entry_adm_v1"
SAMPLE_FLOOR = 20

ACTION_ORDER = [
    "BUY_NOW",
    "WAIT_REQUOTE",
    "SKIP_STALE",
    "BUY_DEFENSIVE",
    "NO_BUY_AI",
    "SKIP_SOURCE_QUALITY",
    "SKIP_PRE_SUBMIT_SAFETY",
]

RELEVANT_STAGES = {
    "scalp_entry_action_decision_snapshot",
    "ai_confirmed",
    "blocked_ai_score",
    "latency_block",
    "latency_pass",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "pre_submit_liquidity_guard_block",
    "pre_submit_overbought_pullback_guard_block",
    "order_bundle_submitted",
    "scalp_sim_entry_armed",
    "scalp_sim_entry_ai_price_applied",
    "scalp_sim_entry_ai_price_skip_order",
    "scalp_sim_pre_submit_liquidity_guard_would_block",
    "scalp_sim_pre_submit_liquidity_guard_would_pass",
    "scalp_sim_pre_submit_liquidity_guard_unknown",
    "scalp_sim_pre_submit_overbought_guard_would_block",
    "scalp_sim_pre_submit_overbought_guard_would_pass",
    "scalp_sim_buy_order_virtual_pending",
    "scalp_sim_entry_submit_revalidation_warning",
    "scalp_sim_entry_submit_revalidation_block",
    "scalp_sim_buy_order_assumed_filled",
    "scalp_sim_sell_order_assumed_filled",
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = ADM_REPORT_DIR / f"scalp_entry_action_decision_matrix_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _nonempty(value: Any) -> str:
    raw = str(value or "").strip()
    return "" if raw in {"", "-", "None", "none", "null"} else raw


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _event_paths(target_date: str) -> list[Path]:
    paths: list[Path] = []
    for path in [
        THRESHOLD_EVENT_DIR / f"threshold_events_{target_date}.jsonl",
        PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl",
        PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl.gz",
    ]:
        if path.exists():
            paths.append(path)
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"pipeline_events_{target_date}_*.jsonl")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"pipeline_events_{target_date}_*.jsonl.gz")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"threshold_events_{target_date}_*.jsonl")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"threshold_events_{target_date}_*.jsonl.gz")))
    return paths


def _iter_jsonl(path: Path, *, filter_entry_tokens: bool = True) -> Iterable[dict[str, Any]]:
    try:
        with _open_text(path) as handle:
            for line in handle:
                if not line:
                    continue
                if filter_entry_tokens and not any(
                    token in line
                    for token in (
                        "scalp",
                        "ENTRY_PIPELINE",
                        "ai_",
                        "entry_submit",
                        "pre_submit",
                        "order_bundle",
                    )
                ):
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload
    except OSError:
        return


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    if isinstance(fields, dict):
        return fields
    return {}


def _record_key(event: dict[str, Any]) -> str:
    fields = _event_fields(event)
    for key in ("candidate_id", "entry_adm_candidate_id", "sim_record_id", "record_id"):
        value = _nonempty(fields.get(key) or event.get(key))
        if value:
            return value
    return f"{event.get('stock_code') or ''}:{event.get('stage') or ''}:{event.get('emitted_at') or ''}"


def _iter_relevant_events(target_date: str) -> Iterable[dict[str, Any]]:
    seen: set[str] = set()
    for path in _event_paths(target_date):
        for event in _iter_jsonl(path):
            stage = str(event.get("stage") or "").strip()
            if stage not in RELEVANT_STAGES:
                continue
            if str(event.get("emitted_date") or target_date)[:10] != target_date:
                continue
            key = "|".join(
                [
                    str(stage),
                    str(event.get("stock_code") or ""),
                    str(event.get("record_id") or ""),
                    str(event.get("emitted_at") or ""),
                    _record_key(event),
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            event["_source_path"] = str(path)
            yield event


def _score_bucket(score: Any) -> str:
    value = _safe_float(score, None)
    if value is None:
        return "score_unknown"
    if value < 50:
        return "score_lt50"
    if value < 65:
        return "score50_64"
    if value < 75:
        return "score65_74"
    if value < 85:
        return "score75_84"
    return "score85_plus"


def _time_bucket(value: Any) -> str:
    raw = _nonempty(value)
    hour = -1
    try:
        hour = datetime.fromisoformat(str(value)).hour
    except Exception:
        if len(raw) >= 2 and raw[:2].isdigit() and not raw.startswith("20"):
            hour = int(raw[:2])
    if hour < 0:
        return "time_unknown"
    if hour < 10:
        return "time_0900_1000"
    if hour < 12:
        return "time_1000_1200"
    if hour < 14:
        return "time_1200_1400"
    return "time_1400_close"


def _stale_bucket(fields: dict[str, Any]) -> str:
    if _safe_bool(fields.get("entry_submit_revalidation_block")) or _safe_bool(fields.get("quote_stale")):
        return "stale_block"
    quote_age = _safe_float(fields.get("quote_age_ms") or fields.get("context_age_ms"), None)
    if quote_age is None:
        return "stale_unknown"
    if quote_age > 3000:
        return "stale_high"
    if quote_age > 1000:
        return "stale_watch"
    return "fresh"


def _liquidity_bucket(fields: dict[str, Any]) -> str:
    sim_action = _nonempty(fields.get("sim_pre_submit_liquidity_guard_action")).upper()
    sim_reason = _nonempty(fields.get("sim_pre_submit_liquidity_reason"))
    if sim_action == "WOULD_BLOCK":
        return sim_reason or "liquidity_blocked"
    if sim_action == "WOULD_PASS" and sim_reason == "liquidity_ok":
        return "liquidity_ok"
    if sim_action == "WOULD_PASS" and sim_reason == "liquidity_unknown":
        return "liquidity_unknown"
    if sim_action == "WOULD_UNKNOWN":
        return sim_reason or "liquidity_unknown"
    if _safe_bool(fields.get("liquidity_blocked")) or "liquidity" in str(fields.get("blocked_reason") or ""):
        return "liquidity_blocked"
    value = _safe_float(
        fields.get("sim_liquidity_value")
        or fields.get("liquidity_value")
        or fields.get("trade_value_krw")
        or fields.get("liquidity_score"),
        None,
    )
    min_liquidity = _safe_float(fields.get("sim_min_liquidity") or fields.get("min_liquidity"), None)
    if value is None:
        return "liquidity_unknown"
    if min_liquidity is not None and value < min_liquidity:
        return "below_min_liquidity"
    if value < 100_000_000:
        return "liquidity_low"
    if value < 500_000_000:
        return "liquidity_mid"
    return "liquidity_high"


def _overbought_bucket(fields: dict[str, Any]) -> str:
    sim_action = _nonempty(fields.get("sim_pre_submit_overbought_guard_action")).upper()
    sim_reason = _nonempty(fields.get("sim_pre_submit_overbought_reason"))
    if sim_action == "WOULD_BLOCK":
        return sim_reason or "overbought_blocked"
    if sim_action == "WOULD_PASS" and sim_reason == "overbought_ok":
        return "overbought_ok"
    if sim_action == "WOULD_PASS" and sim_reason == "overbought_unknown":
        return "overbought_unknown"
    if _safe_bool(fields.get("overbought_blocked")) or "overbought" in str(fields.get("blocked_reason") or ""):
        return "overbought_blocked"
    risk_state = _nonempty(fields.get("sim_overbought_risk_state") or fields.get("overbought_risk_state"))
    if risk_state in {"pullback_observed", "rebreak_candidate"}:
        return "overbought_ok"
    if risk_state:
        return risk_state
    intraday_range = _safe_float(fields.get("intraday_range_pct"), None)
    distance_high = _safe_float(fields.get("distance_from_day_high_pct"), None)
    if intraday_range is None:
        return "overbought_unknown"
    if intraday_range >= 18 and (distance_high is None or distance_high > -1.0):
        return "overbought_chase_risk"
    if intraday_range >= 10:
        return "overbought_watch"
    return "overbought_normal"


def _risk_context_bucket(fields: dict[str, Any]) -> str:
    if _safe_bool(fields.get("source_quality_blocked")) or _nonempty(fields.get("source_quality_block_reason")):
        return "source_quality_blocker"
    strength = _safe_float(fields.get("latest_strength") or fields.get("strength_momentum"), None)
    buy_pressure = _safe_float(fields.get("buy_pressure_10t") or fields.get("buy_pressure"), None)
    vpw = _safe_float(fields.get("vpw"), None)
    if strength is None and buy_pressure is None and vpw is None:
        return "risk_unknown"
    if (strength is not None and strength < 80) or (buy_pressure is not None and buy_pressure < 40):
        return "weak_strength_momentum"
    if (strength is not None and strength >= 140) or (buy_pressure is not None and buy_pressure >= 70):
        return "strong_strength_momentum"
    return "neutral_strength_momentum"


def _market_regime_continuous_bucket(fields: dict[str, Any]) -> str | None:
    label = _nonempty(fields.get("market_regime_continuous_label"))
    score = _safe_float(fields.get("market_regime_continuous_score"), None)
    if label in {"RISK_ON", "NEUTRAL", "RISK_OFF"}:
        return f"market_regime_{label.lower()}"
    if score is None:
        return None
    if score >= 65:
        return "market_regime_risk_on"
    if score >= 45:
        return "market_regime_neutral"
    return "market_regime_risk_off"


def _price_resolution_bucket(fields: dict[str, Any]) -> str:
    action = _nonempty(fields.get("ai_entry_price_canary_action"))
    reason = _nonempty(fields.get("price_resolution_reason") or fields.get("entry_price_resolution_reason"))
    if action == "USE_DEFENSIVE" or "defensive" in reason.lower():
        return "defensive_limit"
    if _nonempty(fields.get("resolved_order_price")):
        return "resolved_price"
    if _nonempty(fields.get("best_ask")) or _nonempty(fields.get("best_bid")):
        return "quote_based"
    return "price_unknown"


def _chosen_action(stage: str, fields: dict[str, Any]) -> str:
    explicit = _nonempty(fields.get("chosen_action") or fields.get("entry_adm_chosen_action"))
    if explicit in ACTION_ORDER:
        return explicit
    if stage in {
        "pre_submit_liquidity_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "scalp_sim_entry_ai_price_skip_order",
        "scalp_sim_pre_submit_liquidity_guard_would_block",
        "scalp_sim_pre_submit_overbought_guard_would_block",
    }:
        return "SKIP_PRE_SUBMIT_SAFETY"
    if stage == "scalp_sim_pre_submit_liquidity_guard_unknown":
        return "SKIP_SOURCE_QUALITY"
    if stage in {"entry_submit_revalidation_block", "scalp_sim_entry_submit_revalidation_block"}:
        return "SKIP_STALE"
    if stage in {"entry_submit_revalidation_warning", "scalp_sim_entry_submit_revalidation_warning", "latency_block"}:
        return "WAIT_REQUOTE"
    if stage == "blocked_ai_score":
        reason = str(fields.get("ai_input_source_quality_reason") or fields.get("blocked_reason") or "")
        return "SKIP_SOURCE_QUALITY" if "source" in reason or "stale" in reason else "NO_BUY_AI"
    if stage == "ai_confirmed":
        action = str(fields.get("action") or "").upper()
        score = _safe_float(fields.get("ai_score") or fields.get("ai_score_after_bonus"), 0.0) or 0.0
        return "BUY_NOW" if action == "BUY" and score >= 75 else "NO_BUY_AI"
    if stage in {
        "order_bundle_submitted",
        "scalp_sim_entry_ai_price_applied",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_pre_submit_liquidity_guard_would_pass",
        "scalp_sim_pre_submit_overbought_guard_would_pass",
    }:
        return "BUY_DEFENSIVE" if _price_resolution_bucket(fields) == "defensive_limit" else "BUY_NOW"
    if stage in {"scalp_sim_entry_armed", "latency_pass"}:
        return "BUY_DEFENSIVE" if _price_resolution_bucket(fields) == "defensive_limit" else "BUY_NOW"
    return "NO_BUY_AI"


def _eligible_actions(action: str, fields: dict[str, Any]) -> list[str]:
    explicit = _nonempty(fields.get("eligible_actions"))
    if explicit:
        return [item for item in explicit.replace("|", ",").split(",") if item]
    if action in {"BUY_NOW", "BUY_DEFENSIVE"}:
        return ["BUY_NOW", "BUY_DEFENSIVE", "WAIT_REQUOTE", "NO_BUY_AI"]
    if action in {"WAIT_REQUOTE", "SKIP_STALE"}:
        return ["WAIT_REQUOTE", "SKIP_STALE", "NO_BUY_AI"]
    if action == "SKIP_PRE_SUBMIT_SAFETY":
        return ["SKIP_PRE_SUBMIT_SAFETY", "NO_BUY_AI"]
    return ["NO_BUY_AI"]


def _base_row(event: dict[str, Any]) -> dict[str, Any]:
    fields = _event_fields(event)
    stage = str(event.get("stage") or "")
    action = _chosen_action(stage, fields)
    candidate_id = (
        _nonempty(fields.get("entry_adm_candidate_id"))
        or _nonempty(fields.get("candidate_id"))
        or _nonempty(fields.get("sim_record_id"))
        or _nonempty(event.get("record_id"))
        or _record_key(event)
    )
    sim_record_id = _nonempty(fields.get("sim_record_id"))
    row = {
        "candidate_id": candidate_id,
        "record_id": _nonempty(event.get("record_id") or fields.get("record_id")),
        "sim_record_id": sim_record_id,
        "stock_code": _nonempty(event.get("stock_code") or fields.get("stock_code")),
        "stock_name": _nonempty(event.get("stock_name") or fields.get("stock_name")),
        "stage": stage,
        "event_time": _nonempty(event.get("emitted_at")),
        "source_path": event.get("_source_path"),
        "ai_score": _safe_float(fields.get("ai_score") or fields.get("ai_score_after_bonus"), None),
        "ai_action": _nonempty(fields.get("action") or fields.get("ai_action")),
        "chosen_action": action,
        "eligible_actions": _eligible_actions(action, fields),
        "rejected_actions": [item for item in ACTION_ORDER if item not in _eligible_actions(action, fields)],
        "score_bucket": _score_bucket(fields.get("ai_score") or fields.get("ai_score_after_bonus")),
        "risk_context_bucket": _risk_context_bucket(fields),
        "market_regime_continuous_bucket": _market_regime_continuous_bucket(fields),
        "market_regime": _nonempty(fields.get("market_regime")),
        "market_regime_continuous_score": _safe_float(fields.get("market_regime_continuous_score"), None),
        "market_regime_continuous_label": _nonempty(fields.get("market_regime_continuous_label")),
        "market_regime_component_scores": (
            fields.get("market_regime_component_scores")
            if isinstance(fields.get("market_regime_component_scores"), dict)
            else None
        ),
        "swing_entry_recovery_gate_score": _safe_float(fields.get("swing_entry_recovery_gate_score"), None),
        "market_regime_score_version": _nonempty(fields.get("market_regime_score_version")),
        "market_regime_source_quality": _nonempty(fields.get("market_regime_source_quality")),
        "risk_context_owner": _nonempty(fields.get("risk_context_owner")),
        "stale_bucket": _stale_bucket(fields),
        "price_resolution_bucket": _price_resolution_bucket(fields),
        "liquidity_bucket": _liquidity_bucket(fields),
        "overbought_bucket": _overbought_bucket(fields),
        "time_bucket": _time_bucket(event.get("emitted_at") or fields.get("tick_latest_time")),
        "actual_order_submitted": _safe_bool(fields.get("actual_order_submitted"), stage == "order_bundle_submitted"),
        "broker_order_forbidden": _safe_bool(fields.get("broker_order_forbidden"), stage.startswith("scalp_sim_") or action not in {"BUY_NOW", "BUY_DEFENSIVE"}),
        "context_age_ms": _safe_float(fields.get("context_age_ms") or fields.get("tick_latest_age_ms"), None),
        "quote_age_ms": _safe_float(fields.get("quote_age_ms"), None),
        "entry_submit_revalidation_warning": _safe_bool(fields.get("entry_submit_revalidation_warning")),
        "entry_submit_revalidation_block": _safe_bool(fields.get("entry_submit_revalidation_block")),
        "best_bid": _safe_float(fields.get("best_bid"), None),
        "best_ask": _safe_float(fields.get("best_ask"), None),
        "resolved_order_price": _safe_float(fields.get("resolved_order_price") or fields.get("order_price"), None),
        "would_limit_fill": _safe_bool(fields.get("would_limit_fill")),
        "source_quality_block_reason": _nonempty(fields.get("source_quality_block_reason") or fields.get("ai_input_source_quality_reason")),
        "gate_action": _nonempty(fields.get("gate_action")),
        "entry_adm_prompt_applied": _safe_bool(fields.get("entry_adm_prompt_applied")),
        "entry_adm_version": _nonempty(fields.get("entry_adm_version")),
        "entry_adm_source_date": _nonempty(fields.get("entry_adm_source_date")),
        "entry_adm_bucket_token": _nonempty(fields.get("entry_adm_bucket_token")),
        "entry_adm_decision_alignment": _nonempty(fields.get("entry_adm_decision_alignment")),
        "entry_adm_runtime_effect": _nonempty(fields.get("entry_adm_runtime_effect")),
        "entry_adm_forced_action": _nonempty(fields.get("entry_adm_forced_action")),
        "entry_adm_runtime_reason": _nonempty(fields.get("entry_adm_runtime_reason")),
        "entry_adm_runtime_bias_applied": _safe_bool(fields.get("entry_adm_runtime_bias_applied")),
    }
    if not row["sim_record_id"] and str(stage).startswith("scalp_sim_"):
        row["sim_record_id"] = candidate_id if str(candidate_id).startswith("SCALPSIM-") else ""
    return row


def _load_sim_evaluations(target_date: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"
    by_key: dict[str, dict[str, Any]] = {}
    total = 0
    joined_keys: set[str] = set()
    if not path.exists():
        return by_key, {"artifact": None, "rows": 0, "join_keys": 0}
    for item in _iter_jsonl(path, filter_entry_tokens=False):
        total += 1
        for key in (
            _nonempty(item.get("candidate_id")),
            _nonempty(item.get("entry_adm_candidate_id")),
            _nonempty(item.get("sim_record_id")),
        ):
            if key:
                by_key[key] = item
                joined_keys.add(key)
    return by_key, {"artifact": str(path), "rows": total, "join_keys": len(joined_keys)}


def _apply_outcome(row: dict[str, Any], evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    evaluation = {}
    for key in (
        row.get("candidate_id"),
        row.get("sim_record_id"),
    ):
        if key and str(key) in evaluations:
            evaluation = evaluations[str(key)]
            break
    row = dict(row)
    row["outcome_joined"] = bool(evaluation)
    row["profit_rate"] = _safe_float(evaluation.get("profit_rate"), None) if evaluation else None
    row["exit_rule"] = _nonempty(evaluation.get("exit_rule")) if evaluation else ""
    row["sim_post_sell_outcome"] = _nonempty(evaluation.get("outcome")) if evaluation else ""
    for horizon in (10, 30, 60):
        metrics = evaluation.get(f"metrics_{horizon}m") if isinstance(evaluation.get(f"metrics_{horizon}m"), dict) else {}
        row[f"mfe_{horizon}m_pct"] = _safe_float(metrics.get("mfe_pct"), None) if metrics else None
        row[f"mae_{horizon}m_pct"] = _safe_float(metrics.get("mae_pct"), None) if metrics else None
        row[f"close_{horizon}m_pct"] = _safe_float(metrics.get("close_ret_pct"), None) if metrics else None
    mfe_30 = row.get("mfe_30m_pct")
    profit = row.get("profit_rate")
    row["missed_winner"] = bool(profit is not None and profit < 0 and mfe_30 is not None and mfe_30 >= 1.0)
    row["avoided_loser"] = bool(profit is not None and profit < 0 and row.get("chosen_action") in {"NO_BUY_AI", "SKIP_STALE", "SKIP_PRE_SUBMIT_SAFETY", "SKIP_SOURCE_QUALITY"})
    return row


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {
        "scalp_sim_entry_ai_price_skip_order": -1,
        "scalp_sim_pre_submit_liquidity_guard_would_block": -1,
        "scalp_sim_pre_submit_overbought_guard_would_block": -1,
        "scalp_sim_pre_submit_liquidity_guard_unknown": -1,
        "scalp_entry_action_decision_snapshot": 0,
        "order_bundle_submitted": 1,
        "scalp_sim_buy_order_assumed_filled": 2,
        "scalp_sim_pre_submit_liquidity_guard_would_pass": 3,
        "scalp_sim_pre_submit_overbought_guard_would_pass": 3,
        "scalp_sim_buy_order_virtual_pending": 3,
        "pre_submit_liquidity_guard_block": 3,
        "pre_submit_overbought_pullback_guard_block": 3,
        "entry_submit_revalidation_block": 4,
        "scalp_sim_entry_submit_revalidation_block": 4,
        "scalp_sim_entry_submit_revalidation_warning": 5,
        "blocked_ai_score": 5,
        "ai_confirmed": 6,
    }
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("candidate_id") or row.get("record_id") or f"{row.get('stock_code')}:{row.get('event_time')}")
        current = grouped.get(key)
        if not current or priority.get(str(row.get("stage")), 99) < priority.get(str(current.get("stage")), 99):
            grouped[key] = row
    return sorted(grouped.values(), key=lambda item: str(item.get("event_time") or ""))


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _action_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for action in ACTION_ORDER:
        subset = [row for row in rows if row.get("chosen_action") == action]
        joined = [row for row in subset if row.get("outcome_joined") and row.get("profit_rate") is not None]
        profits = [float(row["profit_rate"]) for row in joined if row.get("profit_rate") is not None]
        join_rate = (len(joined) / len(subset)) if subset else 0.0
        outcomes = Counter(str(row.get("sim_post_sell_outcome") or "unjoined") for row in subset)
        summaries.append(
            {
                "action": action,
                "sample_count": len(subset),
                "joined_sample": len(joined),
                "diagnostic_win_rate_pct": round((sum(1 for value in profits if value > 0) / len(profits)) * 100.0, 2) if profits else 0.0,
                "simple_sum_profit_pct": round(sum(profits), 4),
                "equal_weight_avg_profit_pct": _avg(profits),
                "source_quality_adjusted_ev_pct": round((_avg(profits) or 0.0) * join_rate, 4) if subset else None,
                "missed_winner_count": sum(1 for row in subset if row.get("missed_winner")),
                "avoided_loser_count": sum(1 for row in subset if row.get("avoided_loser")),
                "outcome_counts": dict(outcomes),
            }
        )
    return summaries


def _bucket_token(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(key) or "-")
        for key in (
            "score_bucket",
            "risk_context_bucket",
            "market_regime_continuous_bucket",
            "stale_bucket",
            "price_resolution_bucket",
            "liquidity_bucket",
            "overbought_bucket",
            "time_bucket",
        )
    )


def _bucket_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_bucket_token(row)].append(row)
    summaries: list[dict[str, Any]] = []
    for token, subset in grouped.items():
        joined = [row for row in subset if row.get("outcome_joined") and row.get("profit_rate") is not None]
        profits = [float(row["profit_rate"]) for row in joined if row.get("profit_rate") is not None]
        summaries.append(
            {
                "bucket_token": token,
                "sample_count": len(subset),
                "joined_sample": len(joined),
                "dominant_action": Counter(str(row.get("chosen_action")) for row in subset).most_common(1)[0][0],
                "equal_weight_avg_profit_pct": _avg(profits),
                "source_quality_adjusted_ev_pct": round((_avg(profits) or 0.0) * (len(joined) / len(subset)), 4) if subset else None,
                "missed_winner_count": sum(1 for row in subset if row.get("missed_winner")),
                "avoided_loser_count": sum(1 for row in subset if row.get("avoided_loser")),
            }
        )
    return sorted(summaries, key=lambda item: (-_safe_int(item.get("sample_count")), item.get("bucket_token") or ""))[:50]


def build_scalp_entry_action_decision_matrix_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    evaluations, eval_summary = _load_sim_evaluations(target_date)
    raw_rows = [_base_row(event) for event in _iter_relevant_events(target_date)]
    rows = [_apply_outcome(row, evaluations) for row in _dedupe_rows(raw_rows)]
    action_counts = Counter(str(row.get("chosen_action")) for row in rows)
    zero_sample_actions = [action for action in ACTION_ORDER if action_counts.get(action, 0) == 0]
    missing_actions: list[str] = []
    joined_sample = sum(1 for row in rows if row.get("outcome_joined"))
    prompt_applied = sum(1 for row in rows if row.get("entry_adm_prompt_applied"))
    runtime_bias_applied = sum(1 for row in rows if row.get("entry_adm_runtime_bias_applied"))
    runtime_effect_counts = Counter(str(row.get("entry_adm_runtime_effect") or "-") for row in rows)
    forced_action_counts = Counter(str(row.get("entry_adm_forced_action") or "-") for row in rows)
    warnings = []
    if joined_sample < SAMPLE_FLOOR:
        warnings.append("joined_sample_below_sample_floor")
    action_summary = _action_summary(rows)
    action_summary_actions = {str(item.get("action") or "") for item in action_summary if isinstance(item, dict)}
    missing_action_summary_rows = [action for action in ACTION_ORDER if action not in action_summary_actions]
    if missing_action_summary_rows:
        warnings.append("missing_action_bucket_summary_row")
    if any(row.get("risk_context_bucket") == "source_quality_blocker" for row in rows):
        warnings.append("source_quality_gap")
    if rows and prompt_applied == 0:
        warnings.append("prompt_context_not_loaded")
    status = "pass" if not warnings else "warning"
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "scalp_entry_action_decision_matrix",
        "status": status,
        "runtime_effect": False,
        "decision_authority": "entry_advisory_prompt_context_only",
        "application_mode": "operator_override_advisory_prompt",
        "metric_role": "action_decision_matrix",
        "window_policy": "same_day_intraday_events_plus_postclose_sim_post_sell_join",
        "sample_floor": SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
        "forbidden_uses": [
            "threshold mutation",
            "order guard mutation",
            "provider change",
            "bot restart",
            "broker order submit",
        ],
        "matrix_version": f"{MATRIX_VERSION_PREFIX}_{target_date}",
        "actions": list(ACTION_ORDER),
        "bucket_dimensions": [
            "score_bucket",
            "risk_context_bucket",
            "stale_bucket",
            "price_resolution_bucket",
            "liquidity_bucket",
            "overbought_bucket",
            "time_bucket",
        ],
        "summary": {
            "total_candidates": len(rows),
            "joined_sample": joined_sample,
            "sample_floor": SAMPLE_FLOOR,
            "prompt_applied_count": prompt_applied,
            "runtime_bias_applied_count": runtime_bias_applied,
            "runtime_effect_counts": dict(runtime_effect_counts),
            "forced_action_counts": dict(forced_action_counts),
            "action_counts": dict(action_counts),
            "missing_actions": missing_actions,
            "zero_sample_actions": zero_sample_actions,
            "missing_action_summary_rows": missing_action_summary_rows,
            "status": status,
            "warnings": warnings,
            "post_sell_evaluation": eval_summary,
        },
        "action_summary": action_summary,
        "bucket_summary": _bucket_summary(rows),
        "rows": rows,
        "examples": rows[:50],
        "sources": {
            "events": [str(path) for path in _event_paths(target_date)],
            "sim_post_sell_evaluations": eval_summary.get("artifact"),
        },
        "warnings": warnings,
    }
    ADM_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_scalp_entry_action_decision_matrix_markdown(report), encoding="utf-8")
    return report


def render_scalp_entry_action_decision_matrix_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Scalp Entry Action Decision Matrix - {report.get('date')}",
        "",
        "## Contract",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- application_mode: `{report.get('application_mode')}`",
        f"- primary_decision_metric: `{report.get('primary_decision_metric')}`",
        "",
        "## Summary",
        f"- total_candidates: `{summary.get('total_candidates')}`",
        f"- joined_sample/sample_floor: `{summary.get('joined_sample')}` / `{summary.get('sample_floor')}`",
        f"- prompt_applied_count: `{summary.get('prompt_applied_count')}`",
        f"- runtime_bias_applied_count: `{summary.get('runtime_bias_applied_count')}`",
        f"- runtime_effect_counts: `{summary.get('runtime_effect_counts') or {}}`",
        f"- forced_action_counts: `{summary.get('forced_action_counts') or {}}`",
        f"- action_counts: `{summary.get('action_counts')}`",
        f"- missing_actions: `{summary.get('missing_actions')}`",
        f"- zero_sample_actions: `{summary.get('zero_sample_actions')}`",
        "",
        "## Action Summary",
        "| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report.get("action_summary") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('action')}` | {item.get('sample_count')} | {item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | {item.get('equal_weight_avg_profit_pct')} | {item.get('missed_winner_count')} | {item.get('avoided_loser_count')} |"
        )
    bucket_summary = report.get("bucket_summary") if isinstance(report.get("bucket_summary"), list) else []
    lines.extend(["", "## Top Buckets"])
    for item in bucket_summary[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('bucket_token')}` sample=`{item.get('sample_count')}` joined=`{item.get('joined_sample')}` action=`{item.get('dominant_action')}` sq_ev=`{item.get('source_quality_adjusted_ev_pct')}`"
            )
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{warning}`" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build scalp entry action decision matrix report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_scalp_entry_action_decision_matrix_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
