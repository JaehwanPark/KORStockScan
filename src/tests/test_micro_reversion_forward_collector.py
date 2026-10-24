import ast
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.scalping.micro_reversion import forward_collector as collector_module
from src.engine.scalping.micro_reversion.detector import DetectorConfig
from src.engine.scalping.micro_reversion.forward_collector import (
    CollectorLifecycle,
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


def _depth_snapshot(
    *,
    item: str = "000001",
    venue: str = "KRX",
    orderbook_time: str = "090000000",
    received_at_ms: int | None = None,
) -> dict:
    if received_at_ms is None:
        received_at_ms = int(
            datetime.fromisoformat("2026-08-08T09:00:00.010+09:00").timestamp() * 1_000
        )
    return {
        "last_realtime_type_item": {"0D": item},
        "last_realtime_type_effective_venue": {"0D": venue},
        "last_depth_tick": {
            "item": item,
            "orderbook_time_raw": orderbook_time,
            "received_at_ms": received_at_ms,
            "ask_levels": [
                {"level": 1, "price": 10_010, "quantity": 100},
                {"level": 2, "price": 10_020, "quantity": 200},
            ],
            "bid_levels": [
                {"level": 1, "price": 10_000, "quantity": 150},
                {"level": 2, "price": 9_990, "quantity": 250},
            ],
            "ask_depth": 300,
            "bid_depth": 400,
            "route_depth_totals": {
                "combined": {"ask": 300, "bid": 400},
                "KRX": {"ask": 300, "bid": 400},
                "NXT": {"ask": 0, "bid": 0},
            },
        },
    }


def _collector(
    tmp_path: Path,
    *,
    path_capture_enabled: bool = False,
    detector: MultiHorizonShockDetector | None = None,
    queue_size: int = 16,
    depth_capture_enabled: bool = False,
) -> ForwardObservationCollector:
    collector = ForwardObservationCollector(
        flags=ObserverFeatureFlags(
            observer_enabled=True,
            path_capture_enabled=path_capture_enabled,
            depth_capture_enabled=depth_capture_enabled,
        ),
        config=ForwardCollectorConfig(
            output_root=tmp_path,
            observation_queue_size=queue_size,
            path_queue_size=16,
            depth_queue_size=16,
            path_batch_size=4,
            writer_flush_interval_sec=0.01,
            worker_poll_interval_sec=0.01,
        ),
        detector=detector or MultiHorizonShockDetector(),
    )
    collector.start()
    return collector


def _raw_rejected_depth(
    monkeypatch, *, missing_total=False, crossed=False, malformed=False
):
    at = datetime.fromisoformat("2026-10-23T16:00:38.260+09:00").timestamp()
    monkeypatch.setattr("src.engine.kiwoom_websocket.time.time", lambda: at)
    values = {
        "21": "160038",
        "41": "+10010",
        "61": "100",
        "51": "+10000",
        "71": "150",
        "121": "100",
        "125": "150",
        "6064": "100",
        "6065": "150",
        "6086": "0",
        "6087": "0",
        "not_market_data": "excluded",
    }
    if missing_total:
        values.pop("121")
    if crossed:
        values["41"] = "+9990"
    if malformed:
        values["61"] = "unavailable"
    depth = KiwoomWSManager._build_micro_reversion_depth_tick("196170_AL", values)
    depth.update(transport_epoch=123, route_sequence=7)
    return (
        dict(
            last_realtime_type_item={"0D": "196170_AL"},
            last_realtime_type_effective_venue={"0D": "SOR"},
            last_depth_tick=depth,
            micro_observer_packet_receive_time_source="websocket_packet_ingress",
            micro_observer_packet_received_at_ms=int(at * 1000) - 2,
        ),
        values,
    )


@pytest.mark.parametrize("case", ["missing_total", "crossed", "malformed"])
def test_depth_rejection_preserves_raw_fields_through_existing_worker_and_reader(
    tmp_path, monkeypatch, case
):
    from src.engine.scalping.micro_reversion.canary_monitor import (
        normalization_source_quality_census,
        evaluate_canary_snapshot,
        load_canary_guard,
    )

    snapshot, raw = _raw_rejected_depth(monkeypatch, **{case: True})
    c = _collector(tmp_path, depth_capture_enabled=True)
    try:
        assert (
            c.observe_kiwoom_0d("196170", snapshot, realtime_type="0D")
            == ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
        )
        # This is a copied source receipt, not a pointer into mutable WS state.
        snapshot["last_depth_tick"]["raw_depth_fields"]["41"] = "changed later"
    finally:
        c.close()
    state = c.runtime_snapshot().as_dict()
    ledger = state["normalization_rejection_ledger"]
    assert ledger["seen"] == ledger["rows"] == 1
    assert ledger["complete"] and ledger["sealed"]
    row = json.loads(Path(ledger["path"]).read_text())
    assert row["raw_fields"] == {k: v for k, v in raw.items() if k != "not_market_data"}
    assert row["packet_received_at_ms"] == row["normalization_received_at_ms"] - 2
    assert row["route_sequence"] == 7 and row["transport_epoch"] == 123
    assert (
        row["reason"]
        == {
            "missing_total": "depth_fields_invalid",
            "crossed": "depth_bbo_crossed",
            "malformed": "depth_side_empty",
        }[case]
    )
    assert state["depth_enqueued_count"] == 0
    verified = normalization_source_quality_census(state)
    assert verified["status"] == "verified" and verified["complete"]
    assert verified["rejected_quotes_eligible"] is False
    assert (
        evaluate_canary_snapshot(state, load_canary_guard())[
            "normalization_source_quality"
        ]
        == verified
    )


@pytest.mark.parametrize(
    "damage",
    [
        "hash",
        "pid",
        "epoch",
        "counter",
        "partial",
        "authority",
        "symlink",
        "budget",
        "missing_raw",
        "raw_too_long",
        "packet_clock",
        "ingress_claim",
        "incomplete_count",
    ],
)
def test_depth_rejection_custody_fails_closed_or_reports_partial(
    tmp_path, monkeypatch, damage
):
    import hashlib
    from src.engine.scalping.micro_reversion.canary_monitor import (
        normalization_source_quality_census,
    )

    snapshot, _ = _raw_rejected_depth(monkeypatch, missing_total=True)
    if damage == "missing_raw":
        snapshot["last_depth_tick"].pop("raw_depth_fields")
    if damage == "raw_too_long":
        snapshot["last_depth_tick"]["raw_depth_fields"]["41"] = "0" * 10000
    if damage == "packet_clock":
        snapshot["micro_observer_packet_received_at_ms"] += 100000
    c = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True, depth_capture_enabled=True),
        config=ForwardCollectorConfig(
            output_root=tmp_path,
            normalization_evidence_max_bytes=(
                1 if damage == "budget" else 4 * 1024 * 1024
            ),
        ),
    )
    c.start()
    try:
        c.observe_kiwoom_0d("196170", snapshot, realtime_type="0D")
    finally:
        c.close()
    state = c.runtime_snapshot().as_dict()
    ledger = state["normalization_rejection_ledger"]
    path = Path(ledger["path"])
    if damage in {"pid", "epoch", "authority"}:
        row = json.loads(path.read_text())
        if damage == "pid":
            row["process_pid"] += 1
        if damage == "epoch":
            row["local_observer_epoch"] += 1
        if damage == "authority":
            row["actual_order_submitted"] = True
        raw = (json.dumps(row) + "\n").encode()
        path.write_bytes(raw)
        ledger.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if damage == "hash":
        ledger["sha256"] = "0" * 64
    if damage == "counter":
        ledger["seen"] += 1
    if damage == "ingress_claim":
        ledger["ingress_complete"] = False
    if damage == "incomplete_count":
        ledger["incomplete_raw"] = ledger["seen"] + 1
    if damage == "partial":
        path.write_bytes(path.read_bytes()[:-1])
    if damage == "symlink":
        other = path.with_suffix(".original")
        path.rename(other)
        path.symlink_to(other)
    result = normalization_source_quality_census(state)
    if damage in {"budget", "missing_raw", "raw_too_long", "packet_clock"}:
        assert result["status"] == "partial" and not result["complete"]
        assert ledger["bytes"] <= ledger["max_bytes"]
    else:
        assert result["status"] == "invalid" and not result["complete"]


@pytest.mark.parametrize("failure", ["queue", "write", "fsync"])
def test_depth_rejection_write_failure_cannot_seal_clean_shutdown(
    tmp_path, monkeypatch, failure
):
    import queue

    snapshot, _ = _raw_rejected_depth(monkeypatch, missing_total=True)
    c = _collector(tmp_path, depth_capture_enabled=True)
    if failure == "queue":

        def full(_):
            raise queue.Full

        monkeypatch.setattr(c._normalization_queue, "put_nowait", full)
    elif failure == "write":
        p = c._normalization["path"]
        p.parent.mkdir()
        p.write_text("original foreign evidence")
    else:

        def failed(_):
            raise OSError("offline fsync failure")

        monkeypatch.setattr(collector_module.os, "fsync", failed)
    c.observe_kiwoom_0d("196170", snapshot, realtime_type="0D")
    with pytest.raises(RuntimeError, match="shutdown"):
        c.close()
    assert not c.runtime_snapshot().normalization_rejection_ledger["sealed"]
    if c._normalization["file"] is not None:
        c._normalization["file"].close()


