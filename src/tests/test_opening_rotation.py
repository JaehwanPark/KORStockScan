from datetime import datetime
import inspect
from threading import Event, Thread
from types import SimpleNamespace

import pandas as pd
import pytest

from src.engine.scalping.opening_rotation import (
    EntryConfig,
    ExitConfig,
    OpeningRotationRuntimePolicy,
    POSITION_TAG,
    WINDOW_VERSION,
    entry_time_bucket,
    entry_time_bucket_labels,
    entry_window_version,
    evaluate_entry as _evaluate_entry_impl,
    evaluate_exit,
    is_krx_regular_scope,
    is_watch_candidate,
    is_watch_source_scope,
    load_active_runtime_policy,
)
from src.engine import sniper_state_handlers as handlers
from src.engine import sniper_execution_receipts
from src.engine import sniper_sync
from src.engine.scalping import opening_rotation_backtest as rotation_backtest
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
from src.utils import kiwoom_utils

_ORIGINAL_SCANNER_RUNTIME_EVENT_VENUE_FIELDS = (
    handlers._scanner_runtime_event_venue_fields
)


@pytest.fixture(autouse=True)
def _active_krx_opening_policy_for_runtime_unit_tests(monkeypatch):
    """Keep legacy unit fixtures explicit about the reviewed PREOPEN state."""

    monkeypatch.setattr(handlers, "OPENING_ROTATION_RETIRED", False)
    monkeypatch.setattr(
        handlers,
        "load_active_opening_rotation_runtime_policy",
        lambda: OpeningRotationRuntimePolicy(),
    )
    original = _ORIGINAL_SCANNER_RUNTIME_EVENT_VENUE_FIELDS

    def _runtime_venue_fields(stock):
        fields = original(stock)
        if fields.get("effective_venue") != "UNKNOWN":
            return fields
        return {
            **fields,
            "venue": "KRX",
            "effective_venue": "KRX",
            "venue_resolution": "unit_test_explicit_krx_regular_fixture",
            "venue_source_quality_status": "pass",
            "venue_unknown_reviewed_reason": "not_applicable",
            "market_session_bucket": "krx_regular",
        }

    monkeypatch.setattr(
        handlers,
        "_scanner_runtime_event_venue_fields",
        _runtime_venue_fields,
    )


def test_opening_rotation_retirement_disables_runtime_entry_and_final_submit(
    monkeypatch,
):
    monkeypatch.setattr(handlers, "OPENING_ROTATION_RETIRED", True)
    assert handlers._opening_rotation_entry_config().enabled is False

    emitted = []
    monkeypatch.setattr(
        handlers,
        "_consume_entry_opportunity_recheck_ws_handoff",
        lambda _stock, ws_data, _runtime: (ws_data, {}),
    )
    monkeypatch.setattr(handlers, "clear_signal_reference", lambda _stock: None)
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, stage, **fields: emitted.append((stage, fields)),
    )
    stock = {"position_tag": POSITION_TAG, "opening_rotation_1pct_live": True}
    runtime = {
        "strategy": "SCALPING",
        "ratio": 0.10,
        "curr_price": 10_000,
        "liquidity_value": 1_000_000_000,
        "msg": "retired",
        "now_ts": datetime(2026, 8, 14, 11, 0).timestamp(),
        "cooldowns": {},
        "alerted_stocks": set(),
        "opening_rotation_1pct_live": True,
        "pos_tag": POSITION_TAG,
    }

    assert not handlers._submit_watching_triggered_entry(
        stock, "005930", {"curr": 10_000}, 1, runtime
    )
    assert stock["opening_rotation_retired_entry_blocked"] is True
    assert "opening_rotation_1pct_live" not in stock
    assert emitted[0][0] == "opening_rotation_retired_entry_blocked"
    assert emitted[0][1]["broker_order_forbidden"] is True


def _packet(price: int) -> dict:
    return {
        "curr_price": price,
        "quote_stale": False,
        "quote_age_ms": 120.0,
        "quote_stale_threshold_ms": 3000.0,
        "tick_latest_age_ms": 120.0,
        "tick_context_stale": False,
        "tick_context_quality": "fresh_computed",
        "tick_aggressor_pressure_usable": True,
        "spread_bp": 8.0,
        "spread_ticks": 1,
        "buy_pressure_10t": 64.0,
        "tick_aggressor_trusted_count": 8,
        # Newest first, matching the live reaction-context packet.
        "trusted_tick_prices": [price, price, price - 1, price - 1, price - 2],
        "tick_acceleration_ratio": 1.35,
        "price_change_10t_pct": 0.12,
        "volume_ratio_pct": 125.0,
        "micro_vwap_available": True,
        "curr_vs_micro_vwap_bp": 24.0,
        "microstructure_reaction_ask_sweep_score": 72,
        "microstructure_reaction_post_sweep_hold_score": 67,
        "microstructure_reaction_bid_replenishment_score": 61,
        "microstructure_reaction_wall_replenishment_risk_score": 42,
        "microstructure_reaction_vi_proximity_risk": 18,
    }


class _OpeningTTLQuery:
    def __init__(self, owner):
        self.owner = owner

    def filter(self, *_args):
        self.owner.filter_call_count += 1
        return self

    def update(self, values, *, synchronize_session=False):
        self.owner.updates.append((dict(values), synchronize_session))
        return self.owner.update_result


class _OpeningTTLSession:
    def __init__(self, owner):
        self.owner = owner

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, _model):
        return _OpeningTTLQuery(self.owner)

    def get(self, _model, _record_id):
        return self.owner.persisted_row


class _OpeningTTLDB:
    def __init__(self, update_result=1, persisted_row=None):
        self.update_result = update_result
        self.persisted_row = persisted_row
        self.filter_call_count = 0
        self.updates = []

    def get_session(self):
        return _OpeningTTLSession(self)


class _OpeningTTLEventBus:
    def __init__(self):
        self.events = []

    def publish(self, name, payload):
        self.events.append((name, payload))


def test_kt00011_parser_exposes_applied_margin_orderable_capacity(monkeypatch):
    captured = {}

    def _fetch(**kwargs):
        captured.update(kwargs)
        return [
            {
                "return_code": 0,
                "stk_profa_rt": "20%",
                "profa_rt": "40%",
                "aplc_rt": "40%",
                "profa_40ord_alow_amt": "000001200000",
                "profa_40ord_alowq": "000000000120",
                "min_ord_alow_amt": "000000000000",
                "min_ord_alowq": "000000000000",
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", _fetch)

    snapshot = kiwoom_utils.get_orderable_by_margin_kt00011(
        "token",
        "A005930_AL",
        unit_price=10_000,
    )

    assert captured["api_id"] == "kt00011"
    assert captured["payload"] == {"stk_cd": "005930", "uv": "10000"}
    assert snapshot["applied_margin_rate"] == 40
    assert snapshot["applied_margin_tier_recognized"] is True
    assert snapshot["applied_orderable_amount"] == 1_200_000
    assert snapshot["applied_orderable_qty"] == 120
    assert snapshot["requested_unit_price"] == 10_000


def test_kt00011_parser_does_not_round_fractional_applied_margin_rate(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "return_code": 0,
                "aplc_rt": "39.6%",
                "profa_40ord_alow_amt": "000001200000",
                "profa_40ord_alowq": "000000000120",
            }
        ],
    )

    snapshot = kiwoom_utils.get_orderable_by_margin_kt00011(
        "token", "005930", unit_price=10_000
    )

    assert snapshot["applied_margin_rate"] == 0
    assert snapshot["applied_margin_tier_recognized"] is False
    assert snapshot["applied_orderable_qty"] == 0


@pytest.mark.parametrize("raw_return_code", [None, "invalid"])
def test_kt00011_parser_rejects_missing_or_invalid_return_code(
    monkeypatch,
    raw_return_code,
):
    response = {
        "aplc_rt": "40%",
        "profa_40ord_alow_amt": "000001200000",
        "profa_40ord_alowq": "000000000120",
    }
    if raw_return_code is not None:
        response["return_code"] = raw_return_code
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [response],
    )

    snapshot = kiwoom_utils.get_orderable_by_margin_kt00011(
        "token", "005930", unit_price=10_000
    )

    assert snapshot["error"].startswith("kt00011 return_code")
    assert "applied_orderable_qty" not in snapshot


def test_opening_margin_budget_uses_broker_tier_when_cash_guard_is_zero():
    context = handlers._apply_opening_rotation_margin_budget_authority(
        {
            "budget_base": 0,
            "budget_source": "kt00011_min_account_deposit_cash_orderable",
            "cash_orderable_amount": 0,
            "cash_orderable_qty_cap": 0,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": 40,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": 10_000,
        },
        unit_price=10_000,
    )

    assert context["opening_rotation_margin_one_share_authorized"] is True
    assert context["opening_rotation_margin_cash_guard_bypassed"] is True
    assert context["budget_base"] == 1_200_000
    assert context["budget_source"] == "kt00011_applied_margin_orderable"
    assert context["opening_rotation_margin_orderable_qty_cap"] == 120


def test_general_entry_margin_budget_uses_broker_tier_only_on_cash_shortfall():
    context = handlers._apply_general_entry_margin_budget_authority(
        {
            "budget_base": 0,
            "budget_source": "kt00011_min_account_deposit_cash_orderable",
            "cash_orderable_amount": 0,
            "cash_orderable_qty_cap": 0,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": 40,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": 10_000,
        },
        unit_price=10_000,
    )

    assert context["general_entry_margin_one_share_authorized"] is True
    assert context["general_entry_margin_cash_guard_bypassed"] is True
    assert context["general_entry_margin_order_api"] == "kt10000"
    assert context["general_entry_margin_credit_order_api_used"] is False
    assert context["budget_base"] == 1_200_000
    assert context["budget_source"] == "kt00011_applied_margin_orderable"


def test_general_entry_margin_budget_preserves_exact_price_cash_authority():
    context = handlers._apply_general_entry_margin_budget_authority(
        {
            "budget_base": 20_000,
            "budget_source": "kt00011_min_account_deposit_cash_orderable",
            "cash_orderable_amount": 20_000,
            "cash_orderable_qty_cap": 2,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": 40,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": 10_000,
        },
        unit_price=10_000,
    )

    assert context["general_entry_margin_one_share_authorized"] is False
    assert context["general_entry_margin_authority_reason"] == (
        "cash_one_share_capacity_available"
    )
    assert context["general_entry_margin_cash_guard_bypassed"] is False
    assert context["budget_base"] == 20_000
    assert context["cash_orderable_qty_cap"] == 2


@pytest.mark.parametrize(
    ("rate", "checked_price", "reason"),
    [
        (100, 10_000, "applied_margin_rate_not_margin_eligible"),
        (40, 9_990, "kt00011_requested_unit_price_mismatch"),
    ],
)
def test_general_entry_margin_budget_fails_closed_on_ineligible_capacity(
    rate,
    checked_price,
    reason,
):
    context = handlers._apply_general_entry_margin_budget_authority(
        {
            "budget_base": 0,
            "cash_orderable_amount": 0,
            "cash_orderable_qty_cap": 0,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": rate,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": checked_price,
        },
        unit_price=10_000,
    )

    assert context["general_entry_margin_one_share_authorized"] is False
    assert context["general_entry_margin_authority_reason"] == reason
    assert context["budget_base"] == 0


def test_generic_scalp_budget_keeps_cash_only_capacity_when_margin_exists(monkeypatch):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(handlers.kiwoom_orders, "get_last_deposit_meta", lambda: {})
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_orderable_by_margin_kt00011",
        lambda *_args, **_kwargs: {
            "error": "",
            "deposit": 20_000,
            "cash_only_orderable_amount": 20_000,
            "cash_only_orderable_qty": 2,
            "stock_margin_rate": 20,
            "applied_margin_rate": 40,
            "applied_margin_tier_recognized": True,
            "applied_orderable_amount": 1_200_000,
            "applied_orderable_qty": 120,
            "requested_unit_price": 10_000,
        },
    )

    context = handlers._resolve_scalp_cash_budget_context(
        "005930",
        10_000,
        20_000,
    )

    assert context["budget_base"] == 20_000
    assert context["budget_source"] == "kt00011_min_account_deposit_cash_orderable"
    assert context["cash_orderable_qty_cap"] == 2
    assert context["kt00011_applied_orderable_qty"] == 120
    assert "opening_rotation_margin_one_share_authorized" not in context


@pytest.mark.parametrize(
    ("rate", "amount", "qty", "reason"),
    [
        (100, 1_200_000, 120, "applied_margin_rate_not_margin_eligible"),
        (40, 9_999, 120, "applied_margin_orderable_amount_below_one_share"),
        (40, 1_200_000, 0, "applied_margin_orderable_qty_below_one"),
    ],
)
def test_opening_margin_budget_fails_closed_on_ineligible_broker_capacity(
    rate,
    amount,
    qty,
    reason,
):
    context = handlers._apply_opening_rotation_margin_budget_authority(
        {
            "budget_base": 75_000,
            "budget_source": "kt00011_min_account_deposit_cash_orderable",
            "cash_orderable_amount": 75_000,
            "cash_orderable_qty_cap": 7,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": rate,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": amount,
            "kt00011_applied_orderable_qty": qty,
            "kt00011_requested_unit_price": 10_000,
        },
        unit_price=10_000,
    )

    assert context["opening_rotation_margin_one_share_authorized"] is False
    assert context["opening_rotation_margin_authority_reason"] == reason
    assert context["budget_base"] == 75_000
    assert context["cash_orderable_qty_cap"] == 7


def test_opening_margin_budget_fails_closed_on_broker_lookup_error():
    context = handlers._apply_opening_rotation_margin_budget_authority(
        {
            "budget_base": 0,
            "cash_orderable_amount": 0,
            "cash_orderable_qty_cap": 0,
            "kt00011_error": "transport_timeout",
            "kt00011_applied_margin_rate": 40,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": 10_000,
        },
        unit_price=10_000,
    )

    assert context["opening_rotation_margin_one_share_authorized"] is False
    assert context["opening_rotation_margin_authority_reason"] == "kt00011_error"
    assert context["budget_base"] == 0


