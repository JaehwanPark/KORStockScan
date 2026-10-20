"""Report diagnostics preserve frozen selection and incomplete native evidence."""
import json
from pathlib import Path

import pytest

from src.engine.automation import pre_submit_delay_partitioned_research as partitioned
from src.engine.automation import pre_submit_delay_research_review as review
from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import pre_submit_delay_initial_policy as initial


def _committed(tmp_path, *, missing_identity=False, with_short=False, short_value=2, algorithm=None):
    data = tmp_path / "data"
    candidate = tmp_path / "candidate"
    rows = []
    for anchor in ("price_ready", "signal_ready"):
        for n in range(6):
            at = 1792112400.0 + n * 600
            row = dict(identity=initial.digest([anchor, n]), alias=["2026-10-16", f"{n+1:06d}", anchor+str(n)],
                anchor_kind=anchor, session="REGULAR", parent_compatibility=["a"*64, "b"*64],
                native_evaluation_bound=True, committed_at=at, observation_end_at=at+183,
                p0_valid=True, situation="test_situation", execution_context="ALL",
                decision_source_sha256=initial.digest(["decision", anchor, n]),
                pairs={"30": (100 if n == 0 else -10), "60": 5},
                execution_features={"p0_ask": 10000, "p0_bid": 9995,
                                    "original_signal_reference_price": 9900})
            if n == 1:
                row["pairs"].pop("60")
            if not missing_identity:
                row["original_machine_observation_sha256"] = initial.digest(["machine", n])
                row["native_evaluation_attempt_id"] = "native:" + str(n)
            if with_short:
                row.update(research_short_p0_valid=True, research_short_pairs={"1": short_value})
            rows.append(row)
    report, policy = partitioned.build(rows,
        dict(raw_commit_n=12, qualified_pass_n=12, p0_valid_n=12,
             native_evaluation_unverified_n=0, parent_compatibility_unverified_n=0, exclusions={}),
        output_root=candidate, source_date="2026-10-16", publication_date="2026-10-16",
        effective_date="2026-10-19", source_sha256="c"*64, code_contract_sha256="d"*64,
        source_receipt={}, _algorithm=algorithm)
    generation = initial.digest([report, policy])
    base = data / "threshold_cycle/pre_submit_delay_policy/generations" / generation
    base.mkdir(parents=True)
    partitioned.copy_evidence(report, base)
    for name, value in (("report", report), ("policy", policy)):
        (base / (name + ".json")).write_bytes(storage.encoded(value))
    manifest = dict(schema=initial.MANIFEST_SCHEMA, source_date="2026-10-16", generation=generation,
                    source_sha256="c"*64, code_contract_sha256="d"*64,
                    report_artifact_sha256=initial.digest(report), policy_artifact_sha256=initial.digest(policy))
    manifest["manifest_sha256"] = initial.digest(manifest)
    pointer = base.parent.parent / "committed_2026-10-16.json"
    pointer.write_bytes(storage.encoded(manifest))
    return data, base, report, policy


def test_all_sharded_cells_frozen_membership_sparse_pairs_and_native_opportunities(tmp_path):
    data, base, original, policy = _committed(tmp_path)
    before = {str(p): p.read_bytes() for p in data.rglob("*.json")}
    output = tmp_path / "review"
    result = review.generate(data, "2026-10-16", output)
    assert result["census"]["anchors"] == 12
    assert result["unique_independent_opportunities"] == 6
    assert result["census"]["horizon_pairs"] == 22
    assert result["cells_ref"]["count"] == original["cells_ref"]["count"] == 4
    assert result["runtime_effect"] is False
    cells = list(storage.iter_tree(output, result["cells_ref"]))
    cell = next(c for c in cells if c["original_cell"]["anchor_kind"] == "price_ready")
    assert cell["original_cell"]["comparison_delay_sec"] == 30
    # The training winner fails holdout. This diagnostic cannot switch to 60.
    assert cell["selected_delay_sec"] == 0
    assert cell["selection_reason_normalized"] == "training_holdout_direction_not_confirmed"
    assert cell["evidence_verdict"] == "indeterminate"
    assert cell["optimal_delay_proven"] is False
    assert cell["candidates"]["30"]["train"]["n"] == 4
    assert cell["candidates"]["60"]["train"]["n"] == 3
    overlap = next(p for p in cell["pairwise_common_cohort"] if p["split"] == "train")
    assert overlap["left"]["n"] == overlap["right"]["n"] == 3
    original_members = {r["identity"]: r["split"] for part in storage.iter_tree(base, original["partitions_ref"])
                        for r in storage.iter_tree(base, part["membership"])}
    actual_members = {r["identity"]: r["split"] for r in storage.iter_tree(output, result["frozen_membership_ref"])}
    assert actual_members == original_members
    assert before == {str(p): p.read_bytes() for p in data.rglob("*.json")}
    assert result["original_policy_status"] == policy["selection_status"]


