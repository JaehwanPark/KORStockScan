import json
from pathlib import Path
from datetime import datetime
from functools import lru_cache

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import entry_setup_paired_replay_batch as batch
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer
from src.engine.scalping import compact_auxiliary_paired_replay as compact


def compact_row(day="2026-09-17", ordinal=0, verdict="VETO", net=0.5):
    from src.tests.test_strategy_owner_replay import entry_seed, entry_native_path
    from src.engine.scalping.strategy_owner_replay import replay_entry_opportunity
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    seed = entry_seed(day, ordinal)
    depths, trades = entry_native_path(seed)
    for d in depths[:30]:
        d.update(best_bid=9990, best_ask=10000, bid_levels=[[1,9990,1000]], ask_levels=[[1,10000,800]])
    for t in trades:
        t["trade_price"] = 10000
    replay = replay_entry_opportunity(seed, depths, trades, source_ready=True, evaluated_at=datetime.fromisoformat(seed["observed_at"]).timestamp()+181)
    return {"evaluation_key": f"compact-{day}-{ordinal}", "source_date": day,
            "evaluation_attempt_id": seed["evaluation_attempt_id"],
            "entry_economic_plan_sha256": seed["plan_sha256"],
            "scanner_promotion_id": seed["scanner_promotion_id"],
            "stock_code": seed["stock_code"], "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR", "broker_route": "KRX",
            "incumbent_prompt_version": policy.AI_VERSION,
            "incumbent_verdict": verdict, "input": {"entry_setup_evidence_v1": {}},
            "payload_sha256": "a"*64, "issued_prompt_sha256": "b"*64,
            "entry_quality_path": {"status": "evaluable", "first_hit": "net_target_first",
                                   "gross_net_target_pct": net+0.23,
                                   "conservative_execution_cost_pct": 0.23},
            "owner_replay": replay, "exclusion_reason": None}


def compact_result(row, verdict="PASS"):
    return compact.sealed({"candidate_response": {"risk_verdict": verdict},
                           "input_sha256": compact.input_identity(row), "validation_errors": [], "runtime_inference_cost_delta_krw": 0.0})


def test_compact_owner_replay_is_bound_to_exact_attempt_and_plan_hash():
    from copy import deepcopy

    row = compact_row()
    replay = row["owner_replay"]
    assert compact.owner_replay_valid(replay, row)

    wrong_plan = {**row, "entry_economic_plan_sha256": "f" * 64}
    assert not compact.owner_replay_valid(replay, wrong_plan)

    conflicting = deepcopy(replay)
    conflicting["blocker"] = "conflicting-generation"
    indexed, conflicts = compact.index_owner_replays([replay, conflicting])
    key = (row["evaluation_attempt_id"], row["entry_economic_plan_sha256"])
    assert indexed[key] == replay
    assert conflicts == {key}


def test_compact_whole_population_zero_same_verdict_and_unresolved_caution():
    rows = [compact_row(ordinal=i, verdict=v) for i,v in enumerate(["PASS", "VETO", "CAUTION"])]
    results = {r["evaluation_key"]: compact_result(r, "PASS" if i == 0 else "VETO") for i,r in enumerate(rows)}
    metrics = compact.evaluate(rows, results)
    assert metrics["paired_comparable_count"] == 2
    assert metrics["delta_net_ev_pct"] == 0
    assert metrics["exclusion_counts"] == {"caution_followup_terminal_missing": 1}
    assert metrics["denominator_preserved"]
    assert metrics["decision_changed_count"] == 0
    assert metrics["decision_unchanged_count"] == 2
    assert metrics["decision_change_rate"] == 0


def test_compact_no_notional_is_percentage_diagnostic_not_daily_profit():
    empty = compact.evaluate([], {})
    assert empty["portfolio_daily_net_delta_krw"] is None
    assert empty["net_profit_status"] == "not_available_without_owner_plan_and_portfolio_replay"
    row = compact_row()
    row["owner_replay"] = None
    metrics = compact.evaluate([row], {row["evaluation_key"]: compact_result(row)})
    assert metrics["delta_net_ev_pct"] == 0.5
    assert metrics["portfolio_daily_net_delta_krw"] is None
    row["exclusion_reason"] = "exact_stop_distance_missing_or_invalid"
    metrics = compact.evaluate([row], {})
    assert metrics["delta_net_ev_pct"] is None
    assert metrics["paired_comparable_count"] == 0


def test_compact_checkpoint_reuse_economics_rejoin_and_source_block(monkeypatch, tmp_path):
    import src.engine.scalping.entry_setup_evidence as evidence
    row = operating_compact_row()
    model = full_compact_proof()["owner_execution_model_validation"]
    monkeypatch.setattr(compact, "runtime_inference_cost_receipt", lambda *_: full_compact_proof()["runtime_inference_cost_receipt"])
    projection = compact.sealed({"owner_execution_model_validation":model,"rows": [row], "screened_total": 1, "source_manifest_sha256": "d"*64,
                                  "source_tuning_allowed": True, "exclusion_counts": {}, **compact.AUTHORITY})
    monkeypatch.setattr(compact, "prepare", lambda *_: projection)
    monkeypatch.setattr(evidence, "entry_risk_adjudication_openai_schema", lambda *_: {})
    monkeypatch.setattr(evidence, "validate_entry_risk_adjudication", lambda *_args, **_kwargs: [])
    calls = []
    def runner(request):
        calls.append(request)
        return {"candidate_response": {"risk_verdict": "PASS"}}
    first = compact.run(data_root=tmp_path, day="2026-09-17", execute=True, runner=runner)
    second = compact.run(data_root=tmp_path, day="2026-09-17", execute=True, runner=runner)
    assert len(calls) == 1
    assert first == second
    assert first["metrics"]["delta_net_ev_pct"] > 0
    assert first["metrics"]["economic_research_status"] == "supported_cost_adjusted_comparison"
    assert first["metrics"]["promotion_primary_decision_metric"] == "robust_paired_delta_ev_lower_bound_pct"
    assert first["metrics"]["model_delta_ev_is_actual_profit"] is False
    assert len(first["evaluation_fingerprint"]) == 64
    assert first["evaluation_state"] in {"evaluated_hold", "waiting_model_or_sample"}
    assert not first["promotion_pass"]
    identity = compact.input_identity(row)
    row["entry_quality_path"]["gross_net_target_pct"] = 0.9
    assert compact.input_identity(row) == identity
    row["payload_sha256"] = "e"*64
    assert compact.input_identity(row) != identity
    blocked = tmp_path / "blocked"
    projection["source_tuning_allowed"] = False
    projection = compact.sealed(projection)
    report = compact.run(data_root=blocked, day="2026-09-17", execute=True, runner=lambda _: pytest.fail("blocked source cannot call provider"))
    assert report["status"] == "source_contract_blocked"
    assert report["evaluation_state"] == "blocked_source"


