import json

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import SwingStrategyDiscoveryArm, SwingStrategyDiscoveryCandidate
from src.engine import swing_strategy_discovery_sim as mod
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema


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
    assert all("legacy_ml_role" in row["source_features"] for row in candidates)
    assert all(row["sector"] for row in candidates)
    assert all(row["theme_tags"] for row in candidates)


def test_schema_report_and_persistence_are_idempotent(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'swing_strategy_discovery.db'}"
    output_dir = tmp_path / "report"

    ensure_swing_strategy_discovery_schema(db_url)
    ensure_swing_strategy_discovery_schema(db_url)

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

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
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
