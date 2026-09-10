from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
import hashlib
import json
import runpy
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from src.engine.automation import main_ai_current_axis as automation
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import main_ai_current_axis as policy
from src.engine.scalping import main_ai_current_axis_runtime as runtime
from src.engine.scalping.main_ai_current_axis_input import prepare_input
from src.engine.scalping.micro_reversion import ai_quality_bridge as bridge
from src.engine.scalping.micro_reversion import ai_quality_cycle as cycle
from src.engine.scalping.micro_reversion.current_axis_source import (
    CurrentAxisSourceBuffer,
)
from src.tests import test_micro_reversion_ai_quality_bridge as source_fixture
from src.tests import test_micro_reversion_ai_quality_cycle as cycle_fixture
from src.utils.jsonl_io import write_json_object_generation_safe as write_json


def test_current_axis_uses_trusted_data_mount_and_rejects_child_symlink(
    monkeypatch, tmp_path
):
    from src.utils import constants

    shared = tmp_path / "workspace_data"
    shared.mkdir()
    release = tmp_path / "release"
    release.mkdir()
    (release / "data").symlink_to(shared, target_is_directory=True)
    monkeypatch.setattr(constants, "DATA_DIR", (release / "data").resolve())
    loaded = runpy.run_path(policy.__file__)
    assert loaded["RUNTIME_ROOT"] == shared / "runtime/main_ai_current_axis"
    monkeypatch.setattr(policy, "RUNTIME_ROOT", loaded["RUNTIME_ROOT"])
    monkeypatch.setattr(policy, "DATA_DIR", loaded["DATA_DIR"])

    def delivery(target_date, *, root, trace_path):
        assert root == loaded["RUNTIME_ROOT"]
        assert (
            trace_path
            == shared / "ai_decision_trace/ai_decision_trace_2026-09-10.jsonl"
        )
        return runtime.attribution([], target_date=target_date, activation=None)

    monkeypatch.setattr(automation, "post_apply", delivery)
    assert (
        automation.main(
            ["--phase", "postclose", "--target-date", "2026-09-10", "--write"]
        )
        == 0
    )
    status = policy.read(loaded["RUNTIME_ROOT"] / "postclose_status_2026-09-10.json")
    assert status["status"] == "registration_missing_disabled"
    assert status["runtime_effect"] is False
    assert status["provider_call_performed"] is False
    outside = tmp_path / "outside"
    outside.mkdir()
    (loaded["RUNTIME_ROOT"] / "untrusted").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        write_json(
            loaded["RUNTIME_ROOT"] / "untrusted/status.json", {"status": "forbidden"}
        )
    assert not (outside / "status.json").exists()


def prompt_contract(prompt, *, role):
    contract = {
        "prompt_version": f"current_axis_test_{role}",
        "system_prompt": prompt,
        "system_prompt_sha256": (
            hashlib.sha256(prompt.encode()).hexdigest()
            if role == "control"
            else quality._sha256(prompt)
        ),
        "provider": "openai",
        "model": "test-model",
        "transport": "responses_http",
        "schema_name": "entry_v1",
        "require_json": True,
        "temperature": 0.0,
        "max_output_tokens": 240,
        "reasoning_effort": "low",
        "response_schema_mode": "json_object",
        "response_schema_application": "provider_json_object_openai",
        "response_schema_registry_used": False,
        "response_schema_sha256": None,
        "semantic_validator_version": "live_entry_v1_semantic_contract_v1",
    }
    contract["contract_sha256"] = quality._candidate_contract_sha256(contract)
    return contract


def dated_catalog(target_date):
    catalog = source_fixture._current_cost_catalog_payload()
    catalog["target_date"] = target_date
    catalog["content_sha256"] = bridge._producer_sha256(
        {key: value for key, value in catalog.items() if key != "content_sha256"}
    )
    return catalog


