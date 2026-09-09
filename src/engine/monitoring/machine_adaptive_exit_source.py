"""Natural owner-state -> complete census -> ordered research paths.

Called inside attribution, reusing its single canonical stream read. Never
opens a broker connection or creates a second market collector. Legacy source
loss, empty execution scopes and research-only catalog rows are distinct.
"""

from __future__ import annotations

from collections import Counter
from bisect import bisect_right
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.source import OwnerScope, validate_source_day
from src.trading.order.adaptive_exit.models import finite, positive_int
from src.trading.order.adaptive_exit.target_group import group_from_observation
from src.trading.order.tick_utils import get_tick_size
from .widget_comparison_cost import comparison_cost_contract

KST = ZoneInfo("Asia/Seoul")
HORIZON_SEC = 1200  # Fixed source-only comparison horizon, not a live timeout.
MAX_ANCHORS = 64
MAX_ROWS_PER_ANCHOR = 30000
MAX_TOTAL_ROWS = 120000
CADENCE_MS = 1000
MAX_QUOTE_AGE_MS = 1500
TARGET_FIELD = "adaptive_exit_target_observations"
SAMSUNG_STATES = {
    "samsung:morning": (
        "samsung_morning_one_share_state.json",
        "samsung_morning_two_leg_state_v2",
    ),
    "samsung:morning_sor_reentry": (
        "samsung_morning_sor_reentry_state.json",
        "samsung_morning_sor_reentry_two_leg_state_v1",
    ),
    "samsung:midday": (
        "samsung_midday_one_share_state.json",
        "samsung_midday_two_leg_state_v2",
    ),
    "samsung:afternoon": (
        "samsung_afternoon_one_share_state.json",
        "samsung_afternoon_two_leg_state_v2",
    ),
}


def _signed(payload):
    return payload | {"canonical_sha256": canonical_sha256(payload)}


def _valid_census(payload, target_date):
    try:
        return (
            isinstance(payload, dict)
            and payload.get("schema") == "machine_adaptive_exit_owner_census_v1"
            and payload.get("target_date") == target_date
            and payload.get("authority") == AUTHORITY
            and all(payload["authority"].get(k) is v for k, v in AUTHORITY.items())
            and isinstance(payload.get("scopes"), dict)
            and payload.get("canonical_sha256") == canonical_sha256(payload)
        )
    except (TypeError, ValueError, OverflowError):
        return False


def _ms(value):
    stamp = datetime.fromisoformat(str(value))
    if stamp.utcoffset() is None:
        raise ValueError("naive_timestamp")
    return int(stamp.timestamp() * 1000)


def _read(path):
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("state_not_mapping")
        return payload, {
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "status": "loaded",
        }
    except (OSError, ValueError, UnicodeError):
        return None, {
            "path": str(path),
            "sha256": None,
            "status": "state_missing_or_invalid",
        }


def _empty(scope, target_date):
    return {
        "scope": asdict(scope),
        "execution_scope": True,
        "complete": False,
        "expected_episode_lots": {},
        "lot_paths": [],
        "source_trading_dates": [target_date],
        "lots": [],
        "shared_target_groups": {},
        "errors": [],
        "unfilled_buy_count": 0,
    }


def _target_receipts(records):
    found = {}
    for record in records:
        if record.get("adaptive_exit_source_gap"):
            raise ValueError(str(record["adaptive_exit_source_gap"]))
        receipts = record.get(TARGET_FIELD, {})
        if not isinstance(receipts, dict):
            raise ValueError("target_receipt_container_invalid")
        for key, receipt in receipts.items():
            if (
                not isinstance(receipt, dict)
                or receipt.get("schema")
                != "machine_adaptive_exit_target_observation_v1"
                or receipt.get("canonical_sha256") != canonical_sha256(receipt)
                or receipt.get("authority") != AUTHORITY
                or any(
                    receipt.get("authority", {}).get(k) is not v
                    for k, v in AUTHORITY.items()
                )
            ):
                raise ValueError("target_receipt_schema_hash_authority_invalid")
            target = receipt["target"]
            if (
                not isinstance(target, dict)
                or not isinstance(receipt.get("entries"), list)
                or not receipt["entries"]
                or any(not isinstance(e, dict) for e in receipt["entries"])
                or not isinstance(target.get("order_date"), str)
                or not isinstance(target.get("order_no"), str)
            ):
                raise ValueError("target_receipt_entry_schema_invalid")
            if key != target["order_date"] + ":" + target["order_no"]:
                raise ValueError("target_receipt_order_identity_invalid")
            if key in found and found[key] != receipt:
                raise ValueError("conflicting_target_receipts")
            found[key] = receipt
    return list(found.values())


