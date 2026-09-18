"""Offline compact adjudication replay shared by the existing batch and publisher.

No CLI, broker client or policy publisher lives here. Natural input is streamed
once into a small immutable projection. Missing execution economics stays null.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
import fcntl
import hashlib
import gzip
import json
import math
import os
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "compact_auxiliary_paired_economic_v1"
AUTHORITY = dict(
    runtime_effect=False,
    allowed_runtime_apply=False,
    actual_order_submitted=False,
    broker_order_forbidden=True,
)
CONTRACT = {
    "schema": "compact_auxiliary_paired_promotion_v6",
    "learning_episode_floor": 20,
    "holdout_episode_floor": 20,
    "holdout_source_day_floor": 2,
    "minimum_response_coverage": 1.0,
    "same_cohort_only": True,
    "missing_economics_imputed": False,
    "positive_net_delta_required": True,
    "positive_portfolio_daily_delta_required": True,
    "tail_must_not_worsen": True,
    "stress_delta_must_be_positive": True,
    "runtime_inference_cost_delta_required": True,
    "validated_owner_operating_model_required": True,
    "operating_arm_and_scope_required": True,
    "model_holdout_precedes_prompt_learning": True,
    "empirical_error_and_stress_lower_bound_required": True,
}
SOURCE_PROJECTION_CONTRACT = "compact_pre_ai_execution_source_v4"


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def sealed(value):
    value = {k: v for k, v in value.items() if k != "artifact_content_sha256"}
    return {**value, "artifact_content_sha256": digest(value)}


def valid(value):
    try:
        return bool(value and value == sealed(value))
    except (ValueError, TypeError):
        return False


def read(path):
    try:
        actual = path if path.exists() else Path(str(path) + ".gz")
        # Producers publish atomic JSON generations; full frozen operating
        # snapshots can legitimately exceed the old 16 MiB diagnostic limit.
        opener = gzip.open if actual.suffix == ".gz" else open
        with opener(actual, "rt") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".compact-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        Path(name).replace(path)
    finally:
        Path(name).unlink(missing_ok=True)


def report_path(data_root, day):
    return (
        Path(data_root)
        / "report/ai_entry_setup_paired_replay_batch"
        / f"compact_auxiliary_paired_economic_{day}.json"
    )


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def owner_replay_valid(replay, row):
    from src.engine.scalping.strategy_owner_replay import (
        _entry_seed_valid,
        ENTRY_REPLAY_SCHEMA,
    )
    from src.engine.monitoring.research_closed_loop import digest as owner_digest

    seed = replay.get("seed") or {}
    return bool(
        replay.get("schema") == ENTRY_REPLAY_SCHEMA
        and replay.get("status") == "completed_source_only"
        and replay.get("replay_sha256")
        == owner_digest({k: v for k, v in replay.items() if k != "replay_sha256"})
        and _entry_seed_valid(seed)
        and seed.get("source_date") == row.get("source_date")
        and seed.get("evaluation_attempt_id") == row.get("evaluation_attempt_id")
        and seed.get("scanner_promotion_id") == row.get("scanner_promotion_id")
        and seed.get("stock_code") == row.get("stock_code")
        and seed.get("effective_venue") == row.get("effective_venue")
        and seed.get("session_bucket") == row.get("session_bucket")
    )


def owner_operating_arm(replay, row):
    """Use the independently closed holding outcome, never the research arm."""
    from src.engine.scalping import entry_split_order_plan as split
    from src.engine.scalping.strategy_owner_replay import (
        ENTRY_OPERATING_SCHEMA, entry_operating_model_identity, entry_operating_route_supported,
    )
    from src.engine.monitoring.research_closed_loop import digest as owner_digest
    if not owner_replay_valid(replay, row):
        return {}
    seed = replay["seed"]
    context = seed.get("operating_contract") or {}
    arm = (replay.get("operating_arms") or {}).get(split.QUANTITY_LEG_FOUR_ARM_IDS[0]) or {}
    if (
        context.get("schema") != ENTRY_OPERATING_SCHEMA
        or context.get("broker_route") != row.get("broker_route")
        or not entry_operating_route_supported(seed.get("effective_venue"), seed.get("session_bucket"), context.get("broker_route"))
        or context.get("sha256") != owner_digest({k: v for k, v in context.items() if k != "sha256"})
        or context.get("model_implementation_sha256") != entry_operating_model_identity()
        or arm.get("schema") != ENTRY_OPERATING_SCHEMA
        or arm.get("status") != "completed_source_only"
        or arm.get("sha256") != split._canonical_sha256({k: v for k, v in arm.items() if k != "sha256"})
        or arm.get("actual_fill_evidence") is not False
        or any(arm.get(k) is not v for k, v in AUTHORITY.items())
        or arm.get("requested_qty") != seed.get("total_qty")
        or arm.get("modeled_filled_qty") != seed.get("total_qty")
        or arm.get("fill_participation_rate") != 1
        or arm.get("contract_sha256") != context.get("sha256")
        or arm.get("exit_policy_sha256") != context.get("exit_policy_version")
        or arm.get("cost_policy_version") != context.get("cost_policy_version")
        or arm.get("cost_provenance") != "frozen_loaded_trade_profit_configuration_not_broker_settlement"
        or arm.get("budget_krw") != context.get("budget_krw")
        or not finite(arm.get("budget_krw")) or arm["budget_krw"] <= 0
        or not split._valid_generation_id(arm.get("terminal_evidence_sha256"))
        or any(not finite(arm.get(k)) for k in ("net_pnl_krw", "stress_net_pnl_krw", "net_return_pct", "stress_net_return_pct"))
        or abs(arm["net_return_pct"] - arm["net_pnl_krw"] / arm["budget_krw"] * 100) > 1e-10
        or abs(arm["stress_net_return_pct"] - arm["stress_net_pnl_krw"] / arm["budget_krw"] * 100) > 1e-10
    ):
        return {}
    return arm


def owner_model_scope_valid(model, pair):
    from src.engine.scalping import entry_split_order_plan as split
    from src.engine.scalping.strategy_owner_replay import ENTRY_MODEL_SELECTION
    seed = pair["owner_replay"]["seed"]
    scope = split._entry_operating_scope(seed)
    for proof in model.get("validated_scopes") or []:
        if not isinstance(proof, dict) or proof.get("scope_sha256") != scope:
            continue
        cal, held = proof.get("calibration_rows"), proof.get("holdout_rows")
        if not isinstance(cal, list) or not isinstance(held, list):
            continue
        rows = cal + held
        if (
            proof.get("contract") == ENTRY_MODEL_SELECTION
            and proof.get("validated") is True
            and proof.get("sha256") == split._canonical_sha256({k: v for k, v in proof.items() if k != "sha256"})
            and proof.get("actual_rows_sha256") == split._canonical_sha256(rows)
            and proof.get("calibration_attempt_count") == len(proof.get("calibration_rows") or [])
            and proof.get("holdout_attempt_count") == len(proof.get("holdout_rows") or [])
            and len(rows) >= 20 and cal and held
            and len({r.get("episode_id") for r in rows if isinstance(r, dict)}) == len(rows)
            and isinstance(proof.get("available_after_date"), str)
            and proof["available_after_date"] < pair["source_date"]
            and all(isinstance(r, dict) and r.get("scope_sha256") == scope
                    and isinstance(r.get("source_date"), str) and r["source_date"] < pair["source_date"]
                    and isinstance(r.get("completion_date") or r["source_date"], str)
                    and (r.get("completion_date") or r["source_date"]) <= proof["available_after_date"]
                    and r.get("episode_id") != seed.get("entry_plan_sha256") for r in rows)
        ):
            dimensions = ("vwap_error_bps", "receipt_clock_error_sec", "quantity_error",
                          "net_error_budget_pct", "capital_error_minutes", "reserve_error_minutes")
            if not all(all(finite(r.get(k)) for k in dimensions)
                       and r.get("false_fill") is False and r.get("missed_fill") is False
                       and r.get("quantity_error") == 0 for r in rows):
                continue
            tolerance = {k: max(abs(r[k]) for r in cal) for k in dimensions}
            if (proof.get("tolerance") != tolerance
                or any(abs(r[k]) > tolerance[k] + 1e-12 for r in held for k in dimensions)
                or proof.get("optimistic_net_error_budget_pct") != max([0.] + [r["net_error_budget_pct"] for r in held])):
                continue
            return True
    return False


def runtime_inference_cost_receipt(root, day):
    """Use the existing reviewed accounting owner; never invent an FX rate.

    The currently supported accounting contract is explicit operator zero
    pricing. Nonzero USD pricing needs a reviewed KRW conversion owner and
    measured token deltas, and is a contract gap rather than free inference.
    """
    from src.engine.scalping.micro_reversion.provider_budget import (
        load_reviewed_pricing_artifact, OPERATOR_ZERO_COST_BASIS, ProviderBudgetError)
    path = Path(root) / "policy/micro_reversion/provider_pricing.json"
    try:
        pricing = load_reviewed_pricing_artifact(path, as_of_date=date.fromisoformat(day))
        price = pricing.price_for("openai", "gpt-5.4-nano")
        if (pricing.pricing_basis != OPERATOR_ZERO_COST_BASIS
            or price.input_usd_per_million_tokens != 0 or price.output_usd_per_million_tokens != 0):
            raise ValueError("reviewed_nonzero_runtime_krw_conversion_and_token_delta_contract_required")
        return dict(status="reviewed_operator_zero_cost", delta_krw=0.,
            pricing_path=str(path), pricing_file_sha256=pricing.artifact_file_sha256,
            pricing_content_sha256=pricing.artifact_content_sha256,
            raw_source_sha256=pricing.raw_source_bytes_sha256,
            effective_from=pricing.effective_from.isoformat(), effective_to=pricing.effective_to.isoformat(),
            basis=pricing.pricing_basis, provider="openai", model="gpt-5.4-nano")
    except (OSError, ValueError, ProviderBudgetError) as exc:
        return dict(status="source_gap", delta_krw=None, blocker=str(exc),
            owner="micro_reversion_reviewed_provider_pricing",
            closure_test="effective_reviewed_zero_accounting_or_reviewed_measured_token_and_krw_conversion_contract")


def operating_comparison_metrics(pairs, model):
    """Both decision filters share frozen quantity, budget, and holding owner.

    Reuse existing economic metrics and single-position reservations. The lower
    bound is an observed error/stress envelope, not a confidence interval.
    Unchanged decisions cancel model error; inference deltas still count.
    """
    from copy import deepcopy
    from src.engine.scalping import entry_split_order_plan as split
    empty = dict(status="source_gap", incumbent=None, candidate=None,
        robust_paired_delta_ev_lower_bound_pct=None, model_error_penalty_pct=None,
        blocker="validated_operating_scope_exposure_or_runtime_cost_missing",
        owner="entry_execution_model_scope_and_reviewed_provider_pricing",
        closure_test="independent_prior_model_holdout_exact_scope_and_complete_frozen_exposure_witnesses")
    if not pairs:
        return empty
    old_rows, new_rows, lower, penalties = [], [], [], []
    for pair in pairs:
        replay = pair.get("owner_replay") or {}
        arm = owner_operating_arm(replay, pair)
        if not arm or not owner_model_scope_valid(model, pair):
            return empty
        cost = pair.get("runtime_inference_cost_delta_krw")
        if not finite(cost) or any(not finite(arm.get(k)) or arm[k] < 0
            for k in ("capital_krw_minutes", "reserve_krw_minutes")):
            return empty
        proof = next(p for p in model["validated_scopes"]
                     if p["scope_sha256"] == split._entry_operating_scope(replay["seed"]))
        changed = pair["candidate_verdict"] != pair["incumbent_verdict"]
        error = 2 * max(proof["optimistic_net_error_budget_pct"], proof["tolerance"]["net_error_budget_pct"])
        penalty = error if changed else 0.
        penalties.append(penalty)
        lower.append(min(pair["delta_net_pct"], pair["stress_delta_net_pct"]) - penalty
                     - cost / arm["budget_krw"] * 100)
        for verdict, rows, inference in ((pair["incumbent_verdict"], old_rows, 0.),
                                          (pair["candidate_verdict"], new_rows, cost)):
            selected = verdict == "PASS"
            output = deepcopy(arm)
            for k in ("net_pnl_krw", "capital_krw_minutes", "reserve_krw_minutes", "fill_participation_rate"):
                output[k] *= int(selected)
            output["net_pnl_krw"] -= inference
            rows.append(dict(budget_krw=arm["budget_krw"], arms={"decision": output}))
    portfolio = portfolio_metrics(pairs)
    if portfolio["portfolio_daily_net_delta_krw"] is None:
        return {**empty, "status": "unsupported_scope", "blocker": "overlapping_owner_capital_allocation_unsupported"}
    return dict(status="supported_operating_comparison", blocker=None,
        incumbent=split._economic_metrics(old_rows, "decision"),
        candidate=split._economic_metrics(new_rows, "decision"),
        robust_paired_delta_ev_lower_bound_pct=sum(lower) / len(lower),
        model_error_penalty_pct=sum(penalties) / len(penalties),
        lower_bound_method="mean_same_pair_minimum_base_stress_delta_minus_changed_decision_two_arm_empirical_error_and_inference_cost",
        **portfolio)


def prepare(data_root, day):
    """Use actual compact screens, never fabricated AI for machine BLOCK rows."""
    from src.utils.jsonl_io import iter_jsonl, existing_or_gzip_path
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.scalping.mechanistic_entry_runtime_policy import COMPACT_AI_VARIANTS

    root = Path(data_root)
    source = read(
        root
        / "report/observation_source_quality_audit"
        / f"observation_source_quality_audit_{day}.json"
    )
    receipt = source.get("machine_ai_natural_source_consumption") or {}
    manifest = receipt.get("source_manifest") or {}
    traces, conflicts = {}, set()
    trace_path = existing_or_gzip_path(
        root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl"
    )
    for trace in iter_jsonl(trace_path) if trace_path else []:
        if (
            trace.get("decision_stage") != "entry_screen"
            or trace.get("prompt_version") not in COMPACT_AI_VARIANTS
            or trace.get("provider_called") is not True
            or trace.get("entry_mechanistic_action") != "ENTER_NOW"
        ):
            continue
        key = trace.get("decision_trace_id")
        if not key:
            continue
        if key in traces and traces[key] != trace:
            conflicts.add(key)
        traces[key] = trace
    wanted = {t.get("payload_sha256") for t in traces.values()}
    payloads, payload_conflicts = {}, set()
    payload_path = existing_or_gzip_path(
        root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl"
    )
    for payload in iter_jsonl(payload_path) if payload_path else []:
        key = (
            payload.get("request_envelope_sha256"),
            payload.get("payload_sha256"),
            payload.get("prompt_sha256"),
        )
        if payload.get("payload_sha256") not in wanted:
            continue
        if key in payloads and payloads[key] != payload:
            payload_conflicts.add(key)
        payloads[key] = payload
    labels = read(
        root
        / "report/ai_decision_outcome_labels"
        / f"ai_decision_outcome_labels_{day}.json"
    )
    by_trace = {r.get("decision_trace_id"): r for r in labels.get("labels", [])}
    split = read(
        root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json"
    )
    summary = split.get("input_summary") or {}
    owner_source = (summary.get("compact_pre_ai_execution_replay")
        or summary.get("entry_opportunity_executable_replay_refresh")
        or (summary.get("daily_diagnostic") or {}).get("entry_opportunity_executable_replay") or {})
    owner_rows = {
        r.get("seed", {}).get("evaluation_attempt_id"): r
        for r in owner_source.get("rows", [])
    }
    rows, exclusions = [], Counter()
    for key, trace in sorted(traces.items()):
        payload_key = (
            trace.get("request_envelope_sha256"),
            trace.get("payload_sha256"),
            trace.get("prompt_sha256"),
        )
        payload = payloads.get(payload_key) or {}
        raw = payload.get("sanitized_user_input")
        outcome = (by_trace.get(key, {}).get("horizon_metrics") or {}).get("10m") or {}
        path = outcome.get("entry_quality_path") or {}
        row_identity = {
            "source_date": day,
            "evaluation_attempt_id": trace.get("evaluation_attempt_id"),
            "scanner_promotion_id": trace.get("scanner_promotion_id"),
            "stock_code": trace.get("stock_code"),
            "effective_venue": trace.get("effective_venue"),
            "session_bucket": trace.get("session_bucket"),
        }
        owner_replay = owner_rows.get(trace.get("evaluation_attempt_id")) or {}
        owner_valid = owner_replay_valid(owner_replay, row_identity)
        label_identity_reasons = [r for r in by_trace.get(key,{}).get("primary_cohort_exclusion_reasons") or []
            if r in {"payload_trace_venue_mismatch","payload_trace_session_mismatch","canonical_context_venue_session_mismatch"}]
        reason = None
        if key in conflicts or payload_key in payload_conflicts:
            reason = "conflicting_exact_input"
        elif (
            trace.get("model") != "gpt-5.4-nano"
            or trace.get("provider_actual") != "openai"
            or trace.get("semantic_validation_status") != "pass"
            or trace.get("decision_quality_contract_status") != "pass"
        ):
            reason = "natural_contract_invalid"
        elif (
            payload.get("redacted") is not False
            or payload.get("replay_exact") is not True
            or not isinstance(raw, dict)
            or hashlib.sha256(_json_bytes(raw)).hexdigest()
            != payload.get("sanitized_user_input_sha256")
            or payload.get("payload_sha256") != trace.get("payload_sha256")
            or payload.get("request_envelope_sha256")
            != trace.get("request_envelope_sha256")
            or payload.get("prompt_sha256") != trace.get("prompt_sha256")
        ):
            reason = "frozen_payload_missing_or_invalid"
        elif label_identity_reasons:
            reason = "source_label_identity_contract_invalid:" + label_identity_reasons[0]
        elif not owner_valid and path.get("status") != "evaluable":
            reason = path.get("label_reason") or "terminal_path_not_evaluable"
        elif not owner_valid and (
            path.get("first_hit") not in {"net_target_first", "exact_stop_first"}
            or not finite(path.get("conservative_execution_cost_pct"))
        ):
            reason = "full_cost_or_terminal_missing"
        verdict = str(trace.get("entry_ai_risk_verdict") or "")
        if not reason and verdict not in {"PASS", "VETO", "CAUTION"}:
            reason = "routing_semantics_missing"
        if reason:
            exclusions[reason] += 1
        rows.append(
            {
                **row_identity,
                "evaluation_key": key,
                "decision_ts": trace.get("decision_ts"),
                "effective_venue": trace.get("effective_venue"),
                "session_bucket": trace.get("session_bucket"),
                "broker_route": trace.get("broker_route"),
                "machine_bundle_sha256": trace.get("machine_bundle_sha256"),
                "incumbent_prompt_version": trace.get("prompt_version"),
                "issued_prompt_sha256": trace.get("prompt_sha256"),
                "payload_sha256": trace.get("payload_sha256"),
                "incumbent_verdict": verdict,
                # Preserve frozen source for a later owner-path evaluation;
                # exclusion, not deletion of the payload, controls execution.
                "input": raw if isinstance(raw, dict) and payload.get("replay_exact") is True
                    and payload.get("redacted") is False else None,
                "owner_replay": owner_replay if owner_valid else None,
                "entry_quality_path": path,
                "source_label_identity_reasons": label_identity_reasons,
                "exclusion_reason": reason,
                "natural_contract_evidence": {k: trace.get(k) for k in
                    ("result_source", "model", "provider_actual", "semantic_validation_status",
                     "decision_quality_contract_status", "decision_quality_contract_errors")},
            }
        )
    return sealed(
        {
            "schema": "compact_auxiliary_frozen_projection_v1",
            "source_projection_contract": SOURCE_PROJECTION_CONTRACT,
            "target_date": day,
            "source_manifest_sha256": manifest.get("source_manifest_sha256"),
            "source_tuning_allowed": receipt.get("tuning_input_allowed") is True
            and isinstance(manifest.get("source_manifest_sha256"), str)
            and len(manifest["source_manifest_sha256"]) == 64,
            "source_label_report_sha256": digest(labels),
            "owner_execution_model_validation": split.get("execution_model_validation") or {},
            "screened_total": len(rows),
            "exclusion_counts": dict(exclusions),
            "rows": rows,
            **AUTHORITY,
        }
    )


def input_identity(row):
    return digest(
        {
            k: row.get(k)
            for k in (
                "evaluation_key",
                "source_date",
                "payload_sha256",
                "issued_prompt_sha256",
                "machine_bundle_sha256",
                "input",
                "incumbent_prompt_version",
            )
        }
    )


def evaluate(rows, results):
    """Cost/stop path CF is a percentage diagnostic, not portfolio realized PnL."""
    pairs, exclusions, transitions = [], Counter(), Counter()
    scope_exclusions = defaultdict(Counter)
    def exclude(row, reason):
        exclusions[reason] += 1
        scope_exclusions["|".join((row["effective_venue"], row["session_bucket"]))][reason] += 1
    for row in rows:
        key = row["evaluation_key"]
        reason = row.get("exclusion_reason")
        result = results.get(key) or {}
        response = result.get("candidate_response") or {}
        if not reason and (
            not valid(result)
            or result.get("input_sha256") != input_identity(row)
            or result.get("validation_errors")
            or not response
        ):
            reason = "candidate_response_missing_or_invalid"
        path = row.get("entry_quality_path") or {}
        owner_replay = row.get("owner_replay") or {}
        arm = owner_operating_arm(owner_replay, row)
        owner_valid = bool(arm)
        terminal = (
            path.get("gross_net_target_pct")
            if path.get("first_hit") == "net_target_first"
            else path.get("exact_stop_distance_pct")
        )
        cost = path.get("conservative_execution_cost_pct")
        if (
            not reason
            and not owner_valid
            and (not finite(terminal) or not finite(cost) or cost < 0)
        ):
            reason = "terminal_net_missing"
        if reason:
            exclude(row, reason)
            continue
        candidate = response.get("risk_verdict")
        incumbent = row.get("incumbent_verdict")
        if candidate not in {"PASS", "VETO", "CAUTION"}:
            exclude(row, "routing_semantics_missing")
            continue
        if "CAUTION" in (incumbent, candidate):
            exclude(row, "caution_followup_terminal_missing")
            continue
        net = arm.get("net_return_pct") if owner_valid else terminal - cost
        stress_net = arm.get("stress_net_return_pct") if owner_valid else net - cost
        if not finite(net) or not finite(stress_net):
            exclude(row, "terminal_net_missing")
            continue
        old, new = (
            (net if incumbent == "PASS" else 0.0),
            (net if candidate == "PASS" else 0.0),
        )
        transitions[f"{incumbent}->{candidate}"] += 1
        pairs.append(
            {
                k: row.get(k)
                for k in (
                    "evaluation_key",
                    "source_date",
                    "effective_venue",
                    "session_bucket",
                    "broker_route",
                    "incumbent_prompt_version",
                    "evaluation_attempt_id",
                    "scanner_promotion_id",
                    "stock_code",
                )
            }
            | {
                "incumbent_net_pct": old,
                "candidate_net_pct": new,
                "delta_net_pct": new - old,
                "stress_delta_net_pct": stress_net
                * (int(candidate == "PASS") - int(incumbent == "PASS")),
                "same_verdict": incumbent == candidate,
                "candidate_response_sha256": result.get("artifact_content_sha256"),
                "incumbent_verdict": incumbent,
                "candidate_verdict": candidate,
                "runtime_inference_cost_delta_krw": result.get(
                    "runtime_inference_cost_delta_krw"
                ),
                "owner_replay": owner_replay if owner_valid else None,
            }
        )
    n = len(pairs)
    source_excluded = sum(bool(r.get("exclusion_reason")) for r in rows)
    eligible = len(rows) - source_excluded
    portfolio = portfolio_metrics(pairs)
    scope_coverage = {}
    paired_groups = _scope_groups(pairs)
    for scope, population in _scope_groups(rows).items():
        comparable = len(paired_groups.get(scope, []))
        source_count = sum(bool(r.get("exclusion_reason")) for r in population)
        eligible_count = len(population) - source_count
        scope_coverage[scope] = dict(screened_total=len(population), paired_comparable_count=comparable,
            source_excluded_count=source_count, economic_eligible_count=eligible_count,
            response_coverage=comparable / eligible_count if eligible_count else None,
            denominator_preserved=comparable + sum(scope_exclusions[scope].values()) == len(population),
            exclusion_counts=dict(scope_exclusions[scope]))
    return {
        "screened_total": len(rows),
        "paired_comparable_count": n,
        "denominator_preserved": n + sum(exclusions.values()) == len(rows),
        "source_excluded_count": source_excluded,
        "economic_eligible_count": eligible,
        "response_coverage": n / eligible if eligible else None,
        "exclusion_counts": dict(exclusions),
        "verdict_transitions": dict(transitions),
        "incumbent_net_ev_pct": sum(p["incumbent_net_pct"] for p in pairs) / n
        if n
        else None,
        "candidate_net_ev_pct": sum(p["candidate_net_pct"] for p in pairs) / n
        if n
        else None,
        "delta_net_ev_pct": sum(p["delta_net_pct"] for p in pairs) / n if n else None,
        **portfolio,
        "counterfactual_not_realized_pnl": True,
        "metric_role": "sim_probe_ev",
        "decision_authority": "offline_cf_diagnostic_no_order_authority",
        "window_policy": "same_frozen_input_completed_bar_cost_stop_path",
        "sample_floor": CONTRACT,
        "primary_decision_metric": "equal_weight_avg_profit_pct",
        "source_quality_gate": "exact_natural_compact_input_full_cost_terminal",
        "scope_coverage": scope_coverage,
        "forbidden_uses": [
            "actual_pnl",
            "standalone_prompt_promotion",
            "broker_authority",
        ],
        "pairs": pairs,
    }


def _scope_groups(rows):
    groups = defaultdict(list)
    for row in rows:
        groups["|".join((str(row.get("effective_venue")), str(row.get("session_bucket"))))].append(row)
    return groups


def scope_candidate_validation(pairs, rows, metrics, plan, *, candidate, now):
    """Freeze each policy scope only after every observed route can learn.

    Earlier scopes never move their cutoff. A later scope may collect its own
    learning population, but may not use that population as its holdout.
    """
    from src.engine.scalping.strategy_owner_replay import entry_operating_route_supported
    previous = plan.get("scope_candidates") or {}
    frozen = dict(previous)
    validations = {}
    for scope, population in _scope_groups(rows).items():
        versions = {r.get("incumbent_prompt_version") for r in population}
        incumbent = next(iter(versions)) if len(versions) == 1 else None
        exact = [p for p in _scope_groups(pairs).get(scope, [])
                 if p.get("incumbent_prompt_version") == incumbent]
        state = frozen.get(scope) or {}
        if state and state.get("incumbent_prompt_version") != incumbent:
            # A changed incumbent is a new comparison; old evidence cannot
            # silently authorize it or reset already claimed holdout keys.
            exact = []
        routes = defaultdict(set)
        for pair in exact:
            if entry_operating_route_supported(pair["effective_venue"], pair["session_bucket"], pair["broker_route"]):
                routes[pair["broker_route"]].add((pair["source_date"], pair["scanner_promotion_id"]))
        if not state and incumbent and incumbent != candidate and routes and all(
                len(keys) >= CONTRACT["learning_episode_floor"] for keys in routes.values()):
            state = {"candidate_frozen_at": now.isoformat(), "incumbent_prompt_version": incumbent,
                     "learning_manifest_sha256": digest(exact)}
            frozen[scope] = state
        cutoff = state.get("candidate_frozen_at")
        cutoff_day = cutoff[:10] if cutoff else now.date().isoformat()
        validations[scope] = {
            "incumbent_prompt_version": incumbent,
            "candidate_frozen_at": cutoff,
            "coverage": metrics.get("scope_coverage", {}).get(scope, {}),
            "chronological_validation": {"candidate_frozen_at": cutoff,
                "learning_pairs": [p for p in exact if p["source_date"] <= cutoff_day],
                "holdout_pairs": [p for p in exact if p["source_date"] > cutoff_day] if cutoff else [],
                "holdout_consumed": False},
        }
    return validations, frozen


def _comparison_signatures(parent, day, candidate):
    paths = [parent / f"compact_candidate_plan_{candidate}.json"]
    for path in parent.glob("compact_auxiliary_paired_economic_*.json"):
        source_day = path.stem.removeprefix("compact_auxiliary_paired_economic_")
        if len(source_day) == 10 and "2026-06-05" <= source_day < day:
            paths.append(path)
    return {str(path): [path.stat().st_size, path.stat().st_mtime_ns] if path.exists() else None
            for path in sorted(paths)}


def portfolio_metrics(pairs):
    """Reuse the owner's one-position reservation, independently for both arms."""
    empty = {
        "portfolio_daily_net_delta_krw": None,
        "net_profit_status": "not_available_without_owner_plan_and_portfolio_replay",
    }
    if not pairs:
        return empty
    days = defaultdict(lambda: [0.0, 0.0])
    reservations = {}
    for pair in sorted(
        pairs,
        key=lambda r: ((r.get("owner_replay") or {}).get("seed") or {}).get(
            "observed_at", ""
        ),
    ):
        replay = pair.get("owner_replay") or {}
        seed = replay.get("seed") or {}
        arm = owner_operating_arm(replay, pair)
        if not seed or not finite(arm.get("net_pnl_krw")):
            return empty
        start, end = seed.get("observed_at"), arm.get("modeled_exit_at")
        if not start or not end or end <= start:
            return empty
        for i, verdict in enumerate(
            (pair["incumbent_verdict"], pair["candidate_verdict"])
        ):
            if verdict != "PASS":
                continue
            if reservations.get(i, "") > start:
                # Requires standalone owner replay for a genuine allocation
                # conflict, rather than adding independent episode profits.
                return empty
            reservations[i] = end
            days[pair["source_date"]][i] += arm["net_pnl_krw"]
        if finite(pair.get("runtime_inference_cost_delta_krw")):
            days[pair["source_date"]][1] -= pair["runtime_inference_cost_delta_krw"]
        days[pair["source_date"]]
    return {
        "portfolio_daily_net_delta_krw": {
            d: v[1] - v[0] for d, v in sorted(days.items())
        },
        "net_profit_status": "owner_one_position_nonoverlapping_cf",
        "portfolio_allocation_contract": "existing_owner_one_concurrent_position",
        "counterfactual_not_realized_pnl": True,
    }


