from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from src.engine.lifecycle import broker_cost_source as C
from src.engine.lifecycle.broker_cost_reconciliation import digest, source_generation

DAY = "2026-10-08"
NOW = datetime(2026, 10, 8, 21, tzinfo=C.KST)


def broker_fixture(tmp_path):
    diary = {"stk_cd": "005930", "buy_qty": "2", "sell_qty": "2",
             "buy_amt": "20000", "sell_amt": "20200", "cmsn_alm_tax": "10", "pl_amt": "190"}
    orders = [{"stk_cd": "005930", "ord_no": order, "io_tp_nm": side,
               "cntr_qty": "2", "cntr_pric": price, "oso_qty": "0", "ord_stt": "체결"}
              for order, side, price in (("0000011", "+매수", "10000"), ("0000012", "-매도", "10100"))]
    calls = []
    def transport(api, payload):
        calls.append((api, payload))
        result = {"return_code": 0}
        if api == "ka00001":
            result["acctNo"] = "1234567890"
        elif api == "ka10170":
            result[C.LISTS[api]] = [deepcopy(diary)]
        elif api == "ka10076":
            result[C.LISTS[api]] = deepcopy(orders)
        else:
            result["trst_ovrl_trde_prps_array"] = []
        return [result], {"page_count": 1, "continuous_terminal_received": True}
    source = C.collect(tmp_path, DAY, transport=transport, now=NOW)
    legs = [{"at": DAY + " 10:00:00", "order_no": "11", "execution_no": "1",
             "qty": 2, "price": 10000, "route": "SOR"}]
    sells = [{**legs[0], "at": DAY + " 10:01:00", "order_no": "12", "price": 10100}]
    context = dict(target_date=DAY, record_id=7, stock_code="005930", buy_legs=legs,
                   sell_legs=sells, peer_records=[7], custody_rows=[{
                       "record_id": 7, "state": "full", "source_quality_reasons": [],
                       "owner_type": "main_scalping", "owner_id": "main_scalping:7",
                       "account_key": "test_account"}])
    return source, context, transport, calls


def seal(source):
    source["source_sha256"] = digest({k: v for k, v in source.items() if k != "source_sha256"})


def test_real_cost_collection_and_whole_position_without_fake_fill_allocation(tmp_path):
    source, context, _, _ = broker_fixture(tmp_path)
    result = C.reconcile_position(source, **context)
    assert result["status"] == "actual_cost_reconciled"
    assert result["actual_fees_taxes_krw"] == 10
    assert result["exact_pnl_krw"] == 190
    assert result["exact_profit_rate"] == .95
    assert result["allocation_scope"] == "broker_day_symbol_whole_position"
    assert "legs" not in result
    assert "1234567890" not in C.source_path(tmp_path, DAY).read_text()


def test_repeated_collection_is_zero_call_and_zero_write(tmp_path):
    source, _, transport, calls = broker_fixture(tmp_path)
    mtime = C.source_path(tmp_path, DAY).stat().st_mtime_ns
    calls.clear()
    assert C.collect(tmp_path, DAY, transport=transport, now=NOW) == source
    assert calls == []
    assert C.source_path(tmp_path, DAY).stat().st_mtime_ns == mtime


@pytest.mark.parametrize("field,value", [("continuous_terminal_received", False),
    ("continuous_page_limit_reached", True), ("continuous_next_key_missing", True), ("page_count", 2)])
def test_incomplete_transport_never_replaces_verified_source(tmp_path, field, value):
    source, _, transport, _ = broker_fixture(tmp_path)
    def failed(api, payload):
        pages, meta = transport(api, payload)
        meta[field] = value
        return pages, meta
    with pytest.raises(ValueError):
        C.collect(tmp_path, DAY, transport=failed, now=NOW, refresh=True)
    assert C.load_source(tmp_path, DAY) == source