def test_anchor_counts_do_not_become_independent_opportunities_when_identity_missing(tmp_path):
    data, _, _, _ = _committed(tmp_path, missing_identity=True)
    result = review.generate(data, "2026-10-16", tmp_path / "review")
    assert result["unique_independent_opportunities"] is None
    assert result["known_identity_subset_unique_opportunities"] == 0
    assert result["independent_identity_status"] == "partial_native_identity_not_preserved"
    assert result["compact_enrichment"]["status"] == "unavailable"


def test_short_diagnostics_are_visible_without_reselecting_the_committed_policy(tmp_path):
    data, _, _, _ = _committed(tmp_path, with_short=True, algorithm=initial.PAIRED_ALGORITHM)
    result = review.generate(data, "2026-10-16", tmp_path / "review")
    assert result["horizons_sec"] == [1, 30, 60]
    cell = next(storage.iter_tree(tmp_path / "review", result["cells_ref"]))
    assert cell["candidates"]["1"]["train"]["mean_bp"] == 2
    assert cell["original_cell"]["candidate_delays_sec"] == [30, 60]
    groups = list(storage.iter_tree(tmp_path / "review", result["feature_groups_ref"]))
    assert {r["feature"] for r in groups} == {"original_signal_price_progress", "p0_spread_bp"}
    assert all(r["selection_authority"] is False for r in groups)


def test_v4_short_candidate_is_consumed_by_native_prepared_lookup(tmp_path):
    data, base, report, policy = _committed(tmp_path, with_short=True, short_value=50)
    prepared = initial.PreparedPolicy.from_artifacts(policy, report, target_date="2026-10-19")
    selected = prepared.lookup(target_date="2026-10-19", market="REGULAR",
                               kind="test_situation", parents=["a"*64, "b"*64])
    assert selected["delay_sec"] == 1
    assert policy["algorithm"] == initial.ALGORITHM
    initial.validate(policy, report, target_date="2026-10-19")


@pytest.mark.parametrize("invalid", [False, None, "true"])
def test_v4_cannot_select_short_quote_without_strict_p0_clock(invalid):
    row = dict(pairs={30: 1}, p0_valid=True, research_short_p0_valid=invalid, research_short_pairs={"1": 30})
    with pytest.raises(ValueError, match="short_pair_contract_invalid"):
        initial.selection_pairs(row, initial.ALGORITHM)
    assert initial.selection_pairs(row, initial.PAIRED_ALGORITHM) == {30: 1}


@pytest.mark.parametrize("basis,delay,allowed,expected", [
    ("incumbent_on_unconfirmed_pattern", 0, True, "indeterminate"),
    ("unsupported", None, False, "indeterminate"),
    ("unverified_lineage_immediate_default", 0, False, "indeterminate"),
    ("paired_quote_immediate", 0, True, "immediate_supported_on_observed_pairs"),
    ("paired_quote_initial", 30, True, "positive_delay_supported"),
    ("paired_quote_initial", 30, False, "indeterminate"),
])
def test_zero_evidence_is_distinct_from_existing_behavior(basis, delay, allowed, expected):
    assert initial.selection_evidence(dict(selection_basis=basis, delay_sec=delay,
                                           runtime_apply_allowed=allowed)) == expected


