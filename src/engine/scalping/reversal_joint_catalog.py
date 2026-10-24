"""Frozen joint-study definitions; dependencies never become operating members.

Scalping owns this versioned catalog. It cannot publish a policy or call a
provider. Existing catalogs and their hashes remain addressable.
"""

from __future__ import annotations
import copy
import math
from src.engine.scalping import reversal_path_catalog as BASE
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = "main_joint_definition_catalog_v1"
AUTHORITY = "APPROVED_JOINT_PATTERN_IMPLEMENTATION_REGISTRATION_20261013"
PARENT = "d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b"
RESEARCH_RESULT = "eebaf02f318e04f899dad97d282ec338973d9a7804a5be95b165999ed97dd83a"
EVIDENCE_FILE_SHA256 = (
    "2ed3b288b5c587664999e525cc8f4cdbe3c96b21d9957fdacc919f361ef32e13"
)


def _definition(group, market, band, route, *, base=None, refinement=None):
    value = dict(
        kind="composed_confirmation_refinement" if base else "manual_path_pattern",
        definition_version=1,
        symbol_group=group,
        market=market,
        price_band=band,
        route=route,
        item_rule="symbol_NX" if route == "NXT" else "symbol_AL",
        label_contract=copy.deepcopy(BASE.LABEL),
        feature_time="actual_confirmation_received_prefix",
    )
    if base:
        value.update(
            original_definition_ref=dict(
                branch_id=base, definition_sha256=digest(BASE.definition(base))
            ),
            conditional_refinement=refinement,
            optional_unknown="preserve_original_confirmation",
            root_contract=dict(signal="original_confirmation"),
            filters={},
        )
    else:
        value.update(
            root_confirmation="BREAKOUT60",
            root_contract=dict(
                signal="BREAKOUT",
                warmup_seconds=60,
                prior_high_window_seconds=60,
                comparison="strict_greater",
                condition_trigger="known_false_to_known_true",
                confirmation="HIGH_BREAKOUT",
            ),
            filters=dict(ret_min=0.0, dd_max=0.4, buy10_min=60.0),
        )
    return value


_SPECIFICATIONS = {
    "jusung_after_refined": _definition(
        "036930",
        "AFTER",
        "GE_100000",
        "SOR",
        base="legacy_dd5_ge_0_4_v1",
        refinement=dict(feature="vwap", operator="ge", bound=0.0),
    ),
    "jusung_after_breakout": _definition("036930", "AFTER", "GE_100000", "SOR"),
    "general_pre_refined": _definition(
        "other_non_fixed",
        "PRE",
        "LT_20000",
        "NXT",
        base="legacy_dd5_0_8_vol_up_v1",
        refinement=dict(feature="session", operator="le", bound=0.4),
    ),
    "general_pre_breakout": _definition("other_non_fixed", "PRE", "LT_20000", "NXT"),
}
ALIASES = {
    alias: "manual_joint_" + digest(value)[:16]
    for alias, value in _SPECIFICATIONS.items()
}
DEFINITIONS = {
    ALIASES[alias]: copy.deepcopy(value) for alias, value in _SPECIFICATIONS.items()
}
COMPOSED = {
    b: d
    for b, d in DEFINITIONS.items()
    if d["kind"] == "composed_confirmation_refinement"
}
PHASES = {
    b: (
        BASE.branch(d["original_definition_ref"]["branch_id"])["decision_phase"]
        if b in COMPOSED
        else "HIGH_BREAKOUT"
    )
    for b, d in DEFINITIONS.items()
}


def changes():
    return {
        "036930|AFTER|GE_100000|SOR": dict(
            remove=["legacy_dd5_ge_0_4_v1"],
            add=sorted(
                ALIASES[k] for k in ("jusung_after_refined", "jusung_after_breakout")
            ),
        ),
        "other_non_fixed|PRE|LT_20000|NXT": dict(
            remove=["legacy_dd5_0_8_vol_up_v1"],
            add=sorted(
                ALIASES[k] for k in ("general_pre_refined", "general_pre_breakout")
            ),
        ),
    }


def refinement_truth(bid, features):
    rule = COMPOSED[bid]["conditional_refinement"]
    value = features.get(rule["feature"])
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("joint_refinement_feature_invalid")
    return (
        value >= rule["bound"] if rule["operator"] == "ge" else value <= rule["bound"]
    )


