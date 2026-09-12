from datetime import datetime
import hashlib
import json
import pytest

from src.engine.scalping import entry_setup_scalping_rollout as rollout
from src.engine.scalping import entry_setup_live_policy as policy
from src.tests.test_entry_setup_live_policy import _enable_probe_contract

NOW = datetime.fromisoformat("2026-09-11T12:00:00+09:00")


def pin(monkeypatch, tmp_path):
    payload = {
        **rollout.CONTRACT,
        "effective_from": "2026-09-11T11:59:00+09:00",
        "operator_authority": "all_scalping_v2_14_2026_09_11",
        "reviewed_commit": "a" * 40,
    }
    path = tmp_path / "rollout.json"
    path.write_text(json.dumps(payload))
    monkeypatch.setenv(rollout.PATH_ENV, str(path))
    monkeypatch.setenv(rollout.SHA_ENV, hashlib.sha256(path.read_bytes()).hexdigest())
    _enable_probe_contract(monkeypatch)
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-09-11")
    for key in ("MAX_DAILY_RECHECK", "MAX_DAILY_BUY_RECOVERY"):
        monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_" + key, "100")
    return path


def pin_auto_promotion(monkeypatch, tmp_path):
    payload = {
        **rollout.AUTO_PROMOTION_CONTRACT,
        "effective_from": "2026-09-11T11:59:00+09:00",
        "operator_authority": "all_sessions_v2_15_plus_auto_promotion_2026_09_14",
        "reviewed_commit": "b" * 40,
    }
    path = tmp_path / "auto-promotion.json"
    path.write_text(json.dumps(payload))
    monkeypatch.setenv(rollout.AUTO_PROMOTION_PATH_ENV, str(path))
    monkeypatch.setenv(
        rollout.AUTO_PROMOTION_SHA_ENV, hashlib.sha256(path.read_bytes()).hexdigest()
    )
    _enable_probe_contract(monkeypatch)
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-09-11")
    for key in ("MAX_DAILY_RECHECK", "MAX_DAILY_BUY_RECOVERY"):
        monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_" + key, "100")
    return path


def test_auto_promotion_pin_covers_all_sessions_and_falls_back_to_v2_14(
    monkeypatch, tmp_path
):
    pin_auto_promotion(monkeypatch, tmp_path)
    monkeypatch.setattr(policy, "ACTIVATION_DIR", tmp_path / "activations")
    loaded = rollout.load_auto_promotion(now=NOW)
    assert loaded and loaded["valid"] is True
    assert set(rollout.AUTO_PROMOTION_SCOPES) == set(rollout.SCOPES) | set(
        rollout.OBSERVE_ONLY_SCOPES
    )

    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=policy.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        strategy="SCALPING",
        now=NOW,
    )
    assert resolved["enabled"] is True
    assert resolved["selected_prompt_version"] == (
        policy.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )
    assert resolved["scope_authority"] == "operator_all_session_auto_promotion"


def test_auto_promotion_cli_writes_one_immutable_contract(tmp_path):
    output = tmp_path / "auto-promotion.json"
    assert rollout.main(
        [
            "--auto-promotion",
            "--effective-from",
            "2026-09-14T07:35:00+09:00",
            "--reviewed-commit",
            "c" * 40,
            "--output",
            str(output),
            "--confirm",
            "APPLY_ALL_SESSIONS_V2_15_PLUS_AUTO_PROMOTION",
        ]
    ) == 0
    payload = json.loads(output.read_text())
    assert payload["schema"] == rollout.AUTO_PROMOTION_SCHEMA
    assert payload["operator_authority"] == (
        "all_sessions_v2_15_plus_auto_promotion_2026_09_14"
    )
    with pytest.raises(SystemExit):
        rollout.main(
            [
                "--auto-promotion",
                "--effective-from",
                "2026-09-14T07:35:00+09:00",
                "--reviewed-commit",
                "c" * 40,
                "--output",
                str(output),
                "--confirm",
                "APPLY_ALL_SESSIONS_V2_15_PLUS_AUTO_PROMOTION",
            ]
        )


def test_auto_promotion_authorizes_exact_scope_only(monkeypatch, tmp_path):
    path = pin_auto_promotion(monkeypatch, tmp_path)
    decision = {
        "entry_setup_live_policy_scope_authority": "operator_all_session_auto_promotion",
        "entry_setup_live_policy_runtime_effect": True,
        "entry_setup_live_policy_target_date": "2026-09-11",
        "entry_setup_live_policy_activation_sha256": hashlib.sha256(
            path.read_bytes()
        ).hexdigest(),
        "entry_setup_live_policy_effective_venue": "KRX_NXT_INTEGRATED",
        "entry_setup_live_policy_session_bucket": "KRX_NXT_AFTERMARKET",
    }
    assert rollout.decision_authorized("SCALPING", decision, now=NOW)
    decision["entry_setup_live_policy_activation_sha256"] = "0" * 64
    assert not rollout.decision_authorized("SCALPING", decision, now=NOW)


