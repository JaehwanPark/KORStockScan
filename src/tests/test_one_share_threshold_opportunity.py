import gzip
import json

from src.engine.monitoring import one_share_threshold_opportunity as mod


def _event(
    record_id,
    stage,
    fields=None,
    *,
    code="000001",
    name="sample",
    emitted_at="2026-07-01T09:00:00+09:00",
):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "record_id": record_id,
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields or {},
        "emitted_at": emitted_at,
    }


def test_residual_not_submitted_source_prefers_explicit_terminal_outcome():
    assert (
        mod._residual_not_submitted_source(
            {
                "entry_split_probe_terminal_outcome": "residual_not_submitted",
                "entry_split_residual_blocked_observed": True,
                "entry_split_probe_phase": "aborted",
            }
        )
        == "explicit_terminal_outcome"
    )
    assert (
        mod._residual_not_submitted_source(
            {
                "entry_split_residual_blocked_observed": True,
                "entry_split_probe_phase": "residual_partial_submitted",
            }
        )
        == ""
    )


def test_build_report_aggregates_threshold_opportunity_and_orders(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    rows = []
    for idx, profit in enumerate([0.8, 0.5, -0.1], start=1):
        rows.extend(
            [
                _event(
                    idx,
                    "blocked_ai_score",
                    {
                        "reason": "blocked_ai_score_below_buy_score_threshold",
                        "ai_score": "72",
                    },
                    code=f"00000{idx}",
                ),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {
                        "forced_entry_reason": "rising_missed_one_share_entry",
                        "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    },
                    code=f"00000{idx}",
                ),
            ]
        )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": f"00000{idx}",
                    "stock_name": "sample",
                    "profit_rate": profit,
                    "peak_profit": profit + 0.2,
                    "exit_rule": (
                        "scalp_take_profit" if profit > 0 else "scalp_soft_stop"
                    ),
                }
            )
            for idx, profit in enumerate([0.8, 0.5, -0.1], start=1)
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    assert report["summary"]["forced_record_count"] == 3
    assert report["summary"]["post_sell_joined_count"] == 3
    assert report["summary"]["code_improvement_order_count"] == 1
    assert report["summary"]["source_only_existing_family_evidence_count"] == 1
    assert report["summary"]["automatic_implementation_candidate_count"] == 0
    opportunity = report["threshold_opportunities"][0]
    assert opportunity["threshold_group"] == "ai_score_near_buy"
    assert opportunity["valid_profit_sample"] == 3
    assert opportunity["equal_weight_avg_profit_pct"] == 0.4
    order = report["code_improvement_orders"][0]
    assert order["source_report_type"] == "one_share_threshold_opportunity"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert order["route"] == "existing_family"
    assert order["implementation_status"] == "source_evidence_candidate"
    assert (
        order["implementation_provenance"]["source_audit_implementation_status"]
        == "implemented"
    )
    assert order["implementation_provenance"]["target_hook_implementation_status"] == (
        "requires_independent_verification"
    )
    assert order["implementation_provenance"]["workorder_intake_role"] == (
        "attach_existing_family_evidence"
    )
    assert (
        order["implementation_provenance"]["requires_separate_runtime_apply_candidate"]
        is True
    )
    assert order["implementation_provenance"]["broker_order_forbidden"] is True
    assert "broker_guard_bypass" in order["forbidden_uses"]
    assert report["ai_review"]["status"] == "unavailable"
    assert report["probe_split_attribution"]["intent_record_count"] == 3
    assert report["probe_split_attribution"]["status"] == "observed"
    assert report["probe_split_attribution"]["target_date_probe_to_residual"] == {
        "status": "no_natural_sample",
        "probe_first_submitted_count": 0,
        "probe_first_submit_with_provenance_count": 0,
        "probe_first_submit_provenance_gap_count": 0,
        "resolution_count": 0,
        "resolution_coverage_pct": None,
        "residual_submitted_record_count": 0,
        "residual_blocked_record_count": 0,
        "residual_not_submitted_record_count": 0,
        "residual_not_submitted_source_counts": {},
        "residual_terminal_abort_detail_reason_counts": {},
        "unresolved_record_count": 0,
    }


def test_forced_reason_on_ineligible_skip_does_not_create_probe_intent(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "rising_missed_watch_not_rising_skipped",
                {
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "rising_missed_one_share_eligible": False,
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[],
        generated_at="fixed",
        ai_provider="none",
    )

    assert report["summary"]["forced_record_count"] == 0
    assert report["probe_split_attribution"]["status"] == "no_natural_sample"
    assert report["source_coverage_manifest"]["missing_post_sell_dates"] == []


def test_downstream_forced_flag_does_not_replace_primary_forced_entry_identity(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                    emitted_at="2026-07-01T09:00:00+09:00",
                ),
                _event(
                    1,
                    "order_bundle_submitted",
                    {
                        "rising_missed_one_share_entry_forced": True,
                        "actual_order_submitted": True,
                    },
                    emitted_at="2026-07-01T09:01:00+09:00",
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "stock_code": "000001", "profit_rate": 0.1})
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )
    row = report["joined_examples"][0]

    assert row["entry_time"] == "2026-07-01T09:00:00+09:00"
    assert row["source_stage"] == "rising_missed_one_share_entry"
    assert row["actual_order_submitted_observed"] is True
    assert row["forced_event_count"] == 2


