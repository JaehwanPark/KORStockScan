"""Dated, source-bound holding path vote policy for the next trading session.

An estimated initial bundle selects only the code baseline. It is not a
realized economic winner and it cannot change an order or a safety guard.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.ai.holding_exit_vote import (
    MARKETS, PATH_IDS, PATH_POLICY_BY_MARKET, PATH_PROMPT_VERSION,
    decide_path_snapshot, input_snapshot_id, validate_path_policy,
)


SCHEMA = "holding_path_vote_selected_policy_v1"
START_DATE = "2026-09-26"
MAX_BYTES = 1024 * 1024
ENV_PATH = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_FILE"
ENV_SHA = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_SHA256"
ENV_DATE = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_ACTIVE_DATE"


def digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")).hexdigest()


def policy_path(data_root: Path, target_date: str) -> Path:
    date.fromisoformat(target_date)
    return Path(data_root) / "threshold_cycle" / "holding_path_vote_policy" / (
        f"holding_path_vote_policy_{target_date}.json"
    )


def source_quality_from_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep the summary producer and strict consumer on one cohort projection."""
    population = observation.get("completed_population_quality") or {}
    replay = observation.get("holding_path_vote_replay") or {}
    return {
        "strict_population_count": replay.get("strict_population_count"),
        "completed_population_complete": population.get("complete"),
        "main_completed_ids": population.get("db_completed_main_ids") or [],
        "strict_completed_ids": population.get("strict_completed_position_ids") or [],
        "source_gap_ids": population.get("source_gap_ids") or [],
        "excluded_by_id": population.get("excluded_all_reasons") or {},
        "vote_replay_excluded_by_id": replay.get("excluded_by_position_id") or {},
        "source_gap_date_count": len(population.get("source_gap_dates") or []),
    }


def _scenario_decisions(path_id: str, policy: dict[str, Any]) -> dict[str, str]:
    """Expose a vote-availability envelope, not a fabricated AI or EV sample."""
    outcomes = {}
    for name, passes, vetoes, age in (
        ("all_pass", 2, 0, 0.0),
        ("all_veto", 0, 2, 0.0),
        ("mixed", 1, 1, 0.0),
        ("late", 2, 0, policy["max_latest_age_sec"] + 1.0),
        ("source_gap", 0, 0, 0.0),
    ):
        snapshot = {
            "path_id": path_id, "vote_count": passes + vetoes,
            "pass_count": passes, "veto_count": vetoes,
            "firm_pass_count": passes, "firm_veto_count": vetoes,
            "duration_sec": 10.0 if passes + vetoes else 0.0,
            "latest_vote_age_sec": age if passes + vetoes else None,
        }
        outcomes[name] = decide_path_snapshot(snapshot, policy)["decision"]
    return outcomes


