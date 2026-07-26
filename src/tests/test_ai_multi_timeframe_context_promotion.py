import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import ai_multi_timeframe_context_promotion as promotion
from src.engine.scalping.entry_candle_context import entry_candle_context_enabled
from src.engine.scalping.holding_decision_context import (
    holding_decision_context_enabled,
)
from src.engine.scalping import multi_timeframe_context

KST = ZoneInfo("Asia/Seoul")
TEST_NOW = datetime(2026, 7, 27, 8, 30, tzinfo=KST)


def _validation(provider_none=0):
    results = []
    for symbol, venue in (
        ("005930", "KRX"),
        ("096770", "KRX"),
        ("100090", "KRX"),
        ("005930_NX", "NXT"),
    ):
        results.append(
            {
                "symbol": symbol,
                "venue": venue,
                "summary": {"required_source_field_match_status": "pass"},
                "ai_payload_exact_validation": {
                    "summary": {
                        "required_payload_match_status": "pass",
                        "request_count": 1,
                        "endpoint_counts": {
                            "analyze_target": 1,
                            "entry_price": 1,
                            "holding_score": 1,
                            "holding_flow": 1,
                        },
                        "mismatch_count": 0,
                        "source_unavailable_count": 0,
                        "provider_none_count": 0,
                        "forming_bar_included_count": 0,
                    }
                },
            }
        )
    return {
        "schema": "ai_input_external_validation_v1",
        "date": "2026-07-27",
        "status": "pass" if not provider_none else "fail",
        "summary": {
            "mismatch_count": 0,
            "payload_mismatch_count": 0,
            "payload_source_unavailable_count": 0,
            "provider_none_count": provider_none,
        },
        "results": results,
    }


def _review():
    return {
        "target_date": "2026-07-27",
        "reviewed_at": "2026-07-26T15:00:00+09:00",
        "reviewed_source_hash": promotion.reviewed_source_hash(),
        "status": "pass",
        "finding_count": 0,
        "operator_authorization_id": promotion.AUTHORITY_ID,
        "checks": {"tests": "pass", "compile": "pass", "diff_check": "pass"},
    }


def _runtime_manifest(tmp_path):
    return {
        "target_date": "2026-07-27",
        "source_date": "2026-07-24",
        "generated_at": "2026-07-27T08:30:00+09:00",
        "env_file": str(tmp_path / "threshold_runtime_env_2026-07-27.env"),
        "env_overrides": {"KEEP_EXISTING": "yes"},
        "selected_families": ["existing_family"],
    }