def test_probe_split_attribution_flags_submitted_row_without_variant(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {
                        "rising_missed_one_share_entry_forced": True,
                        "entry_split_order_probe_first_applied": True,
                    },
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    attribution = report["probe_split_attribution"]
    assert attribution["actual_submit_observed_count"] == 1
    assert attribution["probe_first_submitted_count"] == 1
    assert attribution["entry_split_variant_observed_count"] == 0
    assert attribution["submitted_split_provenance_gap_count"] == 1
    assert attribution["status"] == "instrumentation_gap"
    assert attribution["probe_to_residual_status"] == "instrumentation_gap"
    coverage = report["source_coverage_manifest"]
    assert coverage["expected_post_sell_dates"] == []
    assert coverage["entry_date_partition_match_required"] is False
    assert coverage["pending_or_right_censored_submit_count"] == 1


def test_non_split_submit_is_not_a_probe_provenance_gap(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    attribution = report["probe_split_attribution"]
    assert attribution["status"] == "observed"
    assert attribution["probe_first_submitted_count"] == 0
    assert attribution["legacy_or_non_split_submit_count"] == 1
    assert attribution["submitted_split_provenance_gap_count"] == 0
    assert attribution["probe_to_residual_status"] == "no_natural_sample"


def test_probe_to_residual_attribution_joins_submit_and_terminal_outcomes(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {
                        "rising_missed_one_share_entry_forced": True,
                        "entry_split_order_probe_first_applied": True,
                        "entry_split_probe_bundle_id": "bundle-submit",
                        "entry_split_order_variant_id": "variant-submit",
                    },
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
                _event(
                    1,
                    "residual_submitted",
                    {
                        "actual_order_submitted": True,
                        "entry_split_probe_bundle_id": "bundle-submit",
                    },
                ),
                _event(
                    1,
                    "residual_blocked",
                    {"entry_split_probe_bundle_id": "bundle-submit"},
                ),
                _event(
                    2,
                    "rising_missed_one_share_entry",
                    {
                        "rising_missed_one_share_entry_forced": True,
                        "entry_split_order_probe_first_applied": True,
                        "entry_split_probe_bundle_id": "bundle-abort",
                        "entry_split_order_variant_id": "variant-abort",
                    },
                ),
                _event(2, "order_bundle_submitted", {"actual_order_submitted": True}),
                _event(
                    2,
                    "residual_blocked",
                    {
                        "probe_bundle_id": "bundle-abort",
                        "entry_split_probe_phase": "aborted",
                        "entry_split_probe_abort_reason": (
                            "residual_revalidation_timeout"
                        ),
                        "entry_split_probe_terminal_abort_reason": (
                            "residual_revalidation_timeout"
                        ),
                        "entry_split_probe_terminal_abort_detail_reason": (
                            "timeout_wait_confirmation_not_reached"
                        ),
                        "entry_split_probe_terminal_failure_signature": (
                            "residual_revalidation_timeout|WEAK|wait|price_tick|0/2"
                        ),
                    },
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    attribution = report["probe_split_attribution"]
    assert attribution["probe_to_residual_status"] == "observed"
    assert attribution["probe_to_residual_resolution_count"] == 2
    assert attribution["probe_to_residual_resolution_coverage_pct"] == 100.0
    assert attribution["residual_submitted_record_count"] == 1
    assert attribution["residual_blocked_record_count"] == 2
    assert attribution["residual_not_submitted_record_count"] == 1
    assert attribution["probe_to_residual_unresolved_record_count"] == 0
    assert attribution["target_date_probe_to_residual"] == {
        "status": "observed",
        "probe_first_submitted_count": 2,
        "probe_first_submit_with_provenance_count": 2,
        "probe_first_submit_provenance_gap_count": 0,
        "resolution_count": 2,
        "resolution_coverage_pct": 100.0,
        "residual_submitted_record_count": 1,
        "residual_blocked_record_count": 2,
        "residual_not_submitted_record_count": 1,
        "residual_not_submitted_source_counts": {"legacy_aborted_phase_fallback": 1},
        "residual_terminal_abort_detail_reason_counts": {
            "timeout_wait_confirmation_not_reached": 1
        },
        "unresolved_record_count": 0,
    }
    assert attribution["residual_not_submitted_source_counts"] == {
        "legacy_aborted_phase_fallback": 1
    }
    assert attribution["residual_terminal_abort_reason_counts"] == {
        "residual_revalidation_timeout": 1
    }
    assert attribution["residual_terminal_abort_detail_reason_counts"] == {
        "timeout_wait_confirmation_not_reached": 1
    }
    assert attribution["residual_terminal_failure_signature_coverage_count"] == 1
    contract = attribution["probe_to_residual_contract"]
    assert contract["runtime_effect"] is False
    assert contract["allowed_runtime_apply"] is False
    assert contract["primary_decision_metric"] == (
        "probe_to_residual_resolution_coverage_pct"
    )


def test_probe_to_residual_attribution_flags_missing_terminal_event(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {
                        "rising_missed_one_share_entry_forced": True,
                        "entry_split_order_probe_first_applied": True,
                        "entry_split_probe_bundle_id": "bundle-open",
                        "entry_split_order_variant_id": "variant-open",
                    },
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    attribution = report["probe_split_attribution"]
    assert attribution["status"] == "observed"
    assert attribution["probe_to_residual_status"] == "instrumentation_gap"
    assert attribution["probe_to_residual_resolution_count"] == 0
    assert attribution["probe_to_residual_resolution_coverage_pct"] == 0.0
    assert attribution["probe_to_residual_unresolved_record_count"] == 1
    assert attribution["target_date_probe_to_residual"]["status"] == (
        "instrumentation_gap"
    )
    assert attribution["target_date_probe_to_residual"]["unresolved_record_count"] == 1


def test_valid_profit_sample_floor_blocks_incomplete_pnl_order(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    rows = []
    for idx in range(1, 4):
        rows.extend(
            [
                _event(
                    idx,
                    "blocked_ai_score",
                    {
                        "reason": "blocked_ai_score_below_buy_score_threshold",
                        "ai_score": "72",
                    },
                    code=f"00000{idx}",
                ),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {"forced_entry_reason": "rising_missed_one_share_entry"},
                    code=f"00000{idx}",
                ),
            ]
        )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": f"00000{idx}",
                    "stock_name": "sample",
                    "profit_rate": 0.7 if idx == 1 else None,
                    "exit_rule": "scalp_take_profit",
                }
            )
            for idx in range(1, 4)
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    evaluation = report["primary_blocker_evaluations"][0]
    assert evaluation["sample"] == 3
    assert evaluation["valid_profit_sample"] == 1
    assert evaluation["equal_weight_avg_profit_pct"] == 0.7
    assert report["threshold_opportunities"] == []
    assert report["summary"]["code_improvement_order_count"] == 0
    assert report["code_improvement_orders"] == []


def test_ai_review_annotations_are_source_only(tmp_path, monkeypatch):
    def fake_ai_review(report, *, provider):
        return json.dumps(
            {
                "schema_version": 1,
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [
                    {
                        "candidate_id": "one_share_threshold_ai_score_near_buy",
                        "recommended_disposition": "attach_existing_entry_hook",
                        "confidence": "medium",
                        "reason": "bounded entry hook already exists",
                        "required_followup": ["verify post-apply attribution"],
                    }
                ],
                "audit": {"status": "pass", "issues": [], "reason": "source-only"},
                "codex_directives": [],
            }
        ), {"provider": provider, "status": "success"}

    monkeypatch.setattr(mod, "_call_ai_review", fake_ai_review)
    report = {
        "target_date": "2026-07-01",
        "window": {},
        "summary": {},
        "metric_contract": {},
        "source_coverage_manifest": {"status": "pass"},
        "threshold_opportunities": [],
        "code_improvement_orders": [
            {
                "candidate_id": "one_share_threshold_ai_score_near_buy",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ],
    }

    reviewed = mod._apply_ai_review(report, provider="openai")

    order = reviewed["code_improvement_orders"][0]
    assert reviewed["ai_review"]["status"] == "parsed"
    assert reviewed["ai_review"]["runtime_effect"] is False
    assert order["ai_recommended_disposition"] == "attach_existing_entry_hook"
    assert order["runtime_effect"] is False


def test_ai_review_reuses_parsed_result_when_actionable_digest_is_unchanged(
    tmp_path, monkeypatch
):
    calls = []

    def fake_ai_review(report, *, provider):
        calls.append(report["target_date"])
        return json.dumps(
            {
                "schema_version": 1,
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [
                    {
                        "candidate_id": "one_share_threshold_ai_score_near_buy",
                        "recommended_disposition": "attach_existing_entry_hook",
                        "confidence": "medium",
                        "reason": "bounded entry hook already exists",
                        "required_followup": ["verify post-apply attribution"],
                    }
                ],
                "audit": {"status": "pass", "issues": [], "reason": "source-only"},
                "codex_directives": [],
            }
        ), {"provider": provider, "status": "success"}

    monkeypatch.setattr(mod, "_call_ai_review", fake_ai_review)
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    rows = []
    for idx in range(1, 4):
        rows.extend(
            [
                _event(idx, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
            ]
        )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": "000001",
                    "profit_rate": 0.5,
                }
            )
            for idx in range(1, 4)
        ),
        encoding="utf-8",
    )

    first = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="openai",
    )
    second = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="openai",
        previous_report=first,
    )

    assert calls == ["2026-07-01"]
    assert second["candidate_change"]["status"] == "unchanged"
    assert second["ai_review"]["status"] == "parsed"
    assert second["ai_review"]["provider_status"]["status"] == "reused"
    assert second["ai_review"]["provider_status"]["new_provider_call"] is False
    assert second["code_improvement_orders"][0]["ai_recommended_disposition"] == (
        "attach_existing_entry_hook"
    )