def test_normalization_evidence_bounds_rejections_without_changing_valid_depth(
    tmp_path, monkeypatch
):
    from src.engine.scalping.micro_reversion.canary_monitor import (
        normalization_source_quality_census,
    )

    rejected, _ = _raw_rejected_depth(monkeypatch, missing_total=True)
    valid, _ = _raw_rejected_depth(monkeypatch)
    c = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True, depth_capture_enabled=True),
        config=ForwardCollectorConfig(
            output_root=tmp_path,
            path_batch_size=256,
            depth_queue_size=1000,
            normalization_evidence_max_bytes=4096,
        ),
    )
    c.start()
    try:
        for _ in range(98):
            assert (
                c.observe_kiwoom_0d("196170", rejected, realtime_type="0D")
                == ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
            )
        assert (
            c.observe_kiwoom_0d("196170", valid, realtime_type="0D")
            == ProducerCanaryResult.ENQUEUED
        )
    finally:
        c.close()
    state = c.runtime_snapshot().as_dict()
    ledger = state["normalization_rejection_ledger"]
    assert state["depth_enqueued_count"] == state["depth_worker_processed_count"] == 1
    assert ledger["seen"] == 98 and ledger["rows"] + ledger["omitted"] == 98
    assert 0 < ledger["bytes"] <= 4096 and ledger["omitted"] > 0
    assert normalization_source_quality_census(state)["status"] == "partial"


def test_factory_is_default_off_and_creates_no_output(tmp_path, monkeypatch) -> None:
    for name in (
        "SCALP_MICRO_REVERSION_OBSERVER_ENABLED",
        "SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED",
        "SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED",
        "SCALP_MICRO_REVERSION_DISCOVERY_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SCALP_MICRO_REVERSION_PATH_ROOT", str(tmp_path))

    assert build_forward_collector_from_env() is None
    assert list(tmp_path.iterdir()) == []


def test_timestamp_rejection_tail_is_bounded_and_keeps_route_epoch(tmp_path) -> None:
    collector = _collector(tmp_path, depth_capture_enabled=True, queue_size=128)
    received = int(
        datetime.fromisoformat("2026-08-08T09:00:20+09:00").timestamp() * 1000
    )
    try:
        for _ in range(70):
            assert (
                collector.observe_kiwoom_0b(
                    "000001", _snapshot(received_at_ms=received), realtime_type="0B"
                )
                == ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
            )
        old_epoch = collector.runtime_snapshot().sequence_epoch
        new_epoch = collector.begin_transport_epoch()
        assert (
            collector.observe_kiwoom_0d(
                "000001",
                _depth_snapshot(item="000001_NX", venue="NXT", received_at_ms=received),
                realtime_type="0D",
            )
            == ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
        )
        assert (
            collector.observe_kiwoom_0b(
                "000001", _snapshot(exchange_time="invalid"), realtime_type="0B"
            )
            == ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
        )
        snapshot = collector.runtime_snapshot().as_dict()
        rows = snapshot["timestamp_rejection_samples"]
        assert snapshot["timestamp_rejection_sample_total"] == 72
        assert len(rows) == 64
        assert rows[0]["rejection_index"] == 9
        assert rows[0]["local_observer_epoch"] == old_epoch
        assert rows[-2]["local_observer_epoch"] == new_epoch
        assert rows[-2]["realtime_type"] == "0D"
        assert rows[-2]["item"] == "000001_NX"
        assert rows[-2]["venue"] == "NXT"
        assert rows[-2]["session_bucket"] == "NXT_REGULAR_OVERLAP"
        assert rows[-2]["process_pid"] > 0
        assert rows[-2]["exchange_to_receive_lag_ms"] == 20_000
        assert rows[-2]["maximum_exchange_to_receive_lag_ms"] == 10_000
        assert rows[-1]["raw_exchange_time"] is None
        assert rows[-1]["reason"] == "invalid_or_future_timestamp"
        assert rows[-1]["session_bucket"] is None
        assert snapshot["enqueued_count"] == snapshot["depth_enqueued_count"] == 0
        assert snapshot["actual_order_submitted"] is False
        assert (
            snapshot["metric_contracts"]["timestamp_rejection"]["decision_authority"]
            == "source_observation_only"
        )
    finally:
        collector.close()


@pytest.mark.parametrize("realtime_type", ["0B", "0D"])
@pytest.mark.parametrize(
    "packet_case",
    [
        "trusted",
        "missing",
        "untrusted",
        "future",
        "infinite",
        "nan",
        "malformed",
        "boolean",
        "fractional",
        "numeric_string",
    ],
)
def test_rejection_separates_packet_ingress_from_normalization(
    tmp_path, realtime_type, packet_case
):
    collector = _collector(tmp_path, depth_capture_enabled=True)
    received = int(
        datetime.fromisoformat("2026-08-08T09:00:20+09:00").timestamp() * 1000
    )
    snapshot = (
        _snapshot(received_at_ms=received)
        if realtime_type == "0B"
        else _depth_snapshot(received_at_ms=received)
    )
    if packet_case != "missing":
        snapshot["micro_observer_packet_received_at_ms"] = (
            received + 1 if packet_case == "future" else received - 12000
        )
        if packet_case in {
            "infinite",
            "nan",
            "malformed",
            "boolean",
            "fractional",
            "numeric_string",
        }:
            snapshot["micro_observer_packet_received_at_ms"] = {
                "infinite": float("inf"),
                "nan": float("nan"),
                "malformed": "bad-clock",
                "boolean": True,
                "fractional": received - 12000.5,
                "numeric_string": str(received - 12000),
            }[packet_case]
        snapshot["micro_observer_packet_receive_time_source"] = (
            "unknown" if packet_case == "untrusted" else "websocket_packet_ingress"
        )
    try:
        observe = getattr(collector, "observe_kiwoom_" + realtime_type.lower())
        assert observe("000001", snapshot, realtime_type=realtime_type) == (
            ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
        )
        row = collector.runtime_snapshot().timestamp_rejection_samples[-1]
        assert row["exchange_to_receive_lag_ms"] == 20000
        assert row["maximum_exchange_to_receive_lag_ms"] == 10000
        assert row["packet_to_normalization_ms"] == (
            12000 if packet_case == "trusted" else None
        )
        assert row["exchange_to_packet_receive_lag_ms"] == (
            8000 if packet_case == "trusted" else None
        )
        assert row["packet_receive_provenance_status"] == (
            "trusted_packet_ingress"
            if packet_case == "trusted"
            else "missing_or_invalid"
        )
    finally:
        collector.close()


def test_missing_receive_time_is_not_reported_as_epoch_zero_latency(tmp_path):
    collector = _collector(tmp_path)
    snapshot = _snapshot()
    snapshot["last_trade_tick"]["received_at_ms"] = None
    try:
        assert (
            collector.observe_kiwoom_0b("000001", snapshot, realtime_type="0B")
            == ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
        )
        row = collector.runtime_snapshot().timestamp_rejection_samples[-1]
        assert row["received_at_ms"] is None
        assert row["exchange_to_receive_lag_ms"] is None
        assert row["receive_to_rejection_check_ms"] is None
    finally:
        collector.close()


def test_factory_resolves_default_output_from_repository_not_process_cwd(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", "true")
    monkeypatch.setenv("SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED", "true")
    monkeypatch.delenv("SCALP_MICRO_REVERSION_PATH_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    collector = build_forward_collector_from_env(start=False)

    assert collector is not None
    assert collector.config.output_root == (
        (Path(__file__).parents[2] / "data").resolve()
        / "observations/scalp_micro_reversion_forward"
    )
    assert collector.config.observation_queue_size == 50_000
    assert collector.config.depth_queue_size == 50_000


def test_release_shared_mount_captures_trade_and_depth_without_weakening_guard(
    tmp_path,
):
    import inspect

    release = tmp_path / "release"
    data = tmp_path / "state"
    release.mkdir()
    data.mkdir()
    (release / "data").symlink_to(data)
    tree = ast.parse(inspect.getsource(collector_module))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "DEFAULT_OUTPUT_ROOT"
            for target in node.targets
        )
    )
    root = eval(
        compile(ast.Expression(assignment.value), "collector", "eval"),
        {"REPOSITORY_ROOT": release},
    )
    assert root == data / "observations/scalp_micro_reversion_forward"
    collector = _collector(root, path_capture_enabled=True, depth_capture_enabled=True)
    try:
        assert (
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
            is ProducerCanaryResult.ENQUEUED
        )
        assert (
            collector.observe_kiwoom_0d("000001", _depth_snapshot(), realtime_type="0D")
            is ProducerCanaryResult.ENQUEUED
        )
    finally:
        collector.close()
    snapshot = collector.runtime_snapshot()
    assert snapshot.worker_error_count == snapshot.depth_worker_error_count == 0
    assert snapshot.worker_processed_count == snapshot.depth_worker_processed_count == 1
    assert list(root.rglob("market_stream.jsonl"))
    assert list(root.rglob("market_depth_stream.jsonl"))
    from src.engine.scalping.micro_reversion.path_journal import (
        _assert_no_symlink_ancestors,
    )

    child_link = root / "unsafe-child"
    child_link.symlink_to(data)
    with pytest.raises(OSError, match="ancestor symlink"):
        _assert_no_symlink_ancestors(child_link / "rows.jsonl")