def compose(bid, original, features, *, epoch, sequence):
    d = COMPOSED[bid]
    ref = d["original_definition_ref"]
    if (
        ref["definition_sha256"] != digest(BASE.definition(ref["branch_id"]))
        or original.get("branch_definition_sha256")
        != BASE.branch(ref["branch_id"]).get("definition_sha256")
        or BASE.matches(ref["branch_id"], original, original.get("branch_features", {}))
        is not True
        or original["epoch"] != epoch
        or original["native_sequence"] != sequence
    ):
        raise ValueError("joint_original_confirmation_binding_invalid")
    truth = refinement_truth(bid, features)
    if truth is False:
        return None
    e = copy.deepcopy(original)
    e.update(
        branch_features=copy.deepcopy(features),
        extended_definition_id=bid,
        branch_definition_sha256=digest(d),
        signal_kind=PHASES[bid],
        signal_proof=dict(
            epoch=epoch,
            price=e["confirmation_price"],
            native_epoch=e["native_epoch"],
            native_sequence=sequence,
            root_contract=d["root_contract"],
            original_definition_ref=copy.deepcopy(ref),
            original_confirmation=copy.deepcopy(original),
            refinement_truth="UNKNOWN" if truth is None else "TRUE",
            refinement_feature_ref=dict(
                epoch=epoch,
                native_epoch=e["native_epoch"],
                native_sequence=sequence,
                feature=d["conditional_refinement"]["feature"],
                value=features.get(d["conditional_refinement"]["feature"]),
            ),
        ),
    )
    return e


def validate_composed(event):
    bid = event.get("extended_definition_id")
    d = COMPOSED[bid]
    p = event.get("signal_proof") or {}
    base = p.get("original_confirmation") or {}
    ref = d["original_definition_ref"]
    if any(
        type(base.get(k)) not in (int, float)
        or not math.isfinite(base[k])
        or base[k] <= 0
        for k in (
            "epoch",
            "confirmation_price",
            "entry_ask",
            "low_price",
            "native_epoch",
            "native_sequence",
        )
    ) or any(type(base[k]) is not int for k in ("native_epoch", "native_sequence")):
        raise ValueError("joint_original_numeric_identity_invalid")
    if base.get("path_definition_id"):
        from src.engine.scalping.reversal_path_auxiliary import validate_signal

        validate_signal(base)
    else:
        # Legacy FIRST uses its original low proof, not the path-signal schema.
        from src.engine.scalping.continuous_reversal_branches import FIRST, CONFIRMED

        if (
            base.get("decision_phase") not in {FIRST, CONFIRMED}
            or not 0 < base.get("low_price", 0) < base.get("confirmation_price", 0)
            or base.get("entry_ask", 0) <= 0
        ):
            raise ValueError("joint_original_low_proof_invalid")
        if base["decision_phase"] == CONFIRMED and not (
            0 <= base["epoch"] - base["anchor_epoch"] <= 5
            and base["confirmation_price"] > base["anchor_price"] > base["low_price"]
        ):
            raise ValueError("joint_original_confirmation_timeline_invalid")
    if (
        base.get("branch_definition_sha256")
        != BASE.branch(ref["branch_id"]).get("definition_sha256")
        or BASE.matches(ref["branch_id"], base, base.get("branch_features", {}))
        is not True
        or p.get("original_definition_ref") != ref
        or event.get("branch_definition_sha256") != digest(d)
        or event.get("decision_phase") != PHASES[bid]
        or event.get("signal_kind") != PHASES[bid]
        or any(
            event.get(k) != base.get(k)
            for k in (
                "symbol",
                "venue",
                "market",
                "source_item",
                "epoch",
                "native_epoch",
                "native_sequence",
                "confirmation_price",
                "entry_ask",
                "event_id",
                "signal_id",
            )
        )
    ):
        raise ValueError("joint_composed_signal_invalid")
    expected = compose(
        bid,
        base,
        event["branch_features"],
        epoch=event["epoch"],
        sequence=event["native_sequence"],
    )
    if expected is None or expected["signal_proof"] != p:
        raise ValueError("joint_refinement_proof_invalid")
    return base
