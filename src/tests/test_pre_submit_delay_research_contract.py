"""Research clocks and lineage cannot widen the executable delay contract."""

import copy
from datetime import datetime

import pytest

from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.engine.scalping import pre_submit_delay_tuning as owner


def receipts(*, p0_offset=0.0):
    at = datetime.fromisoformat("2026-10-16T09:00:00+09:00").timestamp()
    commit = dict(
        delay_intent_id="original-intent",
        decision_committed_at_epoch=at,
        anchor_kind="price_ready",
        anchor_contract_version=2,
        route="KRX_NXT_INTEGRATED",
        quote_transport_epoch=7,
        delay_policy_sha256=None,
        owner="main_scalping",
        planned_qty=10,
        original_machine_observation_sha256="a" * 64,
        market_session_bucket="KRX_REGULAR",
        entry_action="ENTER_NOW",
        auxiliary_effective_action="PASS",
        evaluation_attempt_id="native-attempt",
        request_id="native-request",
        entry_mechanistic_policy_sha256="b" * 64,
        entry_ai_soft_policy_sha256="c" * 64,
        observation_grid_version=owner.OBSERVATION_GRID_VERSION,
        observation_horizons_sec=list(owner.OBSERVATION_HORIZONS),
        observation_tolerance_sec=owner.SHORT_OBSERVATION_TOLERANCE_SEC,
    )
    commit["decision_source_sha256"] = owner.decision_source_sha256(commit)

    def quote(target, offset=None):
        offset = target if offset is None else offset
        value = dict(
            delay_intent_id=commit["delay_intent_id"],
            decision_source_sha256=commit["decision_source_sha256"],
            target_delay_sec=target,
            actual_offset_sec=offset,
            quote_observed_at_epoch=at + offset,
            route=commit["route"],
            quote_route=commit["route"],
            quote_transport_epoch=7,
            ask_price=10000 - target,
            best_bid=9990 - target,
            ask_qty=20,
            ws_last_0d_epoch=at + offset - 0.1,
            quote_consistency_state="single_source",
            quote_valid=True,
            quote_source_reason="valid",
            route_depth_source_sha256="d" * 64,
        )
        if target in owner.SHORT_RESEARCH_HORIZONS:
            value.update(
                quote_contract_version=2,
                observation_grid_version=owner.OBSERVATION_GRID_VERSION,
                observation_tolerance_sec=0.25,
                target_due_at_epoch=at + target,
            )
        value["quote_source_sha256"] = owner.quote_source_sha256(value)
        return value

    def row(stage, fields):
        return dict(
            emitted_date="2026-10-16", stock_code="005930", stage=stage, fields=fields
        )

    rows = [
        row("pre_submit_delay_committed", commit),
        row("pre_submit_delay_quote_observed", quote(0, p0_offset)),
    ]
    return commit, quote, row, rows


def test_legacy_hashes_and_policy_grid_preserved():
    fields = {"target_delay_sec": 30, "ask_price": 10000}
    assert owner.quote_source_sha256(fields) == owner._digest(
        {key: str(fields.get(key)) for key in owner._QUOTE_SOURCE_KEYS}
    )
    assert initial.HORIZONS == (0, 30, 60, 120, 180)
    assert owner.observation_horizons({}) == initial.HORIZONS


@pytest.mark.parametrize(
    "target,offset,valid", [(1, 3.2, False), (3, 3.2, True), (5, 3.2, False)]
)
def test_short_clock_cannot_relabel_one_late_snapshot(target, offset, valid):
    commit, quote, _, _ = receipts()
    assert (owner._quote_source_issue(commit, quote(target, offset)) is None) is valid


def test_grid_and_quote_clock_metadata_are_bound_to_source_hashes():
    commit, quote, _, _ = receipts()
    original = commit["decision_source_sha256"]
    changed = copy.deepcopy(commit)
    changed["observation_tolerance_sec"] = 3
    assert owner.decision_source_sha256(changed) != original
    assert owner.observation_horizons(changed) is None
    value = quote(1)
    value["target_due_at_epoch"] += 0.1
    assert owner._quote_source_issue(commit, value) is not None
    value["quote_source_sha256"] = owner.quote_source_sha256(value)
    assert (
        owner._quote_source_issue(commit, value) == "quote_observation_contract_invalid"
    )


def test_short_pairs_are_diagnostic_and_require_a_timely_baseline():
    _, quote, row, rows = receipts()
    rows.extend(row("pre_submit_delay_quote_observed", quote(t)) for t in (1, 3, 5, 30))
    projected, _ = initial.project_rows(rows)
    assert set(projected[0]["pairs"]) == {30}
    assert set(projected[0]["research_short_pairs"]) == {1, 3, 5}
    assert projected[0]["independent_opportunity_sha256"]
    assert projected[0]["execution_features"]["p0_ask"] == 10000
    _, quote, row, rows = receipts(p0_offset=1)
    rows.extend(row("pre_submit_delay_quote_observed", quote(t)) for t in (1, 3, 5, 30))
    projected, _ = initial.project_rows(rows)
    assert set(projected[0]["pairs"]) == {30}
    assert projected[0]["research_short_pairs"] == {}
    assert projected[0]["research_short_p0_valid"] is False


