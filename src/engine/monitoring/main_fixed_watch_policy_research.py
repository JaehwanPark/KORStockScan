"""Bounded Main fixed-watch research using retained native Main observations.

Initial Doosan adoption follows the operator's designated non-Samsung parent;
research support does not veto that initial adoption. This producer cannot
publish/activate policies or create admissions, broker calls or orders.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping import entry_policy_hypothesis_research as replay
from src.engine.scalping import entry_strategy_policy as strategy
from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
from src.engine.scalping.postclose_entry_validation import opportunity_identity, decision_time
from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json as atomic_write_json

SCHEMA = "main_fixed_watch_policy_research_v1"
SYMBOL = "034020"
SOURCE_START = "2026-09-29"
FAMILIES = {
    "continuous_flow": ("trigger_buy_pressure", (55., 60., 65.)),
    "pullback_resume": ("recovery_tick_acceleration", (.8, 1., 1.2)),
    "range_overheat_avoidance": ("overextension_vwap_bp", (60., 80., 100.)),
}
KST = ZoneInfo("Asia/Seoul")


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def freeze(parent, files, *, source_date, publication_date, target_date):
    if not SOURCE_START <= source_date <= publication_date < target_date:
        raise ValueError("fixed_watch_research_date_contract_invalid")
    for value in (source_date, publication_date, target_date):
        date.fromisoformat(value)
    base = deepcopy(parent)
    if "strategy" not in base:
        base = strategy.seed(parent, ("KRX", "KRX_REGULAR"))
    if strategy.validate(base["strategy"]):
        raise ValueError("fixed_watch_parent_strategy_invalid")
    candidates = [{"id": "baseline", "family": "baseline", "policy": deepcopy(parent)}]
    for family, (name, values) in FAMILIES.items():
        for value in values:
            policy = strategy._mutate_tree(base, {name: value}, None)
            if strategy.validate(policy["strategy"]):
                raise ValueError("fixed_watch_candidate_strategy_invalid")
            candidates.append({"id": f"{family}:{value}", "family": family,
                               "parameters": {name: value}, "policy": policy})
    manifest = []
    for path in files:
        path = Path(path).resolve(strict=True)
        before = path.stat()
        sha = file_sha(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("fixed_watch_source_changed_while_freezing")
        manifest.append({"path": str(path), "bytes": after.st_size, "sha256": sha})
    return dict(schema=SCHEMA, symbol=SYMBOL, owner_type="main_scalping",
        watch_origin="MAIN_FIXED_WATCH", source_date=source_date,
        publication_date=publication_date, target_date=target_date,
        venue="KRX", session="KRX_REGULAR", parent_policy_sha256=strategy.digest(parent),
        rollback_parent_sha256=strategy.digest(parent), candidates=candidates,
        source_manifest=manifest, source_manifest_sha256=strategy.digest(manifest),
        kernel_sha256=strategy.digest({str(Path(p).resolve()): file_sha(p)
            for p in (strategy.__file__, replay.calibration.__file__, replay.evidence.__file__,
                      runtime.__file__, replay.__file__, __file__)}),
        initial_policy_designation="current_main_non_samsung",
        initial_policy_preproof_required=False, success_retention_veto=False,
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False)


def evaluate(frozen):
    if frozen.get("schema") != SCHEMA or frozen.get("symbol") != SYMBOL:
        raise ValueError("fixed_watch_research_identity_invalid")
    if len(frozen["candidates"]) != 10 or frozen["source_manifest_sha256"] != strategy.digest(frozen["source_manifest"]):
        raise ValueError("fixed_watch_research_freeze_invalid")
    expected = freeze(frozen["candidates"][0]["policy"], [], source_date=frozen["source_date"],
                      publication_date=frozen["publication_date"], target_date=frozen["target_date"])
    for field in ("owner_type", "watch_origin", "candidates", "parent_policy_sha256", "kernel_sha256",
                  "initial_policy_preproof_required", "runtime_effect", "allowed_runtime_apply"):
        if frozen.get(field) != expected[field]:
            raise ValueError("fixed_watch_frozen_contract_invalid:" + field)
    census, exclusions, native, scanner, seen = Counter(), Counter(), [], [], {}
    conflicts = set()
    costs = []
    for item in frozen["source_manifest"]:
        path = Path(item["path"])
        if file_sha(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError("fixed_watch_frozen_source_changed")
        for row in replay.stream_array(path):
            if row.get("stock_code") != SYMBOL:
                continue
            census["symbol_rows"] += 1
            try:
                if not SOURCE_START <= row["source_date"] <= frozen["source_date"]:
                    raise ValueError("source_date_outside_study")
                if (row.get("effective_venue"), row.get("session_bucket")) != ("KRX", "KRX_REGULAR"):
                    raise ValueError("scope_not_supported")
                if not replay.calibration._machine_source_contract_valid(row):
                    raise ValueError("source_provenance_unverified")
                if row.get("watch_origin") not in {"MAIN_FIXED_WATCH", "ZERO_BASE_DISCOVERY", "SCANNER_PROMOTION", None, ""}:
                    raise ValueError("non_main_watch_origin")
                identity = opportunity_identity(row)
                decision_time(row)
                if not isinstance(row.get("setup_evidence"), dict):
                    raise ValueError("setup_evidence_missing")
                # Retain one earliest actual decision per native admission.
                trace = row.get("decision_trace_id")
                if not trace:
                    raise ValueError("decision_trace_missing")
                key = (identity, trace)
                digest = strategy.digest(row)
                if key in seen:
                    if seen[key] != digest:
                        conflicts.add(identity)
                        raise ValueError("duplicate_trace_conflict")
                    census["duplicate_rows"] += 1
                    continue
                seen[key] = digest
                value, reason = replay.calibration._machine_path_value(row)
                if value is None:
                    raise ValueError("cost_or_path_unresolved:" + str(reason))
                costs.append(row.get("comparison", {}).get("entry_cost_contract"))
                (native if row.get("watch_origin") == "MAIN_FIXED_WATCH" else scanner).append(row)
            except (KeyError, TypeError, ValueError) as exc:
                exclusions[str(exc)] += 1
        if file_sha(path) != item["sha256"]:
            raise ValueError("fixed_watch_source_changed_during_evaluation")
    def earliest(rows):
        result = {}
        for row in sorted(rows, key=lambda r: (decision_time(r), r["decision_trace_id"])):
            identity = opportunity_identity(row)
            if identity not in conflicts:
                result.setdefault(identity, row)
        return list(result.values())
    native, scanner = earliest(native), earliest(scanner)
    days = sorted({row["source_date"] for row in native})
    training = [r for r in native if days and r["source_date"] < days[-1]]
    validation = [r for r in native if days and r["source_date"] == days[-1]]
    results = []
    for candidate in frozen["candidates"]:
        metrics = {}
        for label, rows in (("training", training), ("validation", validation), ("scanner_diagnostic", scanner)):
            metrics[label] = replay.economy(rows, replay.decision_vector(rows, candidate["policy"])) if rows else None
        results.append(dict(id=candidate["id"], family=candidate["family"],
                            policy_sha256=strategy.digest(candidate["policy"]), **metrics))
    baseline = results[0]
    improving = [r for r in results[1:] if r["training"]
        and strategy.machine_winrate_improves(r["training"], baseline["training"])]
    chosen = max(improving, key=lambda r: strategy.machine_admission_rank(r["training"])) if improving else None
    selected = (chosen if chosen and chosen["validation"]
        and strategy.machine_winrate_improves(chosen["validation"], baseline["validation"]) else None)
    status = ("source_gap" if not native else "insufficient_sample" if not training or not validation
              else "candidate_ready" if selected else "measured_no_improvement")
    return dict(schema=SCHEMA, symbol=SYMBOL, owner_type="main_scalping", watch_origin="MAIN_FIXED_WATCH",
        source_date=frozen["source_date"], source_target_date=frozen["source_date"],
        publication_date=frozen["publication_date"], target_date=frozen["target_date"],
        venue="KRX", session="KRX_REGULAR", parent_policy_sha256=frozen["parent_policy_sha256"],
        candidate_policy_sha256=selected["policy_sha256"] if selected else None,
        source_manifest_sha256=frozen["source_manifest_sha256"], kernel_sha256=frozen["kernel_sha256"],
        cost_model_sha256=strategy.digest(costs) if costs else None,
        rollback_parent_sha256=frozen["rollback_parent_sha256"], selection_status=status,
        training_scope=sorted({r["source_date"] for r in training}), validation_scope=days[-1:] if days else [],
        native_support={"fixed_watch_opportunities": len(native), "scanner_diagnostic_opportunities": len(scanner)},
        validation_role="historical_chronological_replay", independent_postfreeze_support=0,
        census=dict(census), exclusions=dict(exclusions), candidates=results,
        entry_runtime_eligible=True, initial_policy_designation="current_main_non_samsung",
        initial_policy_preproof_required=False, initial_designation_is_profitability_proof=False,
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
        actual_completed_net_profit_krw=None, research_profit_is_broker_pnl=False)


def run(data_root, *, source_date, publication_date, target_date, output_dir=None):
    data_root = Path(data_root).resolve()
    bundle = runtime.for_cohort(runtime.load_effective(data_root=data_root, target_date=source_date), ("KRX", "KRX_REGULAR"))
    if bundle is None:
        raise ValueError("main_fixed_watch_parent_policy_missing")
    files = sorted((data_root / "report/machine_observation_projection").glob("machine_observation_projection_????-??-??_*.json"))
    gzip_only = sorted((data_root / "report/machine_observation_projection").glob("machine_observation_projection_????-??-??_*.json.gz"))
    files += [p for p in gzip_only if not p.with_suffix("").exists()]
    files = [p for p in files if SOURCE_START <= p.name.split("_")[-3] <= source_date]
    output = Path(output_dir) if output_dir else data_root / "report/main_fixed_watch_policy_research"
    frozen = freeze(bundle["machine_policy"], files, source_date=source_date,
                    publication_date=publication_date, target_date=target_date)
    frozen["parent_bundle_sha256"] = bundle["bundle_sha256"]
    contract_path = output / "frozen" / f"{strategy.digest(frozen)}.json"
    if contract_path.exists():
        if json.loads(contract_path.read_text()) != frozen:
            raise ValueError("fixed_watch_frozen_contract_conflict")
    else:
        atomic_write_json(contract_path, frozen)
    result = evaluate(frozen)
    result["frozen_contract_path"] = str(contract_path.resolve())
    result["frozen_contract_sha256"] = file_sha(contract_path)
    result["parent_bundle_sha256"] = bundle["bundle_sha256"]
    result["report_sha256"] = strategy.digest(result)
    atomic_write_json(output / f"main_fixed_watch_policy_research_{source_date}.json", result)
    return result


def validate_report(result, *, source_date):
    if (result.get("schema") != SCHEMA or result.get("source_date") != source_date
        or result.get("source_target_date") != source_date
        or result.get("symbol") != SYMBOL or result.get("owner_type") != "main_scalping"
        or result.get("watch_origin") != "MAIN_FIXED_WATCH"
        or result.get("runtime_effect") is not False or result.get("allowed_runtime_apply") is not False
        or result.get("actual_order_submitted") is not False
        or result.get("initial_policy_preproof_required") is not False
        or result.get("initial_policy_designation") != "current_main_non_samsung"
        or result.get("selection_status") not in {"source_gap", "insufficient_sample", "candidate_ready", "measured_no_improvement"}):
        raise ValueError("fixed_watch_report_contract_invalid")
    if result.get("report_sha256") != strategy.digest({k: v for k, v in result.items() if k != "report_sha256"}):
        raise ValueError("fixed_watch_report_hash_invalid")
    path = Path(result["frozen_contract_path"])
    if file_sha(path) != result["frozen_contract_sha256"]:
        raise ValueError("fixed_watch_report_frozen_hash_invalid")
    frozen = json.loads(path.read_text())
    for field in ("symbol", "source_date", "publication_date", "target_date",
                  "parent_policy_sha256", "parent_bundle_sha256", "source_manifest_sha256", "kernel_sha256"):
        if result.get(field) != frozen.get(field):
            raise ValueError("fixed_watch_report_binding_invalid:" + field)
    if not isinstance(result.get("candidates"), list) or len(result["candidates"]) != 10:
        raise ValueError("fixed_watch_report_candidate_budget_invalid")
    for candidate, definition in zip(result["candidates"], frozen["candidates"]):
        if (candidate.get("id") != definition["id"]
            or candidate.get("policy_sha256") != strategy.digest(definition["policy"])):
            raise ValueError("fixed_watch_report_candidate_binding_invalid")
    if (result.get("entry_runtime_eligible") is not True
        or result.get("actual_completed_net_profit_krw") is not None
        or result.get("initial_designation_is_profitability_proof") is not False):
        raise ValueError("fixed_watch_report_authority_invalid")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--publication-date")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    publication = args.publication_date or args.source_date
    result = run(args.data_root, source_date=args.source_date, publication_date=publication,
                 target_date=_next_krx_trading_day(publication), output_dir=args.output_dir)
    print(json.dumps({k: result[k] for k in ("symbol", "selection_status", "native_support", "initial_policy_designation")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