def _add_lot(census, *, scope, eid, lid, entry, receipts, state_hash, target_date):
    """Count every known filled lot before deciding path support."""
    lots = census["expected_episode_lots"].setdefault(eid, [])
    if lid in lots:
        raise ValueError("duplicate_owner_episode_lot")
    lots.append(lid)
    row = {
        "episode_id": eid,
        "lot_id": lid,
        "disposition": "source_invalid",
        "reason": "first_fill_or_target_receipt_missing",
        "state_sha256": state_hash,
        "source_date": target_date,
        "entry_binding": dict(entry),
    }
    census["lots"].append(row)
    matches = [
        r
        for r in receipts
        for e in r["entries"]
        if e.get("episode_id") == eid and e.get("lot_id") == lid
    ]
    if len(matches) != 1:
        _record_shared_targets(census, matches, scope, state_hash, target_date)
        if matches:
            row.update(
                disposition="unsupported_policy_epoch",
                reason="target_replacement_or_aggregated_lot_epoch",
            )
        return
    receipt = matches[0]
    _record_shared_targets(census, matches, scope, state_hash, target_date)
    try:
        if receipt["scope"] != asdict(scope):
            raise ValueError("target_scope_mismatch")
        frozen = next(
            e
            for e in receipt["entries"]
            if e["episode_id"] == eid and e["lot_id"] == lid
        )
        if any(
            frozen.get(k) != entry.get(k)
            for k in ("order_date", "order_no", "quantity", "price")
        ):
            raise ValueError("entry_fill_changed_after_target_epoch")
        clock = frozen["first_fill_observation"]
        if (
            not isinstance(clock, dict)
            or clock.get("schema") != "machine_first_fill_observation_v1"
            or clock.get("timestamp_provenance")
            != "broker_reconciliation_observation_not_exchange_fill_time"
            or clock.get("status") != "first_fill_observed_not_exchange_time"
        ):
            raise ValueError("first_fill_observation_unavailable")
        first = _ms(clock["first_observed_at"])
        uncertainty = (
            first - _ms(clock["last_zero_observed_at"])
            if clock.get("last_zero_observed_at")
            else None
        )
        if uncertainty is not None and uncertainty < 0:
            raise ValueError("first_fill_clock_bound_invalid")
        ack = _ms(receipt["target_ack_observed_at"])
        if datetime.fromtimestamp(first / 1000, KST).date().isoformat() != target_date:
            raise ValueError("entry_outside_target_date")
        if not first <= ack < first + HORIZON_SEC * 1000:
            raise ValueError("target_clock_or_comparison_horizon_invalid")
        target = receipt["target"]
        if (
            entry["order_date"] != target_date
            or target["order_date"] != target_date
            or not isinstance(entry["order_no"], str)
            or not entry["order_no"]
            or not positive_int(entry["quantity"])
            or not finite(entry["price"])
            or entry["price"] <= 0
        ):
            raise ValueError("entry_identity_or_fill_invalid")
        if len(receipt["entries"]) != 1 or target["quantity"] != entry["quantity"]:
            row.update(
                disposition="unsupported_policy_epoch",
                reason="aggregated_target_partial_cancel_adapter_required",
            )
            return
        if frozen["quantity"] != frozen["requested_quantity"]:
            row.update(
                disposition="unsupported_policy_epoch",
                reason="partial_buy_fill_not_full_fill_population",
            )
            return
        if receipt["entry_policy_hash"] != canonical_sha256(receipt["entry_policy"]):
            raise ValueError("entry_policy_hash_mismatch")
        cost = comparison_cost_contract(target_date)
        position = {
            "owner_id": scope.owner,
            "scope_key": scope.key,
            "episode_id": eid,
            "lot_id": lid,
            "position_epoch": receipt["canonical_sha256"],
            "first_fill_at_ms": first,
            "open_qty": entry["quantity"],
            "entry_price": entry["price"],
            "original_target": target["price"],
            "round_trip_cost_pct": cost["round_trip_cost_pct"],
            "cost_contract_hash": cost["contract_sha256"],
            "tick_size": get_tick_size(entry["price"]),
        }
        from src.trading.order.adaptive_exit.source import normalize_position

        normalize_position(position, scope=scope)
        row.update(
            disposition="pending_ordered_path",
            reason="ordered_post_target_source_pending",
            path_seed={
                "position": position,
                "entry_policy_hash": receipt["entry_policy_hash"],
                "entry_order_key": entry["order_date"] + ":" + entry["order_no"],
                "target_order_key": target["order_date"] + ":" + target["order_no"],
                "target_ack_at_ms": ack,
                "horizon_end_ms": first + HORIZON_SEC * 1000,
                "cost_contract": cost,
                "owner_receipt_hash": receipt["canonical_sha256"],
                "clock_basis": "local_first_fill_and_ack_observations_not_exchange_time",
                "first_fill_observation_uncertainty_ms": uncertainty,
            },
        )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        row["reason"] = str(exc)


