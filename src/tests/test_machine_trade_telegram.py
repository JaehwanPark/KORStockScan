import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.notify import machine_trade_telegram as n
from src.trading.order.owner_custody_registry import OrderOwnerRegistry


def event(rows, kind, intent="a", **kw):
    row = dict(schema="order_owner_registry_event_v1", event=kind,
               intent_id=intent, observed_at_kst="2026-09-11T12:00:00+09:00",
               previous_hash=rows[-1]["event_hash"] if rows else "0" * 64, **kw)
    row["event_hash"] = hashlib.sha256(row["previous_hash"].encode() + OrderOwnerRegistry._canonical(row)).hexdigest()
    rows.append(row)
    return rows


def reserve(rows, intent="a", **kw):
    values = dict(account_key="live", owner_type="widget_auto_trade", owner_id="005930",
                  action="NEW", side="BUY", symbol="005930", quantity=10, filled_qty=0)
    values.update(kw)
    event(rows, "INTENT_RESERVED", intent, **values)
    event(rows, "ORDER_BOUND", intent, broker_order_no="0000012")


def state(tmp_path, rows=None):
    path = tmp_path / "state.json"
    n.initialize(path, rows or [], "live")
    return path, n.load(path)


@pytest.mark.parametrize("owner", ["widget_auto_trade", "episode"])
@pytest.mark.parametrize("side", ["BUY", "SELL"])
def test_all_owners_sides_partial_full_restart_and_amount_only(tmp_path, owner, side):
    path, s = state(tmp_path)
    rows = []
    reserve(rows, owner_type=owner, side=side, symbol="999999")
    n.collect(s, rows)
    assert not s["deliveries"]  # accepted is not a fill
    event(rows, "FILL_RECORDED", filled_qty=3, fill_amount=0)
    n.collect(s, rows)
    sent = []
    n.deliver(path, s, lambda text: sent.append(text) or 123)
    assert len(sent) == 1 and "3/10주 (부분체결)" in sent[0] and "999999" in sent[0]
    s = n.load(path)
    event(rows, "FILL_RECORDED", filled_qty=3, fill_amount=123000)
    n.collect(s, rows)
    n.deliver(path, s, lambda _: pytest.fail("duplicate"))
    event(rows, "FILL_RECORDED", filled_qty=10)
    n.collect(s, rows)
    n.deliver(path, s, lambda text: sent.append(text) or 124)
    assert len(sent) == 2 and "이번 체결 7주" in sent[-1] and "전량체결" in sent[-1]


@pytest.mark.parametrize("change", [dict(owner_type="main_scalping"), dict(owner_type="sim"),
                                       dict(account_key="demo"), dict(action="CANCEL")])
def test_excluded_owners_accounts_actions(tmp_path, change):
    _, s = state(tmp_path)
    rows = []
    reserve(rows, **change)
    event(rows, "FILL_RECORDED", filled_qty=1)
    n.collect(s, rows)
    assert not s["deliveries"]


@pytest.mark.parametrize("kind", ["MIGRATED_POSITION_REGISTERED", "MANUAL_EXIT_RECONCILED"])
def test_historical_reconciliation_never_becomes_new_fill(tmp_path, kind):
    _, s = state(tmp_path)
    rows = []
    event(rows, kind, owner_type="episode", account_key="live", action="NEW", side="SELL",
          symbol="005930", owner_id="machine", quantity=10, filled_qty=3, broker_order_no="123")
    event(rows, "FILL_RECORDED", filled_qty=5)
    n.collect(s, rows)
    assert not s["deliveries"]


def test_initial_baseline_no_history_and_reinitialization_forbidden(tmp_path):
    rows = []
    reserve(rows)
    event(rows, "FILL_RECORDED", filled_qty=4)
    path, s = state(tmp_path, rows)
    n.collect(s, rows)
    assert not s["deliveries"]
    with pytest.raises(RuntimeError):
        n.initialize(path, rows, "live")
    event(rows, "FILL_RECORDED", filled_qty=5)
    n.collect(s, rows)
    assert "이번 체결 1주" in s["deliveries"]["a:5"]["message"]


