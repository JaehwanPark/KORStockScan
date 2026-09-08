"""Exercise real controller -> canonical summary -> strict/PREOPEN contracts offline."""

import json
from copy import deepcopy

import pytest

from src.engine.automation import drought_handoff as handoff
from src.engine.scalping import entry_ai_gate_backtest as backtest
from src.engine.scalping import entry_recheck_drought_controller as producer
from src.engine import threshold_cycle_preopen_apply as preopen
from src.tests.submit_drought_fixtures import make_report

DAY = "2026-09-08"


def publish(root, owner, day, payload):
    path = handoff.report_path(root, owner, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return path


@pytest.fixture
def chain(tmp_path, monkeypatch):
    root = tmp_path / "report"
    for mod in (producer, backtest):
        monkeypatch.setattr(
            mod, "BUY_FUNNEL_SENTINEL_DIR", root / "buy_funnel_sentinel"
        )
        monkeypatch.setattr(mod, "DROUGHT_REPORT_DIR", root / handoff.CONTROLLER)
        monkeypatch.setattr(
            mod,
            "load_source_quality_preflight",
            lambda d: {"status": "pass", "tuning_input_allowed": True},
        )
    monkeypatch.setattr(backtest, "REPORT_DIR", root / "entry_ai_gate_backtest")
    monkeypatch.setattr(backtest, "THRESHOLD_CYCLE_DIR", tmp_path / "thresholds")
    monkeypatch.setattr(backtest, "RUNTIME_ENV_DIR", tmp_path / "runtime")
    runtime = backtest.RUNTIME_ENV_DIR / f"threshold_runtime_env_{DAY}.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(json.dumps({"target_date": DAY, "env_overrides": {}}))
    for day in ("2026-09-04", "2026-09-07", DAY):
        publish(root, "buy_funnel_sentinel", day, make_report(day, samples=30))
    report = producer.build_report(DAY)
    publish(root, handoff.CONTROLLER, DAY, report)
    rows = [
        {
            "order_id": i,
            "decision": "implement_now",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for i in handoff.REQUIRED_IDS
    ]
    rows += report["code_improvement_orders"]
    publish(root, "code_improvement_workorder", DAY, {"date": DAY, "orders": rows})
    ev = {
        "code_improvement_workorder": {"orders": []},
        "entry_funnel": {"entry_submit_drought_handoff_selected": True},
    }
    summary = {"drought_handoff": handoff.canonical_receipt(root, DAY, ev)}
    return root, report, ev, summary


def test_current_canonical_receipt_accepts_intentional_previous_ev_snapshot(chain):
    root, report, ev, summary = chain
    assert report["drought_conditional_policy"]["desired_enabled"] is True
    assert report["drought_conditional_policy"]["intraday_escalation_allowed"] is False
    assert handoff.controller_error(report, root, DAY) == ""
    result = handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)
    assert result["status"] == "pass", result
    assert result["ev_snapshot_diff"]["missing_in_ev"]


@pytest.mark.parametrize("mutation", ["remove", "decision", "authority", "acceptance"])
def test_aggregate_true_cannot_hide_changed_canonical_instruction(chain, mutation):
    root, _, ev, summary = chain
    path = handoff.report_path(root, "code_improvement_workorder", DAY)
    payload = json.loads(path.read_text())
    if mutation == "remove":
        payload["orders"].pop()
    else:
        payload["orders"][0][
            {
                "decision": "decision",
                "authority": "runtime_effect",
                "acceptance": "acceptance_tests",
            }[mutation]
        ] = "changed"
    path.write_text(json.dumps(payload))
    result = handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)
    assert "drought_runtime_summary_canonical_receipt_mismatch" in result["issues"]


def test_missing_controller_is_strict_failure_and_explicit_off_is_respected(chain):
    root, _, ev, _ = chain
    handoff.report_path(root, handoff.CONTROLLER, DAY).unlink()
    summary = {"drought_handoff": handoff.canonical_receipt(root, DAY, ev)}
    assert (
        handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)["status"]
        == "fail"
    )
    assert (
        handoff.verify_drought_handoff(
            root, DAY, ev=ev, summary=summary, require_controller=False
        )["status"]
        == "pass"
    )


