"""Content-addressed, exact-scope REPLACE intake for the frozen joint study.

Registration/publication belongs to the existing scalping publisher. This
module has no provider, broker, cron, or trading-process authority.
"""

from __future__ import annotations
import copy
import fcntl
import json
from pathlib import Path
from src.engine.scalping import reversal_joint_catalog as J
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N

AUTHORITY = J.AUTHORITY
SCHEMA = "main_joint_registration_request_v1"
SELECTION_AUTHORITY = "APPROVED_REGISTERED_JOINT_VARIANT_WINRATE_SELECTION_20261013"


def variant_groups(parent):
    groups = {}
    membership = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    for sid, change in J.changes().items():
        before = set(membership[sid])
        refined = set(change["add"]) & set(J.COMPOSED)
        addition = set(change["add"]) - refined
        after = (before - set(change["remove"])) | set(change["add"])
        groups[sid] = dict(
            previous_baseline=sorted(before),
            alternatives={
                "PREVIOUS_BASELINE": sorted(before),
                "ADD_A_ONLY": sorted(before | addition),
                "REPLACE_F_ONLY": sorted((before - set(change["remove"])) | refined),
                "JOINT_BALANCED": sorted(after),
            },
        )
    return groups


def select_variant(groups, sid, current, metrics, *, authority):
    if authority != SELECTION_AUTHORITY:
        raise ValueError("joint_variant_selection_not_delegated")
    alternatives = dict(groups[sid]["alternatives"], CURRENT_NATIVE=sorted(current))
    valid = []
    cohort = (metrics.get("CURRENT_NATIVE") or {}).get("source_universe_sha256")
    for name, ids in alternatives.items():
        m = metrics.get(name) or {}
        counts = m.get("counts", m)
        n = (
            counts.get("WIN", 0)
            + counts.get("FAIL_STOP", counts.get("STOP", 0))
            + counts.get("FAIL_TIMEOUT", counts.get("TIMEOUT", 0))
        )
        if (
            not n
            or m.get("source_complete") is not True
            or m.get("comparison_complete") is not True
        ):
            continue
        if not cohort or m.get("source_universe_sha256") != cohort:
            continue
        from fractions import Fraction

        valid.append(
            (
                Fraction(counts.get("WIN", 0), n),
                counts.get("WIN", 0),
                ids == sorted(current),
                name,
                ids,
            )
        )
    incumbent = next((v for v in valid if v[3] == "CURRENT_NATIVE"), None)
    if incumbent is None:
        return dict(branch_ids=sorted(current), status="comparison_incomplete_carry")
    winner = max(valid, key=lambda v: (v[0], v[1], v[2], v[3]))
    return dict(
        branch_ids=winner[4],
        variant=winner[3],
        status="selected" if winner[4] != sorted(current) else "carried",
    )


def pending_path(data_root):
    return N.root(Path(data_root)) / "joint-registration.json"


def validate_request(request):
    if (
        request.get("schema") != SCHEMA
        or request.get("artifact_content_sha256")
        != P.seal(request)["artifact_content_sha256"]
        or request.get("operator_receipt") != AUTHORITY
        or request.get("kind") != "REPLACE"
        or request.get("scopes") != J.changes()
        or request.get("registry_sha256") != C.JOINT_SHA256
        or request.get("research_batch_sha256") != J.RESEARCH_RESULT
        or request.get("definition_hashes")
        != {b: P.digest(d) for b, d in J.DEFINITIONS.items()}
        or request.get("comparison_result_required") is not False
        or not request.get("source_receipts")
    ):
        raise ValueError("joint_registration_authority_or_definition_changed")
    groups = request.get("variant_groups") or {}
    baseline = {
        "036930|AFTER|GE_100000|SOR": [
            "legacy_dd5_ge_0_4_v1",
            "manual_extended_27bebc59a6315682",
        ],
        "other_non_fixed|PRE|LT_20000|NXT": [
            "legacy_dd5_0_8_vol_up_v1",
            "manual_extended_f74502b35a4fae1f",
            "manual_residual_29b499784843baed",
            "manual_residual_bac0e83e966ed3ea",
        ],
    }
    frozen_parent = {
        "continuous_reversal": {"operating_manifest": {"scopes": baseline}}
    }
    if (
        groups != variant_groups(frozen_parent)
        or request.get("selection_authority") != SELECTION_AUTHORITY
    ):
        raise ValueError("joint_registration_variant_authority_changed")
    for source in request["source_receipts"]:
        if P.file_hash(N.source_path(source["path"])) != source["sha256"]:
            raise ValueError("joint_registration_evidence_changed")
    if not {J.EVIDENCE_FILE_SHA256, J.RESEARCH_RESULT} <= {
        s["sha256"] for s in request["source_receipts"]
    }:
        raise ValueError("joint_registration_frozen_research_missing")
    return request


