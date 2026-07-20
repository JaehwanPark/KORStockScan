from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from src.trading.entry.entry_types import PlannedOrder
from src.trading.order.broker_gateway import BrokerGateway
from src.trading.order.order_types import BrokerOrderResult


class OrderManager:
    """Submits single or concurrent order batches through an injected gateway."""

    def __init__(self, gateway: BrokerGateway, *, max_workers: int = 4) -> None:
        self.gateway = gateway
        self.max_workers = max_workers

    def submit_order(self, order: PlannedOrder) -> BrokerOrderResult:
        return self.gateway.submit_order(order)

    def submit_orders_async(
        self, orders: list[PlannedOrder]
    ) -> list[BrokerOrderResult]:
        if not orders:
            return []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(orders))) as pool:
            futures = [pool.submit(self.submit_order, order) for order in orders]
            return [future.result() for future in futures]


class InMemoryBrokerGateway:
    """Simple fake gateway suitable for tests and local dry-runs."""

    def submit_order(self, order: PlannedOrder) -> BrokerOrderResult:
        now = time.time()
        return BrokerOrderResult(
            accepted=True,
            order_tag=order.tag,
            broker_order_id=f"SIM-{order.symbol}-{int(now * 1000)}",
            order_status="SUBMITTED",
            request_timestamp=now,
            response_timestamp=now,
            raw=order.to_dict(),
        )
