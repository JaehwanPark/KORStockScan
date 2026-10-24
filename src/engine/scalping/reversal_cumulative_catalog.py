"""Frozen manual hypotheses and exact-scope variants; no publication authority."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = "main_cumulative_definition_catalog_v2"
DATA_SHA256 = "a3eec24e197415fc50f2bf7572eb6b3ce5de39248cff22a5893d8dba83e417e5"
_raw = Path(__file__).with_name("reversal_cumulative_data.json").read_bytes()
if hashlib.sha256(_raw).hexdigest() != DATA_SHA256:
    raise ValueError("cumulative_catalog_data_changed")
_data = json.loads(_raw)
DEFINITIONS = _data["definitions"]
LEGACY_DEFINITIONS = DEFINITIONS
GROUPS = _data["groups"]
RECOMMENDATIONS = _data["recommendations"]
PARENT = _data["parent_bundle_sha256"]
RESEARCH_RESULT = _data["research_result_sha256"]
RESEARCH_MANIFEST = _data["research_manifest_sha256"]
PROGRESS_DATA_SHA256 = (
    "b70882e87411bf76b22330b61c9e3aa158eba42c5f8ad798eb8c2d3b8a72aef4"
)
_progress_raw = (
    Path(__file__).with_name("reversal_price_progress_data.json").read_bytes()
)
if hashlib.sha256(_progress_raw).hexdigest() != PROGRESS_DATA_SHA256:
    raise ValueError("price_progress_catalog_data_changed")
PROGRESS = json.loads(_progress_raw)
PROGRESS_RESULT = PROGRESS["research_result_sha256"]
PROGRESS_DEFINITIONS = {
    b: d for b, d in PROGRESS["definitions"].items() if b not in LEGACY_DEFINITIONS
}
if any(PROGRESS["definitions"].get(b) != d for b, d in LEGACY_DEFINITIONS.items()):
    raise ValueError("price_progress_legacy_definition_changed")
DEFINITIONS = dict(LEGACY_DEFINITIONS, **PROGRESS_DEFINITIONS)
CATALOGS = {RESEARCH_RESULT: _data, PROGRESS_RESULT: PROGRESS}
REFINEMENTS = {
    b: d for b, d in DEFINITIONS.items() if d["kind"] == "cumulative_refinement"
}
ROOTS = {b: d for b, d in DEFINITIONS.items() if d["kind"] == "cumulative_root"}
FEATURE_VERSION = "manual_cumulative_confirmation_prefix_v2"
FIELDS = dict(
    ret="ret",
    session="session",
    vwap="vwap",
    buy="buy10",
    volume="volume",
    spread="spread",
    dd="dd",
    price10="return10_pct",
    bid10="bid_return10_pct",
    bid30="bid_return30_pct",
    range10="range_spread10",
    progress="price_progress_spreads10",
)


def catalog(batch=None):
    try:
        return CATALOGS[RESEARCH_RESULT if batch is None else batch]
    except (KeyError, TypeError):
        raise ValueError("cumulative_research_batch_unknown") from None


def registry(batch=None):
    from src.engine.scalping import reversal_extended_catalog as C

    catalog(batch)
    return C.PROGRESS_SHA256 if batch == PROGRESS_RESULT else C.CUMULATIVE_SHA256


def definition(bid):
    return copy.deepcopy(DEFINITIONS[bid])


def phase(bid):
    d = DEFINITIONS[bid]
    if bid in REFINEMENTS:
        return d["decision_phase"]
    root = d["root_confirmation"]
    if root.startswith("FIRST_BID"):
        return "FIRST_PRICE_HOLD"
    if root.startswith("FIRST_HOLD"):
        return "FIRST_PRICE_HOLD"
    if root.startswith("RETEST"):
        return "RETEST_RECLAIM_FIRST"
    if root == "BREAKOUT60":
        return "HIGH_BREAKOUT"
    if root.startswith("BREAKOUT60_HOLD"):
        return "HIGH_BREAKOUT_HOLD"
    if root.startswith("VWAP"):
        return "VWAP_RECLAIM_HOLD"
    if root.startswith("RISING"):
        return "RISING_STRUCTURE_HOLD"
    return "MOMENTUM_HOLD" if "_HOLD" in root else "MOMENTUM_CROSS"


PHASES = {b: phase(b) for b in DEFINITIONS}


def root_contract(root):
    signal = (
        "native_first_turn"
        if root.startswith(("FIRST", "RETEST"))
        else (
            "BREAKOUT"
            if root.startswith("BREAKOUT")
            else (
                "MOMENTUM"
                if root.startswith("MOMENTUM")
                else "VWAP_RECLAIM" if root.startswith("VWAP") else "RISING_STRUCTURE"
            )
        )
    )
    d = dict(
        signal=signal,
        confirmation=(
            "HOLD"
            if "_HOLD" in root
            else "RETEST_FIRST" if root.startswith("RETEST") else "immediate"
        ),
        condition_trigger=(
            "native_first_turn"
            if signal == "native_first_turn"
            else "known_false_to_known_true"
        ),
    )
    if "_HOLD" in root:
        d["hold_seconds"] = int(root.rsplit("HOLD", 1)[1])
    if signal == "MOMENTUM":
        d["return_60s_min_pct"] = float(root.split("_")[1])
    if signal != "native_first_turn":
        d["warmup_seconds"] = 60
    if root.startswith("RETEST"):
        d.update(maximum_wait_seconds=30, allowed_below_original_low_pct=0.2)
    if root.startswith("FIRST_BID"):
        d.update(
            confirmation="FIRST_BID_ADVANCE_HOLD",
            maximum_wait_seconds=30,
            quote_continuity_required=True,
            trade_and_bid_hold=True,
            first_bid_advance_consumed=True,
        )
    return d


def condition(features, rules):
    """Unknown preserves a refinement, but never creates an additive signal."""
    if "when" in rules:
        applies = condition(features, rules["when"])
        return (
            True
            if applies is False
            else None if applies is None else condition(features, rules["require"])
        )
    unknown = False
    for rule, bound in rules.items():
        if rule == "structure":
            value = features.get("structure")
            if value is None:
                unknown = True
                continue
            if value not in {"RISING", "FALLING", "MIXED"}:
                raise ValueError("cumulative_structure_invalid")
            result = (value == "RISING") if bound == "RISING" else value != "FALLING"
        else:
            suffix = next(
                (
                    s
                    for s in ("_min_exclusive", "_max_exclusive", "_min", "_max")
                    if rule.endswith(s)
                ),
                None,
            )
            if suffix is None or rule[: -len(suffix)] not in FIELDS:
                raise ValueError("cumulative_filter_operator_invalid")
            value = features.get(FIELDS[rule[: -len(suffix)]])
            if value is None:
                unknown = True
                continue
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("cumulative_feature_invalid")
            result = (
                value > bound
                if suffix == "_min_exclusive"
                else (
                    value < bound
                    if suffix == "_max_exclusive"
                    else value >= bound if suffix == "_min" else value <= bound
                )
            )
        if not result:
            return False
    return None if unknown else True


def dependencies(ids):
    """Finite dependency order; internal ancestors are never operating members."""
    order = []
    active = set()
    seen = set()
    from src.engine.scalping import reversal_extended_catalog as C

    def visit(bid):
        if bid in active:
            raise ValueError("cumulative_dependency_cycle")
        if bid in seen:
            return
        active.add(bid)
        if bid in REFINEMENTS:
            ref = REFINEMENTS[bid]["original_definition_ref"]
            if ref["definition_sha256"] != digest(C.definition(ref["branch_id"])):
                raise ValueError("cumulative_dependency_changed")
            visit(ref["branch_id"])
        elif bid in C.JOINT.COMPOSED:
            visit(C.JOINT.COMPOSED[bid]["original_definition_ref"]["branch_id"])
        active.remove(bid)
        seen.add(bid)
        order.append(bid)

    for bid in ids:
        visit(bid)
    return tuple(order)


def variants(scope, batch=None):
    g = catalog(batch)["groups"][scope]
    base = set(g["baseline"])
    result = {"CURRENT": sorted(base)}
    refs = {}
    for name, replacements in sorted(g["refinements"].items()):
        refs[name] = sorted(replacements.values())
        for original, successor in sorted(replacements.items()):
            refs[name + "@" + original] = sorted((base - {original}) | {successor})
    for a, bid in sorted(g["additions"].items()):
        result["A:" + a] = sorted(base | {bid})
    for f, ids in refs.items():
        result["F:" + f] = ids
    for a, bid in sorted(g["additions"].items()):
        for f, ids in refs.items():
            result["J:" + a + "+" + f] = sorted(set(ids) | {bid})
    return result


def membership(scope, variant, batch=None):
    g = catalog(batch)["groups"][scope]
    base = set(g["baseline"])
    if variant == "CURRENT":
        return sorted(base)
    kind, expression = variant.split(":", 1)
    addition = None
    if kind == "J":
        addition, expression = expression.split("+", 1)
    elif kind == "A":
        return sorted(base | {g["additions"][expression]})
    name, _, original = expression.partition("@")
    replacement = g["refinements"][name]
    result = (
        (base - {original}) | {replacement[original]}
        if original
        else set(replacement.values())
    )
    return sorted(result | ({g["additions"][addition]} if addition else set()))


def valid_membership(scope, ids, batch=None):
    """Validate the finite expression grammar without expanding 25k portfolios."""
    g = catalog(batch)["groups"][scope]
    selected = set(ids)
    additions = selected & set(g["additions"].values())
    if len(additions) > 1 or len(ids) != len(selected):
        return False
    selected -= additions
    base = set(g["baseline"])
    if selected == base:
        return True
    for mapping in g["refinements"].values():
        if selected == set(mapping.values()):
            return True
        for original, child in mapping.items():
            if selected == (base - {original}) | {child}:
                return True
    return False


def compose(bid, original, features):
    """Refine this exact native confirmation, without resetting its clock."""
    from src.engine.scalping import reversal_extended_catalog as C

    d = REFINEMENTS[bid]
    ref = d["original_definition_ref"]
    original_id = ref["branch_id"]
    if ref["definition_sha256"] != digest(C.definition(original_id)) or original.get(
        "branch_definition_sha256"
    ) != C.branch(original_id).get("definition_sha256"):
        raise ValueError("cumulative_original_definition_invalid")
    truth = condition(features, d["filters"])
    if truth is False:
        return None
    event = copy.deepcopy(original)
    event.update(
        extended_definition_id=bid,
        branch_definition_sha256=digest(d),
        decision_phase=PHASES[bid],
        signal_kind=PHASES[bid],
        branch_features=copy.deepcopy(features),
        spread_pct=features["spread"],
        drawdown_5m_pct=features["dd"],
        volume_ratio_60s=features["volume"],
        signal_proof=dict(
            root_contract=dict(signal="original_confirmation"),
            original_definition_ref=copy.deepcopy(ref),
            original_confirmation=copy.deepcopy(original),
            refinement_truth="UNKNOWN" if truth is None else "TRUE",
            feature_version=d["feature_contract"],
            refinement_features=copy.deepcopy(features),
        ),
    )
    return event


def validate_signal(event):
    """Validate proof ownership as well as branch, quote and confirmation identity."""
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.scalping import reversal_extended_auxiliary as A
    from src.engine.scalping.continuous_reversal_branches import FIRST, CONFIRMED

    bid = event.get("extended_definition_id")
    d = DEFINITIONS[bid]
    proof = event.get("signal_proof") or {}
    fields = (
        "epoch",
        "confirmation_price",
        "entry_ask",
        "native_epoch",
        "native_sequence",
    )
    if (
        event.get("branch_definition_sha256") != digest(d)
        or event.get("decision_phase") != PHASES[bid]
        or event.get("signal_kind") != PHASES[bid]
        or any(
            type(event.get(k)) not in (int, float)
            or not math.isfinite(event[k])
            or event[k] <= 0
            for k in fields
        )
        or any(type(event[k]) is not int for k in ("native_epoch", "native_sequence"))
        or not C.applicable(
            bid,
            C.cell_key(event["symbol"], event["market"], event["confirmation_price"]),
            event["venue"],
        )
        or event.get("source_item")
        != event["symbol"] + ("_NX" if d["route"] == "NXT" else "_AL")
    ):
        raise ValueError("cumulative_signal_identity_invalid")
    if bid in REFINEMENTS:
        original = proof.get("original_confirmation") or {}
        ref = d["original_definition_ref"]
        if original.get("extended_definition_id") in DEFINITIONS:
            validate_signal(original)
        elif (
            original.get("extended_definition_id")
            or original.get("path_definition_id")
            or original.get("decision_phase") not in {FIRST, CONFIRMED}
        ):
            A.validate_signal(original)
        elif original.get("decision_phase") not in {
            FIRST,
            CONFIRMED,
        } or not 0 < original.get("low_price", 0) < original.get(
            "confirmation_price", 0
        ):
            raise ValueError("cumulative_original_native_proof_invalid")
        if original.get("decision_phase") == CONFIRMED and not (
            0 <= original["epoch"] - original.get("anchor_epoch", -1) <= 5
            and original["confirmation_price"]
            > original.get("anchor_price", 0)
            > original.get("low_price", 0)
        ):
            raise ValueError("cumulative_original_confirmation_timeline_invalid")
        if (
            any(
                event.get(k) != original.get(k)
                for k in (
                    *fields,
                    "symbol",
                    "market",
                    "venue",
                    "source_item",
                    "event_id",
                    "signal_id",
                )
            )
            or proof.get("original_definition_ref") != ref
            or C.matches(
                ref["branch_id"], original, original.get("branch_features", {})
            )
            is not True
        ):
            raise ValueError("cumulative_original_confirmation_changed")
        expected = compose(bid, original, proof.get("refinement_features") or {})
        if expected is None or expected != event:
            raise ValueError("cumulative_refinement_proof_invalid")
        return
    root = d["root_confirmation"]
    if (
        proof.get("root_confirmation") != root
        or proof.get("root_contract") != root_contract(root)
        or proof.get("feature_version") != d["feature_contract"]
        or condition(event.get("branch_features", {}), d["filters"]) is not True
        or proof.get("native_epoch") != event["native_epoch"]
        or type(proof.get("native_sequence")) is not int
        or proof["native_sequence"] > event["native_sequence"]
        or any(
            type(proof.get(k)) not in (int, float)
            or not math.isfinite(proof[k])
            or proof[k] <= 0
            for k in ("epoch", "price", "minimum_price")
        )
        or proof["native_sequence"] <= 0
        or proof["epoch"] > event["epoch"]
        or proof["minimum_price"] > min(proof["price"], event["confirmation_price"])
    ):
        raise ValueError("cumulative_root_proof_invalid")
    hold = int(root.rsplit("HOLD", 1)[1]) if "_HOLD" in root else 0
    if hold:
        if (
            event["epoch"] < proof["epoch"] + hold
            or proof.get("minimum_price", 0) < proof.get("price", 1)
            or event["confirmation_price"] < proof["price"]
            or proof["native_sequence"] >= event["native_sequence"]
        ):
            raise ValueError("cumulative_hold_proof_invalid")
    elif not root.startswith("RETEST") and (
        proof["epoch"] != event["epoch"]
        or proof["native_sequence"] != event["native_sequence"]
        or proof["price"] != event["confirmation_price"]
    ):
        raise ValueError("cumulative_root_confirmation_shifted")
    if (
        root.startswith(("MOMENTUM", "BREAKOUT", "VWAP", "RISING"))
        and proof.get("previous_condition") is not False
    ):
        raise ValueError("cumulative_unknown_root_promotion")
    if root.startswith("MOMENTUM"):
        threshold = float(root.split("_")[1])
        value = proof.get("return_60s_pct")
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value < threshold
            or proof.get("threshold") != threshold
        ):
            raise ValueError("cumulative_momentum_root_invalid")
    if root.startswith("BREAKOUT"):
        prior = proof.get("prior_high")
        if (
            type(prior) not in (int, float)
            or not math.isfinite(prior)
            or not 0 < prior < proof["price"]
        ):
            raise ValueError("cumulative_breakout_root_invalid")
    if root.startswith("VWAP"):
        value = proof.get("vwap_at_root")
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("cumulative_vwap_root_invalid")
    if root.startswith("RISING") and proof.get("structure_at_root") != "RISING":
        raise ValueError("cumulative_structure_root_invalid")
    if root.startswith(("FIRST", "RETEST")):
        low = proof.get("low")
        if (
            type(low) not in (int, float)
            or not math.isfinite(low)
            or not 0 < low < proof["price"]
            or not proof.get("anchor_event_id")
        ):
            raise ValueError("cumulative_first_root_invalid")
    if root.startswith("RETEST"):
        if (
            any(
                type(proof.get(k)) not in (int, float) or not math.isfinite(proof[k])
                for k in ("touch_epoch", "touch_price", "touch_sequence")
            )
            or not proof["native_sequence"]
            < proof["touch_sequence"]
            < event["native_sequence"]
            or not proof["epoch"]
            <= proof["touch_epoch"]
            <= event["epoch"]
            <= proof["epoch"] + 30
            or proof["touch_price"] > proof["low"]
            or proof["minimum_price"] > proof["touch_price"]
            or proof["minimum_price"] < proof["low"] * 0.998
            or event["confirmation_price"] < proof["price"]
        ):
            raise ValueError("cumulative_retest_proof_invalid")
    if root.startswith("FIRST_BID"):
        numeric = (
            "turn_epoch",
            "turn_sequence",
            "turn_price",
            "initial_bid",
            "bid_at_root",
            "minimum_bid",
        )
        if (
            any(
                type(proof.get(k)) not in (int, float)
                or not math.isfinite(proof[k])
                or proof[k] <= 0
                for k in numeric
            )
            or type(proof["turn_sequence"]) is not int
            or not proof["turn_sequence"]
            < proof["native_sequence"]
            < event["native_sequence"]
            or not proof["turn_epoch"]
            <= proof["epoch"]
            <= event["epoch"]
            <= proof["turn_epoch"] + 30
            or proof["price"] < proof["turn_price"]
            or proof["bid_at_root"] <= proof["initial_bid"]
            or proof["minimum_bid"] < proof["bid_at_root"]
            or type(event.get("confirmation_bid")) not in (int, float)
            or not math.isfinite(event["confirmation_bid"])
            or not proof["minimum_bid"] <= event["confirmation_bid"]
            or proof.get("quote_contiguous") is not True
        ):
            raise ValueError("cumulative_bid_hold_proof_invalid")
