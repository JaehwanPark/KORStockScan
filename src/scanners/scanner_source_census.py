"""Bounded scanner adapter/pool telemetry; never a selection or request owner.

Owned by the scanner package because it observes its existing source adapters.
These receipts do not claim visibility into rows already filtered inside an API
adapter. Unknown physical routes remain unknown rather than clock-inferred.
"""

import hashlib
import json
import re
import time
from contextvars import ContextVar
from functools import wraps

from src.engine.sniper_time import scalping_session_venue_provenance
from src.utils.pipeline_event_logger import emit_pipeline_event

_cycle = ContextVar("scanner_source_census_cycle", default="")
MAX_ROWS = 1024
AUTHORITY = "scanner_adapter_pool_observation_only"
MARKET_DATA_ROUTES = {
    "krx_only",
    "nxt_only",
    "krx_nxt_integrated",
    "unknown",
}


def source_cycle_id():
    return _cycle.get()


def source_target_venue(code, request_venue="UNKNOWN"):
    """Contradictory suffix/request evidence is unknown, never a route override."""
    code = str(code or "")
    if code.endswith("_AL"):
        return "UNKNOWN"
    if code.endswith("_NX"):
        return "UNKNOWN" if request_venue == "KRX" else "NXT"
    return request_venue if request_venue in {"KRX", "NXT"} else "UNKNOWN"


def source_target_market_data_route(code, request_route="unknown"):
    """Preserve the requested data route; suffix conflicts fail closed."""
    code = str(code or "")
    request_route = str(request_route or "unknown")
    if request_route not in MARKET_DATA_ROUTES:
        return "unknown"
    if code.endswith("_AL"):
        return (
            "krx_nxt_integrated"
            if request_route == "krx_nxt_integrated"
            else "unknown"
        )
    if code.endswith("_NX"):
        return "nxt_only" if request_route == "nxt_only" else "unknown"
    return request_route