def test_amendment_parent_and_child_fills(tmp_path):
    _, s = state(tmp_path)
    rows = []
    reserve(rows, side="SELL")
    reserve(rows, "child", side="SELL", action="AMEND")
    event(rows, "SELL_AMEND_RECONCILED", "child", action="NEW", quantity=8,
          filled_qty=2, broker_order_no="0000013", amendment_parent_intent_id="a",
          amendment_parent_filled_qty=2)
    n.collect(s, rows)
    assert set(s["deliveries"]) == {"a:2", "child:2"}
    event(rows, "FILL_RECORDED", "child", filled_qty=8)
    n.collect(s, rows)
    assert "이번 체결 6주" in s["deliveries"]["child:8"]["message"]


def test_partial_cancel_fill_refresh(tmp_path):
    _, s = state(tmp_path)
    rows = []
    reserve(rows, side="SELL")
    event(rows, "PARTIAL_CANCEL_TARGET_FILL_REFRESHED", filled_qty=2)
    n.collect(s, rows)
    assert set(s["deliveries"]) == {"a:2"}


def test_corrupt_state_source_and_nonblocking_read(tmp_path):
    rows = []
    reserve(rows)
    path, s = state(tmp_path, rows)
    with pytest.raises(RuntimeError, match="rewritten"):
        n.collect(s, rows[:1])
    path.write_text("broken")
    with pytest.raises(ValueError):
        n.load(path)
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    registry.path.write_text("\n".join(json.dumps(e) for e in rows))
    registry.lock_path.touch()
    assert n.read_events(registry) == rows
    registry.path.write_text(registry.path.read_text().replace('"quantity": 10', '"quantity": 11'))
    with pytest.raises(RuntimeError):
        n.read_events(registry)


def queued(tmp_path):
    path, s = state(tmp_path)
    rows = []
    reserve(rows)
    event(rows, "FILL_RECORDED", filled_qty=1)
    n.collect(s, rows)
    return path, s


def test_uncertain_delivery_and_crash_never_replayed(tmp_path):
    path, s = queued(tmp_path)
    def fail(_):
        raise TimeoutError()
    n.deliver(path, s, fail)
    assert s["deliveries"]["a:1"]["status"] == "uncertain"
    n.deliver(path, n.load(path), lambda _: pytest.fail("ambiguous resend"))
    s["deliveries"]["a:1"]["status"] = "sending"
    n.save(path, s)
    assert n.load(path)["deliveries"]["a:1"]["status"] == "uncertain"


def test_explicit_rejection_bounded_retry(tmp_path):
    path, s = queued(tmp_path)
    attempts = []
    def reject(_):
        attempts.append(1)
        raise n.RejectedDelivery("rate_limit", 60)
    for clock in [0, 5, 59, 60, 120, 180]:
        n.deliver(path, s, reject, now=lambda: clock)
    assert len(attempts) == 3
    assert s["deliveries"]["a:1"]["status"] == "failed"


def test_telegram_api_false_and_receipt_validation(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"TELEGRAM_TOKEN": "fake", "ADMIN_ID": "fake"}))
    monkeypatch.setattr(n, "CONFIG_PATH", config)
    with patch.object(n.request, "urlopen") as mocked:
        mocked.return_value.__enter__.return_value.read.return_value = b'{"ok":false,"parameters":{"retry_after":90}}'
        with pytest.raises(n.RejectedDelivery) as failure:
            n.send_telegram("test")
        assert failure.value.retry_after == 90
        mocked.return_value.__enter__.return_value.read.return_value = b'{"ok":true,"result":{"message_id":123}}'
        assert n.send_telegram("test") == 123


@pytest.mark.parametrize("side", ["BUY", "SELL"])
def test_terminal_cancel_target_fill_only(tmp_path, side):
    _, s = state(tmp_path)
    rows = []
    reserve(rows, side=side)
    reserve(rows, "cancel", action="CANCEL", side=side)
    event(rows, f"{side}_TERMINAL_CANCEL_RECONCILED", filled_qty=4,
          terminal_cancel_reconciliation={"cancel_intent_id": "cancel"})
    n.collect(s, rows)
    assert set(s["deliveries"]) == {"a:4"}


