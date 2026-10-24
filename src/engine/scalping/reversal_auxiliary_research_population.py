"""Bounded v6 research snapshots using unchanged sources and changed-scope replay.

No provider or runtime mutation. Unchanged branch definitions reuse their native
point census; changed memberships run the current FSM over the original prefix.
Only a hash-selected reservoir is materialized in the existing shared store.
"""

from __future__ import annotations
import copy
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_research as Q
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as R
from src.engine.scalping import reversal_extended_runtime as LIVE
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import continuous_reversal_operating_postclose as O


def retained_source_inventory(data_root, machine, *, as_of):
    """Find retained dates omitted by the published cumulative manifest."""
    from datetime import date
    from src.engine.scalping.continuous_reversal_source import _source_quality_receipt

    if date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("research_source_inventory_date_invalid")
    represented = {p["normalized_source"]["day"] for p in machine["partitions"]}
    base = Path(data_root) / "observations/scalp_micro_reversion_forward"
    dates = sorted(
        {
            p.name.removeprefix("trade_date=")
            for p in base.glob("trade_date=*")
            if p.is_dir()
            and "2026-09-29" <= p.name.removeprefix("trade_date=") <= as_of
        }
    )
    rows = []
    for day in dates:
        files = list(
            (base / ("trade_date=" + day)).glob(
                "venue=*/session=*/market_stream*.jsonl*"
            )
        )
        files = [
            p
            for p in files
            if "event_references" not in p.name
            and p.name.endswith((".jsonl", ".jsonl.gz"))
        ]
        if not files:
            continue
        quality = _source_quality_receipt(data_root, day)
        rows.append(
            dict(
                day=day,
                raw_files=len(files),
                raw_bytes=sum(p.stat().st_size for p in files),
                normalized_in_manifest=day in represented,
                source_quality_eligible=quality["eligible"],
                source_quality_status=quality["status"],
                source_quality_receipts=quality["receipts"],
                needs_backfill=day not in represented and quality["eligible"],
            )
        )
    return P.seal(
        dict(
            schema="auxiliary_retained_source_inventory_v1",
            as_of=as_of,
            rows=rows,
            missing_eligible_dates=[
                row["day"] for row in rows if row["needs_backfill"]
            ],
            excluded_unverified_dates=[
                row["day"]
                for row in rows
                if not row["source_quality_eligible"]
                and not row["normalized_in_manifest"]
            ],
            **P.AUTH,
        )
    )


def operating_path_status(
    label,
    *,
    entry_at,
    position_key=None,
    pin_sha256=None,
    handoffs=(),
    automatic_coverage_end=None,
):
    """Keep the fixed research outcome separate from observed automatic custody."""
    from src.engine.scalping.main_stop_policy import finite
    from src.engine.scalping.main_stop_replay import valid_handoff

    result = dict(
        research_status=label.get("status"),
        operating_status="not_observed",
        actual_realized_net_krw=None,
        **P.AUTH,
    )
    if not position_key or not pin_sha256 or not finite(entry_at):
        return result
    if not isinstance(pin_sha256, str) or len(pin_sha256) != 64:
        return result
    relevant = []
    for row in handoffs:
        if (
            not valid_handoff(row)
            or row.get("position_key") != position_key
            or row.get("pin_sha256") != pin_sha256
            or row["at"] < entry_at
        ):
            raise ValueError("research_operating_handoff_binding_invalid")
        if row.get("registered") is True and row["at"] <= entry_at + 1800:
            relevant.append(row)
    target = label.get("hit_at") if label.get("status") == "WIN" else None
    if target is not None and (
        not finite(target) or not entry_at <= target <= entry_at + 1800
    ):
        raise ValueError("research_target_clock_invalid")
    if relevant:
        first = min(relevant, key=lambda row: row["at"])
        result.update(
            operating_status=(
                "target_before_manual_handoff"
                if target is not None and target < first["at"]
                else (
                    "target_handoff_order_unresolved"
                    if target == first["at"]
                    else "manual_handoff_before_target"
                )
            ),
            handoff_at=first["at"],
            handoff_source_sha256=first["source_sha256"],
        )
    # Empty handoff lists never establish uninterrupted automatic management.
    # A separate consumer-verified coverage bound is required even for a WIN.
    elif (
        finite(automatic_coverage_end)
        and target is not None
        and automatic_coverage_end >= target
    ):
        result["operating_status"] = "target_within_verified_automatic_coverage"
    return result


