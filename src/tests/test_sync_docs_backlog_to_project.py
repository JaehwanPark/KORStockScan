from src.engine.sync_docs_backlog_to_project import (
    BacklogTask,
    DOC_PROMPT,
    DOC_SCALPING,
    DOC_PLAN,
    DOC_CHECKLIST,
    ProjectItem,
    _due_date_from_checklist_path,
    _desired_status_option_id,
    _env,
    _env_bool,
    _find_option_id_by_name,
    _checklist_track_from_source,
    _ensure_apply_target,
    _infer_apply_target_text,
    _infer_slot_label,
    _infer_time_window,
    _is_managed_project_title,
    _slot_equals,
    _slot_key,
    collect_backlog_tasks,
    parse_checklist_tasks,
    parse_plan_tasks,
    parse_prompt_tasks,
    parse_scalping_logic_tasks,
    sync_backlog_to_project,
)


def test_parse_plan_tasks_has_remaining_items():
    tasks = parse_plan_tasks()
    titles = [t.title for t in tasks]
    assert any("0-1b 원격 경량 프로파일링" in title for title in titles)
    assert all("SCALP_PRESET_TP SELL 의도 확인" not in title for title in titles)


def test_parse_checklist_excludes_done_checkboxes():
    tasks = parse_checklist_tasks()
    titles = [t.title for t in tasks]
    assert any("SCALPING 모델 shadow 비교안 WATCHING shared prompt 구현 착수" in title for title in titles)
    assert all("RELAX-LATENCY 운영서버 승격 가능/불가 최종 결론" not in title for title in titles)


def test_parse_checklist_uses_env_override(monkeypatch):
    monkeypatch.setenv(
        "DOC_CHECKLIST_PATH",
        str(DOC_CHECKLIST.parent / "2026-04-14-stage2-todo-checklist.md"),
    )
    tasks = parse_checklist_tasks()
    assert len(tasks) > 0
    assert all("2026-04-14-stage2-todo-checklist.md" not in t.source for t in tasks)


def test_parse_checklist_fallback_when_primary_missing(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sync_docs_backlog_to_project.DOC_CHECKLIST",
        DOC_CHECKLIST.parent / "__missing-checklist__.md",
    )
    tasks = parse_checklist_tasks()
    assert len(tasks) > 0
    assert any("-stage2-todo-checklist.md" in t.source for t in tasks)


def test_parse_checklist_collects_multiple_stage2_files():
    tasks = parse_checklist_tasks()
    due_dates = {t.due_date for t in tasks}
    assert "2026-04-15" in due_dates
    assert "2026-04-16" in due_dates


def test_checklist_track_from_source_uses_mmdd_suffix():
    assert _checklist_track_from_source(DOC_CHECKLIST.parent / "2026-04-14-stage2-todo-checklist.md") == "Checklist0414"


def test_parse_checklist_skips_past_due_stage2_files_by_default(monkeypatch):
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-04-13")
    tasks = parse_checklist_tasks()
    assert all((not t.due_date) or t.due_date >= "2026-04-13" for t in tasks)


def test_due_date_from_checklist_path():
    assert _due_date_from_checklist_path(DOC_CHECKLIST) == "2026-04-13"
    assert _due_date_from_checklist_path(DOC_CHECKLIST.parent / "misc.md") == ""


def test_parse_scalping_logic_has_phase2_and_phase3():
    tasks = parse_scalping_logic_tasks()
    titles = [t.title for t in tasks]
    assert any(title.startswith("2-1 ") for title in titles)
    assert any(title.startswith("3-1 ") for title in titles)
    assert all(title != "0-1b 원격 경량 프로파일링" or titles.count(title) == 1 for title in titles)


def test_parse_prompt_has_detail_tasks_with_due_for_p0(monkeypatch):
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-04-12")
    tasks = parse_prompt_tasks()
    titles = [t.title for t in tasks]
    task_map = {t.title: t for t in tasks}
    assert any(title.startswith("작업 10 ") for title in titles)
    assert "작업 1 SCALP_PRESET_TP SELL 의도 확인" not in task_map
    assert "작업 2 AI 운영계측 추가" not in task_map
    assert "작업 3 HOLDING hybrid override 조건 명세" not in task_map
    assert task_map["작업 10 HOLDING hybrid 적용"].due_date == ""


def test_parse_prompt_excludes_done_marker_and_keeps_open_tasks():
    tasks = parse_prompt_tasks()
    titles = [t.title for t in tasks]
    assert "작업 1 SCALP_PRESET_TP SELL 의도 확인" not in titles
    assert "작업 3 HOLDING hybrid override 조건 명세" not in titles
    assert not any(title.startswith("작업 4 ") for title in titles)
    assert any(title.startswith("작업 5 ") for title in titles)


def test_parse_prompt_excludes_deferred_marker():
    tasks = parse_prompt_tasks()
    titles = [t.title for t in tasks]
    assert "작업 4 WATCHING 75 정합화 원격 canary" not in titles


