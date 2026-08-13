"""Deterministic source-only entry x exit path replay contract.

This is the P2-A engine.  It is intentionally callable only with an explicit
in-memory path and frozen policy.  It has no data-discovery CLI, no ranking
output, and no sim/live consumer.
"""

from __future__ import annotations

import gzip
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .path_journal import validate_market_stream_path_provenance

P2_REPLAY_SCHEMA = "scalp_micro_reversion_p2_path_replay_v2"
P2_REPLAY_AUTHORITY = "p2_path_research_only_selection_authority_false"
SOURCE_EXCLUSION_SCHEMA = "scalp_micro_reversion_source_exclusion_manifest_v1"
SOURCE_EXCLUSION_SCOPE_POLICY = "exact_trade_date_venue_session_sequence_epoch"
_SOURCE_EXCLUSION_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
)
DEFAULT_SOURCE_EXCLUSION_MANIFEST = (
    Path(__file__).parents[4]
    / "configs"
    / "scalp_micro_reversion_source_exclusions.json.txt"
)
P2_REPLAY_METRIC_CONTRACT = {
    "metric_role": "primary_ev_research_candidate",
    "decision_authority": P2_REPLAY_AUTHORITY,
    "window_policy": "frozen_discovery_then_holdout_confirmation_joint_path",
    "sample_floor": "owned_by_confirmation_gate_not_synthetic_tests",
    "primary_decision_metric": "net_ev_per_all_detected_signal",
    "source_quality_gate": (
        "continuous_parent_wave_path_and_decision_watermark_and_"
        "declared_fill_bound_and_same_timestamp_policy_and_"
        "next_observation_reclaim_execution"
    ),
    "forbidden_uses": (
        "real_data_policy_ranking_before_gate_b",
        "sim_or_live_policy_selection",
        "touch_as_real_fill",
        "hybrid_passive_cancel_receipt_or_real_fill_inference",
        "broker_order_submission",
        "threshold_or_provider_or_bot_mutation",
    ),
}


def _parse_iso_timestamp_ms(value: object) -> int:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("canonical stream timestamp must include timezone")
    return int(parsed.timestamp() * 1_000)


def _parse_iso_timestamp(value: object) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("canonical stream timestamp must include timezone")
    return parsed


def load_source_exclusion_manifest(
    path: Path = DEFAULT_SOURCE_EXCLUSION_MANIFEST,
) -> dict[str, Any]:
    """Load the fail-closed source exclusion contract used by P2 reconstruction."""

    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("P2 source exclusion manifest is missing or invalid") from exc
    return _validate_source_exclusion_manifest(payload)


