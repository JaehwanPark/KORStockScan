"""Initial machine-first policy and exact-scope postclose succession for main.

This is a policy publisher/consumer, not another market-data producer. Initial
operator adoption is distinct from evidence-qualified threshold promotion.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_15_2_BALANCED_BOUNDED_RECOVERY_PROMPT_VERSION,
    decision_quality_balanced_entry_system_prompt,
    ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
    ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION,
    ENTRY_MACHINE_AUXILIARY_COMPACT_V1_PROMPT_VERSION,
    ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
    FROZEN_COMPACT_V2_VARIANTS,
    machine_auxiliary_compact_entry_system_prompt,
)
from src.engine.scalping.entry_setup_evidence import (
    MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
    MECHANISTIC_PRIMARY_ROLE_CONTRACT,
    validate_mechanistic_entry_threshold_policy,
)
from src.utils.market_day import is_krx_trading_day

SCHEMA = "main_mechanistic_entry_runtime_policy_v1"
KST = ZoneInfo("Asia/Seoul")
COHORT = ["KRX", "KRX_REGULAR"]
# New dated bundles are compact and self-contained.  Existing V2.15.2 bundles
# remain readable so a running PID never loses its frozen policy merely because
# the publisher is upgraded.
LEGACY_AI_VERSION = DECISION_QUALITY_V2_15_2_BALANCED_BOUNDED_RECOVERY_PROMPT_VERSION
LEGACY_COMPACT_AI_VERSION = ENTRY_MACHINE_AUXILIARY_COMPACT_V1_PROMPT_VERSION
AI_VERSION = ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION
LEGACY_AI_VARIANT = "machine_first_pass_veto_v2"
LEGACY_COMPACT_AI_VARIANT = "machine_first_compact_pass_veto_v1"
AI_VARIANT = "machine_first_compact_pass_veto_v3"
COMPACT_AI_VARIANTS = {
    **FROZEN_COMPACT_V2_VARIANTS,
    AI_VERSION: AI_VARIANT,
    ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION: (
        "machine_first_compact_opportunity_pass_veto_v2"
    ),
    ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION: (
        "machine_first_compact_risk_pass_veto_v2"
    ),
}
AI_ADDENDUM = """
Machine-first binding risk screen (this role supersedes legacy veto wording):
The deterministic machine has already assessed this exact current setup.
Use mechanistic_entry_assessment for its action, reason and bound evidence.
You have binding PASS/VETO authority over a machine-selected entry point.
PASS means the current supported setup may proceed to final execution guards.
VETO rejects this point, never a permanent symbol ban. Cite current adverse
fact IDs and their matching risk codes; do not target a BUY quota or agreement.
LIQUIDITY_FRAGILE, ADVERSE_TAPE or REWARD_RISK_WEAK may justify VETO only with
bound adverse facts and acknowledged supporting facts. Weigh compensating
evidence; a bounded risk is not automatically a veto. Missing confirmation
alone or missing optional data is not a VETO reason. Use CAUTION for an
unresolved recheck, INSUFFICIENT only for a supported source gap; neither
authorizes exposure. You cannot promote machine RECHECK/BLOCK to an entry.
Historical policy context is diagnostic, not present evidence or a forecast.
Do not use historical winning outcomes to manufacture current positive facts.
Do not require another pullback when a supported continuation is already ready.
Hard source, freshness, execution and order guards remain authoritative.
""".strip()


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
    ).hexdigest()


def root(data_root: Path) -> Path:
    return data_root / "runtime" / "mechanistic_entry_policy"


def next_target(source_date: str) -> str:
    day = date.fromisoformat(source_date)
    for _ in range(15):
        day += timedelta(days=1)
        if is_krx_trading_day(day):
            return day.isoformat()
    raise ValueError("next_trading_date_unresolved")


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("policy_object_required")
    return value


@lru_cache(maxsize=32)
def _source_hash(path: str, signature: tuple) -> str:
    source = Path(path)
    observed = hashlib.sha256(source.read_bytes()).hexdigest()
    if _signature(source) != signature:
        raise ValueError("machine_policy_source_changed_during_read")
    return observed


def _signature(path: Path) -> tuple:
    stat = path.stat()
    return (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def validate(bundle: dict, *, target_date: str) -> None:
    if (
        bundle.get("schema") != SCHEMA
        or bundle.get("target_date") != target_date
        or bundle.get("cohort") != COHORT
        or bundle.get("role_contract") != MECHANISTIC_PRIMARY_ROLE_CONTRACT
        or bundle.get("bundle_sha256")
        != digest({k: v for k, v in bundle.items() if k != "bundle_sha256"})
        or bundle.get("adoption_basis")
        != "user_authorized_initial_policy_with_guarded_succession"
        or bundle.get("actual_order_submitted") is not False
        or bundle.get("hard_guards_unchanged") is not True
    ):
        raise ValueError("machine_bundle_contract_invalid")
    source = str(bundle.get("source_date") or "")
    if any(
        not isinstance(bundle.get(key), str)
        or re.fullmatch(r"[0-9a-f]{64}", bundle[key]) is None
        for key in ("source_file_sha256", "source_artifact_sha256", "bundle_sha256")
    ):
        raise ValueError("machine_bundle_hash_format_invalid")
    if source < "2026-06-05" or next_target(source) != target_date:
        raise ValueError("machine_bundle_date_invalid")
    if validate_mechanistic_entry_threshold_policy(bundle.get("machine_policy")):
        raise ValueError("machine_bundle_threshold_invalid")
    if (
        "hierarchy" in bundle["machine_policy"]
        and bundle.get("hierarchy_adopted") is not True
    ):
        raise ValueError("machine_hierarchy_adoption_missing")
    ai = bundle.get("ai_policy") or {}
    if not isinstance(ai, dict):
        raise ValueError("machine_bundle_ai_policy_invalid")
    if not _validate_ai_policy(ai, bundle.get("historical_context")):
        raise ValueError("machine_bundle_ai_policy_invalid")
    scopes = bundle.get("scope_policies")
    if bundle.get("all_continuous_adopted") is True:
        from src.engine.scalping.entry_setup_scalping_rollout import (
            AUTO_PROMOTION_SCOPES,
        )

        if not isinstance(scopes, dict) or set(scopes) != set(AUTO_PROMOTION_SCOPES):
            raise ValueError("machine_bundle_scope_coverage_invalid")
        for scope, scoped in scopes.items():
            if not isinstance(scoped, dict):
                raise ValueError("machine_scope_policy_invalid")
            policy, sai, context = (
                scoped.get("machine_policy"),
                scoped.get("ai_policy"),
                scoped.get("historical_context"),
            )
            if (
                validate_mechanistic_entry_threshold_policy(policy)
                or not isinstance(sai, dict)
                or not isinstance(context, dict)
            ):
                raise ValueError("machine_scope_policy_invalid")
            if context.get("scope") != scope or not _validate_ai_policy(sai, context):
                raise ValueError("machine_scope_ai_binding_invalid")
            if policy.get("hierarchy") and (
                bundle.get("hierarchy_adopted") is not True
                or any(
                    f"{r['match']['venue']}|{r['match']['session_bucket']}" != scope
                    for r in policy["hierarchy"]["rules"]
                )
            ):
                raise ValueError("machine_scope_rule_leak")
        if scopes["KRX|KRX_REGULAR"]["machine_policy"] != bundle["machine_policy"]:
            raise ValueError("machine_scope_legacy_projection_mismatch")
    elif scopes is not None:
        raise ValueError("machine_scope_adoption_missing")


def for_cohort(bundle: dict | None, cohort: tuple[str, str]) -> dict | None:
    """Project a validated bundle without borrowing another market's child."""
    if bundle is None:
        return None
    if bundle.get("all_continuous_adopted") is True:
        scoped = bundle["scope_policies"].get("|".join(cohort))
        return {**bundle, **scoped, "selected_scope": list(cohort)} if scoped else None
    return bundle if list(cohort) == COHORT else None


