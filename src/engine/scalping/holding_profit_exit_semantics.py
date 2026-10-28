"""Read-only semantic checks for the real main trailing-profit exit chain."""

from __future__ import annotations

from collections import Counter, defaultdict
import ast
import re
from datetime import datetime
import hashlib
import json
import math
from typing import Any, Callable
from zoneinfo import ZoneInfo

from src.engine.ai.holding_exit_vote import (
    PATH_POLICY_BY_MARKET,
    input_snapshot_id,
    path_signal_snapshot,
)
from src.engine.scalping.trailing_threshold_policy import market_type_at
from src.engine.scalping.trailing_exit_decision import EXIT_WAIT_STAGES
from src.engine.scalping.trailing_mechanical_policy import (
    classifier_hash,
    market_values_hash,
    CLASSIFIER_VERSION,
)

KST = ZoneInfo("Asia/Seoul")
LIFECYCLE_STATES = {
    "signal_observed",
    "deferred",
    "guard_wait",
    "pending_submit",
    "pending_terminal",
    "completed",
}
ECONOMICS_STATES = {"pending", "verified", "unavailable"}


def historical_buy_gap_resolution(report, *, data_root, accepted_position_ids, now):
    """Resolve only original missing-decision lineage, after native re-audit.

    The caller is the Sentinel producer. BUY receipts can restore future
    collection, but cannot manufacture the missing decision-time reference.
    A later, fully bound natural terminal independently witnesses collection.
    This disposition never grants economic or execution eligibility.
    """
    from pathlib import Path
    from src.engine.ai.holding_exit_vote import restore_buy_fill_receipt
    from src.engine.monitoring.semantic_incident_contract import holding_gap_identity

    root = Path(data_root).resolve()
    semantics = report["profit_exit_semantics"]
    identity = holding_gap_identity(semantics)
    day = report["target_date"]
    ids = sorted(map(str, accepted_position_ids))
    if (
        now.tzinfo is None
        or day >= now.astimezone(KST).date().isoformat()
        or semantics.get("target_date") != day
        or semantics.get("source_generation") != report.get("source_generation")
        or semantics.get("policy_status") != "verified_incumbent_carried"
        or identity is None
        or identity["schema"] != "holding_source_gap_identity_v2"
        or ids != sorted({row[0][7:] for row in identity["gaps"]})
        or any(len(row) != 7 for row in identity["gaps"])
    ):
        raise ValueError("holding_historical_gap_population_unproven")
    losses = {row["position_id"]: row for row in semantics["source_gap_details"]}
    latest_loss = max(
        float(row["signal_id"].split(":", 1)[0]) for row in losses.values()
    )
    healthy = [
        row
        for row in semantics["lifecycle"]
        if row.get("lifecycle_state") == "completed"
        and row.get("blocking_reason") is None
        and row.get("signal_at", 0) > latest_loss
        and row.get("orders")
        and row["position_key"][7:] not in losses
    ]
    if not healthy or not semantics.get("consumed_pids"):
        raise ValueError("holding_current_collection_unproven")
    receipts = {}
    for record in sorted(set(ids + [row["position_key"][7:] for row in healthy])):
        path = root / "runtime/holding_buy_fill_receipts" / (record + ".json")
        from src.engine.scalping.entry_split_monitor_projection import _read

        if any(parent.is_symlink() for parent in path.parents):
            raise ValueError("holding_historical_source_symlink")
        body, source = _read(path, 262144)
        stock = dict(
            id=int(record),
            code=body["code"],
            buy_time=body["buy_time"],
            buy_price=body["buy_price"],
            buy_qty=body["buy_qty"],
        )
        if (
            body.get("source") != "accepted_broker_execution"
            or restore_buy_fill_receipt(stock, root) != "restored"
        ):
            raise ValueError("holding_current_buy_restoration_unproven")
        # Exercise the actual broker inventory display boundary that caused
        # the historical loss, without modifying the receipt or live position.
        displayed = dict(
            id=int(record),
            code=body["code"],
            buy_time=body["buy_time"],
            buy_price=int(body["buy_price"]),
            buy_qty=body["buy_qty"],
        )
        if restore_buy_fill_receipt(displayed, root) != "restored":
            raise ValueError("holding_current_display_restoration_unproven")
        if record in losses and body["code"] != losses[record]["stock_code"]:
            raise ValueError("holding_historical_buy_symbol_conflict")
        signal_at = (
            float(losses[record]["signal_id"].split(":", 1)[0])
            if record in losses
            else min(
                row["signal_at"]
                for row in healthy
                if row["position_key"] == "record:" + record
            )
        )
        if _epoch(body["buy_time"]) is None or not _epoch(body["buy_time"]) < signal_at:
            raise ValueError("holding_historical_buy_clock_conflict")
        if any(
            row["position_key"] == "record:" + record
            and row["buy_fill_identity"] != body["buy_fill_identity"]
            for row in healthy
        ):
            raise ValueError("holding_current_buy_generation_conflict")
        # _read also checks no-follow path custody and concurrent mutation.
        if _read(path, 262144)[1] != source:
            raise ValueError("holding_historical_buy_source_changed")
        receipts[record] = dict(
            path=str(path),
            sha256=source["sha256"],
            buy_fill_identity=body["buy_fill_identity"],
        )
    return dict(
        schema="holding_historical_buy_gap_resolution_v1",
        source_date=day,
        source_generation=report["source_generation"],
        source_gap_identity=identity,
        accepted_at=now.isoformat(),
        disposition="historical_decision_lineage_unrecoverable",
        original_decision_lineage_recovered=False,
        buy_receipts=receipts,
        current_collection_lifecycle=healthy,
        runtime_effect=False,
        actual_order_submitted=False,
        economic_eligibility=False,
    )


def historical_resolution_code():
    """Current collection repair and native audit, not a trading approval."""
    from pathlib import Path

    engine = Path(__file__).resolve().parents[1]
    return {
        name: hashlib.sha256((engine / name).read_bytes()).hexdigest()
        for name in (
            "scalping/holding_profit_exit_semantics.py",
            "holding_exit_sentinel.py",
            "ai/holding_exit_vote.py",
            "sniper_trade_review_report.py",
        )
    }


