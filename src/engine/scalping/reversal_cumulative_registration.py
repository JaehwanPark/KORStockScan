"""Explicit intake and fixed-variant selection; preparing grants no live authority."""

from __future__ import annotations

import copy
import fcntl
import json
import hashlib
import re
from datetime import date
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from src.engine.scalping import reversal_cumulative_catalog as Q
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N

SCHEMA = "main_cumulative_registration_request_v2"
PREPARED = "main_cumulative_registration_prepared_v2"
AUTHORITY = "APPROVED_CUMULATIVE_POLICY_REGISTRATION_V2"
SELECTION_AUTHORITY = "APPROVED_FIXED_CUMULATIVE_VARIANT_SELECTION_V2"


def pending_path(data_root):
    return N.root(Path(data_root)) / "cumulative-registration.json"


def groups(batch=None):
    return copy.deepcopy(Q.catalog(batch)["groups"])


@lru_cache(maxsize=2)
def _definition_hash_items(batch):
    """Derived once from the import-time hash-verified frozen catalog bytes."""
    return tuple((b, P.digest(d)) for b, d in Q.catalog(batch)["definitions"].items())


def definition_hashes(batch=None):
    # Return a fresh map so a prepared/request object cannot mutate the cache.
    return dict(_definition_hash_items(Q.catalog(batch)["research_result_sha256"]))


def _dates(publication, target):
    if (
        type(publication) is not str
        or type(target) is not str
        or date.fromisoformat(publication).isoformat() != publication
        or publication < "2026-10-15"
        or target != N.next_target(publication)
    ):
        raise ValueError("cumulative_registration_dates_invalid")


def _receipts(receipts, *, check_sources, batch=None):
    data = Q.catalog(batch)
    named = data.get(
        "evidence_names",
        dict(result="result-reviewed.json", manifest="frozen-manifest.json"),
    )
    names = {
        named["result"],
        named["manifest"],
        "validation.json",
        "native-parity.json",
        "baseline-bundle.json",
    }
    if (
        not isinstance(receipts, list)
        or len(receipts) != len(names)
        or {r.get("name") for r in receipts if isinstance(r, dict)} != names
    ):
        raise ValueError("cumulative_registration_receipts_invalid")
    for r in receipts:
        if (
            not isinstance(r.get("path"), str)
            or not Path(r["path"]).is_absolute()
            or not re.fullmatch("[0-9a-f]{64}", str(r.get("sha256", "")))
        ):
            raise ValueError("cumulative_registration_receipts_invalid")
        expected = {
            named["result"]: data["research_result_sha256"],
            named["manifest"]: data["research_manifest_sha256"],
        }.get(r["name"])
        if expected and r["sha256"] != expected:
            raise ValueError("cumulative_research_changed")
        if check_sources and P.file_hash(r["path"]) != r["sha256"]:
            raise ValueError("cumulative_registration_evidence_changed")


