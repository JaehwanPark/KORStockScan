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
import os
import re
import tempfile
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


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


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
    publication = str(bundle.get("publication_date") or source)
    if any(
        not isinstance(bundle.get(key), str)
        or re.fullmatch(r"[0-9a-f]{64}", bundle[key]) is None
        for key in ("source_file_sha256", "source_artifact_sha256", "bundle_sha256")
    ):
        raise ValueError("machine_bundle_hash_format_invalid")
    if (
        source < "2026-06-05"
        or publication < source
        or next_target(publication) != target_date
    ):
        raise ValueError("machine_bundle_date_invalid")
    machine_source = bundle.get("machine_evaluation_source")
    if machine_source is not None and (
        not isinstance(machine_source, dict)
        or str(machine_source.get("source_date") or "") < "2026-06-05"
        or str(machine_source.get("source_date") or "") > publication
        or re.fullmatch(
            r"[0-9a-f]{64}",
            str(machine_source.get("artifact_content_sha256") or ""),
        )
        is None
        or re.fullmatch(
            r"[0-9a-f]{64}", str(machine_source.get("file_sha256") or "")
        )
        is None
    ):
        raise ValueError("machine_evaluation_source_invalid")
    compact_source = bundle.get("compact_evaluation_source")
    if compact_source is not None and (
        not isinstance(compact_source, dict)
        or re.fullmatch(
            r"[0-9a-f]{64}",
            str(compact_source.get("artifact_content_sha256") or ""),
        )
        is None
        or re.fullmatch(
            r"[0-9a-f]{64}",
            str(compact_source.get("machine_policy_sha256") or ""),
        )
        is None
    ):
        raise ValueError("compact_evaluation_source_invalid")
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


def compact_terminal_gate_allowed(source_receipt: dict) -> bool:
    """One CF authority rule for #82, publication and the final verifier."""
    gate = source_receipt.get("machine_terminal_tuning_gate") or {}
    if not isinstance(gate, dict):
        return False
    source_date = str(source_receipt.get("target_date") or "")
    try:
        date.fromisoformat(source_date)
    except ValueError:
        return False
    if source_date < "2026-06-05":
        return False
    return bool(
        source_date < "2026-09-15"
        or gate.get("decision_counterfactual_tuning_input_allowed") is True
    )


