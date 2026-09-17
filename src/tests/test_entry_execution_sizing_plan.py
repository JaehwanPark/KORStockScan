import hashlib
import json
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
