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


def test_seed_different_gaps_share_failure_cooldown(tmp_path, monkeypatch):
    now = BASE + timedelta(hours=1)
    monkeypatch.setattr(reader.time, "time", lambda: now.timestamp())
    def failed(_):
        raise RuntimeError("budget unavailable")
    with pytest.raises(RuntimeError, match="budget unavailable"):
        reader.shared_completed_bar_seed("005930_AL", now=now, fetch=failed,
                                         root=tmp_path, missing_range="gap_a")
    with pytest.raises(RuntimeError, match="retry_deferred"):
        reader.shared_completed_bar_seed("005930_AL", now=now,
            fetch=lambda _: pytest.fail("cross-range duplicate REST"),
            root=tmp_path, missing_range="gap_b")
    monkeypatch.setattr(reader.time, "time", lambda: now.timestamp() + 61)
    result = reader.shared_completed_bar_seed("005930_AL", now=now+timedelta(seconds=61),
        fetch=lambda _: {"stk_min_pole_chart_qry": []}, root=tmp_path, missing_range="gap_b")
    assert result["_completed_bar_source"]["rest_request_count"] == 1


@pytest.mark.parametrize("corruption", [None, [], {}, {"status": "complete"}, "missing_result", "invalid_clock"])
def test_bootstrap_corrupt_seed_is_controlled_without_rest(tmp_path, monkeypatch, corruption):
    now = BASE + timedelta(hours=1)
    monkeypatch.setattr(reader.time, "time", lambda: now.timestamp())
    monkeypatch.setattr(reader, "COMPLETED_BARS_ROOT", tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE", "ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS", "005930")
    def missing(*args, **kwargs):
        raise FileNotFoundError("projection not present")
    monkeypatch.setattr(reader, "read_shared_completed_bars", missing)
    reader.shared_completed_bar_seed("005930_AL", now=now,
        fetch=lambda _: {"stk_min_pole_chart_qry": []}, root=tmp_path)
    path = next(p for p in (tmp_path/".seed/2026-09-21").glob("*.json") if not p.name.endswith(".admission.json"))
    if isinstance(corruption, str):
        doc = json.loads(path.read_text())
        doc.pop("content_sha256")
        if corruption == "missing_result":
            doc.pop("result")
        else:
            doc["received_at_epoch"] = "invalid"
        doc["content_sha256"] = digest(doc)
    else:
        doc = corruption
    atomic_json(path, doc)
    with pytest.raises((RuntimeError, ValueError), match="completed_bar_seed_receipt_invalid"):
        reader.selected_completed_bar_payload("005930", now=now,
            seed_fetch=lambda _: pytest.fail("corruption must not trigger REST"))


def test_no_seed_cannot_bypass_history_floor(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE", "ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS", "005930")
    monkeypatch.setattr(reader, "read_shared_completed_bars", lambda *a, **kw:
                        {"stk_min_pole_chart_qry": [{}], "_completed_bar_source": {}})
    with pytest.raises(RuntimeError, match="history_insufficient"):
        reader.selected_completed_bar_payload("005930", now=BASE, minimum_bars=2)


def test_invalid_history_scope_does_not_bootstrap(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE", "ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS", "005930")
    monkeypatch.setattr(reader, "read_shared_completed_bars", lambda *a, **kw: pytest.fail("invalid scope read"))
    with pytest.raises(RuntimeError, match="history_scope_invalid"):
        reader.selected_completed_bar_payload("005930", now=BASE, history_scope="unknown",
                                             seed_fetch=lambda _: pytest.fail("invalid scope REST"))


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
@pytest.mark.parametrize("observed", [False, True])
def test_episode_gateway_uses_same_reader_without_rest_or_stale_cache(tmp_path,monkeypatch,module,cls,observed):
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
    if observed: receipt["history_basis"]="observed_valid_rows"
    selected={"stk_min_pole_chart_qry":[{"cntr_tm":"20260921100900","open_pric":"70000","high_pric":"70100","low_pric":"70000","cur_prc":"70100","trde_qty":"4"}],"_completed_bar_source":receipt}
    monkeypatch.setattr(reader,"selected_completed_bar_payload",lambda *args,**kw:selected)
    result=gateway.completed_sor_minute_bars(trade_date=now.date(),now=now)
    assert result.source_ok and result.bars[0].close_price==70100 and result.source_receipt==receipt
    assert result.bars[0].history_basis == ("observed_valid_rows" if observed else "")
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


def test_mid_session_ws_cannot_rebase_session_anchor(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE","ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS","005930")
    raw={"stk_min_pole_chart_qry":[{}]*100,"_completed_bar_source":{"complete_session_prefix":False}}
    monkeypatch.setattr(reader,"read_shared_completed_bars",lambda *args,**kw:raw)
    with pytest.raises(RuntimeError,match="session_anchor_history_incomplete"):
        reader.selected_completed_bar_payload("005930",now=BASE,history_scope="session")
    seed={"stk_min_pole_chart_qry":[{"cntr_tm":"20260921160000"}],"_completed_bar_source":{"source":"kiwoom_ka10080_AL_seed","adjustment":"adjusted_1"}}
    monkeypatch.setattr(reader,"shared_completed_bar_seed",lambda *args,**kw:seed)
    selected=reader.selected_completed_bar_payload("005930",now=BASE,history_scope="session",seed_fetch=lambda _:None)
    assert selected is seed and selected["_completed_bar_source"]["ws_selection_blocker"]=="session_anchor_history_incomplete"


def session_point(seq, stamp, cumulative):
    at = datetime.fromisoformat(stamp)
    return replace(point(seq, 0), exchange_timestamp=stamp, local_receive_timestamp=stamp,
                   session_bucket=reader._bar_session(at), cumulative_volume_raw=str(cumulative))


def consume_at_source_time(projection, rows, integrity=INTEGRITY):
    for row in rows:
        projection.consume([row], integrity=integrity, journal_path="durable.jsonl",
                           now_ts=datetime.fromisoformat(row.local_receive_timestamp).timestamp()+.1)


def test_quiet_premarket_opening_prefix_uses_zero_origin_not_synthetic_bars(tmp_path):
    p = CompletedBarProjection(tmp_path)
    consume_at_source_time(p, [session_point(1, "2026-09-21T08:03:10+09:00", 2),
                               session_point(2, "2026-09-21T08:04:01+09:00", 4)])
    now = datetime.fromisoformat("2026-09-21T08:05:00+09:00")
    r = reader.read_shared_completed_bars("005930_AL", now=now, root=tmp_path, snapshot_path=bind(tmp_path,p,now))
    assert r["_completed_bar_source"]["complete_session_prefix"] is True
    assert [x["cntr_tm"] for x in r["stk_min_pole_chart_qry"]] == ["20260921080300"]
    assert r["_completed_bar_source"]["session_coverage"]["prior_cumulative"] == 0


@pytest.mark.parametrize("defect", [None, "lost_volume", "changed_producer", "changed_epoch", "corrupt_hash"])
def test_session_prefix_uses_only_proven_durable_prior_session(tmp_path, defect):
    p = CompletedBarProjection(tmp_path)
    consume_at_source_time(p, [session_point(1, "2026-09-21T08:49:10+09:00", 5000)])
    path = tmp_path/"2026-09-21/005930_AL/SOR_PREMARKET.json"
    prior = json.loads(path.read_text())
    if defect in {"changed_producer", "changed_epoch", "corrupt_hash"}:
        prior.pop("content_sha256")
        if defect == "changed_producer": prior["producer"]["pid"] += 1
        if defect == "changed_epoch": prior["source_epoch"] += 1
        prior["content_sha256"] = "invalid" if defect == "corrupt_hash" else digest(prior)
        atomic_json(path, prior)
    start = 5102 if defect == "lost_volume" else 5002
    consume_at_source_time(p, [session_point(1, "2026-09-21T09:03:10+09:00", start),
                               session_point(2, "2026-09-21T09:04:01+09:00", start+2)])
    now = datetime.fromisoformat("2026-09-21T09:05:00+09:00")
    r = reader.read_shared_completed_bars("005930_AL", now=now, root=tmp_path, snapshot_path=bind(tmp_path,p,now))
    assert r["_completed_bar_source"]["complete_session_prefix"] is (defect is None)


def test_truncated_native_history_never_claims_session_anchor(tmp_path):
    p = CompletedBarProjection(tmp_path, max_bars=2)
    consume_at_source_time(p, [session_point(i, f"2026-09-21T08:0{i}:01+09:00", i*2) for i in range(1,5)])
    now = datetime.fromisoformat("2026-09-21T08:05:00+09:00")
    r = reader.read_shared_completed_bars("005930_AL", now=now, root=tmp_path, snapshot_path=bind(tmp_path,p,now))
    assert r["stk_min_pole_chart_qry"]
    assert r["_completed_bar_source"]["complete_session_prefix"] is False


def test_epoch_change_revokes_prefix_but_allows_new_rolling_suffix(tmp_path):
    p = CompletedBarProjection(tmp_path)
    consume_at_source_time(p, [session_point(1,"2026-09-21T08:01:01+09:00",2),
                               session_point(2,"2026-09-21T08:02:01+09:00",4)])
    changed = {**INTEGRITY, "observer_epoch": 8}
    consume_at_source_time(p, [replace(session_point(i,f"2026-09-21T08:0{i+2}:01+09:00",4+i*2),sequence_epoch=8) for i in range(1,4)],changed)
    now = datetime.fromisoformat("2026-09-21T08:06:00+09:00")
    snapshot = bind(tmp_path,p,now);doc=json.loads(snapshot.read_text())
    doc["shared_transport_producer"]["completed_bar_integrity"] = changed;atomic_json(snapshot,doc)
    r = reader.read_shared_completed_bars("005930_AL", now=now, root=tmp_path, snapshot_path=snapshot)
    assert r["stk_min_pole_chart_qry"] and not r["_completed_bar_source"]["complete_session_prefix"]


def test_session_transition_uses_unpublished_durable_tail_cursor(tmp_path):
    p = CompletedBarProjection(tmp_path)
    journal = tmp_path/"prior.jsonl"
    previous = [session_point(1,"2026-09-21T08:49:01+09:00",5000),
                session_point(2,"2026-09-21T08:49:20+09:00",5002)]
    journal.write_text(''.join(json.dumps(x.as_dict())+'\n' for x in previous))
    for row in previous:
        p.consume([row],integrity=INTEGRITY,journal_path=journal,
                  now_ts=datetime.fromisoformat(row.local_receive_timestamp).timestamp()+.1)
    prior = json.loads((tmp_path/"2026-09-21/005930_AL/SOR_PREMARKET.json").read_text())
    assert prior["cursor"]["sequence"] == 1  # Pending-only updates were not published.
    # Real session partitions have distinct projection objects in one process.
    p = CompletedBarProjection(tmp_path)
    consume_at_source_time(p,[session_point(1,"2026-09-21T09:02:01+09:00",5004),
                              session_point(2,"2026-09-21T09:03:01+09:00",5006)])
    now=datetime.fromisoformat("2026-09-21T09:04:00+09:00")
    r=reader.read_shared_completed_bars("005930_AL",now=now,root=tmp_path,snapshot_path=bind(tmp_path,p,now))
    assert r["_completed_bar_source"]["complete_session_prefix"]
    proof=r["_completed_bar_source"]["session_coverage"]
    assert proof["prior_cursor"]["sequence"]==2
    assert proof["prior_journal_tail"]["end_byte"]==journal.stat().st_size


def test_pre_session_boundary_prints_do_not_create_invalid_bars(tmp_path,monkeypatch):
    p=CompletedBarProjection(tmp_path)
    boundary=replace(point(1,0),exchange_timestamp="2026-09-21T15:59:01+09:00",
                     local_receive_timestamp="2026-09-21T15:59:01+09:00",cumulative_volume_raw="5000")
    consume_at_source_time(p,[boundary,point(2,181,cumulative=5002),point(3,241,cumulative=5004)])
    now=BASE+timedelta(minutes=5)
    snapshot=bind(tmp_path,p,now)
    monkeypatch.setattr(reader,"SNAPSHOT_PATH",snapshot)
    monkeypatch.setattr(reader,"COMPLETED_BARS_ROOT",tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE","ws")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS","005930")
    r=reader.selected_completed_bar_payload("005930",now=now,history_scope="session",
                seed_fetch=lambda _:pytest.fail("REST despite complete native session"))
    assert r["_completed_bar_source"]["complete_session_prefix"]
    assert r["_completed_bar_source"]["rest_request_count"]==0
    assert [b['cntr_tm']for b in r["stk_min_pole_chart_qry"]]==["20260921160300"]


def test_post_session_print_seals_prior_bar_without_cross_session_candle(tmp_path):
    p=CompletedBarProjection(tmp_path)
    end=replace(session_point(2,"2026-09-21T08:49:01+09:00",4),
                exchange_timestamp="2026-09-21T08:51:01+09:00",local_receive_timestamp="2026-09-21T08:51:01+09:00")
    consume_at_source_time(p,[session_point(1,"2026-09-21T08:49:01+09:00",2),end])
    doc=json.loads((tmp_path/"2026-09-21/005930_AL/SOR_PREMARKET.json").read_text())
    assert [x['source_time']for x in doc['bars']]==["20260921084900"]
    assert doc['bars'][0]['status']=='complete'


def test_ready_mode_retains_rest_until_native_floor_then_selects_ws(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE","ws_when_ready")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS","005930")
    native={"stk_min_pole_chart_qry":[{}],"_completed_bar_source":{
        "source":"kiwoom_ws_AL_completed_1m","complete_session_prefix":False,"content_sha256":"native"}}
    monkeypatch.setattr(reader,"read_shared_completed_bars",lambda *a,**kw:native)
    selected={}
    def no_seed(_):pytest.fail("ready mode must retain existing REST cadence, not freeze a seed")
    assert reader.selected_completed_bar_payload("005930",now=BASE,history_scope="session",seed_fetch=no_seed,selection_receipt=selected) is None
    assert selected["reason"]=="session_anchor_history_incomplete"
    assert reader.selected_completed_bar_payload("005930",now=BASE,minimum_bars=2,seed_fetch=no_seed,selection_receipt=selected) is None
    assert selected["reason"]=="completed_bar_history_insufficient"
    native["stk_min_pole_chart_qry"].append({})
    assert reader.selected_completed_bar_payload("005930",now=BASE,minimum_bars=2,seed_fetch=no_seed,selection_receipt=selected) is native
    assert selected["status"]=="ws_selected"
    assert not reader.completed_bar_cache_requires_revalidation("005930",{"stk_min_pole_chart_qry":[]})
    assert reader.completed_bar_cache_requires_revalidation("005930",native)
    annotated=reader.annotate_completed_bar_rest({"stk_min_pole_chart_qry":[]},"005930",{"mode":"ws_when_ready","reason":"session_anchor_history_incomplete"})
    assert annotated["_completed_bar_source"]["request_code"]=="005930"
    assert not reader.completed_bar_cache_requires_revalidation("005930",annotated)


def test_ready_mode_does_not_mask_invalid_live_source_with_rest(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_SOURCE","ws_when_ready")
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS","005930")
    def invalid(*a,**kw):raise ValueError("completed_bar_live_binding_invalid")
    monkeypatch.setattr(reader,"read_shared_completed_bars",invalid)
    with pytest.raises(RuntimeError,match="live_binding_invalid"):
        reader.selected_completed_bar_payload("005930",now=BASE,seed_fetch=lambda _:pytest.fail("invalid source REST"))


def test_bar_readiness_mode_does_not_expand_quote_source_modes(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_MARKET_DATA_SOURCE","ws_when_ready")
    with pytest.raises(RuntimeError,match="widget_market_data_source_invalid"):
        reader.widget_market_data_source(None)


def test_ineligible_boundary_cannot_certify_session_prefix(tmp_path):
    p=CompletedBarProjection(tmp_path)
    boundary=replace(point(1,0),exchange_timestamp="2026-09-21T15:59:01+09:00",
        local_receive_timestamp="2026-09-21T15:59:01+09:00",cumulative_volume_raw="5000",
        path_consumer_eligible=False,path_order_status="duplicate_source_sequence")
    consume_at_source_time(p,[boundary,point(2,181,cumulative=5002),point(3,241,cumulative=5004)])
    now=BASE+timedelta(minutes=5)
    r=reader.read_shared_completed_bars("005930_AL",now=now,root=tmp_path,snapshot_path=bind(tmp_path,p,now))
    assert not r["_completed_bar_source"]["complete_session_prefix"]


def test_observed_history_preserves_sealed_pre_restart_rows_and_excludes_gap(tmp_path):
    p = CompletedBarProjection(tmp_path)
    run(p, [point(1,10), point(2,60), point(3,121)])
    p = CompletedBarProjection(tmp_path)
    run(p, [point(4,190), point(5,240), point(6,301)])
    now = BASE + timedelta(hours=1)
    snapshot = bind(tmp_path,p,now)
    strict = reader.read_shared_completed_bars('005930_AL', now=now, root=tmp_path, snapshot_path=snapshot)
    assert len(strict['stk_min_pole_chart_qry']) == 1
    observed = reader.read_shared_completed_bars('005930_AL', now=now, root=tmp_path, snapshot_path=snapshot, allow_partial_history=True)
    assert [r['cntr_tm'] for r in observed['stk_min_pole_chart_qry']] == ['20260921160100','20260921160400']
    assert observed['_completed_bar_source']['full_session_claimed'] is False
    assert len(observed['_completed_bar_source']['excluded_bars']) == 1
    assert all(r['_history_basis']=='observed_valid_rows' for r in observed['stk_min_pole_chart_qry'])


@pytest.mark.parametrize('defect', ['price','missing_price','future_availability','identity','hash','dead_producer'])
def test_observed_history_keeps_identity_integrity_and_excludes_bad_rows(tmp_path, defect):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60),point(3,121),point(4,181)])
    now=BASE+timedelta(hours=1); snapshot=bind(tmp_path,p,now)
    path=tmp_path/'2026-09-21/005930_AL/SOR_AFTERMARKET.json'
    doc=payload(tmp_path);bar=doc['bars'][1]
    if defect=='price':bar['low']=-1
    elif defect=='missing_price':bar.pop('low')
    elif defect=='future_availability':bar['available_at_epoch']=now.timestamp()+60
    elif defect=='identity':bar['source_item']='034020_AL'
    elif defect=='hash':bar['volume']+=1
    elif defect=='dead_producer':
        snap=json.loads(snapshot.read_text());snap['shared_transport_producer']['connection_available']=False;atomic_json(snapshot,snap)
    if defect!='hash':
        doc.pop('content_sha256');doc['content_sha256']=digest(doc)
    atomic_json(path,doc)
    if defect in {'identity','hash','dead_producer'}:
        with pytest.raises(ValueError):
            reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=snapshot,allow_partial_history=True)
    else:
        out=reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=snapshot,allow_partial_history=True)
        assert len(out['stk_min_pole_chart_qry'])==1
        assert out['stk_min_pole_chart_qry'][0]['cntr_tm']=='20260921160200'


def test_observed_history_quiet_snapshot_age_is_not_disconnect(tmp_path):
    p=CompletedBarProjection(tmp_path);run(p,[point(1,10),point(2,60),point(3,121)])
    now=BASE+timedelta(hours=1);snapshot=bind(tmp_path,p,now-timedelta(minutes=5))
    with pytest.raises(ValueError,match='live_binding'):
        reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=snapshot)
    assert reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=snapshot,allow_partial_history=True)['stk_min_pole_chart_qry']


