from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.engine.error_detectors import process_health as process_health_module
from src.engine.error_detectors.process_health import (
    ProcessHealthDetector,
    reset_heartbeat,
    write_heartbeat,
    HEARTBEAT_PATH,
    POSTCLOSE_BOT_ISOLATION_PATH,
)


_ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT = (
    process_health_module._samsung_morning_runtime_contract
)


@pytest.mark.parametrize('leak', ['none', 'timer', 'process', 'buy', 'main', 'exit'])
def test_registry_retirement_negative_census_preserves_main_and_exits(tmp_path, monkeypatch, leak):
    from src.engine.infrastructure import runtime_release_router as router
    from src.trading.config.owner_retirement import RETIRED_EPISODE_PROFILES
    units = router._retirement_units(RETIRED_EPISODE_PROFILES)
    monkeypatch.setattr(router, '_episode_retirement_receipts', lambda root: [])
    states = {unit: dict(ActiveState='inactive', UnitFileState='masked', MainPID='0') for unit in units}
    processes, orders = [], []
    if leak == 'timer':
        states[next(u for u in units if u.endswith('.timer'))]['UnitFileState'] = 'enabled'
    if leak == 'process':
        processes = [dict(pid=1, argv=['python', '-m', 'src.trading.low_price_two_leg.runtime',
                                      '--profile', 'renamed', '--symbol', '034020'])]
    if leak in {'buy', 'main', 'exit'}:
        orders = [dict(event='INTENT_RESERVED', order_date='2026-10-07', symbol='034020',
            side='SELL' if leak == 'exit' else 'BUY', action='NEW',
            owner_type='main_scalping' if leak == 'main' else 'episode', intent_id='i')]
    result = process_health_module._retirement_expected_set(tmp_path,
        datetime.fromisoformat('2026-10-07T08:00:00+09:00'),
        states=states, processes=processes, registry_rows=orders)
    assert result['status'] == ('retirement_leak' if leak in {'timer','process','buy'} else 'retired_not_expected')


def test_retirement_census_missing_units_is_unverified(tmp_path, monkeypatch):
    from src.engine.infrastructure import runtime_release_router as router
    monkeypatch.setattr(router, '_episode_retirement_receipts', lambda root: [])
    result = process_health_module._retirement_expected_set(tmp_path,
        datetime.fromisoformat('2026-10-07T08:00:00+09:00'), states={}, processes=[], registry_rows=[])
    assert result['status'] == 'retirement_unverified'


def test_retirement_process_identity_is_executed_module_not_test_targets():
    assert process_health_module._process_entrypoint(['python','-m','pytest',
        'src/tests/test_widget_retirement.py','src/tests/test_episode_retirement_main_watch.py']) == 'pytest'
    assert process_health_module._process_entrypoint(['bash','-c','python -m src.trading.widget_auto_trade']) == ''
    assert process_health_module._process_entrypoint(['python','-m','src.trading.widget_auto_trade.engine']) == 'src.trading.widget_auto_trade.engine'


@pytest.mark.parametrize('error,alive', [
    (PermissionError(1, 'different runtime user'), True),
    (ProcessLookupError(3, 'no process'), False),
    (OSError(5, 'unexpected I/O fault'), False),
])
def test_pid_presence_separates_signal_permission_from_absence(monkeypatch,error,alive):
    def probe(pid,signal):
        assert (pid,signal)==(1234,0)
        raise error
    monkeypatch.setattr(os,'kill',probe)
    assert process_health_module._pid_exists(1234) is alive


def test_retired_samsung_expected_set_accepts_disabled_timers(monkeypatch):
    monkeypatch.setattr(
        process_health_module, "_systemd_unit_state",
        lambda unit: {
            "unit": unit,
            "LoadState": "loaded",
            "UnitFileState": "disabled",
            "ActiveState": "inactive",
            "MainPID": 0,
        },
    )
    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-29T17:05:00+09:00")
    )
    assert result["severity"] == "pass"
    assert result["status"] == "retired_one_share_timers_inactive"


def test_retired_samsung_expected_set_detects_reenabled_timer(monkeypatch):
    def unit_state(unit):
        enabled = unit == "korstockscan-samsung-morning-one-share.timer"
        return {
            "unit": unit,
            "LoadState": "loaded",
            "UnitFileState": "enabled" if enabled else "disabled",
            "ActiveState": "active" if enabled else "inactive",
            "MainPID": 0,
        }

    monkeypatch.setattr(process_health_module, "_systemd_unit_state", unit_state)
    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-29T17:05:00+09:00")
    )
    assert result["severity"] == "fail"
    assert result["reason"] == "retired_timer_enabled_or_active"


