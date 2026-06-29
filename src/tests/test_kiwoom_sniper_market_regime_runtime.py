import inspect
import os
import threading
import time
from types import SimpleNamespace

from src.engine import kiwoom_sniper_v2
from src.engine import sniper_market_regime
from src.utils.constants import TRADING_RULES


class _RuntimeRecordSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _RuntimeRecordDB:
    def __init__(self, record_id):
        self.record_id = record_id

    def get_session(self):
        return _RuntimeRecordSession()

    def find_reusable_watching_record(self, session, *, rec_date, stock_code, strategy=None):
        return SimpleNamespace(id=self.record_id)


class _ExpireQuery:
    def __init__(self, calls):
        self.calls = calls

    def filter(self, *conditions):
        return self

    def update(self, values, synchronize_session=False):
        self.calls.append((values, synchronize_session))
        return 1


class _ExpireSession:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, model):
        return _ExpireQuery(self.calls)


class _ExpireDB:
    def __init__(self):
        self.calls = []

    def get_session(self):
        return _ExpireSession(self.calls)


def _reset_scanner_hot_override_cache():
    with kiwoom_sniper_v2._SCANNER_HOT_RUNTIME_OVERRIDES_LOCK:
        kiwoom_sniper_v2._SCANNER_HOT_RUNTIME_OVERRIDES.update(
            {"mtime_ns": None, "values": {}, "next_check_ts": 0.0}
        )


def _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path):
    _reset_scanner_hot_override_cache()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )


def test_current_market_regime_code_returns_regime_code(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_ON",
                allow_swing_entry=True,
                swing_score=80,
            )

    monkeypatch.setattr(kiwoom_sniper_v2, "MARKET_REGIME", FakeMarketRegime())

    assert kiwoom_sniper_v2._current_market_regime_code() == "BULL"


def test_current_market_regime_code_falls_back_to_neutral(monkeypatch):
    class BrokenMarketRegime:
        def refresh_if_needed(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(kiwoom_sniper_v2, "MARKET_REGIME", BrokenMarketRegime())

    assert kiwoom_sniper_v2._current_market_regime_code() == "NEUTRAL"


def test_scanner_ws_reg_recovery_throttle_keeps_state_by_source_and_code(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_REG_RECOVERY_CODE_TTL_SEC", "20")
    last_emit_ts = {}

    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_watching_ws_snapshot_recovery",
        "240810",
        100.0,
    ) is True
    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_watching_ws_snapshot_recovery",
        "240810",
        109.9,
    ) is False
    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_watching_ws_snapshot_recovery",
        "240810",
        110.0,
    ) is False
    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_watching_ws_snapshot_recovery",
        "240810",
        120.0,
    ) is True
    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_fast_precheck_stale_ws_recovery",
        "240810",
        120.0,
    ) is False
    assert kiwoom_sniper_v2._scanner_ws_reg_recovery_throttle_allows(
        last_emit_ts,
        "scanner_watching_ws_snapshot_recovery",
        "",
        120.0,
    ) is False


def test_restore_holding_runtime_state_rehydrates_scalping_defaults(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "highest_prices", {})

    targets = [
        {
            "id": 1,
            "code": "123456",
            "name": "TEST",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "buy_price": 10000,
            "buy_qty": 5,
            "buy_time": "2026-04-08 09:10:00",
        }
    ]

    kiwoom_sniper_v2._restore_holding_runtime_state(targets)
    stock = targets[0]

    assert stock["exit_mode"] == "SCALP_PRESET_TP"
    assert int(stock["preset_tp_price"]) > 10000
    assert stock["hard_stop_pct"] == TRADING_RULES.SCALP_PRESET_HARD_STOP_PCT
    assert stock["buy_qty"] == 5
    assert stock["holding_started_at"] == "2026-04-08 09:10:00"
    assert kiwoom_sniper_v2.highest_prices["123456"] == 10000


def test_scalping_scanner_promoted_target_attaches_active_watching(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "scanner_promotion_id": "SCANPROM-005930-1000000",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "REALTIME_RANK_START",
            "current_price_observed": 70000,
            "price_delta_since_first_seen_pct": "0.50",
            "scanner_source_family": "scalping_scanner_rising_start_source_v1",
            "scanner_source_role": "primary_rising_start",
        }
    )

    assert attached is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == [
        {
            "id": 77,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "type": "SCALP",
            "buy_price": 70000,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "position_tag": "SCANNER",
            "scanner_promotion_id": "SCANPROM-005930-1000000",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "REALTIME_RANK_START",
            "current_price_observed": 70000,
            "price_delta_since_first_seen_pct": "0.50",
            "marcap": 123456789,
        }
    ]
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_runtime_target_attach"})
    ]
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "attached"
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True


def test_scalping_scanner_promoted_target_skips_immediate_capacity_overflow(monkeypatch, tmp_path):
    emitted = []
    published = []
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "1")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC", "0")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 1,
                "code": "000001",
                "name": "RISING",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "entry_armed_at_epoch": 1000.0,
                "price_delta_since_first_seen_pct": "1.0",
            }
        ],
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 2,
            "code": "000002",
            "name": "FLAT",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCANNER",
            "buy_price": 10000,
            "added_time": 1010.0,
            "entry_armed_at_epoch": 1010.0,
            "price_delta_since_first_seen_pct": "0.0",
        }
    )

    assert attached is False
    assert [target["code"] for target in kiwoom_sniper_v2.ACTIVE_TARGETS] == ["000001"]
    assert published == []
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scalping_dynamic_watch_cap_capacity"
    assert emitted[-1]["fields"]["scanner_attach_capacity_cap"] == 1
    assert emitted[-1]["fields"]["scanner_attach_capacity_watching_count"] == 1
    assert emitted[-1]["fields"]["scanner_attach_capacity_candidate_overflow"] is True
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_scanner_promoted_target_allows_higher_priority_capacity_candidate(monkeypatch, tmp_path):
    emitted = []
    published = []
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "1")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 1,
                "code": "000001",
                "name": "FLAT",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "entry_armed_at_epoch": 1000.0,
                "price_delta_since_first_seen_pct": "0.0",
            }
        ],
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 2,
            "code": "000002",
            "name": "RISING",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCANNER",
            "buy_price": 10000,
            "added_time": 1010.0,
            "entry_armed_at_epoch": 1010.0,
            "price_delta_since_first_seen_pct": "1.0",
        }
    )

    assert attached is True
    assert [target["code"] for target in kiwoom_sniper_v2.ACTIVE_TARGETS] == ["000001", "000002"]
    assert published == [("COMMAND_WS_REG", {"codes": ["000002"], "source": "scanner_runtime_target_attach"})]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "attached"
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_scanner_promoted_target_blocks_capacity_replacement_when_hot_disabled(monkeypatch, tmp_path):
    emitted = []
    published = []
    override_path = tmp_path / "operator_runtime_overrides.env"
    _reset_scanner_hot_override_cache()
    monkeypatch.setattr(kiwoom_sniper_v2, "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH", override_path)
    monkeypatch.setattr(kiwoom_sniper_v2, "_SCANNER_HOT_RUNTIME_OVERRIDE_REFRESH_SEC", 0.0)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "1")
    override_path.write_text(
        "export KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED=false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 1,
                "code": "000001",
                "name": "FLAT",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "entry_armed_at_epoch": 1000.0,
                "price_delta_since_first_seen_pct": "0.0",
            }
        ],
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 2,
            "code": "000002",
            "name": "RISING",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCANNER",
            "buy_price": 10000,
            "added_time": 1010.0,
            "entry_armed_at_epoch": 1010.0,
            "price_delta_since_first_seen_pct": "3.0",
        }
    )

    assert attached is False
    assert [target["code"] for target in kiwoom_sniper_v2.ACTIVE_TARGETS] == ["000001"]
    assert published == []
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scalping_dynamic_watch_cap_capacity"
    assert emitted[-1]["fields"]["scanner_attach_capacity_cap"] == 1
    assert emitted[-1]["fields"]["scanner_attach_capacity_watching_count"] == 1
    assert emitted[-1]["fields"]["scanner_attach_capacity_candidate_overflow"] is True
    _reset_scanner_hot_override_cache()
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_scanner_promoted_target_allows_recent_promotion_grace_capacity_candidate(monkeypatch, tmp_path):
    emitted = []
    published = []
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "1")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC", "60")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 1,
                "code": "000001",
                "name": "RISING_OLD",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "entry_armed_at_epoch": 1000.0,
                "price_delta_since_first_seen_pct": "1.0",
            }
        ],
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 2,
            "code": "000002",
            "name": "RECENT_FLAT",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCANNER",
            "buy_price": 10000,
            "added_time": 1500.0,
            "entry_armed_at_epoch": 1495.0,
            "price_delta_since_first_seen_pct": "0.0",
        }
    )

    assert attached is True
    assert [target["code"] for target in kiwoom_sniper_v2.ACTIVE_TARGETS] == ["000001", "000002"]
    assert published == [("COMMAND_WS_REG", {"codes": ["000002"], "source": "scanner_runtime_target_attach"})]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "attached"
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_scanner_promoted_target_blocks_name_code_mismatch(monkeypatch):
    emitted = []
    published = []
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "두산")
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "000150",
            "name": "아로마티카",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 5450,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "scanner_promotion_id": "SCANPROM-000150-1000000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "PRICE_JUMP_START",
            "current_price_observed": 5450,
        }
    )

    assert attached is False
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == []
    assert published == []
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scanner_identity_name_mismatch"
    assert emitted[-1]["fields"]["scanner_identity_payload_name"] == "아로마티카"
    assert emitted[-1]["fields"]["scanner_identity_db_name"] == "두산"
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True
    assert emitted[-1]["fields"]["scanner_identity_mismatch_expired"] is True
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]


def test_scalping_scanner_promoted_target_blocks_source_price_ws_mismatch(monkeypatch):
    emitted = []
    published = []
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda code: {"curr": 1_647_000}),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "000150",
            "name": "아로마티카",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 5450,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "scanner_promotion_id": "SCANPROM-000150-1000000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "PRICE_JUMP_START",
            "current_price_observed": 5450,
        }
    )

    assert attached is False
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == []
    assert published == []
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scanner_identity_price_mismatch"
    assert emitted[-1]["fields"]["scanner_identity_ws_curr"] == 1_647_000
    assert emitted[-1]["fields"]["scanner_identity_price_ratio"] > 300
    assert emitted[-1]["fields"]["scanner_identity_mismatch_expired"] is True
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]


def test_scalping_scanner_promoted_target_refresh_resets_eval_state(monkeypatch):
    emitted = []
    published = []
    existing = {
        "id": 77,
        "code": "011930",
        "name": "OLD",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "added_time": 1000.0,
        "_scanner_last_full_eval_epoch": 1500.0,
        "_scanner_fast_precheck_logged_at": 1500.0,
        "_scanner_runtime_queue_lag_logged_at": 1500.0,
        "_scanner_heavy_eval_lag_logged_at": 1500.0,
        "_scanner_heavy_queue_enter_epoch": 1500.0,
        "_scanner_fast_precheck_result": "eligible_for_heavy_entry_eval",
        "_scanner_fast_precheck_reason": "fast_precheck_pass",
        "_scanner_fast_precheck_fields": {"fast_precheck_result": "eligible_for_heavy_entry_eval"},
        "_scanner_watching_runtime_skip_logged": {"scanner_full_eval_loop_budget_deferred": 1500.0},
    }
    older_never_eval = {
        "id": 88,
        "code": "000001",
        "name": "OLDER",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1200.0,
        "added_time": 1200.0,
    }
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [older_never_eval, existing])
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    refreshed = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "011930",
            "name": "NEW",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 20500,
            "added_time": 2000.0,
            "entry_armed_at_epoch": 2000.0,
            "scanner_promotion_id": "SCANPROM-011930-2000000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "scanner_promotion_emitted_epoch": "2000.000",
            "source_signature": "PRICE_JUMP_START",
            "current_price_observed": 20500,
            "price_delta_since_first_seen_pct": "2.35",
            "comparable_flu_delta_since_first_seen": "1.10",
            "cntr_str_available": "True",
            "cntr_str": "145.5",
        }
    )

    assert refreshed is True
    assert existing["entry_armed_at_epoch"] == 2000.0
    assert existing["scanner_promotion_id"] == "SCANPROM-011930-2000000"
    assert existing["price_delta_since_first_seen_pct"] == "2.35"
    assert existing["comparable_flu_delta_since_first_seen"] == "1.10"
    assert existing["cntr_str"] == "145.5"
    for key in (
        "_scanner_last_full_eval_epoch",
        "_scanner_fast_precheck_logged_at",
        "_scanner_runtime_queue_lag_logged_at",
        "_scanner_heavy_eval_lag_logged_at",
        "_scanner_heavy_queue_enter_epoch",
        "_scanner_fast_precheck_result",
        "_scanner_fast_precheck_reason",
        "_scanner_fast_precheck_fields",
        "_scanner_watching_runtime_skip_logged",
    ):
        assert key not in existing
    ordered = kiwoom_sniper_v2._runtime_iteration_targets(
        [older_never_eval, existing],
        now_ts=2001.0,
    )
    assert [target["id"] for target in ordered] == [77, 88]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "refreshed"
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["011930"], "source": "scanner_runtime_target_refresh"})
    ]


def test_scalping_scanner_promoted_target_refresh_preserves_higher_positive_delta(monkeypatch):
    emitted = []
    published = []
    existing = {
        "id": 77,
        "code": "397030",
        "name": "에이프릴바이오",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "added_time": 1000.0,
        "scanner_promotion_id": "SCANPROM-397030-1000000",
        "scanner_promotion_reason": "price_jump_start_acceleration",
        "scanner_promotion_emitted_epoch": "1000.000",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "price_delta_since_first_seen_pct": "7.72",
        "comparable_flu_delta_since_first_seen": "7.72",
        "cntr_str": "181.0",
    }
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [existing])
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    refreshed = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "397030",
            "name": "에이프릴바이오",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 15500,
            "added_time": 2000.0,
            "entry_armed_at_epoch": 2000.0,
            "scanner_promotion_id": "SCANPROM-397030-2000000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "scanner_promotion_emitted_epoch": "2000.000",
            "source_signature": "PRICE_JUMP_START",
            "current_price_observed": 15500,
            "price_delta_since_first_seen_pct": "0.00",
            "comparable_flu_delta_since_first_seen": "0.00",
            "cntr_str_available": "True",
            "cntr_str": "190.0",
        }
    )

    assert refreshed is True
    assert existing["price_delta_since_first_seen_pct"] == "7.72"
    assert existing["comparable_flu_delta_since_first_seen"] == "7.72"
    assert existing["entry_armed_at_epoch"] == 1000.0
    assert existing["added_time"] == 1000.0
    assert existing["scanner_promotion_id"] == "SCANPROM-397030-1000000"
    assert existing["scanner_promotion_emitted_epoch"] == "1000.000"
    assert existing["source_signature"] == "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
    assert existing["cntr_str"] == "190.0"
    assert emitted[-1]["fields"]["price_delta_since_first_seen_pct"] == "7.72"
    assert emitted[-1]["fields"]["scanner_promotion_id"] == "SCANPROM-397030-1000000"
    assert emitted[-1]["fields"]["scanner_positive_delta_context_preserved"] is True
    assert emitted[-1]["fields"]["scanner_positive_delta_context_previous_pct"] == "7.72"
    assert emitted[-1]["fields"]["scanner_positive_delta_context_incoming_pct"] == "0.00"
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["397030"], "source": "scanner_runtime_target_refresh"})
    ]


