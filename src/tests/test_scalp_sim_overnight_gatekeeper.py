import json
from pathlib import Path

from src.engine import scalp_sim_overnight as overnight


class _FakeOvernightAI:
    def __init__(self, action="SELL_TODAY"):
        self.action = action
        self.calls = []

    def evaluate_scalping_overnight_decision(self, name, code, ctx):
        self.calls.append((name, code, ctx))
        return {
            "action": self.action,
            "confidence": 77,
            "reason": "unit-test decision",
            "risk_note": "unit-test",
            "ai_parse_ok": True,
            "ai_response_ms": 123,
            "ai_model": "gpt-5.4-mini",
            "openai_endpoint_name": "overnight",
            "openai_schema_name": "overnight_v1",
            "openai_transport_mode": "responses_ws",
            "openai_ws_used": True,
        }


def _state_path(tmp_path: Path, positions: list[dict]) -> Path:
    path = tmp_path / "scalp_live_simulator_state.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "simulation_book": "scalp_ai_buy_all",
                "active_positions": positions,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _position(**overrides):
    row = {
        "name": "SIMTEST",
        "code": "000001",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "actual_order_submitted": False,
        "sim_record_id": "SIM-000001-1",
        "sim_parent_record_id": "PARENT-1",
        "buy_price": 10000,
        "buy_qty": 3,
        "last_ai_profit_rate": 0.5,
        "last_ai_peak_profit": 0.8,
        "last_ai_action": "HOLD",
        "last_ai_score": 72,
        "holding_price_samples": [{"price": 10100}],
    }
    row.update(overrides)
    return row


def test_sell_today_closes_sim_without_real_order(tmp_path):
    path = _state_path(tmp_path, [_position()])

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_FakeOvernightAI("SELL_TODAY"),
        state_path=path,
        emit_events=False,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert report["summary"]["sell_today"] == 1
    assert report["summary"]["active_after"] == 0
    assert payload["active_positions"] == []
    row = report["rows"][0]
    assert row["decision"] == "SELL_TODAY"
    assert row["sell_today_realized_profit_pct"] is not None
    assert row["runtime_features"]["actual_order_submitted"] is False
    assert row["runtime_features"]["broker_order_forbidden"] is True


def test_emitted_events_include_metric_contract_and_openai_provenance(tmp_path, monkeypatch):
    emitted = []
    monkeypatch.setattr(
        overnight,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, fields: emitted.append((stage, fields)),
    )
    path = _state_path(tmp_path, [_position()])

    overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_FakeOvernightAI("SELL_TODAY"),
        state_path=path,
        emit_events=True,
    )

    decision_fields = dict(emitted[0][1])
    sell_fields = dict(emitted[1][1])
    assert emitted[0][0] == "scalp_sim_overnight_decision"
    assert decision_fields["metric_role"] == "sim_probe_ev"
    assert decision_fields["decision_authority"] == "sim_observation_only"
    assert decision_fields["threshold_family"] == "scalp_sim_overnight_ai_carry"
    assert decision_fields["source_quality_gate"] == "overnight_decision_coverage"
    assert decision_fields["openai_model"] == "gpt-5.4-mini"
    assert decision_fields["openai_transport_mode"] == "responses_ws"
    assert decision_fields["openai_ws_used"] is True
    assert decision_fields["openai_response_ms"] == 123
    assert sell_fields["runtime_effect"] == "simulated_completed_only"


def test_hold_overnight_keeps_active_state_with_carry_fields(tmp_path):
    path = _state_path(tmp_path, [_position()])

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_FakeOvernightAI("HOLD_OVERNIGHT"),
        state_path=path,
        emit_events=False,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert report["summary"]["hold_overnight"] == 1
    assert report["summary"]["active_after"] == 1
    active = payload["active_positions"][0]
    assert active["status"] == "HOLDING"
    assert active["scalp_sim_overnight_status"] == "HOLD_OVERNIGHT"
    assert active["scalp_sim_overnight_decision_date"] == "2026-05-19"
    assert active["actual_order_submitted"] is False


def test_ai_failure_falls_back_to_sell_today(tmp_path):
    class _FailingAI:
        def evaluate_scalping_overnight_decision(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    path = _state_path(tmp_path, [_position()])

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_FailingAI(),
        state_path=path,
        emit_events=False,
    )

    assert report["summary"]["ai_failure_fallback"] == 1
    assert report["summary"]["sell_today"] == 1
    assert report["summary"]["active_after"] == 0


def test_ai_timeout_fallback_is_attributed(tmp_path):
    class _TimeoutAI:
        def evaluate_scalping_overnight_decision(self, *_args, **_kwargs):
            return {
                "action": "SELL_TODAY",
                "confidence": 0,
                "reason": "ai_failure_sell_today_fallback",
                "risk_note": "ai_response_error_or_insufficient_context",
                "ai_parse_ok": False,
                "ai_result_source": "exception",
                "ai_exception_message": "Request timed out.",
            }

    path = _state_path(tmp_path, [_position()])

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_TimeoutAI(),
        state_path=path,
        emit_events=False,
    )

    assert report["summary"]["ai_failure_fallback"] == 1
    assert report["summary"]["ai_timeout_fallback"] == 1
    assert report["rows"][0]["overnight_ai_fallback"] is True
    assert report["rows"][0]["overnight_ai_fallback_class"] == "timeout"


def test_idempotency_skips_same_date_decision(tmp_path):
    path = _state_path(
        tmp_path,
        [
            _position(
                scalp_sim_overnight_status="HOLD_OVERNIGHT",
                scalp_sim_overnight_decision_date="2026-05-19",
            )
        ],
    )
    ai = _FakeOvernightAI("SELL_TODAY")

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=ai,
        state_path=path,
        emit_events=False,
    )

    assert report["summary"]["idempotent_skipped"] == 1
    assert report["summary"]["active_after"] == 1
    assert ai.calls == []


def test_excludes_real_non_sim_and_completed_rows(tmp_path):
    path = _state_path(
        tmp_path,
        [
            _position(sim_record_id="SIM-A", actual_order_submitted=True),
            _position(sim_record_id="SIM-B", simulation_book="other"),
            _position(sim_record_id="SIM-C", status="COMPLETED"),
        ],
    )

    report = overnight.run_sim_overnight(
        target_date="2026-05-19",
        ai_engine=_FakeOvernightAI("SELL_TODAY"),
        state_path=path,
        emit_events=False,
    )

    assert report["summary"]["decision_target"] == 0
    assert report["summary"]["active_after"] == 3
