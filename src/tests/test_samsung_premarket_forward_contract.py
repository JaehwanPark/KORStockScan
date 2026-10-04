"""Frozen contract, null handling and honest source readiness; tmp inputs only."""
from copy import deepcopy
from datetime import datetime

import pytest

from src.engine.scalping import samsung_premarket_forward_contract as forward
from src.engine.scalping import mechanistic_entry_runtime_policy as M, entry_strategy_policy as S
from src.tests.test_mechanistic_entry_runtime_policy import source


@pytest.fixture
def contract(tmp_path, monkeypatch):
    bundle = M.publish(source(tmp_path, source_date="2026-10-02"), data_root=tmp_path,
        bootstrap=True, adopt_all_continuous=True,
        now=datetime(2026, 10, 3, 20, tzinfo=M.KST))
    # The fixture publisher's calendar targets the same reviewed next date.
    assert bundle["target_date"] == "2026-10-06"
    parent = M.for_cohort(bundle, forward.SCOPE)
    assert parent is not None
    # Bind reviewed anchors to tmp fixture values, never to a runtime writer.
    monkeypatch.setattr(forward, "REVIEWED_BUNDLE_SHA256", bundle["bundle_sha256"])
    monkeypatch.setattr(forward, "REVIEWED_PARENT_SHA256", S.digest(parent["machine_policy"]))
    return forward.freeze_contract(bundle)


def features(**changes):
    return dict(usable=True, past_exact_nx_bound=True, phase="distribution", delta=10,
                price_pct=0., proof=.7, depletion=100, refill=.2, downward=False, **changes)


def test_frozen_parent_scope_and_no_policy_authority(contract):
    forward.validate_contract(contract)
    assert [h["id"] for h in contract["hypotheses"]] == list(forward.IDS)
    assert contract["comparison"]["winner_retention_veto"] is False
    assert contract["comparison"]["parent_empty"].startswith("comparison_not_identifiable")
    assert contract["official_policy_candidate"] is None
    assert contract["allowed_runtime_apply"] is False


@pytest.mark.parametrize("price,phase,expected", [
    (0., "distribution", (True, True)), (.02, "distribution", (True, False)),
    (0., "range_or_no_setup", (False, True)), (-.02, "distribution", (False, False))])
def test_masks_compare_only_predecision_conditions(contract, price, phase, expected):
    f = features(); f.update(price_pct=price, phase=phase)
    result = forward.hypothesis_masks(f, guard_envelope=True, contract=contract)
    assert result["status"] == "observed" and tuple(result["masks"].values()) == expected


@pytest.mark.parametrize("key,value", [
    ("delta", None), ("proof", float("nan")), ("refill", None), ("price_pct", True),
    ("past_exact_nx_bound", False), ("phase", None), ("usable", False), ("downward", 0)])
def test_unknowns_never_become_zero_or_failed_binary(contract, key, value):
    f = features(); f[key] = value
    result = forward.hypothesis_masks(f, guard_envelope=True, contract=contract)
    assert result["status"] == "source_gap" and all(v is None for v in result["masks"].values())


@pytest.mark.parametrize("changes", [{"delta": -1}, {"proof": .49}, {"depletion": 0},
                                      {"refill": .51}, {"downward": True}])
def test_observed_nonconfirming_values_are_false(contract, changes):
    f = features(); f.update(changes)
    result = forward.hypothesis_masks(f, guard_envelope=True, contract=contract)
    assert result["status"] == "observed" and not any(result["masks"].values())


def test_hard_guard_exclusion_cannot_be_changed_by_strong_features(contract):
    result = forward.hypothesis_masks(features(), guard_envelope=False, contract=contract)
    assert result["status"] == "guard_excluded" and not any(result["masks"].values())


@pytest.mark.parametrize("guard", [None, 1, "unknown"])
def test_unknown_guard_proof_remains_null(contract, guard):
    result = forward.hypothesis_masks(features(), guard_envelope=guard, contract=contract)
    assert result["status"] == "source_gap" and all(v is None for v in result["masks"].values())


def test_legacy_krx_only_bundle_is_not_premarket_parent(tmp_path):
    bundle = M.publish(source(tmp_path, source_date="2026-10-02"), data_root=tmp_path,
        bootstrap=True, now=datetime(2026, 10, 3, 20, tzinfo=M.KST))
    with pytest.raises(ValueError, match="premarket_parent_missing"):
        forward.freeze_contract(bundle)