def test_scanner_pipeline_stock_snapshot_preserves_positive_promotion_context():
    snapshot = kiwoom_sniper_v2._scanner_pipeline_stock_snapshot(
        {
            "id": 77,
            "name": "POSITIVE",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "scanner_promotion_id": "SCANPROM-011930-2000000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "scanner_promotion_emitted_epoch": "2000.000",
            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
            "entry_armed_at_epoch": 2000.0,
            "added_time": 2000.0,
            "current_price_observed": 20500,
            "price_delta_since_first_seen_pct": "2.35",
            "comparable_flu_delta_since_first_seen": "1.10",
            "cntr_str_available": "True",
            "cntr_str": "145.5",
            "_scanner_fast_precheck_result": "eligible_for_heavy_entry_eval",
        }
    )

    assert snapshot["price_delta_since_first_seen_pct"] == "2.35"
    assert snapshot["comparable_flu_delta_since_first_seen"] == "1.10"
    assert snapshot["current_price_observed"] == 20500
    assert snapshot["cntr_str"] == "145.5"
    assert "_scanner_fast_precheck_result" not in snapshot


def test_scalping_scanner_promoted_target_does_not_override_holding(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [{"code": "005930", "name": "SAMSUNG", "strategy": "SCALPING", "status": "HOLDING"}],
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 78,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "scanner_promotion_id": "SCANPROM-005930-1000001",
            "scanner_promotion_emitted_epoch": "1000.001",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert attached is False
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == [
        {"code": "005930", "name": "SAMSUNG", "strategy": "SCALPING", "status": "HOLDING"}
    ]
    assert published == []
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "same_symbol_active_order_or_holding"
    assert emitted[-1]["fields"]["existing_status"] == "HOLDING"
    assert emitted[-1]["fields"]["existing_actual_order_submitted"] == "not_applicable_existing_actual_order_submitted"


def test_scalping_scanner_promoted_target_ignores_non_real_same_symbol_observation(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 11,
                "code": "005930",
                "name": "SIM",
                "strategy": "SCALPING",
                "status": "HOLDING",
                "position_tag": "SIM",
                "actual_order_submitted": False,
                "simulation_owner": "scalp_ai_buy_all",
            }
        ],
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 0)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 78,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1000.0,
            "scanner_promotion_id": "SCANPROM-005930-1000001",
            "scanner_promotion_emitted_epoch": "1000.001",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert attached is True
    assert len(kiwoom_sniper_v2.ACTIVE_TARGETS) == 2
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[-1]["status"] == "WATCHING"
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_runtime_target_attach"})
    ]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "attached"


def test_scalping_scanner_promoted_target_refreshes_existing_watching_and_ws(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 10,
                "code": "005930",
                "name": "OLD",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "buy_price": 69000,
            }
        ],
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    refreshed = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "005930",
            "name": "NEW",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1001.0,
            "scanner_promotion_id": "SCANPROM-005930-1001000",
            "scanner_promotion_emitted_epoch": "1001.000",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert refreshed is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["id"] == 77
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["name"] == "NEW"
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["buy_price"] == 70000
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["entry_armed_at_epoch"] == 1001.0
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_runtime_target_refresh"})
    ]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "refreshed"


def test_scalping_scanner_promoted_target_refreshes_recency_from_promotion_epoch(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 10,
                "code": "005930",
                "name": "OLD",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "buy_price": 69000,
                "entry_armed_at_epoch": 900.0,
            }
        ],
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    refreshed = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "005930",
            "name": "NEW",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1001.0,
            "scanner_promotion_id": "SCANPROM-005930-1200000",
            "scanner_promotion_emitted_epoch": "1200.000",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert refreshed is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["entry_armed_at_epoch"] == 1200.0
    assert kiwoom_sniper_v2._runtime_iteration_targets(kiwoom_sniper_v2.ACTIVE_TARGETS, now_ts=1205.0)[0]["id"] == 77
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_runtime_target_refresh"})
    ]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "refreshed"


def test_scalping_scanner_promoted_target_hydrates_missing_record_id(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", _RuntimeRecordDB(record_id=88))
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 0)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "scanner_promotion_id": "SCANPROM-005930-1001001",
            "scanner_promotion_emitted_epoch": "1001.001",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert attached is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["id"] == 88
    assert emitted[-1]["fields"]["runtime_record_id"] == 88
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_runtime_target_attach"})
    ]


def test_runtime_added_time_uses_scanner_entry_armed_epoch():
    target = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "added_time": 2000.0,
        "entry_armed_at_epoch": 1234.5,
    }

    assert kiwoom_sniper_v2._runtime_added_time_for_target(target, now_ts=3000.0) == 1234.5


def test_runtime_added_time_keeps_non_scanner_added_time():
    target = {
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "added_time": 2000.0,
        "entry_armed_at_epoch": 1234.5,
    }

    assert kiwoom_sniper_v2._runtime_added_time_for_target(target, now_ts=3000.0) == 2000.0


def test_scalping_fifo_candidates_preserve_scanner_entry_armed_order():
    watching = [
        {
            "id": 1,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "added_time": 3000.0,
            "entry_armed_at_epoch": 900.0,
        },
        {
            "id": 2,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "added_time": 1000.0,
            "entry_armed_at_epoch": 2500.0,
        },
        {
            "id": 3,
            "strategy": "SCALPING",
            "position_tag": "VCP_CANDID",
            "added_time": 100.0,
            "entry_armed_at_epoch": 100.0,
        },
        {
            "id": 4,
            "strategy": "KOSPI_ML",
            "position_tag": "BASE",
            "added_time": 10.0,
        },
    ]

    ordered = kiwoom_sniper_v2._scalping_fifo_candidates(watching, now_ts=4000.0)

    assert [target["id"] for target in ordered] == [1, 2]


