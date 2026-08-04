from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detectors.resource_usage import ResourceUsageDetector
from src.engine.monitoring.system_metric_sampler import (
    _append_json_line_durable,
    _cpu_pct,
)


def test_cpu_pct_separates_compute_from_iowait():
    prev = {
        "user": 100,
        "nice": 0,
        "system": 100,
        "idle": 100,
        "iowait": 100,
        "irq": 0,
        "softirq": 0,
        "steal": 0,
    }
    curr = {
        "user": 120,
        "nice": 0,
        "system": 110,
        "idle": 102,
        "iowait": 158,
        "irq": 0,
        "softirq": 0,
        "steal": 0,
    }

    assert _cpu_pct(curr, prev) == {
        "cpu_busy_pct": 97.78,
        "cpu_non_idle_pct": 97.78,
        "cpu_compute_busy_pct": 33.33,
        "iowait_pct": 64.44,
    }


def test_system_metric_append_writes_complete_json_records(tmp_path):
    sample_path = tmp_path / "system_metric_samples.jsonl"

    _append_json_line_durable(sample_path, {"epoch": 1, "cpu": {"iowait_pct": 2.0}})
    _append_json_line_durable(sample_path, {"epoch": 2, "cpu": {"iowait_pct": 3.0}})

    rows = [json.loads(line) for line in sample_path.read_text().splitlines()]
    assert [row["epoch"] for row in rows] == [1, 2]