def test_approved_observed_session_selects_ws_without_seed(monkeypatch,tmp_path):
    p=CompletedBarProjection(tmp_path);run(p,[point(1,10),point(2,60),point(3,121)])
    now=BASE+timedelta(hours=1);snapshot=bind(tmp_path,p,now)
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_BAR_SOURCE','ws_when_ready')
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS','005930')
    monkeypatch.setenv('KORSTOCKSCAN_WS_COMPLETED_BAR_GAP_POLICY','observed_valid_rows')
    monkeypatch.setattr(reader,'COMPLETED_BARS_ROOT',tmp_path);monkeypatch.setattr(reader,'SNAPSHOT_PATH',snapshot)
    result=reader.selected_completed_bar_payload('005930_AL',now=now,history_scope='session',seed_fetch=lambda _:pytest.fail('REST forbidden'))
    assert result['_completed_bar_source']['history_basis']=='observed_valid_rows'
    assert result['_completed_bar_source']['complete_session_prefix'] is False
    assert reader.selected_completed_bar_payload('005930_AL',now=now,minimum_bars=2) is None


@pytest.mark.parametrize('module,cls', [('samsung_midday_one_share.policy','MiddayOneSharePolicy'),('samsung_afternoon_one_share.policy','AfternoonOneSharePolicy'),('low_price_two_leg.profiles','RegularTwoLegPolicy')])
def test_episode_policy_uses_observed_range_without_requiring_missing_minute(module,cls):
    import importlib
    from datetime import time
    mod=importlib.import_module('src.trading.'+module)
    kwargs={'lookback_bars':2}
    if cls=='RegularTwoLegPolicy':kwargs.update(symbol='006800',scan_start=time(9,35),scan_last_bar=time(9,44))
    policy=getattr(mod,cls)(**kwargs)
    stamp=BASE.replace(hour=policy.scan_start.hour,minute=policy.scan_start.minute,second=0)
    rows=[mod.MinuteBar(stamp-timedelta(minutes=2),10200,10200,10000,10000),mod.MinuteBar(stamp,10000,10000,10000,10000)]
    assert policy.evaluate(rows) is None
    observed=[replace(row,history_basis='observed_valid_rows') for row in rows]
    assert policy.evaluate(observed) is not None
    assert policy.evaluate(list(reversed(observed))) is None


