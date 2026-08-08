import ast
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.scalping.micro_reversion.detector import DetectorConfig
from src.engine.scalping.micro_reversion.forward_collector import (
    ForwardCollectorConfig,
    ForwardObservationCollector,
    ProducerCanaryResult,
    build_forward_collector_from_env,
)
from src.engine.scalping.micro_reversion.multi_horizon import (
    MultiHorizonConfig,
    MultiHorizonShockDetector,
)
from src.engine.scalping.micro_reversion.observation_adapter import (
    ObserverFeatureFlags,
)


def _snapshot(
    *,
    item: str = "000001",
    venue: str = "KRX",
    exchange_time: str = "090000000",
    received_at_ms: int | None = None,
    price: int = 10_000,
) -> dict:
    if received_at_ms is None:
        received_at_ms = int(
            datetime.fromisoformat("2026-08-08T09:00:00.010+09:00").timestamp() * 1_000
        )
    return {
        "last_ws_item": item,
        "last_realtime_type_item": {"0B": item},
        "last_realtime_type_effective_venue": {"0B": venue},
        "last_trade_tick": {
            "exchange_time_raw": exchange_time,
            "exchange_code_9081": "1",
            "received_at_ms": received_at_ms,
            "price": price,
            "volume": 10,
            "best_bid": price - 10,
            "best_ask": price + 10,
            "quote_age_ms": 10.0,
            "aggressor_side": "SELL",
        },
    }


def _collector(
    tmp_path: Path,
    *,
    path_capture_enabled: bool = False,
    detector: MultiHorizonShockDetector | None = None,
    queue_size: int = 16,
    manual_excluded_symbols: tuple[str, ...] = (),
) -> ForwardObservationCollector:
    collector = ForwardObservationCollector(
        flags=ObserverFeatureFlags(
            observer_enabled=True,
            path_capture_enabled=path_capture_enabled,
        ),
        config=ForwardCollectorConfig(
            output_root=tmp_path,
            observation_queue_size=queue_size,
            path_queue_size=16,
            path_batch_size=4,
            writer_flush_interval_sec=0.01,
            worker_poll_interval_sec=0.01,
        ),
        detector=detector,
        manual_excluded_symbols=manual_excluded_symbols,
    )
    collector.start()
    return collector


def test_factory_is_default_off_and_creates_no_output(tmp_path, monkeypatch) -> None:
    for name in (
        "SCALP_MICRO_REVERSION_OBSERVER_ENABLED",
        "SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED",
        "SCALP_MICRO_REVERSION_DISCOVERY_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SCALP_MICRO_REVERSION_PATH_ROOT", str(tmp_path))

    assert build_forward_collector_from_env() is None
    assert list(tmp_path.iterdir()) == []


def test_integrated_al_item_is_blocked_without_venue_guess(tmp_path) -> None:
    collector = _collector(tmp_path)
    try:
        result = collector.observe_kiwoom_0b(
            "000001",
            _snapshot(item="000001_AL", venue=""),
            realtime_type="0B",
        )
        snapshot = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
    assert snapshot.raw_exchange_code_9081_observed_count == 0
    assert snapshot.missing_or_conflicting_venue_count == 1


def test_0b_item_does_not_fall_back_to_generic_last_ws_item(tmp_path) -> None:
    collector = _collector(tmp_path)
    snapshot_payload = _snapshot()
    snapshot_payload["last_realtime_type_item"] = {}
    try:
        result = collector.observe_kiwoom_0b(
            "000001", snapshot_payload, realtime_type="0B"
        )
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MISSING_0B_ITEM
    assert runtime.missing_0b_item_count == 1


def test_manual_control_veto_precedes_queue_and_has_zero_leak(tmp_path) -> None:
    collector = _collector(
        tmp_path,
        manual_excluded_symbols=("000001",),
    )
    try:
        result = collector.observe_kiwoom_0b(
            "000001", _snapshot(price=-1), realtime_type="0B"
        )
        snapshot = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MANUAL_CONTROL_EXCLUDED
    assert snapshot.enqueued_count == 0
    assert snapshot.manual_control_excluded_count == 1
    assert snapshot.manual_control_event_leak_count == 0
    assert collector._source_sequences == {}
    assert collector._detector_clock_ms == {}


