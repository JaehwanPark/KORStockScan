from __future__ import annotations

import argparse
import json
import math
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.tests.bedrock_nova_micro_shadow import shadow_jsonl_path
from src.utils.jsonl_io import read_jsonl

POST_SELL_DIR = Path("data/post_sell")
REPORT_DIR = Path("data/report/bedrock_nova_micro_one_day_decision")
MIN_EDGE_PCT = 0.01


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return numeric
    except Exception:
        return None


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _sell_dt(target_date: str, row: dict[str, Any]) -> datetime | None:
    raw = str(row.get("sell_time") or "").strip()
    if not raw:
        return None
    try:
        parts = [int(part) for part in raw.split(":")[:3]]
        return datetime.combine(datetime.fromisoformat(target_date).date(), time(parts[0], parts[1], parts[2]))
    except Exception:
        return None


def _metric(row: dict[str, Any] | None, window: str, key: str) -> float | None:
    if not isinstance(row, dict):
        return None
    metrics = row.get(f"metrics_{window}")
    if not isinstance(metrics, dict):
        return None
    return _safe_float(metrics.get(key))


def _post_sell_eval_path(target_date: str) -> Path:
    return POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"


def _post_sell_candidate_path(target_date: str) -> Path:
    return POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl"


def _is_entry_watch(row: dict[str, Any]) -> bool:
    stage = str(row.get("source_event_stage") or "unknown").lower()
    endpoint = str(row.get("endpoint_name") or "").lower()
    if stage == "scalp_sim_holding_review":
        return False
    return stage == "watching_analyze_target" or "watch" in stage or endpoint == "analyze_target"


def _is_buy_related(row: dict[str, Any]) -> bool:
    return "BUY" in {
        str(row.get("openai_action") or "").strip().upper(),
        str(row.get("nova_action") or "").strip().upper(),
    }


def _is_holding_continuation(row: dict[str, Any]) -> bool:
    stage = str(row.get("source_event_stage") or "").strip()
    if stage != "scalp_sim_holding_review":
        return False
    actions = {
        str(row.get("openai_action") or "").strip().upper(),
        str(row.get("nova_action") or "").strip().upper(),
    }
    return bool(actions & {"HOLD", "EXIT", "TRIM", "DROP", "SELL"})


def _load_comparable_shadow_rows(target_date: str) -> list[dict[str, Any]]:
    path = shadow_jsonl_path(target_date)
    rows = read_jsonl(path) if path.exists() else []
    comparable: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("parse_ok")).lower() != "true":
            continue
        if str(row.get("model_name") or row.get("openai_model") or "gpt-5-nano") not in {"gpt-5-nano", ""}:
            continue
        if not row.get("openai_action") or not row.get("nova_action"):
            continue
        comparable.append(row)
    return comparable


