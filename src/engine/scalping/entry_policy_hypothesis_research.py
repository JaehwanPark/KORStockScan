"""Offline hypotheses over retained Main/auxiliary sources; no live consumer.

Reuse the production decision kernels. Outputs are exploratory CF evidence,
never publisher inputs, new provider responses, fills or runtime authority.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import resource
import time

from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping import compact_auxiliary_paired_replay as compact
from src.engine.scalping import entry_setup_evidence as evidence
from src.engine.scalping import entry_strategy_policy as strategy
from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
from src.engine.scalping.postclose_entry_validation import opportunity_identity, source_identifier

SCHEMA = "retained_entry_policy_hypothesis_research_v1"
DAYS = ("2026-09-29", "2026-09-30", "2026-10-02")
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
                 actual_order_submitted=False, provider_calls=0,
                 canonical_policy_written=False, live_promotion_forbidden=True)
TEMPLATES = {
    "flow": ("trigger_buy_pressure", "tape_supportive_score", "minimum_micro_net_aggressive_delta_10t", "minimum_micro_price_change_10t_pct"),
    "liquidity": ("maximum_spread_bp", "minimum_fillability_score", "maximum_top3_ask_to_bid_ratio"),
    "structure": ("structural_positive_returns", "structural_positive_slopes", "early_volume_ratio", "volume_confirm_ratio"),
    "recovery": ("recovery_positive_windows", "recovery_tick_acceleration", "reference_reclaim_bp", "rejection_rebound_pct"),
    "breakout": ("breakout_lookback", "breakout_event_window", "breakout_failure_closes", "breakout_tolerance_ticks"),
    "pullback": ("structure_pullback_return_min", "structure_pullback_return_max", "structure_pullback_drawdown_pct", "structure_bounce_slope"),
    "volume": ("volume_absent_ratio", "volume_confirm_ratio", "short_volume_ratio", "structure_volume_confirm"),
    "extension": ("overextension_runup_pct", "overextension_vwap_bp", "overextension_ma5_bp", "late_watch_sec"),
}


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def stream_array(path, key="rows"):
    """One bounded pass through a frozen JSON array, including gzip inputs."""
    opener = gzip.open if Path(path).suffix == ".gz" else open
    decoder = json.JSONDecoder()
    with opener(path, "rt") as stream:
        buffer = ""
        pattern = re.compile(r'"' + re.escape(key) + r'"\s*:\s*\[')
        while not (match := pattern.search(buffer)):
            chunk = stream.read(262144)
            if not chunk or len(buffer) > 1048576:
                raise ValueError("research_array_header_missing_or_oversized")
            buffer += chunk
        buffer = buffer[match.end():]
        while True:
            buffer = buffer.lstrip(" ,\n\r\t")
            if buffer.startswith("]"):
                return
            try:
                row, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = stream.read(262144)
                if not chunk or len(buffer) > 32 * 1024 * 1024:
                    raise ValueError("research_array_row_invalid_or_oversized")
                buffer += chunk
                continue
            buffer = buffer[end:]
            if not isinstance(row, dict):
                raise ValueError("research_array_row_not_object")
            yield row


def tags(row):
    setup = row.get("setup_evidence") or (row.get("input") or {}).get("entry_setup_evidence_v1") or {}
    parts = ((setup.get("mechanistic_context") or {}).get("group") or {}).get("key_parts") or {}
    return {**parts, "family": setup.get("setup_family"),
            "phase": setup.get("structure_phase") or parts.get("structure_phase")}


def matches(row, condition):
    if condition is None:
        return True
    if condition["kind"] == "numeric":
        setup = row["setup_evidence"]
        value = strategy.features(setup["strategy_raw_input"], setup).get(condition["feature"])
        if value is None:
            return False
        return (value < condition["boundary"]) == (condition["side"] == "lt")
    return all(tags(row).get(k) == v for k, v in condition["match"].items())


def conditions(training, *, minimum_opportunities=5, auxiliary=False):
    """Boundaries and leaf support depend only on predecision training data."""
    result = [None]
    if not auxiliary:
        observations = defaultdict(set)
        for row in training:
            setup = row["setup_evidence"]
            for name, value in strategy.features(setup["strategy_raw_input"], setup).items():
                if value is not None:
                    observations[name].add(value)
        for name, values in sorted(observations.items()):
            values = sorted(values)
            if len(values) > 1:
                for boundary in sorted({values[len(values)//3], values[2*len(values)//3]}):
                    result.extend(dict(kind="numeric", feature=name, boundary=boundary, side=side)
                                  for side in ("lt", "ge"))
    dimensions = (("structure_phase", "liquidity_band", "volatility_band", "price_tick_band")
                  if auxiliary else ("family", "phase", "liquidity_band"))
    typed = {}
    for width in (1, 2):
        for axes in itertools.combinations(dimensions, width):
            for row in training:
                match = {axis: tags(row).get(axis) for axis in axes}
                if not all(source_identifier(v) and v != "UNKNOWN" for v in match.values()):
                    continue
                key = tuple(sorted(match.items()))
                typed.setdefault(key, set()).add(opportunity_identity(row))
    result.extend(dict(kind="type", match=dict(key)) for key, support in sorted(typed.items())
                  if len(support) >= minimum_opportunities)
    return result


def machine_profiles(parent, domains, *, maximum=240):
    base = parent if "strategy" in parent else strategy.seed(parent, ("KRX", "KRX_REGULAR"))
    inherited = strategy.default_profile(base)
    seen, result = set(), []

    def add(name, changes):
        changes = {key: value for key, value in changes.items() if value != inherited[key]}
        if not changes or len(result) >= maximum:
            return
        policy = strategy._mutate_tree(base, changes, None)
        if strategy.validate(policy["strategy"]):
            return
        sha = strategy.digest(policy)
        if sha not in seen:
            seen.add(sha)
            result.append(dict(name=name, changes=changes, policy=policy, sha256=sha))

    # Every coordinate gets its nearest lower/higher hypothesis before edges.
    for key, values in domains.items():
        below = [v for v in values if v < inherited[key]]
        above = [v for v in values if v > inherited[key]]
        for side, options in (("lower", below), ("higher", above)):
            if options:
                add("single:"+key+":"+side, {key: max(options) if side == "lower" else min(options)})
    for name, axes in TEMPLATES.items():
        for side in ("lower", "higher", "relax"):
            changes = {}
            for key in axes:
                values = domains[key]
                direction = next((d for d, names in strategy.ADMISSION_EXPANSION_DIRECTION.items() if key in names), None)
                chosen = direction if side == "relax" else side
                changes[key] = min(values) if chosen == "lower" else max(values) if chosen == "higher" else inherited[key]
            add("joint:"+name+":"+side, changes)
    for names in (("flow", "liquidity"), ("structure", "volume"), ("recovery", "flow"), ("pullback", "volume")):
        for side in ("lower", "higher", "relax"):
            axes = set(itertools.chain.from_iterable(TEMPLATES[n] for n in names))
            change = {}
            for key in sorted(axes):
                direction = next((d for d, values in strategy.ADMISSION_EXPANSION_DIRECTION.items() if key in values), None)
                chosen = direction if side == "relax" else side
                change[key] = min(domains[key]) if chosen == "lower" else max(domains[key]) if chosen == "higher" else inherited[key]
            add("joint:"+"+".join(names)+":"+side, change)
    for side in ("lower", "higher", "relax"):
        change = {}
        for key, values in domains.items():
            direction = next((d for d, names in strategy.ADMISSION_EXPANSION_DIRECTION.items() if key in names), None)
            chosen = direction if side == "relax" else side
            change[key] = min(values) if chosen == "lower" else max(values) if chosen == "higher" else inherited[key]
        add("joint:all:"+side, change)
    for key, values in domains.items():
        for value in (min(values), max(values)):
            add("edge:"+key+":"+str(value), {key: value})
    return result


def decision_vector(rows, policy):
    cache, result = {}, []
    for row in rows:
        setup = row["setup_evidence"]
        key = strategy.digest(setup)
        if key not in cache:
            cache[key] = evidence.mechanistic_entry_policy_decision(setup, policy=policy)["action"]
        result.append(cache[key])
    return result


def economy(rows, actions):
    return calibration._machine_admission_metrics(rows, actions,
        prepared_paths=[calibration._machine_path_value(row) for row in rows], recovery=True)


def machine_summary(metric):
    keys = ("selected_opportunity_count", "win_rate_pct", "support_adjusted_win_rate_pct",
            "selected_path_ev_pct", "existing_success_retention_rate_pct", "paired_admission_delta_pct",
            "historical_action_outcome_counts", "transition_attempt_counts")
    return {**{k: metric.get(k) for k in keys}, "recovery_metrics": metric["recovery_metrics"]}


def research_qualified(metric):
    recovered = metric["recovery_metrics"]
    return (recovered["selected_opportunity_count"] > 0
            and recovered["successful_opportunity_weight"] > 0)


def auxiliary_winrate_qualified(score, baseline):
    """Research eligibility, not publication: higher PASS win rate first.

    Lost successful PASSes and paired net CF remain reported tradeoffs. They
    must not silently impose a 100% retention or positive-EV selection floor.
    The existing half-exposure research floor avoids a one-row perfect winner.
    """
    return bool(score["pass_count"] >= max(1, .5 * baseline["pass_count"])
        and score["pass_win_rate_pct"] is not None and baseline["pass_win_rate_pct"] is not None
        and score["pass_win_rate_pct"] > baseline["pass_win_rate_pct"])


def auxiliary_winrate_rank(score):
    adjusted = strategy.machine_support_adjusted_win_rate(dict(
        win_rate_pct=score["pass_win_rate_pct"], selected_opportunity_count=score["pass_count"]))
    return (adjusted if adjusted is not None else -math.inf,
            score["pass_win_rate_pct"] if score["pass_win_rate_pct"] is not None else -math.inf,
            score["pass_count"])


def publisher_diagnostic(training, train_actions, held, held_actions, policy, parent, reference, search_hash):
    """Recompute existing gate; exploratory reuse still forbids live promotion."""
    def arm(rows, actions):
        transitions=Counter(r["comparison"]["incumbent_machine_action"]+"->"+new for r,new in zip(rows,actions))
        return dict(source_dates=sorted({r["source_date"] for r in rows}),
            opportunity_ids=sorted({strategy.digest(opportunity_identity(r)) for r in rows}),
            changed_opportunity_ids=sorted({strategy.digest(opportunity_identity(r)) for r,new in zip(rows,actions)
                if r["comparison"]["incumbent_machine_action"]!=new}),
            economics=economy(rows,actions),action_transition_counts=dict(transitions),train_search_sha256=search_hash)
    proof=dict(train=arm(training,train_actions),holdout=arm(held,held_actions),
        incumbent_train=arm(training,[r["comparison"]["incumbent_machine_action"] for r in training]),
        incumbent_holdout=arm(held,[r["comparison"]["incumbent_machine_action"] for r in held]),
        split_manifest=reference["split_manifest"],evaluation_contract=dict(
            selection_version=strategy.RECOVERY_SELECTION_VERSION,evaluation_basis=strategy.MACHINE_EVALUATION_BASIS,
            parent_sha256=strategy.digest(parent),scope=["KRX","KRX_REGULAR"],
            input_sha256=reference["input_sha256"],source_contract_sha256=reference["source_contract_sha256"],
            train_search_sha256=search_hash))
    candidate=dict(schema="main_entry_strategy_candidate_v2",parent_policy=parent,parent_sha256=strategy.digest(parent),
        scope=["KRX","KRX_REGULAR"],policy=policy,policy_sha256=strategy.digest(policy),evidence=proof,
        evidence_sha256=strategy.digest(proof),evaluation_basis=strategy.MACHINE_EVALUATION_BASIS,
        selection_score_version=strategy.RECOVERY_SELECTION_VERSION,selected_without_holdout=True)
    return dict(existing_gate_errors=strategy.promotion_errors(candidate,parent,("KRX","KRX_REGULAR")),
        pristine_holdout=False,live_promotion_forbidden=True,candidate=candidate)


def fixed_horizon_net(row, label, horizon, label_hash):
    """Different diagnostic estimand; never fabricate a stop or actual exit."""
    if (not label or label.get("decision_trace_id") != row.get("evaluation_key")
        or label.get("stock_code") != row.get("stock_code")
        or label.get("decision_ts") != row.get("decision_ts")
        or label.get("machine_bundle_sha256") != row.get("machine_bundle_sha256")
        or label.get("source_quality_status") != "pass"
        or horizon not in (label.get("matured_horizons_min") or [])
        or row.get("ai_stage_path", {}).get("label_report_sha256") != label_hash):
        return None
    path = (label.get("horizon_metrics") or {}).get(str(horizon)+"m") or {}
    cost = (row.get("ai_stage_path") or {}).get("conservative_execution_cost_pct")
    if (type(path.get("sample_count")) is not int or path["sample_count"] < 1
        or path.get("counterfactual_only") is not True
        or path.get("window_basis") != "post_decision_same_route"
        or path.get("window_start") != row.get("decision_ts")
        or not compact.finite(path.get("end_return_pct"))
        or not compact.finite(cost) or cost < 0
        or not all(str(path.get(observed) or "").upper() == str(row.get(native) or "").upper()
                   and bool(row.get(native)) for observed,native in
                   (("observed_venue","effective_venue"),("observed_session_bucket","session_bucket")))):
        return None
    return round(path["end_return_pct"] - cost, 10)


def auxiliary_profiles(training, prompt, *, maximum=6000):
    """Existing response soft-policy counts, risk materiality and two-axis leaves."""
    parent = dict(veto_min_independent_evidence_count=2, pass_min_positive_evidence_count=2,
        materiality_max={"LIQUIDITY_FRAGILE": 0., "ADVERSE_TAPE": 0., "REWARD_RISK_WEAK": 0.}, prompt_version=prompt)
    result, seen = [], set()

    def add(policy):
        if len(result) >= maximum or not evidence.validate_auxiliary_soft_policy(policy):
            return
        sha = compact.digest(policy)
        if sha not in seen:
            seen.add(sha)
            result.append(policy)

    for veto, positive in itertools.product((1, 2, 3), repeat=2):
        add(dict(schema="auxiliary_soft_policy_v1", veto_min_independent_evidence_count=veto,
                 pass_min_positive_evidence_count=positive))
    values = defaultdict(set)
    for row in training:
        for key, value in evidence.auxiliary_materiality_values(row["input"]["entry_setup_evidence_v1"]).items():
            if value is not None:
                values[key].add(value)
    choices = {}
    for key, maximum_bound in (("LIQUIDITY_FRAGILE",500.),("ADVERSE_TAPE",1.),("REWARD_RISK_WEAK",10.)):
        observed = sorted(values[key])
        choices[key] = sorted({0., maximum_bound} | ({observed[len(observed)//3],observed[2*len(observed)//3]} if observed else set()))
    profiles = []
    for positive in (1, 2, 3):
        profiles.append({**parent, "pass_min_positive_evidence_count": positive})
        for key, options in choices.items():
            profiles.extend({**parent, "pass_min_positive_evidence_count": positive,
                "materiality_max": {**parent["materiality_max"], key: boundary}} for boundary in options)
        for left, right in itertools.combinations(choices, 2):
            for a, b in itertools.product(choices[left], choices[right]):
                profiles.append({**parent, "pass_min_positive_evidence_count": positive,
                    "materiality_max": {**parent["materiality_max"], left:a, right:b}})
    for profile in profiles:
        add(dict(schema="auxiliary_soft_policy_v2", parent=profile, leaves=[]))
    for condition in conditions(training, auxiliary=True):
        if condition:
            for profile in profiles:
                add(dict(schema="auxiliary_soft_policy_v2", parent=parent,
                         leaves=[dict(match=condition["match"],profile=profile)]))
    return result


def auxiliary_summary(rows, verdicts, *, horizon=10):
    pairs = [(row["incumbent_verdict"], new, row["nets"][horizon])
             for row,new in zip(rows,verdicts) if row["nets"].get(horizon) is not None]
    passes = [net for _,new,net in pairs if new == "PASS"]
    old_passes = [net for old,_,net in pairs if old == "PASS"]
    return dict(comparable=len(pairs),pass_count=len(passes),
        pass_win_rate_pct=100*sum(v>0 for v in passes)/len(passes) if passes else None,
        pass_mean_cf_net_pct=sum(passes)/len(passes) if passes else None,
        baseline_mean_cf_net_pct=sum(old_passes)/len(old_passes) if old_passes else None,
        loss_pass_count=sum(v<0 for v in passes),
        successful_pass_lost=sum(old=="PASS" and new!="PASS" and net>0 for old,new,net in pairs),
        changed_count=sum(old!=new for old,new,_ in pairs),
        paired_mean_cf_delta_pct=sum((int(new=="PASS")-int(old=="PASS"))*net for old,new,net in pairs)/len(pairs) if pairs else None,
        transitions=dict(Counter(old+"->"+new for old,new,_ in pairs)))


def auxiliary_vector(rows, policy):
    result=[]
    for row in rows:
        assessment=evidence.evaluate_auxiliary_policy(row["replay_response"],
            setup_evidence=row["input"]["entry_setup_evidence_v1"],
            machine_policy=row["machine_policy"],soft_policy=policy)
        if assessment["validation_errors"]:
            raise ValueError("research_auxiliary_candidate_validation_failed")
        result.append(assessment["effective_verdict"])
    return result


def restore_native_metadata(rows, trace_path):
    wanted = {r["evaluation_key"] for r in rows}
    indexed, conflicts, digest = {}, set(), hashlib.sha256()
    opener = gzip.open if trace_path.suffix == ".gz" else open
    original = file_sha(trace_path)
    identity = ("stock_code","decision_ts","payload_sha256","machine_bundle_sha256","effective_venue","session_bucket")
    metadata = ("watch_origin","watch_admission_id","watch_generation_id")
    total = 0
    with opener(trace_path,"rb") as stream:
        for line in stream:
            total += len(line)
            if total > 64*1024*1024:
                raise ValueError("research_trace_budget_exceeded")
            digest.update(line)
            if not line.strip():
                continue
            trace = json.loads(line)
            key = trace.get("decision_trace_id")
            if key not in wanted:
                continue
            value = {k:trace.get(k) for k in (*identity,*metadata)}
            if key in indexed and indexed[key] != value:
                conflicts.add(key)
            indexed[key]=value
    assert file_sha(trace_path) == original, "research_trace_generation_changed"
    repaired = 0
    for row in rows:
        key=row["evaluation_key"]; native=indexed.get(key) or {}
        if (not source_identifier(key) or key in conflicts
            or not all(compact.sha256_hex(row.get(k)) for k in ("payload_sha256","machine_bundle_sha256"))
            or not all(source_identifier(native.get(k)) for k in metadata)
            or not all(row.get(k)==native.get(k) for k in identity[:4])
            or not all(str(row.get(k) or "").upper()==str(native.get(k) or "").upper() for k in identity[4:])
            or any(source_identifier(row.get(k)) and row[k]!=native[k] for k in metadata)):
            continue
        if not all(row.get(k)==native[k] for k in metadata):
            row.update({k:native[k] for k in metadata});repaired += 1
    return dict(file_sha256=original,decoded_sha256=digest.hexdigest(),repaired_rows=repaired,conflicts=len(conflicts))


def auxiliary_observation(row):
    setup=row["input"]["entry_setup_evidence_v1"]
    raw=row["replay_response"]
    materiality=evidence.auxiliary_materiality_values(setup)
    micro=setup.get("micro_recovery_observation") or {}
    tail=(setup.get("tail_risk_assessment") or {}).get("inputs") or {}
    values={"support_count":len(set(raw.get("supporting_fact_ids") or [])),
            "adverse_count":len(set(raw.get("contradicting_fact_ids") or [])),
            "confidence":raw.get("confidence") if compact.finite(raw.get("confidence")) else None}
    values.update({"materiality:"+k:v for k,v in materiality.items()})
    values.update({"tail:"+k:v if compact.finite(v) else None for k,v in tail.items()
                   if k in {"spread_bp","fillability_score","top3_ask_to_bid_ratio"}})
    values.update({"micro:"+k:micro.get(k) if micro.get("source_usable") is True else None
                   for k in ("price_change_10t_pct","net_aggressive_delta_10t")})
    return {k:row.get(k) for k in ("source_date","stock_code","decision_ts","incumbent_verdict")} | dict(
        nets={str(k):v for k,v in row["nets"].items()},
        opportunity=list(opportunity_identity(row)),generation=[str(row["effective_venue"]).upper(),
        str(row["session_bucket"]).upper(),compact.digest(row["machine_policy"]),row["incumbent_prompt_version"],
        compact.digest(row.get("parent_auxiliary_soft_policy"))],features=values,type_parts=tags(row))


def feature_filter_matches(row, condition):
    if condition["kind"]=="and":
        return all(feature_filter_matches(row,item) for item in condition["parts"])
    if condition["kind"]=="type":
        return all(row["type_parts"].get(k)==v for k,v in condition["match"].items())
    value=row["features"].get(condition["feature"])
    return (compact.finite(value) and ((value<condition["boundary"])==(condition["side"]=="lt")))


def feature_filter_conditions(training, *, maximum=1000, minimum_opportunities=5):
    """Post-PASS research hypotheses; no new binding risk or provider answer."""
    result=[]; numeric=defaultdict(set); typed={}
    for row in training:
        for name,value in row["features"].items():
            if compact.finite(value):numeric[name].add(value)
        for name in ("structure_phase","liquidity_band","volatility_band","price_tick_band"):
            value=row["type_parts"].get(name)
            if source_identifier(value) and value!="UNKNOWN":typed[(name,value)]=True
    candidates=[]
    for name,values in sorted(numeric.items()):
        values=sorted(values)
        boundaries={values[len(values)//3],values[2*len(values)//3]} if len(values)>1 else set()
        if name=="support_count":boundaries|={3,4,5,6}
        for boundary in sorted(boundaries):
            candidates.extend(dict(kind="numeric",feature=name,boundary=boundary,side=side) for side in ("lt","ge"))
    candidates.extend(dict(kind="type",match={name:value}) for name,value in sorted(typed))
    def supported(condition):
        return len({tuple(row["opportunity"]) for row in training if feature_filter_matches(row,condition)})>=minimum_opportunities
    result=[item for item in candidates if supported(item)][:maximum]
    singles=list(result)
    for left,right in itertools.combinations(singles,2):
        if len(result)>=maximum:break
        condition=dict(kind="and",parts=[left,right])
        if supported(condition):result.append(condition)
        if len(result)>=maximum:break
    return result


def chronological_feature_filter_fold(rows, training_day, evaluation_day):
    training=[r for r in rows if r["source_date"]==training_day]
    held=[r for r in rows if r["source_date"]==evaluation_day]
    hypotheses=feature_filter_conditions(training)
    baseline=auxiliary_summary(training,[r["incumbent_verdict"] for r in training])
    trials=[]
    for condition in hypotheses:
        vector=["CAUTION" if r["incumbent_verdict"]=="PASS" and feature_filter_matches(r,condition) else r["incumbent_verdict"] for r in training]
        score=auxiliary_summary(training,vector)
        if auxiliary_winrate_qualified(score, baseline):
            trials.append(dict(condition=condition,train=score))
    selected=max(trials,key=lambda t:auxiliary_winrate_rank(t["train"]),default=None)
    if selected:
        vector=["CAUTION" if r["incumbent_verdict"]=="PASS" and feature_filter_matches(r,selected["condition"]) else r["incumbent_verdict"] for r in held]
        selected["diagnostic_later_day"]=auxiliary_summary(held,vector)
    return dict(training_day=training_day,evaluation_day=evaluation_day,hypotheses=len(hypotheses),selected=selected,
                training_rows=len(training),evaluation_rows=len(held),pristine_holdout=False)


def run_feature_filter_research(output):
    source=compact.read(output/"auxiliary-research-observations.json");assert compact.valid(source)
    grouped=defaultdict(list)
    for row in source["rows"]:
        row["nets"]={int(k):v for k,v in row["nets"].items()}
        grouped[tuple(row["generation"])].append(row)
    results=[]
    for generation,rows in sorted(grouped.items()):
        training=[r for r in rows if r["source_date"]<DAYS[-1]];held=[r for r in rows if r["source_date"]==DAYS[-1]]
        if not training:continue
        hypotheses=feature_filter_conditions(training)
        compact.write(output/("frozen-ai-feature-filters-"+compact.digest(generation)+".json"),compact.sealed(dict(hypotheses=hypotheses,**AUTHORITY)))
        trials=[]
        for condition in hypotheses:
            vector=["CAUTION" if r["incumbent_verdict"]=="PASS" and feature_filter_matches(r,condition) else r["incumbent_verdict"] for r in training]
            score=auxiliary_summary(training,vector)
            trials.append(dict(condition=condition,train=score,vector_sha256=compact.digest(vector)))
        baseline=auxiliary_summary(training,[r["incumbent_verdict"] for r in training])
        selectable=[t for t in trials if auxiliary_winrate_qualified(t["train"], baseline)]
        selected=max(selectable,key=lambda t:auxiliary_winrate_rank(t["train"]),default=None)
        leader=selected or max(trials,key=lambda t:auxiliary_winrate_rank(t["train"]),default=None)
        if leader:
            condition=leader["condition"]
            vector=["CAUTION" if r["incumbent_verdict"]=="PASS" and feature_filter_matches(r,condition) else r["incumbent_verdict"] for r in held]
            train_vector=["CAUTION" if r["incumbent_verdict"]=="PASS" and feature_filter_matches(r,condition) else r["incumbent_verdict"] for r in training]
            leader["diagnostic_held"]=auxiliary_summary(held,vector)
            leader["horizons"]={str(h):dict(train=auxiliary_summary(training,train_vector,horizon=h),held=auxiliary_summary(held,vector,horizon=h)) for h in (1,3,5,10)}
            leader["leave_one_symbol_out_sensitivity"]={symbol:auxiliary_summary(
                [r for r in training if r["stock_code"]!=symbol],
                [v for r,v in zip(training,train_vector) if r["stock_code"]!=symbol]) for symbol in sorted({r["stock_code"] for r in training})}
        results.append(dict(generation=list(generation),hypotheses=len(trials),unique_vectors=len({t["vector_sha256"] for t in trials}),
            changed_hypotheses=sum(t["train"]["changed_count"]>0 for t in trials),train_baseline=baseline,
            selected_research_hypothesis=selected,diagnostic_leader=leader,promotion_pass=False,
            chronological_reselection=chronological_feature_filter_fold(rows,DAYS[0],DAYS[1]),
            representation="offline_feature_filter_not_registered_policy"))
        compact.write(output/("ai-feature-filter-trials-"+compact.digest(generation)+".json"),compact.sealed(dict(trials=trials,**AUTHORITY)))
    result=dict(results=results,hypotheses=sum(r["hypotheses"] for r in results),source_sha256=source["artifact_content_sha256"],
        metric_role="immediate_cf_only_caution_followup_unverified",pristine_holdout=False,
        selection_objective="higher_pass_win_rate_than_incumbent_support_adjusted_train_only",
        successful_pass_lost_role="reported_tradeoff_not_candidate_exclusion",**AUTHORITY)
    compact.write(output/"auxiliary-feature-filter-result.json",compact.sealed(result))
    return result


def pattern_metric(rows, mask):
    groups=defaultdict(list); nonentry_success=0
    for row,selected in zip(rows,mask):
        value,reason=calibration._machine_path_value(row)
        if not selected or reason:continue
        groups[opportunity_identity(row)].append(value>0)
        nonentry_success+=int(value>0 and row.get("machine_action")!="ENTER_NOW")
    n=len(groups);rate=100*sum(sum(v)/len(v) for v in groups.values())/n if n else None
    return dict(opportunities=n,weighted_target_first_pct=rate,
        support_adjusted_pct=strategy.machine_support_adjusted_win_rate(dict(win_rate_pct=rate,selected_opportunity_count=n)),
        nonentry_positive_attempts=nonentry_success,pattern_role="forecast_only_not_entry_authority")


def run_pattern_classifier_research(root,output):
    reference=compact.read(root/"tmp/main-machine-auxiliary-source-remediation-20261003/after-machine.json")
    excluded={r.get("attempt_id") or r.get("decision_trace_id") for r in reference["source_exclusions"]}
    rows=[]
    expected={item["path"]:item["sha256"] for item in compact.read(root/"tmp/main-machine-auxiliary-source-remediation-20261003/after-metrics.json")["input_manifest"]}
    for day in DAYS:
        path=root/"data/report/machine_observation_projection"/f"machine_observation_projection_{day}_0_0.json.gz"
        assert file_sha(path)==expected[str(path)]
        for row in stream_array(path):
            if (row.get("effective_venue"),row.get("session_bucket"))==("KRX","KRX_REGULAR") and row.get("decision_trace_id") not in excluded:
                rows.append(row)
        assert file_sha(path)==expected[str(path)]
    train_ids={tuple(k) for k in reference["split_manifest"]["train_opportunity_ids"]}
    held_ids={tuple(k) for k in reference["split_manifest"]["holdout_opportunity_ids"]}
    training=[r for r in rows if opportunity_identity(r) in train_ids];held=[r for r in rows if opportunity_identity(r) in held_ids]
    hypotheses=conditions(training)[1:]
    compact.write(output/"frozen-pattern-classifier-hypotheses.json",compact.sealed(dict(hypotheses=hypotheses,**AUTHORITY)))
    trials=[dict(condition=c,train=pattern_metric(training,[matches(r,c) for r in training])) for c in hypotheses]
    selectable=[t for t in trials if t["train"]["opportunities"]>=5]
    selected=max(selectable,key=lambda t:t["train"]["support_adjusted_pct"],default=None)
    if selected:selected["diagnostic_held"]=pattern_metric(held,[matches(r,selected["condition"]) for r in held])
    result=dict(hypotheses=len(trials),train_baseline=pattern_metric(training,[True]*len(training)),
        selected_diagnostic_pattern=selected,diagnostic_held_baseline=pattern_metric(held,[True]*len(held)),
        promotion_pass=False,pristine_holdout=False,reason="pattern_prediction_does_not_override_machine_guards",**AUTHORITY)
    compact.write(output/"pattern-classifier-result.json",compact.sealed(result))
    compact.write(output/"pattern-classifier-trials.json",compact.sealed(dict(trials=trials,**AUTHORITY)))
    return result


def run_auxiliary_research(root, output):
    # No AI calls: expand soft hypotheses and horizon labels from frozen rows.
    all_aux=[]; auxiliary_inputs=[]; latest_source=None; source_hashes={}
    for day in DAYS:
        path=root/"data/report/ai_entry_setup_paired_replay_batch"/f"compact_auxiliary_paired_economic_{day}.source.json"
        source=compact.read(path);assert compact.valid(source)
        latest_source=source
        source_hashes[day]=source["artifact_content_sha256"]
        rows=deepcopy(source["rows"])
        trace=root/"data/ai_decision_trace"/f"ai_decision_trace_{day}.jsonl"
        trace=trace if trace.exists() else Path(str(trace)+".gz")
        repair=restore_native_metadata(rows,trace)
        labels_path=root/"data/report/ai_decision_outcome_labels"/f"ai_decision_outcome_labels_{day}.json"
        labels_path=labels_path if labels_path.exists() else Path(str(labels_path)+".gz")
        label_report=compact.read(labels_path);label_hash=compact.digest(label_report)
        indexed={r.get("decision_trace_id"):r for r in label_report.get("labels",[])}
        auxiliary_inputs.append(dict(day=day,source_path=str(path),source_sha256=file_sha(path),label_path=str(labels_path),label_sha256=file_sha(labels_path),trace_path=str(trace),trace_repair=repair))
        for row in rows:
            row["nets"]={h:fixed_horizon_net(row,indexed.get(row["evaluation_key"]),h,compact.digest(indexed.get(row["evaluation_key"]) or {})) for h in (1,3,5,10)}
            row["fixed_path_cf_net_pct"]=compact.auxiliary_stage_net(row)
            all_aux.append(row)
    population=compact.sealed({**latest_source,"rows":all_aux,
        "history_projection_sha256s":{d:h for d,h in source_hashes.items() if d<DAYS[-1]},**AUTHORITY})
    replay=compact.evaluate_auxiliary_stage(population)
    compact.write(output/"auxiliary-existing-stage-replay.json",replay)
    current_report=compact.read(root/"data/report/ai_entry_setup_paired_replay_batch"/f"compact_auxiliary_paired_economic_{DAYS[-1]}.json")
    current_results=(current_report.get("auxiliary_prompt_results") or {}) if compact.valid(current_report) and current_report.get("source_projection_sha256")==source_hashes[DAYS[-1]] else {}
    prompt_results=compact.auxiliary_population_prompt_results(population,
        root/"data/report/ai_entry_setup_paired_replay_batch",current_results)
    eligible=[]; aux_excluded=Counter(); seen=set()
    for row in sorted(all_aux,key=lambda r:(r["source_date"],r["decision_ts"],r["evaluation_key"])):
        natural=row.get("natural_contract_evidence") or {}
        if natural.get("semantic_validation_status")!="pass" or natural.get("decision_quality_contract_status")!="pass":
            aux_excluded["natural_response_invalid"]+=1;continue
        if not isinstance(row.get("input"),dict) or row.get("source_label_identity_reasons"):
            aux_excluded["frozen_input_or_scope_invalid"]+=1;continue
        try:identity=opportunity_identity(row)
        except (ValueError,TypeError,KeyError):
            aux_excluded["native_opportunity_missing"]+=1;continue
        if identity in seen:aux_excluded["duplicate_opportunity"]+=1;continue
        # Reuse production deterministic citation repair, preserving raw text.
        setup=row["input"].get("entry_setup_evidence_v1") or {}
        raw=row.get("raw_response") or {}
        repaired,_=evidence.repair_mechanistic_pass_citations(raw,setup_evidence=setup)
        parent_result=evidence.evaluate_auxiliary_policy(repaired,setup_evidence=setup,machine_policy=row["machine_policy"],soft_policy=row.get("parent_auxiliary_soft_policy"))
        if parent_result["validation_errors"] or parent_result["effective_verdict"]!=row.get("incumbent_verdict"):
            aux_excluded["raw_response_or_parent_verdict_invalid"]+=1;continue
        seen.add(identity);row["replay_response"]=repaired;eligible.append(row)
    by_generation=defaultdict(list)
    for row in eligible:
        key=(str(row["effective_venue"]).upper(),str(row["session_bucket"]).upper(),
             compact.digest(row["machine_policy"]),row["incumbent_prompt_version"],compact.digest(row.get("parent_auxiliary_soft_policy")))
        by_generation[key].append(row)
    auxiliary=[]; total_policies=0
    for generation,rows in sorted(by_generation.items()):
        training=[r for r in rows if r["source_date"]<DAYS[-1]]; held=[r for r in rows if r["source_date"]==DAYS[-1]]
        if not training:
            auxiliary.append(dict(generation=list(generation),train_rows=0,held_rows=len(held),status="no_retained_training_rows"));continue
        policies=auxiliary_profiles(training,generation[3]); total_policies+=len(policies)
        compact.write(output/("frozen-auxiliary-"+compact.digest(generation)+".json"),compact.sealed(dict(generation=list(generation),policies=policies,**AUTHORITY)))
        scores=[]; verdict_cache={}
        for policy in policies:
            sha=compact.digest(policy)
            vector=auxiliary_vector(training,policy)
            verdict_cache[sha]=vector
            metrics=auxiliary_summary(training,vector)
            scores.append(dict(policy=policy,sha256=sha,train=metrics,
                all_response_changed=sum(new!=r["incumbent_verdict"] for r,new in zip(training,vector)),
                action_sha256=compact.digest(vector),veto_axis_observed=any(r["incumbent_verdict"]=="VETO" for r in training)))
        ranked=sorted(scores,key=lambda x:auxiliary_winrate_rank(x["train"]),reverse=True)
        best=ranked[0]
        held_vector=auxiliary_vector(held,best["policy"])
        best["diagnostic_held"]=auxiliary_summary(held,held_vector)
        best["horizon_sensitivity"]={str(h):dict(train=auxiliary_summary(training,verdict_cache[best["sha256"]],horizon=h),diagnostic_held=auxiliary_summary(held,held_vector,horizon=h)) for h in (1,3,5,10)}
        item=dict(generation=list(generation),train_rows=len(training),held_rows=len(held),hypotheses=len(policies),
            unique_verdict_vectors=len({s["action_sha256"] for s in scores}),changed_hypotheses=sum(s["all_response_changed"]>0 for s in scores),
            train_horizon_coverage={str(h):sum(r["nets"].get(h) is not None for r in training) for h in (1,3,5,10)},
            held_horizon_coverage={str(h):sum(r["nets"].get(h) is not None for r in held) for h in (1,3,5,10)},
            selected_diagnostic=best,promotion_pass=False,pristine_holdout=False,
            full_cost_valid_rows=sum(compact.stage_full_cost_valid(r) for r in rows))
        auxiliary.append(item)
        compact.write(output/("auxiliary-trials-"+compact.digest(generation)+".json"),compact.sealed(dict(trials=scores,**AUTHORITY)))
    aux=dict(schema=SCHEMA,screened_total=len(all_aux),valid_independent_responses=len(eligible),exclusions=dict(aux_excluded),
        raw_verdict_counts=dict(Counter(r.get("incumbent_verdict") for r in all_aux)),hypotheses=total_policies,scope_generation_results=auxiliary,
        fixed_path_comparable_count=sum(r["fixed_path_cf_net_pct"] is not None for r in eligible),
        fixed_horizon_coverage={str(h):sum(r["nets"].get(h) is not None for r in eligible) for h in (1,3,5,10)},
        existing_stage_eligible_count=replay.get("eligible_count"),
        retained_prompt_variant_responses=sum(len(items) for items in prompt_results.values()),
        prompt_rewrite_status="not_tested_without_exact_variant_responses" if not any(prompt_results.values()) else "retained_variants_require_exact_paired_review",
        source_manifest=auxiliary_inputs,**AUTHORITY)
    compact.write(output/"auxiliary-result.json",compact.sealed(aux))
    compact.write(output/"auxiliary-research-observations.json",compact.sealed(dict(rows=[auxiliary_observation(r) for r in eligible],**AUTHORITY)))
    for item in auxiliary_inputs:
        assert file_sha(item["source_path"])==item["source_sha256"]
        assert file_sha(item["label_path"])==item["label_sha256"]
    return aux


def run_research(workspace, output, *, maximum_profiles=240):
    root=Path(workspace).resolve(); output=Path(output).resolve()
    if not output.is_relative_to(root/"tmp"):
        raise ValueError("research_output_must_be_workspace_tmp")
    output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic(); code_before=file_sha(__file__)
    (output/"reviewed-machine-source.py").write_bytes(Path(__file__).read_bytes())
    kernels={str(Path(module.__file__).resolve()):file_sha(module.__file__) for module in
             (calibration,compact,evidence,strategy,runtime_policy)}
    previous=root/"tmp/main-machine-auxiliary-source-remediation-20261003"
    reference=json.loads((previous/"after-machine.json").read_text())
    expected=json.loads((previous/"after-metrics.json").read_text())["input_manifest"]
    exclusions={r.get("attempt_id") or r.get("decision_trace_id") for r in reference["source_exclusions"]}
    parent=runtime_policy.for_cohort(runtime_policy.load_effective(data_root=root/"data",target_date=DAYS[-1]),("KRX","KRX_REGULAR"))["machine_policy"]
    assert strategy.digest(parent)==reference["incumbent_machine_policy_sha256"]
    training_ids={tuple(k) for k in reference["split_manifest"]["train_opportunity_ids"]}
    held_ids={tuple(k) for k in reference["split_manifest"]["holdout_opportunity_ids"]}
    native=[]; manifests=[]; census=defaultdict(Counter)
    for item in expected:
        path=Path(item["path"]);assert file_sha(path)==item["sha256"]
        for row in stream_array(path):
            if (row.get("effective_venue"),row.get("session_bucket"))!=("KRX","KRX_REGULAR"):
                continue
            t=tags(row); path_value,path_reason=calibration._machine_path_value(row)
            for label in ("all",str(t.get("phase")),str(t.get("family"))):
                bucket=census[(str(row.get("machine_action")),label)]
                bucket["attempts"]+=1;bucket["target_first"]+=int(path_value is not None and path_value>0)
            if row.get("decision_trace_id") not in exclusions:
                decision=evidence.mechanistic_entry_policy_decision(row["setup_evidence"],policy=parent)
                row["comparison"]={**row.get("comparison",{}),"incumbent_machine_action":decision["action"],"incumbent_machine_reason":decision["reason"]}
                native.append(row)
        assert file_sha(path)==item["sha256"]
        manifests.append(dict(path=str(path),sha256=item["sha256"]))
    training=[r for r in native if opportunity_identity(r) in training_ids]
    held=[r for r in native if opportunity_identity(r) in held_ids]
    assert (len(native),len(training),len(held))==(99,71,28)
    baseline=[r["comparison"]["incumbent_machine_action"] for r in training]
    baseline_metric=economy(training,baseline)
    masks=conditions(training); profiles=machine_profiles(parent,reference["search_domain"]["domains"],maximum=maximum_profiles)
    if len(masks)*len(profiles)>16000:
        raise ValueError("research_machine_hypothesis_budget_exceeded")
    mask_vectors=[[matches(r,condition) for r in training] for condition in masks]
    definition=dict(schema=SCHEMA,source_manifest=manifests,training_dates=DAYS[:2],diagnostic_held_date=DAYS[-1],
        pristine_holdout=False,masks=masks,profiles=[{k:v for k,v in p.items() if k!="policy"} for p in profiles],
        parent_sha256=strategy.digest(parent),code_sha256=code_before,kernel_sha256s=kernels,**AUTHORITY)
    compact.write(output/"frozen-machine-hypotheses.json",compact.sealed(definition))
    trials=[]; vectors={}; failures=Counter()
    print("frozen machine",len(profiles),"profiles",len(masks),"masks",flush=True)
    for index,profile in enumerate(profiles):
        try: vector=decision_vector(training,profile["policy"])
        except (ValueError,TypeError,KeyError) as exc:
            failures[str(exc)]+=1;continue
        vectors[profile["sha256"]]=vector
        for mask_index,mask in enumerate(mask_vectors):
            actions=[new if active else old for new,active,old in zip(vector,mask,baseline)]
            metric=economy(training,actions)
            trials.append(dict(profile_sha256=profile["sha256"],profile_name=profile["name"],condition_index=mask_index,
                kind="global" if masks[mask_index] is None else masks[mask_index]["kind"],
                action_sha256=compact.digest(actions),changed_attempts=sum(a!=b for a,b in zip(actions,baseline)),
                qualified=research_qualified(metric),rank=list(strategy.machine_admission_rank(metric)),train=machine_summary(metric)))
        if index%20==0:print("machine profiles",index+1,"trials",len(trials),flush=True)
    ranked=sorted(trials,key=lambda t:tuple(-math.inf if v is None else v for v in t["rank"]),reverse=True)
    chosen=next((t for t in ranked if t["qualified"]),None)
    diagnostic=[]
    for kind in ("global","numeric","type"):
        item=next((t for t in ranked if t["kind"]==kind),None)
        if item:diagnostic.append(item)
    if chosen and chosen not in diagnostic:diagnostic.insert(0,chosen)
    by_sha={p["sha256"]:p for p in profiles}
    for trial in diagnostic:
        profile=by_sha[trial["profile_sha256"]]; condition=masks[trial["condition_index"]]
        raw_held=decision_vector(held,profile["policy"])
        actions=[new if matches(r,condition) else r["comparison"]["incumbent_machine_action"] for r,new in zip(held,raw_held)]
        trial["diagnostic_held"]=machine_summary(economy(held,actions))
        train_actions=[new if active else old for new,active,old in zip(vectors[profile["sha256"]],mask_vectors[trial["condition_index"]],baseline)]
        sensitivity={}
        for symbol in sorted({r["stock_code"] for r in training}):
            subset=[(r,a) for r,a in zip(training,train_actions) if r["stock_code"]!=symbol]
            sensitivity[symbol]=machine_summary(economy([r for r,_ in subset],[a for _,a in subset]))
        trial["leave_one_symbol_out_sensitivity"]=sensitivity
        if trial["kind"]=="numeric":
            canonical=strategy._mutate_tree(parent,profile["changes"],(condition["feature"],condition["boundary"],condition["side"]))
            assert decision_vector(training,canonical)==train_actions,"conditional_canonical_leaf_replay_mismatch"
            trial["canonical_policy"]=canonical
        elif trial["kind"]=="global":trial["canonical_policy"]=profile["policy"]
        else:trial["representation"]="offline_type_dispatch_not_registered_runtime_policy"
        if "canonical_policy" in trial:
            trial["publisher_diagnostic"]=publisher_diagnostic(training,train_actions,held,actions,
                trial["canonical_policy"],parent,reference,compact.digest(definition))
    sequence=[]
    groups=defaultdict(list)
    for row in native:groups[opportunity_identity(row)].append(row)
    for identity,rows in groups.items():
        rows.sort(key=lambda r:r["decision_ts"])
        if rows[0]["comparison"]["incumbent_machine_action"]!="ENTER_NOW":
            later=next((r for r in rows[1:] if r["comparison"]["incumbent_machine_action"]=="ENTER_NOW"),None)
            sequence.append(dict(opportunity=list(identity),attempts=len(rows),later_parent_enter=later is not None,
                elapsed_seconds=(datetime.fromisoformat(later["decision_ts"])-datetime.fromisoformat(rows[0]["decision_ts"])).total_seconds() if later else None))
    machine=dict(schema=SCHEMA,baseline=machine_summary(baseline_metric),native_rows=len(native),train_rows=len(training),held_rows=len(held),
        unique_profiles=len(profiles),hypotheses=len(trials),unique_action_vectors=len({t["action_sha256"] for t in trials}),
        changed_hypotheses=sum(t["changed_attempts"]>0 for t in trials),qualified_hypotheses=sum(t["qualified"] for t in trials),
        max_recovered_train_opportunities=max((t["train"]["recovery_metrics"]["selected_opportunity_count"] for t in trials),default=0),
        profile_failures=dict(failures),selected_research_candidate=chosen,diagnostic_leaders=diagnostic,
        sequence=sequence,promotion_pass=False,promotion_blockers=["exploratory_reused_held_date","offline_hypothesis_not_publisher_input"],**AUTHORITY)
    compact.write(output/"machine-trials.json",compact.sealed(dict(trials=trials,**AUTHORITY)))
    compact.write(output/"machine-result.json",compact.sealed(machine))
    aux=run_auxiliary_research(root,output)
    feature_filters=run_feature_filter_research(output)
    patterns=run_pattern_classifier_research(root,output)
    total_policies=aux["hypotheses"]
    auxiliary_inputs=aux["source_manifest"]
    assert code_before==file_sha(__file__),"research_code_changed_during_run"
    for path,sha in kernels.items():
        assert file_sha(path)==sha,"research_kernel_changed_during_run"
    assert strategy.digest(runtime_policy.for_cohort(runtime_policy.load_effective(data_root=root/"data",target_date=DAYS[-1]),("KRX","KRX_REGULAR"))["machine_policy"])==strategy.digest(parent)
    for item in auxiliary_inputs:
        assert file_sha(item["source_path"])==item["source_sha256"]
        assert file_sha(item["label_path"])==item["label_sha256"]
    result=dict(schema=SCHEMA,code_sha256=code_before,wall_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        machine_hypotheses=len(trials),machine_qualified_hypotheses=machine["qualified_hypotheses"],auxiliary_hypotheses=total_policies,
        feature_filter_hypotheses=feature_filters["hypotheses"],pattern_classifier_hypotheses=patterns["hypotheses"],
        source_manifest=manifests+auxiliary_inputs,pristine_holdout=False,**AUTHORITY)
    compact.write(output/"result.json",compact.sealed(result))
    print(json.dumps({k:v for k,v in result.items() if k!="source_manifest"}),flush=True)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--maximum-profiles",type=int,default=240)
    parser.add_argument("--phase",choices=("all","auxiliary"),default="all")
    args=parser.parse_args(argv)
    if not 1<=args.maximum_profiles<=240:
        parser.error("maximum profiles must be between 1 and 240")
    if args.phase=="all":
        run_research(args.workspace,args.output,maximum_profiles=args.maximum_profiles)
    else:
        root=args.workspace.resolve();output=args.output.resolve()
        if not output.is_relative_to(root/"tmp"):
            raise ValueError("research_output_must_be_workspace_tmp")
        output.mkdir(parents=True,exist_ok=True)
        started=time.monotonic();before=file_sha(__file__)
        frozen=compact.read(output/"frozen-machine-hypotheses.json")
        machine=compact.read(output/"machine-result.json")
        assert compact.valid(frozen) and compact.valid(machine)
        assert file_sha(output/"reviewed-machine-source.py")==frozen["code_sha256"]
        for item in frozen["source_manifest"]:
            assert file_sha(item["path"])==item["sha256"]
        for name,sha in frozen["kernel_sha256s"].items():
            assert file_sha(name)==sha
        aux=run_auxiliary_research(root,output)
        filters=run_feature_filter_research(output)
        patterns=run_pattern_classifier_research(root,output)
        assert file_sha(__file__)==before,"auxiliary_research_code_changed"
        for name,sha in frozen["kernel_sha256s"].items():
            assert file_sha(name)==sha,"auxiliary_research_kernel_changed"
        result=dict(schema=SCHEMA,main_phase_code_sha256=frozen["code_sha256"],
            main_result_sha256=machine["artifact_content_sha256"],auxiliary_phase_code_sha256=before,
            auxiliary_hypotheses=aux["hypotheses"],feature_filter_hypotheses=filters["hypotheses"],
            pattern_classifier_hypotheses=patterns["hypotheses"],wall_seconds=time.monotonic()-started,
            pristine_holdout=False,**AUTHORITY)
        compact.write(output/"final-phase-acceptance.json",compact.sealed(result))
        print(json.dumps(result),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