def test_runtime_iteration_targets_prioritizes_recent_scanner_without_mutating_targets():
    targets = [
        {"id": "holding", "code": "000004", "status": "HOLDING", "strategy": "SCALPING"},
        {"id": "old", "code": "000001", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER", "entry_armed_at_epoch": 1000.0},
        {"id": "base", "code": "000003", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCALP_BASE", "added_time": 900.0},
        {"id": "new", "code": "000002", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER", "entry_armed_at_epoch": 1200.0},
        {"id": "ordered", "code": "000005", "status": "BUY_ORDERED", "strategy": "SCALPING"},
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1300.0)

    assert [target["id"] for target in ordered] == ["ordered", "holding", "new", "old", "base"]
    assert [target["id"] for target in targets] == ["holding", "old", "base", "new", "ordered"]


def test_runtime_iteration_targets_moves_non_real_holding_behind_scanner():
    targets = [
        {"id": "sim_holding", "code": "000010", "status": "HOLDING", "strategy": "SCALPING", "simulation_owner": "scalp_ai_buy_all", "actual_order_submitted": False},
        {"id": "probe_holding", "code": "000011", "status": "HOLDING", "strategy": "SWING", "swing_intraday_probe": True},
        {"id": "real_holding", "code": "000012", "status": "HOLDING", "strategy": "SCALPING", "actual_order_submitted": True},
        {"id": "scanner", "code": "000013", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER", "entry_armed_at_epoch": 1200.0},
        {"id": "ordered", "code": "000014", "status": "SELL_ORDERED", "strategy": "SCALPING"},
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1300.0)
    context = kiwoom_sniper_v2._runtime_queue_context(targets, now_ts=1300.0)

    assert [target["id"] for target in ordered] == ["ordered", "real_holding", "scanner", "sim_holding", "probe_holding"]
    assert [target["id"] for target in targets] == ["sim_holding", "probe_holding", "real_holding", "scanner", "ordered"]
    assert context["real_holding_count"] == 1
    assert context["non_real_holding_count"] == 2
    assert context["pre_scanner_runtime_count"] == 2


def test_runtime_iteration_targets_uses_added_time_when_scanner_armed_epoch_missing():
    targets = [
        {"id": "old", "code": "000001", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER", "added_time": 1000.0},
        {"id": "new", "code": "000002", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER", "added_time": 1200.0},
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1300.0)

    assert [target["id"] for target in ordered] == ["new", "old"]


def test_runtime_iteration_targets_prioritizes_due_strength_recheck_scanner():
    targets = [
        {
            "id": "new_never_eval",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1300.0,
        },
        {
            "id": "pending_recheck",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1200.0,
            "_scanner_last_full_eval_epoch": 1400.0,
            "entry_strength_momentum_recheck_pending": True,
            "entry_strength_momentum_recheck_after_epoch": 1499.0,
        },
        {
            "id": "real_holding",
            "code": "000003",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "actual_order_submitted": True,
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1500.0)

    assert [target["id"] for target in ordered] == [
        "real_holding",
        "pending_recheck",
        "new_never_eval",
    ]


def test_scanner_strength_recheck_waiting_waits_until_due_epoch():
    target = {
        "entry_strength_momentum_recheck_pending": True,
        "entry_strength_momentum_recheck_after_epoch": 1502.0,
    }

    assert kiwoom_sniper_v2._scanner_strength_recheck_waiting(target, now_ts=1500.0) is True
    assert kiwoom_sniper_v2._scanner_strength_recheck_pending(target, now_ts=1500.0) is False
    assert kiwoom_sniper_v2._scanner_strength_recheck_waiting(target, now_ts=1502.0) is False
    assert kiwoom_sniper_v2._scanner_strength_recheck_pending(target, now_ts=1502.0) is True


def test_runtime_iteration_targets_round_robins_scanner_full_eval():
    targets = [
        {
            "id": "processed_new",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1300.0,
            "_scanner_last_full_eval_epoch": 1400.0,
        },
        {
            "id": "never_eval_old",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1200.0,
        },
        {
            "id": "processed_oldest_eval",
            "code": "000003",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1100.0,
            "_scanner_last_full_eval_epoch": 1390.0,
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1500.0)

    assert [target["id"] for target in ordered] == [
        "never_eval_old",
        "processed_oldest_eval",
        "processed_new",
    ]


def test_runtime_iteration_targets_prioritizes_positive_scanner_delta_before_zero_delta():
    targets = [
        {
            "id": "zero_delta_newer",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1500.0,
            "price_delta_since_first_seen_pct": "0.00",
        },
        {
            "id": "positive_delta_older",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "13.95",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["positive_delta_older", "zero_delta_newer"]


def test_runtime_iteration_targets_orders_positive_scanner_by_delta_magnitude():
    targets = [
        {
            "id": "small_positive",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1500.0,
            "price_delta_since_first_seen_pct": "0.70",
        },
        {
            "id": "large_positive",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "13.95",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["large_positive", "small_positive"]


def test_runtime_iteration_targets_prioritizes_due_rising_recheck():
    targets = [
        {
            "id": "evaluated_positive",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "_scanner_last_full_eval_epoch": 1500.0,
            "price_delta_since_first_seen_pct": "1.20",
        },
        {
            "id": "due_recheck",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1450.0,
            "_scanner_last_full_eval_epoch": 1510.0,
            "_scanner_rising_cooldown_recheck_after_epoch": 1599.0,
            "price_delta_since_first_seen_pct": "0.80",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["due_recheck", "evaluated_positive"]


def test_runtime_iteration_targets_prioritizes_due_terminal_hardgate_recheck():
    targets = [
        {
            "id": "evaluated_positive",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "_scanner_last_full_eval_epoch": 1500.0,
            "price_delta_since_first_seen_pct": "1.20",
        },
        {
            "id": "due_terminal_hardgate_recheck",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1450.0,
            "_scanner_last_full_eval_epoch": 1510.0,
            "_scanner_rising_terminal_hardgate_recheck_after_epoch": 1599.0,
            "price_delta_since_first_seen_pct": "0.80",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["due_terminal_hardgate_recheck", "evaluated_positive"]


def test_runtime_iteration_targets_delays_cooldown_waiting_scanner_behind_fresh_candidate():
    targets = [
        {
            "id": "cooldown_waiting",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1500.0,
            "_scanner_rising_cooldown_recheck_after_epoch": 1660.0,
            "price_delta_since_first_seen_pct": "5.00",
        },
        {
            "id": "fresh_candidate",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "1.20",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["fresh_candidate", "cooldown_waiting"]


def test_runtime_iteration_targets_promotes_cooldown_recheck_when_due():
    targets = [
        {
            "id": "cooldown_due",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1500.0,
            "_scanner_rising_cooldown_recheck_after_epoch": 1599.0,
            "price_delta_since_first_seen_pct": "0.80",
        },
        {
            "id": "fresh_candidate",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "1.20",
        },
    ]

    ordered = kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1600.0)

    assert [target["id"] for target in ordered] == ["cooldown_due", "fresh_candidate"]


def test_scanner_promotion_latency_trace_fields_measure_ws_and_heavy_latency():
    target = {
        "id": 77,
        "code": "123456",
        "name": "TEST",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_id": "SCANPROM-123456-1000",
        "scanner_promotion_emitted_epoch": "1000.000",
        "source_signature": "REALTIME_RANK_START",
        "_scanner_fast_precheck_result": "eligible_for_heavy_entry_eval",
        "_scanner_fast_precheck_reason": "fast_precheck_pass",
    }
    ws_data = {
        "curr": 10000,
        "last_realtime_type_ts": {"0B": 1002.5},
        "strength_momentum_history": [{"ts": 1003.0}],
    }

    fields = kiwoom_sniper_v2._scanner_promotion_latency_trace_fields(
        target,
        ws_data,
        now_ts=1005.0,
        trace_phase="fast_precheck",
        fast_precheck_fields={
            "fast_precheck_result": "eligible_for_heavy_entry_eval",
            "fast_precheck_reason": "fast_precheck_pass",
        },
        heavy_queue_enter_epoch=1004.0,
    )

    assert fields["decision_authority"] == "real_scalping_scanner_latency_observation_only"
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["promotion_to_trace_sec"] == 5.0
    assert fields["promotion_to_last_0b_sec"] == 2.5
    assert fields["last_0b_to_trace_sec"] == 2.5
    assert fields["promotion_to_strength_history_sec"] == 3.0
    assert fields["heavy_queue_enter_epoch"] == "1004.000"
    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"


def test_scanner_positive_delta_uses_promotion_fallback_when_stock_delta_is_zero(monkeypatch):
    def fake_find_context(stock, *, min_delta, require_bid_imbalance):
        assert min_delta == 0.5
        assert require_bid_imbalance is False
        return {
            "allowed": True,
            "price_delta_since_first_seen_pct": "7.80",
            "scanner_context_source": "promotion_event_fallback",
            "scanner_context_emitted_epoch": "1782175601.000",
            "scanner_promotion_reason": "price_jump_start_acceleration",
            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE,REALTIME_RANK_START",
        }

    stock = {
        "code": "010690",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.00",
    }
    monkeypatch.setattr(
        kiwoom_sniper_v2.sniper_state_handlers,
        "_find_scanner_rising_strength_context",
        fake_find_context,
    )

    assert kiwoom_sniper_v2._scanner_positive_delta_value(stock) == 7.8
    assert stock["price_delta_since_first_seen_pct"] == "7.80"
    assert stock["_scanner_rising_context_source"] == "promotion_event_fallback"


def test_scalping_fifo_overflow_preserves_unevaluated_scanner_before_generic_watching(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    targets = [
        {
            "id": "scanner_never_eval_old",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1000.0,
        },
        {
            "id": "generic_new",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "MIDDLE",
            "added_time": 1400.0,
        },
        {
            "id": "scanner_evaluated",
            "code": "000003",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1300.0,
            "_scanner_last_full_eval_epoch": 1450.0,
        },
    ]

    overflow_order = kiwoom_sniper_v2._scalping_fifo_overflow_candidates(targets, now_ts=1500.0)

    assert [target["id"] for target in overflow_order] == [
        "generic_new",
        "scanner_evaluated",
        "scanner_never_eval_old",
    ]


def test_scalping_fifo_overflow_preserves_positive_scanner_before_zero_delta_scanner(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    targets = [
        {
            "id": "positive_delta_old",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1000.0,
            "price_delta_since_first_seen_pct": "13.95",
        },
        {
            "id": "zero_delta_new",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "0.00",
        },
    ]

    overflow_order = kiwoom_sniper_v2._scalping_fifo_overflow_candidates(targets, now_ts=1500.0)

    assert [target["id"] for target in overflow_order] == ["zero_delta_new", "positive_delta_old"]


def test_scalping_fifo_overflow_preserves_evaluated_rising_scanner_before_zero_delta_scanner(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    targets = [
        {
            "id": "evaluated_positive_delta_old",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1000.0,
            "_scanner_last_full_eval_epoch": 1200.0,
            "price_delta_since_first_seen_pct": "2.35",
        },
        {
            "id": "zero_delta_new",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1400.0,
            "price_delta_since_first_seen_pct": "0.00",
        },
    ]

    overflow_order = kiwoom_sniper_v2._scalping_fifo_overflow_candidates(targets, now_ts=1500.0)

    assert [target["id"] for target in overflow_order] == [
        "zero_delta_new",
        "evaluated_positive_delta_old",
    ]


def test_scalping_fifo_overflow_preserves_recent_scanner_promotion_grace(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC", "60")
    targets = [
        {
            "id": "positive_delta_old",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1000.0,
            "price_delta_since_first_seen_pct": "1.20",
        },
        {
            "id": "recent_zero_delta",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1495.0,
            "price_delta_since_first_seen_pct": "0.00",
        },
    ]

    overflow_order = kiwoom_sniper_v2._scalping_fifo_overflow_candidates(targets, now_ts=1500.0)

    assert [target["id"] for target in overflow_order] == ["positive_delta_old", "recent_zero_delta"]


def test_scalping_fifo_overflow_keeps_scanner_candidates_without_mutating_input_order(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    targets = [
        {
            "id": "scanner_never_eval",
            "code": "000001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1200.0,
        },
        {
            "id": "generic_old",
            "code": "000002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "MIDDLE",
            "added_time": 1100.0,
        },
    ]

    overflow_order = kiwoom_sniper_v2._scalping_fifo_overflow_candidates(targets, now_ts=1500.0)

    assert [target["id"] for target in targets] == ["scanner_never_eval", "generic_old"]
    assert [target["id"] for target in overflow_order] == ["generic_old", "scanner_never_eval"]


def test_scanner_full_eval_max_per_loop_env(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", raising=False)
    assert kiwoom_sniper_v2._scanner_full_eval_max_per_loop() == 8

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "3")
    assert kiwoom_sniper_v2._scanner_full_eval_max_per_loop() == 3

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "0")
    assert kiwoom_sniper_v2._scanner_full_eval_max_per_loop() == 1
    _reset_scanner_hot_override_cache()


def test_scanner_rising_full_eval_relief_defaults_to_aggressive_budget_and_uses_env(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_EXTRA_PER_LOOP", raising=False)
    assert kiwoom_sniper_v2._scanner_rising_full_eval_extra_per_loop() == 8

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_EXTRA_PER_LOOP", "4")
    assert kiwoom_sniper_v2._scanner_rising_full_eval_extra_per_loop() == 4


def test_scalping_fifo_max_active_env(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", raising=False)
    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 24

    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "12")
    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 12

    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "0")
    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 1
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_dynamic_watch_cap_reduces_without_restart(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "24")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE", "18")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS", "12000")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC", "0")

    effective = kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(
        19000.0,
        now_ts=1000.0,
        buy_time_allowed=True,
    )

    assert effective == 22
    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 22
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_dynamic_watch_cap_recovers_gradually(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "24")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE", "18")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS", "12000")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS", "7000")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK", "3")

    assert kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(19000.0, now_ts=1000.0, buy_time_allowed=True) == 22
    assert kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(6000.0, now_ts=1001.0, buy_time_allowed=True) == 22
    assert kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(6000.0, now_ts=1002.0, buy_time_allowed=True) == 22
    assert kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(6000.0, now_ts=1003.0, buy_time_allowed=True) == 23

    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_dynamic_watch_cap_clamps_existing_state_to_hot_min(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "16")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE", "8")
    kiwoom_sniper_v2._SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"] = 8

    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE", "10")

    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 10
    assert kiwoom_sniper_v2._SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"] == 10
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_scalping_dynamic_watch_cap_disabled_keeps_base(monkeypatch, tmp_path):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "24")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", "false")

    assert kiwoom_sniper_v2._update_scalping_dynamic_watch_cap(30000.0, now_ts=1000.0, buy_time_allowed=True) == 24
    assert kiwoom_sniper_v2._scalping_fifo_max_active() == 24
    kiwoom_sniper_v2._reset_scalping_dynamic_watch_cap_state()


def test_initial_ws_registration_groups_caps_scanner_hot_tier(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "2")
    targets = [
        {"id": "hold", "code": "000001", "status": "HOLDING", "strategy": "SCALPING", "position_tag": "SCALP_BASE"},
        {"id": "base", "code": "000002", "status": "WATCHING", "strategy": "KOSPI_ML", "position_tag": "META_V2"},
        {
            "id": "scanner_old_eval",
            "code": "100001",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1000.0,
            "_scanner_last_full_eval_epoch": 1010.0,
        },
        {
            "id": "scanner_keep_fresh",
            "code": "100002",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1020.0,
        },
        {
            "id": "scanner_keep_rising",
            "code": "100003",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "entry_armed_at_epoch": 1030.0,
            "price_delta_since_first_seen_pct": "2.5",
        },
        {"id": "expired", "code": "999999", "status": "EXPIRED", "strategy": "SCALPING", "position_tag": "SCANNER"},
    ]

    priority_codes, scanner_codes = kiwoom_sniper_v2._initial_ws_registration_groups(targets, now_ts=1100.0)

    assert priority_codes == ["000001", "000002"]
    assert scanner_codes == ["100002", "100003"]


def test_swing_watching_default_off_excludes_ws_and_runtime(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", raising=False)
    targets = [
        {"id": "swing", "code": "000002", "status": "WATCHING", "strategy": "KOSPI_ML", "position_tag": "META_V2"},
        {"id": "kosdaq", "code": "000003", "status": "WATCHING", "strategy": "KOSDAQ_ML", "position_tag": "RUNNER"},
        {"id": "hold", "code": "000001", "status": "HOLDING", "strategy": "KOSPI_ML", "position_tag": "META_V2"},
        {"id": "scanner", "code": "100001", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
    ]

    priority_codes, scanner_codes = kiwoom_sniper_v2._initial_ws_registration_groups(targets, now_ts=1100.0)
    iteration_codes = [
        target["code"]
        for target in kiwoom_sniper_v2._runtime_iteration_targets(targets, now_ts=1100.0)
    ]

    assert priority_codes == ["000001"]
    assert scanner_codes == ["100001"]
    assert iteration_codes == ["000001", "100001"]


def test_runtime_scanner_ws_snapshot_cache_uses_bulk_lookup(monkeypatch):
    calls = []

    class FakeWS:
        def get_all_data(self, codes):
            calls.append(list(codes))
            return {
                "005930": {"curr": 70000, "last_ws_update_ts": 1000.0},
                "000660": {"curr": 130000, "last_ws_update_ts": 1000.0},
            }

        def get_latest_data(self, code):
            raise AssertionError("per-symbol lookup should not be used by cache helper")

    targets = [
        {"code": "005930", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
        {"code": "005930", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
        {"code": "000660", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
        {"code": "035720", "status": "WATCHING", "strategy": "SCALPING"},
    ]

    monkeypatch.setattr(kiwoom_sniper_v2, "WS_MANAGER", FakeWS())

    snapshots = kiwoom_sniper_v2._runtime_scanner_ws_snapshot_cache(targets)

    assert calls == [["005930", "000660"]]
    assert snapshots["005930"]["curr"] == 70000
    assert snapshots["000660"]["curr"] == 130000


def test_runtime_scanner_ws_snapshot_cache_fails_closed(monkeypatch):
    class FakeWS:
        def get_all_data(self, codes):
            raise RuntimeError("ws lock unavailable")

    monkeypatch.setattr(kiwoom_sniper_v2, "WS_MANAGER", FakeWS())

    snapshots = kiwoom_sniper_v2._runtime_scanner_ws_snapshot_cache(
        [{"code": "005930", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"}]
    )

    assert snapshots == {}


def test_runtime_scanner_ws_snapshot_cache_returns_code_misses_when_lock_busy(monkeypatch):
    class FakeWS:
        def __init__(self):
            self.lock = threading.Lock()
            self.realtime_data = {"005930": {"curr": 70000}}
            self.lock.acquire()

        def _normalize_code(self, code):
            return str(code or "").strip()[:6]

        def _snapshot_target(self, target):
            return dict(target or {})

        def get_all_data(self, codes):
            raise AssertionError("busy lock should not fall through to blocking get_all_data")

    fake_ws = FakeWS()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_CACHE_LOCK_WAIT_MS", "0")
    monkeypatch.setattr(kiwoom_sniper_v2, "WS_MANAGER", fake_ws)
    try:
        snapshots = kiwoom_sniper_v2._runtime_scanner_ws_snapshot_cache(
            [
                {"code": "005930", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
                {"code": "000660", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"},
            ]
        )
    finally:
        fake_ws.lock.release()

    assert snapshots == {"005930": {}, "000660": {}}


def test_runtime_scanner_ws_snapshot_cache_waits_briefly_for_busy_lock(monkeypatch):
    class FakeWS:
        def __init__(self):
            self.lock = threading.Lock()
            self.realtime_data = {"005930": {"curr": 70000, "last_ws_update_ts": 1000.0}}
            self.lock.acquire()

        def _normalize_code(self, code):
            return str(code or "").strip()[:6]

        def _snapshot_target(self, target):
            return dict(target or {})

        def get_all_data(self, codes):
            raise AssertionError("direct snapshot path should use the existing lock acquisition")

    fake_ws = FakeWS()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_CACHE_LOCK_WAIT_MS", "50")
    monkeypatch.setattr(kiwoom_sniper_v2, "WS_MANAGER", fake_ws)

    def release_lock():
        time.sleep(0.01)
        fake_ws.lock.release()

    thread = threading.Thread(target=release_lock)
    thread.start()
    try:
        snapshots = kiwoom_sniper_v2._runtime_scanner_ws_snapshot_cache(
            [{"code": "005930", "status": "WATCHING", "strategy": "SCALPING", "position_tag": "SCANNER"}]
        )
    finally:
        thread.join(timeout=1.0)

    assert snapshots == {"005930": {"curr": 70000, "last_ws_update_ts": 1000.0}}


def test_scanner_full_eval_effective_limit_expands_for_backlog(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", raising=False)

    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 8}) == 8
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 20}) == 12
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 40}) == 12

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "0")
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 40}) == 8
    _reset_scanner_hot_override_cache()
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_scanner_full_eval_effective_limit_respects_env_caps(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "6")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "4")
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 40}) == 10

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "40")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "40")
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 100}) == 40
    _reset_scanner_hot_override_cache()
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_scanner_full_eval_pressure_reduces_loop_budget_without_restart(tmp_path, monkeypatch):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "8")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "4")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT", "6")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS", "12000")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC", "0")

    queue_context = {"scanner_watching_count": 40}
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit(queue_context) == 12

    effective = kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        19000.0,
        queue_context=queue_context,
        now_ts=1000.0,
        buy_time_allowed=True,
    )

    assert effective == 10
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit(queue_context) == 10
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_scanner_full_eval_pressure_recovers_gradually(tmp_path, monkeypatch):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "8")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "4")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT", "6")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS", "12000")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RELIEF_MS", "7000")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RECOVERY_STREAK", "3")

    queue_context = {"scanner_watching_count": 40}
    assert kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        19000.0,
        queue_context=queue_context,
        now_ts=1000.0,
        buy_time_allowed=True,
    ) == 10
    assert kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        6000.0,
        queue_context=queue_context,
        now_ts=1001.0,
        buy_time_allowed=True,
    ) == 10
    assert kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        6000.0,
        queue_context=queue_context,
        now_ts=1002.0,
        buy_time_allowed=True,
    ) == 10
    assert kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        6000.0,
        queue_context=queue_context,
        now_ts=1003.0,
        buy_time_allowed=True,
    ) == 11

    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_scanner_full_eval_pressure_disabled_keeps_base_limit(tmp_path, monkeypatch):
    _disable_scanner_operator_runtime_overrides(monkeypatch, tmp_path)
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", "8")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", "4")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED", "false")

    queue_context = {"scanner_watching_count": 40}

    assert kiwoom_sniper_v2._update_scanner_full_eval_pressure(
        30000.0,
        queue_context=queue_context,
        now_ts=1000.0,
        buy_time_allowed=True,
    ) == 12
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit(queue_context) == 12
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_scanner_full_eval_budget_defers_before_watching_handler():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    effective_limit_idx = source.index("scanner_full_eval_limit = _scanner_full_eval_effective_limit(")
    budget_check_idx = source.index("if scanner_full_eval_count >= scanner_full_eval_limit:")
    append_idx = source.index("delayed_scanner_heavy_eval.append", budget_check_idx)
    continue_idx = source.index("continue", append_idx)
    inline_handle_idx = source.index("handle_watching_state(\n                        stock,", append_idx)

    assert effective_limit_idx < budget_check_idx
    assert budget_check_idx < append_idx < continue_idx < inline_handle_idx


