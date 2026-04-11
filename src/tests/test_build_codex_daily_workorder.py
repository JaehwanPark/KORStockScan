from src.engine.build_codex_daily_workorder import ProjectTask, _matches_slot, _split_csv, render_markdown, sort_tasks


def test_split_csv_trims_and_drops_empty():
    assert _split_csv("Todo, In Progress, ,Done") == ["Todo", "In Progress", "Done"]


def test_sort_tasks_by_status_due_track_title():
    tasks = [
        ProjectTask(
            item_id="3",
            content_type="DraftIssue",
            title="B task",
            url="",
            due_date="2026-04-15",
            status="Todo",
            track="Plan",
            slot="PREOPEN",
            assignees="",
            state="",
        ),
        ProjectTask(
            item_id="2",
            content_type="DraftIssue",
            title="A task",
            url="",
            due_date="2026-04-14",
            status="In Progress",
            track="AIPrompt",
            slot="INTRADAY",
            assignees="",
            state="",
        ),
        ProjectTask(
            item_id="1",
            content_type="DraftIssue",
            title="C task",
            url="",
            due_date="2026-04-14",
            status="Todo",
            track="Checklist0413",
            slot="POSTCLOSE",
            assignees="",
            state="",
        ),
    ]
    sorted_tasks = sort_tasks(tasks, ["In Progress", "Todo"])
    assert [t.item_id for t in sorted_tasks] == ["2", "1", "3"]


def test_render_markdown_includes_template_and_ids():
    tasks = [
        ProjectTask(
            item_id="ITEM_123",
            content_type="Issue",
            title="테스트 작업",
            url="https://example.com/issue/1",
            due_date="2026-04-13",
            status="Todo",
            track="Plan",
            slot="PREOPEN",
            assignees="jaehwan",
            state="OPEN",
        )
    ]
    md = render_markdown(
        owner="JaehwanPark",
        project_number=1,
        project_title="KORStockScan Ops",
        generated_at="2026-04-11T23:00:00+09:00",
        statuses=["Todo", "In Progress"],
        slots=["PREOPEN"],
        tasks=tasks,
        max_items=20,
    )
    assert "Codex 일일 작업지시서" in md
    assert "ITEM_123" in md
    assert "Codex 전달 템플릿" in md
    assert "슬롯필터" in md


def test_matches_slot_case_insensitive():
    assert _matches_slot("PREOPEN", {"preopen"})
    assert not _matches_slot("INTRADAY", {"preopen"})
    assert _matches_slot("", set())
