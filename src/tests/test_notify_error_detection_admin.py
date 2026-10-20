import json

from src.engine import notify_error_detection_admin as notifier


def test_native_machine_alert_and_exact_bound_recovery(tmp_path, monkeypatch):
    report, state = tmp_path/'report.json', tmp_path/'state.json'
    sent = []
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('token', 'admin'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *args: sent.append(args[-1]))
    incident = dict(source_date='2026-10-06', target_date='2026-10-07',
        stage='main_machine_policy', scope='report', reason='continuous_reversal_report_hash_or_date_invalid',
        status='source_invalid', generation='a'*64, owner='DirectFamilySourceRepairMainMechanisticEntry')
    details = dict(semantic_alerts=[incident], semantic_source_bindings=[
        dict(incident, as_of_date='2026-10-07')])
    payload = dict(target_date='2026-10-07', results=[dict(detector_id='artifact_freshness',
        severity='warning', details=details)])
    def call():
        report.write_text(json.dumps(payload))
        return notifier.notify_from_report(report, mode='full', log_file='log', state_file=state)
    assert call() == 'sent'
    assert len(sent) == 1
    details['semantic_alerts'] = []
    observed = dict(source_date='2026-10-06', target_date='2026-10-08',
        report_sha256='b'*64, status='cumulative_winrate_selected', findings=[])
    details['machine_result_semantics'] = observed
    assert call() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    observed['target_date'] = '2026-10-07'
    observed['findings'] = ['continuous_reversal_dated_policy_invalid']
    assert call() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    observed['findings'] = []
    details['semantic_source_bindings'] = [dict(stage='main_machine_policy',
        as_of_date='2026-10-07', source_date='2026-10-06', target_date='2026-10-07',
        generation=observed['report_sha256'], status=observed['status'])]
    assert call() == 'no_alert'
    value = json.loads(state.read_text())
    assert value['active_incident_count'] == 0
    assert value['historical_semantic_incidents'][-1]['disposition'] == 'native_recovered'


def test_semantic_warning_notifies_stably_and_unobservable_is_not_recovery(tmp_path, monkeypatch):
    report, state = tmp_path / "report.json", tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(notifier, "_send_telegram", lambda *_args: sent.append(_args[-1]))
    alert = {"source_date": "2026-10-02", "stage": "main_auxiliary_policy", "scope": "report",
             "reason": "auxiliary_outcome_label_source_gap", "status": "source_gap",
             "owner": "compact_auxiliary_paired_replay", "generation": "a" * 64,
             "artifact": "/report/compact.json"}
    payload = {"target_date": "2026-10-02", "timestamp": "2026-10-02T21:00:00+09:00",
        "results": [{"detector_id": "artifact_freshness", "severity": "warning",
                     "summary": "Semantic warnings", "details": {"semantic_alerts": [alert]}}]}
    def notify():
        report.write_text(json.dumps(payload))
        return notifier.notify_from_report(report, mode="full", log_file="logs/health.log", state_file=state, now_ts=1000)
    assert notify() == "sent"
    assert notify() == "duplicate_incident"
    alert["generation"] = "b" * 64
    assert notify() == "sent"
    payload["results"][0]["details"] = {"auxiliary_result_semantics": {"status": "unobservable"}}
    assert notify() == "no_alert"
    assert json.loads(state.read_text())["active_incident_count"] == 1
    for observed in (
        {"status": "pass", "report_sha256": "c" * 64, "source_date": "2026-10-01"},
        {"status": "source_invalid", "report_sha256": "c" * 64, "source_date": "2026-10-02"},
    ):
        payload["results"][0]["details"] = {"auxiliary_result_semantics": observed}
        assert notify() == "no_alert"
        assert json.loads(state.read_text())["active_incident_count"] == 1
    payload["results"][0]["details"] = {"semantic_alerts": [alert]}
    assert notify() == "duplicate_incident"
    payload["results"][0]["details"] = {"auxiliary_result_semantics": {
        "status": "incumbent_carry", "report_sha256": "c" * 64, "source_date": "2026-10-02"}}
    assert notify() == "no_alert"
    assert json.loads(state.read_text())["active_incident_count"] == 0
    assert len(sent) == 2
    assert "source=2026-10-02" in sent[0]