@lru_cache(maxsize=1)
def operating_test_context():
    from src.engine.scalping.strategy_owner_replay import ENTRY_OPERATING_SCHEMA, entry_operating_model_identity
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version
    snapshot = dict(rules={}, environment={}, implementation={})
    return dict(schema=ENTRY_OPERATING_SCHEMA,broker_route="KRX",policy_snapshot=snapshot,initial_policy_state={},
        exit_policy_version=snapshot_version(snapshot),model_implementation_sha256=entry_operating_model_identity(),
        budget_krw=120000.,cost_rate=.0023,cost_policy_version="trade_profit_net_realized_pnl:rate=0.0023",
        cost_provenance="frozen_loaded_trade_profit_configuration_not_broker_settlement",**compact.AUTHORITY)


def operating_compact_row(day="2026-09-17", ordinal=0):
    """Synthetic operating receipt tests consumer wiring, not real profitability."""
    from copy import deepcopy
    from src.engine.scalping import strategy_owner_replay as owner
    from src.engine.scalping.entry_split_order_plan import QUANTITY_LEG_FOUR_ARM_IDS, _canonical_sha256
    row = compact_row(day, ordinal)
    replay = row["owner_replay"]
    seed = replay["seed"]
    context = deepcopy(operating_test_context())
    context["frozen_at"] = seed["observed_at"]
    context["sha256"] = compact.digest({k: v for k, v in context.items() if k != "sha256"})
    seed["operating_contract"] = context
    seed["seed_sha256"] = compact.digest({k: v for k, v in seed.items() if k != "seed_sha256"})
    arm = dict(schema=owner.ENTRY_OPERATING_SCHEMA,status="completed_source_only",actual_fill_evidence=False,
        requested_qty=seed["total_qty"],modeled_filled_qty=seed["total_qty"],fill_participation_rate=1.,
        budget_krw=context["budget_krw"],net_pnl_krw=600.,stress_net_pnl_krw=480.,
        capital_krw_minutes=12000.,reserve_krw_minutes=1200.,
        net_return_pct=.5,stress_net_return_pct=.4,modeled_entry_at=seed["observed_at"],
        modeled_exit_at=replay["arms"][QUANTITY_LEG_FOUR_ARM_IDS[0]]["modeled_exit_at"],
        contract_sha256=context["sha256"],exit_policy_sha256=context["exit_policy_version"],
        cost_policy_version=context["cost_policy_version"],cost_provenance=context["cost_provenance"],
        terminal_evidence_sha256="9"*64,**compact.AUTHORITY)
    arm["sha256"] = _canonical_sha256(arm)
    replay["operating_arms"] = {QUANTITY_LEG_FOUR_ARM_IDS[0]:arm}
    replay["replay_sha256"] = compact.digest({k:v for k,v in replay.items() if k != "replay_sha256"})
    return row


@lru_cache(maxsize=1)
def _full_compact_proof():
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    rows = [operating_compact_row(day, i) for day in ["2026-09-14", "2026-09-16", "2026-09-17"] for i in range(20)]
    metrics = compact.evaluate(rows, {r["evaluation_key"]: compact_result(r) for r in rows})
    frozen = "2026-09-15T21:00:00+09:00"
    from src.engine.scalping import entry_split_order_plan as split
    from src.tests.test_entry_split_order_plan import _operating_economic_fixture
    scope = split._entry_operating_scope(rows[0]["owner_replay"]["seed"])
    _, actuals, _ = _operating_economic_fixture()
    for actual in actuals:
        actual["scope_sha256"] = scope
    inputs = split._entry_operating_input_rows([rows[0]["owner_replay"]])
    validation = split.evaluate_entry_split_operating_economics(inputs, actuals,
        {"2026-09-08":10,"2026-09-09":10},target_date="2026-09-17")
    model_scope = validation["model_scopes"][0]
    assert model_scope["validated"]
    from tempfile import mkdtemp
    from src.tests.test_micro_reversion_provider_budget import _write_pricing_artifact
    pricing_root = Path(mkdtemp(prefix="adq-reviewed-pricing-fixture-"))
    pricing_path = _write_pricing_artifact(pricing_root / "policy/micro_reversion",
        effective_to="2026-09-30", pricing_basis="operator_accounting_zero_cost",
        prices=[dict(provider="openai",model="gpt-5.4-nano",input_usd_per_million_tokens="0",output_usd_per_million_tokens="0")])
    pricing_path.rename(pricing_path.with_name("provider_pricing.json"))
    inference_receipt = compact.runtime_inference_cost_receipt(pricing_root, "2026-09-17")
    assert inference_receipt["status"] == "reviewed_operator_zero_cost"
    return compact.sealed({"schema": compact.SCHEMA, "target_date": "2026-09-17",
        "runtime_inference_cost_receipt": inference_receipt,
        "incumbent_prompt_version": policy.AI_VERSION,
        "candidate_prompt_version": policy.ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
        "source_manifest_sha256": "d"*64, "promotion_contract_sha256": compact.digest(compact.CONTRACT),
        "status": "comparison_complete", "candidate_frozen_at": frozen,
        # Synthetic validated scope exercises wiring; it is not actual economic evidence.
        "owner_execution_model_validation": {"contract_version": "entry_split_execution_model_validation_v1", "source_date": "2026-09-17", "status": "validated_scope", "allowed_runtime_apply": True, "validated_scopes": [model_scope]},
        "metrics": metrics, "candidate_improvement_proven": True, "selection_disposition": "candidate_selected",
        "chronological_validation": {"candidate_frozen_at": frozen, "learning_pairs": metrics["pairs"][:20],
                                     "holdout_pairs": metrics["pairs"][20:], "holdout_consumed": False}, **compact.AUTHORITY})


def full_compact_proof():
    from copy import deepcopy
    return deepcopy(_full_compact_proof())

def test_compact_signed_owner_cf_forward_holdout_positive_and_corruption():
    proof = full_compact_proof()
    kwargs = dict(incumbent=proof["incumbent_prompt_version"], selected=proof["candidate_prompt_version"], source_manifest_sha256="d"*64)
    assert compact.promotion_valid(proof, **kwargs)
    proof["chronological_validation"]["holdout_consumed"] = True
    assert not compact.promotion_valid(compact.sealed(proof), **kwargs)
    proof["chronological_validation"]["holdout_consumed"] = False
    proof["metrics"]["response_coverage"] = 0.9
    assert not compact.promotion_valid(compact.sealed(proof), **kwargs)


