"""Bounded, offline explanation of an immutable delay-policy generation.

This report consumes sealed projections, not historical raw ledgers. It never
selects or publishes a policy and cannot authorize runtime actions. Frozen
training/holdout membership remains authoritative for every diagnostic.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
from zoneinfo import ZoneInfo

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
EXECUTION_HORIZONS = (1, 3, 5, 30, 60, 120, 180, 300, 600)


def _sha(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _independent_identity(row):
    """Only reconstruct a cross-anchor identity from preserved native facts."""
    if row.get("native_evaluation_bound") is not True:
        return None
    explicit = row.get("independent_opportunity_sha256")
    if explicit is not None:
        if not _sha(explicit):
            raise ValueError("delay_review_independent_identity_invalid")
    projection = row.get("situation_projection") or {}
    machine = row.get("original_machine_observation_sha256") or projection.get(
        "native_observation_sha256"
    )
    attempt = (
        row.get("native_evaluation_attempt_id")
        or row.get("original_evaluation_attempt_id")
        or row.get("evaluation_attempt_id")
        or projection.get("attempt")
    )
    if _sha(machine) and isinstance(attempt, str) and 0 < len(attempt) <= 512:
        computed = initial.digest(
            [
                row["alias"][0],
                row["alias"][1],
                machine,
                attempt,
                row["parent_compatibility"],
            ]
        )
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

    db.execute(
        "CREATE TABLE compact(alias TEXT,stage TEXT,sha TEXT,body TEXT,conflict INTEGER DEFAULT 0,"
        "PRIMARY KEY(alias,stage)) WITHOUT ROWID"
    )
    receipt = report.get("source_receipt") or {}
    generations = receipt.get("partition_generations")
    result = dict(
        status="unavailable",
        bytes_read=0,
        records_decoded=0,
        invalid_event_identity_n=0,
        malformed_records=0,
        committed_identity_invalid_n=0,
        bound_projection_anchors=0,
    )
    if not isinstance(generations, dict):
        result["reason"] = "partition_generation_receipt_missing"
        return result
    total = 0
    for name, expected in generations.items():
        path = Path(name)
        if (
            not path.is_absolute()
            or not path.resolve().is_relative_to(data_root)
            or path.is_symlink()
            or any(p.is_symlink() for p in path.parents)
            or type(expected.get("size")) is not int
            or expected["size"] < 0
        ):
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
                if (
                    consumed > expected["size"]
                    or result["bytes_read"] + consumed > MAX_COMPACT_BYTES
                ):
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
                    identity_valid = row.get(
                        "execution_source_event_sha256"
                    ) == execution_projection_identity(row)
                except (ValueError, TypeError, OverflowError):
                    identity_valid = False
                if not identity_valid:
                    result["invalid_event_identity_n"] += 1
                    continue
                fields = row.get("fields")
                if not isinstance(fields, dict):
                    continue
                stage = row.get("stage")
                if row.get("family") != "pre_submit_delay" or stage not in {
                    "pre_submit_delay_committed",
                    "pre_submit_delay_quote_observed",
                }:
                    continue
                if (
                    stage == "pre_submit_delay_quote_observed"
                    and initial.number(fields.get("target_delay_sec")) != 0
                ):
                    continue
                if stage == "pre_submit_delay_committed" and fields.get(
                    "decision_source_sha256"
                ) != owner.decision_source_sha256(fields):
                    result["committed_identity_invalid_n"] += 1
                    continue
                alias = initial.digest(
                    [
                        str(row.get("emitted_date")),
                        str(row.get("stock_code")),
                        str(fields.get("delay_intent_id") or ""),
                    ]
                )
                sha = initial.digest(fields)
                db.execute(
                    "INSERT INTO compact(alias,stage,sha,body) VALUES (?,?,?,?) "
                    "ON CONFLICT(alias,stage) DO UPDATE SET conflict=CASE WHEN compact.sha!=excluded.sha "
                    "THEN 1 ELSE compact.conflict END",
                    (alias, stage, sha, storage.encoded(fields).decode()),
                )
            if source_stat(os.fstat(handle.fileno())) != before:
                raise ValueError("delay_review_compact_generation_changed")
        if (
            source_stat(path.stat()) != before
            or consumed != expected["size"]
            or stream_sha.hexdigest() != expected["sha256"]
        ):
            raise ValueError("delay_review_compact_generation_changed")
        result["bytes_read"] += consumed
    result["status"] = "complete"
    return result


def _enrich(db, row, receipt):
    """Bind extra facts to the original alias and decision hash, never replace it."""
    alias = initial.digest(row["alias"])
    found = dict(
        db.execute(
            "SELECT stage,body FROM compact WHERE alias=? AND conflict=0", (alias,)
        )
    )
    commit = (
        json.loads(found["pre_submit_delay_committed"])
        if "pre_submit_delay_committed" in found
        else None
    )
    result = dict(row)
    features = dict(row.get("execution_features") or {})
    if commit and commit.get("decision_source_sha256") == row.get(
        "decision_source_sha256"
    ):
        receipt["bound_projection_anchors"] += 1
        proof = commit.get("entry_auxiliary_policy_identity")
        if proof:
            from src.engine.scalping.reversal_auxiliary_registry import (
                timing_compatibility_identity,
                validate_identity,
            )

            try:
                proof = validate_identity(
                    json.loads(proof) if isinstance(proof, str) else proof
                )
                if (
                    proof["identity_sha256"]
                    == row.get(
                        "captured_parent_compatibility", row["parent_compatibility"]
                    )[1]
                ):
                    result["auxiliary_timing_compatibility_sha256"] = (
                        timing_compatibility_identity(proof)
                    )
            except (ValueError, TypeError, KeyError):
                receipt["compatibility_identity_unverified_n"] = (
                    receipt.get("compatibility_identity_unverified_n", 0) + 1
                )
        machine = commit.get("original_machine_observation_sha256")
        native = (
            commit.get("original_evaluation_attempt_id")
            or commit.get("evaluation_attempt_id")
            or commit.get("request_id")
        )
        if _sha(machine) and isinstance(native, str) and native:
            if row.get("original_machine_observation_sha256") not in (
                None,
                machine,
            ) or row.get("native_evaluation_attempt_id") not in (None, native):
                raise ValueError("delay_review_enrichment_native_identity_conflict")
            result.setdefault("original_machine_observation_sha256", machine)
            result.setdefault("native_evaluation_attempt_id", native)
        reference = initial.number(commit.get("original_signal_reference_price"))
        epoch = initial.number(commit.get("original_signal_reference_epoch"))
        stamp = initial.number(commit.get("decision_committed_at_epoch"))
        signal_id = commit.get("original_signal_id")
        if (
            commit.get("signal_reference_contract_version")
            == "native_confirmation_price_v1"
            and reference is not None
            and reference > 0
            and epoch is not None
            and stamp is not None
            and 0 < epoch <= stamp
            and isinstance(signal_id, str)
            and 0 < len(signal_id) <= 512
        ):
            for name, value in (
                ("original_signal_reference_price", reference),
                ("original_signal_reference_epoch", epoch),
                ("original_signal_id", signal_id),
            ):
                if features.get(name) not in (None, value):
                    raise ValueError(
                        "delay_review_enrichment_signal_reference_conflict"
                    )
                features[name] = value
        quote = (
            json.loads(found["pre_submit_delay_quote_observed"])
            if "pre_submit_delay_quote_observed" in found
            else None
        )
        if quote and row["p0_valid"]:
            from src.engine.scalping.pre_submit_delay_tuning import _quote_source_issue

            ask, bid = initial.number(quote.get("ask_price")), initial.number(
                quote.get("best_bid")
            )
            if (
                not _quote_source_issue(commit, quote)
                and ask is not None
                and bid is not None
                and 0 < bid <= ask
                and str(quote.get("quote_valid")).lower() in {"true", "1"}
            ):
                features.setdefault("p0_ask", ask)
                features.setdefault("p0_bid", bid)
        # current_price_observed / price_cap are sizing/preparation facts. They
        # are not substituted for the original machine signal reference price.
    result["execution_features"] = features
    return result


def _populate(db, root, report, compact_receipt):
    from .pre_submit_delay_situation_projection import machine_parent_mapping

    machine_parents = machine_parent_mapping(
        report.get("machine_parent_compatibility"), target_date=report["effective_date"]
    )
    db.executescript("""
        CREATE TABLE population (
            id TEXT PRIMARY KEY, gid TEXT, day TEXT, symbol TEXT, anchor TEXT,
            session TEXT, situation TEXT, at REAL, end REAL, p0 INTEGER,
            native INTEGER, opportunity TEXT, spread_bp REAL, progress_bp REAL,
            compatibility_gid TEXT, split TEXT DEFAULT 'unqualified'
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
        if (
            not _sha(row.get("identity"))
            or not isinstance(alias, list)
            or len(alias) != 3
            or not isinstance(alias[0], str)
            or not isinstance(alias[1], str)
            or not isinstance(parents, list)
            or len(parents) != 2
            or any(not isinstance(p, str) for p in parents)
            or row.get("anchor_kind") not in {"price_ready", "signal_ready"}
            or not isinstance(row.get("session"), str)
            or not isinstance(row.get("situation"), str)
            or type(row.get("p0_valid")) is not bool
            or type(row.get("native_evaluation_bound")) is not bool
            or initial.number(row.get("committed_at")) is None
            or initial.number(row.get("observation_end_at")) is None
            or not isinstance(row.get("pairs"), dict)
        ):
            raise ValueError("delay_review_projection_invalid")
        date.fromisoformat(alias[0])
        row = _enrich(db, row, compact_receipt)
        independent = _independent_identity(row)
        features = row.get("execution_features") or {}
        ask, bid = initial.number(features.get("p0_ask")), initial.number(
            features.get("p0_bid")
        )
        spread = (
            (ask - bid) / ask * 10000
            if ask is not None and bid is not None and 0 < bid <= ask
            else None
        )
        reference = initial.number(features.get("original_signal_reference_price"))
        progress = (
            (ask - reference) / reference * 10000
            if ask is not None and reference is not None and reference > 0
            else None
        )
        counts["p0_spread_bp_available_anchors"] += spread is not None
        counts["original_signal_price_progress_available_anchors"] += (
            progress is not None
        )
        counts["independent_identity_bound_anchors"] += independent is not None
        counts["p0_valid_anchors"] += row["p0_valid"]
        counts["native_evaluation_bound_anchors"] += row["native_evaluation_bound"]
        counts["unknown_situation_anchors"] += row["situation"] == "UNKNOWN"
        counts["exact_parent_bound_anchors"] += all(_sha(p) for p in parents)
        # Older qualified projections do not preserve these pre-known features.
        # Their absence cannot be repaired from a later quote or today's catalog.
        for name in (
            "original_signal_reference_price",
            "original_signal_reference_epoch",
            "original_signal_id",
            "p0_ask",
            "p0_bid",
            "p0_ask_qty",
            "p0_actual_offset_sec",
            "p0_source_age_sec",
        ):
            counts["available:" + name] += features.get(name) is not None
        for name in (
            "delay_recheck_requested_at_epoch",
            "delay_recheck_completed_at_epoch",
            "delay_terminal_reason",
        ):
            counts["available:" + name] += row.get(name) is not None
        counts["identical_machine_parent_mapped_anchors"] += (
            machine_parents.get(parents[0], parents[0]) != parents[0]
        )
        parents = [machine_parents.get(parents[0], parents[0]), parents[1]]
        compatible = [
            parents[0],
            row.get("auxiliary_timing_compatibility_sha256", parents[1]),
        ]
        db.execute(
            "INSERT INTO population(id,gid,day,symbol,anchor,session,situation,at,end,p0,native,opportunity,spread_bp,progress_bp,compatibility_gid) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                row["identity"],
                _group(row["anchor_kind"], row["session"], parents),
                alias[0],
                alias[1],
                row["anchor_kind"],
                row["session"],
                row["situation"],
                row["committed_at"],
                row["observation_end_at"],
                int(row["p0_valid"]),
                int(row["native_evaluation_bound"]),
                independent,
                spread,
                progress,
                _group(row["anchor_kind"], row["session"], compatible),
            ),
        )
        all_pairs = dict(row["pairs"])
        for horizon, value in (row.get("research_short_pairs") or {}).items():
            if str(horizon) in {str(k) for k in all_pairs}:
                raise ValueError("delay_review_short_horizon_overlap")
            if (
                str(horizon) not in {"1", "3", "5"}
                or row.get("research_short_p0_valid") is not True
            ):
                raise ValueError("delay_review_short_pair_contract_invalid")
            all_pairs[str(horizon)] = value
        for horizon, value in all_pairs.items():
            delay, bp = initial.number(horizon), initial.number(value)
            if (
                delay is None
                or not 0 < delay <= MAX_HORIZON_SEC
                or bp is None
                or not row["p0_valid"]
            ):
                raise ValueError("delay_review_pair_invalid")
            horizons.add(delay)
            if len(horizons) > MAX_HORIZONS:
                raise ValueError("delay_review_horizon_budget_exceeded")
            db.execute("INSERT INTO pairs VALUES (?,?,?)", (row["identity"], delay, bp))
            counts["horizon_pairs"] += 1
            if delay in {1, 3, 5}:
                counts["short_pairs:" + str(int(delay))] += 1
    for index, partition in enumerate(
        storage.iter_tree(root, report["partitions_ref"]), 1
    ):
        if index > MAX_PARTITIONS:
            raise ValueError("delay_review_partition_budget_exceeded")
        body = {k: v for k, v in partition.items() if k != "sha256"}
        if partition.get("sha256") != initial.digest(storage.logical_value(body)):
            raise ValueError("delay_review_partition_hash_invalid")
        gid = _group(
            partition["anchor_kind"],
            partition["session"],
            partition["parent_compatibility"],
        )
        db.execute("INSERT INTO partitions VALUES (?,?)", (gid, partition["sha256"]))
        for member in storage.iter_tree(root, partition["membership"]):
            split = member.get("split")
            if split not in {"train", "validation", "purged", "unqualified"}:
                raise ValueError("delay_review_partition_split_invalid")
            prior = db.execute(
                "SELECT gid,p0,split FROM population WHERE id=?",
                (member.get("identity"),),
            ).fetchone()
            if (
                prior is None
                or prior[0] != gid
                or prior[1] != 1
                or prior[2] != "unqualified"
            ):
                raise ValueError("delay_review_partition_member_invalid")
            # A separately keyed table detects duplicates even for unqualified.
            db.execute("INSERT INTO membership(id) VALUES (?)", (member["identity"],))
            db.execute(
                "UPDATE population SET split=? WHERE id=?", (split, member["identity"])
            )
    if db.execute(
        "SELECT count(*) FROM population p WHERE p.p0=1 AND NOT EXISTS "
        "(SELECT 1 FROM membership r WHERE r.id=p.id)"
    ).fetchone()[0]:
        raise ValueError("delay_review_partition_membership_missing")
    census = report.get("census") or {}
    for key, observed in (
        ("qualified_pass_n", counts["anchors"]),
        ("p0_valid_n", counts["p0_valid_anchors"]),
    ):
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
        values = [
            r[0]
            for r in db.execute(ordered + " LIMIT ? OFFSET ?", (*args, hi - lo + 1, lo))
        ]
        return values[0] + (values[-1] - values[0]) * (at - lo)

    total = math.fsum(v for v, in db.execute(ordered, args))
    signs = db.execute(
        "SELECT sum(v>0),sum(v<0),sum(v=0) FROM (" + query + ")", args
    ).fetchone()
    return dict(
        n=n,
        eligible_n=denominator,
        coverage=n / denominator if denominator else 0,
        mean_bp=total / n if n else None,
        median_bp=quantile(0.5),
        p10_bp=quantile(0.1),
        p90_bp=quantile(0.9),
        improved_n=signs[0] or 0,
        worsened_n=signs[1] or 0,
        equal_n=signs[2] or 0,
    )


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
        if cell.get("comparison_delay_sec") is not None and not cell.get(
            "validation", {}
        ).get("n"):
            return "selected_training_candidate_holdout_pair_unavailable"
        return "unsupported_existing_selection_contract"
    return "unrecognized_selection_basis"


