"""Explicit production opt-in for the reviewed auxiliary input transformation.

This owner projects existing confirmation-prefix facts and opt-in completed bars.
Registration and activation remain with the native policy/overlay publishers;
the offline research authorization is never an activation credential.
"""

from __future__ import annotations

import copy
import math
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import reversal_registered_catalog as C

VERSION = "auxiliary_confirmation_risk_role_production_v1"
REVIEWED_TRANSFORM_SHA256 = (
    "fa382669def440b084b52929ef833d07362057eb38cc1a3fc961d558a286aac6"
)
MODE = "ROLE_VOCAB_PATH"
CANDLE_VERSION = "auxiliary_completed_candle_risk_production_v2"
CANDLE_FIELD = "completed_candle_risk_source"
CANDLE_FACT = "observed_completed_candle_structure"
CANDLE_RISK = "OBSERVED_COMPLETED_CANDLE_CONCERN"


def contract(scope_ids, *, completed_candles=False):
    from src.engine.scalping import continuous_reversal_policy_v5 as V

    valid = {V.scope_id(key, route) for key, route in V.scopes()}
    if (
        not isinstance(scope_ids, list)
        or not scope_ids
        or any(not isinstance(s, str) for s in scope_ids)
        or scope_ids != sorted(set(scope_ids))
        or not set(scope_ids) <= valid
    ):
        raise ValueError("auxiliary_production_input_scope_invalid")
    if P.file_hash(X.__file__) != REVIEWED_TRANSFORM_SHA256:
        raise ValueError("auxiliary_production_input_transform_changed")
    return dict(
        version=CANDLE_VERSION if completed_candles else VERSION,
        mode=MODE,
        input_version=U.VERSION,
        source_sha256=P.file_hash(__file__),
        transform_sha256=REVIEWED_TRANSFORM_SHA256,
        definition_sha256=X.contract(MODE)["definition_sha256"],
        scope_ids=scope_ids[:],
        source_boundary=(
            "ORIGINAL_PREFIX_AND_COMPLETED_ENTRY_CANDLES"
            if completed_candles
            else "ORIGINAL_CONFIRMATION_PREFIX_ONLY"
        ),
        decision_authority="AUXILIARY_RISK_SCREEN_NO_MACHINE_PROMOTION",
        activation_authority="EXISTING_NATIVE_POLICY_PUBLISHER_ONLY",
    )


def validate(value):
    from src.engine.scalping import reversal_auxiliary_compatibility as C

    if isinstance(value, dict) and value.get("version") == CANDLE_VERSION:
        if value != contract(value.get("scope_ids"), completed_candles=True):
            raise ValueError("auxiliary_completed_candle_contract_changed")
        return value
    if not isinstance(value, dict) or not C.contract_matches(
        value,
        contract(
            value.get("scope_ids"),
            completed_candles=value.get("version") == CANDLE_VERSION,
        ),
        {"source_sha256": __file__, "transform_sha256": X.__file__},
    ):
        raise ValueError("auxiliary_production_input_contract_changed")
    return value


def _scope(logical_input, value):
    validate(value)
    if not isinstance(logical_input, dict) or logical_input.get("schema") != U.VERSION:
        raise ValueError("auxiliary_production_input_version_invalid")
    common = logical_input.get("common_context") or {}
    price = common.get("confirmation_price")
    if (
        not isinstance(common.get("symbol"), str)
        or not re.fullmatch(r"[0-9A-Z]{6}", common["symbol"])
        or common.get("market") not in C.ROUTES
        or type(price) not in (int, float)
        or not math.isfinite(price)
        or price <= 0
    ):
        raise ValueError("auxiliary_production_input_scope_source_invalid")
    key = C.cell_key(
        common.get("symbol"), common.get("market"), common.get("confirmation_price")
    )
    if key + "|" + str(common.get("venue")) not in value["scope_ids"]:
        raise ValueError("auxiliary_production_input_scope_mismatch")


def project(logical_input, *, expected_contract, entry_context=None):
    _scope(logical_input, expected_contract)
    # Call the immutable pure transformation only. Its report-only research
    # flags never enter the registry, request, or policy activation contract.
    result = X.project(logical_input, expected_contract=X.contract(MODE))
    if expected_contract["version"] == CANDLE_VERSION:
        source = completed_candle_source(entry_context, logical_input["common_context"])
        result[CANDLE_FIELD] = source
        if source["status"] == "observed":
            setup = result["entry_setup_evidence_v1"]
            setup["context_facts"].append(
                dict(
                    id=CANDLE_FACT,
                    value={k: v for k, v in source.items() if k != "original_context"},
                    unit="completed_minute_observation",
                )
            )
            setup["risk_fact_bindings"][CANDLE_RISK] = [CANDLE_FACT]
    return result


