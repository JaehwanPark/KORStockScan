"""Producer-owned research recommendation identity, without execution authority.

The stable ID tracks an owner/scope/axis across source generations. Proposal
changes have a separate hash so a revised policy cannot reuse old approval.
This module never converts a research decision into an implementation order.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

CONTRACT = "machine_recommendation_identity_v1"


def recommendation_inventory(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect every native recommendation, including nested lanes and mirrors.

    This is read-only intake, not an approval or policy selection function.
    Preserve all source locations and reject contradictory mirror contracts.
    """
    found: dict[str, dict[str, Any]] = {}
    observed_fields: dict[str, dict[str, Any]] = {}
    contract_fields = (
        "recommendation_contract",
        "recommendation_scope",
        "recommendation_proposal_sha256",
        "recommendation_consumer",
        "recommendation_acceptance",
        "recommendation_identity_grants_authority",
    )
    shared_fields = (
        "runtime_effect",
        "allowed_runtime_apply",
        "actual_order_submitted",
        "broker_order_forbidden",
        "recommended_spot",
        "selected_policy",
        "decision",
        "recommendation_tier",
        "implementation_status",
    )

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            if "recommendation_id" in value:
                native_id = value["recommendation_id"]
                scope = value.get("recommendation_scope")
                if (
                    not isinstance(native_id, str)
                    or not native_id.strip()
                    or not isinstance(scope, dict)
                    or any(
                        not isinstance(scope.get(k), str) or not scope[k].strip()
                        for k in ("producer", "scope", "axis")
                    )
                    or value.get("recommendation_contract") != CONTRACT
                    or value.get("recommendation_identity_grants_authority")
                    is not False
                    or not re.fullmatch(
                        r"[0-9a-f]{64}",
                        str(value.get("recommendation_proposal_sha256") or ""),
                    )
                    or any(
                        not isinstance(value.get(k), str) or not value[k].strip()
                        for k in (
                            "recommendation_consumer",
                            "recommendation_acceptance",
                        )
                    )
                ):
                    raise ValueError(
                        f"recommendation_inventory_contract_invalid:{path}"
                    )
                expected = hashlib.sha256(
                    json.dumps(
                        scope,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=True,
                        allow_nan=False,
                    ).encode("ascii")
                ).hexdigest()
                if native_id != f"{scope['producer']}:{expected}":
                    raise ValueError(
                        f"recommendation_inventory_identity_invalid:{path}"
                    )
                previous = found.get(native_id)
                if previous:
                    original = observed_fields[native_id]
                    fields = contract_fields + tuple(
                        k for k in shared_fields if k in original and k in value
                    )
                    if any(
                        original.get(k) != value.get(k)
                        or type(original.get(k)) is not type(value.get(k))
                        for k in fields
                    ):
                        raise ValueError(
                            f"recommendation_inventory_mirror_conflict:{path}"
                        )
                    previous["source_locations"].append(path)
                else:
                    found[native_id] = {
                        "recommendation_id": native_id,
                        "row": value,
                        "source_locations": [path],
                    }
                    observed_fields[native_id] = {}
                observed_fields[native_id].update(
                    {k: value[k] for k in contract_fields + shared_fields if k in value}
                )
            for key, child in value.items():
                visit(child, f"{path}[{json.dumps(key, ensure_ascii=True)}]")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    for key in ("recommendations", "postclose_logic_recommendations"):
        if key in report and (
            not isinstance(report[key], list)
            or any(
                not isinstance(row, dict) or "recommendation_id" not in row
                for row in report[key]
            )
        ):
            raise ValueError(f"recommendation_inventory_primary_id_missing:{key}")
    visit(report, "$")
    return list(found.values())


def bind_recommendation(
    row: dict[str, Any],
    *,
    producer: str,
    scope: str,
    axis: str,
    proposal: dict[str, Any],
    consumer: str,
    acceptance: str,
) -> None:
    """Attach an auditable identity; reject conflicting existing metadata."""
    identity = {"producer": producer, "scope": scope, "axis": axis}
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (
            *identity.values(),
            consumer,
            acceptance,
        )
    ) or not isinstance(proposal, dict):
        raise ValueError("recommendation_identity_contract_invalid")

    def digest(value: object) -> str:
        return hashlib.sha256(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest()

    metadata = {
        "recommendation_id": f"{producer}:{digest(identity)}",
        "recommendation_contract": CONTRACT,
        "recommendation_scope": identity,
        "recommendation_proposal_sha256": digest(proposal),
        "recommendation_consumer": consumer,
        "recommendation_acceptance": acceptance,
        "recommendation_identity_grants_authority": False,
    }
    if any(key in row and row[key] != value for key, value in metadata.items()):
        raise ValueError("recommendation_identity_conflict")
    row.update(metadata)
