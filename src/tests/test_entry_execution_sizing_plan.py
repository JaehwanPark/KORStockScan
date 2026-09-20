import hashlib
import json

import pytest
from datetime import datetime

from src.engine.scalping import entry_execution_sizing_plan as sizing

from src.engine.scalping.entry_execution_sizing_plan import (
    ENTRY_EXECUTION_SIZING_POLICY_SCHEMA,
    ENTRY_PRICE_POLICY_SHA256,
    MECHANISTIC_ENTRY_PRICE_POLICY_SCHEMA,
    OWNER,
    PRICE_OWNER,
    POLICY_VERSION,
    compose_entry_execution_sizing_plan,
    compose_scale_in_execution_sizing_plan,
    runtime_mechanistic_entry_price_policy,
    runtime_entry_execution_sizing_policy,
)
from src.engine.scalping.entry_split_order_plan import build_probe_residual_orders


def _receipt(**updates):
    result = {
        "evaluation_attempt_id": "aims-test-1",
        "entry_primary_decision_owner": "mechanistic_entry_adjudicator",
        "entry_mechanistic_action": "ENTER_NOW",
        "entry_ai_screen_pass": True,
    }
    result.update(updates)
    return result


def _priced(order):
    return {
        **order,
        "entry_price_owner": PRICE_OWNER,
        "entry_price_policy_version": "mechanistic_entry_price_p1_baseline_v1",
        "entry_price_policy_sha256": ENTRY_PRICE_POLICY_SHA256,
        "entry_price_receipt_sha256": "b" * 64,
        "entry_price_captured_at": 1_789_480_000.0,
        "entry_price_route": "KRX",
        "entry_price_epoch": "epoch-1",
    }


