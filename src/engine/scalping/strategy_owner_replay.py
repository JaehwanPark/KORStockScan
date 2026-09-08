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
            quote_ts = ws_data.get("last_ws_update_ts")
            age = now_ts - quote_ts if _finite(quote_ts) else None
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