@pytest.mark.parametrize("field", ["confirmation", "model", "hypothesis", "success", "clock", "authority", "kernel"])
def test_rehashed_spec_changes_do_not_reselect(contract, field):
    c = deepcopy(contract)
    if field == "confirmation": c["common_confirmation"]["maximum_refill_ratio"] = .8
    elif field == "model": c["price_model"]["cost_pct"] = 0
    elif field == "hypothesis": c["hypotheses"][0]["phase"] = "any"
    elif field == "success": c["comparison"]["winner_retention_veto"] = True
    elif field == "clock": c["discovery_dates"] = ["2026-10-06"]
    elif field == "authority": c["allowed_runtime_apply"] = True
    elif field == "kernel": c["kernel_seals"] = {}
    c["content_sha256"] = S.digest({k: v for k, v in c.items() if k != "content_sha256"})
    with pytest.raises(ValueError): forward.validate_contract(c)


@pytest.mark.parametrize("field", ["parent", "bundle"])
def test_self_consistent_rehash_cannot_replace_reviewed_external_anchors(contract, field):
    c = deepcopy(contract)
    if field == "parent":
        c["parent_policy"]["thresholds"]["minimum_micro_net_aggressive_delta_10t"] = 2
        c["parent_policy_sha256"] = S.digest(c["parent_policy"])
        c["common_confirmation"]["minimum_delta"] = 2
    else:
        c["reviewed_bundle_sha256"] = "f" * 64
    c["content_sha256"] = S.digest({k: v for k, v in c.items() if k != "content_sha256"})
    with pytest.raises(ValueError, match="reviewed_parent_or_bundle_changed_replan"):
        forward.validate_contract(c)


def test_no_source_is_waiting_and_presence_is_not_validation(contract, tmp_path):
    day = "2026-10-06"
    inventory = forward.source_inventory(tmp_path, day, contract)
    assert inventory["status"] == "waiting_new_source_date" and len(inventory["missing_source_paths"]) == 4
    for rel in (f"data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json.gz",
                f"data/ai_decision_payloads/ai_decision_payloads_{day}.jsonl",
                f"data/observations/scalp_micro_reversion_forward/trade_date={day}/venue=NXT/session=NXT_PREMARKET/market_stream.manifest.json",
                f"data/observations/scalp_micro_reversion_forward/trade_date={day}/venue=NXT/session=NXT_PREMARKET/market_depth_stream.manifest.json"):
        path = tmp_path / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("{}")
    inventory = forward.source_inventory(tmp_path, day, contract)
    assert inventory["status"] == "source_present_validation_pending"
    assert inventory["source_semantics_verified"] is False and inventory["performance_verified"] is False
    assert len(inventory["available_source_seals"]) == 4
    with pytest.raises(ValueError, match="prefreeze"):
        forward.source_inventory(tmp_path, "2026-10-02", contract)


def test_runtime_policy_validator_generation_change_invalidates_contract(contract, monkeypatch):
    original = forward.file_sha256
    monkeypatch.setattr(forward, "file_sha256", lambda p:
        "f" * 64 if p.name == "mechanistic_entry_runtime_policy.py" else original(p))
    with pytest.raises(ValueError, match="forward_kernel_changed_replan"):
        forward.validate_contract(contract)


def test_inventory_matches_public_loader_with_a_gzip_directory(contract, tmp_path):
    plain = tmp_path / "data/report/machine_observation_projection/machine_observation_projection_2026-10-06_0_1.json"
    plain.parent.mkdir(parents=True)
    plain.write_text('{"generation": "current"}')
    compressed = plain.with_suffix(".json.gz")
    compressed.mkdir()
    result = forward.source_inventory(tmp_path, "2026-10-06", contract)
    assert str(plain) in result["available_source_seals"]
    assert str(compressed) not in result["available_source_seals"]


def test_inventory_matches_public_loader_gzip_precedence(contract, tmp_path):
    plain = tmp_path / "data/report/machine_observation_projection/machine_observation_projection_2026-10-06_0_1.json"
    plain.parent.mkdir(parents=True)
    plain.write_text('{"generation": "legacy_plain"}')
    compressed = plain.with_suffix(".json.gz")
    compressed.write_text('{"generation": "gzip_current"}')
    result = forward.source_inventory(tmp_path, "2026-10-06", contract)
    assert str(compressed) in result["available_source_seals"]
    assert str(plain) not in result["available_source_seals"]