@pytest.mark.parametrize("change", ["manual", "account", "peer", "overnight", "duplicate", "future", "amount", "extra_order", "early_observation", "missing_identity"])
def test_unknown_or_mixed_costs_never_become_exact(tmp_path, change):
    source, context, _, _ = broker_fixture(tmp_path)
    if change == "manual": context["custody_rows"][0]["owner_type"] = "manual"
    if change == "account": context["custody_rows"][0]["account_key"] = "other"
    if change == "peer": context["peer_records"].append(8)
    if change == "overnight": context["buy_legs"][0]["at"] = "2026-10-07 10:00:00"
    if change == "duplicate": context["buy_legs"] *= 2
    if change == "future": context["knowledge_cutoff"] = NOW.timestamp() - 1
    if change == "amount": context["sell_legs"][0]["price"] = 10101
    if change == "early_observation": context["sell_legs"][0]["at"] = DAY + " 23:00:00"
    if change == "missing_identity": context["sell_legs"][0]["execution_no"] = ""
    if change == "extra_order":
        source["observations"]["ka10076"]["pages"][0]["cntr"].append(
            {"stk_cd": "005930", "ord_no": "99", "io_tp_nm": "+매수", "cntr_qty": "1",
             "cntr_pric": "10000", "oso_qty": "0", "ord_stt": "체결"})
        seal(source)
    result = C.reconcile_position(source, **context)
    assert result["status"] != "actual_cost_reconciled"
    assert result["exact_pnl_krw"] is None


def test_settlement_date_and_execution_date_are_distinct(tmp_path):
    source, context, _, _ = broker_fixture(tmp_path)
    source["observed_at"] = "2026-10-13T21:00:00+09:00"
    for side, amount, cost, settle in (("buy", "20000", "4", "20004"), ("sell", "20200", "6", "20194")):
        obs = source["observations"]["kt00015_" + side]
        obs["observed_at"] = source["observed_at"]
        obs["request"]["end_dt"] = "20261013"
        obs["pages"][0]["trst_ovrl_trde_prps_array"] = [{
            "stk_cd": "A005930", "cntr_dt": "20261008", "trde_dt": "20261013",
            "trde_no": "000000001" if side == "buy" else "000000002",
            "io_tp_nm": "매수" if side == "buy" else "매도",
            "crnc_cd": "KRW", "trde_qty_jwa_cnt": "2",
            "trde_amt": amount, "cmsn": cost, "trde_agri_tax": "0", "incm_resi_tax": "0",
            "int_ls_usfe": "0", "tax_sum_cmsn": cost, "exct_amt": settle}]
    del source["observations"]["ka10076"]
    seal(source)
    result = C.reconcile_position(source, **context)
    assert result["status"] == "actual_cost_reconciled"
    assert result["allocation_scope"] == "broker_settled_whole_position"
    assert result["exact_pnl_krw"] == 190
    context["knowledge_cutoff"] = NOW.timestamp()
    assert C.reconcile_position(source, **context)["status"] == "actual_cost_pending"


def test_official_source_changes_generation_even_without_position_receipts(tmp_path):
    before = source_generation(tmp_path, DAY)
    broker_fixture(tmp_path)
    after = source_generation(tmp_path, DAY)
    assert before != after
    assert after["official_source_sha256"]


def test_account_provider_change_cannot_reuse_same_day_cache(tmp_path):
    source, _, transport, _ = broker_fixture(tmp_path)
    transport.provider_key = "different_application"
    with pytest.raises(ValueError, match="provider_changed"):
        C.collect(tmp_path, DAY, transport=transport, now=NOW)
    assert C.load_source(tmp_path, DAY) == source


def test_current_report_consumes_official_cost_without_unproduced_terminal_fields(tmp_path):
    from src.tests.test_broker_cost_reconciliation import fixture
    from src.engine import sniper_trade_review_report as R
    source, context, _, _ = broker_fixture(tmp_path)
    trade, events, _, _, _ = fixture()
    trade["id"], trade["code"] = 7, "005930"
    for event in events:
        event.fields["order_no"] = "11" if event.stage == "position_rebased_after_fill" else "12"
        event.fields.pop("holding_cost_owner", None)
        event.fields.pop("holding_cost_account_scope_sha256", None)
    row = R._completed_trade_projection(trade, events, {"entry_mode": "normal"},
        broker_cost_source=source, cost_custody_rows=context["custody_rows"],
        cost_peer_records=[7], knowledge_cutoff=NOW.timestamp() + 1)
    assert row["broker_actual_cost_observed"] is True
    assert row["realized_pnl_krw"] == 190
    assert row["profit_rate"] == .95


def test_cost_generation_change_rejects_legacy_snapshot_without_cost_binding(tmp_path, monkeypatch):
    from src.engine import holding_exit_observation_report as H
    path = tmp_path / "trade_review_2026-10-08.json"
    path.write_text("{}")
    sidecar = path.with_suffix(".completed_projection.json")
    sidecar.write_text('{"meta": {}}')
    broker_fixture(tmp_path)
    assert H._verified_trade_review_projection(path, DAY, data_root=tmp_path) is None


@pytest.mark.parametrize("value", [None, "", "NaN", "Infinity", True, "-1", "1,000", "1e3"])
def test_missing_cost_is_not_zero(value):
    with pytest.raises(ValueError): C.number(value)


