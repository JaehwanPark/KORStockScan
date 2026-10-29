"""Explicit same-day ADD publication, separate from sealed postclose artifacts.

Scalping owns the reviewed registration; startup automation attests the code PID.
This path never changes source dates, quotas, original PREOPEN files or orders.
"""

from __future__ import annotations
import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_registration as ER

AUTHORITY = "APPROVED_INTRADAY_EXTENDED_REGISTRATION_20261008"
LIFETIME_AUTHORITY = "APPROVED_OPERATOR_SCOPED_ENTRY_LIFETIME_20261029"
LIFETIME_OPERATOR_MAX_SEC = 9.6


def lifetime_parent_origin(parent):
    """Keep the original producer, independently of the later active pointer."""
    family = parent["continuous_reversal"]
    refresh = family.get("code_refresh") or {}
    origin = family.get("release_root") or refresh.get("activation_parent_origin_root")
    if origin is None:
        return None
    commit = family["release_commit"]
    if (not isinstance(origin, str) or not Path(origin).is_absolute()
            or not re.fullmatch(r"[0-9a-f]{40}", str(commit))
            or not family.get("release_root")
            and refresh.get("activation_parent_origin_commit") != commit):
        raise ValueError("lifetime_parent_origin_invalid")
    return dict(root=origin, commit=commit)


def validate_lifetime_auxiliary(family, parent, data_root):
    """Reconcile the immutable as-of auxiliary sources, never a later pointer."""
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    validate_lifetime_parent(family, parent)
    a = validate_lifetime_activation(family)
    snapshot = a.get("auxiliary_handoff") or {}
    expected = {}
    for key, route in V.scopes():
        cell = parent["continuous_reversal"]["auxiliary_cells"][key]["routes"][route]
        payload = cell["payload"]
        expected[V.scope_id(key, route)] = G.definition(
            payload["arm"], input_version=payload["binding"]["input_version"]
        )["registry_sha256"]
    expected.update(I.inherited(data_root, parent))
    overlay = None
    reference = snapshot.get("overlay_generation")
    if reference is not None:
        path = I.root(data_root) / "generations" / (reference["generation"] + ".json")
        if P.file_hash(path) != reference.get("sha256"):
            raise ValueError("lifetime_auxiliary_overlay_changed")
        overlay = I.read(path)
        if overlay.get("artifact_content_sha256") != reference["generation"]:
            raise ValueError("lifetime_auxiliary_overlay_changed")
        I.validate_record(data_root, overlay, parent, check_definitions=True)
        expected.update(overlay["bindings"])
    independent = sorted(I.independent_scopes(data_root, parent, overlay))
    if (snapshot.get("bindings") != expected
            or snapshot.get("independent_scopes") != independent):
        raise ValueError("lifetime_auxiliary_parent_changed")
    source = N.root(Path(data_root)) / "sources" / (
        "reversal-" + family["auxiliary_report_sha256"] + ".json")
    report = I.read(source)
    if (report.get("auxiliary_registry_bindings") != expected
            or report.get("auxiliary_independent_scopes") != independent
            or report.get("auxiliary_reader_code_hashes") != snapshot.get("reader_hashes")):
        raise ValueError("lifetime_auxiliary_handoff_changed")
    for ident in set(expected.values()):
        G.load(data_root, ident)
    return snapshot


def validate_lifetime_current_auxiliary(parent, activation, data_root, day):
    """Machine publisher lock also serializes the native auxiliary publisher."""
    from src.engine.scalping import reversal_auxiliary_intraday as I

    snapshot = activation.get("auxiliary_handoff") or {}
    overlay = I.current(data_root, parent, day=day)
    observed = overlay["artifact_content_sha256"] if overlay else None
    expected = (snapshot.get("overlay_generation") or {}).get("generation")
    if (observed != expected
            or I.effective_bindings(data_root, parent, day=day) != snapshot.get("bindings")
            or sorted(I.independent_scopes(data_root, parent, overlay)) != snapshot.get("independent_scopes")):
        raise ValueError("lifetime_auxiliary_parent_advanced")


