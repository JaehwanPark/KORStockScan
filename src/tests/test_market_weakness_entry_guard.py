from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from src.engine.risk.market_weakness_entry_guard import (
    KST,
    evaluate_market_weakness_entry_guard,
    record_market_weakness_blocked_entry,
)
from src.utils.jsonl_io import read_json_object_strict


def _now() -> datetime:
    return datetime(2026, 8, 31, 10, 0, tzinfo=KST)


def _write_state(path, *, phase="active", active_markets=None, session="2026-08-31"):
    if active_markets is None:
        active_markets = ["KOSPI"]
    path.write_text(
        json.dumps(
            {
                "market_weakness": {
                    "phase": phase,
                    "active_markets": active_markets,
                    "session_key": session,
                    "last_observation_id": "weakness-2",
                    "last_observation_as_of": "2026-08-31T09:08:00+09:00",
                }
            }
        ),
        encoding="utf-8",
    )


def test_active_latch_blocks_only_matching_listing_market(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path)

    kospi = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )
    kosdaq = evaluate_market_weakness_entry_guard(
        symbol="080220",
        owner="widget",
        now=_now(),
        state_path=state_path,
        listing_market="KOSDAQ",
    )

    assert kospi.blocked is True
    assert kospi.reason == "entry_blocked_market_weakness_active"
    assert kospi.exact_market_open_buy_cancel_allowed is True
    assert kosdaq.blocked is False
    assert kosdaq.reason == "market_weakness_active_other_market"
    assert kosdaq.exact_market_open_buy_cancel_allowed is False


def test_release_pending_remains_blocked_until_latch_release(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path, phase="release_pending")

    decision = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )

    assert decision.blocked is True
    assert decision.phase == "release_pending"
    assert decision.exact_market_open_buy_cancel_allowed is True


def test_released_or_prior_session_state_does_not_block(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path, phase="released", active_markets=[])
    released = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="widget",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )
    _write_state(state_path, session="2026-08-28")
    stale = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="widget",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )

    assert released.blocked is False
    assert stale.blocked is False
    assert stale.source_status == "state_session_mismatch"


def test_active_latch_fails_closed_when_symbol_market_is_unresolved(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path)

    decision = evaluate_market_weakness_entry_guard(
        symbol="999999",
        owner="episode",
        now=_now(),
        state_path=state_path,
        symbol_master_dir=tmp_path / "missing-master",
    )

    assert decision.blocked is True
    assert decision.reason == ("entry_blocked_market_weakness_symbol_market_unresolved")
    assert decision.exact_market_open_buy_cancel_allowed is False


def test_active_latch_with_invalid_market_scope_fails_closed(tmp_path):
    state_path = tmp_path / "state.json"
    _write_state(state_path, active_markets=[])

    decision = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )

    assert decision.blocked is True
    assert decision.reason == "entry_blocked_market_weakness_state_invalid"
    assert decision.exact_market_open_buy_cancel_allowed is False


def test_missing_or_invalid_state_is_observable_but_does_not_freeze(tmp_path):
    missing = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="widget",
        now=_now(),
        state_path=tmp_path / "missing.json",
        listing_market="KOSPI",
    )
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{not-json", encoding="utf-8")
    invalid = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="widget",
        now=_now(),
        state_path=invalid_path,
        listing_market="KOSPI",
    )

    assert missing.blocked is False
    assert missing.source_status == "state_missing"
    assert invalid.blocked is False
    assert invalid.source_status == "state_invalid"


def test_operator_rollback_env_disables_guard(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    monkeypatch.setenv(
        "KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED", "0"
    )

    decision = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )

    assert decision.blocked is False
    assert decision.source_status == "operator_rollback_disabled"


def test_blocked_entry_counterfactual_anchor_is_immutable_and_idempotent(tmp_path):
    state_path = tmp_path / "state.json"
    output_dir = tmp_path / "blocked"
    _write_state(state_path)
    decision = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )
    arguments = {
        "now": _now(),
        "scope_id": "005930:morning",
        "session": "KRX_REGULAR",
        "source_signal_id": "005930:2026-08-31:morning:entry-1",
        "signal_bar": "2026-08-31T09:59:00+09:00",
        "reference_price": 100_000,
        "target_price": 100_200,
        "required_quantity": 20,
        "expected_venues": ["SOR"],
        "output_dir": output_dir,
    }

    first = record_market_weakness_blocked_entry(decision, **arguments)
    second = record_market_weakness_blocked_entry(
        decision,
        **{
            **arguments,
            "now": _now() + timedelta(seconds=2),
        },
    )
    conflict = record_market_weakness_blocked_entry(
        decision,
        **{**arguments, "target_price": 100_300},
    )
    payload = read_json_object_strict(Path(first["path"]))

    assert first["status"] == "recorded"
    assert second["status"] == "existing_immutable_observation"
    assert second["content_sha256"] == payload["content_sha256"]
    assert conflict["status"] == "existing_immutable_observation_conflict"
    assert conflict["conflict_fields"] == ["target_price"]
    assert payload["actual_order_submitted"] is False
    assert payload["required_quantity"] == 20
    assert payload["counterfactual_contract"]["horizons_minutes"] == [
        1,
        3,
        5,
        10,
        20,
        30,
    ]


def test_blocked_entry_counterfactual_rejects_corrupt_existing_anchor(tmp_path):
    state_path = tmp_path / "state.json"
    output_dir = tmp_path / "blocked"
    _write_state(state_path)
    decision = evaluate_market_weakness_entry_guard(
        symbol="005930",
        owner="episode",
        now=_now(),
        state_path=state_path,
        listing_market="KOSPI",
    )
    arguments = {
        "now": _now(),
        "scope_id": "005930:morning",
        "session": "KRX_REGULAR",
        "source_signal_id": "005930:2026-08-31:morning:entry-1",
        "signal_bar": "2026-08-31T09:59:00+09:00",
        "reference_price": 100_000,
        "target_price": 100_200,
        "required_quantity": 20,
        "expected_venues": ["SOR"],
        "output_dir": output_dir,
    }

    first = record_market_weakness_blocked_entry(decision, **arguments)
    payload = read_json_object_strict(Path(first["path"]))
    payload["content_sha256"] = "0" * 64
    Path(first["path"]).write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    repeated = record_market_weakness_blocked_entry(
        decision,
        **{
            **arguments,
            "now": _now() + timedelta(seconds=2),
        },
    )

    assert repeated["status"] == "existing_immutable_observation_invalid"
    assert repeated["validation_errors"] == [
        "blocked_entry_content_sha256_invalid"
    ]
