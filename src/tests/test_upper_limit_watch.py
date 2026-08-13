import json
from datetime import date, datetime, timedelta

import pandas as pd

from src.engine.monitoring import upper_limit_watch_report as report
from src.engine.scalping import upper_limit_watch as watch
from src.engine import sniper_overnight_gatekeeper, sniper_state_handlers
from src.scanners import scalping_scanner
from src.utils import kiwoom_utils, pipeline_event_logger


def _observation_fields(**extra):
    return {
        "decision_authority": "upper_limit_source_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        **extra,
    }


def test_report_contract_accepts_pipeline_logger_boolean_strings_and_fails_closed():
    fields = _observation_fields()
    serialized = {key: str(value) for key, value in fields.items()}
    assert report._event_contract_valid(fields) is True
    assert report._event_contract_valid(serialized) is True
    assert report._event_contract_valid({**serialized, "runtime_effect": "0"}) is False
    assert (
        report._event_contract_valid({**serialized, "broker_order_forbidden": "yes"})
        is False
    )


def test_pipeline_logger_output_is_accepted_by_report_reader(tmp_path, monkeypatch):
    event_path = tmp_path / "pipeline_events_2026-08-06.jsonl"
    monkeypatch.setattr(
        pipeline_event_logger,
        "_event_path",
        lambda _target_date: event_path,
    )
    monkeypatch.setattr(pipeline_event_logger, "_get_producer_compactor", lambda: None)
    monkeypatch.setattr(
        pipeline_event_logger, "threshold_family_for_stage", lambda *_args: None
    )
    emitted = pipeline_event_logger.emit_pipeline_event(
        "UPPER_LIMIT_WATCH",
        "테스트",
        "123450",
        "upper_limit_watch_registered",
        fields=_observation_fields(),
    )
    assert emitted["fields"]["runtime_effect"] == "False"
    assert emitted["fields"]["broker_order_forbidden"] == "True"
    stored = json.loads(event_path.read_text(encoding="utf-8"))
    assert report._event_contract_valid(stored["fields"]) is True


def test_official_previous_limit_up_request_uses_updown_type_six(monkeypatch):
    captured = {}

    def fetch(**kwargs):
        captured.update(kwargs)
        return ([{"updown_pric": []}], {})

    monkeypatch.setattr(kiwoom_utils, "_fetch_kiwoom_api_continuous_with_meta", fetch)
    rows, source = kiwoom_utils.get_previous_limit_up_stocks_ka10017("token")
    assert rows == []
    assert captured["api_id"] == "ka10017"
    assert captured["payload"]["updown_tp"] == "6"
    assert captured["payload"]["trde_qty_tp"] == "00000"
    assert source["official_upstream_commit"] == (
        "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"
    )


def test_candidate_source_classifies_intraday_and_consecutive(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "CANDIDATE_DIR", tmp_path)
    source_date = date(2026, 8, 5)

    def fetch_previous(_token):
        return (
            [
                {
                    "Code": "123450",
                    "Name": "테스트",
                    "ConsecutiveCountRaw": "1",
                    "Volume": 10,
                },
                {
                    "Code": "234560",
                    "Name": "연속",
                    "ConsecutiveCountRaw": "2",
                    "Volume": 20,
                },
            ],
            {"request_payload": {"updown_tp": "6"}},
        )

    frames = {
        "123450": pd.DataFrame(
            [{"Open": 900, "High": 1000, "Low": 850, "Close": 1000}],
            index=[pd.Timestamp(source_date)],
        ),
        "234560": pd.DataFrame(
            [{"Open": 1000, "High": 1000, "Low": 1000, "Close": 1000}],
            index=[pd.Timestamp(source_date)],
        ),
    }

    candidates, artifact = watch.build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 8, 6),
        fetch_previous=fetch_previous,
        fetch_daily=lambda _token, code: frames[code],
        latest_date_loader=lambda _db, _date: source_date,
        db_ohlc_loader=lambda _db, code, _date: (
            (900, 1000, 850, 1000, "테스트")
            if code == "123450"
            else (1000, 1000, 1000, 1000, "연속")
        ),
    )

    assert artifact["status"] == "pass"
    by_code = {candidate.code: candidate for candidate in candidates}
    assert by_code["123450"].cohort == "single_limit_up_intraday_traded_close_locked"
    assert by_code["234560"].cohort == "consecutive_limit_up_2plus"


