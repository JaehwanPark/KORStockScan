from io import BytesIO

from src.engine.sync_github_project_calendar import (
    _codex_daily_workorder_slot,
    _graphql_request,
    _event_body,
    _parse_project_item,
    _status_allowed,
    fetch_project_items,
    ProjectItem,
    prune_stale_events,
)


def _sample_node():
    return {
        "id": "PVTI_xxx",
        "isArchived": False,
        "content": {
            "__typename": "Issue",
            "title": "Implement remote fetch hardening",
            "url": "https://github.com/org/repo/issues/123",
            "state": "OPEN",
            "assignees": {"nodes": [{"login": "alice"}, {"login": "bob"}]},
        },
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldDateValue",
                    "date": "2026-04-13",
                    "field": {"name": "Due"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "In Progress",
                    "field": {"name": "Status"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "Scalping Logic",
                    "field": {"name": "Track"},
                },
            ]
        },
    }


def test_parse_project_item_returns_item_when_due_exists():
    parsed = _parse_project_item(
        _sample_node(),
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
    )
    assert parsed is not None
    assert parsed.item_id == "PVTI_xxx"
    assert parsed.title == "Implement remote fetch hardening"
    assert parsed.due_date == "2026-04-13"
    assert parsed.status == "In Progress"
    assert parsed.track == "Scalping Logic"
    assert parsed.slot == ""
    assert parsed.time_window == ""
    assert parsed.assignees == "alice, bob"


def test_parse_project_item_returns_none_when_due_missing():
    node = _sample_node()
    node["fieldValues"]["nodes"] = [fv for fv in node["fieldValues"]["nodes"] if fv.get("__typename") != "ProjectV2ItemFieldDateValue"]
    parsed = _parse_project_item(
        node,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
    )
    assert parsed is None


def test_parse_project_item_reads_slot_single_select():
    node = _sample_node()
    node["fieldValues"]["nodes"].append(
        {
            "__typename": "ProjectV2ItemFieldSingleSelectValue",
            "name": "POSTCLOSE",
            "field": {"name": "Slot"},
        }
    )
    parsed = _parse_project_item(
        node,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
    )
    assert parsed is not None
    assert parsed.slot == "POSTCLOSE"


def test_parse_project_item_reads_status_from_text_fallback():
    node = _sample_node()
    node["fieldValues"]["nodes"] = [
        fv for fv in node["fieldValues"]["nodes"] if fv.get("field", {}).get("name") != "Status"
    ]
    node["fieldValues"]["nodes"].append(
        {
            "__typename": "ProjectV2ItemFieldTextValue",
            "text": "In Progress",
            "field": {"name": "Status"},
        }
    )
    parsed = _parse_project_item(
        node,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
    )
    assert parsed is not None
    assert parsed.status == "In Progress"


def test_status_allowed_requires_explicit_match_when_filter_present():
    assert _status_allowed("Todo", {"Todo", "In Progress"}) is True
    assert _status_allowed("in progress", {"Todo", "In Progress"}) is True
    assert _status_allowed("Done", {"Todo", "In Progress"}) is False
    assert _status_allowed("", {"Todo", "In Progress"}) is False
    assert _status_allowed("", set()) is True


