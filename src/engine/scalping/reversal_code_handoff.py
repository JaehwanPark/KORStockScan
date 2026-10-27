"""Exact reviewed code compatibility for an already-active Main policy.

Scalping validates policy sources; deployment owns the dated receipt. This
never selects a policy or changes thresholds, memberships, or order authority.
"""

from __future__ import annotations
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA = "main_active_policy_code_handoff_v1"
AUTHORITY = "APPROVED_REVIEWED_ACTIVE_POLICY_CODE_HANDOFF"


def code_hashes():
    from src.engine.scalping.continuous_reversal_policy_v6 import contract_modules

    return {
        str(Path(m.__file__).resolve()): P.file_hash(m.__file__)
        for m in contract_modules()
    } | {str(Path(__file__).resolve()): P.file_hash(__file__)}


def path(data_root, day, commit, bundle_sha):
    return (
        Path(data_root)
        / "runtime/mechanistic_entry_policy/code_handoffs"
        / day
        / commit
        / (bundle_sha + ".json")
    )


def validate_receipt(receipt, *, day, commit, root, bundle_sha, pointer_sha):
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("authority") != AUTHORITY
        or receipt.get("artifact_content_sha256")
        != P.seal(receipt)["artifact_content_sha256"]
        or receipt.get("target_date") != day
        or receipt.get("release_commit") != commit
        or receipt.get("release_root") != str(root)
        or receipt.get("bundle_sha256") != bundle_sha
        or receipt.get("current_pointer_sha256") != pointer_sha
        or receipt.get("policy_reselected") is not False
        or receipt.get("provider_called") is not False
        or not receipt.get("source_hashes")
        or not receipt.get("code_hashes")
    ):
        raise ValueError("active_policy_code_handoff_invalid")
    return receipt


def _validated_origin_receipt(
    data_root, day, origin_root, origin_commit, bundle_sha, pointer_sha
):
    """Reuse native sealed ancestry under the approved pipeline-reference scope."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    source = path(data_root, day, origin_commit, bundle_sha)
    if not source.exists():
        return None
    receipt = N._read(source)
    validate_receipt(
        receipt,
        day=day,
        commit=origin_commit,
        root=origin_root,
        bundle_sha=bundle_sha,
        pointer_sha=pointer_sha,
    )
    for name, expected in {
        **receipt["source_hashes"],
        **receipt["code_hashes"],
    }.items():
        if not N.source_receipt_matches(
            dict(path=name, sha256=expected), data_root=data_root
        ):
            raise ValueError("active_policy_origin_receipt_source_changed:" + name)
    refs = {**receipt["source_hashes"], **receipt["code_hashes"]}
    refs[str(source.resolve())] = P.file_hash(source)
    return dict(
        bundle_sha256=bundle_sha,
        source_hashes=refs,
        verification_basis="native_sealed_code_handoff_pipeline_references",
    )


def validate(bundle, data_root, *, original_error):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release

    day = datetime.now(P.KST).date().isoformat()
    root, commit = selected_release(Path(data_root).resolve().parent)
    # Include the selector in the native dependency cache; a later selection
    # cannot keep the preceding compatibility result alive.
    selection = N._read(Path(data_root) / "runtime/runtime_release_selection.json")
    if selection.get("git_commit") != commit or selection.get("release_root") != str(
        root
    ):
        raise ValueError("active_policy_code_selection_changed")
    selected_root, selected_commit = root, commit
    review = None
    if root != Path(__file__).resolve().parents[3]:
        from src.engine.automation import intraday_release_handoff as handoff

        review = handoff._PREDECESSOR_REVIEW.get()
        if (
            review is None
            and selection.get("main_start_authorized") is False
            and selection.get("approval_scope")
            == "after_postclose_deploy_for_next_regular_start"
        ):
            # Source-only recovery of an unconsumed cold release authenticates
            # both native parent receipts before using a repaired reader.
            with handoff.stopped_postclose_review(selection["next_operating_date"]):
                return validate(bundle, data_root, original_error=original_error)
        if not handoff.predecessor_review_matches(
            review, day, root, commit, Path(__file__).resolve().parents[3]
        ):
            raise ValueError("active_policy_code_reader_root_changed")
        root, commit = review["code_root"], review["code_commit"]
        observation = review.get("postclose_observation") or {}
        family = bundle.get("continuous_reversal") or {}
        if (
            family.get("schema") == "continuous_reversal_policy_v6"
            and family.get("release_commit") == selected_commit
            and bundle.get("target_date") == observation.get("prepared_target_date")
            and bundle.get("source_date")
            == bundle.get("publication_date")
            == observation.get("source_date")
            and observation.get("runtime_effect") is False
            and observation.get("actual_pid_consumed") is False
            and observation.get("allowed_runtime_apply") is False
        ):
            # The stopped review authenticates the selected issuer separately
            # from this preparation reader. Validate the original future
            # policy in that issuer, then its complete reviewed code delta.
            from src.engine.scalping import continuous_reversal_policy_v6 as V

            modules = V.contract_modules()
            paths = {
                Path(m.__file__).name: str(Path(m.__file__).resolve().relative_to(root))
                for m in modules
            }
            if len(paths) != len(modules) or set(paths) != set(
                family["contract_file_sha256"]
            ):
                raise ValueError("prepared_main_code_membership_changed")
            N._validate_bundle_sources(
                bundle, data_root, historical_code_root=selected_root
            )
            handoff._verify_entry_code_delta(
                root,
                commit,
                selected_commit,
                paths,
                N.digest(family["contract_file_sha256"]),
            )
            if selected_release(Path(data_root).resolve().parent) != (
                selected_root,
                selected_commit,
            ) or not handoff.predecessor_review_matches(
                review, day, selected_root, selected_commit, root
            ):
                raise ValueError("prepared_main_reader_generation_changed")
            return bundle
    # The authenticated review uses its own dated receipt. Requiring a second
    # receipt for the unchanged selected code would prevent a midnight review.
    receipt_day = day
    receipt_path = path(data_root, receipt_day, commit, bundle["bundle_sha256"])
    if not receipt_path.exists() and review is None:
        # Publication and activation are different dates. Resolve only this
        # selection's exact issued receipt, never scan for a usable PASS.
        try:
            issued = datetime.fromisoformat(str(selection.get("selected_at_kst") or ""))
        except ValueError:
            raise original_error from None
        current_parent = N._read(N.root(Path(data_root)) / "current.json")
        parent_effective = current_parent.get("effective_date")
        cold = (
            selection.get("approval_scope")
            == "after_postclose_deploy_for_next_regular_start"
        )
        source = selection.get("source_date") if cold else bundle.get("source_date")
        if (
            issued.tzinfo is not None
            and selection.get("approved_by") == "user"
            and selection.get("approval_scope")
            in {
                "after_postclose_deploy_for_next_regular_start",
                "ordered_intraday_deploy_and_restart",
            }
            and (
                not cold
                or (
                    selection.get("actual_pid_consumed") is False
                    and selection.get("main_start_authorized") is False
                    and selection.get("next_operating_date") == day
                )
            )
            and current_parent.get("bundle_sha256") == bundle["bundle_sha256"]
            and isinstance(source, str)
            and source < day
            and isinstance(parent_effective, str)
            and parent_effective < day
        ):
            receipt_day = issued.astimezone(P.KST).date().isoformat()
            receipt_path = path(data_root, receipt_day, commit, bundle["bundle_sha256"])
            if receipt_day >= day or not receipt_path.exists():
                raise original_error
            scheduled = N._read(receipt_path)
            if (
                day not in {scheduled.get("activation_date"), scheduled.get("next_activation_date")}
                or scheduled.get("source_trading_date") != source
                or scheduled.get("parent_effective_date") != parent_effective
            ):
                raise original_error
    # Preserve the native reason for unregistered code and tomorrow's parent
    # transition. There is no generic historical-loader fallback.
    if not receipt_path.exists():
        raise original_error
    if root != Path(__file__).resolve().parents[3]:
        raise ValueError("active_policy_code_reader_root_changed")
    pointer = N.root(Path(data_root)) / "current.json"
    pointer_sha = N._source_hash(str(pointer), N._signature(pointer))
    r = N._read(receipt_path)
    validate_receipt(
        r,
        day=receipt_day,
        commit=commit,
        root=root,
        bundle_sha=bundle["bundle_sha256"],
        pointer_sha=pointer_sha,
    )
    if review is not None and (
        r.get("origin_root") != str(selected_root)
        or r.get("origin_commit") != selected_commit
        or r.get("origin_selection_sha256")
        != P.file_hash(Path(data_root) / "runtime/runtime_release_selection.json")
        or r.get("actual_pid_consumed") is not False
    ):
        raise ValueError("active_policy_predecessor_review_unbound")
    current = {
        str(Path(m.__file__).resolve())
        for m in __import__(
            "src.engine.scalping.continuous_reversal_policy_v6",
            fromlist=["contract_modules"],
        ).contract_modules()
    } | {str(Path(__file__).resolve())}
    if set(r["code_hashes"]) != current:
        raise ValueError("active_policy_code_membership_changed")
    for name, expected in {**r["source_hashes"], **r["code_hashes"]}.items():
        if not N.source_receipt_matches(
            dict(path=name, sha256=expected), data_root=data_root
        ):
            raise ValueError("active_policy_code_handoff_source_changed:" + name)
    if N._read(pointer)["bundle_sha256"] != bundle["bundle_sha256"]:
        raise ValueError("active_policy_code_handoff_pointer_changed")
    if receipt_day != day and (
        selected_release(Path(data_root).resolve().parent)
        != (selected_root, selected_commit)
        or N._read(Path(data_root) / "runtime/runtime_release_selection.json")
        != selection
        or N._read(receipt_path) != r
    ):
        raise ValueError("active_policy_activation_handoff_changed")
    if review is not None and (
        selected_release(Path(data_root).resolve().parent)
        != (selected_root, selected_commit)
        or N._read(Path(data_root) / "runtime/runtime_release_selection.json")
        != selection
        or not handoff.predecessor_review_matches(
            review,
            day,
            selected_root,
            selected_commit,
            Path(__file__).resolve().parents[3],
        )
    ):
        raise ValueError("active_policy_predecessor_review_changed")
    return bundle


_ORIGIN_SCRIPT = r"""
import sys,json,hashlib
from pathlib import Path
from src.engine.scalping import mechanistic_entry_runtime_policy as N
root=Path(sys.argv[1]).resolve();day=sys.argv[2];opened={}
def audit(event,args):
    if event!='open' or not isinstance(args[0],str):return
    p=Path(args[0]).absolute()
    if root not in p.parents or not p.is_file():return
    st=p.stat();opened.setdefault(str(p),(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns))
