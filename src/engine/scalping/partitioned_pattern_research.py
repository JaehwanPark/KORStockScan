"""Offline Samsung/other-symbol path research over frozen retained sources.

This module is not a runtime selector. A price-pattern signal is never an order
or a substitute for a native opportunity, machine guard or auxiliary response.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
import itertools
from pathlib import Path
import resource
import time

import numpy as np

from src.engine.scalping import entry_policy_confirmation_research as R
from src.engine.scalping import entry_policy_path_sequence_research as Q

C, P, D = R.C, R.prior, Q.deep
DAYS = D.DAYS
HORIZONS = (3, 5, 10, 20, 30, 60)
OBJECTIVES = {"short": (3, 5, 10), "medium": (10, 20, 30), "long": (20, 30, 60)}
AUTHORITY = {**D.AUTHORITY, "policy_publication_forbidden": True,
             "pristine_holdout": False, "registered_kernel": False,
             "primary_decision_metric": "equal_symbol_day_fixed_horizon_net_cf",
             "sample_floor": "research_only_samsung_3_signals_other_10_signals_5_symbols_80pct_coverage",
             "source_quality_gate": "sealed_retained_sources_exact_partition_clock_route_cost",
             "native_support_increment": 0}
PATTERNS = ("decline_turn", "trend_pullback", "range_reclaim", "higher_low",
            "breakout", "efficient_trend", "lower_range_rebound", "compression_release")
CONFIRMATIONS = ("none", "positive_flow", "flow_price", "depth_flow", "flow_improving")


def write(path, body):
    C.write(path, C.sealed({**body, **AUTHORITY}))


def checked(path, maximum=80 * 1024 * 1024):
    if path.stat().st_size > maximum:
        raise ValueError("source_exceeds_declared_read_budget")
    value = C.read(path)
    if not C.valid(value):
        raise ValueError("source_seal_invalid:" + str(path))
    return value


def partition(symbol):
    if not isinstance(symbol, str) or len(symbol) != 6 or not symbol.isascii() or not symbol.isdigit():
        return "unknown"
    return "samsung" if symbol == "005930" else "non_samsung"


def clock(row):
    value = datetime.fromisoformat(row["ts"])
    if value.tzinfo is None or value.astimezone(C.KST).date().isoformat() != row["day"]:
        raise ValueError("invalid_observation_clock")
    return value


def past_features(row, bars, stamps):
    """Only complete past bars; each lookback has its own coverage flag."""
    now = clock(row)
    end = bisect_right(stamps, now - timedelta(seconds=60))
    result = {}
    if not end:
        return result
    for length in (3, 5, 10, 20):
        if end < length + 1:
            continue
        window, times = bars[end - length - 1:end], stamps[end - length - 1:end]
        if ((now - times[-1]).total_seconds() > 150
            or (end > length + 1 and stamps[end - length - 2] == times[0])
            or any((b - a).total_seconds() != 60 for a, b in zip(times, times[1:]))):
            continue
        valid = True
        for bar, stamp in zip(window, times, strict=True):
            prices = [D.finite(bar.get(k)) for k in ("open", "high", "low", "close")]
            valid &= (stamp.date().isoformat() == row["day"]
                and (bar.get("stock_code"), bar.get("effective_venue"), bar.get("session_bucket"), bar.get("source_request_code"))
                    == (row["symbol"], "KRX", "KRX_REGULAR", row["route"])
                and bar.get("completed_bar_only") is True
                and bar.get("source_quality") == "pass_completed_ka10080_bar"
                and all(x is not None and x > 0 for x in prices))
            if not valid or not prices[2] <= min(prices[0], prices[3]) <= max(prices[0], prices[3]) <= prices[1]:
                valid = False
                break
        if not valid:
            continue
        closes = np.array([b["close"] for b in window], dtype=float)
        hi, lo = max(b["high"] for b in window), min(b["low"] for b in window)
        travel = float(np.abs(np.diff(closes)).sum())
        result[str(length)] = dict(
            ret=100 * (closes[-1] / closes[0] - 1), ret_last=100 * (closes[-1] / closes[-2] - 1),
            range_pct=100 * (hi / lo - 1), drawdown=100 * (closes[-1] / hi - 1),
            location=(closes[-1] - lo) / (hi - lo) if hi > lo else None,
            efficiency=(closes[-1] - closes[0]) / travel if travel else 0.,
            reclaim=bool(closes[-2] <= float(np.mean(closes[:-1])) and closes[-1] > float(np.mean(closes[1:]))),
            breakout=bool(closes[-1] > max(b["high"] for b in window[:-1])),
            higher_low=bool(window[-1]["low"] > window[-2]["low"] and closes[-1] > closes[-2]),
            compression_release=bool(window[-2]["high"] - window[-2]["low"] < float(np.mean([b["high"] - b["low"] for b in window[:-2]]))
                and closes[-1] > window[-2]["high"]),
            oldest_at=times[0].isoformat(), latest_at=times[-1].isoformat(),
        )
    return result


def bind_identity(raw, row):
    if (raw.get("stock_code"), raw.get("source_date"), raw.get("decision_ts"), raw.get("bundle_sha256"), raw.get("outcome_request_code")) != (
            row["symbol"], row["day"], row["ts"], row["bundle"], row["route"]):
        raise ValueError("raw_projection_identity_changed")
    if (raw.get("effective_venue"), raw.get("session_bucket")) != ("KRX", "KRX_REGULAR"):
        raise ValueError("raw_scope_mismatch")
    try:
        native = list(P.opportunity_identity(raw))
    except ValueError:
        native = None
    return dict(watch_origin=raw.get("watch_origin"), native=native,
                watch_admission_id=raw.get("watch_admission_id"), watch_generation_id=raw.get("watch_generation_id"),
                evaluation_attempt_id=raw.get("evaluation_attempt_id"), ai_decision_trace_id=raw.get("ai_decision_trace_id"),
                machine_reason=raw.get("machine_reason"), source_lane=raw.get("source_lane"))


def cadence(rows):
    groups = defaultdict(list)
    for row in rows:
        native = row.get("identity", {}).get("native")
        if native:
            groups[tuple(native)].append(row)
    gaps = []
    for group in groups.values():
        stamps = sorted(clock(row) for row in group)
        gaps.extend((b - a).total_seconds() for a, b in zip(stamps, stamps[1:]) if b > a)
    return dict(native_groups=len(groups), rows_with_native=sum(map(len, groups.values())), adjacent_pairs=len(gaps),
                minimum_sec=min(gaps) if gaps else None,
                median_sec=float(np.median(gaps)) if gaps else None,
                pairs_within={str(s): sum(g <= s for g in gaps) for s in (60, 120, 180, 300, 600)},
                repeat_60_status="evaluable_exposure" if any(g <= 60 for g in gaps) else "not_evaluable_no_adjacent_exposure")


def prepare(root, output):
    source = root / "tmp/path-sequence-validation-20261003/projection.json"
    original = checked(source)
    inputs = {str(source): P.file_sha(source)}
    rows = deepcopy(original["rows"])
    by_trace = {r["trace"]: r for r in rows}
    if len(by_trace) != len(rows):
        raise ValueError("duplicate_trace")
    seen = set()
    for item in original["source_manifest"]:
        path = Path(item["path"])
        if path.stat().st_size != item["bytes"] or P.file_sha(path) != item["sha256"]:
            raise ValueError("frozen_raw_changed")
        inputs[str(path)] = item["sha256"]
        print("identity pass", path.name, flush=True)
        for raw in P.stream_array(path):
            key = raw.get("decision_trace_id")
            if key not in by_trace:
                continue
            if key in seen:
                raise ValueError("duplicate_raw_trace")
            seen.add(key)
            by_trace[key]["identity"] = bind_identity(raw, by_trace[key])
        if P.file_sha(path) != inputs[str(path)]:
            raise ValueError("raw_changed_during_read")
    if seen != set(by_trace):
        raise ValueError("projection_trace_lost")
    for day in DAYS:
        path = root / "data/report/machine_completed_price_source" / f"machine_completed_price_source_{day}.json"
        inputs[str(path)] = P.file_sha(path)
        bars = C.read(path)
        if (not P.calibration._artifact_content_sha256_valid(bars)
            or bars.get("schema") != "machine_completed_price_source_v2" or bars.get("source_date") != day):
            raise ValueError("completed_bar_source_invalid")
        groups = defaultdict(list)
        for bar in bars["prices"]:
            if (bar.get("effective_venue"), bar.get("session_bucket")) == ("KRX", "KRX_REGULAR"):
                groups[(bar.get("stock_code"), bar.get("source_request_code"))].append(bar)
        indexed = {}
        for key, group in groups.items():
            group.sort(key=lambda b: b["timestamp"])
            indexed[key] = (group, [datetime.fromisoformat(b["timestamp"]) for b in group])
        for row in rows:
            if row["day"] == day:
                group, stamps = indexed.get((row["symbol"], row["route"]), ([], []))
                row["past"] = past_features(row, group, stamps)
        if P.file_sha(path) != inputs[str(path)]:
            raise ValueError("bar_source_changed_during_read")
        print("past bar features", day, flush=True)
    # Original source receipts remain bound; keep only fields used downstream.
    keep = ("trace", "day", "symbol", "ts", "bundle", "route", "features", "types", "parent_action",
            "binary", "path_state", "gross", "cost", "sequence", "identity", "past", "observed_price")
    compact = [{k: row.get(k) for k in keep} for row in rows]
    write(output / "projection.json", dict(rows=compact, source_sha256s=inputs,
        code_sha256=P.file_sha(__file__), parent_projection_sha256=original["artifact_content_sha256"]))
    return compact


def shape(row, name, length):
    b = row.get("past", {}).get(str(length), {})
    short = row.get("past", {}).get("3", {})
    if not b:
        return False
    if name == "decline_turn":
        return b["ret"] < 0 and short.get("ret", -1) > 0 and b["ret_last"] > 0
    if name == "trend_pullback":
        return b["ret"] > 0 and short.get("ret", 1) <= 0 and b["ret_last"] > 0
    if name == "range_reclaim":
        return b["reclaim"]
    if name == "higher_low":
        return b["higher_low"]
    if name == "breakout":
        return b["breakout"]
    if name == "efficient_trend":
        return b["efficiency"] >= .5 and b["ret_last"] > 0
    if name == "lower_range_rebound":
        return b["location"] is not None and b["location"] <= .5 and b["ret_last"] > 0
    if name == "compression_release":
        return b["compression_release"]
    raise ValueError("unknown_pattern")


def confirms(row, name):
    f = row["features"]
    positive = Q.positive
    flow = positive(f.get("net_aggressive_delta_10t"))
    if name == "none":
        return True
    if name == "positive_flow":
        return flow
    if name == "flow_price":
        return flow and positive(f.get("price_change_10t_pct"))
    if name == "depth_flow":
        return flow and D.finite(f.get("top3_depth_ratio")) is not None and f["top3_depth_ratio"] >= 1
    if name == "flow_improving":
        return flow and positive((row.get("sequence") or {}).get("delta_change"))
    raise ValueError("unknown_confirmation")


def selected(row, spec):
    if partition(row["symbol"]) != spec["partition"]:
        return False
    if any(row["types"].get(k) != v for k, v in spec["scope"].items()):
        return False
    filt = spec.get("filter")
    if filt:
        value = D.finite(row["features"].get(filt["feature"]))
        if value is None or not (value <= filt["value"] if filt["op"] == "le" else value >= filt["value"]):
            return False
    return shape(row, spec["pattern"], spec["length"]) and confirms(row, spec["confirmation"])


def definitions(training, group):
    """No outcome, held row or other partition participates in definition."""
    if any(partition(r["symbol"]) != group for r in training):
        raise ValueError("cross_partition_training")
    scopes = [{}]
    for key in ("family", "phase", "volatility_band"):
        for value in sorted({r["types"].get(key) for r in training} - {None, "UNKNOWN"}):
            support = [r for r in training if r["types"].get(key) == value]
            if len(support) >= (8 if group == "samsung" else 30):
                scopes.append({key: value})
    if group == "non_samsung":
        for phase, volatility in sorted({(r["types"].get("phase"), r["types"].get("volatility_band")) for r in training}, key=str):
            support = [r for r in training if (r["types"].get("phase"), r["types"].get("volatility_band")) == (phase, volatility)]
            if phase and volatility and len(support) >= 30 and len({r["symbol"] for r in support}) >= 5:
                scopes.append(dict(phase=phase, volatility_band=volatility))
    filters = [None]
    if group == "samsung":
        for feature in ("spread_bp", "curr_vs_micro_vwap_bp", "top3_depth_ratio", "distance_from_day_high_pct"):
            values = [r["features"][feature] for r in training if D.finite(r["features"].get(feature)) is not None]
            if len(values) >= 8:
                for value in sorted(set(float(np.quantile(values, q)) for q in (.25, .5, .75))):
                    filters.extend(dict(feature=feature, op=op, value=value) for op in ("le", "ge"))
    result = []
    for pattern, length, confirm, scope in itertools.product(PATTERNS, (5, 10, 20), CONFIRMATIONS, scopes):
        # Numeric Samsung refinements stay global: never unlimited typed pairs.
        for filt in filters if not scope else [None]:
            spec = dict(partition=group, pattern=pattern, length=length, confirmation=confirm, scope=scope, filter=filt)
            result.append({**spec, "id": C.digest(spec)[:16]})
    return sorted(result, key=lambda s: (bool(s["filter"]) + len(s["scope"]) + (s["confirmation"] != "none"), s["id"]))


def mask_matrix(rows, specs):
    return np.asarray([[selected(row, spec) for row in rows] for spec in specs], dtype=bool).reshape(len(specs), len(rows))


def nonoverlap(rows, masks, horizon):
    """First available signal per symbol; missing outcome never frees a slot."""
    result = np.zeros_like(masks)
    last = {}
    for i in sorted(range(len(rows)), key=lambda i: (rows[i]["ts"], rows[i]["trace"])):
        row = rows[i]
        # Different admission IDs cannot create overlapping capital in a symbol.
        key = (row["day"], row["symbol"])
        stamp = clock(row).timestamp()
        previous = last.setdefault(key, np.full(masks.shape[0], -np.inf))
        chosen = masks[:, i] & (stamp - previous >= horizon * 60)
        result[:, i] = chosen
        previous[chosen] = stamp
    return result


def values(rows, horizon):
    return np.array([D.net_at(r, horizon) if Q.horizon_status(r, horizon) == "comparable" else np.nan for r in rows], dtype=float)


def statistics(rows, masks, horizon, outcome_values=None):
    val = values(rows, horizon) if outcome_values is None else outcome_values
    valid = masks & np.isfinite(val)
    counts = valid.sum(axis=1)
    total = (valid * np.nan_to_num(val)).sum(axis=1)
    grouped, group_count = np.zeros(len(masks)), np.zeros(len(masks))
    symbol_presence, days = {}, {}
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[(row["day"], row["symbol"])].append(i)
    for (day, symbol), positions in sorted(groups.items()):
        ids = np.array(positions)
        sub = valid[:, ids]
        n = sub.sum(axis=1)
        subtotal = (sub * np.nan_to_num(val[ids])).sum(axis=1)
        grouped += np.divide(subtotal, n, out=np.zeros(len(masks)), where=n > 0)
        group_count += n > 0
        symbol_presence[symbol] = symbol_presence.get(symbol, np.zeros(len(masks), dtype=bool)) | (n > 0)
        days[day] = days.get(day, np.zeros(len(masks), dtype=bool)) | (n > 0)
    return dict(selected=masks.sum(axis=1), comparable=counts,
        mean=np.divide(total, counts, out=np.full(len(masks), np.nan), where=counts > 0),
        cluster_mean=np.divide(grouped, group_count, out=np.full(len(masks), np.nan), where=group_count > 0),
        symbols=np.sum(list(symbol_presence.values()), axis=0) if symbol_presence else np.zeros(len(masks)),
        dates=np.sum(list(days.values()), axis=0) if days else np.zeros(len(masks)))


def fit(rows, specs, group, horizons, masks=None):
    masks = mask_matrix(rows, specs) if masks is None else masks
    metrics, accepted = {}, np.ones(len(specs), dtype=bool)
    for h in horizons:
        metrics[h] = statistics(rows, nonoverlap(rows, masks, h), h)
        m = metrics[h]
        accepted &= ((m["comparable"] >= (3 if group == "samsung" else 10))
            & (m["symbols"] >= (1 if group == "samsung" else 5))
            & (m["dates"] >= len({r["day"] for r in rows}))
            & (m["comparable"] >= .8 * m["selected"]))
    score = np.min(np.array([m["cluster_mean"] for m in metrics.values()]), axis=0)
    supported = np.flatnonzero(accepted & np.isfinite(score))
    # Stable order already prefers simpler hypotheses. No held arguments here.
    winner = int(supported[np.argmax(score[supported])]) if len(supported) else None
    return winner, metrics, score, supported


def metric(rows, mask, horizon):
    val = values(rows, horizon)
    ids = np.flatnonzero(mask & np.isfinite(val))
    m = statistics(rows, mask.reshape(1, -1), horizon)
    selected_rows = [rows[i] for i in np.flatnonzero(mask)]
    returns = val[ids]
    native = {tuple(rows[i]["identity"]["native"]) for i in ids if rows[i].get("identity", {}).get("native")}
    basic = {k: (float(v[0]) if k in ("mean", "cluster_mean") else int(v[0])) for k, v in m.items()}
    return {**{k: None if isinstance(v, float) and not np.isfinite(v) else v for k, v in basic.items()},
        "positive": int((returns > 0).sum()), "worst": float(returns.min()) if len(returns) else None,
        "p10": float(np.quantile(returns, .1)) if len(returns) else None,
        "extra_cost_010_mean": float(returns.mean() - .1) if len(returns) else None,
        "statuses": dict(Counter(Q.horizon_status(r, horizon) for r in selected_rows)),
        "path_states": dict(Counter(r["path_state"] for r in selected_rows)),
        "parent_actions": dict(Counter(r["parent_action"] for r in selected_rows)),
        "native_groups": len(native), "native_promotion_support_increment": 0,
        "traces": [r["trace"] for r in selected_rows]}


def evaluated(rows, spec):
    masks = mask_matrix(rows, [spec])
    return {str(h): metric(rows, nonoverlap(rows, masks, h)[0], h) for h in HORIZONS}


def baseline(rows, parent_only=False):
    masks = np.array([[r["parent_action"] == "ENTER_NOW" or not parent_only for r in rows]], dtype=bool)
    return {str(h): metric(rows, nonoverlap(rows, masks, h)[0], h) for h in HORIZONS}


def signal_runs(rows, spec, max_gap=180):
    """Causal observation runs, NOT independent lifecycle/native opportunities."""
    previous, runs = {}, []
    for row in sorted(rows, key=lambda r: (r["ts"], r["trace"])):
        key = (row["day"], row["symbol"], row["bundle"], row["route"])
        hit = selected(row, spec)
        old = previous.get(key)
        stamp = clock(row).timestamp()
        native = row["identity"].get("native")
        continuing = (hit and old and old["hit"] and 0 < stamp - old["stamp"] <= max_gap
                      and native == old["native"] and row["types"].get("phase") == old["phase"])
        if hit:
            if continuing:
                run = old["run"]
            else:
                run = dict(day=row["day"], symbol=row["symbol"], first_ts=row["ts"], last_ts=row["ts"],
                           first_trace=row["trace"], native=native, traces=[], first_parent_enter_ts=None)
                runs.append(run)
            run["last_ts"] = row["ts"]
            run["traces"].append(row["trace"])
            if row["parent_action"] == "ENTER_NOW" and run["first_parent_enter_ts"] is None:
                run["first_parent_enter_ts"] = row["ts"]
        else:
            run = None
        previous[key] = dict(hit=hit, stamp=stamp, native=native, phase=row["types"].get("phase"), run=run)
    starts = {r["first_trace"] for r in runs}
    masks = np.array([[r["trace"] in starts for r in rows]], dtype=bool)
    return dict(boundary="causal_signal_false_phase_native_or_observation_gap_not_lifecycle", max_gap_sec=max_gap,
        runs=runs, native_promotion_support_increment=0,
        first_signal_horizons={str(h): metric(rows, nonoverlap(rows, masks, h)[0], h) for h in HORIZONS})


def repeat_mask(rows, spec, max_gap):
    """Two actual consecutive same-native observations; no inferred ticks."""
    previous, pairs = {}, 0
    mask = np.zeros((1, len(rows)), dtype=bool)
    for i in sorted(range(len(rows)), key=lambda i: (rows[i]["ts"], rows[i]["trace"])):
        row = rows[i]
        key = (row["day"], row["symbol"], row["bundle"], row["route"])
        identity = (row["identity"].get("native"), row["types"].get("phase"))
        stamp, hit = clock(row).timestamp(), selected(row, spec)
        old = previous.get(key)
        adjacent = bool(identity[0] and old and identity == old["identity"] and 0 < stamp - old["stamp"] <= max_gap)
        pairs += adjacent
        mask[0, i] = bool(adjacent and hit and old["hit"])
        previous[key] = dict(identity=identity, stamp=stamp, hit=hit)
    return mask, dict(adjacent_native_phase_pairs=pairs, confirmed_signals=int(mask.sum()),
        status="evaluable_exposure" if pairs else "not_evaluable_no_adjacent_exposure",
        max_gap_sec=max_gap, native_promotion_support_increment=0)


def permutation_check(rows, specs, masks, group, horizons, observed, iterations=99):
    """Exploratory max-search check. Rotate entire ordered symbol-day blocks.

    Circular rotation preserves each day's outcome trajectory and cross-horizon
    association, but is not an independent holdout or proof of stationarity.
    """
    if observed is None or not np.isfinite(observed):
        return dict(status="not_evaluable", iterations=0)
    rng = np.random.default_rng(1003)
    groups = [np.array(sorted([i for i, r in enumerate(rows) if (r["day"], r["symbol"]) == key], key=lambda i: rows[i]["ts"]))
              for key in sorted({(r["day"], r["symbol"]) for r in rows})]
    nm = {h: nonoverlap(rows, masks, h) for h in horizons}
    vals = {h: values(rows, h) for h in horizons}
    maxima = []
    for _ in range(iterations):
        order = np.arange(len(rows))
        for ids in groups:
            if len(ids) > 1:
                order[ids] = np.roll(ids, int(rng.integers(1, len(ids))))
        scores, ok = [], np.ones(len(specs), dtype=bool)
        for h in horizons:
            m = statistics(rows, nm[h], h, vals[h][order])
            ok &= ((m["comparable"] >= (3 if group == "samsung" else 10))
                & (m["symbols"] >= (1 if group == "samsung" else 5))
                & (m["dates"] >= len({r["day"] for r in rows})) & (m["comparable"] >= .8 * m["selected"]))
            scores.append(m["cluster_mean"])
        score = np.min(scores, axis=0)
        possible = score[ok & np.isfinite(score)]
        maxima.append(float(possible.max()) if len(possible) else None)
    usable = [v for v in maxima if v is not None]
    return dict(status="exploratory_circular_block_max_search", iterations=iterations,
                valid_iterations=len(usable), observed_score=observed,
                adjusted_tail_fraction=(1 + sum(v >= observed for v in usable)) / (1 + len(usable)),
                null_max_p95=float(np.quantile(usable, .95)) if usable else None,
                limitation="reused_dates_nonstationary_market_not_confirmatory_p_value")


def fold(rows, group, train_days, held_day, output):
    train = [r for r in rows if r["day"] in train_days]
    held = [r for r in rows if r["day"] == held_day]
    if not train or not held or any(partition(r["symbol"]) != group for r in rows):
        raise ValueError("invalid_partition_or_fold")
    specs = definitions(train, group)
    masks = mask_matrix(train, specs)
    # Deduplicate only training behavior, keeping declared simplest first.
    seen, indices = set(), []
    for i, vector in enumerate(masks):
        key = np.packbits(vector).tobytes()
        if vector.any() and key not in seen:
            seen.add(key); indices.append(i)
    all_count = len(specs)
    specs, masks = [specs[i] for i in indices], masks[indices]
    write(output / f"candidates-{group}-{held_day}.json", dict(partition=group, train_days=train_days,
        held_day=held_day, raw_definition_count=all_count, candidate_count=len(specs), candidates=specs,
        training_traces=[r["trace"] for r in train], selection_uses_held_labels=False))
    result = dict(raw_definitions=all_count, unique_train_vectors=len(specs), train_rows=len(train), held_rows=len(held),
        baselines=dict(all_observations=dict(train=baseline(train), held=baseline(held)),
                       parent_enter=dict(train=baseline(train, True), held=baseline(held, True))), objectives={})
    frozen = {}
    for name, horizons in OBJECTIVES.items():
        winner, metrics, scores, supported = fit(train, specs, group, horizons, masks)
        frozen[name] = dict(spec=specs[winner] if winner is not None else None,
            supported=len(supported), positive_training=int(sum(scores[i] > 0 for i in supported)),
            train_score=float(scores[winner]) if winner is not None else None)
    # The immutable choice is written before evaluating held outcomes.
    write(output / f"selection-{group}-{held_day}.json", dict(train_days=train_days, held_day=held_day, selections=frozen))
    for name, item in frozen.items():
        spec = item["spec"]
        if spec is None:
            result["objectives"][name] = item
            continue
        horizons = OBJECTIVES[name]
        train_result, held_result = evaluated(train, spec), evaluated(held, spec)
        chosen = [r for r in train if selected(r, spec)]
        counts = Counter(r["symbol"] for r in chosen)
        omits = sorted(counts, key=lambda s: (-counts[s], s))[:5] if group == "non_samsung" else []
        sensitivity = []
        for symbol in omits:
            keep = [i for i, r in enumerate(train) if r["symbol"] != symbol]
            reduced = [train[i] for i in keep]
            winner, _, _, _ = fit(reduced, specs, group, horizons, masks[:, keep])
            sensitivity.append(dict(omitted_symbol=symbol, spec=specs[winner] if winner is not None else None,
                held=evaluated(held, specs[winner]) if winner is not None else None))
        # Adjacent lookback lengths are predetermined, never a held-based reselect.
        adjacent = [{**spec, "length": n} for n in (5, 10, 20) if n != spec["length"]]
        result["objectives"][name] = {**item, "train": train_result, "held": held_result,
            "held_causal_signal_runs": signal_runs(held, spec),
            "held_300sec_run_sensitivity": signal_runs(held, spec, 300) if group == "samsung" else None,
            "held_by_symbol": {s: evaluated([r for r in held if r["symbol"] == s], spec) for s in sorted({r["symbol"] for r in held if selected(r, spec)})},
            "train_by_day": {day: evaluated([r for r in train if r["day"] == day], spec) for day in train_days},
            "held_fixed_watch": evaluated([r for r in held if r["identity"].get("watch_origin") == "MAIN_FIXED_WATCH"], spec) if group == "samsung" else None,
            "leave_top_train_symbol_out": sensitivity,
            "lookback_sensitivity": {str(s["length"]): dict(train=evaluated(train, s), held=evaluated(held, s)) for s in adjacent},
            "max_search_null": permutation_check(train, specs, masks, group, horizons, item["train_score"]),
        }
        print("selected", group, held_day, name, item["train_score"], flush=True)
    return result


def census(rows):
    return dict(rows=len(rows), symbols=len({r["symbol"] for r in rows}),
        days=dict(Counter(r["day"] for r in rows)), origins=dict(Counter(r["identity"].get("watch_origin") or "unrecorded" for r in rows)),
        native_cadence=cadence(rows), path_states=dict(Counter(r["path_state"] for r in rows)),
        past_coverage={str(n): sum(str(n) in r["past"] for r in rows) for n in (3, 5, 10, 20)},
        horizon_coverage={str(h): dict(Counter(Q.horizon_status(r, h) for r in rows)) for h in HORIZONS},
        parent_actions=dict(Counter(r["parent_action"] for r in rows)))


def native_replay(root, rows, folds, *, fixed_watch=False):
    source = checked(root / "tmp/deep-retained-policy-research-20261003/native-snapshots.json")
    frozen = checked(root / "tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json")
    parent = frozen["parent_policy"]
    if R.S.digest(parent) != source["parent_sha256"]:
        raise ValueError("native_parent_mismatch")
    index = {r["trace"]: r for r in rows}
    result = {}
    for group in ("samsung", "non_samsung"):
        native = [r for r in source["rows"] if partition(r["stock_code"]) == group
                  and (not fixed_watch or group != "samsung" or r.get("watch_origin") == "MAIN_FIXED_WATCH")]
        prepared = [R.prepare(r, parent) for r in native]
        for row, item in zip(native, prepared, strict=True):
            row["comparison"]["incumbent_machine_action"] = item["decision"]["action"]
        group_result = {}
        for name, choice in folds[group][DAYS[-1]]["objectives"].items():
            spec = choice["spec"]
            if spec is None:
                continue
            actions, linked = [], []
            confirmation = dict(id="offline_retained_guard_adapter", recipe="family_setup_confirmation",
                flow_family="DEPTH_SUPPORTED", match=dict(venue="KRX", session_bucket="KRX_REGULAR"))
            for raw, item in zip(native, prepared, strict=True):
                row = index[raw["decision_trace_id"]]
                hit = selected(row, spec)
                adapted = R.prototype_decision(raw, parent, item, confirmation) if hit else item["decision"]
                actions.append(adapted["action"])
                if hit:
                    linked.append(dict(trace=row["trace"], day=row["day"], native=P.opportunity_identity(raw),
                        baseline=item["decision"]["action"], candidate=adapted["action"], reason=adapted["reason"]))
            by_day = {}
            for day in DAYS:
                ids = [i for i, row in enumerate(native) if row["source_date"] == day]
                by_day[day] = P.machine_summary(P.economy([native[i] for i in ids], [actions[i] for i in ids]))
            group_result[name] = dict(pattern_matches=linked, metrics=P.machine_summary(P.economy(native, actions)), by_day=by_day,
                note="pattern_filters_existing_guard_preserving_prototype_no_new_guard_bypass")
        result[group] = group_result
    return result


def run(root, output, projection):
    if (output / "result.json").exists() or list(output.glob("selection-*.json")):
        raise ValueError("output_already_frozen")
    start = time.monotonic()
    artifact = checked(projection)
    snapshot = projection.with_name("extraction-code.py")
    if not snapshot.exists() or P.file_sha(snapshot) != artifact["code_sha256"]:
        raise ValueError("projection_generator_receipt_missing")
    for path, sha in artifact["source_sha256s"].items():
        if P.file_sha(path) != sha:
            raise ValueError("frozen_input_changed:" + path)
    rows = artifact["rows"]
    if any(r["day"] not in DAYS or partition(r["symbol"]) == "unknown" for r in rows):
        raise ValueError("out_of_scope_row")
    before = Q.policy_hashes(root)
    code_files = [Path(__file__), Path(R.__file__), Path(Q.__file__), Path(D.__file__), Path(P.__file__), Path(C.__file__)]
    hashes = {str(p): P.file_sha(p) for p in code_files}
    write(output / "protocol.json", dict(code_sha256s=hashes, projection_sha256=P.file_sha(projection),
        projection_content_sha256=artifact["artifact_content_sha256"], dates=DAYS, objectives=OBJECTIVES,
        patterns=PATTERNS, confirmations=CONFIRMATIONS, immutable_partition_before_fitting=True,
        nonoverlap="same_symbol_day_fixed_horizon_first_signal_even_if_outcome_missing",
        null_iterations=99, null_seed=1003, reuse_dates_exploratory=True))
    folds, counts = {}, {}
    for group in ("samsung", "non_samsung"):
        population = [r for r in rows if partition(r["symbol"]) == group]
        counts[group] = census(population)
        folds[group] = {}
        for held, train in ((DAYS[1], DAYS[:1]), (DAYS[2], DAYS[:2])):
            print("fold", group, held, flush=True)
            folds[group][held] = fold(population, group, train, held, output)
    guard = native_replay(root, rows, folds)
    if Q.policy_hashes(root) != before or any(P.file_sha(path) != sha for path, sha in hashes.items()):
        raise ValueError("policy_or_research_code_changed")
    write(output / "result.json", dict(census=counts, folds=folds, native_guard_replay=guard,
        operating_policy_hashes_unchanged=len(before), wall_sec=time.monotonic() - start,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def single_fold(rows, group, train_days, held_day, specs, output, label):
    train = [r for r in rows if r["day"] in train_days]
    held = [r for r in rows if r["day"] == held_day]
    if any(partition(r["symbol"]) != group for r in rows):
        raise ValueError("single_fold_partition_mismatch")
    masks = mask_matrix(train, specs)
    choices = {}
    for h in HORIZONS:
        winner, _, scores, supported = fit(train, specs, group, (h,), masks)
        choices[str(h)] = dict(spec=specs[winner] if winner is not None else None,
            supported=len(supported), positive_training=int(sum(scores[i] > 0 for i in supported)),
            train_score=float(scores[winner]) if winner is not None else None)
    write(output / f"single-selection-{label}-{held_day}.json", dict(choices=choices, train_days=train_days,
        held_day=held_day, candidate_definitions_sha256=C.digest(specs), objectives=list(HORIZONS)))
    results = {}
    for h, choice in choices.items():
        spec = choice["spec"]
        if spec is None:
            results[h] = choice
            continue
        training, later = evaluated(train, spec), evaluated(held, spec)
        matches = [r for r in held if selected(r, spec)]
        selected_masks = nonoverlap(held, mask_matrix(held, [spec]), int(h))[0]
        picked = [r for r, hit in zip(held, selected_masks, strict=True) if hit]
        binary = [r["binary"] for r in picked if r.get("binary") is not None]
        # Fixed rule exclusion diagnostics do not reselect on held performance.
        leave_symbol = {}
        if group == "non_samsung":
            for symbol in sorted({r["symbol"] for r in matches}):
                subset = [r for r in held if r["symbol"] != symbol]
                leave_symbol[symbol] = evaluated(subset, spec)[h]
        null = (permutation_check(train, specs, masks, group, (int(h),), choice["train_score"])
                if choice["train_score"] > 0 else dict(status="no_positive_training_edge_not_tested"))
        if "adjusted_tail_fraction" in null:
            null["six_horizon_bonferroni_tail_bound"] = min(1., 6 * null["adjusted_tail_fraction"])
        results[h] = {**choice, "train": training, "held": later,
            "held_symbol_exclusion": leave_symbol, "max_search_null": null,
            "held_causal_signal_runs": signal_runs(held, spec),
            "held_declared_binary": dict(resolved=len(binary), positive=sum(v > 0 for v in binary),
                unresolved=len(picked) - len(binary), conditional_only=True),
            "train_by_day": {day: evaluated([r for r in train if r["day"] == day], spec) for day in train_days},
            "lookback_sensitivity": {str(n): dict(train=evaluated(train, {**spec, "length": n}),
                held=evaluated(held, {**spec, "length": n})) for n in (5, 10, 20)},
        }
        print("single horizon", label, held_day, h, choice["train_score"], flush=True)
    return dict(train_rows=len(train), held_rows=len(held), candidate_count=len(specs), selections=results)


def supplement(root, output, projection, previous):
    if (output / "result.json").exists() or list(output.glob("*selection*.json")):
        raise ValueError("supplement_output_already_frozen")
    artifact, original = checked(projection), checked(previous / "result.json")
    protocol = checked(previous / "protocol.json")
    if P.file_sha(projection) != protocol["projection_sha256"]:
        raise ValueError("supplement_projection_changed")
    snapshot = previous / "reviewed-research-code.py"
    if P.file_sha(snapshot) != protocol["code_sha256s"][str(Path(__file__).resolve())]:
        raise ValueError("original_research_receipt_missing")
    for path, sha in artifact["source_sha256s"].items():
        if P.file_sha(path) != sha:
            raise ValueError("supplement_source_changed")
    before = Q.policy_hashes(root)
    code_hash = P.file_sha(__file__)
    dependencies = [Path(m.__file__) for m in (R, Q, D, P, C, R.S, R.E, P.calibration)]
    dependencies += [root / "tmp/deep-retained-policy-research-20261003/native-snapshots.json",
                     root / "tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json",
                     previous / "result.json", projection]
    dependency_hashes = {str(path): P.file_sha(path) for path in dependencies}
    start = time.monotonic()
    rows = artifact["rows"]
    fixed = [r for r in rows if partition(r["symbol"]) == "samsung" and r["identity"].get("watch_origin") == "MAIN_FIXED_WATCH"]
    write(output / "protocol.json", dict(code_sha256=code_hash, predecessor_sha256=original["artifact_content_sha256"],
        projection_sha256=P.file_sha(projection), dependency_sha256s=dependency_hashes,
        fixed_watch_train_days=[DAYS[1]], fixed_watch_held_day=DAYS[2],
        single_horizons=HORIZONS, definition_changes=False,
        interpretation="additional_origin_and_horizon_validation_on_reused_dates_no_confirmatory_claim"))
    fixed_result = fold(fixed, "samsung", [DAYS[1]], DAYS[2], output)
    singles = {}
    for group in ("samsung", "non_samsung"):
        singles[group] = {}
        population = [r for r in rows if partition(r["symbol"]) == group]
        for held, train in ((DAYS[1], DAYS[:1]), (DAYS[2], DAYS[:2])):
            candidates = checked(previous / f"candidates-{group}-{held}.json")
            singles[group][held] = single_fold(population, group, train, held, candidates["candidates"], output, group)
    fixed_candidates = checked(output / f"candidates-samsung-{DAYS[2]}.json")
    singles["samsung_fixed_watch"] = {DAYS[2]: single_fold(fixed, "samsung", [DAYS[1]], DAYS[2],
        fixed_candidates["candidates"], output, "samsung_fixed_watch")}
    # Native adapters for each latest single horizon remain a separate gate.
    bridge_folds = {group: {DAYS[-1]: {"objectives": singles[group][DAYS[-1]]["selections"]}} for group in ("samsung", "non_samsung")}
    bridge = native_replay(root, rows, bridge_folds)
    fixed_bridge_folds = deepcopy(bridge_folds)
    fixed_bridge_folds["samsung"][DAYS[-1]]["objectives"] = singles["samsung_fixed_watch"][DAYS[-1]]["selections"]
    fixed_bridge = native_replay(root, rows, fixed_bridge_folds, fixed_watch=True)["samsung"]
    if (Q.policy_hashes(root) != before or P.file_sha(__file__) != code_hash
        or any(P.file_sha(path) != sha for path, sha in dependency_hashes.items())):
        raise ValueError("supplement_policy_or_code_changed")
    write(output / "result.json", dict(fixed_watch_census=census(fixed), fixed_watch_robust=fixed_result,
        single_horizons=singles, native_single_horizon_guard_replay=bridge,
        native_fixed_watch_guard_replay=fixed_bridge,
        operating_policy_hashes_unchanged=len(before), wall_sec=time.monotonic() - start,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def mixture_mask(rows, field, leaves):
    """One disjoint type leaf per row; union cannot count a row twice."""
    return np.array([[bool(leaves.get(row["types"].get(field))) and selected(row, leaves[row["types"][field]])
                      for row in rows]], dtype=bool)


def fit_mixture(training, group, specs, field, horizon):
    if any(partition(r["symbol"]) != group for r in training):
        raise ValueError("mixture_cross_partition")
    leaves, diagnostics = {}, {}
    for cell in sorted({r["types"].get(field) for r in training} - {None, "UNKNOWN"}):
        subset = [r for r in training if r["types"].get(field) == cell]
        if len({r["day"] for r in subset}) != len({r["day"] for r in training}):
            diagnostics[cell] = dict(status="training_date_missing")
            continue
        masks = mask_matrix(subset, specs)
        seen, ids = set(), []
        for i, vector in enumerate(masks):
            packed = np.packbits(vector).tobytes()
            if vector.any() and packed not in seen:
                seen.add(packed); ids.append(i)
        local_specs = [specs[i] for i in ids]
        winner, _, scores, supported = fit(subset, local_specs, group, (horizon,), masks[ids])
        score = float(scores[winner]) if winner is not None else None
        diagnostics[cell] = dict(defined=len(local_specs), supported=len(supported), train_score=score,
            status="positive_training_leaf" if score is not None and score > 0 else "no_positive_supported_leaf")
        if score is not None and score > 0:
            leaves[cell] = local_specs[winner]
    return leaves, diagnostics


def mixture_research(root, output, projection, previous):
    if (output / "result.json").exists() or list(output.glob("selection-*.json")):
        raise ValueError("mixture_output_already_frozen")
    source = checked(projection)
    primary = checked(previous / "result.json")
    protocol = checked(previous / "protocol.json")
    if P.file_sha(projection) != protocol["projection_sha256"]:
        raise ValueError("mixture_projection_changed")
    code_hash = P.file_sha(__file__)
    policies = Q.policy_hashes(root)
    rows = source["rows"]
    write(output / "protocol.json", dict(code_sha256=code_hash, projection_sha256=P.file_sha(projection),
        predecessor_sha256=primary["artifact_content_sha256"], fields=["family", "phase"], horizons=HORIZONS,
        training_only_positive_leaf=True, held_dates_reused=True,
        authority="research_price_signal_union_not_machine_guard_replacement"))
    result = {}
    for group in ("samsung", "non_samsung"):
        population = [r for r in rows if partition(r["symbol"]) == group]
        result[group] = {}
        for held_day, train_days in ((DAYS[1], DAYS[:1]), (DAYS[2], DAYS[:2])):
            train = [r for r in population if r["day"] in train_days]
            held = [r for r in population if r["day"] == held_day]
            # Reuse exactly the earlier outcome-free declared candidate grammar.
            specs = checked(previous / f"candidates-{group}-{held_day}.json")["candidates"]
            choices = {}
            for field in ("family", "phase"):
                for h in HORIZONS:
                    leaves, diagnostics = fit_mixture(train, group, specs, field, h)
                    choices[f"{field}:{h}"] = dict(field=field, horizon=h, leaves=leaves, diagnostics=diagnostics)
            write(output / f"selection-{group}-{held_day}.json", dict(choices=choices, train_days=train_days, held_day=held_day))
            folds = {}
            for key, choice in choices.items():
                field, h, leaves = choice["field"], choice["horizon"], choice["leaves"]
                train_mask = nonoverlap(train, mixture_mask(train, field, leaves), h)[0]
                held_mask = nonoverlap(held, mixture_mask(held, field, leaves), h)[0]
                folds[key] = {**choice, "train": metric(train, train_mask, h), "held": metric(held, held_mask, h),
                    "held_by_leaf": {cell: evaluated([r for r in held if r["types"].get(field) == cell], spec)[str(h)] for cell, spec in leaves.items()},
                    "held_baseline": baseline(held)[str(h)],
                    "max_search_null": "not_computed_for_mixture_exploratory_only"}
            result[group][held_day] = folds
            print("mixture", group, held_day, flush=True)
    if P.file_sha(__file__) != code_hash or Q.policy_hashes(root) != policies:
        raise ValueError("mixture_code_or_policy_changed")
    write(output / "result.json", dict(folds=result, operating_policy_hashes_unchanged=len(policies)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--supplement-from", type=Path)
    parser.add_argument("--mixture-from", type=Path)
    args = parser.parse_args(argv)
    root, output = args.workspace.resolve(), args.output.resolve()
    if not output.is_relative_to(root / "tmp") or output == root / "tmp":
        raise ValueError("offline_output_must_be_workspace_tmp_child")
    output.mkdir(parents=True, exist_ok=True)
    if args.prepare:
        if (output / "projection.json").exists():
            raise ValueError("projection_already_frozen")
        prepare(root, output)
    else:
        if args.projection is None:
            raise ValueError("frozen_projection_required")
        if args.supplement_from and args.mixture_from:
            raise ValueError("choose_one_research_mode")
        if args.mixture_from:
            mixture_research(root, output, args.projection.resolve(), args.mixture_from.resolve())
        elif args.supplement_from:
            supplement(root, output, args.projection.resolve(), args.supplement_from.resolve())
        else:
            run(root, output, args.projection.resolve())


if __name__ == "__main__":
    main()
