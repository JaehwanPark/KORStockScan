from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from src.engine.scalping.early_volatility_partial_tp import (
    NXT_POLICY_VERSION,
    PREMARKET_POLICY_VERSION,
    EarlyTPRuntimeLedger,
    EarlyVolatilityTPContext,
    resolve_early_volatility_tp,
)


def _context(**overrides):
    values = {
        "position_cycle_id": "1:005930:1",
        "venue": "KRX",
        "entry_lineage": "SCANNER",
        "average_price": 10_000,
        "holding_qty": 10,
        "entry_bundle_complete": True,
        "pending_entry": False,
        "pending_add": False,
        "quote_fresh": True,
        "quote_conflict": False,
        "direction_state": "NEUTRAL",
        "observed_prices": (10_000, 10_040, 10_080),
        "observation_span_sec": 3.0,
        "tick_sample_count": 3,
        "trade_cost_rate": 0.0023,
    }
    values.update(overrides)
    return EarlyVolatilityTPContext(**values)


def test_resolver_keeps_runner_and_builds_fee_aware_sell_limit():
    decision = resolve_early_volatility_tp(_context())

    assert decision.eligible is True
    assert decision.partial_qty == 3
    assert decision.runner_qty == 7
    assert decision.limit_price >= 10_080
    assert decision.partial_qty + decision.runner_qty == 10
    assert decision.observed_range_pct == 0.8


def test_resolver_fail_closed_contracts():
    cases = [
        (_context(venue="NXT"), "venue_not_policy_cohort"),
        (_context(broker_route="NXT"), "broker_route_not_policy_allowed"),
        (_context(holding_qty=1), "runner_minimum_not_met"),
        (_context(entry_bundle_complete=False), "entry_bundle_not_terminal"),
        (_context(quote_fresh=False), "quote_source_unusable"),
        (_context(direction_state="HARD_NEGATIVE"), "direction_unusable"),
        (
            _context(observed_prices=(10_000, 10_010, 10_020)),
            "volatility_range_not_met",
        ),
        (_context(partial_already_filled=True), "single_partial_already_filled"),
    ]

    for context, expected_reason in cases:
        decision = resolve_early_volatility_tp(context)
        assert decision.eligible is False
        assert decision.reason == expected_reason
        assert decision.partial_qty == 0
        assert decision.runner_qty == context.holding_qty


def test_resolver_accepts_separate_premarket_and_nxt_policy_cohorts():
    for venue, policy_version in (
        ("PREMARKET_KRX_LIKE", PREMARKET_POLICY_VERSION),
        ("NXT", NXT_POLICY_VERSION),
    ):
        decision = resolve_early_volatility_tp(
            _context(
                venue=venue,
                allowed_venue=venue,
                policy_version=policy_version,
                broker_route="NXT",
                allowed_broker_routes=("NXT",),
            )
        )

        assert decision.eligible is True
        assert decision.policy_version == policy_version
        assert decision.venue == venue
        assert decision.broker_route == "NXT"


def test_runtime_ledger_atomic_round_trip(tmp_path):
    path = tmp_path / "ledger.json"
    ledger = EarlyTPRuntimeLedger(path)

    row = ledger.upsert(
        "cycle-1",
        state="OPEN",
        order_no="123",
        reserved_qty=3,
    )
    assert row["position_cycle_id"] == "cycle-1"
    assert ledger.get("cycle-1")["state"] == "OPEN"

    ledger.upsert("cycle-1", state="FILLED_RUNNER", filled_qty=3)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["positions"]["cycle-1"]["state"] == "FILLED_RUNNER"


