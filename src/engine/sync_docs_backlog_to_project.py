"""Parse planning docs and sync remaining tasks to GitHub Project v2 draft items."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request
from zoneinfo import ZoneInfo

from src.utils.market_day import get_krx_trading_day_status


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

DOC_PLAN = Path("docs/plan-korStockScanPerformanceOptimization.prompt.md")
DOC_CHECKLIST = Path("docs/2026-04-13-stage2-todo-checklist.md")
DOC_SCALPING = Path("docs/2026-04-10-scalping-ai-coding-instructions.md")
DOC_PROMPT = Path("docs/2026-04-11-scalping-ai-prompt-coding-instructions.md")


@dataclass(frozen=True)
class BacklogTask:
    title: str
    source: str
    section: str
    track: str
    due_date: str = ""
    apply_target: str = ""


@dataclass(frozen=True)
class ProjectItem:
    item_id: str
    title: str
    content_type: str
    due_date: str = ""
    slot: str = ""
    time_window: str = ""


MANAGED_TRACKS = ("Plan", "ScalpingLogic", "AIPrompt")
CHECKLIST_TRACK_RE = re.compile(r"^Checklist\d{4}$")

TRACK_DEFAULT_SLOT = {
    "Plan": "POSTCLOSE",
    "ScalpingLogic": "INTRADAY",
    "AIPrompt": "POSTCLOSE",
}

SLOT_PREOPEN_KEYWORDS = (
    "장전",
    "preopen",
    "개장 전",
    "오전 8",
    "08:",
)

SLOT_INTRADAY_KEYWORDS = (
    "장중",
    "intraday",
    "실시간",
    "체결",
    "canary",
    "모니터링",
    "운영",
    "동기화",
    "실전",
    "관측",
    "갱신",
    "관찰",
    "추적",
)

SLOT_POSTCLOSE_KEYWORDS = (
    "장후",
    "postclose",
    "마감",
    "eod",
    "리포트",
    "회고",
    "분석",
    "검증",
    "리뷰",
    "평가",
    "비교",
    "판정",
    "정리",
    "후속",
    "결과 정리",
    "다음 세션",
    "15:",
    "15시",
    "문서화",
    "재작업지시",
    "후보안",
)

TIME_ALLDAY_KEYWORDS = ("하루종일", "종일", "all day", "allday")
TIME_UNSCHEDULED_KEYWORDS = ("미정", "tbd", "unscheduled", "예약작업", "추후")

APPLY_TARGET_REMOTE_KEYWORDS = (
    "원격",
    "remote",
    "songstockscan",
    "develop",
    "canary",
)

APPLY_TARGET_MAIN_KEYWORDS = (
    "본서버",
    "메인",
    "main",
    "운영서버",
)


def _local_today_iso() -> str:
    raw = os.getenv("DOC_BACKLOG_TODAY", "").strip()
    if raw:
        return raw
    tz_name = os.getenv("DOC_BACKLOG_TIMEZONE", "Asia/Seoul").strip() or "Asia/Seoul"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Seoul")
    return datetime.now(tz).date().isoformat()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return _read(path)


def _read_candidates(paths: list[Path]) -> tuple[Path, str] | None:
    checked: list[str] = []
    for path in paths:
        checked.append(str(path))
        text = _read_optional(path)
        if text is not None:
            return path, text
    if checked:
        print(
            f"[DOC_BACKLOG_SYNC_WARN] missing source doc candidates: {', '.join(checked)}",
            file=sys.stderr,
        )
    return None


def _checklist_track_from_source(source_path: Path) -> str:
    name = source_path.name
    m = re.match(r"^\d{4}-(\d{2})-(\d{2})-.*checklist\.md$", name)
    if not m:
        return "Checklist"
    return f"Checklist{m.group(1)}{m.group(2)}"


def _scalping_doc_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.getenv("DOC_SCALPING_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(DOC_SCALPING)
    candidates.extend(sorted(Path("docs").glob("*-scalping-ai-coding-instructions.md"), reverse=True))

    deduped: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped


def _prompt_doc_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.getenv("DOC_PROMPT_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(DOC_PROMPT)
    candidates.extend(sorted(Path("docs").glob("*-scalping-ai-prompt-coding-instructions.md"), reverse=True))

    deduped: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped


def _checklist_doc_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.getenv("DOC_CHECKLIST_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(sorted(Path("docs").glob("*-stage2-todo-checklist.md"), reverse=True))
    candidates.append(DOC_CHECKLIST)

    deduped: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped


def _due_date_from_checklist_path(path: Path) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})-stage2-todo-checklist\.md$", path.name)
    if not m:
        return ""
    return m.group(1)


def _extract_section_lines(text: str, heading_prefix: str) -> list[str]:
    lines = text.splitlines()
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(heading_prefix):
            start = i + 1
            break
    if start < 0:
        return []
    out: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        out.append(line)
    return out


def _parse_numbered_items(lines: list[str]) -> list[str]:
    out: list[str] = []
    for raw in lines:
        m = re.match(r"^\s*\d+\.\s+(.+?)\s*$", raw)
        if not m:
            continue
        item = m.group(1).strip()
        item = re.sub(r"`([^`]+)`", r"\1", item)
        if item:
            out.append(item)
    return out


def parse_plan_tasks() -> list[BacklogTask]:
    loaded = _read_candidates([DOC_PLAN])
    if not loaded:
        return []
    source_path, text = loaded
    remaining = _parse_numbered_items(_extract_section_lines(text, "### 아직 남아있는 일"))
    tasks: list[BacklogTask] = []
    for item in remaining:
        tasks.append(
            BacklogTask(
                title=item,
                source=str(source_path),
                section="아직 남아있는 일",
                track="Plan",
            )
        )
    return tasks


def parse_checklist_tasks() -> list[BacklogTask]:
    candidates = _checklist_doc_candidates()
    tasks: list[BacklogTask] = []
    checked: list[str] = []
    loaded_any = False
    today_iso = _local_today_iso()
    forced_path_raw = os.getenv("DOC_CHECKLIST_PATH", "").strip()
    forced_path = Path(forced_path_raw) if forced_path_raw else None
    for source_path in candidates:
        checked.append(str(source_path))
        text = _read_optional(source_path)
        if text is None:
            continue
        loaded_any = True
        due_date = _due_date_from_checklist_path(source_path)
        if due_date and due_date < today_iso and source_path != forced_path:
            continue
        current_section = ""
        for line in text.splitlines():
            heading = re.match(r"^\s*##\s+(.+?)\s*$", line)
            if heading:
                current_section = heading.group(1).strip()
                continue
            m = re.match(r"^\s*-\s*\[ \]\s+(.+?)\s*$", line)
            if not m:
                continue
            item = m.group(1).strip()
            item = re.sub(r"`([^`]+)`", r"\1", item)
            if not item:
                continue
            section_label = "체크박스 미완료"
            if current_section:
                section_label = f"{current_section} / 체크박스 미완료"
            tasks.append(
                BacklogTask(
                    title=item,
                    source=str(source_path),
                    section=section_label,
                    track=_checklist_track_from_source(source_path),
                    due_date=due_date,
                )
            )
    if not loaded_any:
        if checked:
            print(
                f"[DOC_BACKLOG_SYNC_WARN] missing source doc candidates: {', '.join(checked)}",
                file=sys.stderr,
            )
        return []
    return tasks


def parse_scalping_logic_tasks() -> list[BacklogTask]:
    loaded = _read_candidates(_scalping_doc_candidates())
    if not loaded:
        return []
    source_path, text = loaded
    tasks: list[BacklogTask] = []

    # Remaining implementation phases only
    for line in text.splitlines():
        m = re.match(r"^\s*####\s+(0-1b|2-1|2-2|3-1|3-2)\.\s+(.+?)\s*$", line)
        if not m:
            continue
        tasks.append(
            BacklogTask(
                title=f"{m.group(1)} {m.group(2).strip()}",
                source=str(source_path),
                section="단계별 구현 순서",
                track="ScalpingLogic",
            )
        )
    return tasks


def parse_prompt_tasks() -> list[BacklogTask]:
    loaded = _read_candidates(_prompt_doc_candidates())
    if not loaded:
        return []
    source_path, text = loaded
    tasks: list[BacklogTask] = []
    today_iso = _local_today_iso()
    current_phase = "작업 상세"
    lines = text.splitlines()
    current_task_name = ""
    current_task_closed = False
    closed_statuses = {"done", "deferred", "parked", "dropped"}

    def _flush_current_task() -> None:
        nonlocal current_task_name, current_task_closed
        if not current_task_name or current_task_closed:
            current_task_name = ""
            current_task_closed = False
            return
        due_date = today_iso if current_phase.startswith("P0.") else ""
        tasks.append(
            BacklogTask(
                title=current_task_name,
                source=str(source_path),
                section=current_phase,
                track="AIPrompt",
                due_date=due_date,
            )
        )
        current_task_name = ""
        current_task_closed = False

    for line in lines:
        phase = re.match(r"^\s*##\s+(P[0-9][A-Z0-9\-]*\.\s+.+?)\s*$", line)
        if phase:
            _flush_current_task()
            current_phase = phase.group(1).strip()
            continue
        m = re.match(r"^\s*##\s+작업\s+(\d+)\.\s+(.+?)\s*$", line)
        if m:
            _flush_current_task()
            task_name = re.sub(r"`([^`]+)`", r"\1", m.group(2).strip())
            current_task_name = f"작업 {m.group(1)} {task_name}"
            current_task_closed = False
            continue
        if current_task_name:
            status_match = re.match(r"^\s*-\s*자동동기화 상태:\s*(.+?)\s*$", line)
            if status_match:
                status_value = str(status_match.group(1) or "").strip().lower()
                if status_value in closed_statuses:
                    current_task_closed = True
    _flush_current_task()
    return tasks


def _dedupe(tasks: list[BacklogTask]) -> list[BacklogTask]:
    seen: set[str] = set()
    out: list[BacklogTask] = []
    for t in tasks:
        key = re.sub(r"\s+", " ", t.title).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def _infer_apply_target_text(text: str) -> str:
    raw = str(text or "").lower()
    has_remote = any(keyword in raw for keyword in APPLY_TARGET_REMOTE_KEYWORDS)
    has_main = any(keyword in raw for keyword in APPLY_TARGET_MAIN_KEYWORDS)
    if has_remote and has_main:
        return "main,remote"
    if has_remote:
        return "remote"
    if has_main:
        return "main"
    return "-"


def _ensure_apply_target(task: BacklogTask) -> BacklogTask:
    if str(task.apply_target or "").strip():
        return task
    apply_target = _infer_apply_target_text(f"{task.title} {task.section} {task.source}")
    return replace(task, apply_target=apply_target)


def collect_backlog_tasks() -> list[BacklogTask]:
    tasks = []
    tasks.extend(parse_plan_tasks())
    tasks.extend(parse_checklist_tasks())
    tasks.extend(parse_scalping_logic_tasks())
    tasks.extend(parse_prompt_tasks())
    return _dedupe([_ensure_apply_target(t) for t in tasks])


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None or not str(value).strip():
        value = default
    if value is None or not str(value).strip():
        raise RuntimeError(f"missing required env: {name}")
    return str(value)


def _env_bool(name: str, default: bool) -> bool:
    raw_env = os.getenv(name)
    if raw_env is None or not str(raw_env).strip():
        return default
    raw = str(raw_env).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw_env = os.getenv(name)
    if raw_env is None or not str(raw_env).strip():
        return default
    try:
        return int(str(raw_env).strip())
    except ValueError:
        return default


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
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    errors = parsed.get("errors") or []
    fatal: list[dict[str, Any]] = []
    for err in errors:
        err_type = str(err.get("type") or "")
        err_path = err.get("path") or []
        if err_type == "NOT_FOUND" and err_path in (["organization"], ["user"]):
            continue
        fatal.append(err)
    if fatal:
        raise RuntimeError(f"github graphql errors: {fatal}")
    return parsed.get("data") or {}


def _project_query() -> str:
    return """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      title
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
      }
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on DraftIssue { title }
            ... on Issue { title }
            ... on PullRequest { title }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
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
      id
      title
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
      }
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on DraftIssue { title }
            ... on Issue { title }
            ... on PullRequest { title }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
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


