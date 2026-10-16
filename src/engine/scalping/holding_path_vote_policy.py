"""Dated, source-bound holding path vote policy for the next trading session.

An estimated initial bundle selects only the code baseline. It is not a
realized economic winner and it cannot change an order or a safety guard.
"""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.ai.holding_exit_vote import (
    MARKETS, PATH_IDS, PATH_POLICY_BY_MARKET, PATH_PROMPT_VERSION,
    decide_path_snapshot, input_snapshot_id, validate_path_policy,
)


SCHEMA = "holding_path_vote_selected_policy_v1"
START_DATE = "2026-09-26"
MAX_BYTES = 1024 * 1024
ENV_PATH = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_FILE"
ENV_SHA = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_SHA256"
ENV_DATE = "KORSTOCKSCAN_HOLDING_PATH_VOTE_POLICY_ACTIVE_DATE"


def digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("ascii")).hexdigest()


def policy_path(data_root: Path, target_date: str) -> Path:
    date.fromisoformat(target_date)
    return Path(data_root) / "threshold_cycle" / "holding_path_vote_policy" / (
        f"holding_path_vote_policy_{target_date}.json"
    )


def source_quality_from_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep the summary producer and strict consumer on one cohort projection."""
    population = observation.get("completed_population_quality") or {}
    replay = observation.get("holding_path_vote_replay") or {}
    quality = {
        "strict_population_count": replay.get("strict_population_count"),
        "completed_population_complete": population.get("complete"),
        "main_completed_ids": population.get("db_completed_main_ids") or [],
        "strict_completed_ids": population.get("strict_completed_position_ids") or [],
        "source_gap_ids": population.get("source_gap_ids") or [],
        "excluded_by_id": population.get("excluded_all_reasons") or {},
        "vote_replay_excluded_by_id": replay.get("excluded_by_position_id") or {},
        "source_gap_date_count": len(population.get("source_gap_dates") or []),
    }
    if replay.get('source_status') == 'source_gap_partitioned_vote_inputs_unavailable':
        quality.update(
            completed_population_complete=False,
            replay_cohort_status='source_gap_partitioned_vote_inputs_unavailable',
            main_completed_ids_role='vote_eligible_subset',
            available_actual_population_ids_ref=population.get('db_completed_main_ids_ref'),
            available_actual_population_count=population.get('canonical_main_completed_rows'),
        )
    elif replay.get('source_status') == 'sealed_partition_vote_inputs':
        quality.update(replay_cohort_status='sealed_partition_vote_inputs',
            strict_completed_ids=replay.get('strict_completed_position_ids') or [],
            excluded_by_id=replay.get('partition_excluded_by_position_id') or {},
            main_completed_ids_role='available_actual_population_reference',
            available_actual_population_ids_ref=population.get('db_completed_main_ids_ref'),
            available_actual_population_count=population.get('canonical_main_completed_rows'))
    return quality


def _scenario_decisions(path_id: str, policy: dict[str, Any]) -> dict[str, str]:
    """Expose a vote-availability envelope, not a fabricated AI or EV sample."""
    outcomes = {}
    for name, passes, vetoes, age in (
        ("all_pass", 2, 0, 0.0),
        ("all_veto", 0, 2, 0.0),
        ("mixed", 1, 1, 0.0),
        ("late", 2, 0, policy["max_latest_age_sec"] + 1.0),
        ("source_gap", 0, 0, 0.0),
    ):
        snapshot = {
            "path_id": path_id, "vote_count": passes + vetoes,
            "pass_count": passes, "veto_count": vetoes,
            "firm_pass_count": passes, "firm_veto_count": vetoes,
            "duration_sec": 10.0 if passes + vetoes else 0.0,
            "latest_vote_age_sec": age if passes + vetoes else None,
        }
        outcomes[name] = decide_path_snapshot(snapshot, policy)["decision"]
    return outcomes


def create_bundle(
    *, source_date: str, target_date: str, source_report_sha256: str,
    replay: dict[str, Any], source_quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the explicit baseline even when the natural vote cohort is empty."""
    if (date.fromisoformat(source_date).isoformat() != source_date
            or date.fromisoformat(target_date).isoformat() != target_date
            or not START_DATE <= source_date < target_date
            or not isinstance(source_report_sha256, str)
            or len(source_report_sha256) != 64
            or any(char not in "0123456789abcdef" for char in source_report_sha256)):
        raise ValueError("holding_vote_source_or_target_invalid")
    if replay.get("schema") != "holding_path_vote_postclose_replay_v1":
        raise ValueError("holding_vote_replay_schema_invalid")
    numeric=replay.get('vote_numeric_research') or {}
    if numeric.get('parent'):
        return create_successor(source_date=source_date,target_date=target_date,
            source_report_sha256=source_report_sha256,replay=replay,source_quality=source_quality or {})
    if numeric.get('status')=='incumbent_unverified' and source_date>='2026-10-12':
        raise ValueError('holding_vote_actual_incumbent_unverified')
    source_cells = replay.get("path_market")
    expected_keys = {f"{path}|{market}" for path in PATH_IDS for market in MARKETS}
    legacy_keys = {f"EXIT_BAD_ENTRY_REFINED|{m}" for m in MARKETS}
    if not isinstance(source_cells, dict) or set(source_cells) not in (expected_keys, expected_keys | legacy_keys):
        raise ValueError("holding_vote_replay_cells_invalid")
    quality = source_quality or {}
    if (not isinstance(quality, dict)
            or type(quality.get("strict_population_count")) is not int
            or quality["strict_population_count"] < 0
            or type(quality.get("completed_population_complete")) is not bool
            or any(not isinstance(quality.get(key), list) for key in (
                "main_completed_ids", "strict_completed_ids", "source_gap_ids"
            ))
            or not isinstance(quality.get("excluded_by_id"), dict)
            or not isinstance(quality.get("vote_replay_excluded_by_id"), dict)
            or type(quality.get("source_gap_date_count")) is not int
            or quality["source_gap_date_count"] < 0
            or len(quality["strict_completed_ids"]) != quality["strict_population_count"]
            or [str(value) for value in quality["strict_completed_ids"]]
            != [str(value) for value in replay.get("strict_completed_position_ids") or []]
            or not set(map(str, quality["strict_completed_ids"])).issubset(
                set(map(str, quality["main_completed_ids"]))
            )):
        raise ValueError("holding_vote_source_quality_invalid")
    cells = {}
    for path, market in sorted(PATH_POLICY_BY_MARKET):
        key = f"{path}|{market}"
        source = source_cells[key]
        baseline = dict(PATH_POLICY_BY_MARKET[(path, market)])
        if (not isinstance(source, dict)
                or source.get("path_id") != path or source.get("market") != market
                or source.get("runtime_policy_sha256") != input_snapshot_id(baseline)):
            raise ValueError("holding_vote_replay_baseline_mismatch")
        cells[key] = {
            "path_id": path, "market": market,
            "policy": baseline, "policy_sha256": input_snapshot_id(baseline),
            "rollback_policy_sha256": input_snapshot_id(baseline),
            "selection_reason": "baseline_prior_no_verified_paired_economics",
            "eligible_signal_count": int(source.get("eligible_signal_count") or 0),
            "strict_completed_position_count": int(source.get("strict_completed_position_count") or 0),
            "candidate_census": [
                {"axis": row["axis"], "policy_sha256": row["policy_sha256"],
                 "decision_counts": row["decision_counts"],
                 "paired_ev_krw": row["cost_after_paired_ev_krw"],
                 "censoring_status": row["censoring_status"]}
                for row in source["candidate_grid"]
            ],
            "evidence_layers": {
                "strict_realized": {
                    "completed_position_count": quality["strict_population_count"],
                    "replayable_signal_count": int(source.get("eligible_signal_count") or 0),
                    "paired_ev_krw": None,
                    "status": "counterfactual_execution_unobserved",
                },
                "reconstructed_estimate": {
                    "paired_ev_krw": None,
                    "status": "execution_and_vote_outcome_unidentified",
                },
                "stress_scenario": {
                    "decisions": _scenario_decisions(path, baseline),
                    "paired_ev_interval_krw": None,
                    "status": "decision_envelope_only",
                },
                "baseline_prior": {"policy_sha256": input_snapshot_id(baseline)},
            },
            "realized_paired_ev_krw": None,
            "estimated_paired_ev_krw": None,
            "estimate_status": "scenario_bounds_unidentified_without_model_votes",
            "scenario_decisions": _scenario_decisions(path, baseline),
        }
    bundle = {
        "schema": SCHEMA, "source_date": source_date, "target_date": target_date,
        "valid_until": target_date, "assumption_version": "unidentified_v1",
        "source_report_sha256": source_report_sha256,
        "source_quality": quality,
        "model": "gpt-5.4-nano", "prompt_version": PATH_PROMPT_VERSION,
        "evidence_grade": "estimated_provisional",
        "selection_authority": "operator_directed_initial_baseline_2026_09_26",
        "allowed_runtime_apply": True, "validated_realized_edge": False,
        "realized_paired_ev_krw": None, "estimated_paired_ev_krw": None,
        "policy_set_sha256": digest({key: row["policy_sha256"] for key, row in cells.items()}),
        "rollback_policy_set_sha256": digest({
            key: input_snapshot_id(PATH_POLICY_BY_MARKET[(path, market)])
            for (path, market) in sorted(PATH_POLICY_BY_MARKET)
            for key in (f"{path}|{market}",)
        }),
        "cells": cells,
    }
    bundle["bundle_sha256"] = digest(bundle)
    return bundle


