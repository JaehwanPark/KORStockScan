import json
from pathlib import Path

import pytest

from src.engine.monitoring import scalping_avg_down_recovery_calibration as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
        },
    )


def _write_event(path: Path, *, stage: str, emitted_at: str, **fields):
    payload = {"stage": stage, "emitted_at": emitted_at, "fields": fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _route_arm(
    *,
    should_add: bool,
    signature: str,
    price: int = 0,
    qty: int = 0,
    method: str = mod.FIXED_EXIT_METHOD,
):
    return {
        "should_add": should_add,
        "selected_route": "shallow_volatility_avg_down" if should_add else "NO_ADD",
        "action_reason": "shallow_volatility_avg_down" if should_add else "blocked",
        "behavior_signature": signature,
        "proposed_add_price": price,
        "proposed_add_qty": qty,
        "price_allowed": should_add,
        "sizing_status": (
            "existing_sizing_owner_observed" if should_add else "not_applicable_no_add"
        ),
        "route_evaluation_complete": True,
        "exit_replay_method": method,
    }


def _write_exact_episode(
    path: Path,
    *,
    index: int,
    venue: str,
    event_date: str = "2026-07-10",
    policy_version: str = "policy-v2",
    terminal_path: Path | None = None,
    source_authority: str = mod.SOURCE_ONLY_AUTHORITY,
    paired_ready: bool = False,
    source_event_id: str | None = None,
    decision_id: str | None = None,
    candidate_qty: int = 1,
    candidate_sell_price: int = 110,
    observed_sell_price: int | None = None,
    include_paired_outcomes: bool = True,
    paired_terminal_id_namespace: str | None = None,
):
    minute = 9 * 60 + index
    decision_time = f"{event_date}T{minute // 60:02d}:{minute % 60:02d}:00+09:00"
    terminal_minute = minute + 10
    terminal_time = (
        f"{event_date}T{terminal_minute // 60:02d}:"
        f"{terminal_minute % 60:02d}:00+09:00"
    )
    episode_id = f"mlc-{index:032x}"
    paired_id_namespace = paired_terminal_id_namespace or str(index)
    # Production observations never predict the method of a future replay.
    method = mod.FIXED_EXIT_METHOD
    route_replay = {
        "80": _route_arm(
            should_add=True,
            signature=f"candidate-add-{index}",
            price=100,
            qty=candidate_qty,
            method=method,
        ),
        "85": _route_arm(
            should_add=False,
            signature=f"current-no-add-{index}",
            method=method,
        ),
        "90": _route_arm(
            should_add=False,
            signature=f"current-no-add-{index}",
            method=method,
        ),
    }
    _write_event(
        path,
        stage="avg_down_route_arbitration_observed",
        emitted_at=decision_time,
        avg_down_route_schema=mod.ROUTE_EVENT_SCHEMA,
        source_event_id=source_event_id or f"route-event-{index}",
        scale_in_decision_id=decision_id or f"route-decision-{index}",
        position_episode_id=episode_id,
        stock_code=f"{100000 + index:06d}",
        venue=venue,
        session="krx_regular" if venue == "KRX" else "nxt_day",
        configured_min_buy_pressure=85.0,
        effective_min_buy_pressure=85.0,
        runtime_value_source="runtime_rules_loaded_value",
        runtime_candidate_quality_update_id="baseline_no_selected_candidate",
        runtime_candidate_evidence_contract_version="baseline_no_selected_candidate",
        runtime_candidate_evidence_digest="baseline_no_selected_candidate",
        runtime_candidate_selected=False,
        runtime_env_written=False,
        runtime_pid_value_verified=True,
        runtime_natural_match=False,
        runtime_attribution_state="no_selected_candidate_observation",
        pre_add_buy_price=100,
        pre_add_buy_qty=10,
        route_replay=route_replay,
        avg_down_policy_version=policy_version,
        sizing_policy_version="sizing-v1",
        cost_policy_version="trade_profit_net_realized_pnl:rate=0.00230000",
        evidence_authority=mod.SOURCE_ONLY_AUTHORITY,
        exit_replay_feasibility="requires_paired_exit_replay",
    )
    _write_event(
        terminal_path or path,
        stage="avg_down_route_arbitration_terminal",
        emitted_at=terminal_time,
        position_episode_id=episode_id,
        scale_in_decision_id=decision_id or f"route-decision-{index}",
        source_observation_id=source_event_id or f"route-event-{index}",
        stock_code=f"{100000 + index:06d}",
        venue=venue,
        avg_down_policy_version=policy_version,
        sizing_policy_version="sizing-v1",
        cost_policy_version="trade_profit_net_realized_pnl:rate=0.00230000",
        terminal_status="COMPLETED",
        sell_price=(
            candidate_sell_price if observed_sell_price is None else observed_sell_price
        ),
        evidence_authority=source_authority,
        paired_exit_replay=(
            {
                "80": {
                    "status": "COMPLETED",
                    "exit_price": candidate_sell_price,
                    "terminal_source_event_id": (
                        f"paired-terminal-{paired_id_namespace}-80"
                    ),
                    "exit_policy_version": "existing-exit-policy-v1",
                    "evaluation_method": mod.PAIRED_EXIT_METHOD,
                    "evidence_authority": mod.RUNTIME_AUTHORITY,
                },
                "85": {
                    "status": "COMPLETED",
                    "exit_price": 100,
                    "terminal_source_event_id": (
                        f"paired-terminal-{paired_id_namespace}-85"
                    ),
                    "exit_policy_version": "existing-exit-policy-v1",
                    "evaluation_method": mod.PAIRED_EXIT_METHOD,
                    "evidence_authority": mod.RUNTIME_AUTHORITY,
                },
                "90": {
                    "status": "COMPLETED",
                    "exit_price": 100,
                    "terminal_source_event_id": (
                        f"paired-terminal-{paired_id_namespace}-90"
                    ),
                    "exit_policy_version": "existing-exit-policy-v1",
                    "evaluation_method": mod.PAIRED_EXIT_METHOD,
                    "evidence_authority": mod.RUNTIME_AUTHORITY,
                },
                "NO_ADD": {
                    "status": "COMPLETED",
                    "exit_price": 100,
                    "terminal_source_event_id": (
                        f"paired-terminal-{paired_id_namespace}-no-add"
                    ),
                    "exit_policy_version": "existing-exit-policy-v1",
                    "evaluation_method": mod.PAIRED_EXIT_METHOD,
                    "evidence_authority": mod.RUNTIME_AUTHORITY,
                },
            }
            if paired_ready and include_paired_outcomes
            else {}
        ),
    )


def test_legacy_proxy_rows_are_diagnostic_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    _write_event(
        path,
        stage="scalp_sim_scale_in_candidate_funnel",
        emitted_at="2026-07-10T09:00:00+09:00",
        sim_record_id="legacy-1",
        scale_in_arm="AVG_DOWN",
        scale_in_candidate_funnel_state="eligible",
        profit_rate=-0.5,
    )
    _write_event(
        path,
        stage="scalp_sim_holding_mark",
        emitted_at="2026-07-10T09:00:01+09:00",
        sim_record_id="legacy-1",
        profit_rate=1.0,
    )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert report["schema_version"] == 2
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["calibration_reason"] == (
        "exact_route_contract_missing_or_conflicting_current"
    )
    accounting = candidate["source_metrics"]["decision_accounting"]
    assert accounting["raw_event_count"] == 2
    assert accounting["legacy_proxy_event_count"] == 1
    assert accounting["diagnostics"] == {}
    assert accounting["unique_decision_count"] == 0
    assert accounting["unique_episode_count"] == 0
    assert accounting["terminal_counts"] == {}
    assert accounting["target_date_route_observation_count"] == 0
    assert accounting["same_policy_version_decision_count"] == 0
    assert candidate["current_value_source"] == "runtime_rules_display_only"
    assert candidate["target_env_keys"] == []


def test_fixed_exit_positive_edge_remains_source_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 5 else "NXT",
        )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]
    selected = candidate["source_metrics"]["selected_candidate_economics"]

    assert candidate["calibration_state"] == "hold_runtime_scope"
    assert candidate["calibration_reason"] == "requires_paired_exit_replay"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == [mod.TARGET_ENV_KEY]
    assert candidate["current_value"] == 85.0
    assert candidate["recommended_value"] == 80.0
    assert selected["sample_count"] == 10
    assert selected["unique_complete_episode_count"] == 10
    assert selected["candidate_incremental_net_profit_krw"] > 0
    assert selected["candidate_minus_current_net_profit_krw"] > 0
    assert selected["normal_no_add_incremental_net_profit_krw"] == 0
    assert candidate["evidence_authority"] == mod.SOURCE_ONLY_AUTHORITY


