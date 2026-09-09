from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta
import json

import pytest

from src.engine.monitoring import machine_adaptive_exit_source as module
from src.trading.order.adaptive_exit.source import (
    OwnerScope,
    record_first_fill_observation,
    record_target_observation,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256, AUTHORITY
from src.engine.monitoring.machine_adaptive_exit_study import run_study

DAY = "2026-09-09"
NOW = datetime.fromisoformat(DAY + "T09:00:00+09:00")
SCOPE = OwnerScope("episode", "samsung:midday", "005930", "SOR", "KRX_REGULAR")
FIELD = "adaptive_exit_target_observations"


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def leg_source(*, day=DAY, lot="leg1", target="2222222"):
    record = {}
    record_first_fill_observation(
        record,
        previous_filled_qty=0,
        filled_qty=10,
        observed_at=day + "T09:00:00+09:00",
    )
    record.update(
        leg_id=lot,
        quantity=10,
        buy_filled_qty=10,
        fill_price=10000,
        buy_order_no="1111111",
        buy_order_date=day,
        route="SOR",
        position_qty=10,
        target_filled_qty=0,
        target_price=10100,
        target_order_no=target,
        target_order_date=day,
        target_quantity=10,
    )
    record_target_observation(
        record,
        target={
            "order_date": day,
            "order_no": target,
            "route": "SOR",
            "price": 10100,
            "quantity": 10,
        },
        entries=[
            {
                "episode_id": f"samsung:midday:{day}",
                "lot_id": lot,
                "order_no": "1111111",
                "order_date": day,
                "price": 10000,
                "quantity": 10,
                "requested_quantity": 10,
                "first_fill_observation": record[
                    "adaptive_exit_first_fill_observation"
                ],
            }
        ],
        owner=SCOPE.owner,
        profile=SCOPE.profile,
        symbol=SCOPE.symbol,
        session=SCOPE.session,
        entry_policy={"target_ticks": 2},
        observed_at=day + "T09:00:01+09:00",
    )
    return record


def collect(tmp_path, legs, *, day=DAY):
    write(
        tmp_path / "samsung_midday_one_share_state.json",
        {
            "schema": "samsung_midday_two_leg_state_v2",
            "trade_date": day,
            "legs": legs,
            "signal_features": {"strategy": "midday"},
        },
    )
    return module.collect_owner_census(
        target_date=day,
        catalog=(SCOPE,),
        runtime_root=tmp_path,
        widget_state_path=tmp_path / "widget.json",
    )


def raw_path(*, day=DAY, price=10000):
    first = datetime.fromisoformat(day + "T09:00:00+09:00")
    depth, trade = [], []
    for i in range(-2, module.HORIZON_SEC + 1):
        common = {
            "local_receive_timestamp": (first + timedelta(seconds=i)).isoformat(),
            "symbol": "005930",
            "venue": "SOR",
            "session_bucket": "SOR_REGULAR",
            "sequence_epoch": 1,
            "series_sequence": i + 3,
            "source_sequence": i + 3,
            "path_order_status": "accept",
            "path_consumer_eligible": True,
        }
        depth.append(
            common
            | {
                "item": "005930_AL",
                "best_bid": price,
                "best_ask": price + 10,
                "best_ask_qty": 100,
                "bid_levels": [[1, price, 100]],
                "ask_levels": [[1, price + 10, 100]],
            }
        )
        # Actual canonical market stream has no item field.
        trade.append(
            common
            | {
                "schema": "scalp_micro_reversion_market_stream_point_v3",
                "realtime_type": "0B",
                "trade_price": price,
                "trade_qty": 1,
                "aggressor_side": "SELL",
            }
        )
    return {"raw_depth_rows": depth, "raw_market_rows": trade}


def test_target_receipt_is_frozen_and_does_not_change_order_or_first_clock():
    leg = leg_source()
    frozen = deepcopy(leg[FIELD])
    leg["adaptive_exit_first_fill_observation"]["first_observed_at"] = "changed"
    assert leg[FIELD] == frozen
    assert leg["target_order_no"] == "2222222"
    assert next(iter(frozen.values()))["authority"] == AUTHORITY


def test_target_receipt_duplicate_conflict_preserves_original():
    leg = leg_source()
    original = deepcopy(leg[FIELD])
    payload = next(iter(original.values()))
    for target in (payload["target"], payload["target"] | {"price": 10500}):
        record_target_observation(
            leg,
            target=target,
            entries=payload["entries"],
            owner=SCOPE.owner,
            profile=SCOPE.profile,
            symbol=SCOPE.symbol,
            session=SCOPE.session,
            entry_policy=payload["entry_policy"],
            observed_at=DAY + "T09:00:02+09:00",
        )
        assert leg[FIELD] == original
    assert leg["adaptive_exit_source_gap"] == "conflicting_target_observation"


def test_whole_census_preserves_held_legacy_and_full_target_winner(tmp_path):
    winner = leg_source()
    winner.update(position_qty=0, target_filled_qty=10, completed=True)
    legacy = leg_source(lot="leg2", target="3333333")
    legacy.pop(FIELD)
    source, anchors = collect(tmp_path, [winner, legacy])
    c = source["scopes"][SCOPE.key]
    assert c["complete"] and c["expected_episode_lots"] == {
        f"samsung:midday:{DAY}": ["leg1", "leg2"]
    }
    assert len(anchors) == 1 and len(c["lots"]) == 2
    assert c["lots"][1]["disposition"] == "source_invalid"
    assert "first_fill" in c["lots"][1]["reason"]


def test_complete_empty_vs_missing_vs_invalid_not_collapsed(tmp_path):
    empty, _ = collect(tmp_path, [])
    assert empty["scopes"][SCOPE.key]["complete"]
    assert not empty["scopes"]["episode|samsung:morning|005930|SOR|KRX_REGULAR"][
        "complete"
    ]
    invalid, _ = collect(tmp_path, [leg_source() | {"buy_filled_qty": True}])
    assert not invalid["scopes"][SCOPE.key]["complete"]


def test_natural_ordered_source_to_all_scope_study_no_external_input_file(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(module, "HORIZON_SEC", 10)
    source, anchors = collect(tmp_path, [leg_source()])
    bound = module.bind_ordered_paths(source, {anchors[0]["anchor_id"]: raw_path()})
    c = bound["scopes"][SCOPE.key]
    assert c["conservation_valid"] and c["disposition_counts"] == {"eligible": 1}
    assert len(c["lot_paths"][0]["observations"]) == 11
    assert c["lot_paths"][0]["authority"] == AUTHORITY
    assert bound["canonical_sha256"] == canonical_sha256(bound)


@pytest.mark.parametrize(
    "damage,reason",
    [
        ("future", "left_boundary"),
        ("gap", "source_gap"),
        ("epoch", "epoch_changed"),
        ("route", "route"),
        ("overflow", "budget"),
    ],
)
def test_ordered_path_does_not_hide_missing_future_other_route_or_epoch(
    tmp_path, monkeypatch, damage, reason
):
    monkeypatch.setattr(module, "HORIZON_SEC", 10)
    source, anchors = collect(tmp_path, [leg_source()])
    window = raw_path()
    if damage == "future":
        window["raw_depth_rows"] = window["raw_depth_rows"][4:]
    elif damage == "gap":
        window["raw_market_rows"].pop(3)
    elif damage == "epoch":
        for rows in window.values():
            for row in rows[5:]:
                row["sequence_epoch"] = 2
    elif damage == "route":
        window["raw_market_rows"][0]["venue"] = "KRX"
    else:
        window["adaptive_exit_source_overflow"] = True
    bound = module.bind_ordered_paths(source, {anchors[0]["anchor_id"]: window})
    c = bound["scopes"][SCOPE.key]
    assert not c["lot_paths"] and c["conservation_valid"]
    assert reason in c["lots"][0]["reason"]


def test_horizon_not_due_is_pending_not_failed_or_synthetic_exit(tmp_path):
    source, anchors = collect(tmp_path, [leg_source()])
    bound = module.bind_ordered_paths(
        source, {}, evaluated_at=NOW + timedelta(seconds=5)
    )
    assert (
        bound["scopes"][SCOPE.key]["lots"][0]["disposition"]
        == "pending_declared_window"
    )


def test_census_schema_error_does_not_drop_lot_or_claim_complete(tmp_path):
    bad = leg_source()
    next(iter(bad[FIELD].values()))["authority"]["allowed_runtime_apply"] = True
    source, _ = collect(tmp_path, [bad])
    assert not source["scopes"][SCOPE.key]["complete"]
    assert source["scopes"][SCOPE.key]["expected_episode_lots"] == {
        f"samsung:midday:{DAY}": ["leg1"]
    }
    assert "authority" in source["scopes"][SCOPE.key]["errors"][0]


def test_natural_two_day_inputs_emit_native_research_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "HORIZON_SEC", 60)
    prior, anchors = collect(tmp_path, [leg_source(day="2026-09-08")], day="2026-09-08")
    prior = module.bind_ordered_paths(
        prior, {anchors[0]["anchor_id"]: raw_path(day="2026-09-08")}
    )
    write(
        tmp_path
        / "report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json",
        {"rolling_policy_research_v2": {"natural_owner_census": prior}},
    )
    current, anchors = collect(tmp_path, [leg_source()])
    current = module.bind_ordered_paths(current, {anchors[0]["anchor_id"]: raw_path()})
    rolling = module.merge_census_history(current, report_root=tmp_path / "report")
    result = run_study(
        target_date=DAY,
        catalog=(SCOPE,),
        source=rolling,
        contract=module.propose_study_contract(rolling),
    )
    assert result["scopes"][0]["status"] == "study_evaluated"
    assert len(result["policy_promotion_candidates"]) == 3
    assert all(e["unique_episodes"] == 2 for e in result["evidence"])
    assert all(
        not c["eligible_for_next_preopen"]
        for c in result["policy_promotion_candidates"]
    )
    from src.engine.monitoring.machine_adaptive_exit_replay import (
        build_adaptive_exit_source_census,
    )

    child = build_adaptive_exit_source_census(
        {
            "target_date": DAY,
            "rolling_policy_source_contract": {"ready": True},
            "consumers": {
                "widget_postclose_tuning": {"symbols": {}},
                "episode_machine_postclose_tuning": {"profiles": {}},
            },
        },
        owner_census=current,
        study_source=rolling,
        study_contract=module.propose_study_contract(rolling),
    )
    assert len(child["all_scope_study"]["policy_promotion_candidates"]) == 3
    assert "review_native_research_candidates" in child["next_action"]


def test_consecutive_history_includes_zero_day_but_not_missing_day(tmp_path):
    source, _ = collect(tmp_path, [])
    current = module.bind_ordered_paths(source, {})
    prior = deepcopy(current)
    prior["target_date"] = "2026-09-08"
    for c in prior["scopes"].values():
        c["source_trading_dates"] = ["2026-09-08"]
    prior["canonical_sha256"] = canonical_sha256(prior)
    write(
        tmp_path
        / "report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json",
        {"rolling_policy_research_v2": {"natural_owner_census": prior}},
    )
    rolling = module.merge_census_history(current, report_root=tmp_path / "report")
    assert rolling["scopes"][SCOPE.key]["source_trading_dates"] == ["2026-09-08", DAY]
    cfg = module.propose_study_contract(rolling)
    assert cfg["source_only_risk_values_not_approved_envelope"] is True
    assert cfg["scopes"][SCOPE.key]["evaluation"]["train_end"] == "2026-09-08"
    assert not cfg["authority"]["allowed_runtime_apply"]


def test_widget_source_survives_no_legacy_anchor_and_uses_broker_route(tmp_path):
    eid = "005930:2026-09-09:ENTRY:KRX_REGULAR:2026-09-09T09:00:00+09:00"
    original = leg_source()
    payload = next(iter(original[FIELD].values()))
    order = {
        "side": "BUY",
        "broker_accepted": True,
        "order_date": DAY,
        "order_no": "1111111",
        "filled_qty": 10,
        "fill_price": 10000,
        "requested_qty": 10,
        "signal_id": eid,
        "parent_entry_signal_id": None,
        "market_venue": "KRX",
        "broker_route": "SOR",
    }
    sell = {"side": "SELL"}
    record_target_observation(
        sell,
        target=payload["target"],
        entries=[payload["entries"][0] | {"episode_id": eid, "lot_id": "entry"}],
        owner="widget",
        profile="actual:005930:KRX_REGULAR",
        symbol="005930",
        session="KRX_REGULAR",
        entry_policy={"take_profit_bps": 100},
        observed_at=DAY + "T09:00:01+09:00",
    )
    write(
        tmp_path / "widget.json",
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": DAY,
            "symbols": {"005930": {"orders": [order, sell]}},
        },
    )
    source, anchors = module.collect_owner_census(
        target_date=DAY,
        catalog=(),
        runtime_root=tmp_path,
        widget_state_path=tmp_path / "widget.json",
    )
    key = "widget|actual:005930:KRX_REGULAR|005930|SOR|KRX_REGULAR"
    assert source["scopes"][key]["complete"]
    assert source["scopes"][key]["lots"][0]["disposition"] == "pending_ordered_path"
    assert anchors[0]["expected_venues"] == ["SOR"]