def test_opening_margin_budget_rejects_different_kt00011_checked_price():
    context = handlers._apply_opening_rotation_margin_budget_authority(
        {
            "budget_base": 0,
            "cash_orderable_amount": 0,
            "cash_orderable_qty_cap": 0,
            "kt00011_error": "",
            "kt00011_applied_margin_rate": 40,
            "kt00011_applied_margin_tier_recognized": True,
            "kt00011_applied_orderable_amount": 1_200_000,
            "kt00011_applied_orderable_qty": 120,
            "kt00011_requested_unit_price": 9_990,
        },
        unit_price=10_000,
    )

    assert context["opening_rotation_margin_one_share_authorized"] is False
    assert context["opening_rotation_margin_authority_reason"] == (
        "kt00011_requested_unit_price_mismatch"
    )
    assert context["opening_rotation_margin_requested_unit_price"] == 9_990
    assert context["budget_base"] == 0


def test_opening_exact_price_cash_capacity_survives_margin_tier_loss():
    context = {
        "kt00011_error": "",
        "kt00011_requested_unit_price": 10_010,
        "cash_orderable_amount": 10_010,
        "cash_orderable_qty_cap": 1,
        "opening_rotation_margin_one_share_authorized": False,
        "opening_rotation_margin_rate": 100,
    }

    assert handlers._opening_rotation_cash_one_share_authorized(
        context, unit_price=10_010
    )


@pytest.mark.parametrize(
    "context",
    [
        {
            "kt00011_error": "transport_timeout",
            "kt00011_requested_unit_price": 10_010,
            "cash_orderable_amount": 20_000,
            "cash_orderable_qty_cap": 1,
        },
        {
            "kt00011_error": "",
            "kt00011_requested_unit_price": 10_000,
            "cash_orderable_amount": 20_000,
            "cash_orderable_qty_cap": 1,
        },
        {
            "kt00011_error": "",
            "kt00011_requested_unit_price": 10_010,
            "cash_orderable_amount": 10_009,
            "cash_orderable_qty_cap": 1,
        },
    ],
)
def test_opening_exact_price_cash_capacity_fails_closed(context):
    assert not handlers._opening_rotation_cash_one_share_authorized(
        context, unit_price=10_010
    )


def evaluate_entry(
    *,
    previous_state,
    feature_packet,
    source_signature,
    day_change_pct,
    intraday_high_price,
    now_dt,
    promotion_id="PROMO-TEST",
    config=None,
):
    """Keep unit fixtures explicit about promotion-owned state."""
    state = dict(previous_state or {})
    if state:
        state.setdefault("promotion_id", promotion_id)
        state.setdefault("promotion_started_epoch", now_dt.timestamp() - 1.0)
    return _evaluate_entry_impl(
        previous_state=state,
        feature_packet=feature_packet,
        source_signature=source_signature,
        day_change_pct=day_change_pct,
        intraday_high_price=intraday_high_price,
        now_dt=now_dt,
        promotion_id=promotion_id,
        config=config,
    )


def test_watch_source_scope_accepts_every_scanner_lineage():
    config = EntryConfig()
    now_dt = datetime(2026, 7, 21, 9, 20)

    assert is_watch_source_scope(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        now_dt=now_dt,
        config=config,
    )
    assert is_watch_source_scope(
        position_tag="SCANNER",
        source_signature="LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
        now_dt=now_dt,
        config=config,
    )


def test_opening_rotation_requires_explicit_krx_regular_scope():
    assert is_krx_regular_scope(
        effective_venue="KRX", market_session_bucket="krx_regular"
    )
    assert not is_krx_regular_scope(effective_venue="NXT", market_session_bucket="nxt")
    assert not is_krx_regular_scope(effective_venue="", market_session_bucket="")


def test_opening_rotation_watch_slots_cap_two_active_promotions(monkeypatch):
    now_ts = datetime(2026, 8, 12, 9, 10).timestamp()

    def watch(code, promotion_id):
        return {
            "id": code,
            "code": code,
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "scanner_promotion_id": promotion_id,
        }

    first = watch("000001", "PROMO-1")
    second = watch("000002", "PROMO-2")
    third = watch("000003", "PROMO-3")
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [first, second, third])

    first_claim = handlers._claim_opening_rotation_watch_slot(
        first, promotion_id="PROMO-1", now_ts=now_ts
    )
    second_claim = handlers._claim_opening_rotation_watch_slot(
        second, promotion_id="PROMO-2", now_ts=now_ts
    )
    repeated_claim = handlers._claim_opening_rotation_watch_slot(
        first, promotion_id="PROMO-1", now_ts=now_ts + 1
    )
    blocked_claim = handlers._claim_opening_rotation_watch_slot(
        third, promotion_id="PROMO-3", now_ts=now_ts + 1
    )

    assert first_claim["newly_claimed"] is True
    assert second_claim["newly_claimed"] is True
    assert repeated_claim["allowed"] is True
    assert repeated_claim["newly_claimed"] is False
    assert blocked_claim == {
        "allowed": False,
        "reason": "watch_slot_capacity_full",
        "slot_limit": 2,
        "active_slot_count": 2,
        "newly_claimed": False,
    }

    assert handlers._release_opening_rotation_watch_slot(first, promotion_id="PROMO-1")
    replacement_claim = handlers._claim_opening_rotation_watch_slot(
        third, promotion_id="PROMO-3", now_ts=now_ts + 2
    )
    assert replacement_claim["allowed"] is True
    assert replacement_claim["active_slot_count"] == 2


def test_opening_rotation_repeated_claim_backfills_missing_claim_time(monkeypatch):
    now_ts = datetime(2026, 8, 12, 9, 10).timestamp()
    stock = {
        "id": 1,
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-1",
        "opening_rotation_watch_slot_promotion_id": "PROMO-1",
    }
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])

    claim = handlers._claim_opening_rotation_watch_slot(
        stock, promotion_id="PROMO-1", now_ts=now_ts
    )

    assert claim["allowed"] is True
    assert claim["newly_claimed"] is False
    assert stock["opening_rotation_watch_slot_claimed_at_epoch"] == now_ts


def test_opening_rotation_capacity_full_falls_through_without_opening_context(
    monkeypatch,
):
    now_dt = datetime(2026, 8, 12, 9, 10)
    occupied = []
    for index in (1, 2):
        promotion_id = f"PROMO-{index}"
        occupied.append(
            {
                "id": index,
                "code": f"00000{index}",
                "status": "WATCHING",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "scanner_promotion_id": promotion_id,
                "opening_rotation_watch_slot_promotion_id": promotion_id,
            }
        )
    candidate = {
        "id": 3,
        "code": "000003",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-3",
        "source_signature": "PRICE_JUMP_START",
    }
    emitted = []
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [*occupied, candidate])
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *_args, **_kwargs: pytest.fail(
            "capacity-blocked promotion must not prepare Opening context"
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers._handle_watching_opening_rotation(
        candidate,
        "000003",
        {"curr": 10_000, "fluctuation": 3.0},
        {
            "pos_tag": "SCANNER",
            "now_ts": now_dt.timestamp(),
            "now_dt": now_dt,
            "fluctuation": 3.0,
            "curr_price": 10_000,
            "is_trigger": False,
        },
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is False
    assert "opening_rotation_watch_slot_promotion_id" not in candidate
    blocked = next(
        fields
        for stage, fields in emitted
        if stage == "opening_rotation_watch_slot_capacity_blocked"
    )
    assert blocked["opening_rotation_watch_slot_limit"] == 2
    assert blocked["opening_rotation_active_watch_slot_count"] == 2
    assert blocked["actual_order_submitted"] is False


def test_missing_target_date_runtime_policy_is_disabled(tmp_path):
    policy = load_active_runtime_policy(
        now_dt=datetime(2026, 8, 11, 8, 45),
        path=tmp_path / "missing-opening-policy.json",
    )

    assert policy.entry.enabled is False
    assert policy.target_date == "2026-08-11"
    assert policy.source_quality_status == "runtime_default"


def test_opening_rotation_ttl_drop_expires_watch_and_releases_slot(monkeypatch):
    now_dt = datetime(2026, 8, 11, 9, 5)
    promotion_id = "SCANPROM-005930-TTL"
    stock = {
        "id": 505930,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        # A boot-restored Opening watch can carry the runtime owner tag while
        # its DB row intentionally remains the scanner WATCHING row.
        "position_tag": POSITION_TAG,
        "scanner_promotion_id": promotion_id,
        "source_signature": "PRICE_JUMP_START",
        "buy_qty": 0,
        "opening_rotation_1pct_state": {
            "promotion_id": promotion_id,
            "promotion_started_epoch": now_dt.timestamp() - 61.0,
        },
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 70_000,
        "is_trigger": False,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    emitted = []
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *_args, **_kwargs: {"status": "not_enabled"},
    )
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *_args, **_kwargs: _packet(70_000),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 70_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert stock["status"] == "EXPIRED"
    assert stock["opening_rotation_consumed_promotion_id"] == promotion_id
    assert stock["opening_rotation_watch_phase"] == "PROMOTION_TTL_EXPIRED"
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert "opening_rotation_episode_phase" not in stock
    assert fake_db.updates == [({"status": "EXPIRED"}, False)]
    assert event_bus.events == [
        (
            "COMMAND_WS_UNREG",
            {
                "codes": ["005930"],
                "source": "opening_rotation_promotion_ttl_expired",
                "reason": "promotion_ttl_expired",
            },
        )
    ]
    assert [stage for stage, _fields in emitted].count(
        "opening_rotation_promotion_ttl_released"
    ) == 1
    release_fields = next(
        fields
        for stage, fields in emitted
        if stage == "opening_rotation_promotion_ttl_released"
    )
    assert release_fields["opening_rotation_watch_slot_released"] is True
    assert release_fields["opening_rotation_ws_unregister_requested"] is True
    assert release_fields["actual_order_submitted"] is False


def test_opening_rotation_claim_ttl_expires_before_stuck_async_or_price_guard(
    monkeypatch,
):
    now_dt = datetime(2026, 8, 11, 9, 5)
    promotion_id = "SCANPROM-005930-CLAIM-TTL"
    stock = {
        "id": 505931,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "source_signature": "PRICE_JUMP_START",
        "buy_qty": 0,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "opening_rotation_watch_slot_claimed_at_epoch": now_dt.timestamp() - 61.0,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    emitted = []
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_promotion_price_consistency_fields",
        lambda *_args, **_kwargs: pytest.fail(
            "expired watch slot must close before price-source arbitration"
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *_args, **_kwargs: pytest.fail(
            "expired watch slot must close before async context resolution"
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 70_000, "fluctuation": 3.0},
        {
            "pos_tag": "SCANNER",
            "now_ts": now_dt.timestamp(),
            "now_dt": now_dt,
            "fluctuation": 3.0,
            "curr_price": 70_000,
            "is_trigger": False,
        },
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert stock["status"] == "EXPIRED"
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert fake_db.updates == [({"status": "EXPIRED"}, False)]
    release = next(
        fields
        for stage, fields in emitted
        if stage == "opening_rotation_promotion_ttl_released"
    )
    assert release["opening_rotation_watch_slot_released"] is True


def test_opening_rotation_ttl_sweep_expires_slot_without_watching_evaluation(
    monkeypatch,
):
    now_dt = datetime(2026, 8, 13, 10, 0)
    promotion_id = "SCANPROM-005930-SWEEP"
    stock = {
        "id": 505932,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "buy_qty": 0,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "opening_rotation_watch_slot_claimed_at_epoch": now_dt.timestamp() - 61.0,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    emitted = []
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    result = handlers.sweep_expired_opening_rotation_watch_slots(
        [stock], now_ts=now_dt.timestamp()
    )

    assert result == {
        "status": "pass",
        "eligible_count": 1,
        "expired_count": 1,
        "failed_count": 0,
        "promotion_ttl_sec": 60.0,
    }
    assert stock["status"] == "EXPIRED"
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert fake_db.updates == [({"status": "EXPIRED"}, False)]
    assert [stage for stage, _fields in emitted] == [
        "opening_rotation_promotion_ttl_released"
    ]


def test_opening_rotation_ttl_sweep_without_slots_skips_policy_and_db(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "load_active_opening_rotation_runtime_policy",
        lambda: pytest.fail("no-slot sweep must not reload the runtime policy"),
    )
    monkeypatch.setattr(
        handlers,
        "_expire_opening_rotation_ttl_promotion",
        lambda *_args, **_kwargs: pytest.fail("no-slot sweep must not touch DB"),
    )

    result = handlers.sweep_expired_opening_rotation_watch_slots(
        [
            {
                "status": "WATCHING",
                "scanner_promotion_id": "PROMO-1",
                "position_tag": "SCANNER",
            }
        ],
        now_ts=datetime(2026, 8, 13, 10, 0).timestamp(),
    )

    assert result == {
        "status": "no_active_slots",
        "eligible_count": 0,
        "expired_count": 0,
        "failed_count": 0,
    }


def test_opening_rotation_ttl_sweep_backfills_missing_claim_time(monkeypatch):
    now_ts = datetime(2026, 8, 13, 10, 0).timestamp()
    stock = {
        "status": "WATCHING",
        "scanner_promotion_id": "PROMO-MISSING-CLAIM-TIME",
        "opening_rotation_watch_slot_promotion_id": "PROMO-MISSING-CLAIM-TIME",
    }
    monkeypatch.setattr(
        handlers,
        "_expire_opening_rotation_ttl_promotion",
        lambda *_args, **_kwargs: pytest.fail(
            "backfilled ownership receives a fresh TTL before expiration"
        ),
    )

    result = handlers.sweep_expired_opening_rotation_watch_slots([stock], now_ts=now_ts)

    assert result["status"] == "pass"
    assert result["eligible_count"] == 0
    assert result["expired_count"] == 0
    assert stock["opening_rotation_watch_slot_claimed_at_epoch"] == now_ts


def test_async_rising_missed_commit_cannot_preempt_owned_opening_slot(monkeypatch):
    now_dt = datetime(2026, 8, 13, 10, 5)
    promotion_id = "SCANPROM-005930-ASYNC-OWNER"
    generation = ScannerGeneration(
        code="005930",
        promotion_id=promotion_id,
        revision=1,
        record_id=505933,
        venue="KRX",
        promotion_epoch=now_dt.timestamp() - 10.0,
        attach_epoch=now_dt.timestamp() - 9.0,
        observed_price=70_000,
        source_signature="PRICE_JUMP_START",
    )
    stock = {
        "id": 505933,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "opening_rotation_watch_slot_claimed_at_epoch": now_dt.timestamp() - 8.0,
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": "rising_missed:owner-race",
    }
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_maybe_submit_rising_missed_one_share_entry",
        lambda *_args, **_kwargs: pytest.fail(
            "Opening-owned promotion must not enter Rising Missed commit"
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers.handle_scanner_async_rising_missed_commit(
        stock,
        "005930",
        {"curr": 70_000, "fluctuation": 3.0},
        admin_id=1,
        now_ts=now_dt.timestamp(),
        now_dt=now_dt,
        scanner_async_generation=generation,
    )

    assert handled is True
    assert stock["status"] == "WATCHING"
    assert stock["opening_rotation_watch_slot_promotion_id"] == promotion_id
    blocked = next(
        fields
        for stage, fields in emitted
        if stage == "rising_missed_entry_blocked_opening_rotation_owner"
    )
    assert blocked["opening_rotation_watch_slot_owned"] is True
    assert blocked["broker_order_forbidden"] is True
    assert blocked["actual_order_submitted"] is False


def test_final_submit_rechecks_opening_owner_against_rising_missed_race(monkeypatch):
    now_dt = datetime(2026, 8, 13, 10, 10)
    promotion_id = "SCANPROM-005930-FINAL-OWNER"
    stock = {
        "id": 505934,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "opening_rotation_watch_slot_claimed_at_epoch": now_dt.timestamp() - 8.0,
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "rising_missed_scout_upgrade_pending": True,
        "forced_entry_qty": 1,
        "forced_entry_reason": "rising_missed_one_share_entry",
        "target_buy_price": 70_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "ratio": 0.10,
        "curr_price": 70_000,
        "liquidity_value": 1_000_000_000,
        "msg": "",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "cooldowns": {},
        "alerted_stocks": set(),
        "ai_engine": None,
        "pos_tag": "SCANNER",
        "scout_upgrade_entry": False,
        "forced_entry_qty": 1,
        "rising_missed_one_share_entry_forced": True,
    }
    emitted = []
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_deposit",
        lambda *_args, **_kwargs: pytest.fail(
            "owner conflict must block before account or broker access"
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    submitted = handlers._submit_watching_triggered_entry(
        stock,
        "005930",
        {"curr": 70_000},
        admin_id=1,
        runtime=runtime,
    )

    assert submitted is False
    assert stock["opening_rotation_watch_slot_promotion_id"] == promotion_id
    assert "rising_missed_one_share_entry_forced" not in stock
    assert "rising_missed_one_share_scout" not in stock
    assert "target_buy_price" not in stock
    blocked = next(
        fields
        for stage, fields in emitted
        if stage == "entry_submit_blocked_opening_rotation_owner_conflict"
    )
    assert blocked["opening_rotation_watch_slot_owned"] is True
    assert blocked["broker_order_forbidden"] is True
    assert blocked["actual_order_submitted"] is False


@pytest.mark.parametrize(
    "protected_fields",
    [
        {"pending_entry_orders": [{"status": "OPEN", "ord_no": "BUY-1"}]},
        {"buy_qty": 1},
        {"entry_filled_qty": 1},
        {"opening_rotation_order_ambiguity": True},
        {"opening_rotation_new_episode_blocked": True},
    ],
)
def test_opening_rotation_ttl_release_never_expires_order_or_position(
    monkeypatch, protected_fields
):
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-1",
        "buy_qty": 0,
        **protected_fields,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id="PROMO-1",
        now_ts=datetime(2026, 8, 11, 9, 5).timestamp(),
    )

    assert expired is False
    assert stock["status"] == "WATCHING"
    assert fake_db.updates == []
    assert event_bus.events == []


def test_opening_rotation_ttl_release_rejects_stale_promotion_identity(monkeypatch):
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-NEW",
        "buy_qty": 0,
    }
    fake_db = _OpeningTTLDB()
    monkeypatch.setattr(handlers, "DB", fake_db)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id="PROMO-OLD",
        now_ts=datetime(2026, 8, 11, 9, 5).timestamp(),
    )

    assert expired is False
    assert stock["status"] == "WATCHING"
    assert fake_db.filter_call_count == 0


def test_opening_rotation_ttl_release_keeps_ws_for_other_active_owner(monkeypatch):
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-1",
        "buy_qty": 0,
    }
    holding = {
        "id": 2,
        "code": "005930",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "position_tag": "MIDDLE",
        "buy_qty": 1,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock, holding])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *_args, **_kwargs: None)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id="PROMO-1",
        now_ts=datetime(2026, 8, 11, 9, 5).timestamp(),
    )

    assert expired is True
    assert stock["status"] == "EXPIRED"
    assert event_bus.events == []