@pytest.fixture
def artifacts():
    # Aggregate-contract fixture; raw replay/custody materialization is tested
    # in its producer suite. Do not monkeypatch the downstream validators.
    rolling, manifest = cycle_fixture._review_history(24, probe_days=(0,))
    part = next(
        p
        for p in rolling["partitions"]
        if p["economic_population"] == "full_or_zero_exposure"
    )
    days = [
        d.isoformat()
        for d in cycle_fixture._krx_trading_dates(
            date(2026, 8, 25), len(part["source_dates"])
        )
    ]
    mapping = dict(zip(part["source_dates"], days))
    target = days[-1]
    control = prompt_contract("Baseline English prompt.", role="control")
    recommended = prompt_contract("Candidate English prompt.", role="candidate")
    master = source_fixture._canonical_symbol_master_payload()
    catalog = dated_catalog(target)
    reference = {
        "bridge_config": asdict(
            bridge._verified_cost_config_from_payload(
                catalog, target_date=date.fromisoformat(target)
            )
        ),
        "symbol_master": master,
    }
    part.update(
        source_dates=days,
        latest_symbol_master_source_date=target,
        latest_symbol_master_artifact_sha256=bridge._sha256(master),
        control_contract_sha256=control["contract_sha256"],
        candidate_contract_sha256=recommended["contract_sha256"],
        current_prompt_sha256=control["system_prompt_sha256"],
        recommended_prompt_sha256=recommended["system_prompt_sha256"],
    )
    part["selected_cost_profile_id"] = catalog["profiles"][0]["profile_id"]
    part["selected_cost_profile_content_sha256"] = catalog["profiles"][0][
        "content_sha256"
    ]
    for window in part["windows"].values():
        window["selected_dates"] = [mapping[d] for d in window["selected_dates"]]
    part["research_progress"] = cycle._research_progress(part)
    rolling.update(target_date=target, partitions=[part])
    rolling = policy.seal(rolling)
    candidates = cycle.project_r3_candidates_from_validated_r2(rolling)
    research = cycle._research_candidates([part])
    manifest.update(
        target_date=target,
        source_rolling_artifact_sha256=rolling[policy.HASH_FIELD],
        candidates=candidates,
        candidate_count=len(candidates),
        research_candidates=research,
        research_candidate_count=len(research),
    )
    manifest = policy.seal(manifest)
    cycle.validate_r3_source_only_manifest(manifest, source_rolling_artifact=rolling)
    candidate = policy.build_candidate(
        rolling=rolling,
        manifest=manifest,
        candidate_id=candidates[0]["candidate_id"],
        control=control,
        recommended=recommended,
        input_reference=reference,
    )
    preopen = datetime.fromisoformat(candidate["target_date"] + "T07:30:00+09:00")
    authorization = policy.seal(
        {
            "schema": "main_ai_current_axis_operator_authorization_v1",
            "enabled": True,
            "contract_sha256": policy.sha(policy.CONTRACT),
            "operator_instruction_ref": "test://explicit-approval",
            "first_candidate_sha256": candidate[policy.HASH_FIELD],
            "allow_same_contract_renewal": False,
            "reviewed_at_kst": (preopen - timedelta(hours=1)).isoformat(),
            "expires_at_kst": (preopen + timedelta(days=2)).isoformat(),
        }
    )
    return rolling, manifest, candidate, authorization, preopen


def activation_for(artifacts, monkeypatch):
    rolling, manifest, candidate, authorization, preopen = artifacts
    monkeypatch.setenv(policy.ENABLED_ENV, "true")
    return policy.build_activation(
        candidate=candidate,
        rolling=rolling,
        manifest=manifest,
        authorization=authorization,
        now=preopen,
        owner_conflicts=[],
    )


def test_exact_candidate_preopen_and_live_contract(artifacts, monkeypatch):
    activation = activation_for(artifacts, monkeypatch)
    _, _, candidate, authorization, now = artifacts
    assert (
        policy.validate_live_activation(
            activation=activation,
            receipt=policy.apply_receipt(activation),
            authorization=authorization,
            now=now.replace(hour=10),
        )
        == candidate
    )
    assert activation["actual_order_submitted"] is False
    assert candidate["allowed_runtime_apply"] is False


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("no_enable", "explicit_enable"),
        ("wrong_day", "preopen_window"),
        ("after_open", "preopen_window"),
        ("owner_conflict", "owner_conflict"),
        ("wrong_approval", "exact_candidate"),
        ("expired", "time_invalid"),
        ("naive_clock", "aware_clock"),
        ("r3_resealed", "r3_manifest"),
    ],
)
def test_preopen_adversarial_contracts(artifacts, monkeypatch, mutation, reason):
    rolling, manifest, candidate, authorization, now = deepcopy(artifacts)
    monkeypatch.setenv(policy.ENABLED_ENV, "true")
    conflicts = []
    if mutation == "no_enable":
        monkeypatch.delenv(policy.ENABLED_ENV)
    elif mutation == "wrong_day":
        now += timedelta(days=1)
    elif mutation == "after_open":
        now = now.replace(hour=9)
    elif mutation == "owner_conflict":
        conflicts = ["entry_setup_live_policy"]
    elif mutation == "wrong_approval":
        authorization["first_candidate_sha256"] = "0" * 64
        authorization = policy.seal(authorization)
    elif mutation == "expired":
        authorization["expires_at_kst"] = now.isoformat()
        authorization = policy.seal(authorization)
    elif mutation == "naive_clock":
        now = now.replace(tzinfo=None)
    elif mutation == "r3_resealed":
        manifest["candidates"][0]["allowed_runtime_apply"] = True
        manifest = policy.seal(manifest)
    with pytest.raises(ValueError, match=reason):
        policy.build_activation(
            candidate=candidate,
            rolling=rolling,
            manifest=manifest,
            authorization=authorization,
            now=now,
            owner_conflicts=conflicts,
        )