def historical_resolution_sources(report, data_root):
    """Pin the existing native writer's dated source inventory, including gaps."""
    from pathlib import Path
    from src.engine.scalping.entry_split_monitor_projection import _identity
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    from src.engine.scalping.holding_path_vote_policy import policy_path

    root = Path(data_root).resolve()
    day = report["target_date"]
    paths = [
        root / "pipeline_events" / f"pipeline_events_{day}.jsonl",
        root
        / "runtime/sentinel_event_cache"
        / f"holding_exit_sentinel_events_{day}.jsonl",
        root
        / "runtime/sentinel_event_cache"
        / f"holding_exit_sentinel_events_{day}.meta.json",
        root / "report/monitor_snapshots" / f"holding_exit_observation_{day}.json",
        policy_path(root, day),
    ]
    paths += [
        root
        / "runtime/policy_bootstrap"
        / f"runtime_policy_bootstrap{suffix}_{day}.json"
        for suffix in ("", "_verify")
    ]
    archive = root / "runtime/policy_bootstrap/verified_holding_profit_pid" / day
    paths += list(archive.glob("*.json"))
    if len(paths) > 263:
        raise ValueError("holding_historical_pid_inventory_unbounded")
    semantics = report["profit_exit_semantics"]
    keys = {row["position_key"] for row in semantics["lifecycle"]}
    keys.update(row["position_key"] for row in semantics["source_gap_details"])
    paths += [path_vote_store_path(root, key) for key in sorted(keys)]
    result = {}
    for logical in paths:
        for path in (
            logical,
            Path(str(logical) + ".gz"),
            Path(str(logical) + ".gz.archive_receipt.json"),
        ):
            if any(parent.is_symlink() for parent in path.parents):
                raise ValueError("holding_historical_source_symlink")
            result[str(path)] = (
                _identity(path) if path.exists() or path.is_symlink() else None
            )
    return result


def read_historical_resolution(report, *, report_path, report_sha256, data_root, now):
    """Warm native consumer: new generations and changed sources stay active."""
    from pathlib import Path
    from src.engine.scalping.entry_split_monitor_projection import _read, _digest

    if not (Path(report_path).parent / "historical_resolutions").exists():
        return None
    code = historical_resolution_code()
    sources = historical_resolution_sources(report, data_root)
    path = (
        Path(report_path).parent
        / "historical_resolutions"
        / (report_sha256 + "-" + _digest(code) + "-" + _digest(sources) + ".json")
    )
    if not path.exists() and not path.is_symlink():
        return None
    value, reference = _read(path, 262144)
    if (
        value.get("schema") != "holding_historical_resolution_receipt_v1"
        or value.get("report_sha256") != report_sha256
        or value.get("code") != code
        or value.get("receipt_sha256")
        != _digest({k: v for k, v in value.items() if k != "receipt_sha256"})
    ):
        raise ValueError("holding_historical_resolution_invalid")
    if value.get("sources") != historical_resolution_sources(report, data_root):
        raise ValueError("holding_historical_resolution_source_changed")
    resolution = value["resolution"]
    accepted = datetime.fromisoformat(resolution["accepted_at"])
    if now is None or accepted.tzinfo is None or now.tzinfo is None or accepted > now:
        raise ValueError("holding_historical_resolution_clock_invalid")
    expected = historical_buy_gap_resolution(
        report,
        data_root=data_root,
        accepted_position_ids=value["accepted_position_ids"],
        now=accepted,
    )
    if (
        resolution != expected
        or _read(path, 262144)[1] != reference
        or _read(Path(report_path), 8 * 1024 * 1024)[1]["sha256"] != report_sha256
        or value["sources"] != historical_resolution_sources(report, data_root)
    ):
        raise ValueError("holding_historical_resolution_source_changed")
    return value


def _epoch(value: Any) -> float | None:
    if isinstance(value, datetime):
        return (value if value.tzinfo else value.replace(tzinfo=KST)).timestamp()
    try:
        return _epoch(datetime.fromisoformat(str(value)))
    except (ValueError, TypeError):
        return None