def test_opening_rotation_ttl_release_accepts_boot_restored_nat_buy_time(
    monkeypatch,
):
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        # DB keeps SCANNER while the admitted runtime owner uses this tag.
        "position_tag": POSITION_TAG,
        "scanner_promotion_id": "PROMO-RESTORED",
        "buy_qty": 0,
        "buy_time": pd.NaT,
    }
    fake_db = _OpeningTTLDB()
    event_bus = _OpeningTTLEventBus()
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *_args, **_kwargs: None)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id="PROMO-RESTORED",
        now_ts=datetime(2026, 8, 11, 9, 5).timestamp(),
    )

    assert expired is True
    assert stock["status"] == "EXPIRED"
    assert event_bus.events == [
        (
            "COMMAND_WS_UNREG",
            {
                "codes": ["005930"],
                "source": "opening_rotation_promotion_ttl_expired",
                "reason": "promotion_ttl_expired",
            },
        )
    ]


def test_opening_rotation_ttl_release_keeps_slot_when_db_rejects(monkeypatch):
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-1",
        "buy_qty": 0,
    }
    fake_db = _OpeningTTLDB(update_result=0)
    event_bus = _OpeningTTLEventBus()
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id="PROMO-1",
        now_ts=datetime(2026, 8, 11, 9, 5).timestamp(),
    )

    assert expired is False
    assert stock["status"] == "WATCHING"
    assert event_bus.events == []


def test_opening_rotation_ttl_release_converges_when_db_is_already_expired(
    monkeypatch,
):
    promotion_id = "PROMO-1"
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "buy_qty": 0,
    }
    persisted_row = SimpleNamespace(
        stock_code="005930",
        status="EXPIRED",
        strategy="SCALPING",
        position_tag="SCANNER",
        scanner_promotion_id=promotion_id,
        buy_time=None,
        buy_qty=0,
    )
    fake_db = _OpeningTTLDB(update_result=0, persisted_row=persisted_row)
    event_bus = _OpeningTTLEventBus()
    emitted = []
    monkeypatch.setattr(handlers, "DB", fake_db)
    monkeypatch.setattr(handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(
        handlers, "should_retain_ws_subscription", lambda *_args, **_kwargs: False
    )
    monkeypatch.setattr(
        handlers,
        "should_retain_rising_missed_nxt_post_block_subscription",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id=promotion_id,
        now_ts=datetime(2026, 8, 13, 9, 42).timestamp(),
    )

    assert expired is True
    assert stock["status"] == "EXPIRED"
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    release = next(
        fields
        for stage, fields in emitted
        if stage == "opening_rotation_promotion_ttl_released"
    )
    assert release["opening_rotation_db_expiration_result"] == (
        "idempotent_already_expired"
    )


@pytest.mark.parametrize(
    "persisted_overrides",
    [
        {"buy_qty": 1},
        {"buy_time": datetime(2026, 8, 13, 9, 41)},
        {"scanner_promotion_id": "PROMO-NEW"},
        {"status": "HOLDING"},
    ],
)
def test_opening_rotation_ttl_release_does_not_converge_unsafe_db_state(
    monkeypatch, persisted_overrides
):
    promotion_id = "PROMO-1"
    stock = {
        "id": 1,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "buy_qty": 0,
    }
    persisted_fields = {
        "stock_code": "005930",
        "status": "EXPIRED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": promotion_id,
        "buy_time": None,
        "buy_qty": 0,
        **persisted_overrides,
    }
    fake_db = _OpeningTTLDB(
        update_result=0,
        persisted_row=SimpleNamespace(**persisted_fields),
    )
    monkeypatch.setattr(handlers, "DB", fake_db)

    expired = handlers._expire_opening_rotation_ttl_promotion(
        stock,
        "005930",
        promotion_id=promotion_id,
        now_ts=datetime(2026, 8, 13, 9, 42).timestamp(),
    )

    assert expired is False
    assert stock["status"] == "WATCHING"
    assert stock["opening_rotation_watch_slot_promotion_id"] == promotion_id


def test_runtime_skips_opening_when_krx_regular_provenance_is_missing(monkeypatch):
    now_dt = datetime(2026, 8, 11, 9, 20)
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-UNKNOWN-VENUE",
        "opening_rotation_watch_slot_promotion_id": "PROMO-UNKNOWN-VENUE",
        "source_signature": "PRICE_JUMP_START",
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_scanner_runtime_event_venue_fields",
        lambda _stock: {
            "venue": "UNKNOWN",
            "effective_venue": "UNKNOWN",
            "venue_resolution": "explicit_target_venue_missing",
            "venue_source_quality_status": "reviewed_fail_closed",
            "venue_unknown_reviewed_reason": "explicit_target_venue_missing",
            "market_session_bucket": "market_session_bucket_missing",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is False
    assert runtime["is_trigger"] is False
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert emitted[0][0] == "opening_rotation_watch_slot_released"
    assert emitted[0][1]["reason"] == "krx_regular_scope_lost"
    assert emitted[-1][0] == "opening_rotation_krx_regular_scope_skipped"
    assert emitted[-1][1]["broker_order_forbidden"] is True


def test_opening_rotation_upstream_block_records_unknown_day_change(monkeypatch):
    emitted = []
    stock = {
        "id": 41,
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
    }
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    logged = handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="ws_snapshot_missing_or_zero",
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
        ws_data={},
    )

    assert logged is True
    stage, fields = emitted[-1]
    assert stage == "opening_rotation_1pct_upstream_blocked"
    assert fields["opening_rotation_upstream_source_scope"] is True
    assert fields["opening_rotation_upstream_exact_candidate_known"] is False
    assert fields["opening_rotation_upstream_exact_candidate"] is False
    assert fields["freshness_envelope_attempted"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_opening_rotation_upstream_block_dedupes_same_state_but_logs_change(
    monkeypatch,
):
    emitted = []
    stock = {
        "id": 41,
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
    }
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )
    started_at = datetime(2026, 7, 21, 9, 20).timestamp()

    assert handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="scanner_scheduler_generation_warm_parked",
        now_ts=started_at,
        ws_data={"fluctuation": 4.98},
    )
    assert not handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="scanner_scheduler_generation_warm_parked",
        now_ts=started_at + 30.0,
        ws_data={"fluctuation": 4.95},
    )
    assert handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="scanner_queue_rank_deferred",
        now_ts=started_at + 60.0,
        ws_data={"fluctuation": 4.95},
    )
    assert handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="scanner_queue_rank_deferred",
        now_ts=started_at + 361.0,
        ws_data={"fluctuation": 4.95},
    )
    assert not handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="ws_snapshot_missing_or_zero_recovered",
        now_ts=started_at + 370.0,
        ws_data={"fluctuation": 4.95},
    )
    assert handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="scanner_queue_rank_deferred",
        now_ts=started_at + 371.0,
        ws_data={"fluctuation": 4.95},
    )

    assert [stage for stage, _fields in emitted] == [
        "opening_rotation_1pct_upstream_blocked",
        "opening_rotation_1pct_upstream_blocked",
        "opening_rotation_1pct_upstream_blocked",
        "opening_rotation_1pct_upstream_blocked",
    ]
    assert all(fields["runtime_effect"] is False for _stage, fields in emitted)
    assert all(fields["actual_order_submitted"] is False for _stage, fields in emitted)


def test_opening_rotation_upstream_scope_hydrates_scanner_source(monkeypatch):
    stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
    }
    monkeypatch.setattr(
        handlers,
        "_scanner_promotion_correlation_fields",
        lambda target: {"source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"},
    )

    fields = handlers._opening_rotation_upstream_scope_fields(
        stock,
        {"fluctuation": 3.2},
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )

    assert fields["opening_rotation_upstream_source_scope"] is True
    assert fields["opening_rotation_upstream_exact_candidate"] is True


def test_direct_opening_position_is_not_reclassified_by_rising_marker():
    fields = handlers._opening_rotation_upstream_scope_fields(
        {
            "strategy": "SCALPING",
            "position_tag": "OPENING_ROTATION_1PCT",
            "source_signature": "LOW_REBOUND_RISING_MISSED",
        },
        {"fluctuation": 3.2},
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )

    assert fields["opening_rotation_upstream_owner_conflict"] is False
    assert fields["opening_rotation_upstream_exact_candidate"] is True