def validate_projected(logical_input, *, expected_contract):
    """Reject bypassed, doubled or changed derived facts at wire/decode entry.

    Reconstruct the base fact ledger, then reproduce the entire transformed
    input. Numeric values and risk bindings are checked, never just presence.
    """
    _scope(logical_input, expected_contract)
    W.encode(logical_input)
    base = copy.deepcopy(logical_input)
    setup = base["entry_setup_evidence_v1"]
    candle_source = base.pop(CANDLE_FIELD, None)
    if expected_contract["version"] == CANDLE_VERSION:
        # Reproduce derived values from the bounded original producer envelope.
        if not isinstance(candle_source, dict):
            raise ValueError("auxiliary_completed_candle_source_missing")
        original = candle_source.get("original_context")
        # The final full projection comparison below authenticates both the
        # source and derived facts in one pass; do not parse the five bars twice.
        setup["context_facts"] = [
            f for f in setup["context_facts"] if f["id"] != CANDLE_FACT
        ]
        setup["risk_fact_bindings"].pop(CANDLE_RISK, None)
    elif candle_source is not None:
        raise ValueError("auxiliary_completed_candle_unregistered")

    def generated(fid):
        return (
            fid.endswith("/risk_role_observed_spread")
            or "/observed_target_progress_v1/" in fid
        )

    if any(
        generated(f["id"])
        for field in ("positive_facts", "contradicting_facts")
        for f in setup[field]
    ):
        raise ValueError("auxiliary_production_input_fact_role_changed")
    remaining, moved = [], []
    generated_ids = set()
    for fact in setup["context_facts"]:
        if generated(fact["id"]):
            generated_ids.add(fact["id"])
        elif fact["id"].rsplit("/", 1)[-1] in X.SPREAD_NAMES:
            moved.append(fact)
        else:
            remaining.append(fact)
    setup["context_facts"] = remaining
    setup["contradicting_facts"].extend(moved)
    for risk, ids in list(setup["risk_fact_bindings"].items()):
        retained = [fid for fid in ids if fid not in generated_ids]
        if retained:
            setup["risk_fact_bindings"][risk] = retained
        elif any(fid in generated_ids for fid in ids):
            del setup["risk_fact_bindings"][risk]
    if (
        project(
            base,
            expected_contract=expected_contract,
            entry_context=(candle_source or {}).get("original_context"),
        )
        != logical_input
    ):
        raise ValueError("auxiliary_production_input_projection_changed")
    return logical_input


