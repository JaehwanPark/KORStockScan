import json
import copy
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

from src.engine.trade_profit import (
    calculate_net_profit_rate, calculate_net_realized_pnl, get_trade_cost_rate,
)
from src.engine.scalping.initial_quantity_type import classify_quantity_type
from src.engine.scalping.entry_split_order_plan import (
    build_initial_quantity_type_legs,
)
from src.engine.scalping.initial_quantity_following_bars import (
    build_following_bar_source, following_bar_source_valid,
)
from src.engine.scalping.initial_quantity_activation import (
    ENV_FILE, ENV_SHA, baseline_policy_valid, build_initial_quantity_baseline,
    build_initial_quantity_runtime_v2, runtime_v2_policy_valid,
    load_pinned_baseline, select_initial_quantity_baseline,
    publish_initial_quantity_runtime_v2, select_initial_quantity_runtime_v2,
    selected_initial_quantity_env,
)

from src.engine.scalping.initial_quantity_policy import (
    _write_immutable_json,
    _digest,
    _paired_candidate,
    _fresh_observed_price,
    _type_from_decision_receipt,
    build_initial_quantity_policy,
    build_initial_quantity_replay,
    build_refresh_type_policy_candidate,
    completed_trade_fact_census,
    evaluate_refresh_quantity_candidate,
    publish_refresh_quantity_evaluation,
    refresh_quantity_stage_terminal_valid,
    initial_quantity_policy_valid,
    initial_quantity_stage_terminal_valid,
    main as initial_quantity_main,
    publish_initial_quantity_candidate,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _event(record_id: int, stage: str, at: str, **fields) -> dict:
    return {"record_id": record_id, "stock_code": "000001", "stage": stage,
            "emitted_at": at, "fields": fields}


def _quality(tmp_path: Path, day: str) -> None:
    path = (tmp_path / "report" / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": "pass", "target_date": day, "summary": {
        "hard_blocking_contract_gap_count": 0, "tuning_input_allowed": True}}),
        encoding="utf-8")


def _facts(rows: list[dict], exit_day: str) -> list[dict]:
    result = []
    for row in rows:
        sell_at = datetime.combine(datetime.fromisoformat(exit_day).date(),
                                   datetime.strptime(row["sell_time"], "%H:%M:%S").time(),
                                   ZoneInfo("Asia/Seoul"))
        buy_at = sell_at - timedelta(seconds=row["held_sec"])
        result.append({"recommendation_id": row["recommendation_id"],
                       "rec_date": buy_at.date().isoformat(),
                       "stock_code": row["stock_code"], "strategy": row["strategy"],
                       "position_tag": row["position_tag"], "status": "COMPLETED",
                       "buy_price": row["buy_price"], "buy_qty": row["buy_qty"],
                       "buy_time": buy_at.isoformat(), "sell_price": row["sell_price"],
                       "sell_time": sell_at.isoformat(),
                       "profit_rate": calculate_net_profit_rate(row["buy_price"], row["sell_price"]),
                       "realized_pnl_krw": calculate_net_realized_pnl(
                           row["buy_price"], row["sell_price"], row["buy_qty"]),
                       "add_count": 0, "avg_down_count": 0, "pyramid_count": 0})
    return result


@pytest.mark.parametrize("shape,count", [
    ("two_leg_0_0p3", 2), ("three_leg_0_0p3_0p8", 3),
    ("two_leg_0_1tick", 2), ("three_leg_0_1_2tick", 3),
])
@pytest.mark.parametrize("probe_first", [False, True])
def test_initial_quantity_type_leg_templates_preserve_total_and_probe(
        shape, count, probe_first):
    legs = build_initial_quantity_type_legs(
        total_qty=7, selected_shape=shape, probe_first=probe_first,
        route="KRX")
    assert len(legs) == count
    assert sum(leg["qty"] for leg in legs) == 7
    assert all(leg["price"] == 0 for leg in legs)
    assert all(leg["route"] == "KRX" for leg in legs)
    if probe_first:
        assert legs[0]["qty"] == 1
        assert legs[0]["tag"] == "initial_quantity_probe_0"
    else:
        assert legs[0]["qty"] == 4


def test_initial_quantity_type_leg_templates_reject_one_share_split():
    with pytest.raises(ValueError, match="quantity_insufficient"):
        build_initial_quantity_type_legs(
            total_qty=1, selected_shape="two_leg_0_1tick",
            probe_first=True, route="KRX")


@pytest.mark.parametrize("shape,leg_index,expected", [
    ("two_leg_0_1tick", 1, 9990),
    ("three_leg_0_1_2tick", 2, 9980),
    ("two_leg_0_0p3", 1, 9970),
    ("three_leg_0_0p3_0p8", 2, 9920),
])
def test_initial_quantity_p1_resolves_selected_successor_price(
        shape, leg_index, expected):
    from src.engine.sniper_entry_latency import resolve_scalping_entry_price

    result = resolve_scalping_entry_price(
        strategy_id="SCALPING", defensive_order_price=10000,
        target_buy_price=0, best_bid=9990, best_ask=10010,
        phase="initial_quantity_leg", probe_fill_price=10000,
        fresh_mark_price=10000, continuation_action="ALLOW_NORMAL",
        residual_leg_index=leg_index, initial_quantity_shape=shape,
    )
    assert result["allowed"] is True
    assert result["resolved_order_price"] == expected
    blocked = resolve_scalping_entry_price(
        strategy_id="SCALPING", defensive_order_price=10000,
        target_buy_price=0, best_bid=9990, best_ask=10010,
        phase="initial_quantity_leg", probe_fill_price=10000,
        continuation_action="BLOCK", residual_leg_index=leg_index,
        initial_quantity_shape=shape,
    )
    assert blocked["allowed"] is False


def test_first_parent_policy_can_be_selected_without_successor_uplift(
    tmp_path, monkeypatch,
):
    from src.engine.scalping.position_sizing_allocator import (
        resolve_scalping_allocation,
    )
    day = "2026-09-23"
    _quality(tmp_path, day)
    rows = [{
        "recommendation_id": 17, "stock_code": "000001",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "buy_price": 100, "sell_price": 101, "buy_qty": 4,
        "sell_time": "09:35:00", "held_sec": 300,
    }]
    report = build_initial_quantity_replay(
        day, data_dir=tmp_path, fact_rows=_facts(rows, day))
    source_only_stage = publish_initial_quantity_candidate(
        report, output_dir=tmp_path / "without_following")
    with pytest.raises(ValueError, match="winner_following_source_required"):
        build_initial_quantity_baseline(source_only_stage)
    following = build_following_bar_source(
        report, fetch=lambda code, base_dt, limit: (
            [{"source_timestamp": "20260923093200", "저가": 99}],
            {"api_id": "ka10080", "request_code": code,
             "request_base_dt": base_dt,
             "continuous_page_limit_reached": False}),
    )
    stage_dir = tmp_path / "stage"
    stage = publish_initial_quantity_candidate(
        report, output_dir=stage_dir, following_bars=following)
    assert all(row["selected_shape"] == "parent"
               for row in build_initial_quantity_policy(report)["type_policies"].values())
    baseline = build_initial_quantity_baseline(stage)
    assert baseline_policy_valid(baseline)
    malformed = {**baseline, "type_policies": list(baseline["type_policies"])}
    malformed["policy_content_sha256"] = _digest({
        key: value for key, value in malformed.items()
        if key != "policy_content_sha256"})
    assert not baseline_policy_valid(malformed)
    stage_path = stage_dir / f"initial_quantity_stage_{day}.json"
    current = select_initial_quantity_baseline(stage_path, tmp_path / "runtime")
    v2 = build_initial_quantity_runtime_v2(
        stage, baseline, current["current_content_sha256"])
    assert runtime_v2_policy_valid(v2)
    assert v2["parent_policy_content_sha256"] == baseline["policy_content_sha256"]
    assert v2["candidate_policy_content_sha256"] == stage[
        "candidate_policy_content_sha256"]
    assert all(row["ratio_mode"] == "parent_5stage"
               for row in v2["type_policies"].values())
    changed = copy.deepcopy(v2)
    changed["type_policies"]["SAFE_UNKNOWN"]["selected_shape"] = "two_leg_0_1tick"
    changed["policy_content_sha256"] = _digest({
        key: value for key, value in changed.items()
        if key != "policy_content_sha256"})
    assert not runtime_v2_policy_valid(changed)
    env = selected_initial_quantity_env(
        tmp_path / "runtime" / "current.json", "2026-09-24")
    assert current["policy_content_sha256"] == baseline["policy_content_sha256"]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    decision = resolve_scalping_allocation(_context_for_initial_baseline())
    assert decision.policy_status == "initial_policy_loaded"
    assert decision.ratio == pytest.approx(0.25)
    assert decision.policy_version == baseline["policy_version"]
    assert decision.event_fields()["quantity_type_policy_row"] == decision.quantity_type
    policy, status = load_pinned_baseline(
        Path(env[ENV_FILE]), env[ENV_SHA], datetime.fromisoformat(
            "2026-09-30").date())
    assert status == "initial_policy_loaded"
    assert policy == baseline
    monkeypatch.setenv(ENV_SHA, "0" * 64)
    assert resolve_scalping_allocation(
        _context_for_initial_baseline()).ratio == pytest.approx(0.10)
    v2_dir = tmp_path / "v2_runtime"
    parent_current = select_initial_quantity_baseline(stage_path, v2_dir)
    v2_path = publish_initial_quantity_runtime_v2(
        stage_path, v2_dir / "current.json", v2_dir)
    assert json.loads(v2_path.read_text()) == build_initial_quantity_runtime_v2(
        stage, baseline, parent_current["current_content_sha256"])
    selected_v2 = select_initial_quantity_runtime_v2(
        stage_path, v2_dir / "current.json")
    assert selected_v2["parent_current_sha256"] == parent_current[
        "current_content_sha256"]
    env_v2 = selected_initial_quantity_env(
        v2_dir / "current.json", "2026-09-30")
    with pytest.raises(ValueError, match="current_invalid"):
        selected_initial_quantity_env(
            v2_dir / "current.json", "2026-09-23")
    parent_archive = Path(selected_v2["parent_current_file"])
    parent_archive_bytes = parent_archive.read_bytes()
    assert json.loads(parent_archive_bytes) == parent_current
    parent_archive.write_text("{broken")
    with pytest.raises(ValueError, match="current_file_invalid"):
        selected_initial_quantity_env(
            v2_dir / "current.json", "2026-09-30")
    parent_archive.write_bytes(parent_archive_bytes)
    for key, value in env_v2.items():
        monkeypatch.setenv(key, value)
    decision_v2 = resolve_scalping_allocation(_context_for_initial_baseline())
    assert decision_v2.policy_status == "initial_policy_v2_loaded"
    assert decision_v2.ratio == pytest.approx(0.25)
    assert decision_v2.event_fields()["quantity_type_policy_row"] == (
        decision_v2.quantity_type)
    with pytest.raises(ValueError, match="parent_current_invalid"):
        publish_initial_quantity_runtime_v2(
            stage_path, v2_dir / "current.json", v2_dir)
    with pytest.raises(ValueError, match="parent_current_invalid"):
        select_initial_quantity_runtime_v2(
            stage_path, v2_dir / "current.json")
    with pytest.raises(ValueError, match="current_already_selected"):
        another = tmp_path / "other"
        another.mkdir()
        altered = dict(current)
        altered["source_date"] = "2026-09-22"
        # A second selection with changed bytes must be rejected.
        (tmp_path / "runtime" / "current.json").write_text(json.dumps(altered))
        select_initial_quantity_baseline(stage_path, tmp_path / "runtime")


