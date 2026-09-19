"""Current retirement contract replaces obsolete matrix promotion scenarios."""

import importlib
import shlex
from dataclasses import fields
from pathlib import Path

import pytest

from src.engine.lifecycle import retirement as policy


def test_limit_down_stale_candidates_and_env_cannot_regain_authority():
    active = {"family": "samsung_machine_entry_policy"}
    stale = {"family": "limit_down_watch", "selected": True, "allowed_runtime_apply": True}
    raw = {"source_signature": "LIMIT_DOWN_LIVE_UNLOCK", "stage": "sell_completed"}
    cleaned = policy.current_report_view({
        "calibration_candidates": [stale, active],
        "limit_down_watch": stale,
        "raw_rows": [raw],
    })
    assert cleaned["calibration_candidates"] == [active]
    assert "limit_down_watch" not in cleaned
    assert cleaned["raw_rows"] == [raw]
    assert policy.without_retired_env({
        "KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED": "true",
        "KORSTOCKSCAN_LIMIT_DOWN_LIVE_POLICY_FILE": "/tmp/stale.json",
        "THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT": "true",
        "KORSTOCKSCAN_SCALPING_MAX_QTY": "25",
    }) == {"KORSTOCKSCAN_SCALPING_MAX_QTY": "25"}
    assert policy.retirement_env()["KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED"] == "false"


@pytest.mark.parametrize("name", sorted(policy.RETIRED_FAMILIES))
def test_retired_namespaces_cannot_be_current_sources(name):
    assert policy.retired_owner(name)
    assert policy.retired_artifact(
        Path("data/report") / name / f"{name}_2026-09-04.json"
    )
    assert not policy.retired_owner("swing_" + name)
    payload = {
        "calibration_candidates": [
            {"family": name},
            {"family": "samsung_machine_entry_policy"},
        ]
    }
    assert policy.current_report_view(payload)["calibration_candidates"] == [
        {"family": "samsung_machine_entry_policy"}
    ]


def test_latency_recommendation_retirement_preserves_runtime_safety_telemetry():
    report_name = "latency_classifier_recommendation"
    runtime_telemetry_family = "latency_classifier_runtime_profile"

    assert policy.retired_owner(report_name)
    assert policy.retired_artifact(
        Path("data/report") / report_name / f"{report_name}_2026-09-04.json"
    )
    assert runtime_telemetry_family in policy.RETIRED_CALIBRATION_FAMILIES
    assert not policy.retired_owner(runtime_telemetry_family)
    status = policy.retired_status(report_name)
    assert status["retirement_id"] == policy.LATENCY_RECOMMENDATION_RETIREMENT_ID
    assert status["allowed_runtime_apply"] is False


def test_calibration_only_retirement_filters_mixed_collections_not_raw_telemetry():
    family = "latency_classifier_runtime_profile"
    stale = {"family": family, "allowed_runtime_apply": True}
    active = {"family": "samsung_machine_entry_policy"}
    raw = {"family": family, "threshold_family": family, "stage": "latency_block"}
    cleaned = policy.current_report_view(
        {
            "calibration_candidates": [stale, active],
            "calibration_outcome": {"decisions": [stale, active]},
            "post_apply_attribution": {"calibration_decisions": [stale, active]},
            "approval_requests": [{"source_family": family}, active],
            "raw_rows": [raw],
        }
    )
    assert cleaned["calibration_candidates"] == [active]
    assert cleaned["calibration_outcome"]["decisions"] == [active]
    assert cleaned["post_apply_attribution"]["calibration_decisions"] == [active]
    assert cleaned["approval_requests"] == [active]
    assert cleaned["raw_rows"] == [raw]
    assert policy.current_report_view({"summary": {"approval_requests": 2}}) == {
        "summary": {"approval_requests": 2}
    }


@pytest.mark.parametrize(
    "module,function",
    [
        (
            "scalp_entry_action_decision_matrix",
            "build_scalp_entry_action_decision_matrix_report",
        ),
        ("lifecycle_decision_matrix", "build_lifecycle_decision_matrix_report"),
        ("lifecycle_bucket_discovery", "build_lifecycle_bucket_discovery_report"),
        ("lifecycle_ai_context", "build_lifecycle_ai_context_report"),
        ("lifecycle_ai_context", "build_lifecycle_ai_context_attribution_report"),
        ("runtime_apply_bridge", "build_runtime_apply_bridge_report"),
    ],
)
def test_retired_builders_do_not_read_or_write_files(module, function, monkeypatch):
    mod = importlib.import_module("src.engine." + module)

    def forbidden(*args, **kwargs):
        pytest.fail("retired producer performed file I/O")

    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    report = getattr(mod, function)("2026-09-04")
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


