import json

from src.engine import notify_panic_state_transition as mod
from src.engine.market_panic_breadth_collector import (
    market_weakness_observation_id,
)
from src.engine.risk.market_weakness_threshold_policy import SCHEMA, threshold_hash


def _refresh_weakness_identity(report: dict) -> dict:
    observation = report["market_weakness_observation"]
    affected = sorted(observation.get("affected_markets") or [])
    recovered = sorted(observation.get("recovery_evidence_markets") or [])
    observation["affected_markets"] = affected
    observation["recovery_evidence_markets"] = recovered
    observation.setdefault("evidence", {})["affected_markets"] = affected
    observation["evidence"]["recovery_evidence_markets"] = recovered
    release_margin = observation.setdefault("release_margin", {})
    release_margin["markets"] = {
        market: {
            "passed": market in recovered,
            "source_quality_ready": True,
            "checks": {
                "market_index_recovered": market in recovered,
                "industry_down_ratio_recovered": market in recovered,
                "industry_severe_down_ratio_recovered": market in recovered,
                "stock_fall_ratio_recovered": market in recovered,
            },
        }
        for market in ("KOSPI", "KOSDAQ")
    }
    observation["observation_id"] = market_weakness_observation_id(observation)
    return report


def _weakness_report(raw_state: str, sequence: int) -> dict:
    as_of = f"2026-08-28T10:{sequence:02d}:00+09:00"
    report = {
        "target_date": "2026-08-28",
        "as_of": as_of,
        "panic_state": "RECOVERY_WATCH",
        "market_weakness_observation": {
            "schema_version": 2,
            "target_date": "2026-08-28",
            "as_of": as_of,
            "raw_state": raw_state,
            "affected_markets": (
                ["KOSDAQ", "KOSPI"]
                if raw_state == "BROAD_WEAKNESS"
                else (["KOSPI"] if raw_state == "SINGLE_MARKET_WEAKNESS" else [])
            ),
            "recovery_evidence_markets": (
                ["KOSDAQ", "KOSPI"] if raw_state == "RECOVERY_EVIDENCE" else []
            ),
            "source_quality_ready": True,
            "source_quality_status": "ok",
            "metric_role": "market_weakness_observation",
            "decision_authority": "source_quality_observation_only",
            "window_policy": "intraday_consecutive_unique_snapshot_hysteresis",
            "sample_floor": {
                "market_index_count": 2,
                "industry_row_count": 3,
                "activation_unique_observations": 2,
                "release_unique_observations": 3,
            },
            "primary_decision_metric": "raw_state_with_release_margin",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "auto_sell",
                "bot_restart",
                "provider_route_change",
                "widget_entry_block",
                "episode_entry_block",
                "open_buy_cancel",
                "target_order_cancel",
                "holding_policy_change",
                "price_or_quantity_change",
                "position_exit",
            ],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "evidence": {
                "market_index_change_pct": {"KOSPI": -1.4, "KOSDAQ": -0.2},
                "industry_down_ratio_pct": 68.0,
                "max_stock_fall_ratio_pct": 74.0,
                "affected_markets": (
                    ["KOSDAQ", "KOSPI"]
                    if raw_state == "BROAD_WEAKNESS"
                    else (["KOSPI"] if raw_state == "SINGLE_MARKET_WEAKNESS" else [])
                ),
                "recovery_evidence_markets": (
                    ["KOSDAQ", "KOSPI"] if raw_state == "RECOVERY_EVIDENCE" else []
                ),
                "market_states": {
                    market: {"source_quality_ready": True}
                    for market in ("KOSPI", "KOSDAQ")
                },
            },
            "release_margin": {
                "passed": raw_state == "RECOVERY_EVIDENCE",
                "thresholds": {
                    "each_market_index_above_pct": -0.9,
                    "weighted_market_index_above_pct": -0.9,
                    "industry_down_ratio_below_pct": 55.0,
                    "industry_severe_down_ratio_below_pct": 10.0,
                    "max_stock_fall_ratio_below_pct": 60.0,
                },
                "checks": {
                    "each_market_index_recovered": raw_state == "RECOVERY_EVIDENCE",
                    "weighted_market_index_recovered": raw_state == "RECOVERY_EVIDENCE",
                    "industry_down_ratio_recovered": raw_state == "RECOVERY_EVIDENCE",
                    "industry_severe_down_ratio_recovered": raw_state
                    == "RECOVERY_EVIDENCE",
                    "stock_fall_ratio_recovered": raw_state == "RECOVERY_EVIDENCE",
                },
            },
            "response_research_contract": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "control": "current_owner_behavior_unchanged",
            },
        },
    }
    return _refresh_weakness_identity(report)


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
        == "sent"
    )

    assert len(sent) == 2
    assert "패닉셀 주의" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["panic_sell"]["phase"] == "released"
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
        json.dumps({"target_date": "2026-06-08", "panic_state": "PANIC_SELL"}),
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
        json.dumps({"target_date": "2026-06-08", "panic_state": "PANIC_SELL"}),
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


