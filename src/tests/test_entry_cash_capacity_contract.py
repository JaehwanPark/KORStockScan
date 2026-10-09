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


def test_source_capacity_rate_deferral_is_not_reported_as_empty_broker_response(monkeypatch):
    calls = []
    def fetch(**kwargs):
        calls.append(kwargs)
        return ([], {"read_rate_control_status": "deferred",
                     "read_rate_control_reason": "shared_read_rate_wait_budget_exhausted",
                     "request_attempt_count": 0})
    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fetch)
    source = kiwoom_utils.get_orderable_by_margin_kt00011(
        "fake", "005930", 10000, source_only=True)
    assert calls[-1]["return_meta"] is True
    assert source == {"error": "kt00011_source_read_deferred:shared_read_rate_wait_budget_exhausted"}
    kiwoom_utils.get_orderable_by_margin_kt00011("fake", "005930", 10000)
    assert "return_meta" not in calls[-1]



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
        assert calls == [{"source_only": True, "source_read_rate_max_wait_sec": 1.25,
                          "request_purpose": "entry_capacity_prefetch", "read_meta": {}}]
        assert handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)["capacity_reuse_status"] == "exact_receipt_reused"
        assert len(calls) == 1
        handlers._read_entry_capacity_snapshot("005930", 10001, source_only=True)
        assert len(calls) == 2  # A final quote change cannot reuse the prepared price.
        assert calls[-1] == {"source_only": True, "request_purpose": "entry_operating_observation", "read_meta": {}}
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
        assert len(calls) == 1 and calls[0] == {"unit_price": 10000, "request_purpose": "entry_live_sizing", "read_meta": {}}
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
        assert calls == [{"unit_price": 10000, "source_only": True,
                          "request_purpose": "entry_operating_observation", "read_meta": {}}]
        handlers._ENTRY_CAPACITY_RECEIPTS[("005930", 10000)] = receipt
        read("005930", 10000, reuse_only=True)  # Live sizing never reuses it.
        assert calls[-1] == {"unit_price": 10000, "request_purpose": "entry_live_sizing", "read_meta": {}}
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


def _capacity_context(stock, code):
    import time
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalContext
    from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
    generation = ScannerGeneration(code=code, promotion_id='test', revision=1,
        record_id=1, venue='SOR', promotion_epoch=time.time(), attach_epoch=time.time(),
        observed_price=10000, source_signature='fixture')
    return ScannerAsyncEvalContext.create(generation=generation, cache_key='source',
        submitted_epoch=time.time(), deadline_epoch=time.time()+5,
        stock_snapshot=stock, ws_snapshot={'curr': 10000},
        state_version=handlers._scanner_async_entry_state_version(stock))


def test_legacy_preparation_is_coalesced_bounded_and_scope_checked(monkeypatch):
    handlers._reset_entry_capacity_receipts()
    clock = [1000.0]
    generation = ["first"]
    reads = []
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda stock, strategy: stock.get("sim", False))
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (generation[0], code, price))
    monkeypatch.setattr(handlers, "_prefetch_entry_capacity_for_async_evaluation",
                        lambda *args, **kwargs: reads.append(args) or {"status": "ready"})
    def request(stock, code, ws):
        return handlers._request_entry_capacity_preparation(stock, code, ws,
            context=_capacity_context(stock, code))
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


def test_pending_preparation_replaces_obsolete_price_even_at_queue_capacity(monkeypatch):
    handlers._reset_entry_capacity_receipts()
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (code, price))
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    try:
        for code in range(8):
            assert handlers._request_entry_capacity_preparation({}, str(code), {"curr": 10000}, context=_capacity_context({}, str(code)))
        assert handlers._request_entry_capacity_preparation({}, '0', {"curr": 10001}, context=_capacity_context({}, '0'))
        assert len(handlers._ENTRY_CAPACITY_PENDING) == 8
        assert ('0', 10000) not in handlers._ENTRY_CAPACITY_PENDING
        assert ('0', 10001) in handlers._ENTRY_CAPACITY_PENDING
        assert not handlers._request_entry_capacity_preparation({}, 'extra', {"curr": 10000})
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


@pytest.fixture
def capacity_runtime(monkeypatch):
    from datetime import datetime, timezone
    handlers._reset_entry_capacity_receipts()
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda code, price: (code, price))
    monkeypatch.setattr(handlers, "log_info", lambda *args: None)
    def receipt(code="005930", price=10000):
        return {"return_code": 0, "cash_orderable_contract_status": "valid",
                "capacity_observed_at": datetime.now(timezone.utc).isoformat(),
                "capacity_source_sha256": "a" * 64,
                "requested_stock_code": code, "requested_unit_price": price}
    yield receipt
    handlers._reset_entry_capacity_receipts()


