"""Sync GitHub Project v2 items to Google Calendar events.

This script is designed for one-way sync:
GitHub Project (source of truth) -> Google Calendar.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from urllib import request

from src.engine.sync_docs_backlog_to_project import (
    collect_backlog_tasks,
    _is_managed_project_title,
    _title_for_project,
)
from src.utils.market_day import get_krx_trading_day_status


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"


@dataclass
class ProjectItem:
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


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"missing required env: {name}")
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = str(os.getenv(name, str(default))).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _norm_key(value: str) -> str:
    return "".join(ch for ch in value.strip().lower() if ch.isalnum())


def _status_allowed(status: str, allowed_statuses: set[str]) -> bool:
    if not allowed_statuses:
        return True
    current = _norm_key(status)
    if not current:
        return False
    return current in {_norm_key(item) for item in allowed_statuses if item.strip()}


def _managed_open_titles_from_docs() -> set[str] | None:
    try:
        return {_title_for_project(task) for task in collect_backlog_tasks()}
    except Exception as exc:
        print(f"[PROJECT_CAL_SYNC_WARN] failed to parse docs backlog for managed title filter: {exc}", file=sys.stderr)
        return None


def _extract_time_range_from_text(text: str) -> tuple[str, str]:
    # Examples:
    # - "(13:20~13:35)"
    # - "10:20 - 10:35"
    # - "13:20"
    m = re.search(
        r"(?P<start>\d{1,2}:\d{2})\s*(?:~|〜|∼|-|–|—|to)\s*(?P<end>\d{1,2}:\d{2})",
        text,
        re.IGNORECASE,
    )
    if m:
        return (m.group("start"), m.group("end"))
    m2 = re.search(r"(?<!\d)(?P<single>\d{1,2}:\d{2})(?!\d)", text)
    if m2:
        return (m2.group("single"), "")
    return ("", "")


def _normalize_hhmm(raw: str) -> str:
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", raw)
    if not m:
        return ""
    hh = int(m.group(1))
    mm = int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return ""
    return f"{hh:02d}:{mm:02d}"


def _parse_time_window(value: str) -> tuple[str, str, str]:
    """Return (mode, start_hhmm, end_hhmm). mode: timed|all_day|unscheduled|none."""
    raw = (value or "").strip()
    if not raw:
        return ("none", "", "")
    key = _norm_key(raw)
    if key in {"allday", "alldayevent", "wholeday"} or "종일" in raw:
        return ("all_day", "", "")
    if key in {"tbd", "unscheduled", "notscheduled"} or "미정" in raw:
        return ("unscheduled", "", "")
    start, end = _extract_time_range_from_text(raw)
    start = _normalize_hhmm(start)
    end = _normalize_hhmm(end)
    if start and end:
        return ("timed", start, end)
    if start:
        return ("timed", start, "")
    return ("none", "", "")


def _graphql_query() -> str:
    return """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
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
      id
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
        # This query asks both organization and user project nodes to support
        # either owner type. One side may return NOT_FOUND and should not fail.
        if err_type == "NOT_FOUND" and err_path in (["organization"], ["user"]):
            continue
        fatal_errors.append(err)

    if fatal_errors:
        raise RuntimeError(f"github graphql errors: {fatal_errors}")
    return parsed["data"]


def _project_node(data: dict[str, Any]) -> dict[str, Any]:
    org_node = (data.get("organization") or {}).get("projectV2")
    user_node = (data.get("user") or {}).get("projectV2")
    node = org_node or user_node
    if not node:
        raise RuntimeError("project not found. check GH_PROJECT_OWNER / GH_PROJECT_NUMBER / token scope")
    return node


