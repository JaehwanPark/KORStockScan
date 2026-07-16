import json

from src.engine import notify_error_detection_admin as notifier


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


def test_notify_from_report_sends_fail_and_cooldowns(tmp_path, monkeypatch):
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
    assert second == "cooldown"
    assert len(sent) == 1
    assert "ERROR DETECTION ALERT" in sent[0]
    assert "cron_completion" in sent[0]


def test_notify_from_report_sends_kiwoom_auth_8005_warning(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    payload = {
        "timestamp": "2026-05-27T10:05:00+09:00",
        "summary_severity": "warning",
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
