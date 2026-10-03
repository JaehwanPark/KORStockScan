"""Bounded retained-source Samsung research and auxiliary consumer validation.

Offline owner in scalping; no live selector, broker/provider client or publisher.
The used 2026-10-02 fold is exploratory, not a pristine performance holdout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import resource
import time

from src.engine.scalping import auxiliary_source_contract as A
from src.engine.scalping import entry_policy_confirmation_research as R
from src.engine.scalping import entry_policy_deep_research as D

C, E, S, P = R.C, R.E, R.S, R.prior
AUTHORITY = {**R.AUTHORITY, "policy_publication_forbidden": True, "partition_contract": A.CONTRACT}
LIMIT = 64 * 1024 * 1024


def in_scope(row):
    return (row.get("stock_code"), row.get("watch_origin"), row.get("effective_venue"),
            row.get("session_bucket")) == ("005930", "MAIN_FIXED_WATCH", "KRX", "KRX_REGULAR")


def phase(prepared):
    return ((prepared["rebuilt"].get("mechanistic_context") or {}).get("group") or {}).get("key_parts", {}).get("structure_phase")


def definitions(training):
    phases = sorted({phase(item) for item in training} - {None, "", "UNKNOWN"})
    specs = []
    for group in [None, *phases]:
        for window in ("all", "before_10", "from_10"):
            for repeat in (1, 2):
                body = dict(recipe="family_setup_confirmation", flow_family="DEPTH_SUPPORTED",
                    match={"venue": "KRX", "session_bucket": "KRX_REGULAR", **({"structure_phase": group} if group else {})},
                    time_window=window, required_consecutive=repeat, repeat_max_gap_sec=60)
                specs.append({**body, "id": C.digest(body)[:16]})
    return specs


def replay(rows, prepared, parent, spec):
    result, previous = [], {}
    for row, item in zip(rows, prepared, strict=True):
        base = item["decision"]["action"]
        clock = A.time_seconds(row.get("decision_ts"))
        key = P.opportunity_identity(row)
        local = datetime.fromisoformat(row["decision_ts"]).astimezone(C.KST)
        window = spec["time_window"]
        time_ok = window == "all" or (local.hour < 10 if window == "before_10" else local.hour >= 10)
        decision = R.prototype_decision(row, parent, item, spec) if in_scope(row) and time_ok else {"action": base}
        confirm = decision["action"] == "ENTER_NOW" and base != "ENTER_NOW"
        earlier = previous.get(key)
        repeats = (earlier[2] + 1 if confirm and earlier and earlier[1] == phase(item)
                   and 0 < clock - earlier[0] <= spec["repeat_max_gap_sec"] else 1 if confirm else 0)
        previous[key] = (clock, phase(item), repeats)
        action = "ENTER_NOW" if confirm and repeats >= spec["required_consecutive"] else base
        result.append({**decision, "action": action, "consecutive_confirmation_count": repeats})
    return result


def episodes(rows, prepared):
    groups, previous = [], {}
    for row, item in zip(rows, prepared, strict=True):
        opportunity = P.opportunity_identity(row)
        # Only already observed decision state/phase, never future price or PnL.
        signature = (phase(item), item["decision"]["action"], item["decision"]["reason"])
        current = previous.get(opportunity)
        if current is None or current[0] != signature:
            group = dict(native_opportunity=opportunity, phase=signature[0], action=signature[1], reason=signature[2],
                first_ts=row["decision_ts"], last_ts=row["decision_ts"], traces=[],
                native_promotion_support_increment=0, boundary="observed_state_transition_not_lifecycle_terminal")
            groups.append(group)
            previous[opportunity] = (signature, group)
        group = previous[opportunity][1]
        group["traces"].append(row["decision_trace_id"])
        group["last_ts"] = row["decision_ts"]
    return dict(segments=groups, native_opportunity_count=len(previous),
        independent_episode_contract="not_proven_retained_native_admission_units")


def exact_response(machine, auxiliary):
    """A same-symbol/day PASS can never populate a recovered attempt."""
    return (machine.get("ai_decision_trace_id") == auxiliary.get("evaluation_key")
        and bool(machine.get("ai_decision_trace_id"))
        and machine.get("evaluation_attempt_id") == auxiliary.get("evaluation_attempt_id")
        and machine.get("bundle_sha256") == auxiliary.get("machine_bundle_sha256")
        and all(machine.get(k) == auxiliary.get(k) for k in ("stock_code", "source_date"))
        and all(isinstance(machine.get(k), str) and isinstance(auxiliary.get(k), str)
                and machine[k].upper() == auxiliary[k].upper() for k in ("effective_venue", "session_bucket"))
        and D.setup_join_digest(machine["setup_evidence"]) is not None
        and D.setup_join_digest(machine["setup_evidence"]) == D.setup_join_digest(
            (auxiliary.get("input") or {}).get("entry_setup_evidence_v1") or {})
        and A.time_seconds(auxiliary.get("decision_ts")) is not None
        and 0 <= A.time_seconds(auxiliary["decision_ts"]) - A.time_seconds(machine["decision_ts"]) <= 60)


def citation_diagnostics(rows):
    report = []
    for row in rows:
        setup = (row.get("input") or {}).get("entry_setup_evidence_v1")
        raw = row.get("raw_response")
        if not isinstance(setup, dict) or not isinstance(raw, dict):
            continue
        repaired, repair = E.repair_mechanistic_pass_citations(raw, setup_evidence=setup)
        assessment = E.evaluate_auxiliary_policy(repaired, setup_evidence=setup,
            machine_policy=row.get("machine_policy"), soft_policy=row.get("parent_auxiliary_soft_policy"))
        citations = [*(raw.get("supporting_fact_ids") or []), *(raw.get("contradicting_fact_ids") or [])]
        report.append(dict(trace=row["evaluation_key"], stock_code=row["stock_code"],
            duplicate_citation_count=len(citations)-len(set(citations)), repair=repair,
            raw_response_sha256=C.digest(raw), replay_response_sha256=C.digest(repaired),
            assessment=assessment, materiality=E.auxiliary_materiality_values(setup),
            operating= A.plan_state(row), fixed_path=row.get("ai_stage_path"),
            raw_response_modified=False))
    return report


def type_error_cells(rows, eligible_keys):
    """Predecision types; CF loss-pass is diagnostic, not realized AI error."""
    cells = defaultdict(list)
    for row in rows:
        if row["evaluation_key"] not in eligible_keys:
            continue
        setup = (row.get("input") or {}).get("entry_setup_evidence_v1") or {}
        context = setup.get("mechanistic_context") or {}
        group = context.get("group") or {}
        valid = (context.get("context_sha256") == C.digest({k:v for k,v in context.items() if k != "context_sha256"})
            and group.get("group_observation_sha256") == C.digest({k:v for k,v in group.items() if k != "group_observation_sha256"}))
        parts = group.get("key_parts", {}) if valid else {}
        families = (context.get("flow") or {}).get("matched_families") if valid else []
        key = (A.partition(row), parts.get("structure_phase", "UNKNOWN"),
               "+".join(sorted(families or [])) or "UNKNOWN", parts.get("liquidity_band", "UNKNOWN"))
        cells[key].append(row)
    result = []
    for key, population in sorted(cells.items()):
        values = [(r, C.auxiliary_stage_net(r)) for r in population]
        result.append(dict(partition=key[0], phase=key[1], flow=key[2], liquidity=key[3],
            attempts=len(values), native_opportunities=len({P.opportunity_identity(r) for r,_ in values}),
            cf_loss_pass_count=sum(r["incumbent_verdict"]=="PASS" and n is not None and n<0 for r,n in values),
            cf_positive_caution_count=sum(r["incumbent_verdict"]=="CAUTION" and n is not None and n>0 for r,n in values),
            cost_gap_count=sum(n is None for _,n in values),
            source_dates=sorted({r["source_date"] for r,_ in values}),
            decision_authority="diagnostic_only_no_rule_selection", realized_profit=None))
    return result


def inputs(root):
    return [root / "tmp/deep-retained-policy-research-20261003/native-snapshots.json",
        root / "tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json",
        root / "tmp/main-machine-auxiliary-source-remediation-20261003/after-machine.json",
        *[root / f"data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_{day}.source.json" for day in P.DAYS]]


def valid_responses(rows):
    accepted, excluded = [], Counter()
    for row in rows:
        natural = row.get("natural_contract_evidence") or {}
        if any(natural.get(k) != "pass" for k in ("semantic_validation_status", "decision_quality_contract_status")):
            excluded["natural_response_invalid"] += 1
            continue
        setup = (row.get("input") or {}).get("entry_setup_evidence_v1")
        if not isinstance(setup, dict) or not isinstance(row.get("raw_response"), dict) or not isinstance(row.get("machine_policy"), dict):
            excluded["response_input_missing"] += 1
            continue
        raw, _ = E.repair_mechanistic_pass_citations(row["raw_response"], setup_evidence=setup)
        result = E.evaluate_auxiliary_policy(raw, setup_evidence=setup, machine_policy=row["machine_policy"],
            soft_policy=row.get("parent_auxiliary_soft_policy"))
        if result["validation_errors"] or result["effective_verdict"] != row["incumbent_verdict"]:
            excluded["response_verdict_or_contract_invalid"] += 1
        elif (row["effective_venue"].upper(), row["session_bucket"].upper()) != ("KRX", "KRX_REGULAR"):
            excluded["other_scope"] += 1
        else:
            accepted.append(row)
    return accepted, dict(excluded)


def run(workspace, output):
    root, output = Path(workspace).resolve(), Path(output).resolve()
    if not output.is_relative_to(root / "tmp") or output == root / "tmp":
        raise ValueError("research_output_must_be_workspace_tmp_child")
    output.mkdir(parents=True, exist_ok=True)
    start, cpu = time.perf_counter(), time.process_time()
    paths = inputs(root)
    # Trace files are smaller than the raw payloads. Exact metadata repair uses
    # the existing bounded reader and unchanged-generation check, once per cold
    # run. Warm resume skips retained projection/trace decoding. It still reads
    # the small cost manifests to bind their backing source-file hashes.
    from src.utils.jsonl_io import existing_or_gzip_path
    trace_paths = [existing_or_gzip_path(root / f"data/ai_decision_trace/ai_decision_trace_{day}.jsonl") for day in P.DAYS]
    trace_paths = [p for p in trace_paths if p and p.exists()]
    observation_path = root / "tmp/deep-retained-policy-research-20261003/observations.json"
    cost_paths = [existing_or_gzip_path(root / f"data/report/micro_reversion_economic_reference/micro_reversion_economic_reference_{day}.json") for day in P.DAYS]
    cost_dependencies, cost_manifest_reads = [], 0
    for path in cost_paths:
        if path and path.exists():
            if path.stat().st_size > LIMIT:
                raise ValueError("cost_reference_scan_budget_exceeded")
            cost_manifest_reads += 1
            for artifact in C.read(path).get("source_artifacts", []):
                resolved = Path(str(artifact.get("resolved_path") or ""))
                if resolved.is_file():
                    cost_dependencies.append(resolved)
    supporting_paths = [*trace_paths, *[p for p in cost_paths if p and p.exists()],
                        *sorted(set(cost_dependencies)), *([observation_path] if observation_path.exists() else [])]
    blobs = {}
    for path in paths:
        if path.stat().st_size > LIMIT:
            raise ValueError("source_scan_budget_exceeded:" + str(path))
        blobs[path] = path.read_bytes()
    import hashlib
    source_hashes = {str(p): hashlib.sha256(b).hexdigest() for p, b in blobs.items()}
    source_hashes.update({str(p): P.file_sha(p) for p in supporting_paths})
    kernels = {str(Path(m.__file__).resolve()): P.file_sha(m.__file__) for m in (R, P, C, E, S, D, A, P.calibration, P.runtime_policy)}
    kernels[str(Path(__file__).resolve())] = P.file_sha(__file__)
    fingerprint = C.digest(dict(sources=source_hashes, kernels=kernels, partitions=A.PARTITIONS,
        contract=A.CONTRACT, windows=["all", "before_10", "from_10"], repeats=[1,2]))
    cached = C.read(output / "result.json")
    if cached:
        if not C.valid(cached) or cached.get("fingerprint") != fingerprint:
            raise ValueError("frozen_research_cache_generation_changed")
        return dict(mode="warm_verified", result_sha256=cached["artifact_content_sha256"],
            wall_sec=time.perf_counter()-start, cpu_sec=time.process_time()-cpu,
            max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            source_byte_verifications=len(paths)+len(supporting_paths), retained_projection_json_decodes=0,
            cost_dependency_manifest_reads=cost_manifest_reads, cost_profile_loads=0,
            bounded_trace_metadata_scan_attempts=0, raw_payload_scans=0)
    if (output / "frozen-candidates.json").exists():
        raise ValueError("incomplete_frozen_checkpoint_requires_new_output")
    decoded = [json.loads(blobs[p]) for p in paths]
    native, old_search, reference, *projections = decoded
    if not C.valid(native) or not C.valid(old_search) or any(not C.valid(p) for p in projections):
        raise ValueError("retained_input_seal_invalid")
    parent = old_search["parent_policy"]
    if C.digest(parent) != native["parent_sha256"]:
        raise ValueError("retained_parent_generation_mismatch")
    all_rows = deepcopy(native["rows"])
    sam = sorted([r for r in all_rows if in_scope(r)], key=lambda r: (r["decision_ts"], r["decision_trace_id"]))
    prepared = [R.prepare(row, parent) for row in sam]
    for row, item in zip(sam, prepared, strict=True):
        if P.calibration._machine_path_value(row)[1]:
            raise ValueError("machine_cost_or_path_invalid")
        row["comparison"] = {**row["comparison"], "incumbent_machine_action": item["decision"]["action"],
                            "incumbent_machine_reason": item["decision"]["reason"]}
    ti = [i for i, row in enumerate(sam) if row["source_date"] < P.DAYS[-1]]
    hi = [i for i, row in enumerate(sam) if row["source_date"] == P.DAYS[-1]]
    train, held = [sam[i] for i in ti], [sam[i] for i in hi]
    tp, hp = [prepared[i] for i in ti], [prepared[i] for i in hi]
    from src.engine.scalping.postclose_entry_validation import chronological_split
    split_train, split_held, split = chronological_split(sam)
    if [r["decision_trace_id"] for r in split_train] != [r["decision_trace_id"] for r in train] or [r["decision_trace_id"] for r in split_held] != [r["decision_trace_id"] for r in held]:
        raise ValueError("dedicated_native_split_changed")
    specs = definitions(tp)
    frozen = C.sealed(dict(fingerprint=fingerprint, parent_policy=parent, candidates=specs,
        split_manifest=split, source_manifest=source_hashes, kernel_manifest=kernels,
        auxiliary_hypotheses="existing_validated_count_materiality_profiles_train_only_and_citation_lifecycle_diagnostics",
        **AUTHORITY))
    C.write(output / "frozen-candidates.json", frozen)
    train_vectors = {s["id"]: [d["action"] for d in replay(train, tp, parent, s)] for s in specs}
    winner, metrics = R.choose(train, train_vectors, specifications={s["id"]: s for s in specs})
    eligible = [s for s in specs if P.research_qualified(metrics[s["id"]])]
    # A redundant clock/repetition condition earns no tie advantage.
    winner = max(sorted(eligible, key=lambda s: s["id"]), key=lambda s: R.rank(metrics[s["id"]],
        complexity=len(s["match"]) + int(s["time_window"] != "all") + int(s["required_consecutive"] > 1)), default={}).get("id")
    C.write(output / "frozen-selection.json", C.sealed(dict(winner=winner, metrics=metrics,
        search_sha256=frozen["artifact_content_sha256"], holdout_used_for_selection=False, **AUTHORITY)))
    auxiliary_rows = [r for p in projections for r in p["rows"]]
    trials, changes = [], []
    for spec in specs:
        held_actions = [d["action"] for d in replay(held, hp, parent, spec)]
        entry = dict(spec=spec, train=metrics[spec["id"]], held=P.economy(held, held_actions))
        if spec["id"] == winner:
            entry["formal_gate"] = P.publisher_diagnostic(train, train_vectors[winner], held, held_actions,
                {**parent, "research_confirmation_overlay": spec}, parent,
                {**reference, "split_manifest": split, "input_sha256": C.digest(source_hashes)}, frozen["artifact_content_sha256"])
            for row, new in zip(train+held, train_vectors[winner]+held_actions, strict=True):
                if new != row["comparison"]["incumbent_machine_action"]:
                    joined = [a for a in auxiliary_rows if exact_response(row, a)]
                    changes.append(dict(trace=row["decision_trace_id"], date=row["source_date"],
                        opportunity=P.opportunity_identity(row), parent=row["comparison"]["incumbent_machine_action"],
                        candidate=new, path=row["entry_quality_path"],
                        auxiliary_response_keys=[a["evaluation_key"] for a in joined],
                        joint_status="exact_response_observed" if len(joined)==1 else "auxiliary_response_not_observed_for_candidate"))
        trials.append(entry)
    # Restore watch lineage only from unchanged trace generation. This does not
    # repair missing stop/fill/price/cost and never overwrites canonical reports.
    upgraded = [C.upgrade_native_watch_metadata(p, root / "data", p["target_date"]) for p in projections]
    auxiliary_rows = [r for p in upgraded for r in p["rows"]]
    cost_cache = {}
    auxiliary_rows = [C.bind_stage_full_cost(r, root / "data", profile_cache=cost_cache) for r in auxiliary_rows]
    # Metadata restoration is also permitted by an exact native response link.
    restored = []
    for row in auxiliary_rows:
        matched = [m for m in all_rows if exact_response(m, row)]
        if len(matched) == 1:
            for key in ("watch_origin", "watch_admission_id", "watch_generation_id", "scanner_promotion_id"):
                if row.get(key) is None and matched[0].get(key) is not None:
                    row[key] = matched[0][key]
            restored.append(row["evaluation_key"])
    population = C.sealed({**projections[-1], "rows": auxiliary_rows, "screened_total": len(auxiliary_rows),
        "source_manifest_sha256": C.digest(source_hashes), "history_projection_sha256s": {
            p["target_date"]: p["artifact_content_sha256"] for p in projections},
        "native_metadata_exact_join_keys": restored})
    stage = {scope: C.evaluate_auxiliary_stage(population, partition_scope=scope) for scope in ("samsung", "non_samsung", "unknown")}
    C.write(output / "auxiliary-population.json", population)
    C.write(output / "auxiliary-stage-results.json", C.sealed({"partitions": stage, **AUTHORITY}))
    valid_aux, invalid_aux = valid_responses(auxiliary_rows)
    fixed_links = [a["evaluation_key"] for a in valid_aux
        if a.get("watch_origin") == "MAIN_FIXED_WATCH" and a.get("stock_code") == "005930"
        and a.get("watch_admission_id") and a.get("watch_generation_id")]
    observations = C.read(observation_path)
    if not C.valid(observations):
        raise ValueError("retained_pre_ai_observation_hash_invalid")
    exact_pre_ai = {row["evaluation_key"]: [m["trace"] for m in observations["rows"] if D.exact_pre_ai_join(m, row)] for row in valid_aux}
    result = C.sealed(dict(fingerprint=fingerprint, source_manifest=source_hashes, kernel_manifest=kernels,
        scope=dict(symbol="005930", origin="MAIN_FIXED_WATCH", venue="KRX", session="KRX_REGULAR"),
        machine=dict(attempts=len(sam), train_attempts=len(train), held_attempts=len(held),
            native_opportunities=len({P.opportunity_identity(r) for r in sam}),
            comparator_attempts=len([r for r in all_rows if r["stock_code"]=="005930" and not in_scope(r)]),
            candidates=len(specs), winner=winner, trials=trials, changes=changes,
            episodes=episodes(sam, prepared),
            temporal_sensitivity={day: dict(attempts=sum(r["source_date"]==day for r in sam),
                recovered=sum(r["date"]==day for r in changes)) for day in P.DAYS},
            new_joint_policy_performance=None),
        auxiliary=dict(partition_counts=dict(Counter(A.partition(r) for r in auxiliary_rows)),
            valid_krx_response_counts=dict(Counter(A.partition(r) for r in valid_aux)),
            baseline_pass_krx_response_counts=dict(Counter(A.partition(r) for r in valid_aux if r["incumbent_verdict"]=="PASS")),
            valid_krx_response_keys=[r["evaluation_key"] for r in valid_aux], response_exclusions=invalid_aux,
            exact_pre_ai_links=exact_pre_ai,
            exact_pre_ai_counts=dict(Counter(A.partition(r) for r in valid_aux if len(exact_pre_ai[r["evaluation_key"]])==1)),
            native_metadata_upgrades=[p.get("native_watch_metadata_upgrade") for p in upgraded],
            type_error_cells=type_error_cells(auxiliary_rows, set(stage["samsung"]["eligible_keys"]+stage["non_samsung"]["eligible_keys"])),
            exact_fixed_watch_response_keys=fixed_links,
            fixed_watch_ai= C.evaluate_auxiliary_stage(C.sealed({**population, "rows": [r for r in auxiliary_rows if r["evaluation_key"] in fixed_links]}), partition_scope="samsung"),
            diagnostics=citation_diagnostics(auxiliary_rows), caution=A.caution_lifecycle(auxiliary_rows)),
        non_samsung_machine_rule_change="deferred_no_new_rule_evidence", **AUTHORITY))
    if source_hashes != {str(p): P.file_sha(p) for p in [*paths, *supporting_paths]}:
        raise ValueError("source_changed_during_research")
    C.write(output / "result.json", result)
    return dict(mode="cold", result_sha256=result["artifact_content_sha256"], wall_sec=time.perf_counter()-start,
        cpu_sec=time.process_time()-cpu, max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_byte_verifications=2*(len(paths)+len(supporting_paths)), retained_projection_json_decodes=len(paths)+1,
        cost_dependency_manifest_reads=cost_manifest_reads, cost_profile_loads=len(cost_cache),
        bounded_trace_metadata_scan_attempts=len(upgraded), raw_payload_scans=0)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
