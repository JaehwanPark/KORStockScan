from __future__ import annotations

import json
from types import SimpleNamespace
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from src.engine.scalping.micro_reversion.contracts import HorizonOutcome
from src.engine.scalping.micro_reversion.replay import (
    ReplayConfig,
    replay_paths,
    resolve_target_date_path,
)
from src.engine.scalping.micro_reversion.report import (
    _common_maturity_cohorts,
    _decision_status,
    build_report,
    write_report,
)
from src.engine.scalping.micro_reversion.symbol_master import (
    SymbolMasterRecord,
    VerifiedSymbolMaster,
)
from src.engine.scalping.micro_reversion.tax import InstrumentType, ListingMarket


def _row(code: str, observed_at: datetime, price: float) -> dict:
    return {
        "stage": "scalping_scanner_fast_precheck",
        "stock_code": code,
        "emitted_at": observed_at.isoformat(),
        "fields": {
            "current_price_observed": str(price),
            "venue": "KRX",
            "best_bid": str(price - 1),
            "best_ask": str(price),
            "quote_age_ms": "100",
        },
    }


def _write_fixture(path: Path) -> None:
    start = datetime.fromisoformat("2026-08-07T09:00:00+09:00")
    rows = [_row("000001", start, 10_000), _row("005930", start, 100_000)]
    rows.append(_row("000001", start + timedelta(seconds=5), 9_950))
    rows.append(_row("005930", start + timedelta(seconds=5), 99_000))
    for offset_sec in range(10, 606, 5):
        rows.append(_row("000001", start + timedelta(seconds=offset_sec), 10_000))
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