def promotion_valid(report, *, incumbent, selected, source_manifest_sha256, effective_date=None, scope=("KRX", "KRX_REGULAR")):
    """A percentage path alone cannot prove executable daily net-profit uplift."""
    scoped = (report.get("scope_validation") or {}).get("|".join(scope))
    if (
        not valid(report)
        or report.get("schema") != SCHEMA
        or report.get("candidate_prompt_version") != selected
        or (scoped or report).get("incumbent_prompt_version") != incumbent
        or selected == incumbent
        or report.get("source_manifest_sha256") != source_manifest_sha256
        or report.get("promotion_contract_sha256") != digest(CONTRACT)
        or any(report.get(k) is not v for k, v in AUTHORITY.items())
    ):
        return False
    inference_receipt = report.get("runtime_inference_cost_receipt") or {}
    try:
        pricing_root = Path(inference_receipt["pricing_path"]).parents[2]
        if (inference_receipt.get("status") != "reviewed_operator_zero_cost"
            or inference_receipt != runtime_inference_cost_receipt(pricing_root, report["target_date"])):
            return False
        day = effective_date or report["target_date"]
        if not inference_receipt["effective_from"] <= day <= inference_receipt["effective_to"]:
            return False
    except (KeyError, IndexError, TypeError):
        return False
    from src.engine.scalping.entry_split_order_plan import EXECUTION_MODEL_CONTRACT
    model = report.get("owner_execution_model_validation") or {}
    if (model.get("contract_version") != EXECUTION_MODEL_CONTRACT
            or model.get("source_date") != report.get("target_date")
            or model.get("status") != "validated_scope"
            or model.get("allowed_runtime_apply") is not True):
        return False
    proof = (scoped or report).get("chronological_validation") or {}
    if proof.get("candidate_frozen_at") != (scoped or report).get("candidate_frozen_at"):
        return False
    learning, holdout = (
        proof.get("learning_pairs") or [],
        proof.get("holdout_pairs") or [],
    )
    try:
        frozen_day = (
            datetime.fromisoformat((scoped or report)["candidate_frozen_at"])
            .astimezone(KST)
            .date()
            .isoformat()
        )
    except (ValueError, KeyError, TypeError):
        return False
    if any(
        p.get("source_date", "") < "2026-06-05"
        or p.get("source_date", "") > report.get("target_date", "")
        for p in learning + holdout
    ):
        return False
    if any(p.get("source_date", "") > frozen_day for p in learning) or any(
        p.get("source_date", "") <= frozen_day for p in holdout
    ):
        return False
    keys = [p.get("evaluation_key") for p in learning + holdout]
    if not all(keys) or len(set(keys)) != len(keys):
        return False
    cohorts = defaultdict(lambda: [[], []])
    for i, rows in enumerate((learning, holdout)):
        for p in rows:
            if (p.get("effective_venue"), p.get("session_bucket")) != tuple(scope):
                continue
            if p.get("incumbent_prompt_version") != incumbent or not owner_replay_valid(
                p.get("owner_replay") or {}, p
            ):
                return False
            arm = owner_operating_arm(p["owner_replay"], p)
            if not arm or not owner_model_scope_valid(model, p):
                return False
            old, new = p.get("incumbent_verdict"), p.get("candidate_verdict")
            if not finite(p.get("runtime_inference_cost_delta_krw")):
                return False
            if old not in {"PASS", "VETO"} or new not in {"PASS", "VETO"}:
                return False
            net, stress = arm.get("net_return_pct"), arm.get("stress_net_return_pct")
            if not finite(net) or not finite(stress):
                return False
            expected = {
                "incumbent_net_pct": net * int(old == "PASS"),
                "candidate_net_pct": net * int(new == "PASS"),
                "delta_net_pct": net * (int(new == "PASS") - int(old == "PASS")),
                "stress_delta_net_pct": stress
                * (int(new == "PASS") - int(old == "PASS")),
            }
            if any(
                not finite(p.get(k)) or not math.isclose(p[k], value, abs_tol=1e-12)
                for k, value in expected.items()
            ):
                return False
            cohort = (
                p.get("effective_venue"),
                p.get("session_bucket"),
                p.get("broker_route"),
            )
            cohorts[cohort][i].append(p)
    coverage = scoped.get("coverage", {}) if scoped is not None else report.get("metrics", {})
    if (not cohorts or coverage.get("response_coverage") != CONTRACT["minimum_response_coverage"]
        or (scoped is not None and (coverage.get("denominator_preserved") is not True
            or coverage.get("paired_comparable_count") != len(learning) + len(holdout)
            or coverage.get("economic_eligible_count") != len(learning) + len(holdout)))):
        return False
    from src.engine.scalping.entry_setup_evidence import mechanistic_scope_supported
    from src.engine.scalping.strategy_owner_replay import entry_operating_route_supported
    if not mechanistic_scope_supported(*scope):
        return False
    exact = [halves for cohort, halves in cohorts.items() if cohort[:2] == tuple(scope)
             and entry_operating_route_supported(*cohort)]
    if not exact:
        return False
    for train, test in exact:
        if (
            len({(p["source_date"], p["scanner_promotion_id"]) for p in train})
            < CONTRACT["learning_episode_floor"]
            or len({(p["source_date"], p["scanner_promotion_id"]) for p in test})
            < CONTRACT["holdout_episode_floor"]
            or len({p["source_date"] for p in test})
            < CONTRACT["holdout_source_day_floor"]
        ):
            return False
        for field in ("delta_net_pct", "stress_delta_net_pct"):
            if (
                any(not finite(p.get(field)) for p in test)
                or sum(p[field] for p in test) <= 0
            ):
                return False
        if min(p["candidate_net_pct"] for p in test) < min(
            p["incumbent_net_pct"] for p in test
        ):
            return False
        portfolio = portfolio_metrics(test)
        daily = portfolio["portfolio_daily_net_delta_krw"]
        if not daily or sum(daily.values()) <= 0:
            return False
        for half in (train, test):
            economics = operating_comparison_metrics(half, model)
            if (economics["status"] != "supported_operating_comparison"
                or economics["robust_paired_delta_ev_lower_bound_pct"] <= 0
                or economics["candidate"]["net_pnl_krw"] <= economics["incumbent"]["net_pnl_krw"]
                or economics["candidate"]["worst"] < economics["incumbent"]["worst"]
                or economics["candidate"]["es10"] < economics["incumbent"]["es10"]):
                return False
    return proof.get("holdout_consumed") is False