def validate_bundle(
    bundle: Any, *, target_date: str, source_report_sha256: str | None = None,
    require_current_code: bool = True,
) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise ValueError("holding_vote_policy_invalid")
    if bundle.get('schema')==SUCCESSOR_SCHEMA:
        return validate_successor(bundle,target_date=target_date,source_report_sha256=source_report_sha256,
                                  require_current_code=require_current_code)
    unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    try:
        valid_dates = (
            date.fromisoformat(bundle["source_date"]).isoformat() == bundle["source_date"]
            and date.fromisoformat(bundle["target_date"]).isoformat() == target_date
            and START_DATE <= bundle["source_date"] < target_date
        )
    except (KeyError, TypeError, ValueError):
        valid_dates = False
    if (bundle.get("schema") != SCHEMA or not valid_dates
            or bundle.get("target_date") != target_date
            or bundle.get("valid_until") != target_date
            or bundle.get("assumption_version") != "unidentified_v1"
            or bundle.get("model") != "gpt-5.4-nano"
            or bundle.get("prompt_version") not in {PATH_PROMPT_VERSION, "holding_path_vote_v10"}
            or bundle.get("evidence_grade") != "estimated_provisional"
            or bundle.get("selection_authority") != "operator_directed_initial_baseline_2026_09_26"
            or bundle.get("allowed_runtime_apply") is not True
            or bundle.get("validated_realized_edge") is not False
            or bundle.get("realized_paired_ev_krw") is not None
            or bundle.get("estimated_paired_ev_krw") is not None
            or bundle.get("bundle_sha256") != digest(unsigned)
            or not isinstance(bundle.get("source_report_sha256"), str)
            or len(bundle["source_report_sha256"]) != 64
            or any(char not in "0123456789abcdef"
                   for char in bundle["source_report_sha256"])
            or (source_report_sha256 is not None
                and bundle["source_report_sha256"] != source_report_sha256)):
        raise ValueError("holding_vote_policy_header_invalid")
    cells = bundle.get("cells")
    expected = {f"{path}|{market}" for path in PATH_IDS for market in MARKETS}
    legacy = bundle.get("prompt_version") == "holding_path_vote_v10"
    if legacy:
        expected |= {f"EXIT_BAD_ENTRY_REFINED|{m}" for m in MARKETS}
    if not isinstance(cells, dict) or set(cells) != expected:
        raise ValueError("holding_vote_policy_cells_invalid")
    quality = bundle.get("source_quality") or {}
    if (not isinstance(quality, dict)
            or type(quality.get("strict_population_count")) is not int
            or type(quality.get("completed_population_complete")) is not bool
            or not isinstance(quality.get("strict_completed_ids"), list)
            or len(quality["strict_completed_ids"]) != quality["strict_population_count"]):
        raise ValueError("holding_vote_policy_source_quality_invalid")
    hashes = {}
    for path, market in sorted(PATH_POLICY_BY_MARKET):
        key = f"{path}|{market}"
        cell = cells[key]
        baseline = PATH_POLICY_BY_MARKET[(path, market)]
        if (not isinstance(cell, dict) or cell.get("path_id") != path
                or cell.get("market") != market
                or not validate_path_policy(cell.get("policy"))
                or cell.get("policy") != baseline
                or cell.get("policy_sha256") != input_snapshot_id(baseline)
                or cell.get("rollback_policy_sha256") != input_snapshot_id(baseline)
                or cell.get("realized_paired_ev_krw") is not None
                or cell.get("estimated_paired_ev_krw") is not None
                or cell.get("scenario_decisions") != _scenario_decisions(path, baseline)):
            raise ValueError("holding_vote_policy_cell_invalid")
        layers = cell.get("evidence_layers")
        if (not isinstance(layers, dict)
                or set(layers) != {"strict_realized", "reconstructed_estimate",
                                   "stress_scenario", "baseline_prior"}
                or (layers.get("strict_realized") or {}).get("paired_ev_krw") is not None
                or (layers.get("reconstructed_estimate") or {}).get("paired_ev_krw") is not None
                or (layers.get("stress_scenario") or {}).get("paired_ev_interval_krw") is not None
                or (layers.get("baseline_prior") or {}).get("policy_sha256")
                != input_snapshot_id(baseline)
                or not isinstance(cell.get("candidate_census"), list)
                or any(not isinstance(row, dict) or row.get("paired_ev_krw") is not None
                       for row in cell["candidate_census"])):
            raise ValueError("holding_vote_policy_evidence_invalid")
        hashes[key] = cell["policy_sha256"]
    if legacy:
        # Validate archived cells without granting them a consumer or a prompt.
        for market in MARKETS:
            key = "EXIT_BAD_ENTRY_REFINED|" + market
            value = dict(PATH_POLICY_BY_MARKET[("EXIT_SOFT_STOP", market)], max_defer_sec=30.0)
            cell = cells[key]
            if (cell.get("policy") != value or cell.get("policy_sha256") != input_snapshot_id(value)
                    or cell.get("rollback_policy_sha256") != input_snapshot_id(value)
                    or cell.get("realized_paired_ev_krw") is not None
                    or cell.get("estimated_paired_ev_krw") is not None):
                raise ValueError("holding_vote_legacy_retired_cell_invalid")
            hashes[key] = cell["policy_sha256"]
    if (bundle.get("policy_set_sha256") != digest(hashes)
            or bundle.get("rollback_policy_set_sha256") != digest(hashes)):
        raise ValueError("holding_vote_policy_set_hash_invalid")
    return bundle


