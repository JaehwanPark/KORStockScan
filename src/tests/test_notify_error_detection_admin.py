import json

from src.engine import notify_error_detection_admin as notifier


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
    alert["generation"] = "b" * 64
    assert notify() == "duplicate_incident"
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
    assert len(sent) == 1
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
    assert value['historical_semantic_incidents'] == []
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