def _parse_project_item(
    node: dict[str, Any],
    *,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
    time_window_field_name: str,
) -> ProjectItem | None:
    if bool(node.get("isArchived")):
        return None

    content = node.get("content") or {}
    content_type = str(content.get("__typename") or "Unknown")

    title = str(content.get("title") or "").strip()
    if not title:
        title = "(untitled)"

    url = str(content.get("url") or "").strip()
    state = str(content.get("state") or "").strip()
    assignees_nodes = ((content.get("assignees") or {}).get("nodes") or []) if content else []
    assignees = ", ".join(str(n.get("login") or "").strip() for n in assignees_nodes if n.get("login"))

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
        elif kind == "ProjectV2ItemFieldTextValue":
            if field_name == status_field_name and not status:
                status = str(fv.get("text") or "").strip()
            elif field_name == track_field_name and not track:
                track = str(fv.get("text") or "").strip()
            elif field_name == slot_field_name and not slot:
                slot = str(fv.get("text") or "").strip()
            elif field_name == time_window_field_name and not time_window:
                time_window = str(fv.get("text") or "").strip()

    if not due_date:
        return None

    return ProjectItem(
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
    )


def fetch_project_items(
    *,
    token: str,
    owner: str,
    number: int,
    due_field_name: str,
    status_field_name: str,
    track_field_name: str,
    slot_field_name: str,
    time_window_field_name: str,
    sync_only_statuses: set[str],
) -> list[ProjectItem]:
    items: list[ProjectItem] = []
    cursor: str | None = None
    query = _graphql_query()
    managed_open_titles = _managed_open_titles_from_docs()
    enforce_managed_doc_filter = managed_open_titles is not None

    while True:
        data = _graphql_request(
            token,
            query,
            {
                "owner": owner,
                "number": number,
                "cursor": cursor,
            },
        )
        project = _project_node(data)
        batch = (project.get("items") or {}).get("nodes") or []
        for node in batch:
            parsed = _parse_project_item(
                node,
                due_field_name=due_field_name,
                status_field_name=status_field_name,
                track_field_name=track_field_name,
                slot_field_name=slot_field_name,
                time_window_field_name=time_window_field_name,
            )
            if not parsed:
                continue
            if (
                enforce_managed_doc_filter
                and _is_managed_project_title(parsed.title)
                and parsed.title not in managed_open_titles
            ):
                continue
            if not _status_allowed(parsed.status, sync_only_statuses):
                continue
            items.append(parsed)

        page_info = (project.get("items") or {}).get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return items