def _project_node(data: dict[str, Any]) -> dict[str, Any]:
    node = ((data.get("organization") or {}).get("projectV2")) or ((data.get("user") or {}).get("projectV2"))
    if not node:
        raise RuntimeError("project not found")
    return node


def _fetch_project_metadata(
    token: str,
    owner: str,
    project_number: int,
    due_field_name: str,
    slot_field_name: str,
    time_window_field_name: str,
) -> tuple[str, dict[str, Any], set[str], list[ProjectItem]]:
    query = _project_query()
    cursor: str | None = None
    project_id = ""
    fields: dict[str, Any] = {}
    existing_titles: set[str] = set()
    existing_items: list[ProjectItem] = []

    while True:
        data = _graphql_request(token, query, {"owner": owner, "number": project_number, "cursor": cursor})
        project = _project_node(data)
        if not project_id:
            project_id = str(project.get("id") or "")
            for f in (project.get("fields") or {}).get("nodes") or []:
                name = str(f.get("name") or "").strip()
                if name:
                    fields[name] = f
        for node in (project.get("items") or {}).get("nodes") or []:
            content = node.get("content") or {}
            title = str(content.get("title") or "").strip()
            content_type = str(content.get("__typename") or "").strip()
            item_id = str(node.get("id") or "").strip()
            due_date_value = ""
            slot_value = ""
            time_window_value = ""
            for fv in (node.get("fieldValues") or {}).get("nodes") or []:
                field_name = str(((fv.get("field") or {}).get("name")) or "").strip()
                kind = str(fv.get("__typename") or "")
                if field_name == due_field_name and kind == "ProjectV2ItemFieldDateValue":
                    due_date_value = str(fv.get("date") or "").strip()
                elif field_name == slot_field_name:
                    if kind == "ProjectV2ItemFieldSingleSelectValue":
                        slot_value = str(fv.get("name") or "").strip()
                    elif kind == "ProjectV2ItemFieldTextValue" and not slot_value:
                        slot_value = str(fv.get("text") or "").strip()
                elif field_name == time_window_field_name:
                    if kind == "ProjectV2ItemFieldSingleSelectValue":
                        time_window_value = str(fv.get("name") or "").strip()
                    elif kind == "ProjectV2ItemFieldTextValue" and not time_window_value:
                        time_window_value = str(fv.get("text") or "").strip()
            if title:
                existing_titles.add(title)
                if item_id:
                    existing_items.append(
                        ProjectItem(
                            item_id=item_id,
                            title=title,
                            content_type=content_type,
                            due_date=due_date_value,
                            slot=slot_value,
                            time_window=time_window_value,
                        ),
                    )
        page = (project.get("items") or {}).get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page.get("endCursor")
    if not project_id:
        raise RuntimeError("project id missing")
    return project_id, fields, existing_titles, existing_items


