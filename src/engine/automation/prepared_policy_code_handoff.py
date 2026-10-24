"""Exact code compatibility for an unchanged, prepared next-session policy.

This does not publish a policy or replace PREOPEN/PID verification. The sealed
origin bootstrap and policy bytes remain immutable. Only reviewed source pairs
can cross this boundary, before or on the original target date.
"""

from datetime import date, datetime
import hashlib
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "prepared_policy_code_handoff_v1"
AUTHORITY = "APPROVED_PREPARED_POLICY_PRESERVING_CODE_HANDOFF"
FAMILIES = {
    "pre_submit_delay": ("pre_submit_delay_handoff", "policy_sha256"),
    "holding_vote": ("holding_path_vote_policy_receipt", "bundle_sha256"),
    "main_stop": ("main_stop_confirmation_receipt", "policy_sha256"),
}


def _sha(path):
    path = Path(path)
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 64 * 1024 * 1024
    ):
        raise ValueError("prepared_code_source_not_regular_bounded")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path):
    _sha(path)
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError("prepared_code_object_required")
    return value


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def receipt_path(data, day, commit, family):
    if (
        family not in FAMILIES
        or date.fromisoformat(day).isoformat() != day
        or not re.fullmatch("[0-9a-f]{40}", commit)
    ):
        raise ValueError("prepared_code_family_invalid")
    return (
        Path(data)
        / "runtime/policy_bootstrap/code_handoffs"
        / day
        / commit
        / (family + ".json")
    )


def _clock(day, now=None):
    today = (
        (now or datetime.now(ZoneInfo("Asia/Seoul")))
        .astimezone(ZoneInfo("Asia/Seoul"))
        .date()
    )
    target = datetime.strptime(day, "%Y-%m-%d").date()
    if day != target.isoformat() or today > target:
        raise ValueError("prepared_code_target_expired")


def _bound(manifest, family):
    name, key = FAMILIES[family]
    bound = manifest.get(name) or {}
    if bound.get("target_date") != manifest.get("target_date"):
        raise ValueError("prepared_code_policy_date_invalid")
    return bound[key]


def _origin(prepared_path, family, day, snapshots=None):
    def historical(path):
        return (snapshots or {}).get(str(path), str(path))

    prepared = _read(prepared_path)
    if (
        prepared.get("schema") != "next_preopen_readiness_v1"
        or prepared.get("status") != "prepared_verified"
        or prepared.get("target_date") != day
        or prepared.get("actual_pid_consumed") is not False
        or prepared.get("runtime_effect") is not False
    ):
        raise ValueError("prepared_code_origin_invalid")
    for field, digest in (
        ("manifest_path", "manifest_file_sha256"),
        ("env_path", "env_sha256"),
        ("verification_path", "verification_sha256"),
        ("controller_path", "controller_sha256"),
        ("summary_path", "summary_sha256"),
    ):
        if _sha(historical(prepared[field])) != prepared[digest]:
            raise ValueError("prepared_code_origin_changed")
    for row in prepared["policy_receipts"]:
        if _sha(historical(row["path"])) != row["sha256"]:
            raise ValueError("prepared_code_origin_changed")
    manifest = _read(historical(prepared["manifest_path"]))
    check = _read(historical(prepared["verification_path"]))
    if (
        manifest.get("selected_release_sha") != prepared["selected_release_commit"]
        or manifest.get("target_date") != day
        or manifest.get("manifest_sha256")
        != _digest({k: v for k, v in manifest.items() if k != "manifest_sha256"})
        or check.get("status") != "pass"
        or check.get("findings") != []
        or check.get("manifest_sha256") != manifest["manifest_sha256"]
    ):
        raise ValueError("prepared_code_origin_invalid")
    _bound(manifest, family)
    return prepared, manifest


