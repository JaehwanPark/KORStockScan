"""Read-only Kiwoom minute-bar backfill for pure-market reversal research.

This producer intentionally uses only the official ``ka10080`` and ``ka20005``
request fields and an already-valid shared token.  It never issues, refreshes,
invalidates, or replaces a token and never calls account or order APIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

import requests

from src.utils import kiwoom_utils

KST = ZoneInfo("Asia/Seoul")
SAMSUNG_CODE = "005930"
DEFAULT_OUTPUT_DIR = Path("data/market_data/pure_market_reversal")
CLEAN_TUNING_BASELINE_DATE = date(2026, 6, 5)
OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-11T10:10:15+09:00",
    "inspected_paths": [
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core/client.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contract": "POST /api/dostk/chart; api-id=ka10080|ka20005",
}
METRIC_CONTRACT = {
    "metric_role": "source_quality_and_market_data_backfill",
    "decision_authority": "offline_pure_market_data_backfill_only",
    "window_policy": "explicit_date_range_by_venue_with_continuation",
    "sample_floor": "requested_start_date_reached_per_requested_venue",
    "primary_decision_metric": "source_coverage_pct",
    "source_quality_gate": (
        "official_ka10080_or_ka20005_success_unique_timestamp_valid_ohlcv_"
        "and_target_date_reached"
    ),
    "forbidden_uses": [
        "real_order_submission",
        "account_or_quantity_call",
        "token_issue_refresh_invalidation_or_replacement",
        "trading_runtime_threshold_or_policy_apply",
        "provider_or_bot_change",
        "historical_bbo_or_signed_tape_imputation",
    ],
}


class BackfillError(RuntimeError):
    """Raised when a read-only backfill cannot preserve its source contract."""


@dataclass(frozen=True)
class MarketBar:
    schema: str
    symbol: str
    request_code: str
    venue: str
    session: str
    source_api_id: str
    source_timestamp: str
    source_time_basis: str
    source_timezone: str
    open: int
    high: int
    low: int
    close: int
    volume: int
    adjusted_price: bool


@dataclass(frozen=True)
class IndexBar:
    schema: str
    symbol: str
    request_code: str
    venue: str
    session: str
    source_api_id: str
    source_timestamp: str
    source_time_basis: str
    source_timezone: str
    open: int
    high: int
    low: int
    close: int
    volume: int
    price_scale: str


def _positive_price(value: object) -> int:
    try:
        parsed = abs(int(float(str(value or "").replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0
    return parsed


def _nonnegative_int(value: object) -> int:
    try:
        parsed = abs(int(float(str(value or "0").replace(",", "").strip())))
    except (TypeError, ValueError):
        return -1
    return parsed


def _session_for(*, venue: str, timestamp: str) -> str | None:
    hhmm = timestamp[8:12]
    if venue == "KRX":
        return "KRX_REGULAR" if "0900" <= hhmm < "1530" else None
    if venue != "NXT":
        return None
    if "0800" <= hhmm < "0850":
        return "NXT_PREMARKET"
    if "0900" <= hhmm < "1530":
        return "NXT_REGULAR"
    if "1540" <= hhmm < "2000":
        return "NXT_AFTERMARKET"
    return None


def _normalize_row(
    row: object, *, venue: str, request_code: str
) -> tuple[MarketBar | None, str | None]:
    if not isinstance(row, dict):
        return None, "invalid_shape"
    timestamp = str(row.get("cntr_tm") or "").strip()[:14]
    if len(timestamp) != 14 or not timestamp.isdigit():
        return None, "invalid_timestamp"
    prices = {
        "open": _positive_price(row.get("open_pric")),
        "high": _positive_price(row.get("high_pric")),
        "low": _positive_price(row.get("low_pric")),
        "close": _positive_price(row.get("cur_prc")),
    }
    volume = _nonnegative_int(row.get("trde_qty"))
    if (
        min(prices.values()) <= 0
        or prices["high"] < max(prices["open"], prices["close"], prices["low"])
        or prices["low"] > min(prices["open"], prices["close"], prices["high"])
        or volume < 0
    ):
        return None, "invalid_ohlcv"
    session = _session_for(venue=venue, timestamp=timestamp)
    if session is None:
        return None, "out_of_session"
    return (
        MarketBar(
            schema="pure_market_minute_bar_v1",
            symbol=SAMSUNG_CODE,
            request_code=request_code,
            venue=venue,
            session=session,
            source_api_id="ka10080",
            source_timestamp=timestamp,
            source_time_basis="ka10080_cntr_tm_bar_timestamp",
            source_timezone="Asia/Seoul",
            open=prices["open"],
            high=prices["high"],
            low=prices["low"],
            close=prices["close"],
            volume=volume,
            adjusted_price=True,
        ),
        None,
    )


def _normalize_index_row(row: object) -> tuple[IndexBar | None, str | None]:
    if not isinstance(row, dict):
        return None, "invalid_shape"
    timestamp = str(row.get("cntr_tm") or "").strip()[:14]
    if len(timestamp) != 14 or not timestamp.isdigit():
        return None, "invalid_timestamp"
    prices = {
        "open": _positive_price(row.get("open_pric")),
        "high": _positive_price(row.get("high_pric")),
        "low": _positive_price(row.get("low_pric")),
        "close": _positive_price(row.get("cur_prc")),
    }
    volume = _nonnegative_int(row.get("trde_qty"))
    if (
        min(prices.values()) <= 0
        or prices["high"] < max(prices["open"], prices["close"], prices["low"])
        or prices["low"] > min(prices["open"], prices["close"], prices["high"])
        or volume < 0
    ):
        return None, "invalid_ohlcv"
    session = _session_for(venue="KRX", timestamp=timestamp)
    if session is None:
        return None, "out_of_session"
    return (
        IndexBar(
            schema="pure_market_index_minute_bar_v1",
            symbol="KOSPI",
            request_code="001",
            venue="KRX",
            session=session,
            source_api_id="ka20005",
            source_timestamp=timestamp,
            source_time_basis="ka20005_cntr_tm_bar_timestamp",
            source_timezone="Asia/Seoul",
            open=prices["open"],
            high=prices["high"],
            low=prices["low"],
            close=prices["close"],
            volume=volume,
            price_scale="raw_index_x100",
        ),
        None,
    )


def _response_json(response: requests.Response, *, api_id: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise BackfillError(f"{api_id}_response_not_json") from exc
    if not isinstance(payload, dict):
        raise BackfillError(f"{api_id}_response_not_object")
    return payload


def fetch_ka10080_history(
    *,
    token: str,
    venue: str,
    start_date: date,
    end_date: date,
    max_pages: int = 120,
    page_delay_sec: float = 0.5,
    post: Callable[..., requests.Response] = requests.post,
) -> tuple[list[MarketBar], dict[str, Any]]:
    """Fetch oldest-needed 1m OHLCV without mutating shared auth state."""
    normalized_venue = venue.strip().upper()
    if normalized_venue not in {"KRX", "NXT"}:
        raise ValueError("venue must be KRX or NXT")
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    if not str(token or "").strip():
        raise BackfillError("cached_token_missing")
    request_code = SAMSUNG_CODE if normalized_venue == "KRX" else f"{SAMSUNG_CODE}_NX"
    url = kiwoom_utils.get_api_url("/api/dostk/chart")
    cont_yn = "N"
    next_key = ""
    unique: dict[str, MarketBar] = {}
    invalid_row_count = 0
    out_of_session_row_count = 0
    duplicate_row_count = 0
    oldest_seen: date | None = None
    page_count = 0
    target_reached = False
    continuation_exhausted = False

    for page_index in range(max(1, int(max_pages))):
        response = post(
            url,
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {str(token).replace('Bearer ', '').strip()}",
                "cont-yn": cont_yn,
                "next-key": next_key,
                "api-id": "ka10080",
            },
            json={
                "stk_cd": request_code,
                "tic_scope": "1",
                "upd_stkpc_tp": "1",
            },
            timeout=(5, 30),
        )
        page_count += 1
        if response.status_code != 200:
            raise BackfillError(f"ka10080_http_{response.status_code}")
        payload = _response_json(response, api_id="ka10080")
        try:
            return_code = int(payload.get("return_code", -1))
        except (TypeError, ValueError):
            return_code = -1
        if return_code != 0:
            # In particular, auth error 8005 remains fail-closed.  This module
            # must never refresh or invalidate the shared runtime token.
            raise BackfillError(f"ka10080_return_{return_code}")
        for raw_row in payload.get("stk_min_pole_chart_qry", []) or []:
            bar, rejection_reason = _normalize_row(
                raw_row,
                venue=normalized_venue,
                request_code=request_code,
            )
            if bar is None:
                if rejection_reason == "out_of_session":
                    out_of_session_row_count += 1
                else:
                    invalid_row_count += 1
                continue
            bar_date = datetime.strptime(bar.source_timestamp[:8], "%Y%m%d").date()
            oldest_seen = (
                bar_date if oldest_seen is None else min(oldest_seen, bar_date)
            )
            if bar.source_timestamp in unique:
                duplicate_row_count += 1
            unique[bar.source_timestamp] = bar
        # Bracket the requested start date with at least one older source row.
        # A page can end in the middle of start_date; stopping at equality would
        # silently persist only the newest fragment of that session.
        if oldest_seen is not None and oldest_seen < start_date:
            target_reached = True
            break
        cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
        next_key = str(response.headers.get("next-key", "") or "").strip()
        if cont_yn != "Y":
            continuation_exhausted = True
            break
        if not next_key:
            raise BackfillError("ka10080_continuation_key_missing")
        if page_index + 1 < max_pages and page_delay_sec > 0:
            time.sleep(page_delay_sec)

    bars = [
        bar
        for _, bar in sorted(unique.items())
        if start_date
        <= datetime.strptime(bar.source_timestamp[:8], "%Y%m%d").date()
        <= end_date
    ]
    dates = sorted({bar.source_timestamp[:8] for bar in bars})
    meta = {
        "venue": normalized_venue,
        "request_code": request_code,
        "api_base_url": url,
        "api_environment": (
            "production"
            if "api.kiwoom.com" in url
            else "mock" if "mockapi.kiwoom.com" in url else "configured_unknown"
        ),
        "page_count": page_count,
        "bar_count": len(bars),
        "trading_date_count": len(dates),
        "oldest_source_date": dates[0] if dates else None,
        "latest_source_date": dates[-1] if dates else None,
        "target_start_date_reached": target_reached,
        "start_date_fully_bracketed": target_reached,
        "continuation_exhausted": continuation_exhausted,
        "invalid_row_count": invalid_row_count,
        "out_of_session_row_count": out_of_session_row_count,
        "duplicate_row_count": duplicate_row_count,
        "source_quality_status": (
            "PASS" if target_reached and bars and invalid_row_count == 0 else "PARTIAL"
        ),
    }
    return bars, meta


def fetch_ka20005_history(
    *,
    token: str,
    start_date: date,
    end_date: date,
    max_pages: int = 120,
    page_delay_sec: float = 0.5,
    post: Callable[..., requests.Response] = requests.post,
) -> tuple[list[IndexBar], dict[str, Any]]:
    """Fetch fully bracketed KOSPI 1m context without auth mutation."""
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    if not str(token or "").strip():
        raise BackfillError("cached_token_missing")
    url = kiwoom_utils.get_api_url("/api/dostk/chart")
    cont_yn = "N"
    next_key = ""
    unique: dict[str, IndexBar] = {}
    invalid_row_count = 0
    out_of_session_row_count = 0
    duplicate_row_count = 0
    oldest_seen: date | None = None
    page_count = 0
    target_reached = False
    continuation_exhausted = False

    for page_index in range(max(1, int(max_pages))):
        response = post(
            url,
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {str(token).replace('Bearer ', '').strip()}",
                "cont-yn": cont_yn,
                "next-key": next_key,
                "api-id": "ka20005",
            },
            json={"inds_cd": "001", "tic_scope": "1"},
            timeout=(5, 30),
        )
        page_count += 1
        if response.status_code != 200:
            raise BackfillError(f"ka20005_http_{response.status_code}")
        payload = _response_json(response, api_id="ka20005")
        try:
            return_code = int(payload.get("return_code", -1))
        except (TypeError, ValueError):
            return_code = -1
        if return_code != 0:
            raise BackfillError(f"ka20005_return_{return_code}")
        for raw_row in payload.get("inds_min_pole_qry", []) or []:
            bar, rejection_reason = _normalize_index_row(raw_row)
            if bar is None:
                if rejection_reason == "out_of_session":
                    out_of_session_row_count += 1
                else:
                    invalid_row_count += 1
                continue
            bar_date = datetime.strptime(bar.source_timestamp[:8], "%Y%m%d").date()
            oldest_seen = (
                bar_date if oldest_seen is None else min(oldest_seen, bar_date)
            )
            if bar.source_timestamp in unique:
                duplicate_row_count += 1
            unique[bar.source_timestamp] = bar
        if oldest_seen is not None and oldest_seen < start_date:
            target_reached = True
            break
        cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
        next_key = str(response.headers.get("next-key", "") or "").strip()
        if cont_yn != "Y":
            continuation_exhausted = True
            break
        if not next_key:
            raise BackfillError("ka20005_continuation_key_missing")
        if page_index + 1 < max_pages and page_delay_sec > 0:
            time.sleep(page_delay_sec)

    bars = [
        bar
        for _, bar in sorted(unique.items())
        if start_date
        <= datetime.strptime(bar.source_timestamp[:8], "%Y%m%d").date()
        <= end_date
    ]
    dates = sorted({bar.source_timestamp[:8] for bar in bars})
    meta = {
        "venue": "KRX",
        "request_code": "001",
        "symbol": "KOSPI",
        "source_api_id": "ka20005",
        "api_base_url": url,
        "api_environment": (
            "production"
            if "api.kiwoom.com" in url
            else "mock" if "mockapi.kiwoom.com" in url else "configured_unknown"
        ),
        "page_count": page_count,
        "bar_count": len(bars),
        "trading_date_count": len(dates),
        "oldest_source_date": dates[0] if dates else None,
        "latest_source_date": dates[-1] if dates else None,
        "target_start_date_reached": target_reached,
        "start_date_fully_bracketed": target_reached,
        "continuation_exhausted": continuation_exhausted,
        "invalid_row_count": invalid_row_count,
        "out_of_session_row_count": out_of_session_row_count,
        "duplicate_row_count": duplicate_row_count,
        "source_quality_status": (
            "PASS" if target_reached and bars and invalid_row_count == 0 else "PARTIAL"
        ),
    }
    return bars, meta


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_backfill(
    bars: Iterable[MarketBar],
    *,
    start_date: date,
    end_date: date,
    venue_meta: list[dict[str, Any]],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    venue_label = "-".join(
        sorted({str(row.get("venue") or "unknown").lower() for row in venue_meta})
    )
    stem = (
        f"samsung_1m_{venue_label}_{start_date.isoformat()}_" f"{end_date.isoformat()}"
    )
    data_path = output_dir / f"{stem}.jsonl"
    manifest_path = output_dir / f"{stem}.manifest.json"
    ordered = sorted(bars, key=lambda bar: (bar.source_timestamp, bar.venue))
    data_content = "".join(
        json.dumps(asdict(bar), ensure_ascii=False, sort_keys=True) + "\n"
        for bar in ordered
    )
    _atomic_write(
        data_path,
        data_content,
    )
    manifest = {
        "schema": "pure_market_minute_backfill_manifest_v1",
        "symbol": SAMSUNG_CODE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bar_count": len(ordered),
        "data_sha256": hashlib.sha256(data_content.encode("utf-8")).hexdigest(),
        "source_quality_status": (
            "PASS"
            if ordered
            and venue_meta
            and all(row.get("source_quality_status") == "PASS" for row in venue_meta)
            else "PARTIAL"
        ),
        "venue_meta": venue_meta,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "token_mutation_forbidden": True,
    }
    _atomic_write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return data_path, manifest_path


def write_index_backfill(
    bars: Iterable[IndexBar],
    *,
    start_date: date,
    end_date: date,
    source_meta: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[Path, Path]:
    stem = f"kospi_1m_krx_{start_date.isoformat()}_{end_date.isoformat()}"
    data_path = output_dir / f"{stem}.jsonl"
    manifest_path = output_dir / f"{stem}.manifest.json"
    ordered = sorted(bars, key=lambda bar: bar.source_timestamp)
    data_content = "".join(
        json.dumps(asdict(bar), ensure_ascii=False, sort_keys=True) + "\n"
        for bar in ordered
    )
    _atomic_write(data_path, data_content)
    manifest = {
        "schema": "pure_market_index_backfill_manifest_v1",
        "symbol": "KOSPI",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bar_count": len(ordered),
        "data_sha256": hashlib.sha256(data_content.encode("utf-8")).hexdigest(),
        "source_quality_status": source_meta.get("source_quality_status"),
        "source_meta": source_meta,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "token_mutation_forbidden": True,
    }
    _atomic_write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return data_path, manifest_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--venues", default="KRX,NXT")
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--page-delay-sec", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-kospi", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    if start_date < CLEAN_TUNING_BASELINE_DATE:
        raise SystemExit(
            "start-date precedes clean tuning baseline 2026-06-05; "
            "pre-baseline data is audit-only"
        )
    if start_date > end_date:
        raise SystemExit("start-date must not be after end-date")
    if end_date >= datetime.now(KST).date():
        raise SystemExit("end-date must be a fully completed prior KST trading date")
    token = kiwoom_utils.get_cached_kiwoom_token()
    if not token:
        raise SystemExit("cached Kiwoom token unavailable; token issuance is forbidden")
    venues = list(
        dict.fromkeys(
            item.strip().upper() for item in args.venues.split(",") if item.strip()
        )
    )
    all_bars: list[MarketBar] = []
    venue_meta: list[dict[str, Any]] = []
    for venue in venues:
        bars, meta = fetch_ka10080_history(
            token=token,
            venue=venue,
            start_date=start_date,
            end_date=end_date,
            max_pages=args.max_pages,
            page_delay_sec=args.page_delay_sec,
        )
        all_bars.extend(bars)
        venue_meta.append(meta)
    paths = write_backfill(
        all_bars,
        start_date=start_date,
        end_date=end_date,
        venue_meta=venue_meta,
        output_dir=args.output_dir,
    )
    index_paths: tuple[Path, Path] | None = None
    index_meta: dict[str, Any] | None = None
    if not args.skip_kospi:
        index_bars, index_meta = fetch_ka20005_history(
            token=token,
            start_date=start_date,
            end_date=end_date,
            max_pages=args.max_pages,
            page_delay_sec=args.page_delay_sec,
        )
        index_paths = write_index_backfill(
            index_bars,
            start_date=start_date,
            end_date=end_date,
            source_meta=index_meta,
            output_dir=args.output_dir,
        )
    complete = (
        bool(all_bars)
        and all(row.get("source_quality_status") == "PASS" for row in venue_meta)
        and (
            args.skip_kospi
            or bool(index_meta)
            and index_meta.get("source_quality_status") == "PASS"
        )
    )
    print(
        json.dumps(
            {
                "status": "complete" if complete else "partial",
                "data_path": str(paths[0]),
                "manifest_path": str(paths[1]),
                "index_data_path": str(index_paths[0]) if index_paths else None,
                "index_manifest_path": str(index_paths[1]) if index_paths else None,
                "bar_count": len(all_bars),
                "venue_meta": venue_meta,
                "index_meta": index_meta,
                "runtime_effect": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
