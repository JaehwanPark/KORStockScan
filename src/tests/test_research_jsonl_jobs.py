import json
import hashlib
import pytest
from src.engine.lifecycle.research_jsonl_jobs import scan
from src.engine.lifecycle.research_disk_budget import use
from src.engine.lifecycle.research_storage import write_tree


def jobs(path, out, project=lambda x: x):
    return list(
        scan(
            path,
            output_root=out,
            project=project,
            projection_sha256="a" * 64,
            job_bytes=30,
            record_bytes=128,
        )
    )


def test_resume_rehashes_bytes_without_decoding_and_handles_append(tmp_path):
    p = tmp_path / "rows.jsonl"
    p.write_text("".join(json.dumps({"id": i}) + "\n" for i in range(12)))
    first = jobs(p, tmp_path / "cache")
    rows = [x["value"] for x in first if x["kind"] == "row"]
    assert len(rows) == 12

    def no_decode(value):
        pytest.fail("source decoded on exact resume")

    second = jobs(p, tmp_path / "cache", no_decode)
    assert [x["value"] for x in second if x["kind"] == "row"] == rows
    assert all(x["reused"] for x in second if x["kind"] == "checkpoint")
    with p.open("a") as f:
        f.write('{"id":12}\n')
    third = jobs(p, tmp_path / "cache")
    assert len([x for x in third if x["kind"] == "row"]) == 13
    assert sum(not x["reused"] for x in third if x["kind"] == "checkpoint") == 1


def test_late_conflict_not_lost_at_scan_job_boundary_and_partial_record_isolated(
    tmp_path,
):
    p = tmp_path / "rows.jsonl"
    p.write_text(
        '{"id":1,"v":1}\n' + (" " * 150) + "\n" + '{"id":1,"v":2}\n' + '{"id":'
    )
    result = jobs(p, tmp_path / "cache")
    assert [x["value"]["v"] for x in result if x["kind"] == "row"] == [1, 2]
    assert (
        sum(
            x["receipt"]["census"].get("isolated_records", 0)
            for x in result
            if x["kind"] == "checkpoint"
        )
        == 2
    )
    # Source change is checked by byte range, independently of physical layout.
    p.write_text(p.read_text().replace('"v":2', '"v":3'))
    changed = jobs(p, tmp_path / "cache")
    assert [x["value"]["v"] for x in changed if x["kind"] == "row"] == [1, 3]


def test_combined_disk_budget_never_deletes_referenced_evidence(tmp_path):
    with use(tmp_path, durable_limit=1024, temp_limit=1024) as budget:
        from src.engine.lifecycle.research_disk_budget import temporary

        with temporary(600):
            with pytest.raises(ValueError, match="combined_disk"):
                with temporary(500):
                    pass
        first = write_tree(tmp_path, [{"id": 1}])
        before = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
        with pytest.raises(ValueError, match="combined_disk"):
            write_tree(tmp_path, [{"text": "a" * 2000}])
        assert before == {p: p.read_bytes() for p in before}
        assert budget.temp_reserved == 0


def test_partial_final_record_is_rebuilt_when_completed_by_append(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id":1}\n{"id":')
    first = jobs(path, tmp_path / "cache")
    assert [x["value"] for x in first if x["kind"] == "row"] == [{"id": 1}]
    with path.open("a") as handle:
        handle.write("2}\n")
    second = jobs(path, tmp_path / "cache")
    assert [x["value"] for x in second if x["kind"] == "row"] == [{"id": 1}, {"id": 2}]


def test_larger_than_two_gibibytes_source_is_scanned_without_replication(tmp_path):
    # Sparse invalid envelope plus a healthy bounded row exercises the exact
    # size boundary without persisting a multi-GiB raw replica each round.
    path = tmp_path / "oversize.jsonl"
    with path.open("wb") as handle:
        handle.write(b"{")
        handle.seek(2 * 1024**3 + 1)
        handle.write(b'\n{"id":"healthy"}\n')
    out = tmp_path / "cache"
    result = list(
        scan(
            path,
            output_root=out,
            project=lambda x: x,
            projection_sha256="b" * 64,
            job_bytes=2 * 1024**3,
            record_bytes=65536,
        )
    )
    assert [x["value"] for x in result if x["kind"] == "row"] == [{"id": "healthy"}]
    checkpoints = [x for x in result if x["kind"] == "checkpoint"]
    assert len(checkpoints) == 2
    assert (
        sum(x["receipt"]["census"].get("isolated_records", 0) for x in checkpoints) == 1
    )
    assert sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) < 1024 * 1024


def test_shared_disk_reservation_includes_existing_sibling_generation(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (second / "old").write_bytes(b"x" * 700)
    with use(first, durable_limit=1024, temp_limit=1024) as budget:
        with use(second):
            assert budget.durable_bytes == 700
        with pytest.raises(ValueError, match="combined_disk"):
            write_tree(first, [{"body": "x" * 500}])