def load_bundle(
    data_root: Path, target_date: str, *,
    source_report_sha256: str | None = None,
    require_current_code: bool = True,
) -> dict[str, Any]:
    path = policy_path(data_root, target_date)
    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
        raise ValueError("holding_vote_policy_file_invalid")
    return validate_bundle(json.loads(path.read_text(encoding="utf-8")),
                           target_date=target_date,
                           source_report_sha256=source_report_sha256,
                           require_current_code=require_current_code)


def verify_source_handoff(data_root: Path, bundle: dict[str, Any], *, _parent_depth: int = 0,
                          require_current_code: bool = True) -> None:
    """Require report bytes, summary receipt and terminal strict handoff."""
    if _parent_depth >= 370:
        raise ValueError('holding_vote_parent_chain_bound_exceeded')
    root = Path(data_root)
    source_date = bundle["source_date"]
    source_file = (root / "report" / "monitor_snapshots" /
                   f"holding_exit_observation_{source_date}.json")
    summary_file = (root / "report" / "runtime_approval_summary" /
                    f"runtime_approval_summary_{source_date}.json")
    from src.engine.lifecycle.snapshot_archive import read_bytes
    if summary_file.is_symlink() or summary_file.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("holding_vote_source_untrusted_path_or_size")
    source_bytes = read_bytes(source_file, maximum=64 * 1024 * 1024)
    if hashlib.sha256(source_bytes).hexdigest() != bundle["source_report_sha256"]:
        raise ValueError("holding_vote_source_report_hash_mismatch")
    observation = json.loads(source_bytes)
    if not isinstance(observation, dict) or observation.get("date") != source_date:
        raise ValueError("holding_vote_source_report_date_mismatch")
    if bundle.get('schema')==SUCCESSOR_SCHEMA:
        research_root=(root/'report/holding_path_vote_research'/source_date).resolve()
        for cell in bundle['cells'].values():
            proof=cell.get('comparison_receipt')
            if proof and (not Path(proof['root']).resolve().is_relative_to(research_root)
                    or Path(proof['root']).is_symlink()
                    or not Path(proof['contract']['performance_receipt']['path']).resolve().is_relative_to((root/'report/holding_path_vote_research').resolve())):
                raise ValueError('holding_vote_research_native_path_invalid')
    replay = observation.get("holding_path_vote_replay") or {}
    preserved_code = None
    if bundle.get('schema') == SUCCESSOR_SCHEMA:
        from .holding_vote_experiment import code_sha
        current_code = code_sha()
        if bundle.get('code_sha256') != current_code:
            validate_successor(bundle, target_date=bundle['target_date'],
                               require_current_code=require_current_code)
            numeric = replay.get('vote_numeric_research') or {}
            if (bundle.get('selection_mode') != 'incumbent_carry'
                    or numeric.get('code_sha256') != bundle.get('code_sha256')
                    or numeric.get('selected_cells')):
                raise ValueError('holding_vote_consumer_source_code_invalid')
            preserved_code = bundle['code_sha256']
            # Reconstruct with the current unchanged selector, then restore
            # only the verified original code identity for exact comparison.
            replay = {**replay, 'vote_numeric_research': {**numeric, 'code_sha256': current_code}}
    expected = create_bundle(
        source_date=source_date, target_date=bundle["target_date"],
        source_report_sha256=bundle["source_report_sha256"],
        replay=replay,
        source_quality=source_quality_from_observation(observation),
    )
    if preserved_code:
        expected['code_sha256'] = preserved_code
        expected['bundle_sha256'] = digest({k:v for k,v in expected.items() if k != 'bundle_sha256'})
    if bundle.get("prompt_version") == PATH_PROMPT_VERSION and bundle != expected:
        raise ValueError("holding_vote_policy_source_semantics_mismatch")
    if bundle.get("prompt_version") == "holding_path_vote_v10":
        for key, cell in expected["cells"].items():
            if cell != bundle["cells"].get(key):
                raise ValueError("holding_vote_legacy_active_cell_mismatch")
    if bundle.get('schema')==SUCCESSOR_SCHEMA:
        # A parent's original code/bytes are historical lineage, not a claim
        # that the current release consumed that old policy in a live PID.
        native=load_bundle(root,source_date,require_current_code=False)
        verify_source_handoff(root,native, _parent_depth=_parent_depth + 1,
                              require_current_code=False)
        parent=bundle['parent']
        if (parent['path']!=str(policy_path(root,source_date))
            or hashlib.sha256(Path(parent['path']).read_bytes()).hexdigest()!=parent['byte_sha256']
            or native['bundle_sha256']!=parent['bundle_sha256']
            or parent.get('native_policy_set_sha256',native['policy_set_sha256'])!=native['policy_set_sha256']
            or {k:c['policy'] for k,c in native['cells'].items() if not k.startswith('EXIT_BAD_ENTRY_REFINED|')}!=parent['cells']):
            raise ValueError('holding_vote_native_parent_changed')
        from src.engine.lifecycle.holding_window_generation import byte_generation
        from src.engine.lifecycle.broker_cost_reconciliation import source_generation
        if bundle.get('selection_mode') == 'validated_successor' and not bundle.get('contract_file_path'):
            raise ValueError('holding_vote_native_experiment_missing')
        if bundle.get('contract_file_path'):
            from .main_stop_policy import bounded_object
            frozen_path = root/'runtime/research/holding_path_vote'/f'experiments_{source_date}.json'
            if (bundle['contract_file_path'] != str(frozen_path)
                    or bounded_object(frozen_path)[1] != bundle.get('contract_file_sha256')):
                raise ValueError('holding_vote_native_experiment_changed')
        if any(source_generation(root,d)!=g for d,g in bundle['cost_generations'].items()):
            raise ValueError('holding_vote_native_cost_generation_changed')
        for name,generation in {**bundle['source_inventory'],**bundle['vote_source_inventory']}.items():
            if not Path(name).resolve().is_relative_to(root.resolve()):
                raise ValueError('holding_vote_native_source_path_invalid')
            if byte_generation(Path(name))!=generation:raise ValueError('holding_vote_native_source_changed')
    receipt = (json.loads(summary_file.read_text(encoding="utf-8"))
               .get("holding_path_vote_policy") or {})
    if (receipt.get("status") != publication_status(bundle)
            or receipt.get("source_date") != source_date
            or receipt.get("target_date") != bundle["target_date"]
            or receipt.get("bundle_sha256") != bundle["bundle_sha256"]
            or receipt.get("policy_set_sha256") != bundle["policy_set_sha256"]
            or receipt.get("source_report_sha256") != bundle["source_report_sha256"]
            or receipt.get("cell_count") != len(bundle["cells"])):
        raise ValueError("holding_vote_summary_binding_invalid")
    from src.engine.automation.postclose_summary_handoff import stage_receipt_issues
    issues = stage_receipt_issues(root / "report", source_date, "summary_handoff")
    if issues == ["summary_handoff:terminal_missing_or_invalid"]:
        issues = stage_receipt_issues(
            root / "report", source_date, "summary_handoff",
            allow_historical_summary=True,
        )
    if issues:
        raise ValueError("holding_vote_strict_handoff_not_complete")