def test_preparation_join_and_frozen_observer_use_one_http(monkeypatch, capacity_runtime):
    import threading, time
    entered, release = threading.Event(), threading.Event()
    calls = []
    def fetch(token, code, unit_price=None, **kw):
        calls.append(kw);entered.set();assert release.wait(1)
        return capacity_runtime(code, unit_price)
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011", fetch)
    result = []
    owner = threading.Thread(target=lambda: result.append(handlers._prefetch_entry_capacity_for_async_evaluation(
        "005930", {"curr": 10000}, time.time()+2)))
    owner.start();assert entered.wait(1)
    frozen = handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)
    assert frozen["error"] == "capacity_source_inflight"
    follower = threading.Thread(target=lambda: result.append(handlers._prefetch_entry_capacity_for_async_evaluation(
        "005930", {"curr": 10000}, time.time()+2)))
    follower.start();release.set();owner.join(2);follower.join(2)
    assert not owner.is_alive() and not follower.is_alive()
    assert len(calls)==1 and all(r["status"]=="ready" for r in result)
    assert not handlers._ENTRY_CAPACITY_EVENTS and not handlers._ENTRY_CAPACITY_SOURCE_INFLIGHT


def test_changed_price_without_demand_does_not_queue_second_http(monkeypatch, capacity_runtime):
    import threading,time
    entered,release=threading.Event(),threading.Event();calls=[]
    def fetch(token,code,unit_price=None,**kw):
        calls.append(unit_price);entered.set();assert release.wait(1)
        return capacity_runtime(code,unit_price)
    monkeypatch.setattr(kiwoom_utils,"get_orderable_by_margin_kt00011",fetch)
    monkeypatch.setattr(handlers,"_is_any_simulated_position",lambda *a:False)
    t=threading.Thread(target=lambda:handlers._prefetch_entry_capacity_for_async_evaluation("005930",{"curr":10000},time.time()+2))
    t.start();assert entered.wait(1)
    new=handlers._prefetch_entry_capacity_for_async_evaluation("005930",{"curr":10001},time.time()+2)
    assert new["status"]=="source_gap" and calls==[10000]
    assert ("005930",10001) not in handlers._ENTRY_CAPACITY_PENDING
    release.set();t.join(2)
    assert handlers.prepare_pending_entry_capacity()["status"]=="idle"
    assert calls==[10000]


def test_required_read_never_joins_or_reuses_source_preparation(monkeypatch, capacity_runtime):
    import threading,time
    entered,release=threading.Event(),threading.Event();calls=[]
    def fetch(token,code,unit_price=None,**kw):
        calls.append(kw)
        if kw.get("source_only"):entered.set();assert release.wait(1)
        return capacity_runtime(code,unit_price)
    monkeypatch.setattr(kiwoom_utils,"get_orderable_by_margin_kt00011",fetch)
    t=threading.Thread(target=lambda:handlers._prefetch_entry_capacity_for_async_evaluation("005930",{"curr":10000},time.time()+2))
    t.start();assert entered.wait(1)
    assert handlers._read_entry_capacity_snapshot("005930",10000)["capacity_reuse_status"]=="fresh_read"
    assert len(calls)==2 and "source_only" not in calls[1]
    release.set();t.join(2)
    assert not handlers._ENTRY_CAPACITY_EVENTS


def test_join_deadline_does_not_retry_failed_or_late_owner(monkeypatch, capacity_runtime):
    import threading,time
    entered,release=threading.Event(),threading.Event();calls=[]
    def fetch(*a,**kw):
        calls.append(kw);entered.set();assert release.wait(1);return {}
    monkeypatch.setattr(kiwoom_utils,"get_orderable_by_margin_kt00011",fetch)
    t=threading.Thread(target=lambda:handlers._read_entry_capacity_snapshot("005930",10000,source_only=True))
    t.start();assert entered.wait(1)
    started=time.time()
    r=handlers._prefetch_entry_capacity_for_async_evaluation("005930",{"curr":10000},time.time()+.35)
    assert r["status"]=="source_gap" and time.time()-started<.15
    assert len(calls)==1
    release.set();t.join(2)
    assert not handlers._ENTRY_CAPACITY_INFLIGHT


def test_capacity_read_diagnostics_failure_never_changes_outcome(monkeypatch, capacity_runtime):
    monkeypatch.setattr(handlers,"log_info",lambda *a:(_ for _ in ()).throw(OSError("fixture")))
    monkeypatch.setattr(kiwoom_utils,"get_orderable_by_margin_kt00011",lambda *a,**kw:capacity_runtime())
    assert handlers._read_entry_capacity_snapshot("005930",10000,source_only=True)["return_code"]==0