def consume_holdout(proof, data_root, *, scopes=None):
    """Called under the existing publisher lock; retries of one proof are safe."""
    path = (
        report_path(data_root, proof["target_date"]).parent
        / "compact_holdout_consumption.json"
    )
    previous = read(path)
    if previous and not valid(previous):
        raise ValueError("compact_holdout_consumption_hash_invalid")
    claims = previous.get("claims", {})
    identity = proof["artifact_content_sha256"]
    scoped = proof.get("scope_validation")
    held = ([p for key, value in scoped.items() if scopes is None or key in scopes
             for p in value["chronological_validation"]["holdout_pairs"]]
            if scoped is not None else proof["chronological_validation"]["holdout_pairs"])
    for pair in held:
        if scopes is not None and "|".join((pair["effective_venue"], pair["session_bucket"])) not in scopes:
            continue
        key = pair["evaluation_key"]
        if key in claims and claims[key] != identity:
            raise ValueError("compact_holdout_already_consumed")
        claims[key] = identity
    write(path, sealed({"claims": claims, **AUTHORITY}))


def applied_decision_version_performance(split_report, *, day):
    """Reuse the existing custody/capital and completed-cost performance owner.

    A real initial-entry submit receipt proves this combined machine/compact
    consumption. Split-policy application alone is not that witness. This
    descriptive realized performance does not estimate causal improvement.
    """
    from src.engine.scalping import entry_split_order_plan as split
    rows=[]; excluded=Counter()
    for row in (split_report.get("operating_economic_state") or {}).get("model_rows") or []:
        receipt=row.get("entry_decision_version_receipt") or {}
        if (row.get("entry_decision_pid_consumed") is not True
            or receipt.get("sha256") != split._canonical_sha256({k:v for k,v in receipt.items() if k != "sha256"})
            or not all(receipt.get(k) for k in ("machine_policy_version","compact_prompt_version","decision_trace_id","runtime_pid"))):
            excluded["exact_submit_decision_version_receipt_missing_or_invalid"]+=1
            continue
        rows.append({**row,"policy_version":receipt["machine_policy_version"]+"|"+receipt["compact_prompt_version"],
            "policy_sha256":receipt.get("machine_bundle_sha256"),"policy_applied":True,
            "pid_consumed":True,"runtime_pid":receipt["runtime_pid"]})
    value=split.build_entry_split_post_apply_performance(rows,target_date=day)
    return {**value,"axis":"joint_applied_machine_and_compact_version",
        "source_owner":"entry_split_exact_initial_owner_custody_completed_cost_capital_join",
        "excluded_counts":dict(excluded),"causal_profit_improvement":None}