def _record_shared_targets(census, receipts, scope, state_hash, target_date):
    for receipt in receipts:
        if len(receipt["entries"]) < 2:
            continue
        key = receipt["target"]["order_date"] + ":" + receipt["target"]["order_no"]
        groups = census.setdefault("shared_target_groups", {})
        if key in groups:
            continue
        record = {
            "source_date": target_date,
            "source_hash": receipt["canonical_sha256"],
            "state_sha256": state_hash,
            "status": "source_invalid",
            "reason": "shared_target_source_binding_invalid",
            "live_partial_cancel_supported": False,
            "current_target_epoch_verified": False,
            "authority": dict(AUTHORITY),
        }
        groups[key] = record
        try:
            group = group_from_observation(receipt, scope=scope)
            record.update(
                group=group.to_payload(),
                status="source_binding_pending_owner_census",
                reason="partial_cancel_coordinator_and_allocation_not_connected",
            )
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
            record["reason"] = str(exc)


def _finalize_shared_targets(census):
    for record in census.get("shared_target_groups", {}).values():
        if record["status"] != "source_binding_pending_owner_census":
            continue
        group = record["group"]
        matching = [r for r in census["lots"] if r["episode_id"] == group["episode_id"]]
        actual = {r["lot_id"]: r.get("entry_binding", {}) for r in matching}
        if (
            not census["complete"]
            or len(actual) != len(matching)
            or any(
                lot not in actual
                or any(
                    actual[lot].get(k) != v
                    for k, v in {
                        "order_date": order["trading_date"],
                        "order_no": order["order_no"],
                        "quantity": qty,
                        "price": price,
                    }.items()
                )
                for lot, order, qty, first, price in group["lots"]
            )
        ):
            record.update(
                status="source_invalid",
                reason="shared_target_current_owner_lot_mismatch",
            )
        else:
            record["status"] = "source_bound_runtime_unavailable"


