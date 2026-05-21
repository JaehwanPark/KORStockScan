from __future__ import annotations

import argparse
import json
import math
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, time
from pathlib import Path
from typing import Any

from src.tests.bedrock_nova_lite_shadow import shadow_jsonl_path
from src.utils.jsonl_io import read_jsonl

POST_SELL_DIR = Path("data/post_sell")
REPORT_DIR = Path("data/report/bedrock_nova_lite_one_day_decision")
LITE_ALLOWED_UNDERPERFORMANCE_PCT = 1.0


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


def _normalize_action(value: Any) -> str:
    return str(value or "").strip().upper()


def _profile_bucket(row: dict[str, Any]) -> str:
    endpoint = str(row.get("endpoint_name") or "").strip().lower()
    stage = str(row.get("source_event_stage") or row.get("pipeline_stage") or "").strip().lower()
    if endpoint == "holding_flow" or "holding" in stage:
        return "holding_flow"
    if endpoint == "entry_price" or "entry_price" in stage:
        return "entry_price"
    return "other_tier2"


def _is_tier2_lite_row(row: dict[str, Any]) -> bool:
    if str(row.get("parse_ok")).lower() != "true":
        return False
    if not row.get("openai_action") or not row.get("nova_action"):
        return False
    endpoint = str(row.get("endpoint_name") or "").strip().lower()
    if endpoint in {"manual_bedrock_nova_lite_test", "analyze_target", "overnight"}:
        return False
    model = str(row.get("openai_model") or row.get("model_name") or "gpt-5.4-mini").strip()
    return model in {"", "gpt-5.4-mini", "gpt-5.4-mini-2026-05-21"}


def _load_comparable_shadow_rows(target_date: str) -> list[dict[str, Any]]:
    path = shadow_jsonl_path(target_date)
    rows = read_jsonl(path) if path.exists() else []
    return [row for row in rows if _is_tier2_lite_row(row)]