def test_changed_initial_candidate_keeps_parent_rollback_and_builds_changed_v2(
        monkeypatch, tmp_path):
    from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES
    from src.engine.scalping import initial_quantity_policy as source

    candidate = {
        "source_date": "2026-09-23", "effective_from": "2026-09-24",
        "following_bar_source_content_sha256": "a" * 64,
        "policy_content_sha256": "b" * 64,
        "report_content_sha256": "c" * 64,
        "input_manifest_sha256": "d" * 64,
        "all_completed_initial_trades": 1,
        "classifier_version": "initial_quantity_type_v1",
        "type_policies": {name: {
            "ratio_mode": "parent_5stage",
            "selected_shape": ("two_leg_0_1tick" if name == "KRX_PARENT"
                               else "parent"),
            "timeout_mode": "existing_runtime_profile",
            "selected_total_wait_sec": None,
        } for name in QUANTITY_TYPES},
    }
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate))
    stage = {
        "candidate_policy_path": str(candidate_path),
        "following_bar_source_path": str(tmp_path / "following.json"),
        "candidate_policy_file_sha256": "e" * 64,
        "receipt_content_sha256": "f" * 64,
    }
    # This unit isolates activation after the producer's strict stage check.
    monkeypatch.setattr(source, "initial_quantity_stage_terminal_valid",
                        lambda value: value is stage)
    baseline = build_initial_quantity_baseline(stage)
    assert baseline_policy_valid(baseline)
    assert baseline["type_policies"]["KRX_PARENT"]["selected_shape"] == "parent"
    v2 = build_initial_quantity_runtime_v2(stage, baseline, "1" * 64)
    assert runtime_v2_policy_valid(v2)
    assert v2["type_policies"]["KRX_PARENT"]["selected_shape"] == (
        "two_leg_0_1tick")


def test_refresh_runtime_pointer_binds_parent_and_changed_type(
        monkeypatch, tmp_path):
    import hashlib
    from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES
    from src.engine.scalping import initial_quantity_policy as source
    from src.engine.scalping.position_sizing_allocator import (
        resolve_scalping_allocation,
    )
    from src.engine.scalping.initial_quantity_activation import (
        build_initial_quantity_refresh_runtime_policy,
        runtime_refresh_policy_valid,
    )

    initial_candidate = {
        "source_date": "2026-09-23", "effective_from": "2026-09-24",
        "following_bar_source_content_sha256": "a" * 64,
        "policy_content_sha256": "b" * 64,
        "report_content_sha256": "c" * 64,
        "input_manifest_sha256": "d" * 64,
        "all_completed_initial_trades": 1,
        "classifier_version": "initial_quantity_type_v1",
        "type_policies": {name: {
            "ratio_mode": "parent_5stage", "selected_shape": "parent",
            "timeout_mode": "existing_runtime_profile",
            "selected_total_wait_sec": None,
        } for name in QUANTITY_TYPES},
    }
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    seed_candidate_path = seed_dir / "candidate.json"
    seed_candidate_path.write_text(json.dumps(initial_candidate))
    seed_stage = {
        "candidate_policy_path": str(seed_candidate_path.resolve()),
        "following_bar_source_path": str((seed_dir / "following.json").resolve()),
        "candidate_policy_file_sha256": "e" * 64,
        "receipt_content_sha256": "f" * 64,
    }
    seed_stage_path = seed_dir / "stage.json"
    seed_stage_path.write_text(json.dumps(seed_stage))
    monkeypatch.setattr(source, "initial_quantity_stage_terminal_valid",
                        lambda value: value == seed_stage)
    current_path = tmp_path / "runtime" / "current.json"
    current = select_initial_quantity_baseline(
        seed_stage_path, current_path.parent)
    parent = json.loads(Path(current["policy_file"]).read_text())

    refresh_dir = tmp_path / "refresh"
    refresh_dir.mkdir()
    refresh_candidate = {
        "source_date": "2026-09-25", "effective_from": "2026-09-26",
        "parent_policy_content_sha256": parent["policy_content_sha256"],
        "policy_content_sha256": "1" * 64,
        "type_policies": {name: {
            "ratio_mode": "parent_5stage",
            "selected_shape": ("two_leg_0_1tick" if name == "KRX_PARENT"
                               else "parent"),
            "timeout_mode": "existing_runtime_profile",
            "selected_total_wait_sec": None,
        } for name in QUANTITY_TYPES},
    }
    candidate_path = refresh_dir / "candidate.json"
    candidate_path.write_text(json.dumps(refresh_candidate))
    report_path = refresh_dir / "report.json"
    report_path.write_text(json.dumps({
        "census": {"input_manifest_sha256": "2" * 64}}))
    refresh_stage = {
        "schema_version": "initial_entry_quantity_refresh_stage_v1",
        "decision": "eligible_source_only",
        "source_date": "2026-09-25",
        "candidate_path": str(candidate_path.resolve()),
        "candidate_file_sha256": hashlib.sha256(
            candidate_path.read_bytes()).hexdigest(),
        "parent_policy_content_sha256": parent["policy_content_sha256"],
        "report_path": str(report_path.resolve()),
        "report_content_sha256": "3" * 64,
        "evaluation_content_sha256": "4" * 64,
        "timeout_research_content_sha256": "5" * 64,
        "following_bar_source_status": "source_bound",
        "following_bar_source_content_sha256": "6" * 64,
        "all_completed_initial_trades": 31,
        "receipt_content_sha256": "7" * 64,
    }
    stage_path = refresh_dir / "stage.json"
    stage_path.write_text(json.dumps(refresh_stage))
    monkeypatch.setattr(source, "refresh_quantity_stage_terminal_valid",
                        lambda value: value == refresh_stage)
    candidate = build_initial_quantity_refresh_runtime_policy(
        refresh_stage, parent, current["current_content_sha256"])
    assert runtime_refresh_policy_valid(candidate)
    assert candidate["type_policies"]["KRX_PARENT"]["selected_shape"] == (
        "two_leg_0_1tick")
    selected = select_initial_quantity_runtime_v2(stage_path, current_path)
    assert selected["parent_current_sha256"] == current[
        "current_content_sha256"]
    env = selected_initial_quantity_env(current_path, "2026-09-26")
    assert env[ENV_FILE] == selected["policy_file"]
    assert env[ENV_SHA] == selected["policy_file_sha256"]
    with pytest.raises(ValueError):
        select_initial_quantity_runtime_v2(stage_path, current_path)
    second_parent = json.loads(Path(selected["policy_file"]).read_text())
    second_candidate = copy.deepcopy(refresh_candidate)
    second_candidate.update(
        source_date="2026-09-27", effective_from="2026-09-28",
        parent_policy_content_sha256=second_parent["policy_content_sha256"],
        policy_content_sha256="8" * 64)
    second_candidate["type_policies"]["KRX_THIN_HIGH_TICK"][
        "selected_shape"] = "two_leg_0_1tick"
    second_candidate["type_policies"]["KRX_PARENT"][
        "ratio_mode"] = "cap_15pct"
    second_candidate["type_policies"]["KRX_PARENT"].update(
        timeout_mode="selected_total_wait_sec", selected_total_wait_sec=90)
    second_candidate_path = refresh_dir / "candidate_second.json"
    second_candidate_path.write_text(json.dumps(second_candidate))
    second_stage = {
        **refresh_stage, "source_date": "2026-09-27",
        "candidate_path": str(second_candidate_path.resolve()),
        "candidate_file_sha256": hashlib.sha256(
            second_candidate_path.read_bytes()).hexdigest(),
        "parent_policy_content_sha256": second_parent["policy_content_sha256"],
        "receipt_content_sha256": "9" * 64,
    }
    second_stage_path = refresh_dir / "stage_second.json"
    second_stage_path.write_text(json.dumps(second_stage))
    monkeypatch.setattr(source, "refresh_quantity_stage_terminal_valid",
                        lambda value: value in (refresh_stage, second_stage))
    selected_second = select_initial_quantity_runtime_v2(
        second_stage_path, current_path)
    assert selected_second["parent_current_sha256"] == selected[
        "current_content_sha256"]
    second_env = selected_initial_quantity_env(current_path, "2026-09-28")
    assert second_env[ENV_FILE] == selected_second["policy_file"]
    for key, value in second_env.items():
        monkeypatch.setenv(key, value)
    capped = resolve_scalping_allocation(_context_for_initial_baseline())
    assert capped.policy_status == "initial_policy_refresh_loaded"
    assert capped.quantity_type == "KRX_PARENT"
    assert capped.ratio == pytest.approx(0.15)
    assert capped.event_fields()["quantity_type_policy_row"] == "KRX_PARENT"
    from src.engine import sniper_state_handlers as handler
    class EffectiveDateClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(
                "2026-09-28T09:30:00+09:00").astimezone(tz)
    monkeypatch.setattr(handler, "datetime", EffectiveDateClock)
    stock = {
        "id": 101, "scalping_sizing_quantity_type": capped.quantity_type,
        "scalping_sizing_quantity_type_policy_row": capped.event_fields()[
            "quantity_type_policy_row"],
        "scalping_sizing_position_sizing_policy_sha256": second_env[ENV_SHA],
        "scalping_sizing_reference_time": "2026-09-28T09:29:50+09:00",
        "effective_venue": "KRX",
    }
    orders, _ = handler._initial_quantity_sequential_plan(
        stock, [{"qty": 5, "price": 10000, "tag": "parent",
                 "dmst_stex_tp": "KRX"}], 5, {})
    assert orders[0]["initial_quantity_sequential_continuation"][
        "total_wait_sec"] == 90


