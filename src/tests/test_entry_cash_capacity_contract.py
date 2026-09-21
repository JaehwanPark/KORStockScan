"""Main entry cash/margin source contracts; no account or order I/O."""

import pytest

from src.utils import kiwoom_utils
from src.engine import sniper_state_handlers as handlers


@pytest.mark.parametrize("wait,expected", [(0, 0), (0.4, 0.4), (99, 1.25), (-1, 0)])
def test_source_capacity_bounded_wait_preserves_priority_and_normal_read(monkeypatch, wait, expected):
    calls = []
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous",
                        lambda **kwargs: calls.append(kwargs) or [])
    kiwoom_utils.get_orderable_by_margin_kt00011("fake", "005930", 10000,
        source_only=True, source_read_rate_max_wait_sec=wait)
    assert calls[-1]["request_class"] == "source_only"
    assert calls[-1]["read_rate_max_wait_sec"] == expected
    assert calls[-1]["max_retries"] == 1
    assert calls[-1]["request_timeout"] == (0.15, 0.15)
    kiwoom_utils.get_orderable_by_margin_kt00011("fake", "005930", 10000)
    assert "request_class" not in calls[-1]
    assert "read_rate_max_wait_sec" not in calls[-1]


def test_async_capacity_prefetch_reused_only_after_completion_and_exact_validation(monkeypatch):
    from datetime import datetime, timezone
    handlers._reset_entry_capacity_receipts()
    clock = [1000.0]
    calls = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (code, price))
    def fetch(token, code, unit_price=None, **kwargs):
        calls.append(kwargs)
        assert handlers._read_entry_capacity_snapshot(code, unit_price, source_only=True)["error"] == "capacity_source_inflight"
        clock[0] += 0.4
        return {"return_code": 0, "cash_orderable_contract_status": "valid",
            "capacity_observed_at": datetime.fromtimestamp(clock[0], timezone.utc).isoformat(),
            "capacity_source_sha256": "a" * 64, "requested_stock_code": code,
            "requested_unit_price": unit_price}
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011", fetch)
    try:
        prefetched = handlers._prefetch_entry_capacity_for_async_evaluation("005930", {"curr": 10000}, 1005)
        assert prefetched == {"status": "ready", "reuse_status": "fresh_read"}
        assert calls == [{"source_only": True, "source_read_rate_max_wait_sec": 1.25}]
        assert handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)["capacity_reuse_status"] == "exact_receipt_reused"
        assert len(calls) == 1
        handlers._read_entry_capacity_snapshot("005930", 10001, source_only=True)
        assert len(calls) == 2  # A final quote change cannot reuse the prepared price.
        assert calls[-1] == {"source_only": True}
        clock[0] += 3
        handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)
        assert len(calls) == 3  # Queued/expired evidence never bypasses freshness.
    finally:
        handlers._reset_entry_capacity_receipts()


@pytest.mark.parametrize("price,deadline,expected", [(0, 1005, None), (10000, 1000.2, None),
                                                       (10000, 1000.8, 0.5)])
def test_async_capacity_prefetch_budget_and_failure_are_source_only(monkeypatch, price, deadline, expected):
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    calls = []
    def read(*args, **kwargs):
        calls.append(kwargs)
        raise ValueError("fixture_failure")
    monkeypatch.setattr(handlers, "_read_entry_capacity_snapshot", read)
    result = handlers._prefetch_entry_capacity_for_async_evaluation("005930", {"curr": price}, deadline)
    if expected is None:
        assert result["status"] == "skipped"
        assert not calls
    else:
        assert calls[0]["source_only"] is True
        assert calls[0]["source_read_rate_max_wait_sec"] == pytest.approx(expected)
        assert result == {"status": "source_gap", "reason": "ValueError:fixture_failure"}


def response(**extra):
    return {
        "return_code": 0,
        "entr": "7129629",
        "aplc_rt": "40%",
        "min_ord_alow_amt": "0",
        "min_ord_alowq": "0",
        "profa_40ord_alow_amt": "100000",
        "profa_40ord_alowq": "10",
        **extra,
    }


