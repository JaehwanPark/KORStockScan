"""Cost-inclusive small-edge approval, exact lineage and authority regression."""

import copy
import json
from datetime import date, timedelta

import pytest

from src.engine.scalping import score_recovery_economics as econ
from src.engine import daily_threshold_cycle_report as daily
from src.engine import threshold_cycle_preopen_apply as preopen

PROFILE = dict(
    min_score=69,
    max_score=74,
    min_buy_pressure=65,
    min_tick_accel=1.2,
    min_micro_vwap_bp=10,
)


def test_empty_valid_days_trigger_maintenance_not_automatic_entry():
    from src.utils.market_day import is_krx_trading_day

    day = date(2026, 6, 5)
    books = []
    while len(books) < 20:
        if is_krx_trading_day(day):
            r = signed_report(day.isoformat(), count=0)
            books.append(econ.evidence_book(r, r["target_date"]))
        day += timedelta(days=1)
    decision = econ.evaluate(
        {
            "score_recovery_current_profile": PROFILE,
            "score_recovery_real_economics": econ.merge_books(books),
        }
    )
    assert not decision["ready"]
    natural = decision["natural_acceptance"]
    assert natural["valid_source_day_count"] == 20
    assert natural["maintenance_review_due"]
    assert natural["next_action"] == "review_source_or_integrate_or_retire"
    assert not natural["allowed_runtime_apply"]


def signed_report(day="2026-09-07", count=10, net=30):
    rows = []
    for i in range(count):
        rows.append(
            dict(
                main_lifecycle_id=f"{day}-id-{i}",
                trade_date=day,
                score_recovery_profile=PROFILE,
                score_recovery_profile_conflict=False,
                promotion_evidence_eligible=True,
                promotion_blockers=[],
                lifecycle_population_scope="real_submitted",
                right_censored=False,
                final_exit_at=f"{day}T09:01:00+09:00",
                scale_in_fill_qty=0,
                fill_completion_class="full_only",
                venue="KRX",
                session_bucket="krx_regular",
                entry_notional_krw=50000,
                exit_amount_krw=50020 + net,
                fees_taxes_krw=20,
                slippage_krw=5,
                realized_net_pnl_krw=net,
                capital_time_krw_hours=50000 / 60,
            )
        )
    return sign(
        dict(
            schema="main_scalping_lifecycle_paired_daily_v2",
            target_date=day,
            global_source_quality_gate_pass=True,
            rows=rows,
        )
    )


def sign(report):
    for key in ("content_sha256", "report_content_sha256", "artifact_content_sha256"):
        report.pop(key, None)
    sha = econ.digest(report)
    report.update(content_sha256=sha, report_content_sha256=sha)
    report["artifact_content_sha256"] = econ.digest(report)
    return report


def real_metrics(net=30):
    reports = [signed_report("2026-09-04", net=net), signed_report(net=net)]
    return dict(
        score_recovery_current_profile=PROFILE,
        score_recovery_real_economics=econ.merge_books(
            [econ.evidence_book(r, r["target_date"]) for r in reports]
        ),
    )


def candidate(metrics=None):
    return dict(
        family="score65_74_recovery_probe",
        sample_count=20,
        sample_floor=20,
        current_values={**PROFILE, "enabled": False},
        recommended_values={**PROFILE, "enabled": True},
        source_metrics=metrics or real_metrics(),
    )


def test_small_real_net_without_ten_minute_or_drought_qualifies():
    metrics = real_metrics()
    metrics.update(
        submitted_to_budget_unique_pct=80,
        score60_74_avg_close_10m_pct=-1,
        score60_74_avg_mfe_10m_pct=0.1,
    )
    decision = econ.evaluate(metrics)
    assert decision["ready"]
    assert decision["cohorts"][0]["mean_net_pct"] == pytest.approx(0.06)
    assert decision["cohorts"][0]["net_krw"] == 600
    assert daily._score65_74_entry_unlock_probe_ready(
        metrics, sample_count=20, sample_floor=20
    )
    assert preopen._score65_74_entry_unlock_candidate(candidate(metrics))