def _mutation_add_draft() -> str:
    return """
mutation($projectId: ID!, $title: String!, $body: String!) {
  addProjectV2DraftIssue(input: { projectId: $projectId, title: $title, body: $body }) {
    projectItem { id }
  }
}
""".strip()


def _mutation_update_field() -> str:
    return """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(
    input: { projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value }
  ) {
    projectV2Item { id }
  }
}
""".strip()


def _title_for_project(task: BacklogTask) -> str:
    return f"[{task.track}] {task.title}".strip()


def _managed_title_key(title: str) -> str:
    normalized = title.strip()
    normalized = re.sub(r"^\[Checklist\d{4}\]", "[Checklist]", normalized)
    return normalized


def _is_managed_project_title(title: str) -> bool:
    normalized = title.strip()
    if re.match(r"^\[Checklist\d{4}\]\s+.+", normalized):
        return True
    return bool(re.match(rf"^\[({'|'.join(MANAGED_TRACKS)})\]\s+.+", normalized))


def _slot_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def _extract_explicit_slot_label(text: str) -> str:
    match = re.search(r"\bSlot\s*:\s*([A-Za-z_ -]+)", text, re.IGNORECASE)
    if not match:
        return ""
    value = _slot_key(match.group(1))
    if value == "preopen":
        return "PREOPEN"
    if value == "intraday":
        return "INTRADAY"
    if value == "postclose":
        return "POSTCLOSE"
    return ""