def auxiliary_prompt(context: object) -> str:
    """Legacy V2.15.2 composer retained for frozen policy readers only."""
    hierarchy_role = (
        "\nA validated hierarchical machine trigger can resolve a legacy setup "
        "WAIT_CONFIRMATION. Do not require the common READY label again. "
        "Assess the selected group, effective symbol thresholds and exact micro "
        "receipt in mechanistic_entry_assessment. For PASS, acknowledge current "
        "supporting facts and every bound adverse fact; trusted micro buy flow "
        "and positive price response may support the validated group trigger. "
        "Missing required micro is a machine RECHECK, never permission to invent "
        "support. Your fact-bound VETO and all final guards remain binding.\n"
        if isinstance(context, dict) and context.get("hierarchy_role_version") == "v1"
        else ""
    )
    return (
        decision_quality_balanced_entry_system_prompt("entry", bounded_recovery=True)
        + "\n\n"
        + AI_ADDENDUM
        + hierarchy_role
        + "\n\nHistorical policy context (not current facts):\n"
        + json.dumps(context, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    )


def compact_auxiliary_prompt(
    context: object | None = None, *, prompt_version: str = AI_VERSION
) -> str:
    """Single runtime/offline prompt; context stays in the user fact payload."""

    del context
    return machine_auxiliary_compact_entry_system_prompt(
        "entry", prompt_version=prompt_version
    )


def compact_prompt_variant(prompt_version: str) -> str:
    if prompt_version == LEGACY_COMPACT_AI_VERSION:
        return LEGACY_COMPACT_AI_VARIANT
    try:
        return COMPACT_AI_VARIANTS[prompt_version]
    except KeyError as exc:
        raise ValueError("unsupported_compact_prompt_version") from exc


def _validate_ai_policy(ai: object, context: object) -> bool:
    if not isinstance(ai, dict) or ai.get("system_prompt_sha256") != digest(
        ai.get("system_prompt")
    ):
        return False
    version = ai.get("prompt_version")
    if version in COMPACT_AI_VARIANTS:
        return ai.get("variant") == compact_prompt_variant(version) and ai.get(
            "system_prompt"
        ) == compact_auxiliary_prompt(context, prompt_version=version)
    if version == LEGACY_COMPACT_AI_VERSION:
        return ai.get("variant") == LEGACY_COMPACT_AI_VARIANT and ai.get(
            "system_prompt"
        ) == compact_auxiliary_prompt(context, prompt_version=version)
    if version == LEGACY_AI_VERSION:
        return ai.get("variant") == LEGACY_AI_VARIANT and ai.get(
            "system_prompt"
        ) == auxiliary_prompt(context)
    return False


def compact_outcome_counts_valid(economic: dict) -> bool:
    """Reconcile every published subtotal against the detailed outcome map."""
    counts = economic.get("verdict_x_action_neutral_outcome_counts")
    if not isinstance(counts, dict) or any(
        not isinstance(key, str)
        or key.partition("|")[0] not in {"PASS", "VETO"}
        or "|" not in key
        or type(value) is not int
        or value < 0
        for key, value in counts.items()
    ):
        return False
    expected = {
        "economic_eligible_count": sum(counts.values()),
        "evaluable_pass_count": sum(
            value for key, value in counts.items() if key.startswith("PASS|")
        ),
        "evaluable_veto_count": sum(
            value for key, value in counts.items() if key.startswith("VETO|")
        ),
        "missed_profit_veto_count": counts.get("VETO|CLEAN_FAST_PROFIT", 0),
        "dangerous_pass_count": sum(
            counts.get(key, 0)
            for key in (
                "PASS|CLEAN_FAST_LOSS_OR_ADVERSE",
                "PASS|PROFIT_AFTER_DEEP_ADVERSE",
            )
        ),
    }
    return all(
        type(economic.get(key)) is int and economic[key] == value
        for key, value in expected.items()
    )


def compact_economic_direction(economic: dict) -> str:
    """Bounded feedback direction; amounts are CF evidence, not candidate uplift."""
    import math

    carry = "carry_balanced_compact_contract"
    for key in (
        "economic_eligible_count",
        "evaluable_pass_count",
        "evaluable_veto_count",
        "material_tail_pass_count",
        "missed_profit_veto_count",
        "dangerous_pass_count",
    ):
        if type(economic.get(key)) is not int or economic[key] < 0:
            return carry
    for key in ("missed_veto_rate", "dangerous_pass_rate"):
        value = economic.get(key)
        if value is not None and (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or not 0 <= value <= 1
        ):
            return carry
    amounts = [
        economic.get("missed_profit_veto_net_sum_pct"),
        economic.get("dangerous_pass_loss_sum_pct"),
    ]
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or value < 0
        for value in amounts
    ):
        return carry
    if economic.get("economic_eligible_count", 0) < 20:
        return carry
    if (
        economic.get("evaluable_pass_count", 0) >= 5
        and economic.get("material_tail_pass_count", 0) > 0
    ):
        return "select_material_risk_specificity_variant"
    missed, loss = amounts
    if (
        missed > loss
        and economic.get("evaluable_veto_count", 0) >= 5
        and economic.get("missed_profit_veto_count", 0) >= 3
        and economic.get("missed_veto_rate") is not None
        and economic["missed_veto_rate"] >= 0.25
    ):
        return "select_opportunity_preservation_variant"
    if (
        loss > missed
        and economic.get("evaluable_pass_count", 0) >= 5
        and economic.get("dangerous_pass_count", 0) >= 3
        and economic.get("dangerous_pass_rate") is not None
        and economic["dangerous_pass_rate"] >= 0.25
    ):
        return "select_material_risk_specificity_variant"
    return carry