def _validate_source_exclusion_manifest(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("P2 source exclusion manifest must be an object")
    if payload.get("schema") != SOURCE_EXCLUSION_SCHEMA:
        raise ValueError("P2 source exclusion manifest schema is invalid")
    if payload.get("scope_policy") != SOURCE_EXCLUSION_SCOPE_POLICY:
        raise ValueError("P2 source exclusion manifest scope policy is invalid")
    forbidden_uses = payload.get("forbidden_uses")
    if (
        any(
            not str(payload.get(field) or "").strip()
            for field in _SOURCE_EXCLUSION_CONTRACT_FIELDS
        )
        or not isinstance(forbidden_uses, list)
        or not forbidden_uses
        or any(not str(value or "").strip() for value in forbidden_uses)
    ):
        raise ValueError("P2 source exclusion manifest metric contract is invalid")
    try:
        generated_at = _parse_iso_timestamp(payload.get("generated_at"))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "P2 source exclusion manifest generated_at is invalid"
        ) from exc
    if generated_at.tzinfo is None or not re.fullmatch(
        r"[0-9a-f]{40}", str(payload.get("source_base_commit") or "")
    ):
        raise ValueError("P2 source exclusion manifest provenance is invalid")
    if (
        payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("trading_runtime_effect") is not False
        or payload.get("selection_authority") is not False
    ):
        raise ValueError("P2 source exclusion manifest authority contract is invalid")
    entries = payload.get("exclusions")
    if not isinstance(entries, list):
        raise ValueError("P2 source exclusion manifest exclusions must be a list")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("P2 source exclusion manifest summary is invalid")
    seen: set[tuple[str, str, str, int]] = set()
    trade_dates: set[str] = set()
    market_stream_row_count = 0
    event_reference_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("P2 source exclusion entry must be an object")
        try:
            scope = (
                str(entry.get("trade_date") or "").strip(),
                str(entry.get("venue") or "").strip(),
                str(entry.get("session_bucket") or "").strip(),
                int(entry.get("sequence_epoch") or 0),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("P2 source exclusion entry scope is invalid") from exc
        if not all(scope[:3]) or scope[3] <= 0:
            raise ValueError("P2 source exclusion entry scope is invalid")
        try:
            date.fromisoformat(scope[0])
        except ValueError as exc:
            raise ValueError("P2 source exclusion entry date is invalid") from exc
        if scope[1] not in {"KRX", "NXT", "SOR"} or not scope[2].startswith(
            f"{scope[1]}_"
        ):
            raise ValueError("P2 source exclusion entry venue/session is invalid")
        if scope in seen:
            raise ValueError("P2 source exclusion entry scope is duplicated")
        if not str(entry.get("reason_code") or "").strip():
            raise ValueError("P2 source exclusion entry reason is missing")
        try:
            row_count = int(entry.get("market_stream_row_count"))
            reference_count = int(entry.get("event_reference_count"))
        except (TypeError, ValueError) as exc:
            raise ValueError("P2 source exclusion entry counts are invalid") from exc
        if row_count <= 0 or reference_count < 0:
            raise ValueError("P2 source exclusion entry counts are invalid")
        try:
            window_start = _parse_iso_timestamp(entry.get("exchange_window_start"))
            window_end = _parse_iso_timestamp(entry.get("exchange_window_end"))
        except (TypeError, ValueError) as exc:
            raise ValueError("P2 source exclusion entry window is invalid") from exc
        if (
            window_end < window_start
            or window_start.date().isoformat() != scope[0]
            or window_end.date().isoformat() != scope[0]
        ):
            raise ValueError("P2 source exclusion entry window is invalid")
        if not str(entry.get("evidence") or "").strip():
            raise ValueError("P2 source exclusion entry evidence is missing")
        market_stream_row_count += row_count
        event_reference_count += reference_count
        seen.add(scope)
        trade_dates.add(scope[0])
    expected_summary = {
        "excluded_scope_count": len(entries),
        "excluded_market_stream_row_count": market_stream_row_count,
        "excluded_event_reference_count": event_reference_count,
        "trade_date_count": len(trade_dates),
    }
    if any(summary.get(field) != value for field, value in expected_summary.items()):
        raise ValueError("P2 source exclusion manifest summary counts are invalid")
    return payload


def p2_reference_exclusion_reason(
    reference: Mapping[str, Any],
    *,
    source_exclusion_manifest: Mapping[str, Any],
) -> str | None:
    """Return an exact date/venue/session/epoch exclusion reason, if present."""

    capture_started_at = _parse_iso_timestamp(reference.get("capture_started_at"))
    scope = (
        capture_started_at.date().isoformat(),
        str(reference.get("venue") or "").strip(),
        str(reference.get("session_bucket") or "").strip(),
        int(reference.get("sequence_epoch") or 0),
    )
    for entry in source_exclusion_manifest.get("exclusions") or ():
        entry_scope = (
            str(entry.get("trade_date") or "").strip(),
            str(entry.get("venue") or "").strip(),
            str(entry.get("session_bucket") or "").strip(),
            int(entry.get("sequence_epoch") or 0),
        )
        if entry_scope == scope:
            return str(entry.get("reason_code") or "source_quality_excluded")
    return None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


class EntryPolicy(StrEnum):
    MARKETABLE_NEXT_ASK = "MARKETABLE_NEXT_ASK"
    PASSIVE_EVENT_BID = "PASSIVE_EVENT_BID"
    ONE_TICK_DEEPER = "ONE_TICK_DEEPER"
    HYBRID_ENTRY = "HYBRID_ENTRY"
    RECLAIM_ENTRY = "RECLAIM_ENTRY"


class EntryExecutionMode(StrEnum):
    MARKETABLE_NEXT_ASK = "MARKETABLE_NEXT_ASK"
    PASSIVE_EVENT_BID = "PASSIVE_EVENT_BID"
    RECLAIM_MARKETABLE_NEXT_ASK = "RECLAIM_MARKETABLE_NEXT_ASK"
    HYBRID_PASSIVE_EVENT_BID = "HYBRID_PASSIVE_EVENT_BID"
    HYBRID_RECLAIM_MARKETABLE_NEXT_ASK = "HYBRID_RECLAIM_MARKETABLE_NEXT_ASK"


class ExitPolicy(StrEnum):
    SINGLE_TP = "SINGLE_TP"
    PARTIAL_TP_RUNNER = "PARTIAL_TP_RUNNER"
    TP_LADDER = "TP_LADDER"


class FillBound(StrEnum):
    UPPER_TOUCH = "UPPER_TOUCH"
    LOWER_TRADE_THROUGH = "LOWER_TRADE_THROUGH"


class SameTimestampPolicy(StrEnum):
    STOP_FIRST = "STOP_FIRST"
    MARK_AMBIGUOUS = "MARK_AMBIGUOUS"


class ReplayTerminalReason(StrEnum):
    NO_ENTRY_FILL = "NO_ENTRY_FILL"
    TAKE_PROFIT = "TAKE_PROFIT"
    PARTIAL_TAKE_PROFIT_THEN_STOP = "PARTIAL_TAKE_PROFIT_THEN_STOP"
    STOP_LOSS = "STOP_LOSS"
    HOLDING_TTL = "HOLDING_TTL"
    AMBIGUOUS_SAME_TIMESTAMP = "AMBIGUOUS_SAME_TIMESTAMP"
    PATH_ENDED = "PATH_ENDED"


@dataclass(frozen=True, slots=True)
class P2ReplayPolicy:
    policy_id: str
    policy_version: str
    entry_policy: EntryPolicy
    exit_policy: ExitPolicy
    fill_bound: FillBound
    entry_ttl_ms: int
    holding_ttl_ms: int
    take_profit_bps: float
    stop_loss_bps: float
    all_in_cost_bps: float
    target_quantity: int = 1
    partial_take_profit_fraction: float = 1.0
    same_timestamp_policy: SameTimestampPolicy = SameTimestampPolicy.STOP_FIRST
    entry_policy_version: str = "entry-policy-v1"
    exit_policy_version: str = "exit-policy-v1"
    cost_model_version: str = "all-in-cost-v1"
    runner_max_ttl_ms: int | None = None
    runner_trailing_bps: float | None = None
    runner_exit_trigger: str | None = None
    max_quote_age_ms: float = 2_500.0
    reclaim_trigger_bps: float | None = None
    hybrid_passive_ttl_ms: int | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.policy_id,
                self.policy_version,
                self.entry_policy_version,
                self.exit_policy_version,
                self.cost_model_version,
            )
        ):
            raise ValueError("policy and component versions are required")
        if self.entry_ttl_ms <= 0 or self.holding_ttl_ms <= 0:
            raise ValueError("entry and holding TTL must be positive")
        if self.take_profit_bps <= 0 or self.stop_loss_bps <= 0:
            raise ValueError("take-profit and stop-loss bps must be positive")
        if self.all_in_cost_bps < 0:
            raise ValueError("all_in_cost_bps must not be negative")
        if self.target_quantity <= 0:
            raise ValueError("target_quantity must be positive")
        if self.max_quote_age_ms <= 0:
            raise ValueError("max_quote_age_ms must be positive")
        if not 0 < self.partial_take_profit_fraction <= 1:
            raise ValueError("partial take-profit fraction must be in (0, 1]")
        object.__setattr__(self, "entry_policy", EntryPolicy(self.entry_policy))
        object.__setattr__(self, "exit_policy", ExitPolicy(self.exit_policy))
        object.__setattr__(self, "fill_bound", FillBound(self.fill_bound))
        object.__setattr__(
            self,
            "same_timestamp_policy",
            SameTimestampPolicy(self.same_timestamp_policy),
        )
        if self.entry_policy is EntryPolicy.ONE_TICK_DEEPER:
            raise ValueError(
                "entry policy is declared but not implemented in P2-A skeleton"
            )
        reclaim_entry = self.entry_policy in {
            EntryPolicy.RECLAIM_ENTRY,
            EntryPolicy.HYBRID_ENTRY,
        }
        if reclaim_entry:
            if (
                self.reclaim_trigger_bps is None
                or not math.isfinite(self.reclaim_trigger_bps)
                or self.reclaim_trigger_bps <= 0
            ):
                raise ValueError("reclaim entry requires positive reclaim_trigger_bps")
        elif self.reclaim_trigger_bps is not None:
            raise ValueError(
                "reclaim_trigger_bps is valid only for reclaim or hybrid entry"
            )
        if self.entry_policy is EntryPolicy.HYBRID_ENTRY:
            if (
                self.hybrid_passive_ttl_ms is None
                or isinstance(self.hybrid_passive_ttl_ms, bool)
                or not isinstance(self.hybrid_passive_ttl_ms, int)
                or self.hybrid_passive_ttl_ms <= 0
                or self.hybrid_passive_ttl_ms >= self.entry_ttl_ms
            ):
                raise ValueError(
                    "hybrid entry requires passive TTL below the entry TTL"
                )
        elif self.hybrid_passive_ttl_ms is not None:
            raise ValueError("hybrid_passive_ttl_ms is valid only for hybrid entry")
        if self.exit_policy is ExitPolicy.TP_LADDER:
            raise ValueError(
                "TP_LADDER is declared but not implemented in P2-A skeleton"
            )
        if self.exit_policy is ExitPolicy.SINGLE_TP:
            if self.partial_take_profit_fraction != 1.0:
                raise ValueError("SINGLE_TP requires partial_take_profit_fraction=1")
        else:
            if self.partial_take_profit_fraction >= 1.0:
                raise ValueError("PARTIAL_TP_RUNNER requires a partial TP fraction")
            if (
                self.runner_max_ttl_ms is None
                or self.runner_max_ttl_ms <= 0
                or self.runner_trailing_bps is None
                or self.runner_trailing_bps <= 0
                or self.runner_exit_trigger != "TRAILING_OR_TTL"
            ):
                raise ValueError("PARTIAL_TP_RUNNER requires frozen runner rules")


