import json
from datetime import datetime

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import entry_setup_paired_replay_batch as batch
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer


def test_refresh_rebinds_only_metadata_without_provider_or_runtime_evidence_change(
    monkeypatch, tmp_path
):
    day = "2026-09-07"
    monkeypatch.setattr(batch, "BATCH_DIR", tmp_path / "batch")
    monkeypatch.setattr(optimizer, "ENTRY_BATCH_DIR", batch.BATCH_DIR)
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    plan = {cohort: version for cohort in batch.DEFAULT_COHORTS}
    cohort_contract = optimizer._entry_cohort_contract({})
    source = {
        "status": "optimizer_candidate_plan_applied_offline_only",
        "artifact_content_sha256": "f" * 64,
        "cohort_contract": cohort_contract,
        "cohort_contract_sha256": cohort_contract["contract_content_sha256"],
    }
    monkeypatch.setattr(batch, "_optimizer_candidate_plan", lambda _: (plan, source))
    monkeypatch.setattr(
        batch, "_run_quality_cli", lambda _: pytest.fail("provider replay forbidden")
    )
    monkeypatch.setattr(
        batch,
        "publish_live_candidate",
        lambda **_: pytest.fail("runtime republication forbidden"),
    )
    detailed_path = tmp_path / "detailed.json"
    detailed = quality._with_artifact_content_sha256(
        {"schema": quality.DETAILED_PAIRED_SCHEMA, "target_date": day}
    )
    detailed_path.write_text(json.dumps(detailed))
    monkeypatch.setattr(quality, "detailed_paired_path", lambda *_, **__: detailed_path)
    original = {
        "schema": batch.BATCH_SCHEMA,
        "target_date": day,
        "status": "completed_offline_only",
        "candidate_prompt_version": version,
        **batch.OFFLINE_BATCH_CONTRACT,
        "cohorts": [
            {
                "effective_venue": v,
                "session_bucket": s,
                "candidate_prompt_version": version,
                "status": "completed_offline_only",
                "report_path": str(detailed_path),
                "detailed_artifact_content_sha256": detailed["artifact_content_sha256"],
            }
            for v, s in batch.DEFAULT_COHORTS
        ],
    }
    batch._atomic_write_json(batch.batch_status_path(day), original)
    result = batch.refresh_optimizer_binding(target_date=day, write=True)
    assert result["candidate_prompt_selection_source"] == source
    assert result["cohort_contract"] == cohort_contract
    assert (
        result["cohort_contract_sha256"] == cohort_contract["contract_content_sha256"]
    )
    assert result["optimizer_binding_refresh_provider_calls"] == 0
    assert batch.live_policy._batch_evidence(
        result
    ) == batch.live_policy._batch_evidence(original)
    detailed_path.write_text(json.dumps({**detailed, "changed": True}))
    with pytest.raises(ValueError, match="detailed_generation_changed"):
        batch.refresh_optimizer_binding(target_date=day, write=False)


def test_binding_refresh_rejects_candidate_switch(monkeypatch):
    monkeypatch.setattr(
        optimizer,
        "_frozen_entry_batch_selection",
        lambda _: {
            ("KRX", "KRX_REGULAR"): {
                "prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[0]
            }
        },
    )
    monkeypatch.setattr(
        batch,
        "_optimizer_candidate_plan",
        lambda _: (
            {("KRX", "KRX_REGULAR"): optimizer.ENTRY_CANDIDATE_ORDER[1]},
            {"status": "optimizer_candidate_plan_applied_offline_only"},
        ),
    )
    with pytest.raises(ValueError, match="changed_executed_candidate"):
        batch.refresh_optimizer_binding(target_date="2026-09-07", write=False)