def validate_lifetime_activation(family):
    """Validate the operator's explicit per-scope transition envelope."""
    from src.engine.scalping.entry_deadline import validate_lifetime_policy

    a = family.get("registration_activation") or {}
    changes = a.get("scope_lifetimes")
    if (
        a.get("schema") != "main_intraday_entry_lifetime_transition_v1"
        or a.get("authority") != LIFETIME_AUTHORITY
        or a.get("artifact_content_sha256") != P.seal(a)["artifact_content_sha256"]
        or a.get("parent_bundle_sha256") != family.get("parent_bundle_sha256")
        or not re.fullmatch(r"[0-9a-f]{64}", str(a.get("parent_bundle_sha256", "")))
        or a.get("source_date") != family.get("source_date")
        or a.get("publication_date") != family.get("publication_date")
        or a.get("target_date") != family.get("effective_date")
        or a.get("release_commit") != family.get("release_commit")
        or a.get("publication_date") != a.get("target_date")
        or a.get("actual_order_submitted") is not False
        or a.get("provider_called") is not False
        or not isinstance(changes, dict)
        or not changes
    ):
        raise ValueError("lifetime_intraday_authority_invalid")
    for sid, requested in changes.items():
        if not isinstance(sid, str) or "|" not in sid:
            raise ValueError("lifetime_intraday_scope_invalid")
        key, route = sid.rsplit("|", 1)
        try:
            cell = family["machine_cells"][key]["routes"][route]
        except (KeyError, TypeError):
            raise ValueError("lifetime_intraday_scope_invalid") from None
        checked = validate_lifetime_policy(requested)
        if checked.get("schema") != "entry_signal_lifetime_policy_v2" or any(
            v > LIFETIME_OPERATOR_MAX_SEC
            for v in checked["branch_max_signal_age_sec"].values()
        ):
            raise ValueError("lifetime_intraday_operator_bound_invalid")
        if (
            cell.get("backend") != "union_v6"
            or cell.get("signal_lifetime_policy") != checked
        ):
            raise ValueError("lifetime_intraday_policy_changed")
    return a


