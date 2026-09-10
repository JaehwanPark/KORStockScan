"""Pinned test generations only; no live policy, launcher or broker calls."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta

import pytest

from src.tests.test_machine_adaptive_exit_activation import (
    CODE,
    OPEN,
    PREOPEN,
    fixture,
    publish,
)
from src.tests.test_machine_adaptive_exit_study import SOURCE_DAYS
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.enrollment import (
    InitialPolicyAdmission,
    PolicyAdmissionCatalog,
)
from src.trading.order.adaptive_exit.owner_loop import binding_authorized
from src.trading.order.adaptive_exit.runtime import OwnerSession
from src.trading.order.adaptive_exit.source import record_target_observation
from src.utils.jsonl_io import write_json_object_generation_safe

pytest_plugins = ["src.tests.test_machine_adaptive_exit_enrollment"]
NEXT = OPEN + timedelta(days=1)


def next_generation(x, tmp_path):
    scope = x.source["scope"]
    data = fixture(
        tmp_path / "next-generation",
        owner=scope["owner"],
        route=scope["route"],
        profile=scope["profile"],
        entry_policy_hash=x.source["entry_policy_hash"],
        source_days=SOURCE_DAYS + ("2026-09-10",),
        target_date="2026-09-11",
    )
    publish(data, now=PREOPEN + timedelta(days=1))
    return InitialPolicyAdmission(
        data["output_path"],
        data["envelope_path"],
        data["envelope"]["canonical_sha256"],
        CODE,
        NEXT - timedelta(minutes=10),
    )


def prepare(catalog, x, *, now=OPEN):
    source = x.source
    context = OwnerSession.from_payload(x.raw()).context
    return catalog.prepare(
        source_receipt=source,
        context=context,
        target_intent_id=OwnerSession.from_payload(x.raw()).target_intent_id,
        now=now,
    )


def test_current_catalog_reaches_existing_owner_enrollment_and_fake_wire(
    enrolled_owner,
):
    x = enrolled_owner
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services,
        admission=PolicyAdmissionCatalog(CODE, x.admission),
    )
    registry = x.registry.path.read_bytes()
    assert x.propose()
    assert not x.wire.calls and x.registry.path.read_bytes() == registry
    assert x.receipt()["envelope_sha256"] == x.admission.expected_envelope_sha256
    x.machine._state = x.machine._load_state()
    x.machine.run_once(OPEN)
    assert OwnerSession.from_payload(x.raw()).driver.orders.phase == "CANCEL_PENDING"
    assert len(x.wire.writes) == 1


def test_next_day_keeps_original_binding_without_reselection(enrolled_owner, tmp_path):
    x = enrolled_owner
    assert x.propose()
    current = next_generation(x, tmp_path)
    retained = replace(x.admission, started_at=NEXT)
    catalog = PolicyAdmissionCatalog(CODE, current, (retained,))
    original = x.path.read_bytes()
    x.machine._state = x.machine._load_state()
    session, receipt = OwnerSession.from_payload(x.raw()), x.receipt()
    assert not current.authorize(session.binding, receipt, now=NEXT)
    assert catalog.authorize(session.binding, receipt, now=NEXT)
    services = replace(x.machine.adaptive_exit_services, admission=catalog)
    assert binding_authorized(services, session, receipt, now=NEXT)
    assert not binding_authorized(
        replace(services, authorize_binding=lambda b: False), session, receipt, now=NEXT
    )
    assert receipt["envelope_sha256"] == retained.expected_envelope_sha256
    assert receipt["envelope_sha256"] != current.expected_envelope_sha256
    assert x.path.read_bytes() == original and not x.wire.calls
    # A new selection cannot retroactively adopt yesterday's target.
    with pytest.raises(ValueError, match="new_position_admission_clock_invalid"):
        prepare(catalog, x, now=NEXT)
    # Before the next window, yesterday's policy would accept this source;
    # the catalog must not fall back to it after current rejects admission.
    prepare(PolicyAdmissionCatalog(CODE, x.admission), x, now=OPEN)
    with pytest.raises(ValueError, match="new_position_admission_clock_invalid"):
        prepare(catalog, x, now=OPEN)


def test_new_day_proposal_uses_only_current_generation(enrolled_owner, tmp_path):
    x = enrolled_owner
    assert x.propose()
    current = next_generation(x, tmp_path)
    catalog = PolicyAdmissionCatalog(CODE, current, (x.admission,))
    entries = deepcopy(x.source["entries"])
    for entry in entries:
        entry["order_date"] = "2026-09-11"
        entry["episode_id"] = entry["episode_id"].replace("2026-09-10", "2026-09-11")
        observation = entry["first_fill_observation"]
        for key in ("first_observed_at", "last_zero_observed_at", "last_observed_at"):
            if observation.get(key):
                observation[key] = observation[key].replace("2026-09-10", "2026-09-11")
    store = {}
    scope = x.source["scope"]
    record_target_observation(
        store,
        **{k: scope[k] for k in ("owner", "profile", "symbol", "session")},
        entry_policy=x.source["entry_policy"],
        observed_at=(NEXT - timedelta(minutes=1)).isoformat(),
        target=x.source["target"] | {"order_date": "2026-09-11"},
        entries=entries,
    )
    old = OwnerSession.from_payload(x.raw())
    context = replace(
        old.context,
        owner_id=old.context.owner_id.replace("2026-09-10", "2026-09-11"),
        position_id=old.context.position_id.replace("2026-09-10", "2026-09-11"),
    )
    session, receipt = catalog.prepare(
        source_receipt=store["adaptive_exit_target_observations"]["2026-09-11:0000002"],
        context=context,
        target_intent_id="synthetic-next-target-intent",
        now=NEXT,
    )
    assert receipt["envelope_sha256"] == current.expected_envelope_sha256
    assert catalog.authorize(session.binding, receipt, now=NEXT)
    assert not x.admission.authorize(session.binding, receipt, now=NEXT)
    assert session.driver.orders.target.trading_date == "2026-09-11"
    assert not x.wire.calls  # Proposal only; no registry enrollment or broker call.


def test_rollback_disables_new_but_retains_original_owner_execution(enrolled_owner):
    x = enrolled_owner
    services = x.machine.adaptive_exit_services
    rollback = PolicyAdmissionCatalog(CODE, None, (x.admission,))
    x.machine.adaptive_exit_services = replace(services, admission=rollback)
    assert not x.propose() and not x.wire.calls
    state = x.machine._state if x.owner == "episode" else x.state
    assert "new_position_admission_disabled" in state["adaptive_exit_enrollment_status"]
    x.machine.adaptive_exit_services = services
    assert x.propose()
    x.machine.adaptive_exit_services = replace(services, admission=rollback)
    with pytest.raises(ValueError, match="new_position_admission_disabled"):
        prepare(rollback, x)
    x.machine._state = x.machine._load_state()
    x.machine.run_once(OPEN)
    assert OwnerSession.from_payload(x.raw()).driver.orders.phase == "CANCEL_PENDING"
    assert len(x.wire.writes) == 1


def test_missing_current_does_not_poison_retained_or_fallback_new(
    enrolled_owner, tmp_path
):
    x = enrolled_owner
    assert x.propose()
    current = replace(
        next_generation(x, tmp_path), policy_path=tmp_path / "missing-current.json"
    )
    catalog = PolicyAdmissionCatalog(CODE, current, (x.admission,))
    session = OwnerSession.from_payload(x.raw())
    assert catalog.authorize(session.binding, x.receipt(), now=NEXT)
    with pytest.raises((OSError, ValueError)):
        prepare(catalog, x, now=NEXT)
    assert not x.wire.calls


@pytest.mark.parametrize("damage", ["missing", "changed", "removed"])
def test_retained_generation_must_still_validate(enrolled_owner, tmp_path, damage):
    x = enrolled_owner
    assert x.propose()
    current = next_generation(x, tmp_path)
    retained = x.admission
    if damage == "missing":
        retained = replace(retained, policy_path=tmp_path / "missing-retained.json")
    elif damage == "changed":
        changed = deepcopy(x.data["envelope"])
        changed["approval_id"] += "_UNAPPROVED_REPLACEMENT"
        changed["canonical_sha256"] = canonical_sha256(changed)
        write_json_object_generation_safe(retained.envelope_path, changed)
    catalog = PolicyAdmissionCatalog(
        CODE, current, () if damage == "removed" else (retained,)
    )
    services = replace(x.machine.adaptive_exit_services, admission=catalog)
    session = OwnerSession.from_payload(x.raw())
    assert not binding_authorized(services, session, x.receipt(), now=NEXT)
    # Missing authority retains the manager, never erases the position.
    assert session.manager_required and not x.wire.calls


@pytest.mark.parametrize("damage", ["unknown", "redirect", "binding", "empty"])
def test_receipt_cannot_redirect_generation_authority(enrolled_owner, tmp_path, damage):
    x = enrolled_owner
    assert x.propose()
    current = next_generation(x, tmp_path)
    catalog = PolicyAdmissionCatalog(CODE, current, (x.admission,))
    receipt = deepcopy(x.receipt())
    if damage == "empty":
        receipt = None
    else:
        if damage == "unknown":
            receipt["envelope_sha256"] = "0" * 64
        elif damage == "redirect":
            receipt["envelope_sha256"] = current.expected_envelope_sha256
        else:
            receipt["binding_sha256"] = "0" * 64
        receipt["canonical_sha256"] = canonical_sha256(receipt)
    assert not catalog.authorize(
        OwnerSession.from_payload(x.raw()).binding, receipt, now=NEXT
    )
    assert not x.wire.calls


@pytest.mark.parametrize(
    "damage", ["duplicate", "mutable", "code", "alias", "digest", "empty", "path"]
)
def test_catalog_rejects_ambiguous_or_unpinned_configuration(
    enrolled_owner, damage, tmp_path
):
    admission = enrolled_owner.admission
    current, retained = admission, ()
    if damage == "duplicate":
        retained = (admission,)
    elif damage == "mutable":
        retained = [admission]
    elif damage == "code":
        current = replace(admission, runtime_code_sha256="d" * 64)
    elif damage == "alias":
        alias = tmp_path / "approval-alias.json"
        alias.symlink_to(admission.envelope_path)
        current = replace(admission, policy_path=alias)
    elif damage == "digest":
        current = replace(admission, expected_envelope_sha256="not-a-pin")
    elif damage == "empty":
        current = None
    else:
        current = replace(admission, policy_path=str(admission.policy_path))
    with pytest.raises(ValueError, match="policy_catalog"):
        PolicyAdmissionCatalog(CODE, current, retained)
