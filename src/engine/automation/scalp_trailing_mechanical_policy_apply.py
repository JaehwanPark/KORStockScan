"""Publish a bounded, source-bound trailing classifier selection for PREOPEN.

The postclose report is research. Only this reviewed deterministic handoff may
create an apply receipt, and bootstrap checks it again before any runtime env.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.automation.runtime_policy_bootstrap import build_manifest
from src.engine.automation.postclose_finalization_generation import (
    snapshot_kinds_for_date,
)
from src.engine.scalping.trailing_mechanical_policy import (
    CLASSIFIER_VERSION, SELECTED_SCHEMA, START_MARKETS, classifier_hash,
    market_values_hash, selected_policy_env, verify_forward_window,
)
from src.utils.constants import DATA_DIR

FAMILY = "scalp_trailing_mechanical_three_axis_selector"
REPORT_DIR = DATA_DIR / "report" / "monitor_snapshots"
POLICY_DIR = DATA_DIR / "report" / "scalp_trailing_mechanical_policy"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"scalp_trailing_mechanical_policy_{target_date}.json"


def _latest_manifest(target_date: str) -> Path | None:
    manifests = sorted((REPORT_DIR / "manifests").glob(
        "monitor_snapshot_manifest_*_postclose_exit.json"
    ))
    eligible = [path for path in manifests
                if path.name.split("_")[3] < target_date]
    return eligible[-1] if eligible else None


def _source(target_date: str) -> tuple[dict[str, Any], bytes, str, str]:
    manifest_path = _latest_manifest(target_date)
    if manifest_path is None:
        raise ValueError("postclose_exit_manifest_missing")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    source_date = str(manifest.get("target_date") or "")
    if (manifest.get("profile") != "postclose_exit"
            or date.fromisoformat(source_date).isoformat() != source_date
            or not "2026-06-05" <= source_date < target_date
            or (date.fromisoformat(target_date) - date.fromisoformat(source_date)).days > 7
            or set(manifest.get("snapshot_kinds") or [])
            != snapshot_kinds_for_date(source_date)):
        raise ValueError("postclose_exit_manifest_invalid")
    source_bytes = {}
    for kind in sorted(snapshot_kinds_for_date(source_date)):
        expected = REPORT_DIR / f"{kind}_{source_date}.json"
        recorded = (manifest.get("snapshot_paths") or {}).get(kind)
        if not isinstance(recorded, str) or Path(recorded).resolve() != expected.resolve():
            raise ValueError(f"postclose_exit_{kind}_path_mismatch")
        from src.engine.lifecycle.snapshot_archive import generation, read_bytes
        if generation(expected)['sha256'] != (manifest.get("snapshot_sha256") or {}).get(kind):
            raise ValueError(f"postclose_exit_{kind}_hash_mismatch")
        if kind == 'holding_exit_observation':
            source_bytes[kind] = read_bytes(expected, maximum=64*1024*1024)
    report_bytes = source_bytes["holding_exit_observation"]
    report = json.loads(report_bytes)
    if (report.get("date") != source_date
            or (report.get("meta") or {}).get("snapshot_profile") != "postclose_exit"):
        raise ValueError("postclose_exit_report_generation_mismatch")
    from .main_trailing_research_handoff import verify_extension
    verify_extension(report,target_date=target_date)
    return report, report_bytes, source_date, _sha(manifest_bytes)


def build_selection(target_date: str) -> dict[str, Any]:
    date.fromisoformat(target_date)
    result: dict[str, Any] = {
        "schema": SELECTED_SCHEMA, "family": FAMILY,
        "target_date": target_date, "allowed_runtime_apply": False,
        "runtime_effect": False, "status": "hold_source_gap",
        "runtime_env_overrides": {},
    }
    try:
        report, report_bytes, source_date, manifest_sha = _source(target_date)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result["reason"] = f"source:{type(exc).__name__}:{exc}"
        return result
    result.update(source_date=source_date, source_report_sha256=_sha(report_bytes),
                  source_manifest_sha256=manifest_sha)
    try:
        verify_forward_window(report, source_date)
    except ValueError as exc:
        result.update(status="hold_source_gap", reason=str(exc))
        return result
    research = report.get("trailing_mechanical_market_tuning") or {}
    candidate = research.get("research_candidate") or {}
    if (not (report.get("mechanical_population_quality") or {}).get("complete")
            or research.get("population_complete") is not True):
        result.update(status="hold_source_gap", reason="mechanical_population_incomplete")
        return result
    if (research.get("status") != "research_candidate_holdout_positive_review_required"
            or not candidate):
        result.update(status="hold_sample_or_edge", reason=research.get("status"))
        return result
    try:
        parent = build_manifest(target_date)["scalp_trailing_mechanical_policy_receipt"]
        values = candidate["values"]
        classifier_values = candidate["classifier_parameters"]
        digest = market_values_hash(values, classifier_values)
        if digest != candidate["market_values_sha256"]:
            raise ValueError("candidate_digest_mismatch")
        changed = [market for market in START_MARKETS
                   if (values[market] != parent["market_values"][market]
                       or classifier_values[market] != parent["classifier_parameters"][market])]
        if len(changed) != 1:
            raise ValueError("one_market_canary_required")
        evidence = research["joint_selection_evidence"]
        if (evidence.get("winner_sha256") != digest
                or evidence.get("tail_review_required") is not False
                or any(not isinstance(evidence.get(key), (int, float))
                       or evidence[key] <= 0 for key in (
                           "holdout_conservative_delta_krw",
                           "holdout_conservative_worst_slippage_delta_krw",
                           "holdout_worst_slippage_min_day_ev_pct",
                       ))):
            raise ValueError("candidate_economics_or_safety_invalid")
        policy = {
            **result,
            "status": "reviewed_one_stage_canary",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
            "apply_scope": "one_stage_canary",
            "changed_market": changed[0],
            "market_values": values,
            "classifier_parameters": classifier_values,
            "market_values_sha256": digest,
            "classifier_version": CLASSIFIER_VERSION,
            "classifier_sha256": classifier_hash(classifier_values),
            "candidate_grid_sha256": (research.get("classifier_policy_research") or {}).get(
                "grid_sha256") or research.get("grid_sha256"),
            "rollback_market_values_sha256": parent["market_values_sha256"],
            "selection_review": {
                "status": "reviewed_one_stage_canary",
                "candidate_sha256": digest,
                "source_quality": "pass",
                "execution_model": "pass",
                "same_stage_owner": "scalp_trailing_take_profit",
                "rollback_sha256": parent["market_values_sha256"],
            },
        }
        policy["runtime_env_overrides"] = selected_policy_env(
            policy, report, target_date=target_date,
            report_sha256=_sha(report_bytes),
        )
    except (KeyError, TypeError, ValueError) as exc:
        result.update(status="hold_selection_contract", reason=str(exc))
        return result
    return policy


def _write(path: Path, payload: dict[str, Any]) -> None:
    from src.engine.infrastructure.research_release_transition import journal_write
    raw=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
    if journal_write(path,raw):return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    selection = build_selection(args.target_date)
    if args.write:
        _write(policy_path(args.target_date), selection)
    print(json.dumps({"target_date": args.target_date,
                      "status": selection["status"],
                      "allowed_runtime_apply": selection["allowed_runtime_apply"],
                      "path": str(policy_path(args.target_date)) if args.write else None},
                     sort_keys=True))
    return 0


def _type_view(report, generation, *, report_path, market, kind):
    """Exact derived view for the existing selector's numeric canary contract.

    Source verification is mandatory before this helper. Research holds remain
    holds; CF, a different market and a holdout-reselected winner cannot enter.
    """
    from copy import deepcopy
    from src.engine.holding_exit_observation_report import _analysis_window_start
    from src.engine.automation.main_trailing_all_scope_research import _sealed
    research=report['trailing_situation_research']
    if market!=research.get('train_selected_market') or kind=='BASE':return None
    cell=research.get('cells',{}).get('actual_completed|'+market+'|'+kind)
    if (not cell or cell.get('disposition')!='research_candidate_requires_existing_selector_review'
        or cell.get('holdout_reselected') is not False
        or cell.get('operating_ai_type_input_compatible') is not True):return None
    manifest=_sealed(Path(report['input_manifest_path']))
    parent=manifest['approved_parent_receipt'];values=deepcopy(parent['market_values'])
    values[market]=cell['candidate_values'];config=parent['classifier_parameters']
    registered=manifest['candidates'][cell['train_selected_candidate']]
    if (registered.get('market_values',registered)!=values
        or registered.get('classifier_parameters',config)!=config
        or train_or_holdout_clock_invalid(cell)):
        raise ValueError('trailing_typed_candidate_registration_invalid')
    winner=market_values_hash(values,config);train,holdout=cell['train'],cell['holdout']
    if len(set(train['verified_days']+holdout['verified_days']))<7:return None
    _,window=_analysis_window_start(target_date=report['source_date'],month_start=None)
    from src.engine.lifecycle.holding_window_generation import capture_window
    dependency=capture_window(Path(manifest['source_data_root']),manifest['consumed_dates'])
    from src.engine.lifecycle import research_storage as storage
    def metrics(row):
        return dict(n=row['n'],paired_ev_pct=row['equal_weight_avg_profit_pct'],
            large_loss_worsened_ids=list(storage.iter_tree(Path(report.get('evidence_root',str(Path(report_path).parent))),row['large_loss_worsened_ids_ref'])),
            execution_slippage_sensitivity={'100':{'paired_ev_pct':row['worst_slippage_ev_pct']}})
    return dict(date=report['source_date'],meta={'snapshot_profile':'postclose_exit'},analysis_window=window,
        mechanical_population_quality=dict(complete=report['status']=='complete',start_entry_day=window['start_date'],
            policy_refresh_start_date=window['policy_refresh_start_date'],classifier_version=CLASSIFIER_VERSION),
        input_window_dependencies=dependency,situation_scope={'market':market,'situation_type':kind},
        situation_classifier_sha256=research['classifier']['classifier_sha256'],
        all_scope_type_source=dict(report_path=str(Path(report_path).resolve()),report_generation=generation),
        trailing_mechanical_market_tuning=dict(schema='scalp_trailing_mechanical_market_tuning_v2',population_complete=True,
            status='research_candidate_holdout_positive_review_required',train_days=train['verified_days'],
            holdout_days=holdout['verified_days'],grid_sha256=research['grid_sha256'],
            research_candidate=dict(values=values,classifier_parameters=config,market_values_sha256=winner,
                decision_authority='research_candidate_requires_policy_selection'),
            joint_three_market={winner:dict(values=values,train=metrics(train),holdout=metrics(holdout))},
            joint_selection_evidence=dict(winner_sha256=winner,tail_review_required=False,
                holdout_conservative_delta_krw=holdout['paired_delta_net_krw'],
                holdout_conservative_worst_slippage_delta_krw=holdout['worst_slippage_delta_net_krw'],
                holdout_worst_slippage_min_day_ev_pct=holdout['worst_slippage_min_day_ev_pct'])))


def verify_type_view(view, *, target_date):
    """Recompute a typed selector view from current sealed producer evidence."""
    from .main_trailing_research_handoff import verify_report
    reference=view['all_scope_type_source'];scope=view['situation_scope']
    report,generation=verify_report(reference['report_path'],target_date=target_date)
    expected=_type_view(report,generation,report_path=reference['report_path'],**dict(
        market=scope['market'],kind=scope['situation_type']))
    if generation!=reference['report_generation'] or expected!=view:
        raise ValueError('trailing_typed_selector_source_changed')


def select_typed_bundle(data_root,report, generation, *, report_path,target_date):
    """Publish source-bound type receipts using unchanged selector safeguards.

    This cannot alter a market-wide parent. Only the market fixed on training
    can receive typed overrides; unsupported cells retain exact parent values.
    """
    from src.engine.automation.main_trailing_all_scope_research import _sealed
    from src.engine.scalping.trailing_situation_policy import initial_bundle,TYPES
    root=Path(data_root).resolve();manifest=_sealed(Path(report['input_manifest_path']))
    parent=manifest['approved_parent_receipt'];research=report['trailing_situation_research']
    market=research.get('train_selected_market');overrides={}
    for kind in TYPES:
        view=_type_view(report,generation,report_path=report_path,market=market,kind=kind) if market else None
        if view is None:continue
        raw=(json.dumps(view,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
        sha=_sha(raw);candidate=view['trailing_mechanical_market_tuning']['research_candidate']
        winner=candidate['market_values_sha256']
        policy=dict(schema=SELECTED_SCHEMA,family=FAMILY,target_date=target_date,source_date=report['source_date'],
            source_report_sha256=sha,allowed_runtime_apply=True,runtime_effect=True,apply_scope='one_stage_canary',
            market_values=candidate['values'],classifier_parameters=candidate['classifier_parameters'],
            market_values_sha256=winner,classifier_version=CLASSIFIER_VERSION,
            classifier_sha256=classifier_hash(candidate['classifier_parameters']),
            rollback_market_values_sha256=parent['market_values_sha256'],
            selection_review=dict(status='reviewed_one_stage_canary',candidate_sha256=winner,
                source_quality='pass',execution_model='pass',same_stage_owner='scalp_trailing_take_profit',
                rollback_sha256=parent['market_values_sha256']))
        # Revalidates the producer-derived view, costs, all economic floors and
        # same-stage rollback. Never publish a failed positive canary.
        selected_policy_env(policy,view,target_date=target_date,report_sha256=sha)
        directory=root/'report/scalp_trailing_situation_selection'/target_date
        # Include source-view bytes: the same numeric winner on a new source
        # must not overwrite selector evidence used by an older policy.
        path=directory/f'{market}-{kind}-{sha}.report.json';policy_file=directory/f'{market}-{kind}-{sha}.policy.json'
        _write(path,view);_write(policy_file,policy)
        overrides[market+'|'+kind]=dict(evidence_kind='actual_completed_paired',parent_sha256=parent['market_values_sha256'],
            selector_evidence_reference=dict(report_path=str(path.relative_to(root)),report_byte_sha256=_sha(path.read_bytes()),
                policy_path=str(policy_file.relative_to(root)),policy_byte_sha256=_sha(policy_file.read_bytes())))
    return initial_bundle(parent['market_values'],parent_sha256=parent['market_values_sha256'],
        source_date=report['source_date'],target_date=target_date,parent_classifier_parameters=parent['classifier_parameters'],
        classifier=research.get('classifier'),overrides=overrides)


def train_or_holdout_clock_invalid(cell):
    return any(cell[split].get('completion_clock_verified') is not True for split in ('train','holdout'))


if __name__ == "__main__":
    raise SystemExit(main())