def _index_evaluations(
    evaluations: list[dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    by_sim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_adm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evaluations:
        sim_id = str(row.get("sim_record_id") or "").strip()
        adm = str(row.get("entry_adm_candidate_id") or "").strip()
        parent = str(row.get("sim_parent_record_id") or "").strip()
        name = str(row.get("stock_name") or "").strip()
        if sim_id:
            by_sim[sim_id].append(row)
        if adm:
            by_adm[adm].append(row)
        if parent:
            by_parent[parent].append(row)
        if name:
            by_name[name].append(row)
    return by_sim, by_adm, by_parent, by_name


def _join_valid_future_evaluation(
    *,
    target_date: str,
    shadow_row: dict[str, Any],
    by_sim: dict[str, list[dict[str, Any]]],
    by_adm: dict[str, list[dict[str, Any]]],
    by_parent: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[str, Any] | None, int]:
    candidates: list[dict[str, Any]] = []
    method = "none"
    sim_id = str(shadow_row.get("sim_record_id") or "").strip()
    adm = str(shadow_row.get("entry_adm_candidate_id") or "").strip()
    parent = str(shadow_row.get("record_id") or shadow_row.get("sim_parent_record_id") or "").strip()
    if sim_id and by_sim.get(sim_id):
        candidates = by_sim[sim_id]
        method = "sim_record_id"
    elif adm and by_adm.get(adm):
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
    name = str(shadow_row.get("symbol") or shadow_row.get("stock_name") or "").strip()
    created_at = _parse_dt(shadow_row.get("created_at"))
    if not name or created_at is None:
        return None
    future: list[tuple[datetime, dict[str, Any]]] = []
    for row in by_name.get(name, []):
        sold_at = _sell_dt(target_date, row)
        if sold_at and sold_at >= created_at:
            future.append((sold_at, row))
    return sorted(future, key=lambda item: item[0])[0][1] if future else None


def _holding_flow_ev_pct(action: str, evaluation: dict[str, Any]) -> float:
    if action == "HOLD":
        return _metric(evaluation, "10m", "close_ret_pct") or 0.0
    if action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return 0.0
    return 0.0


def _entry_price_ev_pct(action: str, evaluation: dict[str, Any]) -> float:
    if action in {"USE_DEFENSIVE", "USE_PASSIVE", "USE_AGGRESSIVE", "USE_MID", "USE_LIMIT"}:
        return _safe_float(evaluation.get("profit_rate")) or 0.0
    return _safe_float(evaluation.get("profit_rate")) or 0.0


def _engine_ev_pct(action: str, profile: str, evaluation: dict[str, Any]) -> float:
    if profile == "holding_flow":
        return _holding_flow_ev_pct(action, evaluation)
    if profile == "entry_price":
        return _entry_price_ev_pct(action, evaluation)
    return _safe_float(evaluation.get("profit_rate")) or 0.0


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _build_profile(
    *,
    target_date: str,
    rows: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
    profile: str,
) -> dict[str, Any]:
    by_sim, by_adm, by_parent, by_name = _index_evaluations(evaluations)
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
            by_sim=by_sim,
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
                            "openai_action": _normalize_action(row.get("openai_action")),
                            "lite_action": _normalize_action(row.get("nova_action")),
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
                    "openai_action": _normalize_action(row.get("openai_action")),
                    "lite_action": _normalize_action(row.get("nova_action")),
                    "sell_time": evaluation.get("sell_time"),
                    "profit_rate": _safe_float(evaluation.get("profit_rate")),
                    "outcome": evaluation.get("outcome"),
                    "join_method": "missing_sim_record_id_weak",
                }
            )
            continue
        if sim_id in seen_sim_ids:
            continue
        openai_action = _normalize_action(row.get("openai_action"))
        lite_action = _normalize_action(row.get("nova_action"))
        openai_ev = _engine_ev_pct(openai_action, profile, evaluation)
        lite_ev = _engine_ev_pct(lite_action, profile, evaluation)
        item = {
            "created_at": row.get("created_at"),
            "endpoint_name": row.get("endpoint_name"),
            "profile": profile,
            "symbol": row.get("symbol"),
            "record_id": row.get("record_id"),
            "entry_adm_candidate_id": row.get("entry_adm_candidate_id"),
            "sim_record_id": sim_id,
            "join_method": method,
            "candidate_count": candidate_count,
            "openai_action": openai_action,
            "openai_score": row.get("openai_score"),
            "lite_action": lite_action,
            "lite_score": row.get("nova_score"),
            "openai_ev_pct": round(openai_ev, 4),
            "lite_ev_pct": round(lite_ev, 4),
            "lite_minus_openai_ev_pct": round(lite_ev - openai_ev, 4),
            "action_pair_bucket": f"{openai_action}->{lite_action}",
            "entry_price_bucket": "entry_price_defensive" if profile == "entry_price" else None,
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
    lite_values = [float(row["lite_ev_pct"]) for row in unique_rows]
    action_pairs = Counter(str(row.get("action_pair_bucket") or "") for row in unique_rows)
    return {
        "profile": profile,
        "source_rows": len(rows),
        "valid_join_rows": len(joined_rows),
        "unique_valid_join_rows": len(unique_rows),
        "prior_only_excluded_count": prior_only_count,
        "unjoined_count": unjoined_count,
        "weak_reference_count": len(weak_reference_rows),
        "weak_reference_rows": weak_reference_rows[:50],
        "join_methods": dict(join_methods),
        "action_pair_counts": {
            f"{openai}->{lite}": count
            for (openai, lite), count in Counter(
                (_normalize_action(row.get("openai_action")), _normalize_action(row.get("nova_action")))
                for row in rows
            ).items()
        },
        "primary_action_pair_counts": dict(action_pairs),
        "openai_source_quality_adjusted_ev_pct": _avg(openai_values),
        "lite_source_quality_adjusted_ev_pct": _avg(lite_values),
        "lite_minus_openai_source_quality_adjusted_ev_pct": round(_avg(lite_values) - _avg(openai_values), 4),
        "lite_profile_underperformance_blocker": bool(
            unique_rows and (_avg(lite_values) < _avg(openai_values) - LITE_ALLOWED_UNDERPERFORMANCE_PCT)
        ),
        "outcome_counts": dict(Counter(str(row.get("outcome") or "unknown") for row in unique_rows)),
        "sample_rows": unique_rows[:50],
        "primary_join_policy": "sim_record_id, entry_adm_candidate_id, or record_id->sim_parent_record_id exact; sell_time >= model decision timestamp; unique sim_record_id",
    }


def _weighted_ev(profiles: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    count = 0
    for profile in profiles:
        rows = int(profile.get("unique_valid_join_rows") or 0)
        total += rows * float(profile.get(key) or 0.0)
        count += rows
    return round(total / count, 4) if count else 0.0


def _choose_winner(profiles: list[dict[str, Any]]) -> tuple[str, str, str, bool]:
    valid = [profile for profile in profiles if int(profile.get("unique_valid_join_rows") or 0) > 0]
    if not valid:
        return "openai", "none", "fail_primary_metric_join_contract", False
    blocked = [profile["profile"] for profile in valid if profile.get("lite_profile_underperformance_blocker")]
    if blocked:
        return "openai", "openai_baseline", f"lite_profile_underperformance_gt_1pct:{','.join(blocked)}", True
    openai_ev = _weighted_ev(valid, "openai_source_quality_adjusted_ev_pct")
    lite_ev = _weighted_ev(valid, "lite_source_quality_adjusted_ev_pct")
    if lite_ev >= openai_ev - LITE_ALLOWED_UNDERPERFORMANCE_PCT:
        return "lite", "tier2_nova_lite_v1", f"lite_within_1pct_or_better diff={lite_ev - openai_ev:.4f}", True
    return "openai", "openai_baseline", f"openai_ev_edge_gt_1pct diff={openai_ev - lite_ev:.4f}", True


def build_decision(target_date: str) -> dict[str, Any]:
    shadow_rows = _load_comparable_shadow_rows(target_date)
    evaluations = read_jsonl(_post_sell_eval_path(target_date)) if _post_sell_eval_path(target_date).exists() else []
    rows_by_profile: dict[str, list[dict[str, Any]]] = {"holding_flow": [], "entry_price": [], "other_tier2": []}
    for row in shadow_rows:
        rows_by_profile.setdefault(_profile_bucket(row), []).append(row)
    profile_results = {
        profile: _build_profile(target_date=target_date, rows=rows, evaluations=evaluations, profile=profile)
        for profile, rows in rows_by_profile.items()
    }
    profiles = list(profile_results.values())
    winner, route_candidate, reason, route_candidate_created = _choose_winner(profiles)
    valid_profiles = [profile for profile in profiles if int(profile.get("unique_valid_join_rows") or 0) > 0]
    openai_ev = _weighted_ev(valid_profiles, "openai_source_quality_adjusted_ev_pct")
    lite_ev = _weighted_ev(valid_profiles, "lite_source_quality_adjusted_ev_pct")
    status = "pass" if route_candidate_created else "fail_primary_metric_join_contract"
    return {
        "report_type": "bedrock_nova_lite_one_day_decision",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision_authority": "one_day_operator_decision_artifact",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_role": "provider_engine_one_day_decision",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "status": status,
        "winner": winner,
        "route_candidate": route_candidate,
        "route_candidate_scope": "gpt-5.4-mini_tier2_all" if route_candidate_created and winner == "lite" else "none",
        "route_candidate_created": route_candidate_created and winner == "lite",
        "winner_reason": reason,
        "lite_allowed_underperformance_pct": LITE_ALLOWED_UNDERPERFORMANCE_PCT,
        "overall": {
            "unique_valid_join_rows": sum(int(profile.get("unique_valid_join_rows") or 0) for profile in profiles),
            "openai_source_quality_adjusted_ev_pct": openai_ev,
            "lite_source_quality_adjusted_ev_pct": lite_ev,
            "lite_minus_openai_source_quality_adjusted_ev_pct": round(lite_ev - openai_ev, 4),
        },
        "source_paths": {
            "shadow_jsonl": str(shadow_jsonl_path(target_date)),
            "sim_post_sell_evaluations": str(_post_sell_eval_path(target_date)),
            "sim_post_sell_candidates": str(_post_sell_candidate_path(target_date)),
        },
        "profile_results": profile_results,
        "next_action": (
            "winner_lite_record_tier2_route_candidate_turn_shadow_off"
            if winner == "lite" and route_candidate_created
            else "winner_openai_keep_openai_turn_lite_shadow_off"
            if route_candidate_created
            else "fail_primary_metric_join_contract"
        ),
        "interpretation_guard": (
            "Do not decide from action exact match count, parse_ok, latency, cost, token/cache savings, "
            "one-dimensional nova_minus_openai score, or all-row action aggregation."
        ),
        "forbidden_uses": [
            "threshold_cycle_ev_auto_apply",
            "runtime_approval_summary_auto_apply",
            "lifecycle_decision_matrix_apply",
            "broker_order_submit",
            "global_provider_route_change_without_approval",
            "intraday_threshold_mutation",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Bedrock Nova Lite One-Day Tier2 Decision - {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- status: `{report['status']}`",
        f"- winner: `{report['winner']}`",
        f"- route_candidate: `{report['route_candidate']}`",
        f"- route_candidate_scope: `{report['route_candidate_scope']}`",
        f"- winner_reason: `{report['winner_reason']}`",
        "",
        "## 근거",
        "",
        (
            "- overall: "
            f"unique_valid_join_rows=`{report['overall']['unique_valid_join_rows']}`, "
            f"openai_ev=`{report['overall']['openai_source_quality_adjusted_ev_pct']}`, "
            f"lite_ev=`{report['overall']['lite_source_quality_adjusted_ev_pct']}`, "
            f"diff=`{report['overall']['lite_minus_openai_source_quality_adjusted_ev_pct']}`"
        ),
    ]
    for profile_name, profile in report["profile_results"].items():
        lines.append(
            f"- {profile_name}: unique_valid_join_rows=`{profile['unique_valid_join_rows']}`, "
            f"openai_ev=`{profile['openai_source_quality_adjusted_ev_pct']}`, "
            f"lite_ev=`{profile['lite_source_quality_adjusted_ev_pct']}`, "
            f"diff=`{profile['lite_minus_openai_source_quality_adjusted_ev_pct']}`, "
            f"underperformance_blocker=`{profile['lite_profile_underperformance_blocker']}`"
        )
    lines.extend(
        [
            f"- source_paths: `{report['source_paths']}`",
            f"- interpretation_guard: `{report['interpretation_guard']}`",
            "",
            "## 다음 액션",
            "",
            f"- `{report['next_action']}`",
            "- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.",
            "- 실제 provider route 변경은 별도 approval/workorder 또는 명시 실행 지시 없이는 적용하지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_decision(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report["target_date"])
    json_path = REPORT_DIR / f"bedrock_nova_lite_one_day_decision_{target_date}.json"
    md_path = REPORT_DIR / f"bedrock_nova_lite_one_day_decision_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build one-day OpenAI vs Bedrock Nova Lite Tier2 decision artifact.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)
    report = build_decision(args.date)
    json_path, md_path = write_decision(report)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "md": str(md_path),
                "status": report["status"],
                "winner": report["winner"],
                "route_candidate": report["route_candidate"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