def test_candidate_source_fails_closed_on_ohlc_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "CANDIDATE_DIR", tmp_path)
    source_date = date(2026, 8, 5)
    daily = pd.DataFrame(
        [{"Open": 900, "High": 1000, "Low": 850, "Close": 1000}],
        index=[pd.Timestamp(source_date)],
    )
    candidates, artifact = watch.build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 8, 6),
        fetch_previous=lambda _token: (
            [{"Code": "123450", "Name": "테스트", "ConsecutiveCountRaw": "1"}],
            {},
        ),
        fetch_daily=lambda _token, _code: daily,
        latest_date_loader=lambda _db, _date: source_date,
        db_ohlc_loader=lambda _db, _code, _date: (900, 1000, 850, 990, "테스트"),
    )
    assert candidates == []
    assert artifact["status"] == "blocked"
    assert artifact["blocked_rows"][0]["reason"] == "ka10081_db_ohlc_mismatch"


def test_report_one_verified_positive_path_opens_next_date_policy(
    tmp_path, monkeypatch
):
    candidate_dir = tmp_path / "candidate"
    event_dir = tmp_path / "events"
    report_dir = tmp_path / "report"
    counterfactual_dir = tmp_path / "counterfactual"
    bounded_dir = tmp_path / "bounded"
    for path in (candidate_dir, event_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(report, "CANDIDATE_DIR", candidate_dir)
    monkeypatch.setattr(report, "EVENT_DIR", event_dir)
    monkeypatch.setattr(report, "REPORT_DIR", report_dir)
    monkeypatch.setattr(report, "COUNTERFACTUAL_DIR", counterfactual_dir)
    monkeypatch.setattr(report, "BOUNDED_DIR", bounded_dir)
    target_date = "2026-08-06"
    candidate = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_candidate_source",
        "target_date": target_date,
        "status": "pass",
        "candidate_count": 1,
        "candidates": [
            {
                "code": "123450",
                "name": "테스트",
                "cohort": "single_limit_up_intraday_traded_close_locked",
                "price_band": "1천~5천",
            }
        ],
        "decision_authority": "upper_limit_source_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    (
        candidate_dir / f"upper_limit_watch_candidate_source_{target_date}.json"
    ).write_text(json.dumps(candidate), encoding="utf-8")
    start = datetime(2026, 8, 6, 9, 0)
    events = [
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_registered",
            "emitted_at": start.isoformat(),
            "fields": _observation_fields(
                cohort="single_limit_up_intraday_traded_close_locked",
                price_band="1천~5천",
            ),
        },
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_trigger_confirmed",
            "emitted_at": (start + timedelta(seconds=10)).isoformat(),
            "fields": _observation_fields(
                trigger_type="pullback_reclaim",
                current_price=1000,
                best_ask=1000,
                best_bid=999,
                quote_age_sec=1.0,
                confirmation_tick_count=2,
            ),
        },
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_reg_requested",
            "emitted_at": (start + timedelta(seconds=180)).isoformat(),
            "fields": _observation_fields(reason="label_capture_stale", force=True),
        },
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_snapshot",
            "emitted_at": (start + timedelta(seconds=190)).isoformat(),
            "fields": _observation_fields(
                current_price=1010, high_price=1010, low_price=1000
            ),
        },
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_released",
            "emitted_at": (start + timedelta(seconds=200)).isoformat(),
            "fields": _observation_fields(reason="rotation_due"),
        },
    ]
    (event_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )

    paths = report.build_artifacts(target_date)
    bounded = json.loads(paths["bounded"].read_text(encoding="utf-8"))
    cumulative = json.loads(paths["counterfactual"].read_text(encoding="utf-8"))
    assert bounded["status"] == "live_auto_apply_ready"
    assert bounded["operator_approval_required"] is False
    assert bounded["ready_candidate_count"] == 1
    daily = json.loads(paths["report"].read_text(encoding="utf-8"))
    assert daily["label_capture_recovery_request_count"] == 1
    assert daily["source_status"]["label_capture_recovery_request_count"] == 1
    assert cumulative["cumulative_update"]["current_row_count"] == 1
    assert cumulative["sample_count"] == 1

    next_date = "2026-08-07"
    candidate["target_date"] = next_date
    (candidate_dir / f"upper_limit_watch_candidate_source_{next_date}.json").write_text(
        json.dumps(candidate), encoding="utf-8"
    )
    next_events = []
    for event in events:
        shifted = dict(event)
        shifted["emitted_at"] = (
            datetime.fromisoformat(event["emitted_at"]) + timedelta(days=1)
        ).isoformat()
        next_events.append(shifted)
    (event_dir / f"pipeline_events_{next_date}.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in next_events),
        encoding="utf-8",
    )
    next_paths = report.build_artifacts(next_date)
    next_cumulative = json.loads(
        next_paths["counterfactual"].read_text(encoding="utf-8")
    )
    assert next_cumulative["cumulative_update"]["prior_artifact_valid"] is True
    assert next_cumulative["cumulative_update"]["prior_row_count"] == 1
    assert next_cumulative["cumulative_update"]["current_row_count"] == 1
    assert next_cumulative["sample_count"] == 2


