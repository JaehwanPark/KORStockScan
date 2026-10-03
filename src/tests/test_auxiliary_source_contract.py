from copy import deepcopy
import json

import pytest

from src.engine.scalping import auxiliary_source_contract as A
from src.engine.scalping import compact_auxiliary_paired_replay as C
from src.engine.scalping import samsung_auxiliary_scope_research as R


def identity(**changes):
    return dict(source_date="2026-10-02", decision_ts="2026-10-02T10:00:00+09:00",
        stock_code="005930", effective_venue="KRX", session_bucket="KRX_REGULAR",
        evaluation_attempt_id="attempt", machine_bundle_sha256="b"*64,
        machine_observation_sha256="c"*64, **changes)


@pytest.mark.parametrize("code,scope", [("005930","samsung"),("000660","non_samsung"),
    (None,"unknown"),(5930,"unknown"),("005930_AL","unknown"),("","unknown")])
def test_partitions_do_not_guess_symbol(code, scope):
    assert A.partition({"stock_code": code}) == scope


def test_capsule_preserves_missing_and_distinct_clocks_without_input_mutation():
    row = identity()
    before = deepcopy(row)
    pre = A.capsule(row, producer="observer", clock="2026-10-02T09:59:59+09:00")
    post = A.capsule(row, producer="response", clock=row["decision_ts"], references={
        "pre_ai_capsule": pre, "pre_ai_append_receipt": {
            "capsule_sha256": pre["sha256"], "structured_append_succeeded": True}})
    assert A.capsule_errors(post, row) == []
    assert pre["identity"]["request_envelope_sha256"] is None
    assert "request_envelope_sha256" in pre["missing_reasons"]
    assert row == before
    post["identity"]["stock_code"] = "000660"
    assert A.capsule_errors(post) == ["capsule_hash_or_contract_invalid"]


def test_capsule_scope_case_difference_preserves_native_text_and_exact_link():
    row = identity()
    pre = A.capsule(row, producer="machine", clock=row["decision_ts"])
    response = {**row, "session_bucket":"krx_regular"}
    post = A.capsule(response, producer="response", clock=row["decision_ts"], references={
        "pre_ai_capsule":pre, "pre_ai_append_receipt":{"capsule_sha256":pre["sha256"], "structured_append_succeeded":True}})
    assert A.capsule_errors(post, response) == []
    assert pre["identity"]["session_bucket"] == "KRX_REGULAR"
    assert post["identity"]["session_bucket"] == "krx_regular"
    assert not A.identity_equal("session_bucket", "KRX_REGULAR", "KRX_REGULAR_AL")
    assert not A.identity_equal("evaluation_attempt_id", "ABC", "abc")


@pytest.mark.parametrize("damage", ["scope", "future", "append", "receipt"])
def test_pre_ai_receipt_conflicts_do_not_become_exact_source(damage):
    row = identity()
    pre = A.capsule({**row, "session_bucket": "NXT" if damage == "scope" else "KRX_REGULAR"},
        producer="observer", clock="2026-10-02T11:00:00+09:00" if damage == "future" else row["decision_ts"])
    result = A.capsule(row, producer="response", clock=row["decision_ts"], references={
        "pre_ai_capsule": pre, "pre_ai_append_receipt": {
            "capsule_sha256": "different" if damage == "receipt" else pre["sha256"],
            "structured_append_succeeded": damage != "append"}})
    if damage == "append":
        assert A.capsule_errors(result, row) == []
        assert result["references"]["pre_ai_append_receipt"]["structured_append_succeeded"] is False
    else:
        assert A.capsule_errors(result, row)


def test_conditional_plan_is_not_executable_and_damaged_contract_isolated():
    probe = dict(schema="entry_pre_ai_conditional_probe_observation_v1", stock_code="005930",
        reservation_performed=False, runtime_effect=False)
    probe["sha256"] = A.digest(probe)
    row = dict(stock_code="005930", entry_economic_observation_probe_contract=json.dumps(probe))
    assert A.plan_state(row)["state"] == "conditional_on_unknown_fill"
    assert A.plan_state(row)["executable"] is False
    row["stock_code"] = "000660"
    assert A.plan_state(row)["errors"] == ["conditional_probe_symbol_conflict"]