def test_replay_uses_all_symbols_and_builds_10_minute_report(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pipeline_events_2026-08-07.jsonl"
    _write_fixture(source)

    result = replay_paths([source], config=ReplayConfig())
    report = build_report(result)

    assert report["schema"] == "scalp_micro_reversion_v0_report_v5"
    assert {observation.symbol for observation in result.observations} == {
        "000001",
        "005930",
    }
    assert all(
        observation.price_source_field == "current_price_observed"
        for observation in result.observations
    )
    assert {event.symbol for event in result.events} == {"000001", "005930"}
    assert max(label.mature_horizon_count for label in result.labels) == 7
    assert report["summary"]["raw_bbo_candidate_rows"] > 0
    assert report["summary"]["raw_micro_capture_rows"] == 0
    assert report["summary"]["raw_micro_context_candidate_rows"] == 0
    assert report["decision"]["status"] == "v0_insufficient_mature_sample"
    assert report["decision"]["gross_reversion_hypothesis_supported"] is True
    assert report["decision"]["execution_economics_resolved"] is False
    assert report["decision"]["applied_to_sim"] is False
    assert report["decision"]["broker_order_forbidden"] is True
    assert report["decision"]["tax_classification_complete"] is False
    assert report["horizon_metrics"]["600"]["sample_count"] == 1
    assert report["cost_model"]["zero_bps_semantics"] == (
        "friction_free_not_slippage_only"
    )
    sensitivity_600 = report["cost_sensitivity"]["600"]
    assert sensitivity_600["break_even_all_in_cost_bps"] == pytest.approx(
        50.251256, abs=1e-6
    )
    assert [row["all_in_cost_bps"] for row in sensitivity_600["scenarios"]] == [
        0.0,
        5.0,
        10.0,
        15.0,
        20.0,
        23.0,
    ]
    assert (
        report["source_quality"]["input_stats"]["conservative_total_cost_bps"] == 23.0
    )
    assert report["common_maturity_cohorts"]["through_60s"]["common_event_count"] == 1
    assert {
        row["sample_count"]
        for row in report["common_maturity_cohorts"]["through_60s"]["metrics"].values()
    } == {1}

    json_path, markdown_path, manifest_path = write_report(
        report, output_root=tmp_path / "report"
    )
    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["decision"]["runtime_effect"] is False
    assert "actual_order_submitted: `false`" in markdown_path.read_text(
        encoding="utf-8"
    )
    assert json.loads(manifest_path.read_text())["report_schema_version"] == (
        "scalp_micro_reversion_v0_report_v5"
    )


def test_prebaseline_custom_input_is_excluded(tmp_path: Path) -> None:
    source = tmp_path / "pipeline_events_2026-06-04.jsonl"
    source.write_text(
        json.dumps(
            _row(
                "000001",
                datetime.fromisoformat("2026-06-04T09:00:00+09:00"),
                10_000,
            )
        ),
        encoding="utf-8",
    )

    result = replay_paths([source])

    assert result.input_stats.prebaseline_row_count == 1
    assert result.observations == ()
    assert result.events == ()
    with pytest.raises(ValueError, match="clean tuning baseline"):
        resolve_target_date_path(date(2026, 6, 4))


def test_clean_baseline_is_compared_in_kst_not_utc(tmp_path: Path) -> None:
    source = tmp_path / "pipeline_events_2026-06-05.jsonl"
    source.write_text(
        json.dumps(
            _row(
                "000001",
                datetime.fromisoformat("2026-06-05T00:30:00+09:00"),
                10_000,
            )
        ),
        encoding="utf-8",
    )

    result = replay_paths(
        [source],
        config=ReplayConfig(session_start=time(0, 0), session_end=time(1, 0)),
    )

    assert result.input_stats.prebaseline_row_count == 0
    assert result.input_stats.deduplicated_observation_count == 1


def test_raw_micro_capture_is_separate_from_complete_micro_context(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pipeline_events_2026-08-07.jsonl"
    row = _row(
        "000001",
        datetime.fromisoformat("2026-08-07T09:00:00+09:00"),
        10_000,
    )
    row["fields"].pop("best_bid")
    row["fields"].pop("best_ask")
    row["fields"]["ofi"] = "1.25"
    source.write_text(json.dumps(row), encoding="utf-8")

    result = replay_paths([source])

    assert result.input_stats.raw_micro_capture_rows == 1
    assert result.input_stats.raw_micro_context_candidate_rows == 0


def test_report_keeps_no_event_dates_in_walk_forward_denominator(
    tmp_path: Path,
) -> None:
    event_day = tmp_path / "pipeline_events_2026-08-07.jsonl"
    no_event_day = tmp_path / "pipeline_events_2026-08-06.jsonl"
    _write_fixture(event_day)
    no_event_day.write_text(
        json.dumps(
            _row(
                "000001",
                datetime.fromisoformat("2026-08-06T09:00:00+09:00"),
                10_000,
            )
        ),
        encoding="utf-8",
    )

    report = build_report(replay_paths([event_day, no_event_day]))

    assert report["summary"]["trade_date_count"] == 2
    assert [row["trade_date"] for row in report["daily_metrics"]] == [
        "2026-08-06",
        "2026-08-07",
    ]
    assert report["daily_metrics"][0]["mature_300s_count"] == 0


def test_common_maturity_comparison_uses_identical_events_per_group() -> None:
    def label(complete_through: int) -> SimpleNamespace:
        return SimpleNamespace(
            outcomes=tuple(
                HorizonOutcome(
                    horizon_sec=horizon,
                    complete=horizon <= complete_through,
                    terminal_return_bps=float(horizon),
                    cost_adjusted_terminal_return_bps=float(horizon - 23),
                )
                for horizon in (15, 30, 60, 120, 180, 300, 600)
            )
        )

    cohorts = _common_maturity_cohorts(
        SimpleNamespace(labels=(label(30), label(60), label(180)))
    )

    assert cohorts["through_30s"]["common_event_count"] == 3
    assert cohorts["through_60s"]["common_event_count"] == 2
    assert cohorts["through_180s"]["common_event_count"] == 1
    assert {
        metric["sample_count"] for metric in cohorts["through_60s"]["metrics"].values()
    } == {2}


def test_replay_applies_verified_symbol_tax_metadata(tmp_path: Path) -> None:
    source = tmp_path / "pipeline_events_2026-08-07.jsonl"
    _write_fixture(source)

    report = build_report(
        replay_paths(
            [source],
            config=ReplayConfig(
                verified_symbol_master=VerifiedSymbolMaster(
                    [
                        SymbolMasterRecord(
                            symbol="A000001",
                            listing_market=ListingMarket.KOSDAQ,
                            instrument_type=InstrumentType.EQUITY,
                            instrument_tax_class=("ordinary_taxable_equity_20bps"),
                            effective_from=date(2026, 1, 1),
                            effective_to=None,
                            metadata_source="test_official_fixture",
                            source_reference="fixture:sha256:abc",
                            verified_at="2026-08-08T10:00:00+09:00",
                        ),
                        SymbolMasterRecord(
                            symbol="A005930",
                            listing_market=ListingMarket.KOSPI,
                            instrument_type=InstrumentType.EQUITY,
                            instrument_tax_class=("ordinary_taxable_equity_20bps"),
                            effective_from=date(2026, 1, 1),
                            effective_to=None,
                            metadata_source="test_official_fixture",
                            source_reference="fixture:sha256:def",
                            verified_at="2026-08-08T10:00:00+09:00",
                        ),
                    ]
                )
            ),
        )
    )

    assert report["decision"]["tax_classification_complete"] is True
    tax_policy = report["cost_model"]["statutory_tax_policy"]
    assert tax_policy["classified_event_count"] == 2
    assert tax_policy["verified_metadata_event_count"] == 2
    assert tax_policy["instrument_tax_class_counts"] == {
        "ordinary_taxable_equity_20bps": 2
    }
    assert tax_policy["exact_sample_gate_status"] == (
        "statutory_tax_only_positive_non_tax_costs_unresolved"
    )


def test_replay_excludes_non_object_json_rows(tmp_path: Path) -> None:
    source = tmp_path / "pipeline_events_2026-08-07.jsonl"
    source.write_text("[]\n", encoding="utf-8")

    result = replay_paths([source])

    assert result.input_stats.invalid_json_count == 1
    assert result.observations == ()


def test_replay_does_not_consult_manual_control_exclusion(tmp_path: Path) -> None:
    source = tmp_path / "pipeline_events_2026-08-07.jsonl"
    _write_fixture(source)

    result = replay_paths([source])

    assert {observation.symbol for observation in result.observations} == {
        "000001",
        "005930",
    }


def test_positive_gross_negative_selected_cost_is_execution_unresolved() -> None:
    status = _decision_status(
        event_count=100,
        fully_mature_event_count=10,
        gross_reversion_supported=True,
        primary_ev_pct=-0.01,
        mature_coverage_rate=0.1,
        trade_date_count=5,
        positive_day_count=0,
        max_date_ev_contribution_rate=0.5,
        eligible_positive_parent_count=0,
    )

    assert status == "v0_gross_edge_cost_sensitive_execution_unresolved"


def test_non_positive_gross_primary_ev_is_rejected() -> None:
    status = _decision_status(
        event_count=100,
        fully_mature_event_count=100,
        gross_reversion_supported=False,
        primary_ev_pct=-0.02,
        mature_coverage_rate=1.0,
        trade_date_count=5,
        positive_day_count=0,
        max_date_ev_contribution_rate=0.2,
        eligible_positive_parent_count=0,
    )

    assert status == "v0_reject_non_positive_gross_300s_ev"


def test_taxable_equity_aggregate_gate_failure_keeps_subcohort_discovery_open() -> None:
    status = _decision_status(
        event_count=2_399,
        fully_mature_event_count=99,
        gross_reversion_supported=True,
        primary_ev_pct=-0.151012,
        mature_coverage_rate=0.041267,
        trade_date_count=5,
        positive_day_count=0,
        max_date_ev_contribution_rate=0.462022,
        eligible_positive_parent_count=0,
        aggregate_taxable_equity_economic_gate_passed=False,
    )

    assert status == (
        "v0_aggregate_taxable_equity_gate_failed_" "subcohort_execution_unresolved"
    )


def test_removed_entry_odds_surfaces_and_no_runtime_authority_imports() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    removed_paths = (
        "src/engine/scalping/entry_odds",
        "src/tests/test_entry_odds_history.py",
        "src/tests/test_entry_odds_observer.py",
        "src/tests/test_entry_odds_producer.py",
    )
    assert all(not (repository_root / path).exists() for path in removed_paths)

    package_root = repository_root / "src/engine/scalping/micro_reversion"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package_root.glob("*.py"))
    ).lower()
    forbidden_imports = (
        "import src.trading",
        "from src.trading",
        "import src.engine.ai",
        "from src.engine.ai",
        "import src.engine.lifecycle",
        "from src.engine.lifecycle",
    )
    assert all(token not in source for token in forbidden_imports)
