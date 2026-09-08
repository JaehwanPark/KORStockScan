"""Pattern research can advance without granting trading authority."""

import hashlib
import json
from datetime import date

import pandas as pd
import pytest

from analysis.claude_scalping_pattern_lab import analyze_ev_patterns as analysis
from analysis.claude_scalping_pattern_lab import build_claude_payload as payload
from analysis.claude_scalping_pattern_lab import economic_evidence as econ
from analysis.claude_scalping_pattern_lab import prepare_dataset as prepare
from src.engine import pattern_lab_ai_review as ai
from src.engine import pattern_lab_currentness_audit as currentness
from src.engine import build_code_improvement_workorder as workorder
from src.engine import scalping_pattern_lab_automation as automation
from src.tests.test_score_recovery_net_approval import sign, signed_report


def write_report(root, day="2026-09-07", count=2, net=1, mutate=None):
    report = signed_report(day, count=count, net=net)
    if mutate:
        mutate(report)
    path = root / f"main_scalping_lifecycle_paired_{day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sign(report)))
    return report


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), True, None]
)
def test_snapshot_nonfinite_or_boolean_is_not_valid_profit(value):
    row = prepare._parse_trade_review(
        {
            "sections": {
                "recent_trades": [{"status": "COMPLETED", "profit_rate": value}]
            }
        },
        "local",
    )[0]
    assert row["profit_valid_flag"] is False


def test_prepared_flags_survive_loss_pattern_merge():
    trades = pd.DataFrame(
        [
            dict(
                trade_id=1,
                status="COMPLETED",
                profit_valid_flag=True,
                profit_rate=-1,
                cohort="partial_fill",
                exit_rule="test",
                partial_then_expand_flag=True,
            )
        ]
    )
    seq = pd.DataFrame([dict(trade_id=1, partial_then_expand_flag=True)])
    assert (
        analysis.extract_loss_patterns(trades, seq)[0]["preconditions"][
            "partial_then_expand_flag"
        ]["count"]
        == 1
    )


