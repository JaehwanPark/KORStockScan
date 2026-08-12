from __future__ import annotations

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.engine.monitoring import widget_collector_expansion_recommendation as rec

KST = ZoneInfo("Asia/Seoul")


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


def _payload_row(code: str, *, liquidity: float, intraday_range: float) -> dict:
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
                    "spread_bp": 8.0,
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
    assert candidate["estimated_added_requests_per_minute"] == 13
    assert candidate["source_quality_adjusted_ev_pct"] == 0.4
    assert candidate["round_trip_cost_pct"] == 0.2
    assert report["runtime_effect"] is False


def test_recommendation_excludes_manual_operator_symbol(tmp_path):
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

    assert report["status"] == "no_qualified_candidate"
    assert report["exclusion_counts"]["manual_control_excluded"] == 1


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
    assert "자동 생성/기동 없음" in sent[0][2]


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