def test_constants_ignore_inherited_enable_flags(monkeypatch):
    from src.utils import constants

    for key in policy.retirement_env():
        monkeypatch.setenv(key, "true")
    rules = constants._build_trading_rules()
    for field in fields(rules):
        if field.name.endswith("_ENABLED") and (
            "KORSTOCKSCAN_" + field.name
        ).startswith(policy.RETIRED_ENV_PREFIXES):
            assert getattr(rules, field.name) is False, field.name


def test_retirement_shell_commands_clear_namespace_and_assert_explicit_off():
    inherited = {
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_POLICY_FILE": "stale.json",
        "KORSTOCKSCAN_UNRELATED_ENABLED": "true",
    }

    commands = policy.retirement_shell_commands(inherited).splitlines()

    assert (
        "unset -- KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED" in commands
    )
    assert (
        "unset -- KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_POLICY_FILE"
        in commands
    )
    assert not any(
        item.startswith("export KORSTOCKSCAN_SCALP_SIM_SCALE_IN_")
        or item.startswith("export KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_")
        for item in commands
    )
    assert not any("KORSTOCKSCAN_UNRELATED_ENABLED" in item for item in commands)


def test_retirement_shell_commands_quote_inherited_names():
    hostile_key = (
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_BAD;"
        "touch /tmp/should-not-run"
    )

    commands = policy.retirement_shell_commands({hostile_key: "true"}).splitlines()

    assert f"unset -- {shlex.quote(hostile_key)}" in commands


def test_startup_runtime_normalization_matches_retirement_contract():
    from src.utils.runtime_flags import (
        STARTUP_RETIRED_RUNTIME_ENV_KEYS,
        normalize_startup_retired_runtime_env,
    )

    legacy_key = next(iter(STARTUP_RETIRED_RUNTIME_ENV_KEYS))
    inherited = {
        legacy_key: "true",
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED": "true",
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_POLICY_FILE": "stale.json",
        "KORSTOCKSCAN_UNRELATED_ENABLED": "true",
    }

    changed = normalize_startup_retired_runtime_env(inherited)

    assert legacy_key not in inherited
    assert (
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_POLICY_FILE" not in inherited
    )
    assert inherited["KORSTOCKSCAN_UNRELATED_ENABLED"] == "true"
    for key, value in policy.retirement_env().items():
        assert inherited[key] == value
    assert "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED" in changed
    assert not any(
        key.startswith("KORSTOCKSCAN_SCALP_SIM_SCALE_IN_")
        or key.startswith("KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_")
        for key in inherited
    )


def test_live_adapters_are_noops_even_with_advisory_true(monkeypatch):
    from src.engine import scalp_entry_adm_runtime as entry
    from src.engine import holding_exit_matrix_runtime as holding
    from src.engine import lifecycle_ai_context as context
    from src.engine import lifecycle_decision_matrix_runtime as matrix

    def forbidden(*args, **kwargs):
        pytest.fail("retired runtime read a matrix")

    monkeypatch.setattr(Path, "read_text", forbidden)
    e = entry.build_scalp_entry_adm_runtime_context(
        prompt_profile="entry", ws_data={}, advisory_enabled=True
    )
    h = holding.build_holding_exit_matrix_runtime_context(
        prompt_profile="holding", ws_data={}, recent_candles=[], advisory_enabled=True
    )
    c = context.build_lifecycle_ai_runtime_context(prompt_profile="entry")
    for result in (e, h, c):
        assert result["applied"] is False
        assert result["prompt_context"] == ""
        assert result["cache_token"] == policy.RETIREMENT_ID
    assert (
        entry.merge_scalp_entry_adm_result_fields({"action": "WAIT", "score": 67}, e)[
            "action"
        ]
        == "WAIT"
    )
    assert (
        holding.merge_holding_exit_matrix_result_fields({"action": "EXIT"}, h)["action"]
        == "EXIT"
    )
    forged = {
        "lifecycle_matrix_selected_action": "BUY",
        "lifecycle_matrix_runtime_effect": "promote",
    }
    assert (
        matrix.apply_lifecycle_decision_to_payload({"action": "WAIT"}, forged)["action"]
        == "WAIT"
    )




