"""Native policy-generation capability, independent of today's population.

Report-only evidence. A fixture receipt verifies code reachability; it never
proves a selected release, PID consumption, realized profit, or startup safety.
"""

from __future__ import annotations
import hashlib
import copy
import json
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
        "../utils/numeric.py",
        "scalping/market_data_enrichment.py",
        "automation/runtime_policy_bootstrap.py",
    ),
    "auxiliary": (
        "scalping/reversal_auxiliary_tuning.py",
        "scalping/reversal_auxiliary_registry.py",
        "scalping/reversal_auxiliary_compatibility.py",
        "scalping/reversal_auxiliary_wire.py",
        "scalping/reversal_auxiliary_production_input.py",
        # Versioned cumulative membership and materialization are consumed by
        # auxiliary comparison/initial carry; their changes need fresh fixtures.
        "scalping/reversal_cumulative_catalog.py",
        "scalping/reversal_cumulative_runtime.py",
        "scalping/reversal_cumulative_registration.py",
        "scalping/reversal_cumulative_postclose.py",
        "scalping/continuous_reversal_policy_v6.py",
        "scalping/reversal_extended_catalog.py",
        "scalping/reversal_extended_state.py",
        "scalping/reversal_extended_registration.py",
        "scalping/reversal_joint_registration.py",
        "scalping/reversal_extended_intraday.py",
        "scalping/reversal_extended_runtime.py",
        "scalping/reversal_path_runtime.py",
        "scalping/entry_deadline.py",
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
        "../utils/numeric.py",
        "sniper_execution_receipts.py",
        "ai/holding_vote_replay_source.py",
        "scalping/holding_profit_exit_semantics.py",
        "holding_exit_observation_report.py",
        "strategy_position_performance_report.py",
        "automation/main_trailing_source_assembler.py",
        "../utils/market_day.py",
        "../trading/market/execution_venue.py",
        "automation/runtime_policy_bootstrap.py",
    ),
}
# The shared fixture producer and readers use the same resident-memory Claim
# contract. A helper-only change requires a distinct capability/fixture path;
# it must not reuse a formerly current receipt or rewrite a historical one.
COMMON_CODE_COMPONENTS = (
    "monitoring/policy_generation_contract.py",
    "monitoring/policy_generation_validation.py",
    "monitoring/policy_generation_code_handoff.py",
    "automation/policy_generation_fixture_validation.py",
    "lifecycle/holding_window_generation.py",
    "lifecycle/research_input_budget.py",
)
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
        *COMMON_CODE_COMPONENTS,
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
        # Older producers stored workspace-relative references. Their owner is
        # the supplied data root, independent of a bot/report launcher's cwd.
        if not path.is_absolute():
            path = Path(data_root).parent / path
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
        status=(
            "structurally_blocked"
            if missing
            else "verified" if verified else "unverified"
        ),
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