@pytest.mark.parametrize('defect', ['future_clock','missing_clock','invalid_clock_type','missing_epoch'])
def test_excluded_bar_cannot_poison_accepted_history_receipt(tmp_path,defect):
    p=CompletedBarProjection(tmp_path)
    run(p,[point(1,10),point(2,60),point(3,121),point(4,181)])
    now=BASE+timedelta(hours=1);snapshot=bind(tmp_path,p,now)
    path=tmp_path/'2026-09-21/005930_AL/SOR_AFTERMARKET.json';doc=payload(tmp_path);bad=doc['bars'][1]
    if defect=='future_clock':bad['available_at_epoch']=now.timestamp()+100
    elif defect=='missing_clock':bad.pop('available_at_epoch')
    elif defect=='invalid_clock_type':bad['available_at_epoch']='invalid'
    else:bad.pop('source_epoch')
    good=doc['bars'][2];doc.pop('content_sha256');doc['content_sha256']=digest(doc);atomic_json(path,doc)
    result=reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=snapshot,allow_partial_history=True)
    assert len(result['stk_min_pole_chart_qry'])==1
    receipt=result['_completed_bar_source']
    assert receipt['available_at_epoch']==good['available_at_epoch']
    assert receipt['historical_source_epochs']==[good['source_epoch']]
    assert any(row['minute_epoch']==bad['minute_epoch'] for row in receipt['excluded_bars'])