def test_fill_quality_does_not_infer_full_from_normal_or_missing_mode(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(prepare, "OUTPUT_DIR", tmp_path)
    trades = pd.DataFrame(
        [
            dict(
                trade_id=i,
                entry_mode="normal" if i != 1 else None,
                rec_date="2026-09-07",
            )
            for i in range(4)
        ]
    )
    seq = pd.DataFrame(
        [
            dict(
                trade_id=0,
                date="2026-09-07",
                observed_full_fill=True,
                observed_partial_fill=False,
            ),
            dict(
                trade_id=1,
                date="2026-09-07",
                observed_full_fill=False,
                observed_partial_fill=False,
            ),
            dict(
                trade_id=2,
                date="2026-09-07",
                observed_full_fill=True,
                observed_partial_fill=True,
            ),
            dict(
                trade_id=3,
                date="2026-09-04",
                observed_full_fill=True,
                observed_partial_fill=False,
            ),
        ]
    )
    result = prepare.enrich_trade_cohort(trades, seq)
    assert list(result.cohort) == [
        "full_fill",
        "unknown_fill",
        "partial_fill",
        "unknown_fill",
    ]


def test_empty_funnel_and_sequence_overwrite_old_files(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(prepare, "ANALYSIS_START", date(2026, 9, 7))
    monkeypatch.setattr(prepare, "ANALYSIS_END", date(2026, 9, 7))
    monkeypatch.setattr(prepare, "_load_snapshot_payload", lambda *a: (None, "none"))
    monkeypatch.setattr(prepare, "_load_pipeline_rows", lambda *a: ([], "none"))
    for name in ("funnel_fact.csv", "sequence_fact.csv"):
        (tmp_path / name).write_text("old\n1\n")
    prepare.build_funnel_fact()
    prepare.build_sequence_fact()
    assert pd.read_csv(tmp_path / "funnel_fact.csv").empty
    assert pd.read_csv(tmp_path / "sequence_fact.csv").empty


def test_tiny_positive_net_cadence_is_research_not_runtime_permission(tmp_path):
    write_report(tmp_path, "2026-09-04")
    write_report(tmp_path, count=0)
    evidence = econ.build_evidence(tmp_path, "2026-09-04", "2026-09-07")
    cohort = evidence["windows"]["rolling_10d"]["cohorts"][0]
    assert cohort["equal_weight_avg_profit_pct"] == pytest.approx(0.002)
    assert cohort["completed_per_valid_source_day"] == 1
    assert cohort["net_krw_per_valid_source_day"] == 1
    assert cohort["net_pnl_krw"] == 2  # No second slippage subtraction.
    assert evidence["windows"]["daily"]["completed_count"] == 0
    assert (
        econ.profit_followups(evidence)[0]["owner_family"]
        == "score65_74_recovery_probe"
    )
    assert not econ.profit_followups(evidence)[0]["allowed_runtime_apply"]
    assert evidence["counterfactual_incremental_ev"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("fees_taxes_krw", None),
        ("fees_taxes_krw", -1),
        ("realized_net_pnl_krw", 999),
        ("realized_net_pnl_krw", True),
        ("entry_notional_krw", 0),
        ("right_censored", True),
        ("fill_completion_class", "unknown"),
        ("lifecycle_population_scope", "sim"),
        ("session_bucket", "nxt"),
        ("promotion_evidence_eligible", False),
        ("final_exit_at", "2026-09-08T09:10:00+09:00"),
    ],
)
def test_invalid_row_isolated_without_blocking_good_row(tmp_path, field, value):
    write_report(tmp_path, mutate=lambda r: r["rows"][0].update({field: value}))
    result = econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")
    assert len(result["observations"]) == 1
    assert result["excluded_rows"]["2026-09-07"]


def test_no_winner_only_candidate_and_partial_kept_separate(tmp_path):
    def mutate(r):
        row = r["rows"][1]
        row.update(realized_net_pnl_krw=-10, exit_amount_krw=50010)

    write_report(tmp_path, mutate=mutate)
    evidence = econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")
    assert econ.profit_followups(evidence) == []
    write_report(
        tmp_path,
        mutate=lambda r: r["rows"][1].update(fill_completion_class="partial_only"),
    )
    assert (
        len(
            econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")["windows"][
                "daily"
            ]["cohorts"]
        )
        == 2
    )