sys.addaudithook(audit)
# A still-closed session has an explicit native code-refresh preparation.
# Authenticate that frozen generation and active parent by role, rather than
# guessing the policy backend from a live-loader exception string.
current=N._read(N.root(root)/'current.json')
candidate_path=N.root(root)/'candidates'/('policy_'+day+'.json')
candidate=N._read(candidate_path) if current.get('effective_date','')<day and candidate_path.is_file() else {}
f=candidate.get('continuous_reversal') or {}
proof=f.get('code_refresh') or {}
prepared_parent=(current.get('effective_date','')<day
    and f.get('effective_date')==day and f.get('effective_mode')=='next_session'
    and proof.get('authority')=='reviewed_identical_policy_code_refresh')
prepared_refs=None
if prepared_parent:
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_code_handoff as H
    N.validate(candidate,target_date=day)
    f=candidate.get('continuous_reversal') or {}
    proof=f.get('code_refresh') or {}
    if (f.get('schema')!=V.SCHEMA or f.get('effective_mode')!='next_session'
            or f.get('effective_date')!=day or f.get('publication_date','')>=day
            or proof.get('authority')!=V.CODE_REFRESH_AUTHORITY):
        raise ValueError('active_policy_code_handoff_rollover_candidate_invalid')
    frozen=N._read(N.root(root)/'generations'/(candidate['bundle_sha256']+'.json'))
    if frozen!=candidate:
        raise ValueError('active_policy_code_handoff_rollover_generation_changed')
    N._validate_bundle_sources(frozen,root)
    b=V._attested_activation_parent(root,day,
        origin_root=proof['activation_parent_origin_root'],
        origin_commit=proof['activation_parent_origin_commit'])
    current=N._read(N.root(root)/'current.json')
    if b is None or b['bundle_sha256']!=current['bundle_sha256'] or b['bundle_sha256']!=f['parent_bundle_sha256']:
        raise ValueError('active_policy_code_handoff_rollover_parent_changed')
    # The native parent validator runs in the original immutable release.
    # Export its verified closure explicitly: auditing this process cannot
    # observe that child, and future evaluation caches are not parent inputs.
    pointer=N.root(root)/'current.json'
    anchored=H._validated_origin_receipt(root,b['target_date'],
        Path(proof['activation_parent_origin_root']),proof['activation_parent_origin_commit'],
        b['bundle_sha256'],H.P.file_hash(pointer))
    if anchored is None:raise ValueError('active_policy_code_handoff_rollover_parent_receipt_missing')
    generation=N.root(root)/'generations'/(candidate['bundle_sha256']+'.json')
    prepared_refs={**anchored['source_hashes'],str(generation):H.P.file_hash(generation),str(pointer):H.P.file_hash(pointer)}
    if N._read(generation)!=candidate:raise ValueError('active_policy_code_handoff_rollover_generation_changed')
else:
    b=N._load_current_uncached(root,day)
refs={} if prepared_refs is None else prepared_refs
for name,identity in (list(opened.items()) if prepared_refs is None else []):
    p=Path(name);st=p.stat()
    if identity!=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns):raise ValueError('origin_source_changed_during_validation')
    refs[name]=N._source_hash(name,N._signature(p))
