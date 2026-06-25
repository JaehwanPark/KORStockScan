"""Report-only stop-loss recovery and pre-sell AVG_DOWN backtest."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "stop_loss_recovery_backtest"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"
SCALE_IN_CF_DIR = DATA_DIR / "report" / "scale_in_incremental_counterfactual"
ASSUMED_AVG_DOWN_RATIO = 0.30

STOP_LOSS_LOGIC_AUDIT_ORDER = [
    "preset_tp_loss_exit",
    "protect_hard_trailing",
    "scalp_hard_soft_stop",
    "mfe_protect",
    "bad_entry",
    "fallback_open_reclaim",
    "swing_probe_sim_exit",
]

FORBIDDEN_USES = [
    "real order enablement",
    "intraday threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "hard/protect/emergency stop delay",
    "broker/order/quantity guard bypass",
]

HARD_SAFETY_TOKENS = (
    "hard_stop",
    "protect_hard",
    "protect_trailing",
    "protect_profit",
    "preset_protect",
    "emergency",
    "daily_limit",
    "limit_up",
)
LOSS_TOKENS = (
    "loss",
    "bad_entry",
    "never_green",
    "retrace",
    "reversal_add_post_eval_fail",
)
CANDIDATE_EXIT_STAGES = {
    "exit_signal",
    "sell_order_sent",
    "sell_completed",
    "scalp_sim_sell_order_assumed_filled",
    "swing_sim_sell_order_assumed_filled",
    "swing_probe_sell_order_assumed_filled",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "null", "none"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "null", "none"):
            return default
        return int(float(value))
    except Exception:
        return default


def _event_path(target_date: str) -> Path:
    return existing_or_gzip_path(PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path or not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def _iter_holding_exit_event_candidates(path: Path) -> Iterable[dict[str, Any]]:
    if not path or not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if "HOLDING_PIPELINE" not in line:
                continue
            if not any(stage in line for stage in CANDIDATE_EXIT_STAGES):
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates: list[str] = []
    current = start
    while current <= end:
        if is_krx_trading_day(current):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _parse_emitted_at(row: dict[str, Any]) -> float:
    text = str(row.get("emitted_at") or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=9)))
        return parsed.timestamp()
    except Exception:
        return 0.0


def _allowed_by_clean_baseline(row: dict[str, Any], policy: dict[str, Any]) -> bool:
    baseline_text = str(policy.get("clean_tuning_baseline_ts_kst") or "")
    if not baseline_text:
        return True
    try:
        baseline = datetime.fromisoformat(baseline_text.replace("Z", "+00:00")).timestamp()
    except Exception:
        return False
    emitted = _parse_emitted_at(row)
    return emitted > 0 and emitted >= baseline


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _exit_rule(row: dict[str, Any]) -> str:
    fields = _fields(row)
    return str(fields.get("exit_rule") or fields.get("last_exit_rule") or "-").strip()


def _sell_reason(row: dict[str, Any]) -> str:
    return str(_fields(row).get("sell_reason_type") or "-").strip().upper()


def _is_non_real(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    return fields.get("actual_order_submitted") is False or fields.get("broker_order_forbidden") is True


def _is_loss_exit(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(value or "").lower()
        for value in (row.get("stage"), _exit_rule(row), _sell_reason(row), _fields(row).get("reason"))
    )
    profit = _safe_float(_fields(row).get("profit_rate"), 0.0)
    return _sell_reason(row) == "LOSS" or profit < 0 or any(token in text for token in LOSS_TOKENS)


def _is_hard_safety_exit(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(value or "").lower()
        for value in (row.get("stage"), _exit_rule(row), _sell_reason(row), _fields(row).get("reason"))
    )
    return any(token in text for token in HARD_SAFETY_TOKENS)


def _exit_family(row: dict[str, Any]) -> str:
    rule = _exit_rule(row).lower()
    strategy = str(_fields(row).get("strategy") or row.get("strategy") or "").upper()
    stage = str(row.get("stage") or "")
    if "preset" in rule:
        return "preset_tp_loss_exit"
    if "hard_stop" in rule or "soft_stop" in rule:
        return "scalp_hard_soft_stop"
    if "mfe_protect" in rule:
        return "mfe_protect"
    if "protect" in rule or "trailing" in rule:
        return "protect_hard_trailing"
    if "bad_entry" in rule:
        return "bad_entry"
    if "open_reclaim" in rule or "scanner_fallback" in rule or "never_green" in rule:
        return "fallback_open_reclaim"
    if stage.startswith("swing_") or strategy in {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}:
        return "swing_probe_sim_exit"
    return "other_loss_exit"


def _evaluation_key(row: dict[str, Any]) -> tuple[str, str]:
    fields = _fields(row)
    record_id = str(row.get("record_id") or fields.get("record_id") or fields.get("recommendation_id") or "").strip()
    sim_id = str(fields.get("sim_record_id") or row.get("sim_record_id") or "").strip()
    if sim_id:
        return "sim", sim_id
    return "real", record_id


def _load_evaluations(target_date: str) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    real_path = existing_or_gzip_path(POST_SELL_DIR / f"post_sell_evaluations_{target_date}.jsonl")
    for row in _iter_jsonl(real_path):
        key = str(row.get("recommendation_id") or row.get("record_id") or "").strip()
        if key:
            result[("real", key)] = row
    sim_path = existing_or_gzip_path(POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl")
    for row in _iter_jsonl(sim_path):
        key = str(row.get("sim_record_id") or "").strip()
        if key:
            result[("sim", key)] = row
    return result


def _metric_for(evaluation: dict[str, Any], horizon: int) -> dict[str, Any]:
    metrics = evaluation.get(f"metrics_{horizon}m")
    return metrics if isinstance(metrics, dict) else {}


def _avg_down_recovery(evaluation: dict[str, Any]) -> dict[str, Any]:
    if not evaluation:
        return {"status": "missing_post_sell_evaluation", "avg_down_recovery_possible": False}
    buy_price = _safe_float(evaluation.get("buy_price"), 0.0)
    sell_price = _safe_float(evaluation.get("sell_price"), 0.0)
    if buy_price <= 0 or sell_price <= 0:
        return {"status": "missing_buy_or_sell_price", "avg_down_recovery_possible": False}
    ratio = ASSUMED_AVG_DOWN_RATIO
    break_even_price = ((buy_price * 1.0) + (sell_price * ratio)) / (1.0 + ratio)
    break_even_from_sell_pct = ((break_even_price / sell_price) - 1.0) * 100.0
    horizon_results = {}
    possible = False
    for horizon in (10, 30, 60):
        metrics = _metric_for(evaluation, horizon)
        if not metrics:
            horizon_results[f"{horizon}m"] = {"status": "missing_horizon"}
            continue
        mfe_pct = _safe_float(metrics.get("mfe_pct"), 0.0)
        close_pct = _safe_float(metrics.get("close_ret_pct"), 0.0)
        recovered = mfe_pct >= break_even_from_sell_pct
        possible = possible or recovered
        horizon_results[f"{horizon}m"] = {
            "mfe_pct": round(mfe_pct, 3),
            "close_ret_pct": round(close_pct, 3),
            "break_even_from_sell_pct": round(break_even_from_sell_pct, 3),
            "avg_down_recovery_possible": recovered,
        }
    return {
        "status": "evaluated",
        "assumed_avg_down_ratio": ratio,
        "break_even_price": round(break_even_price, 3),
        "break_even_from_sell_pct": round(break_even_from_sell_pct, 3),
        "avg_down_recovery_possible": possible,
        "horizons": horizon_results,
    }


def _scale_in_counterfactual_summary(target_date: str) -> dict[str, Any]:
    path = SCALE_IN_CF_DIR / f"scale_in_incremental_counterfactual_{target_date}.json"
    payload = _load_json(path)
    if not payload:
        return {"status": "missing", "path": str(path)}
    return {
        "status": "loaded",
        "path": str(path),
        "summary": payload.get("summary") if isinstance(payload.get("summary"), dict) else {},
        "cohort_count": len(payload.get("cohorts") or []),
    }


def build_report(
    target_date: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    candidate_dates = _date_range(start, end)
    source_dates, excluded_dates = filter_allowed_dates(candidate_dates, policy)
    rows: list[dict[str, Any]] = []
    summary_by_family: dict[str, Counter] = defaultdict(Counter)
    missing_evaluation_count = 0

    for source_date in source_dates:
        evaluations = _load_evaluations(source_date)
        for event in _iter_holding_exit_event_candidates(_event_path(source_date)):
            if not _allowed_by_clean_baseline(event, policy):
                continue
            if str(event.get("pipeline") or "") != "HOLDING_PIPELINE":
                continue
            if str(event.get("stage") or "") not in CANDIDATE_EXIT_STAGES:
                continue
            if not _is_loss_exit(event):
                continue
            family = _exit_family(event)
            hard_safety = _is_hard_safety_exit(event)
            key = _evaluation_key(event)
            evaluation = evaluations.get(key) or {}
            recovery = _avg_down_recovery(evaluation)
            if recovery["status"] != "evaluated":
                missing_evaluation_count += 1
            recovery_possible = bool(recovery.get("avg_down_recovery_possible"))
            summary_by_family[family]["exit_count"] += 1
            summary_by_family[family]["hard_safety_count"] += int(hard_safety)
            summary_by_family[family]["recovery_eligible_count"] += int(not hard_safety)
            summary_by_family[family]["avg_down_recovery_possible_count"] += int(recovery_possible and not hard_safety)
            rows.append(
                {
                    "source_date": source_date,
                    "event_stage": event.get("stage"),
                    "record_id": key[1],
                    "record_key_type": key[0],
                    "stock_code": str(event.get("stock_code") or _fields(event).get("stock_code") or "")[:6],
                    "stock_name": event.get("stock_name") or _fields(event).get("stock_name") or "-",
                    "exit_rule": _exit_rule(event),
                    "sell_reason_type": _sell_reason(event),
                    "profit_rate": _fields(event).get("profit_rate"),
                    "exit_family": family,
                    "hard_safety": hard_safety,
                    "recovery_eligible": not hard_safety,
                    "non_real_observation": _is_non_real(event),
                    "avg_down_recovery": recovery,
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metric_role": "sim_probe_ev",
        "decision_authority": "stop_loss_recovery_forensics_only",
        "window_policy": f"{start}_to_{end}",
        "sample_floor": "report_only_no_hard_decision",
        "primary_decision_metric": "avg_down_recovery_possible_rate",
        "source_quality_gate": "clean_baseline_allowed_pipeline_events_and_post_sell_evaluations",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "stop_loss_logic_audit_order": STOP_LOSS_LOGIC_AUDIT_ORDER,
        "scale_in_counterfactual_sources": {
            source_date: _scale_in_counterfactual_summary(source_date)
            for source_date in source_dates
        },
        "summary": {
            "exit_count": len(rows),
            "missing_post_sell_evaluation_count": missing_evaluation_count,
            "by_exit_family": {
                family: dict(counter)
                for family, counter in sorted(summary_by_family.items())
            },
        },
        "rows": rows,
    }


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Stop Loss Recovery Backtest {report['date']}",
        "",
        f"- runtime_effect: `{report['runtime_effect']}`",
        f"- source_dates: `{', '.join(report.get('source_dates') or []) or '-'}`",
        f"- exit_count: `{report.get('summary', {}).get('exit_count', 0)}`",
        f"- missing_post_sell_evaluation_count: `{report.get('summary', {}).get('missing_post_sell_evaluation_count', 0)}`",
        "",
        "## By Exit Family",
    ]
    for family, row in (report.get("summary", {}).get("by_exit_family") or {}).items():
        lines.append(
            f"- `{family}`: exits={row.get('exit_count', 0)}, "
            f"eligible={row.get('recovery_eligible_count', 0)}, "
            f"recovery_possible={row.get('avg_down_recovery_possible_count', 0)}, "
            f"hard_safety={row.get('hard_safety_count', 0)}"
        )
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(str(report.get("date") or date.today().isoformat()))
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build stop-loss recovery backtest report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print", dest="print_stdout", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_outputs(report)
        print(f"Wrote {json_path}")
        print(f"Wrote {md_path}")
    if args.print_stdout or not args.write:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
