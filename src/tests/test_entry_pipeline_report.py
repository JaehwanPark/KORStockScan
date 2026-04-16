from src.engine import sniper_entry_pipeline_report as report_mod


def test_build_entry_pipeline_flow_report_prefers_jsonl_when_text_log_empty(tmp_path, monkeypatch):
    jsonl_path = tmp_path / "pipeline_events_2026-04-10.jsonl"
    jsonl_path.write_text(
        "\n".join(
            [
                '{"schema_version":1,"event_type":"pipeline_event","pipeline":"ENTRY_PIPELINE","stage":"ai_confirmed","stock_name":"테스트","stock_code":"000001","record_id":1001,"fields":{"ai_score":"85"},"emitted_at":"2026-04-10T09:41:31","emitted_date":"2026-04-10","text_payload":"[ENTRY_PIPELINE] 테스트(000001) stage=ai_confirmed id=1001 ai_score=85"}',
                '{"schema_version":1,"event_type":"pipeline_event","pipeline":"ENTRY_PIPELINE","stage":"entry_armed","stock_name":"테스트","stock_code":"000001","record_id":1001,"fields":{},"emitted_at":"2026-04-10T09:41:32","emitted_date":"2026-04-10","text_payload":"[ENTRY_PIPELINE] 테스트(000001) stage=entry_armed id=1001"}',
                '{"schema_version":1,"event_type":"pipeline_event","pipeline":"ENTRY_PIPELINE","stage":"budget_pass","stock_name":"테스트","stock_code":"000001","record_id":1001,"fields":{"deposit":"1000000"},"emitted_at":"2026-04-10T09:41:33","emitted_date":"2026-04-10","text_payload":"[ENTRY_PIPELINE] 테스트(000001) stage=budget_pass id=1001 deposit=1000000"}',
                '{"schema_version":1,"event_type":"pipeline_event","pipeline":"ENTRY_PIPELINE","stage":"latency_block","stock_name":"테스트","stock_code":"000001","record_id":1001,"fields":{"decision":"REJECT_DANGER"},"emitted_at":"2026-04-10T09:41:34","emitted_date":"2026-04-10","text_payload":"[ENTRY_PIPELINE] 테스트(000001) stage=latency_block id=1001 decision=REJECT_DANGER"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(report_mod, "_jsonl_path", lambda target_date: jsonl_path)
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: [])

    report = report_mod.build_entry_pipeline_flow_report("2026-04-10", since_time="09:41:30")

    assert report["has_data"] is True
    row = report["sections"]["recent_stocks"][0]
    assert row["record_id"] == "1001"
    assert row["latest_status"]["stage"] == "latency_block"
    assert row["stage_class"] == "blocked"
    assert [item["stage"] for item in row["pass_flow"]] == ["watching", "ai_confirmed", "entry_armed", "budget_pass"]


def test_latest_attempt_events_excludes_previous_submitted_attempt(monkeypatch):
    lines = [
        "[2026-04-07 09:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 09:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 09:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=budget_pass id=11",
        "[2026-04-07 09:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=latency_pass id=11",
        "[2026-04-07 09:00:04] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=order_bundle_submitted id=11",
        "[2026-04-07 10:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 10:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 10:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=budget_pass id=11",
        "[2026-04-07 10:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=latency_block id=11 reason=latency_state_danger",
    ]
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: lines)

    report = report_mod.build_entry_pipeline_flow_report("2026-04-07")

    row = report["sections"]["recent_stocks"][0]
    assert [item["stage"] for item in row["pass_flow"]] == [
        "watching",
        "ai_confirmed",
        "entry_armed",
        "budget_pass",
    ]
    assert row["confirmed_failure"]["stage"] == "latency_block"
    assert row["record_id"] == "11"
    assert all(event["stage"] != "order_bundle_submitted" for event in row["events"])
    assert report["metrics"]["budget_pass_stocks"] == 1
    assert report["metrics"]["budget_pass_to_submitted_rate"] == 0.0
    assert report["metrics"]["budget_pass_events"] == 2
    assert report["metrics"]["order_bundle_submitted_events"] == 1
    assert report["metrics"]["budget_pass_event_to_submitted_rate"] == 50.0


def test_latest_attempt_prefers_new_record_id_for_same_stock(monkeypatch):
    lines = [
        "[2026-04-07 09:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=11",
        "[2026-04-07 09:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=11",
        "[2026-04-07 09:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=order_bundle_submitted id=11",
        "[2026-04-07 09:00:03] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=dual_persona_shadow id=11 decision_type=gatekeeper",
        "[2026-04-07 10:00:00] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=ai_confirmed id=12",
        "[2026-04-07 10:00:01] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=entry_armed id=12",
        "[2026-04-07 10:00:02] INFO [ENTRY_PIPELINE] 엘지전자(066570) stage=blocked_zero_qty id=12 qty=0",
    ]
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: lines)

    report = report_mod.build_entry_pipeline_flow_report("2026-04-07")

    row = report["sections"]["recent_stocks"][0]
    assert row["record_id"] == "12"
    assert row["latest_status"]["stage"] == "blocked_zero_qty"
    assert [item["stage"] for item in row["pass_flow"]] == [
        "watching",
        "ai_confirmed",
        "entry_armed",
    ]
    assert all(event["fields"].get("id") == "12" for event in row["events"])


def test_entry_armed_expired_is_classified_as_waiting(monkeypatch, tmp_path):
    lines = [
        "[2026-04-10 09:10:00] INFO [ENTRY_PIPELINE] 테스트(111111) stage=ai_confirmed id=21 action=BUY ai_score=86",
        "[2026-04-10 09:10:01] INFO [ENTRY_PIPELINE] 테스트(111111) stage=entry_armed id=21 ttl_sec=20",
        "[2026-04-10 09:10:22] INFO [ENTRY_PIPELINE] 테스트(111111) stage=entry_armed_expired_after_wait id=21 waited_sec=21.0",
    ]
    jsonl_path = tmp_path / "pipeline_events_2026-04-10.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(report_mod, "_jsonl_path", lambda target_date: jsonl_path)
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date: lines)

    report = report_mod.build_entry_pipeline_flow_report("2026-04-10")

    row = report["sections"]["recent_stocks"][0]
    assert row["latest_status"]["stage"] == "entry_armed_expired_after_wait"
    assert row["stage_class"] == "waiting"
    assert report["metrics"]["expired_armed_total"] == 1
