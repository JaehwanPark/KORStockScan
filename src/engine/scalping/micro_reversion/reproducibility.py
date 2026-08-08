"""Sidecar reproducibility manifest for micro-reversion reports."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

REPRODUCIBILITY_SCHEMA = "scalp_micro_reversion_reproducibility_manifest_v1"
DEFAULT_TEST_SELECTION = (
    "src/tests/test_micro_reversion_contracts.py",
    "src/tests/test_micro_reversion_detector.py",
    "src/tests/test_micro_reversion_execution_journal.py",
    "src/tests/test_micro_reversion_multi_horizon.py",
    "src/tests/test_micro_reversion_observation_path.py",
    "src/tests/test_micro_reversion_outcome_labeler.py",
    "src/tests/test_micro_reversion_registry.py",
    "src/tests/test_micro_reversion_replay.py",
    "src/tests/test_micro_reversion_research_gate.py",
    "src/tests/test_micro_reversion_symbol_master.py",
    "src/tests/test_micro_reversion_tax.py",
)


def write_reproducibility_manifest(
    *,
    report: dict[str, Any],
    json_report_path: Path,
    markdown_report_path: Path,
    output_path: Path,
    repository_root: Path,
    source_paths: Iterable[Path] | None = None,
    test_selection: Iterable[str] = DEFAULT_TEST_SELECTION,
    test_result: str = "not_run_for_this_manifest",
) -> Path:
    repository_root = Path(repository_root).resolve()
    input_paths = tuple(
        _resolve_repository_path(repository_root, raw_path)
        for raw_path in report["source_quality"]["input_stats"]["input_paths"]
    )
    selected_sources = tuple(
        sorted(
            (
                Path(path)
                for path in (
                    source_paths
                    if source_paths is not None
                    else (repository_root / "src/engine/scalping/micro_reversion").glob(
                        "*.py"
                    )
                )
            ),
            key=lambda path: str(path),
        )
    )
    input_rows = _hash_rows(input_paths, repository_root=repository_root)
    source_rows = _hash_rows(selected_sources, repository_root=repository_root)
    tests = tuple(str(path) for path in test_selection)
    test_paths = tuple(
        _resolve_repository_path(repository_root, path) for path in tests
    )
    test_rows = _hash_rows(test_paths, repository_root=repository_root)
    policy_config = {
        "report_schema": report.get("schema"),
        "metric_contract": report.get("metric_contract"),
        "detector_config": report["source_quality"]["input_stats"].get(
            "detector_config"
        ),
        "dedupe_interval_ms": report["source_quality"]["input_stats"].get(
            "dedupe_interval_ms"
        ),
        "max_path_gap_ms": report["source_quality"]["input_stats"].get(
            "max_path_gap_ms"
        ),
        "selected_all_in_cost_bps": report["cost_model"].get(
            "selected_all_in_cost_bps"
        ),
    }
    payload = {
        "schema": REPRODUCIBILITY_SCHEMA,
        "report_id": report.get("report_id"),
        "report_schema_version": report.get("schema"),
        "generated_at": datetime.now().astimezone().isoformat(),
        "implementation_commit": _git_output(repository_root, "rev-parse", "HEAD"),
        "working_tree_dirty": bool(
            _git_output(repository_root, "status", "--porcelain")
        ),
        "input_files": input_rows,
        "input_manifest_hash": _canonical_hash(input_rows),
        "source_files": source_rows,
        "source_manifest_hash": _canonical_hash(source_rows),
        "policy_config": policy_config,
        "policy_config_hash": _canonical_hash(policy_config),
        "reports": {
            "json": {
                "path": _relative_or_absolute(json_report_path, repository_root),
                "sha256": sha256_file(json_report_path),
            },
            "markdown": {
                "path": _relative_or_absolute(markdown_report_path, repository_root),
                "sha256": sha256_file(markdown_report_path),
            },
        },
        "test_selection_manifest": {
            "paths": list(tests),
            "files": test_rows,
            "sha256": _canonical_hash(test_rows),
            "result": test_result,
        },
        "runtime_effect": False,
        "automation_consumption_allowed": False,
        "decision_authority": "audit_reproducibility_only",
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_rows(paths: Iterable[Path], *, repository_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        resolved = Path(path).resolve()
        rows.append(
            {
                "path": _relative_or_absolute(resolved, repository_root),
                "exists": resolved.is_file(),
                "size_bytes": resolved.stat().st_size if resolved.is_file() else None,
                "sha256": sha256_file(resolved) if resolved.is_file() else None,
            }
        )
    return rows


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _git_output(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def _resolve_repository_path(repository_root: Path, value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else repository_root / path


def _relative_or_absolute(path: Path, repository_root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(repository_root))
    except ValueError:
        return str(resolved)