@dataclass(frozen=True, slots=True)
class P2ReplayPoint:
    exchange_timestamp_ms: int
    local_receive_timestamp_ms: int
    source_sequence: int
    trade_price: float | None = None
    trade_qty: int | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    low_price: float | None = None
    high_price: float | None = None
    quote_age_ms: float | None = None
    aggressor_side: str | None = None

    def __post_init__(self) -> None:
        if self.exchange_timestamp_ms <= 0 or self.local_receive_timestamp_ms <= 0:
            raise ValueError("timestamps must be positive")
        if self.local_receive_timestamp_ms < self.exchange_timestamp_ms:
            raise ValueError("receive timestamp must not precede exchange timestamp")
        if self.source_sequence < 0:
            raise ValueError("source_sequence must not be negative")
        for name in (
            "trade_price",
            "best_bid",
            "best_ask",
            "low_price",
            "high_price",
        ):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.trade_qty is not None and self.trade_qty < 0:
            raise ValueError("trade_qty must not be negative")
        if self.quote_age_ms is not None and self.quote_age_ms < 0:
            raise ValueError("quote_age_ms must not be negative")
        if (
            self.low_price is not None
            and self.high_price is not None
            and self.high_price < self.low_price
        ):
            raise ValueError("high_price must not be below low_price")
        if all(
            value is None
            for value in (
                self.trade_price,
                self.best_bid,
                self.best_ask,
                self.low_price,
                self.high_price,
            )
        ):
            raise ValueError("point requires price evidence")
        if self.aggressor_side not in {None, "BUY", "SELL", "UNKNOWN"}:
            raise ValueError("aggressor_side must be BUY, SELL, UNKNOWN, or null")

    @property
    def low(self) -> float | None:
        values = tuple(
            value for value in (self.low_price, self.trade_price) if value is not None
        )
        return min(values) if values else None

    @property
    def high(self) -> float | None:
        values = tuple(
            value for value in (self.high_price, self.trade_price) if value is not None
        )
        return max(values) if values else None


