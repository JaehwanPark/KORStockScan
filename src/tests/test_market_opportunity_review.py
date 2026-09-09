"""Regression coverage for scoped census diagnosis and its non-live consumer."""

from copy import deepcopy
from datetime import datetime, timedelta
import json

import pytest

from src.engine.monitoring import market_opportunity_census as census
from src.engine.monitoring.market_opportunity_review import (
    decision_disposition,
    scoped_diagnostics,
    diagnostic_followups,
    report_sha256,
)
from src.engine import build_code_improvement_workorder as workorder
from src.tests.test_market_opportunity_census import _write_jsonl


@pytest.mark.parametrize(
    "fields,expected",
    [
        (
            {
                "allowed": "False",
                "decision": "REJECT_DANGER",
                "chosen_action": "WAIT_REQUOTE",
            },
            "rejected",
        ),
        (
            {"chosen_action": "NO_BUY_AI", "reason": "ai_input_preflight_blocked"},
            "rejected",
        ),
        ({"chosen_action": "WAIT_REQUOTE"}, "observe_only"),
        (
            {
                "allowed": True,
                "decision_authority": "entry_advisory_prompt_context_only",
            },
            "advisory_only",
        ),
        ({"allowed": "unknown"}, "unresolved"),
        ({"allowed": True}, "allowed"),
    ],
)
def test_snapshot_is_not_approval(fields, expected):
    assert decision_disposition(fields) == expected


def _episode(ts, ident="e1"):
    return {
        "stock_code": "005930",
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "symbol_master_status": "verified",
        "instrument_type": "EQUITY",
        "listing_market": "KOSPI",
        "first_census_at": ts.isoformat(),
        "opportunity_episode_id": ident,
        "scanner_detection_sla_met": False,
        "stage_reached": dict.fromkeys(census.STAGE_ORDER, False),
        "terminal_coverage_reason": "candidate_not_promoted",
    }


def _captures(base, offsets):
    return [
        {
            "captured_at": (base + timedelta(seconds=t)).isoformat(),
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "panel": "liquid_common",
            "source_quality_status": "ok",
            "source": {"normalized_source_payload_sha256": "verified_by_loader"},
        }
        for t in offsets
    ]


def _scoped(rows, captures, **kw):
    return scoped_diagnostics(
        rows,
        captures,
        parse_ts=census._parse_ts,
        summarize=census._summarize_rows_base,
        master_valid=kw.get("master_valid", True),
        trigger_valid=True,
        sample_floor=1,
    )


def test_old_gap_other_scope_master_and_economics_do_not_poison_valid_window():
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    captures = _captures(base, [0, 300, 600, 2400, 2700, 3000])
    rows = [
        _episode(base),
        _episode(base + timedelta(seconds=2400), "recovered"),
        _episode(base + timedelta(seconds=1200), "gap"),
        _episode(base + timedelta(seconds=3000), "pending"),
    ]
    rows.append({**_episode(base, "missing-master"), "symbol_master_status": "missing"})
    rows.append(
        {**_episode(base, "nxt"), "venue": "NXT", "session": "NXT_REGULAR_OVERLAP"}
    )
    result = _scoped(rows, captures)["by_venue_session"]
    scope = result["KRX|KRX_REGULAR"]
    assert scope["eligible_episode_ids"] == ["e1", "recovered"]
    assert scope["conservation_delta"] == 0
    assert scope["status"] == "diagnostic_ready"
    assert scope["economic_status"] == "insufficient_economic_evidence"
    assert not scope["whole_market_coverage_claim_allowed"]
    assert result["NXT|NXT_REGULAR_OVERLAP"]["eligible_episode_count"] == 0
    assert (
        _scoped(rows, captures, master_valid=False)["by_venue_session"][
            "KRX|KRX_REGULAR"
        ]["eligible_episode_count"]
        == 0
    )


def test_unhashed_anchor_does_not_enter_valid_interval():
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    captures = _captures(base, [0, 30, 300, 600])
    captures[1]["source"] = {}
    scope = _scoped([_episode(base + timedelta(seconds=30))], captures)[
        "by_venue_session"
    ]["KRX|KRX_REGULAR"]
    assert scope["eligible_episode_count"] == 0


