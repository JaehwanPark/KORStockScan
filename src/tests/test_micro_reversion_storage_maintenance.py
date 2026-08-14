import gzip
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion import (
    storage_maintenance as storage_maintenance_module,
)
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


def test_storage_maintenance_preserves_open_closed_date_source_inode(
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
    handle = source.open("a+", encoding="utf-8")
    original_inode = os.fstat(handle.fileno()).st_ino
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["failed_candidate_count"] == 1
        assert "source_open_fd" in result["partition_failures"][0]["reason"]
        assert source.stat().st_ino == original_inode
        assert os.fstat(handle.fileno()).st_nlink == 1
        assert not source.with_suffix(".jsonl.gz").exists()
        handle.write('{"value":2}\n')
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    assert source.read_text(encoding="utf-8") == '{"value":1}\n{"value":2}\n'


def test_storage_maintenance_reports_partial_purge_and_recovers_next_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trade_dir = tmp_path / "trade_date=2026-07-01"
    first = trade_dir / "venue=KRX" / "a.jsonl"
    second = trade_dir / "venue=KRX" / "b.jsonl"
    first.parent.mkdir(parents=True)
    first.write_text("a\n", encoding="utf-8")
    second.write_text("bb\n", encoding="utf-8")
    first_bytes = first.stat().st_size
    second_bytes = second.stat().st_size
    real_rmtree = storage_maintenance_module.shutil.rmtree

    def partial_rmtree(path: Path) -> None:
        assert Path(path) == trade_dir
        first.unlink()
        raise OSError("injected_partial_rmtree_failure")

    monkeypatch.setattr(storage_maintenance_module.shutil, "rmtree", partial_rmtree)
    first_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert first_result["status"] == "partial_failure"
    assert not first.exists()
    assert second.exists()
    assert first_result["purge_applied_count"] == 0
    assert first_result["purge_partial_applied_count"] == 1
    assert first_result["deletion_performed"] is True
    assert first_result["actions"][0]["action"] == "purge_trade_date_partial"
    assert first_result["actions"][0]["source_bytes"] == first_bytes
    assert first_result["failed_candidate_count"] == 1
    assert first_result["failed_candidate_bytes"] == second_bytes
    assert first_result["recovery_required_count"] == 1

    monkeypatch.setattr(storage_maintenance_module.shutil, "rmtree", real_rmtree)
    second_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(retention_days=14),
        apply=True,
        purge_expired=True,
    )

    assert second_result["status"] == "pass"
    assert second_result["purge_applied_count"] == 1
    assert not trade_dir.exists()


def test_storage_maintenance_isolates_open_group_and_compresses_peer_group(
    tmp_path: Path,
) -> None:
    session_dir = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=KRX_REGULAR"
    )
    session_dir.mkdir(parents=True)
    first_source = session_dir / "a.jsonl"
    open_source = session_dir / "z.jsonl"
    manifest = session_dir / "a.manifest.json"
    first_source.write_text('{"value":"first"}\n', encoding="utf-8")
    open_source.write_text('{"value":"open"}\n', encoding="utf-8")
    manifest_payload = {
        "schema": "scalp_micro_reversion_market_path_manifest_v1",
        "shards": [
            {
                "index": 0,
                "file": first_source.name,
                "bytes": first_source.stat().st_size,
            }
        ],
    }
    manifest.write_text(json.dumps(manifest_payload) + "\n", encoding="utf-8")
    original_bytes = {
        path: path.read_bytes() for path in (first_source, open_source, manifest)
    }
    original_inodes = {
        path: path.stat().st_ino for path in (first_source, open_source, manifest)
    }
    handle = open_source.open("a+", encoding="utf-8")
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(compression_after_days=1),
            apply=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["action_count"] == 1
        assert not first_source.exists()
        assert first_source.with_suffix(".jsonl.gz").exists()
        assert open_source.read_bytes() == original_bytes[open_source]
        assert open_source.stat().st_ino == original_inodes[open_source]
        assert not open_source.with_suffix(".jsonl.gz").exists()
        updated_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        assert updated_manifest["shards"][0]["file"] == "a.jsonl.gz"
        assert os.fstat(handle.fileno()).st_nlink == 1
    finally:
        handle.close()


def test_storage_maintenance_preserves_source_changed_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    real_assert = storage_maintenance_module._assert_source_unchanged_and_closed
    changed = False

    def assert_with_change(
        path: Path,
        expected: tuple[int, int, int, int, str],
        *,
        phase: str,
    ) -> None:
        nonlocal changed
        if path == source and phase == "before_partition_publish" and not changed:
            changed = True
            with source.open("a", encoding="utf-8") as handle:
                handle.write('{"value":2}\n')
                handle.flush()
                os.fsync(handle.fileno())
        real_assert(path, expected, phase=phase)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_assert_source_unchanged_and_closed",
        assert_with_change,
    )
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert (
        "source_changed_before_partition_publish"
        in result["partition_failures"][0]["reason"]
    )
    assert source.read_text(encoding="utf-8") == '{"value":1}\n{"value":2}\n'
    assert not source.with_suffix(".jsonl.gz").exists()


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


def test_storage_maintenance_explicit_purge_preserves_open_tree_file(
    tmp_path: Path,
) -> None:
    expired = tmp_path / "trade_date=2026-07-01" / "venue=KRX" / "row.jsonl"
    expired.parent.mkdir(parents=True)
    expired.write_text("{}\n", encoding="utf-8")
    handle = expired.open("rb")
    original_inode = os.fstat(handle.fileno()).st_ino
    try:
        result = maintain_forward_storage(
            tmp_path,
            as_of_date=date(2026, 8, 10),
            storage_policy=PathStoragePolicy(retention_days=14),
            apply=True,
            purge_expired=True,
        )

        assert result["status"] == "partial_failure"
        assert result["partition_failure_count"] == 1
        assert result["failed_candidate_count"] == 1
        assert result["failed_candidate_bytes"] == expired.stat().st_size
        assert result["purge_candidate_count"] == 1
        assert result["purge_candidate_bytes"] == expired.stat().st_size
        assert any(
            "source_open_fd" in row["reason"] for row in result["partition_failures"]
        )
        assert expired.stat().st_ino == original_inode
        assert os.fstat(handle.fileno()).st_nlink == 1
        assert expired.parents[1].exists()
    finally:
        handle.close()


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
    peer = trade_dir / "session=PEER" / "peer.jsonl"
    peer.parent.mkdir()
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert result["partition_failure_count"] == 1
    assert result["failed_candidate_count"] == 1
    assert result["failed_candidate_bytes"] == 0
    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_rejects_fifo_and_continues_peer(tmp_path: Path) -> None:
    blocked = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=BLOCKED"
        / "market_stream.jsonl"
    )
    peer = blocked.parents[1] / "session=PEER" / "peer.jsonl"
    blocked.parent.mkdir(parents=True)
    peer.parent.mkdir()
    os.mkfifo(blocked)
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    started = time.monotonic()
    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert time.monotonic() - started < 2
    assert result["status"] == "partial_failure"
    assert blocked.is_fifo()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()
    assert any(
        "unsafe_non_regular_file" in row["reason"]
        for row in result["partition_failures"]
    )


def test_storage_maintenance_isolates_unsafe_trade_date_and_continues_peer(
    tmp_path: Path,
) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external"
    external.mkdir()
    external_source = external / "outside.jsonl"
    external_source.write_text('{"outside":true}\n', encoding="utf-8")
    os.symlink(external, tmp_path / "trade_date=2026-08-07")
    peer = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=PEER" / "peer.jsonl"
    )
    peer.parent.mkdir(parents=True)
    peer.write_text('{"peer":true}\n', encoding="utf-8")

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert any(
        row["trade_date"] == "2026-08-07" for row in result["partition_failures"]
    )
    assert external_source.exists()
    assert not external_source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


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
    original_manifest = manifest.read_bytes()

    dry_run = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
    )

    assert dry_run["action_count"] == 1
    assert dry_run["source_bytes"] == manifest.stat().st_size
    assert dry_run["actions"] == [
        {
            "action": "repair_manifest_reference",
            "path": str(manifest),
            "trade_date": "2026-08-08",
            "source_bytes": manifest.stat().st_size,
            "applied": False,
        }
    ]
    assert manifest.read_bytes() == original_manifest

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert result["action_count"] == 1
    assert result["actions"][0]["action"] == "repair_manifest_reference"
    assert payload["shards"][0]["file"] == "market_stream.jsonl.gz"
    assert payload["shards"][0]["compressed"] is True


