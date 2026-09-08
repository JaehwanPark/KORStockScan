"""Producer-owned research recommendation identity, without execution authority.

The stable ID tracks an owner/scope/axis across source generations. Proposal
changes have a separate hash so a revised policy cannot reuse old approval.
This module never converts a research decision into an implementation order.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CONTRACT = "machine_recommendation_identity_v1"


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