def test_writer_lock_is_nonblocking_and_no_source_mutation(tmp_path):
    import fcntl
    rows = []
    reserve(rows)
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    content = "\n".join(json.dumps(e) for e in rows)
    registry.path.write_text(content)
    with registry.lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            n.read_events(registry)
    assert registry.path.read_text() == content


def test_state_persisted_before_sender_and_missing_state_fails(tmp_path):
    path, s = queued(tmp_path)
    def sender(_):
        assert json.loads(path.read_text())["deliveries"]["a:1"]["status"] == "sending"
        return 123
    n.deliver(path, s, sender)
    with pytest.raises(FileNotFoundError):
        n.load(tmp_path / "missing")


def test_service_contract_only_fill_consumer_and_old_notifiers_disabled():
    root = Path(__file__).resolve().parents[2]
    unit = (root / "deploy/systemd/korstockscan-machine-fill-telegram.service").read_text()
    assert "src.notify.machine_trade_telegram" in unit
    assert "--initialize" not in unit
    assert "ProtectSystem=strict" in unit
    for name, flag in [
        ("doosan-widget-collector", "KORSTOCKSCAN_DOOSAN_WIDGET_TELEGRAM_ENABLED"),
        ("hanwha-ocean-widget-collector", "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_TELEGRAM_ENABLED"),
        ("samsung-widget-collector", "KORSTOCKSCAN_SAMSUNG_WIDGET_TELEGRAM_ENABLED"),
        ("widget-signal-auto-trader", "KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_TELEGRAM_ENABLED"),
    ]:
        assert f'{flag}=false' in (root / f"deploy/systemd/korstockscan-{name}.service").read_text()


def test_rate_limit_applies_to_other_pending_fills(tmp_path):
    path, s = queued(tmp_path)
    s["deliveries"]["b:1"] = dict(s["deliveries"]["a:1"])
    def reject(_):
        raise n.RejectedDelivery("rate_limit", 90)
    n.deliver(path, s, reject, now=lambda: 0)
    n.deliver(path, s, lambda _: pytest.fail("global cooldown bypass"), now=lambda: 5)
    assert s["deliveries"]["b:1"]["attempts"] == 0


def test_restart_preserves_source_order_not_uuid_sort_order(tmp_path):
    path, s = state(tmp_path)
    rows = []
    reserve(rows, 'z-buy', side='BUY')
    event(rows, 'FILL_RECORDED', 'z-buy', filled_qty=1)
    reserve(rows, 'a-sell', side='SELL')
    event(rows, 'FILL_RECORDED', 'a-sell', filled_qty=1)
    n.collect(s, rows)
    n.save(path, s)  # JSON sort_keys puts a-sell first on disk
    s = n.load(path)
    sent = []
    n.deliver(path, s, lambda message: sent.append(message) or 1)
    assert '매수 체결' in sent[0]
    n.deliver(path, s, lambda message: sent.append(message) or 2)
    assert '매도 체결' in sent[1]


def test_read_only_check_does_not_mark_active_sender_uncertain(tmp_path):
    path, s = queued(tmp_path)
    def send(_):
        assert n.load(path, recover_inflight=False)['deliveries']['a:1']['status'] == 'sending'
        assert n.load(path)['deliveries']['a:1']['status'] == 'uncertain'
        return 1
    n.deliver(path, s, send)
    assert n.load(path)['deliveries']['a:1']['status'] == 'sent'


@pytest.mark.parametrize('key,value', [('attempts', -1), ('attempts', True), ('attempts', 4),
    ('attempts', 3), ('next_attempt', float('nan')), ('next_attempt', float('inf')),
    ('next_attempt', -1), ('next_attempt', 'later'), ('sequence', -1), ('sequence', None),
    ('source_hash', 'bad'), ('message', None)])
def test_invalid_delivery_state_fails_before_any_send(tmp_path, key, value):
    path, s = queued(tmp_path)
    s['deliveries']['a:1'][key] = value
    n.save(path, s)
    with pytest.raises(RuntimeError):
        n.load(path)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, True, 'later'])
def test_invalid_global_cooldown_fails_closed(tmp_path, value):
    path, s = queued(tmp_path)
    s['next_delivery_at'] = value
    n.save(path, s)
    with pytest.raises(RuntimeError):
        n.load(path)
