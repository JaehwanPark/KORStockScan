"""Bridge qualified episode research to an exact-date auto-expansion policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.monitoring.machine_recommendation_identity import (
    recommendation_inventory,
)
from src.trading.low_price_two_leg.profiles import profiles_for_target_date
from src.trading.order.regular_two_leg_machine import KST
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

SCHEMA = "low_price_two_leg_auto_expansion_policy_v1"
AUTHORITY = "automatic_exact_date_episode_expansion"
REPORT_SCHEMA = "low_price_two_leg_expanded_candidate_research_v6"
REPORT_DIR = DATA_DIR / "report" / "low_price_two_leg_expanded_candidate_research"
POLICY_DIR = DATA_DIR / "runtime" / "low_price_two_leg_auto_expansion"
PROMOTABLE_LANES = frozenset({"new_symbol", "existing_symbol_time_extension"})


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _next_trading_date(source_date: date) -> date:
    candidate = source_date.fromordinal(source_date.toordinal() + 1)
    while not is_krx_trading_day(candidate):
        candidate = candidate.fromordinal(candidate.toordinal() + 1)
    return candidate


def policy_path(day: date, *, policy_dir: Path = POLICY_DIR) -> Path:
    return policy_dir / f"low_price_two_leg_auto_expansion_{day.isoformat()}.json"


def _previous_profiles(
    effective_date: date, *, policy_dir: Path
) -> dict[str, dict[str, Any]]:
    candidates: list[tuple[date, Path]] = []
    for path in policy_dir.glob("low_price_two_leg_auto_expansion_*.json"):
        try:
            day = date.fromisoformat(path.stem[-10:])
        except ValueError:
            continue
        if day < effective_date:
            candidates.append((day, path))
    if not candidates:
        return {}
    payload = load_policy(max(candidates)[0], policy_dir=policy_dir)
    return {key: dict(value) for key, value in payload["profiles"].items()}


def _valid_recommendation(row: dict[str, Any]) -> bool:
    spot = row.get("recommended_spot")
    paired = row.get("paired_economics")
    try:
        return bool(
            row.get("discovery_lane") in PROMOTABLE_LANES
            and row.get("implementation_status")
            in {
                "source_only_requires_review_and_user_approval",
                "source_only_eligible_for_automatic_promotion",
            }
            and row.get("runtime_effect") is False
            and row.get("recommendation_identity_grants_authority") is False
            and isinstance(spot, dict)
            and _digest(spot) == row.get("recommendation_proposal_sha256")
            and float(row.get("notional_weighted_ev_pct")) > 0.0
            and int(row.get("holdout_signal_episodes")) >= 3
            and int(row.get("holdout_completed_legs")) >= 4
            and int(row.get("holdout_held_legs")) == 0
            and float(row.get("holdout_held_leg_rate_per_filled_leg")) == 0.0
            and float(row.get("holdout_realized_net_profit_krw_per_episode")) > 0.0
            and isinstance(paired, dict)
            and paired.get("comparable_observation_window") is True
            and paired.get("net_profit_improved") is True
            and paired.get("runtime_effect") is False
        )
    except (TypeError, ValueError):
        return False


def _mature_nonperforming_profile_ids(report: dict[str, Any]) -> set[str]:
    if int(report.get("trading_date_count") or 0) < 40:
        return set()
    retired: set[str] = set()
    for research_id, result in (report.get("profiles") or {}).items():
        if not str(research_id).startswith("logic_auto_") or not isinstance(
            result, dict
        ):
            continue
        baseline = result.get("baseline") or {}
        full = baseline.get("full") or {}
        holdout = baseline.get("holdout") or {}
        try:
            mature = (
                int(full.get("signal_episodes") or 0) >= 6
                and int(full.get("completed_legs") or 0) >= 8
                and int(holdout.get("signal_episodes") or 0) >= 3
                and int(holdout.get("completed_legs") or 0) >= 4
            )
            nonpositive = (
                float(full.get("notional_weighted_ev_pct")) <= 0.0
                and float(holdout.get("notional_weighted_ev_pct")) <= 0.0
            )
        except (TypeError, ValueError):
            continue
        if mature and nonpositive:
            retired.add(str(research_id).removeprefix("logic_"))
    return retired


def build_policy(
    *,
    source_date: date,
    report_dir: Path = REPORT_DIR,
    policy_dir: Path = POLICY_DIR,
) -> dict[str, Any]:
    report_path = report_dir / (
        f"low_price_two_leg_expanded_candidate_research_{source_date.isoformat()}.json"
    )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("episode_auto_expansion_source_unreadable") from exc
    if (
        not isinstance(report, dict)
        or report.get("schema") != REPORT_SCHEMA
        or report.get("target_date") != source_date.isoformat()
        or report.get("status")
        not in {"recommendations_ready", "no_qualified_candidate"}
        or report.get("source_quality_status", "PASS") != "PASS"
        or report.get("runtime_effect") is not False
        or report.get("allowed_runtime_apply") is not False
        or report.get("actual_order_submitted") is not False
        or report.get("broker_order_forbidden") is not True
    ):
        raise ValueError("episode_auto_expansion_source_contract_invalid")
    recommendation_inventory(report)
    effective_date = _next_trading_date(source_date)
    profiles = _previous_profiles(effective_date, policy_dir=policy_dir)
    retired_nonperforming_profile_ids = _mature_nonperforming_profile_ids(report)
    static_symbol_sessions = {
        (profile.symbol, profile.session)
        for profile in profiles_for_target_date(effective_date).values()
    }
    superseded_by_static_profile_ids = {
        profile_id
        for profile_id, row in profiles.items()
        if (str(row.get("symbol") or ""), str(row.get("session") or ""))
        in static_symbol_sessions
    }
    retired_profile_ids = (
        retired_nonperforming_profile_ids | superseded_by_static_profile_ids
    )
    for profile_id in retired_profile_ids:
        profiles.pop(profile_id, None)
    promoted: list[str] = []
    for row in report.get("recommendations") or []:
        if not isinstance(row, dict) or not _valid_recommendation(row):
            continue
        symbol = str(row.get("symbol") or "")
        session = str(row.get("session") or "")
        if (symbol, session) in static_symbol_sessions:
            continue
        profile_id = f"auto_{symbol}_{session}"
        spot = dict(row["recommended_spot"])
        profiles[profile_id] = {
            "profile_id": profile_id,
            "symbol": symbol,
            "name": str(row.get("name") or ""),
            "session": session,
            "source_recommendation_id": row["recommendation_id"],
            "source_recommendation_proposal_sha256": row[
                "recommendation_proposal_sha256"
            ],
            "policy": spot,
            "selection_status": "automatically_promoted_qualified_recommendation",
        }
        promoted.append(profile_id)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "source_date": source_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "source_report": str(report_path.resolve()),
        "source_report_sha256": _file_sha256(report_path),
        "profiles": dict(sorted(profiles.items())),
        "newly_promoted_profile_ids": sorted(promoted),
        "retired_nonperforming_profile_ids": sorted(retired_nonperforming_profile_ids),
        "superseded_by_static_profile_ids": sorted(superseded_by_static_profile_ids),
        "profile_count": len(profiles),
        "cardinality_cap": None,
        "runtime_effect": bool(profiles),
        "allowed_runtime_apply": bool(profiles),
        "actual_order_submitted": False,
        "hard_safety_preserved": True,
    }
    payload["policy_hash"] = _digest(payload)
    validate_policy(payload, effective_date=effective_date)
    return payload


def validate_policy(payload: Any, *, effective_date: date) -> None:
    if not isinstance(payload, dict):
        raise ValueError("episode_auto_expansion_policy_invalid")
    canonical = {key: value for key, value in payload.items() if key != "policy_hash"}
    profiles = payload.get("profiles")
    if (
        payload.get("schema") != SCHEMA
        or payload.get("authority") != AUTHORITY
        or payload.get("effective_date") != effective_date.isoformat()
        or payload.get("policy_hash") != _digest(canonical)
        or not isinstance(profiles, dict)
        or payload.get("profile_count") != len(profiles)
        or payload.get("cardinality_cap") is not None
        or payload.get("actual_order_submitted") is not False
        or payload.get("hard_safety_preserved") is not True
        or payload.get("runtime_effect") is not bool(profiles)
        or payload.get("allowed_runtime_apply") is not bool(profiles)
    ):
        raise ValueError("episode_auto_expansion_policy_contract_invalid")
    for profile_id, row in profiles.items():
        policy = row.get("policy") if isinstance(row, dict) else None
        if (
            not isinstance(row, dict)
            or row.get("profile_id") != profile_id
            or not profile_id.startswith("auto_")
            or len(str(row.get("symbol") or "")) != 6
            or not str(row.get("symbol") or "").isdigit()
            or not row.get("name")
            or row.get("session")
            not in {
                "morning",
                "late_morning",
                "midday",
                "afternoon",
                "integrated_aftermarket",
            }
            or not isinstance(policy, dict)
            or set(policy)
            != {
                "scan_start",
                "scan_end",
                "lookback_bars",
                "rolling_high_drawdown_pct",
                "rolling_low_proximity_pct",
                "entry_offsets_ticks",
                "entry_valid_completed_bars",
                "target_ticks",
            }
        ):
            raise ValueError("episode_auto_expansion_profile_contract_invalid")


def load_policy(day: date, *, policy_dir: Path = POLICY_DIR) -> dict[str, Any]:
    path = policy_path(day, policy_dir=policy_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("episode_auto_expansion_policy_unreadable") from exc
    validate_policy(payload, effective_date=day)
    source = Path(str(payload.get("source_report") or ""))
    if not source.is_file() or _file_sha256(source) != payload.get(
        "source_report_sha256"
    ):
        raise ValueError("episode_auto_expansion_source_hash_mismatch")
    return payload


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--policy-dir", type=Path, default=POLICY_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_policy(
        source_date=date.fromisoformat(args.source_date),
        report_dir=args.report_dir,
        policy_dir=args.policy_dir,
    )
    output = policy_path(
        date.fromisoformat(payload["effective_date"]), policy_dir=args.policy_dir
    )
    if args.write:
        _atomic_write(output, payload)
        load_policy(
            date.fromisoformat(payload["effective_date"]), policy_dir=args.policy_dir
        )
    print(
        json.dumps(
            {"output": str(output), **payload}, ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