def _policy(data, day, family, manifest):
    bound = manifest[FAMILIES[family][0]]
    if family == "pre_submit_delay":
        path = Path(bound["policy_path"])
        if not path.resolve().is_relative_to(
            Path(data) / "threshold_cycle/pre_submit_delay_policy"
        ):
            raise ValueError("prepared_code_policy_path_invalid")
        value = _read(path)
        if value.get("policy_sha256") != _bound(manifest, family) or value.get(
            "policy_sha256"
        ) != _digest({k: v for k, v in value.items() if k != "policy_sha256"}):
            raise ValueError("prepared_code_policy_changed")
        expected = value["code_contract_sha256"]
    elif family == "holding_vote":
        from src.engine.scalping import holding_path_vote_policy as V

        path = V.policy_path(data, day)
        value = V.load_bundle(data, day, require_current_code=False)
        if value.get("selection_mode") != "incumbent_carry" or value[
            "bundle_sha256"
        ] != _bound(manifest, family):
            raise ValueError("prepared_code_numeric_successor_forbidden")
        expected = value["code_sha256"]
    else:
        from src.engine.scalping import main_stop_policy as S

        path = S.policy_path(data, day)
        value = S.load_bundle(path, _sha(path), day, require_current_code=False)
        if value["policy_sha256"] != _bound(manifest, family) or any(
            cell["status"] == "selected" for cell in value["cells"].values()
        ):
            raise ValueError("prepared_code_numeric_successor_forbidden")
        expected = value["code_sha256"]
    return path, expected


def verify(data, day, *, family, policy_sha, expected, paths, actual, now=None):
    """Return None only when no such handoff exists; invalid evidence fails."""
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.automation import intraday_release_handoff as H

    data = Path(data).resolve()
    root, commit = selected_release(data.parent)
    path = receipt_path(data, day, commit, family)
    if not path.exists() and not path.is_symlink():
        return None
    _clock(day, now)
    receipt = _read(path)
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("authority") != AUTHORITY
        or receipt.get("receipt_sha256")
        != _digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
        or receipt.get("family") != family
        or receipt.get("target_date") != day
        or receipt.get("release_root") != str(root)
        or receipt.get("release_commit") != commit
        or receipt.get("policy_sha256") != policy_sha
        or receipt.get("original_code_sha256") != expected
        or receipt.get("runtime_code_sha256") != actual
        or receipt.get("paths") != paths
        or receipt.get("policy_effect") != "unchanged"
        or any(
            receipt.get(k) is not False
            for k in (
                "actual_pid_consumed",
                "policy_published",
                "provider_called",
                "broker_called",
            )
        )
    ):
        raise ValueError("prepared_code_receipt_invalid")
    sources = receipt.get("sources") or {}
    if not sources or any(_sha(name) != digest for name, digest in sources.items()):
        raise ValueError("prepared_code_source_changed")
    prepared, manifest = _origin(
        receipt["prepared_receipt"], family, day, receipt["historical_snapshots"]
    )
    policy_path, policy_code = _policy(data, day, family, manifest)
    if (
        prepared["selected_release_commit"] != receipt["origin_commit"]
        or _bound(manifest, family) != policy_sha
        or policy_code != expected
        or sources.get(str(policy_path)) != _sha(policy_path)
    ):
        raise ValueError("prepared_code_origin_invalid")
    actual_hash = _digest({key: _sha(root / name) for key, name in paths.items()})
    if actual_hash != actual:
        raise ValueError("prepared_code_runtime_contract_changed")
    changed = H._verify_entry_code_delta(
        root, commit, receipt["origin_commit"], paths, expected
    )
    # Preserve the legacy consumer status; the basis identifies future custody.
    return dict(
        status="verified_intraday_consumer_repair",
        verification_basis=SCHEMA,
        target_date=day,
        policy_sha256=policy_sha,
        origin_commit=receipt["origin_commit"],
        release_commit=commit,
        code_contract_sha256=expected,
        runtime_code_contract_sha256=actual,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
        actual_pid_consumed=False,
    )


