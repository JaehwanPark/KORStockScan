"""Immutable receipt of the existing stage-specific quote time owners.

This receipt describes resolved configuration. It does not select a new TTL,
attest a source, renew an AI decision, or extend an opportunity deadline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math


@dataclass(frozen=True, slots=True)
class QuoteTimePolicy:
    version: str = "configured_quote_time_policy_v1"
    pre_ai_max_age_ms: float = 3000.0
    canonical_input_max_age_ms: float = 3000.0
    async_transport_max_age_ms: float = 2000.0
    latency_safe_ms: float = 250.0
    latency_caution_ms: float = 700.0
    refresh_max_age_ms: float = 700.0
    consistency_ws_max_age_ms: float = 700.0
    submit_transport_max_age_ms: float = 2000.0
    consistency_enabled: bool = False
    refresh_enabled: bool = True

    def __post_init__(self) -> None:
        if self.version != "configured_quote_time_policy_v1":
            raise ValueError("unsupported_quote_time_policy_version")
        for key, value in asdict(self).items():
            if key.endswith("_ms"):
                if (
                    type(value) not in (int, float)
                    or not math.isfinite(value)
                    or value < 0
                ):
                    raise ValueError(f"invalid_quote_time_policy_limit:{key}")
                object.__setattr__(self, key, float(value))
        if (
            type(self.consistency_enabled) is not bool
            or type(self.refresh_enabled) is not bool
        ):
            raise ValueError("invalid_quote_time_policy_flag")

    def budget_for(self, stage: str) -> float:
        fields = {
            "pre_ai": "pre_ai_max_age_ms",
            "canonical_input": "canonical_input_max_age_ms",
            "async_transport": "async_transport_max_age_ms",
            "latency_safe": "latency_safe_ms",
            "latency": "latency_caution_ms",
            "refresh": "refresh_max_age_ms",
            "consistency": "consistency_ws_max_age_ms",
            "submit_transport": "submit_transport_max_age_ms",
            # Physical entry-send uses the source clock owned by latency,
            # independently of the older transport snapshot check.
            "physical_send": "latency_caution_ms",
        }
        try:
            return float(getattr(self, fields[stage]))
        except KeyError as exc:
            raise ValueError("unknown_quote_time_policy_stage") from exc

    def to_dict(self) -> dict:
        values = asdict(self)
        values["sha256"] = hashlib.sha256(
            json.dumps(
                values, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        values["source_clock"] = "ws_quote_source_receipt.observed_epoch"
        values["transport_clock"] = "last_ws_update_ts"
        values["decision_authority"] = "existing_configured_owners_only"
        return values

    def active_contract_dict(self) -> dict:
        return active_contract_receipt(self.to_dict())


def configured_quote_time_policy(**resolved_values) -> QuoteTimePolicy:
    """Take resolved owner values, never infer authority from a source frame."""
    return QuoteTimePolicy(**resolved_values)


def active_contract_receipt(receipt) -> dict:
    """Keep inactive diagnostic limits out of an execution binding.

    Validate the full producer receipt first. Flags and all active owner values
    remain bound; turning a disabled owner on always changes the contract.
    """
    try:
        policy = QuoteTimePolicy(
            **{field.name: receipt[field.name] for field in fields(QuoteTimePolicy)}
        )
        if dict(receipt) != policy.to_dict():
            raise ValueError("quote_time_policy_receipt_invalid")
        active = dict(receipt)
        active.pop("sha256")
        if not policy.consistency_enabled:
            active.pop("consistency_ws_max_age_ms")
        if not policy.refresh_enabled:
            active.pop("refresh_max_age_ms")
        return active
    except (KeyError, TypeError) as exc:
        raise ValueError("quote_time_policy_receipt_invalid") from exc