def test_ledger_conserves_rows_and_exact_links_without_counting_orphan_as_machine_miss():
    machine = {**identity(), "record_kind":"machine", "machine_action":"ENTER_NOW"}
    response = {**identity(), "record_kind":"response", "decision_trace_id":"trace",
        "provider_called": True, "response_received":True, "semantic_status":"pass", "quality_status":"pass"}
    blocked = {**machine, "machine_observation_sha256":"d"*64, "machine_action":"BLOCK"}
    row = {**identity(), "evaluation_key":"trace", "entry_economic_source_blocker":"exact_stop_missing"}
    report = A.ledger([machine, blocked], [response, response], [row], stage_keys=["trace"])
    assert report["record_count"] == sum(report["primary_counts"].values()) == 3
    assert report["duplicate_count"] == 1
    assert report["primary_counts"] == {"response_linked":1,"not_called_by_machine":1,"stage_comparable":1}
    assert len(report["exact_links"]) == 1
    response["evaluation_attempt_id"] = "other"
    assert A.ledger([machine], [response])["exact_links"] == []


def test_historical_projection_counts_responses_without_inventing_machine_source():
    row = {**identity(), "evaluation_key":"trace", "raw_response":{"risk_verdict":"PASS"},
        "natural_contract_evidence":{"semantic_validation_status":"pass","decision_quality_contract_status":"pass"}}
    projection = C.sealed(dict(schema="compact_auxiliary_frozen_projection_v1", target_date="2026-10-02",
        source_projection_contract=C.SOURCE_PROJECTION_CONTRACT, rows=[row]))
    diagnostic = C.evaluate_auxiliary_stage(projection)["source_diagnostics"]
    assert diagnostic["historical_machine_observed_count"] is None
    assert diagnostic["ledger"]["stages"]["provider_attempted"]["count"] == 1
    assert diagnostic["ledger"]["stages"]["response_received"]["count"] == 1
    assert diagnostic["ledger"]["exact_links"] == []


def test_conflicting_retry_not_counted_as_comparable():
    source = {**identity(), "record_kind":"response", "decision_trace_id":"trace", "provider_called":True}
    result = A.ledger([], [source, {**source, "source_body_sha256":"changed"}], stage_keys=["trace"])
    assert result["primary_counts"] == {"source_gap":1}
    assert result["conflicting_keys"] == ["response:trace"]
    assert "stage_outcome_eligible" not in result["stages"]


def test_timeout_empty_arrays_are_not_a_received_semantic_response():
    source = A.response_record({**identity(), "decision_trace_id":"timeout", "provider_called":True,
        "entry_ai_raw_risk_verdict":None, "entry_ai_raw_risk_codes":[], "result_source":"timeout"})
    result = A.ledger([], [source])
    assert result["primary_counts"] == {"transport_invalid":1}
    assert "response_received" not in result["stages"]


def test_operating_unsupported_cannot_hide_independent_stage_eligibility():
    source = {**identity(), "record_kind":"response", "decision_trace_id":"trace", "provider_called":True,
        "response_received":True, "semantic_status":"pass", "quality_status":"pass"}
    row = {**identity(), "evaluation_key":"trace", "entry_economic_source_status":"unsupported_scope"}
    assert A.ledger([], [source], [row], stage_keys=["trace"])["primary_counts"] == {"stage_comparable":1}


def test_caution_requires_same_native_opportunity_generation_and_later_clock():
    base = {**identity(), "scanner_promotion_id":"promotion", "issued_prompt_sha256":"p"*64,
        "parent_auxiliary_soft_policy_sha256":"s"*64, "evaluation_key":"caution", "incumbent_verdict":"CAUTION"}
    other = {**base, "evaluation_key":"pass", "incumbent_verdict":"PASS", "decision_ts":"2026-10-02T10:01:00+09:00"}
    assert A.caution_lifecycle([base, other])["rows"][0]["next_trace"] == "pass"
    other["scanner_promotion_id"] = "another"
    assert A.caution_lifecycle([base, other])["rows"][0]["status"] == "followup_not_observed"
    assert A.caution_lifecycle([base])["rows"][0]["realized_net_profit"] is None


def test_partition_research_cannot_freeze_whole_scope_policy(tmp_path):
    stage = C.sealed(dict(partition_scope="non_samsung", policy_publication_forbidden=True, scope_results={}))
    with pytest.raises(ValueError, match="not_a_publishable"):
        C.freeze_auxiliary_selection(tmp_path / "forbidden.json", "2026-10-02", stage)
    assert not (tmp_path / "forbidden.json").exists()


def test_publisher_rejects_partition_before_loading_or_writing_runtime(tmp_path):
    from datetime import datetime
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    source = C.sealed(dict(schema=C.SCHEMA, target_date="2026-10-02", source_manifest_sha256="m"*64,
        auxiliary_stage=C.sealed(dict(partition_scope="non_samsung"))))
    with pytest.raises(ValueError, match="partition_research_publication_forbidden"):
        M.publish_compact_evaluation(source, source_receipt={"source_manifest_sha256":"m"*64},
            publication_day="2026-10-03", data_root=tmp_path,
            now=datetime.fromisoformat("2026-10-03T12:00:00+09:00"))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("compressed", [False, True])
