from __future__ import annotations

import json
import hashlib
from types import SimpleNamespace

import pytest

from src.engine.scalping.watching_score_smoothing import (
    MAX_OBSERVATIONS,
    build_diagnostic_artifact,
    evaluate_watching_score,
    normalize_mode,
)
from src.engine import sniper_state_handlers as handlers


def _valid_result(**overrides):
    payload = {
        "ai_parse_ok": True,
        "ai_parse_fail": False,
        "ai_fallback_score_50": False,
        "ai_result_source": "live",
        "cache_hit": False,
    }
    payload.update(overrides)
    return payload


def _step(observations, now_ts, score, action="BUY", mode="report_only", previous=50.0, **result):
    return evaluate_watching_score(
        observations,
        now_ts=now_ts,
        raw_score=score,
        action=action,
        mode=mode,
        ai_result=_valid_result(**result),
        previous_applied_score=previous,
    )


def test_mode_normalization_fails_closed():
    assert normalize_mode("REPORT_ONLY") == "report_only"
    assert normalize_mode("applied") == "applied"
    assert normalize_mode("invalid") == "off"


def test_report_only_projects_but_keeps_raw_applied_score():
    first, observations = _step([], 100.0, 60.0)
    second, observations = _step(observations, 130.0, 90.0, previous=60.0)

    assert first.applied_score == 60.0
    assert second.projected_score < 90.0
    assert second.applied_score == 90.0
    assert second.smoothing_applied is False
    assert len(observations) == 2


def test_applied_mode_uses_projection_after_two_valid_observations():
    _, observations = _step([], 100.0, 60.0, mode="applied")
    second, _ = _step(observations, 130.0, 90.0, mode="applied", previous=60.0)

    assert second.projected_score == pytest.approx(second.applied_score)
    assert 60.0 < second.applied_score < 90.0
    assert second.smoothing_applied is True


def test_sharp_drop_and_drop_action_are_immediate():
    _, observations = _step([], 100.0, 90.0, mode="applied")
    sharp, observations = _step(observations, 130.0, 70.0, mode="applied", previous=90.0)
    drop, _ = _step(observations, 160.0, 80.0, action="DROP", mode="applied", previous=70.0)

    assert sharp.applied_score == 70.0
    assert drop.applied_score == 80.0


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"ai_result_source": "lock_contention", "ai_parse_ok": False}, "lock_contention"),
        ({"ai_fallback_score_50": True}, "fallback_score_50"),
        ({"ai_parse_fail": True}, "parse_invalid"),
        ({"cache_hit": True, "ai_result_source": "cache"}, "cache_hit_same_input"),
        ({"ai_result_source": "cache", "ai_parse_ok": None}, "cache_hit_same_input"),
        ({"ai_result_source": "engine_disabled", "ai_parse_ok": False}, "engine_disabled"),
    ],
)
def test_invalid_responses_do_not_enter_buffer(overrides, expected):
    decision, observations = _step([], 100.0, 50.0, **overrides)

    assert decision.excluded_reason == expected
    assert observations == []


def test_stale_context_does_not_enter_buffer():
    decision, observations = evaluate_watching_score(
        [],
        now_ts=100.0,
        raw_score=80.0,
        action="BUY",
        mode="applied",
        ai_result=_valid_result(),
        quote_stale=True,
    )
    assert decision.excluded_reason == "stale_context_or_quote"
    assert decision.applied_score == 50.0
    assert observations == []


def test_string_false_stale_flags_are_not_treated_as_stale():
    decision, observations = evaluate_watching_score(
        [],
        now_ts=100.0,
        raw_score=80.0,
        action="BUY",
        mode="report_only",
        ai_result=_valid_result(tick_context_stale="False"),
        quote_stale="False",
    )
    assert decision.excluded_reason == ""
    assert len(observations) == 1


def test_fallback_reason_has_priority_over_parse_invalid():
    decision, _ = evaluate_watching_score(
        [],
        now_ts=100.0,
        raw_score=50.0,
        action="WAIT",
        mode="report_only",
        ai_result=_valid_result(ai_parse_ok=False, ai_parse_fail=True, ai_fallback_score_50=True),
    )
    assert decision.excluded_reason == "fallback_score_50"


