"""Synthetic control-plane fixtures only; these are not approved live values."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib

import pytest

from src.engine.automation import machine_adaptive_exit_policy_apply as publisher
from src.engine.monitoring.machine_adaptive_exit_evidence import (
    build_candidate,
    build_evidence,
)
from src.tests.test_machine_adaptive_exit_decision import inputs
from src.tests.test_machine_adaptive_exit_policy import contract
from src.tests.test_machine_adaptive_exit_study import pair, SOURCE_DAYS
from src.trading.config import machine_adaptive_exit_activation as activation
from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    canonical_sha256,
    make_policy_payload,
)
from src.utils.jsonl_io import write_json_object_generation_safe

CODE = "c" * 64
ENTRY = "e" * 64
PREOPEN = datetime.fromisoformat("2026-09-10T07:30:00+09:00")
OPEN = datetime.fromisoformat("2026-09-10T09:00:00+09:00")


def sign(raw):
    raw["canonical_sha256"] = canonical_sha256(raw)
    return raw


def fixture(
    tmp_path,
    *,
    owner="widget",
    route="KRX",
    profile="actual:test",
    entry_policy_hash=ENTRY,
    source_days=SOURCE_DAYS,
    target_date="2026-09-10",
):
    key = f"{owner}|{profile}|005930|{route}|KRX_REGULAR"
    params = asdict(inputs()[0])
    del params["policy_hash"], params["scope_key"]
    policy = make_policy_payload(scope_key=key, parameters=params)
    evaluation = asdict(contract())
    evaluation["holdout_end"] = source_days[-1]
    for k in ("contract_hash", "policy_hash", "scope_key"):
        del evaluation[k]
    scope = dict(
        policy=policy,
        candidate_sha256="a" * 64,
        entry_policy_hashes=[entry_policy_hash],
        evaluation=evaluation,
        execution_cost_guard=dict(
            basis="independently_approved_execution_cost_guard",
            source_sha256="f" * 64,
            round_trip_cost_pct=0.23,
        ),
        model_ids=["base", "stress"],
        execution_bounds=dict(
            sell_ttl_ms=1000,
            maximum_sell_attempts=2,
            maximum_unprotected_ms=5000,
            vanished_arm="exit_with_fresh_guard",
            final_residual="retain_manager_and_alert",
        ),
    )
    frozen = activation.evaluation_contract(scope, scope_key=key)
    models = []
    days = source_days + (source_days[-1],)
    for model in scope["model_ids"]:
        pairs = []
        for i, day in enumerate(days):
            row = pair(
                day, f"episode:{i}", model=model, pnl=10 if model == "base" else 8
            )
            row["policy_hash"] = policy["policy_hash"]
            for leg in ("baseline", "candidate"):
                row[leg].update(
                    policy_hash=policy["policy_hash"],
                    scope_key=key,
                    owner_id=owner,
                    entry_policy_hash=entry_policy_hash,
                )
            pairs.append(row)
        models.append(
            build_evidence(
                pairs,
                frozen,
                source_trading_dates=source_days,
                model_id=model,
                expected_episode_lots={
                    f"episode:{i}": ("leg1",) for i in range(len(days))
                },
            )
        )
    candidate = build_candidate(
        base_evidence=models[0],
        stress_evidence=models[1],
        contract=frozen,
        policy_payload=policy,
    )
    assert candidate["decision"] == "research_ready", candidate["errors"]
    scope["candidate_sha256"] = candidate["canonical_sha256"]
    study = sign(
        dict(
            schema="machine_adaptive_exit_study_v1",
            target_date=source_days[-1],
            authority=dict(AUTHORITY),
            status="study_evaluated",
            evidence=models,
            policy_promotion_candidates=[candidate],
            scopes=[
                dict(
                    scope_key=key,
                    status="study_evaluated",
                    owner_census_valid=True,
                    execution_scope=True,
                )
            ],
        )
    )
    child = sign(
        dict(
            schema="machine_adaptive_exit_source_census_v1",
            family="machine_adaptive_exit_v1",
            target_date=source_days[-1],
            authority=dict(AUTHORITY),
            all_scope_study=study,
        )
    )
    parent = dict(target_date=source_days[-1], rolling_policy_research_v2=child)
    envelope = dict(
        schema=activation.ENVELOPE_SCHEMA,
        family="machine_adaptive_exit_v1",
        validator=activation.VALIDATOR,
        phase="initial_canary",
        approval_id="TEST_ONLY_NOT_LIVE_APPROVAL",
        source_date=source_days[-1],
        target_date=target_date,
        source_report_sha256="a" * 64,
        source_child_sha256=child["canonical_sha256"],
        runtime_code_sha256=CODE,
        valid_from=f"{target_date}T08:00:00+09:00",
        valid_until=f"{target_date}T20:00:00+09:00",
        lifecycle=dict(activation.LIFECYCLE),
        policy_authority=dict(activation.POLICY_AUTHORITY),
        scopes={key: scope},
    )
    data = dict(
        parent=parent,
        envelope=envelope,
        scope=key,
        source_path=tmp_path / "source.json",
        envelope_path=tmp_path / "approval.json",
        output_path=tmp_path / "applied.json",
    )
    persist(data)
    return data


def persist(data):
    child = data["parent"]["rolling_policy_research_v2"]
    sign(child["all_scope_study"])
    sign(child)
    write_json_object_generation_safe(data["source_path"], data["parent"])
    data["envelope"]["source_report_sha256"] = hashlib.sha256(
        data["source_path"].read_bytes()
    ).hexdigest()
    data["envelope"]["source_child_sha256"] = child["canonical_sha256"]
    sign(data["envelope"])
    write_json_object_generation_safe(data["envelope_path"], data["envelope"])


def publish(data, **override):
    kwargs = {k: data[k] for k in ("source_path", "envelope_path", "output_path")}
    kwargs.update(
        expected_envelope_sha256=data["envelope"]["canonical_sha256"],
        runtime_code_sha256=CODE,
        now=PREOPEN,
    )
    return publisher._publish_initial_policy(**(kwargs | override))


def load(data, **override):
    kwargs = dict(
        policy_path=data["output_path"],
        envelope_path=data["envelope_path"],
        expected_envelope_sha256=data["envelope"]["canonical_sha256"],
        runtime_code_sha256=CODE,
        scope_key=data["scope"],
        entry_policy_hash=ENTRY,
        now=OPEN,
    )
    return activation.load_for_new_position(**(kwargs | override))


@pytest.mark.parametrize("cost", [None, 0, -0.1, True, float("inf")])
def test_initial_execution_cost_guard_requires_approved_finite_positive_value(
    tmp_path, cost
):
    data = fixture(tmp_path)
    data["envelope"]["scopes"][data["scope"]]["execution_cost_guard"][
        "round_trip_cost_pct"
    ] = cost
    with pytest.raises(ValueError):
        persist(data)
        publish(data)


def test_research_comparison_cost_is_not_execution_authority(tmp_path):
    data = fixture(tmp_path)
    data["envelope"]["scopes"][data["scope"]]["execution_cost_guard"][
        "basis"
    ] = "research_report_only"
    persist(data)
    with pytest.raises(ValueError):
        publish(data)


@pytest.mark.parametrize(
    "owner,route",
    [("widget", "KRX"), ("widget", "NXT"), ("episode", "SOR"), ("episode", "KRX")],
)
def test_native_candidate_to_atomic_policy_to_read_only_loader(tmp_path, owner, route):
    data = fixture(tmp_path, owner=owner, route=route)
    original = data["source_path"].read_bytes()
    applied = publish(data)
    installed = data["output_path"].read_bytes()
    assert applied["publication_receipt"]["status"] == "published_not_loaded"
    assert applied["publication_receipt"]["authority"] == AUTHORITY
    assert (
        applied["selections"][data["scope"]]["candidate"]["eligible_for_next_preopen"]
        is False
    )
    loaded = load(data)
    assert loaded.policy.scope_key == data["scope"]
    assert (
        loaded.policy.policy_hash
        == data["envelope"]["scopes"][data["scope"]]["policy"]["policy_hash"]
    )
    assert loaded.applied_sha256 == applied["canonical_sha256"]
    assert publish(data, now=PREOPEN.replace(minute=40)) == applied
    assert data["output_path"].read_bytes() == installed
    assert data["source_path"].read_bytes() == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("validator", "choose_weaker_validator"),
        ("phase", "auto_maintenance"),
        ("runtime_code_sha256", "b" * 64),
        ("family", "entry_timing"),
        ("target_date", "2026-09-11"),
        ("source_date", "2026-06-04"),
        ("valid_from", "2026-09-10T08:00:00"),
        ("valid_until", "2026-09-11T20:00:00+09:00"),
        ("scopes", {}),
        ("approval_id", ""),
    ],
)
def test_approval_cannot_choose_registry_or_dates(tmp_path, field, value):
    data = fixture(tmp_path)
    data["envelope"][field] = value
    persist(data)
    with pytest.raises(ValueError):
        publish(data)
    assert not data["output_path"].exists()


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("lifecycle", "new_positions_only", 1),
        ("lifecycle", "maximum_extensions", True),
        ("lifecycle", "rollback", "delete_existing_manager"),
        ("lifecycle", "source_loss_policy", "sell_anyway"),
        ("policy_authority", "new_buy", True),
        ("policy_authority", "safety_override", 0),
    ],
)
def test_literal_authority_and_lifecycle_are_not_overridable(
    tmp_path, section, field, value
):
    data = fixture(tmp_path)
    data["envelope"][section][field] = value
    persist(data)
    with pytest.raises(ValueError):
        publish(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "candidate_missing",
        "duplicate_candidate",
        "duplicate_evidence",
        "scope_not_ready",
        "weak_evaluation",
        "native_id",
        "source_authority",
        "no_stress",
    ],
)
def test_source_and_independent_contract_fail_closed(tmp_path, mutation):
    data = fixture(tmp_path)
    study = data["parent"]["rolling_policy_research_v2"]["all_scope_study"]
    approved = data["envelope"]["scopes"][data["scope"]]
    if mutation == "candidate_missing":
        study["policy_promotion_candidates"] = []
    elif mutation == "duplicate_candidate":
        study["policy_promotion_candidates"] *= 2
    elif mutation == "duplicate_evidence":
        study["evidence"] *= 2
    elif mutation == "scope_not_ready":
        study["scopes"][0]["owner_census_valid"] = False
    elif mutation == "weak_evaluation":
        approved["evaluation"]["minimum_unique_episodes"] -= 1
    elif mutation == "native_id":
        candidate = study["policy_promotion_candidates"][0]
        candidate["recommendation_id"] = "invented"
        sign(candidate)
        approved["candidate_sha256"] = candidate["canonical_sha256"]
    elif mutation == "source_authority":
        study["authority"]["runtime_effect"] = 0
    elif mutation == "no_stress":
        study["evidence"].pop()
    persist(data)
    with pytest.raises(ValueError):
        publish(data)
    assert not data["output_path"].exists()


@pytest.mark.parametrize(
    "now",
    [
        "2026-09-09T23:00:00+09:00",
        "2026-09-10T08:00:00+09:00",
        "2026-09-11T07:00:00+09:00",
    ],
)
def test_publication_is_exact_target_preopen_only(tmp_path, now):
    data = fixture(tmp_path)
    with pytest.raises(ValueError, match="preopen"):
        publish(data, now=datetime.fromisoformat(now))


@pytest.mark.parametrize(
    "change",
    [
        dict(runtime_code_sha256="d" * 64),
        dict(entry_policy_hash="f" * 64),
        dict(scope_key="episode|other|005930|KRX|KRX_REGULAR"),
        dict(expected_envelope_sha256="f" * 64),
        dict(now=PREOPEN),
        dict(now=OPEN.replace(hour=20)),
        dict(now=OPEN.replace(day=11)),
    ],
)
def test_loader_requires_exact_scope_code_authority_and_window(tmp_path, change):
    data = fixture(tmp_path)
    publish(data)
    with pytest.raises(ValueError):
        load(data, **change)


def test_parent_regeneration_does_not_replace_frozen_issued_evidence(tmp_path):
    data = fixture(tmp_path)
    original = publish(data)
    write_json_object_generation_safe(
        data["source_path"], {"target_date": "2026-09-09", "new_generation": True}
    )
    assert load(data).applied_sha256 == original["canonical_sha256"]
    with pytest.raises(ValueError, match="parent_byte_hash"):
        publish(data)


def test_changed_approval_cannot_overwrite_existing_target_generation(tmp_path):
    data = fixture(tmp_path)
    publish(data)
    original = data["output_path"].read_bytes()
    data["envelope"]["approval_id"] = "different_approval"
    persist(data)
    with pytest.raises(ValueError, match="envelope_mismatch"):
        publish(data)
    assert data["output_path"].read_bytes() == original
    with pytest.raises(ValueError):
        load(data)


def test_content_hash_is_not_an_independent_approval(tmp_path):
    data = fixture(tmp_path)
    pin = data["envelope"]["canonical_sha256"]
    data["envelope"]["scopes"][data["scope"]]["execution_bounds"]["sell_ttl_ms"] = 9999
    persist(data)
    with pytest.raises(ValueError, match="independent_approval"):
        publish(data, expected_envelope_sha256=pin)


def test_no_partial_scope_publication_and_unselected_gaps_are_not_blanket_veto(
    tmp_path,
):
    data = fixture(tmp_path)
    study = data["parent"]["rolling_policy_research_v2"]["all_scope_study"]
    study["scopes"].append(
        dict(scope_key="unselected", status="blocked_missing_evidence")
    )
    persist(data)
    assert publish(data)
    other = "episode|missing|000001|KRX|KRX_REGULAR"
    scope = deepcopy(data["envelope"]["scopes"][data["scope"]])
    params = dict(scope["policy"])
    del params["scope_key"], params["policy_hash"]
    scope["policy"] = make_policy_payload(scope_key=other, parameters=params)
    data["envelope"]["scopes"][other] = scope
    persist(data)
    with pytest.raises(ValueError, match="approved_scope_source_not_ready"):
        publish(data)


def test_atomic_write_failure_propagates_without_false_receipt(tmp_path, monkeypatch):
    data = fixture(tmp_path)

    def fail(*args, **kwargs):
        raise OSError("test-only fsync failure")

    monkeypatch.setattr(publisher, "write_json_object_generation_safe", fail)
    with pytest.raises(OSError, match="fsync failure"):
        publish(data)
    assert not data["output_path"].exists()


def test_alias_and_duplicate_json_authority_are_rejected(tmp_path):
    data = fixture(tmp_path)
    alias = tmp_path / "alias.json"
    alias.symlink_to(data["envelope_path"])
    with pytest.raises((OSError, ValueError)):
        publish(data, output_path=alias)
    data["envelope_path"].write_text('{"schema":"a","schema":"b"}')
    with pytest.raises(ValueError):
        publish(data)


def test_read_only_load_checks_authority_changed_during_validation(
    tmp_path, monkeypatch
):
    data = fixture(tmp_path)
    publish(data)
    original = activation.validate_applied

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        data["envelope"]["approval_id"] = "revoked_during_read"
        persist(data)
        return result

    monkeypatch.setattr(activation, "validate_applied", changed)
    with pytest.raises(ValueError, match="approval_changed_during_load"):
        load(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("unique_episodes", 7),
        ("cost_contract_valid", False),
        ("purged_split_valid", False),
        ("holdout_candidate_net_ev_pct", None),
        ("right_censored_pct", 21),
        ("primary_paired_net_pnl_uplift_krw", 0),
        ("source_quality_valid", 1),
    ],
)
def test_even_pinned_native_ready_claim_is_independently_revalidated(
    tmp_path, field, value
):
    data = fixture(tmp_path)
    study = data["parent"]["rolling_policy_research_v2"]["all_scope_study"]
    evidence = study["evidence"][0]
    evidence[field] = value
    sign(evidence)
    candidate = study["policy_promotion_candidates"][0]
    candidate["evidence_hash"] = evidence["canonical_sha256"]
    # Simulate a faulty producer retaining a READY claim despite invalid evidence.
    body = {
        k: v
        for k, v in candidate.items()
        if k not in ("recommendation_id", "canonical_sha256")
    }
    candidate["recommendation_id"] = "adaptive-exit:" + canonical_sha256(body)[:32]
    sign(candidate)
    data["envelope"]["scopes"][data["scope"]]["candidate_sha256"] = candidate[
        "canonical_sha256"
    ]
    persist(data)
    with pytest.raises(ValueError, match="economic_evidence_rejected"):
        publish(data)
    assert not data["output_path"].exists()


def test_next_trading_date_handles_weekend_without_calendar_day_fallback(tmp_path):
    data = fixture(tmp_path)
    envelope = data["envelope"]
    envelope.update(
        source_date="2026-09-11",
        target_date="2026-09-14",
        valid_from="2026-09-14T08:00:00+09:00",
        valid_until="2026-09-14T20:00:00+09:00",
    )
    envelope["scopes"][data["scope"]]["evaluation"]["holdout_end"] = "2026-09-11"
    sign(envelope)
    assert activation.validate_envelope(
        envelope, expected_sha256=envelope["canonical_sha256"], runtime_code_sha256=CODE
    )
    envelope["target_date"] = "2026-09-12"
    sign(envelope)
    with pytest.raises(ValueError, match="exact_next_trading_date"):
        activation.validate_envelope(
            envelope,
            expected_sha256=envelope["canonical_sha256"],
            runtime_code_sha256=CODE,
        )


@pytest.mark.parametrize(
    "part", ["candidate", "base_evidence", "receipt", "source_hash"]
)
def test_rehashed_published_artifact_cannot_change_approved_content(tmp_path, part):
    data = fixture(tmp_path)
    payload = publish(data)
    selected = payload["selections"][data["scope"]]
    if part == "candidate":
        selected["candidate"]["eligible_for_next_preopen"] = True
        sign(selected["candidate"])
    elif part == "base_evidence":
        selected["base_evidence"]["model_id"] = "other"
        sign(selected["base_evidence"])
    elif part == "receipt":
        payload["publication_receipt"]["authority"]["runtime_effect"] = True
    else:
        payload["source_report_sha256"] = "d" * 64
    payload["publication_receipt"]["selection_sha256"] = canonical_sha256(
        payload["selections"]
    )
    sign(payload["publication_receipt"])
    sign(payload)
    write_json_object_generation_safe(data["output_path"], payload)
    with pytest.raises(ValueError):
        load(data)


def test_policy_changed_during_load_is_not_reported_as_consumed(tmp_path, monkeypatch):
    data = fixture(tmp_path)
    publish(data)
    validate = activation.validate_applied

    def changed(*args, **kwargs):
        result = validate(*args, **kwargs)
        write_json_object_generation_safe(data["output_path"], {"revoked": True})
        return result

    monkeypatch.setattr(activation, "validate_applied", changed)
    with pytest.raises(ValueError, match="policy_changed_during_load"):
        load(data)


def test_missing_authority_or_failed_existing_generation_never_falls_back(tmp_path):
    data = fixture(tmp_path)
    publish(data)
    original = data["output_path"].read_bytes()
    with pytest.raises((OSError, ValueError)):
        load(data, envelope_path=tmp_path / "missing.json")
    write_json_object_generation_safe(data["output_path"], {"status": "failed"})
    with pytest.raises(ValueError):
        publish(data)
    assert data["output_path"].read_bytes() != original
    with pytest.raises(ValueError):
        load(data)
