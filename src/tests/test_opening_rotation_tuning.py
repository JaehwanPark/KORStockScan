import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.scalping.opening_rotation import (
    POLICY_SCHEMA_VERSION,
    OpeningRotationRuntimePolicy,
    load_runtime_policy,
    runtime_policy_path,
)
from src.engine.scalping.opening_rotation_tuning import (
    REPORT_SCHEMA_VERSION,
    apply_preopen,
    build_postclose_report,
    candidate_path,
    verify_artifacts,
    write_postclose,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _event(stage: str, at: str, code: str, fields: dict) -> dict:
    return {
        "pipeline": (
            "HOLDING_PIPELINE" if stage == "sell_completed" else "ENTRY_PIPELINE"
        ),
        "stage": stage,
        "stock_code": code,
        "fields": fields,
        "emitted_at": at,
    }


def _audit(root: Path, target_date: str, *, allowed: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"observation_source_quality_audit_{target_date}.json").write_text(
        json.dumps(
            {
                "status": "pass" if allowed else "fail",
                "summary": {"tuning_input_allowed": allowed},
            }
        ),
        encoding="utf-8",
    )


def _candidate_report(
    path: Path,
    *,
    target_date: str,
    baseline: OpeningRotationRuntimePolicy,
    axis: str,
    value,
    proposed: OpeningRotationRuntimePolicy,
    rollback: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": REPORT_SCHEMA_VERSION,
                "target_date": target_date,
                "allowed_runtime_apply": True,
                "active_policy": baseline.as_artifact(),
                "selected_candidate": {
                    "axis": axis,
                    "value": value,
                    "proposed_policy_hash": proposed.policy_hash,
                },
                "rollback": {"triggered": rollback},
            }
        ),
        encoding="utf-8",
    )


def _episode_rows(
    *,
    target_date: str,
    index: int,
    profit_rate: float,
    day_change_pct: float,
    policy: OpeningRotationRuntimePolicy,
) -> list[dict]:
    code = f"{index % 10:06d}"
    episode_id = f"OREP-{target_date.replace('-', '')}-{index:04d}"
    common = {
        "opening_rotation_episode_id": episode_id,
        "opening_rotation_episode_promotion_id": f"PROMO-{index}",
        "opening_rotation_profile_id": policy.profile_id,
        "opening_rotation_policy_hash": policy.policy_hash,
        "opening_rotation_policy_schema_version": POLICY_SCHEMA_VERSION,
        "day_change_pct": day_change_pct,
        "pullback_pct": 0.5,
        "confirmation_pass_count": 3,
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "opening_rotation_margin_one_share_authorized": True,
        "opening_rotation_margin_authority_reason": (
            "kt00011_applied_margin_tier_one_share_confirmed"
        ),
        "opening_rotation_margin_rate": 40,
        "opening_rotation_margin_orderable_amount": 1_200_000,
        "opening_rotation_margin_orderable_qty_cap": 120,
        "opening_rotation_margin_requested_unit_price": 10_000,
        "opening_rotation_margin_cash_guard_bypassed": True,
        "opening_rotation_margin_order_api": "kt10000",
        "opening_rotation_margin_credit_order_api_used": False,
    }
    return [
        _event(
            "opening_rotation_1pct_qualified",
            f"{target_date}T09:10:00+09:00",
            code,
            common,
        ),
        _event(
            "opening_rotation_redundant_submit_guard_bypassed",
            f"{target_date}T09:10:01+09:00",
            code,
            {
                **common,
                "opening_rotation_redundant_submit_guard": "pre_submit_liquidity",
                "opening_rotation_redundant_submit_guard_would_block": True,
            },
        ),
        _event(
            "holding_started",
            f"{target_date}T09:10:05+09:00",
            code,
            {
                **common,
                "opening_rotation_buy_submit_to_fill_ms": 5000,
                "buy_price": 10_000,
            },
        ),
        _event(
            "opening_rotation_profit_target_ordered",
            f"{target_date}T09:10:06+09:00",
            code,
            {**common, "opening_rotation_profit_target_price": 10_070},
        ),
        _event(
            "sell_completed",
            f"{target_date}T09:15:00+09:00",
            code,
            {
                **common,
                "position_tag": "OPENING_ROTATION_1PCT",
                "profit_rate": profit_rate,
                "realized_pnl_krw": int(profit_rate * 100),
                "mfe_pct": max(0.4, profit_rate),
                "mae_pct": min(-0.1, profit_rate),
                "exit_rule": "profit_target_filled",
            },
        ),
    ]