def test_parse_prompt_fallback_when_primary_missing(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sync_docs_backlog_to_project.DOC_PROMPT",
        DOC_PROMPT.parent / "__missing-prompt__.md",
    )
    monkeypatch.setenv("DOC_PROMPT_PATH", str(DOC_PROMPT))
    tasks = parse_prompt_tasks()
    assert len(tasks) > 0
    assert all(str(DOC_PROMPT) in t.source for t in tasks)


def test_collect_backlog_tasks_deduped():
    tasks = collect_backlog_tasks()
    normalized = [" ".join(t.title.split()).lower() for t in tasks]
    assert len(normalized) == len(set(normalized))
    assert all(t.title != "SCALP_PRESET_TP SELL 의도 확인" for t in tasks)


def test_parse_scalping_logic_fallback_when_primary_missing(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sync_docs_backlog_to_project.DOC_SCALPING",
        DOC_SCALPING.parent / "__missing-primary__.md",
    )
    monkeypatch.setenv("DOC_SCALPING_PATH", str(DOC_SCALPING))
    tasks = parse_scalping_logic_tasks()
    assert len(tasks) > 0
    assert all(str(DOC_SCALPING) in t.source for t in tasks)


def test_parse_plan_tasks_empty_when_source_missing(monkeypatch):
    missing = DOC_PLAN.parent / "__missing-plan__.md"
    monkeypatch.setattr("src.engine.sync_docs_backlog_to_project.DOC_PLAN", missing)
    tasks = parse_plan_tasks()
    assert tasks == []


def test_managed_title_detection():
    assert _is_managed_project_title("[Plan] something")
    assert _is_managed_project_title("[AIPrompt] something")
    assert _is_managed_project_title("[Checklist0414] something")
    assert not _is_managed_project_title("[Other] something")
    assert not _is_managed_project_title("plain title")


def test_desired_status_option_id():
    open_title_keys = {"[Plan] alive task", "[Checklist] alive task"}
    assert (
        _desired_status_option_id(
            title="[Plan] alive task",
            desired_open_title_keys=open_title_keys,
            todo_option_id="todo-id",
            done_option_id="done-id",
        )
        == "todo-id"
    )
    assert (
        _desired_status_option_id(
            title="[Plan] closed task",
            desired_open_title_keys=open_title_keys,
            todo_option_id="todo-id",
            done_option_id="done-id",
        )
        == "done-id"
    )
    assert (
        _desired_status_option_id(
            title="[Checklist0413] alive task",
            desired_open_title_keys=open_title_keys,
            todo_option_id="todo-id",
            done_option_id="done-id",
        )
        == "todo-id"
    )
    assert (
        _desired_status_option_id(
            title="manual task",
            desired_open_title_keys=open_title_keys,
            todo_option_id="todo-id",
            done_option_id="done-id",
        )
        == ""
    )


def test_slot_key_normalizes():
    assert _slot_key("In Progress") == "inprogress"
    assert _slot_key("POST_CLOSE") == "postclose"


def test_find_option_id_by_name_normalized():
    options = [
        {"id": "1", "name": "PRE OPEN"},
        {"id": "2", "name": "INTRADAY"},
        {"id": "3", "name": "POST_CLOSE"},
    ]
    assert _find_option_id_by_name(options, "preopen") == "1"
    assert _find_option_id_by_name(options, "POSTCLOSE") == "3"
    assert _find_option_id_by_name(options, "NONE") == ""


def test_infer_slot_label_uses_keyword_then_track_default():
    preopen = BacklogTask(title="2026-04-13 장전 점검", source="x", section="체크", track="Plan")
    intraday = BacklogTask(title="장중 canary 모니터링", source="x", section="체크", track="Plan")
    postclose = BacklogTask(title="장후 리포트 검증", source="x", section="체크", track="Plan")
    fallback = BacklogTask(title="키워드 없음", source="x", section="체크", track="ScalpingLogic")
    plan_fallback = BacklogTask(title="키워드 없음", source="x", section="체크", track="Plan")
    assert _infer_slot_label(preopen) == "PREOPEN"
    assert _infer_slot_label(intraday) == "INTRADAY"
    assert _infer_slot_label(postclose) == "POSTCLOSE"
    assert _infer_slot_label(fallback) == "INTRADAY"
    assert _infer_slot_label(plan_fallback) == "POSTCLOSE"


def test_infer_slot_label_prefers_explicit_slot_over_section_keyword():
    task = BacklogTask(
        title="[AIPrompt0422] Gemini BUY recovery canary 1일차 판정 (Due: 2026-04-22, Slot: INTRADAY, TimeWindow: 12:00~12:20, Track: AIPrompt)",
        source="docs/2026-04-22-stage2-todo-checklist.md",
        section="장전/장중 체크리스트 (08:00~12:20) / 체크박스 미완료",
        track="Checklist0422",
    )
    assert _infer_slot_label(task) == "INTRADAY"


