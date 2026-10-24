"""Local exact-probe custody continuity; never renews a native signal deadline.

The WS owner transfers its existing buffer under its lock. Main may recognize
that buffer before a new packet arrives only with this same-process receipt.
"""

import math

from src.engine.scalping.reversal_source_diagnostics import observation_binding_valid


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _source_rows(source, *, code, route, item, epoch, now, max_age):
    key = {
        "nxt_only": "_NX|nxt_only",
        "krx_nxt_integrated": "_AL|krx_nxt_integrated",
    }.get(route)
    typed = (source.get("realtime_type_snapshots_by_route") or {}).get(key) or {}
    rows = {}
    for kind in ("0B", "0D"):
        row = typed.get(kind) or {}
        stamp = row.get("observed_epoch")
        if (
            row.get("item") != item
            or row.get("market_route") != route
            or row.get("transport_epoch") != epoch
            or type(row.get("route_sequence")) is not int
            or row["route_sequence"] <= 0
            or not _positive(stamp)
            or not 0 <= now - stamp <= max_age
            or (source.get("last_realtime_type_item") or {}).get(kind) != item
            or (source.get("last_realtime_type_market_route") or {}).get(kind) != route
            or (source.get("last_realtime_type_transport_epoch") or {}).get(kind)
            != epoch
            or (source.get("last_realtime_type_ts") or {}).get(kind) != stamp
        ):
            return None
        rows[kind] = row
    book = rows["0D"].get("orderbook") or {}
    if (
        not _positive(rows["0B"].get("current_price"))
        or not book.get("asks")
        or not book.get("bids")
    ):
        return None
    return rows


def _build_receipt(source, payload, *, epoch, lease, now):
    """Called while the WS owner holds its lock, before moving the exact store."""
    expected = payload.get("native_observation")
    if not observation_binding_valid(expected, now=now) or not lease:
        return None
    event = expected["snapshot"][0]
    code, route, item = (
        payload.get("code"),
        payload.get("market_data_route"),
        event.get("source_item"),
    )
    if (
        lease.get("lease_id") != payload.get("physical_probe_lease_id")
        or lease.get("epoch") != epoch
        or lease.get("removing")
        or not event.get("signal_id")
        or not expected.get("snapshot_sha256")
    ):
        return None
    interval_start = lease.get("interval_started_epoch")
    if not _positive(interval_start) or interval_start > now:
        return None
    rows = _source_rows(
        source, code=code, route=route, item=item, epoch=epoch, now=now, max_age=3.0
    )
    history = source.get("strength_momentum_history") or ()
    if (
        not rows
        or not history
        or any(r["observed_epoch"] < interval_start for r in rows.values())
    ):
        return None
    # Every inherited strength row is stamped by the same REAL producer. Old
    # unlabelled buffers and mixed/reconnected histories cannot gain authority.
    previous = (0.0, 0)
    for row in history:
        stamp, sequence = row.get("ts"), row.get("route_sequence")
        if (
            row.get("item") != item
            or row.get("market_route") != route
            or row.get("transport_epoch") != epoch
            or not _positive(stamp)
            or not interval_start <= stamp <= now
            or type(sequence) is not int
            or sequence <= previous[1]
            or stamp < previous[0]
            or sequence > rows["0B"]["route_sequence"]
        ):
            return None
        previous = (stamp, sequence)
    if previous[1] != rows["0B"]["route_sequence"]:
        return None
    if not any(
        row.get("route_sequence") == event.get("native_sequence") for row in history
    ):
        return None
    return dict(
        schema="native_source_continuity_v1",
        code=code,
        item=item,
        route=route,
        transport_epoch=epoch,
        physical_probe_lease_id=lease["lease_id"],
        observer_pid=expected["observer_pid"],
        observer_start_ticks=expected["observer_start_ticks"],
        signal_id=event["signal_id"],
        snapshot_sha256=expected["snapshot_sha256"],
        original_deadline_epoch=expected["deadline_epoch"],
        original_deadline_perf=expected["deadline_perf"],
        family_sha256=expected.get("family_sha256"),
        native_event_id=event.get("event_id"),
        interval_started_epoch=interval_start,
        adopted_epoch=now,
        source_sequences={k: r["route_sequence"] for k, r in rows.items()},
        source_epochs={k: r["observed_epoch"] for k, r in rows.items()},
        history_count=len(history),
        order_authority=False,
    )


def _source_ready(stock, ws_data, *, now, max_age=3.0):
    """An original still-live claim and current exact data, not historical validity."""
    stock, ws_data = stock or {}, ws_data or {}
    receipt = stock.get("_zero_base_source_continuity")
    if not isinstance(receipt, dict) or receipt != ws_data.get(
        "_zero_base_source_continuity"
    ):
        return False
    expected = stock.get("native_observation")
    if not observation_binding_valid(expected, now=now):
        return False
    event = expected["snapshot"][0]
    if (
        receipt.get("schema") != "native_source_continuity_v1"
        or receipt.get("code") != stock.get("code")
        or receipt.get("route") != stock.get("market_data_route")
        or receipt.get("physical_probe_lease_id")
        != stock.get("physical_probe_lease_id")
        or receipt.get("physical_probe_lease_id") != stock.get("ws_handoff_id")
        or receipt.get("transport_epoch") != ws_data.get("market_data_transport_epoch")
        or receipt.get("transport_epoch") != event.get("native_epoch")
        or receipt.get("item") != event.get("source_item")
        or receipt.get("signal_id") != event.get("signal_id")
        or receipt.get("snapshot_sha256") != expected.get("snapshot_sha256")
        or receipt.get("family_sha256") != expected.get("family_sha256")
        or receipt.get("original_deadline_perf") != expected.get("deadline_perf")
        or receipt.get("original_deadline_epoch") != expected.get("deadline_epoch")
        or receipt.get("observer_pid") != expected.get("observer_pid")
        or receipt.get("observer_start_ticks") != expected.get("observer_start_ticks")
        or not _positive(receipt.get("adopted_epoch"))
        or receipt["adopted_epoch"] > now
    ):
        return False
    rows = _source_rows(
        ws_data,
        code=receipt["code"],
        route=receipt["route"],
        item=receipt["item"],
        epoch=receipt["transport_epoch"],
        now=now,
        max_age=max_age,
    )
    return bool(
        rows
        and all(
            r["route_sequence"] >= receipt["source_sequences"][k]
            and r["observed_epoch"] >= receipt["source_epochs"][k]
            for k, r in rows.items()
        )
    )


def build_receipt(source, payload, *, epoch, lease, now):
    try:
        return _build_receipt(source, payload, epoch=epoch, lease=lease, now=now)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        return None


def source_ready(stock, ws_data, *, now, max_age=3.0):
    try:
        return _source_ready(stock, ws_data, now=now, max_age=max_age)
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        return False
