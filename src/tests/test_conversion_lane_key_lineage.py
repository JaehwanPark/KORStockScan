import json
from pathlib import Path

from src.engine.automation import conversion_lane as lane
from src.engine.automation import key_lineage_ledger as ledger
from src.engine.scalping import scalp_sim_auto_approval_control_tower as scalp_catalog
from src.engine.swing import sim_auto_approval_control_tower as swing_catalog


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _patch_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ledger, "REPORT_DIR", tmp_path / "report" / "key_lineage_ledger")
    monkeypatch.setattr(ledger, "APPLY_PLAN_DIR", tmp_path / "threshold_cycle" / "apply_plans")
    monkeypatch.setattr(ledger, "SCALP_POLICY_DIR", tmp_path / "threshold_cycle" / "scalp_sim_policies")
    monkeypatch.setattr(ledger, "SWING_POLICY_DIR", tmp_path / "threshold_cycle" / "swing_sim_policies")
    monkeypatch.setattr(ledger, "HYPOTHESIS_PLAN_DIR", tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans")
    monkeypatch.setattr(lane, "DATA_DIR", tmp_path)
    monkeypatch.setattr(lane, "REPORT_DIR", tmp_path / "report" / "conversion_lane")


def test_active_seed_same_key_continuity_pass(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "seed_a", "status": "active"}], "surfaced_candidates": []},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "seed_a",
                    "status": "active",
                    "entry_source_taxonomy_contract": {
                        "contract_state": "new_axis_pending_taxonomy",
                        "consume_data": True,
                        "runtime_effect_allowed": False,
                    },
                    "taxonomy_contract_data_consumed": True,
                    "taxonomy_contract_runtime_effect_allowed": False,
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / "threshold_apply_2026-06-05.json",
        {"scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_a"]}}},
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "seed_a"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["same_key_continuity_pass_count"] == 1
    assert report["summary"]["key_mismatch_count"] == 0
    assert report["summary"]["active_sim_policy_loaded_for_effect"] is True
    assert report["summary"]["active_sim_policy_active_seed_id_without_count_event_count"] == 1