@pytest.mark.parametrize(
    "change", ["revoked", "wrong_receipt", "future", "after_close", "resealed_prompt"]
)
def test_live_rejects_stale_and_forged_authority(artifacts, monkeypatch, change):
    activation = activation_for(artifacts, monkeypatch)
    _, _, _, authorization, now = artifacts
    now = now.replace(hour=10)
    receipt = policy.apply_receipt(activation)
    if change == "wrong_receipt":
        receipt["activation_sha256"] = "0" * 64
        receipt = policy.seal(receipt)
    elif change == "future":
        now -= timedelta(days=1)
    elif change == "after_close":
        now = now.replace(hour=15, minute=30)
    elif change == "resealed_prompt":
        activation["candidate"]["recommended"]["system_prompt"] = "Forged prompt."
        activation["candidate"] = policy.seal(activation["candidate"])
        activation = policy.seal(activation)
    with pytest.raises(ValueError):
        policy.validate_live_activation(
            activation=activation,
            receipt=receipt,
            authorization=authorization,
            now=now,
            revoked=change == "revoked",
        )


def test_postclose_registration_and_preopen_idempotency(
    artifacts, monkeypatch, tmp_path
):
    rolling, manifest, candidate, authorization, now = artifacts
    monkeypatch.setenv(policy.ENABLED_ENV, "true")
    monkeypatch.setattr(
        cycle, "rolling_report_path", lambda _: tmp_path / "rolling.json"
    )
    monkeypatch.setattr(cycle, "r3_manifest_path", lambda _: tmp_path / "manifest.json")
    monkeypatch.setattr(cycle, "cycle_report_path", lambda _: tmp_path / "cycle.json")
    write_json(
        tmp_path / "cycle.json",
        policy.seal(
            {
                "schema": cycle.CYCLE_SCHEMA,
                "target_date": candidate["source_date"],
                "status": "source_only_no_new_sample",
                "blockers": [],
                "r3_runtime_apply_performed": False,
                "rolling_artifact_sha256": rolling[policy.HASH_FIELD],
                "r3_manifest_artifact_sha256": manifest[policy.HASH_FIELD],
            }
        ),
    )
    monkeypatch.setattr(automation, "owner_conflicts", lambda _: [])
    monkeypatch.setattr(
        cycle,
        "_default_paths",
        lambda _: {
            "cost_profile": tmp_path / "cost.json",
            "symbol_master": tmp_path / "master.json",
        },
    )
    write_json(tmp_path / "cost.json", dated_catalog(candidate["source_date"]))
    write_json(tmp_path / "master.json", candidate["input_reference"]["symbol_master"])
    for name, value in (
        ("rolling", rolling),
        ("manifest", manifest),
        ("operator_authorization", authorization),
    ):
        write_json(tmp_path / f"{name}.json", value)
    write_json(
        tmp_path / "registration.json",
        policy.seal(
            {
                "schema": "main_ai_current_axis_registration_v1",
                "contract_sha256": policy.sha(policy.CONTRACT),
                "control": candidate["control"],
                "recommended": candidate["recommended"],
            }
        ),
    )
    result = automation.postclose(candidate["source_date"], root=tmp_path, write=True)
    write_json(
        tmp_path / f"postclose_status_{candidate['source_date']}.json",
        policy.seal(
            {
                **result,
                "schema": "main_ai_current_axis_cycle_v1",
                "phase": "postclose",
                "target_date": candidate["source_date"],
            }
        ),
    )
    assert result["status"] == "candidate_ready_separate_authorization_required"
    writer = automation.write_json_object_generation_safe

    def crash_before_activation(path, value, **kwargs):
        if Path(path).name == f"activation_{candidate['target_date']}.json":
            raise OSError("test interrupted before commit")
        return writer(path, value, **kwargs)

    monkeypatch.setattr(
        automation, "write_json_object_generation_safe", crash_before_activation
    )
    with pytest.raises(OSError, match="before commit"):
        automation.preopen(candidate["target_date"], root=tmp_path, now=now, write=True)
    assert (tmp_path / "enrollment_receipt.json").exists()
    with pytest.raises(FileNotFoundError):
        runtime.load_active(now.replace(hour=10), root=tmp_path)
    monkeypatch.setattr(automation, "write_json_object_generation_safe", writer)
    first = automation.preopen(
        candidate["target_date"], root=tmp_path, now=now, write=True
    )
    again = automation.preopen(
        candidate["target_date"],
        root=tmp_path,
        now=now + timedelta(minutes=1),
        write=True,
    )
    assert first == again
    activation, loaded = runtime.load_active(now.replace(hour=10), root=tmp_path)
    assert loaded == candidate
    terminal = policy.read(tmp_path / "cycle.json")
    broken_terminal = policy.seal(
        {
            **terminal,
            "blockers": ["late_source_failure"],
            "status": "source_only_blocked_or_deferred",
        }
    )
    write_json(tmp_path / "cycle.json", broken_terminal)
    with pytest.raises(ValueError, match="latest_terminal"):
        runtime.load_active(now.replace(hour=10), root=tmp_path)
    write_json(tmp_path / "cycle.json", terminal)
    write_json(tmp_path / "rollback.json", {"reason": "test"})
    with pytest.raises(ValueError, match="rolled_back"):
        runtime.load_active(now.replace(hour=10), root=tmp_path)
    assert (
        automation.preopen(
            candidate["target_date"], root=tmp_path, now=now, write=True
        )["status"]
        == "rolled_back"
    )


