"""Frozen synthetic path-vote contract and postclose replay fixtures."""

import time
import json
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.ai.holding_exit_vote import (
    MARKETS, PATH_IDS, PATH_POLICY_BY_MARKET, PATH_PROMPT_VERSION,
    PATH_REASON_PREFIX,
    buy_fill_identity_from_legs, buy_fill_identity_from_runtime,
    input_snapshot_id, load_path_events_file, normalize_path_vote_bundle,
    path_policy_baseline_receipt,
    path_signal_snapshot,
)
from src.engine.scalping.holding_path_vote_replay import summarize_holding_path_votes
from src.engine.scalping.holding_path_vote_policy import (
    ENV_DATE, ENV_PATH, ENV_SHA, create_bundle, digest, load_bundle, policy_path,
    runtime_policy_from_env, validate_bundle, verify_source_handoff,
)


def test_v10_holding_prompt_names_each_path_and_keeps_action_directions():
    from src.engine.ai_prompt_contracts import (
        SCALPING_HOLDING_PATH_VOTE_SYSTEM_PROMPT as prompt,
    )
    assert prompt.isascii()
    for path in PATH_IDS:
        assert f"{path}:" in prompt
    assert "An EXIT vote can never permit an ADD" in prompt
    assert "an ADD vote can never permit a SELL" in prompt
    assert "Do not treat a submitted but unfilled ADD" in prompt


BUY_LEGS = [{"at": "1970-01-01T00:00:00+00:00", "order_no": "BUY-1",
             "execution_no": "FILL-1", "qty": 1}]
BUY_IDENTITY = input_snapshot_id([["BUY-1", "FILL-1", 1]])
EMPTY_SOURCE_QUALITY = {
    "strict_population_count": 0,
    "completed_population_complete": False,
    "main_completed_ids": [], "strict_completed_ids": [],
    "source_gap_ids": [], "excluded_by_id": {},
    "vote_replay_excluded_by_id": {}, "source_gap_date_count": 0,
}


def _receipt_stock(**extra):
    return {"_entry_receipt_filled_by_order_no": {"BUY-1": 1},
            "_entry_receipt_executions_by_order_no": {
                "BUY-1": {"FILL-1": {"cumulative_qty": 1}}},
            **extra}


def _events(path, market, *, verdicts=("PASS", "PASS"), position_key="record:7",
            session_key="2026-09-25", base_at=1.0):
    rows = []
    for index, verdict in enumerate(verdicts):
        at = base_at + index * 10.0
        response = {
            "input_snapshot_id": f"snapshot-{index}",
            "votes": [{
                "path_id": path, "verdict": verdict, "conviction": "FIRM",
                "reason_codes": [PATH_REASON_PREFIX[path] + "tape_evidence"],
            }],
        }
        event = normalize_path_vote_bundle(
            response, requested_paths=(path,),
            expected_snapshot_id=f"snapshot-{index}",
            position_key=position_key, market=market, session_key=session_key,
            model="gpt-5.4-nano", route="KRX", transport_epoch="1",
            source_generation=f"item:{index}", requested_at=at,
            received_at=at + 0.5, buy_fill_identity=BUY_IDENTITY,
            buy_fill_legs=BUY_LEGS, quote_observed_at=at - 0.1,
        )[0]
        event["persisted_at"] = at + 0.6
        event["provider_called"] = True
        rows.append(event)
    return rows


def test_baseline_receipt_covers_every_path_and_market_without_apply_authority():
    receipt = path_policy_baseline_receipt()
    assert len(receipt["policy_hashes"]) == len(PATH_IDS) * len(MARKETS)
    assert receipt["policy_set_sha256"] == input_snapshot_id(receipt["policy_hashes"])
    assert receipt["selected_policy"] is None
    assert receipt["allowed_runtime_apply"] is False


def test_zero_natural_votes_publish_source_bound_estimated_baseline(tmp_path):
    source_date, target_date = "2026-09-26", "2026-09-28"
    source = (tmp_path / "report" / "monitor_snapshots" /
              f"holding_exit_observation_{source_date}.json")
    source.parent.mkdir(parents=True)
    source.write_text('{"date":"2026-09-26"}', encoding="utf-8")
    import hashlib
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano",
    )
    bundle = create_bundle(
        source_date=source_date, target_date=target_date,
        source_report_sha256=source_sha, replay=replay,
        source_quality=EMPTY_SOURCE_QUALITY,
    )
    assert len(bundle["cells"]) == 15
    assert bundle["realized_paired_ev_krw"] is None
    assert bundle["evidence_grade"] == "estimated_provisional"
    assert bundle["cells"]["EXIT_TRAILING_TP|PREMARKET"]["scenario_decisions"][
        "source_gap"] == "INSUFFICIENT"
    path = policy_path(tmp_path, target_date)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(bundle), encoding="utf-8")
    assert load_bundle(tmp_path, target_date) == bundle
    selected, receipt = runtime_policy_from_env({
        ENV_DATE: target_date, ENV_PATH: str(path), ENV_SHA: bundle["bundle_sha256"],
    }, data_root=tmp_path, active_date=target_date)
    assert receipt["status"] == "baseline_policy_load_rejected"
    assert selected == PATH_POLICY_BY_MARKET
    source.write_text('{"date":"tampered"}', encoding="utf-8")
    _, rejected = runtime_policy_from_env({
        ENV_DATE: target_date, ENV_PATH: str(path), ENV_SHA: bundle["bundle_sha256"],
    }, data_root=tmp_path, active_date=target_date)
    assert rejected["status"] == "baseline_policy_load_rejected"
    tampered = dict(bundle)
    tampered["cells"] = dict(bundle["cells"])
    tampered["cells"].pop("EXIT_TRAILING_TP|PREMARKET")
    with pytest.raises(ValueError, match="header_invalid|cells_invalid"):
        validate_bundle(tampered, target_date=target_date)


