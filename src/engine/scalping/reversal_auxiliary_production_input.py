"""Explicit production opt-in for the reviewed auxiliary input transformation.

This scalping input owner projects existing confirmation-prefix facts only.
Registration and activation remain with the native policy/overlay publishers;
the offline research authorization is never an activation credential.
"""

from __future__ import annotations

import copy
import math
import re

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


def contract(scope_ids):
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
        version=VERSION,
        mode=MODE,
        input_version=U.VERSION,
        source_sha256=P.file_hash(__file__),
        transform_sha256=REVIEWED_TRANSFORM_SHA256,
        definition_sha256=X.contract(MODE)["definition_sha256"],
        scope_ids=scope_ids[:],
        source_boundary="ORIGINAL_CONFIRMATION_PREFIX_ONLY",
        decision_authority="AUXILIARY_RISK_SCREEN_NO_MACHINE_PROMOTION",
        activation_authority="EXISTING_NATIVE_POLICY_PUBLISHER_ONLY",
    )


def validate(value):
    if not isinstance(value, dict) or value != contract(value.get("scope_ids")):
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
        or not re.fullmatch(r"\d{6}", common["symbol"])
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


def project(logical_input, *, expected_contract):
    _scope(logical_input, expected_contract)
    # Call the immutable pure transformation only. Its report-only research
    # flags never enter the registry, request, or policy activation contract.
    return X.project(logical_input, expected_contract=X.contract(MODE))


def validate_projected(logical_input, *, expected_contract):
    """Reject bypassed, doubled or changed derived facts at wire/decode entry.

    Reconstruct the base fact ledger, then reproduce the entire transformed
    input. Numeric values and risk bindings are checked, never just presence.
    """
    _scope(logical_input, expected_contract)
    W.encode(logical_input)
    base = copy.deepcopy(logical_input)
    setup = base["entry_setup_evidence_v1"]

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
    if project(base, expected_contract=expected_contract) != logical_input:
        raise ValueError("auxiliary_production_input_projection_changed")
    return logical_input
