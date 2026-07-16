import json

from src.engine.automation import ldm_hypothesis_discovery as mod


def _row(source_date, features, profit, quality="pass", weight=1):
    return mod.SourceRow(
        source="fixture",
        source_date=source_date,
        features=features,
        profit_pct=profit,
        source_quality=quality,
        weight=weight,
    )


def test_deterministic_hypothesis_generation_excludes_future_identity_and_pnl_fields():
    rows = [
        _row(
            "2026-05-18",
            {
                "alpha": "A",
                "entry_score_parent": "S1",
                "beta": "B",
                "record_id": "1",
                "profit_rate": 3.0,
            },
            2.0,
        ),
        _row(
            "2026-05-19",
            {
                "alpha": "A",
                "entry_score_parent": "S1",
                "beta": "B",
                "stock_code": "000001",
                "future_label": "x",
            },
            1.0,
        ),
        _row(
            "2026-05-20",
            {"alpha": "A", "entry_score_parent": "S1", "beta": "C", "raw_score": 10},
            -1.0,
        ),
        _row(
            "2026-05-21",
            {"alpha": "D", "entry_score_parent": "S2", "beta": "B", "raw_score": 20},
            -3.0,
        ),
        _row(
            "2026-05-22",
            {"alpha": "A", "entry_score_parent": "S1", "beta": "B", "raw_score": 30},
            None,
            "source_quality_blocked",
        ),
    ]

    hypotheses, diagnostics = mod.build_hypotheses(rows)

    assert diagnostics["candidate_count"] > 0
    assert hypotheses
    all_requirements = [
        requirement
        for hypothesis in hypotheses
        for requirement in hypothesis["observable_requirements"]
    ]
    forbidden_fields = {
        item["field"]
        for item in all_requirements
        if item["field"] in {"record_id", "stock_code", "profit_rate", "future_label"}
    }
    assert forbidden_fields == set()
    itemsets, feature_diagnostics = mod._feature_items(rows)
    assert feature_diagnostics["raw_score"]["numeric"] is True
    assert any("raw_score#bin=" in item for itemset in itemsets for item in itemset)
    assert all(hypothesis["runtime_effect"] is False for hypothesis in hypotheses)
    assert all(
        hypothesis["allowed_runtime_apply"] is False for hypothesis in hypotheses
    )
    assert all(
        hypothesis["broker_order_forbidden"] is True for hypothesis in hypotheses
    )


def test_missing_source_quality_is_preserved_as_contrast_group():
    rows = [
        _row(
            "2026-05-18", {"alpha": "A", "entry_source_parent": "SRC1"}, 1.0, "pass", 3
        ),
        _row(
            "2026-05-19",
            {"alpha": "A", "entry_source_parent": "SRC1"},
            None,
            "source_quality_blocked",
            3,
        ),
        _row(
            "2026-05-20", {"alpha": "B", "entry_source_parent": "SRC2"}, -1.0, "pass", 3
        ),
    ]

    hypotheses, _ = mod.build_hypotheses(rows)

    assert hypotheses
    assert any(
        "source_quality_blocked" in hypothesis["contrast_summary"]["group_counts"]
        for hypothesis in hypotheses
    )


def test_runtime_observable_single_contrast_group_collects_opposite_sample():
    rows = [
        _row(
            "2026-05-18",
            {"entry_score_parent": "S1", "entry_source_parent": "SRC1"},
            1.0,
            "pass",
            3,
        ),
        _row(
            "2026-05-19",
            {"entry_score_parent": "S1", "entry_source_parent": "SRC1"},
            0.8,
            "pass",
            3,
        ),
        _row(
            "2026-05-20",
            {"entry_score_parent": "S2", "entry_source_parent": "SRC2"},
            -1.0,
            "pass",
            3,
        ),
    ]

    hypotheses, _ = mod.build_hypotheses(rows)

    single_group = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis["contrast_summary"]["contrast_coverage_status"]
        == "needs_opposite_sample"
    ]
    assert single_group
    assert all(
        hypothesis["observation_budget_hint"]["priority"] == "collect_contrary_sample"
        for hypothesis in single_group
    )