def test_source_adapter_uses_raw_normalization_without_matrix_or_sim_outcomes(
    monkeypatch,
):
    from src.engine.scalping import entry_observation_source as source

    raw = {
        "stage": "scalp_entry_action_decision_snapshot",
        "stock_code": "005930",
        "record_id": "r1",
        "emitted_at": "2026-09-04T10:00:00+09:00",
        "fields": {
            "source_stage": "ai_confirmed",
            "ai_score": 67,
            "ai_action": "WAIT",
            "record_id": "r1",
        },
    }
    monkeypatch.setattr(
        source.observations, "_iter_relevant_events", lambda day: iter([raw])
    )
    monkeypatch.setattr(
        source.observations,
        "build_scalp_entry_action_decision_matrix_report",
        lambda day: pytest.fail("matrix builder called"),
    )
    result = source.load_entry_observations("2026-09-04")
    assert result["rows"][0]["record_id"] == "r1"
    assert result["rows"][0]["ai_score"] == 67
    assert not result["rows"][0].get("profit_rate")
    assert result["decision_authority"] == "source_only"


def test_wrapper_has_no_retired_producer_commands():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text()
    for name in policy.RETIRED_REPORTS:
        assert "-m src.engine." + name + " " not in script
    assert "entry_recheck_drought_controller" not in script
    assert "-m src.engine.scalping.entry_ai_gate_backtest" not in script
    assert 'ENTRY_AI_GATE_BACKTEST_SCHEDULE="on_demand"' in script
    assert "RUN_ENTRY_AI_GATE_BACKTEST=false" in script
    assert "entry AI gate diagnostic skipped" in script
    assert "-m src.engine.monitoring.samsung_machine_entry_tuning" in script
    assert "RUN_INSTITUTIONAL_FLOW_CONTEXT=false" in script
    assert "THRESHOLD_CYCLE_RUN_INSTITUTIONAL_FLOW_CONTEXT" not in script
    assert "-m src.engine.lifecycle.scale_in_incremental_counterfactual" not in script
    for retired in policy.SCALE_IN_RETIRED_REPORTS:
        assert f"-m src.engine.monitoring.{retired}" not in script


def test_scale_in_counterfactual_report_is_archive_but_avg_down_math_survives():
    from src.engine.lifecycle.scale_in_incremental_counterfactual import (
        compute_fixed_exit_incremental_economics,
    )

    report_path = Path(
        "data/report/scale_in_incremental_counterfactual/"
        "scale_in_incremental_counterfactual_2026-09-04.json"
    )
    assert policy.retired_artifact(report_path)
    assert (
        policy.current_report_view(
            {
                "report_type": "scale_in_incremental_counterfactual",
                "runtime_effect": False,
            }
        )
        == {}
    )
    economics = compute_fixed_exit_incremental_economics(
        pre_add_qty=10,
        pre_add_price=100,
        proposed_qty=1,
        proposed_price=100,
        exit_price=110,
    )
    assert economics["incremental_pnl_krw"] == 10
    assert economics["runtime_authority_ready"] is False




@pytest.mark.parametrize("invalid", [None, True, "invalid", {}])
def test_malformed_catalog_cannot_restore_archived_seeds(invalid):
    cleaned = policy.current_report_view(
        {
            "schema_version": "scalp_sim_policy_catalog_v1",
            "policies": invalid,
            "active_sim_priority_seeds": invalid,
        }
    )
    assert cleaned["active_sim_priority_seeds"] == []


def test_greenfield_env_cannot_reactivate_retired_gate(monkeypatch):
    from src.engine.lifecycle import greenfield_authority as gate

    monkeypatch.setenv(gate.ENABLED_ENV, "true")
    monkeypatch.setattr(
        gate, "_read_policy", lambda path: pytest.fail("retired policy read")
    )
    assert gate.greenfield_authority_active() is False
    assert gate.greenfield_stage_telegram_enabled() is False
    decision = gate.evaluate_greenfield_authority(stage="entry", action="BUY")
    assert decision.active is False
    assert (
        decision.allowed is True
    )  # No additional veto; existing order guards still own submit.




