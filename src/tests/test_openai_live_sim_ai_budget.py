import json
import os
import time

import pytest

from src.engine import ai_engine_openai as openai_module
from src.engine.ai_engine_openai import GPTSniperEngine
from src.engine.sniper_config import CONF


class _RulesProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


def _api_keys() -> list[str]:
    raw = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or ""
    keys = [part.strip() for part in raw.split(",") if part.strip()]
    keys.extend(v for k, v in sorted(CONF.items()) if str(k).startswith("OPENAI_API_KEY") and v)
    return keys


def _assert_entry_action_score_consistent(row: dict) -> None:
    action = str(row.get("action") or "")
    score = int(float(row.get("score", 0) or 0))
    if action == "DROP":
        assert score <= 39
    elif action == "WAIT":
        assert 40 <= score <= 69
    elif action == "BUY":
        assert score >= 70
    else:
        pytest.fail(f"unexpected action: {action!r}")


def _entry_action_from_suitability_score(score: int) -> str:
    if score <= 39:
        return "DROP"
    if score <= 69:
        return "WAIT"
    return "BUY"


def _float_or_none(value):
    try:
        return float(value)
    except Exception:
        return None


_BLIND_REPLAY_FEATURE_KEYS = (
    "source_stage",
    "stage",
    "event_time",
    "time_bucket",
    "risk_context_bucket",
    "market_regime",
    "market_regime_continuous_bucket",
    "market_regime_continuous_label",
    "market_regime_continuous_score",
    "market_regime_source_quality",
    "stale_bucket",
    "price_resolution_bucket",
    "liquidity_bucket",
    "overbought_bucket",
    "latency_state",
    "latency_reason",
    "context_age_ms",
    "quote_age_ms",
    "best_bid",
    "best_ask",
    "resolved_order_price",
    "would_limit_fill",
    "source_quality_block_reason",
    "pre_submit_quote_refresh_applied",
    "pre_submit_quote_refresh_enabled",
    "pre_submit_quote_refresh_quote_age_ms",
    "pre_submit_quote_refresh_reason",
    "pre_submit_ws_snapshot_refresh_age_ms",
    "pre_submit_ws_snapshot_refresh_applied",
    "pre_submit_ws_snapshot_refresh_reason",
    "entry_adm_bucket_lookup_status",
    "entry_adm_bucket_sample_count",
    "scalp_feature_packet_version",
    "ai_input_schema",
    "ai_input_contract_mode",
    "ai_input_source_quality_status",
    "ai_input_source_quality_reason",
    "entry_liquidity_score",
    "entry_liquidity_status",
    "fillability_score",
    "would_fill_now",
    "top1_bid_notional",
    "top1_ask_notional",
    "top3_bid_notional",
    "top3_ask_notional",
    "quote_depth_present",
    "quote_fresh_for_entry",
    "order_flow_pressure_score",
    "entry_order_flow_status",
    "order_flow_pressure_source",
    "entry_momentum_score",
    "entry_momentum_status",
    "entry_context_quality",
    "entry_context_missing_features",
    "latest_strength",
    "buy_pressure_10t",
    "net_aggressive_delta_10t",
    "same_price_buy_absorption",
    "tick_acceleration_ratio",
    "tick_acceleration_ratio_raw",
    "tick_accel_effective_recent_5tick_seconds",
    "recent_5tick_seconds",
    "prev_5tick_seconds",
    "tick_sample_count",
    "tick_window_sample_count",
    "tick_window_span_sec",
    "tick_aggressor_pressure_usable",
    "tick_aggressor_trusted_count",
    "tick_aggressor_price_heuristic_count",
    "tick_context_quality",
    "tick_context_stale",
    "tick_accel_source",
    "quote_age_source",
    "curr_vs_micro_vwap_bp",
    "curr_vs_ma5_bp",
    "micro_vwap_available",
    "ma5_available",
    "minute_candle_context_quality",
    "minute_candle_window_fresh",
    "micro_vwap_value",
    "ma5_value",
    "top1_depth_ratio",
    "top3_depth_ratio",
    "orderbook_total_ratio",
    "microprice_edge_bp",
    "ask_depth_ratio",
    "net_ask_depth",
    "spread_bp",
    "volume_ratio_pct",
    "distance_from_day_high_pct",
    "intraday_range_pct",
    "large_sell_print_detected",
    "large_buy_print_detected",
    "microstructure_reaction_context_status",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_tick_trade_value_recent_sum",
    "microstructure_reaction_tick_trade_value_prev_sum",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
)


def _blind_replay_feature_packet(source_row: dict) -> dict:
    packet = {}
    for key in _BLIND_REPLAY_FEATURE_KEYS:
        value = (source_row or {}).get(key)
        if value not in (None, "", [], {}):
            packet[key] = value
    return packet


