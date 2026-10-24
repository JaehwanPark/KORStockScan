"""Native normal/fast submit ownership, including deterministic interleaving."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest


class SubmitBoundaryReached(Exception):
    pass


def _dispatch_case(monkeypatch, *, fast=False, change=None):
    from src.engine import sniper_state_handlers as h

    at = datetime.fromisoformat("2026-10-16T10:11:11+09:00").timestamp()
    stock = dict(
        id=101,
        code="005930",
        name="OWNERSHIP_TEST",
        status="HOLDING",
        strategy="SCALPING",
        buy_qty=10,
        buy_price=10000,
        fast_exit_broker_route="SOR",
    )
    if fast:
        stock.update(
            exit_token="same-native-claim",
            exit_requested=True,
            fast_exit_retry_pending=False,
        )
    monkeypatch.setattr(h, "ENTRY_LOCK", threading.RLock())
    monkeypatch.setattr(h, "_log_holding_pipeline", lambda *a, **k: None)
    monkeypatch.setattr(h, "_is_scalp_simulated_position", lambda *a: False)
    monkeypatch.setattr(h, "_sell_side_open_time_block_fields", lambda **k: {})
    monkeypatch.setattr(h, "_resolve_holding_elapsed_sec", lambda *a, **k: 120)
    monkeypatch.setattr(h, "_main_stop_normal_exit_fields", lambda *a, **k: {})
    monkeypatch.setattr(
        h,
        "_mutate_stock_state",
        lambda value, **k: value.update(k.get("set_fields", {})),
    )

    def remaining(*args, **kwargs):
        if change:
            change(stock)
        return 10

    monkeypatch.setattr(h, "_confirm_cancel_or_reload_remaining", remaining)

    def boundary(*args, **kwargs):
        raise SubmitBoundaryReached()

    monkeypatch.setattr(h, "_persist_sell_submit_pre_call_boundary", boundary)
    monkeypatch.setattr(
        h,
        "_send_exit_best_ioc",
        lambda *a, **k: pytest.fail("unit case reached transport"),
    )

    def dispatch():
        return h._dispatch_scalp_preset_exit(
            stock=stock,
            code="005930",
            now_ts=at,
            curr_p=9800,
            buy_p=10000,
            profit_rate=-2,
            peak_profit=0,
            strategy="SCALPING",
            sell_reason_type="LOSS",
            reason="native ownership test",
            exit_rule="scalp_hard_stop_pct",
            fast_exit=fast,
        )

    return stock, dispatch


@pytest.mark.parametrize(
    "blocked",
    [
        {"exit_requested": True},
        {"exit_token": "other-claim"},
        {"sell_submit_generation": "original-generation"},
        {"sell_submit_pending": True},
        {"sell_odno": "0000001"},
        {"status": "SELL_ORDERED"},
        {"status": "COMPLETED"},
        {"manual_control_hard_stop_handoff_inflight": True},
        {"manual_control_exclusion_blocked": True},
    ],
)
def test_normal_dispatch_preserves_existing_owner_before_metadata(monkeypatch, blocked):
    stock, dispatch = _dispatch_case(monkeypatch)
    stock.update(
        blocked, last_exit_rule="winner_rule", last_exit_reason="winner_reason"
    )
    before = deepcopy(stock)
    assert dispatch() is False
    assert stock == before


@pytest.mark.parametrize(
    "fast,change",
    [
        (False, {"exit_requested": True, "exit_token": "fast-winner"}),
        (
            False,
            {"sell_submit_generation": "pending-winner", "sell_submit_pending": True},
        ),
        (False, {"buy_qty": 9}),
        (False, {"manual_control_exclusion_blocked": True}),
        (True, {"exit_token": "replacement-claim"}),
        (True, {"sell_submit_generation": "pending-winner"}),
        (True, {"manual_control_hard_stop_handoff_inflight": True}),
    ],
)
def test_dispatch_rechecks_owner_after_account_work(monkeypatch, fast, change):
    winner = {}

    def intervene(stock):
        stock.update(
            change, last_exit_rule="winner_rule", last_exit_reason="winner_reason"
        )
        winner.update(deepcopy(stock))

    stock, dispatch = _dispatch_case(monkeypatch, fast=fast, change=intervene)
    assert dispatch() is False
    assert stock == winner


def test_fast_dispatch_without_claim_cannot_create_submit_context(monkeypatch):
    stock, dispatch = _dispatch_case(monkeypatch, fast=True)
    stock.pop("exit_token")
    before = deepcopy(stock)
    assert dispatch() is False
    assert stock == before


@pytest.mark.parametrize("confirmation", ["unknown", "verified_zero"])
@pytest.mark.parametrize("fast", [False, True])
def test_stale_account_result_cannot_mutate_new_owner_or_db(
    monkeypatch, confirmation, fast
):
    from src.engine import sniper_state_handlers as h
    from src.engine.sniper_trade_utils import BrokerRemainingQty

    stock, dispatch = _dispatch_case(monkeypatch, fast=fast)
    winner = {}

    def stale_response(*a, **k):
        stock.update(
            status="SELL_ORDERED",
            exit_token="new-winner",
            exit_requested=True,
            sell_submit_pending=True,
            sell_submit_generation="winner-generation",
            last_exit_rule="winner-rule",
            sell_cancel_reconciliation_source="winner-source",
        )
        winner.update(deepcopy(stock))
        return BrokerRemainingQty(
            0, confirmation_state=confirmation, source="old-account-response"
        )

    class NoDBMutation:
        def get_session(self):
            pytest.fail("stale account response reached DB mutation")

    monkeypatch.setattr(h, "DB", NoDBMutation())
    monkeypatch.setattr(h, "_confirm_cancel_or_reload_remaining", stale_response)
    assert dispatch() is False
    assert stock == winner


def test_deferred_fast_route_result_cannot_rearm_replacement_claim(monkeypatch):
    from src.engine import sniper_state_handlers as h

    stock, dispatch = _dispatch_case(monkeypatch, fast=True)
    stock["fast_exit_broker_route"] = ""
    winner = {}

    def after_signal(*a, **k):
        stock.update(
            exit_token="replacement-claim",
            exit_requested=True,
            last_exit_rule="new-winner-rule",
        )
        winner.update(deepcopy(stock))

    monkeypatch.setattr(h, "_log_holding_pipeline", after_signal)
    dispatch()
    assert stock == winner


def test_pending_preset_generation_can_reconcile_but_positive_quantity_cannot_replace_it(
    monkeypatch,
):
    reached = []

    def confirmed_quantity(stock):
        reached.append(stock["sell_submit_generation"])

    stock, dispatch = _dispatch_case(monkeypatch, change=confirmed_quantity)
    stock.update(
        preset_tp_ord_no="0000007",
        sell_odno="0000007",
        sell_submit_pending=True,
        sell_submit_generation="original-generation",
    )
    assert dispatch() is False
    assert reached == ["original-generation"]
    assert stock["sell_submit_generation"] == "original-generation"
    assert stock["sell_odno"] == "0000007" and stock["buy_qty"] == 10


@pytest.mark.parametrize("fast", [False, True])
def test_unchanged_normal_or_same_fast_token_reaches_native_custody_boundary(
    monkeypatch, fast
):
    stock, dispatch = _dispatch_case(monkeypatch, fast=fast)
    token = stock.get("exit_token")
    with pytest.raises(SubmitBoundaryReached):
        dispatch()
    assert stock["status"] == "SELL_ORDERED" and stock["sell_submit_pending"] is True
    assert (
        stock["buy_qty"]
        == stock["sell_submit_requested_qty"]
        == stock["sell_submit_owner_position_qty"]
        == 10
    )
    assert stock.get("exit_token") == token


def test_same_fast_token_can_retry_after_safe_pre_call_rollback(monkeypatch):
    from src.engine import sniper_state_handlers as h

    stock, dispatch = _dispatch_case(monkeypatch, fast=True)
    attempts = []

    def external_custody_unavailable_once(value, code, *, target_id):
        attempts.append(value["sell_submit_generation"])
        if len(attempts) > 1:
            raise SubmitBoundaryReached()
        # Existing durability owner already rolled DB back and cleared only
        # its unsubmitted generation. Exercise the dispatcher's real rearm.
        value["status"] = "HOLDING"
        value["sell_cancel_reconciliation_required"] = False
        for field in h._SELL_SUBMIT_CONTEXT_KEYS:
            value.pop(field, None)
        return False

    monkeypatch.setattr(
        h, "_persist_sell_submit_pre_call_boundary", external_custody_unavailable_once
    )
    token = stock["exit_token"]
    dispatch()
    assert stock["status"] == "HOLDING" and stock["fast_exit_retry_pending"] is True
    assert stock["exit_requested"] is False and stock["exit_token"] == token
    assert "sell_submit_generation" not in stock
    with pytest.raises(SubmitBoundaryReached):
        dispatch()
    assert attempts[0] != attempts[1] and stock["exit_token"] == token


NATIVE_CHILD = r"""
import json, sys, threading
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
from src.engine.automation import main_stop_performance as perf
root, source, point = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
data=json.loads(source.read_text())
perf._install_full_isolation(root, root/'result.json')
from src.engine.automation.main_stop_runtime_workload import isolated_main_workload
from src.engine import sniper_state_handlers as h, kiwoom_orders as orders, kiwoom_sniper_v2 as main
from src.engine import sniper_execution_receipts as receipts
from src.engine.scalping import main_stop_policy as policy
from src.database.models import RecommendationHistory
arrived,release=threading.Event(),threading.Event()
normal_kwargs,workers,proof={},{},{}
(root/'capture').mkdir()
with perf._isolated_native_capture(root/'capture') as (_,queue,capture,sink), \
        isolated_main_workload(root/'runtime',policy.StopValues.parse(data['values']),[data['scenario']]) as work:
    dispatch,remaining,transport=h._dispatch_scalp_preset_exit,h._confirm_cancel_or_reload_remaining,orders._post_kiwoom_with_auth_retry
    def pause_response(*a,**k):
        result=transport(*a,**k)
        arrived.set()
        assert release.wait(5)
        return result
    def owned(stock):
        return deepcopy({k:v for k,v in stock.items() if k.startswith(('last_exit_','exit_','sell_','fast_exit_'))
                         or k in ('buy_qty','buy_price','status')})
    def begin_fast():
        stock,code=normal_kwargs['stock'],normal_kwargs['code']
        def call():
            proof['fast_result']=h.evaluate_and_dispatch_fast_scalp_exit(stock,code,
                main.WS_MANAGER.get_latest_data(code),now_ts=h.time.time())
        worker=threading.Thread(target=call,name='native-fast-interleave')
        workers['fast']=worker;worker.start()
        assert arrived.wait(5)
        with main.DB.get_session() as session:
            row=session.query(RecommendationHistory).filter_by(id=stock['id']).one()
            assert row.status=='SELL_ORDERED' and row.buy_qty==10
        proof['winner']=owned(stock)
        proof['custody_before']=receipts._sell_pending_submit_path(stock['id']).read_bytes().hex()
    def interleave(**kw):
        if kw.get('fast_exit') or normal_kwargs:
            return dispatch(**kw)
        normal_kwargs.update(kw)
        try:
            if point=='before_dispatch':begin_fast()
            return dispatch(**kw)
        finally:
            if workers:
                stock=kw['stock']
                proof['loser_left_winner_unchanged']=owned(stock)==proof['winner']
                proof['custody_after']=receipts._sell_pending_submit_path(stock['id']).read_bytes().hex()
                release.set();workers['fast'].join(5)
                assert not workers['fast'].is_alive()
    def after_account(*a,**k):
        result=remaining(*a,**k)
        if point=='after_account' and threading.current_thread().name!='native-fast-interleave' and not workers:
            begin_fast()
        return result
    try:
        with patch.object(h,'_dispatch_scalp_preset_exit',interleave), \
                patch.object(h,'_confirm_cancel_or_reload_remaining',after_account), \
                patch.object(orders,'_post_kiwoom_with_auth_retry',pause_response):
            result=work.run_cycle(0)
    finally:
        release.set()
        for worker in workers.values():worker.join(5)
    drain=work.drain()
