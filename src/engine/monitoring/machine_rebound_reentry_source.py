"""Normalize bounded owner journals and reuse attribution's decoded quote index."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring.machine_rebound_reentry_evaluation import (
    AUTHORITY,
    SOURCE_SCHEMA,
    aware,
)
from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.trading.config.machine_rebound_reentry_policy import (
    digest,
    numeric,
    scope_identity,
)
from src.trading.order.tick_utils import move_price_by_ticks
from src.trading.market.machine_rebound_reentry import (
    immediate_plan_feasible,
    rising_confirmation,
)
from src.utils.jsonl_io import read_json_object_strict


def load_anchors(
    target_date: str, report_root: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = report_root / "machine_rebound_reentry_observations" / target_date
    paths = sorted(
        {
            path.with_suffix("") if path.suffix == ".gz" else path
            for pattern in ("*.json", "*.json.gz")
            for path in root.glob(pattern)
        }
    )
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    gaps: Counter[str] = Counter()
    for path in paths:
        try:
            frame = read_json_object_strict(path)
            content_hash = frame.pop("content_sha256", None)
            if (
                frame.get("schema")
                not in {
                    "machine_rebound_owner_decision_v1",
                    "machine_rebound_owner_terminal_v1",
                }
                or digest(frame) != content_hash
                or frame.get("trade_date") != target_date
                or any(frame.get(key) != value for key, value in AUTHORITY.items())
                or aware(frame.get("observed_at")) is None
            ):
                raise ValueError("journal_contract_invalid")
            groups[frame["opportunity_id"]].append(frame)
        except (OSError, ValueError, KeyError, TypeError):
            gaps["journal_contract_invalid"] += 1
    anchors = []
    cases = []
    for opportunity, frames in groups.items():
        frames.sort(key=lambda frame: aware(frame["observed_at"]))
        terminals = [
            frame
            for frame in frames
            if frame.get("schema") == "machine_rebound_owner_terminal_v1"
        ]
        frames = [
            frame
            for frame in frames
            if frame.get("schema") == "machine_rebound_owner_decision_v1"
        ]
        if not frames:
            gaps["orphan_terminal_receipt"] += 1
            continue
        first = frames[0]
        # Raw decode/windows only for the first causal candidate and control,
        # never once per repeated poll or once per arm.
        early = next(
            (
                frame
                for frame in frames
                if frame.get("baseline_blocked") is True
                and frame.get("market_fresh") is True
                and rising_confirmation(frame)
                and immediate_plan_feasible(frame)
            ),
            None,
        )
        control = next(
            (frame for frame in frames if frame.get("baseline_blocked") is False), None
        )
        chosen = {
            frame["observed_at"]: frame
            for frame in (first, early, control)
            if frame is not None
        }
        case = {
            **scope_identity(first),
            "trade_date": target_date,
            "opportunity_id": opportunity,
            "basis_notional_krw": first.get("basis_notional_krw"),
            "frames": [],
            "observed_poll_count": len(frames),
            "baseline_no_entry_receipt": terminals[0] if len(terminals) == 1 else None,
        }
        first_at = aware(first["observed_at"])
        # Owner exits are not 30-minute markouts. Both hypotheses share the
        # same regular-session observation end, including a later resumption.
        deadline = datetime.combine(
            first_at.date(), time(15, 30), tzinfo=first_at.tzinfo
        )
        if first.get("session") not in {"KRX_REGULAR", "SOR_REGULAR", "NXT_REGULAR"}:
            deadline = first_at + timedelta(minutes=30)
        for frame in chosen.values():
            frame = {**frame, "parent_horizon_end": deadline.isoformat()}
            anchor_id = (
                f"rebound:{digest({'parent': opportunity, 'at': frame['observed_at']})}"
            )
            frame["anchor_id"] = anchor_id
            case["frames"].append(frame)
            anchors.append(
                {
                    "anchor_id": anchor_id,
                    "lifecycle_id": opportunity,
                    "owner": frame["owner"],
                    "scope_id": frame["scope_id"],
                    "symbol": frame["symbol"],
                    "session": frame["session"],
                    "expected_venues": [frame["venue"]],
                    "expected_session_buckets": [frame["session"]],
                    "anchor_at": frame["observed_at"],
                    "anchor_price": frame["reference_price"],
                    "lifecycle_stage": "entry",
                    "anchor_role": "source_only_rebound_owner_decision",
                    "actual_order_submitted": False,
                    "owner_lifecycle_contract_valid": True,
                    "owner_policy_tuning_eligible": False,
                    "rebound_source_frame": frame,
                }
            )
        cases.append(case)
    return anchors, {
        "schema": SOURCE_SCHEMA,
        **AUTHORITY,
        "cases": cases,
        "gap_counts": dict(gaps),
        "journal_artifact_count": len(paths),
        "normalized_anchor_count": len(anchors),
        "raw_decode_passes_added": 0,
        "independent_schedules_added": 0,
    }


def project_outcome(
    frame: dict[str, Any], window: dict[str, Any], *, source_ready: bool
) -> dict[str, Any]:
    result = {**frame, "source_quality_eligible": source_ready}
    pending = {"status": "right_censored", "actual_order_submitted": False}
    result["modeled_owner_exit"] = pending
    if not source_ready:
        return result
    contract = frame.get("owner_contract") or {}
    if contract.get("recipe") != "regular_two_leg_fixed_tick_no_stop_v1":
        pending["status"] = "owner_exit_replay_gap"
        return result
    legs = frame.get("legs") or []
    if not legs or digest(contract) != frame.get("owner_contract_sha256"):
        pending["status"] = "owner_exit_replay_gap"
        return result
    cost = comparison_cost_contract(frame["trade_date"])
    if frame.get("cost_contract") != cost:
        pending["status"] = "cost_contract_gap"
        return result
    checkpoint = frame.get("checkpoint") or {}
    ask, depth = numeric(checkpoint.get("best_ask")), numeric(
        checkpoint.get("best_ask_quantity")
    )
    total = sum(int(leg["quantity"]) for leg in legs)
    if not immediate_plan_feasible(frame):
        # Passive/partial fills need a cancel-aware limit replay; never pretend
        # two legs filled at a common price simply because one did.
        pending["status"] = "passive_or_partial_entry_replay_gap"
        return result
    start = aware(frame["observed_at"])
    end = aware(frame.get("parent_horizon_end"))
    if start is None or end is None or start >= end:
        pending["status"] = "common_horizon_contract_gap"
        return result
    target = move_price_by_ticks(int(ask), int(contract["target_ticks"]))
    points = sorted(
        window.get("depth_points") or [], key=lambda point: point["timestamp"]
    )
    received_ms = numeric(checkpoint.get("depth_received_at_ms"))
    # Runtime transport_epoch starts at 1, whereas raw sequence_epoch is a
    # process-unique time_ns value. They are different namespaces. Both use
    # the same normalized 0D packet's received_at_ms; bind by that exact packet
    # and reject ambiguous epochs instead of equating the counters.
    entry_points = [
        point
        for point in points
        if received_ms is not None
        and round(point["timestamp"].timestamp() * 1000) == received_ms
        and point.get("best_bid") == checkpoint.get("best_bid")
        and point.get("best_ask") == ask
        and point.get("best_ask_qty") == depth
    ]
    epochs = {point.get("sequence_epoch") for point in entry_points}
    entry_point = entry_points[0] if len(epochs) == 1 and entry_points else None
    if (
        entry_point is None
        or not 0 <= (start - entry_point["timestamp"]).total_seconds() <= 1.5
        or entry_point.get("best_ask") != ask
        or entry_point.get("best_bid") != checkpoint.get("best_bid")
        or entry_point.get("best_ask_qty") != depth
    ):
        result["source_quality_eligible"] = False
        pending["status"] = "live_quote_raw_reconciliation_gap"
        return result
    raw_epoch = entry_point["sequence_epoch"]
    points = [point for point in points if point.get("sequence_epoch") == raw_epoch]
    result["epoch_binding"] = {
        "contract": "unique_exact_received_0d_quote_v1",
        "runtime_transport_epoch": checkpoint.get("sequence_epoch"),
        "raw_sequence_epoch": raw_epoch,
        "depth_received_at_ms": received_ms,
    }
    # Target touch is modeled exit, not execution quality evidence. Requiring
    # full displayed depth keeps full/partial economics separate.
    hit = next(
        (
            point
            for point in points
            if start < point["timestamp"] <= end
            and (numeric(point.get("best_bid")) or 0) >= target
            and (numeric(point.get("best_bid_qty")) or 0) >= total
        ),
        None,
    )
    if hit is None:
        return result
    result["modeled_owner_exit"] = {
        "status": "completed_full_position",
        "actual_order_submitted": False,
        "evidence_class": "modeled_owner_exit",
        "entry_at": frame["observed_at"],
        "exit_at": hit["timestamp"].isoformat(),
        "entry_price": ask,
        "exit_price": target,
        "quantity": total,
        "fill_class": "modeled_full_position",
        "net_profit_krw": (target - ask) * total
        - ask * total * cost["round_trip_cost_pct"] / 100.0,
        "cancel_contract": "immediate_marketable_only_existing_unfilled_cancel_unchanged",
        "no_stop_forced_exit": False,
    }
    return result