def test_label_uses_fresh_post_trigger_ask_and_horizon_bid():
    start = datetime(2026, 8, 6, 9, 0)
    label = report._label(
        {
            "row_id": "2026-08-06:123450:1",
            "target_date": "2026-08-06",
            "code": "123450",
            "name": "테스트",
            "cohort": "single_limit_up_intraday_traded_close_locked",
            "price_band": "1천~5천",
            "trigger": {
                "at": (start + timedelta(seconds=10)).isoformat(),
                "trigger_type": "pullback_reclaim",
                "best_ask": 0,
                "best_bid": 0,
                "quote_age_sec": None,
                "confirmation_tick_count": 2,
            },
            "snapshots": [
                {
                    "at": (start + timedelta(seconds=100)).isoformat(),
                    "current_price": 1005,
                }
            ],
            "quote_snapshots": [
                {
                    "at": (start + timedelta(seconds=12)).isoformat(),
                    "best_ask": 1001,
                    "best_bid": 1000,
                    "quote_age_sec": 0.0,
                },
                {
                    "at": (start + timedelta(seconds=192)).isoformat(),
                    "best_ask": 1011,
                    "best_bid": 1010,
                    "quote_age_sec": 0.0,
                },
            ],
        }
    )
    assert label["label_status"] == "pass"
    assert label["entry_price"] == 1001
    assert label["entry_price_source"] == "post_trigger_fresh_0d_ask"
    assert label["exit_price"] == 1010
    assert label["exit_price_source"] == "fresh_0d_bid"


