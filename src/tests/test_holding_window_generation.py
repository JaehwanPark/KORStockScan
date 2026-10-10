"""Cumulative cost revision and immutable input-window regression cases."""
import json
import pytest
from src.engine.lifecycle.holding_window_generation import capture_window, verify_window
from src.engine.lifecycle.broker_cost_reconciliation import receipt_path


def test_past_only_cost_revision_invalidates_window_and_preserves_other_windows(tmp_path):
    prior = capture_window(tmp_path, ["2026-10-07", "2026-10-08"])
    unrelated = capture_window(tmp_path, ["2026-10-08"])
    receipt = receipt_path(tmp_path, "2026-10-07", "1")
    receipt.parent.mkdir(parents=True)
    receipt.write_text('{"revision":1}')
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, prior)
    verify_window(tmp_path, unrelated)
    current = capture_window(tmp_path, prior["dates"])
    assert current["dependencies"]["2026-10-07"]["status"] == "missing"
    assert current["input_window_generation_sha256"] != prior["input_window_generation_sha256"]


def test_legacy_cannot_be_resealed_and_root_is_bound(tmp_path):
    with pytest.raises(ValueError, match="unverified"):
        verify_window(tmp_path, {})
    window = capture_window(tmp_path, ["2026-10-08"])
    other = tmp_path / "other"
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(other, window)


def test_missing_date_arrival_and_same_size_revision_are_detected(tmp_path):
    before = capture_window(tmp_path, ["2026-10-08"])
    path = tmp_path / "report/monitor_snapshots/trade_review_2026-10-08.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"date": "2026-10-08", "meta": {"knowledge_cutoff": "a"}}))
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, before)
    first = capture_window(tmp_path, ["2026-10-08"])
    path.write_text(path.read_text().replace('"a"', '"b"'))
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, first)


def test_projection_dependency_receipt_avoids_redecoding_timelines_and_detects_tamper(tmp_path, monkeypatch):
    from src.engine import log_archive_service as archive
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle import holding_window_generation as window
    directory=tmp_path/'report/monitor_snapshots';directory.mkdir(parents=True)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',directory)
    day='2026-10-08'
    payload={'date':day,'metrics':{'canonical_completed_trades':0},
             'meta':{'snapshot_profile':'postclose_exit','sell_completed_event_ids':[]},
             'sections':{'completed_trade_projection':[],'open_scalp_position_projection':[]}}
    payload['meta']['completed_census_manifest']=completed_census_manifest(payload)
    path=archive.save_monitor_snapshot('trade_review',day,payload)
    original=window.json.loads; decoded=[]
    def once(raw,*a,**k):
        decoded.append(len(raw));return original(raw,*a,**k)
    monkeypatch.setattr(window.json,'loads',once)
    sealed=capture_window(tmp_path,[day])
    assert sealed['dependencies'][day]['status']=='valid_empty'
    assert len(decoded)==1 and max(decoded)<window.MAX_METADATA_BYTES
    sidecar=path.with_suffix('.completed_projection.json')
    sidecar.write_text(sidecar.read_text().replace('postclose_exit','postclose_Exit'))
    with pytest.raises(ValueError,match='generation_changed'):
        verify_window(tmp_path,sealed)


def test_verifier_access_time_cannot_invalidate_same_generation():
    from types import SimpleNamespace
    from src.engine.lifecycle.holding_window_generation import source_stat
    values=dict(st_dev=1,st_ino=2,st_size=3,st_mtime_ns=4,st_ctime_ns=5,st_atime_ns=6)
    assert source_stat(SimpleNamespace(**values))==source_stat(SimpleNamespace(**{**values,'st_atime_ns':7}))
    assert source_stat(SimpleNamespace(**values))!=source_stat(SimpleNamespace(**{**values,'st_ctime_ns':7}))