def test_unit_http_default_cannot_reach_real_account_service(monkeypatch):
    import requests
    import pytest

    monkeypatch.setattr(requests.sessions.Session, "send",
                        lambda *_a, **_kw: pytest.fail("network send escaped test isolation"))
    with pytest.raises(requests.exceptions.RequestException, match="unit_test_http_not_mocked"):
        requests.post("https://api.kiwoom.com/api/dostk/acnt", json={})


def pending(tmp_path, *, records=(7,), days=(DAY,), completion="2026-10-09"):
    return C.enqueue_pending(tmp_path, completion, days, records,
                             ["broker_cost_pending"], now=NOW)


def pending_record(tmp_path, day=DAY, record_id="7", completion="2026-10-09"):
    return C._pending_load(tmp_path)["dates"][day]["records"][completion + ":" + record_id]


def test_pending_enqueue_is_idempotent_bounded_and_never_collects(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "collect", lambda *_a, **_kw: pytest.fail("enqueue used provider"))
    first = pending(tmp_path)
    path = C._pending_path(tmp_path)
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert pending(tmp_path) == first
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert pending_record(tmp_path)["status"] == "pending"
    with pytest.raises(ValueError, match="request_invalid"):
        pending(tmp_path, records=("not-an-id",))
    with pytest.raises(ValueError, match="source_after_completion"):
        pending(tmp_path, days=("2026-10-10",))
    with pytest.raises(ValueError, match="reasons_invalid"):
        C.enqueue_pending(tmp_path, "2026-10-09", [DAY], [7], ["not a reason"])
    assert path.read_bytes() == before[0]


def test_pending_source_dates_persist_across_completion_dates_and_ack_only_matching_records(tmp_path):
    pending(tmp_path, records=(7, 8))
    C.enqueue_pending(tmp_path, "2026-10-10", [DAY], [7], {"cost": ["source_pending"]}, now=NOW)
    C.resolve_pending(tmp_path, "2026-10-09", [7], reason="verified_research_receipt", now=NOW)
    assert pending_record(tmp_path)["status"] == "resolved"
    assert pending_record(tmp_path, record_id="8")["status"] == "pending"
    assert pending_record(tmp_path, completion="2026-10-10")["status"] == "pending"
    pending(tmp_path)
    assert pending_record(tmp_path)["revision"] == 2
    assert pending_record(tmp_path)["status"] == "pending"


def test_drain_collects_target_then_one_prior_and_preserves_intraday_orders(tmp_path):
    old, _, transport, calls = broker_fixture(tmp_path)
    original = C.source_path(tmp_path, DAY).read_bytes()
    pending(tmp_path)
    pending(tmp_path, days=("2026-10-07",), records=(8,))
    calls.clear()
    next_day = NOW + timedelta(days=1)
    result = C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=next_day)
    assert [r["source_date"] for r in result["attempts"]] == ["2026-10-09", "2026-10-07"]
    assert len(calls) == 9  # five TARGET transports, four historical transports
    assert sum(api == "ka10076" for api, _ in calls) == 1
    assert pending_record(tmp_path)["status"] == "pending"
    calls.clear()
    result = C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=next_day)
    assert [r["source_date"] for r in result["attempts"]] == ["2026-10-09", DAY]
    assert result["attempts"][0]["status"] == "already_attempted_today"
    assert len(calls) == 4
    updated = C.load_source(tmp_path, DAY)
    assert updated["observations"]["ka10076"] == old["observations"]["ka10076"]
    archived = C.source_path(tmp_path, DAY).parent / "generations" / DAY / (old["source_sha256"] + ".json")
    assert archived.read_bytes() == original
    receipt = result["attempts"][1]
    assert receipt["previous_source_sha256"] == old["source_sha256"]
    assert receipt["source_sha256"] == updated["source_sha256"]
    assert receipt["source_changed"] is True
    assert receipt["receipt_sha256"] == digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    calls.clear()
    C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=next_day)
    assert calls == []


def test_verified_ack_stops_retry_until_explicit_new_unresolved_record(tmp_path):
    _, _, transport, calls = broker_fixture(tmp_path)
    pending(tmp_path)
    C.resolve_pending(tmp_path, "2026-10-09", [7], now=NOW)
    calls.clear()
    result = C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=NOW + timedelta(days=1))
    assert [r["source_date"] for r in result["attempts"]] == ["2026-10-09"]
    assert result["pending_dates"] == []
    pending(tmp_path, records=(8,))
    calls.clear()
    result = C.drain_pending(tmp_path, "2026-10-10", transport=transport, now=NOW + timedelta(days=2))
    assert [r["source_date"] for r in result["attempts"]] == ["2026-10-10", DAY]
    assert pending_record(tmp_path)["status"] == "resolved"
    assert pending_record(tmp_path, record_id="8")["status"] == "pending"


