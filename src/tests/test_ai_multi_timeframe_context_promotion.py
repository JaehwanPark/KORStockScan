import gzip
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


def test_exact_source_iterator_reads_gzip_only_generation(tmp_path):
    logical = tmp_path / "ai_decision_trace_2026-07-24.jsonl"
    with gzip.open(logical.with_suffix(".jsonl.gz"), "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"decision_trace_id": "trace-1"}) + "\n")

    assert promotion._iter_jsonl(logical) == [{"decision_trace_id": "trace-1"}]


def _validation(provider_none=0):
    results = []
    for symbol in promotion.DEFAULT_PREMARKET_SYMBOLS:
        results.append(
            {
                "symbol": symbol,
                "venue": "NXT",
                "summary": {"required_source_field_match_status": "fail"},
                "ai_payload_exact_validation": {
                    "summary": {
                        "required_payload_match_status": "pass",
                        "request_count": 1,
                        "valid_exact_request_count": 1,
                        "endpoint_counts": {
                            "analyze_target": 1,
                            "entry_price": 1,
                            "holding_score": 1,
                            "holding_flow": 1,
                        },
                        "mismatch_count": 0,
                        "source_unavailable_count": 0,
                        "provider_none_count": provider_none,
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


def _golden_validation():
    return {
        "schema": "ai_input_external_validation_v1",
        "date": promotion.DEFAULT_KRX_GOLDEN_DATE,
        "status": "fail",
        "summary": {
            "mismatch_count": 0,
            "payload_mismatch_count": 0,
            "payload_source_unavailable_count": 0,
            "provider_none_count": 0,
        },
        "results": [
            {
                "symbol": symbol,
                "venue": "KRX",
                "summary": {
                    "required_source_field_match_status": "pass",
                    "mismatch_count": 0,
                },
                "ai_payload_exact_validation": {
                    "summary": {
                        "required_payload_match_status": "fail",
                        "request_count": 0,
                        "valid_exact_request_count": 0,
                        "endpoint_counts": {},
                    }
                },
            }
            for symbol in promotion.DEFAULT_KRX_GOLDEN_SYMBOLS
        ],
    }


def _same_day_krx_validation():
    validation = _validation()
    validation["status"] = "fail"
    validation["results"] = []
    for symbol in promotion.DEFAULT_KRX_GOLDEN_SYMBOLS:
        validation["results"].append(
            {
                "symbol": symbol,
                "venue": "KRX",
                "summary": {
                    "required_source_field_match_status": "pass",
                    "mismatch_count": 0,
                },
                "ai_payload_exact_validation": {
                    "summary": {
                        "required_payload_match_status": "pass",
                        "request_count": 1,
                        "valid_exact_request_count": 1,
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
    return validation


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


def _load_full_market_runtime_env(monkeypatch, target_date):
    for name, value in promotion.full_market_env(target_date).items():
        monkeypatch.setenv(name, value)


def test_evaluate_promotion_is_binary_full_market(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
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
    assert report["env_overrides"]["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE"] == "exact_v2"
    assert report["env_overrides"]["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED"] == "true"
    assert (
        report["env_overrides"]["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE"]
        == "2026-07-27"
    )
    assert all(
        value == "true"
        for key, value in report["env_overrides"].items()
        if not key.endswith("_ACTIVE_DATE")
        and not key.startswith("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_")
    )


def test_evaluate_promotion_fails_closed_on_provider_none(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(provider_none=1),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    assert report["status"] == "fail"
    assert report["decision"] == "blocked_provider_or_schema"
    assert report["env_overrides"] == {}


def test_operator_directed_promotion_bypasses_only_validation_and_review(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation={},
        golden_validation={},
        review={},
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        operator_directed=True,
        operator_authorization_id=promotion.operator_directed_authority_id(
            "2026-07-27"
        ),
        operator_reason="Explicit operator-directed full-market Exact V2 activation.",
        now=TEST_NOW,
    )

    assert report["status"] == "pass"
    assert report["decision"] == "promoted_all_market_sessions_full"
    assert report["promotion_mode"] == promotion.OPERATOR_DIRECTED_PROMOTION_MODE
    assert report["validation_gate"]["bypassed"] is True
    assert report["validation_gate"]["bypassed_findings"]
    assert report["env_overrides"] == promotion.full_market_env("2026-07-27")


def test_operator_directed_promotion_requires_explicit_authority_and_reason(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation={},
        golden_validation={},
        review={},
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        operator_directed=True,
        operator_authorization_id=promotion.operator_directed_authority_id(
            "2026-07-28"
        ),
        operator_reason="",
        now=TEST_NOW,
    )

    assert report["status"] == "fail"
    assert report["decision"] == "blocked_review_or_env"
    assert report["env_overrides"] == {}
    assert "operator_directed_authorization_missing_or_invalid" in report["findings"]
    assert "operator_directed_reason_missing" in report["findings"]


def test_operator_directed_promotion_can_use_the_remaining_apply_window(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation={},
        golden_validation={},
        review={},
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        operator_directed=True,
        operator_authorization_id=promotion.operator_directed_authority_id(
            "2026-07-27"
        ),
        operator_reason="Explicit operator-directed full-market Exact V2 activation.",
        now=datetime(2026, 7, 27, 8, 55, tzinfo=KST),
    )

    assert report["status"] == "pass"
    assert report["promotion_window_status"] == "pass"


def test_validated_promotion_keeps_the_existing_review_end_boundary(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=datetime(2026, 7, 27, 8, 40, tzinfo=KST),
    )

    assert report["status"] == "pass"
    assert report["promotion_window_status"] == "pass"


def test_operator_directed_promotion_closes_at_market_open(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation={},
        golden_validation={},
        review={},
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        operator_directed=True,
        operator_authorization_id=promotion.operator_directed_authority_id(
            "2026-07-27"
        ),
        operator_reason="Explicit operator-directed full-market Exact V2 activation.",
        now=datetime(2026, 7, 27, 9, 0, tzinfo=KST),
    )

    assert report["status"] == "fail"
    assert report["promotion_window_status"] == "premarket_validation_window_closed"


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
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    assert report["status"] == "fail"
    assert report["decision"] == "blocked_provider_or_schema"
    assert (
        "premarket_required_endpoint_exact_request_missing:holding_flow"
        in report["findings"]
    )


def test_evaluate_promotion_uses_nxt_exact_and_krx_golden_split(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    assert report["status"] == "pass"
    assert report["evidence_basis"]["premarket_exact"]["venue"] == "NXT_PREMARKET"
    assert report["evidence_basis"]["krx_golden_source"]["date"] == "2026-07-24"


def test_evaluate_promotion_fails_on_krx_golden_mismatch(tmp_path):
    golden = _golden_validation()
    golden["results"][0]["summary"]["mismatch_count"] = 1
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=golden,
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    assert report["status"] == "fail"
    assert (
        f"krx_golden_symbol_mismatch:{promotion.DEFAULT_KRX_GOLDEN_SYMBOLS[0]}"
        in report["findings"]
    )


def test_evaluate_promotion_ignores_other_venue_summary_failures(tmp_path):
    validation = _validation()
    validation["summary"].update(
        {
            "payload_mismatch_count": 99,
            "payload_source_unavailable_count": 99,
            "provider_none_count": 99,
        }
    )
    golden = _golden_validation()
    golden["summary"]["mismatch_count"] = 99

    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=validation,
        golden_validation=golden,
        review=_review(),
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    assert report["status"] == "pass"
    assert report["findings"] == []


def test_evaluate_promotion_fails_closed_on_reviewed_source_drift(tmp_path):
    review = _review()
    review["reviewed_source_hash"] = "stale-review-hash"
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=review,
        runtime_manifest=_runtime_manifest(tmp_path),
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    assert report["status"] == "fail"
    assert report["decision"] == "blocked_review_or_env"
    assert report["findings"] == ["reviewed_source_hash_mismatch"]
    assert report["env_overrides"] == {}


def test_reviewed_source_hash_covers_live_ai_payload_producer():
    assert "src/engine/ai_engine_openai.py" in promotion.REVIEWED_SOURCE_FILES


def test_evaluate_promotion_is_not_due_before_target_premarket(tmp_path):
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
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
        golden_validation=_golden_validation(),
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
    assert saved["env_overrides"]["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE"] == "exact_v2"
    assert (
        saved["ai_multi_timeframe_context_promotion_status"]
        == "promoted_all_market_sessions_full"
    )
    assert committed["transaction_status"] == "committed"
    assert promotion.promotion_path("2026-07-27").exists()


def test_committed_promotion_exports_authoritative_exact_v2_env(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir()
    promotion_dir = tmp_path / "runtime"
    monkeypatch.setattr(promotion, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    manifest = _runtime_manifest(runtime_dir)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)

    authoritative = promotion.authoritative_runtime_env("2026-07-27")

    assert authoritative == promotion.full_market_env("2026-07-27")
    assert "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE=exact_v2" in (
        promotion.authoritative_runtime_env_exports("2026-07-27")
    )
    assert promotion.authoritative_runtime_env("2026-07-28") == (
        promotion.full_market_env("2026-07-28")
    )


def test_authoritative_runtime_env_rejects_tampered_commit_file(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime_env"
    runtime_dir.mkdir()
    promotion_dir = tmp_path / "runtime"
    monkeypatch.setattr(promotion, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    manifest = _runtime_manifest(runtime_dir)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    promotion.runtime_env_path("2026-07-27").write_text(
        "export KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE=baseline_v1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="runtime env hash mismatch"):
        promotion.authoritative_runtime_env("2026-07-27")


def test_authoritative_runtime_env_rejects_tampered_authority_on_rollover(
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
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    artifact_path = promotion.promotion_path("2026-07-27")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["operator_authorization_id"] = "tampered"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="active committed promotion"):
        promotion.authoritative_runtime_env("2026-07-28")


def test_authoritative_runtime_env_does_not_reactivate_rolled_back_context(
    tmp_path, monkeypatch
):
    promotion_dir = tmp_path / "runtime"
    promotion_dir.mkdir()
    monkeypatch.setattr(promotion, "PROMOTION_DIR", promotion_dir)
    promotion.promotion_path("2026-07-27").write_text(
        json.dumps(
            {
                "target_date": "2026-07-27",
                "decision": "rolled_back_context_only",
                "runtime_activation": False,
                "transaction_status": "rolled_back",
            }
        ),
        encoding="utf-8",
    )

    assert promotion.authoritative_runtime_env("2026-07-27") == {}
    assert promotion.authoritative_runtime_env("2026-07-28") == {}


def test_promotion_rollback_restores_previous_preflight_contract(tmp_path):
    manifest = _runtime_manifest(tmp_path)
    manifest["env_overrides"].update(
        {
            "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE": "baseline_v1",
            "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED": "true",
            "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE": "2026-07-24",
        }
    )
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
        review=_review(),
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        now=TEST_NOW,
    )

    rollback = report["rollback_env_overrides"]
    assert rollback["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE"] == "baseline_v1"
    assert rollback["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED"] == "true"
    assert rollback["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE"] == "2026-07-24"
    assert rollback["KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED"] == "false"


def test_promotion_rollback_preserves_boolean_false_preflight_required():
    rollback = promotion.context_only_rollback_env(
        "2026-07-27",
        {"KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED": False},
    )

    assert rollback["KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED"] == "false"


def test_apply_transaction_rejects_outside_target_premarket(tmp_path):
    manifest = _runtime_manifest(tmp_path)
    report = promotion.evaluate_promotion(
        target_date="2026-07-27",
        validation=_validation(),
        golden_validation=_golden_validation(),
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
        golden_validation=_golden_validation(),
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


def test_runtime_hook_accepts_only_a_committed_operator_directed_artifact(
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
        validation={},
        golden_validation={},
        review={},
        runtime_manifest=manifest,
        runtime_verify={"status": "pass", "passed": True},
        operator_directed=True,
        operator_authorization_id=promotion.operator_directed_authority_id(
            "2026-07-27"
        ),
        operator_reason="Explicit operator-directed full-market Exact V2 activation.",
        now=TEST_NOW,
    )
    promotion.apply_promotion_transaction(report, manifest, now=TEST_NOW)
    monkeypatch.setattr(multi_timeframe_context, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(multi_timeframe_context, "PROMOTION_DIR", promotion_dir)
    multi_timeframe_context._PROMOTION_CACHE.clear()
    multi_timeframe_context._ACTIVATION_CACHE.clear()

    state = multi_timeframe_context.promotion_activation_state(TEST_NOW)

    assert state["active"] is False
    assert state["activation_source"] == "operator_directed_runtime_env_not_loaded"
    assert "KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE" in state["missing_runtime_env"]

    _load_full_market_runtime_env(monkeypatch, "2026-07-27")
    state = multi_timeframe_context.promotion_activation_state(TEST_NOW)

    assert state["active"] is True
    assert state["promotion_mode"] == promotion.OPERATOR_DIRECTED_PROMOTION_MODE
    assert state["runtime_env_readback"] == "complete_exact_v2"
    assert (
        multi_timeframe_context.full_market_promotion_active(
            datetime(2026, 7, 28, 8, 30, tzinfo=KST)
        )
        is False
    )

    rollover_env = promotion.authoritative_runtime_env("2026-07-28")
    assert rollover_env == promotion.full_market_env("2026-07-28")
    for name, value in rollover_env.items():
        monkeypatch.setenv(name, value)
    multi_timeframe_context._ACTIVATION_CACHE.clear()

    rollover_state = multi_timeframe_context.promotion_activation_state(
        datetime(2026, 7, 28, 8, 30, tzinfo=KST)
    )

    assert rollover_state["active"] is True
    assert rollover_state["target_date"] == "2026-07-28"
    assert rollover_state["promotion_target_date"] == "2026-07-27"
    assert rollover_state["promotion_rollover"] is True
    assert rollover_state["runtime_env_readback"] == "complete_exact_v2"


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
        now=TEST_NOW,
    )
    assert report["status"] == "global_runtime_full_pending_natural_endpoint"
    assert "entry_price" in report["pending_natural_endpoints"]
    assert "NXT_AFTERMARKET" in report["pending_natural_sessions"]
    assert report["rollback_required"] is False


def test_krx_post_apply_validation_is_pending_before_0920():
    report = promotion._krx_post_apply_validation(
        target_date="2026-07-27",
        validation={},
        now=TEST_NOW,
    )

    assert report["status"] == "pending_same_day_krx_validation"
    assert report["findings"] == []


def test_krx_post_apply_validation_fails_closed_after_0920():
    report = promotion._krx_post_apply_validation(
        target_date="2026-07-27",
        validation={},
        now=datetime(2026, 7, 27, 9, 20, tzinfo=KST),
    )

    assert report["status"] == "fail"
    assert "krx_post_apply_validation_schema_invalid" in report["findings"]


def test_krx_post_apply_validation_passes_same_day_exact_contract():
    report = promotion._krx_post_apply_validation(
        target_date="2026-07-27",
        validation=_same_day_krx_validation(),
        now=datetime(2026, 7, 27, 9, 20, tzinfo=KST),
    )

    assert report["status"] == "pass"
    assert report["findings"] == []


def test_krx_post_apply_validation_remains_required_after_target_date():
    report = promotion._krx_post_apply_validation(
        target_date="2026-07-27",
        validation={},
        now=datetime(2026, 7, 28, 8, 0, tzinfo=KST),
    )

    assert report["status"] == "fail"
    assert "krx_post_apply_validation_schema_invalid" in report["findings"]


def test_krx_post_apply_validation_fails_closed_on_invalid_target_date():
    report = promotion._krx_post_apply_validation(
        target_date="invalid",
        validation={},
        now=TEST_NOW,
    )

    assert report["status"] == "fail"
    assert report["findings"] == ["krx_post_apply_target_date_invalid"]


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
        now=TEST_NOW,
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
        now=TEST_NOW,
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
        now=TEST_NOW,
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
        now=TEST_NOW,
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
        golden_validation=_golden_validation(),
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
