"""Fail-closed Entry AI consumer of the separately approved current axis."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any
import uuid
import threading

from src.engine.scalping import main_ai_current_axis as policy

_validation_lock = threading.Lock()
_validated_source_key: tuple | None = None


def cache_token() -> str:
    # With the family enabled, do not reuse an AI result across a changed
    # micro input, an expired approval, or a rollback in the same process.
    return uuid.uuid4().hex if policy.enabled() else "disabled"


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink() or path.with_suffix(".json.gz").exists()


def load_active(now: datetime, *, root: Path | None = None) -> tuple[dict, dict]:
    global _validated_source_key
    selected_root = root or policy.RUNTIME_ROOT
    target = policy.now_kst(now).date().isoformat()
    activation = policy.read(selected_root / f"activation_{target}.json")
    receipt = policy.read(selected_root / f"apply_receipt_{target}.json")
    authorization = policy.read(selected_root / "operator_authorization.json")
    first = None
    if authorization.get("first_candidate_sha256") != activation.get(
        "candidate_sha256"
    ):
        first = policy.read(selected_root / "enrollment_receipt.json")
        first_activation = policy.read(
            selected_root / f"activation_{first['target_date']}.json"
        )
        if first != policy.apply_receipt(first_activation):
            raise ValueError("enrollment_activation_receipt_not_committed")
    candidate = policy.validate_live_activation(
        activation=activation,
        receipt=receipt,
        authorization=authorization,
        first_receipt=first,
        now=now,
        revoked=_present(selected_root / "rollback.json"),
    )
    from src.engine.automation.main_ai_current_axis import owner_conflicts
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    policy.validate_postclose_handoff(candidate, root=selected_root)
    if owner_conflicts(target):
        raise ValueError("same_stage_owner_conflict")
    rolling = policy.read(cycle.rolling_report_path(candidate["source_date"]))
    manifest = policy.read(cycle.r3_manifest_path(candidate["source_date"]))
    policy.validate_terminal_cycle(rolling, manifest)
    # Cache validation of immutable content only. Mutable consent, rollback,
    # date/time and competing owner are deliberately checked on every call.
    key = (policy.sha(candidate), policy.sha(rolling), policy.sha(manifest))
    with _validation_lock:
        if key != _validated_source_key:
            rebuilt = policy.build_candidate(
                rolling=rolling,
                manifest=manifest,
                candidate_id=candidate["candidate_id"],
                control=candidate["control"],
                recommended=candidate["recommended"],
                input_reference=candidate["input_reference"],
            )
            if rebuilt != candidate:
                raise ValueError("live_source_generation_changed")
            _validated_source_key = key
    return activation, candidate


def select_request(
    request: Any,
    *,
    execution: dict,
    metadata: dict,
    now: datetime | None = None,
    root: Path | None = None,
    source_reader=None,
) -> tuple[Any, dict]:
    """Change only system/user input; all provider/order execution fields stay."""
    if not policy.enabled():
        return request, {}
    current = now or datetime.now(policy.KST)
    receipt = {
        "schema": "main_ai_current_axis_request_receipt_v1",
        "family": policy.FAMILY,
        "target_date": current.date().isoformat(),
        "request_id": request.request_id,
        "stock_code": request.symbol,
        "status": "not_applied",
        "runtime_effect": False,
        "provider_delivery_confirmed": False,
        "actual_order_submitted": False,
    }
    try:
        if (
            request.endpoint_name != "analyze_target"
            or metadata.get("ai_trace_strategy") not in {"SCALP", "SCALPING"}
            or metadata.get("ai_trace_prompt_type") != "scalping_entry"
            or metadata.get("position_tag") != "SCANNER"
            or metadata.get("entry_setup_live_policy_activation_sha256")
            or metadata.get("main_ai_quality_live_policy_runtime_effect") is True
            or metadata.get("sim_record_id")
            or metadata.get("sim_parent_record_id")
            or metadata.get("position_reconciliation_mode") == "simulation_book"
        ):
            raise ValueError("out_of_scope_or_same_stage_owner_conflict")
        activation, candidate = load_active(current, root=root)
        if request.symbol not in candidate["eligible_symbols"]:
            raise ValueError("outside_approved_cost_symbol_cohort")
        control = candidate["control"]
        if control["system_prompt"] != request.prompt or control[
            "prompt_version"
        ] != metadata.get("main_ai_current_axis_baseline_prompt_version"):
            raise ValueError("current_baseline_prompt_drift")
        for field in policy.EXECUTION_FIELDS:
            if control.get(field) != execution.get(field):
                raise ValueError(f"current_execution_contract_drift:{field}")
        from src.engine.scalping.main_ai_current_axis_input import prepare_input

        user_input, input_receipt = prepare_input(
            base_input=request.user_input,
            request_id=request.request_id,
            symbol=request.symbol,
            metadata=metadata,
            candidate=candidate,
            now=current,
            source_reader=source_reader,
        )
        # Re-read mutable authority after preparation; a concurrent revoke,
        # expiry or replacement cannot be hidden by the first lookup.
        recheck_time = now or datetime.now(policy.KST)
        rechecked, _ = load_active(recheck_time, root=root)
        if rechecked != activation:
            raise ValueError("activation_changed_during_input_preparation")
        age = (
            policy.now_kst(recheck_time)
            - policy.now_kst(
                datetime.fromisoformat(input_receipt["snapshot_captured_at"])
            )
        ).total_seconds()
        if not 0 <= age <= 1:
            raise ValueError("input_stale_after_preparation")
        receipt.update(
            **input_receipt,
            status="prepared_for_provider",
            runtime_effect=True,
            activation_sha256=activation[policy.HASH_FIELD],
            candidate_sha256=candidate[policy.HASH_FIELD],
            r3_candidate_id=candidate["candidate_id"],
            source_date=candidate["source_date"],
            selected_prompt_version=candidate["recommended"]["prompt_version"],
            expected_transport=control["transport"],
            prompt_sha256=hashlib.sha256(
                candidate["recommended"]["system_prompt"].encode()
            ).hexdigest(),
        )
        return (
            replace(
                request,
                prompt=candidate["recommended"]["system_prompt"],
                user_input=user_input,
            ),
            receipt,
        )
    except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
        receipt["reason"] = str(exc)
        return request, receipt


def settle_response(
    receipt: dict,
    *,
    now: datetime | None = None,
    root: Path | None = None,
    provider_transport: str | None = None,
) -> dict:
    """Record delivery independently; revoke in-flight candidate decisions."""
    if receipt.get("runtime_effect") is not True:
        return receipt
    result = {**receipt, "provider_delivery_confirmed": True}
    try:
        if provider_transport is not None and provider_transport.removeprefix(
            "responses_"
        ) != str(receipt.get("expected_transport")).removeprefix("responses_"):
            raise ValueError("provider_transport_changed_while_in_flight")
        activation, _ = load_active(now or datetime.now(policy.KST), root=root)
        if activation[policy.HASH_FIELD] != receipt["activation_sha256"]:
            raise ValueError("activation_replaced_while_in_flight")
    except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
        result.update(
            status="revoked_while_in_flight", decision_usable=False, reason=str(exc)
        )
    else:
        result.update(status="provider_response_received", decision_usable=True)
    return result


def attribution(rows: list[dict], *, target_date: str, activation: dict | None) -> dict:
    """Exact-request delivery census, not fills, EV or economic acceptance."""
    counts: dict[str, int] = {}
    seen = set()
    errors = []
    for row in rows:
        raw = row.get("main_ai_current_axis_receipt")
        if not raw:
            continue
        try:
            receipt = json.loads(raw) if isinstance(raw, str) else raw
            if (
                not isinstance(receipt, dict)
                or receipt.get("schema") != "main_ai_current_axis_request_receipt_v1"
            ):
                raise ValueError("request_receipt_schema_invalid")
            identity = receipt["request_id"]
            if receipt.get("target_date") != target_date:
                raise ValueError("receipt_date_mismatch")
            if identity != row.get("request_id"):
                raise ValueError("exact_request_identity_mismatch")
            if identity in seen:
                raise ValueError("duplicate_exact_request_receipt")
            seen.add(identity)
            status = receipt["status"]
            if status not in {
                "not_applied",
                "prepared_for_provider",
                "revoked_while_in_flight",
                "provider_response_received",
            }:
                raise ValueError("request_receipt_status_invalid")
            if receipt.get("runtime_effect") is not (
                status != "not_applied"
            ) or receipt.get("provider_delivery_confirmed") is not (
                status in {"provider_response_received", "revoked_while_in_flight"}
            ):
                raise ValueError("request_receipt_delivery_status_inconsistent")
            if receipt.get("runtime_effect") is True:
                if not activation or receipt.get("activation_sha256") != activation.get(
                    policy.HASH_FIELD
                ):
                    raise ValueError("activation_receipt_binding_mismatch")
                if row.get("prompt_sha256") != receipt.get("prompt_sha256"):
                    raise ValueError("delivered_prompt_hash_mismatch")
                if row.get("payload_sha256") != receipt.get("input_sha256"):
                    raise ValueError("delivered_input_hash_mismatch")
                if receipt.get("provider_delivery_confirmed") is True and (
                    row.get("provider_called") is not True
                    or row.get("provider_actual") != "openai"
                ):
                    raise ValueError("provider_delivery_confirmation_mismatch")
            counts[status] = counts.get(status, 0) + 1
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(str(exc))
    return policy.seal(
        {
            "schema": "main_ai_current_axis_attribution_v1",
            "target_date": target_date,
            "status": (
                "source_quality_blocked"
                if errors
                else (
                    "observed"
                    if counts
                    else (
                        "no_natural_match"
                        if activation is not None
                        else "not_active_no_apply_receipt"
                    )
                )
            ),
            "metric_role": "delivery_census",
            "decision_authority": "source_only",
            "window_policy": "exact_target_date_unique_provider_request",
            "sample_floor": "one_exact_bound_request_for_delivery_only",
            "primary_decision_metric": "not_applicable_no_economic_claim",
            "source_quality_gate": "exact_request_activation_prompt_and_input_hashes",
            "forbidden_uses": [
                "live_approval",
                "real_fill_claim",
                "ev_or_profit_claim",
            ],
            "status_counts": counts,
            "source_quality_errors": errors,
            "economic_acceptance": "not_evaluated",
            **policy.SOURCE_ONLY,
        }
    )