@pytest.mark.parametrize("promote", [False, True])
def test_compact_public_finalization_uses_direct_pair_policy_consumer(tmp_path, promote, monkeypatch):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    from src.engine.scalping.main_ai_prompt_consumer import verify_compact_handoff
    from src.tests.test_ai_action_outcome_calibration import _compact_router_case_table

    parent = initial(tmp_path)
    proof = full_compact_proof()
    if not promote:
        proof["chronological_validation"]["holdout_pairs"] = []
        proof["candidate_improvement_proven"] = False
        proof["promotion_pass"] = False
        proof["promotion_scopes"] = []
    else:
        proof["promotion_pass"] = True
        proof["promotion_scopes"] = ["KRX|KRX_REGULAR"]
    proof["evaluation_fingerprint"] = compact.digest(["direct", promote])
    proof["evaluation_state"] = "validated_edge" if promote else "evaluated_hold"
    proof["comparison_dependency_signatures"] = compact._comparison_signatures(
        compact.report_path(tmp_path, "2026-09-17").parent,
        "2026-09-17",
        proof["candidate_prompt_version"],
    )
    proof = compact.sealed(proof)
    compact.write(compact.report_path(tmp_path, "2026-09-17"), proof)
    receipt = _compact_router_case_table()["machine_ai_natural_source_receipt"]
    receipt["source_manifest"] = {"source_manifest_sha256": "d" * 64}
    receipt["source_manifest_sha256"] = "d" * 64
    receipt["compact_auxiliary_policy_measurement"] = {"measurement_allowed": True}
    compact.write(
        tmp_path
        / "report/observation_source_quality_audit"
        / "observation_source_quality_audit_2026-09-17.json",
        {"machine_ai_natural_source_consumption": receipt},
    )
    from src.engine.scalping import ai_decision_quality as quality
    from src.tests.test_ai_decision_quality import _trace, _payload, _pending

    monkeypatch.setattr(quality, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        quality,
        "control_path",
        lambda day: tmp_path / "runtime" / f"ai_decision_quality_control_{day}.json",
    )
    monkeypatch.setattr(
        quality,
        "label_report_path",
        lambda day: tmp_path
        / "report/ai_decision_outcome_labels"
        / f"ai_decision_outcome_labels_{day}.json",
    )
    label = {
        **_pending(),
        "label_status": "mature",
        "source_quality_status": "pass",
        "primary_cohort_eligible": True,
        "reason_codes": ["체결근거"],
        "horizon_metrics": {"10m": {"end_return_pct": 0.5}},
    }
    report = {
        "schema": quality.LABEL_REPORT_SCHEMA,
        "target_date": "2026-09-17",
        "outcome_as_of": "2026-09-17T21:00:00+09:00",
        "labels": [label],
        **quality.OFFLINE_CONTRACT,
    }
    generated = quality.build_daily_materialization_reports(
        target_date="2026-09-17",
        promotion={},
        traces=[_trace()],
        payloads=[_payload()],
        labels=[label],
        label_report=report,
        outcome_price_source="pipeline",
        outcome_price_source_requested="pipeline",
        price_source_provenance=[],
    )
    quality.write_source_label_materialization("2026-09-17", generated["reports"])
    proof = compact.sealed(
        {
            **proof,
            "source_label_report_sha256": compact.digest(
                compact.read(quality.label_report_path("2026-09-17"))
            ),
        }
    )
    compact.write(compact.report_path(tmp_path, "2026-09-17"), proof)
    checklist = tmp_path / "docs/checklists/2026-09-21-stage2-todo-checklist.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text(
        "# Next\n\n"
        "<!-- compact_auxiliary_handoff:start -->\n"
        "old compact copy\n"
        "<!-- scanner_lookup_attention_handoff_sha256:abc -->\n"
        "- Scanner lookup source preserved\n"
        "<!-- compact_auxiliary_handoff:end -->\n",
        encoding="utf-8",
    )

    result = compact.finalize(
        data_root=tmp_path, day="2026-09-17", publication_day="2026-09-18"
    )
    assert result["status"] == "compact_direct_policy_and_consumer_complete"
    assert result["effective_date"] == "2026-09-21"
    child = policy.load(data_root=tmp_path, target_date=result["effective_date"])
    assert child["machine_policy"] == parent["machine_policy"]
    assert child["source_artifact_sha256"] == proof["artifact_content_sha256"]
    assert child["compact_evaluation_fingerprint"] == proof["evaluation_fingerprint"]
    assert child["ai_policy"]["prompt_version"] == (
        proof["candidate_prompt_version"]
        if promote
        else parent["ai_policy"]["prompt_version"]
    )
    assert verify_compact_handoff(tmp_path, "2026-09-17")["status"] == "PASS"
    assert not list(
        (tmp_path / "report/main_ai_prompt_consumer").glob(
            "compact_summary_handoff_*.json"
        )
    )
    checklist_text = checklist.read_text(encoding="utf-8")
    assert "old compact copy" not in checklist_text
    assert "Scanner lookup source preserved" in checklist_text
    assert "compact_auxiliary_direct_sha256" in checklist_text
    label_path = quality.label_report_path("2026-09-17")
    original_labels = compact.read(label_path)
    compact.write(label_path, {**original_labels, "tampered": True})
    assert "compact_source_label_revision_stale" in verify_compact_handoff(
        tmp_path, "2026-09-17"
    )["issues"]
    compact.write(label_path, original_labels)
    consumer_path = Path(result["consumer_path"])
    consumer = compact.read(consumer_path)
    consumer["compact_auxiliary"]["policy_bundle_sha256"] = "f" * 64
    compact.write(consumer_path, compact.sealed(consumer))
    assert "compact_direct_consumer_invalid" in verify_compact_handoff(
        tmp_path, "2026-09-17"
    )["issues"]

