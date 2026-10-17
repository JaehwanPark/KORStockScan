"""Bounded, offline explanation of an immutable delay-policy generation.

This report consumes sealed projections, not historical raw ledgers. It never
selects or publishes a policy and cannot authorize runtime actions. Frozen
training/holdout membership remains authoritative for every diagnostic.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path

from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import pre_submit_delay_initial_policy as initial

SCHEMA = "pre_submit_delay_research_review_v1"
MAX_ANCHORS = 200000
MAX_CELLS = 20000
MAX_PARTITIONS = 20000
MAX_HORIZONS = 16
MAX_HORIZON_SEC = 3600
MAX_COMPACT_BYTES = 64 * 1024 * 1024
MAX_COMPACT_RECORDS = 1000000
MAX_DURABLE_BYTES = 512 * 1024 * 1024
MAX_TEMP_BYTES = 1024 * 1024 * 1024


def _sha(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _independent_identity(row):
    """Only reconstruct a cross-anchor identity from preserved native facts."""
    if row.get("native_evaluation_bound") is not True:
        return None
    explicit = row.get("independent_opportunity_sha256")
    if explicit is not None:
        if not _sha(explicit):
            raise ValueError("delay_review_independent_identity_invalid")
    projection = row.get("situation_projection") or {}
    machine = row.get("original_machine_observation_sha256") or projection.get("native_observation_sha256")
    attempt = (row.get("native_evaluation_attempt_id") or row.get("original_evaluation_attempt_id") or row.get("evaluation_attempt_id")
               or projection.get("attempt"))
    if _sha(machine) and isinstance(attempt, str) and 0 < len(attempt) <= 512:
        computed = initial.digest([row["alias"][0], row["alias"][1], machine,
                                   attempt, row["parent_compatibility"]])
        if explicit is not None and explicit != computed:
            raise ValueError("delay_review_independent_identity_mismatch")
        return computed
    return explicit


def _group(anchor, session, parents):
    return initial.digest([anchor, session, parents])


def _compact_index(db, data_root, report):
    """Decode only receipt-bound compact partitions once, under a fixed budget."""
    from src.engine.lifecycle.holding_window_generation import source_stat
    from src.engine.pipeline_event_summary import execution_projection_identity
    from src.engine.scalping import pre_submit_delay_tuning as owner
    db.execute("CREATE TABLE compact(alias TEXT,stage TEXT,sha TEXT,body TEXT,conflict INTEGER DEFAULT 0,"
               "PRIMARY KEY(alias,stage)) WITHOUT ROWID")
    receipt = report.get("source_receipt") or {}
    generations = receipt.get("partition_generations")
    result = dict(status="unavailable", bytes_read=0, records_decoded=0, invalid_event_identity_n=0,
                  malformed_records=0,
                  committed_identity_invalid_n=0, bound_projection_anchors=0)
    if not isinstance(generations, dict):
        result["reason"] = "partition_generation_receipt_missing"
        return result
    total = 0
    for name, expected in generations.items():
        path = Path(name)
        if (not path.is_absolute() or not path.resolve().is_relative_to(data_root)
                or path.is_symlink() or any(p.is_symlink() for p in path.parents)
                or type(expected.get("size")) is not int or expected["size"] < 0):
            raise ValueError("delay_review_compact_receipt_path_invalid")
        total += expected["size"]
    if total > MAX_COMPACT_BYTES:
        result["reason"] = "receipt_bound_compact_budget_exceeded"
        result["declared_bytes"] = total
        return result
    for name, expected in sorted(generations.items()):
        path = Path(name)
        before = source_stat(path.stat())
        if before[2] != expected["size"]:
            raise ValueError("delay_review_compact_generation_changed")
        consumed, stream_sha = 0, hashlib.sha256()
        with path.open("rb") as handle:
            if source_stat(os.fstat(handle.fileno())) != before:
                raise ValueError("delay_review_compact_generation_changed")
            for raw in iter(lambda: handle.readline(storage.RECORD_BYTES + 1), b""):
                consumed += len(raw)
                if consumed > expected["size"] or result["bytes_read"] + consumed > MAX_COMPACT_BYTES:
                    raise ValueError("delay_review_compact_generation_changed")
                stream_sha.update(raw)
                if len(raw) > storage.RECORD_BYTES:
                    raise ValueError("delay_review_compact_record_budget_exceeded")
                result["records_decoded"] += 1
                if result["records_decoded"] > MAX_COMPACT_RECORDS:
                    raise ValueError("delay_review_compact_record_count_exceeded")
                try:
                    row = json.loads(raw)
                except (ValueError, UnicodeError):
                    result["malformed_records"] += 1
                    continue
                if not isinstance(row, dict):
                    result["malformed_records"] += 1
                    continue
                try:
                    identity_valid = row.get("execution_source_event_sha256") == execution_projection_identity(row)
                except (ValueError, TypeError, OverflowError):
                    identity_valid = False
                if not identity_valid:
                    result["invalid_event_identity_n"] += 1
                    continue
                fields = row.get("fields")
                if not isinstance(fields, dict):
                    continue
                stage = row.get("stage")
                if (row.get("family") != "pre_submit_delay" or stage not in {
                        "pre_submit_delay_committed", "pre_submit_delay_quote_observed"}):
                    continue
                if stage == "pre_submit_delay_quote_observed" and initial.number(fields.get("target_delay_sec")) != 0:
                    continue
                if stage == "pre_submit_delay_committed" and fields.get("decision_source_sha256") != owner.decision_source_sha256(fields):
                    result["committed_identity_invalid_n"] += 1
                    continue
                alias = initial.digest([str(row.get("emitted_date")), str(row.get("stock_code")),
                                        str(fields.get("delay_intent_id") or "")])
                sha = initial.digest(fields)
                db.execute("INSERT INTO compact(alias,stage,sha,body) VALUES (?,?,?,?) "
                           "ON CONFLICT(alias,stage) DO UPDATE SET conflict=CASE WHEN compact.sha!=excluded.sha "
                           "THEN 1 ELSE compact.conflict END", (alias, stage, sha, storage.encoded(fields).decode()))
            if source_stat(os.fstat(handle.fileno())) != before:
                raise ValueError("delay_review_compact_generation_changed")
        if (source_stat(path.stat()) != before or consumed != expected["size"]
                or stream_sha.hexdigest() != expected["sha256"]):
            raise ValueError("delay_review_compact_generation_changed")
        result["bytes_read"] += consumed
    result["status"] = "complete"
    return result


def _enrich(db, row, receipt):
    """Bind extra facts to the original alias and decision hash, never replace it."""
    alias = initial.digest(row["alias"])
    found = dict(db.execute("SELECT stage,body FROM compact WHERE alias=? AND conflict=0", (alias,)))
    commit = json.loads(found["pre_submit_delay_committed"]) if "pre_submit_delay_committed" in found else None
    result = dict(row)
    features = dict(row.get("execution_features") or {})
    if commit and commit.get("decision_source_sha256") == row.get("decision_source_sha256"):
        receipt["bound_projection_anchors"] += 1
        machine = commit.get("original_machine_observation_sha256")
        native = commit.get("original_evaluation_attempt_id") or commit.get("evaluation_attempt_id") or commit.get("request_id")
        if _sha(machine) and isinstance(native, str) and native:
            if (row.get("original_machine_observation_sha256") not in (None, machine)
                    or row.get("native_evaluation_attempt_id") not in (None, native)):
                raise ValueError("delay_review_enrichment_native_identity_conflict")
            result.setdefault("original_machine_observation_sha256", machine)
            result.setdefault("native_evaluation_attempt_id", native)
        reference = initial.number(commit.get("original_signal_reference_price"))
        epoch = initial.number(commit.get("original_signal_reference_epoch"))
        stamp = initial.number(commit.get("decision_committed_at_epoch"))
        signal_id = commit.get("original_signal_id")
        if (commit.get("signal_reference_contract_version") == "native_confirmation_price_v1"
                and reference is not None and reference > 0 and epoch is not None
                and stamp is not None and 0 < epoch <= stamp
                and isinstance(signal_id, str) and 0 < len(signal_id) <= 512):
            for name, value in (("original_signal_reference_price", reference),
                                ("original_signal_reference_epoch", epoch), ("original_signal_id", signal_id)):
                if features.get(name) not in (None, value):
                    raise ValueError("delay_review_enrichment_signal_reference_conflict")
                features[name] = value
        quote = json.loads(found["pre_submit_delay_quote_observed"]) if "pre_submit_delay_quote_observed" in found else None
        if quote and row["p0_valid"]:
            from src.engine.scalping.pre_submit_delay_tuning import _quote_source_issue
            ask, bid = initial.number(quote.get("ask_price")), initial.number(quote.get("best_bid"))
            if (not _quote_source_issue(commit, quote) and ask is not None and bid is not None
                    and 0 < bid <= ask and str(quote.get("quote_valid")).lower() in {"true", "1"}):
                features.setdefault("p0_ask", ask)
                features.setdefault("p0_bid", bid)
        # current_price_observed / price_cap are sizing/preparation facts. They
        # are not substituted for the original machine signal reference price.
    result["execution_features"] = features
    return result


def _populate(db, root, report, compact_receipt):
    db.executescript("""
        CREATE TABLE population (
            id TEXT PRIMARY KEY, gid TEXT, day TEXT, symbol TEXT, anchor TEXT,
            session TEXT, situation TEXT, at REAL, end REAL, p0 INTEGER,
            native INTEGER, opportunity TEXT, spread_bp REAL, progress_bp REAL,
            split TEXT DEFAULT 'unqualified'
        ) WITHOUT ROWID;
        CREATE TABLE pairs (id TEXT, horizon REAL, bp REAL,
                            PRIMARY KEY(id,horizon)) WITHOUT ROWID;
        CREATE TABLE partitions (gid TEXT PRIMARY KEY, sha TEXT) WITHOUT ROWID;
        CREATE TABLE membership (id TEXT PRIMARY KEY) WITHOUT ROWID;
        CREATE INDEX population_group ON population(gid,situation,split);
        CREATE INDEX pairs_horizon ON pairs(horizon,id);
    """)
    counts, horizons = Counter(), set()
    for row in storage.iter_tree(root, report["qualified_projection_ref"]):
        counts["anchors"] += 1
        if counts["anchors"] > MAX_ANCHORS:
            raise ValueError("delay_review_anchor_budget_exceeded")
        alias, parents = row.get("alias"), row.get("parent_compatibility")
        if (not _sha(row.get("identity")) or not isinstance(alias, list) or len(alias) != 3
                or not isinstance(alias[0], str) or not isinstance(alias[1], str)
                or not isinstance(parents, list) or len(parents) != 2
                or any(not isinstance(p, str) for p in parents)
                or row.get("anchor_kind") not in {"price_ready", "signal_ready"}
                or not isinstance(row.get("session"), str)
                or not isinstance(row.get("situation"), str)
                or type(row.get("p0_valid")) is not bool
                or type(row.get("native_evaluation_bound")) is not bool
                or initial.number(row.get("committed_at")) is None
                or initial.number(row.get("observation_end_at")) is None
                or not isinstance(row.get("pairs"), dict)):
            raise ValueError("delay_review_projection_invalid")
        date.fromisoformat(alias[0])
        row = _enrich(db, row, compact_receipt)
        independent = _independent_identity(row)
        features = row.get("execution_features") or {}
        ask, bid = initial.number(features.get("p0_ask")), initial.number(features.get("p0_bid"))
        spread = (ask-bid)/ask*10000 if ask is not None and bid is not None and 0 < bid <= ask else None
        reference = initial.number(features.get("original_signal_reference_price"))
        progress = (ask-reference)/reference*10000 if ask is not None and reference is not None and reference > 0 else None
        counts["p0_spread_bp_available_anchors"] += spread is not None
        counts["original_signal_price_progress_available_anchors"] += progress is not None
        counts["independent_identity_bound_anchors"] += independent is not None
        counts["p0_valid_anchors"] += row["p0_valid"]
        counts["native_evaluation_bound_anchors"] += row["native_evaluation_bound"]
        counts["unknown_situation_anchors"] += row["situation"] == "UNKNOWN"
        counts["exact_parent_bound_anchors"] += all(_sha(p) for p in parents)
        # Older qualified projections do not preserve these pre-known features.
        # Their absence cannot be repaired from a later quote or today's catalog.
        for name in ("original_signal_reference_price", "original_signal_reference_epoch", "original_signal_id",
                     "p0_ask", "p0_bid", "p0_ask_qty", "p0_actual_offset_sec", "p0_source_age_sec"):
            counts["available:" + name] += features.get(name) is not None
        for name in ("delay_recheck_requested_at_epoch",
                     "delay_recheck_completed_at_epoch", "delay_terminal_reason"):
            counts["available:" + name] += row.get(name) is not None
        db.execute("INSERT INTO population(id,gid,day,symbol,anchor,session,situation,at,end,p0,native,opportunity,spread_bp,progress_bp) "
                   "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                       row["identity"], _group(row["anchor_kind"], row["session"], parents),
                       alias[0], alias[1], row["anchor_kind"], row["session"], row["situation"],
                       row["committed_at"], row["observation_end_at"], int(row["p0_valid"]),
                       int(row["native_evaluation_bound"]), independent, spread, progress))
        all_pairs = dict(row["pairs"])
        for horizon, value in (row.get("research_short_pairs") or {}).items():
            if str(horizon) in {str(k) for k in all_pairs}:
                raise ValueError("delay_review_short_horizon_overlap")
            if str(horizon) not in {"1", "3", "5"} or row.get("research_short_p0_valid") is not True:
                raise ValueError("delay_review_short_pair_contract_invalid")
            all_pairs[str(horizon)] = value
        for horizon, value in all_pairs.items():
            delay, bp = initial.number(horizon), initial.number(value)
            if (delay is None or not 0 < delay <= MAX_HORIZON_SEC or bp is None
                    or not row["p0_valid"]):
                raise ValueError("delay_review_pair_invalid")
            horizons.add(delay)
            if len(horizons) > MAX_HORIZONS:
                raise ValueError("delay_review_horizon_budget_exceeded")
            db.execute("INSERT INTO pairs VALUES (?,?,?)", (row["identity"], delay, bp))
            counts["horizon_pairs"] += 1
            if delay in {1, 3, 5}:
                counts["short_pairs:" + str(int(delay))] += 1
    for index, partition in enumerate(storage.iter_tree(root, report["partitions_ref"]), 1):
        if index > MAX_PARTITIONS:
            raise ValueError("delay_review_partition_budget_exceeded")
        body = {k: v for k, v in partition.items() if k != "sha256"}
        if partition.get("sha256") != initial.digest(storage.logical_value(body)):
            raise ValueError("delay_review_partition_hash_invalid")
        gid = _group(partition["anchor_kind"], partition["session"], partition["parent_compatibility"])
        db.execute("INSERT INTO partitions VALUES (?,?)", (gid, partition["sha256"]))
        for member in storage.iter_tree(root, partition["membership"]):
            split = member.get("split")
            if split not in {"train", "validation", "purged", "unqualified"}:
                raise ValueError("delay_review_partition_split_invalid")
            prior = db.execute("SELECT gid,p0,split FROM population WHERE id=?", (member.get("identity"),)).fetchone()
            if prior is None or prior[0] != gid or prior[1] != 1 or prior[2] != "unqualified":
                raise ValueError("delay_review_partition_member_invalid")
            # A separately keyed table detects duplicates even for unqualified.
            db.execute("INSERT INTO membership(id) VALUES (?)", (member["identity"],))
            db.execute("UPDATE population SET split=? WHERE id=?", (split, member["identity"]))
    if db.execute("SELECT count(*) FROM population p WHERE p.p0=1 AND NOT EXISTS "
                  "(SELECT 1 FROM membership r WHERE r.id=p.id)").fetchone()[0]:
        raise ValueError("delay_review_partition_membership_missing")
    census = report.get("census") or {}
    for key, observed in (("qualified_pass_n", counts["anchors"]), ("p0_valid_n", counts["p0_valid_anchors"])):
        if census.get(key) != observed:
            raise ValueError("delay_review_projection_census_mismatch")
    return counts, sorted(horizons)


def _stats(db, query, args, denominator):
    n = db.execute("SELECT count(*) FROM (" + query + ")", args).fetchone()[0]
    ordered = "SELECT v FROM (" + query + ") ORDER BY v"
    def quantile(fraction):
        if not n:
            return None
        at = (n - 1) * fraction
        lo, hi = int(at), math.ceil(at)
        values = [r[0] for r in db.execute(ordered + " LIMIT ? OFFSET ?", (*args, hi - lo + 1, lo))]
        return values[0] + (values[-1] - values[0]) * (at - lo)
    total = math.fsum(v for v, in db.execute(ordered, args))
    signs = db.execute("SELECT sum(v>0),sum(v<0),sum(v=0) FROM (" + query + ")", args).fetchone()
    return dict(n=n, eligible_n=denominator, coverage=n / denominator if denominator else 0,
                mean_bp=total / n if n else None, median_bp=quantile(.5), p10_bp=quantile(.1),
                p90_bp=quantile(.9), improved_n=signs[0] or 0, worsened_n=signs[1] or 0,
                equal_n=signs[2] or 0)


def _where(cell, *, split=None):
    text = "p.gid=? AND p.p0=1"
    args = [_group(cell["anchor_kind"], cell["session"], cell["parent_compatibility"])]
    if cell["situation"] != "ALL":
        text += " AND p.situation=?"
        args.append(cell["situation"])
    if split is not None:
        text += " AND p.split=?"
        args.append(split)
    return text, tuple(args)


def _reason(cell, candidates):
    basis = cell.get("selection_basis")
    if cell.get("delay_sec") and basis == "paired_quote_initial":
        return "positive_delay_supported_by_frozen_train_and_holdout"
    reasons = {
        "paired_quote_immediate": "nonpositive_training_and_holdout_price_improvement",
        "incumbent_on_unconfirmed_pattern": "training_holdout_direction_not_confirmed",
        "unverified_lineage_immediate_default": "native_or_parent_lineage_unverified",
    }
    if basis in reasons:
        return reasons[basis]
    if basis == "unsupported":
        if not cell.get("train", {}).get("eligible_n"):
            return "training_population_unavailable"
        if not candidates:
            return "training_paired_quote_unavailable"
        if cell.get("comparison_delay_sec") is not None and not cell.get("validation", {}).get("n"):
            return "selected_training_candidate_holdout_pair_unavailable"
        return "unsupported_existing_selection_contract"
    return "unrecognized_selection_basis"


def _fallback(db, item, supported_anchor):
    key, cell = item["key"], item["value"]
    fallback_key = initial.cell_key(cell["anchor_kind"], cell["session"], parents=cell["parent_compatibility"])
    path, resolved, resolved_key = [key], None, None
    for candidate_key in dict.fromkeys((key, fallback_key)):
        body = db.execute("SELECT body FROM records WHERE id=?", ("cell:" + candidate_key,)).fetchone()
        candidate = json.loads(body[0])["value"] if body else None
        if candidate_key != key:
            path.append(candidate_key)
        if candidate and candidate.get("delay_sec") is not None and candidate.get("runtime_apply_allowed") is not False:
            resolved, resolved_key = candidate["delay_sec"], candidate_key
            break
    if resolved is None:
        resolved = 0
        path.append("policy_default:0")
    anchor_supported = cell["anchor_kind"] == supported_anchor == "price_ready"
    return dict(research_cell_or_parent_delay_sec=resolved, resolved_cell_key=resolved_key,
                resolution_path=path, runtime_policy_anchor_supported=anchor_supported,
                prepared_policy_lookup_delay_sec=resolved if anchor_supported else 0,
                actual_pid_consumption_verified=False)


def _cell_review(db, item, horizons, supported_anchor):
    key, cell = item["key"], item["value"]
    expected = initial.cell_key(cell["anchor_kind"], cell["session"], cell["situation"],
                                cell["execution_context"], parents=cell["parent_compatibility"])
    where, args = _where(cell)
    partition = db.execute("SELECT sha FROM partitions WHERE gid=?", (args[0],)).fetchone()
    if key != expected or partition is None or partition[0] != cell.get("partition_sha256"):
        raise ValueError("delay_review_cell_partition_invalid")
    candidates, overlap = {}, []
    membership = dict(db.execute("SELECT split,count(*) FROM population p WHERE " + where + " GROUP BY split", args))
    for delay in horizons:
        value = {}
        for split in ("train", "validation", "purged", "unqualified"):
            condition, parameters = _where(cell, split=split)
            query = "SELECT q.bp v FROM population p JOIN pairs q ON q.id=p.id WHERE " + condition + " AND q.horizon=?"
            value[split] = _stats(db, query, (*parameters, delay), membership.get(split, 0))
        candidates[str(int(delay)) if delay.is_integer() else str(delay)] = value
    for left_index, left in enumerate(horizons):
        for right in horizons[left_index + 1:]:
            for split in ("train", "validation"):
                condition, parameters = _where(cell, split=split)
                base = (" FROM population p JOIN pairs a ON a.id=p.id JOIN pairs b ON b.id=p.id "
                        "WHERE " + condition + " AND a.horizon=? AND b.horizon=?")
                bind = (*parameters, left, right)
                denominator = membership.get(split, 0)
                overlap.append(dict(left_delay_sec=left, right_delay_sec=right, split=split,
                    left=_stats(db, "SELECT a.bp v" + base, bind, denominator),
                    right=_stats(db, "SELECT b.bp v" + base, bind, denominator),
                    left_minus_right=_stats(db, "SELECT a.bp-b.bp v" + base, bind, denominator)))
    # Short-horizon diagnostics were never candidates of this frozen selector.
    # Their presence must not change the explanation of an unsupported cell.
    selected_candidates = cell.get("candidate_delays_sec")
    observed = (selected_candidates if isinstance(selected_candidates, list) else
                [d for d, stats in candidates.items()
                 if stats["train"]["n"] and initial.number(d) in initial.HORIZONS[1:]])
    independent_n, identity_bound_n, anchors, days, symbols = db.execute(
        "SELECT count(DISTINCT p.opportunity),count(p.opportunity),count(*),count(DISTINCT p.day),"
        "count(DISTINCT p.symbol) FROM population p WHERE " + where, args).fetchone()
    return dict(key=key, original_cell=cell, selection_reason_raw=cell.get("selection_basis"),
                selection_reason_normalized=_reason(cell, observed),
                selected_delay_sec=cell.get("delay_sec"),
                fallback_key=cell.get("fallback_key"),
                fallback_resolution=_fallback(db, item, supported_anchor),
                eligible_p0_anchors=anchors, distinct_source_dates=days, distinct_symbols=symbols,
                unique_independent_opportunities=independent_n if identity_bound_n == anchors else None,
                known_identity_subset_unique_opportunities=independent_n,
                frozen_partition_counts=membership, candidates=candidates, pairwise_common_cohort=overlap,
                diagnostic_only=True, policy_reselected=False)


def _contributions(db, cell_items, horizons):
    for item in cell_items:
        key, cell = item["key"], item["value"]
        where, args = _where(cell)
        for axis, field in (("source_date", "day"), ("symbol", "symbol")):
            for delay in horizons:
                for split, value, n, total in db.execute(
                    f"SELECT p.split,p.{field},count(*),sum(q.bp) FROM population p "
                    "JOIN pairs q ON p.id=q.id WHERE " + where + " AND q.horizon=? "
                    f"GROUP BY p.split,p.{field} ORDER BY p.split,p.{field}", (*args, delay)):
                    yield dict(key=key, axis=axis, value=value, split=split, delay_sec=delay,
                               n=n, sum_price_improvement_bp=total, mean_price_improvement_bp=total / n,
                               metric_role="diagnostic_contribution_not_ev")


def _feature_groups(db, cell_items, horizons):
    """Fixed diagnostic groups; these cannot become policy-selection inputs."""
    specifications = (
        ("original_signal_price_progress", "progress_bp",
         (("down", "p.progress_bp<0"), ("same", "p.progress_bp=0"), ("up", "p.progress_bp>0"))),
        ("p0_spread_bp", "spread_bp",
         (("zero", "p.spread_bp=0"), ("gt0_lt10bp", "p.spread_bp>0 AND p.spread_bp<10"),
          ("ge10bp", "p.spread_bp>=10"))),
    )
    for item in cell_items:
        cell = item["value"]
        for feature, field, buckets in specifications:
            for label, predicate in buckets:
                for split in ("train", "validation"):
                    where, args = _where(cell, split=split)
                    denominator = db.execute("SELECT count(*) FROM population p WHERE " + where, args).fetchone()[0]
                    available = db.execute(f"SELECT count(*) FROM population p WHERE {where} AND p.{field} IS NOT NULL", args).fetchone()[0]
                    if not available:
                        continue
                    bucket_n = db.execute("SELECT count(*) FROM population p WHERE " + where + " AND " + predicate, args).fetchone()[0]
                    if not bucket_n:
                        continue
                    for delay in horizons:
                        query = ("SELECT q.bp v FROM population p JOIN pairs q ON q.id=p.id WHERE "
                                 + where + " AND " + predicate + " AND q.horizon=?")
                        yield dict(key=item["key"], feature=feature, bucket=label, split=split,
                            delay_sec=delay, original_split_n=denominator, feature_available_n=available,
                            bucket_n=bucket_n, stats=_stats(db, query, (*args, delay), bucket_n),
                            selection_authority=False, group_boundaries="fixed_diagnostic_only")


def _output_path(data_root, output_dir):
    data_root, output = Path(data_root).resolve(), Path(output_dir).absolute()
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise ValueError("delay_review_output_path_invalid")
    protected = data_root / "threshold_cycle/pre_submit_delay_policy"
    if output == data_root or output.resolve().is_relative_to(protected):
        raise ValueError("delay_review_output_overlaps_policy_source")
    return data_root, output


def generate(data_root, source_date, output_dir):
    """Write bounded report evidence without changing selected policy or source."""
    from src.engine.lifecycle.research_disk_budget import use
    data_root, output = _output_path(data_root, output_dir)
    with use(output, durable_limit=MAX_DURABLE_BYTES, temp_limit=MAX_TEMP_BYTES):
        return _generate(data_root, source_date, output)


def _generate(data_root, source_date, output_dir):
    date.fromisoformat(source_date)
    data_root, output = _output_path(data_root, output_dir)
    report_path, policy_path, pointer, manifest = initial.committed_paths(
        data_root, source_date, validate_selection=False)
    report, policy = initial._read(report_path), initial._read(policy_path)
    if (initial.digest(report) != manifest["report_artifact_sha256"]
            or initial.digest(policy) != manifest["policy_artifact_sha256"]):
        raise ValueError("delay_review_generation_metadata_changed")
    if report.get("storage_schema") != "pre_submit_delay_sharded_evidence_v3":
        raise ValueError("delay_review_sharded_projection_required")
    if policy.get("cells_ref") != report.get("cells_ref"):
        raise ValueError("delay_review_policy_cells_mismatch")
    if (policy.get("default_delay_sec") != 0 or report.get("default_delay_sec") != 0
            or policy.get("supported_anchor_kind") != "price_ready"):
        raise ValueError("delay_review_policy_fallback_contract_invalid")
    for key, limit in (("qualified_projection_ref", MAX_ANCHORS), ("cells_ref", MAX_CELLS),
                       ("partitions_ref", MAX_PARTITIONS)):
        ref = report.get(key)
        if not isinstance(ref, dict) or type(ref.get("count")) is not int or not 0 <= ref["count"] <= limit:
            raise ValueError("delay_review_evidence_count_or_budget_invalid")
    output.mkdir(parents=True, exist_ok=True)
    from src.engine.lifecycle.holding_window_generation import byte_generation
    code_before = dict(review_module_sha256=byte_generation(Path(__file__))["sha256"],
                       reader_producer_contract_sha256=initial.code_contract())
    generation_before = byte_generation(pointer)
    if initial._read(pointer) != manifest:
        raise ValueError("delay_review_committed_pointer_changed")
    with storage.index(output) as db:
        compact_receipt = _compact_index(db, data_root, report)
        counts, horizons = _populate(db, report_path.parent, report, compact_receipt)
        reason_counts, anchor_reasons = Counter(), Counter()
        seen = set()
        for item in storage.iter_tree(report_path.parent, report["cells_ref"]):
            if item["key"] in seen:
                raise ValueError("delay_review_duplicate_cell")
            seen.add(item["key"])
            storage.put(db, "cell:" + item["key"], item)
        def reviewed():
            for _, item, _ in storage.records(db):
                row = _cell_review(db, item, horizons, policy.get("supported_anchor_kind"))
                reason_counts[row["selection_reason_normalized"]] += 1
                anchor_reasons[(item["value"]["anchor_kind"], row["selection_reason_normalized"])] += 1
                yield row
        cells_ref = storage.write_tree(output, reviewed())
        contributions_ref = storage.write_tree(output, _contributions(db,
            (row for _, row, _ in storage.records(db) if "key" in row), horizons))
        feature_groups_ref = storage.write_tree(output, _feature_groups(db,
            (row for _, row, _ in storage.records(db) if "key" in row), horizons))
        known_unique = db.execute("SELECT count(DISTINCT opportunity) FROM population").fetchone()[0]
        by_anchor = [dict(anchor_kind=a, anchors=n, p0_valid_anchors=p0, pairs=pairs,
                         independent_identity_bound_anchors=bound,
                         known_identity_subset_unique_opportunities=unique,
                         unique_independent_opportunities=unique if bound == n else None)
                     for a, n, p0, pairs, bound, unique in db.execute(
                         "SELECT anchor,count(*),sum(p0),(SELECT count(*) FROM pairs q JOIN population z ON z.id=q.id "
                         "WHERE z.anchor=p.anchor),count(opportunity),count(DISTINCT opportunity) "
                         "FROM population p GROUP BY anchor ORDER BY anchor")]
        split_ref = storage.write_tree(output, (dict(identity=i, source_date=d, symbol=s, anchor_kind=a,
            committed_at=at, observation_end_at=end, split=split, independent_opportunity_sha256=opp)
            for i, d, s, a, at, end, split, opp in db.execute(
                "SELECT id,day,symbol,anchor,at,end,split,opportunity FROM population ORDER BY at,id")))
    if byte_generation(pointer) != generation_before:
        raise ValueError("delay_review_committed_pointer_changed")
    if code_before != dict(review_module_sha256=byte_generation(Path(__file__))["sha256"],
                           reader_producer_contract_sha256=initial.code_contract()):
        raise ValueError("delay_review_code_changed_during_read")
    all_identity_bound = counts["independent_identity_bound_anchors"] == counts["anchors"]
    result = dict(schema=SCHEMA, source_date=source_date, status="complete", partial=False,
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
        metric_role="initial_entry_price_timing_diagnostic", decision_authority="report_only",
        primary_decision_metric="mean_paired_price_improvement_bp",
        window_policy="immutable_committed_generation_and_original_frozen_partitions",
        sample_floor="none_added_existing_selection_preserved",
        source_quality_gate="sealed_manifest_pair_and_fully_consumed_evidence_tree_hashes",
        forbidden_uses=["policy_selection", "runtime_apply", "realized_profit_claim", "synthetic_recheck_pass"],
        input=dict(manifest_path=str(pointer), manifest_sha256=manifest["manifest_sha256"],
                   generation=manifest["generation"], source_sha256=manifest["source_sha256"],
                   original_code_contract_sha256=manifest["code_contract_sha256"],
                   report_artifact_sha256=manifest["report_artifact_sha256"],
                   policy_artifact_sha256=manifest["policy_artifact_sha256"],
                   qualified_projection_ref=report["qualified_projection_ref"],
                   raw_source_reverified=False, consumed_projection_once=True),
        code_provenance=code_before,
        original_policy_status=policy.get("selection_status"), original_default_delay_sec=policy.get("default_delay_sec"),
        original_census=report.get("census"), horizons_sec=horizons,
        short_horizon_observation_status={str(delay): {
            "paired_observation_n": counts.get("short_pairs:" + str(delay), 0),
            "status": "observed_research_only" if delay in horizons else "no_historical_observation"}
            for delay in (1, 3, 5)},
        census={k: v for k, v in counts.items() if not k.startswith("available:")},
        unique_independent_opportunities=known_unique if all_identity_bound else None,
        known_identity_subset_unique_opportunities=known_unique,
        independent_identity_status="complete" if all_identity_bound else "partial_native_identity_not_preserved",
        by_anchor=by_anchor, selection_reason_counts=dict(reason_counts), cells_ref=cells_ref,
        supported_policy_anchor_kind=policy.get("supported_anchor_kind"),
        selection_reason_counts_by_anchor={anchor: {reason: n for (a, reason), n in anchor_reasons.items() if a == anchor}
            for anchor in sorted({a for a, _ in anchor_reasons})},
        cell_count_role="overlapping_parent_and_situation_cells_not_independent_opportunities",
        contributions_ref=contributions_ref, frozen_membership_ref=split_ref,
        feature_groups_ref=feature_groups_ref, compact_enrichment=compact_receipt,
        preserved_field_coverage={k.removeprefix("available:"): v for k, v in counts.items() if k.startswith("available:")},
        analysis_availability=dict(
            price_progress_grouping="available_for_preserved_subset" if counts["original_signal_price_progress_available_anchors"] else "unavailable_original_signal_reference_not_preserved",
            spread_bp_grouping="available_for_preserved_subset" if counts["p0_spread_bp_available_anchors"] else "unavailable_frozen_p0_bid_ask",
            spread_tick_grouping="unavailable_explicit_frozen_tick_size",
            recheck_pass="not_inferred_from_quote_path", opportunity_retention="requires_exact_recheck_outcome",
            paired_net_ev_delta_pct=None, realized_pnl_krw=None),
        limits=dict(max_anchors=MAX_ANCHORS, max_cells=MAX_CELLS, max_partitions=MAX_PARTITIONS,
                    max_horizons=MAX_HORIZONS, maximum_shard_record_bytes=storage.RECORD_BYTES,
                    max_compact_bytes=MAX_COMPACT_BYTES, max_compact_records=MAX_COMPACT_RECORDS,
                    max_durable_output_bytes=MAX_DURABLE_BYTES, max_temporary_bytes=MAX_TEMP_BYTES,
                    exceeded_limit_behavior="fail_before_publishing_new_complete_report"))
    result["artifact_sha256"] = initial.digest(result)
    destination = output / "report.json"
    if destination.exists() and initial._read(destination) != result:
        raise ValueError("delay_review_immutable_report_conflict")
    initial._atomic(destination, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    result = generate(args.data_root, args.source_date, args.output_dir)
    print(json.dumps(dict(status=result["status"], source_date=result["source_date"],
                          report=str(args.output_dir / "report.json"), census=result["census"],
                          selection_reason_counts=result["selection_reason_counts"]), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