def _write_report(path, *, severity="fail", summary="Cron job failures"):
    payload = {
        "timestamp": "2026-05-13T07:50:00+09:00",
        "summary_severity": severity,
        "results": [
            {
                "detector_id": "cron_completion",
                "severity": severity,
                "summary": summary,
                "recommended_action": "Check logs",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_notifier_does_not_silently_deduplicate_undisplayed_incidents(tmp_path, monkeypatch):
    sent = []
    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(notifier, "_send_telegram", lambda *args: sent.append(args[-1]))
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"results": [{"detector_id": f"detector-{i}",
        "severity": "fail", "summary": f"failure-{i}"} for i in range(7)]}))
    assert notifier.notify_from_report(path, mode="full", log_file="log",
                                       state_file=tmp_path / "state.json") == "sent"
    assert len(sent) == 3
    assert all(f"failure-{i}" in "\n".join(sent) for i in range(7))


def test_notify_from_report_skips_when_no_fail(tmp_path):
    report = tmp_path / "report.json"
    _write_report(report, severity="warning", summary="Artifact warnings")

    status = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=tmp_path / "state.json",
        now_ts=1000.0,
    )

    assert status == "no_alert"


def test_notify_from_report_sends_fail_once_per_active_incident(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    state = tmp_path / "state.json"
    _write_report(report)
    sent = []

    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(
        notifier,
        "_send_telegram",
        lambda token, admin_id, message: sent.append(message),
    )

    first = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=state,
        cooldown_sec=600,
        now_ts=1000.0,
    )
    second = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=state,
        cooldown_sec=600,
        now_ts=1200.0,
    )

    assert first == "sent"
    assert second == "duplicate_incident"
    assert len(sent) == 1
    assert "ERROR DETECTION ALERT" in sent[0]
    assert "cron_completion" in sent[0]


def test_notify_from_report_realerts_after_incident_resolves(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    state = tmp_path / "state.json"
    _write_report(report)
    sent = []
    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(
        notifier,
        "_send_telegram",
        lambda token, admin_id, message: sent.append(message),
    )

    assert (
        notifier.notify_from_report(
            report,
            mode="full",
            log_file="logs/run_error_detection.log",
            state_file=state,
            now_ts=1000.0,
        )
        == "sent"
    )

    _write_report(report, severity="pass", summary="All cron jobs passed")
    assert (
        notifier.notify_from_report(
            report,
            mode="full",
            log_file="logs/run_error_detection.log",
            state_file=state,
            now_ts=1100.0,
        )
        == "no_alert"
    )

    _write_report(report)
    assert (
        notifier.notify_from_report(
            report,
            mode="full",
            log_file="logs/run_error_detection.log",
            state_file=state,
            now_ts=1200.0,
        )
        == "sent"
    )
    assert len(sent) == 2


def test_notify_from_report_sends_only_new_incident_in_active_set(
    tmp_path, monkeypatch
):
    report = tmp_path / "report.json"
    state = tmp_path / "state.json"
    _write_report(report)
    sent = []
    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(
        notifier,
        "_send_telegram",
        lambda token, admin_id, message: sent.append(message),
    )

    assert (
        notifier.notify_from_report(
            report,
            mode="full",
            log_file="logs/run_error_detection.log",
            state_file=state,
            now_ts=1000.0,
        )
        == "sent"
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["results"].append(
        {
            "detector_id": "resource_usage",
            "severity": "fail",
            "summary": "Memory available 459.1MB < 500.0MB",
            "recommended_action": "Inspect memory pressure",
        }
    )
    report.write_text(json.dumps(payload), encoding="utf-8")

    assert (
        notifier.notify_from_report(
            report,
            mode="full",
            log_file="logs/run_error_detection.log",
            state_file=state,
            now_ts=1100.0,
        )
        == "sent"
    )
    assert len(sent) == 2
    assert "resource_usage [fail]" in sent[1]
    assert "cron_completion [fail]" not in sent[1]


def test_notify_from_report_normalizes_dynamic_numbers_in_incident(
    tmp_path, monkeypatch
):
    report = tmp_path / "report.json"
    state = tmp_path / "state.json"
    sent = []
    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(
        notifier,
        "_send_telegram",
        lambda token, admin_id, message: sent.append(message),
    )

    _write_report(report, summary="Main loop heartbeat stale for 28s (timeout=15s).")
    first = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=state,
        now_ts=1000.0,
    )
    _write_report(report, summary="Main loop heartbeat stale for 33s (timeout=15s).")
    second = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=state,
        now_ts=5000.0,
    )

    assert first == "sent"
    assert second == "duplicate_incident"
    assert len(sent) == 1