def test_integrated_al_item_preserves_route_with_unknown_actual_venue(
    tmp_path,
) -> None:
    collector = _collector(tmp_path)
    payload = _snapshot(item="000001_AL", venue="", exchange_time="085959000")
    payload["last_realtime_type_market_route"] = {"0B": "krx_nxt_integrated"}
    payload["last_realtime_type_actual_execution_venue"] = {"0B": "UNKNOWN"}
    payload["last_trade_tick"]["exchange_code_9081"] = ""
    try:
        result = collector.observe_kiwoom_0b(
            "000001",
            payload,
            realtime_type="0B",
        )
        deadline = time.monotonic() + 1
        while (
            collector.runtime_snapshot().worker_processed_count < 1
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)
        snapshot = collector.runtime_snapshot()
        series_keys = set(collector._source_sequences)
    finally:
        collector.close()

    assert result is ProducerCanaryResult.ENQUEUED
    assert snapshot.enqueued_count == 1
    assert snapshot.worker_processed_count == 1
    assert snapshot.raw_exchange_code_9081_observed_count == 0
    assert snapshot.missing_or_conflicting_venue_count == 0
    assert ("000001", "SOR", "SOR_PREMARKET") in series_keys


@pytest.mark.parametrize(
    "route,actual_venue",
    [("nxt_only", "UNKNOWN"), ("krx_nxt_integrated", "NXT")],
)
def test_integrated_al_item_rejects_route_or_actual_venue_guess(
    tmp_path, route, actual_venue
) -> None:
    collector = _collector(tmp_path)
    payload = _snapshot(item="000001_AL", venue="", exchange_time="085959000")
    payload["last_realtime_type_market_route"] = {"0B": route}
    payload["last_realtime_type_actual_execution_venue"] = {"0B": actual_venue}
    try:
        result = collector.observe_kiwoom_0b(
            "000001",
            payload,
            realtime_type="0B",
        )
        snapshot = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
    assert snapshot.enqueued_count == 0
    assert snapshot.missing_or_conflicting_venue_count == 1


def test_integrated_al_item_blocks_conflicting_declared_exchange(tmp_path) -> None:
    collector = _collector(tmp_path)
    try:
        result = collector.observe_kiwoom_0b(
            "000001",
            _snapshot(item="000001_AL", venue="KRX"),
            realtime_type="0B",
        )
        snapshot = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
    assert snapshot.enqueued_count == 0
    assert snapshot.missing_or_conflicting_venue_count == 1


def test_realtime_item_symbol_must_match_callback_symbol(tmp_path) -> None:
    collector = _collector(tmp_path, depth_capture_enabled=True)
    depth_snapshot = _depth_snapshot()
    depth_snapshot["last_depth_tick"]["item"] = "999999"
    depth_snapshot["last_realtime_type_item"]["0D"] = "999999"
    try:
        trade_result = collector.observe_kiwoom_0b(
            "000001",
            _snapshot(item="999999", venue="KRX"),
            realtime_type="0B",
        )
        depth_result = collector.observe_kiwoom_0d(
            "000001",
            depth_snapshot,
            realtime_type="0D",
        )
    finally:
        collector.close()

    assert trade_result is ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE
    assert depth_result is ProducerCanaryResult.MISSING_OR_CONFLICTING_VENUE


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


def test_0d_depth_capture_uses_separate_journal_and_sequence(tmp_path) -> None:
    collector = _collector(
        tmp_path, path_capture_enabled=True, depth_capture_enabled=True
    )
    try:
        result = collector.observe_kiwoom_0d(
            "000001", _depth_snapshot(), realtime_type="0D"
        )
        deadline = time.monotonic() + 2
        while (
            collector.runtime_snapshot().depth_writer_persisted_envelope_count < 1
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
    finally:
        collector.close()
    runtime = collector.runtime_snapshot()
    depth_files = tuple(tmp_path.rglob("market_depth_stream.jsonl"))
    market_files = tuple(tmp_path.rglob("market_stream.jsonl"))

    assert result is ProducerCanaryResult.ENQUEUED
    assert runtime.producer_0d_callback_count == 1
    assert runtime.depth_enqueued_count == 1
    assert runtime.depth_worker_processed_count == 1
    assert runtime.depth_writer_persisted_envelope_count == 1
    assert len(depth_files) == 1
    assert market_files == ()
    row = json.loads(depth_files[0].read_text(encoding="utf-8").splitlines()[0])
    assert row["schema"] == "scalp_micro_reversion_market_depth_point_v1"
    assert row["realtime_type"] == "0D"
    assert row["bid_depth"] == 400
    assert row["ask_depth"] == 300
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True


def test_probe_terminal_trace_keeps_real_collector_rejections_and_admission(tmp_path):
    collector = _collector(
        tmp_path, path_capture_enabled=True, depth_capture_enabled=True
    )
    manager = KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 7
    manager._micro_reversion_forward_collector = collector
    good = _depth_snapshot()
    source = good["last_depth_tick"]
    source.update(transport_epoch=7, route_sequence=1, market_route="krx_only")
    manager._exact_probe_item_leases["000001"] = dict(
        lease_id="lease",
        epoch=7,
        interval_started_epoch=source["received_at_ms"] / 1000 - 1,
    )
    bad = {**good, "last_depth_tick": {**source, "ask_levels": []}}
    try:
        manager._observe_micro_reversion_forward("000001", bad, realtime_type="0D")
        source["route_sequence"] = 2
        manager._observe_micro_reversion_forward("000001", good, realtime_type="0D")
        trace = manager.exact_probe_source_trace("000001", "lease")
    finally:
        collector.close()
    counts = trace["lease"]["collector_result_counts_by_type"]["0D"]
    assert counts == {"invalid_depth_snapshot": 1, "enqueued": 1}
    assert (
        trace["lease"]["collector_first_non_enqueued_by_type"]["0D"]["route_sequence"]
        == 1
    )
    assert trace["lease"]["collector_last_result_by_type"]["0D"]["route_sequence"] == 2
    assert collector.runtime_snapshot().depth_writer_persisted_envelope_count == 1
    assert trace["broker_ack_observed"] is None
    assert trace["order_authority"] is False


def test_low_disk_warning_propagates_for_path_and_depth_without_capture_loss(
    tmp_path, monkeypatch
) -> None:
    low_but_not_critical_bytes = 4 * 1024 * 1024 * 1024
    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.path_journal."
        "NonBlockingPathJournalWriter._disk_free_space",
        lambda _writer: low_but_not_critical_bytes,
    )
    collector = _collector(
        tmp_path,
        path_capture_enabled=True,
        depth_capture_enabled=True,
    )
    try:
        assert (
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
            is ProducerCanaryResult.ENQUEUED
        )
        assert (
            collector.observe_kiwoom_0d("000001", _depth_snapshot(), realtime_type="0D")
            is ProducerCanaryResult.ENQUEUED
        )
    finally:
        collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.writer_persisted_envelope_count == 1
    assert runtime.depth_writer_persisted_envelope_count == 1
    assert runtime.writer_low_disk_watermark_breach_count == 1
    assert runtime.depth_writer_low_disk_watermark_breach_count == 1
    assert runtime.writer_capture_degraded_count == 0
    assert runtime.writer_dropped_envelope_count == 0
    assert runtime.depth_writer_dropped_envelope_count == 0
    assert runtime.writer_storage_self_disabled_count == 0
    assert runtime.depth_writer_storage_self_disabled_count == 0


def test_0d_callback_latency_does_not_poison_frozen_0b_canary_metric(
    tmp_path,
) -> None:
    collector = _collector(tmp_path, depth_capture_enabled=True)
    try:
        collector._record_producer_callback_latency("0B", 0.2)
        collector._record_producer_callback_latency("0B", 0.4)
        collector._record_producer_callback_latency("0D", 8.0)
        collector._record_producer_callback_latency("0D", 12.0)
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert runtime.producer_callback_latency_scope == ("kiwoom_0b_trade_callback_only")
    assert runtime.producer_callback_latency_p50_ms == 0.2
    assert runtime.producer_callback_latency_p99_ms == 0.4
    assert runtime.producer_0d_callback_latency_p50_ms == 8.0
    assert runtime.producer_0d_callback_latency_p99_ms == 12.0
    payload = runtime.as_dict()
    assert payload["schema"] == "scalp_micro_reversion_forward_collector_v9"
    depth_contract = payload["metric_contracts"]["depth_callback_latency"]
    capacity_contract = payload["metric_contracts"]["low_disk_capacity_warning"]
    assert {
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    } <= set(depth_contract)
    assert "satisfy_or_bypass_0b_callback_latency_canary" in (
        depth_contract["forbidden_uses"]
    )
    assert {
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    } <= set(capacity_contract)
    assert runtime.writer_low_disk_watermark_bytes > (
        runtime.writer_critical_disk_watermark_bytes
    )
    assert runtime.writer_low_disk_watermark_breach_count >= 0
    assert runtime.depth_writer_low_disk_watermark_breach_count >= 0