@pytest.mark.parametrize("net", [0, -1])
def test_nonpositive_net_is_not_approved(net):
    assert not econ.evaluate(real_metrics(net))["ready"]


def test_many_small_wins_cannot_hide_large_loss():
    metrics = real_metrics()
    row = next(iter(metrics["score_recovery_real_economics"]["observations"].values()))
    row.update(net_krw=-2000, net_return_pct=-4)
    assert not econ.evaluate(metrics)["ready"]


def test_positive_mean_without_dispersion_margin_is_not_approved():
    metrics = real_metrics()
    row = next(iter(metrics["score_recovery_real_economics"]["observations"].values()))
    row.update(net_krw=-500, net_return_pct=-1)
    decision = econ.evaluate(metrics)
    assert decision["cohorts"][0]["mean_net_pct"] > 0
    assert not decision["ready"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("fees_taxes_krw", None),
        ("fees_taxes_krw", float("nan")),
        ("realized_net_pnl_krw", 25),
        ("entry_notional_krw", 0),
        ("fill_completion_class", "partial_then_full"),
        ("right_censored", True),
        ("promotion_evidence_eligible", False),
        ("scale_in_fill_qty", 1),
        ("score_recovery_profile_conflict", True),
    ],
)
def test_missing_cost_double_slippage_partial_or_mixed_never_approve(field, value):
    report = signed_report(count=1)
    report["rows"][0][field] = value
    if isinstance(value, float) and value != value:
        # Nonfinite JSON fails the report hash/serialization contract too.
        assert not econ.evidence_book(report, "2026-09-07")["observations"]
    else:
        assert not econ.evidence_book(sign(report), "2026-09-07")["observations"]


def test_hash_date_baseline_and_empty_sources():
    report = signed_report()
    assert not econ.evidence_book(report, "2026-09-08")["observations"]
    report["rows"][0]["realized_net_pnl_krw"] = 999
    assert not econ.evidence_book(report, "2026-09-07")["observations"]
    assert not econ.evidence_book(signed_report("2026-06-04"), "2026-06-04")[
        "observations"
    ]
    assert econ.evidence_book({}, "2026-09-08")["excluded"] == {
        "paired_source_not_yet_available": 1
    }


def test_duplicate_retry_and_conflicting_generation_do_not_inflate_sample():
    report = signed_report()
    report["rows"].append(copy.deepcopy(report["rows"][0]))
    book = econ.evidence_book(sign(report), "2026-09-07")
    assert len(book["observations"]) == 9
    assert len(econ.merge_books([book, book])["observations"]) == 9
    other = econ.evidence_book(signed_report(net=-20), "2026-09-07")
    assert not econ.merge_books([book, other])["observations"]


def test_cf_only_and_policy_changes_cannot_be_promoted():
    metrics = dict(
        score60_74_cost_adjusted_sample_count=1000,
        score60_74_avg_cost_adjusted_expected_ev_pct=10,
        score60_74_cost_contract_complete=True,
    )
    assert not preopen._score65_74_entry_unlock_candidate(candidate(metrics))
    c = candidate()
    c["recommended_values"]["min_score"] = 60
    assert not preopen._score65_74_entry_unlock_candidate(c)