def _fallback(db, item, supported_anchor):
    key, cell = item["key"], item["value"]
    fallback_key = initial.cell_key(
        cell["anchor_kind"], cell["session"], parents=cell["parent_compatibility"]
    )
    path, resolved, resolved_key = [key], None, None
    for candidate_key in dict.fromkeys((key, fallback_key)):
        body = db.execute(
            "SELECT body FROM records WHERE id=?", ("cell:" + candidate_key,)
        ).fetchone()
        candidate = json.loads(body[0])["value"] if body else None
        if candidate_key != key:
            path.append(candidate_key)
        if (
            candidate
            and candidate.get("delay_sec") is not None
            and candidate.get("runtime_apply_allowed") is not False
        ):
            resolved, resolved_key = candidate["delay_sec"], candidate_key
            break
    if resolved is None:
        resolved = 0
        path.append("policy_default:0")
    anchor_supported = cell["anchor_kind"] == supported_anchor == "price_ready"
    return dict(
        research_cell_or_parent_delay_sec=resolved,
        resolved_cell_key=resolved_key,
        resolution_path=path,
        runtime_policy_anchor_supported=anchor_supported,
        prepared_policy_lookup_delay_sec=resolved if anchor_supported else 0,
        actual_pid_consumption_verified=False,
    )