def _selected_compact_prompt_version(source: dict, previous: dict | None) -> str:
    """Consume only #82's exact-incumbent bounded automatic selection."""

    previous_version = str(
        ((previous or {}).get("ai_policy") or {}).get("prompt_version") or ""
    )
    # The reviewed citation correction is an explicit code migration,
    # not a performance claim. Later changes require #82's exact-version gate.
    if previous_version in {
        "",
        LEGACY_AI_VERSION,
        LEGACY_COMPACT_AI_VERSION,
        *FROZEN_COMPACT_V2_VARIANTS,
    }:
        return AI_VERSION
    case_table = (source.get("hierarchical_entry_quality") or {}).get(
        "machine_decision_case_table"
    ) or {}
    outcomes = case_table.get("compact_auxiliary_screen_outcomes") or {}
    selection = outcomes.get("automatic_successor_selection") or {}
    selected = str(selection.get("selected_prompt_version") or "")
    economic = outcomes.get("economic_contract") or {}
    source_receipt = case_table.get("machine_ai_natural_source_receipt") or {}
    if not compact_outcome_counts_valid(economic):
        return previous_version
    # Publication precedes the final strict verifier. Validate the evidence
    # here as well, before creating a future policy from malformed aggregates.
    count_fields = (
        "screened_total",
        "economic_eligible_count",
        "evaluable_veto_count",
        "evaluable_pass_count",
        "missed_profit_veto_count",
        "dangerous_pass_count",
        "material_tail_pass_count",
    )
    if any(
        type(economic.get(key)) is not int or economic[key] < 0 for key in count_fields
    ):
        return previous_version
    excluded = economic.get("exclusion_counts")
    counts = economic.get("verdict_x_action_neutral_outcome_counts")
    if any(
        not isinstance(mapping, dict)
        or any(type(value) is not int or value < 0 for value in mapping.values())
        for mapping in (excluded, counts)
    ):
        return previous_version
    veto = economic["evaluable_veto_count"]
    passed = economic["evaluable_pass_count"]
    if (
        source_receipt.get("tuning_input_allowed") is not True
        or (case_table.get("compact_auxiliary_policy_measurement") or {}).get(
            "measurement_allowed"
        )
        is not True
        or economic.get("denominator_preserved") is not True
        or economic["screened_total"]
        != economic["economic_eligible_count"] + sum(excluded.values())
        or sum(counts.values()) != economic["economic_eligible_count"]
        or economic["missed_profit_veto_count"] > veto
        or economic["dangerous_pass_count"] > passed
        or economic["material_tail_pass_count"] > passed
        or economic.get("missed_veto_rate")
        != (economic["missed_profit_veto_count"] / veto if veto else None)
        or economic.get("dangerous_pass_rate")
        != (economic["dangerous_pass_count"] / passed if passed else None)
    ):
        return previous_version
    try:
        eligible_count = int(economic.get("economic_eligible_count") or 0)
        veto_count = int(economic.get("evaluable_veto_count") or 0)
        pass_count = int(economic.get("evaluable_pass_count") or 0)
        material_tail_loss_pct = float(economic.get("material_tail_loss_pct"))
        minimum_count = int(selection.get("minimum_economic_eligible_count") or 0)
        minimum_error_count = int(selection.get("minimum_error_count") or 0)
        minimum_denominator = int(selection.get("minimum_relevant_denominator") or 0)
        minimum_error_rate = float(selection.get("minimum_error_rate"))
    except (TypeError, ValueError):
        return previous_version
    expected = previous_version
    economic_direction = compact_economic_direction(economic)
    if economic_direction == "select_material_risk_specificity_variant":
        expected = ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION
    elif economic_direction == "select_opportunity_preservation_variant":
        expected = ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION
    if (
        selection.get("eligible") is True
        and selection.get("recommendation_id")
        == "compact_auxiliary_prompt_automatic_successor_v2"
        and selection.get("contract_version")
        == "compact_auxiliary_economic_selection_v2"
        and selection.get("runtime_effect") is True
        and selection.get("allowed_runtime_apply") is True
        and selection.get("selection_contract")
        == "bounded_registered_variant_exact_incumbent_only_no_freeform_edit"
        and economic.get("schema") == "compact_auxiliary_economic_selection_v2"
        and economic.get("counterfactual_not_realized_pnl") is True
        and economic.get("missing_economics_imputed") is False
        and material_tail_loss_pct == -1.0
        and selection.get("source_manifest_sha256")
        == source_receipt.get("source_manifest_sha256")
        and selection.get("history_receipts_sha256")
        == source_receipt.get("compact_history_receipts_sha256")
        and isinstance(selection.get("source_manifest_sha256"), str)
        and len(selection.get("source_manifest_sha256") or "") == 64
        and selection.get("economic_outcome_counts_sha256")
        == digest(economic.get("verdict_x_action_neutral_outcome_counts") or {})
        and selection.get("economic_outcome_counts_sha256")
        == economic.get("verdict_x_action_neutral_outcome_counts_sha256")
        and eligible_count >= minimum_count
        and minimum_count == 20
        and minimum_error_count == 3
        and minimum_denominator == 5
        and minimum_error_rate == 0.25
        and veto_count + pass_count == eligible_count
        and selection.get("incumbent_prompt_version") == previous_version
        and selected == expected
        and selected in COMPACT_AI_VARIANTS
    ):
        return selected
    return previous_version if previous_version in COMPACT_AI_VARIANTS else AI_VERSION


