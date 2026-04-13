"""Summarize WATCHING 75 shadow-canary results from pipeline events."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.sniper_missed_entry_counterfactual import build_missed_entry_counterfactual_report
from src.utils.constants import DATA_DIR


SHADOW_REPORT_SCHEMA_VERSION = 1


def _pipeline_events_path(target_date: str, *, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _ratio(numerator: int, denominator: int) -> float:
    return round((float(numerator) / float(denominator)) * 100.0, 1) if denominator > 0 else 0.0


def _load_shadow_rows(target_date: str, *, data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    rows = _load_jsonl(_pipeline_events_path(target_date, data_dir=data_dir))
    items: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("pipeline") or "") != "ENTRY_PIPELINE":
            continue
        if str(row.get("stage") or "") != "watching_prompt_75_shadow":
            continue
        fields = dict(row.get("fields") or {})
        score_band = _safe_int(fields.get("score_band"), -1)
        items.append(
            {
                "emitted_at": str(row.get("emitted_at") or ""),
                "record_id": str(row.get("record_id") or row.get("id") or ""),
                "stock_code": str(row.get("stock_code") or ""),
                "stock_name": str(row.get("stock_name") or ""),
                "main_action": str(fields.get("main_action") or "WAIT").upper(),
                "main_score": round(_safe_float(fields.get("main_score"), 0.0), 1),
                "shadow_action": str(fields.get("shadow_action") or "WAIT").upper(),
                "shadow_score": round(_safe_float(fields.get("shadow_score"), 0.0), 1),
                "buy_diverged": str(fields.get("buy_diverged") or "false").strip().lower() == "true",
                "score_band": score_band,
                "threshold_live": _safe_int(fields.get("threshold_live"), 80),
                "threshold_shadow": _safe_int(fields.get("threshold_shadow"), 75),
                "ai_response_ms": _safe_int(fields.get("ai_response_ms"), 0),
                "ai_prompt_type": str(fields.get("ai_prompt_type") or "-"),
                "ai_result_source": str(fields.get("ai_result_source") or "-"),
            }
        )
    items.sort(key=lambda item: (item["emitted_at"], item["stock_code"], item["record_id"]))
    return items


def _normalize_missed_rows(missed_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(missed_report, dict):
        return []
    rows = []
    for row in list(missed_report.get("rows") or []):
        rows.append(
            {
                "record_id": str(row.get("record_id") or ""),
                "stock_code": str(row.get("stock_code") or ""),
                "stock_name": str(row.get("stock_name") or ""),
                "outcome": str(row.get("outcome") or "NEUTRAL").upper(),
                "terminal_stage": str(row.get("terminal_stage") or ""),
                "close_10m_pct": _safe_float(row.get("close_10m_pct"), 0.0),
                "mfe_10m_pct": _safe_float(row.get("mfe_10m_pct"), 0.0),
                "mae_10m_pct": _safe_float(row.get("mae_10m_pct"), 0.0),
                "estimated_counterfactual_pnl_10m_krw": _safe_int(row.get("estimated_counterfactual_pnl_10m_krw"), 0),
            }
        )
    return rows


def _load_missed_report(
    target_date: str,
    *,
    missed_report_json: str | None = None,
    token: str | None = None,
) -> dict[str, Any] | None:
    if missed_report_json:
        with open(missed_report_json, "r", encoding="utf-8") as handle:
            return json.load(handle)
    try:
        return build_missed_entry_counterfactual_report(target_date, token=token)
    except Exception as exc:
        return {
            "date": target_date,
            "rows": [],
            "meta": {"error": f"{type(exc).__name__}: {exc}"},
        }


def _score_band_distribution(shadow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in shadow_rows:
        buckets[_safe_int(row.get("score_band"), -1)].append(row)

    out: list[dict[str, Any]] = []
    for score_band in sorted(buckets):
        items = buckets[score_band]
        samples = len(items)
        main_buy = sum(1 for item in items if item.get("main_action") == "BUY")
        shadow_buy = sum(1 for item in items if item.get("shadow_action") == "BUY")
        diverged = sum(1 for item in items if bool(item.get("buy_diverged")))
        out.append(
            {
                "score_band": score_band,
                "samples": samples,
                "main_buy": main_buy,
                "shadow_buy": shadow_buy,
                "buy_diverged": diverged,
                "buy_diverged_rate": _ratio(diverged, samples),
                "avg_shadow_score": round(sum(_safe_float(item.get("shadow_score"), 0.0) for item in items) / samples, 1)
                if samples
                else 0.0,
            }
        )
    return out


def _action_matrix(shadow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in shadow_rows:
        counts[(str(row.get("main_action") or "WAIT"), str(row.get("shadow_action") or "WAIT"))] += 1
    return [
        {"main_action": main_action, "shadow_action": shadow_action, "samples": samples}
        for (main_action, shadow_action), samples in sorted(counts.items())
    ]


def _join_shadow_with_missed(
    shadow_rows: list[dict[str, Any]],
    missed_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    missed_map = {
        (str(row.get("record_id") or ""), str(row.get("stock_code") or "")): row
        for row in missed_rows
    }
    joined: list[dict[str, Any]] = []
    for row in shadow_rows:
        key = (str(row.get("record_id") or ""), str(row.get("stock_code") or ""))
        joined.append({**row, **(missed_map.get(key) or {})})
    return joined


def _buy_diverged_crosstab(joined_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[bool, list[dict[str, Any]]] = defaultdict(list)
    for row in joined_rows:
        if str(row.get("outcome") or ""):
            buckets[bool(row.get("buy_diverged"))].append(row)

    out: list[dict[str, Any]] = []
    for diverged in (False, True):
        items = buckets.get(diverged, [])
        if not items:
            continue
        samples = len(items)
        outcome_counts = Counter(str(item.get("outcome") or "NEUTRAL") for item in items)
        out.append(
            {
                "buy_diverged": diverged,
                "samples": samples,
                "MISSED_WINNER": int(outcome_counts.get("MISSED_WINNER", 0)),
                "AVOIDED_LOSER": int(outcome_counts.get("AVOIDED_LOSER", 0)),
                "NEUTRAL": int(outcome_counts.get("NEUTRAL", 0)),
                "missed_winner_rate": _ratio(int(outcome_counts.get("MISSED_WINNER", 0)), samples),
                "avg_close_10m_pct": round(sum(_safe_float(item.get("close_10m_pct"), 0.0) for item in items) / samples, 3),
            }
        )
    return out


def _score_band_outcome_crosstab(joined_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in joined_rows:
        if str(row.get("outcome") or ""):
            buckets[_safe_int(row.get("score_band"), -1)].append(row)

    out: list[dict[str, Any]] = []
    for score_band in sorted(buckets):
        items = buckets[score_band]
        samples = len(items)
        outcome_counts = Counter(str(item.get("outcome") or "NEUTRAL") for item in items)
        out.append(
            {
                "score_band": score_band,
                "samples": samples,
                "MISSED_WINNER": int(outcome_counts.get("MISSED_WINNER", 0)),
                "AVOIDED_LOSER": int(outcome_counts.get("AVOIDED_LOSER", 0)),
                "NEUTRAL": int(outcome_counts.get("NEUTRAL", 0)),
                "missed_winner_rate": _ratio(int(outcome_counts.get("MISSED_WINNER", 0)), samples),
            }
        )
    return out


def build_watching_prompt_75_shadow_report(
    target_date: str,
    *,
    data_dir: Path = DATA_DIR,
    missed_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    shadow_rows = _load_shadow_rows(target_date, data_dir=data_dir)
    missed_rows = _normalize_missed_rows(missed_report)
    joined_rows = _join_shadow_with_missed(shadow_rows, missed_rows)

    diverged_count = sum(1 for row in shadow_rows if bool(row.get("buy_diverged")))
    shadow_buy_count = sum(1 for row in shadow_rows if str(row.get("shadow_action") or "") == "BUY")

    return {
        "date": target_date,
        "metrics": {
            "shadow_samples": len(shadow_rows),
            "shadow_buy_count": shadow_buy_count,
            "buy_diverged_count": diverged_count,
            "buy_diverged_rate": _ratio(diverged_count, len(shadow_rows)),
            "joined_missed_rows": sum(1 for row in joined_rows if str(row.get("outcome") or "")),
        },
        "score_band_distribution": _score_band_distribution(shadow_rows),
        "action_matrix": _action_matrix(shadow_rows),
        "cross_tabs": {
            "buy_diverged_vs_outcome": _buy_diverged_crosstab(joined_rows),
            "score_band_vs_outcome": _score_band_outcome_crosstab(joined_rows),
        },
        "rows": joined_rows,
        "meta": {
            "schema_version": SHADOW_REPORT_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "pipeline_jsonl": str(_pipeline_events_path(target_date, data_dir=data_dir)),
        },
    }


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "- 데이터 없음"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def render_watching_prompt_75_shadow_markdown(report: dict[str, Any]) -> str:
    metrics = dict(report.get("metrics") or {})
    lines = [
        f"# WATCHING 75 Shadow Report ({report.get('date')})",
        "",
        "## 요약",
        f"- shadow_samples: `{metrics.get('shadow_samples', 0)}`",
        f"- shadow_buy_count: `{metrics.get('shadow_buy_count', 0)}`",
        f"- buy_diverged_count: `{metrics.get('buy_diverged_count', 0)}`",
        f"- buy_diverged_rate: `{metrics.get('buy_diverged_rate', 0.0)}%`",
        f"- joined_missed_rows: `{metrics.get('joined_missed_rows', 0)}`",
        "",
        "## 75~79 분포",
        _markdown_table(
            list(report.get("score_band_distribution") or []),
            ["score_band", "samples", "main_buy", "shadow_buy", "buy_diverged", "buy_diverged_rate", "avg_shadow_score"],
        ),
        "",
        "## buy_diverged",
        _markdown_table(
            list(report.get("action_matrix") or []),
            ["main_action", "shadow_action", "samples"],
        ),
        "",
        "## buy_diverged x missed_winner",
        _markdown_table(
            list(((report.get("cross_tabs") or {}).get("buy_diverged_vs_outcome") or [])),
            ["buy_diverged", "samples", "MISSED_WINNER", "AVOIDED_LOSER", "NEUTRAL", "missed_winner_rate", "avg_close_10m_pct"],
        ),
        "",
        "## score_band x missed_winner",
        _markdown_table(
            list(((report.get("cross_tabs") or {}).get("score_band_vs_outcome") or [])),
            ["score_band", "samples", "MISSED_WINNER", "AVOIDED_LOSER", "NEUTRAL", "missed_winner_rate"],
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="WATCHING 75 shadow-canary report")
    parser.add_argument("--date", required=True, help="target date (YYYY-MM-DD)")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="base data dir containing pipeline_events/")
    parser.add_argument("--missed-report-json", default=None)
    parser.add_argument("--json-output", default="")
    parser.add_argument("--markdown-output", default="")
    parser.add_argument("--skip-missed", action="store_true")
    args = parser.parse_args()

    missed_report = None
    if not args.skip_missed:
        missed_report = _load_missed_report(args.date, missed_report_json=args.missed_report_json)

    report = build_watching_prompt_75_shadow_report(
        args.date,
        data_dir=Path(args.data_dir),
        missed_report=missed_report,
    )
    markdown = render_watching_prompt_75_shadow_markdown(report)

    if args.json_output:
        path = Path(args.json_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        path = Path(args.markdown_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")

    print(json.dumps({
        "date": report.get("date"),
        "shadow_samples": (report.get("metrics") or {}).get("shadow_samples", 0),
        "buy_diverged_count": (report.get("metrics") or {}).get("buy_diverged_count", 0),
        "joined_missed_rows": (report.get("metrics") or {}).get("joined_missed_rows", 0),
        "json_output": args.json_output or None,
        "markdown_output": args.markdown_output or None,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