def test_native_reference_projection_is_bound_and_never_backfilled():
    commit, quote, row, _ = receipts()
    commit.update(
        signal_reference_contract_version="native_confirmation_price_v1",
        original_signal_reference_price=9900,
        original_signal_reference_epoch=commit["decision_committed_at_epoch"] - 1,
        original_signal_id="native-original-signal",
    )
    commit["decision_source_sha256"] = owner.decision_source_sha256(commit)
    rows = [
        row("pre_submit_delay_committed", commit),
        row("pre_submit_delay_quote_observed", quote(0)),
    ]
    projected, _ = initial.project_rows(rows)
    assert projected[0]["execution_features"]["original_signal_reference_price"] == 9900
    commit["original_signal_reference_price"] = 9800
    projected, counts = initial.project_rows(rows)
    assert projected == []
    assert counts["exclusions"]["commit_or_effective_pass_invalid"] == 1


def test_recheck_stage_has_all_producer_and_projection_owners():
    from src.engine.pipeline_event_summary import EXECUTION_SUMMARY_STAGES
    from src.utils.threshold_cycle_registry import THRESHOLD_STAGE_FAMILY_MAP

    stage = "pre_submit_delay_recheck_observed"
    assert stage in owner.SOURCE_STAGES
    assert stage in EXECUTION_SUMMARY_STAGES
    assert THRESHOLD_STAGE_FAMILY_MAP[stage] == owner.FAMILY
    required = {
        "recheck_status",
        "successor_request_id",
        "successor_evaluation_attempt_id",
        "recheck_submitted_at_epoch",
        "recheck_completed_at_epoch",
        "due_at_epoch",
        "terminal_reason",
        "resolved_machine_observation_sha256",
        "entry_submit_attempt_id",
    }
    assert required <= owner._V2_SOURCE_FIELDS


@pytest.mark.parametrize("sharded", [False, True])
def test_sealed_selection_preserves_prior_qualification_contract(
    tmp_path, monkeypatch, sharded
):
    from src.engine.automation import (
        pre_submit_delay_partitioned_research as partitioned,
    )

    _, quote, row, rows = receipts()
    rows.append(row("pre_submit_delay_quote_observed", quote(30)))
    monkeypatch.setattr(initial, "projection_contract", lambda: "e" * 64)
    report, policy = initial.build_initial(
        rows,
        source_date="2026-10-16",
        publication_date="2026-10-17",
        effective_date="2026-10-19",
        source_sha256="a" * 64,
        code_contract_sha256="b" * 64,
    )
    if sharded:
        report, policy = partitioned.build(
            report["qualified_projection"],
            report["census"],
            output_root=tmp_path,
            source_date="2026-10-16",
            publication_date="2026-10-17",
            effective_date="2026-10-19",
            source_sha256="a" * 64,
            code_contract_sha256="b" * 64,
            source_receipt=None,
        )
    before = initial.digest([report, policy])
    assert report["algorithm"] == initial.ALGORITHM
    assert report["mapping_version"] == initial.MAPPING_VERSION
    monkeypatch.setattr(initial, "projection_contract", lambda: "f" * 64)
    initial.validate(policy, report, target_date="2026-10-19")
    assert report["source_projection_contract_sha256"] == "e" * 64
    assert initial.digest([report, policy]) == before
    # Selection verification does not authorize missing original source proof.
    with pytest.raises(ValueError, match="source_window_unverified"):
        initial.verify_source(tmp_path, report)


@pytest.mark.parametrize("value", [None, "", "x" * 64, "e" * 63, True])
def test_frozen_qualification_contract_requires_real_digest(value):
    with pytest.raises(ValueError, match="projection_contract_invalid"):
        initial.frozen_projection_contract({"source_projection_contract_sha256": value})


@pytest.mark.parametrize(
    "accepted,outcome,expected",
    [
        ("True", "returned_true", "broker_ack_execution_terminal_unobserved"),
        ("False", "raised", "response_uncertain"),
        ("False", "returned_false", "no_broker_ack_observed"),
    ],
)
def test_research_events_cannot_become_broker_terminals(
    tmp_path, monkeypatch, accepted, outcome, expected
):
    import json
    from src.engine.pipeline_event_summary import execution_projection_identity
    from src.tests.test_pre_submit_delay_tuning import _delay_fixture

    commit, _ = _delay_fixture(tmp_path, monkeypatch)
    path = (
        tmp_path
        / "threshold_cycle/date=2026-09-23/family=pre_submit_delay/part-execution-test.jsonl"
    )
    base = json.loads(path.read_text().splitlines()[0])
    fields = dict(
        delay_intent_id=commit["delay_intent_id"],
        decision_source_sha256=commit["decision_source_sha256"],
        submit_finished_at_epoch="131.0",
    )
    additions = []
    for stage, extra in (
        (
            "pre_submit_delay_intent_terminal",
            dict(
                submit_call_outcome=outcome,
                submit_call_broker_accepted=accepted,
                terminal_reason=outcome,
            ),
        ),
        (
            "pre_submit_delay_recheck_observed",
            dict(recheck_status="completed", successor_request_id="new-request"),
        ),
        (
            "pre_submit_delay_intent_terminal",
            dict(observation_only=True, terminal_reason="observation_closed"),
        ),
        (
            "pre_submit_delay_quote_observed",
            dict(
                target_delay_sec=1,
                quote_contract_version=2,
                observation_grid_version=owner.OBSERVATION_GRID_VERSION,
            ),
        ),
    ):
        event = dict(base, stage=stage, fields={**fields, **extra})
        event["execution_source_event_sha256"] = execution_projection_identity(event)
        additions.append(event)
    with path.open("a") as handle:
        for event in additions:
            handle.write(json.dumps(event) + "\n")
    report = owner.build_report("2026-09-23", effective_date="2026-09-24", write=False)
    assert report["terminal_status_counts"] == {expected: 1}
    assert report["terminal_observation_count"] == 1
    assert not report["source_quality_counts"].get("terminal_conflict")
    assert not report["source_quality_counts"].get(
        "sample_duplicate_or_horizon_invalid"
    )
