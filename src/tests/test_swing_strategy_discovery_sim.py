import json
import os

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import SwingStrategyDiscoveryArm, SwingStrategyDiscoveryCandidate, SwingStrategyDiscoveryLabel
from src.engine import swing_strategy_discovery_sim as mod
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema


def _external_test_db_url() -> str:
    db_url = os.getenv("KORSTOCKSCAN_TEST_DATABASE_URL", "").strip()
    if not db_url:
        pytest.skip("set KORSTOCKSCAN_TEST_DATABASE_URL to run DB-backed discovery sim tests")
    if "test" not in db_url.lower():
        pytest.skip("KORSTOCKSCAN_TEST_DATABASE_URL must point to an isolated test database")
    return db_url


def _setup_test_db():
    db_url = _external_test_db_url()
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(SwingStrategyDiscoveryLabel.__table__.delete())
        conn.execute(SwingStrategyDiscoveryArm.__table__.delete())
        conn.execute(SwingStrategyDiscoveryCandidate.__table__.delete())
    return db_url, engine, sessionmaker(bind=engine)


def _source_rows(count=10):
    rows = []
    for idx in range(1, count + 1):
        rows.append(
            {
                "date": "2026-05-19",
                "code": f"{idx:06d}",
                "name": f"종목{idx}",
                "hybrid_mean": 0.35 + idx * 0.02,
                "prob": 0.35 + idx * 0.02,
                "floor_used": 0.10,
                "score_rank": idx,
                "selection_mode": "DIAGNOSTIC_ONLY",
                "meta_score": 50 + idx,
                "sector": f"sector-{idx % 3}",
                "industry": f"industry-{idx % 2}",
                "theme_tags": [f"theme-{idx % 4}"],
            }
        )
    rows[-1]["selection_mode"] = "SELECTED"
    rows[-1]["score_rank"] = 99
    rows[-1]["hybrid_mean"] = 0.12
    rows[-1]["prob"] = 0.12
    return pd.DataFrame(rows)


def _quote_features(count=10):
    position_cycle = ["BREAKOUT", "MIDDLE", "BOTTOM"]
    vol_cycle = ["mid", "high", "low"]
    return {
        f"{idx:06d}": {
            "stock_name": f"종목{idx}",
            "reference_price": 10_000 + idx * 100,
            "position_tag": position_cycle[idx % len(position_cycle)],
            "position_ratio_60d": 0.2 + idx * 0.05,
            "volatility_20d_pct": 1.0 + idx * 0.2,
            "volatility_bucket": vol_cycle[idx % len(vol_cycle)],
            "marcap": 100_000_000_000 + idx,
            "volume": 1_000_000 + idx,
        }
        for idx in range(1, count + 1)
    }


def test_build_candidate_and_arm_rows_keep_sim_only_contract():
    source_rows = _source_rows()
    candidates = mod.build_candidate_rows(
        source_rows,
        target_date="2026-05-19",
        max_candidates=10,
        block_reasons={
            "000001": "blocked_gatekeeper_reject",
            "000002": "blocked_swing_score_vpw",
            "000003": "blocked_swing_gap",
        },
        quote_features=_quote_features(),
    )
    arms = mod.build_arm_rows(candidates, virtual_budget_krw=10_000_000)

    assert len(candidates) == 10
    assert len(arms) == len(candidates) * len(mod.ARM_SET)
    assert {row["selection_arm"] for row in candidates} >= {"lifecycle_rank", "diversity_exploration"}
    assert all(row["decision_authority"] == "swing_sim_exploration_only" for row in candidates)
    assert all(row["actual_order_submitted"] is False for row in candidates)
    assert all(row["broker_order_forbidden"] is True for row in candidates)
    assert all(row["runtime_effect"] is False for row in candidates)
    assert all(row["actual_order_submitted"] is False for row in arms)
    assert all(row["broker_order_forbidden"] is True for row in arms)
    assert all(row["runtime_effect"] is False for row in arms)
    assert all(row["allowed_runtime_apply"] is False for row in arms)
    assert all(row["arm_features"]["allowed_runtime_apply"] is False for row in arms)
    assert all("legacy_ml_role" in row["source_features"] for row in candidates)
    assert all(row["sector"] for row in candidates)
    assert all(row["theme_tags"] for row in candidates)


