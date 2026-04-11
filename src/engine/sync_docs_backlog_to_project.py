"""Parse planning docs and sync remaining tasks to GitHub Project v2 draft items."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request


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


@dataclass(frozen=True)
class ProjectItem:
    item_id: str
    title: str
    content_type: str
    slot: str = ""


MANAGED_TRACKS = ("Plan", "Checklist0413", "ScalpingLogic", "AIPrompt")

TRACK_DEFAULT_SLOT = {
    "Plan": "PREOPEN",
    "Checklist0413": "PREOPEN",
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
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        print(f"[DOC_BACKLOG_SYNC_WARN] missing source doc: {path}", file=sys.stderr)
        return None
    return _read(path)


def _read_candidates(paths: list[Path]) -> tuple[Path, str] | None:
    for path in paths:
        text = _read_optional(path)
        if text is not None:
            return path, text
    return None


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
    immediate = _parse_numbered_items(_extract_section_lines(text, "## 즉시 착수 체크리스트"))
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
    for item in immediate:
        tasks.append(
            BacklogTask(
                title=item,
                source=str(source_path),
                section="즉시 착수 체크리스트",
                track="Plan",
            )
        )
    return tasks


def parse_checklist_tasks() -> list[BacklogTask]:
    loaded = _read_candidates([DOC_CHECKLIST])
    if not loaded:
        return []
    source_path, text = loaded
    tasks: list[BacklogTask] = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*\[ \]\s+(.+?)\s*$", line)
        if not m:
            continue
        item = m.group(1).strip()
        item = re.sub(r"`([^`]+)`", r"\1", item)
        if not item:
            continue
        tasks.append(
            BacklogTask(
                title=item,
                source=str(source_path),
                section="체크박스 미완료",
                track="Checklist0413",
                due_date="2026-04-13",
            )
        )
    return tasks


def parse_scalping_logic_tasks() -> list[BacklogTask]:
    loaded = _read_candidates(_scalping_doc_candidates())
    if not loaded:
        return []
    source_path, text = loaded
    tasks: list[BacklogTask] = []

    # Remaining tasks in status memo
    in_remaining = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- 잔여:"):
            in_remaining = True
            continue
        if in_remaining and stripped.startswith("- 즉,"):
            in_remaining = False
        if not in_remaining:
            continue
        m = re.match(r"^\s*-\s+`([^`]+)`\s*$", line)
        if not m:
            continue
        tasks.append(
            BacklogTask(
                title=m.group(1).strip(),
                source=str(source_path),
                section="상태 메모 잔여",
                track="ScalpingLogic",
            )
        )

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
    loaded = _read_candidates([DOC_PROMPT])
    if not loaded:
        return []
    source_path, text = loaded
    tasks: list[BacklogTask] = []

    # Priority table
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| 우선순위 | 작업명 |"):
            in_table = True
            continue
        if in_table and (not line.strip().startswith("|") or line.strip().startswith("---")):
            if not line.strip().startswith("|"):
                in_table = False
                continue
        if not in_table:
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        if parts[0] in {"우선순위", "---"}:
            continue
        task_name = re.sub(r"`([^`]+)`", r"\1", parts[1]).strip()
        if task_name:
                tasks.append(
                    BacklogTask(
                        title=task_name,
                        source=str(source_path),
                        section="작업 우선순위 요약",
                        track="AIPrompt",
                    )
                )

    # Explicit task headings (작업 1~12)
    for line in text.splitlines():
        m = re.match(r"^\s*##\s+작업\s+(\d+)\.\s+(.+?)\s*$", line)
        if not m:
            continue
        tasks.append(
            BacklogTask(
                title=f"작업 {m.group(1)} {m.group(2).strip()}",
                source=str(source_path),
                section="작업 상세",
                track="AIPrompt",
            )
        )
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


def collect_backlog_tasks() -> list[BacklogTask]:
    tasks = []
    tasks.extend(parse_plan_tasks())
    tasks.extend(parse_checklist_tasks())
    tasks.extend(parse_scalping_logic_tasks())
    tasks.extend(parse_prompt_tasks())
    return _dedupe(tasks)


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"missing required env: {name}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


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
    slot_field_name: str,
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
            slot_value = ""
            for fv in (node.get("fieldValues") or {}).get("nodes") or []:
                field_name = str(((fv.get("field") or {}).get("name")) or "").strip()
                kind = str(fv.get("__typename") or "")
                if field_name != slot_field_name:
                    continue
                if kind == "ProjectV2ItemFieldSingleSelectValue":
                    slot_value = str(fv.get("name") or "").strip()
                elif kind == "ProjectV2ItemFieldTextValue" and not slot_value:
                    slot_value = str(fv.get("text") or "").strip()
            if title:
                existing_titles.add(title)
                if item_id:
                    existing_items.append(
                        ProjectItem(item_id=item_id, title=title, content_type=content_type, slot=slot_value),
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


def _is_managed_project_title(title: str) -> bool:
    return bool(re.match(rf"^\[({'|'.join(MANAGED_TRACKS)})\]\s+.+", title.strip()))


def _slot_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def _infer_slot_label(task: BacklogTask) -> str:
    text = f"{task.title} {task.section}".lower()
    if any(keyword.lower() in text for keyword in SLOT_PREOPEN_KEYWORDS):
        return "PREOPEN"
    if any(keyword.lower() in text for keyword in SLOT_INTRADAY_KEYWORDS):
        return "INTRADAY"
    if any(keyword.lower() in text for keyword in SLOT_POSTCLOSE_KEYWORDS):
        return "POSTCLOSE"
    return TRACK_DEFAULT_SLOT.get(task.track, "POSTCLOSE")


def _find_option_id_by_name(options: list[dict[str, Any]], option_name: str) -> str:
    wanted = _slot_key(option_name)
    for opt in options:
        if _slot_key(str(opt.get("name") or "")) == wanted:
            return str(opt.get("id") or "")
    return ""


def _desired_status_option_id(
    *,
    title: str,
    desired_open_titles: set[str],
    todo_option_id: str,
    done_option_id: str,
) -> str:
    if not _is_managed_project_title(title):
        return ""
    return todo_option_id if title in desired_open_titles else done_option_id


def _body_for_project(task: BacklogTask) -> str:
    return "\n".join(
        [
            f"Source: `{task.source}`",
            f"Section: `{task.section}`",
            f"Track: `{task.track}`",
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
    todo_option_name = _env("GH_PROJECT_TODO_OPTION_NAME", "Todo")
    done_option_name = _env("GH_PROJECT_DONE_OPTION_NAME", "Done")
    slot_preopen_option_name = _env("GH_PROJECT_SLOT_PREOPEN_OPTION_NAME", "PREOPEN")
    slot_intraday_option_name = _env("GH_PROJECT_SLOT_INTRADAY_OPTION_NAME", "INTRADAY")
    slot_postclose_option_name = _env("GH_PROJECT_SLOT_POSTCLOSE_OPTION_NAME", "POSTCLOSE")
    auto_fill_slot = _env_bool("GH_PROJECT_AUTO_FILL_SLOT", True)

    project_id, fields, existing_titles, existing_items = _fetch_project_metadata(
        token,
        owner,
        number,
        slot_field_name,
    )

    status_field = fields.get(status_field_name)
    due_field = fields.get(due_field_name)
    slot_field = fields.get(slot_field_name)
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
    if slot_field and slot_field_type == "ProjectV2SingleSelectField":
        options = slot_field.get("options") or []
        slot_option_ids = {
            "PREOPEN": _find_option_id_by_name(options, slot_preopen_option_name),
            "INTRADAY": _find_option_id_by_name(options, slot_intraday_option_name),
            "POSTCLOSE": _find_option_id_by_name(options, slot_postclose_option_name),
        }

    add_mut = _mutation_add_draft()
    upd_mut = _mutation_update_field()
    tasks_by_title = {_title_for_project(task): task for task in tasks}
    desired_open_titles = set(tasks_by_title.keys())

    created = 0
    skipped_existing = 0
    for task in tasks:
        title = _title_for_project(task)
        if title in existing_titles:
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
            inferred_slot = _infer_slot_label(task)
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
        created += 1

    synced_status_todo = 0
    synced_status_done = 0
    if status_field and status_option_id:
        for item in existing_items:
            desired_option_id = _desired_status_option_id(
                title=item.title,
                desired_open_titles=desired_open_titles,
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

    synced_slot_filled = 0
    if auto_fill_slot and slot_field:
        for item in existing_items:
            if not _is_managed_project_title(item.title):
                continue
            if item.title not in desired_open_titles:
                continue
            if item.slot.strip():
                continue
            task = tasks_by_title.get(item.title)
            if not task:
                continue
            inferred_slot = _infer_slot_label(task)
            if not inferred_slot:
                continue

            if slot_field_type == "ProjectV2SingleSelectField":
                slot_option_id = slot_option_ids.get(inferred_slot, "")
                if not slot_option_id:
                    continue
                if dry_run:
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
                synced_slot_filled += 1
            elif slot_field_type == "ProjectV2Field" and str(slot_field.get("dataType") or "") == "TEXT":
                if dry_run:
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
                synced_slot_filled += 1

    by_track: dict[str, int] = {}
    for t in tasks:
        by_track[t.track] = by_track.get(t.track, 0) + 1

    return {
        "project_owner": owner,
        "project_number": number,
        "dry_run": dry_run,
        "parsed_tasks": len(tasks),
        "created_or_would_create": created,
        "skipped_existing": skipped_existing,
        "status_synced_todo": synced_status_todo,
        "status_synced_done": synced_status_done,
        "slot_filled": synced_slot_filled,
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