def test_label_rejects_explicitly_stale_quote_snapshots():
    start = datetime(2026, 8, 6, 9, 0)
    label = report._label(
        {
            "row_id": "2026-08-06:123450:1",
            "target_date": "2026-08-06",
            "code": "123450",
            "name": "테스트",
            "cohort": "single_limit_up_intraday_traded_close_locked",
            "price_band": "1천~5천",
            "trigger": {
                "at": (start + timedelta(seconds=10)).isoformat(),
                "trigger_type": "pullback_reclaim",
                "best_ask": 0,
                "best_bid": 0,
                "quote_age_sec": None,
                "confirmation_tick_count": 2,
            },
            "snapshots": [],
            "quote_snapshots": [
                {
                    "at": (start + timedelta(seconds=11)).isoformat(),
                    "best_ask": 1001,
                    "best_bid": 1000,
                    "quote_age_sec": 5.01,
                },
                {
                    "at": (start + timedelta(seconds=191)).isoformat(),
                    "best_ask": 1011,
                    "best_bid": 1010,
                    "quote_age_sec": 0.0,
                },
            ],
        }
    )
    assert label["label_status"] == "entry_bbo_missing"
    assert label["entry_bbo_present"] is False


def test_label_rejects_entry_spread_above_live_cap():
    start = datetime(2026, 8, 6, 9, 0)
    label = report._label(
        {
            "row_id": "2026-08-06:123450:1",
            "target_date": "2026-08-06",
            "code": "123450",
            "name": "테스트",
            "cohort": "single_limit_up_intraday_traded_close_locked",
            "price_band": "1천~5천",
            "trigger": {
                "at": (start + timedelta(seconds=10)).isoformat(),
                "trigger_type": "pullback_reclaim",
                "best_ask": 1000,
                "best_bid": 980,
                "quote_age_sec": 0.0,
                "confirmation_tick_count": 2,
            },
            "snapshots": [
                {
                    "at": (start + timedelta(seconds=190)).isoformat(),
                    "current_price": 1010,
                }
            ],
            "quote_snapshots": [],
        }
    )
    assert label["label_status"] == "entry_spread_too_wide"
    assert label["entry_spread_pct"] == 2.0


def test_invalid_prior_artifact_is_excluded_without_blocking_current_date(
    tmp_path, monkeypatch
):
    candidate_dir = tmp_path / "candidate"
    event_dir = tmp_path / "events"
    report_dir = tmp_path / "report"
    counterfactual_dir = tmp_path / "counterfactual"
    bounded_dir = tmp_path / "bounded"
    for path in (candidate_dir, event_dir, counterfactual_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(report, "CANDIDATE_DIR", candidate_dir)
    monkeypatch.setattr(report, "EVENT_DIR", event_dir)
    monkeypatch.setattr(report, "REPORT_DIR", report_dir)
    monkeypatch.setattr(report, "COUNTERFACTUAL_DIR", counterfactual_dir)
    monkeypatch.setattr(report, "BOUNDED_DIR", bounded_dir)

    prior_date = "2026-08-06"
    (
        counterfactual_dir / f"upper_limit_watch_counterfactual_{prior_date}.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "upper_limit_watch_counterfactual",
                "target_date": prior_date,
                "source_quality_status": "blocked",
                "rows": [],
            }
        ),
        encoding="utf-8",
    )
    target_date = "2026-08-07"
    candidate = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_candidate_source",
        "target_date": target_date,
        "status": "pass",
        "candidate_count": 1,
        "candidates": [
            {
                "code": "123450",
                "name": "테스트",
                "cohort": "single_limit_up_intraday_traded_close_locked",
                "price_band": "1천~5천",
            }
        ],
        "decision_authority": "upper_limit_source_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    (
        candidate_dir / f"upper_limit_watch_candidate_source_{target_date}.json"
    ).write_text(json.dumps(candidate), encoding="utf-8")
    start = datetime(2026, 8, 7, 9, 0)
    events = [
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_registered",
            "emitted_at": start.isoformat(),
            "fields": {key: str(value) for key, value in _observation_fields().items()},
        },
        {
            "pipeline": "UPPER_LIMIT_WATCH",
            "stock_code": "123450",
            "stock_name": "테스트",
            "stage": "upper_limit_watch_released",
            "emitted_at": (start + timedelta(seconds=200)).isoformat(),
            "fields": {
                key: str(value)
                for key, value in _observation_fields(reason="rotation_due").items()
            },
        },
    ]
    (event_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )

    paths = report.build_artifacts(target_date)
    cumulative = json.loads(paths["counterfactual"].read_text(encoding="utf-8"))
    assert cumulative["status"] == "pass"
    assert cumulative["source_quality_status"] == "pass"
    assert cumulative["cumulative_update"]["prior_artifact_valid"] is False
    assert cumulative["cumulative_update"]["prior_artifact_excluded"] is True
    assert cumulative["cumulative_update"]["prior_row_count"] == 0
    assert cumulative["cumulative_update"]["current_row_count"] == 1