def test_runtime_snapshot_percentiles_do_not_hold_producer_metrics_lock(
    tmp_path, monkeypatch
) -> None:
    collector = _collector(tmp_path)
    collector._record_producer_callback_latency("0B", 0.2)
    percentile_started = threading.Event()
    release_percentile = threading.Event()
    increment_completed = threading.Event()
    original_percentile = collector_module._percentiles

    def slow_percentile(values, percentile):
        percentile_started.set()
        assert release_percentile.wait(timeout=1.0)
        return original_percentile(values, percentile)

    monkeypatch.setattr(collector_module, "_percentiles", slow_percentile)
    snapshot_thread = threading.Thread(target=collector.runtime_snapshot)
    snapshot_thread.start()
    assert percentile_started.wait(timeout=1.0)

    increment_thread = threading.Thread(
        target=lambda: (
            collector._increment("_producer_0b_callbacks"),
            increment_completed.set(),
        )
    )
    increment_thread.start()
    try:
        assert increment_completed.wait(timeout=0.5)
    finally:
        release_percentile.set()
        snapshot_thread.join(timeout=1.0)
        increment_thread.join(timeout=1.0)
    try:
        assert not snapshot_thread.is_alive()
        assert not increment_thread.is_alive()
    finally:
        collector.close()


def test_0d_depth_capture_is_independently_default_off(tmp_path) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    try:
        result = collector.observe_kiwoom_0d(
            "000001", _depth_snapshot(), realtime_type="0D"
        )
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.DISABLED
    assert runtime.depth_capture_active is False
    assert runtime.producer_0d_callback_count == 0
    assert tuple(tmp_path.rglob("market_depth_stream.jsonl")) == ()


def test_0d_depth_capture_rejects_missing_official_clock(tmp_path) -> None:
    collector = _collector(tmp_path, depth_capture_enabled=True)
    payload = _depth_snapshot(orderbook_time="")
    try:
        result = collector.observe_kiwoom_0d("000001", payload, realtime_type="0D")
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.INVALID_EXCHANGE_TIMESTAMP
    assert runtime.invalid_depth_timestamp_count == 1


def test_0d_depth_capture_does_not_impute_missing_combined_totals(tmp_path) -> None:
    collector = _collector(tmp_path, depth_capture_enabled=True)
    payload = _depth_snapshot()
    payload["last_depth_tick"]["ask_depth"] = None
    payload["last_depth_tick"]["route_depth_totals"]["combined"]["ask"] = None
    try:
        result = collector.observe_kiwoom_0d("000001", payload, realtime_type="0D")
        runtime = collector.runtime_snapshot()
    finally:
        collector.close()

    assert result is ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
    assert runtime.invalid_depth_snapshot_count == 1


def test_stale_series_epoch_is_rejected_before_gap_and_detector(tmp_path) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    entered = threading.Event()
    release = threading.Event()
    detector_calls = 0
    original_process = collector._process_envelope

    class RecordingDetector:
        def process(self, _observation):
            nonlocal detector_calls
            detector_calls += 1
            return ()

    collector._detector = RecordingDetector()

    def paused_process(envelope) -> None:
        entered.set()
        release.wait(timeout=2)
        original_process(envelope)

    collector._process_envelope = paused_process
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    assert entered.wait(timeout=1)
    with collector._state_lock:
        collector._series_epochs[("000001", "KRX", "KRX_REGULAR")] = time.time_ns()
    release.set()
    deadline = time.monotonic() + 1
    while collector._sink.qsize() and time.monotonic() < deadline:
        time.sleep(0.005)
    collector.close()
    runtime = collector.runtime_snapshot()

    assert detector_calls == 0
    assert runtime.worker_processed_count == 0
    assert runtime.stale_sequence_epoch_envelope_count == 1
    assert runtime.unexplained_sequence_gap_count == 0


