"""Initial ledger integration with temporary authority/files; no live values."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import hashlib

import pytest

from src.engine.automation import machine_adaptive_exit_approval as bridge
from src.engine.automation import machine_microstructure_policy_approval as ledger
from src.tests.test_machine_adaptive_exit_activation import (
    CODE,
    PREOPEN,
    fixture,
    load,
    persist,
    publish,
    sign,
)
from src.trading.config import machine_adaptive_exit_activation as activation
from src.trading.config.machine_adaptive_exit_policy import FAMILY
from src.utils.jsonl_io import write_json_object_generation_safe as write

POSTCLOSE = datetime.fromisoformat("2026-09-09T22:00:00+09:00")
DECIDED = datetime.fromisoformat("2026-09-09T22:01:00+09:00")


def context(data):
    return bridge.registry_entry(
        envelope=data["envelope"],
        expected_envelope_sha256=data["envelope"]["canonical_sha256"],
        runtime_code_sha256=CODE,
        execution_readiness={
            "source_sha256": "d" * 64,
            "scope_keys": sorted(data["envelope"]["scopes"]),
            "same_stage_owner_conflict_free": True,
            "owner_services_reviewed": True,
        },
    )


def scheduled(tmp_path, data):
    entry = context(data)
    candidates = bridge.build_candidates(
        source_path=data["source_path"], trusted_entry=entry
    )
    registry = {FAMILY: entry}
    queue_path = tmp_path / "queue.json"
    queue, rejected = ledger.sync_queue(
        ledger.load_queue(queue_path, now=POSTCLOSE),
        source_candidates=candidates,
        source_path=data["source_path"],
        as_of_date=POSTCLOSE.date(),
        source_status="loaded",
        now=POSTCLOSE,
        runtime_registry=registry,
        apply_receipt_dir=tmp_path / "receipts",
    )
    assert rejected == []
    assert all(r["state"] == ledger.STATE_REVIEW_READY for r in queue["candidates"])
    for candidate in candidates:
        queue, _ = ledger.record_operator_decision(
            queue,
            candidate_id=candidate["candidate_id"],
            expected_candidate_sha256=candidate["candidate_sha256"],
            decision="approve",
            operator_authorization_id=data["envelope"]["approval_id"],
            operator_instruction="Synthetic fixture only, not a live authorization",
            approval_dir=tmp_path / "decisions",
            apply_receipt_dir=tmp_path / "receipts",
            runtime_registry=registry,
            now=DECIDED,
        )
    queue, paths = ledger.schedule_preopen_handoffs(
        queue,
        target_date=PREOPEN.date(),
        handoff_dir=tmp_path / "handoffs",
        now=PREOPEN,
        runtime_registry=registry,
    )
    assert len(paths) == len(candidates)
    write(queue_path, queue)
    return entry, queue_path, queue, paths


def run_publish(data, entry, queue_path, **overrides):
    return bridge.publish_preopen(
        **(
            {k: data[k] for k in ("source_path", "envelope_path", "output_path")}
            | dict(queue_path=queue_path, trusted_entry=entry, now=PREOPEN)
            | overrides
        )
    )


def test_native_source_common_ledger_publisher_loader(tmp_path):
    data = fixture(tmp_path)
    before = data["source_path"].read_bytes()
    entry, queue_path, queue, paths = scheduled(tmp_path, data)
    result = run_publish(data, entry, queue_path)
    native = result["selections"][data["scope"]]["candidate"]
    assert queue["candidates"][0]["candidate_id"] == native["recommendation_id"]
    assert native["eligible_for_next_preopen"] is False
    assert result["publication_receipt"]["status"] == "published_not_loaded"
    assert load(data).policy.scope_key == data["scope"]
    assert run_publish(data, entry, queue_path) == result
    assert data["source_path"].read_bytes() == before
    assert FAMILY not in ledger.TRUSTED_RUNTIME_FAMILY_REGISTRY
    assert len(paths) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("same_stage_owner_conflict_free", False),
        ("same_stage_owner_conflict_free", 1),
        ("owner_services_reviewed", False),
        ("owner_services_reviewed", None),
        ("scope_keys", []),
        ("source_sha256", ""),
    ],
)
def test_no_readiness_defaults(tmp_path, field, value):
    data = fixture(tmp_path)
    args = context(data)["initial_approval"]
    args["execution_readiness"][field] = value
    with pytest.raises(ValueError, match="readiness"):
        bridge.registry_entry(**args)


@pytest.mark.parametrize(
    "change",
    [
        "schema",
        "family",
        "native_id",
        "scope",
        "auto",
        "evidence",
        "authority",
        "hash",
    ],
)
def test_candidate_cannot_choose_validator_or_authority(tmp_path, change):
    data = fixture(tmp_path)
    entry = context(data)
    candidate = bridge.build_candidates(
        source_path=data["source_path"], trusted_entry=entry
    )[0]
    if change == "schema":
        candidate["schema"] = "unregistered_schema"
    elif change == "family":
        candidate["runtime_design"]["runtime_family"] = "unregistered_family"
    elif change == "native_id":
        candidate["candidate_id"] = "adaptive-exit:invented"
    elif change == "scope":
        candidate["owner_scope_id"] = "episode|other|005930|KRX|KRX_REGULAR"
    elif change == "auto":
        candidate["first_operator_approval_required"] = False
    elif change == "evidence":
        candidate["evidence"]["selection"]["base_evidence"]["model_id"] = "forged"
    elif change == "authority":
        candidate["allowed_runtime_apply"] = True
    else:
        candidate["candidate_sha256"] = "f" * 64
    assert ledger.evidence_readiness_errors(candidate, runtime_registry={FAMILY: entry})
    assert ledger.runtime_design_errors(candidate, runtime_registry={FAMILY: entry})


def test_candidate_and_registry_pins_independent(tmp_path):
    data = fixture(tmp_path)
    entry = context(data)
    candidate = bridge.build_candidates(
        source_path=data["source_path"], trusted_entry=entry
    )[0]
    assert ledger.evidence_readiness_errors(candidate)
    bad = deepcopy(entry)
    bad["initial_approval"]["envelope"]["approval_id"] = "self-approved"
    assert ledger.evidence_readiness_errors(candidate, runtime_registry={FAMILY: bad})
    # The independent contract is used, without manufacturing legacy 5/10/20d metrics.
    assert "rolling_source_quality_adjusted_ev_pct" not in candidate["evidence"]
    assert (
        ledger.evidence_readiness_errors(candidate, runtime_registry={FAMILY: entry})
        == []
    )


@pytest.mark.parametrize(
    "change",
    [
        "queue_hold",
        "decision_hold",
        "handoff_auto",
        "handoff_quantity_authority",
        "handoff_date",
        "handoff_hash",
        "handoff_axis",
        "handoff_future",
        "missing_handoff",
        "approval_revoked",
        "source_changed",
    ],
)
def test_no_publication_on_handoff_or_current_authority_gap(tmp_path, change):
    data = fixture(tmp_path)
    entry, queue_path, queue, paths = scheduled(tmp_path, data)
    row = queue["candidates"][0]
    if change == "queue_hold":
        row["state"] = ledger.STATE_HOLD
        write(queue_path, queue)
    elif change == "decision_hold":
        path = Path(row["operator_decision_artifact"])
        decision = activation.read_plain(path).payload
        decision["decision"] = "hold"
        write(path, decision)
    elif change == "missing_handoff":
        paths[0].rename(tmp_path / "preserved-handoff.json")
    elif change == "approval_revoked":
        data["envelope"]["approval_id"] = "revoked"
        persist(data)
    elif change == "source_changed":
        data["parent"]["changed"] = True
        write(data["source_path"], data["parent"])
    else:
        handoff = activation.read_plain(paths[0]).payload
        field, value = {
            "handoff_auto": (
                "authorization_mode",
                "enrolled_same_bounded_family_auto_chain",
            ),
            "handoff_quantity_authority": ("allowed_runtime_apply", 1),
            "handoff_date": ("target_date", "2026-09-11"),
            "handoff_hash": ("candidate_sha256", "b" * 64),
            "handoff_axis": ("axis", "entry"),
            "handoff_future": ("created_at_kst", "2026-09-10T07:40:00+09:00"),
        }[change]
        handoff[field] = value
        write(paths[0], handoff)
    with pytest.raises((ValueError, FileNotFoundError)):
        run_publish(data, entry, queue_path)
    assert not data["output_path"].exists()


@pytest.mark.parametrize("auto", [False, True])
def test_initial_scheduler_rejects_wrong_target_and_auto_chain(tmp_path, auto):
    data = fixture(tmp_path)
    entry, _, queue, _ = scheduled(tmp_path, data)
    queue["candidates"][0]["state"] = (
        ledger.STATE_AUTO_CHAIN_ELIGIBLE if auto else ledger.STATE_USER_APPROVED
    )
    now = PREOPEN if auto else datetime.fromisoformat("2026-09-11T07:30:00+09:00")
    result, paths = ledger.schedule_preopen_handoffs(
        queue,
        target_date=now.date(),
        now=now,
        handoff_dir=tmp_path / "wrong",
        runtime_registry={FAMILY: entry},
    )
    assert paths == []
    assert result["candidates"][0]["state"] == ledger.STATE_DESIGN_REQUIRED


@pytest.mark.parametrize("at", ["08:00:00", "08:30:00"])
def test_publisher_cutoff_independent_of_later_admission_window(tmp_path, at):
    data = fixture(tmp_path)
    data["envelope"]["valid_from"] = "2026-09-10T09:00:00+09:00"
    persist(data)
    with pytest.raises(ValueError, match="preopen"):
        publish(data, now=datetime.fromisoformat(f"2026-09-10T{at}+09:00"))
    assert not data["output_path"].exists()


def test_loader_rejects_after_cutoff_publication_even_if_resigned(tmp_path):
    data = fixture(tmp_path)
    data["envelope"]["valid_from"] = "2026-09-10T09:00:00+09:00"
    persist(data)
    result = publish(data)
    result["publication_receipt"]["published_at"] = "2026-09-10T08:30:00+09:00"
    sign(result["publication_receipt"])
    sign(result)
    write(data["output_path"], result)
    with pytest.raises(ValueError, match="publication_window"):
        load(data)


@pytest.mark.parametrize("missing_second", [False, True])
def test_all_selected_owner_scopes_required_atomically(tmp_path, missing_second):
    data = fixture(tmp_path / "widget")
    other = fixture(tmp_path / "episode", owner="episode", profile="low_price:test")
    study = data["parent"]["rolling_policy_research_v2"]["all_scope_study"]
    second = other["parent"]["rolling_policy_research_v2"]["all_scope_study"]
    for field in ("evidence", "scopes", "policy_promotion_candidates"):
        study[field].extend(second[field])
    data["envelope"]["scopes"].update(other["envelope"]["scopes"])
    persist(data)
    entry, queue_path, queue, paths = scheduled(tmp_path, data)
    assert len(paths) == 2
    if missing_second:
        paths[1].rename(tmp_path / "second-preserved.json")
        with pytest.raises(FileNotFoundError):
            run_publish(data, entry, queue_path)
        assert not data["output_path"].exists()
    else:
        result = run_publish(data, entry, queue_path)
        assert len(result["selections"]) == 2
        provenance = result["publication_receipt"]["approval_ledger_receipt"]
        assert len(provenance["native_handoffs"]) == 2
        assert (
            provenance["queue_byte_sha256"]
            == hashlib.sha256(queue_path.read_bytes()).hexdigest()
        )


def test_unrelated_queue_refresh_preserves_original_publication_receipt(tmp_path):
    data = fixture(tmp_path)
    entry, queue_path, queue, _ = scheduled(tmp_path, data)
    result = run_publish(data, entry, queue_path)
    queue["diagnostic_note"] = "unrelated valid queue refresh"
    write(queue_path, queue)
    assert run_publish(data, entry, queue_path) == result


def test_context_cli_intake_decision_preopen_then_family_publish(
    tmp_path, monkeypatch, capsys
):
    data = fixture(tmp_path)
    # Use the actual common producer schema/consumer contract, not a patched loader.
    data["parent"].update(
        schema="machine_microstructure_attribution_v1",
        authority=dict(bridge.AUTHORITY),
        promotion_candidate_intake_contract={
            "schema": ledger.CANDIDATE_SCHEMA,
            "consumer": "src.engine.automation.machine_microstructure_policy_approval",
            "daily_report_runtime_effect": False,
        },
        policy_promotion_candidates=[],
        objective_followups=[],
    )
    persist(data)
    operator_context = tmp_path / "operator-context.json"
    write(operator_context, context(data)["initial_approval"])
    context_hash = hashlib.sha256(operator_context.read_bytes()).hexdigest()
    paths = {
        k: tmp_path / k
        for k in (
            "queue-path",
            "report-dir",
            "approval-dir",
            "handoff-dir",
            "apply-receipt-dir",
        )
    }
    paths["queue-path"] = tmp_path / "queue.json"
    argv = [arg for key, path in paths.items() for arg in ("--" + key, str(path))]
    argv += [
        "--adaptive-exit-initial-context",
        str(operator_context),
        "--adaptive-exit-initial-context-sha256",
        context_hash,
    ]
    clock = [POSTCLOSE]
    monkeypatch.setattr(ledger, "_now_kst", lambda now=None: now or clock[0])
    assert (
        ledger.main(
            argv
            + [
                "--phase",
                "postclose",
                "--target-date",
                "2026-09-09",
                "--source-report",
                str(data["source_path"]),
                "--write",
            ]
        )
        == 0
    )
    queue = ledger.load_queue(paths["queue-path"])
    assert queue["last_sync"]["source_candidate_count"] == 1
    candidate = queue["candidates"][0]
    clock[0] = DECIDED
    assert (
        ledger.main(
            argv
            + [
                "--record-decision",
                "approve",
                "--candidate-id",
                candidate["candidate_id"],
                "--candidate-sha256",
                candidate["candidate_sha256"],
                "--operator-authorization-id",
                data["envelope"]["approval_id"],
                "--operator-instruction",
                "Fixture only",
            ]
        )
        == 0
    )
    clock[0] = PREOPEN
    assert (
        ledger.main(argv + ["--phase", "preopen", "--target-date", "2026-09-10"]) == 2
    )
    assert not paths["handoff-dir"].exists()
    assert (
        ledger.main(
            argv + ["--phase", "preopen", "--target-date", "2026-09-10", "--write"]
        )
        == 0
    )
    trusted = bridge.load_initial_context(
        operator_context, expected_byte_sha256=context_hash
    )
    consumer_argv = [
        arg
        for key, path in {
            "context-path": operator_context,
            "queue-path": paths["queue-path"],
            "source-path": data["source_path"],
            "envelope-path": data["envelope_path"],
            "output-path": data["output_path"],
        }.items()
        for arg in ("--" + key, str(path))
    ]
    consumer_argv += ["--context-sha256", context_hash]
    before = {
        str(p): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    assert bridge.main(consumer_argv + ["--check-only"]) == 0
    assert not data["output_path"].exists()
    assert {
        str(p): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    } == before
    assert bridge.main(consumer_argv + ["--publish"]) == 0
    result = run_publish(data, trusted, paths["queue-path"])
    assert result["publication_receipt"]["approval_ledger_receipt"]["native_handoffs"]
    assert load(data).policy.scope_key == data["scope"]
    assert FAMILY not in ledger.TRUSTED_RUNTIME_FAMILY_REGISTRY
    capsys.readouterr()


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_effect", 0),
        ("first_operator_approval_required", 1),
        ("broker_order_forbidden", 1),
    ],
)
def test_literal_authority_even_when_numeric_equals_boolean(tmp_path, field, value):
    data = fixture(tmp_path)
    entry = context(data)
    candidate = bridge.build_candidates(
        source_path=data["source_path"], trusted_entry=entry
    )[0]
    candidate[field] = value
    assert bridge.candidate_errors(candidate, entry)


def test_output_cannot_overwrite_queue(tmp_path):
    data = fixture(tmp_path)
    entry, queue_path, _, _ = scheduled(tmp_path, data)
    before = queue_path.read_bytes()
    with pytest.raises(ValueError, match="overwrite_authority"):
        run_publish(data, entry, queue_path, output_path=queue_path)
    assert queue_path.read_bytes() == before


@pytest.mark.parametrize("artifact", ["operator_decision_artifact", "preopen_handoff"])
def test_unknown_order_authority_rejected(tmp_path, artifact):
    data = fixture(tmp_path)
    entry, queue_path, queue, _ = scheduled(tmp_path, data)
    path = Path(queue["candidates"][0][artifact])
    raw = activation.read_plain(path).payload
    raw["quantity_authority"] = True
    write(path, raw)
    with pytest.raises(ValueError, match="fields_invalid"):
        run_publish(data, entry, queue_path)
    assert not data["output_path"].exists()


def test_wrong_authorization_id_cannot_issue_positive_handoff(tmp_path):
    data = fixture(tmp_path)
    entry, _, queue, _ = scheduled(tmp_path, data)
    row = queue["candidates"][0]
    row["state"] = ledger.STATE_USER_APPROVED
    row["operator_authorization_id"] = "OTHER_INSTRUCTION"
    result, paths = ledger.schedule_preopen_handoffs(
        queue,
        target_date=PREOPEN.date(),
        now=PREOPEN,
        handoff_dir=tmp_path / "wrong",
        runtime_registry={FAMILY: entry},
    )
    assert paths == []
    assert result["candidates"][0]["state"] == ledger.STATE_DESIGN_REQUIRED


def test_check_only_detects_queue_change_between_two_reads(tmp_path, monkeypatch):
    data = fixture(tmp_path)
    entry, queue_path, _, _ = scheduled(tmp_path, data)
    original = ledger.load_queue

    def changed(path, **kwargs):
        queue = original(path, **kwargs)
        revoked = deepcopy(queue)
        revoked["candidates"][0]["state"] = ledger.STATE_HOLD
        write(path, revoked)
        return queue

    monkeypatch.setattr(ledger, "load_queue", changed)
    with pytest.raises(ValueError, match="authority_changed"):
        run_publish(data, entry, queue_path, check_only=True)
    assert not data["output_path"].exists()


def test_malformed_pinned_context_is_a_contract_error(tmp_path):
    data = fixture(tmp_path)
    raw = context(data)["initial_approval"]
    raw["envelope"]["source_date"] = None
    sign(raw["envelope"])
    raw["expected_envelope_sha256"] = raw["envelope"]["canonical_sha256"]
    path = tmp_path / "malformed-context.json"
    write(path, raw)
    with pytest.raises(ValueError, match="initial_context_invalid"):
        bridge.load_initial_context(
            path, expected_byte_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )
