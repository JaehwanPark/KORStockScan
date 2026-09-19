import hashlib
import json
from pathlib import Path

from src.engine import runtime_approval_summary as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _patch(monkeypatch, tmp_path: Path) -> Path:
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "runtime_approval_summary")
    return data


def _seed_required(target_date: str) -> None:
    for owner, path in mod._paths(target_date).items():
        if owner == "runtime_bootstrap" or owner not in mod.REQUIRED_DIRECT_OWNERS:
            continue
        _write(
            path,
            {
                "report_type": owner,
                "target_date": target_date,
                "status": "valid_empty" if owner == "entry_cancel_wait" else "pass",
                "runtime_effect": False,
            },
        )


def test_summary_passes_with_required_direct_producers_and_optional_receipts_absent(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == "pass"
    assert report["daily_threshold_cycle_retired"] is True
    assert report["threshold_cycle_ev_retired"] is True
    assert report["common_tuning_candidate_created"] is False
    assert report["available_required_source_count"] == report["required_source_count"]
    assert report["sources"]["entry_split_policy"]["required"] is False


def test_summary_distinguishes_missing_required_from_optional(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    mod._paths(target)["entry_split"].unlink()

    report = mod.build_runtime_approval_summary(target)

    assert report["status"] == "incomplete_direct_evidence"
    assert "entry_split:missing" in report["blocking_reasons"]
    assert all("entry_split_policy:missing" != item for item in report["blocking_reasons"])


def test_summary_stream_hashes_large_exact_date_artifact_without_json_load(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    target = "2026-09-19"
    _seed_required(target)
    path = mod._paths(target)["low_price_two_leg"]
    path.write_bytes(b"x" * 1024)
    monkeypatch.setattr(mod, "MAX_DIRECT_JSON_BYTES", 512)

    report = mod.build_runtime_approval_summary(target)
    row = report["sources"]["low_price_two_leg"]

    assert report["status"] == "pass"
    assert row["read_mode"] == "stream_hash_only_large_json"
    assert row["status"] == "large_artifact_present"
    assert row["sha256"] == hashlib.sha256(b"x" * 1024).hexdigest()