def _actual_fill():
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_legs
    at = "2026-10-20T09:25:30"
    legs = [dict(at=at, order_no="order1", execution_no="exec1", qty=1, price=100),
            dict(at="2026-10-20T09:25:34", order_no="order2", execution_no="exec2", qty=3, price=98)]
    trade = dict(id=1, code="403870", status="COMPLETED", buy_time=legs[1]["at"],
                 buy_qty=4, buy_price=98.5, add_count=0)
    fill = dict(code="403870", legs=legs, source={"sha256": "a"*64},
                buy_fill_identity=buy_fill_identity_from_legs(legs), position_buy_time=trade["buy_time"])
    return trade, fill, {"1": {"order1", "order2"}}


def test_fill_path_uses_first_and_last_fill_and_does_not_backfill_missing_horizons():
    trade, fill, orders = _actual_fill()
    first = review._epoch(fill["legs"][0]["at"])
    quotes = [dict(symbol="403870", known_at=first+1.1, ask=100, bid=99, source_sha256="a"*64),
              dict(symbol="403870", known_at=first+4+30.1, ask=97, bid=96, source_sha256="b"*64)]
    result = review._fill_path(trade, fill, quotes, orders)
    early, late = result["anchors"]
    assert early["fill_price"] == 100
    assert late["fill_price"] == 98.5
    assert early["horizons"][0]["ask_change_bp"] == 0
    assert early["horizons"][0]["bid_change_bp"] == -100
    assert early["horizons"][1]["status"] == "no_exact_horizon_quote"
    assert late["horizons"][3]["ask_change_bp"] < 0
    assert result["realized_pnl_krw"] is None
    assert early["continuous_coverage_proven"] is False


@pytest.mark.parametrize("mutation,reason", [
    ("owner", "main_order_owner_unverified"),
    ("quantity", "position_generation_or_scale_in_conflict"),
    ("symbol", "position_generation_or_scale_in_conflict"),
    ("scale_in", "position_generation_or_scale_in_conflict"),
])
def test_fill_path_rejects_wrong_owner_generation_and_scale_in(mutation, reason):
    trade, fill, orders = _actual_fill()
    if mutation == "owner":
        orders = {}
    elif mutation == "quantity":
        trade["buy_qty"] = 5
    elif mutation == "symbol":
        fill["code"] = "005930"
    else:
        trade["add_count"] = 1
    result = review._fill_path(trade, fill, [], orders)
    assert result["anchor_status"] == reason
    assert result["anchors"] == []


def test_execution_review_keeps_every_unlinked_trade_and_null_economics(tmp_path, monkeypatch):
    data = tmp_path/"data"
    data.mkdir()
    trade, _, _ = _actual_fill()
    monkeypatch.setattr(review, "_execution_sources", lambda *a: ([], {"gaps": ["missing"]}))
    monkeypatch.setattr(review, "_snapshot_fills", lambda *a: ({}, {"gaps": ["missing"]}))
    output = tmp_path/"review"
    result = review.generate_execution_review(data, "2026-10-20", output, trades=[trade])
    rows = list(storage.iter_tree(output, result["trades_ref"]))
    assert len(rows) == result["census"]["position_records"] == 1
    assert result["census"]["exact_fill_clock_records"] == 0
    assert result["default_zero_optimality_proven"] is False
    assert rows[0]["realized_pnl_krw"] is None
    assert result["policy_reselected"] is False


@pytest.mark.parametrize("fault", [None, "outer_hash_absent", "attempt", "machine", "position", "hash",
                                  "quote_hash", "stale_quote"])