def test_fetch_project_items_excludes_blank_status_when_filter_present(monkeypatch):
    data = {
        "organization": {
            "projectV2": {
                "items": {
                    "nodes": [
                        {
                            **_sample_node(),
                            "id": "PVTI_blank",
                            "fieldValues": {
                                "nodes": [
                                    fv
                                    for fv in _sample_node()["fieldValues"]["nodes"]
                                    if fv.get("field", {}).get("name") != "Status"
                                ]
                            },
                        },
                        _sample_node(),
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
        "user": {"projectV2": None},
    }

    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar._graphql_request",
        lambda token, query, variables: data,
    )

    items = fetch_project_items(
        token="token",
        owner="JaehwanPark",
        number=1,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
        sync_only_statuses={"Todo", "In Progress"},
    )

    assert [item.item_id for item in items] == ["PVTI_xxx"]


def test_fetch_project_items_excludes_managed_title_missing_from_docs(monkeypatch):
    managed_node = _sample_node()
    managed_node["content"]["title"] = "[Checklist0414] closed in docs"

    data = {
        "organization": {
            "projectV2": {
                "items": {
                    "nodes": [
                        managed_node,
                        {
                            **_sample_node(),
                            "id": "PVTI_keep",
                            "content": {
                                **_sample_node()["content"],
                                "title": "[Checklist0414] still open in docs",
                            },
                        },
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
        "user": {"projectV2": None},
    }

    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar._graphql_request",
        lambda token, query, variables: data,
    )
    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar.collect_backlog_tasks",
        lambda: [
            type(
                "Task",
                (),
                {
                    "title": "still open in docs",
                    "source": "docs/x.md",
                    "section": "s",
                    "track": "Checklist0414",
                    "due_date": "2026-04-14",
                },
            )()
        ],
    )

    items = fetch_project_items(
        token="token",
        owner="JaehwanPark",
        number=1,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
        sync_only_statuses={"Todo", "In Progress"},
    )

    assert [item.title for item in items] == ["[Checklist0414] still open in docs"]


def test_fetch_project_items_excludes_all_managed_titles_when_docs_open_set_empty(monkeypatch):
    managed_node = _sample_node()
    managed_node["content"]["title"] = "[Checklist0414] closed in docs"

    unmanaged_node = {
        **_sample_node(),
        "id": "PVTI_unmanaged",
        "content": {
            **_sample_node()["content"],
            "title": "Unmanaged live task",
        },
    }

    data = {
        "organization": {
            "projectV2": {
                "items": {
                    "nodes": [managed_node, unmanaged_node],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
        "user": {"projectV2": None},
    }

    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar._graphql_request",
        lambda token, query, variables: data,
    )
    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar.collect_backlog_tasks",
        lambda: [],
    )

    items = fetch_project_items(
        token="token",
        owner="JaehwanPark",
        number=1,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
        sync_only_statuses={"Todo", "In Progress"},
    )

    assert [item.title for item in items] == ["Unmanaged live task"]


def test_fetch_project_items_keeps_managed_titles_when_docs_parse_fails(monkeypatch):
    managed_node = _sample_node()
    managed_node["content"]["title"] = "[Checklist0414] fallback keep on parse failure"

    data = {
        "organization": {
            "projectV2": {
                "items": {
                    "nodes": [managed_node],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
        "user": {"projectV2": None},
    }

    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar._graphql_request",
        lambda token, query, variables: data,
    )
    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar.collect_backlog_tasks",
        lambda: (_ for _ in ()).throw(RuntimeError("parse failed")),
    )

    items = fetch_project_items(
        token="token",
        owner="JaehwanPark",
        number=1,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
        sync_only_statuses={"Todo", "In Progress"},
    )

    assert [item.title for item in items] == ["[Checklist0414] fallback keep on parse failure"]


def test_calendar_graphql_request_retries_transient_graphql_internal_error(monkeypatch):
    calls = {"count": 0}

    class _FakeResponse:
        def __init__(self, payload: bytes):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return BytesIO(self._payload).read()

    def _fake_urlopen(req, timeout=30):
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(
                b'{"errors":[{"message":"Something went wrong while executing your query on 2026-04-24T02:40:09Z. Please include `ABC` when reporting this issue."}]}'
            )
        return _FakeResponse(b'{"data":{"organization":{"projectV2":null},"user":{"projectV2":null}}}')

    monkeypatch.setattr("src.engine.sync_github_project_calendar.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("src.engine.sync_github_project_calendar.time.sleep", lambda _: None)

    data = _graphql_request("token", "query Test { viewer { login } }", {})
    assert data == {"organization": {"projectV2": None}, "user": {"projectV2": None}}
    assert calls["count"] == 2


def test_fetch_project_items_keeps_checklist_title_when_only_mmdd_differs(monkeypatch):
    managed_node = _sample_node()
    managed_node["content"]["title"] = "[Checklist0413] mmdd migration safe"

    data = {
        "organization": {
            "projectV2": {
                "items": {
                    "nodes": [managed_node],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
        "user": {"projectV2": None},
    }

    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar._graphql_request",
        lambda token, query, variables: data,
    )
    monkeypatch.setattr(
        "src.engine.sync_github_project_calendar.collect_backlog_tasks",
        lambda: [
            type(
                "Task",
                (),
                {
                    "title": "mmdd migration safe",
                    "source": "docs/x.md",
                    "section": "s",
                    "track": "Checklist0414",
                    "due_date": "2026-04-14",
                },
            )()
        ],
    )

    items = fetch_project_items(
        token="token",
        owner="JaehwanPark",
        number=1,
        due_field_name="Due",
        status_field_name="Status",
        track_field_name="Track",
        slot_field_name="Slot",
        time_window_field_name="TimeWindow",
        sync_only_statuses={"Todo", "In Progress"},
    )

    assert [item.title for item in items] == ["[Checklist0413] mmdd migration safe"]


def test_event_body_contains_private_extended_properties():
    item = ProjectItem(
        item_id="PVTI_1",
        content_type="Issue",
        title="Task A",
        url="https://github.com/org/repo/issues/1",
        due_date="2026-04-14",
        status="Todo",
        track="Prompt",
        slot="",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["summary"] == "Task A"
    assert body["start"]["date"] == "2026-04-14"
    assert body["end"]["date"] == "2026-04-15"
    assert body["extendedProperties"]["private"]["gh_project_item_id"] == "PVTI_1"


def test_event_body_timed_when_slot_exists():
    item = ProjectItem(
        item_id="PVTI_2",
        content_type="Issue",
        title="Task B",
        url="https://github.com/org/repo/issues/2",
        due_date="2026-04-14",
        status="Todo",
        track="Prompt",
        slot="PREOPEN",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-14T08:20:00"
    assert body["end"]["dateTime"] == "2026-04-14T08:50:00"
    assert body["start"]["timeZone"] == "Asia/Seoul"
    assert body["reminders"]["overrides"][0]["minutes"] == 0


def test_event_body_holiday_reclassifies_slot_time_to_intraday():
    item = ProjectItem(
        item_id="PVTI_2b",
        content_type="Issue",
        title="Task Holiday",
        url="https://github.com/org/repo/issues/22",
        due_date="2026-04-12",
        status="Todo",
        track="Prompt",
        slot="PREOPEN",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-12T10:00:00"
    assert body["end"]["dateTime"] == "2026-04-12T10:30:00"


def test_event_body_uses_explicit_time_range_from_title_over_slot_default():
    item = ProjectItem(
        item_id="PVTI_3",
        content_type="Issue",
        title="원격 경량 프로파일링 장중 2차 수집 (13:20~13:35)",
        url="https://github.com/org/repo/issues/3",
        due_date="2026-04-14",
        status="Todo",
        track="ScalpingLogic",
        slot="INTRADAY",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-14T13:20:00"
    assert body["end"]["dateTime"] == "2026-04-14T13:35:00"


def test_event_body_holiday_forces_intraday_over_explicit_time_range():
    item = ProjectItem(
        item_id="PVTI_3b",
        content_type="Issue",
        title="휴장일 수동점검 (13:20~13:35)",
        url="https://github.com/org/repo/issues/33",
        due_date="2026-04-12",
        status="Todo",
        track="ScalpingLogic",
        slot="PREOPEN",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-12T10:00:00"
    assert body["end"]["dateTime"] == "2026-04-12T10:30:00"


def test_event_body_prefers_time_window_field_over_title_and_slot():
    item = ProjectItem(
        item_id="PVTI_4",
        content_type="Issue",
        title="Task C (10:00~10:15)",
        url="https://github.com/org/repo/issues/4",
        due_date="2026-04-14",
        status="Todo",
        track="ScalpingLogic",
        slot="INTRADAY",
        time_window="13:20~13:35",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-14T13:20:00"
    assert body["end"]["dateTime"] == "2026-04-14T13:35:00"


def test_event_body_holiday_forces_intraday_over_time_window():
    item = ProjectItem(
        item_id="PVTI_4b",
        content_type="Issue",
        title="Task Holiday",
        url="https://github.com/org/repo/issues/44",
        due_date="2026-04-12",
        status="Todo",
        track="AIPrompt",
        slot="POSTCLOSE",
        time_window="15:40~16:10",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["dateTime"] == "2026-04-12T10:00:00"
    assert body["end"]["dateTime"] == "2026-04-12T10:30:00"


def test_event_body_all_day_when_unscheduled_time_window():
    item = ProjectItem(
        item_id="PVTI_5",
        content_type="Issue",
        title="Task D",
        url="https://github.com/org/repo/issues/5",
        due_date="2026-04-14",
        status="Todo",
        track="Plan",
        slot="PREOPEN",
        time_window="UNSCHEDULED",
        assignees="alice",
        state="OPEN",
    )
    body = _event_body(
        item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    assert body["start"]["date"] == "2026-04-14"
    assert "dateTime" not in body["start"]


def test_event_body_compacts_managed_track_prefixes():
    checklist_item = ProjectItem(
        item_id="PVTI_6",
        content_type="Issue",
        title="[Checklist0414] 장전 점검",
        url="https://github.com/org/repo/issues/6",
        due_date="2026-04-14",
        status="Todo",
        track="Checklist0414",
        slot="PREOPEN",
        time_window="",
        assignees="alice",
        state="OPEN",
    )
    aip_item = ProjectItem(
        item_id="PVTI_7",
        content_type="Issue",
        title="[AIPrompt] 작업 8 감사용 핵심값 3종 투입",
        url="https://github.com/org/repo/issues/7",
        due_date="2026-04-14",
        status="Todo",
        track="AIPrompt",
        slot="POSTCLOSE",
        time_window="",
        assignees="alice",
        state="OPEN",
    )

    checklist_body = _event_body(
        checklist_item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )
    aip_body = _event_body(
        aip_item,
        event_prefix="",
        owner="org",
        project_number=3,
        event_timezone="Asia/Seoul",
        use_slot_time=True,
        slot_preopen_time="08:20",
        slot_intraday_time="10:00",
        slot_postclose_time="15:40",
        slot_duration_minutes=30,
        slot_reminder_minutes=0,
    )

    assert checklist_body["summary"] == "[CL] 장전 점검"
    assert aip_body["summary"] == "[AIP] 작업 8 감사용 핵심값 3종 투입"


class _FakeEventsApi:
    def __init__(self, list_payloads):
        self._list_payloads = list(list_payloads)
        self.deleted = []
        self._current_op = None

    def list(self, **kwargs):
        self._current_op = ("list", kwargs)
        return self

    def delete(self, **kwargs):
        self._current_op = ("delete", kwargs)
        return self

    def execute(self):
        op, kwargs = self._current_op
        if op == "list":
            return self._list_payloads.pop(0)
        if op == "delete":
            self.deleted.append(kwargs["eventId"])
            return {}
        raise AssertionError(f"unexpected op: {op}")


class _FakeCalendarService:
    def __init__(self, list_payloads):
        self._events = _FakeEventsApi(list_payloads)

    def events(self):
        return self._events


def test_prune_stale_events_dry_run_counts_candidates():
    service = _FakeCalendarService(
        [
            {
                "items": [
                    {
                        "id": "evt_keep",
                        "extendedProperties": {"private": {"gh_project_item_id": "PVTI_keep"}},
                    },
                    {
                        "id": "evt_drop",
                        "extendedProperties": {"private": {"gh_project_item_id": "PVTI_drop"}},
                    },
                ]
            }
        ]
    )
    summary = prune_stale_events(
        service=service,
        calendar_id="primary",
        owner="JaehwanPark",
        project_number=1,
        live_item_ids={"PVTI_keep"},
        dry_run=True,
    )
    assert summary == {
        "deleted": 0,
        "dry_run_deleted": 1,
        "legacy_deleted": 0,
        "legacy_dry_run_deleted": 0,
        "codex_workorder_deleted": 0,
        "codex_workorder_dry_run_deleted": 0,
    }
    assert service._events.deleted == []


def test_prune_stale_events_deletes_removed_items():
    service = _FakeCalendarService(
        [
            {
                "items": [
                    {
                        "id": "evt_drop",
                        "extendedProperties": {"private": {"gh_project_item_id": "PVTI_drop"}},
                    }
                ]
            }
        ]
    )
    summary = prune_stale_events(
        service=service,
        calendar_id="primary",
        owner="JaehwanPark",
        project_number=1,
        live_item_ids={"PVTI_keep"},
        dry_run=False,
    )
    assert summary == {
        "deleted": 1,
        "dry_run_deleted": 0,
        "legacy_deleted": 0,
        "legacy_dry_run_deleted": 0,
        "codex_workorder_deleted": 0,
        "codex_workorder_dry_run_deleted": 0,
    }
    assert service._events.deleted == ["evt_drop"]


def test_prune_stale_events_deletes_legacy_managed_event_without_private_properties():
    service = _FakeCalendarService(
        [
            {"items": []},
            {
                "items": [
                    {
                        "id": "evt_legacy_drop",
                        "summary": "[KORStockScan] [CL] closed task (Due: 2026-04-21, Slot: POSTCLOSE, TimeWindow: 15:40~16:10, Track: Plan)",
                        "description": "Project: JaehwanPark#1 Type: DraftIssue",
                    },
                    {
                        "id": "evt_legacy_keep",
                        "summary": "[KORStockScan] [CL] open task (Due: 2026-04-21, Slot: POSTCLOSE, TimeWindow: 15:40~16:10, Track: Plan)",
                        "description": "Project: JaehwanPark#1 Type: DraftIssue",
                    },
                ]
            },
        ]
    )

    summary = prune_stale_events(
        service=service,
        calendar_id="primary",
        owner="JaehwanPark",
        project_number=1,
        live_item_ids=set(),
        live_managed_title_keys={"[Checklist] open task"},
        event_prefix="[KORStockScan]",
        legacy_time_min="2026-04-21T00:00:00+09:00",
        legacy_time_max="2026-04-22T00:00:00+09:00",
        dry_run=False,
    )

    assert summary == {
        "deleted": 0,
        "dry_run_deleted": 0,
        "legacy_deleted": 1,
        "legacy_dry_run_deleted": 0,
        "codex_workorder_deleted": 0,
        "codex_workorder_dry_run_deleted": 0,
    }
    assert service._events.deleted == ["evt_legacy_drop"]


def test_prune_stale_events_ignores_legacy_event_without_project_marker():
    service = _FakeCalendarService(
        [
            {"items": []},
            {
                "items": [
                    {
                        "id": "evt_other",
                        "summary": "[KORStockScan] [CL] closed task (Due: 2026-04-21, Slot: POSTCLOSE, TimeWindow: 15:40~16:10, Track: Plan)",
                        "description": "Project: Other#1 Type: DraftIssue",
                    }
                ]
            },
        ]
    )

    summary = prune_stale_events(
        service=service,
        calendar_id="primary",
        owner="JaehwanPark",
        project_number=1,
        live_item_ids=set(),
        live_managed_title_keys=set(),
        event_prefix="[KORStockScan]",
        legacy_time_min="2026-04-21T00:00:00+09:00",
        legacy_time_max="2026-04-22T00:00:00+09:00",
        dry_run=False,
    )

    assert summary == {
        "deleted": 0,
        "dry_run_deleted": 0,
        "legacy_deleted": 0,
        "legacy_dry_run_deleted": 0,
        "codex_workorder_deleted": 0,
        "codex_workorder_dry_run_deleted": 0,
    }
    assert service._events.deleted == []


def test_codex_daily_workorder_slot_parser():
    assert _codex_daily_workorder_slot("Codex Daily Workorder (PREOPEN)") == "PREOPEN"
    assert _codex_daily_workorder_slot("[KORStockScan] Codex Daily Workorder (POSTCLOSE)") == "POSTCLOSE"
    assert _codex_daily_workorder_slot("regular task") == ""


def test_prune_stale_events_deletes_stale_codex_daily_workorder_without_project_marker():
    service = _FakeCalendarService(
        [
            {"items": []},
            {"items": []},
            {
                "items": [
                    {
                        "id": "evt_preopen_drop",
                        "summary": "Codex Daily Workorder (PREOPEN)",
                        "description": "",
                    },
                    {
                        "id": "evt_intraday_keep",
                        "summary": "Codex Daily Workorder (INTRADAY)",
                        "description": "",
                    },
                ]
            },
        ]
    )

    summary = prune_stale_events(
        service=service,
        calendar_id="primary",
        owner="JaehwanPark",
        project_number=1,
        live_item_ids=set(),
        live_managed_title_keys=set(),
        live_codex_workorder_slots={"INTRADAY", "POSTCLOSE"},
        event_prefix="[KORStockScan]",
        legacy_time_min="2026-05-22T00:00:00+09:00",
        legacy_time_max="2026-05-23T00:00:00+09:00",
        dry_run=False,
    )

    assert summary == {
        "deleted": 0,
        "dry_run_deleted": 0,
        "legacy_deleted": 0,
        "legacy_dry_run_deleted": 0,
        "codex_workorder_deleted": 1,
        "codex_workorder_dry_run_deleted": 0,
    }
    assert service._events.deleted == ["evt_preopen_drop"]