def _blind_replay_payload(sample: dict, index: int) -> dict:
    return {
        "case_id": f"blind_replay_{index:02d}",
        "authority": "forensics_only_no_runtime_change",
        "stock_code": sample.get("stock_code"),
        "stock_name": sample.get("stock_name"),
        "entry_context": dict(sample.get("blind_features") or {}),
        "withheld_field_policy": "Scoring labels and prior model outputs are intentionally unavailable.",
        "allowed_actions": ["BUY", "WAIT", "DROP"],
    }


def test_live_openai_compare_gpt5_nano_and_gpt54_nano_sample(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=160,
        ),
    )
    engine = GPTSniperEngine(keys[:1], announce_startup=False)
    sample_prompt = (
        "Return exactly one valid minified JSON object. Keys: action, score, reason. "
        "score is entry suitability from 0 to 100. "
        "Use DROP only when score is 0-39, WAIT only when score is 40-69, BUY only when score is 70-100. "
        "reason max 12 Korean words."
    )
    sample_input = json.dumps(
        {
            "price_change_pct": 2.1,
            "buy_pressure": 72,
            "tick_accel": 1.08,
            "quote_age_ms": 420,
            "vwap_bp": 7,
            "stale_quote": False,
            "allowed_actions": ["BUY", "WAIT", "DROP"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    rows = []
    for model_name in ("gpt-5-nano", "gpt-5.4-nano"):
        started = time.perf_counter()
        result = engine._call_openai_safe(
            sample_prompt,
            sample_input,
            require_json=True,
            context_name=f"LIVE_MODEL_COMPARE:{model_name}",
            model_override=model_name,
            endpoint_name="analyze_target",
            symbol="LIVE_TEST",
            cache_key=f"live-model-compare:{model_name}",
        )
        result = engine._merge_last_transport_meta(result)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        score = int(float(result.get("score", 0) or 0))
        row = {
            "model": model_name,
            "reasoning_effort": engine._resolve_openai_reasoning_effort(model_name=model_name),
            "elapsed_ms": elapsed_ms,
            "model_action": str(result.get("action") or ""),
            "action": _entry_action_from_suitability_score(score),
            "score": score,
            "reason": str(result.get("reason") or "")[:160],
            "input_tokens": result.get("openai_input_tokens"),
            "output_tokens": result.get("openai_output_tokens"),
            "total_tokens": result.get("openai_total_tokens"),
            "transport": result.get("openai_transport_mode"),
        }
        rows.append(row)

    print("\n| model | effort | elapsed_ms | model_action | calibrated_action | score | tokens | reason |")
    print("| --- | --- | ---: | --- | --- | ---: | ---: | --- |")
    for row in rows:
        print(
            "| {model} | {reasoning_effort} | {elapsed_ms} | {model_action} | {action} | {score} | {total_tokens} | {reason} |".format(
                **row
            )
        )

    assert {row["model"] for row in rows} == {"gpt-5-nano", "gpt-5.4-nano"}
    assert rows[0]["reasoning_effort"] == "minimal"
    assert rows[1]["reasoning_effort"] == "none"
    for row in rows:
        assert row["model_action"] in {"BUY", "WAIT", "DROP"}
        assert row["action"] in {"BUY", "WAIT", "DROP"}
        assert 0 <= row["score"] <= 100
        _assert_entry_action_score_consistent(row)
        assert row["reason"]
        assert row["elapsed_ms"] > 0


def test_live_openai_compare_models_on_bad_entry_or_stop_loss_performance(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    report_path = "data/report/report_2026-07-10.json"
    ev_path = "data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-10.json"
    with open(report_path, encoding="utf-8") as fp:
        daily_report = json.load(fp)
    with open(ev_path, encoding="utf-8") as fp:
        threshold_ev = json.load(fp)

    worst_actual = min(
        daily_report["performance"]["top_losers"],
        key=lambda row: float(row.get("profit_rate", 0) or 0),
    )
    sim_examples = threshold_ev["scalp_simulator"]["post_sell_join"]["examples"]
    worst_sim = min(sim_examples, key=lambda row: float(row.get("profit_rate", 0) or 0))
    samples = [
        {
            "case_id": "actual_top_loser_bad_entry_forensics",
            "source": report_path,
            "authority": "forensics_only_no_runtime_change",
            "stock_code": worst_actual.get("code"),
            "stock_name": worst_actual.get("name"),
            "strategy": worst_actual.get("strategy"),
            "buy_time": worst_actual.get("buy_time"),
            "sell_time": worst_actual.get("sell_time"),
            "buy_price": worst_actual.get("buy_price"),
            "sell_price": worst_actual.get("sell_price"),
            "profit_rate": worst_actual.get("profit_rate"),
            "realized_pnl_krw": worst_actual.get("realized_pnl_krw"),
            "known_issue": "actual completed scalp loss; evaluate whether entry should have been WAIT/DROP",
        },
        {
            "case_id": "sim_stop_or_entry_forensics",
            "source": ev_path,
            "authority": "sim_forensics_only_no_runtime_change",
            "stock_code": worst_sim.get("stock_code"),
            "stock_name": worst_sim.get("stock_name"),
            "sim_record_id": worst_sim.get("sim_record_id"),
            "profit_rate": worst_sim.get("profit_rate"),
            "outcome": worst_sim.get("outcome"),
            "mfe_10m_pct": worst_sim.get("mfe_10m_pct"),
            "mae_10m_pct": worst_sim.get("mae_10m_pct"),
            "close_10m_pct": worst_sim.get("close_10m_pct"),
            "known_issue": "large adverse excursion after entry; classify bad entry versus stop-loss/timing issue",
        },
    ]

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=192,
        ),
    )
    engine = GPTSniperEngine(keys[:1], announce_startup=False)
    prompt = (
        "You are evaluating historical KORStockScan scalping forensics only. "
        "Return exactly one valid minified JSON object with keys action, score, issue, reason. "
        "action must be BUY, WAIT, or DROP as if this candidate appeared again with the same risk facts. "
        "score is entry suitability from 0 to 100. "
        "Use DROP only when score is 0-39, WAIT only when score is 40-69, BUY only when score is 70-100. "
        "issue must be bad_entry, stop_loss_timing, insufficient_context, or acceptable_risk. "
        "reason must be Korean and at most 10 words. "
        "Do not recommend broker, threshold, bot, provider, or cap changes."
    )

    rows = []
    for sample in samples:
        for model_name in ("gpt-5-nano", "gpt-5.4-nano"):
            started = time.perf_counter()
            result = engine._call_openai_safe(
                prompt,
                json.dumps(sample, ensure_ascii=False, separators=(",", ":")),
                require_json=True,
                context_name=f"LIVE_BAD_ENTRY_STOP_COMPARE:{sample['case_id']}:{model_name}",
                model_override=model_name,
                endpoint_name="analyze_target",
                symbol=str(sample.get("stock_code") or "LIVE_TEST"),
                cache_key=f"bad-entry-stop-compare:{sample['case_id']}:{model_name}",
            )
            result = engine._merge_last_transport_meta(result)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            row = {
                "case_id": sample["case_id"],
                "stock_name": sample.get("stock_name"),
                "profit_rate": sample.get("profit_rate"),
                "model": model_name,
                "effort": engine._resolve_openai_reasoning_effort(model_name=model_name),
                "elapsed_ms": elapsed_ms,
                "model_action": str(result.get("action") or ""),
                "score": int(float(result.get("score", 0) or 0)),
                "issue": str(result.get("issue") or ""),
                "reason": str(result.get("reason") or "")[:160],
                "tokens": result.get("openai_total_tokens"),
            }
            row["action"] = _entry_action_from_suitability_score(row["score"])
            rows.append(row)

    print(
        "\n| case | stock | pnl_pct | model | effort | elapsed_ms | model_action | "
        "calibrated_action | score | issue | tokens | reason |"
    )
    print("| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |")
    for row in rows:
        print(
            "| {case_id} | {stock_name} | {profit_rate} | {model} | {effort} | {elapsed_ms} | "
            "{model_action} | {action} | {score} | {issue} | {tokens} | {reason} |".format(**row)
        )

    assert {row["case_id"] for row in rows} == {sample["case_id"] for sample in samples}
    for row in rows:
        assert row["model"] in {"gpt-5-nano", "gpt-5.4-nano"}
        assert row["model_action"] in {"BUY", "WAIT", "DROP"}
        assert row["action"] in {"BUY", "WAIT", "DROP"}
        assert 0 <= row["score"] <= 100
        _assert_entry_action_score_consistent(row)
        assert row["issue"] in {"bad_entry", "stop_loss_timing", "insufficient_context", "acceptable_risk"}
        assert row["reason"]
        assert row["elapsed_ms"] > 0


def test_live_openai_compare_models_on_loss_after_entry_decision(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    entry_matrix_path = "data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-09.json"
    realized_report_path = "data/report/report_2026-07-10.json"
    with open(entry_matrix_path, encoding="utf-8") as fp:
        entry_matrix = json.load(fp)
    with open(realized_report_path, encoding="utf-8") as fp:
        realized_report = json.load(fp)

    entry_decision = next(
        row
        for row in entry_matrix["rows"]
        if row.get("record_id") == "16283"
        and row.get("stock_code") == "024060"
        and row.get("stage") == "scalp_entry_action_decision_snapshot"
        and row.get("chosen_action") == "BUY_DEFENSIVE"
        and row.get("outcome_joined") is True
        and float(row.get("profit_rate", 0) or 0) < 0
    )
    submitted_order = next(
        row
        for row in entry_matrix["rows"]
        if row.get("record_id") == entry_decision["record_id"]
        and row.get("stock_code") == entry_decision["stock_code"]
        and row.get("stage") == "order_bundle_submitted"
        and row.get("actual_order_submitted") is True
        and row.get("broker_order_submitted") is True
    )
    realized_trade = next(
        row
        for row in realized_report["performance"]["top_losers"]
        if row.get("code") == entry_decision["stock_code"] and float(row.get("profit_rate", 0) or 0) < 0
    )

    sample = {
        "case_id": "loss_after_entry_decision_forensics",
        "source": entry_matrix_path,
        "realized_report_source": realized_report_path,
        "authority": "forensics_only_no_runtime_change",
        "record_id": entry_decision.get("record_id"),
        "stock_code": entry_decision.get("stock_code"),
        "stock_name": entry_decision.get("stock_name"),
        "entry_event_time": entry_decision.get("event_time"),
        "source_stage": entry_decision.get("source_stage"),
        "entry_decision_stage": entry_decision.get("stage"),
        "entry_chosen_action": entry_decision.get("chosen_action"),
        "entry_eligible_actions": entry_decision.get("eligible_actions"),
        "entry_rejected_actions": entry_decision.get("rejected_actions"),
        "entry_ai_score": entry_decision.get("ai_score"),
        "entry_matrix_profit_rate": entry_decision.get("profit_rate"),
        "entry_outcome_joined": entry_decision.get("outcome_joined"),
        "source_quality_block_reason": entry_decision.get("source_quality_block_reason"),
        "submit_event_time": submitted_order.get("event_time"),
        "actual_order_submitted": submitted_order.get("actual_order_submitted"),
        "broker_order_submitted": submitted_order.get("broker_order_submitted"),
        "realized_profit_rate": realized_trade.get("profit_rate"),
        "realized_pnl_krw": realized_trade.get("realized_pnl_krw"),
        "buy_time": realized_trade.get("buy_time"),
        "sell_time": realized_trade.get("sell_time"),
        "buy_price": realized_trade.get("buy_price"),
        "sell_price": realized_trade.get("sell_price"),
        "known_issue": "entry decision existed and a real submitted trade finished at a loss",
    }

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=192,
        ),
    )
    engine = GPTSniperEngine(keys[:1], announce_startup=False)
    prompt = (
        "You are evaluating one historical KORStockScan entry decision that later lost money. "
        "Return exactly one valid minified JSON object with keys action, score, issue, reason. "
        "action must be BUY, WAIT, or DROP as if this candidate appeared again with the same facts. "
        "score is entry suitability from 0 to 100. "
        "Use DROP only when score is 0-39, WAIT only when score is 40-69, BUY only when score is 70-100. "
        "issue must be bad_entry, stop_loss_timing, insufficient_context, or acceptable_risk. "
        "reason must be Korean and at most 10 words. "
        "Do not recommend broker, threshold, bot, provider, or cap changes."
    )

    rows = []
    for model_name in ("gpt-5-nano", "gpt-5.4-nano"):
        started = time.perf_counter()
        result = engine._call_openai_safe(
            prompt,
            json.dumps(sample, ensure_ascii=False, separators=(",", ":")),
            require_json=True,
            context_name=f"LIVE_ENTRY_DECISION_LOSS_COMPARE:{model_name}",
            model_override=model_name,
            endpoint_name="analyze_target",
            symbol=str(sample["stock_code"]),
            cache_key=f"entry-decision-loss-compare:{sample['record_id']}:{model_name}",
        )
        result = engine._merge_last_transport_meta(result)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        rows.append(
            {
                "case_id": sample["case_id"],
                "record_id": sample["record_id"],
                "stock_name": sample["stock_name"],
                "entry_action": sample["entry_chosen_action"],
                "realized_profit_rate": sample["realized_profit_rate"],
                "model": model_name,
                "effort": engine._resolve_openai_reasoning_effort(model_name=model_name),
                "elapsed_ms": elapsed_ms,
                "model_action": str(result.get("action") or ""),
                "score": int(float(result.get("score", 0) or 0)),
                "issue": str(result.get("issue") or ""),
                "reason": str(result.get("reason") or "")[:160],
                "tokens": result.get("openai_total_tokens"),
            }
        )
        rows[-1]["action"] = _entry_action_from_suitability_score(rows[-1]["score"])

    print(
        "\n| case | record | stock | entry_action | realized_pnl_pct | model | effort | elapsed_ms | "
        "model_action | calibrated_action | score | issue | tokens | reason |"
    )
    print("| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |")
    for row in rows:
        print(
            "| {case_id} | {record_id} | {stock_name} | {entry_action} | {realized_profit_rate} | "
            "{model} | {effort} | {elapsed_ms} | {model_action} | {action} | {score} | {issue} | {tokens} | {reason} |".format(
                **row
            )
        )

    assert entry_decision["chosen_action"] == "BUY_DEFENSIVE"
    assert float(entry_decision["profit_rate"]) < 0
    assert submitted_order["actual_order_submitted"] is True
    assert float(realized_trade["profit_rate"]) < 0
    assert {row["model"] for row in rows} == {"gpt-5-nano", "gpt-5.4-nano"}
    for row in rows:
        assert row["model_action"] in {"BUY", "WAIT", "DROP"}
        assert row["action"] in {"BUY", "WAIT", "DROP"}
        assert 0 <= row["score"] <= 100
        _assert_entry_action_score_consistent(row)
        assert row["issue"] in {"bad_entry", "stop_loss_timing", "insufficient_context", "acceptable_risk"}
        assert row["reason"]
        assert row["elapsed_ms"] > 0


def test_live_openai_blind_replay_action_score_accuracy_on_realized_entries(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    entry_matrix_path = "data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-07-09.json"
    realized_report_path = "data/report/report_2026-07-10.json"
    with open(entry_matrix_path, encoding="utf-8") as fp:
        entry_matrix = json.load(fp)
    with open(realized_report_path, encoding="utf-8") as fp:
        realized_report = json.load(fp)

    submitted_keys = {
        (str(row.get("record_id")), str(row.get("stock_code")))
        for row in entry_matrix["rows"]
        if row.get("stage") == "order_bundle_submitted"
        and row.get("actual_order_submitted") is True
        and row.get("broker_order_submitted") is True
    }
    submitted_rows_by_stock = {}
    for row in entry_matrix["rows"]:
        if (
            row.get("stage") == "order_bundle_submitted"
            and row.get("actual_order_submitted") is True
            and row.get("broker_order_submitted") is True
        ):
            submitted_rows_by_stock.setdefault(str(row.get("stock_code") or ""), row)
    submitted_stock_codes = {stock_code for _, stock_code in submitted_keys if stock_code}
    realized_entries = []
    for row in entry_matrix["rows"]:
        profit_rate = _float_or_none(row.get("profit_rate"))
        key = (str(row.get("record_id")), str(row.get("stock_code")))
        if (
            row.get("stage") == "scalp_entry_action_decision_snapshot"
            and row.get("outcome_joined") is True
            and row.get("chosen_action") in {"BUY_NOW", "BUY_DEFENSIVE"}
            and key in submitted_keys
            and profit_rate is not None
            and profit_rate != 0
        ):
            realized_entries.append((profit_rate, row))

    cases_per_side = int(os.getenv("KORSTOCKSCAN_OPENAI_LIVE_ACCURACY_CASES_PER_SIDE", "5"))
    entry_profit_cases = [
        {
            "case_id": f"profit:entry:{row.get('record_id')}:{row.get('stock_code')}",
            "source": entry_matrix_path,
            "authority": "forensics_only_no_runtime_change",
            "record_id": row.get("record_id"),
            "stock_code": row.get("stock_code"),
            "stock_name": row.get("stock_name"),
            "entry_event_time": row.get("event_time"),
            "entry_chosen_action": row.get("chosen_action"),
            "entry_eligible_actions": row.get("eligible_actions"),
            "entry_rejected_actions": row.get("rejected_actions"),
            "entry_ai_score": row.get("ai_score"),
            "blind_features": _blind_replay_feature_packet(row),
            "realized_profit_rate": row.get("profit_rate"),
            "known_outcome_label": "profit",
            "known_issue": "real submitted entry joined with completed realized profit outcome",
        }
        for _, row in sorted(
            (x for x in realized_entries if x[0] > 0),
            key=lambda item: item[0],
            reverse=True,
        )[:cases_per_side]
    ]
    entry_loss_cases = [
        {
            "case_id": f"loss:entry:{row.get('record_id')}:{row.get('stock_code')}",
            "source": entry_matrix_path,
            "authority": "forensics_only_no_runtime_change",
            "record_id": row.get("record_id"),
            "stock_code": row.get("stock_code"),
            "stock_name": row.get("stock_name"),
            "entry_event_time": row.get("event_time"),
            "entry_chosen_action": row.get("chosen_action"),
            "entry_eligible_actions": row.get("eligible_actions"),
            "entry_rejected_actions": row.get("rejected_actions"),
            "entry_ai_score": row.get("ai_score"),
            "blind_features": _blind_replay_feature_packet(row),
            "realized_profit_rate": row.get("profit_rate"),
            "known_outcome_label": "loss",
            "known_issue": "real submitted entry joined with completed realized loss outcome",
        }
        for _, row in sorted(
            (x for x in realized_entries if x[0] < 0),
            key=lambda item: item[0],
        )[:cases_per_side]
    ]
    report_cases = []
    for source_key, outcome_label, reverse_sort in (
        ("top_winners", "profit", True),
        ("top_losers", "loss", False),
    ):
        rows = []
        for row in realized_report.get("performance", {}).get(source_key, []) or []:
            profit_rate = _float_or_none(row.get("profit_rate"))
            stock_code = str(row.get("code") or row.get("stock_code") or "")
            if not stock_code or stock_code not in submitted_stock_codes or profit_rate is None:
                continue
            if outcome_label == "profit" and profit_rate <= 0:
                continue
            if outcome_label == "loss" and profit_rate >= 0:
                continue
            rows.append((profit_rate, row))
        for _, row in sorted(rows, key=lambda item: item[0], reverse=reverse_sort)[:cases_per_side]:
            stock_code = str(row.get("code") or row.get("stock_code") or "")
            submitted_row = submitted_rows_by_stock.get(stock_code) or {}
            report_cases.append(
                {
                    "case_id": f"{outcome_label}:report:{stock_code}:{row.get('profit_rate')}",
                    "source": realized_report_path,
                    "authority": "forensics_only_no_runtime_change",
                    "record_id": None,
                    "stock_code": stock_code,
                    "stock_name": row.get("name") or row.get("stock_name"),
                    "entry_event_time": row.get("buy_time"),
                    "entry_chosen_action": "realized_report_submitted_stock",
                    "entry_eligible_actions": None,
                    "entry_rejected_actions": None,
                    "entry_ai_score": None,
                    "blind_features": _blind_replay_feature_packet(submitted_row),
                    "realized_profit_rate": row.get("profit_rate"),
                    "known_outcome_label": outcome_label,
                    "known_issue": "realized report outcome for a stock with submitted order evidence",
                }
            )

    def _take_unique_by_side(primary, fallback, outcome_label):
        selected = []
        seen = set()
        for sample in [*primary, *fallback]:
            if sample["known_outcome_label"] != outcome_label:
                continue
            key = (sample.get("stock_code"), sample.get("record_id"), sample.get("realized_profit_rate"))
            if key in seen:
                continue
            seen.add(key)
            selected.append(sample)
            if len(selected) >= cases_per_side:
                break
        return selected

    samples = [
        *_take_unique_by_side(entry_profit_cases, report_cases, "profit"),
        *_take_unique_by_side(entry_loss_cases, report_cases, "loss"),
    ]

    assert any(sample["known_outcome_label"] == "profit" for sample in samples), "expected at least one profit case"
    assert any(sample["known_outcome_label"] == "loss" for sample in samples), "expected at least one loss case"

    model_name = os.getenv("KORSTOCKSCAN_OPENAI_LIVE_ACCURACY_MODEL", "gpt-5-nano")
    reasoning_effort = os.getenv("KORSTOCKSCAN_OPENAI_LIVE_ACCURACY_EFFORT", "minimal")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            OPENAI_TRANSPORT_MODE="http",
            OPENAI_REASONING_EFFORT=reasoning_effort,
            OPENAI_ANALYZE_TARGET_TIMEOUT_MS=10000,
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512,
        ),
    )
    engine = GPTSniperEngine(keys[:1], announce_startup=False)
    prompt = (
        "You are evaluating a KORStockScan entry candidate using only pre-entry/source fields. "
        "The realized outcome, realized PnL, prior model action, and prior model score are withheld. "
        "Return exactly one valid minified JSON object with keys action, score, issue, confidence, missing_features, reason. "
        "action must be BUY, WAIT, or DROP as if this candidate appeared now with the same observable facts. "
        "score is entry suitability from 0 to 100. "
        "Use DROP only when score is 0-39, WAIT only when score is 40-69, BUY only when score is 70-100. "
        "issue must be bad_entry, stop_loss_timing, insufficient_context, or acceptable_risk. "
        "confidence must be an integer from 0 to 100. "
        "missing_features must be an array of up to 4 short English feature names that would materially improve judgment. "
        "missing_features must only name pre-entry observable market/source fields, such as order_flow_pressure, "
        "quote_depth, tick_acceleration, micro_vwap, trade_value, liquidity_status, or risk_regime. "
        "Never request withheld scoring labels, realized PnL, realized outcome, prior model action, or prior model score. "
        "reason must be Korean and at most 6 words. "
        "Do not recommend broker, threshold, bot, provider, or cap changes."
    )

    rows = []
    for sample in samples:
        started = time.perf_counter()
        result = engine._call_openai_safe(
            prompt,
            json.dumps(_blind_replay_payload(sample, len(rows) + 1), ensure_ascii=False, separators=(",", ":")),
            require_json=True,
            context_name=f"LIVE_BLIND_REPLAY_ACTION_SCORE_ACCURACY:{model_name}:{reasoning_effort}:{sample['case_id']}",
            model_override=model_name,
            endpoint_name="analyze_target",
            symbol=str(sample.get("stock_code") or "LIVE_TEST"),
            cache_key=f"blind-replay-action-score-accuracy:{model_name}:{reasoning_effort}:{sample['case_id']}",
        )
        result = engine._merge_last_transport_meta(result)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        score = int(float(result.get("score", 0) or 0))
        model_action = str(result.get("action") or "")
        calibrated_action = _entry_action_from_suitability_score(score)
        expected_signal = "BUY" if sample["known_outcome_label"] == "profit" else "AVOID"
        model_signal = "BUY" if model_action == "BUY" else "AVOID"
        score_signal = "BUY" if calibrated_action == "BUY" else "AVOID"
        missing_features = result.get("missing_features")
        missing_features_display = ",".join(str(item) for item in missing_features or [])[:180] if isinstance(
            missing_features,
            list,
        ) else str(missing_features or "")[:180]
        rows.append(
            {
                "case_id": sample["case_id"],
                "stock_name": sample["stock_name"],
                "outcome": sample["known_outcome_label"],
                "profit_rate": sample["realized_profit_rate"],
                "model": model_name,
                "effort": engine._resolve_openai_reasoning_effort(model_name=model_name),
                "elapsed_ms": elapsed_ms,
                "model_action": model_action,
                "calibrated_action": calibrated_action,
                "score": score,
                "expected_signal": expected_signal,
                "action_correct": model_signal == expected_signal,
                "score_correct": score_signal == expected_signal,
                "mismatch": model_action != calibrated_action,
                "issue": str(result.get("issue") or ""),
                "confidence": result.get("confidence"),
                "missing_features": missing_features,
                "missing_features_display": missing_features_display,
                "tokens": result.get("openai_total_tokens"),
                "reason": str(result.get("reason") or "")[:160],
            }
        )

    total = len(rows)
    action_correct = sum(1 for row in rows if row["action_correct"])
    score_correct = sum(1 for row in rows if row["score_correct"])
    mismatch_count = sum(1 for row in rows if row["mismatch"])
    profit_buy = sum(1 for row in rows if row["outcome"] == "profit" and row["model_action"] == "BUY")
    loss_buy = sum(1 for row in rows if row["outcome"] == "loss" and row["model_action"] == "BUY")

    print(
        "\n| outcome | stock | pnl_pct | model | effort | elapsed_ms | model_action | "
        "calibrated_action | score | expected | action_ok | score_ok | mismatch | issue | confidence | tokens | missing_features | reason |"
    )
    print(
        "| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |"
    )
    for row in rows:
        print(
            "| {outcome} | {stock_name} | {profit_rate} | {model} | {effort} | {elapsed_ms} | "
            "{model_action} | {calibrated_action} | {score} | {expected_signal} | {action_correct} | "
            "{score_correct} | {mismatch} | {issue} | {confidence} | {tokens} | {missing_features_display} | {reason} |".format(
                **row
            )
        )
    print(
        "\nsummary: total={total}, action_correct={action_correct}, score_correct={score_correct}, "
        "mismatch_count={mismatch_count}, profit_buy={profit_buy}, loss_buy={loss_buy}".format(
            total=total,
            action_correct=action_correct,
            score_correct=score_correct,
            mismatch_count=mismatch_count,
            profit_buy=profit_buy,
            loss_buy=loss_buy,
        )
    )

    assert total == len(samples)
    assert {row["model"] for row in rows} == {model_name}
    assert {row["effort"] for row in rows} == {engine._resolve_openai_reasoning_effort(model_name=model_name)}
    for row in rows:
        assert row["model_action"] in {"BUY", "WAIT", "DROP"}
        assert row["calibrated_action"] in {"BUY", "WAIT", "DROP"}
        assert 0 <= row["score"] <= 100
        _assert_entry_action_score_consistent({"action": row["calibrated_action"], "score": row["score"]})
        assert row["issue"] in {"bad_entry", "stop_loss_timing", "insufficient_context", "acceptable_risk"}
        if row["confidence"] is not None:
            assert 0 <= int(float(row["confidence"])) <= 100
        if row["missing_features"] is not None:
            assert isinstance(row["missing_features"], list)
            missing_text = ",".join(str(item).lower() for item in row["missing_features"])
            for forbidden in ("realized", "outcome", "prior_model", "pnl", "profit_rate", "known"):
                assert forbidden not in missing_text
        assert row["reason"]
        assert row["elapsed_ms"] > 0


