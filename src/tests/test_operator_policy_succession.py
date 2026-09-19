"""Contracts still consumed by runtime_policy_bootstrap."""

import json
from pathlib import Path

import pytest

from src.engine.automation import operator_policy_succession as mod


def test_lock_values_normalize_boolean_and_single_key_contracts():
    assert mod.lock_values(
        {
            "env_key": "KORSTOCKSCAN_EXAMPLE_ENABLED",
            "env_value": True,
            "env_overrides": {"KORSTOCKSCAN_LIMIT": 3},
        }
    ) == {
        "KORSTOCKSCAN_EXAMPLE_ENABLED": "true",
        "KORSTOCKSCAN_LIMIT": "3",
    }


def test_explicit_off_and_manual_veto_remain_protected():
    assert mod.classify(
        {
            "family": mod.SCORE,
            "env_overrides": {mod.SCORE_PREFIX + "ENABLED": "false"},
        }
    ) == "protected_veto"
    assert mod.classify({"family": mod.SCORE, "manual_veto": True}) == (
        "protected_veto"
    )


def test_operator_env_parser_reads_assignments_without_executing_shell(tmp_path):
    path = tmp_path / "operator.env"
    path.write_text(
        "export KORSTOCKSCAN_EXAMPLE=true UNRELATED=1\n", encoding="utf-8"
    )
    assert mod.read_operator_env(path) == {
        "KORSTOCKSCAN_EXAMPLE": "true",
        "UNRELATED": "1",
    }

    path.write_text(f"unset {mod.SCORE_PREFIX}ENABLED\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expression_not_supported"):
        mod.read_operator_env(path)


def test_exact_key_allowlist_rejects_safety_quantity_and_provider():
    for key in (
        "KORSTOCKSCAN_SCALP_HARD_STOP",
        "KORSTOCKSCAN_ORDER_QTY",
        mod.SCORE_PREFIX + "MAX_QUOTE_STALE_AGE_MS",
    ):
        assert key not in mod.POLICY_KEYS[mod.SCORE]


def test_all_installed_json_locks_have_explicit_classification():
    root = Path(__file__).resolve().parents[2]
    locks = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (
            root / "data" / "threshold_cycle" / "operator_runtime_env_locks"
        ).glob("*.json")
    ]
    report = mod.inventory(locks)
    assert report["lock_count"] == len(locks)
    assert locks
    assert not [
        row
        for row in report["locks"]
        if row["classification"] == "unclassified_protected"
    ]


@pytest.mark.parametrize("family", [mod.PYRAMID, mod.AVG_DOWN])
def test_retired_scale_in_succession_cannot_recompute_policy(family):
    candidate = {
        "family": family,
        "stage": "scale_in",
        "allowed_runtime_apply": True,
    }
    assert mod.succession_reason(
        candidate,
        {},
        {},
        {},
        ordinary_allowed=True,
        target_date="2026-09-19",
    ) == "independent_scale_in_strategy_retired_20260918"
