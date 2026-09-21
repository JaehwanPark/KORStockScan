"""Durable AL projection and independent consumer contracts; no broker I/O."""
from dataclasses import replace
from datetime import datetime, timedelta
import json
import os

import pytest

from src.engine.scalping.micro_reversion.completed_bars import CompletedBarProjection, atomic_json, digest
from src.engine.scalping.micro_reversion.path_journal import MarketStreamPoint, NonBlockingPathJournalWriter
from src.trading.market import shared_ws_snapshot as reader

BASE = datetime.fromisoformat("2026-09-21T16:00:00+09:00")
INTEGRITY = {"observer_epoch": 7, "transport_epoch": 2, "loss_revision": [0], "adapter_loss": 0, "writer_loss": 0, "projection_errors": 0}


def point(seq, seconds, *, qty=2, cumulative=None, price=70000):
    stamp = BASE + timedelta(seconds=seconds)
    return MarketStreamPoint("005930", stamp.isoformat(), stamp.isoformat(), seq, 7, seq,
                             "SOR", "SOR_AFTERMARKET", "0B", trade_price=price, trade_qty=qty,
                             source_item="005930_AL", cumulative_volume_raw=str(seq * 2 if cumulative is None else cumulative),
                             trade_volume_raw=str(qty))


def run(projection, points, integrity=INTEGRITY):
    projection.consume(points, integrity=integrity, journal_path="durable.jsonl", now_ts=(BASE+timedelta(hours=1)).timestamp())


def payload(tmp_path):
    return json.loads((tmp_path / "2026-09-21/005930_AL/SOR_AFTERMARKET.json").read_text())


def bind(tmp_path, p, now):
    path = tmp_path / "snapshot.json"
    atomic_json(path, {"generated_at_epoch": now.timestamp(), "shared_transport_producer": {
        "process": p.producer, "source_commit": os.getenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", ""),
        "connection_available": True, "registered_items": ["005930_AL"], "transport_epoch": 2,
        "completed_bar_integrity": INTEGRITY,
    }})
    return path


def test_complete_quiet_not_freshened_or_imputed(tmp_path):
    p = CompletedBarProjection(tmp_path)
    run(p, [point(1, 10), point(2, 60), point(3, 80, price=70100), point(4, 121)])
    before = payload(tmp_path)
    assert [(b["source_time"], b["status"]) for b in before["bars"]] == [
        ("20260921160000", "gap"), ("20260921160100", "complete"), ("20260921160200", "pending")]
    now = BASE + timedelta(hours=1, minutes=10)
    result = reader.read_shared_completed_bars("005930_AL", now=now, root=tmp_path, snapshot_path=bind(tmp_path,p,now))
    assert result["stk_min_pole_chart_qry"] == [{"cntr_tm":"20260921160100", "open_pric":"70000", "high_pric":"70100", "low_pric":"70000", "cur_prc":"70100", "trde_qty":"4"}]
    run(p, [])
    assert payload(tmp_path) == before


@pytest.mark.parametrize("bad", [point(5, 125), point(4,125,cumulative=100), replace(point(4,125),cumulative_volume_raw=None)])
def test_actual_loss_invalidates_completed_suffix(tmp_path,bad):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60),point(3,80),bad,point(6,181,cumulative=102)])
    assert not any(b["status"]=="complete" for b in payload(tmp_path)["bars"])


def test_late_revision_duplicate_and_reconnect(tmp_path):
    p=CompletedBarProjection(tmp_path)
    last=point(4,121)
    run(p,[point(1,10),point(2,60),point(3,80),last])
    before=payload(tmp_path)
    run(p,[last])
    assert payload(tmp_path)==before
    run(p,[point(5,85)])
    assert all(b["status"]!="complete" for b in payload(tmp_path)["bars"])
    integrity={**INTEGRITY,"observer_epoch":8}
    run(p,[replace(point(1,190),sequence_epoch=8)],integrity)
    assert payload(tmp_path)["bars"][-1]["status"]=="gap"


def test_restart_keeps_only_closed_history_and_marks_new_partial(tmp_path):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60),point(3,121)])
    p=CompletedBarProjection(tmp_path)
    run(p,[point(4,190)])
    bars=payload(tmp_path)["bars"]
    assert [(b["source_time"],b["status"]) for b in bars]==[("20260921160100","complete"),("20260921160300","gap")]


def test_reader_rejects_loss_revision_hash_and_process(tmp_path):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60),point(3,121)])
    now=BASE+timedelta(hours=1)
    snapshot=bind(tmp_path,p,now)
    doc=json.loads(snapshot.read_text());doc["shared_transport_producer"]["completed_bar_integrity"]["adapter_loss"]=1;atomic_json(snapshot,doc)
    with pytest.raises(ValueError,match="source_contract"):
        reader.read_shared_completed_bars("005930_AL",now=now,root=tmp_path,snapshot_path=snapshot)
    snapshot=bind(tmp_path,p,now)
    path=tmp_path/"2026-09-21/005930_AL/SOR_AFTERMARKET.json"
    doc=payload(tmp_path);doc["bars"][1]["volume"]=100;atomic_json(path,doc)
    with pytest.raises(ValueError,match="source_contract"):
        reader.read_shared_completed_bars("005930_AL",now=now,root=tmp_path,snapshot_path=snapshot)