def test_nonentry_capacity_reuses_exact_receipt_without_new_account_read(monkeypatch):
    from datetime import datetime, timezone
    handlers._reset_entry_capacity_receipts()
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (code, price))
    calls = []
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *args, **kwargs: calls.append(kwargs) or {})
    try:
        read = handlers._read_entry_capacity_snapshot
        assert read("005930", 10000, source_only=True, reuse_only=True)["error"] == "capacity_observation_cache_miss_nonentry"
        assert not calls
        handlers._ENTRY_CAPACITY_RECEIPTS[("005930", 10000)] = {
            "return_code": 0, "cash_orderable_contract_status": "valid",
            "capacity_observed_at": datetime.fromtimestamp(999, timezone.utc).isoformat(),
            "capacity_source_sha256": "a" * 64, "requested_stock_code": "005930",
            "requested_unit_price": 10000,
        }
        assert read("005930", 10000, source_only=True, reuse_only=True)["capacity_reuse_status"] == "exact_receipt_reused"
        assert "error" in read("005930", 10001, source_only=True, reuse_only=True)
        assert not calls
        read("005930", 10000, reuse_only=True)  # Normal sizing never uses this exemption.
        assert len(calls) == 1 and calls[0] == {"unit_price": 10000}
    finally:
        handlers._reset_entry_capacity_receipts()


@pytest.mark.parametrize("age,reused", [(-0.001, False), (2.001, True),
                                      (4.999, True), (5.0, True), (5.001, False)])
def test_nonentry_five_second_reuse_does_not_extend_entry_or_submit(monkeypatch, age, reused):
    from datetime import datetime, timezone
    handlers._reset_entry_capacity_receipts()
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (code, price))
    calls = []
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *args, **kwargs: calls.append(kwargs) or {})
    receipt = {
        "return_code": 0, "cash_orderable_contract_status": "valid",
        "capacity_observed_at": datetime.fromtimestamp(1000 - age, timezone.utc).isoformat(),
        "capacity_source_sha256": "a" * 64, "requested_stock_code": "005930",
        "requested_unit_price": 10000,
    }
    try:
        read = handlers._read_entry_capacity_snapshot
        handlers._ENTRY_CAPACITY_RECEIPTS[("005930", 10000)] = receipt
        result = read("005930", 10000, source_only=True, reuse_only=True)
        assert (result.get("capacity_reuse_status") == "exact_receipt_reused") is reused
        if reused:
            assert result["capacity_observed_at"] == receipt["capacity_observed_at"]
            assert result["capacity_reuse_max_age_sec"] == 5.0
        else:
            assert result["error"] == "capacity_observation_cache_miss_nonentry"
        assert not calls
        assert not handlers._entry_capacity_receipt_valid(receipt, "005930", 10000, 1000)
        read("005930", 10000, source_only=True)  # ENTER_NOW still requires <=2s.
        assert calls == [{"unit_price": 10000, "source_only": True}]
        handlers._ENTRY_CAPACITY_RECEIPTS[("005930", 10000)] = receipt
        read("005930", 10000, reuse_only=True)  # Live sizing never reuses it.
        assert calls[-1] == {"unit_price": 10000}
        assert len(calls) == 2
    finally:
        handlers._reset_entry_capacity_receipts()


@pytest.mark.parametrize("field,value", [
    ("capacity_source_sha256", ""), ("return_code", 3),
    ("cash_orderable_contract_status", "missing"),
    ("requested_stock_code", "000660"), ("requested_unit_price", 10001),
    ("capacity_observed_at", "1970-01-01T00:16:36"),
])
def test_nonentry_extended_age_still_requires_bound_proof(field, value):
    from datetime import datetime, timezone
    receipt = {"return_code": 0, "cash_orderable_contract_status": "valid",
        "capacity_observed_at": datetime.fromtimestamp(996, timezone.utc).isoformat(),
        "capacity_source_sha256": "a" * 64, "requested_stock_code": "005930",
        "requested_unit_price": 10000}
    assert not handlers._entry_capacity_receipt_valid(
        {**receipt, field: value}, "005930", 10000, 1000, nonentry_observation=True)


