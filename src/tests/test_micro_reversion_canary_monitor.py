import ast
import hashlib
import json
import tomllib
from pathlib import Path

from src.engine.scalping.micro_reversion.canary_monitor import (
    CANARY_GUARD_SCHEMA,
    CANARY_MONITOR_SCHEMA,
    CanaryGuard,
    _DEPTH_ROW_EXCLUSION_COUNTERS,
    _DEPTH_ZERO_STOP_COUNTERS,
    _FORBIDDEN_TRUE_FIELDS,
    _ROW_EXCLUSION_COUNTERS,
    _ZERO_STOP_COUNTERS,
    evaluate_canary_snapshot,
    load_canary_guard,
    run_callback_latency_preflight,
    write_canary_runtime_snapshot,
)
from src.engine.scalping.micro_reversion.forward_collector import (
    PRODUCER_CALLBACK_LATENCY_SCOPE,
)


def _guard() -> CanaryGuard:
    return CanaryGuard(
        baseline_id="test-baseline",
        minimum_callback_samples=1_000,
        producer_callback_latency_p95_max_ms=1.0,
        producer_callback_latency_p99_max_ms=2.0,
        latency_breach_confirmation_snapshots=3,
        latency_breach_immediate_multiplier=2.0,
        snapshot_stale_after_sec=30.0,
        config_sha256="test-sha",
    )


def _healthy_snapshot(**overrides):
    snapshot = {field: 0 for field in _ZERO_STOP_COUNTERS}
    snapshot.update({field: 0 for field in _ROW_EXCLUSION_COUNTERS})
    snapshot.update({field: False for field in _FORBIDDEN_TRUE_FIELDS})
    snapshot.update(
        {
            "schema": "scalp_micro_reversion_forward_collector_v9",
            "collector_lifecycle": "running",
            "observer_runtime_loaded": True,
            "producer_observation_connected": True,
            "observer_runtime_effect": True,
            "observation_capture_active": True,
            "broker_order_forbidden": True,
            "writer_count": 0,
            "writer_alive_count": 0,
            "producer_0b_callback_count": 1_000,
            "producer_callback_latency_scope": PRODUCER_CALLBACK_LATENCY_SCOPE,
            "producer_callback_latency_p95_ms": 0.1,
            "producer_callback_latency_p99_ms": 0.2,
            "isolated_error_type": None,
            "canary_auto_stop_reason": None,
            "path_exchange_timestamp_regression_exceeded_count": 0,
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
                "latency_breach_confirmation_snapshots = 3",
                "latency_breach_immediate_multiplier = 2.0",
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
    assert evaluation["latency_breach_confirmation_snapshots"] == 3
    assert evaluation["latency_breach_immediate_multiplier"] == 2.0


def test_low_disk_warning_does_not_stop_healthy_lossless_capture() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            writer_low_disk_watermark_breach_count=1,
            writer_capture_degraded_count=0,
            writer_dropped_envelope_count=0,
            writer_error_count=0,
            writer_storage_self_disabled_count=0,
            depth_writer_low_disk_watermark_breach_count=2,
        ),
        _guard(),
    )

    assert evaluation["status"] == "healthy_observer_canary"
    assert evaluation["stop_required"] is False
    assert evaluation["stop_reasons"] == ()
    assert evaluation["operational_capacity_warnings"] == (
        "writer_low_disk_watermark_capacity_warning:writers=1",
        "depth_writer_low_disk_watermark_capacity_warning:writers=2",
    )


def test_guard_excludes_queue_loss_but_stops_on_authority_and_latency() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            observation_dropped_envelope_count=1,
            actual_order_submitted=True,
            producer_callback_latency_p95_ms=1.1,
            producer_callback_latency_p99_ms=2.1,
        ),
        _guard(),
    )

    assert evaluation["status"] == "stop_required"
    assert evaluation["stop_required"] is True
    reasons = "\n".join(evaluation["stop_reasons"])
    assert "observation_dropped_envelope_count=1" not in reasons
    assert (
        "raw_row_exclusion_required:observation_dropped_envelope_count=1"
        in evaluation["source_quality_row_exclusions"]
    )
    assert "forbidden_authority_field:actual_order_submitted" in reasons
    assert "producer_callback_latency_p95_exceeded" in reasons
    assert "producer_callback_latency_p99_exceeded" in reasons


def test_guard_rejects_callback_latency_without_exact_0b_scope() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(producer_callback_latency_scope="combined_0b_0d"),
        _guard(),
    )

    assert evaluation["status"] == "stop_required"
    assert evaluation["stop_required"] is True
    assert "producer_callback_latency_scope_invalid" in evaluation["stop_reasons"]


def test_guard_does_not_apply_frozen_0b_limit_to_depth_callback_latency() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            producer_callback_latency_p95_ms=0.2,
            producer_callback_latency_p99_ms=0.4,
            producer_0d_callback_latency_p95_ms=8.0,
            producer_0d_callback_latency_p99_ms=12.0,
        ),
        _guard(),
    )

    assert evaluation["status"] == "healthy_observer_canary"
    assert evaluation["stop_required"] is False
    assert evaluation["stop_reasons"] == ()