def _cell_review(db, item, horizons, supported_anchor):
    key, cell = item["key"], item["value"]
    expected = initial.cell_key(
        cell["anchor_kind"],
        cell["session"],
        cell["situation"],
        cell["execution_context"],
        parents=cell["parent_compatibility"],
    )
    where, args = _where(cell)
    partition = db.execute(
        "SELECT sha FROM partitions WHERE gid=?", (args[0],)
    ).fetchone()
    if (
        key != expected
        or partition is None
        or partition[0] != cell.get("partition_sha256")
    ):
        raise ValueError("delay_review_cell_partition_invalid")
    candidates, overlap = {}, []
    membership = dict(
        db.execute(
            "SELECT split,count(*) FROM population p WHERE "
            + where
            + " GROUP BY split",
            args,
        )
    )
    for delay in horizons:
        value = {}
        for split in ("train", "validation", "purged", "unqualified"):
            condition, parameters = _where(cell, split=split)
            query = (
                "SELECT q.bp v FROM population p JOIN pairs q ON q.id=p.id WHERE "
                + condition
                + " AND q.horizon=?"
            )
            value[split] = _stats(
                db, query, (*parameters, delay), membership.get(split, 0)
            )
        candidates[str(int(delay)) if delay.is_integer() else str(delay)] = value
    for left_index, left in enumerate(horizons):
        for right in horizons[left_index + 1 :]:
            for split in ("train", "validation"):
                condition, parameters = _where(cell, split=split)
                base = (
                    " FROM population p JOIN pairs a ON a.id=p.id JOIN pairs b ON b.id=p.id "
                    "WHERE " + condition + " AND a.horizon=? AND b.horizon=?"
                )
                bind = (*parameters, left, right)
                denominator = membership.get(split, 0)
                overlap.append(
                    dict(
                        left_delay_sec=left,
                        right_delay_sec=right,
                        split=split,
                        left=_stats(db, "SELECT a.bp v" + base, bind, denominator),
                        right=_stats(db, "SELECT b.bp v" + base, bind, denominator),
                        left_minus_right=_stats(
                            db, "SELECT a.bp-b.bp v" + base, bind, denominator
                        ),
                    )
                )
    # Short-horizon diagnostics were never candidates of this frozen selector.
    # Their presence must not change the explanation of an unsupported cell.
    selected_candidates = cell.get("candidate_delays_sec")
    observed = (
        selected_candidates
        if isinstance(selected_candidates, list)
        else [
            d
            for d, stats in candidates.items()
            if stats["train"]["n"] and initial.number(d) in initial.HORIZONS[1:]
        ]
    )
    independent_n, identity_bound_n, anchors, days, symbols = db.execute(
        "SELECT count(DISTINCT p.opportunity),count(p.opportunity),count(*),count(DISTINCT p.day),"
        "count(DISTINCT p.symbol) FROM population p WHERE " + where,
        args,
    ).fetchone()
    research = [
        (float(delay), stats)
        for delay, stats in candidates.items()
        if stats["train"]["n"]
    ]
    winner, winner_stats = (
        min(research, key=lambda v: (-v[1]["train"]["mean_bp"], v[0]))
        if research
        else (None, None)
    )
    # A new diagnostic compares short observations without rewriting the sealed
    # selector, borrowing different parent generations, or choosing on holdout.
    direction = "indeterminate"
    if winner_stats and winner_stats["validation"]["n"]:
        train_mean, holdout_mean = (
            winner_stats["train"]["mean_bp"],
            winner_stats["validation"]["mean_bp"],
        )
        if train_mean > 0 and holdout_mean > 0:
            direction = "positive_delay_supported"
        elif train_mean <= 0 and holdout_mean <= 0:
            direction = "immediate_supported_on_observed_pairs"
    return dict(
        key=key,
        original_cell=cell,
        selection_reason_raw=cell.get("selection_basis"),
        selection_reason_normalized=_reason(cell, observed),
        evidence_verdict=initial.selection_evidence(cell),
        optimal_delay_proven=False,
        selected_delay_sec=cell.get("delay_sec"),
        fallback_key=cell.get("fallback_key"),
        fallback_resolution=_fallback(db, item, supported_anchor),
        eligible_p0_anchors=anchors,
        distinct_source_dates=days,
        distinct_symbols=symbols,
        unique_independent_opportunities=(
            independent_n if identity_bound_n == anchors else None
        ),
        known_identity_subset_unique_opportunities=independent_n,
        frozen_partition_counts=membership,
        candidates=candidates,
        pairwise_common_cohort=overlap,
        expanded_grid_research=dict(
            train_selected_delay_sec=winner,
            evidence_verdict=direction,
            train=winner_stats["train"] if winner_stats else None,
            validation=winner_stats["validation"] if winner_stats else None,
            comparison_population="candidate_own_p0_pairs_consult_pairwise_common_cohort",
            policy_selection_authority=False,
        ),
        diagnostic_only=True,
        policy_reselected=False,
    )


def _contributions(db, cell_items, horizons):
    for item in cell_items:
        key, cell = item["key"], item["value"]
        where, args = _where(cell)
        for axis, field in (("source_date", "day"), ("symbol", "symbol")):
            for delay in horizons:
                for split, value, n, total in db.execute(
                    f"SELECT p.split,p.{field},count(*),sum(q.bp) FROM population p "
                    "JOIN pairs q ON p.id=q.id WHERE " + where + " AND q.horizon=? "
                    f"GROUP BY p.split,p.{field} ORDER BY p.split,p.{field}",
                    (*args, delay),
                ):
                    yield dict(
                        key=key,
                        axis=axis,
                        value=value,
                        split=split,
                        delay_sec=delay,
                        n=n,
                        sum_price_improvement_bp=total,
                        mean_price_improvement_bp=total / n,
                        metric_role="diagnostic_contribution_not_ev",
                    )