@pytest.mark.parametrize('mode',['ws_when_ready','ws'])
def test_dead_producer_is_not_missing_artifact_rest_permission(tmp_path,monkeypatch,mode):
    p=CompletedBarProjection(tmp_path);run(p,[point(1,10),point(2,60),point(3,121)])
    now=BASE+timedelta(hours=1);snapshot=bind(tmp_path,p,now)
    monkeypatch.setattr(reader,'COMPLETED_BARS_ROOT',tmp_path);monkeypatch.setattr(reader,'SNAPSHOT_PATH',snapshot)
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_BAR_SOURCE',mode)
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_BAR_WS_SYMBOLS','005930')
    monkeypatch.setenv('KORSTOCKSCAN_WS_COMPLETED_BAR_GAP_POLICY','observed_valid_rows')
    def dead(_):raise FileNotFoundError('/proc/exited/stat')
    monkeypatch.setattr(reader,'process_generation',dead)
    with pytest.raises(RuntimeError,match='completed_bar_live_binding_invalid'):
        reader.selected_completed_bar_payload('005930_AL',now=now,seed_fetch=lambda _:pytest.fail('dead producer must not trigger REST'))


def test_quote_source_gap_retains_cause_not_false_pid_binding(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_MARKET_DATA_SOURCE','ws')
    monkeypatch.setenv('KORSTOCKSCAN_WIDGET_WS_SYMBOLS','005930')
    context=SimpleNamespace(request_code='005930_AL',name='NXT_AFTERMARKET')
    receipt={'status':'source_gap','reason':'field_clock_route_or_epoch_invalid:0B'}
    with pytest.raises(RuntimeError,match='widget_ws_source_unavailable:field_clock_route_or_epoch_invalid:0B'):
        reader.select_widget_ws_inputs(context,receipt,now_ts=BASE.timestamp())
    assert receipt['selection_reason']=='widget_ws_source_unavailable:field_clock_route_or_epoch_invalid:0B'
    assert receipt['input_adopted'] is False


def test_excluded_row_revokes_full_prefix_claim(tmp_path):
    p=CompletedBarProjection(tmp_path)
    consume_at_source_time(p,[session_point(1,'2026-09-21T08:00:10+09:00',2),session_point(2,'2026-09-21T08:01:01+09:00',4),session_point(3,'2026-09-21T08:02:01+09:00',6)])
    path=tmp_path/'2026-09-21/005930_AL/SOR_PREMARKET.json';doc=json.loads(path.read_text());doc['bars'][1]['low']=-1;doc.pop('content_sha256');doc['content_sha256']=digest(doc);atomic_json(path,doc)
    now=BASE.replace(hour=8,minute=3)
    result=reader.read_shared_completed_bars('005930_AL',now=now,root=tmp_path,snapshot_path=bind(tmp_path,p,now),allow_partial_history=True)
    assert len(result['stk_min_pole_chart_qry'])==1
    assert result['_completed_bar_source']['complete_session_prefix'] is False
