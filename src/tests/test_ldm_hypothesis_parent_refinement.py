import gzip
import json

from src.engine.automation import ldm_hypothesis_discovery
from src.engine.lifecycle.archive import ldm_hypothesis_parent_refinement_readers as mod


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


def test_retired_current_producer_preserves_prior_and_has_no_authority(tmp_path,monkeypatch):
    import importlib
    current=importlib.import_module('src.engine.automation.ldm_hypothesis_discovery')
    prior=tmp_path/"prior.json";prior.write_text("original")
    def forbidden(*a,**kw):raise AssertionError("retired producer accessed storage")
    monkeypatch.setattr(type(prior),"write_text",forbidden)
    monkeypatch.setattr(type(prior),"read_text",forbidden)
    result=current.build_hypotheses("2026-10-12")
    assert result["status"]=="retired" and result["allowed_runtime_apply"] is False