def test_scanner_rising_full_eval_relief_is_checked_before_budget_defer():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    budget_check_idx = source.index("if scanner_full_eval_count >= scanner_full_eval_limit:")
    relief_idx = source.index("relief_allowed = (", budget_check_idx)
    skip_idx = source.index('skip_reason="scanner_full_eval_loop_budget_deferred"', relief_idx)
    append_idx = source.index("delayed_scanner_heavy_eval.append", skip_idx)

    assert budget_check_idx < relief_idx < skip_idx < append_idx


def test_scanner_rising_strength_recheck_queues_ws_recovery_only_for_stale_snapshot_before_watch_eviction():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    handle_idx = source.index("handle_watching_state(")
    recheck_idx = source.index('entry_strength_momentum_recheck_pending"))', handle_idx)
    source_reason_idx = source.index("entry_strength_momentum_recheck_source_quality_block_reason", recheck_idx)
    stale_reason_idx = source.index('== "stale_ws_snapshot"', source_reason_idx)
    queue_idx = source.index('scanner_strength_recheck_stale_ws_recovery', stale_reason_idx)
    eviction_idx = source.index("_maybe_expire_scanner_watch_after_full_eval", queue_idx)

    assert handle_idx < recheck_idx < source_reason_idx < stale_reason_idx < queue_idx < eviction_idx


def test_scanner_rest_quote_loop_budget_is_checked_before_recovery_calls():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    limit_idx = source.index("scanner_rest_quote_fallback_loop_limit =")
    helper_idx = source.index("def _scanner_rest_quote_recovery_options", limit_idx)
    first_call_idx = source.index("_scanner_rest_quote_recovery_options(stock, now_ts)", helper_idx)
    first_recover_idx = source.index("_recover_missing_ws_snapshot(", first_call_idx)
    second_call_idx = source.index("_scanner_rest_quote_recovery_options(", first_recover_idx)
    second_recover_idx = source.index("_recover_missing_ws_snapshot(", second_call_idx)

    assert limit_idx < helper_idx < first_call_idx < first_recover_idx < second_call_idx < second_recover_idx


def test_run_sniper_builds_scanner_ws_cache_before_target_iteration():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    context_idx = source.index("queue_context = _runtime_queue_context(")
    cache_idx = source.index("scanner_ws_snapshot_cache = _runtime_scanner_ws_snapshot_cache", context_idx)
    loop_idx = source.index('for stock in queue_context["iteration_targets"]:', cache_idx)
    cached_lookup_idx = source.index("scanner_ws_snapshot_cache.get(code)", loop_idx)
    fallback_lookup_idx = source.index("WS_MANAGER.get_latest_data(code)", cached_lookup_idx)

    assert context_idx < cache_idx < loop_idx < cached_lookup_idx < fallback_lookup_idx


def test_run_sniper_batches_scanner_ws_recovery_reg_before_loop_end():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    pending_idx = source.index("pending_scanner_ws_reg")
    queue_idx = source.index("def _queue_scanner_ws_reg", pending_idx)
    missing_recovery_idx = source.index("publish_ws_reg=False", queue_idx)
    missing_queue_idx = source.index('_queue_scanner_ws_reg(code, "scanner_watching_ws_snapshot_recovery")', missing_recovery_idx)
    stale_recovery_idx = source.index("scanner_fast_precheck_stale_ws_recovery", missing_queue_idx)
    stale_no_publish_idx = source.index("publish_ws_reg=False", stale_recovery_idx)
    stale_queue_idx = source.index('_queue_scanner_ws_reg(code, "scanner_fast_precheck_stale_ws_recovery")', stale_no_publish_idx)
    final_flush_idx = source.rindex("_flush_pending_scanner_ws_reg()")
    prune_idx = source.index("targets[:] = [t for t in targets", final_flush_idx)

    assert pending_idx < queue_idx < missing_recovery_idx < missing_queue_idx
    assert missing_queue_idx < stale_no_publish_idx < stale_queue_idx
    assert stale_queue_idx < final_flush_idx < prune_idx


def test_run_sniper_defers_scanner_skip_event_emits_until_loop_tail():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    defer_def_idx = source.index("def _defer_scanner_watching_runtime_skip")
    missing_idx = source.index('_defer_scanner_watching_runtime_skip(\n                                stock', defer_def_idx)
    final_flush_idx = source.rindex("_flush_deferred_scanner_skip_events()")
    executor_submit_idx = source.index("_SCANNER_OBSERVATION_EXECUTOR.submit", defer_def_idx)
    prune_idx = source.index("targets[:] = [t for t in targets", final_flush_idx)
    direct_emit_after_defer = source.find("sniper_state_handlers.emit_scanner_watching_runtime_skip", defer_def_idx, final_flush_idx)

    assert defer_def_idx < missing_idx < final_flush_idx < prune_idx
    assert defer_def_idx < executor_submit_idx < final_flush_idx
    assert direct_emit_after_defer == source.index("sniper_state_handlers.emit_scanner_watching_runtime_skip", defer_def_idx)


def test_run_sniper_defers_scanner_precheck_and_lag_event_emits_until_loop_tail():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    defer_log_def_idx = source.index("def _defer_scanner_entry_pipeline_log")
    fast_def_idx = source.index("def _defer_emit_scanner_fast_precheck", defer_log_def_idx)
    queue_def_idx = source.index("def _defer_emit_scanner_runtime_queue_lag", fast_def_idx)
    heavy_def_idx = source.index("def _defer_emit_scanner_heavy_eval_lag", queue_def_idx)
    loop_idx = source.index('for stock in queue_context["iteration_targets"]:', heavy_def_idx)
    fast_call_idx = source.index("_defer_emit_scanner_fast_precheck(", loop_idx)
    queue_call_idx = source.index("_defer_emit_scanner_runtime_queue_lag(", fast_call_idx)
    heavy_call_idx = source.index("_defer_emit_scanner_heavy_eval_lag(", heavy_def_idx)
    final_flush_idx = source.rindex("_flush_deferred_scanner_pipeline_events()")
    skip_flush_idx = source.rindex("_flush_deferred_scanner_skip_events()")
    direct_fast_emit = source.find("sniper_state_handlers.emit_scanner_fast_precheck(", loop_idx, final_flush_idx)
    direct_queue_emit = source.find("sniper_state_handlers.emit_scanner_runtime_queue_lag(", loop_idx, final_flush_idx)
    direct_heavy_emit = source.find("sniper_state_handlers.emit_scanner_heavy_eval_lag(", loop_idx, final_flush_idx)

    assert defer_log_def_idx < fast_def_idx < queue_def_idx < heavy_def_idx < loop_idx
    assert heavy_def_idx < heavy_call_idx < final_flush_idx
    assert loop_idx < fast_call_idx < queue_call_idx < final_flush_idx < skip_flush_idx
    assert direct_fast_emit == -1
    assert direct_queue_emit == -1
    assert direct_heavy_emit == -1


def test_scanner_pipeline_events_flush_before_heavy_eval_handler():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    flush_def_idx = source.index("def _flush_delayed_scanner_heavy_eval")
    heavy_lag_idx = source.index("_defer_emit_scanner_heavy_eval_lag(", flush_def_idx)
    pipeline_flush_idx = source.index("_flush_deferred_scanner_pipeline_events()", heavy_lag_idx)
    heavy_handle_idx = source.index(
        "handle_watching_state(\n                        delayed_stock",
        pipeline_flush_idx,
    )

    assert flush_def_idx < heavy_lag_idx < pipeline_flush_idx < heavy_handle_idx


def test_scanner_heavy_eval_refreshes_ws_snapshot_before_handler():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    flush_def_idx = source.index("def _flush_delayed_scanner_heavy_eval")
    eval_ws_idx = source.index("eval_ws_data = delayed_ws_data", flush_def_idx)
    recheck_idx = source.index("_scanner_ws_subscription_recheck_snapshot_and_fields(", eval_ws_idx)
    assign_idx = source.index("eval_ws_data = recheck_snapshot", recheck_idx)
    handle_idx = source.index(
        "handle_watching_state(\n                        delayed_stock",
        assign_idx,
    )
    eval_arg_idx = source.index("eval_ws_data", handle_idx)

    assert flush_def_idx < eval_ws_idx < recheck_idx < assign_idx < handle_idx < eval_arg_idx


def test_scanner_heavy_eval_stale_recheck_repairs_before_handler():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    flush_def_idx = source.index("def _flush_delayed_scanner_heavy_eval")
    recheck_idx = source.index("_scanner_ws_subscription_recheck_snapshot_and_fields(", flush_def_idx)
    fresh_idx = source.index("_scanner_heavy_eval_recheck_fresh_sec()", recheck_idx)
    stale_idx = source.index("heavy_recheck_repair_needed = bool(", fresh_idx)
    recover_idx = source.index("scanner_heavy_eval_stale_ws_recovery", stale_idx)
    merge_idx = source.index("heavy_recheck_skip_fields = {", recover_idx)
    skip_idx = source.index('skip_reason="scanner_heavy_eval_stale_snapshot_recheck"', recover_idx)
    merged_arg_idx = source.index("**heavy_recheck_skip_fields", skip_idx)
    continue_idx = source.index("continue", skip_idx)
    handle_idx = source.index(
        "handle_watching_state(\n                        delayed_stock",
        continue_idx,
    )

    assert recheck_idx < fresh_idx < stale_idx < recover_idx < merge_idx < skip_idx
    assert skip_idx < merged_arg_idx < continue_idx < handle_idx


def test_scanner_strength_recheck_waiting_skips_before_full_eval_budget():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    waiting_idx = source.index("if _scanner_strength_recheck_waiting(stock")
    budget_idx = source.index("if scanner_full_eval_count >= scanner_full_eval_limit:", waiting_idx)
    append_idx = source.index("delayed_scanner_heavy_eval.append", budget_idx)

    assert waiting_idx < budget_idx < append_idx


def test_scanner_fast_precheck_not_eligible_skips_before_heavy_eval():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    precheck_idx = source.index("fast_precheck_result = str(stock.get")
    not_eligible_idx = source.index('fast_precheck_result != "eligible_for_heavy_entry_eval"', precheck_idx)
    fields_store_idx = source.index('stock_value["_scanner_fast_precheck_fields"] = dict(fields)')
    fields_arg_idx = source.index('fast_precheck_fields=dict(stock.get("_scanner_fast_precheck_fields") or {})', not_eligible_idx)
    ws_reg_idx = source.index("scanner_fast_precheck_stale_ws_recovery", not_eligible_idx)
    recovered_idx = source.index("scanner_fast_precheck_stale_ws_recovered", ws_reg_idx)
    recheck_idx = source.index("throttle_sec=0", recovered_idx)
    waiting_idx = source.index("if _scanner_strength_recheck_waiting(stock", not_eligible_idx)
    budget_idx = source.index("if scanner_full_eval_count >= scanner_full_eval_limit:", waiting_idx)
    append_idx = source.index("delayed_scanner_heavy_eval.append", budget_idx)

    assert precheck_idx < not_eligible_idx < waiting_idx < budget_idx < append_idx
    assert fields_store_idx < precheck_idx < fields_arg_idx < waiting_idx
    assert not_eligible_idx < ws_reg_idx < waiting_idx
    assert ws_reg_idx < recovered_idx < recheck_idx < waiting_idx


def test_scanner_fast_precheck_is_flushed_before_non_scanner_targets():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    transition_flush_idx = source.index("and not _is_scanner_watching_target(stock)")
    flush_call_idx = source.index("_flush_delayed_scanner_heavy_eval()", transition_flush_idx)
    buy_ordered_idx = source.index("if status == 'BUY_ORDERED':", flush_call_idx)
    final_flush_idx = source.rindex("_flush_delayed_scanner_heavy_eval()")
    prune_idx = source.index("targets[:] = [t for t in targets", final_flush_idx)

    assert transition_flush_idx < flush_call_idx < buy_ordered_idx
    assert final_flush_idx < prune_idx


def test_holding_missing_ws_snapshot_reaches_holding_freshness_guard():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    missing_ws_branch_idx = source.index("if not ws_data or ws_data.get('curr', 0) == 0:")
    holding_guard_idx = source.index("if status == 'HOLDING':", missing_ws_branch_idx)
    handler_call_idx = source.index("handle_holding_state(", holding_guard_idx)
    continue_idx = source.index("continue", handler_call_idx)

    assert missing_ws_branch_idx < holding_guard_idx < handler_call_idx < continue_idx


def test_recover_missing_ws_snapshot_reissues_ws_reg_before_fallback(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})
    stock = {}

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, "005930", 1000.0, {})

    assert ws_data == {}
    assert published == [("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_watching_ws_snapshot_recovery"})]
    assert fields["ws_recovery_outcome"] == "ws_reg_reissued_waiting_snapshot"


def _scanner_watch_stock(**overrides):
    stock = {
        "id": 77,
        "code": "123456",
        "name": "TEST",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1000.0,
        "scanner_promotion_id": "SCANPROM-123456-1000",
    }
    stock.update(overrides)
    return stock


def test_scanner_watch_ai_terminal_blocker_requires_two_fresh_repeats():
    stock = _scanner_watch_stock()
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_ai_score",
        "reason": "below_ai_score",
        "fresh_input_confirmed": True,
        "observed_epoch": 1100.0,
    }

    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_ai_score",
        "reason": "below_ai_score",
        "fresh_input_confirmed": True,
        "observed_epoch": 1110.0,
    }
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1110.0)

    assert first["should_evict"] is False
    assert first["eviction_attempt_count"] == 1
    assert second["should_evict"] is True
    assert second["eviction_attempt_count"] == 2
    assert second["terminal_stage"] == "blocked_ai_score"