def test_profile_venue_dates_and_runtime_scope_are_separate():
    metrics = real_metrics()
    observations = metrics["score_recovery_real_economics"]["observations"]
    for i, row in enumerate(observations.values()):
        if i < 10:
            row.update(venue="NXT", session="nxt")
    assert not econ.evaluate(metrics)["ready"]
    metrics = real_metrics()
    version = econ.approval_version(metrics)
    assert econ.runtime_scope_allowed(
        version,
        PROFILE,
        {"effective_venue": "KRX", "market_session_bucket": "krx_regular"},
    )
    assert not econ.runtime_scope_allowed(
        version, PROFILE, {"effective_venue": "NXT", "market_session_bucket": "nxt"}
    )
    assert not econ.runtime_scope_allowed(version, {**PROFILE, "min_score": 60}, {})
    assert not econ.runtime_scope_allowed(
        "score_recovery_real_net_v1:broken", PROFILE, {}
    )
    assert econ.runtime_scope_allowed(
        "score69_74:operator_override:2026-07-04", PROFILE, {}
    )


def test_daily_book_merge_preserves_full_census_and_current_profile():
    metrics = real_metrics()
    merged = daily._aggregate_metric_dicts([metrics, metrics])
    merged["score_recovery_current_profile"] = PROFILE
    assert len(merged["score_recovery_real_economics"]["observations"]) == 20
    assert econ.evaluate(merged)["ready"]
    assert (
        daily._source_sample_count_for_family("score65_74_recovery_probe", merged) == 20
    )


def test_real_producer_preserves_profile_and_reconciles_actual_price_pnl(tmp_path):
    from src.tests.test_main_lifecycle_paired import _complete_lifecycle, TARGET_DATE
    from src.engine.scalping import main_lifecycle_journal as journal
    from src.engine.scalping import main_lifecycle_paired as paired

    events = _complete_lifecycle("score", include_scale=True)
    for event in events:
        if event["stage"] == "entry_decision":
            event["data"].update(
                score_recovery_applied=True, score_recovery_profile=json.dumps(PROFILE)
            )
        if "realized_net_pnl_krw" in event["data"]:
            event["data"]["realized_net_pnl_krw"] = 30
        event["session_bucket"] = "krx_regular"
        args = {
            key: event[key]
            for key in (
                "main_lifecycle_id",
                "record_id",
                "stock_code",
                "attempt_id",
                "trade_date",
                "stage",
                "observed_at",
                "venue",
                "session_bucket",
                "data",
            )
        }
        assert journal.append_transition_safe(
            **args, output_path=tmp_path / "journal.jsonl"
        )
    report = paired.build_daily_report(
        TARGET_DATE,
        source_path=tmp_path / "journal.jsonl",
        write=False,
        reviewed_cost_profile_sha256="a" * 64,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256="b" * 64,
        symbol_master_artifact_verified=True,
    )
    row = report["rows"][0]
    assert row["score_recovery_profile"] == PROFILE
    assert row["entry_notional_krw"] == 50000
    assert row["exit_amount_krw"] == 50050
    assert row["promotion_evidence_eligible"] is True
    book = econ.evidence_book(report, TARGET_DATE)
    assert len(book["observations"]) == 1
    assert next(iter(book["observations"].values()))["net_krw"] == 30


def test_realized_net_does_not_require_ai_replay_depth_or_duplicate_slippage_basis():
    report = signed_report()
    for row in report["rows"]:
        row["promotion_evidence_eligible"] = False
        row["promotion_blockers"] = [
            "bbo_coverage_below_95pct",
            "depth_coverage_below_90pct",
            "slippage_basis_source_exit_qty_coverage_incomplete",
        ]
    assert len(econ.evidence_book(sign(report), "2026-09-07")["observations"]) == 10
    report["rows"][0]["promotion_blockers"].append(
        "broker_execution_raw_provenance_gap"
    )
    assert len(econ.evidence_book(sign(report), "2026-09-07")["observations"]) == 9


def test_observed_partial_losses_are_separate_and_veto_full_only_survivor_bias():
    metrics = real_metrics()
    report = signed_report(count=1, net=-10)
    report["rows"][0]["fill_completion_class"] = "partial_then_full"
    report["rows"][0]["main_lifecycle_id"] = "partial-id"
    partial = econ.evidence_book(sign(report), "2026-09-07")["partial_observations"]
    assert len(partial) == 1
    metrics["score_recovery_real_economics"]["partial_observations"] = partial
    decision = econ.evaluate(metrics)
    assert decision["sample_count"] == 20
    assert decision["cohorts"][0]["partial_loss_veto"] is True
    assert not decision["ready"]