def membership_complete(request, membership):
    return all(
        set(v["add"]) <= set(membership.get(s, []))
        and not set(v["remove"]) & set(membership.get(s, []))
        for s, v in request["scopes"].items()
    )


def pending(data_root, parent, target_date):
    path = pending_path(data_root)
    if not path.exists():
        return None
    r = validate_request(N._read(path))
    m = parent["continuous_reversal"].get("operating_manifest", {})
    ancestry = m.get("registration_receipts", []) + [m.get("change_receipt") or {}]
    if membership_complete(r, m.get("scopes", {})):
        if not any(
            a.get("artifact_content_sha256") == r["artifact_content_sha256"]
            for a in ancestry
        ):
            raise ValueError("joint_registration_consumed_receipt_missing")
        return None
    if any(
        a.get("artifact_content_sha256") == r["artifact_content_sha256"]
        for a in ancestry
    ):
        # A consumed or superseded request is never re-applied after rollback.
        return None
    if (
        r["parent_bundle_sha256"] != parent["bundle_sha256"]
        or r["target_date"] != target_date
    ):
        raise ValueError("joint_registration_parent_or_target_changed")
    return r


def intake(
    data_root,
    evidence_path,
    parity_path,
    *,
    parent,
    publication,
    target_date,
    origin_root,
    origin_commit,
    confirm,
):
    if confirm != AUTHORITY:
        raise ValueError("joint_registration_explicit_authority_required")
    evidence_path, parity_path = Path(evidence_path), Path(parity_path)
    result_path = evidence_path.parent / "opportunity-frontier-result.json"
    parity = json.loads(parity_path.read_text())
    evidence = json.loads(evidence_path.read_text())
    code = {Path(m.__file__).name: P.file_hash(m.__file__) for m in V_modules()}
    if (
        P.file_hash(evidence_path) != J.EVIDENCE_FILE_SHA256
        or evidence.get("result_sha256") != J.RESEARCH_RESULT
        or P.file_hash(result_path) != J.RESEARCH_RESULT
        or parent["bundle_sha256"] != J.PARENT
        or parity.get("status") != "pass"
        or parity.get("mismatches") != 0
        or parity.get("definition_hashes")
        != {b: P.digest(d) for b, d in J.DEFINITIONS.items()}
        or parity.get("parent_bundle_sha256") != parent["bundle_sha256"]
        or parity.get("contract_file_sha256") != code
        or not parent["source_date"] <= publication <= target_date
    ):
        raise ValueError("joint_registration_research_or_parity_invalid")
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    actual = V._attested_activation_parent(
        data_root, publication, origin_root=origin_root, origin_commit=origin_commit
    )
    if actual["bundle_sha256"] != parent["bundle_sha256"]:
        raise ValueError("joint_registration_parent_cas_failed")
    root = N.root(Path(data_root))
    root.mkdir(parents=True, exist_ok=True)
    with (root / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pointer = N._read(root / "current.json")
        if pointer["bundle_sha256"] != parent["bundle_sha256"]:
            raise ValueError("joint_registration_parent_changed")
        archive = (
            Path(data_root)
            / "report/continuous_reversal_operating/registrations"
            / J.RESEARCH_RESULT
        )
        archive.mkdir(parents=True, exist_ok=True)
        receipts = []
        for path in (
            evidence_path,
            result_path,
            evidence_path.parent / "frozen-manifest.json",
            evidence_path.parent / "joint-result.json",
            parity_path,
        ):
            raw = path.read_bytes()
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError("joint_registration_archive_budget_exceeded")
            sha = P.file_hash(path)
            dest = archive / (sha + ".json")
            if not dest.exists():
                with dest.open("xb") as f:
                    f.write(raw)
            if P.file_hash(dest) != sha:
                raise ValueError("joint_registration_archive_conflict")
            receipts.append(dict(path=str(dest.resolve()), sha256=sha))
        r = P.seal(
            dict(
                schema=SCHEMA,
                kind="REPLACE",
                operator_receipt=AUTHORITY,
                parent_bundle_sha256=parent["bundle_sha256"],
                research_batch_sha256=J.RESEARCH_RESULT,
                registry_sha256=C.JOINT_SHA256,
                scopes=J.changes(),
                definition_hashes={b: P.digest(d) for b, d in J.DEFINITIONS.items()},
                source_receipts=receipts,
                publication_date=publication,
                target_date=target_date,
                activation_parent_origin=dict(
                    root=str(Path(origin_root).resolve()), commit=origin_commit
                ),
                comparison_result_required=False,
                actual_order_submitted=False,
            )
        )
        r = P.seal(
            dict(
                r,
                variant_groups=variant_groups(parent),
                selection_authority=SELECTION_AUTHORITY,
            )
        )
        validate_request(r)
        destination = archive / (r["artifact_content_sha256"] + ".json")
        if destination.exists() and N._read(destination) != r:
            raise ValueError("joint_registration_request_conflict")
        N._atomic_write_json(destination, r)
        path = pending_path(data_root)
        if path.exists() and N._read(path) != r:
            old = validate_request(N._read(path))
            stable = (
                "operator_receipt",
                "parent_bundle_sha256",
                "research_batch_sha256",
                "registry_sha256",
                "scopes",
                "definition_hashes",
                "publication_date",
                "target_date",
                "variant_groups",
                "selection_authority",
            )
            if any(old.get(k) != r.get(k) for k in stable):
                raise ValueError("joint_registration_pending_conflict")
            # Review fixes can change the parity/code receipt before adoption.
            # Preserve the original batch; never relabel it or repeat its delta.
            if "supersedes_pending_sha256" in old:
                old_base = {
                    k: v
                    for k, v in old.items()
                    if k not in ("artifact_content_sha256", "supersedes_pending_sha256")
                }
                if P.seal(old_base) == r:
                    return old
            r = P.seal(
                dict(r, supersedes_pending_sha256=old["artifact_content_sha256"])
            )
            validate_request(r)
            destination = archive / (r["artifact_content_sha256"] + ".json")
            if destination.exists() and N._read(destination) != r:
                raise ValueError("joint_registration_request_conflict")
            N._atomic_write_json(destination, r)
        N._atomic_write_json(path, r)
        return r


def V_modules():
    from src.engine.scalping.continuous_reversal_policy_v6 import contract_modules

    return contract_modules()


def load_offline_parent(data_root, publication):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    r = validate_request(N._read(pending_path(data_root)))
    if r["publication_date"] != publication:
        raise ValueError("joint_publication_date_changed")
    origin = r["activation_parent_origin"]
    p = V._attested_activation_parent(
        data_root,
        publication,
        origin_root=origin["root"],
        origin_commit=origin["commit"],
    )
    if p["bundle_sha256"] != r["parent_bundle_sha256"]:
        raise ValueError("joint_offline_parent_changed")
    return p


def apply_selection(machine, parent):
    """Select only approved whole memberships on their own opportunity counts."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_union as A

    manifest = copy.deepcopy(machine["operating_manifest"])
    groups = manifest.get("approved_variant_groups") or {}
    if not groups:
        return machine
    chosen = {}
    complete = machine.get("status") == "completed" and bool(
        machine.get("source_manifest_receipt")
    )
    current = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    for sid in groups:
        cohort = P.digest(
            [machine["source_manifest_sha256"], sid, machine["label_contract"]]
        )
        metrics = {
            name: dict(
                machine["proposal_metrics"].get(sid + "::" + name) or {},
                source_universe_sha256=cohort,
                source_complete=complete,
                comparison_complete=complete,
            )
            for name in (*groups[sid]["alternatives"], "CURRENT_NATIVE")
        }
        chosen[sid] = select_variant(
            groups,
            sid,
            current[sid],
            metrics,
            authority=manifest.get("selection_authority"),
        )
        manifest["scopes"][sid] = chosen[sid]["branch_ids"]
    manifest["definitions"] = {
        b: C.definition(b)
        for b in sorted({b for ids in manifest["scopes"].values() for b in ids})
    }
    manifest["registry_sha256"] = C.registry_for(
        b for ids in manifest["scopes"].values() for b in ids
    )
    manifest["detector_manifest_hash"] = P.digest(
        {k: manifest[k] for k in ("schema", "scopes", "definitions", "registry_sha256")}
    )
    manifest["variant_selection_receipt"] = P.seal(
        dict(
            schema="joint_variant_selection_v1",
            authority=manifest["selection_authority"],
            source_manifest_sha256=machine["source_manifest_sha256"],
            parent_bundle_sha256=parent["bundle_sha256"],
            selected=chosen,
            memberships={s: manifest["scopes"][s] for s in groups},
        )
    )
    cells = {c["key"]: copy.deepcopy(c) for c in machine["cells"]}
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        cell = cells[key]["routes"][route]
        if sid not in groups:
            continue
        ids = manifest["scopes"][sid]
        payload = dict(
            composition="ANY_MATCH_ONE_INTENT", branches=[C.branch(b) for b in ids]
        )
        aux = parent["continuous_reversal"]["auxiliary_cells"][key]["routes"][route][
            "payload"
        ]
        cell.update(
            payload=payload,
            payload_sha256=P.digest(payload),
            backend="union_v6",
            scope_execution_hash=V.scope_hash(
                ids, aux, "union_v6", machine["execution_code_sha256"]
            ),
        )
    return P.seal(
        dict(
            machine,
            operating_manifest=manifest,
            cells=list(cells.values()),
            variant_selection=chosen,
            variant_selection_basis="cumulative_target_first_win_fraction",
        )
    )


def initial_reports(
    data_root,
    day,
    publication,
    parent,
    machine,
    *,
    output_directory=None,
    publish_policy=True,
    effective_date=None,
):
    """Metadata-only initial binding; never clone the comparison call ledger."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_extended_union as A
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_registry as G

    r = validate_request(machine["registration_change"])
    target = effective_date or r["target_date"]
    manifest = V.detector_manifest(parent, effective_date=target, changes=r)
    if manifest != machine["operating_manifest"]:
        raise ValueError("joint_initial_machine_manifest_changed")
    if output_directory is not None and publish_policy:
        raise ValueError("joint_isolated_output_required")
    mc = copy.deepcopy(parent["continuous_reversal"]["machine_cells"])
    ac = copy.deepcopy(parent["continuous_reversal"]["auxiliary_cells"])
    bindings = {}
    current = I.effective_bindings(data_root, parent, day=publication)
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        ids = manifest["scopes"][sid]
        old = ac[key]["routes"][route]
        aux = dict(arm=old["payload"]["arm"], binding=A.binding(old["payload"]["arm"]))
        payload = dict(
            composition="ANY_MATCH_ONE_INTENT", branches=[C.branch(b) for b in ids]
        )
        mc[key]["routes"][route] = dict(
            payload=payload,
            payload_sha256=P.digest(payload),
            backend="union_v6",
            scope_execution_hash=V.scope_hash(
                ids, aux, "union_v6", machine["execution_code_sha256"]
            ),
            status=(
                "operator_initial_registered"
                if sid in r["scopes"]
                else "verified_membership_carried"
            ),
        )
        ac[key]["routes"][route] = dict(
            payload=aux,
            payload_sha256=P.digest(aux),
            actual_response_evidence=[],
            local_metrics=None,
            inherited_from=old.get("inherited_from"),
            initial_binding=dict(
                operator_receipt=AUTHORITY,
                research_batch_sha256=J.RESEARCH_RESULT,
                source_scope=sid,
                source_bundle_sha256=parent["bundle_sha256"],
                comparison_result_required=False,
                response_evidence_role="typed_fixture_not_actual_comparison",
            ),
        )
        prior = G.load(data_root, current[sid])
        projector = G.projector(prior["input_version"])
        custom = (
            prior["prompt"]
            != projector.PROMPT + projector.ARM_SUFFIXES[prior["base_arm"]]
        )
        bindings[sid] = G.register(
            data_root,
            G.definition(
                prior["base_arm"],
                input_version=A.VERSION,
                prompt=prior["prompt"] if custom else None,
                hypothesis=prior["hypothesis"],
                development_keys=prior["development_keys"],
            ),
        )
    receipts = (
        machine["source_receipts"]
        + r["source_receipts"]
        + I.lineage_sources(
            data_root, parent, I.current(data_root, parent, day=publication)
        )
    )
    for ident in sorted(set(bindings.values()) | set(current.values())):
        path = G.directory(data_root) / (ident + ".json")
        receipts.append(dict(path=str(path.resolve()), sha256=P.file_hash(path)))
    issued = P.seal(
        dict(
            machine,
            cells=list(mc.values()),
            status="completed",
            adoption_basis="operator_designated",
            comparison_complete=False,
            comparison_state="incomplete",
            scope_pending=[],
            membership_status="registered",
            registration_state="registered",
            source_receipts=receipts,
        )
    )
    auxiliary = P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=day,
            target_date=day,
            publication_date=publication,
            status="completed",
            cells=list(ac.values()),
            machine_report_sha256=issued["artifact_content_sha256"],
            parent_bundle_sha256=parent["bundle_sha256"],
            source_receipts=receipts,
            auxiliary_registry_bindings=bindings,
            auxiliary_reader_code_hashes=I.code_hashes(),
            adoption_basis="operator_designated",
            comparison_complete=False,
            comparison_state="incomplete",
            scope_pending=[],
            scope_census=dict(
                planned=len(V.scopes()),
                new_ready=len(V.scopes()),
                new_actual_pid_consumed=0,
                native_carried=0,
                contract_gaps=0,
            ),
            auxiliary_independent_scopes=sorted(
                I.independent_scopes(
                    data_root, parent, I.current(data_root, parent, day=publication)
                )
            ),
            initial_registration=r,
            results_sources=[],
            owner_request_census=dict(expected=0, missing=0),
            expected_owner_requests=0,
            actual_provider_calls=0,
            registration_state="registered",
            historical_research_ref=J.RESEARCH_RESULT,
            **P.AUTH,
        )
    )
    out = (
        Path(output_directory)
        if output_directory is not None
        else Path(data_root)
        / "report/continuous_reversal_operating/registrations"
        / r["artifact_content_sha256"]
        / "publication"
    )
    P.write(out / "machine-comparison.json", issued)
    P.write(out / "machine.json", issued)
    P.write(out / "auxiliary.json", auxiliary)
    if publish_policy:
        import subprocess

        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        V.stage(
            data_root,
            day,
            publication,
            issued,
            auxiliary,
            target_date=target,
            release_commit=commit,
        )
    return auxiliary