def test_refresh_wait_selection_requires_exact_start_and_dated_costed_edge():
    from src.engine.scalping.initial_quantity_policy import (
        _eligible_refresh_total_wait,
    )

    rows = [{"quantity_type": "KRX_PARENT", "actual_net_pnl_krw": 100,
             "entry_date": f"2026-09-{24 + index // 10:02d}"}
            for index in range(30)]
    supported = {
        "modeled_count": 30, "verified_cross_count": 3,
        "order_start_source_counts": {
            "initial_quantity_bundle_order_start_at": 30},
        "conservative_ev_pct": 0.8,
        "conservative_net_pnl_krw": 3100,
        "daily_conservative_delta_net_pnl_krw": {
            "2026-09-24": 30, "2026-09-25": 30,
            "2026-09-26": 40},
    }
    research = {"horizons_sec": [60, 90], "selections": {
        "KRX_PARENT": {"parent_costed_ev_pct": 0.5,
                       "candidate_metrics": {
                           "two_leg_0_1tick:5:60": {
                               **supported, "conservative_ev_pct": 1.0,
                               "order_start_source_counts": {
                                   "entry_cancel_wait_submission_context_frozen_at":
                                   30}},
                           "two_leg_0_1tick:5:90": supported}}}}
    assert _eligible_refresh_total_wait(
        {"trades": rows}, research, "KRX_PARENT",
        "two_leg_0_1tick", 30) == 90
    research["selections"]["KRX_PARENT"]["candidate_metrics"][
        "two_leg_0_1tick:5:90"]["daily_conservative_delta_net_pnl_krw"][
            "2026-09-25"] = -1
    assert _eligible_refresh_total_wait(
        {"trades": rows}, research, "KRX_PARENT",
        "two_leg_0_1tick", 30) is None


def _context_for_initial_baseline():
    from src.engine.scalping.position_sizing_allocator import ScalpingSizingContext
    return ScalpingSizingContext(
        allocation_stage="initial_entry",
        reference_time=datetime.fromisoformat("2026-09-30T10:00:00+09:00"),
        source_signature="A,B,C", effective_venue="KRX",
        budget_base_krw=10_000_000, price_krw=10_000,
    )