def test_buffer_barrier_eviction_and_scope():
    buffer = CurrentAxisSourceBuffer(max_rows=2)
    common = {
        "symbol": "000001",
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 1,
    }
    for kind in ("market", "depth", "references"):
        for sequence in range(1, 4):
            buffer.add(
                kind,
                {
                    **common,
                    "source_sequence": sequence,
                    "local_receive_timestamp": f"2026-09-07T10:00:0{sequence}+09:00",
                },
            )
    scope = ("000001", "KRX", "KRX_REGULAR", 1)
    stamp = int(datetime.fromisoformat("2026-09-07T10:00:03+09:00").timestamp() * 1000)
    with pytest.raises(ValueError, match="pending"):
        buffer.snapshot(
            scope, captured_at_ms=stamp, market_sequence=4, depth_sequence=3
        )
    copy = buffer.snapshot(
        scope, captured_at_ms=stamp, market_sequence=3, depth_sequence=3
    )
    assert len(copy["market"]) == 2
    assert copy["coverage_start_ms"] > stamp - 2000
    copy["market"][0]["source_sequence"] = 999
    assert (
        buffer.snapshot(
            scope, captured_at_ms=stamp, market_sequence=3, depth_sequence=3
        )["market"][0]["source_sequence"]
        == 2
    )
    buffer.invalidate()
    with pytest.raises(ValueError, match="warming"):
        buffer.snapshot(
            scope, captured_at_ms=stamp, market_sequence=3, depth_sequence=3
        )


def test_identifiable_bad_source_is_isolated_and_can_recover():
    buffer = CurrentAxisSourceBuffer()
    stamp = "2026-09-07T10:00:00+09:00"
    captured = int(datetime.fromisoformat(stamp).timestamp() * 1000)
    common = {
        "session_bucket": "KRX_REGULAR",
        "sequence_epoch": 1,
        "local_receive_timestamp": stamp,
        "source_sequence": 1,
    }
    scopes = [
        ("000001", "KRX", "KRX_REGULAR", 1),
        ("000002", "KRX", "KRX_REGULAR", 1),
        ("000001", "NXT", "KRX_REGULAR", 1),
    ]
    for symbol, venue, _, _ in scopes:
        for kind in ("market", "depth", "references"):
            buffer.add(kind, {**common, "symbol": symbol, "venue": venue})
    buffer.invalidate_scope("000002", "KRX")
    buffer.invalidate_scope("000001", "NXT")
    assert buffer.snapshot(
        scopes[0], captured_at_ms=captured, market_sequence=1, depth_sequence=1
    )["market"]
    for scope in scopes[1:]:
        with pytest.raises(ValueError, match="warming"):
            buffer.snapshot(
                scope, captured_at_ms=captured, market_sequence=1, depth_sequence=1
            )
    for kind in ("market", "depth", "references"):
        buffer.add(
            kind, {**common, "symbol": "000002", "venue": "KRX", "source_sequence": 2}
        )
    recovered = buffer.snapshot(
        scopes[1], captured_at_ms=captured, market_sequence=2, depth_sequence=2
    )
    assert recovered["coverage_start_ms"] == captured


