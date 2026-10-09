"""Advisory projection and paired statistics, using retained-source fixtures."""

import copy
from datetime import datetime, timedelta

import pytest
from src.engine.scalping import market_weakness_research as R
from src.engine.market_panic_breadth_collector import market_weakness_observation_id
from src.tests.test_notify_panic_state_transition import _weakness_report

DAY = "2026-10-08"


def observation(at=DAY + "T09:00:00+09:00", state="SINGLE_MARKET_WEAKNESS"):
    o = copy.deepcopy(_weakness_report(state, 0)["market_weakness_observation"])
    o.update(target_date=at[:10], as_of=at)
    o["observation_id"] = market_weakness_observation_id(o)
    assert not R.market_weakness_observation_contract_errors(o)
    return o


def row(
    day=DAY, identity="one", outcome="W", value=2, index=-1.4, origin="natural_decision"
):
    at = day + "T09:04:00+09:00"
    result = dict(
        opportunity_id=identity,
        identity_grade="canonical",
        source_date=day,
        decision_ts=at,
        time_precision="exact",
        machine_confirmed_at=at,
        auxiliary_completed_at=None,
        entry_ask=100,
        event_id=identity,
        symbol="005930",
        listing_market="KOSPI",
        session="REGULAR",
        route="SOR",
        machine_hash="machine",
        auxiliary_hash="aux",
        auxiliary_version="prompt",
        machine_action="ENTER_NOW",
        auxiliary_verdict="PASS",
        features=dict(volume_ratio_60s=value, drawdown_5m_pct=-1),
        decision_origin=origin,
        outcome_kind="counterfactual_price_path",
        outcome=outcome,
        classification_kind="raw_market_snapshot",
        **R.AUTH,
    )
    result["joins"] = {
        str(d): dict(
            grade="B", state="WEAKNESS", index_change_pct=index, episode_id=identity
        )
        for d in R.DELAYS
    }
    result["scope_key"] = R.scope_key(result)
    return result


def registry(r):
    d = dict(
        kind="post_auxiliary_withhold_cf",
        axis="volume_ratio_60s",
        weakness_index_max_pct=-1,
        feature_max_exclusive=1,
        before="no_additional_withhold",
        after=1,
        unit="ratio",
        operator="lt",
        parent_hash="machine",
        auxiliary_hash="aux",
    )
    return R.seal(
        dict(
            scopes={
                r["scope_key"]: dict(
                    scope={
                        k: r[k]
                        for k in (
                            "symbol",
                            "listing_market",
                            "session",
                            "route",
                            "machine_hash",
                            "auxiliary_hash",
                            "decision_origin",
                            "classification_kind",
                            "outcome_kind",
                        )
                    },
                    fixed_after_source_date="2026-10-01",
                    seed_source_generation="seed",
                    candidates=[dict(candidate_id=R.digest(d), definition=d)],
                )
            },
            **R.AUTH,
        )
    )


@pytest.mark.parametrize("age,grade", [(0, "B"), (300, "B"), (301, "U"), (-1, "U")])
def test_join_freshness_and_future(age, grade):
    r = row()
    r["decision_ts"] = (
        datetime.fromisoformat(DAY + "T09:00:00+09:00") + timedelta(seconds=age)
    ).isoformat()
    assert R.join_snapshot(r, [observation()])["grade"] == grade


def test_join_market_is_listing_not_execution_and_minute_uses_bucket_start():
    r = row()
    r["listing_market"] = "KOSDAQ"
    j = R.join_snapshot(r, [observation()])
    assert j["state"] == "NEAR_WEAKNESS_BOUNDARY"
    assert j["index_change_pct"] == -0.2
    r.update(decision_ts=DAY + "T09:00:50+09:00", time_precision="minute")
    assert R.join_snapshot(r, [observation(DAY + "T09:00:10+09:00")])["grade"] == "U"
    assert R.join_snapshot(r, [observation()])["grade"] == "C"