def test_scanner_watch_strength_and_liquidity_hardgates_evict_non_rising_after_one_fresh_block(monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "",
    )
    for stage, reason in (
        ("blocked_strength_momentum", "below_window_buy_value"),
        ("blocked_liquidity", "below_min_liquidity"),
    ):
        stock = _scanner_watch_stock(price_delta_since_first_seen_pct="0.00")
        stock["_scanner_watch_last_terminal_block"] = {
            "stage": stage,
            "reason": reason,
            "fresh_input_confirmed": True,
            "observed_epoch": 1100.0,
        }

        decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)

        assert decision["should_evict"] is True
        assert decision["eviction_attempt_count"] == 1
        assert decision["eviction_reason"] == "scanner_hardgate_prefilter"
        assert decision["terminal_stage"] == stage


def test_scanner_watch_rising_strength_hardgate_defers_for_terminal_recheck(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_DELAY_SEC", "5")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "",
    )
    stock = _scanner_watch_stock(price_delta_since_first_seen_pct="1.20")
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_strength_momentum",
        "reason": "below_buy_ratio",
        "fresh_input_confirmed": True,
        "observed_epoch": 1100.0,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "terminal_hardgate_recheck_pending"
    assert decision["eviction_attempt_count"] == 1
    assert decision["scanner_full_eval_budget_source"] == "not_applicable_terminal_hardgate"
    assert stock["_scanner_rising_terminal_hardgate_recheck_after_epoch"] == 1105.0
    assert stock["_scanner_rising_recheck_reason"] == "terminal_hardgate_recheck_pending"


def test_scanner_watch_rising_strength_hardgate_evicts_after_terminal_recheck_attempt_limit(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_MAX_ATTEMPTS", "1")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "",
    )
    stock = _scanner_watch_stock(price_delta_since_first_seen_pct="1.20")
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_strength_momentum",
        "reason": "below_buy_ratio",
        "fresh_input_confirmed": True,
        "observed_epoch": 1100.0,
    }

    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_strength_momentum",
        "reason": "below_buy_ratio",
        "fresh_input_confirmed": True,
        "observed_epoch": 1106.0,
    }
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1106.0)

    assert first["should_evict"] is False
    assert second["should_evict"] is True
    assert second["eviction_attempt_count"] == 2
    assert second["eviction_reason"] == "scanner_hardgate_prefilter"


def test_scanner_watch_terminal_blocker_does_not_double_count_same_observation():
    stock = _scanner_watch_stock()
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_vpw",
        "reason": "below_vpw",
        "fresh_input_confirmed": True,
        "observed_epoch": 1100.0,
    }

    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1101.0)

    assert first["eviction_attempt_count"] == 1
    assert second["should_evict"] is False
    assert second["eviction_attempt_count"] == 1


def test_scanner_watch_fresh_terminal_resets_source_quality_eviction_counter():
    stock = _scanner_watch_stock(
        _scanner_watch_eviction_stale_first_seen_epoch=1000.0,
        _scanner_watch_eviction_stale_count=2,
    )
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_strength_momentum",
        "reason": "below_window_buy_value",
        "fresh_input_confirmed": True,
        "observed_epoch": 1100.0,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)

    assert decision["should_evict"] is False
    assert "_scanner_watch_eviction_stale_count" not in stock
    assert "_scanner_watch_eviction_stale_first_seen_epoch" not in stock


def test_scanner_watch_terminal_eviction_rejects_real_order_or_holding_rows():
    for stock in (
        _scanner_watch_stock(status="BUY_ORDERED"),
        _scanner_watch_stock(status="SELL_ORDERED"),
        _scanner_watch_stock(status="HOLDING"),
        _scanner_watch_stock(buy_qty=1),
        _scanner_watch_stock(buy_time="2026-06-22 09:10:00"),
    ):
        stock["_scanner_watch_last_terminal_block"] = {
            "stage": "blocked_vpw",
            "reason": "below_vpw",
            "fresh_input_confirmed": True,
        }
        decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(stock, now_ts=1100.0)
        assert decision["should_evict"] is False


def test_scanner_watch_stale_eviction_requires_three_attempts_and_age():
    stock = _scanner_watch_stock()
    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1000.0,
        stale_reason="ws_snapshot_missing_or_zero",
        recovery_fields={"ws_recovery_outcome": "ws_reg_reissued_waiting_snapshot"},
    )
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1050.0,
        stale_reason="ws_snapshot_missing_or_zero",
        recovery_fields={"ws_recovery_outcome": "rest_quote_unavailable"},
    )
    third = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1091.0,
        stale_reason="ws_snapshot_missing_or_zero",
        recovery_fields={"ws_recovery_outcome": "rest_quote_unavailable"},
    )

    assert first["should_evict"] is False
    assert second["should_evict"] is False
    assert third["should_evict"] is True
    assert third["eviction_attempt_count"] == 3
    assert third["stale_age_sec"] == 91.0


def test_scanner_watch_insufficient_history_eviction_requires_three_attempts_and_age():
    stock = _scanner_watch_stock()
    for observed_epoch in (1000.0, 1050.0, 1091.0):
        stock["_scanner_watch_last_terminal_block"] = {
            "stage": "blocked_strength_momentum",
            "reason": "insufficient_history",
            "fresh_input_confirmed": False,
            "observed_epoch": observed_epoch,
        }
        decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_terminal(
            stock,
            now_ts=observed_epoch,
        )
        assert decision["should_evict"] is False
        last_decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
            stock,
            now_ts=observed_epoch,
            stale_reason="insufficient_history",
            recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
        )

    assert last_decision["should_evict"] is True
    assert last_decision["eviction_reason"] == "source_quality_unresolved"
    assert last_decision["terminal_stage"] == "not_applicable_terminal_stage"
    assert last_decision["terminal_reason"] == "insufficient_history"
    assert last_decision["fresh_input_confirmed"] is False
    assert last_decision["eviction_attempt_count"] == 3
    assert last_decision["stale_age_sec"] == 91.0


def test_scanner_watch_cooldown_pool_block_requires_repeat_and_remaining_time():
    short = _scanner_watch_stock(
        _scanner_watch_last_pool_block={
            "reason": "entry_cooldown_active",
            "observed_epoch": 1000.0,
            "cooldown_remaining_sec": 59,
        }
    )
    short_decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_pool_block(
        short,
        now_ts=1000.0,
    )
    assert short_decision["should_evict"] is False
    assert short_decision["eviction_attempt_count"] == 0

    stock = _scanner_watch_stock()
    stock["_scanner_watch_last_pool_block"] = {
        "reason": "entry_cooldown_active",
        "observed_epoch": 1000.0,
        "cooldown_remaining_sec": 120,
    }
    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_pool_block(stock, now_ts=1000.0)
    stock["_scanner_watch_last_pool_block"] = {
        "reason": "entry_cooldown_active",
        "observed_epoch": 1031.0,
        "cooldown_remaining_sec": 89,
    }
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_pool_block(stock, now_ts=1031.0)

    assert first["should_evict"] is False
    assert first["eviction_attempt_count"] == 1
    assert second["should_evict"] is True
    assert second["eviction_reason"] == "safety_cooldown_pool_blocked"
    assert second["terminal_reason"] == "entry_cooldown_active"
    assert second["cooldown_remaining_sec"] == 89


def test_scanner_watch_after_full_eval_routes_cooldown_pool_block_to_eviction(monkeypatch):
    stock = _scanner_watch_stock(
        _scanner_watch_last_pool_block={
            "reason": "entry_cooldown_active",
            "observed_epoch": 1031.0,
            "cooldown_remaining_sec": 89,
        },
        _scanner_watch_eviction_pool_block_reason="entry_cooldown_active",
        _scanner_watch_eviction_pool_block_count=1,
        _scanner_watch_eviction_last_pool_block_observed_epoch=1000.0,
    )
    captured = {}

    def fake_expire(target, code, targets, *, decision, emit_event_fn=None):
        captured["decision"] = decision
        return True

    monkeypatch.setattr(kiwoom_sniper_v2, "_expire_scanner_watch_target", fake_expire)

    expired = kiwoom_sniper_v2._maybe_expire_scanner_watch_after_full_eval(
        stock,
        "123456",
        [stock],
        now_ts=1031.0,
    )

    assert expired is True
    assert captured["decision"]["eviction_reason"] == "safety_cooldown_pool_blocked"
    assert captured["decision"]["terminal_reason"] == "entry_cooldown_active"


def test_scanner_rising_cooldown_relief_blocks_watch_eviction(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_COOLDOWN_EVICTION_RELIEF_ENABLED", "true")
    stock = {
        "id": 88,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-005930-1000000",
        "price_delta_since_first_seen_pct": "0.80",
        "_scanner_watch_last_pool_block": {
            "reason": "entry_cooldown_active",
            "observed_epoch": 1000.0,
            "cooldown_remaining_sec": 120,
        },
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_pool_block(stock, now_ts=1000.0)

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "cooldown_recheck_pending"
    assert stock["_scanner_rising_cooldown_recheck_after_epoch"] == 1120.0


def test_scanner_rising_stale_ws_gap_defers_eviction_for_priority_recovery(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    stock = {
        "id": 89,
        "code": "010690",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.80",
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2000.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={"ws_recovery_outcome": "ws_reg_reissued_waiting_snapshot"},
    )

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "ws_gap_recovery_deferred_priority"
    assert decision["ws_gap_recovery_deferred_priority"] is True
    assert stock["_scanner_rising_ws_gap_priority_recheck_after_epoch"] == 2005.0


def test_scanner_rising_stale_ws_gap_priority_expires_after_standard_stale_guard(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    stock = {
        "id": 90,
        "code": "010690",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.80",
        "_scanner_watch_eviction_stale_first_seen_epoch": 2000.0,
        "_scanner_watch_eviction_stale_count": 2,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2091.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={"ws_recovery_outcome": "ws_reg_reissued_waiting_snapshot"},
    )

    assert decision["should_evict"] is True
    assert decision["eviction_reason"] == "stale_recovery_failed"
    assert decision["eviction_attempt_count"] == 3
    assert decision["stale_age_sec"] == 91.0


def test_scanner_rising_insufficient_history_evicts_after_buy_window(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "scalping_new_buy_cutoff",
    )
    stock = {
        "id": 90,
        "code": "095500",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "7.12",
    }

    first = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2000.0,
        stale_reason="insufficient_history",
        recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
    )
    second = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2061.0,
        stale_reason="insufficient_history",
        recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
    )

    assert first["should_evict"] is False
    assert first["eviction_reason"] == "ws_gap_recovery_deferred_priority"
    assert second["should_evict"] is True
    assert second["eviction_reason"] == "source_quality_unresolved_after_buy_window"
    assert second["terminal_reason"] == "insufficient_history"
    assert second["eviction_attempt_count"] == 2
    assert second["stale_age_sec"] == 61.0
    assert second["after_buy_window_source_quality_expired"] is True


def test_scanner_rising_insufficient_history_keeps_priority_recheck_before_cutoff(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "outside_scalping_buy_window",
    )
    stock = {
        "id": 91,
        "code": "372320",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "3.82",
        "_scanner_watch_eviction_stale_first_seen_epoch": 2000.0,
        "_scanner_watch_eviction_stale_count": 1,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2061.0,
        stale_reason="insufficient_history",
        recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
    )

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "ws_gap_recovery_deferred_priority"
    assert decision["ws_gap_recovery_deferred_priority"] is True
    assert stock["_scanner_watch_eviction_stale_count"] == 2


def test_scanner_rising_insufficient_history_keeps_priority_recheck_after_standard_stale_guard_before_cutoff(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "",
    )
    stock = {
        "id": 93,
        "code": "037710",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "11.15",
        "_scanner_watch_eviction_stale_first_seen_epoch": 2000.0,
        "_scanner_watch_eviction_stale_count": 2,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2091.0,
        stale_reason="insufficient_history",
        recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
    )

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "ws_gap_recovery_deferred_priority"
    assert decision["ws_gap_recovery_deferred_priority"] is True
    assert stock["_scanner_watch_eviction_stale_count"] == 3


def test_scanner_rising_insufficient_history_evicts_after_operator_start_time(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_START_TIME", "00:00:00")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "scalping_buy_time_block_reason",
        lambda _now_t: "outside_scalping_buy_window",
    )
    stock = {
        "id": 92,
        "code": "095500",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "7.12",
        "_scanner_watch_eviction_stale_first_seen_epoch": 2000.0,
        "_scanner_watch_eviction_stale_count": 1,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=2061.0,
        stale_reason="insufficient_history",
        recovery_fields={"ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"},
    )

    assert decision["should_evict"] is True
    assert decision["eviction_reason"] == "source_quality_unresolved_after_buy_window"
    assert decision["after_buy_window_source_quality_expired"] is True


def test_scanner_watch_after_full_eval_routes_nonfresh_insufficient_history_to_source_quality_eviction(monkeypatch):
    stock = _scanner_watch_stock()
    stock["_scanner_watch_last_terminal_block"] = {
        "stage": "blocked_strength_momentum",
        "reason": "insufficient_history",
        "fresh_input_confirmed": False,
        "observed_epoch": 1091.0,
    }
    stock["_scanner_watch_eviction_stale_first_seen_epoch"] = 1000.0
    stock["_scanner_watch_eviction_stale_count"] = 2
    captured = {}

    def fake_expire(target, code, targets, *, decision, emit_event_fn=None):
        captured["decision"] = decision
        return True

    monkeypatch.setattr(kiwoom_sniper_v2, "_expire_scanner_watch_target", fake_expire)

    expired = kiwoom_sniper_v2._maybe_expire_scanner_watch_after_full_eval(
        stock,
        "123456",
        [stock],
        now_ts=1091.0,
    )

    assert expired is True
    assert captured["decision"]["eviction_reason"] == "source_quality_unresolved"
    assert captured["decision"]["terminal_reason"] == "insufficient_history"


def test_scanner_watch_stale_recovery_resets_eviction_counter():
    stock = _scanner_watch_stock()
    kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1000.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={"ws_recovery_outcome": "ws_reg_reissued_waiting_snapshot"},
    )

    recovered = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1010.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={"ws_recovery_outcome": "rest_quote_applied"},
    )

    assert recovered["should_evict"] is False
    assert "_scanner_watch_eviction_stale_count" not in stock
    assert "_scanner_watch_eviction_stale_first_seen_epoch" not in stock


def test_scanner_watch_budget_deferred_is_not_eviction_reason():
    stock = _scanner_watch_stock()
    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        stock,
        now_ts=1000.0,
        stale_reason="scanner_full_eval_loop_budget_deferred",
        recovery_fields={"ws_recovery_outcome": "not_applicable_ws_recovery_outcome"},
    )

    assert decision["should_evict"] is False
    assert decision["eviction_attempt_count"] == 0


