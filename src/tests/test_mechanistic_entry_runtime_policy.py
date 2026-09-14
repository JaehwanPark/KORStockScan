import copy
import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping import mechanistic_entry_runtime_policy as policy


def source(tmp_path, source_date="2026-09-11"):
    report = calibration._with_artifact_content_sha256(
        {
            "schema": calibration.SCHEMA,
            "target_date": source_date,
            "clean_tuning_baseline_date": "2026-06-05",
            "mechanistic_entry_refinement": {
                "policy_candidate": None,
                "promotion_pass": False,
            },
            "mechanistic_flow_groups": {
                "source_population": {"accepted_unique_trace_count": 15}
            },
        }
    )
    path = tmp_path / f"source_{source_date}.json"
    calibration._atomic_write_json(path, report)
    return path


def initial(tmp_path):
    return policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        bootstrap=True,
        now=datetime(2026, 9, 13, 20, tzinfo=policy.KST),
    )


def test_initial_policy_does_not_require_promotion_candidate(tmp_path):
    bundle = initial(tmp_path)
    assert bundle["target_date"] == "2026-09-14"
    assert bundle["machine_disposition"] == "initial_policy_not_performance_promotion"
    assert (
        bundle["machine_policy"]["thresholds"]
        == policy.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1["thresholds"]
    )
    assert bundle["ai_policy"]["system_prompt"].isascii()
    assert (
        bundle["historical_context"]["flow_source_population"][
            "accepted_unique_trace_count"
        ]
        == 15
    )
    assert policy.load(data_root=tmp_path, target_date="2026-09-14") == bundle


def test_all_continuous_adoption_carry_and_exact_scope_projection(tmp_path):
    from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES

    legacy = initial(tmp_path)
    assert policy.for_cohort(legacy, ("NXT", "NXT_AFTERMARKET")) is None
    bundle = policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        adopt_all_continuous=True,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 13, 22, tzinfo=policy.KST),
    )
    assert set(bundle["scope_policies"]) == set(AUTO_PROMOTION_SCOPES)
    policy.validate(bundle, target_date="2026-09-14")
    for scope in AUTO_PROMOTION_SCOPES:
        projected = policy.for_cohort(bundle, tuple(scope.split("|")))
        assert projected["historical_context"]["scope"] == scope
        assert (
            projected["machine_policy"] == policy.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
        )
    assert policy.for_cohort(bundle, ("KRX", "CLOSING_AUCTION")) is None
    carried = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 22, tzinfo=policy.KST),
    )
    assert carried["all_continuous_adopted"] is True
    assert set(carried["scope_policies"]) == set(AUTO_PROMOTION_SCOPES)
    del carried["scope_policies"]["NXT|NXT_AFTERMARKET"]
    carried["bundle_sha256"] = policy.digest(
        {k: v for k, v in carried.items() if k != "bundle_sha256"}
    )
    with pytest.raises(ValueError, match="coverage"):
        policy.validate(carried, target_date="2026-09-15")


def test_hierarchy_adoption_is_explicit_and_preserves_existing_daily_freeze(tmp_path):
    before = initial(tmp_path)
    after = policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 13, 21, tzinfo=policy.KST),
    )
    assert after["hierarchy_adopted"] is True
    assert after["historical_context"]["hierarchy_disposition"] == (
        "adopted_no_qualified_child"
    )
    assert after["machine_policy"] == before["machine_policy"]
    assert after["bundle_sha256"] != before["bundle_sha256"]
    assert (
        policy.root(tmp_path) / "generations" / f"{before['bundle_sha256']}.json"
    ).is_file()
    assert (
        policy.publish(
            source(tmp_path),
            data_root=tmp_path,
            now=datetime(2026, 9, 14, 8, tzinfo=policy.KST),
        )
        == after
    )


