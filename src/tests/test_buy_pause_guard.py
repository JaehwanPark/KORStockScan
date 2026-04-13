from datetime import datetime

from src.engine import buy_pause_guard as guard_mod


def _make_trade(
    trade_id,
    *,
    profit_rate,
    realized_pnl_krw,
    sell_time,
    exit_rule="scalp_scanner_fallback_never_green",
):
    return {
        "id": trade_id,
        "strategy": "SCALPING",
        "status": "COMPLETED",
        "entry_mode": "fallback",
        "profit_rate": profit_rate,
        "realized_pnl_krw": realized_pnl_krw,
        "sell_time": sell_time,
        "buy_time": sell_time,
        "exit_signal": {"exit_rule": exit_rule},
    }


def test_buy_pause_guard_does_not_alert_before_sample_ready(tmp_path, monkeypatch):
    state_path = tmp_path / "buy_pause_guard_state.json"
    monkeypatch.setattr(guard_mod, "BUY_PAUSE_GUARD_STATE_PATH", state_path)
    monkeypatch.setattr(
        guard_mod,
        "_collect_trade_rows",
        lambda target_date: [
            _make_trade(1, profit_rate=-0.8, realized_pnl_krw=-11000, sell_time=f"{target_date} 09:33:00"),
            _make_trade(2, profit_rate=-0.7, realized_pnl_krw=-12000, sell_time=f"{target_date} 09:34:00"),
        ],
    )
    monkeypatch.setattr(guard_mod, "_find_previous_trading_day_avg_loss", lambda now_dt: ("2026-04-08", -0.5))

    result = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 9, 35, 0),
        send_alert=False,
    )

    assert result["should_alert"] is False
    assert result["metrics_snapshot"]["sample_ready"] is False
    assert not state_path.exists()


def test_buy_pause_guard_creates_pending_on_two_of_three(tmp_path, monkeypatch):
    state_path = tmp_path / "buy_pause_guard_state.json"
    monkeypatch.setattr(guard_mod, "BUY_PAUSE_GUARD_STATE_PATH", state_path)
    monkeypatch.setattr(
        guard_mod,
        "_collect_trade_rows",
        lambda target_date: [
            _make_trade(1, profit_rate=-0.82, realized_pnl_krw=-9000, sell_time=f"{target_date} 09:46:00"),
            _make_trade(2, profit_rate=-0.71, realized_pnl_krw=-8000, sell_time=f"{target_date} 09:48:00"),
            _make_trade(3, profit_rate=-0.66, realized_pnl_krw=-7000, sell_time=f"{target_date} 09:52:00"),
        ],
    )
    monkeypatch.setattr(guard_mod, "_find_previous_trading_day_avg_loss", lambda now_dt: ("2026-04-08", -0.45))
    alerts = []
    monkeypatch.setattr(guard_mod, "_publish_guard_alert", lambda message: alerts.append(message))

    result = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 9, 55, 0),
        send_alert=True,
    )

    assert result["should_alert"] is True
    assert result["alert_sent"] is True
    assert result["state_status"] == "pending"
    assert result["guard_id"].startswith("BPG-20260409-0955-")
    assert alerts and "/buy_pause_confirm" in alerts[0]

    state = guard_mod.load_buy_pause_guard_state(now_dt=datetime(2026, 4, 9, 9, 55, 0))
    assert state["status"] == "pending"
    assert state["latest_trade_fingerprint"] == result["metrics_snapshot"]["latest_trade_fingerprint"]


def test_buy_pause_guard_pending_and_reject_suppress_same_fingerprint(tmp_path, monkeypatch):
    state_path = tmp_path / "buy_pause_guard_state.json"
    monkeypatch.setattr(guard_mod, "BUY_PAUSE_GUARD_STATE_PATH", state_path)
    base_rows = [
        _make_trade(1, profit_rate=-0.82, realized_pnl_krw=-9000, sell_time="2026-04-09 09:46:00"),
        _make_trade(2, profit_rate=-0.71, realized_pnl_krw=-8000, sell_time="2026-04-09 09:48:00"),
        _make_trade(3, profit_rate=-0.66, realized_pnl_krw=-7000, sell_time="2026-04-09 09:52:00"),
    ]
    rows_holder = {"rows": list(base_rows)}
    monkeypatch.setattr(guard_mod, "_collect_trade_rows", lambda target_date: list(rows_holder["rows"]))
    monkeypatch.setattr(guard_mod, "_find_previous_trading_day_avg_loss", lambda now_dt: ("2026-04-08", -0.45))

    first = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 9, 55, 0),
        send_alert=False,
    )
    duplicate = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 10, 0, 0),
        send_alert=False,
    )
    rejected = guard_mod.reject_buy_pause_guard(first["guard_id"], now_dt=datetime(2026, 4, 9, 10, 1, 0))
    after_reject_same = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 10, 2, 0),
        send_alert=False,
    )

    rows_holder["rows"].append(
        _make_trade(4, profit_rate=-0.73, realized_pnl_krw=-6000, sell_time="2026-04-09 10:03:00")
    )
    after_new_trade = guard_mod.evaluate_buy_pause_guard(
        "2026-04-09",
        now_dt=datetime(2026, 4, 9, 10, 4, 0),
        send_alert=False,
    )

    assert duplicate["guard_id"] == first["guard_id"]
    assert duplicate["state_status"] == "pending"
    assert rejected["ok"] is True
    assert after_reject_same["guard_id"] == first["guard_id"]
    assert after_reject_same["state_status"] == "rejected"
    assert after_new_trade["guard_id"] != first["guard_id"]
    assert after_new_trade["state_status"] == "pending"


def test_confirm_buy_pause_guard_updates_state(monkeypatch, tmp_path):
    state_path = tmp_path / "buy_pause_guard_state.json"
    monkeypatch.setattr(guard_mod, "BUY_PAUSE_GUARD_STATE_PATH", state_path)
    guard_mod.save_buy_pause_guard_state(
        {
            "active_guard_id": "BPG-20260409-1000-01",
            "status": "pending",
            "created_at": "2026-04-09 10:00:00",
            "expires_at": "2026-04-09 11:00:00",
            "metrics_snapshot": {"fallback_win_rate": 0.0},
            "latest_trade_fingerprint": "3:3:2026-04-09 09:52:00:-24000",
        }
    )
    calls = []
    monkeypatch.setattr(
        guard_mod,
        "set_buy_side_pause",
        lambda paused, **kwargs: calls.append((paused, kwargs)) or True,
    )

    result = guard_mod.confirm_buy_pause_guard(
        "BPG-20260409-1000-01",
        now_dt=datetime(2026, 4, 9, 10, 5, 0),
    )

    assert result["ok"] is True
    assert calls and calls[0][0] is True
    state = guard_mod.load_buy_pause_guard_state(now_dt=datetime(2026, 4, 9, 10, 5, 0))
    assert state["status"] == "confirmed"