def test_estimated_policy_strict_handoff_and_bootstrap_consume_same_hash(
    tmp_path, monkeypatch,
):
    from src.engine.automation import postclose_summary_handoff as handoff
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    from src.engine import build_next_stage2_checklist
    import hashlib
    source_date, target_date = "2026-09-26", "2026-09-28"
    report_dir = tmp_path / "report"
    observation = (report_dir / "monitor_snapshots" /
                   f"holding_exit_observation_{source_date}.json")
    observation.parent.mkdir(parents=True)
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano",
    )
    observation.write_text(json.dumps({
        "date": source_date, "holding_path_vote_replay": replay,
        "completed_population_quality": {
            "complete": False, "db_completed_main_ids": [],
            "strict_completed_position_ids": [], "source_gap_ids": [],
            "excluded_all_reasons": {}, "source_gap_dates": [],
        },
    }), encoding="utf-8")
    source_sha = hashlib.sha256(observation.read_bytes()).hexdigest()
    bundle = create_bundle(source_date=source_date, target_date=target_date,
                           source_report_sha256=source_sha, replay=replay,
                           source_quality=EMPTY_SOURCE_QUALITY)
    selected_file = policy_path(tmp_path, target_date)
    selected_file.parent.mkdir(parents=True)
    selected_file.write_text(json.dumps(bundle), encoding="utf-8")
    receipt = {
        "status": "estimated_provisional_published",
        "source_date": source_date, "target_date": target_date,
        "bundle_sha256": bundle["bundle_sha256"],
        "policy_set_sha256": bundle["policy_set_sha256"],
        "source_report_sha256": source_sha,
        "cell_count": 15, "allowed_runtime_apply": True,
    }
    summary_file = report_dir / "runtime_approval_summary" / (
        f"runtime_approval_summary_{source_date}.json")
    summary_file.parent.mkdir(parents=True)
    summary_file.write_text(json.dumps({
        "schema_version": 3, "holding_path_vote_policy": receipt,
    }), encoding="utf-8")
    monkeypatch.setattr(build_next_stage2_checklist, "_next_krx_trading_day",
                        lambda _: target_date)
    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_a: [])
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    checked = handoff.verify_summary_handoff(
        source_date, report_dir=report_dir, checklist_path=tmp_path / "unused.md",
        require_tower=False, require_checklist=False,
    )
    assert checked["status"] == "pass"
    env, bootstrap_receipt = bootstrap._holding_vote_handoff(target_date)
    assert bootstrap_receipt["bundle_sha256"] == bundle["bundle_sha256"]
    assert env[ENV_SHA] == bundle["bundle_sha256"]
    selected, runtime_receipt = runtime_policy_from_env(
        env, data_root=tmp_path, active_date=target_date)
    assert runtime_receipt["status"] == "estimated_provisional_loaded"
    assert selected == PATH_POLICY_BY_MARKET
    stale, stale_receipt = runtime_policy_from_env(
        env, data_root=tmp_path, active_date="2026-09-29")
    assert stale == PATH_POLICY_BY_MARKET
    assert stale_receipt["status"] == "baseline_policy_target_date_stale"
    altered = json.loads(json.dumps(bundle))
    altered["cells"]["EXIT_TRAILING_TP|PREMARKET"]["eligible_signal_count"] = 1
    altered["bundle_sha256"] = digest({
        key: value for key, value in altered.items() if key != "bundle_sha256"
    })
    validate_bundle(altered, target_date=target_date)
    with pytest.raises(ValueError, match="source_semantics_mismatch"):
        verify_source_handoff(tmp_path, altered)
    receipt["policy_set_sha256"] = "0" * 64
    summary_file.write_text(json.dumps({
        "schema_version": 3, "holding_path_vote_policy": receipt,
    }), encoding="utf-8")
    assert handoff.verify_summary_handoff(
        source_date, report_dir=report_dir, checklist_path=tmp_path / "unused.md",
        require_tower=False, require_checklist=False,
    )["status"] == "fail"


