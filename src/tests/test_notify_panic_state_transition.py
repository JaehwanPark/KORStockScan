import json

from src.engine import notify_panic_state_transition as mod


def test_panic_sell_start_and_release_notifications(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin", "user1", "user2"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps(
            {
                "panic_state": "PANIC_SELL",
                "panic_metrics": {"stop_loss_exit_count": 3},
                "microstructure_detector": {"metrics": {"max_panic_score": 0.82}},
            }
        ),
        encoding="utf-8",
    )

    first = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1000.0,
    )
    second = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1010.0,
    )
    report.write_text(
        json.dumps({"panic_state": "NORMAL", "panic_metrics": {}}), encoding="utf-8"
    )
    third = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1020.0,
    )
    fourth = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=state,
        now_ts=1030.0,
    )

    assert first == "sent"
    assert second == "no_transition"
    assert third == "release_pending"
    assert fourth == "sent"
    assert len(sent) == 6
    assert "패닉셀 주의" in sent[0][1]
    assert "체감 강도\n  🔴 ▰▰▰▰▰▰▰▰▰▰▱▱ 82% · 위험 높음" in sent[0][1]
    assert "패닉셀 경보 해제" in sent[-1][1]
    assert "해제 상태\n  🟢 회복 확인 · 신규 자동매매 변경 없음" in sent[-1][1]
    assert "체감 강도" not in sent[-1][1]
    assert "PANIC_SELL" not in sent[0][1]


def test_panic_sell_recovery_confirmed_debounces_release_before_reactive(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"panic_state": "RECOVERY_CONFIRMED"}), encoding="utf-8"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "release_pending"
    )

    report.write_text(json.dumps({"panic_state": "RECOVERY_WATCH"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "no_transition"
    )

    assert len(sent) == 1
    assert "패닉셀 주의" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "active"
    assert saved["panic_sell"]["state"] == "RECOVERY_WATCH"


def test_panic_sell_second_recovery_confirmed_releases_after_pending(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"panic_state": "RECOVERY_CONFIRMED"}), encoding="utf-8"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "release_pending"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "sent"
    )

    assert len(sent) == 2
    assert "패닉셀 주의" in sent[0][1]
    assert "패닉셀 경보 해제" in sent[1][1]


def test_panic_sell_restart_notice_is_suppressed_right_after_release(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-06-08.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "PANIC_SELL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "NORMAL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "release_pending"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "RECOVERY_WATCH"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1030.0
        )
        == "restart_suppressed_after_release"
    )

    assert len(sent) == 2
    assert "패닉셀 주의" in sent[0][1]
    assert "패닉셀 경보 해제" in sent[1][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "released"
    assert saved["panic_sell"]["state"] == "NORMAL"
    assert saved["panic_sell"]["last_notification"]["transition"] == "release"


def test_panic_sell_suppressed_restart_does_not_create_second_release(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-06-08.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "PANIC_SELL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "NORMAL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "release_pending"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "RECOVERY_WATCH"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1030.0
        )
        == "restart_suppressed_after_release"
    )

    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "NORMAL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1040.0
        )
        == "no_transition"
    )

    assert len(sent) == 2
    assert "패닉셀 경보 해제" in sent[1][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "released"
    assert saved["panic_sell"]["state"] == "NORMAL"
    assert saved["panic_sell"]["last_notification"]["transition"] == "release"


def test_panic_sell_restart_notice_sends_after_release_suppression_window(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-06-08.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "released",
                    "state": "NORMAL",
                    "session_key": "2026-06-08",
                    "updated_at_ts": 1000.0,
                    "report_file": str(report),
                    "last_notification": {
                        "transition": "release",
                        "sent_at_ts": 1000.0,
                        "state": "NORMAL",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "PANIC_SELL"}),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=2000.0
        )
        == "sent"
    )

    assert len(sent) == 1
    assert "패닉셀 주의" in sent[0][1]


def test_panic_sell_force_bypasses_restart_suppression_after_release(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-06-08.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "released",
                    "state": "NORMAL",
                    "session_key": "2026-06-08",
                    "updated_at_ts": 1000.0,
                    "report_file": str(report),
                    "last_notification": {
                        "transition": "release",
                        "sent_at_ts": 1000.0,
                        "state": "NORMAL",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps({"target_date": "2026-06-08", "panic_state": "RECOVERY_WATCH"}),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, force=True, now_ts=1030.0
        )
        == "sent"
    )

    assert len(sent) == 1
    assert "패닉셀" in sent[0][1]