def test_shared_rebound_retirement_removes_only_independent_scale_in_authority():
    families = ["scalping_pyramid_quality_gate", "scalping_avg_down_recovery_quality_gate", "post_probe_winner_recovery"]
    assert policy.current_report_view({"calibration_candidates": [
        *({"family": f} for f in families), {"family": "mechanistic_entry_runtime"}
    ]})["calibration_candidates"] == [{"family": "mechanistic_entry_runtime"}]
    env = policy.without_retired_env({
        "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT": "0.1",
        "KORSTOCKSCAN_AVG_DOWN_RUNTIME_EVIDENCE_DIGEST": "old",
        "KORSTOCKSCAN_REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_ENABLED": "true",
        "KORSTOCKSCAN_ENABLE_SCALE_IN": "true",
    })
    assert len(env) == 2  # Shared safety and ADD enable are preserved.
    assert policy.retirement_env()["KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID"] == "false"
    for report in policy.SCALE_IN_RETIRED_REPORTS:
        assert policy.retired_artifact(Path("data/report") / report / "old.json")
        assert policy.retired_status(report)["retirement_id"] == policy.SCALE_IN_RETIREMENT_ID


def test_scale_in_retirement_preserves_avg_down_common_spread_guard():
    from src.engine.lifecycle.retirement import without_retired_env
    common = {"KORSTOCKSCAN_SCALPING_PYRAMID_PRICE_GUARD_ENABLED": "true",
              "KORSTOCKSCAN_SCALPING_PYRAMID_MAX_SPREAD_BPS": "80"}
    assert without_retired_env(common) == common


def test_rising_missed_scout_retirement_cannot_be_overridden_by_old_env():
    old = {"KORSTOCKSCAN_RISING_MISSED_ONE_SHARE_ENTRY_ENABLED": "true",
           "KORSTOCKSCAN_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW": "999999",
           "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED": "true",
           "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true"}
    clean = policy.without_retired_env(old)
    assert "KORSTOCKSCAN_RISING_MISSED_ONE_SHARE_ENTRY_ENABLED" not in clean
    assert "KORSTOCKSCAN_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW" not in clean
    assert clean["KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED"] == "true"
    assert clean["KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED"] == "true"
    for name in policy.RISING_MISSED_SCOUT_RETIRED_REPORTS:
        assert policy.retired_status(name)["retirement_id"] == policy.RISING_MISSED_SCOUT_RETIREMENT_ID


@pytest.mark.parametrize("name", ["one_share_threshold_opportunity", "rising_missed_scout_workorder"])
def test_rising_missed_scout_sources_are_not_read_by_current_consumers(name, monkeypatch):
    from src.engine import build_code_improvement_workorder as workorder
    from src.engine import build_next_stage2_checklist as checklist
    def forbidden(*args, **kwargs):
        pytest.fail("retired source was read")
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    path = Path("data/report") / name / (name + "_2026-09-18.json")
    assert workorder._load_json(path) == {}
    assert checklist._load_json(path) == {}


def test_retired_scout_orders_cannot_reenter_current_mixed_bundle():
    active = {"source_report_type": "buy_funnel_sentinel", "order_id": "ordinary"}
    stale = [{"source_report_type": name, "order_id": "old", "runtime_effect": True}
             for name in policy.RISING_MISSED_SCOUT_RETIRED_REPORTS]
    raw = {"stage": "sell_completed", "record_id": 7, "profit_rate": 0.2}
    cleaned = policy.current_report_view({"orders": stale + [active], "raw_rows": [raw]})
    assert cleaned["orders"] == [active]
    assert cleaned["raw_rows"] == [raw]


@pytest.mark.parametrize("key", ["entry_opportunity_recheck_armed", "entry_opportunity_recheck_pending"])
@pytest.mark.parametrize("where", ["stock", "runtime"])
def test_retired_recheck_intent_cannot_reach_buy_submission(monkeypatch, key, where):
    from src.engine import sniper_state_handlers as handlers
    stock, runtime = {"record_id": 71}, {}
    (stock if where == "stock" else runtime)[key] = True
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", "true")
    monkeypatch.setattr(handlers.kiwoom_orders, "send_buy_order", lambda *a, **k: pytest.fail("retired broker submit"))
    assert handlers._submit_watching_triggered_entry(stock, "005930", {}, "test", runtime) is False