def test_expire_scanner_watch_target_updates_db_and_memory_by_record_id(monkeypatch):
    class FakeQuery:
        def __init__(self):
            self.updated = False

        def filter(self, *conditions):
            self.conditions = conditions
            return self

        def update(self, values, synchronize_session=False):
            self.updated = values == {"status": "EXPIRED"} and synchronize_session is False
            return 1

    class FakeSession:
        def __init__(self):
            self.query_obj = FakeQuery()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query(self, model):
            self.model = model
            return self.query_obj

    class FakeDB:
        def __init__(self):
            self.session = FakeSession()

        def get_session(self):
            return self.session

    fake_db = FakeDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    stock = _scanner_watch_stock()
    emitted = []
    decision = {
        "eviction_reason": "terminal_blocker_repeated",
        "eviction_attempt_count": 2,
        "terminal_stage": "blocked_vpw",
        "terminal_reason": "below_vpw",
        "fresh_input_confirmed": True,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "observed_epoch": "1100.000",
    }

    expired = kiwoom_sniper_v2._expire_scanner_watch_target(
        stock,
        "123456",
        [stock],
        decision=decision,
        emit_event_fn=lambda *args: emitted.append(args),
    )

    assert expired is True
    assert fake_db.session.query_obj.updated is True
    assert stock["status"] == "EXPIRED"
    assert emitted[-1][2] == "scalping_scanner_watch_eviction"
    assert emitted[-1][3]["target_status"] == "WATCHING"
    assert emitted[-1][3]["actual_order_submitted"] is False
    assert emitted[-1][3]["broker_order_forbidden"] is True


def test_expire_scanner_watch_target_rejects_bought_rows_before_db(monkeypatch):
    class FailingDB:
        def get_session(self):
            raise AssertionError("DB should not be touched for bought rows")

    monkeypatch.setattr(kiwoom_sniper_v2, "DB", FailingDB())
    stock = _scanner_watch_stock(buy_qty=1)
    expired = kiwoom_sniper_v2._expire_scanner_watch_target(
        stock,
        "123456",
        [stock],
        decision={"eviction_reason": "terminal_blocker_repeated"},
    )

    assert expired is False
    assert stock["status"] == "WATCHING"


def test_krx_open_watchlist_reset_expires_only_unbought_watching_rows(monkeypatch):
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    emitted = []
    pre_open_epoch = kiwoom_sniper_v2.datetime(2026, 6, 24, 8, 50, 0).timestamp()
    targets = [
        _scanner_watch_stock(id=101, code="111111", name="PREOPEN1"),
        _scanner_watch_stock(id=102, code="222222", name="HELD", status="HOLDING", buy_qty=1),
        _scanner_watch_stock(id=103, code="333333", name="ORDERED", status="BUY_ORDERED"),
        _scanner_watch_stock(id=104, code="444444", name="BOUGHT_WATCH", buy_qty=1),
        _scanner_watch_stock(
            id=105,
            code="555555",
            name="SWING",
            strategy="KOSDAQ_ML",
            position_tag="SWING",
            added_time=pre_open_epoch,
        ),
    ]

    reset_codes = kiwoom_sniper_v2._reset_krx_open_watch_targets(
        targets,
        now_dt=kiwoom_sniper_v2.datetime(2026, 6, 24, 9, 0, 1),
        emit_event_fn=lambda *args: emitted.append(args),
    )

    assert reset_codes == ["111111", "555555"]
    assert targets[0]["status"] == "EXPIRED"
    assert targets[1]["status"] == "HOLDING"
    assert targets[2]["status"] == "BUY_ORDERED"
    assert targets[3]["status"] == "WATCHING"
    assert targets[4]["status"] == "EXPIRED"
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]
    assert [event[2] for event in emitted] == ["krx_open_watchlist_reset", "krx_open_watchlist_reset"]
    assert emitted[0][3]["reset_reason"] == "krx_open_reprice_watchlist_reset"
    assert emitted[0][3]["actual_order_submitted"] is False
    assert emitted[0][3]["broker_order_forbidden"] is True


def test_krx_open_watchlist_reset_waits_until_market_open(monkeypatch):
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    stock = _scanner_watch_stock(id=106, code="666666")

    reset_codes = kiwoom_sniper_v2._reset_krx_open_watch_targets(
        [stock],
        now_dt=kiwoom_sniper_v2.datetime(2026, 6, 24, 8, 59, 59),
    )

    assert reset_codes == []
    assert stock["status"] == "WATCHING"
    assert fake_db.calls == []


def test_krx_open_watchlist_reset_keeps_post_open_scanner_targets(monkeypatch):
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    now_dt = kiwoom_sniper_v2.datetime(2026, 6, 24, 9, 3, 0)
    post_open_epoch = kiwoom_sniper_v2.datetime(2026, 6, 24, 9, 1, 0).timestamp()
    stock = _scanner_watch_stock(
        id=107,
        code="777777",
        added_time=post_open_epoch,
        entry_armed_at_epoch=post_open_epoch,
        scanner_promotion_emitted_epoch=str(post_open_epoch),
    )

    reset_codes = kiwoom_sniper_v2._reset_krx_open_watch_targets([stock], now_dt=now_dt)

    assert reset_codes == []
    assert stock["status"] == "WATCHING"
    assert fake_db.calls == []


def test_recover_missing_ws_snapshot_skips_rest_quote_for_non_rising_repeated_miss(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    published = []
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000, "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback"},
    )
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.00",
        "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
    }

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, "005930", 1000.0, {})

    assert ws_data == {}
    assert fields["ws_recovery_action"] == "ws_reg_reissued"
    assert fields["ws_recovery_outcome"] == "ws_reg_reissued_waiting_snapshot"
    assert fields["rest_quote_fallback_eligible"] is False
    assert calls == []
    assert len(published) == 1


def test_recover_missing_ws_snapshot_applies_rest_quote_on_first_positive_scanner_miss(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000, "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback"},
    )
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-005930-1000000",
        "price_delta_since_first_seen_pct": "0.60",
    }

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        stock,
        "005930",
        1000.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_ws_gap_early_rest_fallback_allowed(stock),
    )

    assert ws_data["curr"] == 70000
    assert fields["ws_recovery_action"] == "ws_reg_reissued_rest_quote_fallback"
    assert fields["ws_recovery_outcome"] == "rest_quote_applied"
    assert fields["rest_quote_fallback_eligible"] is True
    assert stock["_scanner_ws_snapshot_recovery"]["miss_count"] == 1
    assert calls == [("005930", 1000.0)]


def test_recover_missing_ws_snapshot_defers_rest_quote_when_loop_budget_exhausted(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000},
    )
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.70",
        "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
    }

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        stock,
        "005930",
        1000.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_rest_quote_fallback_allowed_for_ws_gap(stock),
        rest_quote_deferred_reason="rest_quote_loop_budget_deferred",
    )

    assert ws_data == {}
    assert fields["ws_recovery_action"] == "ws_reg_reissued_rest_quote_fallback"
    assert fields["ws_recovery_outcome"] == "rest_quote_loop_budget_deferred"
    assert fields["ws_gap_recovery_deferred_priority"] is True
    assert fields["rest_quote_fallback_deferred_reason"] == "rest_quote_loop_budget_deferred"
    assert stock["_scanner_ws_snapshot_recovery"]["last_fallback_outcome"] == "rest_quote_loop_budget_deferred"
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_due(
        stock,
        1004.0,
        allow_early_rest_fallback=True,
    ) is False
    assert calls == []
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_recover_missing_ws_snapshot_rate_limits_rest_quote_burst(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000},
    )

    for idx, code in enumerate(
        (
            "005930",
            "000660",
            "035420",
            "051910",
            "068270",
            "247540",
            "373220",
            "005380",
            "012330",
        ),
        start=1,
    ):
        stock = {
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "price_delta_since_first_seen_pct": "0.70",
            "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
        }
        ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
            stock,
            code,
            1000.0 + idx,
            {},
            allow_early_rest_fallback=kiwoom_sniper_v2._scanner_rest_quote_fallback_allowed_for_ws_gap(stock),
        )
        if idx <= 8:
            assert ws_data["curr"] == 70000
            assert fields["ws_recovery_outcome"] == "rest_quote_applied"
            assert fields["rest_quote_rate_limit_decision"] in {
                "rest_quote_allowed",
                "rest_quote_allowed_dynamic_boost",
            }
            assert fields["rest_quote_dynamic_budget_boosted"] == (idx >= 7)
        else:
            assert ws_data == {}
            assert fields["ws_recovery_outcome"] == "rest_quote_rate_limited"

    assert calls == [
        ("005930", 1001.0),
        ("000660", 1002.0),
        ("035420", 1003.0),
        ("051910", 1004.0),
        ("068270", 1005.0),
        ("247540", 1006.0),
        ("373220", 1007.0),
        ("005380", 1008.0),
    ]
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_scanner_rest_quote_rate_limit_uses_bounded_operator_override(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW", "4")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS", "0")

    outcomes = [
        kiwoom_sniper_v2._scanner_rest_quote_fallback_rate_limit(1000.0 + idx, priority=True)
        for idx in range(7)
    ]

    assert outcomes[:6] == [(True, "rest_quote_allowed")] * 6
    assert outcomes[6] == (False, "rest_quote_rate_limited")
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_scanner_rest_quote_rate_limit_dynamic_boosts_on_pressure(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW", "4")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS", "2")

    outcomes = [
        kiwoom_sniper_v2._scanner_rest_quote_fallback_rate_limit(1000.0 + idx, priority=True)
        for idx in range(9)
    ]

    assert outcomes[:6] == [(True, "rest_quote_allowed")] * 6
    assert outcomes[6:8] == [(True, "rest_quote_allowed_dynamic_boost")] * 2
    assert outcomes[8] == (False, "rest_quote_rate_limited")
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_scanner_rest_quote_loop_limit_allows_bounded_intraday_recovery_override(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", raising=False)
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 6

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", "8")
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 8

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", "99")
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 24


def test_scanner_rest_quote_budget_caps_cover_intraday_observation_override(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", "24")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW", "12")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS", "6")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS", "8")

    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 24
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_calls_per_window() == 12
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_positive_reserve_calls() == 6
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_dynamic_max_extra_calls() == 8

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", "99")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW", "99")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS", "99")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS", "99")

    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 24
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_calls_per_window() == 12
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_positive_reserve_calls() == 6
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_dynamic_max_extra_calls() == 8


def test_scanner_rest_quote_budget_hot_reloads_operator_override_file(tmp_path, monkeypatch):
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()
    override_path = tmp_path / "operator_runtime_overrides.env"
    monkeypatch.setattr(kiwoom_sniper_v2, "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH", override_path)
    monkeypatch.setattr(kiwoom_sniper_v2, "_SCANNER_HOT_RUNTIME_OVERRIDE_REFRESH_SEC", 0.0)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_SUBSCRIPTION_RECHECK_FRESH_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK", raising=False)
    _reset_scanner_hot_override_cache()

    override_path.write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP=7",
                "export KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS=3",
                "export KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC=4",
                "export KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC=9",
                "export KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC=21",
                "export KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC=11",
                "export KORSTOCKSCAN_SCANNER_WS_SUBSCRIPTION_RECHECK_FRESH_SEC=12",
                "export KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC=6",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=18",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=10",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED=false",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=9",
                "export KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=28",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED=true",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=14",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS=10000",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS=5000",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=20",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK=4",
                "export KORSTOCKSCAN_BUY_SCORE_THRESHOLD=1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(override_path, ns=(1_000_000_000, 1_000_000_000))

    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 7
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_dynamic_max_extra_calls() == 3
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_defer_sec() == 4.0
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_wait_sec() == 9.0
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_persistent_sec() == 21.0
    assert kiwoom_sniper_v2._scanner_ws_persistent_repair_min_interval_sec() == 11.0
    assert kiwoom_sniper_v2._scanner_ws_subscription_recheck_fresh_sec() == 12.0
    assert kiwoom_sniper_v2._scanner_heavy_eval_recheck_fresh_sec() == 6.0
    assert kiwoom_sniper_v2._scanner_full_eval_max_per_loop() == 18
    assert kiwoom_sniper_v2._scanner_full_eval_backlog_extra_per_loop() == 10
    assert kiwoom_sniper_v2._scanner_full_eval_auto_pressure_enabled() is False
    assert kiwoom_sniper_v2._scanner_full_eval_auto_pressure_min_limit(28) == 9
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 40}) == 28
    assert kiwoom_sniper_v2._scalping_fifo_base_max_active() == 28
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_enabled() is True
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_min(28) == 14
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_pressure_ms() == 10000.0
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_relief_ms() == 5000.0
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_cooldown_sec() == 20.0
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_recovery_streak() == 4
    assert (
        kiwoom_sniper_v2._scanner_hot_runtime_override_value("KORSTOCKSCAN_BUY_SCORE_THRESHOLD")
        is None
    )

    override_path.write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP=4",
                "export KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS=1",
                "export KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC=6",
                "export KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC=2",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP=9",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP=3",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED=true",
                "export KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT=5",
                "export KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=20",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE=12",
                "export KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC=5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(override_path, ns=(2_000_000_000, 2_000_000_000))

    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_max_per_loop() == 4
    assert kiwoom_sniper_v2._scanner_rest_quote_fallback_dynamic_max_extra_calls() == 1
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_wait_sec() == 6.0
    assert kiwoom_sniper_v2._scanner_heavy_eval_recheck_fresh_sec() == 2.0
    assert kiwoom_sniper_v2._scanner_full_eval_max_per_loop() == 9
    assert kiwoom_sniper_v2._scanner_full_eval_backlog_extra_per_loop() == 3
    assert kiwoom_sniper_v2._scanner_full_eval_auto_pressure_enabled() is True
    assert kiwoom_sniper_v2._scanner_full_eval_auto_pressure_min_limit(12) == 5
    assert kiwoom_sniper_v2._scanner_full_eval_effective_limit({"scanner_watching_count": 40}) == 12
    assert kiwoom_sniper_v2._scalping_fifo_base_max_active() == 20
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_min(20) == 12
    assert kiwoom_sniper_v2._scalping_dynamic_watch_cap_cooldown_sec() == 5.0
    _reset_scanner_hot_override_cache()
    kiwoom_sniper_v2._reset_scanner_full_eval_pressure_state()