def test_notify_from_report_sends_kiwoom_auth_8005_warning(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    payload = {
        "timestamp": "2026-05-27T10:05:00+09:00",
        "summary_severity": "warning",
        "operational_mutations": ["kiwoom_auth_restart_flag"],
        "results": [
            {
                "detector_id": "kiwoom_auth_8005_restart",
                "severity": "warning",
                "summary": "Fresh Kiwoom auth 8005 detected; restart.flag created for graceful bot restart.",
                "recommended_action": "Verify bot restart",
            }
        ],
    }
    report.write_text(json.dumps(payload), encoding="utf-8")
    sent = []

    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("token", "admin"))
    monkeypatch.setattr(
        notifier,
        "_send_telegram",
        lambda token, admin_id, message: sent.append(message),
    )

    status = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=tmp_path / "state.json",
        now_ts=1000.0,
    )

    assert status == "sent"
    assert len(sent) == 1
    assert "kiwoom_auth_8005_restart [warning]" in sent[0]
    assert "operational mutations: kiwoom_auth_restart_flag" in sent[0]


def test_notify_from_report_missing_config_does_not_raise(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    _write_report(report)

    monkeypatch.setattr(notifier, "_load_telegram_config", lambda: ("", ""))

    status = notifier.notify_from_report(
        report,
        mode="full",
        log_file="logs/run_error_detection.log",
        state_file=tmp_path / "state.json",
        now_ts=1000.0,
    )

    assert status == "missing_config"


def test_cancel_wait_detector_warning_reaches_notification_and_recovers(tmp_path, monkeypatch):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture, _reseal_reconciliation
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics, _semantic_alerts
    from src.engine.automation import entry_cancel_wait_tuning as cancel
    report, policy, path, pp = _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=True)
    original_report, original_policy = json.loads(json.dumps(report)), json.loads(json.dumps(policy))
    report['historical_reconciliation']['zero_is_verified'] = True
    _reseal_reconciliation(report)
    policy['report_proof_sha256'] = report['proof_sha256']
    policy['sha256'] = cancel._digest({k:v for k,v in policy.items() if k != 'sha256'})
    path.write_text(json.dumps(report)); pp.write_text(json.dumps(policy))
    semantics = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    details = {'entry_cancel_wait_result_semantics':semantics,
               'semantic_alerts':_semantic_alerts('entry_cancel_wait_tuning', semantics, '2026-10-02')}
    artifact = tmp_path/'detector.json'; state = tmp_path/'notify-state.json'
    sent = []
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('token','admin'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_a: sent.append(_a[-1]))
    payload = {'target_date':'2026-10-02','results':[dict(detector_id='artifact_freshness',severity='warning',details=details)]}
    def notify():
        artifact.write_text(json.dumps(payload))
        return notifier.notify_from_report(artifact, mode='full', log_file='log', state_file=state, now_ts=1000)
    assert notify() == 'sent'
    assert notify() == 'duplicate_incident'
    assert len(sent) == 1
    details.clear(); details['entry_cancel_wait_result_semantics'] = {'status':'not_evaluated_legacy','source_date':'2026-10-02'}
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    path.write_text(json.dumps(original_report)); pp.write_text(json.dumps(original_policy))
    details['entry_cancel_wait_result_semantics'] = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 0


def test_cancel_wait_warning_accepts_only_exact_previous_native_run_date():
    alert = dict(source_date='2026-10-02',stage='entry_cancel_wait_tuning',scope='report',
        reason='cancel_wait_false_historical_zero',status='source_invalid',owner='EntryCancelWaitSourceReconciliation1002')
    observed = dict(source_date='2026-10-02',execution=dict(source_date='2026-10-02',status='running',run_id='native-1002'))
    item = dict(detector_id='artifact_freshness',severity='warning',details={
        'semantic_alerts':[alert],'entry_cancel_wait_result_semantics':observed})
    report = dict(target_date='2026-10-03',results=[item])
    assert len(notifier._alert_results(report)) == 1
    observed['execution']['source_date'] = '2026-10-01'
    assert notifier._alert_results(report) == []


