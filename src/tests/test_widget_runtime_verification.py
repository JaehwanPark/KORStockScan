from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.trading.widget_auto_trade import runtime_verification as verification


@pytest.fixture
def context(tmp_path, monkeypatch):
    for key in verification.ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(verification.ENV_KEYS[0], "true")
    monkeypatch.setenv("OPENAI_API_KEY", "never-disclose-provider-secret")
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "never-disclose-account")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_TOKEN", "never-disclose-token")
    identity = {
        "pid": 42,
        "start_ticks": 123456,
        "boot_id": "a" * 8
        + "-"
        + "b" * 4
        + "-"
        + "c" * 4
        + "-"
        + "d" * 4
        + "-"
        + "e" * 12,
        "uids": [os.getuid()] * 4,
        "gids": [33] * 4,
    }
    monkeypatch.setattr(verification, "process_identity", lambda pid: dict(identity))
    monkeypatch.setattr(
        verification,
        "_systemd_identity",
        lambda: {"pid": 42, "cgroup": "/system.slice/widget.service"},
    )
    trader = SimpleNamespace(
        state_path=tmp_path / "state.json",
        _policy_date=datetime.now(verification.KST).date(),
        enabled=True,
        entry_qty=10,
        specs=[SimpleNamespace(code="005930")],
        _configured_execution_policies={"005930": "test-policy"},
        _dated_execution_policies={
            "005930": {"KRX_REGULAR": {"policy_id": "test-policy", "target": 2}}
        },
    )
    assert verification.publish_startup_receipt(trader, interval_sec=1, once=False)
    return SimpleNamespace(
        trader=trader,
        path=verification.receipt_path(trader.state_path),
        identity=identity,
        day=trader._policy_date,
        expected={verification.ENV_KEYS[0]: "true"},
    )


def verify(context, **kwargs):
    return verification.verify_startup_receipt(
        context.path,
        target_date=context.day,
        expected_environment=kwargs.pop("expected_environment", context.expected),
        **kwargs,
    )


def change_receipt(context, transform, *, rehash=True):
    payload = json.loads(context.path.read_text())
    payload.pop("receipt_sha256")
    transform(payload)
    payload["receipt_sha256"] = (
        verification.content_hash(payload) if rehash else "0" * 64
    )
    context.path.write_text(json.dumps(payload))


def test_round_trip_with_different_observer_gid_and_no_secrets(context):
    result = verify(context)
    assert result["passed"] is True
    assert result["status"] == "verified_requested_startup_fields"
    assert result["runtime_effect"] is False
    assert result["current_policy_consumption_verified"] is False
    assert result["verified_environment_keys"] == list(context.expected)
    contents = context.path.read_text()
    assert "never-disclose" not in contents
    assert "OPENAI_API_KEY" not in contents
    assert "BROKER_ACCOUNT_KEY" not in contents
    assert "AUTO_TRADER_TOKEN" not in contents
    assert context.path.stat().st_mode & 0o777 == 0o600


def test_missing_and_empty_environment_are_distinct(context):
    key = verification.ENV_KEYS[1]
    assert verify(context, expected_environment={key: None})["passed"]
    assert not verify(context, expected_environment={key: ""})["passed"]


def test_without_expectations_is_not_a_pass(context):
    result = verify(context, expected_environment=None)
    assert result["status"] == "observed_not_compared"
    assert not result["passed"]


def test_legacy_policy_list_order_is_not_silently_rehashed(context):
    legacy_policy = {
        "034020": {
            "allowed_entry_states": ["ENTRY_READY", "ENTRY_CAUTION"],
            "new_entry_runtime_eligible": False,
        }
    }
    context.trader._dated_execution_policies = legacy_policy
    assert verification.publish_startup_receipt(
        context.trader, interval_sec=1, once=False
    )
    before = context.path.read_bytes()
    legacy_hash = verification.content_hash(legacy_policy)
    canonical_policy = json.loads(json.dumps(legacy_policy))
    canonical_policy["034020"]["allowed_entry_states"].sort()
    result = verify(
        context, expected_policy_sha256=verification.content_hash(canonical_policy)
    )
    assert result["passed"] is False
    assert result["mismatched_keys"] == ["loaded_execution_policies_sha256"]
    historical = verify(context, expected_policy_sha256=legacy_hash)
    assert historical["passed"] is True
    assert historical["current_policy_consumption_verified"] is False
    assert context.path.read_bytes() == before


def test_mismatch_names_only_never_values(context):
    result = verify(
        context, expected_environment={verification.ENV_KEYS[0]: "secret-input"}
    )
    assert result["findings"] == ["configuration_mismatch"]
    assert result["mismatched_keys"] == [verification.ENV_KEYS[0]]
    assert "secret-input" not in json.dumps(result)


