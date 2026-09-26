"""Publish a bounded, source-bound trailing classifier selection for PREOPEN.

The postclose report is research. Only this reviewed deterministic handoff may
create an apply receipt, and bootstrap checks it again before any runtime env.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.automation.runtime_policy_bootstrap import build_manifest
from src.engine.scalping.trailing_mechanical_policy import (
    CLASSIFIER_VERSION, SELECTED_SCHEMA, START_MARKETS, classifier_hash,
    market_values_hash, selected_policy_env,
)
from src.utils.constants import DATA_DIR

FAMILY = "scalp_trailing_mechanical_three_axis_selector"
REPORT_DIR = DATA_DIR / "report" / "monitor_snapshots"
POLICY_DIR = DATA_DIR / "report" / "scalp_trailing_mechanical_policy"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"scalp_trailing_mechanical_policy_{target_date}.json"


def _latest_manifest(target_date: str) -> Path | None:
    manifests = sorted((REPORT_DIR / "manifests").glob(
        "monitor_snapshot_manifest_*_postclose_exit.json"
    ))
    eligible = [path for path in manifests
                if path.name.split("_")[3] < target_date]
    return eligible[-1] if eligible else None


def _source(target_date: str) -> tuple[dict[str, Any], bytes, str, str]:
    manifest_path = _latest_manifest(target_date)
    if manifest_path is None:
        raise ValueError("postclose_exit_manifest_missing")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    source_date = str(manifest.get("target_date") or "")
    if (manifest.get("profile") != "postclose_exit"
            or date.fromisoformat(source_date).isoformat() != source_date
            or not "2026-06-05" <= source_date < target_date
            or (date.fromisoformat(target_date) - date.fromisoformat(source_date)).days > 7
            or set(manifest.get("snapshot_kinds") or []) != {
                "trade_review", "post_sell_feedback", "holding_exit_observation"
            }):
        raise ValueError("postclose_exit_manifest_invalid")
    source_bytes = {}
    for kind in ("trade_review", "post_sell_feedback", "holding_exit_observation"):
        expected = REPORT_DIR / f"{kind}_{source_date}.json"
        recorded = (manifest.get("snapshot_paths") or {}).get(kind)
        if not isinstance(recorded, str) or Path(recorded).resolve() != expected.resolve():
            raise ValueError(f"postclose_exit_{kind}_path_mismatch")
        raw = expected.read_bytes()
        if _sha(raw) != (manifest.get("snapshot_sha256") or {}).get(kind):
            raise ValueError(f"postclose_exit_{kind}_hash_mismatch")
        source_bytes[kind] = raw
    report_bytes = source_bytes["holding_exit_observation"]
    report = json.loads(report_bytes)
    if (report.get("date") != source_date
            or (report.get("meta") or {}).get("snapshot_profile") != "postclose_exit"):
        raise ValueError("postclose_exit_report_generation_mismatch")
    return report, report_bytes, source_date, _sha(manifest_bytes)


def build_selection(target_date: str) -> dict[str, Any]:
    date.fromisoformat(target_date)
    result: dict[str, Any] = {
        "schema": SELECTED_SCHEMA, "family": FAMILY,
        "target_date": target_date, "allowed_runtime_apply": False,
        "runtime_effect": False, "status": "hold_source_gap",
        "runtime_env_overrides": {},
    }
    try:
        report, report_bytes, source_date, manifest_sha = _source(target_date)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result["reason"] = f"source:{type(exc).__name__}:{exc}"
        return result
    result.update(source_date=source_date, source_report_sha256=_sha(report_bytes),
                  source_manifest_sha256=manifest_sha)
    research = report.get("trailing_mechanical_market_tuning") or {}
    candidate = research.get("research_candidate") or {}
    if (not (report.get("mechanical_population_quality") or {}).get("complete")
            or research.get("population_complete") is not True):
        result.update(status="hold_source_gap", reason="mechanical_population_incomplete")
        return result
    if (research.get("status") != "research_candidate_holdout_positive_review_required"
            or not candidate):
        result.update(status="hold_sample_or_edge", reason=research.get("status"))
        return result
    try:
        parent = build_manifest(target_date)["scalp_trailing_mechanical_policy_receipt"]
        values = candidate["values"]
        classifier_values = candidate["classifier_parameters"]
        digest = market_values_hash(values, classifier_values)
        if digest != candidate["market_values_sha256"]:
            raise ValueError("candidate_digest_mismatch")
        changed = [market for market in START_MARKETS
                   if (values[market] != parent["market_values"][market]
                       or classifier_values[market] != parent["classifier_parameters"][market])]
        if len(changed) != 1:
            raise ValueError("one_market_canary_required")
        evidence = research["joint_selection_evidence"]
        if (evidence.get("winner_sha256") != digest
                or evidence.get("tail_review_required") is not False
                or any(not isinstance(evidence.get(key), (int, float))
                       or evidence[key] <= 0 for key in (
                           "holdout_conservative_delta_krw",
                           "holdout_conservative_worst_slippage_delta_krw",
                           "holdout_worst_slippage_min_day_ev_pct",
                       ))):
            raise ValueError("candidate_economics_or_safety_invalid")
        policy = {
            **result,
            "status": "reviewed_one_stage_canary",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
            "apply_scope": "one_stage_canary",
            "changed_market": changed[0],
            "market_values": values,
            "classifier_parameters": classifier_values,
            "market_values_sha256": digest,
            "classifier_version": CLASSIFIER_VERSION,
            "classifier_sha256": classifier_hash(classifier_values),
            "candidate_grid_sha256": (research.get("classifier_policy_research") or {}).get(
                "grid_sha256") or research.get("grid_sha256"),
            "rollback_market_values_sha256": parent["market_values_sha256"],
            "selection_review": {
                "status": "reviewed_one_stage_canary",
                "candidate_sha256": digest,
                "source_quality": "pass",
                "execution_model": "pass",
                "same_stage_owner": "scalp_trailing_take_profit",
                "rollback_sha256": parent["market_values_sha256"],
            },
        }
        policy["runtime_env_overrides"] = selected_policy_env(
            policy, report, target_date=target_date,
            report_sha256=_sha(report_bytes),
        )
    except (KeyError, TypeError, ValueError) as exc:
        result.update(status="hold_selection_contract", reason=str(exc))
        return result
    return policy


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    selection = build_selection(args.target_date)
    if args.write:
        _write(policy_path(args.target_date), selection)
    print(json.dumps({"target_date": args.target_date,
                      "status": selection["status"],
                      "allowed_runtime_apply": selection["allowed_runtime_apply"],
                      "path": str(policy_path(args.target_date)) if args.write else None},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