def test_cancel_wait_consumer_incident_is_not_recovered_by_pending_consumers(tmp_path, monkeypatch):
    artifact, state = tmp_path/'detector.json', tmp_path/'state.json'
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('token','admin'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_a: None)
    incident = dict(source_date='2026-10-02',stage='entry_cancel_wait_tuning',scope='report',
        reason='cancel_wait_consumer_projection_invalid',status='source_invalid',
        owner='EntryCancelWaitSourceReconciliation1002')
    observed = dict(source_date='2026-10-02',status='source_invalid',report_sha256='a'*64,
        findings=[incident['reason']],consumers={'status':'pending'})
    details = {'semantic_alerts':[incident], 'entry_cancel_wait_result_semantics':observed}
    payload = dict(target_date='2026-10-02',results=[dict(detector_id='artifact_freshness',severity='warning',details=details)])
    def notify():
        artifact.write_text(json.dumps(payload))
        return notifier.notify_from_report(artifact,mode='full',log_file='log',state_file=state,now_ts=1000)
    assert notify() == 'sent'
    details['semantic_alerts'] = []
    observed.update(status='incumbent_carry',findings=[])
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    observed['consumers']['status'] = 'verified'
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 0


def test_cancel_wait_finished_previous_run_warning_and_recovery_keep_identity(tmp_path, monkeypatch):
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics, _semantic_alerts
    from src.tests.test_error_detector_artifact_freshness import _cancel_wait_consumer_fixture
    paths = _cancel_wait_consumer_fixture(tmp_path,monkeypatch)
    artifact, state = tmp_path/'detector.json', tmp_path/'state.json'
    text = paths['checklist'].read_text()
    paths['checklist'].unlink()
    sent = []
    monkeypatch.setattr(notifier, '_load_telegram_config',lambda:('token','admin'))
    monkeypatch.setattr(notifier, '_send_telegram',lambda *_a:sent.append(_a[-1]))
    def notify():
        result = _entry_cancel_wait_result_semantics(tmp_path,'2026-10-02')
        details = {'entry_cancel_wait_result_semantics':result,
            'semantic_alerts':_semantic_alerts('entry_cancel_wait_tuning',result,'2026-10-02')}
        artifact.write_text(json.dumps(dict(target_date='2026-10-03',results=[dict(
            detector_id='artifact_freshness',severity='warning',details=details)])))
        return notifier.notify_from_report(artifact,mode='full',log_file='log',state_file=state,now_ts=1000)
    assert notify() == 'sent'
    assert notify() == 'duplicate_incident'
    paths['checklist'].write_text(text)
    assert notify() == 'no_alert'
    value = json.loads(state.read_text())
    assert value['active_incident_count'] == 0
    assert value['historical_semantic_incidents'][-1]['disposition'] == 'native_recovered'
    assert len(sent) == 1


def test_cancel_wait_execution_incident_needs_current_command_success_to_recover(tmp_path, monkeypatch):
    artifact, state = tmp_path/'detector.json', tmp_path/'state.json'
    monkeypatch.setattr(notifier,'_load_telegram_config',lambda:('token','admin'))
    monkeypatch.setattr(notifier,'_send_telegram',lambda *_a:None)
    alert = dict(source_date='2026-10-02',stage='entry_cancel_wait_tuning',scope='report',
        reason='cancel_wait_execution_failed',status='source_invalid',owner='EntryCancelWaitSourceReconciliation1002')
    observed = dict(source_date='2026-10-02',status='source_invalid',report_sha256='a'*64,findings=[alert['reason']],
        execution=dict(source_date='2026-10-02',status='running',run_id='current',command_status='failed'))
    details = {'entry_cancel_wait_result_semantics':observed,'semantic_alerts':[alert]}
    payload = dict(target_date='2026-10-02',results=[dict(detector_id='artifact_freshness',severity='warning',details=details)])
    def notify():
        artifact.write_text(json.dumps(payload))
        return notifier.notify_from_report(artifact,mode='full',log_file='log',state_file=state,now_ts=1000)
    assert notify() == 'sent'
    details['semantic_alerts'] = []
    observed.update(status='incumbent_carry',findings=[])
    observed['execution'].pop('command_status')
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    observed['execution']['command_status'] = 'succeeded'
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 0