def test_transport_epoch_drops_queued_old_rows_and_restarts_both_sequences(
    tmp_path,
) -> None:
    collector = _collector(
        tmp_path,
        path_capture_enabled=True,
        depth_capture_enabled=True,
    )
    base_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:00.010+09:00").timestamp() * 1_000
    )
    try:
        with collector._transport_epoch_lock:
            old_epoch = collector.runtime_snapshot().sequence_epoch
            assert (
                collector.observe_kiwoom_0b(
                    "000001",
                    _snapshot(received_at_ms=base_ms),
                    realtime_type="0B",
                )
                is ProducerCanaryResult.ENQUEUED
            )
            assert (
                collector.observe_kiwoom_0d(
                    "000001",
                    _depth_snapshot(received_at_ms=base_ms),
                    realtime_type="0D",
                )
                is ProducerCanaryResult.ENQUEUED
            )
            new_epoch = collector.begin_transport_epoch()
            assert new_epoch > old_epoch
            assert (
                collector.observe_kiwoom_0b(
                    "000001",
                    _snapshot(
                        exchange_time="090001000",
                        received_at_ms=base_ms + 1_000,
                        price=10_010,
                    ),
                    realtime_type="0B",
                )
                is ProducerCanaryResult.ENQUEUED
            )
            assert (
                collector.observe_kiwoom_0d(
                    "000001",
                    _depth_snapshot(
                        orderbook_time="090001000",
                        received_at_ms=base_ms + 1_000,
                    ),
                    realtime_type="0D",
                )
                is ProducerCanaryResult.ENQUEUED
            )

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            runtime = collector.runtime_snapshot()
            if (
                runtime.writer_persisted_envelope_count >= 1
                and runtime.depth_writer_persisted_envelope_count >= 1
            ):
                break
            time.sleep(0.01)
    finally:
        collector.close()

    runtime = collector.runtime_snapshot()
    market_file = next(tmp_path.rglob("market_stream.jsonl"))
    depth_file = next(tmp_path.rglob("market_depth_stream.jsonl"))
    market_rows = [
        json.loads(line)
        for line in market_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    depth_rows = [
        json.loads(line)
        for line in depth_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(market_rows) == len(depth_rows) == 1
    assert market_rows[0]["sequence_epoch"] == new_epoch
    assert depth_rows[0]["sequence_epoch"] == new_epoch
    assert market_rows[0]["source_sequence"] == 1
    assert depth_rows[0]["source_sequence"] == 1
    assert market_rows[0]["series_sequence"] == 1
    assert depth_rows[0]["series_sequence"] == 1
    assert runtime.stale_sequence_epoch_envelope_count == 1
    assert runtime.depth_dropped_envelope_count == 1


def test_event_symbol_mismatch_is_blocked_and_counted(tmp_path) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)

    class MismatchedDetector:
        def process(self, _observation):
            return (SimpleNamespace(event=SimpleNamespace(symbol="000002")),)

    collector._detector = MismatchedDetector()
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
    collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.event_symbol_mismatch_count == 1
    assert runtime.shock_event_count == 0
    assert runtime.event_reference_persisted_count == 0


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


def test_crossed_optional_bbo_is_sanitized_without_losing_trade_sequence(
    tmp_path,
) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    snapshot = _snapshot()
    snapshot["last_trade_tick"]["best_bid"] = 10_100
    snapshot["last_trade_tick"]["best_ask"] = 10_000

    assert (
        collector.observe_kiwoom_0b("000001", snapshot, realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    deadline = time.monotonic() + 1
    while (
        collector.runtime_snapshot().worker_processed_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    collector.close()

    runtime = collector.runtime_snapshot()
    stream = next(tmp_path.rglob("market_stream.jsonl"))
    row = json.loads(stream.read_text(encoding="utf-8"))
    assert runtime.crossed_bbo_sanitized_count == 1
    assert runtime.crossed_bbo_sanitized_rate == 100.0
    assert runtime.adapter_invalid_envelope_count == 0
    assert runtime.observation_dropped_envelope_count == 0
    assert row["trade_price"] == 10_000
    assert row["best_bid"] is None
    assert row["best_ask"] is None
    assert row["quote_age_ms"] is None


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
    invalid_payload = _snapshot(item="000002", price=-1)
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
        invalid_collector.observe_kiwoom_0b(
            "000002",
            _snapshot(item="000002"),
            realtime_type="0B",
        )
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


def test_collector_close_defers_writers_until_worker_drain_then_retries(
    tmp_path,
) -> None:
    collector = _collector(tmp_path)
    entered = threading.Event()
    release = threading.Event()

    def blocked_process(_envelope) -> None:
        entered.set()
        release.wait(timeout=2)

    requested_writers: list[str] = []

    class RecordingWriter:
        def __init__(self, name: str) -> None:
            self.name = name
            self.close_requested = False
            self.wait_calls = 0
            self.alive = True

        def request_close(self) -> None:
            self.close_requested = True
            requested_writers.append(self.name)
            self.alive = False

        def wait_closed(self, *, timeout_sec: float) -> None:
            self.wait_calls += 1
            assert self.close_requested is True
            assert requested_writers == ["first", "second"]

        def metrics(self):
            return SimpleNamespace(writer_alive=self.alive)

    first_writer = RecordingWriter("first")
    second_writer = RecordingWriter("second")
    collector._process_envelope = blocked_process
    collector._writers[("2026-08-08", "KRX", "KRX_REGULAR")] = first_writer
    collector._writers[("2026-08-08", "NXT", "NXT_REGULAR_OVERLAP")] = second_writer
    assert (
        collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        is ProducerCanaryResult.ENQUEUED
    )
    assert entered.wait(timeout=1)

    with pytest.raises(RuntimeError, match="shutdown had 1 error"):
        collector.close(timeout_sec=0.01)
    assert first_writer.close_requested is False
    assert second_writer.close_requested is False
    assert collector._lifecycle is CollectorLifecycle.CLOSE_FAILED
    assert collector._close_attempts == 1
    assert collector._close_failures == 1
    assert collector._writer_alive_after_close == 0
    assert collector._reference_reconciliation_errors == 0
    release.set()
    collector.close(timeout_sec=1)
    assert collector._lifecycle is CollectorLifecycle.CLOSED
    assert first_writer.wait_calls == 1
    assert second_writer.wait_calls == 1
    assert collector._close_attempts == 2
    with pytest.raises(RuntimeError, match="one-shot"):
        collector.start()


def test_close_waits_for_inflight_callback_then_drains_enqueued_row(
    tmp_path, monkeypatch
) -> None:
    collector = _collector(tmp_path)
    callback_entered = threading.Event()
    callback_release = threading.Event()
    close_errors: list[Exception] = []
    original_timestamp = __import__(
        "src.engine.scalping.micro_reversion.forward_collector",
        fromlist=["_exchange_timestamp_from_0b"],
    )._exchange_timestamp_from_0b

    def paused_timestamp(*args, **kwargs):
        callback_entered.set()
        callback_release.wait(timeout=2)
        return original_timestamp(*args, **kwargs)

    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.forward_collector."
        "_exchange_timestamp_from_0b",
        paused_timestamp,
    )
    observe_result: list[ProducerCanaryResult] = []
    observe_thread = threading.Thread(
        target=lambda: observe_result.append(
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        )
    )
    observe_thread.start()
    assert callback_entered.wait(timeout=1)

    def close_collector() -> None:
        try:
            collector.close(timeout_sec=1)
        except Exception as exc:
            close_errors.append(exc)

    close_thread = threading.Thread(target=close_collector)
    close_thread.start()
    time.sleep(0.02)
    assert close_thread.is_alive()
    assert collector._active_callbacks == 1
    callback_release.set()
    observe_thread.join(timeout=1)
    close_thread.join(timeout=2)

    runtime = collector.runtime_snapshot()
    assert close_errors == []
    assert observe_result == [ProducerCanaryResult.ENQUEUED]
    assert runtime.collector_lifecycle == CollectorLifecycle.CLOSED.value
    assert runtime.collector_active_callback_count == 0
    assert runtime.enqueued_count == 1
    assert runtime.worker_processed_count == 1
    assert collector._sink.qsize() == 0


def test_callback_barrier_timeout_is_retryable_and_does_not_strand_row(
    tmp_path, monkeypatch
) -> None:
    collector = _collector(tmp_path)
    callback_entered = threading.Event()
    callback_release = threading.Event()
    module = __import__(
        "src.engine.scalping.micro_reversion.forward_collector",
        fromlist=["_exchange_timestamp_from_0b"],
    )
    original_timestamp = module._exchange_timestamp_from_0b

    def paused_timestamp(*args, **kwargs):
        callback_entered.set()
        callback_release.wait(timeout=2)
        return original_timestamp(*args, **kwargs)

    monkeypatch.setattr(module, "_exchange_timestamp_from_0b", paused_timestamp)
    observe_result: list[ProducerCanaryResult] = []
    observe_thread = threading.Thread(
        target=lambda: observe_result.append(
            collector.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
        )
    )
    observe_thread.start()
    assert callback_entered.wait(timeout=1)

    with pytest.raises(RuntimeError, match="shutdown had 1 error"):
        collector.close(timeout_sec=0.01)
    assert collector._lifecycle is CollectorLifecycle.CLOSE_FAILED
    assert collector._stop_requested.is_set() is False
    assert collector._thread is not None and collector._thread.is_alive()

    callback_release.set()
    observe_thread.join(timeout=1)
    collector.close(timeout_sec=1)
    runtime = collector.runtime_snapshot()

    assert observe_result == [ProducerCanaryResult.ENQUEUED]
    assert runtime.collector_lifecycle == CollectorLifecycle.CLOSED.value
    assert runtime.collector_close_attempt_count == 2
    assert runtime.collector_close_failure_count == 1
    assert runtime.collector_worker_alive_after_close_count == 1
    assert runtime.enqueued_count == runtime.worker_processed_count == 1
    assert collector._sink.qsize() == 0


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

    path_files = list(tmp_path.rglob("market_stream.jsonl"))
    reference_files = list(tmp_path.rglob("market_stream_event_references.jsonl"))
    assert len(path_files) == 1
    assert len(reference_files) == 1
    assert path_files[0].read_text(encoding="utf-8").strip()
    assert reference_files[0].read_text(encoding="utf-8").strip()
    assert snapshot.shock_event_count == 1
    stream_rows = [
        json.loads(line)
        for line in path_files[0].read_text(encoding="utf-8").splitlines()
    ]
    assert len(stream_rows) == snapshot.enqueued_count == 2
    assert all(
        row["schema"] == "scalp_micro_reversion_market_stream_point_v3"
        for row in stream_rows
    )
    assert snapshot.canonical_stream_point_count == 2
    assert snapshot.canonical_stream_duplicate_count == 0
    assert snapshot.canonical_stream_pre_window_point_count == 1
    assert snapshot.canonical_stream_active_window_point_count == 1
    assert snapshot.canonical_stream_post_window_point_count == 0
    assert snapshot.canonical_stream_complete_segment_count == 0
    assert snapshot.canonical_stream_incomplete_segment_count == 1
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


def test_bounded_exchange_timestamp_regression_is_raw_persisted_and_quarantined(
    tmp_path,
) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    received_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:54.121+09:00").timestamp() * 1_000
    )
    payloads = (
        _snapshot(
            exchange_time="090054000",
            received_at_ms=received_ms,
            price=10_000,
        ),
        _snapshot(
            exchange_time="090053000",
            received_at_ms=received_ms + 4,
            price=9_990,
        ),
        _snapshot(
            exchange_time="090054000",
            received_at_ms=received_ms + 9,
            price=9_995,
        ),
    )
    try:
        for payload in payloads:
            assert (
                collector.observe_kiwoom_0b("000001", payload, realtime_type="0B")
                is ProducerCanaryResult.ENQUEUED
            )
        deadline = time.monotonic() + 2
        while (
            collector.runtime_snapshot().worker_processed_count < len(payloads)
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)
    finally:
        collector.close()
    runtime = collector.runtime_snapshot()
    stream_path = next(tmp_path.rglob("market_stream.jsonl"))
    stream_rows = [json.loads(line) for line in stream_path.read_text().splitlines()]

    assert [row["source_sequence"] for row in stream_rows] == [1, 2, 3]
    assert [row["path_order_status"] for row in stream_rows] == [
        "accept",
        "exchange_timestamp_regression_quarantined",
        "accept",
    ]
    assert [row["path_consumer_eligible"] for row in stream_rows] == [
        True,
        False,
        True,
    ]
    assert [row["exchange_timestamp_regression_ms"] for row in stream_rows] == [
        0,
        1_000,
        0,
    ]
    assert runtime.worker_processed_count == 3
    assert runtime.path_accepted_envelope_count == 2
    assert runtime.path_sequence_gap_count == 0
    assert runtime.path_out_of_order_sequence_count == 0
    assert runtime.path_exchange_timestamp_regression_count == 1
    assert runtime.path_exchange_timestamp_regression_quarantined_count == 1
    assert runtime.path_exchange_timestamp_regression_exceeded_count == 0
    assert runtime.path_exchange_timestamp_regression_max_ms == 1_000
    assert runtime.path_exchange_timestamp_regression_tolerance_ms == 1_000
    assert runtime.path_local_receive_timestamp_regression_count == 0
    assert runtime.actual_order_submitted is False
    assert runtime.broker_order_forbidden is True


def test_exchange_timestamp_regression_over_bound_remains_hard_stop_metric(
    tmp_path,
) -> None:
    collector = _collector(tmp_path, path_capture_enabled=True)
    received_ms = int(
        datetime.fromisoformat("2026-08-08T09:00:54.121+09:00").timestamp() * 1_000
    )
    try:
        for payload in (
            _snapshot(exchange_time="090054000", received_at_ms=received_ms),
            _snapshot(exchange_time="090052000", received_at_ms=received_ms + 4),
        ):
            assert (
                collector.observe_kiwoom_0b("000001", payload, realtime_type="0B")
                is ProducerCanaryResult.ENQUEUED
            )
        deadline = time.monotonic() + 2
        while (
            collector.runtime_snapshot().worker_processed_count < 2
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)
    finally:
        collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.path_exchange_timestamp_regression_count == 1
    assert runtime.path_exchange_timestamp_regression_quarantined_count == 0
    assert runtime.path_exchange_timestamp_regression_exceeded_count == 1
    assert runtime.path_exchange_timestamp_regression_max_ms == 2_000


def test_shutdown_reconciliation_detects_orphan_and_unreferenced_segments(
    tmp_path,
) -> None:
    collector = ForwardObservationCollector(
        detector=MultiHorizonShockDetector(),
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
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
    assert runtime.reference_reconciliation_duration_ms >= 0
    assert runtime.reference_reconciliation_path_rows_scanned == 1
    assert runtime.reference_reconciliation_reference_rows_scanned == 1
    assert runtime.reference_reconciliation_peak_tracked_key_count >= 2
    assert runtime.duplicate_event_reference_count == 0
    assert runtime.duplicate_event_id_count == 0
    assert runtime.duplicate_path_reference_pair_count == 0


def test_shutdown_reconciliation_counts_duplicate_references(tmp_path) -> None:
    collector = ForwardObservationCollector(
        detector=MultiHorizonShockDetector(),
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
    )
    key = ("2026-08-08", "KRX", "KRX_REGULAR")
    path = collector.config.storage_policy.partition_path(
        tmp_path,
        trade_date=key[0],
        venue=key[1],
        session_bucket=key[2],
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"path_segment_id": "segment-1"}) + "\n")
    reference = {
        "path_segment_id": "segment-1",
        "shock_event_id": "event-1",
    }
    path.with_name("event_references.jsonl").write_text(
        "\n".join((json.dumps(reference), json.dumps(reference))) + "\n"
    )
    collector._reference_partitions.add(key)

    collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.reference_reconciliation_completed is True
    assert runtime.reference_reconciliation_path_rows_scanned == 1
    assert runtime.reference_reconciliation_reference_rows_scanned == 2
    assert runtime.duplicate_event_reference_count == 1
    assert runtime.duplicate_event_id_count == 1
    assert runtime.duplicate_path_reference_pair_count == 1


def test_shutdown_reconciliation_reads_all_rotated_path_shards(tmp_path) -> None:
    collector = ForwardObservationCollector(
        detector=MultiHorizonShockDetector(),
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
    )
    key = ("2026-08-08", "KRX", "KRX_REGULAR")
    path = collector.config.storage_policy.partition_path(
        tmp_path,
        trade_date=key[0],
        venue=key[1],
        session_bucket=key[2],
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"path_segment_id": "segment-1"}) + "\n")
    rotated = collector.config.storage_policy.shard_path(path, 1)
    rotated.write_text(json.dumps({"path_segment_id": "segment-2"}) + "\n")
    path.with_name("event_references.jsonl").write_text(
        "\n".join(
            (
                json.dumps(
                    {"path_segment_id": "segment-1", "shock_event_id": "event-1"}
                ),
                json.dumps(
                    {"path_segment_id": "segment-2", "shock_event_id": "event-2"}
                ),
            )
        )
        + "\n"
    )
    collector._reference_partitions.add(key)

    collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.reference_reconciliation_completed is True
    assert runtime.reference_reconciliation_path_rows_scanned == 2
    assert runtime.reference_reconciliation_reference_rows_scanned == 2
    assert runtime.event_reference_coverage_pct == 100.0
    assert runtime.orphan_reference_count == 0
    assert runtime.unreferenced_segment_count == 0


