import json

from src.engine.monitoring import one_share_threshold_opportunity as mod


def _event(record_id, stage, fields=None, *, code="000001", name="sample", emitted_at="2026-07-01T09:00:00+09:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "record_id": record_id,
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields or {},
        "emitted_at": emitted_at,
    }


def test_build_report_aggregates_threshold_opportunity_and_orders(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    rows = []
    for idx, profit in enumerate([0.8, 0.5, -0.1], start=1):
        rows.extend(
            [
                _event(
                    idx,
                    "blocked_ai_score",
                    {
                        "reason": "blocked_ai_score_below_buy_score_threshold",
                        "ai_score": "72",
                    },
                    code=f"00000{idx}",
                ),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {
                        "forced_entry_reason": "rising_missed_one_share_entry",
                        "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    },
                    code=f"00000{idx}",
                ),
            ]
        )
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": f"00000{idx}",
                    "stock_name": "sample",
                    "profit_rate": profit,
                    "peak_profit": profit + 0.2,
                    "exit_rule": "scalp_take_profit" if profit > 0 else "scalp_soft_stop",
                }
            )
            for idx, profit in enumerate([0.8, 0.5, -0.1], start=1)
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    assert report["summary"]["forced_record_count"] == 3
    assert report["summary"]["post_sell_joined_count"] == 3
    assert report["summary"]["code_improvement_order_count"] == 1
    opportunity = report["threshold_opportunities"][0]
    assert opportunity["threshold_group"] == "ai_score_near_buy"
    assert opportunity["valid_profit_sample"] == 3
    assert opportunity["equal_weight_avg_profit_pct"] == 0.4
    order = report["code_improvement_orders"][0]
    assert order["source_report_type"] == "one_share_threshold_opportunity"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["requires_separate_runtime_apply_candidate"] is True
    assert order["implementation_provenance"]["broker_order_forbidden"] is True
    assert "broker_guard_bypass" in order["forbidden_uses"]
    assert report["ai_review"]["status"] == "unavailable"


def test_valid_profit_sample_floor_blocks_incomplete_pnl_order(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-01.jsonl"
    post_sell_path = tmp_path / "post_sell_candidates_2026-07-01.jsonl"
    rows = []
    for idx in range(1, 4):
        rows.extend(
            [
                _event(
                    idx,
                    "blocked_ai_score",
                    {"reason": "blocked_ai_score_below_buy_score_threshold", "ai_score": "72"},
                    code=f"00000{idx}",
                ),
                _event(
                    idx,
                    "rising_missed_one_share_entry",
                    {"forced_entry_reason": "rising_missed_one_share_entry"},
                    code=f"00000{idx}",
                ),
            ]
        )
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    post_sell_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "recommendation_id": idx,
                    "stock_code": f"00000{idx}",
                    "stock_name": "sample",
                    "profit_rate": 0.7 if idx == 1 else None,
                    "exit_rule": "scalp_take_profit",
                }
            )
            for idx in range(1, 4)
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        since_date="2026-07-01",
        pipeline_paths=[pipeline_path],
        post_sell_paths=[post_sell_path],
        generated_at="fixed",
        ai_provider="none",
    )

    opportunity = report["threshold_opportunities"][0]
    assert opportunity["sample"] == 3
    assert opportunity["valid_profit_sample"] == 1
    assert opportunity["equal_weight_avg_profit_pct"] == 0.7
    assert report["summary"]["code_improvement_order_count"] == 0
    assert report["code_improvement_orders"] == []


def test_ai_review_annotations_are_source_only(tmp_path, monkeypatch):
    def fake_ai_review(report, *, provider):
        return json.dumps(
            {
                "schema_version": 1,
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [
                    {
                        "candidate_id": "one_share_threshold_ai_score_near_buy",
                        "recommended_disposition": "attach_existing_entry_hook",
                        "confidence": "medium",
                        "reason": "bounded entry hook already exists",
                        "required_followup": ["verify post-apply attribution"],
                    }
                ],
                "audit": {"status": "pass", "issues": [], "reason": "source-only"},
                "codex_directives": [],
            }
        ), {"provider": provider, "status": "success"}

    monkeypatch.setattr(mod, "_call_ai_review", fake_ai_review)
    report = {
        "target_date": "2026-07-01",
        "window": {},
        "summary": {},
        "metric_contract": {},
        "threshold_opportunities": [],
        "code_improvement_orders": [
            {
                "candidate_id": "one_share_threshold_ai_score_near_buy",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ],
    }

    reviewed = mod._apply_ai_review(report, provider="openai")

    order = reviewed["code_improvement_orders"][0]
    assert reviewed["ai_review"]["status"] == "parsed"
    assert reviewed["ai_review"]["runtime_effect"] is False
    assert order["ai_recommended_disposition"] == "attach_existing_entry_hook"
    assert order["runtime_effect"] is False


def test_ai_review_malformed_schema_version_is_parse_rejected():
    status, payload, warnings = mod._parse_ai_review(
        json.dumps(
            {
                "schema_version": "bad",
                "reviewer": "one_share_threshold_opportunity_ai_review",
                "candidate_reviews": [],
                "audit": {"status": "pass", "issues": [], "reason": "source-only"},
                "codex_directives": [],
            }
        )
    )

    assert status == "parse_rejected"
    assert payload["schema_version"] == "bad"
    assert "ai_review_schema_version_invalid" in warnings


def test_hard_safety_group_does_not_create_code_order():
    opportunities = [
        {
            "candidate_id": "one_share_threshold_cooldown_or_hard_safety",
            "threshold_group": "cooldown_or_hard_safety",
            "mapped_family": "hard_safety_observation_only",
            "target_subsystem": "entry_hard_safety_preserve",
            "sample": 3,
            "valid_profit_sample": 3,
            "profitable_count": 3,
            "loss_or_flat_count": 0,
            "equal_weight_avg_profit_pct": 0.6,
        }
    ]

    assert mod._build_code_orders(opportunities, {"pipeline_events": [], "post_sell_candidates": []}) == []


def test_write_outputs(tmp_path):
    report = {
        "target_date": "2026-07-01",
        "generated_at": "fixed",
        "window": {"since_date": "2026-06-30", "until_date": "2026-07-01"},
        "summary": {
            "forced_record_count": 1,
            "post_sell_joined_count": 1,
            "profitable_joined_count": 1,
            "loss_or_flat_joined_count": 0,
            "threshold_opportunity_count": 1,
            "code_improvement_order_count": 1,
            "ai_review_status": "parsed",
        },
        "threshold_opportunities": [
            {
                "threshold_group": "ai_score_near_buy",
                "candidate_id": "one_share_threshold_ai_score_near_buy",
                "mapped_family": "entry_opportunity_recheck_runtime",
                "sample": 3,
                "valid_profit_sample": 3,
                "equal_weight_avg_profit_pct": 0.4,
                "profitable_count": 2,
                "loss_or_flat_count": 1,
            }
        ],
        "code_improvement_orders": [
            {
                "order_id": "order_one_share_threshold_ai_score_near_buy_entry_hook_review",
                "mapped_family": "entry_opportunity_recheck_runtime",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "ai_recommended_disposition": "attach_existing_entry_hook",
                "evidence": ["sample=3"],
            }
        ],
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert json.loads(output_json.read_text(encoding="utf-8"))["target_date"] == "2026-07-01"
    markdown = output_md.read_text(encoding="utf-8")
    assert "One Share Threshold Opportunity" in markdown
    assert "runtime_effect: false" in markdown