def test_exhausted_registry_never_replays_default_candidate(monkeypatch):
    version = optimizer.ENTRY_CANDIDATE_ORDER[0]
    monkeypatch.setattr(
        batch,
        "_optimizer_candidate_plan",
        lambda _: (
            {cohort: version for cohort in batch.DEFAULT_COHORTS},
            {"research_only_cohorts": [f"{v}/{s}" for v, s in batch.DEFAULT_COHORTS]},
        ),
    )
    monkeypatch.setattr(
        quality,
        "_offline_openai_api_keys",
        lambda: pytest.fail("no provider credential access required"),
    )
    monkeypatch.setattr(
        batch,
        "_cohort_result",
        lambda **_: pytest.fail("exhausted registry must not replay"),
    )
    monkeypatch.setattr(
        batch,
        "publish_live_candidate",
        lambda **_: pytest.fail("exhausted registry must not publish live candidate"),
    )
    report = batch.run_batch(
        target_date="2026-09-07",
        as_of=datetime(2026, 9, 7, 22, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=False,
    )
    assert report["status"] == "completed_offline_only"
    assert all(
        row["status"] == "hold_candidate_registry_exhausted"
        for row in report["cohorts"]
    )
    assert (
        report["krx_bounded_live_candidate"]["status"]
        == "blocked_candidate_registry_exhausted_source_only"
    )


def test_optimizer_candidate_plan_is_hash_bound_and_cohort_isolated(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(optimizer, "REPORT_DIR", tmp_path / "optimizer")
    target_date = "2026-09-04"
    body = {
        "schema": optimizer.SCHEMA,
        "target_date": target_date,
        "status": "ready_source_only_continuous_search",
        "stage_optimizers": {
            "entry": {
                "cohort_optimizers": [
                    {
                        "effective_venue": "KRX",
                        "session_bucket": "KRX_REGULAR",
                        "prompt_search_ready": True,
                        "cross_cohort_selection_forbidden": True,
                        "selected_challenger": {
                            "prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[1]
                        },
                    },
                    {
                        "effective_venue": "NXT",
                        "session_bucket": "NXT_AFTERMARKET",
                        "prompt_search_ready": True,
                        "cross_cohort_selection_forbidden": True,
                        "selected_challenger": {
                            "prompt_version": optimizer.ENTRY_CANDIDATE_ORDER[0]
                        },
                    },
                ]
            }
        },
        "runtime_effect": False,
        "runtime_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "entry_cohort_contract": optimizer._entry_cohort_contract({}),
    }
    report = {**body, "artifact_content_sha256": optimizer._canonical_sha256(body)}
    path, _markdown = optimizer.report_paths(target_date)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report), encoding="utf-8")

    plan, source = batch._optimizer_candidate_plan(target_date)

    assert plan == {
        ("KRX", "KRX_REGULAR"): optimizer.ENTRY_CANDIDATE_ORDER[1],
        ("NXT", "NXT_AFTERMARKET"): optimizer.ENTRY_CANDIDATE_ORDER[0],
    }
    assert source["status"] == "optimizer_candidate_plan_applied_offline_only"

    report["stage_optimizers"]["entry"]["cohort_optimizers"][0][
        "effective_venue"
    ] = "NXT"
    path.write_text(json.dumps(report), encoding="utf-8")
    fallback, source = batch._optimizer_candidate_plan(target_date)
    assert set(fallback.values()) == {batch.DEFAULT_CANDIDATE_PROMPT_VERSION}
    assert source["status"] == "fallback_default_candidate"


def test_dual_aftermarket_contract_is_observe_only_without_provider_replay():
    contract = optimizer._entry_cohort_contract(
        {
            "candidate_summaries": [
                {
                    "stage": "entry",
                    "effective_venue": "INTEGRATED",
                    "session_bucket": "KRX_NXT_AFTERMARKET",
                    "market_data_route": "SOR",
                    "cohort_key_version": "v2",
                    "authority_state": "OBSERVE_ONLY",
                }
            ]
        }
    )
    rows = batch._dual_source_only_cohorts({"cohort_contract": contract})

    assert contract["version"] == "v2"
    assert rows == [
        {
            "effective_venue": "INTEGRATED",
            "session_bucket": "KRX_NXT_AFTERMARKET",
            "market_data_route": "SOR",
            "cohort_key_version": "v2",
            "authority_state": "OBSERVE_ONLY",
            "status": "completed_observe_only",
            "provider_call_performed": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "next_action": "retain_route_isolated_source_observation",
        }
    ]