def test_pending_expiry_is_terminal_explicit_and_original_source_is_preserved(tmp_path):
    old, _, transport, calls = broker_fixture(tmp_path)
    original = C.source_path(tmp_path, DAY).read_bytes()
    pending(tmp_path)
    calls.clear()
    later = NOW + timedelta(days=61)
    result = C.drain_pending(tmp_path, later.date().isoformat(), transport=transport, now=later)
    assert result["expired_dates"] == [DAY]
    record = pending_record(tmp_path)
    assert record["status"] == "expired"
    assert record["expiry_reason"] == "broker_cost_date_outside_supported_window"
    assert record["next_action"] == "retain_unknown_require_external_verified_cost_source"
    assert result["pending_dates"] == []
    assert C.source_path(tmp_path, DAY).read_bytes() == original
    assert C.load_source(tmp_path, DAY) == old
    pending(tmp_path)
    assert pending_record(tmp_path)["status"] == "expired"


def test_failed_prior_claim_is_not_retried_until_next_kst_day_and_keeps_source(tmp_path):
    old, _, transport, calls = broker_fixture(tmp_path)
    original = C.source_path(tmp_path, DAY).read_bytes()
    pending(tmp_path)
    next_day = NOW + timedelta(days=1)
    def incomplete(api, payload):
        pages, meta = transport(api, payload)
        if payload.get("base_dt") == "20261008":
            meta["continuous_terminal_received"] = False
        return pages, meta
    result = C.drain_pending(tmp_path, "2026-10-09", transport=incomplete, now=next_day)
    assert result["status"] == "source_gap"
    assert result["attempts"][1]["status"] == "source_gap"
    assert C.source_path(tmp_path, DAY).read_bytes() == original
    assert pending_record(tmp_path)["status"] == "pending"
    calls.clear()
    C.drain_pending(tmp_path, "2026-10-09", transport=incomplete, now=next_day)
    assert calls == []
    result = C.drain_pending(tmp_path, "2026-10-10", transport=transport, now=next_day + timedelta(days=1))
    assert result["attempts"][1]["source_sha256"] != old["source_sha256"]


def test_failed_target_daily_claim_never_becomes_observed_on_unchanged_retry(tmp_path):
    _, _, transport, calls = broker_fixture(tmp_path)
    def incomplete(api, payload):
        pages, meta = transport(api, payload)
        meta["continuous_terminal_received"] = False
        return pages, meta
    first = C.drain_pending(tmp_path, "2026-10-09", transport=incomplete, now=NOW + timedelta(days=1))
    assert first["status"] == "source_gap"
    calls.clear()
    second = C.drain_pending(tmp_path, "2026-10-09", transport=incomplete, now=NOW + timedelta(days=1))
    assert second["status"] == "source_gap"
    assert second["attempts"][0]["last_collection_status"] == "source_gap"
    assert second["attempts"][0]["last_attempt_receipt_sha256"] == first["attempts"][0]["receipt_sha256"]
    assert calls == []


def test_early_target_can_freeze_final_same_day_orders_without_repeating_prior_claim(tmp_path):
    _, _, transport, calls = broker_fixture(tmp_path)
    pending(tmp_path)
    early = NOW.replace(hour=18) + timedelta(days=1)
    C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=early)
    calls.clear()
    final = C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=early.replace(hour=21))
    assert [r["source_date"] for r in final["attempts"]] == ["2026-10-09"]
    assert len(calls) == 5
    assert sum(api == "ka10076" for api, _ in calls) == 1


def test_generation_collision_preserves_current_source_bytes(tmp_path):
    source, _, transport, _ = broker_fixture(tmp_path)
    path = C.source_path(tmp_path, DAY)
    original = path.read_bytes()
    archived = path.parent / "generations" / DAY / (source["source_sha256"] + ".json")
    archived.parent.mkdir(parents=True)
    archived.write_bytes(b"foreign-incomplete-generation\n")
    with pytest.raises(ValueError, match="history_collision"):
        C.collect(tmp_path, DAY, transport=transport, now=NOW + timedelta(days=1))
    assert path.read_bytes() == original
    assert archived.read_bytes() == b"foreign-incomplete-generation\n"