def test_new_native_states_and_nonmachine_recovery_are_persisted(tmp_path, monkeypatch):
    from src.engine.monitoring.semantic_incident_contract import fingerprint
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('token', 'admin'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_: None)
    for stage, status in [('main_machine_policy', 'operator_initial_registered'),
                          ('main_auxiliary_policy', 'verified_carried'),
                          ('main_machine_policy', 'published_policy'),
                          ('holding_profit_exit', 'pending_terminal'),
                          ('initial_quantity', 'valid_empty')]:
        alert = dict(stage=stage, source_date='2026-10-08', target_date='2026-10-12', scope='report',
                     reason='policy_binding_gap', status='source_invalid', owner='old', generation=None, artifact='/native/report')
        state = tmp_path / (stage + status + '.json')
        state.write_text(json.dumps({'semantic_incidents': {'legacy': alert}}))
        obs = dict(source_date=alert['source_date'], target_date=alert['target_date'], status=status,
                   findings=[], native_validated=True, observation_complete=True, report_sha256='a'*64)
        details = dict(semantic_observations=[dict(stage=stage, semantics=obs)], semantic_source_bindings=[
            dict(stage=stage, as_of_date='2026-10-11', generation=obs['report_sha256'],
                 **{k: obs[k] for k in ['source_date', 'target_date', 'status']})])
        report = tmp_path/'report.json'
        report.write_text(json.dumps(dict(target_date='2026-10-11', results=[dict(detector_id='artifact_freshness', details=details)])))
        assert notifier.notify_from_report(report, mode='full', log_file='', state_file=state) == 'no_alert'
        result = json.loads(state.read_text())
        assert result['semantic_incidents'] == {}
        assert result['historical_semantic_incidents'][-1]['disposition'] == 'native_recovered'
        assert fingerprint(alert) == fingerprint(dict(alert, owner='new'))


def test_comparison_source_gap_and_partial_read_do_not_recover():
    from src.engine.monitoring.semantic_incident_contract import closure_verified
    incident = dict(stage='main_auxiliary_policy', source_date='2026-10-08', scope='report', reason='auxiliary_outcome_label_source_gap')
    obs = dict(source_date='2026-10-08', status='source_gap', report_sha256='a'*64, findings=[],
               policy_states={'comparison_state': 'source_gap'}, observation_complete=True)
    assert not closure_verified(incident, obs, True)
    # Structure may recover independently of incomplete economic comparison.
    incident['reason'] = 'policy_binding_gap'
    assert closure_verified(incident, obs, True)
    obs['observation_complete'] = False
    assert not closure_verified(incident, obs, True)


def test_overflow_and_corrupt_state_are_explicit(tmp_path):
    from src.engine.monitoring.semantic_incident_contract import reconcile
    rows = [dict(stage='initial_quantity', source_date='2026-10-11', scope=str(n), reason='source_gap', artifact='/native') for n in range(135)]
    state = reconcile({}, {}, '2026-10-11', rows, source_matches=lambda _: True)
    assert len(state['semantic_incidents']) == 128
    assert state['semantic_state_complete'] is False
    assert state['semantic_overflow']['unresolved_omitted_count'] == 7
    path = tmp_path/'state.json'; path.write_text('{damaged')
    assert notifier.notify_from_report(tmp_path/'absent', mode='full', log_file='', state_file=path) == 'state_invalid'
    assert path.read_text() == '{damaged'


def test_notification_lock_and_failed_delivery_are_retryable(tmp_path, monkeypatch):
    import fcntl
    report, state = tmp_path/'report.json', tmp_path/'state.json'
    _write_report(report)
    with state.with_suffix('.json.lock').open('a') as locked:
        fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert notifier.notify_from_report(report, mode='full', log_file='', state_file=state) == 'state_busy'
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('token', 'admin'))
    def fail(*_): raise OSError('transport')
    monkeypatch.setattr(notifier, '_send_telegram', fail)
    import pytest
    with pytest.raises(OSError): notifier.notify_from_report(report, mode='full', log_file='', state_file=state)
    value = json.loads(state.read_text())
    assert not value.get('sent_at')
    assert value['last_delivery_status'] == 'failed_retryable'
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_: None)
    assert notifier.notify_from_report(report, mode='full', log_file='', state_file=state) == 'sent'


