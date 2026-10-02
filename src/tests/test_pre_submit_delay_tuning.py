"""The delay family cannot promote partial quote evidence as executable EV."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from src.engine.scalping import pre_submit_delay_tuning as delay


def _price_pattern_fixture(tmp_path, monkeypatch, records, *, write=False):
    """Lossless forward-day observations, with no order/fill/exit receipts."""
    from src.engine.pipeline_event_summary import execution_projection_identity

    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report/pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle/pre_submit_delay_policy")
    day = "2026-10-02"
    directory = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    directory.mkdir(parents=True, exist_ok=True)
    events = []
    epoch = datetime(2026, 10, 2, 9, tzinfo=delay.KST).timestamp()
    for index, record in enumerate(records):
        stamp = epoch + record.get("offset", index * 300)
        prices = record["prices"]
        base = prices.get(0, 10000)
        frozen_type = delay.decision_type_snapshot(
            price=base, ask=base, bid=base - 1, venue="KRX", session="KRX_REGULAR")
        commit = {
            "delay_intent_id": f"intent-{index}", "entry_action": "ENTER_NOW",
            "auxiliary_effective_action": "PASS", "owner": "main_scalping",
            "planned_qty": 500, "route": "KRX_NXT_INTEGRATED",
            "market_session_bucket": "KRX_REGULAR", "decision_committed_at_epoch": stamp,
            "quote_transport_epoch": 7, "delay_policy_sha256": "parent-delay",
            "original_machine_observation_sha256": record.get("machine", delay._digest(index)),
            "price_cap": record.get("cap", base), "delay_decision_type": frozen_type,
            **record.get("commit_overrides", {}),
        }
        commit["decision_source_sha256"] = delay.decision_source_sha256(commit)
        stages = [("pre_submit_delay_committed", commit)]
        for second, price in prices.items():
            quote = {
                "delay_intent_id": commit["delay_intent_id"], "target_delay_sec": second,
                "actual_offset_sec": second, "quote_observed_at_epoch": stamp + second,
                "decision_source_sha256": commit["decision_source_sha256"],
                "quote_transport_epoch": 7, "route": commit["route"], "quote_route": commit["route"],
                "ask_price": price, "best_bid": price - 1, "ask_qty": 1,
                "ws_last_0d_epoch": stamp + second - .2,
                "quote_valid": True, "quote_consistency_state": "single_source",
                "route_depth_source_sha256": "a" * 64,
                **record.get("quote_overrides", {}).get(second, {}),
            }
            quote["quote_source_sha256"] = delay.quote_source_sha256(quote)
            stages.append(("pre_submit_delay_quote_observed", quote))
        for stage, fields in stages:
            event = {
                "schema_version": 1, "event_type": "threshold_cycle_event",
                "family": delay.FAMILY, "pipeline": "entry", "stage": stage,
                "stock_name": "fixture", "stock_code": record.get("code", "005930"),
                "record_id": index + 1, "fields": fields,
                "emitted_at": datetime.fromtimestamp(stamp, delay.KST).isoformat(), "emitted_date": day,
            }
            event["execution_source_event_sha256"] = execution_projection_identity(event)
            events.append(event)
    (directory / "part-execution-fixture.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
    return delay.build_report(day, effective_date="2026-10-05", write=write)


def test_price_pattern_computes_without_actual_orders_or_terminal(tmp_path, monkeypatch):
    report = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 9950, 60: 10050, 120: 10000, 180: 9900}},
    ], write=True)
    price = report["price_pattern_analysis"]
    assert price["status"] == "computed" and price["analysis_complete"] is True
    assert [row["mean_paired_price_improvement_bp"] for row in price["candidate_grid"]] == [0, 50, -50, 0, 100]
    assert price["candidate_grid"][2]["price_cap_exceeded_count"] == 1
    assert price["candidate_grid"][1]["paired_count"] == 1  # Depth 1 vs planned qty 500.
    assert price["examples"][0]["price_change_bp"] == -50
    assert price["examples"][0]["frozen_spread_bp"] is not None
    assert len(price["examples"]) <= 8
    assert report["terminal_observation_count"] == 0
    assert report["first_blocker"] == "exact_submit_terminal_receipt_missing"
    assert report["selected_delay_sec"] is None
    assert all(row["paired_net_ev_delta_pct"] is None for row in report["candidate_grid"])
    assert delay.price_pattern_projection(report)["analysis_complete"] is True
    policy = json.loads(delay.policy_path("2026-10-02").read_text())
    assert policy["runtime_apply_allowed"] is False
    assert policy["report_sha256"] == delay._digest({k: v for k, v in report.items() if k != "policy_sha256"})
    from src.engine.automation import postclose_summary_handoff as stages, runtime_policy_bootstrap as bootstrap
    assert stages._stage_output_issues(tmp_path / "report", "2026-10-02", delay.FAMILY) == []
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    assert bootstrap._pre_submit_delay_handoff("2026-10-05")[0] == {}


@pytest.mark.parametrize("prices,status,counts", [
    ({0: 10000, 30: 9950}, "partial", [1, 1, 0, 0, 0]),
    ({30: 9950, 60: 10050}, "source_gap", [0, 0, 0, 0, 0]),
    ({0: 10000}, "source_gap", [1, 0, 0, 0, 0]),
])
def test_price_pattern_partial_horizons_do_not_require_all_quotes(tmp_path, monkeypatch, prices, status, counts):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": prices}])["price_pattern_analysis"]
    assert price["status"] == status
    assert [row["paired_count"] for row in price["candidate_grid"]] == counts
    assert price["candidate_grid"][4]["mean_paired_price_improvement_bp"] is None


def test_price_pattern_averages_paired_returns_not_prices(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"code": "000001", "prices": {0: 10000, 30: 9500}},
        {"code": "000002", "prices": {0: 1000, 30: 1050}, "cap": None},
    ])["price_pattern_analysis"]
    row = price["candidate_grid"][1]
    assert row["mean_paired_price_improvement_bp"] == 0
    assert row["improved_count"] == row["worse_count"] == 1
    assert row["coverage"] == 1 and row["improved_fraction"] == .5
    assert (row["p10_price_improvement_bp"], row["p90_price_improvement_bp"]) == (-400, 400)
    assert row["price_cap_unknown_count"] == 1


def test_price_pattern_boolean_zero_horizon_cannot_supply_control_price(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [{
        "prices": {0: 10000, 30: 9950}, "quote_overrides": {0: {"target_delay_sec": False}},
    }])["price_pattern_analysis"]
    assert price["status"] == "source_gap"
    assert all(row["paired_count"] == 0 for row in price["candidate_grid"])


@pytest.mark.parametrize("overrides", [
    {"quote_transport_epoch": 8}, {"quote_route": "NXT_ONLY"},
    {"ask_price": True}, {"best_bid": 20000}, {"actual_offset_sec": -1},
    {"quote_consistency_state": "conflicted"},
])
def test_price_pattern_isolates_invalid_horizon(tmp_path, monkeypatch, overrides):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [{
        "prices": {0: 10000, 30: 9950, 60: 9900}, "quote_overrides": {30: overrides},
    }])["price_pattern_analysis"]
    assert price["status"] == "partial"
    assert price["candidate_grid"][1]["paired_count"] == 0
    assert price["candidate_grid"][2]["mean_paired_price_improvement_bp"] == 100


@pytest.mark.parametrize("change,expected,recommended", [
    (-50, "pattern_supported", 30), (50, "pattern_supported", 0),
    (0, "no_price_difference", 0),
])
def test_price_pattern_validates_delay_immediate_and_ties(tmp_path, monkeypatch, change, expected, recommended):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 10000 + change, 60: 10000 + change}} for _ in range(3)
    ])["price_pattern_analysis"]
    assert price["selection"]["status"] == expected
    assert price["selection"]["comparison_delay_sec"] == 30  # Shortest tied delay.
    assert price["recommended_delay_sec"] == recommended
    assert price["selection"]["validation_paired_count"] == 1


def test_price_pattern_does_not_reselect_from_validation(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 9900, 60: 9950}},
        {"prices": {0: 10000, 30: 9900, 60: 9950}},
        {"prices": {0: 10000, 30: 10100, 60: 9700}},
    ])["price_pattern_analysis"]
    assert price["recommended_delay_sec"] == 30
    assert price["selection"]["status"] == "pattern_not_confirmed"
    assert price["selection"]["validation_mean_price_improvement_bp"] == -100


def test_price_pattern_validation_coverage_and_tail_use_frozen_candidate_pairs(tmp_path, monkeypatch):
    report = _price_pattern_fixture(tmp_path, monkeypatch,
        [{"prices": {0: 10000, 30: 9950}} for _ in range(4)] + [
            {"prices": {0: 10000, 30: 10100}},
            {"prices": {0: 10000}},
            {"prices": {0: 10000, 30: 9800}},
        ])
    selection = report["price_pattern_analysis"]["selection"]
    stats = selection["validation_statistics"]
    assert selection["comparison_delay_sec"] == selection["recommended_delay_sec"] == 30
    assert selection["status"] == "pattern_supported"
    assert stats["eligible_opportunity_count"] == 3 and stats["paired_count"] == 2
    assert stats["coverage"] == pytest.approx(2 / 3)
    assert stats["improved_count"] == stats["worse_count"] == 1
    assert stats["mean_paired_price_improvement_bp"] == stats["median_price_improvement_bp"] == 50
    assert (stats["p10_price_improvement_bp"], stats["p90_price_improvement_bp"]) == (-70, 170)
    assert delay.price_pattern_projection(report)["analysis_complete"] is True


def test_price_pattern_purges_overlapping_learning_paths(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"offset": index * 30, "prices": {0: 10000, 30: 9900, 180: 9800}} for index in range(3)
    ])["price_pattern_analysis"]
    assert price["status"] == "partial" and price["analysis_complete"] is True
    assert price["selection"]["purged_learning_count"] == 2
    assert price["selection"]["status"] == "insufficient_sample"


def test_price_pattern_keeps_first_retry_even_when_later_has_better_source(tmp_path, monkeypatch):
    machine = "b" * 64
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"machine": machine, "prices": {30: 9950}},
        {"machine": machine, "prices": {0: 10000, 30: 9900}},
    ])["price_pattern_analysis"]
    assert price["eligible_attempt_count"] == 2 and price["eligible_opportunity_count"] == 1
    assert price["duplicate_intent_count"] == 1 and price["paired_comparison_count"] == 0
    assert price["status"] == "source_gap"


def test_price_pattern_unknown_retry_identity_keeps_prices_but_not_validation(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"machine": "", "prices": {0: 10000, 30: 9900}} for _ in range(3)
    ])["price_pattern_analysis"]
    assert price["paired_comparison_count"] == 3
    assert price["retry_linkage_unknown_count"] == 3
    assert price["selection"]["status"] == "insufficient_sample"


def test_price_pattern_candidate_ranking_requires_common_learning_pairs(tmp_path, monkeypatch):
    price = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 9900}}, {"prices": {0: 10000, 60: 9800}},
        {"prices": {0: 10000, 30: 9900, 60: 9800}},
    ])["price_pattern_analysis"]
    assert price["analysis_complete"] is True
    assert price["selection"]["status"] == "insufficient_comparable_pairs"
    assert price["recommended_delay_sec"] is None


def test_price_pattern_orphan_quotes_are_source_gap_not_valid_empty(tmp_path, monkeypatch):
    _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}])
    path = next((tmp_path / "threshold_cycle/date=2026-10-02/family=pre_submit_delay").glob("part-execution-*.jsonl"))
    path.write_text("".join(line + "\n" for line in path.read_text().splitlines()
                            if json.loads(line)["stage"] != "pre_submit_delay_committed"))
    report = delay.build_report("2026-10-02", effective_date="2026-10-05", write=False)
    assert report["price_pattern_analysis"]["status"] == "source_gap"
    assert report["price_pattern_analysis"]["empty_population_verified"] is False
    assert delay.price_pattern_projection(report)["status"] == "source_gap"


def test_price_pattern_explicit_veto_is_valid_empty_without_price_pairs(tmp_path, monkeypatch):
    report = _price_pattern_fixture(tmp_path, monkeypatch, [{
        "prices": {0: 10000, 30: 9900}, "commit_overrides": {"auxiliary_effective_action": "VETO"},
    }])
    assert report["price_pattern_analysis"]["status"] == "valid_empty"
    assert delay.price_pattern_projection(report)["status"] == "valid_empty"


@pytest.mark.parametrize("mutation", ["nested_authority", "nonfinite_statistic", "false_complete", "outer_schema",
                                      "wrong_metric", "selection_count", "validation_statistic", "zero_control",
                                      "quantile_order", "unsupported_comparison", "duplicate_candidates", "boolean_grid"])
def test_price_pattern_consumer_rejects_rehashed_semantic_contradictions(tmp_path, monkeypatch, mutation):
    report = _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}])
    section = report["price_pattern_analysis"]
    if mutation == "nested_authority":
        section["type_census"][0]["selection"]["runtime_apply_allowed"] = True
    elif mutation == "nonfinite_statistic":
        section["candidate_grid"][1]["mean_paired_price_improvement_bp"] = float("inf")
    elif mutation == "false_complete":
        section["status"] = "computed"
    elif mutation == "outer_schema":
        report["schema"] = "other_report"
    elif mutation == "selection_count":
        section["selection"]["learning_opportunity_count"] += 1
    elif mutation == "validation_statistic":
        section["selection"]["validation_statistics"]["p10_price_improvement_bp"] = 1
    elif mutation == "zero_control":
        section["candidate_grid"][0]["mean_paired_price_improvement_bp"] = 1
    elif mutation == "quantile_order":
        section["candidate_grid"][1]["median_price_improvement_bp"] = -1000
    elif mutation == "unsupported_comparison":
        section["selection"]["comparison_delay_sec"] = 60
    elif mutation == "duplicate_candidates":
        section["selection"]["candidate_delays_sec"] = [30, 30]
    elif mutation == "boolean_grid":
        section["candidate_grid"][0]["delay_sec"] = False
    else:
        section["primary_decision_metric"] = "realized_profit"
    section["section_sha256"] = delay._digest({k: v for k, v in section.items() if k != "section_sha256"})
    assert delay.price_pattern_projection(report)["status"] == "source_invalid"


def test_price_pattern_consumer_rejects_supported_direction_contradiction(tmp_path, monkeypatch):
    report = _price_pattern_fixture(tmp_path, monkeypatch, [
        {"prices": {0: 10000, 30: 9900}} for _ in range(3)
    ])
    section = report["price_pattern_analysis"]
    section["selection"]["validation_mean_price_improvement_bp"] = -100
    section["section_sha256"] = delay._digest({k: v for k, v in section.items() if k != "section_sha256"})
    assert delay.price_pattern_projection(report)["status"] == "source_invalid"


def test_price_pattern_legacy_and_tampered_section_fail_separately(tmp_path, monkeypatch):
    assert delay.price_pattern_projection({})["status"] == "not_evaluated_legacy"
    report = _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}], write=True)
    report["price_pattern_analysis"]["candidate_grid"][1]["paired_count"] = 3
    section = report["price_pattern_analysis"]
    section["section_sha256"] = delay._digest({k: v for k, v in section.items() if k != "section_sha256"})
    assert delay.price_pattern_projection(report)["status"] == "source_invalid"
    # Bind both outer hashes too: stage must still reject the semantic defect.
    policy = json.loads(delay.policy_path("2026-10-02").read_text())
    policy["report_sha256"] = delay._digest({k: v for k, v in report.items() if k != "policy_sha256"})
    policy["policy_sha256"] = delay._digest({k: v for k, v in policy.items() if k != "policy_sha256"})
    report["policy_sha256"] = policy["policy_sha256"]
    delay._atomic_json(delay.report_path("2026-10-02"), report)
    delay._atomic_json(delay.policy_path("2026-10-02"), policy)
    from src.engine.automation import postclose_summary_handoff as stages
    assert "pre_submit_delay:price_pattern_contract_invalid" in stages._stage_output_issues(
        tmp_path / "report", "2026-10-02", delay.FAMILY)


def _delay_fixture(tmp_path, monkeypatch, *, quote_overrides=None):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=pre_submit_delay"
    source.mkdir(parents=True, exist_ok=True)
    commit = {
        "delay_intent_id": "intent-1", "entry_action": "ENTER_NOW",
        "auxiliary_effective_action": "PASS", "owner": "main_scalping",
        "planned_qty": "5", "route": "KRX", "market_session_bucket": "KRX_REGULAR",
        "decision_committed_at_epoch": "100.0", "quote_transport_epoch": "7",
        "delay_policy_sha256": "policy", "original_machine_observation_sha256": "machine",
    }
    commit["decision_source_sha256"] = delay.decision_source_sha256(commit)
    quote = {
        "delay_intent_id": "intent-1", "target_delay_sec": "30.0",
        "actual_offset_sec": "30.0", "quote_observed_at_epoch": "130.0",
        "decision_source_sha256": commit["decision_source_sha256"],
        "quote_transport_epoch": "7", "route": "KRX", "quote_route": "KRX",
        "ask_price": "1550", "best_bid": "1549", "ask_qty": "1",
        "ws_last_0d_epoch": "129.8", "ws_last_0d_age_sec": "0.2",
        "quote_valid": "True", "quote_consistency_state": "single_source",
        "route_depth_source_sha256": "a" * 64,
    }
    quote.update(quote_overrides or {})
    quote["quote_source_sha256"] = delay.quote_source_sha256(quote)
    with (source / "part-execution-test.jsonl").open("w", encoding="utf-8") as handle:
        for index, (stage, fields) in enumerate((
            ("pre_submit_delay_committed", commit),
            ("pre_submit_delay_quote_observed", quote),
        )):
            event = {
                "schema_version": 1, "event_type": "threshold_cycle_event",
                "family": "pre_submit_delay", "pipeline": "entry", "stage": stage,
                "stock_name": "test", "stock_code": "355390", "record_id": 1,
                "fields": fields, "emitted_at": "2026-09-23T09:00:00+09:00",
                "emitted_date": "2026-09-23",
            }
            from src.engine.pipeline_event_summary import execution_projection_identity
            event["execution_source_event_sha256"] = execution_projection_identity(event)
            handle.write(json.dumps(event) + "\n")
    return commit, quote


def test_reader_quarantines_cross_epoch_and_mutated_quote_receipts(tmp_path, monkeypatch):
    commit, quote = _delay_fixture(tmp_path, monkeypatch, quote_overrides={"quote_transport_epoch": "8"})
    report = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert report["eligible_attempt_count"] == 1
    assert report["candidate_grid"][1]["source_valid_attempt_count"] == 0
    assert report["missing_counts"]["30s_source_invalid"] == 1
    assert report["source_quality_counts"]["quote_generation_or_epoch_mismatch"] == 1


def test_reader_accepts_exact_generation_once_and_rejects_late_clock(tmp_path, monkeypatch):
    _delay_fixture(tmp_path, monkeypatch)
    report = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert report["candidate_grid"][1]["source_valid_attempt_count"] == 1
    assert report["source_quality_counts"]["quote_valid"] == 1
    _delay_fixture(tmp_path, monkeypatch, quote_overrides={"quote_observed_at_epoch": "140.0"})
    report = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert report["candidate_grid"][1]["source_valid_attempt_count"] == 0
    assert report["source_quality_counts"]["quote_clock_or_hash_invalid"] == 1


def test_valid_quote_and_terminal_report_model_gap_without_source_gap(tmp_path, monkeypatch):
    commit, _ = _delay_fixture(tmp_path, monkeypatch)
    source = (tmp_path / "threshold_cycle" / "date=2026-09-23" /
              "family=pre_submit_delay" / "part-execution-test.jsonl")
    from src.engine.pipeline_event_summary import execution_projection_identity
    terminal = json.loads(source.read_text().splitlines()[0])
    terminal["stage"] = "pre_submit_delay_intent_terminal"
    terminal["fields"] = {"delay_intent_id": "intent-1",
                          "decision_source_sha256": commit["decision_source_sha256"],
                          "submit_finished_at_epoch": "131.0",
                          "submit_call_outcome": "returned_false",
                          "submit_call_broker_accepted": "False"}
    terminal["execution_source_event_sha256"] = execution_projection_identity(terminal)
    with source.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(terminal) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24")
    assert report["status"] == "model_not_validated"
    assert report["source"]["status"] == "ready"
    assert report["first_blocker"] == "paired_fill_terminal_cost_model_not_validated"
    assert all(row["paired_net_ev_pct"] is None for row in report["candidate_grid"])
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path("2026-09-23")))
    now = datetime(2026, 9, 24, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now)["status"] == "no_validated_delay_policy_not_evaluated"
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    assert bootstrap._pre_submit_delay_handoff("2026-09-24")[1]["status"] == "no_validated_candidate_not_evaluated"


def test_reader_quarantines_duplicate_horizon_and_unbound_terminal(tmp_path, monkeypatch):
    _delay_fixture(tmp_path, monkeypatch)
    source = (tmp_path / "threshold_cycle" / "date=2026-09-23" /
              "family=pre_submit_delay" / "part-execution-test.jsonl")
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    duplicate = json.loads(json.dumps(rows[1]))
    duplicate["emitted_at"] = "2026-09-23T09:00:01+09:00"
    duplicate["fields"]["ask_price"] = "1551"
    duplicate["fields"]["quote_source_sha256"] = delay.quote_source_sha256(duplicate["fields"])
    from src.engine.pipeline_event_summary import execution_projection_identity
    duplicate["execution_source_event_sha256"] = execution_projection_identity(duplicate)
    terminal = json.loads(json.dumps(rows[0]))
    terminal["stage"] = "pre_submit_delay_intent_terminal"
    terminal["fields"] = {
        "delay_intent_id": "intent-1", "decision_source_sha256": "old-generation",
        "submit_finished_at_epoch": "131.0",
    }
    terminal["execution_source_event_sha256"] = execution_projection_identity(terminal)
    with source.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(duplicate) + "\n")
        handle.write(json.dumps(terminal) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    row = report["horizon_source_quality"][1]
    assert row["eligible_attempt_count"] == 1
    assert row["observed_attempt_count"] == 1
    assert row["quarantined_attempt_count"] == 1
    assert row["unobserved_attempt_count"] == 0
    assert report["terminal_observation_count"] == 0
    assert report["raw_terminal_observation_count"] == 1
    assert report["source_quality_counts"]["terminal_unbound_or_clock_invalid"] == 1


def test_reader_distinguishes_valid_empty_source_partition(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=pre_submit_delay"
    source.mkdir(parents=True)
    (source / "part-execution-empty.jsonl").write_text("", encoding="utf-8")
    rows, receipt = delay._source_rows("2026-09-23")
    assert rows == []
    assert receipt["status"] == "valid_empty"
    assert receipt["raw_event_count"] == 0


def test_reader_keeps_uncertain_response_and_restart_gap_out_of_fill_economics(tmp_path, monkeypatch):
    commit, _ = _delay_fixture(tmp_path, monkeypatch)
    source = (tmp_path / "threshold_cycle" / "date=2026-09-23" /
              "family=pre_submit_delay" / "part-execution-test.jsonl")
    before = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert before["eligible_terminal_unobserved_count"] == 1
    assert before["horizon_source_quality"][2]["unobserved_attempt_count"] == 1
    assert before["candidate_grid"][1]["paired_net_ev_pct"] is None

    terminal = json.loads(source.read_text().splitlines()[0])
    terminal["stage"] = "pre_submit_delay_intent_terminal"
    terminal["fields"] = {
        "delay_intent_id": "intent-1",
        "decision_source_sha256": commit["decision_source_sha256"],
        "submit_finished_at_epoch": "131.0", "submit_call_outcome": "raised",
        "submit_call_broker_accepted": "False", "actual_order_submitted": "False",
    }
    from src.engine.pipeline_event_summary import execution_projection_identity
    terminal["execution_source_event_sha256"] = execution_projection_identity(terminal)
    with source.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(terminal) + "\n")
    after = delay.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert after["terminal_status_counts"] == {"response_uncertain": 1}
    assert after["eligible_terminal_unobserved_count"] == 0
    assert after["candidate_grid"][1]["paired_net_ev_pct"] is None


def test_decision_type_is_frozen_from_known_submit_inputs_and_reported_separately(tmp_path, monkeypatch):
    observed = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561, venue="KRX", session="KRX_REGULAR",
    )
    assert observed["type_key"] == "KRX|KRX_REGULAR|5_TO_10BP"
    assert observed["liquidity_band"] == "UNKNOWN"
    assert observed["volatility_band"] == "UNKNOWN"
    assert observed["market_cap_krw"] is None
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=pre_submit_delay"
    source.mkdir(parents=True)
    commit = {
        "delay_intent_id": "intent-1", "entry_action": "ENTER_NOW",
        "auxiliary_effective_action": "PASS", "planned_qty": 5,
        "owner": "main_scalping", "route": "KRX",
        "delay_decision_type": json.dumps(observed, sort_keys=True),
    }
    quote = {"delay_intent_id": "intent-1", "target_delay_sec": 30,
             "ask_price": 1550, "ask_qty": 1, "quote_valid": True, "route": "KRX"}
    with (source / "part-execution-test.jsonl").open("w", encoding="utf-8") as handle:
        for index, (stage, fields) in enumerate((
            ("pre_submit_delay_committed", commit),
            ("pre_submit_delay_quote_observed", quote),
        )):
            handle.write(json.dumps({
                "stage": stage, "fields": fields,
                "family": "pre_submit_delay", "emitted_date": "2026-09-23",
                "execution_source_event_sha256": f"{index + 1:064x}",
            }) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24")
    group = report["type_census"][0]
    assert group["type_key"] == observed["type_key"]
    assert group["eligible_attempt_count"] == 1
    assert group["candidate_grid"][1]["source_valid_attempt_count"] == 0
    assert group["candidate_grid"][1]["paired_net_ev_delta_pct"] is None
    assert report["selected_delay_sec"] is None
    assert report["first_blocker"] == "fresh_route_bound_horizon_quote_missing"
    policy = json.loads(delay.policy_path("2026-09-23").read_text())
    assert policy["type_policies"][observed["type_key"]]["selected_delay_sec"] is None
    assert policy["scope_policies"]["KRX|KRX_REGULAR"]["selected_delay_sec"] is None
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE",
                       str(delay.policy_path("2026-09-23")))
    loaded = delay.load_runtime_policy(
        now=datetime(2026, 9, 24, 9, tzinfo=timezone(timedelta(hours=9))),
        decision_type=observed,
    )
    assert loaded["delay_sec"] == 0  # Existing immediate-submit behavior, not a selected delay policy.
    assert loaded["status"] == "no_validated_delay_policy_source_gap"


def test_existing_post_decision_quote_is_counted_without_inventing_fill(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=dynamic_entry_price_resolver"
    source.mkdir(parents=True)
    (source / "part-execution-test.jsonl").write_text(json.dumps({
        "stage": "order_leg_sent", "emitted_date": "2026-09-23",
        "stock_code": "355390", "emitted_at": "2026-09-23T10:53:05+09:00",
    }) + "\n", encoding="utf-8")
    raw = tmp_path / "pipeline_events"
    raw.mkdir()
    with (raw / "pipeline_events_2026-09-23.jsonl").open("w", encoding="utf-8") as handle:
        for elapsed, ask in ((0, 1564), (30, 1550)):
            handle.write(json.dumps({
                "stock_code": "355390", "stage": "quote_observed",
                "emitted_at": (
                    datetime(2026, 9, 23, 10, 53, 5, tzinfo=timezone(timedelta(hours=9)))
                    + timedelta(seconds=elapsed)
                ).isoformat(),
                "fields": {"fresh_best_ask": ask},
            }) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24")
    from src.engine.automation import postclose_summary_handoff as stages
    assert stages.STAGE_REGISTRY["pre_submit_delay"][0] == ()
    assert stages._stage_output_issues(tmp_path / "report", "2026-09-23", "pre_submit_delay") == []
    census = report["existing_quote_census"]
    assert census["submit_count"] == 1
    assert census["horizon_stock_count"]["30"] == 1
    assert census["not_a_fill_or_route_validity_claim"] is True
    assert report["first_blocker"] == "exact_commit_and_horizon_quote_binding_missing"
    assert all(row["paired_net_ev_pct"] is None for row in report["candidate_grid"])
    assert delay._existing_quote_census("2026-09-23")["cache_hit"] is True

    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path("2026-09-23")))
    now = datetime(2026, 9, 24, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now)["delay_sec"] == 0
    assert delay.load_runtime_policy(now=now)["status"] == "no_validated_delay_policy_source_gap"
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    handoff_env, handoff = bootstrap._pre_submit_delay_handoff("2026-09-24")
    assert handoff["status"] == "no_validated_candidate_source_gap"
    assert handoff_env == {}
    # A self-consistent file pair still cannot promote a 30-second arm when
    # the underlying report only contains quote fields and no paired EV.
    source_report = json.loads(delay.report_path("2026-09-23").read_text())
    source_policy = json.loads(delay.policy_path("2026-09-23").read_text())
    source_report.pop("policy_sha256")
    source_policy.pop("policy_sha256")
    source_report["selected_delay_sec"] = 30.0
    source_policy.update(selected_delay_sec=30.0, runtime_apply_allowed=True,
                         selection_status="selected", model_status="validated",
                         paired_net_ev_delta_pct=1.0, holdout_net_ev_delta_pct=0.0,
                         expires_on="9999-12-31", carry_forward_until_superseded=True)
    source_policy["report_sha256"] = delay._digest(source_report)
    source_policy["policy_sha256"] = delay._digest(source_policy)
    source_report["policy_sha256"] = source_policy["policy_sha256"]
    delay._atomic_json(delay.report_path("2026-09-23"), source_report)
    delay._atomic_json(delay.policy_path("2026-09-23"), source_policy)
    assert delay.load_runtime_policy(now=now)["status"] == "policy_economics_unvalidated"
    assert bootstrap._pre_submit_delay_handoff("2026-09-24")[1]["status"] == "binding_invalid"
    delay.report_path("2026-09-23").write_text("{}\n", encoding="utf-8")
    assert delay.load_runtime_policy(now=now)["status"] == "policy_report_identity_invalid"
    assert bootstrap._pre_submit_delay_handoff("2026-09-24")[1]["status"] == "binding_invalid"


def test_source_census_aggregates_only_clean_baseline_partitions(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")

    def write_day(day, identity):
        source = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
        source.mkdir(parents=True)
        (source / "part-execution-test.jsonl").write_text(json.dumps({
            "stage": "pre_submit_delay_committed",
            "fields": {"delay_intent_id": identity},
            "family": "pre_submit_delay", "emitted_date": day,
            "execution_source_event_sha256": identity.ljust(64, "0"),
        }) + "\n", encoding="utf-8")

    write_day("2026-06-04", "archive-only")
    write_day("2026-06-05", "baseline-day")
    write_day("2026-09-22", "prior-day")
    write_day("2026-09-23", "target-day")
    rows, source = delay._source_rows("2026-09-23")
    assert [row["fields"]["delay_intent_id"] for row in rows] == [
        "baseline-day", "prior-day", "target-day",
    ]
    assert source["window_policy"] == "clean_baseline_cumulative_through_target_date"
    assert source["clean_tuning_baseline_date"] == "2026-06-05"
    assert source["source_dates"] == ["2026-06-05", "2026-09-22", "2026-09-23"]


def test_live_quote_observer_keeps_small_level_one_depth_as_valid_source(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append((a, kw)))
    monkeypatch.setattr(
        handlers, "_build_quote_consistency_fields",
        lambda *a, **kw: ({"quote_consistency_state": "single_source", "quote_consistency_entry_blocked": False}, 0, 0, 0),
    )
    stock = {"_pre_submit_delay_observation": {
        "id": "exact-intent", "committed_at_epoch": 100.0,
        "remaining_sec": [30.0], "route": "KRX",
        "quote_transport_epoch": 7, "decision_source_sha256": "d" * 64,
    }}
    ws = {
        "ws_route": "KRX", "orderbook": {
            "asks": [{"price": 1564, "volume": 1}],
            "bids": [{"price": 1561, "volume": 31}],
        }, "last_realtime_type_ts": {"0D": 129.8},
        "market_data_transport_epoch": 7,
        "realtime_type_snapshots_by_route": {"KRX|krx": {"0D": {
            "market_route": "KRX", "transport_epoch": 7,
            "observed_epoch": 129.8,
            "orderbook": {"asks": [{"price": 1564, "volume": 1}],
                          "bids": [{"price": 1561, "volume": 31}]},
        }}},
    }
    assert handlers.pre_submit_delay_observation_due(stock, now_ts=129.9) is False
    assert handlers.pre_submit_delay_observation_due(stock, now_ts=130.0) is True
    handlers.observe_pre_submit_delay_quote(stock, "355390", ws, now_ts=130.0)
    assert events[0][0][2] == "pre_submit_delay_quote_observed"
    assert events[0][1]["ask_qty"] == 1
    assert events[0][1]["quote_valid"] is True
    assert len(events[0][1]["quote_source_sha256"]) == 64
    assert events[0][1]["actual_order_submitted"] is False
    assert "_pre_submit_delay_observation" not in stock


def test_live_quote_observer_rejects_cross_route_depth_even_with_fresh_flat_bbo(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append(kw))
    monkeypatch.setattr(handlers, "_build_quote_consistency_fields",
                        lambda *a, **kw: ({"quote_consistency_state": "single_source"}, 0, 0, 0))
    stock = {"_pre_submit_delay_observation": {
        "id": "intent", "committed_at_epoch": 100.0, "remaining_sec": [30.0],
        "route": "KRX", "quote_transport_epoch": 7, "decision_source_sha256": "d" * 64,
    }}
    ws = {"ws_route": "KRX", "market_data_transport_epoch": 7,
          "orderbook": {"asks": [{"price": 1564, "volume": 1}],
                        "bids": [{"price": 1561, "volume": 31}]},
          "last_realtime_type_ts": {"0D": 129.8},
          "realtime_type_snapshots_by_route": {"NXT|nxt": {"0D": {
              "market_route": "NXT", "transport_epoch": 7,
              "observed_epoch": 129.8,
              "orderbook": {"asks": [{"price": 1564, "volume": 1}],
                            "bids": [{"price": 1561, "volume": 31}]},
          }}}}
    handlers.observe_pre_submit_delay_quote(stock, "355390", ws, now_ts=130.0)
    assert events[0]["quote_valid"] is False
    assert events[0]["route_depth_source_sha256"] is None


def test_session_route_uses_exact_partition_without_ws_route_or_flat_bbo(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append(kw))
    stock = {"market_session_bucket": "KRX_REGULAR", "_pre_submit_delay_observation": {
        "id": "intent", "committed_at_epoch": 100.0, "remaining_sec": [30.0],
        "route": "KRX_NXT_INTEGRATED", "quote_transport_epoch": 7,
        "decision_source_sha256": "d" * 64}}
    ws = {"market_data_transport_epoch": 7,
          "orderbook": {"asks": [{"price": 2000, "volume": 1}],
                        "bids": [{"price": 1990, "volume": 1}]},
          "realtime_type_snapshots_by_route": {"AL|krx_nxt_integrated": {"0D": {
              "market_route": "krx_nxt_integrated", "transport_epoch": 7,
              "observed_epoch": 129.8, "item": "355390_AL",
              "orderbook": {"asks": [{"price": 1550, "volume": 2}],
                            "bids": [{"price": 1549, "volume": 3}]}}}}}
    assert handlers._pre_submit_delay_expected_route(stock, ws) == "KRX_NXT_INTEGRATED"
    assert handlers._pre_submit_delay_expected_route(
        {"market_session_bucket": "PREMARKET_KRX_LIKE"}, ws) == "NXT_ONLY"
    assert handlers._pre_submit_delay_expected_route(
        {"market_session_bucket": "krx_like_premarket"}, ws) == "NXT_ONLY"
    assert handlers._pre_submit_delay_expected_route(
        {"market_session_bucket": "krx_regular"}, ws) == "KRX_NXT_INTEGRATED"
    handlers.observe_pre_submit_delay_quote(stock, "355390", ws, now_ts=130.0)
    assert events[0]["quote_valid"] is True
    assert events[0]["ask_price"] == 1550
    assert events[0]["best_bid"] == 1549
    assert events[0]["quote_route"] == "KRX_NXT_INTEGRATED"
    premarket = {"market_session_bucket": "krx_like_premarket", "_pre_submit_delay_observation": {
        "id": "pre-intent", "committed_at_epoch": 100.0, "remaining_sec": [30.0],
        "route": "NXT_ONLY", "quote_transport_epoch": 7,
        "decision_source_sha256": "e" * 64}}
    nxt_depth = {**ws["realtime_type_snapshots_by_route"]["AL|krx_nxt_integrated"]["0D"],
                 "market_route": "nxt_only", "item": "355390_NX"}
    handlers.observe_pre_submit_delay_quote(
        premarket, "355390", {**ws, "realtime_type_snapshots_by_route": {
            "NX|nxt_only": {"0D": nxt_depth}}}, now_ts=130.0)
    assert events[1]["quote_valid"] is True
    assert events[1]["quote_route"] == "NXT_ONLY"


def test_family_ledger_isolates_scanner_summary_gap_and_unmatched_family_raw(tmp_path, monkeypatch):
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor, execution_projection_identity
    from src.engine.automation import postclose_summary_handoff as handoff

    day = "2026-09-29"
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw_path.parent.mkdir()
    scanner = {"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
               "stage": "scalping_scanner_fast_precheck", "stock_name": "test",
               "stock_code": "355390", "record_id": 1, "fields": {},
               "emitted_at": f"{day}T10:00:00", "emitted_date": day}
    commit = {**scanner, "stage": "pre_submit_delay_committed", "record_id": 3,
              "fields": {"delay_intent_id": "intent-1", "entry_action": "ENTER_NOW",
                         "auxiliary_effective_action": "PASS", "owner": "main_scalping"}}
    raw_rows = [scanner, {**scanner, "record_id": 2}, commit,
                {**commit, "record_id": 4, "fields": {**commit["fields"], "delay_intent_id": "intent-2"}}]
    raw_path.write_text("".join(json.dumps(row) + "\n" for row in raw_rows))
    compact_dir = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    compact_dir.mkdir(parents=True)
    compact = {"schema_version": 1, "event_type": "threshold_cycle_event",
               "family": "pre_submit_delay", **{key: commit[key] for key in
               ("pipeline", "stage", "stock_name", "stock_code", "record_id", "fields", "emitted_at", "emitted_date")},
               "execution_source_event_sha256": execution_projection_identity(commit)}
    (compact_dir / "part-execution-1000.jsonl").write_text(json.dumps(compact) + "\n")
    compactor = ProducerSummaryCompactor(summary_dir=tmp_path / "pipeline_event_summaries", mode="shadow")
    for row in (scanner, commit, raw_rows[3]):
        compactor.submit(row)
    compactor.flush()
    ledger = delay.seal_family_source_ledger(tmp_path, day)
    assert ledger["summary_diagnostic"]["raw_summary_gap_by_stage"]["scalping_scanner_fast_precheck"] == 1
    assert ledger["status"] == "ready_with_isolation"
    assert ledger["matched_event_ids"] == [execution_projection_identity(commit)]
    assert len(ledger["raw_only_event_ids"]) == 1
    assert delay.family_source_ledger_issues(tmp_path, day) == []
    report = delay.build_report(day, effective_date="2026-09-30", write=False,
                                require_family_ledger=True)
    assert report["source"]["raw_only_event_count"] == 1
    assert report["selected_delay_sec"] is None
    monkeypatch.setattr(handoff, "_stage_code", lambda *args, **kwargs: "fixture-code")
    terminal = handoff.run_stage(
        "pre_submit_delay", day, report_dir=tmp_path / "report", project=tmp_path,
        runner=lambda *args, **kwargs: delay.build_report(
            day, effective_date="2026-09-30", require_family_ledger=True) and 0,
    )
    assert terminal["status"] == "succeeded"
    assert handoff.stage_receipt_issues(tmp_path / "report", day, "pre_submit_delay",
                                        code_hash="fixture-code") == []


def test_sealed_family_valid_empty_does_not_claim_source_gap_or_enable_delay(tmp_path, monkeypatch):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap

    day = "2026-09-29"
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir()
    raw.write_text(json.dumps({"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
                               "stage": "unrelated_stage", "stock_code": "355390", "record_id": 1,
                               "emitted_at": f"{day}T10:00:00", "emitted_date": day,
                               "fields": {}}) + "\n")
    ledger = delay.seal_family_source_ledger(tmp_path, day)
    assert ledger["status"] == "valid_empty"
    report = delay.build_report(day, effective_date="2026-09-30", require_family_ledger=True)
    assert report["source"]["status"] == "valid_empty"
    assert report["status"] == "valid_empty"
    assert report["selected_delay_sec"] is None
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path(day)))
    now = datetime(2026, 9, 30, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now)["status"] == "no_validated_delay_policy_not_evaluated"
    env, handoff = bootstrap._pre_submit_delay_handoff("2026-09-30")
    assert env == {}
    assert handoff["status"] == "no_validated_candidate_not_evaluated"


def test_due_intent_requires_same_policy_owner_quantity_cap_and_route(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    frozen_type = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561,
        venue="KRX", session="KRX_REGULAR",
    )
    due = {
        "id": "intent", "delay_sec": 30.0, "policy_sha256": "policy",
        "machine_key": ("attempt", "observation"),
        "machine_policy_sha256": "machine", "ai_policy_sha256": "ai",
        "ai_effective_assessment": "PASS", "planned_qty": 5,
        "price_cap": 1564, "route": "KRX", "decision_type": frozen_type,
    }
    policy = {"status": "loaded", "delay_sec": 30.0, "policy_sha256": "policy"}
    machine = {
        "entry_mechanistic_action": "ENTER_NOW",
        "evaluation_attempt_id": "attempt",
        "machine_observation_sha256": "observation",
        "entry_mechanistic_policy_sha256": "machine",
        "entry_ai_soft_policy_sha256": "ai",
        "entry_ai_effective_assessment": "PASS",
    }
    kwargs = dict(quote_route="KRX", requested_qty=5, final_price=1563)
    assert handlers.pre_submit_delay_due_matches(due, policy, machine, frozen_type, **kwargs)
    assert handlers.pre_submit_delay_due_matches(
        due, policy,
        {**machine, "entry_ai_effective_assessment": {"effective_verdict": "PASS"}},
        frozen_type, **kwargs,
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "final_price": 1565}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "requested_qty": 6}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "quote_route": "NXT"}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, {**policy, "policy_sha256": "successor"}, machine, frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "entry_ai_effective_assessment": "VETO"},
        frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine,
        {**frozen_type, "session_bucket": "NXT_AFTERMARKET"}, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine,
        {**frozen_type, "type_key": "KRX|KRX_REGULAR|GE_10BP"}, **kwargs
    )
    assert handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "evaluation_attempt_id": "successor"},
        frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "machine_observation_sha256": ""},
        frozen_type, **kwargs
    )


def test_expired_delay_does_not_submit_without_current_trigger(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append((a, kw)))
    stock = {"_pre_submit_delay_pending": {
        "id": "intent", "delay_sec": 30.0, "committed_at_epoch": 100.0,
        "due_monotonic": 200.0, "machine_key": ("attempt", "observation"),
    }}
    assert not handlers.expire_untriggered_pre_submit_delay(stock, "355390", now_mono=199.9)
    assert handlers.expire_untriggered_pre_submit_delay(stock, "355390", now_mono=200.0)
    assert "_pre_submit_delay_pending" not in stock
    assert events[0][0][2] == "pre_submit_delay_intent_terminal"
    assert events[0][1]["actual_order_submitted"] is False


def test_zero_delay_intent_closes_on_actual_submit_call(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline",
                        lambda *args, **fields: events.append((args[2], fields)))
    monkeypatch.setattr(handlers, "submit_attempt_fields", lambda *args: {
        "entry_submit_attempt_broker_accepted": True,
        "entry_submit_attempt_return_outcome": "returned",
    })
    stock = {"_pre_submit_delay_zero_intent": {
        "id": "zero-intent", "delay_sec": 0.0,
        "committed_at_epoch": 100.0,
        "machine_observation_sha256": "observation",
    }}
    handlers._observe_entry_submit_finished(stock, "005930", True)
    stage, fields = events[0]
    assert stage == "pre_submit_delay_intent_terminal"
    assert fields["delay_intent_id"] == "zero-intent"
    assert fields["selected_delay_sec"] == 0.0
    assert fields["actual_order_submitted"] is True
    assert "_pre_submit_delay_zero_intent" not in stock


def test_type_selected_delay_never_spills_into_another_type(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    target = "2026-09-23"
    effective = "2026-09-24"
    selected_type = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561, venue="KRX", session="KRX_REGULAR"
    )
    other_type = delay.decision_type_snapshot(
        price=25000, ask=25000, bid=24950, venue="KRX", session="KRX_REGULAR"
    )
    assert selected_type["type_key"] != other_type["type_key"]
    row = {"delay_sec": 30.0, "candidate_passed": True,
           "paired_net_ev_delta_pct": .2, "holdout_net_ev_delta_pct": .1,
           "source_valid_attempt_count": 12, "holdout_attempt_count": 4,
           "model_fill_error": .01}
    report = {
        "schema": delay.REPORT_SCHEMA, "analysis_axis": delay.FAMILY,
        "source_date": target, "effective_date": effective,
        "selected_delay_sec": None, "status": "validated_edge",
        "model_status": "validated", "source": {"status": "ready"},
        "terminal_observation_count": 12, "candidate_grid": [],
        "scope_census": [],
        "type_census": [{"type_key": selected_type["type_key"],
                         "candidate_grid": [row]}],
        "selected_type_policies": {selected_type["type_key"]: 30.0},
    }
    policy = {
        "schema": delay.POLICY_SCHEMA, "source_date": target,
        "effective_from": effective, "expires_on": "9999-12-31",
        "carry_forward_until_superseded": True,
        "selection_status": "selected_by_type",
        "selected_delay_sec": None, "runtime_apply_allowed": True,
        "scope_policies": {},
        "type_policies": {selected_type["type_key"]: {
            "selected_delay_sec": 30.0, "runtime_apply_allowed": True,
            "selection_status": "selected", "model_status": "validated",
            "paired_net_ev_delta_pct": .2, "holdout_net_ev_delta_pct": .1,
        }},
    }
    policy["report_sha256"] = delay._digest(report)
    policy["policy_sha256"] = delay._digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    delay._atomic_json(delay.report_path(target), report)
    delay._atomic_json(delay.policy_path(target), policy)
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path(target)))
    now = datetime(2026, 9, 24, 10, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now, decision_type=selected_type)["delay_sec"] == 30.0
    assert delay.load_runtime_policy(now=now, decision_type=other_type)["delay_sec"] == 0.0
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    assert bootstrap._pre_submit_delay_handoff(effective)[1]["status"] == "verified_candidate"
    carry_env, carry_receipt = bootstrap._pre_submit_delay_handoff("2026-09-25")
    assert carry_receipt["status"] == "verified_carried_candidate"
    assert carry_env["KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE"] == "2026-09-25"
    policy["type_policies"][selected_type["type_key"]]["holdout_net_ev_delta_pct"] = -.1
    policy["report_sha256"] = delay._digest({k: v for k, v in report.items() if k != "policy_sha256"})
    policy.pop("policy_sha256")
    policy["policy_sha256"] = delay._digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    delay._atomic_json(delay.report_path(target), report)
    delay._atomic_json(delay.policy_path(target), policy)
    assert delay.load_runtime_policy(now=now, decision_type=selected_type)["delay_sec"] == 0.0