def _feature_groups(db, cell_items, horizons):
    """Fixed diagnostic groups; these cannot become policy-selection inputs."""
    specifications = (
        (
            "original_signal_price_progress",
            "progress_bp",
            (
                ("down", "p.progress_bp<0"),
                ("same", "p.progress_bp=0"),
                ("up", "p.progress_bp>0"),
            ),
        ),
        (
            "p0_spread_bp",
            "spread_bp",
            (
                ("zero", "p.spread_bp=0"),
                ("gt0_lt10bp", "p.spread_bp>0 AND p.spread_bp<10"),
                ("ge10bp", "p.spread_bp>=10"),
            ),
        ),
    )
    for item in cell_items:
        cell = item["value"]
        for feature, field, buckets in specifications:
            for label, predicate in buckets:
                for split in ("train", "validation"):
                    where, args = _where(cell, split=split)
                    denominator = db.execute(
                        "SELECT count(*) FROM population p WHERE " + where, args
                    ).fetchone()[0]
                    available = db.execute(
                        f"SELECT count(*) FROM population p WHERE {where} AND p.{field} IS NOT NULL",
                        args,
                    ).fetchone()[0]
                    if not available:
                        continue
                    bucket_n = db.execute(
                        "SELECT count(*) FROM population p WHERE "
                        + where
                        + " AND "
                        + predicate,
                        args,
                    ).fetchone()[0]
                    if not bucket_n:
                        continue
                    for delay in horizons:
                        query = (
                            "SELECT q.bp v FROM population p JOIN pairs q ON q.id=p.id WHERE "
                            + where
                            + " AND "
                            + predicate
                            + " AND q.horizon=?"
                        )
                        yield dict(
                            key=item["key"],
                            feature=feature,
                            bucket=label,
                            split=split,
                            delay_sec=delay,
                            original_split_n=denominator,
                            feature_available_n=available,
                            bucket_n=bucket_n,
                            stats=_stats(db, query, (*args, delay), bucket_n),
                            selection_authority=False,
                            group_boundaries="fixed_diagnostic_only",
                        )


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
        data_root, source_date, validate_selection=False
    )
    report, policy = initial._read(report_path), initial._read(policy_path)
    if (
        initial.digest(report) != manifest["report_artifact_sha256"]
        or initial.digest(policy) != manifest["policy_artifact_sha256"]
    ):
        raise ValueError("delay_review_generation_metadata_changed")
    if report.get("storage_schema") != "pre_submit_delay_sharded_evidence_v3":
        raise ValueError("delay_review_sharded_projection_required")
    if policy.get("cells_ref") != report.get("cells_ref"):
        raise ValueError("delay_review_policy_cells_mismatch")
    if (
        policy.get("default_delay_sec") != 0
        or report.get("default_delay_sec") != 0
        or policy.get("supported_anchor_kind") != "price_ready"
    ):
        raise ValueError("delay_review_policy_fallback_contract_invalid")
    for key, limit in (
        ("qualified_projection_ref", MAX_ANCHORS),
        ("cells_ref", MAX_CELLS),
        ("partitions_ref", MAX_PARTITIONS),
    ):
        ref = report.get(key)
        if (
            not isinstance(ref, dict)
            or type(ref.get("count")) is not int
            or not 0 <= ref["count"] <= limit
        ):
            raise ValueError("delay_review_evidence_count_or_budget_invalid")
    output.mkdir(parents=True, exist_ok=True)
    from src.engine.lifecycle.holding_window_generation import byte_generation

    code_before = dict(
        review_module_sha256=byte_generation(Path(__file__))["sha256"],
        reader_producer_contract_sha256=initial.code_contract(),
    )
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
                row = _cell_review(
                    db, item, horizons, policy.get("supported_anchor_kind")
                )
                reason_counts[row["selection_reason_normalized"]] += 1
                anchor_reasons[
                    (item["value"]["anchor_kind"], row["selection_reason_normalized"])
                ] += 1
                yield row

        cells_ref = storage.write_tree(output, reviewed())
        contributions_ref = storage.write_tree(
            output,
            _contributions(
                db, (row for _, row, _ in storage.records(db) if "key" in row), horizons
            ),
        )
        feature_groups_ref = storage.write_tree(
            output,
            _feature_groups(
                db, (row for _, row, _ in storage.records(db) if "key" in row), horizons
            ),
        )
        known_unique = db.execute(
            "SELECT count(DISTINCT opportunity) FROM population"
        ).fetchone()[0]
        by_anchor = [
            dict(
                anchor_kind=a,
                anchors=n,
                p0_valid_anchors=p0,
                pairs=pairs,
                independent_identity_bound_anchors=bound,
                known_identity_subset_unique_opportunities=unique,
                unique_independent_opportunities=unique if bound == n else None,
            )
            for a, n, p0, pairs, bound, unique in db.execute(
                "SELECT anchor,count(*),sum(p0),(SELECT count(*) FROM pairs q JOIN population z ON z.id=q.id "
                "WHERE z.anchor=p.anchor),count(opportunity),count(DISTINCT opportunity) "
                "FROM population p GROUP BY anchor ORDER BY anchor"
            )
        ]
        split_ref = storage.write_tree(
            output,
            (
                dict(
                    identity=i,
                    source_date=d,
                    symbol=s,
                    anchor_kind=a,
                    committed_at=at,
                    observation_end_at=end,
                    split=split,
                    independent_opportunity_sha256=opp,
                )
                for i, d, s, a, at, end, split, opp in db.execute(
                    "SELECT id,day,symbol,anchor,at,end,split,opportunity FROM population ORDER BY at,id"
                )
            ),
        )
        compatibility_ref = storage.write_tree(
            output,
            (
                dict(
                    compatibility_group=group,
                    anchor_kind=anchor,
                    session=market,
                    anchors=n,
                    original_parent_groups=parents,
                    source_dates=days,
                    symbols=symbols,
                    original_partitions_preserved=True,
                    policy_selection_authority=False,
                )
                for group, anchor, market, n, parents, days, symbols in db.execute(
                    "SELECT compatibility_gid,anchor,session,count(*),count(DISTINCT gid),count(DISTINCT day),"
                    "count(DISTINCT symbol) FROM population WHERE p0=1 AND native=1 "
                    "GROUP BY compatibility_gid,anchor,session ORDER BY compatibility_gid"
                )
            ),
        )
    if byte_generation(pointer) != generation_before:
        raise ValueError("delay_review_committed_pointer_changed")
    if code_before != dict(
        review_module_sha256=byte_generation(Path(__file__))["sha256"],
        reader_producer_contract_sha256=initial.code_contract(),
    ):
        raise ValueError("delay_review_code_changed_during_read")
    all_identity_bound = (
        counts["independent_identity_bound_anchors"] == counts["anchors"]
    )
    result = dict(
        schema=SCHEMA,
        source_date=source_date,
        status="complete",
        partial=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        metric_role="initial_entry_price_timing_diagnostic",
        decision_authority="report_only",
        primary_decision_metric="mean_paired_price_improvement_bp",
        window_policy="immutable_committed_generation_and_original_frozen_partitions",
        sample_floor="none_added_existing_selection_preserved",
        source_quality_gate="sealed_manifest_pair_and_fully_consumed_evidence_tree_hashes",
        forbidden_uses=[
            "policy_selection",
            "runtime_apply",
            "realized_profit_claim",
            "synthetic_recheck_pass",
        ],
        input=dict(
            manifest_path=str(pointer),
            manifest_sha256=manifest["manifest_sha256"],
            generation=manifest["generation"],
            source_sha256=manifest["source_sha256"],
            original_code_contract_sha256=manifest["code_contract_sha256"],
            report_artifact_sha256=manifest["report_artifact_sha256"],
            policy_artifact_sha256=manifest["policy_artifact_sha256"],
            qualified_projection_ref=report["qualified_projection_ref"],
            raw_source_reverified=False,
            consumed_projection_once=True,
        ),
        code_provenance=code_before,
        original_policy_status=policy.get("selection_status"),
        original_default_delay_sec=policy.get("default_delay_sec"),
        original_census=report.get("census"),
        horizons_sec=horizons,
        short_horizon_observation_status={
            str(delay): {
                "paired_observation_n": counts.get("short_pairs:" + str(delay), 0),
                "status": (
                    (
                        "observed_policy_candidate"
                        if policy.get("algorithm") == initial.ALGORITHM
                        else "observed_research_only"
                    )
                    if delay in horizons
                    else "no_historical_observation"
                ),
            }
            for delay in (1, 3, 5)
        },
        census={k: v for k, v in counts.items() if not k.startswith("available:")},
        unique_independent_opportunities=known_unique if all_identity_bound else None,
        known_identity_subset_unique_opportunities=known_unique,
        independent_identity_status=(
            "complete"
            if all_identity_bound
            else "partial_native_identity_not_preserved"
        ),
        by_anchor=by_anchor,
        selection_reason_counts=dict(reason_counts),
        cells_ref=cells_ref,
        supported_policy_anchor_kind=policy.get("supported_anchor_kind"),
        selection_reason_counts_by_anchor={
            anchor: {
                reason: n for (a, reason), n in anchor_reasons.items() if a == anchor
            }
            for anchor in sorted({a for a, _ in anchor_reasons})
        },
        cell_count_role="overlapping_parent_and_situation_cells_not_independent_opportunities",
        default_delay_interpretation="existing_behavior_without_comparative_evidence",
        contributions_ref=contributions_ref,
        frozen_membership_ref=split_ref,
        semantic_compatibility_ref=compatibility_ref,
        compatibility_contract=(
            "native_identical_machine_parents_and_exact_auxiliary_timing_identity"
            if report.get("machine_parent_compatibility")
            else "exact_machine_prompt_model_options_validator_and_schema_except_local_fact_alias"
        ),
        feature_groups_ref=feature_groups_ref,
        compact_enrichment=compact_receipt,
        preserved_field_coverage={
            k.removeprefix("available:"): v
            for k, v in counts.items()
            if k.startswith("available:")
        },
        analysis_availability=dict(
            price_progress_grouping=(
                "available_for_preserved_subset"
                if counts["original_signal_price_progress_available_anchors"]
                else "unavailable_original_signal_reference_not_preserved"
            ),
            spread_bp_grouping=(
                "available_for_preserved_subset"
                if counts["p0_spread_bp_available_anchors"]
                else "unavailable_frozen_p0_bid_ask"
            ),
            spread_tick_grouping="unavailable_explicit_frozen_tick_size",
            recheck_pass="not_inferred_from_quote_path",
            opportunity_retention="requires_exact_recheck_outcome",
            paired_net_ev_delta_pct=None,
            realized_pnl_krw=None,
        ),
        limits=dict(
            max_anchors=MAX_ANCHORS,
            max_cells=MAX_CELLS,
            max_partitions=MAX_PARTITIONS,
            max_horizons=MAX_HORIZONS,
            maximum_shard_record_bytes=storage.RECORD_BYTES,
            max_compact_bytes=MAX_COMPACT_BYTES,
            max_compact_records=MAX_COMPACT_RECORDS,
            max_durable_output_bytes=MAX_DURABLE_BYTES,
            max_temporary_bytes=MAX_TEMP_BYTES,
            exceeded_limit_behavior="fail_before_publishing_new_complete_report",
        ),
    )
    result["artifact_sha256"] = initial.digest(result)
    destination = output / "report.json"
    if destination.exists() and initial._read(destination) != result:
        raise ValueError("delay_review_immutable_report_conflict")
    initial._atomic(destination, result)
    return result


