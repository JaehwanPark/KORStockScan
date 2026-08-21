from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring import widget_collector_expansion_recommendation as rec
from src.engine.monitoring import widget_research_watch_collector as watch

KST = ZoneInfo("Asia/Seoul")


def test_recommendation_and_collector_capacity_contracts_match():
    assert rec.MAX_ACTIVE_RESEARCH_WATCH_SYMBOLS == watch.MAX_SYMBOLS == 15
    assert rec.MAX_RECOMMENDATIONS == 20


def test_collection_overflow_uses_active_and_candidate_union():
    candidates = [
        {"stock_code": f"1{index:05d}", "recommendation_tier": "research_watch"}
        for index in range(10)
    ]
    active_codes = frozenset(f"2{index:05d}" for index in range(10))

    context = rec._collection_capacity_context(
        candidates=candidates,
        active_codes=active_codes,
    )

    assert context == {
        "active_research_watch_count": 10,
        "candidate_research_watch_count": 10,
        "active_candidate_union_count": 20,
        "research_watch_overflow_candidate_count": 5,
    }


def _replay_row(
    code: str,
    *,
    hit: str,
    end_return: float,
    portable: bool = True,
) -> dict:
    return {
        "stock_code": code,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "entry_path_first_hit": hit,
        "end_return_pct": end_return,
        "mechanical_signal": portable and hit == "target_first",
        "mechanical_candidate_before_spread_gate": portable and hit != "target_first",
        "mechanical_source_issue": None,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _payload_row(
    code: str,
    *,
    liquidity: float,
    intraday_range: float,
    spread_bp: float = 8.0,
) -> dict:
    return {
        "schema": "ai_decision_payload_v1",
        "endpoint": "analyze_target",
        "replay_exact": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "symbol": code,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "sanitized_user_input": {
            "exact_payload": {
                "features": {
                    "entry_liquidity_score": liquidity,
                    "intraday_range_pct": intraday_range,
                    "spread_bp": spread_bp,
                },
                "quote": {"quote_stale": False},
                "entry_candle_context": {
                    "source_quality": {"status": "fresh_consistent"}
                },
            }
        },
    }


def test_recommendation_ranks_positive_liquid_non_active_symbol(tmp_path):
    replay_dir = tmp_path / "replay"
    payload_dir = tmp_path / "payload"
    replay_dir.mkdir()
    payload_dir.mkdir()
    target_date = date(2026, 8, 6)
    replay = {
        "schema": "widget_mechanical_entry_replay_v1",
        "target_date": target_date.isoformat(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "rows": [
            _replay_row("111111", hit="target_first", end_return=0.8),
            _replay_row("111111", hit="target_first", end_return=0.4),
            _replay_row("005930", hit="target_first", end_return=1.0),
            _replay_row("005930", hit="target_first", end_return=1.0),
        ],
    }
    (replay_dir / f"widget_mechanical_entry_replay_{target_date}.json").write_text(
        json.dumps(replay), encoding="utf-8"
    )
    payload_rows = [
        _payload_row("111111", liquidity=85, intraday_range=3.0),
        _payload_row("111111", liquidity=80, intraday_range=2.5),
        _payload_row("005930", liquidity=90, intraday_range=2.0),
    ]
    (payload_dir / f"ai_decision_payloads_{target_date}.jsonl").write_text(
        "\n".join(json.dumps(row) for row in payload_rows) + "\n",
        encoding="utf-8",
    )

    report = rec.build_recommendation_report(
        target_date=target_date,
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        manual_excluded_codes=frozenset(),
    )

    assert report["status"] == "recommendations_ready"
    assert [row["stock_code"] for row in report["recommendations"]] == ["111111"]
    candidate = report["recommendations"][0]
    assert candidate["collector_created"] is False
    assert candidate["service_started"] is False
    assert candidate["research_collection_status"] == "not_enrolled"
    assert candidate["already_enrolled_research_watch"] is False
    assert candidate["estimated_added_requests_per_minute"] is None
    assert candidate["estimated_added_memory_mb"] is None
    assert (
        candidate["resource_profile"] == "shared_budget_paced_research_watch_collector"
    )
    assert (
        candidate["resource_estimate_policy"]
        == "no_fixed_per_symbol_increment;shared_service_total_cap_only"
    )
    assert candidate["estimated_shared_total_requests_per_minute"] == 15
    assert candidate["estimated_shared_service_memory_cap_mb"] == 256
    assert candidate["source_quality_adjusted_ev_pct"] == 0.4
    assert candidate["round_trip_cost_pct"] == 0.2
    assert candidate["recommendation_tier"] == "research_watch"
    assert candidate["observed_trading_date_count"] == 1
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False

    active_report = rec.build_recommendation_report(
        target_date=target_date,
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        active_research_watch_codes=frozenset({"111111"}),
    )
    active_candidate = active_report["recommendations"][0]
    assert active_candidate["research_collection_status"] == "active_shared_collector"
    assert active_candidate["already_enrolled_research_watch"] is True
    assert active_report["recommended_active_research_watch_count"] == 1
    assert active_report["recommended_not_enrolled_count"] == 0


def test_recommendation_artifact_retains_twenty_and_surfaces_collector_overflow(
    monkeypatch,
):
    codes = [f"{index:06d}" for index in range(1, 22)]
    replay = {
        code: {
            "sample_count": 2,
            "target_first_count": 2,
            "adverse_first_count": 0,
            "end_returns": [0.5, 0.5],
            "trading_dates": {"2026-08-18"},
            "mechanical_signal_count": 0,
            "pre_spread_candidate_count": 0,
            "source_qualified_joined_count": 2,
        }
        for code in codes
    }
    features = {
        code: [
            {
                "entry_liquidity_score": 70.0,
                "intraday_range_pct": 3.0,
                "spread_bp": 10.0,
                "quote_fresh": True,
            }
        ]
        for code in codes
    }
    monkeypatch.setattr(
        rec,
        "_load_replay_history",
        lambda *args, **kwargs: (replay, []),
    )
    monkeypatch.setattr(
        rec,
        "_load_feature_history",
        lambda *args, **kwargs: (features, []),
    )
    monkeypatch.setattr(rec, "_load_names", lambda paths: {})

    report = rec.build_recommendation_report(target_date=date(2026, 8, 18))

    assert report["qualified_candidate_count"] == 21
    assert report["reported_candidate_count"] == 20
    assert len(report["recommendations"]) == 20
    assert report["qualified_beyond_report_limit_count"] == 1
    assert report["research_watch_report_limit"] == 20
    assert report["research_watch_collection_capacity"] == 15
    assert report["research_watch_overflow_candidate_count"] == 6

    message = rec.build_telegram_message(report)
    assert "공유수집 총예산 ≤15 req/min, 서비스 메모리 상한 256MB" in message
    assert "예상부하 +13 req/min" not in message
    assert "추천기록 상한 20개 · 동시수집 상한 15개 · 교체/대기 검토 6개" in message
    assert len(message) < 4096


def test_recommendation_does_not_filter_manual_operator_symbol(tmp_path):
    replay_dir = tmp_path / "replay"
    payload_dir = tmp_path / "payload"
    replay_dir.mkdir()
    payload_dir.mkdir()
    target_date = date(2026, 8, 6)
    replay = {
        "schema": "widget_mechanical_entry_replay_v1",
        "target_date": target_date.isoformat(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "rows": [
            _replay_row("111111", hit="target_first", end_return=0.8),
            _replay_row("111111", hit="target_first", end_return=0.4),
        ],
    }
    (replay_dir / f"widget_mechanical_entry_replay_{target_date}.json").write_text(
        json.dumps(replay), encoding="utf-8"
    )
    (payload_dir / f"ai_decision_payloads_{target_date}.jsonl").write_text(
        json.dumps(_payload_row("111111", liquidity=85, intraday_range=3.0)) + "\n",
        encoding="utf-8",
    )

    report = rec.build_recommendation_report(
        target_date=target_date,
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        manual_excluded_codes=frozenset({"111111"}),
    )

    assert report["status"] == "recommendations_ready"
    assert [row["stock_code"] for row in report["recommendations"]] == ["111111"]
    assert "manual_control_excluded" not in report["exclusion_counts"]
    assert report["manual_control_exclusion_applied"] is False
    assert report["source"]["manual_control_exclusion_applied"] is False


def test_admin_notifier_sends_once_and_never_creates_service(tmp_path):
    sent: list[tuple[str, str, str]] = []
    report = {
        "schema": "widget_collector_expansion_recommendation_v1",
        "status": "no_qualified_candidate",
        "authority": rec.AUTHORITY,
        "target_date": "2026-08-06",
        "recommendation_only": True,
        "widget_runtime_effect": False,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "collector_created": False,
        "service_started": False,
        "metric_contract": rec.METRIC_CONTRACT,
        "recommendations": [],
    }
    notifier = rec.WidgetExpansionRecommendationNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
        enabled=True,
    )

    assert notifier.notify(report) == "sent"
    assert notifier.notify(report) == "duplicate"
    assert sent[0][0:2] == ("token", "admin")
    assert "자동 생성/기동 권한 없음" in sent[0][2]


def test_telegram_distinguishes_already_enrolled_research_watch():
    report = {
        "target_date": "2026-08-21",
        "recommendations": [
            {
                "stock_code": "111111",
                "stock_name": "기존관찰",
                "recommendation_score": 70.0,
                "recommendation_tier": "research_watch",
                "observed_trading_date_count": 3,
                "sample_count": 5,
                "target_first_count": 3,
                "adverse_first_count": 1,
                "source_quality_adjusted_ev_pct": 0.3,
                "median_entry_liquidity_score": 70.0,
                "median_intraday_range_pct": 4.0,
                "median_spread_bp": 10.0,
                "estimated_shared_total_requests_per_minute": 15,
                "estimated_shared_service_memory_cap_mb": 256,
                "research_collection_status": "active_shared_collector",
            }
        ],
        "implementation_review_candidate_count": 0,
        "research_watch_candidate_count": 1,
        "recommended_active_research_watch_count": 1,
        "recommended_not_enrolled_count": 0,
        "research_watch_capacity_status": "verified_active_candidate_union",
    }

    message = rec.build_telegram_message(report)

    assert "수집상태: 기존 공동수집기 등록·축적 중" in message
    assert "표시된 후보는 기존 공동수집기에 모두 등록" in message
    assert "미등록 후보" not in message


def test_default_target_date_uses_completed_session_date():
    assert rec._resolve_default_target_date(
        now=datetime(2026, 8, 6, 21, 15, tzinfo=KST)
    ) == date(2026, 8, 6)
    assert rec._resolve_default_target_date(
        now=datetime(2026, 8, 6, 8, 0, tzinfo=KST)
    ) == date(2026, 8, 5)
    assert rec._resolve_default_target_date(
        now=datetime(2026, 8, 8, 21, 15, tzinfo=KST)
    ) == date(2026, 8, 7)


def test_recommendation_keeps_positive_ev_observation_candidate_without_portable_setup(
    tmp_path,
):
    replay_dir = tmp_path / "replay"
    payload_dir = tmp_path / "payload"
    replay_dir.mkdir()
    payload_dir.mkdir()
    target_date = date(2026, 8, 6)
    replay = {
        "schema": "widget_mechanical_entry_replay_v1",
        "target_date": target_date.isoformat(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "rows": [
            _replay_row("111111", hit="target_first", end_return=0.8, portable=False),
            _replay_row("111111", hit="target_first", end_return=0.4, portable=False),
        ],
    }
    (replay_dir / f"widget_mechanical_entry_replay_{target_date}.json").write_text(
        json.dumps(replay), encoding="utf-8"
    )
    (payload_dir / f"ai_decision_payloads_{target_date}.jsonl").write_text(
        json.dumps(_payload_row("111111", liquidity=85, intraday_range=3.0)) + "\n",
        encoding="utf-8",
    )

    report = rec.build_recommendation_report(
        target_date=target_date,
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        manual_excluded_codes=frozenset(),
    )

    assert report["status"] == "recommendations_ready"
    candidate = report["recommendations"][0]
    assert candidate["stock_code"] == "111111"
    assert candidate["portability_ratio_pct"] == 0.0


def test_cli_writes_replay_and_recommendation_without_notification(tmp_path):
    payload_dir = tmp_path / "payload"
    label_dir = tmp_path / "labels"
    replay_dir = tmp_path / "replay"
    output_dir = tmp_path / "output"
    for directory in (payload_dir, label_dir):
        directory.mkdir()
    (payload_dir / "ai_decision_payloads_2026-08-06.jsonl").write_text(
        "", encoding="utf-8"
    )
    (label_dir / "ai_decision_outcome_labels_2026-08-06.json").write_text(
        json.dumps(
            {
                "schema": "ai_decision_outcome_labels_v1",
                "target_date": "2026-08-06",
                "generated_at": "2026-08-06T21:00:00+09:00",
                "status": "partial_horizons_keep_maturing",
                "labels": [],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    assert (
        rec.main(
            [
                "--target-date",
                "2026-08-06",
                "--payload-dir",
                str(payload_dir),
                "--label-dir",
                str(label_dir),
                "--replay-dir",
                str(replay_dir),
                "--output-dir",
                str(output_dir),
                "--write",
            ]
        )
        == 0
    )

    assert (replay_dir / "widget_mechanical_entry_replay_2026-08-06.json").exists()
    report_path = (
        output_dir / "widget_collector_expansion_recommendation_2026-08-06.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "no_qualified_candidate"
    assert report["telegram_status"] == "not_requested"
    assert report["collector_created"] is False


def test_source_artifact_gate_rejects_missing_or_authority_mismatched_label(
    tmp_path,
):
    target_date = date(2026, 8, 6)
    payload_path = tmp_path / "payload.jsonl"
    label_path = tmp_path / "labels.json"

    assert rec._source_artifact_issues(
        target_date=target_date,
        payload_path=payload_path,
        label_path=label_path,
    ) == [
        "exact_payload_artifact_missing",
        "outcome_label_artifact_missing_or_invalid",
    ]

    payload_path.write_text("", encoding="utf-8")
    label_path.write_text(
        json.dumps(
            {
                "schema": "ai_decision_outcome_labels_v1",
                "target_date": target_date.isoformat(),
                "generated_at": "2026-08-06T21:00:00+09:00",
                "status": "mature_label_rows_available",
                "labels": [],
                "runtime_effect": True,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    assert rec._source_artifact_issues(
        target_date=target_date,
        payload_path=payload_path,
        label_path=label_path,
    ) == ["outcome_label_contract_mismatch"]


def test_recommendation_marks_multi_date_liquid_sample_implementation_review_ready(
    tmp_path,
):
    replay_dir = tmp_path / "replay"
    payload_dir = tmp_path / "payload"
    replay_dir.mkdir()
    payload_dir.mkdir()
    dates = [date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6)]
    for index, trading_date in enumerate(dates):
        rows = [
            _replay_row("111111", hit="target_first", end_return=0.6),
            _replay_row("111111", hit="target_first", end_return=0.4),
        ]
        if index == 2:
            rows = rows[:1]
        replay = {
            "schema": "widget_mechanical_entry_replay_v1",
            "target_date": trading_date.isoformat(),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "rows": rows,
        }
        (replay_dir / f"widget_mechanical_entry_replay_{trading_date}.json").write_text(
            json.dumps(replay), encoding="utf-8"
        )
        (payload_dir / f"ai_decision_payloads_{trading_date}.jsonl").write_text(
            json.dumps(
                _payload_row(
                    "111111",
                    liquidity=85,
                    intraday_range=4.0,
                    spread_bp=12.0,
                )
            )
            + "\n",
            encoding="utf-8",
        )

    report = rec.build_recommendation_report(
        target_date=dates[-1],
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        manual_excluded_codes=frozenset(),
    )

    candidate = report["recommendations"][0]
    assert candidate["recommendation_tier"] == "implementation_review"
    assert candidate["implementation_review_ready"] is True
    assert candidate["implementation_review_blockers"] == []
    assert candidate["observed_trading_date_count"] == 3
    assert candidate["sample_count"] == 5
    assert report["implementation_review_candidate_count"] == 1


def test_recommendation_keeps_wide_spread_candidate_as_research_watch(tmp_path):
    replay_dir = tmp_path / "replay"
    payload_dir = tmp_path / "payload"
    replay_dir.mkdir()
    payload_dir.mkdir()
    target_date = date(2026, 8, 6)
    replay = {
        "schema": "widget_mechanical_entry_replay_v1",
        "target_date": target_date.isoformat(),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "rows": [
            _replay_row("111111", hit="target_first", end_return=0.8),
            _replay_row("111111", hit="target_first", end_return=0.4),
        ],
    }
    (replay_dir / f"widget_mechanical_entry_replay_{target_date}.json").write_text(
        json.dumps(replay), encoding="utf-8"
    )
    (payload_dir / f"ai_decision_payloads_{target_date}.jsonl").write_text(
        json.dumps(
            _payload_row("111111", liquidity=85, intraday_range=3.0, spread_bp=60.0)
        )
        + "\n",
        encoding="utf-8",
    )

    report = rec.build_recommendation_report(
        target_date=target_date,
        replay_dir=replay_dir,
        payload_dir=payload_dir,
        manual_excluded_codes=frozenset(),
    )

    candidate = report["recommendations"][0]
    assert candidate["recommendation_tier"] == "research_watch"
    assert "median_spread_too_wide" in candidate["implementation_review_blockers"]
    assert report["implementation_review_candidate_count"] == 0
    message = rec.build_telegram_message(report)
    assert "구현검토 0개 · 연구관찰 1개" in message
    assert "즉시 구현검토 후보는 없으며" in message


def test_load_names_reads_archived_gzip_sentinel(monkeypatch, tmp_path):
    replay_dir = tmp_path / "replay"
    sentinel_dir = tmp_path / "sentinel"
    replay_dir.mkdir()
    sentinel_dir.mkdir()
    replay_path = replay_dir / "widget_mechanical_entry_replay_2026-08-06.json"
    replay_path.write_text("{}", encoding="utf-8")
    sentinel_path = sentinel_dir / "buy_funnel_sentinel_events_2026-08-06.jsonl.gz"
    with gzip.open(sentinel_path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"stock_code": "111111", "stock_name": "테스트"}))
        handle.write("\n")
    monkeypatch.setattr(rec, "DEFAULT_SENTINEL_DIR", sentinel_dir)

    assert rec._load_names([replay_path]) == {"111111": "테스트"}


def test_load_names_ignores_damaged_display_only_archive(monkeypatch, tmp_path):
    replay_dir = tmp_path / "replay"
    sentinel_dir = tmp_path / "sentinel"
    replay_dir.mkdir()
    sentinel_dir.mkdir()
    replay_path = replay_dir / "widget_mechanical_entry_replay_2026-08-06.json"
    replay_path.write_text("{}", encoding="utf-8")
    (sentinel_dir / "buy_funnel_sentinel_events_2026-08-06.jsonl.gz").write_bytes(
        b"not-gzip"
    )
    monkeypatch.setattr(rec, "DEFAULT_SENTINEL_DIR", sentinel_dir)

    assert rec._load_names([replay_path]) == {}


def test_wait_for_source_artifacts_retries_without_transient_service_failure(
    monkeypatch, tmp_path
):
    calls = 0
    clock = 0.0

    def fake_issues(**_kwargs):
        nonlocal calls
        calls += 1
        return ["outcome_label_contract_mismatch"] if calls < 3 else []

    def monotonic():
        return clock

    def sleeper(seconds):
        nonlocal clock
        clock += seconds

    monkeypatch.setattr(rec, "_source_artifact_issues", fake_issues)

    issues = rec._wait_for_source_artifacts(
        target_date=date(2026, 8, 6),
        payload_path=tmp_path / "payload",
        label_path=tmp_path / "label",
        wait_sec=60,
        poll_sec=10,
        monotonic=monotonic,
        sleeper=sleeper,
    )

    assert issues == []
    assert calls == 3
    assert clock == 20.0


def test_systemd_service_waits_for_postclose_label_contract():
    service = Path(
        "deploy/systemd/korstockscan-widget-expansion-recommendation.service"
    ).read_text(encoding="utf-8")
    wrapper = Path("deploy/run_machine_microstructure_final_refresh.sh").read_text(
        encoding="utf-8"
    )

    assert (
        "ExecStart=/home/ubuntu/KORStockScan/deploy/run_machine_microstructure_final_refresh.sh"
        in service
    )
    assert "--source-wait-sec 900" in wrapper
    assert "--source-poll-sec 30" in wrapper
    assert "TimeoutStartSec=1200" in service