def test_active_arm_priority_tags_matching_arm_without_duplication():
    candidates = mod.build_candidate_rows(
        _source_rows(3),
        target_date="2026-06-01",
        max_candidates=3,
        block_reasons={},
        quote_features=_quote_features(3),
    )
    arms = mod.build_arm_rows(
        candidates,
        virtual_budget_krw=10_000_000,
        active_arm_priority_policies={
            "arm05_breakout_conf_trailing": {
                "priority_policy_id": "priority_arm05",
                "priority_arm_id": "arm05_breakout_conf_trailing",
                "status": "active",
                "priority_source": "surviving_arms",
                "source_report_date": "2026-06-01",
            }
        },
    )

    assert len(arms) == len(candidates) * len(mod.ARM_SET)
    priority_rows = [row for row in arms if row.get("swing_active_arm_priority")]
    assert len(priority_rows) == len(candidates)
    assert {row["arm_id"] for row in priority_rows} == {"arm05_breakout_conf_trailing"}
    assert {row["priority_policy_id"] for row in priority_rows} == {"priority_arm05"}
    assert all(row["arm_features"]["swing_active_arm_priority"] is True for row in priority_rows)
    assert all(row["actual_order_submitted"] is False for row in priority_rows)
    assert all(row["broker_order_forbidden"] is True for row in priority_rows)
    assert all(row["runtime_effect"] is False for row in priority_rows)


def test_active_arm_priority_raises_default_cap_but_explicit_cap_wins(tmp_path, monkeypatch):
    policy_file = tmp_path / "swing_sim_policy_catalog_2026-06-01.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "swing_sim_policy_catalog_v1",
                "active_arm_priority_policies": [
                    {
                        "priority_policy_id": "priority_arm05",
                        "priority_arm_id": "arm05_breakout_conf_trailing",
                        "status": "active",
                        "source_report_date": "2026-06-01",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: _source_rows(70))
    monkeypatch.setattr(mod, "load_block_reason_map", lambda target_date: {})
    monkeypatch.setattr(mod, "fetch_quote_features", lambda codes, db_url=mod.POSTGRES_URL: _quote_features(70))
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": len(list(codes)),
            "rows_by_code": {
                f"{idx:06d}": {
                    "sector": f"sector-{idx % 3}",
                    "industry": f"industry-{idx % 2}",
                    "theme_tags": [f"theme-{idx % 4}"],
                    "theme_source": "test",
                    "theme_source_quality": "ok",
                }
                for idx in range(1, 71)
            },
            "warnings": [],
        },
    )

    report = mod.build_swing_strategy_discovery_report(
        "2026-06-01",
        persist=False,
        swing_sim_policy_file=policy_file,
    )
    explicit = mod.build_swing_strategy_discovery_report(
        "2026-06-01",
        max_candidates=5,
        persist=False,
        swing_sim_policy_file=policy_file,
    )

    assert report["summary"]["effective_max_daily_candidates"] == 80
    assert report["summary"]["candidate_count"] == 70
    assert report["summary"]["active_arm_priority_policy_count"] == 1
    assert explicit["summary"]["effective_max_daily_candidates"] == 5
    assert explicit["summary"]["candidate_count"] == 5


def test_active_bucket_priority_raises_default_cap_without_arm_duplication(tmp_path, monkeypatch):
    policy_file = tmp_path / "swing_sim_policy_catalog_2026-06-01.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "swing_sim_policy_catalog_v1",
                "active_arm_priority_policies": [
                    {
                        "priority_policy_id": "priority_bucket_entry",
                        "priority_bucket_id": "swing_bucket_entry_combo_probe",
                        "status": "active",
                        "source_report_date": "2026-06-01",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: _source_rows(70))
    monkeypatch.setattr(mod, "load_block_reason_map", lambda target_date: {})
    monkeypatch.setattr(mod, "fetch_quote_features", lambda codes, db_url=mod.POSTGRES_URL: _quote_features(70))
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": len(list(codes)),
            "rows_by_code": {
                f"{idx:06d}": {
                    "sector": f"sector-{idx % 3}",
                    "industry": f"industry-{idx % 2}",
                    "theme_tags": [f"theme-{idx % 4}"],
                    "theme_source": "test",
                    "theme_source_quality": "ok",
                }
                for idx in range(1, 71)
            },
            "warnings": [],
        },
    )

    report = mod.build_swing_strategy_discovery_report(
        "2026-06-01",
        persist=False,
        swing_sim_policy_file=policy_file,
    )

    assert report["summary"]["effective_max_daily_candidates"] == 80
    assert report["summary"]["candidate_count"] == 70
    assert report["summary"]["active_arm_priority_policy_count"] == 1
    assert report["summary"]["active_arm_priority_arm_count"] == 0