@pytest.mark.parametrize(
    "field", ["listing_market", "machine_hash", "session", "route"]
)
def test_missing_scope_stays_unmatched(field):
    r = row()
    r[field] = None
    assert R.join_snapshot(r, [observation()])["grade"] == "U"


def test_exact_availability_and_known_delay():
    o = observation()
    o.update(
        observed_available_at=DAY + "T09:01:00+09:00",
        availability_receipt_verified=True,
    )
    assert R.join_snapshot(row(), [o])["grade"] == "A"
    o["observed_source_delay_sec"] = "181"
    assert R.join_snapshot(row(), [o])["grade"] == "U"
    o["observed_source_delay_sec"] = "180"
    assert R.join_snapshot(row(), [o])["grade"] == "A"


def test_delay_retains_original_age_and_reconstructed_does_not_replace_raw():
    r = row()
    r["decision_ts"] = DAY + "T09:02:00+09:00"
    assert R.join_snapshot(r, [observation()], delay=180)["grade"] == "U"
    o = R.reconstruct_latches([observation(), observation(DAY + "T09:01:00+09:00")])[-1]
    j = R.join_snapshot(row(), [o])
    assert j["reconstructed_active"] is True
    assert j["classification_kind"] == "raw_market_snapshot"


def test_timezone_required_and_policy_change_breaks_latch():
    assert R.timestamp(DAY + "T09:00:00") is None
    o = observation()
    o2 = observation(DAY + "T09:01:00+09:00")
    o2["hysteresis_policy"] = {"policy_hash": "changed"}
    assert R.reconstruct_latches([o2, o])[-1]["reconstructed_active"]["KOSPI"] is False


@pytest.mark.parametrize(
    "label,ask,contract,expected",
    [
        ({"status": "WIN", "delay_sec": 1800}, 100, R.LABEL, "W"),
        ({"status": "WIN", "delay_sec": 1800.01}, 100, R.LABEL, "U"),
        ({"status": "WIN"}, 100, R.LABEL, "U"),
        ({"status": "FAIL_STOP"}, 100, R.LABEL, "F"),
        ({"status": "FAIL_TIMEOUT"}, None, R.LABEL, "U"),
        ({"status": "WIN", "delay_sec": 10}, 100, dict(R.LABEL, cost_rate=0), "U"),
        (
            {"status": "UNRESOLVED", "reason": "same_bar_order_unknown"},
            100,
            R.LABEL,
            "U",
        ),
    ],
)
def test_outcome_contract(label, ask, contract, expected):
    assert R.label_value(label, ask, contract)[0] == expected


def trace():
    return dict(
        schema="ai_decision_trace_v1",
        decision_stage="entry_screen",
        decision_ts=DAY + "T09:01:00+09:00",
        stock_code="005930",
        decision_trace_id="d",
        evaluation_attempt_id="a",
        source_event_stage="native",
        entry_mechanistic_action="BLOCK",
        provider_called=False,
        entry_ai_risk_verdict="VETO",
        machine_bundle_sha256="m",
        market_data_route="krx_nxt_integrated",
        session_bucket="krx_regular",
    )


def test_trace_not_called_is_not_veto_or_zero_outcome():
    r, reason = R.project_trace(trace(), DAY, "KOSPI")
    assert reason is None
    assert r["auxiliary_verdict"] == "not_called"
    assert r["identity_grade"] == "trace_only"
    assert r["outcome"] == "U"


def test_native_auxiliary_hash_is_real_version_evidence():
    t = trace()
    t.update(
        provider_called=True,
        decision_evaluation_status="evaluated",
        result_source="live",
        prompt_version="p",
        entry_ai_risk_verdict="PASS",
        continuous_reversal_consumption={"auxiliary_component_sha256": "h"},
    )
    assert R.project_trace(t, DAY, "KOSPI")[0]["auxiliary_verdict"] == "PASS"