def test_ai_review_does_not_reuse_incomplete_prior_candidate_census(
    tmp_path, monkeypatch
):
    calls = []

    def fake_ai_review(report, *, provider):
        calls.append(report["target_date"])
        return json.dumps(
            {
                "schema_version": 1,
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [
                    {
                        "candidate_id": "one_share_threshold_ai_score_near_buy",
                        "recommended_disposition": "keep_collecting",
                        "confidence": "medium",
                        "reason": "source-only sample",
                        "required_followup": [],
                    }
                ],
                "audit": {"status": "pass", "issues": [], "reason": "ok"},
                "codex_directives": [],
            }
        ), {"provider": provider, "status": "success"}

    monkeypatch.setattr(mod, "_call_ai_review", fake_ai_review)
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for idx in range(1, 4)
            for row in (
                _event(idx, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
            )
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": "000001",
                    "profit_rate": 0.5,
                }
            )
            for idx in range(1, 4)
        ),
        encoding="utf-8",
    )
    first = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        ai_provider="openai",
    )
    del first["code_improvement_orders"][0]["ai_review_reason"]

    second = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        ai_provider="openai",
        previous_report=first,
    )

    assert calls == ["2026-07-01", "2026-07-02"]
    assert second["ai_review"]["provider_status"]["status"] == "success"