def test_legacy_contract_reader_does_not_override_natural_source():
    # Provisional research is never a live eligibility switch, even with no losses.
    scope = asdict(SCOPE)
    raw = {
        "schema": "machine_adaptive_exit_owner_census_v1",
        "target_date": DAY,
        "authority": dict(AUTHORITY),
        "scopes": {
            SCOPE.key: {
                "scope": scope,
                "complete": True,
                "source_trading_dates": [DAY],
                "expected_episode_lots": {},
                "lot_paths": [],
            }
        },
    }
    raw["canonical_sha256"] = canonical_sha256(raw)
    result = run_study(
        target_date=DAY,
        catalog=(SCOPE,),
        source=raw,
        contract=module.propose_study_contract(raw),
    )
    assert result["scopes"][0]["status"] == "healthy_no_natural_sample"
    assert result["runtime_automation"]["eligible_for_next_preopen"] is False


def test_invalid_target_entries_are_named_without_losing_known_buy_lot(tmp_path):
    record = leg_source()
    receipt = next(iter(record[FIELD].values()))
    receipt["entries"] = ["malformed"]
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    source, _ = collect(tmp_path, [record])
    c = source["scopes"][SCOPE.key]
    assert not c["complete"] and len(c["lots"]) == 1
    assert c["errors"] == ["target_receipt_entry_schema_invalid"]


