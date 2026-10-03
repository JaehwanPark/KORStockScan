"""Offline retained-path and past-observation research; no live consumer."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import time

import numpy as np

from src.engine.scalping import entry_policy_deep_research as deep

C = deep.C
HORIZONS = (1, 3, 5, 10, 20, 30, 60)
OBJECTIVES = {"short": (3, 5, 10), "medium": (10, 20, 30), "long": (20, 30, 60)}
RULES = (
    "price_turn", "price_and_flow_turn", "price_micro_confirmed",
    "price_turn_spread", "phase_recovery", "vwap_reclaim_flow",
    "flow_price_improve", "pressure_spread_price",
)
STATIC_RULES = ("current_flow_price", "current_vwap_flow", "current_recovery")
BAR_RULES = ("bar_turn", "bar_two_step_recovery", "bar_higher_low", "bar_breakout_five",
             "bar_ma5_reclaim", "bar_turn_flow", "bar_breakout_micro", "bar_ma5_flow")
AUTHORITY = {**deep.AUTHORITY,
    "primary_decision_metric": "cost_bound_path_and_chronological_cf",
    "source_quality_gate": "exact_retained_source_cost_scope_and_past_only_features"}


def write(path, value):
    C.write(path, C.sealed({**value, **AUTHORITY}))


def finite(value):
    return deep.finite(value)


def state(path, cost):
    """Symmetric descriptive states; retain source defects in separate flags."""
    if cost is None:
        return "cost_gap"
    if not path:
        return "path_missing"
    first = path.get("first_hit")
    if first == "same_bar_ambiguous":
        return "same_bar_ambiguous"
    if first == "neither_hit":
        return "neither_boundary_hit"
    for expected, field, name in (
        ("net_target_first", "time_to_net_target_sec", "target"),
        ("exact_stop_first", "time_to_exact_stop_sec", "stop"),
    ):
        if first == expected:
            delay = finite(path.get(field))
            if delay is None or delay < 0:
                return "hit_time_gap"
            return ("fast_" if delay <= 180 else "late_") + name
    return "path_source_gap"


def extend_row(raw, previous):
    if (raw.get("source_provenance_verified") is not True
        or raw.get("machine_observation_hash_verified") is not True
        or (raw.get("effective_venue"), raw.get("session_bucket")) != ("KRX", "KRX_REGULAR")):
        raise ValueError("invalid_projection_provenance_or_scope")
    numeric, typed = deep.features(raw)
    gross, cost = deep.projection_horizons(raw)
    checks = dict(day=raw["source_date"], symbol=raw["stock_code"], ts=raw["decision_ts"],
                  bundle=raw["bundle_sha256"], features=numeric, types=typed, gross=gross, cost=cost)
    for key, value in checks.items():
        if previous[key] != value:
            raise ValueError("retained_projection_changed:" + key)
    result = deepcopy(previous)
    result["path"] = raw.get("entry_quality_path") or {}
    result["path_state"] = state(result["path"], cost)
    result["route"] = raw.get("outcome_request_code")
    source = raw["setup_evidence"].get("strategy_raw_input") or {}
    result["observed_price"] = finite((source.get("current") or {}).get("price"))
    result["horizons"] = deepcopy(raw.get("outcome_horizon_metrics") or {})
    for horizon in HORIZONS:
        metric = result["horizons"].get(f"{horizon}m") or {}
        if (cost is not None and metric.get("status") == "observed"
            and type(metric.get("sample_count")) is int and metric["sample_count"] > 0
            and finite(metric.get("end_return_pct")) is not None):
            result["gross"][str(horizon)] = metric["end_return_pct"]
    return result


def sequence_rows(rows):
    """Nearest unambiguous past snapshots, each 15..180s apart, same route."""
    groups = defaultdict(list)
    result = []
    for row in rows:
        groups[(row["day"], row["symbol"], row["bundle"], row.get("route"))].append(row)
    for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
        counts = Counter(row["ts"] for row in group)
        ordered = sorted(group, key=lambda row: (row["ts"], row["trace"]))
        for i, original in enumerate(ordered):
            row = deepcopy(original)
            row["sequence"] = {}
            row["sequence_status"] = "past_observation_missing"
            now = datetime.fromisoformat(row["ts"])
            if not now.tzinfo or now.date().isoformat() != row["day"]:
                raise ValueError("invalid_decision_clock")
            if not key[-1] or counts[row["ts"]] != 1:
                row["sequence_status"] = "route_missing_or_same_time_ambiguous"
                result.append(row)
                continue
            candidates = [r for r in ordered[:i]
                          if counts[r["ts"]] == 1
                          and 15 <= (now - datetime.fromisoformat(r["ts"])).total_seconds() <= 180]
            if not candidates:
                result.append(row)
                continue
            prior = candidates[-1]
            prior_ts = datetime.fromisoformat(prior["ts"])
            older = [r for r in ordered[:i]
                     if counts[r["ts"]] == 1
                     and 15 <= (prior_ts - datetime.fromisoformat(r["ts"])).total_seconds() <= 180]
            old = older[-1] if older else None
            a, b = row["features"], prior["features"]
            def difference(name):
                x, y = finite(a.get(name)), finite(b.get(name))
                return x - y if x is not None and y is not None else None
            def change(left, right):
                x, y = finite(left.get("observed_price")), finite(right.get("observed_price"))
                return 100 * (x / y - 1) if x is not None and y is not None and x > 0 and y > 0 else None
            row["sequence"] = dict(
                previous_trace=prior["trace"], previous_ts=prior["ts"],
                older_trace=old["trace"] if old else None,
                older_ts=old["ts"] if old else None,
                gap_sec=(now - prior_ts).total_seconds(),
                price_change_pct=change(row, prior),
                previous_price_change_pct=change(prior, old) if old else None,
                previous_phase=prior["types"].get("phase"),
                previous_delta=finite(b.get("net_aggressive_delta_10t")),
                previous_vwap=finite(b.get("curr_vs_micro_vwap_bp")),
                delta_change=difference("net_aggressive_delta_10t"),
                micro_price_change=difference("price_change_10t_pct"),
                pressure_change=difference("buy_pressure_10t"),
                spread_change=difference("spread_bp"),
            )
            row["sequence_status"] = "three_snapshots" if old else "two_snapshots"
            result.append(row)
    return sorted(result, key=lambda row: (row["day"], row["ts"], row["symbol"], row["trace"]))


def positive(value):
    return finite(value) is not None and value > 0


def nonpositive(value):
    return finite(value) is not None and value <= 0


def rule(row, name):
    s, f = row.get("sequence") or {}, row["features"]
    price_up = positive(s.get("price_change_pct"))
    turn = price_up and nonpositive(s.get("previous_price_change_pct"))
    delta_up = positive(f.get("net_aggressive_delta_10t"))
    micro_up = positive(f.get("price_change_10t_pct"))
    if name in BAR_RULES:
        b = row.get("bar_features") or {}
        return bool({
            "bar_turn": b.get("turn"),
            "bar_two_step_recovery": b.get("two_step_recovery"),
            "bar_higher_low": b.get("higher_low"),
            "bar_breakout_five": b.get("breakout_five"),
            "bar_ma5_reclaim": b.get("ma5_reclaim"),
            "bar_turn_flow": b.get("turn") and delta_up,
            "bar_breakout_micro": b.get("breakout_five") and delta_up and micro_up,
            "bar_ma5_flow": b.get("ma5_reclaim") and delta_up,
        }[name])
    recovery = row["types"].get("phase") in {"recovery_continuation", "continuation"}
    values = {
        "price_turn": turn,
        "price_and_flow_turn": turn and nonpositive(s.get("previous_delta")) and delta_up,
        "price_micro_confirmed": price_up and delta_up and micro_up,
        "price_turn_spread": turn and nonpositive(s.get("spread_change")),
        "phase_recovery": price_up and recovery and s.get("previous_phase") in {
            "pullback", "rebound_attempt", "range_or_no_setup"},
        "vwap_reclaim_flow": positive(f.get("curr_vs_micro_vwap_bp"))
            and nonpositive(s.get("previous_vwap")) and delta_up,
        "flow_price_improve": price_up and positive(s.get("delta_change")) and positive(s.get("micro_price_change")),
        "pressure_spread_price": price_up and positive(s.get("pressure_change"))
            and finite(s.get("spread_change")) is not None and s["spread_change"] < 0,
        "current_flow_price": delta_up and micro_up,
        "current_vwap_flow": positive(f.get("curr_vs_micro_vwap_bp")) and delta_up,
        "current_recovery": recovery,
    }
    if name not in values:
        raise ValueError("undefined_research_rule")
    return bool(values[name])


def horizon_status(row, horizon):
    end = datetime.fromisoformat(row["ts"]) + timedelta(minutes=horizon)
    if end.date().isoformat() != row["day"] or (end.hour, end.minute, end.second, end.microsecond) > (15, 30, 0, 0):
        return "session_censored"
    if finite(row.get("cost")) is None:
        return "cost_gap"
    if deep.net_at(row, horizon) is None:
        return "price_gap"
    return "comparable"


def metric(rows, mask, horizon):
    selected = [r for r, yes in zip(rows, mask) if yes]
    available = [r for r in selected if horizon_status(r, horizon) == "comparable"]
    vals = [deep.net_at(r, horizon) for r in available]
    baseline = [r for r in rows if horizon_status(r, horizon) == "comparable"]
    baseline_vals = [deep.net_at(r, horizon) for r in baseline]
    counts = Counter(r["symbol"] for r in available)
    prices = [r.get("horizons", {}).get(f"{horizon}m", {}) for r in available]
    def avg(values):
        values = [v for v in values if finite(v) is not None]
        return float(np.mean(values)) if values else None
    return dict(
        total=len(rows), selected=len(selected), comparable=len(available),
        coverage_pct=100 * len(available) / len(selected) if selected else None,
        statuses=dict(Counter(horizon_status(r, horizon) for r in selected)),
        symbols=len(counts), mean=avg(vals),
        symbol_day_mean=deep.weighted_mean(available, vals), baseline_mean=avg(baseline_vals),
        positive=sum(v > 0 for v in vals), losses=sum(v <= 0 for v in vals),
        positive_excluded=sum(v > 0 for v in baseline_vals) - sum(v > 0 for v in vals),
        p10=float(np.quantile(vals, .1)) if vals else None,
        max_symbol_share_pct=100 * max(counts.values()) / len(vals) if vals else None,
        mean_mfe_pct=avg([m.get("mfe_pct") for m in prices]),
        mean_mae_pct=avg([m.get("mae_pct") for m in prices]),
        extra_cost_stress={str(c): avg(vals) - c if vals else None for c in (.05, .10)},
        path_states=dict(Counter(r.get("path_state", "unavailable") for r in selected)),
    )


def selection_mask(rows, definition):
    return [rule(r, definition["rule"]) and (definition["phase"] is None
            or r["types"].get("phase") == definition["phase"]) for r in rows]


def anchors(rows, spacing):
    """Observation sampling does not merge exact chart routes or use outcomes."""
    previous, result = {}, []
    for row in sorted(rows, key=lambda r: (r["ts"], r["trace"])):
        key = (row["day"], row["symbol"], row["bundle"], row.get("route"))
        now = datetime.fromisoformat(row["ts"])
        if key not in previous or (now - previous[key]).total_seconds() >= spacing:
            previous[key] = now
            result.append(row)
    return result


def definitions(training, names):
    phases = [None]
    for phase in sorted({r["types"].get("phase") for r in training if r["types"].get("phase")}):
        group = [r for r in training if r["types"].get("phase") == phase]
        if len(group) >= 30 and len({r["symbol"] for r in group}) >= 5:
            phases.append(phase)
    return [dict(rule=name, phase=phase) for phase in phases for name in names]


def fit_inputs(training, definitions_, horizons):
    return dict(
        masks=np.asarray([selection_mask(training, d) for d in definitions_], dtype=bool),
        values={h: np.array([deep.net_at(r, h) if horizon_status(r, h) == "comparable" else np.nan
                            for r in training], dtype=float) for h in horizons},
        groups={key: np.array([i for i, r in enumerate(training) if (r["day"], r["symbol"]) == key])
                for key in sorted({(r["day"], r["symbol"]) for r in training})},
    )


def choose(training, definitions_, horizons, *, prepared=None, omit_symbol=None):
    prepared = prepared or fit_inputs(training, definitions_, horizons)
    masks = prepared["masks"] & np.array([r["symbol"] != omit_symbol for r in training], dtype=bool)
    selected_counts = masks.sum(axis=1)
    computed = {}
    for h in horizons:
        values = prepared["values"][h]
        comparable = masks & np.isfinite(values)
        counts = comparable.sum(axis=1)
        sums = (comparable * np.nan_to_num(values)).sum(axis=1)
        group_totals = np.zeros(len(definitions_))
        group_counts = np.zeros(len(definitions_))
        symbols = defaultdict(lambda: np.zeros(len(definitions_), dtype=bool))
        for (_, symbol), ids in prepared["groups"].items():
            sub = comparable[:, ids]
            n = sub.sum(axis=1)
            total = (sub * np.nan_to_num(values[ids])).sum(axis=1)
            group_totals += np.divide(total, n, out=np.zeros(len(definitions_)), where=n > 0)
            group_counts += n > 0
            symbols[symbol] |= n > 0
        symbol_counts = np.sum(list(symbols.values()), axis=0) if symbols else np.zeros(len(definitions_))
        computed[h] = [dict(selected=int(selected_counts[i]), comparable=int(counts[i]),
            symbols=int(symbol_counts[i]), coverage_pct=100 * counts[i] / selected_counts[i] if selected_counts[i] else None,
            mean=float(sums[i] / counts[i]) if counts[i] else None,
            symbol_day_mean=float(group_totals[i] / group_counts[i]) if group_counts[i] else None)
            for i in range(len(definitions_))]
    trials = []
    for i, definition in enumerate(definitions_):
        metrics = {str(h): computed[h][i] for h in horizons}
        phase_rows = [r for r in training if r["symbol"] != omit_symbol
                      and r["types"].get("phase") == definition["phase"]]
        phase_supported = definition["phase"] is None or (
            len(phase_rows) >= 30 and len({r["symbol"] for r in phase_rows}) >= 5)
        eligible = all(m["comparable"] >= 10 and m["symbols"] >= 5
                       and m["coverage_pct"] >= 80 for m in metrics.values()) and phase_supported
        score = min(m["symbol_day_mean"] for m in metrics.values()) if eligible else None
        trials.append(dict(definition=definition, train=metrics, eligible=eligible, score=score))
    selected = max((t for t in trials if t["eligible"]),
                   key=lambda t: (t["score"], min(m["comparable"] for m in t["train"].values())), default=None)
    return deepcopy(selected), trials


def evaluate_selected(training, held, selected, horizons, names):
    if selected is None:
        return None
    definition = selected["definition"]
    a, b = selection_mask(training, definition), selection_mask(held, definition)
    selected["positive_training"] = selected["score"] > 0 and all(m["mean"] > 0 for m in selected["train"].values())
    selected["all_horizons"] = {str(h): dict(train=metric(training, a, h), held=metric(held, b, h)) for h in HORIZONS}
    common_a = [r for r in training if all(horizon_status(r, h) == "comparable" for h in horizons)]
    common_b = [r for r in held if all(horizon_status(r, h) == "comparable" for h in horizons)]
    selected["common_population"] = {str(h): dict(
        train=metric(common_a, selection_mask(common_a, definition), h),
        held=metric(common_b, selection_mask(common_b, definition), h)) for h in horizons}
    selected["held_traces"] = [r["trace"] for r, yes in zip(held, b) if yes]
    selected["held_symbols"] = {symbol: {str(h): metric(
        [r for r in held if r["symbol"] == symbol],
        selection_mask([r for r in held if r["symbol"] == symbol], definition), h) for h in horizons}
        for symbol in sorted({r["symbol"] for r, yes in zip(held, b) if yes})}
    symbols = sorted({r["symbol"] for r, yes in zip(training, a) if yes})
    selected["leave_selected_train_symbol_out"] = []
    # Reselect only the predeclared definitions; no held labels in fitting.
    frozen = definitions(training, names)
    prepared = fit_inputs(training, frozen, horizons)
    for symbol in symbols:
        fitted, _ = choose(training, frozen, horizons, prepared=prepared, omit_symbol=symbol)
        selected["leave_selected_train_symbol_out"].append(dict(
            omitted_symbol=symbol, definition=fitted["definition"] if fitted else None,
            score=fitted["score"] if fitted else None))
    return selected


def fold(rows, train_days, held_day, *, names=RULES):
    training = [r for r in rows if r["day"] in train_days]
    held = [r for r in rows if r["day"] == held_day]
    result = dict(train_rows=len(training), held_rows=len(held), objectives={})
    for role, rule_names in (("sequence", names), ("static", STATIC_RULES)):
        choices = definitions(training, rule_names)
        for name, horizons in OBJECTIVES.items():
            selected, trials = choose(training, choices, horizons)
            result["objectives"][role + ":" + name] = dict(
                definitions=len(choices), trials=trials,
                selected=evaluate_selected(training, held, selected, horizons, rule_names))
    return result


def classification(rows):
    cross = Counter((r.get("quality_reason") or "missing_path", r["path_state"]) for r in rows)
    return dict(total=len(rows), states=dict(Counter(r["path_state"] for r in rows)),
        crosswalk=[dict(old_reason=k[0], state=k[1], count=v) for k, v in sorted(cross.items())],
        path_cadence_gaps=sum(r["path"].get("cadence_complete") is False for r in rows),
        by_state={state_: {str(h): metric(rows, [r["path_state"] == state_ for r in rows], h)
                         for h in HORIZONS} for state_ in sorted({r["path_state"] for r in rows})},
        path_label_is_not_actual_fill=True)


def aux_risk(row, name):
    f = row["features"]
    def get(key):
        # An exact pre-AI observation may fill a missing input; no guessed joins.
        value = finite(f.get(key))
        return value if value is not None else finite(f.get("pre_ai:" + key))
    delta, price = get("net_aggressive_delta_10t"), get("price_change_10t_pct")
    spread, tick = get("spread_bp"), get("tick_pct")
    s = row.get("sequence") or {}
    return bool({
        "flow_without_price": positive(delta) and nonpositive(price),
        "buy_pressure_without_price": get("buy_pressure_10t") is not None
            and get("buy_pressure_10t") > 50 and nonpositive(price),
        "spread_over_tick_without_price": spread is not None and tick is not None
            and spread > tick * 100 and nonpositive(price),
        "flow_weakening_spread_widening": finite(s.get("delta_change")) is not None
            and s["delta_change"] < 0 and positive(s.get("spread_change")),
    }[name])


def auxiliary(root, rows):
    aux = deep.auxiliary_rows(root)
    old = C.read(root / "tmp/deep-retained-policy-research-20261003/observations.json")
    seq = {r["trace"]: r for r in rows}
    index = defaultdict(list)
    for r in old["rows"]:
        if r.get("ai_trace"):
            index[r["ai_trace"]].append(r)
    for row in aux:
        matches = index[row["trace"]]
        if row["exact_pre_ai_projection_join"] and len(matches) == 1:
            row["sequence"] = seq[matches[0]["trace"]]["sequence"]
        row["horizons"] = {}
    names = ("flow_without_price", "buy_pressure_without_price", "spread_over_tick_without_price", "flow_weakening_spread_widening")
    result = dict(rows=len(aux), exact_pre_ai_joins=sum(r["exact_pre_ai_projection_join"] for r in aux),
                  new_prompt_responses=0, new_prompt_effect="unsupported", folds={})
    for held_day, train_days in ((deep.DAYS[1], deep.DAYS[:1]), (deep.DAYS[2], deep.DAYS[:2])):
        training = [r for r in aux if r["day"] in train_days]
        held = [r for r in aux if r["day"] == held_day]
        trials = []
        for name in names:
            masks = {"train": [not aux_risk(r, name) for r in training],
                     "held": [not aux_risk(r, name) for r in held]}
            comparisons = {str(h): {k: metric(sample, masks[k], h)
                                   for k, sample in (("train", training), ("held", held))}
                           for h in (1, 3, 5, 10)}
            relevant = [comparisons[str(h)]["train"] for h in (3, 5, 10)]
            behavior_changed = any(not x for x in masks["train"])
            eligible = behavior_changed and all(m["comparable"] >= 3 and m["positive_excluded"] == 0 for m in relevant)
            trials.append(dict(rule=name, eligible=eligible,
                behavior_changed=behavior_changed,
                score=min(m["symbol_day_mean"] for m in relevant) if eligible else None,
                comparisons=comparisons, flagged_train=sum(not x for x in masks["train"]),
                flagged_held=sum(not x for x in masks["held"])))
        chosen = max((r for r in trials if r["eligible"]), key=lambda r: r["score"], default=None)
        result["folds"][held_day] = dict(train_rows=len(training), held_rows=len(held), trials=trials,
                                        selected=chosen["rule"] if chosen else None)
    return result


def bar_features(row, prices, timestamps):
    """Use canonical completed bars, conservatively lagged by 60 seconds."""
    now = datetime.fromisoformat(row["ts"])
    cutoff = now - timedelta(seconds=60)
    end = bisect_right(timestamps, cutoff)
    if end < 6:
        return {}, "fewer_than_six_past_bars"
    window = prices[end - 6:end]
    times = timestamps[end - 6:end]
    if (now - (times[-1] + timedelta(seconds=60))).total_seconds() > 90:
        return {}, "stale_past_bar"
    if (len(set(times)) != 6 or (end > 6 and timestamps[end - 7] == times[0])
        or any(not 0 < (b - a).total_seconds() <= 90 for a, b in zip(times, times[1:]))):
        return {}, "past_bar_cadence_or_duplicate_gap"
    if any(t.date().isoformat() != row["day"] for t in times):
        return {}, "cross_date_past_bar"
    for bar in window:
        if (bar.get("stock_code"), bar.get("effective_venue"), bar.get("session_bucket"), bar.get("source_request_code")) != (
            row["symbol"], "KRX", "KRX_REGULAR", row.get("route")):
            return {}, "past_bar_route_mismatch"
        if bar.get("completed_bar_only") is not True or bar.get("source_quality") != "pass_completed_ka10080_bar":
            return {}, "past_bar_source_invalid"
        values = [finite(bar.get(k)) for k in ("open", "high", "low", "close")]
        if any(v is None or v <= 0 for v in values) or not values[2] <= min(values[0], values[3]) <= max(values[0], values[3]) <= values[1]:
            return {}, "past_bar_ohlc_invalid"
    closes = [b["close"] for b in window]
    turn = closes[-2] <= closes[-3] and closes[-1] > closes[-2]
    breakout = closes[-1] > max(b["high"] for b in window[:-1])
    reclaim = closes[-2] <= float(np.mean(closes[:-1])) and closes[-1] > float(np.mean(closes[1:]))
    return dict(turn=turn, two_step_recovery=closes[-3] <= closes[-4] and closes[-3] < closes[-2] < closes[-1],
        higher_low=window[-1]["low"] > window[-2]["low"] and closes[-1] > closes[-2]
            and closes[-1] > window[-1]["open"], breakout_five=breakout, ma5_reclaim=reclaim,
        latest_bar_at=times[-1].isoformat(), oldest_bar_at=times[0].isoformat(),
        decision_lag_sec=(now - times[-1]).total_seconds()), "usable"


def add_bar_features(root, rows):
    result, manifest = [], []
    for day in deep.DAYS:
        path = root / "data/report/machine_completed_price_source" / f"machine_completed_price_source_{day}.json"
        before = deep.prior.file_sha(path)
        cache = C.read(path)
        if (not deep.prior.calibration._artifact_content_sha256_valid(cache)
            or cache.get("schema") != "machine_completed_price_source_v2"
            or cache.get("source_date") != day):
            raise ValueError("completed_cache_invalid")
        groups = defaultdict(list)
        for bar in cache["prices"]:
            if (bar.get("effective_venue"), bar.get("session_bucket")) == ("KRX", "KRX_REGULAR"):
                groups[(bar.get("stock_code"), bar.get("source_request_code"))].append(bar)
        indexed = {}
        for key, group in groups.items():
            group.sort(key=lambda b: b["timestamp"])
            indexed[key] = (group, [datetime.fromisoformat(b["timestamp"]) for b in group])
        for original in rows:
            if original["day"] != day:
                continue
            row = deepcopy(original)
            prices, timestamps = indexed.get((row["symbol"], row.get("route")), ([], []))
            row["bar_features"], row["bar_status"] = bar_features(row, prices, timestamps)
            result.append(row)
        if deep.prior.file_sha(path) != before:
            raise ValueError("completed_cache_changed")
        manifest.append(dict(path=str(path), sha256=before, artifact_content_sha256=cache["artifact_content_sha256"]))
    return result, manifest


def run_bars(root, output):
    started = time.monotonic()
    parent = output.parent
    projection = C.read(parent / "projection.json")
    if (not C.valid(projection) or projection.get("extraction_code_sha256") !=
        deep.prior.file_sha(parent / "reviewed-snapshot-phase-source.py")):
        raise ValueError("snapshot_phase_receipt_invalid")
    original_protocol = C.read(parent / "snapshot-phase-protocol.json")
    if not C.valid(original_protocol):
        raise ValueError("snapshot_protocol_invalid")
    for path, sha in original_protocol["code_input_sha256s"].items():
        if Path(path).resolve() != Path(__file__).resolve() and deep.prior.file_sha(path) != sha:
            raise ValueError("snapshot_dependency_changed")
    for item in projection["source_manifest"]:
        if deep.prior.file_sha(item["path"]) != item["sha256"]:
            raise ValueError("snapshot_source_changed")
    code_sha = deep.prior.file_sha(__file__)
    before = policy_hashes(root)
    source_paths = [root / "data/report/machine_completed_price_source" / f"machine_completed_price_source_{d}.json" for d in deep.DAYS]
    source_hashes = {str(p): deep.prior.file_sha(p) for p in source_paths}
    write(output / "protocol.json", dict(code_sha256=code_sha, source_sha256s=source_hashes,
        parent_projection_sha256=projection["artifact_content_sha256"], sequence_rules=BAR_RULES,
        static_rules=STATIC_RULES, objectives=OBJECTIVES, minimum_train_comparable=10,
        minimum_train_symbols=5, minimum_coverage_pct=80, bar_minimum_lag_sec=60,
        minimum_bars=6, max_bar_gap_sec=90, pristine_holdout=False))
    rows, manifest = add_bar_features(root, projection["rows"])
    write(output / "projection.json", dict(rows=rows, source_manifest=manifest,
        parent_projection_sha256=projection["artifact_content_sha256"], code_sha256=code_sha))
    eligible = [r for r in rows if r["bar_status"] == "usable"]
    population = anchors(eligible, 600)
    folds = {}
    for held_day, train_days in ((deep.DAYS[1], deep.DAYS[:1]), (deep.DAYS[2], deep.DAYS[:2])):
        print("completed bar fold", held_day, flush=True)
        folds[held_day] = fold(population, train_days, held_day, names=BAR_RULES)
    sensitivity = {}
    for spacing in (3600, 86400):
        population_ = anchors(eligible, spacing)
        held = [r for r in population_ if r["day"] == deep.DAYS[-1]]
        sensitivity[str(spacing)] = {}
        for name, result in folds[deep.DAYS[-1]]["objectives"].items():
            if result["selected"]:
                definition = result["selected"]["definition"]
                sensitivity[str(spacing)][name] = {str(h): metric(held, selection_mask(held, definition), h) for h in HORIZONS}
    write(output / "machine-results.json", dict(folds=folds, anchor_sensitivity=sensitivity,
        bar_status_by_day={d: dict(Counter(r["bar_status"] for r in rows if r["day"] == d)) for d in deep.DAYS},
        original_population=len(rows), eligible_population=len(eligible),
        anchor_counts=dict(Counter(r["day"] for r in population)), pristine_holdout=False,
        live_feature_delivery_proven=False))
    write(output / "auxiliary-results.json", auxiliary(root, rows))
    for path, sha in source_hashes.items():
        if deep.prior.file_sha(path) != sha:
            raise ValueError("completed_source_changed_during_run")
    for path, sha in original_protocol["code_input_sha256s"].items():
        if Path(path).resolve() != Path(__file__).resolve() and deep.prior.file_sha(path) != sha:
            raise ValueError("snapshot_dependency_changed_during_run")
    if policy_hashes(root) != before or deep.prior.file_sha(__file__) != code_sha:
        raise ValueError("policy_or_research_code_changed")
    write(output / "execution-receipt.json", dict(code_sha256=code_sha,
        policy_hash_count=len(before), policy_hash_mismatches=0, elapsed_seconds=time.monotonic() - started,
        parent_projection_sha256=projection["artifact_content_sha256"], source_manifest=manifest,
        snapshot_protocol_sha256=original_protocol["artifact_content_sha256"],
        actual_profit_validated=False, registered_policy_promotion_count=0, pristine_holdout=False))
    print("completed bar phase complete", time.monotonic() - started, flush=True)


def single_horizon_validation(rows):
    eligible = [r for r in rows if r["bar_status"] == "usable"]
    population = anchors(eligible, 600)
    folds = {}
    for held_day, train_days in ((deep.DAYS[1], deep.DAYS[:1]), (deep.DAYS[2], deep.DAYS[:2])):
        training = [r for r in population if r["day"] in train_days]
        held = [r for r in population if r["day"] == held_day]
        results = {}
        for role, names in (("sequence", BAR_RULES), ("static", STATIC_RULES)):
            choices = definitions(training, names)
            for h in (3, 5, 10, 20, 30, 60):
                selected, trials = choose(training, choices, (h,))
                results[f"{role}:{h}"] = dict(definitions=len(choices), trials=trials,
                    selected=evaluate_selected(training, held, selected, (h,), names))
        folds[held_day] = results
    return folds


def retained_path_diagnostics(rows):
    """Descriptive outcome groups cannot be used as entry features."""
    result = {}
    sampled = anchors(rows, 600)
    for group in ("all", "neither_boundary_hit", "late_target", "late_stop"):
        population = [r for r in sampled if group == "all" or r["path_state"] == group]
        result[group] = {}
        for h in HORIZONS:
            available = [r for r in population if horizon_status(r, h) == "comparable"]
            full = [r for r in available if finite((r.get("horizons", {}).get(f"{h}m") or {}).get("mfe_pct")) is not None]
            touched = [r for r in full if r["horizons"][f"{h}m"]["mfe_pct"] >= r["cost"] + .1]
            result[group][str(h)] = dict(
                comparable=len(available), cost_mean=float(np.mean([r["cost"] for r in available])) if available else None,
                gross_endpoint_mean=float(np.mean([r["gross"][str(h)] for r in available])) if available else None,
                net_endpoint_mean=float(np.mean([deep.net_at(r, h) for r in available])) if available else None,
                positive_net_endpoints=sum(deep.net_at(r, h) > 0 for r in available),
                mfe_available=len(full), mfe_above_cost_and_point_one=len(touched),
                touched_then_nonpositive_endpoint=sum(deep.net_at(r, h) <= 0 for r in touched),
                actual_fill_or_exit_proven=False, post_outcome_group_not_a_predictor=True)
    return result


def run_horizons(root, output):
    started = time.monotonic()
    projection = C.read(output / "projection.json")
    parent_receipt = C.read(output / "execution-receipt.json")
    if (not C.valid(projection) or not C.valid(parent_receipt)
        or projection.get("code_sha256") != parent_receipt.get("code_sha256")
        or projection.get("code_sha256") != deep.prior.file_sha(output / "reviewed-completed-phase-source.py")):
        raise ValueError("completed_phase_receipt_invalid")
    code_sha = deep.prior.file_sha(__file__)
    before = policy_hashes(root)
    inherited = C.read(output.parent / "snapshot-phase-protocol.json")
    if not C.valid(inherited):
        raise ValueError("snapshot_protocol_invalid")
    dependency_hashes = dict(inherited["code_input_sha256s"])
    dependency_hashes[str(Path(__file__))] = code_sha
    dependency_hashes[str(output / "projection.json")] = deep.prior.file_sha(output / "projection.json")
    for path, sha in dependency_hashes.items():
        if deep.prior.file_sha(path) != sha:
            raise ValueError("horizon_dependency_changed")
    write(output / "single-horizon-protocol.json", dict(code_sha256=code_sha,
        code_input_sha256s=dependency_hashes,
        parent_projection_sha256=projection["artifact_content_sha256"],
        horizons=[3, 5, 10, 20, 30, 60], sequence_rules=BAR_RULES, static_rules=STATIC_RULES,
        minimum_train_comparable=10, minimum_train_symbols=5, minimum_coverage_pct=80,
        pristine_holdout=False, post_held_horizon_selection_forbidden=True))
    for item in projection["source_manifest"]:
        if deep.prior.file_sha(item["path"]) != item["sha256"]:
            raise ValueError("completed_phase_source_changed")
    result = single_horizon_validation(projection["rows"])
    write(output / "single-horizon-results.json", dict(folds=result,
        parent_projection_sha256=projection["artifact_content_sha256"], code_sha256=code_sha,
        pristine_holdout=False, post_held_horizon_selection_forbidden=True))
    write(output / "retained-path-diagnostics.json", dict(groups=retained_path_diagnostics(projection["rows"]),
        parent_projection_sha256=projection["artifact_content_sha256"], code_sha256=code_sha))
    if policy_hashes(root) != before or deep.prior.file_sha(__file__) != code_sha:
        raise ValueError("policy_or_code_changed")
    for path, sha in dependency_hashes.items():
        if deep.prior.file_sha(path) != sha:
            raise ValueError("horizon_dependency_changed_during_run")
    for item in projection["source_manifest"]:
        if deep.prior.file_sha(item["path"]) != item["sha256"]:
            raise ValueError("completed_phase_source_changed_during_run")
    write(output / "single-horizon-receipt.json", dict(code_sha256=code_sha,
        parent_projection_sha256=projection["artifact_content_sha256"], policy_hash_count=len(before),
        policy_hash_mismatches=0, elapsed_seconds=time.monotonic() - started,
        registered_policy_promotion_count=0, pristine_holdout=False))
    print("single horizon phase complete", time.monotonic() - started, flush=True)


def extract(root, output):
    previous_path = root / "tmp/deep-retained-policy-research-20261003/full-observations.json"
    previous = C.read(previous_path)
    if not C.valid(previous):
        raise ValueError("invalid_parent_projection")
    index = {r["trace"]: r for r in previous["rows"]}
    result, seen = [], set()
    for item in previous["source_manifest"]:
        path = Path(item["path"])
        if deep.prior.file_sha(path) != item["sha256"]:
            raise ValueError("frozen_source_changed")
        print("extract", path.name, flush=True)
        for raw in deep.prior.stream_array(path):
            trace = raw.get("decision_trace_id")
            if trace not in index:
                continue
            if trace in seen:
                raise ValueError("duplicate_retained_trace")
            seen.add(trace)
            result.append(extend_row(raw, index[trace]))
        if deep.prior.file_sha(path) != item["sha256"]:
            raise ValueError("source_changed_during_extraction")
    if seen != set(index):
        raise ValueError("retained_population_lost")
    rows = sequence_rows(result)
    write(output / "projection.json", dict(rows=rows, source_manifest=previous["source_manifest"],
        parent_sha256=previous["artifact_content_sha256"], extraction_code_sha256=deep.prior.file_sha(__file__)))
    return rows


def policy_hashes(root):
    paths = C.read(root / "tmp/integrated-workspace-baseline-20261003/policy-hashes.before.json")
    return {path: deep.prior.file_sha(root / path) for path in paths}


def run(root, output, reuse=False):
    started = time.monotonic()
    code_paths = (Path(__file__), Path(deep.__file__), Path(deep.prior.__file__),
                  Path(deep.prior.calibration.__file__), Path(C.__file__),
                  Path(deep.prior.strategy.__file__), Path(deep.prior.evidence.__file__),
                  Path(deep.prior.runtime_policy.__file__))
    inputs = {str(p): deep.prior.file_sha(p) for p in code_paths}
    for name in ("auxiliary-result.json", "auxiliary-research-observations.json"):
        p = root / "tmp/retained-source-policy-research-20261003" / name
        inputs[str(p)] = deep.prior.file_sha(p)
    for name in ("full-observations.json", "observations.json"):
        p = root / "tmp/deep-retained-policy-research-20261003" / name
        inputs[str(p)] = deep.prior.file_sha(p)
    before = policy_hashes(root)
    write(output / "protocol.json", dict(code_input_sha256s=inputs, dates=deep.DAYS,
        sequence_rules=RULES, static_rules=STATIC_RULES, objectives=OBJECTIVES,
        minimum_train_comparable=10, minimum_train_symbols=5, minimum_coverage_pct=80,
        sequence_gap_sec=[15, 180], maximum_history_sec=360,
        policy_hashes_before=before, pristine_holdout=False))
    if reuse:
        cached = C.read(output / "projection.json")
        if not C.valid(cached) or cached.get("extraction_code_sha256") != inputs[str(Path(__file__))]:
            raise ValueError("unreviewed_projection_code_or_content")
        for item in cached["source_manifest"]:
            if deep.prior.file_sha(item["path"]) != item["sha256"]:
                raise ValueError("projection_source_changed")
        rows = cached["rows"]
    else:
        rows = extract(root, output)
    write(output / "classification.json", classification(rows))
    eligible = [r for r in rows if r["sequence_status"] in {"two_snapshots", "three_snapshots"}]
    results = {}
    for held_day, train_days in ((deep.DAYS[1], deep.DAYS[:1]), (deep.DAYS[2], deep.DAYS[:2])):
        population = anchors(eligible, 600)
        print("chronological", held_day, len(population), flush=True)
        results[held_day] = fold(population, train_days, held_day)
    # Same fixed selected rules under coarser anchors; do not reselect on held data.
    sensitivity = {}
    for spacing in (3600, 86400):
        population = anchors(eligible, spacing)
        training = [r for r in population if r["day"] in deep.DAYS[:2]]
        held = [r for r in population if r["day"] == deep.DAYS[-1]]
        sensitivity[str(spacing)] = {}
        for name, result in results[deep.DAYS[-1]]["objectives"].items():
            selected = result["selected"]
            if selected:
                definition = selected["definition"]
                sensitivity[str(spacing)][name] = {str(h): dict(
                    train=metric(training, selection_mask(training, definition), h),
                    held=metric(held, selection_mask(held, definition), h)) for h in HORIZONS}
    write(output / "machine-results.json", dict(folds=results, anchor_sensitivity=sensitivity,
        sequence_counts=dict(Counter(r["sequence_status"] for r in rows)),
        full_population_baseline={day: {str(h): metric([r for r in rows if r["day"] == day],
            [True] * sum(r["day"] == day for r in rows), h) for h in HORIZONS} for day in deep.DAYS},
        sequence_population=len(eligible), original_population=len(rows), pristine_holdout=False))
    write(output / "auxiliary-results.json", auxiliary(root, rows))
    for path, sha in inputs.items():
        if deep.prior.file_sha(path) != sha:
            raise ValueError("research_input_changed")
    if policy_hashes(root) != before:
        raise ValueError("runtime_policy_changed")
    write(output / "execution-receipt.json", dict(code_input_sha256s=inputs,
        policy_hash_count=len(before), policy_hash_mismatches=0, elapsed_seconds=time.monotonic() - started,
        actual_profit_validated=False, registered_policy_promotion_count=0, pristine_holdout=False))
    print("complete", time.monotonic() - started, flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-projection", action="store_true")
    parser.add_argument("--phase", choices=("snapshots", "completed-bars", "horizons"), default="snapshots")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if not output.is_relative_to(root / "tmp"):
        raise ValueError("output_must_be_workspace_tmp")
    output.mkdir(parents=True, exist_ok=True)
    if args.phase == "horizons":
        run_horizons(root, output)
    elif args.phase == "completed-bars":
        run_bars(root, output)
    else:
        run(root, output, args.reuse_projection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
