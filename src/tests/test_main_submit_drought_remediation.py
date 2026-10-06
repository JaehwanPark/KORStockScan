"""Main observation and selected recipe custody; no provider or broker I/O."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_setup_evidence as E
from src.tests.test_entry_strategy_policy import raw, setup, policy


def confirmed():
    payload = raw()
    payload["stock_code"] = "000660"
    payload["current"]["fluctuation_pct"] = 1
    payload["features"].update(
        curr_vs_micro_vwap_bp=-5, curr_vs_ma5_bp=0, micro_vwap_available=True
    )
    selected = A.candidate_policy(policy())
    original = E.mechanistic_entry_policy_decision(setup(payload), policy=selected)[
        "effective_setup_evidence"
    ]
    return original, A.bind_confirmation(original, selected), selected


def response(ledger):
    return dict(
        schema=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
        risk_verdict="PASS",
        risk_codes=["NO_BLOCKING_RISK"],
        supporting_fact_ids=list(A.CONFIRMATION_FACTS),
        contradicting_fact_ids=ledger["contradicting_facts"],
        confidence=70,
    )


def test_confirmation_is_separate_and_all_consumers_agree():
    original, ledger, selected = confirmed()
    assert ledger["setup_state"] == original["setup_state"]
    assert ledger["positive_facts"] == original["positive_facts"]
    assert ledger["strategy_raw_sha256"] == original["strategy_raw_sha256"]
    assert not E.validate_entry_setup_evidence(ledger)
    schema = E.entry_risk_adjudication_openai_schema(ledger)
    assert "NO_BLOCKING_RISK" in schema["properties"]["risk_codes"]["items"]["enum"]
    assert set(A.CONFIRMATION_FACTS) <= set(
        schema["properties"]["supporting_fact_ids"]["items"]["enum"]
    )
    assert not E.validate_mechanistic_risk_screen(
        response(ledger), setup_evidence=ledger, policy=selected
    )
    result = E.compose_mechanistic_primary_decision(
        setup_evidence=ledger, ai_risk_adjudication=response(ledger), policy=selected
    )
    assert result["action"] == "WAIT" and result["entry_probe_intent"] is True
    assert result["entry_ai_screen_pass"] is True
    assert result["actual_order_submitted"] is False
    # The English recipe instruction and exact facts reach the compact payload.
    from src.engine.ai_engine_openai import _entry_provider_ledger

    wire = _entry_provider_ledger(ledger)
    assert wire["machine_confirmation"] == ledger["machine_confirmation"]
    assert all(f in wire["positive_facts"] for f in A.CONFIRMATION_FACTS)
    assert wire["machine_confirmation"]["screen_rule"].isascii()


@pytest.mark.parametrize(
    "damage",
    [
        "source",
        "policy",
        "receipt",
        "values",
        "missing",
        "contradiction",
        "invented",
        "legacy",
    ],
)
def test_confirmation_never_repairs_invalid_or_unbound_pass(damage):
    original, ledger, selected = confirmed()
    r = response(ledger)
    if damage in {"source", "policy", "receipt", "values"}:
        key = {
            "source": "source_sha256",
            "policy": "policy_sha256",
            "receipt": "decision_receipt_sha256",
            "values": "values",
        }[damage]
        ledger["machine_confirmation"][key] = {} if damage == "values" else "f" * 64
        ledger["machine_confirmation"]["confirmation_sha256"] = A.S.digest(
            {
                k: v
                for k, v in ledger["machine_confirmation"].items()
                if k != "confirmation_sha256"
            }
        )
        ledger["evidence_sha256"] = A.S.digest(
            {k: v for k, v in ledger.items() if k != "evidence_sha256"}
        )
    elif damage == "missing":
        ledger.pop("machine_confirmation")
    elif damage == "contradiction":
        r["risk_codes"] = ["CONFIRMATION_MISSING"]
    elif damage == "invented":
        r["supporting_fact_ids"].append("future_profit_confirmed")
    else:
        selected = policy()
    result = E.compose_mechanistic_primary_decision(
        setup_evidence=ledger, ai_risk_adjudication=r, policy=selected
    )
    assert not result["entry_probe_intent"]
    assert not result["entry_ai_screen_pass"]


def test_original_caution_is_preserved_after_contract_repair():
    original, ledger, selected = confirmed()
    r = response(ledger)
    r.update(
        risk_verdict="CAUTION",
        risk_codes=["CONFIRMATION_MISSING"],
        supporting_fact_ids=original["positive_facts"][:2],
    )
    before = deepcopy(r)
    result = E.compose_mechanistic_primary_decision(
        setup_evidence=ledger, ai_risk_adjudication=r, policy=selected
    )
    assert r == before and result["entry_ai_advisory_verdict"] == "CAUTION"
    assert not result["entry_probe_intent"]


@pytest.mark.parametrize("damage", [None, {}, [], "bad"])
def test_malformed_confirmation_is_a_contract_error(damage):
    _, ledger, _ = confirmed()
    ledger["machine_confirmation"] = damage
    assert "entry_machine_confirmation_invalid" in E.validate_entry_setup_evidence(
        ledger
    )


def test_confirmation_builder_never_rehashes_arbitrary_input_damage():
    original, _, selected = confirmed()
    original["positive_facts"].append("fake_current_fact")
    with pytest.raises(ValueError, match="machine_confirmation_setup_invalid"):
        A.bind_confirmation(original, selected)


def test_metadata_restoration_matches_recorded_digest_without_source_mutation():
    from src.engine.scalping.entry_setup_source_repair import (
        restore_original_recipe_metadata,
    )

    original, _, selected = confirmed()
    assessment = E.mechanistic_entry_policy_decision(original, policy=selected)
    assessment.pop("effective_setup_evidence", None)
    bad = deepcopy(original)
    bad["strategy_selection"]["policy_sha256"] = A.S.digest(selected)
    capture = dict(
        schema="mechanistic_entry_observation_v1",
        source=dict(
            setup_evidence=bad,
            exact_payload=bad["strategy_raw_input"],
            assessment=assessment,
        ),
        redacted=False,
        provider_called=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    capture["machine_observation_sha256"] = A.S.digest(capture)
    before = deepcopy(capture)
    restored, proof = restore_original_recipe_metadata(capture)
    assert restored == original and capture == before
    assert proof["restored_evidence_sha256"] == proof["original_evidence_sha256"]
    assert proof["changed_fields"] == ["strategy_selection.policy_sha256"]
    capture["source"]["setup_evidence"]["positive_facts"].append("fake_fact")
    capture["machine_observation_sha256"] = A.S.digest(
        {k: v for k, v in capture.items() if k != "machine_observation_sha256"}
    )
    with pytest.raises(ValueError):
        restore_original_recipe_metadata(capture)


def test_price_path_excludes_ambiguity_and_missing_bars_without_zero_imputation():
    from src.engine.scalping import main_submit_drought_research as R

    at = datetime.fromisoformat("2026-10-06T09:00:30+09:00")
    start = at.replace(second=0).timestamp() + 60
    bars = {
        start + i * 60: dict(open=100.0, high=100.1, low=99.9, close=100.0)
        for i in range(20)
    }
    assert R.price_path(at.isoformat(), bars)["net_return_pct"] == pytest.approx(-0.33)
    bars[start]["high"] = 101.0
    assert R.price_path(at.isoformat(), bars)["net_return_pct"] == 0.5
    bars[start]["low"] = 99.0
    assert R.price_path(at.isoformat(), bars)["net_return_pct"] is None
    bars.pop(start)
    assert R.price_path(at.isoformat(), bars)["net_return_pct"] is None


def test_comparison_has_no_preservation_or_sample_size_gate():
    from src.engine.scalping import main_submit_drought_research as R

    assert R.choose({"win_rate": 0.2}, {"D": {"win_rate": 0.3}})["winner"] == "D"
    assert R.choose({"win_rate": 0.3}, {"D": {"win_rate": 0.3}})["winner"] is None
    assert R.choose({"win_rate": None}, {"D": {"win_rate": None}})["winner"] is None
    assert (
        R.choose(
            {"win_rate": None},
            {
                "D": {
                    "win_rate": 0.9,
                    "wins": 1,
                    "losses": 2,
                    "outcome_states": {
                        "target_first": 1,
                        "adverse_first": 2,
                        "timeout": 10,
                    },
                }
            },
        )["winner"]
        is None
    )


def test_recipe_monitor_uses_latest_exact_revision():
    from src.tests.test_submission_bottleneck_monitor import event, START
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from datetime import timedelta

    fields = dict(
        machine_revision_schema="exact_machine_revision_v1",
        machine_observation_sha256="a" * 64,
        machine_revision_parent_sha256="",
        entry_machine_confirmation_sha256="c" * 64,
        entry_machine_confirmation_recipe_id=A.RECIPE_ID,
        entry_machine_confirmation_source_sha256="d" * 64,
        entry_machine_confirmation_policy_sha256="e" * 64,
    )
    row = monitor.snapshot([event(**fields)], START + timedelta(seconds=2))["rows"][0]
    assert (
        row["recipe_confirmation_evidence"]["entry_machine_confirmation_sha256"]
        == "c" * 64
    )
    later = event(
        when=START + timedelta(seconds=1),
        action="RECHECK",
        screen="not_requested_machine_nonentry",
        machine_revision_schema="exact_machine_revision_v1",
        machine_observation_sha256="b" * 64,
        machine_revision_parent_sha256="a" * 64,
    )
    row = monitor.snapshot([event(**fields), later], START + timedelta(seconds=2))[
        "rows"
    ][0]
    assert row["recipe_confirmation_evidence"] is None


def test_conflicting_auxiliary_responses_isolate_one_capture(tmp_path):
    import json
    from src.engine.scalping import main_submit_drought_research as R

    source = tmp_path / "ai_decision_trace/ai_decision_trace_2026-10-06.jsonl"
    source.parent.mkdir()
    final = dict(entry_ai_advisory_verdict="PASS")
    base = dict(
        machine_observation_sha256="a" * 64,
        decision_quality_final_response=final,
        decision_quality_final_response_sha256=A.S.digest(final),
        response_sha256="c" * 64,
    )
    source.write_text(
        "\n".join(
            json.dumps(t)
            for t in (
                base,
                dict(base, response_sha256="d" * 64),
                dict(base, machine_observation_sha256="b" * 64),
            )
        )
        + "\n"
    )
    traces, receipt = R._traces(tmp_path, "2026-10-06")
    assert traces["a" * 64]["source_gap"] == "exact_machine_trace_response_conflict"
    assert traces["b" * 64]["original_response_sha256"] == "c" * 64
    assert receipt["bytes"] == source.stat().st_size


def test_daily_source_projection_is_bounded_and_consumed_by_exact_day(
    tmp_path, monkeypatch
):
    import json
    from src.engine.scalping import main_submit_drought_research as R
    from src.engine.scalping import mechanistic_entry_runtime_policy as M

    original, _, selected = confirmed()
    raw_input = original["strategy_raw_input"]
    raw_input["entry_machine_input_as_of"] = datetime.fromisoformat(
        "2026-10-06T09:00:30+09:00"
    ).timestamp()
    original = setup(raw_input)
    capture = dict(
        schema="mechanistic_entry_observation_v1",
        captured_at="2026-10-06T09:00:30+09:00",
        source=dict(
            setup_evidence=original,
            exact_payload=raw_input,
            assessment=E.mechanistic_entry_policy_decision(original, policy=selected),
        ),
        label_context=dict(stock_code="000660"),
        redacted=False,
        provider_called=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    capture["source"]["assessment"].pop("effective_setup_evidence", None)
    capture["machine_observation_sha256"] = A.S.digest(capture)
    source = tmp_path / "ai_decision_payloads/ai_decision_payloads_2026-10-06.jsonl"
    source.parent.mkdir()
    source.write_text(json.dumps(capture) + "\n")
    monkeypatch.setattr(M, "for_cohort", lambda *a: dict(machine_policy=selected))
    bundle = dict(
        bundle_sha256="b" * 64,
        scope_policies={"KRX|KRX_REGULAR": dict(machine_policy=selected)},
    )
    result = R.build_daily(
        data_root=tmp_path,
        target_date="2026-10-06",
        bundle=bundle,
        source_bytes=source.stat().st_size,
    )
    assert (
        result["total_count"]
        == result["included_count"] + result["excluded_count"]
        == 1
    )
    assert result["groups"]["non_samsung"]["candidates"]["D"]["win_rate"] is None
    output = (
        tmp_path
        / "report/ai_decision_action_outcome_calibration/main_submit_drought_research_2026-10-06.json"
    )
    output.parent.mkdir(parents=True)
    output.write_text(json.dumps(result))
    assert (
        R.load_projection(tmp_path, "2026-10-06")["status"]
        == "observed_price_counterfactual"
    )
    assert R.load_projection(tmp_path, "2026-10-07")["status"] == "not_observed"
    source.write_text(source.read_text().replace("000660", "005930"))
    assert R.load_projection(tmp_path, "2026-10-06")["status"] == "source_gap"


@pytest.mark.parametrize(
    "last_call,refresh,expected",
    [(0, False, 1), (1, False, 1), (995, False, 0), (995, True, 1)],
)
def test_watching_evaluates_above_smart_target_with_existing_cooldown(
    monkeypatch, last_call, refresh, expected
):
    from src.engine import sniper_state_handlers as H
    from src.utils.constants import TRADING_RULES
    from src.tests.test_sniper_scale_in import _DummyDB

    calls = []
    for name in (
        "_handle_watching_opening_rotation",
        "_opening_rotation_handoff_defers_pre_ai_baseline",
    ):
        monkeypatch.setattr(H, name, lambda *a, **k: False)
    monkeypatch.setattr(H, "DB", _DummyDB())
    monkeypatch.setattr(H, "LAST_AI_CALL_TIMES", {"005930": last_call})
    monkeypatch.setattr(H, "LAST_LOG_TIMES", {})
    monkeypatch.setattr(H, "TRADING_RULES", TRADING_RULES)
    monkeypatch.setattr(H, "_resolve_stock_marcap", lambda *a: 1_000_000_000_000)
    monkeypatch.setattr(H, "_log_entry_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(H, "arm_big_bite_if_triggered", lambda **k: (False, {}))
    monkeypatch.setattr(H, "confirm_big_bite_follow_through", lambda **k: (True, {}))
    monkeypatch.setattr(
        H,
        "evaluate_scalping_strength_momentum",
        lambda *a, **k: dict(enabled=True, allowed=True, reason="ok"),
    )
    monkeypatch.setattr(
        H,
        "_resolve_watching_state_change_refresh",
        lambda *a, **k: dict(
            allowed=refresh,
            reason="machine_source_fresh_retry" if refresh else "cooldown",
        ),
    )
    monkeypatch.setattr(
        H, "_resolve_early_accel_recheck", lambda *a, **k: dict(allowed=False)
    )
    monkeypatch.setattr(
        H,
        "_resolve_scanner_async_entry_ai",
        lambda *a, **k: calls.append(k) or dict(status="pending"),
    )
    runtime = dict(
        strategy="SCALPING",
        pos_tag="SCANNER",
        now_ts=1000.0,
        now_dt=datetime(2026, 10, 6, 10),
        curr_price=273000,
        current_vpw=100,
        fluctuation=1,
        cooldowns={},
        event_bus=SimpleNamespace(publish=lambda *a, **k: None),
        is_trigger=False,
        msg="",
        ratio=0.1,
        liquidity_value=1e9,
        current_ai_score=75,
        ai_prob=0.75,
        buy_threshold=0.7,
        strong_vpw=100,
    )
    radar = SimpleNamespace(get_smart_target_price=lambda *a, **k: (268500, 0))
    H._handle_watching_strategy_branch(
        dict(
            id=1,
            code="005930",
            name="Samsung",
            strategy="SCALPING",
            position_tag="SCANNER",
        ),
        "005930",
        dict(
            curr=273000,
            last_ws_update_ts=1000.0,
            v_pw=100,
            ask_tot=100000,
            bid_tot=100000,
            open=270000,
        ),
        radar,
        object(),
        runtime,
        {
            **asdict(TRADING_RULES),
            "AI_WATCHING_COOLDOWN": 90,
            "MIN_SCALP_LIQUIDITY": 0,
            "BIG_BITE_HARD_GATE_TAGS_SCALPING": [],
        },
    )
    assert len(calls) == expected