def primary_input_blocker(row, model):
    """Keep research proxy diagnostics outside provider-funded primary search."""
    reason = row.get("exclusion_reason")
    if reason:
        return ("unsupported_scope" if reason == "natural_contract_invalid" else "source_gap", reason)
    if row.get("source_label_identity_reasons"):
        return "source_gap", "source_label_identity_contract_invalid:"+row["source_label_identity_reasons"][0]
    from src.engine.scalping.strategy_owner_replay import entry_operating_route_supported
    if not entry_operating_route_supported(row.get("effective_venue"), row.get("session_bucket"), row.get("broker_route")):
        return "unsupported_scope", "session_market_route_contract_invalid"
    replay = row.get("owner_replay") or {}
    arm = owner_operating_arm(replay, row)
    if not arm:
        raw = next(iter((replay.get("operating_arms") or {}).values()), {})
        disposition = {"unsupported_scope":"unsupported_scope", "terminal_pending":"pending"}.get(raw.get("status"), "source_gap")
        return disposition, raw.get("blocker") or "independent_operating_arm_missing_or_invalid"
    if not owner_model_scope_valid(model, row):
        return "insufficient_sample" if model.get("status") == "insufficient_mature_sample" else "source_gap", "independent_prior_operating_model_scope_not_validated"
    return None