def build_cumulative(data_root, parent, machine, *, seed, excluded=(), per_scope=6):
    """Census every retained confirmation; materialize only a blind reservoir.

    Current cumulative partitions already contain frozen root truth and the
    approved 30-minute labels. They must match the actual current membership;
    historical AI calls and legacy ten-minute labels are never the universe.
    """
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_cumulative_postclose as cumulative

    if (
        not isinstance(seed, str)
        or not seed
        or type(per_scope) is not int
        or not 1 <= per_scope <= 10
    ):
        raise ValueError("research_reservoir_config_invalid")
    if machine.get("artifact_content_sha256") != P.seal(machine)[
        "artifact_content_sha256"
    ] or parent.get("bundle_sha256") != N.digest(
        {k: v for k, v in parent.items() if k != "bundle_sha256"}
    ):
        raise ValueError("research_population_source_changed")
    manifest = parent["continuous_reversal"]["operating_manifest"]
    if (
        machine.get("label_contract") != C.LABEL
        or machine.get("operating_manifest", {}).get("scopes") != manifest["scopes"]
    ):
        raise ValueError("research_current_machine_or_label_contract_changed")
    until = machine["source_date"]
    inventory = retained_source_inventory(data_root, machine, as_of=until)
    pool = defaultdict(dict)
    census = defaultdict(Counter)
    dates = defaultdict(Counter)
    seen = {}
    admitted = {}
    conflicts = set(machine.get("quarantined_conflicts", []))
    excluded = set(excluded)
    receipts = {}
    partition_census = []
    with S.Store(data_root, readonly=True) as store:
        for part in machine["partitions"]:
            rec = part["normalized_source"]
            day = rec["day"]
            if not "2026-09-29" <= day <= until:
                raise ValueError("research_partition_date_outside_scope")
            dates[day]  # Retain source dates with zero eligible confirmations.
            with N.source_anchor(data_root):
                path = N.source_path(rec["path"])
            if str(path) not in receipts:
                if P.file_hash(path) != rec["sha256"]:
                    raise ValueError("research_normalized_source_changed")
                receipts[str(path)] = dict(path=str(path), sha256=rec["sha256"])
            records = store.get(part["records_object"])
            if (
                P.digest(records) != part["records_sha256"]
                or len(records) != part["points"]
            ):
                raise ValueError("research_partition_changed")
            for point in records:
                sid = point["scope"]
                key = point["opportunity_key"]
                if point.get("day") != day or sid not in manifest["scopes"]:
                    raise ValueError("research_point_scope_or_date_invalid")
                fingerprint = P.digest(point)
                if key in seen:
                    if seen[key] != fingerprint:
                        conflicts.add(key)
                        previous = admitted.pop(key, None)
                        if previous is not None:
                            old_sid, old_day, old_status = previous
                            census[old_sid]["eligible_" + old_status] -= 1
                            dates[old_day]["eligible_" + old_status] -= 1
                            census[old_sid]["conflicting_source_excluded"] += 1
                    continue
                seen[key] = fingerprint
                counter = census[sid]
                counter["all_points"] += 1
                dates[day]["all_points"] += 1
                if not any(
                    point.get("truth", {}).get(b) == "TRUE"
                    for b in manifest["scopes"][sid]
                ):
                    counter["not_selected_machine_confirmation"] += 1
                    continue
                counter["current_machine_confirmations"] += 1
                dates[day]["current_machine_confirmations"] += 1
                status = point["outcome"]["status"]
                counter[status] += 1
                dates[day][status] += 1
                if key in excluded or key in conflicts:
                    counter["development_or_source_excluded"] += 1
                    continue
                if status not in {"WIN", "FAIL_STOP", "FAIL_TIMEOUT"}:
                    counter["outcome_not_evaluable"] += 1
                    continue
                counter["eligible_" + status] += 1
                dates[day]["eligible_" + status] += 1
                admitted[key] = (sid, day, status)
                select(pool, point, None, seed=seed, limit=per_scope)
            partition_census.append(
                dict(
                    day=day,
                    route=rec["venue"],
                    session=rec["session"],
                    source_rows=rec["rows"],
                    records=len(records),
                    records_sha256=part["records_sha256"],
                )
            )
            print(
                json.dumps(
                    dict(
                        partition=len(partition_census),
                        total=len(machine["partitions"]),
                        censused=len(seen),
                        retained=sum(map(len, pool.values())),
                    )
                ),
                flush=True,
            )
        selected = []
        for sid in sorted(pool):
            for key, (_, point, _) in sorted(pool[sid].items()):
                if key in conflicts:
                    continue
                snapshot = cumulative.materialize(store, point, manifest["scopes"][sid])
                if not snapshot[0].get("branch_signals"):
                    raise ValueError("research_selected_snapshot_has_no_signal")
                from datetime import datetime

                event = snapshot[0]
                if (
                    event.get("symbol") != point["symbol"]
                    or event.get("market") != sid.split("|")[1]
                    or event.get("venue") != sid.rsplit("|", 1)[1]
                    or datetime.fromtimestamp(event["epoch"], K.KST).date().isoformat()
                    != point["day"]
                    or not set(event["branch_signals"]) <= set(manifest["scopes"][sid])
                ):
                    raise ValueError("research_selected_snapshot_identity_changed")
                selected.append((point, snapshot))
    with S.Store(data_root) as store:
        points = [
            dict(
                point,
                snapshot_obj=store.put(snapshot),
                operating_outcome=operating_path_status(
                    point["outcome"], entry_at=snapshot[0]["epoch"]
                ),
            )
            for point, snapshot in selected
        ]
        obj = store.put(points)
    return P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=until,
            policy_schema="continuous_reversal_policy_v6",
            parent_bundle_sha256=parent["bundle_sha256"],
            operating_manifest=manifest,
            execution_code_sha256=machine["execution_code_sha256"],
            label_contract=C.LABEL,
            source_parent_machine_sha256=machine["artifact_content_sha256"],
            retained_source_inventory=inventory,
            retained_source_coverage_complete=not inventory["missing_eligible_dates"],
            source_receipts=list(receipts.values()),
            partitions=[
                dict(
                    records_object=obj,
                    records_sha256=P.digest(points),
                    points=len(points),
                )
            ],
            population="all_current_machine_confirmations_from_retained_cumulative_partitions",
            source_dates=sorted(dates),
            source_window=dict(since="2026-09-29", until=until),
            source_materializer_hashes={
                Path(module.__file__).name: P.file_hash(module.__file__)
                for module in (Q, cumulative)
            },
            partition_census=partition_census,
            eligible_census={k: dict(v) for k, v in census.items()},
            daily_census={k: dict(v) for k, v in dates.items()},
            selection=dict(
                seed=seed,
                per_scope=per_scope,
                method="scope_hash_reservoir_label_blind",
            ),
            operating_outcome_authority="observed_exact_custody_only_not_research_label",
            metric_role="diagnostic_win_rate",
            decision_authority="offline_auxiliary_prompt_research_only",
            window_policy="all_retained_source_partitions_since_2026_09_29_current_membership",
            sample_floor="none_explicit_counts_and_unobservable",
            primary_decision_metric="cumulative_PASS_TP_over_TP_plus_FP_on_paired_confirmations",
            source_quality_gate="frozen_normalized_and_record_hashes_current_membership_exact_typed_input",
            forbidden_uses=[
                "realized_profit",
                "order_authority",
                "policy_activation_without_publication",
            ],
            quarantined_conflicts=sorted(conflicts),
            development_keys=sorted(excluded),
            **P.AUTH,
        )
    )


