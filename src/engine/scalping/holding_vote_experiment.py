"""Frozen numerical EXIT-vote comparison, using the original vote population.

This family owns no prompt budget, ADD authorization, hard safety or new exit
rule. The stop and trailing adapters retain their original execution models.
"""

from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
import hashlib
import math
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

from .holding_path_vote_policy import digest, validate_bundle, load_bundle
from .holding_path_vote_replay import _candidate_policies
from .main_stop_policy import bounded_object, finite, StopValues

SCHEMA = "holding_vote_numeric_experiment_v1"
RESULT_SCHEMA = "holding_vote_numeric_research_v1"
EXIT_PATHS = {"EXIT_SOFT_STOP", "EXIT_TRAILING_TP", "EXIT_POST_ADD_FAIL"}
NUMERIC_KEYS = {
    "window_sec",
    "min_votes",
    "pass_votes",
    "veto_votes",
    "firm_pass_votes",
    "firm_veto_votes",
    "max_latest_age_sec",
    "max_gap_sec",
    "min_duration_sec",
    "max_defer_sec",
}


def _code_paths():
    names = (
        "scalping/holding_vote_experiment.py",
        "scalping/holding_vote_exit_models.py",
        "scalping/holding_path_vote_policy.py",
        "scalping/holding_decision_context.py",
        "scalping/ai_market_snapshot.py",
        "scalping/holding_path_vote_replay.py",
        "scalping/main_stop_replay.py",
        "scalping/main_stop_policy.py",
        "scalping/universal_trailing_replay.py",
        "ai/holding_vote_replay_source.py",
        "ai/holding_exit_vote.py",
        "scalping/trailing_exit_decision.py",
        "sniper_state_handlers.py",
        "sniper_execution_receipts.py",
        "holding_exit_observation_report.py",
        "strategy_position_performance_report.py",
        "automation/main_trailing_source_assembler.py",
        "../utils/market_day.py",
        "automation/main_stop_postclose.py",
        "automation/main_stop_source_index.py",
        "lifecycle/broker_cost_reconciliation.py",
        "lifecycle/research_storage.py",
        "lifecycle/research_input_budget.py",
    )
    return names + (
        "lifecycle/holding_window_generation.py",
        "lifecycle/snapshot_archive.py",
    )


def code_sha():
    engine = Path(__file__).parents[1]
    names = _code_paths()
    from src.engine.lifecycle.holding_window_generation import cached_code_generation

    values = cached_code_generation([engine / name for name in names])
    return digest({name: values[str(engine / name)] for name in names})


def grid(path, parent):
    return {digest(policy): policy for _, policy in _candidate_policies(path, parent)}