@pytest.mark.parametrize("hour,minute,expected", [(11, 0, 1), (15, 10, 0), (15, 20, 0)])
def test_actionable_scope_excludes_hard_cutoff_but_preserves_broad_count(
    hour, minute, expected
):
    base = datetime(2026, 9, 8, hour, minute, tzinfo=census.KST)
    scope = _scoped([_episode(base)], _captures(base, [0, 300, 600]))[
        "by_venue_session"
    ]["KRX|KRX_REGULAR"]
    assert scope["raw_episode_count"] == 1
    assert scope["eligible_episode_count"] == expected
    assert scope["conservation_delta"] == 0
    assert not scope["runtime_buy_window_receipt_verified"]
    if not expected:
        assert scope["exclusion_counts"] == {"intended_new_buy_hard_cutoff": 1}


def test_premarket_logical_cohort_requires_exact_route_and_matching_promotion(tmp_path):
    from src.tests.test_market_opportunity_census import _promoted_ws_bundle_event

    base = datetime(2026, 9, 8, 8, 10, tzinfo=census.KST)
    bundle = _promoted_ws_bundle_event(base)
    fields = bundle["fields"]
    fields.update(
        effective_venue="PREMARKET_KRX_LIKE", market_session_bucket="krx_like_premarket"
    )
    samples = json.loads(fields["rising_missed_entry_turn_bbo_samples"])
    for sample in samples:
        sample.update(
            effective_venue="PREMARKET_KRX_LIKE",
            market_session_bucket="krx_like_premarket",
            observed_venue="NXT",
            market_route="nxt_only",
            observed_item="005930_NX",
        )
    fields["rising_missed_entry_turn_bbo_samples"] = json.dumps(samples)
    promotion = {
        "stage": "scalping_scanner_candidate_promoted",
        "stock_code": "005930",
        "emitted_at": base.isoformat(),
        "fields": {
            "scanner_promotion_id": "PROM-1",
            "effective_venue": "PREMARKET_KRX_LIKE",
        },
    }
    path = tmp_path / "pipeline.jsonl"
    _write_jsonl(path, [promotion])
    index = census._load_stage_index(
        path, tmp_path / "absent.jsonl", target_date="2026-09-08"
    )
    assert index["005930"]["scanner_promoted"][0]["venue"] == "PREMARKET_KRX_LIKE"
    for native_id, expected in (
        ("PROM-OTHER", "PREMARKET_KRX_LIKE"),
        ("PROM-1", "NXT"),
    ):
        promotion["fields"]["scanner_promotion_id"] = native_id
        _write_jsonl(path, [promotion, bundle])
        bbo = {}
        index = census._load_stage_index(
            path,
            tmp_path / "absent.jsonl",
            target_date="2026-09-08",
            executable_bbo_index=bbo,
        )
        row = index["005930"]["scanner_promoted"][0]
        assert row["venue"] == expected
        assert bbo["005930"]["NXT"]["NXT_PREMARKET"]
    samples[0]["observed_item"] = "005930"
    fields["rising_missed_entry_turn_bbo_samples"] = json.dumps(samples)
    _write_jsonl(path, [promotion, bundle])
    index = census._load_stage_index(
        path, tmp_path / "absent.jsonl", target_date="2026-09-08"
    )
    assert index["005930"]["scanner_promoted"][0]["venue"] == "PREMARKET_KRX_LIKE"


def test_attach_absent_is_first_gap_unless_downstream_proves_consumption():
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    event = {"ts": base, "venue": "KRX", "scanner_promotion_id": "P1", "record_id": "1"}
    index = {"005930": {"scanner_promoted": [event]}}
    args = dict(after=base, require_venue=True, require_lineage=True)
    episode = {**_episode(base), "first_census_at": base}
    row = census._coverage_row(episode, index, **args)
    assert row["terminal_coverage_reason"] == "scanner_runtime_attach_gap"
    index["005930"]["fast_precheck"] = [event]
    row = census._coverage_row(episode, index, **args)
    assert row["terminal_coverage_reason"] == "scanner_heavy_eval_gap"
    assert row["handoff_receipt_gaps"] == ["runtime_watch_attached"]
    index["005930"]["runtime_watch_attach_attempted"] = [
        {
            **event,
            "runtime_target_attach_outcome": "watching_skipped",
            "reason": "existing_owner",
        },
        {**event, "scanner_promotion_id": "OTHER", "reason": "wrong_promotion"},
    ]
    row = census._coverage_row(episode, index, **args)
    assert len(row["runtime_attach_attempts"]) == 1
    assert row["runtime_attach_attempts"][0]["reason"] == "existing_owner"