def _archive(source, directory):
    """Bounded, content-addressed copy; never overwrite a prior evidence object."""
    source = Path(source)
    if source.stat().st_size > 16 * 1024**2:
        raise ValueError("cumulative_archive_budget_exceeded")
    content = source.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    if P.file_hash(source) != sha:
        raise ValueError("cumulative_source_changed_during_archive")
    dest = Path(directory) / (sha + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with dest.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        pass
    if P.file_hash(dest) != sha:
        raise ValueError("cumulative_archive_conflict")
    return dict(path=str(dest.resolve()), sha256=sha, name=source.name)


def counts(metric):
    source = metric.get("counts", metric)
    names = ("WIN", "FAIL_STOP", "FAIL_TIMEOUT", "UNRESOLVED")
    if any(type(source.get(k, 0)) is not int or source.get(k, 0) < 0 for k in names):
        raise ValueError("cumulative_counts_invalid")
    w = source.get("WIN", 0)
    n = w + source.get("FAIL_STOP", 0) + source.get("FAIL_TIMEOUT", 0)
    return w, n


def select_variant(group, current, metrics, *, authority):
    if authority != SELECTION_AUTHORITY:
        raise ValueError("cumulative_selection_not_delegated")
    variants = dict(group["alternatives"], CURRENT_NATIVE=sorted(current))
    baseline = metrics.get("CURRENT_NATIVE") or {}
    cohort = baseline.get("source_universe_sha256")
    usable = []
    for name, ids in variants.items():
        m = metrics.get(name) or {}
        w, n = counts(m)
        if (
            not n
            or not cohort
            or m.get("source_universe_sha256") != cohort
            or m.get("source_complete") is not True
            or m.get("comparison_complete") is not True
        ):
            continue
        usable.append(dict(name=name, ids=ids, w=w, n=n))
    old = next((x for x in usable if x["name"] == "CURRENT_NATIVE"), None)
    if old is None:
        return dict(branch_ids=sorted(current), status="comparison_incomplete_carry")
    best = max((Fraction(x["w"], x["n"]), x["w"]) for x in usable)
    ties = [x for x in usable if (Fraction(x["w"], x["n"]), x["w"]) == best]
    winner = min(
        ties,
        key=lambda x: (
            "CURRENT_NATIVE" if x["ids"] == sorted(current) else x["name"],
            x["name"] != "CURRENT_NATIVE",
            x["name"],
        ),
    )
    improved = (
        best[0] > Fraction(old["w"], old["n"])
        or best[0] == Fraction(old["w"], old["n"])
        and best[1] > old["w"]
    )
    if not improved:
        winner = old
    return dict(
        branch_ids=winner["ids"],
        variant=winner["name"],
        status="selected" if winner["ids"] != sorted(current) else "carried",
        wins=winner["w"],
        resolved=winner["n"],
    )


def validate_request(request, *, check_sources=True):
    if not isinstance(request, dict):
        raise ValueError("cumulative_registration_request_invalid")
    batch = request.get("research_batch_sha256")
    data = Q.catalog(batch)
    _dates(request.get("publication_date"), request.get("target_date"))
    if (
        request.get("schema") != SCHEMA
        or request.get("artifact_content_sha256")
        != P.seal(request)["artifact_content_sha256"]
        or request.get("operator_receipt") != AUTHORITY
        or request.get("kind") != "REPLACE"
        or request.get("research_batch_sha256") != data["research_result_sha256"]
        or request.get("registry_sha256") != Q.registry(batch)
        or request.get("definition_hashes") != definition_hashes(batch)
        or request.get("variant_groups") != data["groups"]
        or request.get("selection_authority") != SELECTION_AUTHORITY
        or request.get("comparison_result_required") is not False
        or request.get("parent_bundle_sha256") != Q.PARENT
        or not request.get("source_receipts")
    ):
        raise ValueError("cumulative_registration_authority_or_definition_invalid")
    memberships = request.get("initial_memberships") or {}
    if (
        not isinstance(memberships, dict)
        or set(memberships) != set(data["groups"])
        or not isinstance(request.get("scopes"), dict)
    ):
        raise ValueError("cumulative_initial_scope_invalid")
    for sid, ids in memberships.items():
        if ids != Q.membership(sid, data["recommendations"][sid], batch):
            raise ValueError("cumulative_initial_variant_invalid")
        base = set(data["groups"][sid]["baseline"])
        if request["scopes"].get(sid) != dict(
            remove=sorted(base - set(ids)), add=sorted(set(ids) - base)
        ):
            raise ValueError("cumulative_initial_delta_invalid")
    if set(request["scopes"]) != set(memberships):
        raise ValueError("cumulative_delta_scope_invalid")
    if (
        any(request.get(k) != v for k, v in P.AUTH.items())
        or not isinstance(request.get("contract_file_sha256"), dict)
        or not request["contract_file_sha256"]
    ):
        raise ValueError("cumulative_registration_contract_missing")
    _receipts(request["source_receipts"], check_sources=check_sources, batch=batch)
    return request


def approval(manifest):
    entries = manifest.get("registration_receipts", []) + [
        manifest.get("change_receipt") or {}
    ]
    return next(
        (
            x
            for x in reversed(entries)
            if x.get("schema") == SCHEMA and x.get("operator_receipt") == AUTHORITY
        ),
        None,
    )


def pending(data_root, parent, target_date):
    path = pending_path(data_root)
    if not path.exists():
        return None
    request = validate_request(N._read(path))
    m = parent["continuous_reversal"].get("operating_manifest", {})
    if any(
        x.get("artifact_content_sha256") == request["artifact_content_sha256"]
        for x in m.get("registration_receipts", []) + [m.get("change_receipt") or {}]
    ):
        return None
    if (
        request["parent_bundle_sha256"] != parent["bundle_sha256"]
        or request["target_date"] != target_date
    ):
        raise ValueError("cumulative_registration_parent_or_date_changed")
    return request


def consumed(data_root, request):
    """Read-only CLI routing check before opening the original code transition."""
    root = N.root(Path(data_root))
    pointer = root / "current.json"
    if not pointer.exists():
        return False
    ident = N._read(pointer).get("bundle_sha256")
    if not re.fullmatch("[0-9a-f]{64}", str(ident)):
        raise ValueError("cumulative_current_pointer_invalid")
    current = N._read(root / "generations" / (ident + ".json"))
    N.validate(current, target_date=current["target_date"])
    if current["bundle_sha256"] != ident:
        raise ValueError("cumulative_current_pointer_changed")
    m = current.get("continuous_reversal", {}).get("operating_manifest", {})
    return any(
        r.get("artifact_content_sha256") == request["artifact_content_sha256"]
        for r in m.get("registration_receipts", []) + [m.get("change_receipt") or {}]
    )


def prepare(
    evidence_root,
    output,
    *,
    parent,
    parity_path,
    publication,
    target_date,
    research_batch=None,
):
    """Immutable deploy-wait package. Does not write a pending request or policy."""
    evidence_root, output = Path(evidence_root), Path(output)
    data = Q.catalog(research_batch)
    batch = data["research_result_sha256"]
    _dates(publication, target_date)
    if parent["bundle_sha256"] != Q.PARENT:
        raise ValueError("cumulative_research_parent_changed_recomparison_required")
    named = data.get(
        "evidence_names",
        dict(result="result-reviewed.json", manifest="frozen-manifest.json"),
    )
    result_path = evidence_root / named["result"]
    manifest_path = evidence_root / named["manifest"]
    if (
        P.file_hash(result_path) != batch
        or P.file_hash(manifest_path) != data["research_manifest_sha256"]
    ):
        raise ValueError("cumulative_research_changed")
    frozen = json.loads(manifest_path.read_text())
    baseline_path = evidence_root / "baseline-bundle.json"
    if not baseline_path.exists():
        paths = [
            Path(k)
            for k in frozen["source_seals"]
            if Path(k).name == "baseline-bundle.json"
        ]
        if len(paths) != 1:
            raise ValueError("cumulative_frozen_parent_missing")
        baseline_path = paths[0]
    baseline_hashes = {
        v
        for k, v in frozen["source_seals"].items()
        if Path(k).name == "baseline-bundle.json"
    }
    if (
        baseline_hashes != {P.file_hash(baseline_path)}
        or N._read(baseline_path) != parent
    ):
        raise ValueError("cumulative_frozen_parent_changed")
    N.validate(parent, target_date=parent["target_date"])
    result = json.loads(result_path.read_text())
    parity = json.loads(Path(parity_path).read_text())
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    if (
        parity.get("status") != "pass"
        or type(parity.get("mismatches")) is not int
        or parity["mismatches"] != 0
        or parity.get("partition_count") != len(frozen["partitions"])
        or parity.get("reference_result_sha256") != batch
        or parity.get("parent_bundle_sha256") != Q.PARENT
        or parity.get("definition_catalog_sha256") != Q.registry(batch)
        or parity.get("contract_file_sha256") != code
    ):
        raise ValueError("cumulative_native_parity_invalid")
    if json.loads(baseline_path.read_text()).get("bundle_sha256") != Q.PARENT:
        raise ValueError("cumulative_frozen_parent_changed")
    memberships = {}
    deltas = {}
    for sid, g in data["groups"].items():
        key, route = sid.rsplit("|", 1)
        actual = sorted(
            b["branch_id"]
            for b in parent["continuous_reversal"]["machine_cells"][key]["routes"][
                route
            ]["payload"]["branches"]
        )
        if actual != g["baseline"]:
            raise ValueError("cumulative_scope_parent_changed")
        variant = result["scopes"][sid]["recommendation"]["variant"]
        if variant != data["recommendations"][sid]:
            raise ValueError("cumulative_recommendation_changed")
        ids = Q.membership(sid, variant, batch)
        memberships[sid] = ids
        deltas[sid] = dict(
            remove=sorted(set(actual) - set(ids)), add=sorted(set(ids) - set(actual))
        )
    archive = output / "evidence"
    archive.mkdir(parents=True, exist_ok=True)
    receipts = []
    for path in [
        result_path,
        manifest_path,
        evidence_root / "validation.json",
        Path(parity_path),
        baseline_path,
    ]:
        receipts.append(_archive(path, archive))
    prepared = P.seal(
        dict(
            schema=PREPARED,
            status="prepared_waiting_deployment",
            parent_bundle_sha256=Q.PARENT,
            research_batch_sha256=batch,
            registry_sha256=Q.registry(batch),
            publication_date=publication,
            target_date=target_date,
            initial_memberships=memberships,
            scopes=deltas,
            variant_groups=groups(batch),
            source_receipts=receipts,
            definition_hashes=definition_hashes(batch),
            selection_authority=SELECTION_AUTHORITY,
            operator_receipt=None,
            comparison_result_required=False,
            contract_file_sha256=code,
            **P.AUTH,
        )
    )
    destination = output / "prepared-registration.json"
    if destination.exists() and N._read(destination) != prepared:
        raise ValueError("cumulative_prepared_package_conflict")
    P.write(destination, prepared)
    return prepared


def intake(data_root, prepared_path, *, confirm, origin_root, origin_commit):
    if confirm != AUTHORITY:
        raise ValueError("cumulative_explicit_registration_authority_required")
    p = N._read(Path(prepared_path))
    if (
        p.get("schema") != PREPARED
        or p.get("artifact_content_sha256") != P.seal(p)["artifact_content_sha256"]
    ):
        raise ValueError("cumulative_prepared_package_invalid")
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    if (
        p.get("status") != "prepared_waiting_deployment"
        or p.get("operator_receipt") is not None
        or any(p.get(k) != v for k, v in P.AUTH.items())
        or p.get("contract_file_sha256")
        != {
            Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
        }
    ):
        raise ValueError("cumulative_prepared_code_or_authority_changed")
    # Validate the complete proposed request before creating any runtime path.
    proposed = P.seal(dict(p, schema=SCHEMA, kind="REPLACE", operator_receipt=confirm))
    validate_request(proposed)
    actual = V._attested_activation_parent(
        data_root,
        p["publication_date"],
        origin_root=origin_root,
        origin_commit=origin_commit,
    )
    if actual["bundle_sha256"] != p["parent_bundle_sha256"]:
        raise ValueError("cumulative_intake_parent_cas_failed")
    root = N.root(Path(data_root))
    root.mkdir(parents=True, exist_ok=True)
    with (root / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if N._read(root / "current.json")["bundle_sha256"] != p["parent_bundle_sha256"]:
            raise ValueError("cumulative_intake_parent_cas_failed")
        m = actual.get("continuous_reversal", {}).get("operating_manifest", {})
        consumed_hashes = {
            r["artifact_content_sha256"]
            for r in m.get("registration_receipts", [])
            + [m.get("change_receipt") or {}]
            if r.get("artifact_content_sha256")
        }
        for name in (
            "extended-registration.json",
            "residual-registration.json",
            "joint-registration.json",
        ):
            other_path = root / name
            if other_path.exists():
                other = N._read(other_path)
                if (
                    other.get("parent_bundle_sha256") == p["parent_bundle_sha256"]
                    and other.get("artifact_content_sha256") not in consumed_hashes
                ):
                    raise ValueError("cumulative_other_registration_pending:" + name)
        batch = p["research_batch_sha256"]
        archive = (
            Path(data_root)
            / "report/continuous_reversal_operating/registrations"
            / batch
        )
        archive.mkdir(parents=True, exist_ok=True)
        receipts = []
        for receipt in p["source_receipts"]:
            source = Path(receipt["path"])
            if P.file_hash(source) != receipt["sha256"]:
                raise ValueError("cumulative_prepared_evidence_changed")
            copied = _archive(source, archive)
            if copied["sha256"] != receipt["sha256"]:
                raise ValueError("cumulative_prepared_evidence_changed")
            receipts.append(dict(copied, name=receipt["name"]))
        request = P.seal(
            dict(
                schema=SCHEMA,
                kind="REPLACE",
                operator_receipt=confirm,
                parent_bundle_sha256=p["parent_bundle_sha256"],
                research_batch_sha256=batch,
                registry_sha256=p["registry_sha256"],
                scopes=p["scopes"],
                initial_memberships=p["initial_memberships"],
                variant_groups=p["variant_groups"],
                selection_authority=SELECTION_AUTHORITY,
                definition_hashes=p["definition_hashes"],
                source_receipts=receipts,
                contract_file_sha256=p["contract_file_sha256"],
                publication_date=p["publication_date"],
                target_date=p["target_date"],
                activation_parent_origin=dict(
                    root=str(Path(origin_root).resolve()), commit=origin_commit
                ),
                comparison_result_required=False,
                **P.AUTH,
            )
        )
        validate_request(request)
        path = pending_path(data_root)
        if path.exists() and N._read(path) != request:
            raise ValueError("cumulative_pending_request_conflict")
        P.write(archive / (request["artifact_content_sha256"] + ".json"), request)
        P.write(path, request)
        return request


def apply_selection(machine, parent):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    manifest = copy.deepcopy(machine["operating_manifest"])
    registered = manifest.get("cumulative_variant_groups")
    if not registered:
        return machine
    current = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    chosen = {}
    complete = machine.get("status") == "completed" and bool(
        machine.get("source_manifest_receipt")
    )
    batch = approval(manifest)["research_batch_sha256"]
    for sid, g in registered.items():
        cohort = P.digest(
            [machine["source_manifest_sha256"], sid, machine["label_contract"]]
        )
        alternatives = Q.variants(sid, batch)
        metrics = {
            name: dict(
                machine["proposal_metrics"].get(sid + "::" + name) or {},
                source_universe_sha256=cohort,
                source_complete=complete,
                comparison_complete=complete,
            )
            for name in (*alternatives, "CURRENT_NATIVE")
        }
        chosen[sid] = select_variant(
            dict(alternatives=alternatives),
            current[sid],
            metrics,
            authority=manifest.get("cumulative_selection_authority"),
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
    manifest["cumulative_selection_receipt"] = P.seal(
        dict(
            schema="cumulative_variant_selection_v2",
            authority=SELECTION_AUTHORITY,
            parent_bundle_sha256=parent["bundle_sha256"],
            source_manifest_sha256=machine["source_manifest_sha256"],
            selected=chosen,
            memberships={s: manifest["scopes"][s] for s in registered},
        )
    )
    return P.seal(
        dict(
            machine,
            operating_manifest=manifest,
            cumulative_selection=chosen,
            variant_selection_basis="cumulative_target_first_win_fraction",
        )
    )


def validate_manifest(manifest):
    registered = manifest.get("cumulative_variant_groups")
    if not registered:
        if any(b in Q.DEFINITIONS for b in manifest["definitions"]):
            raise ValueError("cumulative_membership_authority_missing")
        return False
    request = approval(manifest)
    if not request:
        raise ValueError("cumulative_membership_authority_missing")
    validate_request(request, check_sources=False)
    batch = request["research_batch_sha256"]
    if (
        registered != Q.catalog(batch)["groups"]
        or manifest.get("cumulative_selection_authority") != SELECTION_AUTHORITY
    ):
        raise ValueError("cumulative_variant_authority_changed")
    receipt = manifest.get("cumulative_selection_receipt")
    if receipt and (
        receipt.get("artifact_content_sha256")
        != P.seal(receipt)["artifact_content_sha256"]
        or receipt.get("authority") != SELECTION_AUTHORITY
        or not re.fullmatch(
            "[0-9a-f]{64}", str(receipt.get("parent_bundle_sha256", ""))
        )
        or not re.fullmatch(
            "[0-9a-f]{64}", str(receipt.get("source_manifest_sha256", ""))
        )
        or set(receipt.get("selected", {})) != set(registered)
        or receipt.get("memberships") != {s: manifest["scopes"][s] for s in registered}
    ):
        raise ValueError("cumulative_selection_receipt_invalid")
    for sid in registered:
        ids = manifest["scopes"][sid]
        if not Q.valid_membership(sid, ids, batch):
            raise ValueError("cumulative_unapproved_membership")
        if receipt and receipt["selected"][sid].get("branch_ids") != ids:
            raise ValueError("cumulative_selection_membership_changed")
        if not receipt and ids != request["initial_memberships"][sid]:
            raise ValueError("cumulative_selection_receipt_missing")
    return True


def load_offline_parent(data_root, publication):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    request = validate_request(N._read(pending_path(data_root)))
    if request["publication_date"] != publication:
        raise ValueError("cumulative_publication_date_changed")
    origin = request["activation_parent_origin"]
    parent = V._attested_activation_parent(
        data_root,
        publication,
        origin_root=origin["root"],
        origin_commit=origin["commit"],
    )
    if parent["bundle_sha256"] != request["parent_bundle_sha256"]:
        raise ValueError("cumulative_offline_parent_changed")
    return parent


def run_postclose(data_root, day, publication, mode, *, source=None):
    from src.engine.scalping import reversal_cumulative_postclose as O

    request = validate_request(N._read(pending_path(data_root)))
    parent = load_offline_parent(data_root, publication)
    if pending(data_root, parent, request["target_date"]) is None:
        raise ValueError("cumulative_registration_already_consumed")
    if mode == "machine":
        return O.build(data_root, day, publication, parent, source=source)
    if mode in {"prepare-inputs", "calls"}:
        return dict(
            status="initial_registration_compatible_auxiliary_carry",
            actual_provider_calls=0,
            comparison_complete=False,
            runtime_effect=False,
            actual_order_submitted=False,
        )
    if mode != "auxiliary":
        raise ValueError("cumulative_postclose_mode_invalid")
    from src.engine.scalping.continuous_reversal_operating_postclose import directory

    machine = N._read(directory(data_root, day) / "machine-comparison.json")
    return O.initial_reports(data_root, day, publication, parent, machine)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    prep = sub.add_parser("prepare")
    for name in ("evidence-root", "output", "parent", "parity"):
        prep.add_argument("--" + name, type=Path, required=True)
    prep.add_argument("--publication-date", required=True)
    prep.add_argument("--target-date", required=True)
    prep.add_argument("--research-batch-sha256", default=Q.RESEARCH_RESULT)
    adopt = sub.add_parser("intake")
    for name in ("data-root", "prepared", "origin-root"):
        adopt.add_argument("--" + name, type=Path, required=True)
    adopt.add_argument("--origin-commit", required=True)
    adopt.add_argument("--confirm", required=True)
    args = parser.parse_args(argv)
    if args.operation == "prepare":
        result = prepare(
            args.evidence_root,
            args.output,
            parent=N._read(args.parent),
            parity_path=args.parity,
            publication=args.publication_date,
            target_date=args.target_date,
            research_batch=args.research_batch_sha256,
        )
    else:
        result = intake(
            args.data_root,
            args.prepared,
            confirm=args.confirm,
            origin_root=args.origin_root,
            origin_commit=args.origin_commit,
        )
    print(
        json.dumps(
            dict(
                status=result.get("status", "registered_pending"),
                artifact_content_sha256=result["artifact_content_sha256"],
                actual_order_submitted=False,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
