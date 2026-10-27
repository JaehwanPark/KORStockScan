"""Explicit intake and fixed-variant selection; preparing grants no live authority."""

from __future__ import annotations

import copy
import fcntl
import json
import hashlib
import re
import math
from contextlib import contextmanager
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


SCORING_SCHEMA = "cumulative_scoring_contract_v1"
SCORING_AUTHORITY = "APPROVED_REGULAR_NONFIXED_CHRONOLOGICAL_WILSON_V1"
SCORE_VERSION = "chronological_target_first_wilson_v1"
SCOPED_METRIC = "scope_bound_chronological_wilson_and_raw_fraction"
SOURCE_FIRST = "verified_native_source_before_machine_v1"
SCORING_INTENT_SCHEMA = "cumulative_source_first_scoring_intent_v1"
SCORE_Z = 1.959963984540054
STATISTICAL_WINDOW = 1800
SCORING_ALIASES = {
    "other_non_fixed|REGULAR|LT_20000|SOR": ("A05", "A09"),
    "other_non_fixed|REGULAR|20000_TO_100000|SOR": ("A08",),
    "other_non_fixed|REGULAR|GE_100000|SOR": ("A12", "A14"),
}


def scoring_spec():
    return dict(
        version=SCORE_VERSION,
        z=SCORE_Z,
        seconds=STATISTICAL_WINDOW,
        unit="first_confirmation_per_day_symbol_route",
        unresolved_occupies_window=True,
        label_contract=C.LABEL,
    )


def selection_metadata(report):
    """One producer/consumer identity for raw and scope-bound selections."""
    manifest = report.get("operating_manifest") or {}
    if not isinstance(manifest, dict):
        raise ValueError("cumulative_selection_manifest_invalid")
    contract = report.get("scoring_contract")
    scoped = manifest.get("cumulative_scoring_contract")
    if contract is None and scoped is None:
        if report.get("primary_decision_metric") not in (
            None, "cost_bound_cumulative_target_first_fraction", "cumulative_raw_win_fraction"
        ):
            raise ValueError("cumulative_selection_metric_unknown")
        return dict(selection_basis="cumulative_raw_win_fraction")
    if (
        not isinstance(contract, dict) or scoped != contract
        or report.get("primary_decision_metric") != SCOPED_METRIC
        or report.get("statistic_contract") != scoring_spec()
        or report.get("label_contract") != C.LABEL
        or report.get("publication_date") != report.get("source_date")
        or report.get("publication_date", "") < contract.get("publication_date", "")
        or report.get("scope_decision_metrics") != {
            sid: SCORE_VERSION for sid in contract.get("scopes", {})
        }
    ):
        raise ValueError("cumulative_selection_metric_binding_invalid")
    validate_scoring(contract)
    if not validate_manifest(manifest):
        raise ValueError("cumulative_selection_manifest_missing")
    receipt = manifest["cumulative_selection_receipt"]
    if (
        receipt.get("parent_bundle_sha256") != report.get("parent_bundle_sha256")
        or receipt.get("source_manifest_sha256") != report.get("source_manifest_sha256")
        or report["publication_date"] == contract["publication_date"] and (
            contract["parent_bundle_sha256"] != report.get("parent_bundle_sha256")
            or contract["source_manifest_sha256"] != report.get("source_manifest_sha256")
        )
    ):
        raise ValueError("cumulative_selection_report_binding_invalid")
    return dict(
        selection_basis=SCOPED_METRIC,
        scoring_contract_sha256=contract["artifact_content_sha256"],
        statistic_contract_sha256=P.digest(scoring_spec()),
    )


