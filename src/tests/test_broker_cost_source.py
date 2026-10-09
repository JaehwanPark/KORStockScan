from copy import deepcopy
from datetime import datetime

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