def test_postclose_selects_only_one_predeclared_axis_with_strict_sample_floors(
    tmp_path,
):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    runtime = tmp_path / "runtime"
    baseline = OpeningRotationRuntimePolicy(target_date="2026-08-06")
    sequence = 0
    for target_date in ("2026-08-06", "2026-08-07", "2026-08-08"):
        rows = []
        for _ in range(10):
            rows.extend(
                _episode_rows(
                    target_date=target_date,
                    index=sequence,
                    profit_rate=0.5,
                    day_change_pct=2.5,
                    policy=baseline,
                )
            )
            sequence += 1
        for _ in range(2):
            rows.extend(
                _episode_rows(
                    target_date=target_date,
                    index=sequence,
                    profit_rate=-1.0,
                    day_change_pct=1.6,
                    policy=baseline,
                )
            )
            sequence += 1
        _write_jsonl(events / f"pipeline_events_{target_date}.jsonl", rows)
        _audit(audits, target_date)

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=runtime,
    )

    assert report["source_quality"]["status"] == "pass"
    assert report["performance"]["complete_episode_count"] == 36
    assert report["funnel"]["margin_authorized_episode_count"] == 36
    assert report["funnel"]["margin_cash_guard_bypassed_episode_count"] == 36
    assert report["funnel"]["margin_applied_rate_counts"] == {"40": 36}
    assert report["funnel"]["margin_order_api_counts"] == {"kt10000": 36}
    assert report["funnel"]["margin_credit_order_api_used_episode_count"] == 0
    assert report["funnel"]["margin_order_contract_violation_count"] == 0
    assert report["funnel"]["duplicate_submit_guard_bypass_episode_count"] == 36
    assert report["funnel"]["duplicate_submit_guard_bypass_filled_episode_count"] == 36
    assert (
        report["funnel"]["duplicate_submit_guard_bypass_complete_episode_count"] == 36
    )
    assert report["funnel"]["duplicate_submit_guard_bypass_counts"] == {
        "pre_submit_liquidity": 36
    }
    assert (
        report["downstream_guard_overlap"]["performance"]["complete_episode_count"]
        == 36
    )
    assert report["selected_candidate"]["axis"] == "day_change_lower"
    assert report["selected_candidate"]["value"] == 2.0
    assert candidate["status"] == "eligible"
    assert candidate["proposed_policy"]["entry"]["min_day_change_pct"] == 2.0
    assert candidate["proposed_policy"]["watch_slots"] == 2
    assert candidate["proposed_policy"]["scale_in_allowed"] is False


def test_postclose_blocks_tuning_when_source_quality_is_missing(tmp_path):
    events = tmp_path / "events"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    _write_jsonl(
        events / "pipeline_events_2026-08-08.jsonl",
        _episode_rows(
            target_date="2026-08-08",
            index=1,
            profit_rate=0.5,
            day_change_pct=2.5,
            policy=policy,
        ),
    )

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=tmp_path / "missing-audits",
        runtime_root=tmp_path / "runtime",
    )

    assert report["status"] == "source_quality_blocked"
    assert report["performance"]["source_quality_adjusted_ev_pct"] is None
    assert candidate["status"] == "no_change"


def test_postclose_blocks_tuning_on_margin_order_contract_violation(tmp_path):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    rows = _episode_rows(
        target_date="2026-08-08",
        index=1,
        profit_rate=0.5,
        day_change_pct=2.5,
        policy=policy,
    )
    # A later valid receipt must not erase an earlier forbidden-order event.
    rows[0]["fields"]["opening_rotation_margin_order_api"] = "kt10006"
    rows[0]["fields"]["opening_rotation_margin_credit_order_api_used"] = True
    _write_jsonl(events / "pipeline_events_2026-08-08.jsonl", rows)
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=tmp_path / "runtime",
    )

    assert report["status"] == "source_quality_blocked"
    assert report["source_quality"]["margin_order_contract_violation_count"] == 1
    assert report["funnel"]["margin_order_contract_violation_count"] == 1
    assert report["funnel"]["margin_credit_order_api_used_episode_count"] == 1
    assert report["performance"]["source_quality_adjusted_ev_pct"] is None
    assert candidate["status"] == "no_change"


