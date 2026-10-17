"""Report diagnostics preserve frozen selection and incomplete native evidence."""
import json
from pathlib import Path

import pytest

from src.engine.automation import pre_submit_delay_partitioned_research as partitioned
from src.engine.automation import pre_submit_delay_research_review as review
from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import pre_submit_delay_initial_policy as initial


def _committed(tmp_path, *, missing_identity=False, with_short=False):
    data = tmp_path / "data"
    candidate = tmp_path / "candidate"
    rows = []
    for anchor in ("price_ready", "signal_ready"):
        for n in range(6):
            at = 1792112400.0 + n * 600
            row = dict(identity=initial.digest([anchor, n]), alias=["2026-10-16", f"{n+1:06d}", anchor+str(n)],
                anchor_kind=anchor, session="REGULAR", parent_compatibility=["a"*64, "b"*64],
                native_evaluation_bound=True, committed_at=at, observation_end_at=at+183,
                p0_valid=True, situation="test_situation", execution_context="ALL",
                decision_source_sha256=initial.digest(["decision", anchor, n]),
                pairs={"30": (100 if n == 0 else -10), "60": 5},
                execution_features={"p0_ask": 10000, "p0_bid": 9995,
                                    "original_signal_reference_price": 9900})
            if n == 1:
                row["pairs"].pop("60")
            if not missing_identity:
                row["original_machine_observation_sha256"] = initial.digest(["machine", n])
                row["native_evaluation_attempt_id"] = "native:" + str(n)
            if with_short:
                row.update(research_short_p0_valid=True, research_short_pairs={"1": 2})
            rows.append(row)
    report, policy = partitioned.build(rows,
        dict(raw_commit_n=12, qualified_pass_n=12, p0_valid_n=12,
             native_evaluation_unverified_n=0, parent_compatibility_unverified_n=0, exclusions={}),
        output_root=candidate, source_date="2026-10-16", publication_date="2026-10-16",
        effective_date="2026-10-19", source_sha256="c"*64, code_contract_sha256="d"*64,
        source_receipt={})
    generation = initial.digest([report, policy])
    base = data / "threshold_cycle/pre_submit_delay_policy/generations" / generation
    base.mkdir(parents=True)
    partitioned.copy_evidence(report, base)
    for name, value in (("report", report), ("policy", policy)):
        (base / (name + ".json")).write_bytes(storage.encoded(value))
    manifest = dict(schema=initial.MANIFEST_SCHEMA, source_date="2026-10-16", generation=generation,
                    source_sha256="c"*64, code_contract_sha256="d"*64,
                    report_artifact_sha256=initial.digest(report), policy_artifact_sha256=initial.digest(policy))
    manifest["manifest_sha256"] = initial.digest(manifest)
    pointer = base.parent.parent / "committed_2026-10-16.json"
    pointer.write_bytes(storage.encoded(manifest))
    return data, base, report, policy


def test_all_sharded_cells_frozen_membership_sparse_pairs_and_native_opportunities(tmp_path):
    data, base, original, policy = _committed(tmp_path)
    before = {str(p): p.read_bytes() for p in data.rglob("*.json")}
    output = tmp_path / "review"
    result = review.generate(data, "2026-10-16", output)
    assert result["census"]["anchors"] == 12
    assert result["unique_independent_opportunities"] == 6
    assert result["census"]["horizon_pairs"] == 22
    assert result["cells_ref"]["count"] == original["cells_ref"]["count"] == 4
    assert result["runtime_effect"] is False
    cells = list(storage.iter_tree(output, result["cells_ref"]))
    cell = next(c for c in cells if c["original_cell"]["anchor_kind"] == "price_ready")
    assert cell["original_cell"]["comparison_delay_sec"] == 30
    # The training winner fails holdout. This diagnostic cannot switch to 60.
    assert cell["selected_delay_sec"] == 0
    assert cell["selection_reason_normalized"] == "training_holdout_direction_not_confirmed"
    assert cell["candidates"]["30"]["train"]["n"] == 4
    assert cell["candidates"]["60"]["train"]["n"] == 3
    overlap = next(p for p in cell["pairwise_common_cohort"] if p["split"] == "train")
    assert overlap["left"]["n"] == overlap["right"]["n"] == 3
    original_members = {r["identity"]: r["split"] for part in storage.iter_tree(base, original["partitions_ref"])
                        for r in storage.iter_tree(base, part["membership"])}
    actual_members = {r["identity"]: r["split"] for r in storage.iter_tree(output, result["frozen_membership_ref"])}
    assert actual_members == original_members
    assert before == {str(p): p.read_bytes() for p in data.rglob("*.json")}
    assert result["original_policy_status"] == policy["selection_status"]