def test_paired_lifecycle_replay_can_emit_only_existing_buy_pressure_axis(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
            observed_sell_price=90,
        )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["calibration_reason"] == "paired_incremental_net_edge_ready"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["target_env_keys"] == [mod.TARGET_ENV_KEY]
    assert candidate["changed_target_env_keys"] == [mod.TARGET_ENV_KEY]
    assert candidate["current_values"] == {mod.TARGET_VALUE_KEY: 85.0}
    assert candidate["recommended_values"] == {mod.TARGET_VALUE_KEY: 80.0}
    assert candidate["bounds"] == mod.BOUNDS
    assert candidate["max_step_per_day"] == 5.0
    assert len(candidate["evidence_digest"]) == 64
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 1
    assert (
        report["runtime_update_contract"]["evidence_digest"]
        == candidate["evidence_digest"]
    )
    selected = candidate["source_metrics"]["selected_candidate_economics"]
    assert selected["evaluation_method"] == mod.PAIRED_EXIT_METHOD
    assert selected["candidate_incremental_net_profit_krw"] > 0


def test_paired_labels_without_independent_terminal_outcomes_cannot_promote(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
            include_paired_outcomes=False,
        )

    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]

    assert candidate["allowed_runtime_apply"] is False
    assert candidate["calibration_reason"] == ("route_economic_coverage_gap")
    accounting = candidate["source_metrics"]["decision_accounting"]
    assert accounting["diagnostics"]["terminal_incomplete_or_untrusted"] == 10