def test_live_openai_holding_schema_for_sim_ai_budget(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            GPT_FAST_MODEL=os.getenv("KORSTOCKSCAN_OPENAI_LIVE_TEST_MODEL", "gpt-5-nano"),
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_RESPONSES_WS_POOL_SIZE=1,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=10000,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False,
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=1024,
        ),
    )
    engine = GPTSniperEngine(keys, announce_startup=False)
    result = engine.analyze_target(
        "SIM_BUDGET_LIVE_TEST",
        {
            "curr": 10000,
            "fluctuation": 0.45,
            "v_pw": 121.0,
            "buy_ratio": 58.0,
            "ask_tot": 80000,
            "bid_tot": 95000,
            "orderbook": {
                "asks": [{"price": 10010, "volume": 3000}, {"price": 10020, "volume": 4500}],
                "bids": [{"price": 10000, "volume": 3800}, {"price": 9990, "volume": 4200}],
            },
        },
        [
            {"time": "10:00:00", "price": 10000, "volume": 120, "dir": "BUY", "strength": 121.0},
            {"time": "09:59:59", "price": 9990, "volume": 80, "dir": "SELL", "strength": 119.0},
            {"time": "09:59:58", "price": 10000, "volume": 150, "dir": "BUY", "strength": 120.5},
        ],
        [
            {"체결시간": "09:58:00", "시가": 9980, "현재가": 9990, "고가": 10010, "저가": 9970, "거래량": 1200},
            {"체결시간": "09:59:00", "시가": 9990, "현재가": 10000, "고가": 10020, "저가": 9980, "거래량": 1400},
        ],
        strategy="SCALPING",
        cache_profile="holding",
        prompt_profile="holding",
    )
    pool = getattr(engine, "_responses_ws_pool", None)
    if pool is not None:
        pool.close()

    assert result["openai_ws_used"] is True
    assert result["openai_endpoint_name"] == "analyze_target"
    assert result["openai_schema_name"] == "holding_exit_v1"
    assert result["ai_parse_ok"] is True
    assert result["action_schema"] == "holding_exit_v1"
    assert result["action_v2"] in {"HOLD", "TRIM", "EXIT"}