def test_execution_join_requires_native_plan_identity_not_symbol_and_time(tmp_path, monkeypatch, fault):
    from src.tests.test_main_trailing_source_assembler import _issued_trailing_receipt, DAY
    from src.engine.scalping import pre_submit_delay_tuning as owner
    receipt, known, _ = _issued_trailing_receipt(tmp_path, monkeypatch)
    commit = dict(delay_intent_id="intent", owner="main_scalping", entry_action="ENTER_NOW",
        auxiliary_effective_action="PASS", original_machine_observation_sha256=receipt["machine_observation_sha256"],
        original_evaluation_attempt_id=receipt["evaluation_attempt_id"], planned_qty=2,
        decision_committed_at_epoch=known, market_session_bucket="REGULAR",
        anchor_kind="price_ready", route="KRX_NXT_INTEGRATED", quote_transport_epoch=7)
    if fault in ("attempt", "machine"):
        key = "original_evaluation_attempt_id" if fault == "attempt" else "original_machine_observation_sha256"
        commit[key] = "other" if fault == "attempt" else "f"*64
    commit["decision_source_sha256"] = owner.decision_source_sha256(commit)
    plan = dict(stage="entry_execution_sizing_plan", record_id=7, stock_code="005930", emitted_date=DAY,
        fields=dict(trailing_entry_plan_receipt=receipt, trailing_entry_plan_receipt_sha256=receipt["receipt_sha256"]))
    if fault == "position":
        plan["record_id"] = 8
    if fault == "hash":
        plan["fields"]["trailing_entry_plan_receipt_sha256"] = "e"*64
    if fault == "outer_hash_absent":
        plan["fields"].pop("trailing_entry_plan_receipt_sha256")
    event = dict(stage="pre_submit_delay_committed", stock_code="005930", emitted_date=DAY, fields=commit)
    quote = dict(delay_intent_id="intent", decision_source_sha256=commit["decision_source_sha256"],
        target_delay_sec=180, actual_offset_sec=180, quote_observed_at_epoch=known+180,
        quote_transport_epoch=7, route=commit["route"], quote_route=commit["route"],
        ask_price=90, best_bid=89, ask_qty=5, ws_last_0d_epoch=known+179.8,
        quote_valid=True, quote_consistency_state="single_source", route_depth_source_sha256="a"*64)
    if fault == "stale_quote":
        quote["ws_last_0d_epoch"] = known+170
    quote["quote_source_sha256"] = owner.quote_source_sha256(quote)
    if fault == "quote_hash":
        quote["quote_source_sha256"] = "f"*64
    observation = dict(event, stage="pre_submit_delay_quote_observed", fields=quote)
    rows, quotes, _, _ = review._timing_opportunities([(event, {}), (plan, {}), (observation, {"offset": 99})])
    assert len(rows) == 1
    assert rows[0]["record_id"] == ("7" if fault in (None, "outer_hash_absent", "quote_hash", "stale_quote") else None)
    assert rows[0]["modeled_fill"] is None
    # The native delay sampler remains useful after the trailing observer has
    # stopped. Preserve its actual timestamp and reject bad source/plan links.
    if fault in (None, "outer_hash_absent"):
        assert quotes["7"][0]["ask"] == 90
        assert quotes["7"][0]["known_at"] == known+180
        assert quotes["7"][0]["source"] == {"offset": 99}
    else:
        assert not quotes


def test_execution_source_invalidated_mid_read_discards_partial_day(tmp_path, monkeypatch):
    from src.engine.automation import main_trailing_source_store as native
    index = tmp_path/"report/main_trailing_source_index/2026-10-20/pipeline_events.sqlite"
    index.parent.mkdir(parents=True)
    index.touch()
    monkeypatch.setattr(native, "generation", lambda *a: {"sha256": "a"*64})
    def changed(*args, **kwargs):
        yield {"row": {"stage": "order_leg_sent"}}, {}
        raise native.InputPending("trailing_index_source_generation_changed")
    monkeypatch.setattr(native, "read_rows", changed)
    rows, receipt = review._execution_sources(tmp_path, ["2026-10-20"])
    assert not rows
    assert receipt["gaps"][0]["reason"] == "trailing_index_source_generation_changed"


def test_execution_source_record_budget_does_not_publish_partial_census(tmp_path, monkeypatch):
    from src.engine.automation import main_trailing_source_store as native
    index = tmp_path/"report/main_trailing_source_index/2026-10-20/pipeline_events.sqlite"
    index.parent.mkdir(parents=True)
    index.touch()
    monkeypatch.setattr(review, "MAX_COMPACT_RECORDS", 0)
    monkeypatch.setattr(native, "generation", lambda *a: {"sha256": "a"*64})
    monkeypatch.setattr(native, "read_rows", lambda *a, **k: iter([
        ({"row": {"stage": "order_leg_sent"}}, {})]))
    with pytest.raises(ValueError, match="execution_source_budget_exceeded"):
        review._execution_sources(tmp_path, ["2026-10-20"])