def completed_candle_source(context, common):
    """Bound existing completed bars to the entry source; no I/O or new veto.

    Only five completed observations are projected. Missing/stale/conflicting
    context remains explicit unknown; no synthetic bars or future structure.
    The source item is independent of the policy venue label.
    """
    if context is None:
        return dict(
            status="unavailable",
            reason="entry_candle_context_missing",
            original_context=None,
        )
    if not isinstance(context, dict):
        raise ValueError("auxiliary_completed_candle_context_invalid")
    keys = (
        "schema",
        "request_code",
        "session",
        "rest_route",
        "ws_route",
        "route_equivalence",
        "source_quality",
        "bar_schema",
        "bars",
        "causal_revision",
    )
    bars = context.get("bars")
    if not isinstance(bars, list) or len(bars) > 60:
        raise ValueError("auxiliary_completed_candle_bounds_invalid")
    # Forming rows are never risk facts. Keep their completed predecessors;
    # rejecting a whole payload with a normal live forming bar would recreate
    # permanent missing context during every active minute.
    bars = [
        row
        for row in bars
        if not isinstance(row, dict) or row.get("forming") is not True
    ]
    # Retain only the existing source contract's needed fields and five bars.
    quality = context.get("source_quality")
    if not isinstance(quality, dict):
        quality = {}
    window = quality.get("decision_window")
    if not isinstance(window, dict):
        window = {}
    original = {
        k: copy.deepcopy(context.get(k))
        for k in keys
        if k not in {"bars", "source_quality", "bar_schema"}
    }
    original["bars"] = [
        (
            {
                k: copy.deepcopy(row.get(k))
                for k in ("t", "o", "h", "l", "c", "v", "forming", "partial_volume")
            }
            if isinstance(row, dict)
            else None
        )
        for row in bars[-5:]
    ]
    original["bar_schema"] = {
        k: (context.get("bar_schema") or {}).get(k)
        for k in ("order", "timezone", "interval")
    }
    original["source_quality"] = dict(
        status=quality.get("status"),
        blockers=copy.deepcopy(quality.get("blockers")),
        decision_window={
            k: window.get(k) for k in ("provider_call_allowed", "end_timestamp")
        },
    )
    result = dict(
        status="unavailable",
        reason="entry_candle_source_unverified",
        original_context=original,
    )
    causal = original.get("schema") == "entry_completed_revision_context_v1"
    revision = original.get("causal_revision") or {}
    if causal and (
        not re.fullmatch(r"[0-9a-f]{64}", str(revision.get("revision", "")))
        or not re.fullmatch(r"[0-9a-f]{64}", str(revision.get("rows_sha256", "")))
        or type(revision.get("available_at")) not in (int, float)
        or not math.isfinite(revision["available_at"])
        or revision.get("confirmation_at") != common.get("epoch")
        or not 0 < revision["available_at"] <= revision["confirmation_at"]
    ):
        return result
    if (
        original.get("schema")
        not in {"entry_candle_context_v1", "entry_completed_revision_context_v1"}
        or original.get("request_code") != common.get("source_item")
        or quality.get("status")
        != ("verified_causal_revision" if causal else "fresh_consistent")
        or quality.get("blockers")
        or window.get("provider_call_allowed") is not True
        or (original.get("bar_schema") or {}).get("order") != "oldest_to_latest"
        or (original.get("bar_schema") or {}).get("timezone") != "Asia/Seoul"
        or (original.get("bar_schema") or {}).get("interval") != "1m"
    ):
        return result
    now = common.get("epoch")
    if type(now) not in (int, float) or not math.isfinite(now):
        raise ValueError("auxiliary_completed_candle_clock_invalid")
    zone = ZoneInfo("Asia/Seoul")
    day = datetime.fromtimestamp(now, zone).date().isoformat()
    try:
        end = datetime.fromisoformat(window["end_timestamp"])
    except (KeyError, TypeError, ValueError):
        return result
    if end.tzinfo is None or end.astimezone(zone).date().isoformat() != day:
        return result
    rows = []
    for bar in original["bars"]:
        if not isinstance(bar, dict) or bar.get("forming") is not False:
            return result
        try:
            stamp = datetime.fromisoformat(day + "T" + bar["t"]).replace(tzinfo=zone)
            values = [bar[k] for k in ("o", "h", "l", "c", "v")]
        except (KeyError, TypeError, ValueError):
            return result
        if (
            any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or min(values[:4]) <= 0
            or values[4] < 0
            or not bar["l"]
            <= min(bar["o"], bar["c"])
            <= max(bar["o"], bar["c"])
            <= bar["h"]
            or stamp.timestamp() + 60 > now
            or (rows and stamp.timestamp() <= rows[-1]["epoch"])
        ):
            return result
        rows.append(
            dict(
                epoch=stamp.timestamp(),
                **{k: bar[k] for k in ("o", "h", "l", "c", "v")},
                partial_volume=bar.get("partial_volume") is not False,
            )
        )
    if not rows or rows[-1]["epoch"] != end.timestamp():
        return result
    # The existing producer must authorize the current minute window. Do not
    # reuse yesterday's or an earlier completed window after a missing suffix.
    if int(now // 60) - int(rows[-1]["epoch"] // 60) != 1:
        return result
    last = rows[-1]
    prev = (
        rows[-2] if len(rows) > 1 and rows[-2]["epoch"] == last["epoch"] - 60 else None
    )
    span = last["h"] - last["l"]
    result.update(
        status="observed",
        reason=None,
        source_sha256=P.digest(original),
        latest_upper_wick_ratio=(
            (last["h"] - max(last["o"], last["c"])) / span if span else None
        ),
        latest_close_return_pct=(100 * (last["c"] / prev["c"] - 1) if prev else None),
        latest_volume_ratio=(
            last["v"] / prev["v"]
            if prev
            and prev["v"] > 0
            and not prev["partial_volume"]
            and not last["partial_volume"]
            else None
        ),
        interpretation="Observed completed structure only; no fixed veto, future outcome or extra confirmation.",
    )
    return result
