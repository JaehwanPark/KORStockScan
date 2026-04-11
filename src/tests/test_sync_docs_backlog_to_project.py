from src.engine.sync_docs_backlog_to_project import (
    collect_backlog_tasks,
    parse_checklist_tasks,
    parse_plan_tasks,
    parse_prompt_tasks,
    parse_scalping_logic_tasks,
)


def test_parse_plan_tasks_has_remaining_items():
    tasks = parse_plan_tasks()
    titles = [t.title for t in tasks]
    assert any("0-1b 원격 경량 프로파일링" in title for title in titles)


def test_parse_checklist_excludes_done_checkboxes():
    tasks = parse_checklist_tasks()
    titles = [t.title for t in tasks]
    assert any("원격 `latency remote_v2` 설정 유지 상태 확인".replace("`", "") in title for title in titles)
    assert all("선반영 범위 확정" not in title for title in titles)


def test_parse_scalping_logic_has_phase2_and_phase3():
    tasks = parse_scalping_logic_tasks()
    titles = [t.title for t in tasks]
    assert any(title.startswith("2-1 ") for title in titles)
    assert any(title.startswith("3-1 ") for title in titles)


def test_parse_prompt_has_priority_and_detail_tasks():
    tasks = parse_prompt_tasks()
    titles = [t.title for t in tasks]
    assert any("SCALP_PRESET_TP SELL 의도 확인" in title for title in titles)
    assert any(title.startswith("작업 10 ") for title in titles)


def test_collect_backlog_tasks_deduped():
    tasks = collect_backlog_tasks()
    normalized = [" ".join(t.title.split()).lower() for t in tasks]
    assert len(normalized) == len(set(normalized))
