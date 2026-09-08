"""User-authorized strategy override succession, effective next PREOPEN.

An approval receipt supersedes exact strategy keys, not safety or manual vetoes.
Original operator files are immutable evidence. This module never edits them,
starts a process, calls a provider, or manufactures an economic candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shlex
from datetime import date
from pathlib import Path

from src.engine.scalping import strategy_owner_components as components

SCHEMA = "operator_strategy_policy_succession_v1"
EFFECTIVE_DATE = "2026-09-09"
AUTHORITY = "user_authorized_strategy_lock_auto_succession_20260908"
SCORE = "score65_74_recovery_probe"
PYRAMID = "scalping_pyramid_quality_gate"
AVG_DOWN = "scalping_avg_down_recovery_quality_gate"
SCORE_PREFIX = "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_"
# Exact owned keys, not prefix permission. In particular freshness, caps,
# strong-micro bypasses and provider settings cannot inherit this authority.
POLICY_KEYS = {
    SCORE: frozenset(
        SCORE_PREFIX + suffix
        for suffix in (
            "ENABLED",
            "MIN_SCORE",
            "MAX_SCORE",
            "MIN_BUY_PRESSURE",
            "MIN_TICK_ACCEL",
            "MIN_MICRO_VWAP_BP",
            "THRESHOLD_VERSION",
            "CALIBRATION_STATE",
        )
    ),
    PYRAMID: frozenset({"KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT"}),
    AVG_DOWN: frozenset(
        {
            "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE",
            "KORSTOCKSCAN_AVG_DOWN_RUNTIME_QUALITY_UPDATE_ID",
            "KORSTOCKSCAN_AVG_DOWN_RUNTIME_EVIDENCE_CONTRACT_VERSION",
            "KORSTOCKSCAN_AVG_DOWN_RUNTIME_EVIDENCE_DIGEST",
            "KORSTOCKSCAN_AVG_DOWN_RUNTIME_PREVIOUS_MIN_BUY_PRESSURE",
        }
    ),
}
POLICY_STAGES = {SCORE: "entry", PYRAMID: "scale_in", AVG_DOWN: "scale_in"}
STRATEGY_FAMILIES = frozenset(
    {
        SCORE,
        PYRAMID,
        AVG_DOWN,
        "early_accel_recheck_runtime",
        "entry_opportunity_recheck_runtime",
        "entry_price_gap_profile_runtime",
        "pre_submit_liquidity_relief_runtime",
        "profit_stagnation_exit_runtime",
        "real_pyramid_scale_in_quality_guard_runtime",
        "rising_missed_normal_buy_bridge",
        "scalping_scanner_real_source_guard_runtime",
        "score65_74_recovery_probe_strong_micro_override_runtime",
        "weak_context_late_entry_guard_runtime",
        "weak_pullback_entry_block_runtime",
    }
)
# These existing integration hooks retire the separate recheck/guard when a
# formally selected entry owner takes over. Do not create competing tuning axes.
FORMAL_ENTRY_SUCCESSORS = frozenset(
    {
        "early_accel_recheck_runtime",
        "pre_submit_liquidity_relief_runtime",
        "weak_context_late_entry_guard_runtime",
        "scalping_scanner_real_source_guard_runtime",
        "score65_74_recovery_probe_strong_micro_override_runtime",
    }
)
PROTECTED_FAMILIES = frozenset(
    {
        "buy_side_time_block_disable_runtime",
        "buy_side_time_block_runtime",
        "sell_side_open_time_block_runtime",
        "quote_consistency_normalization",
        "holding_decision_context_v1",
        "latency_spread_relief_real_operator_override",
        "scalp_sim_ai_budget_manager",
        "scalp_sim_candidate_window_expansion",
        "late_entry_price_drift_guard_runtime",
        "soft_stop_dynamic_grace_runtime",
        "entry_price_gap_profile_runtime",
        "real_pyramid_scale_in_quality_guard_runtime",
        "rising_missed_normal_buy_bridge",
    }
)


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def lock_values(lock):
    values = dict(lock.get("env_overrides") or {})
    if lock.get("env_key"):
        values.setdefault(lock["env_key"], lock.get("env_value", "true"))
    return {
        str(k): str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in values.items()
    }


def classify(lock):
    family = lock.get("family")
    values = lock_values(lock)
    if lock.get("enabled") is False:
        return "inactive_archive"
    if lock.get("manual_veto") is True or lock.get("safety_veto") is True:
        return "protected_veto"
    # An explicit family OFF is a veto, not an underperforming strategy.
    enable_keys = (
        {str(lock.get("env_key") or "")}
        | POLICY_KEYS.get(family, set())
        | components.KEYS.get(family, set())
    )
    if any(
        key.endswith("_ENABLED") and values.get(key, "").lower() in {"false", "0"}
        for key in enable_keys
    ):
        return "protected_veto"
    if family in POLICY_KEYS:
        return "strategy_auto_successor"
    if family in components.OWNERS:
        return "existing_owner_managed_component"
    if family in FORMAL_ENTRY_SUCCESSORS:
        return "existing_formal_entry_owner_supersession"
    if family in PROTECTED_FAMILIES:
        return "protected_safety_operational_or_source_only"
    if family in STRATEGY_FAMILIES:
        return "strategy_owner_contract_missing"
    if family == "persistent_operator_overrides_2026_06_26":
        return "mixed_key_scoped_overlay"
    return "unclassified_protected"


def inventory(locks):
    rows = []
    for lock in locks:
        family = lock.get("family")
        role = classify(lock)
        rows.append(
            {
                "lock_id": lock.get("lock_id"),
                "path": lock.get("path"),
                "family": family,
                "classification": role,
                "successor_owner": (
                    family
                    if family in POLICY_KEYS
                    else (
                        components.OWNERS.get(family) or "existing_formal_entry_owner"
                        if family in FORMAL_ENTRY_SUCCESSORS
                        or family in components.OWNERS
                        else None
                    )
                ),
                "auto_successor_keys": sorted(
                    set(lock_values(lock))
                    & (
                        POLICY_KEYS.get(family, set())
                        | components.KEYS.get(family, set())
                    )
                ),
                "operator_reapproval_required": role
                not in {
                    "strategy_auto_successor",
                    "strategy_owner_contract_missing",
                    "mixed_key_scoped_overlay",
                    "existing_formal_entry_owner_supersession",
                    "existing_owner_managed_component",
                    "inactive_archive",
                },
                "reason": (
                    "existing_family_producer_contract_required_not_manual_approval"
                    if role == "strategy_owner_contract_missing"
                    else role
                ),
            }
        )
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "effective_date": EFFECTIVE_DATE,
        "lock_count": len(rows),
        "locks": rows,
    }


def read_operator_env(path):
    """Parse exports without executing shell or exposing unrelated secrets."""
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = shlex.split(line, comments=True)
        if parts[:1] == ["export"]:
            parts = parts[1:]
        if parts and all(re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", part) for part in parts):
            for part in parts:
                key, value = part.split("=", 1)
                result[key] = value
        elif (
            any(
                key in line
                for key in set().union(
                    *POLICY_KEYS.values(),
                    components.ALL_KEYS,
                    {components.ENV_KEY},
                    {SCORE_PREFIX + "EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP"},
                )
            )
            and parts
        ):
            raise ValueError("operator_strategy_env_expression_not_supported")
    return result


def source_snapshot(runtime_dir, lock_dir, keys, target_date):
    """Bind only affected keys; unrelated operator changes do not stale a policy."""
    keys = set(keys)
    if keys & POLICY_KEYS[SCORE]:
        keys.add(SCORE_PREFIX + "EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP")
    rows = []
    for path in sorted(lock_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = {k: v for k, v in lock_values(payload).items() if k in keys}
        if values:
            rows.append(
                {
                    "path": str(path.resolve()),
                    "lock_id": payload.get("lock_id"),
                    "enabled": payload.get("enabled", True),
                    "classification": classify(payload),
                    "values": values,
                }
            )
    for name in (
        "operator_runtime_overrides.env",
        f"operator_runtime_overrides_{target_date}.env",
    ):
        path = runtime_dir / name
        values = {k: v for k, v in read_operator_env(path).items() if k in keys}
        if values:
            rows.append({"path": str(path.resolve()), "values": values})
    return rows


def current_locked_values(lock, runtime_dir, target_date):
    values = lock_values(lock)
    for name in (
        "operator_runtime_overrides.env",
        f"operator_runtime_overrides_{target_date}.env",
    ):
        values.update(read_operator_env(runtime_dir / name))
    # A carried policy receipt is later than the historical operator layers.
    values.update(lock.get("_policy_carried_values") or {})
    return values


def prepare_locks(locks, candidates, previous, runtime_dir, lock_dir, target_date):
    """Carry the accepted successor, never resurrect the original strategy lock."""
    result = [dict(lock) for lock in locks]
    if target_date < EFFECTIVE_DATE:
        return result
    same_day = runtime_dir / f"threshold_runtime_env_{target_date}.json"
    if same_day.exists():
        published = json.loads(same_day.read_text(encoding="utf-8"))
        if published.get("operator_policy_succession"):
            previous = published
    prior_values = validate_receipt(previous, runtime_dir, lock_dir) if previous else {}
    prior_rows = (previous.get("operator_policy_succession") or {}).get("policies", [])
    for row in prior_rows:
        family = row["family"]
        env = {k: prior_values[k] for k in row["env_overrides"]}
        # Expiration of yesterday's date-scoped instruction is normal. A new
        # instruction for today is not silently hidden by the carried policy.
        previous_sources = [
            source
            for source in row["operator_sources"]
            if not (
                match := re.fullmatch(
                    r"operator_runtime_overrides_(\d{4}-\d{2}-\d{2})\.env",
                    Path(source["path"]).name,
                )
            )
            or match[1] >= target_date
        ]
        if (
            source_snapshot(runtime_dir, lock_dir, set(env), target_date)
            != previous_sources
        ):
            raise ValueError(
                "operator_succession_new_operator_instruction_requires_reconciliation"
            )
        matching = [lock for lock in result if lock.get("family") == family]
        if not matching:
            matching = [
                {
                    "family": family,
                    "stage": row["stage"],
                    "enabled": True,
                    "lock_id": row["predecessor_lock_id"],
                    "priority": row["priority"],
                }
            ]
            result.extend(matching)
        for lock in matching:
            lock["env_overrides"] = {**lock_values(lock), **env}
            lock["_policy_carried_values"] = env
            lock["_policy_succession"] = row
    # Persistent overlays can pin a strategy key without a family JSON lock.
    existing = {lock.get("family") for lock in result}
    overlays = read_operator_env(runtime_dir / "operator_runtime_overrides.env")
    overlays.update(
        read_operator_env(runtime_dir / f"operator_runtime_overrides_{target_date}.env")
    )
    for candidate in candidates:
        family = candidate.get("family")
        keys = POLICY_KEYS.get(family, set()) & set(overlays)
        if keys and family not in existing:
            env = {
                k: v
                for k, v in previous.get("env_overrides", {}).items()
                if k in POLICY_KEYS[family]
            }
            env.update({k: overlays[k] for k in keys})
            result.append(
                {
                    "family": family,
                    "stage": candidate.get("stage"),
                    "priority": candidate.get("priority"),
                    "enabled": True,
                    "lock_id": "persistent_strategy_overlay:" + family,
                    "env_overrides": env,
                }
            )
            existing.add(family)
    return result


def succession_reason(
    candidate, lock, proposed, current, *, ordinary_allowed, target_date
):
    """Additional ownership/baseline check; ordinary family gates run first."""
    family = candidate.get("family")
    if target_date < EFFECTIVE_DATE:
        return "before_authorized_effective_date"
    if (
        family != lock.get("family")
        or candidate.get("stage") != POLICY_STAGES.get(family)
        or lock.get("stage") != candidate.get("stage")
    ):
        return "successor_owner_or_stage_mismatch"
    if (lock.get("_policy_succession") or {}).get("applied_target_date") == target_date:
        return "same_day_policy_frozen"
    if classify(lock) not in {"strategy_auto_successor", "mixed_key_scoped_overlay"}:
        return "protected_or_missing_successor_owner"
    if not ordinary_allowed or candidate.get("allowed_runtime_apply") is not True:
        return "candidate_not_independently_approved"
    if not proposed or set(proposed) - POLICY_KEYS.get(family, set()):
        return "candidate_key_ownership_mismatch"
    for key, value in current.items():
        if (
            key.endswith("_ENABLED")
            and key in POLICY_KEYS.get(family, set())
            and str(value).lower() in {"false", "0"}
        ):
            return "explicit_operator_off_veto"
    if family == SCORE:
        from src.engine.scalping.score_recovery_economics import (
            evaluate_policy,
            profile,
        )

        expected = {
            k: current.get(SCORE_PREFIX + k.upper())
            for k in (
                "min_score",
                "max_score",
                "min_buy_pressure",
                "min_tick_accel",
                "min_micro_vwap_bp",
            )
        }
        # Runtime uses the existing effective floor, even when the raw lock is 0.
        expected["min_micro_vwap_bp"] = max(
            float(expected["min_micro_vwap_bp"]),
            float(current.get(SCORE_PREFIX + "EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP", 10)),
        )
        if profile(expected) != profile(candidate.get("current_values")):
            return "economic_baseline_differs_from_effective_lock"
        economics = evaluate_policy(
            candidate.get("source_metrics") or {}, candidate.get("sample_floor", 20)
        )
        if not economics.get("ready") or economics.get("profile") != profile(
            candidate.get("recommended_values")
        ):
            return "existing_family_economics_not_ready"
    elif family in {PYRAMID, AVG_DOWN}:
        key = (
            "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT"
            if family == PYRAMID
            else "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
        )
        before = float(candidate.get("current_value"))
        after = float(candidate.get("recommended_value"))
        bounds = candidate.get("bounds") or {}
        if not all(
            math.isfinite(v)
            for v in (
                before,
                after,
                float(current.get(key)),
                float(bounds.get("min")),
                float(bounds.get("max")),
            )
        ):
            return "nonfinite_economic_values"
        if before != float(current[key]):
            return "economic_baseline_differs_from_effective_lock"
        if not float(bounds["min"]) <= after <= float(bounds["max"]) or abs(
            after - before
        ) > float(candidate.get("max_step_per_day", 0)):
            return "family_bounded_step_invalid"
        if candidate.get(
            "runtime_update_mode"
        ) != "single_cumulative_quality_update" or not candidate.get("evidence_digest"):
            return "family_cumulative_evidence_missing"
        window = candidate.get("cumulative_quality_window") or {}
        dates = window.get("source_dates") or []
        if (
            window.get("window_policy") != "clean_baseline_cumulative"
            or not dates
            or any(
                not date(2026, 6, 5)
                <= date.fromisoformat(d)
                < date.fromisoformat(target_date)
                for d in dates
            )
            or window.get("end_date") >= target_date
        ):
            return "family_cumulative_window_invalid"
        if candidate.get("source_quality_gate") not in {
            "pass",
            "pass_with_row_exclusions",
        }:
            return "family_source_quality_not_ready"
        if family == PYRAMID and candidate.get("decision_evidence_gate") != "pass":
            return "family_economics_not_ready"
        if family == PYRAMID:
            from src.engine.monitoring.scalping_pyramid_quality_calibration import (
                _profit_grid_decision,
            )

            grid = (candidate.get("source_metrics") or {}).get("profit_threshold_grid")
            decision = _profit_grid_decision(
                candidate.get("current_values") or {}, grid
            )
            if (
                decision.get("status") not in {"adjust_up", "adjust_down"}
                or decision.get("selected_min_profit_pct") != after
            ):
                return "family_economic_replay_not_ready"
    else:
        return "successor_owner_not_registered"
    return ""


def validate_receipt(manifest, runtime_dir, lock_dir):
    receipt = manifest.get("operator_policy_succession")
    if receipt is None:
        if manifest.get("operator_policy_succession_required") is True:
            raise ValueError("operator_succession_receipt_missing")
        return validate_components(manifest, runtime_dir, lock_dir)
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != SCHEMA
        or receipt.get("authority") != AUTHORITY
    ):
        raise ValueError("operator_succession_receipt_invalid")
    signed = {k: v for k, v in receipt.items() if k != "sha256"}
    if receipt.get("sha256") != digest(signed) or receipt.get(
        "target_date"
    ) != manifest.get("target_date"):
        raise ValueError("operator_succession_receipt_hash_or_date_mismatch")
    if receipt["target_date"] < EFFECTIVE_DATE:
        raise ValueError("operator_succession_before_authorization")
    if not isinstance(receipt.get("policies"), list):
        raise ValueError("operator_succession_policy_list_invalid")
    runtime_file = runtime_dir / f"threshold_runtime_env_{receipt['target_date']}.env"
    actual_env = read_operator_env(runtime_file)
    values = {}
    for row in receipt.get("policies", []):
        family = row["family"]
        env = row["env_overrides"]
        if (
            row.get("stage") != POLICY_STAGES.get(family)
            or row.get("state")
            not in {"superseded_by_verified_policy", "carried_verified_policy"}
            or not row.get("predecessor_lock_id")
            or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("candidate_sha256", "")))
            or not EFFECTIVE_DATE
            <= str(row.get("applied_target_date", ""))
            <= receipt["target_date"]
        ):
            raise ValueError("operator_succession_policy_identity_invalid")
        if (
            not env
            or set(env) - POLICY_KEYS.get(family, set())
            or set(env) & set(values)
        ):
            raise ValueError("operator_succession_key_ownership_invalid")
        if (
            source_snapshot(runtime_dir, lock_dir, set(env), receipt["target_date"])
            != row["operator_sources"]
        ):
            raise ValueError("operator_succession_operator_source_changed")
        if any(
            str(manifest.get("env_overrides", {}).get(k)) != str(v)
            for k, v in env.items()
        ):
            raise ValueError("operator_succession_manifest_env_mismatch")
        if any(actual_env.get(k) != str(v) for k, v in env.items()):
            raise ValueError("operator_succession_runtime_file_mismatch")
        if family not in manifest.get("selected_families", []):
            raise ValueError("operator_succession_owner_not_selected")
        values.update(env)
    values.update(validate_components(manifest, runtime_dir, lock_dir))
    return values


def component_bundle(target_date, rows):
    return json.dumps(
        {
            "schema": components.SCHEMA,
            "target_date": target_date,
            "components": [
                {k: row[k] for k in ("family", "owner", "baseline", "policies")}
                for row in rows
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def validate_components(manifest, runtime_dir, lock_dir):
    receipt = manifest.get("strategy_owner_components")
    if receipt is None:
        if manifest.get("strategy_owner_components_required"):
            raise ValueError("owner_component_receipt_missing")
        return {}
    if (
        receipt.get("schema") != components.SCHEMA
        or receipt.get("authority") != AUTHORITY
        or receipt.get("target_date") != manifest.get("target_date")
        or receipt.get("sha256")
        != digest({k: v for k, v in receipt.items() if k != "sha256"})
    ):
        raise ValueError("owner_component_receipt_invalid")
    day = receipt["target_date"]
    if day < EFFECTIVE_DATE:
        raise ValueError("owner_component_before_authorization")
    values, seen = {}, set()
    for row in receipt["components"]:
        family = row["family"]
        env = row["env_overrides"]
        if (
            family in seen
            or family not in components.OWNERS
            or row.get("owner") != components.OWNERS[family]
            or not row.get("predecessor_lock_id")
            or set(env) != components.KEYS[family]
            or components.profile(family, row["baseline"]) is None
            or components.profile(
                family, {k.removeprefix(components.PREFIX): v for k, v in env.items()}
            )
            != row["baseline"]
            or source_snapshot(runtime_dir, lock_dir, set(env), day)
            != row["operator_sources"]
        ):
            raise ValueError("owner_component_contract_invalid")
        for policy in row["policies"]:
            if (
                policy["baseline"] != row["baseline"]
                or not components.bounded_change(
                    family, policy["baseline"], policy["profile"]
                )
                or not components.valid_scope(policy["venue"], policy["session"])
                or not policy.get("source_dates")
                or any(not "2026-06-05" <= d < day for d in policy["source_dates"])
                or not re.fullmatch(
                    r"[a-f0-9]{64}", str(policy.get("context_sha256", ""))
                )
                or not re.fullmatch(
                    r"[a-f0-9]{64}", str(policy.get("evidence_sha256", ""))
                )
            ):
                raise ValueError("owner_component_policy_invalid")
        seen.add(family)
        values.update(env)
    values[components.ENV_KEY] = component_bundle(day, receipt["components"])
    actual = read_operator_env(runtime_dir / f"threshold_runtime_env_{day}.env")
    if any(
        manifest.get("env_overrides", {}).get(k) != v or actual.get(k) != v
        for k, v in values.items()
    ):
        raise ValueError("owner_component_env_mismatch")
    return values


def prepare_components(
    locks,
    previous,
    runtime_dir,
    lock_dir,
    target_date,
    research=None,
    include_families=None,
    safety_reverts=None,
):
    """Adopt existing behavior without an EV gate; never borrow another approval.

    Components are not independent stage owners. A verified real economic book
    may replace a scoped policy; a missing book carries the last verified policy.
    """
    if target_date < EFFECTIVE_DATE:
        return locks, [], {}
    same_day = runtime_dir / f"threshold_runtime_env_{target_date}.json"
    if same_day.exists():
        published = json.loads(same_day.read_text())
        if published.get("strategy_owner_components"):
            previous = published
    if previous.get("strategy_owner_components"):
        validate_components(previous, runtime_dir, lock_dir)
    prior = {
        r["family"]: r
        for r in (previous.get("strategy_owner_components") or {}).get("components", [])
    }
    remaining, decisions, env = [], [], {}
    for lock in locks:
        family = lock.get("family")
        if (
            classify(lock) != "existing_owner_managed_component"
            or lock.get("stage") != components.STAGES.get(family)
            or family in (safety_reverts or set())
            or (include_families is not None and family not in include_families)
        ):
            remaining.append(lock)
            continue
        effective = current_locked_values(lock, runtime_dir, target_date)
        owned = {key: effective.get(key) for key in components.KEYS[family]}
        baseline = components.profile(
            family, {k.removeprefix(components.PREFIX): v for k, v in owned.items()}
        )
        if baseline is None or any(
            not value for key, value in baseline.items() if key.endswith("_ENABLED")
        ):
            remaining.append(lock)  # Unsupported/mixed/off contracts remain explicit.
            continue
        old = prior.get(family)
        policies = []
        if old:
            previous_sources = [
                s
                for s in old["operator_sources"]
                if not (
                    (
                        m := re.fullmatch(
                            r"operator_runtime_overrides_(\d{4}-\d{2}-\d{2})\.env",
                            Path(s["path"]).name,
                        )
                    )
                    and m[1] < target_date
                )
            ]
            if (
                source_snapshot(runtime_dir, lock_dir, set(owned), target_date)
                != previous_sources
            ):
                raise ValueError("owner_component_operator_instruction_changed")
            policies = old["policies"]
        evaluation = {
            "state": "baseline_migrated" if not old else "last_verified_policy_carried",
            "policies": policies,
        }
        if previous.get("target_date") != target_date and research:
            evaluation = components.evaluate(research, family, baseline, target_date)
            if evaluation["policies"]:
                policies = evaluation["policies"]
        row = {
            "family": family,
            "owner": components.OWNERS[family],
            "baseline": baseline,
            "env_overrides": owned,
            "policies": policies,
            "predecessor_lock_id": lock.get("lock_id"),
            "operator_sources": source_snapshot(
                runtime_dir, lock_dir, set(owned), target_date
            ),
            "state": evaluation["state"],
            "structural_migration_requires_ev": False,
            "previous_policies": old["policies"] if old else [],
            "economic_evaluation": evaluation,
            "economic_sample_floor": 20,
            "economic_acceptance": "separate_real_post_apply",
        }
        decisions.append(
            {
                "family": family,
                "stage": lock.get("stage"),
                "selected": False,
                "same_stage_owner_claim": False,
                "decision_reason": "integrated_into_existing_owner",
                "env_overrides": {},
                "strategy_owner_component": row,
            }
        )
        env.update(owned)
    return remaining, decisions, env


def build_component_receipt(target_date, decisions):
    rows = [
        d["strategy_owner_component"]
        for d in decisions
        if d.get("strategy_owner_component")
    ]
    if not rows:
        return None
    receipt = {
        "schema": components.SCHEMA,
        "authority": AUTHORITY,
        "target_date": target_date,
        "components": rows,
    }
    receipt["sha256"] = digest(receipt)
    return receipt


def build_receipt(target_date, decisions, runtime_dir, lock_dir):
    rows = []
    for decision in decisions:
        evidence = decision.get("operator_policy_succession")
        if not decision.get("selected") or not evidence:
            continue
        env = {
            k: v
            for k, v in decision["env_overrides"].items()
            if k in POLICY_KEYS.get(decision["family"], set())
        }
        rows.append(
            {
                **evidence,
                "family": decision["family"],
                "env_overrides": env,
                "operator_sources": source_snapshot(
                    runtime_dir, lock_dir, set(env), target_date
                ),
            }
        )
    receipt = {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "target_date": target_date,
        "policies": rows,
    }
    receipt["sha256"] = digest(receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--runtime-dir", type=Path)
    parser.add_argument("--lock-dir", type=Path)
    args = parser.parse_args(argv)
    from src.utils.constants import DATA_DIR

    runtime_dir = args.runtime_dir or DATA_DIR / "threshold_cycle/runtime_env"
    lock_dir = args.lock_dir or DATA_DIR / "threshold_cycle/operator_runtime_env_locks"
    path = runtime_dir / f"threshold_runtime_env_{args.target_date}.json"
    if not path.exists():
        return 0
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("target_date") != args.target_date:
        raise ValueError("operator_succession_target_date_mismatch")
    values = validate_receipt(manifest, runtime_dir, lock_dir)
    for key, value in sorted(values.items()):
        print(f"export {key}={shlex.quote(str(value))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
