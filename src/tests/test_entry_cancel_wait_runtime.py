from src.engine.scalping.entry_cancel_wait_runtime import (
    COUNTERFACTUAL_AUTHORITY,
    candidate_thresholds,
    new_counterfactual_observation,
    observe_counterfactual,
)


def test_candidate_steps_follow_profile_contract():
    assert candidate_thresholds("standard", 60) == [30, 60, 90]
    assert candidate_thresholds("breakout", 120) == [90, 120, 150]
    assert candidate_thresholds("pullback", 600) == [540, 600, 660]


def test_counterfactual_completes_without_order_authority():
    observation = new_counterfactual_observation(
        order_no="1",
        submitted_at=1.0,
        cancelled_at=30.0,
        submitted_price=1000,
        qty=1,
        profile="standard",
        actual_timeout_sec=60,
        selected_timeout_sec=60,
    )
    observation, events = observe_counterfactual(
        observation, now_ts=91.0, current_price=990
    )
    assert any(
        item["stage"] == "entry_cancel_wait_counterfactual_threshold" for item in events
    )
    observation, events = observe_counterfactual(
        observation, now_ts=152.0, current_price=1010
    )
    completed = [
        item
        for item in events
        if item["stage"] == "entry_cancel_wait_counterfactual_completed"
    ]
    assert completed
    assert completed[0]["counterfactual_ev_pct"] == 1.0
    assert COUNTERFACTUAL_AUTHORITY == "entry_cancel_wait_counterfactual_only"


def economic_rows():
    scope=['KRX','KRX_REGULAR','KRX','standard']
    model=dict(validated=True,available_after_date='2026-09-07',actual_parent_ids=[],scope=scope,
        supported_states=['full','no_fill','partial'],net_error_pct=.01)
    rows=[]
    for day in ('2026-09-08','2026-09-09'):
        arms={}
        for timeout,pnl in ((30,20.),(60,10.),(90,30.)):
            arms[str(timeout)]=dict(status='completed_source_only',net_pnl_krw=pnl,stress_net_pnl_krw=pnl-1,
                capital_krw_minutes=1000.,reserve_krw_minutes=100.,modeled_exit_at=day+'T10:02:00+09:00',
                modeled_filled_qty=1,behavior_sha256=str(timeout))
        rows.append(dict(parent_id=day,source_date=day,scope=scope,fill_class='full',requested_qty=1,
            submitted_at=day+'T10:00:00+09:00',notional_krw=1000.,budget_krw=2000.,incumbent_timeout_sec=60,arms=arms))
    return rows,model,{'2026-09-08':1,'2026-09-09':1}