def runtime_policy_from_env(
    env: dict[str, str], *, data_root: Path, active_date: str | None = None,
) -> tuple[dict, dict]:
    """Load once at process start; exact code baseline is the only fallback."""
    baseline = {key: dict(value) for key, value in PATH_POLICY_BY_MARKET.items()}
    target_date = str(env.get(ENV_DATE) or "")
    today = active_date or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    if target_date and target_date != today:
        return baseline, {"status": "baseline_policy_target_date_stale",
                          "target_date": target_date, "active_date": today}
    try:
        expected_path = policy_path(data_root, target_date) if target_date else None
    except ValueError:
        expected_path = None
    if not target_date or not expected_path or env.get(ENV_PATH) != str(expected_path):
        return baseline, {"status": "baseline_policy_env_missing_or_mismatch"}
    try:
        bundle = load_bundle(data_root, target_date)
        if bundle["bundle_sha256"] != env.get(ENV_SHA):
            raise ValueError("holding_vote_policy_env_hash_mismatch")
        verify_source_handoff(data_root, bundle)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return baseline, {"status": "baseline_policy_load_rejected",
                          "reason": str(exc)}
    selected = {(path, market): dict(bundle["cells"][f"{path}|{market}"]["policy"])
                for path in PATH_IDS for market in MARKETS}
    return selected, {"status": ("validated_successor_loaded" if bundle.get("selection_mode")=="validated_successor" else "verified_incumbent_loaded" if bundle.get("schema")==SUCCESSOR_SCHEMA else "estimated_provisional_loaded"),
                      "target_date": target_date,
                      "bundle_sha256": bundle["bundle_sha256"],
                      "source_date": bundle["source_date"]}


