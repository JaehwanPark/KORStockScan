import time
from datetime import UTC, datetime
from src.trading.config.entry_config import EntryConfig
from src.trading.entry.entry_orchestrator import EntryOrchestrator
from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import SignalSnapshot
from src.trading.entry.latency_monitor import LatencyMonitor
from src.trading.entry.normal_entry_builder import NormalEntryBuilder
from src.trading.entry.state_machine import EntryStateMachine
from src.trading.logging.trade_logger import TradeLogger
from src.trading.market.market_data_cache import MarketDataCache
from src.trading.order.order_manager import InMemoryBrokerGateway, OrderManager


def _snapshot():
    return SignalSnapshot(
        symbol="005930",
        strategy_id="SCALP",
        signal_time=datetime.now(UTC),
        signal_price=10_000,
        signal_strength=0.95,
        planned_qty=10,
        side="BUY",
        context={},
    )


def _build_orchestrator(config: EntryConfig, *, order_rtt_avg_ms: int = 100):
    cache = MarketDataCache(stale_after_ms=config.max_ws_age_ms_for_caution)
    cache.update(
        "005930",
        last_price=10_010,
        best_ask=10_020,
        best_bid=10_000,
        received_at=time.time(),
    )
    return EntryOrchestrator(
        market_data_cache=cache,
        latency_monitor=LatencyMonitor(config),
        entry_policy=EntryPolicy(config),
        normal_entry_builder=NormalEntryBuilder(config),
        order_manager=OrderManager(InMemoryBrokerGateway()),
        state_machine=EntryStateMachine(),
        trade_logger=TradeLogger(),
        order_rtt_avg_ms=order_rtt_avg_ms,
        order_rtt_p95_ms=order_rtt_avg_ms + 50,
    )


def test_orchestrator_safe_path_returns_normal():
    config = EntryConfig()
    orchestrator = _build_orchestrator(config, order_rtt_avg_ms=100)
    result = orchestrator.process(_snapshot())
    assert result["mode"] == "normal"
    assert result["status"] == "ORDER_FILLED"


def test_orchestrator_caution_path_submits_normal():
    config = EntryConfig(
        max_order_rtt_avg_ms_for_safe=50,
        max_order_rtt_avg_ms_for_caution=300,
    )
    orchestrator = _build_orchestrator(config, order_rtt_avg_ms=120)
    result = orchestrator.process(_snapshot())
    assert result["mode"] == "normal"
    assert result["status"] == "ORDER_FILLED"


def test_orchestrator_danger_path_rejects():
    config = EntryConfig(
        max_spread_ratio_for_safe=0.0001,
        max_spread_ratio_for_caution=0.0001,
    )
    orchestrator = _build_orchestrator(config, order_rtt_avg_ms=100)
    result = orchestrator.process(_snapshot())
    assert result["mode"] == "reject"
    assert result["status"] == "REJECTED_DANGER"