def test_retired_recheck_policy_env_and_workorder_are_filtered():
    stale = {"family": "entry_opportunity_recheck_runtime", "allowed_runtime_apply": True}
    active = {"family": "samsung_machine_entry_policy"}
    assert policy.current_calibration_rows([stale, active]) == [active]
    assert policy.current_report_view({"orders": [{"order_id": "order_entry_recheck_repair", "runtime_effect": True}, {"order_id": "order_entry_submit_drought_auto_resolution"}]})["orders"] == [{"order_id": "order_entry_submit_drought_auto_resolution"}]
    assert policy.without_retired_env({"KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true", "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_RECHECK": "100", "COMMON": "keep"}) == {"COMMON": "keep"}
    assert policy.retirement_env()["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"] == "false"


def test_retired_recheck_custody_events_cannot_recreate_threshold_partitions():
    from src.utils.threshold_cycle_registry import threshold_family_for_stage
    assert threshold_family_for_stage("entry_opportunity_recheck_filled") == ""
    assert threshold_family_for_stage("entry_opportunity_recheck_sell_completed") == ""
    assert threshold_family_for_stage("unknown", {"threshold_family": "entry_opportunity_recheck_runtime"}) == ""
    assert threshold_family_for_stage("budget_pass") == "entry_mechanical_momentum"


def test_claude_lab_stale_orders_are_excluded_without_retiring_existing_families():
    from src.engine.lifecycle.retirement import current_report_view, retired_artifact
    old = {"orders": [
        {"order_id": "shared_identity", "source_report_type": "scalping_pattern_lab_automation", "delta_ev": 100},
        {"order_id": "shared_identity", "source_report_type": "entry_split_order_plan", "family": "score65_74_recovery_probe"},
    ], "non_selected_orders": [{"source_report_type": "scalping_pattern_lab_automation"}]}
    filtered = current_report_view(old)
    assert len(filtered["orders"]) == 1
    assert filtered["orders"][0]["source_report_type"] == "entry_split_order_plan"
    assert filtered["non_selected_orders"] == []
    assert retired_artifact("/archive/claude_scalping_pattern_lab/outputs/result.json")


def test_main_shared_lab_clis_are_retired_before_any_provider_or_file_read(monkeypatch):
    from src.engine import pattern_lab_ai_review as reviewer
    from src.engine import pattern_lab_currentness_audit as currentness
    from src.engine import pattern_lab_propagation_audit as propagation
    def forbidden(*args, **kwargs):
        raise AssertionError("Retired Main Lab must not read or call provider")
    monkeypatch.setattr(reviewer, "_build_input_context", forbidden)
    monkeypatch.setattr(currentness, "_lab_paths", forbidden)
    monkeypatch.setattr(propagation, "_load_json", forbidden)
    assert reviewer.review_current_generation("2026-09-17", include_swing=False)["status"] == "retired"
    assert currentness.build_pattern_lab_currentness_audit("2026-09-17", include_swing=False)["status"] == "retired"
    assert propagation.build_pattern_lab_propagation_audit("2026-09-17", include_swing=False)["status"] == "retired"


def test_old_auto_checklist_lab_source_is_not_carried_forward():
    from src.engine.build_next_stage2_checklist import _merge_preserved_auto_tasks, AUTO_START, AUTO_END
    previous = AUTO_START + "\n## 장후\n- [ ] `[OldLabWork]` old lab\n  - Source: data/report/scalping_pattern_lab_automation/old.json\n- [ ] `[ActiveOwner]` independent source\n  - Source: data/report/entry_split_order_plan/current.json\n" + AUTO_END
    result = _merge_preserved_auto_tasks(previous, AUTO_START + "\n## 장후\n" + AUTO_END)
    assert "OldLabWork" not in result
    assert "ActiveOwner" in result




def test_retired_entry_scale_in_is_blocked_before_common_buy_guards(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    def unexpected_guard(*args, **kwargs):
        pytest.fail("Retired entry source reached a common buy guard")

    monkeypatch.setattr(handlers, "_scale_in_exit_authority_block_reason", unexpected_guard)
    for key in ("source_signature", "scanner_source_signature"):
        result = handlers.can_consider_scale_in(
            {key: "PRICE_JUMP_START,LIMIT_DOWN_LIVE_UNLOCK"},
            "005930", {}, "SCALPING", "NORMAL",
            bypass_scalping_buy_window=True, bypass_scale_in_cooldown=True,
        )
        assert result == {
            "allowed": False,
            "reason": "retired_entry_source_scale_in_forbidden",
        }
