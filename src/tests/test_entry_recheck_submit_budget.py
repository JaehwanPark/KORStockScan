"""No broker calls: durable quota, crash, rejection and concurrency contracts."""

import multiprocessing
import gzip
import json

import pytest

from src.engine.scalping import entry_recheck_submit_budget as budget
from src.engine.scalping.entry_opportunity_recheck import EntryOpportunityRecheckState
from src.tests.test_entry_opportunity_recheck import _decision, _enabled_config


@pytest.fixture(autouse=True)
def isolated_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(budget, "DATA_DIR", tmp_path)
    monkeypatch.setattr(budget, "DIRECTORY", tmp_path / "budget")


def reserve(index, scope="KRX|KRX_REGULAR"):
    return budget.reserve(
        trade_date="2026-09-07",
        attempt_id=f"attempt-{index}",
        code=f"{index:06d}",
        scope=scope,
        limit=3,
    )


def test_three_unsubmitted_krx_arms_leave_nxt_submission_budget_available():
    state = EntryOpportunityRecheckState()
    config = _enabled_config(
        allowed_scopes=frozenset({"KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"})
    )
    for index in range(3):
        decision = _decision(config=config, state=state, code=f"{index:06d}")
        assert decision.allowed
        state.record_recheck(f"{index:06d}")
    assert state.daily_recheck_count == 3
    assert budget.observed_count("2026-09-07") == 0
    assert _decision(
        config=config,
        state=state,
        code="000004",
        effective_venue="NXT",
        market_session_bucket="NXT_AFTERMARKET",
    ).allowed
    assert reserve(4, "NXT|NXT_AFTERMARKET")["allowed"]


def test_only_definitive_reject_releases_quota_and_attempt_never_replays():
    for index in range(3):
        assert reserve(index)["allowed"]
    budget.settle(trade_date="2026-09-07", attempt_id="attempt-0")
    assert not reserve(4)["allowed"]  # unknown/crash remains charged
    budget.settle(
        trade_date="2026-09-07", attempt_id="attempt-0", definitive_reject=True
    )
    assert budget.observed_count("2026-09-07") == 2
    assert not reserve(0)["allowed"]
    assert reserve(4, "NXT|NXT_AFTERMARKET")["allowed"]
    budget.settle(trade_date="2026-09-07", attempt_id="attempt-4", broker_order_no="B4")
    budget.settle(trade_date="2026-09-07", attempt_id="attempt-4", broker_order_no="B4")
    assert budget.observed_count("2026-09-07") == 3
    with pytest.raises(ValueError, match="outcome_conflict"):
        budget.settle(
            trade_date="2026-09-07", attempt_id="attempt-4", definitive_reject=True
        )


def test_cross_process_race_never_exceeds_existing_total_cap():
    with multiprocessing.get_context("fork").Pool(4) as pool:
        results = pool.map(reserve, range(12))
    assert sum(result["allowed"] for result in results) == 3
    assert budget.observed_count("2026-09-07") == 3


def test_corrupt_ledger_is_not_reset_or_treated_as_zero():
    assert reserve(0)["allowed"]
    path = budget.DIRECTORY / "2026-09-07.json"
    path.write_text('{"bad":true}')
    assert budget.observed_count("2026-09-07") is None
    with pytest.raises(ValueError, match="invalid_budget_ledger"):
        reserve(1)
    assert path.read_text() == '{"bad":true}'


def test_budget_source_quality_failure_blocks_evaluation():
    assert (
        _decision(buy_recovery_cap_source_quality_ok=False).reason
        == "recheck_submit_budget_ledger_invalid"
    )


@pytest.mark.parametrize(
    "response,expected",
    [
        (None, False),
        ({}, False),
        ({"return_code": "0"}, False),
        ({"return_code": "-1"}, True),
        ({"return_code": "PAUSED"}, True),
        ({"return_code": "BUY_TIME_BLOCKED"}, True),
        ({"return_code": "-1", "rt_cd": "0"}, False),
        ({"return_code": "-1", "ord_no": "B1"}, False),
        (
            {
                "return_code": "OWNER_REGISTRY_BLOCKED",
                "owner_registry_required": True,
                "broker_order_attempted": False,
            },
            True,
        ),
        (
            {
                "return_code": "OWNER_REGISTRY_BLOCKED",
                "owner_registry_required": True,
                "broker_order_attempted": True,
            },
            False,
        ),
        ({"return_code": "-1", "owner_registry_ambiguous": True}, False),
    ],
)
def test_known_local_or_broker_reject_releases_but_unknown_acceptance_never_does(
    response, expected
):
    assert budget.definitive_no_order_rejection(response) is expected