def test_postclose_candidate_failure_preserves_delivery_census(monkeypatch, tmp_path):
    monkeypatch.setattr(policy, "RUNTIME_ROOT", tmp_path)
    monkeypatch.setattr(
        automation,
        "postclose",
        lambda *a, **kw: (_ for _ in ()).throw(ValueError("late candidate failure")),
    )
    calls = []

    def delivery(target_date, **kwargs):
        calls.append(target_date)
        return runtime.attribution([], target_date=target_date, activation=None)

    monkeypatch.setattr(automation, "post_apply", delivery)
    assert (
        automation.main(
            ["--phase", "postclose", "--target-date", "2026-09-07", "--write"]
        )
        == 1
    )
    assert calls == ["2026-09-07"]
    result = policy.read(tmp_path / "postclose_status_2026-09-07.json")
    assert result["status"] == "blocked_contract"
    assert result["post_apply_attribution"]["economic_acceptance"] == "not_evaluated"


def test_same_stage_owner_requires_exact_valid_inactive_generation(
    monkeypatch, tmp_path
):
    from src.engine.scalping import entry_setup_live_policy as entry_owner

    path = tmp_path / "entry_owner.json"
    monkeypatch.setattr(entry_owner, "activation_path", lambda _: path)
    assert automation.owner_conflicts("2026-09-08") == [
        "entry_setup_preopen_owner_state_missing"
    ]
    payload = {
        "schema": entry_owner.PREOPEN_ACTIVATION_SCHEMA,
        "target_date": "2026-09-08",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "status": "inactive_fallback_v2_13",
    }
    payload["artifact_sha256"] = entry_owner._canonical_sha256(payload)
    write_json(path, payload)
    assert automation.owner_conflicts("2026-09-08") == []
    payload["target_date"] = "2026-09-09"
    write_json(path, payload)
    assert automation.owner_conflicts("2026-09-08") == [
        "entry_setup_preopen_owner_state_invalid"
    ]


@dataclass
class Request:
    prompt: str = "Baseline English prompt."
    user_input: str = "{}"
    endpoint_name: str = "analyze_target"
    request_id: str = "request-test"
    symbol: str = "000001"
    model_name: str = "test-model"
    metadata: dict = field(default_factory=dict)


def test_disabled_has_no_artifact_or_source_reads(monkeypatch):
    monkeypatch.delenv(policy.ENABLED_ENV, raising=False)
    monkeypatch.setattr(
        runtime, "load_active", lambda *a, **k: pytest.fail("disabled read")
    )
    request = Request()
    assert runtime.select_request(request, execution={}, metadata={}) == (request, {})
    assert runtime.cache_token() == "disabled"


def test_request_integration_only_mutates_prompt_and_input(artifacts, monkeypatch):
    activation = activation_for(artifacts, monkeypatch)
    _, _, candidate, _, now = artifacts
    now = now.replace(hour=10)
    monkeypatch.setattr(runtime, "load_active", lambda *a, **k: (activation, candidate))
    import src.engine.scalping.main_ai_current_axis_input as inputs

    monkeypatch.setattr(
        inputs,
        "prepare_input",
        lambda **kw: (
            '{"enriched":true}',
            {
                "snapshot_captured_at": now.isoformat(),
                "input_sha256": "a" * 64,
            },
        ),
    )
    metadata = {
        "ai_trace_strategy": "SCALPING",
        "ai_trace_prompt_type": "scalping_entry",
        "position_tag": "SCANNER",
        "main_ai_current_axis_baseline_prompt_version": candidate["control"][
            "prompt_version"
        ],
    }
    request = Request()
    selected, receipt = runtime.select_request(
        request, execution=candidate["control"], metadata=metadata, now=now
    )
    assert receipt["runtime_effect"] is True
    assert selected.prompt == candidate["recommended"]["system_prompt"]
    assert selected.model_name == request.model_name
    assert selected.request_id == request.request_id
    assert request.user_input == "{}"
    assert runtime.cache_token() != runtime.cache_token()
    assert runtime.settle_response(receipt, now=now)["decision_usable"] is True
    assert (
        runtime.settle_response(receipt, now=now, provider_transport="responses_ws")[
            "decision_usable"
        ]
        is False
    )
    monkeypatch.setattr(
        runtime,
        "load_active",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("rollback")),
    )
    assert runtime.settle_response(receipt, now=now)["decision_usable"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("position_tag", "WIDGET"),
        ("ai_trace_strategy", "SWING"),
        ("sim_record_id", "sim-1"),
        ("entry_setup_live_policy_activation_sha256", "active"),
    ],
)
def test_non_main_or_competing_owner_never_uses_candidate(monkeypatch, field, value):
    monkeypatch.setenv(policy.ENABLED_ENV, "true")
    metadata = {
        "ai_trace_strategy": "SCALPING",
        "ai_trace_prompt_type": "scalping_entry",
        "position_tag": "SCANNER",
        field: value,
    }
    monkeypatch.setattr(
        runtime, "load_active", lambda *a, **k: pytest.fail("must not read approval")
    )
    request = Request()
    actual, receipt = runtime.select_request(request, execution={}, metadata=metadata)
    assert actual is request
    assert receipt["runtime_effect"] is False


