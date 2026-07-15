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


def test_claude_payload_feedback_selector_uses_daily_clean_baseline_artifacts(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "data" / "report"
    ev_dir = report_dir / "threshold_cycle_ev"
    ev_dir.mkdir(parents=True)
    (ev_dir / "threshold_cycle_ev_2026-06-05_rolling5d.json").write_text(
        "{}", encoding="utf-8"
    )
    (ev_dir / "threshold_cycle_ev_2026-06-03.json").write_text("{}", encoding="utf-8")
    (ev_dir / "threshold_cycle_ev_2026-06-04.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(payload, "REPORT_DIR", report_dir)

    path, source_date = payload._latest_feedback_artifact_path(
        "threshold_cycle_ev",
        "threshold_cycle_ev",
        "2026-06-05",
    )

    assert path == ev_dir / "threshold_cycle_ev_2026-06-04.json"
    assert source_date == "2026-06-04"
