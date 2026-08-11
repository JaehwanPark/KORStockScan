from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.trading.widget_auto_trade.gateway import SubmitResult
from src.trading.widget_auto_trade.manual_orders import ManualWidgetOrderExecutor

KST = ZoneInfo("Asia/Seoul")


class _Gateway:
    def __init__(self, *, reject_at: int | None = None) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.reject_at = reject_at

    def _result(self) -> SubmitResult:
        index = len(self.calls)
        rejected = self.reject_at == index
        return SubmitResult(
            accepted=not rejected,
            order_no="" if rejected else f"ORDER-{index}",
            return_code="-1" if rejected else "0",
            return_msg="rejected" if rejected else "ok",
        )

    def submit_limit_buy(self, **kwargs) -> SubmitResult:
        self.calls.append(("limit_buy", kwargs))
        return self._result()

    def submit_sell(self, **kwargs) -> SubmitResult:
        self.calls.append(("market_sell", kwargs))
        return self._result()

    def submit_limit_sell(self, **kwargs) -> SubmitResult:
        self.calls.append(("limit_sell", kwargs))
        return self._result()


def _executor(tmp_path, gateway: _Gateway) -> ManualWidgetOrderExecutor:
    return ManualWidgetOrderExecutor(
        gateway=gateway,
        state_path=tmp_path / "manual-state.json",
        event_dir=tmp_path / "events",
    )


def _execute(executor: ManualWidgetOrderExecutor, **overrides):
    values = {
        "side": "BUY",
        "quantity": 5,
        "client_request_id": "a23279a7-d98e-4cab-9902-dd1a317404b4",
        "reference_price": 230_500,
        "market_venue": "KRX",
        "session": "KRX_REGULAR",
        "snapshot_observed_at": "2026-08-12T09:10:01+09:00",
        "now": datetime(2026, 8, 12, 9, 10, 2, tzinfo=KST),
    }
    values.update(overrides)
    return executor.execute(**values)


def test_buy_splits_odd_quantity_current_leg_first_and_routes_krx_to_sor(tmp_path):
    gateway = _Gateway()
    result = _execute(_executor(tmp_path, gateway))

    assert result["status"] == "accepted"
    assert result["accepted_order_count"] == 2
    assert gateway.calls == [
        (
            "limit_buy",
            {"code": "005930", "qty": 3, "route": "SOR", "price": 230_500},
        ),
        (
            "limit_buy",
            {"code": "005930", "qty": 2, "route": "SOR", "price": 229_000},
        ),
    ]


def test_one_share_buy_submits_only_current_price_leg(tmp_path):
    gateway = _Gateway()
    result = _execute(
        _executor(tmp_path, gateway),
        quantity=1,
        client_request_id="886d1082-4060-4a5d-8fc6-a51cb50eb1ef",
    )

    assert result["expected_order_count"] == 1
    assert gateway.calls[0][1]["qty"] == 1


def test_buy_stops_after_first_rejection_instead_of_leaving_lower_only_order(
    tmp_path,
):
    gateway = _Gateway(reject_at=1)
    result = _execute(_executor(tmp_path, gateway))

    assert result["status"] == "rejected"
    assert len(gateway.calls) == 1
    assert result["actual_order_submitted"] is False


def test_second_buy_rejection_reports_partial_and_preserves_first_order(tmp_path):
    gateway = _Gateway(reject_at=2)
    result = _execute(_executor(tmp_path, gateway))

    assert result["status"] == "partial"
    assert result["accepted_order_count"] == 1
    assert result["orders"][0]["order_no"] == "ORDER-1"
    assert result["orders"][1]["accepted"] is False
    assert result["actual_order_submitted"] is True


def test_second_buy_transport_failure_preserves_first_order_receipt(tmp_path):
    class SecondLegTransportFailure(_Gateway):
        def submit_limit_buy(self, **kwargs) -> SubmitResult:
            self.calls.append(("limit_buy", kwargs))
            if len(self.calls) == 2:
                raise TimeoutError("broker timeout")
            return self._result()

    gateway = SecondLegTransportFailure()
    result = _execute(_executor(tmp_path, gateway))

    assert result["status"] == "ambiguous"
    assert result["accepted_order_count"] == 1
    assert result["orders"][0]["order_no"] == "ORDER-1"
    assert result["orders"][1]["ambiguous"] is True
    assert result["actual_order_submitted"] is True


