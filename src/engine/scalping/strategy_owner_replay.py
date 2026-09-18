"""First-use research for existing Entry/holding components.

Reuses the isolated full holding-policy adapter and its bounded quote capture.
Quote-counterfactual outcomes are never actual fills or standalone live approval.
This module neither submits orders nor changes the original operator files.
"""

from __future__ import annotations

import copy
import fcntl
import json
import math
import os
import re
import tempfile
import threading
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from functools import lru_cache
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.engine.scalping import strategy_owner_components as owner

SCHEMA = "strategy_owner_first_use_replay_v1"
SEED_STAGE = "strategy_owner_replay_seed_observed"
MAX_SEEDS_PER_DAY = 8
MAX_REPORT_SECONDS = 300
MAX_PROVIDER_CALLS = 8
REPLAY_FLOOR = 10
SOURCE_START_DATE = "2026-09-08"
KST = ZoneInfo("Asia/Seoul")
AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
_SEED_LOCK = threading.Lock()
_SEED_DAY = ""
_SEED_COUNTS = {}


def _finite(value, *, positive=False):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and (not positive or value > 0)
    )


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _timestamp(value, day):
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None or parsed.astimezone(KST).date().isoformat() != day:
        raise ValueError("source_timestamp_day_or_timezone_invalid")
    return parsed


def valid_seed(seed, day):
    """Validate intrinsic provenance before any isolated/provider evaluation."""
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version, thaw

    try:
        if (
            not isinstance(seed, dict)
            or seed.get("schema") != SCHEMA
            or not SOURCE_START_DATE <= day
            or any(seed.get(k) is not v for k, v in AUTHORITY.items())
            or not owner.valid_scope(seed.get("venue"), seed.get("session"))
            or not _sha(seed.get("context_sha256"))
            or not re.fullmatch(r"\d{6}", str(seed.get("stock_code", "")))
        ):
            return False
        _timestamp(seed["emitted_at"], day)
        component = seed["strategy_owner_replay"]
        family = seed["family"]
        if (
            component.get("family") != family
            or not owner.bounded_change(
                family, component.get("baseline"), component.get("profile")
            )
            or component["profile"] != proposal(family, component["baseline"])
            or set(seed["profiles"]) != set(owner.OWNERS)
            or any(owner.profile(f, p) != p for f, p in seed["profiles"].items())
            or component["baseline"] != seed["profiles"][family]
            or not all(
                v for k, v in component["baseline"].items() if k.endswith("_ENABLED")
            )
            or not _finite(seed.get("pre_add_buy_price"), positive=True)
            or not _finite(seed.get("pre_add_buy_qty"), positive=True)
            or seed["pre_add_buy_qty"] != int(seed["pre_add_buy_qty"])
            or not _finite(seed.get("cost_rate"))
            or not 0 <= seed["cost_rate"] < 1
        ):
            return False
        identity = seed["source_event_id"]
        if (
            not isinstance(identity, str)
            or not identity.startswith("owner-component-")
            or not _sha(identity.removeprefix("owner-component-"))
            or any(
                seed.get(k) != identity
                for k in ("position_episode_id", "scale_in_decision_id")
            )
            or snapshot_version(seed["policy_snapshot"]) != seed["exit_policy_version"]
        ):
            return False
        rules = SimpleNamespace(**thaw(seed["policy_snapshot"]["rules"]))
        if (
            owner.runtime_profiles(rules) != seed["profiles"]
            or owner.context_fingerprint(rules) != seed["context_sha256"]
        ):
            return False
        if family == owner.WEAK:
            if (
                seed.get("entry_authority", {}).get("blocked") is not False
                or not isinstance(seed.get("entry_submit_attempt_id"), str)
                or not seed["entry_submit_attempt_id"]
                or not isinstance(seed.get("entry_guard_inputs"), dict)
                or seed.get("entry_fill_model")
                != "conditional_full_executable_ask_not_broker_receipt"
            ):
                return False
        return True
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False


def proposal(family, baseline):
    """One adjacent hypothesis, not an improvement or approval claim."""
    key = (
        "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES"
        if family == owner.WEAK
        else "SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC"
    )
    values = dict(baseline)
    values[key] -= owner.STEPS[key]
    return values if owner.bounded_change(family, baseline, values) else None


