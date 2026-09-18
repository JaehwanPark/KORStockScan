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
    "schema": "compact_auxiliary_paired_promotion_v3",
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
}


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
        ENTRY_OPERATING_SCHEMA, entry_operating_model_identity,
    )
    from src.engine.monitoring.research_closed_loop import digest as owner_digest
    if not owner_replay_valid(replay, row):
        return {}
    seed = replay["seed"]
    context = seed.get("operating_contract") or {}
    arm = (replay.get("operating_arms") or {}).get(split.QUANTITY_LEG_FOUR_ARM_IDS[0]) or {}
    if (
        context.get("schema") != ENTRY_OPERATING_SCHEMA
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
            return True
    return False


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
    owner_source = (
        (split.get("input_summary") or {}).get("daily_diagnostic") or {}
    ).get("entry_opportunity_executable_replay") or {}
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
                "input": raw if not reason else None,
                "owner_replay": owner_replay if owner_valid else None,
                "entry_quality_path": path,
                "exclusion_reason": reason,
            }
        )
    return sealed(
        {
            "schema": "compact_auxiliary_frozen_projection_v1",
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
            exclusions[reason] += 1
            continue
        candidate = response.get("risk_verdict")
        incumbent = row.get("incumbent_verdict")
        if candidate not in {"PASS", "VETO", "CAUTION"}:
            exclusions["routing_semantics_missing"] += 1
            continue
        if "CAUTION" in (incumbent, candidate):
            exclusions["caution_followup_terminal_missing"] += 1
            continue
        net = arm.get("net_return_pct") if owner_valid else terminal - cost
        stress_net = arm.get("stress_net_return_pct") if owner_valid else net - cost
        if not finite(net) or not finite(stress_net):
            exclusions["terminal_net_missing"] += 1
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
        "forbidden_uses": [
            "actual_pnl",
            "standalone_prompt_promotion",
            "broker_authority",
        ],
        "pairs": pairs,
    }


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


def promotion_valid(report, *, incumbent, selected, source_manifest_sha256):
    """A percentage path alone cannot prove executable daily net-profit uplift."""
    if (
        not valid(report)
        or report.get("schema") != SCHEMA
        or report.get("candidate_prompt_version") != selected
        or report.get("incumbent_prompt_version") != incumbent
        or selected == incumbent
        or report.get("source_manifest_sha256") != source_manifest_sha256
        or report.get("promotion_contract_sha256") != digest(CONTRACT)
        or any(report.get(k) is not v for k, v in AUTHORITY.items())
    ):
        return False
    from src.engine.scalping.entry_split_order_plan import EXECUTION_MODEL_CONTRACT
    model = report.get("owner_execution_model_validation") or {}
    if (model.get("contract_version") != EXECUTION_MODEL_CONTRACT
            or model.get("source_date") != report.get("target_date")
            or model.get("status") != "validated_scope"
            or model.get("allowed_runtime_apply") is not True):
        return False
    proof = report.get("chronological_validation") or {}
    if proof.get("candidate_frozen_at") != report.get("candidate_frozen_at"):
        return False
    learning, holdout = (
        proof.get("learning_pairs") or [],
        proof.get("holdout_pairs") or [],
    )
    try:
        frozen_day = (
            datetime.fromisoformat(report["candidate_frozen_at"])
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
    if not cohorts or report.get("metrics", {}).get("response_coverage") != 1.0:
        return False
    if ("KRX", "KRX_REGULAR", "KRX") not in cohorts:
        return False
    for train, test in [cohorts[("KRX", "KRX_REGULAR", "KRX")]]:
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
    return proof.get("holdout_consumed") is False


def consume_holdout(proof, data_root):
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
    for pair in proof["chronological_validation"]["holdout_pairs"]:
        key = pair["evaluation_key"]
        if key in claims and claims[key] != identity:
            raise ValueError("compact_holdout_already_consumed")
        claims[key] = identity
    write(path, sealed({"claims": claims, **AUTHORITY}))


def run(
    *,
    data_root,
    day,
    candidate_version=None,
    execute=False,
    max_new=30,
    timeout_sec=45.0,
    runner=None,
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
    root = Path(data_root)
    path = report_path(root, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        projection_path = path.with_suffix(".source.json")
        projection = read(projection_path)
        dependency_paths = [
            root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl",
            root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl",
            root
            / "report/ai_decision_outcome_labels"
            / f"ai_decision_outcome_labels_{day}.json",
            root
            / "report/observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json",
            root
            / "report/entry_split_order_plan"
            / f"entry_split_order_plan_{day}.json",
        ]
        signatures = {}
        for dependency in dependency_paths:
            actual = (
                dependency if dependency.exists() else Path(str(dependency) + ".gz")
            )
            signatures[str(dependency)] = (
                [actual.stat().st_size, actual.stat().st_mtime_ns]
                if actual.exists()
                else None
            )
        label_dependency = str(root / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{day}.json")
        # An additive label contract revision does not require rereading large
        # frozen raw inputs. Changed diagnostic/economic paths still rebuild.
        if valid(projection) and projection.get("projection_contract_sha256") == digest(CONTRACT):
            prior = projection.get("dependency_signatures") or {}
            if prior.get(label_dependency) != signatures.get(label_dependency) and all(
                    prior.get(k) == v for k, v in signatures.items() if k != label_dependency):
                label_report = read(Path(label_dependency))
                label_index = {x.get("decision_trace_id"): x for x in label_report.get("labels") or [] if isinstance(x, dict)}
                if label_report.get("target_date") == day and all(
                        row.get("entry_quality_path") == (((label_index.get(row.get("evaluation_key")) or {}).get("horizon_metrics") or {}).get("10m") or {}).get("entry_quality_path", {})
                        for row in projection.get("rows") or []):
                    write(path.parent / "compact_source_generations" / (projection["artifact_content_sha256"] + ".json"), projection)
                    projection = sealed({**projection, "dependency_signatures": signatures,
                                         "source_label_report_sha256": digest(label_report)})
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
            projection = sealed(
                {**prepare(root, day), "dependency_signatures": signatures, "projection_contract_sha256": digest(CONTRACT)}
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
        previous = read(path)
        if valid(previous) and previous.get("candidate_prompt_version") != candidate:
            raise ValueError("frozen_candidate_selection_mismatch")
        if (valid(previous)
                and previous.get("promotion_contract_sha256") == digest(CONTRACT)
                and previous.get("source_projection_sha256") == projection["artifact_content_sha256"]
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
        for row in projection["rows"]:
            key = row["evaluation_key"]
            if row["exclusion_reason"] or not projection["source_tuning_allowed"]:
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
            if not execute or calls >= max_new:
                continue
            cached = results.get(key) or {}
            if (
                valid(cached)
                and cached.get("input_sha256") == input_identity(row)
                and not cached.get("validation_errors")
            ):
                continue
            try:
                setup = row["input"]["entry_setup_evidence_v1"]
                schema = entry_risk_adjudication_openai_schema(setup)
                prompt = compact_auxiliary_prompt(prompt_version=candidate)
                identity = digest(
                    [
                        day,
                        key,
                        input_identity(row),
                        candidate,
                        digest(prompt),
                        digest(schema),
                    ]
                )
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
        metrics = evaluate(projection["rows"], results)
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
        plan = read(plan_path)
        if plan and not valid(plan):
            raise ValueError("candidate_plan_hash_invalid")
        history = []
        for old_path in sorted(
            path.parent.glob("compact_auxiliary_paired_economic_*.json")
        ):
            old = read(old_path)
            if (
                valid(old)
                and old.get("schema") == SCHEMA
                and old.get("target_date", "") < day
                and old.get("candidate_prompt_version") == candidate
                and old.get("incumbent_prompt_version") in versions
                and old.get("promotion_contract_sha256") == digest(CONTRACT)
            ):
                history.extend(old.get("metrics", {}).get("pairs", []))
        all_pairs = history + metrics["pairs"]
        frozen_at = plan.get("candidate_frozen_at")
        if (
            not frozen_at
            and len(
                {
                    (p["source_date"], p["scanner_promotion_id"])
                    for p in all_pairs
                    if (p["effective_venue"], p["session_bucket"], p["broker_route"])
                    == ("KRX", "KRX_REGULAR", "KRX")
                }
            )
            >= CONTRACT["learning_episode_floor"]
        ):
            frozen_at = datetime.now(KST).isoformat()
            write(
                plan_path,
                sealed(
                    {
                        "candidate_prompt_version": candidate,
                        "candidate_frozen_at": frozen_at,
                        "learning_manifest_sha256": digest(all_pairs),
                        **AUTHORITY,
                    }
                ),
            )
        frozen_day = frozen_at[:10] if frozen_at else day
        report = sealed(
            {
                "schema": SCHEMA,
                "target_date": day,
                "status": status,
                "generated_at": datetime.now(KST).isoformat(),
                "candidate_frozen_at": frozen_at,
                "candidate_prompt_version": candidate,
                "incumbent_prompt_version": versions[0] if len(versions) == 1 else None,
                "source_manifest_sha256": projection["source_manifest_sha256"],
                "source_projection_sha256": projection["artifact_content_sha256"],
                "source_label_report_sha256": projection.get("source_label_report_sha256"),
                "owner_execution_model_validation": projection.get("owner_execution_model_validation") or {},
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
                "runtime_inference_cost_delta_krw": None,
                "runtime_inference_cost_status": "same_model_token_delta_and_reviewed_krw_conversion_required",
                "chronological_validation": {
                    "candidate_frozen_at": frozen_at,
                    "learning_pairs": [
                        p for p in all_pairs if p["source_date"] <= frozen_day
                    ],
                    "holdout_pairs": [
                        p for p in all_pairs if p["source_date"] > frozen_day
                    ],
                    "holdout_consumed": False,
                },
                "next_owner": "existing_main_owner_execution_cf_and_portfolio_replay",
                "closure_test": "full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts",
                **AUTHORITY,
            }
        )
        report["promotion_pass"] = promotion_valid(
            report,
            incumbent=report["incumbent_prompt_version"],
            selected=candidate,
            source_manifest_sha256=report["source_manifest_sha256"],
        )
        report["candidate_improvement_proven"] = report["promotion_pass"]
        report["selection_disposition"] = (
            "candidate_selected" if report["promotion_pass"] else "incumbent_preserved"
        )
        report = sealed(report)
        write(path, report)
        return report


def finalize(*, data_root, day, publication_day):
    path = report_path(data_root, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _finalize(data_root=data_root, day=day, publication_day=publication_day)


def _finalize(*, data_root, day, publication_day):
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
    report = calibration.build_compact_scope_report(root, day, publication_day)
    calibration_path = calibration.report_path(publication_day, root / "report")
    calibration._atomic_write_json(calibration_path, report)
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
        if bundle["ai_policy"]["prompt_version"] == paired["candidate_prompt_version"]
        and paired["candidate_prompt_version"] != paired["incumbent_prompt_version"]
        else "incumbent_preserved",
        "next_owner": paired.get(
            "next_owner", "existing_main_owner_execution_cf_and_portfolio_replay"
        ),
        "closure_test": paired.get(
            "closure_test",
            "full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts",
        ),
        "candidate_improvement_proven": paired["candidate_improvement_proven"],
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
