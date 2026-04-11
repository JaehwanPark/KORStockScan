"""Build daily Codex workorder markdown from GitHub Project v2 items."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


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
    assignees: str
    state: str


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None or not str(value).strip():
        value = default
    if value is None or not str(value).strip():
        raise RuntimeError(f"missing required env: {name}")
    return str(value)


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
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
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
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on PullRequest {
              title
              url
              state
              assignees(first: 5) { nodes { login } }
            }
            ... on DraftIssue {
              title
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
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
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


def _parse_project_item(
    node: dict[str, Any],
    *,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
) -> ProjectTask | None:
    if bool(node.get("isArchived")):
        return None

    content = node.get("content") or {}
    content_type = str(content.get("__typename") or "Unknown")
    title = str(content.get("title") or "").strip() or "(untitled)"
    url = str(content.get("url") or "").strip()
    state = str(content.get("state") or "").strip()
    assignees_nodes = ((content.get("assignees") or {}).get("nodes") or []) if content else []
    assignees = ", ".join(str(n.get("login") or "").strip() for n in assignees_nodes if n.get("login"))

    due_date = ""
    status = ""
    track = ""
    slot = ""
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
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == track_field_name and not track:
            track = str(fv.get("text") or "").strip()
        elif kind == "ProjectV2ItemFieldTextValue" and field_name == slot_field_name and not slot:
            slot = str(fv.get("text") or "").strip()

    return ProjectTask(
        item_id=str(node.get("id") or "").strip(),
        content_type=content_type,
        title=title,
        url=url,
        due_date=due_date,
        status=status,
        track=track,
        slot=slot,
        assignees=assignees,
        state=state,
    )


def _matches_slot(item_slot: str, target_slots: set[str]) -> bool:
    if not target_slots:
        return True
    return _norm(item_slot) in target_slots


def fetch_project_tasks(
    *,
    token: str,
    owner: str,
    number: int,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
    include_statuses: list[str],
    include_slots: list[str],
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
            )
            if not item:
                continue
            if include_set and _norm(item.status) not in include_set:
                continue
            if not _matches_slot(item.slot, slot_set):
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


def render_markdown(
    *,
    owner: str,
    project_number: int,
    project_title: str,
    generated_at: str,
    statuses: list[str],
    slots: list[str],
    tasks: list[ProjectTask],
    max_items: int,
) -> str:
    top = sort_tasks(tasks, statuses)[:max_items]
    track_counts: dict[str, int] = {}
    for item in top:
        key = item.track or "-"
        track_counts[key] = track_counts.get(key, 0) + 1

    lines: list[str] = []
    lines.append("# Codex 일일 작업지시서")
    lines.append("")
    lines.append(f"- 생성시각: `{generated_at}`")
    lines.append(f"- 프로젝트: `{owner}` / `#{project_number}` / `{project_title or '-'}`")
    lines.append(f"- 상태필터: `{', '.join(statuses) if statuses else '전체'}`")
    lines.append(f"- 슬롯필터: `{', '.join(slots) if slots else '전체'}`")
    lines.append(f"- 후보건수: `{len(tasks)}` / 지시반영건수: `{len(top)}`")
    if track_counts:
        compact = ", ".join(f"{k}:{v}" for k, v in sorted(track_counts.items(), key=lambda kv: kv[0]))
        lines.append(f"- Track 분포: `{compact}`")
    lines.append("")
    lines.append("## 오늘 Codex 실행 큐")
    lines.append("")
    if not top:
        lines.append("1. 현재 상태필터에 해당하는 항목이 없습니다.")
    else:
        for idx, item in enumerate(top, start=1):
            lines.append(f"{idx}. `{item.title}`")
            lines.append(
                f"   - 상태: `{item.status or '-'}` / 슬롯: `{item.slot or '-'}` / 트랙: `{item.track or '-'}` / Due: `{item.due_date or '-'}`"
            )
            if item.assignees:
                lines.append(f"   - 담당자: `{item.assignees}`")
            if item.url:
                lines.append(f"   - 링크: {item.url}")
            lines.append(f"   - Project Item ID: `{item.item_id}`")
    lines.append("")
    lines.append("## Codex 전달 템플릿")
    lines.append("")
    lines.append("```text")
    lines.append("아래 Project 항목을 오늘 작업 대상으로 처리해줘.")
    lines.append("원칙:")
    lines.append("- 판정, 근거, 다음 액션 순서로 보고")
    lines.append("- 관련 문서/체크리스트 동시 업데이트")
    lines.append("- 테스트/검증 결과 포함")
    lines.append("")
    lines.append("[대상 항목]")
    if top:
        for item in top:
            lines.append(
                f"- {item.title} | 상태={item.status or '-'} | 슬롯={item.slot or '-'} | Due={item.due_date or '-'} | ID={item.item_id}"
            )
    else:
        lines.append("- 없음")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_daily_workorder(*, output: Path, max_items: int, slots: list[str] | None = None) -> dict[str, Any]:
    token = _env("GH_PROJECT_TOKEN", os.getenv("GITHUB_TOKEN"))
    owner = _env("GH_PROJECT_OWNER")
    number = int(_env("GH_PROJECT_NUMBER"))
    due_field_name = _env("GH_PROJECT_DUE_FIELD_NAME", "Due")
    status_field_name = _env("GH_PROJECT_STATUS_FIELD_NAME", "Status")
    track_field_name = _env("GH_PROJECT_TRACK_FIELD_NAME", "Track")
    slot_field_name = _env("GH_PROJECT_SLOT_FIELD_NAME", "Slot")
    statuses = _split_csv(os.getenv("GH_CODEX_WORKORDER_STATUSES", "Todo,In Progress"))
    configured_slots = _split_csv(os.getenv("GH_CODEX_WORKORDER_SLOTS", ""))
    selected_slots = slots if slots is not None else configured_slots

    project_title, tasks = fetch_project_tasks(
        token=token,
        owner=owner,
        number=number,
        due_field_name=due_field_name,
        status_field_name=status_field_name,
        track_field_name=track_field_name,
        slot_field_name=slot_field_name,
        include_statuses=statuses,
        include_slots=selected_slots,
    )
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    markdown = render_markdown(
        owner=owner,
        project_number=number,
        project_title=project_title,
        generated_at=generated_at,
        statuses=statuses,
        slots=selected_slots,
        tasks=tasks,
        max_items=max_items,
    )
    write_markdown(output, markdown)

    return {
        "project_owner": owner,
        "project_number": number,
        "project_title": project_title,
        "status_filter": statuses,
        "slot_filter": selected_slots,
        "candidate_tasks": len(tasks),
        "output": str(output),
        "max_items": max_items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Codex daily workorder markdown from GitHub Project")
    parser.add_argument("--output", default="tmp/codex_daily_workorder.md", help="Output markdown path")
    parser.add_argument("--max-items", type=int, default=20, help="Max items in workorder")
    parser.add_argument("--slot", action="append", default=[], help="Target slot filter (repeatable)")
    args = parser.parse_args()

    slot_filter = [s.strip() for s in args.slot if s.strip()] or None
    summary = build_daily_workorder(output=Path(args.output), max_items=max(1, args.max_items), slots=slot_filter)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[CODEX_DAILY_WORKORDER_ERROR] {exc}", file=sys.stderr)
        raise
