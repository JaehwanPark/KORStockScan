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


def test_venue_preflight_matrix_separates_cohort_and_blocks_provider_leak():
    base = {
        "stage": "holding_flow_review",
        "fields": {
            "ai_input_schema": "holding_flow_v2",
            "ai_market_snapshot_id": "aims-1",
            "ai_market_snapshot_captured_at": "2026-07-23T18:00:00+09:00",
            "ai_market_snapshot_effective_venue": "NXT",
            "ai_market_snapshot_session_bucket": "nxt_aftermarket",
            "ai_market_snapshot_broker_route": "NXT",
            "ai_market_snapshot_market_data_route": "nxt_only",
            "ai_market_snapshot_underlying_event_venue": "NXT",
            "ai_market_snapshot_underlying_event_venue_source": (
                "exact_per_realtime_type"
            ),
            "ai_market_snapshot_venue_resolution": "explicit_or_session",
            "ai_input_preflight_source_allowed": True,
            "ai_input_preflight_allowed": False,
            "ai_input_preflight_venue_consistent": True,
            "ai_input_preflight_position_reconciled": True,
            "ai_market_snapshot_missing_as_zero": False,
            "provider_called": False,
        },
    }
    matrix = mod._venue_preflight_matrix([base])
    row = next(
        item
        for item in matrix["rows"]
        if item["row_id"] == "NXT_AFTERMARKET:holding_flow"
    )

    assert row["valid_rows"] == 1
    assert row["provider_called_while_blocked"] == 0
    assert row["broker_route_counts"] == {"NXT": 1}
    assert row["market_data_route_counts"] == {"NXT_ONLY": 1}
    assert row["underlying_event_venue_counts"] == {"NXT": 1}
    assert row["status"] == "ready"
    assert matrix["overall_status"] == "not_ready"