def test_non_rising_ws_misses_do_not_consume_positive_rest_quote_slot(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000},
    )

    for idx, code in enumerate(("005930", "000660"), start=1):
        stock = {
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "price_delta_since_first_seen_pct": "0.00",
            "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
        }
        ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, code, 1000.0 + idx, {})
        assert ws_data == {}
        assert fields["ws_recovery_outcome"] == "ws_reg_reissued_waiting_snapshot"

    positive_stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.72",
    }
    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        positive_stock,
        "035420",
        1003.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_ws_gap_early_rest_fallback_allowed(positive_stock),
    )

    assert ws_data["curr"] == 70000
    assert fields["ws_recovery_outcome"] == "rest_quote_applied"
    assert calls == [("035420", 1003.0)]
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_expired_scanner_ws_miss_does_not_consume_rest_quote_slot(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_fetch_rest_quote_snapshot_for_ws_gap",
        lambda code, now_ts: calls.append((code, now_ts)) or {"curr": 70000},
    )
    stock = {
        "status": "EXPIRED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "1.20",
        "_scanner_ws_snapshot_recovery": {"miss_count": 9, "last_fallback_ts": 900.0},
    }

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        stock,
        "005930",
        1000.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_rest_quote_fallback_allowed_for_ws_gap(stock),
    )

    assert ws_data == {}
    assert fields["rest_quote_fallback_eligible"] is False
    assert fields["ws_recovery_outcome"] == "ws_reg_reissued_waiting_snapshot"
    assert fields["ws_subscription_repair_required"] is True
    assert calls == []
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_recover_missing_ws_snapshot_sets_cooldown_after_rest_quote_failure(monkeypatch):
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(kiwoom_sniper_v2.kiwoom_utils, "get_api_url", lambda path: "https://example.invalid")

    def fail_fetch(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("429")

    monkeypatch.setattr(kiwoom_sniper_v2.kiwoom_utils, "fetch_kiwoom_api_continuous", fail_fetch)

    stock1 = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.70",
        "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
    }
    ws_data1, fields1 = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        stock1,
        "005930",
        1000.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_rest_quote_fallback_allowed_for_ws_gap(stock1),
    )
    stock2 = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "price_delta_since_first_seen_pct": "0.70",
        "_scanner_ws_snapshot_recovery": {"miss_count": 1, "last_fallback_ts": 900.0},
    }
    ws_data2, fields2 = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        stock2,
        "000660",
        1001.0,
        {},
        allow_early_rest_fallback=kiwoom_sniper_v2._scanner_rest_quote_fallback_allowed_for_ws_gap(stock2),
    )

    assert ws_data1 == {}
    assert fields1["ws_recovery_outcome"] == "rest_quote_unavailable"
    assert ws_data2 == {}
    assert fields2["ws_recovery_outcome"] == "rest_quote_rate_limited_cooldown"
    assert len(calls) == 1
    kiwoom_sniper_v2._reset_scanner_rest_quote_fallback_rate_limit_for_tests()


def test_scanner_ws_gap_early_rest_fallback_rejects_observed_price_without_positive_delta():
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-005930-1000000",
        "buy_price": 70000,
        "price_delta_since_first_seen_pct": "0.60",
    }

    assert kiwoom_sniper_v2._scanner_ws_gap_early_rest_fallback_allowed(stock) is False


def test_scanner_ws_gap_early_rest_fallback_rejects_observed_price_without_positive_delta_when_enabled(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-005930-1000000",
        "buy_price": 70000,
        "price_delta_since_first_seen_pct": "0.00",
    }

    assert kiwoom_sniper_v2._scanner_ws_gap_early_rest_fallback_allowed(stock) is False


def test_scanner_ws_gap_early_rest_fallback_hydrates_restored_scanner_context(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", "true")

    def fake_hydrate(stock):
        stock["price_delta_since_first_seen_pct"] = "1.11"
        return stock

    monkeypatch.setattr(
        kiwoom_sniper_v2.sniper_state_handlers,
        "_hydrate_scanner_promotion_runtime_context",
        fake_hydrate,
    )
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "SCANPROM-089790-1782104558056",
        "entry_armed_at_epoch": 1782104558.056512,
    }

    assert kiwoom_sniper_v2._scanner_ws_gap_early_rest_fallback_allowed(stock) is True
    assert stock["price_delta_since_first_seen_pct"] == "1.11"


def test_recover_missing_ws_snapshot_uses_custom_ws_reg_source(monkeypatch):
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})

    kiwoom_sniper_v2._recover_missing_ws_snapshot(
        {},
        "005930",
        1000.0,
        {"curr": 70000},
        ws_reg_source="scanner_fast_precheck_stale_ws_recovery",
    )

    assert published == [
        (
            "COMMAND_WS_REG",
            {"codes": ["005930"], "source": "scanner_fast_precheck_stale_ws_recovery"},
        )
    ]


def test_recover_missing_ws_snapshot_can_defer_ws_reg_publish(monkeypatch):
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})

    ws_data, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        {},
        "005930",
        1000.0,
        {},
        publish_ws_reg=False,
    )

    assert ws_data == {}
    assert published == []
    assert fields["ws_recovery_action"] == "ws_reg_reissued"
    assert fields["ws_recovery_outcome"] == "ws_reg_reissued_waiting_snapshot"


def test_recover_missing_ws_snapshot_keeps_repair_cycle_from_repeating_reg(monkeypatch):
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})
    stock = {}

    _, first_fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, "005930", 1000.0, {})
    _, second_fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, "005930", 1005.0, {})

    assert len(published) == 1
    assert first_fields["ws_repair_cycle_reg_allowed"] is True
    assert second_fields["ws_repair_cycle_reg_allowed"] is False
    assert second_fields["ws_repair_cycle_suppressed_duplicate_reg"] is True
    assert second_fields["ws_recovery_outcome"] == "ws_repair_cycle_waiting_snapshot"


def test_recover_missing_ws_snapshot_marks_persistent_ws_gap_after_cycle_timeout(monkeypatch):
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})
    stock = {
        "_scanner_ws_snapshot_recovery": {
            "repair_cycle_id": "005930:1000000",
            "repair_cycle_started_ts": 1000.0,
            "last_ws_reg_ts": 1000.0,
            "miss_count": 4,
        }
    }

    _, fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(stock, "005930", 1065.0, {})

    assert fields["ws_recovery_outcome"] == "persistent_ws_gap"
    assert fields["ws_subscription_repair_required"] is True
    assert fields["ws_repair_cycle_reg_allowed"] is False
    assert fields["ws_repair_batch_required"] is True
    assert len(published) == 0


def test_recover_missing_ws_snapshot_cycle_store_survives_target_object_refresh(monkeypatch):
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_fetch_rest_quote_snapshot_for_ws_gap", lambda *args, **kwargs: {})
    cycle_store = {}

    _, first_fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        {},
        "005930",
        1000.0,
        {},
        cycle_state_store=cycle_store,
    )
    _, second_fields = kiwoom_sniper_v2._recover_missing_ws_snapshot(
        {},
        "005930",
        1065.0,
        {},
        cycle_state_store=cycle_store,
    )

    assert first_fields["ws_repair_cycle_state"] == "ws_reg_reissued_waiting_snapshot"
    assert second_fields["ws_repair_cycle_state"] == "persistent_ws_gap"
    assert second_fields["ws_repair_batch_required"] is True
    assert len(published) == 1


def test_scanner_ws_subscription_recheck_closes_when_subscribed_snapshot_fresh():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {"curr": 70000, "last_ws_update_ts": 1000.0, "received_types": ["0B"]},
    )

    fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_fields(
        manager,
        "005930",
        {},
        now_ts=1001.0,
    )

    assert fields["ws_subscription_recheck_status"] == "subscribed_fresh_snapshot"
    assert fields["ws_subscription_repair_needed"] is False
    assert fields["ws_subscription_recheck_received_types"] == "0B"
    assert fields["ws_subscription_recheck_entry_realtime_fresh"] is True
    assert fields["ws_subscription_recheck_entry_realtime_source"] == "last_ws_update_ts_with_0B"


def test_scanner_ws_subscription_recheck_prefers_fresher_manager_snapshot():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {"curr": 71000, "last_ws_update_ts": 1029.0, "received_types": ["0B", "0D"]},
    )

    snapshot, fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        "005930",
        {"curr": 70000, "last_ws_update_ts": 1000.0, "received_types": ["0B"]},
        now_ts=1030.0,
    )

    assert snapshot["curr"] == 71000
    assert fields["ws_subscription_recheck_status"] == "subscribed_fresh_snapshot"
    assert fields["ws_subscription_repair_needed"] is False
    assert fields["ws_subscription_recheck_age_sec"] == 1.0
    assert fields["ws_subscription_recheck_received_types"] == "0B,0D"


def test_scanner_ws_subscription_recheck_normalizes_entry_price_timestamp():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {
            "curr": 71000,
            "last_ws_update_ts": 1020.0,
            "last_realtime_type_ts": {"0B": 1028.5, "0D": 1029.0},
            "strength_momentum_history": [{"ts": 1028.5, "price": 71000}],
            "received_types": ["0B", "0D"],
        },
    )

    snapshot, fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        "005930",
        {"curr": 70000, "last_ws_update_ts": 1000.0, "received_types": ["0B"]},
        now_ts=1030.0,
    )

    assert snapshot["last_ws_update_ts"] == 1028.5
    assert snapshot["entry_eval_last_ws_update_ts_normalized_from"] in {
        "last_realtime_type_ts_0B",
        "strength_momentum_history",
    }
    assert fields["ws_subscription_recheck_status"] == "subscribed_fresh_snapshot"
    assert fields["ws_subscription_recheck_age_sec"] == 1.5
    assert fields["ws_subscription_recheck_entry_timestamp_normalized"] is True
    assert fields["ws_subscription_recheck_entry_normalized_age_sec"] == 1.5


def test_scanner_ws_subscription_recheck_selects_manager_snapshot_by_normalized_entry_timestamp():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {
            "curr": 71000,
            "last_ws_update_ts": 1020.0,
            "last_realtime_type_ts": {"0B": 1029.0},
            "received_types": ["0B"],
        },
    )

    snapshot, fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        "005930",
        {"curr": 70000, "last_ws_update_ts": 1025.0, "received_types": ["0B"]},
        now_ts=1030.0,
    )

    assert snapshot["curr"] == 71000
    assert snapshot["last_ws_update_ts"] == 1029.0
    assert fields["ws_subscription_recheck_age_sec"] == 1.0
    assert fields["ws_subscription_recheck_entry_timestamp_source"] == "last_realtime_type_ts_0B"


def test_scanner_ws_subscription_recheck_does_not_normalize_from_non_price_type_only():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {
            "curr": 71000,
            "last_ws_update_ts": 1020.0,
            "last_realtime_type_ts": {"0D": 1029.0, "0w": 1029.5},
            "received_types": ["0D", "0w"],
        },
    )

    snapshot, fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        "005930",
        {},
        now_ts=1030.0,
    )

    assert snapshot["last_ws_update_ts"] == 1020.0
    assert "entry_eval_last_ws_update_ts_normalized_from" not in snapshot
    assert fields["ws_subscription_recheck_status"] == "subscribed_snapshot_stale_or_missing"
    assert fields["ws_subscription_repair_needed"] is True
    assert fields["ws_subscription_recheck_entry_realtime_fresh"] is False
    assert fields["ws_subscription_recheck_entry_realtime_source"] == "missing_fresh_0B_or_strength_history"
    assert fields["ws_subscription_recheck_entry_timestamp_normalized"] is False
    assert fields["ws_subscription_recheck_entry_timestamp_source"] == "last_ws_update_ts"
    assert fields["ws_subscription_recheck_age_sec"] == 10.0


def test_scanner_ws_subscription_recheck_requires_fresh_entry_realtime_source():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {
            "curr": 71000,
            "last_ws_update_ts": 1029.0,
            "last_realtime_type_ts": {"0B": 900.0, "0D": 1029.0, "0w": 1029.0},
            "strength_momentum_history": [{"ts": 900.0, "price": 71000}],
            "received_types": ["0B", "0D", "0w"],
        },
    )

    snapshot, fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        "005930",
        {},
        now_ts=1030.0,
    )

    assert snapshot["curr"] == 71000
    assert fields["ws_subscription_recheck_age_sec"] == 1.0
    assert fields["ws_subscription_recheck_status"] == "subscribed_snapshot_stale_or_missing"
    assert fields["ws_subscription_repair_needed"] is True
    assert fields["ws_subscription_recheck_entry_realtime_fresh"] is False
    assert fields["ws_subscription_recheck_entry_realtime_source"] == "last_realtime_type_ts_0B"


def test_scanner_ws_subscription_recheck_requires_repair_when_subscribed_but_zero_curr():
    manager = SimpleNamespace(subscribed_codes={"005930"})

    fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_fields(
        manager,
        "005930",
        {"curr": 0, "last_ws_update_ts": 1000.0, "received_types": ["0D"]},
        now_ts=1001.0,
    )

    assert fields["ws_subscription_recheck_status"] == "subscribed_snapshot_stale_or_missing"
    assert fields["ws_subscription_repair_needed"] is True
    assert fields["ws_subscription_recheck_received_types"] == "0D"


def test_scanner_rest_quote_applied_keeps_entry_realtime_stale_outcome():
    fields = kiwoom_sniper_v2._scanner_rest_quote_entry_realtime_outcome_fields(
        {
            "ws_recovery_outcome": "rest_quote_applied",
            "ws_subscription_repair_needed": True,
            "ws_subscription_recheck_status": "subscribed_snapshot_stale_or_missing",
        }
    )

    assert fields["ws_recovery_outcome"] == "rest_quote_applied_entry_realtime_still_stale"
    assert fields["rest_quote_price_recovery_only"] is True
    assert fields["entry_evaluable_fresh_after_rest_quote"] is False


def test_scanner_rest_quote_applied_preserves_fresh_entry_realtime_outcome():
    fields = kiwoom_sniper_v2._scanner_rest_quote_entry_realtime_outcome_fields(
        {
            "ws_recovery_outcome": "rest_quote_applied",
            "ws_subscription_repair_needed": False,
            "ws_subscription_recheck_status": "subscribed_fresh_snapshot",
        }
    )

    assert fields["ws_recovery_outcome"] == "rest_quote_applied"
    assert "rest_quote_price_recovery_only" not in fields


def test_scanner_ws_subscription_recheck_requires_repair_without_timestamp():
    manager = SimpleNamespace(
        subscribed_codes={"005930"},
        get_latest_data=lambda code: {"curr": 70000},
    )

    fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_fields(
        manager,
        "005930",
        {},
        now_ts=1001.0,
    )

    assert fields["ws_subscription_recheck_status"] == "subscribed_snapshot_stale_or_missing"
    assert fields["ws_subscription_repair_needed"] is True
    assert fields["ws_subscription_recheck_age_sec"] == "not_available_ws_age_sec"
    assert fields["ws_subscription_recheck_received_types"] == "-"