def candidate_zero_disposition(rows, blockers, report):
    counts = dict(Counter(value[0] for value in blockers.values()))
    scope_dispositions = {}
    for scope, proof in (report.get("scope_validation") or {}).items():
        chronology = proof["chronological_validation"]
        local_counts = Counter(blockers[r["evaluation_key"]][0] for r in _scope_groups(rows).get(scope, [])
                               if r["evaluation_key"] in blockers)
        train, held = chronology["learning_pairs"], chronology["holdout_pairs"]
        by_route = defaultdict(lambda: [[], []])
        for i, half in enumerate((train, held)):
            for pair in half:
                by_route[pair["broker_route"]][i].append(pair)
        coverage = proof["coverage"]
        complete = bool(by_route) and all(
            len({(p["source_date"], p["scanner_promotion_id"]) for p in learn}) >= CONTRACT["learning_episode_floor"]
            and len({(p["source_date"], p["scanner_promotion_id"]) for p in test}) >= CONTRACT["holdout_episode_floor"]
            and len({p["source_date"] for p in test}) >= CONTRACT["holdout_source_day_floor"]
            for learn, test in by_route.values())
        if scope in report.get("promotion_scopes", []):
            disposition = "candidate_selected"
        elif local_counts:
            disposition = next(k for k in ("source_gap", "unsupported_scope", "pending", "insufficient_sample") if local_counts.get(k))
        elif coverage.get("economic_eligible_count", 0) > coverage.get("paired_comparable_count", 0):
            disposition = "pending"
        elif not complete or not proof.get("candidate_frozen_at"):
            disposition = "insufficient_sample"
        elif (coverage.get("denominator_preserved") is not True
              or len({p["evaluation_key"] for p in train + held}) != len(train) + len(held)
              or any(p["source_date"] > proof["candidate_frozen_at"][:10] for p in train)
              or any(p["source_date"] <= proof["candidate_frozen_at"][:10] for p in held)
              or chronology.get("holdout_consumed") is not False):
            disposition = "source_gap"
        else:
            economics = [operating_comparison_metrics(half, report["owner_execution_model_validation"])
                         for halves in by_route.values() for half in halves]
            disposition = ("valid_no_edge" if all(e.get("status") == "supported_operating_comparison" for e in economics)
                           and any(e["robust_paired_delta_ev_lower_bound_pct"] <= 0
                                   or e["candidate"]["worst"] < e["incumbent"]["worst"]
                                   or e["candidate"]["es10"] < e["incumbent"]["es10"] for e in economics)
                           else "source_gap")
        scope_dispositions[scope] = {"status": disposition, "primary_input_disposition_counts": dict(local_counts),
            "coverage": coverage, "valid_no_edge": disposition == "valid_no_edge",
            "owner": "existing_main_execution_and_empirical_model_owners",
            "closure_test": "exact_scope_complete_population_prior_validated_model_and_independent_candidate_holdout"}
    if report.get("promotion_pass"):
        status = "candidate_selected"
    elif counts:
        status = next(k for k in ("source_gap","unsupported_scope","pending","insufficient_sample") if counts.get(k))
    elif report["metrics"]["paired_comparable_count"] < len(rows):
        status = "pending"
    elif scope_dispositions:
        states = {s["status"] for s in scope_dispositions.values()}
        status = next(k for k in ("source_gap", "unsupported_scope", "pending", "insufficient_sample", "valid_no_edge") if k in states)
    else:
        proof = report.get("chronological_validation") or {}
        learning, held = proof.get("learning_pairs") or [], proof.get("holdout_pairs") or []
        complete = (len({(p["source_date"],p["scanner_promotion_id"]) for p in learning}) >= CONTRACT["learning_episode_floor"]
            and len({(p["source_date"],p["scanner_promotion_id"]) for p in held}) >= CONTRACT["holdout_episode_floor"]
            and len({p["source_date"] for p in held}) >= CONTRACT["holdout_source_day_floor"])
        keys=[p["evaluation_key"] for p in learning+held]
        frozen=report.get("candidate_frozen_at") or ""
        chronology=(len(keys)==len(set(keys)) and bool(frozen)
            and all(p["source_date"]<=frozen[:10] for p in learning)
            and all(p["source_date"]>frozen[:10] for p in held)
            and proof.get("holdout_consumed") is False
            and report["metrics"].get("response_coverage")==1.)
        comparison = report["metrics"].get("operating_economic_comparison") or {}
        status = ("valid_no_edge" if complete and chronology and comparison.get("status") == "supported_operating_comparison"
            and comparison.get("robust_paired_delta_ev_lower_bound_pct") is not None
            and comparison["robust_paired_delta_ev_lower_bound_pct"] <= 0 else "source_gap" if complete and not chronology else "insufficient_sample")
    return dict(status=status, primary_input_disposition_counts=counts, scope_dispositions=scope_dispositions,
        blockers=[dict(evaluation_key=key,disposition=value[0],blocker=value[1],
                       owner="existing_main_execution_and_empirical_model_owners",
                       closure_test="lossless_pre_ai_producer_full_operating_arm_prior_model_holdout_and_independent_candidate_holdout")
                  for key,value in blockers.items()],
        valid_no_edge=status == "valid_no_edge", model_delta_ev_is_actual_profit=False)



