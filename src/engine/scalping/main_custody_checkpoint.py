"""Source-only account checkpoints, independent of historical economic costs.

No broker requests, custody mutation, terminal inference, or order authority.
The normal account reader records the unchanged journal generation across its
query window. Postclose verifies the native journal and dispatch continuity.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    write_json_object_generation_safe,
    json_artifact_generation_lock,
)

SCHEMA = "main_custody_checkpoint_v1"
_SOURCE_SINK = None


def configure_sink(sink):
    global _SOURCE_SINK
    _SOURCE_SINK = sink


def enqueue(snapshot, *, query_generation):
    """Use the existing bounded writer, with no trading-thread file reads."""
    import copy

    if _SOURCE_SINK is None:
        return "source_gap"
    # Account snapshots own set-valued coverage facts. Normalize before the
    # bounded JSON queue; doing this only in publish is too late to admit it.
    # Keep all members (including unresolved order codes) and caller ownership.
    frozen = {k: sorted(v) if isinstance(v, set) else copy.deepcopy(v)
              for k, v in snapshot.items()}
    answer = _SOURCE_SINK(
        publish_observation,
        frozen,
        query_generation=query_generation,
        observation_category="main_stop",
    )
    return (
        "queued"
        if isinstance(answer, dict) and answer.get("status") == "queued"
        else "source_gap"
    )


def publish_observation(snapshot, *, query_generation):
    """Confirm the durable writer result without altering the hashed document."""
    import os
    result = publish(snapshot, query_generation=query_generation)
    return dict(structured_append_succeeded=True, artifact_sha256=result['sha256'],
        source_date=result['source_date'], producer_pid=os.getpid(),
        source_status=result['status'], runtime_effect=False)


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def journal_generation(path=None):
    path = Path(path or DATA_DIR / "runtime/order_owner_registry.jsonl")
    if path.is_symlink():
        raise ValueError("custody_checkpoint_registry_symlink")
    stat = path.stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns]


def publish(snapshot, *, query_generation, path=None):
    """Persist normalized native facts; incomplete reads are explicit gaps."""
    from src.trading.order.owner_custody_registry import (
        broker_account_key,
        default_order_owner_registry,
    )

    day = (
        datetime.fromtimestamp(snapshot["captured_at"], ZoneInfo("Asia/Seoul"))
        .date()
        .isoformat()
    )
    current = journal_generation()
    events = default_order_owner_registry().verified_events_snapshot()
    if journal_generation() != current:
        raise ValueError("custody_checkpoint_registry_changed")
    clean = {k: sorted(v) if isinstance(v, set) else v for k, v in snapshot.items()}
    complete = (
        query_generation is not None
        and query_generation == current
        and {"KRX", "NXT"} <= set(snapshot.get("successful_exchanges") or [])
        and snapshot.get("inventory_rows_valid") is True
        and snapshot.get("open_order_rows_valid") is True
        and snapshot.get("open_orders_request_succeeded") is True
        and not snapshot.get("unverified_open_order_codes")
    )
    body = dict(
        schema=SCHEMA,
        source_date=day,
        account_key=broker_account_key(),
        status="recorded" if complete else "source_gap",
        broker_snapshot=clean,
        registry_generation=current,
        query_registry_generation=query_generation,
        registry_event_count=len(events),
        registry_tail_hash=events[-1]["event_hash"] if events else "0" * 64,
        runtime_effect=False,
        allowed_runtime_apply=False,
        historical_terminal_or_profit_inferred=False,
    )
    result = dict(body, sha256=digest(body))
    latest = Path(path or DATA_DIR / f"runtime/main_custody_checkpoints/{day}.json")
    immutable = latest.with_name(f"{day}.{result['sha256']}.json")
    with json_artifact_generation_lock(
        immutable, exclusive=True, blocking=True
    ) as lease:
        if immutable.exists():
            if json.loads(immutable.read_text()) != result:
                raise ValueError("custody_checkpoint_immutable_conflict")
        else:
            write_json_object_generation_safe(immutable, result, generation=lease)
    with json_artifact_generation_lock(latest, exclusive=True, blocking=True) as lease:
        if latest.exists():
            prior = json.loads(latest.read_text())
            if prior["broker_snapshot"]["captured_at"] > snapshot["captured_at"]:
                return result
        write_json_object_generation_safe(latest, result, generation=lease)
    return result


def view(checkpoint, registry, by_date, *, day, current_generation, assessed_at=None):
    """Require a complete account checkpoint and all later native dispatches."""
    result = dict(
        status="unknown",
        known_open_count=None,
        blocker="verified_current_custody_checkpoint_missing",
    )
    try:
        from src.trading.order.owner_custody_registry import (
            OrderOwnerRegistry,
            broker_account_key,
            OwnerRegistryError,
        )

        c = checkpoint
        if (
            not isinstance(c, dict)
            or c.get("schema") != SCHEMA
            or c.get("status") != "recorded"
            or c.get("sha256") != digest({k: v for k, v in c.items() if k != "sha256"})
            or c.get("account_key") != broker_account_key()
            or c.get("source_date") > day
            or c.get("query_registry_generation") != c.get("registry_generation")
            or c["registry_generation"][:2] != current_generation[:2]
            or c["registry_generation"][2] > current_generation[2]
        ):
            raise ValueError("custody_checkpoint_binding_invalid")
        snapshot = c["broker_snapshot"]
        at = snapshot["captured_at"]
        if type(at) not in (int, float) or not math.isfinite(at):
            raise ValueError("custody_checkpoint_clock_invalid")
        if (
            datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul")).date().isoformat()
            != c["source_date"]
        ):
            raise ValueError("custody_checkpoint_date_invalid")
        if assessed_at is not None and (
            not math.isfinite(assessed_at) or at > assessed_at
        ):
            raise ValueError("custody_checkpoint_future_source")
        count = c.get("registry_event_count")
        if (
            type(count) is not int
            or not 0 <= count <= len(registry)
            or c.get("registry_tail_hash")
            != (registry[count - 1]["event_hash"] if count else "0" * 64)
        ):
            raise ValueError("custody_checkpoint_journal_prefix_changed")
        if c["source_date"] not in by_date or day not in by_date:
            raise ValueError("since_checkpoint_dispatch_continuity_missing")
        if (
            snapshot.get("inventory_rows_valid") is not True
            or snapshot.get("open_order_rows_valid") is not True
            or snapshot.get("open_orders_request_succeeded") is not True
            or snapshot.get("unverified_open_order_codes")
            or not {"KRX", "NXT"} <= set(snapshot.get("successful_exchanges") or [])
        ):
            raise ValueError("custody_checkpoint_broker_coverage_invalid")
        if any(
            not r.get("coverage_verified") or r.get("unclassified_identities")
            for d, r in by_date.items()
            if c["source_date"] <= d <= day
        ):
            raise ValueError("since_checkpoint_dispatch_continuity_missing")
        # Reconcile broker facts against the journal at capture, then check all
        # subsequent Main activity. Later fills do not rewrite the snapshot.
        state = OrderOwnerRegistry._state(registry[:count])
        current_state = OrderOwnerRegistry._state(registry)
        manual = OrderOwnerRegistry._manual_disposition(registry, c["account_key"])
        symbols = set(snapshot["inventory_by_code"]) | {
            r.get("symbol")
            for r in state.values()
            if r.get("account_key") == c["account_key"]
            and r.get("owner_type") == "main_scalping"
        }
        for code in symbols:
            qty = (snapshot["inventory_by_code"].get(code) or {}).get("qty", 0)
            if type(qty) is not int or qty < 0:
                raise ValueError("custody_checkpoint_position_quantity_invalid")
            projection = OrderOwnerRegistry._reconcile_symbol_quantity_from_state(
                state,
                account_key=c["account_key"],
                symbol=code,
                broker_quantity=qty,
                retired_manual=True,
            )
            retired = {}
            for row in state.values():
                if (
                    row.get("account_key") == c["account_key"]
                    and row.get("symbol") == code
                    and row.get("owner_type") != "main_scalping"
                    and row.get("action") == "NEW"
                ):
                    key = row.get("position_id")
                    retired[key] = retired.get(key, 0) + int(
                        row.get("filled_qty") or 0
                    ) * (1 if row.get("side") == "BUY" else -1)
            retired_quantity = sum(max(0, v) for v in retired.values())
            if (
                projection["external_manual_remainder"] > retired_quantity
                and not manual
            ):
                raise ValueError("custody_checkpoint_external_owner_unverified")
        # Existing Main orders/intents, including uncertain responses, remain
        # blocking. Historical completed-cost gaps are not current custody.
        main_net = {}
        for row in current_state.values():
            if (
                row.get("account_key") == c["account_key"]
                and row.get("owner_type") == "main_scalping"
                and row.get("action") == "NEW"
            ):
                key = row.get("position_id")
                main_net[key] = main_net.get(key, 0) + int(
                    row.get("filled_qty") or 0
                ) * (1 if row.get("side") == "BUY" else -1)
        if any(q < 0 for q in main_net.values()):
            raise ValueError("custody_checkpoint_main_quantity_conflict")
        if any(q != 0 for q in main_net.values()):
            return dict(
                result,
                status="known_open",
                known_open_count=sum(q != 0 for q in main_net.values()),
                blocker="current_main_position_open",
            )
        open_main = [
            r
            for r in current_state.values()
            if r.get("account_key") == c["account_key"]
            and r.get("owner_type") == "main_scalping"
            and r.get("state") != "ORDER_TERMINAL"
        ]
        if open_main:
            return dict(
                result,
                status="known_open",
                known_open_count=len(open_main),
                blocker="current_main_intent_or_order_open",
            )
        # Unmatched open broker orders have no verified Main/manual partition.
        if any(
            any(type(q) is not int or q != 0 for q in v.values())
            for v in snapshot["open_qty_by_code"].values()
        ):
            raise ValueError("custody_checkpoint_open_order_partition_unknown")
        return dict(
            status="verified_empty",
            known_open_count=0,
            blocker=None,
            checkpoint_sha256=c["sha256"],
            registry_tail_hash=registry[-1]["event_hash"] if registry else None,
            historical_terminal_or_profit_inferred=False,
        )
    except (KeyError, TypeError, ValueError, AttributeError, OwnerRegistryError) as exc:
        return dict(result, blocker=str(exc))
