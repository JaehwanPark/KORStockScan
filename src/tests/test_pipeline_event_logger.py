import json
from types import SimpleNamespace

from src.utils import pipeline_event_logger as logger_mod


def test_emit_pipeline_event_writes_text_and_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "sell_completed",
        record_id=77,
        fields={"reason": "time stop", "profit_rate": "+0.5"},
    )

    assert emitted_messages
    assert emitted_messages[0].startswith("[HOLDING_PIPELINE] 테스트종목(123456) stage=sell_completed")
    assert "id=77" in emitted_messages[0]
    assert "reason=time|stop" in emitted_messages[0]

    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    assert out_path.exists()
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["schema_version"] == 3
    assert rows[0]["pipeline"] == "HOLDING_PIPELINE"
    assert rows[0]["record_id"] == 77
    assert rows[0]["fields"]["reason"] == "time stop"
