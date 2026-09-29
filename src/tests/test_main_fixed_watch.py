from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import RecommendationHistory
from src.engine.scalping import main_fixed_watch as fixed


KST = ZoneInfo("Asia/Seoul")


def epoch(hour: int, minute: int = 5) -> float:
    return datetime(2026, 9, 30, hour, minute, tzinfo=KST).timestamp()


class _TestDB:
    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:")
        RecommendationHistory.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def get_session(self):
        session = self.sessions()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_active_targets(self):
        with self.get_session() as session:
            rows = session.query(RecommendationHistory).filter(
                RecommendationHistory.status.in_(
                    ("WATCHING", "BUY_ORDERED", "HOLDING", "SELL_ORDERED")
                )
            ).all()
            return [{
                "id": row.id, "code": row.stock_code, "name": row.stock_name,
                "status": row.status, "strategy": row.strategy,
                "position_tag": row.position_tag, "watch_origin": row.watch_origin,
                "watch_admission_id": row.watch_admission_id,
                "watch_generation_id": row.watch_generation_id,
                "entry_armed_at_epoch": row.entry_armed_at_epoch,
            } for row in rows]


def test_fixed_watch_route_and_post_receipt_warmup():
    assert fixed.session_route(epoch(8))["item"] == "005930_NX"
    assert fixed.session_route(epoch(10))["item"] == "005930_AL"
    assert fixed.session_route(epoch(16))["item"] == "005930_AL"
    now = epoch(10)
    route = fixed.session_route(now)
    target = {
        "watch_generation_id": fixed.generation_id(now, route),
        "entry_armed_at_epoch": now - 20,
    }
    snapshot = {
        "last_ws_item": route["item"], "curr": 100,
        "last_realtime_type_item": {"0B": route["item"], "0D": route["item"]},
        "last_realtime_type_ts": {"0B": now - 1, "0D": now - 1},
    }
    assert fixed.observation_ready(target, snapshot, now_epoch=now)[1] == "fixed_watch_post_receipt_warmup"
    assert fixed.observation_ready(target, snapshot, now_epoch=now + 10.1) == (True, "ready")
    bad = {**snapshot, "last_realtime_type_item": {"0B": "005930_NX", "0D": route["item"]}}
    assert fixed.observation_ready(target, bad, now_epoch=now + 11)[1] == "exact_0B_missing"


def test_fixed_watch_entry_source_uses_exact_session_item_and_order_route():
    import pytest
    from src.engine import sniper_state_handlers as handlers

    for hour, item, broker_route in (
        (8, "005930_NX", "NXT"),
        (10, "005930_AL", "SOR"),
        (16, "005930_AL", "SOR"),
    ):
        now = epoch(hour)
        session_route = fixed.session_route(now)
        target = {
            "code": "005930",
            "watch_origin": fixed.WATCH_ORIGIN,
            "watch_generation_id": fixed.generation_id(now, session_route),
            "broker_route": broker_route,
        }
        assert handlers._fixed_watch_entry_source_route(target, now) == {
            "item": item,
            "broker_route": broker_route,
        }
        with pytest.raises(ValueError, match="fixed_watch_entry_session_route_conflict"):
            handlers._fixed_watch_entry_source_route(
                {**target, "broker_route": "NXT" if broker_route == "SOR" else "SOR"},
                now,
            )
    assert handlers._fixed_watch_entry_source_route(
        {"code": "005930", "watch_origin": "ZERO_BASE_DISCOVERY"}, epoch(16)
    ) is None