def test_opening_rotation_upstream_handoff_requires_fresh_trusted_ws_tape(
    monkeypatch,
):
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
    }
    ws_data = {
        "curr": 10_000,
        "fluctuation": 3.2,
        "quote_stale": True,
    }
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: _packet(10_000),
    )

    allowed = handlers._opening_rotation_upstream_handoff_fields(
        stock,
        ws_data,
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )
    assert allowed["opening_rotation_upstream_handoff_allowed"] is True
    assert allowed["opening_rotation_upstream_trusted_tick_count"] == 8

    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: {
            **_packet(10_000),
            "tick_context_stale": True,
        },
    )
    blocked = handlers._opening_rotation_upstream_handoff_fields(
        stock,
        ws_data,
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )
    assert blocked["opening_rotation_upstream_handoff_allowed"] is False
    assert (
        blocked["opening_rotation_upstream_handoff_reason"]
        == "fresh_trusted_ws_tape_missing"
    )


def test_opening_rotation_bounded_handoff_can_pass_scanner_stale_backoff(
    monkeypatch,
):
    stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "added_time": 900.0,
    }
    ws_data = {
        "curr": 10_000,
        "fluctuation": 3.2,
        "last_ws_update_ts": 900.0,
    }
    handoff_fields = {
        "opening_rotation_upstream_handoff_allowed": True,
        "opening_rotation_upstream_handoff_reason": (
            "fresh_trusted_ws_tape_to_quote_envelope"
        ),
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_upstream_handoff_fields",
        lambda *args, **kwargs: handoff_fields,
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_ws_stale_backoff_fields",
        lambda *args, **kwargs: {
            "fast_precheck_result": "budget_reallocated",
            "fast_precheck_reason": "scanner_ws_stale_backoff_active",
            "scanner_ws_stale_backoff_active": True,
        },
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_ws_stale_backoff_strong_promotion_recheck",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_candidate_gate_backoff_fields",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_submit_safety_backoff_fields",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_signed_tape_scanner_backoff_fields",
        lambda *args, **kwargs: {},
    )

    fields = handlers._scanner_fast_precheck_fields(
        stock,
        now_ts=1000.0,
        code="005930",
        ws_data=ws_data,
    )

    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert (
        fields["fast_precheck_reason"]
        == "opening_rotation_fresh_tape_quote_envelope_handoff"
    )
    assert fields["opening_rotation_upstream_handoff_allowed"] is True


def test_opening_rotation_does_not_restore_pullback_across_scanner_repromotion(
    monkeypatch,
):
    handlers._OPENING_ROTATION_CONTEXT_CACHE.clear()
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    source_gap_packet = _packet(10_000)
    source_gap_packet.update(
        {
            "tick_context_quality": "missing",
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        }
    )
    packets = iter((source_gap_packet, _packet(10_020)))
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: next(packets),
    )
    first_now = datetime(2026, 7, 21, 10, 40)
    first_stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "SCANPROM-005930-1",
        "intraday_high_price": 10_100,
    }
    first_runtime = {
        "pos_tag": "SCANNER",
        "now_ts": first_now.timestamp(),
        "now_dt": first_now,
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
    }

    assert handlers._handle_watching_opening_rotation(
        first_stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        first_runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert first_runtime["is_trigger"] is False
    assert first_stock["opening_rotation_1pct_state"]["pullback_seen"] is False
    first_observed_fields = next(
        fields
        for args, fields in emitted
        if args[2] == "opening_rotation_1pct_observed"
    )
    assert first_observed_fields["reason"] == "trusted_tick_context_unavailable"
    assert (
        first_observed_fields["opening_rotation_downstream_preview_evaluated"] is False
    )

    second_now = datetime(2026, 7, 21, 10, 41)
    second_stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "SCANPROM-005930-2",
        "intraday_high_price": 10_100,
    }
    second_runtime = {
        "pos_tag": "SCANNER",
        "now_ts": second_now.timestamp(),
        "now_dt": second_now,
        "fluctuation": 3.2,
        "curr_price": 10_020,
        "is_trigger": False,
    }

    assert handlers._handle_watching_opening_rotation(
        second_stock,
        "005930",
        {"curr": 10_020, "fluctuation": 3.2, "ask_tot": 10, "bid_tot": 10},
        second_runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert second_runtime["is_trigger"] is False
    observed_fields = next(
        fields
        for args, fields in emitted
        if args[2] == "opening_rotation_1pct_observed"
        and fields.get("opening_rotation_state_current_promotion_id")
        == "SCANPROM-005930-2"
    )
    assert observed_fields["reason"] == "pullback_not_observed"
    assert observed_fields["opening_rotation_state_source"] == "empty"
    assert observed_fields["opening_rotation_state_restored_across_promotion"] is False
    handlers._OPENING_ROTATION_CONTEXT_CACHE.clear()


def test_entry_collects_then_qualifies_on_pullback_reacceleration():
    config = EntryConfig()
    collecting = evaluate_entry(
        previous_state=None,
        feature_packet=_packet(10_100),
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        day_change_pct=3.2,
        intraday_high_price=12_000,
        now_dt=datetime(2026, 7, 20, 9, 2, 30),
        config=config,
    )
    assert collecting["qualified"] is False
    assert collecting["reason"] == "collecting_before_entry_window"
    assert collecting["state"]["pullback_seen"] is False

    pulled_back = evaluate_entry(
        previous_state=collecting["state"],
        feature_packet=_packet(10_040),
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        day_change_pct=3.3,
        intraday_high_price=12_000,
        now_dt=datetime(2026, 7, 20, 9, 2, 45),
        config=config,
    )
    assert pulled_back["qualified"] is False
    assert pulled_back["reason"] == "collecting_before_entry_window"
    assert pulled_back["state"]["pullback_seen"] is True

    qualified = evaluate_entry(
        previous_state=pulled_back["state"],
        feature_packet=_packet(10_050),
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        day_change_pct=3.4,
        intraday_high_price=12_000,
        now_dt=datetime(2026, 7, 20, 9, 3, 1),
        config=config,
    )
    assert qualified["qualified"] is True
    assert qualified["position_tag"] == POSITION_TAG
    assert qualified["budget_ratio"] == pytest.approx(0.10)
    assert qualified["ai_score_hard_gate"] is False


def test_pullback_wait_exposes_downstream_gate_preview_without_bypass():
    decision = evaluate_entry(
        previous_state=None,
        feature_packet=_packet(10_000),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_000,
        now_dt=datetime(2026, 7, 21, 10, 40),
    )

    assert decision["qualified"] is False
    assert decision["reason"] == "pullback_not_observed"
    assert decision["opening_rotation_downstream_preview_evaluated"] is True
    assert decision["opening_rotation_downstream_preview_passed"] is True
    assert (
        decision["opening_rotation_downstream_preview_first_blocker"]
        == "all_downstream_gates_ready"
    )
    assert (
        decision["opening_rotation_downstream_preview_decision_authority"]
        == "observation_only_no_pattern_or_submit_bypass"
    )


def test_no_pullback_continuation_is_source_only_and_venue_scoped(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_MIN_DELTA_PCT", "1.0")
    fields = handlers._opening_rotation_no_pullback_continuation_fields(
        {
            "scanner_generation_id": "GEN-058610-1",
            "effective_venue": "KRX",
            "venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        reason="pullback_not_observed",
        promotion_price_fields={
            "scanner_promotion_price": 83_300,
            "scanner_promotion_price_source": "scanner_generation_observed_price",
            "scanner_promotion_price_ws_curr": 84_600,
            "scanner_promotion_price_ws_fresh": True,
            "scanner_promotion_price_conflict": False,
        },
    )

    assert fields["opening_rotation_no_pullback_continuation_candidate"] is True
    assert fields[
        "opening_rotation_no_pullback_continuation_current_vs_anchor_delta_pct"
    ] == pytest.approx(1.560624, abs=0.000001)
    assert fields["opening_rotation_no_pullback_continuation_effective_venue"] == "KRX"
    assert fields["opening_rotation_no_pullback_continuation_runtime_effect"] is False
    assert (
        fields["opening_rotation_no_pullback_continuation_allowed_runtime_apply"]
        is False
    )
    assert (
        fields["opening_rotation_no_pullback_continuation_actual_order_submitted"]
        is False
    )
    assert (
        fields["opening_rotation_no_pullback_continuation_broker_order_forbidden"]
        is True
    )

    monkeypatch.setattr(
        handlers,
        "_scanner_runtime_event_venue_fields",
        _ORIGINAL_SCANNER_RUNTIME_EVENT_VENUE_FIELDS,
    )
    missing_venue = handlers._opening_rotation_no_pullback_continuation_fields(
        {"scanner_generation_id": "GEN-058610-1"},
        reason="pullback_not_observed",
        promotion_price_fields={
            "scanner_promotion_price": 83_300,
            "scanner_promotion_price_ws_curr": 84_600,
            "scanner_promotion_price_ws_fresh": True,
            "scanner_promotion_price_conflict": False,
        },
    )
    assert missing_venue["opening_rotation_no_pullback_continuation_candidate"] is False
    assert (
        missing_venue["opening_rotation_no_pullback_continuation_reason"]
        == "source_quality_gate_not_passed"
    )


def test_runtime_observed_event_carries_no_pullback_continuation_provenance(
    monkeypatch,
):
    now_dt = datetime(2026, 7, 30, 10, 4, 33)
    stock = {
        "id": 58610,
        "name": "에스피지",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "SCANPROM-058610-1",
        "scanner_generation_id": "GEN-058610-1",
        "scanner_generation_observed_price": 83_300,
        "current_price_observed": 83_300,
        "_scanner_promotion_price_validated_generation_id": "GEN-058610-1",
        "effective_venue": "KRX",
        "venue": "KRX",
        "market_session_bucket": "krx_regular",
        "intraday_high_price": 86_000,
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 84_600,
        "is_trigger": False,
    }
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *args, **kwargs: {
            "status": "completed",
            "feature_packet": _packet(84_600),
        },
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "058610",
        {
            "curr": 84_600,
            "fluctuation": 3.0,
            "last_ws_update_ts": now_dt.timestamp() - 0.05,
            "last_realtime_type_ts": {"0B": now_dt.timestamp() - 0.05},
        },
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert "opening_rotation_entry_owner_handoff" not in runtime
    observed = next(
        fields
        for args, fields in emitted
        if args[2] == "opening_rotation_1pct_observed"
    )
    assert observed["reason"] == "pullback_not_observed"
    assert observed["scanner_promotion_price"] == 83_300
    assert observed["scanner_promotion_price_ws_curr"] == 84_600
    assert observed["opening_rotation_no_pullback_continuation_candidate"] is True
    assert (
        observed["opening_rotation_no_pullback_continuation_candidate_id"]
        == "GEN-058610-1:KRX:opening_rotation_no_pullback_continuation"
    )
    assert observed["runtime_effect"] is False
    assert observed["allowed_runtime_apply"] is False
    assert observed["actual_order_submitted"] is False
    assert observed["broker_order_forbidden"] is True
    assert not any(
        args[2] == "opening_rotation_entry_owner_handoff" for args, _fields in emitted
    )
    assert stock.get("rising_missed_buy") is None


def test_runtime_does_not_handoff_opening_rotation_source_quality_failure(monkeypatch):
    now_dt = datetime(2026, 7, 30, 10, 5)
    stock = {
        "id": 7,
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-SOURCE-GAP",
        "source_signature": "PRICE_JUMP_START",
        "intraday_high_price": 10_100,
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    source_gap_packet = _packet(10_000)
    source_gap_packet.update(
        {
            "tick_context_quality": "missing",
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        }
    )
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: source_gap_packet,
    )
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert "opening_rotation_entry_owner_handoff" not in runtime
    assert not any(
        args[2] == "opening_rotation_entry_owner_handoff" for args, _fields in emitted
    )


@pytest.mark.parametrize(
    "reason",
    sorted(
        {
            "pullback_not_observed",
            "pullback_out_of_range",
            "reacceleration_not_observed",
            "spread_too_wide",
            "buy_pressure_below_min",
            "trusted_tick_sample_below_min",
            "tick_acceleration_below_min",
            "tick_price_change_below_min",
            "volume_reacceleration_below_min",
            "micro_vwap_unavailable",
            "micro_vwap_distance_out_of_range",
            "ask_sweep_below_min",
            "post_sweep_hold_below_min",
            "bid_replenishment_below_min",
            "wall_replenishment_risk",
            "vi_proximity_risk",
        }
    ),
)
def test_opening_rotation_strategy_miss_reasons_never_handoff_to_entry_ai(reason):
    assert not handlers._opening_rotation_general_entry_handoff_allowed(
        {
            "qualified": False,
            "reason": reason,
            "quote_age_ms": 100.0,
            "quote_stale_threshold_ms": 3000.0,
            "quote_stale": False,
            "tick_context_stale": False,
            "tick_context_quality": "fresh_computed",
            "tick_aggressor_pressure_usable": True,
            "market_data_freshness_state": "fresh",
            "market_data_orderbook_state": "fresh",
        },
        direct_position=False,
    )


@pytest.mark.parametrize(
    "reason",
    [
        "quote_freshness_unavailable",
        "stale_market_context",
        "trusted_tick_context_unavailable",
        "async_context_commit_rejected",
        "feature_context_fetch_failed",
    ],
)
def test_opening_rotation_source_quality_miss_reasons_remain_fail_closed(reason):
    assert not handlers._opening_rotation_general_entry_handoff_allowed(
        {
            "qualified": False,
            "reason": reason,
            "quote_age_ms": 100.0,
            "quote_stale_threshold_ms": 3000.0,
            "quote_stale": False,
            "tick_context_stale": False,
            "tick_context_quality": "fresh_computed",
            "tick_aggressor_pressure_usable": True,
        },
        direct_position=False,
    )


def test_runtime_blocks_opening_rotation_before_async_on_promotion_price_conflict(
    monkeypatch,
):
    now_dt = datetime(2026, 7, 29, 10, 36, 59)
    stock = {
        "id": 475040,
        "name": "스트라드비전",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "SCANPROM-475040-1785299818452",
        "scanner_generation_id": "GEN-475040-1",
        "scanner_generation_observed_price": 2965,
        "current_price": 2575,
        "current_price_observed": 2575,
        "opening_rotation_1pct_state": {"peak_price": 2965},
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 2575,
        "is_trigger": False,
    }
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("conflicted price sources must block before async dispatch")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "475040",
        {
            "curr": 2655,
            "fluctuation": 3.0,
            "last_ws_update_ts": now_dt.timestamp() - 0.055,
            "last_realtime_type_ts": {"0B": now_dt.timestamp() - 0.055},
        },
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert "opening_rotation_1pct_state" not in stock
    blocked = next(
        fields
        for args, fields in emitted
        if args[2] == "opening_rotation_1pct_source_quality_blocked"
    )
    assert blocked["reason"] == "scanner_promotion_price_conflicts_with_fresh_ws"
    assert blocked["scanner_promotion_price"] == 2965
    assert blocked["scanner_promotion_price_source"] == (
        "scanner_generation_observed_price"
    )
    assert blocked["scanner_promotion_price_ws_curr"] == 2655
    assert blocked["scanner_promotion_price_gap_pct"] > 10.0
    assert blocked["allowed_runtime_apply"] is False
    assert blocked["actual_order_submitted"] is False
    assert blocked["broker_order_forbidden"] is True

    handled_again = handlers._handle_watching_opening_rotation(
        stock,
        "475040",
        {
            "curr": 2655,
            "fluctuation": 3.0,
            "last_ws_update_ts": now_dt.timestamp(),
            "last_realtime_type_ts": {"0B": now_dt.timestamp()},
        },
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled_again is True
    assert (
        sum(
            1
            for args, _fields in emitted
            if args[2] == "opening_rotation_1pct_source_quality_blocked"
        )
        == 1
    )


def test_fresh_quote_without_trusted_tape_preserves_pullback_for_repromotion():
    peak = evaluate_entry(
        previous_state=None,
        feature_packet=_packet(10_100),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=15_000,
        now_dt=datetime(2026, 7, 21, 10, 39, 59),
    )
    assert peak["reason"] == "pullback_not_observed"
    source_gap_packet = _packet(10_000)
    source_gap_packet.update(
        {
            "tick_context_quality": "missing",
            "tick_aggressor_pressure_usable": False,
            "tick_aggressor_trusted_count": 0,
        }
    )
    source_gap = evaluate_entry(
        previous_state=peak["state"],
        feature_packet=source_gap_packet,
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=15_000,
        now_dt=datetime(2026, 7, 21, 10, 40, 0),
    )

    assert source_gap["reason"] == "trusted_tick_context_unavailable"
    assert source_gap["state"]["pullback_seen"] is True
    assert source_gap["state"]["last_price"] == 10_000
    assert source_gap["opening_rotation_downstream_preview_evaluated"] is False
    assert source_gap["opening_rotation_downstream_preview_source_quality"] == (
        "trusted_tick_context_unavailable"
    )
    assert source_gap["opening_rotation_downstream_preview_pass_count"] == 0
    assert source_gap["opening_rotation_downstream_preview_first_blocker"] == (
        "trusted_tick_context_unavailable"
    )
    assert source_gap["opening_rotation_downstream_preview_metric_role"] == (
        "diagnostic"
    )
    assert (
        "standalone_buy"
        in source_gap["opening_rotation_downstream_preview_forbidden_uses"]
    )

    recovered = evaluate_entry(
        previous_state=source_gap["state"],
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 21, 10, 40, 1),
    )

    assert recovered["qualified"] is True
    assert recovered["reason"] == "pullback_reacceleration_confirmed"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("quote_age_ms", "-", "quote_freshness_unavailable"),
        ("quote_stale", True, "stale_market_context"),
        ("spread_bp", 51.0, "spread_too_wide"),
        ("buy_pressure_10t", 57.9, "buy_pressure_below_min"),
        (
            "microstructure_reaction_wall_replenishment_risk_score",
            70,
            "wall_replenishment_risk",
        ),
    ],
)
def test_entry_blocks_adverse_or_low_quality_micro_context(field, value, reason):
    packet = _packet(10_020)
    packet[field] = value
    decision = evaluate_entry(
        previous_state={
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
        feature_packet=packet,
        source_signature="REALTIME_RANK_START,BID_IMBALANCE_SURGE",
        day_change_pct=4.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20, 0),
    )
    assert decision["qualified"] is False
    assert decision["reason"] == reason


def test_stale_packet_does_not_mutate_pullback_state_or_enable_next_entry():
    stale_packet = _packet(10_000)
    stale_packet.update(
        {
            "quote_stale": True,
            "quote_age_ms": 5_000.0,
            "tick_context_stale": True,
        }
    )
    stale = evaluate_entry(
        previous_state=None,
        feature_packet=stale_packet,
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 0),
    )
    assert stale["reason"] == "stale_market_context"
    assert stale["state"]["promotion_id"] == "PROMO-TEST"
    assert set(stale["state"]) == {"promotion_id", "promotion_started_epoch"}

    fresh = evaluate_entry(
        previous_state=stale["state"],
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 1),
    )
    assert fresh["qualified"] is False
    assert fresh["reason"] == "pullback_not_observed"


