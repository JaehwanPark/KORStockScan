import pandas as pd

from analysis.gemini_scalping_pattern_lab import analyze_patterns
from analysis.gemini_scalping_pattern_lab import build_dataset


def test_gemini_pattern_lab_excludes_good_exit_from_profit_sample():
    trade_facts = []
    build_dataset._process_post_sell_rows(
        [
            {
                "post_sell_id": "good",
                "recommendation_id": 1,
                "outcome": "GOOD_EXIT",
                "profit_rate": 1.2,
            },
            {
                "post_sell_id": "completed",
                "recommendation_id": 2,
                "outcome": "COMPLETED",
                "profit_rate": 0.8,
            },
        ],
        "local",
        {},
        {},
        trade_facts,
    )

    by_id = {item["trade_id"]: item for item in trade_facts}
    assert by_id["good"]["profit_valid_flag"] == "false"
    assert by_id["good"]["profit_rate"] == ""
    assert by_id["completed"]["profit_valid_flag"] == "true"
    assert by_id["completed"]["profit_rate"] == 0.8


def test_gemini_pattern_lab_cohort_summary_uses_canonical_ev_fields(monkeypatch):
    monkeypatch.setattr(analyze_patterns.config, "MIN_VALID_SAMPLES", 1)
    rows = pd.DataFrame(
        [
            {"cohort": "full_fill", "profit_rate": 1.0, "profit_valid_flag": "true"},
            {"cohort": "full_fill", "profit_rate": -0.5, "profit_valid_flag": "true"},
        ]
    )

    summary = analyze_patterns.cohort_summary(rows)

    assert summary[0]["diagnostic_win_rate_pct"] == 50.0
    assert summary[0]["simple_sum_profit_pct"] == 0.5
    assert summary[0]["equal_weight_avg_profit_pct"] == 0.25
    assert summary[0]["primary_decision_metric"] == "equal_weight_avg_profit_pct"