def test_panic_sell_recovery_watch_is_not_a_panic_alert(tmp_path, monkeypatch):
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
        json.dumps({"panic_state": "RECOVERY_WATCH"}),
        encoding="utf-8",
    )

    assert (
        mod.notify_from_report(
            report, kind="panic_sell", state_file=state, now_ts=1000.0
        )
        == "no_transition"
    )
    assert sent == []


def test_market_weakness_requires_two_unique_observations(tmp_path, monkeypatch):
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
        json.dumps(_weakness_report("SINGLE_MARKET_WEAKNESS", 1)),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1000.0
        )
        == "activation_pending"
    )
    assert sent == []
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1001.0
        )
        == "duplicate_observation"
    )
    report.write_text(
        json.dumps(_weakness_report("SINGLE_MARKET_WEAKNESS", 2)),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "sent"
    )
    assert len(sent) == 1
    assert "한쪽 시장 약세 지속 관찰" in sent[0][1]
    assert "관찰 owner: source-only 상태·반사실 수집" in sent[0][1]
    assert "실행 bridge: 해당 시장 위젯·에피소드 신규·추가 매수 차단" in sent[0][1]
    assert "비영향: 메인봇·보유·매도·목표 주문 변경 없음" in sent[0][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "active"
    assert saved["market_weakness"]["weak_streak"] == 2


def test_market_weakness_notifier_consumes_observation_bound_reviewed_thresholds(
    tmp_path,
    monkeypatch,
):
    report_path = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    for sequence in (1, 2, 3):
        report = _weakness_report("SINGLE_MARKET_WEAKNESS", sequence)
        observation = report["market_weakness_observation"]
        observation["sample_floor"]["activation_unique_observations"] = 3
        observation["sample_floor"]["release_unique_observations"] = 4
        observation["hysteresis_policy"] = {
            "schema": SCHEMA,
            "target_date": "2026-08-28",
            "source_date": "2026-08-27",
            "source": "exact_date_applied_policy",
            "status": "applied",
            "policy_path": "/tmp/reviewed-policy.json",
            "policy_hash": threshold_hash(activation=3, release=4),
            "review_status": "passed_out_of_sample_review",
            "activation_unique_observations": 3,
            "release_unique_observations": 4,
            "minimum_observation_spacing_sec": 60,
            "runtime_effect": True,
            "axis": "market_weakness_hysteresis_consecutive_observation_counts",
        }
        _refresh_weakness_identity(report)
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = mod.notify_from_report(
            report_path,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )
        assert result == ("sent" if sequence == 3 else "activation_pending")

    saved = json.loads(state.read_text(encoding="utf-8"))["market_weakness"]
    assert saved["phase"] == "active"
    assert saved["weak_streak"] == 3
    assert saved["activation_unique_observations"] == 3
    assert saved["release_unique_observations"] == 4
    assert len(sent) == 1


def test_market_weakness_notifier_rejects_intraday_hysteresis_policy_change(
    tmp_path,
    monkeypatch,
):
    report_path = tmp_path / "panic_sell.json"
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(mod, "_send_telegram", lambda *_args, **_kwargs: None)

    first = _weakness_report("SINGLE_MARKET_WEAKNESS", 1)
    report_path.write_text(json.dumps(first), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report_path,
            kind="market_weakness",
            state_file=state_path,
            now_ts=1001.0,
        )
        == "activation_pending"
    )
    before = json.loads(state_path.read_text(encoding="utf-8"))

    changed = _weakness_report("SINGLE_MARKET_WEAKNESS", 2)
    observation = changed["market_weakness_observation"]
    observation["sample_floor"]["activation_unique_observations"] = 3
    observation["sample_floor"]["release_unique_observations"] = 4
    observation["hysteresis_policy"] = {
        "schema": SCHEMA,
        "target_date": "2026-08-28",
        "source_date": "2026-08-27",
        "source": "exact_date_applied_policy",
        "status": "applied",
        "policy_path": "/tmp/reviewed-policy.json",
        "policy_hash": threshold_hash(activation=3, release=4),
        "review_status": "passed_out_of_sample_review",
        "activation_unique_observations": 3,
        "release_unique_observations": 4,
        "minimum_observation_spacing_sec": 60,
        "runtime_effect": True,
        "axis": "market_weakness_hysteresis_consecutive_observation_counts",
    }
    _refresh_weakness_identity(changed)
    report_path.write_text(json.dumps(changed), encoding="utf-8")

    result = mod.notify_from_report(
        report_path,
        kind="market_weakness",
        state_file=state_path,
        now_ts=1002.0,
    )

    assert result == "intraday_hysteresis_policy_mismatch"
    assert json.loads(state_path.read_text(encoding="utf-8")) == before