def _epoch(value):
    numeric = initial.number(value)
    if numeric is not None:
        return numeric
    try:
        stamp = datetime.fromisoformat(str(value))
        return (
            stamp.replace(tzinfo=ZoneInfo("Asia/Seoul"))
            if stamp.tzinfo is None
            else stamp
        ).timestamp()
    except ValueError:
        return None


def _trade_census(through_date):
    """Read position records in one read-only transaction; no DBManager/migrations."""
    from sqlalchemy import create_engine, text
    from src.utils.constants import POSTGRES_URL

    end = date.fromisoformat(through_date) + timedelta(days=1)
    engine = create_engine(
        POSTGRES_URL,
        connect_args={
            "connect_timeout": 3,
            "options": "-c default_transaction_read_only=on -c statement_timeout=5000",
        },
    )
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id,stock_code AS code,strategy,position_tag,status,buy_time,buy_price,buy_qty,"
                    "initial_buy_qty,add_count,sell_time FROM recommendation_history "
                    "WHERE buy_time>=:start AND buy_time<:end AND buy_qty>0 "
                    "AND strategy IN ('SCALPING','SCALP') ORDER BY buy_time,id LIMIT :limit"
                ),
                dict(start="2026-06-05", end=end.isoformat(), limit=MAX_ANCHORS + 1),
            )
            result = [
                {
                    k: v.isoformat() if isinstance(v, (datetime, date)) else v
                    for k, v in row.items()
                }
                for row in rows.mappings()
            ]
    finally:
        engine.dispose()
    if len(result) > MAX_ANCHORS:
        raise ValueError("delay_review_trade_census_budget_exceeded")
    return result


def _execution_sources(data_root, days):
    """Reuse native indexed projections. A missing index never triggers a raw scan."""
    from . import main_trailing_source_store as native

    rows, sources, gaps = [], [], []
    retained = 0
    for day in days:
        path = data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
        if not (
            data_root
            / "report/main_trailing_source_index"
            / day
            / "pipeline_events.sqlite"
        ).is_file():
            gaps.append(dict(source_date=day, reason="native_pipeline_index_absent"))
            continue
        before = len(rows)
        try:
            snapshot = {}
            for value, reference in native.read_rows(
                data_root,
                path,
                kinds=("delay_receipt", "pipeline_receipt"),
                snapshot_receipt=snapshot,
            ):
                encoded = storage.encoded(value)
                retained += len(encoded)
                if retained > MAX_COMPACT_BYTES or len(rows) >= MAX_COMPACT_RECORDS:
                    raise ValueError("delay_review_execution_source_budget_exceeded")
                row = value["row"]
                rows.append((row, reference))
            sources.append(
                dict(source_date=day, **snapshot, selected_rows=len(rows) - before)
            )
        except (OSError, ValueError) as exc:
            del rows[before:]
            gaps.append(dict(source_date=day, reason=str(exc)[:160]))
            if (
                retained > MAX_COMPACT_BYTES
                or str(exc) == "delay_review_execution_source_budget_exceeded"
            ):
                raise ValueError(
                    "delay_review_execution_source_budget_exceeded"
                ) from exc
    return rows, dict(
        sources=sources, gaps=gaps, bytes_decoded=retained, whole_raw_files_scanned=0
    )