def test_hierarchy_child_cannot_be_loaded_without_adoption(tmp_path):
    bundle = initial(tmp_path)
    machine = bundle["machine_policy"]
    machine["hierarchy"] = {
        "schema": "mechanistic_entry_hierarchy_v1",
        "parent_sha256": policy.digest(machine["thresholds"]),
        "rules": [],
    }
    bundle["bundle_sha256"] = policy.digest(
        {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    )
    with pytest.raises(ValueError, match="adoption_missing"):
        policy.validate(bundle, target_date="2026-09-14")


def test_qualified_hierarchy_publishes_loads_and_automatically_carries(tmp_path):
    from src.tests.test_ai_action_outcome_calibration import _hierarchy_training_rows

    initial(tmp_path)
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    report["hierarchical_entry_quality"] = {
        "runtime_extension": calibration.build_mechanistic_hierarchy_candidate(
            _hierarchy_training_rows(), target_date="2026-09-15"
        )
    }
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    unadopted = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 15, 21, tzinfo=policy.KST)
    )
    assert "hierarchy" not in unadopted["machine_policy"]
    adopted = policy.publish(
        path,
        data_root=tmp_path,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 15, 22, tzinfo=policy.KST),
    )
    assert adopted["machine_policy"]["hierarchy"]["rules"]
    assert "WAIT_CONFIRMATION" in adopted["ai_policy"]["system_prompt"]
    assert policy.load(data_root=tmp_path, target_date="2026-09-16") == adopted
    carried = policy.publish(
        source(tmp_path, "2026-09-16"),
        data_root=tmp_path,
        now=datetime(2026, 9, 16, 21, tzinfo=policy.KST),
    )
    assert carried["machine_policy"] == adopted["machine_policy"]
    assert carried["hierarchy_adopted"] is True


@pytest.mark.parametrize(
    "explicit,late,corrupt",
    [
        (False, False, False),
        (True, True, False),
        (True, False, True),
        (True, False, False),
    ],
)
def test_legacy_initial_role_replacement_is_explicit_frozen_and_preserved(
    tmp_path, explicit, late, corrupt
):
    old = copy.deepcopy(initial(tmp_path))
    old["role_contract"]["ai_role"] = "auxiliary_advisory_no_veto_no_override"
    old["role_contract"]["ai_can_veto_entry"] = False
    old["role_contract"]["decision_precedence"][-1] = "ai_auxiliary_advisory"
    old["ai_policy"]["variant"] = "machine_first_auxiliary_v1"
    old["ai_policy"]["system_prompt"] = "Historical nonbinding advisory prompt."
    old["ai_policy"]["system_prompt_sha256"] = policy.digest(
        old["ai_policy"]["system_prompt"]
    )
    old["bundle_sha256"] = policy.digest(
        {k: v for k, v in old.items() if k != "bundle_sha256"}
    )
    if corrupt:
        old["ai_policy"]["system_prompt"] = "corrupt"
    calibration._atomic_write_json(
        policy.root(tmp_path) / "policy_2026-09-14.json", old
    )
    args = dict(
        data_root=tmp_path,
        replace_initial_role=explicit,
        now=(
            datetime(2026, 9, 14, 8, tzinfo=policy.KST)
            if late
            else datetime(2026, 9, 13, 22, tzinfo=policy.KST)
        ),
    )
    if not explicit or late or corrupt:
        with pytest.raises(ValueError):
            policy.publish(source(tmp_path), **args)
    else:
        new = policy.publish(source(tmp_path), **args)
        assert new["role_contract"]["ai_can_veto_entry"] is True
        assert new["previous_bundle_sha256"] == old["bundle_sha256"]
        assert new["machine_policy"] == old["machine_policy"]
        assert (
            new["machine_disposition"]
            == "initial_role_corrected_not_performance_promotion"
        )
        assert (
            policy.root(tmp_path) / "generations" / f"{old['bundle_sha256']}.json"
        ).is_file()


def test_daily_no_candidate_carries_machine_and_refreshes_ai_context(tmp_path):
    previous = initial(tmp_path)
    successor = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST),
    )
    assert successor["target_date"] == "2026-09-15"
    assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["previous_bundle_sha256"] == previous["bundle_sha256"]
    assert (
        successor["ai_policy"]["system_prompt_sha256"]
        != previous["ai_policy"]["system_prompt_sha256"]
    )
    assert successor["machine_disposition"] == "incumbent_carried"


