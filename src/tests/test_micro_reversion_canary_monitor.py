import ast
import hashlib
import json
import tomllib
from pathlib import Path

import pytest

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
            "invalid_exchange_timestamp_count": 0,
            "stale_exchange_timestamp_block_count": 0,
            "invalid_depth_timestamp_count": 0,
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


@pytest.mark.parametrize(
    "field",
    [
        "invalid_exchange_timestamp_count",
        "stale_exchange_timestamp_block_count",
        "invalid_depth_timestamp_count",
    ],
)
def test_timestamp_rejections_require_source_exclusion_without_auto_stop(field):
    snapshot = _healthy_snapshot(**{field: 33})
    if field == "invalid_depth_timestamp_count":
        snapshot.update({key: 0 for key in _DEPTH_ZERO_STOP_COUNTERS})
        snapshot.update({key: 0 for key in _DEPTH_ROW_EXCLUSION_COUNTERS})
        snapshot.update(
            depth_capture_requested=True,
            depth_capture_active=True,
            depth_writer_count=0,
            depth_writer_alive_count=0,
        )
    result = evaluate_canary_snapshot(snapshot, _guard())
    assert result["stop_required"] is False
    assert result["raw_row_exclusion_required"] is True
    assert result["status"] == "healthy_observer_canary_with_source_row_exclusions"
    assert (
        f"timestamp_source_rejected_before_enqueue:{field}=33"
        in result["source_quality_row_exclusions"]
    )
    assert (
        result["timestamp_source_quality"]["exact_rejected_row_exclusion_proven"]
        is False
    )


def test_complete_timestamp_rejection_receipts_prove_exact_current_process_exclusion():
    samples = tuple(
        {
            "process_pid": 123,
            "symbol": symbol,
            "item": symbol,
            "venue": "KRX",
            "realtime_type": "0D",
            "local_observer_epoch": 1,
            "checked_at_ms": 1_000 + index,
            "reason": "stale_exchange_timestamp",
            "rejection_stage": "before_observer_enqueue",
            "rejection_index": index,
        }
        for index, symbol in enumerate(("002070", "355150"), start=1)
    )
    result = evaluate_canary_snapshot(
        _healthy_snapshot(
            invalid_depth_timestamp_count=2,
            stale_exchange_timestamp_block_count=0,
            timestamp_rejection_sample_total=2,
            timestamp_rejection_samples=samples,
            depth_capture_requested=True,
            depth_capture_active=True,
            depth_writer_count=0,
            depth_writer_alive_count=0,
            **{key: 0 for key in _DEPTH_ZERO_STOP_COUNTERS},
            **{key: 0 for key in _DEPTH_ROW_EXCLUSION_COUNTERS},
        ),
        _guard(),
    )

    timestamp = result["timestamp_source_quality"]
    assert timestamp["exact_rejected_row_exclusion_proven"] is True
    assert timestamp["rejection_receipt_coverage_status"] == (
        "complete_current_process"
    )
    assert timestamp["rejection_receipt_count"] == 2
    assert timestamp["rejection_receipt_expected_count"] == 2


def test_bounded_timestamp_rejection_tail_does_not_claim_complete_exclusion():
    samples = [
        {
            "process_pid": 123,
            "symbol": "002070",
            "item": "002070",
            "venue": "KRX",
            "realtime_type": "0B",
            "local_observer_epoch": 1,
            "checked_at_ms": 1_000 + index,
            "reason": "stale_exchange_timestamp",
            "rejection_stage": "before_observer_enqueue",
            "rejection_index": index,
        }
        for index in range(9, 73)
    ]
    result = evaluate_canary_snapshot(
        _healthy_snapshot(
            invalid_exchange_timestamp_count=72,
            stale_exchange_timestamp_block_count=72,
            timestamp_rejection_sample_total=72,
            timestamp_rejection_samples=samples,
        ),
        _guard(),
    )

    timestamp = result["timestamp_source_quality"]
    assert timestamp["exact_rejected_row_exclusion_proven"] is False
    assert timestamp["rejection_receipt_coverage_status"] == ("bounded_tail_or_invalid")


def test_malformed_timestamp_rejection_receipt_fails_closed_without_exception():
    result = evaluate_canary_snapshot(
        _healthy_snapshot(
            invalid_exchange_timestamp_count=1,
            timestamp_rejection_sample_total=1,
            timestamp_rejection_samples=[None],
        ),
        _guard(),
    )

    timestamp = result["timestamp_source_quality"]
    assert timestamp["exact_rejected_row_exclusion_proven"] is False
    assert timestamp["rejection_receipt_coverage_status"] == ("bounded_tail_or_invalid")


