"""Permanent retirement boundaries and surviving consumers; no live I/O."""

from dataclasses import replace
from datetime import date, datetime
import json
from pathlib import Path

import pytest

from src.engine.automation import postclose_summary_handoff as handoff
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry, OwnerOrderContext, OwnerRegistryError,
)


def test_historical_owner_context_cannot_reserve_new_orders(tmp_path, monkeypatch):
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY', 'retirement-test-account')
    context = OwnerOrderContext('widget_auto_trade', 'historical', 'historical-position', 'new-intent')
    context.validate()  # Immutable journal identity remains readable.
    registry = OrderOwnerRegistry(tmp_path / 'journal.jsonl')
    assert not registry.path.exists()
    for side in ('BUY', 'SELL'):
        with pytest.raises(OwnerRegistryError, match='permanently_retired'):
            registry.reserve(context=context, symbol='005930', side=side,
                             quantity=10, route='SOR', order_date='2026-10-06')
    assert not registry.path.exists()












def test_rollback_release_cannot_restore_widget_surface(tmp_path):
    from src.engine.infrastructure.runtime_release_router import _validate_retired_surfaces
    root=tmp_path / "release"
    path=tmp_path / "data/runtime/retirements/widget-retirement-2026-10-06.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(schema="widget_retirement_transition_v1", state="terminal", owner="widget_auto_trade")))
    _validate_retired_surfaces(tmp_path, root)
    old=root / "deploy/run_widget_evaluation.sh"
    old.parent.mkdir(parents=True);old.write_text("retired")
    with pytest.raises(ValueError, match="restores_permanently_retired"):
        _validate_retired_surfaces(tmp_path, root)


@pytest.mark.parametrize("day,schema,accepted", [
    ("2026-10-02", "postclose_stage_terminal_v2", True),
    ("2026-10-06", "postclose_stage_terminal_v2", False),
    ("2026-10-06", "postclose_stage_terminal_v3", True),
])
def test_retirement_generation_rejects_old_stage_receipt(tmp_path, day, schema, accepted):
    import hashlib
    from src.engine.error_detectors.artifact_freshness import _semantic_stage_binding
    path=tmp_path / "data/report/postclose_stage_terminal" / day / "legacy_machine_report.json"
    path.parent.mkdir(parents=True)
    body=dict(schema=schema, source_date=day, stage_id="legacy_machine_report", status="succeeded", exit_code=0)
    sha=hashlib.sha256(json.dumps(body,ensure_ascii=True,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(dict(body,receipt_sha256=sha)))
    if accepted:
        assert _semantic_stage_binding(tmp_path, day, "legacy_machine_report")["status"] == "succeeded"
    else:
        with pytest.raises(ValueError, match="identity_or_hash_invalid"):
            _semantic_stage_binding(tmp_path, day, "legacy_machine_report")