def test_invalid_history_nan_does_not_crash_unrelated_attribution(tmp_path):
    source, _ = collect(tmp_path, [])
    current = module.bind_ordered_paths(source, {})
    prior = deepcopy(current)
    prior.update(target_date="2026-09-08", invalid=float("nan"))
    write(
        tmp_path
        / "report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json",
        {"rolling_policy_research_v2": {"natural_owner_census": prior}},
    )
    rolling = module.merge_census_history(current, report_root=tmp_path / "report")
    assert rolling["scopes"][SCOPE.key]["source_trading_dates"] == [DAY]


@pytest.mark.parametrize("damage", ["invalid_lot", "wrong_count", "invalid_quantity"])
def test_hashed_but_malformed_daily_history_is_isolated(tmp_path, damage):
    current, _ = collect(tmp_path, [])
    current = module.bind_ordered_paths(current, {})
    prior, _ = collect(tmp_path, [leg_source(day="2026-09-08")], day="2026-09-08")
    prior = module.bind_ordered_paths(prior, {})
    c = prior["scopes"][SCOPE.key]
    if damage == "invalid_lot":
        c["lots"] = [None]
    elif damage == "wrong_count":
        c["lots"] = []
    else:
        c["expected_episode_lots"] = {"invalid": 10}
    prior["canonical_sha256"] = canonical_sha256(prior)
    write(
        tmp_path
        / "report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json",
        {"rolling_policy_research_v2": {"natural_owner_census": prior}},
    )
    result = module.merge_census_history(current, report_root=tmp_path / "report")
    assert result["scopes"][SCOPE.key]["source_trading_dates"] == [DAY]
    assert result["scopes"][SCOPE.key]["history_errors"] == [
        "historical_scope_contract_invalid"
    ]


def test_malformed_widget_state_cannot_disappear_as_complete_owner(tmp_path):
    write(
        tmp_path / "widget.json",
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": DAY,
            "symbols": {"005930": "invalid"},
        },
    )
    source, _ = collect(tmp_path, [])
    source = module.bind_ordered_paths(source, {})
    assert source["unscoped_errors"] and not source["owner_envelope_valid"]["widget"]
    result = run_study(target_date=DAY, catalog=(SCOPE,), source=source, contract=None)
    assert not result["all_owner_episode_census_complete"]


def test_malformed_optional_owner_envelope_blocks_without_crashing(tmp_path):
    source, _ = collect(tmp_path, [])
    source = module.bind_ordered_paths(source, {})
    source["owner_envelope_valid"] = [True]
    source["canonical_sha256"] = canonical_sha256(source)
    result = run_study(target_date=DAY, catalog=(SCOPE,), source=source, contract=None)
    assert not result["all_owner_episode_census_complete"]
