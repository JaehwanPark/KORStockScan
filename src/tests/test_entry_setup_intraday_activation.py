"""Exact scheduling exceptions preserve the original source and existing owner."""

from datetime import datetime, timedelta

import pytest

from src.engine.scalping import entry_setup_intraday_activation as intraday
from src.engine.scalping import entry_setup_live_policy as policy
from src.tests.test_entry_setup_live_policy import (
    SOURCE_DATE,
    TARGET_DATE,
    _configure_paths,
    _enable_probe_contract,
    _valid_batch_report,
    _valid_detailed_report,
)

NOW = datetime(2026, 8, 7, 11, 0, tzinfo=policy.KST)
END = NOW.replace(hour=15, minute=30)


@pytest.fixture
def ready(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _enable_probe_contract(monkeypatch)
    monkeypatch.delenv(intraday.PATH_ENV, raising=False)
    monkeypatch.delenv(intraday.SHA_ENV, raising=False)
    detailed = _valid_detailed_report()
    detailed["promotion_quality_gate_pass"] = False
    cumulative = detailed["cumulative_learning"]
    cumulative["promotion_quality_gate_pass"] = False
    cumulative["promotion_quality_checks"] = {
        key: False for key in policy.CUMULATIVE_PROMOTION_CHECK_KEYS
    }
    cumulative["promotion_evidence_floor"] = {"pass": False}
    cumulative["candidate_exposure_decision_count"] = 0
    cumulative["candidate_exposure_unique_symbol_count"] = 0
    cumulative["candidate_probe_risk_budget"] = {"pass": False}
    policy._atomic_write_json(policy.detailed_report_path(SOURCE_DATE), detailed)
    batch = _valid_batch_report()
    batch["cohorts"][0]["promotion_quality_gate_pass"] = False
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)
    policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=NOW - timedelta(minutes=1),
    )
    path = policy.live_candidate_path(SOURCE_DATE)
    assert policy._read_json(path)["canary_mode"] == policy.EXPLORATION_CANARY_MODE
    return path


def _approve(path, **overrides):
    args = dict(
        candidate_path=path,
        expected_candidate_sha256=policy._file_sha256(path),
        operator_instruction_ref="test-only operator approval",
        expires_at=END,
        now=NOW,
    )
    args.update(overrides)
    return intraday.build_approval(**args)


def _pin(monkeypatch, tmp_path, approval):
    path = tmp_path / "approval.json"
    policy._atomic_write_json(path, approval)
    monkeypatch.setenv(intraday.PATH_ENV, str(path))
    monkeypatch.setenv(intraday.SHA_ENV, approval["artifact_sha256"])
    return path


def _resolve(**overrides):
    args = dict(
        configured_prompt_version=policy.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=NOW,
    )
    args.update(overrides)
    return policy.resolve_live_prompt_policy(**args)


def test_original_next_day_candidate_activates_today_only_with_exact_pin(
    ready, monkeypatch, tmp_path
):
    before = ready.read_bytes()
    assert policy._read_json(ready)["effective_date"] == "2026-08-10"
    assert not _resolve()["enabled"]
    assert not policy.build_preopen_activation(target_date=TARGET_DATE)[
        "allowed_runtime_apply"
    ]
    approval = _approve(ready)
    _pin(monkeypatch, tmp_path, approval)
    resolved = _resolve()
    assert resolved["enabled"] and resolved["status"] == "active_bounded_krx_canary"
    assert (
        resolved["selected_prompt_version"]
        == policy.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )
    assert resolved["maximum_daily_exploration_probes"] == 3
    assert resolved["canary_mode"] == "one_share_exploration"
    assert ready.read_bytes() == before
    assert not policy.activation_path(TARGET_DATE).exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"effective_venue": "NXT", "session_bucket": "NXT_AFTERMARKET"},
        {"session_bucket": "PREMARKET_KRX_LIKE"},
        {"position_tag": "MANUAL"},
        {"now": NOW - timedelta(seconds=1)},
        {"now": END},
        {"now": NOW + timedelta(days=1)},
        {"configured_prompt_version": "another_stage_owner"},
    ],
)
def test_scope_time_and_owner_are_not_expanded(ready, monkeypatch, tmp_path, overrides):
    _pin(monkeypatch, tmp_path, _approve(ready))
    assert not _resolve(**overrides)["enabled"]