def test_schema_report_and_persistence_are_idempotent(tmp_path, monkeypatch):
    db_url, _engine, Session = _setup_test_db()
    output_dir = tmp_path / "report"

    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: _source_rows(6))
    monkeypatch.setattr(
        mod,
        "load_block_reason_map",
        lambda target_date: {
            "000001": "blocked_gatekeeper_reject",
            "000002": "blocked_swing_gap",
        },
    )
    monkeypatch.setattr(mod, "fetch_quote_features", lambda codes, db_url=mod.POSTGRES_URL: _quote_features(6))
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": len(list(codes)),
            "rows_by_code": {
                f"{idx:06d}": {
                    "sector": f"sector-{idx % 3}",
                    "industry": f"industry-{idx % 2}",
                    "theme_tags": [f"theme-{idx % 4}"],
                    "theme_source": "test",
                    "theme_source_quality": "ok",
                }
                for idx in range(1, 7)
            },
            "warnings": [],
        },
    )

    paths = mod.write_swing_strategy_discovery_report(
        "2026-05-19",
        db_url=db_url,
        output_dir=output_dir,
        max_candidates=6,
        persist=True,
    )

    report = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert report["runtime_effect"] is False
    assert report["decision_authority"] == "swing_sim_exploration_only"
    assert report["summary"]["candidate_count"] == 6
    assert report["summary"]["arm_count"] == 6 * len(mod.ARM_SET)
    assert report["persist_summary"] == {"candidate_rows": 6, "arm_rows": 6 * len(mod.ARM_SET)}
    assert report["source_quality"]["quote_feature_coverage"] == 1.0
    assert report["warnings"] == []
    assert "broker_order_submit" in report["forbidden_uses"]
    assert paths["md"].exists()

    with Session() as session:
        assert session.query(SwingStrategyDiscoveryCandidate).count() == 6
        assert session.query(SwingStrategyDiscoveryArm).count() == 6 * len(mod.ARM_SET)

    second = mod.write_swing_strategy_discovery_report(
        "2026-05-19",
        db_url=db_url,
        output_dir=output_dir,
        max_candidates=6,
        persist=True,
    )
    assert second["json"] == paths["json"]
    with Session() as session:
        assert session.query(SwingStrategyDiscoveryCandidate).count() == 6
        assert session.query(SwingStrategyDiscoveryArm).count() == 6 * len(mod.ARM_SET)


def test_fetch_quote_features_passes_sql_lookback_limit(monkeypatch):
    captured = {}

    def fake_read_sql(query, engine, params=None):
        captured["sql"] = str(query)
        captured["params"] = dict(params or {})
        return pd.DataFrame(
            [
                {
                    "quote_date": "2026-05-20",
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "open_price": 1,
                    "high_price": 2,
                    "low_price": 1,
                    "close_price": 2,
                    "volume": 10,
                    "marcap": 100,
                    "daily_return": 1.0,
                }
            ]
        )

    monkeypatch.setattr(mod, "create_engine", lambda db_url: object())
    monkeypatch.setattr(mod.pd, "read_sql", fake_read_sql)

    result = mod.fetch_quote_features(["005930"], db_url=mod.POSTGRES_URL, lookback=7)

    assert "ROW_NUMBER() OVER" in captured["sql"]
    assert captured["params"]["lookback"] == 7
    assert result["005930"]["stock_name"] == "삼성전자"