def test_drain_budget_stops_before_next_transport_and_never_promotes_partial_source(tmp_path, monkeypatch):
    _, _, transport, calls = broker_fixture(tmp_path)
    pending(tmp_path)
    ticks = [0.0]
    monkeypatch.setattr(C.time, "monotonic", lambda: ticks[0])
    def slow(api, payload):
        value = transport(api, payload)
        ticks[0] += 90
        return value
    calls.clear()
    result = C.drain_pending(tmp_path, "2026-10-09", transport=slow,
                             now=NOW + timedelta(days=1), budget_seconds=100)
    assert len(calls) == 2
    assert result["status"] == "budget_deferred"
    assert result["attempts"][0]["reason"] == "broker_cost_collection_budget_exhausted"
    assert C.load_source(tmp_path, "2026-10-09") is None
    assert pending_record(tmp_path)["status"] == "pending"
    assert C._pending_load(tmp_path)["dates"][DAY].get("last_attempt_day") is None


def test_drain_lock_prevents_duplicate_calls_and_concurrent_enqueue_is_not_lost(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    _, _, transport, calls = broker_fixture(tmp_path)
    pending(tmp_path)
    entered, release = Event(), Event()
    def paused(api, payload):
        if not entered.is_set():
            entered.set()
            assert release.wait(3)
        return transport(api, payload)
    calls.clear()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(C.drain_pending, tmp_path, "2026-10-09", transport=paused,
                             now=NOW + timedelta(days=1))
        try:
            assert entered.wait(3)
            before = len(calls)
            second = C.drain_pending(tmp_path, "2026-10-09", transport=transport,
                                     now=NOW + timedelta(days=1))
            assert second["status"] == "drain_in_progress"
            assert len(calls) == before
            pending(tmp_path, records=(8,))
            C.resolve_pending(tmp_path, "2026-10-09", [7], now=NOW)
        finally:
            release.set()
        assert future.result(timeout=3)["status"] == "observed"
    assert pending_record(tmp_path)["status"] == "resolved"
    assert pending_record(tmp_path, record_id="8")["status"] == "pending"
    assert len(calls) == 9


def test_pending_correction_archives_exact_old_bytes_and_cache_uses_kst_date(tmp_path):
    old, _, transport, calls = broker_fixture(tmp_path)
    path = C.source_path(tmp_path, DAY)
    original = path.read_bytes()
    def corrected(api, payload):
        pages, meta = transport(api, payload)
        if api == "ka10170":
            pages[0]["tdy_trde_diary"][0]["cmsn_alm_tax"] = "20"
            pages[0]["tdy_trde_diary"][0]["pl_amt"] = "180"
        return pages, meta
    # The UTC date is still DAY, but the actual KST collection day is DAY+1.
    next_morning = (NOW + timedelta(days=1)).replace(hour=1).astimezone(timezone.utc)
    new = C.collect(tmp_path, DAY, transport=corrected, now=next_morning)
    assert new["source_sha256"] != old["source_sha256"]
    archived = path.parent / "generations" / DAY / (old["source_sha256"] + ".json")
    assert archived.read_bytes() == original
    calls.clear()
    assert C.collect(tmp_path, DAY, transport=corrected,
                     now=next_morning.astimezone(C.KST)) == new
    assert calls == []


def test_corrupt_pending_state_fails_closed_without_calls_or_overwrite(tmp_path):
    _, _, transport, calls = broker_fixture(tmp_path)
    pending(tmp_path)
    path = C._pending_path(tmp_path)
    state = json.loads(path.read_text())
    state["dates"][DAY]["records"]["2026-10-09:7"]["status"] = "resolved"
    path.write_text(json.dumps(state))
    bad = path.read_bytes()
    calls.clear()
    with pytest.raises(ValueError, match="pending_contract_invalid"):
        C.drain_pending(tmp_path, "2026-10-09", transport=transport, now=NOW + timedelta(days=1))
    assert path.read_bytes() == bad
    assert calls == []


def test_cli_pending_uses_existing_date_report_and_rejects_refresh_bypass(tmp_path, monkeypatch):
    from src.utils import constants
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
    monkeypatch.setattr(C, "drain_pending", lambda root, day: {
        "status": "source_gap", "source_date": day, "attempts": [], "pending_dates": [DAY]})
    assert C.main(["--date", DAY, "--drain-pending"]) == 2
    report = tmp_path / "report/holding_broker_cost_source" / (DAY + ".json")
    assert json.loads(report.read_text())["pending_dates"] == [DAY]
    with pytest.raises(SystemExit):
        C.main(["--date", DAY, "--drain-pending", "--refresh"])
