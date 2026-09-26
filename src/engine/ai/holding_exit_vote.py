"""Position-bound holding AI votes about permission for an existing exit signal.

The ledger and snapshot are evidence only.  A vote cannot create an exit, an
order, or scale-in authority.  Runtime selection requires a separately reviewed
policy and signal consumer.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import fcntl
from pathlib import Path
from typing import Any


SCHEMA = "holding_exit_vote_v1"
PURPOSE = "EXIT_PERMISSION"
VERDICTS = frozenset({"PASS", "VETO"})
CONVICTIONS = frozenset({"FIRM", "TENTATIVE"})
MARKETS = frozenset({"PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET"})
MAX_VOTES = 48


def input_snapshot_id(payload: dict[str, Any]) -> str:
    """Hash the exact vote input without treating a mutable cache as evidence."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def normalize_vote_response(
    response: Any,
    *,
    expected_snapshot_id: str,
    position_key: str,
    market: str,
    session_key: str,
    model: str,
    prompt_version: str,
    route: str,
    transport_epoch: str,
    source_generation: str,
    requested_at: float,
    received_at: float,
) -> dict[str, Any]:
    """Accept only a fresh, exact, unambiguous provider verdict."""
    base = {
        "schema": SCHEMA,
        "purpose": PURPOSE,
        "position_key": str(position_key or ""),
        "market": str(market or ""),
        "session_key": str(session_key or ""),
        "model": str(model or ""),
        "prompt_version": str(prompt_version or ""),
        "route": str(route or ""),
        "transport_epoch": str(transport_epoch or ""),
        "source_generation": str(source_generation or ""),
        "input_snapshot_id": str(expected_snapshot_id or ""),
        "requested_at": requested_at,
        "received_at": received_at,
        "verdict": None,
        "conviction": None,
        "reason_codes": [],
        "status": "INSUFFICIENT",
        "excluded_reason": "invalid_response",
    }
    if not isinstance(response, dict):
        return base
    if not base["input_snapshot_id"]:
        return {**base, "excluded_reason": "snapshot_missing"}
    if response.get("ai_parse_fail") or response.get("error") or response.get(
        "ai_fallback_score_50"
    ):
        return {**base, "excluded_reason": "provider_or_parse_failure"}
    forbidden = {"score", "confidence", "action", "quantity", "order_price"}
    if forbidden.intersection(response):
        return {**base, "excluded_reason": "legacy_or_order_field"}
    verdict = response.get("verdict")
    conviction = response.get("conviction")
    reasons = response.get("reason_codes")
    if verdict not in VERDICTS or conviction not in CONVICTIONS:
        return {**base, "excluded_reason": "invalid_verdict_or_conviction"}
    if response.get("input_snapshot_id") != expected_snapshot_id:
        return {**base, "excluded_reason": "snapshot_mismatch"}
    if not isinstance(reasons, list) or not 1 <= len(reasons) <= 6 or any(
        not isinstance(value, str)
        or not value
        or len(value) > 48
        or not value.isascii()
        or not all(char.islower() or char.isdigit() or char == "_" for char in value)
        for value in reasons
    ):
        return {**base, "excluded_reason": "invalid_reason_codes"}
    if (
        not base["position_key"]
        or market not in MARKETS
        or not base["session_key"]
        or not base["model"]
        or not base["prompt_version"]
        or not base["route"]
        or not base["transport_epoch"]
        or not base["source_generation"]
        or isinstance(requested_at, bool)
        or isinstance(received_at, bool)
        or not isinstance(requested_at, (int, float))
        or not isinstance(received_at, (int, float))
        or not math.isfinite(requested_at)
        or not math.isfinite(received_at)
        or received_at < requested_at
    ):
        return {**base, "excluded_reason": "missing_or_invalid_provenance"}
    if response.get("cache_hit") is True or response.get("provider_called") is False:
        return {**base, "excluded_reason": "cached_or_not_called"}
    return {
        **base,
        "verdict": verdict,
        "conviction": conviction,
        "reason_codes": reasons,
        "status": "VALID",
        "excluded_reason": None,
    }


