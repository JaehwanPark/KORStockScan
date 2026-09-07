"""Current ask-depletion prompt/input contract. Not the retired #81 family.

This module owns validation, not operator consent. A separately installed,
exact-candidate authorization is required for the first PREOPEN application.
No source-only artifact, positive EV or environment flag constitutes consent.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = ROOT / "data/runtime/main_ai_current_axis"
FAMILY = "main_ai_ask_depletion_prompt_input_v1"
AXIS = "prompt_contract_effect_on_ask_depletion_context"
ENABLED_ENV = "MAIN_AI_CURRENT_AXIS_ENABLED"
CONTRACT = {
    "family": FAMILY,
    "axis": AXIS,
    "stage": "entry",
    "effective_venue": "KRX",
    "session_bucket": "KRX_REGULAR",
    "position_tag": "SCANNER",
    "population": "full_or_zero_exposure",
    "input_owner": "current_abc_exact_tactical_and_ask_depletion",
    "execution_contract": "unchanged_provider_model_transport_schema_parser_and_budget",
    "safety": "existing_entry_submit_price_quantity_account_broker_guards_unchanged",
    "rollback": "baseline_prompt_and_input_without_sticky_cache",
    "legacy_family_reactivation": False,
}
HASH_FIELD = "artifact_content_sha256"
EXECUTION_FIELDS = (
    "provider",
    "model",
    "temperature",
    "reasoning_effort",
    "transport",
    "schema_name",
    "require_json",
    "max_output_tokens",
    "response_schema_mode",
    "response_schema_application",
    "response_schema_registry_used",
    "response_schema_sha256",
    "semantic_validator_version",
)
SOURCE_ONLY = {
    "runtime_effect": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    body = json.loads(
        json.dumps(
            {key: item for key, item in value.items() if key != HASH_FIELD},
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return {**body, HASH_FIELD: sha(body)}


def check(value: Mapping[str, Any], schema: str) -> None:
    if not isinstance(value, Mapping) or value.get("schema") != schema:
        raise ValueError(f"{schema}:schema_invalid")
    if value.get(HASH_FIELD) != seal(value)[HASH_FIELD]:
        raise ValueError(f"{schema}:hash_invalid")


def now_kst(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("aware_clock_required")
    return value.astimezone(KST)


def next_session(source_date: str) -> str:
    current = date.fromisoformat(source_date)
    for _ in range(14):
        current += timedelta(days=1)
        if is_krx_trading_day(current):
            return current.isoformat()
    raise ValueError("next_session_unresolved")


def enabled() -> bool:
    # Deliberately no default-on compatibility aliases or legacy lock lookup.
    return os.environ.get(ENABLED_ENV, "").strip().lower() == "true"


def read(path: Path) -> dict[str, Any]:
    from src.utils.jsonl_io import read_json_object_strict_receipt

    return dict(read_json_object_strict_receipt(path).payload)


def validate_terminal_cycle(
    rolling: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle

    report = read(cycle.cycle_report_path(rolling["target_date"]))
    check(report, cycle.CYCLE_SCHEMA)
    if (
        report.get("target_date") != rolling["target_date"]
        or report.get("blockers") != []
        or report.get("status")
        not in {
            "source_only_no_new_sample",
            "r0_r1_materialized_provider_replay_bounded",
            "r0_r1_materialized_provider_replay_not_requested",
        }
        or report.get("rolling_artifact_sha256") != rolling[HASH_FIELD]
        or report.get("r3_manifest_artifact_sha256") != manifest[HASH_FIELD]
        or report.get("r3_runtime_apply_performed") is not False
    ):
        raise ValueError("latest_terminal_cycle_source_binding_invalid")


def validate_postclose_handoff(candidate: Mapping[str, Any], *, root: Path) -> None:
    status = read(root / f"postclose_status_{candidate['source_date']}.json")
    check(status, "main_ai_current_axis_cycle_v1")
    if (
        status.get("phase") != "postclose"
        or status.get("target_date") != candidate["source_date"]
        or status.get("status") != "candidate_ready_separate_authorization_required"
        or status.get("candidate_sha256") != candidate[HASH_FIELD]
        or status.get("runtime_effect") is not False
    ):
        raise ValueError("latest_postclose_candidate_handoff_invalid")


def build_candidate(
    *,
    rolling: Mapping[str, Any],
    manifest: Mapping[str, Any],
    candidate_id: str,
    control: dict,
    recommended: dict,
    input_reference: dict,
) -> dict:
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
    from src.engine.scalping.micro_reversion.replay_ablation_contract import (
        CURRENT_DESIGN_VERSION,
    )

    cycle.validate_r3_source_only_manifest(manifest, source_rolling_artifact=rolling)
    matches = [
        row for row in manifest["candidates"] if row["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError("exact_full_r3_candidate_required")
    row = matches[0]
    if rolling["target_date"] < "2026-08-25":
        raise ValueError("current_design_activation_source_required")
    for key, expected in {
        "ablation_design_version": CURRENT_DESIGN_VERSION,
        "tuning_axis": AXIS,
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
    }.items():
        if row.get(key) != expected:
            raise ValueError(f"unsupported_current_axis_cohort:{key}")
    for role, contract in (("control", control), ("candidate", recommended)):
        quality._validated_micro_reversion_prompt_contract(contract, contract_role=role)
        if not contract["system_prompt"].isascii():
            raise ValueError("runtime_prompt_must_be_ascii")
        prefix = "current" if role == "control" else "recommended"
        if row[f"{prefix}_contract_sha256"] != quality._candidate_contract_sha256(
            contract
        ):
            raise ValueError(f"r3_{prefix}_contract_mismatch")
        if row[f"{prefix}_prompt_sha256"] != contract["system_prompt_sha256"]:
            raise ValueError(f"r3_{prefix}_prompt_mismatch")
    # A response/schema or probe/quantity adapter change is not a prompt-only
    # promotion. Keep separate Entry Setup V2.14/V2.15 authority independent.
    if any(control.get(key) != recommended.get(key) for key in EXECUTION_FIELDS):
        raise ValueError("execution_or_parser_contract_change_not_registered")
    for field in (
        "analysis_schema",
        "analysis_schema_sha256",
        "supplemental_analysis_schema",
        "supplemental_analysis_schema_sha256",
        "entry_setup_evidence_schema",
        "response_schema_instance_policy",
    ):
        if control.get(field) != recommended.get(field):
            raise ValueError("input_ledger_adapter_change_not_registered")
    if control.get("provider") != "openai" or control.get("schema_name") not in {
        "entry_v1",
        "decision_quality_v2_7_entry",
    }:
        raise ValueError("current_axis_response_adapter_not_registered")
    if control.get("system_prompt") == recommended.get("system_prompt"):
        raise ValueError("candidate_prompt_not_distinct")
    from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge
    from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

    config = quality._micro_reversion_bridge_config(
        input_reference.get("bridge_config")
    )
    master = input_reference.get("symbol_master")
    symbol_master = VerifiedSymbolMaster.from_payload(
        master, require_canonical_owner=True
    )
    master_hash = bridge._sha256(master)
    effective_date = next_session(rolling["target_date"])
    effective_day = date.fromisoformat(effective_date)
    if master_hash != row["latest_symbol_master_artifact_sha256"]:
        raise ValueError("r3_symbol_master_binding_mismatch")
    defaults = bridge.BridgeConfig()
    for field in defaults.__dataclass_fields__:
        if field.startswith("cost_profile_") or field in {
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
        }:
            continue
        if getattr(config, field) != getattr(defaults, field):
            raise ValueError("runtime_input_non_cost_config_change_forbidden")
    if config.cost_profile_verified is not True:
        raise ValueError("reviewed_cost_config_required")
    eligible_symbols = []
    for record in master["records"]:
        lookup = symbol_master.lookup(record["symbol"], as_of=effective_day)
        metadata = bridge._verified_symbol_metadata_context(
            supplied={
                "lookup_status": lookup.status.value,
                "record": lookup.record.as_dict() if lookup.record else None,
                "symbol_master_artifact_sha256": master_hash,
            },
            symbol=record["symbol"],
            snapshot_date=effective_date,
        )
        profile = bridge._resolved_cost_profile(
            config=config,
            observed_date=effective_day,
            venue="KRX",
            symbol_metadata=metadata,
        )
        if (
            metadata.get("instrument_type") == "EQUITY"
            and profile
            and profile.get("profile_id") == row["selected_cost_profile_id"]
            and (profile.get("content_sha256") or profile.get("profile_content_sha256"))
            == row["selected_cost_profile_content_sha256"]
        ):
            eligible_symbols.append(record["symbol"])
    if not eligible_symbols:
        raise ValueError("current_axis_verified_cost_symbol_cohort_empty")
    return seal(
        {
            "schema": "main_ai_current_axis_candidate_v1",
            "contract": CONTRACT,
            "contract_sha256": sha(CONTRACT),
            "source_date": rolling["target_date"],
            "target_date": next_session(rolling["target_date"]),
            "candidate_id": candidate_id,
            "r3_candidate_sha256": row["candidate_sha256"],
            "rolling_sha256": rolling[HASH_FIELD],
            "manifest_sha256": manifest[HASH_FIELD],
            "control": control,
            "recommended": recommended,
            "input_reference": input_reference,
            "eligible_symbols": sorted(set(eligible_symbols)),
            "r3_candidate": row,
            "allowed_runtime_apply": False,
            **SOURCE_ONLY,
        }
    )


def validate_candidate(candidate: Mapping[str, Any]) -> None:
    check(candidate, "main_ai_current_axis_candidate_v1")
    if candidate.get("contract") != CONTRACT or candidate.get("contract_sha256") != sha(
        CONTRACT
    ):
        raise ValueError("runtime_contract_drift")
    if candidate.get("target_date") != next_session(candidate["source_date"]):
        raise ValueError("candidate_target_session_mismatch")
    if any(candidate.get(key) is not value for key, value in SOURCE_ONLY.items()):
        raise ValueError("candidate_source_only_authority_invalid")


def validate_authorization(
    *,
    authorization: Mapping[str, Any],
    candidate: Mapping[str, Any],
    now: datetime,
    first_receipt: Mapping[str, Any] | None = None,
) -> None:
    """Validate externally installed consent; never generate it from reports."""
    check(authorization, "main_ai_current_axis_operator_authorization_v1")
    current = now_kst(now)
    if authorization.get("enabled") is not True or authorization.get(
        "contract_sha256"
    ) != sha(CONTRACT):
        raise ValueError("operator_authorization_disabled_or_contract_mismatch")
    if not str(authorization.get("operator_instruction_ref") or "").strip():
        raise ValueError("operator_instruction_ref_missing")
    reviewed = now_kst(datetime.fromisoformat(authorization["reviewed_at_kst"]))
    expires = now_kst(datetime.fromisoformat(authorization["expires_at_kst"]))
    if not reviewed <= current < expires or expires - reviewed > timedelta(days=31):
        raise ValueError("operator_authorization_time_invalid")
    if authorization.get("first_candidate_sha256") == candidate[HASH_FIELD]:
        return
    if (
        authorization.get("allow_same_contract_renewal") is not True
        or not first_receipt
    ):
        raise ValueError("first_exact_candidate_approval_required")
    check(first_receipt, "main_ai_current_axis_apply_receipt_v1")
    if (
        first_receipt.get("authorization_sha256") != authorization[HASH_FIELD]
        or first_receipt.get("candidate_sha256")
        != authorization["first_candidate_sha256"]
        or first_receipt.get("status") != "applied_preopen"
        or first_receipt.get("contract_sha256") != sha(CONTRACT)
        or first_receipt.get("control_contract_sha256")
        != candidate["r3_candidate"]["current_contract_sha256"]
        or first_receipt.get("recommended_contract_sha256")
        != candidate["r3_candidate"]["recommended_contract_sha256"]
        or first_receipt.get("target_date", "") >= candidate["target_date"]
    ):
        raise ValueError("same_contract_enrollment_receipt_invalid")


def build_activation(
    *,
    candidate: Mapping[str, Any],
    rolling: Mapping[str, Any],
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    now: datetime,
    owner_conflicts: list[str],
    first_receipt: Mapping[str, Any] | None = None,
) -> dict:
    current = now_kst(now)
    validate_candidate(candidate)
    rebuilt = build_candidate(
        rolling=rolling,
        manifest=manifest,
        candidate_id=candidate["candidate_id"],
        control=candidate["control"],
        recommended=candidate["recommended"],
        input_reference=candidate["input_reference"],
    )
    if rebuilt != candidate:
        raise ValueError("candidate_source_generation_mismatch")
    if not enabled():
        raise ValueError("current_axis_explicit_enable_missing")
    if current.date().isoformat() != candidate["target_date"] or not time(
        6
    ) <= current.time() < time(8, 50):
        raise ValueError("exact_target_preopen_window_required")
    if owner_conflicts:
        raise ValueError(
            "same_stage_owner_conflict:" + ",".join(sorted(owner_conflicts))
        )
    validate_authorization(
        authorization=authorization,
        candidate=candidate,
        now=current,
        first_receipt=first_receipt,
    )
    return seal(
        {
            "schema": "main_ai_current_axis_activation_v1",
            "contract_sha256": sha(CONTRACT),
            "candidate": candidate,
            "candidate_sha256": candidate[HASH_FIELD],
            "authorization_sha256": authorization[HASH_FIELD],
            "target_date": candidate["target_date"],
            "applied_at_kst": current.isoformat(),
            "expires_at_kst": datetime.combine(
                current.date(), time(15, 30), KST
            ).isoformat(),
            "status": "applied_preopen",
            "runtime_apply_performed": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    )


def apply_receipt(activation: Mapping[str, Any]) -> dict:
    check(activation, "main_ai_current_axis_activation_v1")
    if (
        activation.get("status") != "applied_preopen"
        or activation.get("runtime_apply_performed") is not True
        or activation.get("actual_order_submitted") is not False
        or activation.get("broker_order_forbidden") is not True
    ):
        raise ValueError("activation_authority_invalid")
    candidate = activation["candidate"]
    return seal(
        {
            "schema": "main_ai_current_axis_apply_receipt_v1",
            "target_date": activation["target_date"],
            "status": "applied_preopen",
            "contract_sha256": sha(CONTRACT),
            "activation_sha256": activation[HASH_FIELD],
            "candidate_sha256": candidate[HASH_FIELD],
            "authorization_sha256": activation["authorization_sha256"],
            "control_contract_sha256": candidate["r3_candidate"][
                "current_contract_sha256"
            ],
            "recommended_contract_sha256": candidate["r3_candidate"][
                "recommended_contract_sha256"
            ],
            "actual_order_submitted": False,
        }
    )


def validate_live_activation(
    *,
    activation: Mapping[str, Any],
    receipt: Mapping[str, Any],
    authorization: Mapping[str, Any],
    now: datetime,
    first_receipt: Mapping[str, Any] | None = None,
    revoked: bool = False,
) -> dict:
    current = now_kst(now)
    if not enabled() or revoked:
        raise ValueError("disabled_or_rolled_back")
    check(activation, "main_ai_current_axis_activation_v1")
    candidate = activation["candidate"]
    validate_candidate(candidate)
    if receipt != apply_receipt(activation):
        raise ValueError("immutable_apply_receipt_mismatch")
    if (
        activation.get("contract_sha256") != sha(CONTRACT)
        or activation.get("candidate_sha256") != candidate[HASH_FIELD]
        or activation.get("authorization_sha256") != authorization.get(HASH_FIELD)
        or activation.get("target_date") != candidate["target_date"]
        or candidate["target_date"] != current.date().isoformat()
    ):
        raise ValueError("activation_scope_binding_invalid")
    applied = now_kst(datetime.fromisoformat(activation["applied_at_kst"]))
    expiry = now_kst(datetime.fromisoformat(activation["expires_at_kst"]))
    if (
        applied.date() != current.date()
        or not time(6) <= applied.time() < time(8, 50)
        or expiry != datetime.combine(current.date(), time(15, 30), KST)
        or not time(9) <= current.time() < time(15, 30)
    ):
        raise ValueError("activation_time_or_session_invalid")
    validate_authorization(
        authorization=authorization,
        candidate=candidate,
        now=current,
        first_receipt=first_receipt,
    )
    return dict(candidate)