def test_prior_selection_skips_invalid_latest_and_preserves_older_valid_rows(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(report, "COUNTERFACTUAL_DIR", tmp_path)
    valid_date = "2026-08-06"
    valid = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_counterfactual",
        "target_date": valid_date,
        "source_quality_status": "pass",
        "rows": [
            {
                "row_id": f"{valid_date}:123450:1",
                "target_date": valid_date,
                "label_status": "pass",
            }
        ],
        **report.COUNTERFACTUAL_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    (tmp_path / f"upper_limit_watch_counterfactual_{valid_date}.json").write_text(
        json.dumps(valid), encoding="utf-8"
    )
    invalid_date = "2026-08-07"
    (tmp_path / f"upper_limit_watch_counterfactual_{invalid_date}.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "upper_limit_watch_counterfactual",
                "target_date": invalid_date,
                "source_quality_status": "blocked",
                "rows": [],
            }
        ),
        encoding="utf-8",
    )

    selected, provenance = report._select_prior("2026-08-08")
    assert selected["target_date"] == valid_date
    assert len(selected["rows"]) == 1
    assert provenance["latest_seen_prior_target_date"] == invalid_date
    assert provenance["invalid_prior_dates_skipped"] == [invalid_date]


def test_upper_limit_submit_guard_rechecks_proximity(monkeypatch):
    now = datetime.now().timestamp()
    stock = {
        "source_signature": "UPPER_LIMIT_LIVE_RECLAIM",
        "upper_limit_live_policy_matched": True,
        "upper_limit_live_policy_sample_count": 1,
        "upper_limit_risk_max_daily_entries": 1,
        "upper_limit_scale_in_allowed": False,
        "upper_limit_same_day_reentry_allowed": False,
        "upper_limit_overnight_allowed": False,
        "upper_limit_normal_scalping_guards_required": True,
        "upper_limit_entry_proximity_guard_required": True,
        "upper_limit_live_trigger_type": "pullback_reclaim",
        "upper_limit_prior_close": 1000,
        "upper_limit_current_limit_price": 1300,
        "upper_limit_max_entry_spread_pct": 1.5,
    }
    ws = {
        "curr": 1270,
        "best_ask": 1271,
        "best_bid": 1270,
        "last_ws_update_ts": now,
    }
    monkeypatch.setattr(
        sniper_state_handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda _code, data, _strategy: (dict(data), {}),
    )
    _refreshed, decision = sniper_state_handlers._upper_limit_live_pre_submit_guard(
        stock, "123450", ws, "SCALPING"
    )
    assert decision["allowed"] is False
    assert decision["reason"] == "upper_limit_live_entry_proximity_blocked"


def test_upper_limit_live_is_forced_out_before_overnight():
    assert (
        sniper_overnight_gatekeeper._bounded_observation_live_overnight_reason(
            {"source_signature": "UPPER_LIMIT_LIVE_RECLAIM"}
        )
        == "upper_limit_live_overnight_forbidden"
    )


