"""One causal replay for frozen manual variants; no new hypotheses or AI calls."""

from __future__ import annotations
from src.engine.scalping.continuous_reversal_source import iter_normalized_symbols

import copy
import gzip
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_cumulative_catalog as Q
from src.engine.scalping import reversal_cumulative_registration as G
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import reversal_extended_runtime as LIVE
from src.engine.scalping import reversal_operating_evaluation as E
from src.engine.scalping.reversal_cumulative_runtime import prefix_features
from src.engine.scalping.reversal_extended_state import State


def chronological_points(points):
    """A failed or unresolved first confirmation consumes the same window as a win."""
    unique = {}
    for point in points:
        key = point["opportunity_key"]
        if key in unique and unique[key] != point:
            raise ValueError("cumulative_statistical_key_conflict")
        unique[key] = point
    result, until = [], {}
    for p in sorted(
        unique.values(),
        key=lambda x: (
            x["day"],
            x["symbol"],
            x["route"],
            x["confirmation_epoch"],
            x["opportunity_key"],
        ),
    ):
        bucket = (p["day"], p["symbol"], p["route"])
        at = p["confirmation_epoch"]
        if type(at) not in (int, float) or not math.isfinite(at):
            raise ValueError("cumulative_confirmation_clock_invalid")
        if at < until.get(bucket, -math.inf):
            continue
        result.append(p)
        until[bucket] = at + G.STATISTICAL_WINDOW
    return result


def chronological_metric(points):
    value = E.metric(Counter(p["outcome"]["status"] for p in points))
    value["score"] = G.wilson_score(value["wins"], value["resolved"])
    return value


def scoring_metrics(records, configs, current, contract, store, *, research_only=False):
    """Read existing point objects once; the full table owns keys, projections only counts."""
    G.validate_scoring(contract, approved=not research_only)
    points = defaultdict(list)
    excluded = defaultdict(list)
    for p in records:
        sid = p["scope"]
        if sid not in contract["scopes"]:
            continue
        ids = {b for v in configs[sid].values() for b in v}
        if not any(p["truth"].get(b) == "TRUE" for b in ids):
            continue
        event, _ = store.get(p["snapshot_obj"])
        at, route = event.get("epoch"), sid.rsplit("|", 1)[1]
        try:
            clock_valid = (
                type(at) in (int, float)
                and math.isfinite(at)
                and datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul"))
                .date()
                .isoformat()
                == p["day"]
            )
        except (ValueError, OverflowError, OSError):
            clock_valid = False
        if (
            not clock_valid
            or event.get("symbol") != p["symbol"]
            or event.get("venue") != route
            or event.get("source_item") != p["symbol"] + "_AL"
            or p["outcome"].get("status")
            not in ("WIN", "FAIL_STOP", "FAIL_TIMEOUT", "UNRESOLVED")
        ):
            excluded[sid].append(p["opportunity_key"])
            continue
        points[sid].append(dict(p, confirmation_epoch=at, route=route))
    metrics, effects = {}, {}
    for sid in contract["scopes"]:
        selected = {}
        for name, ids in configs[sid].items():
            rows = [
                p for p in points[sid] if any(p["truth"].get(b) == "TRUE" for b in ids)
            ]
            seq = chronological_points(rows)
            selected[name] = {p["opportunity_key"]: p for p in seq}
            c = chronological_metric(seq)
            c.update(
                by_day={
                    d: chronological_metric([p for p in seq if p["day"] == d])
                    for d in sorted({p["day"] for p in points[sid]})
                },
                by_symbol={
                    v: chronological_metric([p for p in seq if p["symbol"] == v])
                    for v in sorted({p["symbol"] for p in seq})
                },
            )
            metrics[sid + "::" + name] = dict(
                E.metric(Counter(p["outcome"]["status"] for p in rows)),
                chronological=c,
                statistic_contract_sha256=P.digest(G.scoring_spec()),
                scoring_contract_sha256=contract["artifact_content_sha256"],
                statistic_source_complete=True,
                statistic_excluded_rows=len(excluded[sid]),
            )
        baseline = selected["CURRENT_NATIVE"]
        bykey = {p["opportunity_key"]: p for p in points[sid]}
        baseline_raw = {
            k
            for k, p in bykey.items()
            if any(p["truth"].get(b) == "TRUE" for b in current[sid])
        }
        for name, rows in selected.items():
            added, removed = sorted(rows.keys() - baseline.keys()), sorted(
                baseline.keys() - rows.keys()
            )
            ids = configs[sid][name]
            addition = [
                p
                for k, p in bykey.items()
                if k not in baseline_raw
                and any(p["truth"].get(b) == "TRUE" for b in ids)
            ]
            variant_raw = {
                k
                for k, p in bykey.items()
                if any(p["truth"].get(b) == "TRUE" for b in ids)
            }
            effects[sid + "::" + name] = dict(
                added=E.metric(
                    Counter(
                        bykey[k]["outcome"]["status"]
                        for k in variant_raw - baseline_raw
                    )
                ),
                removed=E.metric(
                    Counter(
                        bykey[k]["outcome"]["status"]
                        for k in baseline_raw - variant_raw
                    )
                ),
                chronological_added=chronological_metric([rows[k] for k in added]),
                chronological_removed=chronological_metric(
                    [baseline[k] for k in removed]
                ),
                selected_keys=sorted(rows),
                added_keys=added,
                removed_keys=removed,
                incremental_standalone=chronological_metric(
                    chronological_points(addition)
                ),
                excluded_keys=sorted(excluded[sid]),
            )
    return metrics, effects