def test_guard_keeps_collector_running_for_bounded_ingress_queue_loss() -> None:
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            observation_queue_full_count=82,
            observation_dropped_envelope_count=82,
        ),
        _guard(),
    )

    assert evaluation["status"] == (
        "healthy_observer_canary_with_source_row_exclusions"
    )
    assert evaluation["stop_required"] is False
    assert evaluation["raw_row_exclusion_required"] is True
    assert evaluation["stop_reasons"] == ()


def test_guard_quarantines_timestamp_regression_without_stopping_collector() -> None:
    quarantined = evaluate_canary_snapshot(
        _healthy_snapshot(
            path_exchange_timestamp_regression_count=1,
            path_exchange_timestamp_regression_quarantined_count=1,
            path_exchange_timestamp_regression_exceeded_count=0,
            path_exchange_timestamp_regression_max_ms=1_000,
            path_exchange_timestamp_regression_tolerance_ms=1_000,
        ),
        _guard(),
    )
    exceeded = evaluate_canary_snapshot(
        _healthy_snapshot(
            path_exchange_timestamp_regression_count=1,
            path_exchange_timestamp_regression_quarantined_count=0,
            path_exchange_timestamp_regression_exceeded_count=1,
            path_exchange_timestamp_regression_max_ms=2_000,
            path_exchange_timestamp_regression_tolerance_ms=1_000,
        ),
        _guard(),
    )

    assert quarantined["status"] == "healthy_observer_canary"
    assert quarantined["stop_required"] is False
    assert exceeded["status"] == ("healthy_observer_canary_with_source_row_exclusions")
    assert exceeded["stop_required"] is False
    assert (
        "raw_row_exclusion_required:"
        "path_exchange_timestamp_regression_exceeded_count=1"
        in exceeded["source_quality_row_exclusions"]
    )
    assert exceeded["raw_row_exclusion_required"] is True


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


def test_depth_capture_request_requires_live_worker_and_zero_stop_metrics() -> None:
    depth_metrics = {field: 0 for field in _DEPTH_ZERO_STOP_COUNTERS}
    depth_metrics.update({field: 0 for field in _DEPTH_ROW_EXCLUSION_COUNTERS})
    healthy = evaluate_canary_snapshot(
        _healthy_snapshot(
            depth_capture_requested=True,
            depth_capture_active=True,
            depth_writer_count=1,
            depth_writer_alive_count=1,
            **depth_metrics,
        ),
        _guard(),
    )
    stopped = evaluate_canary_snapshot(
        _healthy_snapshot(
            depth_capture_requested=True,
            depth_capture_active=False,
            depth_writer_count=1,
            depth_writer_alive_count=1,
            **depth_metrics,
        ),
        _guard(),
    )

    assert healthy["stop_required"] is False
    assert stopped["stop_required"] is True
    assert "depth_capture_requested_but_not_active" in stopped["stop_reasons"]


def test_depth_writer_liveness_mismatch_is_an_immediate_stop() -> None:
    depth_metrics = {field: 0 for field in _DEPTH_ZERO_STOP_COUNTERS}
    depth_metrics.update({field: 0 for field in _DEPTH_ROW_EXCLUSION_COUNTERS})
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            depth_capture_requested=True,
            depth_capture_active=True,
            depth_writer_count=2,
            depth_writer_alive_count=1,
            **depth_metrics,
        ),
        _guard(),
    )

    assert evaluation["stop_required"] is True
    assert (
        "depth_writer_liveness_mismatch:alive=1,expected=2"
        in evaluation["stop_reasons"]
    )


def test_closed_depth_snapshot_allows_stopped_worker_and_writer() -> None:
    depth_metrics = {field: 0 for field in _DEPTH_ZERO_STOP_COUNTERS}
    depth_metrics.update({field: 0 for field in _DEPTH_ROW_EXCLUSION_COUNTERS})
    evaluation = evaluate_canary_snapshot(
        _healthy_snapshot(
            collector_lifecycle="closed",
            observer_runtime_effect=False,
            producer_observation_connected=False,
            observation_capture_active=False,
            reference_reconciliation_completed=True,
            depth_capture_requested=True,
            depth_capture_active=False,
            depth_writer_count=1,
            depth_writer_alive_count=0,
            **depth_metrics,
        ),
        _guard(),
    )

    assert evaluation["stop_required"] is False


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
        "observation_adapter_sha256": (
            repository_root
            / "src/engine/scalping/micro_reversion/observation_adapter.py"
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
        "onset_quality_sha256": (
            repository_root / "src/engine/scalping/micro_reversion/onset_quality.py"
        ),
        "storage_maintenance_sha256": (
            repository_root
            / "src/engine/scalping/micro_reversion/storage_maintenance.py"
        ),
        "kiwoom_websocket_sha256": (repository_root / "src/engine/kiwoom_websocket.py"),
        "canary_guard_config_sha256": guard_path,
        "source_exclusion_manifest_sha256": (
            repository_root / "configs/scalp_micro_reversion_source_exclusions.json.txt"
        ),
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
