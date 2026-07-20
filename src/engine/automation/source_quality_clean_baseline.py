from __future__ import annotations

import json
import os
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

REPORT_TYPE = "source_quality_clean_baseline"
POLICY_PATH = DATA_DIR / "source_quality" / "clean_baseline_policy.json"
REPORT_QUARANTINE_DIR = DATA_DIR / "source_quality" / "report_quarantine"
ANALYTICS_QUARANTINE_DIR = DATA_DIR / "source_quality" / "analytics_quarantine"
DEFAULT_START_DATE = "2026-06-04"
DEFAULT_START_TS_KST = "2026-06-04T14:29:09+09:00"
DEFAULT_REASON = (
    "operator_requested_clean_tuning_restart_after_sim_probe_provenance_patch"
)
DATE_TOKEN_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
FORBIDDEN_USES = [
    "runtime_threshold_apply",
    "order_submit",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
    "manual_threshold_promotion_from_pre_baseline_data",
]
OPERATIONAL_STATUS_REPORT_DIRS = {
    "threshold_cycle_preopen_status",
    "threshold_cycle_postclose_status",
}


def _load_policy_file() -> dict[str, Any]:
    try:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def clean_baseline_policy() -> dict[str, Any]:
    payload = _load_policy_file()
    start_date = str(
        os.environ.get("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE")
        or payload.get("clean_tuning_baseline_date")
        or DEFAULT_START_DATE
    ).strip()
    start_ts = str(
        os.environ.get("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_TS_KST")
        or payload.get("clean_tuning_baseline_ts_kst")
        or DEFAULT_START_TS_KST
    ).strip()
    return {
        "report_type": REPORT_TYPE,
        "enabled": str(
            os.environ.get("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_ENABLED")
            or payload.get("enabled", True)
        )
        .strip()
        .lower()
        not in {"0", "false", "no", "off"},
        "clean_tuning_baseline_date": start_date,
        "clean_tuning_baseline_ts_kst": start_ts,
        "pre_baseline_decision": "decision_disqualified_archive_only",
        "same_day_pre_baseline_decision": "raw_quarantined_archive_only",
        "raw_data_policy": "archive_then_reset_current_day_raw; preserve archives for audit only",
        "derived_report_policy": "regenerate_from_clean_baseline_only",
        "operator_action_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "reason": payload.get("reason") or DEFAULT_REASON,
        "forbidden_uses": list(FORBIDDEN_USES),
    }


def is_date_allowed(source_date: str, policy: dict[str, Any] | None = None) -> bool:
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return True
    try:
        source = date.fromisoformat(str(source_date).strip())
        baseline = date.fromisoformat(
            str(policy.get("clean_tuning_baseline_date") or DEFAULT_START_DATE)
        )
    except ValueError:
        return False
    return source >= baseline


def filter_allowed_dates(
    source_dates: list[str], policy: dict[str, Any] | None = None
) -> tuple[list[str], list[str]]:
    policy = policy or clean_baseline_policy()
    allowed = [item for item in source_dates if is_date_allowed(item, policy)]
    excluded = [item for item in source_dates if item not in allowed]
    return allowed, excluded


def policy_warning_for_date(
    target_date: str, policy: dict[str, Any] | None = None
) -> str | None:
    policy = policy or clean_baseline_policy()
    if is_date_allowed(target_date, policy):
        return None
    return f"clean_tuning_baseline_excludes_date:{target_date}"


def report_date_tokens(path: str | Path) -> list[str]:
    return list(dict.fromkeys(DATE_TOKEN_RE.findall(str(path))))


def report_is_decision_allowed(
    path: str | Path, policy: dict[str, Any] | None = None
) -> bool:
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return True
    if is_operational_status_report(path):
        return True
    tokens = report_date_tokens(path)
    return bool(tokens) and all(is_date_allowed(token, policy) for token in tokens)


def is_operational_status_report(path: str | Path) -> bool:
    parts = set(Path(path).parts)
    return bool(parts & OPERATIONAL_STATUS_REPORT_DIRS)


def _coerce_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _comparable_datetimes(left: datetime, right: datetime) -> tuple[datetime, datetime]:
    if left.tzinfo is None and right.tzinfo is not None:
        right = right.replace(tzinfo=None)
    elif left.tzinfo is not None and right.tzinfo is None:
        left = left.replace(tzinfo=None)
    return left, right


def file_modified_before_clean_baseline(
    path: str | Path, policy: dict[str, Any] | None = None
) -> bool:
    path = Path(path)
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return False
    baseline_ts = _coerce_datetime(
        str(policy.get("clean_tuning_baseline_ts_kst") or DEFAULT_START_TS_KST)
    )
    if baseline_ts is None:
        return False
    try:
        modified_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    except OSError:
        return False
    modified_at, baseline_ts = _comparable_datetimes(modified_at, baseline_ts)
    return modified_at < baseline_ts


