"""Publish a reviewed next-session market-weakness hysteresis policy.

The source report owns counterfactual labeling and deterministic holdout review.
This producer only converts a passed recommendation (or the current reviewed
policy) into an exact-date policy.  It never mutates a running process or
submits an order.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.risk.market_weakness_threshold_policy import (
    AUTHORITY,
    ALLOWED_ACTIVATION_OBSERVATIONS,
    ALLOWED_RELEASE_OBSERVATIONS,
    BASELINE_ACTIVATION_OBSERVATIONS,
    BASELINE_RELEASE_OBSERVATIONS,
    CLEAN_BASELINE_DATE,
    DEFAULT_POLICY_DIR,
    DEFAULT_SOURCE_REPORT_DIR,
    MIN_OBSERVATION_SPACING_SEC,
    canonical_sha256,
    next_krx_trading_day,
    policy_path,
    threshold_hash,
    validate_threshold_recommendation,
    validate_applied_policy,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
REPORT_SCHEMA = "market_weakness_hysteresis_tuning_report_v1"
OUTPUT_DIR = DATA_DIR / "report" / "market_weakness_hysteresis_tuning"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_outputs(
    *,
    source_date: date,
    source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_path = (
        source_report_dir
        / f"machine_microstructure_attribution_{source_date.isoformat()}.json"
    )
    source = _read_json(source_path)
    response = (
        source.get("market_weakness_entry_response")
        if isinstance(source, dict)
        else None
    )
    source_contract_valid = bool(
        isinstance(source, dict)
        and source.get("schema") == "machine_microstructure_attribution_v1"
        and source.get("target_date") == source_date.isoformat()
        and isinstance(response, dict)
        and response.get("schema") == "machine_market_weakness_response_v2"
        and response.get("target_date") == source_date.isoformat()
        and (response.get("authority") or {}).get("runtime_effect") is False
        and (response.get("authority") or {}).get("allowed_runtime_apply") is False
        and (response.get("authority") or {}).get("broker_order_forbidden") is True
    )
    if not source_contract_valid:
        raise ValueError("market_weakness_hysteresis_source_report_invalid")
    assert isinstance(response, dict)
    recommendation = response.get("threshold_recommendation")
    recommendation_valid, recommendation_reason = validate_threshold_recommendation(
        recommendation
    )
    if not recommendation_valid:
        raise ValueError(recommendation_reason)
    assert isinstance(recommendation, dict)
    current = recommendation.get("current_policy")
    if not isinstance(current, dict):
        raise ValueError("market_weakness_hysteresis_current_policy_missing")
    try:
        current_activation = int(current["activation_unique_observations"])
        current_release = int(current["release_unique_observations"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("market_weakness_hysteresis_current_policy_invalid") from exc
    if (
        current_activation not in ALLOWED_ACTIVATION_OBSERVATIONS
        or current_release not in ALLOWED_RELEASE_OBSERVATIONS
    ):
        raise ValueError("market_weakness_hysteresis_current_policy_out_of_bounds")
    selected = recommendation.get("selected_policy")
    selected = selected if isinstance(selected, dict) else None
    try:
        selected_activation = (
            int(selected["activation_unique_observations"])
            if selected is not None
            else None
        )
        selected_release = (
            int(selected["release_unique_observations"])
            if selected is not None
            else None
        )
    except (KeyError, TypeError, ValueError):
        selected_activation = None
        selected_release = None
    selected_valid = bool(
        recommendation.get("policy_candidate_ready") is True
        and selected is not None
        and selected.get("review_status") == "passed_out_of_sample_review"
        and selected_activation in ALLOWED_ACTIVATION_OBSERVATIONS
        and selected_release in ALLOWED_RELEASE_OBSERVATIONS
        and int(selected_activation != current_activation)
        + int(selected_release != current_release)
        == 1
        and abs(selected_activation - current_activation) <= 1
        and abs(selected_release - current_release) <= 1
    )
    if (
        recommendation.get("policy_candidate_ready") is True or selected is not None
    ) and not selected_valid:
        raise ValueError("market_weakness_hysteresis_selected_policy_invalid")
    activation = int(selected_activation) if selected_valid else current_activation
    release = int(selected_release) if selected_valid else current_release
    review_status = (
        "passed_out_of_sample_review"
        if selected_valid
        else "current_policy_carry_forward_no_approved_candidate"
    )
    effective_date = next_krx_trading_day(source_date)
    source_hash = canonical_sha256(source)
    review_hash = str(recommendation.get("review_hash") or "")
    applied = {
        "schema": "market_weakness_hysteresis_policy_applied_v1",
        "target_date": effective_date.isoformat(),
        "source_date": source_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "decision_authority": AUTHORITY,
        "source_report": str(source_path),
        "source_report_canonical_sha256": source_hash,
        "prior_activation_unique_observations": current_activation,
        "prior_release_unique_observations": current_release,
        "activation_unique_observations": activation,
        "release_unique_observations": release,
        "minimum_observation_spacing_sec": MIN_OBSERVATION_SPACING_SEC,
        "policy_hash": threshold_hash(activation=activation, release=release),
        "selection_status": (
            "selected_reviewed_single_hysteresis_axis"
            if selected_valid
            else "current_policy_carry_forward_no_approved_candidate"
        ),
        "review": {
            "status": review_status,
            "method": recommendation.get("review_method"),
            "source_review_hash": review_hash,
            "selected_evidence": selected if selected_valid else None,
        },
        "rollback": {
            "activation_unique_observations": BASELINE_ACTIVATION_OBSERVATIONS,
            "release_unique_observations": BASELINE_RELEASE_OBSERVATIONS,
            "trigger": (
                "missing_invalid_or_mismatched_exact_date_policy_or_source_report"
            ),
        },
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "forbidden_uses": [
            "same_day_hot_threshold_mutation",
            "breadth_definition_or_release_margin_change",
            "main_bot_entry_or_exit_change",
            "price_quantity_target_holding_or_exit_change",
            "broker_guard_or_order_owner_change",
        ],
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }
    valid, reason = validate_applied_policy(applied, target_date=effective_date)
    if not valid:
        raise ValueError(f"generated_market_weakness_policy_invalid:{reason}")
    report = {
        "schema": REPORT_SCHEMA,
        "target_date": source_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "status": (
            "reviewed_candidate_selected"
            if selected_valid
            else "current_policy_carried_forward"
        ),
        "source_report": str(source_path),
        "source_report_canonical_sha256": source_hash,
        "source_contract_valid": source_contract_valid,
        "review_hash": review_hash,
        "selected_policy": selected if selected_valid else None,
        "prior_policy": {
            "activation_unique_observations": current_activation,
            "release_unique_observations": current_release,
        },
        "applied_policy_hash": applied["policy_hash"],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return report, applied


def render_markdown(report: dict[str, Any], applied: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Market Weakness Hysteresis Tuning — {report['target_date']}",
            "",
            f"- Status: `{report['status']}`",
            f"- Effective date: `{report['effective_date']}`",
            (
                "- Thresholds: activation "
                f"`{applied['activation_unique_observations']}`, release "
                f"`{applied['release_unique_observations']}`"
            ),
            f"- Review: `{applied['review']['status']}`",
            f"- Policy hash: `{applied['policy_hash']}`",
            "- Runtime application: next exact KRX session only; no intraday hot mutation.",
            "",
        ]
    )


def write_outputs(
    report: dict[str, Any],
    applied: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    policy_dir: Path = DEFAULT_POLICY_DIR,
) -> tuple[Path, Path, Path]:
    report_path = (
        output_dir / f"market_weakness_hysteresis_tuning_{report['target_date']}.json"
    )
    markdown_path = report_path.with_suffix(".md")
    applied_path = policy_path(
        date.fromisoformat(applied["target_date"]), policy_dir=policy_dir
    )
    _atomic_write_json(report_path, report)
    _atomic_write_text(markdown_path, render_markdown(report, applied))
    _atomic_write_json(applied_path, applied)
    return report_path, markdown_path, applied_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report, applied = build_outputs(source_date=date.fromisoformat(args.target_date))
    paths = write_outputs(report, applied) if args.write else ()
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "effective_date": report["effective_date"],
                    "activation_unique_observations": applied[
                        "activation_unique_observations"
                    ],
                    "release_unique_observations": applied[
                        "release_unique_observations"
                    ],
                    "paths": [str(path) for path in paths],
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