def materialize(store, point, ids):
    """Build only selected confirmations from frozen roots; never call a provider."""
    event, source = copy.deepcopy(store.get(point["snapshot_obj"]))
    features = point.get("cumulative_features")
    if features is None:
        return event, source
    signals = event["branch_signals"]
    inputs = source["branch_inputs"]
    for bid in Q.dependencies(ids):
        if bid not in Q.REFINEMENTS or bid in signals:
            continue
        original = Q.REFINEMENTS[bid]["original_definition_ref"]["branch_id"]
        if original not in signals:
            continue
        child = Q.compose(bid, signals[original], features)
        if child is None:
            continue
        signals[bid] = child
        inp = copy.deepcopy(inputs[original])
        facts = inp.get("facts")
        if not isinstance(facts, dict):
            # Native legacy roots retain the original nested fact ledger.
            # A cumulative child uses the typed extended source envelope;
            # lift only recorded facts and retain missing optional values.
            recorded = (inp.get("entry_setup_evidence_v1") or {}).get("facts")
            if not isinstance(recorded, dict):
                raise ValueError("cumulative_original_confirmation_facts_missing")
            from src.engine.scalping.reversal_extended_auxiliary import FEATURES

            facts = {key: copy.deepcopy(recorded.get(key)) for key in FEATURES}
            inp["facts"] = facts
        facts.update(
            confirmation_price=child["confirmation_price"], entry_ask=child["entry_ask"]
        )
        facts.update(
            spread_pct=features["spread"],
            drawdown_5m_pct=features["dd"],
            volume_ratio_60s=features["volume"],
            return_60s_pct=features["ret"],
            session_return_pct=features["session"],
            vs_vwap_60s_pct=features["vwap"],
            buy_pressure_10t=features["buy10"],
        )
        inp.update(
            signal_kind=child["signal_kind"],
            signal_proof=copy.deepcopy(child["signal_proof"]),
        )
        inputs[bid] = inp
    event["branch_signals"] = {b: e for b, e in signals.items() if b in ids}
    source["branch_inputs"] = {b: e for b, e in inputs.items() if b in ids}
    # This is a newly materialized current-membership snapshot. Its immutable
    # root snapshot may predate the typed cumulative catalog. Keep that parent
    # provenance rather than routing the child through its historical envelope.
    selected_registry = C.registry_for(event["branch_signals"])
    if event.get("registry_sha256") != selected_registry:
        event["materialization_parent_registry_sha256"] = event.get("registry_sha256")
        event["registry_sha256"] = selected_registry
    return event, source