print(json.dumps(dict(bundle_sha256=b['bundle_sha256'],source_hashes=refs)))
"""


def _stopped_origin_receipt(
    data_root, day, origin_root, origin_commit, bundle_sha, pointer_sha
):
    """Recover only the native ancestry of an exact failed selected transition."""
    from src.engine.automation import ordered_intraday_deploy as D

    workspace = Path(data_root).resolve().parent
    selected, selected_raw, _ = D._owned_metadata(
        Path(data_root) / "runtime/runtime_release_selection.json"
    )
    failed_path = (
        Path(data_root)
        / "runtime/release_transitions"
        / day
        / origin_commit
        / "status.json"
    )
    failed, failed_raw, _ = D._owned_metadata(failed_path)
    prior_path = failed_path.with_name("selection-before.json")
    prior, prior_raw, _ = D._owned_metadata(prior_path)
    hold, hold_raw, _ = D._owned_metadata(
        Path(data_root) / "runtime/operator_startup_hold.json"
    )
    identity = failed.get("predecessor_identity")
    preparation_sources = D.stopped_preparation_failure_sources(failed, failed_path)
    expected_hold = dict(
        schema="ordered_deployment_startup_hold_v1",
        authority=D.CONFIRM,
        transition=str(failed_path),
        target_date=day,
        candidate_commit=origin_commit,
        old_pid_identity=identity,
    )
    if (
        selected.get("actual_pid_consumed") is not False
        or selected.get("git_commit") != origin_commit
        or selected.get("release_root") != str(origin_root)
        or selected.get("deployment_transition") != str(failed_path)
        or selected.get("approval_scope") != "ordered_intraday_deploy_and_restart"
        or selected.get("approved_by") != "user"
        or hold != expected_hold
        or failed.get("schema") != "ordered_intraday_deployment_v1"
        or failed.get("authority") != D.CONFIRM
        or failed.get("phase") != "failed"
        or failed.get("status") != "fail"
        or (failed.get("failed_phase") != "selected" and not preparation_sources)
        or failed.get("target_date") != day
        or failed.get("candidate_commit") != origin_commit
        or failed.get("candidate_root") != str(origin_root)
        or (
            failed.get("error")
            != "deployment_validation_failed:src.engine.automation.intraday_release_handoff"
            and not preparation_sources
        )
        or failed.get("policy_effect") != "unchanged"
        or failed.get("original_selection_sha256") != D._digest(prior_raw)
        or prior.get("actual_pid_consumed") is not True
        or prior.get("git_commit") != failed.get("previous_commit")
        or prior.get("release_root") != failed.get("previous_root")
        or not isinstance(identity, dict)
        or (prior.get("actual_pid_receipt") or {}).get("pid") != identity.get("pid")
        or D._main_pids()
        or not D._session_absent()
        or (workspace / "restart.flag").exists()
        or (workspace / "restart.flag").is_symlink()
    ):
        raise ValueError("active_policy_stopped_origin_invalid")
    previous, previous_commit = D.R.validate_release(workspace, prior)
    if selected.get("native_predecessor_path"):
        proof = D.H._native_predecessor(
            day,
            origin_commit,
            previous,
            previous_commit,
            identity,
            selected["native_predecessor_path"],
            selected.get("native_predecessor_sha256"),
        )
    else:
        proof = D._stopped_intraday_predecessor(
            day, previous, previous_commit, identity, failed_path
        )
    if selected.get("native_predecessor_path"):
        # The original native Main need not own an intraday compatibility
        # receipt. Authenticate the already-issued failed candidate receipt,
        # which binds that Main's original selector and active parent.
        issued_path = path(data_root, day, origin_commit, bundle_sha)
        issued, issued_raw, _ = D._owned_metadata(issued_path)
        checked = _validated_origin_receipt(
            data_root, day, origin_root, origin_commit, bundle_sha, pointer_sha
        )
        if (
            checked is None
            or issued.get("origin_root") != str(previous)
            or issued.get("origin_commit") != previous_commit
            or issued.get("origin_selection_sha256") != D._digest(prior_raw)
            or checked["source_hashes"].get(str(issued_path.resolve()))
            != D._digest(issued_raw)
        ):
            raise ValueError("active_policy_stopped_native_ancestry_missing")
    else:
        checked = _validated_origin_receipt(
            data_root, day, previous, previous_commit, bundle_sha, pointer_sha
        )
    if checked is None:
        raise ValueError("active_policy_stopped_native_ancestry_missing")
    # The hold and selector are observed transition state, never frozen policy inputs.
    if (
        D._owned_metadata(Path(data_root) / "runtime/runtime_release_selection.json")[1]
        != selected_raw
        or D._owned_metadata(Path(data_root) / "runtime/operator_startup_hold.json")[1]
        != hold_raw
        or failed_path.read_bytes() != failed_raw
        or prior_path.read_bytes() != prior_raw
        or D._main_pids()
        or not D._session_absent()
    ):
        raise ValueError("active_policy_stopped_origin_changed")
    if any(D.H._sha(path) != sha for path, sha in preparation_sources.items()):
        raise ValueError("active_policy_stopped_preparation_changed")
    checked["source_hashes"].update(preparation_sources)
    checked["source_hashes"].update(proof["frozen_files"])
    checked["source_hashes"].update(
        {str(failed_path): D._digest(failed_raw), str(prior_path): D._digest(prior_raw)}
    )
    checked["verification_basis"] = (
        "verified_stopped_transition_original_native_code_ancestry"
    )
    return checked

def _postclose_origin_receipt(
    data_root,
    day,
    source_date,
    origin_root,
    origin_commit,
    bundle_sha,
    pointer_sha,
    release_commit,
):
    """Bridge the closed trading interval using exact stopped native ancestry.

    This is code-only custody for the unchanged active parent. It neither
    requires nor fabricates the downstream next-session policy/PREOPEN.
    """
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.utils.market_day import is_krx_trading_day, next_krx_trading_date

    root = Path(data_root).resolve()
    workspace = root.parent
    source_day = datetime.fromisoformat(source_date).date()
    observed_day = datetime.fromisoformat(day).date()
    if (
        source_day.isoformat() != source_date
        or observed_day.isoformat() != day
        or not is_krx_trading_day(source_day)
        or source_day >= observed_day
    ):
        raise ValueError("active_policy_postclose_source_date_invalid")
    selected, selected_raw, _ = D._owned_metadata(
        root / "runtime/runtime_release_selection.json"
    )
    next_day = selected.get("next_operating_date")
    try:
        canonical = datetime.fromisoformat(next_day).date().isoformat()
    except (TypeError, ValueError):
        raise ValueError("active_policy_postclose_next_date_invalid") from None

    def stopped():
        return (
            not D._main_pids()
            and D._session_absent()
            and not (workspace / "restart.flag").exists()
            and not (workspace / "restart.flag").is_symlink()
            and not (root / "runtime/operator_startup_hold.json").exists()
            and not (root / "runtime/operator_startup_hold.json").is_symlink()
        )

    scope = selected.get("approval_scope")
    transition_refs = {}
    if scope == "postclose_recovery_before_next_regular_start":
        # The original cold caller used this label before the midnight bridge.
        # Authenticate its native committed transaction, original consumption
        # and original candidate P5; never rewrite that historical selector.
        from src.engine.infrastructure import research_release_transition as T

        backup = Path(selected.get("previous_selection_backup", ""))
        directory = backup.parent
        if (
            not backup.is_absolute()
            or directory.parent != root / "runtime/research_release_transition"
            or directory.resolve() != directory
            or backup.is_symlink()
        ):
            raise ValueError("active_policy_postclose_transition_path_invalid")
        transition_path = directory / "transition.json"
        transition, transition_raw, transition_identity = D._owned_metadata(
            transition_path
        )
        if T._record(transition_path) != transition:
            raise ValueError("active_policy_postclose_transition_changed")
        entries = transition.get("entries") or []
        if (
            transition.get("state") != "verified"
            or transition.get("transition_id") != directory.name
            or len(entries) != 1
            or transition.get("written")
            != [str(root / "runtime/runtime_release_selection.json")]
        ):
            raise ValueError("active_policy_postclose_transition_invalid")
        entry = entries[0]
        before, before_raw, before_identity = D._owned_metadata(backup)
        after_path = directory / str(entry.get("after_snapshot", ""))
        if (
            entry.get("path") != str(root / "runtime/runtime_release_selection.json")
            or entry.get("before_snapshot") != backup.name
            or entry.get("before_sha256") != D._digest(before_raw)
            or selected.get("predecessor_selection_sha256") != D._digest(before_raw)
            or entry.get("after_sha256") != D._digest(selected_raw)
            or set(entry.get("accepted_sha256") or [])
            != {D._digest(before_raw), D._digest(selected_raw)}
            or after_path.parent != directory
            or after_path.name != "after-" + D._digest(selected_raw) + ".bytes"
            or before.get("actual_pid_consumed") is not True
            or before.get("git_commit") != selected.get("previous_git_commit")
            or before.get("release_root") != selected.get("previous_release_root")
        ):
            raise ValueError("active_policy_postclose_transition_binding_invalid")
        after, after_raw, after_identity = D._owned_metadata(after_path)
        proof_path = Path(selected.get("candidate_p5_path", ""))
        if (
            not proof_path.is_absolute()
            or proof_path.resolve() != proof_path
            or proof_path.parent.parent
            != root / "report/main_startup_validation" / source_date
            or proof_path.name != "final.json"
        ):
            raise ValueError("active_policy_postclose_original_p5_path_invalid")
        proof, proof_raw, proof_identity = D._owned_metadata(proof_path)
        if (
            after_raw != selected_raw
            or D._digest(proof_raw) != selected.get("candidate_p5_sha256")
            or proof.get("schema") != "main_policy_load_exit_validation_v1"
            or proof.get("status") != "passed"
            or proof.get("findings") != []
            or proof.get("target_date") != source_date
            or proof.get("execution_release_root") != str(origin_root)
            or proof.get("execution_release_commit") != origin_commit
            or any(
                proof.get(k) is not True
                for k in (
                    "child_terminated",
                    "load_check_passed",
                    "protected_sources_unchanged",
                )
            )
        ):
            raise ValueError("active_policy_postclose_original_p5_invalid")
        for p, raw, identity in (
            (transition_path, transition_raw, transition_identity),
            (backup, before_raw, before_identity),
            (after_path, after_raw, after_identity),
            (proof_path, proof_raw, proof_identity),
        ):
            if D._owned_metadata(p)[1:] != (raw, identity):
                raise ValueError("active_policy_postclose_transition_changed")
            transition_refs[str(p)] = D._digest(raw)
        scope = "after_postclose_deploy_for_next_regular_start"
    if (
        not stopped()
        or selected.get("git_commit") != origin_commit
        or selected.get("release_root") != str(origin_root)
        or selected.get("source_date") != source_date
        or selected.get("approved_by") != "user"
        or scope != "after_postclose_deploy_for_next_regular_start"
        or selected.get("actual_pid_consumed") is not False
        or next_day != canonical
        or next_day != next_krx_trading_date(source_day).isoformat()
        or next_day < day
    ):
        raise ValueError("active_policy_postclose_stopped_origin_invalid")
    checked = _validated_origin_receipt(
        root, source_date, origin_root, origin_commit, bundle_sha, pointer_sha
    )
    if checked is None:
        # A previously selected cold successor issued its own receipt on the
        # selection day, not the historical source day. Resolve that one exact
        # native receipt; never scan for a later/older usable policy proof.
        try:
            selected_at = datetime.fromisoformat(selected["selected_at_kst"])
            if selected_at.tzinfo is None:
                raise ValueError("offset_missing")
            selected_day = selected_at.astimezone(P.KST).date().isoformat()
            if not source_date < selected_day <= day or selected_day > next_day:
                raise ValueError("outside_closed_interval")
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "active_policy_postclose_selection_clock_invalid"
            ) from None
        original = path(root, selected_day, origin_commit, bundle_sha)
        original_body, original_raw, original_identity = D._owned_metadata(original)
        declared_source = original_body.get("postclose_source_date") or original_body.get(
            "source_trading_date"
        )
        if declared_source is None:
            # Legacy same-day receipts did not declare the next activation.
            # Revalidate their native parent scope before issuing a new proof;
            # they remain ineligible for cross-date runtime consumption.
            parent = N._read(
                N.root(root) / "generations" / (bundle_sha + ".json")
            )
            N.validate(parent, target_date=source_date)
            pointer = N._read(N.root(root) / "current.json")
            if (
                parent.get("bundle_sha256") != bundle_sha
                or parent.get("target_date") != source_date
                or pointer.get("effective_date") != source_date
                or pointer.get("bundle_sha256") != bundle_sha
            ):
                raise ValueError("active_policy_postclose_ancestry_source_invalid")
        elif declared_source != source_date:
            raise ValueError("active_policy_postclose_ancestry_source_invalid")
        checked = _validated_origin_receipt(
            root, selected_day, origin_root, origin_commit, bundle_sha, pointer_sha
        )
        if D._owned_metadata(original)[1:] != (original_raw, original_identity):
            raise ValueError("active_policy_postclose_origin_changed")
    if checked is None:
        raise ValueError("active_policy_postclose_native_ancestry_missing")
    paths = [
        root
        / "runtime/update_kospi_status"
        / ("update_kospi_" + source_date + ".json"),
        root
        / "report/threshold_cycle_postclose_status"
        / ("threshold_cycle_postclose_" + source_date + ".status.json"),
    ]
    observed = [D._owned_metadata(p) for p in paths]
    eod, failed = (v[0] for v in observed)
    state = eod.get("db_state") or {}
    import re

    if (
        eod.get("schema_version") != 1
        or eod.get("target_date") != source_date
        or eod.get("status") not in {"completed", "completed_with_warnings"}
        or eod.get("failed_steps") != []
        or state.get("latest_quote_date") != source_date
        or type(state.get("rows_on_latest_date")) is not int
        or state["rows_on_latest_date"] <= 0
        or failed.get("report_type") != "threshold_cycle_postclose_status"
        or failed.get("target_date") != source_date
        or failed.get("schema_version") != 2
        or not isinstance(failed.get("run_id"), str)
        or re.fullmatch("[0-9a-f]{32}", failed["run_id"]) is None
        or type(failed.get("exit_code")) is not int
        or failed.get("runtime_effect") is not False
    ):
        raise ValueError("active_policy_postclose_terminal_evidence_invalid")
    terminal_refs = {}
    if failed.get("status") == "failed":
        if failed["exit_code"] == 0 or failed.get("code_commit") != origin_commit:
            raise ValueError("active_policy_postclose_terminal_evidence_invalid")
    elif failed.get("status") == "succeeded" and failed["exit_code"] == 0:
        # A completed calculation may still require a detector-only code repair.
        # Authenticate its existing workflow and whole-chain owner; never turn
        # a stored success string into a new completion or PID observation.
        workflow = failed.get("workflow_source") or {}
        workflow_root = Path(workflow.get("root", ""))
        script = workflow_root / "deploy/run_threshold_cycle_postclose.sh"
        report_path = (
            root
            / "report/postclose_done_controller"
            / ("postclose_done_controller_" + source_date + ".json")
        )
        if (
            failed.get("reason") != "verified_main_completed"
            or not workflow_root.is_absolute()
            or workflow_root.resolve() != workflow_root
            or workflow.get("script") != str(script)
            or workflow.get("sha256") != P.file_hash(script)
        ):
            raise ValueError("active_policy_postclose_workflow_evidence_invalid")
        if workflow_root == origin_root:
            if workflow.get("commit") != origin_commit:
                raise ValueError("active_policy_postclose_workflow_evidence_invalid")
        else:
            # The calculation can predate a code-only cold selection. Its
            # immutable workflow must already belong to the verified parent's
            # native closure; neither a path nor today's Git alone proves it.
            from src.engine.infrastructure.runtime_release_router import (
                validate_release,
            )

            if checked["source_hashes"].get(str(script)) != workflow["sha256"]:
                raise ValueError("active_policy_postclose_workflow_ancestry_missing")
            validate_release(
                workspace,
                dict(
                    schema="runtime_release_selection_v1",
                    workspace=str(workspace),
                    release_root=str(workflow_root),
                    git_commit=workflow.get("commit"),
                ),
            )
        report, report_raw, report_identity = D._owned_metadata(report_path)
        # The selected predecessor owns this terminal. Running its verification
        # in candidate code would demand the successor receipt being issued.
        script_code = """from pathlib import Path