def test_postclose_preserves_missing_margin_order_provenance_as_sticky_violation(
    tmp_path,
):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    rows = _episode_rows(
        target_date="2026-08-08",
        index=1,
        profit_rate=0.5,
        day_change_pct=2.5,
        policy=policy,
    )
    # Later complete receipts are valid, but the first authorized event was not.
    rows[0]["fields"].pop("opening_rotation_margin_order_api")
    rows[0]["fields"].pop("opening_rotation_margin_credit_order_api_used")
    _write_jsonl(events / "pipeline_events_2026-08-08.jsonl", rows)
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=tmp_path / "runtime",
    )

    assert report["status"] == "source_quality_blocked"
    assert report["source_quality"]["margin_order_contract_violation_count"] == 1
    assert report["funnel"]["margin_order_contract_violation_count"] == 1
    assert report["performance"]["source_quality_adjusted_ev_pct"] is None
    assert candidate["status"] == "no_change"


def test_postclose_source_quality_includes_relevant_date_without_completion(tmp_path):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    _write_jsonl(
        events / "pipeline_events_2026-08-07.jsonl",
        [
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-07T09:10:00+09:00",
                "005930",
                {
                    "scanner_promotion_id": "PROMO-GAP",
                    "day_change_pct": 2.5,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            )
        ],
    )
    _write_jsonl(
        events / "pipeline_events_2026-08-08.jsonl",
        _episode_rows(
            target_date="2026-08-08",
            index=1,
            profit_rate=0.5,
            day_change_pct=2.5,
            policy=policy,
        ),
    )
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=tmp_path / "runtime",
    )

    assert report["source_quality"]["status"] == "blocked"
    assert report["source_quality"]["missing_dates"] == ["2026-08-07"]
    assert candidate["status"] == "no_change"


def test_runtime_loader_rejects_non_tunable_profile_mutation(tmp_path):
    baseline = OpeningRotationRuntimePolicy(target_date="2026-08-09")
    tampered = replace(
        baseline,
        entry=replace(baseline.entry, min_buy_pressure_pct=55.0),
    )
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(tampered.as_artifact()), encoding="utf-8")

    with pytest.raises(ValueError, match="non-tunable entry field"):
        load_runtime_policy(path)


def test_postclose_deduplicates_promotion_bins_and_rejects_episode_hash_conflict(
    tmp_path,
):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    rows = _episode_rows(
        target_date="2026-08-08",
        index=1,
        profit_rate=0.5,
        day_change_pct=2.5,
        policy=policy,
    )
    common = rows[0]["fields"]
    rows.insert(
        0,
        _event(
            "scalping_scanner_candidate_promoted",
            "2026-08-08T09:09:59+09:00",
            "000001",
            {
                "scanner_promotion_id": common["opening_rotation_episode_promotion_id"],
                "day_change_pct": 2.5,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
        ),
    )
    rows[2]["fields"] = {
        **rows[2]["fields"],
        "opening_rotation_policy_hash": "conflicting-policy-hash",
    }
    _write_jsonl(events / "pipeline_events_2026-08-08.jsonl", rows)
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=tmp_path / "runtime",
    )

    assert report["funnel"]["unique_scanner_promotion_count"] == 1
    assert report["day_change_distribution"]["1_5_to_3"] == 1
    assert (
        report["day_change_range_validation"]["status"]
        == "blocked_outside_active_range_complete_outcomes_missing"
    )
    assert (
        report["day_change_range_validation"][
            "outside_active_range_auto_promotion_allowed"
        ]
        is False
    )
    assert report["funnel"]["episode_contract_conflict_count"] == 1
    assert report["funnel"]["strict_episode_count"] == 0
    assert candidate["status"] == "no_change"