def test_fill_snapshot_never_reads_oversized_history(tmp_path, monkeypatch):
    path = tmp_path/"report/monitor_snapshots/trade_review_2026-10-20.json"
    path.parent.mkdir(parents=True)
    with path.open("wb") as stream:
        stream.truncate(17*1024*1024)
    original = Path.open
    def guarded(p, *a, **kw):
        assert p != path, "oversized historical source was opened"
        return original(p, *a, **kw)
    monkeypatch.setattr(Path, "open", guarded)
    fills, receipt = review._snapshot_fills(tmp_path, ["2026-10-20"])
    assert not fills
    assert receipt["gaps"][0]["reason"] == "fill_snapshot_requires_native_projection"


def test_native_fill_reader_reuses_producer_tree_without_raw_or_quote_copy(tmp_path, monkeypatch):
    from src.tests.test_strategy_position_performance_report import _native_fact_projection
    day, raw = _native_fact_projection(tmp_path, monkeypatch, large=False)
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert path not in {raw, raw.with_suffix(".completed_projection.json")}
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    rows, source = review._native_fill_rows(tmp_path, day)
    assert rows
    assert source["source_kind"] == "native_completed_fill_fields"
    assert source["path"].startswith(str(tmp_path))
    assert rows[0]["buy_time"] == day + " 09:00:00"


def test_native_fill_plain_fact_is_bound_by_dependency_not_self_seal(tmp_path, monkeypatch):
    from src.tests.test_strategy_position_performance_report import _native_fact_projection
    from src.engine.lifecycle.holding_window_generation import byte_generation
    day, raw = _native_fact_projection(tmp_path, monkeypatch, large=False)
    dependency_path = raw.with_suffix(".completed_projection.json.dependencies.json")
    dependency = json.loads(dependency_path.read_bytes())
    fact = raw.with_suffix(".fact_projection.json")
    fact.write_bytes(storage.encoded(dict(date=day, snapshot_identity=dependency["snapshot_identity"],
        sections={"completed_trade_projection": [{"id": 1, "buy_time": day+" 09:00:00"}]})))
    dependency["fact_projection"] = byte_generation(fact)
    dependency["artifact_sha256"] = initial.digest({k: v for k,v in dependency.items() if k != "artifact_sha256"})
    dependency_path.write_bytes(storage.encoded(dependency))
    rows, _ = review._native_fill_rows(tmp_path, day)
    assert rows[0]["buy_time"] == day+" 09:00:00"
    fact.write_bytes(fact.read_bytes()+b" ")
    with pytest.raises(ValueError, match="native_fill_fact_changed"):
        review._native_fill_rows(tmp_path, day)


def test_native_fill_reader_rejects_changed_snapshot_epoch(tmp_path, monkeypatch):
    from src.tests.test_strategy_position_performance_report import _native_fact_projection
    day, raw = _native_fact_projection(tmp_path, monkeypatch, large=False)
    raw.write_bytes(raw.read_bytes()+b" ")
    with pytest.raises(ValueError, match="source_binding_invalid"):
        review._native_fill_rows(tmp_path, day)


def test_fill_clock_is_not_replaced_by_position_update_clock():
    trade, fill, orders = _actual_fill()
    trade["buy_time"] = fill["position_buy_time"] = "2026-10-20T09:25:33"
    result = review._fill_path(trade, fill, [], orders)
    assert result["anchors"][1]["at"] == review._epoch("2026-10-20T09:25:34")
    assert result["recorded_buy_time"] == "2026-10-20T09:25:33"


def test_old_position_generation_does_not_match_reused_record_id():
    trade, fill, orders = _actual_fill()
    fill["position_buy_time"] = "2026-10-19T09:25:34"
    result = review._fill_path(trade, fill, [], orders)
    assert result["anchor_status"] == "position_generation_or_scale_in_conflict"


