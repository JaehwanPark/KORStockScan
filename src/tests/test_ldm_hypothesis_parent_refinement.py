import gzip
import json

from src.engine.automation import ldm_hypothesis_discovery
from src.engine.automation import ldm_hypothesis_parent_refinement as mod


def _plan(hypothesis_id, score, source, ev):
    return {
        "soft_hypothesis_id": hypothesis_id,
        "observable_requirements": [
            {"field": "entry_score_parent", "op": "eq", "value": score},
            {"field": "entry_source_parent", "op": "eq", "value": source},
        ],
        "evidence_summary": {"source_quality_adjusted_ev_pct": ev, "sample_weight": 5},
        "contrast_summary": {
            "contrast_ev_delta_pct": abs(ev),
            "contrast_coverage_status": "ok",
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": ldm_hypothesis_discovery.FORBIDDEN_USES,
    }


def _event(hypothesis_id, score, source, *, profit=0.5, quality="pass", parent_id=""):
    fields = {
        "ldm_hypothesis_matched": "True",
        "ldm_hypothesis_id": hypothesis_id,
        "ldm_hypothesis_candidate_features": json.dumps(
            {"entry_score_parent": score, "entry_source_parent": source}
        ),
        "actual_order_submitted": "False",
        "broker_order_forbidden": "True",
        "source_quality_status": quality,
        "profit_rate": str(profit),
    }
    if parent_id:
        fields["source_parent_bucket_id"] = parent_id
    return {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": "scalp_sim_entry_armed",
        "stock_code": "000001",
        "fields": fields,
    }


def _candidate_event(score, source, *, matched="False", hypothesis_id="", profit=0.5):
    fields = {
        "ldm_hypothesis_matched": matched,
        "ldm_hypothesis_candidate_features": json.dumps(
            {"entry_score_parent": score, "entry_source_parent": source}
        ),
        "source_quality_status": "pass",
        "profit_rate": str(profit),
    }
    if hypothesis_id:
        fields["ldm_hypothesis_id"] = hypothesis_id
    return {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": "blocked_ai_score",
        "stock_code": "000001",
        "fields": fields,
    }


def test_parent_refinement_classifies_support_conflict_gap_and_source_quality(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [
                    _plan("h_support", "S1", "SRC1", 1.2),
                    _plan("h_conflict", "S2", "SRC2", 2.5),
                    _plan("h_gap", "S3", "SRC3", 0.8),
                    _plan("h_sq", "S4", "SRC4", 0.4),
                ],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_support",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC1",
                        },
                    },
                    {
                        "source_parent_bucket_id": "parent_conflict",
                        "parent_source_quality_adjusted_ev_pct": -1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S2",
                            "entry_source_parent": "SRC2",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    events = [
        _event("h_support", "S1", "SRC1", profit=0.8),
        _event("h_support", "S1", "SRC1", profit=0.2),
        _event("h_conflict", "S2", "SRC2", profit=1.5),
        _event("h_conflict", "S2", "SRC2", profit=0.7),
        _event("h_gap", "S3", "SRC3", profit=0.6),
        _event("h_gap", "S3", "SRC3", profit=-0.2),
        _event("h_sq", "S4", "SRC4", profit=0.0, quality="source_quality_blocked"),
        _event("h_sq", "S4", "SRC4", profit=0.0, quality="source_quality_blocked"),
    ]
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        "\n".join(json.dumps(item) for item in events) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")

    classes = {
        item["soft_hypothesis_id"]: item["classification"]
        for item in report["refinement_inputs"]
    }
    assert classes["h_support"] == "parent_support"
    assert classes["h_conflict"] == "parent_conflict"
    assert classes["h_gap"] == "taxonomy_gap_candidate"
    assert classes["h_sq"] == "source_quality_gap"
    assert all(
        item["consumption_required"] is True for item in report["refinement_inputs"]
    )
    assert all(item["runtime_effect"] is False for item in report["refinement_inputs"])
    assert all(
        item["allowed_runtime_apply"] is False for item in report["refinement_inputs"]
    )


def test_parent_refinement_reads_gzip_and_derives_contract_drift_recompute(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-15.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [
                    _plan(
                        "h_derived",
                        "score_watch_recovery",
                        "entry_source_wait6579",
                        1.2,
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-14.json").write_text(
        json.dumps(
            {
                "date": "2026-06-14",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_wait6579",
                        "parent_source_quality_adjusted_ev_pct": 0.8,
                        "dimension_filters": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    event = _candidate_event("score_watch_recovery", "entry_source_wait6579")
    gzip_path = pipeline_dir / "pipeline_events_2026-06-15.jsonl.gz"
    with gzip.open(gzip_path, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")

    report = mod.build_refinement_report("2026-06-15")

    assert report["summary"]["hypothesis_match_count"] == 1
    assert report["summary"]["runtime_hypothesis_match_count"] == 0
    assert report["summary"]["derived_hypothesis_match_count"] == 1
    assert report["summary"]["derived_refinement_input_count"] == 1
    assert report["summary"]["raw_event_mutated"] is False
    item = report["refinement_inputs"][0]
    assert item["soft_hypothesis_id"] == "h_derived"
    assert item["source_match_origin"] == "derived_contract_drift_recompute"
    assert item["derived_from_contract_drift"] is True
    assert item["raw_event_mutated"] is False
    assert item["runtime_match_count"] == 0
    assert item["derived_match_count"] == 1
    assert item["raw_ldm_hypothesis_matched"] == {"false": 1}
    assert item["raw_ldm_hypothesis_id_present"] == {"false": 1}
    assert item["classification"] == "parent_support"
    assert item["runtime_effect"] is False
    assert item["allowed_runtime_apply"] is False
    assert item["actual_order_submitted"] is False
    assert item["broker_order_forbidden"] is True
    assert str(gzip_path) in item["source_event_files"]


def test_parent_refinement_reads_jsonl_and_gzip_when_both_exist(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-15.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [
                    _plan(
                        "h_mixed_files",
                        "score_watch_recovery",
                        "entry_source_wait6579",
                        1.2,
                    )
                ],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-14.json").write_text(
        json.dumps({"date": "2026-06-14", "parent_bucket_summaries": []}),
        encoding="utf-8",
    )
    jsonl_path = pipeline_dir / "pipeline_events_2026-06-15.jsonl"
    gzip_path = pipeline_dir / "pipeline_events_2026-06-15.jsonl.gz"
    jsonl_path.write_text(
        json.dumps(
            _event("h_mixed_files", "score_watch_recovery", "entry_source_wait6579")
        )
        + "\n",
        encoding="utf-8",
    )
    with gzip.open(gzip_path, "wt", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                _candidate_event("score_watch_recovery", "entry_source_wait6579")
            )
            + "\n"
        )

    report = mod.build_refinement_report("2026-06-15")
    item = report["refinement_inputs"][0]

    assert report["summary"]["runtime_hypothesis_match_count"] == 1
    assert report["summary"]["derived_hypothesis_match_count"] == 1
    assert report["summary"]["hypothesis_match_count"] == 2
    assert item["source_match_origin"] == "mixed_runtime_and_derived"
    assert item["runtime_match_count"] == 1
    assert item["derived_match_count"] == 1
    assert set(item["source_event_files"]) == {str(jsonl_path), str(gzip_path)}


def test_parent_refinement_keeps_runtime_origin_for_true_match(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_runtime", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(_event("h_runtime", "S1", "SRC1")) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["source_match_origin"] == "runtime_matched"
    assert item["derived_from_contract_drift"] is False
    assert item["runtime_match_count"] == 1
    assert item["derived_match_count"] == 0


def test_parent_refinement_does_not_derive_without_matching_candidate_features(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-15.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_derived", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-15.jsonl").write_text(
        json.dumps(_candidate_event("S2", "SRC2")) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-15")

    assert report["summary"]["candidate_feature_event_count"] == 1
    assert report["summary"]["derived_hypothesis_match_count"] == 0
    assert report["refinement_inputs"] == []


def test_parent_refinement_surfaces_forbidden_runtime_authority_violation(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_forbidden", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_support",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC1",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    event = _event("h_forbidden", "S1", "SRC1")
    event["fields"]["actual_order_submitted"] = "True"
    event["fields"]["broker_order_forbidden"] = "False"
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(event) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "source_quality_gap"
    assert item["gap_reason"] == "forbidden_runtime_authority_violation"
    assert item["forbidden_contract_violation_count"] == 1
    assert (
        "matched_event_forbidden_runtime_authority_violation"
        in item["pressure_reasons"]
    )


def test_parent_refinement_surfaces_missing_runtime_authority_fields(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_missing_contract", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps({"date": "2026-06-01", "parent_bucket_summaries": []}),
        encoding="utf-8",
    )
    event = _event("h_missing_contract", "S1", "SRC1")
    event["fields"].pop("actual_order_submitted")
    event["fields"].pop("broker_order_forbidden")
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(event) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "source_quality_gap"
    assert item["gap_reason"] == "forbidden_runtime_authority_violation"
    assert item["forbidden_contract_violation_count"] == 1


def test_parent_refinement_surfaces_unknown_hypothesis_id_as_source_quality_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_known", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_support",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC1",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(_event("h_unknown", "S1", "SRC1")) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "source_quality_gap"
    assert item["gap_reason"] == "plan_hypothesis_missing"
    assert item["plan_hypothesis_missing_count"] == 1
    assert item["source_parent_bucket_ids"] == ["parent_support"]
    assert (
        "matched_hypothesis_missing_from_observation_plan" in item["pressure_reasons"]
    )


def test_parent_refinement_does_not_match_parent_from_single_feature_only(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [
                    {
                        **_plan("h_single_feature", "S1", "SRC_IGNORED", 1.2),
                        "observable_requirements": [
                            {"field": "entry_score_parent", "op": "eq", "value": "S1"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_score_only_collision",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC_OTHER",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    event = _event("h_single_feature", "S1", "", profit=0.4)
    event["fields"]["ldm_hypothesis_candidate_features"] = json.dumps(
        {"entry_score_parent": "S1"}
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(event) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "taxonomy_gap_candidate"
    assert item["gap_reason"] == "parent_not_found"
    assert item["source_parent_bucket_ids"] == []


def test_parent_refinement_keeps_unknown_explicit_parent_as_taxonomy_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_unknown_parent", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "known_parent",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S9",
                            "entry_source_parent": "SRC9",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        json.dumps(_event("h_unknown_parent", "S1", "SRC1", parent_id="missing_parent"))
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "taxonomy_gap_candidate"
    assert item["gap_reason"] == "parent_not_found"
    assert item["source_parent_bucket_ids"] == []
    assert item["unmatched_source_parent_bucket_ids"] == ["missing_parent"]


def test_parent_refinement_treats_mixed_known_unknown_parent_ids_as_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)

    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [_plan("h_mixed_parent", "S1", "SRC1", 1.2)],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "known_parent",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC1",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    events = [
        _event("h_mixed_parent", "S1", "SRC1", parent_id="known_parent"),
        _event("h_mixed_parent", "S1", "SRC1", parent_id="missing_parent"),
    ]
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        "\n".join(json.dumps(item) for item in events) + "\n",
        encoding="utf-8",
    )

    report = mod.build_refinement_report("2026-06-02")
    item = report["refinement_inputs"][0]

    assert item["classification"] == "taxonomy_gap_candidate"
    assert item["gap_reason"] == "parent_ambiguous"
    assert item["source_parent_bucket_ids"] == ["known_parent"]
    assert item["unmatched_source_parent_bucket_ids"] == ["missing_parent"]


def test_latest_lifecycle_bucket_report_ignores_future_daily_reports(
    tmp_path, monkeypatch
):
    lifecycle_dir = tmp_path / "lifecycle"
    lifecycle_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps({"date": "2026-06-01", "parent_bucket_summaries": []}),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-03.json").write_text(
        json.dumps(
            {
                "date": "2026-06-03",
                "parent_bucket_summaries": [{"source_parent_bucket_id": "future"}],
            }
        ),
        encoding="utf-8",
    )

    report = mod._latest_lifecycle_bucket_report("2026-06-02")

    assert report["date"] == "2026-06-01"


def test_previous_gap_count_ignores_future_refinement_reports(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    for report_date in ("2026-06-01", "2026-06-03"):
        report_dir.joinpath(
            f"ldm_hypothesis_parent_refinement_{report_date}.json"
        ).write_text(
            json.dumps(
                {
                    "date": report_date,
                    "refinement_inputs": [
                        {
                            "soft_hypothesis_id": "h_gap",
                            "classification": "taxonomy_gap_candidate",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    assert mod._previous_gap_count("h_gap", "2026-06-02") == 1


def test_repeated_needs_opposite_sample_gets_opposite_absence_diagnosis(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    pipeline_dir = tmp_path / "pipeline"
    plan_dir = tmp_path / "plans"
    lifecycle_dir = tmp_path / "lifecycle"
    for path in (report_dir, pipeline_dir, plan_dir, lifecycle_dir):
        path.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "LDM_PLAN_DIR", plan_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_BUCKET_DIR", lifecycle_dir)
    for report_date in ("2026-05-29", "2026-06-01"):
        report_dir.joinpath(
            f"ldm_hypothesis_parent_refinement_{report_date}.json"
        ).write_text(
            json.dumps(
                {
                    "date": report_date,
                    "refinement_inputs": [
                        {
                            "soft_hypothesis_id": "h_opposite",
                            "classification": "parent_support",
                            "contrary_sample_need": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
    plan_dir.joinpath("ldm_hypothesis_observation_plan_2026-06-02.json").write_text(
        json.dumps(
            {
                "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
                "hypotheses": [
                    {
                        **_plan("h_opposite", "S1", "SRC1", 1.2),
                        "contrast_summary": {
                            "contrast_ev_delta_pct": 1.2,
                            "contrast_coverage_status": "needs_opposite_sample",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    lifecycle_dir.joinpath("lifecycle_bucket_discovery_2026-06-01.json").write_text(
        json.dumps(
            {
                "date": "2026-06-01",
                "parent_bucket_summaries": [
                    {
                        "source_parent_bucket_id": "parent_support",
                        "parent_source_quality_adjusted_ev_pct": 1.0,
                        "dimension_filters": {
                            "entry_score_parent": "S1",
                            "entry_source_parent": "SRC1",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    pipeline_dir.joinpath("pipeline_events_2026-06-02.jsonl").write_text(
        "\n".join(
            json.dumps(_event("h_opposite", "S1", "SRC1", profit=0.2)) for _ in range(3)
        )
        + "\n",
        encoding="utf-8",
    )

    item = mod.build_refinement_report("2026-06-02")["refinement_inputs"][0]

    assert item["diagnosed_status"] == "parent_support_but_no_contrast"
    assert item["retry_count"] == 2
    assert (
        item["opposite_sample_absence_diagnosis"]["diagnosed_status"]
        == "parent_support_but_no_contrast"
    )
    assert item["recommended_closure_bias"] == "absorbed_into_existing_parent"


def test_repeated_taxonomy_source_quality_parent_conflict_and_fragile_diagnoses():
    source_quality = mod.HypothesisAggregate(
        hypothesis_id="h_sq",
        match_count=5,
        source_quality_blocked_count=5,
    )
    taxonomy = mod.HypothesisAggregate(
        hypothesis_id="h_tax", match_count=5, candidate_features={"x": "y"}
    )
    conflict = mod.HypothesisAggregate(hypothesis_id="h_conflict", match_count=5)
    fragile = mod.HypothesisAggregate(hypothesis_id="h_fragile", match_count=1)

    sq_diag = mod._diagnose_repeated_status(
        classification="source_quality_gap",
        gap_reason="source_quality_blocked",
        contrary_needed=False,
        aggregate=source_quality,
        parent_ids=[],
        previous_counts=mod.Counter({"source_quality_gap": 2}),
    )
    tax_diag = mod._diagnose_repeated_status(
        classification="taxonomy_gap_candidate",
        gap_reason="parent_not_found",
        contrary_needed=False,
        aggregate=taxonomy,
        parent_ids=[],
        previous_counts=mod.Counter({"taxonomy_gap_candidate": 2}),
    )
    conflict_diag = mod._diagnose_repeated_status(
        classification="parent_conflict",
        gap_reason="",
        contrary_needed=False,
        aggregate=conflict,
        parent_ids=["parent"],
        previous_counts=mod.Counter({"parent_conflict": 2}),
    )
    fragile_diag = mod._diagnose_repeated_status(
        classification="parent_support",
        gap_reason="",
        contrary_needed=True,
        aggregate=fragile,
        parent_ids=[],
        previous_counts=mod.Counter({"needs_opposite_sample": 2}),
    )
    repeated_fragile_diag = mod._diagnose_repeated_status(
        classification="parent_support",
        gap_reason="",
        contrary_needed=False,
        aggregate=fragile,
        parent_ids=[],
        previous_counts=mod.Counter({"rejected_as_fragile": 2}),
    )

    assert sq_diag["recommended_closure_bias"] == "source_quality_gap_created"
    assert tax_diag["diagnosed_status"] == "taxonomy_gap_candidate"
    assert tax_diag["recommended_closure_bias"] == "new_parent_candidate_created"
    assert (
        conflict_diag["recommended_closure_bias"]
        == "parent_refinement_candidate_created"
    )
    assert fragile_diag["recommended_closure_bias"] == "rejected_as_fragile"
    assert repeated_fragile_diag["diagnosed_status"] == "rejected_as_fragile"
    assert repeated_fragile_diag["retry_count"] == 2