def test_postclose_enriches_missing_promotion_day_change_from_later_same_identity(
    tmp_path,
):
    events = tmp_path / "events"
    promotion_id = "PROMO-LATE-DAY-CHANGE"
    _write_jsonl(
        events / "pipeline_events_2026-08-08.jsonl",
        [
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-08T09:10:00+09:00",
                "005930",
                {
                    "scanner_promotion_id": promotion_id,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            ),
            _event(
                "scalping_scanner_fast_precheck",
                "2026-08-08T09:10:01+09:00",
                "005930",
                {
                    "scanner_promotion_id": promotion_id,
                    "opening_rotation_upstream_day_change_pct": 3.5,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            ),
            _event(
                "opening_rotation_1pct_observed",
                "2026-08-08T09:10:02+09:00",
                "005930",
                {
                    "scanner_promotion_id": promotion_id,
                    "day_change_pct": 3.6,
                    "reason": "pullback_not_observed",
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            ),
        ],
    )

    report, _candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=tmp_path / "audits",
        runtime_root=tmp_path / "runtime",
    )

    assert report["funnel"]["unique_scanner_promotion_count"] == 1
    assert report["day_change_distribution"]["3_to_5"] == 1
    assert report["day_change_distribution"]["missing"] == 0


def test_postclose_promotion_funnel_excludes_non_krx_or_outside_opening_window(
    tmp_path,
):
    events = tmp_path / "events"
    _write_jsonl(
        events / "pipeline_events_2026-08-08.jsonl",
        [
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-08T09:10:00+09:00",
                "005930",
                {
                    "scanner_promotion_id": "PROMO-KRX",
                    "day_change_pct": 2.5,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            ),
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-08T10:10:00+09:00",
                "000660",
                {
                    "scanner_promotion_id": "PROMO-NXT",
                    "day_change_pct": 2.5,
                    "effective_venue": "NXT",
                    "market_session_bucket": "nxt",
                },
            ),
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-08T14:10:00+09:00",
                "035420",
                {
                    "scanner_promotion_id": "PROMO-LATE",
                    "day_change_pct": 2.5,
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                },
            ),
            _event(
                "scalping_scanner_candidate_promoted",
                "2026-08-08T09:20:00+09:00",
                "051910",
                {
                    "scanner_promotion_id": "PROMO-UNKNOWN",
                    "day_change_pct": 2.5,
                },
            ),
        ],
    )

    report, _candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=tmp_path / "audits",
        runtime_root=tmp_path / "runtime",
    )

    assert report["funnel"]["unique_scanner_promotion_count"] == 1
    assert report["day_change_distribution"]["1_5_to_3"] == 1


def test_postclose_excludes_non_krx_episode_from_ev(tmp_path):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    policy = OpeningRotationRuntimePolicy(target_date="2026-08-08")
    rows = _episode_rows(
        target_date="2026-08-08",
        index=1,
        profit_rate=1.0,
        day_change_pct=2.5,
        policy=policy,
    )
    for row in rows:
        row["fields"]["effective_venue"] = "NXT"
        row["fields"]["market_session_bucket"] = "nxt"
    _write_jsonl(events / "pipeline_events_2026-08-08.jsonl", rows)
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=tmp_path / "runtime",
    )

    assert report["funnel"]["strict_episode_count"] == 0
    assert report["funnel"]["non_krx_or_unknown_episode_scope_excluded_count"] == 1
    assert report["performance"]["source_quality_adjusted_ev_pct"] is None
    assert candidate["status"] == "no_change"


