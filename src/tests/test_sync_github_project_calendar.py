from src.engine.sync_github_project_calendar import _event_body, _parse_project_item, ProjectItem


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
    )
    assert parsed is not None
    assert parsed.item_id == "PVTI_xxx"
    assert parsed.title == "Implement remote fetch hardening"
    assert parsed.due_date == "2026-04-13"
    assert parsed.status == "In Progress"
    assert parsed.track == "Scalping Logic"
    assert parsed.slot == ""
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