@pytest.mark.parametrize("mode", [0o666, 0o620, 0o602, 0o644, 0o400])
def test_review_rejects_writable_receipt(context, mode):
    context.path.chmod(mode)
    assert verify(context)["findings"] == ["receipt_owner_or_permissions_invalid"]


def test_review_rejects_foreign_file_owner(context):
    context.identity["uids"] = [os.getuid() + 1] * 4
    change_receipt(context, lambda payload: payload.update(process=context.identity))
    assert verify(context)["findings"] == ["receipt_owner_or_permissions_invalid"]


def test_review_rejects_replacement_during_verification(context, monkeypatch):
    calls = 0

    def read_unit():
        nonlocal calls
        calls += 1
        if calls == 2:
            replacement = context.path.parent / "replacement.json"
            replacement.write_text(context.path.read_text())
            replacement.chmod(0o600)
            os.replace(replacement, context.path)
        return {"pid": 42, "cgroup": "/system.slice/widget.service"}

    monkeypatch.setattr(verification, "_systemd_identity", read_unit)
    assert verify(context)["findings"] == ["receipt_changed_during_verification"]


@pytest.mark.parametrize("removed", [False, True])
def test_review_rejects_in_place_edit_or_removal(context, monkeypatch, removed):
    calls = 0

    def read_unit():
        nonlocal calls
        calls += 1
        if calls == 2:
            if removed:
                context.path.unlink()
            else:
                context.path.write_text(context.path.read_text() + "\n")
        return {"pid": 42, "cgroup": "/system.slice/widget.service"}

    monkeypatch.setattr(verification, "_systemd_identity", read_unit)
    assert verify(context)["findings"] == ["receipt_changed_during_verification"]


def test_review_logging_failure_does_not_escape_publisher(context, monkeypatch, capfd):
    def fail(*args, **kwargs):
        raise OSError("secret-error-text")

    monkeypatch.setattr(verification, "process_identity", fail)
    monkeypatch.setattr(
        verification.logging.getLogger(verification.__name__), "warning", fail
    )
    assert (
        verification.publish_startup_receipt(context.trader, interval_sec=1, once=False)
        is False
    )
    assert capfd.readouterr().err == "widget_runtime_receipt_publish_failed\n"


def test_review_both_log_sinks_failed_and_cleanup_failed_are_nonfatal(
    context, monkeypatch
):
    def fail(*args, **kwargs):
        raise OSError("secret-error-text")

    monkeypatch.setattr(verification.os, "replace", fail)
    monkeypatch.setattr(type(context.path), "unlink", fail)
    monkeypatch.setattr(
        verification.logging.getLogger(verification.__name__), "warning", fail
    )
    monkeypatch.setattr(verification.os, "write", fail)
    assert not verification.publish_startup_receipt(
        context.trader, interval_sec=1, once=False
    )


def test_review_change_while_reading_json_is_rejected(context, monkeypatch):
    original = verification._file_identity
    calls = 0

    def identity(info):
        nonlocal calls
        calls += 1
        result = original(info)
        if calls == 2:
            result["mtime_ns"] += 1
        return result

    monkeypatch.setattr(verification, "_file_identity", identity)
    assert verify(context)["findings"] == ["receipt_missing_or_invalid"]


@pytest.mark.parametrize(
    "expected", [[], {"TOKEN_SECRET": "value"}, {verification.ENV_KEYS[0]: 1}]
)
def test_bad_expectation_is_rejected_without_echo(context, expected):
    result = verify(context, expected_environment=expected)
    assert result["findings"] == ["expectation_invalid"]
    assert "TOKEN_SECRET" not in json.dumps(result)


@pytest.mark.parametrize(
    "key,value",
    [
        ("pid", 43),
        ("start_ticks", 999),
        ("boot_id", "0" * 36),
        ("uids", [-1] * 4),
        ("gids", [1000] * 4),
    ],
)
def test_wrong_or_reused_process_is_rejected(context, key, value):
    change_receipt(context, lambda payload: payload["process"].update({key: value}))
    assert verify(context)["findings"] == ["process_identity_unverified"]


def test_process_change_during_check_is_rejected(context, monkeypatch):
    calls = iter([{"pid": 42, "cgroup": "unit"}, {"pid": 43, "cgroup": "unit"}])
    monkeypatch.setattr(verification, "_systemd_identity", lambda: next(calls))
    assert verify(context)["findings"] == ["process_changed_during_verification"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_effect", True),
        ("allowed_runtime_apply", 0),
        ("decision_authority", "live"),
        ("schema_version", "old"),
        ("snapshot_phase", "pretend-current"),
        ("environment_hashes", {}),
        ("loaded_execution_policies_sha256", "not-a-hash"),
    ],
)
def test_invalid_contract_fails_closed(context, field, value):
    change_receipt(context, lambda payload: payload.update({field: value}))
    assert verify(context)["findings"] == ["receipt_missing_or_invalid"]