def run_postclose(data_root, day, publication, mode):
    """Publish through the native stage owner without cloning/calling AI ledgers."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O

    r = validate_request(N._read(pending_path(data_root)))
    if day != publication or r["publication_date"] != publication:
        raise ValueError("joint_registration_publication_date_changed")
    parent = load_offline_parent(data_root, publication)
    if pending(data_root, parent, r["target_date"]) is None:
        raise ValueError("joint_registration_already_consumed")
    if mode not in {"machine", "auxiliary"}:
        return dict(
            status="initial_registration_no_new_provider_requests",
            actual_provider_calls=0,
            comparison_complete=False,
            actual_order_submitted=False,
        )
    out = (
        Path(data_root)
        / "report/continuous_reversal_operating/registrations"
        / r["artifact_content_sha256"]
        / "publication"
    )
    if mode == "machine":
        f = parent["continuous_reversal"]
        source = (
            N.root(Path(data_root))
            / "sources"
            / ("reversal-" + f["machine_report_sha256"] + ".json")
        )
        if P.file_hash(source) != f["report_file_sha256"]["machine"]:
            raise ValueError("joint_parent_machine_source_changed")
        machine = P.seal(
            dict(
                schema=O.SCHEMA,
                source_date=day,
                target_date=day,
                publication_date=publication,
                status="completed",
                parent_bundle_sha256=parent["bundle_sha256"],
                registration_change=r,
                operating_manifest=V.detector_manifest(
                    parent, effective_date=r["target_date"], changes=r
                ),
                execution_code_sha256=P.digest(
                    {
                        Path(m.__file__).name: P.file_hash(m.__file__)
                        for m in V.contract_modules()
                    }
                ),
                source_manifest_sha256=f["source_manifest_sha256"],
                source_receipts=[
                    dict(path=str(source.resolve()), sha256=P.file_hash(source))
                ],
                selection_basis="cumulative_raw_win_fraction",
                comparison_complete=False,
                historical_research_ref=J.RESEARCH_RESULT,
                **P.AUTH,
            )
        )
        initial_reports(
            data_root,
            day,
            publication,
            parent,
            machine,
            output_directory=out,
            publish_policy=False,
        )
        issued = N._read(out / "machine.json")
        for path in (
            O.directory(data_root, day) / "machine-comparison.json",
            O.directory(data_root, day) / "machine.json",
            P.directory(data_root, day) / "machine.json",
            Path(data_root)
            / "report/ai_decision_action_outcome_calibration"
            / f"winrate_policy_{day}.json",
        ):
            P.write(path, issued)
        P.write(
            Path(data_root)
            / "report/ai_decision_action_outcome_calibration"
            / f"winrate_policy_terminal_{day}.json",
            P.seal(
                dict(
                    schema=O.SCHEMA,
                    source_date=day,
                    target_date=day,
                    status="completed",
                    report_sha256=issued["artifact_content_sha256"],
                    selection_basis=issued["selection_basis"],
                    disposition="continuous_reversal_selected",
                    staged=dict(status="machine_component_prepared"),
                    **P.AUTH,
                )
            ),
        )
        return issued
    issued = N._read(out / "machine.json")
    aux = N._read(out / "auxiliary.json")
    if (
        issued.get("registration_change") != r
        or aux["machine_report_sha256"] != issued["artifact_content_sha256"]
    ):
        raise ValueError("joint_native_stage_generation_changed")
    import subprocess

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    bundle = V.stage(
        data_root,
        day,
        publication,
        issued,
        aux,
        target_date=r["target_date"],
        release_commit=commit,
    )
    for path in (
        O.directory(data_root, day) / "auxiliary.json",
        P.directory(data_root, day) / "auxiliary.json",
    ):
        P.write(path, aux)
    P.write(
        Path(data_root)
        / "report/ai_entry_setup_paired_replay_batch"
        / f"compact_auxiliary_paired_economic_{day}.json",
        P.seal(
            dict(
                aux,
                staged=dict(
                    status="prepared",
                    bundle_sha256=bundle["bundle_sha256"],
                    target_date=bundle["target_date"],
                ),
            )
        ),
    )
    return dict(
        aux, staged=dict(status="prepared", bundle_sha256=bundle["bundle_sha256"])
    )


def main(argv=None):
    import argparse
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--publication", required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--parity", type=Path, required=True)
    p.add_argument("--origin-root", type=Path, required=True)
    p.add_argument("--origin-commit", required=True)
    p.add_argument("--confirm", required=True)
    a = p.parse_args(argv)
    parent = V._attested_activation_parent(
        a.data_root,
        a.publication,
        origin_root=a.origin_root,
        origin_commit=a.origin_commit,
    )
    print(
        json.dumps(
            intake(
                a.data_root,
                a.evidence,
                a.parity,
                parent=parent,
                publication=a.publication,
                target_date=N.next_target(a.publication),
                origin_root=a.origin_root,
                origin_commit=a.origin_commit,
                confirm=a.confirm,
            )
        )
    )


if __name__ == "__main__":
    main()