def _native_fill_rows(data_root, day):
    """Read fill fields from the existing completed-store, without quote-tree copies."""
    from . import main_trailing_completed_store as native
    from src.engine.lifecycle.snapshot_archive import snapshot_identity
    from src.engine.lifecycle.holding_window_generation import byte_generation

    raw = data_root / "report/monitor_snapshots" / f"trade_review_{day}.json"
    dependency_path = raw.with_suffix(".completed_projection.json.dependencies.json")
    if not dependency_path.is_file():
        return None
    dependency = native._metadata(dependency_path)
    bound = native.binding(data_root, dependency)
    if not bound:
        return None
    allowed = data_root / "report/main_trailing_completed_source" / day
    manifest = Path(bound["manifest_path"])
    if (
        not manifest.resolve().is_relative_to(allowed / "generations")
        or byte_generation(manifest) != bound["manifest_generation"]
    ):
        raise ValueError("delay_review_native_fill_manifest_changed")
    body = native._metadata(manifest)
    original_cache_verified = (
        body.get("extraction_schema") == "original_sealed_completed_stream_v1"
    )
    if (
        body.get("schema") != native.SCHEMA
        or body.get("source_date") != day
        or dependency.get("date") != day
        or body.get("source_data_root") != str(data_root)
        or body.get("artifact_sha256") != bound.get("artifact_sha256")
        or body.get("projection_generation") != dependency.get("projection")
        or body.get("snapshot_identity") != dependency.get("snapshot_identity")
        or (
            not original_cache_verified
            and body["snapshot_identity"] != snapshot_identity(raw)
        )
        or body.get("census_sha256") != dependency.get("census_sha256")
        or body.get("completed_count") != dependency.get("completed_count")
        or body.get("runtime_effect") is not False
        or body.get("allowed_runtime_apply") is not False
        or type(body.get("completed_count")) is not int
        or not 0 <= body["completed_count"] <= MAX_ANCHORS
    ):
        raise ValueError("delay_review_native_fill_source_binding_invalid")
    fact_rows = {}
    scalar_ref = dependency.get("fact_projection")
    if scalar_ref:
        scalar = raw.with_suffix(".fact_projection.json")
        if (
            scalar_ref.get("size", 0) > 4 * 1024 * 1024
            or byte_generation(scalar) != scalar_ref
        ):
            raise ValueError("delay_review_native_fill_fact_changed")
        # The producer seals this plain JSON through the dependency receipt,
        # not an embedded artifact_sha256 like native index metadata.
        value = json.loads(scalar.read_bytes())
        if byte_generation(scalar) != scalar_ref:
            raise ValueError("delay_review_native_fill_fact_changed")
        if (
            value.get("date") != day
            or value.get("snapshot_identity") != body["snapshot_identity"]
        ):
            raise ValueError("delay_review_native_fill_fact_binding_invalid")
        fact_rows = {
            str(r["id"]): r
            for r in value.get("sections", {}).get("completed_trade_projection", [])
        }
    rows = []
    for item in storage.iter_tree(allowed, body["records_ref"]):
        if item["fields_ref"]["count"] > 256:
            raise ValueError("delay_review_native_fill_field_budget")
        fields = {}
        for field in storage.iter_tree(allowed, item["fields_ref"]):
            if field["key"] in fields:
                raise ValueError("delay_review_native_fill_duplicate_field")
            fields[field["key"]] = field["value"]
        legs = fields.get("buy_fill_legs_ref")
        if legs is not None:
            if legs["count"] > 10000:
                raise ValueError("delay_review_native_fill_leg_budget")
            fields["buy_fill_legs"] = list(storage.iter_tree(allowed, legs))
        if str(fields.get("id") or fields.get("record_id")) != item["record_id"]:
            raise ValueError("delay_review_native_fill_record_conflict")
        fact_time = fact_rows.get(item["record_id"], {}).get("buy_time")
        if (
            fact_time is not None
            and fields.get("buy_time") is not None
            and _epoch(fact_time) != _epoch(fields["buy_time"])
        ):
            raise ValueError("delay_review_native_fill_position_clock_conflict")
        fields["buy_time"] = (
            fact_time if fact_time is not None else fields.get("buy_time")
        )
        rows.append(fields)
    if (
        len(rows) != body["completed_count"]
        or native._metadata(dependency_path) != dependency
    ):
        raise ValueError("delay_review_native_fill_census_changed")
    return rows, {
        **bound["manifest_generation"],
        "path": str(manifest),
        "artifact_sha256": body["artifact_sha256"],
        "source_kind": "native_completed_fill_fields",
    }


def _snapshot_fills(data_root, days):
    """Small recorded fill projections only; large sources retain an explicit gap."""
    from src.engine.lifecycle.holding_window_generation import source_stat
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_legs

    fills, sources, gaps = {}, [], []
    total = 0
    for day in days:
        try:
            native = _native_fill_rows(data_root, day)
        except (OSError, ValueError) as exc:
            gaps.append(dict(source_date=day, reason=str(exc)[:160]))
            continue
        path = data_root / "report/monitor_snapshots" / f"trade_review_{day}.json"
        if native is None and not path.is_file():
            gaps.append(dict(source_date=day, reason="fill_snapshot_absent"))
            continue
        if native is not None:
            records, source = native
        else:
            before = source_stat(path.stat())
            if before[2] > 16 * 1024 * 1024 or total + before[2] > MAX_COMPACT_BYTES:
                gaps.append(
                    dict(
                        source_date=day,
                        reason="fill_snapshot_requires_native_projection",
                    )
                )
                continue
            with path.open("rb") as handle:
                raw = handle.read(16 * 1024 * 1024 + 1)
            if len(raw) != before[2] or source_stat(path.stat()) != before:
                raise ValueError("delay_review_fill_snapshot_changed")
            value = json.loads(raw)
            if value.get("date") != day:
                raise ValueError("delay_review_fill_snapshot_date_invalid")
            total += len(raw)
            source = dict(
                path=str(path), sha256=hashlib.sha256(raw).hexdigest(), size=len(raw)
            )
            records = value.get("sections", {}).get("completed_trade_projection", [])
        sources.append(source)
        for row in records:
            legs = row.get("buy_fill_legs")
            identity = buy_fill_identity_from_legs(legs)
            if identity is None:
                continue
            valid = all(
                _epoch(leg.get("at")) is not None
                and (initial.number(leg.get("price")) or 0) > 0
                for leg in legs
            )
            if not valid:
                continue
            key = str(row.get("id"))
            item = dict(
                code=row.get("code"),
                legs=legs,
                buy_fill_identity=identity,
                source=source,
                position_buy_time=row.get("buy_time"),
            )
            if key in fills and fills[key]["buy_fill_identity"] != identity:
                raise ValueError("delay_review_fill_snapshot_conflict")
            fills[key] = item
    return fills, dict(
        sources=sources,
        gaps=gaps,
        legacy_snapshot_bytes_read=total,
        native_read_scope="bound_metadata_and_fill_fields_only",
    )