def test_timeout_http_count_is_not_zero_or_success(monkeypatch):
    import requests
    from src.utils.kiwoom_read_request_control import ReadRequestAdmission
    class Coordinator:
        def acquire(self, **kw):
            return ReadRequestAdmission(
                admitted=True, reason="admitted", request_class=kw["request_class"],
                request_owner=kw["request_owner"], api_id=kw["api_id"],
                request_code=kw["request_code"], pid=0, waited_sec=0,
                requests_in_window_before=0, effective_limit=4, max_limit=5,
                window_sec=1, cooldown_remaining_sec=0, scope_digest="scope")
    monkeypatch.setattr(kiwoom_utils,"resolve_kiwoom_request_token",lambda t:t)
    monkeypatch.setattr(kiwoom_utils.requests,"post",lambda *a,**kw:(_ for _ in ()).throw(requests.exceptions.ReadTimeout()))
    _,meta=kiwoom_utils._fetch_kiwoom_api_continuous_transport("https://api.kiwoom.com/api/dostk/acnt", "fake", "kt00011", {"stk_cd":"005930"},max_retries=1,return_meta=True,read_rate_coordinator=Coordinator())
    assert meta["request_attempt_count"]==1
    assert meta["first_http_started_epoch"]>0 and meta.get("last_http_received_epoch") is None


def test_deposit_delivery_diagnostics_do_not_repeat_exact_source_reads(monkeypatch, capacity_runtime):
    from src.trading.order import owner_custody_registry
    import hashlib

    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", ORIGINAL_CAPACITY_KEY)
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "fixture-token")
    monkeypatch.setattr(kiwoom_utils, "_market_data_cache_scope", lambda _: ("token-hash", "fixture", "2026-10-02"))
    monkeypatch.setattr(owner_custody_registry, "broker_account_key", lambda: "fixture-account")
    monkeypatch.setattr(handlers, "_scale_in_budget_inventory_signature", lambda: "inventory")
    receipt = {"generation": "b" * 64, "observed_epoch": 1,
               "scope_sha256": hashlib.sha256(b"token:fixture-token").hexdigest(), "raw_amount": 10000}
    meta = {"source": "api_fresh", "fallback_used": False, "amount": 10000,
            "raw_amount": 10000, "deposit_source_receipt": receipt}
    monkeypatch.setattr(handlers.kiwoom_orders, "get_last_deposit_meta", lambda: dict(meta))
    calls = []
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *a, **kw: calls.append(kw) or capacity_runtime())
    outputs = []
    for index in range(10):
        meta.update(source="api_fresh" if index == 0 else "loop_cache", cache_hit=bool(index), age_sec=index / 100)
        outputs.append(handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True))
    assert len(calls) == 1
    assert len({row["capacity_observed_at"] for row in outputs}) == 1
    assert len({row["capacity_source_sha256"] for row in outputs}) == 1
    receipt["generation"] = "c" * 64  # Same cash amount, genuinely new broker receipt.
    handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)
    assert len(calls) == 2


ORIGINAL_CAPACITY_KEY = handlers._entry_capacity_receipt_key


@pytest.mark.parametrize("index,new_value", [
    (0, ("new-token", "origin", "day")), (1, "new-account"), (3, 10001),
    (4, "new-inventory-custody"), (5, "new-deposit-floor-generation"),
])
def test_scope_changes_cannot_reuse_capacity_or_convert_other_price(monkeypatch, capacity_runtime, index, new_value):
    key = [("token", "origin", "day"), "account", "005930", 10000, "inventory", "deposit"]
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", lambda *a: tuple(key))
    calls = []
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *a, **kw: calls.append(kw) or capacity_runtime(price=kw["unit_price"]))
    handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)
    key[index] = new_value
    assert "error" in handlers._read_entry_capacity_snapshot("005930", key[3], source_only=True, reuse_only=True)
    assert len(calls) == 1
    handlers._read_entry_capacity_snapshot("005930", key[3], source_only=True)
    assert len(calls) == 2


def test_capacity_telemetry_keeps_denominators_and_exact_evidence(monkeypatch, capacity_runtime):
    import json
    logs = []
    monkeypatch.setattr(handlers, "log_info", logs.append)
    def fetch(*args, **kwargs):
        kwargs["read_meta"].update(request_attempt_count=1, admission_attempt_count=1,
                                   first_http_started_epoch=1, last_http_received_epoch=2)
        return capacity_runtime()
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011", fetch)
    for action in ("ENTER_NOW", "BLOCK", "RECHECK"):
        handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True,
            reuse_only=action != "ENTER_NOW", correlation_id="attempt:" + action,
            diagnostic_context={"mechanistic_action": action, "broker_route": "KRX"})
    rows = [json.loads(line.split("] ", 1)[1]) for line in logs]
    assert [row["result"] for row in rows] == ["fresh_success", "exact_reused", "exact_reused"]
    assert [row["http_attempts"] for row in rows] == [1, 0, 0]
    assert rows[-1]["purpose_totals"]["logical_requests"] == 3
    assert rows[-1]["purpose_totals"]["exact_usable"] == 3
    assert rows[-1]["purpose_totals"]["http_attempts"] == 1
    assert all(row["capacity_source_sha256"] == "a" * 64 for row in rows)
    assert len({row["request_id"] for row in rows}) == 3
    assert all(row["correlation_id"] == "attempt:" + row["mechanistic_action"] for row in rows)