def _write_policy(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_dated_price_and_integrated_sizing_policies_bind_without_new_authority(
    tmp_path, monkeypatch
):
    active_date = "2026-09-16"
    price_payload = {
        "schema_version": MECHANISTIC_ENTRY_PRICE_POLICY_SCHEMA,
        "policy_owner": PRICE_OWNER,
        "policy_version": "mechanistic:test",
        "source_date": "2026-09-15",
        "active_date": active_date,
        "candidate_id": "normal:25",
        "runtime_env": {"KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS": "25"},
        "provider_calls": 0,
        "ai_price_authority": False,
        "runtime_apply_allowed": True,
    }
    price_path, price_sha = _write_policy(tmp_path, "price.json", price_payload)
    for suffix, value in {
        "ENABLED": "true",
        "FILE": str(price_path),
        "VERSION": "mechanistic:test",
        "SOURCE_DATE": "2026-09-15",
        "ACTIVE_DATE": active_date,
        "SHA256": price_sha,
    }.items():
        monkeypatch.setenv(f"KORSTOCKSCAN_MECHANISTIC_ENTRY_PRICE_POLICY_{suffix}", value)
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS", "25")

    policy, status = runtime_mechanistic_entry_price_policy(active_date=active_date)

    assert status == "loaded"
    assert policy["candidate_id"] == "normal:25"
    assert policy["provider_calls"] == 0

    quantity_path, quantity_sha = _write_policy(
        tmp_path, "quantity.json", {"policy_version": "qty:test"}
    )
    split_path, split_sha = _write_policy(
        tmp_path, "split.json", {"policy_version": "split:test"}
    )
    sizing_payload = {
        "schema_version": ENTRY_EXECUTION_SIZING_POLICY_SCHEMA,
        "policy_owner": OWNER,
        "policy_version": "sizing:test",
        "source_date": "2026-09-15",
        "active_date": active_date,
        "quantity_policy_version": "qty:test",
        "quantity_policy_file": str(quantity_path),
        "quantity_policy_sha256": quantity_sha,
        "split_policy_version": "split:test",
        "split_policy_file": str(split_path),
        "split_policy_sha256": split_sha,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_conservation_required": True,
        "runtime_apply_allowed": True,
    }
    sizing_path, sizing_sha = _write_policy(tmp_path, "sizing.json", sizing_payload)
    for suffix, value in {
        "ENABLED": "true",
        "FILE": str(sizing_path),
        "VERSION": "sizing:test",
        "SOURCE_DATE": "2026-09-15",
        "ACTIVE_DATE": active_date,
        "SHA256": sizing_sha,
    }.items():
        monkeypatch.setenv(f"KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_{suffix}", value)
    _freeze_kst_clock(monkeypatch, "2026-09-16T10:00:00+09:00")
    priced = _priced({"qty": 1, "price": 1000})
    priced["entry_price_policy_version"] = "mechanistic:test"
    priced["entry_price_policy_sha256"] = price_sha

    _, fields = compose_entry_execution_sizing_plan(
        [priced],
        expected_total_qty=1,
        action_receipt=_receipt(),
        quantity_policy_version="qty:test",
        split_policy_version="split:test",
    )

    assert fields["entry_execution_sizing_valid"] is True
    assert fields["entry_execution_sizing_policy"] == "sizing:test"
    assert fields["entry_execution_sizing_migration_baseline"] is False

    # A freshly dated policy cannot downgrade to an old proof-less contract.
    sizing_payload.update(source_date="2026-09-17", active_date="2026-09-18")
    _, sizing_sha = _write_policy(tmp_path, "sizing.json", sizing_payload)
    for suffix, value in {"SOURCE_DATE": "2026-09-17", "ACTIVE_DATE": "2026-09-18", "SHA256": sizing_sha}.items():
        monkeypatch.setenv(f"KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_{suffix}", value)
    policy, status = runtime_entry_execution_sizing_policy(active_date="2026-09-18")
    assert policy is None
    assert status == "selection_evidence_invalid"


def test_dated_sizing_policy_rejects_cross_owner_version_mismatch(
    tmp_path, monkeypatch
):
    quantity_path, quantity_sha = _write_policy(
        tmp_path, "quantity.json", {"policy_version": "qty:candidate"}
    )
    split_path, split_sha = _write_policy(
        tmp_path, "split.json", {"policy_version": "split:candidate"}
    )
    payload = {
        "schema_version": ENTRY_EXECUTION_SIZING_POLICY_SCHEMA,
        "policy_owner": OWNER,
        "policy_version": "sizing:test",
        "source_date": "2026-09-15",
        "active_date": "2026-09-16",
        "quantity_policy_version": "qty:candidate",
        "quantity_policy_file": str(quantity_path),
        "quantity_policy_sha256": quantity_sha,
        "split_policy_version": "split:candidate",
        "split_policy_file": str(split_path),
        "split_policy_sha256": split_sha,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_conservation_required": True,
        "runtime_apply_allowed": True,
    }
    path, sha = _write_policy(tmp_path, "sizing.json", payload)
    for suffix, value in {
        "ENABLED": "true",
        "FILE": str(path),
        "VERSION": "sizing:test",
        "SOURCE_DATE": "2026-09-15",
        "ACTIVE_DATE": "2026-09-16",
        "SHA256": sha,
    }.items():
        monkeypatch.setenv(f"KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_{suffix}", value)
    _freeze_kst_clock(monkeypatch, "2026-09-16T10:00:00+09:00")

    _, fields = compose_entry_execution_sizing_plan(
        [_priced({"qty": 1, "price": 1000})],
        expected_total_qty=1,
        action_receipt=_receipt(),
        quantity_policy_version="qty:incumbent",
        split_policy_version="split:incumbent",
    )

    assert fields["entry_execution_sizing_valid"] is False
    assert "integrated_quantity_policy_version_mismatch" in fields[
        "entry_execution_sizing_blockers"
    ]


def test_dated_sizing_policy_rejects_referenced_policy_hash_drift(
    tmp_path, monkeypatch
):
    quantity_path, quantity_sha = _write_policy(
        tmp_path, "quantity.json", {"policy_version": "qty:candidate"}
    )
    split_path, split_sha = _write_policy(
        tmp_path, "split.json", {"policy_version": "split:candidate"}
    )
    payload = {
        "schema_version": ENTRY_EXECUTION_SIZING_POLICY_SCHEMA,
        "policy_owner": OWNER,
        "policy_version": "sizing:test",
        "source_date": "2026-09-15",
        "active_date": "2026-09-16",
        "quantity_policy_version": "qty:candidate",
        "quantity_policy_file": str(quantity_path),
        "quantity_policy_sha256": quantity_sha,
        "split_policy_version": "split:candidate",
        "split_policy_file": str(split_path),
        "split_policy_sha256": split_sha,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_conservation_required": True,
        "runtime_apply_allowed": True,
    }
    path, sha = _write_policy(tmp_path, "sizing.json", payload)
    for suffix, value in {
        "ENABLED": "true",
        "FILE": str(path),
        "VERSION": "sizing:test",
        "SOURCE_DATE": "2026-09-15",
        "ACTIVE_DATE": "2026-09-16",
        "SHA256": sha,
    }.items():
        monkeypatch.setenv(f"KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_{suffix}", value)
    _freeze_kst_clock(monkeypatch, "2026-09-16T10:00:00+09:00")
    quantity_path.write_text('{"policy_version":"drifted"}', encoding="utf-8")

    _, fields = compose_entry_execution_sizing_plan(
        [_priced({"qty": 1, "price": 1000})],
        expected_total_qty=1,
        action_receipt=_receipt(),
        quantity_policy_version="qty:candidate",
        split_policy_version="split:candidate",
    )

    assert fields["entry_execution_sizing_valid"] is False
    assert "entry_execution_sizing_referenced_policy_hash_invalid" in fields[
        "entry_execution_sizing_blockers"
    ]


def test_atomic_plan_preserves_existing_multi_leg_shape_and_quantity():
    original = [
        _priced(
            {
                "qty": 2,
                "price": 1000,
                "entry_split_order_execution_mode": "resolver_limit",
            }
        ),
        _priced(
            {
                "qty": 1,
                "price": 995,
                "entry_split_order_execution_mode": "resolver_limit",
            }
        ),
    ]

    orders, fields = compose_entry_execution_sizing_plan(
        original,
        expected_total_qty=3,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert [item["qty"] for item in orders] == [2, 1]
    assert [item["price"] for item in orders] == [1000, 995]
    assert fields["entry_execution_sizing_valid"] is True
    assert fields["entry_execution_sizing_quantity_conservation_holds"] is True
    assert fields["entry_execution_sizing_policy"] == POLICY_VERSION
    assert fields["entry_price_plan_schema"] == "entry_price_plan_v1"
    assert (
        fields["entry_price_plan_id"]
        == fields["entry_execution_sizing_plan"]["price_plan_id"]
    )
    assert (
        fields["entry_price_plan_sha256"]
        == fields["entry_execution_sizing_plan"]["price_plan_sha256"]
    )
    assert all(item["entry_execution_sizing_plan_id"] for item in orders)
    assert all(
        item["entry_price_plan_id"] == fields["entry_price_plan_id"] for item in orders
    )
    assert fields["entry_execution_sizing_plan"]["legs"] == [
        {
            "leg_index": 1,
            "qty": 2,
            "price_candidate_id": "resolver_limit",
            "price_leg_id": "resolver_limit:leg1",
            "numeric_price": 1000,
            "execution_phase": "immediate",
        },
        {
            "leg_index": 2,
            "qty": 1,
            "price_candidate_id": "resolver_limit",
            "price_leg_id": "resolver_limit:leg2",
            "numeric_price": 995,
            "execution_phase": "immediate",
        },
    ]
    assert fields["entry_price_source_receipt_sha256"] == "b" * 64


def test_probe_and_frozen_residual_share_one_conserved_plan():
    continuation = {
        "requested_qty": 4,
        "residual_qty": 3,
        "residual_quantities": [2, 1],
        "common_fields": {},
    }
    orders, fields = compose_entry_execution_sizing_plan(
        [
            _priced(
                {
                    "qty": 1,
                    "price": 1000,
                    "order_type_code": "3",
                    "entry_split_order_execution_mode": "probe_first_market",
                    "entry_split_order_probe_continuation": continuation,
                }
            )
        ],
        expected_total_qty=4,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert fields["entry_execution_sizing_valid"] is True
    assert fields["entry_execution_sizing_immediate_qty"] == 1
    assert fields["entry_execution_sizing_deferred_qty"] == 3
    assert [leg["qty"] for leg in fields["entry_execution_sizing_plan"]["legs"]] == [
        1,
        2,
        1,
    ]
    assert (
        orders[0]["entry_split_order_probe_continuation"]["common_fields"][
            "entry_execution_sizing_plan_id"
        ]
        == fields["entry_execution_sizing_plan_id"]
    )
    residual, receipt = build_probe_residual_orders(
        orders[0]["entry_split_order_probe_continuation"],
        probe_fill_price=1000,
        best_bid=995,
        best_ask=1000,
    )
    assert receipt["allowed"] is True
    assert [item["price_candidate_id"] for item in residual] == [
        "probe_residual_resolver:leg2",
        "probe_residual_resolver:leg3",
    ]
    assert all(
        item["entry_execution_sizing_plan_id"]
        == fields["entry_execution_sizing_plan_id"]
        for item in residual
    )


def test_plan_rejects_quantity_increase_or_missing_action_authority():
    _, increased = compose_entry_execution_sizing_plan(
        [_priced({"qty": 3, "price": 1000})],
        expected_total_qty=2,
        action_receipt=_receipt(),
        quantity_policy_version=None,
        split_policy_version=None,
    )
    _, unauthorized = compose_entry_execution_sizing_plan(
        [_priced({"qty": 1, "price": 1000})],
        expected_total_qty=1,
        action_receipt={},
        quantity_policy_version=None,
        split_policy_version=None,
    )

    assert increased["entry_execution_sizing_valid"] is False
    assert (
        "quantity_conservation_failed" in increased["entry_execution_sizing_blockers"]
    )
    assert unauthorized["entry_execution_sizing_valid"] is False
    assert (
        "action_receipt_id_missing" in unauthorized["entry_execution_sizing_blockers"]
    )


def test_plan_accepts_one_price_candidate_shared_by_all_legs():
    shared_candidate = "mechanistic:shared"
    orders = [
        _priced({"qty": 1, "price": 1000, "price_candidate_id": shared_candidate}),
        _priced({"qty": 1, "price": 995, "price_candidate_id": shared_candidate}),
    ]

    planned, fields = compose_entry_execution_sizing_plan(
        orders,
        expected_total_qty=2,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert fields["entry_execution_sizing_valid"] is True
    assert {item["price_candidate_id"] for item in planned} == {shared_candidate}
    assert len({item["entry_price_leg_id"] for item in planned}) == 2


def test_plan_rejects_conflicting_price_candidates_or_duplicate_leg_identity():
    conflicting = [
        _priced({"qty": 1, "price": 1000, "price_candidate_id": "candidate-a"}),
        _priced({"qty": 1, "price": 995, "price_candidate_id": "candidate-b"}),
    ]
    duplicate_leg = [
        _priced(
            {
                "qty": 1,
                "price": 1000,
                "price_candidate_id": "candidate-a",
                "entry_price_leg_id": "duplicate-leg",
            }
        ),
        _priced(
            {
                "qty": 1,
                "price": 995,
                "price_candidate_id": "candidate-a",
                "entry_price_leg_id": "duplicate-leg",
            }
        ),
    ]

    _, conflicting_fields = compose_entry_execution_sizing_plan(
        conflicting,
        expected_total_qty=2,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )
    _, duplicate_fields = compose_entry_execution_sizing_plan(
        duplicate_leg,
        expected_total_qty=2,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert "entry_price_candidate_conflict" in conflicting_fields[
        "entry_execution_sizing_blockers"
    ]
    assert "duplicate_price_leg_id" in duplicate_fields[
        "entry_execution_sizing_blockers"
    ]


def test_plan_rejects_price_owner_policy_hash_mismatch():
    order = _priced({"qty": 1, "price": 1000})
    order["entry_price_policy_sha256"] = "0" * 64

    _, fields = compose_entry_execution_sizing_plan(
        [order],
        expected_total_qty=1,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert fields["entry_execution_sizing_valid"] is False
    assert "entry_price_policy_sha256_missing_or_invalid" in fields[
        "entry_execution_sizing_blockers"
    ]


def test_plan_rejects_missing_price_owner_receipt_hash():
    order = _priced({"qty": 1, "price": 1000})
    order.pop("entry_price_receipt_sha256")

    _, fields = compose_entry_execution_sizing_plan(
        [order],
        expected_total_qty=1,
        action_receipt=_receipt(),
        quantity_policy_version="qty-v1",
        split_policy_version="leg-v1",
    )

    assert fields["entry_execution_sizing_valid"] is False
    assert "entry_price_source_receipt_sha256_missing_or_conflicting" in fields[
        "entry_execution_sizing_blockers"
    ]


def test_scale_in_plan_keeps_avg_down_and_pyramid_namespaces_separate():
    avg_orders, avg_fields = compose_scale_in_execution_sizing_plan(
        [
            {"qty": 2, "price": 995, "add_type": "AVG_DOWN"},
            {"qty": 1, "price": 990, "add_type": "AVG_DOWN"},
        ],
        authorized_total_qty=3,
        action_receipt={
            "should_add": True,
            "add_type": "AVG_DOWN",
            "scale_in_action_owner": "avg_down_action_owner",
            "scale_in_action_receipt_schema": "scale_in_action_receipt_v1",
            "scale_in_decision_id": "avgdn-decision-" + ("a" * 32),
            "position_episode_id": "main-life:avg-down-test",
        },
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="scale-in-split:test",
        price_policy_version="scale_in_price_resolver_p1",
    )
    pyramid_orders, pyramid_fields = compose_scale_in_execution_sizing_plan(
        [{"qty": 2, "price": 1005, "add_type": "PYRAMID"}],
        authorized_total_qty=2,
        action_receipt={
            "should_add": True,
            "add_type": "PYRAMID",
            "scale_in_action_owner": "pyramid_action_owner",
            "scale_in_action_receipt_schema": "scale_in_action_receipt_v1",
            "scale_in_decision_id": "pyr-decision-" + ("b" * 32),
            "position_episode_id": "main-life:pyramid-test",
        },
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version=None,
        price_policy_version="scale_in_price_resolver_p1",
    )

    assert avg_fields["scale_in_execution_sizing_valid"] is True
    assert avg_fields["scale_in_price_plan_schema"] == "scale_in_price_plan_v1"
    assert (
        avg_fields["scale_in_price_plan_id"]
        == avg_fields["scale_in_execution_sizing_plan"]["price_plan_id"]
    )
    assert (
        avg_orders[0]["scale_in_price_plan_id"] == avg_fields["scale_in_price_plan_id"]
    )
    assert avg_fields["scale_in_execution_sizing_stage"] == "AVG_DOWN"
    assert avg_fields["scale_in_execution_sizing_total_qty"] == 3
    assert [order["qty"] for order in avg_orders] == [2, 1]
    assert pyramid_fields["scale_in_execution_sizing_valid"] is True
    assert pyramid_fields["scale_in_execution_sizing_stage"] == "PYRAMID"
    assert pyramid_fields["scale_in_execution_sizing_policy"] == (
        "pyramid_execution_sizing_baseline_v1"
    )
    assert (
        avg_fields["scale_in_execution_sizing_plan_id"]
        != (pyramid_fields["scale_in_execution_sizing_plan_id"])
    )
    assert pyramid_orders[0]["qty"] == 2


def test_scale_in_plan_fails_closed_on_owner_or_quantity_escalation():
    _, fields = compose_scale_in_execution_sizing_plan(
        [{"qty": 3, "price": 1000, "add_type": "AVG_DOWN"}],
        authorized_total_qty=2,
        action_receipt={
            "should_add": True,
            "add_type": "AVG_DOWN",
            "scale_in_action_owner": "pyramid_action_owner",
            "scale_in_action_receipt_schema": "scale_in_action_receipt_v1",
            "scale_in_decision_id": "avgdn-decision-" + ("c" * 32),
            "position_episode_id": "main-life:avg-down-test",
        },
        quantity_policy_version=None,
        split_policy_version=None,
        price_policy_version=None,
    )

    assert fields["scale_in_execution_sizing_valid"] is False
    assert (
        "scale_in_action_owner_invalid" in fields["scale_in_execution_sizing_blockers"]
    )
    assert "quantity_increase_detected" in fields["scale_in_execution_sizing_blockers"]
    assert fields["scale_in_execution_sizing_quantity_conservation_holds"] is False


def test_scale_in_plan_rejects_quantity_below_final_authorized_total():
    _, fields = compose_scale_in_execution_sizing_plan(
        [{"qty": 1, "price": 1000, "add_type": "AVG_DOWN"}],
        authorized_total_qty=2,
        action_receipt={
            "should_add": True,
            "add_type": "AVG_DOWN",
            "scale_in_action_owner": "avg_down_action_owner",
            "scale_in_action_receipt_schema": "scale_in_action_receipt_v1",
            "scale_in_decision_id": "avgdn-decision-" + ("d" * 32),
            "position_episode_id": "main-life:avg-down-test",
        },
        quantity_policy_version=None,
        split_policy_version=None,
        price_policy_version=None,
    )

    assert fields["scale_in_execution_sizing_valid"] is False
    assert "quantity_conservation_failed" in fields[
        "scale_in_execution_sizing_blockers"
    ]


def _freeze_kst_clock(monkeypatch, value):
    instant = datetime.fromisoformat(value)

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is not None
            return instant.astimezone(tz)

    monkeypatch.setattr(sizing, "datetime", FixedClock)


def test_default_runtime_policy_date_uses_kst_during_utc_date_boundary(tmp_path, monkeypatch):
    _freeze_kst_clock(monkeypatch, "2026-09-17T16:00:00+00:00")
    prefix = "TEST_DATED_POLICY_"
    payload = {
        "schema_version": "test-schema", "policy_owner": "test-owner",
        "policy_version": "v1", "source_date": "2026-09-17",
        "active_date": "2026-09-18", "runtime_apply_allowed": True,
    }
    path, sha = _write_policy(tmp_path, "dated.json", payload)
    for suffix, value in {
        "ENABLED": "true", "FILE": str(path), "VERSION": "v1",
        "SOURCE_DATE": "2026-09-17", "ACTIVE_DATE": "2026-09-18", "SHA256": sha,
    }.items():
        monkeypatch.setenv(prefix + suffix, value)
    assert sizing._runtime_policy(prefix=prefix, schema="test-schema", owner="test-owner") == (payload, "loaded")
    assert sizing._runtime_policy(prefix=prefix, schema="test-schema", owner="test-owner", active_date="2026-09-17") == (None, "policy_inactive_date")


def test_price_policy_authority_cannot_alias_boolean_or_sizing_env():
    payload = {
        "policy_owner": PRICE_OWNER, "candidate_id": "normal:25",
        "provider_calls": 0, "ai_price_authority": False,
        "runtime_env": {"KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS": "25"},
    }
    assert sizing.mechanistic_entry_price_authority_valid(payload)
    for update in (
        {"provider_calls": False}, {"provider_calls": 0.0},
        {"action_quantity_leg_scale_in_authority": True},
        {"runtime_env": {"KORSTOCKSCAN_SCALPING_MAX_QTY": "25"}},
        {"runtime_env": {}},
        {"runtime_env": {"KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS": True}},
        {"runtime_env": {"KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS": 25.9}},
    ):
        assert not sizing.mechanistic_entry_price_authority_valid({**payload, **update})


def test_atomic_sizing_never_truncates_fractional_or_boolean_quantity_and_price(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_ENABLED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_MECHANISTIC_ENTRY_PRICE_POLICY_ENABLED", raising=False)
    for bad in (True, 1.9, float("nan"), float("inf")):
        for field in ("qty", "price"):
            order = _priced({"qty": 1, "price": 1000, field: bad})
            _, fields = compose_entry_execution_sizing_plan(
                [order], expected_total_qty=1, action_receipt=_receipt(),
                quantity_policy_version="qty:current", split_policy_version="split:current",
            )
            assert fields["entry_execution_sizing_valid"] is False
    assert sizing._positive_int(9007199254740993) == 9007199254740993
    assert sizing._positive_int("25") == 25


def test_replay_anchor_uses_plan_issue_clock_without_refreshing_original_quote():
    from src.tests.test_strategy_owner_replay import entry_owner_event
    event = entry_owner_event()
    plan = event.fields['entry_execution_sizing_plan']
    quote_at = datetime.fromisoformat(event.emitted_at).timestamp()
    original = _priced({'qty': 10, 'price': 10000, 'order_type_code': '00'})
    original.update(entry_price_current_price=10020, entry_price_captured_at=quote_at)
    orders, fields = compose_entry_execution_sizing_plan([original], expected_total_qty=10,
        action_receipt=_receipt(evaluation_attempt_id=plan['action_receipt_id'],
            scanner_promotion_id=plan['scanner_promotion_id'], policy_bundle_hash='a' * 64,
            effective_venue='KRX', market_session_bucket='KRX_REGULAR'),
        quantity_policy_version='qty-original', split_policy_version='leg-original',
        replay_context={'stock_code': '005930', 'observed_at': quote_at + 2,
                        'profile': 'strong_1tick_pressure', 'profile_bps': 11})
    seed = fields['entry_opportunity_replay_seed']
    assert datetime.fromisoformat(seed['observed_at']).timestamp() == quote_at + 2
    assert orders[0]['entry_price_captured_at'] == quote_at
    assert fields['entry_execution_sizing_plan']['price_candidates'][0]['captured_at'] == quote_at


def test_before_ai_observation_is_not_a_submit_pass_and_keeps_frozen_seed():
    from src.engine.sniper_missed_entry_counterfactual import _price_ready_plan, EntryEvent, _load_entry_events
    from src.engine.monitoring.research_closed_loop import digest
    clock = datetime.fromisoformat('2026-09-18T10:00:00+09:00').timestamp()
    order = _priced({'qty': 10, 'price': 10000, 'order_type_code': '00'})
    order.update(entry_price_current_price=10020, entry_price_captured_at=clock)
    receipt = _receipt(entry_ai_screen_pass=False, scanner_promotion_id='pre-ai-p',
        effective_venue='KRX', market_session_bucket='KRX_REGULAR', machine_bundle_sha256='a'*64)
    kwargs = dict(expected_total_qty=10, action_receipt=receipt, quantity_policy_version='qty-original',
        split_policy_version='leg-original', replay_context={'stock_code': '005930', 'observed_at': clock})
    _, actual = compose_entry_execution_sizing_plan([order], **kwargs)
    assert actual['entry_execution_sizing_valid'] is False
    _, observed = compose_entry_execution_sizing_plan([order], observation_only=True, **kwargs)
    assert observed['entry_execution_sizing_valid'] is True
    seed = observed['entry_opportunity_replay_seed']
    seed['retained_owner_metadata'] = 'x' * 32000
    seed['seed_sha256'] = digest({k:v for k,v in seed.items() if k != 'seed_sha256'})
    row = dict(pipeline='ENTRY_PIPELINE', stock_code='005930', stock_name='TEST', record_id=1,
        stage='entry_ai_economic_plan_observed', emitted_at='2026-09-18T10:00:00+09:00',
        emitted_date='2026-09-18', fields=observed)
    decoded = _load_entry_events('2026-09-18', rows=[row])[0]
    assert decoded.fields['entry_opportunity_replay_seed'] == seed
    assert _price_ready_plan(decoded)['observation_only'] is True
    assert _price_ready_plan(EntryEvent(decoded.emitted_at, decoded.signal_date, decoded.name,
        decoded.code, 'entry_execution_sizing_plan', decoded.record_id, decoded.fields)) == {}
    # Hypothetical plans retain the actual machine action; live plans still
    # require ENTER_NOW and an actual auxiliary PASS.
    for action in ('BLOCK', 'RECHECK'):
        scoped = {**kwargs, 'action_receipt': {**receipt, 'entry_mechanistic_action': action}}
        _, observed = compose_entry_execution_sizing_plan([order], observation_only=True, **scoped)
        assert observed['entry_execution_sizing_valid'] is True
        assert observed['entry_execution_sizing_plan']['observed_machine_action'] == action
        _, blocked = compose_entry_execution_sizing_plan([order], **scoped)
        assert blocked['entry_execution_sizing_valid'] is False



@pytest.mark.parametrize('machine_action', ['ENTER_NOW', 'BLOCK', 'RECHECK'])
@pytest.mark.parametrize('guard_allowed,broker_route,venue,session', [
    (True,'KRX','KRX','KRX_REGULAR'),(False,'SOR','KRX','KRX_REGULAR'),
    (True,'SOR','KRX','KRX_REGULAR'),(True,'SOR','NXT','NXT_PREMARKET'),
    (True,'SOR','KRX_NXT_INTEGRATED','KRX_NXT_AFTERMARKET'),
    (True,'SOR','NXT','NXT_REGULAR_OVERLAP'),(True,'SOR','NXT','NXT_AFTERMARKET')])
def test_runtime_pre_ai_producer_freezes_owner_inputs_without_submit(monkeypatch, tmp_path, guard_allowed,broker_route,venue,session,machine_action):
    from copy import deepcopy
    from src.engine import kiwoom_sniper_v2 as runtime
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping import entry_split_order_plan as split
    from src.engine.scalping import strategy_owner_replay as replay
    from src.engine.scalping import avg_down_replay_capture as capture_owner
    from src.engine.sniper_missed_entry_counterfactual import _load_entry_events, _price_ready_plan
    from src.tests.test_pipeline_event_logger import _reset_logger_state
    from src.utils import pipeline_event_logger as logger
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(split, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(logger, 'log_info', lambda *a,**k: None)
    monkeypatch.setattr(logger, 'TRADING_RULES', SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True,
        PIPELINE_EVENT_SCHEMA_VERSION=3, PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False))
    monkeypatch.setattr(handlers, 'emit_pipeline_event', logger.emit_pipeline_event)
    monkeypatch.setattr(handlers, 'observe_candidate_transition_safe', lambda *a,**k: None)
    monkeypatch.setattr(handlers, '_maybe_register_rising_missed_nxt_downstream_block_sampler', lambda *a,**k: None)
    for name in capture_owner.GLOBALS:
        monkeypatch.setattr(handlers,name,set() if name=='ALERTED_STOCKS' else {})
    monkeypatch.setattr(handlers, '_is_any_simulated_position', lambda *a,**k: False)
    monkeypatch.setattr(handlers, '_apply_general_entry_margin_budget_authority', lambda b,**k: b)
    # Only external account source and market guard boundary are controlled.
    # Sizing, price owner, atomic writer and frozen operating producer run normally.
    requests=[]
    def broker_capacity(code, price, fallback, **kwargs):
        requests.append((code, price, fallback, kwargs))
        return {'budget_base':500000,'cash_orderable_qty_cap':40,'kt00011_error':'',
                'kt00011_capacity_source_sha256':'9'*64,
                'kt00011_cash_orderable_contract_status':'valid',
                'kt00011_capacity_observed_at':frozen_clock.isoformat(),
                'kt00011_requested_stock_code':code,'kt00011_requested_unit_price':price,
                'account_deposit':500000,'cash_orderable_amount':400800,
                'budget_source':'kt00011_min_account_deposit_cash_orderable'}
    monkeypatch.setattr(handlers, '_resolve_scalp_cash_budget_context', broker_capacity)
    def guard(**kwargs):
        kwargs['stock']['research_mutation'] = True
        return {'allowed':guard_allowed,'reason':'fixture_guard_block','latency_state':'SAFE',
            'orders':[{'qty':kwargs['planned_qty'],'price':10000,'order_type_code':'00'}]}
    monkeypatch.setattr(handlers, 'evaluate_live_buy_entry', guard)
    # Frozen policy snapshot is a source fixture, not an actual SELL receipt.
    from src.tests.test_avg_down_policy_replay import exit_fixture
    policy_observation, _ = exit_fixture()
    policy_snapshot = deepcopy(policy_observation['policy_snapshot'])
    day = datetime.now(sizing.KST).date().isoformat()
    slot='08:15:00' if 'PREMARKET' in session else '15:45:00' if session=='NXT_AFTERMARKET' else '16:15:00' if 'AFTERMARKET' in session else '10:00:00'
    frozen_clock=datetime.fromisoformat(day+'T'+slot+'+09:00')
    class FixedDatetime(datetime):
        @classmethod
        def now(cls,tz=None):
            return frozen_clock.astimezone(tz) if tz else frozen_clock.replace(tzinfo=None)
    monkeypatch.setattr(handlers.time,'time',lambda: frozen_clock.timestamp())
    monkeypatch.setattr(logger,'datetime',FixedDatetime)
    policy_snapshot['environment']['KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE'] = day
    policy_snapshot['files']={key.replace('2026-09-04',day):value for key,value in policy_snapshot['files'].items()}
    monkeypatch.setattr(capture_owner, '_cached_policy', lambda *a: policy_snapshot)
    stock={'name':'TEST','id':1,'strategy':'SCALPING','source_signature':'scanner-confirmed','is_nxt':True,
        'scanner_promotion_id':'promotion-pre-ai','code':'005930',
        'entry_economic_watch_lifetime': {
            'owner':'kiwoom_sniper_v2._scanner_evaluation_lifetime_anchor/_scalping_watching_ttl_sec',
            'scanner_promotion_id':'promotion-pre-ai','deadline_epoch':frozen_clock.timestamp()+1800,
            'observed_epoch':frozen_clock.timestamp()}}

    before=deepcopy(stock)
    ws={'curr':10020,'effective_route':replay.entry_native_market_venue(venue),'source_epoch':'epoch-1'}
    exact={'current':{'price':10020},'session_bucket':session,'broker_route':broker_route,
           'orderbook_top1':{'bid':{'price':10000},'ask':{'price':10010}}}
    receipt={'evaluation_attempt_id':'pre-ai-live','scanner_promotion_id':'promotion-pre-ai',
             'effective_venue':venue,'session_bucket':session}
    result=handlers._observe_entry_economics_before_ai(stock,'005930',ws,
        exact_payload=exact,assessment={'action':machine_action},capture=receipt,bundle_sha256='a'*64)
    assert stock == before
    assert requests == [('005930',10020,0,{'source_only':True})]
    logger.flush_pipeline_event_producer_summary()
    day=datetime.now(sizing.KST).date().isoformat()
    events, source_contract=split._bounded_execution_projection(day)
    assert source_contract['producer_census']['identity_conservation_holds'] is True
    assert len(events)==1
    if guard_allowed:
        assert result['entry_economic_source_status']=='recorded_source_only', result
        event=_load_entry_events(day,rows=events)[0]
        plan=_price_ready_plan(event)
        assert plan['observation_only'] is True
        seed=json.loads(event.fields['entry_opportunity_replay_seed'])
        assert replay._entry_seed_valid(seed)
        assert seed['operating_contract']['budget_krw'] > 0
        capital = seed['operating_contract']['capital_source']
        assert capital['status'] == 'recorded_source_only'
        assert capital['capacity_source_sha256'] == '9'*64
        assert capital['components']['cash_orderable_amount'] == 400800
        assert seed['operating_contract']['nxt_listing_receipt']['value'] is True
        assert seed['operating_contract']['nxt_listing_receipt']['owner']=='stock.is_nxt'
        assert seed['actual_order_submitted'] is False
        assert events[0]['fields']['entry_ai_screen_pass']=='False'
        assert plan['observed_machine_action'] == machine_action
        if machine_action != 'ENTER_NOW':
            # No synthetic auxiliary response or zero-latency decision receipt.
            assert not any(e['stage'] == 'entry_ai_economic_decision_available' for e in events)
            def forbidden_native(*args, **kwargs):
                raise AssertionError('No native replay or AI call for a plan-only anchor')
            preserved = replay.build_entry_opportunity_replays(day, [event],
                evaluated_at=frozen_clock.timestamp()+3600,
                source_stage='entry_ai_economic_plan_observed', micro_loader=forbidden_native)
            assert preserved['counts']['nonentry_plan_only'] == 1
            assert preserved['counts']['source_gap'] == 0
            assert preserved['rows'][0]['seed'] == seed
            from src.engine.scalping import ai_action_outcome_calibration as main
            from src.engine.scalping import compact_auxiliary_paired_replay as compact
            path = tmp_path / 'report/entry_split_order_plan' / f'entry_split_order_plan_{day}.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'input_summary': {'compact_pre_ai_execution_replay': preserved}}))
            projection = main._machine_operating_projection(tmp_path, [day])
            assert compact.valid(projection)
            assert len(projection['rows']) == 1
            source = projection['rows'][0]
            assert main._machine_nonentry_seed(source) == seed
            assert source['incumbent_verdict'] is None
            if machine_action == 'RECHECK':
                runtime._record_machine_watch_terminal(stock, now_ts=frozen_clock.timestamp()+1801)
                logger.flush_pipeline_event_producer_summary()
                final_events, final_census = split._bounded_execution_projection(day)
                assert final_census['producer_census']['identity_conservation_holds']
                closed = replay.build_entry_opportunity_replays(day, _load_entry_events(day, rows=final_events),
                    evaluated_at=frozen_clock.timestamp()+3600, source_stage='entry_ai_economic_plan_observed',
                    micro_loader=forbidden_native)
                assert closed['rows'][0]['machine_watch_terminal']['deadline_epoch'] == frozen_clock.timestamp()+1800
                source['owner_replay'] = closed['rows'][0]
                row = dict(decision_trace_id='machine-recheck', operating_comparison_input=source,
                    comparison={'incumbent_machine_action':'RECHECK','control_action':'WAIT'},
                    machine_sequence_members=['machine-recheck'], setup_evidence={})
                monkeypatch.setattr(main,'mechanistic_entry_policy_decision',lambda *a,**kw:{'action':'RECHECK'})
                economics = main._machine_sequence_operating_metrics([row], set(), {})
                assert economics['status'] == 'supported_operating_comparison', economics
                assert economics['daily_net_profit_delta_krw'] == 0.
            return
        # The actual source producer's frozen input reaches the existing full
        # holding interpreter. Only account and native market sources are
        # controlled; there is no manually fabricated operating-arm result.
        from src.tests.test_strategy_owner_replay import entry_native_path
        from src.utils.pipeline_event_logger import emit_pipeline_event
        available_at = frozen_clock.isoformat()
        emit_pipeline_event('ENTRY_PIPELINE','TEST','005930','entry_ai_economic_decision_available',
            fields=dict(evaluation_attempt_id=receipt['evaluation_attempt_id'],
                entry_economic_plan_sha256=result['entry_economic_plan_sha256'],
                entry_economic_decision_available_at=available_at))
        logger.flush_pipeline_event_producer_summary()
        retained, _ = split._bounded_execution_projection(day)
        def native_loader(day, root, symbols, anchors, manifest, canary, evaluated_at):
            windows={}
            for anchor in anchors:
                depths,trades=entry_native_path({'observed_at':anchor['anchor_at']})
                native_venue=replay.entry_native_market_venue(venue)
                for tick in trades:
                    tick.update(venue=native_venue,session_bucket=session)
                for frame in depths:
                    frame.update(venue=native_venue,session_bucket=session,item='005930'+({'NXT':'_NX','SOR':'_AL'}.get(native_venue,'')),
                        orderbook_time_raw=datetime.fromisoformat(frame['exchange_timestamp']).strftime('%H%M%S'))
                    if native_venue=='SOR':
                        frame['route_depth_totals']={'combined':{'bid':1000,'ask':800},
                            'KRX':{'bid':600,'ask':400},'NXT':{'bid':400,'ask':400}}
                    at=datetime.fromisoformat(frame['exchange_timestamp']).timestamp()
                    bid,ask=(9980,9990) if frame['source_sequence']<=1 else (9500,9510)
                    frame.update(best_bid=bid,best_ask=ask,bid_levels=[[1,bid,1000]],ask_levels=[[1,ask,800]],
                        ws_data=dict(curr=bid,best_bid=bid,best_ask=ask,best_bid_qty=1000,best_ask_qty=800,
                            last_ws_update_ts=at,last_realtime_type_ts={'0D':at},quote_stale=False))
                    capture_owner.record_main_market_regime('BULL', now_ts=at)
                    frame['recorded_inputs']=capture_owner.recorded_market_inputs('005930',cutoff_ts=at)
                windows[anchor['anchor_id']]=dict(raw_depth_rows=depths,raw_market_rows=trades)
            return {'source_contract_ready':True},{},windows
        computed=replay.build_entry_opportunity_replays(day,_load_entry_events(day,rows=retained),
            source_stage='entry_ai_economic_plan_observed', micro_loader=native_loader,
            evaluated_at=datetime.fromisoformat(available_at).timestamp()+250)
        assert computed['counts']['unique_retained']==1
        assert computed['rows'][0]['status']=='completed_source_only', computed['rows'][0]
        operating=next(iter(computed['rows'][0]['operating_arms'].values()))
        assert operating['status']=='completed_source_only', operating['blocker']
        assert operating['net_pnl_krw']<0
        assert operating['stress_net_pnl_krw']<=operating['net_pnl_krw']
        assert operating['capital_krw_minutes']>0 and operating['reserve_krw_minutes']>0
        assert operating['actual_fill_evidence'] is False
        # Public request/response storage, not a manually assembled evaluator
        # input, joins the independently replayed source by exact attempt.
        from src.tests.test_ai_decision_trace import _enable
        from src.engine.scalping import ai_decision_trace as trace
        from src.engine.scalping import compact_auxiliary_paired_replay as compact
        from src.engine.scalping.mechanistic_entry_runtime_policy import AI_VERSION
        _enable(monkeypatch,tmp_path)
        monkeypatch.setattr(trace,'_now',lambda:frozen_clock)
        request=trace.capture_ai_request(prompt='fixture risk screen',user_input=exact,
            endpoint_name='analyze_target',symbol='005930',request_id='producer-risk-fixture',
            model='gpt-5.4-nano',schema_name='entry_setup_risk_adjudication_v1',require_json=True,
            metadata=dict(evaluation_attempt_id=receipt['evaluation_attempt_id'],
                scanner_promotion_id=receipt['scanner_promotion_id'],effective_venue=venue,session_bucket=session,broker_route=broker_route))
        stored=trace.record_ai_decision_trace({**request,**receipt,
            'machine_bundle_sha256':'a'*64,'entry_mechanistic_action':'ENTER_NOW',
            'entry_economic_plan_sha256':result['entry_economic_plan_sha256'],
            'semantic_validation_status':'pass','decision_quality_contract_status':'pass',
            'entry_ai_risk_verdict':'PASS','action':'BUY','score':80,'provider_actual':'openai',
            'ai_model_actual':'gpt-5.4-nano'},prompt_type='scalping_entry',prompt_version=AI_VERSION,
            result_source='live',stock_code='005930',provider_called=True)
        assert stored
        compact.write(tmp_path/'report/entry_split_order_plan'/f'entry_split_order_plan_{day}.json',
            {'input_summary':{'compact_pre_ai_execution_replay':computed}})
        projection=compact.prepare(tmp_path,day)
        assert len(projection['rows'])==1 and projection['rows'][0]['exclusion_reason'] is None
        row=projection['rows'][0]
        assert compact.owner_operating_arm(row['owner_replay'],row)['net_pnl_krw']==operating['net_pnl_krw']
        candidate=compact.sealed({'candidate_response':{'risk_verdict':'VETO'},
            'input_sha256':compact.input_identity(row),'validation_errors':[],
            'runtime_inference_cost_delta_krw':0.})
        comparison=compact.evaluate(projection['rows'],{row['evaluation_key']:candidate})
        assert comparison['delta_net_ev_pct']>0
        # Avoided modeled loss is not actual profit, and a single supported
        # source still cannot satisfy the independent model/candidate floors.
        assert compact.primary_input_blocker(row,{})[0]=='source_gap'
    else:
        prefix='common_guard_block:'
        assert result['entry_economic_source_blocker'].startswith(prefix)
        assert events[0]['stage']=='entry_ai_economic_source_gap'
    logger._flush_producer_summary_at_exit()
    monkeypatch.setattr(logger,'_PRODUCER_COMPACTOR',None)


def test_main_market_input_cache_is_action_neutral_and_cutoff_bound(monkeypatch):
    from src.engine.scalping import avg_down_replay_capture as capture
    monkeypatch.setattr(capture, '_MAIN_MARKET_REGIME', {})
    monkeypatch.setattr(capture, '_MARKET_INPUTS', {})
    capture.record_main_market_regime('BULL', now_ts=100.)
    assert capture.recorded_market_inputs('005930',cutoff_ts=101.)['market_regime']['value']=='BULL'
    assert capture.recorded_market_inputs('394800',cutoff_ts=101.)['market_regime']['value']=='BULL'
    assert not capture.recorded_market_inputs('005930',cutoff_ts=99.)
    assert not capture.recorded_market_inputs('005930',cutoff_ts=106.)