@contextmanager
def _before_machine(data_root, day):
    """Serialize intake with the existing native machine-stage writer."""
    from src.engine.automation import postclose_summary_handoff as H
    from src.engine.scalping import continuous_reversal_operating_postclose as O

    stage = H.stage_path(Path(data_root) / "report", day, "main_machine_policy")
    stage.parent.mkdir(parents=True, exist_ok=True)
    with stage.with_suffix(".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("cumulative_scoring_machine_stage_active") from exc
        if stage.exists() or any(path.exists() for path in (
            O.directory(data_root, day) / "machine-comparison.json",
            O.directory(data_root, day) / "machine.json",
            Path(data_root) / "report/ai_decision_action_outcome_calibration" / f"winrate_policy_{day}.json",
        )):
            raise ValueError("cumulative_scoring_machine_stage_already_started")
        yield


def _preparation_inputs(data_root, day):
    from src.engine.automation import postclose_summary_handoff as H

    data_root = Path(data_root)
    eod = data_root / "runtime/update_kospi_status" / f"update_kospi_{day}.json"
    if not H._eod_source_valid(H._load_json(eod), day):
        raise ValueError("cumulative_scoring_eod_source_invalid")
    issue = H._machine_source_preflight_issue(data_root / "report", day)
    if issue:
        raise ValueError("cumulative_scoring_preflight_invalid:" + issue)
    audit = data_root / "report/observation_source_quality_audit" / f"observation_source_quality_audit_{day}.json"
    return {
        name: dict(path=str(path.resolve()), sha256=P.file_hash(path))
        for name, path in (
            ("eod", eod), ("preflight", audit),
            ("preflight_binding", Path(str(audit) + ".final-contract.json")),
        )
    }


def _verify_preparation_inputs(data_root, request):
    from src.engine.automation import postclose_summary_handoff as H

    if request.get("preparation_basis") != SOURCE_FIRST:
        raise ValueError("cumulative_scoring_source_first_preparation_required")
    if request.get("preparation_reader_code_sha256") != P.file_hash(H.__file__):
        raise ValueError("cumulative_scoring_preparation_reader_changed")
    if _preparation_inputs(data_root, request["publication_date"]) != request.get("preparation_inputs"):
        raise ValueError("cumulative_scoring_preparation_inputs_changed")
    receipt = request["native_source_manifest_receipt"]
    source = P.ensure_population(
        data_root, request["publication_date"],
        source_generation=receipt.get("source_generation"),
        expected_sha256=request["source_manifest_sha256"],
    )
    if P.population_receipt(source) != receipt:
        raise ValueError("cumulative_scoring_prepared_source_changed")


def wilson_score(w, n):
    if type(w) is not int or type(n) is not int or not 0 <= w <= n:
        raise ValueError("cumulative_counts_invalid")
    if not n:
        return None
    p, z = w / n, SCORE_Z
    return (
        p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    ) / (1 + z * z / n)


def validate_scoring(contract, *, approved=True, check_sources=False):
    if not isinstance(contract, dict) or (
        contract.get("schema") != SCORING_SCHEMA
        or contract.get("artifact_content_sha256")
        != P.seal(contract)["artifact_content_sha256"]
        or contract.get("spec") != scoring_spec()
        or contract.get("operator_receipt") != (SCORING_AUTHORITY if approved else None)
        or not isinstance(contract.get("scopes"), dict)
        or not contract.get("scopes")
        or not set(contract.get("scopes", {})) <= set(SCORING_ALIASES)
        or any(contract.get(k) != v for k, v in P.AUTH.items())
    ):
        raise ValueError("cumulative_scoring_contract_invalid")
    _dates(contract.get("publication_date"), contract.get("target_date"))
    for name in ("parent_bundle_sha256", "source_manifest_sha256", "registry_sha256"):
        if not re.fullmatch("[0-9a-f]{64}", str(contract.get(name, ""))):
            raise ValueError("cumulative_scoring_binding_invalid")
    batch = contract.get("research_batch_sha256")
    catalog = Q.catalog(batch)
    if contract["registry_sha256"] != Q.registry(batch):
        raise ValueError("cumulative_scoring_registry_changed")
    scoped_carry = contract.get("unscored_scope_policy") == "carry_parent"
    if contract.get("unscored_scope_policy") not in (None, "carry_parent"):
        raise ValueError("cumulative_scoring_unscored_policy_invalid")
    if set(contract["scopes"]) != set(SCORING_ALIASES) and not scoped_carry:
        raise ValueError("cumulative_scoring_partial_scope_requires_carry")
    if scoped_carry:
        from src.engine.scalping import continuous_reversal_policy_v6 as V

        frozen = contract.get("frozen_parent_scopes")
        expected_scopes = {V.scope_id(key, route) for key, route in V.scopes()}
        if (
            not isinstance(frozen, dict)
            or set(frozen) != expected_scopes
            or any(not isinstance(ids, list) or ids != sorted(set(ids)) for ids in frozen.values())
        ):
            raise ValueError("cumulative_scoring_frozen_parent_invalid")
    for sid, cfg in contract["scopes"].items():
        aliases = SCORING_ALIASES[sid]
        base = cfg.get("parent_branch_ids", [])
        expected = {
            "ADD_" + a: sorted(set(base) | {catalog["groups"][sid]["additions"][a]})
            for a in aliases
        }
        alternatives = cfg.get("alternatives")
        if (
            not isinstance(alternatives, dict)
            or not alternatives
            or any(expected.get(name) != ids for name, ids in alternatives.items())
            or not scoped_carry and alternatives != expected
            or scoped_carry and contract["frozen_parent_scopes"][sid] != base
        ) or any(
            ids != sorted(set(ids)) or not Q.valid_membership(sid, ids, batch)
            for ids in [base, *(alternatives or {}).values()]
        ):
            raise ValueError("cumulative_scoring_membership_invalid")
    receipts = contract.get("source_receipts")
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("cumulative_scoring_source_missing")
    for r in receipts:
        if (
            not isinstance(r, dict)
            or not Path(r.get("path", "")).is_absolute()
            or not re.fullmatch("[0-9a-f]{64}", str(r.get("sha256", "")))
        ):
            raise ValueError("cumulative_scoring_source_invalid")
        if check_sources and P.file_hash(r["path"]) != r["sha256"]:
            raise ValueError("cumulative_scoring_source_changed")
    if not contract.get("contract_file_sha256"):
        raise ValueError("cumulative_scoring_code_missing")
    intent_sha = contract.get("source_first_intent_sha256")
    if intent_sha is not None and not re.fullmatch("[0-9a-f]{64}", str(intent_sha)):
        raise ValueError("cumulative_scoring_intent_binding_invalid")
    basis = contract.get("preparation_basis")
    if intent_sha is not None and basis != SOURCE_FIRST:
        raise ValueError("cumulative_scoring_source_first_preparation_required")
    if basis is not None:
        inputs = contract.get("preparation_inputs")
        receipt = contract.get("native_source_manifest_receipt")
        if (
            basis != SOURCE_FIRST or not isinstance(inputs, dict)
            or not re.fullmatch("[0-9a-f]{64}", str(contract.get("preparation_reader_code_sha256", "")))
            or set(inputs) != {"eod", "preflight", "preflight_binding"}
            or not isinstance(receipt, dict)
            or any(
                not isinstance(r, dict) or not Path(r.get("path", "")).is_absolute()
                or not re.fullmatch("[0-9a-f]{64}", str(r.get("sha256", "")))
                for r in [*inputs.values(), receipt]
            )
        ):
            raise ValueError("cumulative_scoring_source_preparation_invalid")
    return contract


def scoring_path(data_root):
    return N.root(Path(data_root)) / "cumulative-scoring.json"


def scoring_intent_path(data_root):
    return N.root(Path(data_root)) / "cumulative-scoring-intent.json"


def _validate_scoring_intent(value):
    if (
        not isinstance(value, dict) or value.get("schema") != SCORING_INTENT_SCHEMA
        or value.get("artifact_content_sha256") != P.seal(value)["artifact_content_sha256"]
        or value.get("operator_receipt") != SCORING_AUTHORITY
        or value.get("spec") != scoring_spec()
        or any(value.get(k) != v for k, v in P.AUTH.items())
    ):
        raise ValueError("cumulative_scoring_intent_invalid")
    _dates(value.get("publication_date"), value.get("target_date"))
    probe = dict(value)
    probe.update(schema=SCORING_SCHEMA, source_manifest_sha256="0" * 64,
                 source_receipts=[dict(path="/unmaterialized-source", sha256="0" * 64)])
    validate_scoring(P.seal(probe))
    origin = value.get("activation_parent_origin")
    if (
        not isinstance(origin, dict)
        or not Path(origin.get("root", "")).is_absolute()
        or not re.fullmatch("[0-9a-f]{40}", str(origin.get("commit", "")))
        or not re.fullmatch("[0-9a-f]{64}", str(value.get("preparation_reader_code_sha256", "")))
    ):
        raise ValueError("cumulative_scoring_intent_origin_missing")
    return value


def request_scoring(data_root, *, publication, scope_candidates, confirm, origin_root, origin_commit):
    """Authorize only the frozen selection recipe; source and policy stay unset."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.automation import postclose_summary_handoff as H

    if confirm != SCORING_AUTHORITY:
        raise ValueError("cumulative_scoring_explicit_authority_required")
    parent = V._attested_activation_parent(
        data_root, publication, origin_root=origin_root, origin_commit=origin_commit)
    m = parent["continuous_reversal"]["operating_manifest"]
    batch = approval(m)["research_batch_sha256"]
    catalog = Q.catalog(batch)
    if not isinstance(scope_candidates, dict) or not scope_candidates or any(
        sid not in SCORING_ALIASES or not isinstance(aliases, (tuple, list))
        or not aliases or len(aliases) != len(set(aliases))
        or not set(aliases) <= set(SCORING_ALIASES[sid])
        for sid, aliases in scope_candidates.items()
    ):
        raise ValueError("cumulative_scoring_requested_candidates_invalid")
    scopes = {sid:dict(
        parent_branch_ids=m["scopes"][sid],
        alternatives={"ADD_"+a:sorted(set(m["scopes"][sid])|{catalog["groups"][sid]["additions"][a]}) for a in aliases},
    ) for sid, aliases in scope_candidates.items()}
    intent = P.seal(dict(
        schema=SCORING_INTENT_SCHEMA, spec=scoring_spec(), operator_receipt=confirm,
        publication_date=publication, target_date=N.next_target(publication),
        parent_bundle_sha256=parent["bundle_sha256"], scopes=scopes,
        unscored_scope_policy="carry_parent", frozen_parent_scopes=m["scopes"],
        research_batch_sha256=batch, registry_sha256=Q.registry(batch),
        contract_file_sha256={Path(mod.__file__).name:P.file_hash(mod.__file__) for mod in V.contract_modules()},
        preparation_reader_code_sha256=P.file_hash(H.__file__),
        activation_parent_origin=dict(root=str(Path(origin_root).resolve()),commit=origin_commit),
        **P.AUTH,
    ))
    _validate_scoring_intent(intent)
    path = scoring_intent_path(data_root)
    with _before_machine(data_root, publication), (path.parent/"publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if N._read(path.parent/"current.json")["bundle_sha256"] != parent["bundle_sha256"]:
            raise ValueError("cumulative_scoring_parent_changed")
        if path.exists() and N._read(path) != intent:
            raise ValueError("cumulative_scoring_intent_conflict")
        P.write(path, intent)
    return intent


def fulfill_scoring(data_root, day, publication):
    """Existing wrapper admission point after preflight, before machine launch."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.automation import postclose_summary_handoff as H
    from src.engine.infrastructure import runtime_release_router as router

    path = scoring_intent_path(data_root)
    if not path.exists():
        return P.seal(dict(status="not_requested", source_date=day, **P.AUTH))
    intent = _validate_scoring_intent(N._read(path))
    if intent["publication_date"] != publication:
        return P.seal(dict(status="not_requested_for_publication",source_date=day,**P.AUTH))
    if day != publication:
        raise ValueError("cumulative_scoring_observation_publication_mismatch")
    code = {Path(mod.__file__).name:P.file_hash(mod.__file__) for mod in V.contract_modules()}
    if code != intent["contract_file_sha256"] or P.file_hash(H.__file__) != intent["preparation_reader_code_sha256"]:
        raise ValueError("cumulative_scoring_intent_code_changed")
    pending = scoring_path(data_root)
    if pending.exists():
        prior = validate_scoring(N._read(pending), check_sources=True)
        if prior.get("source_first_intent_sha256") != intent["artifact_content_sha256"]:
            raise ValueError("cumulative_scoring_request_conflict")
        return prior  # Exact resume, no new intake or source refresh.
    root = Path(__file__).resolve().parents[3]
    commit = router.git(root, "rev-parse", "HEAD")
    parent = V._attested_activation_parent(data_root, publication, origin_root=root, origin_commit=commit)
    if parent["bundle_sha256"] != intent["parent_bundle_sha256"] or parent["continuous_reversal"]["operating_manifest"]["scopes"] != intent["frozen_parent_scopes"]:
        raise ValueError("cumulative_scoring_parent_scope_map_changed")
    output = path.parent / "source-first-preparations" / intent["artifact_content_sha256"]
    aliases = {sid:[name.removeprefix("ADD_") for name in cfg["alternatives"]] for sid,cfg in intent["scopes"].items()}
    from src.engine.lifecycle.research_admission import acquire

    reservation = acquire(data_root, "main_machine_policy", day)
    if reservation is None:
        raise ValueError("cumulative_scoring_resource_admission_busy")
    try:
        with reservation.worker():
            prepared = prepare_scoring(data_root, output, parent=parent, day=day, scope_candidates=aliases)
    finally:
        reservation.close()
    if prepared["scopes"] != intent["scopes"]:
        raise ValueError("cumulative_scoring_intent_scope_changed")
    frozen = _archive(path, output/"evidence")
    bound = P.seal(dict(prepared, source_first_intent_sha256=intent["artifact_content_sha256"],
                        source_receipts=prepared["source_receipts"]+[frozen]))
    bound_path = output / "prepared-for-intent.json"
    if bound_path.exists() and N._read(bound_path) != bound:
        raise ValueError("cumulative_scoring_preparation_conflict")
    P.write(bound_path, bound)
    if N._read(path) != intent:
        raise ValueError("cumulative_scoring_intent_changed")
    return intake_scoring(data_root, bound_path, confirm=SCORING_AUTHORITY, origin_root=root, origin_commit=commit)


def scoring_for_build(data_root, parent, day, source_sha):
    old = parent["continuous_reversal"]["operating_manifest"].get(
        "cumulative_scoring_contract"
    )
    path = scoring_path(data_root)
    request = N._read(path) if path.exists() else old
    if request is None:
        return None
    validate_scoring(request, check_sources=True)
    if (
        approval(parent["continuous_reversal"]["operating_manifest"])[
            "research_batch_sha256"
        ]
        != request["research_batch_sha256"]
    ):
        raise ValueError("cumulative_scoring_parent_registry_changed")
    if old and request["artifact_content_sha256"] == old.get("artifact_content_sha256"):
        return request
    if request.get("preparation_basis") is not None:
        _verify_preparation_inputs(data_root, request)
    if (
        request["parent_bundle_sha256"] != parent["bundle_sha256"]
        or request["publication_date"] != day
        or request["source_manifest_sha256"] != source_sha
    ):
        raise ValueError("cumulative_scoring_parent_source_or_date_changed")
    scopes = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    if request.get("unscored_scope_policy") == "carry_parent" and request["frozen_parent_scopes"] != scopes:
        raise ValueError("cumulative_scoring_parent_scope_map_changed")
    if any(scopes[s] != c["parent_branch_ids"] for s, c in request["scopes"].items()):
        raise ValueError("cumulative_scoring_parent_membership_changed")
    return request


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


def select_variant(
    group, current, metrics, *, authority, scoring=None, scope=None, research_only=False
):
    if authority != (None if research_only else SELECTION_AUTHORITY):
        raise ValueError("cumulative_selection_not_delegated")
    if research_only and scoring is None:
        raise ValueError("cumulative_scoring_research_contract_missing")
    if scoring is not None:
        validate_scoring(scoring, approved=not research_only)
        if (
            scope not in scoring["scopes"]
            or group["alternatives"] != scoring["scopes"][scope]["alternatives"]
        ):
            raise ValueError("cumulative_scoring_scope_changed")
    variants = dict(group["alternatives"], CURRENT_NATIVE=sorted(current))
    baseline = metrics.get("CURRENT_NATIVE") or {}
    cohort = baseline.get("source_universe_sha256")
    usable = []
    for name, ids in variants.items():
        m = metrics.get(name) or {}
        if scoring is not None:
            if (
                m.get("statistic_contract_sha256") != P.digest(scoring_spec())
                or m.get("scoring_contract_sha256")
                != scoring["artifact_content_sha256"]
            ):
                raise ValueError("cumulative_scoring_metric_contract_changed")
            m = dict(
                m,
                counts=(m.get("chronological") or {}).get("counts", {}),
                comparison_complete=m.get("comparison_complete") is True
                and m.get("statistic_source_complete") is True,
            )
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
        return dict(
            branch_ids=sorted(current),
            status="comparison_incomplete_carry",
            **(dict(research_only=True) if research_only else {}),
            **(
                dict(
                    research_ranking=[
                        dict(
                            variant=x["name"],
                            wins=x["w"],
                            resolved=x["n"],
                            score=wilson_score(x["w"], x["n"]),
                        )
                        for x in sorted(
                            usable,
                            key=lambda x: (
                                -wilson_score(x["w"], x["n"]),
                                -x["w"],
                                len(x["ids"]),
                                x["name"],
                            ),
                        )
                    ]
                )
                if scoring
                else {}
            ),
        )
    if scoring is not None:
        winner = min(
            usable,
            key=lambda x: (
                -wilson_score(x["w"], x["n"]),
                -x["w"],
                x["name"] != "CURRENT_NATIVE",
                len(x["ids"]),
                x["name"],
            ),
        )
        if wilson_score(winner["w"], winner["n"]) <= wilson_score(old["w"], old["n"]):
            winner = old
        return dict(
            branch_ids=winner["ids"],
            variant=winner["name"],
            status="selected" if winner["ids"] != sorted(current) else "carried",
            **(dict(research_only=True) if research_only else {}),
            wins=winner["w"],
            resolved=winner["n"],
            score=wilson_score(winner["w"], winner["n"]),
            statistic_contract_sha256=P.digest(scoring_spec()),
            scoring_contract_sha256=scoring["artifact_content_sha256"],
        )
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
    scoring = manifest.get("cumulative_scoring_contract")
    if scoring is not None:
        validate_scoring(scoring)
    chosen = {}
    complete = machine.get("status") == "completed" and bool(
        machine.get("source_manifest_receipt")
    )
    batch = approval(manifest)["research_batch_sha256"]
    for sid, g in registered.items():
        if scoring and scoring.get("unscored_scope_policy") == "carry_parent" and sid not in scoring["scopes"]:
            chosen[sid] = dict(
                branch_ids=sorted(current[sid]),
                variant="CURRENT_NATIVE",
                status="carried_unscored_scope",
            )
            manifest["scopes"][sid] = chosen[sid]["branch_ids"]
            continue
        cohort = P.digest(
            [machine["source_manifest_sha256"], sid, machine["label_contract"]]
        )
        scoped = scoring if scoring and sid in scoring["scopes"] else None
        alternatives = (
            scoped["scopes"][sid]["alternatives"] if scoped else Q.variants(sid, batch)
        )
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
            scoring=scoped,
            scope=sid,
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
            schema=(
                "cumulative_variant_selection_v3"
                if scoring
                else "cumulative_variant_selection_v2"
            ),
            **(
                dict(
                    scoring_contract_sha256=scoring["artifact_content_sha256"],
                    statistic_contract_sha256=P.digest(scoring_spec()),
                )
                if scoring
                else {}
            ),
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
            variant_selection_basis=(
                SCORE_VERSION if scoring else "cumulative_target_first_win_fraction"
            ),
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
    scoring = manifest.get("cumulative_scoring_contract")
    if scoring is not None:
        validate_scoring(scoring)
        if (
            not receipt
            or receipt.get("schema") != "cumulative_variant_selection_v3"
            or receipt.get("scoring_contract_sha256")
            != scoring["artifact_content_sha256"]
            or receipt.get("statistic_contract_sha256") != P.digest(scoring_spec())
            or scoring["research_batch_sha256"] != batch
        ):
            raise ValueError("cumulative_scoring_receipt_invalid")
        for sid in scoring["scopes"]:
            selected = receipt.get("selected", {}).get(sid, {})
            if selected.get("status") == "selected" and scoring["scopes"][sid][
                "alternatives"
            ].get(selected.get("variant")) != selected.get("branch_ids"):
                raise ValueError("cumulative_scoring_selected_variant_invalid")
            if selected.get("status") == "comparison_incomplete_carry":
                continue
            if (
                selected.get("score")
                != wilson_score(selected.get("wins"), selected.get("resolved"))
                or selected.get("scoring_contract_sha256")
                != scoring["artifact_content_sha256"]
                or selected.get("statistic_contract_sha256") != P.digest(scoring_spec())
            ):
                raise ValueError("cumulative_scoring_selected_metric_invalid")
        if scoring.get("unscored_scope_policy") == "carry_parent" and any(
            ids != manifest["scopes"][sid]
            for sid, ids in scoring["frozen_parent_scopes"].items()
            if sid not in scoring["scopes"]
        ):
            raise ValueError("cumulative_scoring_unscored_membership_changed")
    elif receipt and receipt.get("schema") != "cumulative_variant_selection_v2":
        raise ValueError("cumulative_selection_schema_invalid")
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


def prepare_scoring(data_root, output, *, parent, day, scope_candidates=None):
    """Freeze verified native inputs before the first machine-stage writer."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.automation import postclose_summary_handoff as H

    N.validate(parent, target_date=parent["target_date"])
    _dates(day, N.next_target(day))
    manifest = parent["continuous_reversal"]["operating_manifest"]
    batch = approval(manifest)["research_batch_sha256"]
    catalog = Q.catalog(batch)
    selected = SCORING_ALIASES if scope_candidates is None else scope_candidates
    if not isinstance(selected, dict) or not selected or any(
        sid not in SCORING_ALIASES
        or not isinstance(aliases, (list, tuple))
        or not aliases
        or len(aliases) != len(set(aliases))
        or not set(aliases) <= set(SCORING_ALIASES[sid])
        for sid, aliases in selected.items()
    ):
        raise ValueError("cumulative_scoring_requested_candidates_invalid")
    scopes = {}
    for sid, aliases in selected.items():
        ids = sorted(manifest["scopes"][sid])
        scopes[sid] = dict(
            parent_branch_ids=ids,
            alternatives={
                "ADD_" + a: sorted(set(ids) | {catalog["groups"][sid]["additions"][a]})
                for a in aliases
            },
        )
    inputs = _preparation_inputs(data_root, day)
    reader_code = P.file_hash(H.__file__)
    with _before_machine(data_root, day):
        pass
    # Population freezing may be expensive. Do not hold the stage writer lock
    # while creating this unapproved draft; a scheduled writer wins normally.
    source = P.ensure_population(data_root, day)
    receipt = P.population_receipt(source)
    if not receipt or not any(
        r["day"] == day and r["venue"] == "SOR" and "REGULAR" in r["session"]
        for r in source["normalized_sources"]["partitions"]
    ):
        raise ValueError("cumulative_scoring_current_source_missing")
    with _before_machine(data_root, day):
        if _preparation_inputs(data_root, day) != inputs:
            raise ValueError("cumulative_scoring_preparation_inputs_changed")
        if P.file_hash(H.__file__) != reader_code:
            raise ValueError("cumulative_scoring_preparation_reader_changed")
        output = Path(output)
        sources = [
            _archive(Path(r["path"]), output / "evidence")
            for r in [receipt, *inputs.values()]
        ]
        contract = P.seal(dict(
            schema=SCORING_SCHEMA, spec=scoring_spec(), operator_receipt=None,
            preparation_basis=SOURCE_FIRST, preparation_inputs=inputs,
            preparation_reader_code_sha256=reader_code,
            native_source_manifest_receipt=receipt,
            parent_bundle_sha256=parent["bundle_sha256"],
            source_manifest_sha256=source["artifact_content_sha256"],
            publication_date=day, target_date=N.next_target(day), scopes=scopes,
            **(dict(unscored_scope_policy="carry_parent", frozen_parent_scopes=copy.deepcopy(manifest["scopes"]))
               if scope_candidates is not None else {}),
            research_batch_sha256=batch, registry_sha256=Q.registry(batch),
            source_receipts=sources,
            contract_file_sha256={Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()},
            **P.AUTH,
        ))
        validate_scoring(contract, approved=False, check_sources=True)
        destination = output / "prepared-scoring.json"
        if destination.exists() and N._read(destination) != contract:
            raise ValueError("cumulative_scoring_preparation_conflict")
        P.write(destination, contract)
        return contract


def intake_scoring(data_root, prepared_path, *, confirm, origin_root, origin_commit):
    """Explicit activation request under the existing policy publisher lock."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    if confirm != SCORING_AUTHORITY:
        raise ValueError("cumulative_scoring_explicit_authority_required")
    prepared = validate_scoring(
        N._read(Path(prepared_path)), approved=False, check_sources=True
    )
    _verify_preparation_inputs(data_root, prepared)
    if prepared["contract_file_sha256"] != {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }:
        raise ValueError("cumulative_scoring_prepared_code_changed")
    parent = V._attested_activation_parent(
        data_root,
        prepared["publication_date"],
        origin_root=origin_root,
        origin_commit=origin_commit,
    )
    if parent["bundle_sha256"] != prepared["parent_bundle_sha256"]:
        raise ValueError("cumulative_scoring_parent_changed")
    if prepared.get("unscored_scope_policy") == "carry_parent" and (
        parent["continuous_reversal"]["operating_manifest"]["scopes"] != prepared["frozen_parent_scopes"]
    ):
        raise ValueError("cumulative_scoring_parent_scope_map_changed")
    request = P.seal(dict(prepared, operator_receipt=confirm))
    validate_scoring(request, check_sources=True)
    root = N.root(Path(data_root))
    with _before_machine(data_root, prepared["publication_date"]), (root / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (
            _preparation_inputs(data_root, prepared["publication_date"]) != prepared["preparation_inputs"]
            or P.file_hash(prepared["native_source_manifest_receipt"]["path"])
            != prepared["native_source_manifest_receipt"]["sha256"]
        ):
            raise ValueError("cumulative_scoring_preparation_inputs_changed")
        if (
            N._read(root / "current.json")["bundle_sha256"]
            != prepared["parent_bundle_sha256"]
        ):
            raise ValueError("cumulative_scoring_parent_changed")
        path = scoring_path(data_root)
        if path.exists() and N._read(path) != request:
            raise ValueError("cumulative_scoring_request_conflict")
        if pending(data_root, parent, prepared["target_date"]) is not None:
            raise ValueError("cumulative_scoring_conflicts_with_registration")
        manifest = parent["continuous_reversal"]["operating_manifest"]
        consumed_hashes = {
            r.get("artifact_content_sha256")
            for r in manifest.get("registration_receipts", [])
            + [manifest.get("change_receipt") or {}]
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
                    other.get("parent_bundle_sha256") == parent["bundle_sha256"]
                    and other.get("artifact_content_sha256") not in consumed_hashes
                ):
                    raise ValueError(
                        "cumulative_scoring_conflicts_with_registration:" + name
                    )
        P.write(path, request)
    return request


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
    scoring = sub.add_parser("prepare-scoring")
    for name in ("data-root", "output", "parent"):
        scoring.add_argument("--" + name, type=Path, required=True)
    scoring.add_argument("--source-date", required=True)
    scoring.add_argument("--scope")
    scoring.add_argument("--candidate", action="append")
    activate = sub.add_parser("intake-scoring")
    for name in ("data-root", "prepared", "origin-root"):
        activate.add_argument("--" + name, type=Path, required=True)
    activate.add_argument("--origin-commit", required=True)
    activate.add_argument("--confirm", required=True)
    request = sub.add_parser("request-scoring")
    for name in ("data-root", "origin-root"):
        request.add_argument("--" + name, type=Path, required=True)
    for name in ("publication-date", "scope", "origin-commit", "confirm"):
        request.add_argument("--" + name, required=True)
    request.add_argument("--candidate", action="append", required=True)
    fulfill = sub.add_parser("fulfill-scoring")
    fulfill.add_argument("--data-root", type=Path, required=True)
    fulfill.add_argument("--source-date", required=True)
    fulfill.add_argument("--publication-date", required=True)
    args = parser.parse_args(argv)
    if args.operation == "request-scoring":
        result = request_scoring(
            args.data_root, publication=args.publication_date,
            scope_candidates={args.scope: args.candidate}, confirm=args.confirm,
            origin_root=args.origin_root, origin_commit=args.origin_commit,
        )
    elif args.operation == "fulfill-scoring":
        result = fulfill_scoring(args.data_root, args.source_date, args.publication_date)
    elif args.operation == "prepare":
        result = prepare(
            args.evidence_root,
            args.output,
            parent=N._read(args.parent),
            parity_path=args.parity,
            publication=args.publication_date,
            target_date=args.target_date,
            research_batch=args.research_batch_sha256,
        )
    elif args.operation == "prepare-scoring":
        if bool(args.scope) != bool(args.candidate):
            raise ValueError("cumulative_scoring_scope_and_candidate_required_together")
        result = prepare_scoring(
            args.data_root,
            args.output,
            parent=N._read(args.parent),
            day=args.source_date,
            scope_candidates={args.scope: args.candidate} if args.scope else None,
        )
    elif args.operation == "intake-scoring":
        result = intake_scoring(
            args.data_root,
            args.prepared,
            confirm=args.confirm,
            origin_root=args.origin_root,
            origin_commit=args.origin_commit,
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