def test_paired_runtime_floor_uses_only_paired_rows_not_fixed_exit_history(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(path, index=index, venue="KRX" if index < 5 else "NXT")
    for index in range(10, 20):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 15 else "NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
        )

    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    paired = candidate["source_metrics"]["paired_runtime_candidate_economics"]

    assert candidate["allowed_runtime_apply"] is True
    assert max(row["sample_count"] for row in paired) == 10


def _mutate_events(path, mutate):
    events = [json.loads(line) for line in path.read_text().splitlines()]
    for event in events:
        mutate(event["stage"], event["fields"])
    path.write_text("".join(json.dumps(event) + "\n" for event in events))


def _paired_ten(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index % 2 else "NXT",
            paired_ready=True,
            source_authority=mod.RUNTIME_AUTHORITY,
        )
    return path


@pytest.mark.parametrize(
    "key,value",
    [
        ("position_episode_id", "mlc-" + "f" * 32),
        ("stock_code", "999999"),
        ("venue", "OTHER"),
        ("avg_down_policy_version", "other-policy"),
        ("sizing_policy_version", "other-sizing"),
        ("cost_policy_version", "other-cost"),
        ("source_observation_id", "other-observation"),
    ],
)
def test_terminal_lineage_mismatch_cannot_promote(tmp_path, monkeypatch, key, value):
    path = _paired_ten(tmp_path, monkeypatch)

    def mutate(stage, fields):
        if stage == "avg_down_route_arbitration_terminal":
            fields[key] = value

    _mutate_events(path, mutate)
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["sample_count"] == 0
    assert candidate["calibration_reason"] == "route_economic_coverage_gap"


def test_fixed_diagnostic_negative_cannot_veto_valid_paired_positive(
    tmp_path, monkeypatch
):
    path = _paired_ten(tmp_path, monkeypatch)
    for index in range(10, 30):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index % 2 else "NXT",
            candidate_sell_price=1,
        )
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["calibration_state"] == "adjust_down"
    assert candidate["condition_feasibility"]["state"] == "bounded_candidate_ready"
    assert (
        candidate["source_metrics"]["candidate_economics"][0][
            "source_quality_adjusted_ev_pct"
        ]
        < 0
    )


def test_zero_increment_no_add_tightening_can_improve_negative_current(
    tmp_path, monkeypatch
):
    path = _paired_ten(tmp_path, monkeypatch)

    def mutate(stage, fields):
        if stage.endswith("_observed"):
            fields["route_replay"]["85"] = _route_arm(
                should_add=True, signature="bad-add", price=100, qty=1
            )
            fields["route_replay"]["90"] = _route_arm(
                should_add=False, signature="no-add"
            )
        else:
            fields["paired_exit_replay"]["80"]["exit_price"] = 90
            fields["paired_exit_replay"]["85"]["exit_price"] = 90

    _mutate_events(path, mutate)
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["calibration_state"] == "adjust_up"
    selected = candidate["source_metrics"]["selected_candidate_economics"]
    assert selected["source_quality_adjusted_ev_pct"] == 0
    assert selected["candidate_minus_current_ev_pct"] > 0