def test_ai_review_contract_change_forces_fresh_review(tmp_path, monkeypatch):
    calls = []

    def fake_ai_review(report, *, provider):
        calls.append(report["target_date"])
        return json.dumps(
            {
                "schema_version": 1,
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [
                    {
                        "candidate_id": "one_share_threshold_ai_score_near_buy",
                        "recommended_disposition": "keep_collecting",
                        "confidence": "medium",
                        "reason": "source-only sample",
                        "required_followup": [],
                    }
                ],
                "audit": {"status": "pass", "issues": [], "reason": "ok"},
                "codex_directives": [],
            }
        ), {"provider": provider, "status": "success"}

    monkeypatch.setattr(mod, "_call_ai_review", fake_ai_review)
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for idx in range(1, 4)
            for row in (
                _event(idx, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
            )
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": "000001",
                    "profit_rate": 0.5,
                }
            )
            for idx in range(1, 4)
        ),
        encoding="utf-8",
    )
    first = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        ai_provider="openai",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_REASONING_EFFORT", "high"
    )

    second = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        ai_provider="openai",
        previous_report=first,
    )

    assert calls == ["2026-07-01", "2026-07-02"]
    assert second["candidate_change"]["status"] == "unchanged"
    assert second["candidate_change"]["ai_review_contract_change_status"] == ("changed")


def test_actionable_digest_changes_when_workorder_intake_role_changes():
    report = {
        "code_improvement_orders": [
            {
                "order_id": "order-1",
                "candidate_id": "candidate-1",
                "route": "existing_family",
                "improvement_type": "source_only_existing_family_evidence",
                "implementation_status": "source_evidence_candidate",
                "target_subsystem": "entry",
                "implementation_provenance": {
                    "threshold_group": "ai_score_near_buy",
                    "workorder_intake_role": "attach_existing_family_evidence",
                    "sample": 3,
                    "valid_profit_sample": 3,
                    "equal_weight_avg_profit_pct": 0.1,
                    "primary_blocker_attribution_status": "pass",
                },
            }
        ]
    }
    before = mod._actionable_semantic_digest(report)
    report["code_improvement_orders"][0]["route"] = "instrumentation_order"

    assert mod._actionable_semantic_digest(report) != before


def test_actionable_digest_covers_order_contract_but_ignores_review_annotations():
    report = {
        "code_improvement_orders": [
            {
                "order_id": "order-1",
                "candidate_id": "candidate-1",
                "forbidden_uses": ["runtime_mutation"],
                "source_paths": ["day-1.jsonl"],
                "ai_review_status": "parsed",
            }
        ]
    }
    before = mod._actionable_semantic_digest(report)
    report["code_improvement_orders"][0]["ai_review_status"] = "unreviewed"
    report["code_improvement_orders"][0]["source_paths"].append("day-2.jsonl")
    assert mod._actionable_semantic_digest(report) == before

    report["code_improvement_orders"][0]["forbidden_uses"].append("broker_guard_bypass")
    assert mod._actionable_semantic_digest(report) != before


def test_ai_review_rejects_partial_current_candidate_census(monkeypatch):
    report = {
        "source_coverage_manifest": {"status": "pass"},
        "candidate_change": {"status": "changed"},
        "summary": {},
        "code_improvement_orders": [
            {"candidate_id": "candidate-a"},
            {"candidate_id": "candidate-b"},
        ],
    }

    monkeypatch.setattr(
        mod,
        "_call_ai_review",
        lambda report, *, provider: (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "one_share_threshold_opportunity_ai_review",
                    "candidate_reviews": [
                        {
                            "candidate_id": "candidate-a",
                            "recommended_disposition": "keep_collecting",
                            "confidence": "low",
                            "reason": "partial",
                            "required_followup": [],
                        }
                    ],
                    "audit": {"status": "pass", "issues": [], "reason": "partial"},
                    "codex_directives": [],
                }
            ),
            {"provider": provider, "status": "success"},
        ),
    )

    reviewed = mod._apply_ai_review(report, provider="openai")

    assert reviewed["ai_review"]["status"] == "parse_rejected"
    assert "ai_review_candidate_census_mismatch" in reviewed["ai_review"]["warnings"][0]
    assert all(
        order["ai_review_status"] == "parse_rejected"
        for order in reviewed["code_improvement_orders"]
    )


def test_ai_review_malformed_schema_version_is_parse_rejected():
    status, payload, warnings = mod._parse_ai_review(
        json.dumps(
            {
                "schema_version": "bad",
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [],
                "audit": {"status": "pass", "issues": [], "reason": "source-only"},
                "codex_directives": [],
            }
        )
    )

    assert status == "parse_rejected"
    assert payload["schema_version"] == "bad"
    assert "ai_review_schema_version_invalid" in warnings


def test_hard_safety_group_does_not_create_code_order():
    opportunities = [
        {
            "candidate_id": "one_share_threshold_cooldown_or_hard_safety",
            "threshold_group": "cooldown_or_hard_safety",
            "mapped_family": "hard_safety_observation_only",
            "target_subsystem": "entry_hard_safety_preserve",
            "sample": 3,
            "valid_profit_sample": 3,
            "profitable_count": 3,
            "loss_or_flat_count": 0,
            "equal_weight_avg_profit_pct": 0.6,
            "candidate_status": "eligible_for_existing_family_evidence",
            "primary_blocker_attribution_status": "pass",
        }
    ]

    assert (
        mod._build_code_orders(
            opportunities, {"pipeline_events": [], "post_sell_candidates": []}
        )
        == []
    )