def test_first_deployment_restores_same_day_accepted_orders_from_compressed_log():
    path = budget.DATA_DIR / "pipeline_events" / "pipeline_events_2026-09-07.jsonl.gz"
    path.parent.mkdir(parents=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for i in range(3):
            row = {
                "stock_code": f"{i:06d}",
                "fields": {
                    "entry_opportunity_recheck_submit_observed": "True",
                    "entry_opportunity_recheck_broker_order_no": f"B{i}",
                    "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
                },
            }
            handle.write(json.dumps(row) + "\n")
    assert not reserve(4, "NXT|NXT_AFTERMARKET")["allowed"]
    assert budget.observed_count("2026-09-07") == 3


def test_runtime_helper_reserves_before_io_and_keeps_ambiguous_outcome(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    monkeypatch.setattr(handlers, "entry_recheck_config_from_env", _enabled_config)
    stock = {
        "entry_opportunity_recheck_armed": True,
        "entry_opportunity_recheck_attempt_id": "runtime-attempt",
        "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
    }
    result = handlers._reserve_entry_recheck_submit_budget(stock, "005930", qty=1)
    assert result["allowed"] and result["active"]
    assert budget.observed_count(result["trade_date"]) == 1
    handlers._settle_entry_recheck_submit_budget(result)
    assert budget.observed_count(result["trade_date"]) == 1
    assert not handlers._reserve_entry_recheck_submit_budget(stock, "005930", qty=1)[
        "allowed"
    ]
    handlers._settle_entry_recheck_submit_budget(result, definitive_reject=True)
    assert budget.observed_count(result["trade_date"]) == 0


@pytest.mark.parametrize(
    "passive,standard", [(True, False), (False, True), (False, False)]
)
def test_post_reservation_delay_cannot_bypass_existing_freshness_guards(
    monkeypatch, passive, standard
):
    from src.engine import sniper_state_handlers as handlers

    assert reserve(1)["allowed"]
    reservation = {
        "active": True,
        "trade_date": "2026-09-07",
        "attempt_id": "attempt-1",
    }
    fields = {"entry_submit_revalidation_warning": "test_after_io"}
    monkeypatch.setattr(
        handlers,
        "_build_entry_submit_revalidation_fields",
        lambda *args, **kwargs: fields,
    )
    monkeypatch.setattr(
        handlers, "_is_passive_probe_stale_submit_block", lambda f: passive
    )
    monkeypatch.setattr(handlers, "_is_standard_stale_submit_block", lambda f: standard)
    allowed, observed = handlers._entry_recheck_post_reservation_guard(
        reservation, {}, {}
    )
    assert observed == fields
    assert allowed is (not passive and not standard)
    assert budget.observed_count("2026-09-07") == int(allowed)


def test_cached_quote_freshness_cannot_survive_slow_reservation(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    assert reserve(1)["allowed"]
    reservation = {
        "active": True,
        "trade_date": "2026-09-07",
        "attempt_id": "attempt-1",
    }
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        handlers,
        "_build_quote_consistency_fields",
        lambda *a, **kw: (
            {
                "quote_consistency_family": "test",
                "quote_consistency_age_ms": 10000.0,
                "normalization_runtime_effect": True,
                "quote_consistency_entry_blocked": True,
            },
            0,
            0,
            0,
        ),
    )
    monkeypatch.setattr(handlers, "_env_or_rule_bool", lambda key, default: True)
    monkeypatch.setattr(handlers, "_env_or_rule_int", lambda key, default: default)
    gate = {
        "entry_order_lifecycle": "standard",
        "quote_consistency_family": "test",
        "quote_consistency_age_ms": 10.0,
        "normalization_runtime_effect": True,
        "quote_consistency_entry_blocked": False,
    }
    allowed, fields = handlers._entry_recheck_post_reservation_guard(
        reservation, {"last_ws_update_ts": 990.0}, gate
    )
    assert allowed is False
    assert fields["quote_stale_at_submit"] is True
    assert budget.observed_count("2026-09-07") == 0
    assert gate["quote_consistency_age_ms"] == 10.0