def validate_contract(contract, *, parent_sha, source_sha, grid_sha, cell):
    """Validate the freeze; None defers only byte binding until discovery.

    Native discovery must repeat this check with the complete input hash before
    any modeled outcome is evaluated. Receipt consumers always supply a hash.
    """
    c = contract
    if (
        not isinstance(c, dict)
        or c.get("schema") != SCHEMA
        or c.get("experiment_sha256")
        != digest({k: v for k, v in c.items() if k != "experiment_sha256"})
        or c.get("parent_sha256") != parent_sha
        or not isinstance(c.get("source_sha256"), str)
        or len(c["source_sha256"]) != 64
        or any(x not in "0123456789abcdef" for x in c["source_sha256"])
        or (source_sha is not None and c["source_sha256"] != source_sha)
        or c.get("candidate_grid_sha256") != grid_sha
        or c.get("cell") != cell
        or cell.split("|")[0] not in EXIT_PATHS
        or c.get("code_sha256") != code_sha()
        or not c.get("approval_reference")
        or not isinstance(c.get("allowed_keys"), list)
        or not c["allowed_keys"]
        or any(not isinstance(key, str) for key in c["allowed_keys"])
        or not set(c["allowed_keys"]) <= NUMERIC_KEYS
        or not isinstance(c.get("max_step"), dict)
        or set(c.get("max_step", {})) != set(c["allowed_keys"])
        or not isinstance(c.get("performance_receipt"), dict)
        or any(not finite(v) or v <= 0 for v in c["max_step"].values())
        or any(
            not finite(c.get(k))
            for k in (
                "frozen_at",
                "split_at",
                "embargo_sec",
                "minimum_paired_ev_krw",
                "min_daily_delta_krw",
                "max_tail_regression_krw",
                "max_exposure_increase_sec",
                "max_model_error_krw",
                "max_standard_error_krw",
                "max_censoring_ratio",
            )
        )
        or c["embargo_sec"] < 240
        or c["frozen_at"] >= c["split_at"] - c["embargo_sec"]
        or any(
            c[k] < 0
            for k in (
                "minimum_paired_ev_krw",
                "min_daily_delta_krw",
                "max_tail_regression_krw",
                "max_exposure_increase_sec",
                "max_model_error_krw",
                "max_standard_error_krw",
            )
        )
        or not 0 <= c["max_censoring_ratio"] < 1
        or any(
            type(c.get(k)) is not int or c[k] < 2
            for k in ("min_train", "min_holdout", "min_train_days", "min_holdout_days")
        )
    ):
        raise ValueError("holding_vote_frozen_contract_invalid")
    performance, sha = bounded_object(
        (c.get("performance_receipt") or {}).get("path", "")
    )
    if (
        sha != c["performance_receipt"].get("sha256")
        or performance.get("schema") != "holding_vote_performance_v1"
        or performance.get("code_sha256") != code_sha()
        or performance.get("status") != "pass"
        or performance.get("scope") != "runtime_and_postclose"
        or performance.get("unresolved_findings") != []
    ):
        raise ValueError("holding_vote_performance_gate_unverified")
    return c


def source_generation_sha(inventory, costs, votes):
    """The approved source includes original votes and their request bytes."""
    if any(not isinstance(value, dict) for value in (inventory, costs, votes)):
        raise ValueError("holding_vote_source_inventory_invalid")
    if any(
        name in inventory and inventory[name] != value for name, value in votes.items()
    ):
        raise ValueError("holding_vote_source_generation_conflict")
    return digest(dict(files={**inventory, **votes}, cost_generations=costs))


def _position_vote_source(position, path):
    first = next(position.rows(), {})
    if path == "EXIT_POST_ADD_FAIL":
        first = next(
            (r for r in position.rows() if r.get("post_add_generation")), first
        )
        return first, first.get("post_add_vote_source")
    return first, first.get("holding_vote_source")


def allowed_candidate(policy, parent, c):
    changes = {k for k in policy if policy[k] != parent[k]}
    return (
        bool(changes)
        and changes <= set(c["allowed_keys"])
        and all(abs(policy[k] - parent[k]) <= c["max_step"][k] for k in changes)
    )


def aggregate(rows, candidate, c):
    """One original position per split; no signal-level pseudo-replication."""
    result = {}
    for split in ("train", "holdout"):
        declared = [r for r in rows if r["split"] == split]
        paired = []
        for row in declared:
            parent = (row.get("outcomes") or {}).get("parent") or {}
            arm = (row.get("outcomes") or {}).get(candidate) or {}
            if (
                parent.get("status") not in {"modeled", "modeled_full_exit"}
                or arm.get("status") not in {"modeled", "modeled_full_exit"}
                or not finite(parent.get("net_krw"))
                or not finite(arm.get("net_krw"))
                or not finite(row.get("actual_net_krw"))
                or abs(parent["net_krw"] - row["actual_net_krw"])
                > c["max_model_error_krw"]
                or any(
                    not finite(x.get(k))
                    for x in (parent, arm)
                    for k in ("exposure_sec", "mae_pct")
                )
            ):
                continue
            paired.append((row, arm["net_krw"] - parent["net_krw"], arm, parent))
        daily = defaultdict(float)
        for row, delta, _, _ in paired:
            daily[row["day"]] += delta
        n = len(paired)
        average = sum(x[1] for x in paired) / n if n else None
        stderr = (
            math.sqrt(sum((x[1] - average) ** 2 for x in paired) / (n - 1) / n)
            if n > 1
            else None
        )
        tail = max(
            (max(0.0, base["net_krw"] - arm["net_krw"]) for _, _, arm, base in paired),
            default=None,
        )
        exposure = max(
            (
                max(0.0, arm["exposure_sec"] - base["exposure_sec"])
                for _, _, arm, base in paired
            ),
            default=None,
        )
        result[split] = dict(
            n=n,
            total=len(declared),
            day_count=len(daily),
            mean_delta_krw=average,
            standard_error_krw=stderr,
            daily_delta_krw=dict(daily),
            worst_day_delta_krw=min(daily.values()) if daily else None,
            max_tail_regression_krw=tail,
            max_exposure_increase_sec=exposure,
        )
    return result