def append_vote(ledger: Any, vote: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """Deduplicate by independent source snapshot within one position generation."""
    existing = [item for item in (ledger or []) if isinstance(item, dict)]
    if vote.get("status") != "VALID" or vote.get("purpose") != PURPOSE:
        return existing[-MAX_VOTES:], "insufficient_not_appended"
    generation = tuple(vote.get(key) for key in (
        "position_key", "market", "session_key", "model", "prompt_version"
    ))
    current = [item for item in existing if tuple(item.get(key) for key in (
        "position_key", "market", "session_key", "model", "prompt_version"
    )) == generation]
    identity = (vote.get("route"), vote.get("transport_epoch"), vote.get("source_generation"))
    if any(
        (item.get("route"), item.get("transport_epoch"), item.get("source_generation"))
        == identity for item in current
    ):
        return current[-MAX_VOTES:], "duplicate_snapshot"
    if current and float(vote["requested_at"]) < max(
        float(item.get("requested_at") or 0.0) for item in current
    ):
        return current[-MAX_VOTES:], "out_of_order"
    return (current + [vote])[-MAX_VOTES:], "appended"


def vote_store_path(data_dir: str | Path, position_key: str) -> Path:
    """Keep one bounded-identity evidence file per position."""
    identity = hashlib.sha256(str(position_key or "").encode("utf-8")).hexdigest()
    return Path(data_dir) / "runtime" / "holding_exit_votes" / f"{identity}.jsonl"


def _read_votes(handle, position_key: str) -> list[dict[str, Any]]:
    handle.seek(0)
    votes = []
    for line in handle:
        try:
            item = json.loads(line)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("vote_store_json_corrupt") from exc
        if (
            not isinstance(item, dict)
            or item.get("schema") != SCHEMA
            or item.get("purpose") != PURPOSE
            or item.get("position_key") != position_key
            or item.get("status") != "VALID"
        ):
            raise ValueError("vote_store_contract_corrupt")
        votes.append(item)
    return votes[-MAX_VOTES:]


def load_votes_file(path: Path, position_key: str) -> list[dict[str, Any]]:
    """Hydrate prior votes after a process restart; malformed rows stay excluded."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return []
    with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            return _read_votes(handle, position_key)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_vote_file(
    path: Path, position_key: str, vote: dict[str, Any]
) -> tuple[list[dict[str, Any]], str]:
    """Atomically deduplicate and durably append one valid vote."""
    if vote.get("position_key") != position_key:
        return [], "position_mismatch"
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    with os.fdopen(descriptor, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            existing = _read_votes(handle, position_key)
            current, status = append_vote(existing, vote)
            if status == "appended":
                handle.seek(0, os.SEEK_END)
                handle.write(json.dumps(vote, sort_keys=True, ensure_ascii=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            return current, status
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def signal_snapshot(
    ledger: Any,
    *,
    position_key: str,
    market: str,
    session_key: str,
    model: str,
    prompt_version: str,
    signal_at: float,
    window_sec: float,
) -> dict[str, Any]:
    """Freeze counts available before an exit signal; never decide an order."""
    eligible = [
        item for item in (ledger or [])
        if isinstance(item, dict)
        and item.get("status") == "VALID"
        and item.get("purpose") == PURPOSE
        and item.get("position_key") == position_key
        and item.get("market") == market
        and item.get("session_key") == session_key
        and item.get("model") == model
        and item.get("prompt_version") == prompt_version
        and isinstance(item.get("received_at"), (float, int))
        and signal_at - max(0.0, window_sec) <= item["received_at"] < signal_at
    ]
    independent = {}
    for item in eligible:
        identity = (
            item.get("route"), item.get("transport_epoch"),
            item.get("source_generation"),
        )
        if all(identity):
            independent.setdefault(identity, item)
    eligible = list(independent.values())
    return {
        "schema": "holding_exit_vote_signal_snapshot_v1",
        "purpose": PURPOSE,
        "position_key": position_key,
        "market": market,
        "session_key": session_key,
        "signal_at": signal_at,
        "window_sec": max(0.0, window_sec),
        "vote_count": len(eligible),
        "pass_count": sum(item["verdict"] == "PASS" for item in eligible),
        "veto_count": sum(item["verdict"] == "VETO" for item in eligible),
        "firm_pass_count": sum(
            item["verdict"] == "PASS" and item["conviction"] == "FIRM"
            for item in eligible
        ),
        "firm_veto_count": sum(
            item["verdict"] == "VETO" and item["conviction"] == "FIRM"
            for item in eligible
        ),
        "latest_vote_age_sec": (
            signal_at - max(item["received_at"] for item in eligible)
            if eligible else None
        ),
        "decision_authority": "observation_only",
    }


def research_decision(
    snapshot: dict[str, Any], *, min_votes: int, pass_votes: int,
    veto_votes: int, firm_veto_votes: int, max_latest_age_sec: float,
) -> dict[str, Any]:
    """Compare an explicit candidate counting rule; never grant runtime authority."""
    result = {
        "purpose": PURPOSE,
        "verdict": "INSUFFICIENT",
        "reason": "candidate_invalid",
        "decision_authority": "offline_research_only",
    }
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("schema") != "holding_exit_vote_signal_snapshot_v1"
        or snapshot.get("purpose") != PURPOSE
        or any(isinstance(value, bool) or not isinstance(value, int) or value < 1
               for value in (min_votes, pass_votes, veto_votes, firm_veto_votes))
        or not isinstance(max_latest_age_sec, (int, float))
        or isinstance(max_latest_age_sec, bool)
        or not math.isfinite(max_latest_age_sec)
        or max_latest_age_sec <= 0
    ):
        return result
    counts = tuple(snapshot.get(key) for key in (
        "vote_count", "pass_count", "veto_count", "firm_veto_count"
    ))
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0
           for value in counts):
        return result
    total, passes, vetoes, firm_vetoes = counts
    age = snapshot.get("latest_vote_age_sec")
    if total != passes + vetoes or firm_vetoes > vetoes:
        return result
    if (
        total < min_votes
        or isinstance(age, bool)
        or not isinstance(age, (int, float))
        or not math.isfinite(age)
        or not 0 <= age <= max_latest_age_sec
    ):
        return {**result, "reason": "quorum_or_freshness_missing"}
    if vetoes >= veto_votes and firm_vetoes >= firm_veto_votes and vetoes > passes:
        return {**result, "verdict": "VETO", "reason": "veto_count_and_strength"}
    if passes >= pass_votes and passes > vetoes:
        return {**result, "verdict": "PASS", "reason": "pass_count_majority"}
    return {**result, "reason": "vote_conflict_or_no_majority"}


# The v1 receipt above remains readable as historical observation. Runtime
# decisions use a separate ledger so old exit-only votes cannot gain authority.
PATH_SCHEMA = "holding_path_vote_v10"
PATH_SNAPSHOT_SCHEMA = "holding_path_vote_signal_v10"
PATH_IDS = frozenset({
    "EXIT_TRAILING_TP", "EXIT_SOFT_STOP", "EXIT_POST_ADD_FAIL",
    "EXIT_BAD_ENTRY_REFINED", "ADD_REBOUND",
})
PATH_REASON_PREFIX = {
    "EXIT_TRAILING_TP": "exit_tp_",
    "EXIT_SOFT_STOP": "exit_soft_",
    "EXIT_POST_ADD_FAIL": "exit_post_add_",
    "EXIT_BAD_ENTRY_REFINED": "exit_bad_entry_",
    "ADD_REBOUND": "add_rebound_",
}
PATH_PROMPT_VERSION = "holding_path_vote_v10"
PATH_MAX_EVENTS = 192
PATH_MAX_STORE_BYTES = 16 * 1024 * 1024


def build_path_vote_input(
    *, stock_code: str, ws_data: dict[str, Any], recent_ticks: list,
    recent_candles: list, position_ctx: dict[str, Any],
    requested_paths: tuple[str, ...], market: str, session_key: str,
    position_key: str, buy_fill_identity: str, route: str,
    transport_epoch: str, source_generation: str,
    quote_observed_at: float, holding_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project exactly the point-in-time fields sent to the path voter."""
    from src.engine.scalping.ai_market_snapshot import ai_input_preflight
    from src.engine.scalping.holding_decision_context import (
        holding_decision_context_model_payload,
    )

    paths = tuple(requested_paths)
    if not paths or len(set(paths)) != len(paths) or set(paths) - PATH_IDS:
        raise ValueError("invalid_holding_vote_paths")
    ws = ws_data if isinstance(ws_data, dict) else {}
    position = position_ctx if isinstance(position_ctx, dict) else {}
    book = ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
    bids = book.get("bids") if isinstance(book.get("bids"), list) else []
    asks = book.get("asks") if isinstance(book.get("asks"), list) else []

    def top_price(levels: list) -> int | None:
        if not levels or not isinstance(levels[0], dict):
            return None
        try:
            price = int(float(levels[0].get("price")))
            return price if price > 0 else None
        except (TypeError, ValueError, OverflowError):
            return None

    preflight = ai_input_preflight(holding_context)
    return {
        "input_schema": PATH_PROMPT_VERSION,
        "requested_paths": list(paths),
        "stock_code": str(stock_code or ""), "market": str(market or ""),
        "session_key": str(session_key or ""),
        "position_key": str(position_key or ""),
        "buy_fill_identity": str(buy_fill_identity or ""),
        "position": {key: position.get(key) for key in (
            "buy_price", "curr_price", "profit_rate", "peak_profit",
            "drawdown_from_peak_pct", "held_sec", "reversal_add_state",
            "reversal_add_executed_at")},
        "quote": {
            "best_bid": top_price(bids), "best_ask": top_price(asks),
            "bid_total_depth": ws.get("bid_tot"),
            "ask_total_depth": ws.get("ask_tot"),
        },
        "last_ticks": [dict(tick) for tick in list(recent_ticks or [])[-10:]
                       if isinstance(tick, dict)],
        "last_candles": [dict(candle) for candle in list(recent_candles or [])[-20:]
                         if isinstance(candle, dict)],
        "flow": holding_decision_context_model_payload(holding_context)
                if isinstance(holding_context, dict) else {},
        "source_quality": {"allowed": preflight.get("allowed") is True,
                           "status": preflight.get("status"),
                           "blockers": preflight.get("blockers")},
        "source": {"route": str(route or ""),
                   "transport_epoch": str(transport_epoch or ""),
                   "source_generation": str(source_generation or ""),
                   "quote_observed_at": quote_observed_at},
    }


def path_vote_input_gaps(payload: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Name missing decision evidence separately for every requested path."""
    position = payload.get("position") or {}
    quote = payload.get("quote") or {}
    flow = payload.get("flow") or {}

    def positive(value: Any) -> bool:
        try:
            return not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0
        except (TypeError, ValueError, OverflowError):
            return False

    def finite(value: Any) -> bool:
        try:
            return not isinstance(value, bool) and math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            return False

    common = []
    if (payload.get("source_quality") or {}).get("allowed") is not True:
        common.append("source_preflight_blocked")
    if not positive(position.get("buy_price")) or not positive(position.get("curr_price")):
        common.append("position_price_missing")
    if not all(finite(position.get(key)) for key in ("profit_rate", "peak_profit", "held_sec")):
        common.append("position_pnl_or_age_missing")
    elif (float(position["held_sec"]) < 0
          or float(position["peak_profit"]) < float(position["profit_rate"])):
        common.append("position_pnl_or_age_inconsistent")
    bid, ask = quote.get("best_bid"), quote.get("best_ask")
    if not positive(bid) or not positive(ask) or float(ask) < float(bid):
        common.append("executable_quote_missing_or_crossed")
    if (not positive(quote.get("bid_total_depth"))
            or not positive(quote.get("ask_total_depth"))):
        common.append("orderbook_depth_missing")
    flow_micro = flow.get("microstructure") if isinstance(flow, dict) else None
    if isinstance(flow_micro, dict):
        for key in ("best_bid", "best_ask"):
            feature_value = flow_micro.get(key)
            if (feature_value is not None and finite(feature_value)
                    and finite(quote.get(key))
                    and float(feature_value) != float(quote[key])):
                common.append("quote_flow_price_conflict")
                break
    if not payload.get("last_ticks"):
        common.append("recent_tape_missing")
    if not isinstance(flow, dict) or not flow:
        common.append("holding_flow_evidence_missing")

    gaps: dict[str, tuple[str, ...]] = {}
    for path in payload.get("requested_paths") or []:
        reasons = list(common)
        if path.startswith("EXIT_") and (
            not positive((flow.get("execution_pnl") or {}).get(
                "executable_sell_price"
            ))
            or not finite((flow.get("execution_pnl") or {}).get(
                "estimated_net_executable_pnl_pct"
            ))
        ):
            reasons.append("executable_exit_pnl_missing")
        elif (path.startswith("EXIT_") and positive(bid)
              and float((flow.get("execution_pnl") or {})[
                  "executable_sell_price"
              ]) != float(bid)):
            reasons.append("executable_exit_bid_conflict")
        if path == "EXIT_TRAILING_TP" and (
            not finite(position.get("drawdown_from_peak_pct"))
            or float(position["drawdown_from_peak_pct"]) < 0
        ):
            reasons.append("peak_drawdown_missing")
        if path == "EXIT_POST_ADD_FAIL" and (
            position.get("reversal_add_state") != "POST_ADD_EVAL"
            or not positive(position.get("reversal_add_executed_at"))
            or not positive((flow.get("position_lifecycle") or {}).get(
                "scale_in_filled_qty"
            ))
        ):
            reasons.append("post_add_fill_evidence_missing")
        if path == "EXIT_BAD_ENTRY_REFINED" and not any(
            (flow.get("position_lifecycle") or {}).get(key) is not None
            for key in ("never_green", "mae_pct")
        ):
            reasons.append("bad_entry_lifecycle_missing")
        if path == "ADD_REBOUND":
            if not payload.get("last_candles"):
                reasons.append("rebound_candle_evidence_missing")
            if (not isinstance(flow.get("signed_tape"), dict)
                    or not isinstance(flow.get("microstructure"), dict)):
                reasons.append("rebound_tape_or_quote_flow_missing")
        gaps[path] = tuple(reasons)
    return gaps


def path_vote_input_hashes(payload: dict[str, Any], *,
                           model: str, prompt_sha256: str | None = None,
                           path_policy_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    """Keep volatile receipt clocks out of the decision-content hash."""
    if prompt_sha256 is None:
        from src.engine.ai_prompt_contracts import (
            SCALPING_HOLDING_PATH_VOTE_SYSTEM_PROMPT,
        )
        prompt_sha256 = hashlib.sha256(
            SCALPING_HOLDING_PATH_VOTE_SYSTEM_PROMPT.encode("ascii")
        ).hexdigest()
    material = {key: value for key, value in payload.items()
                if key not in {"input_snapshot_id", "source", "requested_paths"}}
    # The model receives full provenance, but capture clocks and source ages
    # cannot manufacture a new market observation for vote independence.
    flow = material.get("flow")
    if isinstance(flow, dict):
        flow = dict(flow)
        flow.pop("ai_market_snapshot_v1", None)
        for group, volatile_fields in (
            ("signed_tape", ("age_ms",)),
            ("microstructure", ("quote_age_ms", "ofi_snapshot_age_ms")),
        ):
            if isinstance(flow.get(group), dict):
                flow[group] = {key: value for key, value in flow[group].items()
                               if key not in volatile_fields}
        material["flow"] = flow
    source = payload.get("source") or {}
    material["source_route"] = source.get("route")
    material["transport_epoch"] = source.get("transport_epoch")
    material["model"] = str(model or "")
    material["prompt_sha256"] = str(prompt_sha256 or "")
    paths = tuple(payload.get("requested_paths") or ())
    if path_policy_hashes is not None and (
            set(path_policy_hashes) != set(paths)
            or any(not isinstance(value, str) or len(value) != 64
                   or any(char not in "0123456789abcdef" for char in value)
                   for value in path_policy_hashes.values())):
        raise ValueError("path_policy_hashes_invalid")
    snapshot_id = input_snapshot_id({
        key: value for key, value in payload.items()
        if key != "input_snapshot_id"
    })
    return {
        "input_snapshot_id": snapshot_id,
        "request_payload_sha256": hashlib.sha256(json.dumps(
            {**payload, "input_snapshot_id": snapshot_id},
            ensure_ascii=True, separators=(",", ":"), default=str,
        ).encode("ascii")).hexdigest(),
        "decision_input_sha256": input_snapshot_id({
            **material, "requested_paths": paths,
            **({"path_policy_hashes": path_policy_hashes}
               if path_policy_hashes is not None else {}),
        }),
        "path_decision_input_sha256": {
            path: input_snapshot_id({**material, "path_id": path,
                                     **({"path_policy_sha256": path_policy_hashes[path]}
                                        if path_policy_hashes is not None else {})})
            for path in paths
        },
    }


def path_vote_claims_path(data_dir: str | Path, position_key: str) -> Path:
    identity = hashlib.sha256(str(position_key or "").encode("utf-8")).hexdigest()
    return Path(data_dir) / "runtime" / "holding_path_votes" / f"{identity}.claims.jsonl"


def _read_path_vote_claim_state(
    handle, position_key: str,
) -> tuple[dict[str, str], dict[str, set[str]]]:
    if os.fstat(handle.fileno()).st_size > PATH_MAX_STORE_BYTES:
        raise ValueError("path_vote_claims_oversize")
    handle.seek(0)
    active: dict[str, list[str]] = {}
    for line in handle:
        try:
            item = json.loads(line)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("path_vote_claims_corrupt") from exc
        if (not isinstance(item, dict)
                or item.get("position_key") != position_key
                or item.get("path_id") not in PATH_IDS
                or item.get("status", "CLAIM") not in {"CLAIM", "RELEASE"}
                or not isinstance(item.get("path_hash"), str)
                or len(item["path_hash"]) != 64):
            raise ValueError("path_vote_claims_invalid")
        if item.get("status", "CLAIM") == "RELEASE":
            stack = active.get(item["path_id"], [])
            if not stack or stack[-1] != item["path_hash"]:
                raise ValueError("path_vote_claim_release_mismatch")
            stack.pop()
        else:
            active.setdefault(item["path_id"], []).append(item["path_hash"])
    return (
        {path_id: stack[-1] for path_id, stack in active.items() if stack},
        {path_id: set(stack) for path_id, stack in active.items() if stack},
    )


def _read_path_vote_claims(handle, position_key: str) -> dict[str, str]:
    return _read_path_vote_claim_state(handle, position_key)[0]


def read_path_vote_input_claims(path: Path, position_key: str) -> dict[str, str]:
    if not path.exists():
        return {}
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            return _read_path_vote_claims(handle, position_key)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_path_vote_input_claim_history(
    path: Path, position_key: str,
) -> dict[str, set[str]]:
    """Return every input claimed for a possible provider call and not released."""
    if not path.exists():
        return {}
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            return _read_path_vote_claim_state(handle, position_key)[1]
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def claim_path_vote_inputs(path: Path, position_key: str,
                           path_hashes: dict[str, str]) -> bool:
    """Durably claim changed inputs before a provider request, including crashes."""
    if (not path_hashes or set(path_hashes) - PATH_IDS
            or any(not isinstance(value, str) or len(value) != 64
                   for value in path_hashes.values())):
        raise ValueError("invalid_path_vote_claim")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            _, claimed_history = _read_path_vote_claim_state(handle, position_key)
            if any(value in claimed_history.get(path_id, set())
                   for path_id, value in path_hashes.items()):
                return False
            records = [
                {"position_key": position_key, "path_id": path_id,
                 "path_hash": value, "status": "CLAIM"}
                for path_id, value in sorted(path_hashes.items())
            ]
            handle.seek(0, os.SEEK_END)
            handle.write("".join(json.dumps(item, sort_keys=True) + "\n"
                                 for item in records))
            handle.flush()
            os.fsync(handle.fileno())
            parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
            return True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def release_path_vote_inputs(path: Path, position_key: str,
                             path_hashes: dict[str, str]) -> bool:
    """Release an exact claim only when no provider call was submitted."""
    fd = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            latest = _read_path_vote_claims(handle, position_key)
            if any(latest.get(path_id) != value
                   for path_id, value in path_hashes.items()):
                return False
            records = [
                {"position_key": position_key, "path_id": path_id,
                 "path_hash": value, "status": "RELEASE"}
                for path_id, value in sorted(path_hashes.items())
            ]
            handle.seek(0, os.SEEK_END)
            handle.write("".join(json.dumps(item, sort_keys=True) + "\n"
                                 for item in records))
            handle.flush()
            os.fsync(handle.fileno())
            return True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
PATH_POLICY_BY_MARKET = {
    (path, market): {
        "min_votes": 2, "pass_votes": 2, "veto_votes": 2,
        "firm_pass_votes": 1 if path == "ADD_REBOUND" else 0,
        "firm_veto_votes": 1,
        "window_sec": 180.0, "max_latest_age_sec": 40.0,
        "max_gap_sec": 100.0, "min_duration_sec": 8.0,
        "max_defer_sec": (
            45.0 if path == "EXIT_TRAILING_TP" else
            10.0 if path == "EXIT_POST_ADD_FAIL" else
            30.0 if path == "EXIT_BAD_ENTRY_REFINED" else 90.0
        ),
    }
    for path in sorted(PATH_IDS)
    for market in sorted(MARKETS)
}


def buy_fill_identity_from_legs(legs: Any) -> str | None:
    """Bind a vote generation to exact broker BUY order/execution identities."""
    if not isinstance(legs, list) or not legs:
        return None
    normalized = []
    seen = set()
    for leg in legs:
        if not isinstance(leg, dict):
            return None
        order = str(leg.get("order_no") or "").strip()
        execution = str(leg.get("execution_no") or "").strip()
        qty = leg.get("qty")
        if (not order or order.startswith("__") or not execution
                or isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0
                or (order, execution) in seen):
            return None
        seen.add((order, execution))
        normalized.append((order, execution, qty))
    return input_snapshot_id(sorted(normalized))


def buy_fill_legs_from_runtime(stock: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Reconcile runtime receipt maps into exact broker BUY fill identities."""
    legs = []
    for prefix in ("entry", "add"):
        fills = stock.get(f"_{prefix}_receipt_filled_by_order_no") or {}
        executions = stock.get(f"_{prefix}_receipt_executions_by_order_no") or {}
        if not isinstance(fills, dict) or not isinstance(executions, dict):
            return None
        if prefix == "entry" and not fills:
            return None
        if set(fills) != set(executions):
            return None
        for order, filled_qty in fills.items():
            if (not isinstance(filled_qty, int) or isinstance(filled_qty, bool)
                    or filled_qty <= 0):
                return None
            order_executions = executions.get(order)
            if not isinstance(order_executions, dict) or not order_executions:
                return None
            ordered = []
            for execution, signature in order_executions.items():
                if not isinstance(signature, dict):
                    return None
                cumulative = signature.get("cumulative_qty")
                if (not isinstance(cumulative, int) or isinstance(cumulative, bool)
                        or cumulative <= 0):
                    return None
                ordered.append((cumulative, str(execution)))
            prior = 0
            for cumulative, execution in sorted(ordered):
                if cumulative <= prior:
                    return None
                legs.append({"order_no": order, "execution_no": execution,
                             "qty": cumulative - prior})
                prior = cumulative
            if prior != filled_qty:
                return None
        declared = stock.get(f"{prefix}_filled_qty")
        if declared is not None and (
                isinstance(declared, bool) or not isinstance(declared, int)
                or declared != sum(fills.values())):
            return None
    return legs if buy_fill_identity_from_legs(legs) else None


def buy_fill_identity_from_runtime(stock: dict[str, Any]) -> str | None:
    return buy_fill_identity_from_legs(buy_fill_legs_from_runtime(stock))


def path_policy_baseline_receipt() -> dict[str, Any]:
    """Bind all live code-default path policies without granting selection."""
    hashes = {
        f"{path}|{market}": input_snapshot_id(policy)
        for (path, market), policy in sorted(PATH_POLICY_BY_MARKET.items())
    }
    return {
        "schema": "holding_path_vote_baseline_receipt_v1",
        "prompt_version": PATH_PROMPT_VERSION,
        "model": "gpt-5.4-nano",
        "policy_hashes": hashes,
        "policy_set_sha256": input_snapshot_id(hashes),
        "selected_policy": None,
        "allowed_runtime_apply": False,
        "decision_authority": "code_default_path_market_baseline_only",
    }


def path_vote_store_path(data_dir: str | Path, position_key: str) -> Path:
    identity = hashlib.sha256(str(position_key or "").encode("utf-8")).hexdigest()
    return Path(data_dir) / "runtime" / "holding_path_votes" / f"{identity}.jsonl"


def normalize_path_vote_bundle(
    response: Any, *, requested_paths: tuple[str, ...],
    expected_snapshot_id: str, position_key: str, market: str,
    session_key: str, model: str, route: str, transport_epoch: str,
    source_generation: str, requested_at: float, received_at: float,
    buy_fill_identity: str | None = None,
    buy_fill_legs: list[dict[str, Any]] | None = None,
    quote_observed_at: float | None = None,
    path_policy_hashes: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Return exactly one isolated event for each requested path and call."""
    paths = tuple(requested_paths)
    if not paths or len(set(paths)) != len(paths) or set(paths) - PATH_IDS:
        raise ValueError("invalid_requested_paths")
    if path_policy_hashes is not None and (
            set(path_policy_hashes) != set(paths)
            or any(not isinstance(value, str) or len(value) != 64
                   for value in path_policy_hashes.values())):
        raise ValueError("invalid_path_policy_hashes")
    common = {
        "schema": PATH_SCHEMA, "position_key": str(position_key or ""),
        "market": market, "session_key": str(session_key or ""),
        "model": str(model or ""), "prompt_version": PATH_PROMPT_VERSION,
        "route": str(route or ""), "transport_epoch": str(transport_epoch or ""),
        "source_generation": str(source_generation or ""),
        "buy_fill_identity": str(buy_fill_identity or ""),
        "buy_fill_legs": list(buy_fill_legs or []),
        "quote_observed_at": quote_observed_at,
        "input_snapshot_id": str(expected_snapshot_id or ""),
        "requested_at": requested_at, "received_at": received_at,
    }
    provenance_ok = (
        bool(common["position_key"] and common["session_key"] and common["model"]
             and common["route"] and common["transport_epoch"]
             and common["source_generation"] and common["input_snapshot_id"]
             and len(common["buy_fill_identity"]) == 64
             and buy_fill_identity_from_legs(common["buy_fill_legs"])
             == common["buy_fill_identity"])
        and market in MARKETS
        and all(isinstance(t, (float, int)) and not isinstance(t, bool)
                and math.isfinite(t) for t in (requested_at, received_at))
        and received_at >= requested_at
        and isinstance(quote_observed_at, (int, float))
        and not isinstance(quote_observed_at, bool)
        and math.isfinite(quote_observed_at)
        and 0 <= requested_at - quote_observed_at <= 3.0
    )
    items = response.get("votes") if isinstance(response, dict) else None
    response_ok = (
        isinstance(items, list)
        and response.get("input_snapshot_id") == expected_snapshot_id
        and not response.get("ai_parse_fail")
        and not response.get("error")
        and not response.get("cache_hit")
        and response.get("provider_called") is not False
        and not ({"score", "confidence", "action", "quantity", "order_price"}
                 & response.keys())
    ) if isinstance(response, dict) else False
    grouped: dict[str, list[dict[str, Any]]] = {path: [] for path in paths}
    if response_ok:
        for item in items:
            if isinstance(item, dict) and item.get("path_id") in grouped:
                grouped[item["path_id"]].append(item)
        if any(not isinstance(item, dict) or item.get("path_id") not in grouped
               for item in items):
            response_ok = False
        if [item.get("path_id") for item in items if isinstance(item, dict)] != list(paths):
            response_ok = False
    events = []
    for path in paths:
        vote = grouped[path][0] if response_ok and len(grouped[path]) == 1 else {}
        reason_codes = vote.get("reason_codes")
        prefix = PATH_REASON_PREFIX[path]
        vote_ok = (
            provenance_ok and response_ok and len(grouped[path]) == 1
            and set(vote) == {"path_id", "verdict", "conviction", "reason_codes"}
            and vote.get("verdict") in VERDICTS
            and vote.get("conviction") in CONVICTIONS
            and isinstance(reason_codes, list) and 1 <= len(reason_codes) <= 6
            and all(isinstance(code, str) and code.startswith(prefix)
                    and 5 <= len(code) <= 64 and code.isascii()
                    and all(ch.islower() or ch.isdigit() or ch == "_" for ch in code)
                    for code in reason_codes)
        )
        model_input_insufficient = bool(
            vote_ok and any(code == prefix + "input_insufficient"
                            for code in reason_codes)
        )
        if model_input_insufficient:
            vote_ok = False
        events.append({
            **common, "path_id": path,
            "path_policy_sha256": input_snapshot_id(
                PATH_POLICY_BY_MARKET[(path, market)]
            ) if path_policy_hashes is None and market in MARKETS else (
                path_policy_hashes or {}).get(path),
            "purpose": "ADD_PERMISSION" if path == "ADD_REBOUND" else "EXIT_PERMISSION",
            "verdict": vote.get("verdict") if vote_ok else None,
            "conviction": vote.get("conviction") if vote_ok else None,
            "reason_codes": reason_codes if vote_ok else [],
            "status": "VALID" if vote_ok else "INSUFFICIENT",
            "excluded_reason": None if vote_ok else (
                "missing_or_invalid_provenance" if not provenance_ok else
                "invalid_bundle" if not response_ok else
                "missing_or_duplicate_path" if len(grouped[path]) != 1 else
                "model_input_insufficient" if model_input_insufficient else
                "invalid_path_vote"
            ),
        })
    return events


def _path_event_identity(event: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(event.get(key) for key in (
        "position_key", "market", "session_key", "path_id", "model",
        "prompt_version", "route", "transport_epoch", "source_generation",
    ))


def append_path_events_file(
    path: Path, position_key: str, events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Append one review cycle atomically, including missing votes as gaps."""
    if not events or any(
        event.get("schema") != PATH_SCHEMA
        or event.get("position_key") != position_key
        or event.get("path_id") not in PATH_IDS
        or (event.get("status") == "VALID" and (
            event.get("provider_called") is not True
            or buy_fill_identity_from_legs(event.get("buy_fill_legs"))
            != event.get("buy_fill_identity")
            or not isinstance(event.get("quote_observed_at"), (int, float))
            or isinstance(event.get("quote_observed_at"), bool)
            or not math.isfinite(event["quote_observed_at"])
            or not 0 <= event["requested_at"] - event["quote_observed_at"] <= 3.0))
        for event in events
    ):
        return [], "invalid_events"
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            prior = _read_path_events(handle, position_key)
            identities = {_path_event_identity(item) for item in prior}
            if any(_path_event_identity(item) in identities for item in events):
                return prior, "duplicate_generation"
            if len({_path_event_identity(item) for item in events}) != len(events):
                return prior, "duplicate_path"
            if prior and min(float(item["requested_at"]) for item in events) < max(
                float(item["requested_at"]) for item in prior
            ):
                return prior, "out_of_order"
            persisted_at = __import__("time").time()
            if any(float(item["received_at"]) > persisted_at for item in events):
                return prior, "future_response"
            to_write = [{**item, "persisted_at": persisted_at} for item in events]
            handle.seek(0, os.SEEK_END)
            handle.write("".join(json.dumps(item, sort_keys=True, ensure_ascii=True) + "\n"
                                 for item in to_write))
            handle.flush()
            os.fsync(handle.fileno())
            return (prior + to_write)[-PATH_MAX_EVENTS:], "appended"
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read_path_events(handle, position_key: str) -> list[dict[str, Any]]:
    if os.fstat(handle.fileno()).st_size > PATH_MAX_STORE_BYTES:
        raise ValueError("path_vote_store_oversize")
    handle.seek(0)
    events = []
    for line in handle:
        try:
            item = json.loads(line)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("path_vote_store_json_corrupt") from exc
        if (not isinstance(item, dict) or item.get("schema") != PATH_SCHEMA
                or item.get("position_key") != position_key
                or item.get("path_id") not in PATH_IDS
                or item.get("status") not in {"VALID", "INSUFFICIENT"}
                or not isinstance(item.get("path_policy_sha256"), str)
                or len(item["path_policy_sha256"]) != 64
                or item.get("purpose") != (
                    "ADD_PERMISSION" if item.get("path_id") == "ADD_REBOUND"
                    else "EXIT_PERMISSION"
                )
                or not isinstance(item.get("buy_fill_identity"), str)
                or item.get("status") == "VALID" and (
                    len(item["buy_fill_identity"]) != 64
                    or buy_fill_identity_from_legs(item.get("buy_fill_legs"))
                    != item["buy_fill_identity"]
                    or not isinstance(item.get("quote_observed_at"), (int, float))
                    or isinstance(item.get("quote_observed_at"), bool)
                    or not math.isfinite(item["quote_observed_at"])
                    or not 0 <= item["requested_at"] - item["quote_observed_at"] <= 3.0)
                or not isinstance(item.get("persisted_at"), (int, float))
                or isinstance(item.get("persisted_at"), bool)
                or not math.isfinite(item["persisted_at"])
                or any(not isinstance(item.get(key), (int, float))
                       or isinstance(item[key], bool)
                       or not math.isfinite(item[key])
                       for key in ("requested_at", "received_at"))
                or item["requested_at"] > item["received_at"]
                or item["received_at"] > item["persisted_at"]
                or (item.get("status") == "VALID" and (
                    item.get("provider_called") is not True
                    or not item.get("input_snapshot_id")
                    or item.get("verdict") not in VERDICTS
                    or item.get("conviction") not in CONVICTIONS
                ))):
            raise ValueError("path_vote_store_contract_corrupt")
        events.append(item)
    return events


def load_path_events_file(path: Path, position_key: str) -> list[dict[str, Any]]:
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return []
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            return _read_path_events(handle, position_key)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_path_policy(policy: Any, *, path_id: str | None = None) -> bool:
    if not isinstance(policy, dict):
        return False
    counts = ("min_votes", "pass_votes", "veto_votes", "firm_pass_votes",
              "firm_veto_votes")
    times = ("window_sec", "max_latest_age_sec", "max_gap_sec",
             "min_duration_sec", "max_defer_sec")
    if set(policy) != set(counts) | set(times):
        return False
    if any(not isinstance(policy.get(key), int) or isinstance(policy[key], bool)
           or policy[key] < (2 if key == "min_votes" else 0) for key in counts):
        return False
    if any(not isinstance(policy.get(key), (int, float))
           or isinstance(policy[key], bool) or not math.isfinite(policy[key])
           or policy[key] < 0 for key in times):
        return False
    defer_limit = 90.0
    if path_id is not None:
        if path_id not in PATH_IDS:
            return False
        defer_limit = PATH_POLICY_BY_MARKET[(path_id, "REGULAR")]["max_defer_sec"]
    return (policy["pass_votes"] >= 2 and policy["veto_votes"] >= 2
            and policy["window_sec"] > 0 and policy["max_latest_age_sec"] > 0
            and policy["max_gap_sec"] > 0
            and 0 < policy["max_defer_sec"] <= defer_limit
            and policy["max_latest_age_sec"] <= policy["window_sec"]
            and policy["min_duration_sec"] <= policy["window_sec"])


def path_signal_snapshot(
    ledger: Any, *, position_key: str, market: str, session_key: str,
    path_id: str, model: str, signal_at: float, policy: dict[str, Any],
    source_policy_sha256: str | None = None,
    buy_fill_identity: str | None = None,
) -> dict[str, Any]:
    """Freeze the last contiguous pre-signal sequence for exactly one path."""
    base = {
        "schema": PATH_SNAPSHOT_SCHEMA, "path_id": path_id,
        "position_key": position_key, "market": market,
        "buy_fill_identity": buy_fill_identity,
        "session_key": session_key, "signal_at": signal_at,
        "vote_count": 0, "pass_count": 0, "veto_count": 0,
        "firm_pass_count": 0, "firm_veto_count": 0,
        "missing_cycle_count": 0, "first_vote_at": None,
        "last_vote_at": None, "latest_vote_age_sec": None,
        "max_observed_gap_sec": None, "duration_sec": 0.0,
        "decision": "INSUFFICIENT", "reason": "invalid_policy_or_identity",
    }
    if (path_id not in PATH_IDS or market not in MARKETS
            or not isinstance(buy_fill_identity, str)
            or len(buy_fill_identity) != 64
            or not validate_path_policy(policy, path_id=path_id)
            or not isinstance(signal_at, (int, float)) or isinstance(signal_at, bool)
            or not math.isfinite(signal_at)):
        return base
    source_hash = source_policy_sha256 or input_snapshot_id(policy)
    if (len(source_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in source_hash)):
        return base
    rows = sorted((item for item in (ledger or [])
        if isinstance(item, dict) and item.get("schema") == PATH_SCHEMA
        and item.get("position_key") == position_key
        and item.get("buy_fill_identity") == buy_fill_identity
        and item.get("market") == market and item.get("session_key") == session_key
        and item.get("path_id") == path_id and item.get("model") == model
        and item.get("purpose") == (
            "ADD_PERMISSION" if path_id == "ADD_REBOUND" else "EXIT_PERMISSION"
        )
        and item.get("prompt_version") == PATH_PROMPT_VERSION
        and item.get("path_policy_sha256") == source_hash
        and isinstance(item.get("requested_at"), (float, int))
        and not isinstance(item.get("requested_at"), bool)
        and math.isfinite(item["requested_at"])
        and isinstance(item.get("persisted_at"), (float, int))
        and not isinstance(item.get("persisted_at"), bool)
        and math.isfinite(item["persisted_at"])
        and item["persisted_at"] < signal_at
        and isinstance(item.get("received_at"), (float, int))
        and not isinstance(item.get("received_at"), bool)
        and math.isfinite(item["received_at"])
        and item["requested_at"] <= item["received_at"] <= item["persisted_at"]
        and signal_at - policy["window_sec"] <= item["requested_at"] < signal_at
        and item["received_at"] < signal_at),
        key=lambda item: (item["requested_at"], item["received_at"]))
    segment = []
    missing = 0
    identities = set()
    for item in rows:
        identity = (item.get("route"), item.get("transport_epoch"),
                    item.get("source_generation"))
        if not all(identity) or identity in identities:
            segment, missing = [], missing + 1
            continue
        identities.add(identity)
        if (item.get("status") != "VALID"
                or item.get("provider_called") is not True
                or not item.get("input_snapshot_id")):
            segment, missing = [], missing + 1
            continue
        if segment and item["requested_at"] - segment[-1]["requested_at"] > policy["max_gap_sec"]:
            segment = []
        segment.append(item)
    if segment:
        first, last = segment[0]["requested_at"], segment[-1]["requested_at"]
        base.update({
            "vote_count": len(segment),
            "pass_count": sum(item["verdict"] == "PASS" for item in segment),
            "veto_count": sum(item["verdict"] == "VETO" for item in segment),
            "firm_pass_count": sum(item["verdict"] == "PASS" and item["conviction"] == "FIRM" for item in segment),
            "firm_veto_count": sum(item["verdict"] == "VETO" and item["conviction"] == "FIRM" for item in segment),
            "first_vote_at": first, "last_vote_at": last,
            "latest_vote_age_sec": signal_at - last,
            "max_observed_gap_sec": max((segment[i]["requested_at"] - segment[i-1]["requested_at"] for i in range(1, len(segment))), default=0.0),
            "duration_sec": last - first,
        })
    base["missing_cycle_count"] = missing
    return decide_path_snapshot(base, policy)


def decide_path_snapshot(snapshot: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    result = {**snapshot, "decision": "INSUFFICIENT", "reason": "quorum_or_freshness_missing"}
    if not validate_path_policy(policy, path_id=snapshot.get("path_id")):
        return {**result, "reason": "invalid_policy"}
    count_keys = ("vote_count", "pass_count", "veto_count",
                  "firm_pass_count", "firm_veto_count")
    if (any(not isinstance(snapshot.get(key), int)
            or isinstance(snapshot[key], bool) or snapshot[key] < 0
            for key in count_keys)
            or snapshot["vote_count"] != snapshot["pass_count"] + snapshot["veto_count"]
            or snapshot["firm_pass_count"] > snapshot["pass_count"]
            or snapshot["firm_veto_count"] > snapshot["veto_count"]):
        return {**result, "reason": "invalid_count_contract"}
    if (snapshot.get("vote_count", 0) < policy["min_votes"]
            or snapshot.get("duration_sec", 0) < policy["min_duration_sec"]
            or snapshot.get("latest_vote_age_sec") is None
            or snapshot["latest_vote_age_sec"] > policy["max_latest_age_sec"]):
        return result
    passes, vetoes = snapshot["pass_count"], snapshot["veto_count"]
    pass_ok = (passes >= policy["pass_votes"] and passes > vetoes
               and snapshot["firm_pass_count"] >= policy["firm_pass_votes"])
    veto_ok = (vetoes >= policy["veto_votes"] and vetoes > passes
               and snapshot["firm_veto_count"] >= policy["firm_veto_votes"])
    if pass_ok == veto_ok:
        return {**result, "reason": "conflict_or_no_majority"}
    return {**result, "decision": "PASS" if pass_ok else "VETO",
            "reason": "sequence_majority_and_strength"}