def load(*, data_root: Path, target_date: str) -> dict | None:
    path = root(data_root) / f"policy_{target_date}.json"
    if not path.is_file():
        return None
    bundle = _read(path)
    validate(bundle, target_date=target_date)
    source_path = root(data_root) / "sources" / f"{bundle['source_file_sha256']}.json"
    if (
        _source_hash(str(source_path), _signature(source_path))
        != bundle["source_file_sha256"]
    ):
        raise ValueError("machine_bundle_source_hash_invalid")
    return bundle


def load_effective(*, data_root: Path, target_date: str) -> dict | None:
    """A missing new generation retains the explicitly adopted incumbent.

    Do not relabel the original policy date or hide a corrupt dated policy.
    Market/source freshness is still checked independently at every decision.
    """
    exact = load(data_root=data_root, target_date=target_date)
    if exact is not None:
        return exact
    paths = sorted(
        p
        for p in root(data_root).glob("policy_????-??-??.json")
        if p.stem[7:] < target_date
    )
    return load(data_root=data_root, target_date=paths[-1].stem[7:]) if paths else None


def publish(
    source_path: Path,
    *,
    data_root: Path,
    bootstrap: bool = False,
    replace_initial_role: bool = False,
    adopt_hierarchy: bool = False,
    now: datetime | None = None,
    adopt_all_continuous: bool = False,
) -> dict | None:
    """Refresh a future date until PREOPEN, then retain its frozen generation.

    Only explicit bootstrap creates the first policy. Subsequent canonical
    calibration writes update or carry it through this same bounded publisher.
    No provider calls, env writes, orders or process restarts occur here.
    """
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping.entry_setup_live_policy import (
        _mechanistic_primary_activation_projection,
    )

    policy_root = root(data_root)
    if not bootstrap and not policy_root.is_dir():
        return None
    source = _read(source_path)
    if (
        not calibration._artifact_content_sha256_valid(source)
        or source.get("schema") != calibration.SCHEMA
        or source.get("clean_tuning_baseline_date") != "2026-06-05"
    ):
        raise ValueError("machine_policy_calibration_source_invalid")
    source_date = str(source["target_date"])
    target = next_target(source_date)
    current = (now or datetime.now(KST)).astimezone(KST)
    if source_date < "2026-06-05" or source_date > current.date().isoformat():
        raise ValueError("machine_policy_source_date_invalid")
    policy_root.mkdir(parents=True, exist_ok=True)
    with (policy_root / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            existing = load(data_root=data_root, target_date=target)
        except ValueError:
            # Explicit, pre-activation replacement of the unlaunched advisory
            # seed only. Daily automation cannot migrate an authority contract.
            existing = _read(policy_root / f"policy_{target}.json")
            old_ai = existing.get("ai_policy") or {}
            if (
                not replace_initial_role
                or current
                >= datetime.fromisoformat(target + "T07:35:00").replace(tzinfo=KST)
                or existing.get("machine_disposition")
                != "initial_policy_not_performance_promotion"
                or existing.get("role_contract", {}).get("ai_role")
                != "auxiliary_advisory_no_veto_no_override"
                or existing.get("role_contract", {}).get("ai_can_veto_entry")
                is not False
                or old_ai.get("variant") != "machine_first_auxiliary_v1"
                or old_ai.get("system_prompt_sha256")
                != digest(old_ai.get("system_prompt"))
                or existing.get("bundle_sha256")
                != digest({k: v for k, v in existing.items() if k != "bundle_sha256"})
            ):
                raise ValueError("initial_role_replacement_not_authorized")
            source_file = (
                policy_root / "sources" / f"{existing['source_file_sha256']}.json"
            )
            if (
                _source_hash(str(source_file), _signature(source_file))
                != existing["source_file_sha256"]
            ):
                raise ValueError("initial_role_replacement_source_invalid")
            reviewed = copy.deepcopy(existing)
            reviewed["role_contract"] = copy.deepcopy(MECHANISTIC_PRIMARY_ROLE_CONTRACT)
            reviewed["ai_policy"].update(
                prompt_version=AI_VERSION,
                variant=AI_VARIANT,
                system_prompt=compact_auxiliary_prompt(
                    reviewed.get("historical_context")
                ),
            )
            reviewed["ai_policy"]["system_prompt_sha256"] = digest(
                reviewed["ai_policy"]["system_prompt"]
            )
            reviewed["bundle_sha256"] = digest(
                {k: v for k, v in reviewed.items() if k != "bundle_sha256"}
            )
            validate(reviewed, target_date=target)
        evaluation_incumbent = (
            load_effective(data_root=data_root, target_date=source_date) or existing
        )
        selected_ai_version = _selected_compact_prompt_version(
            source, evaluation_incumbent
        )
        if (
            existing is not None
            and existing.get("role_contract") == MECHANISTIC_PRIMARY_ROLE_CONTRACT
            and existing["source_artifact_sha256"] == source["artifact_content_sha256"]
            and existing.get("ai_policy", {}).get("prompt_version")
            == selected_ai_version
            and (not adopt_hierarchy or existing.get("hierarchy_adopted") is True)
            and (
                not adopt_all_continuous
                or existing.get("all_continuous_adopted") is True
            )
        ):
            return existing
        # A late postclose recovery may publish before PREOPEN, never intraday.
        if target < current.date().isoformat() or (
            target == current.date().isoformat()
            and current.hour * 60 + current.minute >= 7 * 60 + 35
        ):
            if existing is not None:
                return existing
            raise ValueError("machine_policy_publication_window_closed")
        prior_paths = sorted(policy_root.glob("policy_????-??-??.json"))
        prior_paths = [p for p in prior_paths if p.stem[7:] < target]
        previous = existing or (
            load(data_root=data_root, target_date=prior_paths[-1].stem[7:])
            if prior_paths
            else None
        )
        selected_ai_version = _selected_compact_prompt_version(
            source, evaluation_incumbent or previous
        )
        if previous is None and not bootstrap:
            raise ValueError("machine_policy_bootstrap_authority_missing")
        # Freeze one parsed source generation in the existing writer's exact
        # serialization. Candidate validation and later loading use this copy.
        source_hash = hashlib.sha256(
            (json.dumps(source, ensure_ascii=False, indent=2) + "\n").encode()
        ).hexdigest()
        snapshot = policy_root / "sources" / f"{source_hash}.json"
        if not snapshot.is_file():
            calibration._atomic_write_json(snapshot, source)
        if _source_hash(str(snapshot), _signature(snapshot)) != source_hash:
            raise ValueError("machine_policy_source_snapshot_corrupt")
        projection, errors = _mechanistic_primary_activation_projection(
            source_date, source_path=snapshot
        )
        if errors:
            raise ValueError("machine_policy_challenger_invalid:" + ",".join(errors))
        machine = copy.deepcopy(
            previous["machine_policy"]
            if previous
            else MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
        )
        disposition = (
            "incumbent_carried"
            if previous
            else "initial_policy_not_performance_promotion"
        )
        if (
            existing
            and existing.get("role_contract") != MECHANISTIC_PRIMARY_ROLE_CONTRACT
        ):
            disposition = "initial_role_corrected_not_performance_promotion"
        if projection is not None:
            parent_hash = projection.get("incumbent_machine_policy_sha256")
            if parent_hash is not None and parent_hash != digest(machine):
                disposition = "candidate_parent_changed_revalidation_required"
            else:
                machine = projection["threshold_policy"]
                disposition = "evidence_qualified_threshold_update"
        hierarchy_adopted = adopt_hierarchy or bool(
            previous and previous.get("hierarchy_adopted") is True
        )
        hierarchy = (source.get("hierarchical_entry_quality") or {}).get(
            "runtime_extension"
        ) or {}
        child = hierarchy.get("policy_candidate")
        previous_hierarchy_active = bool(
            previous
            and isinstance(previous.get("machine_policy"), dict)
            and "hierarchy" in previous["machine_policy"]
        )
        hierarchy_disposition = (
            "not_adopted"
            if not hierarchy_adopted
            else (
                "incumbent_child_carried"
                if previous_hierarchy_active
                else "adopted_no_qualified_child"
            )
        )
        if hierarchy_adopted and child is not None:
            errors = calibration.validate_hierarchy_candidate(
                hierarchy, source_date=source_date
            )
            if errors:
                raise ValueError(
                    "machine_hierarchy_candidate_invalid:" + ",".join(errors)
                )
            child_policy = child["threshold_policy"]
            child_parent_hash = child.get("incumbent_machine_policy_sha256")
            if child_policy["thresholds"] == machine["thresholds"] and (
                child_parent_hash is None or child_parent_hash == digest(machine)
            ):
                machine = copy.deepcopy(child_policy)
                hierarchy_disposition = "evidence_qualified_hierarchy_update"
            else:
                hierarchy_disposition = "candidate_parent_changed_revalidation_required"
        # A qualified common replacement cannot retain residuals bound to its
        # predecessor. The old complete generation remains in the archive.
        if (
            previous
            and "hierarchy" in previous["machine_policy"]
            and "hierarchy" not in machine
        ):
            hierarchy_disposition = "parent_updated_children_require_revalidation"
        refinement = source.get("mechanistic_entry_refinement") or {}
        flows = source.get("mechanistic_flow_groups") or {}
        context = {
            "source_date": source_date,
            "clean_baseline_date": "2026-06-05",
            "threshold_disposition": disposition,
            "flow_study_status": flows.get("status"),
            "flow_source_population": flows.get("source_population"),
            "retrospective_supported_flow_families": flows.get(
                "retrospective_supported_recheck_families", []
            ),
            "flow_results_are_not_forward_profit_evidence": True,
            "refinement_status": refinement.get("status"),
            "refinement_promotion_pass": refinement.get("promotion_pass"),
            "economics": "unverified_initial_or_carry_is_not_positive_ev_evidence",
            "objective": "prompt_small_net_profits_without_deep_adverse_excursion_or_prolonged_stagnation",
            "optional_micro_features": "use_only_valid_present_measurements_no_missing_data_veto",
            "hierarchy_disposition": hierarchy_disposition,
            "hierarchy_status": hierarchy.get("status"),
            "hierarchy_role_version": "v1" if hierarchy_adopted else None,
        }
        if hierarchy_adopted:
            context["hierarchy_counterfactual_holdout"] = [
                {"id": e["id"], "status": e.get("status"), "holdout": e.get("holdout")}
                for e in hierarchy.get("evaluations", [])[:8]
                if isinstance(e, dict) and "id" in e
            ]
        prompt = compact_auxiliary_prompt(context, prompt_version=selected_ai_version)
        all_continuous = adopt_all_continuous or bool(
            previous and previous.get("all_continuous_adopted") is True
        )
        scope_policies = {}
        if all_continuous:
            from src.engine.scalping.entry_setup_scalping_rollout import (
                AUTO_PROMOTION_SCOPES,
            )

            extensions = (source.get("hierarchical_entry_quality") or {}).get(
                "runtime_extensions_by_scope"
            ) or {}
            for scope in AUTO_PROMOTION_SCOPES:
                old = ((previous or {}).get("scope_policies") or {}).get(scope)
                scoped_machine = copy.deepcopy(
                    old["machine_policy"]
                    if old
                    else MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
                )
                scoped_disposition = (
                    "incumbent_scope_carried"
                    if old
                    else "authorized_common_seed_not_cohort_optimized"
                )
                extension = extensions.get(scope) or {}
                if scope == "KRX|KRX_REGULAR":
                    scoped_machine, scoped_disposition = (
                        copy.deepcopy(machine),
                        disposition,
                    )
                elif (
                    hierarchy_adopted and extension.get("policy_candidate") is not None
                ):
                    errors = calibration.validate_hierarchy_candidate(
                        extension,
                        source_date=source_date,
                        cohort=tuple(scope.split("|")),
                    )
                    if errors:
                        raise ValueError(
                            "machine_scope_candidate_invalid:"
                            + scope
                            + ":"
                            + ",".join(errors)
                        )
                    scoped_child = extension["policy_candidate"]["threshold_policy"]
                    if scoped_child["thresholds"] == scoped_machine["thresholds"]:
                        scoped_machine = copy.deepcopy(scoped_child)
                        scoped_disposition = "evidence_qualified_exact_scope_update"
                    else:
                        scoped_disposition = (
                            "candidate_parent_changed_revalidation_required"
                        )
                scoped_context = {
                    **(context if scope == "KRX|KRX_REGULAR" else {}),
                    "source_date": source_date,
                    "scope": scope,
                    "threshold_disposition": scoped_disposition,
                    "hierarchy_role_version": "v1" if hierarchy_adopted else None,
                    "economics": "initial_or_carry_is_not_positive_ev_evidence",
                    "cross_scope_optimized_threshold_inheritance": False,
                    "hierarchy_status": extension.get("status"),
                    "source_count": extension.get("source_count"),
                    "hierarchy_counterfactual_holdout": [
                        {
                            "id": e["id"],
                            "status": e.get("status"),
                            "holdout": e.get("holdout"),
                        }
                        for e in extension.get("evaluations", [])[:8]
                        if isinstance(e, dict) and "id" in e
                    ],
                }
                scoped_prompt = compact_auxiliary_prompt(
                    scoped_context, prompt_version=selected_ai_version
                )
                scope_policies[scope] = {
                    "machine_policy": scoped_machine,
                    "machine_disposition": scoped_disposition,
                    "historical_context": scoped_context,
                    "ai_policy": {
                        "prompt_version": selected_ai_version,
                        "variant": compact_prompt_variant(selected_ai_version),
                        "system_prompt": scoped_prompt,
                        "system_prompt_sha256": digest(scoped_prompt),
                    },
                }
        previous_ai_version = str(
            ((previous or {}).get("ai_policy") or {}).get("prompt_version") or ""
        )
        compact_prompt_disposition = (
            "compact_contract_migration"
            if previous_ai_version
            in {
                "",
                LEGACY_AI_VERSION,
                LEGACY_COMPACT_AI_VERSION,
                *FROZEN_COMPACT_V2_VARIANTS,
            }
            else (
                "compact_registered_successor_auto_selected"
                if selected_ai_version != previous_ai_version
                else "compact_incumbent_carry"
            )
        )
        bundle = {
            "schema": SCHEMA,
            "target_date": target,
            "source_date": source_date,
            "source_file_sha256": source_hash,
            "source_artifact_sha256": source["artifact_content_sha256"],
            "cohort": COHORT,
            "role_contract": copy.deepcopy(MECHANISTIC_PRIMARY_ROLE_CONTRACT),
            "adoption_basis": "user_authorized_initial_policy_with_guarded_succession",
            "machine_policy": machine,
            "machine_disposition": disposition,
            "hierarchy_adopted": hierarchy_adopted,
            "previous_bundle_sha256": previous["bundle_sha256"] if previous else None,
            "historical_context": context,
            "compact_prompt_disposition": compact_prompt_disposition,
            "ai_policy": {
                "prompt_version": selected_ai_version,
                "variant": compact_prompt_variant(selected_ai_version),
                "system_prompt": prompt,
                "system_prompt_sha256": digest(prompt),
            },
            "hard_guards_unchanged": True,
            "actual_order_submitted": False,
            "generated_at": current.isoformat(),
        }
        bundle["bundle_sha256"] = digest(bundle)
        if all_continuous:
            bundle.update(all_continuous_adopted=True, scope_policies=scope_policies)
            bundle["bundle_sha256"] = digest(
                {k: v for k, v in bundle.items() if k != "bundle_sha256"}
            )
        validate(bundle, target_date=target)
        if existing is not None:
            calibration._atomic_write_json(
                policy_root / "generations" / f"{existing['bundle_sha256']}.json",
                existing,
            )
        calibration._atomic_write_json(
            policy_root / "generations" / f"{bundle['bundle_sha256']}.json", bundle
        )
        calibration._atomic_write_json(policy_root / f"policy_{target}.json", bundle)
        return load(data_root=data_root, target_date=target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--replace-initial-role", action="store_true")
    parser.add_argument("--adopt-all-continuous", action="store_true")
    parser.add_argument(
        "--adopt-hierarchy",
        action="store_true",
        help="Explicit initial adoption; later dated succession is automatic",
    )
    args = parser.parse_args()
    bundle = publish(
        args.source,
        data_root=args.data_root,
        bootstrap=args.bootstrap,
        replace_initial_role=args.replace_initial_role,
        adopt_hierarchy=args.adopt_hierarchy,
        adopt_all_continuous=args.adopt_all_continuous,
    )
    print(
        json.dumps(
            {
                k: bundle.get(k)
                for k in ("target_date", "bundle_sha256", "machine_disposition")
            }
            if bundle
            else {"status": "not_enabled"}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