def test_panic_sell_release_is_suppressed_for_stale_previous_day_active_state(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-05-21.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "active",
                    "state": "PANIC_SELL",
                    "updated_at_ts": 900.0,
                    "report_file": str(tmp_path / "panic_sell_defense_2026-05-20.json"),
                    "last_notification": {
                        "transition": "start",
                        "state": "PANIC_SELL",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps({"target_date": "2026-05-21", "panic_state": "NORMAL"}),
        encoding="utf-8",
    )

    status = mod.notify_from_report(
        report, kind="panic_sell", state_file=state, now_ts=1000.0
    )

    assert status == "stale_previous_active_reset"
    assert sent == []
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "released"
    assert saved["panic_sell"]["state"] == "NORMAL"
    assert saved["panic_sell"]["session_key"] == "2026-05-21"


def test_panic_sell_new_day_active_state_sends_start_after_stale_previous_day_active(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-05-21.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "active",
                    "state": "PANIC_SELL",
                    "updated_at_ts": 900.0,
                    "report_file": str(tmp_path / "panic_sell_defense_2026-05-20.json"),
                    "last_notification": {
                        "transition": "start",
                        "state": "PANIC_SELL",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps({"target_date": "2026-05-21", "panic_state": "PANIC_SELL"}),
        encoding="utf-8",
    )

    status = mod.notify_from_report(
        report, kind="panic_sell", state_file=state, now_ts=1000.0
    )

    assert status == "sent"
    assert len(sent) == 1
    assert "패닉셀" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "active"
    assert saved["panic_sell"]["state"] == "PANIC_SELL"
    assert saved["panic_sell"]["session_key"] == "2026-05-21"
    assert saved["panic_sell"]["last_notification"]["transition"] == "start"


def test_panic_sell_release_keeps_same_day_active_debounce_after_no_transition(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell_defense_2026-05-21.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps({"target_date": "2026-05-21", "panic_state": "PANIC_SELL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "no_transition"
    )

    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["session_key"] == "2026-05-21"
    assert saved["panic_sell"]["last_notification"]["transition"] == "start"

    report.write_text(
        json.dumps({"target_date": "2026-05-21", "panic_state": "NORMAL"}),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "release_pending"
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1030.0
        )
        == "sent"
    )

    assert len(sent) == 2
    assert "패닉셀 주의" in sent[0][1]
    assert "패닉셀 경보 해제" in sent[1][1]


def test_panic_sell_normal_release_is_debounced_before_reactive(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(json.dumps({"panic_state": "NORMAL"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "release_pending"
    )

    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1020.0
        )
        == "no_transition"
    )

    assert len(sent) == 1
    assert "패닉셀 주의" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "active"
    assert saved["panic_sell"]["state"] == "PANIC_SELL"


def test_panic_sell_market_breadth_watch_notice_names_breadth_context(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps(
            {
                "panic_state": "RECOVERY_WATCH",
                "panic_state_reasons": [
                    "live market panic breadth risk_off advisory",
                    "market breadth risk-off watch without panic confirmation",
                ],
                "panic_metrics": {"panic_detected": False},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.36},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )
    assert len(sent) == 1
    assert "시장 전반 약세 주의" in sent[0][1]
    assert "지수와 업종 전반이 약해졌습니다" in sent[0][1]
    assert "현재 단계\n  시장 전반 약세 관찰" in sent[0][1]
    assert "breadth" not in sent[0][1]
    assert "risk-off" not in sent[0][1]
    assert "cluster" not in sent[0][1]


def test_panic_sell_single_market_risk_off_does_not_send_release(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "active",
                    "state": "PANIC_SELL",
                    "updated_at_ts": 900.0,
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps(
            {
                "panic_state": "NORMAL",
                "panic_state_reasons": ["panic thresholds not breached"],
                "panic_metrics": {"panic_detected": False},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.31},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": False,
                    "market_panic_breadth_single_market_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "no_transition"
    )
    assert sent == []
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "active"
    assert saved["panic_sell"]["state"] == "RECOVERY_WATCH"


def test_panic_sell_single_market_risk_off_starts_watch_notice(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps(
            {
                "panic_state": "NORMAL",
                "panic_metrics": {"panic_detected": False},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.31},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": False,
                    "market_panic_breadth_single_market_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )
    assert len(sent) == 1
    assert "시장 전반 약세 주의" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "active"
    assert saved["panic_sell"]["state"] == "RECOVERY_WATCH"
    assert saved["panic_sell"]["context_label"] == "market_breadth_watch"


def test_panic_sell_active_context_escalation_sends_friendly_update(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    report.write_text(
        json.dumps(
            {
                "panic_state": "RECOVERY_WATCH",
                "panic_state_reasons": [
                    "market breadth risk-off watch without panic confirmation"
                ],
                "panic_metrics": {"panic_detected": False},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.37},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )

    report.write_text(
        json.dumps(
            {
                "panic_state": "PANIC_SELL",
                "panic_state_reasons": [
                    "panic thresholds breached",
                    "live market panic breadth risk_off advisory",
                    "recovery conditions not yet met",
                ],
                "panic_metrics": {"panic_detected": True, "stop_loss_exit_count": 10},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.37},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1010.0
        )
        == "sent"
    )

    assert len(sent) == 2
    assert "시장 전반 약세 주의" in sent[0][1]
    assert "시장 약세 + 손실 방어 구간" in sent[1][1]
    assert "현재 단계\n  시장 약세와 손실 방어 동시 감지" in sent[1][1]
    assert "자동매매 변경: 없음" in sent[1][1]
    assert "breadth" not in sent[1][1]
    assert "risk-off" not in sent[1][1]
    assert "cluster" not in sent[1][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["context_label"] == "market_and_stop_loss"


def test_panic_sell_active_state_without_context_sends_same_state_friendly_update(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_sell": {
                    "phase": "active",
                    "state": "PANIC_SELL",
                    "updated_at_ts": 900.0,
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps(
            {
                "panic_state": "PANIC_SELL",
                "panic_metrics": {"panic_detected": True, "stop_loss_exit_count": 10},
                "microstructure_detector": {
                    "panic_signal_count": 0,
                    "metrics": {"max_panic_score": 0.37},
                },
                "microstructure_market_context": {
                    "market_panic_breadth_risk_off_advisory": True,
                },
            }
        ),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "sent"
    )
    assert len(sent) == 1
    assert "시장 약세 + 손실 방어 구간" in sent[0][1]
    assert "breadth" not in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["context_label"] == "market_and_stop_loss"


def test_panic_buying_test_notice_goes_admin_only(tmp_path, monkeypatch):
    report = tmp_path / "panic_buying.json"
    state = tmp_path / "state.json"
    sent = []
    report.write_text(
        json.dumps(
            {
                "panic_buy_state": "PANIC_BUY",
                "panic_buy_metrics": {
                    "panic_buy_active_count": 2,
                    "max_panic_buy_score": 0.66,
                },
                "exhaustion_metrics": {"exhaustion_candidate_count": 1},
                "tp_counterfactual_summary": {"candidate_context_count": 4},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin", "user1"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    status = mod.notify_from_report(
        report,
        kind="panic_buying",
        audience="admin",
        state_file=state,
        force=True,
        now_ts=1000.0,
    )

    assert status == "sent"
    assert [chat_id for chat_id, _ in sent] == ["admin"]
    assert "패닉바잉 주의" in sent[0][1]
    assert "🟠 ▰▰▰▰▰▰▰▰▱▱▱▱ 66% · 주의" in sent[0][1]
    assert "체감 강도\n  ░░░░░░░░░░░░ 확인중" not in sent[0][1]
    assert "PANIC_BUY" not in sent[0][1]


def test_panic_buying_new_day_active_state_sends_start_after_stale_previous_day_active(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_buying_2026-05-21.json"
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    state.write_text(
        json.dumps(
            {
                "panic_buying": {
                    "phase": "active",
                    "state": "PANIC_BUY",
                    "updated_at_ts": 900.0,
                    "report_file": str(tmp_path / "panic_buying_2026-05-20.json"),
                    "last_notification": {
                        "transition": "start",
                        "state": "PANIC_BUY",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    report.write_text(
        json.dumps({"target_date": "2026-05-21", "panic_buy_state": "PANIC_BUY"}),
        encoding="utf-8",
    )

    status = mod.notify_from_report(
        report, kind="panic_buying", state_file=state, now_ts=1000.0
    )

    assert status == "sent"
    assert len(sent) == 1
    assert "패닉바잉" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_buying"]["phase"] == "active"
    assert saved["panic_buying"]["state"] == "PANIC_BUY"
    assert saved["panic_buying"]["session_key"] == "2026-05-21"
    assert saved["panic_buying"]["last_notification"]["transition"] == "start"


def test_missing_config_does_not_send(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    report.write_text(json.dumps({"panic_state": "PANIC_SELL"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("", ""))

    status = mod.notify_from_report(
        report,
        kind="panic_sell",
        audience="all",
        state_file=tmp_path / "state.json",
        now_ts=1000.0,
    )

    assert status == "missing_config"