def test_holding_early_tp_receipt_stays_holding_and_resets_runner_peak(
    monkeypatch, tmp_path
):
    from src.engine import sniper_execution_receipts as receipts

    class Record:
        status = "HOLDING"
        buy_qty = 10

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    stock = {
        "id": 1,
        "code": "005930",
        "name": "test",
        "status": "HOLDING",
        "buy_qty": 10,
        "early_volatility_tp_position_cycle_id": "cycle-1",
        "early_volatility_tp_ord_no": "123",
        "early_volatility_tp_requested_qty": 3,
        "early_volatility_tp_filled_qty": 0,
        "early_volatility_tp_fill_amount": 0,
    }
    monkeypatch.setattr(receipts, "DB", DB())
    monkeypatch.setattr(
        receipts,
        "_EARLY_VOLATILITY_TP_LEDGER",
        EarlyTPRuntimeLedger(tmp_path / "receipt-ledger.json"),
    )

    receipts._handle_early_volatility_tp_sell_execution(
        target_id=1,
        target_stock=stock,
        code="005930",
        order_no="123",
        exec_price=10_100,
        exec_qty=3,
        now=datetime.now(),
        safe_buy_price=10_000,
    )

    assert stock["status"] == "HOLDING"
    assert stock["buy_qty"] == 7
    assert stock["early_volatility_tp_state"] == "FILLED_RUNNER"
    assert stock["early_volatility_tp_applied"] is True
    assert stock["early_volatility_tp_runner_peak_reset_pending"] is True
    assert record.status == "HOLDING"
    assert record.buy_qty == 7


def test_execution_target_matches_early_tp_without_sell_ordered(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "early_volatility_tp_ord_no": "123",
    }
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])

    assert receipts._find_execution_target("005930", "SELL", "123") is stock


def test_execution_target_binds_unique_submitting_early_tp(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "early_volatility_tp_state": "SUBMITTING",
        "early_volatility_tp_ord_no": "",
    }
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])

    assert receipts._find_execution_target("005930", "SELL", "456") is stock
    receipts._apply_order_notice_to_target(
        stock,
        code="005930",
        exec_type="SELL",
        order_no="456",
        status="accepted",
    )
    assert stock["early_volatility_tp_ord_no"] == "456"


def test_position_cycle_reset_and_sell_snapshot_cover_early_tp_and_fast_exit():
    from src.engine import sniper_execution_receipts as receipts

    required_reset = {
        "early_volatility_tp_state",
        "early_volatility_tp_position_cycle_id",
        "early_volatility_tp_logged_observation_signature",
        "fast_exit_decision_executable_sell_price",
        "entry_split_probe_direction_reason",
        "entry_split_probe_source_quality_recheck_released",
    }
    assert required_reset.issubset(set(receipts._SELL_REVIVE_RESET_KEYS))
    assert required_reset.issubset(set(receipts._SELL_COMPLETE_RESET_KEYS))
    assert {
        "fast_exit_decision_mark_price",
        "fast_exit_decision_executable_sell_price",
        "fast_exit_decision_peak_price",
        "fast_exit_decision_quote_state",
        "fast_exit_decision_quote_reason",
    }.issubset(set(receipts._SELL_RECEIPT_SNAPSHOT_KEYS))


def test_replay_candidate_uses_observed_first_hit_and_keeps_runner():
    from src.engine.scalping.early_volatility_partial_tp_replay import (
        Trade,
        replay_candidate,
    )

    kst = timezone(timedelta(hours=9))
    terminal = datetime(2026, 7, 23, 9, 10, tzinfo=kst)
    trade = Trade(
        record_id="1",
        code="005930",
        venue="KRX",
        entry_terminal_at=terminal,
        exit_at=terminal + timedelta(seconds=30),
        exit_price=9_900,
        avg_price=10_000,
        qty=10,
        actual_submit_seen=True,
        completed_seen=True,
        events=[
            {
                "at": terminal,
                "stage": "tick",
                "price": 10_000,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=2),
                "stage": "tick",
                "price": 10_040,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=4),
                "stage": "tick",
                "price": 10_080,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
            {
                "at": terminal + timedelta(seconds=10),
                "stage": "tick",
                "price": 10_100,
                "avg_price": 10_000,
                "qty": 10,
                "add_type": "",
            },
        ],
    )

    result = replay_candidate(trade, 0.30, 0.45, 90)

    assert result is not None
    assert result["partial_qty"] == 3
    assert result["runner_qty"] == 7
    assert result["partial_qty"] + result["runner_qty"] == trade.qty
    assert result["delta_net_profit_krw"] > 0


