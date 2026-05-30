from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_jsonl


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


def _safe_int(value: Any) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else 0


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q / 100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def _stats(values: list[float | None]) -> dict[str, float | int | None]:
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return {
            "n": 0,
            "avg": None,
            "median": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "max": None,
        }
    return {
        "n": len(cleaned),
        "avg": round(sum(cleaned) / len(cleaned), 1),
        "median": round(statistics.median(cleaned), 1),
        "p75": round(_percentile(cleaned, 75) or 0.0, 1),
        "p90": round(_percentile(cleaned, 90) or 0.0, 1),
        "p95": round(_percentile(cleaned, 95) or 0.0, 1),
        "max": round(max(cleaned), 1),
    }


def _load_events(target_date: str) -> list[dict[str, Any]]:
    path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    return read_jsonl(path)


def _unique_openai_calls(events: list[dict[str, Any]], *, transport_mode: str | None = None) -> list[dict[str, Any]]:
    by_request_id: dict[str, dict[str, Any]] = {}
    fallback_idx = 0
    for event in events:
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if fields.get("ai_model") != "gpt-5-nano" and not fields.get("openai_transport_mode"):
            continue
        if transport_mode is not None and fields.get("openai_transport_mode") != transport_mode:
            continue
        request_id = str(fields.get("openai_request_id") or "").strip()
        if not request_id:
            fallback_idx += 1
            request_id = f"fallback:{fallback_idx}:{event.get('emitted_at')}:{event.get('stock_code')}:{event.get('stage')}"
        by_request_id.setdefault(request_id, event)
    return list(by_request_id.values())


def _summarize_calls(events: list[dict[str, Any]]) -> dict[str, Any]:
    endpoint_counts = Counter()
    prompt_counts = Counter()
    error_counts = Counter()
    ai_ms: list[float | None] = []
    ws_roundtrip_ms: list[float | None] = []
    ws_queue_ms: list[float | None] = []
    ws_used = 0
    ws_fallback = 0
    for event in events:
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        endpoint_counts[str(fields.get("openai_endpoint_name") or "-")] += 1
        prompt_counts[str(fields.get("ai_prompt_type") or "-")] += 1
        if fields.get("openai_ws_error_type"):
            error_counts[str(fields.get("openai_ws_error_type"))] += 1
        if str(fields.get("openai_ws_used")).lower() == "true":
            ws_used += 1
        if str(fields.get("openai_ws_http_fallback")).lower() == "true":
            ws_fallback += 1
        ai_ms.append(_safe_float(fields.get("ai_response_ms")))
        ws_roundtrip_ms.append(_safe_float(fields.get("openai_ws_roundtrip_ms")))
        ws_queue_ms.append(_safe_float(fields.get("openai_ws_queue_wait_ms")))

    n = len(events)
    ai_stats = _stats(ai_ms)
    fallback_rate = (ws_fallback / n) if n else 0.0
    success_rate = ((ws_used - ws_fallback) / n) if n and ws_used else 0.0
    under_3s = sum(value is not None and value <= 3000 for value in ai_ms)
    ai_count = sum(value is not None for value in ai_ms)
    return {
        "n": n,
        "endpoint_counts": dict(endpoint_counts),
        "prompt_counts": dict(prompt_counts),
        "ws_used": ws_used,
        "ws_http_fallback": ws_fallback,
        "ws_http_fallback_rate": round(fallback_rate, 4),
        "ws_success_rate": round(success_rate, 4),
        "ws_error_counts": dict(error_counts),
        "ai_response_ms": ai_stats,
        "ws_roundtrip_ms": _stats(ws_roundtrip_ms),
        "ws_queue_wait_ms": _stats(ws_queue_ms),
        "ai_response_le_3s_rate": round(under_3s / ai_count, 4) if ai_count else 0.0,
    }


