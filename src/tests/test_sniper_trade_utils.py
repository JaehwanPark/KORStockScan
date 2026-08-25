from datetime import datetime

from src.engine import sniper_trade_utils


def _exact_cancel_ack(*, route="SOR", code="399720", orig="0000001", qty="5"):
    return {
        "return_code": "0",
        "ord_no": "0000999",
        "base_orig_ord_no": "0000001",
        "cncl_qty": qty,
        "broker_route_attempted": True,
        "effective_dmst_stex_tp": route,
        "cancel_request_api_id": "kt10003",
        "cancel_request_code": code,
        "cancel_request_orig_ord_no": orig,
        "cancel_request_qty": "0",
        "cancel_request_route": route,
        "cancel_request_bound": True,
    }


def _pending_sell_stock(*, started_at, session="krx_regular"):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 911,
        "code": "005930",
        "status": "SELL_ORDERED",
        "buy_qty": 5,
    }
    stock.update(
        receipts.build_pending_sell_submit_context_fields(
            stock,
            code="005930",
            requested_qty=5,
            started_at=started_at,
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket=session,
        )
    )
    assert receipts.persist_pending_sell_submit_custody(stock)
    return stock


def _pending_sell_order_row(*, source, order_time="090001", route="SOR"):
    return {
        "source_api": source,
        "trade_date": "20260825",
        "code": "005930",
        "side": "매도",
        "qty": 5,
        "submitted_quantity_source_valid": True,
        "remaining_qty": 5,
        "ord_no": "0000456",
        "stex_tp": route,
        "sor_yn": "Y" if route == "SOR" else "N",
        "raw": {
            "ord_tm": order_time,
            "dmst_stex_tp": route,
            "sor_yn": "Y" if route == "SOR" else "N",
        },
    }


def test_cancel_ack_requires_official_identity_and_local_request_attestation():
    exact = _exact_cancel_ack()
    assert sniper_trade_utils.cancel_response_ack_exact(
        exact,
        intended_route="SOR",
        expected_orig_order_no="0000001",
        expected_code="399720",
        expected_max_qty=5,
    )
    for field_name, invalid_value in (
        ("ord_no", ""),
        ("base_orig_ord_no", ""),
        ("cncl_qty", "0"),
        ("cncl_qty", "6"),
        ("cancel_request_orig_ord_no", "0000002"),
        ("cancel_request_code", "005930"),
        ("cancel_request_route", "NXT"),
        ("cancel_request_bound", False),
    ):
        candidate = dict(exact)
        candidate[field_name] = invalid_value
        assert not sniper_trade_utils.cancel_response_ack_exact(
            candidate,
            intended_route="SOR",
            expected_orig_order_no="0000001",
            expected_code="399720",
            expected_max_qty=5,
        )


def test_pending_sell_blank_order_binds_exact_official_korean_side(monkeypatch):
    started_at = datetime(
        2026, 8, 25, 9, 0, 0, 500_000, tzinfo=sniper_trade_utils._KST
    ).timestamp()
    stock = _pending_sell_stock(started_at=started_at)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_order_reference_snapshot_kt00007_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="kt00007")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="ka10075")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )

    order_no, reason = sniper_trade_utils.resolve_pending_sell_order_no(
        stock,
        "TOKEN",
        now_epoch=started_at + 2,
    )

    assert order_no == "0000456"
    assert reason == "kt00007_plus_ka10075_exact_unique"
    assert stock["sell_odno"] == "0000456"


def test_pending_sell_blank_order_rejects_prior_second(monkeypatch):
    started_at = datetime(
        2026, 8, 25, 9, 0, 0, 500_000, tzinfo=sniper_trade_utils._KST
    ).timestamp()
    stock = _pending_sell_stock(started_at=started_at)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_order_reference_snapshot_kt00007_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="kt00007", order_time="085959")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="ka10075")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )

    order_no, reason = sniper_trade_utils.resolve_pending_sell_order_no(
        stock,
        "TOKEN",
        now_epoch=started_at + 2,
    )

    assert order_no is None
    assert reason == "pending_sell_order_unique_match_missing"
    assert "sell_odno" not in stock