def test_nonentry_five_second_receipt_reaches_budget_with_original_clock(monkeypatch):
    from datetime import datetime, timezone
    handlers._reset_entry_capacity_receipts()
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "fake")
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(handlers.kiwoom_orders, "get_last_deposit_meta", lambda: {})
    generation = ["account-inventory-1"]
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key",
                        lambda code, price: (generation[0], code, price))
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *a, **kw: pytest.fail("Nonentry must not fetch"))
    observed = datetime.fromtimestamp(996, timezone.utc).isoformat()
    try:
        handlers._ENTRY_CAPACITY_RECEIPTS[(generation[0], "005930", 10000)] = {
            "return_code": 0, "cash_orderable_contract_status": "valid",
            "capacity_observed_at": observed, "capacity_source_sha256": "a" * 64,
            "requested_stock_code": "005930", "requested_unit_price": 10000,
            "deposit": 10000, "cash_only_orderable_amount": 10000,
            "cash_only_orderable_qty": 1,
        }
        resolve = handlers._resolve_scalp_cash_budget_context
        budget = resolve("005930", 10000, 0, source_only=True, reuse_only=True)
        assert budget["kt00011_error"] == ""
        assert budget["cash_orderable_qty_cap"] == 1
        assert budget["kt00011_capacity_observed_at"] == observed
        assert budget["kt00011_capacity_reuse_max_age_sec"] == 5.0
        generation[0] = "account-inventory-2"
        assert resolve("005930", 10000, 0, source_only=True, reuse_only=True)[
            "kt00011_error"] == "capacity_observation_cache_miss_nonentry"
    finally:
        handlers._reset_entry_capacity_receipts()


def test_legacy_preparation_is_coalesced_bounded_and_scope_checked(monkeypatch):
    handlers._reset_entry_capacity_receipts()
    clock = [1000.0]
    generation = ["first"]
    reads = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda stock, strategy: stock.get("sim", False))
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (generation[0], code, price))
    monkeypatch.setattr(handlers, "_prefetch_entry_capacity_for_async_evaluation",
                        lambda *args: reads.append(args) or {"status": "ready"})
    request = handlers._request_entry_capacity_preparation
    try:
        assert not request({"sim": True}, "005930", {"curr": 10000})
        assert not request({"buy_qty": 1}, "005930", {"curr": 10000})
        for _ in range(3):
            assert request({}, "005930", {"curr": 10000})
        assert len(handlers._ENTRY_CAPACITY_PENDING) == 1
        assert not reads  # Main loop cannot wait for or perform broker I/O.
        assert handlers.prepare_pending_entry_capacity() == {"status": "ready"}
        assert reads == [("005930", {"curr": 10000}, 1005.0)]
        assert handlers.prepare_pending_entry_capacity() == {"status": "idle"}
        request({}, "005930", {"curr": 10000})
        generation[0] = "changed"
        assert handlers.prepare_pending_entry_capacity()["reason"] == "expired_or_changed_scope"
        for code in range(8):
            assert request({}, str(code), {"curr": 10000})
        assert not request({}, "extra", {"curr": 10000})
        clock[0] = 1006
        assert handlers.prepare_pending_entry_capacity()["reason"] == "expired_or_changed_scope"
        assert len(reads) == 1
        assert request({}, "fresh", {"curr": 10000})
        assert len(handlers._ENTRY_CAPACITY_PENDING) == 1
    finally:
        handlers._reset_entry_capacity_receipts()


@pytest.mark.parametrize(
    "value,status,parsed",
    [
        (None, "missing", 0),
        ("", "missing", 0),
        ("bad", "invalid", 0),
        (True, "invalid", 0),
        ("1.5", "invalid", 0),
        ("1e3", "invalid", 0),
        ("Infinity", "invalid", 0),
        ("0", "valid_zero", 0),
        ("+000000000000", "valid_zero", 0),
        ("-000000000001", "valid_negative", -1),
        ("+1,000", "valid_positive", 1000),
    ],
)
def test_capacity_preserves_zero_missing_invalid_and_signed_values(
    monkeypatch, value, status, parsed
):
    raw = response(min_ord_alowq=value)
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", lambda **kw: [raw])
    result = kiwoom_utils.get_orderable_by_margin_kt00011("fake", "A005930_AL", 10000)
    assert result["capacity_field_statuses"]["min_ord_alowq"] == status
    assert result["cash_only_orderable_qty"] == parsed
    assert result["cash_orderable_contract_status"] == (
        status if status in {"missing", "invalid"} else "valid"
    )
    assert result["raw"] == raw
    assert result["requested_stock_code"] == "005930"
    assert len(result["capacity_source_sha256"]) == 64


