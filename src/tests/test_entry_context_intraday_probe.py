import json

from src.engine.scalping import entry_context_intraday_probe as mod


def _base_row(**overrides):
    row = {
        "stage": "scalp_entry_action_decision_snapshot",
        "source_stage": "ai_confirmed",
        "candidate_id": "ADM1",
        "record_id": "R1",
        "stock_code": "123456",
        "stock_name": "ProbeA",
        "event_time": "2026-07-13T10:20:00",
        "chosen_action": "NO_BUY_AI",
        "ai_action": "WAIT",
        "ai_score": "64",
        "entry_liquidity_score": 72,
        "entry_liquidity_status": "pass",
        "fillability_score": 68,
        "order_flow_pressure_score": 61,
        "entry_order_flow_status": "neutral",
        "entry_momentum_score": 58,
        "entry_momentum_status": "partial",
        "entry_context_quality": "partial",
        "entry_context_missing_features": "signed_tape,micro_vwap",
    }
    row.update(overrides)
    return row


def test_probe_report_reads_existing_adm_and_summarizes_context(tmp_path, monkeypatch):
    report_path = tmp_path / "adm.json"
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir()
    pipeline_path = pipeline_dir / "pipeline_events_2026-07-13.jsonl"
    pipeline_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "entry_ai_price_canary_applied",
                        "fields": {
                            "stock_code": "123456",
                            "stock_name": "ProbeA",
                            "ai_input_schema": "entry_price_compact_v1",
                            "order_price": "10000",
                            "quote_age_ms": "100",
                            "entry_liquidity_score": "71",
                            "fillability_score": "68",
                            "order_flow_pressure_score": "63",
                            "entry_context_quality": "partial",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "holding_score_review",
                        "fields": {
                            "stock_code": "123456",
                            "stock_name": "ProbeA",
                            "holding_score_input_schema": "holding_score_v2",
                            "profit_rate": "0.35",
                            "peak_profit": "0.80",
                            "holding_score_data_quality": "fresh",
                            "entry_context_quality": "partial",
                            "action": "HOLD",
                            "score": "74",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "holding_flow_override_defer_exit",
                        "fields": {
                            "stock_code": "123456",
                            "stock_name": "ProbeA",
                            "ai_input_schema": "holding_flow_text_v1",
                            "profit_rate": "0.20",
                            "peak_profit": "0.90",
                            "flow_state": "absorption",
                            "entry_context_quality": "partial",
                            "flow_action": "HOLD",
                            "score": "66",
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "artifact": str(report_path),
                "rows": [
                    _base_row(event_time="2026-07-13T10:20:00"),
                    _base_row(
                        candidate_id="ADM2",
                        record_id="R2",
                        stock_code="654321",
                        stock_name="ProbeB",
                        event_time="2026-07-13T10:25:00",
                        entry_context_quality="complete",
                        entry_context_missing_features="",
                    ),
                    _base_row(stage="unrelated_stage", source_stage="not_ai"),
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod.adm_mod,
        "report_paths",
        lambda target_date: (report_path, tmp_path / "adm.md"),
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)

    report = mod.build_probe_report("2026-07-13", sample_limit=10)

    assert report["status"] == "ok"
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["coverage"]["row_count"] == 2
    assert report["coverage"]["complete_or_partial_count"] == 2
    assert report["coverage"]["required_field_counts"]["entry_liquidity_score"] == 2
    assert (
        report["coverage"]["entry_context_missing_feature_counts"]["signed_tape"] == 1
    )
    assert report["sample_rows"][0]["candidate_id"] == "ADM2"
    assert report["sample_rows"][0]["features"]["entry_liquidity_score"] == 72
    decision_probe = report["ai_decision_contract_probe"]
    assert decision_probe["overall_status"] == "ok"
    assert decision_probe["decision_points"]["entry_screen"]["row_count"] == 2
    assert decision_probe["decision_points"]["entry_price"]["coverage_status"] == "ok"
    assert decision_probe["decision_points"]["holding_score"]["coverage_status"] == "ok"
    assert decision_probe["decision_points"]["holding_flow"]["coverage_status"] == "ok"
    assert report["live_openai"]["enabled"] is False
    assert report["openai_endpoint_compare"]["enabled"] is False


def test_probe_report_can_build_adm_before_sampling(monkeypatch):
    monkeypatch.setattr(
        mod.adm_mod,
        "build_scalp_entry_action_decision_matrix_report",
        lambda target_date: {
            "status": "ok",
            "artifact": f"/tmp/scalp_entry_action_decision_matrix_{target_date}.json",
            "rows": [_base_row()],
        },
    )
    monkeypatch.setattr(
        mod.adm_mod,
        "report_paths",
        lambda target_date: (
            mod.Path(f"/tmp/scalp_entry_action_decision_matrix_{target_date}.json"),
            mod.Path(f"/tmp/scalp_entry_action_decision_matrix_{target_date}.md"),
        ),
    )

    report = mod.build_probe_report("2026-07-13", build_adm=True)

    assert report["status"] == "ok"
    assert report["source"]["build_adm"] is True
    assert report["coverage"]["row_count"] == 1


def test_live_openai_is_skipped_without_api_key(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_read_adm_report",
        lambda target_date, *, build_adm: {"status": "ok", "rows": [_base_row()]},
    )
    monkeypatch.setattr(mod, "_api_keys", lambda: [])

    report = mod.build_probe_report("2026-07-13", live_openai=True)

    assert report["live_openai"]["enabled"] is True
    assert report["live_openai"]["summary"]["row_count"] == 0
    assert report["live_openai"]["summary"]["skipped_count"] == 1
    assert report["live_openai"]["results"] == [
        {"status": "skipped", "reason": "OPENAI_API_KEY not configured"}
    ]


def test_live_openai_restores_temporary_rules_override(monkeypatch):
    from src.engine import ai_engine_openai as openai_module

    original_rules = object()

    class FakeEngine:
        def __init__(self, keys, announce_startup=False):
            assert keys == ["test-key"]
            assert announce_startup is False

        def _call_openai_safe(self, *args, **kwargs):
            assert openai_module.TRADING_RULES is not original_rules
            assert (
                getattr(openai_module.TRADING_RULES, "OPENAI_REASONING_EFFORT")
                == "minimal"
            )
            return {
                "action": "WAIT",
                "score": 55,
                "issue": "insufficient_context",
                "confidence": 0.4,
                "missing_features": ["signed_tape"],
                "reason": "정보 부족",
            }

    monkeypatch.setattr(openai_module, "TRADING_RULES", original_rules)
    monkeypatch.setattr(openai_module, "GPTSniperEngine", FakeEngine)
    monkeypatch.setattr(mod, "_api_keys", lambda: ["test-key"])

    results = mod._call_openai([_base_row()], model="gpt-5-nano", effort="minimal")

    assert openai_module.TRADING_RULES is original_rules
    assert results[0]["action"] == "WAIT"
    assert results[0]["action_score_mismatch"] is False


def test_provider_endpoint_compare_runs_bedrock_primary_and_openai_then_restores_env(
    monkeypatch,
):
    from src.engine import ai_engine_openai as openai_module

    original_rules = object()
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")

    class FakeEngine:
        def __init__(self, keys, announce_startup=False):
            assert keys == ["test-key"]
            assert announce_startup is False
            assert (
                getattr(openai_module.TRADING_RULES, "GPT_REPORT_MODEL")
                == "gpt-5.4-mini"
            )
            assert (
                getattr(openai_module.TRADING_RULES, "OPENAI_REASONING_EFFORT") == "low"
            )
            assert (
                getattr(
                    openai_module.TRADING_RULES,
                    "OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS",
                )
                == ()
            )

        def evaluate_scalping_entry_price(
            self,
            stock_name,
            stock_code,
            ws_data,
            recent_ticks,
            recent_candles,
            price_ctx,
            metadata_extra=None,
        ):
            assert (
                metadata_extra["source_event_stage"]
                == "entry_context_intraday_probe_provider_compare"
            )
            bedrock_route = (
                mod.os.environ["KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE"]
                == "primary"
            )
            return {
                "action": "USE_DEFENSIVE",
                "order_price": 10005 if bedrock_route else 10010,
                "confidence": 62,
                "reason": "bedrock compare" if bedrock_route else "openai compare",
                "openai_transport_mode": "bedrock_primary" if bedrock_route else "http",
                "bedrock_primary_used": bedrock_route,
                "bedrock_failback_used": False,
            }

        def evaluate_scalping_holding_flow(
            self,
            stock_name,
            stock_code,
            ws_data,
            recent_ticks,
            recent_candles,
            position_ctx,
            flow_history=None,
            decision_kind="intraday_exit",
            metadata_extra=None,
        ):
            assert decision_kind == "intraday_probe_compare"
            bedrock_route = (
                mod.os.environ["KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE"] == "primary"
            )
            return {
                "action": "HOLD" if bedrock_route else "EXIT",
                "score": 72,
                "flow_state": "absorption" if bedrock_route else "breakdown",
                "next_review_sec": 30,
                "reason": (
                    "bedrock flow compare" if bedrock_route else "openai flow compare"
                ),
                "openai_transport_mode": "bedrock_primary" if bedrock_route else "http",
                "bedrock_primary_used": bedrock_route,
                "bedrock_failback_used": False,
            }

    rows_by_point = {
        "entry_price": [
            {
                "stock_code": "123456",
                "stock_name": "ProbeA",
                "event_time": "2026-07-13T10:30:00",
                "action": "USE_DEFENSIVE",
                "order_price": "10000",
                "quote_age_ms": "100",
                "entry_context_quality": "partial",
            }
        ],
        "holding_flow": [
            {
                "stock_code": "123456",
                "stock_name": "ProbeA",
                "event_time": "2026-07-13T10:35:00",
                "flow_action": "HOLD",
                "flow_state": "absorption",
                "profit_rate": "0.20",
                "peak_profit": "0.80",
            }
        ],
    }
    monkeypatch.setattr(openai_module, "TRADING_RULES", original_rules)
    monkeypatch.setattr(openai_module, "GPTSniperEngine", FakeEngine)
    monkeypatch.setattr(mod, "_api_keys", lambda: ["test-key"])

    result = mod._call_provider_endpoint_compare(
        rows_by_point,
        model="gpt-5.4-mini",
        effort="low",
        sample_limit=5,
    )

    assert openai_module.TRADING_RULES is original_rules
    assert mod.os.environ["KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE"] == "primary"
    assert mod.os.environ["KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE"] == "primary"
    bedrock_entry = result["bedrock_primary"]["decision_points"]["entry_price"]
    openai_entry = result["openai_gpt54_mini"]["decision_points"]["entry_price"]
    assert bedrock_entry["summary"]["bedrock_primary_used_count"] == 1
    assert openai_entry["summary"]["bedrock_primary_used_count"] == 0
    assert result["pairwise"]["entry_price"]["summary"]["pair_count"] == 1
    assert result["pairwise"]["entry_price"]["summary"]["order_price_diff_count"] == 1
    assert result["pairwise"]["holding_flow"]["summary"]["action_diff_count"] == 1
    assert result["pairwise"]["holding_flow"]["summary"]["flow_state_diff_count"] == 1


def test_probe_report_includes_endpoint_compare_when_requested(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_read_adm_report",
        lambda target_date, *, build_adm: {"status": "ok", "rows": [_base_row()]},
    )
    monkeypatch.setattr(
        mod,
        "_read_pipeline_events",
        lambda target_date: {
            "status": "ok",
            "artifact": "/tmp/pipeline.jsonl",
            "rows": [
                {
                    "stage": "entry_ai_price_canary_applied",
                    "fields": {
                        "stock_code": "123456",
                        "ai_input_schema": "entry_price_compact_v1",
                        "order_price": "10000",
                        "quote_age_ms": "100",
                        "entry_liquidity_score": "70",
                        "fillability_score": "65",
                        "order_flow_pressure_score": "61",
                        "entry_context_quality": "partial",
                    },
                }
            ],
            "parse_error_count": 0,
        },
    )
    monkeypatch.setattr(
        mod,
        "_call_provider_endpoint_compare",
        lambda rows_by_point, *, model, effort, sample_limit: {
            "input_variant": "enriched_probe_context_v1",
            "bedrock_primary": {
                "provider_env": {},
                "decision_points": {
                    "entry_price": {
                        "results": [{"status": "ok", "model": model, "effort": effort}],
                        "summary": {"row_count": 1},
                    },
                    "holding_flow": {"results": [], "summary": {"row_count": 0}},
                },
            },
            "openai_gpt54_mini": {
                "provider_env": {},
                "decision_points": {
                    "entry_price": {
                        "results": [{"status": "ok", "model": model, "effort": effort}],
                        "summary": {"row_count": 1},
                    },
                    "holding_flow": {"results": [], "summary": {"row_count": 0}},
                },
            },
            "pairwise": {
                "entry_price": {"results": [], "summary": {"pair_count": 0}},
                "holding_flow": {"results": [], "summary": {"pair_count": 0}},
            },
        },
    )

    report = mod.build_probe_report(
        "2026-07-13",
        compare_openai_endpoints=True,
        endpoint_compare_model="gpt-5.4-mini",
        endpoint_compare_effort="low",
    )

    compare = report["openai_endpoint_compare"]
    assert compare["enabled"] is True
    assert compare["model"] == "gpt-5.4-mini"
    assert compare["effort"] == "low"
    assert (
        compare["provider_override"]["KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE"]
        == "off"
    )
    assert compare["decision_points"]["entry_price"]["summary"]["row_count"] == 1
    provider_compare = report["provider_endpoint_compare"]
    assert provider_compare["enabled"] is True
    assert (
        provider_compare["result"]["bedrock_primary"]["decision_points"]["entry_price"][
            "summary"
        ]["row_count"]
        == 1
    )
    assert (
        provider_compare["result"]["pairwise"]["entry_price"]["summary"]["pair_count"]
        == 0
    )
