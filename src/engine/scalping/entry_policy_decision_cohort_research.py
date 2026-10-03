"""Offline, same-parent cohort research over retained machine observations.

No runtime imports this producer. Its unregistered rules cannot be published.
Native opportunity metrics and observation diagnostics have separate units.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from copy import deepcopy
import math
from pathlib import Path
import resource
from statistics import fmean
import time

from src.engine.scalping import entry_policy_confirmation_research as R
from src.engine.scalping import partitioned_pattern_research as B

P, C, S, E = R.prior, R.C, R.S, R.E
AUTHORITY = {**R.AUTHORITY, "policy_publication_forbidden": True,
    "decision_authority": "offline_only", "synthetic_native_identity": False,
    "primary_decision_metric": "native_cost_bound_target_first",
    "window_policy": "frozen_20260929_20261002",
    "sample_floor": "existing_publisher_support_not_relaxed",
    "source_quality_gate": "exact_parent_raw_hash_scope_identity_and_cost",
    "forbidden_uses": ["live_policy", "orders", "realized_profit", "auxiliary_verdict"]}
RAW_HASHES = {
    "2026-09-29": "21b18ef6624d20e7f7d1037c34359d621a0da78ebe5f7dec760b656a37a2cdd8",
    "2026-09-30": "e6b42618ed06a3243b0eb7014d55f0037883b21dec9b6a38c334959eb1407671",
    "2026-10-02": "7710378fd205bf394d4a090d441a9cb212406781ed405929f2896b6418ba343d",
}
SOURCE_ERRORS = {"strategy_raw_input_missing", "strategy_raw_input_hash_invalid",
    "strategy_tape_score_source_missing", "strategy_momentum_score_source_missing",
    "strategy_source_scope_conflict", "strategy_source_scope_mismatch",
    "strategy_completed_bar_source_missing", "strategy_bar_clock_invalid",
    "strategy_bar_source_from_future", "strategy_future_or_forming_bar",
    "strategy_completed_bar_ohlcv_or_session_invalid", "strategy_completed_bar_coverage_invalid",
    "strategy_local_bar_clock_missing", "strategy_local_bar_clock_invalid",
    "strategy_local_bar_future_or_invalid", "strategy_local_bar_ohlcv_invalid",
    "strategy_local_bar_contract_missing", "strategy_local_bar_sequence_missing",
    "strategy_local_bar_tail_truncated", "entry_situation_raw_capture_invalid",
    "entry_situation_scope_capture_conflict"}
NUMERICS = ("net_aggressive_delta_10t", "price_change_10t_pct", "buy_pressure_10t",
    "curr_vs_micro_vwap_bp", "volume_ratio_pct", "tick_acceleration_ratio",
    "spread_bp", "fillability_score")
TYPES = ("family", "phase", "liquidity_band", "volatility_band", "price_tick_band")


def write(path, body):
    C.write(path, C.sealed({**body, **AUTHORITY}))


def fast_prepare(row, parent):
    """Reuse the exact setup/selector returned by the strategy decision kernel."""
    decision = E.mechanistic_entry_policy_decision(row["setup_evidence"], policy=parent)
    if "effective_setup_evidence" not in decision:
        return R.prepare(row, parent)
    receipt = decision["strategy_selection"]
    effective = S.legacy_projection(parent)
    effective["thresholds"].update({k: receipt["effective_thresholds"][k] for k in effective["thresholds"]})
    return dict(decision=decision, rebuilt=decision["effective_setup_evidence"],
                effective=effective, receipt=receipt)


def guard_summary(prepared, *, provenance=True):
    decision, setup = prepared["decision"], prepared["rebuilt"]
    risks = [r for r in decision["core_comparison"]["risk_assessments"] if r["disposition"] != "COMPENSATED"]
    blockers = []
    source_invalid = not provenance or any(r["risk_code"] == "SOURCE_QUALITY_GAP" for r in risks)
    if not provenance:
        blockers.append("raw_provenance_unverified")
    if source_invalid:
        blockers.append("source_quality_gap")
    if decision.get("liquidity_inputs_complete") is not True:
        blockers.append("liquidity_inputs_missing")
    elif decision.get("liquidity_threshold_pass") is not True:
        blockers.append("liquidity_threshold")
    if (setup.get("local_breakout") or {}).get("recheck_required") is True:
        blockers.append("local_breakout")
    if prepared["receipt"]["effective_thresholds"]["micro_confirmation_recipe"] != 0:
        blockers.append("parent_micro_recipe")
    for risk in risks:
        if not (risk["disposition"] == "RECHECKABLE" and risk["risk_code"] == "CONFIRMATION_MISSING"
                and risk["fact_id"] in R.SOFT_SETUP_FACTS):
            blockers.append("risk:" + risk["risk_code"] + ":" + risk["fact_id"])
    micro = setup.get("micro_recovery_observation") or {}
    thresholds = decision["applied_thresholds"]
    price, delta = E._number(micro.get("price_change_10t_pct")), E._number(micro.get("net_aggressive_delta_10t"))
    confirmation_inputs = bool(micro.get("source_usable") is True and price is not None and delta is not None
        and price > thresholds["minimum_micro_price_change_10t_pct"]
        and delta >= thresholds["minimum_micro_net_aggressive_delta_10t"])
    if source_invalid:
        cohort = "source_invalid"
    elif decision["action"] == "ENTER_NOW":
        cohort = "parent_enter"
    elif decision["action"] == "RECHECK" and decision["reason"] in R.ALLOWED_REASONS and not blockers:
        cohort = "soft_confirmation_only"
    else:
        cohort = "other_guard_or_wait"
    return dict(cohort=cohort, blockers=blockers, unresolved_risks=risks,
        confirmation_inputs_pass=confirmation_inputs, micro_source_usable=micro.get("source_usable") is True,
        price_response_pct=price, aggressive_delta=delta)


def outcome_diagnosis(row):
    """Explain exclusions without changing the production path estimand."""
    value, reason = P.calibration._machine_path_value(row)
    path = row.get("entry_quality_path") or {}
    comparison = row.get("comparison") or {}
    cost = P.calibration._full_entry_cost_pct(comparison.get("entry_cost_contract"), source_date=row["source_date"])
    if reason in {"full_cost_scope_mismatch", "full_cost_missing_or_mismatched"}:
        detail = reason
    elif not path or path.get("schema") != "entry_quality_path_v1":
        detail = "path_missing_or_schema_invalid"
    elif E._number(path.get("conservative_execution_cost_pct")) is None or cost is None or not math.isclose(
            path["conservative_execution_cost_pct"], cost, abs_tol=1e-9, rel_tol=0):
        detail = "path_cost_missing_or_mismatched"
    elif reason is None:
        detail = "eligible_target_first" if value > 0 else "eligible_stop_first"
    elif path.get("cadence_complete") is not True:
        detail = "path_cadence_gap"
    elif path.get("first_hit") == "same_bar_ambiguous":
        detail = "same_bar_ambiguous"
    elif path.get("first_hit") in {"neither", "neither_hit"}:
        detail = "neither_boundary_hit"
    elif (path.get("first_hit") == "exact_stop_first"
          and E._number(path.get("time_to_exact_stop_sec")) is not None
          and E._number(path.get("primary_window_sec")) is not None
          and path["time_to_exact_stop_sec"] > path["primary_window_sec"]):
        detail = "late_stop_contract_censored"
    else:
        detail = "quality_contract_excluded:" + str(path.get("label_reason") or path.get("first_hit") or "unknown")
    return dict(value=value, exclusion=reason, diagnosis=detail, full_cost_pct=cost,
        quality_contract_valid=row.get("entry_quality_contract_valid") is True,
        first_hit=path.get("first_hit"), path_status=path.get("status"), label_reason=path.get("label_reason"),
        target_delay_sec=path.get("time_to_net_target_sec"), stop_delay_sec=path.get("time_to_exact_stop_sec"))


def confirmation_spec(family):
    spec = dict(flow_family=family, recipe="family_setup_confirmation",
                match=dict(venue="KRX", session_bucket="KRX_REGULAR"))
    return {**spec, "id": S.digest(spec)[:16]}


def confirming_families(raw, parent, prepared, guard):
    """Prune only necessary conditions, then invoke the existing adapter."""
    decision = prepared["decision"]
    if (guard["cohort"] == "source_invalid" or decision["action"] != "RECHECK"
        or decision["reason"] not in R.ALLOWED_REASONS or not guard["confirmation_inputs_pass"]):
        return []
    context = prepared["rebuilt"].get("mechanistic_context") or {}
    families = []
    for family in sorted(set((context.get("flow") or {}).get("matched_families") or [])):
        if family not in E.MECHANISTIC_FLOW_FAMILIES:
            raise ValueError("unknown_flow_family")
        result = R.prototype_decision(raw, parent, prepared, confirmation_spec(family))
        if result["action"] == "ENTER_NOW":
            if guard["cohort"] != "soft_confirmation_only":
                raise ValueError("confirmation_changed_nonsoft_guard")
            families.append(family)
    return families


def metric_row(raw, prepared):
    keys = ("source_date", "stock_code", "decision_ts", "decision_trace_id", "effective_venue", "session_bucket",
            "scanner_promotion_id", "watch_origin", "watch_admission_id", "watch_generation_id")
    result = {key: raw.get(key) for key in keys}
    result["comparison"] = dict(incumbent_machine_action=prepared["decision"]["action"],
        incumbent_machine_reason=prepared["decision"]["reason"],
        conservative_execution_cost_pct=(raw.get("comparison") or {}).get("conservative_execution_cost_pct"))
    # Literal grouping-only projection. Never used to rebuild a decision.
    result["setup_evidence"] = dict(mechanistic_context=dict(group=dict(key_parts=deepcopy(
        ((prepared["rebuilt"].get("mechanistic_context") or {}).get("group") or {}).get("key_parts") or {}))))
    return result


def predecision_features(prepared):
    values, _ = B.D.features({"setup_evidence": prepared["rebuilt"]})
    captured = (prepared["rebuilt"].get("strategy_raw_input") or {}).get("features") or {}
    if not (captured.get("micro_vwap_available") is True and captured.get("minute_candle_window_fresh") is True):
        values["curr_vs_micro_vwap_bp"] = None
    return values


def kernel_manifest():
    return {str(Path(m.__file__).resolve()): P.file_sha(m.__file__) for m in (R, P, C, S, E, B, B.D, P.calibration)} | {
        str(Path(__file__).resolve()): P.file_sha(__file__)}


def prepare_source(root, output):
    root, output = R._checked_output(root, output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("research_output_not_empty")
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    source = root / "tmp/partitioned-pattern-deep-research-20261003/source/projection.json"
    parent_path = root / "tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json"
    projected = B.checked(source)
    parent = B.checked(parent_path)["parent_policy"]
    indexed = {r["trace"]: r for r in projected["rows"]}
    if len(indexed) != len(projected["rows"]) or len(indexed) != 7069:
        raise ValueError("frozen_population_changed")
    manifests = {str(p): P.file_sha(p) for p in (source, parent_path)}
    kernels = kernel_manifest()
    write(output / "input-manifest.json", dict(sources=manifests, kernels=kernels,
        expected_raw=RAW_HASHES, parent_sha256=S.digest(parent), population=7069))
    (output / "reviewed-research-code.py").write_bytes(Path(__file__).read_bytes())
    rows, seen = [], set()
    for day, expected in RAW_HASHES.items():
        path = root / f"data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json"
        if P.file_sha(path) != expected:
            raise ValueError("frozen_raw_hash_changed:" + day)
        manifests[str(path)] = expected
        for raw in P.stream_array(path):
            trace = raw.get("decision_trace_id")
            if trace not in indexed:
                continue
            if trace in seen:
                raise ValueError("duplicate_native_trace")
            projection = indexed[trace]
            identity = B.bind_identity(raw, projection)
            if identity != projection["identity"] or raw["source_date"] != day:
                raise ValueError("frozen_identity_changed")
            seen.add(trace)
            row = {k: deepcopy(projection[k]) for k in ("trace", "day", "symbol", "ts", "bundle", "route", "identity", "gross", "cost")}
            row["outcome"] = outcome_diagnosis(raw)
            row["recorded_action"] = raw.get("machine_action")
            try:
                prepared = fast_prepare(raw, parent)
            except ValueError as exc:
                if str(exc) not in SOURCE_ERRORS:
                    raise
                row.update(parent_action=None, parent_reason=str(exc), metric=None, types={}, features={},
                    families=[], confirming_families=[], guard=dict(cohort="source_invalid", blockers=[str(exc)]))
            else:
                provenance = raw.get("source_provenance_verified") is True and raw.get("machine_observation_hash_verified") is True
                guard = guard_summary(prepared, provenance=provenance)
                context = prepared["rebuilt"].get("mechanistic_context") or {}
                row.update(parent_action=prepared["decision"]["action"], parent_reason=prepared["decision"]["reason"],
                    metric=metric_row(raw, prepared), types=P.tags({"setup_evidence": prepared["rebuilt"]}),
                    features=predecision_features(prepared),
                    families=(context.get("flow") or {}).get("matched_families") or [], guard=guard,
                    confirming_families=confirming_families(raw, parent, prepared, guard))
                if identity["native"] and list(P.opportunity_identity(row["metric"])) != identity["native"]:
                    raise ValueError("metric_native_identity_changed")
            rows.append(row)
            if len(rows) % 250 == 0:
                print(f"prepared={len(rows)}/7069 elapsed_sec={time.monotonic()-started:.1f}", flush=True)
        if P.file_sha(path) != expected:
            raise ValueError("raw_changed_during_replay")
    if seen != set(indexed) or kernel_manifest() != kernels:
        raise ValueError("population_or_kernel_changed_during_replay")
    if any(P.file_sha(p) != sha for p, sha in manifests.items()):
        raise ValueError("input_changed_during_replay")
    rows.sort(key=lambda r: (r["day"], r["symbol"], r["ts"], r["trace"]))
    write(output / "projection.json", dict(rows=rows, source_manifest=manifests, kernel_manifest=kernels,
        parent_sha256=S.digest(parent), elapsed_sec=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(f"source_complete rows={len(rows)} elapsed_sec={time.monotonic()-started:.1f}", flush=True)


def native_metric(rows, actions):
    supported = [(r, a) for r, a in zip(rows, actions, strict=True)
                 if r["identity"]["native"] and r["metric"] is not None and r["guard"]["cohort"] != "source_invalid"]
    return P.calibration._machine_admission_metrics([r["metric"] for r, _ in supported], [a for _, a in supported],
        prepared_paths=[(r["outcome"]["value"], r["outcome"]["exclusion"]) for r, _ in supported], recovery=True)


def observation_metric(rows, actions):
    chosen = [(r, a) for r, a in zip(rows, actions, strict=True) if a == "ENTER_NOW"]
    values = [r["outcome"]["value"] for r, _ in chosen
              if r["outcome"]["exclusion"] is None and r["guard"]["cohort"] != "source_invalid"]
    groups, recovered, retained, unknown_removed = defaultdict(list), defaultdict(list), [], []
    for r, a in zip(rows, actions, strict=True):
        if r["guard"]["cohort"] == "source_invalid":
            continue
        old, new = r["parent_action"] == "ENTER_NOW", a == "ENTER_NOW"
        if r["outcome"]["exclusion"]:
            if old and not new:
                unknown_removed.append(r["trace"])
            continue
        v = r["outcome"]["value"]
        if new:
            groups[r["day"], r["symbol"]].append(v)
            if not old:
                recovered[r["day"], r["symbol"]].append(v)
        if old and v > 0:
            retained.append(new)
    def grouped(group):
        metric = dict(selected_opportunity_count=len(group),
            win_rate_pct=100*fmean(fmean(v > 0 for v in values) for values in group.values()) if group else None)
        return dict(symbol_day_groups=len(group), win_rate_pct=metric["win_rate_pct"],
            support_adjusted_score_pct=S.machine_support_adjusted_win_rate(metric),
            mean_path_pct=fmean(fmean(v) for v in group.values()) if group else None)
    return dict(unit="observation_attempt_not_independent_opportunity", selected_attempts=len(chosen),
        selected_symbols=len({r["symbol"] for r, _ in chosen}), eligible_attempts=len(values),
        wins=sum(v > 0 for v in values), losses=sum(v < 0 for v in values),
        win_rate_pct=100*fmean(v > 0 for v in values) if values else None,
        selected_path_mean_pct=fmean(values) if values else None,
        source_invalid_selected_attempts=sum(r["guard"]["cohort"] == "source_invalid" for r, _ in chosen),
        equal_symbol_day_diagnostic=grouped(groups), recovered_symbol_day_diagnostic=grouped(recovered),
        existing_success_retention_rate_pct=100*fmean(retained) if retained else None,
        unevaluated_existing_entry_changes=unknown_removed,
        exclusions=dict(Counter(r["outcome"]["diagnosis"] for r, _ in chosen if r["outcome"]["exclusion"])))


def evaluation(rows, actions):
    changed = [(r, a) for r, a in zip(rows, actions, strict=True) if a != r["parent_action"]]
    return dict(native=native_metric(rows, actions), observations=observation_metric(rows, actions),
        changed_attempt_count=len(changed), changed_native_attempt_count=sum(bool(r["identity"]["native"]) for r, _ in changed),
        changed_outcomes=dict(Counter(r["outcome"]["diagnosis"] for r, _ in changed)),
        changed_traces=[r["trace"] for r, _ in changed])


def census(rows):
    return dict(attempts=len(rows), symbols=len({r["symbol"] for r in rows}),
        native_attempts=sum(bool(r["identity"]["native"]) for r in rows),
        native_groups=len({tuple(r["identity"]["native"]) for r in rows if r["identity"]["native"]}),
        cohorts=dict(Counter(r["guard"]["cohort"] for r in rows)),
        actions=dict(Counter(str(r["parent_action"]) for r in rows)),
        recorded_to_replayed=dict(Counter(str(r["recorded_action"])+"->"+str(r["parent_action"]) for r in rows)),
        outcomes=dict(Counter(r["outcome"]["diagnosis"] for r in rows)),
        cohort_outcomes={c: dict(Counter(r["outcome"]["diagnosis"] for r in rows if r["guard"]["cohort"] == c))
                        for c in sorted({r["guard"]["cohort"] for r in rows})},
        residual_blockers=dict(Counter(b for r in rows for b in r["guard"]["blockers"])),
        confirmations=dict(Counter(f for r in rows for f in r["confirming_families"])))


def repeat_signals(rows, signals, seconds):
    """Two consecutive observations of the same native/phase; no lookahead."""
    if len(rows) != len(signals):
        raise ValueError("repeat_population_mismatch")
    previous, result = {}, [False]*len(rows)
    for i in sorted(range(len(rows)), key=lambda i: (B.clock(rows[i]), rows[i]["trace"])):
        r = rows[i]
        key = r["day"], r["symbol"], r["bundle"]
        native, phase, stamp = r["identity"]["native"], r["types"].get("phase"), B.clock(r)
        old = previous.get(key)
        valid = bool(signals[i] and native and phase and r["guard"]["cohort"] == "soft_confirmation_only")
        result[i] = bool(valid and old and old[0] == native and old[1] == phase and 0 < (stamp-old[2]).total_seconds() <= seconds)
        previous[key] = (native, phase, stamp) if valid else None
    return result


def changed_ledger(rows, actions):
    entries = defaultdict(list)
    for r in rows:
        if r["identity"]["native"] and r["parent_action"] == "ENTER_NOW":
            entries[tuple(r["identity"]["native"])].append(B.clock(r))
    result = []
    for r, action in zip(rows, actions, strict=True):
        if action == r["parent_action"]:
            continue
        times = entries.get(tuple(r["identity"]["native"] or ()), [])
        now = B.clock(r)
        before = [(now-t).total_seconds() for t in times if t < now]
        after = [(t-now).total_seconds() for t in times if t > now]
        result.append(dict(trace=r["trace"], day=r["day"], symbol=r["symbol"], ts=r["ts"],
            native=r["identity"]["native"], watch_origin=r["identity"]["watch_origin"],
            old=r["parent_action"], new=action, outcome=r["outcome"], guard=r["guard"],
            earlier_parent_enter_sec=min(before) if before else None, later_parent_enter_sec=min(after) if after else None,
            actual_fill_or_holdings_proven=False,
            fixed_horizon_net_diagnostic={str(h): r["gross"].get(str(h))-r["cost"]
                if r["gross"].get(str(h)) is not None and r["cost"] is not None else None for h in (3, 5, 10)}))
    return result


def conditions(training):
    """Only predecision training types/quantiles; bounded conjunction depth=2."""
    if any(r["symbol"] == "005930" for r in training):
        raise ValueError("samsung_leak_into_non_samsung_definition")
    types, nums = [], []
    for key in TYPES:
        for value in sorted({r["types"].get(key) for r in training} - {None, "", "UNKNOWN"}):
            types.append(dict(kind="type", key=key, value=value))
    for key in NUMERICS:
        values = sorted({r["features"].get(key) for r in training
                         if E._number(r["features"].get(key)) is not None})
        if len(values) < 2:
            continue
        for boundary in sorted({values[int((len(values)-1)*q)] for q in (.25, .5, .75)}):
            for side in ("lt", "ge"):
                nums.append(dict(kind="numeric", key=key, boundary=boundary, side=side))
    choices = [[], *[[t] for t in types], *[[n] for n in nums], *[[t, n] for t in types for n in nums]]
    result = [c for c in choices if any(matches(r, c) for r in training)]
    if len(result) > 4096:
        raise ValueError("declared_search_budget_exceeded")
    return result


def matches(row, condition):
    for c in condition:
        if c["kind"] == "type":
            if row["types"].get(c["key"]) != c["value"]:
                return False
        else:
            value = E._number(row["features"].get(c["key"]))
            if value is None or (value < c["boundary"]) != (c["side"] == "lt"):
                return False
    return True


def definitions(training, mode):
    cohort = "parent_enter" if mode == "veto" else "soft_confirmation_only"
    subset = [r for r in training if r["guard"]["cohort"] == cohort]
    families = [None] if mode == "veto" else sorted({f for r in subset for f in r["families"]})
    specs = []
    for condition in conditions(subset):
        for family in families:
            spec = dict(mode=mode, condition=condition, flow_family=family)
            specs.append(dict(id=S.digest(spec)[:16], **spec))
    if len(specs) > 32768:
        raise ValueError("declared_candidate_budget_exceeded")
    return specs


def vector(rows, spec):
    actions = []
    for row in rows:
        action = row["parent_action"]
        if row["symbol"] != "005930" and matches(row, spec["condition"]):
            if spec["mode"] == "veto" and row["guard"]["cohort"] == "parent_enter":
                action = "RECHECK"
            elif (spec["mode"] == "recovery" and row["guard"]["cohort"] == "soft_confirmation_only"
                  and spec["flow_family"] in row["confirming_families"]):
                action = "ENTER_NOW"
        actions.append(action)
    return actions


def qualify(metric, baseline, mode):
    """User objective: higher policy win rate; retention/EV are diagnostics.

    Eligibility here is exploratory. Missing changed outcomes remain explicit
    and cannot satisfy a publisher's complete economic evidence requirement.
    """
    if mode == "recovery":
        return bool(metric["recovery_metrics"]["selected_opportunity_count"] > 0
            and metric["win_rate_pct"] is not None
            and (baseline["selected_opportunity_count"] == 0
                 or (baseline["win_rate_pct"] is not None and metric["win_rate_pct"] > baseline["win_rate_pct"])))
    return bool(metric["selected_opportunity_count"] >= max(1, .5*baseline["selected_opportunity_count"])
        and metric["win_rate_pct"] is not None and baseline["win_rate_pct"] is not None
        and metric["win_rate_pct"] > baseline["win_rate_pct"])


def rank(metric, mode, complexity):
    copy = {**metric, "selection_score_version": S.MACHINE_SELECTION_VERSION}
    return tuple(-1e100 if v is None else v for v in S.machine_admission_rank(copy, complexity=complexity))


def metric_brief(metric):
    keys = ("selected_opportunity_count", "selected_attempt_count", "win_rate_pct", "support_adjusted_win_rate_pct",
            "selected_path_ev_pct", "existing_success_retention_rate_pct", "paired_admission_delta_pct",
            "recovery_metrics", "selection_score_version", "unevaluated_existing_entry_changes",
            "transition_attempt_counts", "comparable_opportunity_count", "comparable_attempt_count")
    return {k: metric[k] for k in keys}


def observation_rank(metric, baseline, mode, complexity):
    """Separate exploratory ranking; symbol-days never become native IDs."""
    group = metric["equal_symbol_day_diagnostic"]
    base = baseline["equal_symbol_day_diagnostic"]
    if mode == "veto":
        eligible = (group["symbol_day_groups"] >= max(1, .5*base["symbol_day_groups"])
            and group["win_rate_pct"] is not None and base["win_rate_pct"] is not None
            and group["win_rate_pct"] > base["win_rate_pct"])
    else:
        eligible = (metric["recovered_symbol_day_diagnostic"]["symbol_day_groups"] > 0
            and group["win_rate_pct"] is not None
            and (base["symbol_day_groups"] == 0 or (
                base["win_rate_pct"] is not None and group["win_rate_pct"] > base["win_rate_pct"])))
    score = (group["support_adjusted_score_pct"], group["symbol_day_groups"], -complexity)
    return eligible, tuple(-1e100 if v is None else v for v in score)


def fit(training, mode):
    if any(r["symbol"] == "005930" for r in training):
        raise ValueError("samsung_leak_into_non_samsung_training")
    specs = definitions(training, mode)
    baseline = native_metric(training, [r["parent_action"] for r in training])
    observed_baseline = observation_metric(training, [r["parent_action"] for r in training])
    metrics, unique, winner, score = [], {}, None, None
    observed_winner, observed_score = None, None
    for spec in sorted(specs, key=lambda s: s["id"]):
        actions = vector(training, spec)
        signature = tuple(actions)
        if signature not in unique:
            unique[signature] = native_metric(training, actions), observation_metric(training, actions)
        metric, observed = unique[signature]
        # Retention, incomplete outcomes and path EV remain in the report.
        # They are not a hidden 100% retention filter on win-rate hypotheses.
        eligible = qualify(metric, baseline, mode)
        current = rank(metric, mode, len(spec["condition"]))
        metrics.append(dict(id=spec["id"], research_qualified=eligible, native=metric_brief(metric), observations=observed))
        if eligible and (score is None or current > score):
            winner, score = spec, current
        observed_eligible, observed_current = observation_rank(observed, observed_baseline, mode, len(spec["condition"]))
        if observed_eligible and (observed_score is None or observed_current > observed_score):
            observed_winner, observed_score = spec, observed_current
    best = max(metrics, key=lambda m: rank(m["native"], mode, 0), default=None)
    return dict(mode=mode, candidates=specs, candidate_metrics=metrics, selected=winner,
        diagnostic_best=best, baseline=baseline, unique_training_vectors=len(unique),
        observation_only_selected=observed_winner, observation_only_baseline=observed_baseline,
        training_symbols=sorted({r["symbol"] for r in training}),
        training_traces=[r["trace"] for r in training], holdout_used_for_selection=False)


def checked_preparation(frozen, source):
    """Reuse raw replay only when every preparation dependency is unchanged.

    This bounded allowance concerns the reviewed native selection correction.
    It cannot bless changes to raw extraction, identities, labels or decisions.
    """
    current = kernel_manifest()
    own = str(Path(__file__).resolve())
    previous = frozen["kernel_manifest"]
    def ast_contract(path, allowed, *, ignore_ast_import=False):
        tree = ast.parse(path.read_text())
        tree.body = [node for node in tree.body
                     if not (isinstance(node, ast.FunctionDef) and node.name in allowed)
                     and not (ignore_ast_import and isinstance(node, ast.Import)
                              and [n.name for n in node.names] == ["ast"])]
        return ast.dump(tree, include_attributes=False)
    if set(previous) != set(current):
        raise ValueError("prepared_dependency_changed")
    for path, old_sha in previous.items():
        if path == own or current[path] == old_sha:
            continue
        snapshot = source.parent / "reviewed-dependencies" / Path(path).name
        if (path != str(Path(P.__file__).resolve()) or not snapshot.is_file()
            or snapshot.stat().st_size > 2*1024*1024 or P.file_sha(snapshot) != old_sha):
            raise ValueError("prepared_dependency_changed")
        # The later user correction changes offline research selection only.
        # Raw streaming, source tags, costs and all production kernels stay exact.
        allowed = {"research_qualified", "auxiliary_winrate_qualified", "auxiliary_winrate_rank",
                   "chronological_feature_filter_fold", "run_feature_filter_research", "run_auxiliary_research"}
        if ast_contract(snapshot, allowed) != ast_contract(Path(path), allowed):
            raise ValueError("prepared_dependency_extraction_changed")
    snapshot = source.parent / "reviewed-research-code.py"
    if snapshot.stat().st_size > 2*1024*1024 or P.file_sha(snapshot) != previous.get(own):
        raise ValueError("preparation_code_snapshot_invalid")
    if previous.get(own) != current[own]:
        allowed = {"qualify", "rank", "observation_rank", "fit", "run", "checked_preparation"}
        if ast_contract(snapshot, allowed, ignore_ast_import=True) != ast_contract(Path(__file__), allowed, ignore_ast_import=True):
            raise ValueError("prepared_extraction_contract_changed")
    return current


def run(root, source, output):
    root, output = R._checked_output(root, output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("research_output_not_empty")
    source = Path(source).resolve()
    frozen = B.checked(source)
    # Selection follows the user's corrected objective; raw replay stays exact.
    analysis_kernels = checked_preparation(frozen, source)
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=True)
    (output / "reviewed-analysis-code.py").write_bytes(Path(__file__).read_bytes())
    source_sha = P.file_sha(source)
    rows = frozen["rows"]
    parts = {label: [r for r in rows if B.partition(r["symbol"]) == label] for label in ("samsung", "non_samsung")}
    if sum(map(len, parts.values())) != len(rows):
        raise ValueError("unknown_symbol_partition")
    summary = {k: census(v) for k, v in parts.items()}
    fixed = [r for r in parts["samsung"] if r["identity"]["watch_origin"] == "MAIN_FIXED_WATCH"]
    summary["samsung_fixed_watch"] = census(fixed)
    samsung = {}
    # Fixed candidate predates this run. Repeats are sensitivity, not a new selection.
    for name, group in (("all_samsung", parts["samsung"]), ("fixed_watch", fixed)):
        signals = ["DEPTH_SUPPORTED" in r["confirming_families"] for r in group]
        arms = {}
        for repeat in (0, 60, 120, 180, 300):
            mask = repeat_signals(group, signals, repeat) if repeat else signals
            actions = ["ENTER_NOW" if hit else r["parent_action"] for r, hit in zip(group, mask, strict=True)]
            arms[str(repeat)] = dict(total=evaluation(group, actions), changed=changed_ledger(group, actions),
                by_day={day: evaluation([r for r in group if r["day"] == day],
                    [a for r, a in zip(group, actions, strict=True) if r["day"] == day]) for day in P.DAYS})
        samsung[name] = dict(baseline=evaluation(group, [r["parent_action"] for r in group]), arms=arms)
    folds = []
    others = parts["non_samsung"]
    for train_days, held_day in ((P.DAYS[:1], P.DAYS[1]), (P.DAYS[:2], P.DAYS[2])):
        training, held = [r for r in others if r["day"] in train_days], [r for r in others if r["day"] == held_day]
        for mode in ("veto", "recovery"):
            print(f"fit mode={mode} train={train_days} held={held_day}", flush=True)
            fit_result = fit(training, mode)
            name = mode + "-through-" + train_days[-1]
            # Persist training definitions/selection before applying any held labels.
            write(output / (name + "-frozen.json"), fit_result)
            chosen = fit_result["selected"]
            held_actions = vector(held, chosen) if chosen else [r["parent_action"] for r in held]
            item = dict(mode=mode, train_days=train_days, held_day=held_day, selected=chosen,
                candidate_count=len(fit_result["candidates"]), unique_training_vectors=fit_result["unique_training_vectors"],
                train_baseline=evaluation(training, [r["parent_action"] for r in training]),
                train_selected=evaluation(training, vector(training, chosen)) if chosen else None,
                held_baseline=evaluation(held, [r["parent_action"] for r in held]),
                held_selected=evaluation(held, held_actions) if chosen else None,
                changed_held=changed_ledger(held, held_actions), diagnostic_best_train=fit_result["diagnostic_best"])
            observed = fit_result["observation_only_selected"]
            item["observation_only_research"] = dict(selected=observed,
                role="exploratory_symbol_day_diagnostic_not_native_support",
                training=evaluation(training, vector(training, observed)) if observed else None,
                held=evaluation(held, vector(held, observed)) if observed else None,
                changed_held=changed_ledger(held, vector(held, observed)) if observed else [])
            if chosen:
                item["leave_one_training_symbol_out_fixed_candidate"] = {
                    symbol: native_metric([r for r in training if r["symbol"] != symbol],
                        vector([r for r in training if r["symbol"] != symbol], chosen))
                    for symbol in sorted({r["symbol"] for r, a in zip(training, vector(training, chosen), strict=True)
                                          if r["parent_action"] != a and r["identity"]["native"]})}
            folds.append(item)
    if P.file_sha(source) != source_sha or analysis_kernels != kernel_manifest():
        raise ValueError("input_or_kernel_changed_during_fit")
    write(output / "result.json", dict(schema="machine_decision_cohort_research_v1", source_sha256=source_sha,
        analysis_kernel_manifest=analysis_kernels, preparation_kernel_manifest=frozen["kernel_manifest"],
        research_objective="higher_policy_target_first_win_rate_than_incumbent",
        successful_entry_retention_role="reported_tradeoff_not_candidate_exclusion",
        path_ev_role="reported_separately_not_winrate_selection_floor",
        unknown_changed_outcomes_role="excluded_from_rate_not_imputed_not_publication_proof",
        support_ranking="same_owner_support_adjusted_policy_win_rate_after_strict_rate_improvement",
        parent_sha256=frozen["parent_sha256"], census=summary, samsung=samsung, non_samsung_folds=folds,
        formal_promotion=False, reused_dates=True, elapsed_sec=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(f"research_complete elapsed_sec={time.monotonic()-started:.1f}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare_source(args.workspace, args.output)
    else:
        if not args.source:
            parser.error("run requires --source")
        run(args.workspace, args.source, args.output)


if __name__ == "__main__":
    main()