def test_new_pipeline_stage_preserves_scalar_profile_and_old_stage_is_not_remapped():
    from src.tests.test_main_lifecycle_paired import _pipeline_event, TARGET_DATE
    from src.engine.scalping import main_lifecycle_paired as paired
    from src.engine.scalping.main_lifecycle_journal import PIPELINE_STAGE_MAP

    stock = {
        "id": 123,
        "code": "005930",
        "scanner_promotion_id": "promotion-1",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    event = _pipeline_event(
        stock=stock,
        pipeline="ENTRY_PIPELINE",
        source_stage="score_recovery_real_economics_observed",
        second=1,
        fields={"applied": True, "score_recovery_applied_profile": json.dumps(PROFILE)},
    )
    transition, error, _ = paired._validated_pipeline_transition(
        event, target_date=TARGET_DATE
    )
    assert error is None
    assert transition["data"]["score_recovery_applied"] is True
    assert json.loads(transition["data"]["score_recovery_profile"]) == PROFILE
    assert ("ENTRY_PIPELINE", "score65_74_recovery_probe") not in PIPELINE_STAGE_MAP


def test_preopen_emits_complete_existing_profile_and_scoped_version(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(preopen, "RUNTIME_ENV_DIR", tmp_path)
    c = candidate()
    c.update(
        stage="entry",
        priority=10,
        allowed_runtime_apply=True,
        calibration_state="adjust_up",
        sample_floor_status="ready",
        target_env_keys=daily.CALIBRATION_FAMILY_METADATA[c["family"]][
            "target_env_keys"
        ],
    )
    selected, decisions, env = preopen._select_auto_apply_candidates(
        [c], ai_review={}, require_ai=False, target_date="2026-09-08", operator_locks=[]
    )
    assert decisions[0]["selected"] is True, decisions
    assert selected
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE"] == "69"
    version = env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION"]
    assert version == econ.approval_version(c["source_metrics"])
    assert decisions[0]["threshold_version"] == version
    assert not any(k.startswith("AI_SCORE") for k in env)
    assert not preopen._score65_74_entry_unlock_candidate(c, target_date="2026-09-07")


def test_daily_primary_window_uses_real_book_not_broad_snapshot_volume():
    c = candidate()
    c.update(
        stage="entry",
        priority=10,
        allowed_runtime_apply=True,
        calibration_state="hold_sample",
        sample_floor_status="hold_sample",
        window_policy={"primary": "rolling_20d"},
        source_sample_count=0,
    )
    metrics = real_metrics()
    daily._refresh_candidate_from_primary_window(
        c,
        primary_snapshot={"current": {**PROFILE, "min_score": 60}, "recommended": {}},
        primary_source_metrics=metrics,
        primary_sample_count=20,
        primary_ready=True,
        primary_window="rolling_20d",
    )
    assert c["calibration_state"] == "adjust_up"
    assert c["recommended_values"]["min_score"] == 69
    assert c["recommended_values"]["enabled"] is True
    assert preopen._score65_74_entry_unlock_candidate(c)


def test_loader_consumes_exact_paired_source_without_wait_cf(tmp_path, monkeypatch):
    monkeypatch.setattr(daily, "REPORT_DIR", tmp_path)
    path = (
        tmp_path
        / "main_scalping_lifecycle_paired"
        / "main_scalping_lifecycle_paired_2026-09-07.json"
    )
    path.parent.mkdir()
    path.write_text(json.dumps(signed_report()), encoding="utf-8")
    result = daily._summarize_holding_exit_report_sources("2026-09-07")
    metrics = result["source_metrics"]["buy_score65_74"]
    assert len(metrics["score_recovery_real_economics"]["observations"]) == 10
    assert result["sources"]["main_scalping_lifecycle_paired"]["loaded"] is True


def test_verified_preopen_profile_is_used_instead_of_postclose_defaults(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(daily, "THRESHOLD_APPLY_PLAN_DIR", tmp_path)
    env = {
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_" + k.upper(): str(v)
        for k, v in PROFILE.items()
    }
    env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP"] = "0"
    env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP"] = (
        "10"
    )
    payload = {
        "target_date": "2026-09-08",
        "runtime_env_overrides": env,
        "runtime_env_handoff_verification": {
            "status": "pass",
            "passed": True,
            "target_date": "2026-09-08",
            "selected_families": ["score65_74_recovery_probe"],
        },
        "auto_apply_decisions": [
            {"family": "score65_74_recovery_probe", "selected": True}
        ],
    }
    (tmp_path / "threshold_apply_2026-09-08.json").write_text(json.dumps(payload))
    observation = daily._load_same_day_runtime_apply_observation("2026-09-08")
    assert (
        observation["families"]["score65_74_recovery_probe"]["current_profile"]
        == PROFILE
    )
    report = daily.build_daily_threshold_cycle_report(
        "2026-09-08",
        pipeline_loader=lambda day: [],
        report_source_loader=lambda day: {
            "source_metrics": {"buy_score65_74": real_metrics()}
        },
        completed_rows_loader=lambda start, end: [],
        runtime_apply_observation=observation,
    )
    c = next(
        c
        for c in report["calibration_candidates"]
        if c["family"] == "score65_74_recovery_probe"
    )
    assert c["current_values"]["min_score"] == 69
    assert c["calibration_state"] == "adjust_up"
    assert (
        c["source_metrics"]["current_profile_source"] == "verified_same_day_preopen_env"
    )


@pytest.mark.parametrize(
    "bad", [None, [], "invalid", 1, {"schema": econ.SCHEMA, "observations": []}]
)
def test_malformed_book_cannot_crash_or_approve(bad):
    metrics = real_metrics()
    metrics["score_recovery_real_economics"] = bad
    assert not econ.evaluate(metrics)["ready"]
    assert not preopen._score65_74_entry_unlock_candidate(candidate(metrics))
    econ.merge_books([bad])


def test_none_parent_isolated_when_aggregating_real_book():
    result = daily._aggregate_metric_dicts([None, real_metrics()])
    result["score_recovery_current_profile"] = PROFILE
    assert econ.evaluate(result)["ready"]


def test_sub_won_reconciliation_tolerance_cannot_invent_positive_net():
    report = signed_report(count=1, net=0)
    report["rows"][0]["realized_net_pnl_krw"] = 0.005
    book = econ.evidence_book(sign(report), "2026-09-07")
    assert next(iter(book["observations"].values()))["net_krw"] == 0


def test_live_decision_rejects_unapproved_scope_before_other_entry_checks(monkeypatch):
    from src.engine import sniper_state_handlers as runtime

    metrics = real_metrics()
    values = {
        "AI_SCORE65_74_RECOVERY_PROBE_" + key.upper(): value
        for key, value in PROFILE.items()
    }
    values["AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION"] = econ.approval_version(
        metrics
    )
    monkeypatch.setattr(
        runtime, "_rule", lambda key, default=None: values.get(key, default)
    )
    monkeypatch.setattr(runtime, "_rule_bool", lambda key, default=False: True)
    result = runtime._score65_74_recovery_probe_decision(
        {},
        70,
        {},
        [],
        [],
        None,
        stock={"effective_venue": "NXT", "market_session_bucket": "nxt"},
        code="005930",
    )
    assert (
        result["score65_74_recovery_probe_skip_reason"]
        == "approved_profile_or_scope_mismatch"
    )
