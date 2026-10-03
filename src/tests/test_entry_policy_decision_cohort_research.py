from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from src.engine.scalping import entry_policy_decision_cohort_research as M
from src.tests.test_entry_policy_confirmation_research import case


def prepared_guard():
    row, parent, prepared, spec = case()
    prepared["decision"] = M.E.mechanistic_entry_policy_decision(prepared["rebuilt"], policy=parent)
    return row, parent, prepared, spec


def test_soft_reason_does_not_hide_other_guards():
    _, _, prepared, _ = prepared_guard()
    prepared["decision"]["action"] = "RECHECK"
    prepared["decision"]["reason"] = "TRIGGER_CONFIRMATION_RECHECK"
    assert M.guard_summary(prepared)["cohort"] == "soft_confirmation_only"
    prepared["decision"]["core_comparison"]["risk_assessments"].append(dict(
        risk_code="STRUCTURE_INVALIDATED", fact_id="hard_blocker:large_sell_print_present", disposition="RECHECKABLE"))
    guard = M.guard_summary(prepared)
    assert guard["cohort"] == "other_guard_or_wait"
    assert any("large_sell_print" in b for b in guard["blockers"])


@pytest.mark.parametrize("damage", ["liquidity", "local", "recipe", "source"])
def test_cohort_preserves_nonconfirmation_guards(damage):
    _, _, p, _ = prepared_guard()
    p["decision"].update(action="RECHECK", reason="TRIGGER_CONFIRMATION_RECHECK")
    if damage == "liquidity":
        p["decision"]["liquidity_threshold_pass"] = False
    if damage == "local":
        p["rebuilt"]["local_breakout"] = dict(recheck_required=True)
    if damage == "recipe":
        p["receipt"]["effective_thresholds"]["micro_confirmation_recipe"] = 1
    if damage == "source":
        p["decision"]["core_comparison"]["risk_assessments"] = [dict(
            risk_code="SOURCE_QUALITY_GAP", fact_id="stale", disposition="BLOCKING")]
    assert M.guard_summary(p)["cohort"] != "soft_confirmation_only"
    assert M.guard_summary(p, provenance=False)["cohort"] == "source_invalid"


def outcome_row():
    return dict(source_date="2026-09-29", effective_venue="KRX", session_bucket="KRX_REGULAR",
        comparison=dict(entry_cost_contract=dict(schema="entry_round_trip_cost_v1", source_date="2026-09-29",
            effective_venue="KRX", session_bucket="KRX_REGULAR", basis="source_bound_estimate",
            source_sha256="a"*64, profile_id="test", components_pct=dict(buy_fee=.015, sell_fee=.015, sell_tax=.2, slippage=.07)),
            conservative_execution_cost_pct=.3), entry_quality_contract_valid=False,
        entry_quality_path=dict(schema="entry_quality_path_v1", conservative_execution_cost_pct=.3,
            cadence_complete=True, first_hit="neither", primary_window_sec=180, label_reason="neither_hit"))


@pytest.mark.parametrize("kind", ["neither", "late_stop", "ambiguous", "cost", "path", "cadence"])
def test_censoring_diagnosis_does_not_create_zero_label_or_cost_gap(kind):
    r = outcome_row()
    p = r["entry_quality_path"]
    if kind == "late_stop":
        p.update(first_hit="exact_stop_first", time_to_exact_stop_sec=400)
    if kind == "ambiguous":
        p["first_hit"] = "same_bar_ambiguous"
    if kind == "cost":
        p["conservative_execution_cost_pct"] = .9
    if kind == "path":
        r["entry_quality_path"] = {}
    if kind == "cadence":
        p["cadence_complete"] = False
    result = M.outcome_diagnosis(r)
    assert result["value"] is None
    assert result["exclusion"] == (
        "quality_path_cost_missing_or_mismatched" if kind in {"cost", "path"}
        else "terminal_path_censored")
    assert result["diagnosis"] == {
        "neither": "neither_boundary_hit", "late_stop": "late_stop_contract_censored",
        "ambiguous": "same_bar_ambiguous", "cost": "path_cost_missing_or_mismatched",
        "path": "path_missing_or_schema_invalid", "cadence": "path_cadence_gap"}[kind]