def create_bundle(
    *, source_date: str, target_date: str, source_report_sha256: str,
    replay: dict[str, Any], source_quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the explicit baseline even when the natural vote cohort is empty."""
    if (date.fromisoformat(source_date).isoformat() != source_date
            or date.fromisoformat(target_date).isoformat() != target_date
            or not START_DATE <= source_date < target_date
            or not isinstance(source_report_sha256, str)
            or len(source_report_sha256) != 64
            or any(char not in "0123456789abcdef" for char in source_report_sha256)):
        raise ValueError("holding_vote_source_or_target_invalid")
    if replay.get("schema") != "holding_path_vote_postclose_replay_v1":
        raise ValueError("holding_vote_replay_schema_invalid")
    source_cells = replay.get("path_market")
    expected_keys = {f"{path}|{market}" for path in PATH_IDS for market in MARKETS}
    if not isinstance(source_cells, dict) or set(source_cells) != expected_keys:
        raise ValueError("holding_vote_replay_cells_invalid")
    quality = source_quality or {}
    if (not isinstance(quality, dict)
            or type(quality.get("strict_population_count")) is not int
            or quality["strict_population_count"] < 0
            or type(quality.get("completed_population_complete")) is not bool
            or any(not isinstance(quality.get(key), list) for key in (
                "main_completed_ids", "strict_completed_ids", "source_gap_ids"
            ))
            or not isinstance(quality.get("excluded_by_id"), dict)
            or not isinstance(quality.get("vote_replay_excluded_by_id"), dict)
            or type(quality.get("source_gap_date_count")) is not int
            or quality["source_gap_date_count"] < 0
            or len(quality["strict_completed_ids"]) != quality["strict_population_count"]
            or [str(value) for value in quality["strict_completed_ids"]]
            != [str(value) for value in replay.get("strict_completed_position_ids") or []]
            or not set(map(str, quality["strict_completed_ids"])).issubset(
                set(map(str, quality["main_completed_ids"]))
            )):
        raise ValueError("holding_vote_source_quality_invalid")
    cells = {}
    for path, market in sorted(PATH_POLICY_BY_MARKET):
        key = f"{path}|{market}"
        source = source_cells[key]
        baseline = dict(PATH_POLICY_BY_MARKET[(path, market)])
        if (not isinstance(source, dict)
                or source.get("path_id") != path or source.get("market") != market
                or source.get("runtime_policy_sha256") != input_snapshot_id(baseline)):
            raise ValueError("holding_vote_replay_baseline_mismatch")
        cells[key] = {
            "path_id": path, "market": market,
            "policy": baseline, "policy_sha256": input_snapshot_id(baseline),
            "rollback_policy_sha256": input_snapshot_id(baseline),
            "selection_reason": "baseline_prior_no_verified_paired_economics",
            "eligible_signal_count": int(source.get("eligible_signal_count") or 0),
            "strict_completed_position_count": int(source.get("strict_completed_position_count") or 0),
            "candidate_census": [
                {"axis": row["axis"], "policy_sha256": row["policy_sha256"],
                 "decision_counts": row["decision_counts"],
                 "paired_ev_krw": row["cost_after_paired_ev_krw"],
                 "censoring_status": row["censoring_status"]}
                for row in source["candidate_grid"]
            ],
            "evidence_layers": {
                "strict_realized": {
                    "completed_position_count": quality["strict_population_count"],
                    "replayable_signal_count": int(source.get("eligible_signal_count") or 0),
                    "paired_ev_krw": None,
                    "status": "counterfactual_execution_unobserved",
                },
                "reconstructed_estimate": {
                    "paired_ev_krw": None,
                    "status": "execution_and_vote_outcome_unidentified",
                },
                "stress_scenario": {
                    "decisions": _scenario_decisions(path, baseline),
                    "paired_ev_interval_krw": None,
                    "status": "decision_envelope_only",
                },
                "baseline_prior": {"policy_sha256": input_snapshot_id(baseline)},
            },
            "realized_paired_ev_krw": None,
            "estimated_paired_ev_krw": None,
            "estimate_status": "scenario_bounds_unidentified_without_model_votes",
            "scenario_decisions": _scenario_decisions(path, baseline),
        }
    bundle = {
        "schema": SCHEMA, "source_date": source_date, "target_date": target_date,
        "valid_until": target_date, "assumption_version": "unidentified_v1",
        "source_report_sha256": source_report_sha256,
        "source_quality": quality,
        "model": "gpt-5.4-nano", "prompt_version": PATH_PROMPT_VERSION,
        "evidence_grade": "estimated_provisional",
        "selection_authority": "operator_directed_initial_baseline_2026_09_26",
        "allowed_runtime_apply": True, "validated_realized_edge": False,
        "realized_paired_ev_krw": None, "estimated_paired_ev_krw": None,
        "policy_set_sha256": digest({key: row["policy_sha256"] for key, row in cells.items()}),
        "rollback_policy_set_sha256": digest({
            key: input_snapshot_id(PATH_POLICY_BY_MARKET[(path, market)])
            for (path, market) in sorted(PATH_POLICY_BY_MARKET)
            for key in (f"{path}|{market}",)
        }),
        "cells": cells,
    }
    bundle["bundle_sha256"] = digest(bundle)
    return bundle


def validate_bundle(
    bundle: Any, *, target_date: str, source_report_sha256: str | None = None,
) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise ValueError("holding_vote_policy_invalid")
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    try:
        valid_dates = (
            date.fromisoformat(bundle["source_date"]).isoformat() == bundle["source_date"]
            and date.fromisoformat(bundle["target_date"]).isoformat() == target_date
            and START_DATE <= bundle["source_date"] < target_date
        )
    except (KeyError, TypeError, ValueError):
        valid_dates = False
    if (bundle.get("schema") != SCHEMA or not valid_dates
            or bundle.get("target_date") != target_date
            or bundle.get("valid_until") != target_date
            or bundle.get("assumption_version") != "unidentified_v1"
            or bundle.get("model") != "gpt-5.4-nano"
            or bundle.get("prompt_version") != PATH_PROMPT_VERSION
            or bundle.get("evidence_grade") != "estimated_provisional"
            or bundle.get("selection_authority") != "operator_directed_initial_baseline_2026_09_26"
            or bundle.get("allowed_runtime_apply") is not True
            or bundle.get("validated_realized_edge") is not False
            or bundle.get("realized_paired_ev_krw") is not None
            or bundle.get("estimated_paired_ev_krw") is not None
            or bundle.get("bundle_sha256") != digest(unsigned)
            or not isinstance(bundle.get("source_report_sha256"), str)
            or len(bundle["source_report_sha256"]) != 64
            or any(char not in "0123456789abcdef"
                   for char in bundle["source_report_sha256"])
            or (source_report_sha256 is not None
                and bundle["source_report_sha256"] != source_report_sha256)):
        raise ValueError("holding_vote_policy_header_invalid")
    cells = bundle.get("cells")
    expected = {f"{path}|{market}" for path in PATH_IDS for market in MARKETS}
    if not isinstance(cells, dict) or set(cells) != expected:
        raise ValueError("holding_vote_policy_cells_invalid")
    quality = bundle.get("source_quality") or {}
    if (not isinstance(quality, dict)
            or type(quality.get("strict_population_count")) is not int
            or type(quality.get("completed_population_complete")) is not bool
            or not isinstance(quality.get("strict_completed_ids"), list)
            or len(quality["strict_completed_ids"]) != quality["strict_population_count"]):
        raise ValueError("holding_vote_policy_source_quality_invalid")
    hashes = {}
    for path, market in sorted(PATH_POLICY_BY_MARKET):
        key = f"{path}|{market}"
        cell = cells[key]
        baseline = PATH_POLICY_BY_MARKET[(path, market)]
        if (not isinstance(cell, dict) or cell.get("path_id") != path
                or cell.get("market") != market
                or not validate_path_policy(cell.get("policy"))
                or cell.get("policy") != baseline
                or cell.get("policy_sha256") != input_snapshot_id(baseline)
                or cell.get("rollback_policy_sha256") != input_snapshot_id(baseline)
                or cell.get("realized_paired_ev_krw") is not None
                or cell.get("estimated_paired_ev_krw") is not None
                or cell.get("scenario_decisions") != _scenario_decisions(path, baseline)):
            raise ValueError("holding_vote_policy_cell_invalid")
        layers = cell.get("evidence_layers")
        if (not isinstance(layers, dict)
                or set(layers) != {"strict_realized", "reconstructed_estimate",
                                   "stress_scenario", "baseline_prior"}
                or (layers.get("strict_realized") or {}).get("paired_ev_krw") is not None
                or (layers.get("reconstructed_estimate") or {}).get("paired_ev_krw") is not None
                or (layers.get("stress_scenario") or {}).get("paired_ev_interval_krw") is not None
                or (layers.get("baseline_prior") or {}).get("policy_sha256")
                != input_snapshot_id(baseline)
                or not isinstance(cell.get("candidate_census"), list)
                or any(not isinstance(row, dict) or row.get("paired_ev_krw") is not None
                       for row in cell["candidate_census"])):
            raise ValueError("holding_vote_policy_evidence_invalid")
        hashes[key] = cell["policy_sha256"]
    if (bundle.get("policy_set_sha256") != digest(hashes)
            or bundle.get("rollback_policy_set_sha256") != digest(hashes)):
        raise ValueError("holding_vote_policy_set_hash_invalid")
    return bundle


def load_bundle(
    data_root: Path, target_date: str, *,
    source_report_sha256: str | None = None,
) -> dict[str, Any]:
    path = policy_path(data_root, target_date)
    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
        raise ValueError("holding_vote_policy_file_invalid")
    return validate_bundle(json.loads(path.read_text(encoding="utf-8")),
                           target_date=target_date,
                           source_report_sha256=source_report_sha256)


def verify_source_handoff(data_root: Path, bundle: dict[str, Any]) -> None:
    """Require report bytes, summary receipt and terminal strict handoff."""
    root = Path(data_root)
    source_date = bundle["source_date"]
    source_file = (root / "report" / "monitor_snapshots" /
                   f"holding_exit_observation_{source_date}.json")
    summary_file = (root / "report" / "runtime_approval_summary" /
                    f"runtime_approval_summary_{source_date}.json")
    for path, limit in ((source_file, 64 * 1024 * 1024),
                        (summary_file, 8 * 1024 * 1024)):
        if path.is_symlink() or path.stat().st_size > limit:
            raise ValueError("holding_vote_source_untrusted_path_or_size")
    sha = hashlib.sha256()
    with source_file.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    if sha.hexdigest() != bundle["source_report_sha256"]:
        raise ValueError("holding_vote_source_report_hash_mismatch")
    observation = json.loads(source_file.read_text(encoding="utf-8"))
    if not isinstance(observation, dict) or observation.get("date") != source_date:
        raise ValueError("holding_vote_source_report_date_mismatch")
    expected = create_bundle(
        source_date=source_date, target_date=bundle["target_date"],
        source_report_sha256=bundle["source_report_sha256"],
        replay=observation.get("holding_path_vote_replay") or {},
        source_quality=source_quality_from_observation(observation),
    )
    if bundle != expected:
        raise ValueError("holding_vote_policy_source_semantics_mismatch")
    receipt = (json.loads(summary_file.read_text(encoding="utf-8"))
               .get("holding_path_vote_policy") or {})
    if (receipt.get("status") != "estimated_provisional_published"
            or receipt.get("source_date") != source_date
            or receipt.get("target_date") != bundle["target_date"]
            or receipt.get("bundle_sha256") != bundle["bundle_sha256"]
            or receipt.get("policy_set_sha256") != bundle["policy_set_sha256"]
            or receipt.get("source_report_sha256") != bundle["source_report_sha256"]
            or receipt.get("cell_count") != len(bundle["cells"])):
        raise ValueError("holding_vote_summary_binding_invalid")
    from src.engine.automation.postclose_summary_handoff import stage_receipt_issues
    if stage_receipt_issues(root / "report", source_date, "summary_handoff"):
        raise ValueError("holding_vote_strict_handoff_not_complete")


def runtime_policy_from_env(
    env: dict[str, str], *, data_root: Path, active_date: str | None = None,
) -> tuple[dict, dict]:
    """Load once at process start; exact code baseline is the only fallback."""
    baseline = {key: dict(value) for key, value in PATH_POLICY_BY_MARKET.items()}
    target_date = str(env.get(ENV_DATE) or "")
    today = active_date or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    if target_date and target_date != today:
        return baseline, {"status": "baseline_policy_target_date_stale",
                          "target_date": target_date, "active_date": today}
    try:
        expected_path = policy_path(data_root, target_date) if target_date else None
    except ValueError:
        expected_path = None
    if not target_date or not expected_path or env.get(ENV_PATH) != str(expected_path):
        return baseline, {"status": "baseline_policy_env_missing_or_mismatch"}
    try:
        bundle = load_bundle(data_root, target_date)
        if bundle["bundle_sha256"] != env.get(ENV_SHA):
            raise ValueError("holding_vote_policy_env_hash_mismatch")
        verify_source_handoff(data_root, bundle)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return baseline, {"status": "baseline_policy_load_rejected",
                          "reason": str(exc)}
    selected = {(path, market): dict(bundle["cells"][f"{path}|{market}"]["policy"])
                for path in PATH_IDS for market in MARKETS}
    return selected, {"status": "estimated_provisional_loaded",
                      "target_date": target_date,
                      "bundle_sha256": bundle["bundle_sha256"],
                      "source_date": bundle["source_date"]}