def test_qualified_entry_exposes_freshness_contract_fields():
    decision = evaluate_entry(
        previous_state={
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 1),
    )
    assert decision["qualified"] is True
    assert decision["quote_stale"] is False
    assert decision["tick_context_stale"] is False
    assert decision["tick_context_quality"] == "fresh_computed"
    assert decision["tick_aggressor_pressure_usable"] is True
    assert decision["micro_vwap_available"] is True


def test_entry_window_remains_open_until_1140_but_not_after():
    config = EntryConfig()
    assert is_watch_candidate(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START",
        day_change_pct=2.0,
        now_dt=datetime(2026, 7, 20, 11, 40, 0),
        config=config,
    )
    assert not is_watch_candidate(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START",
        day_change_pct=2.0,
        now_dt=datetime(2026, 7, 20, 11, 40, 1),
        config=config,
    )


def test_rising_missed_source_overlap_is_an_opening_rotation_candidate():
    source_signature = (
        "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
    )
    assert is_watch_candidate(
        position_tag="SCANNER",
        source_signature=source_signature,
        day_change_pct=3.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
        config=EntryConfig(),
    )
    decision = evaluate_entry(
        previous_state={
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
        feature_packet=_packet(10_020),
        source_signature=source_signature,
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )
    assert decision["qualified"] is True
    assert decision["reason"] == "pullback_reacceleration_confirmed"


def test_negative_rising_missed_source_token_does_not_take_entry_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": (
            "NO_LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
        ),
    }
    assert handlers._has_rising_missed_watch_source_marker(stock) is False
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )
    assert is_watch_candidate(
        position_tag="SCANNER",
        source_signature=stock["source_signature"],
        day_change_pct=3.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
        config=EntryConfig(),
    )


def test_zero_rising_missed_diagnostics_do_not_take_opening_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "low_rebound_pct": 0.0,
        "LowReboundPct": "0.0",
        "rising_entry_relief_eligible": False,
        "rising_missed_buy": "False",
        "_scanner_rising_entry_relief_reason": "not_applicable_rising_entry_relief",
    }

    assert handlers._has_rising_missed_watch_source_marker(stock) is True
    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == ""
    )
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )


def test_rising_recheck_hints_do_not_take_opening_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "low_rebound_pct": 0.4,
        "rising_entry_relief_eligible": True,
        "_scanner_rising_entry_relief_reason": "reversal_up_watch_recheck_pending",
    }

    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == ""
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "source_signature",
            "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
        ),
        ("rising_missed_buy", True),
        ("rising_missed_lineage", "normal_buy_bridge"),
    ],
)
def test_rising_missed_lineage_alone_does_not_exclude_opening(field, value):
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        field: value,
    }

    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == ""
    )
    assert not handlers._opening_rotation_yields_to_rising_missed_owner(
        stock, {"pos_tag": "SCANNER"}
    )


def test_runtime_entry_cutoff_defaults_to_1140(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENTRY_END", raising=False)
    assert handlers._opening_rotation_entry_config().entry_end.hour == 11
    assert handlers._opening_rotation_entry_config().entry_end.minute == 40


def test_entry_time_cohorts_are_clock_aligned_and_include_1140_boundary():
    assert entry_window_version() == WINDOW_VERSION
    assert entry_time_bucket(datetime(2026, 7, 20, 9, 10)) == "09:00-09:30"
    assert entry_time_bucket(datetime(2026, 7, 20, 9, 30)) == "09:30-10:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 11, 39, 59)) == "11:30-12:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 11, 40)) == "11:30-12:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 11, 40, 1)) == "outside_entry_window"
    labels = entry_time_bucket_labels()
    assert labels[0] == "09:00-09:30"
    assert labels[-1] == "11:30-12:00"
    assert len(labels) == 6


