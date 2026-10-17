"""Daily monitor snapshot and per-date log archive helpers."""

from __future__ import annotations

import gzip
import gc
import hashlib
import json
import os
import resource
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.utils.constants import DATA_DIR
from src.engine.dashboard_data_repository import (
    load_monitor_snapshot_file_first,
)

LOG_ARCHIVE_DIR = DATA_DIR / "log_archive"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
MONITOR_SNAPSHOT_MANIFEST_DIR = MONITOR_SNAPSHOT_DIR / "manifests"

LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def _env_float(name: str, default: float = 0.0) -> float:
    raw_value = str(os.getenv(name, "")).strip()
    if not raw_value:
        return default
    try:
        return max(0.0, float(raw_value))
    except Exception:
        return default


def _stage_io_delay_sec(base_delay: float, snapshot_kind: str) -> float:
    delay_map = {
        "performance_tuning": _env_float(
            "MONITOR_SNAPSHOT_PERFORMANCE_TUNING_IO_DELAY_SEC", base_delay
        ),
    }
    return delay_map.get(snapshot_kind, base_delay)


def _snapshot_path(kind: str, target_date: str) -> Path:
    safe_kind = str(kind or "").strip().lower().replace("-", "_")
    return MONITOR_SNAPSHOT_DIR / f"{safe_kind}_{target_date}.json"


def _snapshot_manifest_path(target_date: str, profile: str) -> Path:
    safe_profile = str(profile or "full").strip().lower().replace("-", "_")
    return (
        MONITOR_SNAPSHOT_MANIFEST_DIR
        / f"monitor_snapshot_manifest_{target_date}_{safe_profile}.json"
    )


def load_monitor_snapshot(kind: str, target_date: str) -> dict | None:
    """Load monitor snapshots from canonical JSON/GZip files only."""
    path = _snapshot_path(kind, target_date)
    if not path.exists() and Path(f"{path}.gz").exists():
        path = Path(f"{path}.gz")
    if path.exists():
        try:
            if path.suffix == ".gz":
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    return json.load(handle)
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            pass
    return load_monitor_snapshot_file_first(kind, target_date)


def save_monitor_snapshot(kind: str, target_date: str, payload: dict) -> Path:
    from src.engine.infrastructure.research_release_transition import journal_active
    if kind=='trade_review' and journal_active():
        raise ValueError('transition_trade_snapshot_regeneration_forbidden')
    if not isinstance(payload, dict):
        raise TypeError("monitor_snapshot_payload_must_be_object")
    # Finalization reads the bounded date header. JSON round trips can reorder
    # keys, so preserve the supplied date as the first key without inventing it.
    if 'date' in payload:
        payload = {'date': payload['date'],
                   **{key: value for key, value in payload.items() if key != 'date'}}
    if (kind == "trade_review" and isinstance(
        (payload.get("meta") or {}).get("completed_census_manifest"), dict
    )):
        from src.engine.sniper_trade_review_report import completed_census_manifest

        payload["meta"]["completed_census_manifest"] = (
            completed_census_manifest(payload)
        )
    path = _snapshot_path(kind, target_date)
    from src.engine.infrastructure.research_release_transition import journal_json
    if journal_json(path,payload,ensure_ascii=False,indent=2):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)
    if (kind == "trade_review"
        and (payload.get("meta") or {}).get("snapshot_profile") == "postclose_exit"
        and isinstance((payload.get("meta") or {}).get(
            "completed_census_manifest"), dict)
        and isinstance((payload.get("sections") or {}).get(
            "open_scalp_position_projection"), list)):
        _save_trade_review_completed_projection(path, payload)
    return path