def test_broker_flat_requires_both_exchanges_and_zero_open_orders():
    from src.engine.scalping.ai_market_snapshot import (
        _clear_broker_account_snapshot_for_tests,
        broker_symbol_verified_flat,
        publish_broker_account_snapshot,
    )

    now = epoch(10)
    try:
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX"}, open_orders=[],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_exchange_census_incomplete"
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX", "NXT"},
            open_orders=[{"stock_code": "005930", "side": "BUY", "remaining_qty": 1}],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_open_orders_nonzero"
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX", "NXT"}, open_orders=[],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now) == (True, "verified_flat")
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX", "NXT"},
            open_orders=[{"stock_code": "005930", "side": "UNKNOWN", "remaining_qty": 1}],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_open_order_row_unverified"
        publish_broker_account_snapshot(
            inventory=["malformed"], successful_exchanges={"KRX", "NXT"},
            open_orders=[], open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_inventory_rows_invalid"
        publish_broker_account_snapshot(
            inventory=[{"code": "005930", "qty": 1}, {"code": "005930", "qty": 0}],
            successful_exchanges={"KRX", "NXT"}, open_orders=[],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_inventory_rows_invalid"
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX", "NXT"},
            open_orders=["malformed"], open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_open_order_rows_invalid"
        publish_broker_account_snapshot(
            inventory=[], successful_exchanges={"KRX", "NXT"},
            open_orders=[{"stock_code": "005930", "side": "BUY", "remaining_qty": "bad"}],
            open_orders_request_succeeded=True, captured_at=now,
        )
        assert broker_symbol_verified_flat("005930", now_ts=now)[1] == "broker_open_order_row_unverified"
    finally:
        _clear_broker_account_snapshot_for_tests()


def test_fixed_watch_admission_is_idempotent_and_rearms_session(monkeypatch):
    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    db, targets = _TestDB(), []
    assert fixed.reconcile(db, targets, now_epoch=epoch(8), watch_cap=16)[0] == "armed"
    first_id = targets[0]["id"]
    first_admission = targets[0]["watch_admission_id"]
    assert targets[0]["source_signature"] == f"MAIN_FIXED_WATCH:{first_admission}"
    assert not targets[0].get("scanner_promotion_id")
    assert fixed.reconcile(db, targets, now_epoch=epoch(8) + 5, watch_cap=16)[0] == "already_watching"
    assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=16)[0] == "armed"
    assert targets[0]["id"] == first_id
    assert targets[0]["watch_admission_id"] != first_admission
    assert targets[0]["source_signature"] == f"MAIN_FIXED_WATCH:{targets[0]['watch_admission_id']}"
    assert len(db.get_active_targets()) == 1


def test_fixed_watch_new_date_preserves_old_admission_and_replaces_memory(monkeypatch):
    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    db, targets = _TestDB(), []
    first_day = epoch(10)
    assert fixed.reconcile(db, targets, now_epoch=first_day, watch_cap=16)[0] == "armed"
    old_id = targets[0]["id"]
    old_admission = targets[0]["watch_admission_id"]
    next_day = first_day + 86400
    assert fixed.reconcile(db, targets, now_epoch=next_day, watch_cap=16)[0] == "armed"
    assert len(targets) == 1
    assert targets[0]["id"] != old_id
    assert targets[0]["watch_admission_id"] != old_admission
    with db.get_session() as session:
        previous = session.get(RecommendationHistory, old_id)
        assert previous.status == "EXPIRED"
        assert previous.watch_admission_id == old_admission


def test_fixed_watch_never_displaces_a_position_or_overfills_cap(monkeypatch):
    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    db, targets = _TestDB(), []
    with db.get_session() as session:
        session.add(RecommendationHistory(
            rec_date=datetime(2026, 9, 30, tzinfo=KST).date(),
            stock_code="005930", status="HOLDING", strategy="SCALPING",
            position_tag="SCALP_BASE", buy_qty=1,
        ))
    assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=16)[0] == "same_symbol_db_position_or_watch"
    assert not any(t.get("watch_origin") == fixed.WATCH_ORIGIN for t in db.get_active_targets())

    empty_db = _TestDB()
    full = [{"code": f"{i:06d}", "status": "WATCHING", "strategy": "SCALPING"}
            for i in range(16)]
    assert fixed.reconcile(empty_db, full, now_epoch=epoch(10), watch_cap=16)[0] == "fixed_watch_slot_wait"


def test_stale_historical_watches_do_not_block_current_fixed_admission(monkeypatch):
    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    db, targets = _TestDB(), []
    with db.get_session() as session:
        for old_date, strategy in (("2026-05-12", "SCALPING"), ("2026-05-14", "MANUAL")):
            session.add(RecommendationHistory(
                rec_date=datetime.fromisoformat(old_date).date(),
                stock_code="005930", status="WATCHING", strategy=strategy,
                position_tag="SCANNER", buy_qty=0,
            ))
    assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=16)[0] == "armed"
    assert len(targets) == 1 and targets[0]["watch_origin"] == fixed.WATCH_ORIGIN
    with db.get_session() as session:
        historical = session.query(RecommendationHistory).filter(
            RecommendationHistory.stock_code == "005930",
            RecommendationHistory.watch_origin.is_(None),
        ).all()
        assert len(historical) == 2
        assert all(row.status == "WATCHING" for row in historical)


def test_disabled_watch_waits_for_verified_flat_before_expiring(monkeypatch):
    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    db, targets = _TestDB(), []
    assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=16)[0] == "armed"
    monkeypatch.setattr(fixed, "enabled", lambda: False)
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (False, "broker_snapshot_missing_or_stale"))
    assert fixed.reconcile(db, targets, now_epoch=epoch(10) + 30, watch_cap=16)[0].startswith("disabled_custody_wait")
    assert len(db.get_active_targets()) == 1
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda *_: (True, "verified_flat"))
    assert fixed.reconcile(db, targets, now_epoch=epoch(10) + 60, watch_cap=16)[0] == "disabled"
    assert db.get_active_targets() == []


