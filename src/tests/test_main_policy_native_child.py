"""Run genuine policy producers and native Main loading in a kernel-isolated child.

The source copy is byte-identical application code with a disposable data mount.
No fake policy loader, production data, provider or operational PID is involved.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import pytest

from src.engine.automation import main_startup_validation as parent
from src.engine.infrastructure.main_policy_loading import CONSUMER_IDS
from src.engine.scalping import entry_setup_scalping_rollout as authority
from src.engine.scalping import holding_prompt_live_policy as holding
from src.engine.scalping import mechanistic_entry_runtime_policy as machine
from src.engine.scalping import trailing_mechanical_policy as trailing
from src.engine.scalping import trailing_situation_policy as situation
from src.tests.test_mechanistic_entry_runtime_policy import source

ROOT = Path(__file__).resolve().parents[2]
TARGET = "2026-10-19"
OBSERVED = "2026-10-18T12:00:00+09:00"


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_copy(code):
    # Copy actual modules, preserving every byte. Exclude tests/caches and
    # non-code model/data files which the policy readers do not consume.
    for path in (ROOT / "src").rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or path.suffix not in {".py", ".json"}:
            continue
        if any(part in relative.parts for part in ("tests", "__pycache__", "model", "data", "logs")):
            continue
        destination = code / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        assert destination.read_bytes() == path.read_bytes()


def _policies(data, monkeypatch):
    from src.engine.ai_prompt_contracts import DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
    from zoneinfo import ZoneInfo

    bundle = machine.publish(source(data, "2026-10-16"), data_root=data, bootstrap=True,
        adopt_all_continuous=True, now=datetime(2026, 10, 16, 22, tzinfo=ZoneInfo("Asia/Seoul")))
    assert bundle["target_date"] == TARGET
    pin = {**authority.AUTO_PROMOTION_CONTRACT,
        "effective_from": "2026-10-16T07:35:00+09:00",
        "operator_authority": "all_sessions_v2_15_plus_auto_promotion_2026_09_14",
        "reviewed_commit": "a" * 40}
    pin_path = data / "promotion.json"
    pin_path.write_text(json.dumps(pin))
    monkeypatch.setattr(holding, "CANDIDATE_DIR", data / "threshold_cycle/holding_prompt_candidates")
    monkeypatch.setattr(holding, "_cumulative_economics", lambda *_: dict(
        clean_baseline_date="2026-06-05", as_of_date="2026-10-16", row_count=10,
        unique_symbol_count=3, candidate_cost_adjusted_ev_pct=.12,
        control_cost_adjusted_ev_pct=.10, candidate_cost_adjusted_ev_delta_pct=.02,
        candidate_positive_outcome_frequency=.6, candidate_severe_tail_count=0,
        control_severe_tail_count=0, source_reports=[]))
    for cohort in holding.SUPPORTED_COHORTS:
        candidate = holding.build_candidate("2026-10-16", cohort)
        assert candidate["effective_date"] == TARGET
        holding._write_json(holding.candidate_path("2026-10-16", cohort), candidate)
    values = {market: dict(trailing.DEFAULTS) for market in trailing.START_MARKETS}
    vector = trailing.market_values_hash(values)
    typed = situation.initial_bundle(values, parent_sha256=vector,
        source_date="2026-10-16", target_date=TARGET)
    env = {
        authority.AUTO_PROMOTION_PATH_ENV: str(pin_path), authority.AUTO_PROMOTION_SHA_ENV: _hash(pin_path),
        "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION": DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED": "true",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE": "DAILY",
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED": "true",
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE": TARGET,
        "KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE": TARGET,
        situation.ENV_KEY: json.dumps(typed), trailing.VECTOR_SHA_ENV_KEY: vector,
    }
    return env, bundle


@pytest.fixture
def native_child(tmp_path, monkeypatch):
    code, data = tmp_path / "code", tmp_path / "fixture-data"
    data.mkdir()
    _source_copy(code)
    (code / "data").symlink_to(data, target_is_directory=True)
    policy_env, bundle = _policies(data, monkeypatch)
    run_id = uuid.uuid4().hex
    run = tmp_path / run_id
    run.mkdir(mode=0o700)
    child_env = {"PATH": os.defpath, "PYTHONPATH": str(code), "PYTHONDONTWRITEBYTECODE": "1",
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1", "PYTHONNOUSERSITE": "1", **policy_env}
    source_hashes = {str(path): _hash(path) for base in (code / "src", data)
        for path in base.rglob("*") if path.is_file()}
    request = dict(schema=parent.SCHEMA, run_id=run_id, target_date=TARGET,
        observed_at_kst=OBSERVED, execution_release_root=str(code), execution_release_commit="a" * 40,
        data_root=str(data), expected_env_sha256=parent._digest(policy_env), source_hashes=source_hashes,
        manifest={"target_date": TARGET}, consumer_ids=sorted(CONSUMER_IDS),
        expected_policy_hashes={"main_machine": bundle["bundle_sha256"]})
    request["request_sha256"] = parent._digest(request)
    (run / "request.json").write_text(json.dumps(request))
    return dict(code=code, data=data, run=run, request=request, env=child_env,
        sources=source_hashes, bundle=bundle)


def _run(fixture):
    result = subprocess.run([sys.executable, "-I", "-B", str(fixture["code"] / "src/bot_main.py"),
        "--validate-startup", str(fixture["run"] / "request.json")],
        cwd=fixture["code"] / "src", env=fixture["env"], capture_output=True,
        text=True, timeout=90, start_new_session=True, close_fds=True)
    (fixture["run"] / "child-output.log").write_text(result.stdout + result.stderr)
    child_path = fixture["run"] / "child.json"
    child = json.loads(child_path.read_text()) if child_path.exists() else None
    return result, child


def test_real_main_child_loads_nonempty_native_policy_then_exits(native_child):
    result, child = _run(native_child)
    assert result.returncode == 0, (result.stdout, result.stderr, child)
    assert child["status"] == "passed", child
    assert set(child["consumer_results"]) == CONSUMER_IDS
    assert all(row["status"] in {"loaded", "disabled", "parent_only"}
        for row in child["consumer_results"].values())
    for consumer in ("main_machine", "typed_trading_rules", "entry_prompt", "holding_prompt",
                     "trailing_mechanical", "trailing_situation"):
        assert child["consumer_results"][consumer]["status"] == "loaded"
    assert child["consumer_results"]["main_machine"]["policy_sha256"] == native_child["bundle"]["bundle_sha256"]
    assert len(child["consumer_results"]["entry_prompt"]["scope_results"]) == 9
    assert len(child["consumer_results"]["holding_prompt"]["scope_results"]) == 9
    assert len(child["consumer_results"]["trailing_situation"]["scope_keys"]) == 12
    assert child["forbidden_attempt_count"] == 0
    assert (native_child["run"] / "isolation.jsonl").read_bytes() == b""
    assert child["isolation"]["network_access"] is False
    assert child["isolation"]["process_creation"] is False
    assert child["actual_pid_consumed"] is child["runtime_effect"] is child["allowed_runtime_apply"] is False
    assert not Path(f'/proc/{child["validation_pid"]}').exists()
    assert all(_hash(path) == digest for path, digest in native_child["sources"].items())
    assert not (native_child["code"] / "logs").exists()
    assert not list(native_child["data"].rglob("consumed"))
    assert not list(native_child["data"].rglob("pid_*.json"))


def test_real_native_source_corruption_is_failed_under_same_isolation(native_child):
    source_path = machine.preparation_path(native_child["data"], TARGET)
    source_path.write_text("{}")
    # Request binding still describes the original producer generation.
    result, child = _run(native_child)
    assert result.returncode != 0
    assert child is not None and child["status"] == "failed"
    assert any("source_changed" in item for item in child["findings"]), child
    assert child["runtime_effect"] is child["actual_pid_consumed"] is False
    assert not list(native_child["data"].rglob("consumed"))