def test_all_completed_trades_remain_in_denominator_and_no_cross_costs(tmp_path):
    day = "2026-09-23"
    _quality(tmp_path, day)
    terminal_rows = [
        {"post_sell_id": "a", "recommendation_id": 11, "signal_date": day,
         "stock_code": "000001", "strategy": "SCALPING", "position_tag": "SCANNER",
         "actual_order_submitted": True, "buy_price": 100, "sell_price": 110,
         "buy_qty": 4, "profit_rate": 9.7, "sell_time": "09:35:00", "held_sec": 300},
        {"post_sell_id": "b", "recommendation_id": 12, "signal_date": day,
         "stock_code": "000001", "strategy": "SCALPING", "position_tag": "SCANNER",
         "actual_order_submitted": True, "buy_price": 100, "sell_price": 90,
         "buy_qty": 4, "profit_rate": -10.3, "sell_time": "09:35:00", "held_sec": 300},
    ]
    _write_jsonl(tmp_path / "post_sell" / f"post_sell_evaluations_{day}.jsonl", terminal_rows)
    facts = _facts(terminal_rows, day)
    events = []
    for rid in (11, 12):
        events.extend([
            _event(rid, "entry_execution_sizing_plan", f"{day}T09:29:00+09:00",
                   entry_execution_sizing_valid=True, effective_venue="KRX",
                   market_session_bucket="krx_regular", source_signature="OPEN_TOP",
                   reference_time=f"{day}T09:29:00+09:00", current_price=100,
                   classifier_route_key="KRX_0D", classifier_transport_epoch="epoch-1"),
            _event(rid, "position_rebased_after_fill", f"{day}T09:30:00+09:00",
                   entry_mode="normal", fill_price=100, fill_qty=4,
                   order_no=str(rid), execution_no="one", actual_execution_venue="KRX",
                   broker_execution_observed_at=f"{day}T09:30:00+09:00"),
            _event(rid, "holding_quote", f"{day}T09:31:00+09:00",
                   current_price_observed=1, latest_price=98 if rid == 11 else 101,
                   ws_age_ms=100, effective_venue="KRX",
                   classifier_route_key="KRX_0D", classifier_transport_epoch="epoch-1"),
        ])
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", events)
    performance = {}
    report = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=facts,
                                           performance=performance)
    assert performance["census_count"] == 2
    assert performance["trade_evaluation_p99_ms"] >= 0
    assert report["report_content_sha256"] == build_initial_quantity_replay(
        day, data_dir=tmp_path, fact_rows=facts)["report_content_sha256"]
    assert report["census"]["all_completed_initial_trades"] == 2
    assert report["pipeline_source_receipts"][day]["stable_during_scan"] is True
    assert report["census"]["actual_completed_net_pnl_krw"] == sum(
        fact["realized_pnl_krw"] for fact in facts)
    assert {row["stock_code"] for row in report["trades"]} == {"000001"}
    assert report["replay_counts"]["two_leg_0_1tick:paired"] == 2
    rows = {row["trade_id"]: row for row in report["trades"]}
    assert rows["fact:11"]["shapes"]["two_leg_0_1tick"]["fill_state"] == "price_cross_conditional"
    assert rows["fact:12"]["shapes"]["two_leg_0_1tick"]["fill_state"] == "no_cross_observed"
    assert rows["fact:12"]["shapes"]["two_leg_0_1tick"]["candidate_net_pct"] != facts[1]["profit_rate"]
    assert rows["fact:11"]["shapes"]["two_leg_0_1tick"]["candidate_net_pnl_krw"] > 0
    assert rows["fact:11"]["shapes"]["two_leg_0_0p3"]["status"] == "price_offset_collapsed"
    assert report["selections"]["KRX_THIN_HIGH_TICK"]["selected_shape"] == "parent"
    winner_selection = report["selections"]["KRX_THIN_HIGH_TICK"]
    assert winner_selection["winner_count"] == 1
    assert winner_selection["winner_weight_kind"] == "positive_realized_net_pnl_krw"
    assert winner_selection["winner_weight_sum_krw"] == facts[0]["realized_pnl_krw"]
    assert winner_selection["winner_weighted_parent_ev_pct"] == round(
        facts[0]["profit_rate"], 6)
    assert winner_selection["candidate_metrics"]["two_leg_0_1tick"][
        "winner_weighted_conservative_ev_pct"] == round(
            rows["fact:11"]["shapes"]["two_leg_0_1tick"]["conservative_net_pct"], 6)
    calls = []
    def fetch_following(code, base_dt, limit):
        calls.append((code, base_dt, limit))
        return ([{"source_timestamp": "20260923093000", "저가": 100},
                 {"source_timestamp": "20260923093200", "저가": 99},
                 {"source_timestamp": "20260923093300", "저가": 98},
                 {"source_timestamp": "20260923093400", "저가": 100}],
                {"api_id": "ka10080", "request_code": code,
                 "request_base_dt": base_dt,
                 "continuous_page_limit_reached": True})
    following = build_following_bar_source(report, fetch=fetch_following)
    assert calls == [("000001", "20260923", 900)]
    assert following["winner_count"] == 1
    assert following["trades"]["fact:11"]["first_lower_elapsed_from_fill_minute"] == 2
    assert following["weighted_by_type"]["KRX_THIN_HIGH_TICK"][
        "weighted_lower_elapsed_from_fill_minute"] == 2
    assert following["runtime_apply_allowed"] is False
    assert following["sources"]["2026-09-23:000001"]["older_pages_unfetched"] is True
    assert following_bar_source_valid(following, report)
    enriched_policy = build_initial_quantity_policy(report, following_bars=following)
    assert initial_quantity_policy_valid(enriched_policy, report=report,
                                         following_bars=following)
    assert not initial_quantity_policy_valid(enriched_policy, report=report)
    assert enriched_policy["type_policies"]["KRX_THIN_HIGH_TICK"][
        "following_weighted_lower_from_fill_minute"] == 2
    enriched_receipt = publish_initial_quantity_candidate(
        report, output_dir=tmp_path / "enriched", following_bars=following)
    assert initial_quantity_stage_terminal_valid(enriched_receipt)
    replay_file = tmp_path / "replay.json"
    following_file = tmp_path / "following.json"
    replay_file.write_text(json.dumps(report), encoding="utf-8")
    following_file.write_text(json.dumps(following), encoding="utf-8")
    assert initial_quantity_main([
        "--replay", str(replay_file), "--following-bars", str(following_file),
        "--output-dir", str(tmp_path / "cli_enriched")]) == 0
    assert initial_quantity_stage_terminal_valid(json.loads((
        tmp_path / "cli_enriched" / f"initial_quantity_stage_{day}.json").read_text()))
    tampered_following = copy.deepcopy(following)
    tampered_following["weighted_by_type"]["KRX_THIN_HIGH_TICK"][
        "weighted_lower_elapsed_from_fill_minute"] = 1
    tampered_following["report_content_sha256"] = _digest({
        key: value for key, value in tampered_following.items()
        if key != "report_content_sha256"})
    assert not following_bar_source_valid(tampered_following, report)
    incomplete = build_following_bar_source(report, fetch=lambda code, day, limit: (
        [{"source_timestamp": "20260923093400", "저가": 99}],
        {"api_id": "ka10080", "request_code": code,
         "request_base_dt": day, "continuous_page_limit_reached": True}))
    assert incomplete["trades"]["fact:11"]["status"] == "bar_window_source_gap"
    assert following_bar_source_valid(incomplete, report)
    proxy_clock = copy.deepcopy(report)
    proxy_clock["trades"][0]["entry_fill_clock_source"] = (
        "position_rebased_emitted_at_proxy")
    proxy_clock["report_content_sha256"] = _digest({
        key: value for key, value in proxy_clock.items()
        if key != "report_content_sha256"})
    proxy_following = build_following_bar_source(proxy_clock, fetch=fetch_following)
    assert proxy_following["trades"]["fact:11"]["clock_quality"] == (
        "fact_buy_time_proxy")
    assert proxy_following["weighted_by_type"]["KRX_THIN_HIGH_TICK"][
        "observed_minute_lower_count"] == 1
    conflicting = copy.deepcopy(report)
    conflicting["census"]["input_fact_rows"].append(
        {**facts[0], "stock_code": "999999"})
    conflicting["census"]["input_manifest_sha256"] = _digest(
        conflicting["census"]["input_fact_rows"])
    conflicting["report_content_sha256"] = _digest({
        key: value for key, value in conflicting.items()
        if key != "report_content_sha256"})
    assert build_following_bar_source(conflicting, fetch=fetch_following)["trades"][
        "fact:11"]["status"] == "fact_identity_missing"
    assert report["selections"]["KRX_THIN_HIGH_TICK"]["candidate_metrics"][
        "two_leg_0_1tick"]["verified_route_epoch_price_cross_count"] == 1
    policy = build_initial_quantity_policy(report)
    assert initial_quantity_policy_valid(policy, report=report)
    assert not initial_quantity_policy_valid(policy)
    assert policy["runtime_apply_allowed"] is False
    assert not initial_quantity_policy_valid({**policy, "runtime_apply_allowed": True})
    optimistic_bound_report = copy.deepcopy(report)
    optimistic_bound_shape = optimistic_bound_report["trades"][0]["shapes"]["two_leg_0_1tick"]
    optimistic_bound_shape["conservative_net_pct"] = optimistic_bound_shape["candidate_net_pct"] + 0.1
    optimistic_bound_report["report_content_sha256"] = _digest({
        key: value for key, value in optimistic_bound_report.items()
        if key != "report_content_sha256"})
    with pytest.raises(ValueError, match="initial_replay_economics_invalid"):
        build_initial_quantity_policy(optimistic_bound_report)
    inflated_metric_report = copy.deepcopy(report)
    inflated_metric_report["selections"]["KRX_THIN_HIGH_TICK"]["candidate_metrics"][
        "two_leg_0_1tick"]["estimated_net_pnl_krw"] += 100
    inflated_metric_report["report_content_sha256"] = _digest({
        key: value for key, value in inflated_metric_report.items()
        if key != "report_content_sha256"})
    with pytest.raises(ValueError, match="initial_replay_economics_invalid"):
        build_initial_quantity_policy(inflated_metric_report)
    forged_cross_report = copy.deepcopy(report)
    forged_cross_report["selections"]["KRX_THIN_HIGH_TICK"]["candidate_metrics"][
        "two_leg_0_1tick"]["verified_route_epoch_price_cross_count"] += 1
    forged_cross_report["report_content_sha256"] = _digest({
        key: value for key, value in forged_cross_report.items()
        if key != "report_content_sha256"})
    with pytest.raises(ValueError, match="initial_replay_economics_invalid"):
        build_initial_quantity_policy(forged_cross_report)
    inflated_weight_report = copy.deepcopy(report)
    inflated_weight_report["selections"]["KRX_THIN_HIGH_TICK"][
        "winner_weighted_parent_ev_pct"] += 1
    inflated_weight_report["report_content_sha256"] = _digest({
        key: value for key, value in inflated_weight_report.items()
        if key != "report_content_sha256"})
    with pytest.raises(ValueError, match="initial_replay_economics_invalid"):
        build_initial_quantity_policy(inflated_weight_report)
    forged_selection_report = copy.deepcopy(report)
    forged_selection_report["selections"]["KRX_THIN_HIGH_TICK"][
        "selected_shape"] = "two_leg_0_1tick"
    forged_selection_report["report_content_sha256"] = _digest({
        key: value for key, value in forged_selection_report.items()
        if key != "report_content_sha256"})
    with pytest.raises(ValueError, match="initial_replay_economics_invalid"):
        build_initial_quantity_policy(forged_selection_report)
    changed_report = {**report, "selections": {**report["selections"],
                      "SAFE_UNKNOWN": {**report["selections"]["SAFE_UNKNOWN"],
                                       "selected_shape": "two_leg_0_1tick"}}}
    assert not initial_quantity_policy_valid(policy, report=changed_report)
    events[2]["fields"]["classifier_transport_epoch"] = "stale-epoch"
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", events)
    unverified = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=facts)
    assert unverified["selections"]["KRX_THIN_HIGH_TICK"]["selected_shape"] == "parent"
    events[2]["fields"]["classifier_transport_epoch"] = "epoch-1"
    events[2]["fields"]["latest_price"] = 101
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", events)
    no_cross = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=facts)
    assert no_cross["selections"]["KRX_THIN_HIGH_TICK"]["selected_shape"] == "parent"
    events[5]["fields"]["latest_price"] = 98
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", events)
    loss_cross = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=facts)
    loss_shape = next(row for row in loss_cross["trades"] if row["record_id"] == "12")[
        "shapes"]["two_leg_0_1tick"]
    assert loss_shape["fill_state"] == "price_cross_conditional"
    assert loss_shape["conservative_net_pct"] == loss_shape["candidate_net_pct"]
    assert loss_shape["conservative_net_pnl_krw"] == loss_shape["candidate_net_pnl_krw"]
    assert loss_shape["upper_net_pct"] > loss_shape["candidate_net_pct"]


def test_initial_shape_uses_winner_weight_without_successor_uplift_gate():
    from src.engine.scalping.initial_quantity_policy import (
        _select_initial_winner_shape,
    )

    metrics = {
        "parent": {"winner_weighted_conservative_ev_pct": 1.0},
        "two_leg_0_1tick": {
            "state": "paired_with_parent_fallback",
            "winner_comparable_count": 1,
            "winner_weighted_conservative_ev_pct": 1.2,
            "verified_route_epoch_price_cross_count": 0,
            "conservative_ev_pct": -0.5,
        },
    }
    assert _select_initial_winner_shape("KRX_THIN_HIGH_TICK", metrics) == (
        "two_leg_0_1tick")
    assert _select_initial_winner_shape("SAFE_UNKNOWN", metrics) == "parent"
    metrics["two_leg_0_1tick"]["winner_comparable_count"] = 0
    assert _select_initial_winner_shape("KRX_THIN_HIGH_TICK", metrics) == "parent"