def test_pending_sell_blank_order_rejects_cross_snapshot_route_conflict(monkeypatch):
    started_at = datetime(
        2026, 8, 25, 9, 0, 0, 500_000, tzinfo=sniper_trade_utils._KST
    ).timestamp()
    stock = _pending_sell_stock(started_at=started_at)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_order_reference_snapshot_kt00007_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="kt00007", route="KRX")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [_pending_sell_order_row(source="ka10075", route="NXT")],
            {
                "request_succeeded": True,
                "normalization_contract_complete": True,
            },
        ),
    )

    order_no, reason = sniper_trade_utils.resolve_pending_sell_order_no(
        stock,
        "TOKEN",
        now_epoch=started_at + 2,
    )

    assert order_no is None
    assert reason == "pending_sell_order_unique_match_missing"
    assert "sell_odno" not in stock


def test_pending_sell_blank_order_rejects_runtime_context_tamper_before_queries(
    monkeypatch,
):
    started_at = datetime(
        2026, 8, 25, 9, 0, 0, 500_000, tzinfo=sniper_trade_utils._KST
    ).timestamp()
    stock = _pending_sell_stock(started_at=started_at)
    stock["sell_submit_requested_qty"] = 4
    snapshot_calls = []
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_order_reference_snapshot_kt00007_with_meta",
        lambda *args, **kwargs: snapshot_calls.append("kt00007"),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: snapshot_calls.append("ka10075"),
    )

    order_no, reason = sniper_trade_utils.resolve_pending_sell_order_no(
        stock,
        "TOKEN",
        now_epoch=started_at + 2,
    )

    assert order_no is None
    assert reason.startswith("pending_sell_order_context_invalid:")
    assert snapshot_calls == []
    assert "sell_odno" not in stock


def test_cancel_order_retries_resolved_krx_after_sor_mismatch(monkeypatch):
    cancel_calls = []

    def fake_cancel(**kwargs):
        cancel_calls.append(kwargs)
        if len(cancel_calls) == 1:
            return {
                "return_code": "2000",
                "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
            }
        return {**_exact_cancel_ack(route="KRX"), "return_msg": "정상"}

    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders, "send_cancel_order", fake_cancel
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "0000001",
                "remaining_qty": 1,
                "stex_tp": "1",
                "stex_tp_txt": "KRX",
                "sor_yn": "N",
            }
        ],
    )

    result = sniper_trade_utils.send_cancel_order_with_exchange_retry(
        code="399720",
        orig_ord_no="0000001",
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
        lambda **kwargs: (
            cancel_calls.append(kwargs)
            or {
                "return_code": "2000",
                "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
            }
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "0000001",
                "remaining_qty": 1,
                "stex_tp": "1",
                "stex_tp_txt": "S-KRX",
                "sor_yn": "Y",
            }
        ],
    )

    result = sniper_trade_utils.send_cancel_order_with_exchange_retry(
        code="399720",
        orig_ord_no="0000001",
        token="TOKEN",
        qty=0,
    )

    assert result["return_code"] == "2000"
    assert [call["dmst_stex_tp"] for call in cancel_calls] == ["SOR"]


def test_existing_sell_without_pending_generation_never_cancels_or_replaces(
    monkeypatch,
):
    cancel_calls = []

    def fake_cancel(**kwargs):
        cancel_calls.append(kwargs)
        if len(cancel_calls) == 1:
            return {
                "return_code": "2000",
                "return_msg": "[2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
            }
        return {
            **_exact_cancel_ack(route="NXT", qty="1"),
            "return_msg": "정상",
        }

    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders, "send_cancel_order", fake_cancel
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *args, **kwargs: [
            {
                "ord_no": "0000001",
                "remaining_qty": 1,
                "stex_tp": "2",
                "stex_tp_txt": "NXT",
                "sor_yn": "N",
            }
        ],
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([{"code": "399720", "qty": 1}], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda seconds: None)

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="0000001",
        token="TOKEN",
        expected_qty=1,
    )

    assert remaining == 0
    assert remaining.confirmation_state == "unknown"
    assert remaining.source == "sell_cancel_pending_generation_required"
    assert cancel_calls == []


