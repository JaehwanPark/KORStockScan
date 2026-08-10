import ast
import hashlib
import json
import tomllib
from pathlib import Path

from src.engine.scalping.micro_reversion.canary_monitor import (
    CANARY_GUARD_SCHEMA,
    CANARY_MONITOR_SCHEMA,
    CanaryGuard,
    _FORBIDDEN_TRUE_FIELDS,
    _ZERO_STOP_COUNTERS,
    evaluate_canary_snapshot,
    load_canary_guard,
    run_callback_latency_preflight,
    write_canary_runtime_snapshot,
)


def _guard() -> CanaryGuard:
    return CanaryGuard(
        baseline_id="test-baseline",
        minimum_callback_samples=1_000,
        producer_callback_latency_p95_max_ms=1.0,
        producer_callback_latency_p99_max_ms=2.0,
        snapshot_stale_after_sec=30.0,
        config_sha256="test-sha",
    )


def _healthy_snapshot(**overrides):
    snapshot = {field: 0 for field in _ZERO_STOP_COUNTERS}
    snapshot.update({field: False for field in _FORBIDDEN_TRUE_FIELDS})
    snapshot.update(
        {
            "schema": "scalp_micro_reversion_forward_collector_v4",
            "collector_lifecycle": "running",
            "observer_runtime_loaded": True,
            "producer_observation_connected": True,
            "observer_runtime_effect": True,
            "observation_capture_active": True,
            "broker_order_forbidden": True,
            "writer_count": 0,
            "writer_alive_count": 0,
            "producer_0b_callback_count": 1_000,
            "producer_callback_latency_p95_ms": 0.1,
            "producer_callback_latency_p99_ms": 0.2,
            "isolated_error_type": None,
            "canary_auto_stop_reason": None,
        }
    )
    snapshot.update(overrides)
    return snapshot


def _write_guard(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                f'schema = "{CANARY_GUARD_SCHEMA}"',
                'baseline_id = "test-baseline"',
                "",
                "[limits]",
                "minimum_callback_samples = 1000",
                "producer_callback_latency_p95_max_ms = 1.0",
                "producer_callback_latency_p99_max_ms = 2.0",
                "snapshot_stale_after_sec = 30.0",
            )
        ),
        encoding="utf-8",
    )


def test_guard_loader_and_healthy_snapshot_contract(tmp_path) -> None:
    guard_path = tmp_path / "guard.toml"
    _write_guard(guard_path)

    guard = load_canary_guard(guard_path)
    evaluation = evaluate_canary_snapshot(_healthy_snapshot(), guard)

    assert guard.baseline_id == "test-baseline"
    assert evaluation["status"] == "healthy_observer_canary"
    assert evaluation["stop_required"] is False
    assert evaluation["latency_guard_armed"] is True


def test_guard_stops_on_drop_leak_authority_and_latency() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            observation_dropped_envelope_count=1,
            manual_control_event_leak_count=1,
            actual_order_submitted=True,
            producer_callback_latency_p95_ms=1.1,
            producer_callback_latency_p99_ms=2.1,
        ),
        _guard(),
    )

    assert evaluation["status"] == "stop_required"
    assert evaluation["stop_required"] is True
    reasons = "\n".join(evaluation["stop_reasons"])
    assert "observation_dropped_envelope_count=1" in reasons
    assert "manual_control_event_leak_count=1" in reasons
    assert "forbidden_authority_field:actual_order_submitted" in reasons
    assert "producer_callback_latency_p95_exceeded" in reasons
    assert "producer_callback_latency_p99_exceeded" in reasons


def test_latency_guard_warms_up_without_hiding_hard_stop() -> None:
    warming = evaluate_canary_snapshot(
        _healthy_snapshot(producer_0b_callback_count=999),
        _guard(),
    )
    stopped = evaluate_canary_snapshot(
        _healthy_snapshot(
            producer_0b_callback_count=999,
            writer_error_count=1,
        ),
        _guard(),
    )

    assert warming["status"] == "warming_up"
    assert warming["stop_required"] is False
    assert stopped["status"] == "stop_required"
    assert stopped["stop_required"] is True


def test_writer_liveness_mismatch_is_an_immediate_stop() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(writer_count=2, writer_alive_count=1),
        _guard(),
    )

    assert evaluation["stop_required"] is True
    assert "writer_liveness_mismatch:alive=1,expected=2" in evaluation["stop_reasons"]


