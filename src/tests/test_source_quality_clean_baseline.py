import os

from src.engine.automation import source_quality_clean_baseline as baseline


def test_clean_baseline_filters_pre_baseline_dates(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")

    policy = baseline.write_policy(
        clean_tuning_baseline_date="2026-06-04",
        clean_tuning_baseline_ts_kst="2026-06-04T14:29:09+09:00",
    )
    allowed, excluded = baseline.filter_allowed_dates(
        ["2026-06-02", "2026-06-04", "2026-06-05"],
        policy,
    )

    assert allowed == ["2026-06-04", "2026-06-05"]
    assert excluded == ["2026-06-02"]
    assert baseline.policy_warning_for_date("2026-06-02", policy) == "clean_tuning_baseline_excludes_date:2026-06-02"
    assert baseline.policy_warning_for_date("2026-06-04", policy) is None
    assert policy["runtime_effect"] is False
    assert policy["allowed_runtime_apply"] is False


def test_report_quarantine_reasons_follow_clean_baseline_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")
    policy = baseline.write_policy(clean_tuning_baseline_date="2026-06-04")

    assert (
        baseline.report_quarantine_reason(
            "data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json",
            policy,
        )
        == "pre_clean_baseline_report_archive_only"
    )
    assert (
        baseline.report_quarantine_reason(
            "data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json",
            policy,
            include_baseline_date=True,
        )
        == "same_day_existing_report_regenerate_from_clean_raw"
    )
    assert (
        baseline.report_quarantine_reason(
            "data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json",
            policy,
        )
        is None
    )
    assert baseline.report_is_decision_allowed(
        "data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json",
        policy,
    ) is False


def test_operational_status_reports_are_not_clean_tuning_quarantined(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")
    policy = baseline.write_policy(clean_tuning_baseline_date="2026-06-04")

    preopen_status = "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-02.status.json"
    postclose_status = "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-06-02.status.json"

    assert baseline.report_quarantine_reason(preopen_status, policy, include_baseline_date=True) is None
    assert baseline.report_quarantine_reason(postclose_status, policy, include_baseline_date=True) is None
    assert baseline.report_generated_before_clean_baseline(preopen_status, policy) is False
    assert baseline.report_generated_before_clean_baseline(postclose_status, policy) is False
    assert baseline.report_is_decision_allowed(preopen_status, policy) is True


def test_same_day_report_generated_before_baseline_is_archive_only(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")
    policy = baseline.write_policy(
        clean_tuning_baseline_date="2026-06-04",
        clean_tuning_baseline_ts_kst="2026-06-04T14:29:09+09:00",
    )
    path = tmp_path / "report" / "threshold_cycle_ev_2026-06-04.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"generated_at": "2026-06-04T13:00:00+09:00"}', encoding="utf-8")

    assert baseline.report_generated_before_clean_baseline(path, policy) is True
    assert (
        baseline.report_quarantine_reason(path, policy)
        == "same_day_pre_clean_baseline_report_archive_only"
    )


def test_analytics_quarantine_reason_blocks_pre_baseline_parquet_and_old_duckdb(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")
    policy = baseline.write_policy(
        clean_tuning_baseline_date="2026-06-04",
        clean_tuning_baseline_ts_kst="2026-06-04T14:29:09+09:00",
    )
    old_parquet = tmp_path / "analytics" / "parquet" / "pipeline_events" / "date=2026-06-02" / "x.parquet"
    new_parquet = tmp_path / "analytics" / "parquet" / "pipeline_events" / "date=2026-06-04" / "x.parquet"
    duckdb_path = tmp_path / "analytics" / "duckdb" / "korstockscan_analytics.duckdb"
    for path in (old_parquet, new_parquet, duckdb_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    os.utime(duckdb_path, (0, 0))

    assert baseline.analytics_quarantine_reason(old_parquet, policy) == "pre_clean_baseline_parquet_archive_only"
    assert baseline.analytics_quarantine_reason(new_parquet, policy) is None
    assert baseline.analytics_quarantine_reason(duckdb_path, policy) is not None


def test_quarantine_report_tree_moves_archive_only_reports(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline, "POLICY_PATH", tmp_path / "clean_baseline_policy.json")
    policy = baseline.write_policy(clean_tuning_baseline_date="2026-06-04")
    report_dir = tmp_path / "report"
    old_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-02.json"
    same_day_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-04.json"
    future_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-05.json"
    for path in (old_path, same_day_path, future_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    result = baseline.quarantine_report_tree(
        report_dir,
        quarantine_dir=tmp_path / "source_quality" / "report_quarantine",
        policy=policy,
        include_baseline_date=True,
    )

    assert result["quarantined_count"] == 2
    assert not old_path.exists()
    assert not same_day_path.exists()
    assert future_path.exists()
    assert list((tmp_path / "source_quality" / "report_quarantine").glob("*"))