def test_runtime_policy_requires_qualification_and_activation_epoch(
    monkeypatch, tmp_path
):
    from src.engine import sniper_state_handlers as handlers

    policy_path = tmp_path / "policy.json"
    payload = {
        "policy_version": "early_volatility_partial_tp_v1",
        "decision": "implemented_historical_real_validation_pass",
        "qualified_for_runtime": True,
        "effective_venue": "KRX",
        "broker_route": "SOR",
        "partial_ratio": 0.35,
        "target_net_profit_pct": 0.55,
        "ttl_sec": 210,
        "active_from_epoch": 1000.0,
    }
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_ACTIVE_DATE", "2026-07-23")
    monkeypatch.setenv("KORSTOCKSCAN_EARLY_VOLATILITY_TP_POLICY_FILE", str(policy_path))
    handlers._EARLY_VOLATILITY_TP_POLICY_CACHE.clear()

    policy = handlers._early_volatility_tp_policy(datetime(2026, 7, 23))

    assert policy["enabled"] is True
    assert policy["reason"] == "active"
    assert policy["partial_ratio"] == 0.35

    payload["qualified_for_runtime"] = False
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    handlers._EARLY_VOLATILITY_TP_POLICY_CACHE.clear()
    policy = handlers._early_volatility_tp_policy(datetime(2026, 7, 23))
    assert policy == {"enabled": False, "reason": "policy_not_qualified"}


