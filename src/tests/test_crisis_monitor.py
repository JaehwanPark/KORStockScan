from datetime import datetime

from src.scanners import crisis_monitor


def _kst_at(hour: int, minute: int = 0):
    return datetime(2026, 5, 18, hour, minute, tzinfo=crisis_monitor.KST)


def test_crisis_alert_slot_for_three_daily_windows():
    assert crisis_monitor.crisis_alert_slot_for(_kst_at(8, 0)) == "preopen"
    assert crisis_monitor.crisis_alert_slot_for(_kst_at(11, 45)) == "noon"
    assert crisis_monitor.crisis_alert_slot_for(_kst_at(15, 45)) == "postclose"
    assert crisis_monitor.crisis_alert_slot_for(_kst_at(13, 0)) is None


def test_should_send_crisis_risk_alert_once_per_slot(tmp_path):
    state_path = tmp_path / "crisis_monitor_alert_state.json"
    now = _kst_at(8, 30)

    allowed, reason, slot = crisis_monitor.should_send_crisis_risk_alert(now, state_path)

    assert allowed is True
    assert reason == "slot_allowed:preopen"
    assert slot == "preopen"

    crisis_monitor.mark_crisis_risk_alert_sent(now, slot, risk_count=4, path=state_path)

    allowed, reason, slot = crisis_monitor.should_send_crisis_risk_alert(now, state_path)

    assert allowed is False
    assert reason == "slot_already_sent:preopen"
    assert slot == "preopen"


def test_should_send_crisis_risk_alert_allows_next_slot(tmp_path):
    state_path = tmp_path / "crisis_monitor_alert_state.json"
    preopen = _kst_at(8, 30)
    noon = _kst_at(12, 0)

    crisis_monitor.mark_crisis_risk_alert_sent(preopen, "preopen", risk_count=4, path=state_path)

    allowed, reason, slot = crisis_monitor.should_send_crisis_risk_alert(noon, state_path)

    assert allowed is True
    assert reason == "slot_allowed:noon"
    assert slot == "noon"


def test_should_send_crisis_risk_alert_blocks_outside_slots(tmp_path):
    allowed, reason, slot = crisis_monitor.should_send_crisis_risk_alert(
        _kst_at(10, 15),
        tmp_path / "crisis_monitor_alert_state.json",
    )

    assert allowed is False
    assert reason == "outside_alert_slot"
    assert slot is None