def compact_outcome_counts_valid(economic: dict) -> bool:
    """Reconcile every published subtotal against the detailed outcome map."""
    counts = economic.get("verdict_x_action_neutral_outcome_counts")
    router_contract = economic.get("schema") == "compact_auxiliary_router_economic_selection_v3"
    allowed_verdicts = {"PASS", "VETO", "CAUTION"} if router_contract else {"PASS", "VETO"}
    if not isinstance(counts, dict) or any(
        not isinstance(key, str)
        or key.partition("|")[0] not in allowed_verdicts
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
    if router_contract:
        import math

        if any(type(economic.get(key)) not in (int, float)
               or not math.isfinite(economic[key]) or economic[key] < 0
               for key in ("missed_profit_caution_net_sum_pct", "missed_profit_veto_net_sum_pct", "dangerous_pass_loss_sum_pct", "avoided_nonentry_loss_sum_pct")):
            return False
        expected.update(
            evaluable_caution_count=sum(value for key, value in counts.items() if key.startswith("CAUTION|")),
            missed_profit_caution_count=counts.get("CAUTION|CLEAN_FAST_PROFIT", 0),
        )
        if (economic.get("caution_is_not_veto") is not True
            or economic.get("insufficient_is_source_repair_only") is not True
            or economic.get("caution_opportunity_cost_role") != "exact_enter_checkpoint_foregone_opportunity_not_terminal_episode_loss"):
            return False
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
    nonentry_count = economic.get("evaluable_veto_count", 0)
    missed_count = economic.get("missed_profit_veto_count", 0)
    missed_rate = economic.get("missed_veto_rate")
    avoided_nonentry_loss = 0.0
    if economic.get("schema") == "compact_auxiliary_router_economic_selection_v3":
        if not compact_outcome_counts_valid(economic):
            return carry
        caution_amount = economic.get("missed_profit_caution_net_sum_pct")
        if type(caution_amount) not in (int, float) or not math.isfinite(caution_amount) or caution_amount < 0:
            return carry
        missed += caution_amount
        avoided_nonentry_loss = economic["avoided_nonentry_loss_sum_pct"]
        nonentry_count += economic["evaluable_caution_count"]
        missed_count += economic["missed_profit_caution_count"]
        missed_rate = missed_count / nonentry_count if nonentry_count else None
    if (
        missed > loss + avoided_nonentry_loss
        and nonentry_count >= 5
        and missed_count >= 3
        and missed_rate is not None
        and missed_rate >= 0.25
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


def _selected_compact_prompt_version(source: dict, previous: dict | None, *, effective_date=None) -> str:
    """Consume exact-incumbent paired proof; natural errors guide research."""

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
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    proof = outcomes.get("paired_economic_evaluation") or {}
    source_receipt = case_table.get("machine_ai_natural_source_receipt") or {}
    if not (source_receipt.get("tuning_input_allowed") is True
            and compact_terminal_gate_allowed(source_receipt)
            and (case_table.get("compact_auxiliary_policy_measurement") or {}).get("measurement_allowed") is True
            and paired.promotion_valid(proof, incumbent=previous_version,
                selected=proof.get("candidate_prompt_version"),
                source_manifest_sha256=source_receipt.get("source_manifest_sha256"), effective_date=effective_date)):
        return previous_version
    selected = proof.get("candidate_prompt_version")
    return selected if selected in COMPACT_AI_VARIANTS else previous_version


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
    source_payload = _read(source_path)
    if source_payload.get("artifact_content_sha256") != bundle.get(
        "source_artifact_sha256"
    ):
        raise ValueError("machine_bundle_source_artifact_hash_invalid")
    machine_source = bundle.get("machine_evaluation_source") or {}
    if machine_source:
        machine_path = (
            root(data_root)
            / "sources"
            / f"{machine_source['file_sha256']}.json"
        )
        if (
            not machine_path.is_file()
            or _source_hash(str(machine_path), _signature(machine_path))
            != machine_source["file_sha256"]
        ):
            raise ValueError("machine_evaluation_source_file_hash_invalid")
        machine_payload = _read(machine_path)
        if machine_payload.get("artifact_content_sha256") != machine_source.get(
            "artifact_content_sha256"
        ):
            raise ValueError("machine_evaluation_source_artifact_hash_invalid")
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


def publish_compact_evaluation(
    source: dict,
    *,
    source_receipt: dict,
    publication_day: str,
    data_root: Path,
    now: datetime | None = None,
) -> dict:
    """Publish one canonical paired result without a copied calibration owner."""
    from src.engine.scalping import compact_auxiliary_paired_replay as paired

    current = (now or datetime.now(KST)).astimezone(KST)
    source_day = str(source.get("target_date") or "")
    manifest_sha = source_receipt.get("source_manifest_sha256") or (
        source_receipt.get("source_manifest") or {}
    ).get("source_manifest_sha256")
    if (
        not paired.valid(source)
        or source.get("schema") != paired.SCHEMA
        or source_day < "2026-06-05"
        or not source_day <= publication_day <= current.date().isoformat()
        or source.get("source_manifest_sha256") != manifest_sha
    ):
        raise ValueError("compact_direct_evaluation_source_invalid")
    target = next_target(publication_day)
    previous = load_effective(data_root=data_root, target_date=publication_day)
    if previous is None:
        raise ValueError("compact_incumbent_missing_no_implicit_bootstrap")
    policy_root = root(data_root)
    policy_root.mkdir(parents=True, exist_ok=True)
    with (policy_root / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing = load(data_root=data_root, target_date=target)
        if (
            existing
            and existing.get("compact_paired_artifact_sha256")
            == source["artifact_content_sha256"]
            and existing.get("compact_evaluation_source_date") == source_day
        ):
            machine_source = existing.get("machine_evaluation_source") or {}
            machine_top_level = {
                "source_date": machine_source.get("source_date"),
                "source_file_sha256": machine_source.get("file_sha256"),
                "source_artifact_sha256": machine_source.get(
                    "artifact_content_sha256"
                ),
            }
            if all(existing.get(key) == value for key, value in machine_top_level.items()):
                return existing
            repaired = copy.deepcopy(existing)
            repaired.pop("bundle_sha256", None)
            repaired.update(machine_top_level, generated_at=current.isoformat())
            repaired["bundle_sha256"] = digest(repaired)
            validate(repaired, target_date=target)
            _atomic_write_json(
                policy_root / "generations" / f"{existing['bundle_sha256']}.json",
                existing,
            )
            _atomic_write_json(
                policy_root / "generations" / f"{repaired['bundle_sha256']}.json",
                repaired,
            )
            _atomic_write_json(policy_root / f"policy_{target}.json", repaired)
            return load(data_root=data_root, target_date=target)
        if current >= datetime.fromisoformat(target + "T07:35:00").replace(tzinfo=KST):
            if existing is None:
                raise ValueError("compact_preopen_freeze_without_dated_policy")
            return existing
        version = previous["ai_policy"]["prompt_version"]
        selected = source["candidate_prompt_version"]
        inherited = existing or previous
        parent_bundle_hashes = source.get("machine_parent_bundle_sha256s") or []
        parent_policy_hashes = set()
        for parent_bundle_hash in parent_bundle_hashes:
            if re.fullmatch(r"[0-9a-f]{64}", str(parent_bundle_hash or "")) is None:
                continue
            parent_path = policy_root / "generations" / f"{parent_bundle_hash}.json"
            if not parent_path.is_file():
                continue
            try:
                parent_bundle = _read(parent_path)
                validate(parent_bundle, target_date=parent_bundle["target_date"])
            except (KeyError, OSError, ValueError):
                continue
            parent_policy_hashes.add(digest(parent_bundle["machine_policy"]))
        exact_machine_parent = (
            len(parent_policy_hashes) == 1
            and parent_policy_hashes == {digest(inherited["machine_policy"])}
        )
        measurement_allowed = (
            source_receipt.get("tuning_input_allowed") is True
            and compact_terminal_gate_allowed(source_receipt)
            and (source_receipt.get("compact_auxiliary_policy_measurement") or {}).get(
                "measurement_allowed"
            )
            is True
            and exact_machine_parent
        )
        scope_keys = list((previous.get("scope_policies") or {})) or ["|".join(COHORT)]
        promoted_scopes = []
        for scope_key in scope_keys:
            old_ai = (previous.get("scope_policies") or {}).get(
                scope_key, previous
            )["ai_policy"]
            if measurement_allowed and paired.promotion_valid(
                source,
                incumbent=old_ai["prompt_version"],
                selected=selected,
                source_manifest_sha256=manifest_sha,
                effective_date=target,
                scope=tuple(scope_key.split("|")),
            ):
                promoted_scopes.append(scope_key)
        if existing and existing["ai_policy"]["prompt_version"] != version:
            raise ValueError("compact_future_stage_owner_conflict")
        for scope_key in promoted_scopes:
            old_ai = (previous.get("scope_policies") or {}).get(
                scope_key, previous
            )["ai_policy"]
            current_ai = ((existing or {}).get("scope_policies") or {}).get(
                scope_key, existing or previous
            )["ai_policy"]
            if current_ai["prompt_version"] != old_ai["prompt_version"]:
                raise ValueError("compact_future_stage_owner_conflict:" + scope_key)
        if existing:
            _atomic_write_json(
                policy_root / "generations" / f"{existing['bundle_sha256']}.json",
                existing,
            )
        bundle = copy.deepcopy(inherited)
        bundle.pop("bundle_sha256", None)
        if promoted_scopes:
            paired.consume_holdout(source, data_root, scopes=promoted_scopes)
            selected_policies = [
                (value["ai_policy"], value["historical_context"])
                for scope, value in (bundle.get("scope_policies") or {}).items()
                if scope in promoted_scopes
            ]
            if "|".join(COHORT) in promoted_scopes:
                selected_policies.append(
                    (bundle["ai_policy"], bundle.get("historical_context"))
                )
            for ai_policy, context in selected_policies:
                ai_policy.update(
                    prompt_version=selected,
                    variant=compact_prompt_variant(selected),
                    system_prompt=compact_auxiliary_prompt(
                        context, prompt_version=selected
                    ),
                )
                ai_policy["system_prompt_sha256"] = digest(
                    ai_policy["system_prompt"]
                )
        encoded_source = (
            json.dumps(source, ensure_ascii=False, indent=2) + "\n"
        ).encode()
        source_hash = hashlib.sha256(encoded_source).hexdigest()
        _atomic_write_json(policy_root / "sources" / f"{source_hash}.json", source)
        machine_source = bundle.get("machine_evaluation_source") or {}
        bundle.update(
            target_date=target,
            source_date=machine_source.get("source_date", bundle["source_date"]),
            publication_date=publication_day,
            source_file_sha256=machine_source.get(
                "file_sha256", bundle["source_file_sha256"]
            ),
            source_artifact_sha256=machine_source.get(
                "artifact_content_sha256", bundle["source_artifact_sha256"]
            ),
            generated_at=current.isoformat(),
            compact_evaluation_source_date=source_day,
            previous_bundle_sha256=inherited["bundle_sha256"],
            compact_inherited_bundle_sha256=inherited["bundle_sha256"],
            compact_inherited_source_date=inherited["source_date"],
            compact_paired_artifact_sha256=source["artifact_content_sha256"],
            compact_evaluation_fingerprint=source.get("evaluation_fingerprint"),
            compact_prompt_disposition=(
                "compact_paired_candidate_selected"
                if promoted_scopes
                else (
                    "parent_changed_revalidation_required"
                    if parent_bundle_hashes and not exact_machine_parent
                    else "compact_incumbent_carry"
                )
            ),
            compact_promoted_scopes=promoted_scopes,
            compact_evaluation_source={
                "source_date": source_day,
                "artifact_content_sha256": source["artifact_content_sha256"],
                "evaluation_fingerprint": source.get("evaluation_fingerprint"),
                "machine_parent_bundle_sha256s": parent_bundle_hashes,
                "machine_policy_sha256": digest(inherited["machine_policy"]),
                "disposition": (
                    "candidate_selected"
                    if promoted_scopes
                    else "parent_changed_revalidation_required"
                    if parent_bundle_hashes and not exact_machine_parent
                    else "incumbent_carried"
                ),
            },
        )
        bundle["bundle_sha256"] = digest(bundle)
        validate(bundle, target_date=target)
        _atomic_write_json(
            policy_root / "generations" / f"{bundle['bundle_sha256']}.json", bundle
        )
        _atomic_write_json(policy_root / f"policy_{target}.json", bundle)
        return load(data_root=data_root, target_date=target)


def _publish_compact_scope(source: dict, *, data_root: Path, current: datetime) -> dict:
    """Compatibility reader for an older calibration source; publish the pair."""
    table = source["hierarchical_entry_quality"]["machine_decision_case_table"]
    proof = table["compact_auxiliary_screen_outcomes"]["paired_economic_evaluation"]
    receipt = table.get("compact_auxiliary_evaluation_source_receipt") or table[
        "machine_ai_natural_source_receipt"
    ]
    return publish_compact_evaluation(
        proof,
        source_receipt=receipt,
        publication_day=source["target_date"],
        data_root=data_root,
        now=current,
    )

def publish(
    source_path: Path,
    *,
    data_root: Path,
    bootstrap: bool = False,
    replace_initial_role: bool = False,
    adopt_hierarchy: bool = False,
    now: datetime | None = None,
    adopt_all_continuous: bool = False,
    publication_day: str | None = None,
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
    if source.get("report_scope") == "compact_auxiliary_only":
        return _publish_compact_scope(source, data_root=data_root, current=(now or datetime.now(KST)).astimezone(KST))
    current = (now or datetime.now(KST)).astimezone(KST)
    publication_date = publication_day or source_date
    target = next_target(publication_date)
    if (
        source_date < "2026-06-05"
        or source_date > publication_date
        or publication_date > current.date().isoformat()
    ):
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
            source, evaluation_incumbent, effective_date=target
        )
        if (
            existing is not None
            and existing.get("role_contract") == MECHANISTIC_PRIMARY_ROLE_CONTRACT
            and (
                existing.get("machine_evaluation_source") or {}
            ).get("artifact_content_sha256")
            == source["artifact_content_sha256"]
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
            source, evaluation_incumbent or previous, effective_date=target
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
            _atomic_write_json(snapshot, source)
        if _source_hash(str(snapshot), _signature(snapshot)) != source_hash:
            raise ValueError("machine_policy_source_snapshot_corrupt")
        projection, errors = _mechanistic_primary_activation_projection(
            source_date, source_path=snapshot
        )
        if errors:
            raise ValueError("machine_policy_challenger_invalid:" + ",".join(errors))
        scoped_refinements = source.get("mechanistic_refinements_by_scope") or {}
        scoped_extensions = (source.get("hierarchical_entry_quality") or {}).get("runtime_extensions_by_scope") or {}
        qualified_scopes = {scope for scope, evidence in scoped_refinements.items()
                            if evidence.get("policy_candidate") is not None}
        qualified_scopes.update(scope for scope, evidence in scoped_extensions.items()
                                if evidence.get("policy_candidate") is not None)
        if projection is not None or ((source.get("hierarchical_entry_quality") or {}).get("runtime_extension") or {}).get("policy_candidate") is not None:
            qualified_scopes.add("KRX|KRX_REGULAR")
        # Independent scope profits do not validate their shared account capital.
        # Keep the incumbent until an existing owner supplies joint allocation
        # proof; never select a winning subset using the scopes' holdouts.
        joint_scope_unproven = (source.get("report_scope") == "main_mechanistic_entry"
            and len(qualified_scopes) > 1
            and not calibration.machine_joint_scope_evidence_valid(source, qualified_scopes))
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
        if joint_scope_unproven:
            disposition = "joint_scope_capital_replay_required_incumbent_carried"
        elif projection is not None:
            parent_hash = projection.get("incumbent_machine_policy_sha256")
            if parent_hash is not None and parent_hash != digest(machine):
                disposition = "candidate_parent_changed_revalidation_required"
            else:
                machine = projection["threshold_policy"]
                disposition = "evidence_qualified_threshold_update"
        if disposition == "evidence_qualified_threshold_update" and previous:
            # One entry-stage change per generation unless the exact combined
            # machine+compact policy was independently evaluated.
            selected_ai_version = previous["ai_policy"]["prompt_version"]
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
        machine_economic_gate_pass = (
            not joint_scope_unproven and (source.get("report_scope") != "main_mechanistic_entry"
            or (child or {}).get("operating_contract_version") == "machine_operating_daily_net_v1")
        )
        if hierarchy_adopted and child is not None and not machine_economic_gate_pass:
            hierarchy_disposition = "diagnostic_child_parent_economic_gate_not_passed"
        elif hierarchy_adopted and child is not None:
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
        if previous and machine != previous["machine_policy"]:
            selected_ai_version = previous["ai_policy"]["prompt_version"]
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
                scope_projection = None
                if scope != "KRX|KRX_REGULAR":
                    scope_projection, errors = _mechanistic_primary_activation_projection(
                        source_date, source_path=snapshot, cohort=tuple(scope.split("|")))
                    if errors:
                        raise ValueError("machine_scope_common_candidate_invalid:" + scope + ":" + ",".join(errors))
                if scope == "KRX|KRX_REGULAR":
                    scoped_machine, scoped_disposition = (
                        copy.deepcopy(machine),
                        disposition,
                    )
                elif joint_scope_unproven:
                    scoped_disposition = "joint_scope_capital_replay_required_incumbent_carried"
                elif scope_projection is not None:
                    if scope_projection.get("incumbent_machine_policy_sha256") == digest(scoped_machine):
                        scoped_machine = copy.deepcopy(scope_projection["threshold_policy"])
                        scoped_disposition = "evidence_qualified_exact_scope_common_update"
                    else:
                        scoped_disposition = "candidate_parent_changed_revalidation_required"
                elif (
                    hierarchy_adopted
                    and extension.get("policy_candidate") is not None
                    and (source.get("report_scope") != "main_mechanistic_entry"
                         or extension["policy_candidate"].get("operating_contract_version") == "machine_operating_daily_net_v1")
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
                    scoped_parent_hash = extension["policy_candidate"].get("incumbent_machine_policy_sha256")
                    if scoped_child["thresholds"] == scoped_machine["thresholds"] and (
                        scoped_parent_hash is None or scoped_parent_hash == digest(scoped_machine)
                    ):
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
                scoped_ai_version = selected_ai_version if scope == "|".join(COHORT) or not old or old["ai_policy"]["prompt_version"] in {LEGACY_AI_VERSION, LEGACY_COMPACT_AI_VERSION, *FROZEN_COMPACT_V2_VARIANTS} else old["ai_policy"]["prompt_version"]
                if old and scoped_machine != old["machine_policy"]:
                    scoped_ai_version = old["ai_policy"]["prompt_version"]
                scoped_prompt = compact_auxiliary_prompt(
                    scoped_context, prompt_version=scoped_ai_version
                )
                scope_policies[scope] = {
                    "machine_policy": scoped_machine,
                    "machine_disposition": scoped_disposition,
                    "historical_context": scoped_context,
                    "ai_policy": {
                        "prompt_version": scoped_ai_version,
                        "variant": compact_prompt_variant(scoped_ai_version),
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
            "publication_date": publication_date,
            "source_file_sha256": source_hash,
            "source_artifact_sha256": source["artifact_content_sha256"],
            "cohort": COHORT,
            "role_contract": copy.deepcopy(MECHANISTIC_PRIMARY_ROLE_CONTRACT),
            "adoption_basis": "user_authorized_initial_policy_with_guarded_succession",
            "machine_policy": machine,
            "machine_disposition": disposition,
            "machine_evaluation_source": {
                "source_date": source_date,
                "path": str(source_path.resolve()),
                "file_sha256": source_hash,
                "artifact_content_sha256": source["artifact_content_sha256"],
                "report_scope": source.get("report_scope"),
                "noncompact_sections_refreshed": source.get(
                    "noncompact_sections_refreshed"
                ),
                "terminal_state": (
                    source.get("machine_full_evaluation") or {}
                ).get("state"),
                "incumbent_machine_policy_sha256": (
                    source.get("mechanistic_entry_refinement") or {}
                ).get("incumbent_machine_policy_sha256"),
                "disposition": disposition,
            },
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
        if previous and previous.get("compact_evaluation_source"):
            bundle["compact_evaluation_source"] = copy.deepcopy(
                previous["compact_evaluation_source"]
            )
            if disposition == "evidence_qualified_threshold_update":
                bundle["compact_evaluation_source"]["disposition"] = (
                    "parent_changed_revalidation_required"
                )
        bundle["bundle_sha256"] = digest(bundle)
        if all_continuous:
            bundle.update(all_continuous_adopted=True, scope_policies=scope_policies)
            bundle["bundle_sha256"] = digest(
                {k: v for k, v in bundle.items() if k != "bundle_sha256"}
            )
        validate(bundle, target_date=target)
        if selected_ai_version != previous_ai_version:
            from src.engine.scalping import compact_auxiliary_paired_replay as paired
            paired_table = (source.get("hierarchical_entry_quality") or {}).get("machine_decision_case_table") or {}
            paired_proof = paired_table.get("compact_auxiliary_screen_outcomes") or {}
            if paired_proof.get("paired_economic_evaluation"):
                paired.consume_holdout(paired_proof["paired_economic_evaluation"], data_root)
        if existing is not None:
            _atomic_write_json(
                policy_root / "generations" / f"{existing['bundle_sha256']}.json",
                existing,
            )
        _atomic_write_json(
            policy_root / "generations" / f"{bundle['bundle_sha256']}.json", bundle
        )
        _atomic_write_json(policy_root / f"policy_{target}.json", bundle)
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