def test_retired_samsung_expected_set_rejects_incomplete_systemd_state(monkeypatch):
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_state",
        lambda unit: {"unit": unit, "UnitFileState": "disabled"},
    )
    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-29T17:05:00+09:00")
    )
    assert result["severity"] == "fail"
    assert result["reason"] == "retired_unit_unreadable"


def test_retired_samsung_expected_set_accepts_removed_units(monkeypatch):
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_state",
        lambda unit: {
            "unit": unit,
            "LoadState": "not-found",
            "ActiveState": "inactive",
            "UnitFileState": "",
            "MainPID": 0,
        },
    )
    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-29T17:05:00+09:00")
    )
    assert result["severity"] == "pass"


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch, tmp_path):
    monkeypatch.setattr(
        process_health_module, "is_krx_trading_day", lambda target: True
    )
    heartbeat_path = tmp_path / "error_detector_heartbeat.json"
    isolation_path = tmp_path / "postclose_bot_isolation.json"
    pipeline_events_dir = tmp_path / "pipeline_events"
    monkeypatch.setattr(process_health_module, "HEARTBEAT_PATH", heartbeat_path)
    monkeypatch.setattr(process_health_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        process_health_module, "POSTCLOSE_BOT_ISOLATION_PATH", isolation_path
    )
    monkeypatch.setattr(
        process_health_module, "PIPELINE_EVENTS_DIR", pipeline_events_dir
    )
    monkeypatch.setitem(globals(), "HEARTBEAT_PATH", heartbeat_path)
    monkeypatch.setitem(globals(), "POSTCLOSE_BOT_ISOLATION_PATH", isolation_path)
    monkeypatch.setattr(
        process_health_module,
        "_samsung_morning_runtime_contract",
        lambda now: {
            "severity": "pass",
            "status": "not_applicable_test_default",
            "target_date": now.date().isoformat(),
        },
    )
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: True,
    )


