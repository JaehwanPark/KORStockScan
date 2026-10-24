"""Main's read-only policy preparation, shared by live startup and load-and-exit.

This module deliberately imports no Main entrypoint, engine, sink, DB, provider
or transport. Objects may populate the existing in-process native loader caches;
operational consumption receipts and execution authority belong to later callers.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
from collections.abc import Mapping
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
CONSUMER_IDS = frozenset(
    {
        "typed_trading_rules",
        "main_machine",
        "main_auxiliary",
        "pre_submit_delay",
        "main_stop",
        "trailing_mechanical",
        "trailing_situation",
        "initial_quantity",
        "entry_split",
        "holding_path_vote",
        "entry_prompt",
        "holding_prompt",
    }
)


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            _plain(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _sources(*paths, logical_source_receipts=None):
    """Bind stable native sources with bounded memory, including large reports."""
    result = {}
    logical = {}
    if logical_source_receipts is not None:
        from src.engine.infrastructure.startup_validation_code_context import (
            preparation_logical_sources,
        )

        logical = preparation_logical_sources()

    def identity(stat):
        return (
            stat.st_dev,
            stat.st_ino,
            stat.st_mode,
            stat.st_size,
            stat.st_mtime_ns,
            stat.st_ctime_ns,
        )

    for item in paths:
        if not item:
            continue
        path = Path(item)
        if path.is_symlink():
            raise ValueError("startup_policy_source_symlink")
        if str(path) in logical:
            logical_source_receipts[str(path)] = logical[str(path)]
            continue
        from src.engine.infrastructure.startup_validation_code_context import (
            preparation_source_digest,
        )

        reused = preparation_source_digest(path)
        if reused is not None:
            result[str(path)] = reused
            continue
        sha = hashlib.sha256()
        with path.open("rb") as source:
            before = identity(os.fstat(source.fileno()))
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                sha.update(chunk)
            if (
                before != identity(os.fstat(source.fileno()))
                or path.is_symlink()
                or before != identity(path.stat())
            ):
                raise ValueError("startup_policy_source_changed_during_hash")
        result[str(path)] = sha.hexdigest()
    return result


def _loaded(
    value,
    *,
    native_status="loaded",
    policy_sha256=None,
    source_hashes=None,
    status="loaded",
    **extra,
):
    return dict(
        status=status,
        native_status=native_status,
        loaded_object_sha256=_digest(value),
        policy_sha256=policy_sha256,
        source_hashes=source_hashes or {},
        **extra,
    )


def _failure(exc):
    return dict(
        status="failed",
        native_status="load_failed",
        loaded_object_sha256=None,
        policy_sha256=None,
        source_hashes={},
        reason=type(exc).__name__ + ":" + str(exc),
    )


def load_main_policies(
    *,
    target_date: str,
    observed_at: datetime,
    data_root: Path,
    env: Mapping[str, str],
    validation: bool = False,
) -> dict:
    """Load actual native policy objects, without granting runtime authority.

    ``target_date`` selects content. ``observed_at`` remains the real wall clock
    for native operator/freshness checks. Runtime keeps existing safe fallback
    behavior and lifecycle: only delay/trailing prepare at engine startup.
    Other consumers keep their existing live callsites and are marked deferred.
    The validation aggregate nevertheless refuses to label invalid loads
    as PASS. Validation callers must reject a failed aggregate.
    """
    if date.fromisoformat(target_date).isoformat() != target_date:
        raise ValueError("startup_policy_target_date_invalid")
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("startup_policy_observed_clock_must_be_aware")
    data_root = Path(data_root)
    results = {}
    report = dict(
        schema="main_policy_loading_v1",
        target_date=target_date,
        observed_at_kst=observed_at.astimezone(KST).isoformat(),
        consumer_results=results,
        delay_preparation={"status": "preparation_invalid"},
        trailing_preparation={"status": "preparation_invalid"},
        runtime_effect=False,
        actual_pid_consumed=False,
    )

    def consume(name, loader):
        try:
            results[name] = loader()
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            results[name] = _failure(exc)

    # Two native process-cached consumers intentionally use os.environ. Require
    # the supplied startup environment to be that exact policy view, rather than
    # temporarily replacing process globals or silently loading another view.
    supplied = {
        key: value for key, value in env.items() if key.startswith("KORSTOCKSCAN_")
    }
    effective = {
        key: value
        for key, value in os.environ.items()
        if key.startswith("KORSTOCKSCAN_")
    }
    if supplied != effective:
        raise ValueError("startup_policy_process_environment_mismatch")

    if validation:
        from src.utils.constants import TRADING_RULES

        consume(
            "typed_trading_rules",
            lambda: _loaded(
                TRADING_RULES,
                native_status="typed_runtime_rules",
                policy_sha256=_digest(TRADING_RULES),
            ),
        )

    bundle = None
    if validation:
        try:
            from src.engine.scalping.reversal_evaluation_context import (
                prepare_policy_loading,
            )
            from src.engine.scalping import mechanistic_entry_runtime_policy as N

            dependencies = {}
            token = N._READ_DEPENDENCIES.set(dependencies)
            try:
                bundle = prepare_policy_loading(
                    data_root=data_root, day=target_date, preparation=True
                )
                if not bundle:
                    raise ValueError("main_machine_policy_missing")
                path = N.preparation_path(data_root, target_date)
                logical_sources = {}
                source_hashes = _sources(
                    path,
                    *(name for name in dependencies if Path(name).is_file()),
                    logical_source_receipts=logical_sources,
                )
                if not N.dependencies_unchanged(dependencies):
                    raise ValueError("main_machine_dependency_changed_during_loading")
            finally:
                N._READ_DEPENDENCIES.reset(token)
            family = bundle.get("continuous_reversal") or {}
            cells = family.get("machine_cells") or {}
            scopes = sorted(
                key + "|" + route
                for key, cell in cells.items()
                for route in cell.get("routes", {})
            )
            if not scopes:
                scopes = sorted(
                    cells or bundle.get("scope_policies") or {"KRX|KRX_REGULAR": None}
                )
            backend_generation = None
            if family.get("schema") in {
                "continuous_reversal_policy_v5",
                "continuous_reversal_policy_v6",
            }:
                from src.engine.scalping.reversal_current_backend import backend

                backend_generation = getattr(backend(), "_GENERATION", None)
                if backend_generation != family["family_sha256"]:
                    raise ValueError(
                        "main_machine_prepared_backend_generation_mismatch"
                    )
            results["main_machine"] = _loaded(
                bundle,
                native_status="prepared_content_loaded",
                policy_sha256=bundle["bundle_sha256"],
                source_hashes=source_hashes,
                logical_source_receipts=logical_sources,
                scope_keys=scopes,
                backend_generation_sha256=backend_generation,
            )
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            results["main_machine"] = _failure(exc)

    def auxiliary():
        if bundle is None:
            raise ValueError("main_auxiliary_machine_dependency_failed")
        from src.engine.automation.auxiliary_reader_readiness import (
            verify_auxiliary_reader,
        )

        native = verify_auxiliary_reader(
            target_date, data_root=data_root, preparation=validation, bundle=bundle
        )
        if native.get("status") not in {"pass", "not_required"}:
            raise ValueError("main_auxiliary_reader_not_verified")
        logical = {}
        if validation:
            from src.engine.infrastructure.startup_validation_code_context import (
                preparation_logical_sources,
            )

            logical = preparation_logical_sources()
        return _loaded(
            native,
            native_status=native["status"],
            policy_sha256=native.get("bundle_sha256"),
            source_hashes=native.get("source_hashes"),
            logical_source_receipts=logical,
            status="parent_only" if native["status"] == "not_required" else "loaded",
        )

    if validation:
        consume("main_auxiliary", auxiliary)

    def delay():
        from src.engine.scalping.pre_submit_delay_tuning import prepare_runtime_policy

        native = prepare_runtime_policy(
            now=observed_at,
            target_date=target_date if validation else None,
            env=env,
            data_root=data_root,
        )
        report["delay_preparation"] = native
        status = native.get("status")
        if status == "disabled":
            return _loaded(None, native_status=status, status="disabled")
        if status not in {"prepared", "prepared_reused"}:
            raise ValueError(
                "delay_"
                + str(status)
                + ":"
                + str(native.get("fallback_status") or native.get("reason") or "")
            )
        return dict(
            status="loaded",
            native_status=status,
            loaded_object_sha256=native["loaded_object_sha256"],
            policy_sha256=native.get("policy_sha256"),
            source_hashes=native.get("source_hashes") or {},
        )

    consume("pre_submit_delay", delay)

    def stop():
        from src.engine.scalping import main_stop_policy as S

        ident = S.preload(env)
        if ident is None:
            return _loaded(
                None, native_status="effective_legacy_rules", status="parent_only"
            )
        raw = S.load_bundle(env[S.ENV_FILE], env[S.ENV_SHA], target_date)
        if env[S.ENV_DATE] != target_date:
            raise ValueError("stop_target_date_mismatch")
        S.validate_runtime_environment(raw, env)
        loaded = S._LOADED
        if loaded is None or loaded[0] != ident or loaded[1] != target_date:
            raise ValueError("stop_loaded_identity_mismatch")
        sources = _sources(env[S.ENV_FILE])
        if sources[str(Path(env[S.ENV_FILE]))] != env[S.ENV_SHA]:
            raise ValueError("stop_source_changed_after_loading")
        return _loaded(
            loaded,
            policy_sha256=ident,
            source_hashes=sources,
            scope_keys=sorted(loaded[2]),
        )

    if validation:
        consume("main_stop", stop)

    def trailing_mechanical():
        from src.engine.scalping import trailing_mechanical_policy as T

        scalar = {key: getattr(TRADING_RULES, key) for key in T.TP_KEYS}
        loaded = T.runtime_policy_vector_snapshot(scalar)
        return _loaded(loaded, policy_sha256=loaded[3], scope_keys=sorted(loaded[0]))

    if validation:
        consume("trailing_mechanical", trailing_mechanical)

    def trailing_situation():
        from src.engine.scalping import trailing_situation_policy as T

        native = T.prepare_runtime(
            env=env,
            parent_sha256=env.get(
                "KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256"
            ),
            target_date=target_date,
        )
        report["trailing_preparation"] = native
        prepared = T._PREPARED
        if native["status"] == "parent_only":
            return _loaded(None, native_status="parent_only", status="parent_only")
        if native["status"] != "prepared" or prepared is None:
            raise ValueError("trailing_situation_not_prepared")
        return _loaded(
            dict(
                policy_sha256=prepared.policy_sha256,
                parent_sha256=prepared.parent_sha256,
                classifier_sha256=prepared.classifier_sha256,
                target_date=prepared.target_date,
                cells=prepared.cells,
            ),
            native_status=native["status"],
            policy_sha256=prepared.policy_sha256,
            scope_keys=sorted(prepared.cells),
        )

    consume("trailing_situation", trailing_situation)

    def quantity():
        from src.engine.scalping.initial_quantity_activation import (
            ENV_FILE,
            ENV_SHA,
            load_pinned_initial_quantity_policy,
        )

        path = str(env.get(ENV_FILE) or "").strip()
        sha = str(env.get(ENV_SHA) or "").strip().lower()
        if not path and not sha:
            if str(
                env.get("KORSTOCKSCAN_POSITION_SIZING_POLICY_ENABLED", "")
            ).strip().lower() in {"1", "true", "yes", "on"}:
                raise ValueError("quantity_legacy_dynamic_policy_unverified")
            from src.engine.scalping.position_sizing_allocator import (
                _runtime_position_sizing_policy,
            )

            native = _runtime_position_sizing_policy(observed_at, "UNKNOWN")
            return _loaded(native, native_status=native[2], status="parent_only")
        if (
            not path
            or not sha
            or str(env.get("KORSTOCKSCAN_POSITION_SIZING_POLICY_ENABLED", ""))
            .strip()
            .lower()
            in {"1", "true", "yes", "on"}
        ):
            raise ValueError("initial_policy_identity_conflict_fallback")
        policy, native = load_pinned_initial_quantity_policy(
            Path(path), sha, date.fromisoformat(target_date)
        )
        if policy is None:
            raise ValueError(native)
        sources = _sources(path)
        if sources[str(Path(path))] != sha:
            raise ValueError("initial_quantity_source_changed_after_loading")
        return _loaded(
            policy,
            native_status=native,
            policy_sha256=policy["policy_content_sha256"],
            source_hashes=sources,
            scope_keys=sorted(policy["type_policies"]),
        )

    if validation:
        consume("initial_quantity", quantity)

    def split():
        from src.engine.scalping.entry_split_order_plan import _load_policy_from_env

        policy, native = _load_policy_from_env(
            now=observed_at, target_date=target_date, env=env, preparation=validation
        )
        if native == "policy_disabled":
            return _loaded(None, native_status=native, status="disabled")
        if native != "loaded":
            raise ValueError(native)
        daily = policy.get("entry_split_order_daily_baseline_fallback_applied") is True
        key = (
            "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE"
            if daily
            else "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"
        )
        sources = _sources(env.get(key))
        return _loaded(
            policy,
            native_status=native,
            policy_sha256=sources[str(Path(env[key]))],
            source_hashes=sources,
            scope_keys=sorted(policy.get("buckets") or {}),
            policy_version=policy.get("policy_version"),
        )

    if validation:
        consume("entry_split", split)

    def holding_path():
        from src.engine.scalping import holding_path_vote_policy as H

        loaded, native = H.runtime_policy_from_env(
            env, data_root=data_root, active_date=target_date
        )
        configured = any(env.get(key) for key in (H.ENV_PATH, H.ENV_SHA, H.ENV_DATE))
        if not configured:
            return _loaded(loaded, native_status=native["status"], status="parent_only")
        if not native["status"].endswith("_loaded"):
            raise ValueError(native["status"] + ":" + str(native.get("reason", "")))
        return _loaded(
            loaded,
            native_status=native["status"],
            policy_sha256=native["bundle_sha256"],
            source_hashes=_sources(env[H.ENV_PATH]),
            scope_keys=sorted(map(str, loaded)),
        )

    if validation:
        consume("holding_path_vote", holding_path)

    if validation:
        try:
            from src.engine.infrastructure.main_prompt_policy_loading import (
                load_prompt_policy_consumers,
            )

            prompt = load_prompt_policy_consumers(
                target_date=target_date,
                observed_at=observed_at,
                env=env,
                data_root=data_root,
                preparation=validation,
            )
            for key in ("entry_prompt", "holding_prompt"):
                results[key] = prompt[key]
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ImportError,
        ) as exc:
            for key in ("entry_prompt", "holding_prompt"):
                results[key] = _failure(exc)
    else:
        for key in CONSUMER_IDS - results.keys():
            results[key] = dict(
                status="deferred",
                native_status="existing_runtime_callsite",
                loaded_object_sha256=None,
                policy_sha256=None,
                source_hashes={},
                reason="loaded_by_existing_runtime_consumer",
            )
    missing, unexpected = CONSUMER_IDS - results.keys(), results.keys() - CONSUMER_IDS
    report["missing_consumers"] = sorted(missing)
    report["unexpected_consumers"] = sorted(unexpected)
    report["status"] = (
        ("passed" if validation else "deferred")
        if not missing
        and not unexpected
        and all(
            item.get("status")
            in (
                {"loaded", "disabled", "parent_only"}
                if validation
                else {"loaded", "disabled", "parent_only", "deferred"}
            )
            for item in results.values()
        )
        else "failed"
    )
    if not validation and results["trailing_situation"]["status"] == "failed":
        # The existing live prepare_runtime call raises on invalid trailing
        # content. Keep that startup failure instead of silently carrying parent.
        raise ValueError(results["trailing_situation"]["reason"])
    return report