def test_timestamp_rejection_receipt_type_count_mismatch_fails_closed():
    sample = {
        "process_pid": 123,
        "symbol": "002070",
        "item": "002070",
        "venue": "KRX",
        "realtime_type": "0D",
        "local_observer_epoch": 1,
        "checked_at_ms": 1_000,
        "reason": "stale_exchange_timestamp",
        "rejection_stage": "before_observer_enqueue",
        "rejection_index": 1,
    }
    result = evaluate_canary_snapshot(
        _healthy_snapshot(
            invalid_exchange_timestamp_count=1,
            stale_exchange_timestamp_block_count=1,
            timestamp_rejection_sample_total=1,
            timestamp_rejection_samples=[sample],
        ),
        _guard(),
    )

    assert (
        result["timestamp_source_quality"]["exact_rejected_row_exclusion_proven"]
        is False
    )


@pytest.mark.parametrize("value", [None, -1, True, "bad", 0.5, float("inf")])
def test_missing_timestamp_census_is_not_healthy_source_evidence(value):
    result = evaluate_canary_snapshot(
        _healthy_snapshot(invalid_exchange_timestamp_count=value), _guard()
    )
    assert result["stop_required"] is False
    assert result["raw_row_exclusion_required"] is True


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


def _assert_frozen_source_or_reviewed_mount(path, expected):
    import hashlib

    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() == expected:
        return
    if path.name == "forward_collector.py" and expected == (
        "7f63c64aa7f2d3feb6da814d4dcbfda3dae25be8f22a8b96c92b7df58a8f7df4"
    ):
        # 9e0044b8 changes only the trusted shared data mount resolution.
        # Preserve the 9/10 measured receipt and verify every other byte.
        changed = (
            b"# Canonicalize only the trusted deployment mount, not artifact descendants.\n"
            b'DEFAULT_OUTPUT_ROOT = (\n    REPOSITORY_ROOT / "data"\n'
            b').resolve() / "observations/scalp_micro_reversion_forward"\n'
        )
        original = (
            b"DEFAULT_OUTPUT_ROOT = (\n"
            b'    REPOSITORY_ROOT / "data/observations/scalp_micro_reversion_forward"\n)\n'
        )
        assert source.count(changed) == 1
        source = source.replace(changed, original, 1)
    assert hashlib.sha256(source).hexdigest() == expected