def test_write_outputs(tmp_path):
    report = {
        "target_date": "2026-07-01",
        "generated_at": "fixed",
        "window": {"since_date": "2026-06-30", "until_date": "2026-07-01"},
        "summary": {
            "forced_record_count": 1,
            "post_sell_joined_count": 1,
            "profitable_joined_count": 1,
            "loss_or_flat_joined_count": 0,
            "threshold_opportunity_count": 1,
            "code_improvement_order_count": 1,
            "ai_review_status": "parsed",
        },
        "threshold_opportunities": [
            {
                "threshold_group": "ai_score_near_buy",
                "candidate_id": "one_share_threshold_ai_score_near_buy",
                "mapped_family": "entry_opportunity_recheck_runtime",
                "sample": 3,
                "valid_profit_sample": 3,
                "equal_weight_avg_profit_pct": 0.4,
                "profitable_count": 2,
                "loss_or_flat_count": 1,
            }
        ],
        "code_improvement_orders": [
            {
                "order_id": "order_one_share_threshold_ai_score_near_buy_entry_hook_review",
                "mapped_family": "entry_opportunity_recheck_runtime",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "ai_recommended_disposition": "attach_existing_entry_hook",
                "evidence": ["sample=3"],
            }
        ],
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert (
        json.loads(output_json.read_text(encoding="utf-8"))["target_date"]
        == "2026-07-01"
    )
    markdown = output_md.read_text(encoding="utf-8")
    assert "One Share Threshold Opportunity" in markdown
    assert "runtime_effect: false" in markdown


def test_build_report_reads_gzip_pipeline_and_filters_clean_baseline(tmp_path):
    old_pipeline_path = tmp_path / "pipeline_events_2026-06-04.jsonl.gz"
    pipeline_path = tmp_path / "pipeline_events_2026-06-05.jsonl.gz"
    post_sell_path = tmp_path / "post_sell_candidates_2026-06-05.jsonl"
    with gzip.open(old_pipeline_path, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event(
                    "old",
                    "rising_missed_one_share_entry",
                    {"forced_entry_reason": "rising_missed_one_share_entry"},
                    emitted_at="2026-06-04T14:30:00+09:00",
                )
            )
            + "\n"
        )
    with gzip.open(pipeline_path, "wt", encoding="utf-8") as handle:
        for row in [
            _event(
                "new",
                "blocked_ai_score",
                {"reason": "blocked_ai_score_below_buy_score_threshold"},
                emitted_at="2026-06-05T09:00:00+09:00",
            ),
            _event(
                "new",
                "rising_missed_one_share_entry",
                {"forced_entry_reason": "rising_missed_one_share_entry"},
                emitted_at="2026-06-05T09:01:00+09:00",
            ),
        ]:
            handle.write(json.dumps(row) + "\n")
    post_sell_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": "old",
                        "stock_code": "000001",
                        "profit_rate": 9.9,
                    }
                ),
                json.dumps(
                    {
                        "recommendation_id": "new",
                        "stock_code": "000001",
                        "profit_rate": 0.3,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-06-05",
        since_date="2026-06-04",
        pipeline_paths=[old_pipeline_path, pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    assert report["summary"]["forced_record_count"] == 1
    assert report["joined_examples"][0]["record_id"] == "new"
    assert report["source_coverage_manifest"]["pipeline_gzip_path_count"] == 2
    assert report["window"]["clean_baseline_ts_kst"] == "2026-06-05T00:00:00+09:00"


def test_post_sell_maturity_date_does_not_require_same_day_pipeline_partition(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-02.jsonl"
    pipeline_path.write_text(
        "\n".join(
            [
                json.dumps(
                    _event(
                        1,
                        "blocked_ai_score",
                        {"reason": "blocked_ai_score_below_buy_score_threshold"},
                    )
                ),
                json.dumps(
                    _event(
                        1,
                        "rising_missed_one_share_entry",
                        {"forced_entry_reason": "rising_missed_one_share_entry"},
                    )
                ),
                json.dumps(
                    _event(
                        1,
                        "order_bundle_submitted",
                        {"actual_order_submitted": True},
                    )
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "stock_code": "000001", "profit_rate": 1.0})
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    assert report["summary"]["source_coverage_status"] == "pass"
    assert report["source_coverage_manifest"]["post_sell_only_dates"] == ["2026-07-02"]
    assert (
        report["source_coverage_manifest"]["post_sell_only_dates_are_informational"]
        is True
    )
    assert (
        report["source_coverage_manifest"]["entry_date_partition_match_required"]
        is False
    )
    assert (
        report["source_coverage_manifest"]["pending_or_right_censored_submit_count"]
        == 0
    )


def test_terminal_sell_in_later_pipeline_partition_joins_by_record_id(tmp_path):
    entry_pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    sell_pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-02.jsonl"
    cache_dir = tmp_path / "cache"
    entry_pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "blocked_ai_score",
                    {"block_reason": "blocked_ai_score"},
                ),
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
            ]
        ),
        encoding="utf-8",
    )
    sell_pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "sell_completed",
                emitted_at="2026-07-02T09:00:00+09:00",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "stock_code": "000001", "profit_rate": 0.5})
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[entry_pipeline_path, sell_pipeline_path],
        post_sell_paths=[post_sell_path],
        partition_cache_dir=cache_dir,
        use_partition_cache=True,
    )

    assert report["source_coverage_manifest"]["terminal_sell_record_count"] == 1
    assert (
        report["source_coverage_manifest"]["missing_terminal_post_sell_record_count"]
        == 0
    )
    assert report["summary"]["source_coverage_status"] == "pass"