def test_evaluate_promotion_is_binary_full_market(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    assert report["status"] == "pass"
    assert report["decision"] == "promoted_all_market_sessions_full"
    assert report["runtime_activation"] is True
    assert report["scope"]["sessions"] == list(promotion.EXPECTED_SESSIONS)
    assert report["scope"]["endpoints"] == list(promotion.EXPECTED_ENDPOINTS)
    assert all(
        value == "true"
        for key, value in report["env_overrides"].items()
        if not key.endswith("_ACTIVE_DATE")
    )


def test_evaluate_promotion_fails_closed_on_provider_none(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(provider_none=1),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    assert report["status"] == "fail"
    assert report["decision"] == "blocked_provider_or_schema"
    assert report["env_overrides"] == {}


def test_evaluate_promotion_requires_actual_exact_calls_for_each_core_endpoint(
    tmp_path,
):
    validation = _validation()
    for row in validation["results"]:
        row["ai_payload_exact_validation"]["summary"]["endpoint_counts"].pop(
            "holding_flow"
        )
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=validation,
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    assert report["status"] == "fail"
    assert report["decision"] == "blocked_provider_or_schema"
    assert "required_endpoint_exact_request_missing:holding_flow" in report["findings"]


def test_evaluate_promotion_fails_closed_on_reviewed_source_drift(tmp_path):
    review = _review()
    review["reviewed_source_hash"] = "stale-review-hash"
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=review,
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    assert report["status"] == "fail"
    assert report["decision"] == "blocked_review_or_env"
    assert report["findings"] == ["reviewed_source_hash_mismatch"]
    assert report["env_overrides"] == {}


def test_evaluate_promotion_is_not_due_before_target_premarket(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=datetime(2026, 7, 26, 23, 0, tzinfo=KST),
    )
    assert report["status"] == "fail"
    assert report["decision"] == "not_yet_due"
    assert report["promotion_window_status"] == "not_yet_due"
    assert report["env_overrides"] == {}


def test_apply_transaction_preserves_env_and_writes_commit_marker_last(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir()
    promotion_dir = tmp_path / "runtime"
    monkeypatch.setattr(promotion, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    manifest = _runtime_manifest(runtime_dir)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    committed = promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    saved = json.loads(
        promotion.runtime_manifest_path("2026-07-27").read_text(encoding="utf-8")
    )
    assert saved["env_overrides"]["KEEP_EXISTING"] == "yes"
    assert (
        saved["env_overrides"]["KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED"]
        == "true"
    )
    assert saved["selected_families"] == ["existing_family"]
    assert (
        saved["ai_multi_timeframe_context_promotion_status"]
        == "promoted_all_market_sessions_full"
    )
    assert committed["transaction_status"] == "committed"
    assert promotion.promotion_path("2026-07-27").exists()


def test_apply_transaction_rejects_outside_target_premarket(tmp_path):
    manifest = _runtime_manifest(tmp_path)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    with pytest.raises(ValueError, match="outside the target-date PREMARKET"):
        promotion.apply_promotion_transaction(
            report,
            manifest,
            now=datetime(2026, 7, 27, 9, 1, tzinfo=KST),
        )


def test_runtime_hook_trusts_only_committed_hash_matched_artifact(
    tmp_path, monkeypatch
):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir()
    promotion_dir = tmp_path / "runtime"
    monkeypatch.setattr(promotion, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    manifest = _runtime_manifest(runtime_dir)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    monkeypatch.setattr(multi_timeframe_context, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(multi_timeframe_context, "PROMOTION_DIR", promotion_dir)
    multi_timeframe_context._PROMOTION_CACHE.clear()
    multi_timeframe_context._ACTIVATION_CACHE.clear()
    now = datetime(2026, 7, 27, 8, 35, tzinfo=KST)
    assert multi_timeframe_context.full_market_promotion_active(now) is True
    assert (
        multi_timeframe_context.full_market_promotion_active(
            datetime(2026, 7, 27, 8, 29, tzinfo=KST)
        )
        is False
    )
    assert (
        multi_timeframe_context.full_market_promotion_active(
            datetime(2026, 7, 28, 9, 0, tzinfo=KST)
        )
        is True
    )
    for name in promotion.full_market_env("2026-07-27"):
        monkeypatch.delenv(name, raising=False)
    assert entry_candle_context_enabled(
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        now_ts=now,
    )
    assert holding_decision_context_enabled(
        venue="PREMARKET_KRX_LIKE",
        session="premarket_krx_like",
        decision_kind="holding_flow",
        now_ts=now,
    )
    env_path = runtime_dir / "threshold_runtime_env_2026-07-27.env"
    env_path.write_text(
        env_path.read_text(encoding="utf-8") + "# tampered\n", encoding="utf-8"
    )
    assert multi_timeframe_context.full_market_promotion_active(now) is False


def _payload(endpoint, schema, venue="KRX"):
    return {
        "endpoint": endpoint,
        "payload_sha256": f"hash-{endpoint}",
        "sanitized_user_input": {
            "context": {
                "schema": schema,
                "venue": venue,
                "input_bundle_version": promotion.FAMILY,
                "bars": [{"forming": False, "partial_volume": False}],
            }
        },
    }


def _trace(endpoint, venue="KRX"):
    return {
        "decision_ts": "2026-07-27T09:00:01+09:00",
        "decision_trace_id": f"trace-{endpoint}",
        "endpoint": endpoint,
        "effective_venue": venue,
        "session_bucket": "KRX_REGULAR",
        "provider_actual": "openai",
        "payload_replay_exact": True,
        "payload_sha256": f"hash-{endpoint}",
        "response_sha256": f"response-{endpoint}",
    }


def test_first_observation_keeps_missing_endpoint_pending():
    payloads = [
        _payload("analyze_target", "entry_candle_context_v1"),
        _payload("holding_score", "holding_decision_context_v1"),
    ]
    traces = [_trace("analyze_target"), _trace("holding_score")]
    report = promotion.build_first_observation_report(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
            "runtime_manifest_path": "manifest",
        },
        traces=traces,
        payloads=payloads,
    )
    assert report["status"] == "global_runtime_full_pending_natural_endpoint"
    assert "entry_price" in report["pending_natural_endpoints"]
    assert "NXT_AFTERMARKET" in report["pending_natural_sessions"]
    assert report["rollback_required"] is False


def test_first_observation_rejects_uncommitted_evaluation():
    report = promotion.build_first_observation_report(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace("analyze_target")],
        payloads=[_payload("analyze_target", "entry_candle_context_v1")],
    )

    assert report["status"] == "promotion_not_authorized"
    assert report["observations"] == []


def test_first_observation_requests_context_only_rollback_on_provider_none():
    report = promotion.build_first_observation_report(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[{**_trace("analyze_target"), "provider_actual": "none"}],
        payloads=[_payload("analyze_target", "entry_candle_context_v1")],
    )
    assert report["status"] == "rolled_back_context_only"
    assert report["rollback_required"] is True
    assert report["rollback_scope"] == "multi_timeframe_context_only"


def test_observation_allows_separately_marked_forming_one_minute_bar():
    payload = _payload("analyze_target", "entry_candle_context_v1")
    context = payload["sanitized_user_input"]["context"]
    context["bars"] = [{"forming": True, "partial_volume": True}]
    context["multi_timeframe_context"] = {
        "input_bundle_version": promotion.FAMILY,
        "multi_timeframe_bars": {"3m": [{"forming": False, "partial_volume": False}]},
        "source_quality": {"status": "pass"},
    }
    report = promotion.build_first_observation_report(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[_trace("analyze_target")],
        payloads=[payload],
    )
    assert report["failed_observation_count"] == 0


def test_source_quality_zero_counts_do_not_create_false_conflict():
    assert (
        promotion._source_quality_conflicted(
            {
                "status": "pass",
                "conflict_count": 0,
                "duplicate_count": 0,
                "invalid_count": 0,
            }
        )
        is False
    )
    assert promotion._source_quality_conflicted({"conflict_count": 1}) is True


def test_observation_joins_duplicate_payload_hash_by_endpoint():
    entry = _payload("analyze_target", "entry_candle_context_v1")
    holding = _payload("holding_score", "holding_decision_context_v1")
    entry["payload_sha256"] = holding["payload_sha256"] = "shared-hash"
    trace = {
        **_trace("analyze_target"),
        "payload_sha256": "shared-hash",
    }
    report = promotion.build_first_observation_report(
        target_date="2026-07-27",
        promotion={
            "decision": "promoted_all_market_sessions_full",
            "runtime_activation": True,
            "transaction_status": "committed",
            "promoted_at": "2026-07-27T08:30:00+09:00",
        },
        traces=[trace],
        payloads=[holding, entry],
    )
    assert report["failed_observation_count"] == 0


def test_context_rollback_invalidates_commit_marker(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir()
    promotion_dir = tmp_path / "runtime"
    monkeypatch.setattr(promotion, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    manifest = _runtime_manifest(runtime_dir)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    rolled = promotion.rollback_context_transaction(
        target_date="2026-07-27",
        observation={
            "rollback_required": True,
            "status": "rolled_back_context_only",
            "violations": ["provider_none"],
        },
    )
    assert rolled["runtime_activation"] is False
    assert rolled["decision"] == "rolled_back_context_only"
    saved = json.loads(
        promotion.runtime_manifest_path("2026-07-27").read_text(encoding="utf-8")
    )
    assert (
        saved["env_overrides"]["KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED"]
        == "false"
    )