def _calendar_service(sa_json: str):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except Exception as exc:
        raise RuntimeError(
            "google calendar dependencies are missing. install google-auth and google-api-python-client"
        ) from exc

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=[CALENDAR_SCOPE])
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _event_body(
    item: ProjectItem,
    *,
    event_prefix: str,
    owner: str,
    project_number: int,
    event_timezone: str,
    use_slot_time: bool,
    slot_preopen_time: str,
    slot_intraday_time: str,
    slot_postclose_time: str,
    slot_duration_minutes: int,
    slot_reminder_minutes: int,
) -> dict[str, Any]:
    due = date.fromisoformat(item.due_date)
    is_trading_day, trading_day_reason = get_krx_trading_day_status(due)
    slot_key = _norm_key(item.slot)
    holiday_forced_intraday = bool(not is_trading_day and slot_key in {_norm_key("PREOPEN"), _norm_key("POSTCLOSE")})
    slot_to_time = {
        _norm_key("PREOPEN"): slot_preopen_time,
        _norm_key("INTRADAY"): slot_intraday_time,
        _norm_key("POSTCLOSE"): slot_postclose_time,
    }
    start_hhmm = slot_intraday_time if holiday_forced_intraday else slot_to_time.get(slot_key, "")
    end_hhmm = ""
    is_timed_event = bool(use_slot_time and start_hhmm)
    force_all_day = False

    mode, tw_start, tw_end = _parse_time_window(item.time_window)
    if mode == "timed" and not holiday_forced_intraday:
        start_hhmm = tw_start
        end_hhmm = tw_end
        is_timed_event = True
    elif mode in {"all_day", "unscheduled"}:
        force_all_day = True
        is_timed_event = False

    explicit_start_hhmm, explicit_end_hhmm = _extract_time_range_from_text(item.title)
    has_explicit_time = bool(explicit_start_hhmm)
    if has_explicit_time and not force_all_day and mode != "timed" and not holiday_forced_intraday:
        start_hhmm = explicit_start_hhmm
        end_hhmm = explicit_end_hhmm
        is_timed_event = True

    if holiday_forced_intraday and is_timed_event and not force_all_day:
        start_hhmm = slot_intraday_time
        end_hhmm = ""

    description_lines = [
        f"Project: {owner}#{project_number}",
        f"Type: {item.content_type}",
        f"TradingDay: {'true' if is_trading_day else 'false'} ({trading_day_reason})",
        f"Status: {item.status or '-'}",
        f"Slot: {item.slot or '-'}",
        f"TimeWindow: {item.time_window or '-'}",
        f"Track: {item.track or '-'}",
        f"State: {item.state or '-'}",
        f"Assignees: {item.assignees or '-'}",
        f"URL: {item.url or '-'}",
    ]
    body = {
        "summary": f"{event_prefix} {item.title}".strip(),
        "description": "\n".join(description_lines),
        "extendedProperties": {
            "private": {
                "gh_project_item_id": item.item_id,
                "gh_project_owner": owner,
                "gh_project_number": str(project_number),
            }
        },
    }
    if is_timed_event and not force_all_day:
        try:
            start_dt = datetime.fromisoformat(f"{due.isoformat()}T{start_hhmm}:00")
        except ValueError:
            start_dt = datetime.fromisoformat(f"{due.isoformat()}T09:00:00")
        if end_hhmm:
            try:
                end_dt = datetime.fromisoformat(f"{due.isoformat()}T{end_hhmm}:00")
            except ValueError:
                end_dt = start_dt + timedelta(minutes=max(5, slot_duration_minutes))
        else:
            end_dt = start_dt + timedelta(minutes=max(5, slot_duration_minutes))
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(minutes=max(5, slot_duration_minutes))
        body["start"] = {"dateTime": start_dt.isoformat(), "timeZone": event_timezone}
        body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": event_timezone}
        body["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": max(0, slot_reminder_minutes)}],
        }
    else:
        body["start"] = {"date": due.isoformat()}
        body["end"] = {"date": (due + timedelta(days=1)).isoformat()}
    return body


def upsert_events(
    *,
    service,
    calendar_id: str,
    items: list[ProjectItem],
    event_prefix: str,
    owner: str,
    project_number: int,
    event_timezone: str,
    use_slot_time: bool,
    slot_preopen_time: str,
    slot_intraday_time: str,
    slot_postclose_time: str,
    slot_duration_minutes: int,
    slot_reminder_minutes: int,
    dry_run: bool,
) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    for item in items:
        body = _event_body(
            item,
            event_prefix=event_prefix,
            owner=owner,
            project_number=project_number,
            event_timezone=event_timezone,
            use_slot_time=use_slot_time,
            slot_preopen_time=slot_preopen_time,
            slot_intraday_time=slot_intraday_time,
            slot_postclose_time=slot_postclose_time,
            slot_duration_minutes=slot_duration_minutes,
            slot_reminder_minutes=slot_reminder_minutes,
        )
        if dry_run:
            skipped += 1
            continue

        found = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=[f"gh_project_item_id={item.item_id}"],
                singleEvents=True,
                maxResults=1,
            )
            .execute()
        )
        existing = (found.get("items") or [])
        if existing:
            event_id = existing[0]["id"]
            service.events().update(calendarId=calendar_id, eventId=event_id, body=body).execute()
            updated += 1
        else:
            service.events().insert(calendarId=calendar_id, body=body).execute()
            created += 1

    return {
        "created": created,
        "updated": updated,
        "dry_run_skipped": skipped,
    }