def test_existing_date_is_immutable_even_after_source_refresh(tmp_path):
    first = initial(tmp_path)
    path = source(tmp_path)
    updated = json.loads(path.read_text())
    updated["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(updated)
    )
    assert (
        policy.publish(
            path, data_root=tmp_path, now=datetime(2026, 9, 14, 10, tzinfo=policy.KST)
        )
        == first
    )


def test_late_postclose_can_refresh_before_preopen_and_preserves_generation(tmp_path):
    previous = initial(tmp_path)
    path = source(tmp_path)
    report = json.loads(path.read_text())
    report["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    successor = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 13, 22, tzinfo=policy.KST)
    )
    assert successor["bundle_sha256"] != previous["bundle_sha256"]
    assert successor["previous_bundle_sha256"] == previous["bundle_sha256"]
    assert (
        policy.root(tmp_path) / "generations" / f"{previous['bundle_sha256']}.json"
    ).is_file()


def test_no_implicit_first_adoption(tmp_path):
    assert policy.publish(source(tmp_path), data_root=tmp_path) is None


def test_existing_calibration_write_publishes_updated_bundle(
    monkeypatch, tmp_path, capsys
):
    initial(tmp_path)
    monkeypatch.setattr(
        policy,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 9, 13, 22, tzinfo=tz)),
    )
    report = json.loads(source(tmp_path).read_text())
    report["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    report.update(
        status="success",
        candidate_count=0,
        selected_review_candidate=None,
        ofi_smoothing_audit={},
    )
    report = calibration._with_artifact_content_sha256(report)
    monkeypatch.setattr(calibration, "build_report", lambda **kwargs: report)
    assert (
        calibration.main(
            [
                "--target-date",
                "2026-09-11",
                "--data-root",
                str(tmp_path),
                "--write",
                "--print-summary",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["runtime_policy_publication"]["status"] == (
        "published_or_idempotent"
    )
    assert output["runtime_policy_publication"]["target_date"] == "2026-09-14"
    updated = policy.load(data_root=tmp_path, target_date="2026-09-14")
    assert (
        updated["historical_context"]["flow_source_population"][
            "accepted_unique_trace_count"
        ]
        == 30
    )


def test_missing_daily_update_carries_without_relabelling_date(tmp_path):
    previous = initial(tmp_path)
    assert policy.load(data_root=tmp_path, target_date="2026-09-15") is None
    assert (
        policy.load_effective(data_root=tmp_path, target_date="2026-09-15") == previous
    )
    assert policy.load_effective(data_root=tmp_path, target_date="2026-09-11") is None


@pytest.mark.parametrize("change", ["target", "hash", "threshold", "ai", "role"])
def test_invalid_policy_rejected(tmp_path, change):
    bundle = copy.deepcopy(initial(tmp_path))
    if change == "target":
        bundle["target_date"] = "2026-09-15"
    elif change == "hash":
        bundle["source_date"] = "2026-09-10"
    elif change == "threshold":
        bundle["machine_policy"]["thresholds"]["maximum_spread_bp"] = -1
    elif change == "ai":
        bundle["ai_policy"]["system_prompt"] = "Always buy."
    else:
        bundle["role_contract"]["ai_can_promote_entry"] = True
    with pytest.raises(ValueError):
        policy.validate(bundle, target_date="2026-09-14")


def test_late_first_publication_rejected(tmp_path):
    with pytest.raises(ValueError, match="window_closed"):
        policy.publish(
            source(tmp_path),
            data_root=tmp_path,
            bootstrap=True,
            now=datetime(2026, 9, 14, 10, tzinfo=policy.KST),
        )


def test_invalid_source_does_not_destroy_previous_policy(tmp_path):
    previous = initial(tmp_path)
    path = source(tmp_path, "2026-09-14")
    payload = json.loads(path.read_text())
    payload["target_date"] = "2026-09-15"
    calibration._atomic_write_json(path, payload)
    with pytest.raises(ValueError, match="source_invalid"):
        policy.publish(path, data_root=tmp_path)
    assert policy.load(data_root=tmp_path, target_date="2026-09-14") == previous