def _timing_opportunities(events):
    """Exact native machine/attempt -> frozen plan -> record, never a time-nearest join."""
    from src.engine.scalping import trailing_entry_research_source as plans

    delays = [
        row for row, _ in events if row.get("stage", "").startswith("pre_submit_delay_")
    ]
    opportunities, census = initial.project_rows(delays)
    plans_by_attempt, orders, quotes = {}, {}, {}
    for row, reference in events:
        fields = row.get("fields") or {}
        rid = str(row.get("record_id"))
        stage = row.get("stage")
        if stage == "entry_execution_sizing_plan":
            try:
                receipt = plans.validate(fields.get("trailing_entry_plan_receipt"))
            except (ValueError, TypeError, KeyError):
                continue
            if (
                receipt["symbol"] != row.get("stock_code")
                or receipt["position_key"] != "record:" + rid
                or fields.get("trailing_entry_plan_receipt_sha256")
                not in (None, "", receipt["receipt_sha256"])
            ):
                continue
            key = (
                row["emitted_date"],
                row["stock_code"],
                receipt["machine_observation_sha256"],
                receipt["evaluation_attempt_id"],
            )
            plans_by_attempt.setdefault(key, {})[receipt["receipt_sha256"]] = (
                rid,
                receipt,
            )
        elif (
            stage == "order_leg_sent"
            and fields.get("buy_owner_type") == "main_scalping"
        ):
            if (
                str(fields.get("actual_order_submitted")).lower() == "true"
                and fields.get("buy_owner_id") == "main_scalping:" + rid
            ):
                orders.setdefault(rid, set()).add(str(fields.get("order_no")))
        elif stage == "scalp_trailing_input_transition":
            from src.engine.scalping.universal_trailing_replay import (
                quote_source_digest,
                decode_quote,
            )

            try:
                q = fields.get("universal_trailing_quote")
                q = decode_quote(q)
                if not isinstance(q, dict) or q.get("kind") != "QUOTE":
                    continue
                known, event = initial.number(q.get("known_at")), initial.number(
                    q.get("event_at")
                )
                ask, bid = initial.number(q.get("ask")), initial.number(q.get("bid"))
                if (
                    known is None
                    or event is None
                    or not 0 <= known - event <= 0.7
                    or ask is None
                    or bid is None
                    or not 0 < bid <= ask
                    or str(q.get("item", ""))[:6] != row.get("stock_code")
                    or q.get("coverage_complete") is not True
                    or q.get("source_sha256") != quote_source_digest(q)
                ):
                    continue
                quotes.setdefault(rid, []).append(
                    dict(
                        symbol=row["stock_code"],
                        known_at=known,
                        ask=ask,
                        bid=bid,
                        midpoint=(ask + bid) / 2,
                        source_sha256=q["source_sha256"],
                        source=reference,
                    )
                )
            except (ValueError, TypeError):
                continue
    commits = {
        (r["emitted_date"], r["stock_code"], r["fields"]["delay_intent_id"]): r[
            "fields"
        ]
        for r in delays
        if r["stage"] == "pre_submit_delay_committed"
    }
    terminals, quote_fields = {}, {}
    for row, reference in events:
        if row["stage"] == "pre_submit_delay_quote_observed":
            fields = row["fields"]
            key = (row["emitted_date"], row["stock_code"], fields["delay_intent_id"])
            horizon = initial.number(fields.get("target_delay_sec"))
            quote_fields.setdefault(key, {}).setdefault(horizon, {})[
                initial.digest(fields)
            ] = (fields, reference)
        if row["stage"] == "pre_submit_delay_intent_terminal":
            fields = row["fields"]
            key = (row["emitted_date"], row["stock_code"], fields["delay_intent_id"])
            terminals.setdefault(key, []).append(fields)
    result = []
    for opportunity in opportunities:
        alias = tuple(opportunity["alias"])
        commit = commits[alias]
        attempt = commit.get("original_evaluation_attempt_id") or commit.get(
            "evaluation_attempt_id"
        )
        key = (*alias[:2], commit.get("original_machine_observation_sha256"), attempt)
        matches = plans_by_attempt.get(key, {})
        rid, plan = next(iter(matches.values())) if len(matches) == 1 else (None, None)
        # Delay observations may outlive a position's trailing observer. Use
        # those exact, validated quotes too; otherwise a later price decline
        # disappears merely because the position was already closed.
        if rid is not None:
            from src.engine.scalping.pre_submit_delay_tuning import _quote_source_issue

            for observations in quote_fields.get(alias, {}).values():
                if len(observations) != 1:
                    continue
                q, reference = next(iter(observations.values()))
                known = initial.number(q.get("quote_observed_at_epoch"))
                ask, bid = initial.number(q.get("ask_price")), initial.number(
                    q.get("best_bid")
                )
                if (
                    known is None
                    or ask is None
                    or bid is None
                    or not 0 < bid <= ask
                    or str(q.get("quote_valid")).lower() not in {"true", "1"}
                    or _quote_source_issue(commit, q)
                ):
                    continue
                quotes.setdefault(rid, []).append(
                    dict(
                        symbol=alias[1],
                        known_at=known,
                        ask=ask,
                        bid=bid,
                        midpoint=(ask + bid) / 2,
                        source_sha256=q["quote_source_sha256"],
                        source=reference,
                        source_stage="pre_submit_delay_quote_observed",
                        delay_intent_id=alias[2],
                        native_plan_sha256=plan["receipt_sha256"],
                    )
                )
        terminal = terminals.get(alias, [])
        unique = {initial.digest(t): t for t in terminal}
        terminal = next(iter(unique.values())) if len(unique) == 1 else {}
        if (
            terminal.get("decision_source_sha256")
            != opportunity["decision_source_sha256"]
        ):
            terminal = {}
        pairs = {
            **opportunity["pairs"],
            **(opportunity.get("research_short_pairs") or {}),
        }
        comparisons = []
        first_leg = (
            next(iter(plan["execution_plan"].get("legs") or []), {}) if plan else {}
        )
        cap, qty = initial.number(first_leg.get("numeric_price")), initial.number(
            first_leg.get("qty")
        )
        for horizon, improvement in sorted(pairs.items(), key=lambda x: float(x[0])):
            observed = quote_fields.get(alias, {}).get(float(horizon), {})
            q = next(iter(observed.values()))[0] if len(observed) == 1 else {}
            ask, depth = initial.number(q.get("ask_price")), initial.number(
                q.get("ask_qty")
            )
            comparisons.append(
                dict(
                    delay_sec=float(horizon),
                    price_improvement_bp=improvement,
                    ask_price=ask,
                    ask_qty=depth,
                    quote_source_sha256=q.get("quote_source_sha256"),
                    first_leg_price=cap,
                    first_leg_qty=qty,
                    first_leg_quote_price_depth_supported=(
                        ask <= cap and depth >= qty
                        if ask is not None
                        and cap is not None
                        and depth is not None
                        and qty is not None
                        else None
                    ),
                    executable_fill=None,
                    recheck_and_other_guards="unobserved_for_counterfactual",
                )
            )
        result.append(
            dict(
                identity=opportunity["identity"],
                source_date=alias[0],
                symbol=alias[1],
                delay_intent_id=alias[2],
                anchor_kind=opportunity["anchor_kind"],
                session=opportunity["session"],
                situation=opportunity["situation"],
                parents=opportunity["parent_compatibility"],
                committed_at=opportunity["committed_at"],
                native_evaluation_attempt_id=attempt,
                record_id=rid,
                record_link_status=(
                    "exact_native_plan" if rid else "missing_or_conflicting_native_plan"
                ),
                plan_sha256=plan["receipt_sha256"] if plan else None,
                planned_total_qty=plan["execution_plan"]["total_qty"] if plan else None,
                selected_delay_sec=initial.number(commit.get("selected_delay_sec")),
                runtime_policy_status=commit.get("delay_policy_status"),
                terminal_reason=terminal.get("terminal_reason"),
                submit_finished_at_epoch=initial.number(
                    terminal.get("submit_finished_at_epoch")
                ),
                same_opportunity_price_improvement_bp={
                    str(k): v
                    for k, v in sorted(pairs.items(), key=lambda x: float(x[0]))
                },
                candidate_comparisons=comparisons,
                execution_recheck_status="not_inferred_from_quote_path",
                modeled_fill=None,
                paired_net_ev_delta_pct=None,
                historical_tuning_eligible=alias[0] >= "2026-09-29",
            )
        )
    return result, quotes, orders, census


