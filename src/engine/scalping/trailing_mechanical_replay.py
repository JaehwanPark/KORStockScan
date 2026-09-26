"""Source-bound M1 trailing TP research over completed positions.

The report owner supplies strict completed trades. Modeled bids are never fills.
This module has no policy write or live order authority.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.market import session_contract
from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.scalping.trailing_mechanical_strength import (
    _ofi, CONFIG_DEFAULTS, normalize_config,
)
from src.engine.scalping.trailing_start_replay import (
    _candidate_pnl, _epoch, _flag, _number, _validated_events,
)
from src.engine.scalping.trailing_threshold_policy import (
    START_GRID_PCT, closed_exit_gap, market_type_at,
)
from src.engine.scalping.trailing_mechanical_policy import (
    CLASSIFIER_VERSION, DEFAULTS, START_MARKETS, TP_KEYS as THRESHOLD_KEYS,
    classifier_hash,
    market_values_hash, normalize_values, value_hash,
)

SCHEMA = "scalp_trailing_mechanical_market_tuning_v2"
GRID = {
    THRESHOLD_KEYS[0]: START_GRID_PCT,
    THRESHOLD_KEYS[1]: tuple(round(i / 10, 1) for i in range(2, 9)),
    THRESHOLD_KEYS[2]: tuple(round(i / 10, 1) for i in range(4, 13)),
}
DEFAULT_VECTOR = DEFAULTS
SLIPPAGE_SENSITIVITY_BPS = (0, 30, 100)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _signal(rows: list[dict], vectors: dict[str, dict]) -> tuple[dict | None, float | None]:
    armed = False
    arm_at = None
    for row in rows:
        if row.get("_signal_eligible") is False:
            continue
        vector = vectors[row["_market"]]
        strong = row["classifier_state"] == "STRONG"
        decision = evaluate_trailing_take_profit(
            peak_price=row["_peak"], executable_bid=row["_bid"],
            peak_profit_pct=row["_peak_profit"],
            start_pct=vector[THRESHOLD_KEYS[0]], strong=strong,
            weak_limit_pct=vector[THRESHOLD_KEYS[1]],
            strong_limit_pct=vector[THRESHOLD_KEYS[2]],
            already_armed=armed,
        )
        if decision.armed and not armed:
            armed, arm_at = True, row["_at"]
        if decision.triggered:
            return row, arm_at
    return None, arm_at


def _classifier_segment(fields: dict) -> tuple[str, float | None, str, str]:
    return (str(fields.get("classifier_item") or ""),
            _number(fields.get("classifier_transport_epoch")),
            str(fields.get("classifier_route_key") or ""),
            str(fields.get("classifier_market") or ""))


def _validate_classifier_journal(trade: dict, rows: list[dict]) -> str | None:
    """Require the bounded 0D/verified 0B source that produced M1 decisions."""

    receipts: dict[tuple, dict[int, dict]] = {}
    position_key = str(rows[0].get("position_key") or "")
    row_segments = {_classifier_segment(row) for row in rows}
    configured = rows[0].get("scalp_trailing_classifier_parameters")
    if configured is None:
        configured = {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
    try:
        expected_classifier_hash = classifier_hash(configured)
    except (KeyError, TypeError, ValueError):
        return "source_gap_classifier_config_invalid"
    for event in trade.get("timeline") or []:
        if not isinstance(event, dict) or event.get("stage") != "scalp_trailing_mechanical_input":
            continue
        fields = event.get("fields") or {}
        if (fields.get("classifier_version") != CLASSIFIER_VERSION
                or fields.get("classifier_sha256") != expected_classifier_hash
                or fields.get("classifier_position_key") != position_key):
            return "source_gap_classifier_journal_identity"
        item = str(fields.get("classifier_item") or "")
        epoch = _number(fields.get("classifier_transport_epoch"))
        if not item or epoch is None or not epoch.is_integer() or epoch < 0:
            return "source_gap_classifier_journal_route_or_epoch"
        segment = _classifier_segment(fields)
        if segment not in row_segments:
            continue
        segment_receipts = receipts.setdefault(segment, {})
        batch = fields.get("classifier_events")
        if not isinstance(batch, list) or not batch:
            return "source_gap_classifier_journal_unreadable"
        for observation in batch:
            if not isinstance(observation, dict):
                return "source_gap_classifier_journal_shape"
            sequence = _number(observation.get("sequence"))
            at_ms = _number(observation.get("at_ms"))
            if (sequence is None or at_ms is None or not sequence.is_integer()
                    or sequence <= 0 or at_ms <= 0
                    or int(sequence) in segment_receipts):
                return "source_gap_classifier_journal_sequence"
            touch = observation.get("touch")
            prior = observation.get("previous_touch")
            touch_values = ([_number(value) for value in touch]
                            if isinstance(touch, list) and len(touch) == 4 else [])
            if (len(touch_values) != 4 or any(value is None for value in touch_values)
                    or touch_values[0] <= 0 or touch_values[2] < touch_values[0]
                    or touch_values[1] < 0 or touch_values[3] < 0
                    or touch_values[1] + touch_values[3] <= 0):
                return "source_gap_classifier_journal_touch"
            imbalance = ((touch_values[1] - touch_values[3])
                         / (touch_values[1] + touch_values[3]))
            logged_imbalance = _number(observation.get("queue_imbalance"))
            if (logged_imbalance is None
                    or abs(imbalance - logged_imbalance) > 1e-8):
                return "source_gap_classifier_journal_imbalance"
            if prior is not None:
                if not isinstance(prior, list) or len(prior) != 4:
                    return "source_gap_classifier_journal_previous_touch"
                prior_values = [_number(value) for value in prior]
                if any(value is None for value in prior_values):
                    return "source_gap_classifier_journal_previous_touch"
                calculated_ofi = _ofi(tuple(prior_values), tuple(touch_values))
                logged_ofi = _number(observation.get("ofi_proxy"))
                if logged_ofi is None or abs(calculated_ofi - logged_ofi) > 1e-8:
                    return "source_gap_classifier_journal_ofi"
            tape = observation.get("trade_receipts")
            if not isinstance(tape, list):
                return "source_gap_classifier_journal_trade_tape"
            selected_net = 0
            selected_count = 0
            window = configured[str(segment[3])]["trade_window_ms"]
            for fill in tape:
                quantity = _number(fill.get("qty")) if isinstance(fill, dict) else None
                fill_at = _number(fill.get("received_at_ms")) if isinstance(fill, dict) else None
                if (not isinstance(fill, dict)
                        or fill.get("side") not in {"BUY", "SELL"}
                        or fill.get("source") != "kiwoom_0b_signed_trade_volume"
                        or fill.get("quality") != (
                            "signed_trade_volume_positive" if fill.get("side") == "BUY"
                            else "signed_trade_volume_negative"
                        )
                        or quantity is None or not quantity.is_integer() or quantity <= 0
                        or fill_at is None
                        or not at_ms - 1000 <= fill_at <= at_ms):
                    return "source_gap_classifier_journal_trade_receipt"
                if fill_at >= at_ms - window:
                    selected_net += int(quantity) * (1 if fill["side"] == "BUY" else -1)
                    selected_count += 1
            if ((selected_net if selected_count else None)
                    != observation.get("signed_trade_qty")):
                return "source_gap_classifier_journal_trade_sum"
            segment_receipts[int(sequence)] = observation
    for segment_receipts in receipts.values():
        ordered = sorted(segment_receipts.items())
        if any(later_seq != earlier_seq + 1
               or _number(later["at_ms"]) < _number(earlier["at_ms"])
               for (earlier_seq, earlier), (later_seq, later) in zip(ordered, ordered[1:])):
            return "source_gap_classifier_journal_depth_continuity"
        prior_trade_sequence = None
        for _, observation in ordered:
            gap = _validate_trade_peak_receipts(observation, prior_trade_sequence)
            if gap[0]:
                return gap[0]
            prior_trade_sequence = gap[1]
    for row in rows:
        segment_receipts = receipts.get(_classifier_segment(row), {})
        sequence = _number(row.get("classifier_quote_sequence"))
        new_count = int(_number(row.get("classifier_new_event_count")) or 0)
        if new_count > 0 and (sequence is None or int(sequence) not in segment_receipts):
            return "source_gap_classifier_journal_transition_unbound"
        if sequence is not None and int(sequence) in segment_receipts:
            bound = segment_receipts[int(sequence)]
            quote_at = _number(row.get("classifier_quote_received_at_ms"))
            configured_age = _number((row.get("operational_threshold_values") or {}).get(
                "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS"
            )) if isinstance(row.get("operational_threshold_values"), dict) else None
            max_age = configured_age if configured_age is not None and configured_age > 0 else 700
            if (quote_at is None or quote_at != bound["at_ms"]
                    or _number(row.get("executable_bid")) != bound["touch"][0]
                    or not 0 <= row["_at"] * 1000 - quote_at <= max_age):
                return "source_gap_classifier_journal_price_or_clock"
        if (row.get("classifier_state") == "STRONG"
                and (sequence is None or int(sequence) not in segment_receipts
                     or segment_receipts[int(sequence)].get("state") != "STRONG")):
            return "source_gap_classifier_strong_unproven"
    return None


def _validate_trade_peak_receipts(
    observation: dict, prior_trade_sequence: int | None,
) -> tuple[str | None, int | None]:
    """Check the 0B price path within one source segment."""

    peak_receipts = observation.get("trade_peak_receipts")
    if not isinstance(peak_receipts, list):
        return "source_gap_classifier_journal_trade_peak_receipts", prior_trade_sequence
    peak = 0
    prior_at = None
    for receipt in peak_receipts:
        sequence = _number(receipt.get("sequence")) if isinstance(receipt, dict) else None
        at_ms = _number(receipt.get("received_at_ms")) if isinstance(receipt, dict) else None
        price = _number(receipt.get("price")) if isinstance(receipt, dict) else None
        if (sequence is None or not sequence.is_integer() or sequence <= 0
                or at_ms is None or at_ms <= 0
                or at_ms > _number(observation["at_ms"])
                or (prior_at is not None and at_ms < prior_at)
                or (prior_trade_sequence is not None
                    and sequence != prior_trade_sequence + 1)
                or price is None or not price.is_integer() or price <= 0):
            return "source_gap_classifier_journal_trade_peak_receipt", prior_trade_sequence
        prior_trade_sequence, prior_at = int(sequence), at_ms
        peak = max(peak, int(price))
    if (observation.get("trade_peak_gap")
            or _number(observation.get("trade_peak_price_since_prior_depth")) != peak):
        return "source_gap_classifier_journal_trade_peak", prior_trade_sequence
    return None, prior_trade_sequence


def _expand_event_time_rows(
    rows: list[dict], observations: list[dict], incumbent: dict[str, dict],
) -> tuple[list[dict], str | None]:
    """Bind each completed 0D evaluation to its raw quote and event peak."""

    raw_by_sequence = {
        (row["_classifier_segment"], int(row["sequence"])): row
        for row in observations
    }
    expanded = []
    previous_sequence = None
    previous_peak = None
    previous_segment = None
    for row in rows:
        segment = _classifier_segment(row)
        if segment != previous_segment:
            previous_sequence = None
            previous_segment = segment
        if previous_peak is not None and row["_peak"] < previous_peak:
            return [], "source_gap_event_time_replay_peak_reversal"
        sequence = int(row["classifier_quote_sequence"])
        count = int(row["classifier_new_event_count"])
        event_replay = row.get("classifier_event_replay")
        if count > 0 and isinstance(event_replay, list):
            if len(event_replay) != count:
                return [], "source_gap_event_time_replay_count"
            expected = list(range(sequence - count + 1, sequence + 1))
            sequence_values = [_number(event.get("sequence"))
                               if isinstance(event, dict) else None
                               for event in event_replay]
            if any(value is None or not value.is_integer() for value in sequence_values):
                return [], "source_gap_event_time_replay_sequence"
            actual = [int(value) for value in sequence_values]
            if actual != expected or (previous_sequence is not None
                                      and expected[0] != previous_sequence + 1):
                return [], "source_gap_event_time_replay_sequence"
            for event in event_replay:
                raw = raw_by_sequence.get((segment, int(event["sequence"])))
                if raw is None:
                    return [], "source_gap_event_time_replay_raw_missing"
                at_ms = _number(event.get("at_ms"))
                peak = _number(event.get("peak_price"))
                peak_profit = _number(event.get("peak_profit_pct"))
                bid = _number(event.get("executable_bid"))
                bid_qty = _number(event.get("executable_bid_qty"))
                trade_peak = _number(raw.get("trade_peak_price_since_prior_depth"))
                if (at_ms is None or peak is None or peak_profit is None
                        or bid is None or bid_qty is None or trade_peak is None
                        or peak <= 0 or bid <= 0 or bid_qty <= 0
                        or not bid_qty.is_integer() or raw.get("trade_peak_gap")
                        or at_ms != _number(raw.get("at_ms"))
                        or bid != _number(raw["touch"][0])
                        or bid_qty != _number(raw["touch"][1])
                        or event.get("classifier_state") != raw.get("state")
                        or at_ms / 1000 > row["_at"]):
                    return [], "source_gap_event_time_replay_source_or_price"
                if previous_peak is not None and peak != max(previous_peak, trade_peak, bid):
                    return [], "source_gap_event_time_replay_peak_path"
                if peak > row["_peak"]:
                    return [], "source_gap_event_time_replay_peak_path"
                if (peak == row["_peak"]
                        and abs(peak_profit - row["_peak_profit"]) > 1e-8):
                    return [], "source_gap_event_time_replay_peak_profit"
                at = at_ms / 1000.0
                market = market_type_at(at)
                if (market not in START_MARKETS or event.get("market") != market
                        or _number(event.get("start_pct")) !=
                        incumbent[market][THRESHOLD_KEYS[0]]):
                    return [], "source_gap_event_time_replay_market_or_policy"
                strong = event["classifier_state"] == "STRONG"
                limit = incumbent[market][THRESHOLD_KEYS[2] if strong else THRESHOLD_KEYS[1]]
                if (_number(event.get("raw_limit_pct")) != limit
                        or _number(event.get("peak_profit_pct")) is None):
                    return [], "source_gap_event_time_replay_width"
                session = session_contract.resolve_market_session(
                    datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul"))
                )
                expanded.append({
                    **row, "_at": at, "_market": market,
                    "_peak": peak, "_peak_profit": peak_profit,
                    "_bid": bid, "_strong": strong, "_limit": limit,
                    "classifier_state": event["classifier_state"],
                    "classifier_quote_sequence": int(event["sequence"]),
                    "executable_bid_qty": int(bid_qty),
                    "_signal_eligible": bool(
                        not session.blocker and session.exit_allowed_by_clock
                    ),
                })
                previous_peak = peak
            last_event = expanded[-1]
            if (row["_at"] > last_event["_at"]
                    and (row["_peak"] != last_event["_peak"]
                         or row["_bid"] != last_event["_bid"]
                         or row.get("classifier_state") != last_event["classifier_state"])):
                # A later 0B peak, a new trusted bid, or source expiry can
                # change the poll decision after the last 0D in this batch.
                expanded.append(row)
                previous_peak = row["_peak"]
            previous_sequence = sequence
        elif count > 1 or (segment, sequence) not in raw_by_sequence and count > 0:
            return [], "source_gap_event_time_replay_missing"
        elif previous_sequence is not None and sequence > previous_sequence + 1:
            return [], "source_gap_event_time_replay_sequence"
        elif count == 0 and previous_sequence == sequence:
            expanded.append({**row, "_signal_eligible": False})
            previous_peak = row["_peak"]
        else:
            expanded.append(row)
            previous_sequence = sequence
            previous_peak = row["_peak"]
    return expanded, None


def prepare_position(trade: dict) -> dict:
    """Validate an ordered, same-generation source path once per position."""

    if (trade.get("trailing_event_source_status") != "structured_partition_read"
            or not trade.get("trailing_event_source_sha256")):
        return {"rows": [], "source_gap": "source_gap_structured_event_provenance",
                "evidence_grade": None}
    holding_starts = [event for event in trade.get("timeline") or []
                      if isinstance(event, dict)
                      and event.get("stage") == "holding_started"
                      and (event.get("fields") or {}).get(
                          "pipeline_lifecycle_population_scope") == "real_record_bound"
                      and _epoch(event.get("timestamp")) is not None]
    if len(holding_starts) != 1:
        return {"rows": [], "source_gap": "source_gap_holding_start_identity",
                "evidence_grade": None}
    events = [event.get("fields") or {} for event in trade.get("timeline") or []
              if isinstance(event, dict)
              and event.get("stage") == "scalp_trailing_input_transition"]
    if (any(event.get("classifier_version") == CLASSIFIER_VERSION for event in events)
            and any(event.get("classifier_version") != CLASSIFIER_VERSION for event in events)):
        return {"rows": [], "source_gap": "source_gap_mixed_policy_generation",
                "evidence_grade": None}
    rows, gap = _validated_events(events)
    result = {"rows": rows, "source_gap": gap, "evidence_grade": None}
    if gap:
        return result
    if any(_flag(row.get("classifier_journal_gap")) is True for row in rows):
        result.update(rows=[], source_gap="source_gap_classifier_journal_append_failed")
        return result
    if any(_flag(row.get("classifier_event_time_gap")) is True for row in rows):
        result.update(rows=[], source_gap="source_gap_classifier_event_time_crossing_unresolved")
        return result
    quote_sequences = [_number(row.get("classifier_quote_sequence")) for row in rows]
    event_counts = [_number(row.get("classifier_new_event_count")) for row in rows]
    if any(value is None or not value.is_integer() for value in quote_sequences + event_counts):
        result.update(rows=[], source_gap="source_gap_mechanical_event_sequence_missing")
        return result
    if any(
        not row.get("classifier_item")
        or not row.get("classifier_route_key")
        or row.get("classifier_market") != row["_market"]
        or (epoch := _number(row.get("classifier_transport_epoch"))) is None
        or not epoch.is_integer() or epoch < 0
        for row in rows
    ):
        result.update(rows=[], source_gap="source_gap_mechanical_source_identity")
        return result
    journal_gap = _validate_classifier_journal(trade, rows)
    if journal_gap:
        result.update(rows=[], source_gap=journal_gap)
        return result
    row_segments = {_classifier_segment(row) for row in rows}
    result["classifier_observations"] = sorted(
        ({**observation, "_classifier_segment": _classifier_segment(event.get("fields") or {})}
         for event in trade.get("timeline") or []
         if isinstance(event, dict)
         and event.get("stage") == "scalp_trailing_mechanical_input"
         and _classifier_segment(event.get("fields") or {}) in row_segments
         for observation in (event.get("fields") or {}).get("classifier_events") or []),
        key=lambda observation: (int(observation["at_ms"]),
                                 int(observation["sequence"])),
    )
    trade_id = str(trade.get("id") or "").strip()
    expected_position_key = f"record:{trade_id}" if trade_id else ""
    if (not expected_position_key
            or any(row.get("position_key") != expected_position_key for row in rows)):
        result.update(rows=[], source_gap="source_gap_position_trade_identity")
        return result
    if rows[0]["_at"] < _epoch(holding_starts[0]["timestamp"]):
        result.update(rows=[], source_gap="source_gap_pre_holding_observation")
        return result
    for earlier, later in zip(rows, rows[1:]):
        if (later["_at"] - earlier["_at"] > 2
                and _number(later.get("tuning_grid_evaluations_since_event")) <= 1
                and not closed_exit_gap(earlier["_at"], later["_at"])):
            result.update(rows=[], source_gap="source_gap_live_evaluation_interval")
            return result
    if any(row.get("tuning_mechanical_bin_version") !=
           "start_0p1_width_0p1_mechanical_v1" for row in rows):
        if any(_number(row.get("tuning_grid_evaluations_since_event")) != 1
               for row in rows):
            result.update(rows=[], source_gap="source_gap_mechanical_crossing_coverage")
            return result
    first = events[0]
    scalar = first.get("scalp_trailing_policy_values")
    vector = first.get("scalp_trailing_market_values")
    try:
        if not isinstance(scalar, dict):
            raise ValueError("scalar_policy_missing")
        normalize_values(scalar)
        scalar_sha = value_hash(scalar)
        if (first.get("scalp_trailing_policy_value_sha256") != scalar_sha
                or any(event.get("scalp_trailing_policy_value_sha256") != scalar_sha
                       for event in events)):
            raise ValueError("scalar_policy_generation")
        if not isinstance(vector, dict):
            raise ValueError("market_vector_missing")
        explicit_classifier = first.get("scalp_trailing_classifier_parameters") is not None
        classifier_values = first.get("scalp_trailing_classifier_parameters")
        if classifier_values is None:
            classifier_values = {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
        digest = market_values_hash(vector, classifier_values)
        if any(event.get("scalp_trailing_market_values_sha256") != digest
               or event.get("scalp_trailing_market_values") != vector
               or event.get("classifier_version") != CLASSIFIER_VERSION
               or event.get("classifier_sha256") != classifier_hash(classifier_values)
               or (explicit_classifier and event.get(
                   "scalp_trailing_classifier_parameters") != classifier_values)
               for event in events):
            raise ValueError("market_vector_or_classifier_generation")
        grade = "mechanical_direct"
        for row in rows:
            incumbent = vector[row["_market"]]
            state = str(row.get("classifier_state") or "")
            if state not in {"STRONG", "WEAK", "UNKNOWN"}:
                raise ValueError("classifier_state_missing")
            first_crossing = row.get("first_crossing")
            latched_width = _flag(row.get("selected_width_from_latch")) is True
            if latched_width:
                if (not isinstance(first_crossing, dict)
                        or first_crossing.get("classifier_version") != CLASSIFIER_VERSION
                        or first_crossing.get("threshold_key") not in {
                            THRESHOLD_KEYS[1], THRESHOLD_KEYS[2]
                        }
                        or _number(first_crossing.get("at_epoch")) is None
                        or first_crossing["at_epoch"] > row["_at"]):
                    raise ValueError("first_crossing_latch_invalid")
                strong = first_crossing["threshold_key"] == THRESHOLD_KEYS[2]
            else:
                strong = state == "STRONG"
            limit = incumbent[THRESHOLD_KEYS[2] if strong else THRESHOLD_KEYS[1]]
            logged_start = _number(row.get("trailing_start_pct"))
            if (strong != row["_strong"] or abs(float(limit) - row["_limit"]) > 1e-8
                    or logged_start is None
                    or abs(float(incumbent[THRESHOLD_KEYS[0]]) - logged_start) > 1e-8):
                raise ValueError("incumbent_classifier_or_width_mismatch")
        signal = trade.get("exit_signal") or {}
        if signal.get("inferred") or _epoch(signal.get("timestamp")) is None:
            grade = "source_path_terminal_unproven"
        expanded, expansion_gap = _expand_event_time_rows(
            rows, result["classifier_observations"], vector,
        )
        if expansion_gap:
            result.update(rows=[], source_gap=expansion_gap)
            return result
        first_signal = _signal(expanded, vector)[0]
        for row in rows:
            crossing = row.get("first_crossing")
            if not isinstance(crossing, dict):
                continue
            crossing_at = _number(crossing.get("at_epoch"))
            crossing_key = crossing.get("threshold_key")
            expected_key = (
                THRESHOLD_KEYS[2]
                if first_signal and first_signal["classifier_state"] == "STRONG"
                else THRESHOLD_KEYS[1]
            )
            if (first_signal is None or crossing_at != first_signal["_at"]
                    or crossing_key != expected_key):
                result.update(rows=[], source_gap="source_gap_first_crossing_replay_mismatch")
                return result
        result.update({"rows": expanded, "incumbent": vector,
                       "classifier_parameters": classifier_values,
                       "evidence_grade": grade,
                       "policy_sha256": market_values_hash(vector, classifier_values)})
    except (KeyError, TypeError, ValueError) as exc:
        result["source_gap"] = f"source_gap_mechanical_{exc}"
        result["rows"] = []
    return result


def replay_vector(
    trade: dict, prepared: dict, candidate: dict[str, dict],
    *, actual_exit_rule: str, candidate_rows: list[dict] | None = None,
) -> dict:
    """Replay one full three-market vector against the same realized exit."""

    if prepared.get("source_gap"):
        return {"status": "source_gap", "source_gap": prepared["source_gap"]}
    try:
        market_values_hash(candidate)
    except (KeyError, TypeError, ValueError):
        return {"status": "source_gap", "source_gap": "source_gap_candidate_vector"}
    signal = trade.get("exit_signal") or {}
    signal_at = _epoch(signal.get("timestamp")) if not signal.get("inferred") else None
    terminal_grade = prepared["evidence_grade"]
    if signal_at is None:
        # A preserved order-send event can reconstruct the terminal clock only
        # when its rule is explicit and the completed SELL follows that order.
        sent = [event for event in trade.get("timeline") or []
                if isinstance(event, dict) and event.get("stage") == "sell_order_sent"
                and not event.get("is_inferred")
                and (event.get("fields") or {}).get("exit_rule") == actual_exit_rule
                and _epoch(event.get("timestamp")) is not None]
        sells = trade.get("sell_fill_legs")
        if len(sent) == 1 and isinstance(sells, list) and sells:
            order_at = _epoch(sent[0]["timestamp"])
            order_no = str((sent[0].get("fields") or {}).get("ord_no") or "").strip()
            fill_order_nos = {str(leg.get("order_no") or leg.get("ord_no") or "").strip()
                              for leg in sells if isinstance(leg, dict)}
            sell_ats = [_epoch(leg.get("at")) for leg in sells
                        if isinstance(leg, dict)]
            if (order_no and fill_order_nos == {order_no}
                    and len(sell_ats) == len(sells)
                    and all(at is not None and at >= order_at
                            for at in sell_ats)):
                signal_at = order_at
                terminal_grade = "historical_reconstructed"
    if signal_at is None:
        return {"status": "source_gap", "source_gap": "source_gap_direct_or_order_signal_missing"}
    cache_key = (actual_exit_rule, signal_at)
    if prepared.get("_terminal_key") != cache_key:
        prepared["_terminal_rows"] = [
            row for row in prepared["rows"] if row["_at"] <= signal_at + 1
        ]
        prepared["_terminal_key"] = cache_key
        prepared.pop("_incumbent_signal", None)
    rows = prepared["_terminal_rows"]
    if not rows or signal_at - rows[-1]["_at"] > 15:
        return {"status": "source_gap", "source_gap": "source_gap_exit_signal_coverage"}
    buys = trade.get("buy_fill_legs")
    sells = trade.get("sell_fill_legs")
    if (not isinstance(buys, list) or not buys
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in buys)
            or max(_epoch(leg["at"]) for leg in buys) > rows[0]["_at"] + 1):
        return {"status": "source_gap", "source_gap": "source_gap_buy_fill_clock"}
    if (not isinstance(sells, list) or not sells
            or any(not isinstance(leg, dict) or _epoch(leg.get("at")) is None
                   for leg in sells)
            or min(_epoch(leg["at"]) for leg in sells) < signal_at - 1):
        return {"status": "source_gap", "source_gap": "source_gap_sell_before_exit_signal"}
    if "_incumbent_signal" not in prepared:
        prepared["_incumbent_signal"] = _signal(rows, prepared["incumbent"])[0]
    incumbent = prepared["_incumbent_signal"]
    is_tp = actual_exit_rule == "scalp_trailing_take_profit"
    if is_tp and (incumbent is None or abs(incumbent["_at"] - signal_at) > 1):
        return {"status": "source_gap", "source_gap": "source_gap_incumbent_trigger_not_reproduced"}
    if not is_tp and incumbent and incumbent["_at"] < signal_at - 1:
        return {"status": "source_gap", "source_gap": "source_gap_competing_exit_order"}
    actual_pnl = _number(trade.get("realized_pnl_krw"))
    amount = _number(trade.get("buy_fill_amount"))
    if actual_pnl is None or amount is None or amount <= 0:
        return {"status": "source_gap", "source_gap": "source_gap_actual_cost_economics"}
    if candidate_rows is not None:
        if (len(candidate_rows) != len(prepared["rows"])
                or any(candidate_row.get("_at") != original.get("_at")
                       for candidate_row, original in zip(candidate_rows, prepared["rows"]))):
            return {"status": "source_gap", "source_gap": "source_gap_classifier_candidate_rows"}
        candidate_rows = [row for row in candidate_rows if row["_at"] <= signal_at + 1]
    first, arm_at = _signal(candidate_rows if candidate_rows is not None else rows, candidate)
    state = "same_observed_exit"
    modeled = actual_pnl
    gap = None
    censor_reason = None
    candidate_execution: dict[str, Any] | None = None
    modeled_slippage_pnl: tuple[float, ...] = ()
    if first is not None and first["_at"] < signal_at - 1:
        qty = _number(trade.get("buy_filled_qty"))
        bid_qty = _number(first.get("executable_bid_qty"))
        cost = _number(trade.get("effective_cost_rate"))
        candidate_execution = {
            "model": "first_crossing_top_bid",
            "slippage_sensitivity_bps": list(SLIPPAGE_SENSITIVITY_BPS),
        }
        if bid_qty is None or bid_qty <= 0:
            modeled, gap, state = None, "source_gap_executable_bid_depth_missing", "source_gap"
        elif qty is not None and qty > 0 and bid_qty < qty:
            fillable_qty = max(0.0, min(qty, bid_qty))
            fillable_fraction = fillable_qty / qty
            candidate_execution.update({
                "fillable_qty_at_trigger_bid": fillable_qty,
                "required_qty": qty,
                "fillable_fraction": round(fillable_fraction, 6),
                "residual_qty": qty - fillable_qty,
                "identified_partial_proceeds_after_cost_krw": (
                    round(first["_bid"] * fillable_qty * (1.0 - cost), 2)
                    if cost is not None and 0 < cost <= 0.05 else None
                ),
                "identified_partial_buy_basis_krw": (
                    round(float(trade["buy_fill_amount"]) * fillable_fraction, 2)
                    if _number(trade.get("buy_fill_amount")) is not None else None
                ),
            })
            modeled, state = None, "censored_insufficient_trigger_bid_depth"
            censor_reason = "observed_top_bid_depth_covers_only_part_of_position"
        else:
            modeled, gap = _candidate_pnl(trade, first)
            state = "source_gap" if gap else "modeled_earlier_full_sell"
            if gap is None and modeled is not None and qty is not None and cost is not None:
                gross_proceeds = first["_bid"] * qty
                modeled_slippage_pnl = tuple(
                    round(
                        modeled - gross_proceeds * (1.0 - cost) * bps / 10000.0,
                        2,
                    )
                    for bps in SLIPPAGE_SENSITIVITY_BPS
                )
                candidate_execution.update({
                    "required_qty": qty,
                    "observed_top_bid_qty": bid_qty,
                    "full_quantity_depth_supported": True,
                    "modeled_pnl_by_slippage_bps": modeled_slippage_pnl,
                })
    elif is_tp and (first is None or first["_at"] > signal_at + 1):
        modeled, state = None, "censored_after_actual_take_profit"
        censor_reason = "candidate_trigger_after_observed_take_profit_or_not_observed"
    elif first is not None and not is_tp:
        state = "same_time_competing_exit_priority"
        candidate_execution = {
            "model": "observed_competing_exit_priority",
            "competing_exit_rule": actual_exit_rule,
        }
    active = None
    if first:
        chosen = candidate[first["_market"]]
        active = chosen[THRESHOLD_KEYS[2] if first["classifier_state"] == "STRONG"
                        else THRESHOLD_KEYS[1]]
    first_quote_pnl = _candidate_pnl(trade, first)[0] if first else None
    paired_delta = round(modeled - actual_pnl, 2) if modeled is not None else None
    if paired_delta is None:
        paired_delta_by_slippage: tuple[float, ...] | None = None
    elif modeled_slippage_pnl:
        paired_delta_by_slippage = tuple(
            round(value - actual_pnl, 2) for value in modeled_slippage_pnl
        )
    else:
        paired_delta_by_slippage = tuple(
            paired_delta for _ in SLIPPAGE_SENSITIVITY_BPS
        )
    result = {
        "status": state, "source_gap": gap,
        "evidence_grade": terminal_grade,
        "first_arm_at_epoch": arm_at,
        "first_trigger_at_epoch": first["_at"] if first else None,
        "first_trigger_market": first["_market"] if first else None,
        "first_trigger_bid": first["_bid"] if first else None,
        "start_minus_active_limit_pct": (
            round(candidate[first["_market"]][THRESHOLD_KEYS[0]] - active, 6)
            if first else None
        ),
        "modeled_or_observed_pnl_krw": modeled,
        "paired_delta_pnl_krw": paired_delta,
        "paired_delta_pnl_by_slippage_bps": paired_delta_by_slippage,
        "candidate_execution": candidate_execution,
        "first_trigger_modeled_net_pct": (
            round(100 * first_quote_pnl / amount, 6)
            if first_quote_pnl is not None else None
        ),
        "fill_model": "best_bid_full_qty_configured_cost"
        if state == "modeled_earlier_full_sell" else None,
    }
    if censor_reason:
        result["censor_reason"] = censor_reason
    if candidate_execution is not None:
        result["candidate_execution"] = candidate_execution
    return result


def _metric(rows: list[tuple[dict, dict]]) -> dict:
    capital = sum(float(trade["buy_fill_amount"]) for trade, _ in rows)
    delta = sum(float(replay["paired_delta_pnl_krw"]) for _, replay in rows)
    sensitivity = {}
    for bps in SLIPPAGE_SENSITIVITY_BPS:
        key = str(bps)
        slippage_index = SLIPPAGE_SENSITIVITY_BPS.index(bps)
        eligible = [
            (trade, replay, (replay.get("paired_delta_pnl_by_slippage_bps") or ())[slippage_index]
             if len(replay.get("paired_delta_pnl_by_slippage_bps") or ())
             > slippage_index else None)
            for trade, replay in rows
        ]
        eligible = [(trade, replay, delta) for trade, replay, delta in eligible
                    if delta is not None]
        scenario_capital = sum(float(trade["buy_fill_amount"]) for trade, _, _ in eligible)
        scenario_delta = sum(float(delta) for _, _, delta in eligible)
        sensitivity[key] = {
            "n": len(eligible),
            "delta_net_krw": round(scenario_delta, 2),
            "paired_ev_pct": (
                round(100 * scenario_delta / scenario_capital, 6)
                if scenario_capital > 0 else None
            ),
        }
    signs = {
        1 if row["paired_ev_pct"] > 0 else -1 if row["paired_ev_pct"] < 0 else 0
        for row in sensitivity.values() if row["paired_ev_pct"] is not None
    }
    return {
        "n": len(rows), "delta_net_krw": round(delta, 2),
        "paired_ev_pct": round(100 * delta / capital, 6) if capital > 0 else None,
        "execution_slippage_sensitivity": sensitivity,
        "slippage_sign_reversal": -1 in signs and 1 in signs,
        "large_loss_worsened_ids": sorted(str(trade.get("id")) for trade, replay in rows
            if replay["paired_delta_pnl_krw"] < 0
            and replay["modeled_or_observed_pnl_krw"] < 0),
    }


CLASSIFIER_RESEARCH_GRID = (
    ("queue_cutoff_0p1", "m1", 0.1, 0.0, 0, 2),
    ("ofi_cutoff_0p1", "m1", 0.0, 0.1, 0, 2),
    ("net_trade_cutoff_10", "m1", 0.0, 0.0, 10, 2),
    ("adverse_updates_3", "m1", 0.0, 0.0, 0, 3),
    ("queue_only", "queue", 0.0, 0.0, 0, 2),
    ("ofi_only", "ofi", 0.0, 0.0, 0, 2),
    ("trade_only", "trade", 0.0, 0.0, 0, 2),
)

CLASSIFIER_POLICY_GRID = {
    "trade_window_ms": (500, 1000),
    "strong_queue_min": (0.0, 0.1),
    "strong_ofi_min": (0.0, 0.1),
    "strong_signed_qty_min": (0, 10),
    "weak_queue_negative_min": (0.0, 0.1),
    "weak_ofi_negative_min": (0.0, 0.1),
    "weak_signed_qty_negative_min": (0, 10),
    "adverse_updates_required": (2, 3),
}
CLASSIFIER_PAIR_AXES = (
    ("strong_queue_min", "strong_ofi_min"),
    ("strong_queue_min", "strong_signed_qty_min"),
    ("strong_ofi_min", "strong_signed_qty_min"),
    ("weak_queue_negative_min", "weak_ofi_negative_min"),
    ("weak_queue_negative_min", "weak_signed_qty_negative_min"),
    ("weak_ofi_negative_min", "weak_signed_qty_negative_min"),
)
CLASSIFIER_WIDTH_INTERACTIONS = (
    ("strong_queue_min", THRESHOLD_KEYS[2]),
    ("adverse_updates_required", THRESHOLD_KEYS[2]),
    ("weak_queue_negative_min", THRESHOLD_KEYS[1]),
    ("weak_signed_qty_negative_min", THRESHOLD_KEYS[1]),
)


def _classifier_policy_research(
    by_id: dict, outcome_by_id: dict, usable: dict, valid_dates: dict,
    holdout_days: set[str],
) -> dict:
    """Bounded one-market classifier candidates on the entire completed base."""

    result = {
        "schema": "mechanical_strength_closed_loop_research_v2",
        "decision_authority": "report_only_until_reviewed_selection",
        "grid_sha256": _digest({"axes": CLASSIFIER_POLICY_GRID,
                                "pairs": CLASSIFIER_PAIR_AXES,
                                "width_interactions": CLASSIFIER_WIDTH_INTERACTIONS}),
        "markets": {}, "research_candidate": None,
    }
    if not usable:
        result["status"] = "hold_source_gap_no_direct_positions"
        return result
    latest_id = max(usable, key=lambda ident: (valid_dates.get(ident) or "", ident))
    parent = usable[latest_id]
    if any(item["policy_sha256"] != parent["policy_sha256"] for item in usable.values()):
        result["status"] = "hold_mixed_policy_generation"
        return result
    baseline = parent["classifier_parameters"]
    variants = []
    for market in START_MARKETS:
        exposed = [ident for ident, item in usable.items()
                   if any(row["_market"] == market for row in item["rows"])]
        result["markets"][market] = {"exposed_ids": sorted(exposed), "candidates": []}
        if not exposed:
            continue
        axis_changes = {
            key: next((value for value in choices if value != baseline[market][key]), None)
            for key, choices in CLASSIFIER_POLICY_GRID.items()
        }
        changes = [{key: value} for key, value in axis_changes.items()
                   if value is not None]
        changes.extend({a: axis_changes[a], b: axis_changes[b]}
                       for a, b in CLASSIFIER_PAIR_AXES
                       if axis_changes[a] is not None and axis_changes[b] is not None)
        for change in changes:
            candidate = {session: dict(params) for session, params in baseline.items()}
            candidate[market].update(change)
            digest = market_values_hash(parent["incumbent"], candidate)
            variants.append((market, change, candidate, parent["incumbent"], digest))
            result["markets"][market]["candidates"].append(digest)
        for classifier_axis, width_axis in CLASSIFIER_WIDTH_INTERACTIONS:
            changed_value = axis_changes[classifier_axis]
            if changed_value is None:
                continue
            for step in (-0.1, 0.1):
                width = round(parent["incumbent"][market][width_axis] + step, 1)
                if width not in GRID[width_axis]:
                    continue
                values = {session: dict(params) for session, params
                          in parent["incumbent"].items()}
                values[market][width_axis] = width
                if values[market][THRESHOLD_KEYS[2]] < values[market][THRESHOLD_KEYS[1]]:
                    continue
                candidate = {session: dict(params) for session, params in baseline.items()}
                candidate[market][classifier_axis] = changed_value
                digest = market_values_hash(values, candidate)
                variants.append((market, {classifier_axis: changed_value,
                                          width_axis: width}, candidate, values, digest))
                result["markets"][market]["candidates"].append(digest)
    if not variants:
        result["status"] = "unidentified_no_exposure"
        return result
    replayed: dict[str, dict[str, dict]] = {}
    changed: dict[str, set[str]] = {}
    for market, change, candidate, values, digest in variants:
        rows = {}
        changed_ids = set()
        for ident, item in usable.items():
            if not any(row["_market"] == market for row in item["rows"]):
                rows[ident] = {
                    "status": "not_exposed_zero_effect", "source_gap": None,
                    "modeled_or_observed_pnl_krw": by_id[ident].get("realized_pnl_krw"),
                    "paired_delta_pnl_krw": 0.0,
                    "paired_delta_pnl_by_slippage_bps": (0.0, 0.0, 0.0),
                    "evidence_grade": item["evidence_grade"],
                }
                continue
            candidate_rows = _classifier_variant_rows(item, candidate)
            if any(original["classifier_state"] != proposed["classifier_state"]
                   and original["_market"] == market
                   for original, proposed in zip(item["rows"], candidate_rows)):
                changed_ids.add(ident)
            rows[ident] = replay_vector(
                by_id[ident], item, values,
                actual_exit_rule=str(outcome_by_id[ident].get("exit_rule") or ""),
                candidate_rows=candidate_rows,
            )
        replayed[digest] = rows
        changed[digest] = changed_ids
    # A sealed variant with no train-side executable continuation remains in
    # the report, but cannot erase support for every other variant. Admission
    # to the comparison pool uses train dates only; holdout is never used to
    # choose which variants participate in the train ranking.
    train_ids_all = {ident for ident in usable
                     if valid_dates.get(ident) not in holdout_days}
    exposed_by_market = {
        market: set(result["markets"][market]["exposed_ids"])
        for market in START_MARKETS
    }
    comparison_pool = {
        digest for market, _, _, _, digest in variants
        if len({ident for ident, row in replayed[digest].items()
                if ident in train_ids_all
                and ident in exposed_by_market[market]
                and row.get("paired_delta_pnl_krw") is not None}) >= 30
    }
    result["train_comparison_pool_sha256"] = sorted(comparison_pool)
    result["train_ineligible_candidate_sha256"] = sorted(
        set(replayed) - comparison_pool
    )
    common = set(usable) if comparison_pool else set()
    for digest, rows in replayed.items():
        if digest not in comparison_pool:
            continue
        common.intersection_update(ident for ident, row in rows.items()
                                  if row.get("paired_delta_pnl_krw") is not None)
    result["common_support_ids"] = sorted(common)
    result["candidate_count"] = len(variants)
    ranked = []
    for market, change, candidate, values, digest in variants:
        rows = replayed[digest]
        candidate_common = {ident for ident in common
                            if rows[ident].get("paired_delta_pnl_krw") is not None}
        train_ids = sorted(ident for ident in candidate_common
                           if valid_dates[ident] not in holdout_days)
        holdout_ids = sorted(ident for ident in candidate_common
                             if valid_dates[ident] in holdout_days)
        train = _metric([(by_id[ident], rows[ident]) for ident in train_ids])
        holdout = _metric([(by_id[ident], rows[ident]) for ident in holdout_ids])
        changed_train = sorted(changed[digest].intersection(train_ids))
        changed_holdout = sorted(changed[digest].intersection(holdout_ids))
        entry = {
            "market": market, "changed_axes": change, "classifier_parameters": candidate,
            "values": values, "market_values_sha256": digest,
            "train": train, "holdout": holdout,
            "changed_train_ids": changed_train, "changed_holdout_ids": changed_holdout,
            "changed_train_symbol_count": len({
                str(by_id[ident].get("code") or by_id[ident].get("symbol") or "")
                for ident in changed_train
            } - {""}),
            "changed_holdout_symbol_count": len({
                str(by_id[ident].get("code") or by_id[ident].get("symbol") or "")
                for ident in changed_holdout
            } - {""}),
            "common_support_ids": sorted(common),
            "candidate_pairable_common_ids": sorted(candidate_common),
            "train_comparison_eligible": digest in comparison_pool,
            "censored_ids": sorted(set(usable) - candidate_common),
            "censor_reason_by_id": {
                ident: rows[ident].get("censor_reason") or rows[ident].get("source_gap")
                for ident in usable if ident not in candidate_common
            },
        }
        result.setdefault("candidates", {})[digest] = entry
        if digest in comparison_pool:
            ranked.append(entry)
    if not ranked or not common:
        result["status"] = "hold_sample_or_common_support"
        return result
    ranked.sort(key=lambda row: (
        -(row["train"]["execution_slippage_sensitivity"]["100"]["paired_ev_pct"]
          if row["train"]["execution_slippage_sensitivity"]["100"]["paired_ev_pct"] is not None
          else float("-inf")),
        len(row["changed_axes"]), row["market_values_sha256"],
    ))
    result["train_ranked_sha256"] = [row["market_values_sha256"] for row in ranked]
    winner = ranked[0]
    holdout_changed_symbols = {
        str(by_id[ident].get("code") or by_id[ident].get("symbol") or "")
        for ident in winner["changed_holdout_ids"]
    } - {""}
    train_changed_symbols = {
        str(by_id[ident].get("code") or by_id[ident].get("symbol") or "")
        for ident in winner["changed_train_ids"]
    } - {""}
    day_metrics = []
    for day in sorted(holdout_days):
        daily = [(by_id[ident], replayed[winner["market_values_sha256"]][ident])
                 for ident in common if valid_dates[ident] == day]
        daily_metric = _metric(daily)["execution_slippage_sensitivity"]["100"]
        daily_excluded_notional = sum(
            float(by_id[ident].get("buy_fill_amount") or 0)
            for ident in by_id if ident not in common and valid_dates.get(ident) == day
        )
        daily_capital = sum(float(trade["buy_fill_amount"]) for trade, _ in daily)
        day_metrics.append(
            100 * (daily_metric["delta_net_krw"] - daily_excluded_notional)
            / (daily_capital + daily_excluded_notional)
            if daily_capital + daily_excluded_notional > 0 else None
        )
    worst_day = min(day_metrics) if day_metrics and all(value is not None for value in day_metrics) else None
    worst_slippage = winner["holdout"]["execution_slippage_sensitivity"]["100"]
    excluded_holdout_notional = sum(
        float(by_id[ident].get("buy_fill_amount") or 0)
        for ident in by_id if ident not in common and valid_dates.get(ident) in holdout_days
    )
    conservative_holdout_delta = round(
        winner["holdout"]["delta_net_krw"] - excluded_holdout_notional, 2
    )
    conservative_worst_slippage_delta = round(
        worst_slippage["delta_net_krw"] - excluded_holdout_notional, 2
    )
    result["joint_selection_evidence"] = {
        "winner_sha256": winner["market_values_sha256"],
        "unpaired_holdout_worst_case_notional_krw": excluded_holdout_notional,
        "holdout_conservative_delta_krw": conservative_holdout_delta,
        "holdout_conservative_worst_slippage_delta_krw": conservative_worst_slippage_delta,
        "holdout_worst_slippage_min_day_ev_pct": worst_day,
        "tail_review_required": bool(
            winner["train"]["large_loss_worsened_ids"]
            or winner["holdout"]["large_loss_worsened_ids"]
        ),
        "multiple_comparison_candidate_count": len(variants),
    }
    qualified = (
        all(valid_dates.get(ident) for ident in by_id)
        and len({day for day in valid_dates.values() if day}) >= 7
        and len(holdout_days) >= 2
        and winner["train"]["n"] >= 30 and winner["holdout"]["n"] >= 10
        and len(winner["changed_train_ids"]) >= 10
        and len(winner["changed_holdout_ids"]) >= 5
        and len(train_changed_symbols) >= 2 and len(holdout_changed_symbols) >= 2
        and winner["train"]["paired_ev_pct"] is not None
        and winner["train"]["paired_ev_pct"] > 0
        and winner["holdout"]["paired_ev_pct"] is not None
        and winner["holdout"]["paired_ev_pct"] > 0
        and worst_slippage["paired_ev_pct"] is not None
        and worst_slippage["paired_ev_pct"] > 0
        and conservative_holdout_delta > 0
        and conservative_worst_slippage_delta > 0
        and worst_day is not None and worst_day > 0
        and not result["joint_selection_evidence"]["tail_review_required"]
    )
    if qualified:
        result["research_candidate"] = {
            "values": winner["values"],
            "classifier_parameters": winner["classifier_parameters"],
            "market_values_sha256": winner["market_values_sha256"],
            "changed_market": winner["market"],
            "decision_authority": "research_candidate_requires_policy_selection",
        }
        result["status"] = "research_candidate_holdout_positive_review_required"
    else:
        result["status"] = "hold_sample_or_edge_or_safety"
    return result


def _classifier_variant_rows(prepared: dict, variant: tuple | dict) -> list[dict]:
    """Recompute a sealed research rule from validated, ordered raw receipts."""

    if isinstance(variant, dict):
        if set(variant) == set(START_MARKETS):
            market_params = {market: normalize_config(variant[market])
                             for market in START_MARKETS}
        else:
            params = normalize_config(variant)
            market_params = {market: params for market in START_MARKETS}
        mode = "m1"
    else:
        _, mode, queue_cutoff, ofi_cutoff, trade_cutoff, adverse_limit = variant
        params = normalize_config({
            **CONFIG_DEFAULTS,
            "strong_queue_min": queue_cutoff,
            "strong_ofi_min": ofi_cutoff,
            "strong_signed_qty_min": trade_cutoff,
            "weak_queue_negative_min": queue_cutoff,
            "weak_ofi_negative_min": ofi_cutoff,
            "weak_signed_qty_negative_min": trade_cutoff,
            "adverse_updates_required": adverse_limit,
        })
        market_params = {market: params for market in START_MARKETS}
    strong = False
    adverse = 0
    by_sequence: dict[tuple, str] = {}
    previous_segment = None
    for observation in prepared["classifier_observations"]:
        segment = observation["_classifier_segment"]
        params = market_params[segment[3]]
        if segment != previous_segment:
            strong, adverse = False, 0
            previous_segment = segment
        sequence = int(observation["sequence"])
        key = (segment, sequence)
        queue = _number(observation.get("queue_imbalance"))
        ofi = _number(observation.get("ofi_proxy"))
        tape = observation.get("trade_receipts")
        if not isinstance(tape, list):
            by_sequence[key] = "UNKNOWN"
            strong, adverse = False, 0
            continue
        at_ms = int(observation["at_ms"])
        selected_tape = [receipt for receipt in tape
                         if receipt["received_at_ms"] >= at_ms - params["trade_window_ms"]]
        net = (sum(receipt["qty"] * (1 if receipt["side"] == "BUY" else -1)
                   for receipt in selected_tape) if selected_tape else None)
        if (queue is None or ofi is None
                or (mode in {"m1", "trade"} and observation.get("trade_gap"))):
            strong, adverse = False, 0
            by_sequence[key] = "UNKNOWN"
            continue
        if mode == "m1":
            if net is None:
                strong, adverse = False, 0
                by_sequence[key] = "UNKNOWN"
                continue
            positive = (queue > params["strong_queue_min"]
                        and ofi > params["strong_ofi_min"]
                        and net > params["strong_signed_qty_min"])
            negative = (queue < -params["weak_queue_negative_min"]
                        and ofi < -params["weak_ofi_negative_min"]
                        and net < -params["weak_signed_qty_negative_min"])
        elif mode == "queue":
            positive = queue > params["strong_queue_min"]
            negative = queue < -params["weak_queue_negative_min"]
        elif mode == "ofi":
            positive = ofi > params["strong_ofi_min"]
            negative = ofi < -params["weak_ofi_negative_min"]
        else:
            if net is None:
                strong, adverse = False, 0
                by_sequence[key] = "UNKNOWN"
                continue
            positive = net > params["strong_signed_qty_min"]
            negative = net < -params["weak_signed_qty_negative_min"]
        if positive:
            strong, adverse = True, 0
        elif strong and negative:
            adverse += 1
            if adverse >= params["adverse_updates_required"]:
                strong, adverse = False, 0
        else:
            adverse = 0
        by_sequence[key] = "STRONG" if strong else "WEAK"
    result = []
    for row in prepared["rows"]:
        trade_only_unknown = (
            mode in {"queue", "ofi"}
            and str(row.get("classifier_reason") or "").startswith("trade_")
        )
        state = (
            by_sequence.get((_classifier_segment(row),
                             int(row["classifier_quote_sequence"])), "UNKNOWN")
            if row.get("classifier_state") != "UNKNOWN" or trade_only_unknown
            else "UNKNOWN"
        )
        result.append({**row, "classifier_state": state})
    return result


def _classifier_parameter_research(
    by_id: dict, outcome_by_id: dict, usable: dict, valid_dates: dict,
    holdout_days: set[str],
) -> dict:
    """Report parameter and width interactions without granting policy authority."""

    result = {
        "schema": "mechanical_strength_raw_journal_sensitivity_v1",
        "decision_authority": "report_only_no_runtime_apply",
        "grid_sha256": _digest(CLASSIFIER_RESEARCH_GRID),
        "grid": [list(row) for row in CLASSIFIER_RESEARCH_GRID],
        "markets": {}, "research_candidate": None,
    }
    if not usable:
        result["status"] = "source_gap_no_direct_m1_completed_positions"
        return result
    variant_rows = {
        (trade_id, name): _classifier_variant_rows(item, variant)
        for trade_id, item in usable.items()
        for variant in CLASSIFIER_RESEARCH_GRID
        for name in [variant[0]]
    }
    for market in START_MARKETS:
        ids = [trade_id for trade_id, item in usable.items()
               if any(row["_market"] == market for row in item["rows"])]
        scenarios = {}
        scenario_pairs = {}
        for variant in CLASSIFIER_RESEARCH_GRID:
            name = variant[0]
            for width_axis in THRESHOLD_KEYS[1:]:
                for width in sorted({
                    round(DEFAULT_VECTOR[width_axis] + offset, 1)
                    for offset in (-0.2, -0.1, 0.0, 0.1, 0.2)
                    if round(DEFAULT_VECTOR[width_axis] + offset, 1)
                    in GRID[width_axis]
                }):
                    key = f"{name}|{width_axis}={width:.1f}"
                    paired = []
                    censored = []
                    strong_ids = []
                    for trade_id in ids:
                        item = usable[trade_id]
                        rows = variant_rows[(trade_id, name)]
                        if any(row["_market"] == market and row["classifier_state"] == "STRONG"
                               for row in rows):
                            strong_ids.append(trade_id)
                        vector = {session: dict(values)
                                  for session, values in item["incumbent"].items()}
                        vector[market][width_axis] = width
                        try:
                            market_values_hash(vector)
                        except (KeyError, TypeError, ValueError):
                            continue
                        replay = replay_vector(
                            by_id[trade_id], item, vector,
                            actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
                            candidate_rows=rows,
                        )
                        if replay.get("paired_delta_pnl_krw") is None:
                            censored.append(trade_id)
                        else:
                            paired.append((by_id[trade_id], replay))
                    train = [(trade, replay) for trade, replay in paired
                             if valid_dates[str(trade["id"])] not in holdout_days]
                    holdout = [(trade, replay) for trade, replay in paired
                               if valid_dates[str(trade["id"])] in holdout_days]
                    scenarios[key] = {
                        "variant": name, "width_axis": width_axis,
                        "width_pct": width,
                        "strong_exposure_ids": sorted(strong_ids),
                        "paired_ids": sorted(str(trade["id"]) for trade, _ in paired),
                        "censored_or_gap_ids": sorted(censored),
                        "train": _metric(train) if train else None,
                        "holdout": _metric(holdout) if holdout else None,
                    }
                    scenario_pairs[key] = paired
        common = set(ids)
        for paired in scenario_pairs.values():
            common.intersection_update(str(trade["id"]) for trade, _ in paired)
        for key, paired in scenario_pairs.items():
            common_rows = [(trade, replay) for trade, replay in paired
                           if str(trade["id"]) in common]
            common_train = [(trade, replay) for trade, replay in common_rows
                            if valid_dates[str(trade["id"])] not in holdout_days]
            common_holdout = [(trade, replay) for trade, replay in common_rows
                              if valid_dates[str(trade["id"])] in holdout_days]
            scenarios[key]["common_train"] = _metric(common_train) if common_train else None
            scenarios[key]["common_holdout"] = (
                _metric(common_holdout) if common_holdout else None
            )
        result["markets"][market] = {
            "completed_ids": sorted(ids), "scenarios": scenarios,
            "common_support_ids": sorted(common),
            "status": ("research_only_no_live_candidate" if common else
                       "unidentified_no_common_support" if ids else "no_direct_exposure"),
        }
    result["status"] = "research_only_no_live_candidate"
    return result


def summarize_mechanical(
    trades: list[dict], outcomes: list[dict], *, population_complete: bool,
) -> dict:
    """Report bounded single and pair sensitivities; never select live policy."""

    trade_ids = [str(trade.get("id")) for trade in trades]
    outcome_ids = [str(row.get("record_id")) for row in outcomes]
    by_id = {str(trade.get("id")): trade for trade in trades}
    outcome_by_id = {str(row.get("record_id")): row for row in outcomes}
    identity_complete = bool(
        len(by_id) == len(trades) and len(outcome_by_id) == len(outcomes)
        and set(trade_ids) == set(outcome_ids) and "None" not in by_id
    )
    all_ids = sorted(set(by_id) & set(outcome_by_id))
    valid_dates = {}
    entry_date_fallback_ids = []
    completion_clock_mismatch_ids = []
    for trade_id in all_ids:
        completion_day = outcome_by_id[trade_id].get("completion_observed_date")
        sell_legs = by_id[trade_id].get("sell_fill_legs") or []
        sell_epochs = [_epoch(leg.get("at")) for leg in sell_legs
                       if isinstance(leg, dict)]
        final_fill_day = (
            datetime.fromtimestamp(max(sell_epochs), ZoneInfo("Asia/Seoul"))
            .date().isoformat()
            if sell_epochs and len(sell_epochs) == len(sell_legs)
            and all(epoch is not None for epoch in sell_epochs)
            else None
        )
        raw = str(completion_day or final_fill_day
                  or outcome_by_id[trade_id].get("rec_date") or "")
        if completion_day and final_fill_day and completion_day != final_fill_day:
            completion_clock_mismatch_ids.append(trade_id)
        if not completion_day and not final_fill_day:
            entry_date_fallback_ids.append(trade_id)
        try:
            if date.fromisoformat(raw).isoformat() != raw:
                raise ValueError("date_format")
            valid_dates[trade_id] = raw
        except ValueError:
            valid_dates[trade_id] = None
    days = sorted({day for day in valid_dates.values() if day is not None})
    holdout_days = set(days[-max(2, math.ceil(len(days) * .2)):]) if len(days) >= 3 else set()
    prepared = {trade_id: prepare_position(by_id[trade_id]) for trade_id in all_ids}
    for trade_id, day in valid_dates.items():
        if day is None and not prepared[trade_id].get("source_gap"):
            prepared[trade_id]["source_gap"] = "source_gap_completed_outcome_date"
        if (trade_id in completion_clock_mismatch_ids
                and not prepared[trade_id].get("source_gap")):
            prepared[trade_id]["source_gap"] = "source_gap_completion_fill_day_mismatch"
    for trade_id, item in prepared.items():
        if item.get("source_gap"):
            continue
        baseline = replay_vector(
            by_id[trade_id], item, item["incumbent"],
            actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
        )
        if baseline.get("source_gap"):
            item["source_gap"] = baseline["source_gap"]
        else:
            item["evidence_grade"] = baseline["evidence_grade"]
    usable = {trade_id: item for trade_id, item in prepared.items()
              if not item.get("source_gap")}
    result = {
        "schema": SCHEMA, "decision_authority": "report_only_no_runtime_apply",
        "classifier_version": CLASSIFIER_VERSION,
        "numeric_axes": list(THRESHOLD_KEYS),
        "classifier_parameter_research": {
            "schema": "mechanical_strength_raw_journal_sensitivity_v1",
            "status": "hold_population_census_or_empty",
            "research_candidate": None,
        },
        "classifier_policy_research": {
            "schema": "mechanical_strength_closed_loop_research_v2",
            "status": "hold_population_census_or_empty",
            "research_candidate": None,
        },
        "strict_completed_position_ids": sorted(set(trade_ids)),
        "position_identity_census_complete": identity_complete,
        "population_complete": bool(population_complete),
        "source_gap_by_id": {trade_id: item["source_gap"] for trade_id, item in prepared.items()
                             if item.get("source_gap")},
        "evidence_grade_counts": dict(Counter(item["evidence_grade"] for item in usable.values())),
        "evidence_grade_by_id": {trade_id: item["evidence_grade"]
                                 for trade_id, item in usable.items()},
        "policy_sha256_by_id": {trade_id: item["policy_sha256"]
                                for trade_id, item in usable.items()},
        "classifier_state_counts": dict(Counter(
            str(row.get("classifier_state")) for item in usable.values()
            for row in item["rows"]
        )),
        "strong_exposure_ids": sorted(
            trade_id for trade_id, item in usable.items()
            if any(row.get("classifier_state") == "STRONG" for row in item["rows"])
        ),
        "unknown_exposure_ids": sorted(
            trade_id for trade_id, item in usable.items()
            if any(row.get("classifier_state") == "UNKNOWN" for row in item["rows"])
        ),
        "holdout_date_basis": "completion_observed_date_or_final_sell_fill_day",
        "entry_date_fallback_ids": sorted(entry_date_fallback_ids),
        "completion_clock_mismatch_ids": sorted(completion_clock_mismatch_ids),
        "holdout_days": sorted(holdout_days), "markets": {},
        "research_candidate": None, "runtime_selected": None,
    }
    applied_generation_outcome = {}
    for policy_sha in sorted({item["policy_sha256"] for item in usable.values()}):
        ids = sorted(ident for ident, item in usable.items()
                     if item["policy_sha256"] == policy_sha)
        pnl = sum(float(by_id[ident]["realized_pnl_krw"]) for ident in ids)
        capital = sum(float(by_id[ident]["buy_fill_amount"]) for ident in ids)
        applied_generation_outcome[policy_sha] = {
            "completed_ids": ids, "n": len(ids),
            "realized_net_pnl_krw": round(pnl, 2),
            "realized_notional_weighted_ev_pct": (
                round(100 * pnl / capital, 6) if capital > 0 else None
            ),
            "decision_authority": "observed_realized_outcome_no_counterfactual_lift",
        }
    result["applied_generation_outcome"] = applied_generation_outcome
    for trade_id in set(by_id) - set(outcome_by_id):
        result["source_gap_by_id"][trade_id] = "source_gap_position_outcome_missing"
    if not population_complete or not all_ids or not identity_complete:
        result["status"] = (
            "hold_position_identity_census" if not identity_complete
            else "hold_population_census_or_empty"
        )
        return result
    result["classifier_parameter_research"] = _classifier_parameter_research(
        by_id, outcome_by_id, usable, valid_dates, holdout_days,
    )
    result["classifier_policy_research"] = _classifier_policy_research(
        by_id, outcome_by_id, usable, valid_dates, holdout_days,
    )
    grids = GRID
    result["grid"] = {key: list(values) for key, values in grids.items()}
    result["grid_sha256"] = _digest(result["grid"])
    for market in START_MARKETS:
        exposed = {trade_id for trade_id, item in usable.items()
                   if any(row["_market"] == market for row in item["rows"])}
        market_result = {"exposed_ids": sorted(exposed), "axes": {},
                         "pairs": {}, "common_support_ids": [],
                         "source_eligible_ids": sorted(usable),
                         "research_candidate": None, "runtime_selected": None}
        result["markets"][market] = market_result
        if not exposed:
            market_result.update({
                "common_support_ids": sorted(usable),
                "excluded_ids": sorted(set(all_ids) - set(usable)),
                "grid_censored_or_gap_ids": [], "combinations": {},
                "status": ("no_live_exit_exposure" if market == "PREMARKET"
                           else "unidentified_no_market_exposure"),
            })
            continue
        market_grids = {
            axis: tuple(sorted(set(grids[axis]) | {
                item["incumbent"][market][axis] for item in usable.values()
            }))
            for axis in THRESHOLD_KEYS
        }
        market_result["grid"] = {axis: list(values)
                                 for axis, values in market_grids.items()}
        market_result["grid_sha256"] = _digest(market_result["grid"])
        cache: dict[tuple, dict[str, dict]] = {}
        invalid_vector_candidates = []
        def valid_market_change(changes: dict[str, float | int]) -> bool:
            for trade_id, item in usable.items():
                if trade_id not in exposed:
                    continue
                vector = {**item["incumbent"][market], **changes}
                if vector[THRESHOLD_KEYS[2]] < vector[THRESHOLD_KEYS[1]]:
                    return False
            return True
        def evaluate(changes: dict[str, float | int]) -> dict[str, dict]:
            key = tuple(sorted(changes.items()))
            if key not in cache:
                rows = {}
                for trade_id, item in usable.items():
                    if trade_id not in exposed:
                        rows[trade_id] = {
                            "status": "not_exposed_zero_effect", "source_gap": None,
                            "modeled_or_observed_pnl_krw": by_id[trade_id].get("realized_pnl_krw"),
                            "paired_delta_pnl_krw": 0.0,
                        }
                        continue
                    candidate = {session: dict(values) for session, values in item["incumbent"].items()}
                    candidate[market].update(changes)
                    rows[trade_id] = replay_vector(
                        by_id[trade_id], item, candidate,
                        actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
                    )
                cache[key] = rows
            return cache[key]
        for axis in THRESHOLD_KEYS:
            axis_rows = {}
            for value in market_grids[axis]:
                if not valid_market_change({axis: value}):
                    invalid_vector_candidates.append(f"{axis}={value}")
                    continue
                axis_rows[str(value)] = evaluate({axis: value})
            market_result["axes"][axis] = axis_rows
        for left, right in itertools.combinations(THRESHOLD_KEYS, 2):
            pair_name = f"{left}×{right}"
            pair_rows = {}
            for a, b in itertools.product(market_grids[left], market_grids[right]):
                if not valid_market_change({left: a, right: b}):
                    invalid_vector_candidates.append(f"{pair_name}={a}|{b}")
                    continue
                pair_rows[f"{a}|{b}"] = evaluate({left: a, right: b})
            market_result["pairs"][pair_name] = pair_rows
        market_result["invalid_vector_candidates"] = invalid_vector_candidates
        all_candidates = [candidate for axis in market_result["axes"].values()
                          for candidate in axis.values()]
        all_candidates.extend(candidate for pair in market_result["pairs"].values()
                              for candidate in pair.values())
        common = set(usable)
        for candidate in all_candidates:
            common.intersection_update(trade_id for trade_id, row in candidate.items()
                                      if row.get("paired_delta_pnl_krw") is not None)
        market_result["common_support_ids"] = sorted(common)
        market_result["excluded_ids"] = sorted(set(all_ids) - set(usable))
        market_result["grid_censored_or_gap_ids"] = sorted(set(usable) - common)
        for collection in (market_result["axes"], market_result["pairs"]):
            for name, candidates in collection.items():
                collection[name] = {
                    key: {
                        "train": _metric([(by_id[trade_id], row) for trade_id, row in rows.items()
                                          if trade_id in common
                                          and valid_dates[trade_id] not in holdout_days]),
                        "holdout": _metric([(by_id[trade_id], row) for trade_id, row in rows.items()
                                            if trade_id in common
                                            and valid_dates[trade_id] in holdout_days]),
                        "comparison_support_ids": sorted(common),
                        "pairable_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if row.get("paired_delta_pnl_krw") is not None),
                        "censored_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if str(row.get("status") or "").startswith("censored_")),
                        "censor_reason_by_id": {
                            trade_id: row["censor_reason"]
                            for trade_id, row in rows.items()
                            if row.get("censor_reason")
                        },
                        "source_gap_ids": sorted(trade_id for trade_id, row in rows.items()
                                                 if row.get("status") == "source_gap"),
                    } for key, rows in candidates.items()
                }
        baseline_rows = evaluate({})
        baseline_train = _metric([
            (by_id[trade_id], row) for trade_id, row in baseline_rows.items()
            if trade_id in common and valid_dates[trade_id] not in holdout_days
        ])
        baseline_ev = baseline_train["paired_ev_pct"]
        for pair_name in market_result["pairs"]:
            left, right = pair_name.split("×")
            for label, metric in market_result["pairs"][pair_name].items():
                a, b = label.split("|")
                left_metric = market_result["axes"][left].get(a)
                right_metric = market_result["axes"][right].get(b)
                pair_ev = metric["train"]["paired_ev_pct"]
                left_ev = (left_metric or {}).get("train", {}).get("paired_ev_pct")
                right_ev = (right_metric or {}).get("train", {}).get("paired_ev_pct")
                same_support = (
                    metric["comparison_support_ids"]
                    == (left_metric or {}).get("comparison_support_ids")
                    == (right_metric or {}).get("comparison_support_ids")
                )
                metric["train_interaction_ev_pct"] = (
                    round(pair_ev - left_ev - right_ev + baseline_ev, 6)
                    if same_support and None not in (pair_ev, left_ev, right_ev, baseline_ev)
                    else None
                )
        market_result["combinations"] = {}
        if len(days) >= 7 and len(usable) >= 40 and exposed:
            latest_id = max(usable, key=lambda trade_id: (
                valid_dates[trade_id], trade_id
            ))
            baseline = usable[latest_id]["incumbent"][market]
            pools: dict[str, tuple] = {}
            for axis in THRESHOLD_KEYS:
                choices = []
                for value, metric in market_result["axes"][axis].items():
                    ev = metric["train"]["paired_ev_pct"]
                    if ev is not None and float(value) != float(baseline[axis]):
                        choices.append((ev, float(value)))
                for pair_name, metrics in market_result["pairs"].items():
                    pair_axes = pair_name.split("×")
                    if axis not in pair_axes:
                        continue
                    axis_index = pair_axes.index(axis)
                    for label, metric in metrics.items():
                        ev = metric["train_interaction_ev_pct"]
                        value = float(label.split("|")[axis_index])
                        if ev is not None and value != float(baseline[axis]):
                            choices.append((ev, value))
                ranked = sorted(choices, key=lambda row: (-row[0], row[1]))
                two = []
                for _, value in ranked:
                    if value not in two:
                        two.append(value)
                    if len(two) == 2:
                        break
                pools[axis] = (baseline[axis], *two)
            market_result["train_frozen_axis_pools"] = {
                axis: list(values) for axis, values in pools.items()
            }
            market_result["train_frozen_pool_sha256"] = _digest(
                market_result["train_frozen_axis_pools"]
            )
            for values in itertools.product(*(pools[axis] for axis in THRESHOLD_KEYS)):
                changes = dict(zip(THRESHOLD_KEYS, values))
                if changes[THRESHOLD_KEYS[2]] < changes[THRESHOLD_KEYS[1]]:
                    continue
                rows = evaluate(changes)
                train_rows = [(by_id[trade_id], row) for trade_id, row in rows.items()
                              if trade_id in common
                              and valid_dates[trade_id] not in holdout_days]
                holdout_rows = [(by_id[trade_id], row) for trade_id, row in rows.items()
                                if trade_id in common
                                and valid_dates[trade_id] in holdout_days]
                label = "|".join(str(value) for value in values)
                market_result["combinations"][label] = {
                    "values": changes, "train": _metric(train_rows),
                    "holdout": _metric(holdout_rows),
                    "comparison_support_ids": sorted(common),
                    "pairable_ids": sorted(trade_id for trade_id, row in rows.items()
                                           if row.get("paired_delta_pnl_krw") is not None),
                        "censored_ids": sorted(trade_id for trade_id, row in rows.items()
                                               if str(row.get("status") or "").startswith("censored_")),
                        "censor_reason_by_id": {
                            trade_id: row["censor_reason"]
                            for trade_id, row in rows.items()
                            if row.get("censor_reason")
                        },
                }
        market_result["status"] = "research_only_no_live_candidate"
    if len(days) >= 7 and len(usable) >= 40:
        market_choices = {}
        for market in START_MARKETS:
            latest_id = max(usable, key=lambda trade_id: (
                valid_dates[trade_id], trade_id
            ))
            incumbent = usable[latest_id]["incumbent"][market]
            if not result["markets"][market]["exposed_ids"]:
                market_choices[market] = [incumbent]
                continue
            combos = result["markets"][market]["combinations"]
            ranked = sorted(
                (row for row in combos.values()
                 if row["train"]["n"] >= 30
                 and row["train"]["paired_ev_pct"] is not None
                 and row["values"] != incumbent),
                key=lambda row: (-row["train"]["paired_ev_pct"],
                                 sum(row["values"][axis] != incumbent[axis]
                                     for axis in THRESHOLD_KEYS),
                                 _digest(row["values"])),
            )
            market_choices[market] = [incumbent, *(row["values"] for row in ranked[:2])]
        joint = {}
        joint_replays = {}
        for vectors in itertools.product(*(market_choices[market] for market in START_MARKETS)):
            candidate = dict(zip(START_MARKETS, vectors))
            digest = market_values_hash(candidate, usable[latest_id]["classifier_parameters"])
            replayed = {
                trade_id: replay_vector(
                    by_id[trade_id], item, candidate,
                    actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
                ) for trade_id, item in usable.items()
            }
            joint_replays[digest] = replayed
            joint[digest] = {"values": candidate}
        joint_common = set(usable)
        for replayed in joint_replays.values():
            joint_common.intersection_update(
                trade_id for trade_id, row in replayed.items()
                if row.get("paired_delta_pnl_krw") is not None
            )
        result["joint_common_support_ids"] = sorted(joint_common)
        result["joint_grid_censored_or_gap_ids"] = sorted(set(usable) - joint_common)
        for digest, replayed in joint_replays.items():
            paired = {trade_id: row for trade_id, row in replayed.items()
                      if row.get("paired_delta_pnl_krw") is not None}
            train = [(by_id[trade_id], replayed[trade_id]) for trade_id in joint_common
                     if valid_dates[trade_id] not in holdout_days]
            holdout = [(by_id[trade_id], replayed[trade_id]) for trade_id in joint_common
                       if valid_dates[trade_id] in holdout_days]
            joint[digest].update({
                "train": _metric(train), "holdout": _metric(holdout),
                "comparison_support_ids": sorted(joint_common),
                "pairable_ids": sorted(paired),
                "excluded_ids": sorted(set(all_ids) - joint_common),
                "censored_ids": sorted(trade_id for trade_id, row in replayed.items()
                                       if str(row.get("status") or "").startswith("censored_")),
                "censor_reason_by_id": {
                    trade_id: row["censor_reason"]
                    for trade_id, row in replayed.items()
                    if row.get("censor_reason")
                },
                "source_gap_ids": sorted(trade_id for trade_id, row in replayed.items()
                                        if row.get("status") == "source_gap"),
                "evidence_grade_counts": dict(Counter(
                    replayed[trade_id].get("evidence_grade") for trade_id in joint_common
                )),
            })
        result["joint_three_market"] = joint
        result["joint_candidate_count"] = len(joint)
        result["joint_train_ranked_sha256"] = [
            digest for digest, row in sorted(
                joint.items(), key=lambda item: (
                    -(item[1]["train"]["paired_ev_pct"]
                      if item[1]["train"]["paired_ev_pct"] is not None
                      else float("-inf")),
                    sum(
                        item[1]["values"][market][axis]
                        != usable[latest_id]["incumbent"][market][axis]
                        for market in START_MARKETS for axis in THRESHOLD_KEYS
                    ),
                    item[0]
                )
            )
        ]
        if result["joint_train_ranked_sha256"]:
            winner_sha = result["joint_train_ranked_sha256"][0]
            winner = joint[winner_sha]
            holdout_pairs = [(by_id[trade_id], replay_vector(
                by_id[trade_id], usable[trade_id], winner["values"],
                actual_exit_rule=str(outcome_by_id[trade_id].get("exit_rule") or ""),
            )) for trade_id in winner["comparison_support_ids"]
                if valid_dates[trade_id] in holdout_days]
            day_metrics = [
                _metric([pair for pair in holdout_pairs
                         if valid_dates[str(pair[0]["id"])] == day])["paired_ev_pct"]
                for day in holdout_days
            ]
            day_min = min(day_metrics) if day_metrics and all(
                value is not None for value in day_metrics
            ) else None
            slippage_day_metrics = {
                str(bps): [
                    _metric([pair for pair in holdout_pairs
                             if valid_dates[str(pair[0]["id"])] == day])[
                        "execution_slippage_sensitivity"][str(bps)]["paired_ev_pct"]
                    for day in holdout_days
                ]
                for bps in SLIPPAGE_SENSITIVITY_BPS
            }
            worst_slippage_day_ev = [
                value for values in slippage_day_metrics.values() for value in values
            ]
            worst_slippage_day_min = (
                min(worst_slippage_day_ev)
                if worst_slippage_day_ev and all(
                    value is not None for value in worst_slippage_day_ev
                ) else None
            )
            excluded_notional = sum(
                float(by_id[trade_id].get("buy_fill_amount") or 0)
                for trade_id in set(all_ids) - joint_common
            )
            excluded_holdout_notional = sum(
                float(by_id[trade_id].get("buy_fill_amount") or 0)
                for trade_id in set(all_ids) - joint_common
                if valid_dates[trade_id] in holdout_days
            )
            conservative_holdout_delta = (
                winner["holdout"]["delta_net_krw"] - excluded_holdout_notional
            )
            slippage_delta_sensitivity = {
                str(bps): round(
                    winner["holdout"]["execution_slippage_sensitivity"][str(bps)][
                        "delta_net_krw"
                    ] - excluded_holdout_notional,
                    2,
                )
                for bps in SLIPPAGE_SENSITIVITY_BPS
            }
            conservative_slippage_delta = min(slippage_delta_sensitivity.values())
            result["joint_selection_evidence"] = {
                "winner_sha256": winner_sha,
                "holdout_min_day_ev_pct": day_min,
                "holdout_min_day_ev_by_slippage_bps": slippage_day_metrics,
                "holdout_worst_slippage_min_day_ev_pct": worst_slippage_day_min,
                "unpaired_worst_case_notional_krw": excluded_notional,
                "unpaired_holdout_worst_case_notional_krw": excluded_holdout_notional,
                "holdout_conservative_delta_krw": conservative_holdout_delta,
                "holdout_conservative_delta_by_slippage_bps": slippage_delta_sensitivity,
                "holdout_conservative_worst_slippage_delta_krw": conservative_slippage_delta,
                "tail_review_required": bool(
                    winner["train"]["large_loss_worsened_ids"]
                    or winner["holdout"]["large_loss_worsened_ids"]
                ),
                "multiple_comparison_candidate_count": len(joint),
            }
            if (winner["train"]["n"] >= 30 and winner["holdout"]["n"] >= 10
                    and len(holdout_days) >= 2 and day_min is not None and day_min > 0
                    and conservative_holdout_delta > 0
                    and worst_slippage_day_min is not None
                    and worst_slippage_day_min > 0
                    and conservative_slippage_delta > 0
                    and not result["joint_selection_evidence"]["tail_review_required"]
                    and winner["values"] != {
                        market: usable[latest_id]["incumbent"][market]
                        for market in START_MARKETS
                    }):
                result["research_candidate"] = {
                    "values": winner["values"],
                    "classifier_parameters": usable[latest_id]["classifier_parameters"],
                    "market_values_sha256": winner_sha,
                    "evidence_grade_counts": winner["evidence_grade_counts"],
                    "decision_authority": "research_candidate_requires_policy_selection",
                }
                result["status"] = "research_candidate_holdout_positive_review_required"
    classifier_candidate = result["classifier_policy_research"].get("research_candidate")
    if result["classifier_policy_research"].get("status") == "hold_mixed_policy_generation":
        result["research_candidate"] = None
        result["status"] = "hold_mixed_policy_generation"
        return result
    if classifier_candidate and result.get("research_candidate"):
        result["numeric_research_candidate"] = result["research_candidate"]
        result["research_candidate"] = None
        result["status"] = "hold_competing_numeric_and_classifier_candidates"
    elif classifier_candidate:
        result["research_candidate"] = classifier_candidate
        result["joint_selection_evidence"] = result[
            "classifier_policy_research"]["joint_selection_evidence"]
        result["status"] = "research_candidate_holdout_positive_review_required"
    result.setdefault("status", "research_only_no_live_candidate")
    return result
