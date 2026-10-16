"""Operational retention owns closed files, never raw trading evidence."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.engine.infrastructure import log_retention as R


def generation(root, name='writer.log.closed_one'):
    log = root/'logs'; log.mkdir(exist_ok=True)
    path = log/name; path.write_bytes(b'original\r\nevidence\n')
    row = R.register_generation(log/'writer.log', path, owner='writer')
    return path, row


def test_expired_closed_generation_deletes_with_tombstone_and_unknown_stays(tmp_path):
    path, row = generation(tmp_path)
    active = path.parent/'writer.log'; active.write_text('live')
    unknown = path.parent/'unknown.log.1'; unknown.write_text('unknown')
    now = row['closed_at']+31*R.DAY
    preview = R.maintain_logs(tmp_path, now=now)
    assert preview['deleted'] == 1 and path.exists()
    result = R.maintain_logs(tmp_path, now=now, apply=True)
    assert result['status'] == 'complete' and result['deleted'] == 1
    assert not path.exists() and active.read_text() == 'live' and unknown.exists()
    assert R.maintain_logs(tmp_path, now=now, apply=True)['deleted'] == 0


@pytest.mark.parametrize('protection', ['open','pin','reference','modified','symlink'])
def test_expiry_preserves_protected_or_changed_generations(tmp_path, protection):
    path, row = generation(tmp_path); handle = None
    if protection == 'open': handle = path.open('rb')
    if protection == 'pin':
        R.atomic_json(tmp_path/'data/config/log_retention_pins.json',
                      dict(schema='operational_retention_pins_v1', pins=[str(path)]))
    if protection == 'reference':
        docs = tmp_path/'docs'; docs.mkdir(); (docs/'audit.md').write_text(path.name)
    if protection == 'modified': path.write_text('changed')
    if protection == 'symlink':
        dest = tmp_path/'outside'; dest.write_text('original'); path.unlink(); path.symlink_to(dest)
    try:
        result = R.maintain_logs(tmp_path, now=row['closed_at']+31*R.DAY, apply=True)
        assert path.exists() and result['deleted'] == 0
    finally:
        if handle: handle.close()


def test_generation_count_and_capacity_are_per_writer(tmp_path):
    paths = [generation(tmp_path, f'writer.log.closed_{n}')[0] for n in range(11)]
    other = tmp_path/'logs/other.log.closed'; other.write_text('other')
    R.register_generation(tmp_path/'logs/other.log', other, owner='other')
    result = R.maintain_logs(tmp_path, apply=True)
    assert result['status'] == 'complete' and result['deleted'] == 1
    assert sum(p.exists() for p in paths) == 10 and other.exists()


def test_unknown_tmp_worktree_and_evidence_never_age_out(tmp_path):
    run = tmp_path/'tmp/workorder-old'; run.mkdir(parents=True); file = run/'evidence.json'; file.write_text('{}')
    os.utime(file, (1,1))
    assert R.maintain_tmp(tmp_path, apply=True)['deleted'] == 0 and file.exists()
    R.atomic_json(run/'run.retention.json', dict(schema='temporary_run_retention_v1', owner='test',
        closed=True, pinned=False, expires_at=1, files={'evidence.json': R.digest(file)}))
    assert R.maintain_tmp(tmp_path, apply=True)['deleted'] == 1 and not file.exists()


def test_daily_metrics_retains_invalid_and_exact_current_bytes(tmp_path):
    source = tmp_path/'logs/system_metric_samples.jsonl'; source.parent.mkdir()
    original = b'{"ts":"2026-10-10T10:00:00+09:00"}\n{bad}\r\n{"ts":"2026-10-16T10:00:00+09:00"}\r\n'
    source.write_bytes(original)
    result = R.prune_metrics(tmp_path, apply=True,
                            now=datetime(2026,10,16,6,tzinfo=timezone.utc).timestamp())
    assert result['pruned'] == 1 and result['invalid_retained'] == 1
    assert source.read_bytes() == original.split(b'\n',1)[1]


def test_active_file_cannot_register_as_closed(tmp_path):
    p = tmp_path/'writer.log'; p.write_text('live')
    with pytest.raises(ValueError): R.register_generation(p,p,owner='writer')


def test_retention_failure_has_nonzero_and_failed_terminal(tmp_path):
    (tmp_path/'logs').mkdir()
    terminal = tmp_path/'receipt.json'
    R.atomic_json(tmp_path/'data/config/log_retention_pins.json', {'schema':'invalid'})
    assert R.main(['--workspace',str(tmp_path),'--terminal',str(terminal),'--apply']) == 1
    assert json.loads(terminal.read_bytes())['status'] == 'failed'


def test_tmp_recovers_crash_after_unlink_without_deleting_reappeared_path(tmp_path, monkeypatch):
    run = tmp_path/'tmp/run'; run.mkdir(parents=True)
    one = run/'one.json'; one.write_text('one')
    two = run/'two.json'; two.write_text('two')
    manifest = run/'run.retention.json'
    row = dict(schema='temporary_run_retention_v1', owner='test', closed=True, pinned=False,
        expires_at=1, files={p.name:R.digest(p) for p in (one,two)}, delete_pending='one.json')
    R.atomic_json(manifest,row); one.unlink()
    assert R.maintain_tmp(tmp_path,apply=True)['deleted'] == 1
    assert not two.exists() and R.read_json(manifest)['closed'] is False
    assert set(R.read_json(manifest)['deleted_files']) == {'one.json','two.json'}


def test_tmp_retry_does_not_accept_missing_file_without_delete_intent(tmp_path):
    run = tmp_path/'tmp/run'; run.mkdir(parents=True)
    one = run/'one.json'; one.write_text('one')
    two = run/'two.json'; two.write_text('two')
    R.atomic_json(run/'run.retention.json', dict(schema='temporary_run_retention_v1', owner='test',
        closed=True,pinned=False,expires_at=1,files={p.name:R.digest(p) for p in (one,two)}))
    one.unlink()
    result = R.maintain_tmp(tmp_path,apply=True)
    assert result['deleted'] == 0 and result['deferred'] and two.exists()