class TestProcessHealthDetector:
    def setup_method(self):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        if POSTCLOSE_BOT_ISOLATION_PATH.exists():
            POSTCLOSE_BOT_ISOLATION_PATH.unlink()

    def teardown_method(self):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        if POSTCLOSE_BOT_ISOLATION_PATH.exists():
            POSTCLOSE_BOT_ISOLATION_PATH.unlink()

    def test_heartbeat_write_main_loop(self):
        write_heartbeat("main_loop")
        assert HEARTBEAT_PATH.exists()
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "last_beat" in data["main_loop"]
        assert data["main_loop"]["pid"] == os.getpid()

    def test_heartbeat_write_thread(self):
        write_heartbeat("telegram")
        assert HEARTBEAT_PATH.exists()
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "threads" in data
        assert "telegram" in data["threads"]
        assert data["threads"]["telegram"]["alive"] is True

    def test_heartbeat_append_thread(self):
        write_heartbeat("main_loop")
        write_heartbeat("crisis_monitor")
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "crisis_monitor" in data["threads"]

    def test_reset_heartbeat_discards_stale_threads(self):
        write_heartbeat("main_loop")
        write_heartbeat("scalping_scanner")
        reset_heartbeat()
        write_heartbeat("main_loop")
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "scalping_scanner" not in data.get("threads", {})

    def test_detector_pass_when_heartbeat_fresh(self):
        write_heartbeat("main_loop")
        write_heartbeat("telegram")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "pass"


    def test_detector_fails_for_recent_unowned_manual_control_holding_block(
        self, monkeypatch
    ):
        now = datetime.now().astimezone().replace(microsecond=0)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        monkeypatch.setattr(
            process_health_module,
            "manual_control_operator_exclusion_source",
            lambda code: "",
        )
        monkeypatch.setattr(
            process_health_module,
            "manual_control_auto_exclusion_source",
            lambda code: "",
        )
        monkeypatch.setattr(
            process_health_module,
            "evaluate_main_bot_control_exclusion",
            lambda code, **_kwargs: type(
                "Decision", (), {"excluded": True, "reason": "test"}
            )(),
        )
        pipeline_dir = process_health_module.PIPELINE_EVENTS_DIR
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        pipeline_path = pipeline_dir / f"pipeline_events_{now.date().isoformat()}.jsonl"
        pipeline_path.write_text(
            json.dumps(
                {
                    "stage": "manual_control_fast_exit_monitor_blocked",
                    "stock_name": "Sample Holding",
                    "stock_code": "249420",
                    "record_id": 38741,
                    "emitted_at": now.isoformat(),
                    "fields": {
                        "target_status": "HOLDING",
                        "target_strategy": "SCALPING",
                        "manual_control_exclusion_source": "test_config.txt",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        guard = result.details["manual_control_holding_guard"]
        assert guard["status"] == "active_unowned_manual_control_holding_block"
        assert guard["active_block_count"] == 1
        assert guard["active_blocks"][0]["classification"] == (
            "stale_in_memory_or_unowned_exclusion"
        )
        assert "Sample Holding(249420)" in result.summary
        assert "do not bypass quantity" in result.recommended_action

    def test_detector_ignores_stale_block_after_main_policy_releases_holding(
        self, monkeypatch
    ):
        now = datetime.now().astimezone().replace(microsecond=0)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        monkeypatch.setattr(
            process_health_module,
            "manual_control_operator_exclusion_source",
            lambda code: "",
        )
        monkeypatch.setattr(
            process_health_module,
            "manual_control_auto_exclusion_source",
            lambda code: "",
        )
        monkeypatch.setattr(
            process_health_module,
            "evaluate_main_bot_control_exclusion",
            lambda code, **_kwargs: type(
                "Decision", (), {"excluded": False, "reason": "policy_allows"}
            )(),
        )
        pipeline_dir = process_health_module.PIPELINE_EVENTS_DIR
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        pipeline_path = pipeline_dir / f"pipeline_events_{now.date().isoformat()}.jsonl"
        pipeline_path.write_text(
            json.dumps(
                {
                    "stage": "manual_control_fast_exit_monitor_blocked",
                    "stock_name": "Released Holding",
                    "stock_code": "005930",
                    "record_id": 102,
                    "emitted_at": now.isoformat(),
                    "fields": {
                        "target_status": "HOLDING",
                        "target_strategy": "SCALPING",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["manual_control_holding_guard"]["active_block_count"] == 0

    def test_detector_accepts_recent_explicit_operator_holding_exclusion(
        self, monkeypatch
    ):
        now = datetime.now().astimezone().replace(microsecond=0)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        monkeypatch.setattr(
            process_health_module,
            "manual_control_operator_exclusion_source",
            lambda code: "manual_operator",
        )
        monkeypatch.setattr(
            process_health_module,
            "manual_control_auto_exclusion_source",
            lambda code: "",
        )
        pipeline_dir = process_health_module.PIPELINE_EVENTS_DIR
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        pipeline_path = pipeline_dir / f"pipeline_events_{now.date().isoformat()}.jsonl"
        pipeline_path.write_text(
            json.dumps(
                {
                    "stage": "manual_control_fast_exit_monitor_blocked",
                    "stock_name": "Operator Holding",
                    "stock_code": "005930",
                    "record_id": 101,
                    "emitted_at": now.isoformat(),
                    "fields": {
                        "target_status": "HOLDING",
                        "target_strategy": "SCALPING",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        guard = result.details["manual_control_holding_guard"]
        assert guard["recent_holding_event_count"] == 1
        assert guard["recent_blocked_holding_count"] == 1
        assert guard["active_block_count"] == 0

    @pytest.mark.parametrize("thread_alive", [True, False])
    @pytest.mark.parametrize("other_source", [None, "", "auto_open_loss", "auto_hard_stop_handoff_extra"])
    def test_hard_stop_handoff_is_expected_but_other_unowned_blocks_still_fail(
        self, monkeypatch, other_source, thread_alive
    ):
        now = datetime.now().astimezone().replace(microsecond=0)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        monkeypatch.setattr(process_health_module, "manual_control_operator_exclusion_source", lambda code: "")
        monkeypatch.setattr(
            process_health_module, "manual_control_auto_exclusion_source",
            lambda code: "auto_hard_stop_handoff" if code == "456010" else other_source,
        )
        monkeypatch.setattr(
            process_health_module, "evaluate_main_bot_control_exclusion",
            lambda code, **kwargs: type("Decision", (), {"excluded": True, "reason": "operator_manual_control_excluded_symbol"})(),
        )
        codes = ["456010"] + (["123456"] if other_source is not None else [])
        rows = [{"stage": "manual_control_fast_exit_monitor_blocked", "stock_code": code,
                 "record_id": i + 1, "emitted_at": now.isoformat(),
                 "fields": {"target_status": "HOLDING", "target_strategy": "SCALPING"}}
                for i, code in enumerate(codes)]
        directory = process_health_module.PIPELINE_EVENTS_DIR
        directory.mkdir(parents=True)
        (directory / f"pipeline_events_{now.date().isoformat()}.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram", alive=thread_alive)
        result = ProcessHealthDetector().check()
        guard = result.details["manual_control_holding_guard"]
        assert guard["expected_hard_stop_handoff_count"] == 1
        assert guard["expected_hard_stop_handoffs"][0]["stock_code"] == "456010"
        assert guard["recent_blocked_holding_count"] == len(codes)
        assert guard["active_block_count"] == len(codes) - 1
        assert result.severity == ("pass" if other_source is None and thread_alive else "fail")
        if other_source is None:
            assert guard["status"] == "expected_hard_stop_manual_handoff"

    def test_detector_accepts_latest_legacy_handoff_retirement(self, monkeypatch):
        now = datetime.now().astimezone().replace(microsecond=0)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        monkeypatch.setattr(
            process_health_module,
            "manual_control_operator_exclusion_source",
            lambda code: "",
        )
        monkeypatch.setattr(
            process_health_module,
            "manual_control_auto_exclusion_source",
            lambda code: "",
        )
        pipeline_dir = process_health_module.PIPELINE_EVENTS_DIR
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        pipeline_path = pipeline_dir / f"pipeline_events_{now.date().isoformat()}.jsonl"
        rows = [
            {
                "stage": "manual_control_fast_exit_monitor_blocked",
                "stock_name": "Recovered Holding",
                "stock_code": "249420",
                "record_id": 38741,
                "emitted_at": datetime.fromtimestamp(
                    now.timestamp() - 1, tz=now.tzinfo
                ).isoformat(),
                "fields": {
                    "target_status": "HOLDING",
                    "target_strategy": "SCALPING",
                },
            },
            {
                "stage": "manual_control_legacy_scale_in_qty_handoff_retired",
                "stock_name": "Recovered Holding",
                "stock_code": "249420",
                "record_id": 38741,
                "emitted_at": now.isoformat(),
                "fields": {
                    "target_status": "HOLDING",
                    "target_strategy": "SCALPING",
                },
            },
        ]
        pipeline_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        guard = result.details["manual_control_holding_guard"]
        assert guard["recent_holding_event_count"] == 1
        assert guard["recent_blocked_holding_count"] == 0
        assert guard["active_block_count"] == 0

    def test_detector_fails_when_samsung_expected_runtime_fails(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module,
            "_samsung_morning_runtime_contract",
            lambda now: {
                "severity": "fail",
                "status": "expected_process_not_healthy",
                "reason": "exact_date_authority_missing_or_stale",
            },
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "Samsung morning" in result.summary
        assert result.details["samsung_morning_runtime"]["reason"] == (
            "exact_date_authority_missing_or_stale"
        )

    def test_detector_preserves_concurrent_main_and_samsung_failures(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        monkeypatch.setattr(
            process_health_module,
            "_samsung_morning_runtime_contract",
            lambda now: {
                "severity": "fail",
                "status": "expected_process_not_healthy",
                "reason": "exact_date_authority_missing_or_stale",
            },
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "Heartbeat file not found" in result.summary
        assert "Samsung morning expected runtime" in result.summary

    def test_detector_fails_immediately_when_thread_reports_stopped(self):
        write_heartbeat("main_loop")
        write_heartbeat("sniper_engine", alive=False)

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]
        assert result.details["thread_status"] == "stale"
        assert "sniper_engine" in result.summary

    def test_detector_passes_for_sniper_normal_market_close(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=20, minute=0, second=3, microsecond=0)
        )
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        write_heartbeat("main_loop")
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
            unresolved_scalping_count=0,
            unresolved_scalping_codes="",
        )
        # The finalizer writes alive=False once more without knowing the
        # branch reason. The explicit normal terminal marker must survive.
        write_heartbeat("sniper_engine", alive=False)
        state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        state["main_loop"]["last_beat"] = now.isoformat(timespec="seconds")
        state["threads"]["sniper_engine"]["last_beat"] = now.isoformat(
            timespec="seconds"
        )
        HEARTBEAT_PATH.write_text(json.dumps(state), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["thread_status"] == "expected_terminal"
        assert result.details["expected_stopped_threads"] == ["sniper_engine"]
        assert result.details["thread_terminal_reason"]["sniper_engine"] == (
            "market_close"
        )
        assert "sniper_engine" in result.summary
        terminal = state["threads"]["sniper_engine"]
        assert terminal["unresolved_scalping_count"] == 0
        assert terminal["unresolved_scalping_codes"] == ""

    def test_sniper_heartbeat_call_keywords_match_writer_contract(self):
        source = Path(process_health_module.__file__).parents[1] / "kiwoom_sniper_v2.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_sn_whb"
        ]
        assert calls
        for call in calls:
            inspect.signature(write_heartbeat).bind(
                *[object() for _ in call.args],
                **{keyword.arg: object() for keyword in call.keywords},
            )

    @pytest.mark.parametrize(
        "reason,count,codes",
        [
            ("market_close_unresolved_scalping_positions", 1, "005930"),
            ("market_close", 1, "005930"),
            ("market_close", -1, ""),
            ("market_close", "0", ""),
            ("market_close", False, ""),
            ("market_close", 0, "005930"),
        ],
    )
    def test_terminal_diagnostics_survive_finalizer_and_remain_fail_closed(
        self, monkeypatch, reason, count, codes
    ):
        now = datetime.now().astimezone().replace(hour=20, minute=1)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason=reason,
            unresolved_scalping_count=count,
            unresolved_scalping_codes=codes,
        )
        write_heartbeat("sniper_engine", alive=False)
        state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        terminal = state["threads"]["sniper_engine"]
        terminal["last_beat"] = now.isoformat(timespec="seconds")
        assert terminal["terminal_reason"] == reason
        assert terminal["unresolved_scalping_count"] == count
        assert terminal["unresolved_scalping_codes"] == codes
        assert not process_health_module._is_expected_thread_terminal(
            "sniper_engine", terminal, now_ts=now.timestamp()
        )

    def test_new_terminal_reason_does_not_reuse_prior_custody_diagnostics(self):
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
            unresolved_scalping_count=0,
            unresolved_scalping_codes="",
        )
        write_heartbeat("sniper_engine", alive=False, terminal_reason="unexpected_stop")
        terminal = json.loads(HEARTBEAT_PATH.read_text())["threads"]["sniper_engine"]
        assert terminal["terminal_reason"] == "unexpected_stop"
        assert "unresolved_scalping_count" not in terminal
        assert "unresolved_scalping_codes" not in terminal

    def test_detector_rejects_market_close_reason_before_cutoff(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=19, minute=59, second=59, microsecond=0)
        )
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        write_heartbeat("main_loop")
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
        )
        state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        state["main_loop"]["last_beat"] = now.isoformat(timespec="seconds")
        state["threads"]["sniper_engine"]["last_beat"] = now.isoformat(
            timespec="seconds"
        )
        HEARTBEAT_PATH.write_text(json.dumps(state), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]

    def test_detector_rejects_prior_date_market_close_terminal(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=20, minute=1, second=0, microsecond=0)
        )
        prior = now - timedelta(days=1)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        HEARTBEAT_PATH.write_text(
            json.dumps(
                {
                    "main_loop": {
                        "last_beat": now.isoformat(timespec="seconds"),
                        "pid": os.getpid(),
                    },
                    "threads": {
                        "sniper_engine": {
                            "last_beat": prior.isoformat(timespec="seconds"),
                            "alive": False,
                            "terminal_reason": "market_close",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]

    def test_live_heartbeat_clears_prior_terminal_reason(self):
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
            unresolved_scalping_count=1,
            unresolved_scalping_codes="005930",
        )
        write_heartbeat("sniper_engine")

        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))

        assert data["threads"]["sniper_engine"]["alive"] is True
        assert "terminal_reason" not in data["threads"]["sniper_engine"]
        assert "unresolved_scalping_count" not in data["threads"]["sniper_engine"]
        assert "unresolved_scalping_codes" not in data["threads"]["sniper_engine"]

    def test_detector_fail_when_no_heartbeat(self, monkeypatch):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "fail"
        assert "not found" in result.summary.lower()

    def test_detector_fail_when_main_loop_stale(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        write_heartbeat("main_loop")
        stale_data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": os.getpid(),
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(stale_data), encoding="utf-8")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "fail"
        assert "stale" in result.summary.lower()

    def test_detector_warning_when_no_threads(self):
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": os.getpid(),
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "warning"

    def test_detector_pass_when_no_heartbeat_outside_expected_runtime(
        self, monkeypatch
    ):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: False
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "expected_stopped"

    def test_detector_pass_when_pid_dead_outside_expected_runtime(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: False
        )
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "pid_dead"

    def test_detector_fail_when_pid_dead_inside_expected_runtime(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["main_loop_status"] == "startup_not_observed"
        assert "prior-run PID" in result.summary
        assert "PREOPEN handoff" in result.recommended_action

    def test_detector_keeps_dead_current_run_pid_classification(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(
            process_health_module.ProcessHealthDetector,
            "restart_grace_sec",
            property(lambda self: 0),
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["main_loop_status"] == "pid_dead"
        assert "no longer alive" in result.summary

    def test_detector_passes_when_pid_dead_during_postclose_bot_isolation(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        POSTCLOSE_BOT_ISOLATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        POSTCLOSE_BOT_ISOLATION_PATH.write_text(
            json.dumps(
                {
                    "active": True,
                    "target_date": "2026-05-22",
                    "session": "bot",
                    "action": "restart",
                    "reason": "threshold_cycle_postclose_resource_isolation",
                    "started_at": datetime.now()
                    .astimezone()
                    .isoformat(timespec="seconds"),
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "postclose_isolation_pid_dead"
        assert result.details["postclose_bot_isolation"]["reason"] == (
            "threshold_cycle_postclose_resource_isolation"
        )
        assert "No immediate restart" in result.recommended_action
        assert "stop/isolation" in result.recommended_action

    def test_detector_fail_when_postclose_bot_isolation_marker_is_stale(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        POSTCLOSE_BOT_ISOLATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        POSTCLOSE_BOT_ISOLATION_PATH.write_text(
            json.dumps(
                {
                    "active": True,
                    "target_date": "2026-05-22",
                    "session": "bot",
                    "action": "restart",
                    "reason": "threshold_cycle_postclose_resource_isolation",
                    "started_at": "2000-01-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "postclose_bot_isolation" not in result.details

    def test_detector_warns_for_dead_pid_during_restart_grace(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "restart_grace_pid_handoff"
        assert "restart grace" in result.summary

    def test_detector_warns_for_dead_startup_pid_during_grace(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 1.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "startup_grace_prior_run_heartbeat"
        assert "prior-run PID" in result.summary

    @pytest.mark.parametrize("heartbeat_state", ["missing", "stale"])
    @pytest.mark.parametrize("elapsed", [30.0, 180.0])
    def test_detector_startup_grace_boundary_for_heartbeat_gaps(
        self, monkeypatch, heartbeat_state, elapsed
    ):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        if heartbeat_state == "stale":
            HEARTBEAT_PATH.write_text(
                json.dumps(
                    {
                        "main_loop": {
                            "last_beat": "2000-01-01T00:00:00+00:00",
                            "pid": os.getpid(),
                        }
                    }
                ),
                encoding="utf-8",
            )
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: elapsed
        )
        monkeypatch.setattr(
            ProcessHealthDetector, "startup_grace_sec", property(lambda self: 180)
        )

        result = ProcessHealthDetector().check()

        assert result.severity == ("warning" if elapsed < 180 else "fail")
        assert result.details["seconds_since_expected_start"] == elapsed
        if heartbeat_state == "stale":
            assert result.details["main_loop_status"] == "stale"
        elif elapsed < 180:
            assert result.details["main_loop_status"] == "startup_grace_waiting"


def _mock_samsung_systemd_states(
    monkeypatch, *, live: dict, preflight: dict | None = None
):
    states = {
        process_health_module._SAMSUNG_MORNING_TIMER_UNIT: {
            "LoadState": "loaded",
            "UnitFileState": "enabled",
            "ActiveState": "active",
            "SubState": "waiting",
            "Result": "success",
            "Triggers": process_health_module._SAMSUNG_MORNING_LIVE_UNIT,
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT: preflight
        or {
            "LoadState": "loaded",
            "User": "ubuntu",
            "Group": "ubuntu",
            "ActiveState": "activating",
            "SubState": "start",
            "Result": "success",
            "MainPID": 15132,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
        process_health_module._SAMSUNG_MORNING_LIVE_UNIT: live,
    }
    states[process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT].setdefault(
        "User", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT].setdefault(
        "Group", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_LIVE_UNIT].setdefault(
        "User", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_LIVE_UNIT].setdefault(
        "Group", "ubuntu"
    )
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_state",
        lambda unit: {"unit": unit, **states[unit]},
    )
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_journal_receipt",
        lambda unit, *, target_date: {
            "unit": unit,
            "target_date": target_date,
            "status": "not_started",
            "started_at_epoch_us": None,
            "terminal_at_epoch_us": None,
            "runtime_effect": False,
        },
    )








def _write_samsung_authority(path, *, target_date: str, ready: bool):
    path.write_text(
        json.dumps(
            {
                "schema": process_health_module._SAMSUNG_MORNING_AUTHORITY_SCHEMA,
                "target_date": target_date,
                "status": "ready" if ready else "blocked",
                "observed_at_kst": f"{target_date}T07:57:00+09:00",
                "valid_until_kst": f"{target_date}T23:59:59+09:00",
                "decision_authority": (
                    "explicit_user_directed_morning_two_episode_live_start"
                ),
                "source_quality_gate": "PASS",
                "runtime_effect": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": False,
                "policy": {
                    "symbol": "005930",
                    "quantity": 20,
                    "allocation": (
                        "ten_shares_base_limit_and_ten_shares_base_plus_1tick"
                    ),
                    "maximum_episodes_per_day": 2,
                    "unfilled_target": "hold_position_without_forced_exit",
                },
                "rollback": {
                    "action": (
                        "fail_closed_and_disable_only_morning_two_leg_timer_and_services"
                    ),
                    "widget_service_effect": "none",
                },
                "decision": {
                    "ready": ready,
                    "target_date": target_date,
                    "main_bot_active": ready,
                    "main_bot_runtime_env_verified": ready,
                    "main_bot_pid": 14307 if ready else 0,
                    "shared_token_available": ready,
                    "operator_exclusion_source": "manual_operator" if ready else "",
                    "prior_reentry_state_clear": ready,
                    "parallel_widget_trading_allowed": True,
                    "independent_order_ledger_required": True,
                    "blockers": [] if ready else ["blocked"],
                },
            }
        ),
        encoding="utf-8",
    )


def test_samsung_runtime_warns_before_acceptance_deadline(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-01", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:04:59+09:00")
    )

    assert result["severity"] == "warning"
    assert result["status"] == "bounded_wait"
    assert result["reason"] == "exact_date_authority_missing_or_stale"


def test_samsung_runtime_fails_at_acceptance_deadline(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-01", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["status"] == "expected_process_not_healthy"
    assert result["reason"] == "exact_date_authority_missing_or_stale"


def test_samsung_runtime_passes_with_exact_authority_and_live_pid(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "pass"
    assert result["status"] == "healthy_active"


def test_systemd_unit_state_retries_transient_timeout(monkeypatch):
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout="LoadState=loaded\nActiveState=inactive\nMainPID=0\n",
            stderr="",
        )

    monkeypatch.setattr(process_health_module.subprocess, "run", run)

    state = process_health_module._systemd_unit_state("example.service")

    assert len(calls) == 2
    assert state["LoadState"] == "loaded"
    assert state["ActiveState"] == "inactive"
    assert state["MainPID"] == 0
    assert "query_error" not in state


def test_systemd_journal_receipt_uses_exact_started_message_and_latest_terminal(
    monkeypatch,
):
    rows = [
        {
            "__REALTIME_TIMESTAMP": "100",
            "UNIT": "example.service",
            "CODE_FUNC": "job_emit_done_message",
            "JOB_RESULT": "done",
            "MESSAGE": "Started example.service - Example.",
        },
        {
            "__REALTIME_TIMESTAMP": "200",
            "UNIT": "example.service",
            "CODE_FUNC": "unit_log_success",
            "MESSAGE": "example.service: Deactivated successfully.",
        },
        {
            "__REALTIME_TIMESTAMP": "201",
            "UNIT": "example.service",
            "CODE_FUNC": "job_emit_done_message",
            "JOB_RESULT": "done",
            "MESSAGE": "Stopped example.service - Example.",
        },
    ]
    monkeypatch.setattr(
        process_health_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="\n".join(json.dumps(row) for row in rows), stderr=""
        ),
    )

    success_receipt = process_health_module._systemd_unit_journal_receipt(
        "example.service", target_date="2026-09-14"
    )

    assert success_receipt["status"] == "success"
    assert success_receipt["started_at_epoch_us"] == 100
    assert success_receipt["terminal_at_epoch_us"] == 200
    assert success_receipt["runtime_effect"] is False

    rows.extend(
        [
            {
                "__REALTIME_TIMESTAMP": "300",
                "UNIT": "example.service",
                "CODE_FUNC": "job_emit_done_message",
                "JOB_RESULT": "done",
                "MESSAGE": "Started example.service - Example.",
            },
            {
                "__REALTIME_TIMESTAMP": "400",
                "UNIT": "example.service",
                "CODE_FUNC": "unit_log_failure",
                "MESSAGE": "example.service: Failed with result 'exit-code'.",
            },
        ]
    )
    failed_receipt = process_health_module._systemd_unit_journal_receipt(
        "example.service", target_date="2026-09-14"
    )

    assert failed_receipt["status"] == "failed"
    assert failed_receipt["started_at_epoch_us"] == 300
    assert failed_receipt["terminal_at_epoch_us"] == 400


def test_systemd_journal_receipt_accepts_finished_oneshot(monkeypatch):
    rows = [
        {
            "__REALTIME_TIMESTAMP": "100",
            "UNIT": "example-preflight.service",
            "CODE_FUNC": "unit_log_success",
            "MESSAGE": "example-preflight.service: Deactivated successfully.",
        },
        {
            "__REALTIME_TIMESTAMP": "101",
            "UNIT": "example-preflight.service",
            "CODE_FUNC": "job_emit_done_message",
            "JOB_RESULT": "done",
            "MESSAGE": "Finished example-preflight.service - Example preflight.",
        },
    ]
    monkeypatch.setattr(
        process_health_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="\n".join(json.dumps(row) for row in rows), stderr=""
        ),
    )

    receipt = process_health_module._systemd_unit_journal_receipt(
        "example-preflight.service", target_date="2026-09-14"
    )

    assert receipt["status"] == "success"
    assert receipt["started_at_epoch_us"] is None
    assert receipt["terminal_at_epoch_us"] == 101
    assert receipt["terminal_source"] == "finished_job"


def test_samsung_runtime_accepts_durable_success_after_host_reboot(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_journal_receipt",
        lambda unit, *, target_date: {
            "unit": unit,
            "target_date": target_date,
            "status": "success",
            "started_at_epoch_us": 100,
            "terminal_at_epoch_us": 200,
            "runtime_effect": False,
        },
    )
    monkeypatch.setattr(
        process_health_module, "_pid_cmdline_contains_bot_main", lambda pid: False
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T18:40:00+09:00")
    )

    assert result["severity"] == "pass"
    assert result["status"] == "one_shot_completed"
    assert result["reason"] == "exact_date_authority_and_terminal_service_success"
    assert result["live_journal_receipt"]["status"] == "success"


def test_samsung_runtime_reports_latest_journal_failure_before_stale_bound_pid(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )

    def journal_receipt(unit, *, target_date):
        return {
            "unit": unit,
            "target_date": target_date,
            "status": (
                "failed"
                if unit == process_health_module._SAMSUNG_MORNING_LIVE_UNIT
                else "success"
            ),
            "started_at_epoch_us": 100,
            "terminal_at_epoch_us": 200,
            "runtime_effect": False,
        }

    monkeypatch.setattr(
        process_health_module, "_systemd_unit_journal_receipt", journal_receipt
    )
    monkeypatch.setattr(
        process_health_module, "_pid_cmdline_contains_bot_main", lambda pid: False
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T18:40:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_live_service_failed"




def test_samsung_runtime_rejects_corrupt_authority_schema(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    payload["schema"] = "stale_schema"
    authority_path.write_text(json.dumps(payload), encoding="utf-8")
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_schema_invalid"


def test_samsung_runtime_rejects_authority_policy_drift(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    payload["policy"]["quantity"] = 21
    authority_path.write_text(json.dumps(payload), encoding="utf-8")
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_policy_invalid"


def test_samsung_runtime_rejects_prior_date_terminal_result(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Tue 2026-09-01 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_live_service_not_started"


def test_samsung_runtime_rejects_dead_bound_main_bot_pid(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: False,
    )
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_main_bot_pid_inactive"


def test_samsung_terminal_success_survives_planned_main_bot_shutdown(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: False,
    )
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T21:55:00+09:00")
    )

    assert result["severity"] == "pass"
    assert result["status"] == "one_shot_completed"


def test_samsung_runtime_fails_immediately_for_explicit_preflight_failure(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=False)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "failed",
            "SubState": "failed",
            "Result": "failed",
            "MainPID": 0,
            "ExecMainStatus": 3,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:00:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_preflight_failed"


def test_samsung_runtime_rejects_installed_credential_drift(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "User": "ubuntu",
            "Group": "www-data",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_service_credential_contract_mismatch"


@pytest.mark.parametrize(
    ("timer_change", "expected_reason"),
    [
        ({"UnitFileState": "disabled"}, "morning_timer_not_enabled"),
        (
            {"Triggers": "wrong-owner.service"},
            "morning_timer_trigger_contract_mismatch",
        ),
    ],
)
def test_samsung_runtime_rejects_timer_install_contract_drift(
    monkeypatch, tmp_path, timer_change, expected_reason
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )
    original_state = process_health_module._systemd_unit_state

    def changed_state(unit):
        state = original_state(unit)
        if unit == process_health_module._SAMSUNG_MORNING_TIMER_UNIT:
            state.update(timer_change)
        return state

    monkeypatch.setattr(process_health_module, "_systemd_unit_state", changed_state)

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == expected_reason