def test_single_market_weakness_streak_does_not_cross_listing_markets(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(mod, "_send_telegram", lambda *args: None)

    first = _weakness_report("SINGLE_MARKET_WEAKNESS", 1)
    first["market_weakness_observation"]["affected_markets"] = ["KOSPI"]
    _refresh_weakness_identity(first)
    report.write_text(json.dumps(first), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1000.0
        )
        == "activation_pending"
    )

    second = _weakness_report("SINGLE_MARKET_WEAKNESS", 2)
    second["market_weakness_observation"]["affected_markets"] = ["KOSDAQ"]
    _refresh_weakness_identity(second)
    report.write_text(json.dumps(second), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "activation_pending"
    )

    saved = json.loads(state.read_text(encoding="utf-8"))["market_weakness"]
    assert saved["phase"] == "activation_pending"
    assert saved["weak_streak"] == 1
    assert saved["weak_streak_markets"] == ["KOSDAQ"]


def test_broad_raw_observation_does_not_overstate_partially_confirmed_scope(
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
        lambda token, chat_id, message: sent.append(message),
    )

    report.write_text(
        json.dumps(_weakness_report("SINGLE_MARKET_WEAKNESS", 1)),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1000.0
        )
        == "activation_pending"
    )
    report.write_text(
        json.dumps(_weakness_report("BROAD_WEAKNESS", 2)), encoding="utf-8"
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "sent"
    )

    saved = json.loads(state.read_text(encoding="utf-8"))["market_weakness"]
    assert saved["active_markets"] == ["KOSPI"]
    assert "한쪽 시장 약세 지속 관찰" in sent[0]
    assert "시장 전반 약세 지속" not in sent[0]


def test_single_market_latch_releases_on_same_market_recovery(tmp_path, monkeypatch):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(mod, "_send_telegram", lambda *args: sent.append(args))

    for sequence in (1, 2):
        value = _weakness_report("SINGLE_MARKET_WEAKNESS", sequence)
        value["market_weakness_observation"]["affected_markets"] = ["KOSPI"]
        _refresh_weakness_identity(value)
        report.write_text(json.dumps(value), encoding="utf-8")
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )

    for sequence in (3, 4, 5):
        value = _weakness_report("NEAR_WEAKNESS_BOUNDARY", sequence)
        value["market_weakness_observation"]["recovery_evidence_markets"] = ["KOSPI"]
        _refresh_weakness_identity(value)
        report.write_text(json.dumps(value), encoding="utf-8")
        status = mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1010.0 + sequence,
        )

    assert status == "sent"
    saved = json.loads(state.read_text(encoding="utf-8"))["market_weakness"]
    assert saved["phase"] == "released"
    assert saved["active_markets"] == []
    assert len(sent) == 2


def test_broad_latch_narrows_instead_of_releasing_when_one_market_recovers(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(mod, "_load_all_chat_ids", lambda: ["admin"])
    monkeypatch.setattr(mod, "_send_telegram", lambda *args: sent.append(args))

    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("BROAD_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )
    for sequence in (3, 4, 5):
        value = _weakness_report("NEAR_WEAKNESS_BOUNDARY", sequence)
        value["market_weakness_observation"]["recovery_evidence_markets"] = ["KOSPI"]
        _refresh_weakness_identity(value)
        report.write_text(json.dumps(value), encoding="utf-8")
        status = mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1010.0 + sequence,
        )

    assert status == "sent"
    saved = json.loads(state.read_text(encoding="utf-8"))["market_weakness"]
    assert saved["phase"] == "active"
    assert saved["active_scope"] == "SINGLE_MARKET_WEAKNESS"
    assert saved["active_markets"] == ["KOSDAQ"]
    assert len(sent) == 2


def test_market_weakness_distinct_observation_too_close_does_not_advance(
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

    first = _weakness_report("BROAD_WEAKNESS", 1)
    first_observation_id = first["market_weakness_observation"]["observation_id"]
    report.write_text(json.dumps(first), encoding="utf-8")
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1000.0
        )
        == "activation_pending"
    )
    too_close = _weakness_report("BROAD_WEAKNESS", 2)
    too_close["as_of"] = "2026-08-28T10:01:20+09:00"
    too_close["market_weakness_observation"]["as_of"] = "2026-08-28T10:01:20+09:00"
    _refresh_weakness_identity(too_close)
    report.write_text(json.dumps(too_close), encoding="utf-8")

    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1001.0
        )
        == "observation_too_close"
    )
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["weak_streak"] == 1
    assert saved["market_weakness"]["last_observation_id"] == first_observation_id
    assert sent == []


