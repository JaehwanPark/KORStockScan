"""Native policy-generation capability, independent of today's population.

Report-only evidence. A fixture receipt verifies code reachability; it never
proves a selected release, PID consumption, realized profit, or startup safety.
"""

from __future__ import annotations
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from .family_policy_semantics import digest

SCHEMA = "postclose_policy_generation_contract_v1"
START_DATE = "2026-10-12"
ENGINE = Path(__file__).parents[1]
COMPONENTS = {
    "entry_cancel_wait": (
        "automation/entry_cancel_wait_tuning.py",
        "scalping/entry_cancel_wait_runtime.py",
        "scalping/main_custody_checkpoint.py",
        "sniper_sync.py",
        "scalping/ai_market_snapshot.py",
        "scalping/main_stop_policy.py",
        "runtime_approval_summary.py",
        "automation/runtime_policy_bootstrap.py",
    ),
    "rising_missed": (
        "monitoring/rising_missed_classifier_prior.py",
        "monitoring/rising_missed_intraday_feedback.py",
        "scalping/tp1_capital_replay.py",
        "scalping/rising_missed_candidate.py",
        "sniper_state_handlers.py",
        "scalping/market_data_enrichment.py",
        "automation/runtime_policy_bootstrap.py",
    ),
    "auxiliary": (
        "scalping/reversal_auxiliary_tuning.py",
        "scalping/reversal_auxiliary_registry.py",
        "ai/offline_comparison_store.py",
        "runtime_approval_summary.py",
        "automation/runtime_policy_bootstrap.py",
    ),
    "holding_vote": (
        "automation/main_stop_postclose.py",
        "automation/main_stop_source_index.py",
        "lifecycle/broker_cost_reconciliation.py",
        "lifecycle/research_storage.py",
        "scalping/holding_vote_experiment.py",
        "scalping/holding_vote_exit_models.py",
        "scalping/holding_path_vote_replay.py",
        "scalping/holding_path_vote_policy.py",
        "scalping/main_stop_replay.py",
        "scalping/universal_trailing_replay.py",
        "scalping/main_stop_policy.py",
        "ai/holding_exit_vote.py",
        "sniper_state_handlers.py",
        "sniper_execution_receipts.py",
        "ai/holding_vote_replay_source.py",
        "holding_exit_observation_report.py",
        "automation/runtime_policy_bootstrap.py",
    ),
}
STEPS = ("source", "comparison", "selection", "publication", "reader")
OWNERS = {
    "entry_cancel_wait": "DirectFamilySourceRepairEntryCancelWait",
    "rising_missed": "PostcloseStructuralPolicyCompletion1011",
    "auxiliary": "DirectFamilySourceRepairCompactAuxiliary",
    "holding_vote": "MainStopLossRetirementRuntimeTuning1010",
}


def code_generation(family):
    from src.engine.lifecycle.holding_window_generation import cached_code_generation

    names = (
        *COMPONENTS[family],
        "monitoring/policy_generation_contract.py",
        "lifecycle/holding_window_generation.py",
    )
    values = cached_code_generation([ENGINE / name for name in names])
    return digest({name: values[str(ENGINE / name)] for name in names})


def source_body(payload):
    return {
        k: v
        for k, v in payload.items()
        if k
        not in {
            "policy_generation",
            "artifact_sha256",
            "artifact_content_sha256",
            "proof_sha256",
            "generated_at",
            "as_of",
        }
    }


def native(
    payload, *, family, day, data_root, source_state, comparison_state, handoff_state
):
    code = code_generation(family)
    receipt = None
    path = (
        Path(data_root)
        / "report/postclose_generation_validation"
        / f"{family}_{code}.json"
    )
    try:
        from src.engine.scalping.main_stop_policy import bounded_object

        value, byte_sha = bounded_object(path, 65536)
        if (
            value.get("schema") == "postclose_generation_fixture_receipt_v1"
            and value.get("family") == family
            and value.get("code_sha256") == code
            and value.get("status") == "pass"
            and value.get("closure_tests")
            and value.get("unresolved_findings") == []
            and value.get("receipt_sha256")
            == digest({k: v for k, v in value.items() if k != "receipt_sha256"})
        ):
            receipt = dict(path=str(path), sha256=byte_sha)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    body = dict(
        schema=SCHEMA,
        family=family,
        source_date=day,
        as_of=payload.get("generated_at") or payload.get("as_of") or day,
        source_generation=digest(source_body(payload)),
        code_sha256=code,
        components={
            step: dict(
                status="supported",
                verification="fixture_verified" if receipt else "unverified",
            )
            for step in STEPS
        },
        fixture_receipt=receipt,
        source_state=source_state,
        comparison_state=comparison_state,
        handoff_state=handoff_state,
        repair_owner=OWNERS[family],
        closure_test="eligible_source_to_selection_publisher_native_reader",
        retry_key=digest([family, digest(source_body(payload)), code, source_state]),
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_pid_consumed=False,
        realized_profit=None,
    )
    return dict(body, contract_sha256=digest(body))