def test_manifest_failure_is_an_immediate_stop() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(writer_manifest_error_count=1),
        _guard(),
    )

    assert evaluation["stop_required"] is True
    assert (
        "nonzero_stop_metric:writer_manifest_error_count=1"
        in evaluation["stop_reasons"]
    )


def test_closed_snapshot_requires_completed_reconciliation() -> None:
    clean = evaluate_canary_snapshot(
        _healthy_snapshot(
            collector_lifecycle="closed",
            producer_observation_connected=False,
            observer_runtime_effect=False,
            observation_capture_active=False,
            reference_reconciliation_completed=True,
        ),
        _guard(),
    )
    incomplete = evaluate_canary_snapshot(
        _healthy_snapshot(
            collector_lifecycle="closed",
            producer_observation_connected=False,
            observer_runtime_effect=False,
            observation_capture_active=False,
            reference_reconciliation_completed=False,
        ),
        _guard(),
    )

    assert clean["status"] == "stopped_clean"
    assert clean["stop_required"] is False
    assert incomplete["stop_required"] is True
    assert "reconciliation_not_completed_after_close" in incomplete["stop_reasons"]


def test_runtime_snapshot_is_atomic_and_keeps_no_trading_authority(tmp_path) -> None:
    guard_path = tmp_path / "guard.toml"
    output_path = tmp_path / "runtime" / "latest.json"
    _write_guard(guard_path)

    payload = write_canary_runtime_snapshot(
        _healthy_snapshot(),
        guard_path=guard_path,
        output_path=output_path,
    )
    persisted = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["schema"] == CANARY_MONITOR_SCHEMA
    assert persisted == payload
    assert payload["decision_authority"] == (
        "observer_canary_stop_only_no_trading_authority"
    )
    assert payload["canary_guard"]["stop_required"] is False
    assert list(output_path.parent.glob("*.tmp")) == []


def test_main_server_preflight_is_reproducible_and_drop_free() -> None:
    report = run_callback_latency_preflight(
        iterations=1_000,
        warmup=10,
        repeats=3,
    )

    assert report["workload"]["observer_off_then_on"] is True
    assert report["workload"]["path_capture_enabled_on"] is True
    assert report["workload"]["discovery_enabled_on"] is False
    assert report["summary"]["queue_drop_count"] == 0
    assert report["summary"]["worker_error_count"] == 0
    assert report["frozen_limits"]["producer_callback_latency_p95_max_ms"] > 0
    assert report["frozen_limits"]["producer_callback_latency_p99_max_ms"] > 0


def test_repository_guard_matches_frozen_baseline_artifact() -> None:
    repository_root = Path(__file__).parents[2]
    guard_path = repository_root / "configs/scalp_micro_reversion_canary_guard.toml"
    guard = load_canary_guard(guard_path)
    payload = tomllib.loads(guard_path.read_text(encoding="utf-8"))
    baseline_path = repository_root / payload["baseline_artifact"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    assert baseline["baseline_id"] == guard.baseline_id
    assert baseline["frozen_limits"]["derivation"] == payload["derivation"]
    assert {
        key: baseline["frozen_limits"][key] for key in payload["limits"]
    } == payload["limits"]
    assert baseline["summary"]["queue_drop_count"] == 0
    assert baseline["summary"]["worker_error_count"] == 0
    evidence_files = {
        "benchmark_module_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/canary_monitor.py"
        ),
        "forward_collector_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/forward_collector.py"
        ),
        "path_journal_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/path_journal.py"
        ),
        "path_capture_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/path_capture.py"
        ),
        "p2_replay_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/p2_replay.py"
        ),
        "storage_maintenance_sha256": (
            repository_root
            / "src/engine/scalping/micro_reversion/storage_maintenance.py"
        ),
        "kiwoom_websocket_sha256": (repository_root / "src/engine/kiwoom_websocket.py"),
        "canary_guard_config_sha256": guard_path,
    }
    for field, path in evidence_files.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == baseline[field]


def test_canary_monitor_has_no_trading_authority_imports() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "engine"
        / "scalping"
        / "micro_reversion"
        / "canary_monitor.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")

    forbidden_fragments = ("broker", "execution", "order", "ai", "adm", "ldm")
    assert not any(
        fragment in module_name.lower()
        for module_name in imported
        for fragment in forbidden_fragments
    )
