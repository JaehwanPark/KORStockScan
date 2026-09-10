"""Independent, exact-generation initial exit-policy approval and loading.

Research cannot choose this validator or its approval digest. The deployment
owner must separately pin the reviewed envelope and runtime-code digest. This
module supplies no default approval, risk values, broker port or enrollment.
It deliberately does not implement automatic maintenance/R6 approval.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, fields
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    FAMILY,
    EvaluationContract,
    assess_research_evidence,
    canonical_sha256,
    parse_exit_policy,
)
from src.trading.order.adaptive_exit.driver import ExecutionBounds
from src.trading.order.adaptive_exit.models import ExitPolicy, finite
from src.trading.order.adaptive_exit.source import OwnerScope
from src.utils.jsonl_io import read_json_object_strict_receipt
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
ENVELOPE_SCHEMA = "machine_adaptive_exit_initial_approval_v1"
APPLIED_SCHEMA = "machine_adaptive_exit_policy_applied_v1"
RECEIPT_SCHEMA = "machine_adaptive_exit_apply_receipt_v1"
VALIDATOR = "machine_adaptive_exit_initial_validator_v1"
PREOPEN_CUTOFF_KST = time(8, 0)
# These are lifecycle obligations, not instructions to place an order.
LIFECYCLE = {
    "new_positions_only": True,
    "maximum_extensions": 1,
    "existing_position_expiry": "retain_frozen_owner_until_terminal",
    "source_loss_policy": "no_new_order_retain_manager_and_alert",
    "halt_policy": "no_new_order_retain_manager_and_alert",
    "session_end_policy": "no_new_order_retain_manager_and_alert",
    "rollback": "disable_new_enrollment_retain_existing_owner",
}
POLICY_AUTHORITY = {
    "stage": "exit",
    "scope": "owned_sell_only",
    "new_buy": False,
    "increase_quantity": False,
    "other_owner_orders": False,
    "safety_override": False,
}


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _exact(raw, keys, reason):
    _require(isinstance(raw, dict) and set(raw) == set(keys), reason)


def _signed(raw, schema):
    _require(
        isinstance(raw, dict)
        and raw.get("schema") == schema
        and raw.get("canonical_sha256") == canonical_sha256(raw),
        "schema_or_content_hash_invalid:" + schema,
    )


def _literal_contract(raw, expected, reason):
    # Equality alone accepts 0/1 as booleans.
    _require(
        isinstance(raw, dict)
        and raw == expected
        and all(type(raw[k]) is type(v) for k, v in expected.items()),
        reason,
    )


def aware_kst(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    _require(
        isinstance(value, datetime) and value.utcoffset() is not None,
        "aware_time_required",
    )
    return value.astimezone(KST)


def read_plain(path: Path, *, generation=None):
    """Current authority must be a single regular, non-aliased generation."""
    receipt = read_json_object_strict_receipt(path, generation=generation)
    _require(
        receipt.logical_path == path.absolute()
        and receipt.physical_path == receipt.logical_path
        and receipt.generation_census
        == ((receipt.logical_path.name, receipt.physical_identity),),
        "plain_single_generation_required",
    )
    return receipt


def validate_envelope(envelope, *, expected_sha256, runtime_code_sha256):
    """No candidate-supplied registry, validator, floor or authority fallback."""
    _exact(
        envelope,
        {
            "schema",
            "family",
            "validator",
            "phase",
            "approval_id",
            "source_date",
            "target_date",
            "source_report_sha256",
            "source_child_sha256",
            "runtime_code_sha256",
            "valid_from",
            "valid_until",
            "lifecycle",
            "policy_authority",
            "scopes",
            "canonical_sha256",
        },
        "approval_envelope_fields_invalid",
    )
    _signed(envelope, ENVELOPE_SCHEMA)
    _require(
        _digest(expected_sha256)
        and expected_sha256 == envelope["canonical_sha256"]
        and _digest(runtime_code_sha256)
        and envelope["runtime_code_sha256"] == runtime_code_sha256,
        "independent_approval_or_code_pin_mismatch",
    )
    _require(
        envelope["family"] == FAMILY
        and envelope["validator"] == VALIDATOR
        and envelope["phase"] == "initial_canary"
        and isinstance(envelope["approval_id"], str)
        and bool(envelope["approval_id"].strip())
        and _digest(envelope["source_report_sha256"])
        and _digest(envelope["source_child_sha256"]),
        "initial_family_approval_required",
    )
    _literal_contract(envelope["lifecycle"], LIFECYCLE, "lifecycle_contract_invalid")
    _literal_contract(
        envelope["policy_authority"], POLICY_AUTHORITY, "owned_exit_authority_invalid"
    )
    source, target = [
        date.fromisoformat(envelope[k]) for k in ("source_date", "target_date")
    ]
    # Bound iteration by the supplied target, rather than searching indefinitely.
    _require(
        envelope["source_date"] == source.isoformat()
        and envelope["target_date"] == target.isoformat()
        and date(2026, 6, 5) <= source < target
        and is_krx_trading_day(source)
        and is_krx_trading_day(target)
        and not any(
            is_krx_trading_day(source + timedelta(days=i))
            for i in range(1, (target - source).days)
        ),
        "exact_next_trading_date_required",
    )
    start, end = [aware_kst(envelope[k]) for k in ("valid_from", "valid_until")]
    _require(
        start < end and start.date() == end.date() == target,
        "enrollment_window_invalid",
    )
    _require(
        isinstance(envelope["scopes"], dict) and envelope["scopes"],
        "approved_scopes_required",
    )
    for key, scope in envelope["scopes"].items():
        _require(isinstance(key, str), "scope_key_invalid")
        try:
            OwnerScope(*key.split("|"))
        except (TypeError, AttributeError) as exc:
            raise ValueError("scope_key_invalid") from exc
        _exact(
            scope,
            {
                "policy",
                "candidate_sha256",
                "entry_policy_hashes",
                "evaluation",
                "execution_bounds",
                "model_ids",
                "execution_cost_guard",
            },
            "scope_approval_fields_invalid",
        )
        policy = parse_exit_policy(scope["policy"])
        cost = scope["execution_cost_guard"]
        _exact(
            cost,
            {"basis", "source_sha256", "round_trip_cost_pct"},
            "execution_cost_guard_required",
        )
        _require(
            cost["basis"] == "independently_approved_execution_cost_guard"
            and _digest(cost["source_sha256"])
            and finite(cost["round_trip_cost_pct"])
            and cost["round_trip_cost_pct"] > 0,
            "execution_cost_guard_invalid",
        )
        _require(
            policy.scope_key == key and _digest(scope["candidate_sha256"]),
            "scope_policy_binding_invalid",
        )
        entries, models = scope["entry_policy_hashes"], scope["model_ids"]
        _require(
            isinstance(entries, list)
            and entries
            and all(_digest(v) for v in entries)
            and len(entries) == len(set(entries)),
            "entry_policy_bindings_required",
        )
        _require(
            isinstance(models, list)
            and len(models) == 2
            and all(isinstance(v, str) and v.strip() for v in models)
            and models[0] != models[1],
            "independent_models_required",
        )
        _exact(
            scope["execution_bounds"],
            {f.name for f in fields(ExecutionBounds)},
            "execution_bounds_fields_invalid",
        )
        ExecutionBounds(**scope["execution_bounds"])
        contract = evaluation_contract(scope, scope_key=key)
        _require(
            contract.holdout_end == envelope["source_date"],
            "evaluation_source_date_mismatch",
        )
    return envelope


def evaluation_contract(scope, *, scope_key):
    raw = scope["evaluation"]
    _exact(
        raw,
        {f.name for f in fields(EvaluationContract)}
        - {"contract_hash", "scope_key", "policy_hash"},
        "independent_evaluation_fields_invalid",
    )
    values = dict(raw, scope_key=scope_key, policy_hash=scope["policy"]["policy_hash"])
    return EvaluationContract(**values, contract_hash=canonical_sha256(values))


def validate_selection(selection, *, scope_key, approved_scope, source_date):
    _exact(
        selection,
        {"candidate", "base_evidence", "stress_evidence"},
        "selection_fields_invalid",
    )
    candidate = selection["candidate"]
    _signed(candidate, "machine_adaptive_exit_candidate_v1")
    _literal_contract(
        candidate.get("authority"), AUTHORITY, "candidate_source_only_required"
    )
    native_body = {
        k: v
        for k, v in candidate.items()
        if k not in ("canonical_sha256", "recommendation_id")
    }
    _require(
        candidate.get("recommendation_id")
        == "adaptive-exit:" + canonical_sha256(native_body)[:32]
        and candidate["canonical_sha256"] == approved_scope["candidate_sha256"]
        and candidate.get("family") == FAMILY
        and candidate.get("scope_key") == scope_key
        and candidate.get("source_date") == source_date
        and candidate.get("policy") == approved_scope["policy"]
        and candidate.get("decision") == "research_ready"
        and candidate.get("errors") == []
        and candidate.get("eligible_for_next_preopen") is False,
        "approved_native_candidate_required",
    )
    contract = evaluation_contract(approved_scope, scope_key=scope_key)
    _require(
        candidate.get("evaluation_contract_hash") == contract.contract_hash,
        "candidate_evaluation_mismatch",
    )
    for slot, digest_key, model in zip(
        ("base_evidence", "stress_evidence"),
        ("evidence_hash", "stress_evidence_hash"),
        approved_scope["model_ids"],
    ):
        evidence = selection[slot]
        _require(isinstance(evidence, dict), "evidence_object_required")
        result = assess_research_evidence(evidence, contract)
        _require(
            not result["errors"],
            "economic_evidence_rejected:" + ",".join(result["errors"]),
        )
        _require(
            evidence["canonical_sha256"] == candidate.get(digest_key)
            and evidence.get("model_id") == model,
            "native_evidence_binding_mismatch",
        )
    return selection


def validate_applied(payload, *, envelope, expected_sha256, runtime_code_sha256):
    validate_envelope(
        envelope,
        expected_sha256=expected_sha256,
        runtime_code_sha256=runtime_code_sha256,
    )
    _exact(
        payload,
        {
            "schema",
            "family",
            "envelope_sha256",
            "source_date",
            "target_date",
            "source_report_sha256",
            "source_child_sha256",
            "selections",
            "publication_receipt",
            "canonical_sha256",
        },
        "applied_policy_fields_invalid",
    )
    _signed(payload, APPLIED_SCHEMA)
    for key in (
        "family",
        "source_date",
        "target_date",
        "source_report_sha256",
        "source_child_sha256",
    ):
        _require(
            payload[key] == envelope[key], "applied_approval_binding_mismatch:" + key
        )
    _require(payload["envelope_sha256"] == expected_sha256, "applied_envelope_mismatch")
    selected = payload["selections"]
    _require(
        isinstance(selected, dict) and set(selected) == set(envelope["scopes"]),
        "selected_scope_conservation_invalid",
    )
    for key, row in selected.items():
        validate_selection(
            row,
            scope_key=key,
            approved_scope=envelope["scopes"][key],
            source_date=envelope["source_date"],
        )
    receipt = payload["publication_receipt"]
    optional_ledger_fields = set()
    if isinstance(receipt, dict) and "approval_ledger_receipt" in receipt:
        optional_ledger_fields.add("approval_ledger_receipt")
        ledger = receipt["approval_ledger_receipt"]
        _exact(
            ledger,
            {"queue_byte_sha256", "native_handoffs", "canonical_sha256"},
            "initial_ledger_receipt_fields_invalid",
        )
        _require(
            _digest(ledger["queue_byte_sha256"])
            and ledger["canonical_sha256"] == canonical_sha256(ledger)
            and isinstance(ledger["native_handoffs"], dict)
            and set(ledger["native_handoffs"])
            == {row["candidate"]["recommendation_id"] for row in selected.values()},
            "initial_ledger_receipt_binding_invalid",
        )
        for binding in ledger["native_handoffs"].values():
            _exact(
                binding,
                {"candidate_sha256", "decision_byte_sha256", "handoff_byte_sha256"},
                "initial_ledger_native_binding_invalid",
            )
            _require(
                all(_digest(v) for v in binding.values()),
                "initial_ledger_native_hash_invalid",
            )
    _exact(
        receipt,
        {
            "schema",
            "validator",
            "envelope_sha256",
            "selection_sha256",
            "published_at",
            "authority",
            "status",
            "canonical_sha256",
        }
        | optional_ledger_fields,
        "publication_receipt_fields_invalid",
    )
    _signed(receipt, RECEIPT_SCHEMA)
    _literal_contract(
        receipt["authority"], AUTHORITY, "publisher_broker_authority_forbidden"
    )
    _require(
        receipt["validator"] == VALIDATOR
        and receipt["status"] == "published_not_loaded"
        and receipt["envelope_sha256"] == expected_sha256
        and receipt["selection_sha256"] == canonical_sha256(selected),
        "publication_binding_invalid",
    )
    published = aware_kst(receipt["published_at"])
    _require(
        date.fromisoformat(envelope["target_date"]) == published.date()
        and published.time() < PREOPEN_CUTOFF_KST
        and published < aware_kst(envelope["valid_from"]),
        "publication_window_invalid",
    )
    return payload


@dataclass(frozen=True)
class LoadedExitPolicy:
    policy: ExitPolicy
    bounds: ExecutionBounds
    envelope_sha256: str
    applied_sha256: str
    publication_receipt_sha256: str
    entry_policy_hash: str
    valid_from: str
    valid_until: str


def load_for_new_position(
    *,
    policy_path: Path,
    envelope_path: Path,
    expected_envelope_sha256: str,
    runtime_code_sha256: str,
    scope_key: str,
    entry_policy_hash: str,
    now: datetime,
):
    """Read-only selection; the original owner still supplies all order guards.

    No latest-file fallback, stale-policy carry, old-position adoption or state
    write. Existing enrolled sessions retain their own frozen binding instead
    of calling this date-limited new-admission loader.
    """
    envelope_read = read_plain(envelope_path)
    envelope = envelope_read.payload
    policy_read = read_plain(policy_path)
    payload = policy_read.payload
    validate_applied(
        payload,
        envelope=envelope,
        expected_sha256=expected_envelope_sha256,
        runtime_code_sha256=runtime_code_sha256,
    )
    current = aware_kst(now)
    _require(
        aware_kst(envelope["valid_from"])
        <= current
        < aware_kst(envelope["valid_until"]),
        "new_enrollment_outside_window",
    )
    scope = envelope["scopes"].get(scope_key)
    _require(
        scope is not None and entry_policy_hash in scope["entry_policy_hashes"],
        "owner_or_entry_policy_not_approved",
    )
    # A changed/revoked authority during validation is not a successful load.
    _require(read_plain(envelope_path) == envelope_read, "approval_changed_during_load")
    _require(read_plain(policy_path) == policy_read, "policy_changed_during_load")
    return LoadedExitPolicy(
        parse_exit_policy(deepcopy(scope["policy"])),
        ExecutionBounds(**scope["execution_bounds"]),
        expected_envelope_sha256,
        payload["canonical_sha256"],
        payload["publication_receipt"]["canonical_sha256"],
        entry_policy_hash,
        envelope["valid_from"],
        envelope["valid_until"],
    )