def test_canonical_reference_without_stream_is_reported_as_orphan(tmp_path) -> None:
    collector = ForwardObservationCollector(
        detector=MultiHorizonShockDetector(),
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
    )
    key = ("2026-08-08", "KRX", "KRX_REGULAR")
    stream = collector.config.storage_policy.stream_partition_path(
        tmp_path,
        trade_date=key[0],
        venue=key[1],
        session_bucket=key[2],
    )
    stream.parent.mkdir(parents=True)
    reference = {
        "schema": "scalp_micro_reversion_path_event_reference_v2",
        "path_segment_id": "segment-1",
        "shock_event_id": "event-1",
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 7,
        "capture_started_at": "2026-08-08T09:00:00+09:00",
        "segment_event_detected_at_ms": int(
            datetime.fromisoformat("2026-08-08T09:00:01+09:00").timestamp() * 1_000
        ),
        "capture_ended_at": "2026-08-08T09:03:01+09:00",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }
    stream.with_name("market_stream_event_references.jsonl").write_text(
        json.dumps(reference) + "\n", encoding="utf-8"
    )
    collector._reference_partitions.add(key)

    collector.close()
    runtime = collector.runtime_snapshot()

    assert runtime.reference_reconciliation_completed is True
    assert runtime.reference_reconciliation_reference_rows_scanned == 1
    assert runtime.event_reference_coverage_pct == 0.0
    assert runtime.orphan_reference_count == 1


def test_canonical_reconciliation_fails_closed_on_authority_drift(tmp_path) -> None:
    collector = ForwardObservationCollector(
        detector=MultiHorizonShockDetector(),
        flags=ObserverFeatureFlags(observer_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
    )
    key = ("2026-08-08", "KRX", "KRX_REGULAR")
    stream = collector.config.storage_policy.stream_partition_path(
        tmp_path,
        trade_date=key[0],
        venue=key[1],
        session_bucket=key[2],
    )
    stream.parent.mkdir(parents=True)
    stream.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_stream_point_v1",
                "metric_contract_id": (
                    "scalp_micro_reversion_market_stream_contract_v1"
                ),
                "symbol": "000001",
                "venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "sequence_epoch": 7,
                "source_sequence": 1,
                "series_sequence": 1,
                "exchange_timestamp": "2026-08-08T09:00:00+09:00",
                "actual_order_submitted": True,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    collector._reference_partitions.add(key)

    with pytest.raises(RuntimeError, match="shutdown had 1 error"):
        collector.close()

    runtime = collector.runtime_snapshot()
    assert runtime.reference_reconciliation_completed is False
    assert runtime.reference_reconciliation_error_count == 1


def test_ws_producer_hook_isolates_collector_failure(monkeypatch) -> None:
    class BrokenCollector:
        def observe_kiwoom_0b(self, *_args, **_kwargs):
            raise OSError("synthetic observer failure")

    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector = BrokenCollector()

    manager._queue_tick_event("000001", _snapshot(), realtime_type="0B")

    assert "000001" in manager._pending_tick_events
    assert manager._micro_reversion_forward_collector_error == "OSError"


def test_ws_producer_hook_routes_0b_and_0d_without_cross_call(monkeypatch) -> None:
    class RecordingCollector:
        def __init__(self) -> None:
            self.trade_calls = 0
            self.depth_calls = 0

        def observe_kiwoom_0b(self, *_args, **_kwargs):
            self.trade_calls += 1

        def observe_kiwoom_0d(self, *_args, **_kwargs):
            self.depth_calls += 1

    collector = RecordingCollector()
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector = collector

    manager._queue_tick_event("000001", _snapshot(), realtime_type="0D")
    manager._queue_tick_event("000001", _snapshot(), realtime_type="0B")

    assert collector.trade_calls == 1
    assert collector.depth_calls == 1


def test_ws_source_only_collection_reaches_collector_not_trading_event(
    monkeypatch,
) -> None:
    class RecordingCollector:
        def __init__(self) -> None:
            self.trade_calls = 0

        def observe_kiwoom_0b(self, *_args, **_kwargs):
            self.trade_calls += 1

    collector = RecordingCollector()
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector = collector
    manager._micro_reversion_observation_items_by_code = {"000001": "000001_AL"}
    manager._micro_reversion_observation_only_codes.add("000001")

    manager._queue_tick_event("000001", _snapshot(), realtime_type="0B")

    assert collector.trade_calls == 1
    assert manager._pending_tick_events == {}


def test_ws_stop_retains_collector_until_retryable_close_succeeds(monkeypatch) -> None:
    class RetryCollector:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self, *, timeout_sec: float) -> None:
            self.close_calls += 1
            if self.close_calls == 1:
                raise RuntimeError("synthetic retry")

    collector = RetryCollector()
    manager = KiwoomWSManager("test-token")
    manager._stop_event.set()
    manager._micro_reversion_forward_collector = collector
    monkeypatch.setattr(
        manager,
        "_persist_micro_reversion_canary_snapshot",
        lambda: None,
    )

    manager.stop()
    assert manager._micro_reversion_forward_collector is collector
    assert manager._micro_reversion_forward_collector_error == "RuntimeError"

    manager.stop()
    assert collector.close_calls == 2
    assert manager._micro_reversion_forward_collector is None


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


def test_ws_canary_guard_stops_observer_without_stopping_bot(monkeypatch) -> None:
    manager = KiwoomWSManager("test-token")
    manager._started = True
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )

    manager._enforce_micro_reversion_canary_guard(
        {
            "canary_guard": {
                "stop_required": True,
                "stop_reasons": ["nonzero_stop_metric:worker_error_count=1"],
            }
        }
    )

    assert close_calls == ["observer_close"]
    assert manager._started is True
    assert "worker_error_count=1" in (
        manager._micro_reversion_forward_collector_stop_reason
    )


def test_ws_canary_guard_confirms_latency_only_breach_before_observer_stop(
    monkeypatch,
) -> None:
    manager = KiwoomWSManager("test-token")
    manager._started = True
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )
    payload = {
        "canary_guard": {
            "stop_required": True,
            "stop_reasons": [
                "producer_callback_latency_p99_exceeded:2.100000>2.000000"
            ],
            "observed_latency_p99_ms": 2.1,
            "latency_p99_max_ms": 2.0,
            "latency_breach_confirmation_snapshots": 3,
            "latency_breach_immediate_multiplier": 2.0,
        }
    }

    manager._enforce_micro_reversion_canary_guard(payload)
    manager._enforce_micro_reversion_canary_guard(payload)

    assert close_calls == []
    assert manager._micro_reversion_canary_latency_breach_count == 2
    assert manager._micro_reversion_forward_collector_stop_reason == ""

    manager._enforce_micro_reversion_canary_guard(payload)

    assert close_calls == ["observer_close"]
    assert manager._started is True
    assert manager._micro_reversion_canary_latency_breach_count == 3
    assert manager._micro_reversion_forward_collector_stop_reason == (
        "producer_callback_latency_p99_exceeded:2.100000>2.000000"
    )