def test_preopen_materializes_prior_candidate_and_revalidates_hash(tmp_path):
    runtime = tmp_path / "runtime"
    candidates = runtime / "candidates"
    baseline = OpeningRotationRuntimePolicy(target_date="2026-08-09")
    proposed = replace(
        baseline,
        entry=replace(baseline.entry, min_day_change_pct=2.0),
    )
    runtime.mkdir(parents=True, exist_ok=True)
    runtime_policy_path("2026-08-09", root=runtime).write_text(
        json.dumps(baseline.as_artifact()), encoding="utf-8"
    )
    source_report = candidates / "report.json"
    _candidate_report(
        source_report,
        target_date="2026-08-09",
        baseline=baseline,
        axis="day_change_lower",
        value=2.0,
        proposed=proposed,
    )
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "artifact_type": "opening_rotation_runtime_policy_candidate",
        "target_date": "2026-08-09",
        "status": "eligible",
        "selected_axis": "day_change_lower",
        "selected_value": 2.0,
        "source_report_path": str(source_report),
        "source_quality_status": "pass",
        "source_active_policy_hash": baseline.policy_hash,
        "proposed_policy": proposed.as_artifact(),
    }
    path = candidate_path("2026-08-09", root=candidates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    policy, output = apply_preopen(
        "2026-08-10",
        runtime_root=runtime,
        candidate_root=candidates,
        now_dt=datetime.fromisoformat("2026-08-10T08:00:00+09:00"),
    )

    assert policy.entry.min_day_change_pct == 2.0
    assert policy.selected_axis == "day_change_lower"
    assert policy.target_date == "2026-08-10"
    assert load_runtime_policy(output).policy_hash == policy.policy_hash


def test_preopen_rejects_intraday_materialization(tmp_path):
    with pytest.raises(ValueError, match="PREOPEN"):
        apply_preopen(
            "2026-08-10",
            runtime_root=tmp_path / "runtime",
            candidate_root=tmp_path / "candidates",
            now_dt=datetime.fromisoformat("2026-08-10T09:00:00+09:00"),
        )


def test_preopen_carry_forward_preserves_prechange_rollback_origin(tmp_path):
    runtime = tmp_path / "runtime"
    candidates = runtime / "candidates"
    baseline = OpeningRotationRuntimePolicy(
        target_date="2026-08-08",
        applied_at_preopen="2026-08-08T08:00:00+09:00",
        profile_activated_at_preopen="2026-08-08T08:00:00+09:00",
        source_quality_status="PASS",
        profile_id="opening_rotation_baseline",
    )
    proposed = replace(
        baseline,
        entry=replace(baseline.entry, min_day_change_pct=2.0),
    )
    runtime.mkdir(parents=True, exist_ok=True)
    runtime_policy_path("2026-08-08", root=runtime).write_text(
        json.dumps(baseline.as_artifact()), encoding="utf-8"
    )
    source_report = candidates / "report.json"
    _candidate_report(
        source_report,
        target_date="2026-08-08",
        baseline=baseline,
        axis="day_change_lower",
        value=2.0,
        proposed=proposed,
    )
    path = candidate_path("2026-08-08", root=candidates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": REPORT_SCHEMA_VERSION,
                "artifact_type": "opening_rotation_runtime_policy_candidate",
                "target_date": "2026-08-08",
                "status": "eligible",
                "selected_axis": "day_change_lower",
                "selected_value": 2.0,
                "source_report_path": str(source_report),
                "source_quality_status": "pass",
                "source_active_policy_hash": baseline.policy_hash,
                "proposed_policy": proposed.as_artifact(),
            }
        ),
        encoding="utf-8",
    )

    changed, _ = apply_preopen(
        "2026-08-09",
        runtime_root=runtime,
        candidate_root=candidates,
        now_dt=datetime.fromisoformat("2026-08-09T08:00:00+09:00"),
    )
    carried, _ = apply_preopen(
        "2026-08-10",
        runtime_root=runtime,
        candidate_root=candidates,
        now_dt=datetime.fromisoformat("2026-08-10T08:00:00+09:00"),
    )

    assert changed.previous_policy_hash == baseline.policy_hash
    assert carried.previous_policy_hash == baseline.policy_hash
    assert carried.profile_id == changed.profile_id
    assert carried.source_report_path == str(source_report)
    assert carried.profile_activated_at_preopen == changed.profile_activated_at_preopen


