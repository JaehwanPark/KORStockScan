"""Read-only adapters for Main's native entry and holding prompt consumers.

The native resolvers own policy interpretation. This adapter only inventories
their complete scope sets and distinguishes approved absence from a failed
enabled policy. No provider, activation writer or PID consumer is called.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


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


def _source(path, sources, *, required=False):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("prompt_policy_source_symlink:" + str(path))
    if not path.exists() and not required:
        return
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("prompt_policy_source_unbounded:" + str(path))
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if str(path) in sources and sources[str(path)] != actual:
        raise ValueError("prompt_policy_source_changed:" + str(path))
    sources[str(path)] = actual


def _result(rows, sources):
    failures = [row for row in rows if row["status"] == "failed"]
    status = (
        "failed"
        if failures
        else (
            "loaded"
            if any(row["status"] == "loaded" for row in rows)
            else (
                "disabled"
                if rows and all(row["status"] == "disabled" for row in rows)
                else "parent_only"
            )
        )
    )
    return dict(
        status=status,
        native_status="scope_load_failed" if failures else "all_scopes_checked",
        loaded_object_sha256=_digest(rows),
        policy_sha256=_digest([row.get("policy_sha256") for row in rows]),
        source_hashes=sources,
        scope_results=rows,
        reason=(
            ";".join(row.get("reason") or row["native_status"] for row in failures)
            if failures
            else None
        ),
    )


def _entry(*, target_date, observed_at, env, data_root, preparation):
    from src.engine.scalping import entry_setup_live_policy as native
    from src.engine.scalping import entry_setup_scalping_rollout as authority
    from src.engine.scalping import mechanistic_entry_runtime_policy as machine

    if Path(native.DATA_DIR).resolve() != data_root.resolve():
        raise ValueError("entry_prompt_data_root_mismatch")
    sources = {}
    for key in (authority.PATH_ENV, authority.AUTO_PROMOTION_PATH_ENV):
        if env.get(key):
            _source(env[key], sources, required=True)
    policy_path = (
        machine.preparation_path(data_root, target_date)
        if preparation
        else machine.root(data_root) / "current.json"
    )
    _source(policy_path, sources)
    rows = []
    for venue, session in native.SUPPORTED_LIVE_COHORTS:
        resolved = native.resolve_live_prompt_policy(
            configured_prompt_version=env.get(
                "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION", ""
            ),
            effective_venue=venue,
            session_bucket=session,
            position_tag="SCANNER",
            strategy="SCALPING",
            now=observed_at,
            policy_target_date=target_date,
            preparation=preparation,
            data_root=data_root,
        )
        status = resolved.get("status", "missing_native_status")
        if resolved.get("enabled") is True and status in {
            "active_bounded_krx_canary",
            "active_bounded_nxt_canary",
        }:
            state = "loaded"
        elif status == "fallback_operator_disabled" and str(
            env.get(native._cohort_env_key((venue, session)), "")
        ).lower() in {"false", "0", "off", "no"}:
            state = "disabled"
        elif status == "fallback_dual_observe_only_no_live_approval" and not (
            env.get(authority.AUTO_PROMOTION_PATH_ENV)
            or env.get(authority.AUTO_PROMOTION_SHA_ENV)
        ):
            state = "parent_only"
        else:
            state = "failed"
        for name in ("activation_path", "candidate_path"):
            if resolved.get(name):
                _source(resolved[name], sources, required=state == "loaded")
        rows.append(
            dict(
                scope=venue + "|" + session,
                status=state,
                native_status=status,
                loaded_object_sha256=_digest(resolved),
                policy_sha256=resolved.get("machine_bundle_sha256")
                or resolved.get("candidate_contract_sha256"),
                reason=resolved.get("machine_policy_error")
                or ";".join(resolved.get("runtime_contract_errors") or [])
                or status,
            )
        )
    for name in tuple(sources):
        _source(name, sources, required=True)
    return _result(rows, sources)


def _holding(*, target_date, observed_at, env, data_root, preparation):
    from src.engine.scalping import holding_prompt_live_policy as native

    rows, sources = [], {}
    for venue, session in native.SUPPORTED_COHORTS:
        cohort = (venue, session)
        activation_path = native.activation_path(
            target_date, cohort, data_root=data_root
        )
        expected = (
            native.build_activation(target_date, cohort, data_root=data_root)
            if preparation
            else native._read_json(activation_path)
        )
        if expected.get("candidate_path"):
            _source(expected["candidate_path"], sources, required=True)
            candidate = native._read_json(Path(expected["candidate_path"]))
            if (
                sources[str(Path(expected["candidate_path"]))]
                != expected.get("candidate_file_sha256")
                or candidate.get("artifact_sha256")
                != expected.get("candidate_artifact_sha256")
                or candidate.get("artifact_sha256")
                != native._canonical_sha256(
                    {
                        key: value
                        for key, value in candidate.items()
                        if key != "artifact_sha256"
                    }
                )
            ):
                raise ValueError("holding_prompt_candidate_hash_invalid")
        _source(activation_path, sources)
        resolved = native.resolve_holding_prompt_policy(
            effective_venue=venue,
            session_bucket=session,
            now=observed_at,
            policy_target_date=target_date,
            prepared_activation=expected if preparation else None,
            data_root=data_root,
        )
        state = "loaded" if resolved.get("enabled") is True else "failed"
        blocking = expected.get("blocking_reasons") or []
        if expected.get("status") == "fallback_holding_score_v2":
            # Native PREOPEN deliberately publishes a baseline when no qualified
            # candidate exists. Hash/cohort/prompt corruption is never absence.
            valid_absence = bool(
                expected.get("candidate_path") is None
                or not set(blocking).difference(
                    {
                        "holding_prompt_candidate_not_ready",
                        "holding_prompt_candidate_runtime_apply_not_allowed",
                    }
                )
            )
            actual = (
                native._read_json(activation_path)
                if activation_path.is_file()
                else None
            )
            valid_contract = (
                expected.get("schema") == native.ACTIVATION_SCHEMA
                and expected.get("target_date") == target_date
                and expected.get("effective_venue") == venue
                and expected.get("session_bucket") == session
                and expected.get("hard_safety_unchanged") is True
                and expected.get("runtime_effect") is False
                and expected.get("actual_order_submitted") is False
                and expected.get("selected_prompt_version")
                == native.FALLBACK_PROMPT_VERSION
                and expected.get("artifact_sha256")
                == native._canonical_sha256(
                    {
                        key: value
                        for key, value in expected.items()
                        if key != "artifact_sha256"
                    }
                )
            )
            if valid_absence and valid_contract and (preparation or actual == expected):
                state = "parent_only"
        rows.append(
            dict(
                scope=venue + "|" + session,
                status=state,
                native_status=resolved.get("reason")
                or resolved.get("status")
                or "missing_native_status",
                loaded_object_sha256=_digest(resolved),
                policy_sha256=expected.get("artifact_sha256"),
                expected_activation_sha256=expected.get("artifact_sha256"),
                reason=";".join(blocking) if state != "loaded" else None,
            )
        )
    if preparation:
        for row in rows:
            venue, session = row["scope"].split("|", 1)
            latest = native.build_activation(
                target_date, (venue, session), data_root=data_root
            )
            if latest.get("artifact_sha256") != row["expected_activation_sha256"]:
                raise ValueError("holding_prompt_candidate_selection_changed")
    for name in tuple(sources):
        _source(name, sources, required=True)
    return _result(rows, sources)


def load_prompt_policy_consumers(
    *, target_date, observed_at, env, data_root, preparation=None
):
    """Exercise the same native resolvers as Main, with a separate content date.

    The caller supplies the fresh process environment and native prepared view.
    Wall-clock operator checks continue receiving ``observed_at`` unchanged.
    """
    if date.fromisoformat(target_date).isoformat() != target_date:
        raise ValueError("prompt_policy_target_date_invalid")
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("prompt_policy_observed_clock_must_be_aware")
    if {
        key: value for key, value in env.items() if key.startswith("KORSTOCKSCAN_")
    } != {
        key: value
        for key, value in os.environ.items()
        if key.startswith("KORSTOCKSCAN_")
    }:
        raise ValueError("prompt_policy_process_environment_mismatch")
    if preparation is None:
        preparation = target_date != observed_at.astimezone(KST).date().isoformat()
    if not isinstance(preparation, bool):
        raise ValueError("prompt_policy_preparation_mode_invalid")
    result = {}
    for name, loader in (("entry_prompt", _entry), ("holding_prompt", _holding)):
        try:
            result[name] = loader(
                target_date=target_date,
                observed_at=observed_at,
                env=env,
                data_root=Path(data_root),
                preparation=preparation,
            )
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            result[name] = dict(
                status="failed",
                native_status="load_failed",
                loaded_object_sha256=None,
                policy_sha256=None,
                source_hashes={},
                reason=type(exc).__name__ + ":" + str(exc),
            )
    return result
