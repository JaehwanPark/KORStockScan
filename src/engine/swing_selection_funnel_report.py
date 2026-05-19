"""Swing model selection and live-entry funnel report."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, text

from src.model.common_v2 import (
    RECO_DIAGNOSTIC_JSON_PATH,
    RECO_PATH,
    SWING_SELECTION_OWNER,
)
from src.utils.constants import DATA_DIR, POSTGRES_URL
from src.utils.jsonl_io import read_jsonl


SWING_STRATEGIES = {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}
SWING_EVENT_STAGES = {
    "blocked_swing_gap",
    "blocked_swing_score_vpw",
    "gatekeeper_fast_reuse",
    "gatekeeper_fast_reuse_bypass",
    "blocked_gatekeeper_reject",
    "blocked_gatekeeper_missing",
    "blocked_gatekeeper_error",
    "market_regime_block",
    "market_regime_pass",
    "swing_entry_micro_context_observed",
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_holding_started",
    "swing_sim_order_bundle_assumed_filled",
    "swing_scale_in_micro_context_observed",
    "swing_sim_scale_in_order_assumed_filled",
    "swing_exit_micro_context_observed",
    "holding_flow_ofi_smoothing_applied",
    "swing_sim_sell_order_assumed_filled",
    "swing_sim_sell_blocked_zero_qty",
    "swing_probe_entry_candidate",
    "swing_probe_holding_started",
    "swing_probe_exit_signal",
    "swing_probe_sell_order_assumed_filled",
    "swing_probe_scale_in_order_assumed_filled",
    "swing_probe_discarded",
    "order_bundle_submitted",
    "order_submitted",
    "buy_order_submitted",
}
SUBMITTED_STAGES = {"order_bundle_submitted", "order_submitted", "buy_order_submitted"}
SIMULATED_ORDER_STAGES = {
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_order_bundle_assumed_filled",
    "swing_sim_scale_in_order_assumed_filled",
    "swing_sim_sell_order_assumed_filled",
    "swing_probe_holding_started",
    "swing_probe_sell_order_assumed_filled",
    "swing_probe_scale_in_order_assumed_filled",
}


def _micro_group(stage: str) -> str:
    lowered = stage.lower()
    if "scale_in" in lowered or "pyramid" in lowered or "avg_down" in lowered:
        return "scale_in"
    if "sell" in lowered or "exit" in lowered or "holding_flow_ofi" in lowered:
        return "exit"
    return "entry"


def _micro_summary_item(fields: dict) -> tuple[str, str, dict[str, bool]]:
    state = str(fields.get("orderbook_micro_state") or fields.get("swing_micro_state") or "missing").lower()
    advice = str(fields.get("swing_micro_advice") or "MISSING").upper()
    ready = fields.get("orderbook_micro_ready")
    ready_bool = ready is True or str(ready).strip().lower() in {"1", "true", "yes", "y"}
    healthy = fields.get("orderbook_micro_observer_healthy")
    healthy_bool = healthy is True or str(healthy).strip().lower() in {"1", "true", "yes", "y"}
    stale = fields.get("swing_micro_stale")
    stale_bool = stale is True or str(stale).strip().lower() in {"1", "true", "yes", "y"}
    reason_flags = {
        "micro_missing": advice in {"MISSING", ""} or state in {"", "missing"},
        "micro_stale": stale_bool,
        "observer_unhealthy": not healthy_bool,
        "micro_not_ready": not ready_bool,
        "state_insufficient": state == "insufficient",
    }
    return state, advice, reason_flags


def summarize_ofi_qi_events(events: Iterable[dict]) -> dict:
    state_by_group: dict[str, Counter] = defaultdict(Counter)
    advice_by_group: dict[str, Counter] = defaultdict(Counter)
    exit_smoothing_actions = Counter()
    stale_missing_reasons = Counter()
    stale_missing_reason_combinations = Counter()
    stale_missing_reason_combination_records: dict[str, set[str]] = defaultdict(set)
    stale_missing_groups = Counter()
    stale_missing_group_records: dict[str, set[str]] = defaultdict(set)
    stale_missing_stages = Counter()
    stale_missing_examples: list[dict] = []
    stale_missing_records: set[str] = set()
    observer_unhealthy_total = 0
    observer_unhealthy_with_other = 0
    observer_unhealthy_only = 0
    sample_count = 0
    stale_missing_count = 0

    for event in events:
        if not _is_swing_event(event):
            continue
        fields = _event_fields(event)
        if not any(str(key).startswith(("orderbook_micro_", "swing_micro_")) for key in fields):
            continue
        stage = _event_stage(event)
        group = _micro_group(stage)
        state, advice, reason_flags = _micro_summary_item(fields)
        missing = any(reason_flags.values())
        state_by_group[group][state] += 1
        advice_by_group[group][advice] += 1
        sample_count += 1
        stale_missing_count += int(missing)
        for reason, active in reason_flags.items():
            if active:
                stale_missing_reasons[reason] += 1
        if missing:
            active_reasons = [reason for reason, active in reason_flags.items() if active]
            combination = "+".join(active_reasons) if active_reasons else "unknown"
            record_id = str(event.get("record_id") or "")
            stale_missing_reason_combinations[combination] += 1
            if record_id:
                stale_missing_records.add(record_id)
                stale_missing_reason_combination_records[combination].add(record_id)
                stale_missing_group_records[group].add(record_id)
            stale_missing_groups[group] += 1
            stale_missing_stages[stage] += 1
            if reason_flags.get("observer_unhealthy"):
                observer_unhealthy_total += 1
                if len(active_reasons) > 1:
                    observer_unhealthy_with_other += 1
                else:
                    observer_unhealthy_only += 1
            if len(stale_missing_examples) < 10:
                stale_missing_examples.append(
                    {
                        "record_id": str(event.get("record_id") or ""),
                        "stock_code": str(event.get("stock_code") or ""),
                        "stock_name": str(event.get("stock_name") or ""),
                        "stage": stage,
                        "group": group,
                        "reasons": active_reasons,
                        "orderbook_micro_state": state,
                        "swing_micro_advice": advice,
                    }
                )
        if stage == "holding_flow_ofi_smoothing_applied":
            exit_smoothing_actions[str(fields.get("smoothing_action") or "MISSING").upper()] += 1

    reason_counts = dict(stale_missing_reasons)
    return {
        "sample_count": int(sample_count),
        "stale_missing_count": int(stale_missing_count),
        "stale_missing_unique_record_count": int(len(stale_missing_records)),
        "stale_missing_ratio": round(stale_missing_count / sample_count, 4) if sample_count else 0.0,
        "stale_missing_reason_counts": reason_counts,
        "stale_missing_reason_ratios": {
            reason: round(count / sample_count, 4) if sample_count else 0.0
            for reason, count in reason_counts.items()
        },
        "stale_missing_reason_combination_counts": dict(stale_missing_reason_combinations),
        "stale_missing_reason_combination_unique_record_counts": {
            key: len(values) for key, values in stale_missing_reason_combination_records.items()
        },
        "stale_missing_group_counts": dict(stale_missing_groups),
        "stale_missing_group_unique_record_counts": {
            key: len(values) for key, values in stale_missing_group_records.items()
        },
        "stale_missing_stage_counts": dict(stale_missing_stages),
        "observer_unhealthy_overlap": {
            "observer_unhealthy_total": int(observer_unhealthy_total),
            "observer_unhealthy_with_other_reason": int(observer_unhealthy_with_other),
            "observer_unhealthy_only": int(observer_unhealthy_only),
        },
        "stale_missing_examples": stale_missing_examples,
        "entry_micro_state_counts": dict(state_by_group["entry"]),
        "scale_in_micro_state_counts": dict(state_by_group["scale_in"]),
        "exit_micro_state_counts": dict(state_by_group["exit"]),
        "entry_micro_advice_counts": dict(advice_by_group["entry"]),
        "scale_in_micro_advice_counts": dict(advice_by_group["scale_in"]),
        "exit_micro_advice_counts": dict(advice_by_group["exit"]),
        "exit_smoothing_action_counts": dict(exit_smoothing_actions),
    }


def _date_text(target_date: str | date | datetime) -> str:
    return str(pd.to_datetime(target_date).date())


def _safe_read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl(path: str | Path) -> list[dict]:
    return read_jsonl(Path(path))


def _event_fields(event: dict) -> dict:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _event_stage(event: dict) -> str:
    return str(event.get("stage") or event.get("event") or "").strip()


def _event_strategy(event: dict) -> str:
    fields = _event_fields(event)
    return str(event.get("strategy") or fields.get("strategy") or "").strip().upper()


def _event_identity(event: dict) -> tuple[str, str, str]:
    fields = _event_fields(event)
    record_id = str(event.get("record_id") or fields.get("record_id") or "")
    code = str(event.get("stock_code") or fields.get("stock_code") or fields.get("code") or "")
    name = str(event.get("stock_name") or fields.get("stock_name") or fields.get("name") or "")
    return record_id, code, name


def _is_swing_event(event: dict) -> bool:
    stage = _event_stage(event)
    strategy = _event_strategy(event)
    if strategy in SWING_STRATEGIES:
        return True
    if stage in SUBMITTED_STAGES:
        return False
    return stage in SWING_EVENT_STAGES


def summarize_pipeline_events(events: Iterable[dict]) -> dict:
    events = list(events)
    raw_counts = Counter()
    unique_records = defaultdict(set)
    gatekeeper_actions = Counter()
    by_code_stage = Counter()
    discard_reason_counts = Counter()
    discard_origin_reason_counts = Counter()
    discard_reason_unique = defaultdict(set)
    discard_origin_reason_unique = defaultdict(set)
    discard_by_record = Counter()

    for event in events:
        if not _is_swing_event(event):
            continue
        stage = _event_stage(event)
        if not stage:
            continue

        fields = _event_fields(event)
        identity = _event_identity(event)
        raw_counts[stage] += 1
        unique_records[stage].add(identity)
        by_code_stage[(identity[1], identity[2], stage)] += 1

        if stage == "blocked_gatekeeper_reject":
            gatekeeper_actions[str(fields.get("action", "UNKNOWN") or "UNKNOWN")] += 1
        if stage == "swing_probe_discarded":
            reason = str(fields.get("discard_reason") or "UNKNOWN")
            origin = str(fields.get("probe_origin_stage") or "UNKNOWN")
            discard_reason_counts[reason] += 1
            discard_origin_reason_counts[(origin, reason)] += 1
            discard_reason_unique[reason].add(identity)
            discard_origin_reason_unique[(origin, reason)].add(identity)
            discard_by_record[(identity[0], identity[1], identity[2], origin, reason)] += 1

    key_stages = sorted(set(raw_counts) | SWING_EVENT_STAGES)
    return {
        "raw_counts": {stage: int(raw_counts.get(stage, 0)) for stage in key_stages},
        "unique_record_counts": {
            stage: int(len(unique_records.get(stage, set()))) for stage in key_stages
        },
        "gatekeeper_actions": dict(gatekeeper_actions),
        "top_code_stage": [
            {
                "code": code,
                "name": name,
                "stage": stage,
                "raw_count": int(count),
            }
            for (code, name, stage), count in by_code_stage.most_common(20)
        ],
        "swing_probe_discard_summary": {
            "raw_count": int(raw_counts.get("swing_probe_discarded", 0)),
            "unique_records": int(len(unique_records.get("swing_probe_discarded", set()))),
            "reason_counts": dict(discard_reason_counts),
            "reason_unique_record_counts": {
                reason: int(len(records)) for reason, records in discard_reason_unique.items()
            },
            "origin_reason_counts": {
                f"{origin}:{reason}": int(count)
                for (origin, reason), count in discard_origin_reason_counts.most_common()
            },
            "origin_reason_unique_record_counts": {
                f"{origin}:{reason}": int(len(records))
                for (origin, reason), records in discard_origin_reason_unique.items()
            },
            "top_records": [
                {
                    "record_id": record_id,
                    "code": code,
                    "name": name,
                    "probe_origin_stage": origin,
                    "discard_reason": reason,
                    "raw_count": int(count),
                }
                for (record_id, code, name, origin, reason), count in discard_by_record.most_common(20)
            ],
        },
        "submitted_raw_count": int(sum(raw_counts.get(stage, 0) for stage in SUBMITTED_STAGES)),
        "submitted_unique_records": int(
            len(set().union(*(unique_records.get(stage, set()) for stage in SUBMITTED_STAGES)))
            if any(stage in unique_records for stage in SUBMITTED_STAGES)
            else 0
        ),
        "simulated_order_raw_count": int(
            sum(raw_counts.get(stage, 0) for stage in SIMULATED_ORDER_STAGES)
        ),
        "simulated_order_unique_records": int(
            len(set().union(*(unique_records.get(stage, set()) for stage in SIMULATED_ORDER_STAGES)))
            if any(stage in unique_records for stage in SIMULATED_ORDER_STAGES)
            else 0
        ),
        "ofi_qi_summary": summarize_ofi_qi_events(events),
    }


def summarize_recommendation_rows(rows: Iterable[dict]) -> dict:
    df = pd.DataFrame(list(rows))
    if df.empty:
        return {
            "csv_rows": 0,
            "selection_modes": {},
            "position_tags": {},
            "hybrid_mean_max": 0.0,
            "meta_score_max": 0.0,
        }

    hybrid_mean = (
        pd.to_numeric(df["hybrid_mean"], errors="coerce")
        if "hybrid_mean" in df
        else pd.Series([0] * len(df), dtype=float)
    )
    meta_source = "meta_score" if "meta_score" in df else "score"
    meta_score = (
        pd.to_numeric(df[meta_source], errors="coerce")
        if meta_source in df
        else pd.Series([0] * len(df), dtype=float)
    )

    return {
        "csv_rows": int(len(df)),
        "selection_modes": df.get("selection_mode", pd.Series(dtype=str)).fillna("UNKNOWN").value_counts().to_dict(),
        "position_tags": df.get("position_tag", pd.Series(dtype=str)).fillna("UNKNOWN").value_counts().to_dict(),
        "hybrid_mean_max": float(hybrid_mean.max() or 0.0),
        "meta_score_max": float(meta_score.max() or 0.0),
    }


def summarize_db_rows(rows: Iterable[dict]) -> dict:
    df = pd.DataFrame(list(rows))
    if df.empty:
        return {
            "db_rows": 0,
            "by_position_status": {},
            "entered_rows": 0,
            "submitted_or_open_rows": 0,
        }

    status = df.get("status", pd.Series(dtype=str)).fillna("UNKNOWN").astype(str)
    position = df.get("position_tag", pd.Series(dtype=str)).fillna("UNKNOWN").astype(str)
    by_position_status = Counter(zip(position, status))
    buy_qty = pd.to_numeric(df.get("buy_qty", 0), errors="coerce").fillna(0)
    buy_time_present = df.get("buy_time", pd.Series([None] * len(df))).notna()
    active_status = status.isin(["BUY_ORDERED", "HOLDING", "SELL_ORDERED", "COMPLETED"])

    return {
        "db_rows": int(len(df)),
        "by_position_status": {
            f"{pos}:{stat}": int(count) for (pos, stat), count in sorted(by_position_status.items())
        },
        "entered_rows": int(((buy_qty > 0) | buy_time_present).sum()),
        "submitted_or_open_rows": int(active_status.sum()),
    }


def summarize_recommendation_db_load_gap(
    recommendation_csv: dict,
    db_recommendations: dict,
    diagnostic_summary: dict,
) -> dict:
    csv_rows = int(recommendation_csv.get("csv_rows") or 0)
    db_rows = int(db_recommendations.get("db_rows") or 0)
    db_error = diagnostic_summary.get("db_load_error")
    selection_modes = recommendation_csv.get("selection_modes") or {}

    if db_error:
        reason = "db_load_error"
    elif csv_rows <= 0:
        reason = "no_recommendation_csv_rows"
    elif db_rows > 0:
        reason = "loaded"
    elif selection_modes and not any(
        str(mode).upper() in {"SELECTED", "META_V2", "META_FALLBACK", "EOD_TOP5"}
        for mode in selection_modes
    ):
        reason = "diagnostic_only_recommendation_rows"
    else:
        reason = "csv_rows_positive_db_rows_zero"

    return {
        "csv_rows": csv_rows,
        "db_rows": db_rows,
        "db_load_gap": bool(csv_rows > 0 and db_rows <= 0),
        "db_load_skip_reason": reason,
        "db_load_error": str(db_error) if db_error else None,
        "selection_modes": selection_modes,
    }


def load_recommendation_rows(path: str | Path = RECO_PATH) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    df = pd.read_csv(p)
    return df.to_dict("records")


def load_db_rows(target_date: str, db_url: str = POSTGRES_URL) -> list[dict]:
    engine = create_engine(db_url)
    query = text(
        """
        SELECT rec_date, stock_code, stock_name, strategy, trade_type, position_tag,
               status, prob, buy_price, buy_qty, buy_time
        FROM recommendation_history
        WHERE rec_date = :target_date
          AND strategy IN ('KOSPI_ML', 'KOSDAQ_ML', 'MAIN')
        ORDER BY position_tag, stock_code
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"target_date": target_date})
    return df.to_dict("records")