def test_durable_writer_projection_and_isolated_failure(tmp_path):
    class Broken:
        invalidated=False
        def consume(self,*args,**kwargs): raise OSError("projection failure")
        def invalidate(self): self.invalidated=True
    broken=Broken()
    writer=NonBlockingPathJournalWriter(tmp_path/"journal.jsonl",completed_bar_projection=broken,source_integrity=lambda:INTEGRITY)
    writer.start();writer.submit(point(1,10));writer.close()
    assert writer.metrics().persisted_envelope_count==1
    assert broken.invalidated and writer._completed_bar_errors==1
    assert writer.metrics().journal_writer_error_count==0


def test_ws_rollout_explicit_and_shared_across_consumers(monkeypatch,tmp_path):
    p=CompletedBarProjection(tmp_path);run(p,[point(1,10),point(2,60),point(3,121)])
    now=BASE+timedelta(hours=1)
    monkeypatch.setattr(reader,"COMPLETED_BARS_ROOT",tmp_path)
    monkeypatch.setattr(reader,"SNAPSHOT_PATH",bind(tmp_path,p,now))
    assert reader.selected_completed_bar_payload("005930",now=now) is None
    for consumer in ("widget","episode"):
        monkeypatch.setenv(f"KORSTOCKSCAN_{consumer.upper()}_BAR_SOURCE","ws")
        monkeypatch.setenv(f"KORSTOCKSCAN_{consumer.upper()}_BAR_WS_SYMBOLS","005930")
        result=reader.selected_completed_bar_payload("005930",now=now,consumer=consumer)
        assert result["_completed_bar_source"]["request_code"]=="005930_AL"
    assert reader.selected_completed_bar_payload("006800",now=now) is None


def test_durable_writer_to_independent_process_reader(tmp_path):
    import subprocess
    import sys
    p=CompletedBarProjection(tmp_path)
    writer=NonBlockingPathJournalWriter(tmp_path/"stream.jsonl",completed_bar_projection=p,source_integrity=lambda:INTEGRITY)
    writer.start()
    for row in [point(1,10),point(2,60),point(3,121)]: writer.submit(row)
    writer.close()
    now=datetime.now(reader.KST)
    snapshot=bind(tmp_path,p,now)
    script="from datetime import datetime; import json,sys; from src.trading.market.shared_ws_snapshot import read_shared_completed_bars; print(json.dumps(read_shared_completed_bars('005930_AL',now=datetime.fromisoformat(sys.argv[1]),root=sys.argv[2],snapshot_path=sys.argv[3])))"
    result=json.loads(subprocess.check_output([sys.executable,"-c",script,now.isoformat(),str(tmp_path),str(snapshot)],text=True))
    assert result["stk_min_pole_chart_qry"][0]["cntr_tm"]=="20260921160100"
    assert writer.metrics().persisted_envelope_count==3


def test_seed_shared_between_processes_and_preserves_original_clock(tmp_path,monkeypatch):
    import multiprocessing
    now=BASE+timedelta(hours=1)
    monkeypatch.setattr(reader.time,"time",lambda:now.timestamp())
    ctx=multiprocessing.get_context("fork")
    entered,release=ctx.Event(),ctx.Event()
    def holder():
        def fetch(item):
            entered.set();assert release.wait(10)
            return {"stk_min_pole_chart_qry":[],"request_item":item}
        reader.shared_completed_bar_seed("005930_AL",now=now,fetch=fetch,root=tmp_path)
    child=ctx.Process(target=holder);child.start()
    try:
        assert entered.wait(10)
        with pytest.raises(RuntimeError,match="lease_busy"):
            reader.shared_completed_bar_seed("005930_AL",now=now,fetch=lambda _:pytest.fail("duplicate REST"),root=tmp_path)
        release.set();child.join(10);assert child.exitcode==0
        result=reader.shared_completed_bar_seed("005930_AL",now=now+timedelta(minutes=10),fetch=lambda _:pytest.fail("quiet repeated REST"),root=tmp_path)
        assert result["_completed_bar_source"]["received_at_epoch"]==now.timestamp()
        assert result["_completed_bar_source"]["adjustment"]=="adjusted_1"
    finally:
        release.set()
        if child.is_alive(): child.terminate();child.join()


def test_seed_failure_backoff_has_no_cached_success(tmp_path,monkeypatch):
    now=BASE+timedelta(hours=1);monkeypatch.setattr(reader.time,"time",lambda:now.timestamp())
    def failed(_): raise RuntimeError("budget unavailable")
    with pytest.raises(RuntimeError,match="budget unavailable"):
        reader.shared_completed_bar_seed("005930_AL",now=now,fetch=failed,root=tmp_path)
    with pytest.raises(RuntimeError,match="retry_deferred"):
        reader.shared_completed_bar_seed("005930_AL",now=now,fetch=lambda _:pytest.fail("retry before cooldown"),root=tmp_path)