def test_submitted_without_terminal_sell_is_pending_not_source_gap(
    tmp_path, monkeypatch
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            [
                json.dumps(
                    _event(
                        1,
                        "rising_missed_one_share_entry",
                        {"rising_missed_one_share_entry_forced": True},
                    )
                ),
                json.dumps(
                    _event(
                        1, "order_bundle_submitted", {"actual_order_submitted": True}
                    )
                ),
            ]
        ),
        encoding="utf-8",
    )

    def unexpected_call(*args, **kwargs):
        raise AssertionError("no actionable candidate must not call the AI provider")

    monkeypatch.setattr(mod, "_call_ai_review", unexpected_call)
    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[],
        generated_at="fixed",
        ai_provider="openai",
    )

    assert report["summary"]["source_coverage_status"] == "pass"
    assert (
        report["source_coverage_manifest"]["pending_or_right_censored_submit_count"]
        == 1
    )
    assert report["ai_review"]["status"] == ("not_required_no_actionable_candidate")
    assert report["ai_review"]["provider_status"]["new_provider_call"] is False
    assert report["summary"]["ai_reviewed_candidate_count"] == 0
    assert report["candidate_change"]["semantic_change_requires_new_ai_review"] is False


def test_terminal_sell_without_post_sell_row_is_coverage_gap(tmp_path, monkeypatch):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
                _event(1, "order_bundle_submitted", {"actual_order_submitted": True}),
                _event(
                    1,
                    "sell_completed",
                    {"main_lifecycle_reconciled_final_exit": True},
                ),
            ]
        ),
        encoding="utf-8",
    )

    def unexpected_call(*args, **kwargs):
        raise AssertionError("source coverage failure must not call the AI provider")

    monkeypatch.setattr(mod, "_call_ai_review", unexpected_call)
    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[],
        generated_at="fixed",
        ai_provider="openai",
    )

    coverage = report["source_coverage_manifest"]
    assert report["summary"]["source_coverage_status"] == "source_coverage_gap"
    assert coverage["terminal_sell_record_count"] == 1
    assert coverage["missing_terminal_post_sell_record_count"] == 1
    assert coverage["missing_terminal_post_sell_record_ids"] == ["1"]
    assert coverage["pending_or_right_censored_submit_count"] == 0
    assert report["ai_review"]["status"] == "blocked_source_coverage"
    assert report["ai_review"]["provider_status"]["new_provider_call"] is False


def test_fixed_taxonomy_groups_are_not_all_reported_as_new_candidates(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    stages = [
        ("blocked_ai_score", {"block_reason": "blocked_ai_score"}),
        ("latency_block", {"block_reason": "latency"}),
        ("blocked_strength_momentum", {"block_reason": "below_strength"}),
        (
            "pre_submit_liquidity_guard_block",
            {"block_reason": "liquidity"},
        ),
        ("entry_cooldown_active", {"block_reason": "cooldown"}),
        (
            "rising_missed_one_share_entry",
            {"rising_missed_one_share_entry_forced": True},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(_event(1, stage, fields)) for stage, fields in stages),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "stock_code": "000001", "profit_rate": 0.5})
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
    )

    assert report["summary"]["configured_threshold_group_count"] == 5
    assert report["summary"]["observed_threshold_group_evaluation_count"] == 5
    assert report["summary"]["primary_blocker_evaluation_count"] == 1
    assert report["summary"]["primary_attributed_opportunity_count"] == 0
    assert report["summary"]["actionable_candidate_count"] == 0
    assert all(
        item["is_actionable_candidate"] is False
        for item in report["threshold_group_evaluations"]
    )
    assert report["primary_blocker_evaluations"][0]["threshold_group"] == (
        "ai_score_near_buy"
    )
    assert report["threshold_opportunities"] == []


def test_partition_index_cache_reuses_unchanged_source_and_invalidates_change(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    cache_dir = tmp_path / "cache"
    pipeline_path.write_text(
        "\n".join(
            [
                json.dumps(
                    _event(1, "blocked_ai_score", {"block_reason": "blocked_ai_score"})
                ),
                json.dumps(
                    _event(
                        1,
                        "rising_missed_one_share_entry",
                        {"rising_missed_one_share_entry_forced": True},
                    )
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "profit_rate": 0.5}) + "\n",
        encoding="utf-8",
    )

    first = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        partition_cache_dir=cache_dir,
        use_partition_cache=True,
        generated_at="fixed",
    )
    second = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        partition_cache_dir=cache_dir,
        use_partition_cache=True,
        generated_at="fixed",
    )
    pipeline_path.write_text(
        pipeline_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    third = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        partition_cache_dir=cache_dir,
        use_partition_cache=True,
        generated_at="fixed",
    )

    assert first["source_processing"]["cache_miss_count"] == 1
    assert first["source_processing"]["cache_hit_count"] == 0
    assert second["source_processing"]["cache_hit_count"] == 1
    assert second["source_processing"]["source_bytes_scanned"] == 0
    assert third["source_processing"]["cache_miss_count"] == 1
    assert first["threshold_opportunities"] == second["threshold_opportunities"]
    assert first["threshold_opportunities"] == third["threshold_opportunities"]