def test_anchor_counts_do_not_become_independent_opportunities_when_identity_missing(tmp_path):
    data, _, _, _ = _committed(tmp_path, missing_identity=True)
    result = review.generate(data, "2026-10-16", tmp_path / "review")
    assert result["unique_independent_opportunities"] is None
    assert result["known_identity_subset_unique_opportunities"] == 0
    assert result["independent_identity_status"] == "partial_native_identity_not_preserved"
    assert result["compact_enrichment"]["status"] == "unavailable"


def test_short_diagnostics_are_visible_without_reselecting_the_committed_policy(tmp_path):
    data, _, _, _ = _committed(tmp_path, with_short=True)
    result = review.generate(data, "2026-10-16", tmp_path / "review")
    assert result["horizons_sec"] == [1, 30, 60]
    cell = next(storage.iter_tree(tmp_path / "review", result["cells_ref"]))
    assert cell["candidates"]["1"]["train"]["mean_bp"] == 2
    assert cell["original_cell"]["candidate_delays_sec"] == [30, 60]
    groups = list(storage.iter_tree(tmp_path / "review", result["feature_groups_ref"]))
    assert {r["feature"] for r in groups} == {"original_signal_price_progress", "p0_spread_bp"}
    assert all(r["selection_authority"] is False for r in groups)


def test_tampered_projection_shard_rejected_and_complete_report_not_written(tmp_path):
    data, base, report, _ = _committed(tmp_path)
    path = base / report["qualified_projection_ref"]["path"]
    path.write_text("{}")
    with pytest.raises(ValueError, match="research_shard_generation_changed"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review/report.json").exists()


def test_bounds_and_output_source_overlap_fail_before_writing_complete_report(tmp_path, monkeypatch):
    data, base, _, _ = _committed(tmp_path)
    with pytest.raises(ValueError, match="overlaps_policy_source"):
        review.generate(data, "2026-10-16", base / "review")
    monkeypatch.setattr(review, "MAX_ANCHORS", 3)
    with pytest.raises(ValueError, match="evidence_count_or_budget_invalid"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review").exists()


def test_compact_enrichment_checks_exact_receipt_and_never_reads_unlisted_sources(tmp_path):
    data, _, _, _ = _committed(tmp_path)
    # Direct compact-index test avoids manufacturing a new committed selection.
    from src.engine.lifecycle.holding_window_generation import byte_generation
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    path.write_text('{"changed": true}\n')
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)


def test_same_target_output_is_immutable_and_reproducible(tmp_path):
    data, _, _, _ = _committed(tmp_path)
    output = tmp_path / "review"
    first = review.generate(data, "2026-10-16", output)
    assert first == review.generate(data, "2026-10-16", output)
    broken = json.loads((output / "report.json").read_bytes())
    broken["source_date"] = "2026-10-15"
    (output / "report.json").write_bytes(storage.encoded(broken))
    with pytest.raises(ValueError, match="immutable_report_conflict"):
        review.generate(data, "2026-10-16", output)


def test_native_identity_conflict_cannot_fabricate_an_independent_opportunity():
    row = dict(native_evaluation_bound=True, alias=["2026-10-16", "005930", "intent"],
               original_machine_observation_sha256="a"*64, native_evaluation_attempt_id="native",
               parent_compatibility=["b"*64, "c"*64], independent_opportunity_sha256="d"*64)
    with pytest.raises(ValueError, match="independent_identity_mismatch"):
        review._independent_identity(row)
    row["native_evaluation_bound"] = False
    assert review._independent_identity(row) is None


def test_compact_budget_is_explicitly_unavailable_without_opening_large_source(tmp_path):
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-large.jsonl"
    report = {"source_receipt": {"partition_generations": {
        str(path): {"size": review.MAX_COMPACT_BYTES + 1, "sha256": "a"*64}}}}
    with storage.index(tmp_path / "index") as db:
        result = review._compact_index(db, data, report)
    assert result["status"] == "unavailable"
    assert result["reason"] == "receipt_bound_compact_budget_exceeded"
    assert result["bytes_read"] == result["records_decoded"] == 0


def test_identified_bad_compact_rows_do_not_hide_an_exact_native_identity(tmp_path):
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.pipeline_event_summary import execution_projection_identity
    from src.engine.scalping import pre_submit_delay_tuning as owner
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    fields = dict(delay_intent_id="intent", original_machine_observation_sha256="a"*64,
                  evaluation_attempt_id="native")
    fields["decision_source_sha256"] = owner.decision_source_sha256(fields)
    event = dict(family="pre_submit_delay", emitted_date="2026-10-16", stock_code="005930",
                 stage="pre_submit_delay_committed", fields=fields)
    event["execution_source_event_sha256"] = execution_projection_identity(event)
    path.write_bytes(b'\xff\n[]\n{"broken":NaN}\n' + storage.encoded(event) + b"\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {
        str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    original = dict(alias=["2026-10-16", "005930", "intent"], p0_valid=False,
                    native_evaluation_bound=True, decision_source_sha256=fields["decision_source_sha256"])
    with storage.index(tmp_path / "index") as db:
        receipt = review._compact_index(db, data, report)
        enriched = review._enrich(db, original, receipt)
    assert receipt["status"] == "complete"
    assert receipt["malformed_records"] == 2
    assert receipt["invalid_event_identity_n"] == 1
    assert receipt["bound_projection_anchors"] == 1
    assert enriched["native_evaluation_attempt_id"] == "native"
    assert "native_evaluation_attempt_id" not in original


def test_declared_small_but_grown_compact_fails_before_any_source_read(tmp_path, monkeypatch):
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    with path.open("wb") as handle:
        handle.truncate(256 * 1024 * 1024)
    report = {"source_receipt": {"partition_generations": {str(path): {"size": 3, "sha256": "a"*64}}}}
    original_open = Path.open
    def checked_open(target, *args, **kwargs):
        if target == path:
            pytest.fail("grown compact source was opened before its size was checked")
        return original_open(target, *args, **kwargs)
    monkeypatch.setattr(Path, "open", checked_open)
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)


def test_compact_append_during_stream_is_bounded_and_rejected(tmp_path, monkeypatch):
    import io
    from src.engine.lifecycle.holding_window_generation import byte_generation
    data = tmp_path / "data"
    path = data / "threshold_cycle/date=2026-10-16/family=pre_submit_delay/part-execution-000.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}\n")
    generation = byte_generation(path)
    report = {"source_receipt": {"partition_generations": {str(path): {k: generation[k] for k in ("size", "sha256")}}}}
    original_open = Path.open
    class AppendingReader(io.BufferedReader):
        def readline(self, size=-1):
            raw = super().readline(size)
            if raw:
                with original_open(path, "ab") as writer:
                    writer.write(b"{}\n")
            return raw
    def wrapped_open(target, *args, **kwargs):
        if target == path and args and args[0] == "rb":
            return AppendingReader(io.FileIO(path, "rb"))
        return original_open(target, *args, **kwargs)
    monkeypatch.setattr(Path, "open", wrapped_open)
    with storage.index(tmp_path / "index") as db:
        with pytest.raises(ValueError, match="compact_generation_changed"):
            review._compact_index(db, data, report)
    assert path.stat().st_size <= 9