def test_delivery_attribution_is_not_economic_acceptance():
    assert (
        runtime.attribution([], target_date="2026-09-07", activation=None)["status"]
        == "not_active_no_apply_receipt"
    )
    bad = {
        "request_id": "1",
        "main_ai_current_axis_receipt": {
            "request_id": "2",
            "target_date": "2026-09-07",
        },
    }
    report = runtime.attribution([bad], target_date="2026-09-07", activation=None)
    assert report["status"] == "source_quality_blocked"
    assert report["economic_acceptance"] == "not_evaluated"


def test_delivery_census_validates_receipt_status_and_immutable_apply(
    artifacts, monkeypatch, tmp_path
):
    activation = activation_for(artifacts, monkeypatch)
    target = activation["target_date"]
    receipt = {
        "schema": "main_ai_current_axis_request_receipt_v1",
        "request_id": "delivered-1",
        "target_date": target,
        "status": "provider_response_received",
        "runtime_effect": True,
        "provider_delivery_confirmed": True,
        "activation_sha256": activation[policy.HASH_FIELD],
        "prompt_sha256": "a" * 64,
        "input_sha256": "b" * 64,
    }
    row = {
        "request_id": "delivered-1",
        "main_ai_current_axis_receipt": json.dumps(receipt),
        "prompt_sha256": "a" * 64,
        "payload_sha256": "b" * 64,
        "provider_called": True,
        "provider_actual": "openai",
    }
    report = runtime.attribution([row], target_date=target, activation=activation)
    assert report["status_counts"] == {"provider_response_received": 1}
    assert report["economic_acceptance"] == "not_evaluated"
    row["main_ai_current_axis_receipt"] = {
        **receipt,
        "provider_delivery_confirmed": False,
    }
    assert runtime.attribution([row], target_date=target, activation=activation)[
        "source_quality_errors"
    ] == ["request_receipt_delivery_status_inconsistent"]
    write_json(tmp_path / f"activation_{target}.json", activation)
    write_json(tmp_path / f"apply_receipt_{target}.json", {"status": "broken"})
    with pytest.raises(ValueError, match="post_apply_activation_commit"):
        automation.post_apply(
            target, root=tmp_path, trace_path=tmp_path / "absent.jsonl"
        )


def live_input_fixture():
    evidence, _, _ = source_fixture._complete_ask_depletion_feature_fixture()
    market, depth = source_fixture._complete_ask_depletion_paths()
    # Use the same as-of BBO alignment as the canonical five-horizon fixture.
    for row, bid, ask in ((depth[-2], 9960.0, 9970.0), (depth[-1], 9970.0, 9980.0)):
        row["best_bid"], row["best_ask"] = bid, ask
        row["bid_levels"] = [
            [i, bid - (i - 1) * 10, qty] for i, _, qty in row["bid_levels"]
        ]
        row["ask_levels"] = [
            [i, ask + (i - 1) * 10, qty] for i, _, qty in row["ask_levels"]
        ]
    now = datetime.fromisoformat("2026-08-14T09:00:16.100+09:00")
    parsed = source_fixture._replay_context("2026-08-14T09:00:16.000+09:00")[
        "exact_payload"
    ]
    parsed["ai_market_snapshot"]["ai_input_preflight_v1"] = {
        "allowed": True,
        "source_allowed": True,
        "venue_consistent": True,
        "blockers": [],
    }
    candidate = {
        "control": prompt_contract("Baseline English prompt.", role="control"),
        "input_reference": {
            "bridge_config": asdict(source_fixture._verified_config()),
            "symbol_master": source_fixture._canonical_symbol_master_payload(),
        },
        "r3_candidate": {
            key: evidence["economics"][key]
            for key in (
                "selected_cost_profile_id",
                "selected_cost_profile_content_sha256",
            )
        },
    }
    source = {
        "market": market,
        "depth": depth,
        "references": [source_fixture._reference()],
        "collector_barrier_verified": True,
        "coverage_start_ms": 0,
        "generation": 1,
        "sequence_epoch": 123,
    }
    return parsed, candidate, source, now


