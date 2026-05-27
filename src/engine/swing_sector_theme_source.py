"""Sector/theme enrichment for swing strategy discovery sim.

This helper is source-only. Missing sector/theme data must not exclude a
candidate; it is recorded as source quality metadata for later analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from src.utils.constants import DATA_DIR


CACHE_DIR = Path(DATA_DIR) / "runtime" / "swing_strategy_discovery"
REFERENCE_DIR = Path(__file__).resolve().parents[2] / "docs" / "reference"
DECISION_AUTHORITY = "swing_sim_exploration_only"


def _norm_code(value: Any) -> str:
    return str(value or "").replace(".0", "").strip().zfill(6)


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [part.strip() for part in stripped.replace("|", ",").split(",") if part.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _kiwoom_payload_ok(payload: Any) -> bool:
    if isinstance(payload, list):
        return all(_kiwoom_payload_ok(item) for item in payload if isinstance(item, dict))
    if not isinstance(payload, dict):
        return True
    code = payload.get("return_code")
    if code is None:
        return True
    return str(code).strip() == "0"


def _kiwoom_error_message(payload: Any) -> str:
    if isinstance(payload, list):
        messages = [_kiwoom_error_message(item) for item in payload if isinstance(item, dict)]
        return "; ".join(message for message in messages if message)
    if isinstance(payload, dict):
        return str(payload.get("return_msg") or payload.get("message") or "")
    return ""


def cache_path(target_date: str | date) -> Path:
    return CACHE_DIR / f"sector_theme_map_{_date_text(target_date)}.json"


def normalize_theme_map(
    rows_by_code: dict[str, dict[str, Any]] | None,
    *,
    source: str,
    source_quality: str,
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for raw_code, row in (rows_by_code or {}).items():
        code = _norm_code(raw_code)
        if not code.strip("0"):
            continue
        row = row if isinstance(row, dict) else {}
        normalized[code] = {
            "sector": str(row.get("sector") or ""),
            "industry": str(row.get("industry") or ""),
            "sector_code": str(row.get("sector_code") or ""),
            "market_type": str(row.get("market_type") or ""),
            "sector_source": str(row.get("sector_source") or ""),
            "sector_source_quality": str(row.get("sector_source_quality") or "missing"),
            "theme_tags": _as_list(row.get("theme_tags")),
            "theme_source": str(row.get("theme_source") or source),
            "theme_source_quality": str(row.get("theme_source_quality") or source_quality),
        }
    return normalized


def _extract_theme_groups(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("thema_grp", "theme_grp", "theme_group", "theme_list", "output", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _manual_sector_reference_path(target_date: str | date, explicit_path: str | Path | None = None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path)
        return path if path.exists() else None
    env_path = os.getenv("KORSTOCKSCAN_SWING_SECTOR_MANUAL_FILE", "").strip()
    if env_path:
        path = Path(env_path)
        return path if path.exists() else None
    date_key = _date_text(target_date).replace("-", "")
    candidates = [
        REFERENCE_DIR / f"swing_sector_manual_{date_key}.csv",
        REFERENCE_DIR / f"swing_sector_manual_{date_key}.xlsx",
        REFERENCE_DIR / f"data_5126_{date_key}.xlsx",
        REFERENCE_DIR / f"data_5039_{date_key}.csv",
        REFERENCE_DIR / "swing_sector_manual.csv",
        REFERENCE_DIR / "swing_sector_manual.xlsx",
    ]
    for path in candidates:
        if path.exists():
            return path
    latest = sorted(
        list(REFERENCE_DIR.glob("data_5126_*.xlsx"))
        + list(REFERENCE_DIR.glob("data_5039_*.csv"))
        + list(REFERENCE_DIR.glob("swing_sector_manual_*.csv"))
        + list(REFERENCE_DIR.glob("swing_sector_manual_*.xlsx"))
    )
    return latest[-1] if latest else None


def _row_get(row: dict[str, Any], *names: str) -> Any:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        if name in row:
            return row.get(name)
        value = lowered.get(name.strip().lower())
        if value is not None:
            return value
    return None


def _manual_sector_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    if suffix in {".xlsx", ".xlsm"}:
        import pandas as pd

        frame = pd.read_excel(path, dtype=str)
        return frame.fillna("").to_dict("records")
    return []


def fetch_manual_sector_map(
    codes: Iterable[str],
    *,
    target_date: str | date,
    reference_path: str | Path | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    requested = sorted({_norm_code(code) for code in codes if _norm_code(code).strip("0")})
    path = _manual_sector_reference_path(target_date, reference_path)
    diagnostics: dict[str, Any] = {
        "source": "manual_sector_reference",
        "requested_code_count": len(requested),
        "status": "missing_reference_file",
        "path": str(path) if path else "",
    }
    if not requested or path is None:
        return {}, diagnostics
    requested_set = set(requested)
    rows: dict[str, dict[str, Any]] = {}
    try:
        raw_rows = _manual_sector_rows(path)
        for raw in raw_rows:
            code = _norm_code(
                _row_get(raw, "Issue code", "issue_code", "종목코드", "code", "stock_code")
            )
            if code not in requested_set:
                continue
            sector_code = str(_row_get(raw, "Sector code", "sector_code", "업종코드") or "").replace(".0", "").strip()
            industry = str(_row_get(raw, "Industry", "industry", "업종", "업종명") or "").strip()
            market_type = str(_row_get(raw, "Market type", "market_type", "시장구분") or "").strip()
            rows[code] = {
                "sector": industry,
                "industry": industry,
                "sector_code": sector_code,
                "market_type": market_type,
                "theme_tags": [],
                "theme_source": "missing",
                "theme_source_quality": "missing",
                "sector_source": "manual_sector_reference",
                "sector_source_quality": "ok" if industry or sector_code else "missing",
            }
        diagnostics.update(
            {
                "status": "ok",
                "path": str(path),
                "raw_row_count": len(raw_rows),
                "mapped_code_count": len(rows),
            }
        )
        return rows, diagnostics
    except Exception as exc:
        diagnostics.update({"status": "manual_sector_fetch_failed", "error": str(exc)})
        return {}, diagnostics


def fetch_kiwoom_sector_theme_map(
    codes: Iterable[str],
    *,
    token: str | None = None,
    theme_group_fetcher: Callable[[str], Any] | None = None,
    stock_theme_fetcher: Callable[[str, str], Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Fetch Kiwoom theme membership when a token/fetcher is available.

    The adapter is intentionally tolerant because Kiwoom response field names
    differ across wrapper versions.
    """
    requested = sorted({_norm_code(code) for code in codes if _norm_code(code).strip("0")})
    diagnostics: dict[str, Any] = {
        "source": "kiwoom_api",
        "requested_code_count": len(requested),
        "status": "skipped_no_token_or_fetcher",
    }
    if not requested:
        return {}, diagnostics
    token = token or os.getenv("KIWOOM_ACCESS_TOKEN") or os.getenv("KIWOOM_REST_ACCESS_TOKEN")
    token_fetcher: Callable[[], str] | None = None
    explicit_group_fetcher = theme_group_fetcher is not None
    if theme_group_fetcher is None or (stock_theme_fetcher is None and not explicit_group_fetcher):
        try:
            from src.utils import kiwoom_utils

            token_fetcher = getattr(kiwoom_utils, "get_kiwoom_token", None)
            if not explicit_group_fetcher:
                stock_theme_fetcher = stock_theme_fetcher or getattr(kiwoom_utils, "get_stock_theme_groups_ka90001", None)
            theme_group_fetcher = theme_group_fetcher or kiwoom_utils.get_theme_group_list_ka90001
        except Exception as exc:
            diagnostics.update({"status": "kiwoom_helper_unavailable", "error": str(exc)})
            return {}, diagnostics
    if not token and token_fetcher is not None:
        try:
            token = token_fetcher()
        except Exception as exc:
            diagnostics.update({"status": "kiwoom_token_unavailable", "error": str(exc)})
            return {}, diagnostics
    if not token:
        return {}, diagnostics
    try:
        if stock_theme_fetcher is not None:
            rows: dict[str, dict[str, Any]] = {}
            errors: list[str] = []
            interval_sec = float(os.getenv("KORSTOCKSCAN_SWING_THEME_KIWOOM_CALL_INTERVAL_SEC", "1.0") or "0")
            for idx, code in enumerate(requested):
                if idx and interval_sec > 0:
                    time.sleep(interval_sec)
                payload = stock_theme_fetcher(token, code)
                if not _kiwoom_payload_ok(payload):
                    errors.append(f"{code}:{_kiwoom_error_message(payload)}")
                    continue
                for group in _extract_theme_groups(payload):
                    theme_name = str(
                        group.get("thema_nm")
                        or group.get("thema_grp_nm")
                        or group.get("theme_grp_nm")
                        or group.get("theme_name")
                        or group.get("name")
                        or group.get("테마명")
                        or ""
                    ).strip()
                    if not theme_name:
                        continue
                    row = rows.setdefault(
                        code,
                        {
                            "sector": "",
                            "industry": "",
                            "theme_tags": [],
                            "theme_source": "kiwoom_api",
                            "theme_source_quality": "ok",
                        },
                    )
                    if theme_name not in row["theme_tags"]:
                        row["theme_tags"].append(theme_name)
            diagnostics.update(
                {
                    "status": "ok",
                    "lookup_mode": "stock_theme_groups_ka90001",
                    "mapped_code_count": len(rows),
                    "errors": errors[:10],
                }
            )
            return rows, diagnostics

        # Fallback is deliberately catalog-only. Candidate theme membership is
        # only mapped through ka90001 qry_tp=2 to avoid composition fan-out calls.
        groups_payload = theme_group_fetcher(token)
        if not _kiwoom_payload_ok(groups_payload):
            diagnostics.update({"status": "kiwoom_fetch_failed", "error": _kiwoom_error_message(groups_payload)})
            return {}, diagnostics
        groups = _extract_theme_groups(groups_payload)
        diagnostics.update(
            {
                "status": "ok",
                "lookup_mode": "theme_group_catalog_only_ka90001",
                "theme_group_count": len(groups),
                "mapped_code_count": 0,
            }
        )
        return {}, diagnostics
    except Exception as exc:
        diagnostics.update({"status": "kiwoom_fetch_failed", "error": str(exc)})
        return {}, diagnostics