def test_scanner_ws_subscription_recheck_requires_repair_when_snapshot_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_SUBSCRIPTION_RECHECK_FRESH_SEC", raising=False)
    manager = SimpleNamespace(subscribed_codes={"005930"})

    fields = kiwoom_sniper_v2._scanner_ws_subscription_recheck_fields(
        manager,
        "005930",
        {"curr": 70000, "last_ws_update_ts": 1000.0, "received_types": ["0B", "0D"]},
        now_ts=1031.0,
    )

    assert fields["ws_subscription_recheck_status"] == "subscribed_snapshot_stale_or_missing"
    assert fields["ws_subscription_repair_needed"] is True
    assert fields["ws_subscription_recheck_fresh_sec"] == 30.0
    assert fields["ws_subscription_recheck_received_types"] == "0B,0D"


def test_scanner_ws_persistent_repair_min_interval_allows_aggressive_source_refresh(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC", raising=False)
    assert kiwoom_sniper_v2._scanner_ws_persistent_repair_min_interval_sec() == 20.0

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC", "8")
    assert kiwoom_sniper_v2._scanner_ws_persistent_repair_min_interval_sec() == 8.0

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC", "1")
    assert kiwoom_sniper_v2._scanner_ws_persistent_repair_min_interval_sec() == 5.0


def test_scanner_ws_repair_cycle_defaults_are_aggressive_but_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC", raising=False)

    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_wait_sec() == 10.0
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_persistent_sec() == 30.0

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC", "1")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC", "5")
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_wait_sec() == 5.0
    assert kiwoom_sniper_v2._scanner_ws_repair_cycle_persistent_sec() == 10.0


def test_scanner_heavy_eval_recheck_fresh_sec_defaults_to_pre_ai_freshness(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_scanner_hot_override_cache()
    monkeypatch.delenv("KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC", raising=False)
    assert kiwoom_sniper_v2._scanner_heavy_eval_recheck_fresh_sec() == 3.0

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC", "0.5")
    assert kiwoom_sniper_v2._scanner_heavy_eval_recheck_fresh_sec() == 1.0

    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC", "60")
    assert kiwoom_sniper_v2._scanner_heavy_eval_recheck_fresh_sec() == 20.0


def test_persistent_ws_gap_uses_dedicated_repair_batch_queue():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    queue_def_idx = source.index("pending_scanner_ws_persistent_repair")
    queue_call_idx = source.index("_queue_scanner_ws_persistent_repair(")
    force_publish_idx = source.index('"repair_cycle": "persistent_ws_gap"')

    assert queue_def_idx < queue_call_idx < force_publish_idx


def test_subscription_recheck_snapshot_is_applied_before_fast_precheck_retry():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
    helper_idx = source.index("_apply_subscription_recheck_snapshot_if_ready")
    queue_idx = source.index("_queue_scanner_ws_persistent_repair(", helper_idx)
    apply_idx = source.index('phase="fast_precheck"', queue_idx)
    retry_idx = source.index("_defer_emit_scanner_fast_precheck", apply_idx)
    skip_idx = source.index("scanner_fast_precheck_subscription_recheck_snapshot_applied", apply_idx)
    residual_idx = source.index("subscription_alive_but_entry_stale", retry_idx)

    assert helper_idx < queue_idx < apply_idx < retry_idx
    assert apply_idx < skip_idx
    assert retry_idx < residual_idx


def test_scanner_no_trade_eviction_requires_grace_and_repeated_confirmation(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_GRACE_SEC", "60")
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_MIN_COUNT", "2")
    target = {
        "id": 77,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1000.0,
    }
    ws_data = {
        "received_types": {"0D", "0w"},
        "last_ws_update_ts": 1058.0,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_no_trade(
        target,
        ws_data,
        now_ts=1059.0,
    )
    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "scanner_no_trade_grace_active"

    first_confirm = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_no_trade(
        target,
        ws_data,
        now_ts=1061.0,
    )
    assert first_confirm["should_evict"] is False
    assert first_confirm["eviction_attempt_count"] == 1

    second_confirm = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_no_trade(
        target,
        ws_data,
        now_ts=1067.0,
    )
    assert second_confirm["should_evict"] is True
    assert second_confirm["eviction_reason"] == "scanner_no_trade_hot_slot_rotation"
    assert second_confirm["terminal_reason"] == "no_0b_after_grace"
    assert second_confirm["no_trade_received_types"] == "0D,0w"


def test_scanner_stale_eviction_counts_old_rest_quote_with_stale_ws(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_STALE_EVICTION_MAX_WATCH_AGE_SEC", "300")
    target = {
        "id": 77,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1000.0,
        "_scanner_watch_eviction_stale_first_seen_epoch": 1000.0,
        "_scanner_watch_eviction_stale_count": 2,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        target,
        now_ts=1400.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={
            "ws_recovery_outcome": "rest_quote_applied",
            "ws_subscription_repair_needed": True,
            "ws_subscription_recheck_status": "subscribed_snapshot_stale_or_missing",
        },
    )

    assert decision["should_evict"] is True
    assert decision["eviction_reason"] == "stale_recovery_failed"
    assert decision["eviction_attempt_count"] == 3
    assert decision["ws_recovery_outcome"] == "rest_quote_applied_ws_still_stale"


def test_scanner_stale_eviction_resets_recent_rest_quote_recovery(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_REST_QUOTE_STALE_EVICTION_MAX_WATCH_AGE_SEC", "300")
    target = {
        "id": 77,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1300.0,
        "_scanner_watch_eviction_stale_first_seen_epoch": 1300.0,
        "_scanner_watch_eviction_stale_count": 2,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_stale(
        target,
        now_ts=1400.0,
        stale_reason="stale_ws_snapshot",
        recovery_fields={
            "ws_recovery_outcome": "rest_quote_applied",
            "ws_subscription_repair_needed": True,
            "ws_subscription_recheck_status": "subscribed_snapshot_stale_or_missing",
        },
    )

    assert decision["should_evict"] is False
    assert decision["eviction_attempt_count"] == 0
    assert "_scanner_watch_eviction_stale_count" not in target


def test_scanner_no_trade_eviction_resets_when_0b_arrives(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_GRACE_SEC", "60")
    target = {
        "id": 77,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1000.0,
        "_scanner_watch_no_trade_count": 3,
        "_scanner_watch_no_trade_first_observed_epoch": 1061.0,
        "_scanner_watch_no_trade_last_observed_epoch": 1067.0,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_no_trade(
        target,
        {"received_types": {"0B", "0D"}, "last_ws_update_ts": 1070.0},
        now_ts=1070.0,
    )

    assert decision["should_evict"] is False
    assert "_scanner_watch_no_trade_count" not in target
    assert "_scanner_watch_no_trade_first_observed_epoch" not in target
    assert "_scanner_watch_no_trade_last_observed_epoch" not in target


def test_scanner_no_trade_eviction_waits_for_realtime_type(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_GRACE_SEC", "60")
    target = {
        "id": 77,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 0,
        "buy_time": None,
        "entry_armed_at_epoch": 1000.0,
        "_scanner_watch_no_trade_count": 2,
    }

    decision = kiwoom_sniper_v2._scanner_watch_eviction_decision_from_no_trade(
        target,
        {"curr": 70000, "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback"},
        now_ts=1100.0,
    )

    assert decision["should_evict"] is False
    assert decision["eviction_reason"] == "scanner_no_trade_waiting_realtime_type"
    assert "_scanner_watch_no_trade_count" not in target


def test_ws_reg_budget_skipped_expires_scanner_hot_slot(monkeypatch):
    emitted = []
    active = [
        {
            "id": 77,
            "code": "005930",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_qty": 0,
            "buy_time": None,
        },
        {
            "id": 88,
            "code": "000660",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "buy_qty": 1,
        },
    ]
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", active)
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    monkeypatch.setattr(
        kiwoom_sniper_v2.sniper_state_handlers,
        "_log_entry_pipeline",
        lambda target, code, stage, **fields: emitted.append(
            {"target": target, "code": code, "stage": stage, "fields": fields}
        ),
    )

    expired = kiwoom_sniper_v2.handle_ws_reg_budget_skipped(
        {"codes": ["005930", "000660"], "source": "scalping_scanner_promote", "max_items": 24}
    )

    assert expired is True
    assert active[0]["status"] == "EXPIRED"
    assert active[1]["status"] == "HOLDING"
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]
    assert emitted[-1]["stage"] == "scalping_scanner_watch_eviction"
    assert emitted[-1]["fields"]["eviction_reason"] == "scanner_ws_budget_skipped_hot_slot_rotation"
    assert emitted[-1]["fields"]["terminal_reason"] == "ws_item_budget_exhausted"
    assert emitted[-1]["fields"]["ws_recovery_outcome"] == "ws_reg_budget_skipped"


def test_db_poll_scanner_target_attach_logs_recovery(monkeypatch):
    emitted = []
    published = []
    targets = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "code": code, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 99,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "type": "SCALP",
        },
        targets,
        now_ts=1002.0,
    )

    assert attached is True
    assert targets[0]["id"] == 99
    assert targets[0]["added_time"] == 1002.0
    assert published == [
        ("COMMAND_WS_REG", {"codes": ["005930"], "source": "scanner_db_poll_attach"})
    ]
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "db_poll_attached"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "eventbus_attach_missing_recovered_from_database_poll"
    assert emitted[-1]["fields"]["runtime_record_id"] == 99


def test_db_poll_scanner_target_preserves_entry_armed_recency(monkeypatch):
    emitted = []
    published = []
    targets = []
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "code": code, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 101,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "type": "SCALP",
            "entry_armed_at_epoch": 1001.0,
        },
        targets,
        now_ts=2002.0,
    )

    assert attached is True
    assert targets[0]["id"] == 101
    assert targets[0]["added_time"] == 1001.0
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "db_poll_attached"
    assert emitted[-1]["fields"]["runtime_record_id"] == 101


def test_db_poll_scanner_target_blocks_identity_mismatch(monkeypatch):
    emitted = []
    published = []
    targets = []
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "두산")
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "code": code, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 101,
            "code": "000150",
            "name": "아로마티카",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 5450,
            "type": "SCALP",
            "entry_armed_at_epoch": 1001.0,
        },
        targets,
        now_ts=2002.0,
    )

    assert attached is False
    assert targets == []
    assert published == []
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scanner_identity_name_mismatch"
    assert emitted[-1]["fields"]["scanner_identity_payload_name"] == "아로마티카"
    assert emitted[-1]["fields"]["scanner_identity_db_name"] == "두산"
    assert emitted[-1]["fields"]["scanner_identity_mismatch_expired"] is True
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]


def test_boot_filter_drops_invalid_scanner_identity_without_replacing_list(monkeypatch):
    emitted = []
    fake_db = _ExpireDB()
    monkeypatch.setattr(kiwoom_sniper_v2, "_latest_stock_name_from_db", lambda code: "두산" if code == "000150" else "")
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", fake_db)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "code": code, "fields": fields or {}}
        ),
    )
    targets = [
        {
            "id": 101,
            "code": "000150",
            "name": "아로마티카",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 5450,
        },
        {"id": 102, "code": "005930", "name": "SAMSUNG", "strategy": "SCALPING", "status": "WATCHING"},
    ]
    original_id = id(targets)

    targets[:] = kiwoom_sniper_v2._filter_invalid_scanner_identity_targets(targets)

    assert id(targets) == original_id
    assert [target["code"] for target in targets] == ["005930"]
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "scanner_identity_name_mismatch"
    assert emitted[-1]["fields"]["scanner_identity_mismatch_expired"] is True
    assert fake_db.calls == [({"status": "EXPIRED"}, False)]


def test_db_poll_target_attach_skips_existing_real_target(monkeypatch):
    emitted = []
    published = []
    targets = [{"code": "005930", "strategy": "SCALPING", "status": "WATCHING"}]
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 100,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
        },
        targets,
        now_ts=1003.0,
    )

    assert attached is False
    assert targets == [{"code": "005930", "strategy": "SCALPING", "status": "WATCHING"}]
    assert published == []
    assert emitted == []


def test_risk_off_without_confirmed_context_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=["unit"],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": False,
        },
    )

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert "risk=RISK_OFF" in reason
    assert "risk_context=not_confirmed" in reason
    assert meta["market_regime_prior_observed"] is True
    assert meta["market_regime_prior_reason"] == "recovery_gate_signal_insufficient"


def test_non_swing_strategy_does_not_refresh_market_regime(monkeypatch):
    class BrokenMarketRegime:
        def refresh_if_needed(self):
            raise AssertionError("non-swing strategy should not refresh market regime")

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", BrokenMarketRegime())

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("SCALPING")

    assert blocked is False
    assert reason == ""
    assert meta["strategy_scope"] == "non_swing"
    assert meta["confirmed_risk_block"] is False


def test_single_market_risk_off_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": True,
            "confirmed_risk_block": False,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert meta["market_regime_prior_reason"] == "single_market_risk_off_advisory"


def test_oil_only_recovery_gate_deficit_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=35,
                swing_entry_recovery_gate_score=35,
                recovery_gate_state="INSUFFICIENT",
                swing_recovery_gate_label="INSUFFICIENT",
                recovery_gate_reason="oil_only_recovery_signal_insufficient",
                oil_only_recovery_prior=True,
                market_regime_continuous_score=73.1543,
                market_regime_continuous_label="RISK_ON",
                market_regime_source_quality="valid",
                debug={"component_scores": {"vix": 0, "oil": 35, "fng": 0, "local_breadth": 0}, "score_threshold": 70},
                reasons=["원유 반전 시그널"],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=True,
                wti_dead_cross=False,
                wti_from_recent_high_pct=-5.0,
                fng_value=15.0,
                fng_prev=15.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=22.99,
                wti_rsi=45.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": False,
        },
    )

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert "legacy_recovery_gate_score=35/70" in reason
    assert "continuous_label=RISK_ON" in reason
    assert meta["market_regime_prior_reason"] == "oil_only_recovery_signal_insufficient"
    assert meta["oil_only_recovery_prior"] is True
    assert meta["market_regime_continuous_label"] == "RISK_ON"


def test_confirmed_panic_context_blocks_swing_market_regime(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "PANIC_SELL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": True,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is True
    assert meta["confirmed_risk_block"] is True
    assert meta["market_regime_block_reason"] == "confirmed_risk_context"


def test_string_false_risk_flags_do_not_confirm_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": "False",
            "risk_off_advisory": "False",
            "single_market_risk_off_advisory": "False",
            "confirmed_risk_block": False,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert meta["market_regime_prior_observed"] is True


def test_truthy_flag_treats_false_strings_as_false():
    assert sniper_market_regime._truthy_flag("False") is False
    assert sniper_market_regime._truthy_flag("0") is False
    assert sniper_market_regime._truthy_flag("true") is True