def resolve_prepared_code_origin(
    data, day, *, family, policy_sha, expected, paths, selected_root, selected_commit
):
    """Authenticate the frozen policy origin before reviewing a new candidate.

    A new readiness generation can name today's selected release while its
    unchanged policy still carries an older code contract. Resolve that chain
    through the selected release's existing native handoff; never invent a new
    origin, publish a receipt, or treat candidate code as selected code.
    """
    from src.engine.infrastructure.runtime_release_router import selected_release

    if family not in FAMILIES or not isinstance(paths, dict) or not paths:
        raise ValueError("prepared_code_origin_contract_invalid")
    _clock(day)
    data = Path(data).resolve(strict=True)
    root = Path(selected_root).resolve(strict=True)
    selector = data / "runtime/runtime_release_selection.json"
    selector_sha = _sha(selector)
    if selected_release(data.parent) != (root, selected_commit):
        raise ValueError("prepared_code_origin_selection_mismatch")

    def selected_hashes(inventory, *, missing_allowed=False):
        result = {}
        for key, name in inventory.items():
            if (
                not isinstance(key, str)
                or not isinstance(name, str)
                or not (root / name).resolve(strict=False).is_relative_to(root)
            ):
                raise ValueError("prepared_code_origin_path_invalid")
            path = root / name
            if missing_allowed and not path.exists() and not path.is_symlink():
                return None
            result[key] = _sha(path)
        return result

    code_hashes = selected_hashes(paths, missing_allowed=True)
    actual = _digest(code_hashes) if code_hashes is not None else None
    selected_paths = paths
    sources = {str(selector): selector_sha}
    result = dict(
        origin_commit=selected_commit,
        basis="selected_exact_code_contract",
        selected_release_root=str(root),
        selected_release_commit=selected_commit,
        original_code_sha256=expected,
        selected_runtime_code_sha256=actual,
    )
    if actual != expected:
        from src.engine.automation import intraday_release_handoff as H

        path = receipt_path(data, day, selected_commit, family)
        if not path.exists() and not path.is_symlink():
            # A live intraday carry has its own consumed native custody. Do not
            # require or manufacture an unissued prepared-policy receipt.
            checked = H._verify_consumed_handoff(day, selected_commit)
            closed = None
            if checked.get("status") != "pass":
                try:
                    closed = H.closed_consumption_observation(day)
                    checked = H._verify_handoff(
                        day, selected_commit, historical_observer=True
                    )
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    raise ValueError("prepared_code_intraday_custody_invalid") from exc
            if checked.get("status") != "pass":
                raise ValueError("prepared_code_intraday_custody_invalid")
            handoff_path, consumed_path = H._paths(day, selected_commit)
            handoff, consumed = _read(handoff_path), _read(consumed_path)
            manifest_path = H.bootstrap.manifest_path(day)
            manifest = _read(manifest_path)
            origin = manifest.get("selected_release_sha")
            policy_path, policy_code = _policy(data, day, family, manifest)
            if (
                handoff != checked.get("handoff")
                or _bound(manifest, family) != policy_sha
                or policy_code != expected
                or consumed.get("manifest_sha256") != manifest.get("manifest_sha256")
                or origin != H._preopen(day).get("selected_release_commit")
            ):
                raise ValueError("prepared_code_intraday_policy_binding_invalid")
            candidate = Path(H.__file__).resolve().parents[3]
            trigger = "src/engine/sniper_state_handlers.py"
            variant = H.REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS.get(
                (trigger, _sha(candidate / trigger)), {}
            )
            extensions = variant.get("contract_extensions", {}).get(
                (origin, expected), {}
            )
            selected_paths = {
                key: name for key, name in paths.items() if name not in extensions
            }
            code_hashes = selected_hashes(selected_paths)
            actual = _digest(code_hashes)
            H._verify_entry_code_delta(
                root, selected_commit, origin, selected_paths, expected
            )
            sources.update(handoff["frozen_files"])
            sources.update(
                {
                    str(p): _sha(p)
                    for p in (handoff_path, consumed_path, manifest_path, policy_path)
                }
            )
            sources.update(
                {
                    str(root / name): code_hashes[key]
                    for key, name in selected_paths.items()
                }
            )
            identity = consumed["pid_identity"]
            if (
                closed
                and closed["pid_identity"] != identity
                or not closed
                and H._identity(identity["pid"]) != identity
                or _sha(selector) != selector_sha
                or any(_sha(name) != sha for name, sha in sources.items())
            ):
                raise ValueError("prepared_code_intraday_generation_changed")
            if closed:
                sources.update(closed["source_hashes"])
            result.update(
                origin_commit=origin,
                basis=(
                    "verified_closed_intraday_code_handoff"
                    if closed
                    else "verified_selected_intraday_code_handoff"
                ),
                closed_observation=closed,
                selected_runtime_code_sha256=actual,
                selected_paths=selected_paths,
                sources=sources,
                intraday_handoff_path=str(handoff_path),
                intraday_handoff_sha256=_sha(handoff_path),
                intraday_consumed_path=str(consumed_path),
                intraday_consumed_sha256=_sha(consumed_path),
                pid_identity=identity,
                reviewed_extension_hashes=extensions,
            )
            return result
        receipt_sha = _sha(path)
        receipt = _read(path)
        selected_paths = receipt.get("paths")
        if not isinstance(selected_paths, dict) or not selected_paths:
            raise ValueError("prepared_code_origin_inventory_invalid")
        code_hashes = selected_hashes(selected_paths)
        actual = _digest(code_hashes)
        proof = verify(
            data,
            day,
            family=family,
            policy_sha=policy_sha,
            expected=expected,
            paths=selected_paths,
            actual=actual,
        )
        if proof is None:
            raise ValueError("prepared_code_origin_handoff_missing")
        if (
            _sha(path) != receipt_sha
            or proof.get("origin_commit") != receipt.get("origin_commit")
            or proof.get("policy_effect") != "unchanged"
            or proof.get("actual_pid_consumed") is not False
        ):
            raise ValueError("prepared_code_origin_handoff_changed")
        extensions = H.REVIEWED_DELAY_CONTRACT_EXTENSIONS.get(
            (proof["origin_commit"], expected), {}
        )
        expected_paths = dict(selected_paths)
        for name in extensions:
            if name in selected_paths.values():
                continue
            # Historical policy keys are part of their frozen digest. Stop and
            # holding use engine-relative keys (including ../utils), whereas
            # delay uses repository-relative keys. Only values are Git paths.
            if family in {"main_stop", "holding_vote"}:
                if not name.startswith("src/engine/"):
                    raise ValueError(
                        "prepared_code_origin_inventory_extension_unreviewed"
                    )
                key = name[len("src/engine/") :]
            else:
                key = name
            if key in expected_paths:
                raise ValueError("prepared_code_origin_inventory_extension_unreviewed")
            expected_paths[key] = name
        if paths != expected_paths:
            raise ValueError("prepared_code_origin_inventory_extension_unreviewed")
        sources[str(path)] = receipt_sha
        sources.update(receipt["sources"])
        result.update(
            origin_commit=proof["origin_commit"],
            basis="verified_selected_prepared_code_handoff",
            selected_runtime_code_sha256=actual,
            reviewed_extension_hashes={
                name: digest
                for name, digest in extensions.items()
                if name not in selected_paths.values()
            },
            code_handoff_receipt_path=str(path),
            code_handoff_receipt_sha256=receipt_sha,
        )
    sources.update(
        {str(root / name): code_hashes[key] for key, name in selected_paths.items()}
    )
    if (
        _sha(selector) != selector_sha
        or selected_release(data.parent) != (root, selected_commit)
        or any(_sha(name) != digest for name, digest in sources.items())
    ):
        raise ValueError("prepared_code_origin_sources_changed")
    result["sources"] = sources
    result["selected_paths"] = selected_paths
    return result