def collect_owner_census(*, target_date, catalog, runtime_root, widget_state_path):
    """Read each owner file once; missing state is never healthy no-sample.

    Expected lots are based on filled BUY records, not completed SELL winners.
    New receipt scopes are included even if legacy anchor extraction missed them.
    """
    validate_source_day(target_date)
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date

    profiles = profiles_for_target_date(validate_source_day(target_date))
    catalog = (
        set(catalog)
        | {
            OwnerScope("episode", key, p.symbol, p.policy.route, p.session)
            for key, p in profiles.items()
        }
        | {
            OwnerScope(
                "episode",
                key,
                "005930",
                route,
                "NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR",
            )
            for key in SAMSUNG_STATES
            for route in (("NXT", "SOR") if key == "samsung:morning" else ("SOR",))
        }
    )
    scopes = {scope.key: _empty(scope, target_date) for scope in sorted(catalog)}
    source = {
        "schema": "machine_adaptive_exit_owner_census_v1",
        "target_date": target_date,
        "authority": dict(AUTHORITY),
        "scopes": scopes,
        "state_sources": [],
        "collection_contract": {
            "horizon_sec": HORIZON_SEC,
            "maximum_anchors": MAX_ANCHORS,
            "maximum_rows_per_anchor_per_stream": MAX_ROWS_PER_ANCHOR,
            "maximum_total_anchor_rows": MAX_TOTAL_ROWS,
            "cadence_ms": CADENCE_MS,
            "target_fill_does_not_end_observation": True,
            "new_market_requests": 0,
            "shared_target_metric_contract": {
                "metric_role": "source_quality_gate",
                "decision_authority": "shared_target_topology_diagnostic_only",
                "window_policy": "current_source_date_owner_state",
                "sample_floor": "not_applicable_identity_conservation",
                "primary_decision_metric": "shared_target_groups.status",
                "source_quality_gate": "frozen_target_and_current_owner_lot_binding",
                "forbidden_uses": [
                    "actual_lot_fill_attribution",
                    "live_partial_cancel",
                    "runtime_approval",
                    "positive_ev_claim",
                ],
            },
        },
    }
    # One widget daily envelope contains all episodes for all configured symbols.
    widget, binding = _read(Path(widget_state_path))
    source["state_sources"].append(binding)
    symbol_rows = None
    if widget is not None:
        history = widget.get("history", [])
        matches = (
            ([widget] if widget.get("active_date") == target_date else [])
            + [
                h
                for h in history
                if isinstance(h, dict) and h.get("trade_date") == target_date
            ]
            if isinstance(history, list)
            else []
        )
        if (
            widget.get("schema_version") == 1
            and widget.get("execution_authority")
            == "operator_directed_widget_auto_trade_v1"
            and len(matches) == 1
            and isinstance(matches[0].get("symbols"), dict)
        ):
            symbol_rows = matches[0]["symbols"]
    if symbol_rows is not None:
        for symbol, state in symbol_rows.items():
            try:
                if not isinstance(state, dict):
                    raise ValueError("widget_symbol_state_invalid")
                orders = state["orders"]
                if not isinstance(orders, list) or any(
                    not isinstance(o, dict) for o in orders
                ):
                    raise ValueError("widget_orders_invalid")
                receipt_error = None
                try:
                    receipts = _target_receipts(orders)
                except (KeyError, TypeError, ValueError) as exc:
                    receipts, receipt_error = [], str(exc)
                for order in orders:
                    if (
                        order.get("side") != "BUY"
                        or order.get("broker_accepted") is not True
                    ):
                        continue
                    eid = order.get("parent_entry_signal_id") or order.get("signal_id")
                    parts = str(eid).split(":", 4)
                    if len(parts) != 5 or parts[0] != symbol or parts[2] != "ENTRY":
                        raise ValueError("widget_entry_identity_invalid")
                    entry_day = validate_source_day(parts[1])
                    if entry_day.isoformat() > target_date:
                        raise ValueError("widget_future_entry_identity")
                    if entry_day.isoformat() < target_date:
                        source.setdefault("outside_source_date_custody", []).append(
                            {
                                "owner": "widget",
                                "symbol": symbol,
                                "episode_id": eid,
                                "entry_date": parts[1],
                                "order_no": order.get("order_no"),
                                "disposition": "outside_scope",
                                "reason": "prior_entry_clock_not_recreated",
                            }
                        )
                        continue
                    route = order.get("broker_route") or order.get("route")
                    scope = OwnerScope(
                        "widget", f"actual:{symbol}:{parts[3]}", symbol, route, parts[3]
                    )
                    census = scopes.setdefault(scope.key, _empty(scope, target_date))
                    if receipt_error and receipt_error not in census["errors"]:
                        census["errors"].append(receipt_error)
                    quantity = order.get("filled_qty")
                    if type(quantity) is not int or quantity < 0:
                        raise ValueError("widget_fill_quantity_invalid")
                    if quantity == 0:
                        census["unfilled_buy_count"] += 1
                        continue
                    lid = (
                        "entry"
                        if order.get("signal_id") == eid
                        else f"scale_in:{order.get('scale_in_leg_index')}"
                    )
                    _add_lot(
                        census,
                        scope=scope,
                        eid=eid,
                        lid=lid,
                        entry={
                            "order_date": order.get("order_date"),
                            "order_no": order.get("order_no"),
                            "quantity": quantity,
                            "price": order.get("fill_price"),
                        },
                        receipts=receipts,
                        state_hash=binding["sha256"],
                        target_date=target_date,
                    )
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                for key, census in scopes.items():
                    if (
                        census["scope"]["owner"] == "widget"
                        and census["scope"]["symbol"] == symbol
                    ):
                        census["errors"].append(str(exc))
                source.setdefault("unscoped_errors", []).append(
                    f"widget:{symbol}:{exc}"
                )
    source["owner_envelope_valid"] = {
        "widget": symbol_rows is not None and not source.get("unscoped_errors"),
        "episode_inventory": True,
    }
    for census in scopes.values():
        scope = OwnerScope(**census["scope"])
        if scope.owner != "widget":
            continue
        census["complete"] = bool(
            symbol_rows is not None
            and scope.symbol in symbol_rows
            and scope.profile.startswith("actual:")
            and not census["errors"]
        )
        if not scope.profile.startswith("actual:"):
            census["execution_scope"] = False
            census["errors"].append("not_applicable_nonexecution_scope")
        elif symbol_rows is None:
            census["errors"].append("widget_exact_date_state_missing_or_invalid")
    # Catalog paths are trusted profile registry identities, never artifact-supplied paths.
    cache = {}
    for census in list(scopes.values()):
        scope = OwnerScope(**census["scope"])
        if scope.owner != "episode":
            continue
        if scope.profile in SAMSUNG_STATES:
            filename, schema = SAMSUNG_STATES[scope.profile]
            path = Path(runtime_root) / filename
        elif scope.profile in profiles:
            path = (
                Path(runtime_root) / "low_price_two_leg" / f"{scope.profile}_state.json"
            )
            schema = f"low_price_two_leg_{scope.profile}_state_v1"
        else:
            census["execution_scope"] = False
            census["errors"].append("not_applicable_nonexecution_scope")
            continue
        if path not in cache:
            cache[path] = _read(path)
            source["state_sources"].append(cache[path][1])
        state, binding = cache[path]
        try:
            if (
                not state
                or state.get("schema") != schema
                or state.get("trade_date") != target_date
            ):
                raise ValueError("episode_exact_date_state_missing_or_invalid")
            legs = state["legs"]
            if not isinstance(legs, list) or any(not isinstance(x, dict) for x in legs):
                raise ValueError("episode_leg_census_invalid")
            features = state.get("signal_features") or {}
            if not isinstance(features, dict):
                raise ValueError("episode_signal_features_invalid")
            try:
                receipts = _target_receipts(legs)
            except (KeyError, TypeError, ValueError) as exc:
                receipts = []
                census["errors"].append(str(exc))
            for leg in legs:
                route = leg.get("route") or features.get("route")
                # Low-price/Samsung regular owner has a fixed SOR route in its policy.
                if not route and scope.profile in profiles:
                    route = profiles[scope.profile].policy.route
                if not route and scope.profile in {
                    "samsung:midday",
                    "samsung:afternoon",
                }:
                    route = "SOR"
                if route != scope.route:
                    if route not in ("SOR", "KRX", "NXT"):
                        raise ValueError("episode_route_unknown")
                    continue
                qty = leg.get("buy_filled_qty")
                if type(qty) is not int or qty < 0:
                    raise ValueError("episode_fill_quantity_invalid")
                if not qty:
                    census["unfilled_buy_count"] += 1
                    continue
                _add_lot(
                    census,
                    scope=scope,
                    eid=f"{scope.profile}:{target_date}",
                    lid=leg["leg_id"],
                    entry={
                        "order_date": leg.get("buy_order_date"),
                        "order_no": leg.get("buy_order_no"),
                        "quantity": qty,
                        "price": leg.get("fill_price"),
                    },
                    receipts=receipts,
                    state_hash=binding["sha256"],
                    target_date=target_date,
                )
            census["complete"] = not census["errors"]
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            census["errors"].append(str(exc))
    anchors = []
    for census in scopes.values():
        scope = OwnerScope(**census["scope"])
        _finalize_shared_targets(census)
        for row in census["lots"]:
            if "path_seed" not in row or not census["complete"]:
                continue
            if len(anchors) >= MAX_ANCHORS:
                row.update(
                    disposition="source_invalid",
                    reason="postclose_source_anchor_budget_exhausted",
                )
                continue
            seed = row["path_seed"]
            anchor_id = "adaptive-exit-source:" + canonical_sha256(seed)
            row["anchor_id"] = anchor_id
            anchors.append(
                {
                    "anchor_id": anchor_id,
                    "anchor_at": datetime.fromtimestamp(
                        seed["position"]["first_fill_at_ms"] / 1000, KST
                    ).isoformat(),
                    "symbol": scope.symbol,
                    "expected_venues": [scope.route],
                    "expected_session_buckets": [
                        "SOR_REGULAR" if scope.route == "SOR" else scope.session
                    ],
                    "adaptive_exit_source_only": True,
                }
            )
    return source, anchors


