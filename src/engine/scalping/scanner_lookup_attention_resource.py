"""Source-only marginal scanner allocation evidence, shared with rank ordering.

Snapshot returns are opportunity proxies, never broker fills.  The caller must
also pass the independent, real COMPLETED/full-fill economic promotion gates.
Selection math is pure. Final evaluation reads existing compact sources only;
no function has trading authority.
"""

from collections import Counter, defaultdict
from datetime import date, datetime
import math
from zoneinfo import ZoneInfo

from src.engine.scalping.scanner_lookup_attention_policy import (
    MIN_SCORE,
    RESOURCE_PAIR_CONTRACT_VERSION,
    bonus_points_for_score,
    canonical_sha256,
)

HORIZON_SEC = 180
MAX_HORIZON_SEC = 360
MIN_RESOLVED_PAIRS = 3
MIN_RESOLVED_DATES = 2
MAX_ANCHOR_PAIRS_PER_DATE = 32
PARTITION_FIELDS = (
    "rank_partition",
    "priority_tier",
    "watch_budget_owner",
    "market_gainer_partition",
    "reserved_partition",
)


def same_tier_key(score, source_priority, flu_rate, scan_rank=0):
    """Use the live stable score/source/change-rate tie-break in replay too."""
    return (-float(score), int(source_priority), -float(flu_rate), int(scan_rank))


def partition_key(row):
    return tuple(row.get(key) for key in PARTITION_FIELDS)


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer(value):
    number = _finite(value)
    return int(number) if number is not None and number.is_integer() else None


def _boolean(value):
    return {"true": True, "false": False}.get(str(value).strip().lower())


def event_row(event):
    """Retain malformed rows as scoped tombstones; never silently shrink a set."""
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    if fields.get("scanner_prune_reason") == "manual_control_excluded":
        return None
    version = fields.get("lookup_attention_resource_pair_contract_version")
    if not version or version == "scanner_lookup_attention_resource_pair_v1":
        return None
    row = {
        "observation_date": str(event.get("emitted_date") or ""),
        "scan_generation_id": str(fields.get("scanner_scan_generation_id") or ""),
        "stock_code": str(event.get("stock_code") or ""),
        "scan_rank": _integer(fields.get("scanner_scan_rank")),
        "ranked_candidate_count": _integer(
            fields.get("scanner_ranked_candidate_count")
        ),
        "rank_partition": _integer(fields.get("scanner_rank_priority_rank_partition")),
        "priority_tier": str(fields.get("scanner_rank_priority_tier") or ""),
        "watch_budget_owner": str(fields.get("scanner_watch_budget_owner") or ""),
        "market_gainer_partition": _boolean(
            fields.get("scanner_rank_priority_market_gainer_partition")
        ),
        "reserved_partition": str(
            fields.get("scanner_rank_priority_reserved_partition") or ""
        ),
        "source_priority": _integer(fields.get("scanner_rank_priority_source_rank")),
        "flu_rate": _finite(fields.get("scanner_rank_priority_flu_rate")),
        "base_priority_score": _finite(
            fields.get("scanner_rank_priority_score_without_lookup_attention")
        ),
        "candidate_priority_score": _finite(
            fields.get("scanner_rank_priority_score_with_lookup_attention")
        ),
        "actual_priority_score": _finite(
            fields.get("lookup_attention_resource_actual_score")
        ),
        "lookup_attention_snapshot_score": _finite(
            fields.get("lookup_attention_resource_snapshot_score")
        ),
        "counterfactual_bonus_points": _finite(
            fields.get("lookup_attention_resource_counterfactual_bonus_points")
        ),
        "partition_count": _integer(
            fields.get("lookup_attention_resource_partition_count")
        ),
        "partition_codes_sha256": str(
            fields.get("lookup_attention_resource_partition_codes_sha256") or ""
        ),
        "eligibility_pass": _boolean(
            fields.get("lookup_attention_resource_eligibility_pass")
        ),
        "eligibility_reason": str(
            fields.get("lookup_attention_resource_eligibility_reason") or ""
        ),
        "simple_capacity": _boolean(
            fields.get("lookup_attention_resource_simple_capacity")
        ),
        "observed_epoch": _finite(
            fields.get("lookup_attention_resource_observed_epoch")
        ),
        "price": _finite(fields.get("lookup_attention_resource_price")),
        "price_observed_epoch": _finite(
            fields.get("lookup_attention_resource_price_observed_epoch")
        ),
        "terminal": (
            "promoted"
            if event.get("stage") == "scalping_scanner_candidate_promoted"
            else "pruned"
        ),
        "prune_reason": str(fields.get("scanner_prune_reason") or ""),
        "eligible_source": _boolean(
            fields.get("lookup_attention_resource_pair_eligible")
        ),
        "effective_venue": str(fields.get("effective_venue") or ""),
        "market_session_bucket": str(fields.get("market_session_bucket") or ""),
        "contract_version": version,
    }
    return row


