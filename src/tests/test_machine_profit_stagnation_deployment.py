"""Deployment path/pin contracts; no broker calls or service installation."""

import json
import hashlib
from datetime import datetime
from pathlib import Path

import pytest

from src.trading.low_price_two_leg import preflight
from src.trading.widget_auto_trade.runtime_verification import environment_hashes
from src.trading.config.machine_profit_stagnation_policy import (
    PATH_ENV,
    HASH_ENV,
    load_policy,
)


def test_installed_policy_scope_dates_cost_and_pins(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    folder = root / "deploy/machine-profit-stagnation"
    path = folder / "policy.json"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    policy = json.loads(path.read_text())
    assert (
        policy["cost_source_sha256"]
        == hashlib.sha256((folder / "operator-cost.json").read_bytes()).hexdigest()
    )
    assert {
        k: policy[k]
        for k in (
            "min_sec",
            "max_profit_move",
            "max_peak_improve",
            "round_trip_cost_pct",
            "slippage_bps",
            "sell_ttl_sec",
            "max_observation_gap_sec",
        )
    } == dict(
        min_sec=180,
        max_profit_move=0.15,
        max_peak_improve=0.10,
        round_trip_cost_pct=0.23,
        slippage_bps=5,
        sell_ttl_sec=10,
        max_observation_gap_sec=12,
    )
    monkeypatch.setenv(PATH_ENV, str(path))
    monkeypatch.setenv(HASH_ENV, digest)

    def at(day):
        return datetime.fromisoformat(day + "T10:00:00+09:00")

    for owner in ("widget_auto_trade", "episode"):
        assert (
            load_policy(now=at("2026-09-10"), owner=owner, entered_at=at("2026-09-10"))
            is None
        )
        assert (
            load_policy(now=at("2026-09-11"), owner=owner, entered_at=at("2026-09-10"))
            is None
        )
        assert load_policy(
            now=at("2026-09-11"), owner=owner, entered_at=at("2026-09-11")
        ) == (policy, digest)
        assert load_policy(
            now=at("2026-09-14"), owner=owner, entered_at=at("2026-09-14")
        ) == (policy, digest)
    assert (
        load_policy(now=at("2026-09-11"), owner="main", entered_at=at("2026-09-11"))
        is None
    )
    dropins = list(folder.glob("*.service.conf"))
    assert len(dropins) == 9
    for dropin in dropins:
        text = dropin.read_text()
        assert f"WorkingDirectory={root}" in text
        assert f"{PATH_ENV}={path}" in text
        assert f"{HASH_ENV}={digest}" in text
        assert text.count("ExecStart=") == 2


def test_shared_report_mount_allowed_but_external_source_rejected(
    tmp_path, monkeypatch
):
    release = tmp_path / "release"
    release.mkdir()
    data = tmp_path / "canonical" / "data"
    reports = data / "report"
    reports.mkdir(parents=True)
    (release / "data").symlink_to(data, target_is_directory=True)
    source = {"exact": "approved"}
    digest = preflight._canonical_payload_sha256(source)
    (reports / "source.json").write_text(json.dumps(source))
    monkeypatch.setattr(preflight, "PROJECT_ROOT", release)
    monkeypatch.setattr(preflight, "DATA_DIR", data)
    contract = {"source_report_sha256": digest}

    def check(path):
        return preflight._approved_source_report(
            {"source_report": {"path": str(path), "canonical_sha256": digest}},
            contract,
        )

    assert check("data/report/source.json") == (source, "ready")
    assert check(reports / "source.json") == (source, "ready")
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(source))
    assert check(outside) == (None, "research_source_report_unreadable")
    (reports / "escape.json").symlink_to(outside)
    assert check("data/report/escape.json") == (
        None,
        "research_source_report_unreadable",
    )
    assert check("data/report/missing.json") == (
        None,
        "research_source_report_unreadable",
    )
    (reports / "source.json").write_text('{"changed": true}')
    assert check("data/report/source.json") == (
        None,
        "research_source_report_hash_mismatch",
    )


@pytest.mark.parametrize("suffix", ["PATH", "SHA256"])
def test_startup_receipt_includes_machine_policy_pin(suffix):
    key = "KORSTOCKSCAN_MACHINE_PROFIT_STAGNATION_POLICY_" + suffix
    assert environment_hashes({key: "pin"})[key]
    assert environment_hashes({})[key] is None


@pytest.mark.parametrize(
    "name",
    [
        "run_low_price_two_leg_live.sh",
        "run_low_price_two_leg_preflight.sh",
        "run_samsung_morning_one_share_preflight.sh",
        "run_samsung_midday_one_share_preflight.sh",
        "run_samsung_afternoon_one_share_preflight.sh",
    ],
)
def test_machine_wrappers_use_their_own_release(name):
    script = (Path(__file__).resolve().parents[2] / "deploy" / name).read_text()
    assert 'PROJECT_DIR="/home/ubuntu/KORStockScan"' not in script
    assert "BASH_SOURCE[0]" in script
    assert 'PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"' in script
