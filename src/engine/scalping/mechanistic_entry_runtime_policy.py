"""Initial machine-first policy and dated postclose succession for main KRX.

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
AI_VERSION = DECISION_QUALITY_V2_15_2_BALANCED_BOUNDED_RECOVERY_PROMPT_VERSION
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
    ai = bundle.get("ai_policy") or {}
    if not isinstance(ai, dict):
        raise ValueError("machine_bundle_ai_policy_invalid")
    if (
        ai.get("prompt_version") != AI_VERSION
        or ai.get("variant") != "machine_first_pass_veto_v2"
        or ai.get("system_prompt_sha256") != digest(ai.get("system_prompt"))
        or ai.get("system_prompt") != auxiliary_prompt(bundle.get("historical_context"))
    ):
        raise ValueError("machine_bundle_ai_policy_invalid")


def auxiliary_prompt(context: object) -> str:
    return (
        decision_quality_balanced_entry_system_prompt("entry", bounded_recovery=True)
        + "\n\n"
        + AI_ADDENDUM
        + "\n\nHistorical policy context (not current facts):\n"
        + json.dumps(context, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    )


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
    now: datetime | None = None,
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
                variant="machine_first_pass_veto_v2",
                system_prompt=auxiliary_prompt(reviewed.get("historical_context")),
            )
            reviewed["ai_policy"]["system_prompt_sha256"] = digest(
                reviewed["ai_policy"]["system_prompt"]
            )
            reviewed["bundle_sha256"] = digest(
                {k: v for k, v in reviewed.items() if k != "bundle_sha256"}
            )
            validate(reviewed, target_date=target)
        if (
            existing is not None
            and existing.get("role_contract") == MECHANISTIC_PRIMARY_ROLE_CONTRACT
            and existing["source_artifact_sha256"] == source["artifact_content_sha256"]
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
            machine = projection["threshold_policy"]
            disposition = "evidence_qualified_threshold_update"
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
        }
        prompt = auxiliary_prompt(context)
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
            "previous_bundle_sha256": previous["bundle_sha256"] if previous else None,
            "historical_context": context,
            "ai_policy": {
                "prompt_version": AI_VERSION,
                "variant": "machine_first_pass_veto_v2",
                "system_prompt": prompt,
                "system_prompt_sha256": digest(prompt),
            },
            "hard_guards_unchanged": True,
            "actual_order_submitted": False,
            "generated_at": current.isoformat(),
        }
        bundle["bundle_sha256"] = digest(bundle)
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
    args = parser.parse_args()
    bundle = publish(
        args.source,
        data_root=args.data_root,
        bootstrap=args.bootstrap,
        replace_initial_role=args.replace_initial_role,
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