def test_krx_regular_sell_is_market_on_sor(tmp_path):
    gateway = _Gateway()
    result = _execute(
        _executor(tmp_path, gateway),
        side="SELL",
        quantity=4,
        client_request_id="0216a3b1-a41d-431f-99cd-9fc08cb98502",
    )

    assert result["orders"][0]["order_type"] == "MARKET"
    assert result["orders"][0]["price"] is None
    assert gateway.calls == [
        ("market_sell", {"code": "005930", "qty": 4, "route": "SOR"})
    ]


def test_nxt_sell_is_current_price_limit_on_nxt(tmp_path):
    gateway = _Gateway()
    result = _execute(
        _executor(tmp_path, gateway),
        side="SELL",
        quantity=2,
        client_request_id="de7b511b-f21c-47fd-b34a-46db9fe2dfcf",
        market_venue="NXT",
        session="NXT_AFTERMARKET",
    )

    assert result["orders"][0]["order_type"] == "LIMIT"
    assert gateway.calls == [
        (
            "limit_sell",
            {"code": "005930", "qty": 2, "route": "NXT", "price": 230_500},
        )
    ]


def test_nxt_buy_keeps_nxt_route_for_both_limit_legs(tmp_path):
    gateway = _Gateway()
    result = _execute(
        _executor(tmp_path, gateway),
        quantity=2,
        client_request_id="33de24eb-3dcb-4440-b0ef-b80342fa8860",
        market_venue="NXT",
        session="NXT_PREMARKET",
    )

    assert result["status"] == "accepted"
    assert [call[1]["route"] for call in gateway.calls] == ["NXT", "NXT"]


def test_ambiguous_sell_is_not_reported_as_rejected(tmp_path):
    class AmbiguousGateway(_Gateway):
        def submit_sell(self, **kwargs) -> SubmitResult:
            self.calls.append(("market_sell", kwargs))
            return SubmitResult(
                accepted=False,
                order_no="",
                return_code="0",
                return_msg="missing order number",
                ambiguous=True,
            )

    result = _execute(
        _executor(tmp_path, AmbiguousGateway()),
        side="SELL",
        quantity=1,
        client_request_id="5e1736ab-f9b0-40e5-9af6-74e12a18778b",
    )

    assert result["status"] == "ambiguous"
    assert result["actual_order_submitted"] is None


def test_duplicate_request_returns_persisted_result_without_resubmission(tmp_path):
    gateway = _Gateway()
    executor = _executor(tmp_path, gateway)

    first = _execute(executor)
    second = _execute(executor)

    assert first["status"] == "accepted"
    assert second["duplicate_request"] is True
    assert len(gateway.calls) == 2

    lookup = executor.existing_response(
        client_request_id="a23279a7-d98e-4cab-9902-dd1a317404b4",
        now=datetime(2026, 8, 12, 19, 59, tzinfo=KST),
    )
    assert lookup is not None
    assert lookup["duplicate_request"] is True
    assert lookup["status"] == "accepted"


def test_invalid_or_oversized_quantity_is_rejected_before_gateway(tmp_path):
    gateway = _Gateway()
    executor = _executor(tmp_path, gateway)

    for quantity in (0, 101, True):
        try:
            _execute(
                executor,
                quantity=quantity,
                client_request_id="e1c1eca0-df7f-419f-8011-12dad1ad4d38",
            )
        except ValueError as exc:
            assert str(exc) == "invalid_order_quantity"
        else:
            raise AssertionError("invalid quantity accepted")
    assert gateway.calls == []


def test_corrupt_idempotency_state_fails_closed_before_broker(tmp_path):
    gateway = _Gateway()
    executor = _executor(tmp_path, gateway)
    executor.state_path.write_text("{broken", encoding="utf-8")

    try:
        _execute(executor)
    except RuntimeError as exc:
        assert str(exc) == "manual_order_state_unreadable"
    else:
        raise AssertionError("corrupt idempotency state allowed an order")
    assert gateway.calls == []