def fetch_external_sector_theme_map(
    codes: Iterable[str],
    *,
    fetcher: Callable[[str], dict[str, Any] | None] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Best-effort external fallback.

    The default path is disabled unless explicitly enabled because this is an
    enrichment source, not an execution prerequisite.
    """
    requested = sorted({_norm_code(code) for code in codes if _norm_code(code).strip("0")})
    diagnostics: dict[str, Any] = {
        "source": "external_crawl_fallback",
        "requested_code_count": len(requested),
        "status": "disabled",
    }
    if not requested:
        return {}, diagnostics
    if fetcher is None and str(os.getenv("KORSTOCKSCAN_SWING_THEME_EXTERNAL_CRAWL_ENABLED", "false")).lower() not in {
        "1",
        "true",
        "yes",
    }:
        return {}, diagnostics
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for code in requested:
        try:
            row = fetcher(code) if fetcher else None
        except Exception as exc:
            errors.append(f"{code}:{exc}")
            continue
        if not row:
            continue
        rows[code] = {
            "sector": str(row.get("sector") or ""),
            "industry": str(row.get("industry") or ""),
            "theme_tags": _as_list(row.get("theme_tags")),
            "theme_source": "external_crawl_fallback",
            "theme_source_quality": "fallback",
        }
    diagnostics.update({"status": "ok" if rows else "empty", "mapped_code_count": len(rows), "errors": errors[:10]})
    return rows, diagnostics


def build_sector_theme_map(
    codes: Iterable[str],
    *,
    target_date: str | date,
    token: str | None = None,
    allow_external: bool = True,
    manual_sector_path: str | Path | None = None,
    theme_group_fetcher: Callable[[str], Any] | None = None,
    stock_theme_fetcher: Callable[[str, str], Any] | None = None,
    external_fetcher: Callable[[str], dict[str, Any] | None] | None = None,
    write_cache: bool = True,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    requested = sorted({_norm_code(code) for code in codes if _norm_code(code).strip("0")})
    manual_rows, manual_diag = fetch_manual_sector_map(requested, target_date=date_key, reference_path=manual_sector_path)
    kiwoom_rows, kiwoom_diag = fetch_kiwoom_sector_theme_map(
        requested,
        token=token,
        theme_group_fetcher=theme_group_fetcher,
        stock_theme_fetcher=stock_theme_fetcher,
    )
    missing = [code for code in requested if code not in kiwoom_rows]
    external_rows: dict[str, dict[str, Any]] = {}
    external_diag: dict[str, Any] = {"status": "skipped"}
    if allow_external and missing:
        external_rows, external_diag = fetch_external_sector_theme_map(missing, fetcher=external_fetcher)
    merged = normalize_theme_map(manual_rows, source="manual_sector_reference", source_quality="ok")
    for source_rows, source_name, source_quality in (
        (kiwoom_rows, "kiwoom_api", "ok"),
        (external_rows, "external_crawl_fallback", "fallback"),
    ):
        for code, row in normalize_theme_map(source_rows, source=source_name, source_quality=source_quality).items():
            base = merged.setdefault(
                code,
                {
                    "sector": "",
                    "industry": "",
                    "sector_code": "",
                    "market_type": "",
                    "sector_source": "missing",
                    "sector_source_quality": "missing",
                    "theme_tags": [],
                    "theme_source": "missing",
                    "theme_source_quality": "missing",
                },
            )
            for key in ("sector", "industry", "sector_code", "market_type", "sector_source", "sector_source_quality"):
                if row.get(key) and not base.get(key):
                    base[key] = row[key]
            if row.get("theme_tags"):
                base["theme_tags"] = sorted(set(_as_list(base.get("theme_tags")) + _as_list(row.get("theme_tags"))))
            if row.get("theme_source_quality") != "missing":
                base["theme_source"] = row.get("theme_source") or base.get("theme_source") or source_name
                base["theme_source_quality"] = row.get("theme_source_quality") or source_quality
    missing_after_merge = [
        code
        for code in requested
        if code not in merged
        or (
            merged.get(code, {}).get("sector_source_quality") == "missing"
            and merged.get(code, {}).get("theme_source_quality") == "missing"
        )
    ]
    for code in missing_after_merge:
        merged[code] = {
            "sector": "",
            "industry": "",
            "sector_code": "",
            "market_type": "",
            "theme_tags": [],
            "sector_source": "missing",
            "sector_source_quality": "missing",
            "theme_source": "missing",
            "theme_source_quality": "missing",
        }
    sector_missing_count = sum(1 for row in merged.values() if row.get("sector_source_quality") == "missing")
    theme_missing_count = sum(1 for row in merged.values() if row.get("theme_source_quality") == "missing")
    mapped_count = sum(
        1
        for row in merged.values()
        if row.get("sector_source_quality") != "missing" or row.get("theme_source_quality") != "missing"
    )
    missing_count = sum(
        1
        for row in merged.values()
        if row.get("sector_source_quality") == "missing" and row.get("theme_source_quality") == "missing"
    )
    coverage = round(mapped_count / len(requested), 6) if requested else 0.0
    sector_coverage = round((len(merged) - sector_missing_count) / len(requested), 6) if requested else 0.0
    theme_coverage = round((len(merged) - theme_missing_count) / len(requested), 6) if requested else 0.0
    warnings = ["manual_sector_missing", "sector_theme_missing"] if requested and coverage <= 0 else []
    payload = {
        "schema_version": 1,
        "date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "report_type": "swing_sector_theme_source",
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "requested_code_count": len(requested),
        "mapped_code_count": mapped_count,
        "missing_count": missing_count,
        "coverage": coverage,
        "sector_mapped_count": len(merged) - sector_missing_count,
        "sector_missing_count": sector_missing_count,
        "sector_coverage": sector_coverage,
        "theme_mapped_count": len(merged) - theme_missing_count,
        "theme_missing_count": theme_missing_count,
        "theme_coverage": theme_coverage,
        "rows_by_code": merged,
        "diagnostics": {
            "manual_sector": manual_diag,
            "kiwoom": kiwoom_diag,
            "external": external_diag,
        },
        "warnings": warnings,
    }
    if write_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path(date_key).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_sector_theme_cache(target_date: str | date) -> dict[str, Any]:
    path = cache_path(target_date)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--codes", nargs="*", default=[])
    parser.add_argument("--manual-sector-file", default=None)
    parser.add_argument("--no-external", action="store_true")
    args = parser.parse_args(argv)
    payload = build_sector_theme_map(
        args.codes,
        target_date=args.date,
        manual_sector_path=args.manual_sector_file,
        allow_external=not args.no_external,
    )
    print(f"[DONE] swing_sector_theme_source mapped={payload['mapped_code_count']} path={cache_path(args.date)}")


if __name__ == "__main__":
    main()