def test_upper_limit_registry_is_shared_signal_isolation(monkeypatch):
    from src.engine.scalping import limit_down_watch

    received = []
    watch.UPPER_LIMIT_OBSERVATION_REGISTRY.activate(
        "123450", lambda code, data, epoch: received.append((code, data, epoch))
    )
    try:
        assert limit_down_watch.is_observation_only_code("123450") is True
        limit_down_watch.observe_raw_market_data(
            "123450", {"curr": "1000"}, 1.0, realtime_type="0B"
        )
        assert received[0][0] == "123450"
        assert received[0][1]["_upper_limit_realtime_type"] == "0B"
    finally:
        watch.UPPER_LIMIT_OBSERVATION_REGISTRY.release("123450")


def test_live_handoff_requires_policy_two_ticks_and_fresh_bbo():
    class EventBus:
        def publish(self, *_args, **_kwargs):
            return None

    manager = watch.UpperLimitWatchManager("token", object(), EventBus())
    manager.active = watch.UpperLimitCandidate(
        code="123450",
        name="테스트",
        source_trade_date="2026-08-05",
        limit_up_close=1000,
        source_open=900,
        source_high=1000,
        source_low=850,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=10,
    )
    now = datetime.now().timestamp()
    key = "single_limit_up_intraday_traded_close_locked|1천~5천|pullback_reclaim"
    manager.live_policy_by_key = {key: {"sample_count": 1}}
    manager.live_policy_source_date = "2026-08-05"
    manager.live_policy_max_entry_spread_pct = 1.5
    manager.state = {
        "trigger_type": "pullback_reclaim",
        "trigger_confirmed_epoch": now - 1,
        "last_tick_epoch": now - 1,
        "last_quote_epoch": now - 1,
        "current_price": 1010,
        "prior_limit_up_close": 1000,
        "current_upper_limit_price": 1300,
        "best_ask": 1011,
        "best_bid": 1010,
        "trade_value": 1000000,
        "volume": 1000,
    }
    target = manager.live_promotion_target(now_epoch=now, daily_promotion_count=0)
    assert target is not None
    assert target["UpperLimitLivePolicyKey"] == key
    assert target["UpperLimitScaleInAllowed"] is False
    assert manager.live_promotion_target(now_epoch=now, daily_promotion_count=1) is None


def test_rotation_prioritizes_live_ready_type_before_unvalidated_cohort():
    manager = watch.UpperLimitWatchManager("token", object(), object())
    unvalidated = watch.UpperLimitCandidate(
        code="111110",
        name="연속",
        source_trade_date="2026-08-05",
        limit_up_close=1000,
        source_open=1000,
        source_high=1000,
        source_low=1000,
        consecutive_count=2,
        cohort="consecutive_limit_up_2plus",
        price_band="1천~5천",
        volume=10000,
    )
    validated = watch.UpperLimitCandidate(
        code="222220",
        name="단일",
        source_trade_date="2026-08-05",
        limit_up_close=1000,
        source_open=900,
        source_high=1000,
        source_low=850,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=100,
    )
    manager.candidates = [unvalidated, validated]
    manager.live_policy_by_key = {
        "single_limit_up_intraday_traded_close_locked|1천~5천|pullback_reclaim": {
            "sample_count": 1
        }
    }
    assert manager._pick(set(), 1000.0) == validated