@pytest.mark.parametrize("missing", ["quantity", "price_permission", "downstream"])
def test_missing_route_coverage_is_not_no_effect(tmp_path, monkeypatch, missing):
    path = _paired_ten(tmp_path, monkeypatch)

    def mutate(stage, fields):
        if stage.endswith("_observed"):
            arm = fields["route_replay"]["80"]
            if missing == "quantity":
                arm["proposed_add_qty"] = 0
            elif missing == "price_permission":
                arm["price_allowed"] = False
            else:
                arm["route_evaluation_complete"] = False

    _mutate_events(path, mutate)
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["calibration_reason"] == "route_economic_coverage_gap"
    assert candidate["source_metrics"]["coverage_gap"] is True


def test_reused_paired_terminal_source_ids_cannot_promote(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
            paired_terminal_id_namespace="reused",
        )

    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]

    assert candidate["allowed_runtime_apply"] is False
    assert candidate["calibration_reason"] == "requires_paired_exit_replay"


def test_complete_paired_negative_edge_does_not_recommend_fixed_exit_winner(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
            candidate_sell_price=90,
        )

    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]

    assert candidate["allowed_runtime_apply"] is False
    assert candidate["recommended_value"] == candidate["current_value"]
    assert candidate["target_env_keys"] == []


def test_duplicate_and_conflicting_source_ids_do_not_inflate_sample(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    _write_exact_episode(path, index=0, venue="KRX", source_event_id="same-id")
    original = path.read_text(encoding="utf-8").splitlines()[0]
    with path.open("a", encoding="utf-8") as handle:
        handle.write(original + "\n")
    _write_exact_episode(
        path,
        index=1,
        venue="NXT",
        source_event_id="same-id",
        candidate_sell_price=120,
    )

    report = mod.build_report("2026-07-10")
    accounting = report["calibration_candidates"][0]["source_metrics"][
        "decision_accounting"
    ]

    assert accounting["unique_decision_count"] == 0
    assert accounting["diagnostics"]["duplicate_event_count"] == 1
    assert accounting["diagnostics"]["conflicting_duplicate_event_count"] == 1


def test_conflicting_decision_id_excludes_every_variant(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    _write_exact_episode(
        path,
        index=0,
        venue="KRX",
        source_event_id="source-a",
        decision_id="same-decision",
    )
    _write_exact_episode(
        path,
        index=1,
        venue="NXT",
        source_event_id="source-b",
        decision_id="same-decision",
    )

    report = mod.build_report("2026-07-10")
    accounting = report["calibration_candidates"][0]["source_metrics"][
        "decision_accounting"
    ]

    assert accounting["unique_decision_count"] == 0
    assert accounting["diagnostics"]["conflicting_decision_count"] == 1


def test_source_quality_blocked_date_is_excluded(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    _write_exact_episode(path, index=0, venue="KRX")
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "required_field_missing",
        },
    )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["input"] == []
    assert report["source_quality"]["source_quality_excluded_dates"]
    assert candidate["calibration_reason"] == "source_pipeline_events_missing"
    assert candidate["allowed_runtime_apply"] is False


def test_late_sidecar_terminal_closes_base_route_observation(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    base = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    late = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.late.jsonl"
    base.parent.mkdir(parents=True)
    _write_exact_episode(
        base,
        terminal_path=late,
        index=0,
        venue="KRX",
    )

    report = mod.build_report("2026-07-10")
    accounting = report["calibration_candidates"][0]["source_metrics"][
        "decision_accounting"
    ]

    assert accounting["unique_decision_count"] == 1
    assert accounting["terminal_counts"] == {"completed_before_horizon": 1}


def test_cumulative_economics_use_target_date_policy_version_only(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True)
    prior = event_dir / "pipeline_events_2026-07-09.jsonl"
    current = event_dir / "pipeline_events_2026-07-10.jsonl"
    _write_exact_episode(
        prior,
        index=99,
        venue="KRX",
        event_date="2026-07-09",
        policy_version="policy-v1",
    )
    for index in range(10):
        _write_exact_episode(
            current,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            policy_version="policy-v2",
        )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]
    accounting = candidate["source_metrics"]["decision_accounting"]

    assert accounting["unique_decision_count"] == 11
    assert accounting["same_policy_version_decision_count"] == 10
    assert accounting["selected_policy_version"] == "policy-v2"
    assert (
        candidate["source_metrics"]["selected_candidate_economics"]["sample_count"]
        == 10
    )


def test_common_runtime_scope_uses_economic_sample_venues_not_any_terminal(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir(parents=True)
    for index in range(10):
        _write_exact_episode(
            path,
            index=index,
            venue="NXT",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
        )
    _write_exact_episode(
        path,
        index=99,
        venue="KRX",
        source_authority=mod.RUNTIME_AUTHORITY,
        paired_ready=True,
        candidate_qty=0,
    )

    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]

    assert candidate["sample_count"] == 10
    assert (
        candidate["condition_feasibility"]["common_runtime_venue_scope_ready"] is False
    )
    assert candidate["calibration_reason"] == "common_runtime_venue_scope_not_closed"
    assert candidate["allowed_runtime_apply"] is False


def _config_fields():
    return {
        "runtime_config_schema": "avg_down_runtime_config_v1",
        "configured_min_buy_pressure": 85,
        "effective_min_buy_pressure": 85,
        "runtime_value_source": "runtime_rules_loaded_value",
        "runtime_value_raw": "not_set",
        "runtime_pid_value_verified": True,
        "avg_down_policy_version": "policy-v2",
        "sizing_policy_version": "sizing-v1",
        "cost_policy_version": "trade_profit_net_realized_pnl:rate=0.00230000",
        "decision_authority": "source_only_runtime_config_observation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_fresh_loaded_config_preserves_cumulative_evidence_without_daily_route(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    prior = tmp_path / "pipeline_events" / "pipeline_events_2026-07-09.jsonl"
    prior.parent.mkdir()
    for index in range(10):
        _write_exact_episode(
            prior,
            index=index,
            venue="KRX" if index < 5 else "NXT",
            event_date="2026-07-09",
            source_authority=mod.RUNTIME_AUTHORITY,
            paired_ready=True,
        )
    current = prior.with_name("pipeline_events_2026-07-10.jsonl")
    _write_event(
        current,
        stage="avg_down_runtime_config_observed",
        emitted_at="2026-07-10T09:00:00+09:00",
        **_config_fields(),
    )
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["sample_count"] == 10
    assert candidate["current_value_source"] == "same_day_runtime_config_event"
    assert (
        candidate["source_metrics"]["decision_accounting"][
            "target_date_route_observation_count"
        ]
        == 0
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_pid_value_verified", False),
        ("runtime_effect", True),
        ("effective_min_buy_pressure", 80),
        ("avg_down_policy_version", "unknown"),
        ("runtime_value_source", "default_fallback"),
    ],
)
def test_unverified_config_is_not_a_current_value_source(
    tmp_path, monkeypatch, field, value
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir()
    fields = _config_fields()
    fields[field] = value
    _write_event(
        path,
        stage="avg_down_runtime_config_observed",
        emitted_at="2026-07-10T09:00:00+09:00",
        **fields,
    )
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    assert candidate["allowed_runtime_apply"] is False
    assert (
        candidate["source_metrics"]["decision_accounting"]["diagnostics"][
            "invalid_runtime_config_snapshot"
        ]
        == 1
    )


@pytest.mark.parametrize(
    "seconds,qty,leak", [(1, 1, False), (3, 1, False), (1, 0, False), (1, 1, True)]
)
def test_exact_sizing_enrichment_does_not_invent_quantity(
    tmp_path, monkeypatch, seconds, qty, leak
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir()
    _write_exact_episode(path, index=0, venue="KRX", candidate_qty=0)

    def unknown(stage, fields):
        if stage == "avg_down_route_arbitration_observed":
            fields["route_replay"]["80"][
                "sizing_status"
            ] = "real_budget_not_available_without_extra_api_call"

    _mutate_events(path, unknown)
    original = json.loads(path.read_text().splitlines()[0])["fields"]
    _write_event(
        path,
        stage="avg_down_route_sizing_observed",
        emitted_at=f"2026-07-10T09:00:0{seconds}+09:00",
        source_observation_id=original["source_event_id"],
        scale_in_decision_id=original["scale_in_decision_id"],
        position_episode_id=original["position_episode_id"],
        pre_add_buy_price=original["pre_add_buy_price"],
        pre_add_buy_qty=original["pre_add_buy_qty"],
        sizing_replay={"80": {"proposed_add_price": 100, "proposed_add_qty": qty}},
        decision_authority="source_only_route_sizing_observation",
        runtime_effect=leak,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    evidence = mod._collect_exact_evidence([path])
    arm = evidence["decisions"][0]["route_replay"]["80"]
    assert arm["economic_inputs_complete"] is (seconds <= 2 and qty > 0 and not leak)


def test_postclose_runs_independent_replay_and_reports_missing_input(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir()
    _write_exact_episode(path, index=0, venue="KRX")
    report = mod.build_report("2026-07-10")
    replay = report["independent_exit_replay"]
    assert replay["unique_episode_count"] == 1
    assert replay["blocker_counts"] == {"exit_policy_version_missing": 1}
    assert replay["allowed_runtime_apply"] is False


def test_independent_recorded_frames_flow_through_existing_postclose_producer(
    tmp_path, monkeypatch
):
    from src.tests.test_avg_down_replay import replay_fixture, decision
    from src.engine.lifecycle.avg_down_replay import replay_exit_paths

    observation, frames = replay_fixture()

    def record(state, frame, policy, input_digest):
        value = decision(state, frame, policy, input_digest)
        frames[frame["sequence"] - 1].setdefault("full_policy_decisions", {})[
            input_digest
        ] = value
        return value

    expected = replay_exit_paths(observation, frames, full_exit_evaluator=record)
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-09-04.jsonl"
    path.parent.mkdir()
    observed_fields = {
        key: value for key, value in observation.items() if key != "emitted_at"
    }
    observed_fields.update(
        avg_down_route_schema=mod.ROUTE_EVENT_SCHEMA,
        avg_down_policy_version="avg-policy-1",
        sizing_policy_version="sizing-1",
        cost_policy_version="trade_profit_net_realized_pnl:rate=0.00230000",
        configured_min_buy_pressure=85,
        runtime_value_source="runtime_rules_loaded_value",
        runtime_pid_value_verified=True,
    )
    observed_fields["route_replay"] = {
        key: {
            **_route_arm(
                should_add=arm["should_add"],
                signature=f"arm-{key}",
                price=arm.get("proposed_add_price", 0),
                qty=arm.get("proposed_add_qty", 0),
            ),
            **arm,
        }
        for key, arm in observation["route_replay"].items()
    }
    _write_event(
        path,
        stage="avg_down_route_arbitration_observed",
        emitted_at=observation["emitted_at"],
        **observed_fields,
    )
    for frame in frames:
        _write_event(
            path,
            stage="avg_down_exit_replay_frame_observed",
            **frame,
            source_observation_id=observation["source_event_id"],
            decision_authority="source_only_paired_exit_replay",
            runtime_effect=False,
            allowed_runtime_apply=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        )
    report = mod.build_report("2026-09-04")
    replay = report["independent_exit_replay"]
    assert replay["complete_episode_count"] == 1
    actual = replay["episodes"][observation["position_episode_id"]]
    cache_fields = {
        "evidence_digest",
        "replay_observation_digest",
        "replay_source_date",
    }
    assert {key: value for key, value in actual.items() if key not in cache_fields} == {
        key: value for key, value in expected.items() if key not in cache_fields
    }
    assert actual["replay_source_date"] == "2026-09-04"
    assert mod.replay_evidence_contract_errors(replay) == []
    assert report["allowed_runtime_apply"] is False
    assert all(
        mod._valid_paired_exit_outcome(outcome) is None
        for outcome in expected["outcomes"].values()
    )


def test_runtime_attribution_deduplicates_changed_no_add_episodes(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-07-10.jsonl"
    path.parent.mkdir()
    _write_exact_episode(path, index=0, venue="KRX")
    _write_exact_episode(
        path,
        index=0,
        venue="KRX",
        source_event_id="second",
        decision_id="second-decision",
    )

    def selected(stage, fields):
        if stage == "avg_down_route_arbitration_observed":
            fields.update(
                runtime_candidate_selected=True,
                runtime_env_written=True,
                runtime_pid_value_verified=True,
                runtime_natural_match=True,
                runtime_behavior_changed=True,
                runtime_candidate_quality_update_id="selected-1",
                runtime_previous_min_buy_pressure=80,
            )

    _mutate_events(path, selected)
    _write_exact_episode(path, index=1, venue="KRX")
    candidate = mod.build_report("2026-07-10")["calibration_candidates"][0]
    attribution = candidate["runtime_application_attribution"]
    assert attribution["pid_verified_observation_count"] == 2
    assert attribution["natural_match_observation_count"] == 2
    assert attribution["natural_match_count"] == 1
    assert attribution["terminal_attributed_count"] == 1
    assert attribution["no_add_behavior_changed_episode_count"] == 1
    assert attribution["realized_improvement_claimed"] is False