def test_other_symbol_timestamp_rejection_does_not_poison_complete_bar(tmp_path):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60)],{**INTEGRITY,"item_rejections":{"006800_AL":1}})
    run(p,[point(3,121)],{**INTEGRITY,"item_rejections":{"006800_AL":2}})
    assert payload(tmp_path)["bars"][1]["status"]=="complete"
    run(p,[point(4,180)],{**INTEGRITY,"item_rejections":{"005930_AL":1}})
    assert payload(tmp_path)["bars"][-1]["status"]=="gap"


@pytest.mark.parametrize("module,cls",[
    ("low_price_two_leg","KiwoomLowPriceTwoLegGateway"),
    ("samsung_morning_one_share","KiwoomOneShareGateway"),
    ("samsung_midday_one_share","KiwoomMiddayOneShareGateway"),
    ("samsung_afternoon_one_share","KiwoomAfternoonOneShareGateway"),
])
def test_episode_gateway_uses_same_reader_without_rest_or_stale_cache(tmp_path,monkeypatch,module,cls):
    import importlib
    from types import SimpleNamespace
    now=BASE.replace(hour=10)+timedelta(minutes=10)
    # Feed the gateway the reader's validated native adapter result; exercise
    # its existing OHLC parser, including a changed same-minute revision.
    module=importlib.import_module("src.trading."+module+".gateway")
    gateway=object.__new__(getattr(module,cls))
    gateway.symbol="005930";gateway._minute_bars_cache=module.SameMinuteSnapshotCache()
    gateway._post=lambda **kw:pytest.fail("REST invoked with valid WS bars")
    receipt={"source":"kiwoom_ws_AL_completed_1m","request_code":"005930_AL","revision":1}
    selected={"stk_min_pole_chart_qry":[{"cntr_tm":"20260921100900","open_pric":"70000","high_pric":"70100","low_pric":"70000","cur_prc":"70100","trde_qty":"4"}],"_completed_bar_source":receipt}
    monkeypatch.setattr(reader,"selected_completed_bar_payload",lambda *args,**kw:selected)
    result=gateway.completed_sor_minute_bars(trade_date=now.date(),now=now)
    assert result.source_ok and result.bars[0].close_price==70100 and result.source_receipt==receipt
    selected["stk_min_pole_chart_qry"]=[]
    assert gateway.completed_sor_minute_bars(trade_date=now.date(),now=now).bars==()


def test_widget_client_and_delta_preserve_actual_source(monkeypatch,tmp_path):
    from src.engine.monitoring.samsung_widget_advisory import KiwoomReadOnlyClient
    from src.engine.monitoring.widget_research_watch_collector import attach_bar_delta
    selected={"stk_min_pole_chart_qry":[],"_completed_bar_source":{"source":"kiwoom_ws_AL_completed_1m","request_code":"005930_AL","adjustment":"raw_same_day","source_epoch":7,"revision":1}}
    monkeypatch.setattr(reader,"selected_completed_bar_payload",lambda *args,**kw:selected)
    client=KiwoomReadOnlyClient("test",shared_read_control_enabled=False)
    monkeypatch.setattr(client,"_post_uncached",lambda *args,**kw:pytest.fail("REST invoked"))
    assert client.post("/api/dostk/chart","ka10080",{"stk_cd":"005930","tic_scope":"1","upd_stkpc_tp":"1"})==selected
    record={"request_code":"005930","market_session":"KRX_REGULAR","observed_at_kst":BASE.isoformat(),"completed_bars":[],"completed_bar_source":selected["_completed_bar_source"]}
    attach_bar_delta(record,{})
    assert "005930_AL" in record["bar_delta_namespace"] and "raw_same_day" in record["bar_delta_namespace"]
    assert record["bar_market_data_request_code"]=="005930_AL"


def test_cutover_respects_existing_history_floor_and_gap_scope(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE","ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS","005930")
    rows=[{"cntr_tm":"20260921160100"}]
    missing={"from_minute":int(BASE.timestamp()),"to_minute":int(BASE.timestamp())+60,"source_epoch":7}
    selected={"stk_min_pole_chart_qry":rows,"_completed_bar_source":{"missing_range":missing}}
    monkeypatch.setattr(reader,"read_shared_completed_bars",lambda *args,**kw:selected)
    calls=[]
    monkeypatch.setattr(reader,"shared_completed_bar_seed",lambda *args,**kw:calls.append(kw) or {"seed":True})
    assert reader.selected_completed_bar_payload("005930",now=BASE,seed_fetch=lambda _:None,minimum_bars=2)=={"seed":True}
    assert calls[0]["missing_range"]==missing
    rows.append({"cntr_tm":"20260921160200"})
    assert reader.selected_completed_bar_payload("005930",now=BASE,seed_fetch=lambda _:pytest.fail("REST after WS history ready"),minimum_bars=2)==selected
    assert len(calls)==1