def report_generated_before_clean_baseline(
    path: str | Path, policy: dict[str, Any] | None = None
) -> bool:
    path = Path(path)
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return False
    if is_operational_status_report(path):
        return False
    baseline_date = str(policy.get("clean_tuning_baseline_date") or DEFAULT_START_DATE)
    if baseline_date not in report_date_tokens(path):
        return False
    baseline_ts = _coerce_datetime(
        str(policy.get("clean_tuning_baseline_ts_kst") or DEFAULT_START_TS_KST)
    )
    if baseline_ts is None:
        return False
    generated_at: datetime | None = None
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            generated_at = _coerce_datetime(str(payload.get("generated_at") or ""))
    if generated_at is None:
        try:
            generated_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        except OSError:
            return False
    generated_at, baseline_ts = _comparable_datetimes(generated_at, baseline_ts)
    return generated_at < baseline_ts


def analytics_quarantine_reason(
    path: str | Path, policy: dict[str, Any] | None = None
) -> str | None:
    path = Path(path)
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return None
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        tokens = report_date_tokens(path)
        if any(not is_date_allowed(token, policy) for token in tokens):
            return "pre_clean_baseline_parquet_archive_only"
        if file_modified_before_clean_baseline(path, policy):
            return "pre_clean_baseline_parquet_mtime_archive_only"
    if suffix == ".duckdb" and file_modified_before_clean_baseline(path, policy):
        return "pre_clean_baseline_duckdb_archive_only"
    return None


def report_quarantine_reason(
    path: str | Path,
    policy: dict[str, Any] | None = None,
    *,
    include_baseline_date: bool = False,
    include_undated: bool = False,
) -> str | None:
    policy = policy or clean_baseline_policy()
    if not policy.get("enabled", True):
        return None
    if is_operational_status_report(path):
        return None
    tokens = report_date_tokens(path)
    if not tokens:
        return (
            "undated_report_not_allowed_for_clean_tuning" if include_undated else None
        )
    try:
        baseline = date.fromisoformat(
            str(policy.get("clean_tuning_baseline_date") or DEFAULT_START_DATE)
        )
    except ValueError:
        return "invalid_clean_tuning_baseline_policy"
    parsed = []
    for token in tokens:
        try:
            parsed.append(date.fromisoformat(token))
        except ValueError:
            return "invalid_report_date_token"
    if any(item < baseline for item in parsed):
        return "pre_clean_baseline_report_archive_only"
    if include_baseline_date and any(item == baseline for item in parsed):
        return "same_day_existing_report_regenerate_from_clean_raw"
    if report_generated_before_clean_baseline(path, policy):
        return "same_day_pre_clean_baseline_report_archive_only"
    return None


def quarantine_report_tree(
    report_dir: Path,
    *,
    quarantine_dir: Path = REPORT_QUARANTINE_DIR,
    policy: dict[str, Any] | None = None,
    include_baseline_date: bool = True,
    include_undated: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    policy = policy or clean_baseline_policy()
    run_id = (
        datetime.now().astimezone().strftime("%Y-%m-%d_clean_report_quarantine_%H%M%S")
    )
    destination_root = quarantine_dir / run_id
    manifest_rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.rglob("*")):
        if not path.is_file():
            continue
        reason = report_quarantine_reason(
            path,
            policy,
            include_baseline_date=include_baseline_date,
            include_undated=include_undated,
        )
        if not reason:
            continue
        rel = path.relative_to(report_dir)
        manifest_rows.append(
            {
                "source_path": str(path),
                "quarantine_path": str(destination_root / "data" / "report" / rel),
                "relative_path": str(rel),
                "date_tokens": report_date_tokens(path),
                "reason": reason,
                "decision_state": "archive_only_not_allowed_for_clean_tuning",
            }
        )
    if not dry_run and manifest_rows:
        for row in manifest_rows:
            source = Path(row["source_path"])
            dest = Path(row["quarantine_path"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
        destination_root.mkdir(parents=True, exist_ok=True)
        manifest_path = destination_root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest_rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tsv_path = destination_root / "manifest.tsv"
        tsv_path.write_text(
            "source_path\tquarantine_path\treason\tdate_tokens\n"
            + "\n".join(
                f"{row['source_path']}\t{row['quarantine_path']}\t{row['reason']}\t{','.join(row['date_tokens'])}"
                for row in manifest_rows
            )
            + "\n",
            encoding="utf-8",
        )
    return {
        "report_type": "source_quality_report_quarantine",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "dry_run": dry_run,
        "report_dir": str(report_dir),
        "quarantine_root": str(destination_root),
        "quarantined_count": len(manifest_rows),
        "include_baseline_date": include_baseline_date,
        "include_undated": include_undated,
        "policy": policy,
        "manifest_rows": manifest_rows,
    }


def write_policy(
    *,
    clean_tuning_baseline_date: str = DEFAULT_START_DATE,
    clean_tuning_baseline_ts_kst: str = DEFAULT_START_TS_KST,
    reason: str = DEFAULT_REASON,
) -> dict[str, Any]:
    payload = {
        "enabled": True,
        "clean_tuning_baseline_date": clean_tuning_baseline_date,
        "clean_tuning_baseline_ts_kst": clean_tuning_baseline_ts_kst,
        "reason": reason,
        "written_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": list(FORBIDDEN_USES),
    }
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return clean_baseline_policy()