def test_long_lived_runtime_drops_expired_selected_vote_policy(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    key = ("EXIT_TRAILING_TP", "REGULAR")
    changed = {**PATH_POLICY_BY_MARKET[key], "min_votes": 3}
    monkeypatch.setattr(handlers, "_HOLDING_PATH_POLICY", {key: changed})
    monkeypatch.setattr(handlers, "_HOLDING_PATH_POLICY_RECEIPT", {
        "status": "estimated_provisional_loaded", "target_date": "2000-01-01",
        "bundle_sha256": "a" * 64,
    })
    assert handlers._holding_path_policy_for(*key) == PATH_POLICY_BY_MARKET[key]


def test_terminal_receipt_binds_only_same_tp_buy_generation():
    from src.engine import sniper_execution_receipts as receipts
    stock = _receipt_stock(
        id=7, last_exit_rule="scalp_trailing_take_profit",
    )
    buy_identity = buy_fill_identity_from_runtime(stock)
    assert buy_identity
    stock["holding_path_latest_tp_signal"] = {
        "position_key": "record:7", "buy_fill_identity": buy_identity,
        "signal_id": "crossing-7", "signal_at": 20.0,
        "policy_bundle_sha256": "a" * 64,
    }
    bound = receipts._holding_path_terminal_lineage_fields(stock, 7)
    assert bound["holding_path_signal_id"] == "crossing-7"
    assert bound["holding_path_terminal_signal_binding"] == (
        "same_position_buy_generation")
    stock["holding_path_latest_tp_signal"]["buy_fill_identity"] = "0" * 64
    gap = receipts._holding_path_terminal_lineage_fields(stock, 7)
    assert "holding_path_signal_id" not in gap
    assert gap["holding_path_terminal_signal_binding"] == (
        "source_gap_generation_mismatch")


def test_provider_call_returns_separate_votes_once(monkeypatch):
    from src.engine import ai_engine_openai
    from src.engine.scalping import ai_market_snapshot

    engine = object.__new__(ai_engine_openai.GPTSniperEngine)
    engine.lock = threading.Lock()
    engine.ai_disabled = False
    engine._extract_quote_snapshot = lambda _: {
        "best_bid": 99, "best_ask": 100,
        "best_bid_qty": 10, "best_ask_qty": 10,
    }
    monkeypatch.setattr(ai_engine_openai, "ai_input_preflight",
                        lambda _: {"allowed": True, "status": "ok", "blockers": []})
    monkeypatch.setattr(ai_market_snapshot, "ai_input_preflight",
                        lambda _: {"allowed": True, "status": "ok", "blockers": []})
    calls = []
    provider_meta = {"model": "gpt-5.4-nano", "transport": "http"}

    def provider(prompt, user_input, **kwargs):
        payload = json.loads(user_input)
        calls.append((prompt, payload, kwargs))
        engine._set_last_transport_meta({
            "openai_model": "gpt-5.4-nano",
            "openai_response_model": provider_meta["model"],
            "openai_transport_mode": provider_meta["transport"],
        })
        return {
            "input_snapshot_id": payload["input_snapshot_id"],
            "votes": [{"path_id": path, "verdict": "PASS", "conviction": "FIRM",
                       "reason_codes": [PATH_REASON_PREFIX[path] + "tape_evidence"]}
                      for path in payload["requested_paths"]],
        }

    engine._call_openai_safe = provider
    monkeypatch.setattr(ai_engine_openai, "record_ai_decision_trace",
                        lambda *_a, **_kw: {"ai_decision_trace_id": "trace-1"})
    rows = engine.evaluate_scalping_holding_path_votes(
        "Stock", "005930", {"curr": 99}, [], [],
        {"buy_price": 100, "curr_price": 99, "profit_rate": -1,
         "peak_profit": 0, "held_sec": 30, "prior_score": 90},
        requested_paths=("EXIT_SOFT_STOP", "ADD_REBOUND"),
        market="REGULAR", session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY,
        buy_fill_legs=BUY_LEGS,
        route="KRX", transport_epoch="1", source_generation="item:1",
        quote_observed_at=time.time(),
        holding_context={},
    )
    assert len(calls) == 1
    assert [row["path_id"] for row in rows] == ["EXIT_SOFT_STOP", "ADD_REBOUND"]
    assert all(row["status"] == "VALID" for row in rows)
    provider_meta["model"] = "gpt-5.4-nano-2026-03-17"
    snapshot_model = engine.evaluate_scalping_holding_path_votes(
        "Stock", "005930", {"curr": 99}, [], [],
        {"buy_price": 100, "curr_price": 99, "profit_rate": -1,
         "peak_profit": 0, "held_sec": 30},
        requested_paths=("EXIT_SOFT_STOP",), market="REGULAR",
        session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY, buy_fill_legs=BUY_LEGS,
        route="KRX", transport_epoch="1", source_generation="item:snapshot",
        quote_observed_at=time.time(), holding_context={},
    )
    assert snapshot_model[0]["status"] == "VALID"
    provider_meta["model"] = "gpt-5.4-mini"
    wrong_model = engine.evaluate_scalping_holding_path_votes(
        "Stock", "005930", {"curr": 99}, [], [],
        {"buy_price": 100, "curr_price": 99, "profit_rate": -1,
         "peak_profit": 0, "held_sec": 30},
        requested_paths=("EXIT_SOFT_STOP",), market="REGULAR",
        session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY, buy_fill_legs=BUY_LEGS,
        route="KRX", transport_epoch="1", source_generation="item:2",
        quote_observed_at=time.time(), holding_context={},
    )
    assert wrong_model[0]["status"] == "INSUFFICIENT"
    assert wrong_model[0]["excluded_reason"] == (
        "provider_response_model_missing_or_mismatch"
    )
    def untrusted_provider(*args, **kwargs):
        response = provider(*args, **kwargs)
        engine._set_last_transport_meta({})
        response["openai_response_model"] = "gpt-5.4-nano"
        return response

    engine._call_openai_safe = untrusted_provider
    spoofed_model = engine.evaluate_scalping_holding_path_votes(
        "Stock", "005930", {"curr": 99}, [], [],
        {"buy_price": 100, "curr_price": 99, "profit_rate": -1,
         "peak_profit": 0, "held_sec": 30},
        requested_paths=("EXIT_SOFT_STOP",), market="REGULAR",
        session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY, buy_fill_legs=BUY_LEGS,
        route="KRX", transport_epoch="1", source_generation="item:spoof",
        quote_observed_at=time.time(), holding_context={},
    )
    assert spoofed_model[0]["status"] == "INSUFFICIENT"
    assert spoofed_model[0]["excluded_reason"] == (
        "provider_response_model_missing_or_mismatch"
    )
    provider_meta["model"] = "gpt-5.4-nano"
    engine._call_openai_safe = provider
    from types import SimpleNamespace
    monkeypatch.setattr(ai_engine_openai, "TRADING_RULES", SimpleNamespace(
        OPENAI_HOLDING_EXIT_VOTE_MODEL="gpt-5.4-nano",
        OPENAI_HOLDING_EXIT_VOTE_TIMEOUT_MS=1,
    ))

    def slow_provider(*args, **kwargs):
        time.sleep(0.01)
        return provider(*args, **kwargs)

    engine._call_openai_safe = slow_provider
    late = engine.evaluate_scalping_holding_path_votes(
        "Stock", "005930", {"curr": 99}, [], [],
        {"buy_price": 100, "curr_price": 99, "profit_rate": -1,
         "peak_profit": 0, "held_sec": 30},
        requested_paths=("EXIT_SOFT_STOP",), market="REGULAR",
        session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY, buy_fill_legs=BUY_LEGS,
        route="KRX", transport_epoch="1", source_generation="item:3",
        quote_observed_at=time.time(), holding_context={},
    )
    assert late[0]["status"] == "INSUFFICIENT"
    assert late[0]["excluded_reason"] == "provider_response_after_deadline"
    assert calls[0][2]["schema_name"] == PATH_PROMPT_VERSION
    assert calls[0][2]["timeout_ms_override"] >= 3000
    assert "prior_score" not in json.dumps(calls[0][1])


@pytest.mark.parametrize("market", sorted(MARKETS))
@pytest.mark.parametrize("path", sorted(PATH_IDS))
def test_two_independent_path_votes_required_in_every_market(path, market):
    policy = PATH_POLICY_BY_MARKET[(path, market)]
    rows = _events(path, market)
    one = path_signal_snapshot(
        rows[:1], position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=20.0, policy=policy, buy_fill_identity=BUY_IDENTITY,
    )
    assert one["vote_count"] == 1 and one["decision"] == "INSUFFICIENT"
    two = path_signal_snapshot(
        rows, position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=20.0, policy=policy, buy_fill_identity=BUY_IDENTITY,
    )
    assert two["vote_count"] == 2 and two["decision"] == "PASS"
    assert path_signal_snapshot(
        _events(path, market, verdicts=("VETO", "VETO")),
        position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=20.0, policy=policy, buy_fill_identity=BUY_IDENTITY,
    )["decision"] == "VETO"


def test_cross_path_missing_cycle_and_late_receipt_cannot_vote():
    market = "REGULAR"
    path = "ADD_REBOUND"
    rows = _events(path, market)
    rows.append(_events("EXIT_TRAILING_TP", market)[0])
    missing = dict(rows[1], status="INSUFFICIENT", verdict=None,
                   conviction=None, excluded_reason="budget_deferred")
    assert path_signal_snapshot(
        [rows[0], missing, rows[2]], position_key="record:7",
        market=market, session_key="2026-09-25", path_id=path,
        model="gpt-5.4-nano", signal_at=20.0,
        policy=PATH_POLICY_BY_MARKET[(path, market)],
        buy_fill_identity=BUY_IDENTITY,
    )["decision"] == "INSUFFICIENT"
    late = dict(rows[1], persisted_at=21.0)
    assert path_signal_snapshot(
        [rows[0], late], position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path,
        model="gpt-5.4-nano", signal_at=20.0,
        policy=PATH_POLICY_BY_MARKET[(path, market)],
        buy_fill_identity=BUY_IDENTITY,
    )["vote_count"] == 1


def test_slow_provider_response_does_not_refresh_old_quote_vote():
    path, market = "EXIT_TRAILING_TP", "REGULAR"
    rows = _events(path, market)
    delayed = dict(rows[1], received_at=105.0, persisted_at=105.1)
    snapshot = path_signal_snapshot(
        [rows[0], delayed], position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=106.0, policy=PATH_POLICY_BY_MARKET[(path, market)],
        buy_fill_identity=BUY_IDENTITY,
    )
    assert snapshot["vote_count"] == 2
    assert snapshot["decision"] == "INSUFFICIENT"
    assert snapshot["latest_vote_age_sec"] > 40.0


def test_partial_buy_fill_changes_generation_and_replay_uses_signal_time():
    market, path = "REGULAR", "EXIT_TRAILING_TP"
    before = _receipt_stock()
    first_identity = buy_fill_identity_from_runtime(before)
    before["_entry_receipt_filled_by_order_no"]["BUY-1"] = 2
    before["_entry_receipt_executions_by_order_no"]["BUY-1"]["FILL-2"] = {
        "cumulative_qty": 2}
    second_identity = buy_fill_identity_from_runtime(before)
    assert first_identity == BUY_IDENTITY
    assert second_identity != first_identity
    rows = _events(path, market)
    rows[1]["buy_fill_identity"] = second_identity
    assert path_signal_snapshot(
        rows, position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=20.0, policy=PATH_POLICY_BY_MARKET[(path, market)],
        buy_fill_identity=second_identity,
    )["vote_count"] == 1
    legs = [*BUY_LEGS, {**BUY_LEGS[0], "at": "1970-01-01T00:00:09+00:00",
                         "execution_no": "FILL-2"}]
    assert buy_fill_identity_from_legs(legs) == second_identity
    assert buy_fill_identity_from_runtime({}) is None


def test_vote_store_rejects_tampered_raw_buy_fill_id(tmp_path):
    row = _events("EXIT_TRAILING_TP", "REGULAR")[0]
    row["buy_fill_legs"] = [{**BUY_LEGS[0], "execution_no": "OTHER"}]
    path = tmp_path / "votes.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="path_vote_store_contract_corrupt"):
        load_path_events_file(path, "record:7")


def test_due_gap_breaks_two_prior_valid_votes():
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    rows = _events(path, market)
    gap = {**rows[-1], "requested_at": 15.0, "received_at": 15.1,
           "persisted_at": 15.2, "source_generation": "gap:1",
           "status": "INSUFFICIENT", "verdict": None, "conviction": None,
           "provider_called": False}
    snapshot = path_signal_snapshot(
        [*rows, gap], position_key="record:7", market=market,
        session_key="2026-09-25", path_id=path, model="gpt-5.4-nano",
        signal_at=20.0, policy=PATH_POLICY_BY_MARKET[(path, market)],
        buy_fill_identity=BUY_IDENTITY,
    )
    assert snapshot["vote_count"] == 0
    assert snapshot["missing_cycle_count"] == 1
    assert snapshot["decision"] == "INSUFFICIENT"


def test_exit_vote_defer_blocks_concurrent_add_candidate():
    from src.engine import sniper_state_handlers as handlers

    stock = {"status": "HOLDING", "holding_path_exit_hold": {
        "path_id": "EXIT_TRAILING_TP", "signal_id": "crossing-1",
    }}
    assert (handlers._scale_in_exit_authority_block_reason(stock)
            == "holding_path_exit_veto_defer_active")
    stock.pop("holding_path_exit_hold")
    stock["holding_path_exit_candidate"] = {"path_id": "EXIT_SOFT_STOP"}
    assert (handlers._scale_in_exit_authority_block_reason(stock)
            == "holding_path_exit_candidate_active")


def test_due_source_gap_is_durable_and_breaks_prior_vote_sequence(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handlers

    now = datetime(2026, 9, 25, 9, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    monkeypatch.setattr(handlers, "DATA_DIR", tmp_path)
    monkeypatch.setattr(handlers.time, "time", lambda: now)
    monkeypatch.setattr(handlers, "scalp_trailing_market_type_at", lambda _: "REGULAR")
    stock = {"id": 7, "status": "HOLDING", "strategy": "SCALPING",
             "buy_price": 100, "curr_price": 90}
    assert handlers._persist_holding_path_review_gap(
        stock=stock, code="005930", reason="quote_or_tape_unusable",
        paths=("EXIT_TRAILING_TP", "ADD_REBOUND"),
    ) == "appended"
    rows = load_path_events_file(
        handlers.path_vote_store_path(tmp_path, "record:7"), "record:7",
    )
    assert len(rows) == 2
    assert {row["path_id"] for row in rows} == {"EXIT_TRAILING_TP", "ADD_REBOUND"}
    assert all(row["status"] == "INSUFFICIENT" and not row["provider_called"]
               for row in rows)


def test_durable_store_failure_freezes_insufficient_and_blocks_add(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    signal_at = datetime(2026, 9, 25, 9, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    monkeypatch.setattr(handlers, "scalp_trailing_market_type_at", lambda _: "REGULAR")
    stock = {"id": 7, "status": "HOLDING", "strategy": "SCALPING",
             "holding_path_vote_store_gap": "durable_vote_store_unavailable"}
    frozen = handlers._holding_path_signal_decision(
        stock, "005930", path_id="ADD_REBOUND", signal_id="add-1",
        signal_at=signal_at,
    )
    assert frozen["decision"] == "INSUFFICIENT"
    assert frozen["reason"] == "durable_vote_store_unavailable"
    stock.pop("holding_path_vote_store_gap")
    assert handlers._holding_path_signal_decision(
        stock, "005930", path_id="ADD_REBOUND", signal_id="add-1",
        signal_at=signal_at,
    ) == frozen
    stock["holding_path_vote_store_gap"] = "durable_vote_store_unavailable"
    assert handlers.execute_scale_in_order(
        stock=stock, code="005930", ws_data={},
        action={"add_type": "AVG_DOWN"}, admin_id="test",
    )["reason"] == "add_vote_store_unavailable"


def test_scalping_exit_receipt_does_not_publish_neutral_50_as_ai_score():
    from src.engine import sniper_state_handlers as handlers

    stock = {"strategy": "SCALPING", "holding_score_raw": 91.0,
             "holding_score_effective": 91.0}
    handlers._remember_exit_context(
        stock=stock, exit_rule="scalp_trailing_take_profit",
        reason="trailing", peak_profit=1.2, held_sec=20,
        current_ai_score=50.0,
    )
    assert stock["last_exit_current_ai_score"] is None
    assert stock["last_exit_ai_score_raw"] is None
    assert stock["last_exit_ai_score_effective"] is None
    assert stock["last_exit_ai_result_source"] == "retired_holding_score"


def test_bundle_rejects_cross_purpose_reason_and_duplicate_path():
    kwargs = dict(requested_paths=("EXIT_SOFT_STOP", "ADD_REBOUND"),
                  expected_snapshot_id="s", position_key="record:7",
                  buy_fill_identity=BUY_IDENTITY,
                  buy_fill_legs=BUY_LEGS,
                  market="REGULAR", session_key="2026-09-25",
                  model="gpt-5.4-nano", route="KRX", transport_epoch="1",
                  source_generation="item:1", requested_at=1.0, received_at=2.0)
    kwargs["quote_observed_at"] = 0.9
    response = {"input_snapshot_id": "s", "votes": [
        {"path_id": "EXIT_SOFT_STOP", "verdict": "PASS", "conviction": "FIRM",
         "reason_codes": ["add_rebound_tape_supportive"]},
        {"path_id": "ADD_REBOUND", "verdict": "PASS", "conviction": "FIRM",
         "reason_codes": ["add_rebound_tape_supportive"]},
    ]}
    rows = normalize_path_vote_bundle(response, **kwargs)
    assert [item["status"] for item in rows] == ["INSUFFICIENT", "VALID"]
    response["votes"][1]["path_id"] = "EXIT_SOFT_STOP"
    rows = normalize_path_vote_bundle(response, **kwargs)
    assert all(item["status"] == "INSUFFICIENT" for item in rows)


def test_bundle_rejects_reason_from_another_exit_path():
    rows = normalize_path_vote_bundle(
        {"input_snapshot_id": "s", "votes": [{
            "path_id": "EXIT_TRAILING_TP", "verdict": "VETO",
            "conviction": "FIRM", "reason_codes": ["exit_soft_tape_adverse"],
        }]},
        requested_paths=("EXIT_TRAILING_TP",), expected_snapshot_id="s",
        position_key="record:7", market="REGULAR", session_key="2026-09-25",
        buy_fill_identity=BUY_IDENTITY,
        buy_fill_legs=BUY_LEGS,
        quote_observed_at=0.9,
        model="gpt-5.4-nano", route="KRX", transport_epoch="1",
        source_generation="item:1", requested_at=1.0, received_at=2.0,
    )
    assert rows[0]["status"] == "INSUFFICIENT"


def test_bundle_rejects_quote_clock_older_than_three_seconds():
    rows = normalize_path_vote_bundle(
        {"input_snapshot_id": "s", "votes": [{
            "path_id": "EXIT_TRAILING_TP", "verdict": "VETO",
            "conviction": "FIRM", "reason_codes": ["exit_tp_bid_stable"],
        }]},
        requested_paths=("EXIT_TRAILING_TP",), expected_snapshot_id="s",
        position_key="record:7", market="REGULAR", session_key="2026-09-25",
        buy_fill_identity=BUY_IDENTITY, buy_fill_legs=BUY_LEGS,
        model="gpt-5.4-nano", route="KRX", transport_epoch="1",
        source_generation="item:1", quote_observed_at=1.0,
        requested_at=4.1, received_at=4.2,
    )
    assert rows[0]["status"] == "INSUFFICIENT"
    assert rows[0]["excluded_reason"] == "missing_or_invalid_provenance"


def test_model_declared_input_insufficient_never_counts_as_pass_or_veto():
    rows = normalize_path_vote_bundle(
        {"input_snapshot_id": "s", "votes": [{
            "path_id": "ADD_REBOUND", "verdict": "PASS",
            "conviction": "FIRM",
            "reason_codes": ["add_rebound_input_insufficient"],
        }]},
        requested_paths=("ADD_REBOUND",), expected_snapshot_id="s",
        position_key="record:7", market="REGULAR", session_key="2026-09-25",
        buy_fill_identity=BUY_IDENTITY, model="gpt-5.4-nano",
        buy_fill_legs=BUY_LEGS,
        quote_observed_at=0.9,
        route="KRX", transport_epoch="1", source_generation="item:1",
        requested_at=1.0, received_at=2.0,
    )
    assert rows[0]["status"] == "INSUFFICIENT"
    assert rows[0]["excluded_reason"] == "model_input_insufficient"
    rows[0].update(persisted_at=2.1, provider_called=True)
    assert path_signal_snapshot(
        rows, position_key="record:7", market="REGULAR",
        session_key="2026-09-25", path_id="ADD_REBOUND",
        model="gpt-5.4-nano", signal_at=20.0,
        policy=PATH_POLICY_BY_MARKET[("ADD_REBOUND", "REGULAR")],
        buy_fill_identity=BUY_IDENTITY,
    )["decision"] == "INSUFFICIENT"


def test_runtime_exit_veto_has_first_crossing_and_bounded_lifetime(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    start = datetime(2026, 9, 25, 9, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    clock = [start + 30.0]
    monkeypatch.setattr(handlers.time, "time", lambda: clock[0])
    monkeypatch.setattr(handlers, "scalp_trailing_market_type_at", lambda _: "REGULAR")
    monkeypatch.setattr(handlers, "_pre_submit_input_snapshot_has_usable_quote",
                        lambda _: True)
    monkeypatch.setattr(handlers, "ws_quote_source_receipt", lambda *_a, **_kw:
                        {"observed_epoch": clock[0]})
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda _: False)
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *_a, **_kw: None)
    rows = _events("EXIT_TRAILING_TP", "REGULAR", verdicts=("VETO", "VETO"))
    for row in rows:
        for field in ("requested_at", "received_at", "persisted_at"):
            row[field] += start
    monkeypatch.setattr(handlers, "load_path_events_file", lambda *_a: rows)
    stock = _receipt_stock(id=7, strategy="SCALPING", status="HOLDING",
             scalp_trailing_first_crossing={
                 "at_epoch": start + 20.0,
                 "threshold_key": "SCALP_TRAILING_LIMIT_WEAK"},
             holding_path_vote_ledger=rows)
    assert handlers._holding_path_exit_proceeds(
        stock, "005930", exit_rule="scalp_trailing_take_profit",
        profit_rate=1.0, ws_data={}, signal_at=clock[0],
    ) is False
    assert stock["holding_path_exit_hold"]["started_at"] == start + 20.0
    clock[0] = start + 66.0
    assert handlers._holding_path_exit_proceeds(
        stock, "005930", exit_rule="scalp_trailing_take_profit",
        profit_rate=1.0, ws_data={}, signal_at=clock[0],
    ) is True
    assert "holding_path_exit_hold" not in stock


def test_postclose_keeps_strict_population_and_null_economics():
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    rows = _events(path, market)
    policy = PATH_POLICY_BY_MARKET[(path, market)]
    trade = {"id": 7, "buy_fill_legs": BUY_LEGS,
             "exact_sell_fill_time": "1970-01-01T00:01:00+00:00", "timeline": [{
        "stage": "holding_path_signal_snapshot",
        "fields": {"path_id": path, "market": market,
                   "session_key": "2026-09-25", "position_key": "record:7",
                   "buy_fill_identity": BUY_IDENTITY,
                   "signal_id": "soft-1", "signal_at": 20.0,
                   "policy_sha256": input_snapshot_id(policy),
                   "decision": "PASS", "vote_count": 2},
    }]}
    report = summarize_holding_path_votes(
        [trade], load_events=lambda _: rows, model="gpt-5.4-nano",
    )
    cell = report["path_market"][f"{path}|{market}"]
    assert cell["strict_completed_position_count"] == 1
    assert cell["eligible_signal_count"] == 1
    assert cell["runtime_decisions"]["PASS"] == 1
    assert any(candidate["decision_counts"]["PASS"] == 1
               for candidate in cell["candidate_grid"])
    tp_grid = report["path_market"]["EXIT_TRAILING_TP|REGULAR"]["candidate_grid"]
    assert {"quorum_compound", "freshness_compound"}.issubset(
        {candidate["axis"] for candidate in tp_grid})
    assert all(candidate["policy"]["max_defer_sec"] <= 45
               for candidate in tp_grid)
    assert cell["cost_after_paired_ev_krw"] is None
    assert report["selected_policy"] is None
    assert report["allowed_runtime_apply"] is False


def test_postclose_reads_full_position_ledger_without_silent_truncation(tmp_path):
    rows = _events("EXIT_SOFT_STOP", "REGULAR", verdicts=("PASS",) * 193)
    path = tmp_path / "votes.jsonl"
    path.write_text("".join(json.dumps({**row, "provider_called": True}) + "\n"
                            for row in rows), encoding="utf-8")
    assert len(load_path_events_file(path, "record:7")) == 193


@pytest.mark.parametrize("bad_field,bad_value,reason", [
    ("signal_at", float("nan"), "signal_time_invalid"),
    ("vote_count", "broken", "signal_vote_count_invalid"),
])
def test_postclose_quarantines_bad_signal_receipt(bad_field, bad_value, reason):
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    fields = {"path_id": path, "market": market,
              "session_key": "2026-09-25", "position_key": "record:7",
              "buy_fill_identity": BUY_IDENTITY,
              "signal_id": "soft-1", "signal_at": 20.0,
              "policy_sha256": input_snapshot_id(PATH_POLICY_BY_MARKET[(path, market)]),
              "decision": "PASS", "vote_count": 2}
    fields[bad_field] = bad_value
    report = summarize_holding_path_votes(
        [{"id": 7, "buy_fill_legs": BUY_LEGS,
          "exact_sell_fill_time": "1970-01-01T00:01:00+00:00",
          "timeline": [{"stage": "holding_path_signal_snapshot",
                                  "fields": fields}]}],
        load_events=lambda _: _events(path, market), model="gpt-5.4-nano",
    )
    assert reason in report["excluded_by_position_id"]["7"]
    assert report["path_market"][f"{path}|{market}"]["eligible_signal_count"] == 0


def test_postclose_rejects_signal_after_exact_final_sell():
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    fields = {"path_id": path, "market": market,
              "session_key": "2026-09-25", "position_key": "record:7",
              "buy_fill_identity": BUY_IDENTITY,
              "signal_id": "soft-1", "signal_at": 20.0,
              "policy_sha256": input_snapshot_id(PATH_POLICY_BY_MARKET[(path, market)]),
              "decision": "PASS", "vote_count": 2}
    report = summarize_holding_path_votes(
        [{"id": 7, "buy_fill_legs": BUY_LEGS,
          "exact_sell_fill_time": "1970-01-01T00:00:15+00:00",
          "timeline": [{"stage": "holding_path_signal_snapshot", "fields": fields}]}],
        load_events=lambda _: _events(path, market), model="gpt-5.4-nano",
    )
    assert "signal_after_final_sell" in report["excluded_by_position_id"]["7"]
    assert report["path_market"][f"{path}|{market}"]["eligible_signal_count"] == 0


def test_postclose_retains_population_but_excludes_missing_sell_time_and_fill_id():
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    fields = {"path_id": path, "market": market,
              "session_key": "2026-09-25", "position_key": "record:7",
              "buy_fill_identity": BUY_IDENTITY,
              "signal_id": "soft-1", "signal_at": 20.0,
              "policy_sha256": input_snapshot_id(PATH_POLICY_BY_MARKET[(path, market)]),
              "decision": "PASS", "vote_count": 2}
    trade = {"id": 7, "buy_fill_legs": BUY_LEGS, "timeline": [{
        "stage": "holding_path_signal_snapshot", "fields": fields}]}
    first = summarize_holding_path_votes(
        [trade], load_events=lambda _: _events(path, market),
        model="gpt-5.4-nano")
    assert first["strict_population_count"] == 1
    assert "exact_sell_time_missing" in first["excluded_by_position_id"]["7"]
    trade["exact_sell_fill_time"] = "1970-01-01T00:01:00+00:00"
    fields["buy_fill_identity"] = "0" * 64
    second = summarize_holding_path_votes(
        [trade], load_events=lambda _: _events(path, market),
        model="gpt-5.4-nano")
    assert "buy_fill_identity_mismatch" in second["excluded_by_position_id"]["7"]
    assert second["path_market"][f"{path}|{market}"]["eligible_signal_count"] == 0


def test_frozen_replay_runtime_under_five_seconds():
    market, path = "REGULAR", "EXIT_SOFT_STOP"
    policy = PATH_POLICY_BY_MARKET[(path, market)]
    trades = []
    ledgers = {}
    for index in range(250):
        key = f"record:{index + 1}"
        ledgers[key] = _events(path, market, position_key=key)
        trades.append({"id": index + 1, "buy_fill_legs": BUY_LEGS,
                       "exact_sell_fill_time": "1970-01-01T00:01:00+00:00",
                       "timeline": [{
            "stage": "holding_path_signal_snapshot",
            "fields": {"path_id": path, "market": market,
                       "session_key": "2026-09-25", "position_key": key,
                       "buy_fill_identity": BUY_IDENTITY,
                       "signal_id": f"soft-{index}", "signal_at": 20.0,
                       "policy_sha256": input_snapshot_id(policy),
                       "decision": "PASS", "vote_count": 2},
        }]})
    started = time.perf_counter()
    report = summarize_holding_path_votes(
        trades, load_events=ledgers.__getitem__, model="gpt-5.4-nano",
    )
    elapsed = time.perf_counter() - started
    assert report["path_market"][f"{path}|{market}"]["eligible_signal_count"] == 250
    assert elapsed < 5.0


def test_frozen_three_market_all_path_replay_matrix():
    trades = []
    ledgers = {}
    expected_per_cell = 12
    for market in sorted(MARKETS):
        for path in sorted(PATH_IDS):
            policy = PATH_POLICY_BY_MARKET[(path, market)]
            for cohort_index in range(expected_per_cell):
                record_id = len(trades) + 1
                position_key = f"record:{record_id}"
                day = 21 + cohort_index % 3
                session_key = f"2026-09-{day:02d}"
                base_at = datetime(2026, 9, day, 9, tzinfo=ZoneInfo(
                    "Asia/Seoul"
                )).timestamp()
                ledgers[position_key] = _events(
                    path, market, position_key=position_key,
                    session_key=session_key, base_at=base_at,
                )
                legs = [{**BUY_LEGS[0], "at": datetime.fromtimestamp(
                    base_at - 10.0, ZoneInfo("Asia/Seoul")
                ).isoformat()}]
                trades.append({"id": record_id, "buy_fill_legs": legs,
                               "exact_sell_fill_time": datetime.fromtimestamp(
                                   base_at + 30.0, ZoneInfo("Asia/Seoul")
                               ).isoformat(), "timeline": [{
                    "stage": "holding_path_signal_snapshot",
                    "fields": {"path_id": path, "market": market,
                               "session_key": session_key,
                               "position_key": position_key,
                               "buy_fill_identity": BUY_IDENTITY,
                               "signal_id": f"signal-{record_id}",
                               "signal_at": base_at + 20.0,
                               "policy_sha256": input_snapshot_id(policy),
                               "decision": "PASS", "vote_count": 2},
                }]})
    report = summarize_holding_path_votes(
        trades, load_events=ledgers.__getitem__, model="gpt-5.4-nano",
    )
    assert report["strict_population_count"] == expected_per_cell * 15
    assert report["excluded_by_position_id"] == {}
    assert len(report["path_market"]) == 15
    assert all(cell["eligible_signal_count"] == expected_per_cell
               and cell["runtime_decisions"]["PASS"] == expected_per_cell
               and cell["cost_after_paired_ev_krw"] is None
               and cell["allowed_runtime_apply"] is False
               for cell in report["path_market"].values())


def test_final_sell_snapshot_preserves_tp_signal_and_buy_fill_generation():
    from src.engine import sniper_execution_receipts as receipts

    stock = _receipt_stock(
        last_exit_rule="scalp_trailing_take_profit",
        holding_path_latest_tp_signal={
            "position_key": "record:7",
            "buy_fill_identity": BUY_IDENTITY,
            "signal_id": "tp-first-7", "signal_at": 20.0,
            "policy_bundle_sha256": "b" * 64,
        },
    )
    frozen = receipts._normalized_receipt_snapshot(
        receipts._receipt_snapshot(stock, receipts._SELL_RECEIPT_SNAPSHOT_KEYS)
    )
    assert receipts._holding_path_terminal_lineage_fields(frozen, 7) == {
        "holding_path_terminal_signal_binding": "same_position_buy_generation",
        "holding_path_signal_id": "tp-first-7",
        "holding_path_signal_at": 20.0,
        "holding_path_policy_bundle_sha256": "b" * 64,
    }
    frozen["_entry_receipt_executions_by_order_no"]["BUY-1"]["FILL-1"][
        "cumulative_qty"] = 2
    assert receipts._holding_path_terminal_lineage_fields(frozen, 7) == {
        "holding_path_terminal_signal_binding": "source_gap_generation_mismatch",
    }