def test_bad_receipt_hash(context):
    change_receipt(context, lambda payload: None, rehash=False)
    assert not verify(context)["passed"]


def test_fifo_and_symlink_are_not_read(context):
    fifo = context.path.parent / "fifo"
    os.mkfifo(fifo)
    link = context.path.parent / "link.json"
    link.symlink_to(context.path)
    for path in (fifo, link):
        result = verification.verify_startup_receipt(path, target_date=context.day)
        assert result["findings"] == ["receipt_missing_or_invalid"]


def test_missing_receipt_is_explicit(context):
    result = verification.verify_startup_receipt(
        context.path.parent / "missing", target_date=context.day
    )
    assert result["findings"] == ["receipt_missing"]


@pytest.mark.parametrize("content", ["{bad-json", "[]", '{"a":1,"a":2}', " " * 65537])
def test_malformed_oversized_or_duplicate_json(context, content):
    context.path.write_text(content)
    assert verify(context)["findings"] == ["receipt_missing_or_invalid"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("startup_policy_date", "2000-01-01"),
        ("captured_at_kst", "2000-01-01T10:00:00+09:00"),
        ("captured_at_kst", "2026-09-07T10:00:00"),
        ("captured_at_kst", "2099-01-01T10:00:00+09:00"),
    ],
)
def test_wrong_day_naive_or_future_time(context, field, value):
    change_receipt(context, lambda payload: payload.update({field: value}))
    assert verify(context)["findings"] == ["startup_date_mismatch"]


def test_utc_timestamp_is_compared_in_kst(context):
    change_receipt(
        context,
        lambda payload: payload.update(
            {
                "captured_at_kst": datetime.fromisoformat(payload["captured_at_kst"])
                .astimezone(verification.ZoneInfo("UTC"))
                .isoformat()
            }
        ),
    )
    assert verify(context)["passed"]


def test_memory_policies_are_hashed_not_current_files(context):
    initial = json.loads(context.path.read_text())["loaded_execution_policies_sha256"]
    # Rewriting a hypothetical source cannot change what the startup loaded.
    (context.path.parent / "policy.json").write_text('{"different":"disk-generation"}')
    assert verify(context, expected_policy_sha256=initial)["passed"]
    context.trader._dated_execution_policies["005930"]["KRX_REGULAR"]["target"] = 3
    assert verification.publish_startup_receipt(
        context.trader, interval_sec=1, once=False
    )
    assert verify(context, expected_policy_sha256=initial)["findings"] == [
        "configuration_mismatch"
    ]


def test_instrumentation_failure_preserves_prior_bytes_and_hides_exception(
    context, monkeypatch, caplog
):
    prior = context.path.read_bytes()

    def fail(*args):
        raise PermissionError("secret-path-and-token")

    monkeypatch.setattr(verification.os, "replace", fail)
    assert not verification.publish_startup_receipt(
        context.trader, interval_sec=1, once=False
    )
    assert context.path.read_bytes() == prior
    assert not list(context.path.parent.glob(".widget-receipt-*"))
    assert "widget_runtime_receipt_publish_failed" in caplog.text
    assert "secret-path-and-token" not in caplog.text


def test_metadata_permission_failure_has_no_escalation(context, monkeypatch):
    def fail(pid):
        raise PermissionError("sensitive exception")

    monkeypatch.setattr(verification, "process_identity", fail)
    result = verify(context)
    assert result["findings"] == ["process_identity_unverified"]
    assert "sensitive" not in json.dumps(result)


def test_cli_is_read_only_missing_receipt(context, capsys):
    missing = context.path.parent / "missing.json"
    code = verification.main(
        ["--target-date", str(context.day), "--receipt-path", str(missing)]
    )
    assert code == 2
    assert not missing.exists()
    assert json.loads(capsys.readouterr().out)["passed"] is False