def test_delayed_old_report_cannot_clear_new_failure(tmp_path,monkeypatch):
    report,state=tmp_path/'report.json',tmp_path/'state.json'
    _write_report(report)
    payload=json.loads(report.read_text());payload['timestamp']='2026-10-11T10:00:00+09:00'
    report.write_text(json.dumps(payload))
    monkeypatch.setattr(notifier,'_load_telegram_config',lambda:('token','admin'))
    monkeypatch.setattr(notifier,'_send_telegram',lambda *_:None)
    assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='sent'
    before=state.read_bytes()
    payload.update(timestamp='2026-10-11T09:59:00+09:00',results=[])
    report.write_text(json.dumps(payload))
    assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='stale_report'
    assert state.read_bytes()==before


def test_failed_delivery_survives_unobservable_round_trip(tmp_path,monkeypatch):
    import pytest
    report,state=tmp_path/'report.json',tmp_path/'state.json'
    _write_report(report)
    original=report.read_bytes()
    monkeypatch.setattr(notifier,'_load_telegram_config',lambda:('token','admin'))
    monkeypatch.setattr(notifier,'_send_telegram',lambda *_:(_ for _ in ()).throw(OSError('offline')))
    with pytest.raises(OSError):notifier.notify_from_report(report,mode='full',log_file='',state_file=state)
    report.write_text(json.dumps(dict(target_date='2026-10-11',results=[])))
    assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='no_alert'
    report.write_bytes(original)
    monkeypatch.setattr(notifier,'_send_telegram',lambda *_:None)
    assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='sent'


def test_corrupt_report_preserves_incident_state(tmp_path):
    report,state=tmp_path/'report.json',tmp_path/'state.json'
    state.write_text(json.dumps({'semantic_incidents':{'old':{'stage':'initial_quantity'}}}))
    before=state.read_bytes()
    for value in ('{incomplete', '[]', '{}', '{"results":null}'):
        report.write_text(value)
        assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='report_invalid'
        assert state.read_bytes()==before


def test_verified_scope_recovers_without_clearing_other_scope():
    from src.engine.monitoring.semantic_incident_contract import closure_verified
    incident=dict(stage='initial_quantity',source_date='2026-10-12',scope='A',reason='policy_binding')
    observation=dict(source_date='2026-10-12',status='source_gap',report_sha256='a'*64,
        native_validated=True,observation_complete=True,findings=['scope_B_unobserved'],
        scopes={'A':dict(native_validated=True,observation_complete=True,report_sha256='a'*64,findings=[])})
    assert closure_verified(incident,observation,True)
    assert not closure_verified(dict(incident,scope='B'),observation,True)
    observation['scopes']['A']['report_sha256']='b'*64
    assert not closure_verified(incident,observation,True)


def test_partial_delivery_retries_only_failed_batch(tmp_path,monkeypatch):
    import pytest
    report,state=tmp_path/'report.json',tmp_path/'state.json'
    payload=dict(target_date='2026-10-12',results=[dict(detector_id='distinct_'+c,severity='fail',summary=c) for c in 'abcd'])
    report.write_text(json.dumps(payload))
    monkeypatch.setattr(notifier,'_load_telegram_config',lambda:('token','admin'))
    messages=[]
    def send(*args):
        messages.append(args[-1])
        if len(messages)==2:raise OSError('second batch failed')
    monkeypatch.setattr(notifier,'_send_telegram',send)
    with pytest.raises(OSError):notifier.notify_from_report(report,mode='full',log_file='',state_file=state)
    assert len(json.loads(state.read_text())['notified_incident_fingerprints'])==3
    assert notifier.notify_from_report(report,mode='full',log_file='',state_file=state)=='sent'
    assert 'distinct_d' in messages[-1] and 'distinct_a' not in messages[-1]