def test_capture_primary_first_page_before_secondary_without_extra_budget():
    calls = []

    def fetch(token, **kw):
        calls.append(kw)
        return [{"Code": "005930", "Price": 1000}]

    records = census.capture_market_snapshots(
        "not-used",
        target_date="2026-09-08",
        captured_at=datetime(2026, 9, 8, 10, tzinfo=census.KST),
        venues=(v for v in ("KRX", "NXT")),
        panels=(p for p in ("all", "liquid_common")),
        fetcher=fetch,
    )
    assert [(r["panel"], r["venue"]) for r in records] == [
        ("liquid_common", "KRX"),
        ("liquid_common", "NXT"),
        ("all", "KRX"),
        ("all", "NXT"),
    ]
    assert all(
        c["max_pages_limit"] == 1 and c["request_class"] == "source_only" for c in calls
    )
    assert all(r["source"]["capture_budget"]["max_pages"] == 1 for r in records)


@pytest.mark.parametrize("limit,expected", [(None, 10), (1, 1), (100, 10)])
def test_collector_page_bound_does_not_expand_or_change_other_callers(
    monkeypatch, limit, expected
):
    from src.utils import kiwoom_utils

    calls = []

    def fetch(**kw):
        calls.append(kw)
        return [], {}

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fetch)
    kiwoom_utils.get_top_fluctuation_ka10027(
        "fixture", limit=200, max_pages_limit=limit
    )
    assert calls[0]["max_pages"] == expected


def test_actual_reject_shape_reaches_correct_report_reason(tmp_path):
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    common = {"scanner_promotion_id": "PROM-1", "effective_venue": "KRX"}
    events = [
        {
            "stage": "scalping_scanner_candidate_promoted",
            "stock_code": "005930",
            "emitted_at": base.isoformat(),
            "record_id": 1,
            "fields": common,
        },
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "005930",
            "emitted_at": (base + timedelta(seconds=20)).isoformat(),
            "record_id": 1,
            "fields": {
                **common,
                "allowed": "False",
                "decision": "REJECT_DANGER",
                "decision_authority": "entry_advisory_prompt_context_only",
            },
        },
    ]
    path = tmp_path / "events.jsonl"
    _write_jsonl(path, events)
    index = census._load_stage_index(
        path, tmp_path / "absent.jsonl", target_date="2026-09-08"
    )
    row = census._coverage_row(
        {**_episode(base), "first_census_at": base},
        index,
        after=base,
        before=base + timedelta(seconds=300),
        require_venue=True,
        require_lineage=True,
    )
    assert row["terminal_coverage_reason"] == "entry_decision_rejected"


def test_small_net_uses_same_path_and_does_not_invent_short_horizons():
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)

    def bbo(seconds, bid, ask):
        t = base + timedelta(seconds=seconds)
        return {
            "observed_at": t,
            "observed_epoch": t.timestamp(),
            "best_bid": bid,
            "best_ask": ask,
            "best_bid_qty": 1,
            "best_ask_qty": 1,
            "spread_bps": 10,
            "price_source": "test_exact_source",
            "observer_episode_id": "test",
            "timeout_max_lag_sec": 60,
        }

    index = {
        "005930": {
            "KRX": {
                "KRX_REGULAR": [
                    bbo(0, 9990, 10000),
                    bbo(300, 10030, 10040),
                    bbo(1200, 10030, 10040),
                ]
            }
        }
    }
    outcome = census._ex_post_executable_opportunity(
        {**_episode(base), "first_census_at": base},
        index,
        observation_watermark=base + timedelta(seconds=1500),
        round_trip_cost_pct=0.23,
        include_small_net_scenarios=True,
    )
    assert (
        outcome["small_net_scenarios"]["net_0.03_h60"]["cost_adjusted_return_pct"]
        is None
    )
    assert outcome["small_net_scenarios"]["net_0.03_h300"]["label"] == "target_first"
    assert outcome["small_net_scenarios"]["net_0.07_h300"]["label"] == "target_first"
    assert outcome["small_net_scenarios"]["net_0.03_h300"][
        "cost_adjusted_return_pct"
    ] == pytest.approx(0.07)
    report = census._small_net_review(
        [{**_episode(base), "ex_post_executable_opportunity": outcome}]
    )
    assert not report["scenario_returns_additive"]
    assert report["market_data_request_count_added"] == 0
    assert not report["by_venue_session"]["KRX|KRX_REGULAR"]["net_0.03_h300"][
        "economic_evidence_floor_met"
    ]