def bind_ordered_paths(source, windows, *, source_contract_gap=None, evaluated_at=None):
    """Attribution already validated schema/partition/exclusions. No interpolation.

    Regular one-second as-of sampling requires an actual past quote and trade,
    full depth and one epoch. Future rows cannot fill gaps in earlier samples.
    The common horizon is independent of realized target completion.
    """
    from src.trading.market.confirmation_window import build_confirmation_window

    for census in source["scopes"].values():
        for row in census["lots"]:
            seed = row.pop("path_seed", None)
            if seed is None or "anchor_id" not in row or not census["complete"]:
                continue
            try:
                if (
                    evaluated_at is not None
                    and int(evaluated_at.timestamp() * 1000) < seed["horizon_end_ms"]
                ):
                    row.update(
                        disposition="pending_declared_window",
                        reason="common_horizon_not_yet_due",
                    )
                    continue
                window = windows.get(row["anchor_id"], {})
                if source_contract_gap or window.get("adaptive_exit_source_overflow"):
                    raise ValueError(
                        source_contract_gap or "postclose_source_row_budget_exhausted"
                    )
                depths = sorted(
                    window.get("raw_depth_rows", []),
                    key=lambda r: _ms(r["local_receive_timestamp"]),
                )
                trades = sorted(
                    window.get("raw_market_rows", []),
                    key=lambda r: _ms(r["local_receive_timestamp"]),
                )
                p = seed["position"]
                scope = OwnerScope(**census["scope"])
                item = (
                    scope.symbol + {"KRX": "", "NXT": "_NX", "SOR": "_AL"}[scope.route]
                )
                # Canonical MarketStreamPoint V3 stores symbol+venue rather
                # than a wire item. Project only that already-validated exact
                # route; never borrow a depth item's identity for another row.
                for trade in trades:
                    if (
                        trade.get("symbol") != scope.symbol
                        or trade.get("venue") != scope.route
                        or trade.get("schema")
                        != "scalp_micro_reversion_market_stream_point_v3"
                        or trade.get("realtime_type") != "0B"
                        or trade.get("path_order_status") != "accept"
                        or trade.get("path_consumer_eligible") is not True
                        or trade.get("item", item) != item
                    ):
                        raise ValueError(
                            "canonical_market_route_or_order_contract_invalid"
                        )
                trades = [dict(t, item=item) for t in trades]
                if any(d.get("item") != item for d in depths):
                    raise ValueError("canonical_depth_route_mismatch")
                depth_times = [_ms(d["local_receive_timestamp"]) for d in depths]
                trade_times = [_ms(t["local_receive_timestamp"]) for t in trades]
                start, end = p["first_fill_at_ms"], seed["horizon_end_ms"]
                points = []
                di = ti = 0
                source_epoch = None
                for at in range(start, end + 1, CADENCE_MS):
                    while (
                        di < len(depths)
                        and _ms(depths[di]["local_receive_timestamp"]) <= at
                    ):
                        di += 1
                    while (
                        ti < len(trades)
                        and _ms(trades[ti]["local_receive_timestamp"]) <= at
                    ):
                        ti += 1
                    if not di or not ti:
                        raise ValueError("ordered_depth_or_trade_left_boundary_missing")
                    d = depths[di - 1]
                    epoch = d["sequence_epoch"]
                    if source_epoch is not None and epoch != source_epoch:
                        raise ValueError("ordered_path_epoch_changed")
                    source_epoch = epoch
                    # Whole one-second window plus its left watermark. A fixed
                    # 120-row tail would make high-rate valid streams fail just
                    # because more than 120 trades arrived within one second.
                    left_di = max(0, bisect_right(depth_times, at - 1000) - 1)
                    left_ti = max(0, bisect_right(trade_times, at - 1000) - 1)
                    feature = build_confirmation_window(
                        depth_rows=depths[left_di:di],
                        trade_rows=trades[left_ti:ti],
                        item=d["item"],
                        epoch=epoch,
                        checkpoint_at_ms=at,
                        maximum_age_ms=MAX_QUOTE_AGE_MS,
                    )
                    if feature.get("source_quality_status") != "eligible":
                        raise ValueError(
                            "ordered_past_window_source_gap:"
                            + ",".join(feature.get("source_gap_reasons", []))
                        )
                    levels = [
                        (
                            (level["price"], level["quantity"])
                            if isinstance(level, dict)
                            else (level[1], level[2])
                        )
                        for level in d["bid_levels"]
                    ]
                    left_bid = feature["anchor_depth"]["bid"]
                    supportive = (
                        d["best_bid"] >= left_bid
                        and feature["aggressive_buy_trade_backed_ratio"] > 0
                        and feature["refill_ratio"] <= 1
                    )
                    points.append(
                        {
                            "clock": {"now_ms": at, "verified_halt_ms": 0},
                            "snapshot": {
                                "observed_at_ms": at,
                                "quote_at_ms": _ms(d["local_receive_timestamp"]),
                                "source_epoch": str(epoch),
                                "sequence": len(points) + 1,
                                "quote_sequence": d["series_sequence"],
                                "source_hash": canonical_sha256(
                                    {"depth": d, "feature": feature}
                                ),
                                "scope_key": p["scope_key"],
                                "position_epoch": p["position_epoch"],
                                "best_ask": d["best_ask"],
                                "bid_levels": levels,
                                "supportive": supportive,
                                "improvement_bps": (d["best_bid"] / left_bid - 1)
                                * 10000,
                            },
                        }
                    )
                path = _signed(
                    seed
                    | {
                        "schema": "machine_adaptive_exit_lot_path_v1",
                        "authority": dict(AUTHORITY),
                        "observations": points,
                        "sequence_provenance": "as_of_checkpoint_ordinal_raw_sequences_in_source_hash",
                        "support_contract": "past_one_second_bid_nondecay_trade_backing_refill_v1",
                    }
                )
                census["lot_paths"].append(path)
                row.update(
                    disposition="eligible",
                    reason="ordered_modeled_path_bound_not_actual_exit",
                )
            except (KeyError, TypeError, ValueError, OverflowError, IndexError) as exc:
                row.update(disposition="source_invalid", reason=str(exc))
        census["disposition_counts"] = dict(
            Counter(row["disposition"] for row in census["lots"])
        )
        census["conservation_valid"] = sum(
            census["disposition_counts"].values()
        ) == sum(len(lots) for lots in census["expected_episode_lots"].values())
    return _signed(source)


