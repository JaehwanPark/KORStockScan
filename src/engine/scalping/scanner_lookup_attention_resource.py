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
        "scanner_promotion_id": str(fields.get("scanner_promotion_id") or ""),
        "scanner_selection_pair_id": str(
            fields.get("scanner_selection_pair_id") or ""
        ),
        "scanner_selection_pair_role": str(
            fields.get("scanner_selection_pair_role") or ""
        ),
        "scanner_selection_pair_assignment": str(
            fields.get("scanner_selection_pair_assignment") or ""
        ),
        "scanner_selection_pair_contract_version": str(
            fields.get("scanner_selection_pair_contract_version") or ""
        ),
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
        pair_id = row.get("scanner_selection_pair_id") or ""
        pair_valid = bool(
            not pair_id
            or (
                len(pair_id) == 64
                and all(character in "0123456789abcdef" for character in pair_id)
                and row.get("scanner_selection_pair_contract_version")
                == "scanner_lookup_attention_selection_pair_v1"
                and row.get("scanner_selection_pair_role")
                in {"incoming", "outgoing"}
                and row.get("scanner_selection_pair_assignment")
                in {"observe_only", "baseline", "candidate"}
            )
        )
        return bool(
            pair_valid
            and row["eligible_source"] is True
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
        producer_pair_ids = {
            row.get("scanner_selection_pair_id")
            for row in (incoming, outgoing)
            if row.get("scanner_selection_pair_id")
        }
        if producer_pair_ids:
            natural_pair_valid = bool(
                len(producer_pair_ids) == 1
                and all(row.get("scanner_selection_pair_id") for row in (incoming, outgoing))
                and incoming.get("scanner_selection_pair_role") == "incoming"
                and outgoing.get("scanner_selection_pair_role") == "outgoing"
                and incoming.get("scanner_selection_pair_assignment")
                == outgoing.get("scanner_selection_pair_assignment")
            )
            if not natural_pair_valid:
                excluded["selection_pair_identity_conflict"] += 1
                continue
        pair_id = next(iter(producer_pair_ids), "") or canonical_sha256(
            {
                "contract": "scanner_lookup_attention_selection_pair_v1",
                "observation_date": key[0],
                "scan_generation_id": key[1],
                "partition": list(key[2]),
                "incoming_code": incoming["stock_code"],
                "outgoing_code": outgoing["stock_code"],
            }
        )
        resolved.append(
            {
                "scanner_selection_pair_id": pair_id,
                "scanner_selection_pair_identity_source": (
                    "natural_scanner_event"
                    if producer_pair_ids
                    else "historical_deterministic_derivation"
                ),
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
    daily = {
        day: round(
            sum(
                row["incremental_snapshot_return_pct"]
                for row in resolved
                if row["observation_date"] == day
            )
            / sum(row["observation_date"] == day for row in resolved),
            8,
        )
        for day in sorted(dates)
    }
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
        "selection_opportunity_ev_pct": round(ev, 8) if ev is not None else None,
        "incoming_snapshot_ev_pct": round(in_ev, 8) if in_ev is not None else None,
        "daily_incremental_opportunity_pct": daily,
        "daily_net_profit_krw": None,
        "daily_net_profit_reason": "entry_quantity_and_actual_fill_not_observed_for_unselected_arm",
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


LEGACY_INTEGRATED_CONTRACT = "scanner_lookup_attention_integrated_selection_v1"
INTEGRATED_CONTRACT = "scanner_lookup_attention_integrated_selection_v2"
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
    'lookup_attention_weight_experiment_allocation_seed_sha256',
    'lookup_attention_weight_experiment_arm',
    'lookup_attention_weight_experiment_max_marginal_slots',
    'lookup_attention_weight_experiment_mode',
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
    'scanner_selection_pair_assignment',
    'scanner_selection_pair_contract_version',
    'scanner_selection_pair_id',
    'scanner_selection_pair_role',
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


def execution_inputs(target, rows, receipts=None):
    """Read existing sealed compact/operating owners, never historical raw."""
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    from src.engine.scalping import scanner_lookup_attention_policy as policy
    root = (policy.PROJECT_ROOT / "data").resolve(strict=True)
    inputs = {}
    for day in sorted({r.get("observation_date") for r in rows if r.get("observation_date")}):
        pricing = compact.runtime_inference_cost_receipt(root, day)
        receipt = {"source_date": day, "pricing": pricing, "projection_status": "not_read"}
        if receipts is not None:
            receipts.append(receipt)
        if pricing.get("status") != "reviewed_operator_zero_cost":
            continue
        projection = compact.read(compact.report_path(root, day).with_suffix(".source.json"))
        receipt["projection_status"] = "sealed" if compact.valid(projection) else "missing_or_invalid"
        receipt["projection_sha256"] = projection.get("artifact_content_sha256")
        if not compact.valid(projection):
            continue
        labels = compact.read(root / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{day}.json")
        receipt["label_binding_valid"] = projection.get("source_label_report_sha256") == compact.digest(labels)
        if not receipt["label_binding_valid"]:
            continue
        model = projection.get("owner_execution_model_validation") or {}
        receipt["model_status"] = model.get("status") if isinstance(model, dict) else "invalid"
        receipt["source_row_count"] = len(projection.get("rows") or [])
        if not isinstance(model, dict) or not isinstance(projection.get("rows"), list):
            continue
        for row in projection.get("rows") or []:
            if not isinstance(row, dict):
                continue
            evidence = row.get("natural_contract_evidence") or {}
            if not isinstance(evidence, dict):
                continue
            if (row.get("exclusion_reason") or row.get("source_label_identity_reasons")
                    or evidence.get("model") != "gpt-5.4-nano"
                    or evidence.get("provider_actual") != "openai"
                    or evidence.get("semantic_validation_status") != "pass"
                    or evidence.get("decision_quality_contract_status") != "pass"
                    or row.get("incumbent_verdict") not in {"PASS", "VETO"}):
                continue
            key = (day, row.get("scanner_promotion_id"), row.get("stock_code"))
            value = {"row": row, "model": model,
                     "source_projection_sha256": projection["artifact_content_sha256"], "pricing": pricing}
            if key in inputs and inputs[key] != value:
                inputs[key] = None
            elif key not in inputs:
                inputs[key] = value
    return inputs


def selection_execution_book(rows, inputs):
    """Use complete native selections and the existing one-position CF owner."""
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get("observation_date"), row.get("scan_generation_id"), partition_key(row))].append(row)
    pairs, exclusions = [], Counter()
    identical, competing, valid = True, False, bool(groups)
    for values in groups.values():
        census = allocation_book(values, capacity_reasons={"max_new_codes_reached", "general_slot_limit", "max_records_reached"})
        valid = valid and census["complete_partition_count"] == 1 and not census["excluded_partition_counts"]
        valid = valid and all(r.get("simple_capacity") is True for r in values)
        if not valid:
            break
        eligible = [r for r in values if r["eligibility_pass"]]
        k = sum(r["terminal"] == "promoted" for r in values)
        selections = [{r["stock_code"] for r in sorted(eligible, key=lambda r: same_tier_key(
            r[field], r["source_priority"], r["flu_rate"], r["scan_rank"]))[:k]}
            for field in ("base_priority_score", "candidate_priority_score")]
        competing = competing or 0 < k < len(eligible)
        identical = identical and selections[0] == selections[1]
    if valid and identical:
        # Logical selection identity proves delta zero; absent execution inputs
        # still cannot prove either arm's absolute EV or realized profitability.
        return {"status": "no_effect" if competing else "no_capacity_competition", "paired_delta_ev_pct": 0.,
            "baseline_budget_ev_pct": None, "candidate_budget_ev_pct": None,
            "baseline_net_pnl_krw": None, "candidate_net_pnl_krw": None,
            "tail": None, "exposure": None, "model_error": None, "source_gaps": [],
            "pairs": [], "excluded_partition_counts": {}, "execution_comparison_complete": False}
    for key, values in sorted(groups.items(), key=lambda item: str(item[0])):
        census = allocation_book(values, capacity_reasons={"max_new_codes_reached", "general_slot_limit", "max_records_reached"})
        if census["complete_partition_count"] != 1 or census["excluded_partition_counts"]:
            exclusions["complete_partition_or_actual_selection_missing"] += 1
            continue
        if any(r.get("simple_capacity") is not True for r in values):
            exclusions["stateful_selection_unsupported"] += 1
            continue
        eligible = [r for r in values if r["eligibility_pass"]]
        k = sum(r["terminal"] == "promoted" for r in values)
        top = lambda field: {r["stock_code"] for r in sorted(eligible, key=lambda r: same_tier_key(
            r[field], r["source_priority"], r["flu_rate"], r["scan_rank"]))[:k]}
        baseline, candidate = top("base_priority_score"), top("candidate_priority_score")
        if not baseline:
            continue
        generation = []
        frame_budget = None
        for r in eligible:
            if r["stock_code"] not in baseline | candidate:
                continue
            value = inputs.get((key[0], r.get("scanner_promotion_id"), r["stock_code"]))
            if not value:
                exclusions["original_unselected_entry_recipe_quantity_guard_missing"] += 1
                break
            row, model = value["row"], value["model"]
            pricing = value.get("pricing") or {}
            evidence = row.get("natural_contract_evidence") or {}
            if (row.get("exclusion_reason") or row.get("source_label_identity_reasons")
                    or evidence.get("model") != "gpt-5.4-nano" or evidence.get("provider_actual") != "openai"
                    or evidence.get("semantic_validation_status") != "pass"
                    or evidence.get("decision_quality_contract_status") != "pass"
                    or row.get("incumbent_verdict") not in {"PASS", "VETO"}
                    or pricing.get("status") != "reviewed_operator_zero_cost" or pricing.get("delta_krw") != 0.
                    or not pricing.get("pricing_file_sha256")
                    or not pricing.get("effective_from", "") <= key[0] <= pricing.get("effective_to", "")):
                exclusions["natural_ai_contract_or_reviewed_pricing_missing"] += 1
                break
            try:
                arm = compact.owner_operating_arm(row.get("owner_replay") or {}, row)
                valid_model = bool(arm and compact.owner_model_scope_valid(model, row))
            except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
                arm, valid_model = {}, False
            if not arm or not valid_model:
                exclusions["independent_prior_execution_model_or_terminal_missing"] += 1
                break
            seed = row["owner_replay"]["seed"]
            if frame_budget is not None and arm["budget_krw"] != frame_budget:
                exclusions["same_frozen_budget_missing"] += 1
                break
            frame_budget = arm["budget_krw"]
            clock = datetime.fromisoformat(seed["observed_at"]).timestamp()
            if (row.get("source_date") != key[0] or row.get("scanner_promotion_id") != r.get("scanner_promotion_id")
                    or row.get("stock_code") != r["stock_code"] or row.get("effective_venue") != "KRX"
                    or row.get("session_bucket") != "KRX_REGULAR" or row.get("broker_route") != "KRX"
                    or not 0 <= clock - r["observed_epoch"] <= 120):
                exclusions["exact_generation_attempt_scope_or_clock_mismatch"] += 1
                break
            selected = row["incumbent_verdict"] == "PASS"
            old, new = selected and r["stock_code"] in baseline, selected and r["stock_code"] in candidate
            generation.append({**row, "incumbent_verdict": "PASS" if old else "VETO",
                "candidate_verdict": "PASS" if new else "VETO", "filter_role": "scanner_selection_not_ai",
                "delta_net_pct": arm["net_return_pct"] * (int(new) - int(old)),
                "stress_delta_net_pct": arm["stress_net_return_pct"] * (int(new) - int(old)),
                "runtime_inference_cost_delta_krw": 0., "model": model,
                "scan_generation_id": key[1], "source_projection_sha256": value["source_projection_sha256"]})
        else:
            pairs.extend(generation)
    empty = {"status": "source_gap", "paired_delta_ev_pct": None, "baseline_budget_ev_pct": None,
        "candidate_budget_ev_pct": None, "baseline_net_pnl_krw": None, "candidate_net_pnl_krw": None,
        "tail": None, "exposure": None, "model_error": None, "source_gaps": sorted(exclusions) or (["complete_changed_selection_execution_inputs_missing"] if not pairs else []),
        "pairs": pairs, "excluded_partition_counts": dict(exclusions)}
    if not pairs:
        return empty
    # Existing owner rejects overlap independently for each selection arm.
    models = {p["source_date"]: p["model"] for p in pairs}
    merged = {"validated_scopes": [s for m in models.values() for s in m.get("validated_scopes", [])]}
    metric = compact.operating_comparison_metrics(pairs, merged)
    if metric["status"] != "supported_operating_comparison":
        return {**empty, "source_gaps": sorted(set(empty["source_gaps"] + [metric["blocker"]]))}
    budgets = {(p["source_date"], p["scan_generation_id"]): compact.owner_operating_arm(p["owner_replay"], p)["budget_krw"] for p in pairs}
    budget = sum(budgets.values())
    daily = metric["portfolio_daily_net_delta_krw"]
    old = sum(compact.owner_operating_arm(p["owner_replay"], p)["net_pnl_krw"] for p in pairs if p["incumbent_verdict"] == "PASS")
    new = old + sum(daily.values())
    # No unsupported partition is silently dropped from promotion coverage.
    return {**empty, "status": "supported_operating_comparison", "baseline_net_pnl_krw": old,
        "candidate_net_pnl_krw": new, "baseline_budget_ev_pct": old / budget * 100,
        "candidate_budget_ev_pct": new / budget * 100, "paired_delta_ev_pct": (new - old) / budget * 100,
        "daily_net_delta_krw": daily,
        "baseline_daily_net_krw": {day: sum(compact.owner_operating_arm(p["owner_replay"], p)["net_pnl_krw"]
            for p in pairs if p["source_date"] == day and p["incumbent_verdict"] == "PASS") for day in daily},
        "candidate_daily_net_krw": {day: sum(compact.owner_operating_arm(p["owner_replay"], p)["net_pnl_krw"]
            for p in pairs if p["source_date"] == day and p["candidate_verdict"] == "PASS") for day in daily},
        "tail": {k: metric[k] for k in ("incumbent", "candidate")},
        "exposure": {"budget_krw": budget, "portfolio_allocation_contract": metric["portfolio_allocation_contract"]},
        "model_error": sum(compact.owner_operating_arm(p["owner_replay"],p)["budget_krw"] * error
            for p,error in zip(pairs,metric["pair_error_penalties_pct"])) / budget,
        "robust_delta_ev_lower_bound_pct": sum(compact.owner_operating_arm(p["owner_replay"],p)["budget_krw"] * lower
            for p,lower in zip(pairs,metric["pair_lower_bounds_pct"])) / budget,
        "lower_bound_method": "same_frozen_budget_weighted_sum_changed_arm_stress_and_independent_model_error",
        "complete_coverage": not exclusions, "counterfactual_not_realized_pnl": True}


def selection_edge_passes(book):
    from src.engine.scalping import scanner_lookup_attention_policy as policy
    try:
        old, new = book["tail"]["incumbent"], book["tail"]["candidate"]
        return bool(book["status"] == "supported_operating_comparison" and book["complete_coverage"]
            and book["candidate_budget_ev_pct"] > 0 and book["paired_delta_ev_pct"] >= policy.MIN_EV_UPLIFT_PCT
            and book["robust_delta_ev_lower_bound_pct"] > 0 and sum(book["daily_net_delta_krw"].values()) > 0
            and new["p10"] >= old["p10"] - policy.MAX_TAIL_DEGRADATION_PCT
            and new["worst"] >= policy.MIN_WORST_NET_RETURN_PCT)
    except (KeyError, TypeError, ValueError):
        return False


def selection_validation(book, rows, inputs, outcomes, predecessor, target, *, frozen_at=None):
    """Freeze the supported learning population, then consume future dates only."""
    from src.engine.monitoring.scanner_lookup_attention_tuning import _sample_floor_passes, _cohort_book
    prior = (predecessor or {}).get("independent_holdout") or {}
    ids = [r.get("recommendation_id") for r in outcomes]
    if (len(ids) != len(set(ids)) or any(not r.get("rec_date") or r["rec_date"] > target.isoformat()
            or r.get("cohort") not in {"candidate", "control"}
            or _finite(r.get("buy_notional_krw")) is None or r["buy_notional_krw"] <= 0
            or _finite(r.get("net_pnl_krw")) is None or _finite(r.get("net_return_pct")) is None for r in outcomes)):
        return "source_gap", {**prior, "status": "actual_completed_identity_or_cost_invalid"}
    if book["status"] in {"no_effect", "no_capacity_competition"}:
        return "hold_no_edge", {**prior,"status": "not_armed", "reason": book["status"]}
    if book["status"] != "supported_operating_comparison":
        return "source_gap", {**prior,"status": "not_armed", "historical_dates_not_fresh_holdout": True}
    if not selection_edge_passes(book):
        return "hold_no_edge", {**prior,"status": "not_armed"}
    generations = {(p["source_date"], p["scan_generation_id"]) for p in book["pairs"]}
    enough = len(generations) >= MIN_RESOLVED_PAIRS and len({g[0] for g in generations}) >= MIN_RESOLVED_DATES
    if not prior.get("learning_cutoff"):
        if not enough or not _sample_floor_passes(_cohort_book(outcomes)):
            return "hold_sample", {"status": "not_armed"}
        frozen_at = frozen_at or datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        freeze_day = datetime.fromisoformat(frozen_at).astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
        return "forward_holdout_armed", {"status": "armed", "learning_cutoff": max(target.isoformat(),freeze_day),
            "candidate_frozen_at": frozen_at,
            "learning_rows": rows, "learning_inputs": list(inputs.values()),
            "learning_book_sha256": canonical_sha256(book), "learning_outcomes": outcomes,
            "candidate_formula": RESOURCE_PAIR_CONTRACT_VERSION}
    learning_inputs = { (v["row"]["source_date"], v["row"]["scanner_promotion_id"], v["row"]["stock_code"]): v
                        for v in prior.get("learning_inputs", []) if v}
    learned = selection_execution_book(prior.get("learning_rows", []), learning_inputs)
    if (canonical_sha256(learned) != prior.get("learning_book_sha256")
            or prior.get("candidate_formula") != RESOURCE_PAIR_CONTRACT_VERSION
            or not selection_edge_passes(learned)
            or any(r.get("observation_date", "") > prior["learning_cutoff"] for r in prior.get("learning_rows", []))
            or any(r.get("rec_date", "") > prior["learning_cutoff"] for r in prior.get("learning_outcomes", []))
            or not _sample_floor_passes(_cohort_book(prior.get("learning_outcomes", [])))):
        return "source_gap", {**prior, "status": "learning_proof_invalid"}
    cutoff = prior["learning_cutoff"]
    try:
        stamp = datetime.fromisoformat(prior["candidate_frozen_at"])
        freeze_day = stamp.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
        if stamp.tzinfo is None or freeze_day > cutoff:
            raise ValueError("candidate_freeze_clock_invalid")
    except (KeyError, TypeError, ValueError):
        return "source_gap", {**prior,"status":"candidate_freeze_clock_invalid"}
    held_rows = [r for r in rows if r["observation_date"] > cutoff]
    held = selection_execution_book(held_rows, inputs)
    held_generations = {(p["source_date"], p["scan_generation_id"]) for p in held["pairs"]}
    held_outcomes = [r for r in outcomes if str(r.get("rec_date") or "") > cutoff]
    ready = (cutoff < target.isoformat() and selection_edge_passes(held)
             and len(held_generations) >= MIN_RESOLVED_PAIRS and len({g[0] for g in held_generations}) >= MIN_RESOLVED_DATES
             and _sample_floor_passes(_cohort_book(held_outcomes)))
    return ("live_auto_apply_ready" if ready else "hold_sample"), {**prior,
        "status": "validated" if ready else "collecting", "holdout_book": held,
        "holdout_consumed": False, "historical_dates_not_fresh_holdout": True}


def selection_policy_status(
    book, opportunity, rows, inputs, outcomes, predecessor, target, *, frozen_at=None
):
    """Choose an economic disposition without fabricating the unselected arm.

    Full executable replay keeps its existing promotion authority.  When that
    replay is structurally unavailable, complete prospective market-path pairs
    can close the research metric and arm a bounded experiment only after the
    independent real completed model population is mature.
    """
    status, proof = selection_validation(
        book, rows, inputs, outcomes, predecessor, target, frozen_at=frozen_at
    )
    if status != "source_gap":
        return status, proof
    proxy_status = str((opportunity or {}).get("status") or "not_observed")
    opportunity_proof = {
        "status": "not_armed",
        "opportunity_status": proxy_status,
        "opportunity_artifact_sha256": canonical_sha256(opportunity or {}),
        "selection_opportunity_ev_pct": (opportunity or {}).get(
            "selection_opportunity_ev_pct"
        ),
        "historical_execution_inputs_irrecoverable": True,
    }
    if proxy_status in {"not_observed", "contract_invalid"}:
        return "source_gap", opportunity_proof
    if proxy_status in {"hold_no_effect", "no_capacity_competition", "hold_no_edge"}:
        return "hold_no_edge", opportunity_proof
    if proxy_status != "ready" or not (opportunity or {}).get("ready_for_live_gate"):
        return "hold_sample", opportunity_proof
    from src.engine.monitoring.scanner_lookup_attention_tuning import (
        _cohort_book,
        _sample_floor_passes,
    )

    completed_book = _cohort_book(outcomes)
    if not _sample_floor_passes(completed_book):
        return "hold_sample", {
            **opportunity_proof,
            "real_completed_base_support": "insufficient_real_completed_sample",
        }
    return "experiment_ready", {
        **opportunity_proof,
        "status": "experiment_ready",
        "real_completed_base_support": "independent_real_completed_population_mature",
        "experiment_scope": "one_marginal_simple_capacity_slot_krx_regular",
    }


def post_apply_inputs(target, outcomes):
    """Exact immutable selection receipts, never standalone legacy campaign."""
    from src.engine.scalping.scanner_lookup_attention_policy import load_active_policy, POLICY_VERSION
    states = {}
    for day in sorted({target.isoformat(), *(r["rec_date"] for r in outcomes)}):
        active = load_active_policy(day)
        if active.get("active"):
            states[day] = {k:active.get(k) for k in (
                "policy_source_date", "policy_artifact_sha256", "preopen_artifact_sha256",
                "policy_version", "experiment_mode", "experiment_arm")}
    selected = [r for r in outcomes if r["rec_date"] in states and r.get("lookup_attention_weight_runtime_policy_eligible") is True
        and r.get("lookup_attention_weight_policy_artifact_sha256") == states.get(r["rec_date"],{}).get("policy_artifact_sha256")
        and r.get("lookup_attention_weight_policy_version") == POLICY_VERSION]
    incumbent = ({
        "status": (
            "experiment_ready"
            if any(state.get("experiment_mode") is True for state in states.values())
            else "live_auto_apply_ready"
        ),
        "holdout_armed_since": min(s["policy_source_date"] for s in states.values()),
    } if states else {})
    return incumbent, selected, states


def learning_generation(proof):
    if not proof.get("learning_cutoff"):
        return None
    return canonical_sha256({key: proof.get(key) for key in (
        "learning_cutoff", "candidate_frozen_at", "learning_rows", "learning_inputs",
        "learning_book_sha256", "learning_outcomes", "candidate_formula")})


def previous_learning_section(target):
    """Carry an existing frozen candidate across dates, without replaying raw."""
    import json
    from src.engine.scalping.scanner_lookup_attention_policy import SOURCE_REPORT_DIR
    for path in sorted(SOURCE_REPORT_DIR.glob("intraday_ws_freshness_monitor_*.json"), reverse=True):
        day = path.stem.removeprefix("intraday_ws_freshness_monitor_")
        if day >= target.isoformat() or path.stat().st_size > 64 * 1024 * 1024:
            continue
        try:
            section = json.loads(path.read_text())["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"]
            if (section.get("contract_version") == INTEGRATED_CONTRACT
                    and section.get("evaluation_phase") == "postclose_final"
                    and (section.get("independent_holdout") or {}).get("learning_cutoff")
                    and section.get("artifact_sha256") == canonical_sha256({k:v for k,v in section.items() if k != "artifact_sha256"})):
                return section
        except (OSError, KeyError, TypeError, ValueError):
            continue
    return None


def integrated_selection_evaluation(target, events_by_date, *, predecessor=None, migration=None):
    """Bounded final evaluation from incremental native ledgers, never rolling raw.

    Complete simple-capacity selections bind to existing, independently
    validated owner operating replays. Unsupported recipe, terminal or capital
    paths remain null; snapshot/cohort diagnostics never substitute for them.
    """
    from src.engine.monitoring.scanner_lookup_attention_tuning import (
        collect_lineage, load_completed_facts, join_completed_outcomes,
        _latest_symbol_master, _source_quality, _cohort_book, _resource_allocation_pair_book,
        evaluate_post_apply, COST_CONTRACT, _resource_window_start, _conversion_diagnostics,
    )
    generated_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
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
    execution_receipts = []
    inputs = execution_inputs(target, rows, execution_receipts)
    if predecessor and predecessor.get("artifact_sha256") != canonical_sha256({k:v for k,v in predecessor.items() if k != "artifact_sha256"}):
        predecessor = None
    learning_predecessor = predecessor
    if not ((predecessor or {}).get("independent_holdout") or {}).get("learning_cutoff"):
        learning_predecessor = previous_learning_section(target) or predecessor
    # Post-apply PnL is restricted to exact immutable receipt hashes; completed
    # high/low cohorts without selection-version evidence remain observational.
    prior_policy, applied_outcomes, applied_receipts = post_apply_inputs(target, outcomes)
    # Completion revisions and model/source version are in the final input hash.
    import hashlib
    from pathlib import Path
    implementation_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    fingerprint = canonical_sha256({"contract": INTEGRATED_CONTRACT, "evaluator_revision": 4, "evaluator_implementation_sha256": implementation_sha, "execution_source_receipts": execution_receipts, "execution_inputs": list(inputs.values()),
        "events": events_by_date, "facts": facts, "master": master,
        "source_quality": source_quality, "migration": migration, "cost_contract": COST_CONTRACT,
        "prior_policy": prior_policy, "applied_receipts": applied_receipts})
    if (isinstance(predecessor, dict) and predecessor.get("input_sha256") == fingerprint
            and predecessor.get("learning_generation_sha256") == learning_generation((learning_predecessor or {}).get("independent_holdout") or {})
            and predecessor.get("artifact_sha256") == canonical_sha256({k:v for k,v in predecessor.items() if k != "artifact_sha256"})):
        return predecessor
    proxy = _resource_allocation_pair_book(rows, invalid_row_count=lineage["invalid_resource_pair_count"])
    opportunity_economics = {
        **proxy,
        "metric_role": "sim_probe_ev",
        "decision_authority": "research_screen_then_bounded_experiment_only",
        "ready_for_full_live": False,
    }
    conversion = _conversion_diagnostics(observations)
    conversion["intended_consumer"] = "intraday_ws_freshness_monitor.lookup_attention_selection"
    conversion["scope"] = "known_exact_observations;historical_full_census_in_migration_receipt"
    actual_book = _cohort_book(outcomes)
    for cohort in ("all", "candidate", "control"):
        if not actual_book[cohort]["completed_outcome_count"]:
            actual_book[cohort]["net_pnl_krw"] = None
    applied = evaluate_post_apply(prior_policy, applied_outcomes)
    applied["actual_ev_pct"] = applied["book"]["all"]["notional_weighted_ev_pct"] if applied_outcomes else None
    applied["actual_net_pnl_krw"] = applied["book"]["all"]["net_pnl_krw"] if applied_outcomes else None
    if applied["status"] == "not_applicable_before_live_apply":
        applied.pop("book", None)
    primary = selection_execution_book(rows, inputs)
    status, holdout = selection_policy_status(
        primary,
        opportunity_economics,
        rows,
        inputs,
        outcomes,
        learning_predecessor,
        target,
        frozen_at=generated_at,
    )
    if source_quality.get("status") != "pass" or master.get("status") != "pass":
        status = "source_gap"
        holdout = {"status": "source_quality_blocked"}
    if applied["rollback_triggered"] and status != "source_gap":
        status, holdout = "hold_no_edge", {**holdout,"status":"post_apply_rollback"}
    gaps = primary["source_gaps"]
    # Historical report inputs must stay compact. Daily native resource census
    # reaches 58k rows; serialize only the already selected complete proof keys.
    # Exact entry/fill/conversion receipts and raw census diagnostics survive.
    proof_keys = {(row["observation_date"], row["scan_generation_id"], row["stock_code"]) for row in rows}
    native_events = [event for event in events_by_date.get(target.isoformat(), [])
        if event.get("stage") not in {"scalping_scanner_candidate_promoted", "scalping_scanner_candidate_pruned"}
        or (event.get("emitted_date"), (event.get("fields") or {}).get("scanner_scan_generation_id"), event.get("stock_code")) in proof_keys]
    result = {"contract_version": INTEGRATED_CONTRACT, "target_date": target.isoformat(),
        "input_sha256": fingerprint, "status": status, "metric_role": "primary_ev",
        "analysis_mode": (
            "evaluated_existing_execution_owner"
            if primary["pairs"]
            else "evaluated_selection_opportunity_owner"
            if proxy.get("resolved_pair_count")
            else "skipped_" + primary["status"]
        ),
        "quality_finalization": "parent_phase_preserved_by_partial_refresh",
        "execution_inputs": list(inputs.values()), "execution_source_receipts": execution_receipts,
        "evaluation_phase": "postclose_final", "generated_at": generated_at,
        "decision_authority": "source_only_selection_economics",
        "runtime_effect": False, "allowed_runtime_apply": False,
        "actual_order_submitted": False, "broker_order_forbidden": True,
        "window_policy": "rolling90_calendar_native_incremental_ledgers_clean_post_rollout",
        "source_quality_gate": "native_exact_lineage_master_cost_and_same_budget_execution_replay",
        "cost_contract": COST_CONTRACT,
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
        "selection_opportunity_economics": opportunity_economics,
        "actual_completed": {"metric_role": "observational_completed_net", "book": actual_book,
                             "outcomes": outcomes, "causal_uplift": None,
                             "cost_basis": "fixed_fee_tax_comparison_actual_fill_prices_not_broker_reconciled"},
        "actual_applied_version": applied, "post_apply_incumbent": prior_policy,
        "post_apply_completed_outcomes": applied_outcomes, "post_apply_receipts": applied_receipts,
        "post_apply_joint_version_status": "selection_version_attributed;machine_compact_joint_acceptance_in_existing_natural_owner",
        "conversion_diagnostics": conversion,
        "selection_disposition": ("source_gap" if not proxy["complete_partition_count"] else
            "no_capacity_competition" if not proxy["paired_generation_count"] else
            "hold_no_effect" if not proxy["reordered_generation_count"] else "changed_selection"),
        "primary_economics": primary,
        "independent_holdout": holdout, "learning_generation_sha256": learning_generation(holdout),
        "source_gap_owner": "scanner_selection_pair_source_then_natural_assigned_arm_execution",
        "closure_test": "future pair identity reaches opportunity outcome and dated policy; only assigned arm produces natural compact plan guard terminal for post_apply actual economics",
        "eta": None, "first_blocker": gaps[0] if gaps else None,
    }
    from copy import deepcopy
    result = deepcopy(result)
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
    if section.get("contract_version") == INTEGRATED_CONTRACT:
        from src.engine.scalping import scanner_lookup_attention_policy as owner
        from src.engine.monitoring.scanner_lookup_attention_tuning import (
            COST_CONTRACT,
            _resource_allocation_pair_book,
            evaluate_post_apply,
        )
        try:
            inputs = {(v["row"]["source_date"], v["row"]["scanner_promotion_id"], v["row"]["stock_code"]): v
                      for v in section.get("execution_inputs", []) if v}
            rows = section["resource_pair_rows"]
            book = selection_execution_book(rows, inputs)
            expected_opportunity = _resource_allocation_pair_book(
                rows,
                invalid_row_count=(section.get("lineage") or {}).get(
                    "invalid_resource_pair_count", 0
                ),
            )
            proof = section.get("independent_holdout") or {}
            opportunity = section.get("selection_opportunity_economics") or {}
            status, holdout = selection_policy_status(
                book,
                opportunity,
                rows,
                inputs,
                section["actual_completed"]["outcomes"],
                {"independent_holdout": proof},
                target,
            )
            # An armed report validates the original freeze rather than treating
            # its own freeze as an already collected future holdout.
            if section["status"] == "forward_holdout_armed":
                status, holdout = selection_policy_status(
                    book,
                    opportunity,
                    rows,
                    inputs,
                    section["actual_completed"]["outcomes"],
                    None,
                    target,
                    frozen_at=section["generated_at"],
                )
            quality = section["source_quality"].get("status") == "pass" and section["official_symbol_master"].get("status") == "pass"
            if not quality:
                status, holdout = "source_gap", {"status": "source_quality_blocked"}
            applied = evaluate_post_apply(section.get("post_apply_incumbent") or {},section.get("post_apply_completed_outcomes") or [])
            if applied["rollback_triggered"] and status != "source_gap":
                status, holdout = "hold_no_edge", {**holdout,"status":"post_apply_rollback"}
            ready = status in {"live_auto_apply_ready", "experiment_ready"}
            published = date.fromisoformat(policy.get("publication_date") or policy["target_date"])
            dated = date.fromisoformat(policy["target_date"])
            effective = date.fromisoformat(policy["prepared_effective_date"])
            experiment = policy.get("experiment") or {}
            expected_experiment = {}
            if status == "experiment_ready":
                expected_experiment = {
                    "contract_version": "scanner_lookup_attention_experiment_v1",
                    "allocation_seed_sha256": canonical_sha256(
                        {
                            "contract": "scanner_lookup_attention_experiment_allocation_v1",
                            "source_report_artifact_sha256": section[
                                "artifact_sha256"
                            ],
                            "effective_date": effective.isoformat(),
                        }
                    ),
                    "assigned_arm": (
                        "candidate"
                        if owner.count_krx_trading_days(
                            date(2026, 6, 5), effective
                        )
                        % 2
                        else "baseline"
                    ),
                    "max_marginal_slots": 1,
                    "eligible_venue": "KRX",
                    "eligible_session_bucket": "krx_regular",
                    "same_stage_canary_exclusive": True,
                }
            if (not target <= dated <= published < effective or not owner.is_krx_trading_day(dated)
                    or not owner.is_krx_trading_day(effective) or owner.count_krx_trading_days(dated,effective) != 1):
                issues.append("integrated_policy_calendar_binding_invalid")
            expected_status = ("source_quality_blocked" if status == "source_gap" and not quality
                else "source_contract_blocked" if status == "source_gap" else status)
            # Policy owns only sorting permission; source report never owns it.
            issues = [i for i in issues if i != "unsupported_execution_authority"]
            if (section.get("runtime_effect") is not False or section.get("allowed_runtime_apply") is not False
                    or any(p.get("actual_order_submitted") is not False or p.get("broker_order_forbidden") is not True for p in (section,policy))
                    or policy.get("allowed_runtime_apply") is not ready
                    or policy.get("runtime_effect") is not (
                        ready
                        and (
                            status == "live_auto_apply_ready"
                            or (policy.get("experiment") or {}).get("assigned_arm")
                            == "candidate"
                        )
                    )):
                issues.append("unsupported_execution_authority")
            # Reuse the exact existing weight contract without legacy observational evidence.
            zero = {**policy, "status": "source_quality_blocked", "runtime_effect": False, "allowed_runtime_apply": False}
            zero["artifact_sha256"] = canonical_sha256({k:v for k,v in zero.items() if k != "artifact_sha256"})
            if (section.get("evaluation_phase") != "postclose_final"
                    or section.get("cost_contract") != COST_CONTRACT
                    or policy.get("integrated_source_contract") != INTEGRATED_CONTRACT
                    or experiment != expected_experiment
                    or policy.get("source_report_artifact_sha256") != section.get("artifact_sha256")
                    or book != section.get("primary_economics") or status != section.get("status")
                    or opportunity
                    != {
                        **expected_opportunity,
                        "metric_role": "sim_probe_ev",
                        "decision_authority": "research_screen_then_bounded_experiment_only",
                        "ready_for_full_live": False,
                    }
                    or holdout != proof or policy.get("status") != expected_status
                    or policy.get("effective_bonus_points")
                    != (
                        owner.MAX_BONUS_POINTS
                        if status == "live_auto_apply_ready"
                        or (
                            status == "experiment_ready"
                            and (policy.get("experiment") or {}).get("assigned_arm")
                            == "candidate"
                        )
                        else 0.0
                    )
                    or not owner._non_live_payload_valid(zero, source_date=date.fromisoformat(policy["target_date"]))):
                issues.append("integrated_disposition_invalid")
        except (KeyError, TypeError, ValueError, StopIteration, OverflowError, AttributeError):
            issues.append("integrated_disposition_invalid")
        return sorted(set(issues))
    primary = section.get("primary_economics")
    if not isinstance(primary, dict):
        return sorted(set(issues + ["primary_economics_missing"]))
    if (section.get("contract_version") != LEGACY_INTEGRATED_CONTRACT
            or section.get("evaluation_phase") != "postclose_final"
            or policy.get("integrated_source_contract") != LEGACY_INTEGRATED_CONTRACT
            or policy.get("source_report_artifact_sha256") != section.get("artifact_sha256")
            or policy.get("status") != "source_quality_blocked"
            or section.get("status") != "source_gap"
            or primary.get("status") != "source_gap"
            or any(key not in primary or primary[key] is not None for key in (
                "paired_delta_ev_pct", "baseline_budget_ev_pct", "candidate_budget_ev_pct",
                "baseline_net_pnl_krw", "candidate_net_pnl_krw", "tail", "exposure", "model_error"))
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
        binding = report.get("scanner_lookup_attention_publication") or {}
        policy_day = date.fromisoformat(binding.get("policy_date") or target_date).isoformat()
        policy_path = root.parent / "threshold_cycle" / "scanner_lookup_attention_policy" / f"scanner_lookup_attention_policy_{policy_day}.json"
        policy = json.loads(policy_path.read_text())
        issues = validate_integrated_selection(section, policy, target=date.fromisoformat(target_date))
        if binding and (binding.get("publication_date") != policy.get("publication_date")
                or binding.get("effective_date") != policy.get("prepared_effective_date")
                or binding.get("policy_artifact_sha256") != policy.get("artifact_sha256")):
            issues.append("publication_handoff_mismatch")
        if issues or report.get("target_date") != target_date or section.get("evaluation_phase") != "postclose_final":
            raise ValueError("integrated_final_handoff_invalid")
        result.update({"status": section["status"], "source_section_sha256": section["artifact_sha256"],
            "policy_date": policy_day, "publication_date": policy.get("publication_date", policy_day),
            "effective_date": policy.get("prepared_effective_date"), "policy_artifact_sha256": policy["artifact_sha256"],
            "allowed_runtime_apply": policy["allowed_runtime_apply"],
            "primary_economics": section["primary_economics"], "snapshot_proxy": section["snapshot_proxy"],
            "actual_completed": {key:value for key,value in section["actual_completed"].items() if key != "outcomes"}})
    except (OSError, KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        result["source_gap"] = str(exc)
    return result
