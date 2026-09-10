"""Direct gateway and optional report consumer; no broker/network access."""

import hashlib
import importlib
import json
from types import SimpleNamespace

import pytest

from src.engine.monitoring.entry_adverse_flow_summary import build_summary
from src.tests.test_entry_adverse_flow import NOW, SCOPE, tape, source
from src.trading.market.entry_adverse_flow import CONTRACT, evaluate_snapshot
from src.trading.order import (
    entry_adverse_guard as guard,
    entry_adverse_owners as owners,
)


@pytest.mark.parametrize(
    "module,klass",
    [
        ("widget_auto_trade", "KiwoomSharedTokenOrderGateway"),
        ("samsung_morning_one_share", "KiwoomOneShareGateway"),
        ("samsung_midday_one_share", "KiwoomMiddayOneShareGateway"),
        ("samsung_afternoon_one_share", "KiwoomAfternoonOneShareGateway"),
        ("low_price_two_leg", "KiwoomLowPriceTwoLegGateway"),
    ],
)
def test_real_gateway_hook_runs_after_token_and_before_wire(monkeypatch, module, klass):
    mod = importlib.import_module(f"src.trading.{module}.gateway")
    events = []

    class Session:
        def post(self, *a, **k):
            events.append("wire")
            raise AssertionError("wire_forbidden")

    def token():
        events.append("token_wait_finished")
        return "isolated-test-token"

    monkeypatch.setattr(
        mod.kiwoom_utils, "resolve_kiwoom_request_token", lambda value: value
    )
    kwargs = dict(request_session=Session(), token_loader=token)
    if module == "low_price_two_leg":
        kwargs["symbol"] = next(iter(mod.ALLOWED_SYMBOLS))
    gateway = getattr(mod, klass)(**kwargs)

    def veto():
        events.append("last_veto")
        raise guard.EntryNotSent("late_adverse")

    with guard.transport_check(veto), pytest.raises(guard.EntryNotSent):
        gateway._post(endpoint="/api/dostk/ordr", api_id="kt10000", payload={})
    assert events == ["token_wait_finished", "last_veto"]


def test_latest_receipt_must_match_actual_window_endpoint():
    data = tape(adverse=False)
    source(data)["realtime_types"]["0D"]["route_sequence"] += 1
    kwargs = dict(
        snapshot=data,
        symbol="005930",
        route="SOR",
        cutoff_ms=int(NOW.timestamp() * 1000),
    )
    assert evaluate_snapshot(**kwargs)["action"] == "CONTINUE"
    assert (
        evaluate_snapshot(**kwargs, require_latest=True)["action"]
        == "SOURCE_UNAVAILABLE"
    )


def holder(action="WAIT"):
    return {
        guard.KEY: dict(
            contract=CONTRACT,
            identity="one-signal",
            scope=SCOPE,
            signal_at=NOW.isoformat(),
            action=action,
        )
    }


def test_receipt_dedup_conservation_and_economic_null(tmp_path, monkeypatch):
    monkeypatch.setenv(
        owners.EVENT_ROOT_ENV, str(tmp_path / "entry_adverse_flow_events")
    )
    h = holder()
    owners.record(h)
    owners.record(h)
    h[guard.KEY]["action"] = "TRANSPORT_STARTED"
    owners.record(h)
    result = build_summary(target_date=NOW.date().isoformat(), report_root=tmp_path)
    assert result["conservation_ok"] and result["observed_guard_identity_count"] == 1
    assert result["counts"] == {"transport_started": 1}
    assert (
        result["net_profit_krw"] is None and result["notional_weighted_ev_pct"] is None
    )
    assert (
        result["runtime_effect"] is False and result["allowed_runtime_apply"] is False
    )