def test_mount_compatibility_does_not_accept_unreviewed_source(tmp_path):
    source = (
        Path(__file__).parents[2]
        / "src/engine/scalping/micro_reversion/forward_collector.py"
    )
    changed = tmp_path / "forward_collector.py"
    changed.write_bytes(source.read_bytes() + b"\n# Unreviewed change\n")
    with pytest.raises(AssertionError):
        _assert_frozen_source_or_reviewed_mount(
            changed,
            "7f63c64aa7f2d3feb6da814d4dcbfda3dae25be8f22a8b96c92b7df58a8f7df4",
        )


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
        expected = baseline[field]
        if field == "benchmark_module_sha256":
            # Keep the frozen callback-latency benchmark receipt while
            # pinning the reviewed 2026-09-09 source-quality-only census
            # correction.  No callback, writer, stop, or trading authority
            # path changed.
            assert expected == (
                "3c703102ac68ab70315377b907f584dff4efb399d8818ebe84f6b6ba9f26cfd7"
            )
            # Black-only normalization of the reviewed census generation;
            # both AST pins below remain unchanged, as does the frozen receipt.
            expected = (
                "6626103c12138ff0a893f70c89931276c46b92a72d62875e2aaea7dec1629144"
            )
            tree = ast.parse(path.read_bytes())
            census_functions = [
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name
                in {
                    "timestamp_source_quality_census",
                    "_valid_timestamp_rejection_receipt",
                }
            ]
            assert hashlib.sha256(
                ast.dump(
                    ast.Module(body=census_functions, type_ignores=[]),
                    include_attributes=False,
                ).encode()
            ).hexdigest() == (
                "fac1550b0c453b2298a6e39727bb0bf1e47c69da6e5b25017ecf0ff833bda0b1"
            )
            tree.body = [node for node in tree.body if node not in census_functions]
            assert hashlib.sha256(
                ast.dump(tree, include_attributes=False).encode()
            ).hexdigest() == (
                "7048eb4130afeb6a5069a0a545082a788e11b42166a4194de0285eb25cc21336"
            )
        if field == "path_journal_sha256":
            # The callback baseline remains frozen.  The 2026-09-09 EBS-backed
            # compatibility change only raises PathStoragePolicy's projection
            # stop from 2 GiB to its existing 4 GiB hard partition bound.  Pin
            # both the reviewed replacement and the rest of the module so a
            # callback/writer-path edit still invalidates this guard.
            assert expected == (
                "60c47a9d69586d32c26483d92265a90acce24f430278c7e1632f8189d360dc01"
            )
            expected = (
                "48c9e60e7108d7da84cb57af26ff80cd35ce759e4dbfa558411867168a2c98b2"
            )
            tree = ast.parse(path.read_bytes())
            policy_class = next(
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "PathStoragePolicy"
            )
            assert hashlib.sha256(
                ast.dump(policy_class, include_attributes=False).encode()
            ).hexdigest() == (
                "2d228fde3f32cacbbf38c8a89c73d4b457a95622b6bfbce3364885d8a30dc00d"
            )
            tree.body = [
                node
                for node in tree.body
                if not (
                    isinstance(node, ast.ClassDef) and node.name == "PathStoragePolicy"
                )
            ]
            assert hashlib.sha256(
                ast.dump(tree, include_attributes=False).encode()
            ).hexdigest() == (
                "1613c7672802d68fbbe2d07069f83ff88d8b8c96436d66cc5fb7a8d7ca09a929"
            )
        if field == "storage_maintenance_sha256":
            # Explicit post-measurement compatibility, not a new benchmark.
            # See 2026-09-08-intraday-due-work-execution.md. Only the offline
            # report-preservation function changed; keep the frozen receipt
            # and every callback/guard source hash untouched. The reviewed
            # d34bfffe CLI stdout isolation is also included below; it changes
            # no storage function. Future edits must fail these exact pins.
            assert expected == (
                "cc72b533aed4081283ed1cb4d48e50239b13215e3c828bc98139d3bcb7325f9f"
            )
            expected = (
                "438923f08fe3e5d1aa7750d3506cf5341417b7f8986ac195d5e3733584e97dde"
            )
            tree = ast.parse(path.read_bytes())
            tree.body = [
                node
                for node in tree.body
                if not (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "maintain_report_artifact_storage"
                )
            ]
            unchanged_source = ast.dump(tree, include_attributes=False).encode()
            assert hashlib.sha256(unchanged_source).hexdigest() == (
                "627c2468c88e88b7a8fed30d08b0a4cccfa2704185e994b130acaf5935216a8d"
            )
        if field == "forward_collector_sha256":
            # 2026-09-10 additive rejection-clock diagnostics; original
            # measured guard remains frozen. Current 25k valid callbacks and
            # rejected 0B/0D measurements include the final invalid-clock fix.
            # See the separate 10:50 code review and source-bound receipt.
            assert expected == (
                "3ed07ede82cc21930f79206398b50e15d8f5242b0464b9b4d88364347f9dfd70"
            )
            expected = (
                "7f63c64aa7f2d3feb6da814d4dcbfda3dae25be8f22a8b96c92b7df58a8f7df4"
            )
        if field == "kiwoom_websocket_sha256":
            # Preserve the frozen measurement. The 2026-09-10 compatibility
            # review covers the already-reviewed deferred REG/auction changes
            # and additive packet-clock telemetry. Future edits still fail
            # this exact byte pin; no runtime guard is loosened here.
            assert expected == (
                "e33771db11090766c613436c98b1e0e9fbed7663fcebf3663fd633612ad0c052"
            )
            expected = (
                "f2165af17dae160535ddd5ac6ef5a5406eaf1bc8bacf423c3f475ceb514ba15c"
            )
        _assert_frozen_source_or_reviewed_mount(path, expected)


def test_packet_diagnostic_measurement_keeps_existing_latency_limits() -> None:
    evidence = json.loads(
        (
            Path(__file__).resolve().parents[2] / "docs/audit-reports/"
            "2026-09-10-micro-packet-review-latency-validation.json.txt"
        ).read_text()
    )
    assert evidence["runtime_guard_changed"] is False
    assert evidence["summary"]["queue_drop_count"] == 0
    assert evidence["summary"]["worker_error_count"] == 0
    assert evidence["summary"]["observer_on_internal_p95_ms_max"] < 1.0
    assert evidence["summary"]["observer_on_internal_p99_ms_max"] < 2.0
    import hashlib

    root = Path(__file__).resolve().parents[2]
    for source, expected_hash in evidence["source_hashes"].items():
        _assert_frozen_source_or_reviewed_mount(root / source, expected_hash)
    for kind, prefix in (
        ("0B", "producer_callback_latency"),
        ("0D", "producer_0d_callback_latency"),
    ):
        rejected = evidence["rejected_validation"][kind]
        assert rejected["timestamp_rejection_sample_total"] == 5000
        assert rejected["tail_size"] == 64
        assert rejected["latency"][prefix + "_p95_ms"] < 1.0
        assert rejected["latency"][prefix + "_p99_ms"] < 2.0
        assert rejected["packet_to_normalization_ms"] == 12000


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