def test_window_and_capacity_are_bounded():
    observations = []
    for idx in range(10):
        _, observations = _step(observations, 100.0 + idx * 20.0, 60.0 + idx)
    assert len(observations) == MAX_OBSERVATIONS

    decision, observations = _step(observations, 500.0, 75.0)
    assert len(observations) == 1
    assert decision.valid_observation_count == 1


def test_action_consistency_uses_last_three_valid_observations():
    observations = []
    for now_ts, score, action in [(100.0, 70.0, "BUY"), (120.0, 71.0, "WAIT"), (140.0, 72.0, "BUY")]:
        decision, observations = _step(observations, now_ts, score, action=action)
    assert decision.action_consistency == pytest.approx(2 / 3)
    assert decision.confidence == "ready"


def test_applied_mode_never_promotes_subthreshold_raw_score_to_buy():
    observations = []
    for now_ts, score in [(100.0, 82.0), (120.0, 80.0)]:
        _, observations = _step(observations, now_ts, score, action="BUY", mode="applied", previous=score)
    decision, _ = _step(observations, 140.0, 70.0, action="BUY", mode="applied", previous=80.0)
    assert decision.applied_score <= 70.0


def test_applied_buy_requires_three_samples_and_two_buy_votes():
    first, observations = _step([], 100.0, 82.0, action="BUY", mode="applied")
    second, observations = _step(observations, 120.0, 84.0, action="BUY", mode="applied", previous=82.0)
    assert first.applied_score == 82.0
    assert second.applied_score <= 74.0

    third, _ = _step(observations, 140.0, 86.0, action="BUY", mode="applied", previous=second.applied_score)
    assert third.valid_observation_count == 3
    assert third.applied_score > 74.0