def _save_trade_review_completed_projection(path: Path, payload: dict) -> Path:
    """Seal the small holding/exit input beside a potentially huge snapshot."""
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest

    target_date = str(payload.get("date") or "")
    issue = verify_completed_census_manifest(payload, target_date)
    if issue:
        raise ValueError(f"trade_review_completed_projection_invalid:{issue}")
    sections = payload.get("sections") or {}
    if not isinstance(sections.get("open_scalp_position_projection"), list):
        raise ValueError("trade_review_open_position_projection_missing")
    stat = path.stat()
    body = {
        "schema": "trade_review_completed_projection_sidecar_v1",
        "date": target_date,
        "code": payload.get("code"),
        "since": payload.get("since"),
        "meta": {key: (payload.get("meta") or {}).get(key) for key in (
            "warnings", "snapshot_profile", "completed_census_manifest",
            "sell_completed_event_ids", "completion_event_id_count",
            "trailing_event_source_receipts", "completed_census_input_sha256",
            "actual_cost_source_generation", "knowledge_cutoff",
        )},
        "metrics": {key: (payload.get("metrics") or {}).get(key) for key in (
            "canonical_completed_trades", "completed_trades",
            "open_scalp_position_projection_count",
            "open_scalp_position_projection_status",
        )},
        "sections": {key: sections[key] for key in (
            "completed_trade_projection", "open_scalp_position_projection")},
        "snapshot_identity": {
            "device": stat.st_dev, "inode": stat.st_ino, "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns,
        },
    }
    body["artifact_sha256"] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    destination = path.with_suffix(".completed_projection.json")
    fd, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp",
                                dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(body, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    # Dependency consumers need the sealed metadata, not another decode of
    # every timeline. This receipt is emitted by the verified projection
    # producer and bound to the independently verifiable exact file bytes.
    from src.engine.lifecycle.holding_window_generation import seal_dependency_receipt
    fact_projection = _save_trade_review_fact_projection(path, payload, body)
    seal_dependency_receipt(destination, body, fact_projection=fact_projection)
    return destination


def _save_trade_review_fact_projection(path: Path, payload: dict, completed: dict) -> Path | None:
    """Publish scalar facts from the complete producer census, without timelines."""
    from src.engine.lifecycle.holding_window_generation import MAX_PROJECTION_BYTES
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    rows = (payload.get('sections') or {}).get('strategy_position_fact_projection')
    if rows is None:
        return None  # Original legacy snapshots retain their original evidence.
    total = (payload.get('metrics') or {}).get('total_trades')
    if (payload.get('scope') != 'entered'
            or not isinstance(rows, list) or type(total) is not int or len(rows) != total
            or any(not isinstance(row, dict) or str(row.get('rec_date')) != payload['date'] for row in rows)
            or len({str(row.get('id') or '') for row in rows}) != total
            or any(not str(row.get('id') or '').isdigit() for row in rows)):
        raise ValueError('trade_review_fact_projection_census_invalid')
    fields = ('id', 'rec_date', 'code', 'position_tag', 'status', 'completion_observed_date',
              'terminal_population_scope', 'buy_price', 'buy_qty', 'buy_time', 'sell_price', 'sell_time',
              'strict_completion_status', 'broker_actual_cost_observed', 'broker_actual_fees_taxes_krw',
              'realized_pnl_krw_source', 'realized_pnl_krw', 'profit_rate', 'configured_fee_estimate_krw')
    completions = []
    for row in completed['sections']['completed_trade_projection']:
        projected = {key: row.get(key) for key in fields}
        if 'quantity_research_cost' in row:
            projected['quantity_research_cost'] = row['quantity_research_cost']
        # Presence is meaningful: a missing completion-day scale-in history
        # cannot be replaced with a synthetic zero from the entry-day display.
        projected.update({key: row[key] for key in ('add_count', 'avg_down_count', 'pyramid_count') if key in row})
        exit_signal = row.get('exit_signal')
        projected['exit_signal'] = ({key: exit_signal.get(key) for key in ('inferred', 'binding_status')}
                                    if isinstance(exit_signal, dict) else None)
        cost = row.get('actual_cost_reconciliation')
        projected['actual_cost_reconciliation'] = ({'status': cost.get('status')}
                                                  if isinstance(cost, dict) else None)
        completions.append(projected)
    body = dict(schema='trade_review_fact_projection_v1', date=payload['date'], source_scope='entered',
        snapshot_identity=completed['snapshot_identity'],
        meta={key: (payload.get('meta') or {}).get(key) for key in (
            'snapshot_profile', 'warnings', 'actual_cost_source_generation', 'completed_census_manifest')},
        metrics=dict(total_trades=total, canonical_completed_trades=len(completions)),
        sections=dict(recent_trades=rows, completed_trade_projection=completions))
    body['artifact_sha256'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                                                       ensure_ascii=False).encode()).hexdigest()
    if len(json.dumps(body, ensure_ascii=False).encode()) > MAX_PROJECTION_BYTES:
        raise ValueError('trade_review_fact_projection_partition_required')
    destination = path.with_suffix('.fact_projection.json')
    _atomic(destination, body)
    return destination