def test_runtime_policy_selects_premarket_and_nxt_independently(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handlers

    for cohort, suffix, version in (
        ("PREMARKET_KRX_LIKE", "PREMARKET", PREMARKET_POLICY_VERSION),
        ("NXT", "NXT", NXT_POLICY_VERSION),
    ):
        path = tmp_path / f"{suffix.lower()}.json"
        path.write_text(
            json.dumps(
                {
                    "policy_version": version,
                    "decision": "operator_directed_fallback_applied",
                    "qualified_for_runtime": True,
                    "effective_venue": cohort,
                    "broker_route": "NXT",
                    "partial_ratio": 0.35,
                    "target_net_profit_pct": 0.55,
                    "ttl_sec": 210,
                    "active_from_epoch": 1000.0,
                }
            ),
            encoding="utf-8",
        )
        prefix = f"KORSTOCKSCAN_EARLY_VOLATILITY_TP_{suffix}"
        monkeypatch.setenv(f"{prefix}_ENABLED", "true")
        monkeypatch.setenv(f"{prefix}_ACTIVE_DATE", "2026-07-23")
        monkeypatch.setenv(f"{prefix}_POLICY_FILE", str(path))

        policy = handlers._early_volatility_tp_policy(datetime(2026, 7, 23), cohort)

        assert policy["enabled"] is True
        assert policy["cohort"] == cohort
        assert policy["broker_route"] == "NXT"
        assert policy["policy_version"] == version


def test_cancel_confirms_unfilled_absence_and_reconciles_broker_qty(
    monkeypatch, tmp_path
):
    from src.engine import sniper_state_handlers as handlers

    class Record:
        status = "HOLDING"
        buy_qty = 10

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    stock = {
        "id": 1,
        "code": "005930",
        "status": "HOLDING",
        "buy_qty": 10,
        "early_volatility_tp_position_cycle_id": "cycle-1",
        "early_volatility_tp_state": "OPEN",
        "early_volatility_tp_ord_no": "123",
        "early_volatility_tp_broker_route": "NXT",
    }
    monkeypatch.setattr(handlers, "DB", DB())
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_EARLY_VOLATILITY_TP_LEDGER",
        EarlyTPRuntimeLedger(tmp_path / "cancel-ledger.json"),
    )
    cancel_calls = []
    monkeypatch.setattr(
        handlers.sniper_trade_utils,
        "send_cancel_order_with_exchange_retry",
        lambda **kwargs: cancel_calls.append(kwargs) or {"return_code": "0"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": "005930", "qty": 7}], {"KRX"}),
    )

    assert handlers._cancel_early_volatility_tp(
        stock,
        "005930",
        reason="full_exit_precedence",
        now_ts=1000.0,
    )
    assert stock["early_volatility_tp_state"] == "CANCELLED"
    assert stock["buy_qty"] == 7
    assert record.buy_qty == 7
    assert cancel_calls[0]["dmst_stex_tp"] == "NXT"


def test_open_early_tp_ttl_is_managed_after_cohort_session_boundary(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    stock = {
        "strategy": "SCALPING",
        "early_volatility_tp_state": "OPEN",
        "early_volatility_tp_expires_at": 999.0,
        "early_volatility_tp_cohort": "PREMARKET_KRX_LIKE",
        "early_volatility_tp_broker_route": "NXT",
    }
    cancel_calls = []
    monkeypatch.setattr(
        handlers,
        "_cancel_early_volatility_tp",
        lambda *args, **kwargs: cancel_calls.append((args, kwargs)) or True,
    )

    handled = handlers._maybe_manage_early_volatility_tp(
        stock,
        "117730",
        {},
        strategy="SCALPING",
        now_ts=1000.0,
        now_dt=datetime(2026, 7, 23, 9, 0),
        quote_fields={},
    )

    assert handled is True
    assert cancel_calls[0][1]["reason"] == "ttl_expired"


def test_nxt_early_tp_requires_confirmed_symbol_eligibility(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    monkeypatch.setattr(
        handlers,
        "_resolve_holding_sell_dmst_stex_tp",
        lambda *_args, **_kwargs: {
            "blocked": False,
            "dmst_stex_tp": "NXT",
            "nxt_enabled": None,
        },
    )
    monkeypatch.setattr(
        handlers,
        "_early_volatility_tp_policy",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("policy must not load when NXT eligibility is unknown")
        ),
    )

    assert (
        handlers._maybe_manage_early_volatility_tp(
            {"status": "HOLDING"},
            "459510",
            {},
            strategy="SCALPING",
            now_ts=1000.0,
            now_dt=datetime(2026, 7, 23, 16, 15),
            quote_fields={},
        )
        is False
    )


def test_early_tp_ineligible_reason_is_logged_once_per_position_state(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    handlers._EARLY_VOLATILITY_TP_OBSERVATION_SIGNATURES.clear()
    now_dt = datetime(2026, 7, 23, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    now_ts = now_dt.timestamp()
    monkeypatch.setattr(
        handlers,
        "_resolve_holding_sell_dmst_stex_tp",
        lambda *_args, **_kwargs: {
            "blocked": False,
            "dmst_stex_tp": "SOR",
            "nxt_enabled": "not_required",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_early_volatility_tp_policy",
        lambda *_args, **_kwargs: {
            "enabled": True,
            "broker_route": "SOR",
            "policy_version": "early_volatility_partial_tp_v1",
            "active_from_epoch": now_ts - 60,
            "target_net_profit_pct": 0.55,
            "partial_ratio": 0.30,
            "ttl_sec": 150,
            "observation_window_sec": 20,
            "min_range_pct": 0.60,
            "min_tick_samples": 3,
            "min_observation_span_sec": 2.0,
        },
    )
    events = []
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda _stock, _code, stage, **fields: events.append((stage, fields)),
    )
    stock = {
        "id": 1,
        "name": "지엔씨에너지",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 41_200,
        "buy_qty": 1,
        "holding_started_at": now_ts - 3,
        "entry_execution_cohort": "KRX",
        "entry_execution_broker_route": "SOR",
        "entry_split_probe_phase": "aborted",
        "holding_price_samples": [
            {"ts": now_ts - 3, "price": 41_200},
            {"ts": now_ts - 1, "price": 41_500},
            {"ts": now_ts, "price": 41_450},
        ],
    }
    quote_fields = {
        "quote_consistency_state": "ok",
        "quote_consistency_reason": "ws_only_fresh",
        "quote_consistency_entry_blocked": False,
    }

    for _ in range(2):
        assert (
            handlers._maybe_manage_early_volatility_tp(
                stock,
                "123456",
                {"curr": 41_450},
                strategy="SCALPING",
                now_ts=now_ts,
                now_dt=now_dt,
                quote_fields=quote_fields,
            )
            is False
        )

    observed = [
        fields
        for stage, fields in events
        if stage == "early_volatility_tp_decision_observed"
    ]
    assert len(observed) == 1
    assert observed[0]["reason"] == "runner_minimum_not_met"
    assert observed[0]["eligible"] is False
    assert observed[0]["broker_order_forbidden"] is True
    assert observed[0]["holding_qty"] == 1

    # Runtime holding rows can be reconstructed between monitor loops. The
    # process-local cycle cache must still suppress the same observation even
    # when the transient stock-dict signature is absent.
    rehydrated = dict(stock)
    rehydrated.pop("early_volatility_tp_logged_observation_signature", None)
    assert (
        handlers._maybe_manage_early_volatility_tp(
            rehydrated,
            "123456",
            {"curr": 41_450},
            strategy="SCALPING",
            now_ts=now_ts,
            now_dt=now_dt,
            quote_fields=quote_fields,
        )
        is False
    )
    observed = [
        fields
        for stage, fields in events
        if stage == "early_volatility_tp_decision_observed"
    ]
    assert len(observed) == 1

    # LG전자 regression: partial residual fill left five shares, but the entry
    # bundle became terminal only after the short observation window.
    stock["name"] = "LG전자"
    stock["buy_qty"] = 5
    stock["holding_started_at"] = now_ts - 30
    for _ in range(2):
        assert (
            handlers._maybe_manage_early_volatility_tp(
                stock,
                "123456",
                {"curr": 41_450},
                strategy="SCALPING",
                now_ts=now_ts,
                now_dt=now_dt,
                quote_fields=quote_fields,
            )
            is False
        )
    observed = [
        fields
        for stage, fields in events
        if stage == "early_volatility_tp_decision_observed"
    ]
    assert len(observed) == 2
    assert observed[-1]["reason"] == "observation_window_expired"
    assert observed[-1]["holding_qty"] == 5


def test_final_runner_sell_composes_early_partial_realized_pnl(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts
    from src.engine.trade_profit import calculate_net_realized_pnl

    class Record:
        buy_price = 10_000.0
        buy_qty = 7
        position_tag = "SCANNER"
        status = "HOLDING"
        sell_price = 0
        sell_time = None
        profit_rate = 0.0

    record = Record()

    class Query:
        def filter_by(self, **_kwargs):
            return self

        def first(self):
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def query(self, _model):
            return Query()

    class DB:
        def get_session(self):
            return Session()

    class Bus:
        def publish(self, *_args, **_kwargs):
            return None

    events = []
    monkeypatch.setattr(receipts, "DB", DB())
    monkeypatch.setattr(receipts, "event_bus", Bus())
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: None)
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **fields: events.append(fields),
    )
    snapshot = {
        "name": "test",
        "code": "005930",
        "position_tag": "SCANNER",
        "early_volatility_tp_filled_qty": 3,
        "early_volatility_tp_fill_amount": 30_300,
    }

    receipts._update_db_for_sell(
        1,
        9_900,
        datetime.now(),
        snapshot,
        "SCALPING",
        False,
    )

    expected = calculate_net_realized_pnl(
        10_000, 10_100, 3
    ) + calculate_net_realized_pnl(10_000, 9_900, 7)
    assert record.status == "COMPLETED"
    assert record.buy_qty == 10
    assert record.sell_price == 9_960
    assert snapshot["realized_pnl_krw"] == expected
    assert snapshot["partial_realized_qty"] == 3
    assert snapshot["runner_realized_qty"] == 7
    assert events[-1]["realized_pnl_krw"] == expected


def test_nxt_replay_uses_current_krx_policy_when_no_nxt_hit(monkeypatch, tmp_path):
    from src.engine.scalping import early_volatility_partial_tp_replay as replay

    krx_policy = tmp_path / "krx-policy.json"
    krx_policy.write_text(
        json.dumps(
            {
                "policy_version": "early_volatility_partial_tp_v1",
                "decision": "implemented_historical_real_validation_pass",
                "qualified_for_runtime": True,
                "effective_venue": "KRX",
                "broker_route": "SOR",
                "selection_basis": "operator_directed_named_trade_bootstrap",
                "partial_ratio": 0.35,
                "target_net_profit_pct": 0.55,
                "ttl_sec": 210,
                "observation_window_sec": 120,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        replay,
        "_load_cohort_trades",
        lambda *_args, **_kwargs: ([], {"venue_missing": 2}, "test_source"),
    )

    report = replay.build_nxt_report(
        tmp_path,
        datetime(2026, 7, 23, tzinfo=timezone(timedelta(hours=9))),
        duckdb_path=None,
        fallback_policy_path=krx_policy,
    )

    assert report["eligible_trade_count"] == 0
    assert report["nxt_replay_qualified"] is False
    assert report["qualified_for_runtime"] is True
    assert report["decision"] == "operator_directed_fallback_applied"
    assert report["selected"]["partial_ratio"] == 0.35
    assert report["selected"]["target_net_profit_pct"] == 0.55
    assert report["selected"]["ttl_sec"] == 210
    assert report["fallback"]["used"] is True


def test_premarket_policy_requires_exact_named_trade_nxt_routes(monkeypatch, tmp_path):
    from src.engine.scalping import early_volatility_partial_tp_replay as replay

    krx_policy = tmp_path / "krx-policy.json"
    krx_policy.write_text(
        json.dumps(
            {
                "policy_version": "early_volatility_partial_tp_v1",
                "decision": "implemented_historical_real_validation_pass",
                "qualified_for_runtime": True,
                "effective_venue": "KRX",
                "broker_route": "SOR",
                "partial_ratio": 0.35,
                "target_net_profit_pct": 0.55,
                "ttl_sec": 210,
                "observation_window_sec": 120,
            }
        ),
        encoding="utf-8",
    )
    trades = [
        replay.Trade(record_id="1", code="117730", broker_routes={"NXT"}),
        replay.Trade(record_id="2", code="459510", broker_routes={"NXT"}),
    ]
    monkeypatch.setattr(
        replay,
        "load_operator_bootstrap_trades",
        lambda *_args, **_kwargs: (trades, {}),
    )

    report = replay.build_premarket_report(
        tmp_path,
        datetime(2026, 7, 23, tzinfo=timezone(timedelta(hours=9))),
        source_policy_path=krx_policy,
    )

    assert report["qualified_for_runtime"] is True
    assert report["broker_route"] == "NXT"
    assert report["selected"]["partial_ratio"] == 0.35
    assert report["attribution_contract"]["cohort"] == "PREMARKET_KRX_LIKE"


def test_cohort_policy_writer_records_snapshot_as_activation_floor(
    monkeypatch, tmp_path
):
    from src.engine.scalping import early_volatility_partial_tp_replay as replay

    monkeypatch.setattr(replay, "DATA_DIR", str(tmp_path))
    snapshot_at = "2026-07-23T10:20:50+09:00"
    report = {
        "policy_version": PREMARKET_POLICY_VERSION,
        "decision": "operator_directed_fallback_applied",
        "qualified_for_runtime": True,
        "effective_venue": "PREMARKET_KRX_LIKE",
        "market_session": "KRX_LIKE_PREMARKET_0800_0850",
        "broker_route": "NXT",
        "snapshot_at": snapshot_at,
        "selected": {
            "partial_ratio": 0.35,
            "target_net_profit_pct": 0.55,
            "ttl_sec": 210,
        },
    }

    _, policy_path = replay.write_cohort_artifacts(
        report, "2026-07-23", cohort="PREMARKET_KRX_LIKE"
    )
    policy = json.loads(policy_path.read_text(encoding="utf-8"))

    assert (
        policy["active_from_epoch"] == datetime.fromisoformat(snapshot_at).timestamp()
    )
