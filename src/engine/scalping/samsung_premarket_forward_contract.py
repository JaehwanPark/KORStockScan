"""Freeze two offline observation hypotheses and inventory later source files.

This module does not select a runtime policy, parse API packets, collect data,
or score an unverified later source. Existing research results are discovery.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path

from src.engine.scalping import entry_setup_evidence as E, entry_strategy_policy as S
from src.engine.scalping.entry_setup_source_repair import file_sha256
from src.engine.scalping import mechanistic_entry_runtime_policy as M

SCOPE = ("PREMARKET_KRX_LIKE", "PREMARKET_KRX_LIKE")
IDS = ("distribution_buy_absorption", "flat_price_ask_depletion")
# Reviewed external anchors for this dated contract, independent of its own hash.
REVIEWED_BUNDLE_SHA256 = "3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99"
REVIEWED_PARENT_SHA256 = "656cfd8e824f3135c8a5c7f47ece789a9c1837f53e72355d298fa2602f05b011"
AUTHORITY = dict(metric_role="report_only_confirmation_research", decision_authority="offline_only",
    window_policy="frozen_20261004_discovery_then_later_independent_dates",
    sample_floor="research_binary_three_each_and_two_distinct_dates_not_publisher_support",
    primary_decision_metric="same_cost_bound_binary_winrate_against_observed_parent",
    source_quality_gate="canonical_parent_exact_nx_past_only_native_cost_and_kernel_bound",
    runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
    broker_order_forbidden=True, provider_called=False, live_selector_registered=False,
    forbidden_uses=["orders", "runtime_policy", "source_collection", "synthetic_native_support",
                    "winner_retention_veto", "realized_profit_claim"])


def kernel_seals() -> dict:
    package = Path(__file__).resolve().parent
    return {str(package / name): file_sha256(package / name) for name in (
        "samsung_premarket_forward_contract.py", "samsung_premarket_confirmation_research.py",
        "entry_setup_source_repair.py", "entry_setup_evidence.py", "entry_strategy_policy.py",
        "ai_action_outcome_calibration.py", "ai_decision_quality.py",
        "mechanistic_entry_runtime_policy.py")}


def freeze_contract(bundle: dict) -> dict:
    M.validate(bundle, target_date="2026-10-06")
    parent = M.for_cohort(bundle, SCOPE)
    if parent is None: raise ValueError("premarket_parent_missing")
    return _contract_body(parent["machine_policy"], bundle["bundle_sha256"])


def _contract_body(policy: dict, bundle_sha256: str) -> dict:
    if bundle_sha256 != REVIEWED_BUNDLE_SHA256 or S.digest(policy) != REVIEWED_PARENT_SHA256:
        raise ValueError("forward_reviewed_parent_or_bundle_changed_replan")
    threshold = policy["thresholds"]["minimum_micro_net_aggressive_delta_10t"]
    profile = (policy.get("strategy") or {}).get("nodes", {}).get("root", {}).get("profile", {})
    if profile and profile.get("minimum_micro_net_aggressive_delta_10t") != threshold:
        raise ValueError("ambiguous_root_micro_threshold")
    body = dict(schema="samsung_premarket_forward_observation_contract_v1", **AUTHORITY,
        frozen_on="2026-10-04", discovery_dates=["2026-09-29", "2026-09-30", "2026-10-02"],
        earliest_validation_date="2026-10-06", max_validation_dates=3,
        stock_code="005930", watch_origin="MAIN_FIXED_WATCH", scope=list(SCOPE),
        archive_scope=["NXT", "NXT_PREMARKET"], request_code="005930_NX",
        reviewed_bundle_sha256=bundle_sha256, parent_policy=policy,
        parent_policy_sha256=S.digest(policy), kernel_seals=kernel_seals(),
        hypotheses=[dict(id=IDS[0], phase="distribution", micro_price="nonnegative"),
                    dict(id=IDS[1], phase="any_valid_completed_phase", micro_price="zero")],
        common_confirmation=dict(minimum_delta=threshold, minimum_trade_backed_ratio=.5,
            maximum_refill_ratio=.5, minimum_depletion="strictly_positive",
            ask_window_sec=1, downward_requote=False, quote_max_age_sec=1.5,
            same_epoch_contiguous=True, same_clock_postanchor_trade_excluded=True),
        panels=dict(main="original_parent_binary_and_source_bound_cost_no_nonentry_promotion",
                    archive="ask_entry_bid_exit_price_cf_separate_from_main_native"),
        price_model=dict(horizon_sec=1200, net_target_pct=.1, gross_stop_pct=-.7,
            cost_pct=.23, quote_gap_sec=1.5, price_basis="past_ask_entry_observed_bid_exit",
            source_bound_main_cost_is_separate=True),
        admission=dict(entry="first_eligible_signal_per_panel_and_native_watch",
            reentry="after_known_terminal_only", censored="hold_model_admission_no_success_chasing",
            native="original_date_watch_admission_generation_no_synthetic_opportunities"),
        comparison=dict(baseline="observed_exact_parent_not_soft_only_price_proxy",
            diagnostic_reference="positive_micro_only_not_operating_parent",
            minimum_binary_each=3, minimum_independent_dates=2,
            winrate="candidate_strictly_above_parent_on_same_population",
            parent_empty="comparison_not_identifiable_never_zero_winrate",
            winner_retention_veto=False, reselection_allowed=False,
            costs="same_source_bound_cost_per_row_across_main_comparisons",
            missing="null_and_exclusion_ledger_not_failure_or_zero_profit"),
        stopping=dict(early_success="research_gate_pass_requires_separate_runtime_bridge",
            source_missing="waiting_no_refetch_or_new_hypothesis",
            changed_parent_or_kernel="replan_new_contract_not_silent_reseal",
            evidence_budget_end="report_unproven_or_failed_after_first_three_eligible_dates"),
        official_policy_candidate=None)
    return {**body, "content_sha256": S.digest(body)}


def validate_contract(contract: dict) -> None:
    if not isinstance(contract, dict):
        raise ValueError("forward_contract_invalid")
    if contract.get("content_sha256") != S.digest({k: v for k, v in contract.items() if k != "content_sha256"}):
        raise ValueError("forward_contract_hash_invalid")
    bundle_stub_policy = contract.get("parent_policy")
    if E.validate_mechanistic_entry_threshold_policy(bundle_stub_policy):
        raise ValueError("forward_parent_invalid")
    if contract.get("parent_policy_sha256") != S.digest(bundle_stub_policy):
        raise ValueError("forward_parent_hash_invalid")
    if (contract.get("parent_policy_sha256") != REVIEWED_PARENT_SHA256
            or contract.get("reviewed_bundle_sha256") != REVIEWED_BUNDLE_SHA256):
        raise ValueError("forward_reviewed_parent_or_bundle_changed_replan")
    if any(contract.get(k) != v for k, v in AUTHORITY.items()):
        raise ValueError("forward_authority_invalid")
    hypotheses = contract.get("hypotheses")
    bundle_hash = contract.get("reviewed_bundle_sha256")
    if (not isinstance(bundle_hash, str) or len(bundle_hash) != 64
            or any(c not in "0123456789abcdef" for c in bundle_hash)
            or not isinstance(hypotheses, list)
            or any(not isinstance(h, dict) for h in hypotheses)):
        raise ValueError("forward_contract_identity_invalid")
    if (contract.get("schema") != "samsung_premarket_forward_observation_contract_v1"
            or contract.get("scope") != list(SCOPE) or contract.get("stock_code") != "005930"
            or [h.get("id") for h in hypotheses] != list(IDS)
            or contract.get("earliest_validation_date") != "2026-10-06"
            or contract.get("official_policy_candidate") is not None):
        raise ValueError("forward_contract_scope_invalid")
    if contract.get("kernel_seals") != kernel_seals():
        raise ValueError("forward_kernel_changed_replan")
    if contract != _contract_body(bundle_stub_policy, contract["reviewed_bundle_sha256"]):
        raise ValueError("forward_frozen_spec_changed")


def hypothesis_masks(features: dict, *, guard_envelope: bool | None, contract: dict) -> dict:
    """Past-only feature interface; unknowns are null, hard guards are exclusion.

    The future consumer must independently prove canonical/route/native joins
    and invoke the original guard owner before setting guard_envelope=True.
    """
    validate_contract(contract)
    if guard_envelope is False:
        return dict(status="guard_excluded", masks={key: False for key in IDS})
    if guard_envelope is not True:
        return dict(status="source_gap", masks={key: None for key in IDS})
    numeric = ("delta", "price_pct", "proof", "depletion", "refill")
    if (features.get("usable") is not True or features.get("past_exact_nx_bound") is not True
            or features.get("phase") not in E.STRUCTURE_PHASES
            or any(type(features.get(k)) not in (int, float) or not math.isfinite(features[k]) for k in numeric)
            or type(features.get("downward")) is not bool
            or not 0 <= features["proof"] <= 1 or not 0 <= features["refill"]):
        return dict(status="source_gap", masks={key: None for key in IDS})
    common = contract["common_confirmation"]
    positive = bool(features["delta"] >= common["minimum_delta"]
        and features["depletion"] > 0 and features["proof"] >= common["minimum_trade_backed_ratio"]
        and features["refill"] <= common["maximum_refill_ratio"] and features["downward"] is False)
    return dict(status="observed", masks={IDS[0]: positive and features["phase"] == "distribution"
        and features["price_pct"] >= 0, IDS[1]: positive and features["price_pct"] == 0})


def source_inventory(root: Path, day: str, contract: dict) -> dict:
    """Read-only readiness inventory; file presence does not prove semantic validity."""
    validate_contract(contract)
    if date.fromisoformat(day).isoformat() != day or day < contract["earliest_validation_date"]:
        raise ValueError("prefreeze_validation_date")
    projection = root / f"data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json"
    if Path(str(projection) + ".gz").is_file(): projection = Path(str(projection) + ".gz")
    capture = root / f"data/ai_decision_payloads/ai_decision_payloads_{day}.jsonl"
    if not capture.is_file(): capture = Path(str(capture) + ".gz")
    archive = root / f"data/observations/scalp_micro_reversion_forward/trade_date={day}/venue=NXT/session=NXT_PREMARKET"
    required = [projection, capture, archive / "market_stream.manifest.json", archive / "market_depth_stream.manifest.json"]
    missing = [str(p) for p in required if not p.is_file()]
    available = {str(p): file_sha256(p) for p in required if p.is_file()}
    status = ("waiting_new_source_date" if not available else "waiting_source_materialization") if missing else "source_present_validation_pending"
    body = dict(schema="samsung_premarket_forward_source_inventory_v1", **AUTHORITY,
        day=day, status=status, missing_source_paths=missing, available_source_seals=available,
        frozen_contract_sha256=contract["content_sha256"], source_semantics_verified=False,
        parent_policy_consumption_verified=False, data_collected=False, performance_verified=False,
        official_policy_candidate=None)
    return {**body, "content_sha256": S.digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prepare-date", default="2026-10-06")
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if not destination.is_relative_to(Path("tmp").resolve()) or destination.exists():
        parser.error("output must be a new directory inside workspace tmp")
    contract = freeze_contract(json.loads(args.bundle.read_text()))
    inventory = source_inventory(Path.cwd(), args.prepare_date, contract)
    destination.mkdir(parents=True)
    for name, value in (("frozen-contract.json", contract), ("source-inventory.json", inventory)):
        (destination / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"hypotheses": len(contract["hypotheses"]), "status": inventory["status"]}))


if __name__ == "__main__":
    main()