def test_dynamic_manual_exclusion_purges_state_and_drops_queued_envelope(
    tmp_path,
) -> None:
    collector = _collector(tmp_path, manual_excluded_symbols=())
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().worker_processed_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)

    collector._manual_refresh_lock.acquire()
    try:
        assert (
            collector.observe_kiwoom_0b(
                "000001",
                _snapshot(
                    exchange_time="090001000",
                    received_at_ms=(
                        int(
                            datetime.fromisoformat(
                                "2026-08-08T09:00:01.010+09:00"
                            ).timestamp()
                            * 1_000
                        )
                    ),
                ),
                realtime_type="0B",
            )
            is ProducerCanaryResult.ENQUEUED
        )
        assert collector.refresh_manual_exclusions(("000001",)) == ("000001",)
    finally:
        collector._manual_refresh_lock.release()

    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().manual_control_post_exclusion_envelope_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    runtime = collector.runtime_snapshot()
    collector.close()

    assert runtime.manual_control_new_exclusion_count == 1
    assert runtime.manual_control_state_purge_count >= 1
    assert runtime.manual_control_post_exclusion_envelope_count == 1
    assert runtime.manual_control_event_leak_count == 0
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.DISABLED
    )


def test_future_skew_is_bounded_and_stale_trade_time_is_blocked(tmp_path) -> None:
    collector = _collector(tmp_path)
    received_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:00+09:00").timestamp() * 1_000
    )
    try:
        adjusted = collector.observe_kiwoom_0b(
            "000001",
            _snapshot(exchange_time="090000500", received_at_ms=received_ms),
            realtime_type="0B",
        )
        stale = collector.observe_kiwoom_0b(
            "000001",
            _snapshot(exchange_time="085900000", received_at_ms=received_ms),
            realtime_type="0B",
        )
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert adjusted is ProducerCanaryResult.ENQUEUED
    assert stale is ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
    assert runtime.future_exchange_timestamp_adjustment_count == 1
    assert runtime.stale_exchange_timestamp_block_count == 1


def test_worker_refreshes_file_backed_manual_exclusions_off_producer_path(
    tmp_path, monkeypatch
) -> None:
    configured = set()
    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.observation_adapter."
        "configured_manual_control_exclusion_codes",
        lambda: frozenset(configured),
    )
    collector = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(
            output_root=tmp_path,
            worker_poll_interval_sec=0.005,
            manual_exclusion_refresh_interval_sec=0.01,
        ),
    )
    collector.start()
    configured.add("000001")
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().manual_control_new_exclusion_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    try:
        result = collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MANUAL_CONTROL_EXCLUDED
    assert runtime.manual_control_refresh_count >= 1
    assert runtime.manual_control_new_exclusion_count == 1
    assert runtime.manual_control_event_leak_count == 0


def test_observation_queue_full_is_nonblocking_and_counted(tmp_path) -> None:
    collector = _collector(tmp_path, queue_size=1)
    entered = threading.Event()
    release = threading.Event()

    def blocked_process(_envelope) -> None:
        entered.set()
        release.wait(timeout=2)

    collector._process_envelope = blocked_process
    try:
        assert (
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
            is ProducerCanaryResult.ENQUEUED
        )
        assert entered.wait(timeout=1)
        assert (
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
            is ProducerCanaryResult.ENQUEUED
        )
        started = time.perf_counter()
        assert (
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
            is ProducerCanaryResult.QUEUE_FULL
        )
        assert time.perf_counter() - started < 0.1
        snapshot = collector.runtime_snapshot()
    finally:
        release.set()
        collector.close()

    assert snapshot.observation_queue_full_count == 1
    assert snapshot.observation_dropped_envelope_count == 1