def test_partial_sector_theme_missing_stays_source_quality_summary(monkeypatch):
    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: _source_rows(3))
    monkeypatch.setattr(mod, "load_block_reason_map", lambda target_date: {})
    monkeypatch.setattr(mod, "fetch_quote_features", lambda codes, db_url=mod.POSTGRES_URL: _quote_features(3))
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": 2,
            "missing_count": 1,
            "sector_mapped_count": 2,
            "sector_missing_count": 1,
            "theme_mapped_count": 1,
            "theme_missing_count": 2,
            "rows_by_code": {
                "000001": {
                    "sector": "sector-1",
                    "industry": "industry-1",
                    "theme_tags": ["theme-1"],
                    "theme_source": "test",
                    "theme_source_quality": "ok",
                },
                "000002": {
                    "sector": "sector-2",
                    "industry": "industry-2",
                    "theme_tags": [],
                    "theme_source": "missing",
                    "theme_source_quality": "missing",
                },
            },
            "warnings": [],
        },
    )

    report = mod.build_swing_strategy_discovery_report("2026-05-22", db_url=mod.POSTGRES_URL, max_candidates=3, persist=False)

    assert report["warnings"] == []
    assert report["source_quality"]["sector_theme_mapped_rows"] == 2
    assert report["source_quality"]["sector_theme_missing_rows"] == 1
    assert report["source_quality"]["sector_theme_coverage"] == 0.666667
    assert report["source_quality"]["sector_missing_rows"] == 1
    assert report["source_quality"]["theme_missing_rows"] == 2