def test_diagnostic_artifact_is_explicitly_non_authoritative(tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    source = pipeline_dir / "pipeline_events_2026-06-12.jsonl"
    source.write_text(
        json.dumps(
            {
                "stage": "ai_confirmed",
                "stock_code": "005930",
                "emitted_at": "2026-06-12T09:10:00",
                "fields": {
                    "ai_score_policy_version": "watching_score_smoothing_v1",
                    "ai_score_raw": 80,
                    "ai_score_projected": 75,
                    "ai_score_excluded_reason": "-",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_diagnostic_artifact("2026-06-12", data_root=tmp_path, write=True)

    assert report["decision_authority"] == "report_only_no_automation_chain_authority"
    assert report["runtime_effect"] is False
    assert "threshold_cycle_input" in report["forbidden_uses"]
    assert report["transition_guard"]["eligible"] is False
    assert report["metrics"]["regular_observed_count"] == 1
    assert report["metrics"]["projection_observed_count"] == 0
    assert report["metrics"]["valid_response_count"] == 0
    assert (tmp_path / "report" / "ai_watching_score_smoothing_diagnostic" / "ai_watching_score_smoothing_diagnostic_2026-06-12.json").exists()


def test_diagnostic_detects_invalid_response_in_applied_mode(tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    (pipeline_dir / "pipeline_events_2026-06-12.jsonl").write_text(
        json.dumps(
            {
                "stage": "ai_confirmed",
                "stock_code": "005930",
                "fields": {
                    "ai_score_policy_version": "watching_score_smoothing_v1",
                    "ai_score_raw": 90,
                    "ai_score_projected": 90,
                    "ai_score_smoothing_mode": "applied",
                    "ai_score_excluded_reason": "stale_context_or_quote",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_diagnostic_artifact("2026-06-12", data_root=tmp_path)
    guard = report["transition_guard"]["criteria"]["stale_invalid_included_count"]
    assert guard == {"maximum": 0, "observed": 1, "status": "fail"}


def test_external_evidence_cannot_override_transition_criteria(tmp_path):
    criteria_keys = {
        "normal_session_count",
        "valid_response_count",
        "unique_symbol_count",
        "sequence_3plus_count",
        "lock_contention_rate_pct",
        "stale_invalid_included_count",
        "score_stddev_reduction_pct",
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "safety_and_provenance_guards",
    }
    artifacts = []
    for target_date in ("2026-06-15", "2026-06-16", "2026-06-17"):
        for role in ("post_sell", "source_quality", "postclose_verification"):
            path = tmp_path / f"{role}_{target_date}.json"
            path.write_text(json.dumps({"target_date": target_date, "role": role}), encoding="utf-8")
            artifacts.append(
                {
                    "path": str(path),
                    "target_date": target_date,
                    "role": role,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": ["2026-06-15", "2026-06-16", "2026-06-17"],
        "artifacts": artifacts,
        "criteria": {key: {"status": "pass", "observed": "verified"} for key in criteria_keys},
    }
    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)
    assert report["transition_guard"]["eligible"] is False
    assert report["transition_guard"]["status"] == "await_required_evidence"
    assert report["guard_evidence_source"] == "three_session_postclose_review"
    assert report["guard_evidence_accepted"] is True
    assert "buy_wait_flip_rate_reduction_pct" in report["transition_guard"]["manual_review_required_criteria"]

    assert any(item["status"] != "pass" for item in report["transition_guard"]["criteria"].values())


def _write_guard_artifacts(root, session_dates):
    artifacts = []
    for target_date in session_dates:
        for role in ("post_sell", "source_quality", "postclose_verification"):
            path = root / f"{role}_{target_date}.json"
            path.write_text(json.dumps({"target_date": target_date, "role": role}), encoding="utf-8")
            artifacts.append(
                {
                    "path": str(path),
                    "target_date": target_date,
                    "role": role,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return artifacts


def _write_projection_events(root, session_dates):
    pipeline_dir = root / "pipeline_events"
    pipeline_dir.mkdir(exist_ok=True)
    symbols = [f"{idx:06d}" for idx in range(50)]
    for day_index, target_date in enumerate(session_dates):
        rows = []
        for symbol in symbols:
            for seq in range(2):
                raw = 40 if seq == 0 else 80
                rows.append(
                    json.dumps(
                        {
                            "stage": "ai_watching_score_projection",
                            "stock_code": symbol,
                            "emitted_at": f"{target_date}T09:{day_index}{seq}:00",
                            "fields": {
                                "ai_score_policy_version": "watching_score_smoothing_v1",
                                "ai_score_raw": raw,
                                "ai_score_projected": 60,
                                "ai_score_excluded_reason": "-",
                            },
                        }
                    )
                )
        (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _manual_review_criteria(root, criteria, session_dates):
    thresholds = {
        "buy_wait_flip_rate_reduction_pct": 20.0,
        "sharp_drop_delay_p95_sec": 30.0,
        "projected_buy_source_quality_adjusted_ev_pct": 0.0,
        "projected_missed_upside_delta_pctp": 2.0,
        "parse_fallback_lock_contention_degradation": "no_degradation",
        "safety_and_provenance_guards": "no_breach",
    }
    observed_values = {
        "buy_wait_flip_rate_reduction_pct": 25.0,
        "sharp_drop_delay_p95_sec": 20.0,
        "projected_buy_source_quality_adjusted_ev_pct": 0.1,
        "projected_missed_upside_delta_pctp": 1.0,
        "parse_fallback_lock_contention_degradation": "no_degradation",
        "safety_and_provenance_guards": "no_breach",
    }
    payload = {}
    for key in criteria:
        path = root / f"manual_{key}.json"
        observed = observed_values[key]
        threshold = thresholds[key]
        path.write_text(
            json.dumps(
                {
                    "criterion": key,
                    "status": "pass",
                    "observed": observed,
                    "threshold": threshold,
                    "session_dates": session_dates,
                }
            ),
            encoding="utf-8",
        )
        payload[key] = {
            "status": "pass",
            "observed": observed,
            "threshold": threshold,
            "session_dates": session_dates,
            "artifact_path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return payload


def test_diagnostic_aggregates_verified_three_session_projection_metrics(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "criteria": {"normal_session_count": {"status": "pass", "observed": 3}},
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["guard_evidence_accepted"] is True
    assert report["metrics"]["normal_session_count"] == 3
    assert report["metrics"]["valid_response_count"] == 300
    assert report["metrics"]["unique_symbol_count"] == 50
    assert report["metrics"]["sequence_3plus_count"] == 50
    assert report["transition_guard"]["automatic_criteria_passed"] is True
    assert report["transition_guard"]["eligible"] is False
    assert report["transition_guard"]["applied_candidate_status"] == "manual_review_required"
    assert report["transition_guard"]["status"] == "manual_postclose_review_required"
    assert all(item["exists"] and item["sha256"] for item in report["input_artifact_checks"])


def test_diagnostic_manual_review_names_only_cannot_close_applied_candidate(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": sorted(manual_criteria),
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["automatic_criteria_passed"] is True
    assert report["transition_guard"]["manual_review_passed"] is False
    assert report["transition_guard"]["eligible"] is False
    assert report["transition_guard"]["applied_candidate_status"] == "manual_review_required"


def test_diagnostic_manual_review_can_close_applied_candidate_after_auto_metrics_pass(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": _manual_review_criteria(tmp_path, manual_criteria, session_dates),
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["automatic_criteria_passed"] is True
    assert report["transition_guard"]["manual_review_passed"] is True
    assert report["transition_guard"]["eligible"] is True
    assert report["transition_guard"]["applied_candidate_status"] == "eligible"
    assert report["transition_guard"]["status"] == "eligible_for_next_preopen_applied_review"


def test_diagnostic_manual_review_threshold_violation_blocks_eligible(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    criteria = _manual_review_criteria(tmp_path, manual_criteria, session_dates)
    criteria["sharp_drop_delay_p95_sec"]["observed"] = 999.0
    path = tmp_path / "manual_sharp_drop_delay_p95_sec_bad.json"
    path.write_text(
        json.dumps(
            {
                "criterion": "sharp_drop_delay_p95_sec",
                "status": "pass",
                "observed": 999.0,
                "threshold": 30.0,
                "session_dates": session_dates,
            }
        ),
        encoding="utf-8",
    )
    criteria["sharp_drop_delay_p95_sec"]["artifact_path"] = str(path)
    criteria["sharp_drop_delay_p95_sec"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": criteria,
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["automatic_criteria_passed"] is True
    assert report["transition_guard"]["manual_review_passed"] is False
    assert report["transition_guard"]["eligible"] is False


def test_diagnostic_manual_review_artifact_mismatch_blocks_eligible(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    criteria = _manual_review_criteria(tmp_path, manual_criteria, session_dates)
    path = tmp_path / "manual_wrong_criterion.json"
    path.write_text(
        json.dumps(
            {
                "criterion": "wrong_criterion",
                "status": "pass",
                "observed": 25.0,
                "threshold": 20.0,
                "session_dates": session_dates,
            }
        ),
        encoding="utf-8",
    )
    criteria["buy_wait_flip_rate_reduction_pct"]["artifact_path"] = str(path)
    criteria["buy_wait_flip_rate_reduction_pct"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": criteria,
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["manual_review_passed"] is False
    assert report["transition_guard"]["eligible"] is False


def test_diagnostic_manual_review_numeric_threshold_equivalence(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    criteria = _manual_review_criteria(tmp_path, manual_criteria, session_dates)
    criteria["sharp_drop_delay_p95_sec"]["threshold"] = 30
    path = tmp_path / "manual_sharp_drop_delay_p95_sec_int_threshold.json"
    path.write_text(
        json.dumps(
            {
                "criterion": "sharp_drop_delay_p95_sec",
                "status": "pass",
                "observed": 20.0,
                "threshold": 30,
                "session_dates": session_dates,
            }
        ),
        encoding="utf-8",
    )
    criteria["sharp_drop_delay_p95_sec"]["artifact_path"] = str(path)
    criteria["sharp_drop_delay_p95_sec"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": criteria,
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["manual_review_passed"] is True
    assert report["transition_guard"]["eligible"] is True


def test_diagnostic_manual_review_session_coverage_mismatch_blocks_eligible(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates)
    manual_criteria = {
        "buy_wait_flip_rate_reduction_pct",
        "sharp_drop_delay_p95_sec",
        "projected_buy_source_quality_adjusted_ev_pct",
        "projected_missed_upside_delta_pctp",
        "parse_fallback_lock_contention_degradation",
        "safety_and_provenance_guards",
    }
    criteria = _manual_review_criteria(tmp_path, manual_criteria, session_dates)
    criteria["safety_and_provenance_guards"]["session_dates"] = session_dates[:2]
    path = tmp_path / "manual_safety_bad_session_dates.json"
    path.write_text(
        json.dumps(
            {
                "criterion": "safety_and_provenance_guards",
                "status": "pass",
                "observed": "no_breach",
                "threshold": "no_breach",
                "session_dates": session_dates[:2],
            }
        ),
        encoding="utf-8",
    )
    criteria["safety_and_provenance_guards"]["artifact_path"] = str(path)
    criteria["safety_and_provenance_guards"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
        "manual_review": {
            "reviewed": True,
            "status": "pass",
            "source": "operator_postclose_review",
            "criteria": criteria,
        },
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["transition_guard"]["manual_review_passed"] is False
    assert report["transition_guard"]["eligible"] is False


def test_diagnostic_invalid_only_projection_session_does_not_count_as_normal_session(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    _write_projection_events(tmp_path, session_dates[:2])
    pipeline_dir = tmp_path / "pipeline_events"
    rows = []
    for symbol in [f"{idx:06d}" for idx in range(50)]:
        rows.append(
            json.dumps(
                {
                    "stage": "ai_watching_score_projection",
                    "stock_code": symbol,
                    "emitted_at": "2026-06-17T09:00:00",
                    "fields": {
                        "ai_score_policy_version": "watching_score_smoothing_v1",
                        "ai_score_raw": 50,
                        "ai_score_projected": 50,
                        "ai_score_excluded_reason": "parse_invalid",
                    },
                }
            )
        )
    (pipeline_dir / "pipeline_events_2026-06-17.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["metrics"]["normal_session_count"] == 2
    assert report["transition_guard"]["criteria"]["normal_session_count"]["status"] == "pending"
    assert "parse_invalid_rate_pct" not in report["transition_guard"]["criteria"]
    assert report["metrics"]["parse_invalid_rate_observed_pct"] > 0
    assert report["metrics"]["projection_exclusion_counts"]["parse_invalid"] == 50


def test_diagnostic_cache_hit_projection_rows_are_observed_not_transition_criteria(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    for target_date in session_dates:
        rows = []
        for symbol in [f"{idx:06d}" for idx in range(50)]:
            rows.append(
                json.dumps(
                    {
                        "stage": "ai_watching_score_projection",
                        "stock_code": symbol,
                        "emitted_at": f"{target_date}T09:00:00",
                        "fields": {
                            "ai_score_policy_version": "watching_score_smoothing_v1",
                            "ai_score_raw": 50,
                            "ai_score_projected": 50,
                            "ai_score_excluded_reason": "cache_hit_same_input",
                        },
                    }
                )
            )
        (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["metrics"]["cache_hit_same_input_rate_observed_pct"] > 0
    assert report["metrics"]["projection_exclusion_counts"]["cache_hit_same_input"] == 150
    assert "cache_hit_same_input_rate_observed_pct" not in report["transition_guard"]["criteria"]


def test_diagnostic_invalid_projection_rows_do_not_count_for_symbol_or_sequence(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    for target_date in session_dates:
        rows = []
        for symbol in [f"{idx:06d}" for idx in range(50)]:
            for seq in range(3):
                rows.append(
                    json.dumps(
                        {
                            "stage": "ai_watching_score_projection",
                            "stock_code": symbol,
                            "emitted_at": f"{target_date}T09:0{seq}:00",
                            "fields": {
                                "ai_score_policy_version": "watching_score_smoothing_v1",
                                "ai_score_raw": 50,
                                "ai_score_projected": 50,
                                "ai_score_excluded_reason": "parse_invalid",
                            },
                        }
                    )
                )
        (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["metrics"]["projection_observed_count"] == 450
    assert report["metrics"]["valid_response_count"] == 0
    assert report["metrics"]["unique_symbol_count"] == 0
    assert report["metrics"]["sequence_3plus_count"] == 0
    assert report["transition_guard"]["criteria"]["unique_symbol_count"]["status"] == "pending"
    assert report["transition_guard"]["criteria"]["sequence_3plus_count"]["status"] == "pending"


def test_diagnostic_regular_only_sessions_do_not_count_as_normal_projection_sessions(tmp_path):
    session_dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    for target_date in session_dates:
        (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text(
            json.dumps(
                {
                    "stage": "ai_confirmed",
                    "stock_code": "005930",
                    "fields": {
                        "ai_score_policy_version": "watching_score_smoothing_v1",
                        "ai_score_raw": 80,
                        "ai_score_projected": 80,
                        "ai_score_excluded_reason": "-",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
    evidence = {
        "source": "three_session_postclose_review",
        "reviewed": True,
        "normal_session_dates": session_dates,
        "artifacts": _write_guard_artifacts(tmp_path, session_dates),
    }

    report = build_diagnostic_artifact("2026-06-17", data_root=tmp_path, guard_evidence=evidence)

    assert report["metrics"]["regular_observed_count"] == 3
    assert report["metrics"]["projection_observed_count"] == 0
    assert report["metrics"]["normal_session_count"] == 0
    assert report["transition_guard"]["criteria"]["normal_session_count"]["status"] == "pending"


def test_unreviewed_guard_evidence_cannot_make_transition_eligible(tmp_path):
    report = build_diagnostic_artifact(
        "2026-06-17",
        data_root=tmp_path,
        guard_evidence={
            "source": "unreviewed",
            "normal_session_dates": ["2026-06-15", "2026-06-16", "2026-06-17"],
            "artifacts": [],
            "criteria": {"normal_session_count": {"status": "pass", "observed": 3}},
        },
    )
    assert report["guard_evidence_accepted"] is False
    assert report["transition_guard"]["eligible"] is False


def test_ai_confirmed_optional_provenance_keeps_existing_score_contract():
    fields = handlers._build_ai_ops_log_fields(
        {
            **_valid_result(),
            "ai_score_raw": 82.0,
            "ai_score_projected": 76.5,
            "ai_score_smoothing_mode": "report_only",
            "ai_score_smoothing_applied": False,
            "ai_score_valid_observation_count": 3,
            "ai_score_dispersion": 8.2,
            "ai_action_consistency": 2 / 3,
            "ai_early_refresh_trigger": "micro_vwap_side_changed",
            "ai_score_excluded_reason": "-",
            "ai_score_policy_version": "watching_score_smoothing_v1",
        },
        ai_score_raw=82.0,
        ai_score_after_bonus=82.0,
    )

    assert fields["ai_score_raw"] == "82.0"
    assert fields["ai_score_after_bonus"] == "82.0"
    assert fields["ai_score_projected"] == 76.5
    assert fields["ai_score_smoothing_mode"] == "report_only"
    assert fields["ai_score_smoothing_applied"] is False


def test_report_only_mode_enables_bounded_state_change_refresh(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=False,
            AI_WATCHING_SCORE_SMOOTHING_MODE="report_only",
            AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
        ),
    )
    stock = {"last_watching_ai_state_signature": handlers._build_watching_refresh_signature({"buy_ratio": 50.0})}
    result = handlers._resolve_watching_state_change_refresh(
        stock,
        {"buy_ratio": 70.0},
        now_ts=125.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert result["allowed"] is True
    assert "buy_pressure_delta" in result["reason"]

    too_early = handlers._resolve_watching_state_change_refresh(
        stock,
        {"buy_ratio": 70.0},
        now_ts=115.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert too_early == {"allowed": False, "reason": "early_refresh_min_interval", "signature": {}}


def test_report_only_ignores_legacy_feature_signature_until_next_normal_ai_call(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=False,
            AI_WATCHING_SCORE_SMOOTHING_MODE="report_only",
            AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
        ),
    )
    stock = {
        "last_watching_ai_state_signature": {
            "micro_vwap_side": "positive",
            "ma5_side": "positive",
            "buy_pressure_10t": 50.0,
            "tick_acceleration_regime": "fast",
            "large_sell_print_detected": True,
            "top3_depth_regime": "balanced",
            "quote_freshness": "unknown",
        }
    }

    result = handlers._resolve_watching_state_change_refresh(
        stock,
        {"buy_ratio": 70.0},
        now_ts=125.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )

    assert result["allowed"] is False
    assert result["reason"] == "legacy_signature_source_mismatch"
    assert result["signature"]["signature_source"] == "runtime_context_v2"


def test_watching_refresh_signature_uses_available_feature_axes(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=False,
            AI_WATCHING_SCORE_SMOOTHING_MODE="report_only",
            AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
        ),
    )
    ws_data = {"buy_ratio": 50.0, "orderbook": {"asks": [{"total": 100}], "bids": [{"total": 100}]}}
    previous_signature = handlers._build_watching_refresh_signature(
        ws_data,
        {
            "micro_vwap_bp": 12.0,
            "curr_vs_ma5_bp": 8.0,
            "tick_accel": 2.0,
            "large_sell_print": True,
        },
    )
    current_ws_data = {
        **ws_data,
        "micro_vwap_bp": -6.0,
        "curr_vs_ma5_bp": -4.0,
        "tick_accel": 0.6,
        "large_sell_print": True,
    }
    stock = {"last_watching_ai_state_signature": previous_signature}

    result = handlers._resolve_watching_state_change_refresh(
        stock,
        current_ws_data,
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )

    assert previous_signature["signature_source"] == "runtime_context_v2"
    assert "micro_vwap_side" in previous_signature["available_axes"]
    assert result["allowed"] is True
    assert "micro_vwap_side_changed" in result["reason"]
    assert "ma5_side_changed" in result["reason"]
    assert "tick_acceleration_regime_changed" in result["reason"]


def test_watching_refresh_does_not_compare_unavailable_feature_axes(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=False,
            AI_WATCHING_SCORE_SMOOTHING_MODE="report_only",
            AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
        ),
    )
    previous_signature = handlers._build_watching_refresh_signature(
        {"buy_ratio": 50.0},
        {"micro_vwap_bp": 12.0, "tick_accel": 2.0, "large_sell_print": True},
    )

    result = handlers._resolve_watching_state_change_refresh(
        {"last_watching_ai_state_signature": previous_signature},
        {"buy_ratio": 50.0},
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )

    assert result["allowed"] is False
    assert result["reason"] == "state_unchanged"


def test_watching_refresh_signature_treats_string_false_large_sell_as_false():
    signature = handlers._build_watching_refresh_signature(
        {"buy_ratio": 50.0, "large_sell_print": "False"}
    )

    assert "large_sell_print_detected" in signature["available_axes"]
    assert signature["large_sell_print_detected"] is False


def test_off_mode_preserves_legacy_state_refresh_without_new_min_interval(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_WATCHING_STATE_CHANGE_REFRESH_ENABLED=True,
            AI_WATCHING_SCORE_SMOOTHING_MODE="off",
            AI_WATCHING_STATE_CHANGE_BUY_PRESSURE_DELTA=10.0,
        ),
    )
    stock = {
        "last_watching_ai_state_signature": {
            "micro_vwap_side": "positive",
            "ma5_side": "positive",
            "buy_pressure_10t": 50.0,
            "tick_acceleration_regime": "steady",
            "large_sell_print_detected": False,
            "top3_depth_regime": "balanced",
            "quote_freshness": "unknown",
        }
    }
    result = handlers._resolve_watching_state_change_refresh(
        stock,
        {"buy_ratio": 70.0},
        now_ts=115.0,
        last_ai_time=100.0,
        cooldown_sec=90,
    )
    assert result["allowed"] is True


def test_projection_refresh_does_not_mutate_runtime_score_or_last_call(monkeypatch):
    stock = {
        "id": 1,
        "name": "TEST",
        "rt_ai_prob": 0.81,
        "last_watching_ai_action": "BUY",
    }
    events = []
    submitted = {}

    class ProjectionEngine:
        def submit_watching_score_projection(self, **kwargs):
            submitted.update(kwargs)
            return object()

    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(handlers, "DUAL_PERSONA_ENGINE", ProjectionEngine())
    monkeypatch.setattr(handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{}])
    monkeypatch.setattr(handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [])
    monkeypatch.setattr(handlers, "_extract_buy_recovery_probe_features", lambda *args, **kwargs: {"buy_pressure": 60})
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: events.append((stage, fields)))

    executed = handlers._run_watching_score_projection_refresh(
        stock,
        "005930",
        {"orderbook": {"asks": [], "bids": []}, "quote_stale": False},
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
        refresh_reason="buy_pressure_delta",
        current_ai_score=81.0,
    )

    assert executed is True
    assert stock["watching_score_projection_inflight"] is True
    assert events == []
    submitted["callback"]({
        **_valid_result(),
        "action": "WAIT",
        "score": 55,
        "reason": "projection",
    })
    assert stock["rt_ai_prob"] == 0.81
    assert stock["last_watching_ai_action"] == "BUY"
    assert stock.get("last_watching_ai_score") is None
    assert stock["watching_score_projection_inflight"] is False
    assert events[0][0] == "ai_watching_score_projection"
    assert events[0][1]["runtime_score_preserved"] == "81.0"
    assert events[0][1]["runtime_effect"] is False


def test_projection_refresh_without_projection_engine_does_not_fetch_context(monkeypatch):
    calls = {"ticks": 0, "candles": 0}

    def _ticks(*args, **kwargs):
        calls["ticks"] += 1
        return [{}]

    def _candles(*args, **kwargs):
        calls["candles"] += 1
        return []

    monkeypatch.setattr(handlers, "DUAL_PERSONA_ENGINE", None)
    monkeypatch.setattr(handlers.kiwoom_utils, "get_tick_history_ka10003", _ticks)
    monkeypatch.setattr(handlers.kiwoom_utils, "get_minute_candles_ka10080", _candles)

    executed = handlers._run_watching_score_projection_refresh(
        {"id": 1, "name": "TEST"},
        "005930",
        {"orderbook": {"asks": [], "bids": []}},
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
        refresh_reason="buy_pressure_delta",
        current_ai_score=81.0,
    )

    assert executed is False
    assert calls == {"ticks": 0, "candles": 0}


def test_projection_refresh_inflight_does_not_fetch_context(monkeypatch):
    calls = {"ticks": 0}

    class ProjectionEngine:
        def submit_watching_score_projection(self, **kwargs):
            raise AssertionError("inflight projection must not submit another request")

    monkeypatch.setattr(handlers, "DUAL_PERSONA_ENGINE", ProjectionEngine())
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: calls.__setitem__("ticks", calls["ticks"] + 1) or [{}],
    )

    executed = handlers._run_watching_score_projection_refresh(
        {"id": 1, "name": "TEST", "watching_score_projection_inflight": True},
        "005930",
        {"orderbook": {"asks": [], "bids": []}},
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
        refresh_reason="buy_pressure_delta",
        current_ai_score=81.0,
    )

    assert executed is False
    assert calls["ticks"] == 0


def test_projection_refresh_none_submit_clears_inflight(monkeypatch):
    stock = {"id": 1, "name": "TEST"}

    class ProjectionEngine:
        def submit_watching_score_projection(self, **kwargs):
            return None

    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(handlers, "DUAL_PERSONA_ENGINE", ProjectionEngine())
    monkeypatch.setattr(handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{}])
    monkeypatch.setattr(handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [])

    executed = handlers._run_watching_score_projection_refresh(
        stock,
        "005930",
        {"orderbook": {"asks": [], "bids": []}},
        now_ts=130.0,
        last_ai_time=100.0,
        cooldown_sec=90,
        refresh_reason="buy_pressure_delta",
        current_ai_score=81.0,
    )

    assert executed is False
    assert stock["watching_score_projection_inflight"] is False