def test_census_deduplicates_retries_and_quarantines_only_bad_scope():
    a = R.Aggregator()
    r = row()
    a.add(r)
    retry = dict(r, decision_ts=DAY + "T09:04:03+09:00", evaluation_attempt_id="retry")
    a.add(retry)
    bad = dict(r, entry_ask=101)
    a.add(bad)
    other = row(identity="other")
    other["symbol"] = "082270"
    other["scope_key"] = R.scope_key(other)
    a.add(other)
    d = a.daily(DAY)
    assert d["census"]["projected_rows"] == 4
    assert d["census"]["duplicate_rows"] == 2
    assert list(d["scopes"]) == [other["scope_key"]]
    assert d["conflict_scopes"] == [r["scope_key"]]
    a.close()


def test_candidates_fixed_from_features_not_outcomes_and_bounded():
    a = R.Aggregator()
    for n in range(12):
        a.add(row(identity=str(n), value=n, outcome="W" if n % 2 else "F"))
    d = a.daily(DAY)
    c = R.freeze_candidates(d, "g")
    d2 = copy.deepcopy(d)
    for scope in d2["scopes"].values():
        scope["counts"] = {"outcome_W": 0}
    assert c == R.freeze_candidates(d2, "g")
    assert max(len(s["candidates"]) for s in c["scopes"].values()) <= 6
    assert all(
        s["machine_status"] == "numeric_adjustment_unidentifiable"
        for s in c["scopes"].values()
    )
    a.close()


def favorable(a):
    for day, failures in [("2026-10-06", 1), ("2026-10-07", 2), ("2026-10-08", 3)]:
        for n, outcome, value in [(n, "W", 2) for n in range(3)] + [
            (n, "F", 0.5) for n in range(failures)
        ]:
            r = row(day, day + outcome + str(n), outcome, value)
            for j in r["joins"].values():
                j["episode_id"] = day + "weak"
            a.add(r)


def test_paired_cluster_bootstrap_and_scope_winner_are_deterministic():
    a = R.Aggregator(registry(row()))
    favorable(a)
    x = a.comparison("g")
    c = x["comparisons"][0]
    assert c["status"] == "eligible_advisory"
    assert c["scope_winner"]
    assert c["bootstrap_valid_iterations"] == 1000
    assert c["candidate"]["raw_win_rate"] == 1
    assert c["empirical_lower_5pct_delta"] > 0
    assert x == a.comparison("g")
    a.close()


def test_delay_gap_is_coverage_loss_not_successful_withhold():
    a = R.Aggregator(registry(row()))
    r = row(outcome="F", value=0.5)
    r["joins"]["180"] = {"grade": "U"}
    a.add(r)
    x = a.comparison("g")["comparisons"][0]
    assert x["excluded_opportunities"] == 0
    assert x["status"] != "eligible_advisory"
    a.close()


def test_outcome_U_worst_case_does_not_change_stored_labels():
    p = dict(selected={"W": 1, "U": 1}, excluded={"F": 1, "U": 1})
    assert R.pair_delta(p) > 0
    assert R.pair_delta(p, worst_u=True) == 0
    assert p["selected"]["U"] == 1


def test_aggregate_export_merge_preserves_statistics(tmp_path):
    a = R.Aggregator(registry(row()), scratch_root=tmp_path)
    favorable(a)
    out = a.export()
    b = R.Aggregator(registry(row()))
    b.merge(out)
    assert b.comparison("g")["comparisons"] == a.comparison("g")["comparisons"]
    a.close()
    b.close()
    assert not list(tmp_path.iterdir())


def test_indexed_join_matches_checked_snapshots_and_validates_only_once(monkeypatch):
    observations = [
        observation(),
        observation(DAY + "T09:01:00+09:00"),
        observation(DAY + "T09:05:00+09:00"),
    ]
    index = R.ObservationIndex(observations)
    expected = [R.join_snapshot(row(), observations, delay=d) for d in R.DELAYS]
    monkeypatch.setattr(
        R,
        "market_weakness_observation_contract_errors",
        lambda _: pytest.fail("repeated full-day validation"),
    )
    assert [R.join_snapshot(row(), index, delay=d) for d in R.DELAYS] == expected
