"""Generate the next trading day's stage2 checklist from postclose artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import PROJECT_ROOT
from src.utils.market_day import get_krx_trading_day_status

DOCS_DIR = PROJECT_ROOT / "docs"
CHECKLIST_DIR = DOCS_DIR / "checklists"
EV_REPORT_DIR = PROJECT_ROOT / "data" / "report" / "threshold_cycle_ev"
SWING_RUNTIME_APPROVAL_DIR = PROJECT_ROOT / "data" / "report" / "swing_runtime_approval"
CODE_IMPROVEMENT_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "code_improvement_workorder"
)
RUNTIME_APPLY_GAP_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "runtime_apply_gap_audit"
)
TUNING_PERFORMANCE_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "tuning_performance_control_tower"
)
AUTOMATION_TRIGGER_DECISION_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "automation_chain_trigger_decision"
)
RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR = (
    PROJECT_ROOT / "data" / "report" / "rising_missed_scout_workorder"
)
RISING_MISSED_NORMAL_BUY_BRIDGE_CANDIDATE_REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "report"
    / "rising_missed_normal_buy_bridge_candidate_discovery"
)

AUTO_START = "<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->"
AUTO_END = "<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->"
SYNC_COMMAND = (
    "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && "
    "PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar"
)


@dataclass(frozen=True)
class GeneratedTask:
    task_id: str
    title: str
    slot: str
    time_window: str
    track: str
    source: str
    lines: tuple[str, ...]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _missing_required_postclose_artifacts(source_date: str) -> list[Path]:
    required = [
        EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json",
    ]
    return [path for path in required if not path.exists()]


def _has_payload(payload: dict[str, Any]) -> bool:
    return bool(payload)


def _next_krx_trading_day(source_date: str) -> str:
    current = date.fromisoformat(source_date)
    for _ in range(14):
        current += timedelta(days=1)
        is_trading_day, _ = get_krx_trading_day_status(current)
        if is_trading_day:
            return current.isoformat()
    raise RuntimeError(f"could not resolve next KRX trading day after {source_date}")


def _compact_mmdd(target_date: str) -> str:
    return target_date[5:7] + target_date[8:10]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def stage2_checklist_path(target_date: str) -> Path:
    return CHECKLIST_DIR / f"{target_date}-stage2-todo-checklist.md"


def _list_selected_families(ev_report: dict[str, Any]) -> list[str]:
    runtime_apply = (
        ev_report.get("runtime_apply")
        if isinstance(ev_report.get("runtime_apply"), dict)
        else {}
    )
    raw = runtime_apply.get("selected_families")
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _has_runtime_change(ev_report: dict[str, Any]) -> bool:
    runtime_apply = (
        ev_report.get("runtime_apply")
        if isinstance(ev_report.get("runtime_apply"), dict)
        else {}
    )
    return bool(runtime_apply.get("runtime_change")) or bool(
        _list_selected_families(ev_report)
    )


def _has_approval_request(
    ev_report: dict[str, Any], swing_report: dict[str, Any]
) -> bool:
    if (
        isinstance(ev_report.get("approval_requests"), list)
        and ev_report["approval_requests"]
    ):
        return True
    swing_ev = (
        ev_report.get("swing_runtime_approval")
        if isinstance(ev_report.get("swing_runtime_approval"), dict)
        else {}
    )
    for payload in (swing_ev, swing_report):
        if (
            isinstance(payload.get("approval_requests"), list)
            and payload["approval_requests"]
        ):
            return True
        if isinstance(payload.get("requests"), list) and payload["requests"]:
            return True
        summary = (
            payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        )
        requested = payload.get("requested", summary.get("requested", 0))
        try:
            if int(requested or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _has_sim_probe_activity(ev_report: dict[str, Any]) -> bool:
    simulator = (
        ev_report.get("scalp_simulator")
        if isinstance(ev_report.get("scalp_simulator"), dict)
        else {}
    )
    try:
        if int(simulator.get("event_count") or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass
    daily = (
        ev_report.get("daily_ev_summary")
        if isinstance(ev_report.get("daily_ev_summary"), dict)
        else {}
    )
    source_split = (
        daily.get("source_split") if isinstance(daily.get("source_split"), dict) else {}
    )
    for key in ("sim", "probe"):
        payload = (
            source_split.get(key) if isinstance(source_split.get(key), dict) else {}
        )
        try:
            if int(payload.get("sample") or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _code_workorder_count(
    ev_report: dict[str, Any], code_report: dict[str, Any]
) -> int:
    code_ev = (
        ev_report.get("code_improvement_workorder")
        if isinstance(ev_report.get("code_improvement_workorder"), dict)
        else {}
    )
    for payload in (
        (
            code_report.get("summary")
            if isinstance(code_report.get("summary"), dict)
            else {}
        ),
        code_ev,
    ):
        try:
            count = int(payload.get("selected_order_count") or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            return count
    return 0


def _runtime_gap_preopen_pending_items(
    runtime_gap_report: dict[str, Any],
) -> list[dict[str, Any]]:
    if not runtime_gap_report:
        return []
    by_id: dict[str, dict[str, Any]] = {}
    ledger = runtime_gap_report.get("candidate_route_ledger")
    if isinstance(ledger, list):
        for item in ledger:
            if not isinstance(item, dict):
                continue
            candidate_id = str(
                item.get("candidate_id") or item.get("family") or ""
            ).strip()
            if not candidate_id:
                continue
            final_disposition = str(item.get("final_disposition") or "").strip()
            failure_state = str(item.get("failure_state") or "").strip()
            next_stage = str(
                item.get("next_retry_stage") or item.get("preopen_apply_state") or ""
            ).strip()
            if (
                final_disposition == "post_apply_attribution_pending"
                or failure_state == "retry_pending"
                or next_stage == "preopen_apply_candidate"
            ):
                by_id[candidate_id] = item
    retry_queue = runtime_gap_report.get("retry_queue")
    if isinstance(retry_queue, list):
        for item in retry_queue:
            if not isinstance(item, dict):
                continue
            candidate_id = str(item.get("candidate_id") or "").strip()
            if not candidate_id:
                continue
            current = dict(by_id.get(candidate_id) or {})
            current.update(item)
            by_id[candidate_id] = current
    return sorted(
        by_id.values(),
        key=lambda item: str(item.get("candidate_id") or item.get("family") or ""),
    )


def _runtime_gap_preopen_pending_summary(runtime_gap_report: dict[str, Any]) -> str:
    items = _runtime_gap_preopen_pending_items(runtime_gap_report)
    if not items:
        return ""
    rendered = []
    for item in items[:5]:
        candidate_id = str(item.get("candidate_id") or item.get("family") or "-")
        family = str(item.get("family") or "").strip()
        state = str(item.get("failure_state") or item.get("final_disposition") or "-")
        reason = str(
            item.get("failure_reason")
            or item.get("failure_code")
            or item.get("retry_reason")
            or "-"
        )
        if family and family not in candidate_id:
            candidate_id = f"{candidate_id} / family={family}"
        rendered.append(f"`{candidate_id}`({state}, reason={reason})")
    suffix = f" 외 {len(items) - 5}건" if len(items) > 5 else ""
    return ", ".join(rendered) + suffix


def _runtime_gap_codex_directive_summary(runtime_gap_report: dict[str, Any]) -> str:
    directives = runtime_gap_report.get("codex_workorder_directives")
    if not isinstance(directives, list):
        return ""
    rendered: list[str] = []
    for item in directives[:5]:
        if not isinstance(item, dict):
            continue
        directive_type = str(item.get("directive_type") or "-")
        candidate_id = str(item.get("candidate_id") or "-")
        blocking_contract = str(
            item.get("blocking_contract") or item.get("ai_reasoning_summary") or "-"
        )
        rendered.append(f"`{directive_type}`:{candidate_id}(block={blocking_contract})")
    if not rendered:
        return ""
    suffix = f" 외 {len(directives) - 5}건" if len(directives) > 5 else ""
    return ", ".join(rendered) + suffix


def _source_dimension_gap_summary(runtime_gap_report: dict[str, Any]) -> str:
    summary = (
        runtime_gap_report.get("source_dimension_gap_summary")
        if isinstance(runtime_gap_report.get("source_dimension_gap_summary"), dict)
        else {}
    )
    actionable = int(summary.get("actionable_unknown_gap_count") or 0)
    if actionable <= 0:
        return ""
    gap_count = int(summary.get("gap_count") or actionable)
    resolutions = (
        summary.get("recommended_resolution_counts")
        if isinstance(summary.get("recommended_resolution_counts"), dict)
        else {}
    )
    missing_keys = (
        summary.get("missing_dimension_key_counts")
        if isinstance(summary.get("missing_dimension_key_counts"), dict)
        else {}
    )
    return (
        f"actionable_unknown_gap_count=`{actionable}`, source_dimension_gap_count=`{gap_count}`, "
        f"recommended_resolution_counts=`{resolutions}`, missing_dimension_key_counts=`{missing_keys}`"
    )


def _quiet_gap_summary(runtime_gap_report: dict[str, Any]) -> str:
    summary = (
        runtime_gap_report.get("quiet_gap_summary")
        if isinstance(runtime_gap_report.get("quiet_gap_summary"), dict)
        else {}
    )
    quiet_count = int(summary.get("quiet_gap_count") or 0)
    if quiet_count <= 0:
        return ""
    type_counts = (
        summary.get("quiet_gap_type_counts")
        if isinstance(summary.get("quiet_gap_type_counts"), dict)
        else {}
    )
    return (
        f"quiet_gap_count=`{quiet_count}`, rollup_required_count=`{summary.get('rollup_required_count') or 0}`, "
        f"sim_live_connected_quiet_gap_count=`{summary.get('sim_live_connected_quiet_gap_count') or 0}`, "
        f"observation_source_quality_warning_count=`{summary.get('observation_source_quality_warning_count') or 0}`, "
        f"quiet_gap_type_counts=`{type_counts}`"
    )


def _rising_missed_scout_summary(rising_missed_report: dict[str, Any]) -> str:
    if not rising_missed_report:
        return "report_missing_or_unreadable"
    summary = (
        rising_missed_report.get("summary")
        if isinstance(rising_missed_report.get("summary"), dict)
        else {}
    )
    order_count = summary.get("code_improvement_order_count")
    if order_count is None:
        orders = rising_missed_report.get("code_improvement_orders")
        order_count = len(orders) if isinstance(orders, list) else 0
    return (
        f"code_improvement_order_count=`{order_count}`, "
        f"forced_scout_with_post_sell_count=`{summary.get('forced_scout_with_post_sell_count') or 0}`, "
        f"profitable_forced_scout_count=`{summary.get('profitable_forced_scout_count') or 0}`, "
        f"loss_or_flat_forced_scout_count=`{summary.get('loss_or_flat_forced_scout_count') or 0}`, "
        f"current_missed_count=`{summary.get('current_missed_count') or 0}`"
    )


def _rising_missed_normal_buy_bridge_summary(bridge_report: dict[str, Any]) -> str:
    if not bridge_report:
        return "report_missing_or_unreadable"
    summary = (
        bridge_report.get("summary")
        if isinstance(bridge_report.get("summary"), dict)
        else {}
    )
    return (
        f"status=`{summary.get('status') or 'unknown'}`, "
        f"bridge_candidate_count=`{summary.get('bridge_candidate_count') or 0}`, "
        f"code_improvement_order_count=`{summary.get('code_improvement_order_count') or 0}`, "
        f"runtime_env_key=`{summary.get('runtime_env_key') or 'KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED'}`"
    )


def _automation_trigger_decision_summary(trigger_report: dict[str, Any]) -> str:
    if not trigger_report:
        return "trigger_report_missing=`true`, required_action=`run_required_or_report_generation_check`"

    summary = (
        trigger_report.get("summary")
        if isinstance(trigger_report.get("summary"), dict)
        else {}
    )
    decisions = (
        trigger_report.get("decisions")
        if isinstance(trigger_report.get("decisions"), list)
        else []
    )
    reason_counts: dict[str, int] = {}
    run_steps: list[str] = []
    skip_steps: list[str] = []
    source_missing_steps: list[str] = []
    for raw_decision in decisions:
        if not isinstance(raw_decision, dict):
            continue
        step_id = str(raw_decision.get("step_id") or "").strip()
        decision = str(raw_decision.get("decision") or "").strip()
        if step_id and decision == "run":
            run_steps.append(step_id)
        elif step_id and decision == "skip":
            skip_steps.append(step_id)
        if step_id and raw_decision.get("source_missing") is True:
            source_missing_steps.append(step_id)
        reasons = raw_decision.get("trigger_reasons")
        if isinstance(reasons, list):
            for reason in reasons:
                key = str(reason).strip()
                if key:
                    reason_counts[key] = reason_counts.get(key, 0) + 1

    top_reasons = ", ".join(
        f"{reason}:{count}"
        for reason, count in sorted(
            reason_counts.items(), key=lambda item: (-item[1], item[0])
        )[:5]
    )
    return (
        f"total_steps=`{summary.get('total_steps') or len(decisions)}`, "
        f"run_count=`{summary.get('run_count') or len(run_steps)}`, "
        f"skip_count=`{summary.get('skip_count') or len(skip_steps)}`, "
        f"source_missing_count=`{summary.get('source_missing_count') or len(source_missing_steps)}`, "
        f"force_override_count=`{summary.get('force_override_count') or 0}`, "
        f"run_steps_sample=`{', '.join(run_steps[:5]) or '-'}`, "
        f"skip_steps_sample=`{', '.join(skip_steps[:5]) or '-'}`, "
        f"top_reasons=`{top_reasons or '-'}`"
    )


def _task_line(task: GeneratedTask, target_date: str) -> str:
    return (
        f"- [ ] `[{task.task_id}] {task.title}` "
        f"(`Due: {target_date}`, `Slot: {task.slot}`, `TimeWindow: {task.time_window}`, `Track: {task.track}`)"
    )


def _render_task(task: GeneratedTask, target_date: str) -> list[str]:
    out = [_task_line(task, target_date), f"  - Source: {task.source}"]
    out.extend(f"  - {line}" for line in task.lines)
    out.append("")
    return out


def _task_sort_key(task: GeneratedTask) -> tuple[int, str, str]:
    slot_order = {"PREOPEN": 0, "INTRADAY": 1, "POSTCLOSE": 2}
    return (slot_order.get(task.slot, 99), task.time_window, task.task_id)


def _build_tasks(
    *,
    source_date: str,
    target_date: str,
    ev_report: dict[str, Any],
    swing_report: dict[str, Any],
    code_report: dict[str, Any],
    runtime_gap_report: dict[str, Any],
    trigger_report: dict[str, Any],
    rising_missed_report: dict[str, Any],
    rising_missed_normal_buy_bridge_report: dict[str, Any],
) -> list[GeneratedTask]:
    mmdd = _compact_mmdd(target_date)
    ev_path = EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json"
    tuning_performance_path = (
        TUNING_PERFORMANCE_REPORT_DIR
        / f"tuning_performance_control_tower_{source_date}.json"
    )
    code_md_path = (
        DOCS_DIR
        / "code-improvement-workorders"
        / f"code_improvement_workorder_{source_date}.md"
    )
    runtime_gap_path = (
        RUNTIME_APPLY_GAP_REPORT_DIR / f"runtime_apply_gap_audit_{source_date}.json"
    )
    runtime_gap_pending = _runtime_gap_preopen_pending_summary(runtime_gap_report)
    runtime_gap_directives = _runtime_gap_codex_directive_summary(runtime_gap_report)
    source_dimension_gap_summary = _source_dimension_gap_summary(runtime_gap_report)
    quiet_gap_summary = _quiet_gap_summary(runtime_gap_report)
    trigger_decision_path = (
        AUTOMATION_TRIGGER_DECISION_REPORT_DIR
        / f"automation_chain_trigger_decision_{source_date}.json"
    )
    rising_missed_path = (
        RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR
        / f"rising_missed_scout_workorder_{source_date}.json"
    )
    rising_missed_normal_buy_bridge_path = (
        RISING_MISSED_NORMAL_BUY_BRIDGE_CANDIDATE_REPORT_DIR
        / f"rising_missed_normal_buy_bridge_candidate_discovery_{source_date}.json"
    )
    trigger_decision_summary = _automation_trigger_decision_summary(trigger_report)
    rising_missed_summary = _rising_missed_scout_summary(rising_missed_report)
    rising_missed_normal_buy_bridge_summary = _rising_missed_normal_buy_bridge_summary(
        rising_missed_normal_buy_bridge_report
    )
    tuning_sources = f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})"
    tuning_decision_line = "판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다."
    if tuning_performance_path.exists():
        tuning_sources = (
            f"[tuning_performance_control_tower_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(tuning_performance_path)}), "
            f"{tuning_sources}"
        )
        tuning_decision_line = "판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다."
    threshold_source = (
        f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
        "[threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), "
        "[run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)"
    )
    threshold_lines = [
        "판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.",
        "금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.",
        "다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.",
    ]
    if runtime_gap_pending:
        threshold_source = (
            f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
            "[threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), "
            "[run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)"
        )
        threshold_lines = [
            threshold_lines[0],
            f"판정 기준: runtime apply gap audit의 `post_apply_attribution_pending`/`retry_pending` 후보가 다음 PREOPEN apply plan과 runtime env에서 소비되는지 사용자에게 표면화한다. 확인 대상: {runtime_gap_pending}.",
            threshold_lines[1],
            "다음 액션: `runtime_gap_pending_consumed`, `runtime_gap_pending_not_consumed`, `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.",
        ]
    tasks = [
        GeneratedTask(
            task_id=f"ThresholdEnvAutoApplyPreopen{mmdd}",
            title="threshold env 자동 apply 산출물 및 사용자 개입 여부 확인",
            slot="PREOPEN",
            time_window="08:50~08:55",
            track="RuntimeStability",
            source=threshold_source,
            lines=tuple(threshold_lines),
        ),
        GeneratedTask(
            task_id=f"RisingMissedScoutRuntimePreopen{mmdd}",
            title="rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인",
            slot="PREOPEN",
            time_window="08:55~09:00",
            track="ScalpingLogic",
            source=(
                f"[rising_missed_scout_workorder_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(rising_missed_path)}), "
                f"[rising_missed_normal_buy_bridge_candidate_discovery_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(rising_missed_normal_buy_bridge_path)}), "
                f"[code_improvement_workorder_{source_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{source_date}.json), "
                f"[threshold_apply_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_{target_date}.json), "
                f"[threshold_runtime_env_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_{target_date}.json), "
                f"[threshold_runtime_env_verify_{target_date}.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_{target_date}.json)"
            ),
            lines=(
                f"판정 기준: 전일 `rising_missed_scout_workorder` 요약({rising_missed_summary})과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약({rising_missed_normal_buy_bridge_summary})을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.",
                "금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.",
                "다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.",
            ),
        ),
    ]
    if _has_approval_request(ev_report, swing_report):
        tasks.append(
            GeneratedTask(
                task_id=f"SwingPreFinalAutoAndFinalApprovalPreopen{mmdd}",
                title="스윙 pre-final auto state 및 final approval artifact 확인",
                slot="PREOPEN",
                time_window="08:45~08:50",
                track="RuntimeStability",
                source=(
                    f"[swing_runtime_approval_{source_date}.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_{source_date}.json), "
                    f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})"
                ),
                lines=(
                    "판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.",
                    "금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.",
                    "다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.",
                ),
            )
        )
    selected = _list_selected_families(ev_report)
    if _has_runtime_change(ev_report):
        tasks.append(
            GeneratedTask(
                task_id=f"RuntimeEnvIntradayObserve{mmdd}",
                title="전일 selected runtime family 장중 provenance 및 rollback guard 확인",
                slot="INTRADAY",
                time_window="09:05~09:20",
                track="RuntimeStability",
                source=f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})",
                lines=(
                    f"판정 기준: selected_families={', '.join(selected) if selected else '-'}가 runtime event provenance에 찍히는지 확인한다.",
                    "금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.",
                    "다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.",
                ),
            )
        )
    if _has_sim_probe_activity(ev_report):
        tasks.append(
            GeneratedTask(
                task_id=f"SimProbeIntradayCoverage{mmdd}",
                title="sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인",
                slot="INTRADAY",
                time_window="09:35~09:50",
                track="ScalpingLogic",
                source=f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)})",
                lines=(
                    "판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.",
                    "금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.",
                    "다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.",
                ),
            )
        )
    tasks.append(
        GeneratedTask(
            task_id=f"IntradaySourceQualityGateCheck{mmdd}",
            title="장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인",
            slot="INTRADAY",
            time_window="14:20~14:35",
            track="RuntimeStability",
            source=(
                f"[pipeline_events_{target_date}.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_{target_date}.jsonl), "
                f"[threshold_events_{target_date}.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_{target_date}.jsonl), "
                f"[observation_source_quality_audit_{target_date}.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_{target_date}.json), "
                "[observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)"
            ),
            lines=(
                f"판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date {target_date} --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.",
                "금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.",
                "다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.",
            ),
        )
    )
    tasks.extend(
        [
            GeneratedTask(
                task_id=f"ThresholdDailyEVReport{mmdd}",
                title="daily EV real/sim/combined split 및 자동 반영 결과 확인",
                slot="POSTCLOSE",
                time_window="16:30~16:45",
                track="RuntimeStability",
                source=tuning_sources,
                lines=(
                    tuning_decision_line,
                    "금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.",
                    "다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.",
                ),
            ),
            GeneratedTask(
                task_id=f"PostcloseSourceQualityGateReview{mmdd}",
                title="장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인",
                slot="POSTCLOSE",
                time_window="16:25~16:35",
                track="RuntimeStability",
                source=(
                    f"[observation_source_quality_audit_{target_date}.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_{target_date}.json), "
                    f"[threshold_cycle_ev_{target_date}.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_{target_date}.json), "
                    f"[code_improvement_workorder_{target_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{target_date}.json), "
                    f"[threshold_cycle_postclose_verification_{target_date}.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_{target_date}.json)"
                ),
                lines=(
                    "판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.",
                    "금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.",
                    "다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.",
                ),
            ),
            GeneratedTask(
                task_id=f"HumanInterventionSummary{mmdd}",
                title="자동화체인 사용자 개입 요구사항 분류 및 누락 확인",
                slot="POSTCLOSE",
                time_window="17:00~17:15",
                track="RuntimeStability",
                source=(
                    f"[threshold_cycle_ev_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(ev_path)}), "
                    "[time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)"
                ),
                lines=(
                    "판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.",
                    "금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.",
                    "다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.",
                ),
            ),
        ]
    )
    if _has_payload(code_report) and code_md_path.exists():
        tasks.append(
            GeneratedTask(
                task_id=f"CodeImprovementWorkorderReview{mmdd}",
                title="code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인",
                slot="POSTCLOSE",
                time_window="21:15~21:25",
                track="ScalpingLogic",
                source=(
                    f"[code_improvement_workorder_{source_date}.md](/home/ubuntu/KORStockScan/{_rel(code_md_path)}), "
                    f"[code_improvement_workorder_{source_date}.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_{source_date}.json)"
                ),
                lines=(
                    f"판정 기준: selected_order_count={_code_workorder_count(ev_report, code_report)}와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.",
                    "금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.",
                    "다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.",
                ),
            )
        )
    if _has_payload(trigger_report):
        tasks.append(
            GeneratedTask(
                task_id=f"AutomationTriggerDecisionSummary{mmdd}",
                title="자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인",
                slot="POSTCLOSE",
                time_window="21:40~21:55",
                track="RuntimeStability",
                source=(
                    f"[automation_chain_trigger_decision_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(trigger_decision_path)}), "
                    "[run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)"
                ),
                lines=(
                    f"판정 기준: trigger decision summary의 {trigger_decision_summary}를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.",
                    "금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.",
                    "다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.",
                ),
            ),
        )
    tasks.extend(
        [
            *(
                [
                    GeneratedTask(
                        task_id=f"RuntimeApplyGapDirectiveReview{mmdd}",
                        title="runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md), "
                            "[runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)"
                        ),
                        lines=(
                            f"판정 기준: runtime apply gap audit의 Codex 작업지시 {runtime_gap_directives}를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.",
                            "금지: 작업지시만을 approval artifact나 즉시 runtime env 수정 권한으로 해석하지 않는다. 장중 반영은 별도의 사용자 명시 지시와 bounded 단일축 계약이 필요하며 broker/order/provider/cap guard는 우회하지 않는다.",
                            "다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.",
                        ),
                    )
                ]
                if runtime_gap_directives
                else []
            ),
            *(
                [
                    GeneratedTask(
                        task_id=f"LifecycleSourceDimensionGapReview{mmdd}",
                        title="lifecycle source dimension gap 자동 표면화 및 처리 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md)"
                        ),
                        lines=(
                            f"판정 기준: source dimension gap summary의 {source_dimension_gap_summary}를 확인하고 workorder/checklist 표면화 누락 여부를 닫는다.",
                            "금지: source-dimension gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.",
                            "다음 액션: `implement_now`, `already_covered_by_fallback`, `rollup_only`, `defer_until_postclose_report`, `reject_not_applicable` 중 하나로 닫는다.",
                        ),
                    )
                ]
                if source_dimension_gap_summary and not runtime_gap_directives
                else []
            ),
            *(
                [
                    GeneratedTask(
                        task_id=f"LifecycleQuietGapReview{mmdd}",
                        title="lifecycle quiet gap rollup 자동 표면화 및 처리 확인",
                        slot="POSTCLOSE",
                        time_window="21:25~21:40",
                        track="ScalpingLogic",
                        source=(
                            f"[runtime_apply_gap_audit_{source_date}.json](/home/ubuntu/KORStockScan/{_rel(runtime_gap_path)}), "
                            f"[runtime_apply_gap_audit_{source_date}.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_{source_date}.md)"
                        ),
                        lines=(
                            f"판정 기준: quiet gap summary의 {quiet_gap_summary}를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.",
                            "금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.",
                            "다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.",
                        ),
                    )
                ]
                if quiet_gap_summary and not runtime_gap_directives
                else []
            ),
        ]
    )
    return tasks


def _render_auto_block(
    *,
    source_date: str,
    target_date: str,
    ev_report: dict[str, Any],
    swing_report: dict[str, Any],
    code_report: dict[str, Any],
    runtime_gap_report: dict[str, Any],
    trigger_report: dict[str, Any],
    rising_missed_report: dict[str, Any],
    rising_missed_normal_buy_bridge_report: dict[str, Any],
    exclude_task_ids: set[str] | None = None,
) -> str:
    tasks = _build_tasks(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        rising_missed_normal_buy_bridge_report=rising_missed_normal_buy_bridge_report,
    )
    exclude_task_ids = exclude_task_ids or set()
    tasks = [task for task in tasks if task.task_id not in exclude_task_ids]
    tasks.sort(key=_task_sort_key)
    by_slot = {"PREOPEN": [], "INTRADAY": [], "POSTCLOSE": []}
    for task in tasks:
        by_slot.setdefault(task.slot, []).append(task)

    lines = [
        AUTO_START,
        f"## 자동 생성 체크리스트 (`{source_date}` postclose -> `{target_date}`)",
        "",
        "- 이 블록은 postclose 자동화 산출물에서 생성된다.",
        "- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.",
        "- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.",
        "",
    ]
    sections = (
        ("PREOPEN", "장전 체크리스트 (08:45~09:00)"),
        ("INTRADAY", "장중 체크리스트 (09:05~15:20)"),
        ("POSTCLOSE", "장후 체크리스트 (20:05~21:55)"),
    )
    for slot, heading in sections:
        lines.append(f"## {heading}")
        lines.append("")
        if not by_slot.get(slot):
            lines.append("- 해당 슬롯 자동 생성 항목 없음.")
            lines.append("")
            continue
        for task in by_slot[slot]:
            lines.extend(_render_task(task, target_date))
    lines.append(AUTO_END)
    return "\n".join(lines).rstrip() + "\n"


def _render_new_document(target_date: str, auto_block: str) -> str:
    return "\n".join(
        [
            f"# {target_date} Stage2 To-Do Checklist",
            "",
            "## 오늘 목적",
            "",
            "- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.",
            "- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.",
            "- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.",
            "",
            "## 오늘 강제 규칙",
            "",
            "- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.",
            "- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.",
            "- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.",
            "- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.",
            "- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.",
            "- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.",
            "- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.",
            "",
            auto_block.rstrip(),
            "",
            _render_sync_section().rstrip(),
            "",
        ]
    )


def _render_sync_section() -> str:
    return "\n".join(
        [
            "## Project/Calendar 동기화",
            "",
            "문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.",
            "",
            "```bash",
            SYNC_COMMAND,
            "```",
        ]
    )


def _upsert_auto_block(existing: str, auto_block: str) -> str:
    if AUTO_START in existing and AUTO_END in existing:
        prefix, rest = existing.split(AUTO_START, 1)
        _, suffix = rest.split(AUTO_END, 1)
        return prefix.rstrip() + "\n\n" + auto_block.rstrip() + "\n" + suffix

    sync_heading = "\n## Project/Calendar 동기화"
    if sync_heading in existing:
        prefix, suffix = existing.split(sync_heading, 1)
        return (
            prefix.rstrip()
            + "\n\n"
            + auto_block.rstrip()
            + "\n"
            + sync_heading
            + suffix
        )

    suffix = "" if existing.endswith("\n") else "\n"
    return existing + suffix + "\n" + auto_block


def _manual_text_without_auto_block(existing: str) -> str:
    if AUTO_START not in existing or AUTO_END not in existing:
        return existing
    prefix, rest = existing.split(AUTO_START, 1)
    _, suffix = rest.split(AUTO_END, 1)
    return prefix + suffix


def _auto_block_text(existing: str) -> str:
    if AUTO_START not in existing or AUTO_END not in existing:
        return ""
    _, rest = existing.split(AUTO_START, 1)
    body, _ = rest.split(AUTO_END, 1)
    return AUTO_START + body + AUTO_END


def _existing_manual_task_ids(existing: str) -> set[str]:
    text = _manual_text_without_auto_block(existing)
    return {match.group(1) for match in re.finditer(r"`\[([A-Za-z0-9_:-]+)\]", text)}


def _task_ids_from_text(text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(
            r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)\]", text, re.MULTILINE
        )
    }


def _task_slot_from_block(block: str, fallback_slot: str) -> str:
    match = re.search(r"`Slot:\s*([A-Z_]+)`", block)
    if match:
        return match.group(1)
    return fallback_slot


def _preserved_auto_task_blocks(
    existing: str, generated_task_ids: set[str]
) -> dict[str, list[str]]:
    text = _auto_block_text(existing)
    if not text:
        return {}
    preserved: dict[str, list[str]] = {"PREOPEN": [], "INTRADAY": [], "POSTCLOSE": []}
    current_slot = ""
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## 장전"):
            current_slot = "PREOPEN"
        elif line.startswith("## 장중"):
            current_slot = "INTRADAY"
        elif line.startswith("## 장후"):
            current_slot = "POSTCLOSE"

        if re.match(r"^- \[[ xX]\] `\[[A-Za-z0-9_:-]+]", line):
            if current:
                block = "\n".join(current).rstrip()
                task_id_match = re.match(
                    r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0]
                )
                task_id = task_id_match.group(1) if task_id_match else ""
                if task_id and task_id not in generated_task_ids:
                    slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
                    preserved.setdefault(slot, []).append(block)
            current = [line]
            continue

        if current:
            if line.startswith("## ") or line == AUTO_END:
                block = "\n".join(current).rstrip()
                task_id_match = re.match(
                    r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0]
                )
                task_id = task_id_match.group(1) if task_id_match else ""
                if task_id and task_id not in generated_task_ids:
                    slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
                    preserved.setdefault(slot, []).append(block)
                current = []
            else:
                current.append(line)
    if current:
        block = "\n".join(current).rstrip()
        task_id_match = re.match(r"^- \[[ xX]\] `\[([A-Za-z0-9_:-]+)]", current[0])
        task_id = task_id_match.group(1) if task_id_match else ""
        if task_id and task_id not in generated_task_ids:
            slot = _task_slot_from_block(block, current_slot or "POSTCLOSE")
            preserved.setdefault(slot, []).append(block)
    return {slot: blocks for slot, blocks in preserved.items() if blocks}


def _merge_preserved_auto_tasks(existing: str, auto_block: str) -> str:
    preserved = _preserved_auto_task_blocks(existing, _task_ids_from_text(auto_block))
    if not preserved:
        return auto_block
    lines: list[str] = []
    current_slot = ""

    def flush_slot(slot: str) -> None:
        if not slot:
            return
        for block in preserved.pop(slot, []):
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(block.splitlines())
            lines.append("")

    for line in auto_block.splitlines():
        if line.startswith("## 장전"):
            flush_slot(current_slot)
            current_slot = "PREOPEN"
        elif line.startswith("## 장중"):
            flush_slot(current_slot)
            current_slot = "INTRADAY"
        elif line.startswith("## 장후"):
            flush_slot(current_slot)
            current_slot = "POSTCLOSE"
        if line == AUTO_END:
            flush_slot(current_slot)
            current_slot = ""
        lines.append(line)
    if preserved:
        insert_at = len(lines) - 1 if lines and lines[-1] == AUTO_END else len(lines)
        extra: list[str] = []
        for blocks in preserved.values():
            for block in blocks:
                if extra and extra[-1] != "":
                    extra.append("")
                extra.extend(block.splitlines())
                extra.append("")
        lines[insert_at:insert_at] = extra
    return "\n".join(lines).rstrip() + "\n"


def build_next_stage2_checklist(source_date: str) -> dict[str, Any]:
    source_date = str(source_date).strip()
    if not source_date:
        raise ValueError("source_date is required")
    date.fromisoformat(source_date)
    target_date = _next_krx_trading_day(source_date)
    target_path = stage2_checklist_path(target_date)
    missing_required = _missing_required_postclose_artifacts(source_date)
    if missing_required:
        missing = ", ".join(_rel(path) for path in missing_required)
        raise RuntimeError(
            f"required postclose artifacts are missing for {source_date}: {missing}"
        )
    ev_report = _load_json(EV_REPORT_DIR / f"threshold_cycle_ev_{source_date}.json")
    swing_report = _load_json(
        SWING_RUNTIME_APPROVAL_DIR / f"swing_runtime_approval_{source_date}.json"
    )
    code_report = _load_json(
        CODE_IMPROVEMENT_REPORT_DIR / f"code_improvement_workorder_{source_date}.json"
    )
    runtime_gap_report = _load_json(
        RUNTIME_APPLY_GAP_REPORT_DIR / f"runtime_apply_gap_audit_{source_date}.json"
    )
    trigger_report = _load_json(
        AUTOMATION_TRIGGER_DECISION_REPORT_DIR
        / f"automation_chain_trigger_decision_{source_date}.json"
    )
    rising_missed_report = _load_json(
        RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR
        / f"rising_missed_scout_workorder_{source_date}.json"
    )
    rising_missed_normal_buy_bridge_report = _load_json(
        RISING_MISSED_NORMAL_BUY_BRIDGE_CANDIDATE_REPORT_DIR
        / f"rising_missed_normal_buy_bridge_candidate_discovery_{source_date}.json"
    )
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    exclude_task_ids = _existing_manual_task_ids(existing) if existing else set()
    auto_block = _render_auto_block(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        rising_missed_normal_buy_bridge_report=rising_missed_normal_buy_bridge_report,
        exclude_task_ids=exclude_task_ids,
    )
    if existing:
        auto_block = _merge_preserved_auto_tasks(existing, auto_block)

    if existing:
        content = _upsert_auto_block(existing, auto_block)
        created = False
    else:
        content = _render_new_document(target_date, auto_block)
        created = True

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    tasks = _build_tasks(
        source_date=source_date,
        target_date=target_date,
        ev_report=ev_report,
        swing_report=swing_report,
        code_report=code_report,
        runtime_gap_report=runtime_gap_report,
        trigger_report=trigger_report,
        rising_missed_report=rising_missed_report,
        rising_missed_normal_buy_bridge_report=rising_missed_normal_buy_bridge_report,
    )
    tasks = [task for task in tasks if task.task_id not in exclude_task_ids]
    tasks.sort(key=_task_sort_key)
    return {
        "source_date": source_date,
        "target_date": target_date,
        "path": str(target_path),
        "created": created,
        "task_count": len(tasks),
        "tasks": [task.task_id for task in tasks],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build next trading day's stage2 checklist from postclose outputs."
    )
    parser.add_argument(
        "--source-date",
        default="",
        help="Postclose source date in YYYY-MM-DD. Defaults to KST today.",
    )
    args = parser.parse_args()
    source_date = (
        args.source_date.strip()
        or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    )
    summary = build_next_stage2_checklist(source_date)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[NEXT_STAGE2_CHECKLIST_ERROR] {exc}", file=sys.stderr)
        raise
