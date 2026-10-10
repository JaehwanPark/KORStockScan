"""Content-bound dependencies of a cumulative Main holding report.

This lifecycle contract seals input generations, including missing dates. It
does not allocate costs or acquire policy/order authority. A legacy report
without the consumed window cannot be made current by resealing its bytes.
"""
from __future__ import annotations

from datetime import date, timedelta
from contextlib import ExitStack
import gzip
import hashlib
import json
import io
from pathlib import Path

from .broker_cost_reconciliation import digest, source_generation

SCHEMA = "holding_input_window_generation_v1"
MAX_DATES = 370
MAX_PROJECTION_BYTES = 4 * 1024 * 1024
MAX_METADATA_BYTES = 512 * 1024


def source_stat(stat):
    """Access time changes when this verifier reads; it is not source mutation."""
    return tuple(getattr(stat, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def byte_generation(path):
    """Independent byte verification, with a constant 64 KiB read buffer."""
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('window_dependency_path_invalid')
    before = path.stat()
    sha = hashlib.sha256()
    size = 0
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(64 * 1024), b''):
            size += len(block)
            sha.update(block)
    if source_stat(path.stat()) != source_stat(before) or size != before.st_size:
        raise ValueError('window_dependency_changed_during_read')
    return {'path': path.name, 'size': size, 'sha256': sha.hexdigest()}


def seal_dependency_receipt(sidecar, payload):
    """Only the existing, census-verified projection writer calls this."""
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    if verify_completed_census_manifest(payload, payload['date']) is not None:
        raise ValueError('window_dependency_census_invalid')
    body = {'schema':'holding_projection_dependency_receipt_v1', 'date':payload['date'],
            'projection':byte_generation(sidecar), 'snapshot_identity':payload['snapshot_identity'],
            'census_sha256':digest(payload['meta']['completed_census_manifest']),
            'meta':{k:payload['meta'].get(k) for k in (
                'actual_cost_source_generation', 'knowledge_cutoff', 'snapshot_profile')},
            'completed_count':len(payload['sections']['completed_trade_projection'])}
    body['artifact_sha256'] = digest(body)
    if len(json.dumps(body).encode()) > MAX_METADATA_BYTES:
        raise ValueError('window_dependency_metadata_budget_exceeded')
    _atomic(Path(str(sidecar) + '.dependencies.json'), body)


def _file_generation(path: Path) -> dict:
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("window_dependency_path_invalid")
    before = path.stat()
    if before.st_size > MAX_PROJECTION_BYTES:
        raise ValueError("window_dependency_projection_unbounded")
    with path.open("rb") as handle:
        raw = handle.read(MAX_PROJECTION_BYTES + 1)
    after = path.stat()
    if len(raw) > MAX_PROJECTION_BYTES or source_stat(before) != source_stat(after):
        raise ValueError("window_dependency_changed_during_read")
    return {"path": path.name, "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}, raw


def _capture_day(root, directory, day):
    with ExitStack() as budget:
        return _capture_day_inputs(root, directory, day, budget)


def _capture_day_inputs(root, directory, day, budget):
    from .research_input_budget import Claim
    def decode(content):
        budget.enter_context(Claim(len(content) * 8))
        return json.loads(content)
    raw = directory / f"trade_review_{day}.json"
    compressed = Path(str(raw) + ".gz")
    sidecar = raw.with_suffix(".completed_projection.json")
    # The bounded sidecar is authoritative only with its original snapshot
    # identity. Preserve that binding as well as the sidecar's bytes.
    if raw.is_file() and sidecar.is_file():
        receipt = Path(str(sidecar) + '.dependencies.json')
        if receipt.is_file():
            if receipt.stat().st_size > MAX_METADATA_BYTES:
                raise ValueError('window_dependency_metadata_budget_exceeded')
            receipt_generation, content = _file_generation(receipt)
            metadata = decode(content)
            generation = byte_generation(sidecar)
            if (metadata.get('schema') != 'holding_projection_dependency_receipt_v1'
                    or metadata.get('date') != day or metadata.get('projection') != generation
                    or metadata.get('artifact_sha256') != digest({k:v for k,v in metadata.items() if k != 'artifact_sha256'})
                    or type(metadata.get('completed_count')) is not int or metadata['completed_count'] < 0):
                raise ValueError('window_dependency_receipt_invalid')
            generation['dependency_receipt'] = receipt_generation
            value = metadata
        else:
            # Legacy projections remain verifiable when small. Large historical
            # files require the existing producer's receipt, not an unbounded
            # JSON decode or a fabricated validation marker.
            if sidecar.stat().st_size > MAX_PROJECTION_BYTES:
                raise ValueError('window_dependency_legacy_metadata_required')
            generation, content = _file_generation(sidecar)
            value = decode(content)
        stat = raw.stat()
        identity = {"device": stat.st_dev, "inode": stat.st_ino,
                    "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                    "ctime_ns": stat.st_ctime_ns}
        if raw.is_symlink() or value.get("snapshot_identity") != identity:
            raise ValueError("window_dependency_snapshot_binding_invalid")
        generation["snapshot_identity"] = identity
        if not receipt.is_file():
            from src.engine.sniper_trade_review_report import verify_completed_census_manifest
            payload = {k: v for k, v in value.items() if k != 'artifact_sha256'}
            expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                                ensure_ascii=False).encode()).hexdigest()
            if (value.get('schema') != 'trade_review_completed_projection_sidecar_v1'
                    or expected != value.get('artifact_sha256')
                    or verify_completed_census_manifest(value, day) is not None):
                raise ValueError('window_dependency_projection_contract_invalid')
    elif raw.is_file() or compressed.is_file():
        path = raw if raw.is_file() else compressed
        generation, content = _file_generation(path)
        if path.suffix == '.gz':
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as handle:
                content = handle.read(MAX_PROJECTION_BYTES + 1)
        if len(content) > MAX_PROJECTION_BYTES:
            raise ValueError("window_dependency_decoded_projection_unbounded")
        value = decode(content)
    else:
        generation, value = None, None
    costs = source_generation(root, day)
    status = "missing"
    census = None
    cutoff = None
    profile = None
    if value is not None:
        if value.get("date") != day:
            raise ValueError("window_dependency_snapshot_date_invalid")
        meta = value.get("meta") or {}
        recorded = meta.get("actual_cost_source_generation")
        if recorded != costs and (recorded is not None or costs["count"]
                                  or costs.get("official_source_sha256")):
            raise ValueError("window_dependency_cost_generation_changed:" + day)
        census = meta.get("completed_census_manifest")
        cutoff = meta.get("knowledge_cutoff")
        profile = meta.get("snapshot_profile")
        census_sha = value.get('census_sha256') or (digest(census) if census else None)
        status = "observed" if (value.get('completed_count', 0) > 0 or (value.get("sections") or {}).get(
            "completed_trade_projection")) else "valid_empty" if census_sha else "unverified"
    return {"status": status, "projection": generation,
            "census_sha256": (value.get('census_sha256') or (digest(census) if census else None)) if value else None,
            "cost_generation": costs, "profile": profile,
            "knowledge_cutoff": cutoff}


def capture_window(data_root: Path, dates: list[str]) -> dict:
    if not dates or len(dates) > MAX_DATES or dates != sorted(set(dates)):
        raise ValueError("window_dependency_dates_invalid")
    parsed = [date.fromisoformat(day) for day in dates]
    if any(day.isoformat() != text for day, text in zip(parsed, dates)) or any(
        right - left != timedelta(days=1) for left, right in zip(parsed, parsed[1:])
    ):
        raise ValueError("window_dependency_dates_invalid")
    root = Path(data_root).resolve()
    directory = root / "report/monitor_snapshots"
    rows = {}
    for day in dates:
        try:
            rows[day] = _capture_day(root, directory, day)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # The date is identifiable. Isolate it and retain its generation;
            # an invalid old row cannot erase valid current analysis.
            projections = {}
            for path in directory.glob(f'trade_review_{day}*'):
                if path.is_file() and not path.is_symlink():
                    stat = path.stat()
                    projections[path.name] = byte_generation(path) if stat.st_size <= MAX_PROJECTION_BYTES else {
                        'size':stat.st_size, 'mtime_ns':stat.st_mtime_ns, 'ctime_ns':stat.st_ctime_ns,
                        'inode':stat.st_ino, 'device':stat.st_dev, 'status':'unverified_unbounded_source'}
            rows[day] = {'status':'source_gap', 'reason':str(exc), 'projection':projections,
                         'census_sha256':None, 'cost_generation':source_generation(root, day),
                         'profile':None, 'knowledge_cutoff':None}
    body = {"schema": SCHEMA, "data_root": str(root), "dates": dates,
            "dependencies": rows}
    return {**body, "input_window_generation_sha256": digest(body)}


def verify_window(data_root: Path, recorded: dict) -> None:
    if not isinstance(recorded, dict) or recorded.get("schema") != SCHEMA:
        raise ValueError("window_dependency_unverified")
    body = {key: value for key, value in recorded.items()
            if key != "input_window_generation_sha256"}
    if digest(body) != recorded.get("input_window_generation_sha256"):
        raise ValueError("window_dependency_hash_invalid")
    if capture_window(data_root, recorded.get("dates")) != recorded:
        raise ValueError("window_dependency_generation_changed")