def test_runtime_entry_cutoff_ignores_intraday_env_mutation(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENTRY_END", "10:45")
    monkeypatch.setenv("KORSTOCKSCAN_OPENING_ROTATION_1PCT_MIN_DAY_CHANGE_PCT", "4.5")
    config = handlers._opening_rotation_entry_config()
    assert config.entry_end.hour == 11
    assert config.entry_end.minute == 40
    assert config.min_day_change_pct == 1.5
    assert entry_window_version(config) == WINDOW_VERSION


def _fresh_ws_envelope(now_ts=1000.0):
    return {
        "curr": 10_000,
        "best_ask": 10_010,
        "best_bid": 9_990,
        "last_ws_update_ts": now_ts - 0.1,
    }


def _rest_envelope(now_ts=1000.0):
    return {
        "market_data_freshness_state": "rest_enriched",
        "market_data_orderbook_state": "rest_enriched",
        "market_data_effective_price_source": "ka10004_rest_orderbook",
        "market_data_effective_quote_age_ms": 100.0,
        "market_data_effective_age_basis": "absolute_timestamp:rest_received_ts",
        "market_data_effective_best_ask": 10_010,
        "market_data_effective_best_bid": 9_990,
        "curr": 10_000,
        "best_ask": 10_010,
        "best_bid": 9_990,
        "quote_age_ms": 100.0,
        "quote_stale": False,
    }


def test_opening_rotation_fresh_ws_envelope_skips_rest(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("fresh WS must not trigger REST")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        _fresh_ws_envelope(),
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "fresh_ws"
    assert fields["opening_rotation_freshness_envelope_selected_source"] == "current_ws"
    assert enriched["quote_stale"] is False


def test_opening_rotation_uses_recent_scanner_rest_envelope_for_stale_ws(
    monkeypatch,
):
    cached = _rest_envelope()
    stock = {
        "_scanner_market_data_enrichment_ws_data": cached,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in cached.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 999.8,
    }
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("scanner envelope cache must be reused")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "rest_enriched"
    assert (
        fields["opening_rotation_freshness_envelope_selected_source"]
        == "scanner_envelope_cache"
    )
    assert enriched["quote_age_ms"] == pytest.approx(300.0)


def test_opening_rotation_expired_scanner_rest_envelope_stays_blocked(monkeypatch):
    cached = _rest_envelope()
    stock = {
        "_scanner_market_data_enrichment_ws_data": cached,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in cached.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 998.5,
    }
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", None)

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["market_data_freshness_state"] == "stale"
    assert fields["opening_rotation_freshness_envelope_rest_budget_reason"] == (
        "kiwoom_token_missing"
    )
    assert enriched["quote_stale"] is True


def test_opening_rotation_stale_ws_uses_bounded_rest_quote_only(monkeypatch):
    handlers._OPENING_ROTATION_FRESHNESS_RATE_EPOCHS.clear()
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda code, timeout_ms: (
            {
                "source": "ka10004_rest_orderbook",
                "curr": 10_000,
                "best_ask": 10_010,
                "best_bid": 9_990,
                "rest_received_ts": 999.9,
            },
            "ok",
            12.5,
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "rest_enriched"
    assert fields["opening_rotation_freshness_envelope_rest_attempted"] is True
    assert enriched["curr"] == 10_000
    assert enriched["quote_stale"] is False
    assert "rest_signed_trade_ticks" not in enriched


def test_opening_rotation_unknown_quote_time_basis_remains_blocked(monkeypatch):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", None)

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        {
            "curr": 10_000,
            "best_ask": 10_010,
            "best_bid": 9_990,
            "quote_age_ms": 10.0,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["opening_rotation_freshness_envelope_rest_budget_reason"] == (
        "kiwoom_token_missing"
    )
    assert enriched["quote_stale"] is True


def test_opening_rotation_recent_conflict_overrides_fresh_ws(monkeypatch):
    conflicted = {
        **_rest_envelope(),
        "market_data_freshness_state": "conflicted",
        "market_data_orderbook_state": "conflicted",
        "market_data_effective_price_source": "ws_rest_conflicted",
    }
    stock = {
        "_scanner_market_data_enrichment_ws_data": conflicted,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in conflicted.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 999.9,
    }
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("active conflict must fail closed without another REST call")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        _fresh_ws_envelope(),
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["market_data_freshness_state"] == "conflicted"
    assert enriched["quote_stale"] is True


def test_opening_rotation_feature_packet_uses_effective_envelope(monkeypatch):
    captured = {}
    effective_ws = _rest_envelope()
    freshness_fields = {
        **{
            key: value
            for key, value in effective_ws.items()
            if key.startswith("market_data_")
        },
        "opening_rotation_freshness_envelope_ready": True,
        "opening_rotation_freshness_envelope_selected_source": (
            "scanner_envelope_cache"
        ),
    }
    monkeypatch.setattr(
        handlers,
        "_resolve_opening_rotation_freshness_envelope",
        lambda *args, **kwargs: (effective_ws, freshness_fields),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ka10003 heuristic tape must not support opening entry")
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda *args, **kwargs: [],
    )

    def _extract(ws_data, recent_ticks, recent_candles, *, now):
        captured["ws_data"] = ws_data
        return {"quote_age_ms": 9999.0, "quote_stale": True}

    monkeypatch.setattr(handlers, "extract_scalping_feature_packet", _extract)
    handlers._OPENING_ROTATION_CONTEXT_CACHE.clear()

    packet = handlers._opening_rotation_feature_packet(
        {},
        "005930",
        {"curr": 9_900, "quote_stale": True},
        now_ts=1000.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )

    assert captured["ws_data"]["curr"] == 10_000
    assert packet["quote_stale"] is False
    assert packet["quote_age_ms"] == pytest.approx(100.0)
    assert packet["quote_age_source"] == "opening_rotation_freshness_envelope"
    assert packet["market_data_effective_price_source"] == ("ka10004_rest_orderbook")


def test_stale_entry_decision_preserves_envelope_provenance():
    packet = _packet(10_000)
    packet.update(
        {
            "quote_stale": True,
            "market_data_freshness_state": "conflicted",
            "market_data_effective_price_source": "ws_rest_conflicted",
            "opening_rotation_freshness_envelope_ready": False,
            "opening_rotation_freshness_envelope_selected_source": (
                "scanner_envelope_cache"
            ),
        }
    )

    decision = evaluate_entry(
        previous_state=None,
        feature_packet=packet,
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )

    assert decision["reason"] == "stale_market_context"
    assert decision["market_data_freshness_state"] == "conflicted"
    assert decision["market_data_effective_price_source"] == "ws_rest_conflicted"
    assert decision["opening_rotation_freshness_envelope_ready"] is False


def test_entry_contract_has_no_ai_score_input():
    assert "ai_score" not in inspect.signature(evaluate_entry).parameters


@pytest.mark.parametrize(
    ("profit_rate", "held_sec", "exit_rule"),
    [
        (0.1, 300, "opening_rotation_stagnation_exit"),
        (0.4, 600, "opening_rotation_max_hold_exit"),
    ],
)
def test_exit_policy_is_cost_aware_and_deterministic(profit_rate, held_sec, exit_rule):
    decision = evaluate_exit(
        profit_rate=profit_rate,
        held_sec=held_sec,
        config=ExitConfig(),
    )
    assert decision["should_exit"] is True
    assert decision["exit_rule"] == exit_rule
    assert decision["ai_score_hard_gate"] is False


def test_exit_policy_hands_drawdown_to_holding_ai_without_strategy_stop():
    decision = evaluate_exit(profit_rate=-0.5, held_sec=20, config=ExitConfig())
    assert decision["should_exit"] is False
    assert decision["holding_ai_handoff_required"] is True
    assert decision["reason"] == "holding_ai_drawdown_trigger"


def test_exit_policy_holds_active_position_after_entry_cutoff():
    decision = evaluate_exit(profit_rate=0.45, held_sec=240)
    assert decision["should_exit"] is False
    assert decision["reason"] == "hold"


def test_runtime_branch_uses_mechanical_authority_without_pre_submit_retag(
    monkeypatch,
):
    stock = {
        "id": 7,
        "name": "테스트",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-RUNTIME-7",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "intraday_high_price": 10_100,
        "opening_rotation_1pct_state": {
            "promotion_id": "PROMO-RUNTIME-7",
            "promotion_started_epoch": datetime(2026, 7, 20, 9, 19, 59).timestamp(),
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "fluctuation": 3.5,
        "curr_price": 10_020,
        "is_trigger": False,
    }
    ws_data = {
        "curr": 10_020,
        "fluctuation": 3.5,
        "ask_tot": 80_000,
        "bid_tot": 90_000,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: _packet(10_020),
    )
    entry_logs = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: entry_logs.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        ws_data,
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is True
    assert runtime["pos_tag"] == POSITION_TAG
    assert runtime["current_ai_score"] == 0.0
    assert runtime["opening_rotation_mechanical_signal_strength"] == pytest.approx(0.8)
    assert runtime["opening_rotation_window_version"] == WINDOW_VERSION
    assert runtime["opening_rotation_decision_time_bucket"] == "09:00-09:30"
    assert stock["position_tag"] == "SCANNER"
    assert stock["opening_rotation_window_version"] == WINDOW_VERSION
    assert stock["opening_rotation_decision_time_bucket"] == "09:00-09:30"
    assert "scale_in_locked" not in stock
    assert "opening_rotation_1pct_live" not in stock
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    qualified_log = next(
        fields
        for args, fields in entry_logs
        if args[2] == "opening_rotation_1pct_qualified"
    )
    assert any(
        args[2] == "opening_rotation_watch_slot_claimed" for args, _fields in entry_logs
    )
    released_log = next(
        fields
        for args, fields in entry_logs
        if args[2] == "opening_rotation_watch_slot_released"
    )
    assert released_log["reason"] == "entry_qualified"
    assert released_log["opening_rotation_watch_slot_released"] is True
    _, replay = rotation_backtest._canonical_replay_inputs(qualified_log)
    assert replay["missing"] == ()
    assert qualified_log["opening_rotation_window_version"] == WINDOW_VERSION
    assert qualified_log["opening_rotation_decision_time_bucket"] == "09:00-09:30"


def test_full_watching_branch_never_calls_ai_for_rotation_candidate(monkeypatch):
    stock = {
        "id": 8,
        "name": "테스트",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-RUNTIME-8",
        "source_signature": "REALTIME_RANK_START,BID_IMBALANCE_SURGE",
        "intraday_high_price": 10_100,
        "opening_rotation_1pct_state": {
            "promotion_id": "PROMO-RUNTIME-8",
            "promotion_started_epoch": datetime(2026, 7, 20, 9, 19, 59).timestamp(),
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
    }
    runtime = {
        "strategy": "SCALPING",
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "curr_price": 10_020,
        "current_vpw": 125.0,
        "fluctuation": 3.5,
        "cooldowns": {},
        "event_bus": None,
        "is_trigger": False,
        "msg": "",
        "ratio": 0.10,
        "liquidity_value": None,
        "current_ai_score": 99.0,
        "ai_prob": 0.99,
        "buy_threshold": 70,
        "strong_vpw": 120,
    }
    ws_data = {
        "curr": 10_020,
        "fluctuation": 3.5,
        "ask_tot": 80_000,
        "bid_tot": 90_000,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: _packet(10_020),
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    class _ForbiddenAI:
        def __getattr__(self, name):
            raise AssertionError(f"AI access is prohibited: {name}")

    handled = handlers._handle_watching_strategy_branch(
        stock,
        "005930",
        ws_data,
        radar=None,
        ai_engine=_ForbiddenAI(),
        runtime=runtime,
        config={"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert handled is True
    assert runtime["is_trigger"] is True
    assert runtime["current_ai_score"] == 0.0


def test_broker_submit_activation_commits_rotation_tag_and_scale_in_lock():
    stock = {
        "position_tag": "SCANNER",
        "opening_rotation_1pct_state": {"phase": "QUALIFIED"},
    }
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}

    handlers._activate_opening_rotation_after_broker_submit(stock, "005930")

    assert stock["position_tag"] == POSITION_TAG
    assert stock["scale_in_locked"] is True
    assert stock["opening_rotation_1pct_live"] is True
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE


def test_opening_rotation_first_buy_fill_persists_entry_time_cohort(monkeypatch):
    events = []

    class _NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            return None

        def join(self):
            return None

    monkeypatch.setattr(sniper_execution_receipts.threading, "Thread", _NoopThread)
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda name, code, target_id, stage, **fields: events.append((stage, fields)),
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_submit_opening_rotation_profit_order",
        lambda *args, **kwargs: True,
    )
    sniper_execution_receipts.highest_prices = {}
    stock = {
        "id": 7,
        "name": "테스트",
        "code": "005930",
        "strategy": "SCALPING",
        "position_tag": POSITION_TAG,
        "opening_rotation_window_version": WINDOW_VERSION,
        "pending_entry_orders": [
            {
                "ord_no": "ROT1",
                "qty": 1,
                "filled_qty": 0,
                "price": 10_000,
                "status": "OPEN",
            }
        ],
        "entry_requested_qty": 1,
        "requested_buy_qty": 1,
    }

    sniper_execution_receipts._handle_entry_buy_execution(
        target_id=7,
        target_stock=stock,
        code="005930",
        order_no="ROT1",
        exec_price=10_000,
        exec_qty=1,
        now=datetime(2026, 7, 20, 10, 29, 59),
    )

    assert stock["opening_rotation_entry_time_bucket"] == "10:00-10:30"
    holding_started = [fields for stage, fields in events if stage == "holding_started"]
    assert holding_started[-1]["opening_rotation_entry_time_bucket"] == "10:00-10:30"
    assert holding_started[-1]["opening_rotation_window_version"] == WINDOW_VERSION


def test_general_margin_authority_promotes_from_pending_order_only_on_fill(monkeypatch):
    events = []

    class _NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            return None

        def join(self):
            return None

    monkeypatch.setattr(sniper_execution_receipts.threading, "Thread", _NoopThread)
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda name, code, target_id, stage, **fields: events.append((stage, fields)),
    )
    sniper_execution_receipts.highest_prices = {}
    stock = {
        "id": 8,
        "name": "테스트",
        "code": "005930",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "pending_entry_orders": [
            {
                "ord_no": "MARGIN1",
                "qty": 1,
                "filled_qty": 0,
                "price": 10_000,
                "status": "OPEN",
                "general_entry_margin_one_share_authorized": True,
                "general_entry_margin_authority_reason": (
                    "kt00011_applied_margin_tier_one_share_confirmed"
                ),
                "general_entry_margin_order_api": "kt10000",
                "general_entry_margin_order_leg_limit_price": 10_000,
                "general_entry_margin_order_leg_qty": 1,
                "general_entry_margin_credit_order_api_used": False,
                "general_entry_margin_scale_in_allowed": False,
                "general_entry_margin_scale_in_forbidden": True,
            }
        ],
        "entry_requested_qty": 1,
        "requested_buy_qty": 1,
    }

    assert "general_entry_margin_scale_in_forbidden" not in stock
    sniper_execution_receipts._handle_entry_buy_execution(
        target_id=8,
        target_stock=stock,
        code="005930",
        order_no="MARGIN1",
        exec_price=10_000,
        exec_qty=1,
        now=datetime(2026, 8, 13, 11, 55),
    )

    assert stock["general_entry_margin_scale_in_forbidden"] is True
    assert stock["general_entry_margin_order_api"] == "kt10000"
    assert stock["general_entry_margin_order_leg_qty"] == 1
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    holding_started = [fields for stage, fields in events if stage == "holding_started"]
    assert holding_started[-1]["general_entry_margin_one_share_authorized"] is True
    assert holding_started[-1]["general_entry_margin_scale_in_forbidden"] is True


def test_rotation_tag_activation_is_strictly_after_broker_acceptance():
    watch_source = inspect.getsource(handlers._handle_watching_opening_rotation)
    submit_source = inspect.getsource(handlers._submit_watching_triggered_entry)

    assert "_activate_opening_rotation_after_broker_submit" not in watch_source
    send_index = submit_source.index("kiwoom_orders.send_buy_order(")
    reject_guard_index = submit_source.index('if rt_cd != "0":', send_index)
    activate_index = submit_source.index(
        "_activate_opening_rotation_after_broker_submit", reject_guard_index
    )
    stage_index = submit_source.index("_stage_buy_order_submission(", activate_index)
    assert send_index < reject_guard_index < activate_index < stage_index


def test_margin_capacity_stays_inside_allocator_and_one_share_submit_contract():
    submit_source = inspect.getsource(handlers._submit_watching_triggered_entry)

    initial_margin_index = submit_source.index(
        "_apply_opening_rotation_margin_budget_authority"
    )
    initial_allocator_index = submit_source.index(
        "sizing_decision = resolve_scalping_allocation", initial_margin_index
    )
    one_share_stage_cap_index = submit_source.index(
        "stage_qty_cap=1", initial_allocator_index
    )
    latency_index = submit_source.index("evaluate_live_buy_entry(")
    final_margin_index = submit_source.index(
        '"opening_rotation_margin_pre_submit_revalidated"'
    )
    final_allocator_index = submit_source.index(
        "_revalidate_scalping_sizing_for_final_order_price", final_margin_index
    )
    one_share_plan_index = submit_source.index(
        '"opening_rotation_best_bid_one_share"', final_allocator_index
    )

    assert initial_margin_index < initial_allocator_index
    assert initial_allocator_index < one_share_stage_cap_index < latency_index
    assert final_margin_index < final_allocator_index < one_share_plan_index
    assert "kt10006" not in submit_source


def test_general_margin_capacity_uses_one_share_exact_leg_and_no_residual_contract():
    submit_source = inspect.getsource(handlers._submit_watching_triggered_entry)

    initial_margin_index = submit_source.index(
        "_apply_general_entry_margin_budget_authority"
    )
    initial_allocator_index = submit_source.index(
        "sizing_decision = resolve_scalping_allocation", initial_margin_index
    )
    pre_submit_index = submit_source.index(
        '"general_entry_margin_pre_submit_revalidated"'
    )
    final_allocator_index = submit_source.index(
        "_revalidate_scalping_sizing_for_final_order_price", pre_submit_index
    )
    leg_recheck_index = submit_source.index(
        '"general_entry_margin_order_leg_revalidated"', final_allocator_index
    )
    broker_send_index = submit_source.index(
        "kiwoom_orders.send_buy_order(", leg_recheck_index
    )

    assert initial_margin_index < initial_allocator_index < pre_submit_index
    assert pre_submit_index < final_allocator_index < leg_recheck_index
    assert leg_recheck_index < broker_send_index
    assert '"probe_expand_forbidden": True' in submit_source
    assert '"entry_split_probe_residual_expand_forbidden": True' in submit_source
    assert '"entry_split_probe_scale_in_forbidden": True' in submit_source
    assert "if general_entry_margin_authorized" in submit_source
    assert "effective_leg_price > 0" in submit_source
    assert "qty == 1" in submit_source
    assert "kt10006" not in submit_source


def test_general_margin_position_provenance_survives_receipts_and_clears_on_revive():
    keys = set(sniper_execution_receipts._GENERAL_ENTRY_MARGIN_POSITION_KEYS)

    assert keys <= set(sniper_execution_receipts._BUY_RECEIPT_SNAPSHOT_KEYS)
    assert keys <= set(sniper_execution_receipts._SELL_RECEIPT_SNAPSHOT_KEYS)
    assert keys <= set(sniper_execution_receipts._SELL_REVIVE_RESET_KEYS)
    assert keys <= set(sniper_execution_receipts._SELL_COMPLETE_RESET_KEYS)
    assert keys.isdisjoint(
        set(sniper_execution_receipts._FAST_EXIT_DECISION_RESET_KEYS)
    )


@pytest.mark.parametrize(
    "guard_name",
    sorted(handlers._OPENING_ROTATION_REDUNDANT_SUBMIT_GUARDS),
)
def test_opening_rotation_bypasses_only_declared_duplicate_submit_alpha_guards(
    guard_name,
):
    assert (
        handlers._opening_rotation_submit_guard_enforced(
            opening_rotation_active=True,
            guard_name=guard_name,
        )
        is False
    )
    assert (
        handlers._opening_rotation_submit_guard_enforced(
            opening_rotation_active=False,
            guard_name=guard_name,
        )
        is True
    )


@pytest.mark.parametrize(
    "guard_name",
    [
        "exit_authority_conflict",
        "same_symbol_loss_reentry_cooldown",
        "latency_stale_conflict",
        "observed_mark_gap",
        "caution_stale_negative_micro",
        "opening_quote_tick_1s_freshness",
        "late_entry_price_drift",
        "pre_submit_price",
        "lower_limit_live",
        "account_order_quantity",
        "margin_exact_price",
        "scanner_generation",
        "greenfield_authority",
        "broker_submit",
    ],
)
def test_opening_rotation_keeps_submit_and_hard_safety_guards(guard_name):
    assert (
        handlers._opening_rotation_submit_guard_enforced(
            opening_rotation_active=True,
            guard_name=guard_name,
        )
        is True
    )


def test_opening_rotation_duplicate_guard_bypass_has_episode_provenance(monkeypatch):
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: logs.append((args, fields)),
    )
    stock = {
        "opening_rotation_episode_id": "OREP-1",
        "opening_rotation_redundant_submit_guard_bypasses": [],
    }

    handlers._record_opening_rotation_redundant_submit_guard_bypass(
        stock,
        "005930",
        guard_name="pre_submit_liquidity",
        guard_fields={"pre_submit_liquidity_reason": "below_min_liquidity"},
    )
    handlers._record_opening_rotation_redundant_submit_guard_bypass(
        stock,
        "005930",
        guard_name="pre_submit_liquidity",
    )
    handlers._record_opening_rotation_redundant_submit_guard_bypass(
        stock,
        "005930",
        guard_name="weak_context_late_entry",
    )

    assert stock["opening_rotation_redundant_submit_guard_bypass_count"] == 2
    assert stock["opening_rotation_redundant_submit_guard_bypasses"] == [
        "pre_submit_liquidity",
        "weak_context_late_entry",
    ]
    provenance = handlers._opening_rotation_provenance_fields(stock)
    assert provenance["opening_rotation_redundant_submit_guard_bypass_count"] == 2
    assert provenance["opening_rotation_redundant_submit_guard_bypasses"] == (
        "pre_submit_liquidity,weak_context_late_entry"
    )
    assert logs[0][0][2] == "opening_rotation_redundant_submit_guard_bypassed"
    assert len(logs) == 2
    assert logs[0][1]["actual_order_submitted"] is False
    assert logs[0][1]["broker_order_forbidden"] is False
    assert "stale_or_conflict_bypass" in logs[0][1]["forbidden_uses"]


def test_opening_rotation_duplicate_guard_bypass_is_wired_before_common_blocks():
    submit_source = inspect.getsource(handlers._submit_watching_triggered_entry)

    for guard_name in handlers._OPENING_ROTATION_REDUNDANT_SUBMIT_GUARDS:
        assert f'guard_name="{guard_name}"' in submit_source
    for hard_guard_call in (
        "_is_standard_stale_submit_block",
        "_evaluate_caution_stale_negative_micro_submit_block",
        "_limit_down_live_pre_submit_guard",
        "_stage_buy_order_submission",
    ):
        assert hard_guard_call in submit_source


def test_opening_rotation_ignores_stale_generic_ai_wait_veto_without_weakening_latency(
    monkeypatch,
):
    monkeypatch.setenv(
        "KORSTOCKSCAN_KRX_DIRECT_CANARY_LIVE_AI_WAIT_BLOCK_ENABLED", "true"
    )
    now_ts = datetime(2026, 7, 20, 9, 20).timestamp()
    verdict = handlers._evaluate_krx_direct_canary_live_ai_wait_submit_block(
        strategy="SCALPING",
        stock={
            "last_watching_ai_action": "WAIT",
            "last_watching_ai_result_source": "live",
            "last_watching_ai_confirmed_at": now_ts - 1.0,
        },
        runtime={"effective_venue": "KRX"},
        latency_gate={
            "latency_state": "DANGER",
            "latency_true_ofi_direct_canary_applied": True,
        },
        entry_ai_submit_authority={},
        retry_fields={},
        now_ts=now_ts,
    )

    assert verdict["blocked"] is True
    assert (
        handlers._opening_rotation_submit_guard_enforced(
            opening_rotation_active=True,
            guard_name="krx_direct_canary_live_ai_wait",
        )
        is False
    )
    assert (
        handlers._opening_rotation_submit_guard_enforced(
            opening_rotation_active=True,
            guard_name="latency_stale_conflict",
        )
        is True
    )


def test_holding_common_trailing_does_not_overwrite_an_existing_exit_owner():
    holding_source = inspect.getsource(handlers.handle_holding_state)
    normalized_holding_source = " ".join(holding_source.split())

    assert (
        "if not is_sell_signal and trailing_stop_price > 0 "
        "and curr_p <= trailing_stop_price:"
    ) in normalized_holding_source
    assert holding_source.index(
        'exit_rule = "opening_rotation_common_trailing_stop"'
    ) < (holding_source.index('exit_rule = "protect_trailing_stop"'))


def test_exact_opening_slot_skips_preceding_rising_hook_outside_candidate_band(
    monkeypatch,
):
    handlers.COOLDOWNS = {}
    handlers.ALERTED_STOCKS = set()
    handlers.EVENT_BUS = None
    monkeypatch.setattr(
        handlers, "_observe_entry_cancel_wait_counterfactuals", lambda *a, **k: None
    )
    monkeypatch.setattr(handlers, "_log_watching_state_debug", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *a, **k: {"allowed": True},
    )
    monkeypatch.setattr(
        handlers, "_maybe_emit_entry_ai_price_skip_followup", lambda *a, **k: None
    )
    monkeypatch.setattr(
        handlers,
        "_maybe_submit_rising_missed_one_share_entry",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("rising_missed hook must not run")
        ),
    )
    branch_calls = []
    monkeypatch.setattr(
        handlers,
        "_handle_watching_strategy_branch",
        lambda *a, **k: branch_calls.append((a, k)) or False,
    )
    stock = {
        "id": 9,
        "code": "005930",
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-EXACT-OWNER",
        "opening_rotation_watch_slot_promotion_id": "PROMO-EXACT-OWNER",
        "opening_rotation_watch_slot_claimed_at_epoch": datetime(
            2026, 7, 20, 9, 19, 50
        ).timestamp(),
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_class": "not_rising_missed",
    }

    assert handlers._has_rising_missed_watch_source_marker(stock) is True
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )

    handlers.handle_watching_state(
        stock,
        "005930",
        # +7% is outside the initial Opening candidate band. Exact slot
        # ownership must still suppress a competing pre-hook.
        {"curr": 10_000, "fluctuation": 7.0},
        admin_id=1,
        now_ts=datetime(2026, 7, 20, 9, 20).timestamp(),
        now_dt=datetime(2026, 7, 20, 9, 20),
        radar=None,
        ai_engine=None,
    )
    assert branch_calls


def test_opening_slot_release_converges_when_provenance_emit_fails(monkeypatch):
    stock = {
        "status": "WATCHING",
        "scanner_promotion_id": "PROMO-RELEASE-FAIL",
        "opening_rotation_watch_slot_promotion_id": "PROMO-RELEASE-FAIL",
        "opening_rotation_watch_slot_claimed_at_epoch": 1000.0,
    }
    errors = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr(handlers, "log_error", lambda message: errors.append(message))

    released = handlers._release_opening_rotation_watch_slot_with_event(
        stock,
        "005930",
        promotion_id="PROMO-RELEASE-FAIL",
        reason="test_release",
    )

    assert released is True
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert "opening_rotation_watch_slot_claimed_at_epoch" not in stock
    assert errors and "provenance emit failed" in errors[-1]


def test_rising_missed_lineage_is_consumed_by_opening_before_scout_hook(monkeypatch):
    handlers.COOLDOWNS = {}
    handlers.ALERTED_STOCKS = set()
    handlers.EVENT_BUS = None
    monkeypatch.setattr(
        handlers, "_observe_entry_cancel_wait_counterfactuals", lambda *a, **k: None
    )
    monkeypatch.setattr(handlers, "_log_watching_state_debug", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *a, **k: {"allowed": True},
    )
    monkeypatch.setattr(
        handlers, "_maybe_emit_entry_ai_price_skip_followup", lambda *a, **k: None
    )
    scout_calls = []
    monkeypatch.setattr(
        handlers,
        "_maybe_submit_rising_missed_one_share_entry",
        lambda *a, **k: scout_calls.append((a, k)) or True,
    )
    branch_calls = []
    monkeypatch.setattr(
        handlers,
        "_handle_watching_strategy_branch",
        lambda *a, **k: branch_calls.append((a, k)) or True,
    )
    stock = {
        "id": 10,
        "code": "005930",
        "name": "테스트",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": (
            "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
        ),
    }

    handlers.handle_watching_state(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        admin_id=1,
        now_ts=datetime(2026, 7, 20, 9, 20).timestamp(),
        now_dt=datetime(2026, 7, 20, 9, 20),
        radar=None,
        ai_engine=None,
    )

    assert branch_calls
    assert scout_calls == []


def test_explicit_rising_missed_class_alone_does_not_exclude_opening():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_class": "rising_missed_raw",
    }

    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )


def test_rising_missed_scout_upgrade_cannot_be_retagged_as_rotation(monkeypatch):
    promotion_id = "PROMO-RISING-MISSED-TAKEOVER"
    emitted = []
    stock = {
        "id": 11,
        "name": "테스트",
        "status": "HOLDING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_one_share_scout": True,
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
        "opening_rotation_1pct_state": {"phase": "PULLBACK_OBSERVED"},
        "opening_rotation_mechanical_signal_strength": 0.8,
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
        "scout_upgrade_entry": True,
    }
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("opening feature path must not run for scout upgrade")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is False
    assert runtime["is_trigger"] is False
    assert stock["position_tag"] == "SCANNER"
    assert "opening_rotation_1pct_state" not in stock
    assert "opening_rotation_mechanical_signal_strength" not in stock
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE
    released = next(
        fields
        for stage, fields in emitted
        if stage == "opening_rotation_watch_slot_released"
    )
    assert released["reason"] == "specialist_owner_takeover"


def test_cancel_ambiguity_consumes_new_promotion_until_reconciliation(monkeypatch):
    emitted = []
    stock = {
        "id": 12,
        "name": "테스트",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "SCANPROM-005930-NEW",
        "opening_rotation_episode_id": "OPENROT-OLD",
        "opening_rotation_order_ambiguity": True,
        "opening_rotation_new_episode_blocked": True,
    }
    now_dt = datetime(2026, 7, 20, 9, 20)
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": now_dt.timestamp(),
        "now_dt": now_dt,
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("blocked episode must not evaluate a new promotion")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert emitted[-1][0][2] == "opening_rotation_new_episode_reconciliation_blocked"
    assert (
        emitted[-1][1]["reason"] == "broker_reconciliation_required_before_new_episode"
    )
    assert emitted[-1][1]["actual_order_submitted"] is False


def test_broker_accepted_promotion_cannot_reenter_after_unfilled_cancel(monkeypatch):
    emitted = []
    stock = {
        "id": 7,
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": "PROMO-CONSUMED",
        "opening_rotation_episode_id": "OREP-CONSUMED",
        "opening_rotation_episode_promotion_id": "PROMO-CONSUMED",
    }
    handlers._activate_opening_rotation_after_broker_submit(stock, "005930")
    stock.update(
        {
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "opening_rotation_1pct_live": False,
        }
    )
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("a consumed promotion must not be evaluated again")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is False
    assert stock["opening_rotation_consumed_promotion_id"] == "PROMO-CONSUMED"
    assert emitted[-1][0][2] == "opening_rotation_consumed_promotion_dropped"


def test_runtime_branch_does_not_fall_back_to_ai_after_1500_entry_window(monkeypatch):
    promotion_id = "PROMO-AFTER-ENTRY-WINDOW"
    stock = {
        "id": 7,
        "name": "테스트",
        "position_tag": POSITION_TAG,
        "source_signature": "PRICE_JUMP_START",
        "scanner_promotion_id": promotion_id,
        "opening_rotation_watch_slot_promotion_id": promotion_id,
    }
    runtime = {
        "pos_tag": POSITION_TAG,
        "now_ts": datetime(2026, 7, 20, 15, 1).timestamp(),
        "now_dt": datetime(2026, 7, 20, 15, 1),
        "fluctuation": 3.5,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}
    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.5},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert handled is True
    assert runtime["is_trigger"] is False
    assert "opening_rotation_watch_slot_promotion_id" not in stock
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE
    assert emitted[-1][0] == "opening_rotation_watch_slot_released"
    assert emitted[-1][1]["reason"] == "entry_window_closed"