@pytest.mark.parametrize("bad", ["hash", "date", "action", "json"])
def test_invalid_receipt_isolated(tmp_path, monkeypatch, bad):
    root = tmp_path / "entry_adverse_flow_events"
    monkeypatch.setenv(owners.EVENT_ROOT_ENV, str(root))
    owners.record(holder())
    path = next(root.iterdir())
    event = json.loads(path.read_text())
    if bad == "hash":
        event["receipt_sha256"] = "0" * 64
    if bad == "date":
        event["target_date"] = "2026-06-01"
    if bad == "action":
        event["state"]["action"] = []
        event["receipt_sha256"] = hashlib.sha256(
            json.dumps(event["state"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    path.write_text("broken" if bad == "json" else json.dumps(event))
    result = build_summary(target_date=NOW.date().isoformat(), report_root=tmp_path)
    assert result["status"] == "source_contract_gap" and not result["conservation_ok"]


def test_optional_absent_and_archive_never_prove_economics(tmp_path):
    assert (
        build_summary(target_date="2026-09-10", report_root=tmp_path)["status"]
        == "not_observed"
    )
    assert (
        build_summary(target_date="2026-06-04", report_root=tmp_path)["status"]
        == "pre_clean_baseline_excluded"
    )


def test_diagnostic_write_failure_does_not_interrupt_order_result(monkeypatch):
    def fail(h):
        raise OSError("disk")

    monkeypatch.setattr(owners, "_record_receipt", fail)
    h = holder("TRANSPORT_STARTED")
    owners.record(h)
    assert h[guard.KEY]["action"] == "TRANSPORT_STARTED"
    assert h[guard.KEY + "_receipt_error"] == "OSError"


def test_corrupt_persisted_clock_cannot_restart_wait(monkeypatch):
    h = holder()
    h[guard.KEY]["signal_at"] = "invalid"
    m = SimpleNamespace(_save=lambda: None)
    assert not owners._prepare(m, h, "one-signal", NOW, SCOPE, "ENTRY", NOW)
    assert h[guard.KEY]["action"] == "SKIP_STATE_INVALID"


def test_parent_attribution_consumes_optional_receipt(tmp_path, monkeypatch):
    from src.engine.monitoring.machine_microstructure_attribution import (
        build_report,
        render_markdown,
    )

    root = tmp_path / "report"
    monkeypatch.setenv(owners.EVENT_ROOT_ENV, str(root / "entry_adverse_flow_events"))
    owners.record(holder("SKIP_ADVERSE_FLOW"))
    report = build_report(
        NOW.date().isoformat(),
        report_root=root,
        observation_root=tmp_path / "observations",
        source_exclusion_manifest_path=tmp_path / "absent.json",
        canary_snapshot_path=None,
        canary_snapshot_dir=tmp_path / "canary",
        widget_state_path=tmp_path / "widget.json",
        now=NOW,
    )
    assert report["entry_adverse_flow"]["counts"] == {"not_sent_terminal": 1}
    assert "Entry Adverse Flow Receipts" in render_markdown(report)
    assert report["authority"]["allowed_runtime_apply"] is False


def test_pending_expiry_not_hidden_by_upstream_wait(tmp_path, monkeypatch):
    monkeypatch.setenv(owners.EVENT_ROOT_ENV, str(tmp_path))
    h = holder()
    h[guard.KEY]["deadline_ms"] = int(NOW.timestamp() * 1000) - 1
    owners.expire_pending(SimpleNamespace(_save=lambda: None), h, NOW)
    assert h[guard.KEY]["action"] == "SKIP_DEADLINE"


def test_unselected_episode_does_not_inherit_widget_source_requirements(
    tmp_path, monkeypatch
):
    from src.trading.config.machine_entry_adverse_policy import PATH_ENV, HASH_ENV

    policy = dict(
        contract=CONTRACT,
        enabled=True,
        valid_from="2026-06-05T00:00:00+09:00",
        valid_until=None,
        scopes=[SCOPE],
        approval_reference="isolated-test",
    )
    raw = json.dumps(policy).encode()
    path = tmp_path / "policy.json"
    path.write_bytes(raw)
    monkeypatch.setenv(PATH_ENV, str(path))
    monkeypatch.setenv(HASH_ENV, hashlib.sha256(raw).hexdigest())
    m = SimpleNamespace(
        entry_timing_owner="episode",
        entry_timing_scope_id="other",
        entry_timing_session="KRX_REGULAR",
        policy=SimpleNamespace(symbol="005930", route="SOR"),
        _state={},
    )
    leg = dict(status="PLANNED", leg_id="L1")
    assert owners.episode_prepare(m, leg, NOW)
    assert leg == dict(status="PLANNED", leg_id="L1")
