from datetime import UTC, datetime, timedelta
from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import EntryDecision, LatencyState, LatencyStatus, SignalSnapshot


def _snapshot(**overrides):
    base = SignalSnapshot(
        symbol="005930",
        strategy_id="SCALP",
        signal_time=datetime.now(UTC),
        signal_price=10_000,
        signal_strength=0.9,
        planned_qty=10,
        side="BUY",
        context={},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _latency(state):
    return LatencyStatus(
        state=state,
        ws_age_ms=100,
        ws_jitter_ms=50,
        order_rtt_avg_ms=100,
        order_rtt_p95_ms=200,
        quote_stale=False,
        spread_ratio=0.001,
    )


def test_policy_allows_normal_in_safe():
    policy = EntryPolicy(EntryConfig())
    result = policy.evaluate(snapshot=_snapshot(), latency_status=_latency(LatencyState.SAFE), latest_price=10_010)
    assert result.decision == EntryDecision.ALLOW_NORMAL


def test_policy_rejects_slippage_in_safe():
    policy = EntryPolicy(EntryConfig(normal_allowed_slippage_ticks=1, normal_allowed_slippage_pct=0.0001))
    result = policy.evaluate(snapshot=_snapshot(), latency_status=_latency(LatencyState.SAFE), latest_price=10_500)
    assert result.decision == EntryDecision.REJECT_SLIPPAGE


def test_policy_allows_caution_after_slippage_check():
    policy = EntryPolicy(EntryConfig())
    result = policy.evaluate(snapshot=_snapshot(), latency_status=_latency(LatencyState.CAUTION), latest_price=10_020)
    assert result.decision == EntryDecision.ALLOW_NORMAL
    assert result.reason == "caution_normal_entry_allowed"


def test_policy_rejects_danger():
    policy = EntryPolicy(EntryConfig())
    result = policy.evaluate(snapshot=_snapshot(), latency_status=_latency(LatencyState.DANGER), latest_price=10_000)
    assert result.decision == EntryDecision.REJECT_DANGER


def test_policy_rejects_timeout():
    policy = EntryPolicy(EntryConfig(entry_deadline_ms=100))
    snapshot = _snapshot(signal_time=datetime.now(UTC) - timedelta(seconds=1))
    result = policy.evaluate(snapshot=snapshot, latency_status=_latency(LatencyState.SAFE), latest_price=10_000)
    assert result.decision == EntryDecision.REJECT_TIMEOUT