def test_discovery_can_include_bottom_rebound_source_without_runtime_authority(tmp_path, monkeypatch):
    source_path = tmp_path / "swing_bottom_rebound_candidate_source_2026-05-22.json"
    source_path.write_text(
        json.dumps(
            {
                "report_type": "swing_bottom_rebound_candidate_source",
                "date": "2026-05-22",
                "policy_version": "bottom_rebound_swing_source_v1",
                "decision_authority": "swing_sim_candidate_source_only",
                "runtime_effect": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
                "candidate_rows": [
                    {
                        "candidate_id": "br:2026-05-22:000101",
                        "stock_code": "000101",
                        "stock_name": "BottomOnly",
                        "candidate_rank": 1,
                        "lifecycle_exploration_score": 5.5,
                        "source_quality_adjusted_ev_pct": 1.2,
                        "recommended_sim_entry_policy": "atr_pullback_entry",
                        "diagnostic_features": {
                            "kiwoom_sector": "Software",
                            "kiwoom_theme_tags": ["AI"],
                        },
                        "source_features": {"source_primary_adjusted_ev_pct": 1.2},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: pd.DataFrame())
    monkeypatch.setattr(mod, "load_block_reason_map", lambda target_date: {})
    monkeypatch.setattr(
        mod,
        "fetch_quote_features",
        lambda codes, db_url=mod.POSTGRES_URL: {
            "000101": {
                "stock_name": "BottomOnly",
                "reference_price": 1000,
                "position_tag": "BOTTOM",
                "position_ratio_60d": 0.1,
                "volatility_20d_pct": 2.0,
                "volatility_bucket": "mid",
                "marcap": 10_000_000_000,
                "volume": 100000,
            }
        },
    )
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": 1,
            "rows_by_code": {
                "000101": {
                    "sector": "Software",
                    "industry": "Software",
                    "theme_tags": ["AI"],
                    "theme_source": "test",
                    "theme_source_quality": "ok",
                }
            },
            "warnings": [],
        },
    )

    report = mod.build_swing_strategy_discovery_report(
        "2026-05-22",
        db_url=mod.POSTGRES_URL,
        max_candidates=3,
        persist=False,
        include_bottom_rebound_source=True,
        bottom_rebound_source_path=source_path,
    )

    assert report["summary"]["candidate_count"] == 1
    assert report["source_quality"]["safe_pool_source_rows"] == 0
    assert report["source_quality"]["bottom_rebound_source_rows"] == 1
    assert report["source_quality"]["combined_source_rows"] == 1
    assert report["source_quality"]["bottom_rebound_source"]["status"] == "ok"
    assert "safe_pool_empty_bottom_rebound_source_used" in report["warnings"]
    example = report["examples"][0]
    assert example["stock_code"] == "000101"
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["arm_count"] == len(mod.BOTTOM_REBOUND_ARM_SET)
    assert set(report["summary"]["arm_policy_counts"]) == {item["arm_id"] for item in mod.BOTTOM_REBOUND_ARM_SET}
    assert report["summary"]["source_family_bucket_counts"] == {"bottom_rebound": 1}
    assert report["summary"]["bottom_rebound_selected_candidate_count"] == 1
    assert report["summary"]["bottom_rebound_arm_count"] == len(mod.BOTTOM_REBOUND_ARM_SET)
    assert report["bottom_rebound_arm_set"] == mod.BOTTOM_REBOUND_ARM_SET
    assert report["examples"][0]["bottom_rebound_source"]["present"] is True
    assert report["examples"][0]["source_family_bucket"] == "bottom_rebound"


def test_bottom_rebound_source_persists_candidate_and_dedicated_arms(tmp_path, monkeypatch):
    db_url, _engine, Session = _setup_test_db()
    source_path = tmp_path / "swing_bottom_rebound_candidate_source_2026-05-22.json"
    source_path.write_text(
        json.dumps(
            {
                "report_type": "swing_bottom_rebound_candidate_source",
                "date": "2026-05-22",
                "decision_authority": "swing_sim_candidate_source_only",
                "runtime_effect": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
                "candidate_rows": [
                    {
                        "candidate_id": "br:2026-05-22:000101",
                        "stock_code": "000101",
                        "stock_name": "BottomOnly",
                        "candidate_rank": 1,
                        "lifecycle_exploration_score": 5.5,
                        "source_quality_adjusted_ev_pct": 1.2,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "load_safe_pool_rows", lambda target_date: pd.DataFrame())
    monkeypatch.setattr(mod, "load_block_reason_map", lambda target_date: {})
    monkeypatch.setattr(
        mod,
        "fetch_quote_features",
        lambda codes, db_url=mod.POSTGRES_URL: {
            "000101": {
                "stock_name": "BottomOnly",
                "reference_price": 1000,
                "position_tag": "BOTTOM",
                "position_ratio_60d": 0.1,
                "volatility_20d_pct": 2.0,
                "volatility_bucket": "mid",
                "marcap": 10_000_000_000,
                "volume": 100000,
            }
        },
    )
    monkeypatch.setattr(
        mod,
        "build_sector_theme_map",
        lambda codes, target_date, allow_external=True: {
            "mapped_code_count": 1,
            "rows_by_code": {},
            "warnings": [],
        },
    )

    report = mod.build_swing_strategy_discovery_report(
        "2026-05-22",
        db_url=db_url,
        max_candidates=3,
        persist=True,
        include_bottom_rebound_source=True,
        bottom_rebound_source_path=source_path,
    )

    assert report["persist_summary"] == {
        "candidate_rows": 1,
        "arm_rows": len(mod.BOTTOM_REBOUND_ARM_SET),
    }
    assert report["summary"]["bottom_rebound_persisted_candidate_count"] == 1
    assert report["summary"]["bottom_rebound_persisted_arm_count"] == len(mod.BOTTOM_REBOUND_ARM_SET)
    with Session() as session:
        candidate = session.query(SwingStrategyDiscoveryCandidate).one()
        arms = session.query(SwingStrategyDiscoveryArm).all()
        source_features = json.loads(candidate.source_features)
        assert source_features["bottom_rebound_source"]["present"] is True
        assert source_features["source_family_bucket"] == "bottom_rebound"
        assert {arm.arm_id for arm in arms} == {item["arm_id"] for item in mod.BOTTOM_REBOUND_ARM_SET}
        assert all(arm.actual_order_submitted is False for arm in arms)
        assert all(arm.broker_order_forbidden is True for arm in arms)
        assert all(arm.runtime_effect is False for arm in arms)


def test_safe_pool_nan_bottom_metadata_is_not_bottom_candidate():
    safe_rows = pd.DataFrame(
        [
            {
                "date": "2026-05-22",
                "code": "000001",
                "name": "SafeOnly",
                "hybrid_mean": 0.8,
                "prob": 0.8,
                "score_rank": 1,
                "selection_mode": "SELECTED",
            }
        ]
    )
    bottom_rows = pd.DataFrame(
        [
            {
                "date": "2026-05-22",
                "code": "000002",
                "name": "BottomOnly",
                "hybrid_mean": 0.9,
                "prob": 0.9,
                "score_rank": 1,
                "selection_mode": "BOTTOM_REBOUND_SOURCE",
                "bottom_rebound_source_present": True,
                "bottom_rebound_candidate_id": "br:2026-05-22:000002",
            }
        ]
    )
    merged = mod.merge_optional_source_rows(safe_rows, bottom_rows)

    candidates = mod.build_candidate_rows(
        merged,
        target_date="2026-05-22",
        max_candidates=2,
        quote_features=_quote_features(2),
    )
    by_code = {row["stock_code"]: row for row in candidates}
    assert by_code["000001"]["source_family_bucket"] == "safe_pool"
    assert by_code["000001"]["source_features"]["bottom_rebound_source"]["present"] is False
    assert by_code["000002"]["source_family_bucket"] == "bottom_rebound"
    arms = mod.build_arm_rows(candidates)
    safe_arms = [row for row in arms if row["stock_code"] == "000001"]
    bottom_arms = [row for row in arms if row["stock_code"] == "000002"]
    assert len(safe_arms) == len(mod.ARM_SET)
    assert len(bottom_arms) == len(mod.BOTTOM_REBOUND_ARM_SET)


def test_bottom_rebound_overlap_preserves_metadata_and_dedicated_arms():
    safe_rows = _source_rows(1)
    bottom_rows = pd.DataFrame(
        [
            {
                "date": "2026-05-22",
                "code": "000001",
                "name": "Overlap",
                "hybrid_mean": 0.9,
                "prob": 0.9,
                "score_rank": 1,
                "selection_mode": "BOTTOM_REBOUND_SOURCE",
                "bottom_rebound_source_present": True,
                "bottom_rebound_candidate_id": "br:2026-05-22:000001",
                "bottom_rebound_candidate_rank": 1,
            }
        ]
    )
    merged = mod.merge_optional_source_rows(safe_rows, bottom_rows)
    candidates = mod.build_candidate_rows(
        merged,
        target_date="2026-05-22",
        max_candidates=1,
        quote_features=_quote_features(1),
    )
    assert candidates[0]["stock_code"] == "000001"
    assert candidates[0]["source_family_bucket"] == "bottom_rebound"
    assert candidates[0]["source_features"]["bottom_rebound_source"]["present"] is True
    assert candidates[0]["source_features"]["bottom_rebound_source"]["candidate_id"] == "br:2026-05-22:000001"
    arms = mod.build_arm_rows(candidates)
    assert [row["arm_id"] for row in arms] == [item["arm_id"] for item in mod.BOTTOM_REBOUND_ARM_SET]


def test_bottom_rebound_source_contract_must_be_source_only(tmp_path):
    source_path = tmp_path / "bad_source.json"
    source_path.write_text(
        json.dumps(
            {
                "decision_authority": "swing_sim_candidate_source_only",
                "runtime_effect": True,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
                "candidate_rows": [{"stock_code": "000101"}],
            }
        ),
        encoding="utf-8",
    )

    rows, diagnostics = mod.load_bottom_rebound_source_rows("2026-05-22", source_path=source_path)

    assert rows.empty
    assert diagnostics["status"] == "blocked_contract"


def test_bottom_rebound_candidate_uses_dedicated_anticipatory_arm_context():
    candidate = {
        "candidate_key": "000101",
        "source_date": "2026-05-22",
        "stock_code": "000101",
        "policy_version": mod.POLICY_VERSION,
        "volatility_bucket": "bottom_rebound",
        "lifecycle_exploration_score": 0.8,
        "_reference_price": 1000.0,
        "source_features": {
            "bottom_rebound_source": {
                "present": True,
                "entry_context": {"setup_type": "anticipatory_bottom_rebound_swing"},
            }
        },
    }

    arms = mod.build_arm_rows([candidate], virtual_budget_krw=1_000_000)

    assert [row["arm_id"] for row in arms] == [item["arm_id"] for item in mod.BOTTOM_REBOUND_ARM_SET]
    assert {row["entry_policy"] for row in arms} == {
        "bottom_rebound_next_open_entry",
        "bottom_rebound_signal_close_retest_limit_entry",
        "bottom_rebound_atr_pullback_limit_entry",
    }
    assert all(row["arm_features"]["arm_policy_version"] == mod.BOTTOM_REBOUND_ARM_POLICY_VERSION for row in arms)
    assert all(row["allowed_runtime_apply"] is False for row in arms)
    assert all(row["arm_features"]["allowed_runtime_apply"] is False for row in arms)
    assert all(
        row["arm_features"]["bottom_rebound_entry_context"]["entry_context_contract"][
            "do_not_require_breakout_confirmation"
        ]
        is True
        for row in arms
    )
    assert all(
        row["arm_features"]["bottom_rebound_entry_context"]["entry_context_contract"]["allowed_runtime_apply"] is False
        for row in arms
    )
    assert all(row["actual_order_submitted"] is False for row in arms)