def small_row(i=0, *, action="RECHECK", value=.1, native=True):
    now = datetime.fromisoformat("2026-09-29T09:10:00+09:00") + timedelta(seconds=i*60)
    identity = ["2026-09-29", "000660", "KRX", "KRX_REGULAR", "p1"] if native else None
    cohort = "parent_enter" if action == "ENTER_NOW" else "soft_confirmation_only"
    return dict(trace=str(i), symbol="000660", day="2026-09-29", ts=now.isoformat(), bundle="a"*64,
        identity=dict(native=identity, watch_origin=None), parent_action=action,
        types=dict(phase="rebound", family="RECOVERY_CONFIRMATION", liquidity_band="SUPPORTIVE"),
        features=dict(spread_bp=float(i+1)), families=["DEPTH_SUPPORTED"], confirming_families=["DEPTH_SUPPORTED"],
        guard=dict(cohort=cohort), outcome=dict(value=value, exclusion=None if value is not None else "terminal_path_censored",
            diagnosis="eligible_target_first" if value is not None and value > 0 else "eligible_stop_first" if value is not None else "neither_boundary_hit"),
        metric=dict(source_date="2026-09-29", stock_code="000660", effective_venue="KRX", session_bucket="KRX_REGULAR",
            scanner_promotion_id="p1", decision_ts=now.isoformat(), decision_trace_id=str(i),
            comparison=dict(incumbent_machine_action=action, conservative_execution_cost_pct=.3)), cost=.3, gross={})


def test_native_metrics_do_not_count_missing_identity_or_censor_as_failure():
    rows = [small_row(0, value=.1), small_row(1, value=None), small_row(2, value=-.5, native=False)]
    metric = M.native_metric(rows, ["ENTER_NOW"]*3)
    assert metric["selected_opportunity_count"] == 1
    assert metric["selected_attempt_count"] == 1
    assert metric["win_rate_pct"] == 100
    assert metric["excluded_attempt_counts"] == {"terminal_path_censored": 1}
    assert M.observation_metric(rows, ["ENTER_NOW"]*3)["losses"] == 1


def test_decisions_do_not_use_labels_and_source_invalid_cannot_recover():
    rows = [small_row(), small_row(1, value=None)]
    spec = dict(mode="recovery", flow_family="DEPTH_SUPPORTED", condition=[])
    actions = M.vector(rows, spec)
    assert actions == ["ENTER_NOW"]*2
    rows[0]["outcome"] = {"value": -999, "exclusion": "fake_future"}
    assert M.vector(rows, spec) == actions
    rows[0]["guard"]["cohort"] = "source_invalid"
    assert M.vector(rows, spec)[0] == "RECHECK"


def test_veto_changes_unlabelled_rows_and_reports_coverage_risk():
    rows = [small_row(0, action="ENTER_NOW", value=None)]
    actions = M.vector(rows, dict(mode="veto", condition=[]))
    assert actions == ["RECHECK"]
    assert M.native_metric(rows, actions)["unevaluated_existing_entry_changes"] == ["0"]


def test_training_conditions_are_partitioned_and_outcome_independent():
    rows = [small_row(i) for i in range(4)]
    before = M.conditions(rows)
    rows[0]["outcome"]["value"] = -999
    assert M.conditions(rows) == before
    rows[0]["symbol"] = "005930"
    with pytest.raises(ValueError, match="samsung_leak"):
        M.conditions(rows)
    with pytest.raises(ValueError, match="samsung_leak"):
        M.fit(rows, "veto")


@pytest.mark.parametrize("damage", ["signal", "native", "phase", "guard"])
def test_repeat_resets_on_all_observed_invalid_intermediate_rows(damage):
    rows = [small_row(i) for i in range(4)]
    signals = [True]*4
    if damage == "signal":
        signals[1] = False
    if damage == "native":
        rows[1]["identity"]["native"] = None
    if damage == "phase":
        rows[1]["types"]["phase"] = "other"
    if damage == "guard":
        rows[1]["guard"]["cohort"] = "other_guard_or_wait"
    assert M.repeat_signals(rows, signals, 120) == [False, False, False, True]
    assert M.repeat_signals(rows, signals, 59) == [False]*4


def test_timing_uses_parent_entries_even_without_economic_labels():
    rows = [small_row(0, action="ENTER_NOW", value=None), small_row(1),
            small_row(2, action="ENTER_NOW", value=None)]
    ledger = M.changed_ledger(rows, ["ENTER_NOW"]*3)
    assert len(ledger) == 1
    assert ledger[0]["earlier_parent_enter_sec"] == 60
    assert ledger[0]["later_parent_enter_sec"] == 60
    assert ledger[0]["actual_fill_or_holdings_proven"] is False