def unchanged_scopes(old_manifest, new_manifest):
    result = set()
    for sid, ids in new_manifest["scopes"].items():
        if set(ids) != set(old_manifest["scopes"].get(sid, [])):
            continue
        if all(C.branch(b) == C.OLD.branch(b) for b in ids):
            result.add(sid)
    return result


def select(pool, point, snapshot, *, seed, limit):
    key = point["opportunity_key"]
    rank = P.digest([seed, key])
    bucket = pool[point["scope"]]
    if key in bucket:
        return
    if len(bucket) < limit or rank < max(v[0] for v in bucket.values()):
        bucket[key] = (rank, copy.deepcopy(point), snapshot)
        if len(bucket) > limit:
            bucket.pop(max(bucket, key=lambda k: bucket[k][0]))


def build(data_root, parent, machine, *, seed, excluded, per_scope=6):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    if (
        not isinstance(seed, str)
        or not seed
        or type(per_scope) is not int
        or not 1 <= per_scope <= 10
    ):
        raise ValueError("research_reservoir_config_invalid")
    if machine["artifact_content_sha256"] != P.seal(machine)["artifact_content_sha256"]:
        raise ValueError("research_population_source_changed")
    if parent["continuous_reversal"]["schema"] != V.SCHEMA:
        raise ValueError("research_v6_parent_required")
    manifest = parent["continuous_reversal"]["operating_manifest"]
    same = unchanged_scopes(machine["operating_manifest"], manifest)
    changed = set(manifest["scopes"]) - same
    pool = defaultdict(dict)
    census = defaultdict(Counter)
    receipts = []
    conflicts = set(machine.get("quarantined_conflicts", []))
    seen = {}
    excluded = set(excluded)
    with S.Store(data_root, readonly=True) as store:
        for number, part in enumerate(machine["partitions"]):
            records = store.get(part["records_object"])
            if P.digest(records) != part["records_sha256"]:
                raise ValueError("research_partition_changed")
            old = {p["opportunity_key"]: p for p in records}
            for p in records:
                if p["scope"] not in same:
                    continue
                key = p["opportunity_key"]
                fingerprint = P.digest(p)
                if key in seen:
                    if seen[key] != fingerprint:
                        conflicts.add(key)
                    continue
                seen[key] = fingerprint
                census[p["scope"]]["all_points"] += 1
                census[p["scope"]][p["outcome"]["status"]] += 1
                if key in excluded or key in conflicts:
                    continue
                if p["outcome"]["status"] not in {"WIN", "FAIL_STOP", "FAIL_TIMEOUT"}:
                    continue
                # Object is loaded only if this point enters the reservoir.
                select(pool, p, None, seed=seed, limit=per_scope)
            rec = part["normalized_source"]
            market = K.market_bucket(rec["session"])
            route = rec["venue"]
            affected = [
                s
                for s in changed
                if s.split("|")[1] == market and s.split("|")[-1] == route
            ]
            if not affected:
                continue
            with N.source_anchor(data_root):
                path = N.source_path(rec["path"])
            if P.file_hash(path) != rec["sha256"]:
                raise ValueError("research_normalized_source_changed")
            receipts.append(dict(path=str(path.resolve()), sha256=rec["sha256"]))
            raw = json.loads(gzip.decompress(path.read_bytes()))["symbols"]
            for symbol, source_rows in sorted(raw.items()):
                keys = (
                    [C.cell_key(symbol, market, 1)]
                    if C.group(symbol) == "samsung"
                    else [f"{C.group(symbol)}|{market}|{b}" for b in C.BANDS]
                )
                sids = [key + "|" + route for key in keys]
                if not set(sids) & changed:
                    continue
                from src.trading.market.session_contract import (
                    market_source_partition_venue as _explicit_item_venue,
                )

                for item in sorted(
                    {
                        r[9]
                        for r in source_rows
                        if isinstance(r[9], str)
                        and r[9].split("_", 1)[0] == symbol
                        and _explicit_item_venue(r[9]) == route
                    }
                ):
                    rows = [r[:] for r in source_rows]
                    for row in rows:
                        if row[9] != item:
                            row[8] = 0
                    ids = sorted(
                        {bid for sid in sids for bid in manifest["scopes"][sid]}
                    )
                    state = R.State(
                        branch_ids=ids,
                        registry_sha256=C.SHA256,
                        session_anchor=next((r for r in rows if r[8]), None),
                        offline=True,
                    )
                    times = [r[0] for r in rows]
                    _, ends, valid = K.segments(rows)
                    tree = K.Tree([r[3] if r[8] else None for r in rows])
                    for index, row in enumerate(rows):
                        ready = state.observe(
                            row, symbol=symbol, venue=route, session=rec["session"]
                        )
                        sid = C.cell_key(symbol, market, row[3] or 1) + "|" + route
                        if ready and sid in changed:
                            event = ready[0]["event"]
                            key = U.opportunity(event)
                            hits = set(event["branch_signals"]) & set(
                                manifest["scopes"][sid]
                            )
                            if hits and key not in seen:
                                seen[key] = "replayed"
                                label = K.label(
                                    rows,
                                    times,
                                    tree,
                                    ends,
                                    valid,
                                    index,
                                    event["entry_ask"],
                                )
                                previous = old.get(key)
                                if (
                                    label["status"] == "UNRESOLVED"
                                    and previous
                                    and previous["outcome"].get("source")
                                    == "same_item_completed_bar_backfill"
                                ):
                                    old_event = store.get(previous["snapshot_obj"])[0]
                                    if all(
                                        old_event.get(k) == event.get(k)
                                        for k in (
                                            "entry_ask",
                                            "epoch",
                                            "source_item",
                                            "native_epoch",
                                            "native_sequence",
                                        )
                                    ):
                                        label = copy.deepcopy(previous["outcome"])
                                        census[sid]["reused_exact_bar_label"] += 1
                                census[sid]["all_points"] += 1
                                census[sid][label["status"]] += 1
                                if label["status"] == "UNRESOLVED":
                                    census[sid][
                                        "unresolved_reason:"
                                        + label.get("reason", "unrecorded")
                                    ] += 1
                                if (
                                    key not in excluded
                                    and key not in conflicts
                                    and label["status"]
                                    in {"WIN", "FAIL_STOP", "FAIL_TIMEOUT"}
                                ):
                                    rank = P.digest([seed, key])
                                    bucket = pool[sid]
                                    if len(bucket) < per_scope or rank < max(
                                        v[0] for v in bucket.values()
                                    ):
                                        snapshot = O.subset(
                                            LIVE.snapshot(state, ready[0]),
                                            manifest["scopes"][sid],
                                        )
                                        p = dict(
                                            opportunity_key=key,
                                            scope=sid,
                                            day=rec["day"],
                                            symbol=symbol,
                                            outcome=label,
                                        )
                                        select(
                                            pool,
                                            p,
                                            snapshot,
                                            seed=seed,
                                            limit=per_scope,
                                        )
                        state.ready.clear()
            print(
                json.dumps(
                    dict(
                        partition=number + 1,
                        total=len(machine["partitions"]),
                        points=sum(v["all_points"] for v in census.values()),
                        retained=sum(map(len, pool.values())),
                    )
                ),
                flush=True,
            )
        # Freeze exact native snapshots only for the selected, bounded reservoir.
        materialized = []
        for sid, bucket in pool.items():
            for key, (_, p, snapshot) in bucket.items():
                if key in conflicts:
                    continue
                if snapshot is None:
                    snapshot = copy.deepcopy(store.get(p["snapshot_obj"]))
                    # v6 changed the envelope registry, while these scope roots
                    # and their exact definitions are identical. Source facts,
                    # signals, times and labels remain untouched.
                    before = P.digest(
                        U.production_request(
                            snapshot[1], U.V1.ARMS[1], event=snapshot[0]
                        )
                    )
                    snapshot[0]["registry_sha256"] = C.SHA256
                    assert before == P.digest(
                        U.production_request(
                            snapshot[1], U.V1.ARMS[1], event=snapshot[0]
                        )
                    )
                materialized.append((p, snapshot))
    with S.Store(data_root) as store:
        points = []
        for p, snapshot in materialized:
            points.append(dict(p, snapshot_obj=store.put(snapshot)))
        obj = store.put(points)
    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    result = P.seal(
        dict(
            schema=O.SCHEMA,
            source_date=machine["source_date"],
            policy_schema=V.SCHEMA,
            parent_bundle_sha256=parent["bundle_sha256"],
            operating_manifest=manifest,
            execution_code_sha256=P.digest(code),
            source_parent_machine_sha256=machine["artifact_content_sha256"],
            source_receipts=receipts,
            label_contract=C.LABEL,
            partitions=[
                dict(
                    records_object=obj,
                    records_sha256=P.digest(points),
                    points=len(points),
                )
            ],
            population="all_source_partitions_with_bounded_hash_reservoir",
            selection=dict(seed=seed, per_scope=per_scope),
            eligible_census={k: dict(v) for k, v in census.items()},
            unchanged_scopes=sorted(same),
            replayed_scopes=sorted(changed),
            quarantined_conflicts=sorted(conflicts),
            development_keys=sorted(excluded),
            **P.AUTH,
        )
    )
    return result