def source_dependency_signatures(data_root, day):
    root = Path(data_root).resolve()
    paths = [root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl",
             root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl",
             root / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{day}.json",
             root / "report/observation_source_quality_audit" / f"observation_source_quality_audit_{day}.json",
             root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json"]
    signatures = {}
    for dependency in paths:
        actual = dependency if dependency.exists() else Path(str(dependency) + ".gz")
        signatures[str(dependency)] = [actual.stat().st_size, actual.stat().st_mtime_ns] if actual.exists() else None
    return signatures


def run(
    *,
    data_root,
    day,
    candidate_version=None,
    execute=False,
    max_new=30,
    timeout_sec=45.0,
    runner=None,
    allow_source_rebuild=True,
):
    """Bounded, resumable offline batch; all mutation occurs under a day lock."""
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.entry_setup_evidence import (
        entry_risk_adjudication_openai_schema,
        validate_entry_risk_adjudication,
    )
    from src.engine.scalping.mechanistic_entry_runtime_policy import (
        COMPACT_AI_VARIANTS,
        compact_auxiliary_prompt,
    )
    from src.engine.ai_prompt_contracts import (
        ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
    )

    if (
        date.fromisoformat(day).isoformat() < "2026-06-05"
        or max_new <= 0
        or timeout_sec <= 0
    ):
        raise ValueError("compact_batch_bounds_invalid")
    root = Path(data_root).resolve()
    path = report_path(root, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        projection_path = path.with_suffix(".source.json")
        projection = read(projection_path)
        signatures = source_dependency_signatures(root, day)
        dependency_paths = [Path(p) for p in signatures]
        label_dependency = str(root / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{day}.json")
        split_dependency = str(root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json")
        # An additive label contract revision does not require rereading large
        # frozen raw inputs. Changed diagnostic/economic paths still rebuild.
        if valid(projection):
            prior = projection.get("dependency_signatures") or {}
            if prior.get(label_dependency) != signatures.get(label_dependency) and all(
                    prior.get(k) == v for k, v in signatures.items() if k not in (label_dependency,split_dependency)):
                label_report = read(Path(label_dependency))
                label_index = {x.get("decision_trace_id"): x for x in label_report.get("labels") or [] if isinstance(x, dict)}
                if label_report.get("target_date") == day and all(
                        row.get("entry_quality_path") == (((label_index.get(row.get("evaluation_key")) or {}).get("horizon_metrics") or {}).get("10m") or {}).get("entry_quality_path", {})
                        for row in projection.get("rows") or []):
                    write(path.parent / "compact_source_generations" / (projection["artifact_content_sha256"] + ".json"), projection)
                    projection = sealed({**projection, "dependency_signatures": {**prior,label_dependency:signatures[label_dependency]},
                                         "source_label_report_sha256": digest(label_report)})
                    write(projection_path, projection)
        # Code-only source contract upgrades and bounded owner/model refreshes
        # must not rescan sealed raw trace/payload generations. An exclusion
        # with no original frozen input stays excluded, even if an owner exists.
        prior = projection.get("dependency_signatures") or {}
        split_dependency = str(root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json")
        unchanged_raw = (valid(projection) and prior.get(label_dependency) == signatures.get(label_dependency)
            and all(prior.get(k) == v for k, v in signatures.items() if k not in (split_dependency, label_dependency)))
        if unchanged_raw and (projection.get("source_projection_contract") != SOURCE_PROJECTION_CONTRACT
            or projection.get("projection_contract_sha256") != digest(CONTRACT)
            or prior.get(split_dependency) != signatures.get(split_dependency)):
            labels = read(Path(label_dependency))
            by_trace = {r.get("decision_trace_id"): r for r in labels.get("labels") or []}
            split_report = read(Path(split_dependency))
            summary = split_report.get("input_summary") or {}
            owner_source = (summary.get("compact_pre_ai_execution_replay")
                or summary.get("entry_opportunity_executable_replay_refresh")
                or (summary.get("daily_diagnostic") or {}).get("entry_opportunity_executable_replay") or {})
            owners = {r.get("seed", {}).get("evaluation_attempt_id"): r for r in owner_source.get("rows") or []}
            rebound = []
            for original in projection.get("rows") or []:
                row = dict(original)
                owner = owners.get(row.get("evaluation_attempt_id")) or {}
                row["owner_replay"] = owner if owner_replay_valid(owner, row) else None
                label = by_trace.get(row.get("evaluation_key")) or {}
                row["source_label_identity_reasons"]=[r for r in label.get("primary_cohort_exclusion_reasons") or []
                    if r in {"payload_trace_venue_mismatch","payload_trace_session_mismatch","canonical_context_venue_session_mismatch"}]
                row.setdefault("natural_contract_evidence", {k: label.get(k) for k in
                    ("result_source", "model", "provider_actual", "semantic_validation_status",
                     "decision_quality_contract_status", "decision_quality_contract_errors")})
                if (row["owner_replay"] and isinstance(row.get("input"), dict)
                    and row.get("exclusion_reason") in {"exact_stop_distance_missing", "exact_stop_distance_missing_or_invalid", "terminal_path_not_evaluable", "full_cost_or_terminal_missing"}):
                    row["exclusion_reason"] = None
                rebound.append(row)
            write(path.parent / "compact_source_generations" / (projection["artifact_content_sha256"] + ".json"), projection)
            projection = sealed({**projection, "rows": rebound,
                "exclusion_counts": dict(Counter(r["exclusion_reason"] for r in rebound if r.get("exclusion_reason"))),
                "owner_execution_model_validation": split_report.get("execution_model_validation") or {},
                "dependency_signatures": signatures, "projection_contract_sha256": digest(CONTRACT),
                "source_projection_contract": SOURCE_PROJECTION_CONTRACT,
                "source_upgrade": {"original_projection_sha256": projection["artifact_content_sha256"],
                    "raw_not_read": True, "original_missing_input_not_reconstructed": True}})
            write(projection_path, projection)
        if (
            not valid(projection)
            or projection.get("dependency_signatures") != signatures
            or projection.get("projection_contract_sha256") != digest(CONTRACT)
        ):
            if valid(projection):
                write(
                    path.parent
                    / "compact_source_generations"
                    / (projection["artifact_content_sha256"] + ".json"),
                    projection,
                )
            if not allow_source_rebuild:
                raise ValueError("compact_finalize_requires_evaluation_of_changed_source")
            projection = sealed(
                {**prepare(root, day), "dependency_signatures": signatures,
                 "projection_contract_sha256": digest(CONTRACT), "source_projection_contract": SOURCE_PROJECTION_CONTRACT}
            )
            for dependency in dependency_paths:
                actual = dependency if dependency.exists() else Path(str(dependency) + ".gz")
                after = [actual.stat().st_size, actual.stat().st_mtime_ns] if actual.exists() else None
                if after != signatures[str(dependency)]:
                    raise ValueError("compact_source_generation_changed_during_freeze")
            write(projection_path, projection)
        candidate = (
            candidate_version
            or ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION
        )
        if candidate not in COMPACT_AI_VARIANTS:
            raise ValueError("unregistered_compact_candidate")
        candidate_prompt = compact_auxiliary_prompt(prompt_version=candidate)
        candidate_contract = digest([candidate_prompt, {
            r["evaluation_key"]: digest(entry_risk_adjudication_openai_schema(r["input"]["entry_setup_evidence_v1"]))
            for r in projection["rows"] if not r.get("exclusion_reason") and isinstance(r.get("input"), dict)
        }])
        frozen_plan = read(path.parent / f"compact_candidate_plan_{candidate}.json")
        if (frozen_plan.get("scope_candidates") and frozen_plan.get("candidate_prompt_sha256")
                and frozen_plan["candidate_prompt_sha256"] != digest(candidate_prompt)):
            raise ValueError("frozen_candidate_prompt_or_schema_changed")
        cost_receipt = runtime_inference_cost_receipt(root, day)
        previous = read(path)
        if valid(previous) and previous.get("candidate_prompt_version") != candidate:
            raise ValueError("frozen_candidate_selection_mismatch")
        if (valid(previous)
                and previous.get("candidate_contract_sha256") == candidate_contract
                and previous.get("runtime_inference_cost_receipt") == cost_receipt
                and previous.get("promotion_contract_sha256") == digest(CONTRACT)
                and previous.get("source_projection_sha256") == projection["artifact_content_sha256"]
                and previous.get("comparison_dependency_signatures") == _comparison_signatures(path.parent, day, candidate)
                and (previous.get("status") in {"valid_empty", "comparison_complete", "incumbent_preserved"}
                     or previous.get("metrics", {}).get("economic_eligible_count") == 0)):
            return previous
        checkpoint = read(path.with_suffix(".checkpoint.json"))
        if (
            valid(checkpoint)
            and checkpoint.get("candidate_prompt_version") != candidate
        ):
            raise ValueError("frozen_checkpoint_candidate_mismatch")
        results = (
            checkpoint.get("results", {})
            if valid(checkpoint)
            else previous.get("results", {})
            if valid(previous)
            else {}
        )
        ledger, calls = None, 0
        execution_errors = []
        cost_receipt = runtime_inference_cost_receipt(root, day)
        primary_blockers = {}
        for row in projection["rows"]:
            value = primary_input_blocker(row, projection.get("owner_execution_model_validation") or {})
            if value is None and cost_receipt["delta_krw"] is None:
                value = ("source_gap", cost_receipt["blocker"])
            if value is not None:
                primary_blockers[row["evaluation_key"]] = value
        for row in projection["rows"]:
            key = row["evaluation_key"]
            if row["evaluation_key"] in primary_blockers or not projection["source_tuning_allowed"]:
                continue
            if row["incumbent_prompt_version"] == candidate:
                results[key] = sealed(
                    {
                        "candidate_response": {
                            "risk_verdict": row["incumbent_verdict"]
                        },
                        "input_sha256": input_identity(row),
                        "validation_errors": [],
                        "self_comparison": True,
                    }
                )
                continue
            setup = row["input"]["entry_setup_evidence_v1"]
            schema = entry_risk_adjudication_openai_schema(setup)
            prompt = candidate_prompt
            identity = digest([day, key, input_identity(row), candidate, digest(prompt), digest(schema)])
            cached = results.get(key) or {}
            if cached and cached.get("candidate_identity") != identity:
                results.pop(key, None)
                cached = {}
            if not execute or calls >= max_new:
                continue
            if (
                valid(cached)
                and cached.get("input_sha256") == input_identity(row)
                and not cached.get("validation_errors")
            ):
                continue
            try:
                request = {
                    "paired_replay_id": identity,
                    "paired_replay_parent_id": key,
                    "stage": "entry",
                    "candidate_input": row["input"],
                    "control": {"provider": "openai", "model": "gpt-5.4-nano"},
                    "candidate": {
                        "provider": "openai",
                        "model": "gpt-5.4-nano",
                        "prompt_version": candidate,
                        "system_prompt": prompt,
                        "response_schema": schema,
                        "response_schema_sha256": quality._sha256(schema),
                        "schema_name": "entry_setup_risk_adjudication_v1",
                        "max_output_tokens": 512,
                        "reasoning_effort": "none",
                    },
                    **AUTHORITY,
                }
                if runner is None:
                    from src.engine.scalping.micro_reversion.provider_budget import (
                        ProviderBudgetLedger,
                        load_reviewed_pricing_artifact,
                        AttemptIdentity,
                        TokenCeiling,
                    )

                    now = datetime.now(KST)
                    if ledger is None:
                        ledger = ProviderBudgetLedger(
                            ledger_path=root
                            / "offline_provider_budget"
                            / f"ai_micro_reversion_provider_budget_{now.date()}.jsonl",
                            pricing=load_reviewed_pricing_artifact(
                                root / "policy/micro_reversion/provider_pricing.json",
                                as_of_date=now.date(),
                            ),
                            execution_date=now.date(),
                            daily_attempt_cap=390,
                            daily_usd_cap="1.0",
                        )
                    attempt = AttemptIdentity(
                        day,
                        key,
                        identity,
                        "compact_auxiliary",
                        "openai",
                        "gpt-5.4-nano",
                        1,
                    )
                    permit = ledger.reserve_attempt(
                        attempt,
                        token_ceiling=TokenCeiling(
                            len(json.dumps(row["input"]).encode())
                            + len(prompt.encode())
                            + 4096,
                            512,
                        ),
                    )
                    calls += 1
                    result = quality.execute_openai_prompt_v2_candidate(
                        request, timeout_sec=timeout_sec
                    )
                    provenance = result.get("provider_provenance") or {}
                    settlement = ledger.settle_attempt(
                        attempt,
                        actual_input_tokens=provenance["input_tokens"],
                        actual_output_tokens=provenance["output_tokens"],
                        provider_response_sha256=provenance["response_sha256"],
                    )
                    result["provider_budget_reservation_id"] = permit.reservation_id
                    result["evaluation_provider_cost_usd"] = str(
                        settlement.actual_cost_usd
                    )
                else:
                    calls += 1
                    result = runner(request)
                result["validation_errors"] = validate_entry_risk_adjudication(
                    result.get("candidate_response"), setup_evidence=setup
                )
                results[key] = sealed(
                    {
                        **result,
                        "input_sha256": input_identity(row),
                        "candidate_identity": identity,
                    }
                )
                write(
                    path.with_suffix(".checkpoint.json"),
                    sealed(
                        {
                            "candidate_prompt_version": candidate,
                            "results": results,
                            **AUTHORITY,
                        }
                    ),
                )
            except Exception as exc:
                execution_errors.append(type(exc).__name__)
                break
        cost_receipt = runtime_inference_cost_receipt(root, day)
        for key, result in list(results.items()):
            if valid(result) and cost_receipt["status"] == "reviewed_operator_zero_cost":
                results[key] = sealed({**result, "runtime_inference_cost_delta_krw": cost_receipt["delta_krw"],
                                       "runtime_inference_cost_receipt": cost_receipt})
        metrics = evaluate([
            {**row,"exclusion_reason":row.get("exclusion_reason") or primary_blockers.get(row["evaluation_key"],(None,None))[1]}
            for row in projection["rows"]], results)
        metrics["operating_economic_comparison"] = operating_comparison_metrics(
            metrics["pairs"], projection.get("owner_execution_model_validation") or {})
        versions = sorted({r["incumbent_prompt_version"] for r in projection["rows"]})
        status = (
            "source_contract_blocked"
            if not projection["source_tuning_allowed"]
            else "valid_empty"
            if not projection["rows"]
            else "source_contract_blocked"
            if metrics["economic_eligible_count"] == 0
            else "incumbent_preserved"
            if versions == [candidate]
            else "execution_failed"
            if execution_errors
            else "comparison_complete"
            if metrics["paired_comparable_count"] == metrics["economic_eligible_count"]
            else "execution_deferred"
        )
        plan_path = path.parent / f"compact_candidate_plan_{candidate}.json"
        history = []
        coverage_history = []
        for old_path in sorted(
            path.parent.glob("compact_auxiliary_paired_economic_*.json")
        ):
            old = read(old_path)
            if (
                valid(old)
                and old.get("schema") == SCHEMA
                and old.get("target_date", "") < day
                and old.get("candidate_prompt_version") == candidate
                and old.get("promotion_contract_sha256") == digest(CONTRACT)
            ):
                history.extend(old.get("metrics", {}).get("pairs", []))
                coverage_history.append(old)
        all_pairs = history + metrics["pairs"]
        population = [
            {**row, "exclusion_reason": row.get("exclusion_reason") or primary_blockers.get(row["evaluation_key"], (None, None))[1]}
            for row in projection["rows"]]
        # Count every eligible earlier request, including unanswered requests;
        # successful pairs alone cannot establish chronological coverage.
        cumulative_coverage = {}
        for scope, group in _scope_groups(population).items():
            versions_in_scope = {r.get("incumbent_prompt_version") for r in group}
            incumbent = next(iter(versions_in_scope)) if len(versions_in_scope) == 1 else None
            receipts = [metrics["scope_coverage"][scope]]
            for old in coverage_history:
                old_scope = (old.get("scope_validation") or {}).get(scope, old)
                if old_scope.get("incumbent_prompt_version") == incumbent:
                    receipt = (old.get("metrics", {}).get("scope_coverage") or {}).get(scope)
                    if receipt:
                        receipts.append(receipt)
            totals = {k: sum(r.get(k, 0) for r in receipts) for k in
                      ("screened_total", "paired_comparable_count", "source_excluded_count", "economic_eligible_count")}
            totals["denominator_preserved"] = all(r.get("denominator_preserved") is True for r in receipts)
            totals["response_coverage"] = (totals["paired_comparable_count"] / totals["economic_eligible_count"]
                                           if totals["economic_eligible_count"] else None)
            cumulative_coverage[scope] = totals
        with plan_path.with_suffix(".lock").open("a") as candidate_lock:
            fcntl.flock(candidate_lock, fcntl.LOCK_EX)
            plan = read(plan_path)
            if plan and (not valid(plan) or plan.get("candidate_prompt_version") != candidate):
                raise ValueError("candidate_plan_hash_invalid")
            if (plan.get("scope_candidates") and plan.get("candidate_prompt_sha256")
                    and plan["candidate_prompt_sha256"] != digest(candidate_prompt)):
                raise ValueError("frozen_candidate_prompt_or_schema_changed")
            if plan.get("scope_candidates") and plan.get("promotion_contract_sha256") != digest(CONTRACT):
                raise ValueError("candidate_plan_contract_mismatch")
            scope_validation, scope_candidates = scope_candidate_validation(
                all_pairs, population, {"scope_coverage": cumulative_coverage}, plan,
                candidate=candidate, now=datetime.now(KST))
            if scope_candidates != (plan.get("scope_candidates") or {}):
                write(plan_path, sealed({"candidate_prompt_version": candidate,
                    "scope_candidates": scope_candidates, "promotion_contract_sha256": digest(CONTRACT),
                    "candidate_prompt_sha256": digest(candidate_prompt), **AUTHORITY}))
        frozen_at = min((v["candidate_frozen_at"] for v in scope_validation.values()
                         if v["candidate_frozen_at"]), default=None)
        chronology = {"candidate_frozen_at": frozen_at,
            "learning_pairs": [p for v in scope_validation.values() for p in v["chronological_validation"]["learning_pairs"]],
            "holdout_pairs": [p for v in scope_validation.values() for p in v["chronological_validation"]["holdout_pairs"]],
            "holdout_consumed": False}
        report = sealed(
            {
                "schema": SCHEMA,
                "target_date": day,
                "status": status,
                "generated_at": datetime.now(KST).isoformat(),
                "candidate_frozen_at": frozen_at,
                "candidate_prompt_version": candidate,
                "candidate_contract_sha256": candidate_contract,
                "incumbent_prompt_version": versions[0] if len(versions) == 1 else None,
                "source_manifest_sha256": projection["source_manifest_sha256"],
                "source_projection_sha256": projection["artifact_content_sha256"],
                "source_label_report_sha256": projection.get("source_label_report_sha256"),
                "owner_execution_model_validation": projection.get("owner_execution_model_validation") or {},
                "post_apply_decision_version_performance": applied_decision_version_performance(
                    read(root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json"),day=day),
                "owner_execution_model_status": (projection.get("owner_execution_model_validation") or {}).get("status", "missing"),
                "promotion_contract_sha256": digest(CONTRACT),
                "promotion_contract": CONTRACT,
                "candidate_improvement_proven": False,
                "promotion_pass": False,
                "selection_disposition": "incumbent_preserved",
                "provider_calls_this_run": calls,
                "execution_errors": execution_errors,
                "results": results,
                "metrics": metrics,
                "evaluation_provider_cost_usd": sum(
                    float(r.get("evaluation_provider_cost_usd") or 0)
                    for r in results.values()
                ),
                "runtime_inference_cost_delta_krw": cost_receipt["delta_krw"],
                "runtime_inference_cost_status": cost_receipt["status"],
                "runtime_inference_cost_receipt": cost_receipt,
                "chronological_validation": chronology,
                "scope_validation": scope_validation,
                "comparison_dependency_signatures": _comparison_signatures(path.parent, day, candidate),
                "next_owner": "existing_main_owner_execution_cf_and_portfolio_replay",
                "closure_test": "full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts",
                **AUTHORITY,
            }
        )
        from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES
        report["promotion_scopes"] = [scope for scope in AUTO_PROMOTION_SCOPES if promotion_valid(
            report, incumbent=(scope_validation.get(scope) or {}).get("incumbent_prompt_version"), selected=candidate,
            source_manifest_sha256=report["source_manifest_sha256"], scope=tuple(scope.split("|")))]
        report["promotion_pass"] = bool(report["promotion_scopes"])
        report["candidate_improvement_proven"] = report["promotion_pass"]
        report["selection_disposition"] = (
            "candidate_selected" if report["promotion_pass"] else "incumbent_preserved"
        )
        report["candidate_zero_disposition"] = candidate_zero_disposition(projection["rows"], primary_blockers, report)
        report = sealed(report)
        write(path, report)
        return report


def finalize(*, data_root, day, publication_day, preserve_noncompact_scope=False):
    path = report_path(data_root, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _finalize(data_root=data_root, day=day, publication_day=publication_day,
                         preserve_noncompact_scope=preserve_noncompact_scope)


def _finalize(*, data_root, day, publication_day, preserve_noncompact_scope=False):
    """Reuse calibration, optimizer, publisher and final consumer; no provider."""
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping.micro_reversion import (
        main_ai_prompt_optimizer as optimizer,
    )
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    from src.engine.scalping import main_ai_prompt_consumer as consumer

    root = Path(data_root)
    if publication_day > datetime.now(KST).date().isoformat():
        raise ValueError("compact_publication_date_in_future")
    report = calibration.build_compact_scope_report(root, day, publication_day,
                                                    preserve_noncompact_scope=preserve_noncompact_scope)
    integration = report.get("postclose_integration") or {}
    if integration.get("phase") == "finalize":
        expected = (integration.get("phases") or {}).get("finalize") or {}
        paired = report["hierarchical_entry_quality"]["machine_decision_case_table"]["compact_auxiliary_screen_outcomes"]["paired_economic_evaluation"]
        if (expected.get("paired_artifact_content_sha256") != paired["artifact_content_sha256"]
                or integration.get("source_label_report_sha256") != report["hierarchical_entry_quality"]["machine_decision_case_table"]["ai_quality_diagnostics"]["source_label_report_sha256"]
                or (integration.get("dependency_signatures") is not None
                    and integration["dependency_signatures"] != source_dependency_signatures(root, day))):
            raise ValueError("postclose_finalize_source_changed_before_publication")
    calibration_path = calibration.report_path(publication_day, root / "report")
    calibration._atomic_write_json(calibration_path, report)
    table = report["hierarchical_entry_quality"]["machine_decision_case_table"]
    if preserve_noncompact_scope and table.get("microstructure_evaluation") is not None:
        from src.engine.scalping.microstructure_reaction_context import refresh_machine_evaluation_link
        refresh_machine_evaluation_link(calibration_path, report_root=root / "report")
    bundle = policy.publish(calibration_path, data_root=root)
    if bundle is None:
        raise ValueError("compact_dated_policy_not_published")
    optimizer_path = (
        root
        / "report/main_ai_prompt_optimizer"
        / f"main_ai_prompt_optimizer_{publication_day}.json"
    )
    plan = read(optimizer_path)
    if optimizer_path.exists() and not valid(plan):
        raise ValueError("compact_optimizer_existing_hash_invalid")
    plan.update(
        schema=optimizer.SCHEMA,
        target_date=publication_day,
        compact_auxiliary_evaluation=optimizer.compact_evaluation_plan(report),
        compact_scope_status="terminal_evaluation_policy_published",
        compact_source_calibration_artifact_content_sha256=report["artifact_content_sha256"],
        **AUTHORITY,
    )
    write(optimizer_path, sealed(plan))
    paired = report["hierarchical_entry_quality"]["machine_decision_case_table"][
        "compact_auxiliary_screen_outcomes"
    ]["paired_economic_evaluation"]
    view = {
        "schema": "compact_auxiliary_consumer_handoff_v2",
        "source_date": day,
        "publication_date": publication_day,
        "effective_date": bundle["target_date"],
        "paired_artifact_content_sha256": paired["artifact_content_sha256"],
        "calibration_artifact_content_sha256": report["artifact_content_sha256"],
        "optimizer_artifact_content_sha256": read(optimizer_path)[
            "artifact_content_sha256"
        ],
        "policy_bundle_sha256": bundle["bundle_sha256"],
        "calibration_path": str(calibration_path.resolve()),
        "optimizer_path": str(optimizer_path.resolve()),
        "paired_path": str(report_path(root, day).resolve()),
        "evaluation_status": paired["status"],
        "selection_disposition": "candidate_selected"
        if bundle.get("compact_promoted_scopes") or (bundle["ai_policy"]["prompt_version"] == paired["candidate_prompt_version"]
        and paired["candidate_prompt_version"] != paired["incumbent_prompt_version"])
        else "incumbent_preserved",
        "next_owner": paired.get(
            "next_owner", "existing_main_owner_execution_cf_and_portfolio_replay"
        ),
        "closure_test": paired.get(
            "closure_test",
            "full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts",
        ),
        "candidate_improvement_proven": paired["candidate_improvement_proven"],
        "postclose_integration": report.get("postclose_integration"),
        "metrics": {k: v for k, v in paired["metrics"].items() if k != "pairs"},
        "actual_pid_consumed": False,
        "actual_net_profit_improvement": None,
        **AUTHORITY,
    }
    consumer_path = (
        root
        / "report/main_ai_prompt_consumer"
        / f"main_ai_prompt_consumer_{publication_day}.json"
    )
    handoff = read(consumer_path)
    if consumer_path.exists() and not valid(handoff):
        raise ValueError("compact_consumer_existing_hash_invalid")
    handoff.update(
        schema=consumer.SCHEMA,
        target_date=publication_day,
        compact_auxiliary=view,
        compact_scope_status="connected_terminal_evaluation_and_dated_policy",
        **AUTHORITY,
    )
    write(consumer_path, sealed(handoff))
    refresh_summaries(root, day, view, consumer_path)
    verified = consumer.verify_compact_handoff(root, day)
    if verified["status"] != "PASS":
        raise ValueError(
            "compact_last_consumer_handoff_failed:" + ",".join(verified["issues"])
        )
    return {
        "status": "compact_scope_policy_and_summary_handoff_complete",
        **view,
        "strict_family_verification": verified,
    }


def refresh_handoff(*, data_root, day, publication_day):
    """Rebind late summaries without candidate execution or policy publication."""
    from src.engine.scalping import main_ai_prompt_consumer as consumer
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    root = Path(data_root).resolve()
    path = report_path(root, day)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        consumer_path = root / "report/main_ai_prompt_consumer" / f"main_ai_prompt_consumer_{publication_day}.json"
        handoff = read(consumer_path)
        view = handoff.get("compact_auxiliary") or {}
        paired = read(path)
        bundle = policy.load(data_root=root, target_date=view.get("effective_date", ""))
        if (not valid(handoff) or not valid(paired) or view.get("source_date") != day
                or view.get("publication_date") != publication_day
                or view.get("paired_artifact_content_sha256") != paired.get("artifact_content_sha256")
                or bundle is None or bundle["bundle_sha256"] != view.get("policy_bundle_sha256")):
            raise ValueError("compact_existing_handoff_generation_invalid")
        refresh_summaries(root, day, view, consumer_path)
        verified = consumer.verify_compact_handoff(root, day)
        if verified["status"] != "PASS":
            raise ValueError("compact_last_consumer_handoff_failed:" + ",".join(verified["issues"]))
        return {"status": "compact_scope_policy_and_summary_handoff_complete", **view,
                "strict_family_verification": verified}


def source_is_compact(report):
    return report.get("report_scope") == "compact_auxiliary_only"


def summary_paths(root, day):
    root = Path(root) / "report"
    tower = (
        root
        / "tuning_performance_control_tower"
        / f"tuning_performance_control_tower_{day}.json"
    )
    if not tower.exists():
        tower = (
            root
            / "tuning_performance_control_tower"
            / f"compact_auxiliary_control_tower_{day}.json"
        )
    return [
        root / f"threshold_cycle_{day}.json",
        root / "threshold_cycle_ev" / f"threshold_cycle_ev_{day}.json",
        root / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json",
        tower,
    ]


def refresh_summaries(root, day, view, consumer_path):
    """Update only one section; preserve canonical native terminal/other families."""
    sources = {}
    for path in summary_paths(root, day):
        before = path.stat() if path.exists() else None
        value = read(path)
        if not value:
            if path.name.startswith("compact_auxiliary_control_tower_"):
                value = {
                    "schema": "compact_auxiliary_scoped_control_tower_v1",
                    "source_date": day,
                    "whole_native_chain_done_claimed": False,
                }
            else:
                raise ValueError("compact_last_summary_missing:" + str(path))
        value["compact_auxiliary_economic_tuning"] = view
        if before and (before.st_ino, before.st_size, before.st_mtime_ns) != (
            path.stat().st_ino,
            path.stat().st_size,
            path.stat().st_mtime_ns,
        ):
            raise ValueError("compact_summary_changed_during_refresh")
        if "artifact_content_sha256" in value:
            value = sealed(value)
        write(path, value)
        sources[str(path.resolve())] = digest(view)
    from src.engine.build_next_stage2_checklist import (
        _checklist_write_lock,
        _atomic_write_checklist,
        _render_new_document,
    )

    checklist_path = (
        Path(root).parent
        / "docs/checklists"
        / f"{view['effective_date']}-stage2-todo-checklist.md"
    )
    start, end = (
        "<!-- compact_auxiliary_handoff:start -->",
        "<!-- compact_auxiliary_handoff:end -->",
    )
    block = "\n".join(
        [
            start,
            f"<!-- compact_auxiliary_handoff_sha256:{digest(view)} -->",
            "",
            "## Compact auxiliary 장후 handoff",
            "",
            f"- 평가 원천 {day}; 발행 {view['publication_date']}; 적용 {view['effective_date']}. 선정 상태 `{view['selection_disposition']}`, 평가 상태 `{view['evaluation_status']}`.",
            f"- 정책 bundle `{view['policy_bundle_sha256']}`; consumer generation `{read(consumer_path)['artifact_content_sha256']}`. 실제 PID 소비 및 자연 비용 후 성과는 미확인이다.",
            f"- 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`; 다음 확인 `{view['next_owner']}` / `{view['closure_test']}`. 결손 net은 null이며 이 기록은 주문·guard·provider 변경 승인이 아니다.",
            "",
            end,
        ]
    )
    with _checklist_write_lock(checklist_path):
        text = (
            checklist_path.read_text(encoding="utf-8")
            if checklist_path.exists()
            else _render_new_document(view["effective_date"], "")
        )
        if start in text:
            a, b = text.index(start), text.index(end) + len(end)
            text = text[:a] + block + text[b:]
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
        _atomic_write_checklist(checklist_path, text)
    receipt_path = (
        Path(root)
        / "report/main_ai_prompt_consumer"
        / f"compact_summary_handoff_{day}.json"
    )
    write(
        receipt_path,
        sealed(
            {
                "schema": "compact_summary_handoff_v1",
                "source_date": day,
                "consumer_path": str(consumer_path.resolve()),
                "consumer_artifact_content_sha256": read(consumer_path)[
                    "artifact_content_sha256"
                ],
                "summary_section_hashes": sources,
                "checklist_path": str(checklist_path.resolve()),
                "checklist_section_sha256": digest(view),
                "whole_native_chain_done_claimed": False,
                **AUTHORITY,
            }
        ),
    )