def test_batch_waits_for_full_day_maturity_without_provider_or_artifact(monkeypatch):
    called = []
    monkeypatch.setattr(batch, "_cohort_result", lambda **kwargs: called.append(kwargs))

    report = batch.run_batch(
        target_date="2026-08-06",
        as_of=datetime(2026, 8, 6, 20, 59, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=False,
    )

    assert report["status"] == "not_ready_full_day_outcome_maturity"
    assert called == []
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True


def test_dynamic_candidate_blocks_stale_live_artifact_before_maturity(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(batch, "BATCH_DIR", tmp_path / "batch")
    monkeypatch.setattr(
        batch.live_policy, "LIVE_CANDIDATE_DIR", tmp_path / "candidates"
    )
    candidate = optimizer.ENTRY_CANDIDATE_ORDER[1]
    monkeypatch.setattr(
        batch,
        "_optimizer_candidate_plan",
        lambda _target_date: (
            {
                ("KRX", "KRX_REGULAR"): candidate,
                ("NXT", "NXT_AFTERMARKET"): batch.DEFAULT_CANDIDATE_PROMPT_VERSION,
            },
            {"status": "optimizer_candidate_plan_applied_offline_only"},
        ),
    )
    stale_path = batch.live_policy.live_candidate_path("2026-09-04")
    stale_path.parent.mkdir(parents=True)
    stale_path.write_text(
        json.dumps({"status": "live_auto_apply_ready", "allowed_runtime_apply": True}),
        encoding="utf-8",
    )

    report = batch.run_batch(
        target_date="2026-09-04",
        as_of=datetime(2026, 9, 4, 20, 59, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=True,
    )

    assert report["status"] == "not_ready_full_day_outcome_maturity"
    blocked = json.loads(stale_path.read_text(encoding="utf-8"))
    assert blocked["status"] == "blocked"
    assert blocked["selected_prompt_version"] == candidate
    assert blocked["allowed_runtime_apply"] is False


def test_predecessor_wait_treats_failed_as_recoverable_until_succeeded(monkeypatch):
    observed = iter(
        [
            {"status": "failed", "reason": "tail_repair_pending"},
            {"status": "failed", "reason": "tail_repair_running"},
            {"status": "succeeded", "reason": "tail_repair_done_reconciliation"},
        ]
    )
    clock = {"now": 0.0}

    monkeypatch.setattr(batch, "_read_json", lambda _path: next(observed))
    monkeypatch.setattr(batch.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        batch.time,
        "sleep",
        lambda seconds: clock.__setitem__("now", clock["now"] + seconds),
    )

    passed, predecessor = batch._wait_for_predecessor(
        target_date="2026-08-11",
        wait_sec=120,
        interval_sec=30,
    )

    assert passed is True
    assert predecessor["status"] == "succeeded"
    assert clock["now"] == 60


def test_predecessor_wait_closes_failed_state_only_after_timeout(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(
        batch,
        "_read_json",
        lambda _path: {"status": "failed", "reason": "tail_repair_pending"},
    )
    monkeypatch.setattr(batch.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        batch.time,
        "sleep",
        lambda seconds: clock.__setitem__("now", clock["now"] + seconds),
    )

    passed, predecessor = batch._wait_for_predecessor(
        target_date="2026-08-11",
        wait_sec=60,
        interval_sec=30,
    )

    assert passed is False
    assert predecessor["status"] == "failed"
    assert clock["now"] == 60


def test_main_uses_distinct_exit_code_for_predecessor_timeout(monkeypatch):
    monkeypatch.setattr(
        batch,
        "run_batch",
        lambda **_kwargs: {"status": "blocked_predecessor_timeout"},
    )

    exit_code = batch.main(
        [
            "--date",
            "2026-08-11",
            "--predecessor-wait-sec",
            "0",
        ]
    )

    assert exit_code == 3


def test_batch_runs_krx_and_nxt_as_separate_outcome_blind_cohorts(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(batch, "BATCH_DIR", tmp_path / "batch")
    monkeypatch.setattr(quality, "RUNTIME_DIR", tmp_path / "runtime")
    monkeypatch.setattr(
        quality,
        "DETAILED_PAIRED_REPORT_DIR",
        tmp_path / "detailed",
    )
    monkeypatch.setattr(quality, "_offline_openai_api_keys", lambda: ["configured"])
    published = []
    monkeypatch.setattr(
        batch,
        "publish_live_candidate",
        lambda **kwargs: (
            published.append(kwargs)
            or {
                "status": "blocked",
                "effective_date": "2026-08-07",
                "allowed_runtime_apply": False,
            }
        ),
    )

    def fake_quality_cli(argv):
        venue = argv[argv.index("--venue") + 1]
        session = argv[argv.index("--session-bucket") + 1]
        mode = argv[argv.index("--mode") + 1]
        if mode == "control":
            quality._atomic_write_json(
                quality.control_path(
                    "2026-08-06",
                    effective_venue=venue,
                    session_bucket=session,
                ),
                {
                    "status": "control_manifest_frozen_collect_exact_samples",
                    "controls": [
                        {
                            "decision_stage": "entry",
                            "provider_actual": "openai",
                            "sample_count": 50,
                        }
                    ],
                },
            )
            return
        assert mode == "detailed"
        assert "--execute-candidate" in argv
        quality._atomic_write_json(
            quality.detailed_paired_path(
                "2026-08-06",
                candidate_prompt_version=(
                    batch.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
                ),
                effective_venue=venue,
                session_bucket=session,
            ),
            {
                "prepared_request_count": 30,
                "request_count": 30,
                "result_count": 30,
                "candidate_execution_performed": True,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "candidate_exposure_decision_count": 12,
                "candidate_exposure_unique_symbol_count": 8,
                "promotion_quality_gate_pass": False,
                "candidate_execution_selection": {
                    "policy": (
                        "complete_eligible_census"
                        if venue == "NXT"
                        else quality.CANDIDATE_EXECUTION_SELECTION_POLICY
                    ),
                    "outcome_blind": True,
                    "contract_pass": True,
                    "eligible_pending_count": 30,
                    "selected_execution_count": 30,
                    "deferred_new_count": 0,
                    "distinct_execution_count": 30,
                    "distinct_execution_cap": 30,
                    "distinct_execution_cap_pass": True,
                    "checkpoint_evaluated_setup_state_counts": {"READY": 30},
                },
            },
        )

    monkeypatch.setattr(batch, "_run_quality_cli", fake_quality_cli)

    report = batch.run_batch(
        target_date="2026-08-06",
        as_of=datetime(2026, 8, 6, 21, 5, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=True,
    )

    assert report["status"] == "completed_offline_only"
    assert [row["effective_venue"] for row in report["cohorts"]] == ["KRX", "NXT"]
    assert all(
        row["candidate_execution_selection"]["outcome_blind"] is True
        for row in report["cohorts"]
    )
    assert report["cohorts"][1]["candidate_execution_selection"]["policy"] == (
        "complete_eligible_census"
    )
    persisted = json.loads(batch.batch_status_path("2026-08-06").read_text())
    assert persisted["status"] == "completed_offline_only"
    assert persisted["actual_order_submitted"] is False
    assert report["krx_bounded_live_candidate"]["status"] == "blocked"
    assert published[0]["source_date"] == "2026-08-06"
    assert published[0]["write"] is True


def test_nxt_failure_does_not_cancel_completed_krx_candidate(monkeypatch):
    monkeypatch.setattr(quality, "_offline_openai_api_keys", lambda: ["configured"])

    def fake_cohort(**kwargs):
        if kwargs["venue"] == "NXT":
            raise RuntimeError("nxt_provider_failed")
        return {
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "status": "completed_offline_only",
            "promotion_quality_gate_pass": True,
            "candidate_execution_selection": {
                "outcome_blind": True,
                "contract_pass": True,
            },
        }

    published = []
    monkeypatch.setattr(batch, "_cohort_result", fake_cohort)
    monkeypatch.setattr(
        batch,
        "publish_live_candidate",
        lambda **kwargs: (
            published.append(kwargs)
            or {
                "status": "live_auto_apply_ready",
                "effective_date": "2026-08-07",
                "allowed_runtime_apply": True,
            }
        ),
    )

    report = batch.run_batch(
        target_date="2026-08-06",
        as_of=datetime(2026, 8, 6, 21, 5, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=False,
    )

    assert report["status"] == "completed_offline_only_with_cohort_failures"
    assert report["cohort_failure_count"] == 1
    assert report["cohorts"][0]["status"] == "completed_offline_only"
    assert report["cohorts"][1]["status"] == "failed_offline_cohort"
    assert report["krx_bounded_live_candidate"]["status"] == ("live_auto_apply_ready")
    assert published[0]["batch_report"] is report


def test_batch_executes_and_publishes_registered_v2_15_bounded_candidate(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(quality, "_offline_openai_api_keys", lambda: ["configured"])
    monkeypatch.setattr(batch, "BATCH_DIR", tmp_path / "batch")
    live_policy = batch.live_policy
    monkeypatch.setattr(live_policy, "LIVE_CANDIDATE_DIR", tmp_path / "candidates")
    optimizer_candidate = "decision_quality_v2_15_bounded_recovery"
    candidate_plan = {
        ("KRX", "KRX_REGULAR"): optimizer_candidate,
        ("NXT", "NXT_AFTERMARKET"): batch.DEFAULT_CANDIDATE_PROMPT_VERSION,
    }
    monkeypatch.setattr(
        batch,
        "_optimizer_candidate_plan",
        lambda _target_date: (
            candidate_plan,
            {
                "status": "optimizer_candidate_plan_applied_offline_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
        ),
    )
    observed: list[tuple[str, str]] = []

    def fake_cohort(**kwargs):
        observed.append((kwargs["venue"], kwargs["candidate_prompt_version"]))
        return {
            "effective_venue": kwargs["venue"],
            "session_bucket": kwargs["session_bucket"],
            "status": "completed_offline_only",
            "candidate_prompt_version": kwargs["candidate_prompt_version"],
            "promotion_quality_gate_pass": False,
            "candidate_execution_selection": {
                "outcome_blind": True,
                "contract_pass": True,
            },
        }

    published = []
    monkeypatch.setattr(batch, "_cohort_result", fake_cohort)
    monkeypatch.setattr(
        batch,
        "publish_live_candidate",
        lambda **kwargs: published.append(kwargs),
    )

    report = batch.run_batch(
        target_date="2026-09-04",
        as_of=datetime(2026, 9, 4, 21, 5, tzinfo=quality.KST),
        max_new_requests=30,
        workers=2,
        timeout_sec=45.0,
        require_predecessor=False,
        predecessor_wait_sec=0,
        predecessor_interval_sec=1,
        write=True,
    )

    assert observed == [
        ("KRX", optimizer_candidate),
        ("NXT", batch.DEFAULT_CANDIDATE_PROMPT_VERSION),
    ]
    assert report["candidate_prompt_version"] == optimizer_candidate
    assert len(published) == 2
    assert published[1]["cohort"] == ("NXT", "NXT_AFTERMARKET")
    assert published[0]["candidate_prompt_version"] == optimizer_candidate
    assert published[0]["source_date"] == "2026-09-04"
    assert published[0]["write"] is True
    blocked_path = live_policy.live_candidate_path("2026-09-04")
    blocked = json.loads(blocked_path.read_text())
    assert blocked["status"] == "blocked"
    assert blocked["allowed_runtime_apply"] is False
    assert blocked["blocking_reasons"] == ["full_day_candidate_refresh_pending"]
    assert blocked["artifact_sha256"] == live_policy._canonical_sha256(
        {key: value for key, value in blocked.items() if key != "artifact_sha256"}
    )


def test_cohort_rejects_stale_candidate_execution_selection_policy(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(quality, "RUNTIME_DIR", tmp_path / "runtime")
    monkeypatch.setattr(
        quality,
        "DETAILED_PAIRED_REPORT_DIR",
        tmp_path / "detailed",
    )

    def fake_quality_cli(argv):
        venue = argv[argv.index("--venue") + 1]
        session = argv[argv.index("--session-bucket") + 1]
        mode = argv[argv.index("--mode") + 1]
        if mode == "control":
            quality._atomic_write_json(
                quality.control_path(
                    "2026-08-06",
                    effective_venue=venue,
                    session_bucket=session,
                ),
                {
                    "status": "control_manifest_frozen_collect_exact_samples",
                    "controls": [
                        {
                            "decision_stage": "entry",
                            "provider_actual": "openai",
                            "sample_count": 30,
                        }
                    ],
                },
            )
            return
        quality._atomic_write_json(
            quality.detailed_paired_path(
                "2026-08-06",
                candidate_prompt_version=(
                    batch.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
                ),
                effective_venue=venue,
                session_bucket=session,
            ),
            {
                "prepared_request_count": 30,
                "request_count": 30,
                "result_count": 30,
                "candidate_execution_performed": True,
                "provider_failed_count": 0,
                "candidate_provider_none_count": 0,
                "candidate_execution_selection": {
                    "policy": "deterministic_outcome_blind_symbol_round_robin_v1",
                    "outcome_blind": True,
                    "contract_pass": True,
                    "checkpoint_evaluated_setup_state_counts": {"READY": 30},
                },
            },
        )

    monkeypatch.setattr(batch, "_run_quality_cli", fake_quality_cli)

    try:
        batch._cohort_result(
            target_date="2026-08-06",
            as_of=datetime(2026, 8, 6, 21, 5, tzinfo=quality.KST),
            venue="KRX",
            session_bucket="KRX_REGULAR",
            max_new_requests=30,
            workers=2,
            timeout_sec=45.0,
        )
    except RuntimeError as exc:
        assert str(exc) == "candidate_execution_contract_failed:KRX:KRX_REGULAR"
    else:
        raise AssertionError("stale selection policy must fail closed")


def _empty_control_manifest():
    control = {
        "schema": quality.CONTROL_SCHEMA,
        "target_date": "2026-09-07",
        "status": "control_manifest_gap_fix_required",
        "controls": [],
        "conflicts": [],
        "supplemental_conflicts": [],
        "missing_natural_stages": ["entry", "entry_price", "holding", "overnight"],
        "excluded_counts": {"payload_hash_missing": 2},
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    control["control_manifest_sha256"] = quality._sha256(control)
    control["cohort_filter"] = {
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "runtime_effect": False,
    }
    return control


def test_empty_source_quality_control_is_terminal_without_provider_replay(
    monkeypatch, tmp_path
):
    control = _empty_control_manifest()
    path = tmp_path / "control.json"
    path.write_text(json.dumps(control))
    calls = []
    monkeypatch.setattr(batch, "_run_quality_cli", lambda args: calls.append(args))
    monkeypatch.setattr(quality, "control_path", lambda *a, **kw: path)
    result = batch._cohort_result(
        target_date="2026-09-07",
        as_of=datetime(2026, 9, 7, 22, 0, tzinfo=quality.KST),
        venue="KRX",
        session_bucket="KRX_REGULAR",
        max_new_requests=30,
        workers=2,
        timeout_sec=60,
    )
    assert len(calls) == 1 and calls[0][-1] == "control"
    assert result["status"] == "hold_no_exact_entry_control"
    assert (
        result["control_source_quality_status"] == "control_manifest_gap_fix_required"
    )
    assert result["provider_call_count"] == 0
    assert result["source_excluded_counts"] == {"payload_hash_missing": 2}


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_date", "2026-09-04"),
        ("status", "promotion_failed_no_control_reset"),
        ("controls", [{"decision_stage": "entry"}]),
        ("conflicts", ["signature_conflict"]),
        ("supplemental_conflicts", ["signature_conflict"]),
        ("excluded_counts", {}),
        ("excluded_counts", {"bad": True}),
        ("excluded_counts", {"bad": -1}),
        ("runtime_effect", True),
        ("allowed_runtime_apply", True),
        ("actual_order_submitted", True),
        ("broker_order_forbidden", False),
    ],
)
def test_empty_control_rejects_invalid_or_conflicting_manifest_even_with_valid_hash(
    field, value
):
    control = _empty_control_manifest()
    control[field] = value
    control["control_manifest_sha256"] = quality._sha256(
        {
            k: v
            for k, v in control.items()
            if k not in {"control_manifest_sha256", "cohort_filter"}
        }
    )
    assert (
        batch._verified_empty_control(
            control, target_date="2026-09-07", venue="KRX", session_bucket="KRX_REGULAR"
        )
        is False
    )


def test_empty_control_rejects_hash_and_cohort_mismatch():
    control = _empty_control_manifest()
    control["excluded_counts"]["payload_hash_missing"] = 3
    assert (
        batch._verified_empty_control(
            control, target_date="2026-09-07", venue="KRX", session_bucket="KRX_REGULAR"
        )
        is False
    )
    control = _empty_control_manifest()
    assert (
        batch._verified_empty_control(
            control,
            target_date="2026-09-07",
            venue="NXT",
            session_bucket="NXT_AFTERMARKET",
        )
        is False
    )