@pytest.mark.parametrize(
    "raw,reason,authorized",
    [
        (response(), "kt00011_applied_margin_tier_one_share_confirmed", True),
        (response(min_ord_alowq=None), "kt00011_error", False),
        (response(min_ord_alow_amt="bad", min_ord_alowq="3"), "kt00011_error", False),
        (
            response(profa_40ord_alowq="1.9"),
            "applied_margin_capacity_contract_invalid",
            False,
        ),
        (response(aplc_rt="100%"), "applied_margin_rate_not_margin_eligible", False),
        (response(aplc_rt="4%0"), "applied_margin_tier_unrecognized", False),
        (
            response(min_ord_alow_amt="-1", min_ord_alowq="-1"),
            "kt00011_applied_margin_tier_one_share_confirmed",
            True,
        ),
        (
            response(min_ord_alow_amt="20000", min_ord_alowq="2"),
            "cash_one_share_capacity_available",
            False,
        ),
    ],
)
def test_cash_parser_to_margin_owner_is_fail_closed_without_disabling_valid_margin(
    monkeypatch, raw, reason, authorized
):
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", lambda **kw: [raw])
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "fake")
    monkeypatch.setattr(handlers.kiwoom_orders, "get_last_deposit_meta", lambda: {})
    budget = handlers._resolve_scalp_cash_budget_context("005930", 10000, 3000000)
    result = handlers._apply_general_entry_margin_budget_authority(
        budget, unit_price=10000
    )
    assert result["general_entry_margin_one_share_authorized"] is authorized
    assert result["general_entry_margin_authority_reason"] == reason
    if budget["kt00011_cash_orderable_contract_status"] in {"missing", "invalid"}:
        assert budget["cash_orderable_qty_cap"] == 0
        assert not handlers._scalping_cash_one_share_authorized(
            budget, unit_price=10000
        )
    fields = handlers._general_entry_margin_budget_log_fields(result)
    assert (
        fields["kt00011_capacity_source_sha256"]
        == budget["kt00011_capacity_source_sha256"]
    )
    assert fields["general_entry_margin_scope"] == "cash_shortfall_one_share_only"
    assert not fields["general_entry_margin_scale_in_allowed"]
    assert fields["general_entry_margin_order_api"] == "kt10000"
    mismatch = handlers._apply_general_entry_margin_budget_authority(
        budget, unit_price=11000
    )
    assert not mismatch["general_entry_margin_one_share_authorized"]


@pytest.mark.parametrize("code", [False, 0.5, "0.5", None, "", "invalid"])
def test_no_fractional_boolean_or_missing_success_code(monkeypatch, code):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **kw: [response(return_code=code)],
    )
    assert kiwoom_utils.get_orderable_by_margin_kt00011("fake", "005930", 10000)[
        "error"
    ]


@pytest.mark.parametrize(
    "rows", [[], [None], ["invalid"], [response(return_code=0.5)], response()]
)
def test_missing_or_invalid_response_never_becomes_uncapped_fallback(monkeypatch, rows):
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", lambda **kw: rows)
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "fake")
    monkeypatch.setattr(handlers.kiwoom_orders, "get_last_deposit_meta", lambda: {})
    budget = handlers._resolve_scalp_cash_budget_context("005930", 10000, 3000000)
    assert budget["kt00011_error"]
    assert budget["cash_orderable_qty_cap"] == 0
    result = handlers._apply_general_entry_margin_budget_authority(
        budget, unit_price=10000
    )
    assert not result["general_entry_margin_one_share_authorized"]


def test_nonfinite_applied_and_unselected_tiers_do_not_escape_source_parser(
    monkeypatch,
):
    raw = response(profa_40ord_alowq="Infinity", profa_20ord_alow_amt="Infinity")
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", lambda **kw: [raw])
    result = kiwoom_utils.get_orderable_by_margin_kt00011("fake", "005930", 10000)
    assert result["applied_orderable_contract_status"] == "invalid"
    assert result["applied_orderable_qty"] == 0