def test_market_weakness_recovery_requires_declared_release_margin(
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
    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("BROAD_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )

    invalid_release = _weakness_report("RECOVERY_EVIDENCE", 3)
    invalid_release["market_weakness_observation"]["release_margin"]["passed"] = False
    _refresh_weakness_identity(invalid_release)
    report.write_text(json.dumps(invalid_release), encoding="utf-8")

    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "source_quality_blocked"
    )
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "active"
    assert saved["market_weakness"]["recovery_streak"] == 0
    assert saved["market_weakness"]["last_source_gate"]["state_contract_valid"] is False
    assert len(sent) == 1


def test_market_weakness_missing_observation_identity_is_source_blocked(
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
    missing_identity = _weakness_report("BROAD_WEAKNESS", 1)
    missing_identity["market_weakness_observation"]["observation_id"] = ""
    report.write_text(json.dumps(missing_identity), encoding="utf-8")

    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1000.0
        )
        == "source_quality_blocked"
    )
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "unknown"
    assert saved["market_weakness"]["weak_streak"] == 0
    assert saved["market_weakness"]["last_source_gate"]["identity_valid"] is False
    assert sent == []


def test_market_weakness_observe_only_still_advances_canonical_state(
    tmp_path, monkeypatch
):
    report = tmp_path / "panic_sell.json"
    state = tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(
        mod,
        "_send_telegram",
        lambda token, chat_id, message: sent.append((chat_id, message)),
    )

    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("BROAD_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        assert (
            mod.notify_from_report(
                report,
                kind="market_weakness",
                state_file=state,
                now_ts=1000.0 + sequence,
                send_enabled=False,
            )
            == "state_updated_notify_disabled"
        )

    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "active"
    assert saved["market_weakness"]["weak_streak"] == 2
    assert "pending_notification" not in saved["market_weakness"]
    assert sent == []


def test_market_weakness_release_needs_three_margin_passes(tmp_path, monkeypatch):
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

    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("BROAD_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )
    report.write_text(
        json.dumps(_weakness_report("NEAR_WEAKNESS_BOUNDARY", 3)),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "weakness_latched"
    )
    for sequence in (4, 5):
        report.write_text(
            json.dumps(_weakness_report("RECOVERY_EVIDENCE", sequence)),
            encoding="utf-8",
        )
        assert (
            mod.notify_from_report(
                report,
                kind="market_weakness",
                state_file=state,
                now_ts=1010.0 + sequence,
            )
            == "release_pending"
        )
    report.write_text(
        json.dumps(_weakness_report("RECOVERY_EVIDENCE", 6)),
        encoding="utf-8",
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1020.0
        )
        == "sent"
    )
    assert len(sent) == 2
    assert "시장 전반 약세 지속" in sent[0][1]
    assert "시장 약세 관찰 해제" in sent[1][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "released"
    assert saved["market_weakness"]["recovery_streak"] == 3


def test_market_weakness_source_gap_never_releases_active_latch(tmp_path, monkeypatch):
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
    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("BROAD_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )
    blocked = _weakness_report("RECOVERY_EVIDENCE", 3)
    blocked["market_weakness_observation"]["source_quality_ready"] = False
    _refresh_weakness_identity(blocked)
    report.write_text(json.dumps(blocked), encoding="utf-8")

    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "source_quality_blocked"
    )
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["phase"] == "active"
    assert saved["market_weakness"]["recovery_streak"] == 0
    assert len(sent) == 1


def test_market_weakness_single_market_escalates_to_broad(tmp_path, monkeypatch):
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

    for sequence in (1, 2):
        report.write_text(
            json.dumps(_weakness_report("SINGLE_MARKET_WEAKNESS", sequence)),
            encoding="utf-8",
        )
        mod.notify_from_report(
            report,
            kind="market_weakness",
            state_file=state,
            now_ts=1000.0 + sequence,
        )
    report.write_text(
        json.dumps(_weakness_report("BROAD_WEAKNESS", 3)), encoding="utf-8"
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1010.0
        )
        == "no_transition"
    )
    report.write_text(
        json.dumps(_weakness_report("BROAD_WEAKNESS", 4)), encoding="utf-8"
    )
    assert (
        mod.notify_from_report(
            report, kind="market_weakness", state_file=state, now_ts=1020.0
        )
        == "sent"
    )
    assert len(sent) == 2
    assert "한쪽 시장 약세 지속 관찰" in sent[0][1]
    assert "시장 전반 약세로 확산" in sent[1][1]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["market_weakness"]["active_scope"] == "BROAD_WEAKNESS"


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