def validate_lifetime_parent(family, parent):
    """Only the explicitly issued lifetimes may differ from the active parent."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    a = validate_lifetime_activation(family)
    if parent.get("bundle_sha256") != a["parent_bundle_sha256"]:
        raise ValueError("lifetime_intraday_parent_changed")
    previous = parent["continuous_reversal"]
    if (
        a.get("parent_validation_origin") != lifetime_parent_origin(parent)
        or family["operating_manifest"]
        != V.detector_manifest(parent, effective_date=family["effective_date"])
        or previous["auxiliary_cells"] != family["auxiliary_cells"]
        or previous["source_date"] != family["source_date"]
        or previous["source_manifest_sha256"] != family["source_manifest_sha256"]
        or a.get("selection_parent_bundle_sha256")
        != previous.get("parent_bundle_sha256")
    ):
        raise ValueError("lifetime_intraday_parent_behavior_changed")
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        old = previous["machine_cells"][key]["routes"][route]
        new = family["machine_cells"][key]["routes"][route]
        if {
            k: v
            for k, v in old.items()
            if k not in {"signal_lifetime_policy", "scope_execution_hash"}
        } != {
            k: v
            for k, v in new.items()
            if k not in {"signal_lifetime_policy", "scope_execution_hash"}
        }:
            raise ValueError("lifetime_intraday_machine_behavior_changed")
        expected = a["scope_lifetimes"].get(sid, old.get("signal_lifetime_policy"))
        if new.get("signal_lifetime_policy") != expected:
            raise ValueError("lifetime_intraday_unissued_scope_changed")
    return parent


def stage_lifetime(
    data_root,
    day,
    *,
    confirm,
    release_commit,
    expected_parent_bundle_sha256,
    scope_lifetimes,
    now=None,
):
    """Issue an explicit same-day lifetime change over the authenticated parent."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping.entry_deadline import validate_lifetime_policy

    clock = now or datetime.now(P.KST)
    if (
        confirm != LIFETIME_AUTHORITY
        or clock.astimezone(P.KST).date().isoformat() != day
    ):
        raise ValueError("lifetime_intraday_explicit_today_authority_required")
    if not isinstance(scope_lifetimes, dict) or not scope_lifetimes:
        raise ValueError("lifetime_intraday_scope_invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_parent_bundle_sha256)):
        raise ValueError("lifetime_intraday_parent_cas_failed")
    parent = N.load_effective(data_root=Path(data_root), target_date=day)
    if not parent:
        raise ValueError("lifetime_intraday_parent_missing")
    if parent.get("bundle_sha256") != expected_parent_bundle_sha256:
        raise ValueError("lifetime_intraday_parent_cas_failed")
    previous = parent["continuous_reversal"]
    from src.engine.scalping import reversal_auxiliary_intraday as I

    overlay = I.current(data_root, parent, day=day)
    auxiliary_handoff = dict(
        bindings=I.effective_bindings(data_root, parent, day=day),
        independent_scopes=sorted(I.independent_scopes(data_root, parent, overlay)),
        reader_hashes=I.code_hashes(),
        overlay_generation=(dict(
            generation=overlay["artifact_content_sha256"],
            sha256=P.file_hash(I.root(data_root) / "generations" /
                              (overlay["artifact_content_sha256"] + ".json")),
        ) if overlay else None),
    )
    policies = {sid: validate_lifetime_policy(p) for sid, p in scope_lifetimes.items()}
    if any(p["schema"] != "entry_signal_lifetime_policy_v2" for p in policies.values()):
        raise ValueError("lifetime_intraday_branch_policy_required")
    if any(
        v > LIFETIME_OPERATOR_MAX_SEC
        for p in policies.values()
        for v in p["branch_max_signal_age_sec"].values()
    ):
        raise ValueError("lifetime_intraday_operator_bound_invalid")
    available = {V.scope_id(k, r) for k, r in V.scopes()}
    if not set(policies).issubset(available):
        raise ValueError("lifetime_intraday_scope_invalid")
    candidate = (
        N.root(Path(data_root)) / "intraday_candidates" / ("policy_" + day + ".json")
    )
    if candidate.exists():
        prior = N._read(candidate)
        a = prior.get("continuous_reversal", {}).get("registration_activation") or {}
        if (
            a.get("parent_bundle_sha256") == parent["bundle_sha256"]
            and a.get("release_commit") == release_commit
            and a.get("scope_lifetimes") == policies
        ):
            N.validate(prior, target_date=day)
            V.validate_sources(prior, data_root)
            return prior
        raise ValueError("lifetime_intraday_candidate_exists")
    cells = copy.deepcopy(previous["machine_cells"])
    auxiliary_cells = copy.deepcopy(previous["auxiliary_cells"])
    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    execution_code_sha256 = P.digest(code)
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        cell = cells[key]["routes"][route]
        if sid in policies:
            if cell.get("backend") != "union_v6":
                raise ValueError("lifetime_intraday_backend_invalid")
            cell["signal_lifetime_policy"] = policies[sid]
        ids = [b["branch_id"] for b in cell["payload"]["branches"]]
        cell["scope_execution_hash"] = V.scope_hash(
            ids,
            auxiliary_cells[key]["routes"][route]["payload"],
            cell["backend"],
            execution_code_sha256,
            cell.get("signal_lifetime_policy"),
        )
    activation = P.seal(
        dict(
            schema="main_intraday_entry_lifetime_transition_v1",
            authority=confirm,
            parent_bundle_sha256=parent["bundle_sha256"],
            parent_validation_origin=lifetime_parent_origin(parent),
            auxiliary_handoff=auxiliary_handoff,
            selection_parent_bundle_sha256=previous["parent_bundle_sha256"],
            scope_lifetimes=policies,
            source_date=previous["source_date"],
            publication_date=day,
            target_date=day,
            release_commit=release_commit,
            requested_at=clock.isoformat(),
            provider_called=False,
            actual_order_submitted=False,
        )
    )
    sources = []
    for name in ("machine", "auxiliary"):
        path = (
            N.root(Path(data_root))
            / "sources"
            / ("reversal-" + previous[name + "_report_sha256"] + ".json")
        )
        if P.file_hash(path) != previous["report_file_sha256"][name]:
            raise ValueError("lifetime_intraday_parent_report_changed")
        sources.append(dict(path=str(path.resolve()), sha256=P.file_hash(path)))
    manifest = V.detector_manifest(parent, effective_date=day)
    common = dict(
        schema=O.SCHEMA,
        source_date=previous["source_date"],
        publication_date=day,
        target_date=day,
        status="completed",
        parent_bundle_sha256=parent["bundle_sha256"],
        observation_mode="operator_lifetime_transition_parent_evidence_only",
        source_receipts=sources,
        **P.AUTH,
    )
    machine = P.seal(
        dict(
            common,
            cells=list(cells.values()),
            operating_manifest=manifest,
            execution_code_sha256=execution_code_sha256,
            source_manifest_sha256=previous["source_manifest_sha256"],
            registration_activation=activation,
        )
    )
    auxiliary = P.seal(
        dict(
            common,
            cells=list(auxiliary_cells.values()),
            machine_report_sha256=machine["artifact_content_sha256"],
            auxiliary_registry_bindings=auxiliary_handoff["bindings"],
            auxiliary_independent_scopes=auxiliary_handoff["independent_scopes"],
            auxiliary_reader_code_hashes=auxiliary_handoff["reader_hashes"],
        )
    )
    return V.stage(
        data_root,
        previous["source_date"],
        day,
        machine,
        auxiliary,
        target_date=day,
        release_commit=release_commit,
        effective_mode="intraday",
        registration_activation=activation,
    )


def validate_activation(family):
    a = family.get("registration_activation") or {}
    if (
        a.get("schema") != "main_extended_intraday_registration_v1"
        or a.get("authority") != AUTHORITY
        or a.get("artifact_content_sha256") != P.seal(a)["artifact_content_sha256"]
        or a.get("parent_bundle_sha256") != family["parent_bundle_sha256"]
        or a.get("research_batch_sha256") != C.RESEARCH_BATCH_SHA256
        or a.get("target_date") != family["effective_date"]
        or a.get("publication_date") != family["publication_date"]
        or a.get("source_date") != family["source_date"]
        or a.get("release_commit") != family["release_commit"]
        or family["publication_date"] != family["effective_date"]
        or a.get("comparison_result_required") is not False
    ):
        raise ValueError("extended_intraday_authority_or_date_invalid")
    approved = {
        d["symbol_group"]
        + "|"
        + d["market"]
        + "|"
        + d["price_band"]
        + "|"
        + d["route"]: [b]
        for b, d in C.NEW_DEFINITIONS.items()
    }
    expected = copy.deepcopy(a.get("parent_scopes", {}))
    if not expected or a.get("approved_additions") != approved:
        raise ValueError("extended_intraday_additions_invalid")
    for sid, ids in approved.items():
        if sid not in expected:
            raise ValueError("extended_intraday_parent_scope_missing")
        expected[sid] = sorted(set(expected[sid]) | set(ids))
    if expected != family["operating_manifest"]["scopes"]:
        raise ValueError("extended_intraday_membership_changed")
    return a


def stage(data_root, day, *, confirm, release_commit, now=None):
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O

    clock = now or datetime.now(P.KST)
    if confirm != AUTHORITY or clock.astimezone(P.KST).date().isoformat() != day:
        raise ValueError("extended_intraday_explicit_today_authority_required")
    parent = N.load_effective(data_root=Path(data_root), target_date=day)
    change = ER.pending(data_root, parent, N.next_target(day))
    if change is None:
        if (parent["continuous_reversal"].get("registration_activation") or {}).get(
            "research_batch_sha256"
        ) == C.RESEARCH_BATCH_SHA256:
            return parent
        raise ValueError("extended_intraday_registration_missing")
    candidate = (
        N.root(Path(data_root)) / "intraday_candidates" / ("policy_" + day + ".json")
    )
    if candidate.exists():
        prior = N._read(candidate)
        pf = prior.get("continuous_reversal", {})
        proof = pf.get("registration_activation") or {}
        if (
            pf.get("release_commit") == release_commit
            and pf.get("parent_bundle_sha256") == parent["bundle_sha256"]
            and proof.get("registered_request_sha256")
            == change["artifact_content_sha256"]
        ):
            N.validate(prior, target_date=day)
            V.validate_sources(prior, data_root)
            return prior
    f = parent["continuous_reversal"]
    source_date = f["source_date"]
    activation = P.seal(
        dict(
            schema="main_extended_intraday_registration_v1",
            authority=confirm,
            parent_bundle_sha256=parent["bundle_sha256"],
            parent_scopes=copy.deepcopy(f["operating_manifest"]["scopes"]),
            approved_additions={s: c["add"] for s, c in change["scopes"].items()},
            research_batch_sha256=C.RESEARCH_BATCH_SHA256,
            registered_request_sha256=change["artifact_content_sha256"],
            source_date=source_date,
            publication_date=day,
            target_date=day,
            original_planned_target=change["target_date"],
            release_commit=release_commit,
            requested_at=clock.isoformat(),
            comparison_result_required=False,
            actual_order_submitted=False,
        )
    )
    out = (
        Path(data_root)
        / "report/continuous_reversal_intraday_registration"
        / day
        / activation["artifact_content_sha256"]
    )
    P.write(out / "authorization.json", activation)
    source = (
        N.root(Path(data_root))
        / "sources"
        / ("reversal-" + f["machine_report_sha256"] + ".json")
    )
    if P.file_hash(source) != f["report_file_sha256"]["machine"]:
        raise ValueError("extended_intraday_parent_report_changed")
    manifest = V.detector_manifest(parent, effective_date=day, changes=change)
    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    machine = P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=source_date,
            publication_date=day,
            target_date=day,
            status="completed",
            parent_bundle_sha256=parent["bundle_sha256"],
            operating_manifest=manifest,
            execution_code_sha256=P.digest(code),
            source_manifest_sha256=f["source_manifest_sha256"],
            registration_change=change,
            policy_schema=V.SCHEMA,
            source_receipts=[
                dict(path=str(source.resolve()), sha256=P.file_hash(source)),
                dict(
                    path=str((out / "authorization.json").resolve()),
                    sha256=P.file_hash(out / "authorization.json"),
                ),
            ],
            population="frozen_registered_research_batch",
            observation_mode="explicit_registration_no_new_replay",
            cumulative_metrics=None,
            comparison_state="incomplete",
            registration_activation=activation,
            **P.AUTH,
        )
    )
    auxiliary = ER.initial_reports(
        data_root,
        source_date,
        day,
        parent,
        machine,
        publish_policy=False,
        output_directory=out,
        effective_date=day,
    )
    issued = N._read(out / "machine.json")
    bundle = V.stage(
        data_root,
        source_date,
        day,
        issued,
        auxiliary,
        target_date=day,
        release_commit=release_commit,
        effective_mode="intraday",
        registration_activation=activation,
    )
    P.write(
        out / "staged.json",
        P.seal(
            dict(
                status="staged",
                bundle_sha256=bundle["bundle_sha256"],
                source_date=source_date,
                target_date=day,
                actual_pid_consumed=False,
                provider_called=False,
            )
        ),
    )
    return bundle