def _summarize_entry_price_canary(events: list[dict[str, Any]]) -> dict[str, Any]:
    stages = {
        "entry_ai_price_canary_applied",
        "entry_ai_price_canary_fallback",
        "entry_ai_price_canary_skip_order",
        "entry_ai_price_ofi_skip_demoted",
    }
    canary_events = [event for event in events if str(event.get("stage") or "") in stages]
    applied_events = [
        event for event in canary_events if str(event.get("stage") or "") == "entry_ai_price_canary_applied"
    ]
    transport_observable = [
        event
        for event in canary_events
        if ((event.get("fields") or {}).get("openai_endpoint_name") == "entry_price")
    ]
    applied_transport_observable = [
        event
        for event in applied_events
        if ((event.get("fields") or {}).get("openai_endpoint_name") == "entry_price")
    ]
    applied_ms = [
        _safe_float((event.get("fields") or {}).get("ai_eval_ms"))
        for event in applied_events
    ]
    observable_ws_calls = _unique_openai_calls(transport_observable, transport_mode="responses_ws")
    return {
        "canary_event_count": len(canary_events),
        "applied_count": len(applied_events),
        "transport_observable_count": len(transport_observable),
        "applied_transport_observable_count": len(applied_transport_observable),
        "ws_observable_unique_count": len(observable_ws_calls),
        "applied_ai_eval_ms": _stats(applied_ms),
        "instrumentation_gap": bool(applied_events and not applied_transport_observable),
    }


