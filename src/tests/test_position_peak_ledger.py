from datetime import datetime

from src.engine.scalping.position_peak_ledger import PositionPeakRuntimeLedger


def _dongyang_stock(**overrides):
    stock = {
        "id": 117,
        "code": "001520",
        "name": "동양",
        "strategy": "SCALPING",
        "buy_price": 1123,
        "buy_qty": 1,
        "buy_time": datetime(2026, 7, 23, 12, 9, 30),
    }
    stock.update(overrides)
    return stock


def test_dongyang_peak_survives_restart_and_rejects_average_mismatch(tmp_path):
    ledger = PositionPeakRuntimeLedger(tmp_path / "position_peak.json")
    stock = _dongyang_stock()

    recorded = ledger.record(
        stock,
        peak_price=1140,
        observed_at=1_785_000_000.0,
        reason="holding_peak_update",
    )

    assert recorded["peak_price"] == 1140
    restarted = _dongyang_stock()
    assert ledger.restore_peak(restarted) == (1140, "ledger_peak_restored")

    changed_cycle_basis = _dongyang_stock(buy_price=1124)
    assert ledger.restore_peak(changed_cycle_basis) == (
        0,
        "ledger_average_price_mismatch",
    )


def test_peak_only_decreases_for_explicit_runner_rebaseline(tmp_path):
    ledger = PositionPeakRuntimeLedger(tmp_path / "position_peak.json")
    stock = _dongyang_stock()
    ledger.record(
        stock,
        peak_price=1140,
        observed_at=1.0,
        reason="holding_peak_update",
    )

    unchanged = ledger.record(
        stock,
        peak_price=1130,
        observed_at=2.0,
        reason="lower_tick",
    )
    assert unchanged["peak_price"] == 1140

    reset = ledger.record(
        stock,
        peak_price=1130,
        observed_at=3.0,
        reason="early_partial_runner_rebaseline",
        allow_decrease=True,
    )
    assert reset["peak_price"] == 1130


def test_completed_cycle_is_removed_without_touching_new_cycle(tmp_path):
    ledger = PositionPeakRuntimeLedger(tmp_path / "position_peak.json")
    old = _dongyang_stock()
    new = _dongyang_stock(id=118, buy_time=datetime(2026, 7, 23, 13, 0, 0))
    ledger.record(old, peak_price=1140, observed_at=1.0, reason="old")
    ledger.record(new, peak_price=1150, observed_at=2.0, reason="new")

    assert ledger.remove_for_stock(old) is True
    assert ledger.get_for_stock(old) is None
    assert ledger.restore_peak(new) == (1150, "ledger_peak_restored")


def test_simulated_scalp_never_writes_real_peak_ledger(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    monkeypatch.setattr(
        handlers.POSITION_PEAK_LEDGER,
        "record",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("sim peak must not enter the real runtime ledger")
        ),
    )
    stock = _dongyang_stock(
        scalp_live_simulator=True,
        simulation_book="SCALP_LIVE_SIM",
    )

    handlers._persist_scalping_position_peak(
        stock,
        "001520",
        peak_price=1140,
        observed_at=1.0,
        reason="simulated_peak",
    )