@pytest.mark.parametrize("anchor,child_delay,expected_research,expected_lookup", [
    ("price_ready", 0, 0, 0), ("price_ready", None, 30, 30), ("signal_ready", None, 30, 0),
])
def test_exact_parent_fallback_preserves_explicit_zero_and_runtime_anchor_scope(
        tmp_path, anchor, child_delay, expected_research, expected_lookup):
    parents = ["a"*64, "b"*64]
    parent_key = initial.cell_key(anchor, "REGULAR", parents=parents)
    child_key = initial.cell_key(anchor, "REGULAR", "situation", parents=parents)
    parent = dict(anchor_kind=anchor, session="REGULAR", parent_compatibility=parents,
                  delay_sec=30, runtime_apply_allowed=True)
    child = {**parent, "delay_sec": child_delay, "runtime_apply_allowed": child_delay is not None}
    item = dict(key=child_key, value=child)
    with storage.index(tmp_path / "index") as db:
        storage.put(db, "cell:" + parent_key, dict(key=parent_key, value=parent))
        storage.put(db, "cell:" + child_key, item)
        result = review._fallback(db, item, "price_ready")
    assert result["research_cell_or_parent_delay_sec"] == expected_research
    assert result["prepared_policy_lookup_delay_sec"] == expected_lookup
    assert result["resolved_cell_key"] == (child_key if child_delay is not None else parent_key)


def test_durable_output_budget_prevents_complete_report_publication(tmp_path, monkeypatch):
    data, _, _, _ = _committed(tmp_path)
    monkeypatch.setattr(review, "MAX_DURABLE_BYTES", 1)
    with pytest.raises(ValueError, match="research_combined_disk_budget_exceeded"):
        review.generate(data, "2026-10-16", tmp_path / "review")
    assert not (tmp_path / "review/report.json").exists()