def test_venue_preflight_requires_payload_identity_for_provider_rows():
    fields = {
        "ai_input_schema": "entry_screen_hot_v1",
        "ai_market_snapshot_id": "aims-krx",
        "ai_market_snapshot_captured_at": "2026-07-23T10:00:00+09:00",
        "ai_market_snapshot_effective_venue": "KRX",
        "ai_market_snapshot_session_bucket": "krx_regular",
        "ai_market_snapshot_broker_route": "SOR",
        "ai_market_snapshot_market_data_route": "krx_nxt_integrated",
        "ai_market_snapshot_underlying_event_venue_source": "not_provided",
        "ai_market_snapshot_venue_resolution": "explicit",
        "ai_input_preflight_source_allowed": True,
        "ai_input_preflight_allowed": True,
        "ai_input_preflight_venue_consistent": True,
        "ai_market_snapshot_missing_as_zero": False,
        "provider_called": True,
    }

    missing = mod._venue_preflight_matrix(
        [{"stage": "scalp_entry_action_decision_snapshot", "fields": fields}]
    )
    missing_row = next(
        item for item in missing["rows"] if item["row_id"] == "KRX:entry_screen"
    )
    assert missing_row["payload_contract_missing"] == 1
    assert missing_row["duplicate_candle_contract_missing"] == 1
    assert missing_row["status"] == "not_ready"

    fields.update(
        {
            "ai_input_payload_sha256": "a" * 64,
            "ai_input_payload_bytes": 1234,
            "ai_input_duplicate_candle_views_omitted": True,
        }
    )
    complete = mod._venue_preflight_matrix(
        [{"stage": "scalp_entry_action_decision_snapshot", "fields": fields}]
    )
    complete_row = next(
        item for item in complete["rows"] if item["row_id"] == "KRX:entry_screen"
    )
    assert complete_row["payload_contract_missing"] == 0
    assert complete_row["duplicate_candle_contract_missing"] == 0
    assert complete_row["duplicate_candle_views_present"] == 0
    assert complete_row["status"] == "ready"


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
            expected_fallback_endpoints = (
                ("entry_price",)
                if mod.os.environ.get(
                    "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS"
                )
                == "entry_price"
                else ()
            )
            assert (
                getattr(
                    openai_module.TRADING_RULES,
                    "OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS",
                )
                == expected_fallback_endpoints
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
                "ai_input_schema": "entry_price_compact_v1",
                "action": "USE_DEFENSIVE",
                "order_price": "10000",
                "quote_age_ms": "100",
                "quote_stale": False,
                "entry_liquidity_score": "70",
                "fillability_score": "65",
                "order_flow_pressure_score": "61",
                "entry_context_quality": "partial",
                "ai_input_source_quality_status": "partial",
            }
        ],
        "holding_flow": [
            {
                "stock_code": "123456",
                "stock_name": "ProbeA",
                "event_time": "2026-07-13T10:35:00",
                "ai_input_schema": "holding_flow_text_v1",
                "flow_action": "HOLD",
                "flow_state": "absorption",
                "profit_rate": "0.20",
                "peak_profit": "0.80",
                "entry_context_quality": "partial",
                "ai_input_source_quality_status": "partial",
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
    candidate = result["entry_price_candidate_route"]
    assert candidate["provider_env"]["KORSTOCKSCAN_OPENAI_ENTRY_PRICE_TIMEOUT_MS"] == (
        "15000"
    )
    assert candidate["decision_points"]["entry_price"]["summary"]["row_count"] == 1
    assert result["candidate_pairwise"]["entry_price"]["summary"]["pair_count"] == 1


def test_provider_endpoint_compare_skips_source_quality_contract_gaps(monkeypatch):
    from src.engine import ai_engine_openai as openai_module

    class FailIfConstructed:
        def __init__(self, *args, **kwargs):
            raise AssertionError("provider must not run on invalid source rows")

    monkeypatch.setattr(openai_module, "GPTSniperEngine", FailIfConstructed)
    monkeypatch.setattr(mod, "_api_keys", lambda: ["test-key"])

    result = mod._run_endpoint_provider_compare(
        {
            "entry_price": [
                {
                    "stock_code": "123456",
                    "event_time": "2026-07-22T10:00:00",
                    "openai_endpoint_name": "entry_price",
                }
            ]
        },
        provider_mode="openai_only",
        provider_label="openai_only",
        model="gpt-5.4-mini",
        effort="low",
        sample_limit=1,
        points=("entry_price",),
    )

    assert result["entry_price"]["summary"]["row_count"] == 0
    assert result["entry_price"]["summary"]["skipped_count"] == 1
    assert result["entry_price"]["results"][0]["reason"] == (
        "source_quality_contract_missing"
    )


def test_decision_point_rows_prefers_latest_emitted_at():
    rows = mod._decision_point_rows(
        [],
        [
            {
                "stage": "entry_ai_price_canary_applied",
                "emitted_at": "2026-07-22T10:00:00",
                "fields": {"stock_code": "old", "openai_endpoint_name": "entry_price"},
            },
            {
                "stage": "entry_ai_price_canary_applied",
                "emitted_at": "2026-07-22T11:00:00",
                "fields": {"stock_code": "new", "openai_endpoint_name": "entry_price"},
            },
        ],
    )

    assert rows["entry_price"][0]["stock_code"] == "new"
    assert rows["entry_price"][0]["emitted_at"] == "2026-07-22T11:00:00"


def test_holding_provider_probe_rehydrates_model_bars_and_structured_flags():
    bars = [
        {
            "t": f"09:{index:02d}",
            "o": 10000 + index,
            "h": 10002 + index,
            "l": 9998 + index,
            "c": 10001 + index,
            "v": 100 + index,
            "forming": index == 19,
            "partial_volume": index == 19,
        }
        for index in range(20)
    ]
    fields = {
        "holding_context_enabled": "True",
        "holding_context_venue": "NXT",
        "holding_context_session": "nxt_aftermarket",
        "holding_context_rest_route": "_NX",
        "holding_context_ws_route": "krx_nxt_integrated",
        "holding_context_model_bars": repr(bars),
        "holding_context_model_structure": repr(
            {"returns_pct": {"3": 0.2, "20": 0.8}}
        ),
        "holding_context_candle_risk_flags": "['venue_conflict']",
        "holding_context_blockers": "['candle_source_quality']",
        "holding_context_source_quality_status": "blocked",
    }

    context = mod._fields_to_holding_decision_context(fields)
    candles = mod._entry_context_to_recent_candles(context["candle"])

    assert len(context["candle"]["bars"]) == 20
    assert context["candle"]["risk_flags"] == ["venue_conflict"]
    assert context["source_quality"]["blockers"] == ["candle_source_quality"]
    assert context["candle"]["structure"]["returns_pct"]["20"] == 0.8
    assert len(candles) == 20
    assert candles[-1]["close"] == 10020
    assert candles[-1]["forming"] is True


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