def prune_stale_events(
    *,
    service,
    calendar_id: str,
    owner: str,
    project_number: int,
    live_item_ids: set[str],
    dry_run: bool,
) -> dict[str, int]:
    page_token = None
    deleted = 0
    dry_run_deleted = 0
    owner_prop = f"gh_project_owner={owner}"
    number_prop = f"gh_project_number={project_number}"

    while True:
        resp = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=[owner_prop, number_prop],
                singleEvents=True,
                maxResults=250,
                pageToken=page_token,
            )
            .execute()
        )
        for event in resp.get("items", []):
            private = ((event.get("extendedProperties") or {}).get("private") or {})
            item_id = str(private.get("gh_project_item_id") or "").strip()
            event_id = str(event.get("id") or "").strip()
            if not event_id or not item_id or item_id in live_item_ids:
                continue
            if dry_run:
                dry_run_deleted += 1
                continue
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            deleted += 1

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return {
        "deleted": deleted,
        "dry_run_deleted": dry_run_deleted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync GitHub Project to Google Calendar.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to Google Calendar.")
    args = parser.parse_args()

    gh_token = _env("GH_PROJECT_TOKEN", os.getenv("GITHUB_TOKEN"))
    owner = _env("GH_PROJECT_OWNER")
    project_number = int(_env("GH_PROJECT_NUMBER"))
    due_field_name = _env("GH_PROJECT_DUE_FIELD_NAME", "Due")
    status_field_name = _env("GH_PROJECT_STATUS_FIELD_NAME", "Status")
    track_field_name = _env("GH_PROJECT_TRACK_FIELD_NAME", "Track")
    slot_field_name = _env("GH_PROJECT_SLOT_FIELD_NAME", "Slot")
    time_window_field_name = _env("GH_PROJECT_TIME_WINDOW_FIELD_NAME", "TimeWindow")
    event_prefix = _env("GCAL_EVENT_PREFIX", "[KORStockScan]")
    event_timezone = _env("GCAL_EVENT_TIMEZONE", "Asia/Seoul")
    use_slot_time = _env_bool("GCAL_USE_SLOT_TIME", True)
    slot_preopen_time = _env("GCAL_SLOT_PREOPEN_TIME", "08:20")
    slot_intraday_time = _env("GCAL_SLOT_INTRADAY_TIME", "10:00")
    slot_postclose_time = _env("GCAL_SLOT_POSTCLOSE_TIME", "15:40")
    slot_duration_minutes = _env_int("GCAL_SLOT_DURATION_MINUTES", 30)
    slot_reminder_minutes = _env_int("GCAL_SLOT_REMINDER_MINUTES", 0)
    calendar_id = _env("GOOGLE_CALENDAR_ID")
    service_account_json = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    dry_run = args.dry_run or _env_bool("SYNC_DRY_RUN", False)

    only_status_raw = str(os.getenv("GH_SYNC_ONLY_STATUSES", "") or "").strip()
    if not only_status_raw:
        only_status_raw = "Todo,In Progress"
    sync_only_statuses = {x.strip() for x in only_status_raw.split(",") if x.strip()}

    items = fetch_project_items(
        token=gh_token,
        owner=owner,
        number=project_number,
        due_field_name=due_field_name,
        status_field_name=status_field_name,
        track_field_name=track_field_name,
        slot_field_name=slot_field_name,
        time_window_field_name=time_window_field_name,
        sync_only_statuses=sync_only_statuses,
    )

    service = _calendar_service(service_account_json)
    counts = upsert_events(
        service=service,
        calendar_id=calendar_id,
        items=items,
        event_prefix=event_prefix,
        owner=owner,
        project_number=project_number,
        event_timezone=event_timezone,
        use_slot_time=use_slot_time,
        slot_preopen_time=slot_preopen_time,
        slot_intraday_time=slot_intraday_time,
        slot_postclose_time=slot_postclose_time,
        slot_duration_minutes=slot_duration_minutes,
        slot_reminder_minutes=slot_reminder_minutes,
        dry_run=dry_run,
    )
    prune_counts = prune_stale_events(
        service=service,
        calendar_id=calendar_id,
        owner=owner,
        project_number=project_number,
        live_item_ids={item.item_id for item in items},
        dry_run=dry_run,
    )

    summary = {
        "project_owner": owner,
        "project_number": project_number,
        "items_with_due_date": len(items),
        "status_filter_applied": sorted(sync_only_statuses),
        "dry_run": dry_run,
        **counts,
        **prune_counts,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[PROJECT_CAL_SYNC_ERROR] {exc}", file=sys.stderr)
        raise