def event_generation(events: list[Any]) -> str:
    digest = hashlib.sha256()
    for event in events:
        material = {
            "at": _epoch(event.emitted_at),
            "stage": event.stage,
            "record_id": str(event.record_id),
            "fields": _fields(event),
        }
        digest.update(
            json.dumps(
                material,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
                allow_nan=False,
            ).encode()
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _mechanical_check(
    transition: dict,
    snapshot: dict,
    receipt: dict | None,
    market: str,
    target_date: str,
    *,
    record_symbol: tuple[str, str] | None = None,
) -> str | None:
    if not receipt:
        return "tp_mechanical_policy_receipt_missing"
    try:
        vector, classifier = receipt["market_values"], receipt["classifier_parameters"]
        observed_vector = transition.get("scalp_trailing_market_values")
        if isinstance(observed_vector, str):
            observed_vector = json.loads(observed_vector)
        vector_sha = market_values_hash(vector, classifier)
        effective = vector[market]
        typed_sha = transition.get("effective_trailing_policy_sha256")
        if typed_sha:
            from src.engine.scalping.trailing_situation_policy import (
                PreparedTrailingPolicy,
                PreparedPin,
            )

            policy = receipt.get("situation_policy")
            if not isinstance(policy, dict) or policy.get("policy_sha256") != typed_sha:
                return "tp_situation_policy_receipt_missing"
            prepared = PreparedTrailingPolicy.prepare(
                policy, target_date=target_date, parent_sha256=vector_sha
            )
            raw_pin = transition.get("trailing_situation_pin")
            raw_pin = json.loads(raw_pin) if isinstance(raw_pin, str) else raw_pin
            position_key = transition.get("position_key")
            pin_key = position_key
            legacy_base = (
                isinstance(raw_pin, dict)
                and isinstance(raw_pin.get("position_key"), str)
                and raw_pin["position_key"].startswith("target:")
                and raw_pin["position_key"] != position_key
            )
            if legacy_base:
                # Historical Main hydration used target:id:symbol for an
                # unclassified BASE pin. Bind both original row identities;
                # preserve the pin/hash and prove exactly the approved parent.
                if (
                    not isinstance(record_symbol, tuple)
                    or len(record_symbol) != 2
                    or not re.fullmatch(r"[1-9][0-9]*", str(record_symbol[0]))
                    or not re.fullmatch(r"[0-9]{6}", str(record_symbol[1]))
                    or position_key != "record:" + record_symbol[0]
                    or raw_pin.get("position_key")
                    != "target:" + ":".join(record_symbol)
                    or raw_pin.get("situation_type") != "BASE"
                    or raw_pin.get("reason") != "legacy_context_unbound"
                    or type(raw_pin.get("entry_at")) not in (int, float)
                    or raw_pin["entry_at"] != 0
                    or raw_pin.get("classifier_sha256") is not None
                    or raw_pin.get("feature_sha256") is not None
                    or not isinstance(snapshot.get("buy_fill_identity"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", snapshot["buy_fill_identity"])
                ):
                    return "tp_situation_legacy_record_symbol_unbound"
                pin_key = raw_pin["position_key"]
            pin = PreparedPin.prepare(raw_pin, pin_key)
            snapshot_pin = snapshot.get("trailing_situation_pin")
            if isinstance(snapshot_pin, str):
                if len(snapshot_pin) > 4096:
                    raise ValueError("trailing_situation_snapshot_pin_budget_invalid")
                try:
                    snapshot_pin = json.loads(snapshot_pin)
                except ValueError:
                    # The native pipeline logger persisted dictionary repr.
                    # Decode only a flat literal; never evaluate source code.
                    tree = ast.parse(snapshot_pin, mode="eval")
                    body = tree.body
                    if (
                        not isinstance(body, ast.Dict)
                        or len(body.keys) != 8
                        or any(
                            not isinstance(k, ast.Constant)
                            or not isinstance(k.value, str)
                            for k in body.keys
                        )
                        or len({k.value for k in body.keys}) != 8
                        or any(not isinstance(v, ast.Constant) for v in body.values)
                    ):
                        raise ValueError("trailing_situation_snapshot_literal_invalid")
                    snapshot_pin = ast.literal_eval(tree)
            if (
                transition.get("classification_origin_hash")
                != pin.classification_origin_hash
                or snapshot.get("position_key") != position_key
                or snapshot_pin != raw_pin
                or snapshot.get("effective_trailing_policy_sha256") != typed_sha
            ):
                return "tp_situation_origin_or_snapshot_unbound"
            effective = prepared.effective(
                market, pin, position_key=pin.position_key, target_date=target_date
            )
            if legacy_base and dict(effective) != vector[market]:
                return "tp_situation_legacy_base_parent_mismatch"
        if (
            receipt["market_values_sha256"] != vector_sha
            or receipt["classifier_version"] != CLASSIFIER_VERSION
            or receipt["classifier_sha256"] != classifier_hash(classifier)
            or transition.get("scalp_trailing_market_values_sha256") != vector_sha
            or observed_vector != vector
            or transition.get("scalp_trailing_policy_date") != target_date
            or transition.get("classifier_version") != CLASSIFIER_VERSION
            or transition.get("classifier_sha256") != receipt["classifier_sha256"]
            or _float(transition.get("trailing_start_pct"))
            != effective["SCALP_TRAILING_START_PCT"]
        ):
            return "tp_mechanical_policy_generation_mismatch"
        crossing = _first_crossing_fields(transition)
        if (
            _float(
                transition.get("raw_limit_pct", transition.get("trailing_limit_pct"))
            )
            != effective[crossing["threshold_key"]]
        ):
            return "tp_mechanical_policy_width_mismatch"
        pinned = snapshot.get("mechanical_policy_receipt")
        if isinstance(pinned, str):
            pinned = json.loads(pinned)
        if (
            not isinstance(pinned, dict)
            or pinned.get("scalp_trailing_market_values_sha256") != vector_sha
            or pinned.get("scalp_trailing_policy_date") != target_date
        ):
            return "tp_snapshot_mechanical_policy_unbound"
    except (KeyError, TypeError, ValueError, SyntaxError):
        return "tp_mechanical_policy_contract_invalid"
    return None


def _first_crossing_fields(fields: dict) -> dict:
    raw = fields.get("first_crossing")
    return json.loads(raw) if isinstance(raw, str) else (raw or {})


def _float(value: Any) -> float | None:
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _fields(event: Any) -> dict[str, Any]:
    return event.fields if isinstance(getattr(event, "fields", None), dict) else {}


def _first_crossing(event: Any) -> dict[str, Any] | None:
    raw = _fields(event).get("first_crossing")
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def first_crossing_source(
    first,
    *,
    stock_code,
    buy_fill_identity,
    mechanical_fields,
    policy_fields,
    start_pct,
    observed_at,
    evaluator,
):
    """Freeze mandatory evidence without carrying sampled grid/quote histories."""
    fields = mechanical_fields or {}
    body = {
        key: fields.get(key)
        for key in (
            "classifier_version",
            "classifier_sha256",
            "effective_trailing_policy_sha256",
            "classification_origin_hash",
            "trailing_situation_pin",
        )
    }
    body.update(
        {
            key: policy_fields.get(key)
            for key in (
                "scalp_trailing_market_values",
                "scalp_trailing_market_values_sha256",
                "scalp_trailing_policy_date",
            )
        }
    )
    body.update(
        schema="scalp_trailing_first_crossing_source_v1",
        stock_code=str(stock_code),
        position_key=first.get("position_key"),
        buy_fill_identity=buy_fill_identity,
        first_crossing=dict(first),
        runtime_pid=first.get("source_runtime_pid"),
        observed_at=observed_at,
        evaluator=evaluator,
        trailing_start_pct=start_pct,
        raw_limit_pct=first.get("threshold_pct"),
        tuning_exit_allowed_by_clock=True,
        trigger_kind="trailing_peak_worsen_floor",
        actual_order_submitted=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
        metric_role="source_quality_gate",
        decision_authority="native_first_crossing_observation_only",
        window_policy="same_position_buy_generation_pid_and_native_latch",
        sample_floor=1,
        primary_decision_metric="first_crossing_source_binding",
        source_quality_gate="native_latch_clock_policy_and_buy_identity",
        forbidden_uses=[
            "historical_crossing_backfill",
            "quote_coverage_inference",
            "order_or_threshold_authority",
            "actual_economics",
        ],
    )
    # Bound each receipt independently; the existing 256-row grid cap stays intact.
    body = json.loads(json.dumps(body, sort_keys=True, allow_nan=False))
    receipt = {**body, "source_sha256": input_snapshot_id(body)}
    if len(json.dumps(receipt, sort_keys=True, allow_nan=False).encode()) > 8192:
        raise ValueError("tp_first_crossing_source_budget_invalid")
    return receipt


def _native_crossing_source(event, snapshot):
    raw = _fields(event).get("first_crossing_source")
    if isinstance(raw, str) and len(raw.encode()) > 8192:
        raise ValueError("tp_first_crossing_source_budget_invalid")
    body = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(body, dict):
        raise ValueError("tp_first_crossing_source_missing")
    if len(json.dumps(body, sort_keys=True, allow_nan=False).encode()) > 8192:
        raise ValueError("tp_first_crossing_source_budget_invalid")
    first = body.get("first_crossing")
    if (
        body.get("schema") != "scalp_trailing_first_crossing_source_v1"
        or body.get("source_sha256")
        != input_snapshot_id({k: v for k, v in body.items() if k != "source_sha256"})
        or body.get("actual_order_submitted") is not False
        or body.get("runtime_effect") is not False
        or body.get("allowed_runtime_apply") is not False
        or not isinstance(first, dict)
        or body.get("stock_code") != str(getattr(event, "stock_code", ""))
        or body.get("position_key") != "record:" + str(getattr(event, "record_id", ""))
        or body.get("position_key") != snapshot.get("position_key")
        or body.get("buy_fill_identity") != snapshot.get("buy_fill_identity")
        or not re.fullmatch("[0-9a-f]{64}", str(body.get("buy_fill_identity") or ""))
        or type(body.get("runtime_pid")) is not int
        or body["runtime_pid"] <= 0
        or _float(body.get("runtime_pid")) != _float(snapshot.get("runtime_pid"))
        or first.get("source_runtime_pid") != body.get("runtime_pid")
        or first.get("position_key") != body.get("position_key")
        or first.get("buy_fill_identity") != body.get("buy_fill_identity")
        or first.get("at_epoch") != _float(snapshot.get("signal_at"))
        or type(first.get("at_epoch")) not in (int, float)
        or not math.isfinite(first["at_epoch"])
        or _float(body.get("observed_at")) is None
        or not first["at_epoch"] <= body["observed_at"] <= _epoch(event.emitted_at)
    ):
        raise ValueError("tp_first_crossing_source_binding_invalid")
    return body


def _latency_distribution(rows: list[Any], field: str) -> dict[str, Any]:
    values = sorted(
        value
        for row in rows
        if (value := _float(_fields(row).get(field))) is not None and value >= 0
    )
    if not values:
        return {"count": 0, "p50_ms": None, "p95_ms": None, "p99_ms": None}
    return {
        "count": len(values),
        "p50_ms": values[math.ceil(len(values) * 0.50) - 1],
        "p95_ms": values[math.ceil(len(values) * 0.95) - 1],
        "p99_ms": values[math.ceil(len(values) * 0.99) - 1],
    }


def audit_profit_exit_flow(
    events: list[Any],
    *,
    target_date: str,
    load_votes: Callable[[str], list[dict[str, Any]]],
    observation: dict[str, Any] | None = None,
    policies: dict[tuple[str, str], dict[str, Any]] | None = None,
    policy_bundle_sha256: str | None = None,
    as_of: datetime | None = None,
    source_generation: str | None = None,
    mechanical_policy_receipt: dict | None = None,
    consumed_pid: int | None = None,
    consumed_pids: list[int] | None = None,
    mechanical_receipts_by_pid: dict[int, dict] | None = None,
    model: str = "gpt-5.4-nano",
) -> dict[str, Any]:
    """Audit evidence order; absent natural positions remain valid empty."""
    selected = policies or PATH_POLICY_BY_MARKET
    cutoff = (
        _epoch(as_of)
        if as_of is not None
        else max((_epoch(event.emitted_at) or 0 for event in events), default=0)
    )
    events = [
        event
        for event in events
        if (at := _epoch(event.emitted_at)) is not None
        and datetime.fromtimestamp(at, KST).date().isoformat() == target_date
        and at <= cutoff
    ]
    generation = event_generation(events)
    if source_generation is not None and source_generation != generation:
        raise ValueError("holding_semantic_source_generation_mismatch")
    stages = Counter()
    scoped: dict[str, list[Any]] = defaultdict(list)
    for event in events:
        fields = _fields(event)
        if fields.get("pipeline_lifecycle_population_scope") != "real_record_bound":
            continue
        record_id = str(getattr(event, "record_id", "") or "").strip()
        if not record_id:
            continue
        stage = str(getattr(event, "stage", "") or "")
        stages[stage] += 1
        scoped[record_id].append(event)

    findings: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    gap_details: list[dict[str, Any]] = []
    policy_gaps: list[dict[str, str]] = []
    runtime_gaps: list[dict[str, str]] = []
    counts = Counter()
    receipt_observations = []
    lifecycles: list[dict] = []
    market_trigger = Counter()
    market_trigger_kind = Counter()
    timing_rows: dict[str, list[Any]] = defaultdict(list)
    observation_at = _epoch(
        ((observation or {}).get("meta") or {}).get("knowledge_cutoff")
    )
    observation_available = observation_at is not None and observation_at <= cutoff
    if not observation_available:
        observation = {}
    strict_ids = set(
        str(value)
        for value in (
            (observation or {}).get("completed_population_quality") or {}
        ).get("strict_completed_position_ids")
        or []
    )
    outcomes = {
        str(row.get("record_id")): row
        for row in (observation or {}).get("position_outcomes") or []
        if isinstance(row, dict) and row.get("record_id") is not None
    }

    def add(bucket: list[dict[str, str]], record_id: str, reason: str) -> None:
        bucket.append({"position_id": record_id, "reason": reason})

    for record_id, rows in scoped.items():
        rows = sorted(rows, key=lambda row: _epoch(row.emitted_at))
        # The same durable broker terminal can be observed again while its
        # attribution outbox waits for ACK. Use the existing native identity,
        # clock and complete-payload verifier, never a timestamp/count heuristic.
        terminals = [
            (index, row)
            for index, row in enumerate(rows)
            if row.stage == "sell_completed"
        ]
        if len(terminals) > 1:
            from src.engine.sniper_trade_review_report import (
                HoldingEvent,
                _quantity_sell_receipt_observations,
            )

            normalized, receipts = _quantity_sell_receipt_observations(
                [
                    HoldingEvent(
                        row.emitted_at.isoformat(),
                        row.stock_name,
                        row.stock_code,
                        row.stage,
                        row.fields,
                        str(index),
                    )
                    for index, row in terminals
                ],
                record_id=record_id,
            )
            if receipts:
                kept = {int(row.raw_line) for row in normalized}
                removed = {index for index, _ in terminals} - kept
                # Causal sequencing uses first observation time. The verified
                # broker clock remains in the audit, never substituted for the
                # local receipt time (broker seconds can precede submit logs).
                rows = [row for index, row in enumerate(rows) if index not in removed]
                receipt_observations.extend(receipts)
        row_order = {id(row): index for index, row in enumerate(rows)}
        counts["holding_started"] += int(
            any(getattr(row, "stage", "") == "holding_started" for row in rows)
        )
        reviews = [
            row for row in rows if getattr(row, "stage", "") == "holding_path_review"
        ]
        counts["review_due"] += len(reviews)
        counts["review_unchanged_input"] += sum(
            _fields(row).get("status") == "unchanged_input_skip" for row in reviews
        )
        counts["vote_source_gap"] += sum(
            getattr(row, "stage", "") == "holding_path_vote_source_gap" for row in rows
        )
        collected = [
            row
            for row in rows
            if getattr(row, "stage", "") == "holding_path_votes_collected"
        ]
        timing_rows["vote_claim_ms"].extend(collected)
        timing_rows["engine_call_ms"].extend(collected)
        timing_rows["vote_store_ms"].extend(collected)
        counts["vote_bundle_persisted"] += len(collected)
        counts["provider_called"] += sum(
            max(0, int(_float(_fields(row).get("provider_calls")) or 0))
            for row in collected
        )
        snapshots = [
            event
            for event in rows
            if getattr(event, "stage", "") == "holding_path_signal_snapshot"
            and _fields(event).get("path_id") == "EXIT_TRAILING_TP"
        ]
        timing_rows["signal_snapshot_ms"].extend(snapshots)
        timing_rows["signal_provider_wait_ms"].extend(snapshots)
        transitions = [
            event
            for event in rows
            if getattr(event, "stage", "") == "scalp_trailing_input_transition"
        ]
        native_crossings = [
            event
            for event in rows
            if getattr(event, "stage", "") == "scalp_trailing_first_crossing_transition"
        ]
        exits = [
            event
            for event in rows
            if getattr(event, "stage", "") == "exit_signal"
            and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"
        ]
        sent = [
            event
            for event in rows
            if getattr(event, "stage", "") == "sell_order_sent"
            and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"
        ]
        partial = [
            event
            for event in rows
            if getattr(event, "stage", "") == "sell_partial_fill_progress"
            and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"
        ]
        completed = [
            event
            for event in rows
            if getattr(event, "stage", "") == "sell_completed"
            and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"
        ]
        if not (snapshots or exits or sent or partial or completed):
            continue
        counts["tp_signal_snapshots"] += len(snapshots)
        counts["tp_exit_signals"] += len(exits)
        counts["tp_sell_submitted"] += len(sent)
        counts["tp_sell_partial_fill"] += len(partial)
        counts["tp_sell_completed"] += len(completed)
        counts["tp_arm_observed"] += sum(
            str(_fields(row).get("armed")).lower() == "true" for row in transitions
        )
        counts["tp_source_ready"] += sum(
            str(_fields(row).get("tuning_grid_source_complete")).lower() == "true"
            for row in transitions
        )
        counts["tp_veto_defer"] += sum(
            getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
            for row in rows
        )
        snapshot_ids = [str(_fields(row).get("signal_id") or "") for row in snapshots]
        snapshot_keys = [
            (
                _fields(row).get("position_key"),
                _fields(row).get("buy_fill_identity"),
                _fields(row).get("signal_id"),
            )
            for row in snapshots
        ]
        if len(snapshot_keys) != len(set(snapshot_keys)):
            add(findings, record_id, "tp_duplicate_signal_snapshot_id")
        for row in exits:
            if (
                str(_fields(row).get("holding_path_signal_id") or "")
                not in snapshot_ids
            ):
                add(gaps, record_id, "tp_exit_without_vote_snapshot")
        for row in sent:
            if not any(
                _fields(exit_row).get("holding_path_signal_id")
                == _fields(row).get("holding_path_signal_id")
                for exit_row in exits
            ):
                add(findings, record_id, "tp_sell_without_exit_signal")
        for row in (*partial, *completed):
            fields = _fields(row)
            signal_id = str(fields.get("holding_path_signal_id") or "")
            if signal_id and signal_id not in snapshot_ids:
                add(gaps, record_id, "tp_terminal_signal_generation_unmatched")
            if (
                fields.get("holding_path_terminal_signal_binding")
                != "same_position_buy_generation"
            ):
                add(gaps, record_id, "tp_terminal_buy_generation_unbound")
            order_no = str(fields.get("order_no") or "")
            submitted_orders = {str(_fields(item).get("ord_no") or "") for item in sent}
            if (
                order_no not in {"", "-"}
                and submitted_orders
                and order_no not in submitted_orders
            ):
                add(gaps, record_id, "tp_terminal_order_number_unmatched")
        for row in completed:
            fields = _fields(row)
            if _float(fields.get("remaining_sell_qty")) is None:
                add(gaps, record_id, "tp_terminal_remaining_quantity_missing")
            elif _float(fields.get("remaining_sell_qty")) != 0.0:
                add(findings, record_id, "tp_terminal_remaining_quantity_nonzero")
        counted_vote_keys: set[tuple[str, str, str]] = set()
        for event in snapshots:
            fields = _fields(event)
            signal_at = _float(fields.get("signal_at"))
            market = str(fields.get("market") or "")
            signal_id = str(fields.get("signal_id") or "")
            position_key = str(fields.get("position_key") or "")
            raw_buy_identity = fields.get("buy_fill_identity")
            buy_identity = (
                ""
                if raw_buy_identity in (None, "", "None", "-")
                else str(raw_buy_identity)
            )
            policy = selected.get(("EXIT_TRAILING_TP", market))
            if (
                signal_at is None
                or not signal_id
                or not policy
                or market_type_at(signal_at) != market
                or position_key != f"record:{record_id}"
                or buy_identity
                and re.fullmatch(r"[0-9a-f]{64}", buy_identity) is None
            ):
                add(findings, record_id, "tp_signal_identity_or_market_invalid")
                continue
            if fields.get("policy_sha256") != input_snapshot_id(policy):
                add(findings, record_id, "tp_signal_policy_hash_mismatch")
                continue
            if (
                policy_bundle_sha256 is not None
                and fields.get("policy_bundle_sha256") != policy_bundle_sha256
            ):
                add(policy_gaps, record_id, "tp_signal_bundle_hash_mismatch")
            elif policy_bundle_sha256 is not None and fields.get(
                "policy_load_status"
            ) not in {
                "estimated_provisional_loaded",
                "validated_successor_loaded",
                "verified_incumbent_loaded",
            }:
                add(runtime_gaps, record_id, "tp_runtime_policy_load_unproven")
            elif policy_bundle_sha256 is None and fields.get("policy_load_status") in {
                "estimated_provisional_loaded",
                "validated_successor_loaded",
                "verified_incumbent_loaded",
            }:
                add(policy_gaps, record_id, "tp_loaded_policy_bundle_missing")
            if not buy_identity:
                add(gaps, record_id, "tp_signal_buy_generation_missing")
                # Identify the original missing-source incident, without
                # inventing BUY lineage or advancing its lifecycle. Only a
                # complete, unambiguous signal/terminal population qualifies.
                # Hash original canonical rows, not the growing session/report.
                # A prior bound partial exit is not another missing terminal.
                # Bind the later unbound terminal through its original order,
                # since that terminal intentionally has no signal/BUY fields.
                matched_sent = [
                    row
                    for row in sent
                    if _fields(row).get("holding_path_signal_id") == signal_id
                    and _fields(row).get("holding_path_position_key") == position_key
                    and _fields(row).get("holding_path_buy_fill_identity")
                    in (None, "", "None", "-")
                    and getattr(row, "stock_code", None) == event.stock_code
                ]
                prior_snapshots = [row for row in snapshots if row is not event]
                prior_partial_bound = (
                    bool(partial)
                    and bool(prior_snapshots)
                    and all(
                        _epoch(row.emitted_at) < _epoch(event.emitted_at)
                        and getattr(row, "stock_code", None) == event.stock_code
                        and _fields(row).get("position_key") == position_key
                        and re.fullmatch(
                            r"[0-9a-f]{64}", str(_fields(row).get("buy_fill_identity"))
                        )
                        and _fields(row).get("signal_id") != signal_id
                        for row in prior_snapshots
                    )
                    and all(
                        _epoch(row.emitted_at) < _epoch(event.emitted_at)
                        and getattr(row, "stock_code", None) == event.stock_code
                        and _fields(row).get("holding_path_terminal_signal_binding")
                        == "same_position_buy_generation"
                        and any(
                            _fields(row).get("holding_path_signal_id")
                            == _fields(prior).get("signal_id")
                            and _fields(row).get("holding_path_buy_fill_identity")
                            == _fields(prior).get("buy_fill_identity")
                            and _fields(row).get("holding_path_position_key")
                            == position_key
                            for prior in prior_snapshots
                        )
                        for row in partial
                    )
                )
                matched_partial_terminal = (
                    prior_partial_bound
                    and len(matched_sent) == len(completed) == 1
                    and _epoch(event.emitted_at)
                    <= _epoch(matched_sent[0].emitted_at)
                    <= _epoch(completed[0].emitted_at)
                    and _fields(matched_sent[0]).get("ord_no")
                    == _fields(completed[0]).get("order_no")
                    and sum(
                        _fields(row).get("ord_no")
                        == _fields(completed[0]).get("order_no")
                        for row in sent
                    )
                    == 1
                )
                if (
                    len(completed) == 1
                    and (
                        len(snapshots) == 1 and not partial or matched_partial_terminal
                    )
                    and getattr(completed[0], "stock_code", None) == event.stock_code
                    and re.fullmatch(r"[0-9]{6}", event.stock_code or "")
                    and _epoch(completed[0].emitted_at) >= _epoch(event.emitted_at)
                    and _fields(completed[0]).get(
                        "holding_path_terminal_signal_binding"
                    )
                    == "source_gap_generation_mismatch"
                    and str(_fields(completed[0]).get("order_no") or "").isdigit()
                    and _float(_fields(completed[0]).get("remaining_sell_qty")) == 0
                ):
                    proof = dict(
                        position_id=record_id,
                        position_key=position_key,
                        stock_code=event.stock_code,
                        signal_id=signal_id,
                        signal_source_sha256=event_generation([event]),
                        terminal_source_sha256=event_generation(completed),
                        source_disposition="original_buy_generation_absent",
                        historical_recovery_proven=False,
                    )
                    for reason in (
                        "tp_signal_buy_generation_missing",
                        "tp_terminal_buy_generation_unbound",
                    ):
                        gap_details.append(dict(proof, reason=reason))
                continue
            crossing_rows = [
                row
                for row in transitions
                if _epoch(row.emitted_at) <= _epoch(event.emitted_at)
                and _fields(row).get("position_key") == position_key
                and (_first_crossing(row) or {}).get("at_epoch") == signal_at
            ]
            crossing_candidates = [(row, _fields(row)) for row in crossing_rows]
            for row in native_crossings:
                if (
                    _epoch(row.emitted_at) > _epoch(event.emitted_at)
                    or _fields(row).get("position_key") != position_key
                    or _fields(row).get("buy_fill_identity") != buy_identity
                    or _float(_fields(row).get("first_crossing_at")) != signal_at
                ):
                    continue
                try:
                    if getattr(row, "stock_code", None) != getattr(
                        event, "stock_code", None
                    ):
                        raise ValueError("tp_first_crossing_symbol_invalid")
                    source = _native_crossing_source(row, fields)
                except (ValueError, TypeError, KeyError, OverflowError):
                    add(gaps, record_id, "tp_first_crossing_source_invalid")
                    continue
                crossing_candidates.append((row, source))
            if not crossing_candidates:
                add(gaps, record_id, "tp_first_crossing_transition_missing")
                exhausted = [
                    row
                    for row in transitions
                    if _epoch(row.emitted_at) <= _epoch(event.emitted_at)
                    and str(_fields(row).get("observation_coverage_exhausted")).lower()
                    == "true"
                ]
                if exhausted:
                    last = exhausted[-1]
                    gap_details.append(
                        dict(
                            position_id=record_id,
                            signal_id=signal_id,
                            reason="tp_first_crossing_transition_missing",
                            source_disposition="sampled_grid_exhausted_before_signal",
                            last_grid_transition_at=last.emitted_at.isoformat(),
                            last_grid_sequence=_float(
                                _fields(last).get("event_sequence")
                            ),
                            grid_sample_limit=_float(
                                _fields(last).get("observation_max_samples")
                            ),
                            historical_recovery_proven=False,
                            actual_order_submitted=False,
                        )
                    )
            else:
                origin, transition = max(
                    crossing_candidates, key=lambda item: _epoch(item[0].emitted_at)
                )
                crossing = _first_crossing_fields(transition)
                if (
                    crossing.get("market") != market
                    or crossing.get("threshold_key")
                    not in {"SCALP_TRAILING_LIMIT_WEAK", "SCALP_TRAILING_LIMIT_STRONG"}
                    or transition.get("tuning_exit_allowed_by_clock")
                    not in {"True", "true", True}
                ):
                    add(findings, record_id, "tp_crossing_arm_or_clock_invalid")
                pid_receipt = (mechanical_receipts_by_pid or {}).get(
                    _float(fields.get("runtime_pid")), mechanical_policy_receipt
                )
                record_symbol = (
                    (record_id, str(getattr(event, "stock_code", "")))
                    if str(getattr(origin, "record_id", "")) == record_id
                    and getattr(origin, "stock_code", None)
                    == getattr(event, "stock_code", None)
                    else None
                )
                mechanical_error = _mechanical_check(
                    transition,
                    fields,
                    pid_receipt,
                    market,
                    target_date,
                    record_symbol=record_symbol,
                )
                if mechanical_error:
                    add(policy_gaps, record_id, mechanical_error)
                valid_pids = set(
                    consumed_pids
                    or ([consumed_pid] if consumed_pid is not None else [])
                )
                if _float(fields.get("runtime_pid")) not in valid_pids:
                    add(
                        runtime_gaps,
                        record_id,
                        "tp_mechanical_pid_consumption_unproven",
                    )
                evaluator = str(transition.get("evaluator") or "normal")
                kind = "fast" if evaluator.startswith("fast") else "normal"
                market_trigger[f"{market}|{kind}"] += 1
                trigger_kind = str(transition.get("trigger_kind") or "")
                if trigger_kind == "trailing_peak_worsen_floor":
                    market_trigger_kind[f"{market}|{kind}|{trigger_kind}"] += 1
                else:
                    add(
                        gaps,
                        record_id,
                        "tp_first_crossing_trigger_kind_missing_or_invalid",
                    )
            try:
                votes = load_votes(position_key)
            except (OSError, ValueError):
                add(gaps, record_id, "tp_vote_ledger_unreadable")
                votes = []
            for vote in votes:
                if (
                    vote.get("path_id") != "EXIT_TRAILING_TP"
                    or vote.get("market") != market
                    or any(
                        (at := _float(vote.get(key))) is None
                        or at > min(cutoff, signal_at)
                        for key in ("requested_at", "received_at", "persisted_at")
                    )
                ):
                    continue
                identity = (
                    str(vote.get("path_id")),
                    str(vote.get("market")),
                    str(vote.get("input_snapshot_id")),
                )
                if identity in counted_vote_keys:
                    continue
                counted_vote_keys.add(identity)
                counts["tp_vote_claimed"] += bool(
                    vote.get("path_decision_input_sha256")
                )
                counts["tp_vote_provider_called"] += vote.get("provider_called") is True
                counts["tp_vote_valid_persisted"] += (
                    vote.get("status") == "VALID"
                    and _float(vote.get("persisted_at")) is not None
                )
            if not votes and _float(fields.get("vote_count")):
                add(gaps, record_id, "tp_vote_ledger_missing")
            expected = path_signal_snapshot(
                votes,
                position_key=position_key,
                market=market,
                session_key=str(fields.get("session_key") or ""),
                path_id="EXIT_TRAILING_TP",
                model=model,
                signal_at=signal_at,
                policy=policy,
                buy_fill_identity=buy_identity,
            )
            count = _float(fields.get("vote_count"))
            if (
                count is None
                or count != expected["vote_count"]
                or fields.get("decision") != expected["decision"]
            ):
                add(
                    findings if votes else gaps,
                    record_id,
                    "tp_vote_snapshot_replay_mismatch",
                )
            counts[f"tp_decision_{fields.get('decision') or 'UNKNOWN'}"] += 1
            matching_exit = [
                row
                for row in exits
                if _fields(row).get("holding_path_signal_id") == signal_id
            ]
            matching_sent = [
                row
                for row in sent
                if _fields(row).get("holding_path_signal_id") == signal_id
            ]
            matching_completed = [
                row
                for row in completed
                if _fields(row).get("holding_path_signal_id") == signal_id
            ]
            matching_partial = [
                row
                for row in partial
                if _fields(row).get("holding_path_signal_id") == signal_id
            ]
            for row in (
                *matching_exit,
                *matching_sent,
                *matching_partial,
                *matching_completed,
            ):
                bound = _fields(row)
                if (
                    bound.get("holding_path_position_key") != position_key
                    or bound.get("holding_path_buy_fill_identity") != buy_identity
                ):
                    add(gaps, record_id, "tp_lifecycle_buy_generation_unbound")

            def same_generation(row: Any) -> bool:
                return (
                    _fields(row).get("holding_path_position_key") == position_key
                    and _fields(row).get("holding_path_buy_fill_identity")
                    == buy_identity
                )

            matching_exit = [row for row in matching_exit if same_generation(row)]
            matching_sent = [row for row in matching_sent if same_generation(row)]
            matching_partial = [row for row in matching_partial if same_generation(row)]
            matching_completed = [
                row for row in matching_completed if same_generation(row)
            ]
            if any(not str(_fields(row).get("ord_no") or "") for row in matching_sent):
                add(gaps, record_id, "tp_submit_order_identity_missing")
            matching_sent = [
                row for row in matching_sent if str(_fields(row).get("ord_no") or "")
            ]
            submitted_orders = {str(_fields(row)["ord_no"]) for row in matching_sent}
            for row in (*matching_partial, *matching_completed):
                if str(
                    _fields(row).get("order_no") or ""
                ) not in submitted_orders or not any(
                    str(_fields(attempt).get("ord_no"))
                    == str(_fields(row).get("order_no"))
                    and _epoch(attempt.emitted_at) <= _epoch(row.emitted_at)
                    for attempt in matching_sent
                ):
                    add(gaps, record_id, "tp_terminal_attempt_unmatched")

            def matches_submitted_attempt(row: Any) -> bool:
                return any(
                    str(_fields(attempt).get("ord_no"))
                    == str(_fields(row).get("order_no"))
                    and _epoch(attempt.emitted_at) <= _epoch(row.emitted_at)
                    for attempt in matching_sent
                )

            matching_partial = [
                row
                for row in matching_partial
                if matches_submitted_attempt(row)
                and _fields(row).get("holding_path_terminal_signal_binding")
                == "same_position_buy_generation"
            ]
            matching_completed = [
                row
                for row in matching_completed
                if matches_submitted_attempt(row)
                and _fields(row).get("holding_path_terminal_signal_binding")
                == "same_position_buy_generation"
                and _float(_fields(row).get("remaining_sell_qty")) == 0.0
            ]
            if any(
                _epoch(row.emitted_at) < _epoch(event.emitted_at)
                for row in matching_exit
            ):
                add(findings, record_id, "tp_exit_before_vote_snapshot")
            if matching_exit and any(
                _epoch(row.emitted_at) < _epoch(matching_exit[0].emitted_at)
                for row in matching_sent
            ):
                add(findings, record_id, "tp_submit_before_exit_signal")
            if fields.get("decision") == "VETO" and matching_exit:
                elapsed = _epoch(matching_exit[0].emitted_at) - signal_at
                if elapsed < 0:
                    add(findings, record_id, "tp_veto_exit_before_first_crossing")
                elif elapsed < policy["max_defer_sec"] and not any(
                    _fields(row).get("signal_id") == signal_id
                    for row in rows
                    if getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
                ):
                    add(gaps, record_id, "tp_veto_defer_or_safety_reason_missing")
            deferrals = [
                row
                for row in rows
                if getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
                and _fields(row).get("signal_id") == signal_id
                and _fields(row).get("position_key") == position_key
                and _fields(row).get("buy_fill_identity") == buy_identity
            ]
            last_exit_index = max(
                (row_order[id(row)] for row in matching_exit), default=-1
            )
            guards = [
                row
                for row in rows
                if getattr(row, "stage", "") in EXIT_WAIT_STAGES
                and row_order[id(row)] > last_exit_index
                and _fields(row).get("holding_path_signal_id") == signal_id
                and _fields(row).get("holding_path_position_key") == position_key
                and _fields(row).get("holding_path_buy_fill_identity") == buy_identity
            ]
            state = (
                "completed"
                if matching_completed
                else (
                    "pending_terminal"
                    if matching_sent
                    else (
                        "guard_wait"
                        if guards
                        else (
                            "pending_submit"
                            if matching_exit
                            else (
                                "deferred"
                                if deferrals
                                and _fields(deferrals[-1]).get("phase") != "released"
                                else "signal_observed"
                            )
                        )
                    )
                )
            )
            economics = "pending"
            outcome = outcomes.get(record_id)
            if matching_completed:
                economics = "unavailable"
                cost = (outcome or {}).get("actual_cost_reconciliation") or {}
                known_at = max(
                    _epoch(cost.get("cost_available_at")) or float("inf"),
                    _epoch(cost.get("reconciled_at")) or float("inf"),
                )
                if (
                    record_id in strict_ids
                    and outcome
                    and outcome.get("sell_quantity_conserved") is True
                    and _float(outcome.get("profit_rate")) is not None
                    and _float(outcome.get("realized_pnl_krw")) is not None
                    and cost.get("status") == "actual_cost_reconciled"
                    and known_at <= cutoff
                    and outcome.get("holding_path_buy_fill_identity") == buy_identity
                ):
                    economics = "verified"
                elif (
                    known_at > cutoff and cost.get("status") == "actual_cost_reconciled"
                ):
                    economics = "pending"
            if state in {"pending_submit", "pending_terminal"}:
                counts[f"tp_{state}"] += 1
            counts[f"tp_economics_{economics}"] += 1
            lifecycles.append(
                {
                    "position_key": position_key,
                    "buy_fill_identity": buy_identity,
                    "signal_id": signal_id,
                    "lifecycle_state": state,
                    "economics_status": economics,
                    "signal_at": signal_at,
                    "elapsed_sec": max(0, cutoff - signal_at),
                    "blocking_reason": (
                        (_fields(guards[-1]).get("reason") or guards[-1].stage)
                        if guards
                        else None
                    ),
                    "orders": sorted(submitted_orders),
                    "attempts": [
                        {
                            "order_no": _fields(row).get("ord_no"),
                            "attempt_id": _fields(row).get("attempt_id"),
                            "submitted_at": row.emitted_at.isoformat(),
                            "terminal_events": [
                                getattr(item, "stage", "")
                                for item in rows
                                if _fields(item).get("order_no")
                                == _fields(row).get("ord_no")
                                and _fields(item).get("holding_path_signal_id")
                                == signal_id
                                and _fields(item).get("holding_path_buy_fill_identity")
                                == buy_identity
                                and getattr(item, "stage", "")
                                in {
                                    "sell_partial_fill_progress",
                                    "sell_completed",
                                    "sell_order_cancelled",
                                    "sell_order_rejected",
                                }
                            ],
                        }
                        for row in matching_sent
                    ],
                }
            )
        if completed and not sent:
            add(gaps, record_id, "tp_completed_without_submit_receipt")
        outcome = outcomes.get(record_id)
        if completed and outcome is not None:
            if outcome.get("sell_quantity_conserved") is not True:
                add(findings, record_id, "tp_sell_quantity_not_conserved")
            if (
                _float(outcome.get("profit_rate")) is None
                or _float(outcome.get("realized_pnl_krw")) is None
            ):
                counts["tp_economics_null"] += 1
            if not outcome.get("exact_sell_fill_time"):
                counts["tp_forward_censored_no_sell_time"] += 1
            elif (
                outcome.get("post_sell_status") == "pass"
                and (_epoch(outcome.get("post_sell_observed_at")) or float("inf"))
                <= cutoff
            ):
                counts["tp_forward_observed"] += 1
            else:
                counts["tp_forward_censored_source_or_horizon_gap"] += 1
        buy_qty = max(
            (_float(_fields(row).get("buy_qty")) or 0.0 for row in exits), default=0.0
        )
        if buy_qty and any(
            (_float(_fields(row).get("qty")) or 0.0) > buy_qty for row in sent
        ):
            add(findings, record_id, "tp_submitted_quantity_exceeds_buy")
    semantic_status = (
        "semantic_contract_invalid"
        if findings
        else (
            "policy_binding_gap"
            if policy_gaps
            else (
                "runtime_not_consumed"
                if runtime_gaps
                else (
                    "source_gap"
                    if gaps
                    else "valid_empty" if not counts["tp_signal_snapshots"] else "pass"
                )
            )
        )
    )
    status = semantic_status
    if semantic_status == "pass":
        status = (
            "pending_submit"
            if counts["tp_pending_submit"]
            else "pending_terminal" if counts["tp_pending_terminal"] else "pass"
        )
    return {
        "schema": "holding_profit_exit_semantics_v2",
        "target_date": target_date,
        "status": status,
        "semantic_status": semantic_status,
        "lifecycle": lifecycles,
        "economics_status": (
            "unavailable"
            if counts["tp_economics_unavailable"]
            else (
                "pending"
                if counts["tp_economics_pending"] or not lifecycles
                else "verified"
            )
        ),
        "as_of": (
            datetime.fromtimestamp(cutoff, KST).isoformat()
            if cutoff
            else f"{target_date}T00:00:00+09:00"
        ),
        "source_generation": generation,
        "mechanical_policy_sha256": (mechanical_policy_receipt or {}).get(
            "market_values_sha256"
        ),
        "mechanical_policy_sha256_by_pid": {
            str(pid): receipt.get("market_values_sha256")
            for pid, receipt in (mechanical_receipts_by_pid or {}).items()
        },
        "consumed_pid": consumed_pid,
        "consumed_pids": sorted(
            set(consumed_pids or ([consumed_pid] if consumed_pid is not None else []))
        ),
        "observation_as_of_status": (
            "available" if observation_available else "unassessed_source_as_of"
        ),
        "decision_authority": "report_only_no_order_or_policy_mutation",
        "funnel": dict(sorted(counts.items())),
        "by_market_trigger": dict(sorted(market_trigger.items())),
        "by_market_trigger_kind": dict(sorted(market_trigger_kind.items())),
        "latency_ms": {
            field: _latency_distribution(rows, field)
            for field, rows in sorted(timing_rows.items())
        },
        "findings": findings,
        "source_gaps": gaps,
        "source_gap_details": gap_details,
        "terminal_receipt_observations": receipt_observations,
        "policy_binding_gaps": policy_gaps,
        "runtime_consumption_gaps": runtime_gaps,
        "strict_completed_position_count": len(strict_ids),
    }
