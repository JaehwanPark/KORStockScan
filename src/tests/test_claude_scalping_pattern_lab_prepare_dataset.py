import json

import pandas as pd

from analysis.claude_scalping_pattern_lab import build_claude_payload as payload
from analysis.claude_scalping_pattern_lab import prepare_dataset as prepare


def test_claude_pattern_lab_jsonl_fallback_is_streaming(monkeypatch, tmp_path):
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    target = "2026-05-14"
    path = event_dir / f"pipeline_events_{target}.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "holding_started",
                        "record_id": 1,
                        "stock_code": "005930",
                        "emitted_at": f"{target}T09:00:00",
                        "fields": {},
                    }
                ),
                json.dumps(
                    {
                        "stage": "position_rebased_after_fill",
                        "record_id": 1,
                        "stock_code": "005930",
                        "emitted_at": f"{target}T09:00:01",
                        "fields": {
                            "fill_qty": "1",
                            "cum_filled_qty": "1",
                            "requested_qty": "1",
                            "fill_quality": "FULL_FILL",
                            "entry_mode": "normal",
                        },
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(prepare, "PIPELINE_EVENT_DIR", event_dir)
    monkeypatch.setattr(prepare, "USE_DUCKDB_PRIMARY", False)

    rows, source = prepare._load_pipeline_rows(target)

    assert source == "jsonl:.jsonl"
    assert not isinstance(rows, list)
    parsed = prepare._stream_sequence_events(rows, target, prepare.SERVER_LOCAL)
    assert len(parsed) == 1
    assert parsed[0]["trade_id"] == 1
    assert parsed[0]["holding_started_count"] == 1
    assert parsed[0]["rebase_count"] == 1


def test_claude_pattern_lab_duckdb_query_is_column_bounded(monkeypatch):
    captured = {}

    class _FakeFrame:
        empty = True

        def to_dict(self, orient):
            return []

    class _FakeRepo:
        def __init__(self, read_only=False):
            self.read_only = read_only

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return None

        def register_parquet_dataset(self, dataset):
            return True

        def query(self, sql, params):
            captured["sql"] = sql
            captured["params"] = params
            return _FakeFrame()

    monkeypatch.setattr(prepare, "DUCKDB_AVAILABLE", True)
    monkeypatch.setattr(prepare, "TuningDuckDBRepository", _FakeRepo)
    monkeypatch.setattr(prepare, "_DUCKDB_VIEW_READY", False)

    assert prepare._load_pipeline_rows_from_duckdb("2026-05-14") == []
    sql = " ".join(captured["sql"].split())

    assert "SELECT *" not in sql
    assert "stage IN" in sql
    assert "fields_json" not in sql
    assert captured["params"][0] == "2026-05-14"


def test_claude_pattern_lab_empty_input_overwrites_trade_fact_with_header(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    stale_path = output_dir / "trade_fact.csv"
    stale_path.write_text("stale_col\nstale\n", encoding="utf-8")

    monkeypatch.setattr(prepare, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        prepare, "_load_snapshot_payload", lambda *_args, **_kwargs: (None, "missing")
    )

    df = prepare.build_trade_fact()

    assert df.empty
    written = pd.read_csv(stale_path)
    assert list(written.columns) == prepare.TRADE_FACT_COLUMNS
    assert len(written) == 0


def test_source_manifest_requires_krx_trading_days_not_calendar_days(
    monkeypatch, tmp_path
):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    monkeypatch.setattr(prepare, "OUTPUT_DIR", output_dir)

    prepare.write_source_manifest(
        {
            "pipeline_source_stats": {"duckdb": 2, "none": 2},
            "non_trading_pipeline_source_stats": {"jsonl:.jsonl.gz": 1},
            "covered_dates": ["2026-07-17", "2026-07-18", "2026-07-20"],
            "expected_dates": ["2026-07-17", "2026-07-20"],
        }
    )

    manifest = json.loads((output_dir / "source_manifest.json").read_text())
    assert manifest["history_coverage_ok"] is True
    assert manifest["expected_trading_date_count"] == 2
    assert manifest["covered_expected_trading_date_count"] == 2
    assert manifest["missing_expected_trading_dates"] == []
    assert manifest["observed_non_trading_dates"] == ["2026-07-18"]
    assert manifest["non_trading_pipeline_source_stats"] == {"jsonl:.jsonl.gz": 1}


def test_source_manifest_surfaces_missing_krx_trading_day(monkeypatch, tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    monkeypatch.setattr(prepare, "OUTPUT_DIR", output_dir)

    prepare.write_source_manifest(
        {
            "pipeline_source_stats": {"duckdb": 1, "none": 1},
            "covered_dates": ["2026-07-20"],
            "expected_dates": ["2026-07-17", "2026-07-20"],
        }
    )

    manifest = json.loads((output_dir / "source_manifest.json").read_text())
    assert manifest["history_coverage_ok"] is False
    assert manifest["missing_expected_trading_dates"] == ["2026-07-17"]


def test_run_manifest_preserves_trading_day_coverage_provenance(monkeypatch, tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    monkeypatch.setattr(payload, "OUTPUT_DIR", output_dir)
    source_manifest = {
        "data_source_mode": "mixed",
        "history_coverage_start": "2026-06-05",
        "history_coverage_end": "2026-07-31",
        "history_coverage_ok": False,
        "expected_trading_date_count": 40,
        "covered_expected_trading_date_count": 39,
        "missing_expected_trading_dates": ["2026-07-17"],
        "observed_non_trading_dates": ["2026-06-13"],
        "local_pipeline_source_stats": {"duckdb": 39, "none": 1},
        "non_trading_pipeline_source_stats": {"jsonl:.jsonl.gz": 1},
    }
    (output_dir / "source_manifest.json").write_text(json.dumps(source_manifest))

    empty = pd.DataFrame()
    payload.write_run_manifest(empty, empty, empty)

    manifest = json.loads((output_dir / "run_manifest.json").read_text())
    assert manifest["missing_expected_trading_dates"] == ["2026-07-17"]
    assert manifest["expected_trading_date_count"] == 40
    assert manifest["covered_expected_trading_date_count"] == 39
    assert manifest["non_trading_pipeline_source_stats"] == {"jsonl:.jsonl.gz": 1}


def test_claude_payload_feedback_selector_uses_daily_clean_baseline_artifacts(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "data" / "report"
    ev_dir = report_dir / "threshold_cycle_ev"
    ev_dir.mkdir(parents=True)
    (ev_dir / "threshold_cycle_ev_2026-06-06_rolling5d.json").write_text(
        "{}", encoding="utf-8"
    )
    (ev_dir / "threshold_cycle_ev_2026-06-03.json").write_text("{}", encoding="utf-8")
    (ev_dir / "threshold_cycle_ev_2026-06-04.json").write_text("{}", encoding="utf-8")
    (ev_dir / "threshold_cycle_ev_2026-06-05.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(payload, "REPORT_DIR", report_dir)

    path, source_date = payload._latest_feedback_artifact_path(
        "threshold_cycle_ev",
        "threshold_cycle_ev",
        "2026-06-06",
    )

    assert path == ev_dir / "threshold_cycle_ev_2026-06-05.json"
    assert source_date == "2026-06-05"