class TestResourceUsageDetector:
    def test_classify_pass(self):
        detector = ResourceUsageDetector()
        severity, summary = detector._classify([], [])
        assert severity == "pass"

    def test_classify_warning(self):
        detector = ResourceUsageDetector()
        severity, summary = detector._classify([], ["high cpu"])
        assert severity == "warning"

    def test_classify_fail(self):
        detector = ResourceUsageDetector()
        severity, summary = detector._classify(["disk full"], [])
        assert severity == "fail"

    def test_read_latest_sample_valid(self, tmp_path):
        import time as _time

        sample_file = tmp_path / "samples.jsonl"
        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(_time.time()),
            "cpu": {"cpu_busy_pct": 45.0},
            "memory": {"mem_available_mb": 8192.0},
            "loadavg": {"15m": 2.0},
        }
        sample_file.write_text(json.dumps(sample), encoding="utf-8")

        with patch(
            "src.engine.error_detectors.resource_usage.SAMPLER_JSONL", sample_file
        ):
            result = ResourceUsageDetector._read_latest_sample()
            assert result is not None
            assert result["cpu"]["cpu_busy_pct"] == 45.0

    def test_read_latest_sample_no_file(self):
        with patch(
            "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
            Path("/nonexistent/samples.jsonl"),
        ):
            result = ResourceUsageDetector._read_latest_sample()
            assert result is None

    def test_check_disk_free(self):
        free_mb = ResourceUsageDetector._check_disk_free()
        assert free_mb > 0

    def test_normal_resources_pass(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 20.0},
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "pass"

    def test_high_cpu_fails(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 95.0},
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "fail"

    def test_iowait_is_reported_separately_from_compute_cpu(self):
        import time

        sample = {
            "ts": "2026-07-31T14:52:10+09:00",
            "epoch": int(time.time()),
            "cpu": {
                "cpu_busy_pct": 97.96,
                "cpu_non_idle_pct": 97.96,
                "cpu_compute_busy_pct": 46.2,
                "iowait_pct": 51.76,
            },
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                result = ResourceUsageDetector().check()

        assert result.severity == "fail"
        assert "I/O wait 51.76%" in result.summary
        assert "CPU compute busy" not in result.summary
        assert result.details["cpu_non_idle_pct"] == 97.96
        assert result.details["cpu_compute_busy_pct"] == 46.2

    def test_legacy_cpu_sample_derives_compute_busy_from_iowait(self):
        import time

        sample = {
            "ts": "2026-07-31T14:52:10+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 97.96, "iowait_pct": 51.76},
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                result = ResourceUsageDetector().check()

        assert result.details["cpu_compute_busy_pct"] == pytest.approx(46.2)

    def test_cpu_above_old_threshold_warns_under_95_fail_threshold(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 91.0},
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "warning"
            assert "approaching 95.0%" in result.summary

    def test_low_memory_fails(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 20.0},
            "memory": {
                "mem_available_mb": 100.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "fail"

    def test_high_swap_with_healthy_memory_warns_not_fails(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 20.0},
            "memory": {
                "mem_available_mb": 8192.0,
                "swap_total_mb": 4096.0,
                "swap_free_mb": 8.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "warning"
            assert result.details["swap_pressure_state"] == "swap_high_memory_healthy"

    def test_high_swap_with_unhealthy_memory_fails(self):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()),
            "cpu": {"cpu_busy_pct": 20.0},
            "memory": {
                "mem_available_mb": 1500.0,
                "swap_total_mb": 4096.0,
                "swap_free_mb": 8.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                detector = ResourceUsageDetector()
                result = detector.check()
            assert result.severity == "fail"

    def test_non_trading_day_ignores_stale_sampler_but_keeps_resource_checks(
        self, monkeypatch
    ):
        import time

        sample = {
            "ts": "2026-05-09T18:00:00+09:00",
            "epoch": int(time.time()) - 999999,
            "cpu": {"cpu_busy_pct": 20.0},
            "memory": {
                "mem_available_mb": 4096.0,
                "swap_total_mb": 8192.0,
                "swap_free_mb": 7000.0,
            },
            "loadavg": {"15m": 1.5},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "samples.jsonl"
            sample_file.write_text(json.dumps(sample), encoding="utf-8")
            monkeypatch.setattr(
                "src.engine.error_detectors.resource_usage.is_krx_trading_day",
                lambda target: False,
            )
            with (
                patch(
                    "src.engine.error_detectors.resource_usage.SAMPLER_JSONL",
                    sample_file,
                ),
                patch.object(
                    ResourceUsageDetector, "_check_disk_free", return_value=8192.0
                ),
            ):
                result = ResourceUsageDetector().check()

        assert result.severity == "pass"
        assert result.details["sampler_status"] == "skip_non_trading_day"

    def test_log_rotate_cooldown_persists_across_detector_instances(self, tmp_path):
        project_root = tmp_path / "project"
        deploy_dir = project_root / "deploy"
        deploy_dir.mkdir(parents=True)
        rotate_script = deploy_dir / "run_logs_rotation_cleanup_cron.sh"
        rotate_script.write_text(
            "#!/usr/bin/env bash\necho rotated\n", encoding="utf-8"
        )
        cooldown_state = tmp_path / "tmp" / "rotate_state.txt"

        calls = []

        def fake_run(*args, **kwargs):
            calls.append((args, kwargs))

            class Result:
                stdout = "rotated\n"

            return Result()

        with (
            patch(
                "src.engine.error_detectors.resource_usage.PROJECT_ROOT", project_root
            ),
            patch.object(
                ResourceUsageDetector, "_ROTATE_COOLDOWN_STATE", cooldown_state
            ),
            patch(
                "src.engine.error_detectors.resource_usage.subprocess.run",
                side_effect=fake_run,
            ),
        ):
            first_details = {}
            ResourceUsageDetector(dry_run=False)._auto_rotate_logs(first_details)
            second_details = {}
            ResourceUsageDetector(dry_run=False)._auto_rotate_logs(second_details)

        assert len(calls) == 1
        assert first_details["log_rotate_trigger"] == "ok"
        assert second_details["log_rotate_trigger"] == "cooldown_active"
        assert cooldown_state.exists()

    def test_log_rotate_script_missing_does_not_write_cooldown(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        cooldown_state = tmp_path / "tmp" / "rotate_state.txt"

        with (
            patch(
                "src.engine.error_detectors.resource_usage.PROJECT_ROOT", project_root
            ),
            patch.object(
                ResourceUsageDetector, "_ROTATE_COOLDOWN_STATE", cooldown_state
            ),
        ):
            details = {}
            ResourceUsageDetector(dry_run=False)._auto_rotate_logs(details)

        assert details["log_rotate_trigger"] == "script_not_found"
        assert not cooldown_state.exists()

    def test_log_rotate_timeout_does_not_write_cooldown(self, tmp_path):
        import subprocess

        project_root = tmp_path / "project"
        deploy_dir = project_root / "deploy"
        deploy_dir.mkdir(parents=True)
        rotate_script = deploy_dir / "run_logs_rotation_cleanup_cron.sh"
        rotate_script.write_text(
            "#!/usr/bin/env bash\necho rotated\n", encoding="utf-8"
        )
        cooldown_state = tmp_path / "tmp" / "rotate_state.txt"

        with (
            patch(
                "src.engine.error_detectors.resource_usage.PROJECT_ROOT", project_root
            ),
            patch.object(
                ResourceUsageDetector, "_ROTATE_COOLDOWN_STATE", cooldown_state
            ),
            patch(
                "src.engine.error_detectors.resource_usage.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="rotate", timeout=30),
            ),
        ):
            details = {}
            ResourceUsageDetector(dry_run=False)._auto_rotate_logs(details)

        assert details["log_rotate_trigger"].startswith("error:")
        assert not cooldown_state.exists()
