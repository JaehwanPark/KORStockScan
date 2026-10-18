"""Immutable Main stop preregistration and later source finalization.

Registration freezes a hypothesis and finite comparison before prospective
holdout observations exist. Historical studies retain their real registration
time and are report-only. Neither artifact grants operator or order authority.
"""
from __future__ import annotations

from dataclasses import asdict
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import time

from .main_stop_policy import MARKETS, ROLES, TUNABLE, StopValues, bounded_object, digest, finite

PREREGISTRATION_SCHEMA = "main_stop_preregistration_v1"
SOURCE_SEAL_SCHEMA = "main_stop_experiment_source_seal_v1"
PREPARATION_SCHEMA = "main_stop_experiment_preparation_v1"
SCHEMA = "main_stop_experiment_v2"
MAX_BYTES = 1024 * 1024
MAX_SOURCES = 4096
MODES = {"prospective", "historical_report_only"}
PARAMETERS = {
    "parent_sha256", "code_sha256", "operator_lock_sha256", "allowed_keys",
    "max_daily_change", "split_at", "embargo_sec", "min_train", "min_holdout",
    "minimum_paired_ev_krw", "max_censoring_ratio", "max_standard_error_krw",
    "candidate_grid", "source_start_at", "source_end_at", "hypothesis",
}
OPTIONAL_PARAMETERS = {"selection_cost_grade", "selection_quantity_status"}
COST_GRADES = ("exact_execution", "exact_position_total", "broker_total_allocated")
_PUBLISHED_SOURCES = ContextVar('main_stop_publisher_verified_sources', default=None)


def _published_source_identity(name,expected):
    from src.engine.lifecycle.holding_window_generation import source_stat
    path=Path(name)
    if path.exists():
        _safe_path(path)
        return ['physical',list(source_stat(path.stat()))]
    if path.parent.name=='pipeline_events' and path.name.endswith('.jsonl'):
        from src.engine.automation.main_stop_postclose import _archived_pipeline_source
        _archived_pipeline_source(path,expected,verify_full=False)
        archive=Path(str(path)+'.gz');receipt=Path(str(archive)+'.archive_receipt.json')
        return ['archive',list(source_stat(archive.lstat())),list(source_stat(receipt.lstat()))]
    raise ValueError('stop_experiment_source_generation_changed')


@contextmanager
def published_source_context(inventory, dependency_stats):
    """Reuse only publisher-sealed bytes whose native file identity still holds.

    The native committed reader first checks report/policy/source/catalog and
    dependency bindings. No standalone experiment, publisher or preflight
    enters this scope; those retain full byte verification. Check identities
    before and after semantic validation to reject replacement during a read.
    Lossless archives retain the original logical hash and exact native archive
    custody; absent raw data without that verified custody remains invalid.
    """
    trusted={}
    for name,expected in inventory.items():
        observed=_published_source_identity(name,expected)
        if observed[0]=='physical' and dependency_stats.get(name)!=observed[1]:
            raise ValueError('stop_experiment_source_generation_changed')
        trusted[name]=(expected,observed)
    token=_PUBLISHED_SOURCES.set(trusted)
    try:
        yield
        for name,(expected,observed) in trusted.items():
            if _published_source_identity(name,expected)!=observed:
                raise ValueError('stop_experiment_source_generation_changed')
    finally:_PUBLISHED_SOURCES.reset(token)


def selection_cost_grade(contract):
    """One frozen economic population; old contracts retain strict exact costs."""
    grade = (contract or {}).get("selection_cost_grade", "exact_execution")
    if grade not in COST_GRADES:
        raise ValueError("stop_selection_cost_grade_invalid")
    return grade


def selection_quantity_status(contract):
    status=(contract or {}).get('selection_quantity_status','full_fill')
    if status not in {'full_fill','settled_partial'}:
        raise ValueError('stop_selection_quantity_status_invalid')
    return status


