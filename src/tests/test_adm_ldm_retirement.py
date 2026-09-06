"""Current retirement contract replaces obsolete matrix promotion scenarios."""

import importlib
from dataclasses import fields
from pathlib import Path

import pytest

from src.engine.lifecycle import retirement as policy


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
        (
            "scalp_sim_scale_in_window_approval",
            "build_scalp_sim_scale_in_window_approval",
        ),
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


@pytest.mark.parametrize(
    "selector",
    [
        "_select_runtime_apply_bridge_approval",
        "_select_lifecycle_bucket_sim_auto_approval",
        "_select_scalp_sim_scale_in_window_approval",
    ],
)
def test_preopen_retired_selectors_ignore_approved_archive(selector):
    from src.engine import threshold_cycle_preopen_apply as preopen
    import inspect

    fn = getattr(preopen, selector)
    args = {
        name: {}
        for name, param in inspect.signature(fn).parameters.items()
        if param.default is inspect.Parameter.empty
    }
    assert fn(**args) == ([], [], {})


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


def test_mixed_catalog_cannot_reintroduce_ldm_seed():
    from src.engine.scalping import scalp_sim_auto_approval_control_tower as tower

    report = tower.build_policy_catalog(
        {
            "date": "2026-09-04",
            "approved_policies": [
                {
                    "source_id": "lifecycle_bucket_discovery",
                    "active_sim_priority_seeds": [
                        {"active_seed_id": "old", "status": "active"}
                    ],
                }
            ],
        }
    )
    assert report["policies"] == []
    assert report["active_sim_priority_seeds"] == []
    assert report["hypothesis_observation_plan"] == {}


def test_wrapper_has_no_retired_producer_commands():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text()
    for name in policy.RETIRED_REPORTS:
        assert "-m src.engine." + name + " " not in script
    assert "-m src.engine.scalping.entry_recheck_drought_controller" in script
    assert "-m src.engine.scalping.entry_ai_gate_backtest" not in script
    assert 'ENTRY_AI_GATE_BACKTEST_SCHEDULE="on_demand"' in script
    assert "RUN_ENTRY_AI_GATE_BACKTEST=false" in script
    assert "entry AI gate diagnostic skipped" in script
    assert "-m src.engine.monitoring.samsung_machine_entry_tuning" in script
    assert "RUN_INSTITUTIONAL_FLOW_CONTEXT=false" in script
    assert "THRESHOLD_CYCLE_RUN_INSTITUTIONAL_FLOW_CONTEXT" not in script
    assert "-m src.engine.lifecycle.scale_in_incremental_counterfactual" not in script
    assert (
        '"$PROJECT_DIR/src/engine/lifecycle/scale_in_incremental_counterfactual.py"'
        in script
    )
    avg_down_block = script.split(
        'if [ "$RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION"', 1
    )[1].split('if [ "$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY"', 1)[0]
    assert "scale_in_incremental_counterfactual.py" in avg_down_block


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


def test_current_summaries_expose_institutional_retirement_without_artifact_read():
    from src.engine import runtime_approval_summary as runtime_summary
    from src.engine import threshold_cycle_ev_report as ev_summary

    ev, path, warnings = ev_summary._institutional_flow_context_summary("2026-09-04")
    runtime = runtime_summary._institutional_flow_context_summary(
        {"institutional_flow_context": {"available": True, "runtime_effect": True}}
    )

    assert ev["status"] == "retired"
    assert ev["replacement_source"] == ("exact_ai_context_investor_and_program_flow")
    assert path is None
    assert warnings == []
    assert runtime["status"] == "retired"
    assert runtime["runtime_effect"] is False


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


def test_verifier_reports_retired_enabled_artifact_without_promoting_it(
    tmp_path, monkeypatch
):
    import json
    from src.engine import threshold_cycle_preopen_apply as preopen

    monkeypatch.setattr(preopen, "RUNTIME_ENV_DIR", tmp_path)
    path = preopen.runtime_env_manifest_path("2026-09-07")
    path.write_text(
        json.dumps(
            {
                "target_date": "2026-09-07",
                "selected_families": [],
                "env_overrides": {"KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED": "true"},
            }
        )
    )
    result = preopen.verify_runtime_env_handoff("2026-09-07")
    assert result["passed"] is False
    assert any(item["family"] == "adm_ldm_retired" for item in result["findings"])
