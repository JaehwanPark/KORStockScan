"""Offline confirmation-grammar research; no runtime caller or publisher.

The prototype composes two existing kernels. Its overlay is deliberately NOT
accepted by the live policy validator. Metrics cannot confer that authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import itertools
import json
from pathlib import Path
import resource
import time

from src.engine.scalping import entry_policy_hypothesis_research as prior

C, S, E = prior.compact, prior.strategy, prior.evidence
AUTHORITY = {**prior.AUTHORITY, "broker_order_forbidden": True,
             "pristine_holdout": False, "registered_kernel": False,
             "metric_role": "offline_cost_bound_machine_path_not_actual_profit"}
ALLOWED_REASONS = {"MICRO_PRICE_RESPONSE_RECHECK", "TRIGGER_CONFIRMATION_RECHECK"}
DIMENSIONS = ("structure_phase", "liquidity_band", "volatility_band")
SOFT_SETUP_FACTS = {"trigger_confirmation_missing", "volume_confirmation_missing",
                    "micro_continuation_unconfirmed", "no_supported_setup"}


def write(path, value):
    C.write(path, C.sealed({**value, **AUTHORITY}))


def prepare(row, parent):
    """No outcomes participate in either parent replay or context production."""
    setup = row["setup_evidence"]
    decision = E.mechanistic_entry_policy_decision(setup, policy=parent)
    rebuilt, effective, receipt = S.rebuild(setup, parent)
    return dict(decision=decision, rebuilt=rebuilt, effective=effective, receipt=receipt)


def definitions(training_prepared, *, extend_setup=False):
    """Observed training types only; no symbol, future label or guessed type."""
    choices = {}
    for prepared in training_prepared:
        context = prepared["rebuilt"].get("mechanistic_context") or {}
        parts = (context.get("group") or {}).get("key_parts") or {}
        if (parts.get("venue"), parts.get("session_bucket")) != ("KRX", "KRX_REGULAR"):
            continue
        pairs = [(key, parts[key]) for key in DIMENSIONS if parts.get(key) not in (None, "", "UNKNOWN")]
        for family in (context.get("flow") or {}).get("matched_families") or []:
            if family not in E.MECHANISTIC_FLOW_FAMILIES:
                continue
            for size in range(3):
                for subset in itertools.combinations(pairs, size):
                    for recipe in (["legacy_group_trigger", "family_setup_confirmation"] if extend_setup else ["legacy_group_trigger"]):
                        spec = dict(flow_family=family, match=dict(venue="KRX", session_bucket="KRX_REGULAR", **dict(subset)))
                        if extend_setup:
                            spec["recipe"] = recipe
                        choices[S.digest(spec)] = spec
    return [dict(id=key[:16], **value) for key, value in sorted(choices.items())]


def prototype_decision(row, parent, prepared, spec):
    """Resolve only an existing soft confirmation wait; keep all other guards.

    The existing hierarchy kernel requires fresh usable positive flow AND
    positive price response and compensates only trigger/volume confirmation.
    Thresholds are the exact effective parent leaf. No new fact is fabricated.
    """
    baseline = prepared["decision"]
    if baseline["action"] != "RECHECK" or baseline["reason"] not in ALLOWED_REASONS:
        return dict(action=baseline["action"], reason="parent_guard_or_action_preserved")
    # A selected parent micro recipe has extra conditions. Until this adapter
    # carries those conditions explicitly, it cannot replace that decision.
    if prepared["receipt"]["effective_thresholds"]["micro_confirmation_recipe"] != 0:
        return dict(action=baseline["action"], reason="parent_micro_recipe_preserved")
    policy = deepcopy(prepared["effective"])
    rule = dict(id=spec["id"], match=spec["match"], flow_family=spec["flow_family"],
                thresholds={key: policy["thresholds"][key] for key in E.MECHANISTIC_PARAMETER_BOUNDS},
                symbols={}, micro=None)
    policy["hierarchy"] = dict(schema=E.MECHANISTIC_HIERARCHY_SCHEMA,
        parent_sha256=S.digest(policy["thresholds"]), rules=[rule])
    errors = E.validate_mechanistic_entry_threshold_policy(policy)
    if errors:
        raise ValueError("prototype_scalar_policy_invalid:" + ",".join(errors))
    decision = E.mechanistic_entry_policy_decision(prepared["rebuilt"], policy=policy)
    if decision.get("hierarchy_selection", {}).get("rule_id") != spec["id"]:
        return dict(action=baseline["action"], reason="unmatched_parent_inherited")
    if spec.get("recipe") == "family_setup_confirmation" and family_setup_confirmed(prepared, decision):
        decision = {**decision, "action": "ENTER_NOW", "reason": "offline_family_setup_confirmation",
                    "confirmation_basis": "matched_flow_family_and_current_trusted_positive_flow_price",
                    "replaced_soft_fact_ids": [risk["fact_id"] for risk in decision["core_comparison"]["risk_assessments"]
                                               if risk["disposition"] != "COMPENSATED"]}
    # The strategy outer layer normally owns this veto after fact rebuilding.
    decision = E._apply_entry_situation_veto(decision, row["setup_evidence"], parent)
    if decision["action"] != "ENTER_NOW":
        return dict(action=baseline["action"], reason=decision["reason"])
    return dict(action="ENTER_NOW", reason=decision["reason"],
                group_trigger_pass=decision.get("group_trigger_pass"),
                hierarchy_selection=decision.get("hierarchy_selection"),
                replaced_soft_fact_ids=decision.get("replaced_soft_fact_ids", []))


def family_setup_confirmed(prepared, decision):
    """Explicit unregistered hypothesis, not a fabricated production fact."""
    setup = prepared["rebuilt"]
    micro = setup.get("micro_recovery_observation") or {}
    thresholds = decision["applied_thresholds"]
    price = E._number(micro.get("price_change_10t_pct"))
    delta = E._number(micro.get("net_aggressive_delta_10t"))
    core = decision["core_comparison"]
    return bool(core.get("preferred_action") == "RECHECK"
        and not (setup.get("local_breakout") or {}).get("recheck_required")
        and decision.get("liquidity_inputs_complete") is True and decision.get("liquidity_threshold_pass") is True
        and micro.get("source_usable") is True and price is not None and delta is not None
        and price > thresholds["minimum_micro_price_change_10t_pct"]
        and delta >= thresholds["minimum_micro_net_aggressive_delta_10t"]
        and any(risk["disposition"] == "RECHECKABLE" for risk in core["risk_assessments"])
        and all(risk["disposition"] == "COMPENSATED" or
                (risk["disposition"] == "RECHECKABLE" and risk["risk_code"] == "CONFIRMATION_MISSING"
                 and risk["fact_id"] in SOFT_SETUP_FACTS) for risk in core["risk_assessments"]))


def rank(metric, *, complexity=0):
    return tuple(-1e100 if value is None else value for value in S.machine_admission_rank(metric, complexity=complexity))


def choose(training, vectors, *, specifications=None):
    """Selection has no held-out argument. Every tie uses a fixed digest ID."""
    metrics = {key: prior.economy(training, actions) for key, actions in vectors.items()}
    eligible = [key for key in sorted(metrics) if prior.research_qualified(metrics[key])]
    def complexity(key):
        return len((specifications or {}).get(key, {}).get("match", {}))
    winner = max(eligible, key=lambda key: rank(metrics[key], complexity=complexity(key)), default=None)
    return winner, metrics


def replay(rows, parent, prepared, spec):
    return [prototype_decision(row, parent, item, spec) for row, item in zip(rows, prepared, strict=True)]


def _checked_output(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root / "tmp") or output == root / "tmp":
        raise ValueError("research_output_must_be_workspace_tmp_child")
    if (output / "result.json").exists() or (output / "frozen-candidates.json").exists():
        raise ValueError("research_output_already_frozen")
    return root, output


def run(workspace, output, *, extend_setup=False):
    root, output = _checked_output(workspace, output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    source = root / "tmp/deep-retained-policy-research-20261003/native-snapshots.json"
    reference_path = root / "tmp/main-machine-auxiliary-source-remediation-20261003/after-machine.json"
    winrate_source = root / "data/report/ai_decision_action_outcome_calibration/winrate_policy_2026-10-02.json"
    manifests = {str(path): prior.file_sha(path) for path in (source, reference_path, winrate_source)}
    native = json.loads(source.read_text())
    if not C.valid(native):
        raise ValueError("native_snapshot_hash_invalid")
    reference = json.loads(reference_path.read_text())
    parent = prior.runtime_policy.for_cohort(prior.runtime_policy.load_effective(
        data_root=root / "data", target_date=prior.DAYS[-1]), ("KRX", "KRX_REGULAR"))["machine_policy"]
    if S.digest(parent) != native["parent_sha256"] or S.digest(parent) != reference["incumbent_machine_policy_sha256"]:
        raise ValueError("frozen_parent_mismatch")
    rows = deepcopy(native["rows"])
    prepared = [prepare(row, parent) for row in rows]
    for row, item in zip(rows, prepared, strict=True):
        if (row["source_date"] not in prior.DAYS or (row["effective_venue"], row["session_bucket"]) != ("KRX", "KRX_REGULAR")
                or prior.calibration._machine_path_value(row)[1]):
            raise ValueError("native_scope_or_cost_path_invalid")
        row["comparison"] = {**row.get("comparison", {}),
            "incumbent_machine_action": item["decision"]["action"], "incumbent_machine_reason": item["decision"]["reason"]}
    split = reference["split_manifest"]
    train_ids = {tuple(key) for key in split["train_opportunity_ids"]}
    held_ids = {tuple(key) for key in split["holdout_opportunity_ids"]}
    if train_ids & held_ids:
        raise ValueError("opportunity_split_overlap")
    ti = [i for i, row in enumerate(rows) if prior.opportunity_identity(row) in train_ids]
    hi = [i for i, row in enumerate(rows) if prior.opportunity_identity(row) in held_ids]
    if (len(rows), len(ti), len(hi)) != (99, 71, 28) or len(set(ti + hi)) != len(rows):
        raise ValueError("native_split_population_changed")
    training, held = [rows[i] for i in ti], [rows[i] for i in hi]
    train_prepared, held_prepared = [prepared[i] for i in ti], [prepared[i] for i in hi]
    specs = definitions(train_prepared, extend_setup=extend_setup)
    specification_index = {spec["id"]: spec for spec in specs}
    kernels = {str(Path(module.__file__).resolve()): prior.file_sha(module.__file__)
               for module in (prior, C, S, E, prior.calibration, prior.runtime_policy)}
    kernels[str(Path(__file__).resolve())] = prior.file_sha(__file__)
    frozen = dict(schema="offline_confirmation_search_v1", source_manifest=manifests,
        kernel_manifest=kernels, parent_policy=parent, parent_sha256=S.digest(parent),
        split_manifest=split, train_count=len(training), held_count=len(held), candidates=specs,
        definition_basis="training_predecision_types_only", selection_basis=S.RECOVERY_SELECTION_VERSION,
        same_held_dates_used_in_prior_research=True, extend_setup_confirmation=extend_setup,
        extension_basis="posthoc_after_run_01" if extend_setup else None)
    write(output / "frozen-candidates.json", frozen)
    (output / "reviewed-source.py").write_bytes(Path(__file__).read_bytes())
    search_hash = prior.file_sha(output / "frozen-candidates.json")
    train_decisions = {spec["id"]: replay(training, parent, train_prepared, spec) for spec in specs}
    train_vectors = {key: [d["action"] for d in values] for key, values in train_decisions.items()}
    winner, metrics = choose(training, train_vectors, specifications=specification_index)
    write(output / "frozen-selection.json", dict(winner=winner, train_search_sha256=search_hash,
        candidate_metrics=metrics, holdout_used_for_selection=False))
    # Only now open held actions. All trials are diagnostic; no reselection.
    held_decisions = {spec["id"]: replay(held, parent, held_prepared, spec) for spec in specs}
    held_vectors = {key: [d["action"] for d in values] for key, values in held_decisions.items()}
    trials, changed = [], []
    for spec in specs:
        key = spec["id"]
        prototype_policy = {**deepcopy(parent), "research_confirmation_overlay": spec}
        gate = prior.publisher_diagnostic(training, train_vectors[key], held, held_vectors[key],
            prototype_policy, parent, reference, search_hash)
        trials.append(dict(id=key, specification=spec, train=metrics[key], holdout=prior.economy(held, held_vectors[key]),
            existing_gate_errors=gate["existing_gate_errors"], selected=key == winner))
        if key == winner:
            write(output / "selected-candidate.json", dict(candidate=gate["candidate"],
                existing_gate_errors=gate["existing_gate_errors"],
                replay_kernel="parent_strategy_then_scalar_group_with_explicit_offline_recipe_then_parent_veto"))
            for part, group, actions, decisions in (("train", training, train_vectors[key], train_decisions[key]),
                                                   ("holdout", held, held_vectors[key], held_decisions[key])):
                for row, action, decision in zip(group, actions, decisions, strict=True):
                    if action == row["comparison"]["incumbent_machine_action"]:
                        continue
                    changed.append(dict(split=part, day=row["source_date"], symbol=row["stock_code"],
                        decision_trace_id=row["decision_trace_id"], opportunity=list(prior.opportunity_identity(row)),
                        from_action=row["comparison"]["incumbent_machine_action"], to_action=action,
                        prior_reason=row["comparison"]["incumbent_machine_reason"],
                        first_hit=row["entry_quality_path"]["first_hit"], net_path_pct=prior.calibration._machine_path_value(row)[0],
                        prototype_decision=decision))
    # Remove each training symbol, regenerate its definitions, and reselect.
    sensitivity = []
    for symbol in sorted({row["stock_code"] for row in training}):
        indices = [i for i, row in enumerate(training) if row["stock_code"] != symbol]
        subset = [training[i] for i in indices]
        allowed = {spec["id"] for spec in definitions([train_prepared[i] for i in indices], extend_setup=extend_setup)}
        picked, submetrics = choose(subset, {key: [actions[i] for i in indices]
            for key, actions in train_vectors.items() if key in allowed}, specifications=specification_index)
        sensitivity.append(dict(removed_symbol=symbol, selected=picked, same_candidate=picked == winner,
            train=submetrics.get(picked), holdout=prior.economy(held, held_vectors[picked]) if picked else None))
    # Earlier chronological fold; definition and selection use only 9/29.
    early_i = [i for i, row in enumerate(training) if row["source_date"] == prior.DAYS[0]]
    later_i = [i for i, row in enumerate(training) if row["source_date"] == prior.DAYS[1]]
    early = [training[i] for i in early_i]
    allowed = {spec["id"] for spec in definitions([train_prepared[i] for i in early_i], extend_setup=extend_setup)}
    early_winner, early_metrics = choose(early, {key: [actions[i] for i in early_i]
        for key, actions in train_vectors.items() if key in allowed}, specifications=specification_index)
    chronological = dict(train_day=prior.DAYS[0], diagnostic_day=prior.DAYS[1], selected=early_winner,
        train=early_metrics.get(early_winner), holdout=prior.economy([training[i] for i in later_i],
            [train_vectors[early_winner][i] for i in later_i]) if early_winner else None)
    # Official registered veto report over exactly this native subset; coverage
    # is not represented as the full source census.
    receipt = json.loads(winrate_source.read_text())["source_receipt"]
    registered = prior.calibration.build_winrate_policy_report(rows, source_receipt=receipt,
        target_date="2026-10-02", publication_day="2026-10-03", data_root=root / "data")
    if registered["parent_machine_policy_sha256"] != S.digest(parent):
        raise ValueError("registered_report_parent_changed")
    C.write(output / "registered-vwap-report.json", registered)
    nonentry_diagnostics = []
    for row, item in zip(rows, prepared, strict=True):
        if item["decision"]["action"] == "ENTER_NOW":
            continue
        setup = item["rebuilt"]
        core = E.mechanistic_entry_action_core(setup, policy=item["effective"])
        nonentry_diagnostics.append(dict(day=row["source_date"], symbol=row["stock_code"],
            decision_trace_id=row["decision_trace_id"], parent_action=item["decision"]["action"],
            parent_reason=item["decision"]["reason"], first_hit=row["entry_quality_path"]["first_hit"],
            micro=setup.get("micro_recovery_observation"),
            local_breakout=setup.get("local_breakout"),
            flow_families=(setup.get("mechanistic_context", {}).get("flow") or {}).get("matched_families"),
            unresolved_risks=[risk for risk in core["risk_assessments"] if risk["disposition"] != "COMPENSATED"]))
    write(output / "nonentry-fact-diagnostics.json", dict(rows=nonentry_diagnostics,
        reason_counts=dict(Counter(row["parent_reason"] for row in nonentry_diagnostics))))
    for path, sha in {**manifests, **kernels}.items():
        if prior.file_sha(path) != sha:
            raise ValueError("research_input_or_code_changed:" + path)
    result = dict(schema="offline_confirmation_result_v1", parent_sha256=S.digest(parent),
        source_manifest=manifests, kernel_manifest=kernels, train_search_sha256=search_hash,
        trials=trials, selected=winner, changed=changed, sensitivity=sensitivity, chronological=chronological,
        baseline={part: prior.economy(group, [row["comparison"]["incumbent_machine_action"] for row in group])
                  for part, group in (("train", training), ("holdout", held))},
        candidate_count=len(specs), unique_training_vectors=len({tuple(actions) for actions in train_vectors.values()}),
        eligible_training_candidate_count=sum(prior.research_qualified(metric) for metric in metrics.values()),
        gate_error_counts=dict(Counter(error for trial in trials for error in trial["existing_gate_errors"])),
        registered_report_disposition=registered["disposition"], elapsed_seconds=time.monotonic() - started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(output / "result.json", result)
    return dict(candidate_count=len(specs), selected=winner, changed=len(changed),
                elapsed_seconds=result["elapsed_seconds"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extend-setup-confirmation", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.output, extend_setup=args.extend_setup_confirmation), sort_keys=True))
