from __future__ import annotations

from src.engine.error_detectors.schedule_contract import evaluate_schedule_contract


def test_unavailable_crontab_preserves_expectation():
    status, details = evaluate_schedule_contract(
        None,
        markers=["JOB_MARKER"],
    )

    assert status == "unknown"
    assert details["reason"] == "installed_crontab_unavailable_expectation_preserved"


def test_commented_marker_does_not_install_job():
    status, _ = evaluate_schedule_contract(
        "# 10 20 * * 1-5 runner # JOB_MARKER\n",
        markers=["JOB_MARKER"],
    )

    assert status == "disabled_not_installed"


def test_explicit_false_parent_disables_job():
    status, details = evaluate_schedule_contract(
        "10 20 * * 1-5 PARENT_ENABLED=false runner # JOB_MARKER\n",
        markers=["JOB_MARKER"],
        parent_env_key="PARENT_ENABLED",
        parent_default_enabled=True,
    )

    assert status == "disabled_by_parent"
    assert details["parent_explicit_values"] == ["false"]


def test_quoted_true_parent_enables_job():
    status, _ = evaluate_schedule_contract(
        "10 20 * * 1-5 PARENT_ENABLED='true' runner # JOB_MARKER\n",
        markers=["JOB_MARKER"],
        parent_env_key="PARENT_ENABLED",
        parent_default_enabled=False,
    )

    assert status == "enabled"
