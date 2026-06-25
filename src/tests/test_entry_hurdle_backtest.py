import gzip
import json

from src.engine.scalping import entry_hurdle_backtest as mod


def test_entry_hurdle_backtest_classifies_overblocking_from_existing_artifacts(tmp_path, monkeypatch):
    buy_dir = tmp_path / "buy_funnel_sentinel"
    missed_dir = tmp_path / "monitor_snapshots"
    buy_dir.mkdir(parents=True)
    missed_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "BUY_FUNNEL_DIR", buy_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])

    (buy_dir / "buy_funnel_sentinel_2026-06-05.json").write_text(
        json.dumps(
            {
                "current": {
                    "session": {
                        "stage_unique": {
                            "ai_confirmed": 10,
                            "budget_pass": 5,
                            "latency_pass": 3,
                            "blocked_ai_score": 2,
                            "order_bundle_submitted": 1,
                            "pre_submit_late_entry_price_drift_guard_block": 1,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 10.0,
                            "submitted_to_budget_unique_pct": 20.0,
                        },
                    },
                },
                "classification": {
                    "primary": "SUBMIT_DROUGHT_CRITICAL",
                    "submit_drought_handoff_state": "handoff_required",
                    "submit_drought_root_cause": {
                        "quote_freshness_attribution": {
                            "runtime_effect": False,
                            "decision_authority": "submit_drought_quote_freshness_attribution_only",
                            "refresh_subreason_counts": {"latest_ws_snapshot_fresh": 2},
                            "refresh_attempted_count": 2,
                            "refresh_applied_count": 2,
                            "still_latency_blocked_after_refresh_count": 0,
                            "latency_pass_recovered_count": 2,
                            "order_bundle_submitted_after_refresh_count": 1,
                            "latency_pass_recovered_downstream_stage_counts": {
                                "pre_submit_liquidity_guard_block": 1,
                                "order_bundle_submitted": 1,
                            },
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    with gzip.open(missed_dir / "missed_entry_counterfactual_2026-06-05.json.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "metrics": {
                        "blocker_outcome_metrics": {
                            "pre_submit_liquidity_guard_block": {
                                "evaluated_candidates": 5,
                                "missed_winner_count": 4,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                            "blocked_ai_score": {
                                "evaluated_candidates": 4,
                                "missed_winner_count": 3,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                            "pre_submit_late_entry_price_drift_guard_block": {
                                "evaluated_candidates": 4,
                                "missed_winner_count": 3,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            }
                        },
                        "cohort_outcome_metrics": {
                            "entry_armed_latency_or_safety_block": {
                                "evaluated_candidates": 5,
                                "missed_winner_rate": 80.0,
                                "avoided_loser_rate": 0.0,
                            }
                        },
                    }
                }
            )
        )

    report = mod.build_report("2026-06-05", start_date="2026-06-05", end_date="2026-06-07")

    assert report["runtime_effect"] is False
    assert report["source_dates"] == ["2026-06-05"]
    assert report["summary"]["submitted_to_ai_unique_pct"] == 10.0
    blocker = report["summary"]["blocker_tradeoff"]["pre_submit_liquidity_guard_block"]
    assert blocker["missed_winner_rate"] == 80.0
    assert blocker["hurdle_decision"] == "overblocking_candidate"
    diagnostics = report["summary"]["next_action_diagnostics"]
    assert diagnostics["metric_role"] == "next_action_diagnostic"
    assert diagnostics["window_policy"] == "2026-06-05_to_2026-06-07"
    assert diagnostics["primary_decision_metric"] == "missed_winner_vs_avoided_loser_tradeoff"
    assert diagnostics["runtime_effect"] is False
    assert diagnostics["actual_order_submitted_provenance_preserved"] is True
    assert "entry price reprice" in diagnostics["forbidden_uses"]
    assert "risk expansion" in diagnostics["forbidden_uses"]
    assert "broker guard bypass" in diagnostics["forbidden_uses"]
    assert "stale quote guard bypass" in diagnostics["forbidden_uses"]
    assert diagnostics["quote_freshness_totals"]["latency_pass_recovered_count"] == 2
    assert diagnostics["quote_freshness_totals"]["order_bundle_submitted_after_refresh_count"] == 1
    action_ids = [item["action_id"] for item in diagnostics["recommended_next_actions"]]
    assert action_ids == [
        "trace_latency_refresh_recovered_downstream_blocker",
        "review_pre_submit_liquidity_relief_scope",
        "review_ai_wait_score_recheck_scope",
        "audit_late_entry_price_drift_guard_context",
    ]
    assert all(item["runtime_effect"] is False for item in diagnostics["recommended_next_actions"])
    assert not report["missing_artifacts"]