def test_fact_census_rejects_open_positions_and_uncosted_profit_rates(tmp_path):
    day = "2026-09-23"
    base = _facts([{"recommendation_id": 3, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    rows, census = completed_trade_fact_census(day, data_dir=tmp_path,
        fact_rows=[base, {**base, "recommendation_id": 4, "status": "HOLDING"},
                   {**base, "recommendation_id": 5, "profit_rate": 0.0}])
    assert len(rows) == census["all_completed_initial_trades"] == 1
    assert census["excluded"]["not_completed"] == 1
    assert census["excluded"]["terminal_cost_contract_mismatch"] == 1


def test_fact_quality_block_keeps_completed_trade_in_census(tmp_path):
    day = "2026-09-23"
    fact = _facts([{"recommendation_id": 7, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    quality = (tmp_path / "report" / "observation_source_quality_audit"
               / f"observation_source_quality_audit_{day}.json")
    quality.parent.mkdir(parents=True)
    quality.write_text(json.dumps({"status": "warning", "target_date": day, "summary": {
        "hard_blocking_contract_gap_count": "1"}}), encoding="utf-8")
    report = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=[fact])
    assert report["census"]["all_completed_initial_trades"] == 1
    assert report["replay_counts"]["parent:source_quality_blocked"] == 1
    following = build_following_bar_source(
        report, fetch=lambda *_: pytest.fail("blocked source must not call provider"))
    assert following["winner_count"] == 1
    assert following["request_count"] == 0
    assert following["trades"]["fact:7"]["status"] == "parent_source_quality_blocked"
    with pytest.raises(ValueError, match="completed_parent_economics_missing"):
        build_initial_quantity_policy(report)


def test_type_coverage_keeps_source_quality_blocked_trade_in_denominator(tmp_path):
    allowed_day, blocked_day = "2026-09-22", "2026-09-23"
    _quality(tmp_path, allowed_day)
    facts = []
    for rid, day in ((71, allowed_day), (72, blocked_day)):
        facts.extend(_facts([{"recommendation_id": rid, "stock_code": "000001",
                              "strategy": "SCALPING", "position_tag": "SCANNER",
                              "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                              "sell_time": "09:35:00", "held_sec": 300}], day))
    report = build_initial_quantity_replay(blocked_day, data_dir=tmp_path,
                                           fact_rows=facts)
    assert report["census"]["all_completed_initial_trades"] == 2
    assert report["replay_counts"]["parent:source_quality_blocked"] == 1
    assert report["selections"]["SAFE_UNKNOWN"]["candidate_metrics"]["parent"]["coverage_of_type"] == 0.5
    assert report["selections"]["SAFE_UNKNOWN"]["candidate_metrics"]["parent"]["coverage_of_all_completed"] == 0.5


def test_source_quality_requires_exact_date_and_explicit_tuning_allowance(tmp_path):
    day = "2026-09-23"
    fact = _facts([{"recommendation_id": 7, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    quality = (tmp_path / "report" / "observation_source_quality_audit"
               / f"observation_source_quality_audit_{day}.json")
    quality.parent.mkdir(parents=True)
    for audit in (
        {"status": "pass", "target_date": "2026-09-22", "summary": {
            "tuning_input_allowed": True, "hard_blocking_contract_gap_count": 0}},
        {"status": "pass", "target_date": day, "summary": {
            "hard_blocking_contract_gap_count": 0}},
        {"status": "pass", "target_date": day, "summary": {
            "tuning_input_allowed": True}},
    ):
        quality.write_text(json.dumps(audit), encoding="utf-8")
        report = build_initial_quantity_replay(day, data_dir=tmp_path,
                                               fact_rows=[fact])
        assert report["census"]["all_completed_initial_trades"] == 1
        assert report["replay_counts"]["parent:source_quality_blocked"] == 1


def test_split_anchor_uses_first_fill_and_original_notional_for_ev():
    entry_at = datetime.fromisoformat("2026-09-23T09:30:00+09:00")
    trade = {"entry_date": "2026-09-23", "entry_at_fact_buy_time": entry_at.isoformat(),
             "exit_at": (entry_at + timedelta(minutes=5)).isoformat(),
             "buy_price": 100.0, "sell_price": 101.0, "buy_qty": 4,
             "profit_rate": calculate_net_profit_rate(100, 101),
             "realized_net_pnl_krw": calculate_net_realized_pnl(100, 101, 4)}
    path = {"source_gap": [],
            "decisions": [{"at": entry_at - timedelta(seconds=1),
                           "stage": "entry_execution_sizing_plan",
                           "fields": {"effective_venue": "KRX",
                                      "market_session_bucket": "krx_regular",
                                      "source_signature": "A",
                                      "classifier_route_key": "KRX_0D",
                                      "classifier_transport_epoch": "epoch-1"}}],
            "fills": [{"at": entry_at, "price": 99.0, "qty": 2, "venue": "KRX",
                       "order_no": "1", "execution_no": "a", "clock_source": "broker_execution_observed_at"},
                      {"at": entry_at + timedelta(seconds=1), "price": 101.0,
                       "qty": 2, "venue": "KRX", "order_no": "1",
                       "execution_no": "b", "clock_source": "broker_execution_observed_at"}],
            "prices": [{"at": entry_at + timedelta(seconds=30), "price": 97.0,
                        "venue": "KRX", "route": "KRX_0D", "epoch": "epoch-1"}]}
    result = _paired_candidate(trade, path, "two_leg_0_1tick")
    assert result["status"] == "paired"
    assert result["counterfactual_anchor_price"] == 99.0
    assert result["parent_avg_buy_price"] == 100.0
    assert result["candidate_notional_denominator_krw"] == 400.0
    assert result["candidate_net_pnl_krw"] == pytest.approx(
        4 * 101 - (2 * 99 + 2 * 98) - get_trade_cost_rate() * (4 * 101),
        abs=0.001)
    assert result["candidate_net_pnl_krw"] > trade["realized_net_pnl_krw"]
    assert result["verified_route_epoch_price_cross_count"] == 1
    assert result["candidate_net_pct"] == pytest.approx(
        result["candidate_net_pnl_krw"] / 400.0 * 100, abs=0.001)
    path["fills"][0]["clock_source"] = "position_rebased_emitted_at_proxy"
    assert _paired_candidate(trade, path, "two_leg_0_1tick")[
        "verified_route_epoch_price_cross_count"] == 0
    path["fills"] = [{**path["fills"][0], "price": 99.5, "qty": 4}]
    assert _paired_candidate(trade, path, "two_leg_0_1tick")["status"] == "entry_anchor_not_tick_aligned"


def test_completed_parent_economics_survive_missing_pipeline_join(tmp_path):
    day = "2026-09-23"
    _quality(tmp_path, day)
    fact = _facts([{"recommendation_id": 7, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    report = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=[fact])
    assert report["replay_counts"]["parent:paired"] == 1
    assert report["trades"][0]["quantity_type"] == "SAFE_UNKNOWN"
    assert report["trades"][0]["shapes"]["two_leg_0_1tick"]["status"] == "path_source_gap"
    assert report["trades"][0]["source_gap"] == ["pipeline_missing"]


def test_immutable_stage_receipt_binds_report_candidate_and_rejects_conflict(tmp_path):
    day = "2026-09-23"
    _quality(tmp_path, day)
    fact = _facts([{"recommendation_id": 7, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    report = build_initial_quantity_replay(day, data_dir=tmp_path,
                                           fact_rows=[fact])
    output_dir = tmp_path / "published"
    receipt = publish_initial_quantity_candidate(report, output_dir=output_dir)
    assert receipt == publish_initial_quantity_candidate(report, output_dir=output_dir)
    assert initial_quantity_stage_terminal_valid(receipt)
    assert receipt["all_completed_initial_trades"] == 1
    assert receipt["runtime_apply_allowed"] is False
    assert json.loads(Path(receipt["report_path"]).read_text()) == report
    assert initial_quantity_policy_valid(
        json.loads(Path(receipt["candidate_policy_path"]).read_text()), report=report)
    Path(receipt["candidate_policy_path"]).write_text("{}", encoding="utf-8")
    assert not initial_quantity_stage_terminal_valid(receipt)
    with pytest.raises(ValueError, match="immutable_artifact_conflict"):
        publish_initial_quantity_candidate(report, output_dir=output_dir)


def test_refresh_uses_only_new_entries_and_requires_post_apply_receipts(
    tmp_path, monkeypatch,
):
    prior_day, new_day = "2026-09-22", "2026-09-23"
    _quality(tmp_path, prior_day)
    _quality(tmp_path, new_day)
    before = _facts([{"recommendation_id": 11, "stock_code": "000001",
                      "strategy": "SCALPING", "position_tag": "SCANNER",
                      "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                      "sell_time": "09:35:00", "held_sec": 300}], prior_day)
    after = _facts([{"recommendation_id": 12, "stock_code": "000001",
                     "strategy": "SCALPING", "position_tag": "SCANNER",
                     "buy_price": 100, "sell_price": 99, "buy_qty": 4,
                     "sell_time": "09:35:00", "held_sec": 300}], new_day)
    seed_report = build_initial_quantity_replay(prior_day, data_dir=tmp_path,
                                                fact_rows=before)
    candidate = build_initial_quantity_policy(seed_report)
    parent_body = {**candidate, "runtime_apply_allowed": True, "runtime_effect": True,
                   "activation_state": "reviewed_active"}
    parent_body.pop("policy_content_sha256")
    parent = {**parent_body, "policy_content_sha256": _digest(parent_body)}
    refresh = build_initial_quantity_replay(new_day, data_dir=tmp_path,
                                            fact_rows=before + after,
                                            entry_on_or_after=parent["effective_from"])
    assert refresh["generation_kind"] == "refresh_post_apply_replay"
    assert refresh["census"]["all_completed_initial_trades"] == 1
    assert refresh["census"]["excluded"]["before_refresh_start"] == 1
    with pytest.raises(ValueError, match="initial_replay_integrity_invalid"):
        build_initial_quantity_policy(refresh)
    evaluation = evaluate_refresh_quantity_candidate(refresh, parent_policy=parent)
    assert evaluation["state"] == "carry_parent"
    assert "independent_post_apply_dates_below_three" in evaluation["global_blockers"]
    assert "parent_pid_consumption_missing" in evaluation["global_blockers"]
    assert "post_apply_terminal_cost_binding_missing" in evaluation["global_blockers"]
    assert evaluation["runtime_apply_allowed"] is False

    following = build_following_bar_source(
        seed_report, fetch=lambda code, base_dt, limit: (
            [{"source_timestamp": "20260922093200", "저가": 99}],
            {"api_id": "ka10080", "request_code": code,
             "request_base_dt": base_dt,
             "continuous_page_limit_reached": False}),
    )
    stage = publish_initial_quantity_candidate(
        seed_report, output_dir=tmp_path / "baseline_stage",
        following_bars=following)
    active_baseline = build_initial_quantity_baseline(stage)
    assert baseline_policy_valid(active_baseline)
    baseline_evaluation = evaluate_refresh_quantity_candidate(
        refresh, parent_policy=active_baseline)
    assert baseline_evaluation["parent_policy_content_sha256"] == (
        active_baseline["policy_content_sha256"])
    assert baseline_evaluation["state"] == "carry_parent"
    assert baseline_evaluation["runtime_apply_allowed"] is False
    assert all(row["minimum_completed_count"] == 30 for row in
               baseline_evaluation["type_decisions"].values())
    assert "parent_pid_consumption_missing" in baseline_evaluation["global_blockers"]
    assert "parent_trade_policy_binding_missing" in baseline_evaluation["global_blockers"]
    v2_parent = build_initial_quantity_runtime_v2(
        stage, active_baseline, "a" * 64)
    v2_evaluation = evaluate_refresh_quantity_candidate(
        refresh, parent_policy=v2_parent)
    assert v2_evaluation["state"] == "carry_parent"
    assert v2_evaluation["parent_policy_content_sha256"] == v2_parent[
        "policy_content_sha256"]
    assert all(row["minimum_completed_count"] == 30 for row in
               v2_evaluation["type_decisions"].values())
    changed_v2 = copy.deepcopy(v2_parent)
    changed_v2["type_policies"]["KRX_PARENT"]["selected_shape"] = (
        "two_leg_0_1tick")
    changed_body = {key: value for key, value in changed_v2.items()
                    if key not in {"policy_version", "policy_content_sha256"}}
    changed_v2["policy_version"] = (
        "initial-quantity-runtime-v2-" + _digest(changed_body)[:12])
    changed_v2["policy_content_sha256"] = _digest({
        key: value for key, value in changed_v2.items()
        if key != "policy_content_sha256"})
    assert runtime_v2_policy_valid(changed_v2)
    changed_evaluation = evaluate_refresh_quantity_candidate(
        refresh, parent_policy=changed_v2)
    assert changed_evaluation["type_decisions"]["KRX_PARENT"][
        "selected_shape"] == "two_leg_0_1tick"
    assert changed_evaluation["state"] == "carry_parent"
    broken_baseline = copy.deepcopy(active_baseline)
    broken_baseline["type_policies"]["SAFE_UNKNOWN"]["selected_shape"] = "two_leg_0_1tick"
    with pytest.raises(ValueError, match="refresh_parent_or_replay_contract_invalid"):
        evaluate_refresh_quantity_candidate(
            refresh, parent_policy=broken_baseline)
    with pytest.raises(ValueError, match="refresh_parent_or_replay_contract_invalid"):
        evaluate_refresh_quantity_candidate(refresh, parent_policy=None)
    with pytest.raises(ValueError, match="refresh_parent_or_replay_contract_invalid"):
        evaluate_refresh_quantity_candidate(None, parent_policy=active_baseline)
    parent_path = (tmp_path / "active_parent.json").resolve()
    _write_immutable_json(parent_path, active_baseline)
    from src.engine.scalping.initial_quantity_timeout_research import (
        build_timeout_research,
    )
    refresh_timeout = build_timeout_research(
        new_day, data_dir=tmp_path,
        fact_rows=refresh["census"]["input_fact_rows"],
        entry_on_or_after=active_baseline["effective_from"])
    synthetic_eligible = copy.deepcopy(baseline_evaluation)
    synthetic_eligible["state"] = "eligible_source_only"
    synthetic_eligible["global_blockers"] = []
    synthetic_eligible["type_decisions"]["KRX_PARENT"]["selected_shape"] = (
        "two_leg_0_1tick")
    candidate = build_refresh_type_policy_candidate(
        refresh, synthetic_eligible, active_baseline, refresh_timeout)
    assert candidate["type_policies"]["KRX_PARENT"]["selected_shape"] == (
        "two_leg_0_1tick")
    assert candidate["type_policies"]["KRX_PARENT"]["selected_total_wait_sec"] is None
    assert candidate["runtime_apply_allowed"] is False
    assert candidate["broker_order_forbidden"] is True
    with pytest.raises(ValueError, match="no_selected_change"):
        build_refresh_type_policy_candidate(
            refresh, {**synthetic_eligible,
                      "type_decisions": {name: {"selected_shape": "parent"}
                                         for name in synthetic_eligible["type_decisions"]}},
            active_baseline, refresh_timeout)
    from src.engine.scalping import initial_quantity_policy as policy_module
    with monkeypatch.context() as patch:
        patch.setattr(policy_module, "evaluate_refresh_quantity_candidate",
                      lambda *_args, **_kwargs: synthetic_eligible)
        eligible_stage = publish_refresh_quantity_evaluation(
            refresh, parent_policy=active_baseline,
            parent_policy_path=parent_path,
            output_dir=tmp_path / "eligible_source_only_stage",
            timeout_research=refresh_timeout)
        assert refresh_quantity_stage_terminal_valid(eligible_stage)
        from src.engine.scalping.initial_quantity_activation import (
            build_initial_quantity_refresh_runtime_policy,
            runtime_refresh_policy_valid,
        )
        runtime_candidate = build_initial_quantity_refresh_runtime_policy(
            eligible_stage, active_baseline, "a" * 64)
        assert runtime_refresh_policy_valid(runtime_candidate)
        assert runtime_candidate["type_policies"]["KRX_PARENT"][
            "selected_shape"] == "two_leg_0_1tick"
        Path(eligible_stage["candidate_path"]).write_text("{}")
        assert not refresh_quantity_stage_terminal_valid(eligible_stage)
    refresh_stage = publish_refresh_quantity_evaluation(
        refresh, parent_policy=active_baseline,
        parent_policy_path=parent_path,
        output_dir=tmp_path / "refresh_stage",
        timeout_research=refresh_timeout)
    assert refresh_stage["decision"] == "carry_parent"
    assert refresh_quantity_stage_terminal_valid(refresh_stage)
    selected_dir = tmp_path / "selected_refresh_parent"
    select_initial_quantity_baseline(
        tmp_path / "baseline_stage" / f"initial_quantity_stage_{prior_day}.json",
        selected_dir)
    replay_path = (tmp_path / "refresh_replay_input.json").resolve()
    _write_immutable_json(replay_path, refresh)
    assert initial_quantity_main([
        "--replay", str(replay_path),
        "--data-dir", str(tmp_path),
        "--parent-current", str(selected_dir / "current.json"),
        "--output-dir", str(tmp_path / "refresh_cli")]) == 0
    cli_stage = json.loads((tmp_path / "refresh_cli" /
                            f"initial_quantity_refresh_stage_{new_day}.json").read_text())
    assert cli_stage["timeout_research_status"] == "source_bound"
    assert refresh_quantity_stage_terminal_valid(cli_stage)
    timeout_path = Path(cli_stage["timeout_research_path"])
    timeout_report = json.loads(timeout_path.read_text())
    assert timeout_report["generation_kind"] == "refresh_post_apply_timeout_research"
    assert timeout_report["census"] == refresh["census"]
    assert timeout_report["entry_on_or_after"] == active_baseline["effective_from"]
    assert timeout_report["runtime_apply_allowed"] is False
    from src.engine.automation.postclose_summary_handoff import source_receipt
    cli_stage_path = (tmp_path / "refresh_cli" /
                      f"initial_quantity_refresh_stage_{new_day}.json")
    assert source_receipt({"initial_quantity_refresh_stage": cli_stage_path},
                          new_day)["sources"]["initial_quantity_refresh_stage"]["sha256"]
    with pytest.raises(RuntimeError, match="initial_quantity_refresh_stage_invalid"):
        source_receipt({"initial_quantity_refresh_stage": cli_stage_path}, prior_day)
    with pytest.raises(RuntimeError, match="initial_quantity_refresh_stage_invalid"):
        source_receipt({"initial_quantity_refresh_stage": tmp_path / "missing.json"},
                       new_day)
    changed = copy.deepcopy(refresh_stage)
    changed["report_file_sha256"] = "0" * 64
    assert not refresh_quantity_stage_terminal_valid(changed)
    timeout_path.write_text("{}", encoding="utf-8")
    assert not refresh_quantity_stage_terminal_valid(cli_stage)
    empty = build_initial_quantity_replay(
        new_day, data_dir=tmp_path, fact_rows=before,
        entry_on_or_after=active_baseline["effective_from"])
    empty_stage = publish_refresh_quantity_evaluation(
        empty, parent_policy=active_baseline,
        parent_policy_path=parent_path,
        output_dir=tmp_path / "empty_refresh_stage",
        timeout_research=build_timeout_research(
            new_day, data_dir=tmp_path,
            fact_rows=empty["census"]["input_fact_rows"],
            entry_on_or_after=active_baseline["effective_from"]))
    assert empty_stage["all_completed_initial_trades"] == 0
    assert empty_stage["decision"] == "carry_parent"
    assert refresh_quantity_stage_terminal_valid(empty_stage)
    future_day = "2026-09-28"
    future_empty = build_initial_quantity_replay(
        future_day, data_dir=tmp_path, fact_rows=before,
        entry_on_or_after=active_baseline["effective_from"])
    future_timeout = build_timeout_research(
        future_day, data_dir=tmp_path, fact_rows=before,
        entry_on_or_after=active_baseline["effective_from"])
    with pytest.raises(ValueError, match="refresh_timeout_research_required"):
        publish_refresh_quantity_evaluation(
            future_empty, parent_policy=active_baseline,
            parent_policy_path=parent_path,
            output_dir=tmp_path / "future_without_timeout")
    future_stage = publish_refresh_quantity_evaluation(
        future_empty, parent_policy=active_baseline,
        parent_policy_path=parent_path,
        timeout_research=future_timeout,
        output_dir=tmp_path / "future_refresh_stage")
    future_stage_path = (tmp_path / "future_refresh_stage" /
                         f"initial_quantity_refresh_stage_{future_day}.json")
    assert refresh_quantity_stage_terminal_valid(future_stage)
    assert source_receipt({"initial_quantity_refresh_stage": future_stage_path},
                          future_day)["sources"]["initial_quantity_refresh_stage"]["sha256"]
    with pytest.raises(RuntimeError, match="initial_quantity_refresh_stage_invalid"):
        source_receipt({"initial_quantity_refresh_stage":
                        tmp_path / "empty_refresh_stage" /
                        f"initial_quantity_refresh_stage_{new_day}.json"},
                       future_day)
    winning_after = _facts([{"recommendation_id": 13, "stock_code": "000001",
                            "strategy": "SCALPING", "position_tag": "SCANNER",
                            "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                            "sell_time": "09:35:00", "held_sec": 300}], new_day)
    winning_refresh = build_initial_quantity_replay(
        new_day, data_dir=tmp_path, fact_rows=before + winning_after,
        entry_on_or_after=active_baseline["effective_from"])
    missing_following = evaluate_refresh_quantity_candidate(
        winning_refresh, parent_policy=active_baseline)
    assert "winner_following_source_missing" in missing_following["global_blockers"]
    winning_timeout = build_timeout_research(
        new_day, data_dir=tmp_path,
        fact_rows=winning_refresh["census"]["input_fact_rows"],
        entry_on_or_after=active_baseline["effective_from"])
    with pytest.raises(ValueError, match="refresh_winner_following_source_required"):
        publish_refresh_quantity_evaluation(
            winning_refresh, parent_policy=active_baseline,
            parent_policy_path=parent_path,
            output_dir=tmp_path / "winning_refresh_stage",
            timeout_research=winning_timeout)
    winning_following = build_following_bar_source(
        winning_refresh, fetch=lambda code, base_dt, limit: (
            [{"source_timestamp": "20260923093200", "저가": 99}],
            {"api_id": "ka10080", "request_code": code,
             "request_base_dt": base_dt,
             "continuous_page_limit_reached": False}),
    )
    winning_stage = publish_refresh_quantity_evaluation(
        winning_refresh, parent_policy=active_baseline,
        parent_policy_path=parent_path,
        following_bars=winning_following,
        timeout_research=winning_timeout,
        output_dir=tmp_path / "winning_refresh_stage")
    assert refresh_quantity_stage_terminal_valid(winning_stage)
    from src.utils import kiwoom_utils
    calls = []
    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", lambda: "test-token")

    def fake_candles(token, code, *, limit, explicit_request_code, base_dt):
        calls.append((token, code, limit, explicit_request_code, base_dt))
        return ([{"source_timestamp": "20260923093200", "저가": 99}],
                {"api_id": "ka10080", "request_code": code,
                 "request_base_dt": base_dt,
                 "continuous_page_limit_reached": False})

    monkeypatch.setattr(kiwoom_utils, "get_minute_candles_ka10080_with_meta",
                        fake_candles)
    winning_replay_path = (tmp_path / "winning_refresh_replay_input.json").resolve()
    _write_immutable_json(winning_replay_path, winning_refresh)
    assert initial_quantity_main([
        "--replay", str(winning_replay_path),
        "--data-dir", str(tmp_path),
        "--parent-current", str(selected_dir / "current.json"),
        "--output-dir", str(tmp_path / "winning_refresh_cli")]) == 0
    assert len(calls) == 1 and calls[0][0] == "test-token"
    auto_stage = json.loads((tmp_path / "winning_refresh_cli" /
                             f"initial_quantity_refresh_stage_{new_day}.json").read_text())
    assert auto_stage["following_bar_source_status"] == "source_bound"
    assert refresh_quantity_stage_terminal_valid(auto_stage)
    attempts = []

    def failed_token():
        attempts.append(True)
        raise RuntimeError("offline_fixture")

    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", failed_token)
    assert initial_quantity_main([
        "--replay", str(winning_replay_path),
        "--data-dir", str(tmp_path),
        "--parent-current", str(selected_dir / "current.json"),
        "--output-dir", str(tmp_path / "winning_refresh_api_gap")]) == 0
    assert len(attempts) == 1
    gap_stage = json.loads((tmp_path / "winning_refresh_api_gap" /
                            f"initial_quantity_refresh_stage_{new_day}.json").read_text())
    gap_source = json.loads(Path(gap_stage["following_bar_source_path"]).read_text())
    assert next(iter(gap_source["sources"].values()))["status"] == "fetch_failed"
    assert refresh_quantity_stage_terminal_valid(gap_stage)

    import hashlib
    parent_file_sha = hashlib.sha256(parent_path.read_bytes()).hexdigest()
    plan_sha = "b" * 64
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{new_day}.jsonl", [
        _event(13, "entry_execution_sizing_plan", f"{new_day}T09:29:00+09:00",
               entry_execution_sizing_valid=True, effective_venue="KRX",
               entry_submit_attempt_id="attempt-13",
               entry_execution_sizing_plan_sha256=plan_sha,
               position_sizing_policy_status="initial_policy_loaded",
               position_sizing_policy_sha256=parent_file_sha,
               quantity_type_policy_row="KRX_PARENT"),
        _event(13, "order_bundle_submitted", f"{new_day}T09:29:59+09:00",
               actual_order_submitted=True, effective_venue="KRX"),
        _event(13, "order_leg_sent", f"{new_day}T09:29:59+09:00",
               actual_order_submitted=True, broker_order_no="13",
               entry_submit_attempt_id="attempt-13",
               entry_execution_sizing_plan_sha256=plan_sha,
               tag="first"),
        _event(13, "position_rebased_after_fill", f"{new_day}T09:30:00+09:00",
               entry_mode="normal", fill_price=100, fill_qty=4,
               order_no="13", execution_no="one",
               actual_execution_venue="KRX",
               broker_execution_observed_at=f"{new_day}T09:30:00+09:00"),
    ])
    bound_refresh = build_initial_quantity_replay(
        new_day, data_dir=tmp_path, fact_rows=before + winning_after,
        entry_on_or_after=active_baseline["effective_from"])
    assert bound_refresh["trades"][0]["applied_policy_file_sha256"] == parent_file_sha
    assert bound_refresh["trades"][0]["policy_decision_stage"] == (
        "entry_execution_sizing_plan")
    bound_evaluation = evaluate_refresh_quantity_candidate(
        bound_refresh, parent_policy=active_baseline,
        parent_policy_file_sha256=parent_file_sha)
    assert bound_evaluation["parent_policy_bound_trade_count"] == 1
    assert "parent_trade_policy_binding_missing" not in bound_evaluation["global_blockers"]
    assert "parent_pid_consumption_missing" in bound_evaluation["global_blockers"]
    wrong_file = evaluate_refresh_quantity_candidate(
        bound_refresh, parent_policy=active_baseline,
        parent_policy_file_sha256="0" * 64)
    assert "parent_trade_policy_binding_missing" in wrong_file["global_blockers"]
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{new_day}.jsonl", [
        _event(13, "entry_execution_sizing_plan", f"{new_day}T09:29:00+09:00",
               entry_execution_sizing_valid=True, effective_venue="KRX",
               entry_submit_attempt_id="attempt-13",
               entry_execution_sizing_plan_sha256=plan_sha,
               position_sizing_policy_status="initial_policy_loaded",
               position_sizing_policy_sha256=parent_file_sha),
        _event(13, "order_leg_sent", f"{new_day}T09:29:59+09:00",
               actual_order_submitted=True, broker_order_no="13",
               entry_submit_attempt_id="attempt-13",
               entry_execution_sizing_plan_sha256="c" * 64,
               tag="first"),
        _event(13, "position_rebased_after_fill", f"{new_day}T09:30:00+09:00",
               entry_mode="normal", fill_price=100, fill_qty=4,
               order_no="13", execution_no="one",
               actual_execution_venue="KRX",
               broker_execution_observed_at=f"{new_day}T09:30:00+09:00"),
    ])
    mismatched = build_initial_quantity_replay(
        new_day, data_dir=tmp_path, fact_rows=before + winning_after,
        entry_on_or_after=active_baseline["effective_from"])
    assert mismatched["trades"][0]["applied_policy_file_sha256"] is None
    assert "parent_trade_policy_binding_missing" in evaluate_refresh_quantity_candidate(
        mismatched, parent_policy=active_baseline,
        parent_policy_file_sha256=parent_file_sha)["global_blockers"]


def test_refresh_timeout_research_valid_empty_and_source_date_gate(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import (
        build_timeout_research, timeout_research_valid,
    )
    from src.engine.automation.postclose_summary_handoff import source_receipt

    day = "2026-09-28"
    report = build_timeout_research(
        day, data_dir=tmp_path, fact_rows=[], entry_on_or_after=day)
    assert report["generation_kind"] == "refresh_post_apply_timeout_research"
    assert report["cost_model"] == "canonical_sell_notional_only_v1"
    assert report["census"]["all_completed_initial_trades"] == 0
    assert report["entry_on_or_after"] == day
    assert timeout_research_valid(report)
    legacy_refresh = {**report, "cost_model": "buy_and_sell_notional_legacy"}
    legacy_refresh["report_content_sha256"] = _digest({
        key: value for key, value in legacy_refresh.items()
        if key != "report_content_sha256"})
    assert not timeout_research_valid(legacy_refresh)
    no_cost_model = {key: value for key, value in report.items()
                     if key != "cost_model"}
    no_cost_model["report_content_sha256"] = _digest({
        key: value for key, value in no_cost_model.items()
        if key != "report_content_sha256"})
    assert not timeout_research_valid(no_cost_model)
    initial = build_timeout_research(day, data_dir=tmp_path, fact_rows=[])
    assert not timeout_research_valid(initial)
    legacy_path = tmp_path / "initial_quantity_refresh_stage_2026-09-28.json"
    legacy_path.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="initial_quantity_refresh_stage_invalid"):
        source_receipt({"initial_quantity_refresh_stage": legacy_path}, day)


def test_refresh_reuses_exact_pipeline_scan_for_timeout_research(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research

    day = "2026-09-28"
    _quality(tmp_path, day)
    facts = _facts([{"recommendation_id": 31, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", [
        _event(31, "entry_execution_sizing_plan", f"{day}T09:29:50+09:00",
               entry_execution_sizing_valid=True, effective_venue="KRX"),
        _event(31, "position_rebased_after_fill", f"{day}T09:30:00+09:00",
               entry_mode="normal", fill_price=100, fill_qty=4,
               order_no="31", execution_no="one", actual_execution_venue="KRX",
               broker_execution_observed_at=f"{day}T09:30:00+09:00"),
        _event(31, "market_observation", f"{day}T09:31:00+09:00",
               effective_venue="KRX", latest_price=99, ws_age_ms=0),
    ])
    cache = {}
    replay = build_initial_quantity_replay(
        day, data_dir=tmp_path, fact_rows=facts,
        entry_on_or_after=day, path_cache=cache)
    assert replay["cost_model"] == "canonical_sell_notional_only_v1"
    from src.engine.scalping.initial_quantity_policy import initial_replay_economics_valid
    legacy_refresh = {**replay, "cost_model": "buy_and_sell_notional_legacy"}
    legacy_refresh["report_content_sha256"] = _digest({
        key: value for key, value in legacy_refresh.items()
        if key != "report_content_sha256"})
    assert not initial_replay_economics_valid(legacy_refresh)
    assert replay == build_initial_quantity_replay(
        day, data_dir=tmp_path, fact_rows=facts, entry_on_or_after=day)
    cached_perf = {}
    cached = build_timeout_research(
        day, data_dir=tmp_path, fact_rows=replay["census"]["input_fact_rows"],
        entry_on_or_after=day, path_cache=cache, performance=cached_perf)
    independent = build_timeout_research(
        day, data_dir=tmp_path, fact_rows=facts, entry_on_or_after=day)
    assert cached == independent
    assert cached["pipeline_source_receipts"] == replay["pipeline_source_receipts"]
    assert cached_perf["shared_pipeline_scan_reused"] is True
    assert cached_perf["date_scan_seconds"] == {}
    with pytest.raises(ValueError, match="timeout_research_shared_source_mismatch"):
        build_timeout_research(day, data_dir=tmp_path, fact_rows=facts,
                               entry_on_or_after=day,
                               path_cache={**cache, "price_horizon_seconds": 600})


def test_fact_buy_clock_fallback_is_labeled_without_broker_claim(tmp_path):
    day = "2026-09-23"
    _quality(tmp_path, day)
    fact = _facts([{"recommendation_id": 7, "stock_code": "000001",
                    "strategy": "SCALPING", "position_tag": "SCANNER",
                    "buy_price": 100, "sell_price": 101, "buy_qty": 4,
                    "sell_time": "09:35:00", "held_sec": 300}], day)[0]
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl", [
        _event(7, "entry_execution_sizing_plan", f"{day}T09:29:00+09:00",
               entry_execution_sizing_valid=True, effective_venue="KRX",
               market_session_bucket="krx_regular", source_signature="A",
               reference_time=f"{day}T09:29:00+09:00", current_price=100),
        _event(7, "holding_quote", f"{day}T09:31:00+09:00",
               latest_price=98, ws_age_ms=20, effective_venue="KRX"),
    ])
    report = build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=[fact])
    assert report["trades"][0]["shapes"]["two_leg_0_1tick"][
        "fill_clock_source"] == "trade_performance_fact_buy_time"


def test_overnight_entry_date_and_late_submit_receipt_are_preserved(tmp_path):
    exit_day = "2026-07-08"
    entry_day = "2026-07-07"
    _quality(tmp_path, entry_day)
    _quality(tmp_path, exit_day)
    terminal_rows = [{
        "post_sell_id": "overnight", "recommendation_id": 71,
        "signal_date": exit_day, "stock_code": "000001", "strategy": "SCALPING",
        "position_tag": "SCANNER", "actual_order_submitted": True,
        "buy_price": 100, "sell_price": 101, "buy_qty": 4,
        "profit_rate": 0.7, "sell_time": "08:08:07", "held_sec": 49038,
    }]
    _write_jsonl(tmp_path / "post_sell" / f"post_sell_evaluations_{exit_day}.jsonl", terminal_rows)
    _write_jsonl(tmp_path / "pipeline_events" / f"pipeline_events_{entry_day}.jsonl", [
        _event(71, "position_rebased_after_fill", f"{entry_day}T18:30:40+09:00",
               entry_mode="normal", avg_buy_price=100, fill_qty=4),
        _event(71, "order_bundle_submitted", f"{entry_day}T18:30:48+09:00",
               actual_order_submitted=True, source_signature="A", latest_price=100,
               ws_age_ms=50),
        _event(71, "holding_quote", f"{entry_day}T18:30:50+09:00",
               latest_price=98, ws_age_ms=50),
    ])
    report = build_initial_quantity_replay(exit_day, data_dir=tmp_path,
                                           fact_rows=_facts(terminal_rows, exit_day))
    row = report["trades"][0]
    assert row["entry_date"] == entry_day
    shape = row["shapes"]["two_leg_0_1tick"]
    assert shape["status"] == "paired"
    assert shape["decision_emitted_after_fill_proxy"] is True
    assert shape["fill_clock_source"] == "position_rebased_emitted_at_proxy"


def test_classifier_and_price_use_only_valid_decision_time_sources():
    assert classify_quantity_type({"effective_venue": "NXT", "source_signature": "A",
                                   "reference_time": "2026-09-23T09:30:00+09:00"}) == "SAFE_UNKNOWN"
    assert classify_quantity_type({"effective_venue": "KRX",
                                   "source_signature": ["UNKNOWN", "NOT_APPLICABLE_SOURCE_SIGNATURE"],
                                   "reference_time": "2026-09-23T09:30:00+09:00",
                                   "market_session_bucket": "krx_regular"}) == "SAFE_UNKNOWN"
    assert classify_quantity_type({"effective_venue": "KRX", "source_signature": "A",
                                   "reference_time": "2026-09-23T09:30:00+09:00",
                                   "market_session_bucket": "krx_regular", "current_price": 100}) == "KRX_THIN_HIGH_TICK"
    assert classify_quantity_type({"effective_venue": "KRX", "source_signature": "A",
                                   "reference_time": "2026-09-23T09:30:00+09:00",
                                   "market_session_bucket": "nxt_regular", "current_price": 100}) == "KRX_PARENT"
    feature = {"effective_venue": "KRX", "source_signature": "A",
               "reference_time": "2026-09-23T09:30:00+09:00",
               "market_session_bucket": "krx_regular", "current_price": 12000,
               "liquidity_band": "SUPPORTIVE", "trusted_flow_state": "BUY_DOMINANT",
               "trusted_flow_fresh": True, "classifier_route_key": "KRX_0D",
               "classifier_transport_epoch": "epoch-1",
               "feature_route_key": "KRX_0D",
               "feature_transport_epoch": "epoch-1"}
    assert classify_quantity_type(feature) == "KRX_PARENT"
    verified = {**feature, "feature_snapshot_at": "2026-09-23T09:29:59.500+09:00"}
    assert classify_quantity_type(verified) == "KRX_LIQUID_FLOW_SUPPORT"
    assert classify_quantity_type({**verified, "feature_transport_epoch": "old"}) == "KRX_PARENT"
    assert classify_quantity_type({**verified, "feature_snapshot_at": "2026-09-23T09:29:57+09:00"}) == "KRX_PARENT"
    assert _fresh_observed_price({"current_price_observed": 1,
                                  "latest_price": 100, "ws_age_ms": 20}) == (100.0, "fresh_ws_latest_price")
    assert _fresh_observed_price({"current_price_observed": 1})[0] is None
    assert _fresh_observed_price({"latest_price": 100, "ws_age_ms": 20,
                                  "quote_consistency_state": "conflict"})[0] is None
    entry = datetime.fromisoformat("2026-09-23T09:30:00+09:00")
    assert _type_from_decision_receipt({
        "effective_venue": "KRX", "source_signature": "A",
        "reference_time": entry.isoformat(), "market_session_bucket": "krx_regular",
        "price_krw": 100, "quantity_type": "KRX_THIN_HIGH_TICK",
        "quantity_type_classifier_version": "initial_quantity_type_v1"},
        decision_at=entry + timedelta(seconds=1), entry_at=entry) == "SAFE_UNKNOWN"
    assert _type_from_decision_receipt({
        "effective_venue": "KRX", "source_signature": "A",
        "reference_time": (entry + timedelta(seconds=1)).isoformat(),
        "market_session_bucket": "krx_regular", "price_krw": 100,
        "quantity_type": "KRX_THIN_HIGH_TICK",
        "quantity_type_classifier_version": "initial_quantity_type_v1"},
        decision_at=entry - timedelta(seconds=1), entry_at=entry) == "SAFE_UNKNOWN"


def test_source_only_artifact_publish_is_immutable(tmp_path):
    path = tmp_path / "candidate.json"
    first = _write_immutable_json(path, {"value": 1})
    assert first == _write_immutable_json(path, {"value": 1})
    with pytest.raises(ValueError, match="immutable_artifact_conflict"):
        _write_immutable_json(path, {"value": 2})
    assert json.loads(path.read_text()) == {"value": 1}