def test_capacity_exception_cleans_up_and_is_not_cached_as_success(monkeypatch, capacity_runtime):
    import json
    logs = []
    monkeypatch.setattr(handlers, "log_info", logs.append)
    def failed(*args, **kwargs):
        raise OSError("mock source failure")
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011", failed)
    with pytest.raises(OSError):
        handlers._read_entry_capacity_snapshot("005930", 10000, source_only=True)
    assert not handlers._ENTRY_CAPACITY_EVENTS
    assert not handlers._ENTRY_CAPACITY_SOURCE_INFLIGHT
    assert not handlers._ENTRY_CAPACITY_INFLIGHT
    assert not handlers._ENTRY_CAPACITY_RECEIPTS
    row = json.loads(logs[-1].split("] ", 1)[1])
    assert row["result"] == "http_failed"
    assert row["http_attempts"] is None  # Unknown attempts are never asserted to be zero.


def test_preparation_rechecks_deadline_after_scope_work(monkeypatch, capacity_runtime):
    clock = [1000.0]
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    def slow_key(code, price):
        clock[0] += .3
        return (code, price)
    monkeypatch.setattr(handlers, "_entry_capacity_receipt_key", slow_key)
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *a, **kw: pytest.fail("Expired preparation must not start HTTP"))
    result = handlers._prefetch_entry_capacity_for_async_evaluation("005930", {"curr": 10000}, 1000.5)
    assert result == {"status": "source_gap", "reason": "capacity_preparation_deadline_deferred"}
    assert not handlers._ENTRY_CAPACITY_INFLIGHT


def test_explicit_unsupported_route_skips_only_capacity_preparation(monkeypatch, capacity_runtime):
    import time
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011",
                        lambda *a, **kw: pytest.fail("Explicit unsupported replay route needs no capacity source"))
    result = handlers._prefetch_entry_capacity_for_async_evaluation("005930", {"curr": 10000}, time.time() + 1,
        diagnostic_context={"broker_route": "unknown-route", "effective_venue": "KRX", "session_bucket": "KRX_REGULAR"})
    assert result == {"status": "skipped", "reason": "explicit_unsupported_operating_route"}


def test_late_preparation_response_is_not_ready_for_expired_worker(monkeypatch, capacity_runtime):
    clock = [1000.0]
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    def late_response(*args, **kwargs):
        clock[0] = 1001.1
        return {"return_code": 0, "cash_orderable_contract_status": "valid",
                "capacity_observed_at": "1970-01-01T00:16:41+00:00",
                "capacity_source_sha256": "a" * 64,
                "requested_stock_code": "005930", "requested_unit_price": 10000}
    monkeypatch.setattr(kiwoom_utils, "get_orderable_by_margin_kt00011", late_response)
    result = handlers._prefetch_entry_capacity_for_async_evaluation("005930", {"curr": 10000}, 1001)
    assert result == {"status": "source_gap", "reason": "capacity_preparation_deadline_deferred"}
    # The valid receipt keeps its original clock for a subsequent natural frame.
    assert handlers._ENTRY_CAPACITY_RECEIPTS[("005930", 10000)]["capacity_observed_at"].endswith("00:16:41+00:00")
    assert not handlers._ENTRY_CAPACITY_INFLIGHT


def test_capacity_totals_preserve_out_of_order_midnight_completions(capacity_runtime):
    def row(day):
        return {"date": day, "purpose": "entry_operating_observation", "http_attempts": 1,
                "admission_attempts": 1, "result": "fresh_success"}
    totals = handlers._entry_capacity_read_totals
    assert totals(row("2026-10-02"))["logical_requests"] == 1
    assert totals(row("2026-10-03"))["logical_requests"] == 1
    assert totals(row("2026-10-02"))["logical_requests"] == 2
    assert totals(row("2026-10-03"))["logical_requests"] == 2
    totals(row("2026-10-04"))
    assert totals(row("2026-10-02"))["outside_retained_day_window"] is True
    assert totals(row("2026-10-04"))["logical_requests"] == 2
    assert len(handlers._ENTRY_CAPACITY_STATS["days"]) == 2