def validate_cost_selection(evidence, contract):
    """Runtime rechecks the exact grade used by the native selector, no pooling."""
    if "selection_cost_grade" not in contract:
        return
    costs = evidence.get("cost_selection") or {}
    grade = selection_cost_grade(contract)
    if (costs.get("schema") != "main_stop_cost_selection_v1"
            or costs.get("selection_cost_grade") != grade
            or costs.get('selection_quantity_status') != selection_quantity_status(contract)
            or costs.get("comparison_metric") != "causal_modeled_exit_net_krw"
            or costs.get("actual_cost_usage") != "source_eligibility_only"
            or costs.get('denominator_policy') != 'all_registered_positions_including_unknown_cost_or_source'
            or costs.get("actual_profit_claimed") is not False
            or set(costs.get("aggregates_by_grade", {})) != set(COST_GRADES)
            or costs["aggregates_by_grade"][grade] != evidence.get("aggregates")
            or costs.get("cost_selection_sha256") != digest({k:v for k,v in costs.items()
                                                             if k != "cost_selection_sha256"})):
        raise ValueError("stop_selection_cost_evidence_invalid")
    # Every candidate shares the same observed position intersection. Grades
    # remain separate even if their individual samples do not pass the floor.
    for grouped in costs["aggregates_by_grade"].values():
        if set(grouped) != set(evidence["aggregates"]):
            raise ValueError("stop_selection_cost_evidence_invalid")
        for split in ("train", "holdout"):
            if len({(row.get(split + "_n"), row.get(split + "_total"))
                    for row in grouped.values()}) > 1:
                raise ValueError("stop_selection_cost_denominator_mismatch")
        from .main_stop_replay import choose
        choose(grouped,contract)  # Validate every reported grade, never pool it.
    for split in ('train','holdout'):
        if len({row[split+'_total'] for grouped in costs['aggregates_by_grade'].values()
                for row in grouped.values()})>1:
            raise ValueError('stop_selection_cost_denominator_mismatch')


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _clock():
    now = time.time()
    if not finite(now) or now <= 0:
        raise ValueError("stop_experiment_clock_invalid")
    return now


def _plain(value):
    """Freeze caller-owned containers and reject non-JSON/nonfinite values."""
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True, allow_nan=False))


def _safe_path(path):
    path = Path(path).absolute()
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("stop_experiment_path_invalid")
    return path


def _reference(path, body, hash_key):
    value, byte_sha = bounded_object(_safe_path(path), MAX_BYTES)
    if value != body:
        raise ValueError("stop_experiment_immutable_collision")
    return dict(path=str(path), sha256=byte_sha, **{hash_key: body[hash_key]})