def test_slot_equals_normalized():
    assert _slot_equals("POST_CLOSE", "postclose")
    assert not _slot_equals("PREOPEN", "INTRADAY")


def test_infer_time_window_uses_explicit_range():
    task = BacklogTask(title="장중 2차 수집 (13:20~13:35)", source="x", section="체크", track="Checklist0414")
    assert _infer_time_window(task, slot_label="INTRADAY", default_duration_min=30) == "13:20~13:35"


def test_infer_time_window_uses_slot_default_when_missing():
    task = BacklogTask(title="일반 작업", source="x", section="체크", track="AIPrompt")
    assert _infer_time_window(task, slot_label="POSTCLOSE", default_duration_min=30) == "15:40~16:10"


def test_infer_time_window_holiday_forces_intraday_default_for_postclose():
    task = BacklogTask(title="일반 작업", source="x", section="체크", track="AIPrompt", due_date="2026-04-12")
    assert _infer_time_window(task, slot_label="POSTCLOSE", default_duration_min=30) == "10:00~10:30"


def test_infer_time_window_holiday_ignores_explicit_postclose_range():
    task = BacklogTask(
        title="휴장일 작업 (15:40~16:10)",
        source="x",
        section="체크",
        track="AIPrompt",
        due_date="2026-04-12",
    )
    assert _infer_time_window(task, slot_label="POSTCLOSE", default_duration_min=30) == "10:00~10:30"


def test_infer_time_window_unscheduled_keyword():
    task = BacklogTask(title="예약 작업(미정)", source="x", section="체크", track="Plan")
    assert _infer_time_window(task, slot_label="POSTCLOSE", default_duration_min=30) == "UNSCHEDULED"


def test_infer_apply_target_text_detects_remote_and_main():
    assert _infer_apply_target_text("원격 canary 설정 반영") == "remote"
    assert _infer_apply_target_text("main 운영서버 승격") == "main"
    assert _infer_apply_target_text("main/원격 동시 비교") == "main,remote"
    assert _infer_apply_target_text("일반 문서 작업") == "-"


def test_ensure_apply_target_fills_missing_target():
    task = BacklogTask(
        title="원격 canary 설정값 확정",
        source="docs/2026-04-15-stage2-todo-checklist.md",
        section="장전 체크리스트",
        track="Checklist0415",
    )
    filled = _ensure_apply_target(task)
    assert filled.apply_target == "remote"


def test_env_bool_uses_default_when_blank(monkeypatch):
    monkeypatch.delenv("X_FLAG", raising=False)
    assert _env_bool("X_FLAG", True) is True
    monkeypatch.setenv("X_FLAG", "")
    assert _env_bool("X_FLAG", True) is True
    monkeypatch.setenv("X_FLAG", "false")
    assert _env_bool("X_FLAG", True) is False


def test_env_uses_default_when_blank(monkeypatch):
    monkeypatch.delenv("X_NAME", raising=False)
    assert _env("X_NAME", "Slot") == "Slot"
    monkeypatch.setenv("X_NAME", "")
    assert _env("X_NAME", "Slot") == "Slot"


def test_sync_backlog_updates_due_for_existing_item(monkeypatch):
    task = BacklogTask(
        title="작업 2 AI 운영계측 추가",
        source="docs/prompt.md",
        section="P0. 즉시 착수 가능한 확인/계측",
        track="AIPrompt",
        due_date="2026-04-12",
    )
    existing_title = "[AIPrompt] 작업 2 AI 운영계측 추가"

    monkeypatch.setenv("GH_PROJECT_TOKEN", "token")
    monkeypatch.setenv("GH_PROJECT_OWNER", "JaehwanPark")
    monkeypatch.setenv("GH_PROJECT_NUMBER", "1")
    monkeypatch.setattr(
        "src.engine.sync_docs_backlog_to_project.collect_backlog_tasks",
        lambda: [task],
    )
    monkeypatch.setattr(
        "src.engine.sync_docs_backlog_to_project._fetch_project_metadata",
        lambda *args, **kwargs: (
            "PROJECT_1",
            {
                "Due": {"id": "FIELD_DUE", "__typename": "ProjectV2Field", "dataType": "DATE"},
            },
            {existing_title},
            [
                ProjectItem(
                    item_id="ITEM_1",
                    title=existing_title,
                    content_type="DraftIssue",
                    due_date="",
                    slot="",
                    time_window="",
                )
            ],
        ),
    )

    calls = []

    def _fake_graphql_request(token, query, variables):
        calls.append(variables)
        return {}

    monkeypatch.setattr("src.engine.sync_docs_backlog_to_project._graphql_request", _fake_graphql_request)

    summary = sync_backlog_to_project(dry_run=False, limit=10)
    assert summary["created_or_would_create"] == 0
    assert summary["due_filled"] == 1
    assert summary["due_reclassified"] == 0
    assert any(call.get("value") == {"date": "2026-04-12"} for call in calls)