def _fill_path(trade, fill, quotes, orders):
    rid = str(trade["id"])
    result = dict(
        record_id=rid,
        symbol=trade["code"],
        status=trade["status"],
        recorded_buy_time=trade["buy_time"],
        recorded_buy_price=trade["buy_price"],
        recorded_buy_qty=trade["buy_qty"],
        anchors=[],
        realized_pnl_krw=None,
        economics_status="not_evaluated_no_exact_cost_binding",
        anchor_status="exact_fill_clock_unavailable",
        main_owner_verified=False,
    )
    if not fill:
        return result
    legs = fill["legs"]
    if (
        fill["code"] != trade["code"]
        or sum(leg["qty"] for leg in legs) != trade["buy_qty"]
        or _epoch(fill.get("position_buy_time")) != _epoch(trade["buy_time"])
        or (trade.get("add_count") or 0) != 0
    ):
        result["anchor_status"] = "position_generation_or_scale_in_conflict"
        return result
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_legs

    if buy_fill_identity_from_legs(legs) != fill["buy_fill_identity"]:
        raise ValueError("delay_review_fill_identity_invalid")
    ordered = sorted(legs, key=lambda leg: _epoch(leg["at"]))
    result["main_owner_verified"] = ordered[0]["order_no"] in orders.get(rid, set())
    result["all_leg_order_owner_receipts_observed"] = all(
        leg["order_no"] in orders.get(rid, set()) for leg in legs
    )
    if not result["main_owner_verified"]:
        result["anchor_status"] = "main_order_owner_unverified"
        return result
    result.update(
        anchor_status="exact_first_and_last_recorded_fill",
        fill_identity=fill["buy_fill_identity"],
        fill_source=fill["source"],
        fill_count=len(legs),
    )
    observations = sorted(
        (q for q in quotes if q.get("symbol") == trade["code"]),
        key=lambda q: q["known_at"],
    )
    weighted = sum(leg["price"] * leg["qty"] for leg in legs) / sum(
        leg["qty"] for leg in legs
    )
    for name, at, price in (
        ("first_fill", _epoch(ordered[0]["at"]), ordered[0]["price"]),
        ("last_recorded_fill", _epoch(ordered[-1]["at"]), weighted),
    ):
        paths = []
        for horizon in EXECUTION_HORIZONS:
            target = at + horizon
            tolerance = 0.25 if horizon in (1, 3, 5) else 3.0
            found = next(
                (
                    q
                    for q in observations
                    if target <= q["known_at"] <= target + tolerance
                ),
                None,
            )
            paths.append(
                dict(
                    horizon_sec=horizon,
                    status="observed" if found else "no_exact_horizon_quote",
                    observed_at=found["known_at"] if found else None,
                    ask=found["ask"] if found else None,
                    bid=found["bid"] if found else None,
                    ask_change_bp=(
                        (found["ask"] - price) / price * 10000 if found else None
                    ),
                    bid_change_bp=(
                        (found["bid"] - price) / price * 10000 if found else None
                    ),
                    source_sha256=found["source_sha256"] if found else None,
                )
            )
        window = [q for q in observations if at <= q["known_at"] <= at + 600]
        result["anchors"].append(
            dict(
                anchor_kind=name,
                at=at,
                fill_price=price,
                fill_clock_resolution_sec=1,
                short_horizon_clock_quality="broker_second_resolution",
                horizons=paths,
                observed_quote_n=len(window),
                observed_min_ask_change_bp=(
                    min((q["ask"] - price) / price * 10000 for q in window)
                    if window
                    else None
                ),
                minimum_role="sampled_path_diagnostic_not_future_optimal_entry",
                continuous_coverage_proven=False,
            )
        )
    return result


def generate_execution_review(data_root, through_date, output_dir, *, trades=None):
    """Census every real position, preserving gaps and exact opportunity linkage."""
    data_root, output = _output_path(data_root, output_dir)
    date.fromisoformat(through_date)
    trades = _trade_census(through_date) if trades is None else trades
    if len(trades) > MAX_ANCHORS or len({str(t["id"]) for t in trades}) != len(trades):
        raise ValueError("delay_review_trade_census_invalid")
    for trade in trades:
        if (
            not "2026-06-05" <= str(trade["buy_time"])[:10] <= through_date
            or _epoch(trade["buy_time"]) is None
            or (initial.number(trade.get("buy_qty")) or 0) <= 0
        ):
            raise ValueError("delay_review_trade_census_scope_invalid")
    days = sorted(
        {str(t["buy_time"])[:10] for t in trades}
        | {
            p.name
            for p in (data_root / "report/main_trailing_source_index").glob(
                "????-??-??"
            )
            if "2026-09-29" <= p.name <= through_date
        }
    )
    events, source_receipt = _execution_sources(data_root, days)
    opportunities, quotes, orders, census = _timing_opportunities(events)
    fills, fill_receipt = _snapshot_fills(data_root, days)
    output.mkdir(parents=True, exist_ok=True)
    from src.engine.lifecycle.research_disk_budget import use

    with use(output, durable_limit=MAX_DURABLE_BYTES, temp_limit=MAX_TEMP_BYTES):
        trade_rows = [
            _fill_path(t, fills.get(str(t["id"])), quotes.get(str(t["id"]), []), orders)
            for t in trades
        ]
        trade_ref = storage.write_tree(output, trade_rows)
        opportunities_ref = storage.write_tree(output, opportunities)
        census_ref = storage.write_tree(output, trades)
    result = dict(
        schema="pre_submit_delay_execution_review_v1",
        through_date=through_date,
        status="complete_with_explicit_coverage",
        runtime_effect=False,
        allowed_runtime_apply=False,
        decision_authority="report_only",
        metric_role="initial_entry_price_timing_diagnostic",
        primary_decision_metric="same_opportunity_quote_and_exact_fill_anchored_price_change",
        window_policy="clean_baseline_census_forward_refresh_only_for_tuning",
        sample_floor="diagnostic_no_promotion",
        source_quality_gate="native_index_and_exact_fill_identity",
        forbidden_uses=[
            "policy_publication",
            "modeled_fill_as_actual",
            "future_minimum_entry",
            "gross_as_net",
        ],
        clean_census_start="2026-06-05",
        policy_refresh_start="2026-09-29",
        census=dict(
            position_records=len(trades),
            opportunity_anchors=len(opportunities),
            price_ready_anchors=sum(
                r["anchor_kind"] == "price_ready" for r in opportunities
            ),
            exact_fill_clock_records=sum(bool(r["anchors"]) for r in trade_rows),
            anchor_status_counts=dict(Counter(r["anchor_status"] for r in trade_rows)),
        ),
        qualification_census=census,
        trade_census_sha256=initial.digest(trades),
        trade_census_ref=census_ref,
        trades_ref=trade_ref,
        opportunities_ref=opportunities_ref,
        pipeline_source=source_receipt,
        fill_source=fill_receipt,
        paired_net_ev_delta_pct=None,
        realized_pnl_krw=None,
        policy_reselected=False,
        default_zero_optimality_proven=False,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    result["artifact_sha256"] = initial.digest(result)
    destination = output / "execution_report.json"
    if destination.exists() and initial._read(destination) != result:
        raise ValueError("delay_review_immutable_execution_report_conflict")
    initial._atomic(destination, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--execution-through-date",
        help="Optional read-only real-position census and indexed path review",
    )
    args = parser.parse_args(argv)
    result = generate(args.data_root, args.source_date, args.output_dir)
    if args.execution_through_date:
        execution = generate_execution_review(
            args.data_root, args.execution_through_date, args.output_dir
        )
        print(
            json.dumps(
                dict(
                    execution_report=str(args.output_dir / "execution_report.json"),
                    census=execution["census"],
                ),
                sort_keys=True,
            )
        )
    print(
        json.dumps(
            dict(
                status=result["status"],
                source_date=result["source_date"],
                report=str(args.output_dir / "report.json"),
                census=result["census"],
                selection_reason_counts=result["selection_reason_counts"],
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
