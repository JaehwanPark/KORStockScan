from src.engine.sync_github_project_calendar import (
    _event_body,
    _parse_project_item,
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
        event_prefix="[KORStockScan]",
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
    assert body["summary"] == "[KORStockScan] Task A"
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
        event_prefix="[KORStockScan]",
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
    assert summary == {"deleted": 0, "dry_run_deleted": 1}
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
    assert summary == {"deleted": 1, "dry_run_deleted": 0}
    assert service._events.deleted == ["evt_drop"]