def test_partition_cache_payload_excludes_unrelated_population(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    cache_dir = tmp_path / "cache"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event("unrelated", "blocked_ai_score", {"block_reason": "ai_score"}),
                _event("forced", "blocked_ai_score", {"block_reason": "ai_score"}),
                _event(
                    "forced",
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
                _event("terminal-only", "sell_completed"),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        partition_cache_dir=cache_dir,
        use_partition_cache=True,
    )
    cache_payload = json.loads(
        next(cache_dir.glob("*.json")).read_text(encoding="utf-8")
    )

    assert set(cache_payload["forced"]) == {"forced"}
    assert set(cache_payload["threshold_counts"]) == {"forced"}
    assert set(cache_payload["primary_blockers"]) == {"forced"}
    assert set(cache_payload["cross_partition_provenance"]) == {"terminal-only"}
    assert "unrelated" not in json.dumps(cache_payload["threshold_counts"])
    assert report["source_processing"]["cache_payload_scope"] == (
        "local_forced_records_plus_cross_partition_terminal_sell_provenance"
    )


def test_targeted_scan_verifies_top_level_record_id_after_nested_prefilter_candidate(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    forced = _event(
        "forced",
        "rising_missed_one_share_entry",
        {"rising_missed_one_share_entry_forced": True},
    )
    nested_first_matching_wrong_top_level = {
        "fields": {"record_id": "forced", "block_reason": "latency"},
        "record_id": "unrelated",
        "stage": "latency_block",
        "emitted_at": "2026-07-01T08:59:00+09:00",
    }
    nested_first_nonmatching_correct_top_level = {
        "fields": {"record_id": "unrelated", "block_reason": "latency"},
        "record_id": "forced",
        "stage": "latency_block",
        "emitted_at": "2026-07-01T08:59:00+09:00",
    }
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                nested_first_matching_wrong_top_level,
                nested_first_nonmatching_correct_top_level,
                forced,
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps(
            {
                "recommendation_id": "forced",
                "stock_code": "000001",
                "profit_rate": 0.5,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
    )

    row = report["source_identity_conflict_examples"]
    assert row == []
    assert report["summary"]["forced_record_count"] == 1
    assert report["primary_blocker_evaluations"][0]["threshold_group"] == (
        "latency_or_freshness"
    )
    assert report["threshold_opportunities"] == []


def test_primary_blocker_uses_event_time_and_rejects_post_force_only(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    "causal",
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                    emitted_at="2026-07-01T09:00:00+09:00",
                ),
                _event(
                    "causal",
                    "latency_block",
                    {"block_reason": "latency"},
                    emitted_at="2026-07-01T09:01:00+09:00",
                ),
                _event(
                    "causal",
                    "blocked_ai_score",
                    {"block_reason": "blocked_ai_score"},
                    emitted_at="2026-07-01T08:59:00+09:00",
                ),
                _event(
                    "post-only",
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                    emitted_at="2026-07-01T09:00:00+09:00",
                ),
                _event(
                    "post-only",
                    "latency_block",
                    {"block_reason": "latency"},
                    emitted_at="2026-07-01T09:01:00+09:00",
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": record_id,
                    "stock_code": "000001",
                    "profit_rate": 0.5,
                }
            )
            for record_id in ("causal", "post-only")
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )
    examples = {row["record_id"]: row for row in report["joined_examples"]}

    assert examples["causal"]["primary_threshold_group"] == "ai_score_near_buy"
    assert examples["causal"]["primary_blocker_event"]["emitted_at"] == (
        "2026-07-01T08:59:00+09:00"
    )
    assert examples["post-only"]["primary_threshold_group"] is None
    assert examples["post-only"]["primary_blocker_attribution_status"] == (
        "post_force_or_unordered_blocker_only"
    )


def test_main_explicit_partition_cache_dir_enables_cache(tmp_path, monkeypatch):
    captured = {}

    def fake_build_report(target_date, **kwargs):
        captured.update({"target_date": target_date, **kwargs})
        return {"summary": {}}

    monkeypatch.setattr(mod, "build_report", fake_build_report)
    monkeypatch.setattr(mod, "write_outputs", lambda *args, **kwargs: None)

    assert (
        mod.main(
            [
                "--target-date",
                "2026-07-01",
                "--pipeline-path",
                str(tmp_path / "pipeline.jsonl"),
                "--partition-cache-dir",
                str(tmp_path / "cache"),
                "--output-json",
                str(tmp_path / "report.json"),
                "--output-md",
                str(tmp_path / "report.md"),
            ]
        )
        == 0
    )
    assert captured["partition_cache_dir"] == tmp_path / "cache"
    assert captured["use_partition_cache"] is True


def test_conflicting_post_sell_rows_fail_closed_instead_of_last_row_wins(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(1, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 1,
                        "signal_date": "2026-07-01",
                        "stock_code": "000001",
                        "profit_rate": 0.5,
                    }
                ),
                json.dumps(
                    {
                        "recommendation_id": 1,
                        "signal_date": "2026-07-02",
                        "stock_code": "000001",
                        "profit_rate": -0.5,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert report["summary"]["source_coverage_status"] == "source_coverage_gap"
    assert report["source_coverage_manifest"]["identity_conflict_record_count"] == 1
    assert report["post_sell_identity_diagnostics"]["ambiguous_record_id_count"] == 1
    assert report["post_sell_identity_diagnostics"]["last_row_wins_allowed"] is False
    assert report["code_improvement_orders"] == []


def test_post_sell_stock_code_mismatch_blocks_join(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(1, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps(
            {
                "recommendation_id": 1,
                "stock_code": "999999",
                "profit_rate": 0.5,
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert (
        report["source_identity_conflict_examples"][0]["source_identity_status"]
        == "post_sell_stock_code_conflict"
    )
    assert report["source_coverage_manifest"]["status"] == "source_coverage_gap"


def test_reused_forced_record_id_is_quarantined(tmp_path):
    first_pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    second_pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-02.jsonl"
    first_pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "rising_missed_one_share_entry",
                {"rising_missed_one_share_entry_forced": True},
                code="000001",
                emitted_at="2026-07-01T09:00:00+09:00",
            )
        ),
        encoding="utf-8",
    )
    second_pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "rising_missed_one_share_entry",
                {"rising_missed_one_share_entry_forced": True},
                code="000002",
                emitted_at="2026-07-02T09:00:00+09:00",
            )
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps(
            {
                "recommendation_id": 1,
                "stock_code": "000001",
                "profit_rate": 0.5,
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[first_pipeline_path, second_pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["forced_record_count"] == 1
    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert (
        report["source_identity_conflict_examples"][0]["source_identity_status"]
        == "forced_record_id_reused"
    )
    assert report["source_coverage_manifest"]["status"] == "source_coverage_gap"


def test_post_sell_missing_stock_code_is_quarantined(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "rising_missed_one_share_entry",
                {"rising_missed_one_share_entry_forced": True},
            )
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "profit_rate": 0.5}),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert (
        report["source_identity_conflict_examples"][0]["source_identity_status"]
        == "post_sell_stock_code_missing"
    )
    assert report["source_coverage_manifest"]["status"] == "source_coverage_gap"


def test_relevant_malformed_source_rows_block_candidate_and_ai_review(
    tmp_path, monkeypatch
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    valid_pipeline_rows = [
        row
        for idx in range(1, 4)
        for row in (
            _event(idx, "blocked_ai_score", {"block_reason": "blocked_ai_score"}),
            _event(
                idx,
                "rising_missed_one_share_entry",
                {"rising_missed_one_share_entry_forced": True},
            ),
        )
    ]
    pipeline_path.write_text(
        "\n".join(
            [
                *(json.dumps(row) for row in valid_pipeline_rows),
                '{"record_id": 1, "stage": "rising_missed_one_share_entry"',
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        "\n".join(
            [
                *(
                    json.dumps(
                        {
                            "recommendation_id": idx,
                            "stock_code": "000001",
                            "profit_rate": 0.5,
                        }
                    )
                    for idx in range(1, 4)
                ),
                '{"recommendation_id": 4, "stock_code": "000001"',
            ]
        ),
        encoding="utf-8",
    )

    def unexpected_call(*args, **kwargs):
        raise AssertionError("malformed source coverage must block the AI provider")

    monkeypatch.setattr(mod, "_call_ai_review", unexpected_call)
    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        ai_provider="openai",
    )

    assert report["source_processing"]["invalid_json_row_count"] == 1
    assert report["post_sell_identity_diagnostics"]["invalid_json_row_count"] == 1
    assert report["source_coverage_manifest"]["invalid_source_json_row_count"] == 2
    assert report["source_coverage_manifest"]["status"] == "source_coverage_gap"
    assert report["code_improvement_orders"] == []
    assert report["ai_review"]["status"] == "blocked_source_coverage"


def test_propagated_forced_event_stock_conflict_is_quarantined(tmp_path):
    first_pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    second_pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-02.jsonl"
    first_pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "rising_missed_one_share_entry",
                {"rising_missed_one_share_entry_forced": True},
                code="000001",
                emitted_at="2026-07-01T09:00:00+09:00",
            )
        ),
        encoding="utf-8",
    )
    second_pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "order_bundle_submitted",
                {
                    "rising_missed_one_share_entry_forced": True,
                    "actual_order_submitted": True,
                },
                code="000002",
                emitted_at="2026-07-01T09:00:01+09:00",
            )
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps(
            {
                "recommendation_id": 1,
                "stock_code": "000001",
                "profit_rate": 0.5,
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        since_date="2026-07-01",
        pipeline_paths=[first_pipeline_path, second_pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert (
        report["source_identity_conflict_examples"][0]["source_identity_status"]
        == "forced_record_id_reused"
    )
    assert report["source_coverage_manifest"]["status"] == "source_coverage_gap"


def test_conflicting_terminal_sell_identity_is_quarantined(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "rising_missed_one_share_entry",
                    {"rising_missed_one_share_entry_forced": True},
                    emitted_at="2026-07-01T09:00:00+09:00",
                ),
                _event(
                    1,
                    "sell_completed",
                    emitted_at="2026-07-01T09:10:00+09:00",
                ),
                _event(
                    1,
                    "sell_completed",
                    emitted_at="2026-07-01T09:11:00+09:00",
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps(
            {
                "recommendation_id": 1,
                "signal_date": "2026-07-01",
                "stock_code": "000001",
                "profit_rate": 0.5,
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
    )

    assert report["summary"]["post_sell_joined_count"] == 0
    assert report["summary"]["source_identity_conflict_record_count"] == 1
    assert (
        report["source_identity_conflict_examples"][0]["source_identity_status"]
        == "terminal_sell_identity_conflict"
    )