@pytest.mark.parametrize(
    "key,value",
    [
        (policy.CANARY_ENV_KEY, "false"),
        ("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES", ""),
        ("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "2"),
        (
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
            "false",
        ),
        ("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-08-06"),
    ],
)
def test_current_vetoes_precede_intraday_approval(
    ready, monkeypatch, tmp_path, key, value
):
    _pin(monkeypatch, tmp_path, _approve(ready))
    monkeypatch.setenv(key, value)
    assert not _resolve()["enabled"]


@pytest.mark.parametrize(
    "part", ["approval", "candidate", "batch", "detailed", "code", "missing_pin"]
)
def test_pinned_generation_changes_fail_closed(ready, monkeypatch, tmp_path, part):
    approval = _approve(ready)
    path = _pin(monkeypatch, tmp_path, approval)
    assert _resolve()["enabled"]
    if part == "missing_pin":
        monkeypatch.delenv(intraday.SHA_ENV)
    elif part == "code":
        monkeypatch.setattr(intraday, "PROJECT_ROOT", tmp_path / "different-code")
    else:
        source = {
            "approval": path,
            "candidate": ready,
            "batch": policy.batch_report_path(SOURCE_DATE),
            "detailed": policy.detailed_report_path(SOURCE_DATE),
        }[part]
        source.write_bytes(source.read_bytes() + b" ")
        # Approval hash is canonical; change its content, not just whitespace.
        if part == "approval":
            changed = policy._read_json(source)
            changed["expires_at"] = END.replace(hour=16).isoformat()
            policy._atomic_write_json(source, changed)
    result = _resolve()
    assert result["enabled"] is False
    assert result["runtime_effect"] is False


def test_schema_failure_in_other_cohort_does_not_veto_valid_krx(ready):
    batch_path = policy.batch_report_path(SOURCE_DATE)
    batch = policy._read_json(batch_path)
    batch["cohorts"][1]["status"] = "blocked"
    batch["status"] = "completed_offline_only_with_cohort_failures"
    policy._atomic_write_json(batch_path, batch)
    candidate = policy._read_json(ready)
    detailed = policy._read_json(policy.detailed_report_path(SOURCE_DATE))
    candidate = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        detailed_report=detailed,
        detailed_path=policy.detailed_report_path(SOURCE_DATE),
        generated_at=NOW - timedelta(minutes=1),
    )
    policy._atomic_write_json(ready, candidate)
    assert _approve(ready)["canary_mode"] == policy.EXPLORATION_CANARY_MODE


def test_bad_krx_source_is_not_a_scheduling_exception(ready):
    detailed_path = policy.detailed_report_path(SOURCE_DATE)
    detailed = policy._read_json(detailed_path)
    detailed["promotion_report_integrity_pass"] = False
    policy._atomic_write_json(detailed_path, detailed)
    with pytest.raises(ValueError):
        _approve(ready)


def test_approval_cannot_reset_existing_daily_cap(ready, monkeypatch, tmp_path):
    policy.record_exploration_probe_submission(
        trade_date=TARGET_DATE, broker_order_no="original-order", stock_code="005930"
    )
    before = policy.exploration_probe_cap_path(TARGET_DATE).read_bytes()
    _pin(monkeypatch, tmp_path, _approve(ready))
    assert _resolve()["enabled"]
    assert policy.read_exploration_probe_submit_count(TARGET_DATE) == 1
    assert policy.exploration_probe_cap_path(TARGET_DATE).read_bytes() == before


def test_approval_publication_never_overwrites_an_existing_receipt(tmp_path):
    path = tmp_path / "approval.json"
    intraday.write_new_approval(path, {"original": True})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        intraday.write_new_approval(path, {"replacement": True})
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "kwargs",
    [
        {"expected_candidate_sha256": "not-the-approved-candidate"},
        {"operator_instruction_ref": ""},
        {"expires_at": END + timedelta(seconds=1)},
        {"expires_at": NOW},
        {"now": NOW.replace(tzinfo=None)},
    ],
)
def test_invalid_operator_contract_is_rejected(ready, kwargs):
    with pytest.raises(ValueError):
        _approve(ready, **kwargs)
