import json

from src.engine.lifecycle.archive import ldm_hypothesis_discovery_readers as mod


def _row(source_date, features, profit, quality="pass", weight=1):
    return mod.SourceRow(
        source="fixture",
        source_date=source_date,
        features=features,
        profit_pct=profit,
        source_quality=quality,
        weight=weight,
    )










def test_missing_rate_cap_excludes_sparse_feature():
    rows = []
    for idx in range(16):
        features = {"entry_score_parent": "S1"}
        if idx < 3:
            features["sparse_alpha"] = "A"
        rows.append(
            _row(f"2026-05-{18 + idx:02d}", features, 1.0 if idx % 2 else -1.0, "pass")
        )

    _, diagnostics = mod._feature_items(rows)

    assert diagnostics["sparse_alpha"]["excluded_reason"] == "missing_rate_cap"




def test_catalog_merge_rejects_invalid_plan_without_writing(tmp_path, monkeypatch):
    swing_dir = tmp_path / "swing"
    swing_dir.mkdir()
    monkeypatch.setattr(mod, "SWING_POLICY_DIR", swing_dir)
    (swing_dir / "swing_sim_policy_catalog_2026-06-01.json").write_text(
        json.dumps({"schema_version": "swing_sim_policy_catalog_v1", "policies": []}),
        encoding="utf-8",
    )
    invalid_plan = {
        "schema_version": mod.OBSERVATION_PLAN_SCHEMA_VERSION,
        "runtime_effect": False,
        "live_runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": mod.FORBIDDEN_USES,
        "hypotheses": [
            "not_a_hypothesis",
            {
                "soft_hypothesis_id": "bad",
                "observable_requirements": [
                    {"field": "submit_quality_parent", "op": "eq", "value": "SQ"}
                ],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": mod.FORBIDDEN_USES,
            },
        ],
        "hypothesis_count": 2,
    }

    result = mod.merge_sim_policy_catalogs("2026-06-01", invalid_plan)

    assert result["swing"]["merged"] is False


def test_retired_current_producer_preserves_prior_and_has_no_authority(tmp_path,monkeypatch):
    import importlib
    current=importlib.import_module('src.engine.automation.ldm_hypothesis_discovery')
    prior=tmp_path/"prior.json";prior.write_text("original")
    def forbidden(*a,**kw):raise AssertionError("retired producer accessed storage")
    monkeypatch.setattr(type(prior),"write_text",forbidden)
    monkeypatch.setattr(type(prior),"read_text",forbidden)
    result=current.build_hypotheses("2026-10-12")
    assert result["status"]=="retired" and result["allowed_runtime_apply"] is False