def test_account_sync_does_not_attach_legacy_preset_exit_to_rotation_tag(monkeypatch):
    class _DB:
        get_session_calls = 0

        @staticmethod
        def get_latest_marcap(code):
            return 0

        @classmethod
        def get_session(cls):
            cls.get_session_calls += 1
            raise RuntimeError("scale-in history lookup was not expected")

    record = SimpleNamespace(
        id=11,
        stock_code="005930",
        stock_name="테스트",
        strategy="SCALPING",
        trade_type="SCALP",
        position_tag=POSITION_TAG,
        buy_qty=3,
        buy_price=10_000,
        buy_time=datetime(2026, 7, 20, 9, 20),
        scale_in_locked=True,
    )
    sniper_sync.DB = _DB()
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.EVENT_BUS = None
    monkeypatch.setattr(sniper_sync, "_recover_order_refs_from_logs", lambda code: {})

    target = sniper_sync._ensure_runtime_target(record)

    assert target["position_tag"] == POSITION_TAG
    assert target["scale_in_locked"] is True
    assert "exit_mode" not in target
    assert _DB.get_session_calls == 0

    existing = dict(target)
    existing["exit_mode"] = "SCALP_PRESET_TP"
    sniper_sync.ACTIVE_TARGETS = [existing]
    refreshed = sniper_sync._ensure_runtime_target(record)
    assert _DB.get_session_calls == 0
    assert "exit_mode" not in refreshed


def test_execution_receipt_does_not_seed_ai_score_for_rotation_tag():
    stock = {
        "strategy": "SCALPING",
        "position_tag": POSITION_TAG,
        "entry_submit_ai_score": 99,
        "pending_entry_orders": [{"ord_no": "123", "ai_score": 88}],
    }
    assert (
        sniper_execution_receipts._resolve_entry_submit_ai_score(stock, "123") is None
    )


class _OpeningSellQuery:
    def __init__(self, record):
        self.record = record
        self.filters = {}

    def filter_by(self, **kwargs):
        self.filters.update(kwargs)
        return self

    def filter(self, *args, **kwargs):
        return self

    def update(self, values):
        if any(
            getattr(self.record, key, None) != value
            for key, value in self.filters.items()
        ):
            return 0
        if "status" not in self.filters and self.record.status != "HOLDING":
            return 0
        for key, value in values.items():
            setattr(self.record, key, value)
        return 1


class _OpeningSellSession:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, _model):
        return _OpeningSellQuery(self.record)


class _OpeningSellDB:
    def __init__(self, *, target_id):
        self.record = SimpleNamespace(
            id=target_id,
            stock_code="005930",
            buy_qty=1,
            status="HOLDING",
            scale_in_locked=True,
        )

    def get_session(self):
        return _OpeningSellSession(self.record)


def _install_opening_sell_owner(monkeypatch, stock, *, target_id):
    stock.update(
        {
            "id": target_id,
            "code": "005930",
            "status": "HOLDING",
            "buy_qty": 1,
        }
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "DB",
        _OpeningSellDB(target_id=target_id),
    )


def test_fill_receipt_places_exactly_one_cost_aware_target_order(monkeypatch):
    submitted = []
    logs = []
    stock = {
        "id": 7,
        "name": "테스트",
        "position_tag": POSITION_TAG,
        "opening_rotation_episode_id": "OREP-1",
        "opening_rotation_episode_promotion_id": "PROMO-1",
        "opening_rotation_profile_id": "profile-1",
        "opening_rotation_policy_hash": "hash-1",
        "opening_rotation_policy_schema_version": "opening_rotation_runtime_policy_v2",
        "opening_rotation_margin_one_share_authorized": True,
        "opening_rotation_margin_authority_reason": (
            "kt00011_applied_margin_tier_one_share_confirmed"
        ),
        "opening_rotation_margin_rate": 40,
        "opening_rotation_margin_orderable_amount": 1_200_000,
        "opening_rotation_margin_orderable_qty_cap": 120,
        "opening_rotation_margin_requested_unit_price": 10_010,
        "opening_rotation_margin_cash_guard_bypassed": True,
        "opening_rotation_margin_order_api": "kt10000",
        "opening_rotation_margin_credit_order_api_used": False,
    }
    _install_opening_sell_owner(monkeypatch, stock, target_id=7)
    monkeypatch.setattr(
        sniper_execution_receipts.kiwoom_utils,
        "get_tick_size",
        lambda _price: 10,
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "get_trade_cost_rate",
        lambda: 0.0023,
    )
    monkeypatch.setattr(
        "src.engine.kiwoom_orders.send_sell_order_market",
        lambda **kwargs: submitted.append(kwargs)
        or {"return_code": "0", "ord_no": "0000001"},
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logs.append((args, kwargs)),
    )

    assert sniper_execution_receipts._submit_opening_rotation_profit_order(
        stock,
        code="005930",
        buy_fill_price=10_000,
        filled_qty=1,
    )
    # A duplicated BUY receipt must reuse the confirmed target ownership.
    assert sniper_execution_receipts._submit_opening_rotation_profit_order(
        stock,
        code="005930",
        buy_fill_price=10_000,
        filled_qty=1,
    )

    assert len(submitted) == 1
    assert submitted[0]["qty"] == 1
    assert submitted[0]["price"] == 10_070
    assert submitted[0]["order_type"] == "00"
    assert submitted[0]["dmst_stex_tp"] == "KRX"
    target_log = next(
        fields
        for args, fields in logs
        if args[3] == "opening_rotation_profit_target_ordered"
    )
    assert target_log["opening_rotation_margin_one_share_authorized"] is True
    assert target_log["opening_rotation_margin_rate"] == 40
    assert target_log["opening_rotation_margin_cash_guard_bypassed"] is True
    assert target_log["opening_rotation_margin_order_api"] == "kt10000"
    assert target_log["opening_rotation_margin_credit_order_api_used"] is False
    assert stock["opening_rotation_profit_target_order_no"] == "0000001"
    assert stock["preset_tp_ord_no"] == "0000001"
    assert logs[-1][0][3] == "opening_rotation_profit_target_ordered"


def test_concurrent_buy_receipts_claim_one_target_submission(monkeypatch):
    entered = Event()
    release = Event()
    submitted = []
    results = []
    stock = {
        "name": "테스트",
        "position_tag": POSITION_TAG,
        "opening_rotation_episode_id": "OREP-CONCURRENT",
    }
    _install_opening_sell_owner(monkeypatch, stock, target_id=8)
    monkeypatch.setattr(
        sniper_execution_receipts.kiwoom_utils,
        "get_tick_size",
        lambda _price: 10,
    )
    monkeypatch.setattr(
        sniper_execution_receipts, "get_trade_cost_rate", lambda: 0.0023
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: None,
    )

    def _submit(**kwargs):
        submitted.append(kwargs)
        entered.set()
        assert release.wait(timeout=2.0)
        return {"return_code": "0", "ord_no": "0000002"}

    monkeypatch.setattr("src.engine.kiwoom_orders.send_sell_order_market", _submit)

    first = Thread(
        target=lambda: results.append(
            sniper_execution_receipts._submit_opening_rotation_profit_order(
                stock,
                code="005930",
                buy_fill_price=10_000,
                filled_qty=1,
            )
        )
    )
    first.start()
    assert entered.wait(timeout=2.0)
    second_result = sniper_execution_receipts._submit_opening_rotation_profit_order(
        stock,
        code="005930",
        buy_fill_price=10_000,
        filled_qty=1,
    )
    release.set()
    first.join(timeout=2.0)

    assert not first.is_alive()
    assert results == [True]
    assert second_result is True
    assert len(submitted) == 1
    assert stock["opening_rotation_profit_target_order_no"] == "0000002"


def test_target_order_notice_without_exact_receipt_never_wins_response_race(
    monkeypatch,
):
    stock = {
        "name": "테스트",
        "position_tag": POSITION_TAG,
        "opening_rotation_episode_id": "OREP-NOTICE-RACE",
    }
    _install_opening_sell_owner(monkeypatch, stock, target_id=9)
    monkeypatch.setattr(
        sniper_execution_receipts.kiwoom_utils,
        "get_tick_size",
        lambda _price: 10,
    )
    monkeypatch.setattr(
        sniper_execution_receipts, "get_trade_cost_rate", lambda: 0.0023
    )
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: None,
    )

    def _submit(**_kwargs):
        stock["opening_rotation_profit_target_order_no"] = "0000003"
        return {"return_code": "-1", "return_msg": "response_late_after_notice"}

    monkeypatch.setattr("src.engine.kiwoom_orders.send_sell_order_market", _submit)

    assert not sniper_execution_receipts._submit_opening_rotation_profit_order(
        stock,
        code="005930",
        buy_fill_price=10_000,
        filled_qty=1,
    )
    assert "opening_rotation_profit_target_order_no" not in stock
    assert stock["opening_rotation_profit_order_protection_failed"] is True
    assert stock["opening_rotation_episode_phase"] == "TARGET_SUBMIT_FAILED"


def test_failed_target_submit_blocks_reentry_and_arms_protection_exit(monkeypatch):
    stock = {"name": "테스트", "position_tag": POSITION_TAG}
    _install_opening_sell_owner(monkeypatch, stock, target_id=10)
    monkeypatch.setattr(
        sniper_execution_receipts.kiwoom_utils,
        "get_tick_size",
        lambda _price: 10,
    )
    monkeypatch.setattr(
        "src.engine.kiwoom_orders.send_sell_order_market",
        lambda **kwargs: {"return_code": "-1", "return_msg": "rejected"},
    )

    assert not sniper_execution_receipts._submit_opening_rotation_profit_order(
        stock,
        code="005930",
        buy_fill_price=10_000,
        filled_qty=1,
    )
    assert stock["opening_rotation_profit_order_protection_failed"] is True
    assert stock["opening_rotation_new_episode_blocked"] is True
    holding_source = inspect.getsource(handlers.handle_holding_state)
    assert "opening_rotation_target_protection_failure_exit" in holding_source


def test_holding_ai_handoff_is_called_once_and_cannot_choose_buy(monkeypatch):
    calls = []
    stock = {
        "id": 7,
        "name": "테스트",
        "buy_price": 10_000,
        "opening_rotation_episode_id": "OREP-1",
    }

    class _HoldingAI:
        def evaluate_scalping_holding_score(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {"action": "BUY", "reason": "invalid scale-in suggestion"}

    monkeypatch.setattr(
        handlers, "_pre_submit_input_snapshot_has_usable_quote", lambda _ws: True
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: [{"price": 9_950}],
    )
    monkeypatch.setattr(
        handlers,
        "_get_holding_minute_candles_with_meta",
        lambda *args, **kwargs: ([{"close": 9_950}], {}),
    )
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *a, **k: None)

    first = handlers._opening_rotation_holding_ai_once(
        stock=stock,
        code="005930",
        ws_data={"curr": 9_950, "best_bid": 9_940, "best_ask": 9_950},
        ai_engine=_HoldingAI(),
        profit_rate=-0.5,
        peak_profit=0.1,
        held_sec=30,
    )
    second = handlers._opening_rotation_holding_ai_once(
        stock=stock,
        code="005930",
        ws_data={"curr": 9_940, "best_bid": 9_930, "best_ask": 9_940},
        ai_engine=_HoldingAI(),
        profit_rate=-0.6,
        peak_profit=0.1,
        held_sec=40,
    )

    assert first == second == "HOLD"
    assert len(calls) == 1
    assert stock["opening_rotation_holding_ai_called"] is True


def test_full_sell_reconciliation_releases_symbol_but_preserves_cooldown(monkeypatch):
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", {"005930"})
    monkeypatch.setattr(handlers, "COOLDOWNS", {"005930": 12345.0})
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}

    result = handlers.reconcile_scalp_reentry_after_sell_completed(
        "005930",
        profit_rate=0.4,
        exit_price=10_070,
        exit_rule="profit_target_filled",
        completed_at=1.0,
        position_tag=POSITION_TAG,
    )

    assert result["reconciled"] is True
    assert "005930" not in handlers.ALERTED_STOCKS
    assert handlers.COOLDOWNS["005930"] == 12345.0
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE


def test_ratchet_is_shadow_only_and_recorded_once_on_fresh_trusted_trend(
    monkeypatch,
):
    logs = []
    stock = {
        "opening_rotation_episode_id": "OREP-1",
        "opening_rotation_profit_target_price": 10_070,
        "opening_rotation_ratchet_shadow_price": 10_080,
    }
    ws_data = {
        "best_bid": 10_020,
        "best_ask": 10_030,
        "recent_trade_ticks": [
            {"price": 10_040},
            {"price": 10_030},
            {"price": 10_020},
        ],
    }
    monkeypatch.setattr(handlers, "_get_ws_snapshot_age_sec", lambda _ws: 0.1)
    monkeypatch.setattr(
        handlers,
        "infer_tick_aggressor_side",
        lambda tick: {
            "source": "declared_aggressor_side",
            "trade_price": tick["price"],
        },
    )
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logs.append((args, kwargs)),
    )

    handlers._record_opening_rotation_ratchet_shadow_once(
        stock, "005930", ws_data, curr_price=10_040
    )
    handlers._record_opening_rotation_ratchet_shadow_once(
        stock, "005930", ws_data, curr_price=10_040
    )

    assert stock["opening_rotation_ratchet_shadow_recorded"] is True
    assert stock["opening_rotation_ratchet_real_order_enabled"] is False
    assert len(logs) == 1
    assert logs[0][1]["real_order_changed"] is False