def test_series_gap_attributes_queue_and_invalid_envelope_losses(tmp_path) -> None:
    collector = _collector(tmp_path, queue_size=1)
    entered = threading.Event()
    release = threading.Event()
    original_process = collector._process_envelope

    def block_first(envelope) -> None:
        if not entered.is_set():
            entered.set()
            release.wait(timeout=2)
        original_process(envelope)

    collector._process_envelope = block_first
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    assert entered.wait(timeout=1)
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.QUEUE_FULL
    )
    release.set()
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().worker_processed_count < 2
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().worker_processed_count < 3
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    runtime = collector.runtime_snapshot()
    collector.close()

    assert runtime.series_with_gap_count == 1
    assert runtime.queue_drop_explained_gap_count == 1
    assert runtime.unexplained_sequence_gap_count == 0

    invalid_collector = _collector(tmp_path / "invalid")
    invalid_payload = _snapshot(price=-1)
    invalid_payload["last_trade_tick"]["best_bid"] = None
    invalid_payload["last_trade_tick"]["best_ask"] = None
    assert (
        invalid_collector.observe_kiwoom_0b(
            "000002",
            invalid_payload,
            realtime_type="0B",
        )
        is ProducerCanaryResult.INVALID_ENVELOPE
    )
    assert (
        invalid_collector.observe_kiwoom_0b("000002", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    deadline = time.monotonic() + 1
    while (
        invalid_collector.runtime_snapshot().worker_processed_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    invalid_runtime = invalid_collector.runtime_snapshot()
    invalid_collector.close()

    assert invalid_runtime.invalid_envelope_explained_gap_count == 1
    assert invalid_runtime.unexplained_sequence_gap_count == 0


def test_collector_close_attempts_every_writer_after_worker_timeout(tmp_path) -> None:
    collector = _collector(tmp_path)
    entered = threading.Event()
    release = threading.Event()

    def blocked_process(_envelope) -> None:
        entered.set()
        release.wait(timeout=2)

    class RecordingWriter:
        def __init__(self, *, fail: bool = False) -> None:
            self.closed = False
            self.fail = fail

        def close(self, *, timeout_sec: float) -> None:
            self.closed = True
            if self.fail:
                raise OSError("synthetic writer close failure")

    first_writer = RecordingWriter(fail=True)
    second_writer = RecordingWriter()
    collector._process_envelope = blocked_process
    collector._writers[("2026-08-08", "KRX", "KRX_REGULAR")] = first_writer
    collector._writers[("2026-08-08", "NXT", "NXT_REGULAR_OVERLAP")] = second_writer
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    assert entered.wait(timeout=1)

    with pytest.raises(RuntimeError, match="shutdown had 2 error"):
        collector.close(timeout_sec=0.01)
    assert first_writer.closed is True
    assert second_writer.closed is True
    release.set()
    with pytest.raises(RuntimeError, match="one-shot"):
        collector.start()


def test_forward_path_capture_persists_event_and_separates_authority(
    tmp_path,
) -> None:
    detector = MultiHorizonShockDetector(
        MultiHorizonConfig(
            horizons_ms=(1_000,),
            detector_base=DetectorConfig(
                return_window_ms=1_000,
                reference_max_lag_ms=2_000,
                min_robust_history=3,
                absolute_shock_bps=-10.0,
                cooldown_ms=0,
            ),
        )
    )
    collector = _collector(
        tmp_path,
        path_capture_enabled=True,
        detector=detector,
    )
    base_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:00.010+09:00").timestamp() * 1_000
    )
    assert (
        collector.observe_kiwoom_0b(
            "000001",
            _snapshot(received_at_ms=base_ms),
            realtime_type="0B",
        )
        is ProducerCanaryResult.ENQUEUED
    )
    assert (
        collector.observe_kiwoom_0b(
            "000001",
            _snapshot(
                exchange_time="090001000",
                received_at_ms=base_ms + 1_000,
                price=9_800,
            ),
            realtime_type="0B",
        )
        is ProducerCanaryResult.ENQUEUED
    )
    deadline = time.monotonic() + 2
    while (
        collector.runtime_snapshot().shock_event_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    collector.close()
    snapshot = collector.runtime_snapshot()

    path_files = list(tmp_path.rglob("market_path.jsonl"))
    reference_files = list(tmp_path.rglob("event_references.jsonl"))
    assert len(path_files) == 1
    assert len(reference_files) == 1
    assert path_files[0].read_text(encoding="utf-8").strip()
    assert reference_files[0].read_text(encoding="utf-8").strip()
    assert snapshot.shock_event_count == 1
    assert snapshot.writer_persisted_envelope_count >= 1
    assert snapshot.writer_bytes_per_persisted_envelope > 0
    assert snapshot.writer_bytes_by_trade_date["2026-08-08"] > 0
    assert snapshot.writer_last_error_types == ()
    assert snapshot.event_reference_coverage_pct == 100.0
    assert snapshot.orphan_reference_count == 0
    assert snapshot.unreferenced_segment_count == 0
    assert snapshot.reference_reconciliation_error_count == 0
    assert snapshot.reference_reconciliation_completed is True
    assert snapshot.event_reference_write_latency_p95_ms > 0
    assert (
        snapshot.writer_last_persisted_sequence_by_series["000001|KRX|KRX_REGULAR"][
            "series_sequence"
        ]
        >= 1
    )
    assert snapshot.observer_runtime_effect is False
    assert snapshot.trading_runtime_effect is False
    assert snapshot.trading_decision_effect is False
    assert snapshot.sim_position_effect is False
    assert snapshot.threshold_effect is False
    assert snapshot.broker_effect is False
    assert snapshot.actual_order_submitted is False


def test_detector_clock_adjustment_is_measured(tmp_path) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    received_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:00.010+09:00").timestamp() * 1_000
    )
    for _ in range(2):
        assert (
            collector.observe_kiwoom_0b(
                "000001",
                _snapshot(received_at_ms=received_ms),
                realtime_type="0B",
            )
            is ProducerCanaryResult.ENQUEUED
        )
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().worker_processed_count < 2
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    runtime = collector.runtime_snapshot()
    collector.close()

    assert runtime.detector_clock_adjustment_count == 1
    assert runtime.detector_clock_adjustment_max_ms == 1


def test_shutdown_reconciliation_detects_orphan_and_unreferenced_segments(
    tmp_path,
) -> None:
    collector = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
        manual_excluded_symbols=(),
    )
    key = ("2026-08-08", "KRX", "KRX_REGULAR")
    path = collector.config.storage_policy.partition_path(
        tmp_path,
        trade_date=key[0],
        venue=key[1],
        session_bucket=key[2],
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"path_segment_id": "segment-path"}) + "\n")
    path.with_name("event_references.jsonl").write_text(
        json.dumps({"path_segment_id": "segment-reference"}) + "\n"
    )
    collector._reference_partitions.add(key)

    collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.reference_reconciliation_completed is True
    assert runtime.event_reference_coverage_pct == 0.0
    assert runtime.orphan_reference_count == 1
    assert runtime.unreferenced_segment_count == 1


