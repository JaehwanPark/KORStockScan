import json
from pathlib import Path

from src.engine.watching_prompt_75_shadow_report import (
    build_watching_prompt_75_shadow_report,
    render_watching_prompt_75_shadow_markdown,
)


def _write_pipeline_events(tmp_path: Path, target_date: str, rows: list[dict]) -> Path:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    path = event_dir / f"pipeline_events_{target_date}.jsonl"
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def test_build_shadow_report_includes_distribution_and_crosstab(tmp_path: Path):
    target_date = "2026-04-13"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "watching_prompt_75_shadow",
                "stock_code": "111111",
                "stock_name": "테스트A",
                "record_id": 101,
                "emitted_at": "2026-04-13T09:10:00",
                "fields": {
                    "main_action": "WAIT",
                    "main_score": "77.0",
                    "shadow_action": "BUY",
                    "shadow_score": "76.0",
                    "buy_diverged": "true",
                    "score_band": "77",
                    "threshold_live": "80",
                    "threshold_shadow": "75",
                    "ai_response_ms": "123",
                },
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "watching_prompt_75_shadow",
                "stock_code": "222222",
                "stock_name": "테스트B",
                "record_id": 102,
                "emitted_at": "2026-04-13T09:11:00",
                "fields": {
                    "main_action": "WAIT",
                    "main_score": "75.0",
                    "shadow_action": "WAIT",
                    "shadow_score": "74.0",
                    "buy_diverged": "false",
                    "score_band": "75",
                },
            },
        ],
    )
    missed_report = {
        "rows": [
            {
                "record_id": 101,
                "stock_code": "111111",
                "outcome": "MISSED_WINNER",
                "terminal_stage": "latency_block",
                "close_10m_pct": 1.2,
                "mfe_10m_pct": 1.5,
                "mae_10m_pct": -0.2,
                "estimated_counterfactual_pnl_10m_krw": 12000,
            },
            {
                "record_id": 102,
                "stock_code": "222222",
                "outcome": "AVOIDED_LOSER",
                "terminal_stage": "blocked_ai_score",
                "close_10m_pct": -0.8,
                "mfe_10m_pct": 0.1,
                "mae_10m_pct": -1.1,
                "estimated_counterfactual_pnl_10m_krw": -4000,
            },
        ]
    }

    report = build_watching_prompt_75_shadow_report(target_date, data_dir=tmp_path, missed_report=missed_report)

    assert report["metrics"]["shadow_samples"] == 2
    assert report["metrics"]["buy_diverged_count"] == 1
    assert report["metrics"]["joined_missed_rows"] == 2
    assert report["score_band_distribution"][0]["score_band"] == 75
    assert report["score_band_distribution"][1]["score_band"] == 77
    assert report["cross_tabs"]["buy_diverged_vs_outcome"][0]["buy_diverged"] is False
    assert report["cross_tabs"]["buy_diverged_vs_outcome"][1]["buy_diverged"] is True
    assert report["cross_tabs"]["buy_diverged_vs_outcome"][1]["MISSED_WINNER"] == 1


def test_render_shadow_report_markdown_handles_empty_rows(tmp_path: Path):
    target_date = "2026-04-13"
    _write_pipeline_events(tmp_path, target_date, [])
    report = build_watching_prompt_75_shadow_report(target_date, data_dir=tmp_path, missed_report={"rows": []})

    markdown = render_watching_prompt_75_shadow_markdown(report)

    assert "shadow_samples: `0`" in markdown
    assert "데이터 없음" in markdown