def save_monitor_snapshot_manifest(
    target_date: str, *, profile: str, snapshots: dict[str, str], verified_prefix: dict | None = None,
    _publication_path: Path | None = None,
) -> Path:
    canonical_path = _snapshot_manifest_path(target_date, profile)
    manifest_path = Path(_publication_path) if _publication_path is not None else canonical_path
    if _publication_path is not None and (verified_prefix is None or manifest_path.parent!=canonical_path.parent):
        raise ValueError('postclose_exit_manifest_publication_path_invalid')
    tracked_paths = {
        key: value
        for key, value in (snapshots or {}).items()
        if isinstance(value, str) and value.startswith("/")
    }
    payload = {
        "target_date": target_date,
        "profile": str(profile or "full"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_kinds": sorted(tracked_paths.keys()),
        "snapshot_paths": tracked_paths,
        "snapshot_sha256": {
            key: (verified_prefix['snapshot_sha256'][key]
                  if verified_prefix is not None and key in POSTCLOSE_PREFIX_KINDS
                  else _sha256_file(Path(path)))
            for key, path in tracked_paths.items()
        },
    }
    if verified_prefix is not None:
        if (profile!='postclose_exit' or set(tracked_paths)!=POSTCLOSE_PREFIX_KINDS|{'holding_exit_observation'}
                or any(tracked_paths[key]!=verified_prefix['snapshot_paths'][key] for key in POSTCLOSE_PREFIX_KINDS)):
            raise ValueError('postclose_exit_prefix_handoff_invalid')
        payload['postclose_phase']='holding_suffix'
        payload['completion_prefix_manifest_sha256']=verified_prefix['artifact_sha256']
    if profile == "postclose_exit" and target_date >= "2026-09-28":
        from src.engine.lifecycle.broker_cost_reconciliation import source_generation
        payload["actual_cost_source_generation"] = source_generation(DATA_DIR, target_date)
        if verified_prefix is not None:
            projected_costs=verified_prefix['actual_cost_source_generation']
        else:
            from src.engine.holding_exit_observation_report import _verified_trade_review_projection
            trade_path = Path(tracked_paths.get("trade_review", ""))
            projection = _verified_trade_review_projection(trade_path, target_date, data_root=DATA_DIR,metadata_only=True)
            if projection is None:
                raise ValueError("postclose_exit_trade_projection_generation_invalid")
            projected_costs = (projection.get("meta") or {}).get("actual_cost_source_generation")
        if (projected_costs != payload["actual_cost_source_generation"]
                and (projected_costs is not None or payload["actual_cost_source_generation"]["count"]
                     or payload["actual_cost_source_generation"].get("official_source_sha256"))):
            raise ValueError("postclose_exit_actual_cost_generation_changed")
        holding_path = Path(tracked_paths.get("holding_exit_observation", ""))
        from src.engine.lifecycle.snapshot_archive import read_bytes
        holding = json.loads(read_bytes(holding_path, maximum=64 * 1024 * 1024))
        from src.engine.lifecycle.holding_window_generation import verify_window
        window = holding.get("input_window_dependencies")
        verify_window(DATA_DIR, window)
        if holding.get("input_window_generation_sha256") != window["input_window_generation_sha256"]:
            raise ValueError("window_dependency_report_binding_invalid")
        payload["input_window_dependencies"] = window
        payload["input_window_generation_sha256"] = window["input_window_generation_sha256"]
        holding_costs = (holding.get("actual_cost_source_generations") or {}).get(target_date)
        if (holding_costs != payload["actual_cost_source_generation"]
                and (holding_costs is not None or payload["actual_cost_source_generation"]["count"]
                     or payload["actual_cost_source_generation"].get("official_source_sha256"))):
            raise ValueError("postclose_exit_holding_cost_generation_changed")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    from src.engine.infrastructure.research_release_transition import journal_json
    if journal_json(manifest_path,payload,ensure_ascii=False,indent=2):
        return manifest_path
    fd, name = tempfile.mkstemp(prefix=f".{manifest_path.name}.", suffix=".tmp", dir=manifest_path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, manifest_path)
    finally:
        temporary.unlink(missing_ok=True)
    return manifest_path


def _sha256_file(path: Path) -> str:
    if path.parent.name == 'monitor_snapshots' and path.suffix == '.json':
        from src.engine.lifecycle.snapshot_archive import generation
        return generation(path)['sha256']
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


POSTCLOSE_PREFIX_KINDS=frozenset({'trade_review','post_sell_feedback','missed_entry_counterfactual'})


def _postclose_pipeline_guard(data_root, day):
    """Seal raw partition identity without rescanning the multi-gigabyte source.

    This is deliberately a physical generation seal between the two phases.
    Archiving a raw partition during that interval requires a new prefix;
    archive receipts alone do not prove the prefix consumed that generation.
    """
    from src.engine.lifecycle.holding_window_generation import source_stat
    directory = Path(data_root) / 'pipeline_events'
    generations = {}
    for suffix in ('.jsonl', '.late.jsonl'):
        logical = directory / f'pipeline_events_{day}{suffix}'
        for path in (logical, Path(str(logical) + '.gz'),
                     Path(str(logical) + '.archive_receipt.json'),
                     Path(str(logical) + '.gz.archive_receipt.json')):
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise ValueError('postclose_exit_prefix_path_invalid')
            generations[path.name] = list(source_stat(path.stat())) if path.exists() else None
    return {'schema': 'postclose_prefix_raw_generation_v1', 'partitions': generations}


def _postclose_prefix_guard(data_root,day,manifest_path=None):
    from src.engine.lifecycle.holding_window_generation import source_stat
    directory=Path(data_root)/'report/monitor_snapshots'
    paths=[]
    for name in (*sorted(POSTCLOSE_PREFIX_KINDS),'trade_review.completed_projection','trade_review.fact_projection'):
        logical=(directory/f'{name}_{day}.json' if '.completed_projection' not in name and '.fact_projection' not in name
                 else directory/f'trade_review_{day}.{name.split(".",1)[1]}.json')
        paths.extend((logical,Path(str(logical)+'.gz'),Path(str(logical)+'.gz.archive_receipt.json')))
    paths.append(directory/f'trade_review_{day}.completed_projection.json.dependencies.json')
    if manifest_path is not None:paths.append(Path(manifest_path))
    result={}
    for path in paths:
        if path.is_symlink():raise ValueError('postclose_exit_prefix_path_invalid')
        result[str(path)]=source_stat(path.stat()) if path.exists() else None
    result['raw_pipeline_generation'] = _postclose_pipeline_guard(data_root, day)
    return result


def _postclose_prefix_native_proof(data_root,day):
    from src.engine.lifecycle.holding_window_generation import _capture_day,MAX_METADATA_BYTES
    from src.engine.lifecycle.snapshot_archive import generation,read_bytes
    native=_capture_day(Path(data_root),Path(data_root)/'report/monitor_snapshots',day)
    if native.get('profile')!='postclose_exit' or native.get('status') not in {'observed','valid_empty'}:
        raise ValueError('postclose_exit_prefix_trade_source_invalid')
    sidecar=Path(data_root)/'report/monitor_snapshots'/f'trade_review_{day}.completed_projection.json'
    raw=read_bytes(Path(str(sidecar)+'.dependencies.json'),maximum=MAX_METADATA_BYTES)
    dependency=json.loads(raw)
    bound=native['projection']['dependency_receipt']
    if len(raw)!=bound['size'] or hashlib.sha256(raw).hexdigest()!=bound['sha256']:
        raise ValueError('postclose_exit_prefix_dependency_changed')
    fact=generation(sidecar.with_name(f'trade_review_{day}.fact_projection.json'))
    if dependency.get('fact_projection')!=fact:
        raise ValueError('postclose_exit_prefix_fact_projection_unsealed')
    return dict(native_trade_generation=native,fact_projection=fact)


def save_postclose_exit_prefix_manifest(target_date,*,snapshots,raw_pipeline_generation):
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    if set(snapshots)!=POSTCLOSE_PREFIX_KINDS:
        raise ValueError('postclose_exit_prefix_population_invalid')
    before=_postclose_prefix_guard(DATA_DIR,target_date)
    if before['raw_pipeline_generation'] != raw_pipeline_generation:
        raise ValueError('postclose_exit_prefix_pipeline_changed_during_build')
    proof=_postclose_prefix_native_proof(DATA_DIR,target_date)
    payload=dict(schema='monitor_snapshot_completion_prefix_v1',target_date=target_date,
        profile='postclose_exit',postclose_phase='completion_prefix',
        completion_scope='completion_prefix_only',runtime_effect=False,
        generated_at=datetime.now().isoformat(),snapshot_kinds=sorted(snapshots),
        snapshot_paths=dict(snapshots),snapshot_sha256={key:_sha256_file(Path(value)) for key,value in snapshots.items()},
        actual_cost_source_generation=proof['native_trade_generation']['cost_generation'],
        raw_pipeline_generation=raw_pipeline_generation,
        native_source_proof=proof)
    if _postclose_prefix_guard(DATA_DIR,target_date)!=before:
        raise ValueError('postclose_exit_prefix_changed_during_publication')
    payload['artifact_sha256']=digest(payload)
    path=_snapshot_manifest_path(target_date,'postclose_exit_completion_prefix')
    _atomic(path,payload)
    return path


def _read_verified_postclose_exit_prefix(target_date,*,data_root):
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    from src.engine.monitor_snapshot_runtime import _read_phase_manifest_bytes
    directory=Path(data_root)/'report/monitor_snapshots'
    path=directory/'manifests'/f'monitor_snapshot_manifest_{target_date}_postclose_exit_completion_prefix.json'
    before=_postclose_prefix_guard(data_root,target_date,path)
    raw=_read_phase_manifest_bytes(path,limit=MAX_METADATA_BYTES)
    body=json.loads(raw)
    if (not isinstance(body,dict) or body.get('schema')!='monitor_snapshot_completion_prefix_v1'
            or body.get('target_date')!=target_date or body.get('profile')!='postclose_exit'
            or body.get('postclose_phase')!='completion_prefix' or body.get('completion_scope')!='completion_prefix_only'
            or body.get('runtime_effect') is not False
            or body.get('artifact_sha256')!=digest({key:value for key,value in body.items() if key!='artifact_sha256'})
            or set(body.get('snapshot_kinds') or [])!=POSTCLOSE_PREFIX_KINDS
            or set(body.get('snapshot_paths') or {})!=POSTCLOSE_PREFIX_KINDS
            or set(body.get('snapshot_sha256') or {})!=POSTCLOSE_PREFIX_KINDS):
        raise ValueError('postclose_exit_prefix_manifest_invalid')
    if body.get('raw_pipeline_generation') != before['raw_pipeline_generation']:
        raise ValueError('postclose_exit_prefix_pipeline_generation_changed')
    for kind in POSTCLOSE_PREFIX_KINDS:
        source=directory/f'{kind}_{target_date}.json'
        if Path(body['snapshot_paths'][kind]).resolve()!=source.resolve() or _sha256_file(source)!=body['snapshot_sha256'][kind]:
            raise ValueError('postclose_exit_prefix_generation_changed')
    proof=_postclose_prefix_native_proof(data_root,target_date)
    if body.get('native_source_proof')!=proof or body.get('actual_cost_source_generation')!=proof['native_trade_generation']['cost_generation']:
        raise ValueError('postclose_exit_prefix_native_generation_changed')
    if _postclose_prefix_guard(data_root,target_date,path)!=before:
        raise ValueError('postclose_exit_prefix_changed_during_validation')
    return path,body,before


def verified_postclose_exit_prefix_manifest(target_date: str,*,data_root:Path=DATA_DIR)->Path|None:
    """Verify only the completion prefix; never claim holding or full closure."""
    try:return _read_verified_postclose_exit_prefix(target_date,data_root=data_root)[0]
    except (OSError,ValueError,TypeError,KeyError,AttributeError):return None


def _verified_postclose_exit_snapshot_manifest(
    target_date: str, *, data_root: Path = DATA_DIR,
    expected_raw_pipeline_generation: dict | None = None,
    manifest_path: Path | None = None,
) -> Path | None:
    """Reuse only a sealed exact-date snapshot whose raw pipeline has not advanced."""
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection

    directory = Path(data_root) / "report" / "monitor_snapshots"
    manifest_path = (Path(manifest_path) if manifest_path is not None else
                     directory / "manifests" / f"monitor_snapshot_manifest_{target_date}_postclose_exit.json")
    expected = {"trade_review", "post_sell_feedback", "missed_entry_counterfactual",
                "holding_exit_observation"}
    try:
        from src.engine.lifecycle.holding_window_generation import MAX_PROJECTION_BYTES,source_stat
        manifest_before=source_stat(manifest_path.stat())
        if manifest_path.is_symlink() or manifest_before[2]>MAX_PROJECTION_BYTES:
            return None
        with manifest_path.open('rb') as handle:
            raw=handle.read(MAX_PROJECTION_BYTES+1)
        if len(raw)>MAX_PROJECTION_BYTES or source_stat(manifest_path.stat())!=manifest_before:
            return None
        manifest = json.loads(raw)
        if not isinstance(manifest,dict):
            return None
        # The physical seal protects this validation/publication interval.
        # It is not retained as a future startup gate: closed raw partitions
        # may subsequently move through the existing lossless archive flow.
        raw_guard=_postclose_pipeline_guard(data_root,target_date)
        if expected_raw_pipeline_generation is not None and raw_guard!=expected_raw_pipeline_generation:
            return None
        from src.engine.lifecycle.broker_cost_reconciliation import source_generation
        costs = source_generation(data_root, target_date)
        if (manifest.get("actual_cost_source_generation") != costs
                and (costs["count"] or costs.get("official_source_sha256") or manifest.get("actual_cost_source_generation") is not None)):
            return None
        if (manifest.get("target_date") != target_date
            or manifest.get("profile") != "postclose_exit"
            or set(manifest.get("snapshot_kinds") or []) != expected):
            return None
        pipeline = Path(data_root) / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
        if pipeline.exists() and pipeline.stat().st_mtime > manifest_path.stat().st_mtime:
            return None
        for kind in expected:
            path = directory / f"{kind}_{target_date}.json"
            if Path((manifest.get("snapshot_paths") or {}).get(kind, "")).resolve() != path.resolve():
                return None
            if _sha256_file(path) != (manifest.get("snapshot_sha256") or {}).get(kind):
                return None
        projection = _verified_trade_review_projection(
            directory / f"trade_review_{target_date}.json", target_date, data_root=Path(data_root),metadata_only=True)
        if projection is None:
            return None
        recorded_costs = (projection.get("meta") or {}).get("actual_cost_source_generation")
        if recorded_costs != costs and (costs["count"] or costs.get("official_source_sha256") or recorded_costs is not None):
            return None
        holding_path = directory / f"holding_exit_observation_{target_date}.json"
        from src.engine.lifecycle.snapshot_archive import read_bytes
        holding = json.loads(read_bytes(holding_path, maximum=64 * 1024 * 1024))
        from src.engine.lifecycle.holding_window_generation import verify_window
        window = holding.get("input_window_dependencies")
        verify_window(data_root, window)
        if (manifest.get("input_window_dependencies") != window
            or manifest.get("input_window_generation_sha256") != window["input_window_generation_sha256"]
            or holding.get("input_window_generation_sha256") != window["input_window_generation_sha256"]):
            return None
        if (holding.get("date") != target_date
            or (holding.get("meta") or {}).get("snapshot_profile") != "postclose_exit"):
            return None
        if target_date >= '2026-10-12':
            from src.engine.scalping.holding_vote_experiment import code_sha
            numeric = (holding.get('holding_path_vote_replay') or {}).get('vote_numeric_research') or {}
            if (numeric.get('status') == 'incumbent_unverified'
                    or numeric.get('code_sha256') != code_sha()):
                return None
        holding_costs = (holding.get("actual_cost_source_generations") or {}).get(target_date)
        if holding_costs != costs and (holding_costs is not None or costs["count"] or costs.get("official_source_sha256")):
            return None
        if source_generation(data_root, target_date) != costs:
            return None
        if (source_stat(manifest_path.stat())!=manifest_before
                or _postclose_pipeline_guard(data_root,target_date)!=raw_guard):
            return None
        return manifest_path
    except (OSError, ValueError, TypeError, KeyError):
        return None


def verified_postclose_exit_snapshot_manifest(target_date: str, *, data_root: Path = DATA_DIR) -> Path | None:
    """Verify the published canonical generation, never an unpublished candidate."""
    return _verified_postclose_exit_snapshot_manifest(target_date,data_root=data_root)


def archived_log_path(log_path: Path, target_date: str) -> Path:
    return LOG_ARCHIVE_DIR / str(target_date) / f"{log_path.name}.gz"


def _iter_raw_candidate_paths(log_path: Path) -> list[Path]:
    candidates = [log_path]
    candidates.extend(
        sorted(
            [
                path
                for path in log_path.parent.glob(f"{log_path.name}.*")
                if path.suffix != ".gz"
            ],
            key=lambda path: path.name,
        )
    )
    return candidates


def _read_matching_lines(
    path: Path, *, target_date: str, marker: str | None = None
) -> list[str]:
    if not path.exists() or not path.is_file():
        return []

    opener = gzip.open if path.suffix == ".gz" else open
    lines: list[str] = []
    with opener(path, "rt", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            if f"[{target_date}" not in raw_line:
                continue
            if marker and marker not in raw_line:
                continue
            lines.append(raw_line.strip())
    return lines


def iter_target_log_lines(
    log_paths: Iterable[Path],
    *,
    target_date: str,
    marker: str | None = None,
) -> list[str]:
    lines: list[str] = []
    for log_path in log_paths:
        raw_lines: list[str] = []
        for candidate in _iter_raw_candidate_paths(log_path):
            raw_lines.extend(
                _read_matching_lines(candidate, target_date=target_date, marker=marker)
            )
        if raw_lines:
            lines.extend(raw_lines)
            continue
        archive_path = archived_log_path(log_path, target_date)
        lines.extend(
            _read_matching_lines(archive_path, target_date=target_date, marker=marker)
        )
    return lines


def archive_target_date_logs(target_date: str, log_paths: Iterable[Path]) -> list[dict]:
    archived: list[dict] = []
    for log_path in log_paths:
        lines: list[str] = []
        for candidate in _iter_raw_candidate_paths(log_path):
            lines.extend(_read_matching_lines(candidate, target_date=target_date))
        if not lines:
            continue

        archive_path = archived_log_path(log_path, target_date)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(lines).strip()
        if payload:
            payload = f"{payload}\n"
        with gzip.open(archive_path, "wt", encoding="utf-8") as handle:
            handle.write(payload)
        archived.append(
            {
                "log_name": log_path.name,
                "path": str(archive_path),
                "line_count": len(lines),
                "archived_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": (
                    archive_path.stat().st_size if archive_path.exists() else 0
                ),
            }
        )
    return archived


def save_monitor_snapshots_for_date(target_date: str) -> dict[str, str]:
    return save_monitor_snapshots_for_date_with_profile(
        target_date,
        profile="full",
        io_delay_sec=0.0,
    )


def save_monitor_snapshots_for_date_with_profile(
    target_date: str,
    *,
    profile: str = "full",
    io_delay_sec: float = 0.0,
    postclose_phase: str = 'all',
) -> dict[str, str]:
    from src.engine.buy_pause_guard import evaluate_buy_pause_guard
    from src.engine.holding_exit_observation_report import (
        build_holding_exit_observation_report,
    )
    from src.engine.sniper_missed_entry_counterfactual import (
        build_missed_entry_counterfactual_report,
    )
    from src.engine.sniper_performance_tuning_report import (
        build_performance_tuning_report,
    )
    from src.engine.sniper_post_sell_feedback import build_post_sell_feedback_report
    from src.engine.sniper_trade_review_report import build_trade_review_report
    from src.engine.wait6579_ev_cohort_report import build_wait6579_ev_cohort_report

    normalized_profile = str(profile or "full").strip().lower()
    if normalized_profile not in {"full", "intraday_light", "postclose_exit"}:
        raise ValueError(f"Unsupported monitor snapshot profile: {profile}")
    if postclose_phase not in {'all','completion_prefix','holding_suffix'} or (normalized_profile!='postclose_exit' and postclose_phase!='all'):
        raise ValueError('postclose_exit_snapshot_phase_invalid')
    prefix_body=prefix_guard=prefix_manifest=None
    if postclose_phase=='holding_suffix':
        prefix_manifest,prefix_body,prefix_guard=_read_verified_postclose_exit_prefix(target_date,data_root=DATA_DIR)
    pipeline_before=None
    if postclose_phase=='completion_prefix':
        pipeline_before=_postclose_pipeline_guard(DATA_DIR,target_date)
    sleep_sec = max(0.0, float(io_delay_sec))
    trend_env_name = (
        "MONITOR_SNAPSHOT_INTRADAY_TREND_MAX_DATES"
        if normalized_profile == "intraday_light"
        else "MONITOR_SNAPSHOT_FULL_TREND_MAX_DATES"
    )
    trend_max_dates = None
    trend_env_value = os.getenv(trend_env_name, "").strip()
    if trend_env_value:
        try:
            trend_max_dates = int(trend_env_value)
        except Exception:
            trend_max_dates = None
    snapshot_order = (
        (
            "trade_review",
            lambda: build_trade_review_report(
                target_date=target_date,
                since_time=None,
                top_n=300,
                scope="entered",
                write_research_costs=normalized_profile == 'postclose_exit',
            ),
        ),
        (
            "performance_tuning",
            lambda: build_performance_tuning_report(
                target_date=target_date,
                since_time=None,
                trend_max_dates=trend_max_dates,
            ),
        ),
        (
            "wait6579_ev_cohort",
            lambda: build_wait6579_ev_cohort_report(
                target_date=target_date,
            ),
        ),
        (
            "post_sell_feedback",
            lambda: build_post_sell_feedback_report(
                target_date=target_date,
                evaluate_now=True,
            ),
        ),
        (
            "missed_entry_counterfactual",
            lambda: build_missed_entry_counterfactual_report(
                target_date=target_date,
            ),
        ),
        (
            "holding_exit_observation",
            lambda: build_holding_exit_observation_report(
                target_date=target_date,
                all_scope_research=normalized_profile == 'postclose_exit',
            ),
        ),
    )
    allowed_by_profile = {
        "full": {
            "trade_review",
            "performance_tuning",
            "wait6579_ev_cohort",
            "post_sell_feedback",
            "missed_entry_counterfactual",
            "holding_exit_observation",
        },
        "intraday_light": {
            "trade_review",
            "performance_tuning",
            "wait6579_ev_cohort",
        },
        "postclose_exit": {
            "trade_review",
            "post_sell_feedback",
            "missed_entry_counterfactual",
            "holding_exit_observation",
        },
    }

    send_alert = normalized_profile == "full"
    buy_pause_guard = evaluate_buy_pause_guard(target_date, send_alert=send_alert)
    result: dict[str, str] = {
        "profile": normalized_profile,
        "io_delay_sec": f"{sleep_sec:.3f}",
    }
    if postclose_phase!='all':
        result['postclose_phase']=postclose_phase
        result['completion_scope']='completion_prefix_only' if postclose_phase=='completion_prefix' else 'full_postclose_snapshot'
    if prefix_body is not None:
        result.update(prefix_body['snapshot_paths'])
    result["io_delay_sec_per_stage"] = json.dumps(
        {
            "default": f"{sleep_sec:.3f}",
            "performance_tuning": f"{_stage_io_delay_sec(sleep_sec, 'performance_tuning'):.3f}",
        }
    )
    if trend_max_dates is not None:
        result["trend_max_dates"] = str(trend_max_dates)

    selected_kinds = allowed_by_profile[normalized_profile]
    if postclose_phase=='completion_prefix':selected_kinds=POSTCLOSE_PREFIX_KINDS
    elif postclose_phase=='holding_suffix':selected_kinds={'holding_exit_observation'}
    selected_entries = [item for item in snapshot_order if item[0] in selected_kinds]
    stage_metrics: dict[str, dict] = {}
    for idx, (snapshot_kind, build_fn) in enumerate(selected_entries):
        stage_delay = _stage_io_delay_sec(sleep_sec, snapshot_kind)
        if idx > 0 and stage_delay > 0:
            time.sleep(stage_delay)
        stage_started_at = time.monotonic()
        print(
            json.dumps(
                {
                    "event": "monitor_snapshot_stage_start",
                    "target_date": target_date,
                    "profile": normalized_profile,
                    "snapshot_kind": snapshot_kind,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        payload = build_fn()
        payload.setdefault("meta", {})
        payload["meta"]["saved_snapshot_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        payload["meta"]["snapshot_kind"] = snapshot_kind
        payload["meta"]["snapshot_profile"] = normalized_profile
        payload["meta"]["buy_pause_guard"] = buy_pause_guard
        result[snapshot_kind] = str(
            save_monitor_snapshot(snapshot_kind, target_date, payload)
        )
        stage_metrics[snapshot_kind] = {
            "duration_sec": round(time.monotonic() - stage_started_at, 3),
            "process_max_rss_kb": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        }
        print(
            json.dumps(
                {
                    "event": "monitor_snapshot_stage_complete",
                    "target_date": target_date,
                    "profile": normalized_profile,
                    "snapshot_kind": snapshot_kind,
                    **stage_metrics[snapshot_kind],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        del payload
        gc.collect()
    result["stage_metrics"] = json.dumps(stage_metrics, sort_keys=True)

    def _finalize_snapshot_manifest() -> dict[str, str]:
        if postclose_phase=='completion_prefix':
            manifest=save_postclose_exit_prefix_manifest(target_date,
                snapshots={key:result[key] for key in POSTCLOSE_PREFIX_KINDS},
                raw_pipeline_generation=pipeline_before)
            result['snapshot_manifest']=str(manifest)
            return result
        if prefix_guard is not None and _postclose_prefix_guard(DATA_DIR,target_date,prefix_manifest)!=prefix_guard:
            raise ValueError('postclose_exit_prefix_changed_during_holding_build')
        candidate=None
        if postclose_phase=='holding_suffix':
            canonical=_snapshot_manifest_path(target_date,normalized_profile)
            canonical.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(prefix=f'.{canonical.name}.holding_suffix.',suffix='.candidate.json',dir=canonical.parent)
            os.close(fd)
            candidate=Path(name)
        manifest_path = save_monitor_snapshot_manifest(
            target_date,
            profile=normalized_profile,
            snapshots=result,
            **({'verified_prefix':prefix_body} if prefix_body is not None else {}),
            **({'_publication_path':candidate} if candidate is not None else {}),
        )
        if postclose_phase=='holding_suffix':
            if _verified_postclose_exit_snapshot_manifest(target_date,data_root=DATA_DIR,
                    expected_raw_pipeline_generation=prefix_body['raw_pipeline_generation'],manifest_path=manifest_path)!=manifest_path:
                raise ValueError('postclose_exit_holding_suffix_full_generation_invalid')
            if _postclose_prefix_guard(DATA_DIR,target_date,prefix_manifest)!=prefix_guard:
                raise ValueError('postclose_exit_prefix_changed_during_holding_publication')
            # Preserve a failed candidate and the previous canonical bytes.
            # Only a native verified four-kind generation becomes visible.
            os.replace(manifest_path,canonical)
            manifest_path=canonical
            result['full_snapshot_native_verified']=True
        result["snapshot_manifest"] = str(manifest_path)
        return result

    return _finalize_snapshot_manifest()