def issue_selected(data, day, *, release_root):
    """Complete native prepared-code custody before the ordered P5 consumer.

    The ordered caller holds the release-set lock and its owned startup hold.
    Reuse verified receipts without rewriting their immutable generations.
    """
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.infrastructure import runtime_release_router as R
    from src.engine.scalping import main_stop_policy as S, holding_vote_experiment as V
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    data, root = Path(data).resolve(), Path(release_root).resolve(strict=True)
    with D._existing_selector_lock(data / "runtime/runtime_release_selection.lock"):
        selected, commit = R.selected_release(data.parent)
        if selected != root:
            raise ValueError("prepared_code_issuance_not_selected")
        selection = data / "runtime/runtime_release_selection.json"
        before = _sha(selection)
        checked = H._verify_handoff(day, commit)
        if checked.get("status") != "pass" or checked.get("findings"):
            raise ValueError("prepared_code_issuance_handoff_invalid")
        prepared_path = Path(checked["handoff"]["prepared_receipt_path"])
        prepared = _read(prepared_path)
        manifest = _read(prepared["manifest_path"])
        results = []
        for family, inventory in (
            ("pre_submit_delay", CONTRACT_PATHS),
            ("main_stop", S.implementation_paths()),
            ("holding_vote", V._code_paths()),
        ):
            paths = {
                name: name if family == "pre_submit_delay" else "src/engine/" + name
                for name in inventory
            }
            policy_sha = _bound(manifest, family)
            _, expected = _policy(data, day, family, manifest)
            actual = _digest({name: _sha(root / path) for name, path in paths.items()})
            existing = verify(
                data,
                day,
                family=family,
                policy_sha=policy_sha,
                expected=expected,
                paths=paths,
                actual=actual,
            )
            path = receipt_path(data, day, commit, family)
            if existing is None:
                issue(
                    data,
                    day,
                    family=family,
                    policy_sha=policy_sha,
                    expected=expected,
                    paths=paths,
                    release_root=root,
                    prepared_receipt=prepared_path,
                    origin_verification=prepared["verification_path"],
                    confirm=AUTHORITY,
                )
            results.append(
                dict(
                    family=family,
                    path=str(path),
                    sha256=_sha(path),
                    actual_pid_consumed=False,
                )
            )
        if _sha(selection) != before or R.selected_release(data.parent) != (
            root,
            commit,
        ):
            raise ValueError("prepared_code_issuance_selection_changed")
        return results