def build_swing_selection_funnel_report(
    target_date: str | date | datetime,
    *,
    recommendation_rows: Iterable[dict] | None = None,
    diagnostic_summary: dict | None = None,
    db_rows: Iterable[dict] | None = None,
    event_rows: Iterable[dict] | None = None,
    recommendation_path: str | Path = RECO_PATH,
    diagnostic_json_path: str | Path = RECO_DIAGNOSTIC_JSON_PATH,
    db_url: str = POSTGRES_URL,
) -> dict:
    date_key = _date_text(target_date)

    if recommendation_rows is None:
        recommendation_rows = load_recommendation_rows(recommendation_path)
    if diagnostic_summary is None:
        diagnostic_summary = _safe_read_json(diagnostic_json_path)
    if db_rows is None:
        try:
            db_rows = load_db_rows(date_key, db_url=db_url)
        except Exception as exc:
            db_rows = []
            diagnostic_summary = {**diagnostic_summary, "db_load_error": str(exc)}
    if event_rows is None:
        event_path = Path(DATA_DIR) / "pipeline_events" / f"pipeline_events_{date_key}.jsonl"
        event_rows = _read_jsonl(event_path)

    model = {
        "owner": diagnostic_summary.get("owner", SWING_SELECTION_OWNER),
        "selection_mode": diagnostic_summary.get("selection_mode", "UNKNOWN"),
        "selected_count": int(diagnostic_summary.get("selected_count", 0) or 0),
        "floor_bull": diagnostic_summary.get("floor_bull"),
        "floor_bear": diagnostic_summary.get("floor_bear"),
        "fallback_written_to_recommendations": bool(
            diagnostic_summary.get("fallback_written_to_recommendations", False)
        ),
        "latest_stats": diagnostic_summary.get("latest_stats", {}),
        "score_distribution": diagnostic_summary.get("score_distribution", {}),
    }

    recommendation_csv = summarize_recommendation_rows(recommendation_rows)
    db_recommendations = summarize_db_rows(db_rows)

    return {
        "date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "owner": SWING_SELECTION_OWNER,
        "model_selection": model,
        "recommendation_csv": recommendation_csv,
        "db_recommendations": db_recommendations,
        "recommendation_db_load": summarize_recommendation_db_load_gap(
            recommendation_csv,
            db_recommendations,
            diagnostic_summary,
        ),
        "pipeline_events": summarize_pipeline_events(event_rows),
    }