def test_compact_json_string_semantics_and_repeated_input_envelopes(tmp_path):
    import hashlib
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION
    day = "2026-09-17"
    raw = {"entry_setup_evidence_v1": {}}
    original_sha = hashlib.sha256(json.dumps(raw, indent=2).encode()).hexdigest()
    semantic_sha = hashlib.sha256(_json_bytes(raw)).hexdigest()
    traces, payloads, labels = [], [], []
    for i in range(2):
        trace = {"decision_trace_id": f"req-{i}", "decision_stage": "entry_screen", "prompt_version": AI_VERSION,
                 "provider_called": True, "provider_actual": "openai", "model": "gpt-5.4-nano",
                 "entry_mechanistic_action": "ENTER_NOW", "semantic_validation_status": "pass",
                 "decision_quality_contract_status": "pass", "entry_ai_risk_verdict": "PASS",
                 "payload_sha256": original_sha, "prompt_sha256": f"prompt-{i}", "request_envelope_sha256": f"env-{i}"}
        traces.append(trace)
        payloads.append({k: trace[k] for k in ["payload_sha256", "prompt_sha256", "request_envelope_sha256"]} | {
            "input_format": "json_string", "redacted": False, "replay_exact": True,
            "sanitized_user_input": raw, "sanitized_user_input_sha256": semantic_sha})
        labels.append({"decision_trace_id": f"req-{i}", "horizon_metrics": {"10m": {"entry_quality_path": compact_row()["entry_quality_path"]}}})
    for folder, name, rows in [("ai_decision_trace", "ai_decision_trace", traces), ("ai_decision_payloads", "ai_decision_payloads", payloads)]:
        path = tmp_path / folder / f"{name}_{day}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("".join(json.dumps(r)+"\n" for r in rows))
    compact.write(tmp_path / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{day}.json", {"labels": labels})
    result = compact.prepare(tmp_path, day)
    assert result["screened_total"] == 2
    assert result["exclusion_counts"] == {}


def test_compact_recomputed_owner_economics_and_consumed_holdout(tmp_path):
    proof = full_compact_proof()
    kwargs = dict(incumbent=proof["incumbent_prompt_version"], selected=proof["candidate_prompt_version"], source_manifest_sha256="d"*64)
    assert compact.promotion_valid(proof, **kwargs)
    missing_model = dict(proof, owner_execution_model_validation={})
    assert not compact.promotion_valid(compact.sealed(missing_model), **kwargs)
    compact.consume_holdout(proof, tmp_path)
    compact.consume_holdout(proof, tmp_path)
    proof["chronological_validation"]["holdout_pairs"][0]["delta_net_pct"] += 1
    changed = compact.sealed(proof)
    assert not compact.promotion_valid(changed, **kwargs)
    with pytest.raises(ValueError, match="already_consumed"):
        compact.consume_holdout(changed, tmp_path)
    proof = full_compact_proof()
    proof["chronological_validation"]["holdout_pairs"][0]["runtime_inference_cost_delta_krw"] = None
    assert not compact.promotion_valid(compact.sealed(proof), **kwargs)


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
                candidate_prompt_version=(batch.DEFAULT_CANDIDATE_PROMPT_VERSION),
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
                candidate_prompt_version=(batch.DEFAULT_CANDIDATE_PROMPT_VERSION),
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


def test_zero_trace_control_is_terminal_without_repeating_same_source(
    monkeypatch, tmp_path
):
    control = _empty_control_manifest()
    control["excluded_counts"] = {}
    control["input_trace_count"] = 0
    control["input_trace_census_status"] = "empty"
    control["input_trace_source"] = {
        "path": "/tmp/ai_decision_trace_2026-09-07.jsonl",
        "exists": True,
        "size_bytes": 1024,
    }
    control["control_manifest_sha256"] = quality._sha256(
        {
            key: value
            for key, value in control.items()
            if key not in {"control_manifest_sha256", "cohort_filter"}
        }
    )
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
    assert result["source_trace_count"] == 0
    assert result["source_trace_census_status"] == "empty"
    assert result["source_trace_artifact"]["exists"] is True
    assert result["provider_call_count"] == 0


@pytest.mark.parametrize(
    "source_proof",
    [
        None,
        {"path": "/tmp/missing.jsonl", "exists": False, "size_bytes": 0},
        {"path": "/tmp/empty.jsonl", "exists": True, "size_bytes": 0},
    ],
)
def test_zero_trace_control_rejects_missing_or_empty_source_artifact(source_proof):
    control = _empty_control_manifest()
    control["excluded_counts"] = {}
    control["input_trace_count"] = 0
    control["input_trace_census_status"] = "empty"
    if source_proof is not None:
        control["input_trace_source"] = source_proof
    control["control_manifest_sha256"] = quality._sha256(
        {
            key: value
            for key, value in control.items()
            if key not in {"control_manifest_sha256", "cohort_filter"}
        }
    )

    assert not batch._verified_empty_control(
        control,
        target_date="2026-09-07",
        venue="KRX",
        session_bucket="KRX_REGULAR",
    )


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


@pytest.mark.parametrize("defect", ["legacy_only", "wrong_scope", "late_model", "unsealed_model", "operating_net_corrupt", "missing_scope", "bad_model_date"])
def test_compact_reused_model_requires_operating_outcome_and_prior_exact_scope(defect):
    proof = full_compact_proof()
    pair = proof["chronological_validation"]["learning_pairs"][0]
    model = proof["owner_execution_model_validation"]["validated_scopes"][0]
    if defect == "missing_scope":
        proof["owner_execution_model_validation"]["validated_scopes"] = []
    elif defect == "bad_model_date":
        model["available_after_date"] = None
        model["sha256"] = compact.digest({k:v for k,v in model.items() if k != "sha256"})
    elif defect == "legacy_only":
        pair["owner_replay"].pop("operating_arms")
        pair["owner_replay"]["replay_sha256"] = compact.digest({k:v for k,v in pair["owner_replay"].items() if k != "replay_sha256"})
    elif defect == "wrong_scope":
        model["scope_sha256"] = "0" * 64
    elif defect == "late_model":
        model["available_after_date"] = pair["source_date"]
        model["sha256"] = compact.digest({k:v for k,v in model.items() if k != "sha256"})
    elif defect == "unsealed_model":
        model["sha256"] = "0" * 64
    else:
        from src.engine.scalping.entry_split_order_plan import QUANTITY_LEG_FOUR_ARM_IDS
        pair["owner_replay"]["operating_arms"][QUANTITY_LEG_FOUR_ARM_IDS[0]]["net_pnl_krw"] += 1
    assert not compact.promotion_valid(compact.sealed(proof),incumbent=proof["incumbent_prompt_version"],selected=proof["candidate_prompt_version"],source_manifest_sha256="d"*64)


def test_compact_operating_money_and_stress_do_not_use_legacy_research_arm():
    row = operating_compact_row()
    result = compact.evaluate([row], {row["evaluation_key"]:compact_result(row)})
    assert result["delta_net_ev_pct"] == .5
    assert result["portfolio_daily_net_delta_krw"] == {"2026-09-17":600.}
    assert result["pairs"][0]["stress_delta_net_pct"] == .4
    legacy = compact_row()
    diagnostic = compact.evaluate([legacy], {legacy["evaluation_key"]:compact_result(legacy)})
    assert diagnostic["portfolio_daily_net_delta_krw"] is None


def test_compact_large_atomic_operating_generation_is_consumable(tmp_path):
    path = tmp_path / "operating.json"
    generation = {"frozen_inputs": "x" * (17 * 1024 * 1024)}
    compact.write(path, generation)
    assert compact.read(path) == generation


def test_additive_label_revision_reuses_frozen_projection_without_raw_rescan(monkeypatch, tmp_path):
    row = compact_row()
    projection = compact.sealed({"rows": [row], "screened_total": 1,
        "source_manifest_sha256": "d"*64, "source_tuning_allowed": True, "exclusion_counts": {}, **compact.AUTHORITY})
    monkeypatch.setattr(compact, "prepare", lambda *_: projection)
    compact.run(data_root=tmp_path, day="2026-09-17", execute=False)
    path = tmp_path / "report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-09-17.json"
    report = {"target_date": "2026-09-17", "labels": [{"decision_trace_id": row["evaluation_key"],
        "horizon_metrics": {"10m": {"entry_quality_path": row["entry_quality_path"]}},
        "evaluation_label_contract": {"diagnostic": "additive_revision"}}]}
    # Other label cohorts must not invalidate this frozen compact population.
    report["labels"].extend([{"decision_trace_id": "unrelated"}] * 2)
    compact.write(path, report)
    monkeypatch.setattr(compact, "prepare", lambda *_: pytest.fail("additive revision cannot rescan frozen raw"))
    refreshed = compact.run(data_root=tmp_path, day="2026-09-17", execute=False)
    assert refreshed["source_label_report_sha256"] == compact.digest(compact.read(path))
    assert refreshed["metrics"]["screened_total"] == 1
    # A real path revision must reach the original source producer.
    report["labels"][0]["horizon_metrics"]["10m"]["entry_quality_path"]["gross_net_target_pct"] = .8
    compact.write(path, report)
    calls = []
    monkeypatch.setattr(compact, "prepare", lambda *_: calls.append(True) or projection)
    compact.run(data_root=tmp_path, day="2026-09-17", execute=False)
    assert calls == [True]


@pytest.mark.parametrize("revision", ["identity_changed", "label_removed", "duplicate_identity"])
def test_label_admission_revision_requires_evaluation_before_publication(monkeypatch, tmp_path, revision):
    row = compact_row()
    projection = compact.sealed(dict(rows=[row], screened_total=1,
        source_manifest_sha256="d" * 64, source_tuning_allowed=True,
        exclusion_counts={}, **compact.AUTHORITY))
    label = {"decision_trace_id": row["evaluation_key"],
        "horizon_metrics": {"10m": {"entry_quality_path": row["entry_quality_path"]}}}
    label_path = tmp_path / "report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-09-17.json"
    labels = {"target_date": "2026-09-17", "labels": [label]}
    compact.write(label_path, labels)
    monkeypatch.setattr(compact, "prepare", lambda *_: projection)
    compact.run(data_root=tmp_path, day="2026-09-17", execute=False)
    if revision == "identity_changed":
        label["primary_cohort_exclusion_reasons"] = ["canonical_context_venue_session_mismatch"]
    elif revision == "label_removed":
        labels["labels"] = []
    else:
        labels["labels"].append(dict(label))
    compact.write(label_path, labels)
    monkeypatch.setattr(compact, "prepare", lambda *_: pytest.fail("finalization must not rescan raw"))
    with pytest.raises(ValueError, match="compact_finalize_requires_evaluation_of_changed_source"):
        compact.run(data_root=tmp_path, day="2026-09-17", execute=False, allow_source_rebuild=False)
    # Reproduce an old writer masking the revision with current stat/hash.
    source_path = compact.report_path(tmp_path, "2026-09-17").with_suffix(".source.json")
    source = compact.read(source_path)
    source["dependency_signatures"] = compact.source_dependency_signatures(tmp_path, "2026-09-17")
    source["source_label_report_sha256"] = compact.digest(compact.read(label_path))
    compact.write(source_path, compact.sealed(source))
    with pytest.raises(ValueError, match="compact_finalize_requires_evaluation_of_changed_source"):
        compact.run(data_root=tmp_path, day="2026-09-17", execute=False, allow_source_rebuild=False)
    calls = []
    monkeypatch.setattr(compact, "prepare", lambda *_: calls.append(True) or projection)
    compact.run(data_root=tmp_path, day="2026-09-17", execute=False)
    assert calls == [True]


def test_operating_comparison_error_envelope_exposure_and_capital_conflict():
    from copy import deepcopy
    from src.engine.scalping import entry_split_order_plan as split
    proof = full_compact_proof()
    pairs = proof['chronological_validation']['holdout_pairs']
    model = proof['owner_execution_model_validation']
    good = compact.operating_comparison_metrics(pairs, model)
    assert good['status'] == 'supported_operating_comparison'
    assert good['robust_paired_delta_ev_lower_bound_pct'] > 0
    assert good['candidate']['net_pnl_krw'] > good['incumbent']['net_pnl_krw']
    assert good['candidate']['capital_krw_minutes'] > 0
    assert good['candidate']['reserve_krw_minutes'] > 0
    inflated = deepcopy(model)
    scope = inflated['validated_scopes'][0]
    for r in scope['calibration_rows'] + scope['holdout_rows']:
        r['net_error_budget_pct'] = 1.
    scope['tolerance']['net_error_budget_pct'] = 1.
    scope['optimistic_net_error_budget_pct'] = 1.
    scope['actual_rows_sha256'] = split._canonical_sha256(scope['calibration_rows'] + scope['holdout_rows'])
    scope['sha256'] = split._canonical_sha256({k:v for k,v in scope.items() if k != 'sha256'})
    rejected = compact.operating_comparison_metrics(pairs, inflated)
    assert rejected['status'] == 'supported_operating_comparison'
    assert rejected['robust_paired_delta_ev_lower_bound_pct'] < 0
    proof['owner_execution_model_validation'] = inflated
    kwargs = dict(incumbent=proof['incumbent_prompt_version'], selected=proof['candidate_prompt_version'], source_manifest_sha256='d'*64)
    assert not compact.promotion_valid(compact.sealed(proof), **kwargs)
    # Signed but incomplete exposure is a source gap, not zero occupancy.
    damaged = deepcopy(pairs[:1])
    replay = damaged[0]['owner_replay']
    arm = next(iter(replay['operating_arms'].values()))
    arm.pop('reserve_krw_minutes')
    arm['sha256'] = split._canonical_sha256({k:v for k,v in arm.items() if k != 'sha256'})
    replay['replay_sha256'] = compact.digest({k:v for k,v in replay.items() if k != 'replay_sha256'})
    assert compact.operating_comparison_metrics(damaged, model)['robust_paired_delta_ev_lower_bound_pct'] is None
    overlapping = deepcopy(pairs[:1]) * 2
    assert compact.operating_comparison_metrics(overlapping, model)['blocker'] == 'overlapping_owner_capital_allocation_unsupported'


def test_source_contract_code_upgrade_preserves_exclusions_without_raw_rescan(monkeypatch, tmp_path):
    day='2026-09-17'
    row=compact_row()
    row.update(input=None, owner_replay=None, exclusion_reason='exact_stop_distance_missing')
    row.pop("entry_economic_plan_sha256")
    projection=compact.sealed(dict(rows=[row],screened_total=1,source_manifest_sha256='d'*64,
        source_tuning_allowed=True, exclusion_counts={'exact_stop_distance_missing':1}, **compact.AUTHORITY))
    monkeypatch.setattr(compact,'prepare',lambda *_: projection)
    compact.run(data_root=tmp_path,day=day,execute=False)
    path=compact.report_path(tmp_path,day).with_suffix('.source.json')
    old=compact.read(path)
    old.pop('source_projection_contract')
    old['projection_contract_sha256']='e'*64
    compact.write(path,compact.sealed(old))
    monkeypatch.setattr(compact,'prepare',lambda *_: pytest.fail('code upgrade must not rescan frozen raw'))
    result=compact.run(data_root=tmp_path,day=day,execute=False)
    source=compact.read(path)
    assert source['source_upgrade']['raw_not_read'] is True
    assert source['rows'][0]['input'] is None
    assert source['rows'][0]['exclusion_reason']=='exact_stop_distance_missing'
    assert result['metrics']['delta_net_ev_pct'] is None
    assert result['provider_calls_this_run']==0


def test_source_contract_upgrade_reclassifies_historical_response_failure_without_raw_rescan(monkeypatch, tmp_path):
    day = "2026-09-17"
    row = compact_row()
    row.update(input=None, owner_replay=None, exclusion_reason="natural_contract_invalid",
        natural_contract_evidence={"model": "gpt-5.4-nano", "provider_actual": "openai",
            "semantic_validation_status": "not_evaluated_transport",
            "decision_quality_contract_status": "not_evaluated_transport",
            "result_source": "transport_error"})
    projection = compact.sealed(dict(rows=[row], screened_total=1,
        source_manifest_sha256="d"*64, source_tuning_allowed=True,
        exclusion_counts={"natural_contract_invalid": 1}, **compact.AUTHORITY))
    monkeypatch.setattr(compact, "prepare", lambda *_: projection)
    compact.run(data_root=tmp_path, day=day, execute=False)
    path = compact.report_path(tmp_path, day).with_suffix(".source.json")
    old = compact.read(path)
    old["source_projection_contract"] = "compact_pre_ai_execution_source_v5"
    old["projection_contract_sha256"] = "e"*64
    old["rows"][0]["exclusion_reason"] = "natural_response_semantic_invalid"
    compact.write(path, compact.sealed(old))
    monkeypatch.setattr(compact, "prepare", lambda *_: pytest.fail("upgrade must use frozen evidence"))
    report = compact.run(data_root=tmp_path, day=day, execute=False)
    upgraded = compact.read(path)
    assert upgraded["source_upgrade"]["raw_not_read"] is True
    assert upgraded["rows"][0]["exclusion_reason"] == "natural_response_transport_invalid"
    assert report["candidate_zero_disposition"]["primary_input_disposition_counts"] == {"source_gap": 1}


def test_compact_primary_source_gap_does_not_spend_provider_budget(monkeypatch,tmp_path):
    row=compact_row()
    projection=compact.sealed(dict(rows=[row],screened_total=1,source_manifest_sha256='d'*64,
        source_tuning_allowed=True,exclusion_counts={},**compact.AUTHORITY))
    monkeypatch.setattr(compact,'prepare',lambda *_:projection)
    result=compact.run(data_root=tmp_path,day='2026-09-17',execute=True,
        runner=lambda _:pytest.fail('diagnostic-only rows must not call the provider'))
    assert result['provider_calls_this_run']==0
    assert result['candidate_zero_disposition']['status']=='source_gap'
    assert result['metrics']['delta_net_ev_pct'] is None


def test_actual_decision_version_performance_reuses_completed_cost_owner():
    receipt=dict(evaluation_attempt_id='attempt',machine_bundle_sha256='a'*64,
        machine_policy_version='machine-v1',compact_prompt_version='compact-v1',decision_trace_id='trace',runtime_pid=123)
    receipt['sha256']=compact.digest(receipt)
    row=dict(episode_id='natural-episode',status='COMPLETED',origin='real',owner='main_scalping',
        exact_lineage=True,cost_complete=True,entry_decision_pid_consumed=True,entry_decision_version_receipt=receipt,
        scope_sha256='b'*64,fill_class='full',completion_date='2026-09-17',net_pnl_krw=200.,profit_rate=.2,
        budget_krw=100000.,capital_krw_minutes=100.,reserve_krw_minutes=10.,net_error_budget_pct=.01)
    report={'operating_economic_state':{'model_rows':[row,row,{**row,'episode_id':'simulation','origin':'sim'}]}}
    value=compact.applied_decision_version_performance(report,day='2026-09-17')
    assert value['groups'][0]['cumulative']['completed_episodes']==1
    assert value['groups'][0]['rolling']['net_pnl_krw']==200.
    assert value['groups'][0]['policy_version']=='machine-v1|compact-v1'
    assert value['causal_profit_improvement'] is None
    report['operating_economic_state']['model_rows'].append({**row,'net_pnl_krw':999.})
    assert not compact.applied_decision_version_performance(report,day='2026-09-17')['groups']


def test_supported_operating_owner_cannot_override_source_label_venue_conflict():
    row=operating_compact_row()
    row['source_label_identity_reasons']=['canonical_context_venue_session_mismatch']
    blocker=compact.primary_input_blocker(row,full_compact_proof()['owner_execution_model_validation'])
    assert blocker==('source_gap','source_label_identity_contract_invalid:canonical_context_venue_session_mismatch')


@pytest.mark.parametrize("venue,session,route", [
    ("KRX", "KRX_REGULAR", "SOR"),
    ("NXT", "NXT_PREMARKET", "SOR"),
    ("KRX_NXT_INTEGRATED", "KRX_NXT_AFTERMARKET", "SOR"),
    ("NXT", "NXT_REGULAR_OVERLAP", "SOR"),
    ("NXT", "NXT_AFTERMARKET", "SOR"),
])
def test_registered_sor_scope_independent_promotion_and_dated_consumer(tmp_path, venue, session, route):
    from copy import deepcopy
    from datetime import datetime
    from src.engine.scalping import entry_split_order_plan as split, mechanistic_entry_runtime_policy as policy
    from src.tests.test_mechanistic_entry_runtime_policy import source
    parent = policy.publish(source(tmp_path), data_root=tmp_path, bootstrap=True,
        adopt_all_continuous=True, now=datetime(2026,9,13,20,tzinfo=policy.KST))
    proof = full_compact_proof()
    scope = (venue, session)
    for pair in proof['chronological_validation']['learning_pairs'] + proof['chronological_validation']['holdout_pairs']:
        pair.update(effective_venue=venue, session_bucket=session, broker_route=route)
        owner=pair['owner_replay']; seed=owner['seed']
        seed.update(effective_venue=venue,session_bucket=session)
        context=seed['operating_contract'];context['broker_route']=route
        context['sha256']=compact.digest({k:v for k,v in context.items() if k!='sha256'})
        seed['seed_sha256']=compact.digest({k:v for k,v in seed.items() if k!='seed_sha256'})
        for arm in owner['operating_arms'].values():
            arm['contract_sha256']=context['sha256']
            arm['sha256']=split._canonical_sha256({k:v for k,v in arm.items() if k!='sha256'})
        owner['replay_sha256']=compact.digest({k:v for k,v in owner.items() if k!='replay_sha256'})
    exact_scope=split._entry_operating_scope(proof['chronological_validation']['learning_pairs'][0]['owner_replay']['seed'])
    model=proof['owner_execution_model_validation']['validated_scopes'][0]
    model['scope_sha256']=exact_scope
    for key in ('calibration_rows','holdout_rows'):
        for row in model[key]:row['scope_sha256']=exact_scope
    model['actual_rows_sha256']=split._canonical_sha256(model['calibration_rows']+model['holdout_rows'])
    model['sha256']=split._canonical_sha256({k:v for k,v in model.items() if k!='sha256'})
    # An unrelated scope may be pending or have a different incumbent. Neither
    # can remove this scope's complete population or authorize the other scope.
    coverage = proof['metrics']['scope_coverage']['KRX|KRX_REGULAR']
    proof['metrics']['response_coverage'] = .5
    original_incumbent = proof['incumbent_prompt_version']
    scope_key = '|'.join(scope)
    proof['scope_validation'] = {scope_key: {
        'incumbent_prompt_version': original_incumbent,
        'candidate_frozen_at': proof['candidate_frozen_at'],
        'coverage': coverage,
        'chronological_validation': deepcopy(proof['chronological_validation']),
    }}
    proof['incumbent_prompt_version'] = None
    proof=compact.sealed(proof)
    kwargs=dict(incumbent=original_incumbent,selected=proof['candidate_prompt_version'],source_manifest_sha256='d'*64)
    assert compact.promotion_valid(proof,scope=scope,**kwargs)
    assert compact.primary_input_blocker(proof['chronological_validation']['learning_pairs'][0],proof['owner_execution_model_validation']) is None
    assert not compact.promotion_valid(proof,scope=('NXT','NXT_REGULAR'),**kwargs)
    # Existing public dated publisher receives the validated economic proof.
    from src.tests.test_ai_action_outcome_calibration import _compact_router_case_table
    receipt=deepcopy(_compact_router_case_table()['machine_ai_natural_source_receipt'])
    receipt['source_manifest_sha256']='d'*64
    receipt['compact_auxiliary_policy_measurement']={'measurement_allowed':True}
    table={'compact_auxiliary_screen_outcomes':{'paired_economic_evaluation':proof},
           'machine_ai_natural_source_receipt':receipt}
    report=compact.sealed({'report_scope':'compact_auxiliary_only','target_date':'2026-09-18',
        'evaluation_source_date':'2026-09-17','hierarchical_entry_quality':{'machine_decision_case_table':table}})
    successor=policy._publish_compact_scope(report,data_root=tmp_path,current=datetime(2026,9,18,21,tzinfo=policy.KST))
    assert successor['compact_promoted_scopes']==['|'.join(scope)]
    loaded=policy.load_effective(data_root=tmp_path,target_date='2026-09-21')
    assert policy.for_cohort(loaded,scope)['ai_policy']['prompt_version']==proof['candidate_prompt_version']
    for parent_scope_key,value in parent['scope_policies'].items():
        if parent_scope_key!='|'.join(scope):
            assert loaded['scope_policies'][parent_scope_key]['ai_policy']['prompt_version']==value['ai_policy']['prompt_version']
    # No route pooling may manufacture a passing learning/holdout population.
    short=deepcopy(proof)
    short['scope_validation'][scope_key]['chronological_validation']['holdout_pairs']=short['scope_validation'][scope_key]['chronological_validation']['holdout_pairs'][:19]
    assert not compact.promotion_valid(compact.sealed(short),scope=scope,**kwargs)
    missing = deepcopy(proof)
    missing['scope_validation'][scope_key]['coverage']['response_coverage'] = .95
    assert not compact.promotion_valid(compact.sealed(missing),scope=scope,**kwargs)


def test_later_scope_freezes_without_moving_earlier_holdout_or_pooling_routes():
    from copy import deepcopy
    from datetime import datetime
    earlier = full_compact_proof()['chronological_validation']['learning_pairs']
    incumbent = earlier[0]['incumbent_prompt_version']
    candidate = full_compact_proof()['candidate_prompt_version']
    later = deepcopy(earlier)
    for pair in later:
        pair.update(effective_venue='NXT', session_bucket='NXT_PREMARKET', broker_route='SOR')
    rows = [earlier[0], later[0]]
    metrics = {'scope_coverage': {}}
    first, frozen = compact.scope_candidate_validation(earlier + later[:1], rows, metrics, {},
        candidate=candidate, now=datetime(2026,9,15,21,tzinfo=compact.KST))
    assert first['KRX|KRX_REGULAR']['candidate_frozen_at'].startswith('2026-09-15')
    assert first['NXT|NXT_PREMARKET']['candidate_frozen_at'] is None
    for pair in later[1:]:
        pair['source_date'] = '2026-09-16'
    second, successor = compact.scope_candidate_validation(earlier + later, rows, metrics,
        {'scope_candidates': frozen}, candidate=candidate, now=datetime(2026,9,17,21,tzinfo=compact.KST))
    assert successor['KRX|KRX_REGULAR'] == frozen['KRX|KRX_REGULAR']
    assert second['NXT|NXT_PREMARKET']['candidate_frozen_at'].startswith('2026-09-17')
    assert len(second['NXT|NXT_PREMARKET']['chronological_validation']['learning_pairs']) == 20
    assert not second['NXT|NXT_PREMARKET']['chronological_validation']['holdout_pairs']
    # A newly observed direct route still needs its own 20 learning episodes.
    direct = deepcopy(later[:19])
    for pair in direct:
        pair['broker_route'] = 'NXT'
    waiting, _ = compact.scope_candidate_validation(earlier + later + direct, rows, metrics,
        {'scope_candidates': frozen}, candidate=candidate, now=datetime(2026,9,17,21,tzinfo=compact.KST))
    assert waiting['NXT|NXT_PREMARKET']['candidate_frozen_at'] is None


@pytest.mark.parametrize('verdict,selected_scopes,status', [
    ('PASS', ['KRX|KRX_REGULAR'], 'candidate_selected'), ('VETO', [], 'valid_no_edge')])
def test_public_compact_run_preserves_prior_unanswered_holdout_and_recovers(monkeypatch, tmp_path, verdict, selected_scopes, status):
    from datetime import datetime
    from src.engine.scalping import entry_setup_evidence as evidence
    proof = full_compact_proof()
    monkeypatch.setattr(compact, 'runtime_inference_cost_receipt', lambda *_: proof['runtime_inference_cost_receipt'])
    monkeypatch.setattr(evidence, 'entry_risk_adjudication_openai_schema', lambda *_: {})
    monkeypatch.setattr(evidence, 'validate_entry_risk_adjudication', lambda *_args, **_kwargs: [])
    class Clock(datetime):
        day = '2026-09-15'
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(cls.day + 'T21:00:00+09:00')
    monkeypatch.setattr(compact, 'datetime', Clock)
    def prepare(_root, day):
        model = {**proof['owner_execution_model_validation'], 'source_date': day}
        return compact.sealed({'owner_execution_model_validation': model,
            'rows': [operating_compact_row(day, i) for i in range(20)], 'screened_total': 20,
            'source_manifest_sha256': 'd'*64, 'source_tuning_allowed': True,
            'exclusion_counts': {}, **compact.AUTHORITY})
    monkeypatch.setattr(compact, 'prepare', prepare)
    runner = lambda _: {'candidate_response': {'risk_verdict': verdict}}
    learning = compact.run(data_root=tmp_path, day='2026-09-14', execute=True, runner=runner)
    assert learning['scope_validation']['KRX|KRX_REGULAR']['candidate_frozen_at'].startswith('2026-09-15')
    Clock.day = '2026-09-16'
    partial = compact.run(data_root=tmp_path, day='2026-09-16', execute=True, max_new=19, runner=runner)
    assert partial['metrics']['paired_comparable_count'] == 19
    Clock.day = '2026-09-17'
    held = compact.run(data_root=tmp_path, day='2026-09-17', execute=True, runner=runner)
    assert held['metrics']['response_coverage'] == 1.
    scope = held['scope_validation']['KRX|KRX_REGULAR']
    assert scope['coverage']['economic_eligible_count'] == 60
    assert scope['coverage']['paired_comparable_count'] == 59
    assert not held['promotion_pass']
    assert held['candidate_zero_disposition']['scope_dispositions']['KRX|KRX_REGULAR']['status'] == 'pending'
    # The resumable producer may repair the actual missing response. No
    # complete response is reissued and no missing economics becomes zero.
    compact.run(data_root=tmp_path, day='2026-09-16', execute=True, runner=runner)
    recovered = compact.run(data_root=tmp_path, day='2026-09-17', execute=True, runner=runner)
    assert recovered['scope_validation']['KRX|KRX_REGULAR']['coverage']['response_coverage'] == 1.
    assert recovered['promotion_scopes'] == selected_scopes
    assert recovered['candidate_zero_disposition']['scope_dispositions']['KRX|KRX_REGULAR']['status'] == status


@pytest.mark.parametrize('venue,session,route', [
    ('KRX','KRX_REGULAR','UNKNOWN'),('KRX','KRX_REGULAR','NXT'),
    ('NXT','NXT_PREMARKET','KRX'),('NXT','UNREGISTERED','SOR')])
def test_operating_market_route_contract_rejects_real_mismatch(venue,session,route):
    from src.engine.scalping.strategy_owner_replay import entry_operating_route_supported
    assert not entry_operating_route_supported(venue,session,route)


@pytest.mark.parametrize("reason", [
    "natural_contract_invalid",
    "natural_response_transport_invalid",
    "natural_response_semantic_invalid",
    "natural_provider_or_model_contract_invalid",
])
def test_natural_response_failures_are_source_gaps_not_market_scope(reason):
    row = compact_row()
    row["exclusion_reason"] = reason
    disposition, blocker = compact.primary_input_blocker(row, {})
    assert (disposition, blocker) == ("source_gap", reason)
    accountability = compact.blocker_accountability(disposition, blocker)
    assert accountability["owner"] == "ai_decision_trace_and_quality_response_contract"


@pytest.mark.parametrize("patch,expected", [
    ({"semantic_validation_status": "not_evaluated_transport", "result_source": "timeout"},
     "natural_response_transport_invalid"),
    ({"semantic_validation_status": None, "result_source": "timeout",
      "decision_quality_contract_status": "not_evaluated_transport"},
     "natural_response_transport_invalid"),
    ({"semantic_validation_status": "semantic_rejected"},
     "natural_response_semantic_invalid"),
    ({"decision_quality_contract_status": "fail"},
     "natural_response_semantic_invalid"),
    ({"provider_actual": "other"},
     "natural_provider_or_model_contract_invalid"),
])
def test_natural_response_contract_preserves_first_failure_boundary(patch, expected):
    trace = {"model": "gpt-5.4-nano", "provider_actual": "openai",
             "semantic_validation_status": "pass",
             "decision_quality_contract_status": "pass", **patch}
    assert compact.natural_response_contract_exclusion(trace) == expected


def test_calibration_cli_has_no_compact_postclose_phase():
    from src.engine.scalping import ai_action_outcome_calibration as calibration

    with pytest.raises(SystemExit):
        calibration.main(
            ["--target-date", "2026-09-17", "--postclose-phase", "evaluate"]
        )


@pytest.mark.parametrize("changed_contract", ["prompt", "schema", "pricing"])
def test_compact_reuse_binds_current_candidate_and_pricing(monkeypatch, tmp_path, changed_contract):
    from src.engine.scalping import entry_setup_evidence as evidence
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    proof = full_compact_proof()
    row = operating_compact_row()
    projection = compact.sealed(dict(rows=[row], screened_total=1, exclusion_counts={},
        source_manifest_sha256="d"*64, source_tuning_allowed=True,
        owner_execution_model_validation=proof["owner_execution_model_validation"], **compact.AUTHORITY))
    monkeypatch.setattr(compact, "prepare", lambda *_: projection)
    monkeypatch.setattr(compact, "runtime_inference_cost_receipt", lambda *_: proof["runtime_inference_cost_receipt"])
    monkeypatch.setattr(evidence, "entry_risk_adjudication_openai_schema", lambda *_: {})
    monkeypatch.setattr(evidence, "validate_entry_risk_adjudication", lambda *a, **k: [])
    calls = []
    def runner(request):
        calls.append(request)
        return {"candidate_response": {"risk_verdict": "PASS"}}
    first = compact.run(data_root=tmp_path, day="2026-09-17", execute=True, runner=runner)
    assert first["metrics"]["paired_comparable_count"] == 1
    if changed_contract == "prompt":
        original = policy.compact_auxiliary_prompt
        monkeypatch.setattr(policy, "compact_auxiliary_prompt", lambda **k: original(**k) + "\nReviewed revision.")
    elif changed_contract == "schema":
        monkeypatch.setattr(evidence, "entry_risk_adjudication_openai_schema", lambda *_: {"changed": True})
    else:
        monkeypatch.setattr(compact, "runtime_inference_cost_receipt", lambda *_: dict(status="source_gap", delta_krw=None, blocker="pricing_missing"))
    refreshed = compact.run(data_root=tmp_path, day="2026-09-17", execute=False, runner=runner)
    assert len(calls) == 1
    assert refreshed["metrics"]["paired_comparable_count"] == 0
    assert refreshed["metrics"]["delta_net_ev_pct"] is None
    if changed_contract != "pricing":
        compact.run(data_root=tmp_path, day="2026-09-17", execute=True, runner=runner)
        assert len(calls) == 2


def test_compact_shared_data_mount_reuses_snapshot_and_finalization_never_rescans(monkeypatch, tmp_path):
    from src.engine.scalping import entry_setup_evidence as evidence
    root = tmp_path / "actual"
    root.mkdir()
    alias = tmp_path / "release_data"
    alias.symlink_to(root, target_is_directory=True)
    proof = full_compact_proof()
    row = operating_compact_row()
    projection = compact.sealed(dict(rows=[row], screened_total=1, exclusion_counts={},
        source_manifest_sha256="d"*64, source_tuning_allowed=True,
        owner_execution_model_validation=proof["owner_execution_model_validation"], **compact.AUTHORITY))
    prepared = []
    monkeypatch.setattr(compact, "prepare", lambda *a: prepared.append(a) or projection)
    monkeypatch.setattr(compact, "runtime_inference_cost_receipt", lambda *_: proof["runtime_inference_cost_receipt"])
    monkeypatch.setattr(evidence, "entry_risk_adjudication_openai_schema", lambda *_: {})
    monkeypatch.setattr(evidence, "validate_entry_risk_adjudication", lambda *a, **k: [])
    calls = []
    def runner(request):
        calls.append(request)
        return {"candidate_response": {"risk_verdict": "PASS"}}
    compact.run(data_root=root, day="2026-09-17", execute=True, runner=runner)
    compact.run(data_root=alias, day="2026-09-17", execute=True, runner=runner)
    assert len(prepared) == len(calls) == 1
    raw = root / "ai_decision_trace/ai_decision_trace_2026-09-17.jsonl"
    raw.parent.mkdir()
    raw.write_text("changed generation")
    with pytest.raises(ValueError, match="finalize_requires_evaluation"):
        compact.run(data_root=alias, day="2026-09-17", allow_source_rebuild=False)
    assert len(prepared) == len(calls) == 1