def activate(data_root, day, *, pid, confirm, now=None):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    if (
        confirm not in {AUTHORITY, LIFETIME_AUTHORITY}
        or Path(data_root).resolve() != Path(H.DATA_DIR).resolve()
    ):
        raise ValueError("extended_intraday_activation_authority_required")
    clock = H._today(day, now)
    root, commit = H._selection()
    candidate = N._read(
        N.root(Path(data_root)) / "intraday_candidates" / ("policy_" + day + ".json")
    )
    if (
        candidate.get("continuous_reversal", {}).get("registration_activation") or {}
    ).get("authority") != confirm:
        raise ValueError("extended_intraday_candidate_authority_mismatch")
    identity = H._identity(pid)
    check = H.verify(day, commit, now=clock)
    _, consumed_path = H._paths(day, commit)
    consumed = H._read(consumed_path)
    if (
        identity["cwd"] != str(root / "src")
        or check["status"] != "pass"
        or consumed.get("status") != "pass"
        or consumed.get("pid_identity") != identity
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("selected_release_commit") != commit
    ):
        raise ValueError("extended_intraday_code_consumption_missing")
    bootstrap = H._checked_bootstrap(day, pid)
    evidence = dict(
        schema="intraday_main_policy_code_pid_v1",
        target_date=day,
        release_commit=commit,
        pid_identity=identity,
        consumed_path=str(consumed_path),
        consumed_sha256=P.file_hash(consumed_path),
        manifest_sha256=bootstrap["manifest_sha256"],
        verified_at=clock.isoformat(),
        custody_and_order_paths="existing_native_main_guards_unchanged",
    )
    return V.activate(
        data_root,
        day,
        now=clock,
        intraday_evidence=evidence,
        expected_intraday_bundle_sha256=candidate["bundle_sha256"],
        expected_intraday_authority=confirm,
    )


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--date", required=True)
    p.add_argument(
        "--mode", choices=["stage", "stage-lifetime", "activate"], required=True
    )
    p.add_argument("--confirm", required=True)
    p.add_argument("--pid", type=int)
    p.add_argument("--scope-lifetimes-file", type=Path)
    p.add_argument("--parent-bundle-sha256")
    a = p.parse_args(argv)
    if a.mode in {"stage", "stage-lifetime"}:
        from src.engine.infrastructure.runtime_release_router import selected_release

        _, commit = selected_release(a.data_root.resolve().parent)
        if a.mode == "stage-lifetime":
            if a.scope_lifetimes_file is None:
                raise ValueError("lifetime_intraday_scope_file_required")
            policies = json.loads(a.scope_lifetimes_file.read_text(encoding="utf-8"))
            b = stage_lifetime(
                a.data_root,
                a.date,
                confirm=a.confirm,
                release_commit=commit,
                expected_parent_bundle_sha256=a.parent_bundle_sha256,
                scope_lifetimes=policies,
            )
        else:
            if a.scope_lifetimes_file is not None or a.parent_bundle_sha256 is not None:
                raise ValueError("lifetime_intraday_scope_file_unexpected")
            b = stage(a.data_root, a.date, confirm=a.confirm, release_commit=commit)
        result = dict(
            status="staged",
            bundle_sha256=b["bundle_sha256"],
            target_date=b["target_date"],
            actual_pid_consumed=False,
        )
    else:
        if a.scope_lifetimes_file is not None or a.parent_bundle_sha256 is not None:
            raise ValueError("lifetime_intraday_scope_file_unexpected")
        result = activate(a.data_root, a.date, pid=a.pid, confirm=a.confirm)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
