"""Report-only intraday market breadth collector for panic detection.

The collector refreshes live market/industry breadth evidence for the panic
reports. It does not mutate runtime thresholds, order routing, or broker state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.risk.market_weakness_threshold_policy import (
    BASELINE_ACTIVATION_OBSERVATIONS,
    BASELINE_RELEASE_OBSERVATIONS,
    MIN_OBSERVATION_SPACING_SEC,
    observation_thresholds,
    resolve_effective_thresholds,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import write_json_object_generation_safe

SCHEMA_VERSION = 2
REPORT_DIRNAME = "market_panic_breadth"
OBSERVATION_DIRNAME = "market_weakness_observations"
REPORT_ONLY_FORBIDDEN_USES = [
    "runtime_threshold_apply",
    "order_submit",
    "auto_sell",
    "bot_restart",
    "provider_route_change",
]
KOSPI_CODES = {"001", "1001", "KOSPI"}
KOSDAQ_CODES = {"101", "2001", "KOSDAQ"}
DEFAULT_INDEX_DROP_FLOOR_PCT = -1.2
DEFAULT_INDUSTRY_DOWN_RATIO_FLOOR_PCT = 62.0
DEFAULT_SEVERE_DOWN_FLOOR_PCT = -2.0
DEFAULT_SEVERE_DOWN_RATIO_FLOOR_PCT = 15.0
DEFAULT_STOCK_FALL_RATIO_FLOOR_PCT = 70.0
DEFAULT_INDEX_RISE_FLOOR_PCT = 1.2
DEFAULT_INDUSTRY_UP_RATIO_FLOOR_PCT = 62.0
DEFAULT_SEVERE_UP_FLOOR_PCT = 2.0
DEFAULT_SEVERE_UP_RATIO_FLOOR_PCT = 15.0
DEFAULT_STOCK_RISE_RATIO_FLOOR_PCT = 70.0
DEFAULT_MARKET_WEIGHTS = {
    "KOSPI": 0.65,
    "KOSDAQ": 0.35,
}
MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS = BASELINE_ACTIVATION_OBSERVATIONS
MARKET_WEAKNESS_RELEASE_OBSERVATIONS = BASELINE_RELEASE_OBSERVATIONS
MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC = MIN_OBSERVATION_SPACING_SEC
MARKET_WEAKNESS_RELEASE_INDEX_MARGIN_PCT = 0.3
MARKET_WEAKNESS_RELEASE_INDUSTRY_MARGIN_PCT = 7.0
MARKET_WEAKNESS_RELEASE_SEVERE_MARGIN_PCT = 5.0
MARKET_WEAKNESS_RELEASE_STOCK_MARGIN_PCT = 10.0
MARKET_WEAKNESS_MIN_MARKET_INDEX_COUNT = 2
MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT = 3
KST = ZoneInfo("Asia/Seoul")


def market_weakness_observation_id(observation: dict[str, Any]) -> str:
    """Return the immutable schema-v2 identity for one weakness snapshot."""

    identity_payload = {
        "schema_version": 2,
        "target_date": observation.get("target_date"),
        "as_of": observation.get("as_of"),
        "source_quality_status": observation.get("source_quality_status"),
        "source_quality_ready": observation.get("source_quality_ready"),
        "raw_state": observation.get("raw_state"),
        "affected_markets": observation.get("affected_markets"),
        "recovery_evidence_markets": observation.get("recovery_evidence_markets"),
        "evidence": observation.get("evidence"),
        "release_margin": observation.get("release_margin"),
        "hysteresis_policy": observation.get("hysteresis_policy"),
    }
    return (
        "market-weakness-"
        + hashlib.sha256(
            json.dumps(
                identity_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()[:20]
    )


def market_weakness_observation_contract_errors(
    observation: dict[str, Any],
) -> list[str]:
    """Validate the immutable, market-scoped source-only observation contract."""

    errors: list[str] = []
    supported_markets = {"KOSPI", "KOSDAQ"}
    raw_state = _safe_str(observation.get("raw_state"))
    affected_raw = observation.get("affected_markets")
    recovered_raw = observation.get("recovery_evidence_markets")
    affected = (
        sorted({_safe_str(value).upper() for value in affected_raw})
        if isinstance(affected_raw, list)
        else []
    )
    recovered = (
        sorted({_safe_str(value).upper() for value in recovered_raw})
        if isinstance(recovered_raw, list)
        else []
    )
    if observation.get("schema_version") != 2:
        errors.append("market_scope_schema_v2_required")
    try:
        observed_at = datetime.fromisoformat(_safe_str(observation.get("as_of")))
    except ValueError:
        observed_at = None
    if (
        observed_at is None
        or observed_at.tzinfo is None
        or observed_at.astimezone(KST).date().isoformat()
        != _safe_str(observation.get("target_date"))
    ):
        errors.append("exact_date_aware_observation_time_invalid")
    if observation.get("source_quality_status") != "ok":
        errors.append("source_quality_status_not_ok")
    if observation.get("source_quality_ready") is not True:
        errors.append("source_quality_not_ready")
    sample_floor = observation.get("sample_floor")
    try:
        activation_observations, release_observations, spacing_sec = (
            observation_thresholds(observation)
        )
    except ValueError:
        activation_observations = None
        release_observations = None
        spacing_sec = None
    if not (
        observation.get("metric_role") == "market_weakness_observation"
        and observation.get("window_policy")
        == "intraday_consecutive_unique_snapshot_hysteresis"
        and isinstance(sample_floor, dict)
        and sample_floor.get("market_index_count")
        == MARKET_WEAKNESS_MIN_MARKET_INDEX_COUNT
        and sample_floor.get("industry_row_count")
        == MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
        and sample_floor.get("activation_unique_observations")
        == activation_observations
        and sample_floor.get("release_unique_observations") == release_observations
        and spacing_sec == MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC
        and observation.get("primary_decision_metric")
        == "raw_state_with_release_margin"
    ):
        errors.append("metric_contract_invalid")
    required_forbidden_uses = set(
        REPORT_ONLY_FORBIDDEN_USES
        + [
            "widget_entry_block",
            "episode_entry_block",
            "open_buy_cancel",
            "target_order_cancel",
            "holding_policy_change",
            "price_or_quantity_change",
            "position_exit",
        ]
    )
    forbidden_uses = observation.get("forbidden_uses")
    if not isinstance(forbidden_uses, list) or not required_forbidden_uses.issubset(
        {_safe_str(value) for value in forbidden_uses}
    ):
        errors.append("forbidden_use_contract_invalid")
    response_contract = observation.get("response_research_contract")
    if not (
        isinstance(response_contract, dict)
        and response_contract.get("runtime_effect") is False
        and response_contract.get("allowed_runtime_apply") is False
        and response_contract.get("control") == "current_owner_behavior_unchanged"
    ):
        errors.append("response_research_contract_invalid")
    if not (
        observation.get("decision_authority") == "source_quality_observation_only"
        and observation.get("runtime_effect") is False
        and observation.get("allowed_runtime_apply") is False
    ):
        errors.append("authority_contract_invalid")
    if raw_state not in {
        "BROAD_WEAKNESS",
        "SINGLE_MARKET_WEAKNESS",
        "RECOVERY_EVIDENCE",
        "NEAR_WEAKNESS_BOUNDARY",
        "UNKNOWN",
    }:
        errors.append("raw_state_invalid")
    elif raw_state == "UNKNOWN" and observation.get("source_quality_ready") is True:
        errors.append("unknown_state_with_ready_source_invalid")
    if not isinstance(affected_raw, list) or any(
        market not in supported_markets for market in affected
    ):
        errors.append("affected_market_scope_invalid")
    if not isinstance(recovered_raw, list) or any(
        market not in supported_markets for market in recovered
    ):
        errors.append("recovery_market_scope_invalid")
    if affected_raw != affected:
        errors.append("affected_market_scope_not_canonical")
    if recovered_raw != recovered:
        errors.append("recovery_market_scope_not_canonical")
    if raw_state == "BROAD_WEAKNESS" and affected != ["KOSDAQ", "KOSPI"]:
        errors.append("broad_market_scope_invalid")
    elif raw_state == "SINGLE_MARKET_WEAKNESS" and len(affected) != 1:
        errors.append("single_market_scope_invalid")
    elif raw_state not in {"BROAD_WEAKNESS", "SINGLE_MARKET_WEAKNESS"} and affected:
        errors.append("non_weak_state_affected_scope_invalid")
    if set(affected) & set(recovered):
        errors.append("weak_and_recovery_scope_conflict")

    evidence = observation.get("evidence")
    evidence_market_states = (
        evidence.get("market_states")
        if isinstance(evidence, dict)
        and isinstance(evidence.get("market_states"), dict)
        else None
    )
    if not (
        isinstance(evidence, dict)
        and evidence.get("affected_markets") == affected
        and evidence.get("recovery_evidence_markets") == recovered
        and isinstance(evidence_market_states, dict)
        and all(
            isinstance(evidence_market_states.get(market), dict)
            and evidence_market_states[market].get("source_quality_ready") is True
            for market in supported_markets
        )
    ):
        errors.append("market_scope_evidence_contract_invalid")

    release_margin = observation.get("release_margin")
    release_thresholds = (
        release_margin.get("thresholds")
        if isinstance(release_margin, dict)
        and isinstance(release_margin.get("thresholds"), dict)
        else None
    )
    required_release_threshold_names = {
        "each_market_index_above_pct",
        "weighted_market_index_above_pct",
        "industry_down_ratio_below_pct",
        "industry_severe_down_ratio_below_pct",
        "max_stock_fall_ratio_below_pct",
    }
    if not (
        isinstance(release_thresholds, dict)
        and set(release_thresholds) == required_release_threshold_names
        and all(
            (value := _safe_float(release_thresholds.get(name), None)) is not None
            and math.isfinite(value)
            for name in required_release_threshold_names
        )
    ):
        errors.append("release_threshold_contract_invalid")
    market_checks = (
        release_margin.get("markets")
        if isinstance(release_margin, dict)
        and isinstance(release_margin.get("markets"), dict)
        else None
    )
    passed_markets: list[str] = []
    if not isinstance(release_margin, dict) or not isinstance(
        release_margin.get("passed"), bool
    ):
        errors.append("release_margin_contract_invalid")
    if market_checks is None:
        errors.append("market_release_contract_missing")
    else:
        for market in sorted(supported_markets):
            market_check = market_checks.get(market)
            checks = (
                market_check.get("checks")
                if isinstance(market_check, dict)
                and isinstance(market_check.get("checks"), dict)
                else None
            )
            required_check_names = {
                "market_index_recovered",
                "industry_down_ratio_recovered",
                "industry_severe_down_ratio_recovered",
                "stock_fall_ratio_recovered",
            }
            market_contract_valid = bool(
                isinstance(market_check, dict)
                and isinstance(market_check.get("passed"), bool)
                and isinstance(market_check.get("source_quality_ready"), bool)
                and isinstance(checks, dict)
                and set(checks) == required_check_names
                and all(isinstance(value, bool) for value in checks.values())
                and market_check["passed"]
                is bool(market_check["source_quality_ready"] and all(checks.values()))
            )
            if not market_contract_valid:
                errors.append(f"market_release_contract_invalid:{market}")
            elif market_check["passed"]:
                passed_markets.append(market)
    global_checks = (
        release_margin.get("checks")
        if isinstance(release_margin, dict)
        and isinstance(release_margin.get("checks"), dict)
        else None
    )
    required_global_check_names = {
        "each_market_index_recovered",
        "weighted_market_index_recovered",
        "industry_down_ratio_recovered",
        "industry_severe_down_ratio_recovered",
        "stock_fall_ratio_recovered",
    }
    if not (
        isinstance(release_margin, dict)
        and isinstance(global_checks, dict)
        and set(global_checks) == required_global_check_names
        and all(isinstance(value, bool) for value in global_checks.values())
        and release_margin.get("passed")
        is bool(observation.get("source_quality_ready") and all(global_checks.values()))
    ):
        errors.append("global_release_check_contract_invalid")
    if recovered != passed_markets:
        errors.append("recovery_market_release_mismatch")
    if raw_state == "RECOVERY_EVIDENCE" and (
        not isinstance(release_margin, dict) or release_margin.get("passed") is not True
    ):
        errors.append("global_recovery_margin_not_passed")

    observation_id = _safe_str(observation.get("observation_id"))
    try:
        expected_id = market_weakness_observation_id(observation)
    except (TypeError, ValueError):
        expected_id = ""
    if not observation_id or observation_id != expected_id:
        errors.append("observation_identity_invalid")
    return list(dict.fromkeys(errors))


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _report_path(target_date: str) -> Path:
    return _report_dir() / f"{REPORT_DIRNAME}_{target_date}.json"


def _observation_path(target_date: str, as_of: str, observation_id: str) -> Path:
    timestamp = "".join(character for character in as_of if character.isdigit())[:14]
    timestamp = timestamp or "unknown_time"
    return (
        DATA_DIR
        / "report"
        / OBSERVATION_DIRNAME
        / target_date
        / f"market_weakness_observation_{timestamp}_{observation_id[-12:]}.json"
    )


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        text = str(value).replace(",", "").replace("+", "").strip()
        result = float(text)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int = 0) -> int:
    parsed = _safe_float(value, None)
    return int(parsed) if parsed is not None else default


def _field(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row.get(name) not in (None, ""):
            return row.get(name)
    lower = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        value = lower.get(name.lower())
        if value not in (None, ""):
            return value
    return None


def _find_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            if node and all(isinstance(item, dict) for item in node):
                signal_rows = [
                    item
                    for item in node
                    if any(
                        key in item
                        for key in (
                            "inds_cd",
                            "upjong_cd",
                            "stk_cd",
                            "code",
                            "cur_prc",
                            "flu_rt",
                            "chg_rt",
                        )
                    )
                ]
                if signal_rows:
                    rows.extend(signal_rows)
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            for value in node.values():
                visit(value)

    visit(payload)
    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        code = _safe_str(
            _field(row, "inds_cd", "upjong_cd", "stk_cd", "code", "marketCode")
        )
        name = _safe_str(
            _field(row, "inds_nm", "upjong_nm", "stk_nm", "name", "marketName")
        )
        dedup[(code, name)] = row
    return list(dedup.values())


def parse_kiwoom_industry_rows(
    payloads: list[dict[str, Any]] | dict[str, Any] | list[Any],
    *,
    source_market: str | None = None,
) -> list[dict[str, Any]]:
    normalized_source_market = _safe_str(source_market).upper() or None
    if normalized_source_market not in {None, "KOSPI", "KOSDAQ"}:
        raise ValueError(f"unsupported source_market: {source_market}")
    payload_list = payloads if isinstance(payloads, list) else [payloads]
    parsed: list[dict[str, Any]] = []
    for row in _find_rows(payload_list):
        code = _safe_str(
            _field(row, "inds_cd", "upjong_cd", "stk_cd", "code", "marketCode")
        )
        name = _safe_str(
            _field(row, "inds_nm", "upjong_nm", "stk_nm", "name", "marketName")
        )
        price = _safe_float(
            _field(row, "cur_prc", "curr_price", "close_pric", "price"), None
        )
        change_pct = _safe_float(
            _field(
                row,
                "flu_rt",
                "chg_rt",
                "change_rate",
                "fluctuation_rate",
                "updown_rate",
            ),
            None,
        )
        change = _safe_float(
            _field(row, "pred_pre", "chg_prc", "change", "change_price"), None
        )
        volume = _safe_float(_field(row, "trde_qty", "volume", "acc_trdvol"), None)
        rising_count = _safe_int(_field(row, "rising", "rise", "up_count"), 0)
        flat_count = _safe_int(_field(row, "stdns", "flat", "unchanged_count"), 0)
        fall_count = _safe_int(_field(row, "fall", "down", "down_count"), 0)
        listed_count = _safe_int(
            _field(row, "flo_stk_num", "listed_count", "stock_count"), 0
        )
        if price is None and change_pct is None and change is None:
            continue
        parsed.append(
            {
                "code": code,
                "name": name or code,
                "price": abs(price) if price is not None else None,
                "change": change,
                "change_pct": change_pct,
                "volume": volume,
                "rising_count": rising_count,
                "flat_count": flat_count,
                "fall_count": fall_count,
                "listed_count": listed_count,
                # ka20003 returns a market-specific industry universe selected by
                # request inds_cd.  The response rows do not repeat that parent
                # market, so preserve the request provenance explicitly.
                "source_market": normalized_source_market,
                "raw_keys": sorted(str(key) for key in row.keys()),
            }
        )
    return parsed


def _is_market_index(row: dict[str, Any]) -> str | None:
    code = _safe_str(row.get("code")).upper()
    raw_name = _safe_str(row.get("name"))
    name = raw_name.upper()
    if code in KOSDAQ_CODES or raw_name in {"종합(KOSDAQ)", "코스닥"}:
        return "KOSDAQ"
    if code in KOSPI_CODES or raw_name in {"종합(KOSPI)", "코스피"} or name == "KOSPI":
        return "KOSPI"
    return None


def _weighted_average(values: list[tuple[float, float]]) -> float | None:
    total_weight = sum(weight for _, weight in values if weight > 0)
    if total_weight <= 0:
        return None
    return round(
        sum(value * weight for value, weight in values if weight > 0) / total_weight, 3
    )


def _industry_breadth_metrics(
    rows: list[dict[str, Any]],
    *,
    severe_down_floor_pct: float,
    severe_up_floor_pct: float,
) -> dict[str, Any]:
    pct_rows = [row for row in rows if row.get("change_pct") is not None]
    down_rows = [row for row in pct_rows if float(row.get("change_pct") or 0.0) < 0.0]
    severe_down_rows = [
        row
        for row in pct_rows
        if float(row.get("change_pct") or 0.0) <= severe_down_floor_pct
    ]
    up_rows = [row for row in pct_rows if float(row.get("change_pct") or 0.0) > 0.0]
    severe_up_rows = [
        row
        for row in pct_rows
        if float(row.get("change_pct") or 0.0) >= severe_up_floor_pct
    ]
    sample_count = len(pct_rows)

    def ratio(count: int) -> float:
        return round((count / sample_count) * 100.0, 1) if sample_count else 0.0

    return {
        "sample_count": sample_count,
        "up_count": len(up_rows),
        "up_ratio_pct": ratio(len(up_rows)),
        "down_count": len(down_rows),
        "down_ratio_pct": ratio(len(down_rows)),
        "severe_down_count": len(severe_down_rows),
        "severe_down_floor_pct": severe_down_floor_pct,
        "severe_down_ratio_pct": ratio(len(severe_down_rows)),
        "severe_up_count": len(severe_up_rows),
        "severe_up_floor_pct": severe_up_floor_pct,
        "severe_up_ratio_pct": ratio(len(severe_up_rows)),
    }


def summarize_breadth(
    rows: list[dict[str, Any]],
    *,
    index_drop_floor_pct: float = DEFAULT_INDEX_DROP_FLOOR_PCT,
    industry_down_ratio_floor_pct: float = DEFAULT_INDUSTRY_DOWN_RATIO_FLOOR_PCT,
    severe_down_floor_pct: float = DEFAULT_SEVERE_DOWN_FLOOR_PCT,
    severe_down_ratio_floor_pct: float = DEFAULT_SEVERE_DOWN_RATIO_FLOOR_PCT,
    stock_fall_ratio_floor_pct: float = DEFAULT_STOCK_FALL_RATIO_FLOOR_PCT,
    index_rise_floor_pct: float = DEFAULT_INDEX_RISE_FLOOR_PCT,
    industry_up_ratio_floor_pct: float = DEFAULT_INDUSTRY_UP_RATIO_FLOOR_PCT,
    severe_up_floor_pct: float = DEFAULT_SEVERE_UP_FLOOR_PCT,
    severe_up_ratio_floor_pct: float = DEFAULT_SEVERE_UP_RATIO_FLOOR_PCT,
    stock_rise_ratio_floor_pct: float = DEFAULT_STOCK_RISE_RATIO_FLOOR_PCT,
) -> dict[str, Any]:
    market_indices: dict[str, dict[str, Any]] = {}
    industry_rows: list[dict[str, Any]] = []
    for row in rows:
        market = _is_market_index(row)
        if market:
            current = market_indices.get(market)
            if current is None or row.get("change_pct") is not None:
                market_indices[market] = row
        else:
            industry_rows.append(row)

    industry_breadth = _industry_breadth_metrics(
        industry_rows,
        severe_down_floor_pct=severe_down_floor_pct,
        severe_up_floor_pct=severe_up_floor_pct,
    )
    sample_count = int(industry_breadth["sample_count"])
    down_ratio = float(industry_breadth["down_ratio_pct"])
    severe_ratio = float(industry_breadth["severe_down_ratio_pct"])
    up_ratio = float(industry_breadth["up_ratio_pct"])
    severe_up_ratio = float(industry_breadth["severe_up_ratio_pct"])
    scoped_industry_rows: dict[str, list[dict[str, Any]]] = {
        "KOSPI": [],
        "KOSDAQ": [],
    }
    for row in industry_rows:
        source_market = _safe_str(row.get("source_market")).upper()
        if source_market in scoped_industry_rows:
            scoped_industry_rows[source_market].append(row)
    index_changes = {
        market: float(row.get("change_pct"))
        for market, row in market_indices.items()
        if row.get("change_pct") is not None
    }
    weighted_index_change = _weighted_average(
        [
            (change, DEFAULT_MARKET_WEIGHTS.get(market, 0.0))
            for market, change in index_changes.items()
        ]
    )
    stock_fall_rows = []
    stock_rise_rows = []
    stock_breadth_by_market: dict[str, dict[str, Any]] = {}
    stock_fall_weight_values: list[tuple[float, float]] = []
    stock_rise_weight_values: list[tuple[float, float]] = []
    for market, row in market_indices.items():
        listed = _safe_int(row.get("listed_count"), 0)
        fall = _safe_int(row.get("fall_count"), 0)
        rising = _safe_int(row.get("rising_count"), 0)
        flat = _safe_int(row.get("flat_count"), 0)
        denominator = listed or (fall + rising + flat)
        fall_ratio = round((fall / denominator) * 100.0, 1) if denominator else 0.0
        rise_ratio = round((rising / denominator) * 100.0, 1) if denominator else 0.0
        weight = (
            float(denominator)
            if denominator > 0
            else DEFAULT_MARKET_WEIGHTS.get(market, 0.0)
        )
        stock_fall_weight_values.append((fall_ratio, weight))
        stock_rise_weight_values.append((rise_ratio, weight))
        stock_fall_rows.append(
            {
                "market": market,
                "listed_count": denominator,
                "rising_count": rising,
                "flat_count": flat,
                "fall_count": fall,
                "fall_ratio_pct": fall_ratio,
            }
        )
        stock_rise_rows.append(
            {
                "market": market,
                "listed_count": denominator,
                "rising_count": rising,
                "flat_count": flat,
                "fall_count": fall,
                "rise_ratio_pct": rise_ratio,
            }
        )
        stock_breadth_by_market[market] = {
            "listed_count": denominator,
            "fall_ratio_pct": fall_ratio,
            "rise_ratio_pct": rise_ratio,
        }
    max_stock_fall_ratio = max(
        [row["fall_ratio_pct"] for row in stock_fall_rows], default=0.0
    )
    max_stock_rise_ratio = max(
        [row["rise_ratio_pct"] for row in stock_rise_rows], default=0.0
    )
    weighted_stock_fall_ratio = _weighted_average(stock_fall_weight_values) or 0.0
    weighted_stock_rise_ratio = _weighted_average(stock_rise_weight_values) or 0.0
    index_risk_off = (
        weighted_index_change is not None
        and weighted_index_change <= index_drop_floor_pct
    )
    single_market_index_risk_off = any(
        change <= index_drop_floor_pct for change in index_changes.values()
    )
    industry_risk_off = sample_count > 0 and down_ratio >= industry_down_ratio_floor_pct
    severe_risk_off = sample_count > 0 and severe_ratio >= severe_down_ratio_floor_pct
    stock_breadth_risk_off = weighted_stock_fall_ratio >= stock_fall_ratio_floor_pct
    single_market_stock_risk_off = max_stock_fall_ratio >= stock_fall_ratio_floor_pct
    risk_off = bool(
        index_risk_off
        and (industry_risk_off or severe_risk_off or stock_breadth_risk_off)
    )
    index_risk_on = (
        weighted_index_change is not None
        and weighted_index_change >= index_rise_floor_pct
    )
    single_market_index_risk_on = any(
        change >= index_rise_floor_pct for change in index_changes.values()
    )
    industry_risk_on = sample_count > 0 and up_ratio >= industry_up_ratio_floor_pct
    severe_risk_on = sample_count > 0 and severe_up_ratio >= severe_up_ratio_floor_pct
    stock_breadth_risk_on = weighted_stock_rise_ratio >= stock_rise_ratio_floor_pct
    single_market_stock_risk_on = max_stock_rise_ratio >= stock_rise_ratio_floor_pct
    risk_on = bool(
        index_risk_on and (industry_risk_on or severe_risk_on or stock_breadth_risk_on)
    )
    market_states: dict[str, dict[str, Any]] = {}
    affected_markets: list[str] = []
    risk_on_markets: list[str] = []
    for market in ("KOSPI", "KOSDAQ"):
        market_industry = _industry_breadth_metrics(
            scoped_industry_rows[market],
            severe_down_floor_pct=severe_down_floor_pct,
            severe_up_floor_pct=severe_up_floor_pct,
        )
        stock_row = stock_breadth_by_market.get(market) or {}
        index_change = index_changes.get(market)
        index_weak = bool(
            index_change is not None and index_change <= index_drop_floor_pct
        )
        stock_weak = bool(
            stock_row.get("listed_count", 0) > 0
            and stock_row.get("fall_ratio_pct", 0.0) >= stock_fall_ratio_floor_pct
        )
        industry_weak = bool(
            market_industry["sample_count"] >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
            and market_industry["down_ratio_pct"] >= industry_down_ratio_floor_pct
        )
        severe_weak = bool(
            market_industry["sample_count"] >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
            and market_industry["severe_down_ratio_pct"] >= severe_down_ratio_floor_pct
        )
        index_strong = bool(
            index_change is not None and index_change >= index_rise_floor_pct
        )
        stock_strong = bool(
            stock_row.get("listed_count", 0) > 0
            and stock_row.get("rise_ratio_pct", 0.0) >= stock_rise_ratio_floor_pct
        )
        industry_strong = bool(
            market_industry["sample_count"] >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
            and market_industry["up_ratio_pct"] >= industry_up_ratio_floor_pct
        )
        severe_strong = bool(
            market_industry["sample_count"] >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
            and market_industry["severe_up_ratio_pct"] >= severe_up_ratio_floor_pct
        )
        scope_ready = bool(
            index_change is not None
            and (
                market_industry["sample_count"]
                >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
                or stock_row.get("listed_count", 0) > 0
            )
        )
        weak = bool(
            scope_ready
            and (index_weak or stock_weak)
            and (industry_weak or severe_weak or stock_weak)
        )
        strong = bool(
            scope_ready
            and (index_strong or stock_strong)
            and (industry_strong or severe_strong or stock_strong)
        )
        if weak:
            affected_markets.append(market)
        if strong:
            risk_on_markets.append(market)
        market_states[market] = {
            "source_quality_ready": scope_ready,
            "industry_scope_status": (
                "request_market_bound"
                if market_industry["sample_count"]
                >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
                else (
                    "market_stock_breadth_bound"
                    if stock_row.get("listed_count", 0) > 0
                    else "market_scope_provenance_missing"
                )
            ),
            "index_change_pct": index_change,
            "industry_breadth": market_industry,
            "stock_breadth": stock_row,
            "risk_off_advisory": weak,
            "risk_on_advisory": strong,
            "checks": {
                "index_weak": index_weak,
                "industry_weak": industry_weak,
                "industry_severe_weak": severe_weak,
                "stock_weak": stock_weak,
                "index_strong": index_strong,
                "industry_strong": industry_strong,
                "industry_severe_strong": severe_strong,
                "stock_strong": stock_strong,
            },
        }
    single_market_risk_off = bool(not risk_off and affected_markets)
    single_market_risk_on = bool(not risk_on and risk_on_markets)
    reasons: list[str] = []
    if index_risk_off:
        reasons.append("weighted_market_index_intraday_drop")
    elif single_market_index_risk_off:
        reasons.append("single_market_index_intraday_drop")
    if industry_risk_off:
        reasons.append("industry_breadth_down_ratio_high")
    if severe_risk_off:
        reasons.append("industry_severe_down_ratio_high")
    if stock_breadth_risk_off:
        reasons.append("weighted_listed_stock_fall_ratio_high")
    elif single_market_stock_risk_off:
        reasons.append("single_market_listed_stock_fall_ratio_high")
    if not risk_off:
        reasons.append("live market breadth panic thresholds not breached")
    risk_on_reasons: list[str] = []
    if index_risk_on:
        risk_on_reasons.append("weighted_market_index_intraday_rise")
    elif single_market_index_risk_on:
        risk_on_reasons.append("single_market_index_intraday_rise")
    if industry_risk_on:
        risk_on_reasons.append("industry_breadth_up_ratio_high")
    if severe_risk_on:
        risk_on_reasons.append("industry_severe_up_ratio_high")
    if stock_breadth_risk_on:
        risk_on_reasons.append("weighted_listed_stock_rise_ratio_high")
    elif single_market_stock_risk_on:
        risk_on_reasons.append("single_market_listed_stock_rise_ratio_high")
    if not risk_on:
        risk_on_reasons.append("live market breadth risk-on thresholds not breached")

    return {
        "metric_role": "risk_regime_state",
        "decision_authority": "source_quality_only",
        "window_policy": "intraday_observe_only",
        "sample_floor": "at least one market index and live industry rows when available",
        "primary_decision_metric": "weighted_composite_risk_off_advisory",
        "source_quality_gate": "Kiwoom REST ka20003 current industry/index snapshot must be generated intraday",
        "forbidden_uses": REPORT_ONLY_FORBIDDEN_USES,
        "market_indices": market_indices,
        "weighted_market_breadth": {
            "market_weights": DEFAULT_MARKET_WEIGHTS,
            "index_change_pct": weighted_index_change,
            "stock_fall_ratio_pct": weighted_stock_fall_ratio,
            "stock_rise_ratio_pct": weighted_stock_rise_ratio,
            "single_market_risk_off_advisory": single_market_risk_off,
            "single_market_risk_on_advisory": single_market_risk_on,
        },
        "industry_breadth": industry_breadth,
        "market_states": market_states,
        "affected_markets": (
            ["KOSPI", "KOSDAQ"] if risk_off else sorted(affected_markets)
        ),
        "risk_on_markets": (
            ["KOSPI", "KOSDAQ"] if risk_on else sorted(risk_on_markets)
        ),
        "stock_breadth": {
            "markets": stock_fall_rows,
            "rise_markets": stock_rise_rows,
            "max_fall_ratio_pct": max_stock_fall_ratio,
            "fall_ratio_floor_pct": stock_fall_ratio_floor_pct,
            "max_rise_ratio_pct": max_stock_rise_ratio,
            "rise_ratio_floor_pct": stock_rise_ratio_floor_pct,
        },
        "thresholds": {
            "index_drop_floor_pct": index_drop_floor_pct,
            "industry_down_ratio_floor_pct": industry_down_ratio_floor_pct,
            "severe_down_ratio_floor_pct": severe_down_ratio_floor_pct,
            "stock_fall_ratio_floor_pct": stock_fall_ratio_floor_pct,
            "index_rise_floor_pct": index_rise_floor_pct,
            "industry_up_ratio_floor_pct": industry_up_ratio_floor_pct,
            "severe_up_ratio_floor_pct": severe_up_ratio_floor_pct,
            "stock_rise_ratio_floor_pct": stock_rise_ratio_floor_pct,
        },
        "risk_off_advisory": risk_off,
        "risk_on_advisory": risk_on,
        "single_market_risk_off_advisory": single_market_risk_off,
        "single_market_risk_on_advisory": single_market_risk_on,
        "reasons": reasons,
        "risk_on_reasons": risk_on_reasons,
    }


def build_market_weakness_observation(
    summary: dict[str, Any],
    *,
    target_date: str,
    as_of: str,
    source_quality_status: str,
) -> dict[str, Any]:
    """Build a stateless, source-only weakness/recovery observation.

    Alert activation/release streaks are intentionally owned by the notifier.
    This producer only labels one immutable market snapshot and exposes the
    margins needed to audit why a release was or was not eligible.
    """

    hysteresis = resolve_effective_thresholds(
        target_date=datetime.fromisoformat(target_date).date()
    )
    market_indices = (
        summary.get("market_indices")
        if isinstance(summary.get("market_indices"), dict)
        else {}
    )
    index_changes = {
        str(market): change
        for market, row in market_indices.items()
        if isinstance(row, dict)
        for change in [_safe_float(row.get("change_pct"), None)]
        if change is not None
    }
    weighted = (
        summary.get("weighted_market_breadth")
        if isinstance(summary.get("weighted_market_breadth"), dict)
        else {}
    )
    industry = (
        summary.get("industry_breadth")
        if isinstance(summary.get("industry_breadth"), dict)
        else {}
    )
    stock = (
        summary.get("stock_breadth")
        if isinstance(summary.get("stock_breadth"), dict)
        else {}
    )
    thresholds = (
        summary.get("thresholds") if isinstance(summary.get("thresholds"), dict) else {}
    )
    market_states = (
        summary.get("market_states")
        if isinstance(summary.get("market_states"), dict)
        else {}
    )
    affected_markets = sorted(
        {
            str(market)
            for market in summary.get("affected_markets") or []
            if str(market) in {"KOSPI", "KOSDAQ"}
        }
    )
    weighted_index_change = _safe_float(weighted.get("index_change_pct"), None)
    industry_sample_count = _safe_int(industry.get("sample_count"), 0)
    industry_down_ratio = _safe_float(industry.get("down_ratio_pct"), None)
    severe_down_ratio = _safe_float(industry.get("severe_down_ratio_pct"), None)
    max_stock_fall_ratio = _safe_float(stock.get("max_fall_ratio_pct"), None)
    index_drop_floor = _safe_float(
        thresholds.get("index_drop_floor_pct"), DEFAULT_INDEX_DROP_FLOOR_PCT
    )
    industry_down_floor = _safe_float(
        thresholds.get("industry_down_ratio_floor_pct"),
        DEFAULT_INDUSTRY_DOWN_RATIO_FLOOR_PCT,
    )
    severe_down_floor = _safe_float(
        thresholds.get("severe_down_ratio_floor_pct"),
        DEFAULT_SEVERE_DOWN_RATIO_FLOOR_PCT,
    )
    stock_fall_floor = _safe_float(
        thresholds.get("stock_fall_ratio_floor_pct"),
        DEFAULT_STOCK_FALL_RATIO_FLOOR_PCT,
    )
    source_quality_ready = bool(
        source_quality_status == "ok"
        and as_of[:10] == target_date
        and {"KOSPI", "KOSDAQ"}.issubset(index_changes)
        and all(
            isinstance(market_states.get(market), dict)
            and market_states[market].get("source_quality_ready") is True
            for market in ("KOSPI", "KOSDAQ")
        )
        and industry_sample_count >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
        and weighted_index_change is not None
        and industry_down_ratio is not None
        and severe_down_ratio is not None
        and max_stock_fall_ratio is not None
        and index_drop_floor is not None
        and industry_down_floor is not None
        and severe_down_floor is not None
        and stock_fall_floor is not None
    )
    release_thresholds = {
        "each_market_index_above_pct": (
            round(index_drop_floor + MARKET_WEAKNESS_RELEASE_INDEX_MARGIN_PCT, 3)
            if index_drop_floor is not None
            else None
        ),
        "weighted_market_index_above_pct": (
            round(index_drop_floor + MARKET_WEAKNESS_RELEASE_INDEX_MARGIN_PCT, 3)
            if index_drop_floor is not None
            else None
        ),
        "industry_down_ratio_below_pct": (
            round(
                industry_down_floor - MARKET_WEAKNESS_RELEASE_INDUSTRY_MARGIN_PCT,
                3,
            )
            if industry_down_floor is not None
            else None
        ),
        "industry_severe_down_ratio_below_pct": (
            round(
                severe_down_floor - MARKET_WEAKNESS_RELEASE_SEVERE_MARGIN_PCT,
                3,
            )
            if severe_down_floor is not None
            else None
        ),
        "max_stock_fall_ratio_below_pct": (
            round(stock_fall_floor - MARKET_WEAKNESS_RELEASE_STOCK_MARGIN_PCT, 3)
            if stock_fall_floor is not None
            else None
        ),
    }
    release_checks = {
        "each_market_index_recovered": bool(
            source_quality_ready
            and all(
                value > release_thresholds["each_market_index_above_pct"]
                for value in index_changes.values()
            )
        ),
        "weighted_market_index_recovered": bool(
            source_quality_ready
            and weighted_index_change
            > release_thresholds["weighted_market_index_above_pct"]
        ),
        "industry_down_ratio_recovered": bool(
            source_quality_ready
            and industry_down_ratio
            < release_thresholds["industry_down_ratio_below_pct"]
        ),
        "industry_severe_down_ratio_recovered": bool(
            source_quality_ready
            and severe_down_ratio
            < release_thresholds["industry_severe_down_ratio_below_pct"]
        ),
        "stock_fall_ratio_recovered": bool(
            source_quality_ready
            and max_stock_fall_ratio
            < release_thresholds["max_stock_fall_ratio_below_pct"]
        ),
    }
    release_margin_pass = bool(source_quality_ready and all(release_checks.values()))
    market_release_checks: dict[str, dict[str, Any]] = {}
    recovery_evidence_markets: list[str] = []
    for market in ("KOSPI", "KOSDAQ"):
        market_state = (
            market_states.get(market)
            if isinstance(market_states.get(market), dict)
            else {}
        )
        market_industry = (
            market_state.get("industry_breadth")
            if isinstance(market_state.get("industry_breadth"), dict)
            else {}
        )
        market_stock = (
            market_state.get("stock_breadth")
            if isinstance(market_state.get("stock_breadth"), dict)
            else {}
        )
        market_index_change = _safe_float(market_state.get("index_change_pct"), None)
        market_down_ratio = _safe_float(market_industry.get("down_ratio_pct"), None)
        market_severe_ratio = _safe_float(
            market_industry.get("severe_down_ratio_pct"), None
        )
        market_fall_ratio = _safe_float(market_stock.get("fall_ratio_pct"), None)
        listed_count = _safe_int(market_stock.get("listed_count"), 0)
        scoped_industry_ready = (
            _safe_int(market_industry.get("sample_count"), 0)
            >= MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT
        )
        checks = {
            "market_index_recovered": bool(
                market_index_change is not None
                and market_index_change
                > release_thresholds["each_market_index_above_pct"]
            ),
            "industry_down_ratio_recovered": bool(
                scoped_industry_ready
                and market_down_ratio is not None
                and market_down_ratio
                < release_thresholds["industry_down_ratio_below_pct"]
            ),
            "industry_severe_down_ratio_recovered": bool(
                scoped_industry_ready
                and market_severe_ratio is not None
                and market_severe_ratio
                < release_thresholds["industry_severe_down_ratio_below_pct"]
            ),
            "stock_fall_ratio_recovered": bool(
                listed_count <= 0
                or (
                    market_fall_ratio is not None
                    and market_fall_ratio
                    < release_thresholds["max_stock_fall_ratio_below_pct"]
                )
            ),
        }
        market_passed = bool(
            source_quality_ready
            and market_state.get("source_quality_ready") is True
            and all(checks.values())
        )
        if market_passed:
            recovery_evidence_markets.append(market)
        market_release_checks[market] = {
            "passed": market_passed,
            "source_quality_ready": market_state.get("source_quality_ready") is True,
            "checks": checks,
        }
    recovery_evidence_markets.sort()
    if not source_quality_ready:
        raw_state = "UNKNOWN"
    elif bool(summary.get("risk_off_advisory")):
        raw_state = "BROAD_WEAKNESS"
    elif bool(summary.get("single_market_risk_off_advisory")) and affected_markets:
        raw_state = "SINGLE_MARKET_WEAKNESS"
    elif release_margin_pass:
        raw_state = "RECOVERY_EVIDENCE"
    else:
        raw_state = "NEAR_WEAKNESS_BOUNDARY"
    source_candidate_affected_markets = list(affected_markets)
    if raw_state not in {"BROAD_WEAKNESS", "SINGLE_MARKET_WEAKNESS"}:
        affected_markets = []

    evidence = {
        "market_index_change_pct": index_changes,
        "weighted_market_index_change_pct": weighted_index_change,
        "industry_sample_count": industry_sample_count,
        "industry_down_ratio_pct": industry_down_ratio,
        "industry_severe_down_ratio_pct": severe_down_ratio,
        "max_stock_fall_ratio_pct": max_stock_fall_ratio,
        "broad_risk_off_advisory": bool(summary.get("risk_off_advisory")),
        "single_market_risk_off_advisory": bool(
            summary.get("single_market_risk_off_advisory")
        ),
        "affected_markets": affected_markets,
        "source_candidate_affected_markets": source_candidate_affected_markets,
        "market_states": market_states,
        "recovery_evidence_markets": recovery_evidence_markets,
        "risk_on_advisory": bool(summary.get("risk_on_advisory")),
    }
    release_margin = {
        "passed": release_margin_pass,
        "thresholds": release_thresholds,
        "checks": release_checks,
        "markets": market_release_checks,
    }
    identity_source = {
        "target_date": target_date,
        "as_of": as_of,
        "raw_state": raw_state,
        "affected_markets": affected_markets,
        "recovery_evidence_markets": recovery_evidence_markets,
        "source_quality_ready": source_quality_ready,
        "source_quality_status": source_quality_status,
        "evidence": evidence,
        "release_margin": release_margin,
        "hysteresis_policy": hysteresis.observation_contract(),
    }
    observation_id = market_weakness_observation_id(identity_source)
    history_path = _observation_path(target_date, as_of, observation_id)
    return {
        "schema_version": 2,
        "observation_id": observation_id,
        "target_date": target_date,
        "as_of": as_of,
        "raw_state": raw_state,
        "affected_markets": affected_markets,
        "recovery_evidence_markets": recovery_evidence_markets,
        "source_quality_ready": source_quality_ready,
        "source_quality_status": source_quality_status,
        "metric_role": "market_weakness_observation",
        "decision_authority": "source_quality_observation_only",
        "window_policy": "intraday_consecutive_unique_snapshot_hysteresis",
        "sample_floor": {
            "market_index_count": MARKET_WEAKNESS_MIN_MARKET_INDEX_COUNT,
            "industry_row_count": MARKET_WEAKNESS_MIN_INDUSTRY_SAMPLE_COUNT,
            "activation_unique_observations": (
                hysteresis.activation_unique_observations
            ),
            "release_unique_observations": hysteresis.release_unique_observations,
        },
        "primary_decision_metric": "raw_state_with_release_margin",
        "source_quality_gate": "same-session fresh KOSPI/KOSDAQ and industry breadth snapshot",
        "forbidden_uses": REPORT_ONLY_FORBIDDEN_USES
        + [
            "widget_entry_block",
            "episode_entry_block",
            "open_buy_cancel",
            "target_order_cancel",
            "holding_policy_change",
            "price_or_quantity_change",
            "position_exit",
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "evidence": evidence,
        "release_margin": release_margin,
        "hysteresis_policy": hysteresis.observation_contract(),
        "history_path": str(history_path),
        "response_research_contract": {
            "status": "source_only_counterfactual_collection",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "owner_isolation_required": ["main", "widget", "episode"],
            "control": "current_owner_behavior_unchanged",
            "candidate_arms": [
                "delay_new_entry_until_recovery_confirmed",
                "skip_new_entry_during_confirmed_weakness",
                "relative_strength_and_liquidity_exception",
            ],
            "required_outcomes": [
                "cost_adjusted_ev_pct",
                "adverse_first_rate_pct",
                "missed_upside_pct",
                "fill_feasibility_pct",
                "capital_occupation_minutes",
            ],
            "guards": [
                "no_change_to_existing_target_orders",
                "no_forced_exit_or_stop_change",
                "no_quantity_or_price_mutation",
                "owner_specific_evaluation_only",
            ],
        },
    }


def fetch_kiwoom_market_breadth(
    token: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from src.utils import kiwoom_utils

    url = kiwoom_utils.get_api_url("/api/dostk/sect")
    parsed_rows: list[dict[str, Any]] = []
    for inds_cd, source_market in (("001", "KOSPI"), ("101", "KOSDAQ")):
        payloads = kiwoom_utils.fetch_kiwoom_api_continuous(
            url=url,
            token=token,
            api_id="ka20003",
            payload={"inds_cd": inds_cd},
            use_continuous=False,
        )
        parsed_rows.extend(
            parse_kiwoom_industry_rows(payloads, source_market=source_market)
        )
    return parsed_rows, {
        "transport": "kiwoom_rest",
        "endpoint": "/api/dostk/sect",
        "api_ids": ["ka20003"],
        "request_payloads": [{"inds_cd": "001"}, {"inds_cd": "101"}],
        "doc_basis": {
            "rest_api": "https://openapi.kiwoom.com/m/guide/apiguide",
            "official_repository_commit": ("9180debf7aea0074715dd8f7a15af432afbfc403"),
            "official_repository_retrieved_at": "2026-08-31T07:50:26+09:00",
            "official_repository_paths": [
                "kiwoom/_data/kiwoom_api_spec.json#ka20003",
                "examples/국내주식/업종/get_domestic_all_sector_indices.py",
            ],
            "ws_types": ["0J 업종지수", "0U 업종등락"],
        },
    }


def build_market_panic_breadth_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    rows: list[dict[str, Any]] | None = None,
    token: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    as_of = as_of or datetime.now(KST)
    as_of = as_of.replace(tzinfo=KST) if as_of.tzinfo is None else as_of.astimezone(KST)
    errors: list[str] = []
    source = {
        "transport": "injected_rows" if rows is not None else "kiwoom_rest",
        "endpoint": None,
        "api_ids": [],
        "doc_basis": {
            "rest_api": "https://openapi.kiwoom.com/m/guide/apiguide",
            "ws_types": ["0J 업종지수", "0U 업종등락"],
        },
    }
    parsed_rows = list(rows or [])
    if rows is None:
        try:
            if not token:
                from src.utils.kiwoom_utils import get_kiwoom_token

                token = get_kiwoom_token()
            if token:
                parsed_rows, source = fetch_kiwoom_market_breadth(token)
            else:
                errors.append("kiwoom_token_missing")
        except Exception as exc:
            errors.append(f"kiwoom_breadth_fetch_failed:{exc}")
            parsed_rows = []

    summary = summarize_breadth(parsed_rows)
    source_quality_status = "ok" if parsed_rows else "missing_live_breadth_rows"
    if errors:
        source_quality_status = "fetch_error"
    as_of_text = as_of.isoformat(timespec="seconds")
    weakness_observation = build_market_weakness_observation(
        summary,
        target_date=target_date,
        as_of=as_of_text,
        source_quality_status=source_quality_status,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_DIRNAME,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "as_of": as_of_text,
        "dry_run": bool(dry_run),
        "policy": {
            "report_only": True,
            "runtime_effect": "report_only_no_mutation",
            "live_runtime_effect": False,
            "does_not_submit_orders": True,
            "forbidden_uses": REPORT_ONLY_FORBIDDEN_USES,
        },
        "source": source,
        "source_quality": {
            "status": source_quality_status,
            "errors": errors,
            "sample_count": len(parsed_rows),
        },
        "rows": parsed_rows[:300],
        "panic_breadth": summary,
        "market_weakness_observation": weakness_observation,
    }


def write_report(report: dict[str, Any]) -> Path:
    target_date = _safe_str(report.get("target_date")) or datetime.now(KST).strftime(
        "%Y-%m-%d"
    )
    path = _report_path(target_date)
    observation = report.get("market_weakness_observation")
    if isinstance(observation, dict):
        history_path = _observation_path(
            target_date,
            _safe_str(observation.get("as_of")),
            _safe_str(observation.get("observation_id")),
        )
        declared_history_path = Path(_safe_str(observation.get("history_path")))
        if declared_history_path != history_path:
            raise ValueError("market_weakness_history_path_contract_mismatch")
        write_json_object_generation_safe(history_path, observation)
    write_json_object_generation_safe(path, report)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect report-only intraday market panic breadth."
    )
    parser.add_argument(
        "--date", dest="target_date", default=datetime.now(KST).strftime("%Y-%m-%d")
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_market_panic_breadth_report(args.target_date, dry_run=args.dry_run)
    if not args.dry_run:
        write_report(report)
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
