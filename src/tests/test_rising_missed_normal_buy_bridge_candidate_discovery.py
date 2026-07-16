import json

from src.engine.monitoring import (
    rising_missed_normal_buy_bridge_candidate_discovery as mod,
)


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_bridge_candidate_discovery_surfaces_preopen_env_candidate(tmp_path):
    diagnostic = _write(
        tmp_path / "diag.json",
        {
            "rising_missed_buy": [
                {
                    "stock_code": "000001",
                    "stock_name": "candidate",
                    "rising_missed_class": "rising_missed_raw",
                    "rising_missed_one_share_eligible": True,
                    "latest_blocker": {
                        "stage": "first_ai_wait",
                        "reason": "big_bite_not_confirmed",
                        "ai_action": "BUY",
                        "ai_score": "70",
                        "entry_score_threshold": "75",
                        "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    },
                },
                {
                    "stock_code": "000002",
                    "stock_name": "waiter",
                    "rising_missed_class": "rising_missed_raw",
                    "rising_missed_one_share_eligible": True,
                    "latest_blocker": {
                        "stage": "first_ai_wait",
                        "ai_action": "WAIT",
                        "ai_score": "70",
                    },
                },
                {
                    "stock_code": "000003",
                    "stock_name": "source-bad",
                    "rising_missed_class": "source_quality_excluded",
                    "rising_missed_one_share_eligible": False,
                    "latest_blocker": {
                        "stage": "first_ai_wait",
                        "ai_action": "BUY",
                        "ai_score": "70",
                    },
                },
            ]
        },
    )
    scout = _write(
        tmp_path / "scout.json", {"summary": {"profitable_forced_scout_count": 3}}
    )
    prior = _write(tmp_path / "prior.json", {"summary": {"prior_count": 2}})

    report = mod.build_report(
        "2026-07-07",
        source_paths={
            "intraday_entry_blocker_diagnostics": diagnostic,
            "rising_missed_scout_workorder": scout,
            "rising_missed_classifier_prior": prior,
        },
        generated_at="fixed",
    )

    assert report["summary"]["status"] == "preopen_env_candidate"
    assert report["summary"]["bridge_candidate_count"] == 1
    assert report["summary"]["blocked_reason_counts"]["entry_ai_action_not_buy"] == 1
    assert report["summary"]["blocked_reason_counts"]["source_quality_excluded"] == 1
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    order = report["code_improvement_orders"][0]
    assert (
        order["order_id"] == "order_rising_missed_normal_buy_bridge_preopen_env_review"
    )
    assert order["next_preopen_candidate"]["env"] == {
        "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED": "true"
    }
    assert order["implementation_provenance"]["uses_normal_buy_sizing"] is True
    assert (
        order["implementation_provenance"]["forced_one_share_qty_or_tag_used"] is False
    )
    assert "broker_guard_bypass" in order["forbidden_uses"]


def test_bridge_candidate_discovery_write_outputs(tmp_path):
    report = {
        "target_date": "2026-07-07",
        "generated_at": "fixed",
        "summary": {
            "status": "hold_no_candidate",
            "runtime_env_key": "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED",
            "bridge_candidate_count": 0,
            "blocked_row_count": 0,
            "code_improvement_order_count": 0,
        },
        "bridge_candidates": [],
        "code_improvement_orders": [],
    }

    output_json = tmp_path / "bridge.json"
    output_md = tmp_path / "bridge.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert (
        json.loads(output_json.read_text(encoding="utf-8"))["summary"]["status"]
        == "hold_no_candidate"
    )
    markdown = output_md.read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED" in markdown
    assert "- none" in markdown


def test_bridge_candidate_discovery_reports_missing_required_diagnostic_source(
    tmp_path,
):
    report = mod.build_report(
        "2026-07-07",
        source_paths={
            "intraday_entry_blocker_diagnostics": tmp_path / "missing_diag.json",
            "rising_missed_scout_workorder": tmp_path / "missing_scout.json",
            "rising_missed_classifier_prior": tmp_path / "missing_prior.json",
        },
        generated_at="fixed",
    )

    assert report["summary"]["status"] == "source_missing"
    assert report["summary"]["missing_required_sources"] == [
        "intraday_entry_blocker_diagnostics"
    ]
    assert report["summary"]["bridge_candidate_count"] == 0
    assert report["code_improvement_orders"] == []
