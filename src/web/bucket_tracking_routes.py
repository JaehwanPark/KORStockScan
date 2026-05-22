"""Read-only lifecycle bucket tracking dashboard."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, render_template_string, request

from src.utils.constants import DATA_DIR


bucket_tracking_bp = Blueprint("bucket_tracking", __name__)

DEFAULT_DAYS = 5
MAX_DAYS = 20
DEFAULT_TOP = 200
MAX_TOP = 1000
STAGES = ("entry", "submit", "holding", "scale_in", "exit", "overnight")
BLOCKED_STATES = {
    "blocked_source_quality",
    "blocked_rolling_conflict",
    "runtime_blocked_contract_gap",
}
HUMAN_STATES = {
    "new_bucket_candidate",
    "code_patch_required",
    "automation_handoff_gap",
    "runtime_blocked_contract_gap",
}
STATE_PRIORITY = {
    "live_auto_apply_ready": 0,
    "runtime_blocked_contract_gap": 1,
    "blocked_source_quality": 1,
    "blocked_rolling_conflict": 1,
    "code_patch_required": 2,
    "automation_handoff_gap": 2,
    "new_bucket_candidate": 2,
    "sim_auto_approved": 3,
    "source_only_keep_collecting": 4,
    "bootstrap_pending": 4,
}


def _today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _parse_date(value: str | None) -> str:
    raw = str(value or "").strip() or _today_string()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return _today_string()


def _request_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    value = request.args.get(name, default=default, type=int)
    try:
        number = int(value)
    except Exception:
        number = default
    return max(minimum, min(maximum, number))


def _date_window(end_date: str, days: int) -> list[str]:
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    start = end - timedelta(days=max(1, days) - 1)
    return [(start + timedelta(days=idx)).strftime("%Y-%m-%d") for idx in range(max(1, days))]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        number = float(value)
    except Exception:
        return None
    return number if number == number else None


def _discovery_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json"


def _bridge_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "runtime_apply_bridge" / f"runtime_apply_bridge_{target_date}.json"


def _ldm_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target_date}.json"


def _source_count_from_ldm(ldm: dict[str, Any]) -> int:
    total = 0
    for section in (
        "entry_bucket_attribution",
        "scale_in_bucket_attribution",
        "overnight_bucket_attribution",
    ):
        summary = ldm.get(section, {}).get("summary", {}) if isinstance(ldm.get(section), dict) else {}
        total += _safe_int(summary.get("bucket_count"))
    return total


def _state_group(state: str) -> str:
    if state == "live_auto_apply_ready":
        return "live"
    if state in BLOCKED_STATES:
        return "blocked"
    if state in {"code_patch_required", "automation_handoff_gap", "new_bucket_candidate"}:
        return "human"
    if state == "sim_auto_approved":
        return "sim"
    return "source"


def _candidate_row(target_date: str, item: dict[str, Any]) -> dict[str, Any]:
    state = str(item.get("classification_state") or "source_only_keep_collecting")
    return {
        "date": target_date,
        "row_type": "discovery",
        "bucket_id": str(item.get("bucket_id") or "-"),
        "stage": str(item.get("stage") or "unknown"),
        "bucket_type": str(item.get("bucket_type") or "-"),
        "bucket_key": str(item.get("bucket_key") or "-"),
        "classification_state": state,
        "bridge_candidate_state": "",
        "state_group": _state_group(state),
        "recommended_route": str(item.get("recommended_route") or "-"),
        "recommended_action": str(item.get("recommended_action") or "-"),
        "sample": _safe_int(item.get("sample")),
        "joined_sample": _safe_int(item.get("joined_sample")),
        "ev": _safe_float(item.get("source_quality_adjusted_ev_pct")),
        "source_quality_gate": str(item.get("source_quality_gate") or "-"),
        "live_auto_apply_family": str(item.get("live_auto_apply_family") or "-"),
        "decision_authority": str(item.get("decision_authority") or "-"),
        "runtime_effect": bool(item.get("runtime_effect")),
        "ai_followup": str(item.get("ai_review_followup_required") or "-"),
        "ai_block_reason": str(item.get("ai_review_blocked_reason") or item.get("ai_final_reason") or "-"),
        "blocked_reason": "-",
        "last_seen": target_date,
    }


def _bridge_row(target_date: str, item: dict[str, Any]) -> dict[str, Any]:
    state = str(item.get("bridge_candidate_state") or "bootstrap_pending")
    rolling = item.get("rolling_confirmation") if isinstance(item.get("rolling_confirmation"), dict) else {}
    blocked = []
    if rolling.get("blocked_route"):
        blocked.append(f"route={rolling.get('blocked_route')}")
    if rolling.get("expected_route"):
        blocked.append(f"expected={rolling.get('expected_route')}")
    for branch in ("pyramid", "avg_down"):
        branch_meta = rolling.get(branch) if isinstance(rolling.get(branch), dict) else {}
        if branch_meta.get("blocked_route"):
            blocked.append(f"{branch}:route={branch_meta.get('blocked_route')}")
        if branch_meta.get("expected_route"):
            blocked.append(f"{branch}:expected={branch_meta.get('expected_route')}")
    return {
        "date": target_date,
        "row_type": "bridge",
        "bucket_id": str(item.get("lifecycle_bucket_discovery_bucket_id") or item.get("candidate_id") or item.get("family") or "-"),
        "stage": str(item.get("stage") or "unknown"),
        "bucket_type": "runtime_apply_bridge",
        "bucket_key": ",".join(str(value) for value in item.get("source_bucket_keys") or []) or str(item.get("family") or "-"),
        "classification_state": str(item.get("lifecycle_bucket_discovery_classification_state") or "-"),
        "bridge_candidate_state": state,
        "state_group": _state_group(state),
        "recommended_route": "-",
        "recommended_action": str(item.get("runtime_effect_after_approval") or "-"),
        "sample": 0,
        "joined_sample": 0,
        "ev": None,
        "source_quality_gate": str((rolling or {}).get("lifecycle_bucket_discovery_gate") or "-"),
        "live_auto_apply_family": str(item.get("family") or "-"),
        "decision_authority": str(item.get("decision_authority") or "-"),
        "runtime_effect": bool(item.get("allowed_runtime_apply")),
        "ai_followup": str(item.get("lifecycle_bucket_discovery_ai_followup_required") or "-"),
        "ai_block_reason": str(item.get("lifecycle_bucket_discovery_ai_block_ignored_reason") or "-"),
        "blocked_reason": "; ".join(blocked) or "-",
        "last_seen": target_date,
    }


def _sort_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    state = row.get("bridge_candidate_state") or row.get("classification_state") or ""
    return (
        STATE_PRIORITY.get(str(state), 9),
        -_safe_int(row.get("joined_sample")),
        str(row.get("stage") or ""),
        str(row.get("bucket_id") or ""),
    )


def _row_identity(row: dict[str, Any]) -> str:
    return f"{row.get('row_type')}::{row.get('bucket_id')}"


def _row_state(row: dict[str, Any]) -> str:
    return str(row.get("bridge_candidate_state") or row.get("classification_state") or "")


def _summarize_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("stage") or "unknown"),
            str(row.get("state_group") or "source"),
            str(row.get("bucket_type") or "-"),
        )
        group = groups.setdefault(
            key,
            {
                "stage": key[0],
                "state_group": key[1],
                "bucket_type": key[2],
                "count": 0,
                "joined_sample": 0,
                "changed_count": 0,
                "top_bucket_ids": [],
            },
        )
        group["count"] += 1
        group["joined_sample"] += _safe_int(row.get("joined_sample"))
        if bool(row.get("changed_from_previous")):
            group["changed_count"] += 1
        if len(group["top_bucket_ids"]) < 5:
            group["top_bucket_ids"].append(row.get("bucket_id"))
    return sorted(
        groups.values(),
        key=lambda item: (
            STAGES.index(item["stage"]) if item["stage"] in STAGES else 99,
            STATE_PRIORITY.get(item["state_group"], 8),
            -int(item["count"]),
            item["bucket_type"],
        ),
    )


def build_bucket_tracking_view_model(
    *,
    target_date: str,
    days: int = DEFAULT_DAYS,
    stage_filter: str = "all",
    state_filter: str = "all",
    top: int = DEFAULT_TOP,
) -> dict[str, Any]:
    dates = _date_window(target_date, days)
    rows_by_date: dict[str, list[dict[str, Any]]] = {}
    timeline: list[dict[str, Any]] = []
    missing_dates: list[dict[str, Any]] = []
    current_state_counts: Counter[str] = Counter()
    current_stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    current_source_total = 0
    current_surfaced_total = 0
    current_sim_total = 0
    current_live_total = 0
    current_blocked_total = 0
    current_code_patch_total = 0
    current_human_intervention = False

    for item_date in dates:
        date_rows: list[dict[str, Any]] = []
        discovery = _load_json(_discovery_path(item_date))
        bridge = _load_json(_bridge_path(item_date))
        ldm = _load_json(_ldm_path(item_date))
        missing = []
        if not discovery:
            missing.append("lifecycle_bucket_discovery")
        if not bridge:
            missing.append("runtime_apply_bridge")
        if not ldm:
            missing.append("lifecycle_decision_matrix")
        if missing:
            missing_dates.append({"date": item_date, "missing": missing})

        ldm_source_count = _source_count_from_ldm(ldm)
        discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
        bridge_summary = bridge.get("summary") if isinstance(bridge.get("summary"), dict) else {}
        surfaced_count = _safe_int(discovery_summary.get("surfaced_candidate_count"))
        sim_count = _safe_int(discovery_summary.get("sim_auto_approved_count"))
        live_count = max(
            _safe_int(discovery_summary.get("live_auto_apply_ready_count")),
            _safe_int(bridge_summary.get("live_auto_apply_ready_count")),
        )
        blocked_count = 0
        code_patch_count = _safe_int(discovery_summary.get("code_patch_required_count"))

        candidates = discovery.get("candidates") if isinstance(discovery.get("candidates"), list) else []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            row = _candidate_row(item_date, candidate)
            if row["classification_state"] in BLOCKED_STATES:
                blocked_count += 1
            date_rows.append(row)

        bridge_candidates = bridge.get("candidates") if isinstance(bridge.get("candidates"), list) else []
        for candidate in bridge_candidates:
            if not isinstance(candidate, dict):
                continue
            row = _bridge_row(item_date, candidate)
            if row["bridge_candidate_state"] in BLOCKED_STATES:
                blocked_count += 1
            date_rows.append(row)

        rows_by_date[item_date] = date_rows
        if item_date == target_date:
            current_source_total = ldm_source_count
            current_surfaced_total = surfaced_count
            current_sim_total = sim_count
            current_live_total = live_count
            current_blocked_total = blocked_count
            current_code_patch_total = code_patch_count
            current_human_intervention = (
                bool(discovery_summary.get("human_intervention_required"))
                or bool(bridge_summary.get("human_approval_required"))
                or code_patch_count > 0
            )
            for row in date_rows:
                state = _row_state(row)
                current_state_counts[state] += 1
                current_stage_counts[row["stage"]][state] += 1

        timeline.append(
            {
                "date": item_date,
                "missing": missing,
                "ldm_source_bucket_count": ldm_source_count,
                "surfaced_count": surfaced_count,
                "sim_auto_approved_count": sim_count,
                "live_auto_apply_ready_count": live_count,
                "bridge_candidate_count": _safe_int(bridge_summary.get("candidate_count")),
                "blocked_count": blocked_count,
                "code_patch_required_count": code_patch_count,
                "ai_review_status": discovery_summary.get("ai_two_pass_review_status") or "-",
                "source_contract_status": discovery_summary.get("source_contract_status") or "-",
            }
        )

    previous_rows_by_id: dict[str, dict[str, Any]] = {}
    history_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item_date in dates:
        if item_date >= target_date:
            continue
        for row in rows_by_date.get(item_date, []):
            row_id = _row_identity(row)
            previous_rows_by_id[row_id] = row
            history_by_id[row_id].append(
                {
                    "date": item_date,
                    "state": _row_state(row),
                    "state_group": str(row.get("state_group") or ""),
                }
            )

    filtered_rows = []
    for row in rows_by_date.get(target_date, []):
        row_id = _row_identity(row)
        previous = previous_rows_by_id.get(row_id)
        previous_state = _row_state(previous) if previous else ""
        current_state = _row_state(row)
        row["previous_state"] = previous_state or "-"
        row["first_seen_in_window"] = (history_by_id.get(row_id) or [{"date": target_date}])[0]["date"]
        row["changed_from_previous"] = bool(previous_state and previous_state != current_state)
        row["change_label"] = (
            f"{previous_state} -> {current_state}"
            if row["changed_from_previous"]
            else "new_in_window"
            if not previous_state
            else "unchanged"
        )
        row["history"] = history_by_id.get(row_id, []) + [
            {"date": target_date, "state": current_state, "state_group": str(row.get("state_group") or "")}
        ]
        if stage_filter != "all" and row.get("stage") != stage_filter:
            continue
        row_state = str(row.get("bridge_candidate_state") or row.get("classification_state") or "")
        if state_filter != "all" and row_state != state_filter and row.get("state_group") != state_filter:
            continue
        filtered_rows.append(row)
    filtered_rows = sorted(filtered_rows, key=_sort_key)[:top]

    return {
        "date": target_date,
        "days": days,
        "date_range": {"start": dates[0], "end": dates[-1]},
        "filters": {
            "stage": stage_filter,
            "state": state_filter,
            "top": top,
            "available_stages": ["all", *STAGES],
            "available_states": [
                "all",
                "live",
                "blocked",
                "human",
                "sim",
                "source",
                "live_auto_apply_ready",
                "sim_auto_approved",
                "runtime_blocked_contract_gap",
                "code_patch_required",
                "new_bucket_candidate",
                "source_only_keep_collecting",
                "bootstrap_pending",
            ],
        },
        "summary": {
            "mode": "current_date_with_history",
            "current_date": target_date,
            "history_days": days,
            "ldm_source_bucket_count": current_source_total,
            "surfaced_count": current_surfaced_total,
            "sim_auto_approved_count": current_sim_total,
            "live_auto_apply_ready_count": current_live_total,
            "blocked_count": current_blocked_total,
            "code_patch_required_count": current_code_patch_total,
            "human_intervention_required": current_human_intervention,
            "row_count": len(filtered_rows),
            "state_counts": dict(current_state_counts),
            "changed_count": sum(1 for row in filtered_rows if row.get("changed_from_previous")),
            "new_in_window_count": sum(1 for row in filtered_rows if row.get("change_label") == "new_in_window"),
        },
        "stage_summary": {
            stage: dict(current_stage_counts.get(stage, Counter()))
            for stage in STAGES
        },
        "groups": _summarize_groups(filtered_rows),
        "timeline": timeline,
        "buckets": filtered_rows,
        "missing_dates": missing_dates,
    }


@bucket_tracking_bp.route("/api/bucket-tracking")
def bucket_tracking_api():
    target_date = _parse_date(request.args.get("date"))
    days = _request_int("days", DEFAULT_DAYS, minimum=1, maximum=MAX_DAYS)
    top = _request_int("top", DEFAULT_TOP, minimum=1, maximum=MAX_TOP)
    stage = str(request.args.get("stage") or "all").strip() or "all"
    state = str(request.args.get("state") or "all").strip() or "all"
    return jsonify(
        build_bucket_tracking_view_model(
            target_date=target_date,
            days=days,
            stage_filter=stage,
            state_filter=state,
            top=top,
        )
    )


@bucket_tracking_bp.route("/bucket-tracking")
def bucket_tracking_view():
    target_date = _parse_date(request.args.get("date"))
    days = _request_int("days", DEFAULT_DAYS, minimum=1, maximum=MAX_DAYS)
    top = _request_int("top", DEFAULT_TOP, minimum=1, maximum=MAX_TOP)
    stage = str(request.args.get("stage") or "all").strip() or "all"
    state = str(request.args.get("state") or "all").strip() or "all"
    model = build_bucket_tracking_view_model(
        target_date=target_date,
        days=days,
        stage_filter=stage,
        state_filter=state,
        top=top,
    )
    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>버킷 추적 대시보드</title>
      <style>
        :root {
          --bg: #f8fafc;
          --card: #ffffff;
          --ink: #0f172a;
          --muted: #64748b;
          --line: #d8e0ea;
          --accent: #0053db;
          --ok: #047857;
          --warn: #b45309;
          --bad: #b91c1c;
          --soft: #eef4ff;
        }
        * { box-sizing: border-box; }
        body { margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        .wrap { max-width: 1380px; margin: 0 auto; padding: 22px; }
        .header { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:18px; }
        h1 { margin: 0 0 8px; font-size: 26px; }
        p { margin: 0; color: var(--muted); line-height: 1.55; }
        .filters { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
        input, select, button { border:1px solid var(--line); border-radius:8px; padding:9px 10px; background:#fff; color:var(--ink); font:inherit; }
        button { background:var(--accent); color:#fff; font-weight:700; cursor:pointer; }
        .kpis { display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap:10px; margin-bottom:14px; }
        .card { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px; }
        .label { color:var(--muted); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.03em; }
        .value { font-size:24px; font-weight:800; margin-top:6px; }
        .funnel { display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap:8px; margin-bottom:14px; }
        .funnel .card { min-height:92px; }
        .timeline { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin-bottom:14px; }
        .timeline-date { font-weight:800; margin-bottom:8px; }
        .timeline-grid { display:grid; grid-template-columns: 1fr 1fr; gap:4px 8px; color:var(--muted); font-size:12px; }
        .sections { display:grid; grid-template-columns: 320px 1fr; gap:14px; align-items:start; }
        .group-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:8px; margin-bottom:14px; }
        .group-card { border:1px solid var(--line); border-radius:8px; padding:10px; background:#fbfdff; }
        .group-title { display:flex; justify-content:space-between; gap:8px; align-items:center; font-weight:800; margin-bottom:8px; }
        .group-meta { color:var(--muted); font-size:12px; line-height:1.45; }
        .stage-list { display:grid; gap:8px; }
        .stage-row { display:flex; justify-content:space-between; gap:8px; border-top:1px solid var(--line); padding-top:8px; font-size:13px; }
        table { width:100%; border-collapse:collapse; font-size:12px; }
        th, td { padding:8px 9px; border-top:1px solid var(--line); text-align:left; vertical-align:top; }
        th { color:var(--muted); font-size:11px; text-transform:uppercase; background:#f1f5f9; position:sticky; top:0; }
        .state { display:inline-flex; border-radius:999px; padding:3px 8px; font-weight:800; font-size:11px; background:var(--soft); color:var(--accent); white-space:nowrap; }
        .state.live, .state.sim { background:#dcfce7; color:var(--ok); }
        .state.blocked, .state.human { background:#fee2e2; color:var(--bad); }
        .state.source { background:#fef3c7; color:var(--warn); }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; overflow-wrap:anywhere; }
        .muted { color:var(--muted); }
        .missing { color:var(--bad); font-weight:700; }
        @media (max-width: 980px) {
          .header { flex-direction:column; }
          .filters { justify-content:flex-start; }
          .kpis, .funnel, .sections { grid-template-columns:1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="header">
          <div>
            <h1>버킷 추적 대시보드</h1>
            <p>{{ model.date }} 현재 bucket 상태를 중심으로 보여주고, 최근 {{ model.days }}일 이력은 상태 변화 신호로만 붙입니다.</p>
          </div>
          <form class="filters" method="get" action="/bucket-tracking">
            <input type="date" name="date" value="{{ model.date }}">
            <input type="number" name="days" min="1" max="20" value="{{ model.days }}" title="최근 N일">
            <input type="number" name="top" min="1" max="1000" value="{{ model.filters.top }}" title="상위 표시 개수">
            <select name="stage">
              {% for item in model.filters.available_stages %}
                <option value="{{ item }}" {% if item == model.filters.stage %}selected{% endif %}>stage={{ item }}</option>
              {% endfor %}
            </select>
            <select name="state">
              {% for item in model.filters.available_states %}
                <option value="{{ item }}" {% if item == model.filters.state %}selected{% endif %}>state={{ item }}</option>
              {% endfor %}
            </select>
            <button type="submit">조회</button>
          </form>
        </div>

        <div class="kpis">
          <div class="card"><div class="label">현재 기준일</div><div class="value">{{ model.summary.current_date }}<br><span class="muted">이력 {{ model.days }}일</span></div></div>
          <div class="card"><div class="label">LDM Source Buckets</div><div class="value">{{ model.summary.ldm_source_bucket_count }}</div></div>
          <div class="card"><div class="label">Surfaced</div><div class="value">{{ model.summary.surfaced_count }}</div></div>
          <div class="card"><div class="label">Sim Auto</div><div class="value">{{ model.summary.sim_auto_approved_count }}</div></div>
          <div class="card"><div class="label">Live Ready</div><div class="value">{{ model.summary.live_auto_apply_ready_count }}</div></div>
          <div class="card"><div class="label">Blocked / Code</div><div class="value">{{ model.summary.blocked_count }} / {{ model.summary.code_patch_required_count }}</div></div>
        </div>

        <div class="funnel">
          <div class="card"><div class="label">1. LDM source bucket</div><div class="value">{{ model.summary.ldm_source_bucket_count }}</div><p>entry/scale/overnight bucket source</p></div>
          <div class="card"><div class="label">2. Discovery surfaced</div><div class="value">{{ model.summary.surfaced_count }}</div><p>자동화체인이 표면화한 후보</p></div>
          <div class="card"><div class="label">3. Sim auto</div><div class="value">{{ model.summary.sim_auto_approved_count }}</div><p>실주문 권한 없는 sim policy</p></div>
          <div class="card"><div class="label">4. Bridge candidate</div><div class="value">{{ model.summary.state_counts.get('blocked_source_quality', 0) + model.summary.state_counts.get('bootstrap_pending', 0) + model.summary.live_auto_apply_ready_count }}</div><p>entry/scale live bridge 검토</p></div>
          <div class="card"><div class="label">5. Live ready</div><div class="value">{{ model.summary.live_auto_apply_ready_count }}</div><p>다음 PREOPEN env 후보</p></div>
          <div class="card"><div class="label">6. Follow-up</div><div class="value">{{ model.summary.blocked_count + model.summary.code_patch_required_count }}</div><p>차단 또는 구현 필요</p></div>
        </div>

        <div class="timeline">
          {% for day in model.timeline %}
            <div class="card">
              <div class="timeline-date">{{ day.date }}</div>
              {% if day.missing %}
                <div class="missing">missing: {{ day.missing|join(', ') }}</div>
              {% endif %}
              <div class="timeline-grid">
                <span>LDM</span><strong>{{ day.ldm_source_bucket_count }}</strong>
                <span>surfaced</span><strong>{{ day.surfaced_count }}</strong>
                <span>sim</span><strong>{{ day.sim_auto_approved_count }}</strong>
                <span>live</span><strong>{{ day.live_auto_apply_ready_count }}</strong>
                <span>blocked</span><strong>{{ day.blocked_count }}</strong>
                <span>AI</span><strong>{{ day.ai_review_status }}</strong>
              </div>
            </div>
          {% endfor %}
        </div>

        <div class="card" style="margin-bottom:14px;">
          <h2 style="margin-top:0;font-size:18px;">현재 버킷 그룹</h2>
          <div class="group-grid">
            {% for group in model.groups %}
              <div class="group-card">
                <div class="group-title">
                  <span>{{ group.stage }} / {{ group.bucket_type }}</span>
                  <span class="state {{ group.state_group }}">{{ group.count }}</span>
                </div>
                <div class="group-meta">state={{ group.state_group }}, joined={{ group.joined_sample }}, changed={{ group.changed_count }}</div>
                <div class="group-meta mono">{{ group.top_bucket_ids|join(' · ') }}</div>
              </div>
            {% else %}
              <div class="muted">현재 기준일에 표시할 그룹이 없습니다.</div>
            {% endfor %}
          </div>
        </div>

        <div class="sections">
          <div class="card">
            <h2 style="margin-top:0;font-size:18px;">Stage 요약</h2>
            <div class="stage-list">
              {% for stage, counts in model.stage_summary.items() %}
                <div class="stage-row">
                  <strong>{{ stage }}</strong>
                  <span class="mono">{{ counts }}</span>
                </div>
              {% endfor %}
            </div>
            <p style="margin-top:14px;">human intervention: <strong>{{ 'required' if model.summary.human_intervention_required else 'none' }}</strong></p>
          </div>
          <div class="card">
            <h2 style="margin-top:0;font-size:18px;">현재 상세 버킷</h2>
            <table>
              <thead>
                <tr>
                  <th>state</th><th>change</th><th>stage</th><th>bucket</th><th>route</th><th>sample</th><th>EV</th><th>quality</th><th>live family</th><th>bridge</th><th>follow-up</th>
                </tr>
              </thead>
              <tbody>
                {% for row in model.buckets %}
                  <tr>
                    <td><span class="state {{ row.state_group }}">{{ row.bridge_candidate_state or row.classification_state }}</span></td>
                    <td>{{ row.change_label }}<br><span class="muted">first {{ row.first_seen_in_window }}</span></td>
                    <td>{{ row.stage }}</td>
                    <td><div class="mono">{{ row.bucket_id }}</div><div class="muted">{{ row.bucket_type }} / {{ row.bucket_key }}</div></td>
                    <td>{{ row.recommended_route }}<br><span class="muted">{{ row.recommended_action }}</span></td>
                    <td>{{ row.sample }} / {{ row.joined_sample }}</td>
                    <td>{% if row.ev is not none %}{{ '%.4f'|format(row.ev) }}{% else %}-{% endif %}</td>
                    <td>{{ row.source_quality_gate }}</td>
                    <td class="mono">{{ row.live_auto_apply_family }}</td>
                    <td>{{ row.bridge_candidate_state or '-' }}<br><span class="muted">{{ row.blocked_reason }}</span></td>
                    <td>{{ row.ai_followup }}<br><span class="muted">{{ row.ai_block_reason }}</span></td>
                  </tr>
                {% else %}
                  <tr><td colspan="11" class="muted">조건에 맞는 bucket row가 없습니다.</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(template, model=model)