def test_live_input_reuses_canonical_causal_builders_without_provider_claim():
    parsed, candidate, source, now = live_input_fixture()
    text, receipt = prepare_input(
        base_input=json.dumps(parsed),
        request_id="live-1",
        symbol="000001",
        metadata={},
        candidate=candidate,
        now=now,
        source_reader=lambda *a, **kw: source,
    )
    enriched = json.loads(text)
    assert enriched["exact_payload"] == parsed
    assert (
        enriched[bridge.TACTICAL_EVIDENCE_SCHEMA]["source_quality"][
            "future_outcome_fields_in_context"
        ]
        is False
    )
    assert enriched[bridge.TACTICAL_EVIDENCE_SCHEMA]["runtime_effect"] is False
    assert (
        enriched[bridge.ASK_DEPLETION_FEATURE_VIEW_SCHEMA]["context"]["symbol"]
        == "000001"
    )
    assert receipt["provider_delivery_confirmed"] is False
    assert receipt["input_sha256"] == hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.parametrize(
    "defect",
    [
        "pending",
        "stale",
        "future",
        "sim",
        "wrong_symbol",
        "missing_depth",
        "coverage",
        "preflight",
    ],
)
def test_live_input_rejects_causal_and_custody_defects(defect):
    parsed, candidate, source, now = live_input_fixture()
    metadata = {}
    symbol = "000001"
    if defect == "pending":
        source["collector_barrier_verified"] = False
    elif defect == "stale":
        now += timedelta(seconds=2)
    elif defect == "future":
        now -= timedelta(seconds=2)
    elif defect == "sim":
        metadata["sim_record_id"] = "sim-1"
    elif defect == "wrong_symbol":
        symbol = "000002"
    elif defect == "missing_depth":
        source["depth"] = []
    elif defect == "coverage":
        source["coverage_start_ms"] = int(now.timestamp() * 1000)
    elif defect == "preflight":
        parsed["ai_market_snapshot"]["ai_input_preflight_v1"]["source_allowed"] = False
    with pytest.raises(ValueError):
        prepare_input(
            base_input=json.dumps(parsed),
            request_id="live-1",
            symbol=symbol,
            metadata=metadata,
            candidate=candidate,
            now=now,
            source_reader=lambda *a, **kw: source,
        )


def test_same_contract_renewal_requires_committed_first_identity(
    artifacts, monkeypatch
):
    activation = activation_for(artifacts, monkeypatch)
    _, _, candidate, authorization, now = deepcopy(artifacts)
    authorization = policy.seal({**authorization, "allow_same_contract_renewal": True})
    activation = policy.seal(
        {**activation, "authorization_sha256": authorization[policy.HASH_FIELD]}
    )
    first = policy.apply_receipt(activation)
    next_candidate = policy.seal(
        {
            **candidate,
            "source_date": candidate["target_date"],
            "target_date": policy.next_session(candidate["target_date"]),
        }
    )
    policy.validate_authorization(
        authorization=authorization,
        candidate=next_candidate,
        now=now + timedelta(days=1),
        first_receipt=first,
    )
    changed = deepcopy(next_candidate)
    changed["r3_candidate"]["recommended_contract_sha256"] = "0" * 64
    changed = policy.seal(changed)
    with pytest.raises(ValueError, match="enrollment_receipt"):
        policy.validate_authorization(
            authorization=authorization,
            candidate=changed,
            now=now + timedelta(days=1),
            first_receipt=first,
        )


def test_invalidation_never_waits_for_bulk_snapshot_copy():
    buffer = CurrentAxisSourceBuffer()
    finished = threading.Event()
    with buffer._lock:
        worker = threading.Thread(target=lambda: (buffer.invalidate(), finished.set()))
        worker.start()
        assert finished.wait(1), "producer invalidation waited for consumer row copying"
    worker.join(timeout=1)
    assert buffer.generation == 1


