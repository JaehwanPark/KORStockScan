"""Main entry cash/margin source contracts; no account or order I/O."""

import pytest

from src.utils import kiwoom_utils
from src.engine import sniper_state_handlers as handlers


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