def observe_seed(handlers, stock, code, *, now_ts, ws_data, entry=None, ai_engine=None):
    """Fail-open instrumentation at an existing decision, with no new data calls."""
    from src.engine.scalping import avg_down_replay_capture as capture
    from src.engine.lifecycle.avg_down_policy_replay import _json_value
    from src.engine.lifecycle.avg_down_replay import finite_number

    global _SEED_DAY
    family = owner.WEAK if entry is not None else owner.PROFIT
    try:
        if (
            not isinstance(stock, dict)
            or str(stock.get("strategy", "")).upper() not in {"SCALPING", "SCALP"}
            or handlers._is_any_simulated_position(stock, stock.get("strategy"))
        ):
            return
        venue, session = owner.stock_scope(stock)
        if not owner.valid_scope(venue, session):
            return
        state = handlers._strategy_owner_component_state(stock)
        baseline = state["profiles"].get(family)
        if baseline is None or not all(
            v for k, v in baseline.items() if k.endswith("_ENABLED")
        ):
            return
        candidate = proposal(family, baseline)
        if candidate is None or state.get("context_sha256") is None:
            return
        # A selected component is evaluated by real attribution, not by another
        # nested first-use trial. The first event, including its gaps, owns a seed.
        if state["applied_families"]:
            return
        day = datetime.fromtimestamp(now_ts, KST).date().isoformat()
        if day < SOURCE_START_DATE:
            return
        entry_attempt_id = (
            handlers.submit_attempt_fields(stock, code).get("entry_submit_attempt_id")
            if entry
            else None
        )
        if entry:
            # Retries of one promotion/record are not independent economic
            # opportunities. Preserve the first native attempt as provenance.
            parent = stock.get("scanner_promotion_id") or stock.get("id")
            if not entry_attempt_id or not parent:
                return
            identity = [day, code, parent]
        else:
            identity = stock.get("main_lifecycle_id") or [
                stock.get("id"),
                stock.get("date"),
                stock.get("buy_price"),
            ]
        if not identity:
            return
        episode = "owner-component-" + owner.digest([family, identity, venue, session])
        marks = stock.setdefault("_strategy_owner_replay_seeds", [])
        if episode in marks:
            return
        marks.append(episode)
        del marks[:-8]
        target = copy.deepcopy(stock)
        if any(
            target.get(k)
            for k in (
                "pending_add_order",
                "pending_entry_orders",
                "sell_submit_pending",
                "exit_token",
            )
        ):
            return
        if entry:
            if entry.get("authority", {}).get("blocked") is not False:
                return
            orders = entry.get("planned_orders") or []
            if len(orders) != 1:
                return  # No invented split/full entry fill.
            order = orders[0]
            qty, limit_price = order.get("qty"), order.get("price")
            fields, _, ask, _ = handlers._build_quote_consistency_fields(
                ws_data, side="buy", now_ts=now_ts
            )
            available = finite_number(ws_data.get("best_ask_qty"))
            depth_price = finite_number(ws_data.get("best_ask"))
            if available is None or depth_price != ask:
                levels = (ws_data.get("orderbook") or {}).get("asks") or []
                available = finite_number(levels[0].get("volume")) if levels else None
                depth_price = finite_number(levels[0].get("price")) if levels else None
            from src.trading.market.quote_consistency import ws_quote_receive_age_ms

            quote_age_ms = ws_quote_receive_age_ms(ws_data, now_ts=now_ts)
            age = quote_age_ms / 1000.0 if quote_age_ms is not None else None
            if (
                type(qty) is not int
                or qty <= 0
                or not _finite(ask, positive=True)
                or not _finite(limit_price, positive=True)
                or limit_price < ask
                or not _finite(available, positive=True)
                or available < qty
                or depth_price != ask
                or not _finite(age)
                or not 0 <= age <= 1
                or entry.get("order_type_code") != "00"
                or fields.get("quote_consistency_state") not in {"ok", "single_source"}
                or fields.get("quote_consistency_reason")
                not in {"ws_only_fresh", "ws_rest_gap_ok"}
            ):
                return
            # A full executable-ask counterfactual, explicitly not a broker fill.
            target.update(
                status="HOLDING",
                buy_qty=qty,
                buy_price=ask,
                date=datetime.fromtimestamp(now_ts, KST).isoformat(),
                holding_started_at=datetime.fromtimestamp(now_ts, KST).replace(
                    tzinfo=None
                ),
                order_time=now_ts,
            )
        if (
            target.get("status") != "HOLDING"
            or not target.get("buy_qty")
            or not target.get("buy_price")
        ):
            return
        current_ai = entry.get("ai_engine") if entry else ai_engine
        if current_ai is None:
            stock["_strategy_owner_replay_capture_state"] = "current_ai_state_missing"
            return
        capture.record_ai_state(code, current_ai)
        prepared = capture.prepare(handlers, target, code, episode, now_ts=now_ts)
        if prepared.get("replay_capture_state") != "armed_source_only":
            stock["_strategy_owner_replay_capture_state"] = prepared.get(
                "replay_capture_state"
            )
            return
        with _SEED_LOCK:
            if _SEED_DAY != day:
                _SEED_COUNTS.clear()
                _SEED_DAY = day
            if _SEED_COUNTS.get(family, 0) >= MAX_SEEDS_PER_DAY // 2:
                stock["_strategy_owner_replay_capture_state"] = (
                    "bounded_daily_seed_capacity"
                )
                return
            _SEED_COUNTS[family] = _SEED_COUNTS.get(family, 0) + 1
        if entry:
            prepared["replay_peak_price"] = target["buy_price"]
        seed = {
            **prepared,
            "schema": SCHEMA,
            "family": family,
            "strategy_owner_replay": {
                "family": family,
                "baseline": baseline,
                "profile": candidate,
            },
            "profiles": state["profiles"],
            "score_profile": stock.get("_strategy_owner_score_profile"),
            "context_sha256": state["context_sha256"],
            "source_event_id": episode,
            "position_episode_id": episode,
            "scale_in_decision_id": episode,
            "stock_code": code,
            "venue": venue,
            "session": session,
            "emitted_at": datetime.fromtimestamp(now_ts, KST).isoformat(),
            "pre_add_buy_price": target["buy_price"],
            "pre_add_buy_qty": target["buy_qty"],
            "cost_rate": handlers.get_trade_cost_rate(),
            "entry_guard_inputs": (
                _json_value(entry.get("guard_inputs")) if entry else None
            ),
            "entry_authority": entry.get("authority") if entry else None,
            "entry_submit_attempt_id": entry_attempt_id,
            "entry_fill_model": (
                "conditional_full_executable_ask_not_broker_receipt" if entry else None
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        encoded = json.dumps(
            seed, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        )
        if len(encoded.encode()) > capture.MAX_SNAPSHOT_BYTES:
            return
        emitted = handlers.emit_pipeline_event(
            "ENTRY_PIPELINE" if entry else "HOLDING_PIPELINE",
            stock.get("name", code),
            code,
            SEED_STAGE,
            fields={
                "owner_component_seed": encoded,
                "source_event_id": episode,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "source_only_owner_component_replay",
            },
        )
        if (
            not isinstance(emitted, dict)
            or emitted.get("structured_append_succeeded") is not True
        ):
            stock["_strategy_owner_replay_capture_state"] = "structured_seed_append_gap"
            return
        capture.register(
            episode=episode,
            source_id=episode,
            decision_id=episode,
            code=code,
            venue=venue,
            now_ts=now_ts,
            fields=prepared,
        )
        stock["_strategy_owner_replay_capture_state"] = "armed_source_only"
    except Exception as exc:
        # Missing seed/frame contracts block only offline first-use research.
        if isinstance(stock, dict):
            stock["_strategy_owner_replay_capture_state"] = (
                "source_gap:" + type(exc).__name__
            )
        return


def report_path(report_dir, day):
    return (
        Path(report_dir)
        / "strategy_owner_first_use_replay"
        / f"strategy_owner_first_use_replay_{day}.json"
    )


def _decode(value):
    return json.loads(value) if isinstance(value, str) else value


def _wire_authority(fields):
    # The lossless pipeline emitter stringifies scalar fields. Never use
    # truthiness ("False" is truthy), or a missing-field default here.
    return all(
        str(fields.get(k)).lower() == str(v).lower() for k, v in AUTHORITY.items()
    )


def _wire_cutoff(fields, observed, day):
    emitted = datetime.fromisoformat(fields["emitted_at"])
    if emitted.utcoffset() is None:  # Pipeline logger's documented local KST clock.
        emitted = emitted.replace(tzinfo=KST)
    return (
        fields.get("_source_event_date", day) == day
        and emitted.astimezone(KST).date().isoformat() == day
        and 0 <= (emitted - observed).total_seconds() <= 5
    )


def collect(events, day):
    seeds, frames, conflicts = {}, {}, set()
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("fields", {}), dict):
            continue
        fields = {**event, **(event.get("fields") or {})}
        if fields.get("stage") == SEED_STAGE:
            try:
                seed = _decode(fields.get("owner_component_seed"))
                identity = seed["source_event_id"]
                if (
                    not valid_seed(seed, day)
                    or fields.get("source_event_id") != identity
                    or not _wire_authority(fields)
                    or fields.get("decision_authority")
                    != "source_only_owner_component_replay"
                    or fields.get("stock_code") != seed["stock_code"]
                    or not _wire_cutoff(
                        fields, _timestamp(seed["emitted_at"], day), day
                    )
                ):
                    conflicts.add(identity)
                    continue
                if identity in seeds and seeds[identity] != seed:
                    conflicts.add(identity)
                if len(seeds) < MAX_SEEDS_PER_DAY or identity in seeds:
                    seeds[identity] = seed
            except (ValueError, TypeError, KeyError):
                continue
        elif fields.get("stage") == "avg_down_exit_replay_frame_observed":
            identity = fields.get("source_observation_id")
            if identity not in seeds:
                continue
            try:
                if (
                    not _wire_authority(fields)
                    or fields.get("decision_authority")
                    != "source_only_paired_exit_replay"
                    or not _wire_cutoff(
                        fields, _timestamp(fields["replay_observed_at"], day), day
                    )
                ):
                    raise ValueError("frame_authority_or_cutoff_invalid")
                frame = {
                    k: fields.get(k)
                    for k in (
                        "source_event_id",
                        "source_observation_id",
                        "scale_in_decision_id",
                        "position_episode_id",
                        "stock_code",
                        "venue",
                        "exit_policy_version",
                        "replay_frame_schema",
                        "sequence",
                        "capture_gap",
                        "capture_end",
                    )
                }
                for name in ("market", "external_results", "full_policy_decisions"):
                    frame[name] = _decode(fields.get(name, {}))
                frame["emitted_at"] = fields["replay_observed_at"]
                _timestamp(frame["emitted_at"], day)
                rows = frames.setdefault(identity, [])
                if len(rows) <= 7200:
                    rows.append(frame)
            except (ValueError, TypeError, KeyError):
                conflicts.add(identity)
    return [
        (seed, frames.get(identity, []))
        for identity, seed in sorted(
            seeds.items(), key=lambda p: (p[1]["emitted_at"], p[0])
        )
        if identity not in conflicts
    ]


def valid_row(row, day):
    try:
        family = row["family"]
        if (
            row["date"] != day
            or not SOURCE_START_DATE <= day
            or row.get("evidence_class")
            != "exact_policy_quote_counterfactual_not_real_fill"
            or not owner.valid_scope(row["venue"], row["session"])
            or not owner.bounded_change(family, row["baseline"], row["profile"])
            or row["profile"] != proposal(family, row["baseline"])
            or set(row["profiles"]) != set(owner.OWNERS)
            or any(owner.profile(f, p) != p for f, p in row["profiles"].items())
            or row["profiles"][family] != row["baseline"]
            or any(
                not _sha(row.get(k))
                for k in ("context_sha256", "input_sha256", "replay_sha256")
            )
            or not row["id"].startswith("owner-component-")
            or not _sha(row["id"].removeprefix("owner-component-"))
            or len(row["arms"]) != 2
        ):
            return False
        for arm in row["arms"]:
            if (
                not _finite(arm["net"])
                or not _finite(arm["notional"], positive=True)
                or not _finite(arm["capital"])
                or arm["capital"] < 0
                or type(arm["known_no_entry"]) is not bool
            ):
                return False
            if arm["known_no_entry"]:
                if family != owner.WEAK or arm["net"] != 0 or arm["capital"] != 0:
                    return False
            elif arm["capital"] <= 0:
                return False
        return True
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False


def _signed(value):
    frozen = copy.deepcopy({k: v for k, v in value.items() if k != "sha256"})
    return {**frozen, "sha256": owner.digest(frozen)}


def build(day, inputs, *, executor=None, cached=None, checkpoint=None):
    from src.engine.lifecycle.avg_down_policy_replay import (
        replay_with_current_policy_ai,
        implementation_identity,
    )

    executor = executor or replay_with_current_policy_ai
    deadline = time.monotonic() + MAX_REPORT_SECONDS
    remaining_calls = MAX_PROVIDER_CALLS
    result = {
        "schema": SCHEMA,
        "state": "checkpoint_source_only",
        "target_date": day,
        "rows": [],
        "blocked": {},
        "attempts": {},
        "implementation": implementation_identity(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "source_only_owner_component_replay",
    }
    same_implementation = (cached or {}).get("implementation") == result[
        "implementation"
    ]
    previous = {
        r["input_sha256"]: r
        for r in (cached or {}).get("rows", [])
        if same_implementation and valid_row(r, day)
    }
    # Retain completed attempt tombstones even if later source collection loses
    # a seed. A terminal provider rejection is not a new retry opportunity.
    result["attempts"] = copy.deepcopy((cached or {}).get("attempts", {}))
    remaining_calls = max(
        0,
        MAX_PROVIDER_CALLS
        - sum(r["provider_calls"] for r in result["attempts"].values()),
    )
    seen = set()
    for seed, frames in inputs[:MAX_SEEDS_PER_DAY]:
        if not valid_seed(seed, day):
            result["blocked"][
                "invalid_seed:" + str(len(seen))
            ] = "seed_contract_invalid"
            continue
        identity = seed["source_event_id"]
        if identity in seen:
            result["rows"] = [r for r in result["rows"] if r["id"] != identity]
            result["blocked"][identity] = "duplicate_seed_identity"
            continue
        seen.add(identity)
        source_sha = owner.digest([seed, frames])
        if source_sha in previous:
            result["rows"].append(previous[source_sha])
            continue
        if identity in result["attempts"]:
            result["blocked"][identity] = {
                "state": "terminal_first_attempt_not_retried",
                "first_result": result["attempts"][identity].get("reason"),
            }
            continue
        if time.monotonic() >= deadline:
            result["blocked"][identity] = "bounded_report_deadline"
            continue
        # Reserve before entering a paid worker. A crash/kill must not turn an
        # unknown request outcome into another first attempt or a fresh budget.
        result["attempts"][identity] = {
            "input_sha256": source_sha,
            "provider_calls": remaining_calls,
            "provider_calls_known": False,
            "terminal": True,
            "reason": "reserved_inflight_unknown_request_outcome",
        }
        if checkpoint:
            checkpoint(_signed(result))
        calls_known = False
        try:
            budget_before = remaining_calls
            replay = executor(
                seed, frames, max_provider_calls=remaining_calls, deadline=deadline
            )
            calls = replay.get("policy_ai_provider_call_count", 0)
            if type(calls) is not int or not 0 <= calls <= remaining_calls:
                raise ValueError("provider_budget_receipt_invalid")
            remaining_calls -= calls
            calls_known = True
        except Exception as exc:
            replay = {"adapter_error": "bounded_replay_failure:" + type(exc).__name__}
            remaining_calls = 0  # An unknown request outcome cannot restore budget.
        result["attempts"][identity] = {
            "input_sha256": source_sha,
            "provider_calls": budget_before - remaining_calls,
            "provider_calls_known": calls_known,
            "terminal": True,
        }
        outcomes = replay.get("outcomes") or {}
        if (
            replay.get("state") != "paired_exit_complete_source_only"
            or replay.get("blockers")
            or replay.get("actual_order_submitted") is not False
            or replay.get("broker_order_forbidden") is not True
            or not _sha(replay.get("evidence_digest"))
            or replay.get("evidence_digest")
            != owner.digest({k: v for k, v in replay.items() if k != "evidence_digest"})
            or set(outcomes) != {"baseline", "profile"}
            or (
                seed["family"] == owner.WEAK
                and outcomes.get("baseline", {}).get("known_no_entry") is not True
            )
        ):
            result["blocked"][identity] = (
                replay.get("adapter_error")
                or replay.get("blockers")
                or "exact_policy_replay_incomplete"
            )
            result["attempts"][identity]["reason"] = copy.deepcopy(
                result["blocked"][identity]
            )
            if checkpoint:
                checkpoint(_signed(result))
            continue
        values = []
        try:
            notional = seed["pre_add_buy_price"] * seed["pre_add_buy_qty"]
            start = _timestamp(seed["emitted_at"], day)
            for key in ("baseline", "profile"):
                row = outcomes[key]
                elapsed = (_timestamp(row["exit_time"], day) - start).total_seconds()
                net = row["net_pnl_krw"]
                if (
                    row.get("full_policy_evaluation") is not True
                    or row.get("status") != "COMPLETED"
                    or row.get("filled_add_qty") != 0
                    or type(net) not in (int, float)
                    or not math.isfinite(net)
                    or not 0 <= elapsed <= 7200
                    or (elapsed == 0 and row.get("known_no_entry") is not True)
                    or (
                        row.get("known_no_entry") is not True
                        and row.get("exit_qty") != seed["pre_add_buy_qty"]
                    )
                    or (
                        row.get("known_no_entry") is True
                        and (net != 0 or elapsed != 0 or row.get("exit_qty") != 0)
                    )
                ):
                    raise ValueError("replay_terminal_cost_or_scope_invalid")
                values.append(
                    {
                        "net": net,
                        "capital": notional * elapsed / 3600,
                        "notional": notional,
                        "known_no_entry": row.get("known_no_entry") is True,
                    }
                )
            compact = {
                "id": identity,
                "date": day,
                "family": seed["family"],
                "baseline": seed["strategy_owner_replay"]["baseline"],
                "profile": seed["strategy_owner_replay"]["profile"],
                "profiles": seed["profiles"],
                "score_profile": seed.get("score_profile"),
                "context_sha256": seed["context_sha256"],
                "venue": seed["venue"],
                "session": seed["session"],
                "arms": values,
                "input_sha256": source_sha,
                "replay_sha256": replay.get("evidence_digest"),
                "evidence_class": "exact_policy_quote_counterfactual_not_real_fill",
            }
            if not valid_row(compact, day):
                raise ValueError("compact_replay_contract_invalid")
            result["rows"].append(compact)
        except (TypeError, ValueError, KeyError, OverflowError):
            result["blocked"][identity] = "replay_economic_contract_invalid"
        result["attempts"][identity]["reason"] = result["blocked"].get(
            identity, "completed_source_only"
        )
        if checkpoint:
            checkpoint(_signed(result))
    result["state"] = "completed_source_only"
    return _signed(result)


def load(report_dir, day, *, require_current=True, require_terminal=True):
    from src.engine.lifecycle.avg_down_policy_replay import implementation_identity

    try:
        value = json.loads(report_path(report_dir, day).read_text())
        if (
            value.get("schema") != SCHEMA
            or value.get("state")
            not in {"checkpoint_source_only", "completed_source_only"}
            or (require_terminal and value.get("state") != "completed_source_only")
            or value.get("target_date") != day
            or (
                require_current
                and value.get("implementation") != implementation_identity()
            )
            or value.get("sha256")
            != owner.digest({k: v for k, v in value.items() if k != "sha256"})
            or any(value.get(k) is not v for k, v in AUTHORITY.items())
            or not isinstance(value.get("attempts"), dict)
            or any(
                not isinstance(r, dict)
                or not _sha(r.get("input_sha256"))
                or type(r.get("provider_calls")) is not int
                or not 0 <= r["provider_calls"] <= MAX_PROVIDER_CALLS
                or r.get("terminal") is not True
                for r in value.get("attempts", {}).values()
            )
            or any(not valid_row(r, day) for r in value.get("rows", []))
            or not isinstance(value.get("rows"), list)
            or len({r["id"] for r in value["rows"]}) != len(value["rows"])
        ):
            return None
        return value
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def materialize(day, report_dir):
    """Called only by the existing postclose CLI, never by a live/PREOPEN loader."""
    from src.engine.monitoring.scalping_avg_down_recovery_calibration import (
        _events_paths_for_date,
        _iter_events,
    )

    if day < SOURCE_START_DATE:
        return None
    path = report_path(report_dir, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("owner_component_replay_already_running") from None
        previous = load(report_dir, day, require_current=False, require_terminal=False)
        if path.exists() and previous is None:
            # A damaged checkpoint cannot reset the paid-request ledger.
            raise ValueError("owner_component_replay_checkpoint_invalid")
        result = build(
            day,
            collect(_iter_events(_events_paths_for_date(day)), day),
            cached=previous,
            checkpoint=lambda value: _publish(value, report_dir, day),
        )
        _publish(result, report_dir, day)
        return result


def _publish(result, report_dir, day):
    path = report_path(report_dir, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(result, handle, ensure_ascii=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def attach_replays(book, report_dir, day):
    value = load(report_dir, day)
    if value is not None:
        book["replays"] = {row["id"]: row for row in value["rows"]}
        book["replay_sources"] = {day: value["sha256"]}
    return book


def first_use_policies(
    book, family, baseline, target_date, tried=(), *, diagnostics=None
):
    """Paired exact replay AND real full-fill quality; at most one bounded trial.

    No executed challenger is needed for first use. Real economic promotion
    still belongs to owner.evaluate after this finite canary generates outcomes.
    """
    diagnostics = {} if diagnostics is None else diagnostics
    diagnostics.update(
        replay_floor=REPLAY_FLOOR,
        real_full_fill_floor=20,
        chronological_halves_required=True,
        cohort_checks=[],
        state="waiting_exact_replay",
    )
    groups = {}
    for row in book.get("replays", {}).values():
        if (
            not isinstance(row, dict)
            or not valid_row(row, row.get("date", ""))
            or row.get("family") != family
            or row.get("baseline") != baseline
            or row.get("date") not in book.get("replay_sources", {})
            or not "2026-06-05" <= row["date"] < target_date
            or not owner.bounded_change(family, baseline, row.get("profile"))
        ):
            continue
        key = owner.digest(
            [
                family,
                baseline,
                row["profile"],
                row["context_sha256"],
                row["venue"],
                row["session"],
                row.get("score_profile"),
                row["profiles"],
            ]
        )
        if key not in tried:
            groups.setdefault(key, []).append(row)
        else:
            diagnostics["state"] = "prior_trial_terminal_not_rearmed"
    candidates = []
    for trial_id, rows in sorted(groups.items()):
        example = rows[0]
        days = sorted({r["date"] for r in rows})
        check = {
            "cohort_sha256": trial_id,
            "replay_count": len(rows),
            "replay_day_count": len(days),
            "state": "waiting_replay_sample",
        }
        diagnostics["cohort_checks"].append(check)
        if len(rows) < REPLAY_FLOOR or len(days) < 2:
            continue
        actual = [
            r
            for r in book.get("rows", {}).values()
            if r.get("date") in book.get("sources", {})
            and "2026-06-05" <= r["date"] < target_date
            and r["profiles"] == example["profiles"]
            and r.get("score_profile") == example.get("score_profile")
            and r["context_sha256"] == example["context_sha256"]
            and r["venue"] == example["venue"]
            and r["session"] == example["session"]
        ]
        real_days = sorted({r["date"] for r in actual})
        check.update(
            real_full_fill_count=len(actual),
            real_day_count=len(real_days),
            state="waiting_real_full_fill_quality",
        )
        if len(actual) < 20 or len(real_days) < 2:
            continue
        real_split = real_days[len(real_days) // 2]
        real_halves = [
            [r for r in actual if (r["date"] >= real_split) == late]
            for late in (False, True)
        ]
        if any(
            len(half) < 10 or sum(r["net"] for r in half) <= 0 for half in real_halves
        ):
            check["state"] = "real_halves_sample_or_net_quality_not_met"
            continue
        split = days[len(days) // 2]
        metrics = []
        for late in (False, True):
            half = [r for r in rows if (r["date"] >= split) == late]
            if len(half) < REPLAY_FLOOR // 2:
                break
            arms = [
                {
                    "net": sum(r["arms"][i]["net"] for r in half),
                    "capital": sum(r["arms"][i]["capital"] for r in half),
                    "days": len({r["date"] for r in half}),
                    "sample_count": len(half),
                }
                for i in (0, 1)
            ]
            before, after = arms
            if (
                after["capital"] <= 0
                or after["net"] <= max(0, before["net"])
                or (
                    before["capital"] > 0
                    and after["net"] / after["capital"]
                    <= before["net"] / before["capital"]
                )
            ):
                break
            metrics.append(arms)
        if len(metrics) != 2:
            check["state"] = "replay_halves_sample_or_net_efficiency_not_met"
            continue
        check["state"] = "bounded_canary_eligible"
        candidates.append(
            {
                "venue": example["venue"],
                "session": example["session"],
                "context_sha256": example["context_sha256"],
                "score_profile": example.get("score_profile"),
                "cohort_sha256": trial_id,
                "other_profiles": {
                    k: v for k, v in example["profiles"].items() if k != family
                },
                "baseline": baseline,
                "profile": example["profile"],
                "metrics": metrics,
                "source_dates": sorted(set(days) | set(real_days)),
                "replay_sources": {d: book["replay_sources"][d] for d in days},
                "real_sources": {d: book["sources"][d] for d in real_days},
                "sample_floor": REPLAY_FLOOR,
                "real_full_fill_sample_count": len(actual),
                "evidence_sha256": owner.digest([rows, actual]),
                "mode": "first_use_bounded_canary",
                "trial_id": trial_id,
                "canary_start_date": target_date,
                "canary_until_date": (
                    date.fromisoformat(target_date) + timedelta(days=6)
                ).isoformat(),
                "canary_max_calendar_days": 7,
                "real_promotion_required": True,
                "runtime_safety_and_quantity_unchanged": True,
            }
        )
    # One first-use hypothesis per owner, not a multi-axis or multi-cohort trial.
    candidates.sort(
        key=lambda p: (
            -(p["metrics"][0][1]["net"] - p["metrics"][0][0]["net"])
            / p["metrics"][0][0]["days"],
            p["trial_id"],
        )
    )
    if candidates:
        diagnostics["state"] = "bounded_canary_eligible"
    elif groups:
        diagnostics["state"] = "waiting_or_no_edge_see_cohort_checks"
    return candidates[:1]

# Existing entry-owner research: fixed before looking at the subsequent path.
ENTRY_REPLAY_SCHEMA = 'entry_opportunity_executable_replay_v1'
ENTRY_PRICE_SELECTION = 'entry_price_chronological_union_v2'
ENTRY_REPLAY_EXIT = dict(horizon_sec=180, take_profit_pct=0.5, stop_loss_pct=-0.5)
ENTRY_REPLAY_COST = dict(round_trip_pct=0.23, stress_round_trip_pct=0.28,
                         basis='missed_entry_research_cost_not_broker_actual')
ENTRY_REPLAY_ALLOCATION = dict(max_concurrent_research_positions=1,
    reservation_sec=180, basis='conservative_common_reservation_not_live_capacity')
ENTRY_REPLAY_PROFILES = {
    'normal': 'normal_defensive_bps',
    'strong_1tick_pressure': 'conditional_strong_defensive_bps',
    'favorable_micro': 'normal_favorable_defensive_bps',
    'favorable_wide_micro': 'normal_favorable_defensive_bps',
    'weak_liquidity_wide_spread': 'normal_weak_defensive_bps',
}


def freeze_entry_opportunity(plan, *, stock_code, observed_at, profile=None,
                             profile_bps=None, anchor_price=None, sizing_context=None, candidate_leg_plan=None, operating_context=None):
    """Freeze an order-free, non-increasing research menu alongside an owner plan.

    The original orders, quantities, prices and signed plan are never changed.
    Probe continuations with unknown future prices are not replayable.
    """
    from src.engine.monitoring.research_closed_loop import digest
    from src.trading.order.tick_utils import move_price_down_by_bps, clamp_price_to_tick
    try:
        if (not _finite(observed_at, positive=True) or plan.get('valid') is not True or plan.get('blockers')
            or type(plan.get('total_qty')) is not int or plan['total_qty'] <= 0
            or plan.get('deferred_probe_residual_qty') != 0
            or not re.fullmatch(r'\d{6}', stock_code)
            or plan.get('effective_venue') not in ('KRX', 'NXT')
            or not plan.get('market_session_bucket') or not _sha(plan.get('policy_bundle_hash'))):
            return None
        clock = datetime.fromtimestamp(observed_at, KST)
        legs = plan['legs']
        def frozen_legs(owner_plan):
            issued = {x.get('price_leg_id'): x for x in owner_plan.get('price_candidates', [])}
            result = []
            for x in owner_plan['legs']:
                order_type = str(issued.get(x.get('price_leg_id'), {}).get('order_type_code') or '00')
                price = x['numeric_price']
                if (type(x['qty']) is not int or x['qty'] <= 0 or type(price) is not int
                    or price < 0 or (price == 0 and order_type not in ('3', '03'))
                    or x.get('execution_phase') != 'immediate'):
                    raise ValueError('registered_order_price_or_leg_missing')
                result.append(dict(qty=x['qty'], price=price, order_type_code=order_type))
            if not 0 < len(result) <= 3 or sum(x['qty'] for x in result) != plan['total_qty']:
                raise ValueError('registered_leg_quantity_conservation_failed')
            return result
        original_legs = frozen_legs(plan)
        # Reuse the registered flat-10 quantity alternative with the ORIGINAL
        # context/caps. Missing context is an unchanged quantity control.
        candidate_qty, candidate_quantity_version = plan['total_qty'], plan['quantity_policy_version']
        if sizing_context is not None:
            from dataclasses import replace
            from src.engine.scalping.position_sizing_allocator import (
                resolve_scalping_allocation, FORMULA_VERSION, ROLLBACK_FORMULA_VERSION)
            alternative = resolve_scalping_allocation(replace(sizing_context,
                simulation=True, initial_tier=1, initial_formula_version=FORMULA_VERSION))
            if alternative.ratio != .10 or alternative.effective_qty <= 0:
                return None
            candidate_qty = min(plan['total_qty'], alternative.effective_qty)
            candidate_quantity_version = ROLLBACK_FORMULA_VERSION
        candidate_legs = original_legs
        candidate_leg_version, candidate_leg_sha = plan['split_policy_version'], digest(plan)
        if candidate_leg_plan is not None:
            alternative_legs = frozen_legs(candidate_leg_plan)
            if (candidate_leg_plan.get('valid') is not True or candidate_leg_plan.get('blockers')
                or candidate_leg_plan.get('deferred_probe_residual_qty') != 0
                or candidate_leg_plan.get('total_qty') != plan['total_qty']
                or any(candidate_leg_plan.get(k) != plan.get(k) for k in (
                    'scanner_promotion_id', 'action_receipt_id', 'effective_venue',
                    'market_session_bucket', 'policy_bundle_hash', 'quantity_policy_version'))
                or not candidate_leg_plan.get('split_policy_version')
                or not 0 < len(alternative_legs) <= 3
                or sum(x['qty'] for x in alternative_legs) != plan['total_qty']
                or any(type(x['qty']) is not int or x['qty'] <= 0
                    or (x['price'], x['order_type_code']) not in {(a['price'], a['order_type_code']) for a in original_legs} for x in alternative_legs)):
                return None
            candidate_legs = alternative_legs
            candidate_leg_version = candidate_leg_plan['split_policy_version']
            candidate_leg_sha = digest(candidate_leg_plan)
        if operating_context is not None and candidate_leg_plan is None:
            # Existing capped weight menu retains every price
            # issued by the original owner and keep quantity fixed in phase one.
            n = len(original_legs)
            if plan['total_qty'] >= n:
                from src.trading.order.split_execution_math import split_qty
                from src.engine.scalping.entry_split_order_plan import PASSIVE_CENTER_MAX_FIRST_WEIGHT
                counts = split_qty(plan['total_qty'], n, min(1 / n, PASSIVE_CENTER_MAX_FIRST_WEIGHT))
                candidate_legs = [{**x, 'qty': counts[i]} for i, x in enumerate(original_legs)]
                candidate_leg_version = 'entry_split_quantity_fixed_guarded_weights_v1'
                candidate_leg_sha = digest(candidate_legs)
                candidate_qty, candidate_quantity_version = plan['total_qty'], plan['quantity_policy_version']
        seed = dict(schema=ENTRY_REPLAY_SCHEMA, stock_code=stock_code,
            source_date=clock.date().isoformat(), observed_at=clock.isoformat(),
            scanner_promotion_id=plan['scanner_promotion_id'],
            evaluation_attempt_id=plan['action_receipt_id'],
            effective_venue=plan['effective_venue'], session_bucket=plan['market_session_bucket'],
            policy_bundle_sha256=plan['policy_bundle_hash'],
            plan_sha256=digest(plan), entry_price_receipt_sha256=plan['price_plan_sha256'],
            entry_price_policy_sha256=plan['price_policy_sha256'],
            incumbent_quantity_policy_version=plan['quantity_policy_version'],
            candidate_quantity_policy_version=candidate_quantity_version,
            incumbent_leg_policy_version=plan['split_policy_version'],
            candidate_leg_policy_version=candidate_leg_version,
            candidate_leg_plan_sha256=candidate_leg_sha, candidate_legs=candidate_legs,
            candidate_leg_control_only=candidate_leg_plan is None,
            total_qty=plan['total_qty'], candidate_qty=candidate_qty,
            legs=original_legs,
            exit_contract=ENTRY_REPLAY_EXIT.copy(), cost_contract=ENTRY_REPLAY_COST.copy(),
            research_entry_ttl_sec=10, modeled_submit_delay_ms=150,
            allocation_contract=ENTRY_REPLAY_ALLOCATION.copy(),
            price_candidates={}, **AUTHORITY)
        if operating_context is not None:
            seed['operating_contract'] = copy.deepcopy(operating_context)
        # Only the exact existing BPS formula can become an automatic price policy.
        # Other price branches remain quantity/leg research, not guessed BPS joins.
        if (all(x['price'] > 0 and x['order_type_code'] not in ('3', '03') for x in original_legs)
            and profile in ENTRY_REPLAY_PROFILES and type(profile_bps) is int and profile_bps > 0
            and type(anchor_price) is int and anchor_price > 0
            and legs[0]['numeric_price'] == move_price_down_by_bps(anchor_price, profile_bps)):
            seed.update(profile=profile, target_value_key=ENTRY_REPLAY_PROFILES[profile],
                        incumbent_bps=profile_bps, anchor_price=anchor_price)
            from src.engine.scalping.entry_execution_sizing_plan import PRICE_POLICY_BPS_BOUNDS
            lower, upper = PRICE_POLICY_BPS_BOUNDS[seed['target_value_key']]
            if not lower <= profile_bps <= upper:
                for key in ('profile', 'target_value_key', 'incumbent_bps', 'anchor_price'):
                    seed.pop(key)
                return {**seed, 'seed_sha256': digest(seed)}
            for bps in sorted({max(lower, profile_bps - 1), profile_bps, min(upper, profile_bps + 1)}):
                shift = move_price_down_by_bps(anchor_price, bps) - legs[0]['numeric_price']
                seed['price_candidates'][str(bps)] = [clamp_price_to_tick(x['numeric_price'] + shift) for x in legs]
        return {**seed, 'seed_sha256': digest(seed)}
    except (TypeError, ValueError, KeyError, OverflowError, AttributeError):
        return None


def _entry_seed_valid(seed):
    from src.engine.monitoring.research_closed_loop import digest
    from src.trading.order.tick_utils import move_price_down_by_bps, clamp_price_to_tick
    try:
        if not isinstance(seed, dict):
            return False
        if seed.get('price_candidates'):
            bps, anchor, legs = seed['incumbent_bps'], seed['anchor_price'], seed['legs']
            if (type(bps) is not int or bps <= 0 or type(anchor) is not int or anchor <= 0
                or ENTRY_REPLAY_PROFILES.get(seed['profile']) != seed['target_value_key']
                or legs[0]['price'] != move_price_down_by_bps(anchor, bps)):
                return False
            from src.engine.scalping.entry_execution_sizing_plan import PRICE_POLICY_BPS_BOUNDS
            lower, upper = PRICE_POLICY_BPS_BOUNDS[seed['target_value_key']]
            if not lower <= bps <= upper:
                return False
            expected = {str(b): [clamp_price_to_tick(x['price'] +
                move_price_down_by_bps(anchor, b) - legs[0]['price']) for x in legs]
                for b in sorted({max(lower, bps - 1), bps, min(upper, bps + 1)})}
            if seed['price_candidates'] != expected:
                return False
        return bool(isinstance(seed, dict) and seed.get('schema') == ENTRY_REPLAY_SCHEMA
            and digest({k: v for k, v in seed.items() if k != 'seed_sha256'}) == seed.get('seed_sha256')
            and all(seed.get(k) is v for k, v in AUTHORITY.items())
            and seed.get('exit_contract') == ENTRY_REPLAY_EXIT
            and seed.get('cost_contract') == ENTRY_REPLAY_COST
            and seed.get('allocation_contract') == ENTRY_REPLAY_ALLOCATION
            and seed.get('research_entry_ttl_sec') == 10
            and seed.get('modeled_submit_delay_ms') == 150
            and seed['source_date'] >= '2026-06-05'
            and _timestamp(seed['observed_at'], seed['source_date'])
            and type(seed['total_qty']) is int and seed['total_qty'] > 0
            and type(seed['candidate_qty']) is int and 0 < seed['candidate_qty'] <= seed['total_qty']
            and 0 < len(seed['legs']) <= 3
            and sum(x['qty'] for x in seed['legs']) == seed['total_qty']
            and all(type(x['qty']) is int and x['qty'] > 0
                    and type(x['price']) is int and (x['price'] > 0 or
                        (x['price'] == 0 and x.get('order_type_code') in ('3', '03'))) for x in seed['legs'])
            and (not seed.get('candidate_legs') or (
                _sha(seed.get('candidate_leg_plan_sha256'))
                and 0 < len(seed['candidate_legs']) <= 3
                and sum(x['qty'] for x in seed['candidate_legs']) == seed['total_qty']
                and all(type(x['qty']) is int and x['qty'] > 0
                    and type(x['price']) is int and (x['price'], x.get('order_type_code', '00')) in
                        {(a['price'], a.get('order_type_code', '00')) for a in seed['legs']}
                    for x in seed['candidate_legs'])))
            and re.fullmatch(r'\d{6}', seed['stock_code'])
            and seed['effective_venue'] in ('KRX', 'NXT')
            and all(seed[k] for k in ('scanner_promotion_id', 'evaluation_attempt_id', 'session_bucket'))
            and all(_sha(seed[k]) for k in ('policy_bundle_sha256', 'plan_sha256',
                'entry_price_receipt_sha256', 'entry_price_policy_sha256')))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def replay_entry_opportunity(seed, depth_rows, trade_rows, *, source_ready, evaluated_at):
    """Replay all arms on one continuous exact-scope native path, without requests.

    Marketable full-depth fills are modeled; a passive price touch is unresolved.
    A no-fill is supported only if BOTH the observed asks and trades stay above
    every limit throughout the entire declared TTL. Actual outcomes stay separate.
    """
    from src.engine.monitoring.research_closed_loop import digest
    from src.engine.monitoring.machine_microstructure_attribution import _validate_depth_row, _validate_stream_row
    from src.engine.scalping.entry_split_order_plan import QUANTITY_LEG_FOUR_ARM_IDS
    result = dict(schema=ENTRY_REPLAY_SCHEMA, status='source_gap', blocker=None,
                  seed_sha256=seed.get('seed_sha256') if isinstance(seed, dict) else None,
                  arms=None, price_arms=None, **AUTHORITY)
    try:
        if not source_ready or not _entry_seed_valid(seed) or not _finite(evaluated_at, positive=True):
            raise ValueError('seed_or_source_contract_invalid')
        start = _timestamp(seed['observed_at'], seed['source_date']).timestamp()
        end = start + ENTRY_REPLAY_EXIT['horizon_sec']
        if evaluated_at < end:
            result.update(status='maturity_waiting', blocker='declared_replay_window_not_due', seed=seed)
            return result
        quotes, trades, epochs, identities, trade_identities = [], [], set(), {}, {}
        for row in depth_rows:
            valid, clock, _, _, bid, ask = _validate_depth_row(row)
            if not valid or clock is None:
                raise ValueError('native_depth_contract_invalid')
            at = clock.timestamp()
            if not start - 1.5 <= at <= end + 1.5:
                continue
            if (row.get('symbol') != seed['stock_code'] or row.get('venue') != seed['effective_venue']
                or row.get('session_bucket') != seed['session_bucket']
                or row.get('path_consumer_eligible') is False):
                raise ValueError('native_scope_mismatch')
            epoch, seq = row.get('sequence_epoch'), row.get('source_sequence')
            if type(epoch) is not int or epoch <= 0 or type(seq) is not int or seq <= 0:
                raise ValueError('native_identity_missing')
            identity, sha = (epoch, seq), digest(row)
            if identity in identities:
                if identities[identity] != sha:
                    raise ValueError('native_identity_conflict')
                continue
            identities[identity] = sha
            epochs.add(epoch)
            series = row.get('series_sequence')
            if type(series) is not int or series <= 0:
                raise ValueError('native_depth_series_identity_missing')
            quotes.append((at, bid, ask, row['best_bid_qty'], row['best_ask_qty'], seq, series))
        quotes.sort()
        if (len(epochs) != 1 or not quotes or quotes[0][0] > start
            or end - quotes[-1][0] > 1.5
            or any(b[0] - a[0] > 1.5 or b[-2] <= a[-2] or b[-1] != a[-1] + 1 for a, b in zip(quotes, quotes[1:]))):
            raise ValueError('native_quote_window_incomplete_or_cross_epoch')
        for row in trade_rows:
            valid, eligible, clock, price, _, _ = _validate_stream_row(row)
            if not valid or not eligible or clock is None:
                raise ValueError('native_trade_contract_invalid')
            at = clock.timestamp()
            if start <= at <= start + seed['research_entry_ttl_sec']:
                if (row.get('symbol') != seed['stock_code'] or row.get('venue') != seed['effective_venue']
                    or row.get('session_bucket') != seed['session_bucket']
                    or row.get('sequence_epoch') not in epochs
                    or type(row.get('source_sequence')) is not int
                    or type(row.get('series_sequence')) is not int):
                    raise ValueError('native_trade_scope_or_identity_invalid')
                identity, sha = (row['sequence_epoch'], row['source_sequence']), digest(row)
                if identity in trade_identities:
                    if trade_identities[identity] != sha:
                        raise ValueError('native_trade_identity_conflict')
                    continue
                trade_identities[identity] = sha
                trades.append((at, price, row['series_sequence']))
        trades.sort()
        if (not trades or trades[0][0] - start > 1.5
            or start + seed['research_entry_ttl_sec'] - trades[-1][0] > 1.5
            or any(b[2] != a[2] + 1 for a, b in zip(trades, trades[1:]))):
            raise ValueError('native_trade_window_unproven')
        def arm(quantity, candidate_leg, prices, *, execution_only=False):
            if type(quantity) is not int or not 0 < quantity <= seed['total_qty']:
                raise ValueError('candidate_quantity_outside_frozen_bound')
            shape = (seed.get('candidate_legs') or seed['legs']) if candidate_leg else seed['legs']
            counts = [quantity * x['qty'] // seed['total_qty'] for x in shape]
            counts[0] += quantity - sum(counts)
            entry_at = start + seed['modeled_submit_delay_ms'] / 1000
            total_buy = fill_qty = 0
            filled_legs = []
            fill_events = []
            depth_used = {}
            for index, (qty, limit) in enumerate(zip(counts, prices)):
                if not qty:
                    continue
                market_order = shape[index].get('order_type_code') in ('3', '03')
                if type(limit) is not int or limit < 0 or (limit == 0 and not market_order):
                    raise ValueError('registered_numeric_price_invalid')
                arrival = entry_at + index * seed['modeled_submit_delay_ms'] / 1000
                entry = max((q for q in quotes if q[0] <= arrival), default=None)
                if entry is None or arrival - entry[0] > .7:
                    raise ValueError('modeled_entry_quote_missing_or_stale')
                if market_order or limit >= entry[2]:
                    remaining = entry[4] - depth_used.get(entry[-2], 0)
                    if remaining < qty:
                        raise ValueError('full_quantity_depth_unproven')
                    depth_used[entry[-2]] = depth_used.get(entry[-2], 0) + qty
                    fill_qty += qty
                    total_buy += qty * entry[2]
                    filled_legs.append((arrival, qty * entry[2]))
                    fill_events.append(dict(at=datetime.fromtimestamp(arrival, KST).isoformat(), qty=qty, price=entry[2], reserved_price=limit or entry[2]))
                elif not (all(q[2] > limit for q in quotes if arrival <= q[0] <= start + seed['research_entry_ttl_sec'])
                          and all(t[1] > limit for t in trades if arrival <= t[0])):
                    raise ValueError('passive_queue_fill_or_partial_unproven')
            common = dict(terminal_conservation_holds=True, cost_complete=True,
                counterfactual_executable=True, entry_price_receipt_sha256=seed['entry_price_receipt_sha256'],
                exit_policy_sha256=digest(seed['exit_contract']), cost_contract_sha256=digest(seed['cost_contract']),
                terminal_contract_version='fixed_quote_research_exit_180sec_v1',
                terminal_observed_at=datetime.fromtimestamp(end, KST).isoformat(),
                requested_qty=quantity, modeled_filled_qty=fill_qty,
                actual_fill_evidence=False, modeled_fill_events=fill_events,
                modeled_reserved_notional_krw=sum(q * p for q, p in zip(counts, prices)))
            if not fill_qty:
                return dict(net_return_pct=0.0, net_pnl_krw=0.0, capital_krw_minutes=0.0,
                    stress_net_return_pct=0.0, fill_participation_rate=0.0,
                    modeled_outcome='supported_no_fill', **common)
            entry_price = total_buy / fill_qty
            last_fill_at = max(at for at, _ in filled_legs)
            if execution_only:
                return dict(modeled_entry_vwap=entry_price,
                    modeled_last_fill_at=datetime.fromtimestamp(last_fill_at, KST).isoformat(),
                    modeled_entry_at=datetime.fromtimestamp(min(at for at, _ in filled_legs), KST).isoformat(),
                    modeled_outcome='operating_entry_execution_only', **common)
            exit_quote = next((q for q in quotes if q[0] > last_fill_at and q[0] <= end and
                (q[1] / entry_price - 1) * 100 >= ENTRY_REPLAY_EXIT['take_profit_pct']), None)
            stop_quote = next((q for q in quotes if q[0] > last_fill_at and q[0] <= end and
                (q[1] / entry_price - 1) * 100 <= ENTRY_REPLAY_EXIT['stop_loss_pct']), None)
            terminal = min((q for q in (exit_quote, stop_quote) if q), default=None)
            terminal = terminal or max((q for q in quotes if q[0] <= end), default=None)
            if terminal is None or terminal[3] < fill_qty or terminal[0] <= last_fill_at:
                raise ValueError('full_exit_depth_or_duration_unproven')
            gross = (terminal[1] / entry_price - 1) * 100
            net = gross - ENTRY_REPLAY_COST['round_trip_pct']
            return dict(net_return_pct=net, stress_net_return_pct=gross - ENTRY_REPLAY_COST['stress_round_trip_pct'],
                net_pnl_krw=total_buy * net / 100,
                capital_krw_minutes=sum(notional * (terminal[0] - at) / 60 for at, notional in filled_legs),
                fill_participation_rate=fill_qty / quantity,
                modeled_entry_vwap=entry_price,
                modeled_last_fill_at=datetime.fromtimestamp(last_fill_at, KST).isoformat(),
                modeled_entry_at=datetime.fromtimestamp(min(at for at, _ in filled_legs), KST).isoformat(),
                modeled_exit_at=datetime.fromtimestamp(terminal[0], KST).isoformat(),
                modeled_outcome='modeled_full_or_partial_filled_terminal', **common)
        prices = [x['price'] for x in seed['legs']]
        arms, price_arms, operating_arms = {}, {}, {}
        for i, name in enumerate(QUANTITY_LEG_FOUR_ARM_IDS):
            quantity=seed['candidate_qty'] if i % 2 else seed['total_qty']
            values=[x['price'] for x in (seed.get('candidate_legs') or seed['legs'])] if i>=2 else prices
            try:
                execution=arm(quantity,i>=2,values,execution_only=True)
                if seed.get('operating_contract'):
                    operating_arms[name]=replay_operating_entry_arm(seed,execution,depth_rows,trade_rows=trade_rows)
                try:arms[name]=arm(quantity,i>=2,values)
                except ValueError:
                    if not seed.get('operating_contract'):raise
                    arms[name]=execution
            except ValueError as exc:
                if not seed.get('operating_contract'):raise
                gap=dict(schema=ENTRY_OPERATING_SCHEMA,status='unsupported_scope',blocker=str(exc),
                    net_pnl_krw=None,stress_net_pnl_krw=None,capital_krw_minutes=None,reserve_krw_minutes=None,
                    requested_qty=quantity,actual_fill_evidence=False,**AUTHORITY)
                from src.engine.scalping.entry_split_order_plan import _canonical_sha256
                operating_arms[name]={**gap,'sha256':_canonical_sha256(gap)}
        for bps,values in seed['price_candidates'].items():
            try:price_arms[bps]=arm(seed['total_qty'],False,values)
            except ValueError:
                if not seed.get('operating_contract'):raise
        result.update(status='completed_source_only', blocker=None, seed=seed,
                      arms=arms, price_arms=price_arms,
                      native_window_sha256=digest([depth_rows, trade_rows]))
        if seed.get('operating_contract'):result['operating_arms']=operating_arms
        result['replay_sha256'] = digest(result)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        result.update(blocker=str(exc), arms=None, price_arms=None)
    return result


def build_entry_opportunity_replays(day, events, *, evaluated_at=None, micro_loader=None,
                                    source_stage="entry_execution_sizing_plan"):
    """Existing missed-entry report embeds exact plan/path replays, including submits.

    Reads the existing native collector via its canonical exclusion/parser owner.
    No collector, network call, raw deletion, or additional scheduled stage.
    """
    import ast
    from collections import Counter
    from src.engine.monitoring import machine_microstructure_attribution as micro
    from src.engine.monitoring.research_closed_loop import digest
    from src.engine.sniper_missed_entry_counterfactual import _price_ready_plan
    from src.engine.scalping.entry_split_order_plan import QUANTITY_LEG_FOUR_ARM_IDS
    output = dict(schema=ENTRY_REPLAY_SCHEMA, source_date=day, rows=[],
                  counts={}, quantity_leg_events=[], **AUTHORITY)
    candidates, rejected, conflicts, valid_counts = {}, Counter(), set(), Counter()
    first_blockers = Counter()
    availability, availability_conflicts = {}, set()
    if source_stage == "entry_ai_economic_plan_observed":
        for event in events:
            if event.stage != "entry_ai_economic_decision_available":
                continue
            key = (event.fields.get("evaluation_attempt_id"), event.fields.get("entry_economic_plan_sha256"))
            value = event.fields.get("entry_economic_decision_available_at")
            if key in availability and availability[key] != value:
                availability_conflicts.add(key)
            availability[key] = value
    for event in events:
        if event.stage != source_stage:
            continue
        plan, seed = _price_ready_plan(event), event.fields.get('entry_opportunity_replay_seed')
        try:
            if isinstance(seed, str) and len(seed) <= 2 * 1024 * 1024:
                try:
                    seed = json.loads(seed)
                except ValueError:
                    seed = ast.literal_eval(seed)
            if (not plan or not _entry_seed_valid(seed) or seed.get('source_date') != day
                or seed.get('plan_sha256') != digest(plan)
                or seed.get('plan_sha256') != event.fields.get('entry_execution_sizing_plan_sha256')
                or seed.get('stock_code') != event.code
                or seed.get('evaluation_attempt_id') != plan['action_receipt_id']):
                raise ValueError('original_plan_or_frozen_seed_missing_or_invalid')
            if source_stage == "entry_ai_economic_plan_observed":
                available_key = (seed['evaluation_attempt_id'], seed['plan_sha256'])
                if available_key in availability_conflicts or available_key not in availability:
                    raise ValueError('pre_ai_decision_availability_missing_or_conflicting')
                available_at = _timestamp(availability[available_key], day)
                if available_at < _timestamp(seed['observed_at'], day):
                    raise ValueError('pre_ai_decision_availability_before_plan')
                # Derived replay clock; preserve the original immutable seed/plan identity.
                seed = {**seed, 'original_pre_ai_seed_sha256': seed['seed_sha256'],
                        'plan_observed_at': seed['observed_at'], 'observed_at': available_at.isoformat()}
                seed['seed_sha256'] = digest({k:v for k,v in seed.items() if k != 'seed_sha256'})
            key = digest([seed[k] for k in ('stock_code', 'scanner_promotion_id',
                'evaluation_attempt_id', 'effective_venue', 'session_bucket', 'policy_bundle_sha256')])
            valid_counts[key] += 1
            if key in candidates:
                if candidates[key] != seed:
                    conflicts.add(key)
                else:
                    rejected['duplicate_exact_plan'] += 1
            else:
                candidates[key] = seed
        except (TypeError, ValueError, KeyError, SyntaxError, RecursionError) as exc:
            first_blockers[str(exc)] += 1
            rejected['original_plan_or_frozen_seed_missing_or_invalid'] += 1
    rejected['conflicting_exact_plan'] += len(conflicts)
    # Raw-row and unique-attempt dispositions are separate conserved populations.
    row_disposition = dict(retained_anchor_rows=len(candidates) - len(conflicts),
        duplicate_rows=sum(n - 1 for k, n in valid_counts.items() if k not in conflicts),
        conflicting_rows=sum(valid_counts[k] for k in conflicts),
        rejected_rows=rejected['original_plan_or_frozen_seed_missing_or_invalid'])
    seeds = {k: v for k, v in candidates.items() if k not in conflicts}
    now = evaluated_at if evaluated_at is not None else time.time()
    ready = {k: v for k, v in seeds.items()
             if _timestamp(v['observed_at'], day).timestamp() + ENTRY_REPLAY_EXIT['horizon_sec'] <= now}
    waiting = len(seeds) - len(ready)
    for key, seed in seeds.items():
        if key not in ready:
            output['rows'].append(dict(schema=ENTRY_REPLAY_SCHEMA, status='maturity_waiting',
                blocker='declared_replay_window_not_due', seed=seed, arms=None, price_arms=None, **AUTHORITY))
    if ready:
        anchors = [dict(anchor_id=k, symbol=v['stock_code'], anchor_at=v['observed_at'],
                    expected_venues=[v['effective_venue']], expected_session_buckets=[v['session_bucket']],
                    bounded_entry_opportunity_replay=True) for k, v in ready.items()]
        try:
            canary = micro.resolve_target_canary_snapshot(target_date=date.fromisoformat(day),
                latest_path=micro.DEFAULT_CANARY_SNAPSHOT_PATH, daily_root=micro.CANARY_DAILY_SNAPSHOT_DIR)
            generation_paths = [micro.OBSERVATION_ROOT / f'trade_date={day}',
                                micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST]
            if canary is not None:
                generation_paths.append(canary)
            generation = micro._source_generation_contract({}, extra_paths=generation_paths)
            if any(Path(r['path']).is_symlink() for r in generation['source_rows']):
                raise ValueError('native_source_final_symlink')
            source, inventory, windows = (micro_loader or micro._micro_context)(
                day, micro.OBSERVATION_ROOT, {v['stock_code'] for v in ready.values()}, anchors,
                micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST, canary, datetime.fromtimestamp(now, KST))
            after = micro._source_generation_contract({}, extra_paths=generation_paths)
            if generation != after:
                raise ValueError('native_source_generation_changed_during_replay')
            output['native_source'] = {**source, 'source_generation': generation}
            for key, seed in ready.items():
                window = windows.get(key) or {}
                result = replay_entry_opportunity(seed, window.get('raw_depth_rows') or [],
                    window.get('raw_market_rows') or [], evaluated_at=now,
                    source_ready=(source.get('source_contract_ready') is True
                                  and not window.get('adaptive_exit_source_overflow')
                                  and not micro._invalid_contract_count_for_scope(
                                      inventory.get(seed['stock_code']) or {},
                                      expected_venues=[seed['effective_venue']],
                                      expected_sessions=[seed['session_bucket']])))
                if result.get('seed') is None:
                    result['seed'] = seed
                output['rows'].append(result)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            output['native_source'] = dict(status='source_gap', reason=str(exc))
            output['rows'] = [r for r in output['rows'] if r['status'] == 'maturity_waiting']
            output['rows'].extend(dict(schema=ENTRY_REPLAY_SCHEMA, status='source_gap',
                blocker='native_source_contract_unavailable', seed=seed, arms=None, price_arms=None,
                **AUTHORITY) for seed in ready.values())
    reservation, promotions, admitted = -math.inf, set(), set()
    for key, seed in sorted(ready.items(), key=lambda kv: (kv[1]['observed_at'], kv[1]['seed_sha256'])):
        at = _timestamp(seed['observed_at'], day).timestamp()
        promotion = (seed['stock_code'], seed['scanner_promotion_id'])
        if at >= reservation and promotion not in promotions:
            admitted.add(key)
            reservation = at + ENTRY_REPLAY_ALLOCATION['reservation_sec']
            promotions.add(promotion)
    for row in output['rows']:
        if row['status'] != 'completed_source_only':
            continue
        seed = row['seed']
        key = digest([seed[k] for k in ('stock_code', 'scanner_promotion_id',
            'evaluation_attempt_id', 'effective_venue', 'session_bucket', 'policy_bundle_sha256')])
        row['incumbent_execution_arm'] = dict(row['arms'].get(QUANTITY_LEG_FOUR_ARM_IDS[0]) or {})
        row['allocation_admitted'] = key in admitted
        if key not in admitted:
            for arm in row['arms'].values():
                arm.update(net_return_pct=0., stress_net_return_pct=0., net_pnl_krw=0.,
                    capital_krw_minutes=0., fill_participation_rate=0., modeled_filled_qty=0,
                    modeled_outcome='modeled_no_exposure_common_reservation')
        row['replay_sha256'] = digest({k: v for k, v in row.items() if k != 'replay_sha256'})
    completed = [r for r in output['rows'] if r['status'] == 'completed_source_only']
    # Receipt denominator includes incomplete usable-anchor attempts; exclude no row silently.
    for row in completed:
        seed = row['seed']
        receipt = {k: seed[k] for k in ('source_date', 'scanner_promotion_id', 'evaluation_attempt_id',
            'stock_code', 'effective_venue', 'session_bucket', 'policy_bundle_sha256',
            'incumbent_quantity_policy_version', 'candidate_quantity_policy_version',
            'incumbent_leg_policy_version', 'candidate_leg_policy_version', 'entry_price_policy_sha256')}
        receipt.update(schema='entry_quantity_leg_four_arm_evaluation_v1', arms=row['arms'],
                       eligible_attempt_count=len(seeds), native_replay_sha256=row['replay_sha256'])
        receipt['entry_price_replay_row'] = row
        receipt['receipt_sha256'] = digest(receipt)
        output['quantity_leg_events'].append(dict(source_date=day, stock_code=seed['stock_code'],
            stage='entry_quantity_leg_four_arm_evaluation',
            observed_at=seed['observed_at'], effective_venue=seed['effective_venue'],
            market_session_bucket=seed['session_bucket'],
            entry_quantity_leg_four_arm_evaluation=receipt))
    output['counts'] = dict(unique_retained=len(seeds), completed=len(completed),
        maturity_waiting=waiting, source_gap=len(ready) - len(completed), excluded=dict(rejected),
        source_stage=source_stage, raw_plan_rows=sum(e.stage == source_stage for e in events),
        raw_row_disposition=row_disposition, first_blocker_counts=dict(first_blockers))
    output['sha256'] = digest(output)
    return output


def select_entry_price_replay(rows, *, eligible_count=None, source_counts=None):
    """Choose on calibration ONLY, test that frozen choice once on latest day.

    Entire common opportunity population includes supported zero-fill arms.
    Output is re-evaluated by publisher/PREOPEN/runtime from signed paired rows.
    """
    from collections import Counter, defaultdict
    from src.engine.monitoring.research_closed_loop import digest
    groups, seen, conflicts = defaultdict(list), {}, set()
    # A completed-row list cannot prove the original population or its latest
    # eligible date. Formal selection always needs the producer's full census.
    try:
        if (not isinstance(source_counts, dict) or type(eligible_count) is not int
            or any(date.fromisoformat(d).isoformat() != d or d < '2026-06-05'
                   or type(n) is not int or n < 0 for d, n in source_counts.items())
            or sum(source_counts.values()) != eligible_count):
            return []
    except (TypeError, ValueError):
        return []
    for row in rows:
        try:
            if row.get('status') != 'completed_source_only':
                continue
            body = {k: v for k, v in row.items() if k != 'replay_sha256'}
            if digest(body) != row.get('replay_sha256'):
                continue
            seed = row['seed']
            if not _entry_seed_valid(seed):
                continue
            identity = tuple(seed[k] for k in ('stock_code', 'scanner_promotion_id',
                'evaluation_attempt_id', 'effective_venue', 'session_bucket', 'policy_bundle_sha256'))
            if identity in seen:
                if seen[identity] != row:
                    conflicts.add(identity)
                continue
            seen[identity] = row
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    union = [row for identity, row in seen.items() if identity not in conflicts]
    complete_by_date = Counter(r['seed']['source_date'] for r in union)
    if any(n > source_counts.get(day, 0) for day, n in complete_by_date.items()):
        return []
    def group_key(seed):
        return tuple(seed.get(k) for k in ('profile', 'target_value_key', 'incumbent_bps',
            'effective_venue', 'session_bucket', 'policy_bundle_sha256', 'entry_price_policy_sha256'))
    for identity, row in seen.items():
        if identity in conflicts:
            continue
        seed = row['seed']
        if not seed.get('price_candidates') or str(seed.get('incumbent_bps')) not in row['price_arms']:
            continue
        group = group_key(seed)
        groups[group].append(row)
    def metrics(sample, bps, target_group):
        if not sample:
            raise ValueError("latest_source_partition_missing_outcomes")
        ordered = sorted(sample, key=lambda r: (r['seed']['observed_at'], r['seed']['seed_sha256']))
        arms, reserved_until, promotions = [], -math.inf, set()
        for r in ordered:
            seed = r['seed']
            at = _timestamp(seed['observed_at'], seed['source_date']).timestamp()
            promotion = (seed['source_date'], seed['stock_code'], seed['scanner_promotion_id'])
            if r.get('allocation_admitted') is False or at < reserved_until or promotion in promotions:
                # Explicit modeled no exposure from the SAME allocation rule for both policies.
                arms.append(dict(net_return_pct=0., stress_net_return_pct=0., net_pnl_krw=0.,
                    capital_krw_minutes=0., fill_participation_rate=0., cost_complete=True,
                    counterfactual_executable=True))
            else:
                if bps is not None and group_key(seed) == target_group:
                    arms.append(r['price_arms'][str(bps)])
                elif seed.get('price_candidates'):
                    arms.append(r['price_arms'][str(seed['incumbent_bps'])])
                else:
                    # Other price branches stay on their original owner-issued plan.
                    from src.engine.scalping.entry_split_order_plan import QUANTITY_LEG_FOUR_ARM_IDS
                    arms.append(r['arms'][QUANTITY_LEG_FOUR_ARM_IDS[0]])
                reserved_until = at + ENTRY_REPLAY_ALLOCATION['reservation_sec']
                promotions.add(promotion)
        for a in arms:
            if (not all(_finite(a.get(k)) for k in ('net_return_pct', 'stress_net_return_pct',
                    'net_pnl_krw', 'capital_krw_minutes', 'fill_participation_rate'))
                or a['capital_krw_minutes'] < 0 or not 0 <= a['fill_participation_rate'] <= 1
                or a.get('cost_complete') is not True or a.get('counterfactual_executable') is not True):
                raise ValueError('paired_arm_invalid')
        net = [a['net_return_pct'] for a in arms]
        pnl = sum(a['net_pnl_krw'] for a in arms)
        capital = sum(a['capital_krw_minutes'] for a in arms)
        dates = {r['seed']['source_date'] for r in sample}
        return dict(source_quality_adjusted_ev_pct=sum(net) / len(net),
            stress_ev_pct=sum(a['stress_net_return_pct'] for a in arms) / len(arms),
            modeled_net_profit_krw=pnl, modeled_net_profit_per_source_day=pnl / len(dates),
            downside_p10_net_pct=sorted(net)[max(0, math.ceil(len(net) * .1) - 1)],
            positive_terminal_frequency=sum(n > 0 for n in net) / len(net),
            fill_participation_rate=sum(a['fill_participation_rate'] for a in arms) / len(arms),
            modeled_capital_krw_minutes=capital,
            modeled_net_profit_per_capital_minute=pnl / capital if capital > 0 else 0.0,
            paired_sample_count=len(arms), qualified_source_day_count=len(dates))
    def improved(c, i):
        return bool(c['source_quality_adjusted_ev_pct'] > 0 and c['stress_ev_pct'] > 0
            and c['source_quality_adjusted_ev_pct'] > i['source_quality_adjusted_ev_pct']
            and c['modeled_net_profit_per_source_day'] > i['modeled_net_profit_per_source_day']
            and c['stress_ev_pct'] >= i['stress_ev_pct']
            and c['downside_p10_net_pct'] >= i['downside_p10_net_pct']
            and c['positive_terminal_frequency'] >= i['positive_terminal_frequency']
            and c['fill_participation_rate'] >= i['fill_participation_rate'] - .05
            and c['modeled_net_profit_per_capital_minute'] >= i['modeled_net_profit_per_capital_minute'])
    selected, proposals = [], []
    for group, sample in groups.items():
        try:
            days = sorted(d for d, n in source_counts.items() if n > 0) if source_counts is not None else sorted({r['seed']['source_date'] for r in union})
            if source_counts is not None and any(r['seed']['source_date'] not in source_counts for r in union):
                continue
            if len(sample) < 20 or len(days) < 2:
                continue
            cal = [r for r in union if r['seed']['source_date'] < days[-1]]
            hold = [r for r in union if r['seed']['source_date'] == days[-1]]
            inc_bps = group[2]
            menu = set.intersection(*(set(r['price_arms']) for r in sample))
            incumbent = metrics(cal, None, group)
            candidates = [(int(bps), metrics(cal, bps, group)) for bps in menu if int(bps) != inc_bps]
            candidates = [(bps, m) for bps, m in candidates if improved(m, incumbent)]
            if not candidates:
                continue
            bps, _ = max(candidates, key=lambda x: (x[1]['modeled_net_profit_per_source_day'], -x[0]))
            denominator = eligible_count if eligible_count is not None else len(rows)
            if type(denominator) is not int or denominator < len(union) or len(union) / denominator < .8:
                continue
            proposals.append((group, sample, days, cal, hold, bps, metrics(cal, bps, group)))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    proposals.sort(key=lambda p: (-p[-1]['modeled_net_profit_per_source_day'], str(p[0]), p[5]))
    for group, sample, days, cal, hold, bps, _ in proposals[:1]:
        try:
            inc_bps = group[2]
            # No second candidate is tested against the same holdout after a veto.
            if not improved(metrics(hold, bps, group), metrics(hold, None, group)):
                continue
            candidate_metrics = metrics(union, bps, group)
            if not improved(candidate_metrics, metrics(union, None, group)):
                continue
            denominator = eligible_count if eligible_count is not None else len(rows)
            if type(denominator) is not int or denominator < len(union) or len(union) / denominator < .8:
                continue
            proof = dict(selection_contract=ENTRY_PRICE_SELECTION, profile=group[0],
                target_value_key=group[1], incumbent_bps=inc_bps, selected_bps=bps,
                scope_parent=list(group[3:]), eligible_attempt_count=denominator,
                paired_rows=union, changed_profile_paired_sample_count=len(sample),
                union_contract='all_valid_price_ready_fixed_other_profiles_v1',
                calibration_dates=days[:-1], holdout_dates=[days[-1]],
                source_counts=source_counts,
                metrics=candidate_metrics, incumbent_metrics=metrics(union, None, group),
                allocation_contract=ENTRY_REPLAY_ALLOCATION.copy(),
                minimum_cost_adjusted_ev_pct=0.0, positive_net_required=True,
                cost_scope='conditional_price_execution_common_upstream_screen_cost_not_reestimated',
                actual_provider_cost_krw=None,
                metric_role='primary_ev', decision_authority='existing_bounded_price_family',
                window_policy='same_frozen_opportunity_union_chronological_latest_day_holdout',
                sample_floor=20, primary_decision_metric='source_quality_adjusted_ev_pct',
                source_quality_gate='exact_signed_native_quote_trade_cost_exit_source',
                forbidden_uses=['broker_fill_quality', 'realized_pnl', 'end_to_end_entry_net_profit', 'quantity_or_action_authority'])
            proof['evidence_sha256'] = digest(proof)
            selected.append(proof)
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    return selected


def entry_price_selection_evidence_valid(proof):
    from src.engine.monitoring.research_closed_loop import digest
    try:
        if not isinstance(proof, dict) or proof.get('selection_contract') != ENTRY_PRICE_SELECTION:
            return False
        candidates = select_entry_price_replay(proof['paired_rows'], eligible_count=proof['eligible_attempt_count'],
            source_counts=proof.get('source_counts'))
        return any(digest(p) == digest(proof) for p in candidates)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False

# Initial-entry economics reuse the full holding interpreter, not the fixed
# research TP/SL kernel. Missing exact-state services never become assumed HOLD.
ENTRY_OPERATING_SCHEMA = 'entry_split_operating_economics_v1'
ENTRY_MODEL_SELECTION = 'entry_split_empirical_model_holdout_v1'


@lru_cache(maxsize=1)
def entry_operating_model_identity():
    from src.engine.lifecycle.avg_down_policy_replay import implementation_identity
    identity=implementation_identity()
    base=Path(__file__).resolve().parents[3]
    import hashlib
    for name in ("src/engine/scalping/avg_down_replay_capture.py","src/engine/scalping/micro_reversion/path_journal.py"):
        identity[name]=hashlib.sha256((base/name).read_bytes()).hexdigest()
    return owner.digest(identity)



def freeze_entry_operating_context(handlers, stock, sizing_context, *, now_ts):
    from src.engine.scalping import avg_down_replay_capture as capture
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version
    from src.engine.trade_profit import get_trade_cost_rate
    try:
        if handlers._is_any_simulated_position(stock, stock.get('strategy')):
            return None
        budget = sizing_context.budget_base_krw * sizing_context.safety_ratio
        if sizing_context.absolute_budget_cap_krw > 0:
            budget = min(budget, sizing_context.absolute_budget_cap_krw)
        if not _finite(budget, positive=True):
            return None
        snapshot = capture._cached_policy(handlers, now_ts)
        from types import SimpleNamespace
        from src.engine.sniper_execution_receipts import initial_scalp_preset_exit_fields
        if not handlers.is_default_position_tag("SCALPING", stock.get("position_tag")):
            return None
        initial_exit = initial_scalp_preset_exit_fields(stock, rules=SimpleNamespace(**snapshot["rules"]))
        value = dict(schema=ENTRY_OPERATING_SCHEMA,
            initial_fill_exit_contract_version="main_scalp_preset_initial_fill_v1",
            initial_fill_exit_owner="sniper_execution_receipts.initial_scalp_preset_exit_fields",
            initial_fill_exit_state=initial_exit,
            initial_micro_estimator_state=capture.micro_state(handlers, stock.get('code', '')),
            frozen_at=datetime.fromtimestamp(now_ts, KST).isoformat(),
            policy_snapshot=snapshot, exit_policy_version=snapshot_version(snapshot),
            initial_policy_state=capture.holding_state(handlers, {k:v for k,v in stock.items() if k not in {"entry_split_initial_entry_seed","entry_split_initial_entry_lineage_conflict"}}),
            budget_krw=budget, cost_rate=get_trade_cost_rate(),
            model_implementation_sha256=entry_operating_model_identity(),
            cost_policy_version='trade_profit_net_realized_pnl:rate=' + str(get_trade_cost_rate()),
            cost_provenance='frozen_loaded_trade_profit_configuration_not_broker_settlement',
            stress_cost_rate_increment=(ENTRY_REPLAY_COST['stress_round_trip_pct'] - ENTRY_REPLAY_COST['round_trip_pct']) / 100,
            max_frame_gap_sec=capture.MAX_FRAME_GAP_SEC, **AUTHORITY)
        return {**value, 'sha256': owner.digest(value)}
    except (ValueError, TypeError, AttributeError, KeyError):
        return None


def replay_operating_entry_arm(seed, arm, depth_rows, *, executor=None, trade_rows=()):
    """Independent CF holding path, original reserve and conservative full exit.

    Default executor is the existing no-network/no-write disposable interpreter.
    Recorded exact-state policy evaluations can be supplied by its existing pure
    replay engine in tests; an actual SELL is never an exit decision for this arm.
    """
    from src.engine.lifecycle import avg_down_policy_replay as adapter
    from src.engine.trade_profit import calculate_net_realized_pnl
    from src.engine.scalping.entry_split_order_plan import _canonical_sha256 as economics_digest
    result = dict(schema=ENTRY_OPERATING_SCHEMA, status='source_gap', net_pnl_krw=None,
        stress_net_pnl_krw=None, net_return_pct=None, capital_krw_minutes=None,
        reserve_krw_minutes=None, blocker=None, actual_fill_evidence=False,
        source_gap_owner='entry_execution_sizing_plan->sniper_state_handlers->strategy_owner_replay',
        closure_test='frozen operating timeout/cost/state; full executable initial fill then independent full holding exit; partial/no-fill requires state-specific cancel acknowledgement and late-fill inventory witness', **AUTHORITY)
    try:
        context = seed.get('operating_contract')
        if (not isinstance(context, dict) or context.get('schema') != ENTRY_OPERATING_SCHEMA
            or owner.digest({k: v for k, v in context.items() if k != 'sha256'}) != context.get('sha256')
            or context.get('exit_policy_version') != adapter.snapshot_version(context['policy_snapshot'])
            or context.get('model_implementation_sha256') != entry_operating_model_identity()
            or any(context.get(k) is not v for k, v in AUTHORITY.items())
            or not _finite(context.get('cost_rate')) or not 0 <= context['cost_rate'] < 1
            or not _finite(context.get('stress_cost_rate_increment')) or context['stress_cost_rate_increment'] < 0
            or context.get('cost_policy_version') != 'trade_profit_net_realized_pnl:rate=' + str(context['cost_rate'])
            or context.get('cost_provenance') != 'frozen_loaded_trade_profit_configuration_not_broker_settlement'
            or not _finite(context.get('budget_krw'), positive=True)
            or _timestamp(context['frozen_at'], seed['source_date']) > _timestamp(seed['observed_at'], seed['source_date'])
            or not _entry_seed_valid(seed) or arm.get('requested_qty') != seed['total_qty']):
            raise ValueError('frozen_operating_contract_or_quantity_scope_invalid')
        started = _timestamp(seed['observed_at'], seed['source_date']).timestamp()
        fills = arm.get('modeled_fill_events') or []
        qty = arm.get('modeled_filled_qty')
        if type(qty) is not int or qty < 0 or qty > seed['total_qty']:
            raise ValueError('operating_entry_quantity_invalid')
        if sum(x['qty'] for x in fills) != qty:
            raise ValueError('operating_entry_fill_conservation_invalid')
        reserve = arm.get('modeled_reserved_notional_krw')
        if not _finite(reserve, positive=True):
            reserve = sum(x['qty'] * (x['price'] or seed.get('anchor_price', 0)) for x in seed['legs'])
        if not _finite(reserve, positive=True) or reserve > context['budget_krw']:
            raise ValueError('frozen_reservation_or_budget_unproven')
        result.update(budget_krw=context['budget_krw'], source_date=seed['source_date'],
            exit_policy_sha256=context['exit_policy_version'], cost_policy_version=context['cost_policy_version'],
            cost_provenance=context['cost_provenance'], contract_sha256=context['sha256'],
            requested_qty=seed['total_qty'], modeled_filled_qty=qty,
            fill_participation_rate=qty / seed['total_qty'])
        ttls=context.get('order_leg_ttl_sec')
        if (not isinstance(ttls,list) or len(ttls)!=len(seed['legs']) or any(not _finite(t,positive=True) for t in ttls)
            or not _finite(context.get('order_bundle_hard_ttl_sec'),positive=True) or not context.get('order_timeout_owner')):
            raise ValueError('frozen_operating_order_timeout_contract_missing')
        if 0 < qty < seed['total_qty']:
            result.update(status='unsupported_scope',blocker='counterfactual_partial_pending_entry_cancel_and_late_fill_inventory_unproven')
            return {**result,'sha256':economics_digest(result)}
        if not qty:
            result.update(status='unsupported_scope',blocker='counterfactual_zero_fill_cancel_ack_and_late_fill_window_unproven')
            return {**result,'sha256':economics_digest(result)}
        if any(type(x['qty']) is not int or x['qty'] <= 0 or not _finite(x['price'], positive=True)
               or _timestamp(x['at'], seed['source_date']).timestamp() < started for x in fills):
            raise ValueError('operating_entry_fill_clock_or_price_invalid')
        last_at = max(_timestamp(x['at'], seed['source_date']).timestamp() for x in fills)
        first_at=min(_timestamp(x['at'],seed['source_date']).timestamp() for x in fills)
        from src.engine.monitoring.machine_microstructure_attribution import _validate_depth_row
        if any(valid and clock is not None and first_at < clock.timestamp() < last_at
            for valid,clock,*_ in (_validate_depth_row(row) for row in depth_rows)):
            raise ValueError('operating_pre_final_fill_holding_transition_unmodeled')
        amount = sum(x['qty'] * x['price'] for x in fills)
        weighted = amount / qty
        state = copy.deepcopy(context['initial_policy_state'])
        stock = state['stock']
        if "initial_fill_exit_state" in context:
            from types import SimpleNamespace
            from src.engine.sniper_execution_receipts import initial_scalp_preset_exit_fields
            expected = initial_scalp_preset_exit_fields(stock, rules=SimpleNamespace(**context['policy_snapshot']['rules']))
            if (context.get('initial_fill_exit_contract_version') != 'main_scalp_preset_initial_fill_v1'
                or context.get('initial_fill_exit_owner') != 'sniper_execution_receipts.initial_scalp_preset_exit_fields'
                or context['initial_fill_exit_state'] != expected):
                raise ValueError('frozen_initial_fill_exit_transition_invalid')
            stock.update(expected)
        # These are modeled inventory fields, never a receipt of a real fill.
        stock.update(code=seed['stock_code'], status='HOLDING', strategy='SCALPING',
            buy_price=weighted, buy_qty=qty, pending_add_order=None, pending_entry_orders=[],
            sell_submit_pending=False, buy_time=datetime.fromtimestamp(last_at, KST).isoformat(),
            holding_started_at=adapter._json_value(datetime.fromtimestamp(last_at, KST)), order_time=last_at)
        episode = 'entry-operating-' + seed['seed_sha256']
        observation = dict(source_event_id=episode, scale_in_decision_id=episode,
            position_episode_id=episode, stock_code=seed['stock_code'], venue=seed['effective_venue'],
            emitted_at=datetime.fromtimestamp(last_at, KST).isoformat(),
            exit_policy_version=context['exit_policy_version'], policy_snapshot=context['policy_snapshot'],
            initial_policy_state=state, pre_add_buy_qty=qty, pre_add_buy_price=weighted,
            replay_peak_price=weighted, replay_start_sequence=0,
            replay_max_frame_gap_sec=context['max_frame_gap_sec'], cost_rate=context['cost_rate'],
            entry_split_initial_only=True, effective_min_buy_pressure=1,
            route_replay={'ENTRY': dict(should_add=False, route_evaluation_complete=True)})
        micro_store = None
        if context.get('initial_micro_estimator_state') is not None:
            from src.engine.scalping.micro_estimator_state import MicroEstimatorStore, MicroEstimatorConfig, SymbolMicroEstimatorState
            micro = context['initial_micro_estimator_state']
            if not isinstance(micro, dict) or not isinstance(micro.get('config'), dict):
                raise ValueError('frozen_micro_estimator_contract_invalid')
            micro_store = MicroEstimatorStore(MicroEstimatorConfig(**micro['config']))
            if micro.get('state') is not None:
                micro_store._states[seed['stock_code']] = SymbolMicroEstimatorState(**adapter.thaw(copy.deepcopy(micro['state'])))
        frames = []
        for row in depth_rows:
            clock = row.get('exchange_at') or row.get('observed_at') or row.get('emitted_at')
            # Native validation precedes this helper; exact policy/service values
            # remain bound to the recorded frame, never looked up from today's env.
            from src.engine.monitoring.machine_microstructure_attribution import _validate_depth_row
            if (row.get('symbol') != seed['stock_code'] or row.get('venue') != seed['effective_venue']
                or row.get('session_bucket') != seed['session_bucket']):
                raise ValueError('operating_native_frame_scope_mismatch')
            valid, parsed, _, _, bid, ask = _validate_depth_row(row)
            if not valid or parsed is None or row.get('path_consumer_eligible') is False:
                raise ValueError('operating_native_frame_invalid')
            if parsed.timestamp() <= last_at:
                continue
            ws = row.get('ws_data')
            if not isinstance(ws, dict):
                from src.engine.monitoring.machine_microstructure_attribution import _validate_stream_row
                tick_values = []
                for tick in trade_rows:
                    valid_tick, eligible_tick, tick_at, tick_price, _, _ = _validate_stream_row(tick)
                    if (valid_tick and eligible_tick and tick_at is not None
                        and tick.get('symbol') == seed['stock_code'] and tick.get('venue') == seed['effective_venue']
                        and tick.get('session_bucket') == seed['session_bucket']
                        and 0 <= parsed.timestamp() - tick_at.timestamp() <= context['max_frame_gap_sec']):
                        tick_values.append((tick_at.timestamp(), tick_price))
                if not tick_values:
                    raise ValueError('operating_recorded_trade_price_missing')
                ws = dict(curr=max(tick_values)[1], best_bid=bid, best_ask=ask,
                    best_bid_qty=row['best_bid_qty'], best_ask_qty=row['best_ask_qty'],
                    last_ws_update_ts=parsed.timestamp(), last_realtime_type_ts={'0D':parsed.timestamp()},quote_stale=False)
            micro_frame = row.get('micro_estimator_state')
            if micro_store is not None:
                micro_store.update_from_ws_quote(seed['stock_code'], ws, now_ts=parsed.timestamp(), tier='hot')
                from dataclasses import asdict
                micro_frame = dict(config=asdict(micro_store.config),
                    state=asdict(micro_store._states[seed['stock_code']]))
            frames.append(dict(source_event_id='entry-frame-' + owner.digest(row),
                source_observation_id=episode, scale_in_decision_id=episode,
                position_episode_id=episode, stock_code=seed['stock_code'], venue=seed['effective_venue'],
                exit_policy_version=context['exit_policy_version'],
                replay_frame_schema='avg_down_exit_replay_frame_v1', sequence=len(frames) + 1,
                emitted_at=parsed.isoformat(), market=dict(best_bid=bid, best_ask=ask,
                    best_bid_qty=row['best_bid_qty'], best_ask_qty=row['best_ask_qty'],
                    source_quality='fresh_conflict_free', ws_data=copy.deepcopy(ws),
                    micro_estimator_state=micro_frame,
                    market_regime=row.get('market_regime'),market_regime_observed_at=row.get('market_regime_observed_at'),
                    recorded_inputs=row.get('recorded_inputs', {})),
                full_policy_decisions=row.get('full_policy_decisions', {}), external_results=row.get('external_results', {})))
        exit_result = (executor or adapter.isolated_replay)(observation, frames)
        if exit_result.get('evidence_digest') != owner.digest({k: v for k, v in exit_result.items() if k != 'evidence_digest'}):
            raise ValueError('operating_full_policy_result_digest_invalid')
        outcome = (exit_result.get('outcomes') or {}).get('ENTRY') or {}
        if (exit_result.get('state') != 'paired_exit_complete_source_only' or exit_result.get('blockers')
            or exit_result.get('actual_order_submitted') is not False or exit_result.get('broker_order_forbidden') is not True
            or outcome.get('status') != 'COMPLETED' or outcome.get('full_policy_evaluation') is not True
            or outcome.get('exit_qty') != qty):
            result['status'] = 'terminal_pending' if 'pending_exit_outcome' in str(exit_result.get('blockers')) else 'unsupported_scope'
            result['blocker'] = 'operating_full_policy_incomplete:' + str(exit_result.get('blockers') or exit_result.get('adapter_error'))
            return {**result, 'sha256': economics_digest(result)}
        terminal = _timestamp(outcome['exit_time'], seed['source_date']).timestamp()
        if terminal <= last_at or not _finite(outcome.get('exit_price'), positive=True):
            raise ValueError('operating_exit_clock_or_price_invalid')
        net = calculate_net_realized_pnl(round(weighted, 4), outcome['exit_price'], qty, cost_rate=context['cost_rate'])
        if net != outcome.get('net_pnl_krw'):
            raise ValueError('operating_cost_owner_result_mismatch')
        stress = calculate_net_realized_pnl(round(weighted, 4), outcome['exit_price'], qty,
            cost_rate=context['cost_rate'] + context['stress_cost_rate_increment'])
        holding = sum(x['qty'] * x['price'] * (terminal - _timestamp(x['at'], seed['source_date']).timestamp()) / 60 for x in fills)
        # Reserve each child until fill or its frozen TTL, then use holding capital.
        ttl = started + context['order_bundle_hard_ttl_sec']
        reserved=0.; outstanding=reserve; reserve_clock=started
        for fill in sorted(fills,key=lambda x:x['at']):
            at=_timestamp(fill['at'],seed['source_date']).timestamp()
            reserved+=outstanding*max(0.,min(at,ttl)-reserve_clock)/60
            outstanding-=fill['qty']*fill.get('reserved_price',fill['price'])
            if outstanding < -1e-8:raise ValueError('operating_reserve_conservation_invalid')
            reserve_clock=at
        reserved+=max(0.,outstanding)*max(0.,ttl-reserve_clock)/60
        result.update(status='completed_source_only', net_pnl_krw=net, stress_net_pnl_krw=stress,
            net_return_pct=net / context['budget_krw'] * 100,
            stress_net_return_pct=stress / context['budget_krw'] * 100,
            modeled_entry_at=datetime.fromtimestamp(first_at, KST).isoformat(),
            capital_krw_minutes=holding, reserve_krw_minutes=reserved,
            modeled_entry_notional_krw=amount, modeled_exit_at=outcome['exit_time'],
            terminal_evidence_sha256=exit_result['evidence_digest'], modeled_outcome='operating_terminal')
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        result['blocker'] = str(exc)
    return {**result, 'sha256': economics_digest(result)}

def entry_split_actual_economic_receipt(stock, *, buy_price, buy_qty, profit_rate, completion_at):
    """Observe the existing completed sell receipt; missing fields remain null."""
    from src.engine.scalping import entry_split_order_plan as split
    from src.engine.trade_profit import get_trade_cost_rate
    seed=stock.get('entry_split_initial_entry_seed') or {}
    if not _entry_seed_valid(seed) or not seed.get('operating_contract'):
        return None
    context=seed['operating_contract']
    completion_at=completion_at.replace(tzinfo=KST) if completion_at.tzinfo is None else completion_at.astimezone(KST)
    cost_version='trade_profit_net_realized_pnl:rate=' + str(get_trade_cost_rate())
    qty=int(buy_qty) if _finite(buy_qty,positive=True) and int(buy_qty)==buy_qty else None
    net=stock.get('realized_pnl_krw')
    complete=(stock.get('sell_execution_receipt_economics_complete') is True
        and stock.get('sell_execution_receipt_quantity_contract_complete') is True
        and _finite(net) and _finite(profit_rate) and qty is not None and 0<qty<=seed['total_qty']
        and stock.get('entry_split_initial_entry_lineage_conflict') is not True
        and cost_version==context['cost_policy_version'])
    decision=context.get('entry_decision_version_receipt') or {}
    decision_valid=(decision.get('sha256')==split._canonical_sha256({k:v for k,v in decision.items() if k!='sha256'})
        and decision.get('machine_bundle_sha256')==seed['policy_bundle_sha256']
        and decision.get('evaluation_attempt_id')==seed['evaluation_attempt_id']
        and all(decision.get(k) for k in ('machine_policy_version','compact_prompt_version','decision_trace_id','runtime_pid')))
    value=dict(episode_id=str(stock.get('position_episode_id') or seed['plan_sha256']),
        plan_sha256=seed['plan_sha256'],source_date=seed['source_date'],
        completion_date=completion_at.astimezone(KST).date().isoformat(),completed_at=completion_at.isoformat(),
        status='COMPLETED',origin='real',owner='main_scalping',
        scope_sha256=split._entry_operating_scope(seed),entry_qty=qty,
        requested_qty=seed['total_qty'],actual_entry_vwap=buy_price,profit_rate=profit_rate if _finite(profit_rate) else None,
        net_pnl_krw=net if _finite(net) else None,cost_complete=complete,exact_lineage=complete,
        cost_policy_version=cost_version,cost_provenance='completed_sell_execution_receipt_trade_profit_configuration',
        budget_krw=context['budget_krw'],capital_krw_minutes=None,reserve_krw_minutes=None,
        entry_decision_version_receipt=decision if decision_valid else None,
        entry_decision_pid_consumed=bool(decision_valid),
        entry_decision_version_blocker=None if decision_valid else 'exact_submit_decision_version_receipt_missing_or_invalid',
        policy_version=stock.get('entry_split_order_policy_version'),
        policy_sha256=stock.get('entry_split_order_policy_sha256'),
        policy_applied=stock.get('entry_split_order_policy_applied') is True,
        runtime_pid=stock.get('entry_split_order_runtime_pid'),
        pid_consumed=stock.get('entry_split_order_runtime_consumed') is True,
        fill_class='full' if qty==seed['total_qty'] else 'partial',
        cost_settlement_reconciled=stock.get('broker_cost_settlement_reconciled') is True,
        blocker=None if complete else 'completed_initial_inventory_cost_or_lineage_unproven')
    return {**value,'sha256':split._canonical_sha256(value)}