def test_storage_maintenance_reports_partial_unlink_and_recovers_next_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=KRX_REGULAR"
    session.mkdir(parents=True)
    first = session / "stream.jsonl"
    second = session / "stream.part-000001.jsonl"
    first.write_text('{"row":1}\n', encoding="utf-8")
    second.write_text('{"row":2}\n', encoding="utf-8")
    manifest = session / "stream.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "shards": [
                    {"index": 0, "file": first.name, "bytes": first.stat().st_size},
                    {
                        "index": 1,
                        "file": second.name,
                        "bytes": second.stat().st_size,
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    real_unlink = Path.unlink

    def fail_second_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == second:
            raise OSError("injected_second_unlink_failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_second_unlink)
    first_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert first_result["status"] == "partial_failure"
    assert first_result["recovery_required_count"] == 1
    assert first_result["failed_candidate_count"] == 1
    assert first_result["failed_candidate_bytes"] == second.stat().st_size
    assert first_result["action_count"] == 3
    assert not first.exists()
    assert first.with_suffix(".jsonl.gz").exists()
    assert second.exists()
    assert second.with_suffix(".jsonl.gz").exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert all(row["file"].endswith(".gz") for row in manifest_payload["shards"])

    monkeypatch.setattr(Path, "unlink", real_unlink)
    second_result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second_result["status"] == "pass"
    assert not second.exists()
    assert second_result["actions"][0]["action"] == ("finalize_verified_compression")


def test_storage_maintenance_rejects_external_gzip_symlink_before_source_unlink(
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
    payload = b'{"row":1}\n'
    source.write_bytes(payload)
    external = tmp_path.parent / f"{tmp_path.name}-external.gz"
    external.write_bytes(gzip.compress(payload, mtime=0))
    original_external = external.read_bytes()
    target = source.with_suffix(".jsonl.gz")
    target.symlink_to(external)

    result = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert result["status"] == "partial_failure"
    assert source.read_bytes() == payload
    assert target.is_symlink()
    assert external.read_bytes() == original_external
    assert result["action_count"] == 0
    assert any("symlink" in row["reason"] for row in result["partition_failures"])


def test_storage_maintenance_reports_gzip_published_before_directory_fsync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        tmp_path
        / "trade_date=2026-08-08"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    source.parent.mkdir(parents=True)
    source.write_text('{"row":1}\n', encoding="utf-8")
    source_bytes = source.stat().st_size
    real_fsync_directory = storage_maintenance_module._fsync_directory
    call_count = 0

    def fail_first_directory_fsync(path: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("injected_publish_directory_fsync_failure")
        real_fsync_directory(path)

    monkeypatch.setattr(
        storage_maintenance_module,
        "_fsync_directory",
        fail_first_directory_fsync,
    )
    first = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    target = source.with_suffix(".jsonl.gz")
    assert first["status"] == "partial_failure"
    assert source.exists()
    assert target.exists()
    assert first["action_count"] == 1
    assert first["actions"][0]["action"] == ("publish_verified_gzip_source_preserved")
    assert first["failed_candidate_count"] == 1
    assert first["failed_candidate_bytes"] == source_bytes
    assert first["partition_failures"][0]["published_target_count"] == "1"
    assert first["recovery_required_count"] == 1

    monkeypatch.setattr(
        storage_maintenance_module,
        "_fsync_directory",
        real_fsync_directory,
    )
    second = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second["status"] == "pass"
    assert not source.exists()
    assert second["actions"][0]["action"] == "finalize_verified_compression"


def test_storage_maintenance_isolates_invalid_manifest_group(
    tmp_path: Path,
) -> None:
    blocked_session = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=BLOCKED"
    )
    peer_session = blocked_session.with_name("session=PEER")
    blocked_session.mkdir(parents=True)
    peer_session.mkdir(parents=True)
    blocked = blocked_session / "a.jsonl"
    peer = peer_session / "z.jsonl"
    blocked.write_text('{"row":"blocked"}\n', encoding="utf-8")
    peer.write_text('{"row":"peer"}\n', encoding="utf-8")
    (blocked_session / "a.manifest.json").write_text("{malformed", encoding="utf-8")
    (peer_session / "z.manifest.json").write_text(
        json.dumps(
            {"shards": [{"index": 0, "file": peer.name, "bytes": peer.stat().st_size}]}
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

    assert result["status"] == "partial_failure"
    assert result["partition_failure_count"] >= 1
    assert blocked.exists()
    assert not blocked.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()


def test_storage_maintenance_rejects_overlapping_manifest_ownership_before_mutation(
    tmp_path: Path,
) -> None:
    conflict_session = (
        tmp_path / "trade_date=2026-08-08" / "venue=KRX" / "session=CONFLICT"
    )
    peer_session = conflict_session.with_name("session=PEER")
    conflict_session.mkdir(parents=True)
    peer_session.mkdir(parents=True)
    source = conflict_session / "market_stream.jsonl"
    source.write_text('{"row":"conflict"}\n', encoding="utf-8")
    manifests = (
        conflict_session / "a.manifest.json",
        conflict_session / "b.manifest.json",
    )
    payload = {
        "shards": [{"index": 0, "file": source.name, "bytes": source.stat().st_size}]
    }
    for manifest in manifests:
        manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    peer = peer_session / "peer.jsonl"
    peer.write_text('{"row":"peer"}\n', encoding="utf-8")
    peer_manifest = peer_session / "peer.manifest.json"
    peer_manifest.write_text(
        json.dumps(
            {"shards": [{"index": 0, "file": peer.name, "bytes": peer.stat().st_size}]}
        )
        + "\n",
        encoding="utf-8",
    )
    original = {path: path.read_bytes() for path in (source, *manifests)}

    first = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert first["status"] == "partial_failure"
    assert any(
        "multiple manifests claim one shard" in row["reason"]
        for row in first["partition_failures"]
    )
    assert {path: path.read_bytes() for path in (source, *manifests)} == original
    assert not source.with_suffix(".jsonl.gz").exists()
    assert not peer.exists()
    assert peer.with_suffix(".jsonl.gz").exists()

    second = maintain_forward_storage(
        tmp_path,
        as_of_date=date(2026, 8, 10),
        storage_policy=PathStoragePolicy(compression_after_days=1),
        apply=True,
    )

    assert second["status"] == "partial_failure"
    assert {path: path.read_bytes() for path in (source, *manifests)} == original
    assert not source.with_suffix(".jsonl.gz").exists()