def test_scoped_policy_carry_preserves_common_override_and_off(tmp_path,monkeypatch):
    import hashlib,json
    from datetime import datetime
    from src.engine.scalping import entry_cancel_wait_runtime as runtime
    from src.engine.scalping.strategy_owner_components import digest
    policy=dict(schema=runtime.ECONOMIC_SCHEMA,runtime_family=runtime.RUNTIME_FAMILY,
        effective_date='2026-09-21',source_date='2026-09-18',policy_version='test',
        scope_overrides=[dict(scope=['KRX','KRX_REGULAR','KRX','standard'],
            base_timeout_sec=90,incumbent_timeout_sec=60,timeout_sec=30)])
    policy['sha256']=digest(policy)
    path=tmp_path/'policy.json';path.write_text(json.dumps(policy))
    monkeypatch.setenv('KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_FILE',str(path))
    monkeypatch.setenv('KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())
    stock=dict(effective_venue='KRX',session_bucket='KRX_REGULAR',broker_route='KRX')
    at=datetime.fromisoformat('2026-09-21T10:00:00+09:00').timestamp()
    assert runtime.resolve_scoped_timeout(stock,'standard',90,enabled=True,now_ts=at)==30
    primary=dict(effective_venue='KRX',market_session_bucket='KRX_REGULAR',ai_trace_broker_route='KRX')
    assert runtime.resolve_scoped_timeout({'last_watching_ai_machine_primary_fields':primary},'standard',90,enabled=True,now_ts=at)==30
    assert runtime.resolve_scoped_timeout({**stock,'last_watching_ai_machine_primary_fields':{**primary,'effective_venue':'NXT'}},'standard',90,enabled=True,now_ts=at)==90
    for conflict in (
        {**stock, 'last_watching_ai_machine_primary_fields':{**primary, 'ai_trace_broker_route':'SOR'}},
        {**stock, 'entry_execution_broker_route':'SOR'},
        {**stock, 'last_watching_ai_machine_primary_fields':{**primary, 'market_session_bucket':'NXT_AFTERMARKET'}},
        {**stock, 'market_session_bucket':'NXT_AFTERMARKET'},
    ):
        assert runtime.resolve_scoped_timeout(conflict,'standard',90,enabled=True,now_ts=at)==90
        assert conflict['entry_cancel_wait_policy_receipt']['entry_cancel_wait_policy_status']=='cancel_wait_scope_context_conflict'
    assert runtime.resolve_scoped_timeout(stock,'standard',120,enabled=True,now_ts=at)==120
    assert runtime.resolve_scoped_timeout(stock,'standard',90,enabled=False,now_ts=at)==90
    assert runtime.resolve_scoped_timeout({**stock,'broker_route':'SOR'},'standard',90,enabled=True,now_ts=at)==90
    assert runtime.resolve_scoped_timeout(stock,'standard',90,enabled=True,now_ts=at-86400)==90
    path.write_text(path.read_text()+' ')
    assert runtime.resolve_scoped_timeout(stock,'standard',90,enabled=True,now_ts=at)==90


def test_training_choice_precedes_holdout_and_rejects_without_runner_up():
    from src.engine.scalping.entry_cancel_wait_runtime import evaluate_economic_search
    rows,model,counts=economic_rows()
    rows[1]['arms']['90']['net_pnl_krw']=-5.
    rows[1]['arms']['90']['stress_net_pnl_krw']=-6.
    result=evaluate_economic_search(rows,model,counts)
    assert result['selected']['timeout_sec']==90  # Selected on training alone.
    assert result['status']=='holdout_rejected'
    assert result['consumed_holdouts']==['2026-09-09']
    assert evaluate_economic_search(rows,model,counts,consumed_holdouts=result['consumed_holdouts'])['status']=='holdout_already_consumed'


def test_same_capital_joint_economics_includes_verified_zero_dates():
    from src.engine.scalping.entry_cancel_wait_runtime import evaluate_economic_search
    rows,model,counts=economic_rows()
    counts['2026-09-07']=0
    counts['2026-09-08']=1
    model['available_after_date']='2026-09-06'
    result=evaluate_economic_search(rows,model,counts)
    assert result['status']=='economic_improvement_validated'
    assert result['selected']['training']['mean_day_delta_krw']==10.
    assert result['delta_ev_pct']==2.
    assert result['selected']['timeout_sec']==90


def test_missing_parent_or_capital_cannot_be_promoted():
    from src.engine.scalping.entry_cancel_wait_runtime import evaluate_economic_search
    rows,model,counts=economic_rows()
    counts['2026-09-08']=2
    assert evaluate_economic_search(rows,model,counts)['status']=='unsupported_scope'
    counts['2026-09-08']=1
    rows[0]['budget_krw']=500.
    assert evaluate_economic_search(rows,model,counts)['status']=='no_edge'


def test_full_fill_model_cannot_promote_a_no_fill_candidate():
    from src.engine.scalping.entry_cancel_wait_runtime import evaluate_economic_search
    rows,model,counts=economic_rows();model['supported_states']=['full']
    rows[0]['arms']['30']['modeled_filled_qty']=0
    assert evaluate_economic_search(rows,model,counts)['status']=='unsupported_scope'