def load_p2_points_from_canonical_stream(
    stream_files: Iterable[Path],
    *,
    reference: dict[str, Any],
    source_exclusion_manifest: Mapping[str, Any] | None = None,
) -> tuple[P2ReplayPoint, ...]:
    """Reconstruct one event window without granting discovery authority."""

    if reference.get("schema") != "scalp_micro_reversion_path_event_reference_v2":
        raise ValueError("P2 canonical reconstruction requires a v2 reference")
    if (
        reference.get("actual_order_submitted") is not False
        or reference.get("broker_order_forbidden") is not True
        or reference.get("trading_runtime_effect") is not False
    ):
        raise ValueError("P2 reference authority contract is invalid")
    scope = (
        str(reference.get("symbol") or "").strip(),
        str(reference.get("venue") or "").strip(),
        str(reference.get("session_bucket") or "").strip(),
        int(reference.get("sequence_epoch") or 0),
    )
    if not all(scope[:3]) or scope[3] <= 0:
        raise ValueError("P2 reference stream scope is invalid")
    exclusion_manifest = (
        load_source_exclusion_manifest()
        if source_exclusion_manifest is None
        else _validate_source_exclusion_manifest(dict(source_exclusion_manifest))
    )
    exclusion_reason = p2_reference_exclusion_reason(
        reference,
        source_exclusion_manifest=exclusion_manifest,
    )
    if exclusion_reason is not None:
        raise ValueError(
            "P2 reference is excluded by source-quality manifest: "
            f"{exclusion_reason}"
        )
    start_ms = _parse_iso_timestamp_ms(reference.get("capture_started_at"))
    end_ms = _parse_iso_timestamp_ms(reference.get("capture_ended_at"))
    if end_ms < start_ms:
        raise ValueError("P2 reference capture window is invalid")
    points: list[P2ReplayPoint] = []
    seen_sequences: set[int] = set()
    for path in stream_files:
        opener = gzip.open if Path(path).suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("canonical stream row must be an object")
                stream_contract = (
                    row.get("schema"),
                    row.get("metric_contract_id"),
                )
                if stream_contract not in {
                    (
                        "scalp_micro_reversion_market_stream_point_v1",
                        "scalp_micro_reversion_market_stream_contract_v1",
                    ),
                    (
                        "scalp_micro_reversion_market_stream_point_v2",
                        "scalp_micro_reversion_market_stream_contract_v2",
                    ),
                    (
                        "scalp_micro_reversion_market_stream_point_v3",
                        "scalp_micro_reversion_market_stream_contract_v3",
                    ),
                }:
                    raise ValueError("unexpected canonical stream schema or contract")
                if (
                    row.get("actual_order_submitted") is not False
                    or row.get("broker_order_forbidden") is not True
                    or row.get("trading_runtime_effect") is not False
                ):
                    raise ValueError("canonical stream authority contract is invalid")
                row_scope = (
                    str(row.get("symbol") or "").strip(),
                    str(row.get("venue") or "").strip(),
                    str(row.get("session_bucket") or "").strip(),
                    int(row.get("sequence_epoch") or 0),
                )
                if row_scope != scope:
                    continue
                exchange_ms = _parse_iso_timestamp_ms(row.get("exchange_timestamp"))
                if exchange_ms < start_ms or exchange_ms > end_ms:
                    continue
                sequence = int(row.get("series_sequence") or 0)
                source_sequence = int(row.get("source_sequence") or 0)
                if (
                    sequence <= 0
                    or source_sequence != sequence
                    or sequence in seen_sequences
                ):
                    raise ValueError(
                        "canonical stream sequence is invalid or duplicate"
                    )
                seen_sequences.add(sequence)
                if stream_contract[0].endswith("_v3"):
                    _, eligible, _ = validate_market_stream_path_provenance(
                        path_order_status=row.get("path_order_status"),
                        path_consumer_eligible=row.get("path_consumer_eligible"),
                        exchange_timestamp_regression_ms=row.get(
                            "exchange_timestamp_regression_ms"
                        ),
                    )
                    if not eligible:
                        continue
                points.append(
                    P2ReplayPoint(
                        exchange_timestamp_ms=exchange_ms,
                        local_receive_timestamp_ms=_parse_iso_timestamp_ms(
                            row.get("local_receive_timestamp")
                        ),
                        source_sequence=sequence,
                        trade_price=_optional_float(row.get("trade_price")),
                        trade_qty=_optional_int(row.get("trade_qty")),
                        best_bid=_optional_float(row.get("best_bid")),
                        best_ask=_optional_float(row.get("best_ask")),
                        quote_age_ms=_optional_float(row.get("quote_age_ms")),
                        aggressor_side=(
                            None
                            if row.get("aggressor_side") is None
                            else str(row.get("aggressor_side"))
                        ),
                    )
                )
    points.sort(key=lambda row: (row.exchange_timestamp_ms, row.source_sequence))
    return tuple(points)