def _infer_slot_label(task: BacklogTask) -> str:
    explicit_slot = _extract_explicit_slot_label(str(task.title or ""))
    if explicit_slot:
        return explicit_slot

    section_text = str(task.section or "").lower()
    if any(keyword.lower() in section_text for keyword in SLOT_PREOPEN_KEYWORDS):
        return "PREOPEN"
    if any(keyword.lower() in section_text for keyword in SLOT_POSTCLOSE_KEYWORDS):
        return "POSTCLOSE"
    if any(keyword.lower() in section_text for keyword in SLOT_INTRADAY_KEYWORDS):
        return "INTRADAY"

    text = f"{task.title} {task.section}".lower()
    if any(keyword.lower() in text for keyword in SLOT_PREOPEN_KEYWORDS):
        return "PREOPEN"
    if any(keyword.lower() in text for keyword in SLOT_POSTCLOSE_KEYWORDS):
        return "POSTCLOSE"
    if any(keyword.lower() in text for keyword in SLOT_INTRADAY_KEYWORDS):
        return "INTRADAY"
    if CHECKLIST_TRACK_RE.match(str(task.track or "")):
        return "PREOPEN"
    return TRACK_DEFAULT_SLOT.get(task.track, "POSTCLOSE")


def _find_option_id_by_name(options: list[dict[str, Any]], option_name: str) -> str:
    wanted = _slot_key(option_name)
    for opt in options:
        if _slot_key(str(opt.get("name") or "")) == wanted:
            return str(opt.get("id") or "")
    return ""


def _slot_equals(left: str, right: str) -> bool:
    return _slot_key(left) == _slot_key(right)


def _extract_time_range_from_text(text: str) -> tuple[str, str]:
    m = re.search(
        r"(?P<start>\d{1,2}:\d{2})\s*(?:~|〜|∼|-|–|—|to)\s*(?P<end>\d{1,2}:\d{2})",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group("start"), m.group("end")
    m2 = re.search(r"(?<!\d)(?P<single>\d{1,2}:\d{2})(?!\d)", text)
    if m2:
        return m2.group("single"), ""
    return "", ""


def _normalize_hhmm(raw: str) -> str:
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", raw)
    if not m:
        return ""
    h = int(m.group(1))
    mm = int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mm <= 59):
        return ""
    return f"{h:02d}:{mm:02d}"