def test_output_boundary_precedes_read_or_write(tmp_path):
    with pytest.raises(ValueError, match="workspace_tmp"):
        M.prepare_source(tmp_path, tmp_path / "data/policy")
    out = tmp_path / "tmp/existing"
    out.mkdir(parents=True)
    (out / "projection.json").write_text("existing")
    with pytest.raises(ValueError, match="not_empty"):
        M.prepare_source(tmp_path, out)
    assert (out / "projection.json").read_text() == "existing"


def test_fast_prepare_reuses_exact_decision_receipt(monkeypatch):
    _, parent, p, _ = case()
    p["receipt"]["effective_thresholds"].update(p["effective"]["thresholds"])
    decision = dict(p["decision"], effective_setup_evidence=p["rebuilt"], strategy_selection=p["receipt"])
    monkeypatch.setattr(M.E, "mechanistic_entry_policy_decision", lambda *a, **k: deepcopy(decision))
    actual = M.fast_prepare({"setup_evidence": {}}, parent)
    assert actual["rebuilt"] == p["rebuilt"]
    assert actual["effective"]["thresholds"] == p["effective"]["thresholds"]


def test_winrate_objective_allows_lost_successes_without_imputing_unknown_outcomes():
    baseline = dict(selected_opportunity_count=10, win_rate_pct=80)
    metric = dict(selected_opportunity_count=8, win_rate_pct=90, paired_admission_delta_pct=.01,
        existing_success_retention_rate_pct=90, unevaluated_existing_entry_changes=[])
    assert M.qualify(metric, baseline, "veto")
    metric["existing_success_retention_rate_pct"] = 100
    assert M.qualify(metric, baseline, "veto")
    metric["unevaluated_existing_entry_changes"] = ["censored"]
    assert M.qualify(metric, baseline, "veto")
    metric["win_rate_pct"] = 80
    assert not M.qualify(metric, baseline, "veto")
    metric["win_rate_pct"] = 79
    assert not M.qualify(metric, baseline, "veto")


def test_missing_native_id_keeps_lost_winner_in_separate_observation_diagnostic(monkeypatch):
    rows = [small_row(0, action="ENTER_NOW", value=-.8), small_row(1, action="ENTER_NOW", value=.1),
            small_row(2, action="ENTER_NOW", value=.1, native=False)]
    rows[0]["metric"]["scanner_promotion_id"] = "bad"
    rows[0]["identity"]["native"][-1] = "bad"
    for r, value in zip(rows, (1, 5, 1), strict=True):
        r["features"]["spread_bp"] = value
    spec = dict(id="veto", mode="veto", condition=[dict(kind="numeric", key="spread_bp", boundary=2, side="lt")])
    monkeypatch.setattr(M, "definitions", lambda *args: [spec])
    actions = M.vector(rows, spec)
    assert M.qualify(M.native_metric(rows, actions), M.native_metric(rows, ["ENTER_NOW"]*3), "veto")
    assert M.observation_metric(rows, actions)["existing_success_retention_rate_pct"] == 50
    result = M.fit(rows, "veto")
    assert result["selected"] == spec
    assert result["candidate_metrics"][0]["observations"]["existing_success_retention_rate_pct"] == 50


@pytest.mark.parametrize("damage", ["none", "selection", "extraction", "snapshot", "dependency"])
def test_cached_raw_replay_reuse_rejects_nonselection_changes(tmp_path, monkeypatch, damage):
    from pathlib import Path
    original = Path(M.__file__).read_text()
    old = original.replace('metric["win_rate_pct"] > baseline["win_rate_pct"]',
        'metric["win_rate_pct"] >= baseline["win_rate_pct"]') if damage == "selection" else original
    if damage == "extraction":
        old = old.replace('"raw_provenance_unverified"', '"raw_provenance_replaced"')
    snapshot = tmp_path / "reviewed-research-code.py"
    snapshot.write_text(old)
    manifests = M.kernel_manifest()
    manifests[str(Path(M.__file__).resolve())] = M.P.file_sha(snapshot)
    if damage == "dependency":
        manifests[str(Path(M.E.__file__).resolve())] = "f"*64
    frozen = dict(kernel_manifest=manifests)
    if damage == "snapshot":
        snapshot.write_text(old + "\n# changed after hash\n")
    if damage in {"extraction", "snapshot", "dependency"}:
        with pytest.raises(ValueError, match="prepared_|preparation_code"):
            M.checked_preparation(frozen, tmp_path / "projection.json")
    else:
        assert M.checked_preparation(frozen, tmp_path / "projection.json") == M.kernel_manifest()