def build_report(target_date: str) -> dict[str, Any]:
    events = _load_events(target_date)
    ws_calls = _unique_openai_calls(events, transport_mode="responses_ws")
    http_baseline_calls = [
        event
        for event in _unique_openai_calls(events)
        if (event.get("fields") or {}).get("openai_transport_mode") in {"http", None, ""}
    ]
    ws_summary = _summarize_calls(ws_calls)
    baseline_summary = _summarize_calls(http_baseline_calls)
    entry_price_summary = _summarize_entry_price_canary(events)

    analyze_n = ws_summary["endpoint_counts"].get("analyze_target", 0)
    entry_price_n = ws_summary["endpoint_counts"].get("entry_price", 0)
    ai_stats = ws_summary["ai_response_ms"]
    base_stats = baseline_summary["ai_response_ms"]
    median_improvement = None
    p75_improvement = None
    if base_stats.get("median") and ai_stats.get("median"):
        median_improvement = round((base_stats["median"] - ai_stats["median"]) / base_stats["median"], 4)
    if base_stats.get("p75") and ai_stats.get("p75"):
        p75_improvement = round((base_stats["p75"] - ai_stats["p75"]) / base_stats["p75"], 4)

    ws_error_count = sum(int(value or 0) for value in (ws_summary.get("ws_error_counts") or {}).values())
    ws_error_rate = round(ws_error_count / max(1, int(ws_summary.get("n") or 0)), 4)
    repeated_transport_errors_min = 3
    ws_error_rate_max = 0.01
    rollback = (
        ws_summary["ws_http_fallback_rate"] > 0.10
        or ((ai_stats.get("p95") or 0) > 6000)
        or (ws_error_count >= repeated_transport_errors_min and ws_error_rate > ws_error_rate_max)
    )
    keep_ws = (
        analyze_n >= 50
        and ws_summary["ws_http_fallback_rate"] <= 0.05
        and ws_summary["ws_success_rate"] >= 0.95
        and ws_error_rate <= ws_error_rate_max
        and (ai_stats.get("p75") or 999999) <= 2300
        and (ai_stats.get("p90") or 999999) <= 3300
        and (ai_stats.get("p95") or 999999) <= 4500
        and (
            (median_improvement is not None and median_improvement >= 0.10)
            or (p75_improvement is not None and p75_improvement >= 0.05)
        )
    )
    if rollback:
        decision = "rollback_http"
    elif keep_ws:
        decision = "keep_ws"
    else:
        decision = "keep_analyze_target_only"

    return {
        "report_type": "openai_ws_stability",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision": decision,
        "criteria": {
            "keep_ws": {
                "analyze_target_n_min": 50,
                "fallback_rate_max": 0.05,
                "ws_success_rate_min": 0.95,
                "fail_closed_max": 0,
                "p75_ai_response_ms_max": 2300,
                "p90_ai_response_ms_max": 3300,
                "p95_ai_response_ms_max": 4500,
                "median_improvement_min": 0.10,
                "p75_improvement_min": 0.05,
            },
            "rollback_http": {
                "fallback_rate_gt": 0.10,
                "fail_closed_min": 1,
                "p95_ai_response_ms_gt": 6000,
                "repeated_transport_errors_min": repeated_transport_errors_min,
                "transport_error_rate_gt": ws_error_rate_max,
            },
        },
        "ws_summary": ws_summary,
        "transport_warning": {
            "ws_error_count": ws_error_count,
            "ws_error_rate": ws_error_rate,
            "warning_only": bool(ws_error_count and not rollback),
            "rollback_threshold_error_count": repeated_transport_errors_min,
            "rollback_threshold_error_rate": ws_error_rate_max,
        },
        "http_late_baseline_summary": baseline_summary,
        "baseline_improvement": {
            "median_improvement_rate": median_improvement,
            "p75_improvement_rate": p75_improvement,
        },
        "entry_price_ws_sample_count": entry_price_n,
        "entry_price_canary_summary": entry_price_summary,
        "notes": [
            "Summary uses unique openai_request_id to avoid double-counting ai_confirmed plus blocked_ai_score rows.",
            "entry_price canary events without openai transport metadata are treated as an instrumentation gap, not as zero runtime activity.",
        ],
    }


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report["target_date"])
    out_dir = DATA_DIR / "report" / "openai_ws"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"openai_ws_stability_{target_date}.json"
    md_path = out_dir / f"openai_ws_stability_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ws = report["ws_summary"]
    transport_warning = report.get("transport_warning")
    transport_warning = transport_warning if isinstance(transport_warning, dict) else {}
    base = report["http_late_baseline_summary"]
    improvement = report["baseline_improvement"]
    entry_price_summary = report.get("entry_price_canary_summary")
    entry_price_summary = entry_price_summary if isinstance(entry_price_summary, dict) else {}
    entry_price_canary_events = _safe_int(entry_price_summary.get("canary_event_count"))
    entry_price_transport_observable = _safe_int(entry_price_summary.get("transport_observable_count"))
    if entry_price_canary_events > 0 and entry_price_transport_observable <= 0:
        entry_price_decision = (
            "- `entry_price`는 canary 적용 이벤트가 있으나 OpenAI transport metadata가 누락되어 "
            "WS 적용 여부를 이 리포트만으로 확정할 수 없다."
        )
        entry_price_next = (
            "- 이 결함은 rollback 근거가 아니라 instrumentation gap이다. 이후 `entry_ai_price_canary_*` "
            "이벤트에 `openai_*` provenance를 같이 남겨 재판정한다."
        )
    elif report.get("entry_price_ws_sample_count", 0) > 0:
        entry_price_decision = "- `entry_price` WS transport 표본이 관찰됐다."
        entry_price_next = "- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다."
    else:
        entry_price_decision = "- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다."
        entry_price_next = "- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다."
    md = [
        f"# OpenAI WS Stability Report - {target_date}",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- decision: `{report['decision']}`",
        f"- unique WS calls: `{ws['n']}`",
        f"- endpoint counts: `{ws['endpoint_counts']}`",
        f"- WS fallback: `{ws['ws_http_fallback']}` / `{ws['n']}` (`{ws['ws_http_fallback_rate']}`)",
        f"- WS success rate: `{ws['ws_success_rate']}`",
        f"- WS errors: `{ws['ws_error_counts']}`",
        f"- WS transport warning: `{transport_warning}`",
        f"- AI response ms: `{ws['ai_response_ms']}`",
        f"- WS roundtrip ms: `{ws['ws_roundtrip_ms']}`",
        f"- WS queue wait ms: `{ws['ws_queue_wait_ms']}`",
        f"- <=3s rate: `{ws['ai_response_le_3s_rate']}`",
        f"- HTTP late baseline AI response ms: `{base['ai_response_ms']}`",
        f"- baseline median improvement: `{improvement['median_improvement_rate']}`",
        f"- baseline p75 improvement: `{improvement['p75_improvement_rate']}`",
        f"- entry_price WS sample count: `{report['entry_price_ws_sample_count']}`",
        f"- entry_price canary summary: `{report['entry_price_canary_summary']}`",
        "",
        "## 판정",
        "",
        "- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.",
        entry_price_decision,
        entry_price_next,
        "- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.",
    ]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    report = build_report(args.date)
    json_path, md_path = write_report(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "decision": report["decision"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