def _best_effort(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return False

    return wrapped


def observe_cycle(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        token = _cycle.set(f"SCANSRC-{time.time_ns()}")
        try:
            return fn(*args, **kwargs)
        finally:
            _cycle.reset(token)

    return wrapped


def _emit(stage, rows, *, source, status, total, rejected, generation=""):
    """Telemetry exceptions must not alter scanner return values or guards."""
    selected = rows[:MAX_ROWS]
    payload = json.dumps(selected, sort_keys=True, separators=(",", ":"))
    fields = {
        **scalping_session_venue_provenance(),
        "metric_role": "funnel_count",
        "decision_authority": AUTHORITY,
        "window_policy": "same_source_cycle_and_exact_route",
        "sample_floor": "one_adapter_or_pool_receipt",
        "primary_decision_metric": "scanner_source_output_count",
        "source_quality_gate": "bounded_hashed_rows_and_conservation",
        "forbidden_uses": "standalone_buy,live_apply,guard_relaxation,raw_api_universe_claim",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "scanner_source_cycle_id": _cycle.get() or generation or "unbound",
        "scanner_scan_generation_id": generation,
        "scanner_source_name": source,
        "scanner_source_status": status,
        "scanner_source_input_count": total,
        "scanner_source_output_count": len(rows),
        "scanner_source_rejected_count": rejected,
        "scanner_source_omitted_count": max(0, len(rows) - len(selected)),
        "scanner_source_rows_json": payload,
        "scanner_source_rows_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "scanner_source_scope": "adapter_return_not_raw_api_universe",
    }
    try:
        receipt = emit_pipeline_event(
            "ENTRY_PIPELINE", "scanner_source_census", "", stage, fields=fields
        )
    except Exception:
        # The missing receipt is detectable by consumers, not a trading veto.
        return False
    return (
        not isinstance(receipt, dict)
        or receipt.get("structured_append_succeeded") is True
    )


@_best_effort
def observe_fetch(
    source,
    targets,
    *,
    status,
    request_venue="UNKNOWN",
    request_route="unknown",
):
    rows = []
    rejected = 0
    for target in targets:
        if not isinstance(target, dict):
            rejected += 1
            continue
        code = str(target.get("Code") or target.get("code") or "")
        match = re.fullmatch(r"(\d{6})(?:_(AL|NX))?", code)
        if not match:
            rejected += 1
            continue
        venue = source_target_venue(code, request_venue)
        rows.append(
            {
                "stock_code": match.group(1),
                "venue": venue,
                "market_data_route": source_target_market_data_route(
                    code, request_route
                ),
            }
        )
    return _emit(
        "scalping_scanner_source_fetch_census",
        rows,
        source=source,
        status=status,
        total=len(targets),
        rejected=rejected,
    )


@_best_effort
def observe_pool(targets, *, generation):
    rows = []
    rejected = 0
    for rank, target in enumerate(targets, 1):
        if not isinstance(target, dict):
            rejected += 1
            continue
        code = str(target.get("Code") or "")
        if re.fullmatch(r"\d{6}", code) is None:
            rejected += 1
            continue
        suffix = str(target.get("MarketSuffix") or "")
        venue = "NXT" if suffix in {"NX", "_NX"} else "UNKNOWN"
        proven_venues = set(target.get("ScannerSourceVenues") or []) & {"KRX", "NXT"}
        if venue == "NXT" and "KRX" in proven_venues:
            venue = "UNKNOWN"
        elif len(proven_venues) == 1:
            venue = next(iter(proven_venues))
        proven_routes = sorted(
            set(target.get("ScannerSourceRoutes") or []) & MARKET_DATA_ROUTES
        )
        # A strategy's clock-derived venue is not quote-route evidence.
        rows.append(
            {
                "stock_code": code,
                "venue": venue,
                "market_data_routes": proven_routes,
                "rank": rank,
                "sources": sorted(target.get("SourceSet") or []),
            }
        )
    return _emit(
        "scalping_scanner_candidate_pool_census",
        rows,
        source="ranked_candidate_pool",
        status=(
            "returned" if rows else "rejected_pool_rows" if rejected else "empty_pool"
        ),
        total=len(targets),
        rejected=rejected,
        generation=generation,
    )


def decode_receipt(fields):
    """Consumer validation accepts logger string booleans, never unknown values."""
    try:
        if (
            not fields.get("scanner_source_cycle_id")
            or fields.get("scanner_source_cycle_id") == "unbound"
        ):
            return None
        if fields.get("decision_authority") != AUTHORITY or any(
            str(fields.get(k)).lower() != expected
            for k, expected in (
                ("runtime_effect", "false"),
                ("allowed_runtime_apply", "false"),
                ("actual_order_submitted", "false"),
                ("broker_order_forbidden", "true"),
            )
        ):
            return None
        payload = fields["scanner_source_rows_json"]
        if (
            hashlib.sha256(payload.encode()).hexdigest()
            != fields["scanner_source_rows_sha256"]
        ):
            return None
        rows = json.loads(payload)
        count_text = [
            str(fields[f"scanner_source_{k}_count"])
            for k in ("input", "output", "rejected", "omitted")
        ]
        if any(re.fullmatch(r"[0-9]+", value) is None for value in count_text):
            return None
        total, output, rejected, omitted = (int(value) for value in count_text)
        if (
            min(total, output, rejected, omitted) < 0
            or total != output + rejected
            or output != len(rows) + omitted
            or not isinstance(rows, list)
            or len(rows) > MAX_ROWS
        ):
            return None
        if any(
            not isinstance(r, dict)
            or not re.fullmatch(r"\d{6}", str(r.get("stock_code") or ""))
            or r.get("venue") not in {"KRX", "NXT", "UNKNOWN"}
            or (
                "market_data_route" in r
                and r.get("market_data_route") not in MARKET_DATA_ROUTES
            )
            or (
                "market_data_routes" in r
                and (
                    not isinstance(r.get("market_data_routes"), list)
                    or any(
                        route not in MARKET_DATA_ROUTES
                        for route in r.get("market_data_routes")
                    )
                )
            )
            for r in rows
        ):
            return None
        return rows
    except (ValueError, TypeError, KeyError, AttributeError):
        return None