def issue(
    data,
    day,
    *,
    family,
    policy_sha,
    expected,
    paths,
    release_root,
    prepared_receipt,
    origin_verification,
    confirm,
    previous_handoff=None,
):
    """Issue under the deployment caller's release-set and selection locks."""
    from src.engine.infrastructure.runtime_release_router import (
        validate_release,
        selected_release,
    )
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    import subprocess

    _clock(day)
    if confirm != AUTHORITY:
        raise ValueError("prepared_code_authority_required")
    data = Path(data).resolve()
    root = Path(release_root).resolve()
    from src.engine.automation import ordered_intraday_deploy as ordered

    if ordered._main_pids() or not ordered._session_absent():
        raise ValueError("prepared_code_main_running")
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    validate_release(
        data.parent,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(data.parent),
            release_root=str(root),
            git_commit=commit,
        ),
    )
    selected_root, selected_commit = selected_release(data.parent)
    previous = None
    historical = None
    if previous_handoff is not None:
        previous_path = receipt_path(data, day, selected_commit, family)
        if Path(previous_handoff) != previous_path:
            raise ValueError("prepared_code_previous_handoff_not_selected")
        previous = _read(previous_path)
        previous_sha = _sha(previous_path)
        previous_actual = _digest(
            {key: _sha(selected_root / name) for key, name in paths.items()}
        )
        verified = verify(
            data,
            day,
            family=family,
            policy_sha=policy_sha,
            expected=expected,
            paths=paths,
            actual=previous_actual,
        )
        if (
            verified is None
            or verified.get("release_commit") != selected_commit
            or _sha(previous_path) != previous_sha
            or previous.get("original_prepared_receipt") != str(prepared_receipt)
        ):
            raise ValueError("prepared_code_previous_handoff_changed")
        historical = previous["historical_snapshots"]
        # Reuse only the native verifier's immutable original coordinates.
        # Never restore historical aliases over the current controller/policy.
        prepared, manifest = _origin(
            previous["prepared_receipt"], family, day, historical
        )
    else:
        prepared, manifest = _origin(prepared_receipt, family, day)
    origin = prepared["selected_release_commit"]
    if previous is None and selected_commit not in {origin, commit}:
        raise ValueError("prepared_code_selection_changed")
    policy_path, policy_code = _policy(data, day, family, manifest)
    if (
        str(origin_verification) != prepared["verification_path"]
        or _bound(manifest, family) != policy_sha
        or policy_code != expected
    ):
        raise ValueError("prepared_code_origin_not_verified")
    changed = H._verify_entry_code_delta(root, commit, origin, paths, expected)
    actual = _digest({key: _sha(root / name) for key, name in paths.items()})
    historical_paths = tuple(
        map(
            Path,
            (
                prepared_receipt,
                origin_verification,
                prepared["manifest_path"],
                prepared["env_path"],
                prepared["verification_path"],
                prepared["controller_path"],
                prepared["summary_path"],
                *(row["path"] for row in prepared["policy_receipts"]),
            ),
        )
    )
    snapshots = {}
    frozen = Path(data) / "runtime/policy_bootstrap/code_handoffs/frozen"
    frozen.mkdir(parents=True, exist_ok=True)
    for source in historical_paths:
        physical = Path(historical[str(source)]) if historical is not None else source
        before = _sha(physical)
        raw = physical.read_bytes()
        if hashlib.sha256(raw).hexdigest() != before:
            raise ValueError("prepared_code_origin_changed")
        destination = frozen / (before + ".snapshot")
        try:
            with destination.open("xb") as handle:
                handle.write(raw)
        except FileExistsError:
            pass
        if _sha(destination) != before or _sha(physical) != before:
            raise ValueError("prepared_code_frozen_origin_changed")
        snapshots[str(source)] = str(destination)
    sources = {name: _sha(name) for name in snapshots.values()}
    sources[str(policy_path)] = _sha(policy_path)
    if previous is not None:
        if _sha(previous_path) != previous_sha or selected_release(data.parent) != (
            selected_root,
            selected_commit,
        ):
            raise ValueError("prepared_code_previous_handoff_changed")
        sources[str(previous_path)] = previous_sha
    body = dict(
        schema=SCHEMA,
        authority=confirm,
        family=family,
        target_date=day,
        release_root=str(root),
        release_commit=commit,
        origin_commit=origin,
        policy_sha256=policy_sha,
        original_code_sha256=expected,
        runtime_code_sha256=actual,
        paths=paths,
        changed_paths=changed,
        prepared_receipt=snapshots[str(prepared_receipt)],
        original_prepared_receipt=str(prepared_receipt),
        historical_snapshots=snapshots,
        origin_verification=snapshots[str(origin_verification)],
        sources=sources,
        policy_effect="unchanged",
        actual_pid_consumed=False,
        policy_published=False,
        provider_called=False,
        broker_called=False,
    )
    if previous is not None:
        body["previous_handoff"] = dict(
            path=str(previous_path), sha256=previous_sha, release_commit=selected_commit
        )
    body["receipt_sha256"] = _digest(body)
    destination = receipt_path(data, day, commit, family)
    if destination.exists() and _read(destination) != body:
        raise ValueError("prepared_code_immutable_conflict")
    N._atomic_write_json(destination, body)
    return body