assert proof['loser_left_winner_unchanged']
assert proof['custody_before']==proof['custody_after']
assert proof['fast_result'] is True
assert not drain['errors'] and len(drain['transport_trace'])==1
assert result['semantic']['pending_custody_verified']
assert all(v==0 for v in result['losses'].values())
assert not perf._FULL_ISOLATION['denied']
(root/'result.json').write_text(json.dumps(dict(proof=proof,result=result,drain=drain)))
"""


@pytest.mark.parametrize("point", ["before_dispatch", "after_account"])
def test_native_fast_winner_keeps_generation_metadata_and_durable_custody(
    tmp_path, point
):
    from src.tests.test_main_stop_runtime_workload import _native_scenario
    from src.tests.test_main_stop_policy import baseline

    source = tmp_path / "input.json"
    source.write_text(
        json.dumps(
            dict(scenario=_native_scenario("normal_first"), values=asdict(baseline()))
        )
    )
    root = tmp_path / "private"
    root.mkdir()
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(Path(__file__).resolve().parents[2]),
    )
    answer = subprocess.run(
        [sys.executable, "-c", NATIVE_CHILD, str(root), str(source), point],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert answer.returncode == 0, answer.stdout + answer.stderr
    body = json.loads((root / "result.json").read_text())
    assert body["proof"]["winner"]["last_exit_rule"] == "scalp_hard_stop_pct"
    assert body["result"]["raw_disposition"]["exit_rule"] == "scalp_hard_stop_pct"
    assert body["drain"]["actual_order_submitted"] is False
