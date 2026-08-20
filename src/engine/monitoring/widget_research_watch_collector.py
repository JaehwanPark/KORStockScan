"""Collect low-rate KRX evidence for user-approved widget research watches.

This collector is intentionally below the advisory and execution layers.  It
stores one completed-minute observation per symbol and cannot create signals,
policies, orders, accounts, tokens, services, or trading state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, time as clock_time
from pathlib import Path
from typing import Any

from src.engine.monitoring.samsung_widget_advisory import (
    KiwoomReadOnlyClient,
    ReadOnlyRequestBudget,
    _parse_bbo,
    _positive_int,
    completed_session_bars,
)
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_symbol_runtime_policy import OFFICIAL_REFERENCE
from src.engine.sniper_config import CONF
from src.utils import kiwoom_utils
from src.utils.constants import PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

AUTHORITY = "operator_directed_widget_research_watch_observation_only"
CONFIG_SCHEMA = "widget_research_watch_config_v1"
OBSERVATION_SCHEMA = "widget_research_watch_observation_v1"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "data/config/widget_research_watch_symbols.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/monitoring/widget_research_watch"
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data/runtime/widget_research_watch"
COLLECTION_START = clock_time(9, 0)
COLLECTION_END = clock_time(15, 31)
DEFAULT_INTERVAL_SEC = 60.0
MAX_SYMBOLS = 15
REQUESTS_PER_SYMBOL_CYCLE = 3
REQUEST_BUDGET_PER_MINUTE = 18
REQUEST_BUDGET_HEADROOM = 3

METRIC_CONTRACT = {
    "metric_role": "widget_research_watch_market_observation",
    "decision_authority": AUTHORITY,
    "window_policy": (
        "krx_regular_latest_completed_one_minute_at_budget_paced_symbol_cycle"
    ),
    "sample_floor": "one_fresh_quote_bbo_and_completed_bar_row",
    "primary_decision_metric": "future_symbol_specific_cost_adjusted_ev_pct",
    "source_quality_gate": "fresh_krx_quote_bbo_and_completed_one_minute_bar",
    "forbidden_uses": [
        "entry_or_exit_signal",
        "automatic_policy_or_collector_promotion",
        "real_or_sim_order_submission",
        "account_or_quantity_decision",
        "token_issue_or_refresh",
        "provider_or_bot_change",
        "broker_or_hard_safety_bypass",
    ],
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"widget_research_watch_json_invalid:{path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"widget_research_watch_json_not_object:{path}")
    return payload


def load_config(
    *,
    observed_date: date,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = _load_json(config_path)
    if (
        config.get("schema") != CONFIG_SCHEMA
        or config.get("enabled") is not True
        or config.get("authority") != AUTHORITY
        or config.get("runtime_effect") is not False
        or config.get("allowed_runtime_apply") is not False
        or config.get("actual_order_submitted") is not False
        or config.get("broker_order_forbidden") is not True
    ):
        raise ValueError("widget_research_watch_config_contract_mismatch")
    try:
        effective_from = date.fromisoformat(str(config.get("effective_from") or ""))
    except ValueError as exc:
        raise ValueError("widget_research_watch_effective_date_invalid") from exc
    if observed_date < effective_from:
        raise ValueError("widget_research_watch_not_yet_effective")
    rows = config.get("symbols")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_SYMBOLS:
        raise ValueError("widget_research_watch_symbol_count_invalid")
    symbols: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("widget_research_watch_symbol_row_invalid")
        code = str(row.get("stock_code") or "").strip()
        name = str(row.get("stock_name") or "").strip()
        tier = str(row.get("recommendation_tier") or "").strip()
        if (
            len(code) != 6
            or not code.isdigit()
            or not name
            or tier != "research_watch"
            or code in seen
        ):
            raise ValueError("widget_research_watch_symbol_contract_mismatch")
        seen.add(code)
        symbols.append(
            {
                "stock_code": code,
                "stock_name": name,
                "recommendation_tier": tier,
                "source_target_date": str(row.get("source_target_date") or ""),
                "source_report_sha256": str(
                    row.get("source_report_sha256") or ""
                ).strip(),
            }
        )

    source_rows = config.get("source_reports")
    if source_rows is None:
        source_rows = [
            {
                "target_date": config.get("source_target_date"),
                "path": config.get("source_report"),
                "sha256": config.get("source_report_sha256"),
            }
        ]
    if (
        not isinstance(source_rows, list)
        or not source_rows
        or len(source_rows) > MAX_SYMBOLS
    ):
        raise ValueError("widget_research_watch_source_reports_invalid")

    allowed_by_lineage: dict[tuple[str, str], set[str]] = {}
    resolved_sources: list[dict[str, str]] = []
    for source_row in source_rows:
        if not isinstance(source_row, dict):
            raise ValueError("widget_research_watch_source_report_row_invalid")
        target_date = str(source_row.get("target_date") or "").strip()
        source_path = PROJECT_ROOT / str(source_row.get("path") or "")
        expected_sha = str(source_row.get("sha256") or "").strip()
        try:
            source_target_date = date.fromisoformat(target_date)
        except ValueError as exc:
            raise ValueError(
                "widget_research_watch_source_target_date_invalid"
            ) from exc
        if source_target_date >= effective_from:
            raise ValueError("widget_research_watch_source_not_prior_to_effective_date")
        if not source_path.is_file() or len(expected_sha) != 64:
            raise ValueError("widget_research_watch_source_report_missing")
        if _sha256(source_path) != expected_sha:
            raise ValueError("widget_research_watch_source_report_hash_mismatch")
        report = _load_json(source_path)
        if (
            report.get("schema") != "widget_collector_expansion_recommendation_v1"
            or report.get("target_date") != target_date
            or report.get("runtime_effect") is not False
            or report.get("allowed_runtime_apply") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
            or report.get("collector_created") is not False
            or report.get("service_started") is not False
        ):
            raise ValueError("widget_research_watch_source_report_contract_mismatch")
        recommendation_rows = report.get("recommendations")
        allowed = (
            {
                str(row.get("stock_code") or "")
                for row in recommendation_rows
                if isinstance(row, dict)
                and row.get("recommendation_tier") == "research_watch"
                and row.get("implementation_review_ready") is False
            }
            if isinstance(recommendation_rows, list)
            else set()
        )
        lineage = (target_date, expected_sha)
        if lineage in allowed_by_lineage:
            raise ValueError("widget_research_watch_source_report_duplicate")
        allowed_by_lineage[lineage] = allowed
        resolved_sources.append(
            {
                "target_date": target_date,
                "path": str(source_path),
                "sha256": expected_sha,
            }
        )

    default_lineage = (
        str(config.get("source_target_date") or "").strip(),
        str(config.get("source_report_sha256") or "").strip(),
    )
    default_source_path = str(PROJECT_ROOT / str(config.get("source_report") or ""))
    if default_lineage not in allowed_by_lineage or not any(
        row["target_date"] == default_lineage[0]
        and row["sha256"] == default_lineage[1]
        and row["path"] == default_source_path
        for row in resolved_sources
    ):
        raise ValueError("widget_research_watch_default_source_report_mismatch")
    used_lineages: set[tuple[str, str]] = set()
    for symbol in symbols:
        lineage = (
            symbol["source_target_date"] or default_lineage[0],
            symbol["source_report_sha256"] or default_lineage[1],
        )
        allowed = allowed_by_lineage.get(lineage)
        if allowed is None or symbol["stock_code"] not in allowed:
            raise ValueError("widget_research_watch_symbol_not_in_source_report")
        symbol["source_target_date"], symbol["source_report_sha256"] = lineage
        used_lineages.add(lineage)
    if used_lineages != set(allowed_by_lineage):
        raise ValueError("widget_research_watch_unused_source_report")
    return {
        **config,
        "symbols": symbols,
        "source_reports_resolved": resolved_sources,
        "source_report_resolved": default_source_path,
    }


class WidgetResearchWatchCollector:
    def __init__(
        self,
        *,
        config: dict[str, Any],
        client: KiwoomReadOnlyClient | None = None,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    ) -> None:
        self.config = config
        self.output_dir = output_dir
        self.snapshot_dir = snapshot_dir
        self.request_budget = ReadOnlyRequestBudget(
            max_requests_per_minute=REQUEST_BUDGET_PER_MINUTE
        )
        self._client_override = client
        self._last_record_key: dict[str, str] = {}

    def _client(self) -> KiwoomReadOnlyClient:
        if self._client_override is not None:
            return self._client_override
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        if not token:
            raise RuntimeError("shared_cached_token_unavailable")
        return KiwoomReadOnlyClient(token, budget=self.request_budget)

    def _collect_symbol(
        self,
        *,
        symbol: dict[str, str],
        observed_at: datetime,
        client: KiwoomReadOnlyClient,
    ) -> dict[str, Any]:
        code = symbol["stock_code"]
        quote = client.post("/api/dostk/stkinfo", "ka10001", {"stk_cd": code})
        bbo_raw = client.post("/api/dostk/mrkcond", "ka10004", {"stk_cd": code})
        bars_raw = client.post(
            "/api/dostk/chart",
            "ka10080",
            {"stk_cd": code, "tic_scope": "1", "upd_stkpc_tp": "1"},
        )
        bbo = _parse_bbo(bbo_raw, observed_at)
        bars = completed_session_bars(
            bars_raw.get("stk_min_pole_chart_qry"),
            observed_at=observed_at,
            session_start=COLLECTION_START,
            session_end=clock_time(15, 30),
            limit=400,
        )
        latest = bars[-1] if bars else None
        current_price = _positive_int(quote.get("cur_prc"))
        best_bid = _positive_int(bbo.get("best_bid"))
        best_ask = _positive_int(bbo.get("best_ask"))
        source_issues: list[str] = []
        if current_price is None:
            source_issues.append("quote_price_missing")
        if best_bid is None or best_ask is None or best_ask < best_bid:
            source_issues.append("bbo_invalid")
        if latest is None:
            source_issues.append("completed_bar_missing")
        else:
            try:
                latest_at = datetime.strptime(
                    latest.source_time[:12], "%Y%m%d%H%M"
                ).replace(tzinfo=KST)
            except ValueError:
                source_issues.append("completed_bar_timestamp_invalid")
            else:
                age_sec = (observed_at - latest_at).total_seconds()
                if not 0 <= age_sec <= 120:
                    source_issues.append("completed_bar_stale")
        return {
            "schema": OBSERVATION_SCHEMA,
            "status": "PASS" if not source_issues else "SOURCE_QUALITY_BLOCKED",
            "stock_code": code,
            "stock_name": symbol["stock_name"],
            "observed_at_kst": observed_at.isoformat(),
            "trading_date": observed_at.date().isoformat(),
            "market_venue": "KRX",
            "market_session": "KRX_REGULAR",
            "current_price": current_price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_bp": (
                round((best_ask - best_bid) / best_bid * 10000.0, 6)
                if best_bid and best_ask
                else None
            ),
            "latest_completed_bar": (
                {
                    "source_time": latest.source_time,
                    "open": latest.open,
                    "high": latest.high,
                    "low": latest.low,
                    "close": latest.close,
                    "volume": latest.volume,
                }
                if latest is not None
                else None
            ),
            "source_quality_issues": source_issues,
            "source_recommendation": {
                "target_date": symbol["source_target_date"],
                "report_sha256": symbol["source_report_sha256"],
                "recommendation_tier": symbol["recommendation_tier"],
                "operator_directed_implementation": True,
            },
            "official_reference": OFFICIAL_REFERENCE,
            "token_mode": "shared_cache_only_no_issue_no_refresh",
            "metric_contract": METRIC_CONTRACT,
            "authority": AUTHORITY,
            "advisory_generated": False,
            "entry_event": None,
            "exit_event": None,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }

    def _record(self, payload: dict[str, Any]) -> bool:
        code = str(payload["stock_code"])
        latest = payload.get("latest_completed_bar")
        bar_time = latest.get("source_time") if isinstance(latest, dict) else None
        observation_minute = str(payload.get("observed_at_kst") or "")[:16]
        key = (
            f"{payload['trading_date']}:"
            f"{bar_time or observation_minute}:{payload['status']}"
        )
        snapshot_path = self.snapshot_dir / f"{code}.json"
        try:
            previous_snapshot = _load_json(snapshot_path)
        except ValueError:
            previous_snapshot = {}
        payload["record_key"] = key
        _atomic_write(snapshot_path, payload)
        if (
            self._last_record_key.get(code) == key
            or previous_snapshot.get("record_key") == key
        ):
            self._last_record_key[code] = key
            return False
        self._last_record_key[code] = key
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / (
            f"widget_research_watch_{code}_{payload['trading_date'].replace('-', '')}.jsonl"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return True

    def _collect_symbol_safely(
        self,
        *,
        symbol: dict[str, str],
        observed_at: datetime,
        client: KiwoomReadOnlyClient,
    ) -> dict[str, Any]:
        try:
            return self._collect_symbol(
                symbol=symbol,
                observed_at=observed_at,
                client=client,
            )
        except Exception as exc:
            return {
                "schema": OBSERVATION_SCHEMA,
                "status": "SOURCE_ERROR",
                "stock_code": symbol["stock_code"],
                "stock_name": symbol["stock_name"],
                "observed_at_kst": observed_at.isoformat(),
                "trading_date": observed_at.date().isoformat(),
                "market_venue": "KRX",
                "market_session": "KRX_REGULAR",
                "latest_completed_bar": None,
                "source_quality_issues": [type(exc).__name__],
                "source_recommendation": {
                    "target_date": symbol["source_target_date"],
                    "report_sha256": symbol["source_report_sha256"],
                    "recommendation_tier": symbol["recommendation_tier"],
                    "operator_directed_implementation": True,
                },
                "official_reference": OFFICIAL_REFERENCE,
                "token_mode": "shared_cache_only_no_issue_no_refresh",
                "metric_contract": METRIC_CONTRACT,
                "authority": AUTHORITY,
                "advisory_generated": False,
                "entry_event": None,
                "exit_event": None,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }

    def collect_once(
        self,
        observed_at: datetime | None = None,
        *,
        pace_requests: bool = False,
    ) -> list[dict[str, Any]]:
        current = (observed_at or datetime.now(KST)).astimezone(KST)
        if not (COLLECTION_START <= current.time() < COLLECTION_END):
            return []
        client = self._client()
        results: list[dict[str, Any]] = []
        symbols = self.config["symbols"]
        pause_sec = (
            _effective_cycle_interval_sec(
                configured_interval_sec=DEFAULT_INTERVAL_SEC,
                symbol_count=len(symbols),
            )
            / len(symbols)
            if pace_requests
            else 0.0
        )
        for index, symbol in enumerate(symbols):
            symbol_observed_at = datetime.now(KST) if pace_requests else current
            if symbol_observed_at.time() >= COLLECTION_END:
                break
            payload = self._collect_symbol_safely(
                symbol=symbol,
                observed_at=symbol_observed_at,
                client=client,
            )
            self._record(payload)
            results.append(payload)
            if pause_sec > 0 and index + 1 < len(symbols):
                time.sleep(pause_sec)
        return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--interval-sec", type=float, default=DEFAULT_INTERVAL_SEC)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--check-config", action="store_true")
    return parser


def _effective_cycle_interval_sec(
    *, configured_interval_sec: float, symbol_count: int
) -> float:
    """Pace the shared collector without widening its Kiwoom REST budget.

    Each symbol uses quote, BBO, and minute-bar requests.  Preserve three
    requests per minute as headroom for timing jitter and shared-token
    contention instead of raising the existing collector-local budget when the
    operator enrolls more symbols.
    """

    symbols = max(1, int(symbol_count))
    usable_per_minute = max(
        REQUESTS_PER_SYMBOL_CYCLE,
        REQUEST_BUDGET_PER_MINUTE - REQUEST_BUDGET_HEADROOM,
    )
    budget_paced = symbols * REQUESTS_PER_SYMBOL_CYCLE / usable_per_minute * 60.0
    return max(30.0, float(configured_interval_sec), budget_paced)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    observed_at = datetime.now(KST)
    if not is_krx_trading_day(observed_at.date()):
        return 1 if args.check_config else 0
    try:
        config = load_config(observed_date=observed_at.date(), config_path=args.config)
    except ValueError:
        return 1 if args.check_config else 2
    if args.check_config:
        return 0
    collector = WidgetResearchWatchCollector(config=config)
    if args.once:
        collector.collect_once(observed_at, pace_requests=True)
        return 0
    symbols = max(1, len(config["symbols"]))
    interval_sec = _effective_cycle_interval_sec(
        configured_interval_sec=float(args.interval_sec),
        symbol_count=symbols,
    )
    per_symbol_pause = interval_sec / symbols
    while True:
        now = datetime.now(KST)
        if now.time() >= COLLECTION_END:
            return 0
        if now.time() < COLLECTION_START:
            time.sleep(
                min(
                    30.0,
                    (
                        datetime.combine(now.date(), COLLECTION_START, KST) - now
                    ).total_seconds(),
                )
            )
            continue
        client = collector._client()
        for symbol in config["symbols"]:
            current = datetime.now(KST)
            if current.time() >= COLLECTION_END:
                return 0
            payload = collector._collect_symbol_safely(
                symbol=symbol,
                observed_at=current,
                client=client,
            )
            collector._record(payload)
            time.sleep(per_symbol_pause)


if __name__ == "__main__":
    raise SystemExit(main())