def test_fixed_watch_uses_one_of_sixteen_slots_without_fifo_eviction(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main

    monkeypatch.setattr(fixed, "enabled", lambda: True)
    monkeypatch.setattr(main, "_scalping_fifo_max_active", lambda: 16)
    fixed_target = {
        "id": 900, "code": "005930", "strategy": "SCALPING",
        "position_tag": "SCALP_BASE", "status": "WATCHING",
        "watch_origin": fixed.WATCH_ORIGIN,
    }
    ordinary = [{
        "id": i + 1, "code": f"{i:06d}", "strategy": "SCALPING",
        "position_tag": "SCANNER", "status": "WATCHING",
        "entry_armed_at_epoch": epoch(10) - 100 + i,
    } for i in range(15)]
    assert fixed_target not in main._scalping_fifo_candidates(
        [fixed_target, *ordinary], epoch(10)
    )
    assert main._scalping_watch_budget_overflow_candidates(
        [fixed_target, *ordinary], epoch(10)
    ) == []
    extra = {**ordinary[-1], "id": 99, "code": "999999"}
    evicted = main._scalping_watch_budget_overflow_candidates(
        [fixed_target, *ordinary, extra], epoch(10)
    )
    assert len(evicted) == 1 and evicted[0] is not fixed_target


def test_fixed_watch_machine_lineage_uses_admission_not_fake_scanner_promotion():
    from src.engine.scalping.ai_decision_trace import bind_machine_observation_revision
    from src.engine.scalping.ai_action_outcome_calibration import _machine_evaluation_key

    state = {}
    capture = {
        "machine_capture_status": "captured",
        "watch_origin": fixed.WATCH_ORIGIN,
        "watch_admission_id": "FIXED-2026-09-30-005930-krx_regular-krx_nxt_integrated-a1",
        "scanner_promotion_id": None,
        "evaluation_attempt_id": "attempt-1",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "machine_observation_sha256": "a" * 64,
    }
    bind_machine_observation_revision(state, capture, symbol="005930", bundle_sha256="b" * 64)
    assert capture["machine_revision_schema"] == "exact_machine_revision_v1"
    key = _machine_evaluation_key({
        **capture, "stock_code": "005930", "session_bucket": "krx_regular",
        "bundle_sha256": "b" * 64,
    })
    assert key.startswith("machine-fixed:")
    assert "attempt-1" in key


def test_fixed_watch_selects_machine_policy_without_changing_scanner_population():
    from datetime import datetime
    from src.engine import kiwoom_sniper_v2 as main
    from src.engine import sniper_state_handlers as handlers

    today = datetime.now(fixed.session_contract.KST).date()
    target = {
        "code": "005930",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCALP_BASE",
        "watch_origin": fixed.WATCH_ORIGIN,
        "watch_admission_id": f"FIXED-{today}-005930-krx_regular-krx_nxt_integrated-a1",
        "watch_generation_id": "a" * 64,
    }
    assert handlers._entry_ai_policy_position_tag(target) == "SCANNER"
    assert target["position_tag"] == "SCALP_BASE"
    assert not main._is_scanner_watching_target(target)
    assert not main._is_scalping_fifo_target(target)
    assert handlers._scanner_promotion_correlation_fields(
        target, allow_runtime_hydration=False
    )["watch_origin"] == fixed.WATCH_ORIGIN
    for change in (
        {"watch_admission_id": "FIXED-2026-01-01-005930-krx_regular-a1"},
        {"watch_origin": "ZERO_BASE_DISCOVERY"},
        {"code": "000660"},
        {"watch_generation_id": ""},
    ):
        assert handlers._entry_ai_policy_position_tag({**target, **change}) == "SCALP_BASE"


def test_fixed_watch_block_case_keeps_exact_identity_and_source_gap():
    from src.engine.scalping.ai_action_outcome_calibration import build_machine_decision_case_table

    case = {
        "decision_trace_id": "fixed-trace", "evaluation_attempt_id": "fixed-attempt",
        "watch_origin": fixed.WATCH_ORIGIN, "watch_admission_id": "FIXED-a1",
        "watch_generation_id": "generation-a", "scanner_promotion_id": None,
        "decision_snapshot_id": "snapshot-a",
        "decision_ts": "2026-09-30T10:00:00+09:00", "source_date": "2026-09-30",
        "stock_code": "005930", "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR", "bundle_sha256": "a" * 64,
        "machine_action": "BLOCK", "entry_quality_path": {"status": "source_gap"},
    }
    report = build_machine_decision_case_table([case])
    assert report["case_count"] == 1
    assert report["incomplete_attempt_identity_count"] == 0
    assert report["rows"][0]["watch_origin"] == fixed.WATCH_ORIGIN
    assert report["rows"][0]["watch_admission_id"] == "FIXED-a1"
