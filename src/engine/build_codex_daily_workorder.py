"""Build daily Codex workorder markdown from GitHub Project v2 items."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from zoneinfo import ZoneInfo

from src.engine.sync_docs_backlog_to_project import (
    _completed_runbook_slots,
    _infer_slot_label,
    _infer_time_window,
    _is_managed_project_title,
    _managed_title_key,
    collect_backlog_tasks,
)
from src.utils.market_day import get_krx_trading_day_status


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
RETRYABLE_GRAPHQL_HTTP_STATUS = {502, 503, 504}


@dataclass(frozen=True)
class ProjectTask:
    item_id: str
    content_type: str
    title: str
    url: str
    due_date: str
    status: str
    track: str
    slot: str
    time_window: str
    assignees: str
    state: str
    source: str
    section: str
    apply_target: str = ""


@dataclass(frozen=True)
class RunbookCheck:
    check_id: str
    title: str
    slot: str
    time_window: str
    source: str
    section: str
    artifact_checks: tuple[str, ...]
    decision_rule: str
    forbidden: str


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None or not str(value).strip():
        value = default
    if value is None or not str(value).strip():
        raise RuntimeError(f"missing required env: {name}")
    return str(value)


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _local_today_iso() -> str:
    raw = os.getenv("CODEX_WORKORDER_TARGET_DATE", "").strip()
    if raw:
        return raw
    tz_name = os.getenv("CODEX_WORKORDER_TIMEZONE", "Asia/Seoul").strip() or "Asia/Seoul"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Seoul")
    return datetime.now(tz).date().isoformat()


def _graphql_query() -> str:
    return """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      title
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isArchived
          content {
            __typename
            ... on Issue {
              title
              url
              body
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              body
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
              body
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
  user(login: $owner) {
    projectV2(number: $number) {
      title
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isArchived
          content {
            __typename
            ... on Issue {
              title
              url
              body
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              body
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
              body
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
}
""".strip()


def _graphql_request(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = request.Request(
        GITHUB_GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    max_attempts = _env_int("CODEX_WORKORDER_GRAPHQL_MAX_ATTEMPTS", 4, minimum=1)
    timeout_sec = _env_int("CODEX_WORKORDER_GRAPHQL_TIMEOUT_SEC", 45, minimum=5)
    retry_base_delay_sec = _env_float("CODEX_WORKORDER_GRAPHQL_RETRY_DELAY_SEC", 2.0, minimum=0.0)
    body = ""
    for attempt in range(1, max_attempts + 1):
        try:
            with request.urlopen(req, timeout=timeout_sec) as resp:
                body = resp.read().decode("utf-8")
            break
        except error.HTTPError as exc:
            retryable = exc.code in RETRYABLE_GRAPHQL_HTTP_STATUS
            if not retryable or attempt >= max_attempts:
                raise
            delay = retry_base_delay_sec * attempt
            print(
                f"[CODEX_DAILY_WORKORDER_RETRY] github graphql HTTP {exc.code}; "
                f"attempt={attempt}/{max_attempts}; retry_in={delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
        except (error.URLError, TimeoutError) as exc:
            if attempt >= max_attempts:
                raise
            delay = retry_base_delay_sec * attempt
            print(
                f"[CODEX_DAILY_WORKORDER_RETRY] github graphql transport error: {exc}; "
                f"attempt={attempt}/{max_attempts}; retry_in={delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    parsed = json.loads(body)
    errors = parsed.get("errors") or []
    fatal_errors: list[dict[str, Any]] = []
    for err in errors:
        err_type = str(err.get("type") or "")
        err_path = err.get("path") or []
        if err_type == "NOT_FOUND" and err_path in (["organization"], ["user"]):
            continue
        fatal_errors.append(err)
    if fatal_errors:
        raise RuntimeError(f"github graphql errors: {fatal_errors}")
    return parsed.get("data") or {}


def _project_node(data: dict[str, Any]) -> dict[str, Any]:
    node = ((data.get("organization") or {}).get("projectV2")) or ((data.get("user") or {}).get("projectV2"))
    if not node:
        raise RuntimeError("project not found. check GH_PROJECT_OWNER / GH_PROJECT_NUMBER / token scope")
    return node


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _norm(value: str) -> str:
    return value.strip().lower()


def _parse_body_metadata(body: str) -> tuple[str, str, str]:
    source = ""
    section = ""
    apply_target = ""
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("Source:"):
            source = line.split(":", 1)[1].strip().strip("`")
        elif line.startswith("Section:"):
            section = line.split(":", 1)[1].strip().strip("`")
        elif line.startswith("ApplyTarget:"):
            apply_target = line.split(":", 1)[1].strip().strip("`")
    return source, section, apply_target


def _track_from_title_prefix(title: str) -> str:
    match = re.match(r"^\s*\[([A-Za-z0-9_-]+)\]", title)
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith(("Checklist", "RunbookOps", "RuntimeStability", "ScalpingLogic", "AIPrompt", "Plan")):
        return value
    return ""


def _parse_project_item(
    node: dict[str, Any],
    *,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
    time_window_field_name: str,
) -> ProjectTask | None:
    if bool(node.get("isArchived")):
        return None

    content = node.get("content") or {}
    content_type = str(content.get("__typename") or "Unknown")
    title = str(content.get("title") or "").strip() or "(untitled)"
    url = str(content.get("url") or "").strip()
    body = str(content.get("body") or "")
    state = str(content.get("state") or "").strip()
    assignees_nodes = ((content.get("assignees") or {}).get("nodes") or []) if content else []
    assignees = ", ".join(str(n.get("login") or "").strip() for n in assignees_nodes if n.get("login"))
    source, section, apply_target = _parse_body_metadata(body)
    if not apply_target:
        apply_target = "-"

    due_date = ""
    status = ""
    track = ""
    slot = ""
    time_window = ""
    for fv in (node.get("fieldValues") or {}).get("nodes") or []:
        field_name = str(((fv.get("field") or {}).get("name")) or "").strip()
        kind = str(fv.get("__typename") or "")
        if kind == "ProjectV2ItemFieldDateValue" and field_name == due_field_name:
            due_date = str(fv.get("date") or "").strip()
        elif kind == "ProjectV2ItemFieldSingleSelectValue":
            if field_name == status_field_name:
                status = str(fv.get("name") or "").strip()
            elif field_name == track_field_name:
                track = str(fv.get("name") or "").strip()
            elif field_name == slot_field_name:
                slot = str(fv.get("name") or "").strip()
            elif field_name == time_window_field_name:
                time_window = str(fv.get("name") or "").strip()
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == track_field_name and not track:
            track = str(fv.get("text") or "").strip()
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == slot_field_name and not slot:
            slot = str(fv.get("text") or "").strip()
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == time_window_field_name and not time_window:
            time_window = str(fv.get("text") or "").strip()

    if not track:
        track = _track_from_title_prefix(title)

    return ProjectTask(
        item_id=str(node.get("id") or "").strip(),
        content_type=content_type,
        title=title,
        url=url,
        due_date=due_date,
        status=status,
        track=track,
        slot=slot,
        time_window=time_window,
        assignees=assignees,
        state=state,
        source=source,
        section=section,
        apply_target=apply_target,
    )


def _matches_slot(item_slot: str, target_slots: set[str]) -> bool:
    if not target_slots:
        return True
    return _norm(item_slot) in target_slots


def _resolve_slot_filters_for_target_date(
    *,
    selected_slots: list[str],
    target_date: str,
) -> tuple[list[str], bool, str]:
    if not target_date:
        return selected_slots, False, ""

    is_trading_day, reason = get_krx_trading_day_status(date.fromisoformat(target_date))
    if is_trading_day:
        return selected_slots, False, reason

    normalized = {_norm(slot) for slot in selected_slots if slot.strip()}
    if normalized == {"intraday"}:
        return [], True, reason
    if normalized and "intraday" not in normalized:
        return ["__holiday_skip__"], True, reason
    return selected_slots, True, reason


def fetch_project_tasks(
    *,
    token: str,
    owner: str,
    number: int,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
    time_window_field_name: str,
    include_statuses: list[str],
    include_slots: list[str],
    target_date: str | None,
    include_overdue: bool,
) -> tuple[str, list[ProjectTask]]:
    query = _graphql_query()
    cursor: str | None = None
    project_title = ""
    out: list[ProjectTask] = []
    include_set = {_norm(s) for s in include_statuses if s.strip()}
    slot_set = {_norm(s) for s in include_slots if s.strip()}

    while True:
        data = _graphql_request(token, query, {"owner": owner, "number": number, "cursor": cursor})
        project = _project_node(data)
        if not project_title:
            project_title = str(project.get("title") or "").strip()
        page = project.get("items") or {}
        nodes = page.get("nodes") or []
        for node in nodes:
            item = _parse_project_item(
                node,
                due_field_name=due_field_name,
                status_field_name=status_field_name,
                track_field_name=track_field_name,
                slot_field_name=slot_field_name,
                time_window_field_name=time_window_field_name,
            )
            if not item:
                continue
            if include_set and _norm(item.status) not in include_set:
                continue
            if not _matches_slot(item.slot, slot_set):
                continue
            if target_date:
                if not item.due_date:
                    continue
                if include_overdue:
                    if item.due_date > target_date:
                        continue
                elif item.due_date != target_date:
                    continue
            out.append(item)
        page_info = page.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return project_title, out


def _date_sort_value(raw: str) -> str:
    return raw if raw else "9999-12-31"


def sort_tasks(tasks: list[ProjectTask], status_order: list[str]) -> list[ProjectTask]:
    order = {name: i for i, name in enumerate(status_order)}
    default_rank = len(order) + 10
    return sorted(
        tasks,
        key=lambda t: (
            order.get(t.status, default_rank),
            _date_sort_value(t.due_date),
            t.track or "zzz",
            t.title.lower(),
        ),
    )


def _task_completeness_score(task: ProjectTask) -> tuple[int, int, int, int, str]:
    return (
        1 if task.due_date else 0,
        1 if task.slot else 0,
        1 if task.time_window else 0,
        1 if task.source or task.section else 0,
        task.item_id,
    )


def dedupe_tasks(tasks: list[ProjectTask]) -> list[ProjectTask]:
    deduped: dict[str, ProjectTask] = {}
    order: list[str] = []
    for task in tasks:
        key = " ".join(str(task.title or "").split()).strip().lower()
        if not key:
            key = task.item_id
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = task
            order.append(key)
            continue
        if _task_completeness_score(task) > _task_completeness_score(existing):
            deduped[key] = task
    return [deduped[key] for key in order]


def _open_managed_title_keys_for_target_date(target_date: str) -> set[str]:
    keys: set[str] = set()
    for task in collect_backlog_tasks():
        if str(task.due_date or "").strip() != target_date:
            continue
        title = " ".join(f"[{task.track}] {task.title}".split()).strip()
        if not _is_managed_project_title(title):
            continue
        keys.add(_managed_title_key(title))
    return keys


def _filter_stale_same_day_managed_tasks(tasks: list[ProjectTask], target_date: str) -> list[ProjectTask]:
    if not target_date:
        return tasks
    open_keys = _open_managed_title_keys_for_target_date(target_date)
    filtered: list[ProjectTask] = []
    for task in tasks:
        if (
            task.due_date == target_date
            and _is_managed_project_title(task.title)
            and _managed_title_key(task.title) not in open_keys
        ):
            continue
        filtered.append(task)
    return filtered


def _project_title_for_backlog_task(task: Any) -> str:
    return " ".join(f"[{task.track}] {task.title}".split()).strip()


def _doc_task_id(task: Any) -> str:
    title_key = _managed_title_key(_project_title_for_backlog_task(task))
    return f"DOC:{title_key}"


def _local_backlog_project_tasks(
    *,
    target_date: str,
    include_slots: list[str],
    include_statuses: list[str],
    include_overdue: bool,
    default_duration_min: int,
) -> list[ProjectTask]:
    """Return local checklist/runbook tasks so workorders do not depend on Project sync freshness."""

    status = "Todo"
    include_set = {_norm(s) for s in include_statuses if s.strip()}
    if include_set and _norm(status) not in include_set:
        return []
    slot_set = {_norm(s) for s in include_slots if s.strip()}
    out: list[ProjectTask] = []
    for task in collect_backlog_tasks():
        due_date = str(getattr(task, "due_date", "") or "").strip()
        if target_date:
            if not due_date:
                continue
            if include_overdue:
                if due_date > target_date:
                    continue
            elif due_date != target_date:
                continue
        slot = _infer_slot_label(task)
        if not _matches_slot(slot, slot_set):
            continue
        time_window = _infer_time_window(
            task,
            slot_label=slot,
            default_duration_min=default_duration_min,
        )
        out.append(
            ProjectTask(
                item_id=_doc_task_id(task),
                content_type="LocalDoc",
                title=_project_title_for_backlog_task(task),
                url="",
                due_date=due_date,
                status=status,
                track=str(getattr(task, "track", "") or ""),
                slot=slot,
                time_window=time_window,
                assignees="",
                state="OPEN",
                source=str(getattr(task, "source", "") or ""),
                section=str(getattr(task, "section", "") or ""),
                apply_target=str(getattr(task, "apply_target", "") or "-"),
            )
        )
    return out


def _target_date_compact(target_date: str | None) -> str:
    raw = str(target_date or _local_today_iso()).strip()
    return raw.replace("-", "") if raw else "YYYYMMDD"


def build_runbook_operational_checks(*, target_date: str | None, slots: list[str] | None) -> list[RunbookCheck]:
    """Build runbook-derived Codex workorder checks without creating Project items."""

    compact = _target_date_compact(target_date)
    date_text = str(target_date or _local_today_iso())
    completed_slots = _completed_runbook_slots(date_text)
    selected = {_norm(slot) for slot in (slots or []) if str(slot or "").strip()}
    include_all = not selected
    checks: list[RunbookCheck] = []

    if (include_all or "preopen" in selected) and "PREOPEN" not in completed_slots:
        checks.append(
            RunbookCheck(
                check_id=f"PreopenAutomationHealthCheck{compact}",
                title="장전 자동화체인 상태 확인",
                slot="PREOPEN",
                time_window="08:00~09:00",
                source="docs/time-based-operations-runbook.md",
                section="장전 확인 절차",
                artifact_checks=(
                    "logs/ensemble_scanner.log",
                    "data/daily_recommendations_v2.csv",
                    "data/daily_recommendations_v2_diagnostics.json",
                    "logs/threshold_cycle_preopen_cron.log",
                    f"data/threshold_cycle/apply_plans/threshold_apply_{date_text}.json",
                    f"data/threshold_cycle/runtime_env/threshold_runtime_env_{date_text}.json",
                    "threshold_apply swing_runtime_approval requested/approved/blocked",
                    "tmux bot session / src/run_bot.sh runtime env source 여부",
                ),
                decision_rule=(
                    "pass|warning|fail|not_yet_due 중 하나로 판정. preopen apply와 final scanner의 당일 [DONE] marker, "
                    "final scanner 추천/empty/fallback diagnostic 분리, apply plan selected/blocked family, "
                    "AI guard, same-stage owner 충돌, runtime env 생성 여부, "
                    "스윙 approval request/approved/blocked 및 dry-run 강제 여부 확인."
                ),
                forbidden="실패해도 수동 env override, final approval artifact 없는 스윙 env 반영, removed phase0 real-canary 재개, 스윙 dry-run 해제, 장전 수동 enable/hold 판정 금지.",
            )
        )
    if (include_all or "intraday" in selected) and "INTRADAY" not in completed_slots:
        checks.append(
            RunbookCheck(
                check_id=f"IntradayAutomationHealthCheck{compact}",
                title="장중 자동화체인 상태 확인",
                slot="INTRADAY",
                time_window="09:05~15:30",
                source="docs/time-based-operations-runbook.md",
                section="장중 확인 절차",
                artifact_checks=(
                    "logs/run_buy_funnel_sentinel_cron.log",
                    "logs/run_holding_exit_sentinel_cron.log",
                    "logs/run_panic_sell_defense_cron.log",
                    f"data/pipeline_events/pipeline_events_{date_text}.jsonl",
                    f"data/threshold_cycle/threshold_events_{date_text}.jsonl",
                    f"data/report/panic_sell_defense/panic_sell_defense_{date_text}.md",
                    f"data/report/error_detection/error_detection_{date_text}.json",
                ),
                decision_rule=(
                    "pass|warning|fail|not_yet_due 중 하나로 판정. Sentinel RUNTIME_OPS, panic_state, "
                    "pipeline/threshold event append, "
                    "스윙 dry-run provenance, runtime_change=false 유지 확인. "
                    "SystemErrorDetector report의 summary_severity 및 fail detector 확인. "
                    "fail이면 detector별 details을 읽고 운영장애/계측/incident로 분류."
                ),
                forbidden="Sentinel 결과로 당일 runtime threshold 변경 금지. "
                          "SystemErrorDetector 탐지 결과로 runtime threshold/spread/주문/재시작 변경 금지.",
            )
        )
    if (include_all or "postclose" in selected) and "POSTCLOSE" not in completed_slots:
        checks.append(
            RunbookCheck(
                check_id=f"PostcloseAutomationHealthCheck{compact}",
                title="장후 자동화체인 상태 확인",
                slot="POSTCLOSE",
                time_window="16:00~20:45",
                source="docs/time-based-operations-runbook.md",
                section="장후 확인 절차",
                artifact_checks=(
                    "logs/threshold_cycle_postclose_cron.log",
                    "logs/swing_model_retrain_cron.log",
                    "logs/tuning_monitoring_postclose_cron.log",
                    f"data/report/threshold_cycle_ev/threshold_cycle_ev_{date_text}.md",
                    f"data/report/swing_selection_funnel/swing_selection_funnel_{date_text}.md",
                    f"data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date_text}.md",
                    f"data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date_text}.md",
                    f"data/report/swing_improvement_automation/swing_improvement_automation_{date_text}.json",
                    f"data/report/swing_runtime_approval/swing_runtime_approval_{date_text}.json",
                    f"data/report/swing_model_retrain/status/swing_model_retrain_{date_text}.status.json",
                    f"data/report/swing_model_retrain/swing_model_retrain_{date_text}.json",
                    f"data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_{date_text}.md",
                    f"data/report/runtime_approval_summary/runtime_approval_summary_{date_text}.md",
                    f"data/report/observation_source_quality_audit/observation_source_quality_audit_{date_text}.md",
                    f"data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_{date_text}.json",
                    f"docs/code-improvement-workorders/code_improvement_workorder_{date_text}.md",
                    f"data/report/error_detection/error_detection_{date_text}.json",
                ),
                decision_rule=(
                    "pass|warning|fail|not_yet_due 중 하나로 판정. daily EV 제출물, postclose AI correction, "
                    "real/sim/combined split, swing lifecycle automation, swing runtime approval, pattern lab automation, "
                    "swing model retrain status/promotion guard, tuning monitoring의 threshold postclose predecessor DONE 확인, "
                    "code improvement workorder 생성 여부 확인. "
                    "SystemErrorDetector 하루 누적 fail detector가 있으면 incident/playbook 분류. "
                    "Tuning Chain Control State는 GREEN|YELLOW|RED|GRAY 중 하나로 별도 기록하고, "
                    "blocked_stage=input_health|chain_completion|decision_integrity|disposition|runtime_uptake|feedback_closure|-와 "
                    "impact, next_action을 함께 남긴다. EV 손익은 control state의 primary 기준이 아니다."
                ),
                forbidden="postclose 실패 시 threshold 수동 변경이 아니라 같은 date wrapper 재실행/복구 우선. "
                          "swing model retrain 결과로 스윙 dry-run 해제/브로커 주문 허용 금지. "
                          "tuning monitoring은 threshold_cycle_postclose 완료 전 선행 산출물을 소비하지 않는다. "
                          "SystemErrorDetector 결과로 runtime threshold/spread/주문 변경 금지.",
            )
        )
    return checks


def render_markdown(
    *,
    owner: str,
    project_number: int,
    project_title: str,
    generated_at: str,
    target_date: str | None,
    include_overdue: bool,
    holiday_override: bool,
    holiday_reason: str,
    statuses: list[str],
    slots: list[str],
    tasks: list[ProjectTask],
    max_items: int,
    runbook_checks: list[RunbookCheck] | None = None,
) -> str:
    unique_tasks = dedupe_tasks(tasks)
    top = sort_tasks(unique_tasks, statuses)[:max_items]
    runbook_checks = runbook_checks or []
    track_counts: dict[str, int] = {}
    for item in top:
        key = item.track or "-"
        track_counts[key] = track_counts.get(key, 0) + 1

    lines: list[str] = []
    lines.append("# Codex 일일 작업지시서")
    lines.append("")
    lines.append(f"- 생성시각: `{generated_at}`")
    lines.append(f"- 프로젝트: `{owner}` / `#{project_number}` / `{project_title or '-'}`")
    lines.append(f"- 기준일자: `{target_date or '-'}` / overdue 포함: `{include_overdue}`")
    if holiday_override:
        lines.append(f"- 휴장일 재분류: `true` / 사유: `{holiday_reason or '-'}` / 슬롯정책: `all -> INTRADAY`")
    lines.append(f"- 상태필터: `{', '.join(statuses) if statuses else '전체'}`")
    lines.append(f"- 슬롯필터: `{', '.join(slots) if slots else '전체'}`")
    duplicate_count = max(0, len(tasks) - len(unique_tasks))
    lines.append(
        f"- 후보건수: `{len(tasks)}` / 중복제거후: `{len(unique_tasks)}` / 지시반영건수: `{len(top)}`"
    )
    lines.append(f"- Runbook 운영확인 항목: `{len(runbook_checks)}`")
    if duplicate_count:
        lines.append(f"- 중복축약건수: `{duplicate_count}`")
    if track_counts:
        compact = ", ".join(f"{k}:{v}" for k, v in sorted(track_counts.items(), key=lambda kv: kv[0]))
        lines.append(f"- Track 분포: `{compact}`")
    lines.append("")

    # 슬롯별 그룹화
    slot_order = ["PREOPEN", "INTRADAY", "POSTCLOSE"]
    slot_groups: dict[str, list[ProjectTask]] = {slot: [] for slot in slot_order}
    for item in top:
        slot = item.slot or "-"
        if slot in slot_groups:
            slot_groups[slot].append(item)
        else:
            slot_groups["-"] = slot_groups.get("-", [])
            slot_groups["-"].append(item)

    lines.append("## 오늘 Codex 실행 큐")
    lines.append("")
    if not top:
        lines.append("1. 현재 상태필터에 해당하는 항목이 없습니다.")
        lines.append("")
    else:
        idx = 1
        for slot in slot_order:
            group = slot_groups[slot]
            if not group:
                lines.append(f"### {slot} (없음)")
                lines.append("해당 슬롯에 작업이 없습니다.")
                lines.append("")
                continue
            lines.append(f"### {slot}")
            lines.append("")
            for item in group:
                lines.append(f"{idx}. `{item.title}`")
                lines.append(
                    f"   - 상태: `{item.status or '-'}` / 슬롯: `{item.slot or '-'}` / 트랙: `{item.track or '-'}` / 반영대상: `{item.apply_target or '-'}` / Due: `{item.due_date or '-'}` / TimeWindow: `{item.time_window or '-'}`"
                )
                if item.section:
                    lines.append(f"   - 섹션: `{item.section}`")
                if item.source:
                    lines.append(f"   - 소스: `{item.source}`")
                if item.assignees:
                    lines.append(f"   - 담당자: `{item.assignees}`")
                if item.url:
                    lines.append(f"   - 링크: {item.url}")
                lines.append(f"   - Project Item ID: `{item.item_id}`")
                lines.append("")
                idx += 1
        # 알 수 없는 슬롯 처리
        unknown = slot_groups.get("-", [])
        if unknown:
            lines.append("### 기타 슬롯")
            lines.append("")
            for item in unknown:
                lines.append(f"{idx}. `{item.title}`")
                lines.append(
                    f"   - 상태: `{item.status or '-'}` / 슬롯: `{item.slot or '-'}` / 트랙: `{item.track or '-'}` / 반영대상: `{item.apply_target or '-'}` / Due: `{item.due_date or '-'}` / TimeWindow: `{item.time_window or '-'}`"
                )
                if item.section:
                    lines.append(f"   - 섹션: `{item.section}`")
                if item.source:
                    lines.append(f"   - 소스: `{item.source}`")
                if item.assignees:
                    lines.append(f"   - 담당자: `{item.assignees}`")
                if item.url:
                    lines.append(f"   - 링크: {item.url}")
                lines.append(f"   - Project Item ID: `{item.item_id}`")
                lines.append("")
                idx += 1

    lines.append("## Runbook 운영 확인 큐")
    lines.append("")
    if not runbook_checks:
        lines.append("1. 현재 슬롯에 해당하는 runbook 운영 확인 항목이 없습니다.")
        lines.append("")
    else:
        for idx, check in enumerate(runbook_checks, start=1):
            lines.append(f"{idx}. `{check.check_id}` - {check.title}")
            lines.append(
                f"   - 슬롯: `{check.slot}` / TimeWindow: `{check.time_window}` / Source: `{check.source}` / Section: `{check.section}`"
            )
            lines.append(f"   - 판정 기준: {check.decision_rule}")
            lines.append(f"   - 금지/주의: {check.forbidden}")
            lines.append("   - 확인 artifact:")
            for artifact in check.artifact_checks:
                lines.append(f"     - `{artifact}`")
            lines.append("")

    lines.append("## Codex 전달 템플릿")
    lines.append("")
    lines.append("```text")
    lines.append("아래 Project 항목을 오늘 작업 대상으로 처리해줘.")
    lines.append("원칙:")
    lines.append("- 작업시간이 지났으나 반복적으로 실행해야하는 작업은 시간이 지났어도 확인해서 실행(필수)")
    lines.append("- 판정, 근거, 다음 액션 순서로 보고")
    lines.append("- 관련 문서/체크리스트 동시 업데이트")
    lines.append("- 테스트/검증 결과 포함")
    lines.append("- workorder에 적힌 Source/Section을 기준으로 우선 문맥을 맞출 것")
    lines.append("")
    lines.append("[대상 항목]")
    if top:
        # 슬롯별로 대상 항목도 그룹화
        for slot in slot_order:
            group = slot_groups[slot]
            lines.append(f"### {slot}")
            if group:
                for item in group:
                    lines.append(
                        f"- {item.title} | 상태={item.status or '-'} | 슬롯={item.slot or '-'} | 반영대상={item.apply_target or '-'} | Due={item.due_date or '-'} | Source={item.source or '-'} | Section={item.section or '-'} | ID={item.item_id}"
                    )
            else:
                lines.append("- 없음")
        unknown = slot_groups.get("-", [])
        if unknown:
            lines.append("### 기타 슬롯")
            for item in unknown:
                lines.append(
                    f"- {item.title} | 상태={item.status or '-'} | 슬롯={item.slot or '-'} | 반영대상={item.apply_target or '-'} | Due={item.due_date or '-'} | Source={item.source or '-'} | Section={item.section or '-'} | ID={item.item_id}"
                )
    else:
        lines.append("- 없음")
    lines.append("")
    lines.append("[Runbook 운영 확인]")
    if runbook_checks:
        for check in runbook_checks:
            base = (
                f"- [{check.check_id}] {check.title} | 슬롯={check.slot} | TimeWindow={check.time_window} "
                f"| Source={check.source} | Section={check.section} | 판정=pass|warning|fail|not_yet_due"
            )
            if check.slot == "POSTCLOSE":
                base += (
                    " | Tuning Chain Control State=GREEN|YELLOW|RED|GRAY"
                    " | blocked_stage=input_health|chain_completion|decision_integrity|disposition|runtime_uptake|feedback_closure|-"
                    " | impact=... | next_action=..."
                )
            lines.append(base)
    else:
        lines.append("- 없음")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_daily_workorder(
    *,
    output: Path,
    max_items: int,
    slots: list[str] | None = None,
    target_date: str | None = None,
    include_overdue: bool | None = None,
) -> dict[str, Any]:
    token = _env("GH_PROJECT_TOKEN", os.getenv("GITHUB_TOKEN"))
    owner = _env("GH_PROJECT_OWNER")
    number = int(_env("GH_PROJECT_NUMBER"))
    due_field_name = _env("GH_PROJECT_DUE_FIELD_NAME", "Due")
    status_field_name = _env("GH_PROJECT_STATUS_FIELD_NAME", "Status")
    track_field_name = _env("GH_PROJECT_TRACK_FIELD_NAME", "Track")
    slot_field_name = _env("GH_PROJECT_SLOT_FIELD_NAME", "Slot")
    time_window_field_name = _env("GH_PROJECT_TIME_WINDOW_FIELD_NAME", "TimeWindow")
    statuses = _split_csv(os.getenv("GH_CODEX_WORKORDER_STATUSES", "Todo,In Progress"))
    configured_slots = _split_csv(os.getenv("GH_CODEX_WORKORDER_SLOTS", ""))
    include_local_docs = _env_bool("CODEX_WORKORDER_INCLUDE_LOCAL_DOCS", True)
    default_duration_min = _env_int("GH_PROJECT_DEFAULT_TIME_WINDOW_MINUTES", 30, minimum=5)
    selected_slots = slots if slots is not None else configured_slots
    resolved_target_date = target_date or _local_today_iso()
    resolved_include_overdue = (
        include_overdue if include_overdue is not None else _env_bool("CODEX_WORKORDER_INCLUDE_OVERDUE", True)
    )
    effective_slots, holiday_override, holiday_reason = _resolve_slot_filters_for_target_date(
        selected_slots=selected_slots,
        target_date=resolved_target_date,
    )

    project_title, tasks = fetch_project_tasks(
        token=token,
        owner=owner,
        number=number,
        due_field_name=due_field_name,
        status_field_name=status_field_name,
        track_field_name=track_field_name,
        slot_field_name=slot_field_name,
        time_window_field_name=time_window_field_name,
        include_statuses=statuses,
        include_slots=effective_slots,
        target_date=resolved_target_date,
        include_overdue=resolved_include_overdue,
    )
    local_doc_tasks: list[ProjectTask] = []
    if include_local_docs:
        local_doc_tasks = _local_backlog_project_tasks(
            target_date=resolved_target_date,
            include_slots=effective_slots,
            include_statuses=statuses,
            include_overdue=resolved_include_overdue,
            default_duration_min=default_duration_min,
        )
        tasks.extend(local_doc_tasks)
    tasks = _filter_stale_same_day_managed_tasks(tasks, resolved_target_date)
    runbook_checks = build_runbook_operational_checks(target_date=resolved_target_date, slots=effective_slots)
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    markdown = render_markdown(
        owner=owner,
        project_number=number,
        project_title=project_title,
        generated_at=generated_at,
        target_date=resolved_target_date,
        include_overdue=resolved_include_overdue,
        holiday_override=holiday_override,
        holiday_reason=holiday_reason,
        statuses=statuses,
        slots=effective_slots,
        tasks=tasks,
        max_items=max_items,
        runbook_checks=runbook_checks,
    )
    write_markdown(output, markdown)

    return {
        "project_owner": owner,
        "project_number": number,
        "project_title": project_title,
        "target_date": resolved_target_date,
        "include_overdue": resolved_include_overdue,
        "status_filter": statuses,
        "slot_filter": effective_slots,
        "holiday_override": holiday_override,
        "holiday_reason": holiday_reason,
        "candidate_tasks": len(tasks),
        "local_doc_tasks": len(local_doc_tasks),
        "runbook_operational_checks": len(runbook_checks),
        "output": str(output),
        "max_items": max_items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Codex daily workorder markdown from GitHub Project")
    parser.add_argument("--output", default="tmp/codex_daily_workorder.md", help="Output markdown path")
    parser.add_argument("--max-items", type=int, default=20, help="Max items in workorder")
    parser.add_argument("--slot", action="append", default=[], help="Target slot filter (repeatable)")
    parser.add_argument("--target-date", default="", help="Target due date in YYYY-MM-DD. Defaults to local today.")
    parser.add_argument("--no-overdue", action="store_true", help="Exclude overdue items and keep only target date.")
    args = parser.parse_args()

    slot_filter = [s.strip() for s in args.slot if s.strip()] or None
    summary = build_daily_workorder(
        output=Path(args.output),
        max_items=max(1, args.max_items),
        slots=slot_filter,
        target_date=args.target_date.strip() or None,
        include_overdue=not args.no_overdue,
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[CODEX_DAILY_WORKORDER_ERROR] {exc}", file=sys.stderr)
        raise