def _valid_daily_scope(old, current, day):
    """A self hash does not prove that daily census conservation is valid."""
    if (
        old.get("scope") != current["scope"]
        or old.get("source_trading_dates") != [day]
        or not isinstance(old.get("expected_episode_lots"), dict)
        or not isinstance(old.get("lot_paths"), list)
        or not isinstance(old.get("lots"), list)
    ):
        return False
    expected = []
    for eid, lots in old["expected_episode_lots"].items():
        if (
            not isinstance(eid, str)
            or not eid
            or not isinstance(lots, list)
            or not lots
            or any(not isinstance(lot, str) or not lot for lot in lots)
            or len(set(lots)) != len(lots)
        ):
            return False
        expected.extend((eid, lot) for lot in lots)
    observed = []
    for row in old["lots"]:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("episode_id"), str)
            or not isinstance(row.get("lot_id"), str)
            or not isinstance(row.get("disposition"), str)
            or not row["disposition"]
            or row.get("source_date") != day
        ):
            return False
        observed.append((row["episode_id"], row["lot_id"]))
    return len(observed) == len(set(observed)) and set(observed) == set(expected)


def merge_census_history(current, *, report_root, maximum_days=20):
    """Accumulate consecutive observed source days from the existing parent.

    Missing days are not zero-yield days. Current owner state is never used to
    reconstruct a historical policy, fill clock or post-target price path.
    """
    from src.utils.market_day import is_krx_trading_day
    from copy import deepcopy

    result = deepcopy(current)
    day = validate_source_day(current["target_date"])
    history = []
    for _ in range(maximum_days - 1):
        day -= timedelta(days=1)
        while day >= validate_source_day("2026-06-05") and not is_krx_trading_day(day):
            day -= timedelta(days=1)
        if day < validate_source_day("2026-06-05"):
            break
        path = (
            Path(report_root)
            / "machine_microstructure_attribution"
            / f"machine_microstructure_attribution_{day.isoformat()}.json"
        )
        parent, binding = _read(path)
        child = (parent or {}).get("rolling_policy_research_v2", {})
        prior = child.get("natural_owner_census", {}) if isinstance(child, dict) else {}
        if not _valid_census(prior, day.isoformat()):
            break
        history.append((prior, binding))
    for key, census in result["scopes"].items():
        if not census["complete"]:
            continue
        bindings = []
        for prior, binding in history:
            old = prior.get("scopes", {}).get(key, {})
            if not isinstance(old, dict) or old.get("complete") is not True:
                break
            if not _valid_daily_scope(old, census, prior["target_date"]):
                census.setdefault("history_errors", []).append(
                    "historical_scope_contract_invalid"
                )
                break
            if set(census["expected_episode_lots"]).intersection(
                old["expected_episode_lots"]
            ):
                census["errors"].append("historical_duplicate_episode_identity")
                census["complete"] = False
                break
            census["expected_episode_lots"].update(
                deepcopy(old["expected_episode_lots"])
            )
            census["lot_paths"] = deepcopy(old["lot_paths"]) + census["lot_paths"]
            census["lots"] = deepcopy(old["lots"]) + census["lots"]
            census["source_trading_dates"].insert(0, prior["target_date"])
            bindings.append(binding)
        census["history_bindings"] = bindings
        census["disposition_counts"] = dict(
            Counter(row["disposition"] for row in census["lots"])
        )
        census["conservation_valid"] = sum(
            census["disposition_counts"].values()
        ) == sum(len(lots) for lots in census["expected_episode_lots"].values())
    result["aggregation"] = "consecutive_observed_owner_days_not_missing_day_imputation"
    return _signed(result)


