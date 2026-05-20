from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QNA = ROOT / "docs" / "plan-korStockScanPerformanceOptimization.qna.md"
ARCHIVE = ROOT / "docs" / "archive" / "plan-korStockScanPerformanceOptimization.qna.pre-automation-renewal-2026-05-13.md"


def test_qna_is_automation_chain_oriented():
    text = QNA.read_text(encoding="utf-8")

    required_terms = (
        "자동화체인 오판 방지 FAQ",
        "Metric Decision Contract",
        "diagnostic_win_rate",
        "primary_ev",
        "simple_sum_profit_pct",
        "daily-only",
        "rolling/cumulative",
        "actual_order_submitted=false",
        "runtime_approval_summary",
        "plan_rebase_daily_renewal",
        "bounded_document_mutation_queue",
        "document_mutation_allowed=true",
        "1차 수정(first-pass bounded update)",
        "2차 감리(second-pass audit review)",
        "approval artifact",
        "runtime_effect=false",
        "allowed_runtime_apply=false",
        "instrumentation_gap",
        "source_quality_blocker",
    )

    missing = [term for term in required_terms if term not in text]
    assert missing == []


def test_qna_moves_legacy_latency_details_to_archive():
    text = QNA.read_text(encoding="utf-8")
    archive_text = ARCHIVE.read_text(encoding="utf-8")

    legacy_terms = (
        "ShadowDiff0428",
        "2026-04-27 15:00 offline bundle",
        "same bundle + canary_applied=False",
    )

    for term in legacy_terms:
        assert term not in text
        assert term in archive_text
