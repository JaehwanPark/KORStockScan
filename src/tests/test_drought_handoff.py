"""Normal submit drought handoff survives dedicated recheck retirement."""

import json

import pytest

from src.engine.automation import drought_handoff as handoff

DAY = "2026-09-17"


def publish(root, owner, payload):
    path = handoff.report_path(root, owner, DAY)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return path


@pytest.fixture
def chain(tmp_path):
    rows = [
        {"order_id": order_id, "decision": "implement_now",
         "runtime_effect": False, "allowed_runtime_apply": False}
        for order_id in handoff.REQUIRED_IDS
    ]
    publish(tmp_path, "code_improvement_workorder", {"date": DAY, "orders": rows})
    publish(tmp_path, "buy_funnel_sentinel", {"entry_submit_drought_contract": {"critical": True}})
    ev = {"code_improvement_workorder": {"orders": []}}
    summary = {"drought_handoff": handoff.canonical_receipt(tmp_path, DAY, ev)}
    return tmp_path, ev, summary


def test_normal_handoff_needs_no_retired_controller(chain):
    root, ev, summary = chain
    result = handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)
    assert result["status"] == "pass", result
    assert result["ev_snapshot_diff"]["missing_in_ev"] == sorted(handoff.REQUIRED_IDS)
    assert not any("controller" in key for key in summary["drought_handoff"])


@pytest.mark.parametrize("mutation", ["remove", "decision", "authority", "acceptance"])
def test_changed_normal_instruction_cannot_hide_behind_summary(chain, mutation):
    root, ev, summary = chain
    path = handoff.report_path(root, "code_improvement_workorder", DAY)
    payload = json.loads(path.read_text())
    if mutation == "remove":
        payload["orders"].pop()
    else:
        key = {"decision": "decision", "authority": "runtime_effect", "acceptance": "acceptance_tests"}[mutation]
        payload["orders"][0][key] = "changed"
    path.write_text(json.dumps(payload))
    assert handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)["status"] == "fail"
    summary["drought_handoff"] = handoff.canonical_receipt(root, DAY, ev)
    result = handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)
    assert result["status"] == ("fail" if mutation in {"remove", "authority"} else "pass")


def test_old_recheck_orders_and_controller_do_not_reenter_normal_handoff(chain):
    root, ev, summary = chain
    path = handoff.report_path(root, "code_improvement_workorder", DAY)
    payload = json.loads(path.read_text())
    payload["orders"].append({"order_id": "order_entry_recheck_source_repair", "decision": "implement_now", "runtime_effect": True})
    payload["orders"].append({"order_id": "old-opaque-id", "source_report_type": "entry_recheck_drought_controller", "runtime_effect": True})
    path.write_text(json.dumps(payload))
    publish(root, "entry_recheck_drought_controller", {"calibration_candidates": [{"family": "entry_opportunity_recheck_runtime", "allowed_runtime_apply": True}]})
    summary["drought_handoff"] = handoff.canonical_receipt(root, DAY, ev)
    assert len(summary["drought_handoff"]["canonical_orders"]) == len(handoff.REQUIRED_IDS)
    assert handoff.verify_drought_handoff(root, DAY, ev=ev, summary=summary)["status"] == "pass"
