"""Offline Samsung source reuse and causal recovery research. No live caller.

The market grid is a reconstructed price experiment. Main comparisons preserve
the incumbent guards and native identities. Neither surface is a publisher.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from datetime import datetime
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import mean, median
import sys
import time

from src.engine.scalping import entry_policy_decision_cohort_research as D

P, S = D.P, D.S
DAYS = ("2026-09-29", "2026-09-30", "2026-10-02")
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, policy_publication_forbidden=True, provider_calls=0,
    decision_authority="offline_research_only", metric_role="diagnostic_pattern_research",
    primary_decision_metric="cost_bound_target_first_win_rate", sample_floor="three_research_outcomes_not_live_support",
    window_policy="frozen_three_previously_explored_dates", pristine_holdout=False,
    source_quality_gate="hash_clock_exact_route_epoch_sequence_and_completed_bars",
    forbidden_uses=["orders", "runtime_policy", "realized_profit", "synthetic_native_support"])
MICRO = ("buy_pressure_10t", "net_aggressive_delta_10t", "price_change_10t_pct", "tick_acceleration_ratio")


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def epoch(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timezone_missing")
    return parsed.timestamp()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write(path, value):
    body = {**value, **AUTHORITY}
    body["content_sha256"] = digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read(path):
    value = json.loads(path.read_text())
    if "content_sha256" in value:
        if digest({k:v for k,v in value.items() if k != "content_sha256"}) != value["content_sha256"]:
            raise ValueError('content_seal_invalid:'+str(path))
    return value


def volume_ratio(window):
    if len(window)<6 or any(not finite(b.get('v')) or b['v']<0 for b in window[-6:]):
        return None
    falling=[b['v'] for b in window[-6:-1] if b['c']<b['o']]
    rising=[b['v'] for b in window[-3:] if b['c']>b['o']]
    return mean(rising)/mean(falling) if rising and falling and mean(falling)>0 else None


def captured_volume_ratio(raw):
    """Main uses its own capture; later historical corrections cannot mask it."""
    context=raw['setup_evidence']['strategy_raw_input'].get('entry_candle_context') or {}
    if context.get('request_code')!='005930_AL':return None
    rows=((context.get('strategy_completed_bars') or {}).get('body') or {}).get('bars',[])
    now=epoch(raw['decision_ts']);window=[]
    for b in rows:
        try:t=epoch(b['dt'])
        except (KeyError,TypeError,ValueError):return None
        if (t+60>now or b['dt'][:10]!=raw['decision_ts'][:10]
            or b.get('forming') is not False or b.get('partial_volume') is not False):
            continue
        window.append(dict(b,t=t))
    window.sort(key=lambda b:b['t'])
    tail=window[-6:]
    if (len(tail)<6 or now-tail[-1]['t']-60>=120
        or any(b['t']-a['t']!=60 for a,b in zip(tail,tail[1:]))):return None
    return volume_ratio(tail)


def restore_features(raw, previous=None):
    """Keep valid adverse values; this never changes the execution guard."""
    setup = raw["setup_evidence"]
    f = setup["strategy_raw_input"].get("features") or {}
    quality = (f.get("tick_aggressor_pressure_usable") is True
        and f.get("tick_context_stale") is False and f.get("quote_stale") is False
        and (f.get("tick_aggressor_trusted_count") or 0) >= 10)
    flow = (setup.get("mechanistic_context") or {}).get("flow") or {}
    program = (flow.get("execution_context") or {}).get("program_net_qty")
    values = {"raw:"+k: f.get(k) if quality and finite(f.get(k)) else None for k in MICRO}
    values.update(raw_quality=quality, large_sell=f.get("large_sell_print_detected"),
        raw_absorption=f.get("same_price_buy_absorption") if quality else None,
        program_qty=program if finite(program) and (flow.get("source_quality") or {}).get("status")=="fresh_consistent" else None,
        program_change=None, large_sell_cleared=None, delta_improved=None)
    if previous and raw.get("watch_admission_id") and (0 < epoch(raw["decision_ts"])-previous["t"] <= 180
                     and previous["identity"] == raw.get("watch_admission_id")):
        old = previous["features"]
        if finite(values["program_qty"]) and finite(old.get("program_qty")):
            values["program_change"] = values["program_qty"]-old["program_qty"]
        if quality and old.get("raw_quality"):
            values["large_sell_cleared"] = old.get("large_sell") is True and values["large_sell"] is False
            a,b=values["raw:net_aggressive_delta_10t"],old.get("raw:net_aggressive_delta_10t")
            values["delta_improved"] = a>b if finite(a) and finite(b) else None
    return values


def stream_rows(root, day, kind, manifest):
    """Read repository-normalized observations, not broker packet formats."""
    base=root/"data/observations/scalp_micro_reversion_forward"/("trade_date="+day)/"venue=SOR/session=SOR_REGULAR"
    stem="market_stream" if kind=="trade" else "market_depth_stream"
    meta=base/(stem+".manifest.json")
    if not meta.exists():
        return [], {"status":"source_missing"}
    before=P.file_sha(meta); declared=read(meta)
    paths=[base/s["file"] for s in declared["shards"]]
    if any(p.parent != base or not p.is_file() for p in paths):
        raise ValueError("stream_shard_missing_or_outside_partition")
    manifest[str(meta)]=before
    rows=[]; rejected=Counter(); last={}; duplicate=set()
    for path in paths:
        h=P.file_sha(path); manifest[str(path)]=h
        opener = gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz' else path.open()
        with opener as handle:
            for line in handle:
                if '005930' not in line:
                    continue
                r=json.loads(line)
                if r.get("symbol") != "005930":
                    continue
                expected_schema = "scalp_micro_reversion_market_stream_point_v3" if kind == "trade" else "scalp_micro_reversion_market_depth_point_v1"
                if r.get("schema") != expected_schema:
                    rejected["schema_mismatch"] += 1
                    continue
                if (r.get("source_item",r.get("item")),r.get("venue"),r.get("session_bucket")) != ("005930_AL","SOR","SOR_REGULAR"):
                    rejected["route_mismatch"]+=1;continue
                try:
                    t,ex=epoch(r["local_receive_timestamp"]),epoch(r["exchange_timestamp"])
                    if r["local_receive_timestamp"][:10]!=day:
                        raise ValueError("day_mismatch")
                    ep,seq=r["sequence_epoch"],r["series_sequence"]
                    if type(ep) is not int or type(seq) is not int or seq<1:
                        raise ValueError("sequence_identity_invalid")
                except (KeyError,TypeError,ValueError):
                    rejected["clock_or_sequence_invalid"]+=1;continue
                identity=(ep,seq)
                if identity in duplicate:
                    raise ValueError("duplicate_stream_sequence")
                duplicate.add(identity)
                prev=last.get(ep); last[ep]=(seq,t)
                clock_ok=0<=t-ex<=5
                continuity=prev is None or (seq==prev[0]+1 and t>=prev[1])
                common=dict(t=t,ex=ex,ep=ep,seq=seq,continuous=continuity)
                if kind=="trade":
                    price,qty=r.get("trade_price"),r.get("trade_qty")
                    valid=bool(clock_ok and r.get("path_consumer_eligible") is True
                        and r.get("path_order_status")=="accept" and finite(price) and price>0)
                    rows.append(dict(**common,p=price,q=qty,side=r.get("aggressor_side"),valid=valid,
                        flow_valid=valid and finite(qty) and qty>0 and r.get("aggressor_side") in {"BUY","SELL"}))
                    if not rows[-1]['flow_valid']:rejected['trade_flow_invalid']+=1
                else:
                    bid,ask=r.get("best_bid"),r.get("best_ask")
                    valid=bool(clock_ok and finite(bid) and finite(ask) and 0<bid<ask)
                    rows.append(dict(**common,bid=bid,ask=ask,bq=r.get("best_bid_qty"),aq=r.get("best_ask_qty"),valid=valid))
                    if not finite(bid) or not finite(ask) or bid<=0 or ask<=0:
                        rejected['depth_price_missing_or_nonpositive']+=1
                    elif bid==ask:rejected['locked_depth']+=1
                    elif bid>ask:rejected['crossed_depth']+=1
                if not continuity:rejected["sequence_or_receive_discontinuity"]+=1
                if not clock_ok:rejected["exchange_receive_clock_gap"]+=1
        if P.file_sha(path)!=h:raise ValueError("stream_changed_during_read")
    if P.file_sha(meta)!=before:raise ValueError("stream_manifest_changed")
    rows.sort(key=lambda r:(r["t"],r["ep"],r["seq"]))
    return rows,dict(count=len(rows),first=rows[0]["t"] if rows else None,last=rows[-1]["t"] if rows else None,
        epochs=sorted({r["ep"] for r in rows}),invalid=sum(not r["valid"] for r in rows),issues=dict(rejected),
        measured_file_bytes=sum(p.stat().st_size for p in paths),declared_bytes_are_incremental=True)


def market_features(trades, depths, times):
    """All clocks are local receipt clocks; no future or cross-epoch join."""
    tt=[r["t"] for r in trades]; dt=[r["t"] for r in depths]
    history=deque(maxlen=60); last_ep=None; burst=None
    for r in trades:
        if r["ep"]!=last_ep or not r["continuous"] or not r['flow_valid']:
            history.clear();burst=None
        last_ep=r["ep"]
        if r["flow_valid"] and len(history)>=20:
            old=sorted(history); threshold=max(old[int((len(old)-1)*.95)],median(old)*3)
            if r["side"]=="SELL" and r["q"]>=threshold:
                burst=dict(t=r["t"],p=r["p"],seq=r["seq"])
        r["past_burst"]=burst
        if r["flow_valid"]:history.append(r["q"])
    output=[]
    for now in times:
        end=bisect_right(tt,now); start=bisect_left(tt,now-30)
        window=trades[start:end]
        values=dict(stream_valid=False,depth_valid=False,buy_share10=None,buy_share30=None,
            sell_decay=None,trade_volume_ratio=None,stream_absorption=None,burst_recovery_ticks=None,
            bid_recovery_ticks=None,stream_epoch=None,stream_source_max_at=None)
        usable=(len(window)>=3 and end>0 and start>0 and trades[start-1]["t"]<=now-30
            and now-window[-1]["t"]<=1.5 and len({r["ep"] for r in window+[trades[start-1]]})==1
            and all(r["flow_valid"] and r["continuous"] for r in window)
            and max(b["t"]-a["t"] for a,b in zip([trades[start-1]]+window,window))<=10)
        if usable:
            last=window[-1]; ep=last["ep"]; recent=[r for r in window if r["t"]>now-10]
            earlier=[r for r in window if now-20<r["t"]<=now-10]
            def qty(rs,side=None):return sum(r["q"] for r in rs if side is None or r["side"]==side)
            total=qty(window); latest=qty(recent); old=qty(earlier)
            values.update(stream_valid=True,buy_share30=qty(window,"BUY")/total if total else None,
                buy_share10=qty(recent,"BUY")/latest if latest else None,
                trade_volume_ratio=latest/old if old else None,
                sell_decay=qty(recent,"SELL")/qty(earlier,"SELL") if qty(earlier,"SELL") else None,
                stream_absorption=qty(window,"SELL")>qty(window,"BUY") and last["p"]>=window[0]["p"],
                stream_epoch=ep,stream_source_max_at=last["t"])
            burst=last.get("past_burst")
            if burst and 0<now-burst["t"]<=60:
                recovery=trades[bisect_left(tt,burst["t"]):end]
                if (recovery and all(r["ep"]==ep and r["flow_valid"] and r["continuous"] for r in recovery)
                    and all(b['t']-a['t']<=10 for a,b in zip(recovery,recovery[1:]))):
                    low=min(r["p"] for r in recovery)
                    values["burst_recovery_ticks"]=(last["p"]-low)/500
            dend=bisect_right(dt,now); dstart=bisect_left(dt,now-10); dw=depths[dstart:dend]
            if (dw and now-dw[-1]["t"]<=1.5 and all(r["valid"] and r["continuous"] and r["ep"]==ep for r in dw)
                and dstart>0 and depths[dstart-1]["ep"]==ep and depths[dstart-1]['valid']
                and depths[dstart-1]["t"]<=now-10
                and max(b["t"]-a["t"] for a,b in zip([depths[dstart-1]]+dw,dw))<=5):
                values.update(depth_valid=True,bid_recovery_ticks=(dw[-1]["bid"]-min(r["bid"] for r in dw))/500,
                    stream_source_max_at=max(last["t"],dw[-1]["t"]))
        output.append(values)
    return output


def episode_features(bars):
    """A pivot is known only after two later completed bars. Prefix invariant."""
    rows=[]; active=None; previous_pivot=None; events=[]; segment_start=0
    for i,b in enumerate(bars):
        t=b["t"]+60
        contiguous=i==0 or b["t"]-bars[i-1]["t"]==60
        if not contiguous:
            active=None;previous_pivot=None;segment_start=i
        if active and (b["c"]<active["support"]-500 or b["c"]>=active["resistance"] or t-active["at"]>=1800):
            events.append(dict(at=t,episode=active["id"],event="closed",reason="support_break" if b["c"]<active["support"]-500 else "resistance_or_timeout"))
            active=None
        if i>=4 and all(bars[j]["t"]-bars[j-1]["t"]==60 for j in range(i-3,i+1)):
            pivot=bars[i-2]
            if (pivot["l"]<=min(x["l"] for x in bars[i-4:i-2]) and pivot["l"]<min(x["l"] for x in bars[i-1:i+1])):
                if active is None:
                    past=bars[max(segment_start,i-20):i]
                    active=dict(id=digest([b["day"],"005930_AL",pivot["t"],pivot["l"]])[:20],
                        at=t,support=pivot["l"],resistance=max(x["h"] for x in past),retest=False,
                        higher_low=previous_pivot is not None and pivot["l"]>previous_pivot)
                    events.append(dict(at=t,episode=active["id"],event="confirmed",pivot_at=pivot["t"]))
                previous_pivot=pivot["l"]
        if active and t>active["at"] and b["l"]<=active["support"]+500:
            active["retest"]=True
        window=bars[max(segment_start,i-19):i+1]
        complete=len(window)>=5 and all(v["t"]-u["t"]==60 for u,v in zip(window,window[1:]))
        low=min(x["l"] for x in window); high=max(x["h"] for x in window)
        full_volume=complete and len(window)>=6 and all(finite(x.get("v")) for x in window[-6:])
        known=[x.get('volume_known_at') for x in window[-6:]]
        volume_known_at=max(known) if full_volume and all(finite(x) for x in known) else None
        f=dict(episode_active=active is not None,retest=bool(active and active["retest"]),
            higher_low=bool(active and active["higher_low"]),past_up=i>0 and contiguous and b["c"]>bars[i-1]["c"],
            range_location=(b["c"]-low)/(high-low) if complete and high>low else None,
            drawdown_pct=(b["c"]/high-1)*100 if complete else None,
            support_distance_ticks=(b["c"]-active["support"])/500 if active else None,
            rebound_volume_ratio=volume_ratio(window) if full_volume else None)
        rows.append(dict(day=b["day"],t=t,price=b["c"],episode=active["id"] if active else None,
            features=f,bar_index=i,volume_known_at=volume_known_at))
    return rows,events


def price_label(bars, at, price, cost):
    """Future complete bars only; omit the partially observed decision minute."""
    future=[b for b in bars if at<=b["t"] and b['t']+60<=at+600]
    if (not finite(price) or price<=0 or not finite(cost) or cost<0 or not future
        or future[0]['t']-at>=60):
        return dict(binary=None,net=None,status="price_coverage_gap")
    target=price*(1+(cost+.1)/100); stop=price*.993
    for i,b in enumerate(future):
        if i and b['t']-future[i-1]['t']!=60:
            return dict(binary=None,net=None,status='price_coverage_gap')
        hit,loss=b["h"]>=target,b["l"]<=stop
        if hit and loss:return dict(binary=None,net=None,status="same_bar_ambiguous")
        if hit:return dict(binary=1,net=.1,status="target_first",delay=b["t"]+60-at)
        if loss:return dict(binary=0,net=-.7-cost,status="stop_first",delay=b["t"]+60-at)
    if future[-1]['t']+60<at+540:
        return dict(binary=None,net=None,status='price_coverage_gap')
    return dict(binary=None,net=(future[-1]["c"]/price-1)*100-cost,status="neither")


def prepare(root, output):
    started=time.monotonic();manifest={};capture=[];volumes=defaultdict(lambda:defaultdict(list))
    kernels={str(Path(m.__file__).resolve()):P.file_sha(Path(m.__file__))
        for m in [sys.modules[__name__], D, D.R, P, P.calibration, S, D.E]}
    prior_path=root/'tmp/samsung-source-consumption-exploration-20261003/source-census.json'
    prior=read(prior_path);manifest[str(prior_path)]=P.file_sha(prior_path)
    for p,h in prior['source_manifest'].items():
        if 'samsung_widget_advisory_' in p or 'widget_signal_auto_trade_events_' in p:
            if P.file_sha(Path(p))!=h:raise ValueError('widget_context_source_changed')
            manifest[p]=h
    widget_context=dict(fills=prior['widget_fills'],not_main_training=True,
        days={day:{k:v for k,v in value.items() if k.startswith('widget_')}
            for day,value in prior['days'].items()})
    parent_path=root/"tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json"
    parent=read(parent_path)["parent_policy"];manifest[str(parent_path)]=P.file_sha(parent_path)
    if S.digest(parent)!="d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a":
        raise ValueError("incumbent_changed_research_replan_required")
    source_census={}
    for day in DAYS:
        path=root/f"data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json"
        h=P.file_sha(path);manifest[str(path)]=h
        if h!=D.RAW_HASHES[day]:raise ValueError("frozen_observation_changed")
        rows=[]
        for raw in P.stream_array(path):
            if (raw.get("stock_code"),raw.get("effective_venue"),raw.get("session_bucket"))!=("005930","KRX","KRX_REGULAR"):
                continue
            if not raw.get("source_provenance_verified") or not raw.get("machine_observation_hash_verified"):
                raise ValueError("samsung_capture_provenance_invalid")
            prepared=D.fast_prepare(raw,parent);guard=D.guard_summary(prepared)
            current=D.outcome_diagnosis(raw)
            try:native=list(P.opportunity_identity(raw))
            except ValueError:native=None
            c=raw['setup_evidence']['strategy_raw_input'].get('entry_candle_context') or {}
            if c.get('request_code')=='005930_AL':
                for b in ((c.get('strategy_completed_bars') or {}).get('body') or {}).get('bars',[]):
                    if (b.get('forming') is not False or b.get('partial_volume') is not False
                        or not finite(b.get('v')) or b['v']<0):continue
                    try:bt=epoch(b['dt'])
                    except (KeyError,ValueError):continue
                    if b['dt'][:10]!=day or bt+60>epoch(raw['decision_ts']):continue
                    volumes[day][bt].append(dict(o=b['o'],h=b['h'],l=b['l'],c=b['c'],v=b['v'],known=epoch(raw['decision_ts'])))
            rows.append(dict(raw=raw,prepared=prepared,guard=guard,native=native,current=current))
        previous=None
        for obj in sorted(rows,key=lambda x:x['raw']['decision_ts']):
            raw=obj['raw'];t=epoch(raw['decision_ts']);f=restore_features(raw,previous)
            values=obj['current']; label=dict(binary=int(values['value']>0) if values['value'] is not None else None,
                net=values['value'],status=values['diagnosis'])
            capture.append(dict(day=day,t=t,ts=raw['decision_ts'],trace=raw['decision_trace_id'],
                native=obj['native'],price=raw['setup_evidence']['strategy_raw_input']['current']['price'],
                parent=obj['prepared']['decision']['action'],guard=obj['guard'],features=f,
                recoverable=bool(D.confirming_families(raw,parent,obj['prepared'],obj['guard'])),
                label=label,cost=raw['comparison']['conservative_execution_cost_pct'],
                captured_volume_ratio=captured_volume_ratio(raw),volume_basis='own_asof_raw_capture'))
            previous=dict(t=t,identity=raw.get('watch_admission_id'),features=f)
        if P.file_sha(path)!=h:raise ValueError('capture_changed_during_read')
        source_census[day]=dict(captures=len(rows))
        print(day,'capture replay',len(rows),flush=True)
    market=[];episode_events={};bar_sets={}
    for day in DAYS:
        path=root/f'data/report/machine_completed_price_source/machine_completed_price_source_{day}.json'
        h=P.file_sha(path);manifest[str(path)]=h;original=read(path)
        if not P.calibration._artifact_content_sha256_valid(original):raise ValueError('price_seal_invalid')
        bars=[];vol_conflicts=0
        for b in original['prices']:
            if (b.get('stock_code'),b.get('effective_venue'),b.get('session_bucket'),b.get('source_request_code'))!=('005930','KRX','KRX_REGULAR','005930_AL'):continue
            if b.get('completed_bar_only') is not True or not (0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']):raise ValueError('invalid_completed_bar')
            t=epoch(b['timestamp']);v=volumes[day].get(t,[])
            exact=[x for x in v if all(x[a]==b[k] for a,k in [('o','open'),('h','high'),('l','low'),('c','close')])]
            valid=bool(exact and len(exact)==len(v) and len({x['v'] for x in exact})==1)
            if v and not valid:vol_conflicts+=1
            bars.append(dict(day=day,t=t,o=b['open'],h=b['high'],l=b['low'],c=b['close'],
                v=exact[0]['v'] if valid else None,volume_known_at=min(x['known'] for x in exact) if valid else None))
        bars.sort(key=lambda b:b['t'])
        if len({b['t'] for b in bars})!=len(bars):raise ValueError('duplicate_completed_bar')
        bar_sets[day]=bars;grid,events=episode_features(bars);episode_events[day]=events
        trades,tc=stream_rows(root,day,'trade',manifest);depths,dc=stream_rows(root,day,'depth',manifest)
        native=[r for r in capture if r['day']==day]
        stream=market_features(trades,depths,[r['t'] for r in grid+native])
        for r,f in zip(grid,stream[:len(grid)]):
            r['features'].update(f);r.update(label=price_label(bars,r['t'],r['price'],.33),cost=.33,
                trace=digest([day,r['t'],'market_grid']),native=None,parent=None)
        times=[r['t'] for r in grid]
        for r,f in zip(native,stream[len(grid):]):
            i=bisect_right(times,r['t'])-1
            if i>=0 and r['t']-times[i]<120:
                g=grid[i];r['episode']=g['episode'];r['features'].update({k:v for k,v in g['features'].items() if k not in f})
            else:r['episode']=None
            r['features']['rebound_volume_ratio']=r['captured_volume_ratio']
            r['features'].update(f)
            r['price_label']=price_label(bars,r['t'],r['price'],r['cost'])
        market.extend(grid)
        source_census[day].update(bars=len(bars),volumes=sum(b['v'] is not None for b in bars),volume_conflicts=vol_conflicts,
            trade=tc,depth=dc,grid_stream_valid=sum(r['features']['stream_valid'] for r in grid),
            main_stream_valid=sum(r['features']['stream_valid'] for r in native),episodes=sum(e['event']=='confirmed' for e in events))
        if P.file_sha(path)!=h:raise ValueError('price_changed_during_read')
        print(day,'stream',len(trades),len(depths),'valid grid',source_census[day]['grid_stream_valid'],flush=True)
    for p,h in {**manifest,**kernels}.items():
        if P.file_sha(Path(p))!=h:raise ValueError('source_changed:'+p)
    value=dict(market=market,main=capture,source_census=source_census,source_manifest=manifest,
        kernel_manifest=kernels,widget_context=widget_context,
        episodes=episode_events,parent_sha256=S.digest(parent),elapsed_sec=time.monotonic()-started,
        raw_stream_retained=True,feature_time_rule='past_local_receive_and_completed_bar_only',
        independent_stream_binding='005930_AL_SOR_REGULAR_context_not_main_runtime_epoch_or_actual_consumption',
        volume_grid_basis='retrospective_same_route_completed_bars_not_asof_capture_receipts')
    write(output/'projection.json',value)
    return value


def predicate(row, condition):
    key,op,value=condition; observed=row['features'].get(key)
    if observed is None:return False
    if op=='is':return observed is value
    if not finite(observed):return False
    return observed>=value if op=='ge' else observed<=value


BASES = [
    [('episode_active','is',True),('past_up','is',True)],
    [('retest','is',True),('past_up','is',True)],
    [('higher_low','is',True),('past_up','is',True)],
    [('past_up','is',True),('range_location','le',.5)],
    [('retest','is',True),('support_distance_ticks','ge',2)],
]
EXTRAS = {
    'price':[('drawdown_pct','le',-.4),('range_location','le',.35),('support_distance_ticks','le',3)],
    'volume':[('rebound_volume_ratio','ge',1.),('rebound_volume_ratio','ge',1.5)],
    'restored':[('raw:buy_pressure_10t','ge',50.),('raw:buy_pressure_10t','ge',60.),
        ('raw:net_aggressive_delta_10t','ge',1.),('raw_absorption','ge',1.),
        ('raw_absorption','ge',2.),('program_change','ge',1.),('large_sell_cleared','is',True),('delta_improved','is',True)],
    'stream':[('buy_share10','ge',.55),('buy_share10','ge',.65),('sell_decay','le',.75),
        ('trade_volume_ratio','ge',1.2),('stream_absorption','is',True),
        ('burst_recovery_ticks','ge',1.),('burst_recovery_ticks','ge',2.),('bid_recovery_ticks','ge',1.)],
}


def definitions(training, level):
    allowed=['price']+(['volume'] if level in {'volume','restored','stream'} else [])
    if level in {'restored','stream'}:allowed+=['restored']
    if level=='stream':allowed+=['stream']
    extras=[x for name in allowed for x in EXTRAS[name]]
    extras=[x for x in extras if sum(predicate(r,x) for r in training)>=2]
    rules=[]
    for base in BASES:
        for additional in [()] + [(x,) for x in extras] + list(itertools.combinations(extras,2)):
            conditions={}
            for key,op,value in base+list(additional):
                old=conditions.get((key,op))
                conditions[key,op]=value if old is None or op=='is' else max(value,old) if op=='ge' else min(value,old)
            rule=[(key,op,value) for (key,op),value in sorted(conditions.items())]
            if sum(all(predicate(r,c) for c in rule) for r in training)<2:continue
            rules.append(dict(id=digest(rule)[:16],conditions=rule))
    return sorted(rules,key=lambda r:(len(r['conditions']),r['id']))


def actions(rows,rule,mode):
    result=[]
    for r in rows:
        matched=all(predicate(r,c) for c in rule['conditions']) if rule else True
        if mode=='market':choose=matched
        elif mode=='filter':choose=r['parent']=='ENTER_NOW' and matched
        elif mode=='recover':choose=r['parent']=='ENTER_NOW' or (r['recoverable'] and matched)
        elif mode=='parent':choose=r['parent']=='ENTER_NOW'
        else:raise ValueError('unknown_mode')
        result.append(choose)
    return result


def select_exposures(rows,mask):
    selected=[];seen=set();reserved={}
    for i in sorted(range(len(rows)),key=lambda i:(rows[i]['day'],rows[i]['t'],rows[i]['trace'])):
        r=rows[i]
        if not mask[i] or r['t']<reserved.get(r['day'],-math.inf):continue
        key=(r['day'],r.get('episode'))
        if key[1] is not None and key in seen:continue
        if key[1] is not None:seen.add(key)
        selected.append(r);reserved[r['day']]=r['t']+600
    return selected


def summary(rows,mask):
    chosen=select_exposures(rows,mask); labels=[r['label'] for r in chosen]
    wins=sum(l['binary']==1 for l in labels); losses=sum(l['binary']==0 for l in labels); n=wins+losses
    p=wins/n if n else None;z=1.6448536269514722
    lower=(p+z*z/(2*n)-z*math.sqrt((p*(1-p)+z*z/(4*n))/n))/(1+z*z/n) if n else None
    nets=[l['net'] for l in labels if finite(l.get('net'))]
    return dict(selected=len(chosen),wins=wins,losses=losses,evaluable=n,win_rate=p,wilson_lower=lower,
        coverage=n/len(chosen) if chosen else None,mean_net=mean(nets) if nets else None,
        statuses=dict(Counter(l['status'] for l in labels)),traces=[r['trace'] for r in chosen],
        dates=sorted({r['day'] for r in chosen}),native_groups=len({tuple(r['native']) for r in chosen if r.get('native')}),
        missing_native_exposures=sum(not r.get('native') for r in chosen),
        attempts=sum(mask),
        net_basis='synthetic_target_stop_and_neither_time_exit' if rows and rows[0]['parent'] is None else 'source_bound_evaluable_path_only',
        unit='nonoverlapping_research_episode_exposures_not_native_promotion_count')


def fit(training,rules,mode):
    best=None;seen=set();supported=0
    for rule in rules:
        mask=actions(training,rule,mode);signature=tuple(mask)
        if signature in seen:continue
        seen.add(signature);metric=summary(training,mask)
        if metric['evaluable']<3:continue
        supported+=1
        rank=(metric['wilson_lower'],metric['win_rate'],metric['evaluable'],-len(rule['conditions']))
        if best is None or rank>best[0]:best=(rank,rule,metric)
    return dict(rule=best[1] if best else None,train=best[2] if best else None,
        definitions=len(rules),unique_actions=len(seen),supported=supported)


def run(source,output):
    started=time.monotonic();source_sha=P.file_sha(source);data=read(source);folds=[];candidates=[]
    for p,h in data['kernel_manifest'].items():
        if P.file_sha(Path(p))!=h:raise ValueError('research_kernel_changed:'+p)
    for lane in ['market','main']:
        rows=data[lane]
        for train_days,held in [(DAYS[:1],DAYS[1]),(DAYS[:2],DAYS[2])]:
            training=[r for r in rows if r['day'] in train_days];test=[r for r in rows if r['day']==held]
            for mode in (['market'] if lane=='market' else ['filter','recover']):
                baseline_rule=dict(conditions=BASES[1]) if lane=='market' else None
                base_mode='market' if lane=='market' else 'parent'
                for level in ['price','volume','restored','stream']:
                    rules=definitions(training,level);selected=fit(training,rules,mode)
                    candidates.append(dict(lane=lane,mode=mode,level=level,train_days=list(train_days),
                        rules=rules,sha256=digest(rules)))
                    row=dict(lane=lane,mode=mode,level=level,train_days=list(train_days),held_day=held,**selected,
                        raw_main_features_available=lane=='main',
                        baseline_train=summary(training,actions(training,baseline_rule,base_mode)),
                        baseline_held=summary(test,actions(test,baseline_rule,base_mode)))
                    rule=selected['rule']
                    row['held']=summary(test,actions(test,rule,mode)) if rule else None
                    row['frozen_rule_sha256']=digest(rule) if rule else None
                    if len(train_days)==1 and rule:
                        follow=[r for r in rows if r['day']==DAYS[2]]
                        row['unchanged_followthrough']=summary(follow,actions(follow,rule,mode))
                    if rule and lane=='main':
                        changed=[r for r,choose in zip(test,actions(test,rule,mode)) if choose!=(r['parent']=='ENTER_NOW')]
                        row['changed_attempts']=[dict(trace=r['trace'],ts=r['ts'],parent=r['parent'],label=r['label'],
                            native=r['native'],guard=r['guard']) for r in changed]
                    folds.append(row)
                    print(lane,mode,level,train_days,selected['supported'],'held',row['held'] and (row['held']['wins'],row['held']['evaluable']),flush=True)
    if P.file_sha(source)!=source_sha:raise ValueError('projection_changed_during_run')
    write(output/'frozen-candidates.json',dict(candidates=candidates,source_projection_sha256=source_sha))
    write(output/'result.json',dict(folds=folds,source_projection_sha256=source_sha,
        kernel_manifest=data['kernel_manifest'],frozen_candidates_sha256=P.file_sha(output/'frozen-candidates.json'),
        source_census=data['source_census'],elapsed_sec=time.monotonic()-started,
        selection='train_only_wilson_then_win_rate_support_simplicity_no_winner_retention_veto',
        all_results_exploratory=True))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run'])
    parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':prepare(args.root.resolve(),args.output.resolve())
    else:
        if not args.source:parser.error('--source is required')
        run(args.source.resolve(),args.output.resolve())


if __name__=='__main__':main()