def test_pending_sell_cancel_does_not_issue_uncustodied_sor_route_retry(monkeypatch):
    started_at = datetime(
        2026, 8, 25, 9, 0, 0, 500_000, tzinfo=sniper_trade_utils._KST
    ).timestamp()
    stock = _pending_sell_stock(started_at=started_at)
    stock["sell_odno"] = "0000001"
    cancel_calls = []
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "2000",
            "return_msg": "[571412] SOR route mismatch",
        },
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [{"code": "005930", "ord_no": "0000001"}],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="005930",
        orig_ord_no="0000001",
        token="TOKEN",
        expected_qty=5,
        target_stock=stock,
    )

    assert remaining == 0
    assert remaining.source == "sell_order_still_open"
    assert len(cancel_calls) == 1
    assert cancel_calls[0]["dmst_stex_tp"] == "SOR"


def test_confirm_cancel_or_reload_remaining_sums_all_venue_rows(monkeypatch):
    monkeypatch.setattr(
        sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **kwargs: _exact_cancel_ack(),
    )
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: (
            [
                {"code": "399720", "qty": 2},
                {"code": "399720", "qty": 3},
            ],
            {"KRX", "NXT"},
        ),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="",
        token="TOKEN",
        expected_qty=5,
    )

    assert remaining == 5
    assert remaining.confirmation_state == "confirmed_positive"


def test_confirm_cancel_or_reload_remaining_rejects_non_integer_broker_quantity(
    monkeypatch,
):
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": "005930", "qty": "1e2"}], {"KRX", "NXT"}),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        "005930", "", "token", 100
    )

    assert int(remaining) == 0
    assert remaining.confirmation_state == "unknown"
    assert remaining.source == "kt00018_inventory_quantity_malformed"
    assert remaining.successful_exchanges == ("KRX", "NXT")


def test_confirm_cancel_or_reload_remaining_requires_pending_generation_before_cancel(
    monkeypatch,
):
    inventory_calls = []
    monkeypatch.setattr(
        sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **kwargs: {
            "return_code": "2000",
            "return_msg": "cancel state unknown",
        },
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: (
            inventory_calls.append(token) or ([{"code": "399720", "qty": 8}], {"KRX"})
        ),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="0000001",
        token="TOKEN",
        expected_qty=10,
    )

    assert remaining == 0
    assert remaining.confirmation_state == "unknown"
    assert remaining.source == "sell_cancel_pending_generation_required"
    assert inventory_calls == []


def test_confirm_cancel_or_reload_remaining_never_reuses_expected_qty_on_lookup_gap(
    monkeypatch,
):
    monkeypatch.setattr(
        sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **kwargs: _exact_cancel_ack(),
    )
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: (_ for _ in ()).throw(RuntimeError("inventory unavailable")),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="",
        token="TOKEN",
        expected_qty=10,
    )

    assert remaining == 0
    assert remaining.confirmation_state == "unknown"
    assert remaining.source == "inventory_lookup_failed"


def test_confirm_cancel_or_reload_remaining_distinguishes_verified_all_venue_zero(
    monkeypatch,
):
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([], {"KRX", "NXT"}),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code="399720",
        orig_ord_no="",
        token="TOKEN",
        expected_qty=10,
    )

    assert remaining == 0
    assert remaining.confirmation_state == "verified_zero"
    assert remaining.source == "kt00018_all_venues_position_absent"