def test_preopen_and_strict_reject_changed_canonical_history(chain, monkeypatch):
    root, report, ev, summary = chain
    publish(root, "buy_funnel_sentinel", DAY, make_report(DAY, samples=40))
    assert (
        handoff.controller_error(report, root, DAY)
        == "drought_controller_sentinel_source_changed"
    )
    monkeypatch.setattr(
        preopen,
        "_entry_recheck_drought_controller_path",
        lambda d: handoff.report_path(root, handoff.CONTROLLER, d),
    )
    monkeypatch.setattr(
        preopen, "_source_quality_preflight_status", lambda d: {"blocked": False}
    )
    candidates, status = preopen._load_entry_recheck_drought_controller_candidates(DAY)
    assert (
        status["runtime_update_contract_error"]
        == "drought_controller_sentinel_source_changed"
    )
    assert all(c["allowed_runtime_apply"] is False for c in candidates)


def test_rehashing_without_recomputing_meaning_cannot_bless_stale_history(chain):
    root, report, _, _ = chain
    publish(root, "buy_funnel_sentinel", DAY, make_report(DAY, samples=40))
    _, digest = handoff.read_source(
        handoff.report_path(root, "buy_funnel_sentinel", DAY)
    )
    report["drought_conditional_policy"]["history"][-1]["source_sha256"] = digest
    assert (
        handoff.controller_error(report, root, DAY)
        == "drought_controller_sentinel_semantic_mismatch"
    )


def test_legacy_history_is_explicit_transition_and_valid_off_not_false_success(chain):
    root, _, _, _ = chain
    for day in ("2026-09-04", "2026-09-07"):
        source = make_report(day, samples=30)
        source["schema_version"] = 5
        publish(root, "buy_funnel_sentinel", day, source)
    report = producer.build_report(DAY)
    assert report["drought_conditional_policy"]["desired_enabled"] is False
    assert handoff.controller_error(report, root, DAY) == ""
    assert len(report["maintenance_review"]["history_transition"]) == 2
    assert report["maintenance_review"]["conditional_next_preopen_date"] == "2026-09-11"


@pytest.mark.parametrize("bad", [None, [], "bad", {"orders": "bad"}])
def test_malformed_controller_fails_closed_without_crashing(chain, bad):
    root, report, _, _ = chain
    broken = deepcopy(report)
    broken["maintenance_review"] = bad
    assert handoff.controller_error(broken, root, DAY)


def test_native_review_order_omission_is_rejected_even_after_summary_refresh(chain):
    root, report, ev, _ = chain
    assert report["code_improvement_orders"]
    publish(
        root,
        "code_improvement_workorder",
        DAY,
        {
            "date": DAY,
            "orders": [
                {
                    "order_id": i,
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
                for i in handoff.REQUIRED_IDS
            ],
        },
    )
    summary = {"drought_handoff": handoff.canonical_receipt(root, DAY, ev)}
    assert (
        "drought_controller_review_orders_missing"
        in handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)["issues"]
    )


def test_recovery_repairs_controller_first_and_finishes_strict_without_live_apply():
    from src.engine.automation import postclose_done_controller as done

    error = "drought_controller_sentinel_source_changed"
    verification = {
        "drought_canonical_handoff": {
            "status": "fail",
            "issues": [error],
            "controller_validation_error": error,
            "controller_required": True,
        },
        "missing_downstream_links": [error],
        "code_improvement_workorder_source_fingerprint": {
            "issues": ["workorder_source_hash_changed"]
        },
        "source_generation_warnings": ["workorder_source_hash_changed"],
    }
    actions = done._recovery_actions(DAY, verification, allow_wrapper_rerun=False)
    assert actions[0].action == "refresh_entry_recheck_drought_controller"
    assert "--require-summary-handoff" in actions[-1].command
    assert not any(
        "--auto-apply" in a.command
        or "deploy/run_threshold_cycle_postclose.sh" in a.command
        for a in actions
    )