def test_projection_pools_only_verified_alias_equivalence_and_retains_captured_hashes(tmp_path, monkeypatch):
    from copy import deepcopy
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import reversal_auxiliary_registry as registry
    records, originals = [], []
    for alias in ("f6", "f7"):
        schema = {"format": {"schema": {"properties": {"fact": {"type": "string", "enum": [alias]}}}}}
        proof = registry.provider_identity(dict(instructions="Same prompt", model="gpt-5.4-nano", text=schema),
            dict(policy_version="continuous_reversal_policy_v6", registry_sha256="c"*64))
        proof["semantic"]["response_contract"] = deepcopy(schema)
        proof["identity_sha256"] = initial.digest(proof["semantic"])
        originals.append(proof["identity_sha256"])
        records.append(dict(prices={0: 10000, 30: 9900}, commit_overrides=dict(
            original_evaluation_attempt_id="native-"+alias,
            entry_mechanistic_policy_sha256="a"*64,
            entry_ai_soft_policy_sha256=proof["identity_sha256"],
            entry_auxiliary_policy_identity_version=proof["schema"],
            entry_auxiliary_policy_identity=json.dumps(proof))))
    _price_pattern_fixture(tmp_path, monkeypatch, records)
    path = next(tmp_path.glob("threshold_cycle/date=*/family=pre_submit_delay/*.jsonl"))
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    projected, _ = initial.project_rows(rows)
    assert len(projected) == 2
    assert projected[0]["parent_compatibility"] == projected[1]["parent_compatibility"]
    assert [r["captured_parent_compatibility"][1] for r in projected] == originals


def test_tampered_projection_shard_rejected_and_complete_report_not_written(tmp_path):
    data, base, report, _ = _committed(tmp_path)
    path = base / report["qualified_projection_ref"]["path"]
    path.write_text("{}")
    with pytest.raises(ValueError, match="research_shard_generation_changed"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review/report.json").exists()


def test_bounds_and_output_source_overlap_fail_before_writing_complete_report(tmp_path, monkeypatch):
    data, base, _, _ = _committed(tmp_path)
    with pytest.raises(ValueError, match="overlaps_policy_source"):
        review.generate(data, "2026-10-16", base / "review")
    monkeypatch.setattr(review, "MAX_ANCHORS", 3)
    with pytest.raises(ValueError, match="evidence_count_or_budget_invalid"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review").exists()


def test_compact_enrichment_checks_exact_receipt_and_never_reads_unlisted_sources(tmp_path):
    data, _, _, _ = _committed(tmp_path)
    # Direct compact-index test avoids manufacturing a new committed selection.
    from src.engine.lifecycle.holding_window_generation import byte_generation
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    path.write_text('{"changed": true}\n')
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)


def test_same_target_output_is_immutable_and_reproducible(tmp_path):
    data, _, _, _ = _committed(tmp_path)
    output = tmp_path / "review"
    first = review.generate(data, "2026-10-16", output)
    assert first == review.generate(data, "2026-10-16", output)
    broken = json.loads((output / "report.json").read_bytes())
    broken["source_date"] = "2026-10-15"
    (output / "report.json").write_bytes(storage.encoded(broken))
    with pytest.raises(ValueError, match="immutable_report_conflict"):
        review.generate(data, "2026-10-16", output)


def test_native_identity_conflict_cannot_fabricate_an_independent_opportunity():
    row = dict(native_evaluation_bound=True, alias=["2026-10-16", "005930", "intent"],
               original_machine_observation_sha256="a"*64, native_evaluation_attempt_id="native",
               parent_compatibility=["b"*64, "c"*64], independent_opportunity_sha256="d"*64)
    with pytest.raises(ValueError, match="independent_identity_mismatch"):
        review._independent_identity(row)
    row["native_evaluation_bound"] = False
    assert review._independent_identity(row) is None


def test_compact_budget_is_explicitly_unavailable_without_opening_large_source(tmp_path):
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-large.jsonl"
    report = {"source_receipt": {"partition_generations": {
        str(path): {"size": review.MAX_COMPACT_BYTES + 1, "sha256": "a"*64}}}}
    with storage.index(tmp_path / "index") as db:
        result = review._compact_index(db, data, report)
    assert result["status"] == "unavailable"
    assert result["reason"] == "receipt_bound_compact_budget_exceeded"
    assert result["bytes_read"] == result["records_decoded"] == 0


def test_identified_bad_compact_rows_do_not_hide_an_exact_native_identity(tmp_path):
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.pipeline_event_summary import execution_projection_identity
    from src.engine.scalping import pre_submit_delay_tuning as owner
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    fields = dict(delay_intent_id="intent", original_machine_observation_sha256="a"*64,
                  evaluation_attempt_id="native")
    fields["decision_source_sha256"] = owner.decision_source_sha256(fields)
    event = dict(family="pre_submit_delay", emitted_date="2026-10-16", stock_code="005930",
                 stage="pre_submit_delay_committed", fields=fields)
    event["execution_source_event_sha256"] = execution_projection_identity(event)
    path.write_bytes(b'\xff\n[]\n{"broken":NaN}\n' + storage.encoded(event) + b"\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {
        str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    original = dict(alias=["2026-10-16", "005930", "intent"], p0_valid=False,
                    native_evaluation_bound=True, decision_source_sha256=fields["decision_source_sha256"])
    with storage.index(tmp_path / "index") as db:
        receipt = review._compact_index(db, data, report)
        enriched = review._enrich(db, original, receipt)
    assert receipt["status"] == "complete"
    assert receipt["malformed_records"] == 2
    assert receipt["invalid_event_identity_n"] == 1
    assert receipt["bound_projection_anchors"] == 1
    assert enriched["native_evaluation_attempt_id"] == "native"
    assert "native_evaluation_attempt_id" not in original


def test_declared_small_but_grown_compact_fails_before_any_source_read(tmp_path, monkeypatch):
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    with path.open("wb") as handle:
        handle.truncate(256 * 1024 * 1024)
    report = {"source_receipt": {"partition_generations": {str(path): {"size": 3, "sha256": "a"*64}}}}
    original_open = Path.open
    def checked_open(target, *args, **kwargs):
        if target == path:
            pytest.fail("grown compact source was opened before its size was checked")
        return original_open(target, *args, **kwargs)
    monkeypatch.setattr(Path, "open", checked_open)
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)


def test_compact_append_during_stream_is_bounded_and_rejected(tmp_path, monkeypatch):
    import io
    from src.engine.lifecycle.holding_window_generation import byte_generation
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    original_open = Path.open
    class AppendingReader(io.BufferedReader):
        def readline(self, size=-1):
            raw = super().readline(size)
            if raw:
                with original_open(path, "ab") as writer:
                    writer.write(b"{}\n")
            return raw
    def wrapped_open(target, *args, **kwargs):
        if target == path and args and args[0] == "rb":
            return AppendingReader(io.FileIO(path, "rb"))
        return original_open(target, *args, **kwargs)
    monkeypatch.setattr(Path, "open", wrapped_open)
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)
    assert path.stat().st_size <= 9


