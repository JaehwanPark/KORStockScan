"""Explicit offline repair receipts for one legacy setup grammar defect.

No archive writer, publisher, public-loader registration or runtime caller.
The original canonical capture remains the observation identity. A receipt
only repairs its setup representation, never its decision, cost or outcome.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
import re

from src.engine.scalping import entry_setup_evidence as E
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import mechanistic_entry_runtime_policy as M
from src.engine.scalping.ai_decision_trace import _json_bytes

SCHEMA = "entry_setup_family_state_repair_v1"
ERROR = "entry_setup_family_state_inconsistent"
CHANGED_FIELDS = {"setup_state", "execution_readiness_state", "recheck_reasons", "evidence_sha256"}
AUTHORITY = {
    "consumer_scope": "explicit_offline_uncached_machine_observation",
    "metric_role": "source_quality_gate",
    "decision_authority": "offline_source_representation_repair_only",
    "window_policy": "exact_canonical_capture_and_original_scope_parent",
    "sample_floor": "one_exact_identifiable_defect_not_independent_opportunity",
    "primary_decision_metric": "strict_evidence_and_unchanged_recheck_decision",
    "source_quality_gate": "capture_raw_bundle_scope_kernel_and_archive_hash_bound",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "provider_called": False,
    "forbidden_uses": ["runtime_apply", "entry_promotion", "cost_or_outcome_imputation",
                       "native_identity_synthesis", "policy_publication"],
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def restore_original_recipe_metadata(capture: dict) -> tuple[dict, dict]:
    """Recover one originally hashed metadata value, without inventing a hash.

    The canonical capture seals both the original evidence digest and its
    recipe's parent digest. Restoration must match that already recorded
    evidence digest exactly. No feature, legacy fact, action or outcome changes.
    """
    from src.engine.scalping.entry_admission_recipe import DECISION_SCHEMA
    if (capture.get('schema') != 'mechanistic_entry_observation_v1'
        or capture.get('machine_observation_sha256') != S.digest({
            k: v for k, v in capture.items() if k != 'machine_observation_sha256'})
        or capture.get('redacted') is not False
        or any(capture.get(k) is not v for k, v in (
            ('provider_called', False), ('runtime_effect', False),
            ('allowed_runtime_apply', False), ('actual_order_submitted', False),
            ('broker_order_forbidden', True)))):
        raise ValueError('recipe_metadata_capture_invalid')
    source = capture.get('source') or {}
    original = source.get('setup_evidence') or {}
    recipe = (source.get('assessment') or {}).get('admission_recipe') or {}
    raw = original.get('strategy_raw_input')
    if (E.validate_entry_setup_evidence(original) != ['entry_setup_evidence_sha256_invalid']
        or recipe.get('schema') != DECISION_SCHEMA or not isinstance(raw, dict)
        or raw != source.get('exact_payload') or original.get('strategy_raw_sha256') != S.digest(raw)
        or recipe.get('original_raw_sha256') != original.get('strategy_raw_sha256')
        or re.fullmatch('[0-9a-f]{64}', str(recipe.get('parent_sha256'))) is None
        or not isinstance(original.get('strategy_selection'), dict)):
        raise ValueError('recipe_metadata_defect_not_exact')
    restored = deepcopy(original)
    restored['strategy_selection']['policy_sha256'] = recipe['parent_sha256']
    if E.validate_entry_setup_evidence(restored):
        raise ValueError('recipe_metadata_original_digest_not_restored')
    return restored, dict(schema='entry_recipe_original_metadata_restoration_v1',
        original_capture_sha256=capture['machine_observation_sha256'],
        original_evidence_sha256=original['evidence_sha256'],
        restored_evidence_sha256=restored['evidence_sha256'],
        recorded_policy_metadata_sha256=original['strategy_selection'].get('policy_sha256'),
        restored_parent_policy_sha256=recipe['parent_sha256'],
        changed_fields=['strategy_selection.policy_sha256'],
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
        costs_or_outcomes_imputed=False)


def kernel_seals() -> dict:
    """Bind the repair and consumer, without importing a cyclic consumer."""
    package = Path(__file__).resolve().parent
    return {name: file_sha256(package / name) for name in (
        "entry_setup_source_repair.py", "entry_setup_evidence.py",
        "entry_strategy_policy.py", "ai_decision_quality.py",
        "ai_action_outcome_calibration.py", "mechanistic_entry_runtime_policy.py")}


def _reconstruct(capture: dict, bundle: dict) -> tuple[dict, dict]:
    if (capture.get("schema") != "mechanistic_entry_observation_v1"
            or capture.get("machine_observation_sha256") != hashlib.sha256(
                _json_bytes({k: v for k, v in capture.items()
                             if k != "machine_observation_sha256"})).hexdigest()
            or capture.get("redacted") is not False
            or any(capture.get(k) is not v for k, v in (
                ("provider_called", False), ("runtime_effect", False),
                ("allowed_runtime_apply", False), ("actual_order_submitted", False),
                ("broker_order_forbidden", True)))):
        raise ValueError("source_repair_canonical_capture_invalid")
    source = capture.get("source") or {}
    old = source.get("setup_evidence") or {}
    if (E.validate_entry_setup_evidence(old) != [ERROR]
            or old.get("setup_family") != "NO_VALID_SETUP"
            or old.get("setup_state") != "WAIT_CONFIRMATION"
            or (old.get("local_breakout") or {}).get("recheck_required") is not True):
        raise ValueError("source_repair_defect_not_exact")
    raw = old.get("strategy_raw_input")
    if (not isinstance(raw, dict) or not raw
            or old.get("strategy_raw_sha256") != S.digest(raw)
            or raw != source.get("exact_payload")):
        raise ValueError("source_repair_exact_raw_invalid")
    at = datetime.fromisoformat(capture["captured_at"])
    observed = datetime.fromisoformat(raw["strategy_observed_at"])
    if at.utcoffset() is None or observed.utcoffset() is None or observed > at:
        raise ValueError("source_repair_timestamp_invalid")
    context = capture.get("label_context") or {}
    scope = tuple(str(context.get(k) or "").upper()
                  for k in ("effective_venue", "session_bucket"))
    if scope != tuple(str(raw.get(k) or "").upper()
                      for k in ("effective_venue", "session_bucket")):
        raise ValueError("source_repair_scope_conflict")
    for key in ("stock_code", "snapshot_id", "evaluation_attempt_id", "broker_route"):
        if not context.get(key) or raw.get(key) != context[key]:
            raise ValueError("source_repair_identity_conflict:" + key)
    for key in ("watch_origin", "watch_admission_id", "watch_generation_id"):
        if raw.get(key) != context.get(key) or capture.get(key) != context.get(key):
            raise ValueError("source_repair_watch_conflict:" + key)
    M.validate(bundle, target_date=bundle["target_date"])
    if bundle["bundle_sha256"] != capture.get("bundle_sha256"):
        raise ValueError("source_repair_original_bundle_conflict")
    scoped = M.for_cohort(bundle, scope)
    if scoped is None:
        raise ValueError("source_repair_parent_scope_missing")
    parent = scoped["machine_policy"]
    repaired, _, _ = S.rebuild(old, parent)
    changed = {k for k in set(old) | set(repaired) if old.get(k) != repaired.get(k)}
    if (changed != CHANGED_FIELDS or E.validate_entry_setup_evidence(repaired)
            or repaired.get("setup_family") != "NO_VALID_SETUP"
            or repaired.get("setup_state") != "UNCONFIRMED"
            or repaired.get("execution_readiness_state") != "UNCONFIRMED"
            or repaired.get("recheck_reasons") != ["SETUP_DISCOVERY_RECHECK"]):
        raise ValueError("source_repair_reconstruction_not_exact")
    decision = E.mechanistic_entry_policy_decision(repaired, policy=parent)
    recorded = source.get("assessment") or {}
    expected = ("RECHECK", "local_breakout_confirmation_required")
    if (decision.get("action"), decision.get("reason")) != expected or (
            recorded.get("action"), recorded.get("reason")) != expected:
        raise ValueError("source_repair_decision_or_guard_changed")
    return repaired, {
        "scope": list(scope), "parent_policy_sha256": S.digest(parent),
        "original_setup_sha256": S.digest(old),
        "repaired_setup_sha256": S.digest(repaired),
        "changed_fields": sorted(changed), "original_validation_errors": [ERROR],
        "machine_action": decision["action"], "machine_reason": decision["reason"],
    }


def build_receipt(capture: dict, bundle: dict, *, source_path: Path,
                  source_sha256: str, source_line: int) -> dict:
    """Caller supplies a sealed archive location; consumption verifies its hash."""
    if re.fullmatch(r"[0-9a-f]{64}", source_sha256 or "") is None or (
            type(source_line) is not int or source_line <= 0):
        raise ValueError("source_repair_archive_location_invalid")
    repaired, proof = _reconstruct(capture, bundle)
    body = {
        "schema": SCHEMA, **AUTHORITY, **proof,
        "original_capture_sha256": capture["machine_observation_sha256"],
        "original_bundle": deepcopy(bundle),
        "repaired_setup_evidence": repaired,
        "source_location": {"path": str(source_path.resolve()),
                            "physical_sha256": source_sha256, "line": source_line},
        "kernel_seals": kernel_seals(),
    }
    return {**body, "content_sha256": S.digest(body)}


def consume_receipt(capture: dict, receipt: dict, *, source_path: Path,
                    source_sha256: str) -> tuple[dict, dict]:
    """Reject stale/tampered receipts; return a working setup, never a new capture."""
    if receipt.get("content_sha256") != S.digest(
            {k: v for k, v in receipt.items() if k != "content_sha256"}):
        raise ValueError("source_repair_receipt_hash_invalid")
    location = receipt.get("source_location") or {}
    expected = build_receipt(capture, receipt["original_bundle"],
        source_path=source_path, source_sha256=source_sha256,
        source_line=location.get("line"))
    if receipt != expected:
        raise ValueError("source_repair_receipt_binding_invalid")
    if file_sha256(source_path) != source_sha256:
        raise ValueError("source_repair_archive_hash_changed")
    # The receipt line is evidence too; hashing a receipt with a fabricated
    # line number must not make that location valid.
    import gzip
    import json
    opener = gzip.open if source_path.suffix == ".gz" else open
    located = None
    with opener(source_path, "rt") as stream:
        for line, text in enumerate(stream, 1):
            if line == location["line"]:
                located = json.loads(text)
                break
    if file_sha256(source_path) != source_sha256:
        raise ValueError("source_repair_archive_hash_changed")
    if located != capture:
        raise ValueError("source_repair_archive_line_conflict")
    return deepcopy(receipt["repaired_setup_evidence"]), {
        "schema": SCHEMA, **AUTHORITY,
        "receipt_sha256": receipt["content_sha256"],
        "original_validation_errors": receipt["original_validation_errors"],
        "original_capture_sha256": capture["machine_observation_sha256"],
        "original_setup_sha256": receipt["original_setup_sha256"],
        "repaired_setup_sha256": receipt["repaired_setup_sha256"],
        "parent_policy_sha256": receipt["parent_policy_sha256"],
    }


def replay_archive_subset(*, data_root: Path, dates: tuple[str, ...], stock_code: str,
                          scope: tuple[str, str], repair_trace: str) -> dict:
    """Bounded CLI-only real consumer replay, without public cache writers.

    A process-local archive selector limits input to canonical records in the
    requested scope. Pipeline data and the real label/cost owners are unchanged.
    No hook is installed by importing this module or by consuming a receipt.
    """
    import json
    from src.engine.scalping import ai_action_outcome_calibration as calibration

    if (not dates or len(dates) > 3 or dates != tuple(sorted(set(dates)))
            or any(re.fullmatch(r"2026-\d{2}-\d{2}", d) is None or d < "2026-09-29" for d in dates)
            or re.fullmatch(r"\d{6}", stock_code) is None or len(scope) != 2):
        raise ValueError("source_repair_replay_scope_invalid")
    seals, selected, locations, original_populations = {}, {}, {}, {}
    archive_iterator = calibration.iter_jsonl
    for day in dates:
        path = data_root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl"
        if not path.exists(): path = path.with_suffix(".jsonl.gz")
        seals[str(path.resolve())] = file_sha256(path)
        # Preserve physical line numbers and inspect canonical data only.
        import gzip
        opener = gzip.open if path.suffix == ".gz" else open
        rows = []
        original_valid = {}
        with opener(path, "rt") as stream:
            for line, text in enumerate(stream, 1):
                if not text.strip(): continue
                capture = json.loads(text)
                if (capture.get("schema") == "mechanistic_entry_observation_v1"
                        and calibration._kst_date_from_aware_timestamp(capture.get("captured_at")) == day
                        and capture.get("redacted") is False
                        and all(capture.get(k) is v for k, v in (
                            ("provider_called", False), ("runtime_effect", False),
                            ("allowed_runtime_apply", False), ("actual_order_submitted", False),
                            ("broker_order_forbidden", True)))
                        and capture.get("machine_observation_sha256") == hashlib.sha256(_json_bytes(
                            {k: v for k, v in capture.items() if k != "machine_observation_sha256"})).hexdigest()
                        and not E.validate_entry_setup_evidence((capture.get("source") or {}).get("setup_evidence"))):
                    original_valid[capture["machine_observation_sha256"]] = capture
                context = capture.get("label_context") or {}
                if (capture.get("schema") == "mechanistic_entry_observation_v1"
                        and context.get("stock_code") == stock_code
                        and tuple(str(context.get(k) or "").upper()
                                  for k in ("effective_venue", "session_bucket")) == scope):
                    trace = capture["machine_observation_sha256"]
                    if trace in locations: raise ValueError("source_repair_duplicate_capture")
                    rows.append(capture); locations[trace] = path, line
        selected[str(path.resolve())] = rows
        original_populations[day] = list(original_valid.values())
    captures = [c for rows in selected.values() for c in rows]
    target = next((c for c in captures if c["machine_observation_sha256"] == repair_trace), None)
    if target is None: raise ValueError("source_repair_target_missing")
    parent_path = data_root / "runtime/mechanistic_entry_policy/generations" / (target["bundle_sha256"] + ".json")
    seals[str(parent_path.resolve())] = file_sha256(parent_path)
    bundle = json.loads(parent_path.read_text())
    path, line = locations[repair_trace]
    receipt = build_receipt(target, bundle, source_path=path,
                           source_sha256=seals[str(path.resolve())], source_line=line)
    # Bind all actual read dependencies in the bounded label/cost lane.
    for day in dates:
        for rel in (f"pipeline_events/pipeline_events_{day}.jsonl",
                    f"report/machine_completed_price_source/machine_completed_price_source_{day}.json",
                    f"report/micro_reversion_economic_reference/micro_reversion_economic_reference_{day}.json"):
            dependency = data_root / rel
            if not dependency.exists(): dependency = Path(str(dependency) + ".gz")
            if dependency.is_file():
                seals[str(dependency.resolve())] = file_sha256(dependency)
                if "economic_reference" in rel:
                    from src.engine.scalping.ai_action_outcome_calibration import _load_json
                    for item in _load_json(dependency).get("source_artifacts", []):
                        resolved = Path(str(item.get("resolved_path") or ""))
                        if resolved.is_file(): seals[str(resolved.resolve())] = file_sha256(resolved)

    def only_selected(path):
        if Path(path).parent.name == "ai_decision_payloads":
            return iter(selected.get(str(Path(path).resolve()), []))
        return archive_iterator(path)

    # The full-population cache's manifest cannot match a six-row diagnostic
    # selector or the repaired population. Verify its original population with
    # the unchanged cache owner first, then use only the exact requested routes.
    # This adapter is report-only; it does not rewrite/reseal that old cache.
    completed_loader = calibration._machine_completed_price_rows
    verified_batches = {}
    def original_population_prices(*, data_root, day, observations, fetcher, as_of):
        if fetcher is not None or as_of is not None:
            raise ValueError("source_repair_price_adapter_provider_forbidden")
        if day not in verified_batches:
            verified_batches[day] = calibration._machine_completed_price_rows_locked(
                data_root=data_root, day=day, observations=original_populations[day], fetcher=None, as_of=None)
        prices, proof, codes = verified_batches[day]
        expected_routes = {
            (str(c["label_context"]["stock_code"]),
             calibration._normalized_venue(c["label_context"].get("effective_venue")),
             calibration._normalized_session(c["label_context"].get("session_bucket")),
             calibration._machine_outcome_request_code(c)) for c in observations}
        filtered = [p for p in prices if (
            str(p.get("stock_code")), calibration._normalized_venue(p.get("effective_venue")),
            calibration._normalized_session(p.get("session_bucket")), p.get("source_request_code")) in expected_routes]
        return filtered, {**proof,
            "original_population_count": len(original_populations[day]),
            "original_capture_manifest_sha256": S.digest(sorted(
                c["machine_observation_sha256"] for c in original_populations[day])),
            "offline_exact_route_subset_count": len(filtered),
            "cache_resealed": False,
            "population_binding": "verified_original_population_then_report_only_route_subset"}, codes

    calibration.iter_jsonl = only_selected
    calibration._machine_completed_price_rows = original_population_prices
    try:
        options = dict(target_date=dates[-1], minimum_source_date=dates[0], independent_machine=True)
        baseline, baseline_counts = calibration._load_machine_observation_rows_uncached(data_root, **options)
        repaired, repaired_counts = calibration._load_machine_observation_rows_uncached(data_root, **options,
            source_setup_repairs={repair_trace: receipt})
    finally:
        calibration.iter_jsonl = archive_iterator
        calibration._machine_completed_price_rows = completed_loader
    base = {r["decision_trace_id"]: r for r in baseline}
    fixed = {r["decision_trace_id"]: r for r in repaired}
    if len(base) != len(baseline) or len(fixed) != len(repaired) or set(fixed) - set(base) != {repair_trace}:
        raise ValueError("source_repair_consumer_count_or_identity_invalid")
    if any(row != fixed.get(trace) for trace, row in base.items()):
        raise ValueError("source_repair_unchanged_rows_drift")
    row = fixed[repair_trace]
    if row["machine_action"] != "RECHECK" or E.validate_entry_setup_evidence(row["setup_evidence"]):
        raise ValueError("source_repair_last_consumer_invalid")
    native = lambda rows: sorted({(r["watch_origin"], r["watch_admission_id"], r["watch_generation_id"])
                                for r in rows})
    if native(baseline) != native(repaired):
        raise ValueError("source_repair_native_opportunity_changed")
    if any(file_sha256(Path(p)) != h for p, h in seals.items()):
        raise ValueError("source_repair_replay_source_changed")
    body = {"schema": "entry_setup_family_state_repair_replay_v1", **AUTHORITY,
        "dates": list(dates), "stock_code": stock_code, "scope": list(scope),
        "source_seals": seals, "receipt": receipt,
        "canonical_count": len(captures), "baseline_count": len(baseline), "repaired_count": len(repaired),
        "baseline_census": baseline_counts, "repaired_census": repaired_counts,
        "existing_rows_unchanged": True, "native_opportunities": native(repaired),
        "native_count": len(native(repaired)), "repaired_row": row,
        "baseline_rows_sha256": S.digest(baseline), "repaired_rows_sha256": S.digest(repaired),
        "input_selection": "process_local_exact_canonical_scope_and_verified_original_population_price_subset",
    }
    return {**body, "content_sha256": S.digest(body)}


def main() -> None:
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dates", nargs="+", required=True)
    parser.add_argument("--stock-code", required=True)
    parser.add_argument("--scope", required=True, help="Exact VENUE|SESSION")
    parser.add_argument("--repair-trace", required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(Path("tmp").resolve()) or output.exists():
        parser.error("output must be a new file inside workspace tmp")
    value = replay_archive_subset(data_root=args.data_root.resolve(), dates=tuple(args.dates),
        stock_code=args.stock_code, scope=tuple(args.scope.split("|")), repair_trace=args.repair_trace)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: value[k] for k in ("canonical_count", "baseline_count", "repaired_count", "native_count")}))


if __name__ == "__main__":
    main()