def _holding_gap_fixture():
    from src.engine.monitoring.semantic_incident_contract import holding_gap_identity
    semantics = dict(schema='holding_profit_exit_semantics_v2', status='source_gap', semantic_status='source_gap',
        findings=[], policy_binding_gaps=[], runtime_consumption_gaps=[],
        source_gaps=[dict(position_id='42', reason='tp_first_crossing_transition_missing')],
        source_gap_details=[dict(position_id='42', reason='tp_first_crossing_transition_missing',
            signal_id='signal-1', source_disposition='sampled_grid_exhausted_before_signal', historical_recovery_proven=False)],
        lifecycle=[dict(position_key='record:42', signal_id='signal-1', buy_fill_identity='b'*64)])
    identity = holding_gap_identity(semantics)
    alert = dict(source_date='2026-10-16', target_date='2026-10-16', stage='holding_profit_exit',
        scope='report', reason='source_gap', status='source_gap', generation='a'*64, artifact='/release-one/report',
        owner='HoldingProfitExitSourceContractRepair', source_gap_identity=identity)
    observed = dict(source_date=alert['source_date'], target_date=alert['target_date'], status='source_gap',
        findings=['source_gap'], native_validated=True, observation_complete=True,
        report_sha256=alert['generation'], source_gap_identity=identity)
    details = dict(semantic_alerts=[alert], holding_profit_exit_semantics=observed,
        semantic_source_bindings=[dict(stage=alert['stage'], as_of_date='2026-10-16',
            source_date=alert['source_date'], target_date=alert['target_date'], status='source_gap', generation=alert['generation'])])
    return semantics, alert, observed, details


def test_holding_original_gap_deduplicates_regeneration_but_keeps_unresolved(tmp_path, monkeypatch):
    import copy
    from src.engine.monitoring.semantic_incident_contract import fingerprint
    _, alert, observed, details = _holding_gap_fixture()
    report, state = tmp_path/'report.json', tmp_path/'state.json'
    sent=[]
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('fake', 'fake'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_: sent.append(1))
    def notify():
        report.write_text(json.dumps(dict(target_date='2026-10-16', results=[dict(detector_id='artifact_freshness', details=details)])))
        return notifier.notify_from_report(report, mode='full', log_file='', state_file=state)
    assert notify() == 'sent'
    key=fingerprint(alert)
    alert.update(generation='c'*64, artifact='/different-release/report')
    observed['report_sha256']=alert['generation']
    details['semantic_source_bindings'][0]['generation']=alert['generation']
    assert notify() == 'duplicate_incident'
    persisted=json.loads(state.read_text())
    assert persisted['notified_incident_fingerprints'] == [key]
    assert persisted['semantic_incidents'][key]['generation'] == 'c'*64
    assert not persisted['historical_semantic_incidents']
    # Unobservable/missing alert rounds cannot manufacture recovery.
    details['semantic_alerts']=[]
    assert notify() == 'no_alert'
    assert json.loads(state.read_text())['active_incident_count'] == 1
    details['semantic_alerts']=[alert]
    # Distinct BUY, signal, position or population must alert even at the same count.
    for index, value in ((0,'record:43'),(1,'d'*64),(2,'signal-2')):
        changed=copy.deepcopy(alert)
        changed['source_gap_identity']['gaps'][0][index]=value
        observed['source_gap_identity']=changed['source_gap_identity']
        details['semantic_alerts']=[changed]
        assert notify() == 'sent'
    assert len(sent)==4


def test_holding_gap_legacy_delivery_upgrade_requires_exact_native_bytes(tmp_path, monkeypatch):
    from src.engine.monitoring.semantic_incident_contract import fingerprint
    _, alert, observed, details = _holding_gap_fixture()
    legacy={k:v for k,v in alert.items() if k!='source_gap_identity'}
    old_key=fingerprint(legacy)
    report=tmp_path/'report.json'
    report.write_text(json.dumps(dict(target_date='2026-10-16', results=[dict(detector_id='artifact_freshness', details=details)])))
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('fake', 'fake'))
    sent=[]
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_: sent.append(1))
    for defect in (None, 'hash', 'partial', 'binding', 'undelivered'):
        state=tmp_path/f'{defect}.json'
        old=dict(legacy)
        if defect=='hash':old['generation']='e'*64
        if defect in {'partial','binding'}:old['generation']='f'*64
        if defect=='partial':observed['observation_complete']=False
        if defect=='binding':details['semantic_source_bindings']=[]
        report.write_text(json.dumps(dict(target_date='2026-10-16', results=[dict(detector_id='artifact_freshness', details=details)])))
        key=fingerprint(old)
        state.write_text(json.dumps(dict(semantic_incidents={key:old}, notified_incident_fingerprints=[] if defect=='undelivered' else [key])))
        result=notifier.notify_from_report(report, mode='full', log_file='', state_file=state)
        assert result == ('duplicate_incident' if defect is None else 'sent')
        if defect is None:
            assert not sent
            assert json.loads(state.read_text())['notified_incident_fingerprints']==[fingerprint(alert)]
        observed['observation_complete']=True
        details['semantic_source_bindings']=[dict(stage=alert['stage'], as_of_date='2026-10-16',
            source_date=alert['source_date'], target_date=alert['target_date'], status='source_gap', generation=alert['generation'])]