SUCCESSOR_SCHEMA='holding_path_vote_selected_policy_v2'


def publication_status(bundle):
    return ('validated_successor_published' if bundle.get('selection_mode')=='validated_successor'
            else 'verified_incumbent_carried' if bundle.get('schema')==SUCCESSOR_SCHEMA
            else 'estimated_provisional_published')


def create_successor(*,source_date,target_date,source_report_sha256,replay,source_quality):
    """Carry all original cells, changing only a verified numerical EXIT cell."""
    from .holding_vote_experiment import grid,verify_receipt,code_sha
    numeric=replay['vote_numeric_research'];parent=numeric['parent']
    expected={f'{path}|{market}' for path in PATH_IDS for market in MARKETS}
    if (parent.get('target_date')!=source_date or set(parent.get('cells',{}))!=expected
        or not START_DATE<=source_date<target_date or len(source_report_sha256)!=64
        or numeric.get('code_sha256')!=code_sha()):
        raise ValueError('holding_vote_successor_parent_invalid')
    selected=numeric.get('selected_cells') or {};cells={}
    for key in sorted(expected):
        path,market=key.split('|');original=parent['cells'][key]
        if not validate_path_policy(original,path_id=path):raise ValueError('holding_vote_parent_cell_invalid')
        policy=dict(original);receipt=None
        if key in selected:
            if path=='ADD_REBOUND':raise ValueError('holding_vote_add_authority_forbidden')
            row=selected[key];receipt=row['receipt']
            verified=verify_receipt(receipt,parent=original,source_sha=numeric['source_sha256'],cell=key)
            if (receipt['contract']['parent_sha256']!=parent['bundle_sha256']
                or verified['status']!='selected' or grid(path,original).get(verified['selected'])!=row['policy']):
                raise ValueError('holding_vote_successor_comparison_invalid')
            policy=dict(row['policy'])
        cells[key]=dict(path_id=path,market=market,policy=policy,policy_sha256=input_snapshot_id(policy),
            rollback_policy_sha256=input_snapshot_id(original),
            selection_reason='validated_successor' if receipt else 'incumbent_carry',comparison_receipt=receipt,
            realized_paired_ev_krw=None,estimated_paired_ev_krw=(receipt['aggregates'][receipt['selected']]['holdout']['mean_delta_krw'] if receipt else None))
    value=dict(schema=SUCCESSOR_SCHEMA,source_date=source_date,target_date=target_date,valid_until=target_date,
        source_report_sha256=source_report_sha256,source_quality=source_quality,model='gpt-5.4-nano',
        prompt_version=PATH_PROMPT_VERSION,selection_mode='validated_successor' if selected else 'incumbent_carry',
        evidence_grade='validated_counterfactual_successor' if selected else 'verified_incumbent_carry',
        selection_authority='frozen_holding_vote_numeric_exit_experiment',allowed_runtime_apply=True,
        validated_realized_edge=False,realized_paired_ev_krw=None,actual_profit_verified=False,
        parent=parent,code_sha256=code_sha(),source_inventory=numeric.get('source_inventory',{}),
        contract_file_path=numeric.get('contract_file_path'),contract_file_sha256=numeric.get('contract_file_sha256'),
        vote_source_inventory=numeric.get('vote_source_inventory',{}),source_sha256=numeric.get('source_sha256'),cost_generations=numeric.get('cost_generations',{}),
        policy_set_sha256=digest({key:row['policy_sha256'] for key,row in cells.items()}),
        rollback_policy_set_sha256=digest({key:input_snapshot_id(policy) for key,policy in parent['cells'].items()}),cells=cells)
    value['bundle_sha256']=digest(value)
    return validate_successor(value,target_date=target_date,source_report_sha256=source_report_sha256)