def test_post_arm_dimensions_are_not_catalog_match_requirements():
    rows = [
        _row(
            "2026-05-18",
            {
                "entry_score_parent": "S1",
                "entry_source_parent": "SRC1",
                "submit_quality_parent": "SQ1",
            },
            1.0,
            "pass",
            3,
        ),
        _row(
            "2026-05-19",
            {
                "entry_score_parent": "S1",
                "entry_source_parent": "SRC1",
                "submit_quality_parent": "SQ1",
            },
            -1.0,
            "pass",
            3,
        ),
        _row(
            "2026-05-20",
            {
                "entry_score_parent": "S2",
                "entry_source_parent": "SRC2",
                "submit_quality_parent": "SQ2",
            },
            0.0,
            "pass",
            3,
        ),
    ]

    hypotheses, _ = mod.build_hypotheses(rows)

    assert hypotheses
    assert all(
        requirement["field"] in mod.ARMING_OBSERVABLE_REQUIREMENT_FIELDS
        for hypothesis in hypotheses
        for requirement in hypothesis["observable_requirements"]
    )
    assert any(
        dimension["field"] == "submit_quality_parent"
        for hypothesis in hypotheses
        for dimension in hypothesis["observation_dimensions"]
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


def test_catalog_merge_preserves_existing_policy_sections(tmp_path, monkeypatch):
    catalog_dir = tmp_path / "scalp"
    swing_dir = tmp_path / "swing"
    catalog_dir.mkdir()
    swing_dir.mkdir()
    monkeypatch.setattr(mod, "SCALP_POLICY_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SWING_POLICY_DIR", swing_dir)
    (catalog_dir / "scalp_sim_policy_catalog_2026-06-01.json").write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [{"policy_id": "keep"}],
                "active_sim_priority_seeds": [{"active_seed_id": "seed"}],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_sim_policy_catalog_2026-06-01.json").write_text(
        json.dumps(
            {
                "schema_version": "swing_sim_policy_catalog_v1",
                "policies": [{"policy_id": "keep"}],
                "active_arm_priority_policies": [{"priority_policy_id": "arm"}],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01",
        "hypotheses": [
            {
                "soft_hypothesis_id": "h1",
                "observable_requirements": [
                    {"field": "entry_score_parent", "op": "eq", "value": "S1"}
                ],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": mod.FORBIDDEN_USES,
            }
        ],
    }
    plan = mod.build_observation_plan(report, "2026-06-02")

    result = mod.merge_sim_policy_catalogs("2026-06-01", plan)

    assert result["scalp"]["merged"] is True
    assert result["swing"]["merged"] is True
    scalp = json.loads(
        (catalog_dir / "scalp_sim_policy_catalog_2026-06-01.json").read_text()
    )
    swing = json.loads(
        (swing_dir / "swing_sim_policy_catalog_2026-06-01.json").read_text()
    )
    assert scalp["policies"] == [{"policy_id": "keep"}]
    assert scalp["active_sim_priority_seeds"] == [{"active_seed_id": "seed"}]
    assert (
        scalp["hypothesis_observation_plan"]["schema_version"]
        == mod.OBSERVATION_PLAN_SCHEMA_VERSION
    )
    assert swing["active_arm_priority_policies"] == [{"priority_policy_id": "arm"}]


def test_catalog_merge_rejects_invalid_plan_without_writing(tmp_path, monkeypatch):
    catalog_dir = tmp_path / "scalp"
    swing_dir = tmp_path / "swing"
    catalog_dir.mkdir()
    swing_dir.mkdir()
    monkeypatch.setattr(mod, "SCALP_POLICY_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SWING_POLICY_DIR", swing_dir)
    original = {
        "schema_version": "scalp_sim_policy_catalog_v1",
        "policies": [{"policy_id": "keep"}],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (catalog_dir / "scalp_sim_policy_catalog_2026-06-01.json").write_text(
        json.dumps(original),
        encoding="utf-8",
    )
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

    assert result["scalp"]["merged"] is False
    assert result["swing"]["merged"] is False
    scalp = json.loads(
        (catalog_dir / "scalp_sim_policy_catalog_2026-06-01.json").read_text()
    )
    assert scalp == original