import json,sys
from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
from src.engine.infrastructure.validation_digest_session import postclose_session
with postclose_session(Path(sys.argv[1]),sys.argv[2]):
    print(json.dumps(done_terminal_receipt_issues(Path(sys.argv[3]),sys.argv[2],started_after_ns=0)))
"""
        issues = json.loads(
            subprocess.check_output(
                [
                    str(origin_root / ".venv/bin/python"),
                    "-B",
                    "-c",
                    script_code,
                    str(root),
                    source_date,
                    str(report_path),
                ],
                cwd=origin_root,
                env={**os.environ, "PYTHONPATH": str(origin_root)},
                text=True,
                timeout=300,
            )
        )
        if (
            report.get("main_run_id") != failed["run_id"]
            or issues != []
            or D._owned_metadata(report_path)[1:] != (report_raw, report_identity)
        ):
            raise ValueError("active_policy_postclose_completed_evidence_invalid")
        for name in (
            Path(report["attempt_path"]),
            Path(report["verification_attempt_path"]),
            script,
        ):
            terminal_refs[str(name)] = P.file_hash(name)
    else:
        raise ValueError("active_policy_postclose_terminal_evidence_invalid")
    # Mutable observed aliases must not invalidate the issued code handoff when
    # the repaired postclose producer naturally publishes its next attempt.
    frozen = (
        path(root, day, release_commit, bundle_sha).with_suffix("") / "postclose_origin"
    )
    if any(p.is_symlink() for p in (frozen, *frozen.parents)):
        raise ValueError("active_policy_postclose_evidence_path_invalid")
    frozen.mkdir(parents=True, exist_ok=True)
    refs = {}
    for original, (_, raw, identity) in zip(paths, observed):
        destination = frozen / original.name
        if destination.exists() or destination.is_symlink():
            if D._owned_metadata(destination)[1] != raw:
                raise ValueError("active_policy_postclose_frozen_evidence_conflict")
        else:
            with destination.open("xb") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        if D._owned_metadata(original)[1:] != (raw, identity):
            raise ValueError("active_policy_postclose_evidence_changed")
        refs[str(destination)] = D._digest(raw)
    if (
        D._owned_metadata(root / "runtime/runtime_release_selection.json")[1]
        != selected_raw
        or not stopped()
    ):
        raise ValueError("active_policy_postclose_origin_changed")
    checked["source_hashes"].update(refs | transition_refs | terminal_refs)
    checked["verification_basis"] = "verified_closed_postclose_native_code_ancestry"
    return checked


def issue(
    data_root,
    day,
    *,
    origin_root,
    release_root,
    parity_path,
    confirm,
    recover_stopped_origin=False,
    postclose_source_date=None,
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.infrastructure.runtime_release_router import (
        selected_release,
        validate_release,
        git,
    )

    issued_at = datetime.now(P.KST)
    if (
        confirm != AUTHORITY
        or day != issued_at.date().isoformat()
        or postclose_source_date is not None
        and recover_stopped_origin is not False
    ):
        raise ValueError("active_policy_code_handoff_authority_required")
    workspace = Path(data_root).resolve().parent
    origin_root = Path(origin_root).resolve()
    release_root = Path(release_root).resolve()
    selected, previous = selected_release(workspace)
    if selected != origin_root or release_root != Path(__file__).resolve().parents[3]:
        raise ValueError("active_policy_code_handoff_origin_changed")
    selection_path = workspace / "data/runtime/runtime_release_selection.json"
    selection_before = selection_path.read_bytes()
    selection = json.loads(selection_before)
    from datetime import date
    from src.utils.market_day import next_krx_trading_date
    activation_date = day
    next_activation_date = next_krx_trading_date(date.fromisoformat(day)).isoformat()
    source_trading_date = None
    cold = (selection.get("approval_scope") == "after_postclose_deploy_for_next_regular_start"
            and selection.get("actual_pid_consumed") is False)
    if cold:
        source_trading_date = selection["source_date"]
        activation_date = selection["next_operating_date"]
        next_activation_date = activation_date
        if (
            selection.get("approved_by") != "user"
            or selection.get("actual_pid_consumed") is not False
            or next_krx_trading_date(date.fromisoformat(source_trading_date)).isoformat()
            != activation_date
            or not source_trading_date <= day <= activation_date
        ):
            raise ValueError("active_policy_code_activation_date_invalid")
    selection_sha = P.file_hash(selection_path)
    commit = git(release_root, "rev-parse", "HEAD")
    validate_release(
        workspace,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(workspace),
            release_root=str(release_root),
            git_commit=commit,
        ),
    )
    pointer = N.root(Path(data_root)) / "current.json"
    before = pointer.read_bytes()
    ptr = json.loads(before)
    bundle = N._read(
        N.root(Path(data_root)) / "generations" / (ptr["bundle_sha256"] + ".json")
    )
    if not cold:
        source_trading_date = bundle.get("source_date")
    N.validate(bundle, target_date=bundle["target_date"])
    parity = json.loads(Path(parity_path).read_text())
    codes = code_hashes()
    expected = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    if (
        parity.get("status") != "pass"
        or parity.get("mismatches") != 0
        or parity.get("parent_bundle_sha256") != bundle["bundle_sha256"]
        or parity.get("contract_file_sha256") != expected
        or not parity.get("confirmation_parity", {}).get("hits")
    ):
        raise ValueError("active_policy_code_handoff_parity_invalid")
    if any(
        d != C.definition(b)
        for b, d in bundle["continuous_reversal"]["operating_manifest"][
            "definitions"
        ].items()
    ):
        raise ValueError("active_policy_code_handoff_definition_changed")
    checked = _validated_origin_receipt(
        data_root,
        day,
        origin_root,
        previous,
        bundle["bundle_sha256"],
        P.file_hash(pointer),
    )
    closed_parent = None
    if (
        checked is None
        and recover_stopped_origin is False
        and postclose_source_date is None
        and selection.get("approval_scope") == "ordered_intraday_deploy_and_restart"
        and selection.get("actual_pid_consumed") is True
        and ptr.get("effective_date", day) < day
    ):
        from src.engine.automation import intraday_release_handoff as H
        from src.engine.automation import ordered_intraday_deploy as D
        from src.engine.automation.next_preopen_readiness import target_after_postclose

        closed_parent = H.closed_consumption_observation()
        if (
            selection.get("approved_by") != "user"
            or selection.get("main_start_authorized") is not False
            or closed_parent.get("schema")
            != "intraday_closed_consumption_observation_v1"
            or closed_parent.get("basis") is not None
            or any(
                closed_parent.get(key) is not False
                for key in (
                    "runtime_effect",
                    "current_observation_verified",
                    "new_pid_consumption_claimed",
                )
            )
            or closed_parent.get("target_date") != ptr["effective_date"]
            or closed_parent.get("release_commit") != previous
            or closed_parent.get("selection_sha256") != selection_sha
            or target_after_postclose(ptr["effective_date"]) != day
            or D._main_pids()
            or not D._session_absent()
            or any(
                p.exists() or p.is_symlink()
                for p in (
                    workspace / "restart.flag",
                    workspace / "data/runtime/operator_startup_hold.json",
                )
            )
        ):
            raise ValueError("active_policy_closed_parent_scope_invalid")
        checked = _validated_origin_receipt(
            data_root,
            ptr["effective_date"],
            origin_root,
            previous,
            bundle["bundle_sha256"],
            P.file_hash(pointer),
        )
        if checked is None:
            raise ValueError("active_policy_closed_parent_receipt_missing")
        checked = {
            **checked,
            "verification_basis": "verified_ordered_closed_native_parent",
        }
    if recover_stopped_origin is True:
        checked = _stopped_origin_receipt(
            data_root,
            day,
            origin_root,
            previous,
            bundle["bundle_sha256"],
            P.file_hash(pointer),
        )
    elif recover_stopped_origin is not False:
        raise ValueError("active_policy_stopped_recovery_flag_invalid")
    if postclose_source_date is not None:
        checked = _postclose_origin_receipt(
            data_root,
            day,
            postclose_source_date,
            origin_root,
            previous,
            bundle["bundle_sha256"],
            P.file_hash(pointer),
            commit,
        )
    if checked is None:
        output = subprocess.check_output(
            [
                str(origin_root / ".venv/bin/python"),
                "-B",
                "-c",
                _ORIGIN_SCRIPT,
                str(Path(data_root).resolve()),
                day,
            ],
            cwd=origin_root,
            env={**os.environ, "PYTHONPATH": str(origin_root)},
            text=True,
            timeout=120,
        )
        checked = json.loads(output)
    if (
        checked["bundle_sha256"] != bundle["bundle_sha256"]
        or pointer.read_bytes() != before
        or selection_path.read_bytes() != selection_before
        or closed_parent is not None and H.closed_consumption_observation() != closed_parent
    ):
        raise ValueError("active_policy_code_handoff_parent_changed")
    sources = dict(checked["source_hashes"])
    # A successor of a code-only release observes its predecessor selector.
    # This is transition provenance, not an immutable policy input: validate()
    # independently binds the current selector to this exact candidate root
    # and commit. All policy/source and prior receipt hashes remain frozen.
    observed_selection = sources.pop(str(selection_path.resolve()), None)
    if observed_selection is not None and observed_selection != selection_sha:
        raise ValueError("active_policy_code_handoff_selection_changed")
    # The native transition owner advances this coordination record while
    # publishing. It is observed provenance, like the selector, not policy
    # input. Keep all policy and immutable terminal sources byte-bound.
    coordination = (
        Path(data_root).resolve() / "runtime/research_release_transition/current.json"
    )
    observed_coordination = sources.pop(str(coordination), None)
    transition_observation = None

    def verify_coordination():
        if observed_coordination is None:
            return None
        from src.engine.infrastructure import research_release_transition as T

        if (
            coordination.is_symlink()
            or coordination.parent.resolve() != coordination.parent
        ):
            raise ValueError("active_policy_code_handoff_coordination_path_invalid")
        T.assert_readable(data_root)
        record = T._record(coordination)
        if P.file_hash(coordination) != observed_coordination:
            raise ValueError("active_policy_code_handoff_coordination_changed")
        return dict(
            path=str(coordination),
            sha256=observed_coordination,
            transition_id=record["transition_id"],
            state=record["state"],
        )

    transition_observation = verify_coordination()
    sources[str(Path(parity_path).resolve())] = P.file_hash(parity_path)
    for row in parity.get("targeted_validation", []):
        if P.file_hash(row["path"]) != row["sha256"]:
            raise ValueError("active_policy_code_handoff_test_evidence_changed")
        sources[row["path"]] = row["sha256"]
    r = P.seal(
        dict(
            schema=SCHEMA,
            authority=confirm,
            target_date=day,
            issued_at_kst=issued_at.isoformat(),
            activation_date=activation_date,
            next_activation_date=next_activation_date,
            source_trading_date=source_trading_date,
            parent_effective_date=ptr.get("effective_date"),
            release_commit=commit,
            release_root=str(release_root),
            origin_root=str(origin_root),
            origin_commit=previous,
            bundle_sha256=bundle["bundle_sha256"],
            origin_selection_sha256=selection_sha,
            origin_transition_observation=transition_observation,
            origin_closed_observation=closed_parent,
            current_pointer_sha256=P.file_hash(pointer),
            source_hashes=sources,
            code_hashes=codes,
            pipeline_source_validation=N.PIPELINE_REFERENCE_VALIDATION,
            origin_verification_basis=checked.get(
                "verification_basis", "native_origin_validator"
            ),
            pipeline_source_reference_count=sum(
                N.is_pipeline_source_reference(p, data_root=data_root) for p in sources
            ),
            policy_reselected=False,
            provider_called=False,
            actual_pid_consumed=False,
            source_semantics_repair=True,
            **(
                {"postclose_source_date": postclose_source_date}
                if postclose_source_date is not None
                else {}
            ),
        )
    )
    dest = path(data_root, day, commit, bundle["bundle_sha256"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and N._read(dest) != r:
        raise ValueError("active_policy_code_handoff_receipt_conflict")
    if verify_coordination() != transition_observation:
        raise ValueError("active_policy_code_handoff_coordination_changed")
    N._atomic_write_json(dest, r)
    return r


def issue_activation_rollover(data_root, day, *, verified_receipt, confirm):
    """Issue a failed PREOPEN's exact consumer proof from native parent custody.

    Preserve the immutable original and its consumer code. The already reviewed
    source proof supplies activation intent, not a replacement policy or PID.
    """
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.automation import next_preopen_readiness as Q
    from src.engine.infrastructure import runtime_release_router as R
    import fcntl

    data = Path(data_root).resolve()
    workspace = data.parent
    workflow = Path(__file__).resolve().parents[3]
    if confirm != AUTHORITY:
        raise ValueError("activation_rollover_authority_required")
    workflow_commit = R.git(workflow, "rev-parse", "HEAD")
    R.validate_release(workspace, dict(schema="runtime_release_selection_v1",
        workspace=str(workspace), release_root=str(workflow), git_commit=workflow_commit))
    with (R.scheduled_execution_lease(workspace, exclusive=True),
          R.runtime_release_set_lock(workspace),
          Q.failed_preopen_recovery(day, confirm=Q.RECOVERY_AUTHORITY)):
        with (N.root(data) / "publisher.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            selector = data / "runtime/runtime_release_selection.json"
            selected_raw = selector.read_bytes()
            selected = json.loads(selected_raw)
            consumer, commit = R.selected_release(workspace)
            pointer = N.root(data) / "current.json"
            pointer_raw = pointer.read_bytes()
            current = json.loads(pointer_raw)
            issued = datetime.fromisoformat(selected["selected_at_kst"])
            source = selected.get("source_date")
            if (issued.tzinfo is None or selected.get("approved_by") != "user"
                    or selected.get("approval_scope") != "after_postclose_deploy_for_next_regular_start"
                    or selected.get("actual_pid_consumed") is not False
                    or selected.get("main_start_authorized") is not False
                    or selected.get("next_operating_date") != day
                    or current.get("effective_date") != source
                    or not source < issued.astimezone(P.KST).date().isoformat() < day
                    or D._main_pids() or not D._session_absent()):
                raise ValueError("activation_rollover_stopped_generation_required")
            original_day = issued.astimezone(P.KST).date().isoformat()
            original = path(data, original_day, commit, current["bundle_sha256"])
            original_raw = original.read_bytes()
            old = N._read(original)
            if _validated_origin_receipt(data, original_day, consumer, commit,
                    current["bundle_sha256"], P.file_hash(pointer)) is None:
                raise ValueError("activation_rollover_original_missing")
            proof_path = Path(verified_receipt).resolve(strict=True)
            proof_raw = proof_path.read_bytes()
            proof = N._read(proof_path)
            if (proof_path != path(data, day, proof["release_commit"], current["bundle_sha256"])
                    or proof.get("activation_date") != day
                    or proof.get("source_trading_date") != source
                    or proof.get("origin_root") != str(consumer)
                    or proof.get("origin_commit") != commit
                    or proof.get("actual_pid_consumed") is not False
                    or proof.get("origin_selection_sha256") != P.file_hash(selector)
                    or _validated_origin_receipt(data, day, Path(proof["release_root"]),
                        proof["release_commit"], current["bundle_sha256"], P.file_hash(pointer)) is None):
                raise ValueError("activation_rollover_native_proof_invalid")
            refs = {**old["source_hashes"], str(original): P.file_hash(original),
                    str(proof_path): P.file_hash(proof_path),
                    str(Path(__file__).resolve()): P.file_hash(__file__)}
            result = P.seal(dict(old, target_date=day,
                issued_at_kst=datetime.now(P.KST).isoformat(), activation_date=day,
                next_activation_date=day,
                source_trading_date=source, source_hashes=refs,
                parent_effective_date=current.get("effective_date"),
                actual_pid_consumed=False,
                activation_rollover=dict(original_receipt=str(original),
                    original_sha256=P.file_hash(original), verified_receipt=str(proof_path),
                    verified_sha256=P.file_hash(proof_path), workflow_commit=workflow_commit,
                    policy_reselected=False, actual_pid_consumed=False)))
            Q.require_failed_preopen_recovery(data, day)
            if (selector.read_bytes() != selected_raw or pointer.read_bytes() != pointer_raw
                    or original.read_bytes() != original_raw or proof_path.read_bytes() != proof_raw
                    or D._main_pids() or not D._session_absent()):
                raise ValueError("activation_rollover_generation_changed")
            destination = path(data, day, commit, current["bundle_sha256"])
            if destination.exists() and N._read(destination) != result:
                raise ValueError("activation_rollover_receipt_conflict")
            N._atomic_write_json(destination, result)
            validate_receipt(N._read(destination), day=day, commit=commit, root=consumer,
                bundle_sha=current["bundle_sha256"], pointer_sha=P.file_hash(pointer))
            return result


LEGACY_PREPARED_PARENT_SCOPE_CODE = (
    "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471"
)


def repair_prepared_parent_scope(
    data_root, day, *, consumer_root, expected_receipt_sha256, confirm
):
    """Migrate the exact unconsumed legacy receipt to its native parent scope.

    The reviewed immutable workflow is separate from unchanged consumer code.
    Preserve the original receipt and all observations; no policy, selector,
    PID or future preparation is published by this metadata producer.
    """
    import hashlib
    from src.engine.infrastructure import runtime_release_router as R
    from src.engine.infrastructure import research_release_transition as T
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    data = Path(data_root).resolve()
    workspace = data.parent
    consumer = Path(consumer_root).resolve()
    workflow = Path(__file__).resolve().parents[3]
    sha = lambda raw: hashlib.sha256(raw).hexdigest()

    def require(ok, reason):
        if not ok:
            raise ValueError("active_parent_scope_repair_" + reason)

    require(confirm == AUTHORITY, "authority_required")
    workflow_commit = R.git(workflow, "rev-parse", "HEAD")
    R.validate_release(
        workspace,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(workspace),
            release_root=str(workflow),
            git_commit=workflow_commit,
        ),
    )
    pointer = N.root(data) / "current.json"
    selector = data / "runtime/runtime_release_selection.json"
    with (
        R.runtime_release_set_lock(workspace),
        (N.root(data) / "publisher.lock").open("a") as lock,
    ):
        import fcntl

        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        selection, selection_raw, _ = D._owned_metadata(selector)
        ptr, pointer_raw, _ = D._owned_metadata(pointer)
        source = ptr["effective_date"]
        bundle = ptr["bundle_sha256"]
        selected, commit = R.selected_release(workspace)

        def stopped():
            require(
                selected == consumer
                and R.selected_release(workspace) == (consumer, commit),
                "selection_changed",
            )
            require(
                not D._main_pids() and D._session_absent(), "main_or_supervisor_present"
            )
            require(
                not (data / "runtime/operator_startup_hold.json").exists()
                and not (data / "runtime/operator_startup_hold.json").is_symlink(),
                "startup_hold_present",
            )
            require(
                not (workspace / "restart.flag").exists()
                and not (workspace / "restart.flag").is_symlink(),
                "restart_present",
            )
            require(
                selector.read_bytes() == selection_raw
                and pointer.read_bytes() == pointer_raw,
                "protected_generation_changed",
            )
            require(
                day == datetime.now(P.KST).date().isoformat(), "target_date_invalid"
            )
            V._require_closed_postclose_window(data, source, day, datetime.now(P.KST))

        stopped()
        require(
            selection.get("approved_by") == "user"
            and selection.get("approval_scope")
            == "after_postclose_deploy_for_next_regular_start"
            and selection.get("actual_pid_consumed") is False
            and not selection.get("actual_pid_receipt")
            and not selection.get("deployment_transition")
            and selection.get("source_date") == source
            and selection.get("next_operating_date") == day,
            "stopped_cold_selection_required",
        )
        require(
            P.file_hash(consumer / "src/engine/scalping/reversal_code_handoff.py")
            == LEGACY_PREPARED_PARENT_SCOPE_CODE,
            "legacy_producer_required",
        )
        current_path = path(data, day, commit, bundle)
        old, old_raw, _ = D._owned_metadata(current_path)
        require(sha(old_raw) == expected_receipt_sha256, "receipt_changed")
        validate_receipt(
            old,
            day=day,
            commit=commit,
            root=consumer,
            bundle_sha=bundle,
            pointer_sha=sha(pointer_raw),
        )
        actual = {
            str(consumer / Path(name).relative_to(workflow)): P.file_hash(
                consumer / Path(name).relative_to(workflow)
            )
            for name in code_hashes()
        }
        require(old["code_hashes"] == actual, "consumer_code_changed")
        backup = Path(selection.get("previous_selection_backup", ""))
        directory = backup.parent
        require(
            backup.is_absolute()
            and directory.parent == data / "runtime/research_release_transition"
            and directory.resolve() == directory
            and not backup.is_symlink(),
            "transition_path_invalid",
        )
        transition_path = directory / "transition.json"
        transition_raw = D._owned_metadata(transition_path)[1]
        transition = T._record(transition_path)
        entries = transition.get("entries") or []
        require(
            transition.get("state") == "verified"
            and transition.get("transition_id") == directory.name
            and len(entries) == 1
            and transition.get("written") == [str(selector)],
            "verified_transition_required",
        )
        entry = entries[0]
        prior, prior_raw, _ = D._owned_metadata(backup)
        after = directory / str(entry.get("after_snapshot", ""))
        after_raw = D._owned_metadata(after)[1]
        require(
            entry.get("path") == str(selector)
            and entry.get("before_snapshot") == backup.name
            and entry.get("before_sha256")
            == sha(prior_raw)
            == selection.get("predecessor_selection_sha256")
            and set(
                entry.get("accepted_sha256")
                or [entry.get("before_sha256"), entry.get("after_sha256")]
            )
            == {sha(prior_raw), sha(selection_raw)}
            and entry.get("after_sha256") == sha(selection_raw)
            and after.parent == directory
            and after.name == "after-" + sha(selection_raw) + ".bytes"
            and after_raw == selection_raw
            and transition_path.read_bytes() == transition_raw,
            "transition_binding_invalid",
        )
        origin = Path(prior["release_root"])
        origin_commit = prior["git_commit"]
        require(
            old.get("origin_root") == str(origin)
            and old.get("origin_commit") == origin_commit
            and old.get("origin_selection_sha256") == sha(prior_raw),
            "origin_binding_invalid",
        )
        R.validate_release(workspace, prior)
        p5_path = Path(selection.get("candidate_p5_path", ""))
        p5, p5_raw, _ = D._owned_metadata(p5_path)
        import re

        require(
            p5_path.parent.parent == data / "report/main_startup_validation" / day
            and p5_path.name == "final.json"
            and re.fullmatch("[0-9a-f]{32}", p5_path.parent.name) is not None
            and sha(p5_raw) == selection.get("candidate_p5_sha256")
            and p5.get("schema") == "main_policy_load_exit_validation_v1"
            and p5.get("status") == "passed"
            and p5.get("findings") == []
            and p5.get("target_date") == day
            and p5.get("execution_release_root") == str(consumer)
            and p5.get("execution_release_commit") == commit
            and all(
                p5.get(k) is True
                for k in (
                    "child_terminated",
                    "load_check_passed",
                    "protected_sources_unchanged",
                )
            ),
            "historical_candidate_p5_invalid",
        )
        # Revalidate the actual active parent in its original native release.
        # The failed future cache is neither repaired nor granted authority.
        parent = V._attested_activation_parent(
            data, day, origin_root=origin, origin_commit=origin_commit
        )
        require(
            parent is not None
            and parent["bundle_sha256"] == bundle
            and parent["target_date"] == source,
            "parent_changed",
        )
        checked = _validated_origin_receipt(
            data, source, origin, origin_commit, bundle, sha(pointer_raw)
        )
        require(checked is not None, "native_parent_receipt_missing")
        stopped()
        require(current_path.read_bytes() == old_raw, "receipt_changed")
        snapshots = current_path.with_suffix("") / "attempts"
        snapshots.mkdir(parents=True, exist_ok=True)
        require(
            not snapshots.is_symlink()
            and not any(p.is_symlink() for p in snapshots.parents),
            "snapshot_alias",
        )
        original = snapshots / ("before-parent-scope-" + sha(old_raw) + ".json")
        require(not original.is_symlink(), "snapshot_alias")
        if original.exists():
            require(original.read_bytes() == old_raw, "snapshot_changed")
        else:
            with original.open("xb") as out:
                out.write(old_raw)
        refs = {
            **checked["source_hashes"],
            **{
                str(p): P.file_hash(p)
                for p in (
                    original,
                    transition_path,
                    backup,
                    after,
                    p5_path,
                    Path(__file__).resolve(),
                )
            },
        }
        repaired = P.seal(
            dict(
                old,
                source_hashes=refs,
                origin_verification_basis="native_parent_scope_repaired",
                pipeline_source_reference_count=sum(
                    N.is_pipeline_source_reference(p, data_root=data) for p in refs
                ),
                source_scope_repair=dict(
                    schema="main_active_parent_source_scope_repair_v1",
                    authority=confirm,
                    workflow_root=str(workflow),
                    workflow_commit=workflow_commit,
                    original_receipt=dict(path=str(original), sha256=sha(old_raw)),
                    native_parent_receipt=str(
                        path(data, source, origin_commit, bundle)
                    ),
                    historical_candidate_p5=str(p5_path),
                    future_policy_validated=False,
                    policy_reselected=False,
                    actual_pid_consumed=False,
                ),
            )
        )
        for name, expected in refs.items():
            require(
                N.source_receipt_matches(
                    dict(path=name, sha256=expected), data_root=data
                ),
                "parent_source_changed",
            )
        stopped()
        require(current_path.read_bytes() == old_raw, "receipt_changed")
        N._atomic_write_json(current_path, repaired)
        require(N._read(current_path) == repaired, "publication_readback_changed")
        stopped()
        return repaired
