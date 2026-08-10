from src.engine.scalping.micro_reversion.observation_adapter import (
    AdapterResult,
    BoundedObservationQueue,
    ObservationAdapter,
    ObserverFeatureFlags,
)


def _fields(**overrides):
    values = {
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "exchange_timestamp": "2026-08-08T09:00:00+09:00",
        "local_receive_timestamp": "2026-08-08T09:00:00.010+09:00",
        "source_sequence": 1,
        "sequence_epoch": 1,
        "realtime_type": "0B",
        "trade_price": 10_000,
        "trade_qty": 10,
    }
    values.update(overrides)
    values["series_sequence"] = overrides.get(
        "series_sequence", values["source_sequence"]
    )
    return values


def test_feature_flags_default_to_all_disabled(monkeypatch) -> None:
    for name in (
        "SCALP_MICRO_REVERSION_OBSERVER_ENABLED",
        "SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED",
        "SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED",
        "SCALP_MICRO_REVERSION_DISCOVERY_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)

    flags = ObserverFeatureFlags.from_env()

    assert flags.observer_enabled is False
    assert flags.observation_capture_active is False
    assert flags.authority_dict()["trading_decision_effect"] is False


def test_adapter_only_enqueues_immutable_envelope_when_enabled() -> None:
    sink = BoundedObservationQueue(maxsize=1)
    adapter = ObservationAdapter(
        sink,
        flags=ObserverFeatureFlags(observer_enabled=True),
        queue_depth=sink.qsize,
    )

    assert adapter.observe(**_fields()) is AdapterResult.ENQUEUED
    envelope = sink.get(timeout=0.01)
    assert envelope.symbol == "000001"
    assert envelope.trade_price == 10_000
    assert adapter.observe(**_fields(source_sequence=2)) is AdapterResult.ENQUEUED
    assert adapter.observe(**_fields(source_sequence=3)) is AdapterResult.QUEUE_FULL

    snapshot = adapter.runtime_snapshot()
    assert snapshot.queue_high_water == 1
    assert snapshot.queue_full_count == 1
    assert snapshot.dropped_envelope_count == 1
    assert snapshot.actual_order_submitted is False
    assert snapshot.observer_runtime_loaded is True
    assert snapshot.observation_capture_active is False
    assert snapshot.exchange_to_receive_latency_p95_ms == 10.0


def test_adapter_has_no_manual_control_classification_contract() -> None:
    sink = BoundedObservationQueue(maxsize=1)
    adapter = ObservationAdapter(
        sink,
        flags=ObserverFeatureFlags(observer_enabled=True),
    )

    result = adapter.observe(**_fields())

    assert result is AdapterResult.ENQUEUED
    assert "manual_control_excluded" not in sink.get(timeout=0.01).as_dict()


def test_adapter_isolates_sink_failure() -> None:
    class BrokenSink:
        def put_nowait(self, _envelope):
            raise OSError("synthetic failure")

    adapter = ObservationAdapter(
        BrokenSink(),
        flags=ObserverFeatureFlags(observer_enabled=True),
    )

    assert adapter.observe(**_fields()) is AdapterResult.ISOLATED_ERROR
    assert adapter.runtime_snapshot().isolated_error_count == 1