def inspect(contract, *, family, day, payload=None, data_root=None):
    """Verify the native generation, then project structural and data states."""
    if not contract:
        return dict(
            status="unverified",
            findings=["policy_generation_unverified"] if day >= START_DATE else [],
            missing_components=[],
            observation_complete=False,
        )
    c = contract
    if (
        not isinstance(c, dict)
        or c.get("schema") != SCHEMA
        or c.get("family") != family
        or c.get("source_date") != day
        or c.get("contract_sha256")
        != digest({k: v for k, v in c.items() if k != "contract_sha256"})
        or set(c.get("components", {})) != set(STEPS)
        or c.get("runtime_effect") is not False
        or c.get("allowed_runtime_apply") is not False
        or c.get("realized_profit") is not None
        or c.get("actual_pid_consumed") is not False
    ):
        raise ValueError("policy_generation_contract_invalid")
    if payload is not None and c["source_generation"] != digest(source_body(payload)):
        raise ValueError("policy_generation_native_generation_mismatch")
    if any(not isinstance(v, dict) for v in c["components"].values()):
        raise ValueError("policy_generation_component_type_invalid")
    missing = [k for k, v in c["components"].items() if v.get("status") != "supported"]
    if payload is not None and c.get("as_of") != (
        payload.get("generated_at") or payload.get("as_of") or day
    ):
        raise ValueError("policy_generation_clock_binding_invalid")
    verified = (
        data_root is not None
        and c.get("code_sha256") == code_generation(family)
        and bool(c.get("fixture_receipt"))
    )
    if verified and data_root is not None:
        from src.engine.scalping.main_stop_policy import bounded_object

        reference = c["fixture_receipt"]
        path = Path(reference["path"])
        directory = Path(data_root) / "report/postclose_generation_validation"
        if path.resolve().parent != directory.resolve():
            raise ValueError("policy_generation_fixture_path_invalid")
        value, sha = bounded_object(path, 65536)
        verified = (
            sha == reference["sha256"]
            and value.get("schema") == "postclose_generation_fixture_receipt_v1"
            and value.get("status") == "pass"
            and value.get("code_sha256") == c["code_sha256"]
            and value.get("family") == family
            and value.get("closure_tests")
            and value.get("unresolved_findings") == []
            and value.get("receipt_sha256")
            == digest({k: v for k, v in value.items() if k != "receipt_sha256"})
        )
    return dict(
        status="structurally_blocked"
        if missing
        else "verified"
        if verified
        else "unverified",
        missing_components=missing,
        findings=(
            ["policy_generation_component_missing:" + x for x in missing]
            or (
                ["policy_generation_unverified"]
                if not verified and day >= START_DATE
                else []
            )
        ),
        source_state=c.get("source_state"),
        comparison_state=c.get("comparison_state"),
        handoff_state=c.get("handoff_state"),
        source_generation=c["source_generation"],
        code_sha256=c["code_sha256"],
        contract_sha256=c["contract_sha256"],
        repair_owner=c.get("repair_owner"),
        closure_test=c.get("closure_test"),
        observation_complete=True,
        runtime_effect=False,
        allowed_runtime_apply=False,
        realized_profit=None,
    )


def observations(root, day, *, data_root=None):
    """Bounded native receipts; never regenerate reports or evaluate a grid."""
    from src.engine.scalping.main_stop_policy import bounded_object

    root = Path(root)
    data = Path(data_root) if data_root is not None else root / "data"
    items = []
    paths = {
        "entry_cancel_wait": data
        / "report/entry_cancel_wait_tuning"
        / f"entry_cancel_wait_tuning_{day}.json",
        "rising_missed": data
        / "report/rising_missed_classifier_prior"
        / f"rising_missed_classifier_prior_{day}.json",
        "auxiliary": data
        / "report/reversal_auxiliary_tuning"
        / day
        / "evaluation.json",
        "holding_vote": data
        / "report/monitor_snapshots"
        / f"holding_exit_observation_{day}.json",
    }
    for family, path in paths.items():
        if not path.exists() and not path.is_symlink():
            continue
        try:
            payload, report_sha = bounded_object(path, 8 * 1024 * 1024)
            native_payload = (
                payload.get("holding_path_vote_replay") or {}
                if family == "holding_vote"
                else payload
            )
            projection = inspect(
                native_payload.get("policy_generation"),
                family=family,
                day=day,
                payload=native_payload,
                data_root=data,
            )
            scoped = dict(
                projection,
                report_sha256=report_sha,
                native_validated=projection["status"] == "verified",
            )
            items.append(
                dict(
                    scoped,
                    family=family,
                    source_date=day,
                    artifact=str(path),
                    scopes={family: scoped},
                )
            )
        except (OSError, ValueError, TypeError, KeyError) as exc:
            items.append(
                dict(
                    status="unobservable",
                    family=family,
                    source_date=day,
                    artifact=str(path),
                    observation_complete=False,
                    native_validated=False,
                    report_sha256=None,
                    findings=["policy_generation_contract_invalid"],
                    reason=str(exc),
                )
            )
    return items


def retirement_dispositions(root):
    """Selected-code evidence retires expectations; absence is not recovery."""
    from src.engine.scalping.main_stop_policy import bounded_object

    root = Path(root)
    try:
        selector, _ = bounded_object(
            root / "data/runtime/runtime_release_selection.json", 65536
        )
        selected = Path(selector.get("release_root") or "")
        if not selected.is_absolute():
            return {}
        source = selected / "src/engine/error_detectors/artifact_freshness.py"
        if source.is_symlink() or source.stat().st_size > 1024 * 1024:
            return {}
        raw = source.read_bytes()
        if (
            b'"id": "code_improvement_workorder"' in raw
            or b"'id': 'code_improvement_workorder'" in raw
        ):
            return {}
        return {
            "code_improvement_workorder": dict(
                disposition="retired_no_longer_expected",
                effective_date="2026-10-11",
                retirement_contract="native_recommendation_intake_retired_aggregate_v1",
                selected_release=str(selected),
                selected_code_sha256=hashlib.sha256(raw).hexdigest(),
                historical_missing_preserved=True,
            )
        }
    except (OSError, ValueError, TypeError, KeyError):
        return {}