def validate_successor(bundle, *,target_date,source_report_sha256=None,require_current_code=True):
    from .holding_vote_experiment import code_sha,grid,verify_receipt,source_generation_sha
    current_code = code_sha()
    if bundle.get('code_sha256') != current_code:
        # Only the already-consumed incumbent is preserved; new research and
        # numerical successor comparisons still require their exact code.
        if bundle.get('selection_mode') != 'incumbent_carry':
            raise ValueError('holding_vote_successor_code_changed')
        if require_current_code:
            from .holding_vote_experiment import _code_paths
            from src.engine.automation.intraday_release_handoff import verify_entry_consumer_code
            verify_entry_consumer_code(target_date, family='holding_vote',
                policy_sha=bundle.get('bundle_sha256'), expected=bundle.get('code_sha256'),
                paths={name: 'src/engine/' + name for name in _code_paths()}, actual=current_code)
    if (bundle.get('schema')!=SUCCESSOR_SCHEMA or bundle.get('bundle_sha256')!=digest({k:v for k,v in bundle.items() if k!='bundle_sha256'})
        or date.fromisoformat(bundle['source_date']).isoformat()!=bundle['source_date']
        or date.fromisoformat(target_date).isoformat()!=target_date
        or not START_DATE<=bundle['source_date']<target_date or bundle.get('target_date')!=target_date
        or bundle.get('valid_until')!=target_date
        or bundle.get('selection_authority')!='frozen_holding_vote_numeric_exit_experiment'
        or bundle.get('allowed_runtime_apply') is not True or bundle.get('validated_realized_edge') is not False
        or bundle.get('actual_profit_verified') is not False or bundle.get('realized_paired_ev_krw') is not None
        or bundle.get('model')!='gpt-5.4-nano' or bundle.get('prompt_version')!=PATH_PROMPT_VERSION
        or not isinstance(bundle.get('source_report_sha256'),str) or len(bundle['source_report_sha256'])!=64
        or any(c not in '0123456789abcdef' for c in bundle['source_report_sha256'])
        or (source_report_sha256 is not None and bundle['source_report_sha256']!=source_report_sha256)):
        raise ValueError('holding_vote_successor_header_invalid')
    if bundle.get('source_sha256') is not None and bundle['source_sha256'] != source_generation_sha(
            bundle.get('source_inventory'), bundle.get('cost_generations'), bundle.get('vote_source_inventory')):
        raise ValueError('holding_vote_successor_source_binding_invalid')
    parent=bundle['parent'];cells=bundle['cells']
    expected={f'{path}|{market}' for path in PATH_IDS for market in MARKETS}
    if (parent.get('target_date')!=bundle['source_date'] or set(parent['cells'])!=expected or set(cells)!=expected
        or parent.get('policy_set_sha256')!=digest({k:input_snapshot_id(v) for k,v in parent['cells'].items()})
        or bundle.get('rollback_policy_set_sha256')!=parent['policy_set_sha256']):
        raise ValueError('holding_vote_successor_parent_invalid')
    selected=False
    for key,cell in cells.items():
        path,market=key.split('|');original=parent['cells'][key];policy=cell['policy']
        if (not validate_path_policy(original,path_id=path) or not validate_path_policy(policy,path_id=path)
            or cell.get('path_id')!=path or cell.get('market')!=market
            or cell.get('policy_sha256')!=input_snapshot_id(policy)
            or cell.get('rollback_policy_sha256')!=input_snapshot_id(original)
            or cell.get('realized_paired_ev_krw') is not None):raise ValueError('holding_vote_successor_cell_invalid')
        receipt=cell.get('comparison_receipt')
        if receipt:
            if path=='ADD_REBOUND' or receipt['contract']['parent_sha256']!=parent['bundle_sha256']:
                raise ValueError('holding_vote_successor_authority_invalid')
            proof=verify_receipt(receipt,parent=original,source_sha=bundle['source_sha256'],cell=key)
            if (proof['status']!='selected' or grid(path,original).get(proof['selected'])!=policy
                or cell.get('selection_reason')!='validated_successor'
                or cell.get('estimated_paired_ev_krw')!=proof['aggregates'][proof['selected']]['holdout']['mean_delta_krw']):
                raise ValueError('holding_vote_successor_proof_invalid')
            selected=True
        elif (policy!=original or cell.get('selection_reason')!='incumbent_carry'
              or cell.get('estimated_paired_ev_krw') is not None):raise ValueError('holding_vote_unproved_change')
    if (bundle.get('selection_mode')!=('validated_successor' if selected else 'incumbent_carry')
        or bundle.get('evidence_grade')!=('validated_counterfactual_successor' if selected else 'verified_incumbent_carry')
        or bundle.get('policy_set_sha256')!=digest({k:c['policy_sha256'] for k,c in cells.items()})):
        raise ValueError('holding_vote_successor_set_invalid')
    return bundle