@pytest.mark.parametrize("revoked", [False, True])
@pytest.mark.parametrize("capture_valid", [False, True])
def test_actual_openai_call_captures_selected_bytes_and_discards_revoked_response(
    monkeypatch, revoked, capture_valid
):
    from dataclasses import replace
    from src.engine import ai_engine_openai as engine_module
    from src.tests.test_ai_engine_openai_transport import _build_engine

    engine = _build_engine()
    captured = {}
    sent = {}
    baseline = {}
    receipt = {
        "runtime_effect": True,
        "selected_prompt_version": "candidate-test",
        "prompt_sha256": hashlib.sha256(b"Selected English prompt.").hexdigest(),
        "input_sha256": hashlib.sha256(b'{"selected":true}').hexdigest(),
    }

    def select_request(request, **kwargs):
        baseline["request"] = request
        return (
            replace(
                request,
                prompt="Selected English prompt.",
                user_input='{"selected":true}',
            ),
            receipt,
        )

    monkeypatch.setattr(runtime, "select_request", select_request)
    monkeypatch.setattr(
        runtime,
        "settle_response",
        lambda value, **kw: {
            **value,
            "decision_usable": not (revoked and value.get("runtime_effect")),
            "provider_delivery_confirmed": True,
        },
    )

    def capture_request(**kw):
        captured.update(kw)
        return {
            "ai_prompt_sha256": hashlib.sha256(kw["prompt"].encode()).hexdigest(),
            "ai_input_payload_sha256": hashlib.sha256(
                kw["user_input"].encode()
            ).hexdigest(),
            "ai_prompt_replay_exact": capture_valid,
            "ai_input_payload_replay_exact": capture_valid,
        }

    monkeypatch.setattr(engine_module, "capture_ai_request", capture_request)

    def transport(request):
        sent["request"] = request
        return SimpleNamespace(
            payload={"action": "BUY", "score": 90},
            transport_mode="http",
            roundtrip_ms=1,
            usage_meta={},
            timing_meta={},
        )

    monkeypatch.setattr(engine, "_call_openai_responses_http", transport)
    result = engine._call_openai_safe(
        "Baseline English prompt.",
        "{}",
        schema_name="entry_v1",
        endpoint_name="analyze_target",
        symbol="000001",
        transport_mode_override="http",
    )
    assert (
        captured["prompt"]
        == sent["request"].prompt
        == ("Selected English prompt." if capture_valid else baseline["request"].prompt)
    )
    assert (
        captured["user_input"]
        == sent["request"].user_input
        == ('{"selected":true}' if capture_valid else "{}")
    )
    assert result["action"] == ("WAIT" if revoked and capture_valid else "BUY")
    metadata = engine._consume_last_transport_meta()
    assert json.loads(metadata["main_ai_current_axis_receipt"])[
        "decision_usable"
    ] is not (revoked and capture_valid)


def test_live_collector_registers_read_only_handoff_and_closes_with_owner(
    monkeypatch, tmp_path
):
    from src.engine.scalping.micro_reversion import current_axis_source
    from src.tests.test_micro_reversion_forward_collector import _collector

    monkeypatch.setenv(policy.ENABLED_ENV, "true")
    monkeypatch.setattr(current_axis_source, "_owner", None)
    monkeypatch.setattr(current_axis_source, "_owner_conflict", False)
    collector = _collector(tmp_path, depth_capture_enabled=True)
    try:
        assert collector._current_axis_buffer is not None
        with pytest.raises(ValueError, match="warming"):
            current_axis_source.live_source("000001", captured_at_ms=1)
    finally:
        collector.close()
    with pytest.raises(ValueError, match="not_ready"):
        current_axis_source.live_source("000001", captured_at_ms=1)


@pytest.mark.parametrize(
    "auto,mode,write",
    [
        ("true", "auto_bounded_live", True),
        ("false", "auto_bounded_live", False),
        ("true", "observe", False),
    ],
)
def test_current_preopen_wrapper_requires_auto_live_after_entry_owner(
    auto, mode, write
):
    import subprocess

    wrapper = (policy.ROOT / "deploy/run_threshold_cycle_preopen.sh").read_text()
    start = wrapper.index("current_axis_preopen_args=(")
    assert wrapper.index("-m src.engine.scalping.entry_setup_live_policy") < start
    snippet = wrapper[start : wrapper.index("finished_at=", start)]
    result = subprocess.run(
        [
            "bash",
            "-c",
            f'VENV_PY=/bin/echo\nTARGET_DATE=2026-09-08\nAUTO_APPLY={auto}\nAPPLY_MODE={mode}\nmark_preopen_failed() {{ echo "unexpected_failure:$*"; }}\n'
            + snippet,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        "-m src.engine.automation.main_ai_current_axis --phase preopen --target-date 2026-09-08"
        in result.stdout
    )
    assert ("--write" in result.stdout) is write
    assert "unexpected_failure" not in result.stdout


def test_current_postclose_wrapper_handoff_follows_research_without_provider():
    import subprocess

    wrapper = (policy.ROOT / "deploy/run_threshold_cycle_postclose.sh").read_text()
    start = wrapper.index('if [[ "$TARGET_DATE" > "2026-09-06" ]]; then')
    assert wrapper.index("-m src.engine.scalping.main_ai_prompt_consumer") < start
    snippet = wrapper[
        start : wrapper.index(
            'if [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT"', start
        )
    ]
    result = subprocess.run(
        [
            "bash",
            "-c",
            'VENV_PY=/unused\nTARGET_DATE=2026-09-07\nrun_postclose_cmd() { echo "$*"; }\nemit_postclose_marker() { echo "$*"; }\n'
            + snippet,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--phase postclose --target-date 2026-09-07 --write" in result.stdout
    assert result.stdout.count("src.engine.automation.main_ai_current_axis") == 1
