"""Scanner adapter receipts remain bounded, exact and observational."""

import json
from datetime import datetime

import pytest

from src.scanners import scanner_source_census as source
from src.scanners import scalping_scanner as scanner
from src.engine.monitoring import market_opportunity_census as census
from src.tests.test_market_opportunity_census import _write_jsonl


def test_adapter_receipt_conservation_and_consumer_first_gap(monkeypatch, tmp_path):
    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *args, **kw: emitted.append((args, kw))
    )

    @source.observe_cycle
    def run():
        return scanner._fetch_scan_source(
            "fixture", lambda: [{"Code": "005930"}], stex_tp="1"
        )

    # A real adapter accepts kwargs; no request is made.
    @source.observe_cycle
    def run_valid():
        return scanner._fetch_scan_source(
            "fixture", lambda **kw: [{"Code": "005930"}], stex_tp="1"
        )

    assert run() == []
    assert (
        "fetch_exception:TypeError" == emitted[-1][1]["fields"]["scanner_source_status"]
    )
    result = run_valid()
    assert result[0]["Code"] == "005930"
    args, kw = emitted[-1]
    fields = {k: str(v) for k, v in kw["fields"].items()}
    assert source.decode_receipt(fields) == [{"stock_code": "005930", "venue": "KRX"}]
    at = datetime(2026, 9, 9, 10, tzinfo=census.KST)
    path = tmp_path / "source.jsonl"
    _write_jsonl(
        path,
        [
            {
                "stage": args[3],
                "stock_code": "",
                "emitted_at": at.isoformat(),
                "fields": fields,
            }
        ],
    )
    receipts = []
    index = census._load_stage_index(
        path,
        tmp_path / "absent.jsonl",
        target_date="2026-09-09",
        scanner_source_receipts=receipts,
    )
    row = census._coverage_row(
        {
            "stock_code": "005930",
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "first_census_at": at,
        },
        index,
        after=at,
        before=None,
        require_venue=True,
        require_lineage=True,
    )
    assert row["terminal_coverage_reason"] == "scanner_fetch_seen_pool_unobserved"
    assert row["source_fetch_observed_exact"]
    assert receipts[0]["contract_valid"]
    for key, value in (
        ("runtime_effect", "true"),
        ("scanner_source_input_count", "2"),
        ("scanner_source_input_count", 1.5),
        ("scanner_source_input_count", True),
        ("scanner_source_rows_sha256", "bad"),
    ):
        assert source.decode_receipt({**fields, key: value}) is None


def test_bounded_rows_do_not_change_original_candidates(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    targets = [{"Code": f"{i:06d}"} for i in range(1100)]
    source.observe_cycle(source.observe_fetch)("fixture", targets, status="returned")
    fields = emitted[0]
    assert len(source.decode_receipt(fields)) == source.MAX_ROWS
    assert fields["scanner_source_omitted_count"] == 76
    assert len(targets) == 1100
    assert all(r["venue"] == "UNKNOWN" for r in source.decode_receipt(fields))


def test_telemetry_failure_does_not_veto_fetch_or_pool(monkeypatch):
    def fail(*a, **kw):
        raise OSError("fixture sink failure")

    monkeypatch.setattr(source, "emit_pipeline_event", fail)
    assert (
        scanner._fetch_scan_source("fixture", lambda: [{"Code": "005930"}])[0]["Code"]
        == "005930"
    )
    assert not source.observe_pool([{"Code": "005930"}], generation="gen")


def test_empty_adapter_is_not_assumed_valid_empty_market(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    assert source.observe_cycle(scanner._fetch_scan_source)("fixture", lambda: []) == []
    assert (
        emitted[0]["scanner_source_status"] == "empty_adapter_return_unproven_upstream"
    )
    assert source.decode_receipt(emitted[0]) == []


def test_source_quality_owner_validates_receipt(monkeypatch):
    from src.engine import observation_source_quality_audit as audit

    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    source.observe_pool(
        [{"Code": "005930", "ScannerSourceVenues": {"KRX"}}], generation="G1"
    )
    stage = "scalping_scanner_candidate_pool_census"
    contract = audit.STAGE_CONTRACTS[stage]
    result = audit._row_contract_violations(stage, {"fields": emitted[0]}, contract)
    assert not any(result.values()), result


def test_unbound_cycle_cannot_be_used_as_exact_fetch(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    source.observe_fetch("fixture", [{"Code": "005930"}], status="returned")
    assert source.decode_receipt(emitted[0]) is None


def test_pool_rejects_only_identifiable_invalid_code(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    source.observe_pool([None, {"Code": "bad"}, {"Code": "005930"}], generation="G1")
    assert emitted[0]["scanner_source_input_count"] == 3
    assert emitted[0]["scanner_source_rejected_count"] == 2
    assert source.decode_receipt(emitted[0])[0]["stock_code"] == "005930"


def test_independent_stage_reach_is_not_same_source_cycle_conversion():
    at = datetime(2026, 9, 9, 10, tzinfo=census.KST)
    row = {
        "ts": at,
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "scanner_source_cycle_id": "A",
    }
    index = {
        "005930": {
            "source_seen": [row],
            "candidate_evaluated": [{**row, "scanner_source_cycle_id": "B"}],
        }
    }
    episode = {
        "stock_code": "005930",
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "first_census_at": at,
    }
    result = census._coverage_row(
        episode, index, after=at, require_venue=True, require_lineage=True
    )
    assert result["source_pool_cycle_join"]["matched_cycle_ids"] == []
    index["005930"]["candidate_evaluated"][0]["scanner_source_cycle_id"] = "A"
    result = census._coverage_row(
        episode, index, after=at, require_venue=True, require_lineage=True
    )
    assert result["source_pool_cycle_join"]["matched_cycle_ids"] == ["A"]


@pytest.mark.parametrize(
    "code,request_venue,expected",
    [
        ("005930_NX", "KRX", "UNKNOWN"),
        ("005930_NX", "NXT", "NXT"),
        ("005930_AL", "KRX", "UNKNOWN"),
        ("005930", "UNKNOWN", "UNKNOWN"),
    ],
)
def test_physical_route_conflict_never_overrides_request(code, request_venue, expected):
    assert source.source_target_venue(code, request_venue) == expected


def test_source_batch_is_not_duplicated_or_dropped_in_logger(monkeypatch):
    from src.utils import pipeline_event_logger as logger

    emitted = []
    monkeypatch.setattr(
        source, "emit_pipeline_event", lambda *a, **kw: emitted.append(kw["fields"])
    )
    source.observe_pool(
        [{"Code": "005930", "ScannerSourceVenues": {"KRX"}}], generation="G1"
    )
    fields = {k: str(v) for k, v in emitted[0].items()}
    stage = "scalping_scanner_candidate_pool_census"
    assert "scanner_source_rows_json" not in logger._project_fields_for_text(
        stage, fields
    )
    assert source.decode_receipt(
        logger._project_fields_for_compact_stream(stage, fields)
    )