def _write_immutable(path, body, hash_key):
    """Publish complete bytes with no replacing rename or overwrite race."""
    path = _safe_path(path)
    raw = (json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("stop_experiment_manifest_unbounded")
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe_path(path)
    fd, name = tempfile.mkstemp(prefix=".stop-experiment-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(name, path)
        except FileExistsError:
            pass
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return _reference(path, body, hash_key)
    finally:
        os.unlink(name)


def _read_reference(reference, schema, hash_key):
    if (not isinstance(reference, dict) or set(reference) != {"path", "sha256", hash_key}
            or not isinstance(reference.get("path"), str) or not _sha(reference.get("sha256"))
            or not _sha(reference.get(hash_key))):
        raise ValueError("stop_experiment_reference_invalid")
    body, byte_sha = bounded_object(_safe_path(reference["path"]), MAX_BYTES)
    if (body.get("schema") != schema or byte_sha != reference["sha256"]
            or body.get(hash_key) != reference[hash_key]
            or body.get(hash_key) != digest({k: v for k, v in body.items() if k != hash_key})):
        raise ValueError("stop_experiment_reference_invalid")
    return body


def _validate_parameters(parameters):
    p = parameters
    if (not isinstance(p, dict) or not PARAMETERS <= set(p)
            or not set(p) <= PARAMETERS | OPTIONAL_PARAMETERS):
        raise ValueError("stop_experiment_parameters_invalid")
    selection_cost_grade(p)
    selection_quantity_status(p)
    if 'selection_quantity_status' in p and 'selection_cost_grade' not in p:
        raise ValueError('stop_selection_quantity_requires_cost_contract')
    if (any(not _sha(p[k]) for k in ("parent_sha256", "code_sha256", "operator_lock_sha256"))
            or not isinstance(p["hypothesis"], str) or not p["hypothesis"].strip()
            or len(p["hypothesis"]) > 4096
            or not isinstance(p["allowed_keys"], list) or len(p["allowed_keys"]) != 1
            or any(not isinstance(key, str) or key not in TUNABLE for key in p["allowed_keys"])
            or not isinstance(p["max_daily_change"], dict)
            or set(p["max_daily_change"]) != set(p["allowed_keys"])
            or any(not finite(v) or v <= 0 for v in p["max_daily_change"].values())
            or any(type(p[k]) is not int or p[k] < 2 for k in ("min_train", "min_holdout"))
            or any(not finite(p[k]) for k in ("split_at", "embargo_sec", "source_start_at", "source_end_at",
                       "minimum_paired_ev_krw", "max_censoring_ratio", "max_standard_error_krw"))
            or p["source_start_at"] <= 0 or p["embargo_sec"] < 60
            or not p["source_start_at"] < p["split_at"] - p["embargo_sec"]
            or not p["split_at"] + p["embargo_sec"] < p["source_end_at"]
            or p["minimum_paired_ev_krw"] < 0 or p["max_standard_error_krw"] < 0
            or not 0 <= p["max_censoring_ratio"] < 1):
        raise ValueError("stop_experiment_parameters_invalid")
    grid = p["candidate_grid"]
    if not isinstance(grid, dict) or not 2 <= len(grid) <= 64 or "parent" not in grid:
        raise ValueError("stop_experiment_candidate_grid_invalid")
    parent = StopValues.parse(grid["parent"])
    if digest(asdict(parent)) != p["parent_sha256"]:
        raise ValueError("stop_experiment_parent_invalid")
    # Import lazily: the replay validator delegates v2 validation to this module.
    from .main_stop_replay import candidates
    native = candidates(parent)
    expected = {name: asdict(value) for name, value in native.items()
                if name == "parent" or (name.split(":")[0] in p["allowed_keys"]
                    and abs(getattr(value, name.split(":")[0]) - getattr(parent, name.split(":")[0]))
                    <= p["max_daily_change"][name.split(":")[0]])}
    if grid != expected:
        raise ValueError("stop_experiment_candidate_grid_invalid")


def _validate_registration(body, *, enforce_window=True):
    expected = {"schema", "experiment_id", "revision", "cell", "mode", "frozen_at",
                "parameters", "allowed_runtime_apply", "preregistration_sha256"}
    if (not isinstance(body, dict) or set(body) != expected
            or body["schema"] != PREREGISTRATION_SCHEMA
            or not isinstance(body["experiment_id"], str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", body["experiment_id"])
            or type(body["revision"]) is not int or not 1 <= body["revision"] <= 1000000
            or body["cell"] not in {f"{role}|{market}" for role in ROLES for market in MARKETS}
            or body["mode"] not in MODES or not finite(body["frozen_at"]) or body["frozen_at"] <= 0
            or body["allowed_runtime_apply"] is not False
            or body["preregistration_sha256"] != digest({k: v for k, v in body.items()
                                                        if k != "preregistration_sha256"})):
        raise ValueError("stop_preregistration_invalid")
    _validate_parameters(body["parameters"])
    p = body["parameters"]
    if not enforce_window:
        return body
    if body["mode"] == "prospective":
        if body["frozen_at"] >= p["split_at"] - p["embargo_sec"]:
            raise ValueError("stop_experiment_not_frozen_before_holdout")
    elif p["source_end_at"] > body["frozen_at"]:
        raise ValueError("stop_historical_source_window_in_future")
    return body


def register_experiment(directory, *, experiment_id, revision, cell, parameters,
                        mode="prospective"):
    """Create an immutable preregistration; callers cannot provide frozen_at.

    ``parameters`` contains no source hash or performance PASS. Both are bound
    later. A repeat with identical parameters returns the original receipt;
    a changed hypothesis, grid, parent or code requires a new revision.
    """
    now = _clock()
    body = dict(schema=PREREGISTRATION_SCHEMA, experiment_id=experiment_id,
                revision=revision, cell=cell, mode=mode, frozen_at=now,
                parameters=_plain(parameters), allowed_runtime_apply=False)
    body["preregistration_sha256"] = digest(body)
    _validate_registration(body, enforce_window=False)
    path = _safe_path(directory) / experiment_id / f"preregistration_{revision}.json"
    if path.exists():
        existing, _ = bounded_object(_safe_path(path), MAX_BYTES)
        _validate_registration(existing)
        if {k: v for k, v in existing.items() if k not in {"frozen_at", "preregistration_sha256"}} != {
                k: v for k, v in body.items() if k not in {"frozen_at", "preregistration_sha256"}}:
            raise ValueError("stop_experiment_revision_conflict")
        if existing["frozen_at"] > now:
            raise ValueError("stop_experiment_clock_regressed")
        return _reference(path, existing, "preregistration_sha256")
    _validate_registration(body)
    return _write_immutable(path, body, "preregistration_sha256")


def _verify_inventory(inventory):
    from src.engine.lifecycle.holding_window_generation import byte_generation
    if not isinstance(inventory, dict) or not 1 <= len(inventory) <= MAX_SOURCES:
        raise ValueError("stop_experiment_source_inventory_invalid")
    for name, expected in inventory.items():
        if not isinstance(name, str) or not Path(name).is_absolute() or not isinstance(expected, dict):
            raise ValueError("stop_experiment_source_inventory_invalid")
        trusted=(_PUBLISHED_SOURCES.get() or {}).get(name)
        if trusted is not None:
            if trusted[0]!=expected or _published_source_identity(name,expected)!=trusted[1]:
                raise ValueError('stop_experiment_source_generation_changed')
            continue
        path=_safe_path(name)
        if not path.exists() and path.parent.name=='pipeline_events' and path.name.endswith('.jsonl'):
            from src.engine.automation.main_stop_postclose import _archived_pipeline_source
            _archived_pipeline_source(path,expected,verify_full=True)
            continue
        if byte_generation(_safe_path(name)) != expected:
            raise ValueError("stop_experiment_source_generation_changed")


def _verify_performance(reference, code_sha, *, mode, source_sha, require_native=False):
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError("stop_performance_gate_unverified")
    body, byte_sha = bounded_object(_safe_path(reference["path"]), MAX_BYTES)
    if byte_sha != reference["sha256"] or body.get("code_sha256") != code_sha:
        raise ValueError("stop_performance_gate_unverified")
    if body.get('schema') == 'main_stop_performance_v2':
        from src.engine.automation.main_stop_performance import validate_receipt
        validate_receipt(body,code_sha=code_sha,source_sha=source_sha,
                         require_full=mode=='prospective')
        return
    if body.get('schema') != 'main_stop_performance_v1' or (require_native and mode=='prospective'):
        raise ValueError('stop_performance_native_producer_required')
    if mode == "historical_report_only":
        if (body.get("status") != "measured" or body.get("scope") != "offline_research_and_pure_decisions"
                or body.get("allowed_runtime_apply") is not False or body.get("source_sha256") != source_sha
                or not isinstance(body.get("metrics"), dict) or not body["metrics"]
                or not isinstance(body.get("unresolved_findings"), list)
                or any(not isinstance(finding, str) or not finding for finding in body["unresolved_findings"])):
            raise ValueError("stop_research_performance_unverified")
    elif (body.get("status") != "pass" or body.get("scope") != "runtime_and_postclose"
            or body.get("unresolved_findings") != []):
        raise ValueError("stop_performance_gate_unverified")


def require_native_publication_performance(contract):
    """New numeric authority always requires native, fully covered evidence.

    Legacy artifact validators deliberately retain their original semantics
    for incumbent reads/carry. Cost grade omission must not grant a new policy
    publication the legacy label-only performance contract.
    """
    if (not isinstance(contract,dict) or not _sha(contract.get('code_sha256'))
            or not _sha(contract.get('source_sha256')) or not isinstance(contract.get('performance_receipt'),dict)):
        raise ValueError('stop_publication_experiment_unverified')
    if contract.get('mode','prospective')!='prospective':
        raise ValueError('stop_historical_experiment_report_only')
    _verify_performance(contract.get('performance_receipt'),contract.get('code_sha256'),
        mode='prospective',source_sha=contract.get('source_sha256'),require_native=True)


def seal_experiment_sources(directory, preregistration, *, source_inventory,
                            observed_start_at, observed_end_at):
    """Seal consumed source before performance measurement; grants no authority.

    Bounds come from the source producer's complete consumed census. Its caller
    must enforce them on replay rows too; this module never infers event time
    from file mtime, a filename or the registration date.
    """
    registered = _validate_registration(_read_reference(
        preregistration, PREREGISTRATION_SCHEMA, "preregistration_sha256"))
    now = _clock()
    p = registered["parameters"]
    if (now < registered["frozen_at"] or now < p["source_end_at"]
            or not finite(observed_start_at) or not finite(observed_end_at)
            or not p["source_start_at"] <= observed_start_at <= observed_end_at <= p["source_end_at"]):
        raise ValueError("stop_experiment_source_window_invalid")
    inventory = _plain(source_inventory)
    _verify_inventory(inventory)
    seal = dict(schema=SOURCE_SEAL_SCHEMA, preregistration=preregistration,
                source_sha256=digest(inventory), source_inventory=inventory,
                source_start_at=p["source_start_at"], source_end_at=p["source_end_at"],
                observed_start_at=observed_start_at, observed_end_at=observed_end_at,
                finalized_at=now, allowed_runtime_apply=False)
    seal["source_seal_sha256"] = digest(seal)
    seal_path = _safe_path(directory) / registered["experiment_id"] / (
        f"source_seal_{registered['revision']}_{seal['source_sha256']}.json")
    if seal_path.exists():
        old, _ = bounded_object(_safe_path(seal_path), MAX_BYTES)
        comparison = {k: v for k, v in seal.items() if k not in {"finalized_at", "source_seal_sha256"}}
        if {k: v for k, v in old.items() if k not in {"finalized_at", "source_seal_sha256"}} != comparison:
            raise ValueError("stop_experiment_source_seal_collision")
        if not finite(old.get("finalized_at")) or old["finalized_at"] > now:
            raise ValueError("stop_experiment_clock_regressed")
        seal = old
    source_ref = _write_immutable(seal_path, seal, "source_seal_sha256")
    return source_ref


def prepare_experiment(preregistration, source_seal):
    """A source-bound evaluation input, deliberately not a runtime contract."""
    registered=_validate_registration(_read_reference(
        preregistration,PREREGISTRATION_SCHEMA,'preregistration_sha256'))
    seal=_read_reference(source_seal,SOURCE_SEAL_SCHEMA,'source_seal_sha256')
    if seal['preregistration']!=preregistration:
        raise ValueError('stop_experiment_preparation_source_mismatch')
    body=dict(registered['parameters'],schema=PREPARATION_SCHEMA,cell=registered['cell'],
        mode=registered['mode'],frozen_at=registered['frozen_at'],source_sha256=seal['source_sha256'],
        preregistration=_plain(preregistration),source_seal=_plain(source_seal),allowed_runtime_apply=False)
    body['preparation_sha256']=digest(body)
    validate_preparation(body,parent_sha=body['parent_sha256'],source_sha=body['source_sha256'],
                         code_sha=body['code_sha256'])
    return body


def validate_preparation(preparation, *, parent_sha, source_sha, code_sha):
    """Validate native registration/seal without accepting a performance verdict."""
    c=preparation
    if not isinstance(c,dict) or c.get('schema')!=PREPARATION_SCHEMA:
        raise ValueError('stop_experiment_preparation_invalid')
    expected=PARAMETERS|(set(c)&OPTIONAL_PARAMETERS)|{'schema','cell','mode','frozen_at','source_sha256',
        'preregistration','source_seal','allowed_runtime_apply','preparation_sha256'}
    if (set(c)!=expected or c['preparation_sha256']!=digest({k:v for k,v in c.items() if k!='preparation_sha256'})
            or c['parent_sha256']!=parent_sha or c['source_sha256']!=source_sha or c['code_sha256']!=code_sha
            or c['allowed_runtime_apply'] is not False):
        raise ValueError('stop_experiment_preparation_invalid')
    registered=_validate_registration(_read_reference(c['preregistration'],PREREGISTRATION_SCHEMA,'preregistration_sha256'))
    if (set(registered['parameters'])!=set(c)&(PARAMETERS|OPTIONAL_PARAMETERS)
            or any(c[k]!=registered['parameters'][k] for k in registered['parameters'])
            or any(c[k]!=registered[k] for k in ('cell','mode','frozen_at'))):
        raise ValueError('stop_experiment_preregistration_changed')
    _validate_source_seal(c,source_sha)
    return c


def finalize_experiment(directory, preregistration, *, source_inventory,
                        performance_receipt, observed_start_at, observed_end_at):
    """Bind real measured performance after source/evaluation preparation."""
    source_ref=seal_experiment_sources(directory,preregistration,source_inventory=source_inventory,
        observed_start_at=observed_start_at,observed_end_at=observed_end_at)
    registered=_validate_registration(_read_reference(preregistration,PREREGISTRATION_SCHEMA,'preregistration_sha256'))
    p=registered['parameters'];seal=_read_reference(source_ref,SOURCE_SEAL_SCHEMA,'source_seal_sha256')
    performance=_plain(performance_receipt)
    _verify_performance(performance,p['code_sha256'],mode=registered['mode'],source_sha=seal['source_sha256'],
                        require_native=True)
    contract = dict(p, schema=SCHEMA, cell=registered["cell"], mode=registered["mode"],
                    frozen_at=registered["frozen_at"], source_sha256=seal["source_sha256"],
                    preregistration=_plain(preregistration), source_seal=source_ref,
                    performance_receipt=performance, allowed_runtime_apply=False)
    contract["experiment_sha256"] = digest(contract)
    validate_experiment_v2(contract, parent_sha=p["parent_sha256"], source_sha=seal["source_sha256"],
                           code_sha=p["code_sha256"], require_promotion=False)
    contract_path = _safe_path(directory) / registered["experiment_id"] / (
        f"experiment_{registered['revision']}_{contract['experiment_sha256']}.json")
    _write_immutable(contract_path, contract, "experiment_sha256")
    return contract


def validate_experiment_v2(contract, *, parent_sha, source_sha, code_sha,
                           require_promotion=True):
    """Validate both immutable producers; no operator authority is granted.

    Runtime/policy consumers keep the default and reject retrospective studies.
    An offline report consumer may explicitly set ``require_promotion=False``.
    Existing operator-key, performance and economic selection gates still apply.
    """
    expected = PARAMETERS | (set(contract) & OPTIONAL_PARAMETERS if isinstance(contract,dict) else set()) | {"schema", "cell", "mode", "frozen_at", "source_sha256",
                             "preregistration", "source_seal", "performance_receipt",
                             "allowed_runtime_apply", "experiment_sha256"}
    c = contract
    if (not isinstance(c, dict) or set(c) != expected or c.get("schema") != SCHEMA
            or c.get("experiment_sha256") != digest({k: v for k, v in c.items() if k != "experiment_sha256"})
            or c.get("parent_sha256") != parent_sha or c.get("source_sha256") != source_sha
            or c.get("code_sha256") != code_sha or c.get("allowed_runtime_apply") is not False):
        raise ValueError("stop_experiment_binding_invalid")
    registered = _validate_registration(_read_reference(
        c["preregistration"], PREREGISTRATION_SCHEMA, "preregistration_sha256"))
    if (set(registered['parameters']) != set(c) & (PARAMETERS | OPTIONAL_PARAMETERS)
            or any(c[k] != registered["parameters"][k] for k in registered['parameters'])
            or any(c[k] != registered[k] for k in ("cell", "mode", "frozen_at"))):
        raise ValueError("stop_experiment_preregistration_changed")
    if require_promotion and c["mode"] != "prospective":
        raise ValueError("stop_historical_experiment_report_only")
    _validate_source_seal(c,source_sha)
    _verify_performance(c["performance_receipt"], code_sha, mode=c["mode"], source_sha=source_sha,
                        require_native='selection_cost_grade' in c)
    return c


def _validate_source_seal(c,source_sha):
    seal = _read_reference(c["source_seal"], SOURCE_SEAL_SCHEMA, "source_seal_sha256")
    if (set(seal) != {"schema", "preregistration", "source_sha256", "source_inventory",
                      "source_start_at", "source_end_at", "observed_start_at", "observed_end_at",
                      "finalized_at", "allowed_runtime_apply", "source_seal_sha256"}
            or seal["preregistration"] != c["preregistration"]
            or seal["source_sha256"] != source_sha
            or seal["source_sha256"] != digest(seal["source_inventory"])
            or any(seal[k] != c[k] for k in ("source_start_at", "source_end_at"))
            or seal["allowed_runtime_apply"] is not False
            or not all(finite(seal[k]) for k in ("observed_start_at", "observed_end_at", "finalized_at"))
            or not c["source_start_at"] <= seal["observed_start_at"] <= seal["observed_end_at"] <= c["source_end_at"]
            or not max(c["frozen_at"], c["source_end_at"]) <= seal["finalized_at"] <= _clock()):
        raise ValueError("stop_experiment_source_seal_invalid")
    _verify_inventory(seal["source_inventory"])
    return seal


def publish_experiment_manifest(output_path, contracts, *, data_root, source_date,
                                target_date, parents, parent_receipt, expected_sha256=None):
    """Publish the exact prospective mapping consumed by native postclose.

    ``parents``/``parent_receipt`` are the native ``post.baseline`` result. The
    explicit output is a research input, never a selected policy. Native
    publication independently repeats operator and economic selection gates.
    Replacement requires the prior byte SHA and preserves its original bytes.
    """
    from src.engine.automation import main_stop_postclose as post
    from src.engine.automation.operator_policy_succession import stop_key_authority
    from src.engine.infrastructure.validation_digest_session import postclose_session
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.lifecycle.research_disk_budget import atomic

    if (date.fromisoformat(source_date).isoformat()!=source_date
            or date.fromisoformat(target_date).isoformat()!=target_date
            or not '2026-09-29'<=source_date<target_date
            or not isinstance(contracts,dict) or len(contracts)!=1
            or set(parents)!={f'{role}|{market}' for role in ROLES for market in MARKETS}
            or expected_sha256 is not None and not _sha(expected_sha256)):
        raise ValueError('stop_experiment_publication_parameters_invalid')
    output_path=_safe_path(output_path).resolve();root=_safe_path(data_root).resolve()
    expected_path=root/'runtime/research/main_stop_confirmation'/f'experiments_{source_date}.json'
    if (output_path.name!=f'experiments_{source_date}.json'
            or (output_path==root or root in output_path.parents) and output_path!=expected_path):
        raise ValueError('stop_experiment_manifest_output_scope_invalid')
    manifest=_plain(contracts)
    raw=(json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
    if len(raw)>MAX_BYTES:raise ValueError('stop_experiment_manifest_unbounded')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    lock_path=_safe_path(output_path.with_name(output_path.name+'.lock'))
    with lock_path.open('a') as lock, postclose_session(root,source_date):
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('stop_experiment_manifest_publisher_busy') from exc
        code_sha=post.code_sha()
        sources=post.sources(root,source_date)
        inventory={str(path):byte_generation(_safe_path(path)) for path in sources}
        _verify_inventory(inventory)
        source_sha=digest(inventory)
        if (not isinstance(parent_receipt,dict) or not isinstance(parent_receipt.get('path'),str)
                or byte_generation(_safe_path(parent_receipt['path']))['sha256']!=parent_receipt.get('sha256')):
            raise ValueError('stop_experiment_publication_parent_unverified')
        protected={str(Path(name).absolute()) for name in inventory}|{str(Path(parent_receipt['path']).absolute())}
        authorities={}
        for cell,contract in manifest.items():
            if cell not in parents or not isinstance(contract,dict) or contract.get('cell')!=cell:
                raise ValueError('stop_experiment_manifest_cell_mismatch')
            parent=parents[cell]
            if not isinstance(parent,StopValues):parent=StopValues.parse(parent)
            validate_experiment_v2(contract,parent_sha=digest(asdict(parent)),source_sha=source_sha,
                                   code_sha=code_sha,require_promotion=True)
            require_native_publication_performance(contract)
            authorities[cell]=stop_key_authority(root,target_date,contract['allowed_keys'])
            if authorities[cell]['sha256']!=contract['operator_lock_sha256']:
                raise ValueError('stop_experiment_operator_source_changed')
            protected.update(str(Path(contract[name]['path']).absolute())
                             for name in ('preregistration','source_seal','performance_receipt'))
        if str(output_path) in protected:raise ValueError('stop_experiment_manifest_overlaps_source')
        existing=None
        if output_path.exists():
            prior,prior_sha=bounded_object(output_path,MAX_BYTES)
            if prior==manifest:
                existing=prior_sha
            elif expected_sha256!=prior_sha:
                raise ValueError('stop_experiment_manifest_cas_conflict')
            else:
                # Link the old immutable inode before replacing the public name.
                history=_safe_path(output_path.parent/'manifest_history'/output_path.stem/(prior_sha+'.json'))
                history.parent.mkdir(parents=True,exist_ok=True)
                try:os.link(output_path,history)
                except FileExistsError:
                    if bounded_object(history,MAX_BYTES)[1]!=prior_sha:
                        raise ValueError('stop_experiment_manifest_history_changed')
        elif expected_sha256 is not None:
            raise ValueError('stop_experiment_manifest_cas_conflict')
        if (post.code_sha()!=code_sha or post.sources(root,source_date)!=sources
                or any(byte_generation(Path(name))!=generation for name,generation in inventory.items())
                or byte_generation(_safe_path(parent_receipt['path']))['sha256']!=parent_receipt['sha256']
                or any(stop_key_authority(root,target_date,manifest[cell]['allowed_keys'])!=authority
                       for cell,authority in authorities.items())):
            raise ValueError('stop_experiment_manifest_dependency_changed')
        if existing is None:
            with atomic(output_path,len(raw)):
                fd,name=tempfile.mkstemp(prefix='.stop-manifest-',dir=output_path.parent)
                try:
                    with os.fdopen(fd,'wb') as handle:
                        handle.write(raw);handle.flush();os.fsync(handle.fileno())
                    os.replace(name,output_path)
                    directory_fd=os.open(output_path.parent,os.O_DIRECTORY)
                    try:os.fsync(directory_fd)
                    finally:os.close(directory_fd)
                finally:
                    if os.path.exists(name):os.unlink(name)
        observed,byte_sha=bounded_object(output_path,MAX_BYTES)
        if observed!=manifest:raise ValueError('stop_experiment_manifest_changed')
        receipt=dict(schema='main_stop_experiment_manifest_receipt_v1',path=str(output_path),sha256=byte_sha,
            source_date=source_date,target_date=target_date,cells=sorted(manifest),source_sha256=source_sha,
            code_sha256=code_sha,parent_receipt=_plain(parent_receipt),
            allowed_runtime_apply=False,target_policy_published=False)
        receipt['receipt_sha256']=digest(receipt)
        _write_immutable(output_path.parent/'manifest_receipts'/(receipt['receipt_sha256']+'.json'),receipt,'receipt_sha256')
        return receipt


def main():
    """Explicit-output prospective manifest producer; never run postclose."""
    import argparse
    from src.engine.automation import main_stop_postclose as post
    parser=argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--data-root',required=True);parser.add_argument('--date',required=True)
    parser.add_argument('--target',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--contract',action='append',required=True)
    parser.add_argument('--expected-sha256')
    args=parser.parse_args()
    contracts={}
    for name in args.contract:
        contract,_=bounded_object(_safe_path(name),MAX_BYTES)
        cell=contract.get('cell')
        if not isinstance(cell,str) or cell in contracts:raise ValueError('stop_experiment_manifest_cell_mismatch')
        contracts[cell]=contract
    parents,parent=post.baseline(Path(args.data_root),args.target)
    receipt=publish_experiment_manifest(args.output,contracts,data_root=args.data_root,
        source_date=args.date,target_date=args.target,parents=parents,parent_receipt=parent,
        expected_sha256=args.expected_sha256)
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':main()