def test_summary_renders_current_canonical_decision_and_diagnostic_ev_difference(chain):
    from src.engine.runtime_approval_summary import (
        render_runtime_approval_summary_markdown,
    )

    _, _, _, summary = chain
    rendered = render_runtime_approval_summary_markdown(summary)
    assert "previous-generation diagnostic diff" in rendered
    assert "not PID application" in rendered


def test_controller_publish_detects_input_change_during_generation(chain, monkeypatch):
    root, _, _, _ = chain
    original = producer._entry_recheck_drought_candidate

    def change_source(**kwargs):
        result = original(**kwargs)
        publish(root, "buy_funnel_sentinel", DAY, make_report(DAY, samples=50))
        return result

    monkeypatch.setattr(producer, "_entry_recheck_drought_candidate", change_source)
    with pytest.raises(RuntimeError, match="source_changed"):
        producer.build_report(DAY)


def test_diagnostic_history_drift_is_not_an_extra_preopen_activation_gate(chain):
    root, report, _, _ = chain
    old_day = report["maintenance_review"]["source_days"][0]["source_date"]
    publish(root, "buy_funnel_sentinel", old_day, make_report(old_day, samples=40))
    assert handoff.controller_source_error(report, root, DAY) == ""
    assert (
        handoff.controller_error(report, root, DAY)
        == "drought_controller_sentinel_source_changed"
    )


def test_canonical_producer_retains_native_reviews_even_with_max_orders_one(
    chain, monkeypatch, tmp_path
):
    from src.engine import build_code_improvement_workorder as workorder

    root, report, _, _ = chain
    monkeypatch.setattr(
        workorder,
        "_load_source_json",
        lambda path, **kw: (
            handoff.read_source(path)[0] if path.is_relative_to(root) else {}
        ),
    )
    monkeypatch.setattr(
        workorder, "_source_path_enabled", lambda path, **kw: path.is_relative_to(root)
    )
    monkeypatch.setattr(
        workorder,
        "buy_funnel_sentinel_report_path",
        lambda d: handoff.report_path(root, "buy_funnel_sentinel", d),
    )
    monkeypatch.setattr(
        workorder,
        "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR",
        root / "code_improvement_workorder",
    )
    monkeypatch.setattr(
        workorder, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "workorders"
    )
    built = workorder.build_code_improvement_workorder(
        DAY, max_orders=1, include_swing=False
    )
    ids = {r["order_id"] for r in built["orders"]}
    assert {r["order_id"] for r in report["code_improvement_orders"]} <= ids
    assert built["source"]["entry_recheck_drought_controller"]
    assert handoff.canonical_receipt(root, DAY, {})["issues"] == []


def test_strict_verifier_calls_controller_contract_and_honors_installed_off(
    chain, monkeypatch, tmp_path
):
    from src.engine import verify_threshold_cycle_postclose_chain as verifier

    root, _, ev, _ = chain
    handoff.report_path(root, handoff.CONTROLLER, DAY).unlink()
    summary = {"drought_handoff": handoff.canonical_receipt(root, DAY, ev)}
    publish(root, "runtime_approval_summary", DAY, summary)
    publish(root, "threshold_cycle_ev", DAY, ev)
    log = tmp_path / "postclose.log"
    monkeypatch.setattr(verifier, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(verifier, "REPORT_DIR", root)
    monkeypatch.setattr(
        verifier, "VERIFY_DIR", root / "threshold_cycle_postclose_verification"
    )
    monkeypatch.setattr(verifier, "LOG_PATH", log)
    monkeypatch.setattr(
        verifier,
        "_load_json",
        lambda path: handoff.read_source(path)[0] if path.is_relative_to(root) else {},
    )
    for flag, state in (("true", "fail"), ("false", "pass")):
        log.write_text(
            f"[START] threshold-cycle postclose target_date={DAY}\n[DONE] threshold-cycle postclose target_date={DAY} entry_recheck_drought_controller={flag}\n"
        )
        report = verifier.build_threshold_cycle_postclose_verification(
            DAY, require_summary_handoff=True
        )
        assert report["drought_canonical_handoff"]["status"] == state
        if flag == "true":
            assert (
                "drought_controller_missing_or_invalid"
                in report["missing_downstream_links"]
            )