def test_ws_canary_guard_resets_latency_confirmation_after_healthy_snapshot(
    monkeypatch,
) -> None:
    manager = KiwoomWSManager("test-token")
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )
    breach = {
        "canary_guard": {
            "stop_required": True,
            "stop_reasons": [
                "producer_callback_latency_p95_exceeded:1.100000>1.000000"
            ],
            "observed_latency_p95_ms": 1.1,
            "latency_p95_max_ms": 1.0,
            "latency_breach_confirmation_snapshots": 3,
            "latency_breach_immediate_multiplier": 2.0,
        }
    }

    manager._enforce_micro_reversion_canary_guard(breach)
    manager._enforce_micro_reversion_canary_guard(
        {"canary_guard": {"stop_required": False, "stop_reasons": []}}
    )
    manager._enforce_micro_reversion_canary_guard(breach)

    assert close_calls == []
    assert manager._micro_reversion_canary_latency_breach_count == 1


def test_ws_canary_snapshot_exposes_latency_confirmation_count(
    monkeypatch,
) -> None:
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_canary_latency_breach_count = 2

    class Snapshot:
        def as_dict(self):
            return {"observer_runtime_loaded": True}

    class Collector:
        def runtime_snapshot(self):
            return Snapshot()

    manager._micro_reversion_forward_collector = Collector()

    snapshot = manager.micro_reversion_forward_collector_snapshot()

    assert snapshot["canary_latency_breach_consecutive_count"] == 2


def test_ws_canary_guard_stops_severe_latency_breach_immediately(
    monkeypatch,
) -> None:
    manager = KiwoomWSManager("test-token")
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )

    manager._enforce_micro_reversion_canary_guard(
        {
            "canary_guard": {
                "stop_required": True,
                "stop_reasons": [
                    "producer_callback_latency_p99_exceeded:4.000000>2.000000"
                ],
                "observed_latency_p99_ms": 4.0,
                "latency_p99_max_ms": 2.0,
                "latency_breach_confirmation_snapshots": 3,
                "latency_breach_immediate_multiplier": 2.0,
            }
        }
    )

    assert close_calls == ["observer_close"]
    assert manager._micro_reversion_canary_latency_breach_count == 0


def test_ws_canary_guard_fails_closed_when_latency_policy_provenance_is_missing(
    monkeypatch,
) -> None:
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_canary_latency_breach_count = 1
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )

    manager._enforce_micro_reversion_canary_guard(
        {
            "canary_guard": {
                "stop_required": True,
                "stop_reasons": [
                    "producer_callback_latency_p99_exceeded:2.100000>2.000000"
                ],
                "observed_latency_p99_ms": 2.1,
                "latency_p99_max_ms": 2.0,
            }
        }
    )

    assert close_calls == ["observer_close"]
    assert manager._micro_reversion_canary_latency_breach_count == 0


def test_ws_canary_auto_stop_is_latched_for_manager_lifetime(monkeypatch) -> None:
    monkeypatch.setenv("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", "true")
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector_stop_reason = "worker_error_count=1"

    manager._start_micro_reversion_forward_collector()

    assert manager._micro_reversion_forward_collector is None
    assert manager._micro_reversion_forward_collector_error == "CanaryAutoStopLatched"


def test_ws_canary_monitor_failure_closes_only_observer(monkeypatch) -> None:
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager._micro_reversion_forward_collector = object()
    close_calls = []
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append("observer_close"),
    )

    manager._fail_closed_micro_reversion_canary_monitor(OSError("disk full"))

    assert close_calls == ["observer_close"]
    assert manager._started is True
    assert manager._micro_reversion_forward_collector_error == "OSError"
    assert manager._micro_reversion_forward_collector_stop_reason == (
        "canary_monitor_failure:OSError"
    )


def test_ws_start_does_not_overwrite_collector_with_pending_close(
    monkeypatch,
) -> None:
    monkeypatch.setenv("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", "true")
    manager = KiwoomWSManager("test-token")
    retained = object()
    manager._micro_reversion_forward_collector = retained
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: None,
    )

    manager._start_micro_reversion_forward_collector()

    assert manager._micro_reversion_forward_collector is retained
    assert manager._micro_reversion_forward_collector_error == (
        "PreviousCollectorClosePending"
    )


def test_ws_monitor_start_failure_closes_created_collector(
    monkeypatch,
) -> None:
    class RecordingCollector:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self, *, timeout_sec: float) -> None:
            self.close_calls += 1

    collector = RecordingCollector()
    monkeypatch.setenv("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", "true")
    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.forward_collector."
        "build_forward_collector_from_env",
        lambda *, start: collector,
    )
    manager = KiwoomWSManager("test-token")
    monkeypatch.setattr(
        manager,
        "_start_micro_reversion_canary_monitor",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic thread failure")),
    )
    monkeypatch.setattr(
        manager,
        "_persist_micro_reversion_canary_snapshot",
        lambda: None,
    )

    manager._start_micro_reversion_forward_collector()

    assert collector.close_calls == 1
    assert manager._micro_reversion_forward_collector is None
    assert manager._micro_reversion_forward_collector_stop_reason == (
        "canary_monitor_start_failure:RuntimeError"
    )


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

    forbidden_fragments = (
        "broker",
        "order",
        "execution",
        "ai",
        "adm",
        "ldm",
        "manual_control",
    )
    assert not any(
        fragment in module_name.lower()
        for module_name in imported
        for fragment in forbidden_fragments
    )


def test_depth_freezes_existing_owner_inputs_without_future_or_new_requests(tmp_path):
    from src.engine.scalping.avg_down_replay_capture import record_market_inputs

    snapshot = _depth_snapshot()
    cutoff = (
        datetime.fromisoformat(snapshot["exchange_timestamp"]).timestamp()
        if "exchange_timestamp" in snapshot
        else None
    )
    # The collector owns the actual canonical clock; inspect its persisted point
    # before recording a second frame, without modifying protocol fields.
    collector = _collector(
        tmp_path, path_capture_enabled=True, depth_capture_enabled=True
    )
    try:
        assert (
            collector.observe_kiwoom_0d("000001", snapshot, realtime_type="0D")
            is ProducerCanaryResult.ENQUEUED
        )
    finally:
        collector.close()
    path = next(tmp_path.rglob("market_depth_stream.jsonl"))
    first = json.loads(path.read_text().splitlines()[0])
    clock = datetime.fromisoformat(first["exchange_timestamp"]).timestamp()
    record_market_inputs("000001", now_ts=clock - 1, market_regime="BULL")
    record_market_inputs("000001", now_ts=clock + 1, future_input="forbidden")
    from dataclasses import replace
    from src.engine.scalping.micro_reversion.path_journal import MarketDepthPoint

    fields = {
        k: first[k]
        for k in (
            "symbol",
            "exchange_timestamp",
            "local_receive_timestamp",
            "source_sequence",
            "sequence_epoch",
            "series_sequence",
            "venue",
            "session_bucket",
            "item",
            "orderbook_time_raw",
            "best_bid",
            "best_ask",
            "best_bid_qty",
            "best_ask_qty",
            "bid_depth",
            "ask_depth",
            "bid_levels",
            "ask_levels",
            "route_depth_totals",
        )
    }
    point = MarketDepthPoint(**fields)
    row = point.as_dict()
    assert row["recorded_inputs"]["market_regime"]["value"] == "BULL"
    assert "future_input" not in row["recorded_inputs"]
    record_market_inputs("000001", now_ts=clock, market_regime="BEAR")
    assert point.as_dict() == row
    assert (
        row["actual_order_submitted"] is False and row["broker_order_forbidden"] is True
    )