def test_ordered_raw_path_requires_two_reclaim_ticks_and_fresh_quote(monkeypatch):
    manager = watch.UpperLimitWatchManager("token", object(), object())
    manager.active = watch.UpperLimitCandidate(
        code="123450",
        name="테스트",
        source_trade_date="2026-08-05",
        limit_up_close=1000,
        source_open=900,
        source_high=1000,
        source_low=850,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=10,
    )
    manager.state = {
        "phase": "WAITING_FIRST_TICK",
        "prior_limit_up_close": 1000,
        "current_upper_limit_price": 1300,
        "last_tick_epoch": 0.0,
        "last_quote_epoch": 0.0,
        "tick_count": 0,
        "quote_count": 0,
        "transition_count": 0,
        "consecutive_reclaim_tick_count": 0,
        "consecutive_gap_hold_tick_count": 0,
        "trigger_confirmed_epoch": 0.0,
        "prior_close_broken_observed": False,
    }
    emitted = []
    monkeypatch.setattr(
        manager, "_emit", lambda stage, **fields: emitted.append((stage, fields))
    )
    monkeypatch.setattr(manager, "_write_state", lambda: None)
    manager.on_raw_market_data(
        "123450",
        {"_upper_limit_realtime_type": "0D", "best_ask": 1001, "best_bid": 1000},
        10.0,
    )
    manager.on_raw_market_data("123450", {"curr": 990, "open": 1010}, 11.0)
    manager.on_raw_market_data("123450", {"curr": 1000, "open": 1010}, 12.0)
    assert manager.state["trigger_type"] == ""
    manager.on_raw_market_data("123450", {"curr": 1001, "open": 1010}, 13.0)
    assert manager.state["trigger_type"] == "pullback_reclaim"
    trigger = [
        fields
        for stage, fields in emitted
        if stage == "upper_limit_watch_trigger_confirmed"
    ]
    assert trigger[0]["best_ask"] == 1001
    assert trigger[0]["quote_age_sec"] == 3.0


def test_triggered_label_capture_reissues_bounded_forced_reg_when_feed_stalls(
    monkeypatch,
):
    published = []
    event_bus = type(
        "EventBus",
        (),
        {"publish": lambda self, event, payload: published.append((event, payload))},
    )()
    manager = watch.UpperLimitWatchManager("token", object(), event_bus)
    candidate = watch.UpperLimitCandidate(
        code="123450",
        name="테스트",
        source_trade_date="2026-08-12",
        limit_up_close=1000,
        source_open=900,
        source_high=1000,
        source_low=850,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=10,
    )
    manager.candidates = [candidate]
    manager.active = candidate
    manager.loaded_date = "2026-08-13"
    manager.state = {
        "phase": "ABOVE_PRIOR_LIMIT_CLOSE",
        "registered_epoch": 800.0,
        "last_transition_epoch": 900.0,
        "trigger_confirmed_epoch": 900.0,
        "trigger_type": "gap_hold_breakout",
        "last_tick_epoch": 950.0,
        "last_quote_epoch": 970.0,
        "last_reg_request_epoch": 960.0,
        "last_label_capture_recovery_epoch": 0.0,
        "label_capture_recovery_count": 0,
        "first_tick_epoch": 850.0,
        "reg_request_count": 1,
    }
    emitted = []
    monkeypatch.setattr(watch, "feature_enabled", lambda: True)
    monkeypatch.setattr(watch, "_krx_session_phase", lambda _epoch: "OPEN")
    monkeypatch.setattr(manager, "_load_candidates", lambda _epoch: None)
    monkeypatch.setattr(
        manager, "_emit", lambda stage, **fields: emitted.append((stage, fields))
    )
    monkeypatch.setattr(manager, "_write_state", lambda: None)

    manager.reconcile(now_epoch=1000.0, allow_activation=False)

    assert published == [
        (
            "COMMAND_WS_REG",
            {
                "codes": ["123450"],
                "source": "upper_limit_watch_observation_recovery",
                "reason": "label_capture_stale",
                "required_realtime_types": ("0B", "0D"),
                "force": True,
                "repair_cycle": "upper_limit_label_capture_stale",
            },
        )
    ]
    assert manager.state["label_capture_recovery_count"] == 1
    assert manager.state["last_label_capture_recovery_epoch"] == 1000.0
    assert any(
        stage == "upper_limit_watch_label_capture_recovery"
        and fields["tick_stale"] is True
        and fields["quote_stale"] is True
        for stage, fields in emitted
    )

    manager.reconcile(now_epoch=1010.0, allow_activation=False)
    assert len(published) == 1

    manager.state["last_tick_epoch"] = 1039.0
    manager.state["last_quote_epoch"] = 1039.0
    manager.reconcile(now_epoch=1040.0, allow_activation=False)
    assert len(published) == 1


