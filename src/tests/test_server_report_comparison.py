import json

from src.engine.server_report_comparison import (
    MetricSpec,
    SectionPolicy,
    _build_section_result,
    _compare_metrics,
    build_snapshot_summary,
    render_checklist_append_block,
    render_markdown_report,
)


def test_compare_metrics_uses_safe_metric_allowlist_only():
    policy = SectionPolicy(
        key="trade_review",
        label="Trade Review",
        remote_path_template="/api/trade-review?date={date}",
        safe_metrics=(
            MetricSpec("completed_trades", ("metrics", "completed_trades")),
            MetricSpec("open_trades", ("metrics", "open_trades")),
        ),
        excluded_metric_labels=("avg_profit_rate", "profit_rate"),
    )
    local_payload = {"metrics": {"completed_trades": 2, "open_trades": 1, "avg_profit_rate": 0.0}}
    remote_payload = {"metrics": {"completed_trades": 3, "open_trades": 1, "avg_profit_rate": 5.0}}

    rows = _compare_metrics(local_payload, remote_payload, policy)

    assert [row["label"] for row in rows] == ["completed_trades", "open_trades"]
    assert rows[0]["delta_remote_minus_local"] == 1.0


def test_build_section_result_preserves_excluded_metric_labels():
    policy = SectionPolicy(
        key="post_sell_feedback",
        label="Post Sell Feedback",
        remote_path_template="/api/post-sell-feedback?date={date}",
        safe_metrics=(MetricSpec("total_candidates", ("metrics", "total_candidates")),),
        excluded_metric_labels=("avg_realized_profit_rate", "profit_rate"),
    )

    result = _build_section_result(
        policy,
        local_payload={"metrics": {"total_candidates": 1}},
        remote_payload={"metrics": {"total_candidates": 2}},
    )

    assert result["status"] == "ok"
    assert result["excluded_metric_labels"] == ["avg_realized_profit_rate", "profit_rate"]
    assert result["safe_metric_rows"][0]["delta_remote_minus_local"] == 1.0


def test_render_markdown_report_mentions_excluded_metrics_and_status():
    comparison = {
        "date": "2026-04-09",
        "remote_base_url": "https://songstockscan.ddns.net",
        "since_time": "09:00:00",
        "policy": {"reason": "safe only"},
        "sections": {
            "trade_review": {
                "label": "Trade Review",
                "status": "ok",
                "remote_url": "https://songstockscan.ddns.net/api/trade-review?date=2026-04-09",
                "excluded_metric_labels": ["avg_profit_rate", "profit_rate"],
                "safe_metric_rows": [
                    {
                        "label": "completed_trades",
                        "local": 2,
                        "remote": 3,
                        "delta_remote_minus_local": 1.0,
                    }
                ],
                "distribution_refs": {},
            }
        },
    }

    rendered = render_markdown_report(comparison)

    assert "excluded_from_criteria" in rendered
    assert "avg_profit_rate" in rendered
    assert "completed_trades" in rendered


def test_snapshot_summary_and_checklist_block_surface_safe_diff_only():
    comparison = {
        "date": "2026-04-09",
        "remote_base_url": "https://songstockscan.ddns.net",
        "since_time": "09:00:00",
        "generated_at": "2026-04-09 12:00:05",
        "policy": {"reason": "safe only"},
        "sections": {
            "trade_review": {
                "label": "Trade Review",
                "status": "ok",
                "safe_metric_rows": [
                    {"label": "completed_trades", "local": 2, "remote": 3, "delta_remote_minus_local": 1.0},
                    {"label": "open_trades", "local": 1, "remote": 1, "delta_remote_minus_local": 0.0},
                ],
            }
        },
    }

    summary = build_snapshot_summary(comparison)
    assert summary["sections"][0]["differing_metric_count"] == 1
    assert summary["sections"][0]["top_diffs"][0]["label"] == "completed_trades"

    block = render_checklist_append_block(comparison, report_relpath="data/report/server_comparison/server_comparison_2026-04-09.md")
    assert "본서버 vs songstockscan 자동 비교" in block
    assert "completed_trades" in block
    assert "safe only" in block