def test_ws_producer_hook_isolates_collector_failure(monkeypatch) -> None:
    class BrokenCollector:
        def observe_kiwoom_0b(self, *_args, **_kwargs):
            raise OSError("synthetic observer failure")

    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector = BrokenCollector()
    monkeypatch.setattr(
        "src.engine.kiwoom_websocket.observe_raw_market_data",
        lambda *_args, **_kwargs: None,
    )

    manager._queue_tick_event("000001", _snapshot(), realtime_type="0B")

    assert "000001" in manager._pending_tick_events
    assert manager._micro_reversion_forward_collector_error == "OSError"


def test_ws_producer_integration_remains_default_off(monkeypatch) -> None:
    monkeypatch.delenv("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")

    manager._start_micro_reversion_forward_collector()
    snapshot = manager.micro_reversion_forward_collector_snapshot()

    assert manager._micro_reversion_forward_collector is None
    assert snapshot["observer_runtime_loaded"] is False
    assert snapshot["observer_runtime_effect"] is False
    assert snapshot["trading_runtime_effect"] is False
    assert snapshot["actual_order_submitted"] is False


def test_forward_collector_has_no_forbidden_runtime_imports() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "engine"
        / "scalping"
        / "micro_reversion"
        / "forward_collector.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")

    forbidden_fragments = ("broker", "order", "execution", "ai", "adm", "ldm")
    assert not any(
        fragment in module_name.lower()
        for module_name in imported
        for fragment in forbidden_fragments
    )