def valid_row(row):
    try:
        score = row["lookup_attention_snapshot_score"]
        bonus = bonus_points_for_score(score)
        return bool(
            row["eligible_source"] is True
            and row["effective_venue"] == "KRX"
            and row["market_session_bucket"] == "krx_regular"
            and row["contract_version"] == RESOURCE_PAIR_CONTRACT_VERSION
            and row["scan_generation_id"].startswith("SCANGEN-")
            and len(row["stock_code"]) == 6
            and row["stock_code"].isdigit()
            and 1 <= row["scan_rank"] <= row["ranked_candidate_count"]
            and row["rank_partition"] in (0, 1)
            and row["priority_tier"].startswith("tier_")
            and row["watch_budget_owner"]
            and row["reserved_partition"]
            and isinstance(row["market_gainer_partition"], bool)
            and row["source_priority"] >= 0
            and _finite(row["flu_rate"]) is not None
            and 0 <= score <= 1
            and abs(row["counterfactual_bonus_points"] - bonus) <= 1e-6
            and abs(
                row["candidate_priority_score"] - row["base_priority_score"] - bonus
            )
            <= 1e-6
            and (
                abs(row["actual_priority_score"] - row["base_priority_score"]) <= 1e-6
                or abs(row["actual_priority_score"] - row["candidate_priority_score"])
                <= 1e-6
            )
            and row["partition_count"] > 0
            and isinstance(row["eligibility_pass"], bool)
            and isinstance(row["simple_capacity"], bool)
            and row["observed_epoch"] > 0
            and datetime.fromtimestamp(row["observed_epoch"], ZoneInfo("Asia/Seoul"))
            .date()
            .isoformat()
            == row["observation_date"]
            and row["terminal"] in {"promoted", "pruned"}
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def allocation_book(
    rows,
    *,
    invalid_row_count=0,
    capacity_reasons=(),
    cost_bps=(1.5, 1.5, 20.0),
    _proof_keys=None,
):
    """Rebuild complete partitions, then measure only the actual marginal swap.

    Completeness and baseline reproduction are contractual.  Legacy generation
    counts remain diagnostics; they cannot add an independent 20/5/10 hurdle.
    """
    groups = defaultdict(list)
    excluded = Counter()
    for row in rows:
        # A corrupt partition identity quarantines its whole generation.
        key = (
            row.get("observation_date"),
            row.get("scan_generation_id"),
            partition_key(row),
        )
        groups[key].append(row)
    unknown_groups = {
        key[:2]
        for key, values in groups.items()
        if any(
            any(value is None or value == "" for value in partition_key(row))
            for row in values
        )
    }
    complete = []
    observed_dates = set()
    for key, values in groups.items():
        if key[:2] in unknown_groups or not all(valid_row(row) for row in values):
            excluded["invalid_partition"] += 1
            continue
        unique = {row["stock_code"]: row for row in values}
        digest = canonical_sha256(sorted(unique))
        if len(unique) != len(values) or any(
            row["partition_count"] != len(values)
            or row["partition_codes_sha256"] != digest
            for row in values
        ):
            excluded["incomplete_or_conflicting_partition"] += 1
            continue
        observed_dates.add(key[0])
        complete.append((key, values))

    # One representative complete partition per date preserves no-effect
    # diagnostics. Economic proofs below retain every competitor, not just the
    # winning symbols. Selection is made before inspecting future returns.
    if _proof_keys is not None:
        first_dates = set()
        for key, _ in complete:
            if key[0] not in first_dates:
                _proof_keys.add(key)
                first_dates.add(key[0])

    # Pair both legs at the same future scan generation, not at independently
    # cherry-picked prices or incomparable holding periods.
    snapshots = defaultdict(dict)
    for key, values in complete:
        for row in values:
            epoch, price_epoch, price = (
                row["observed_epoch"],
                row.get("price_observed_epoch"),
                row.get("price"),
            )
            if (
                _finite(price) is not None
                and price > 0
                and _finite(price_epoch) is not None
                and 0 <= epoch - price_epoch <= 120
            ):
                snapshots[(key[0], row["stock_code"])][row["scan_generation_id"]] = row

    opportunities = []
    paired_values = {}
    paired_generations = set()
    changed_generations = set()
    moved = 0
    for key, values in complete:
        if not any(row["counterfactual_bonus_points"] > 0 for row in values):
            continue
        if not all(row["simple_capacity"] for row in values):
            excluded["stateful_replacement_or_upgrade"] += 1
            continue
        actual_codes = {
            row["stock_code"] for row in values if row["terminal"] == "promoted"
        }
        eligible = [row for row in values if row["eligibility_pass"]]
        if not actual_codes.issubset({row["stock_code"] for row in eligible}):
            excluded["promoted_eligibility_mismatch"] += 1
            continue
        if any(
            row["terminal"] == "pruned" and row["prune_reason"] not in capacity_reasons
            for row in eligible
        ):
            excluded["unreproduced_guard_terminal"] += 1
            continue
        k = len(actual_codes)

        def top(field):
            return sorted(
                eligible,
                key=lambda row: same_tier_key(
                    row[field],
                    row["source_priority"],
                    row["flu_rate"],
                    row["scan_rank"],
                ),
            )[:k]

        if {row["stock_code"] for row in top("actual_priority_score")} != actual_codes:
            excluded["actual_selection_not_reproduced"] += 1
            continue
        if not k or k == len(eligible):
            continue
        paired_generations.add(key[:2])
        for row in eligible:
            paired_values[(key[0], key[1], row["stock_code"])] = row
        baseline = {row["stock_code"]: row for row in top("base_priority_score")}
        proposed = {row["stock_code"]: row for row in top("candidate_priority_score")}
        incoming, outgoing = sorted(proposed.keys() - baseline.keys()), sorted(
            baseline.keys() - proposed.keys()
        )
        if incoming:
            changed_generations.add(key[:2])
        moved += len(incoming)
        for in_code, out_code in zip(incoming, outgoing):
            opportunities.append((key, proposed[in_code], baseline[out_code]))

    resolved = []
    occupied_until = {}
    selected_per_date = Counter()
    missing = 0
    for key, incoming, outgoing in sorted(
        opportunities,
        key=lambda item: (
            item[1]["observed_epoch"],
            item[1]["stock_code"],
            item[2]["stock_code"],
        ),
    ):
        anchor = max(incoming["observed_epoch"], outgoing["observed_epoch"])
        episode_key = (key[0], incoming["stock_code"], outgoing["stock_code"])
        if anchor < occupied_until.get(episode_key, 0):
            continue
        if selected_per_date[key[0]] >= MAX_ANCHOR_PAIRS_PER_DATE:
            continue
        selected_per_date[key[0]] += 1
        if _proof_keys is not None:
            _proof_keys.add(key)
        occupied_until[episode_key] = anchor + MAX_HORIZON_SEC
        in_snap = snapshots.get((key[0], incoming["stock_code"]), {})
        out_snap = snapshots.get((key[0], outgoing["stock_code"]), {})
        future = sorted(
            (in_snap[g]["observed_epoch"], g)
            for g in in_snap.keys() & out_snap.keys()
            if HORIZON_SEC <= in_snap[g]["observed_epoch"] - anchor <= MAX_HORIZON_SEC
            and abs(in_snap[g]["observed_epoch"] - out_snap[g]["observed_epoch"]) <= 1
        )
        anchors_valid = all(
            row["scan_generation_id"] in snapshots.get((key[0], row["stock_code"]), {})
            for row in (incoming, outgoing)
        )
        if not anchors_valid or not future:
            missing += 1
            continue
        end_epoch, generation = future[0]
        if _proof_keys is not None:
            for row in (in_snap[generation], out_snap[generation]):
                _proof_keys.add(
                    (row["observation_date"], generation, partition_key(row))
                )

        def net(start, end):
            ratio = end["price"] / start["price"]
            return (ratio - 1) * 100 - (
                cost_bps[0] + ratio * (cost_bps[1] + cost_bps[2])
            ) / 100

        in_return = net(incoming, in_snap[generation])
        out_return = net(outgoing, out_snap[generation])
        resolved.append(
            {
                "observation_date": key[0],
                "scan_generation_id": key[1],
                "incoming_code": incoming["stock_code"],
                "outgoing_code": outgoing["stock_code"],
                "label_generation_id": generation,
                "anchor_epoch": anchor,
                "label_epoch": end_epoch,
                "incoming_snapshot_net_return_pct": round(in_return, 8),
                "outgoing_snapshot_net_return_pct": round(out_return, 8),
                "incremental_snapshot_return_pct": round(in_return - out_return, 8),
            }
        )
    dates = {row["observation_date"] for row in resolved}
    ev = (
        sum(row["incremental_snapshot_return_pct"] for row in resolved) / len(resolved)
        if resolved
        else None
    )
    in_ev = (
        sum(row["incoming_snapshot_net_return_pct"] for row in resolved) / len(resolved)
        if resolved
        else None
    )
    mature = len(resolved) >= MIN_RESOLVED_PAIRS and len(dates) >= MIN_RESOLVED_DATES
    ready = bool(mature and ev > 0 and in_ev > 0)
    status = (
        "not_observed"
        if not rows
        else (
            "contract_invalid"
            if not complete
            else (
                "hold_no_effect"
                if not any(
                    row["counterfactual_bonus_points"] > 0
                    for _, values in complete
                    for row in values
                )
                else (
                    "no_capacity_competition"
                    if not paired_generations
                    else (
                        "hold_no_effect"
                        if not changed_generations
                        else (
                            "hold_sample"
                            if not mature
                            else "ready" if ready else "hold_no_edge"
                        )
                    )
                )
            )
        )
    )
    candidate_count = sum(
        row["lookup_attention_snapshot_score"] > MIN_SCORE
        for row in paired_values.values()
    )
    return {
        "contract_version": RESOURCE_PAIR_CONTRACT_VERSION,
        "metric_role": "causal_runtime_hook_gate",
        "decision_authority": "snapshot_opportunity_cf_requires_independent_real_completed_ev",
        "window_policy": "latest20_krx_dates_first32_nonoverlapping_pairs_per_date_same_future_generation_180_to_360s",
        "sampling_policy": "time_ordered_before_future_return_lookup;bounded_causal_sample_not_population_ev",
        "sample_floor": "resolved_marginal_pairs>=3_on>=2_dates;generation20_dates5_cohort10_diagnostic_only",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "complete_partition_exact_selection_reproduction_observed_snapshot_prices",
        "forbidden_uses": [
            "standalone_live_promotion",
            "real_execution_quality",
            "broker_guard_bypass",
            "synthetic_missing_returns",
            "extrapolate_bounded_sample_to_population_ev",
        ],
        "status": status,
        "ready_for_live_gate": ready,
        "invalid_row_count": invalid_row_count,
        "excluded_partition_counts": dict(sorted(excluded.items())),
        "complete_partition_count": len(complete),
        "observed_date_count": len(observed_dates),
        "paired_generation_count": len(paired_generations),
        "trading_date_count": len({key[0] for key in paired_generations}),
        "paired_candidate_observation_count": candidate_count,
        "paired_control_observation_count": len(paired_values) - candidate_count,
        "reordered_generation_count": len(changed_generations),
        "counterfactual_moved_in_count": moved,
        "counterfactual_moved_out_count": moved,
        "unpaired_or_guard_pruned_row_count": len(rows) - len(paired_values),
        "resolved_pair_count": len(resolved),
        "resolved_date_count": len(dates),
        "unobserved_pair_count": missing,
        "selected_anchor_pair_count": sum(selected_per_date.values()),
        "source_quality_adjusted_ev_pct": round(ev, 8) if ev is not None else None,
        "incoming_snapshot_ev_pct": round(in_ev, 8) if in_ev is not None else None,
        "pairs": resolved,
        "retention_review": (
            "review_merge_into_scanner_diagnostics"
            if len(observed_dates) >= 20 and not changed_generations
            else "collecting"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def compact_evidence_rows(rows, *, capacity_reasons=()):
    """Keep bounded, independently replayable partitions and their label proofs.

    Run once per source date so the producer need not keep ninety days of raw
    competitor dictionaries in memory. Invalid partitions never become proofs;
    their raw counts remain in lineage diagnostics, not a global live veto.
    """
    keys = set()
    diagnostics = allocation_book(
        rows, capacity_reasons=capacity_reasons, _proof_keys=keys
    )
    retained = (
        rows
        if len(rows) <= 1024
        else [
            row
            for row in rows
            if (
                row.get("observation_date"),
                row.get("scan_generation_id"),
                partition_key(row),
            )
            in keys
        ]
    )
    return retained, {
        "raw_row_count": len(rows),
        "raw_invalid_row_count": sum(not valid_row(row) for row in rows),
        "raw_complete_partition_count": diagnostics["complete_partition_count"],
        "raw_reordered_generation_count": diagnostics["reordered_generation_count"],
        "raw_excluded_partition_counts": diagnostics["excluded_partition_counts"],
    }


INTEGRATED_CONTRACT = "scanner_lookup_attention_integrated_selection_v1"
NATIVE_FIELDS = (
    '905',
    '907',
    'attempt_id',
    'block_reason',
    'buy_sell_type',
    'decision',
    'effective_venue',
    'fill_quality',
    'lookup_attention_actual_order_submitted',
    'lookup_attention_allowed_runtime_apply',
    'lookup_attention_broker_order_forbidden',
    'lookup_attention_resource_actual_score',
    'lookup_attention_resource_counterfactual_bonus_points',
    'lookup_attention_resource_eligibility_pass',
    'lookup_attention_resource_eligibility_reason',
    'lookup_attention_resource_observed_epoch',
    'lookup_attention_resource_pair_contract_version',
    'lookup_attention_resource_pair_eligible',
    'lookup_attention_resource_partition_codes_sha256',
    'lookup_attention_resource_partition_count',
    'lookup_attention_resource_price',
    'lookup_attention_resource_price_observed_epoch',
    'lookup_attention_resource_simple_capacity',
    'lookup_attention_resource_snapshot_score',
    'lookup_attention_runtime_effect',
    'lookup_attention_snapshot_score',
    'lookup_attention_state',
    'lookup_attention_weight_actual_order_submitted',
    'lookup_attention_weight_allowed_runtime_apply',
    'lookup_attention_weight_bonus_points',
    'lookup_attention_weight_broker_order_forbidden',
    'lookup_attention_weight_decision_authority',
    'lookup_attention_weight_effective_venue',
    'lookup_attention_weight_eligible_session_buckets',
    'lookup_attention_weight_eligible_venues',
    'lookup_attention_weight_forbidden_uses',
    'lookup_attention_weight_market_session_bucket',
    'lookup_attention_weight_max_source_age_sec',
    'lookup_attention_weight_policy_applied',
    'lookup_attention_weight_policy_artifact_sha256',
    'lookup_attention_weight_policy_reason',
    'lookup_attention_weight_policy_source_date',
    'lookup_attention_weight_policy_state',
    'lookup_attention_weight_policy_version',
    'lookup_attention_weight_preopen_artifact_sha256',
    'lookup_attention_weight_rollback_bonus_points',
    'lookup_attention_weight_runtime_effect',
    'lookup_attention_weight_same_priority_tier_only',
    'lookup_attention_weight_source_age_sec',
    'lookup_attention_weight_source_fresh',
    'main_lifecycle_attempt_id',
    'main_lifecycle_record_id',
    'main_lifecycle_scanner_promotion_id',
    'main_lifecycle_session_bucket',
    'main_lifecycle_trade_date',
    'main_lifecycle_venue',
    'market_session_bucket',
    'order_filled_qty',
    'order_remaining_qty',
    'order_requested_qty',
    'order_side',
    'realtime_lookup_source_date',
    'realtime_lookup_source_time',
    'reason',
    'receipt_quantity_contract_complete',
    'runtime_record_id',
    'scanner_promotion_id',
    'scanner_prune_reason',
    'scanner_rank_priority_flu_rate',
    'scanner_rank_priority_market_gainer_partition',
    'scanner_rank_priority_rank_partition',
    'scanner_rank_priority_reserved_partition',
    'scanner_rank_priority_score_with_lookup_attention',
    'scanner_rank_priority_score_without_lookup_attention',
    'scanner_rank_priority_source_rank',
    'scanner_rank_priority_tier',
    'scanner_ranked_candidate_count',
    'scanner_scan_generation_id',
    'scanner_scan_rank',
    'scanner_watch_budget_owner',
    'venue',
)
NATIVE_STAGES = {
    "scalping_scanner_candidate_promoted", "scalping_scanner_candidate_pruned",
    "scalping_scanner_runtime_target_attach", "position_rebased_after_fill",
    "scalping_scanner_fast_precheck", "scalping_scanner_heavy_eval_completion",
    "scalp_entry_action_decision_snapshot", "pre_submit_entry_ai_authority_guard_block",
    "entry_submit_revalidation_block", "entry_submit_revalidation_warning",
    "order_bundle_submitted",
}


def capture_native_event(state, event):
    """Retain only existing decoder inputs; no API, AI, or sizing invocation."""
    if event.get("stage") not in NATIVE_STAGES:
        return
    fields = event.get("fields")
    if not isinstance(fields, dict):
        return
    if not (fields.get("scanner_promotion_id") or fields.get("main_lifecycle_scanner_promotion_id")
            or fields.get("lookup_attention_resource_pair_contract_version")):
        return
    # Fingerprint includes all native semantics: conflicting mirrors must reach
    # the decoder as conflicts rather than overwrite a valid source record.
    native = {key: event.get(key) for key in
              ("stage", "stock_code", "record_id", "emitted_date", "emitted_at", "fields")}
    native["fields"] = {key: fields[key] for key in NATIVE_FIELDS if key in fields}
    state.setdefault("lookup_attention_native_events", {})[canonical_sha256(native)] = native


def integrated_selection_evaluation(target, events_by_date, *, predecessor=None, migration=None):
    """Bounded final evaluation from incremental native ledgers, never rolling raw.

    Existing missed-entry replay explicitly lacks exact fill/exit/capital replay.
    Sampled snapshots and realized high/low cohorts cannot repair that source
    contract. Keep the primary null until that existing execution owner supplies
    a reproducible portfolio comparison; do not add a new fill simulator here.
    """
    from src.engine.monitoring.scanner_lookup_attention_tuning import (
        collect_lineage, load_completed_facts, join_completed_outcomes,
        _latest_symbol_master, _source_quality, _cohort_book, _resource_allocation_pair_book,
        evaluate_post_apply, COST_CONTRACT, _resource_window_start, _conversion_diagnostics,
    )
    if migration is None and isinstance(predecessor, dict):
        migration = predecessor.get("historical_migration_diagnostics")
    migration = migration if isinstance(migration, dict) else {}
    observations, lineage = collect_lineage(target, events_by_date=events_by_date)
    rows = lineage.pop("_resource_pair_rows", [])
    # Exact original COMPLETED observation identities can be rejoined to fresh
    # fact revisions. Historical cohort denominators remain archive diagnostics.
    identity = lambda row: (row.get("observation_date"), row.get("recommendation_id"), row.get("scanner_promotion_id"), row.get("stock_code"))
    native_keys = {identity(row) for row in observations}
    observations += [row for row in migration.get("outcomes", []) if identity(row) not in native_keys]
    resource_keys = {(row.get("observation_date"), row.get("scan_generation_id"), row.get("stock_code")) for row in rows}
    rows += [row for row in migration.get("resource_pair_rows", []) if (row.get("observation_date"), row.get("scan_generation_id"), row.get("stock_code")) not in resource_keys]
    observations = [row for row in observations if lineage["window_start"] <= str(row.get("observation_date") or "") <= target.isoformat()]
    resource_start = _resource_window_start(target).isoformat()
    rows = [row for row in rows if resource_start <= str(row.get("observation_date") or "") <= target.isoformat()]
    facts = load_completed_facts(date.fromisoformat(lineage["window_start"]), target)
    symbols, master = _latest_symbol_master(target)
    outcomes, exclusions = join_completed_outcomes(observations, facts, eligible_symbols=symbols)
    source_quality = _source_quality(target, {date.fromisoformat(row["rec_date"]) for row in outcomes}
                                    | {date.fromisoformat(row["observation_date"]) for row in rows if row.get("observation_date")})
    # No production read of the retired report/campaign. Current integrated
    # publisher is zero-only; archive campaign helpers retain archive authority.
    prior_policy = {}
    # Completion revisions and model/source version are in the final input hash.
    fingerprint = canonical_sha256({"contract": INTEGRATED_CONTRACT, "evaluator_revision": 2,
        "events": events_by_date, "facts": facts, "master": master,
        "source_quality": source_quality, "migration": migration, "cost_contract": COST_CONTRACT,
        "prior_policy": prior_policy})
    if (isinstance(predecessor, dict) and predecessor.get("input_sha256") == fingerprint
            and predecessor.get("artifact_sha256") == canonical_sha256({k:v for k,v in predecessor.items() if k != "artifact_sha256"})):
        return predecessor
    proxy = _resource_allocation_pair_book(rows, invalid_row_count=lineage["invalid_resource_pair_count"])
    conversion = _conversion_diagnostics(observations)
    conversion["intended_consumer"] = "intraday_ws_freshness_monitor.lookup_attention_selection"
    conversion["scope"] = "known_exact_observations;historical_full_census_in_migration_receipt"
    actual_book = _cohort_book(outcomes)
    for cohort in ("all", "candidate", "control"):
        if not actual_book[cohort]["completed_outcome_count"]:
            actual_book[cohort]["net_pnl_krw"] = None
    applied = evaluate_post_apply(prior_policy, outcomes)
    applied["actual_ev_pct"] = None
    applied["actual_net_pnl_krw"] = None
    if applied["status"] == "not_applicable_before_live_apply":
        applied.pop("book", None)
    gaps = ["original_unselected_entry_recipe_quantity_guard_missing",
            "exact_fill_exit_cost_counterfactual_replay_missing",
            "same_budget_portfolio_capital_path_missing"]
    # Historical report inputs must stay compact. Daily native resource census
    # reaches 58k rows; serialize only the already selected complete proof keys.
    # Exact entry/fill/conversion receipts and raw census diagnostics survive.
    proof_keys = {(row["observation_date"], row["scan_generation_id"], row["stock_code"]) for row in rows}
    native_events = [event for event in events_by_date.get(target.isoformat(), [])
        if event.get("stage") not in {"scalping_scanner_candidate_promoted", "scalping_scanner_candidate_pruned"}
        or (event.get("emitted_date"), (event.get("fields") or {}).get("scanner_scan_generation_id"), event.get("stock_code")) in proof_keys]
    result = {"contract_version": INTEGRATED_CONTRACT, "target_date": target.isoformat(),
        "input_sha256": fingerprint, "status": "source_gap", "metric_role": "primary_ev",
        "evaluation_phase": "postclose_final", "generated_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        "decision_authority": "source_only_selection_economics",
        "runtime_effect": False, "allowed_runtime_apply": False,
        "actual_order_submitted": False, "broker_order_forbidden": True,
        "window_policy": "rolling90_calendar_native_incremental_ledgers_clean_post_rollout",
        "source_quality_gate": "native_exact_lineage_master_cost_and_same_budget_execution_replay",
        "sample_floor": {"real_total": 20, "real_dates": 5, "real_cohort": 10, "real_cohort_dates": 3,
                         "paired": 3, "paired_dates": 2},
        "forbidden_uses": ["snapshot_as_execution_ev", "cohort_mean_as_causal_uplift", "source_gap_as_zero_or_no_edge"],
        "native_events": native_events,
        "native_resource_export_scope": "bounded_complete_partition_label_proofs;raw_census_in_lineage_and_original_pipeline",
        "historical_migration_diagnostics": migration,
        "lineage": lineage, "source_quality": source_quality, "official_symbol_master": master,
        "exclusions": exclusions, "resource_pair_rows": rows,
        "snapshot_proxy": {**proxy, "metric_role": "supporting_proxy",
                           "ready_for_live_gate": False, "diagnostic_snapshot_gate_pass": proxy["ready_for_live_gate"]},
        "actual_completed": {"metric_role": "observational_completed_net", "book": actual_book,
                             "outcomes": outcomes, "causal_uplift": None,
                             "cost_basis": "fixed_fee_tax_comparison_actual_fill_prices_not_broker_reconciled"},
        "actual_applied_version": applied,
        "conversion_diagnostics": conversion,
        "selection_disposition": ("source_gap" if not proxy["complete_partition_count"] else
            "no_capacity_competition" if not proxy["paired_generation_count"] else
            "hold_no_effect" if not proxy["reordered_generation_count"] else "changed_selection"),
        "primary_economics": {"status": "source_gap", "paired_delta_ev_pct": None,
            "baseline_budget_ev_pct": None, "candidate_budget_ev_pct": None,
            "baseline_net_pnl_krw": None, "candidate_net_pnl_krw": None,
            "tail": None, "exposure": None, "model_error": None, "source_gaps": gaps},
        "independent_holdout": {"status": "not_armed", "historical_dates_not_fresh_holdout": True},
        "source_gap_owner": "sniper_missed_entry_counterfactual.exact_fill_exit_cost_counterfactual_replay",
        "closure_test": "native original requested quantity/recipe/guards plus ordered fill/exit/cost and full frozen capital path reproduce both selections before independent forward holdout",
        "eta": None,
    }
    result["artifact_sha256"] = canonical_sha256(result)
    return result


def validate_integrated_selection(section, policy, *, target):
    """Shared publisher/PREOPEN/verifier predicate for the supported contract.

    The current source owner cannot reproduce executable portfolio CF. The only
    publishable state is an explicit zero-bonus disposition. Unsupported ready
    claims fail closed, including self-hashed fabricated paired economics.
    """
    issues = []
    if not isinstance(section, dict) or not isinstance(policy, dict):
        return ["integrated_source_or_policy_missing"]
    for payload in (section, policy):
        if (payload is section and payload.get("target_date") != target.isoformat()) or (payload is policy and payload.get("source_evaluation_date") != target.isoformat()):
            issues.append("integrated_exact_date_mismatch")
        try:
            expected_hash = canonical_sha256({k:v for k,v in payload.items() if k != "artifact_sha256"})
        except (TypeError, ValueError):
            expected_hash = None
        if not expected_hash or payload.get("artifact_sha256") != expected_hash:
            issues.append("integrated_artifact_hash_mismatch")
        if (payload.get("runtime_effect") is not False or payload.get("allowed_runtime_apply") is not False
                or payload.get("actual_order_submitted") is not False or payload.get("broker_order_forbidden") is not True):
            issues.append("unsupported_execution_authority")
    primary = section.get("primary_economics")
    if not isinstance(primary, dict):
        return sorted(set(issues + ["primary_economics_missing"]))
    if (section.get("contract_version") != INTEGRATED_CONTRACT
            or section.get("evaluation_phase") != "postclose_final"
            or policy.get("integrated_source_contract") != INTEGRATED_CONTRACT
            or policy.get("source_report_artifact_sha256") != section.get("artifact_sha256")
            or policy.get("status") != "source_quality_blocked"
            or section.get("status") != "source_gap"
            or primary.get("paired_delta_ev_pct") is not None
            or not primary.get("source_gaps")
            or policy.get("effective_bonus_points") != 0.0):
        issues.append("integrated_disposition_invalid")
    return sorted(set(issues))


def selection_handoff(report_dir, target_date):
    """Compact, hash-bound diagnostic consumption shared by Daily/EV/summary."""
    import json
    from pathlib import Path
    root = Path(report_dir)
    path = root / "intraday_ws_freshness_monitor" / f"intraday_ws_freshness_monitor_{target_date}.json"
    result = {"source_path": str(path), "source_evaluation_date": target_date,
              "status": "source_missing", "allowed_runtime_apply": False}
    try:
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("integrated_source_exceeds_bounded_read")
        report = json.loads(path.read_text())
        section = report["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"]
        policy_path = root.parent / "threshold_cycle" / "scanner_lookup_attention_policy" / f"scanner_lookup_attention_policy_{target_date}.json"
        policy = json.loads(policy_path.read_text())
        issues = validate_integrated_selection(section, policy, target=date.fromisoformat(target_date))
        if issues or report.get("target_date") != target_date or section.get("evaluation_phase") != "postclose_final":
            raise ValueError("integrated_final_handoff_invalid")
        result.update({"status": section["status"], "source_section_sha256": section["artifact_sha256"],
            "primary_economics": section["primary_economics"], "snapshot_proxy": section["snapshot_proxy"],
            "actual_completed": {key:value for key,value in section["actual_completed"].items() if key != "outcomes"}})
    except (OSError, KeyError, TypeError, ValueError) as exc:
        result["source_gap"] = str(exc)
    return result