def test_active_seed_count_zero_window_is_consumed_but_excluded_from_effect(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "seed_a",
                    "status": "active",
                    "entry_source_taxonomy_contract": {
                        "contract_state": "new_axis_pending_taxonomy",
                        "consume_data": True,
                        "runtime_effect_allowed": False,
                    },
                    "taxonomy_contract_data_consumed": True,
                    "taxonomy_contract_runtime_effect_allowed": False,
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_a"]}},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps({"fields": {"scalp_sim_auto_policy_active_seed_count": "0"}}) + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    row = report["lineage_rows"][0]
    assert row["conversion_state"] == "policy_not_loaded_window"
    assert row["same_key_continuity"] == "not_observed"
    assert row["evidence"]["excluded_from_active_priority_effect"] is True
    assert row["evidence"]["entry_source_taxonomy_contract"]["contract_state"] == "new_axis_pending_taxonomy"
    assert report["summary"]["active_sim_policy_zero_count_event_count"] == 1
    assert report["summary"]["active_sim_policy_zero_count_data_consumed"] is True
    assert report["summary"]["active_sim_policy_zero_count_effect_excluded"] is True
    assert report["summary"]["active_sim_priority_pending_taxonomy_contract_count"] == 1
    assert report["summary"]["natural_match_0_count"] == 0


def test_active_seed_count_positive_window_allows_natural_match_zero(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "seed_a", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_a"]}},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps({"fields": {"scalp_sim_auto_policy_active_seed_count": "2"}}) + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["lineage_rows"][0]["conversion_state"] == "natural_match_0"
    assert report["summary"]["active_sim_policy_loaded_for_effect"] is True
    assert report["summary"]["active_sim_policy_positive_count_event_count"] == 1
    assert report["summary"]["natural_match_0_count"] == 1


def test_key_lineage_splits_active_seed_new_entry_from_followup_context(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "scalp_sim_entry_armed",
                        "fields": {
                            "scalp_sim_auto_policy_active_seed_count": "2",
                            "active_seed_candidate_observable_prefix": "{\"entry_score_parent\":\"score_watch_recovery\"}",
                            "active_seed_id": "seed_a",
                            "scalp_sim_active_priority_seed_matched": "True",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_panic_scale_in_blocked",
                        "fields": {
                            "scalp_sim_auto_policy_active_seed_count": "2",
                            "active_seed_candidate_observable_prefix": "{\"entry_score_parent\":\"score_watch_recovery\"}",
                            "scalp_sim_active_priority_seed_matched": "True",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_entry_armed",
                        "fields": {
                            "scalp_sim_auto_policy_active_seed_count": "2",
                            "active_seed_candidate_observable_prefix": "{\"entry_score_parent\":\"score_mid_recovery\"}",
                            "scalp_sim_active_priority_seed_matched": "False",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_holding_started",
                        "fields": {
                            "scalp_sim_auto_policy_active_seed_count": "2",
                            "active_seed_candidate_observable_prefix": "{\"entry_score_parent\":\"score_mid_recovery\"}",
                            "scalp_sim_active_priority_seed_matched": "False",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["active_seed_candidate_event_count"] == 4
    assert report["summary"]["active_seed_candidate_new_entry_event_count"] == 2
    assert report["summary"]["active_seed_candidate_followup_event_count"] == 2
    assert report["summary"]["active_seed_candidate_matched_event_count"] == 1
    assert report["summary"]["active_seed_candidate_matched_true_without_seed_id_event_count"] == 0
    assert report["summary"]["active_seed_candidate_unmatched_event_count"] == 2
    assert report["summary"]["active_seed_candidate_new_entry_unmatched_event_count"] == 1
    assert report["summary"]["active_seed_candidate_followup_unmatched_event_count"] == 1
    assert report["summary"]["active_seed_candidate_eligible_event_count"] == 3
    assert report["summary"]["active_seed_candidate_not_match_eligible_event_count"] == 1
    assert report["summary"]["active_seed_candidate_without_seed_id_event_count"] == 2
    assert report["summary"]["active_seed_candidate_raw_without_seed_id_event_count"] == 3
    assert report["summary"]["active_seed_candidate_followup_without_seed_id_event_count"] == 1
    assert report["summary"]["active_seed_candidate_raw_followup_without_seed_id_event_count"] == 2
    assert report["summary"]["active_seed_candidate_not_match_eligible_reason_counts"] == {
        "diagnostic_followup_without_seed_context": 1
    }
    assert report["summary"]["active_seed_candidate_without_seed_id_reason_counts"] == {
        "new_entry_without_seed_id": 1,
        "followup_missing_parent_seed_id": 1,
    }
    assert report["summary"]["active_seed_candidate_missing_parent_seed_lookup_key_counts"] == {
        '{"entry_score_parent":"score_mid_recovery"}': 1,
    }
    assert report["summary"]["active_seed_candidate_lineage_closure_status"] == "closed_with_producer_followup"
    assert report["summary"]["active_seed_candidate_lineage_followup_required"] is True
    assert report["summary"]["active_seed_candidate_followup_stage_counts"] == {
        "scalp_sim_holding_started": 1,
        "scalp_sim_panic_scale_in_blocked": 1,
    }


def test_key_lineage_excludes_diagnostic_active_seed_candidate_from_blocker(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "stage": "scalp_sim_holding_started",
                "fields": {
                    "scalp_sim_auto_policy_active_seed_count": "2",
                    "active_seed_candidate_observable_prefix": "{\"entry_score_parent\":\"score_mid_recovery\"}",
                    "active_seed_match_eligible": False,
                    "active_seed_match_exclusion_reason": "diagnostic_followup_without_seed_context",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["active_seed_candidate_event_count"] == 1
    assert report["summary"]["active_seed_candidate_eligible_event_count"] == 0
    assert report["summary"]["active_seed_candidate_not_match_eligible_event_count"] == 1
    assert report["summary"]["active_seed_candidate_without_seed_id_event_count"] == 0
    assert report["summary"]["active_seed_candidate_raw_without_seed_id_event_count"] == 1
    assert report["summary"]["active_seed_candidate_not_match_eligible_reason_counts"] == {
        "diagnostic_followup_without_seed_context": 1
    }
    assert report["summary"]["active_seed_candidate_without_seed_id_reason_counts"] == {}


def test_key_lineage_dedupes_panic_scale_in_no_match_followup(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "stage": "scalp_sim_panic_scale_in_blocked",
            "fields": {
                "sim_record_id": "sim_a",
                "source_stage": "scale_in",
                "scalp_sim_candidate_window_source_stage": "first_ai_wait",
                "lifecycle_bucket_match_status": "no_match",
                "active_seed_candidate_observable_prefix": "{\"entry_source_parent\":\"entry_source_observed_other\"}",
            },
        },
        {
            "stage": "scalp_sim_panic_scale_in_blocked",
            "fields": {
                "sim_record_id": "sim_a",
                "source_stage": "scale_in",
                "scalp_sim_candidate_window_source_stage": "first_ai_wait",
                "lifecycle_bucket_match_status": "no_match",
                "active_seed_candidate_observable_prefix": "{\"entry_source_parent\":\"entry_source_observed_other\"}",
            },
        },
        {
            "stage": "scalp_sim_panic_scale_in_blocked",
            "fields": {
                "sim_record_id": "sim_b",
                "source_stage": "scale_in",
                "lifecycle_bucket_match_status": "matched",
            },
        },
        {
            "stage": "scalp_sim_panic_scale_in_blocked",
            "fields": {
                "source_stage": "scale_in",
                "lifecycle_bucket_match_status": "no_match",
            },
        },
    ]
    event_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["panic_scale_in_event_count"] == 4
    assert report["summary"]["panic_scale_in_unique_sim_record_count"] == 2
    assert report["summary"]["panic_scale_in_match_status_counts"] == {"matched": 1, "no_match": 3}
    assert report["summary"]["panic_scale_in_no_match_event_count"] == 3
    assert report["summary"]["panic_scale_in_no_match_unique_sim_record_count"] == 1
    assert report["summary"]["panic_scale_in_no_match_missing_sim_record_id_event_count"] == 1
    assert report["summary"]["panic_scale_in_no_match_repeated_followup_event_count"] == 1
    assert report["summary"]["panic_scale_in_no_match_source_stage_counts"] == {"first_ai_wait": 2, "scale_in": 1}


def test_runtime_observed_seed_not_in_catalog_is_key_mismatch(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "stale_seed"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["key_mismatch_count"] == 1
    assert report["lineage_rows"][0]["same_key_continuity"] == "fail"
    assert report["lineage_blockers"][0]["blocker_class"] == "key_lineage"


def test_key_lineage_event_io_guard_streams_and_truncates_untracked_ids(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_KEY_LINEAGE_EVENT_UNTRACKED_VALUE_LIMIT", "1")
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "tracked_seed", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["tracked_seed"]}},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        "\n".join(
            [
                json.dumps({"fields": {"active_seed_id": "unknown_seed_a"}}),
                json.dumps({"fields": {"active_seed_id": "unknown_seed_b"}}),
                json.dumps({"fields": {"active_seed_id": "tracked_seed"}}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["same_key_continuity_pass_count"] == 1
    assert report["summary"]["event_io_guard"]["mode"] == "streaming_jsonl"
    assert report["summary"]["event_io_guard"]["lines_read"] == 3
    assert report["summary"]["event_io_guard"]["truncated_untracked_value_count"] == 1
    assert report["summary"]["event_io_guard"]["truncated_untracked_value_count_by_field"] == {"active_seed_id": 1}


def test_key_lineage_event_io_guard_skips_oversized_lines(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_KEY_LINEAGE_EVENT_LINE_BYTES_LIMIT", "20")
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "too_large"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["source_key_count"] == 0
    assert report["summary"]["event_io_guard"]["oversized_line_skipped_count"] == 1


def test_active_seed_candidate_without_seed_details_split_new_entry_and_followup(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    prefix = {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_blocked_ai_score",
    }
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "seed_a", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "scalp_sim_entry_armed",
                        "fields": {
                            "active_seed_candidate_observable_prefix": json.dumps(prefix, sort_keys=True),
                            "scalp_sim_active_priority_seed_matched": False,
                            "active_seed_match_source": "no_match",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_holding_started",
                        "fields": {
                            "active_seed_candidate_observable_prefix": json.dumps(prefix, sort_keys=True),
                            "scalp_sim_active_priority_seed_matched": False,
                            "active_seed_match_source": "no_match",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_holding_started",
                        "fields": {
                            "active_seed_candidate_observable_prefix": json.dumps(prefix, sort_keys=True),
                            "scalp_sim_active_priority_seed_matched": True,
                            "active_seed_id": "seed_a",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)
    summary = report["summary"]

    assert summary["active_seed_candidate_event_count"] == 3
    assert summary["active_seed_candidate_followup_event_count"] == 2
    assert summary["active_seed_candidate_followup_without_seed_id_event_count"] == 1
    assert summary["active_seed_candidate_without_seed_id_reason_counts"] == {
        "followup_missing_parent_seed_id": 1,
        "new_entry_without_seed_id": 1,
    }
    assert summary["active_seed_candidate_without_seed_id_detail_counts"] == {
        "parent_seed_id_not_propagated_to_followup": 1,
        "taxonomy_pending_or_natural_no_match": 1,
    }
    assert summary["active_seed_candidate_missing_parent_seed_stage_counts"] == {
        "scalp_sim_holding_started": 1
    }


def test_key_lineage_infers_followup_parent_seed_from_unique_observable_prefix(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    prefix = {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
    }
    prefix_text = json.dumps(prefix, sort_keys=True)
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "seed_wait6579",
                    "status": "active",
                    "observable_prefix": prefix,
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_wait6579"]}},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "stage": "scalp_sim_holding_started",
                "fields": {
                    "scalp_sim_auto_policy_active_seed_count": "1",
                    "active_seed_candidate_observable_prefix": prefix_text,
                    "scalp_sim_active_priority_seed_matched": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)
    summary = report["summary"]

    assert summary["same_key_continuity_pass_count"] == 1
    assert summary["active_seed_candidate_raw_without_seed_id_event_count"] == 1
    assert summary["active_seed_candidate_without_seed_id_event_count"] == 0
    assert summary["active_seed_candidate_followup_without_seed_id_event_count"] == 0
    assert summary["active_seed_candidate_inferred_parent_seed_id_event_count"] == 1
    assert summary["active_seed_candidate_inferred_parent_seed_id_stage_counts"] == {
        "scalp_sim_holding_started": 1
    }
    assert summary["active_seed_candidate_lineage_closure_status"] == "closed"
    assert summary["active_seed_candidate_lineage_followup_required"] is False
    assert "inferred_parent_seed_id=`1`" in ledger._render_markdown(report)


def test_key_lineage_keeps_ambiguous_observable_prefix_as_followup_gap(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    prefix = {"entry_score_parent": "score_watch_recovery"}
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "active_sim_priority_seeds": [
                {"active_seed_id": "seed_a", "status": "active", "observable_prefix": prefix},
                {"active_seed_id": "seed_b", "status": "active", "observable_prefix": prefix},
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_a", "seed_b"]}},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "stage": "scalp_sim_holding_started",
                "fields": {
                    "scalp_sim_auto_policy_active_seed_count": "2",
                    "active_seed_candidate_observable_prefix": json.dumps(prefix, sort_keys=True),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)
    summary = report["summary"]

    assert summary["active_seed_candidate_ambiguous_parent_seed_prefix_event_count"] == 1
    assert summary["active_seed_candidate_inferred_parent_seed_id_event_count"] == 0
    assert summary["active_seed_candidate_without_seed_id_event_count"] == 1
    assert summary["active_seed_candidate_lineage_followup_required"] is True


def test_runtime_lineage_uses_target_apply_catalog_not_next_catalog(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-02.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "runtime_seed", "status": "active"}]},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "next_day_seed", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-02.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": "2026-06-02",
            "scalp_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-02.json"),
                "approved_request": {"active_sim_priority_seed_ids": ["runtime_seed"]},
            },
            "swing_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-02.json"),
            },
        },
    )
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / "threshold_apply_2026-06-05.json",
        {"scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["next_day_seed"]}}},
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "runtime_seed"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["key_mismatch_count"] == 0
    assert report["summary"]["same_key_continuity_pass_count"] == 1


def test_hypothesis_plan_without_catalog_becomes_catalog_missing(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans" / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["catalog_missing_count"] == 1


def test_hypothesis_match_attempt_without_id_is_natural_match_zero(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans" / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"hypothesis_observation_plan": {"hypotheses": [{"hypothesis_id": "hyp_1"}]}},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps({"fields": {"ldm_hypothesis_matched": "False", "ldm_hypothesis_candidate_features": "{}"}}) + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["natural_match_0_count"] == 1
    assert report["summary"]["not_instrumented_count"] == 0


def test_runtime_matched_lifecycle_bucket_source_id_closes_bucket_continuity(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    source_bucket_id = "lifecycle_flow:combo_entry:abc123"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "policies": [
                {
                    "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
                    "approved_bucket_rows": [
                        {
                            "bucket_id": "lifecycle_flow:combo_entry",
                            "source_bucket_id": source_bucket_id,
                            "classification_state": "lifecycle_flow_sim_probe_candidate",
                            "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                            "source_quality_adjusted_ev_pct": 0.75,
                            "sample": 4,
                        }
                    ],
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "fields": {
                    "bucket_directed_sim_probe": "True",
                    "lifecycle_bucket_match_status": "matched",
                    "lifecycle_bucket_bucket_id": "lifecycle_flow:combo_entry",
                    "lifecycle_bucket_source_bucket_id": source_bucket_id,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    bucket_rows = [row for row in report["lineage_rows"] if row["source_key_type"] == "bucket"]
    assert bucket_rows[0]["source_key_id"] == source_bucket_id
    assert bucket_rows[0]["conversion_state"] == "matched"
    assert bucket_rows[0]["same_key_continuity"] == "pass"
    assert bucket_rows[0]["positive_ev_candidate"] is True
    assert bucket_rows[0]["runtime_observed_same_key"] is True
    assert report["summary"]["positive_ev_runtime_observed_count"] == 1
    assert report["summary"]["bucket_same_key_continuity_pass_count"] == 1


def test_key_lineage_marks_new_postclose_candidates_not_due_when_runtime_uses_prior_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "lifecycle_flow:known_shortfall",
                    "source_bucket_id": "lifecycle_flow:known_shortfall:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 1,
                    "sample_floor": 10,
                },
                {
                    "bucket_id": "lifecycle_flow:unknown_floor",
                    "source_bucket_id": "lifecycle_flow:unknown_floor:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 0,
                },
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-04.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-04.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": "2026-06-04",
            "scalp_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-04.json")
            },
            "swing_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-04.json")
            },
        },
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["runtime_policy_source_date"] == "2026-06-04"
    assert report["summary"]["postclose_candidate_source_date"] == target
    assert report["summary"]["runtime_policy_matches_postclose_candidate_source"] is False
    assert report["summary"]["new_postclose_candidates_due_state"] == "not_due_until_next_preopen"
    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_unknown_floor_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_related_count"] == 2
    assert report["summary"]["positive_ev_sample_floor_count_scope"] == "lineage_rows"
    assert report["summary"]["positive_ev_sample_floor_window_policy"] == "source_report_window"
    assert report["summary"]["positive_ev_sample_floor_basis"] == "lineage_evidence_sample_vs_sample_floor"


def test_key_lineage_keeps_explicit_zero_primary_ev_non_positive(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    source_bucket_id = "lifecycle_flow:combo_entry:zero_ev"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "policies": [
                {
                    "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
                    "approved_bucket_rows": [
                        {
                            "bucket_id": "lifecycle_flow:combo_entry",
                            "source_bucket_id": source_bucket_id,
                            "classification_state": "lifecycle_flow_sim_probe_candidate",
                            "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                            "primary_ev": 0.0,
                            "source_quality_adjusted_ev_pct": 0.75,
                            "sample": 4,
                        }
                    ],
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "fields": {
                    "bucket_directed_sim_probe": "True",
                    "lifecycle_bucket_match_status": "matched",
                    "lifecycle_bucket_bucket_id": "lifecycle_flow:combo_entry",
                    "lifecycle_bucket_source_bucket_id": source_bucket_id,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    bucket_rows = [row for row in report["lineage_rows"] if row["source_key_type"] == "bucket"]
    assert bucket_rows[0]["same_key_continuity"] == "pass"
    assert bucket_rows[0]["positive_ev_candidate"] is False
    assert report["summary"]["positive_ev_runtime_observed_count"] == 0


def test_conversion_lane_adds_runtime_observed_matched_bucket_to_real_queue(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {
                "lineage_blocker_count": 0,
                "active_seed_candidate_inferred_parent_seed_id_event_count": 2,
                "active_seed_candidate_inferred_parent_seed_id_stage_counts": {
                    "scalp_sim_holding_started": 2
                },
                "active_seed_candidate_ambiguous_parent_seed_prefix_event_count": 1,
            },
            "lineage_rows": [
                {
                    "source_key_id": "lifecycle_flow:combo_entry:abc123",
                    "source_key_type": "bucket",
                    "source_artifact": "scalp_sim_policy_catalog",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "evidence": {
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "primary_ev": 0.75,
                        "sample": 4,
                        "bucket_id": "lifecycle_flow:combo_entry",
                    },
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})

    report = lane.build_conversion_lane(target)

    assert report["summary"]["real_conversion_queue_count"] == 1
    assert report["summary"]["positive_ev_runtime_observed_count"] == 1
    assert report["summary"]["positive_ev_real_conversion_queue_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 0
    assert report["summary"]["positive_ev_sample_floor_unknown_floor_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_related_count"] == 1
    assert report["summary"]["active_seed_candidate_inferred_parent_seed_id_event_count"] == 2
    assert report["summary"]["active_seed_candidate_inferred_parent_seed_id_stage_counts"] == {
        "scalp_sim_holding_started": 2
    }
    assert report["summary"]["active_seed_candidate_ambiguous_parent_seed_prefix_event_count"] == 1
    assert "inferred_parent_seed_id=`2`" in lane._render_markdown(report)
    assert report["summary"]["conversion_candidate_strategy_scope_counts"]["scalp"] == 1
    assert report["summary"]["unscoped_conversion_candidate_count"] == 0
    assert report["summary"]["conversion_blocker_count"] == 1
    assert report["real_conversion_queue"][0]["conversion_state"] == "runtime_observed"
    assert report["real_conversion_queue"][0]["runtime_observation_scope"] == "previous_preopen_policy_runtime_observed"
    assert report["real_conversion_queue"][0]["positive_ev_candidate"] is True
    assert report["real_conversion_queue"][0]["sample_floor_blocked"] is False
    assert report["real_conversion_queue"][0]["sample_floor_unknown_floor"] is True


def test_conversion_lane_merges_lineage_match_into_existing_lifecycle_candidate(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    source_bucket_id = "bucket:source:1"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [
                {
                    "source_key_id": source_bucket_id,
                    "source_key_type": "bucket",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "runtime_match_key": source_bucket_id,
                    "postclose_observed_key": source_bucket_id,
                    "evidence": {"primary_ev": 1.2, "sample": 12, "sample_floor": 10},
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket:source",
                    "source_bucket_id": source_bucket_id,
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "sample": 12,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    candidate = next(item for item in report["conversion_candidates"] if item["source_key_id"] == source_bucket_id)

    assert candidate["conversion_state"] == "runtime_observed"
    assert candidate["runtime_observed_same_key"] is True
    assert candidate["runtime_observation_scope"] == "previous_preopen_policy_runtime_observed"
    assert report["summary"]["positive_ev_runtime_observed_count"] == 1


def test_conversion_lane_does_not_count_non_positive_ev_as_positive(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [
                {
                    "source_key_id": "lifecycle_flow:combo_entry:abc123",
                    "source_key_type": "bucket",
                    "source_artifact": "scalp_sim_policy_catalog",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "evidence": {
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "primary_ev": -0.1,
                        "sample": 4,
                        "bucket_id": "lifecycle_flow:combo_entry",
                    },
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})

    report = lane.build_conversion_lane(target)

    assert report["summary"]["real_conversion_queue_count"] == 0
    assert report["summary"]["positive_ev_runtime_observed_count"] == 0
    assert report["summary"]["top_blocker_ranked_class"] == "sample_floor"
    assert report["summary"]["top_blocker_by_count_class"] == "sample_floor"
    assert report["summary"]["positive_ev_real_conversion_queue_count"] == 0


def test_conversion_lane_promotes_lineage_blocker_to_rank(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 1},
            "lineage_rows": [],
            "lineage_blockers": [
                {
                    "blocker_id": "b1",
                    "source_key_id": "seed_x",
                    "source_key_type": "active_seed",
                    "next_repair_action": "runtime_observed_seed_not_in_catalog",
                }
            ],
        },
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket_a",
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "sample": 3,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["key_lineage_blocker_count"] == 1
    assert report["conversion_blocker_rank"][0]["blocker_class"] == "key_lineage"


def test_conversion_lane_submit_drought_blockers_have_split_axes(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {"summary": {"lineage_blocker_count": 0}, "lineage_rows": [], "lineage_blockers": []},
    )
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "report" / "buy_funnel_sentinel" / f"buy_funnel_sentinel_{target}.json",
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
                "submit_drought_handoff_state": "handoff_required",
                "submit_drought_root_cause": {
                    "latency_root_cause_counts": {"unknown_latency_reason": 7},
                    "quote_freshness_attribution": {
                        "refresh_subreason_counts": {
                            "ws_snapshot_refresh_failed_stale": 3,
                            "observer_quote_refresh_failed_missing": 2,
                            "observer_quote_refresh_failed_stale": 1,
                        },
                        "refresh_attempted_count": 5,
                        "refresh_applied_count": 0,
                        "latency_pass_recovered_count": 1,
                        "order_bundle_submitted_after_refresh_count": 1,
                    },
                    "unknown_latency_reason_count": 7,
                    "unknown_latency_workorder_required": True,
                },
            }
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["submit_drought_split_complete"] is True
    assert report["summary"]["submit_drought_closure_axis_count"] == 6
    assert report["summary"]["submit_funnel_blocker_count"] == 6
    assert report["summary"]["submit_drought_is_ldm_bucket_blocker"] is False
    assert report["summary"]["buy_funnel_source_present"] is True
    assert report["summary"]["buy_funnel_classification_primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert report["summary"]["submit_drought_blocker_source_state"] == "submit_drought_critical"
    assert report["summary"]["submit_drought_unknown_latency_reason_count"] == 7
    assert report["summary"]["submit_drought_unknown_latency_workorder_required"] is True
    assert report["summary"]["submit_drought_refresh_attempted_count"] == 5
    assert report["summary"]["submit_drought_quote_freshness_subaction_counts"][
        "close_ws_snapshot_refresh_stale_source"
    ] == 3
    assert report["summary"]["submit_drought_quote_freshness_subaction_counts"][
        "close_observer_quote_missing"
    ] == 2
    assert report["summary"]["submit_drought_quote_freshness_subaction_counts"][
        "close_observer_quote_stale_source"
    ] == 1
    assert report["summary"]["submit_drought_quote_freshness_subaction_counts"][
        "close_unknown_latency_reason"
    ] == 7
    assert report["summary"]["top_ldm_bucket_blocker_class"] is None
    submit_blockers = [
        item for item in report["conversion_blocker_rank"] if item["blocker_class"] == "submit_drought"
    ]
    assert {item["blocker_axis"] for item in submit_blockers} == set(lane.SUBMIT_DROUGHT_CLOSURE_AXES)
    latency_blocker = next(item for item in submit_blockers if item["blocker_axis"] == "LATENCY_PRE_SUBMIT")
    assert latency_blocker["next_repair_action"] == "close_submit_drought_latency_pre_submit_quote_freshness"
    assert latency_blocker["quote_freshness_subaction_counts"]["close_observer_quote_missing"] == 2
    assert all(item["blocker_runtime_effect"] is False for item in submit_blockers)
    assert all(item["blocker_allowed_runtime_apply"] is False for item in submit_blockers)


def test_conversion_lane_records_buy_funnel_non_submit_drought_source_state(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {"summary": {"lineage_blocker_count": 0}, "lineage_rows": [], "lineage_blockers": []},
    )
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "report" / "buy_funnel_sentinel" / f"buy_funnel_sentinel_{target}.json",
        {
            "report_type": "buy_funnel_sentinel",
            "classification": {
                "primary": "PRICE_GUARD_DROUGHT",
                "matches": ["PRICE_GUARD_DROUGHT", "LATENCY_DROUGHT"],
            },
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["submit_funnel_blocker_count"] == 0
    assert report["summary"]["submit_drought_split_complete"] is False
    assert report["summary"]["buy_funnel_source_present"] is True
    assert report["summary"]["buy_funnel_report_type"] == "buy_funnel_sentinel"
    assert report["summary"]["buy_funnel_classification_primary"] == "PRICE_GUARD_DROUGHT"
    assert report["summary"]["buy_funnel_classification_matches"] == [
        "PRICE_GUARD_DROUGHT",
        "LATENCY_DROUGHT",
    ]
    assert report["summary"]["submit_drought_blocker_source_state"] == "not_submit_drought_critical"


def test_conversion_lane_marks_new_positive_postclose_candidate_not_due_until_next_preopen(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {
                "lineage_blocker_count": 0,
                "runtime_policy_source_date": "2026-06-04",
                "postclose_candidate_source_date": target,
                "new_postclose_candidates_due_state": "not_due_until_next_preopen",
            },
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "entry:source_stage:wait6579_ev_cohort",
                    "source_bucket_id": "entry:source_stage:wait6579_ev_cohort:abc",
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 2.0,
                    "sample": 52,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    candidate = report["conversion_candidates"][0]

    assert candidate["positive_ev_candidate"] is True
    assert candidate["runtime_observed_same_key"] is False
    assert candidate["runtime_observation_scope"] == "new_postclose_candidate_not_due_until_next_preopen"
    assert candidate["sample_floor_status"] == "pass"
    assert candidate["sample_floor_blocked"] is False
    assert candidate["sample_floor_unknown_floor"] is False
    assert report["summary"]["positive_ev_not_due_until_next_preopen_count"] == 1
    assert report["summary"]["positive_ev_runtime_observed_count"] == 0
    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 0
    assert report["summary"]["positive_ev_sample_floor_unknown_floor_count"] == 0


def test_conversion_lane_counts_known_positive_sample_floor_shortfall(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {"summary": {"lineage_blocker_count": 0}, "lineage_rows": [], "lineage_blockers": []},
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "lifecycle_flow:thin_positive",
                    "source_bucket_id": "lifecycle_flow:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    candidate = report["conversion_candidates"][0]

    assert candidate["required_sample"] == 10
    assert candidate["sample_floor_status"] == "below_floor"
    assert candidate["sample_floor_blocked"] is True
    assert candidate["sample_floor_unknown_floor"] is False
    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_unknown_floor_count"] == 0
    assert report["summary"]["positive_ev_sample_floor_related_count"] == 1
    assert report["summary"]["positive_ev_sample_floor_count_scope"] == "conversion_candidates"
    assert report["summary"]["positive_ev_sample_floor_window_policy"] == "source_report_window"
    assert report["summary"]["positive_ev_sample_floor_basis"] == "candidate_sample_vs_required_sample"


def test_conversion_lane_marks_mixed_sample_floor_windows(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {"summary": {"lineage_blocker_count": 0}, "lineage_rows": [], "lineage_blockers": []},
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "scalp_daily_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "scalp:thin_positive",
                    "source_bucket_id": "scalp:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ],
        },
    )
    _write(
        tmp_path / "report" / "swing_lifecycle_bucket_discovery" / f"swing_lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "swing_rolling_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "swing:thin_positive",
                    "source_bucket_id": "swing:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.8,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ],
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 2
    assert report["summary"]["positive_ev_sample_floor_window_policy"] == "mixed_source_windows"
    assert report["summary"]["positive_ev_sample_floor_window_policy_counts"] == {
        "scalp_daily_window": 1,
        "swing_rolling_window": 1,
    }
    markdown = lane._render_markdown(report)
    assert "window_counts=`{'scalp_daily_window': 1, 'swing_rolling_window': 1}`" in markdown


def test_key_lineage_marks_mixed_sample_floor_windows(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {"summary": {"source_window_policy": "scalp_daily_window"}},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-04.json",
        {"hypothesis_observation_plan": {"hypotheses": [{"hypothesis_id": "hypothesis_a"}]}},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-04.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": "2026-06-04",
            "scalp_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-04.json")
            },
            "swing_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-04.json")
            },
        },
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "scalp_daily_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket_a",
                    "source_bucket_id": "bucket_a:source",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.6,
                    "sample": 1,
                    "sample_floor": 10,
                },
                {
                    "bucket_id": "bucket_b",
                    "source_bucket_id": "bucket_b:source",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.7,
                    "sample": 1,
                    "sample_floor": 10,
                    "sample_floor_window_policy": "bucket_custom_window",
                },
            ],
        },
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["positive_ev_sample_floor_window_policy"] == "mixed_source_windows"
    assert report["summary"]["positive_ev_sample_floor_window_policy_counts"]["scalp_daily_window"] == 1
    assert report["summary"]["positive_ev_sample_floor_window_policy_counts"]["bucket_custom_window"] == 1


def test_conversion_blocker_class_ignores_source_key_field_names():
    row = {
        "source_key_type": "bucket",
        "source_key_id": "bucket_a",
        "next_blocker": "bridge_contract",
        "bridge_state": "blocked_contract_gap",
    }

    assert lane._blocker_class("bridge_contract", row) == "bridge_contract"


def test_sim_policy_catalogs_merge_latest_hypothesis_plan(monkeypatch, tmp_path):
    plan_dir = tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans"
    _write(plan_dir / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    monkeypatch.setattr(scalp_catalog, "LDM_HYPOTHESIS_PLAN_DIR", plan_dir)
    monkeypatch.setattr(swing_catalog, "LDM_HYPOTHESIS_PLAN_DIR", plan_dir)

    scalp = scalp_catalog.build_policy_catalog({"date": "2026-06-04", "approved_policies": []})
    swing = swing_catalog.build_policy_catalog({"date": "2026-06-04", "active_arm_priority_policies": []})

    assert scalp["hypothesis_observation_plan"]["hypotheses"][0]["hypothesis_id"] == "hyp_1"
    assert swing["hypothesis_observation_plan"]["hypotheses"][0]["hypothesis_id"] == "hyp_1"
