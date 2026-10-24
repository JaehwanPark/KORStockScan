from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.infrastructure import main_prompt_policy_loading as adapter
from src.engine.scalping import entry_setup_live_policy as entry
from src.engine.scalping import entry_setup_scalping_rollout as authority
from src.engine.scalping import holding_prompt_live_policy as holding
from src.engine.scalping import mechanistic_entry_runtime_policy as machine
from src.tests.test_mechanistic_entry_runtime_policy import source

KST = ZoneInfo("Asia/Seoul")
TARGET = "2026-09-14"
OBSERVED = datetime(2026, 9, 13, 12, tzinfo=KST)


def _prepare(monkeypatch, tmp_path):
    for key in list(os.environ):
        if key.startswith("KORSTOCKSCAN_"):
            monkeypatch.delenv(key)
    monkeypatch.setattr(entry, "DATA_DIR", tmp_path)
    pin = {**authority.AUTO_PROMOTION_CONTRACT,
        "effective_from": "2026-09-11T07:35:00+09:00",
        "operator_authority": "all_sessions_v2_15_plus_auto_promotion_2026_09_14",
        "reviewed_commit": "a" * 40}
    pin_path = tmp_path / "promotion.json"
    pin_path.write_text(json.dumps(pin))
    env = {
        authority.AUTO_PROMOTION_PATH_ENV: str(pin_path),
        authority.AUTO_PROMOTION_SHA_ENV: hashlib.sha256(pin_path.read_bytes()).hexdigest(),
        "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION": entry.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED": "true",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE": "DAILY",
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED": "true",
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE": TARGET,
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    bundle = machine.publish(source(tmp_path), data_root=tmp_path, bootstrap=True,
        adopt_all_continuous=True, now=datetime(2026, 9, 11, 22, tzinfo=KST))
    return env, bundle, pin_path


def _holding_candidates(monkeypatch, data):
    monkeypatch.setattr(holding, "CANDIDATE_DIR", data / "threshold_cycle/holding_prompt_candidates")
    monkeypatch.setattr(holding, "_cumulative_economics", lambda *_: dict(
        clean_baseline_date="2026-06-05", as_of_date="2026-09-11", row_count=10,
        unique_symbol_count=3, candidate_cost_adjusted_ev_pct=.12,
        control_cost_adjusted_ev_pct=.10, candidate_cost_adjusted_ev_delta_pct=.02,
        candidate_positive_outcome_frequency=.6, candidate_severe_tail_count=0,
        control_severe_tail_count=0, source_reports=[]))
    for cohort in holding.SUPPORTED_COHORTS:
        candidate = holding.build_candidate("2026-09-11", cohort)
        assert candidate["status"] == "preopen_apply_ready"
        holding._write_json(holding.candidate_path("2026-09-11", cohort), candidate)


def test_future_native_prompt_scopes_load_without_activation_or_clock_change(monkeypatch, tmp_path):
    env, bundle, _ = _prepare(monkeypatch, tmp_path)
    _holding_candidates(monkeypatch, tmp_path)
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    assert {name: row["status"] for name, row in result.items()} == {
        "entry_prompt": "loaded", "holding_prompt": "loaded"}
    assert len(result["entry_prompt"]["scope_results"]) == len(entry.SUPPORTED_LIVE_COHORTS)
    assert len(result["holding_prompt"]["scope_results"]) == len(holding.SUPPORTED_COHORTS)
    assert {row["policy_sha256"] for row in result["entry_prompt"]["scope_results"]} == {bundle["bundle_sha256"]}
    assert not (tmp_path / "runtime/holding_prompt_live_policy").exists()
    assert not (machine.root(tmp_path) / "current.json").exists()
    assert not list(tmp_path.rglob("consumed"))


def test_native_current_and_prepared_holding_same_payload_have_same_digest(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    _holding_candidates(monkeypatch, tmp_path)
    prepared = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    for cohort in holding.SUPPORTED_COHORTS:
        activation = holding.build_activation(TARGET, cohort, data_root=tmp_path)
        holding._write_json(holding.activation_path(TARGET, cohort, data_root=tmp_path), activation)
    current = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=datetime(2026, 9, 14, 12, tzinfo=KST), env=env, data_root=tmp_path)
    assert current["holding_prompt"]["loaded_object_sha256"] == prepared["holding_prompt"]["loaded_object_sha256"]


def test_absent_holding_candidate_is_explicit_native_parent_only(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    assert result["holding_prompt"]["status"] == "parent_only"
    assert all(row["reason"] for row in result["holding_prompt"]["scope_results"])


def test_tampered_holding_candidate_never_becomes_approved_absence(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    _holding_candidates(monkeypatch, tmp_path)
    path = holding.candidate_path("2026-09-11", holding.SUPPORTED_COHORTS[0])
    payload = json.loads(path.read_text())
    payload["selected_prompt_sha256"] = "0" * 64
    path.write_text(json.dumps(payload))
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    assert result["holding_prompt"]["status"] == "failed"
    assert "holding_prompt_candidate_hash_invalid" in result["holding_prompt"]["reason"]


def test_future_missing_machine_does_not_load_old_current(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(machine, "load_effective", lambda **_: pytest.fail("current loader reached"))
    machine.preparation_path(tmp_path, TARGET).unlink()
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    assert result["entry_prompt"]["status"] == "failed"


def test_runtime_does_not_accept_future_date_override(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="requires_preparation"):
        entry.resolve_live_prompt_policy(configured_prompt_version="any", effective_venue="KRX",
            session_bucket="KRX_REGULAR", now=OBSERVED, policy_target_date=TARGET)
    with pytest.raises(ValueError, match="requires_preparation"):
        holding.resolve_holding_prompt_policy(effective_venue="KRX", session_bucket="KRX_REGULAR",
            now=OBSERVED, policy_target_date=TARGET)


def test_same_day_preparation_does_not_load_runtime_current(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    _holding_candidates(monkeypatch, tmp_path)
    monkeypatch.setattr(machine, "load_effective", lambda **_: pytest.fail("current loader reached"))
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=datetime(2026, 9, 14, 12, tzinfo=KST), env=env, data_root=tmp_path,
        preparation=True)
    assert {row["status"] for row in result.values()} == {"loaded"}


def test_future_operator_pin_content_loads_without_current_execution_authority(monkeypatch, tmp_path):
    env, _, pin = _prepare(monkeypatch, tmp_path)
    payload = json.loads(pin.read_text())
    payload["effective_from"] = "2026-09-14T07:35:00+09:00"
    pin.write_text(json.dumps(payload))
    env[authority.AUTO_PROMOTION_SHA_ENV] = hashlib.sha256(pin.read_bytes()).hexdigest()
    monkeypatch.setenv(authority.AUTO_PROMOTION_SHA_ENV, env[authority.AUTO_PROMOTION_SHA_ENV])
    result = adapter.load_prompt_policy_consumers(target_date=TARGET,
        observed_at=OBSERVED, env=env, data_root=tmp_path)
    assert result["entry_prompt"]["status"] == "loaded"
    prepared = authority.load_auto_promotion(now=OBSERVED, env=env,
        preparation_target_date=TARGET)
    assert prepared["valid"] is True
    assert prepared["execution_authority"] is False
    assert authority.load_auto_promotion(now=OBSERVED, env=env)["valid"] is False
    # Even a forged present-date decision cannot reuse a content-only load to
    # obtain live authority: the final native boundary reloads the actual clock.
    decision = dict(entry_setup_live_policy_runtime_effect=True,
        entry_setup_live_policy_target_date=OBSERVED.date().isoformat(),
        entry_setup_live_policy_effective_venue="KRX",
        entry_setup_live_policy_session_bucket="KRX_REGULAR",
        entry_setup_live_policy_scope_authority="operator_all_session_auto_promotion",
        entry_setup_live_policy_activation_sha256=env[authority.AUTO_PROMOTION_SHA_ENV])
    assert authority.decision_authorized("SCALPING", decision, now=OBSERVED) is False


@pytest.mark.parametrize("kind", ["rollout", "auto_promotion"])
def test_prepared_pin_still_requires_hash_schema_and_target_lower_bound(monkeypatch, tmp_path, kind):
    env, _, pin_path = _prepare(monkeypatch, tmp_path)
    if kind == "rollout":
        payload = {**authority.CONTRACT, "effective_from": "2026-09-15T07:35:00+09:00",
            "operator_authority": "all_scalping_v2_14_2026_09_11", "reviewed_commit": "a" * 40}
        path_key, sha_key = authority.PATH_ENV, authority.SHA_ENV
        load = authority.load_rollout
    else:
        payload = json.loads(pin_path.read_text())
        payload["effective_from"] = "2026-09-15T07:35:00+09:00"
        path_key, sha_key = authority.AUTO_PROMOTION_PATH_ENV, authority.AUTO_PROMOTION_SHA_ENV
        load = authority.load_auto_promotion
    pin_path.write_text(json.dumps(payload))
    env.update({path_key: str(pin_path), sha_key: hashlib.sha256(pin_path.read_bytes()).hexdigest()})
    assert load(now=OBSERVED, env=env, preparation_target_date=TARGET)["valid"] is False
    payload["effective_from"] = "2026-09-14T07:35:00+09:00"
    pin_path.write_text(json.dumps(payload))
    # A valid date cannot repair the now-stale original byte pin.
    assert load(now=OBSERVED, env=env, preparation_target_date=TARGET)["valid"] is False
    env[sha_key] = hashlib.sha256(pin_path.read_bytes()).hexdigest()
    assert load(now=OBSERVED, env=env, preparation_target_date=TARGET)["valid"] is True
    payload["operator_authority"] = "unauthorized"
    pin_path.write_text(json.dumps(payload))
    env[sha_key] = hashlib.sha256(pin_path.read_bytes()).hexdigest()
    assert load(now=OBSERVED, env=env, preparation_target_date=TARGET)["valid"] is False


def test_supplied_environment_cannot_hide_process_override(monkeypatch, tmp_path):
    env, _, _ = _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "false")
    with pytest.raises(ValueError, match="environment_mismatch"):
        adapter.load_prompt_policy_consumers(target_date=TARGET,
            observed_at=OBSERVED, env=env, data_root=tmp_path)