def test_live_openai_scalp_sim_overnight_schema(monkeypatch):
    if os.getenv("RUN_OPENAI_LIVE_TESTS") != "1":
        pytest.skip("live OpenAI test disabled; set RUN_OPENAI_LIVE_TESTS=1")
    keys = _api_keys()
    if not keys:
        pytest.fail("RUN_OPENAI_LIVE_TESTS=1 requires OPENAI_API_KEY or OPENAI_API_KEYS")

    monkeypatch.setattr(
        openai_module,
        "TRADING_RULES",
        _RulesProxy(
            openai_module.TRADING_RULES,
            GPT_FAST_MODEL=os.getenv("KORSTOCKSCAN_OPENAI_LIVE_TEST_MODEL", "gpt-5-nano"),
            OPENAI_TRANSPORT_MODE="responses_ws",
            OPENAI_RESPONSES_WS_ENABLED=True,
            OPENAI_RESPONSES_WS_POOL_SIZE=1,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=10000,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False,
            OPENAI_REASONING_EFFORT="auto",
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=1024,
        ),
    )
    engine = GPTSniperEngine(keys, announce_startup=False)
    result = engine.evaluate_scalping_overnight_decision(
        "SIM_OVERNIGHT_LIVE_TEST",
        "000002",
        {
            "position_status": "SIM_HOLDING",
            "strategy": "SCALPING",
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "avg_price": 10000,
            "buy_price": 10000,
            "buy_qty": 1,
            "curr_price": 10020,
            "pnl_pct": 0.1,
            "peak_profit_pct": 0.3,
            "held_minutes": 35,
            "last_holding_ai_action": "HOLD",
            "last_holding_ai_score": 72,
            "order_status_note": "sim-only overnight test; no broker order is allowed",
        },
    )
    pool = getattr(engine, "_responses_ws_pool", None)
    if pool is not None:
        pool.close()

    assert result["openai_endpoint_name"] == "overnight"
    assert result["openai_schema_name"] == "overnight_v1"
    assert result["ai_parse_ok"] is True
    assert result["action"] in {"SELL_TODAY", "HOLD_OVERNIGHT"}