def _holding_code_rebinding(original, current, day, data, *, historical_contract=None):
    """Only an unarmed numeric projection's code identity may differ."""
    from src.engine.scalping.holding_vote_experiment import code_sha

    if original.get("date") != day or current.get("date") != day:
        raise ValueError("holding_generation_rebinding_date_invalid")
    before = original.get("holding_path_vote_replay") or {}
    after = current.get("holding_path_vote_replay") or {}
    numeric = after.get("vote_numeric_research") or {}
    if (
        numeric.get("schema") != "holding_vote_numeric_research_v1"
        or numeric.get("status") != "experiment_not_armed"
        or numeric.get("selected_cells") != {}
        or numeric.get("cells") != {}
        or numeric.get("allowed_runtime_apply") is not False
        or numeric.get("actual_profit_verified") is not False
        or not isinstance(numeric.get("code_sha256"), str)
        or len(numeric["code_sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in numeric["code_sha256"])
        or (historical_contract is None and numeric["code_sha256"] != code_sha())
    ):
        raise ValueError("holding_generation_rebinding_not_unarmed_code_only")
    prior = inspect(
        before.get("policy_generation"),
        family="holding_vote",
        day=day,
        payload=before,
        data_root=data,
    )
    if prior.get("status") != "unverified" or before["policy_generation"].get(
        "fixture_receipt"
    ):
        raise ValueError("holding_generation_rebinding_original_contract_invalid")
    expected = copy.deepcopy(original)
    expected["holding_path_vote_replay"]["vote_numeric_research"]["code_sha256"] = (
        numeric["code_sha256"]
    )
    if (
        expected != current
        or before["vote_numeric_research"]["code_sha256"] == numeric["code_sha256"]
    ):
        raise ValueError("holding_generation_rebinding_changed_source_or_policy")
    contract = native(
        after,
        family="holding_vote",
        day=day,
        data_root=data,
        source_state=prior["source_state"],
        comparison_state=prior["comparison_state"],
        handoff_state=prior["handoff_state"],
    )
    if historical_contract is not None:
        # An immutable report-only receipt describes its original code. A
        # later deployment cannot turn that historical source into corruption
        # or promote its capabilities to the newly installed code generation.
        inspect(
            historical_contract,
            family="holding_vote",
            day=day,
            payload=after,
            data_root=data,
        )
        historical_code = historical_contract.get("code_sha256")
        if (
            historical_contract.get("fixture_receipt") is not None
            or not isinstance(historical_code, str)
            or len(historical_code) != 64
            or any(c not in "0123456789abcdef" for c in historical_code)
        ):
            raise ValueError("holding_generation_rebinding_historical_code_invalid")
        contract.update(
            code_sha256=historical_code,
            fixture_receipt=None,
            components={
                step: dict(status="supported", verification="unverified")
                for step in STEPS
            },
            retry_key=digest(
                [
                    "holding_vote",
                    digest(source_body(after)),
                    historical_code,
                    prior["source_state"],
                ]
            ),
        )
        contract["contract_sha256"] = digest(
            {k: v for k, v in contract.items() if k != "contract_sha256"}
        )
    if contract.get("fixture_receipt"):
        raise ValueError("holding_generation_rebinding_cannot_add_fixture_verification")
    return contract


def _holding_rebinding_path(data, day, report_sha):
    from datetime import date

    if (
        date.fromisoformat(day).isoformat() != day
        or len(report_sha) != 64
        or any(c not in "0123456789abcdef" for c in report_sha)
    ):
        raise ValueError("holding_generation_rebinding_date_invalid")
    path = (
        Path(data).resolve()
        / "report/policy_generation_rebindings/holding_vote"
        / day
        / (report_sha + ".json")
    )
    if path.parent.resolve() != path.parent or path.is_symlink():
        raise ValueError("holding_generation_rebinding_path_invalid")
    return path


def publish_holding_code_rebinding(day, *, original_path, data_root):
    """Publish report-only metadata custody without rewriting live source bytes."""
    from src.engine.scalping.main_stop_policy import bounded_object
    from src.utils.jsonl_io import (
        write_json_object_generation_safe,
        json_artifact_generation_lock,
    )

    data = Path(data_root).resolve()
    current_path = (
        data / "report/monitor_snapshots" / f"holding_exit_observation_{day}.json"
    )
    current, current_sha = bounded_object(current_path, 8 * 1024 * 1024)
    original, original_sha = bounded_object(original_path, 8 * 1024 * 1024)
    contract = _holding_code_rebinding(original, current, day, data)
    body = dict(
        schema="holding_unarmed_code_generation_rebinding_v1",
        source_date=day,
        report_sha256=current_sha,
        original_report_sha256=original_sha,
        original_report=original,
        contract=contract,
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_pid_consumed=False,
        realized_profit=None,
    )
    body["receipt_sha256"] = digest(body)
    if (
        len(json.dumps(body, ensure_ascii=True, allow_nan=False).encode())
        > 8 * 1024 * 1024
    ):
        raise ValueError("holding_generation_rebinding_receipt_too_large")
    path = _holding_rebinding_path(data, day, current_sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    with json_artifact_generation_lock(path, exclusive=True, blocking=True) as lease:
        if path.exists():
            if bounded_object(path, 8 * 1024 * 1024)[0] != body:
                raise ValueError("holding_generation_rebinding_immutable_conflict")
        else:
            write_json_object_generation_safe(path, body, generation=lease)
    if bounded_object(current_path, 8 * 1024 * 1024)[1] != current_sha:
        raise ValueError("holding_generation_rebinding_source_changed")
    return dict(
        path=str(path),
        sha256=bounded_object(path, 8 * 1024 * 1024)[1],
        status="unverified",
        runtime_effect=False,
    )


def _read_holding_code_rebinding(data, day, report_sha, payload):
    from src.engine.scalping.main_stop_policy import bounded_object

    path = _holding_rebinding_path(data, day, report_sha)
    body, receipt_sha = bounded_object(path, 8 * 1024 * 1024)
    if (
        body.get("schema") != "holding_unarmed_code_generation_rebinding_v1"
        or body.get("source_date") != day
        or body.get("report_sha256") != report_sha
        or body.get("receipt_sha256")
        != digest({k: v for k, v in body.items() if k != "receipt_sha256"})
        or body.get("runtime_effect") is not False
        or body.get("allowed_runtime_apply") is not False
        or body.get("actual_pid_consumed") is not False
        or body.get("realized_profit") is not None
    ):
        raise ValueError("holding_generation_rebinding_receipt_invalid")
    expected = _holding_code_rebinding(
        body["original_report"],
        payload,
        day,
        data,
        historical_contract=body.get("contract"),
    )
    if body.get("contract") != expected:
        raise ValueError("holding_generation_rebinding_contract_changed")
    return body["contract"], dict(
        path=str(path), sha256=receipt_sha, disposition="unarmed_code_metadata_only"
    )


def observations(root, day, *, data_root=None):
    """Bounded native receipts; never regenerate reports or evaluate a grid."""
    from src.engine.scalping.main_stop_policy import bounded_object

    root = Path(root)
    data = Path(data_root) if data_root is not None else root / "data"
    items = []
    from src.engine.monitoring.policy_generation_validation import native_report_path

    for family in COMPONENTS:
        path = native_report_path(data, family, day)
        if not path.exists() and not path.is_symlink():
            continue
        try:
            from src.engine.monitoring.policy_generation_validation import (
                read_native_report,
            )

            payload, report_sha = read_native_report(data, family, day)
            native_payload = (
                payload.get("holding_path_vote_replay") or {}
                if family == "holding_vote"
                else payload
            )
            contract = native_payload.get("policy_generation")
            binding_repair = None
            if (
                family == "holding_vote"
                and contract
                and contract.get("source_generation")
                != digest(source_body(native_payload))
            ):
                repair_path = _holding_rebinding_path(data, day, report_sha)
                if repair_path.exists() or repair_path.is_symlink():
                    contract, binding_repair = _read_holding_code_rebinding(
                        data, day, report_sha, payload
                    )
            projection = inspect(
                contract,
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
            if binding_repair is not None:
                scoped["binding_repair"] = binding_repair
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