@pytest.mark.parametrize("anchor,child_delay,expected_research,expected_lookup", [
    ("price_ready", 0, 0, 0), ("price_ready", None, 30, 30), ("signal_ready", None, 30, 0),
])
def test_exact_parent_fallback_preserves_explicit_zero_and_runtime_anchor_scope(
        tmp_path, anchor, child_delay, expected_research, expected_lookup):
    parents = ["a"*64, "b"*64]
    parent_key = initial.cell_key(anchor, "REGULAR", parents=parents)
    child_key = initial.cell_key(anchor, "REGULAR", "situation", parents=parents)
    parent = dict(anchor_kind=anchor, session="REGULAR", parent_compatibility=parents,
                  delay_sec=30, runtime_apply_allowed=True)
    child = {**parent, "delay_sec": child_delay, "runtime_apply_allowed": child_delay is not None}
    item = dict(key=child_key, value=child)
    with storage.index(tmp_path / "index") as db:
        storage.put(db, "cell:" + parent_key, dict(key=parent_key, value=parent))
        storage.put(db, "cell:" + child_key, item)
        result = review._fallback(db, item, "price_ready")
    assert result["research_cell_or_parent_delay_sec"] == expected_research
    assert result["prepared_policy_lookup_delay_sec"] == expected_lookup
    assert result["resolved_cell_key"] == (child_key if child_delay is not None else parent_key)


def test_durable_output_budget_prevents_complete_report_publication(tmp_path, monkeypatch):
    data, _, _, _ = _committed(tmp_path)
    monkeypatch.setattr(review, "MAX_DURABLE_BYTES", 1)
    with pytest.raises(ValueError, match="research_combined_disk_budget_exceeded"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review/report.json").exists()