def machine_cells(parent, manifest, execution_code):
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    cells = copy.deepcopy(parent["continuous_reversal"]["machine_cells"])
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        ids = manifest["scopes"][sid]
        cell = cells[key]["routes"][route]
        if sid in manifest.get("cumulative_variant_groups", {}):
            payload = dict(
                composition="ANY_MATCH_ONE_INTENT", branches=[C.branch(b) for b in ids]
            )
            cell.update(
                payload=payload,
                payload_sha256=P.digest(payload),
                backend="union_v6",
                status="registered_fixed_variant",
            )
        auxiliary = parent["continuous_reversal"]["auxiliary_cells"][key]["routes"][
            route
        ]["payload"]
        actual = [b["branch_id"] for b in cell["payload"]["branches"]]
        cell["scope_execution_hash"] = V.scope_hash(
            actual, auxiliary, cell["backend"], execution_code
        )
    return list(cells.values())


def build(data_root, day, publication, parent, *, source=None, publish_outputs=True):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    change = G.pending(data_root, parent, N.next_target(publication))
    manifest = V.detector_manifest(
        parent, effective_date=N.next_target(publication), changes=change
    )
    registered = manifest.get("cumulative_variant_groups") or {}
    if not registered:
        raise ValueError("cumulative_postclose_registration_missing")
    batch = G.approval(manifest)["research_batch_sha256"]
    catalog = Q.catalog(batch)
    source = source or P.ensure_population(data_root, day)
    if (
        source.get("artifact_content_sha256")
        != P.seal(source)["artifact_content_sha256"]
    ):
        raise ValueError("cumulative_source_manifest_changed")
    scoring = G.scoring_for_build(
        data_root, parent, publication, source["artifact_content_sha256"]
    )
    if scoring is not None:
        if change:
            raise ValueError("cumulative_scoring_conflicts_with_registration")
        if day != publication:
            raise ValueError("cumulative_scoring_observation_publication_mismatch")
        manifest["cumulative_scoring_contract"] = scoring
    out = O.directory(data_root, day)
    out.mkdir(parents=True, exist_ok=True)
    configs = {}
    current = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    for sid, ids in manifest["scopes"].items():
        configs[sid] = (
            dict(Q.variants(sid, batch), CURRENT_NATIVE=current[sid])
            if sid in registered and not (
                scoring is not None
                and scoring.get("unscored_scope_policy") == "carry_parent"
                and sid not in scoring["scopes"]
            )
            else dict(CURRENT_NATIVE=current[sid])
        )
    if scoring is not None:
        for sid, cfg in scoring["scopes"].items():
            configs[sid] = dict(cfg["alternatives"], CURRENT_NATIVE=current[sid])
    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    children = defaultdict(list)
    for bid, d in catalog["definitions"].items():
        if d["kind"] == "cumulative_refinement":
            children[d["original_definition_ref"]["branch_id"]].append(bid)
    canonical = {}
    conflicts = set()
    partitions = []
    receipts = list(scoring["source_receipts"]) if scoring else []
    bars = {}
    census = Counter()
    observed = Counter()
    detection_memberships = {
        sid: sorted({bid for ids in variants.values() for bid in ids})
        for sid, variants in configs.items()
    }
    with S.Store(data_root) as store:
        for rec in source["normalized_sources"]["partitions"]:
            if rec["day"] > day:
                raise ValueError("cumulative_source_after_observation_date")
            if rec["day"] < "2026-09-29":
                census["pre_refresh_partitions_excluded"] += 1
                continue
            market = K.market_bucket(rec["session"])
            route = rec["venue"]
            if route not in C.ROUTES.get(market, ()):
                continue
            with N.source_anchor(data_root):
                path = N.source_path(rec["path"])
            if P.file_hash(path) != rec["sha256"]:
                raise ValueError("cumulative_normalized_source_changed")
            if rec["day"] not in bars:

                def sink(origin, raw):
                    import hashlib

                    dest = (
                        out
                        / "frozen"
                        / ("bars-" + hashlib.sha256(raw).hexdigest() + ".json")
                    )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        dest.write_bytes(raw)
                    return dest

                bars[rec["day"]] = P.completed_bars(
                    data_root, rec["day"], snapshot_sink=sink, source=source
                )
                receipts.extend(bars[rec["day"]][1])
            fingerprint = P.digest(
                [
                    rec,
                    manifest["cumulative_variant_groups"],
                    current,
                    code,
                    bars[rec["day"]][1],
                    C.LABEL,
                    detection_memberships,
                ]
            )
            cached = store.checkpoint("cumulative-native-v2:" + fingerprint)
            if cached:
                records = cached["records"]
                counts = cached["census"]
                coverage = cached["coverage"]
            else:
                records = []
                counts = Counter()
                coverage = Counter()
                for symbol, source_rows in iter_normalized_symbols(path):
                    # Storage route is the normalized source item's route,
                    # not the policy cohort or an inferred execution venue.
                    # KRX's unsuffixed items must not be discarded as SOR.
                    item = symbol + {"KRX": "", "NXT": "_NX", "SOR": "_AL"}[route]
                    rows = [r[:] for r in source_rows]
                    for r in rows:
                        if r[9] != item:
                            r[8] = 0
                    counts["source_rows"] += len(rows)
                    counts["valid_source_rows"] += sum(bool(r[8]) for r in rows)
                    anchor = next((r for r in rows if r[8]), None)
                    if anchor is None:
                        continue
                    keys = (
                        [C.cell_key(symbol, market, 1)]
                        if C.group(symbol) == "samsung"
                        else [f"{C.group(symbol)}|{market}|{b}" for b in C.BANDS]
                    )
                    requested = {
                        b
                        for key in keys
                        for ids in configs[V.scope_id(key, route)].values()
                        for b in ids
                    }
                    native = [
                        b
                        for b in Q.dependencies(sorted(requested))
                        if b not in Q.REFINEMENTS
                    ]
                    state = State(
                        branch_ids=native, session_anchor=anchor, offline=True
                    )
                    times = [r[0] for r in rows]
                    _, ends, valid = K.segments(rows)
                    tree = K.Tree([r[3] if r[8] else None for r in rows])
                    for i, row in enumerate(rows):
                        ready = state.observe(
                            row, symbol=symbol, venue=route, session=rec["session"]
                        )
                        sid = V.scope_id(C.cell_key(symbol, market, row[3] or 1), route)
                        if row[8]:
                            coverage[sid] += 1
                        if ready and K.good_quote(row):
                            event, inp = LIVE.snapshot(state, ready[0])
                            allowed = (
                                set(catalog["groups"][sid]["baseline"])
                                | set(catalog["groups"][sid]["additions"].values())
                                if sid in registered
                                else set(current[sid])
                            )
                            signals = {
                                b: e
                                for b, e in event["branch_signals"].items()
                                if b in allowed
                                and C.applicable(b, sid.rsplit("|", 1)[0], route)
                            }
                            if signals:
                                event["branch_signals"] = signals
                                inp["branch_inputs"] = {
                                    b: v
                                    for b, v in inp["branch_inputs"].items()
                                    if b in signals
                                }
                                f = prefix_features(
                                    state, row, state.diagnostic_rolling["values"]
                                )
                                truth = set(signals)
                                for original in signals:
                                    for bid in children.get(original, ()):
                                        if (
                                            C.applicable(
                                                bid, sid.rsplit("|", 1)[0], route
                                            )
                                            and Q.condition(
                                                f, Q.REFINEMENTS[bid]["filters"]
                                            )
                                            is not False
                                        ):
                                            truth.add(bid)
                                label = K.label(
                                    rows,
                                    times,
                                    tree,
                                    ends,
                                    valid,
                                    i,
                                    event["entry_ask"],
                                )
                                bar = bars[rec["day"]][0].get((rec["day"], item))
                                if bar and rec.get("cutoff_epoch") is not None:
                                    bar = K.Bars(
                                        [
                                            r
                                            for r in bar.rows
                                            if r["t"] + 60 <= rec["cutoff_epoch"]
                                        ]
                                    )
                                if label["status"] == "UNRESOLVED" and bar:
                                    extra = bar.label(row[0], row[5], 1800)
                                    if extra["status"] != "UNRESOLVED":
                                        label = dict(
                                            extra, source="same_item_completed_bar"
                                        )
                                records.append(
                                    dict(
                                        opportunity_key=U.opportunity(event),
                                        native_alias=event["canonical_opportunity_id"],
                                        scope=sid,
                                        day=rec["day"],
                                        symbol=symbol,
                                        outcome=label,
                                        truth={b: "TRUE" for b in sorted(truth)},
                                        cumulative_features=f,
                                        snapshot_obj=store.put([event, inp]),
                                    )
                                )
                        state.ready.clear()
                    if any(v for k, v in state.counts.items() if "overload" in k):
                        raise ValueError("cumulative_replay_overload")
                if P.file_hash(path) != rec["sha256"]:
                    raise ValueError("cumulative_source_replaced_during_read")
                cached = dict(
                    records=records, census=dict(counts), coverage=dict(coverage)
                )
                store.checkpoint("cumulative-native-v2:" + fingerprint, cached)
                store.commit()
            census.update(counts)
            observed.update(coverage)
            for p in records:
                key = p["opportunity_key"]
                if key in canonical and P.digest(canonical[key]) != P.digest(p):
                    conflicts.add(key)
                else:
                    canonical[key] = p
            obj = store.put(records)
            partitions.append(
                dict(
                    normalized_source=rec,
                    records_object=obj,
                    records_sha256=P.digest(records),
                    points=len(records),
                )
            )
            receipts.append(dict(path=str(path.resolve()), sha256=rec["sha256"]))
        store.commit()
    for k in conflicts:
        canonical.pop(k, None)
    # Integer masks make membership comparisons independent of raw replay cost.
    bits = defaultdict(lambda: defaultdict(int))
    labels = defaultdict(lambda: defaultdict(int))
    sizes = Counter()
    for p in canonical.values():
        sid = p["scope"]
        bit = 1 << sizes[sid]
        sizes[sid] += 1
        labels[sid][p["outcome"]["status"]] |= bit
        for bid in p["truth"]:
            bits[sid][bid] |= bit
    metrics = {}
    effects = {}
    for sid, variants in configs.items():
        baseline = 0
        for bid in current[sid]:
            baseline |= bits[sid][bid]
        for name, ids in variants.items():
            union = 0
            for bid in ids:
                union |= bits[sid][bid]
            c = Counter(
                {
                    status: (union & mask).bit_count()
                    for status, mask in labels[sid].items()
                }
            )
            metrics[sid + "::" + name] = E.metric(c)
            effects[sid + "::" + name] = {
                role: E.metric(
                    {s: (mask & value).bit_count() for s, value in labels[sid].items()}
                )
                for role, mask in [
                    ("removed", baseline & ~union),
                    ("added", union & ~baseline),
                ]
            }
    if scoring is not None:
        with S.Store(data_root, readonly=True) as store:
            scored, deltas = scoring_metrics(
                canonical.values(), configs, current, scoring, store
            )
        for key, value in scored.items():
            metrics[key].update(value)
            effects[key].update(deltas[key])
    source_receipt = P.population_receipt(source)
    if source_receipt:
        receipts.append(source_receipt)
    report = P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=day,
            target_date=day,
            publication_date=publication,
            status="completed",
            parent_bundle_sha256=parent["bundle_sha256"],
            operating_manifest=manifest,
            execution_code_sha256=P.digest(code),
            cells=copy.deepcopy(
                list(parent["continuous_reversal"]["machine_cells"].values())
            ),
            registration_change=change,
            policy_schema=V.SCHEMA,
            source_manifest_sha256=source["artifact_content_sha256"],
            source_manifest_receipt=source_receipt,
            source_receipts=receipts,
            label_contract=C.LABEL,
            fixed_proposals=configs,
            proposal_metrics=metrics,
            partitions=partitions,
            input_census=dict(census),
            quarantined_conflicts=sorted(conflicts),
            detection_coverage={},
            valid_observation_counts=dict(observed),
            detection_coverage_role="valid_observation_counts_only_no_common_truth_mask_claim",
            compressed_coverage_masks=[],
            population="all_eligible_retained_native_ticks_from_2026_09_29",
            observation_mode="confirmation_replay",
            source_quality_gate="frozen_source_hash_and_eligible_rows_only",
            metric_role="main_entry_win_rate_selection",
            decision_authority="registered_fixed_variant_selection_only",
            primary_decision_metric=(
                G.SCOPED_METRIC
                if scoring
                else "cost_bound_cumulative_target_first_fraction"
            ),
            **(
                dict(
                    scoring_contract=scoring,
                    statistic_contract=G.scoring_spec(),
                    scope_decision_metrics={
                        sid: G.SCORE_VERSION for sid in scoring["scopes"]
                    },
                )
                if scoring
                else {}
            ),
            sample_floor="none",
            window_policy="all_eligible_cumulative_source_from_2026_09_29",
            forbidden_uses=[
                "actual_fill_claim",
                "realized_pnl_claim",
                "source_gap_zero_imputation",
            ],
            actual_trades_claimed=False,
            comparison_complete=True,
            **P.AUTH,
        )
    )
    if not change:
        report = G.apply_selection(report, parent)
    report = P.seal(
        dict(
            report,
            cells=machine_cells(
                parent, report["operating_manifest"], report["execution_code_sha256"]
            ),
        )
    )
    # Full fixed-variant diagnostics are immutable compressed evidence. Runtime
    # and semantic readers consume the bounded selected/current projection.
    table = P.seal(
        dict(
            schema=(
                "cumulative_fixed_comparison_table_v3"
                if scoring
                else "cumulative_fixed_comparison_table_v2"
            ),
            **(
                dict(scoring_contract=scoring, statistic_contract=G.scoring_spec())
                if scoring
                else {}
            ),
            parent_bundle_sha256=parent["bundle_sha256"],
            source_manifest_sha256=source["artifact_content_sha256"],
            fixed_proposals=configs,
            proposal_metrics=metrics,
            selection_effects=effects,
            **P.AUTH,
        )
    )
    table_path = (
        out
        / "frozen"
        / ("fixed-comparisons-" + table["artifact_content_sha256"] + ".json.gz")
    )
    table_path.parent.mkdir(parents=True, exist_ok=True)
    raw = gzip.compress(
        json.dumps(
            table, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode(),
        mtime=0,
    )
    if table_path.exists() and table_path.read_bytes() != raw:
        raise ValueError("cumulative_comparison_archive_conflict")
    if not table_path.exists():
        with table_path.open("xb") as handle:
            handle.write(raw)
    receipt = dict(path=str(table_path.resolve()), sha256=P.file_hash(table_path))
    small = {
        s: dict(
            CURRENT_NATIVE=current[s],
            SELECTED=report["operating_manifest"]["scopes"][s],
        )
        for s in configs
    }
    small_metrics = {}
    selected_effects = {}
    for sid in configs:
        selected = report.get("cumulative_selection", {}).get(sid, {}).get("variant")
        if not selected:
            selected = (
                catalog["recommendations"][sid]
                if change and sid in registered
                else "CURRENT_NATIVE"
            )
        for name, origin in [
            ("CURRENT_NATIVE", "CURRENT_NATIVE"),
            ("SELECTED", selected),
        ]:
            small_metrics[sid + "::" + name] = metrics.get(
                sid + "::" + origin, metrics[sid + "::CURRENT_NATIVE"]
            )
        selected_effects[sid] = {
            k: v
            for k, v in effects[sid + "::" + selected].items()
            if not k.endswith("_keys")
        }
    report = P.seal(
        dict(
            report,
            fixed_proposals=small,
            proposal_metrics=small_metrics,
            selection_effects=selected_effects,
            fixed_comparison_table=dict(
                receipt,
                artifact_content_sha256=table["artifact_content_sha256"],
                variant_count=sum(map(len, configs.values())),
            ),
            source_receipts=report["source_receipts"] + [receipt],
        )
    )
    P.write(out / "machine-comparison.json", report)
    if publish_outputs:
        for path in [
            out / "machine.json",
            P.directory(data_root, day) / "machine.json",
            Path(data_root)
            / "report/ai_decision_action_outcome_calibration"
            / f"winrate_policy_{day}.json",
        ]:
            P.write(path, report)
        P.write(
            Path(data_root)
            / "report/ai_decision_action_outcome_calibration"
            / f"winrate_policy_terminal_{day}.json",
            P.seal(
                dict(
                    schema=O.SCHEMA,
                    source_date=day,
                    target_date=day,
                    status="completed",
                    report_sha256=report["artifact_content_sha256"],
                    **G.selection_metadata(report),
                    disposition="continuous_reversal_selected",
                    staged=dict(status="machine_component_prepared"),
                    **P.AUTH,
                )
            ),
        )
    return report


def initial_reports(
    data_root, day, publication, parent, machine, *, publish_policy=True
):
    """Bind current auxiliary and its lineage under the existing publisher lock."""
    import fcntl
    from src.engine.scalping import reversal_auxiliary_intraday as I

    folder = I.root(data_root)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _initial_reports_locked(
            data_root, day, publication, parent, machine, publish_policy=publish_policy
        )


def _initial_reports_locked(
    data_root, day, publication, parent, machine, *, publish_policy
):
    """Carry compatible current auxiliary contracts; no new performance gate."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_registry as A

    request = (
        G.validate_request(machine["registration_change"])
        if machine.get("registration_change")
        else None
    )
    manifest = machine["operating_manifest"]
    if request:
        if (
            V.detector_manifest(
                parent, effective_date=request["target_date"], changes=request
            )
            != manifest
        ):
            raise ValueError("cumulative_initial_manifest_changed")
    else:
        G.validate_manifest(manifest)
    ac = copy.deepcopy(parent["continuous_reversal"]["auxiliary_cells"])
    current = I.effective_bindings(data_root, parent, day=publication)
    overlay = I.current(data_root, parent, day=publication)
    bindings = {}
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        old = ac[key]["routes"][route]
        if old["payload"].get("binding") != U.binding(old["payload"].get("arm")):
            raise ValueError("cumulative_compatible_auxiliary_binding_missing")
        prior = A.load(data_root, current[sid])
        if prior["input_version"] != U.VERSION:
            raise ValueError("cumulative_auxiliary_input_contract_incompatible")
        bindings[sid] = current[sid]
        # Source evidence and custom prompt/registry remain current; no campaign cloning.
        if not old.get("actual_response_evidence"):
            old["initial_binding"] = dict(
                operator_receipt=G.AUTHORITY,
                research_batch_sha256=G.approval(manifest)["research_batch_sha256"],
                source_scope=sid,
                source_bundle_sha256=parent["bundle_sha256"],
                comparison_result_required=False,
                response_evidence_role="compatible_current_auxiliary_contract_carry",
            )
    receipts = (
        list(machine["source_receipts"])
        + (request["source_receipts"] if request else [])
        + I.lineage_sources(data_root, parent, overlay)
    )
    for ident in sorted(set(bindings.values())):
        path = A.directory(data_root) / (ident + ".json")
        receipts.append(dict(path=str(path.resolve()), sha256=P.file_hash(path)))
    issued = P.seal(
        dict(
            machine,
            cells=machine_cells(parent, manifest, machine["execution_code_sha256"]),
            status="completed",
            membership_status="registered",
            registration_state="registered",
            scope_pending=[],
            adoption_basis=(
                "operator_designated_fixed_manual_variants"
                if request
                else "cumulative_fixed_variant_selected"
            ),
            source_receipts=receipts,
        )
    )
    auxiliary = P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=day,
            target_date=day,
            publication_date=publication,
            status="completed",
            cells=list(ac.values()),
            machine_report_sha256=issued["artifact_content_sha256"],
            source_receipts=receipts,
            parent_bundle_sha256=parent["bundle_sha256"],
            auxiliary_registry_bindings=bindings,
            auxiliary_reader_code_hashes=I.code_hashes(),
            initial_registration=request,
            results_sources=[],
            comparison_complete=False,
            comparison_state="compatible_current_contract_carry",
            scope_pending=[],
            expected_owner_requests=0,
            actual_provider_calls=0,
            registration_state="registered",
            auxiliary_independent_scopes=sorted(
                I.independent_scopes(data_root, parent, overlay)
            ),
            scope_census=dict(
                planned=len(V.scopes()),
                new_ready=len(V.scopes()),
                new_actual_pid_consumed=0,
                native_carried=0,
                contract_gaps=0,
            ),
            owner_request_census=dict(expected=0, missing=0),
            **P.AUTH,
        )
    )
    out = O.directory(data_root, day)
    for name, value in [
        ("machine-comparison", issued),
        ("machine", issued),
        ("auxiliary", auxiliary),
    ]:
        P.write(out / (name + ".json"), value)
    if publish_policy:
        import subprocess

        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        shared = P.directory(data_root, day)
        P.write(shared / "auxiliary.json", auxiliary)
        P.write(
            shared / "call-freeze.json",
            P.seal(
                dict(
                    schema=O.SCHEMA,
                    source_date=day,
                    status="frozen",
                    machine_report_sha256=machine["artifact_content_sha256"],
                    comparison_contract="compatible_current_contract_carry",
                    census=dict(expected_owner_requests=0, actual_provider_calls=0),
                    **P.AUTH,
                )
            ),
        )
        # Prior response evidence belongs to its original campaign; never truncate it.
        responses = shared / "provider-results.jsonl"
        if not responses.exists():
            with responses.open("x"):
                pass
        bundle = V.stage(
            data_root,
            day,
            publication,
            issued,
            auxiliary,
            target_date=(
                request["target_date"] if request else N.next_target(publication)
            ),
            release_commit=commit,
        )
        P.write(
            Path(data_root)
            / "report/ai_entry_setup_paired_replay_batch"
            / f"compact_auxiliary_paired_economic_{day}.json",
            P.seal(
                dict(
                    auxiliary,
                    staged=dict(
                        status="prepared",
                        bundle_sha256=bundle["bundle_sha256"],
                        target_date=bundle["target_date"],
                    ),
                )
            ),
        )
    return auxiliary


def compatible_inputs(machine):
    """No configured auxiliary campaign means carry, never all-variant AI fanout."""
    G.validate_manifest(machine["operating_manifest"])
    return dict(
        status="compatible_auxiliary_carry_no_campaign",
        actual_provider_calls=0,
        comparison_complete=False,
        **P.AUTH,
    )
