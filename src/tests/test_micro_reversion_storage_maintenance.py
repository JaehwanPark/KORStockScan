import gzip
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion.path_journal import PathStoragePolicy
from src.engine.scalping.micro_reversion.storage_maintenance import (
    maintain_forward_storage,
)


def test_storage_maintenance_dry_run_does_not_mutate(tmp_path: Path) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
    )

    assert result["mode"] == "dry_run"
    assert result["action_count"] == 1
    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_compresses_and_verifies_closed_date(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = '{"value":1}\n{"value":2}\n'
    source.write_text(original, encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    compressed = source.with_suffix(".jsonl.gz")
    assert result["action_count"] == 1
    assert not source.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert handle.read() == original


def test_storage_maintenance_repoints_manifest_to_compressed_shard(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"value":1}\n', encoding="utf-8")
    manifest = source.with_name("market_stream.manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_path_manifest_v1",
                "shards": [
                    {"index": 0, "file": source.name, "bytes": source.stat().st_size}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["shards"][0]["file"] == "market_stream.jsonl.gz"
    assert payload["shards"][0]["compressed"] is True
    assert payload["storage_maintenance_as_of_date"] == "2026-08-10"


def test_storage_maintenance_never_purges_expired_date_without_explicit_opt_in(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
    )

    assert expired.parents[1].exists()
    assert not expired.exists()
    assert expired.with_suffix(".jsonl.gz").exists()
    assert result["purge_enabled"] is False
    assert result["purge_status"] == "disabled_no_deletion_authority"
    assert result["purge_candidate_count"] == 1
    assert result["purge_candidate_bytes"] > 0
    assert result["purge_applied_count"] == 0
    assert result["deletion_performed"] is False
    assert all(row["action"] != "purge_trade_date" for row in result["actions"])


def test_storage_maintenance_purges_only_expired_trade_date_with_explicit_opt_in(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    current = tmp_path / "trade_date=2026-08-10" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    current.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")
    current.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert result["action_count"] == 1
    assert not expired.parents[1].exists()
    assert current.exists()
    assert result["purge_enabled"] is True
    assert result["purge_status"] == "explicit_opt_in_apply"
    assert result["purge_candidate_count"] == 1
    assert result["purge_applied_count"] == 1
    assert result["deletion_performed"] is True


def test_storage_maintenance_purge_dry_run_reports_but_does_not_delete(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        purge_expired=True,
    )

    assert expired.exists()
    assert result["mode"] == "dry_run"
    assert result["purge_status"] == "explicit_opt_in_dry_run"
    assert result["purge_applied_count"] == 0
    assert result["deletion_performed"] is False
    assert result["actions"] == [
        {
            "action": "purge_trade_date",
            "path": str(expired.parents[1]),
            "trade_date": "2026-07-01",
            "source_bytes": expired.stat().st_size,
            "applied": False,
        }
    ]


@pytest.mark.parametrize(
    ("apply", "purge_expired"),
    (("true", False), (False, "true")),
)
def test_storage_maintenance_rejects_non_boolean_authority(
    tmp_path: Path,
    apply: object,
    purge_expired: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="storage maintenance authorities must be native booleans",
    ):
        maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            apply=apply,  # type: ignore[arg-type]
            purge_expired=purge_expired,  # type: ignore[arg-type]
        )


def test_storage_maintenance_does_not_follow_nested_symlink(tmp_path: Path) -> None:
    real_session = tmp_path / "real_session"
    real_session.mkdir()
    source = real_session / "market_stream.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    trade_dir = tmp_path / "trade_date=2026-08-08" / "venue=KRX"
    trade_dir.mkdir(parents=True)
    os.symlink(real_session, trade_dir / "session=KRX_REGULAR")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["action_count"] == 0
    assert source.exists()


def test_storage_maintenance_rejects_future_apply_and_protects_runtime_date(
    tmp_path: Path,
) -> None:
    runtime_trade_date = datetime.now(ZoneInfo("Asia/Seoul")).date()
    source = (
        tmp_path
        / f"trade_date={runtime_trade_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="storage maintenance as-of date must not be in the future",
    ):
        maintain_forward_storage(
            tmp_path,
            as_of_date=runtime_trade_date + timedelta(days=1),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_recovers_interrupted_source_unlink(
    tmp_path: Path,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    original = '{"value":1}\n'
    source.write_text(original, encoding="utf-8")
    compressed = source.with_suffix(".jsonl.gz")
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write(original)

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["actions"][0]["action"] == "finalize_verified_compression"
    assert not source.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert handle.read() == original


def test_storage_maintenance_repairs_manifest_after_interrupted_refresh(
    tmp_path: Path,
) -> None:
    compressed = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl.gz"
    )
    compressed.parent.mkdir(parents=True)
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write('{"value":1}\n')
    manifest = compressed.with_name("market_stream.manifest.json")
    manifest.write_text(
        json.dumps(
            {
                "schema": "scalp_micro_reversion_market_path_manifest_v1",
                "shards": [
                    {
                        "index": 0,
                        "file": "market_stream.jsonl",
                        "bytes": 12,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert result["action_count"] == 0
    assert payload["shards"][0]["file"] == "market_stream.jsonl.gz"
    assert payload["shards"][0]["compressed"] is True