def test_duplicate_identity_all_copies_excluded_and_hash_tamper_blocked(tmp_path):
    write_report(
        tmp_path,
        count=3,
        mutate=lambda r: r["rows"][1].update(
            main_lifecycle_id=r["rows"][0]["main_lifecycle_id"]
        ),
    )
    assert (
        len(econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")["observations"])
        == 1
    )
    p = tmp_path / "main_scalping_lifecycle_paired_2026-09-07.json"
    r = json.loads(p.read_text())
    r["rows"][2]["realized_net_pnl_krw"] = 100000
    p.write_text(json.dumps(r))
    result = econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")
    assert not result["observations"]
    assert result["excluded_source_dates"]["2026-09-07"] == "invalid_source_contract"


def test_rolling_window_not_all_history_and_old_missing_day_does_not_block(tmp_path):
    write_report(tmp_path, "2026-06-08", count=5)
    write_report(tmp_path, "2026-09-07", count=1)
    e = econ.build_evidence(tmp_path, "2026-04-01", "2026-09-07")
    assert e["windows"]["cumulative"]["completed_count"] == 6
    assert e["windows"]["rolling_10d"]["completed_count"] == 1
    assert len(e["windows"]["rolling_10d"]["expected_dates"]) == 10
    assert min(e["windows"]["cumulative"]["expected_dates"]) >= "2026-06-05"
    assert e["status"] == "available"


def test_retired_adm_contract_has_no_repair_or_sample_wait():
    c = automation._entry_adm_source_quality_contract(
        {"status": "retired", "available": False}
    )
    assert c["blocked_reasons"] == []
    assert c["sample_floor_status"] == "not_applicable"
    item = dict(
        review_id="ai_review_gap",
        reason="Missing source and sample floor",
        required_followup=[
            "scalping_pattern_lab_automation_source_report_missing",
            "scalping_pattern_lab_automation_sample_floor_missing",
        ],
    )
    p = dict(
        final_conclusions=[item],
        interpretation={
            "review_items": [
                dict(review_id="ai_review_gap", reason="scalp_entry_adm source missing")
            ]
        },
    )
    ctx = {
        "sources": {
            "scalping_pattern_lab_automation": {
                "summary": {"source_quality_contracts": {"scalp_entry_adm": c}}
            }
        }
    }
    result = ai._apply_source_contract_resolutions(p, ctx)
    assert (
        result["final_conclusions"][0]["source_context_resolution"]["status"]
        == "resolved_as_retired_not_applicable"
    )
    p["final_conclusions"][0]["required_followup"].append("active_entry_cost_gap")
    result = ai._apply_source_contract_resolutions(p, ctx)
    assert "source_context_resolution" not in result["final_conclusions"][0]


def test_no_retired_or_zero_event_recommendation():
    seq = pd.DataFrame(
        [
            dict(
                rebase_integrity_flag=True,
                partial_then_expand_flag=True,
                same_symbol_repeat_flag=True,
            )
        ]
    )
    backlog = analysis.build_ev_backlog(
        [], [], [{"blocker": "latency guard miss", "total_blocked": 9000}], seq
    )
    text = json.dumps(backlog)
    assert "fallback" not in text and "latency_canary" not in text and "50" not in text
    findings = automation._extract_findings(
        "claude",
        {"opportunity_cost": [{"blocker": "liquidity gate miss", "total_blocked": 0}]},
        {},
    )
    assert not findings


def seed_v3_lab(tmp_path):
    root = tmp_path / "lab"
    out = root / "outputs"
    out.mkdir(parents=True)
    ev = {
        "schema_version": 3,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "date": "2026-09-08",
        "source_isolation": {
            "schema": "pattern_lab_date_isolation_v1",
            "target_date": "2026-09-08",
            "status": "isolated",
            "included_dates": ["2026-09-07"],
            "excluded_dates": ["2026-09-08"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "ev_backlog": [
            {
                "title": "AI threshold miss EV recovery",
                "expected_effect": "research",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ],
    }
    for name, value in (
        ("ev_analysis_result.json", ev),
        ("tuning_observability_summary.json", {}),
        ("source_manifest.json", {}),
    ):
        (out / name).write_text(json.dumps(value))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    (out / "run_manifest.json").write_text(
        json.dumps(
            {
                "run_at": "2026-09-08T21:00:00+09:00",
                "analysis_end": "2026-09-08",
                "history_coverage_end": "2026-09-07",
                "history_coverage_ok": False,
                "generation_sha256": hashes,
            }
        )
    )
    return root


def test_single_lab_v3_isolated_history_and_generation_binding(tmp_path, monkeypatch):
    root = seed_v3_lab(tmp_path)
    monkeypatch.setattr(automation, "CLAUDE_LAB_DIR", root)
    monkeypatch.setattr(automation, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "report")
    r = automation.build_scalping_pattern_lab_automation_report("2026-09-08")
    assert r["existing_family_inputs"]
    assert not r["allowed_runtime_apply"]
    (root / "outputs/ev_analysis_result.json").write_text("{}")
    r = automation.build_scalping_pattern_lab_automation_report("2026-09-08")
    assert not r["existing_family_inputs"]
    assert r["rejected_findings"]


@pytest.mark.parametrize("tamper", [False, True])
def test_currentness_consumer_checks_generation_without_economic_floor(
    tmp_path, monkeypatch, tamper
):
    root = seed_v3_lab(tmp_path)
    out = root / "outputs"
    monkeypatch.setattr(currentness, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(currentness, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        currentness,
        "_lab_paths",
        lambda: {
            "claude_scalping": {
                "lab_dir": root,
                "analysis_result": out / "ev_analysis_result.json",
                "manifest": out / "run_manifest.json",
                "observability": out / "tuning_observability_summary.json",
            }
        },
    )
    if tamper:
        (out / "source_manifest.json").write_text('{"different_generation": true}')
    report = currentness.build_pattern_lab_currentness_audit(
        "2026-09-08", include_swing=False
    )
    check = next(
        c
        for c in report["checks"]
        if c["check_id"] == "claude_small_net_generation_contract"
    )
    assert check["status"] == ("fail" if tamper else "pass")


def test_isolated_generation_profit_handoff_and_second_pass_fixed_point(
    tmp_path, monkeypatch
):
    root = tmp_path / "lab"
    out = root / "outputs"
    out.mkdir(parents=True)
    day = "2026-09-08"
    monkeypatch.setattr(analysis.config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(analysis.config, "ANALYSIS_START", date(2026, 9, 7))
    monkeypatch.setattr(analysis.config, "ANALYSIS_END", date(2026, 9, 8))
    monkeypatch.setattr(analysis, "OUTPUT_DIR", out)
    monkeypatch.setattr(payload, "OUTPUT_DIR", out)
    monkeypatch.setattr(payload, "ANALYSIS_START", date(2026, 9, 7))
    monkeypatch.setattr(payload, "ANALYSIS_END", date(2026, 9, 8))
    monkeypatch.setattr(payload, "_load_feedback_sources", lambda: {})
    monkeypatch.setattr(automation, "CLAUDE_LAB_DIR", root)
    monkeypatch.setattr(
        automation, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "automation"
    )
    write_report(tmp_path / "data/report/main_scalping_lifecycle_paired", "2026-09-07")
    write_report(tmp_path / "data/report/main_scalping_lifecycle_paired", day)
    pd.DataFrame(columns=prepare.TRADE_FACT_COLUMNS).to_csv(
        out / "trade_fact.csv", index=False
    )
    pd.DataFrame(columns=["date"]).to_csv(out / "funnel_fact.csv", index=False)
    pd.DataFrame(columns=["trade_id", "date"]).to_csv(
        out / "sequence_fact.csv", index=False
    )
    (out / "source_manifest.json").write_text(
        json.dumps(
            {"target_date": day, "covered_dates": [], "history_coverage_ok": False}
        )
    )

    def observe(**kwargs):
        result = {
            "buy_recovery_canary": {
                "total_candidates": 0,
                "recovery_check_candidates": 0,
                "recovery_promoted_candidates": 0,
                "submitted_candidates": 0,
                "blocked_ai_score_share_pct": 0,
            },
            "entry_funnel": {
                "gatekeeper_eval_ms_p95": 0,
                "budget_pass_to_submitted_rate": 0,
            },
            "priority_findings": [],
        }
        (out / "tuning_observability_summary.json").write_text(json.dumps(result))
        return result

    monkeypatch.setattr(payload, "write_tuning_observability_outputs", observe)
    first = analysis.main()
    assert (
        first["economics"]["windows"]["rolling_10d"]["cohorts"][0]["net_pnl_krw"] == 4
    )
    payload.main()
    assert "순이익·거래빈도" in (out / "final_review_report_for_lead_ai.md").read_text()
    r = automation.build_scalping_pattern_lab_automation_report(day)
    assert r["existing_family_inputs"][0]["family"] == "score65_74_recovery_probe"
    assert r["economic_evidence"]["claude"]["windows"]["daily"]["completed_count"] == 2
    by_id, by_slug = workorder._finding_maps(r)
    item = workorder._classify_order(
        r["code_improvement_orders"][0],
        finding_by_order_id=by_id,
        finding_by_title_slug=by_slug,
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert item.decision == "attach_existing_family"
    assert not item.order["allowed_runtime_apply"]
    second = analysis.main()
    payload.main()
    second_auto = automation.build_scalping_pattern_lab_automation_report(day)
    assert first["ev_backlog"] == second["ev_backlog"]
    assert r["code_improvement_orders"] == second_auto["code_improvement_orders"]


def test_missing_funnel_metrics_are_not_zero():
    row = prepare._parse_performance_tuning({"metrics": {}}, "2026-09-08", "local")
    assert row["liquidity_block_events"] is None
    assert analysis.decompose_opportunity_cost(pd.DataFrame([row])) == []
    row["latency_block_events"] = 2
    result = analysis.decompose_opportunity_cost(pd.DataFrame([row]))
    assert result[0]["block_ratio"] is None


def test_capital_time_is_diagnostic_not_a_new_approval_hurdle(tmp_path):
    write_report(
        tmp_path, mutate=lambda r: r["rows"][0].update(capital_time_krw_hours=None)
    )
    e = econ.build_evidence(tmp_path, "2026-09-07", "2026-09-07")
    c = e["windows"]["daily"]["cohorts"][0]
    assert c["completed_count"] == 2
    assert c["net_krw_per_capital_hour"] is None
    assert econ.profit_followups(e)


@pytest.mark.parametrize(
    "change",
    [
        {"runtime_effect": True},
        {"allowed_runtime_apply": "false"},
        {"ev_backlog": None},
    ],
)
def test_v3_malformed_authority_or_backlog_fails_closed(tmp_path, change):
    root = seed_v3_lab(tmp_path)
    ev_path = root / "outputs/ev_analysis_result.json"
    ev = json.loads(ev_path.read_text())
    ev.update(change)
    ev_path.write_text(json.dumps(ev))
    manifest_path = root / "outputs/run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["generation_sha256"][ev_path.name] = hashlib.sha256(
        ev_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    assert not automation._load_lab("claude", root, "2026-09-08")["findings"]


def test_twenty_valid_empty_source_days_trigger_review_not_buy(tmp_path):
    for day in econ.trading_dates("2026-06-05", "2026-07-10")[:20]:
        write_report(tmp_path, day, count=0)
    e = econ.build_evidence(tmp_path, "2026-06-05", "2026-07-10")
    assert e["maintenance_review_due"]
    assert not e["allowed_runtime_apply"]
    assert not econ.profit_followups(e)


def test_ai_context_receives_economics_and_scalping_native_orders(
    tmp_path, monkeypatch
):
    payloads = {
        "pattern_lab_currentness_audit": {"checks": []},
        "scalping_pattern_lab_automation": {
            "economic_evidence": {
                "claude": {
                    "target_date": "2026-09-08",
                    "sources": {"2026-09-07": {"sha256": "a" * 64}},
                    "windows": {
                        "rolling_10d": {
                            "cohorts": [
                                {
                                    "net_pnl_krw": 17,
                                    "notional_weighted_ev_pct": 0.002,
                                    "completed_per_valid_source_day": 10,
                                }
                            ]
                        }
                    },
                    "maintenance_review_due": True,
                }
            }
        },
        "code_improvement_workorder": {
            "orders": [
                {
                    "order_id": f"native-{i}",
                    "source_report_type": "scalping_pattern_lab_automation",
                    "decision": "attach_existing_family",
                    "evidence": [{"net_pnl_krw": 17}],
                }
                for i in range(21)
            ]
        },
    }
    monkeypatch.setattr(
        ai, "_source_paths", lambda *a, **kw: {k: tmp_path / k for k in payloads}
    )
    monkeypatch.setattr(ai, "_load_json", lambda p: payloads[p.name])
    context = ai._build_input_context("2026-09-08", include_swing=False)
    economics = context["sources"]["scalping_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ]["claude"]
    assert economics["windows"]["rolling_10d"]["cohorts"][0]["net_pnl_krw"] == 17
    assert not economics["allowed_runtime_apply"]
    assert context["pattern_lab_workorder_count"] == 21
    assert len(context["pattern_lab_workorder_ids"]) == 21
    assert context["pattern_lab_workorder_omitted_detail_count"] == 1
    assert (
        context["pattern_lab_workorder_orders"][0]["evidence"][0]["net_pnl_krw"] == 17
    )


def test_maintenance_produces_a_native_design_review_not_another_solo_wait():
    evidence = {
        "maintenance_review_due": True,
        "sources": {str(i): {} for i in range(20)},
    }
    row = econ.maintenance_followups(evidence)[0]
    finding = automation._finding_from_backlog_item("claude", row)
    finding.update(
        source_labs=["claude"], confidence="solo", evidence=[finding["evidence"]]
    )
    order = automation._code_improvement_orders([], [finding])[0]
    result = workorder._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert order["order_id"] == "order_pattern_lab_bounded_maintenance_review"
    assert result.decision == "design_family_candidate"
    assert "implementation_status" not in order
    assert not order["allowed_runtime_apply"]


@pytest.mark.parametrize("has_alternative", [True, False])
def test_lab_reads_same_generation_daily_owner_evaluation(tmp_path, has_alternative):
    from src.tests.test_score_recovery_net_approval import (
        real_comparison_metrics,
        real_metrics,
        PROFILE,
    )
    from src.engine.scalping.score_recovery_economics import evaluate_policy

    metrics = real_comparison_metrics() if has_alternative else real_metrics(net=1)
    decision = evaluate_policy(metrics)
    root = tmp_path / "threshold_cycle_calibration"
    root.mkdir()
    path = root / "threshold_cycle_calibration_2026-09-08_postclose.json"
    report = {
        "date": "2026-09-08",
        "run_phase": "postclose",
        "calibration_candidates": [
            {
                "family": "score65_74_recovery_probe",
                "current_values": PROFILE,
                "source_metrics": metrics,
                "sample_floor": 20,
                "condition_feasibility": decision,
            }
        ],
    }
    path.write_text(json.dumps(report))
    evidence = {"target_date": "2026-09-08", "maintenance_review_due": True}
    econ.attach_owner_evaluation(evidence, tmp_path)
    assert evidence["owner_evaluation"]["status"] == "owner_evaluation_verified"
    # A profitable baseline alone does not close the maintenance question of
    # whether the lab can produce a useful improvement.
    assert evidence["maintenance_review_due"] is (not has_alternative)
    report["calibration_candidates"][0]["condition_feasibility"]["ready"] = False
    path.write_text(json.dumps(report))
    evidence["maintenance_review_due"] = True
    econ.attach_owner_evaluation(evidence, tmp_path)
    assert evidence["maintenance_review_due"]
    assert evidence["owner_evaluation"]["status"] == "owner_report_missing_or_invalid"


@pytest.mark.parametrize("missing", ["date", "rec_date"])
def test_missing_date_never_joins_fill_by_trade_id(tmp_path, monkeypatch, missing):
    monkeypatch.setattr(prepare, "OUTPUT_DIR", tmp_path)
    trades = pd.DataFrame(
        [dict(trade_id=1, rec_date="2026-09-07", cohort="unknown_fill")]
    )
    sequence = pd.DataFrame(
        [dict(trade_id=1, date="2026-09-08", observed_full_fill=True)]
    )
    if missing == "date":
        sequence = sequence.drop(columns="date")
    else:
        trades = trades.drop(columns="rec_date")
    assert (
        prepare.enrich_trade_cohort(trades, sequence).iloc[0].cohort == "unknown_fill"
    )


def test_mixed_active_gap_in_interpretation_is_not_retired():
    payload = {
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "reason": "Missing source and sample floor",
                "required_followup": [
                    "scalping_pattern_lab_automation_source_report_missing"
                ],
            }
        ],
        "interpretation": {
            "review_items": [
                {
                    "review_id": "ai_review_gap",
                    "reason": "scalp_entry_adm source missing and active entry cost source missing",
                }
            ]
        },
    }
    context = {
        "sources": {
            "scalping_pattern_lab_automation": {
                "summary": {
                    "source_quality_contracts": {
                        "scalp_entry_adm": {
                            "source_contract_status": "retired",
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                        }
                    },
                }
            }
        }
    }
    result = ai._apply_source_contract_resolutions(payload, context)
    assert "source_context_resolution" not in result["final_conclusions"][0]


@pytest.mark.parametrize("sequence_date", [None, "", "2026-09-08"])
def test_loss_diagnostic_flags_require_exact_date(sequence_date):
    trades = pd.DataFrame(
        [
            dict(
                trade_id=1,
                rec_date="2026-09-07",
                status="COMPLETED",
                profit_valid_flag=True,
                profit_rate=-1,
                cohort="unknown_fill",
                exit_rule="test",
            )
        ]
    )
    sequence = pd.DataFrame(
        [
            dict(
                trade_id=1,
                date=sequence_date,
                partial_then_expand_flag=True,
            )
        ]
    )
    result = analysis.extract_loss_patterns(trades, sequence)
    assert (
        result[0]["preconditions"].get("partial_then_expand_flag", {}).get("count", 0)
        == 0
    )
