from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any

from src.trading.entry.entry_policy import EntryPolicy
from src.trading.entry.entry_types import EntryDecision, PlannedOrder, SignalSnapshot
from src.trading.entry.latency_monitor import LatencyMonitor
from src.trading.entry.normal_entry_builder import NormalEntryBuilder
from src.trading.entry.state_machine import EntryStateMachine
from src.trading.logging.metrics_recorder import MetricsRecorder
from src.trading.logging.trade_logger import TradeLogger
from src.trading.market.market_data_cache import MarketDataCache
from src.trading.market.quote_consistency import build_quote_consistency_snapshot, quote_input_from_ws
from src.trading.order.order_manager import OrderManager


class EntryOrchestrator:
    """Coordinates snapshot, health evaluation, policy, order build, and submit."""

    def __init__(
        self,
        *,
        market_data_cache: MarketDataCache,
        latency_monitor: LatencyMonitor,
        entry_policy: EntryPolicy,
        normal_entry_builder: NormalEntryBuilder,
        order_manager: OrderManager,
        state_machine: EntryStateMachine,
        trade_logger: TradeLogger,
        metrics_recorder: MetricsRecorder | None = None,
        order_rtt_avg_ms: int = 0,
        order_rtt_p95_ms: int = 0,
    ) -> None:
        self.market_data_cache = market_data_cache
        self.latency_monitor = latency_monitor
        self.entry_policy = entry_policy
        self.normal_entry_builder = normal_entry_builder
        self.order_manager = order_manager
        self.state_machine = state_machine
        self.trade_logger = trade_logger
        self.metrics_recorder = metrics_recorder or MetricsRecorder()
        self.order_rtt_avg_ms = order_rtt_avg_ms
        self.order_rtt_p95_ms = order_rtt_p95_ms

    def process(self, snapshot: SignalSnapshot) -> dict[str, Any]:
        symbol = snapshot.symbol
        self.state_machine.transition(symbol, "SIGNAL_DETECTED", reason="signal_received")
        self.trade_logger.log_signal(
            symbol=symbol,
            strategy_id=snapshot.strategy_id,
            signal_time=snapshot.signal_time.isoformat(),
            signal_price=snapshot.signal_price,
            planned_qty=snapshot.planned_qty,
            signal_strength=snapshot.signal_strength,
        )

        self.state_machine.transition(symbol, "POLICY_CHECKING", reason="start_policy_check")
        latest_price = self.market_data_cache.get_last_price(symbol)
        best_ask = self.market_data_cache.get_best_ask(symbol)
        best_bid = self.market_data_cache.get_best_bid(symbol)
        quote_health = self.market_data_cache.get_quote_health(symbol)
        quote_consistency = build_quote_consistency_snapshot(
            ws=quote_input_from_ws(
                {
                    "curr": latest_price,
                    "best_ask": best_ask,
                    "best_bid": best_bid,
                    "quote_consistency_ws_age_ms": quote_health.ws_age_ms,
                }
            ),
            side="buy",
        )
        quote_consistency_fields = quote_consistency.as_event_fields()
        if quote_consistency.canonical_mark_price > 0:
            latest_price = int(quote_consistency.canonical_mark_price)
        latency = self.latency_monitor.evaluate(
            ws_age_ms=quote_health.ws_age_ms,
            ws_jitter_ms=quote_health.ws_jitter_ms,
            order_rtt_avg_ms=self.order_rtt_avg_ms,
            order_rtt_p95_ms=self.order_rtt_p95_ms,
            quote_stale=quote_health.quote_stale,
            spread_ratio=quote_health.spread_ratio,
        )
        if quote_consistency.normalization_runtime_effect and quote_consistency.entry_blocked:
            self.state_machine.transition(symbol, "REJECTED_DANGER", reason=quote_consistency.reason)
            self.metrics_recorder.increment("entry.reject_quote_consistency")
            result = {
                "status": "REJECTED_DANGER",
                "mode": "reject",
                "reason": quote_consistency.reason,
                "latency_state": latency.state.value,
                "orders": [],
                "broker_results": [],
                **quote_consistency_fields,
            }
            self.trade_logger.log_policy(
                symbol=symbol,
                latest_price=latest_price,
                elapsed_ms=int((datetime.now(UTC) - snapshot.signal_time).total_seconds() * 1000),
                latency_state=latency.state.value,
                ws_age_ms=latency.ws_age_ms,
                ws_jitter_ms=latency.ws_jitter_ms,
                order_rtt_avg_ms=latency.order_rtt_avg_ms,
                order_rtt_p95_ms=latency.order_rtt_p95_ms,
                allowed_slippage=0,
                decision="REJECT_DANGER",
                reason=quote_consistency.reason,
                **quote_consistency_fields,
            )
            self.trade_logger.log_result(**result)
            return result
        policy = self.entry_policy.evaluate(
            snapshot=snapshot,
            latency_status=latency,
            latest_price=latest_price,
            now=datetime.now(UTC),
        )
        self.trade_logger.log_policy(
            symbol=symbol,
            latest_price=latest_price,
            elapsed_ms=int((datetime.now(UTC) - snapshot.signal_time).total_seconds() * 1000),
            latency_state=latency.state.value,
            ws_age_ms=latency.ws_age_ms,
            ws_jitter_ms=latency.ws_jitter_ms,
            order_rtt_avg_ms=latency.order_rtt_avg_ms,
            order_rtt_p95_ms=latency.order_rtt_p95_ms,
            allowed_slippage=policy.computed_allowed_slippage,
            decision=policy.decision.value,
            reason=policy.reason,
            **quote_consistency_fields,
        )

        if policy.decision in {
            EntryDecision.REJECT_TIMEOUT,
            EntryDecision.REJECT_SLIPPAGE,
            EntryDecision.REJECT_DANGER,
            EntryDecision.REJECT_MARKET_CONDITION,
        }:
            reject_state = {
                EntryDecision.REJECT_TIMEOUT: "REJECTED_TIMEOUT",
                EntryDecision.REJECT_SLIPPAGE: "REJECTED_SLIPPAGE",
                EntryDecision.REJECT_DANGER: "REJECTED_DANGER",
                EntryDecision.REJECT_MARKET_CONDITION: "REJECTED_MARKET_CONDITION",
            }[policy.decision]
            self.state_machine.transition(symbol, reject_state, reason=policy.reason)
            self.metrics_recorder.increment(f"entry.{policy.decision.value.lower()}")
            result = {
                "status": reject_state,
                "mode": "reject",
                "reason": policy.reason,
                "latency_state": latency.state.value,
                "orders": [],
                "broker_results": [],
            }
            self.trade_logger.log_result(**result)
            return result

        if policy.decision == EntryDecision.ALLOW_NORMAL:
            self.state_machine.transition(symbol, "NORMAL_ORDER_SUBMITTING", reason=policy.reason)
            orders = [self.normal_entry_builder.build(snapshot=snapshot, latest_price=latest_price)]
            mode = "normal"
        else:
            orders = []
            mode = "reject"

        if not orders:
            self.state_machine.transition(symbol, "REJECTED_MARKET_CONDITION", reason="latency_fallback_deprecated")
            self.metrics_recorder.increment("entry.reject_market_condition")
            result = {
                "status": "REJECTED_MARKET_CONDITION",
                "mode": "reject",
                "reason": "latency_fallback_deprecated",
                "latency_state": latency.state.value,
                "orders": [],
                "broker_results": [],
            }
            self.trade_logger.log_result(**result)
            return result

        broker_results = self.order_manager.submit_orders_async(orders)
        for order, broker_result in zip(orders, broker_results):
            self.trade_logger.log_order(
                order_tag=order.tag,
                qty=order.qty,
                price=order.price,
                tif=order.tif,
                request_timestamp=broker_result.request_timestamp,
                response_timestamp=broker_result.response_timestamp,
                broker_order_id=broker_result.broker_order_id,
                order_status=broker_result.order_status,
            )

        accepted = [result for result in broker_results if result.accepted]
        if accepted and all(result.accepted for result in broker_results):
            final_state = "ORDER_FILLED"
        elif accepted:
            final_state = "ORDER_PARTIAL_FILLED"
        else:
            final_state = "ORDER_CANCELLED"
        self.state_machine.transition(symbol, final_state, reason=f"{mode}_submission_complete")

        result = {
            "status": final_state,
            "mode": mode,
            "reason": policy.reason,
            "latency_state": latency.state.value,
            "orders": [self._to_dict(order) for order in orders],
            "broker_results": [self._to_dict(item) for item in broker_results],
        }
        self.trade_logger.log_result(
            normal_mode=(mode == "normal"),
            fallback_mode=False,
            scout_filled=False,
            main_filled=False,
            partial_fill_ratio=(len(accepted) / len(broker_results)) if broker_results else 0.0,
            skipped_reason="",
            status=final_state,
            mode=mode,
        )
        self.metrics_recorder.increment(f"entry.{mode}")
        return result

    @staticmethod
    def _to_dict(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        return value