def test_holding_gap_identity_rejects_partial_ambiguous_or_other_losses():
    import copy
    from src.engine.monitoring.semantic_incident_contract import holding_gap_identity, fingerprint
    semantics, alert, _, _ = _holding_gap_fixture()
    for defect in ('missing', 'duplicate', 'extra', 'reason', 'signal', 'buy', 'invalid_type', 'policy', 'runtime', 'finding'):
        value=copy.deepcopy(semantics)
        if defect=='missing':value.pop('source_gap_details')
        if defect=='duplicate':value['source_gap_details']*=2
        if defect=='extra':value['source_gaps'].append(dict(position_id='43',reason='unknown'))
        if defect=='reason':value['source_gaps'][0]['reason']='other_gap'
        if defect=='signal':value['source_gap_details'][0]['signal_id']='unobserved'
        if defect=='buy':value['lifecycle'][0]['buy_fill_identity']='z'*64
        if defect=='invalid_type':value['source_gap_details'][0]['position_id']=[]
        if defect=='policy':value['policy_binding_gaps']=['missing']
        if defect=='runtime':value['runtime_consumption_gaps']=['missing']
        if defect=='finding':value['findings']=['invalid']
        assert holding_gap_identity(value) is None, defect
    missing=dict(alert, source_gap_identity=None)
    assert fingerprint(missing)!=fingerprint(dict(missing,generation='f'*64))
    assert fingerprint(alert)!=fingerprint(dict(alert,reason='other_gap'))
    changed=json.loads(json.dumps(alert));changed['source_gap_identity']['gaps'].append(
        ['record:43','d'*64,'signal-2','tp_first_crossing_transition_missing','sampled_grid_exhausted_before_signal'])
    assert fingerprint(alert)!=fingerprint(changed)


def test_original_missing_buy_gap_uses_native_delivery_dedup_and_keeps_changed_sources_actionable(tmp_path, monkeypatch):
    import copy
    from src.tests.test_holding_exit_sentinel import _missing_buy_flow_report
    from src.engine.monitoring.semantic_incident_contract import holding_gap_identity, fingerprint
    _, alert, observed, details = _holding_gap_fixture()
    identity = holding_gap_identity(_missing_buy_flow_report())
    alert['source_gap_identity'] = observed['source_gap_identity'] = identity
    report, state = tmp_path/'report.json', tmp_path/'state.json'
    sent = []
    monkeypatch.setattr(notifier, '_load_telegram_config', lambda: ('fake', 'fake'))
    monkeypatch.setattr(notifier, '_send_telegram', lambda *_: sent.append(1))
    def notify():
        report.write_text(json.dumps(dict(target_date='2026-10-16', results=[
            dict(detector_id='artifact_freshness', details=details)])))
        return notifier.notify_from_report(report, mode='full', log_file='', state_file=state)
    assert notify() == 'sent'
    alert.update(generation='c'*64, artifact='/new-release/report')
    observed['report_sha256'] = alert['generation']
    details['semantic_source_bindings'][0]['generation'] = alert['generation']
    assert notify() == 'duplicate_incident'
    persisted = json.loads(state.read_text())
    assert persisted['active_incident_count'] == 1
    assert persisted['semantic_incidents'][fingerprint(alert)]['status'] == 'source_gap'
    changed = holding_gap_identity(_missing_buy_flow_report(damage='terminal'))
    alert['source_gap_identity'] = observed['source_gap_identity'] = changed
    assert notify() == 'sent' and len(sent) == 2
    for defect in ('missing', 'mismatch', 'invalid', 'partial', 'new_gap'):
        semantics = copy.deepcopy(_missing_buy_flow_report())
        if defect == 'missing': semantics['source_gap_details'].pop()
        if defect == 'mismatch': semantics['source_gap_details'][0]['terminal_source_sha256'] = 'f'*64
        if defect == 'invalid': semantics['source_gap_details'][0]['signal_source_sha256'] = 'bad'
        if defect == 'partial': semantics['runtime_consumption_gaps'] = ['unproven']
        if defect == 'new_gap': semantics['source_gaps'].append(dict(position_id='99', reason='new_loss'))
        assert holding_gap_identity(semantics) is None, defect