def _index_evaluations(
    evaluations: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_adm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evaluations:
        adm = str(row.get("entry_adm_candidate_id") or "").strip()
        parent = str(row.get("sim_parent_record_id") or "").strip()
        name = str(row.get("stock_name") or "").strip()
        if adm:
            by_adm[adm].append(row)
        if parent:
            by_parent[parent].append(row)
        if name:
            by_name[name].append(row)
    return by_adm, by_parent, by_name


def _join_valid_future_evaluation(
    *,
    target_date: str,
    shadow_row: dict[str, Any],
    by_adm: dict[str, list[dict[str, Any]]],
    by_parent: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[str, Any] | None, int]:
    candidates: list[dict[str, Any]] = []
    method = "none"
    adm = str(shadow_row.get("entry_adm_candidate_id") or "").strip()
    parent = str(shadow_row.get("record_id") or "").strip()
    if adm and by_adm.get(adm):
        candidates = by_adm[adm]
        method = "entry_adm_candidate_id"
    elif parent and by_parent.get(parent):
        candidates = by_parent[parent]
        method = "record_id_to_sim_parent_record_id"
    if not candidates:
        return method, None, 0
    created_at = _parse_dt(shadow_row.get("created_at"))
    future: list[tuple[datetime, dict[str, Any]]] = []
    for row in candidates:
        sold_at = _sell_dt(target_date, row)
        if created_at and sold_at and sold_at >= created_at:
            future.append((sold_at, row))
    if not future:
        return f"{method}:prior_only", None, len(candidates)
    return method, sorted(future, key=lambda item: item[0])[0][1], len(candidates)


def _weak_future_name_match(
    *,
    target_date: str,
    shadow_row: dict[str, Any],
    by_name: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    name = str(shadow_row.get("symbol") or "").strip()
    created_at = _parse_dt(shadow_row.get("created_at"))
    if not name or created_at is None:
        return None
    future: list[tuple[datetime, dict[str, Any]]] = []
    for row in by_name.get(name, []):
        sold_at = _sell_dt(target_date, row)
        if sold_at and sold_at >= created_at:
            future.append((sold_at, row))
    return sorted(future, key=lambda item: item[0])[0][1] if future else None


def _entry_engine_ev_pct(action: Any, evaluation: dict[str, Any]) -> float:
    if str(action or "").strip().upper() != "BUY":
        return 0.0
    return _safe_float(evaluation.get("profit_rate")) or 0.0


def _holding_engine_ev_pct(action: Any, evaluation: dict[str, Any]) -> float:
    normalized = str(action or "").strip().upper()
    if normalized == "HOLD":
        return _metric(evaluation, "10m", "close_ret_pct") or 0.0
    if normalized in {"EXIT", "TRIM", "DROP", "SELL"}:
        return 0.0
    return 0.0


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _build_scope(
    *,
    target_date: str,
    rows: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
    scope_name: str,
) -> dict[str, Any]:
    by_adm, by_parent, by_name = _index_evaluations(evaluations)
    joined_rows: list[dict[str, Any]] = []
    weak_reference_rows: list[dict[str, Any]] = []
    prior_only_count = 0
    unjoined_count = 0
    join_methods: Counter[str] = Counter()
    seen_sim_ids: OrderedDict[str, dict[str, Any]] = OrderedDict()

    for row in rows:
        method, evaluation, candidate_count = _join_valid_future_evaluation(
            target_date=target_date,
            shadow_row=row,
            by_adm=by_adm,
            by_parent=by_parent,
        )
        join_methods[method] += 1
        if evaluation is None:
            if method.endswith(":prior_only"):
                prior_only_count += 1
            else:
                weak = _weak_future_name_match(target_date=target_date, shadow_row=row, by_name=by_name)
                if weak is not None:
                    weak_reference_rows.append(
                        {
                            "created_at": row.get("created_at"),
                            "symbol": row.get("symbol"),
                            "openai_action": str(row.get("openai_action") or "").strip().upper(),
                            "nova_action": str(row.get("nova_action") or "").strip().upper(),
                            "sim_record_id": weak.get("sim_record_id"),
                            "sell_time": weak.get("sell_time"),
                            "profit_rate": _safe_float(weak.get("profit_rate")),
                            "outcome": weak.get("outcome"),
                            "join_method": "name_nearest_future_sell_weak",
                        }
                    )
                else:
                    unjoined_count += 1
            continue
        sim_id = str(evaluation.get("sim_record_id") or "").strip()
        if not sim_id:
            weak_reference_rows.append(
                {
                    "created_at": row.get("created_at"),
                    "symbol": row.get("symbol"),
                    "openai_action": str(row.get("openai_action") or "").strip().upper(),
                    "nova_action": str(row.get("nova_action") or "").strip().upper(),
                    "sell_time": evaluation.get("sell_time"),
                    "profit_rate": _safe_float(evaluation.get("profit_rate")),
                    "outcome": evaluation.get("outcome"),
                    "join_method": "missing_sim_record_id_weak",
                }
            )
            continue
        if sim_id in seen_sim_ids:
            continue
        openai_action = str(row.get("openai_action") or "").strip().upper()
        nova_action = str(row.get("nova_action") or "").strip().upper()
        if scope_name == "entry_watch_buy":
            openai_ev = _entry_engine_ev_pct(openai_action, evaluation)
            nova_ev = _entry_engine_ev_pct(nova_action, evaluation)
        else:
            openai_ev = _holding_engine_ev_pct(openai_action, evaluation)
            nova_ev = _holding_engine_ev_pct(nova_action, evaluation)
        item = {
            "created_at": row.get("created_at"),
            "symbol": row.get("symbol"),
            "record_id": row.get("record_id"),
            "entry_adm_candidate_id": row.get("entry_adm_candidate_id"),
            "sim_record_id": sim_id,
            "join_method": method,
            "candidate_count": candidate_count,
            "openai_action": openai_action,
            "openai_score": row.get("openai_score"),
            "nova_action": nova_action,
            "nova_score": row.get("nova_score"),
            "openai_ev_pct": round(openai_ev, 4),
            "nova_ev_pct": round(nova_ev, 4),
            "nova_minus_openai_ev_pct": round(nova_ev - openai_ev, 4),
            "profit_rate": _safe_float(evaluation.get("profit_rate")),
            "outcome": evaluation.get("outcome"),
            "sell_time": evaluation.get("sell_time"),
            "exit_rule": evaluation.get("exit_rule"),
            "mfe_10m_pct": _metric(evaluation, "10m", "mfe_pct"),
            "mae_10m_pct": _metric(evaluation, "10m", "mae_pct"),
            "close_10m_pct": _metric(evaluation, "10m", "close_ret_pct"),
            "mfe_60m_pct": _metric(evaluation, "60m", "mfe_pct"),
            "mae_60m_pct": _metric(evaluation, "60m", "mae_pct"),
            "close_60m_pct": _metric(evaluation, "60m", "close_ret_pct"),
        }
        seen_sim_ids[sim_id] = item
        joined_rows.append(item)

    unique_rows = list(seen_sim_ids.values())
    openai_values = [float(row["openai_ev_pct"]) for row in unique_rows]
    nova_values = [float(row["nova_ev_pct"]) for row in unique_rows]
    mae_values = [row["mae_10m_pct"] for row in unique_rows if row.get("mae_10m_pct") is not None]
    missed_upside_count = sum(1 for row in unique_rows if str(row.get("outcome") or "").upper() == "MISSED_UPSIDE")
    return {
        "scope": scope_name,
        "source_rows": len(rows),
        "valid_join_rows": len(joined_rows),
        "unique_valid_join_rows": len(unique_rows),
        "prior_only_excluded_count": prior_only_count,
        "unjoined_count": unjoined_count,
        "weak_reference_count": len(weak_reference_rows),
        "weak_reference_rows": weak_reference_rows[:50],
        "join_methods": dict(join_methods),
        "action_pair_counts": {
            f"{openai}->{nova}": count
            for (openai, nova), count in Counter(
                (str(row.get("openai_action") or "").strip().upper(), str(row.get("nova_action") or "").strip().upper())
                for row in rows
            ).items()
        },
        "openai_source_quality_adjusted_ev_pct": _avg(openai_values),
        "nova_micro_source_quality_adjusted_ev_pct": _avg(nova_values),
        "nova_minus_openai_source_quality_adjusted_ev_pct": round(_avg(nova_values) - _avg(openai_values), 4),
        "avg_mae_10m_pct": _avg([float(value) for value in mae_values]),
        "missed_upside_count": missed_upside_count,
        "outcome_counts": dict(Counter(str(row.get("outcome") or "unknown") for row in unique_rows)),
        "sample_rows": unique_rows[:50],
        "primary_join_policy": "entry_adm_candidate_id exact or record_id->sim_parent_record_id exact, sell_time >= model decision timestamp, unique sim_record_id",
    }


def _choose_scope_winner(scope: dict[str, Any]) -> tuple[str, str]:
    openai_ev = float(scope.get("openai_source_quality_adjusted_ev_pct") or 0.0)
    nova_ev = float(scope.get("nova_micro_source_quality_adjusted_ev_pct") or 0.0)
    diff = nova_ev - openai_ev
    if diff >= MIN_EDGE_PCT:
        return "nova_micro", f"nova_ev_edge_{diff:.4f}_pct"
    if diff <= -MIN_EDGE_PCT:
        return "openai", f"openai_ev_edge_{abs(diff):.4f}_pct"
    if scope.get("scope") == "entry_watch_buy":
        # In near ties, entry chooses the side with lower risk. WAIT has zero MAE exposure.
        return "openai", "entry_tie_breaker_lower_mae_exposure"
    missed = int(scope.get("missed_upside_count") or 0)
    if missed > 0:
        return "nova_micro", "holding_tie_breaker_missed_upside_continuation"
    return "openai", "final_tie_breaker_openai_baseline"


def _scope_decision_summary(scope: dict[str, Any]) -> dict[str, Any]:
    winner, reason = _choose_scope_winner(scope)
    return {
        "scope": scope.get("scope"),
        "winner": winner,
        "reason": reason,
        "unique_valid_join_rows": int(scope.get("unique_valid_join_rows") or 0),
        "openai_source_quality_adjusted_ev_pct": float(scope.get("openai_source_quality_adjusted_ev_pct") or 0.0),
        "nova_micro_source_quality_adjusted_ev_pct": float(
            scope.get("nova_micro_source_quality_adjusted_ev_pct") or 0.0
        ),
        "nova_minus_openai_source_quality_adjusted_ev_pct": float(
            scope.get("nova_minus_openai_source_quality_adjusted_ev_pct") or 0.0
        ),
        "action_pair_counts": scope.get("action_pair_counts") or {},
        "outcome_counts": scope.get("outcome_counts") or {},
    }


def _choose_overall_winner(entry_scope: dict[str, Any], holding_scope: dict[str, Any]) -> tuple[str, str, str]:
    candidates = [entry_scope, holding_scope]
    usable = [scope for scope in candidates if int(scope.get("unique_valid_join_rows") or 0) > 0]
    if not usable:
        return "openai", "openai_baseline", "no_valid_samples_final_tie_breaker_openai_baseline"
    if len(usable) == 1:
        winner, reason = _choose_scope_winner(usable[0])
        profile = "entry_watch_buy_nova_micro_v1" if usable[0].get("scope") == "entry_watch_buy" else "holding_continuation_nova_micro_v1"
        if winner == "openai":
            profile = "openai_baseline"
        return winner, profile, reason
    scope_decisions = {scope["scope"]: _scope_decision_summary(scope) for scope in (entry_scope, holding_scope)}
    entry_decision = scope_decisions.get("entry_watch_buy") or {}
    holding_decision = scope_decisions.get("holding_continuation") or {}
    if entry_decision.get("winner") == "openai" and holding_decision.get("winner") == "nova_micro":
        return (
            "openai",
            "openai_baseline_with_holding_continuation_nova_micro_candidate",
            "split_profile_entry_openai_holding_nova_micro_candidate_no_global_route_change",
        )
    if entry_decision.get("winner") == "nova_micro" and holding_decision.get("winner") == "openai":
        return (
            "openai",
            "openai_baseline_with_entry_watch_buy_nova_micro_candidate",
            "split_profile_entry_nova_micro_holding_openai_candidate_no_global_route_change",
        )
    if entry_decision.get("winner") == holding_decision.get("winner") == "nova_micro":
        entry_diff = abs(float(entry_decision.get("nova_minus_openai_source_quality_adjusted_ev_pct") or 0.0))
        holding_diff = abs(float(holding_decision.get("nova_minus_openai_source_quality_adjusted_ev_pct") or 0.0))
        profile = "entry_watch_buy_nova_micro_v1" if entry_diff >= holding_diff else "holding_continuation_nova_micro_v1"
        return "nova_micro", profile, "both_profiles_nova_micro_ev_edge"
    if entry_decision.get("winner") == holding_decision.get("winner") == "openai":
        return "openai", "openai_baseline", "both_profiles_openai_or_tie_breaker"
    best = max(usable, key=lambda scope: abs(float(scope.get("nova_minus_openai_source_quality_adjusted_ev_pct") or 0.0)))
    winner, reason = _choose_scope_winner(best)
    profile = "entry_watch_buy_nova_micro_v1" if best.get("scope") == "entry_watch_buy" else "holding_continuation_nova_micro_v1"
    if winner == "openai":
        profile = "openai_baseline"
    return winner, profile, reason


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    if start > end:
        start, end = end, start
    days = []
    current = start
    while current <= end:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _merge_scope_results(scope_name: str, daily_scopes: list[dict[str, Any]]) -> dict[str, Any]:
    total_unique = sum(int(scope.get("unique_valid_join_rows") or 0) for scope in daily_scopes)
    openai_weighted = sum(
        float(scope.get("openai_source_quality_adjusted_ev_pct") or 0.0)
        * int(scope.get("unique_valid_join_rows") or 0)
        for scope in daily_scopes
    )
    nova_weighted = sum(
        float(scope.get("nova_micro_source_quality_adjusted_ev_pct") or 0.0)
        * int(scope.get("unique_valid_join_rows") or 0)
        for scope in daily_scopes
    )
    join_methods: Counter[str] = Counter()
    action_pairs: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    sample_rows: list[dict[str, Any]] = []
    weak_rows: list[dict[str, Any]] = []
    for scope in daily_scopes:
        join_methods.update(scope.get("join_methods") or {})
        action_pairs.update(scope.get("action_pair_counts") or {})
        outcomes.update(scope.get("outcome_counts") or {})
        sample_rows.extend(scope.get("sample_rows") or [])
        weak_rows.extend(scope.get("weak_reference_rows") or [])
    openai_ev = round(openai_weighted / total_unique, 4) if total_unique else 0.0
    nova_ev = round(nova_weighted / total_unique, 4) if total_unique else 0.0
    mae_weighted_values = [
        float(scope.get("avg_mae_10m_pct") or 0.0) * int(scope.get("unique_valid_join_rows") or 0)
        for scope in daily_scopes
        if int(scope.get("unique_valid_join_rows") or 0) > 0
    ]
    return {
        "scope": scope_name,
        "source_rows": sum(int(scope.get("source_rows") or 0) for scope in daily_scopes),
        "valid_join_rows": sum(int(scope.get("valid_join_rows") or 0) for scope in daily_scopes),
        "unique_valid_join_rows": total_unique,
        "prior_only_excluded_count": sum(int(scope.get("prior_only_excluded_count") or 0) for scope in daily_scopes),
        "unjoined_count": sum(int(scope.get("unjoined_count") or 0) for scope in daily_scopes),
        "weak_reference_count": sum(int(scope.get("weak_reference_count") or 0) for scope in daily_scopes),
        "weak_reference_rows": weak_rows[:50],
        "join_methods": dict(join_methods),
        "action_pair_counts": dict(action_pairs),
        "openai_source_quality_adjusted_ev_pct": openai_ev,
        "nova_micro_source_quality_adjusted_ev_pct": nova_ev,
        "nova_minus_openai_source_quality_adjusted_ev_pct": round(nova_ev - openai_ev, 4),
        "avg_mae_10m_pct": round(sum(mae_weighted_values) / total_unique, 4) if total_unique else 0.0,
        "missed_upside_count": sum(int(scope.get("missed_upside_count") or 0) for scope in daily_scopes),
        "outcome_counts": dict(outcomes),
        "sample_rows": sample_rows[:50],
        "primary_join_policy": "daily exact joins merged by date; EV is unique-sample weighted across source dates",
    }


def _build_single_day_scopes(target_date: str) -> tuple[dict[str, Any], dict[str, Any]]:
    shadow_rows = _load_comparable_shadow_rows(target_date)
    evaluations = read_jsonl(_post_sell_eval_path(target_date)) if _post_sell_eval_path(target_date).exists() else []
    entry_rows = [row for row in shadow_rows if _is_entry_watch(row) and _is_buy_related(row)]
    holding_rows = [row for row in shadow_rows if _is_holding_continuation(row)]
    entry_scope = _build_scope(target_date=target_date, rows=entry_rows, evaluations=evaluations, scope_name="entry_watch_buy")
    holding_scope = _build_scope(
        target_date=target_date,
        rows=holding_rows,
        evaluations=evaluations,
        scope_name="holding_continuation",
    )
    return entry_scope, holding_scope


def build_decision(target_date: str, *, start_date: str | None = None) -> dict[str, Any]:
    source_dates = _date_range(start_date, target_date) if start_date else [target_date]
    entry_daily: list[dict[str, Any]] = []
    holding_daily: list[dict[str, Any]] = []
    for source_date in source_dates:
        entry_scope, holding_scope = _build_single_day_scopes(source_date)
        entry_scope["source_date"] = source_date
        holding_scope["source_date"] = source_date
        entry_daily.append(entry_scope)
        holding_daily.append(holding_scope)
    entry_scope = (
        _merge_scope_results("entry_watch_buy", entry_daily)
        if len(entry_daily) > 1
        else entry_daily[0]
    )
    holding_scope = (
        _merge_scope_results("holding_continuation", holding_daily)
        if len(holding_daily) > 1
        else holding_daily[0]
    )
    winner, profile, reason = _choose_overall_winner(entry_scope, holding_scope)
    scope_decisions = {
        "entry_watch_buy": _scope_decision_summary(entry_scope),
        "holding_continuation": _scope_decision_summary(holding_scope),
    }
    cumulative = len(source_dates) > 1
    return {
        "report_type": "bedrock_nova_micro_cumulative_decision" if cumulative else "bedrock_nova_micro_one_day_decision",
        "target_date": target_date,
        "start_date": source_dates[0],
        "end_date": target_date,
        "source_dates": source_dates,
        "window_policy": "cumulative" if cumulative else "one_day",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision_authority": (
            "cumulative_operator_decision_artifact"
            if cumulative
            else "one_day_operator_decision_artifact"
        ),
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_role": (
            "provider_engine_cumulative_decision"
            if cumulative
            else "provider_engine_one_day_decision"
        ),
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "winner": winner,
        "winning_profile": profile,
        "winner_reason": reason,
        "scope_decisions": scope_decisions,
        "no_defer_policy": True,
        "min_edge_pct": MIN_EDGE_PCT,
        "source_paths": {
            "shadow_jsonl": [str(shadow_jsonl_path(source_date)) for source_date in source_dates],
            "sim_post_sell_evaluations": [str(_post_sell_eval_path(source_date)) for source_date in source_dates],
            "sim_post_sell_candidates": [str(_post_sell_candidate_path(source_date)) for source_date in source_dates],
        },
        "scope_results": {
            "entry_watch_buy": entry_scope,
            "holding_continuation": holding_scope,
        },
        "next_action": (
            "keep_micro_shadow_collecting_for_profile_split"
            if "candidate" in profile
            else "turn_micro_shadow_off_keep_openai"
            if winner == "openai"
            else f"record_profile_candidate_{profile}_without_global_provider_route_change"
        ),
        "forbidden_uses": [
            "threshold_cycle_ev_auto_apply",
            "runtime_approval_summary_auto_apply",
            "lifecycle_decision_matrix_apply",
            "broker_order_submit",
            "global_provider_route_change",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    entry = report["scope_results"]["entry_watch_buy"]
    holding = report["scope_results"]["holding_continuation"]
    window_policy = str(report.get("window_policy") or "one_day")
    title_prefix = "Bedrock Nova Micro Cumulative Decision" if window_policy == "cumulative" else "Bedrock Nova Micro One-Day Decision"
    lines = [
        f"# {title_prefix} - {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- window_policy: `{window_policy}`",
        f"- source_dates: `{report.get('source_dates')}`",
        f"- winner: `{report['winner']}`",
        f"- winning_profile: `{report['winning_profile']}`",
        f"- winner_reason: `{report['winner_reason']}`",
        f"- no_defer_policy: `{report['no_defer_policy']}`",
        "",
        "## Profile Decisions",
        "",
    ]
    for scope_name, decision in (report.get("scope_decisions") or {}).items():
        lines.extend(
            [
                f"- {scope_name}: winner=`{decision.get('winner')}`, reason=`{decision.get('reason')}`, "
                f"unique_valid_join_rows=`{decision.get('unique_valid_join_rows')}`, "
                f"openai_ev=`{decision.get('openai_source_quality_adjusted_ev_pct')}`, "
                f"nova_micro_ev=`{decision.get('nova_micro_source_quality_adjusted_ev_pct')}`, "
                f"diff=`{decision.get('nova_minus_openai_source_quality_adjusted_ev_pct')}`",
                f"  action_pair_counts: `{decision.get('action_pair_counts')}`",
                f"  outcome_counts: `{decision.get('outcome_counts')}`",
            ]
        )
    lines.extend(
        [
        "",
        "## 근거",
        "",
        (
            "- entry_watch_buy: "
            f"unique_valid_join_rows=`{entry['unique_valid_join_rows']}`, "
            f"openai_ev=`{entry['openai_source_quality_adjusted_ev_pct']}`, "
            f"nova_micro_ev=`{entry['nova_micro_source_quality_adjusted_ev_pct']}`, "
            f"diff=`{entry['nova_minus_openai_source_quality_adjusted_ev_pct']}`"
        ),
        (
            "- holding_continuation: "
            f"unique_valid_join_rows=`{holding['unique_valid_join_rows']}`, "
            f"openai_ev=`{holding['openai_source_quality_adjusted_ev_pct']}`, "
            f"nova_micro_ev=`{holding['nova_micro_source_quality_adjusted_ev_pct']}`, "
            f"diff=`{holding['nova_minus_openai_source_quality_adjusted_ev_pct']}`"
        ),
        f"- source_paths: `{report['source_paths']}`",
        "",
        "## 다음 액션",
        "",
        f"- `{report['next_action']}`",
        "- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.",
        "- global provider route, broker order, threshold mutation 근거로 사용하지 않는다.",
        "",
        ]
    )
    return "\n".join(lines)


def write_decision(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report["target_date"])
    if str(report.get("window_policy") or "") == "cumulative":
        start_date = str(report.get("start_date") or target_date)
        stem = f"bedrock_nova_micro_cumulative_decision_{start_date}_to_{target_date}"
    else:
        stem = f"bedrock_nova_micro_one_day_decision_{target_date}"
    json_path = REPORT_DIR / f"{stem}.json"
    md_path = REPORT_DIR / f"{stem}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build one-day OpenAI vs Bedrock Nova Micro decision artifact.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--start-date", default="")
    args = parser.parse_args(argv)
    report = build_decision(args.date, start_date=args.start_date or None)
    json_path, md_path = write_decision(report)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "md": str(md_path),
                "winner": report["winner"],
                "winning_profile": report["winning_profile"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