@pytest.mark.parametrize(
    "raw_values", [{"13": "001234", "15": "-0010"}, {}, {"13": 1234, "15": 10}]
)
def test_integrated_stream_preserves_raw_volume_lineage_without_inventing_missing_fields(
    tmp_path, raw_values
):
    collector = _collector(tmp_path, path_capture_enabled=True)
    snap = _snapshot(item="000001_AL", venue="SOR")
    snap["last_trade_tick"]["values"] = raw_values
    # A normalized cumulative value is not a substitute for the raw FID.
    snap["last_trade_tick"]["cum_volume"] = 1234
    try:
        assert (
            collector.observe_kiwoom_0b("000001", snap, realtime_type="0B")
            is ProducerCanaryResult.ENQUEUED
        )
        deadline = time.monotonic() + 2
        while (
            collector.runtime_snapshot().writer_persisted_envelope_count < 1
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
    finally:
        collector.close()
    files = list(tmp_path.rglob("market_stream.jsonl"))
    assert len(files) == 1
    row = json.loads(files[0].read_text().splitlines()[0])
    assert row["source_item"] == "000001_AL" and row["venue"] == "SOR"
    assert row["cumulative_volume_raw"] == (
        raw_values.get("13") if isinstance(raw_values.get("13"), str) else None
    )
    assert row["trade_volume_raw"] == (
        raw_values.get("15") if isinstance(raw_values.get("15"), str) else None
    )
    assert row["trade_qty"] == 10 and row["actual_order_submitted"] is False


def _closed_main_rejection_source(
    tmp_path, count=65, *, reconnect=False, close_day="2026-08-08", regression=False
):
    from src.engine.scalping.micro_reversion.canary_monitor import (
        write_canary_runtime_snapshot,
    )

    c = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True, path_capture_enabled=True),
        config=ForwardCollectorConfig(
            output_root=tmp_path / "data/observations/scalp_micro_reversion_forward"
        ),
    )
    c.start()
    received = int(
        datetime.fromisoformat("2026-08-08T09:00:54.121+09:00").timestamp() * 1000
    )
    c.observe_kiwoom_0b(
        "000001",
        (
            _snapshot(exchange_time="090054000", received_at_ms=received)
            if regression
            else _snapshot()
        ),
        realtime_type="0B",
    )
    deadline = time.monotonic() + 2
    while (
        c.runtime_snapshot().writer_persisted_envelope_count != 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    if regression:
        c.observe_kiwoom_0b(
            "000001",
            _snapshot(exchange_time="090053000", received_at_ms=received + 4),
            realtime_type="0B",
        )
    for i in range(count):
        if reconnect and i == count // 2:
            c.begin_transport_epoch()
        c.observe_kiwoom_0b(
            "000001", _snapshot(exchange_time="invalid"), realtime_type="0B"
        )
    if reconnect:
        c.observe_kiwoom_0b("000001", _snapshot(), realtime_type="0B")
    c.close()
    latest = (
        tmp_path / "data/runtime/scalp_micro_reversion_forward_collector/latest.json"
    )
    payload = write_canary_runtime_snapshot(
        c.runtime_snapshot().as_dict(),
        output_path=latest,
        now=datetime.fromisoformat(close_day + "T20:00:00+09:00"),
    )
    closed = next((latest.parent / "closed").glob("2026-08-08-*.json"))
    return c, payload, closed


@pytest.mark.parametrize(
    "fault",
    [None, "counter", "exceeded", "accepted", "missing", "authority", "receipt"],
)
def test_closed_main_ingress_rejection_keeps_tolerated_path_rows_quarantined(
    tmp_path, fault
):
    import gzip
    from src.engine.scalping.continuous_reversal_source import freeze_normalized_sources
    from src.engine.scalping.micro_reversion.observer_source_quality import (
        main_raw_epoch_validation,
    )

    _, payload, _ = _closed_main_rejection_source(tmp_path, count=1, regression=True)
    snap = payload["collector_snapshot"]
    assert snap["path_exchange_timestamp_regression_quarantined_count"] == 1
    assert snap["path_accepted_envelope_count"] == 1
    if fault == "counter":
        snap["path_exchange_timestamp_regression_count"] = 2
    elif fault == "exceeded":
        snap["path_exchange_timestamp_regression_exceeded_count"] = 1
    elif fault == "accepted":
        snap["path_accepted_envelope_count"] = 2
    elif fault == "missing":
        snap.pop("path_exchange_timestamp_regression_quarantined_count")
    elif fault == "authority":
        snap["trading_runtime_effect"] = True
    elif fault == "receipt":
        snap["timestamp_rejection_ledger"]["sha256"] = "0" * 64
    assert main_raw_epoch_validation(payload, source_date="2026-08-08")["eligible"] is (
        fault is None
    )
    if fault is None:
        parts = freeze_normalized_sources(
            tmp_path / "data", "2026-08-08", tmp_path / "freeze"
        )
        rows = [
            row
            for part in parts
            for values in json.loads(gzip.decompress(Path(part["path"]).read_bytes()))[
                "symbols"
            ].values()
            for row in values
        ]
        assert sum(row[8] for row in rows) == 1


@pytest.mark.parametrize(
    "count,reconnect", [(64, False), (65, False), (121, False), (1000, True)]
)
def test_complete_rejection_journal_preserves_valid_rows_through_native_consumer(
    tmp_path, count, reconnect
):
    import gzip
    from src.engine.scalping.continuous_reversal_source import freeze_normalized_sources
    from src.engine.scalping.micro_reversion.observer_source_quality import (
        main_raw_epoch_validation,
    )

    c, payload, closed = _closed_main_rejection_source(
        tmp_path, count, reconnect=reconnect
    )
    snapshot = payload["collector_snapshot"]
    assert len(snapshot["timestamp_rejection_samples"]) == 64
    assert snapshot["timestamp_rejection_ledger"]["rows"] == count
    assert payload["canary_guard"]["timestamp_source_quality"][
        "exact_rejected_row_exclusion_proven"
    ]
    verdict = main_raw_epoch_validation(payload, source_date="2026-08-08")
    assert verdict["eligible"]
    # Quarantine preserves its existing narrow current-epoch scope on reconnect.
    assert verdict["allowed_sequence_epochs"] == [snapshot["sequence_epoch"]]
    parts = freeze_normalized_sources(
        tmp_path / "data", "2026-08-08", tmp_path / "freeze"
    )
    assert (
        sum(
            row[8]
            for part in parts
            for rows in json.loads(gzip.decompress(Path(part["path"]).read_bytes()))[
                "symbols"
            ].values()
            for row in rows
        )
        == 1
    )
    before = closed.read_bytes()
    c.close()
    from src.engine.scalping.micro_reversion.canary_monitor import (
        write_canary_runtime_snapshot,
    )

    write_canary_runtime_snapshot(
        c.runtime_snapshot().as_dict(),
        output_path=closed.parent.parent / "latest.json",
        now=datetime.fromisoformat("2026-08-08T20:01:00+09:00"),
    )
    assert closed.read_bytes() == before


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "partial",
        "hash",
        "pid",
        "start",
        "epoch",
        "index",
        "unsealed",
        "date",
    ],
)
def test_rejection_journal_damage_still_excludes_epoch(tmp_path, damage):
    import hashlib
    from src.engine.scalping.micro_reversion.observer_source_quality import (
        main_raw_epoch_validation,
    )

    c, payload, _ = _closed_main_rejection_source(tmp_path)
    snapshot = payload["collector_snapshot"]
    ledger = snapshot["timestamp_rejection_ledger"]
    path = Path(ledger["path"])
    if damage == "missing":
        path.unlink()
    elif damage == "partial":
        path.write_bytes(path.read_bytes()[:-1])
    elif damage == "hash":
        ledger["sha256"] = "0" * 64
    elif damage == "unsealed":
        ledger["sealed"] = False
    elif damage != "date":
        rows = [json.loads(raw) for raw in path.read_bytes().splitlines()]
        field = {
            "pid": "process_pid",
            "start": "process_start_ticks",
            "epoch": "local_observer_epoch",
            "index": "rejection_index",
        }[damage]
        rows[0][field] = "foreign" if damage == "start" else 999
        raw = b"".join((json.dumps(row) + "\n").encode() for row in rows)
        path.write_bytes(raw)
        ledger.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    assert not main_raw_epoch_validation(
        payload, source_date="2026-08-09" if damage == "date" else "2026-08-08"
    )["eligible"]


def test_midnight_close_retains_exact_previous_source_date(tmp_path):
    from src.engine.scalping.continuous_reversal_source import _source_quality_receipt
    from src.engine.scalping.micro_reversion.observer_source_quality import (
        main_raw_epoch_validation,
    )

    _, _, closed = _closed_main_rejection_source(tmp_path, close_day="2026-08-09")
    payload = json.loads(closed.read_bytes())
    assert payload["source_date"] == "2026-08-08"
    assert payload["generated_at"].startswith("2026-08-09")
    assert main_raw_epoch_validation(payload, source_date="2026-08-08")["eligible"]
    assert _source_quality_receipt(tmp_path / "data", "2026-08-08")["eligible"]
    assert not main_raw_epoch_validation(payload, source_date="2026-08-09")["eligible"]


@pytest.mark.parametrize("failure", ["queue_full", "write", "fsync"])
def test_rejection_persistence_failure_never_publishes_clean_close(
    tmp_path, monkeypatch, failure
):
    c = ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True, path_capture_enabled=True),
        config=ForwardCollectorConfig(output_root=tmp_path),
    )
    c.start()
    if failure == "queue_full":

        def fail(*args):
            raise collector_module.queue.Full

        monkeypatch.setattr(c._rejection_queue, "put_nowait", fail)
    elif failure == "write":
        c._rejection_path.parent.mkdir()
        c._rejection_path.write_text("foreign existing bytes")
    else:

        def fail(*args):
            raise OSError("isolated fsync failure")

        monkeypatch.setattr(collector_module.os, "fsync", fail)
    c.observe_kiwoom_0b(
        "000001", _snapshot(exchange_time="invalid"), realtime_type="0B"
    )
    with pytest.raises(RuntimeError, match="shutdown"):
        c.close()
    snapshot = c.runtime_snapshot().as_dict()
    assert snapshot["collector_lifecycle"] == "close_failed"
    assert not snapshot["timestamp_rejection_ledger"]["sealed"]
    if c._rejection_file is not None:
        c._rejection_file.close()


def test_ws_retains_closed_collector_until_receipt_persistence_succeeds(
    tmp_path, monkeypatch
):
    c, _, _ = _closed_main_rejection_source(tmp_path)
    manager = KiwoomWSManager("offline-token")
    manager._micro_reversion_forward_collector = c

    def fail():
        raise OSError("receipt unavailable")

    monkeypatch.setattr(manager, "_persist_micro_reversion_canary_snapshot", fail)
    assert manager._close_micro_reversion_forward_collector() is False
    assert manager._micro_reversion_forward_collector is c
    monkeypatch.setattr(manager, "_persist_micro_reversion_canary_snapshot", lambda: {})
    assert manager._close_micro_reversion_forward_collector() is True
    assert manager._micro_reversion_forward_collector is None
