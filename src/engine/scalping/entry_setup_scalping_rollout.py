"""Pinned operator rollout of the existing V2.14 entry owner to all SCALPING.

This is a prompt-scope approval, not an economic promotion or a new order owner.
The durable accepted-order ledger, one-share and all execution guards remain.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
PATH_ENV = "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH"
SHA_ENV = "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256"
SCHEMA = "operator_scalping_v2_14_rollout_v1"
SCOPES = (
    "KRX|KRX_REGULAR",
    "NXT|KRX_REGULAR",
    "NXT|NXT_REGULAR_OVERLAP",
    "NXT|NXT_REGULAR",
    "PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE",
    "NXT|NXT_PREMARKET",
    "PREMARKET_KRX_LIKE|NXT_PREMARKET",
    "NXT|NXT_AFTERMARKET",
)
OBSERVE_ONLY_SCOPES = ("KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET",)
AUTO_PROMOTION_PATH_ENV = "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH"
AUTO_PROMOTION_SHA_ENV = "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_SHA256"
AUTO_PROMOTION_SCHEMA = "operator_scalping_prompt_auto_promotion_v1"
AUTO_PROMOTION_SCOPES = SCOPES + OBSERVE_ONLY_SCOPES
AUTO_PROMOTION_CONTRACT = {
    "schema": AUTO_PROMOTION_SCHEMA,
    "strategy": "SCALPING",
    "stage": "entry",
    "position_tags": "all",
    "scopes": list(AUTO_PROMOTION_SCOPES),
    "promotion_mode": "postclose_exact_cohort_preopen_only",
    "candidate_prompt_version_floor": "V2.15",
    "fallback_prompt_version": "V2.14",
    "one_share_probe_first_required": True,
    "residual_multi_leg_forbidden": True,
    "scale_in_forbidden": True,
    "preserve_execution_guards": True,
    "quantity_cap_cooldown_unchanged": True,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "persistence": "until_operator_revocation",
}
CONTRACT = {
    "schema": SCHEMA,
    "strategy": "SCALPING",
    "stage": "entry",
    "position_tags": "all",
    "scopes": list(SCOPES),
    "one_share_probe_first_required": True,
    "residual_multi_leg_forbidden": True,
    "scale_in_forbidden": True,
    "maximum_daily_exploration_probes": 100,
    "cap_basis": "existing_global_durable_broker_accepted_probe_orders",
    "preserve_execution_guards": True,
    "persistence": "until_operator_revocation",
}


def load_auto_promotion(
    *, now: datetime | None = None, env: dict[str, str] | None = None
) -> dict[str, Any] | None:
    """Load the immutable all-session V2.15+ promotion authority.

    This is deliberately independent of the durable V2.14 rollout: an absent,
    malformed, or not-yet-effective pin cannot promote a newer prompt.
    """

    source = os.environ if env is None else env
    path, digest = source.get(AUTO_PROMOTION_PATH_ENV, ""), source.get(
        AUTO_PROMOTION_SHA_ENV, ""
    )
    if not path and not digest:
        return None
    result: dict[str, Any] = {"valid": False, "reason": "auto_promotion_pin_invalid"}
    try:
        policy_path = Path(path)
        if not policy_path.is_absolute():
            return result
        raw = policy_path.read_bytes()
        if len(digest) != 64 or hashlib.sha256(raw).hexdigest() != digest:
            return result
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return result
        current = (now or datetime.now(KST)).astimezone(KST)
        effective = datetime.fromisoformat(payload["effective_from"])
        if effective.tzinfo is None or effective > current:
            return {**result, "reason": "auto_promotion_not_effective"}
        if any(
            type(payload.get(key)) is not type(value) or payload.get(key) != value
            for key, value in AUTO_PROMOTION_CONTRACT.items()
        ):
            return {**result, "reason": "auto_promotion_contract_invalid"}
        if re.fullmatch(r"[0-9a-f]{40}", str(payload.get("reviewed_commit") or "")) is None:
            return result
        if payload.get("operator_authority") != "all_sessions_v2_15_plus_auto_promotion_2026_09_14":
            return result
        return {"valid": True, "sha256": digest, "path": path, "payload": payload}
    except (OSError, ValueError, TypeError, KeyError):
        return result


def load_rollout(
    *, now: datetime | None = None, env: dict[str, str] | None = None
) -> dict[str, Any] | None:
    source = os.environ if env is None else env
    path, digest = source.get(PATH_ENV, ""), source.get(SHA_ENV, "")
    if not path and not digest:
        return None
    result: dict[str, Any] = {"valid": False, "reason": "rollout_pin_invalid"}
    try:
        if not Path(path).is_absolute():
            return result
        raw = Path(path).read_bytes()
        if len(digest) != 64 or hashlib.sha256(raw).hexdigest() != digest:
            return result
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return result
        current = (now or datetime.now(KST)).astimezone(KST)
        effective = datetime.fromisoformat(payload["effective_from"])
        if effective.tzinfo is None or effective > current:
            return {**result, "reason": "rollout_not_effective"}
        if any(
            type(payload.get(k)) is not type(v) or payload.get(k) != v
            for k, v in CONTRACT.items()
        ):
            return {**result, "reason": "rollout_contract_invalid"}
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(payload.get("reviewed_commit") or ""))
            is None
        ):
            return result
        if payload.get("operator_authority") != "all_scalping_v2_14_2026_09_11":
            return result
        return {"valid": True, "sha256": digest, "path": path, "payload": payload}
    except (OSError, ValueError, TypeError, KeyError):
        return result


def scope_authorized(
    strategy: Any, venue: Any, session: Any, *, now: datetime | None = None
) -> bool:
    if str(strategy or "").strip().upper() not in {"SCALPING", "SCALP"}:
        return False
    scope = f"{str(venue or '').strip().upper()}|{str(session or '').strip().upper()}"
    rollout = load_rollout(now=now)
    return bool(scope in SCOPES and rollout and rollout.get("valid") is True)


def scope_authority_mode(venue: Any, session: Any) -> str:
    """Classify scope without extending the immutable live rollout."""

    scope = f"{str(venue or '').strip().upper()}|{str(session or '').strip().upper()}"
    if scope in SCOPES:
        return "existing_live_scope"
    if scope in OBSERVE_ONLY_SCOPES:
        return "observe_only_no_live_approval"
    return "unsupported"


def authorized_scopes(
    *, env: dict[str, str] | None = None, now: datetime | None = None
) -> frozenset[str]:
    rollout = load_rollout(env=env, now=now)
    from src.engine.scalping.entry_recheck_policy import runtime_scope

    return (
        frozenset(runtime_scope(*scope.split("|")) for scope in SCOPES)
        if rollout and rollout.get("valid") is True
        else frozenset()
    )


def decision_authorized(
    strategy: Any, decision: Any, *, now: datetime | None = None
) -> bool:
    current = (now or datetime.now(KST)).astimezone(KST)
    if not isinstance(decision, dict):
        return False
    if decision.get("entry_setup_live_policy_runtime_effect") is not True:
        return False
    if decision.get("entry_setup_live_policy_target_date") != current.date().isoformat():
        return False
    venue = decision.get("entry_setup_live_policy_effective_venue")
    session = decision.get("entry_setup_live_policy_session_bucket")
    authority = decision.get("entry_setup_live_policy_scope_authority")
    if authority == "operator_all_scalping_rollout":
        rollout = load_rollout(now=current)
        return bool(
            rollout
            and rollout.get("valid") is True
            and decision.get("entry_setup_live_policy_activation_sha256")
            == rollout["sha256"]
            and scope_authorized(strategy, venue, session, now=current)
        )
    if authority == "operator_all_session_auto_promotion":
        auto_promotion = load_auto_promotion(now=current)
        scope = f"{str(venue or '').strip().upper()}|{str(session or '').strip().upper()}"
        return bool(
            str(strategy or "").strip().upper() in {"SCALPING", "SCALP"}
            and auto_promotion
            and auto_promotion.get("valid") is True
            and scope in AUTO_PROMOTION_SCOPES
            and decision.get("entry_setup_live_policy_activation_sha256")
            == auto_promotion["sha256"]
        )
    return False


def main(argv: list[str] | None = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(
        description="Publish an immutable SCALPING prompt rollout authority."
    )
    parser.add_argument("--effective-from", required=True)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--auto-promotion", action="store_true")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args(argv)
    effective = datetime.fromisoformat(args.effective_from)
    if (
        effective.tzinfo is None
        or re.fullmatch(r"[0-9a-f]{40}", args.reviewed_commit) is None
    ):
        parser.error("aware effective timestamp and full reviewed commit required")
    output = Path(args.output)
    if output.exists():
        parser.error(
            "use a new immutable approval path; existing approvals cannot be overwritten"
        )
    contract = AUTO_PROMOTION_CONTRACT if args.auto_promotion else CONTRACT
    authority = (
        "all_sessions_v2_15_plus_auto_promotion_2026_09_14"
        if args.auto_promotion
        else "all_scalping_v2_14_2026_09_11"
    )
    expected_confirmation = (
        "APPLY_ALL_SESSIONS_V2_15_PLUS_AUTO_PROMOTION"
        if args.auto_promotion
        else "APPLY_ALL_SCALPING_V2_14"
    )
    if args.confirm != expected_confirmation:
        parser.error(f"--confirm must be {expected_confirmation}")
    payload = {
        **contract,
        "operator_authority": authority,
        "effective_from": effective.astimezone(KST).isoformat(),
        "reviewed_commit": args.reviewed_commit,
        "generated_at": datetime.now(KST).isoformat(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".prompt-rollout-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic publish without replacing an existing approval, including races.
        os.link(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "path": str(output.resolve()),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
