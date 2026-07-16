from datetime import datetime

import src.engine.sniper_entry_metrics as entry_metrics


def test_summarize_today_entry_metrics(tmp_path, monkeypatch):
    target_date = "2026-04-02"
    monkeypatch.setattr(entry_metrics, "LOGS_DIR", tmp_path)

    (tmp_path / "sniper_state_handlers_info.log").write_text(
        "\n".join(
            [
                f"[{target_date} 10:00:00] 📢 INFO in sniper_state_handlers: [LATENCY_ENTRY_DECISION] TEST(123456) mode=normal decision=ALLOW_NORMAL latency=SAFE signal=10000 latest=10000 allowed_slippage=20 orders=1",
                f"[{target_date} 10:01:00] 📢 INFO in sniper_state_handlers: [LATENCY_ENTRY_DECISION] TEST(123456) mode=fallback decision=REJECT_MARKET_CONDITION latency=CAUTION signal=10000 latest=10010 allowed_slippage=30 orders=2",
                f"[{target_date} 10:01:00] 📢 INFO in sniper_state_handlers: [ENTRY_SUBMISSION_BUNDLE] TEST(123456) mode=fallback requested_qty=5 legs=2 primary_ord_no=O1",
                f"[{target_date} 10:01:01] 📢 INFO in sniper_state_handlers: [LATENCY_ENTRY_ORDER_SENT] TEST(123456) tag=fallback_scout qty=1 price=0 type=16 tif=IOC ord_no=O1",
                f"[{target_date} 10:01:01] 📢 INFO in sniper_state_handlers: [LATENCY_ENTRY_ORDER_SENT] TEST(123456) tag=fallback_main qty=4 price=9990 type=00 tif=DAY ord_no=O2",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "sniper_execution_receipts_info.log").write_text(
        "\n".join(
            [
                f"[{target_date} 10:01:05] 📢 INFO in sniper_execution_receipts: [ENTRY_FILL] TEST(123456) tag=fallback_scout ord_no=O1 fill_qty=1 filled=1/1 fill_price=10000",
                f"[{target_date} 10:01:06] 📢 INFO in sniper_execution_receipts: [ENTRY_FILL] TEST(123456) tag=fallback_main ord_no=O2 fill_qty=4 filled=4/4 fill_price=9990",
                f"[{target_date} 10:01:06] 📢 INFO in sniper_execution_receipts: [ENTRY_BUNDLE_FILLED] TEST(123456) mode=fallback filled_qty=5/5 avg_buy=9992",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "kiwoom_orders_info.log").write_text(
        f"[{target_date} 10:01:01] 📢 INFO in kiwoom_orders: [ENTRY_TIF_MAP] IOC buy request promoted to best-IOC(16); requested_limit_price=10000 is advisory only\n",
        encoding="utf-8",
    )

    summary = entry_metrics.summarize_today_entry_metrics(
        now=datetime(2026, 4, 2, 12, 0, 0)
    )

    assert summary.latency_counts["SAFE"] == 1
    assert summary.latency_counts["CAUTION"] == 1
    assert summary.fallback_activation_count == 1
    assert summary.order_tag_counts["fallback_scout"] == 1
    assert summary.fill_tag_counts["fallback_main"] == 1
    assert summary.bundle_filled_mode_counts["fallback"] == 1
    assert summary.tif_promotions == 1


def test_format_entry_metrics_summary():
    summary = entry_metrics.EntryMetricsSummary(date="2026-04-02")
    summary.latency_counts.update({"SAFE": 2, "CAUTION": 1, "DANGER": 3})
    summary.submission_mode_counts.update({"normal": 2, "fallback": 1})
    summary.order_tag_counts.update({"fallback_scout": 1, "fallback_main": 1})
    summary.fill_tag_counts.update({"fallback_scout": 1})
    summary.bundle_filled_mode_counts.update({"fallback": 1})
    summary.order_type_counts.update({"16": 1, "00": 1})
    summary.order_tif_counts.update({"IOC": 1, "DAY": 1})
    summary.tif_promotions = 1

    text = entry_metrics.format_entry_metrics_summary(summary)

    assert "안정 구간 `SAFE`: 2건" in text
    assert "legacy fallback `fallback`: 1건" in text
    assert "현재 live 진입 경로가 아닙니다" in text
    assert "`IOC -> 16` 승격: 1건" in text


def test_format_entry_metrics_summary_compact():
    summary = entry_metrics.EntryMetricsSummary(date="2026-04-02")
    summary.latency_counts.update({"SAFE": 2, "CAUTION": 1, "DANGER": 3})
    summary.submission_mode_counts.update({"normal": 2, "fallback": 1})
    summary.order_tag_counts.update({"fallback_scout": 1, "fallback_main": 1})
    summary.fill_tag_counts.update({"fallback_scout": 1, "fallback_main": 1})
    summary.bundle_filled_mode_counts.update({"fallback": 1})
    summary.order_type_counts.update({"16": 1, "00": 1})
    summary.order_tif_counts.update({"IOC": 1, "DAY": 1})
    summary.tif_promotions = 1

    text = entry_metrics.format_entry_metrics_summary_compact(summary)

    assert "📊 장중 진입 지표 (2026-04-02)" in text
    assert "지연 판정: SAFE 2건 / CAUTION 1건 / DANGER 3건" in text
    assert "진입 방식: 일반 2건 / fallback 1건" in text
    assert "SAFE=일반 진입 가능, CAUTION=현재는 reject, DANGER=신규 진입 차단" in text