def _add_minutes(hhmm: str, minutes: int) -> str:
    normalized = _normalize_hhmm(hhmm)
    if not normalized:
        return ""
    h = int(normalized[:2])
    m = int(normalized[3:])
    total = h * 60 + m + minutes
    total = max(0, min(total, 23 * 60 + 59))
    return f"{total // 60:02d}:{total % 60:02d}"


def _is_all_day_or_unscheduled(text: str) -> str:
    lowered = text.lower()
    if any(k.lower() in lowered for k in TIME_ALLDAY_KEYWORDS):
        return "ALLDAY"
    if any(k.lower() in lowered for k in TIME_UNSCHEDULED_KEYWORDS):
        return "UNSCHEDULED"
    return ""


def _time_window_equals(left: str, right: str) -> bool:
    return re.sub(r"\s+", "", left.strip().lower()) == re.sub(r"\s+", "", right.strip().lower())


def _infer_time_window(task: BacklogTask, *, slot_label: str, default_duration_min: int) -> str:
    text = f"{task.title} {task.section}"
    mode = _is_all_day_or_unscheduled(text)
    if mode:
        return mode

    due_date = (task.due_date or "").strip()
    holiday_forced_intraday = False
    if due_date:
        try:
            is_trading_day, _ = get_krx_trading_day_status(datetime.fromisoformat(due_date).date())
            if not is_trading_day and slot_label in {"PREOPEN", "POSTCLOSE"}:
                slot_label = "INTRADAY"
                holiday_forced_intraday = True
        except Exception:
            pass

    start, end = _extract_time_range_from_text(text)
    start = _normalize_hhmm(start)
    end = _normalize_hhmm(end)
    if start and end and slot_label == "INTRADAY" and not holiday_forced_intraday:
        return f"{start}~{end}"
    if start and slot_label == "INTRADAY" and not holiday_forced_intraday:
        end_auto = _add_minutes(start, max(5, default_duration_min))
        return f"{start}~{end_auto}" if end_auto else start

    slot_default_start = {
        "PREOPEN": "08:20",
        "INTRADAY": "10:00",
        "POSTCLOSE": "15:40",
    }.get(slot_label, "15:40")
    slot_default_start = _normalize_hhmm(slot_default_start) or "15:40"
    slot_default_end = _add_minutes(slot_default_start, max(5, default_duration_min)) or slot_default_start
    return f"{slot_default_start}~{slot_default_end}"


def _desired_status_option_id(
    *,
    title: str,
    desired_open_title_keys: set[str],
    todo_option_id: str,
    done_option_id: str,
) -> str:
    if not _is_managed_project_title(title):
        return ""
    return todo_option_id if _managed_title_key(title) in desired_open_title_keys else done_option_id


def _body_for_project(task: BacklogTask) -> str:
    return "\n".join(
        [
            f"Source: `{task.source}`",
            f"Section: `{task.section}`",
            f"Track: `{task.track}`",
            f"ApplyTarget: `{task.apply_target or '-'}`",
            f"Due: `{task.due_date or '-'}`",
            "",
            "Generated by `sync_docs_backlog_to_project.py`.",
        ]
    )