def acceptable(result, split, c):
    x = result[split]
    return (
        x["n"] >= c["min_" + split]
        and x["day_count"] >= c["min_" + split + "_days"]
        and x["total"] >= x["n"]
        and x["total"] > 0
        and 1 - x["n"] / x["total"] <= c["max_censoring_ratio"]
        and x["standard_error_krw"] <= c["max_standard_error_krw"]
        and x["mean_delta_krw"] > c["minimum_paired_ev_krw"]
        and x["worst_day_delta_krw"] >= c["min_daily_delta_krw"]
        and x["max_tail_regression_krw"] <= c["max_tail_regression_krw"]
        and x["max_exposure_increase_sec"] <= c["max_exposure_increase_sec"]
    )


def select(rows, policies, *, parent, contract):
    """Train winner is fixed once. Failed holdout never selects the runner-up."""
    identities = [r["position_key"] for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("holding_vote_duplicate_position")
    eligible = {
        name: aggregate(rows, name, contract)
        for name, value in policies.items()
        if allowed_candidate(value, parent, contract)
    }
    train = [
        (name, x) for name, x in eligible.items() if acceptable(x, "train", contract)
    ]
    if not train:
        return dict(
            status=(
                "hold_sample"
                if not any(x["train"]["n"] for x in eligible.values())
                else "hold_no_edge"
            ),
            selected=None,
            aggregates=eligible,
        )
    name, _ = max(train, key=lambda pair: (pair[1]["train"]["mean_delta_krw"], pair[0]))
    return dict(
        status=(
            "selected"
            if acceptable(eligible[name], "holdout", contract)
            else "hold_no_edge"
        ),
        selected=name if acceptable(eligible[name], "holdout", contract) else None,
        train_selected=name,
        aggregates=eligible,
    )


def split(first, last, contract):
    if last < contract["split_at"] - contract["embargo_sec"]:
        return "train"
    if first > contract["split_at"] + contract["embargo_sec"]:
        return "holdout"
    return "embargo_or_overlap"


def stop_outcomes(rows, policies, *, prepared_votes, path):
    """Unchanged stop values; only the original path's vote policy differs."""
    from .main_stop_replay import replay

    first = next(rows(), {})
    values = StopValues.parse(first["source_stop_values"])
    original = (
        first.get("post_add_vote_source")
        if path == "EXIT_POST_ADD_FAIL"
        else first.get("holding_vote_source")
    )
    if not isinstance(original, dict) or original.get("policy_sha256") != digest(
        policies["parent"]
    ):
        return {
            name: dict(
                status="source_gap",
                reason="original_policy_generation_mismatch",
                net_krw=None,
            )
            for name in policies
        }
    result = {}
    for name, value in policies.items():

        def vote_reader(row, at):
            source = (
                row.get("post_add_vote_source")
                if path == "EXIT_POST_ADD_FAIL"
                else row.get("holding_vote_source")
            )
            try:
                vote = prepared_votes.snapshot(
                    source,
                    at,
                    market=row["market"],
                    route=row["route"],
                    epoch=row["transport_epoch"],
                    entry_at=first["at"],
                    candidate_policy=value,
                )
                return dict(vote, source_verified=True)
            except (ValueError, OSError, KeyError, TypeError):
                return dict(source_verified=False)

        answer = replay(
            rows(),
            values,
            vote_reader=vote_reader,
            post_add_generation=path == "EXIT_POST_ADD_FAIL",
        )
        result[name] = dict(answer, net_krw=answer.get("modeled_net_krw"))
    return result


def native_research(root, day, *, trailing_assembly=None):
    """An unarmed experiment carries the exact parent; source gaps do too."""
    from src.engine.automation import main_stop_postclose as stop
    import time

    token = stop._DEADLINE.set(time.monotonic() + stop.MAX_RESEARCH_SECONDS)
    try:
        return _native_research(root, day, trailing_assembly=trailing_assembly)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # No partial candidate escapes a failed generation or source census.
        result = _native_research(root, day, skip_experiment=True)
        result.update(status="source_gap", blocker=str(exc), selected_cells={})
        return result
    finally:
        stop._DEADLINE.reset(token)


def _native_research(root, day, *, trailing_assembly=None, skip_experiment=False):
    """Run only an armed frozen experiment; missing source cannot become zero.

    Reuse sealed quote indexes and full vote ledgers. No provider/broker calls.
    Returns an additive replay projection consumed by the dated publisher.
    """
    from src.engine.automation import main_stop_postclose as stop
    from src.engine.automation import main_stop_source_index as index
    from src.engine.ai.holding_vote_replay_source import assemble_votes, PreparedVotes
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.lifecycle import research_storage as storage

    root = Path(root)
    try:
        parent = load_bundle(root, day, require_current_code=False)
        from .holding_path_vote_policy import verify_source_handoff

        verify_source_handoff(root, parent, require_current_code=False)
    except (OSError, ValueError, KeyError, TypeError):
        return dict(
            schema=RESULT_SCHEMA,
            status="incumbent_unverified",
            selected_cells={},
            allowed_runtime_apply=False,
        )
    from .holding_path_vote_policy import policy_path

    parent_path = policy_path(root, day)
    parent_receipt = dict(
        path=str(parent_path),
        byte_sha256=hashlib.sha256(parent_path.read_bytes()).hexdigest(),
        bundle_sha256=parent["bundle_sha256"],
        # The native v10 parent includes three retired cells. Preserve its
        # full receipt, but rollback and successor cover only active cells.
        native_policy_set_sha256=parent["policy_set_sha256"],
        policy_set_sha256=digest(
            {
                key: cell["policy_sha256"]
                for key, cell in parent["cells"].items()
                if key.split("|")[0] != "EXIT_BAD_ENTRY_REFINED"
            }
        ),
        target_date=day,
        cells={
            key: cell["policy"]
            for key, cell in parent["cells"].items()
            if key.split("|")[0] != "EXIT_BAD_ENTRY_REFINED"
        },
    )
    contracts_path = (
        root / "runtime/research/holding_path_vote" / f"experiments_{day}.json"
    )
    result = dict(
        schema=RESULT_SCHEMA,
        status="experiment_not_armed",
        parent=parent_receipt,
        code_sha256=code_sha(),
        selected_cells={},
        cells={},
        allowed_runtime_apply=False,
        actual_profit_verified=False,
    )
    if skip_experiment or not contracts_path.exists():
        return result
    contracts, contract_file_sha = bounded_object(contracts_path)
    inventory = {str(path): byte_generation(path) for path in stop.sources(root, day)}
    if trailing_assembly:
        inventory[str(Path(trailing_assembly) / "manifest.json")] = byte_generation(
            Path(trailing_assembly) / "manifest.json"
        )
        from src.engine.automation.main_trailing_all_scope_research import _sealed
        from src.engine.automation.main_trailing_source_assembler import (
            verify_inventory,
        )

        manifest = _sealed(Path(trailing_assembly) / "manifest.json")
        verify_inventory(manifest, Path(trailing_assembly))
        for reference in storage.iter_tree(
            Path(trailing_assembly), manifest["source_generations_ref"]
        ):
            if byte_generation(Path(reference["path"])) != reference["generation"]:
                raise ValueError("holding_vote_trailing_original_source_changed")
            inventory[reference["path"]] = reference["generation"]
    economic_days = sorted(
        {
            Path(p).name.split("_")[-1][:10]
            for p in inventory
            if "/pipeline_events/" in p
        }
    )
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation

    cost_generations = {d: source_generation(root, d) for d in economic_days}
    for d in economic_days:
        snapshot = root / "report/monitor_snapshots" / f"trade_review_{d}.json"
        for path in (snapshot, snapshot.with_suffix(".completed_projection.json")):
            from src.engine.lifecycle.snapshot_archive import identity_available

            if identity_available(path):
                inventory[str(path)] = byte_generation(path)
    inventory_sha = digest(dict(files=inventory, cost_generations=cost_generations))
    source_sha = inventory_sha
    result.update(
        source_inventory=inventory,
        source_sha256=source_sha,
        cost_generations=cost_generations,
        contract_file_sha256=contract_file_sha,
        contract_file_path=str(contracts_path),
    )
    policies = {}
    for cell, c in contracts.items():
        if cell not in parent_receipt["cells"]:
            raise ValueError("holding_vote_experiment_cell_unknown")
        original = parent_receipt["cells"][cell]
        choices = grid(cell.split("|")[0], original)
        validate_contract(
            c,
            parent_sha=parent["bundle_sha256"],
            source_sha=None,
            grid_sha=digest(choices),
            cell=cell,
        )
        policies[cell] = {"parent": original, **choices}
    stop_paths = sorted(
        {cell.split("|")[0] for cell in policies} - {"EXIT_TRAILING_TP"}
    )
    out = (
        root
        / "report/holding_path_vote_research"
        / day
        / digest([source_sha, code_sha(), contract_file_sha])
    )
    out.mkdir(parents=True, exist_ok=True)
    rows = defaultdict(list)
    vote_sources = {}
    census = Counter()
    # Completed metadata has actual native costs, independent of candidate CF.
    days = sorted(
        {
            Path(p).name.split("_")[-1][:10]
            for p in inventory
            if "/pipeline_events/" in p
        }
    )
    import json

    with storage.index(out / "actual_metadata") as db:
        db.execute("CREATE TABLE actual(id TEXT PRIMARY KEY,body TEXT) WITHOUT ROWID")
        n = 0
        for record in stop.completed_evidence(root, days):
            n += 1
            if n > 20000:
                raise ValueError("holding_vote_position_metadata_budget_exceeded")
            raw = storage.encoded(record).decode()
            if len(raw.encode()) > 8192:
                raise ValueError("holding_vote_actual_metadata_row_unbounded")
            identity = record.get("id") or record.get("record_id")
            if type(identity) not in (str, int) or not str(identity).strip():
                raise ValueError("holding_vote_actual_metadata_identity_missing")
            prior = db.execute(
                "SELECT body FROM actual WHERE id=?", (str(identity),)
            ).fetchone()
            if prior:
                if prior[0] != raw:
                    raise ValueError("holding_vote_actual_metadata_conflict")
                continue
            db.execute(
                "INSERT INTO actual VALUES (?,?)",
                (str(identity), raw),
            )
        prepared = index.prepare(
            out,
            {p: g for p, g in inventory.items() if "/pipeline_events/" in p},
            stop.source_events,
            census,
        )
        if any(
            census.get(k)
            for k in ("malformed", "unidentifiable", "unidentifiable_raw_rows")
        ):
            raise ValueError("holding_vote_unidentifiable_source_census")
        # Discover and seal original inputs before computing any candidate.
        # Keep only small immutable references in a bounded disposable index.
        db.execute(
            "CREATE TABLE votes(position TEXT,path TEXT,body TEXT,PRIMARY KEY(position,path)) WITHOUT ROWID"
        )
        discovery_census = Counter()
        for position in index.positions(
            prepared, out, discovery_census, checkpoint=stop.checkpoint
        ):
            for path in stop_paths:
                first, source = _position_vote_source(position, path)
                if path + "|" + str(first.get("market")) not in policies:
                    continue
                reference = (
                    assemble_votes(root, out, source, vote_sources) if source else None
                )
                db.execute(
                    "INSERT INTO votes VALUES (?,?,?)",
                    (position.key, path, storage.encoded(reference).decode()),
                )
        if discovery_census.get("conflicting_rows"):
            raise ValueError("holding_vote_conflicting_original_source")
        source_sha = source_generation_sha(inventory, cost_generations, vote_sources)
        for cell, c in contracts.items():
            validate_contract(
                c,
                parent_sha=parent["bundle_sha256"],
                source_sha=source_sha,
                grid_sha=digest(grid(cell.split("|")[0], policies[cell]["parent"])),
                cell=cell,
            )
        result["source_sha256"] = source_sha
        for position in index.positions(
            prepared, out, census, checkpoint=stop.checkpoint
        ):
            for path in stop_paths:
                first, _ = _position_vote_source(position, path)
                cell = path + "|" + str(first.get("market"))
                if cell not in policies:
                    continue
                stored = db.execute(
                    "SELECT body FROM actual WHERE id=?", (str(first.get("record_id")),)
                ).fetchone()
                record = json.loads(stored[0]) if stored else {}
                cost = record.get("actual_cost_reconciliation") or {}
                valid = (
                    record.get("status") == "COMPLETED"
                    and record.get("main_automatic_management_allowed") is True
                    and cost.get("status") == "actual_cost_reconciled"
                    and cost.get("receipt_sha256")
                    and cost.get("raw_sha256")
                )
                reference = json.loads(
                    db.execute(
                        "SELECT body FROM votes WHERE position=? AND path=?",
                        (position.key, path),
                    ).fetchone()[0]
                )
                with tempfile.TemporaryDirectory(prefix=".votes-", dir=out) as scratch:
                    reader = PreparedVotes(reference, scratch)
                    try:
                        with position.materialized(out) as materialized:
                            begin = first.get("at", position.first)

                            def source_rows():
                                yield from (
                                    r for r in materialized() if r.get("at", 0) >= begin
                                )

                            outcomes = stop_outcomes(
                                source_rows,
                                policies[cell],
                                prepared_votes=reader,
                                path=path,
                            )
                    finally:
                        reader.close()
                rows[cell].append(
                    dict(
                        position_key=position.key,
                        split=split(position.first, position.last, contracts[cell]),
                        day=datetime.fromtimestamp(
                            position.first, ZoneInfo("Asia/Seoul")
                        )
                        .date()
                        .isoformat(),
                        actual_net_krw=cost.get("exact_pnl_krw") if valid else None,
                        outcomes=outcomes,
                        source_sha256=position.source_sha256,
                    )
                )
    if trailing_assembly:
        _trailing_rows(root, Path(trailing_assembly), out, policies, contracts, rows)
    for cell, arms in policies.items():
        original = arms["parent"]
        chosen = select(
            rows[cell],
            {k: v for k, v in arms.items() if k != "parent"},
            parent=original,
            contract=contracts[cell],
        )
        reference = storage.write_tree(out, rows[cell])
        receipt = dict(
            chosen,
            cell=cell,
            parent_policy_sha256=digest(original),
            candidate_grid_sha256=digest(grid(cell.split("|")[0], original)),
            contract=contracts[cell],
            outcomes_ref=reference,
            root=str(out),
            source_sha256=source_sha,
            code_sha256=code_sha(),
            actual_profit_verified=False,
            evidence_mode="actual_entry_counterfactual_exit",
        )
        receipt["receipt_sha256"] = digest(receipt)
        result["cells"][cell] = receipt
        if chosen["selected"]:
            result["selected_cells"][cell] = dict(
                policy=arms[chosen["selected"]], receipt=receipt
            )
    for path, generation in {**inventory, **vote_sources}.items():
        from src.engine.automation.main_trailing_source_assembler import (
            source_generation_matches,
        )

        if not source_generation_matches(
            root, generation.get("source_date", day), Path(path), generation
        ):
            raise ValueError("holding_vote_source_changed_during_research")
    if any(source_generation(root, d) != g for d, g in cost_generations.items()):
        raise ValueError("holding_vote_cost_generation_changed_during_research")
    if bounded_object(contracts_path)[1] != contract_file_sha:
        raise ValueError("holding_vote_contract_changed_during_research")
    if census.get("conflicting_rows"):
        raise ValueError("holding_vote_conflicting_original_source")
    result.update(
        status="selected" if result["selected_cells"] else "incumbent_carry",
        vote_source_inventory=vote_sources,
        census=dict(census),
    )
    return result


def _trailing_rows(root, assembly, out, policies, contracts, rows):
    from src.engine.lifecycle import research_storage as storage
    from src.engine.automation.main_trailing_all_scope_research import _sealed
    from src.engine.automation.main_trailing_path_projection import load_or_build
    from .universal_trailing_replay import replay_many
    from .trailing_mechanical_policy import classifier_hash

    manifest = _sealed(assembly / "manifest.json")
    parent = manifest["approved_parent_receipt"]
    config = parent["classifier_parameters"]
    vector = parent["market_values"]
    used_bytes = [0]
    for part in storage.iter_tree(assembly, manifest["partitions_ref"]):
        payload, paths, claim = load_or_build(
            assembly / part["path"],
            root=assembly,
            out=out / "source_features",
            expected=part["artifact_sha256"],
            as_of=manifest["as_of"],
            source_date=manifest["source_date"],
            configs=[config],
            counters=Counter(),
            resume=True,
            used_bytes=used_bytes,
        )
        try:
            for position in payload["positions"]:
                if position["evidence_kind"] != "actual_completed":
                    continue
                for cell, arms in policies.items():
                    if not cell.startswith("EXIT_TRAILING_TP|"):
                        continue
                    source = position.get("holding_vote_source") or {}
                    if source.get("market") != cell.split("|")[1]:
                        continue
                    prepared = paths[position["position_key"]].paths[
                        classifier_hash(config)
                    ]
                    if source.get("policy_sha256") != digest(arms["parent"]):
                        answers = {
                            k: dict(
                                status="censored",
                                reason="original_policy_generation_mismatch",
                            )
                            for k in arms
                        }
                    else:
                        answers = replay_many(
                            dict(position, original_trailing_source_required=True),
                            prepared,
                            {k: vector for k in arms},
                            classifier_config=config,
                            vote_policies=arms,
                        )
                    outcomes = {
                        k: dict(
                            v,
                            net_krw=v.get("modeled_net_pnl_krw"),
                            exposure_sec=(
                                v.get("last_sell_permission_at", position["entry_at"])
                                - position["entry_at"]
                            ),
                            mae_pct=v.get("mae_pct"),
                        )
                        for k, v in answers.items()
                    }
                    # Without retained path MAE this arm is censored by aggregate.
                    end = position.get("completion_at")
                    rows[cell].append(
                        dict(
                            position_key=position["position_key"],
                            split=(
                                split(position["entry_at"], end, contracts[cell])
                                if finite(end)
                                else "embargo_or_overlap"
                            ),
                            day=datetime.fromtimestamp(
                                position["entry_at"], ZoneInfo("Asia/Seoul")
                            )
                            .date()
                            .isoformat(),
                            actual_net_krw=(
                                position.get("actual_cost_reconciliation") or {}
                            ).get("exact_pnl_krw"),
                            outcomes=outcomes,
                        )
                    )
        finally:
            claim.close()


def verify_receipt(receipt, *, parent, source_sha, cell):
    from src.engine.lifecycle import research_storage as storage

    if (
        not isinstance(source_sha, str)
        or len(source_sha) != 64
        or receipt.get("receipt_sha256")
        != digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
        or receipt.get("cell") != cell
        or receipt.get("code_sha256") != code_sha()
        or receipt.get("source_sha256") != source_sha
        or receipt.get("parent_policy_sha256") != digest(parent)
    ):
        raise ValueError("holding_vote_comparison_receipt_invalid")
    choices = grid(cell.split("|")[0], parent)
    validate_contract(
        receipt["contract"],
        parent_sha=receipt["contract"]["parent_sha256"],
        source_sha=source_sha,
        grid_sha=digest(choices),
        cell=cell,
    )
    rows = []
    for row in storage.iter_tree(Path(receipt["root"]), receipt["outcomes_ref"]):
        if len(rows) >= 20000:
            raise ValueError("holding_vote_outcome_population_budget_exceeded")
        rows.append(row)
    expected = select(rows, choices, parent=parent, contract=receipt["contract"])
    if any(receipt.get(k) != value for k, value in expected.items()):
        raise ValueError("holding_vote_comparison_recompute_mismatch")
    return expected