def test_partial_source_line_cannot_become_valid_empty_projection(tmp_path, compressed):
    import gzip
    path = tmp_path / "ai_decision_trace/ai_decision_trace_2026-10-02.jsonl"
    path.parent.mkdir()
    data = b'{"decision_stage": "entry_screen"\n'
    if compressed:
        path.with_suffix(".jsonl.gz").write_bytes(gzip.compress(data))
    else:
        path.write_bytes(data)
    with pytest.raises((ValueError, OSError)):
        C.prepare(tmp_path, "2026-10-02")


def test_gzip_machine_and_response_source_census_retains_noncalled_anchor(tmp_path):
    import gzip
    from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION
    machine = dict(schema="mechanistic_entry_observation_v1", label_context=identity(),
        source={"assessment":{"action":"BLOCK"}}, redacted=False,
        bundle_sha256="b"*64, captured_at=identity()["decision_ts"])
    machine["machine_observation_sha256"] = A.digest(machine)
    trace = {**identity(), "decision_stage":"entry_screen", "decision_trace_id":"not-called",
             "prompt_version": AI_VERSION, "provider_called":False, "entry_mechanistic_action":"BLOCK"}
    for folder, value in (("ai_decision_payloads",machine),("ai_decision_trace",trace)):
        path = tmp_path / folder / f"{folder}_2026-10-02.jsonl.gz"
        path.parent.mkdir()
        path.write_bytes(gzip.compress((json.dumps(value)+"\n").encode()))
    projection = C.prepare(tmp_path, "2026-10-02")
    assert projection["rows"] == []
    stage = C.evaluate_auxiliary_stage(projection)
    ledger = stage["source_diagnostics"]["ledger"]
    assert ledger["primary_counts"] == {"not_called_by_machine":1, "provider_attempt_not_observed":1}
    assert ledger["stages"]["machine_observed"]["count"] == 1
    assert C.valid(projection)


def test_caution_default_parent_is_explicit_none_not_missing_generation():
    row = {**identity(), "scanner_promotion_id":"promotion", "issued_prompt_sha256":"p"*64,
        "parent_auxiliary_soft_policy":None, "parent_auxiliary_soft_policy_sha256":None,
        "incumbent_verdict":"CAUTION", "evaluation_key":"trace"}
    assert A.caution_lifecycle([row])["rows"][0]["status"] == "followup_not_observed"
    row.pop("parent_auxiliary_soft_policy")
    assert A.caution_lifecycle([row])["identity_excluded_keys"] == ["trace"]


def test_partitioned_evaluator_keeps_unknown_separate_and_requires_source_seal():
    projection = C.sealed(dict(schema="compact_auxiliary_frozen_projection_v1", target_date="2026-10-02",
        rows=[{**identity(), "evaluation_key":"samsung"}, {**identity(), "stock_code":"000660", "evaluation_key":"other"},
              {**identity(), "stock_code":None, "evaluation_key":"unknown"}]))
    non_sam = C.evaluate_auxiliary_stage(projection, partition_scope="non_samsung")
    assert non_sam["screened_total"] == 1
    assert non_sam["policy_publication_forbidden"] is True
    projection["rows"].append({})
    with pytest.raises(ValueError, match="projection_invalid"):
        C.evaluate_auxiliary_stage(projection, partition_scope="samsung")


@pytest.mark.parametrize("session,supported", [("krx_regular",True),("KRX_REGULAR",True),
    ("KRX_REGULAR_AL",False),("UNKNOWN",False)])
def test_cost_binding_normalizes_registered_scope_only(monkeypatch, session, supported):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    profile = dict(profile_id="reviewed", economic_source_sha256="a"*64,
        buy_fee_bps=1.5, sell_fee_bps=1.5, statutory_sell_tax_bps=20, uncertainty_buffer_bps=0)
    monkeypatch.setattr(calibration, "_hierarchy_cost_profiles", lambda *args: {"005930":profile})
    row = {**identity(), "session_bucket":session, "ai_stage_path":{"conservative_execution_cost_pct":.1}}
    before = deepcopy(row)
    bound = C.bind_stage_full_cost(row, "/unused")
    assert row == before
    assert bound["session_bucket"] == session
    assert C.stage_full_cost_valid(bound) is supported
    if supported:
        assert bound["ai_stage_path"]["conservative_execution_cost_pct"] == pytest.approx(.33)
        assert bound["ai_stage_path"]["entry_cost_contract"]["session_bucket"] == "KRX_REGULAR"
        assert C.bind_stage_full_cost(bound, "/unused") == bound
        bound["source_date"] = "2026-09-30"
        assert C.stage_full_cost_valid(bound) is False