@pytest.mark.parametrize("scope", rollout.SCOPES)
@pytest.mark.parametrize("tag", ["SCANNER", "SCALP_BASE", "MIDDLE", None])
def test_all_scalping_entry_scopes_keep_same_guarded_global_cap(
    monkeypatch, tmp_path, scope, tag
):
    pin(monkeypatch, tmp_path)
    # Runtime wall clock is independently used by handoff config.
    monkeypatch.setattr(
        rollout,
        "datetime",
        type(
            "Clock",
            (),
            {
                "now": staticmethod(lambda *a: NOW),
                "fromisoformat": datetime.fromisoformat,
            },
        ),
    )
    venue, session = scope.split("|")
    actual = policy.resolve_live_prompt_policy(
        configured_prompt_version=policy.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue=venue,
        session_bucket=session,
        position_tag=tag,
        strategy="SCALPING",
        now=NOW,
    )
    assert actual["enabled"] is True, actual
    assert (
        actual["selected_prompt_version"]
        == policy.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )
    assert actual["maximum_daily_exploration_probes"] == 100
    assert actual["canary_mode"] == policy.EXPLORATION_CANARY_MODE


@pytest.mark.parametrize(
    "change", ["hash", "future", "cap", "guard", "strategy", "unknown_scope"]
)
def test_rollout_never_uses_invalid_pin_or_bypasses_guard(
    monkeypatch, tmp_path, change
):
    path = pin(monkeypatch, tmp_path)
    if change in {"future", "cap"}:
        p = json.loads(path.read_text())
        p[
            (
                "effective_from"
                if change == "future"
                else "maximum_daily_exploration_probes"
            )
        ] = ("2026-09-12T00:00:00+09:00" if change == "future" else 101)
        path.write_text(json.dumps(p))
        monkeypatch.setenv(
            rollout.SHA_ENV, hashlib.sha256(path.read_bytes()).hexdigest()
        )
    if change == "hash":
        path.write_text("{}")
    if change == "guard":
        monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "2")
    result = policy.resolve_live_prompt_policy(
        configured_prompt_version=policy.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue="UNKNOWN" if change == "unknown_scope" else "KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCALP_BASE",
        strategy="KOSPI_ML" if change == "strategy" else "SCALPING",
        now=NOW,
    )
    assert result["enabled"] is False


@pytest.mark.parametrize("scope", rollout.SCOPES)
def test_rollout_reaches_existing_recheck_with_safety_guards(
    monkeypatch, tmp_path, scope
):
    from src.tests.test_entry_opportunity_recheck import _decision, _enabled_config
    from src.engine.scalping.entry_recheck_policy import runtime_scope

    path = pin(monkeypatch, tmp_path)
    monkeypatch.setattr(
        rollout,
        "datetime",
        type(
            "Clock",
            (),
            {
                "now": staticmethod(lambda *a: NOW),
                "fromisoformat": datetime.fromisoformat,
            },
        ),
    )
    venue, session = scope.split("|")
    config = _enabled_config(
        allowed_scopes=frozenset({runtime_scope(venue, session)}),
        probe_first_active_date="DAILY",
        max_daily_recheck=100,
        max_daily_buy_recovery=100,
    )
    args = dict(
        config=config,
        position_tag="SCALP_BASE",
        effective_venue=venue,
        market_session_bucket=session,
        today="2026-09-11",
        entry_setup_policy_decision={
            "entry_setup_live_policy_scope_authority": "operator_all_scalping_rollout",
            "entry_setup_live_policy_runtime_effect": True,
            "entry_setup_live_policy_target_date": "2026-09-11",
            "entry_setup_live_policy_activation_sha256": hashlib.sha256(
                path.read_bytes()
            ).hexdigest(),
            "entry_setup_live_policy_effective_venue": venue,
            "entry_setup_live_policy_session_bucket": session,
        },
    )
    assert _decision(**args).allowed
    assert not _decision(**args, latency_state="DANGER").allowed
    assert not _decision(**args, ws_age_ms=1501).allowed
    assert not _decision(**args, source_reason="broker_guard_blocked").allowed

    stale = dict(
        args["entry_setup_policy_decision"],
        entry_setup_live_policy_activation_sha256="0" * 64,
    )
    assert not _decision(**{**args, "entry_setup_policy_decision": stale}).allowed
    assert not _decision(**{**args, "entry_setup_policy_decision": None}).allowed


def test_scope_change_never_resets_existing_accepted_order_ledger(
    monkeypatch, tmp_path
):
    pin(monkeypatch, tmp_path)
    monkeypatch.setattr(policy, "ACTIVATION_DIR", tmp_path / "activation")
    assert (
        policy.record_exploration_probe_submission(
            trade_date="2026-09-11", stock_code="005930", broker_order_no="existing-1"
        )
        == 1
    )
    before = policy.read_exploration_probe_submit_count("2026-09-11")
    for scope in rollout.SCOPES:
        assert rollout.scope_authorized("SCALPING", *scope.split("|"), now=NOW)
    assert policy.read_exploration_probe_submit_count("2026-09-11") == before


def test_publisher_preserves_existing_approval_bytes(tmp_path):
    path = tmp_path / "approval.json"
    args = [
        "--effective-from",
        "2026-09-11T12:00:00+09:00",
        "--reviewed-commit",
        "a" * 40,
        "--output",
        str(path),
        "--confirm",
        "APPLY_ALL_SCALPING_V2_14",
    ]
    assert rollout.main(args) == 0
    first = path.read_bytes()
    with pytest.raises(SystemExit):
        rollout.main(args)
    assert path.read_bytes() == first
    assert (
        rollout.load_rollout(
            now=NOW,
            env={
                rollout.PATH_ENV: str(path),
                rollout.SHA_ENV: hashlib.sha256(first).hexdigest(),
            },
        )["valid"]
        is True
    )