def propose_study_contract(source):
    """Versioned research proposals, deliberately NOT an approval envelope.

    Frozen bounded grid is outcome-independent. Two observed dates permit a
    train/holdout diagnostic, not live approval. Exact activation floors and
    execution readiness still belong to the separately approved envelope.
    """
    configs = {}
    for key, census in source["scopes"].items():
        days = census["source_trading_dates"]
        if len(days) < 2:
            continue
        base = {
            "model_id": "research_base_v1",
            "cancel_latency_ms": 500,
            "submit_latency_ms": 500,
            "sell_ttl_ms": 5000,
            "maximum_sell_attempts": 2,
            "depth_participation": 0.5,
            "extra_sell_cost_pct": 0.0,
            "target_queue_confirmations": 2,
            "terminal_residual": "unresolved_not_zero",
            "horizon_close_lead_ms": 15000,
        }
        stress = base | {
            "model_id": "research_stress_v1",
            "cancel_latency_ms": 1500,
            "submit_latency_ms": 1500,
            "depth_participation": 0.25,
            "extra_sell_cost_pct": 0.02,
            "target_queue_confirmations": 3,
        }
        template = {
            "mode": "time_progress_exit",
            "soft_sec": 60,
            "extension_sec": 30,
            "minimum_progress": 0.5,
            "minimum_improvement_bps": 1.0,
            "hard_wall_sec": None,
            "loss_budget_pct": 1.0,
            "max_quote_age_ms": MAX_QUOTE_AGE_MS,
            "max_observation_gap_ms": CADENCE_MS + MAX_QUOTE_AGE_MS,
            "trail": None,
            "runner_lot_ids": [],
        }
        grid = [template | {"soft_sec": soft} for soft in (60, 120, 180)]
        # Lot roles are source census, never selected by subsequent profit.
        runner_roles = sorted(
            {
                lots[-1]
                for lots in census["expected_episode_lots"].values()
                if len(lots) > 1
            }
        )
        for mode in ("fast_partial_trailing", "time_progress_and_trailing"):
            if runner_roles:
                grid.append(
                    template
                    | {
                        "mode": mode,
                        "runner_lot_ids": runner_roles,
                        "trail": {
                            "fast_sec": 30,
                            "min_progress": 0.75,
                            "gap_ticks": 1,
                            "transition_buffer_ticks": 1,
                            "minimum_net_cushion_pct": 0.01,
                        },
                    }
                )
        configs[key] = {
            "parameter_grid": grid,
            "maximum_candidates": 5,
            "execution_models": [base, stress],
            "rolling_trading_days": 20,
            "evaluation": {
                "train_end": days[-2],
                "holdout_start": days[-1],
                "holdout_end": days[-1],
                "minimum_unique_episodes": 2,
                "minimum_holdout_episodes": 1,
                "minimum_observed_days": 2,
                "minimum_resolved_coverage_pct": 80,
                "maximum_censored_pct": 20,
                "minimum_absolute_uplift_pct_points": 0.000001,
                "maximum_p10_deterioration_pct_points": 0.0,
            },
        }
    return _signed(
        {
            "schema": "machine_adaptive_exit_study_contract_v1",
            "version": "outcome_independent_research_grid_v1",
            "authority": dict(AUTHORITY),
            "target_date": source["target_date"],
            "evaluation_authority": "provisional_research_screening_not_activation",
            "source_only_risk_values_not_approved_envelope": True,
            "execution_assumptions_not_measured_broker_quality": True,
            "scopes": configs,
        }
    )
