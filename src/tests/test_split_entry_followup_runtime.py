from datetime import datetime

import src.engine.sniper_execution_receipts as receipts


def test_emit_split_entry_followup_shadows_logs_integrity_and_recheck(monkeypatch):
    logged = []
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: logged.append((args, kwargs)))

    target_stock = {"name": "테스트A"}

    receipts._emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code="123456",
        target_id=1,
        now=datetime(2026, 4, 17, 12, 0, 0),
        entry_mode="fallback",
        fill_quality="PARTIAL_FILL",
        requested_entry_qty=9,
        cum_filled_qty=1,
        remaining_qty=8,
        new_qty=1,
    )
    receipts._emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code="123456",
        target_id=1,
        now=datetime(2026, 4, 17, 12, 0, 0),
        entry_mode="fallback",
        fill_quality="FULL_FILL",
        requested_entry_qty=9,
        cum_filled_qty=12,
        remaining_qty=0,
        new_qty=12,
    )

    stages = [args[3] for args, _ in logged]
    assert stages == [
        "split_entry_rebase_integrity_shadow",
        "split_entry_rebase_integrity_shadow",
        "split_entry_immediate_recheck_shadow",
    ]
    integrity_kwargs = logged[1][1]
    assert integrity_kwargs["integrity_flags"] == "cum_gt_requested,same_ts_multi_rebase"
    assert integrity_kwargs["rebase_count"] == 2
    recheck_kwargs = logged[2][1]
    assert recheck_kwargs["trigger_reason"] == "partial_then_expand"
    assert recheck_kwargs["first_partial_qty"] == 1


def test_clear_split_entry_shadow_state_removes_runtime_keys():
    target_stock = {
        "_split_entry_rebase_shadow_count": 2,
        "_split_entry_rebase_shadow_last_second": "2026-04-17T12:00:00",
        "_split_entry_rebase_shadow_same_second_count": 2,
        "_split_entry_first_partial_qty": 1,
        "_split_entry_last_immediate_recheck_rebase_count": 2,
        "name": "테스트B",
    }

    receipts._clear_split_entry_shadow_state(target_stock)

    assert target_stock == {"name": "테스트B"}
