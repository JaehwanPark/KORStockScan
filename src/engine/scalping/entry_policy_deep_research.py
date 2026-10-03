"""Bounded offline retained-source research. No policy publisher or live caller."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import itertools
import math
from pathlib import Path
import time

import numpy as np

from src.engine.scalping import entry_policy_hypothesis_research as prior

C = prior.compact
DAYS = prior.DAYS
AUTHORITY = {**prior.AUTHORITY, "synthetic_native_identity": False,
             "metric_role": "diagnostic_research", "decision_authority": "offline_only",
             "window_policy": "frozen_20260929_20261002", "sample_floor": "explicit_research_support",
             "primary_decision_metric": "cost_bound_direction_and_fixed_horizon_cf",
             "source_quality_gate": "retained_hash_bound_scope_cost_and_predecision_features",
             "forbidden_uses": ["live_promotion","actual_profit_claim","synthetic_native_identity","hard_safety_relaxation","provider_or_order_authority"]}
RAW_FEATURES = (
    "buy_pressure_10t", "net_aggressive_delta_10t", "price_change_10t_pct",
    "tick_acceleration_ratio", "curr_vs_micro_vwap_bp", "curr_vs_ma5_bp",
    "distance_from_day_high_pct", "intraday_range_pct", "volume_ratio_pct",
    "top3_depth_ratio", "orderbook_total_ratio", "ask_depth_ratio",
)
MICRO_FEATURES = {"buy_pressure_10t", "net_aggressive_delta_10t", "price_change_10t_pct", "tick_acceleration_ratio"}
HORIZONS = (1, 3, 5, 10)


def write(path, data):
    C.write(path, C.sealed({**data, **AUTHORITY}))


def finite(value):
    return value if C.finite(value) else None


def features(row):
    """Only predecision fields. Outcome/decision labels cannot enter a rule."""
    setup = row["setup_evidence"]
    raw = setup.get("strategy_raw_input") or {}
    raw_features = raw.get("features") or {}
    micro = setup.get("micro_recovery_observation") or {}
    usable = micro.get("source_usable") is True
    values = prior.strategy.features(raw, setup)
    # Nominal price and market cap are excluded from this finite hypothesis set.
    values = {k: finite(v) for k, v in values.items() if k not in {"price", "market_cap_krw"}}
    for name in RAW_FEATURES:
        values[name] = finite(raw_features.get(name)) if name not in MICRO_FEATURES or usable else None
    price = finite((raw.get("current") or {}).get("price"))
    bid = finite(raw_features.get("top3_bid_notional"))
    ask = finite(raw_features.get("top3_ask_notional"))
    delta = finite(micro.get("net_aggressive_delta_10t")) if usable else None
    values["flow_delta_notional_over_depth"] = (
        delta * price / (bid + ask)
        if None not in (price, bid, ask, delta) and price > 0 and bid >= 0 and ask >= 0 and bid + ask > 0 else None
    )
    typed = prior.tags(row)
    typed = {k: v for k, v in typed.items() if k in {"family", "phase", "liquidity_band", "volatility_band", "price_tick_band"}}
    typed["micro_source_usable"] = "yes" if usable else "unknown_or_no"
    return values, typed


def setup_join_digest(setup):
    keys=("structure_phase_sha256","micro_recovery_observation","local_breakout","positive_facts","source_quality")
    if not setup.get("structure_phase_sha256") or not isinstance(setup.get("source_quality"),dict):
        return None
    return C.digest({k:setup.get(k) for k in keys})


def exact_pre_ai_join(observation, source):
    setup=source["input"]["entry_setup_evidence_v1"]
    digest=setup_join_digest(setup)
    if (not digest or observation.get("setup_join_digest")!=digest
        or observation.get("ai_trace")!=source["evaluation_key"]
        or not observation.get("attempt") or observation["attempt"]!=source.get("evaluation_attempt_id")
        or observation["symbol"]!=source["stock_code"] or observation["day"]!=source["source_date"]
        or observation["bundle"]!=source["machine_bundle_sha256"]
        or (str(source["effective_venue"]).upper(),str(source["session_bucket"]).upper())!=("KRX","KRX_REGULAR")):
        return False
    before=datetime.fromisoformat(observation["ts"]);after=datetime.fromisoformat(source["decision_ts"])
    return bool(before.tzinfo and after.tzinfo and 0<=(after-before).total_seconds()<=60)


def projection_horizons(row):
    """Retained route-bound projection diagnostics; no new exit contract."""
    comparison = row.get("comparison") or {}
    cost = prior.calibration._full_entry_cost_pct(comparison.get("entry_cost_contract"), source_date=row["source_date"])
    contract = comparison.get("entry_cost_contract") or {}
    charged = finite(comparison.get("conservative_execution_cost_pct"))
    if (cost is None or charged is None or not math.isclose(cost, charged, abs_tol=1e-9)
        or (contract.get("effective_venue"), contract.get("session_bucket")) != (row.get("effective_venue"), row.get("session_bucket"))
        or row.get("source_provenance_verified") is not True
        or row.get("machine_observation_hash_verified") is not True):
        return {}, None
    metrics = row.get("outcome_horizon_metrics") or {}
    gross = {}
    for horizon in HORIZONS:
        metric = metrics.get(f"{horizon}m") or {}
        if (metric.get("status") == "observed" and type(metric.get("sample_count")) is int
            and metric["sample_count"] > 0 and finite(metric.get("end_return_pct")) is not None):
            gross[str(horizon)] = metric["end_return_pct"]
    return gross, cost


def extract(root, output):
    frozen = C.read(root / "tmp/retained-source-policy-research-20261003/frozen-machine-hypotheses.json")
    reference = C.read(root / "tmp/main-machine-auxiliary-source-remediation-20261003/after-machine.json")
    excluded = {r.get("attempt_id") or r.get("decision_trace_id") for r in reference["source_exclusions"]}
    rows, native, census = [], [], Counter()
    for item in frozen["source_manifest"]:
        path = Path(item["path"])
        assert prior.file_sha(path) == item["sha256"]
        for row in prior.stream_array(path):
            if (row.get("effective_venue"), row.get("session_bucket")) != ("KRX", "KRX_REGULAR"):
                continue
            census["scope_rows"] += 1
            if row.get("source_provenance_verified") is not True or row.get("machine_observation_hash_verified") is not True:
                census["projection_provenance_invalid"] += 1
                continue
            numeric, typed = features(row)
            value, reason = prior.calibration._machine_path_value(row)
            gross, cost = projection_horizons(row)
            is_native = row.get("decision_trace_id") not in excluded
            if is_native:
                native.append(row)
            census["native_rows" if is_native else "lineage_excluded_observations"] += 1
            compact = dict(trace=row["decision_trace_id"], day=row["source_date"], symbol=row["stock_code"],
                ts=row["decision_ts"], bundle=row.get("bundle_sha256"),
                ai_trace=row.get("ai_decision_trace_id"),attempt=row.get("evaluation_attempt_id"),
                setup_join_digest=setup_join_digest(row["setup_evidence"]),
                native_opportunity=list(prior.opportunity_identity(row)) if is_native else None,
                features=numeric, types=typed, parent_action=row["machine_action"],
                binary=float(value > 0) if value is not None else None, path_net=value, path_reason=reason,
                gross=gross, cost=cost, source_role="native_opportunity" if is_native else "observational_only_no_native_lineage",
                path_window_sec=(row.get("entry_quality_path") or {}).get("primary_window_sec"),
                target_delay_sec=(row.get("entry_quality_path") or {}).get("time_to_net_target_sec"),
                pre_target_mae_pct=(row.get("entry_quality_path") or {}).get("pre_target_mae_pct"))
            rows.append(compact)
        assert prior.file_sha(path) == item["sha256"]
    assert len(rows) == 2976 and len(native) == 99, "frozen_source_population_changed"
    write(output / "observations.json", dict(rows=rows, census=dict(census), source_manifest=frozen["source_manifest"]))
    write(output / "native-snapshots.json", dict(rows=native, parent_sha256=frozen["parent_sha256"]))
    return rows, native


def anchors(rows, *, spacing_seconds=600, native=False):
    """Choose first snapshots using timestamps only, before consulting outcomes."""
    result, seen, previous = [], set(), {}
    for row in sorted(rows, key=lambda r: (r["ts"], r["trace"])):
        if native:
            identity = row.get("native_opportunity")
            if not identity or tuple(identity) in seen:
                continue
            seen.add(tuple(identity))
        else:
            key = (row["day"], row["symbol"], row["bundle"])
            now = datetime.fromisoformat(row["ts"])
            if now.tzinfo is None:
                raise ValueError("naive_research_timestamp")
            if key in previous and (now - previous[key]).total_seconds() < spacing_seconds:
                continue
            previous[key] = now
        result.append(row)
    return result


def match(row, condition):
    if condition["kind"] == "and":
        return all(match(row, part) for part in condition["parts"])
    if condition["kind"] == "type":
        return row["types"].get(condition["feature"]) == condition["value"]
    value = finite(row["features"].get(condition["feature"]))
    return value is not None and ((value < condition["boundary"]) == (condition["side"] == "lt"))


def conditions(training, *, minimum=5, maximum=8000):
    """Deduplicate training action vectors without using labels or held data."""
    numeric, typed = defaultdict(set), defaultdict(set)
    for row in training:
        for key, value in row["features"].items():
            if finite(value) is not None:
                numeric[key].add(value)
        for key, value in row["types"].items():
            if prior.source_identifier(value) and value != "UNKNOWN":
                typed[key].add(value)
    singles = []
    for key, values in sorted(numeric.items()):
        values = sorted(values)
        if len(values) < 2:
            continue
        boundaries = {values[min(len(values) - 1, len(values) * q // 4)] for q in (1, 2, 3)}
        for boundary in sorted(boundaries):
            singles.extend(dict(kind="numeric", feature=key, boundary=boundary, side=side) for side in ("lt", "ge"))
    singles.extend(dict(kind="type", feature=key, value=value) for key, values in sorted(typed.items()) for value in sorted(values))
    seen, selected = set(), []
    def consider(condition):
        vector = tuple(match(row, condition) for row in training)
        if minimum <= sum(vector) < len(training) and vector not in seen:
            seen.add(vector)
            selected.append((condition, vector))
    for condition in singles:
        consider(condition)
    supported = list(selected)
    pairs = []
    for (left, a), (right, b) in itertools.combinations(supported, 2):
        vector = tuple(x and y for x, y in zip(a, b))
        if minimum <= sum(vector) < len(training) and vector not in seen:
            seen.add(vector)
            condition = dict(kind="and", parts=[left, right])
            pairs.append((condition, vector))
    # Fixed hash order avoids performance-driven budget allocation.
    pairs.sort(key=lambda item: C.digest(item[0]))
    selected.extend(pairs[:max(0, maximum - len(selected))])
    return selected[:maximum]


def net_at(row, horizon, delay=0):
    cost = finite(row.get("cost"))
    end = finite(row.get("gross", {}).get(str(horizon)))
    start = 0.0 if delay == 0 else finite(row.get("gross", {}).get(str(delay)))
    if cost is None or end is None or start is None or start <= -100 or delay >= horizon:
        return None
    return 100 * ((1 + end / 100) / (1 + start / 100) - 1) - cost


def weighted_mean(rows, values):
    groups = defaultdict(list)
    for row, value in zip(rows, values):
        if finite(value) is not None:
            groups[(row["day"], row["symbol"])].append(value)
    return float(np.mean([np.mean(v) for v in groups.values()])) if groups else None


def metric(rows, mask, *, target="binary", horizon=10, delay=0):
    values = [r.get(target) if target != "net" else net_at(r, horizon, delay) for r in rows]
    available = [(r, v, yes) for r, v, yes in zip(rows, values, mask) if finite(v) is not None]
    chosen = [(r, v) for r, v, yes in available if yes]
    base = [v for _, v, _ in available]
    selected = [v for _, v in chosen]
    base_mean = float(np.mean(base)) if base else None
    mean = float(np.mean(selected)) if selected else None
    return dict(available=len(base), selected=len(selected),
        coverage_pct=100 * len(selected) / len(base) if base else None,
        mean=mean, baseline_mean=base_mean,
        win_rate_pct=100 * sum(v > (0.5 if target == "binary" else 0) for v in selected) / len(selected) if selected else None,
        loss_count=sum(v <= (0.5 if target == "binary" else 0) for v in selected),
        successful_excluded=sum(v > (0.5 if target == "binary" else 0) and not yes for _, v, yes in available),
        symbol_days=len({(r["day"], r["symbol"]) for r, _ in chosen}),
        symbol_day_weighted_mean=weighted_mean([r for r, _ in chosen], selected),
        baseline_symbol_day_weighted_mean=weighted_mean([r for r, _, _ in available], base),
        same_population_exposure_delta=float(sum((int(yes) - 1) * v for _, v, yes in available) / len(base)) if base else None)


def rule_mask(rows, condition, mode="include"):
    values = [match(r, condition) for r in rows]
    return values if mode == "include" else [not v for v in values]


def rule_study(training, held, *, minimum=5, target="binary", robust_horizons=False, mode="include"):
    definitions = conditions(training, minimum=minimum)
    trials = []
    for condition, vector in definitions:
        if mode == "exclude":
            vector = tuple(not v for v in vector)
        primary = metric(training, vector, target=target)
        if primary["selected"] < minimum:
            continue
        if target == "binary":
            score = prior.strategy.machine_support_adjusted_win_rate(dict(
                win_rate_pct=100 * primary["mean"], selected_opportunity_count=primary["selected"]))
        elif robust_horizons:
            across = [metric(training, vector, target="net", horizon=h) for h in (3, 5, 10)]
            if any(m["selected"] < minimum for m in across):
                continue
            score = min(m["symbol_day_weighted_mean"] for m in across)
        else:
            score = primary["symbol_day_weighted_mean"]
        trials.append(dict(condition=condition, mode=mode, score=score, train=primary))
    selected = max(trials, key=lambda t: (t["score"], t["train"]["selected"]), default=None)
    if selected:
        selected = deepcopy(selected)
        vector = rule_mask(held, selected["condition"], mode)
        selected["held"] = metric(held, vector, target=target)
        selected["horizons"] = {str(h):dict(train=metric(training, rule_mask(training, selected["condition"], mode), target="net", horizon=h),
                                          held=metric(held, vector, target="net", horizon=h)) for h in (1, 3, 5, 10)}
        selected["path_net"] = dict(train=metric(training, rule_mask(training, selected["condition"], mode), target="path_net"),
                                    held=metric(held, vector, target="path_net"))
    return dict(definitions=len(definitions), comparable_trials=len(trials), selected=selected,
        train_baseline=metric(training, [True]*len(training), target=target),
        held_baseline=metric(held, [True]*len(held), target=target),
        definition_hash=C.digest([c for c, _ in definitions]), trials=trials)


def delay_study(rows):
    results = []
    for delay in (1, 3):
        for horizon in (3, 5, 10):
            if delay >= horizon:
                continue
            paired = [r for r in rows if net_at(r, horizon) is not None and net_at(r, horizon, delay) is not None]
            for state in ("all", "positive_at_delay", "nonpositive_at_delay"):
                subset = [r for r in paired if state == "all" or ((r["gross"][str(delay)] > 0) == (state == "positive_at_delay"))]
                immediate = [net_at(r, horizon) for r in subset]
                delayed = [net_at(r, horizon, delay) for r in subset]
                results.append(dict(delay_min=delay, horizon_min=horizon, known_at_delay_condition=state,
                    paired=len(subset), immediate_mean_cf_net=float(np.mean(immediate)) if subset else None,
                    delayed_mean_cf_net=float(np.mean(delayed)) if subset else None,
                    paired_price_delta=float(np.mean(np.array(delayed)-np.array(immediate))) if subset else None,
                    delayed_symbol_day_mean=weighted_mean(subset, delayed),
                    delayed_positive=sum(v>0 for v in delayed),
                    quote_fill_followup_guard_verified=False))
    return results


def payoff_summary(rows):
    values = [r["path_net"] for r in rows if finite(r.get("path_net")) is not None]
    wins, losses = [v for v in values if v>0], [v for v in values if v<0]
    gain, loss = (float(np.mean(wins)) if wins else None), (float(-np.mean(losses)) if losses else None)
    return dict(observations=len(values), wins=len(wins), losses=len(losses),
        mean_win_pct=gain, mean_loss_magnitude_pct=loss,
        break_even_win_rate_pct=100*loss/(loss+gain) if gain is not None and loss is not None else None,
        observed_win_rate_pct=100*len(wins)/len(values) if values else None,
        mean_cf_net=float(np.mean(values)) if values else None,
        actual_profit_claim=False)


def causal_frontier(root, native):
    parent = prior.runtime_policy.for_cohort(prior.runtime_policy.load_effective(data_root=root/"data", target_date=DAYS[-1]),
                                            ("KRX", "KRX_REGULAR"))["machine_policy"]
    frozen = C.read(root/"tmp/retained-source-policy-research-20261003/frozen-machine-hypotheses.json")
    assert prior.strategy.digest(parent)==frozen["parent_sha256"]
    profiles = [p for p in frozen["profiles"] if p["name"].startswith("joint:")]
    policy = prior.strategy._mutate_tree(parent, next(p["changes"] for p in profiles if p["name"]=="joint:all:relax"), None)
    details=[]
    for row in native:
        decision=prior.evidence.mechanistic_entry_policy_decision(row["setup_evidence"],policy=parent)
        relaxed=prior.evidence.mechanistic_entry_policy_decision(row["setup_evidence"],policy=policy)
        value,reason=prior.calibration._machine_path_value(row)
        setup=relaxed.get("effective_setup_evidence",row["setup_evidence"])
        micro=setup.get("micro_recovery_observation") or {}
        bindings=prior.evidence._risk_fact_bindings(setup)
        evidence_rows=[]
        for risk,facts in bindings.items():
            evidence_rows.extend(dict(risk=risk,fact=fact,available_counterweights=prior.evidence._required_counterweight_fact_ids(setup,risk_code=risk,fact_id=fact)) for fact in facts)
        details.append(dict(trace=row["decision_trace_id"],day=row["source_date"],symbol=row["stock_code"],
            target_first=value>0 if value is not None else None,path_net=value,path_reason=reason,
            parent_action=decision["action"],parent_reason=decision["reason"],
            relaxed_action=relaxed["action"],relaxed_reason=relaxed["reason"],relaxed_state=setup.get("setup_state"),
            micro=micro,relaxed_local_breakout=setup.get("local_breakout"),
            relaxed_risk_assessments=relaxed["core_comparison"]["risk_assessments"],risk_fact_counterweights=evidence_rows))
    def census(selected):
        return dict(rows=len(selected),parent_actions=dict(Counter(r["parent_action"] for r in selected)),
            relaxed_actions=dict(Counter(r["relaxed_action"] for r in selected)),
            relaxed_reasons=dict(Counter(r["relaxed_reason"] for r in selected)),
            recovered=sum(r["parent_action"]!="ENTER_NOW" and r["relaxed_action"]=="ENTER_NOW" for r in selected),
            risk_without_present_counterweight=dict(Counter(x["risk"]+":"+x["fact"] for r in selected for x in r["risk_fact_counterweights"] if not x["available_counterweights"])))
    return dict(parent_sha256=prior.strategy.digest(parent),examined_profile="joint:all:relax",details=details,
        train_successful_nonentries=census([r for r in details if r["day"]<DAYS[-1] and r["parent_action"]!="ENTER_NOW" and r["target_first"]]),
        held_successful_nonentries=census([r for r in details if r["day"]==DAYS[-1] and r["parent_action"]!="ENTER_NOW" and r["target_first"]]))


def permutation_max_search(rows, *, iterations=199):
    """First symbol/day only. Within-day label permutation with max-search rank."""
    rows=[r for r in anchors(rows,spacing_seconds=86400) if r["binary"] is not None]
    minimum=max(10,math.ceil(.1*len(rows)))
    definitions=conditions(rows,minimum=minimum)
    if not definitions:return dict(status="insufficient_condition_support")
    matrix=np.asarray([v for _,v in definitions],dtype=float)
    counts=matrix.sum(axis=1)
    labels=np.array([r["binary"] for r in rows])
    z=1.6448536269514722
    def scores(y):
        p=matrix@y/counts
        return (p+z*z/(2*counts)-z*np.sqrt((p*(1-p)+z*z/(4*counts))/counts))/(1+z*z/counts)
    actual=scores(labels); best=int(np.argmax(actual)); simulated=[]
    rng=np.random.default_rng(20261003)
    indices=[np.array([i for i,r in enumerate(rows) if r["day"]==day]) for day in sorted({r["day"] for r in rows})]
    for _ in range(iterations):
        shuffled=labels.copy()
        for idx in indices:shuffled[idx]=rng.permutation(labels[idx])
        simulated.append(float(np.max(scores(shuffled))))
    return dict(observations=len(rows),conditions=len(definitions),iterations=iterations,rank_penalty_z=z,
        observed_max_rank=float(actual[best]),selected_condition=definitions[best][0],
        permutation_max_rank_p95=float(np.quantile(simulated,.95)),
        family_search_tail_fraction=(1+sum(x>=actual[best] for x in simulated))/(iterations+1),
        exchangeability_assumption="within_source_date_across_first_symbol_day_observations",
        statistical_confirmation=False)


def auxiliary_rows(root):
    previous=root/"tmp/retained-source-policy-research-20261003"
    observations=C.read(previous/"auxiliary-research-observations.json")
    result=C.read(previous/"auxiliary-result.json")
    assert C.valid(observations) and C.valid(result)
    machine=C.read(root/"tmp/deep-retained-policy-research-20261003/observations.json")
    assert C.valid(machine)
    machine_index=defaultdict(list)
    for row in machine["rows"]:
        if row.get("ai_trace"):machine_index[row["ai_trace"]].append(row)
    index=defaultdict(list)
    for item in result["source_manifest"]:
        path=Path(item["source_path"])
        assert prior.file_sha(path)==item["source_sha256"]
        for row in C.read(path)["rows"]:
            key=(row["source_date"],row["stock_code"],row["decision_ts"])
            index[key].append(row)
    rows=[]
    for observed in observations["rows"]:
        if observed["generation"][:2]!=["KRX","KRX_REGULAR"]:continue
        key=(observed["source_date"],observed["stock_code"],observed["decision_ts"])
        matches=[r for r in index[key] if [str(r["effective_venue"]).upper(),str(r["session_bucket"]).upper(),
            C.digest(r["machine_policy"]),r["incumbent_prompt_version"],C.digest(r.get("parent_auxiliary_soft_policy"))]==observed["generation"]]
        assert len(matches)==1,"auxiliary_retained_input_identity_ambiguous"
        source=matches[0]
        numeric,typed=features(dict(setup_evidence=source["input"]["entry_setup_evidence_v1"]))
        earlier=[r for r in machine_index[source["evaluation_key"]] if exact_pre_ai_join(r,source)]
        if len(earlier)==1:
            numeric.update({"pre_ai:"+k:v for k,v in earlier[0]["features"].items()})
        numeric.update({"aux:"+k:finite(v) for k,v in observed["features"].items()})
        cost=finite((source.get("ai_stage_path") or {}).get("conservative_execution_cost_pct"))
        assert cost is not None and cost>=0
        gross={h:net+cost for h,net in observed["nets"].items() if finite(net) is not None}
        rows.append(dict(trace=source["evaluation_key"],day=key[0],symbol=key[1],ts=key[2],
            bundle=source["machine_bundle_sha256"],native_opportunity=observed["opportunity"],
            features=numeric,types=typed,gross=gross,cost=cost,binary=None,path_net=None,
            exact_pre_ai_projection_join=len(earlier)==1,
            generation=observed["generation"],parent_action=observed["incumbent_verdict"]))
    assert all(r["parent_action"]=="PASS" for r in rows),"different_auxiliary_parent_population"
    return rows


def summarize_study(study):
    return {k:v for k,v in study.items() if k!="trials"}


def extract_full_observations(root, output):
    """One bounded streaming pass through retained outcome-independent caches."""
    cached=C.read(output/"full-observations.json")
    if C.valid(cached) and cached.get("extraction_code_sha256")==prior.file_sha(__file__):
        for item in cached["source_manifest"]:
            assert prior.file_sha(item["path"])==item["sha256"],"full_projection_source_changed"
        return cached["rows"],Counter(cached["census"]),cached["source_manifest"]
    old=C.read(output/"observations.json")
    prior_rows={r["trace"]:r for r in old["rows"]}
    rows=[];manifest=[];census=Counter();seen=set()
    for day in DAYS:
        path=root/"data/report/machine_observation_projection"/f"machine_observation_projection_{day}_0_1.json"
        before=prior.file_sha(path)
        print("full retained projection",day,path.stat().st_size,flush=True)
        for raw in prior.stream_array(path):
            if (raw.get("effective_venue"),raw.get("session_bucket"))!=("KRX","KRX_REGULAR"):
                continue
            census["scope_rows"]+=1
            if raw.get("source_provenance_verified") is not True or raw.get("machine_observation_hash_verified") is not True:
                census["provenance_invalid"]+=1;continue
            if raw.get("bundle_sha256")!="6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87":
                census["different_policy_generation"]+=1;continue
            trace=raw["decision_trace_id"]
            if trace in seen:
                raise ValueError("full_projection_duplicate_exact_trace")
            seen.add(trace)
            try:numeric,typed=features(raw)
            except ValueError as exc:
                census["invalid_predecision_features:"+str(exc)]+=1;continue
            value,reason=prior.calibration._machine_path_value(raw)
            gross,cost=projection_horizons(raw)
            r=dict(trace=trace,day=day,symbol=raw["stock_code"],ts=raw["decision_ts"],bundle=raw["bundle_sha256"],
                features=numeric,types=typed,native_opportunity=None,parent_action=raw["machine_action"],
                binary=float(value>0) if value is not None else None,path_net=value,path_reason=reason,
                gross=gross,cost=cost,source_role="full_observational_population_no_new_native_identity",
                quality_status=(raw.get("entry_quality_path") or {}).get("status"),
                quality_reason=(raw.get("entry_quality_path") or {}).get("label_reason"))
            previous=prior_rows.get(trace)
            if previous:
                for key in ("day","symbol","ts","bundle","features","types","binary","path_net","gross","cost"):
                    if r[key]!=previous[key]:raise ValueError("retained_projection_overlap_mismatch:"+key)
                census["exact_overlap_with_evaluable_projection"]+=1
            census["resolved" if r["binary"] is not None else "unresolved_or_cost_gap"]+=1
            census["has_fixed_10m_costed_price" if net_at(r,10) is not None else "fixed_10m_price_or_cost_gap"]+=1
            rows.append(r)
        assert prior.file_sha(path)==before,"full_retained_projection_changed"
        manifest.append(dict(path=str(path),sha256=before,bytes=path.stat().st_size))
    assert census["exact_overlap_with_evaluable_projection"]==len(prior_rows)
    write(output/"full-observations.json",dict(rows=rows,census=dict(census),source_manifest=manifest,
        extraction_code_sha256=prior.file_sha(__file__)))
    return rows,census,manifest


def coverage_metric(rows, mask):
    selected=[r for r,yes in zip(rows,mask) if yes]
    resolved=[r for r in selected if r["binary"] is not None]
    target=sum(r["binary"]==1 for r in resolved)
    return dict(selected_observations=len(selected),resolved=len(resolved),
        unresolved=len(selected)-len(resolved),known_target_first=target,
        resolved_target_first_pct=100*target/len(resolved) if resolved else None,
        all_selected_known_target_lower_bound_pct=100*target/len(selected) if selected else None,
        censoring_reasons=dict(Counter(r.get("quality_reason") or r.get("path_reason") for r in selected if r["binary"] is None)),
        horizon_metrics={str(h):metric(rows,mask,target="net",horizon=h) for h in HORIZONS})


def full_population_study(root, output, initial):
    rows,census,manifest=extract_full_observations(root,output)
    results={}
    for name,spacing in (("observed_10min",600),("symbol_day_first",86400)):
        population=anchors(rows,spacing_seconds=spacing)
        training=[r for r in population if r["day"]<DAYS[-1]];held=[r for r in population if r["day"]==DAYS[-1]]
        fixed=initial[name]["studies"]["direction"]["selected"]["condition"]
        transferred={arm:coverage_metric(sample,rule_mask(sample,fixed)) for arm,sample in (("train",training),("held",held))}
        minimum=max(10,math.ceil(.1*len(training)))
        studies={}
        # Ranking fixed-price endpoints includes observed non-terminal cases.
        for role,robust in (("net10",False),("robust_net",True)):
            print("unconditioned research",name,role,len(training),len(held),flush=True)
            study=rule_study(training,held,minimum=minimum,target="net",robust_horizons=robust)
            if study["selected"]:
                selected=study["selected"];condition=selected["condition"]
                selected["full_coverage"]={arm:coverage_metric(sample,rule_mask(sample,condition)) for arm,sample in (("train",training),("held",held))}
                selected["stress_cost_pp"]={str(extra):{arm:(metric(sample,rule_mask(sample,condition),target="net")["mean"]-extra
                    if metric(sample,rule_mask(sample,condition),target="net")["mean"] is not None else None) for arm,sample in (("train",training),("held",held))} for extra in (.05,.10)}
            write(output/f"full-{name}-{role}-trials.json",study)
            studies[role]=summarize_study(study)
        results[name]=dict(train=len(training),held=len(held),minimum=minimum,transferred_condition=fixed,
            transferred=transferred,studies=studies,
            baseline={arm:coverage_metric(sample,[True]*len(sample)) for arm,sample in (("train",training),("held",held))},
            delays=dict(train=delay_study(training),held=delay_study(held)))
    result=dict(census=dict(census),source_manifest=manifest,populations=results,
        labels_missing_not_imputed=True,promotion_pass=False)
    write(output/"full-population-result.json",result)
    return result


def run(root, output):
    started=time.monotonic()
    before=prior.file_sha(__file__)
    inputs=[root/"tmp/retained-source-policy-research-20261003"/name for name in
        ("frozen-machine-hypotheses.json","auxiliary-result.json","auxiliary-research-observations.json")]
    inputs.extend(Path(m.__file__) for m in (prior,prior.calibration,prior.evidence,prior.strategy,prior.compact,prior.runtime_policy))
    manifest={str(p):prior.file_sha(p) for p in inputs}
    observations=C.read(output/"observations.json");snapshot=C.read(output/"native-snapshots.json")
    assert C.valid(observations) and C.valid(snapshot)
    for item in observations["source_manifest"]:
        assert prior.file_sha(item["path"])==item["sha256"]
    rows=observations["rows"]
    all_results={}
    sets={"native_first":anchors(rows,native=True),"observed_10min":anchors(rows),
          "symbol_day_first":anchors(rows,spacing_seconds=86400)}
    write(output/"frozen-protocol.json",dict(code_sha256=before,input_sha256s=manifest,
        observations_sha256=observations["artifact_content_sha256"],source_manifest=observations["source_manifest"],
        dates=list(DAYS),maximum_conditions=8000,permutations=199,pristine_holdout=False,
        anchor_counts={name:len(population) for name,population in sets.items()}))
    for name,population in sets.items():
        training=[r for r in population if r["day"]<DAYS[-1]];held=[r for r in population if r["day"]==DAYS[-1]]
        minimum=5 if name=="native_first" else max(10,math.ceil(.1*len(training)))
        studies={}
        for role,target,robust in (("direction","binary",False),("net10","net",False),("robust_net","net",True)):
            print("research",name,role,len(training),len(held),flush=True)
            study=rule_study(training,held,minimum=minimum,target=target,robust_horizons=robust)
            write(output/f"{name}-{role}-trials.json",study)
            studies[role]=summarize_study(study)
        chronological=rule_study([r for r in population if r["day"]==DAYS[0]],
            [r for r in population if r["day"]==DAYS[1]],minimum=minimum,target="binary")
        write(output/f"{name}-chronological-trials.json",chronological)
        for role,study in studies.items():
            if study["selected"]:
                condition=study["selected"]["condition"]
                study["selected"]["held_by_symbol"]={symbol:metric([r for r in held if r["symbol"]==symbol],
                    rule_mask([r for r in held if r["symbol"]==symbol],condition),target="binary" if role=="direction" else "net")
                    for symbol in sorted({r["symbol"] for r in held if match(r,condition)})}
                unseen=[r for r in held if r["symbol"] not in {t["symbol"] for t in training}]
                study["selected"]["held_unseen_symbols"]=metric(unseen,rule_mask(unseen,condition),target="binary" if role=="direction" else "net")
        all_results[name]=dict(rows=len(population),train=len(training),held=len(held),minimum=minimum,
            studies=studies,chronological_reselection=summarize_study(chronological),
            train_payoff=payoff_summary(training),held_payoff=payoff_summary(held),
            delays=dict(train=delay_study(training),held=delay_study(held)))
    print("native causal frontier",flush=True)
    frontier=causal_frontier(root,snapshot["rows"])
    write(output/"causal-frontier.json",frontier)
    print("permutation search",flush=True)
    permutation=permutation_max_search([r for r in rows if r["day"]<DAYS[-1]])
    write(output/"permutation-search.json",permutation)
    aux=auxiliary_rows(root)
    train=[r for r in aux if r["day"]<DAYS[-1]];held=[r for r in aux if r["day"]==DAYS[-1]]
    ai={}
    for role,robust in (("net10",False),("robust_net",True)):
        print("auxiliary",role,flush=True)
        study=rule_study(train,held,minimum=5,target="net",robust_horizons=robust,mode="exclude")
        write(output/f"auxiliary-{role}-trials.json",study)
        ai[role]=summarize_study(study)
    ai["chronological_reselection"]=summarize_study(rule_study([r for r in aux if r["day"]==DAYS[0]],
        [r for r in aux if r["day"]==DAYS[1]],minimum=5,target="net",mode="exclude"))
    ai["leave_symbol_out_reselection"]={}
    for symbol in sorted({r["symbol"] for r in train}):
        fold=rule_study([r for r in train if r["symbol"]!=symbol],[r for r in train if r["symbol"]==symbol],minimum=5,target="net",mode="exclude")
        ai["leave_symbol_out_reselection"][symbol]=summarize_study(fold)
    ai["delays"]=dict(train=delay_study(train),held=delay_study(held))
    ai["population"]=dict(train=len(train),held=len(held),generation=sorted({tuple(r["generation"]) for r in aux}),
        exact_pre_ai_projection_join_count=sum(r["exact_pre_ai_projection_join"] for r in aux),new_prompt_responses=0)
    write(output/"auxiliary-deep-result.json",ai)
    full=full_population_study(root,output,all_results)
    assert before==prior.file_sha(__file__),"research_code_changed"
    for path,sha in manifest.items():assert prior.file_sha(path)==sha,"input_or_kernel_changed"
    result=dict(code_sha256=before,wall_seconds=time.monotonic()-started,populations=all_results,
        permutation=permutation,auxiliary=ai,full_population=full,causal_frontier_summary={k:v for k,v in frontier.items() if k!="details"},
        input_sha256s=manifest,pristine_holdout=False,policy_promotion_count=0)
    write(output/"result.json",result)
    print("complete",result["wall_seconds"],flush=True)
    return result


def matrix_metrics(rows, masks, *, horizon=10):
    """Same metric as metric(..., target='net'), computed once per matrix."""
    values=[net_at(r,horizon) for r in rows]
    indices=[i for i,v in enumerate(values) if v is not None]
    selected=masks[:,indices]
    values=np.array([values[i] for i in indices],dtype=float)
    counts=selected.sum(axis=1)
    sums=selected@values
    wins=selected@(values>0).astype(int)
    group_indices=defaultdict(list)
    for column,index in enumerate(indices):group_indices[(rows[index]["day"],rows[index]["symbol"])].append(column)
    group_means=np.zeros(len(masks));group_counts=np.zeros(len(masks),dtype=int)
    for columns in group_indices.values():
        subset=selected[:,columns];n=subset.sum(axis=1);totals=subset@values[columns]
        group_means+=np.divide(totals,n,out=np.zeros(len(masks)),where=n>0)
        group_counts+=n>0
    baseline=metric(rows,[True]*len(rows),target="net",horizon=horizon)
    results=[]
    for i,n in enumerate(counts):
        n=int(n);nwin=int(wins[i]);ng=int(group_counts[i]);total=len(values)
        results.append(dict(available=total,selected=n,coverage_pct=100*n/total if total else None,
            mean=float(sums[i]/n) if n else None,baseline_mean=baseline["baseline_mean"],
            win_rate_pct=100*nwin/n if n else None,loss_count=n-nwin,
            successful_excluded=int(sum(values>0))-nwin,symbol_days=ng,
            symbol_day_weighted_mean=float(group_means[i]/ng) if ng else None,
            baseline_symbol_day_weighted_mean=baseline["baseline_symbol_day_weighted_mean"],
            same_population_exposure_delta=float((sums[i]-sum(values))/total) if total else None))
    return results


def fast_rule_study(training, held, *, minimum=5, robust_horizons=False):
    definitions=conditions(training,minimum=minimum)
    if not definitions:
        return dict(definitions=0,comparable_trials=0,selected=None,trials=[])
    masks=np.asarray([v for _,v in definitions],dtype=bool)
    horizons={h:matrix_metrics(training,masks,horizon=h) for h in ((3,5,10) if robust_horizons else (10,))}
    trials=[]
    for i,(condition,_) in enumerate(definitions):
        relevant=[horizons[h][i] for h in horizons]
        if any(m["selected"]<minimum for m in relevant):continue
        trials.append(dict(condition=condition,mode="include",train=horizons[10][i],
            score=min(m["symbol_day_weighted_mean"] for m in relevant)))
    selected=max(trials,key=lambda t:(t["score"],t["train"]["selected"]),default=None)
    if selected:
        selected=deepcopy(selected)
        train_mask=rule_mask(training,selected["condition"]);held_mask=rule_mask(held,selected["condition"])
        selected["held"]=metric(held,held_mask,target="net")
        selected["horizons"]={str(h):dict(train=metric(training,train_mask,target="net",horizon=h),
            held=metric(held,held_mask,target="net",horizon=h)) for h in HORIZONS}
        required=(3,5,10) if robust_horizons else (10,)
        selected["positive_training_research_candidate"]=bool(selected["score"]>0 and all(
            selected["horizons"][str(h)]["train"]["mean"] is not None and selected["horizons"][str(h)]["train"]["mean"]>0 for h in required))
        selected["held_full_coverage"]=coverage_metric(held,held_mask)
    return dict(definitions=len(definitions),comparable_trials=len(trials),selected=selected,trials=trials,
        definition_hash=C.digest([c for c,_ in definitions]),train_rows=len(training),held_rows=len(held))


def phase_fold(training,held,*,robust=False):
    results={};rules={}
    for phase in sorted({r["types"].get("phase") for r in training if r["types"].get("phase")}):
        train=[r for r in training if r["types"].get("phase")==phase]
        later=[r for r in held if r["types"].get("phase")==phase]
        if len(train)<30 or len({r["symbol"] for r in train})<5:
            results[phase]=dict(status="sparse_phase_parent_only",train_rows=len(train),held_rows=len(later));continue
        minimum=max(5,math.ceil(.1*len(train)))
        print("phase",phase,"robust",robust,len(train),len(later),flush=True)
        study=fast_rule_study(train,later,minimum=minimum,robust_horizons=robust)
        results[phase]={**study,"minimum":minimum}
        selected=study["selected"]
        if selected and selected["positive_training_research_candidate"]:
            rules[phase]=selected["condition"]
    def masks(rows):
        return [r["types"].get("phase") in rules and match(r,rules[r["types"]["phase"]]) for r in rows]
    return dict(results=results,positive_training_phase_rules=rules,
        combined={str(h):dict(train=metric(training,masks(training),target="net",horizon=h),
            held=metric(held,masks(held),target="net",horizon=h)) for h in HORIZONS},
        held_selected_traces=[r["trace"] for r,yes in zip(held,masks(held)) if yes],
        executable_entry_or_policy=False,pristine_holdout=False)


def run_types(root,output):
    started=time.monotonic();before=prior.file_sha(__file__)
    base=C.read(output/"result.json");full=C.read(output/"full-observations.json");protocol=C.read(output/"frozen-type-protocol.json")
    assert all(C.valid(a) for a in (base,full,protocol))
    assert prior.file_sha(output/"reviewed-base-source.py")==base["code_sha256"]
    assert protocol["source_artifact_sha256"]==full["artifact_content_sha256"]
    for path,sha in base["input_sha256s"].items():assert prior.file_sha(path)==sha,"base_kernel_or_input_changed"
    for item in full["source_manifest"]:assert prior.file_sha(item["path"])==item["sha256"]
    population=anchors(full["rows"])
    training=[r for r in population if r["day"]<DAYS[-1]];held=[r for r in population if r["day"]==DAYS[-1]]
    results={}
    for role,robust in (("net10",False),("robust_net",True)):
        fold=phase_fold(training,held,robust=robust)
        for phase,study in fold["results"].items():
            if "trials" in study:
                write(output/f"phase-{role}-{phase}-trials.json",study)
                study.pop("trials")
        results[role]=fold
    chronological=phase_fold([r for r in population if r["day"]==DAYS[0]],
        [r for r in population if r["day"]==DAYS[1]],robust=True)
    for phase,study in chronological["results"].items():
        if "trials" in study:
            write(output/f"phase-chronological-{phase}-trials.json",study)
            study.pop("trials")
    results["chronological_robust_reselection"]=chronological
    assert before==prior.file_sha(__file__),"type_research_code_changed"
    for path,sha in base["input_sha256s"].items():assert prior.file_sha(path)==sha,"base_kernel_or_input_changed"
    result=dict(results=results,code_sha256=before,base_code_sha256=base["code_sha256"],
        base_result_sha256=base["artifact_content_sha256"],source_artifact_sha256=full["artifact_content_sha256"],
        protocol_sha256=protocol["artifact_content_sha256"],wall_seconds=time.monotonic()-started,
        promotion_count=0,pristine_holdout=False)
    write(output/"type-research-result.json",result)
    write(output/"final-acceptance.json",{k:v for k,v in result.items() if k!="results"})
    print("type complete",result["wall_seconds"],flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--reuse-projection", action="store_true")
    parser.add_argument("--phase",choices=("base","types"),default="base")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / "tmp"):
        raise ValueError("research_output_must_be_workspace_tmp")
    output.mkdir(parents=True, exist_ok=True)
    if args.phase=="types":
        run_types(root,output)
        return 0
    if not args.reuse_projection:
        extract(root, output)
    if not args.extract_only:
        run(root, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