def test_research_scope_cannot_expand_to_other_samsung_origin():
    assert R.in_scope({**identity(), "watch_origin":"MAIN_FIXED_WATCH"})
    assert not R.in_scope({**identity(), "watch_origin":"SCANNER"})


def test_type_cells_preserve_unknown_and_missing_net(monkeypatch):
    monkeypatch.setattr(C,"auxiliary_stage_net",lambda row:None)
    row = {**identity(),"evaluation_key":"trace","scanner_promotion_id":"promotion",
           "incumbent_verdict":"PASS","input":{"entry_setup_evidence_v1":{"mechanistic_context":{
               "group":{"key_parts":{"structure_phase":"untrusted"}}}}}}
    cell = R.type_error_cells([row], {"trace"})[0]
    assert cell["phase"] == cell["flow"] == cell["liquidity"] == "UNKNOWN"
    assert cell["cost_gap_count"] == 1
    assert cell["cf_loss_pass_count"] == 0
    assert cell["realized_profit"] is None


def test_research_choices_use_training_phase_only():
    item = {"rebuilt":{"mechanistic_context":{"group":{"key_parts":{"structure_phase":"continuation"}}}}}
    expected = R.definitions([item])
    item["future_profit"] = 1000
    assert R.definitions([item]) == expected
    assert len(expected) == 12
    assert {s["required_consecutive"] for s in expected} == {1,2}
    assert len(R.definitions([])) == 6


def test_repeat_confirmation_cannot_cross_native_admission_or_stale_gap(monkeypatch):
    monkeypatch.setattr(R.R, "prototype_decision", lambda *args: {"action":"ENTER_NOW"})
    base = {**identity(), "watch_origin":"MAIN_FIXED_WATCH", "watch_admission_id":"first", "watch_generation_id":"gen"}
    rows = [{**base, "decision_ts":stamp} for stamp in
        ("2026-10-02T09:00:00+09:00", "2026-10-02T09:00:30+09:00", "2026-10-02T09:02:00+09:00")]
    rows.append({**base, "watch_admission_id":"second", "decision_ts":"2026-10-02T09:02:20+09:00"})
    prepared = {"decision":{"action":"RECHECK"},"rebuilt":{"mechanistic_context":{"group":{"key_parts":{"structure_phase":"continuation"}}}}}
    spec = {"time_window":"all", "required_consecutive":2, "repeat_max_gap_sec":60}
    before = deepcopy(rows)
    assert [d['action'] for d in R.replay(rows,[prepared]*4,{},spec)] == ['RECHECK','ENTER_NOW','RECHECK','RECHECK']
    assert rows == before


def test_exact_candidate_response_join_requires_trace_attempt_and_predecision_digest(monkeypatch):
    monkeypatch.setattr(R.D, "setup_join_digest", lambda setup: setup.get("hash"))
    machine = {**identity(), "ai_decision_trace_id":"trace", "bundle_sha256":"b"*64,
               "setup_evidence":{"hash":"exact"}}
    response = {**identity(), "evaluation_key":"trace", "session_bucket":"krx_regular",
                "input":{"entry_setup_evidence_v1":{"hash":"exact"}}}
    assert R.exact_response(machine,response)
    for field, value in (("evaluation_key","other"),("evaluation_attempt_id","other"),("machine_bundle_sha256","wrong"),
        ("decision_ts","2026-10-02T10:01:01+09:00"),("session_bucket","NXT_REGULAR")):
        assert not R.exact_response(machine,{**response,field:value})


def test_research_warm_cache_and_incomplete_checkpoint_fail_closed(tmp_path, monkeypatch):
    (tmp_path / "tmp").mkdir()
    src = tmp_path / "source.json"
    src.write_text("{}")
    monkeypatch.setattr(R, "inputs", lambda root: [src])
    output = tmp_path / "tmp/result"
    output.mkdir()
    C.write(output / "result.json", C.sealed(dict(fingerprint="old")))
    with pytest.raises(ValueError, match="generation_changed"):
        R.run(tmp_path, output)
    (output / "result.json").unlink()
    (output / "frozen-candidates.json").write_text("{}")
    with pytest.raises(ValueError, match="incomplete_frozen_checkpoint"):
        R.run(tmp_path, output)