def test_confirm_cancel_never_queries_inventory_without_pending_generation(
    monkeypatch,
):
    inventory_calls = []
    monkeypatch.setattr(
        sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **kwargs: _exact_cancel_ack(),
    )
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [{"code": "399720", "ord_no": "0000001", "remaining_qty": 5}],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda token: inventory_calls.append(token)
        or ([{"code": "399720", "qty": 5}], {"KRX", "NXT"}),
    )

    remaining = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        "399720",
        "0000001",
        "TOKEN",
        5,
    )

    assert remaining.confirmation_state == "unknown"
    assert remaining.source == "sell_cancel_pending_generation_required"
    assert inventory_calls == []


def test_confirm_cancel_reuses_durable_ack_then_waits_for_terminal_absence(
    monkeypatch,
):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 91,
        "code": "399720",
        "name": "ACK",
        "status": "SELL_ORDERED",
        "buy_qty": 5,
        "sell_odno": "0000001",
    }
    stock.update(
        receipts.build_pending_sell_submit_context_fields(
            stock,
            code="399720",
            requested_qty=5,
            started_at=sniper_trade_utils.time.time(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    assert receipts.persist_pending_sell_submit_custody(stock)
    cancel_calls = []
    snapshots = iter(
        (
            (
                [
                    {
                        "code": "399720",
                        "ord_no": "0000001",
                        "remaining_qty": 5,
                    }
                ],
                {
                    "request_succeeded": True,
                    "normalization_contract_complete": True,
                },
            ),
            (
                [],
                {
                    "request_succeeded": True,
                    "normalization_contract_complete": True,
                },
            ),
        )
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs) or _exact_cancel_ack(),
    )
    monkeypatch.setattr(sniper_trade_utils.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: next(snapshots),
    )
    monkeypatch.setattr(
        sniper_trade_utils.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": "399720", "qty": 5}], {"KRX", "NXT"}),
    )

    first = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        "399720",
        "0000001",
        "TOKEN",
        5,
        target_stock=stock,
    )
    second = sniper_trade_utils.confirm_cancel_or_reload_remaining(
        "399720",
        "0000001",
        "TOKEN",
        5,
        target_stock=stock,
    )

    assert first.confirmation_state == "unknown"
    assert first.source == "sell_order_still_open"
    assert second.confirmation_state == "unknown"
    assert second.source == "cancel_terminal_release_required"
    assert int(second) == 0
    assert len(cancel_calls) == 1
    assert receipts.pending_sell_cancel_ack_exact(
        stock,
        code="399720",
        order_no="0000001",
    )


def test_live_runtime_wrappers_forward_sell_custody_keywords(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as runtime

    target = {"id": 1, "code": "123456"}
    confirm_calls = []
    exit_calls = []
    monkeypatch.setattr(
        runtime.sniper_trade_utils,
        "confirm_cancel_or_reload_remaining",
        lambda *args, **kwargs: confirm_calls.append((args, kwargs)) or 0,
    )
    monkeypatch.setattr(
        runtime.sniper_trade_utils,
        "send_exit_best_ioc",
        lambda *args, **kwargs: exit_calls.append((args, kwargs)) or {},
    )

    runtime._confirm_cancel_or_reload_remaining(
        "123456",
        "0000001",
        "TOKEN",
        3,
        target_stock=target,
    )
    runtime._send_exit_best_ioc(
        "123456",
        3,
        "TOKEN",
        dmst_stex_tp="NXT",
        reason_type="LOSS",
        strategy="SCALPING",
        bypass_open_time_block=True,
    )

    assert confirm_calls == [
        (("123456", "0000001", "TOKEN", 3), {"target_stock": target})
    ]
    assert exit_calls == [
        (
            ("123456", 3, "TOKEN"),
            {
                "dmst_stex_tp": "NXT",
                "reason_type": "LOSS",
                "strategy": "SCALPING",
                "bypass_open_time_block": True,
            },
        )
    ]