def test_cli_expected_values_not_echoed(context, capsys):
    path = context.path.parent / "expected.json"
    path.write_text(json.dumps(context.expected))
    assert (
        verification.main(
            [
                "--target-date",
                str(context.day),
                "--receipt-path",
                str(context.path),
                "--expected-env-json",
                str(path),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["passed"]


def test_process_stat_parser_handles_parentheses_and_never_reads_environ(tmp_path):
    root = tmp_path / "proc"
    process = root / "42"
    process.mkdir(parents=True)
    fields = ["S"] + ["0"] * 18 + ["34567"]
    (process / "stat").write_text("42 (python ) name) " + " ".join(fields))
    (process / "status").write_text("Uid:\t1000 1000 1000 1000\nGid:\t33 33 33 33\n")
    boot = root / "sys/kernel/random/boot_id"
    boot.parent.mkdir(parents=True)
    boot.write_text("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    result = verification.process_identity(42, proc_root=root)
    assert result["start_ticks"] == 34567
    assert result["gids"] == [33] * 4
    (process / "stat").write_text("42 (python) " + " ".join(["Z", *fields[1:]]))
    with pytest.raises(ValueError, match="process_not_running"):
        verification.process_identity(42, proc_root=root)


def test_systemd_reader_is_fixed_unit_and_bounded(monkeypatch):
    def run(command, **kwargs):
        assert command[:3] == ["systemctl", "show", verification.UNIT]
        assert kwargs["timeout"] == 5 and kwargs["check"] is True
        assert "shell" not in kwargs
        return SimpleNamespace(
            stdout="MainPID=42\nActiveState=active\nSubState=running\nControlGroup=/system.slice/widget.service\n"
        )

    monkeypatch.setattr(verification.subprocess, "run", run)
    assert verification._systemd_identity()["pid"] == 42


def test_actual_trader_constructor_can_publish_without_broker_calls(tmp_path):
    from src.trading.widget_auto_trade.engine import WidgetSignalAutoTrader

    trader = WidgetSignalAutoTrader(
        gateway=object(),
        specs=(),
        state_path=tmp_path / "state.json",
        owner_registry=object(),
        policy_loader=SimpleNamespace(resolve_all=lambda **kwargs: {}),
        enabled=False,
    )
    assert verification.publish_startup_receipt(trader, interval_sec=1, once=False)
    payload = json.loads(verification.receipt_path(trader.state_path).read_text())
    assert payload["process"]["pid"] == os.getpid()
    assert payload["loaded_execution_policies_sha256"] == verification.content_hash({})


def test_singleton_lock_failure_never_publishes_receipt(tmp_path, monkeypatch):
    from src.trading.widget_auto_trade import service

    monkeypatch.setattr(service, "_acquire_single_instance_lock", lambda path: None)

    def forbidden(*args, **kwargs):
        pytest.fail("duplicate service must not construct trader or publish")

    monkeypatch.setattr(service, "WidgetSignalAutoTrader", forbidden)
    monkeypatch.setattr(service, "publish_startup_receipt", forbidden)
    assert service.main(["--state-path", str(tmp_path / "state.json")]) == 3


def test_fresh_process_cli_emits_only_json_and_loads_no_engine(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.trading.widget_auto_trade.runtime_verification",
            "--target-date",
            "2026-09-07",
            "--receipt-path",
            str(tmp_path / "missing"),
        ],
        cwd=verification.PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert result.stderr == ""
    assert json.loads(result.stdout)["findings"] == ["receipt_missing"]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import src.trading.widget_auto_trade.runtime_verification; "
            "assert 'src.trading.widget_auto_trade.engine' not in sys.modules; "
            "assert 'src.utils.constants' not in sys.modules",
        ],
        cwd=verification.PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_lazy_package_keeps_public_exports():
    from src.trading import widget_auto_trade
    from src.trading.widget_auto_trade import engine

    assert widget_auto_trade.WidgetSignalAutoTrader is engine.WidgetSignalAutoTrader
    assert widget_auto_trade.EXECUTION_AUTHORITY == engine.EXECUTION_AUTHORITY
    with pytest.raises(AttributeError):
        widget_auto_trade.unknown_export


@pytest.mark.parametrize("once", [True, False])
def test_service_wires_receipt_before_trade_cycle_and_failure_is_nonfatal(
    tmp_path, monkeypatch, once
):
    from src.trading.widget_auto_trade import service

    events = []
    trader = SimpleNamespace(
        run_once=lambda: events.append("once"),
        run_forever=lambda **kwargs: events.append("forever"),
    )
    monkeypatch.setattr(service, "_acquire_single_instance_lock", lambda path: object())
    monkeypatch.setattr(service, "_env_qty", lambda: 10)
    monkeypatch.setattr(service, "_env_specs", lambda: ())
    monkeypatch.setattr(service, "_env_enabled", lambda: False)
    monkeypatch.setattr(service, "WidgetAutoTradeEntryTelegramNotifier", lambda: None)
    monkeypatch.setattr(service, "WidgetSignalAutoTrader", lambda **kwargs: trader)

    def publish(observed, **kwargs):
        assert observed is trader
        assert kwargs["once"] is once
        events.append("receipt")
        return False

    monkeypatch.setattr(service, "publish_startup_receipt", publish)
    assert (
        service.main(
            [
                "--state-path",
                str(tmp_path / "state.json"),
                *(["--once"] if once else []),
            ]
        )
        == 0
    )
    assert events == ["receipt", "once" if once else "forever"]