def test_native_handoff_validates_date_hash_authority_and_duplicate_ids():
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    scoped = _scoped([_episode(base)], _captures(base, [0, 300, 600]))
    report = {
        "target_date": "2026-09-08",
        "report_type": "market_opportunity_census",
        "schema_version": census.REPORT_SCHEMA_VERSION,
        "metric_contract": census.METRIC_CONTRACT,
        "diagnostic_followups": diagnostic_followups(scoped, "2026-09-08"),
    }
    report["artifact_sha256"] = report_sha256(report)
    orders = workorder._market_census_followup_orders(report, "2026-09-08")
    assert len(orders) == 1 and orders[0]["census_contract_valid"]
    classified = workorder._classify_order(
        orders[0],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "defer_evidence"
    repeated, escalated = workorder._escalate_repeated_unresolved_orders(
        [classified], repeat_counts={orders[0]["order_id"]: {"count": 10}}
    )
    assert not escalated and repeated[0].decision == "defer_evidence"
    for mutation in ("date", "hash", "authority", "duplicate", "decision"):
        altered = deepcopy(report)
        if mutation == "date":
            altered["target_date"] = "2026-09-07"
        if mutation == "hash":
            altered["extra"] = "tampered"
        if mutation == "authority":
            altered["diagnostic_followups"][0]["runtime_effect"] = "False"
        if mutation == "duplicate":
            altered["diagnostic_followups"] *= 2
        if mutation == "decision":
            altered["diagnostic_followups"][0]["decision"] = "implement_now"
        if mutation != "hash":
            altered["artifact_sha256"] = report_sha256(altered)
        invalid = workorder._market_census_followup_orders(altered, "2026-09-08")
        assert invalid[0]["census_contract_valid"] is False
        assert invalid[0]["allowed_runtime_apply"] is False
        assert invalid[0]["recommendation_id"] is None


def test_full_workorder_builder_consumes_only_bound_census_diagnostics(
    tmp_path, monkeypatch
):
    base = datetime(2026, 9, 8, 10, tzinfo=census.KST)
    scoped = _scoped([_episode(base)], _captures(base, [0, 300, 600]))
    source = {
        "target_date": "2026-09-08",
        "report_type": "market_opportunity_census",
        "schema_version": census.REPORT_SCHEMA_VERSION,
        "metric_contract": census.METRIC_CONTRACT,
        "diagnostic_followups": diagnostic_followups(scoped, "2026-09-08"),
    }
    # Foreign metadata must never override the native evidence-only disposition.
    source["diagnostic_followups"][0]["implementation_status"] = "already_implemented"
    source["audit_only"] = {"ldm_policy": "historical evidence, never live authority"}
    source["artifact_sha256"] = report_sha256(source)
    source_dir = tmp_path / "census"
    source_dir.mkdir()
    source_path = source_dir / "market_opportunity_census_2026-09-08.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setattr(workorder, "MARKET_OPPORTUNITY_CENSUS_DIR", source_dir)
    monkeypatch.setattr(
        workorder, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "report"
    )
    monkeypatch.setattr(workorder, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")
    report = workorder.build_code_improvement_workorder("2026-09-08", max_orders=10)
    items = [
        o
        for o in report["orders"]
        if o.get("source_report_type") == "market_opportunity_census"
    ]
    assert len(items) == 1
    assert items[0]["decision"] == "defer_evidence"
    assert items[0]["allowed_runtime_apply"] is False
    assert items[0]["source_artifact_sha256"] == source["artifact_sha256"]
    assert report["source"]["market_opportunity_census"]
    assert (
        items[0]["recommendation_id"]
        == source["diagnostic_followups"][0]["recommendation_id"]
    )


def test_malformed_existing_census_is_visible_but_missing_is_not_due(tmp_path):
    path = tmp_path / "census.json"
    assert workorder._load_market_census_source(path, isolated_source_mode=True) == {}
    path.write_text("{", encoding="utf-8")
    loaded = workorder._load_market_census_source(path, isolated_source_mode=True)
    result = workorder._market_census_followup_orders(loaded, "2026-09-08")
    assert result[0]["census_contract_valid"] is False
    assert result[0]["order_id"] == "order_market_census_source_contract"
    assert result[0]["recommendation_id"] is None
    assert result[0]["allowed_runtime_apply"] is False