def test_postclose_rollback_uses_first_ten_episodes_of_active_policy_only(
    tmp_path,
):
    events = tmp_path / "events"
    audits = tmp_path / "audits"
    runtime = tmp_path / "runtime"
    candidates = runtime / "candidates"
    runtime.mkdir(parents=True, exist_ok=True)

    previous = OpeningRotationRuntimePolicy(
        target_date="2026-08-07",
        applied_at_preopen="2026-08-07T08:00:00+09:00",
        source_quality_status="PASS",
        profile_id="opening_rotation_previous",
    )
    active = replace(
        previous,
        target_date="2026-08-08",
        applied_at_preopen="2026-08-08T08:00:00+09:00",
        profile_id="opening_rotation_active",
        previous_policy_hash=previous.policy_hash,
        entry=replace(previous.entry, min_day_change_pct=2.0),
    )
    runtime_policy_path("2026-08-07", root=runtime).write_text(
        json.dumps(previous.as_artifact()), encoding="utf-8"
    )
    runtime_policy_path("2026-08-08", root=runtime).write_text(
        json.dumps(active.as_artifact()), encoding="utf-8"
    )

    historical_rows: list[dict] = []
    for index in range(10):
        historical_rows.extend(
            _episode_rows(
                target_date="2026-08-07",
                index=index,
                profit_rate=1.0,
                day_change_pct=2.5,
                policy=previous,
            )
        )
    _write_jsonl(events / "pipeline_events_2026-08-07.jsonl", historical_rows)
    _audit(audits, "2026-08-07")

    active_rows: list[dict] = []
    for index in range(10, 20):
        active_rows.extend(
            _episode_rows(
                target_date="2026-08-08",
                index=index,
                profit_rate=-0.1,
                day_change_pct=2.5,
                policy=active,
            )
        )
    _write_jsonl(events / "pipeline_events_2026-08-08.jsonl", active_rows)
    _audit(audits, "2026-08-08")

    report, candidate = build_postclose_report(
        "2026-08-08",
        events_dir=events,
        source_quality_dir=audits,
        runtime_root=runtime,
    )

    assert report["rollback"]["active_policy_complete_episode_count"] == 10
    assert report["rollback"]["first_ten_source_quality_adjusted_ev_pct"] == -0.1
    assert report["rollback"]["triggered"] is True
    assert candidate["status"] == "rollback"
    assert candidate["proposed_policy"]["policy_hash"] == previous.policy_hash

    source_report = tmp_path / "rollback-report.json"
    source_report.write_text(json.dumps(report), encoding="utf-8")
    candidate["source_report_path"] = str(source_report)
    path = candidate_path("2026-08-08", root=candidates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidate), encoding="utf-8")
    applied, _output = apply_preopen(
        "2026-08-09",
        runtime_root=runtime,
        candidate_root=candidates,
        now_dt=datetime.fromisoformat("2026-08-09T08:00:00+09:00"),
    )
    assert applied.entry.min_day_change_pct == previous.entry.min_day_change_pct
    assert applied.selected_axis == "rollback"


def test_preopen_rejects_multi_axis_or_unverified_candidate(tmp_path):
    runtime = tmp_path / "runtime"
    candidates = runtime / "candidates"
    baseline = OpeningRotationRuntimePolicy(target_date="2026-08-09")
    tampered = replace(
        baseline,
        entry=replace(
            baseline.entry,
            min_day_change_pct=2.0,
            min_pullback_pct=0.4,
            max_pullback_pct=1.2,
        ),
    )
    runtime.mkdir(parents=True, exist_ok=True)
    runtime_policy_path("2026-08-09", root=runtime).write_text(
        json.dumps(baseline.as_artifact()), encoding="utf-8"
    )
    source_report = candidates / "report.json"
    _candidate_report(
        source_report,
        target_date="2026-08-09",
        baseline=baseline,
        axis="day_change_lower",
        value=2.0,
        proposed=tampered,
    )
    path = candidate_path("2026-08-09", root=candidates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": REPORT_SCHEMA_VERSION,
                "target_date": "2026-08-09",
                "status": "eligible",
                "selected_axis": "day_change_lower",
                "selected_value": 2.0,
                "source_report_path": str(source_report),
                "source_quality_status": "pass",
                "source_active_policy_hash": baseline.policy_hash,
                "proposed_policy": tampered.as_artifact(),
            }
        ),
        encoding="utf-8",
    )

    carried, _ = apply_preopen(
        "2026-08-10",
        runtime_root=runtime,
        candidate_root=candidates,
        now_dt=datetime.fromisoformat("2026-08-10T08:00:00+09:00"),
    )

    assert carried.entry == baseline.entry
    assert carried.selected_axis == "carry_forward"
    assert carried.source_quality_status == "runtime_default"


def test_write_and_verify_postclose_artifacts(tmp_path):
    report_root = tmp_path / "report"
    candidate_root = tmp_path / "candidates"
    paths = write_postclose(
        "2026-08-10",
        report_root=report_root,
        candidate_root=candidate_root,
        events_dir=tmp_path / "events",
        source_quality_dir=tmp_path / "audits",
        runtime_root=tmp_path / "runtime",
    )
    assert all(path.exists() for path in paths)
    result = verify_artifacts(
        "2026-08-10",
        report_root=report_root,
        candidate_root=candidate_root,
        runtime_root=tmp_path / "runtime",
        phase="postclose",
    )
    assert result["status"] == "pass"