@dataclass(frozen=True, slots=True)
class P2PolicySnapshot:
    policy_id: str
    policy_version: str
    entry_policy: EntryPolicy
    exit_policy: ExitPolicy
    fill_bound: FillBound
    entry_policy_version: str
    exit_policy_version: str
    cost_model_version: str
    entry_order_ttl_ms: int
    position_holding_ttl_ms: int
    take_profit_bps: float
    stop_loss_bps: float
    all_in_cost_bps: float
    target_quantity: int
    partial_take_profit_fraction: float
    runner_max_ttl_ms: int | None
    runner_trailing_bps: float | None
    runner_exit_trigger: str | None
    same_timestamp_policy: SameTimestampPolicy
    max_quote_age_ms: float
    reclaim_trigger_bps: float | None
    hybrid_passive_ttl_ms: int | None

    @classmethod
    def from_policy(cls, policy: P2ReplayPolicy) -> "P2PolicySnapshot":
        return cls(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            entry_policy=policy.entry_policy,
            exit_policy=policy.exit_policy,
            fill_bound=policy.fill_bound,
            entry_policy_version=policy.entry_policy_version,
            exit_policy_version=policy.exit_policy_version,
            cost_model_version=policy.cost_model_version,
            entry_order_ttl_ms=policy.entry_ttl_ms,
            position_holding_ttl_ms=policy.holding_ttl_ms,
            take_profit_bps=policy.take_profit_bps,
            stop_loss_bps=policy.stop_loss_bps,
            all_in_cost_bps=policy.all_in_cost_bps,
            target_quantity=policy.target_quantity,
            partial_take_profit_fraction=policy.partial_take_profit_fraction,
            runner_max_ttl_ms=policy.runner_max_ttl_ms,
            runner_trailing_bps=policy.runner_trailing_bps,
            runner_exit_trigger=policy.runner_exit_trigger,
            same_timestamp_policy=policy.same_timestamp_policy,
            max_quote_age_ms=policy.max_quote_age_ms,
            reclaim_trigger_bps=policy.reclaim_trigger_bps,
            hybrid_passive_ttl_ms=policy.hybrid_passive_ttl_ms,
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entry_policy"] = self.entry_policy.value
        payload["exit_policy"] = self.exit_policy.value
        payload["fill_bound"] = self.fill_bound.value
        payload["same_timestamp_policy"] = self.same_timestamp_policy.value
        return payload


@dataclass(frozen=True, slots=True)
class P2ReplayResult:
    policy_id: str
    policy_version: str
    policy_contract: P2PolicySnapshot
    fill_bound: FillBound
    filled_quantity: int
    unresolved_quantity: int
    fill_fraction: float
    average_entry_price: float | None
    average_exit_price: float | None
    entry_filled_at_ms: int | None
    entry_execution_mode: EntryExecutionMode | None
    entry_confirmation_at_ms: int | None
    entry_confirmation_local_receive_at_ms: int | None
    entry_confirmation_source_sequence: int | None
    exited_at_ms: int | None
    gross_return_bps: float | None
    net_return_bps: float | None
    net_return_per_detected_signal_bps: float | None
    terminal_reason: ReplayTerminalReason
    partial_fill_observed: bool
    partial_take_profit_observed: bool
    ambiguity_observed: bool
    decision_watermark_timestamp_ms: int
    decision_watermark_local_receive_timestamp_ms: int
    decision_watermark_source_sequence: int
    source_point_count: int
    schema: str = P2_REPLAY_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fill_bound"] = self.fill_bound.value
        payload["terminal_reason"] = self.terminal_reason.value
        payload["entry_execution_mode"] = (
            None
            if self.entry_execution_mode is None
            else self.entry_execution_mode.value
        )
        payload["policy_contract"] = self.policy_contract.as_dict()
        payload.update(
            {
                "selection_authority": False,
                "sim_effect": False,
                "p2_runtime_effect": False,
                "trading_runtime_effect": False,
                "trading_decision_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                **P2_REPLAY_METRIC_CONTRACT,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class _EntryResolution:
    price: float
    exchange_timestamp_ms: int
    local_receive_timestamp_ms: int
    source_sequence: int
    filled_quantity: int
    execution_mode: EntryExecutionMode
    confirmation_exchange_timestamp_ms: int
    confirmation_local_receive_timestamp_ms: int
    confirmation_source_sequence: int


def replay_path(
    points: Iterable[P2ReplayPoint],
    *,
    policy: P2ReplayPolicy,
    decision_watermark_timestamp_ms: int,
    decision_watermark_local_receive_timestamp_ms: int,
    decision_watermark_source_sequence: int,
    event_trade_price: float | None = None,
    event_bid_price: float | None = None,
    event_bid_quote_age_ms: float | None = None,
) -> P2ReplayResult:
    """Replay one frozen policy without looking before the decision watermark."""

    if (
        decision_watermark_timestamp_ms <= 0
        or decision_watermark_local_receive_timestamp_ms
        < decision_watermark_timestamp_ms
        or decision_watermark_source_sequence < 0
    ):
        raise ValueError("decision exchange/local/sequence watermark is invalid")

    path = tuple(points)
    _validate_path(path)
    eligible = tuple(
        point
        for point in path
        if (point.exchange_timestamp_ms, point.source_sequence)
        > (decision_watermark_timestamp_ms, decision_watermark_source_sequence)
        and (point.local_receive_timestamp_ms, point.source_sequence)
        > (
            decision_watermark_local_receive_timestamp_ms,
            decision_watermark_source_sequence,
        )
    )
    entry = _resolve_entry(
        eligible,
        policy=policy,
        decision_watermark_timestamp_ms=decision_watermark_timestamp_ms,
        decision_watermark_local_receive_timestamp_ms=(
            decision_watermark_local_receive_timestamp_ms
        ),
        decision_watermark_source_sequence=decision_watermark_source_sequence,
        event_trade_price=event_trade_price,
        event_bid_price=event_bid_price,
        event_bid_quote_age_ms=event_bid_quote_age_ms,
    )
    if entry is None:
        return _empty_result(
            policy,
            decision_watermark_timestamp_ms,
            decision_watermark_local_receive_timestamp_ms,
            decision_watermark_source_sequence,
            len(path),
        )

    entry_price = entry.price
    entry_time = entry.exchange_timestamp_ms
    entry_resolution_time = entry.exchange_timestamp_ms
    entry_resolution_sequence = entry.source_sequence
    filled_quantity = entry.filled_quantity

    remaining = filled_quantity
    take_profit_quantity = max(
        1, round(filled_quantity * policy.partial_take_profit_fraction)
    )
    take_profit_quantity = min(take_profit_quantity, filled_quantity)
    take_profit_price = entry_price * (1 + policy.take_profit_bps / 10_000.0)
    stop_price = entry_price * (1 - policy.stop_loss_bps / 10_000.0)
    holding_deadline = entry_resolution_time + policy.holding_ttl_ms
    proceeds = 0.0
    exited_quantity = 0
    exit_time: int | None = None
    terminal = ReplayTerminalReason.PATH_ENDED
    partial_tp = False
    take_profit_executed_quantity = 0
    runner_active = False
    ambiguity = False
    runner_deadline = holding_deadline
    runner_peak = entry_price

    holding_points = tuple(
        point
        for point in eligible
        if (point.exchange_timestamp_ms, point.source_sequence)
        > (entry_resolution_time, entry_resolution_sequence)
    )
    for point in holding_points:
        if point.exchange_timestamp_ms > holding_deadline:
            break
        if runner_active:
            runner_peak = max(runner_peak, point.high or runner_peak)
            trailing_stop = runner_peak * (
                1 - float(policy.runner_trailing_bps or 0) / 10_000.0
            )
            stop_price = max(stop_price, trailing_stop)
            if point.exchange_timestamp_ms > runner_deadline:
                break
        stop_hit = (point.low is not None and point.low <= stop_price) or (
            _fresh_quote(point, policy)
            and point.best_bid is not None
            and point.best_bid <= stop_price
        )
        take_profit_fill_quantity = _take_profit_fill_quantity(
            point,
            target_price=take_profit_price,
            planned_quantity=(
                0
                if runner_active
                else min(
                    remaining,
                    take_profit_quantity - take_profit_executed_quantity,
                )
            ),
            bound=policy.fill_bound,
            max_quote_age_ms=policy.max_quote_age_ms,
        )
        take_profit_hit = take_profit_fill_quantity > 0
        same_point_range_crossed = (
            point.low_price is not None
            and point.high_price is not None
            and point.low_price <= stop_price
            and point.high_price >= take_profit_price
        )
        if stop_hit and (take_profit_hit or same_point_range_crossed):
            ambiguity = True
            if policy.same_timestamp_policy is SameTimestampPolicy.MARK_AMBIGUOUS:
                terminal = ReplayTerminalReason.AMBIGUOUS_SAME_TIMESTAMP
                exit_time = point.exchange_timestamp_ms
                break
            take_profit_hit = False
        if stop_hit:
            stop_execution_price = _stop_execution_price(
                point, stop_price=stop_price, policy=policy
            )
            proceeds += remaining * stop_execution_price
            exited_quantity += remaining
            remaining = 0
            exit_time = point.exchange_timestamp_ms
            terminal = (
                ReplayTerminalReason.PARTIAL_TAKE_PROFIT_THEN_STOP
                if take_profit_executed_quantity > 0
                else ReplayTerminalReason.STOP_LOSS
            )
            break
        if take_profit_hit and not runner_active:
            quantity = take_profit_fill_quantity
            proceeds += quantity * take_profit_price
            exited_quantity += quantity
            remaining -= quantity
            take_profit_executed_quantity += quantity
            exit_time = point.exchange_timestamp_ms
            partial_tp = remaining > 0
            if take_profit_executed_quantity >= take_profit_quantity and remaining > 0:
                runner_active = True
                runner_peak = max(runner_peak, point.high or take_profit_price)
                runner_deadline = min(
                    holding_deadline,
                    point.exchange_timestamp_ms + int(policy.runner_max_ttl_ms or 0),
                )
            if remaining == 0:
                terminal = ReplayTerminalReason.TAKE_PROFIT
                break

    if terminal is ReplayTerminalReason.AMBIGUOUS_SAME_TIMESTAMP:
        return P2ReplayResult(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            policy_contract=P2PolicySnapshot.from_policy(policy),
            fill_bound=policy.fill_bound,
            filled_quantity=filled_quantity,
            unresolved_quantity=remaining,
            fill_fraction=round(filled_quantity / policy.target_quantity, 6),
            average_entry_price=round(entry_price, 6),
            average_exit_price=None,
            entry_filled_at_ms=entry_time,
            entry_execution_mode=entry.execution_mode,
            entry_confirmation_at_ms=(entry.confirmation_exchange_timestamp_ms),
            entry_confirmation_local_receive_at_ms=(
                entry.confirmation_local_receive_timestamp_ms
            ),
            entry_confirmation_source_sequence=(entry.confirmation_source_sequence),
            exited_at_ms=exit_time,
            gross_return_bps=None,
            net_return_bps=None,
            net_return_per_detected_signal_bps=None,
            terminal_reason=terminal,
            partial_fill_observed=filled_quantity < policy.target_quantity,
            partial_take_profit_observed=partial_tp,
            ambiguity_observed=True,
            decision_watermark_timestamp_ms=decision_watermark_timestamp_ms,
            decision_watermark_local_receive_timestamp_ms=(
                decision_watermark_local_receive_timestamp_ms
            ),
            decision_watermark_source_sequence=decision_watermark_source_sequence,
            source_point_count=len(path),
        )

    if remaining > 0:
        effective_deadline = runner_deadline if runner_active else holding_deadline
        terminal_point = _last_at_or_before(holding_points, effective_deadline)
        deadline_matured = any(
            point.exchange_timestamp_ms >= effective_deadline
            for point in holding_points
        )
        if deadline_matured and terminal_point is not None:
            terminal_price = (
                (
                    terminal_point.best_bid
                    if _fresh_quote(terminal_point, policy)
                    else None
                )
                or terminal_point.trade_price
                or terminal_point.low
                or entry_price
            )
            proceeds += remaining * terminal_price
            exited_quantity += remaining
            remaining = 0
            exit_time = terminal_point.exchange_timestamp_ms
            terminal = ReplayTerminalReason.HOLDING_TTL

    if remaining > 0:
        realized_exit = proceeds / exited_quantity if exited_quantity > 0 else None
        return P2ReplayResult(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            policy_contract=P2PolicySnapshot.from_policy(policy),
            fill_bound=policy.fill_bound,
            filled_quantity=filled_quantity,
            unresolved_quantity=remaining,
            fill_fraction=round(filled_quantity / policy.target_quantity, 6),
            average_entry_price=round(entry_price, 6),
            average_exit_price=(
                None if realized_exit is None else round(realized_exit, 6)
            ),
            entry_filled_at_ms=entry_time,
            entry_execution_mode=entry.execution_mode,
            entry_confirmation_at_ms=(entry.confirmation_exchange_timestamp_ms),
            entry_confirmation_local_receive_at_ms=(
                entry.confirmation_local_receive_timestamp_ms
            ),
            entry_confirmation_source_sequence=(entry.confirmation_source_sequence),
            exited_at_ms=exit_time,
            gross_return_bps=None,
            net_return_bps=None,
            net_return_per_detected_signal_bps=None,
            terminal_reason=ReplayTerminalReason.PATH_ENDED,
            partial_fill_observed=filled_quantity < policy.target_quantity,
            partial_take_profit_observed=partial_tp,
            ambiguity_observed=ambiguity,
            decision_watermark_timestamp_ms=decision_watermark_timestamp_ms,
            decision_watermark_local_receive_timestamp_ms=(
                decision_watermark_local_receive_timestamp_ms
            ),
            decision_watermark_source_sequence=decision_watermark_source_sequence,
            source_point_count=len(path),
        )

    average_exit = proceeds / exited_quantity
    gross_bps = (average_exit / entry_price - 1.0) * 10_000.0
    return P2ReplayResult(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_contract=P2PolicySnapshot.from_policy(policy),
        fill_bound=policy.fill_bound,
        filled_quantity=filled_quantity,
        unresolved_quantity=0,
        fill_fraction=round(filled_quantity / policy.target_quantity, 6),
        average_entry_price=round(entry_price, 6),
        average_exit_price=round(average_exit, 6),
        entry_filled_at_ms=entry_time,
        entry_execution_mode=entry.execution_mode,
        entry_confirmation_at_ms=entry.confirmation_exchange_timestamp_ms,
        entry_confirmation_local_receive_at_ms=(
            entry.confirmation_local_receive_timestamp_ms
        ),
        entry_confirmation_source_sequence=entry.confirmation_source_sequence,
        exited_at_ms=exit_time,
        gross_return_bps=round(gross_bps, 6),
        net_return_bps=round(gross_bps - policy.all_in_cost_bps, 6),
        net_return_per_detected_signal_bps=round(
            (gross_bps - policy.all_in_cost_bps)
            * (filled_quantity / policy.target_quantity),
            6,
        ),
        terminal_reason=terminal,
        partial_fill_observed=filled_quantity < policy.target_quantity,
        partial_take_profit_observed=partial_tp,
        ambiguity_observed=ambiguity,
        decision_watermark_timestamp_ms=decision_watermark_timestamp_ms,
        decision_watermark_local_receive_timestamp_ms=(
            decision_watermark_local_receive_timestamp_ms
        ),
        decision_watermark_source_sequence=decision_watermark_source_sequence,
        source_point_count=len(path),
    )


def _resolve_entry(
    eligible: tuple[P2ReplayPoint, ...],
    *,
    policy: P2ReplayPolicy,
    decision_watermark_timestamp_ms: int,
    decision_watermark_local_receive_timestamp_ms: int,
    decision_watermark_source_sequence: int,
    event_trade_price: float | None,
    event_bid_price: float | None,
    event_bid_quote_age_ms: float | None,
) -> _EntryResolution | None:
    entry_deadline = decision_watermark_timestamp_ms + policy.entry_ttl_ms
    watermark_confirmation = (
        decision_watermark_timestamp_ms,
        decision_watermark_local_receive_timestamp_ms,
        decision_watermark_source_sequence,
    )
    if policy.entry_policy is EntryPolicy.MARKETABLE_NEXT_ASK:
        return _first_marketable_ask(
            eligible,
            policy=policy,
            deadline_ms=entry_deadline,
            execution_mode=EntryExecutionMode.MARKETABLE_NEXT_ASK,
            confirmation=watermark_confirmation,
        )

    if policy.entry_policy is EntryPolicy.PASSIVE_EVENT_BID:
        bid_price = _validated_event_bid(
            event_bid_price,
            event_bid_quote_age_ms,
            policy=policy,
            entry_policy=policy.entry_policy,
        )
        return _first_passive_fill(
            eligible,
            policy=policy,
            entry_price=bid_price,
            deadline_ms=entry_deadline,
            execution_mode=EntryExecutionMode.PASSIVE_EVENT_BID,
            confirmation=watermark_confirmation,
        )

    if (
        event_trade_price is None
        or not math.isfinite(event_trade_price)
        or event_trade_price <= 0
    ):
        raise ValueError("reclaim or hybrid entry requires event_trade_price")

    reclaim_not_before_ms = decision_watermark_timestamp_ms
    execution_mode = EntryExecutionMode.RECLAIM_MARKETABLE_NEXT_ASK
    if policy.entry_policy is EntryPolicy.HYBRID_ENTRY:
        bid_price = _validated_event_bid(
            event_bid_price,
            event_bid_quote_age_ms,
            policy=policy,
            entry_policy=policy.entry_policy,
        )
        passive_deadline = decision_watermark_timestamp_ms + int(
            policy.hybrid_passive_ttl_ms or 0
        )
        passive_fill = _first_passive_fill(
            eligible,
            policy=policy,
            entry_price=bid_price,
            deadline_ms=passive_deadline,
            execution_mode=EntryExecutionMode.HYBRID_PASSIVE_EVENT_BID,
            confirmation=watermark_confirmation,
        )
        if passive_fill is not None:
            return passive_fill
        reclaim_not_before_ms = passive_deadline
        execution_mode = EntryExecutionMode.HYBRID_RECLAIM_MARKETABLE_NEXT_ASK

    return _first_reclaim_marketable_ask(
        eligible,
        policy=policy,
        event_trade_price=event_trade_price,
        reclaim_not_before_ms=reclaim_not_before_ms,
        entry_deadline_ms=entry_deadline,
        execution_mode=execution_mode,
    )


def _validated_event_bid(
    event_bid_price: float | None,
    event_bid_quote_age_ms: float | None,
    *,
    policy: P2ReplayPolicy,
    entry_policy: EntryPolicy,
) -> float:
    label = entry_policy.value
    if (
        event_bid_price is None
        or not math.isfinite(event_bid_price)
        or event_bid_price <= 0
    ):
        raise ValueError(f"{label} requires positive event_bid_price")
    if (
        event_bid_quote_age_ms is None
        or not math.isfinite(event_bid_quote_age_ms)
        or event_bid_quote_age_ms < 0
        or event_bid_quote_age_ms > policy.max_quote_age_ms
    ):
        raise ValueError(f"{label} requires a fresh event bid quote")
    return event_bid_price


def _first_passive_fill(
    points: tuple[P2ReplayPoint, ...],
    *,
    policy: P2ReplayPolicy,
    entry_price: float,
    deadline_ms: int,
    execution_mode: EntryExecutionMode,
    confirmation: tuple[int, int, int],
) -> _EntryResolution | None:
    for point in points:
        if point.exchange_timestamp_ms > deadline_ms:
            break
        if not _passive_entry_touched(point, entry_price, policy.fill_bound):
            continue
        filled_quantity = policy.target_quantity
        if policy.fill_bound is FillBound.LOWER_TRADE_THROUGH:
            filled_quantity = min(
                policy.target_quantity, max(0, int(point.trade_qty or 0))
            )
        if filled_quantity <= 0:
            continue
        return _EntryResolution(
            price=entry_price,
            exchange_timestamp_ms=point.exchange_timestamp_ms,
            local_receive_timestamp_ms=point.local_receive_timestamp_ms,
            source_sequence=point.source_sequence,
            filled_quantity=filled_quantity,
            execution_mode=execution_mode,
            confirmation_exchange_timestamp_ms=confirmation[0],
            confirmation_local_receive_timestamp_ms=confirmation[1],
            confirmation_source_sequence=confirmation[2],
        )
    return None


def _first_marketable_ask(
    points: tuple[P2ReplayPoint, ...],
    *,
    policy: P2ReplayPolicy,
    deadline_ms: int,
    execution_mode: EntryExecutionMode,
    confirmation: tuple[int, int, int],
) -> _EntryResolution | None:
    confirmation_key = (confirmation[0], confirmation[2])
    for point in points:
        if point.exchange_timestamp_ms > deadline_ms:
            break
        if (point.exchange_timestamp_ms, point.source_sequence) <= confirmation_key:
            continue
        if point.best_ask is None or not _fresh_quote(point, policy):
            continue
        return _EntryResolution(
            price=point.best_ask,
            exchange_timestamp_ms=point.exchange_timestamp_ms,
            local_receive_timestamp_ms=point.local_receive_timestamp_ms,
            source_sequence=point.source_sequence,
            filled_quantity=policy.target_quantity,
            execution_mode=execution_mode,
            confirmation_exchange_timestamp_ms=confirmation[0],
            confirmation_local_receive_timestamp_ms=confirmation[1],
            confirmation_source_sequence=confirmation[2],
        )
    return None


def _first_reclaim_marketable_ask(
    points: tuple[P2ReplayPoint, ...],
    *,
    policy: P2ReplayPolicy,
    event_trade_price: float,
    reclaim_not_before_ms: int,
    entry_deadline_ms: int,
    execution_mode: EntryExecutionMode,
) -> _EntryResolution | None:
    running_low = event_trade_price
    confirmation: P2ReplayPoint | None = None
    reclaim_multiplier = 1 + float(policy.reclaim_trigger_bps or 0) / 10_000.0
    for point in points:
        if point.exchange_timestamp_ms > entry_deadline_ms:
            break
        point_low = point.low
        made_new_low = point_low is not None and point_low < running_low
        if made_new_low:
            running_low = float(point_low)
            confirmation = None
        if confirmation is not None:
            fill = _first_marketable_ask(
                (point,),
                policy=policy,
                deadline_ms=entry_deadline_ms,
                execution_mode=execution_mode,
                confirmation=(
                    confirmation.exchange_timestamp_ms,
                    confirmation.local_receive_timestamp_ms,
                    confirmation.source_sequence,
                ),
            )
            if fill is not None:
                return fill
        if made_new_low or point.exchange_timestamp_ms < reclaim_not_before_ms:
            continue
        if confirmation is None and (
            point.trade_price is not None
            and (point.trade_qty or 0) > 0
            and point.trade_price >= running_low * reclaim_multiplier
        ):
            confirmation = point
    return None


def _passive_entry_touched(
    point: P2ReplayPoint, entry_price: float, bound: FillBound
) -> bool:
    if bound is FillBound.UPPER_TOUCH:
        upper_prices = tuple(
            price
            for price in (point.low_price, point.trade_price, point.best_ask)
            if price is not None
        )
        return bool(upper_prices) and min(upper_prices) <= entry_price
    return (
        point.trade_price is not None
        and point.trade_price < entry_price
        and (point.trade_qty or 0) > 0
    )


def _take_profit_fill_quantity(
    point: P2ReplayPoint,
    *,
    target_price: float,
    planned_quantity: int,
    bound: FillBound,
    max_quote_age_ms: float,
) -> int:
    if bound is FillBound.UPPER_TOUCH:
        upper_prices = tuple(
            price
            for price in (
                point.high_price,
                point.trade_price,
                (
                    point.best_bid
                    if point.quote_age_ms is not None
                    and point.quote_age_ms <= max_quote_age_ms
                    else None
                ),
            )
            if price is not None
        )
        return (
            planned_quantity
            if upper_prices and max(upper_prices) >= target_price
            else 0
        )
    if (
        point.trade_price is not None
        and point.trade_price > target_price
        and (point.trade_qty or 0) > 0
    ):
        return min(planned_quantity, int(point.trade_qty or 0))
    return 0


def _fresh_quote(point: P2ReplayPoint, policy: P2ReplayPolicy) -> bool:
    return (
        point.quote_age_ms is not None
        and 0 <= point.quote_age_ms <= policy.max_quote_age_ms
    )


def _stop_execution_price(
    point: P2ReplayPoint,
    *,
    stop_price: float,
    policy: P2ReplayPolicy,
) -> float:
    candidates = [stop_price]
    candidates.extend(
        price for price in (point.low_price, point.trade_price) if price is not None
    )
    if _fresh_quote(point, policy) and point.best_bid is not None:
        candidates.append(point.best_bid)
    return min(candidates)


def _validate_path(path: tuple[P2ReplayPoint, ...]) -> None:
    previous: P2ReplayPoint | None = None
    for point in path:
        if previous is not None and (
            point.exchange_timestamp_ms < previous.exchange_timestamp_ms
            or point.local_receive_timestamp_ms < previous.local_receive_timestamp_ms
            or point.source_sequence <= previous.source_sequence
        ):
            raise ValueError(
                "path must increase by exchange/local timestamp and source sequence"
            )
        previous = point


def _last_at_or_before(
    points: tuple[P2ReplayPoint, ...], deadline_ms: int
) -> P2ReplayPoint | None:
    result = None
    for point in points:
        if point.exchange_timestamp_ms > deadline_ms:
            break
        result = point
    return result


def _empty_result(
    policy: P2ReplayPolicy,
    watermark_ts: int,
    watermark_local_receive_ts: int,
    watermark_sequence: int,
    source_point_count: int,
) -> P2ReplayResult:
    return P2ReplayResult(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_contract=P2PolicySnapshot.from_policy(policy),
        fill_bound=policy.fill_bound,
        filled_quantity=0,
        unresolved_quantity=0,
        fill_fraction=0.0,
        average_entry_price=None,
        average_exit_price=None,
        entry_filled_at_ms=None,
        entry_execution_mode=None,
        entry_confirmation_at_ms=None,
        entry_confirmation_local_receive_at_ms=None,
        entry_confirmation_source_sequence=None,
        exited_at_ms=None,
        gross_return_bps=None,
        net_return_bps=None,
        net_return_per_detected_signal_bps=0.0,
        terminal_reason=ReplayTerminalReason.NO_ENTRY_FILL,
        partial_fill_observed=False,
        partial_take_profit_observed=False,
        ambiguity_observed=False,
        decision_watermark_timestamp_ms=watermark_ts,
        decision_watermark_local_receive_timestamp_ms=watermark_local_receive_ts,
        decision_watermark_source_sequence=watermark_sequence,
        source_point_count=source_point_count,
    )
