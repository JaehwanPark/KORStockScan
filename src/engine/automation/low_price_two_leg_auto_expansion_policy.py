"""Bridge qualified episode research to an exact-date auto-expansion policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
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
CLOSED_LOOP_SCHEMA = "low_price_two_leg_auto_expansion_policy_v2"
AUTHORITY = "automatic_exact_date_episode_expansion"
REPORT_SCHEMA = "low_price_two_leg_expanded_candidate_research_v7"
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
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


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


def _valid_recommendation(row: dict[str, Any], *, frozen_legacy: bool = False) -> bool:
    spot = row.get("recommended_spot")
    paired = row.get("paired_economics")
    try:
        if not frozen_legacy:
            from src.engine.monitoring.low_price_two_leg_entry_spot_research import paired_economics
            reconstructed = paired_economics(
                row.get("current_economic_outcome") or {},
                row.get("candidate_economic_outcome") or {},
            )
            if paired != reconstructed:
                return False
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
            and (frozen_legacy or (
                paired.get("live_replay_supported") is True
                and (paired.get("economic_superiority_confirmed") is True
                 or paired.get("participation_net_profit_confirmed") is True)
                and paired.get("is_distinct_policy") is True
                and paired.get("comparable_terminal_economics") is True
            ))
            and paired.get("runtime_effect") is False
        )
    except (TypeError, ValueError, OverflowError, AttributeError):
        return False


def _mature_nonperforming_profile_ids(report: dict[str, Any]) -> set[str]:
    if report.get("closed_loop_contract"):
        feedback = report.get("policy_version_feedback") or {}
        cumulative = (feedback.get("cumulative") or {}).get("strategy_revisions") or {}
        holdout = (feedback.get("holdout_last_16") or {}).get(
            "strategy_revisions"
        ) or {}
        retired = set()
        for revision, full in cumulative.items():
            tail = holdout.get(revision) or {}
            try:
                if (
                    revision == "unattributed_version"
                    or full["exact_completed_count"] < 6
                    or full["exact_completed_legs"] < 8
                    or tail["exact_completed_count"] < 3
                    or tail["exact_completed_legs"] < 4
                    or float(full["realized_net_return_pct"]) > 0
                    or float(tail["realized_net_return_pct"]) > 0
                ):
                    continue
                if not all(
                    __import__("math").isfinite(float(x["realized_net_return_pct"]))
                    for x in (full, tail)
                ):
                    continue
                retired.update(
                    profile
                    for profile in full["profile_ids"]
                    if str(profile).startswith("auto_")
                )
            except (KeyError, TypeError, ValueError):
                continue
        return retired
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
    publication_date: date | None = None,
) -> dict[str, Any]:
    report_path = report_dir / (
        f"low_price_two_leg_expanded_candidate_research_{source_date.isoformat()}.json"
    )
    from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
        read_report,
    )

    try:
        report = read_report(report_path)
    except (OSError, ValueError) as exc:
        raise ValueError("episode_auto_expansion_source_unreadable") from exc
    isolated_partial = False
    if isinstance(report, dict) and report.get("status") == "partial_source_quality":
        from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import CandidateRecommendationNotifier
        # Preserve the producer's lossless quarantine contract. Partial coverage
        # permits incumbent/disabled handoff only, never a new promotion.
        isolated_partial = bool(
            report.get("source_quarantine")
            and report.get("eligible_source_symbol_count", 0) > 0
            and report.get("recommendations") == []
            and report.get("recommendation_count") == 0
            and CandidateRecommendationNotifier._valid_report(report)
        )
    if (
        not isinstance(report, dict)
        or report.get("schema") != REPORT_SCHEMA
        or report.get("target_date") != source_date.isoformat()
        or (report.get("status") not in {"recommendations_ready", "no_qualified_candidate"}
            and not isolated_partial)
        or report.get("source_quality_status", "PASS") != "PASS"
        or report.get("runtime_effect") is not False
        or report.get("allowed_runtime_apply") is not False
        or report.get("actual_order_submitted") is not False
        or report.get("broker_order_forbidden") is not True
    ):
        raise ValueError("episode_auto_expansion_source_contract_invalid")
    recommendation_inventory(report)
    from src.engine.monitoring import research_closed_loop as loop

    closed_loop = report.get("closed_loop_contract") == loop.SCHEMA
    joint = (
        loop.combined_joint_gate(report, family="episode", source_date=source_date)
        if closed_loop
        else None
    )
    if closed_loop and joint != report.get("joint_allocation_gate"):
        raise ValueError("episode_joint_allocation_reconstruction_mismatch")
    publication = publication_date or source_date
    from zoneinfo import ZoneInfo
    if not source_date <= publication <= datetime.now(ZoneInfo("Asia/Seoul")).date():
        raise ValueError("episode_publication_date_invalid")
    effective_date = _next_trading_date(publication)
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
        if profile_id in profiles:
            profiles[profile_id]["entry_runtime_eligible"] = False
            profiles[profile_id]["selection_status"] = "retired_entry_exit_custody_only"
    promoted: list[str] = []
    for row in report.get("recommendations") or []:
        if not isinstance(row, dict) or not _valid_recommendation(row):
            continue
        if closed_loop:
            from src.engine.monitoring.episode_prospective_research import (
                execution_feasibility,
                prospective_summary_valid,
            )

            result = report.get("profiles", {}).get(row.get("profile_id")) or {}
            revision = result.get("candidate_revision")
            if (
                joint.get("status") != "pass"
                or not revision
                or loop.load_candidate(
                    result.get("symbol"), owner="episode", lane_id=row.get("profile_id")
                )
                != revision
                or revision["parameters"] != row.get("recommended_spot")
                or not prospective_summary_valid(result, revision)
                or (result.get("prospective_window") or {}).get("status") != "ready"
                or loop.prospective_window(
                    revision,
                    source_date=source_date,
                    qualified_dates=(result.get("prospective_qualified_dates") or []),
                )["status"]
                != "ready"
                or execution_feasibility(result, source_date=source_date).get("status")
                != "pass"
            ):
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
            **(
                {
                    "entry_runtime_eligible": True,
                    "candidate_revision_sha256": revision["revision_sha256"],
                }
                if closed_loop
                else {}
            ),
        }
        promoted.append(profile_id)
    payload: dict[str, Any] = {
        "schema": CLOSED_LOOP_SCHEMA if closed_loop or retired_profile_ids else SCHEMA,
        **(
            {"closed_loop_contract": loop.SCHEMA, "joint_allocation_gate": joint}
            if closed_loop
            else {}
        ),
        "authority": AUTHORITY,
        "source_date": source_date.isoformat(),
        **({"source_disposition": "isolated_source_gap_incumbent_or_disabled_only",
            "source_quarantined_symbol_count": report["quarantined_source_symbol_count"]}
           if isolated_partial else {}),
        **({"publication_date": publication.isoformat()} if publication_date else {}),
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
    source = date.fromisoformat(payload["source_date"])
    publication = date.fromisoformat(payload.get("publication_date") or source.isoformat())
    if not source <= publication < effective_date or _next_trading_date(publication) != effective_date:
        raise ValueError("episode_auto_expansion_publication_date_invalid")
    canonical = {key: value for key, value in payload.items() if key != "policy_hash"}
    profiles = payload.get("profiles")
    if (
        payload.get("schema") not in {SCHEMA, CLOSED_LOOP_SCHEMA}
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

        if payload.get("schema") == CLOSED_LOOP_SCHEMA and (
            type(row.get("entry_runtime_eligible", True)) is not bool
            or row.get("selection_status") == "retired_entry_exit_custody_only"
            and row.get("entry_runtime_eligible") is not False
        ):
            raise ValueError("episode_retired_entry_contract_invalid")
        from src.trading.low_price_two_leg.auto_expansion_service import _profile

        _profile(row, authority_hash=payload["policy_hash"])


def preserve_source_snapshot(payload: dict[str, Any], *, policy_dir: Path) -> Path:
    """Keep exact original bytes independently of a later daily report refresh."""
    source = Path(payload["source_report"])
    expected = str(payload["source_report_sha256"])
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or _file_sha256(source) != expected:
        raise ValueError("episode_auto_expansion_source_hash_mismatch")
    folder = policy_dir / "source_snapshots"
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / f"{expected}.json"
    if snapshot.exists():
        if snapshot.is_symlink() or _file_sha256(snapshot) != expected:
            raise ValueError("episode_auto_expansion_snapshot_conflict")
        return snapshot
    fd, temporary = tempfile.mkstemp(prefix=".source-", dir=folder)
    try:
        with os.fdopen(fd, "wb") as destination, source.open("rb") as origin:
            shutil.copyfileobj(origin, destination, length=1024 * 1024)
            destination.flush()
            os.fsync(destination.fileno())
        if _file_sha256(Path(temporary)) != expected:
            raise ValueError("episode_auto_expansion_source_changed")
        try:
            os.link(temporary, snapshot)
        except FileExistsError:
            if snapshot.is_symlink() or _file_sha256(snapshot) != expected:
                raise ValueError("episode_auto_expansion_snapshot_conflict")
    finally:
        os.unlink(temporary)
    return snapshot


def load_policy(day: date, *, policy_dir: Path = POLICY_DIR) -> dict[str, Any]:
    path = policy_path(day, policy_dir=policy_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("episode_auto_expansion_policy_unreadable") from exc
    validate_policy(payload, effective_date=day)
    if payload.get("schema") == CLOSED_LOOP_SCHEMA:
        from src.engine.monitoring.research_closed_loop import verify_publication

        verify_publication(
            policy_dir, effective_date=day, name=path.name, value=payload
        )
    source = Path(str(payload.get("source_report") or ""))
    if not source.is_file() or _file_sha256(source) != payload.get(
        "source_report_sha256"
    ):
        expected = str(payload.get("source_report_sha256") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("episode_auto_expansion_source_hash_mismatch")
        source = policy_dir / "source_snapshots" / f"{expected}.json"
        if source.is_symlink() or not source.is_file() or _file_sha256(source) != expected:
            raise ValueError("episode_auto_expansion_source_hash_mismatch")
    if payload.get("schema") == CLOSED_LOOP_SCHEMA:
        from src.engine.monitoring import research_closed_loop as loop

        from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
            read_report,
        )

        report = read_report(source)
        source_date = date.fromisoformat(payload["source_date"])
        if (
            report.get("target_date") != str(source_date)
            or _next_trading_date(date.fromisoformat(payload.get("publication_date") or source_date.isoformat())) != day
        ):
            raise ValueError("episode_policy_source_date_invalid")
        recommendation_inventory(report)
        # The immutable source report and native publisher manifest bind the
        # gate; historical candidates are checked against their registry archive.
        previous = _previous_profiles(day, policy_dir=policy_dir)
        for profile_id, row in payload["profiles"].items():
            recommendations = [
                item
                for item in report.get("recommendations", [])
                if item.get("recommendation_id") == row.get("source_recommendation_id")
            ]
            if previous.get(profile_id) == row:
                continue
            if recommendations:
                from src.engine.monitoring.episode_prospective_research import (
                    prospective_summary_valid,
                )

                recommendation = recommendations[0]
                result = (report.get("profiles") or {}).get(
                    recommendation.get("profile_id")
                ) or {}
                revision = result.get("candidate_revision")
                if (
                    not _valid_recommendation(
                        recommendation,
                        frozen_legacy=report.get("schema")
                        == "low_price_two_leg_expanded_candidate_research_v6",
                    )
                    or row["policy"] != recommendation.get("recommended_spot")
                    or row["symbol"] != recommendation.get("symbol")
                    or row["session"] != recommendation.get("session")
                    or (report.get("joint_allocation_gate") or {}).get("status")
                    != "pass"
                    or not revision
                    or not loop.registered_revision(revision)
                    or revision["revision_sha256"]
                    != row.get("candidate_revision_sha256")
                    or revision["parameters"] != row["policy"]
                    or not prospective_summary_valid(result, revision)
                    or loop.prospective_window(
                        revision,
                        source_date=source_date,
                        qualified_dates=result.get("prospective_qualified_dates") or [],
                    )["status"]
                    != "ready"
                    or not loop.verified_execution_receipt(
                        result.get("execution_feasibility") or {}
                    )
                ):
                    raise ValueError("episode_closed_loop_reconstruction_invalid")
            else:
                parent = previous.get(profile_id)
                if parent is None:
                    raise ValueError("episode_closed_loop_parent_missing")
                inherited = dict(row)
                if row.get("entry_runtime_eligible") is False:
                    if profile_id not in set(
                        _mature_nonperforming_profile_ids(report)
                    ) | set(payload.get("superseded_by_static_profile_ids") or []):
                        raise ValueError("episode_retirement_not_declared")
                    inherited.pop("entry_runtime_eligible", None)
                    inherited.pop("selection_status", None)
                    parent = dict(parent)
                    parent.pop("entry_runtime_eligible", None)
                    parent.pop("selection_status", None)
                if inherited != parent:
                    raise ValueError("episode_closed_loop_carry_parent_mismatch")
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
    parser.add_argument("--publication-date", type=date.fromisoformat)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--policy-dir", type=Path, default=POLICY_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_policy(
        source_date=date.fromisoformat(args.source_date),
        report_dir=args.report_dir,
        policy_dir=args.policy_dir,
        publication_date=args.publication_date,
    )
    output = policy_path(
        date.fromisoformat(payload["effective_date"]), policy_dir=args.policy_dir
    )
    if args.write:
        preserve_source_snapshot(payload, policy_dir=args.policy_dir)
        if payload.get("schema") == CLOSED_LOOP_SCHEMA:
            from src.engine.monitoring.research_closed_loop import (
                publication_transaction,
                future_publication_parent,
            )

            publication_transaction(
                args.policy_dir,
                effective_date=date.fromisoformat(payload["effective_date"]),
                files={output.name: payload},
                expected_generation=future_publication_parent(
                    args.policy_dir, date.fromisoformat(payload["effective_date"])
                ),
            )
        else:
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
