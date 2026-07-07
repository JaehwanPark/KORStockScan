from src.engine import sniper_trade_utils


def test_cancel_order_retries_resolved_krx_after_sor_mismatch(monkeypatch):
    cancel_calls = []

    def fake_cancel(**kwargs):
        cancel_calls.append(kwargs)
        if len(cancel_calls) == 1:
            return {
                "return_code": "2000",
                "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
            }
        return {"return_code": "0", "ord_no": "C1", "return_msg": "정상"}

    monkeypatch.setattr(sniper_trade_utils.kiwoom_orders, "send_cancel_order", fake_cancel)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "O1",
                "remaining_qty": 1,
                "stex_tp": "1",
                "stex_tp_txt": "KRX",
                "sor_yn": "N",
            }
        ],
    )

    result = sniper_trade_utils.send_cancel_order_with_exchange_retry(
        code="399720",
        orig_ord_no="O1",
        token="TOKEN",
        qty=0,
    )

    assert result["return_code"] == "0"
    assert [call["dmst_stex_tp"] for call in cancel_calls] == ["SOR", "KRX"]


def test_cancel_order_does_not_retry_when_snapshot_still_sor(monkeypatch):
    cancel_calls = []

    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "2000",
            "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
        },
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "O1",
                "remaining_qty": 1,
                "stex_tp": "1",
                "stex_tp_txt": "S-KRX",
                "sor_yn": "Y",
            }
        ],
    )

    result = sniper_trade_utils.send_cancel_order_with_exchange_retry(
        code="399720",
        orig_ord_no="O1",
        token="TOKEN",
        qty=0,
    )

    assert result["return_code"] == "2000"
    assert [call["dmst_stex_tp"] for call in cancel_calls] == ["SOR"]


def test_confirm_cancel_or_reload_remaining_uses_exchange_retry(monkeypatch):
    cancel_calls = []

    def fake_cancel(**kwargs):
        cancel_calls.append(kwargs)
        if len(cancel_calls) == 1:
            return {
                "return_code": "2000",
                "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
            }
        return {"return_code": "0", "ord_no": "C1", "return_msg": "정상"}

    monkeypatch.setattr(sniper_trade_utils.kiwoom_orders, "send_cancel_order", fake_cancel)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "O1",
                "remaining_qty": 1,
                "stex_tp": "2",
                "stex_tp_txt": "NXT",
                "sor_yn": "N",
            }
        ],
    )
    monkeypatch.setattr(sniper_trade_utils.kiwoom_orders, "get_my_inventory", lambda token: ([{"code": "399720", "qty": 1}], None))
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda seconds: None)

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="O1",
        token="TOKEN",
        expected_qty=1,
    )

    assert remaining == 1
    assert [call["dmst_stex_tp"] for call in cancel_calls] == ["SOR", "NXT"]