def sync_backlog_to_project(*, dry_run: bool = False, limit: int = 150) -> dict[str, Any]:
    tasks = collect_backlog_tasks()[:limit]
    token = _env("GH_PROJECT_TOKEN", os.getenv("GITHUB_TOKEN"))
    owner = _env("GH_PROJECT_OWNER")
    number = int(_env("GH_PROJECT_NUMBER"))
    status_field_name = _env("GH_PROJECT_STATUS_FIELD_NAME", "Status")
    due_field_name = _env("GH_PROJECT_DUE_FIELD_NAME", "Due")
    slot_field_name = _env("GH_PROJECT_SLOT_FIELD_NAME", "Slot")
    time_window_field_name = _env("GH_PROJECT_TIME_WINDOW_FIELD_NAME", "TimeWindow")
    todo_option_name = _env("GH_PROJECT_TODO_OPTION_NAME", "Todo")
    done_option_name = _env("GH_PROJECT_DONE_OPTION_NAME", "Done")
    slot_preopen_option_name = _env("GH_PROJECT_SLOT_PREOPEN_OPTION_NAME", "PREOPEN")
    slot_intraday_option_name = _env("GH_PROJECT_SLOT_INTRADAY_OPTION_NAME", "INTRADAY")
    slot_postclose_option_name = _env("GH_PROJECT_SLOT_POSTCLOSE_OPTION_NAME", "POSTCLOSE")
    auto_fill_slot = _env_bool("GH_PROJECT_AUTO_FILL_SLOT", True)
    reclassify_slot = _env_bool("GH_PROJECT_RECLASSIFY_SLOT", True)
    auto_fill_time_window = _env_bool("GH_PROJECT_AUTO_FILL_TIME_WINDOW", True)
    reclassify_time_window = _env_bool("GH_PROJECT_RECLASSIFY_TIME_WINDOW", True)
    default_duration_min = _env_int("GCAL_SLOT_DURATION_MINUTES", 30)

    project_id, fields, existing_titles, existing_items = _fetch_project_metadata(
        token,
        owner,
        number,
        due_field_name,
        slot_field_name,
        time_window_field_name,
    )

    status_field = fields.get(status_field_name)
    due_field = fields.get(due_field_name)
    slot_field = fields.get(slot_field_name)
    time_window_field = fields.get(time_window_field_name)
    status_option_id = ""
    done_status_option_id = ""
    if status_field and str(status_field.get("__typename")) == "ProjectV2SingleSelectField":
        for opt in status_field.get("options") or []:
            if str(opt.get("name") or "").strip() == todo_option_name:
                status_option_id = str(opt.get("id") or "")
            if str(opt.get("name") or "").strip() == done_option_name:
                done_status_option_id = str(opt.get("id") or "")

    slot_option_ids: dict[str, str] = {}
    slot_field_type = str(slot_field.get("__typename") or "") if slot_field else ""
    slot_field_data_type = str(slot_field.get("dataType") or "") if slot_field else ""
    if slot_field and slot_field_type == "ProjectV2SingleSelectField":
        options = slot_field.get("options") or []
        slot_option_ids = {
            "PREOPEN": _find_option_id_by_name(options, slot_preopen_option_name),
            "INTRADAY": _find_option_id_by_name(options, slot_intraday_option_name),
            "POSTCLOSE": _find_option_id_by_name(options, slot_postclose_option_name),
        }
        missing = [name for name, oid in slot_option_ids.items() if not oid]
        if auto_fill_slot and missing:
            print(
                f"[DOC_BACKLOG_SYNC_WARN] slot option mapping missing: {', '.join(missing)}",
                file=sys.stderr,
            )
    elif auto_fill_slot and not slot_field:
        print(
            f"[DOC_BACKLOG_SYNC_WARN] slot field not found: {slot_field_name}",
            file=sys.stderr,
        )

    time_window_field_type = str(time_window_field.get("__typename") or "") if time_window_field else ""
    time_window_field_data_type = str(time_window_field.get("dataType") or "") if time_window_field else ""
    if auto_fill_time_window and not time_window_field:
        print(
            f"[DOC_BACKLOG_SYNC_WARN] time window field not found: {time_window_field_name}",
            file=sys.stderr,
        )

    add_mut = _mutation_add_draft()
    upd_mut = _mutation_update_field()
    tasks_by_title = {_title_for_project(task): task for task in tasks}
    tasks_by_key = {_managed_title_key(_title_for_project(task)): task for task in tasks}
    slot_by_title = {
        _title_for_project(task): _infer_slot_label(task)
        for task in tasks
    }
    time_window_by_title = {
        _title_for_project(task): _infer_time_window(
            task,
            slot_label=slot_by_title[_title_for_project(task)],
            default_duration_min=default_duration_min,
        )
        for task in tasks
    }
    desired_open_titles = set(tasks_by_title.keys())
    desired_open_title_keys = {_managed_title_key(title) for title in desired_open_titles}
    existing_title_keys = {_managed_title_key(title) for title in existing_titles}
    managed_open_items = [
        item
        for item in existing_items
        if _is_managed_project_title(item.title) and _managed_title_key(item.title) in desired_open_title_keys
    ]
    managed_open_blank_slot = sum(1 for item in managed_open_items if not item.slot.strip())
    managed_open_blank_time_window = sum(1 for item in managed_open_items if not item.time_window.strip())

    created = 0
    skipped_existing = 0
    for task in tasks:
        title = _title_for_project(task)
        if title in existing_titles or _managed_title_key(title) in existing_title_keys:
            skipped_existing += 1
            continue
        if dry_run:
            created += 1
            continue

        created_item = _graphql_request(
            token,
            add_mut,
            {
                "projectId": project_id,
                "title": title,
                "body": _body_for_project(task),
            },
        )
        item_id = ((created_item.get("addProjectV2DraftIssue") or {}).get("projectItem") or {}).get("id")
        if not item_id:
            continue

        if status_field and status_option_id:
            _graphql_request(
                token,
                upd_mut,
                {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": status_field["id"],
                    "value": {"singleSelectOptionId": status_option_id},
                },
            )

        if due_field and task.due_date:
            due_type = str(due_field.get("__typename") or "")
            due_data_type = str(due_field.get("dataType") or "")
            if due_type == "ProjectV2Field" and due_data_type == "DATE":
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": due_field["id"],
                        "value": {"date": task.due_date},
                    },
                )

        if auto_fill_slot and slot_field:
            inferred_slot = slot_by_title.get(title, _infer_slot_label(task))
            if slot_field_type == "ProjectV2SingleSelectField":
                slot_option_id = slot_option_ids.get(inferred_slot, "")
                if slot_option_id:
                    _graphql_request(
                        token,
                        upd_mut,
                        {
                            "projectId": project_id,
                            "itemId": item_id,
                            "fieldId": slot_field["id"],
                            "value": {"singleSelectOptionId": slot_option_id},
                        },
                    )
            elif slot_field_type == "ProjectV2Field" and str(slot_field.get("dataType") or "") == "TEXT":
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": slot_field["id"],
                        "value": {"text": inferred_slot},
                    },
                )

        if auto_fill_time_window and time_window_field:
            inferred_time_window = time_window_by_title.get(
                title,
                _infer_time_window(
                    task,
                    slot_label=slot_by_title.get(title, _infer_slot_label(task)),
                    default_duration_min=default_duration_min,
                ),
            )
            if time_window_field_type == "ProjectV2Field" and time_window_field_data_type == "TEXT":
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": time_window_field["id"],
                        "value": {"text": inferred_time_window},
                    },
                )
        created += 1

    synced_status_todo = 0
    synced_status_done = 0
    if status_field and status_option_id:
        for item in existing_items:
            desired_option_id = _desired_status_option_id(
                title=item.title,
                desired_open_title_keys=desired_open_title_keys,
                todo_option_id=status_option_id,
                done_option_id=done_status_option_id,
            )
            if not desired_option_id:
                continue
            if dry_run:
                if desired_option_id == status_option_id:
                    synced_status_todo += 1
                else:
                    synced_status_done += 1
                continue
            _graphql_request(
                token,
                upd_mut,
                {
                    "projectId": project_id,
                    "itemId": item.item_id,
                    "fieldId": status_field["id"],
                    "value": {"singleSelectOptionId": desired_option_id},
                },
            )
            if desired_option_id == status_option_id:
                synced_status_todo += 1
            else:
                synced_status_done += 1

    synced_due_filled = 0
    synced_due_reclassified = 0
    if due_field:
        due_type = str(due_field.get("__typename") or "")
        due_data_type = str(due_field.get("dataType") or "")
        if due_type == "ProjectV2Field" and due_data_type == "DATE":
            for item in existing_items:
                if not _is_managed_project_title(item.title):
                    continue
                if _managed_title_key(item.title) not in desired_open_title_keys:
                    continue
                task = tasks_by_key.get(_managed_title_key(item.title))
                if not task or not task.due_date:
                    continue
                existing_due = item.due_date.strip()
                if existing_due == task.due_date:
                    continue
                if dry_run:
                    if existing_due:
                        synced_due_reclassified += 1
                    else:
                        synced_due_filled += 1
                    continue
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item.item_id,
                        "fieldId": due_field["id"],
                        "value": {"date": task.due_date},
                    },
                )
                if existing_due:
                    synced_due_reclassified += 1
                else:
                    synced_due_filled += 1

    synced_slot_filled = 0
    synced_slot_reclassified = 0
    if auto_fill_slot and slot_field:
        for item in existing_items:
            if not _is_managed_project_title(item.title):
                continue
            if _managed_title_key(item.title) not in desired_open_title_keys:
                continue
            task = tasks_by_key.get(_managed_title_key(item.title))
            if not task:
                continue
            inferred_slot = slot_by_title.get(item.title, _infer_slot_label(task))
            if not inferred_slot:
                continue
            existing_slot = item.slot.strip()
            if existing_slot and not reclassify_slot:
                continue
            if existing_slot and _slot_equals(existing_slot, inferred_slot):
                continue

            if slot_field_type == "ProjectV2SingleSelectField":
                slot_option_id = slot_option_ids.get(inferred_slot, "")
                if not slot_option_id:
                    continue
                if dry_run:
                    if existing_slot:
                        synced_slot_reclassified += 1
                    else:
                        synced_slot_filled += 1
                    continue
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item.item_id,
                        "fieldId": slot_field["id"],
                        "value": {"singleSelectOptionId": slot_option_id},
                    },
                )
                if existing_slot:
                    synced_slot_reclassified += 1
                else:
                    synced_slot_filled += 1
            elif slot_field_type == "ProjectV2Field" and str(slot_field.get("dataType") or "") == "TEXT":
                if dry_run:
                    if existing_slot:
                        synced_slot_reclassified += 1
                    else:
                        synced_slot_filled += 1
                    continue
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item.item_id,
                        "fieldId": slot_field["id"],
                        "value": {"text": inferred_slot},
                    },
                )
                if existing_slot:
                    synced_slot_reclassified += 1
                else:
                    synced_slot_filled += 1

    synced_time_window_filled = 0
    synced_time_window_reclassified = 0
    if auto_fill_time_window and time_window_field:
        for item in existing_items:
            if not _is_managed_project_title(item.title):
                continue
            if _managed_title_key(item.title) not in desired_open_title_keys:
                continue
            task = tasks_by_key.get(_managed_title_key(item.title))
            if not task:
                continue
            inferred_slot = slot_by_title.get(item.title, _infer_slot_label(task))
            inferred_time_window = time_window_by_title.get(
                item.title,
                _infer_time_window(task, slot_label=inferred_slot, default_duration_min=default_duration_min),
            )
            existing_time_window = item.time_window.strip()
            if existing_time_window and not reclassify_time_window:
                continue
            if existing_time_window and _time_window_equals(existing_time_window, inferred_time_window):
                continue
            if time_window_field_type == "ProjectV2Field" and time_window_field_data_type == "TEXT":
                if dry_run:
                    if existing_time_window:
                        synced_time_window_reclassified += 1
                    else:
                        synced_time_window_filled += 1
                    continue
                _graphql_request(
                    token,
                    upd_mut,
                    {
                        "projectId": project_id,
                        "itemId": item.item_id,
                        "fieldId": time_window_field["id"],
                        "value": {"text": inferred_time_window},
                    },
                )
                if existing_time_window:
                    synced_time_window_reclassified += 1
                else:
                    synced_time_window_filled += 1

    by_track: dict[str, int] = {}
    for t in tasks:
        by_track[t.track] = by_track.get(t.track, 0) + 1

    slot_update_mode = "none"
    if slot_field_type == "ProjectV2SingleSelectField":
        slot_update_mode = "single_select"
    elif slot_field_type == "ProjectV2Field" and slot_field_data_type == "TEXT":
        slot_update_mode = "text"

    return {
        "project_owner": owner,
        "project_number": number,
        "dry_run": dry_run,
        "parsed_tasks": len(tasks),
        "created_or_would_create": created,
        "skipped_existing": skipped_existing,
        "status_synced_todo": synced_status_todo,
        "status_synced_done": synced_status_done,
        "due_filled": synced_due_filled,
        "due_reclassified": synced_due_reclassified,
        "slot_filled": synced_slot_filled,
        "slot_reclassified": synced_slot_reclassified,
        "time_window_filled": synced_time_window_filled,
        "time_window_reclassified": synced_time_window_reclassified,
        "slot_debug": {
            "slot_field_name": slot_field_name,
            "slot_field_detected": bool(slot_field),
            "slot_field_type": slot_field_type or "-",
            "slot_field_data_type": slot_field_data_type or "-",
            "slot_update_mode": slot_update_mode,
            "auto_fill_slot": auto_fill_slot,
            "reclassify_slot": reclassify_slot,
            "slot_option_name_map": {
                "PREOPEN": slot_preopen_option_name,
                "INTRADAY": slot_intraday_option_name,
                "POSTCLOSE": slot_postclose_option_name,
            },
            "slot_option_id_map": slot_option_ids,
            "managed_open_items": len(managed_open_items),
            "managed_open_items_blank_slot": managed_open_blank_slot,
        },
        "time_window_debug": {
            "time_window_field_name": time_window_field_name,
            "time_window_field_detected": bool(time_window_field),
            "time_window_field_type": time_window_field_type or "-",
            "time_window_field_data_type": time_window_field_data_type or "-",
            "auto_fill_time_window": auto_fill_time_window,
            "reclassify_time_window": reclassify_time_window,
            "managed_open_items_blank_time_window": managed_open_blank_time_window,
        },
        "track_breakdown": by_track,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync remaining tasks from docs to GitHub Project")
    parser.add_argument("--dry-run", action="store_true", help="Do not write project items")
    parser.add_argument("--print-backlog-only", action="store_true", help="Only parse docs and print tasks")
    parser.add_argument("--limit", type=int, default=150, help="Max tasks to sync")
    args = parser.parse_args()

    if args.print_backlog_only:
        tasks = collect_backlog_tasks()[: args.limit]
        payload = {
            "count": len(tasks),
            "tasks": [t.__dict__ for t in tasks],
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    summary = sync_backlog_to_project(dry_run=args.dry_run, limit=args.limit)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[DOC_BACKLOG_SYNC_ERROR] {exc}", file=sys.stderr)
        raise