def test_label_capture_recovery_does_not_extend_rotation_beyond_retention(
    monkeypatch,
):
    published = []
    event_bus = type(
        "EventBus",
        (),
        {"publish": lambda self, event, payload: published.append((event, payload))},
    )()
    manager = watch.UpperLimitWatchManager("token", object(), event_bus)
    first = watch.UpperLimitCandidate(
        code="123450",
        name="테스트",
        source_trade_date="2026-08-12",
        limit_up_close=1000,
        source_open=900,
        source_high=1000,
        source_low=850,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=10,
    )
    second = watch.UpperLimitCandidate(
        code="234560",
        name="다음",
        source_trade_date="2026-08-12",
        limit_up_close=2000,
        source_open=1800,
        source_high=2000,
        source_low=1700,
        consecutive_count=1,
        cohort="single_limit_up_intraday_traded_close_locked",
        price_band="1천~5천",
        volume=9,
    )
    manager.candidates = [first, second]
    manager.active = first
    manager.loaded_date = "2026-08-13"
    manager.state = {
        "phase": "ABOVE_PRIOR_LIMIT_CLOSE",
        "registered_epoch": 700.0,
        "last_transition_epoch": 800.0,
        "trigger_confirmed_epoch": 900.0,
        "last_tick_epoch": 900.0,
        "last_quote_epoch": 900.0,
        "last_reg_request_epoch": 900.0,
        "last_label_capture_recovery_epoch": 900.0,
        "label_capture_recovery_count": 1,
        "first_tick_epoch": 750.0,
        "reg_request_count": 2,
    }
    monkeypatch.setattr(watch, "feature_enabled", lambda: True)
    monkeypatch.setattr(watch, "_krx_session_phase", lambda _epoch: "OPEN")
    monkeypatch.setattr(manager, "_load_candidates", lambda _epoch: None)
    monkeypatch.setattr(manager, "_write_state", lambda: None)
    monkeypatch.setattr(
        watch.UPPER_LIMIT_OBSERVATION_REGISTRY, "release", lambda _code: True
    )

    manager.reconcile(now_epoch=1146.0, allow_activation=False)

    assert manager.active is None
    assert not any(
        event == "COMMAND_WS_REG" and payload.get("reason") == "label_capture_stale"
        for event, payload in published
    )
    assert any(
        event == "COMMAND_WS_UNREG" and payload.get("reason") == "rotation_due"
        for event, payload in published
    )


def test_full_budget_reclaims_one_rising_before_upper_reg(monkeypatch):
    class Session:
        pass

    class Context:
        def __enter__(self):
            return Session()

        def __exit__(self, *_args):
            return False

    class DB:
        def get_session(self):
            return Context()

    published = []
    event_bus = type(
        "EventBus",
        (),
        {"publish": lambda self, event, payload: published.append((event, payload))},
    )()
    monkeypatch.setattr(
        scalping_scanner, "_active_scanner_watching_count", lambda _db: 16
    )
    monkeypatch.setattr(scalping_scanner, "_scalping_watching_max_active", lambda: 16)
    monkeypatch.setattr(
        scalping_scanner,
        "_select_non_market_gainer_rising_watching_codes",
        lambda _db, max_to_select: ["654320"],
    )
    monkeypatch.setattr(
        scalping_scanner,
        "_expire_scanner_watching_code_in_session",
        lambda _session, code: code == "654320",
    )
    assert scalping_scanner._reserve_upper_limit_observation_slot(DB(), event_bus)
    assert published == [
        (
            "COMMAND_WS_UNREG",
            {
                "codes": ["654320"],
                "source": "upper_limit_watch_rising_slot_reclaim",
                "reason": "conditional_upper_limit_observation_reservation",
            },
        )
    ]