def render_markdown(report: dict) -> str:
    model = report["model_selection"]
    csv = report["recommendation_csv"]
    db = report["db_recommendations"]
    db_load = report.get("recommendation_db_load") or {}
    events = report["pipeline_events"]
    lines = [
        f"# Swing Selection Funnel Report - {report['date']}",
        "",
        f"- owner: `{report['owner']}`",
        f"- selection_mode: `{model.get('selection_mode')}`",
        f"- selected_count: `{model.get('selected_count')}`",
        f"- fallback_written_to_recommendations: `{model.get('fallback_written_to_recommendations')}`",
        f"- csv_rows: `{csv.get('csv_rows')}`",
        f"- db_rows: `{db.get('db_rows')}`",
        f"- db_load_gap: `{db_load.get('db_load_gap')}`",
        f"- db_load_skip_reason: `{db_load.get('db_load_skip_reason')}`",
        f"- entered_rows: `{db.get('entered_rows')}`",
        f"- submitted_unique_records: `{events.get('submitted_unique_records')}`",
        "",
        "## Pipeline Raw vs Unique",
        "",
        "| stage | raw | unique_records |",
        "| --- | ---: | ---: |",
    ]
    raw_counts = events.get("raw_counts", {})
    unique_counts = events.get("unique_record_counts", {})
    for stage in sorted(raw_counts):
        raw = raw_counts.get(stage, 0)
        unique = unique_counts.get(stage, 0)
        if raw or unique:
            lines.append(f"| `{stage}` | {raw} | {unique} |")

    lines.extend(["", "## Top Code Stage", ""])
    for item in events.get("top_code_stage", [])[:10]:
        lines.append(
            f"- `{item.get('stage')}` {item.get('name')}({item.get('code')}): {item.get('raw_count')}"
        )
    ofi_qi = events.get("ofi_qi_summary") or {}
    lines.extend(
        [
            "",
            "## OFI/QI Micro Context",
            "",
            f"- sample_count: `{ofi_qi.get('sample_count', 0)}`",
            f"- stale_missing_unique_record_count: `{ofi_qi.get('stale_missing_unique_record_count', 0)}`",
            f"- stale_missing_ratio: `{ofi_qi.get('stale_missing_ratio', 0.0)}`",
            f"- stale_missing_reason_counts: `{ofi_qi.get('stale_missing_reason_counts', {})}`",
            f"- stale_missing_reason_combination_counts: `{ofi_qi.get('stale_missing_reason_combination_counts', {})}`",
            f"- stale_missing_reason_combination_unique_record_counts: `{ofi_qi.get('stale_missing_reason_combination_unique_record_counts', {})}`",
            f"- stale_missing_group_counts: `{ofi_qi.get('stale_missing_group_counts', {})}`",
            f"- stale_missing_group_unique_record_counts: `{ofi_qi.get('stale_missing_group_unique_record_counts', {})}`",
            f"- observer_unhealthy_overlap: `{ofi_qi.get('observer_unhealthy_overlap', {})}`",
            f"- entry_micro_state_counts: `{ofi_qi.get('entry_micro_state_counts', {})}`",
            f"- scale_in_micro_state_counts: `{ofi_qi.get('scale_in_micro_state_counts', {})}`",
            f"- exit_smoothing_action_counts: `{ofi_qi.get('exit_smoothing_action_counts', {})}`",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def write_swing_selection_funnel_report(
    target_date: str | date | datetime,
    *,
    output_dir: str | Path | None = None,
    **kwargs,
) -> dict:
    date_key = _date_text(target_date)
    report = build_swing_selection_funnel_report(date_key, **kwargs)
    out_dir = Path(output_dir) if output_dir is not None else Path(DATA_DIR) / "report" / "swing_selection_funnel"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"swing_selection_funnel_{date_key}.json"
    md_path = out_dir / f"swing_selection_funnel_{date_key}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    report["paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build swing model selection funnel report")
    parser.add_argument("target_date", nargs="?", default=_date_text(datetime.now()))
    args = parser.parse_args()
    report = write_swing_selection_funnel_report(args.target_date)
    print(json.dumps(report.get("paths", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
