"""Recommend, but never create, additional widget collector symbols.

The deterministic report combines up to 20 clean-baseline exact Entry-AI
payload/replay dates.  It is an operator recommendation and has no authority to
create collectors, start services, call Kiwoom, or alter trading behavior.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any, Callable
from urllib import parse, request

from src.engine.monitoring import widget_mechanical_entry_replay as mechanical_replay
from src.engine.monitoring.samsung_widget_contract import (
    KST,
    NXT_AFTERMARKET_END,
    previous_krx_trading_date,
)
from src.engine.risk.manual_control_exclusion import (
    configured_manual_control_exclusion_codes,
)
from src.engine.scalping.ai_decision_trace import replay_source_input
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

AUTHORITY = "widget_collector_expansion_recommendation_only"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
ACTIVE_WIDGET_CODES = frozenset({"005930", "034020", "042660"})
DEFAULT_REPLAY_DIR = Path("data/report/widget_mechanical_entry_replay")
DEFAULT_PAYLOAD_DIR = Path("data/ai_decision_payloads")
DEFAULT_SENTINEL_DIR = Path("data/runtime/sentinel_event_cache")
DEFAULT_OUTPUT_DIR = Path("data/report/widget_collector_expansion_recommendation")
DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "widget_collector_expansion_telegram_state.json"
)
MAX_SOURCE_DATES = 20
MAX_RECOMMENDATIONS = 5

METRIC_CONTRACT = {
    "metric_role": "collector_expansion_recommendation",
    "decision_authority": AUTHORITY,
    "window_policy": "last_20_available_clean_baseline_exact_replay_dates",
    "sample_floor": "two_joined_rows_and_one_decisive_outcome",
    "primary_decision_metric": "equal_weight_avg_profit_pct",
    "source_quality_gate": (
        "portable_mechanical_candidate_with_exact_replay_outcome_plus_"
        "fresh_entry_context_liquidity_and_quote_features"
    ),
    "forbidden_uses": [
        "automatic_collector_creation",
        "automatic_service_start_or_restart",
        "real_order_submission",
        "account_or_quantity_decision",
        "trading_runtime_threshold",
        "provider_or_token_route_change",
        "broker_or_hard_safety_bypass",
    ],
}

Sender = Callable[[str, str, str], None]
ConfigLoader = Callable[[], tuple[str, str]]


def _dated_paths(directory: Path, prefix: str, *, through_date: date) -> list[Path]:
    selected: list[tuple[date, Path]] = []
    for path in directory.glob(f"{prefix}_*.json*"):
        raw_date = path.name.removeprefix(f"{prefix}_").split(".", 1)[0]
        try:
            artifact_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if CLEAN_BASELINE_DATE <= artifact_date <= through_date:
            selected.append((artifact_date, path))
    return [path for _, path in sorted(selected)[-MAX_SOURCE_DATES:]]


def _load_names(paths: list[Path]) -> dict[str, str]:
    names: dict[str, str] = {}
    for replay_path in paths:
        target_date = replay_path.stem.rsplit("_", 1)[-1]
        sentinel_path = DEFAULT_SENTINEL_DIR / (
            f"buy_funnel_sentinel_events_{target_date}.jsonl"
        )
        try:
            handle = sentinel_path.open("r", encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                code = str(row.get("stock_code") or "").strip()
                name = str(row.get("stock_name") or "").strip()
                if code and name:
                    names[code] = name
    return names


def _payload_feature(value: object, key: str) -> float | None:
    payload = value if isinstance(value, dict) else {}
    exact = payload.get("exact_payload")
    exact = exact if isinstance(exact, dict) else {}
    features = exact.get("features")
    features = features if isinstance(features, dict) else {}
    try:
        return float(features[key])
    except (KeyError, TypeError, ValueError):
        return None


def _source_qualified_exact_payload(row: object) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    if (
        row.get("schema") != "ai_decision_payload_v1"
        or row.get("endpoint") != "analyze_target"
        or row.get("replay_exact") is not True
        or row.get("runtime_effect") is not False
        or row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
    ):
        return None
    sanitized = replay_source_input(row)
    exact = sanitized.get("exact_payload") if isinstance(sanitized, dict) else None
    if not isinstance(exact, dict):
        return None
    context = exact.get("entry_candle_context")
    context_quality = (
        context.get("source_quality") if isinstance(context, dict) else None
    )
    quote = exact.get("quote")
    if (
        not isinstance(context_quality, dict)
        or context_quality.get("status") != "fresh_consistent"
        or not isinstance(quote, dict)
        or quote.get("quote_stale") not in {True, False}
    ):
        return None
    return exact


def _load_feature_history(
    payload_dir: Path,
    *,
    through_date: date,
    eligible_codes: frozenset[str] | None = None,
) -> tuple[dict[str, list[dict[str, float | bool]]], list[str]]:
    history: dict[str, list[dict[str, float | bool]]] = defaultdict(list)
    paths = _dated_paths(
        payload_dir,
        "ai_decision_payloads",
        through_date=through_date,
    )
    if eligible_codes is not None and not eligible_codes:
        return history, [str(path) for path in paths]
    for path in paths:
        try:
            handle = path.open("r", encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if (
                    str(row.get("effective_venue") or "").upper() != "KRX"
                    or str(row.get("session_bucket") or "").lower() != "krx_regular"
                ):
                    continue
                exact = _source_qualified_exact_payload(row)
                if exact is None:
                    continue
                code = str(row.get("symbol") or "").strip()
                if eligible_codes is not None and code not in eligible_codes:
                    continue
                sanitized = replay_source_input(row)
                liquidity = _payload_feature(sanitized, "entry_liquidity_score")
                intraday_range = _payload_feature(sanitized, "intraday_range_pct")
                spread_bp = _payload_feature(sanitized, "spread_bp")
                quote = exact.get("quote") if isinstance(exact, dict) else None
                quote_stale = (
                    quote.get("quote_stale") if isinstance(quote, dict) else None
                )
                if (
                    not code
                    or liquidity is None
                    or intraday_range is None
                    or spread_bp is None
                    or quote_stale not in {True, False}
                ):
                    continue
                history[code].append(
                    {
                        "entry_liquidity_score": liquidity,
                        "intraday_range_pct": abs(intraday_range),
                        "spread_bp": spread_bp,
                        "quote_fresh": quote_stale is False,
                    }
                )
    return history, [str(path) for path in paths]


def _load_replay_history(
    replay_dir: Path,
    *,
    through_date: date,
    current_replay_report: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[Path]]:
    aggregates: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sample_count": 0,
            "source_qualified_joined_count": 0,
            "target_first_count": 0,
            "adverse_first_count": 0,
            "end_returns": [],
            "mechanical_signal_count": 0,
            "pre_spread_candidate_count": 0,
        }
    )
    paths = _dated_paths(
        replay_dir,
        "widget_mechanical_entry_replay",
        through_date=through_date,
    )
    paths = [path for path in paths if path.suffix == ".json"]
    current_target_date = (
        str(current_replay_report.get("target_date") or "")
        if isinstance(current_replay_report, dict)
        else ""
    )
    reports: list[tuple[Path | None, object]] = []
    for path in paths:
        if current_target_date and path.stem.endswith(f"_{current_target_date}"):
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        reports.append((path, report))
    if current_replay_report is not None:
        reports.append((None, current_replay_report))
    accepted_paths: list[Path] = []
    for path, report in reports:
        if (
            not isinstance(report, dict)
            or report.get("schema") != "widget_mechanical_entry_replay_v1"
            or report.get("runtime_effect") is not False
            or report.get("allowed_runtime_apply") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
        ):
            continue
        try:
            report_date = date.fromisoformat(str(report.get("target_date") or ""))
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date <= through_date:
            continue
        if path is not None and not path.stem.endswith(f"_{report_date}"):
            continue
        if path is not None:
            accepted_paths.append(path)
        for row in report.get("rows", []):
            if not isinstance(row, dict):
                continue
            if (
                str(row.get("effective_venue") or "").upper() != "KRX"
                or str(row.get("session_bucket") or "").lower() != "krx_regular"
            ):
                continue
            code = str(row.get("stock_code") or "").strip()
            if not (len(code) == 6 and code.isdigit()):
                continue
            if (
                row.get("runtime_effect") is not False
                or row.get("actual_order_submitted") is not False
                or row.get("broker_order_forbidden") is not True
            ):
                continue
            item = aggregates[code]
            if str(row.get("mechanical_source_issue") or "").strip():
                continue
            item["source_qualified_joined_count"] += 1
            if not (
                row.get("mechanical_signal") is True
                or row.get("mechanical_candidate_before_spread_gate") is True
            ):
                continue
            first_hit = str(row.get("entry_path_first_hit") or "")
            if first_hit not in {
                "target_first",
                "adverse_first",
                "same_bar_ambiguous",
                "neither_hit",
            }:
                continue
            try:
                end_return = float(row.get("end_return_pct"))
            except (TypeError, ValueError):
                continue
            item["sample_count"] += 1
            if first_hit == "target_first":
                item["target_first_count"] += 1
            elif first_hit == "adverse_first":
                item["adverse_first_count"] += 1
            item["end_returns"].append(end_return)
            item["mechanical_signal_count"] += row.get("mechanical_signal") is True
            item["pre_spread_candidate_count"] += (
                row.get("mechanical_candidate_before_spread_gate") is True
            )
    return aggregates, accepted_paths


def _score_candidate(
    *,
    target_share_pct: float,
    equal_weight_ev_pct: float,
    liquidity_score: float,
    intraday_range_pct: float,
    sample_count: int,
    portability_ratio: float,
) -> float:
    ev_component = max(0.0, min(1.0, (equal_weight_ev_pct + 1.0) / 2.0))
    volatility_component = max(0.0, min(1.0, (intraday_range_pct - 1.0) / 7.0))
    return round(
        target_share_pct * 0.40
        + ev_component * 25.0
        + max(0.0, min(100.0, liquidity_score)) * 0.15
        + min(1.0, sample_count / 10.0) * 10.0
        + volatility_component * 5.0
        + max(0.0, min(1.0, portability_ratio)) * 5.0,
        4,
    )


def build_recommendation_report(
    *,
    target_date: date,
    replay_dir: Path = DEFAULT_REPLAY_DIR,
    payload_dir: Path = DEFAULT_PAYLOAD_DIR,
    manual_excluded_codes: frozenset[str] | None = None,
    current_replay_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    replay, replay_paths = _load_replay_history(
        replay_dir,
        through_date=target_date,
        current_replay_report=current_replay_report,
    )
    excluded_codes = (
        configured_manual_control_exclusion_codes()
        if manual_excluded_codes is None
        else manual_excluded_codes
    )
    exclusion_counts: dict[str, int] = defaultdict(int)
    outcome_candidates: dict[str, dict[str, Any]] = {}
    for code, item in replay.items():
        if code in ACTIVE_WIDGET_CODES:
            exclusion_counts["already_active_widget"] += 1
            continue
        if code in excluded_codes:
            exclusion_counts["manual_control_excluded"] += 1
            continue
        samples = int(item["sample_count"])
        target_first = int(item["target_first_count"])
        adverse_first = int(item["adverse_first_count"])
        decisive = target_first + adverse_first
        end_returns = item["end_returns"]
        equal_weight_ev = sum(end_returns) / len(end_returns) if end_returns else 0.0
        if samples < 2 or decisive < 1:
            exclusion_counts["sample_floor_not_met"] += 1
            continue
        if target_first <= adverse_first or equal_weight_ev <= 0:
            exclusion_counts["outcome_quality_not_positive"] += 1
            continue
        outcome_candidates[code] = {
            **item,
            "sample_count": samples,
            "target_first_count": target_first,
            "adverse_first_count": adverse_first,
            "decisive_sample_count": decisive,
            "equal_weight_avg_profit_pct": equal_weight_ev,
        }
    features, feature_paths = _load_feature_history(
        payload_dir,
        through_date=target_date,
        eligible_codes=frozenset(outcome_candidates),
    )
    names = _load_names(replay_paths)
    candidates: list[dict[str, Any]] = []
    for code, item in outcome_candidates.items():
        samples = int(item["sample_count"])
        target_first = int(item["target_first_count"])
        adverse_first = int(item["adverse_first_count"])
        decisive = int(item["decisive_sample_count"])
        equal_weight_ev = float(item["equal_weight_avg_profit_pct"])
        feature_rows = features.get(code, [])
        if not feature_rows:
            exclusion_counts["liquidity_feature_missing"] += 1
            continue
        liquidity = median(float(row["entry_liquidity_score"]) for row in feature_rows)
        intraday_range = median(
            float(row["intraday_range_pct"]) for row in feature_rows
        )
        spread_bp = median(float(row["spread_bp"]) for row in feature_rows)
        fresh_quote_rate = sum(bool(row["quote_fresh"]) for row in feature_rows) / len(
            feature_rows
        )
        if liquidity < 60 or intraday_range < 1.0 or fresh_quote_rate < 0.80:
            exclusion_counts["tradability_floor_not_met"] += 1
            continue
        portability_count = samples
        source_qualified_joined_count = int(item["source_qualified_joined_count"])
        portability_ratio = portability_count / max(1, source_qualified_joined_count)
        target_share = target_first / decisive * 100
        candidates.append(
            {
                "stock_code": code,
                "stock_name": names.get(code) or code,
                "recommendation_score": _score_candidate(
                    target_share_pct=target_share,
                    equal_weight_ev_pct=equal_weight_ev,
                    liquidity_score=liquidity,
                    intraday_range_pct=intraday_range,
                    sample_count=samples,
                    portability_ratio=portability_ratio,
                ),
                "sample_count": samples,
                "decisive_sample_count": decisive,
                "target_first_count": target_first,
                "adverse_first_count": adverse_first,
                "diagnostic_target_share_among_decisive_pct": round(target_share, 4),
                "equal_weight_avg_profit_pct": round(equal_weight_ev, 6),
                "source_quality_adjusted_ev_pct": round(equal_weight_ev, 6),
                "source_quality_adjustment_policy": (
                    "exclude_ineligible_rows_then_equal_weight"
                ),
                "median_entry_liquidity_score": round(liquidity, 4),
                "median_intraday_range_pct": round(intraday_range, 4),
                "extreme_volatility_warning": intraday_range > 12.0,
                "median_spread_bp": round(spread_bp, 4),
                "fresh_quote_rate_pct": round(fresh_quote_rate * 100, 4),
                "portable_signal_or_candidate_count": portability_count,
                "source_qualified_joined_count": source_qualified_joined_count,
                "portability_ratio_pct": round(portability_ratio * 100, 4),
                "evidence_status": (
                    "early_sample" if samples < 10 else "accumulating_sample"
                ),
                "suggested_session": "KRX_REGULAR",
                "estimated_added_requests_per_minute": 13,
                "estimated_added_memory_mb": 100,
                "collector_created": False,
                "service_started": False,
            }
        )
    candidates.sort(
        key=lambda row: (
            float(row["recommendation_score"]),
            int(row["sample_count"]),
            str(row["stock_code"]),
        ),
        reverse=True,
    )
    recommendations = candidates[:MAX_RECOMMENDATIONS]
    return {
        "schema": "widget_collector_expansion_recommendation_v1",
        "status": (
            "recommendations_ready" if recommendations else "no_qualified_candidate"
        ),
        "target_date": target_date.isoformat(),
        "generated_at": datetime.now(KST).isoformat(),
        "authority": AUTHORITY,
        "recommendations": recommendations,
        "qualified_candidate_count": len(candidates),
        "reported_candidate_count": len(recommendations),
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "source": {
            "market_session_scope": "KRX_REGULAR_ONLY",
            "replay_paths": [str(path) for path in replay_paths],
            "current_replay_in_memory_target_date": (
                str(current_replay_report.get("target_date") or "")
                if isinstance(current_replay_report, dict)
                else None
            ),
            "feature_paths": feature_paths,
            "active_widget_codes": sorted(ACTIVE_WIDGET_CODES),
            "manual_excluded_codes": sorted(excluded_codes),
        },
        "metric_contract": METRIC_CONTRACT,
        "recommendation_only": True,
        "collector_created": False,
        "service_started": False,
        "widget_runtime_effect": False,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_telegram_message(report: dict[str, Any]) -> str:
    lines = [
        "📋 [위젯 수집서비스 확대 후보]",
        f"기준일: {report.get('target_date')}",
        "권한: 추천 전용 · 자동 생성/기동 없음",
    ]
    recommendations = report.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        lines.append("오늘 기준을 통과한 신규 후보가 없습니다.")
        return "\n".join(lines)
    for index, row in enumerate(recommendations, start=1):
        lines.extend(
            [
                (
                    f"{index}. {row.get('stock_name')}({row.get('stock_code')}) "
                    f"점수 {row.get('recommendation_score')}"
                ),
                (
                    "   target/adverse "
                    f"{row.get('target_first_count')}/{row.get('adverse_first_count')}, "
                    f"EV {row.get('source_quality_adjusted_ev_pct')}%, "
                    f"유동성 {row.get('median_entry_liquidity_score')}, "
                    f"장중범위 {row.get('median_intraday_range_pct')}%"
                ),
                (
                    "   예상부하 +"
                    f"{row.get('estimated_added_requests_per_minute')} req/min, "
                    f"+{row.get('estimated_added_memory_mb')}MB"
                ),
            ]
        )
    lines.append("사용자 승인 전에는 collector/service를 만들거나 시작하지 않습니다.")
    return "\n".join(lines)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _source_artifact_issues(
    *,
    target_date: date,
    payload_path: Path,
    label_path: Path,
) -> list[str]:
    issues: list[str] = []
    if not payload_path.is_file():
        issues.append("exact_payload_artifact_missing")
    try:
        label_report = json.loads(label_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        label_report = None
    if not isinstance(label_report, dict):
        issues.append("outcome_label_artifact_missing_or_invalid")
        return issues
    try:
        label_generated_at = datetime.fromisoformat(
            str(label_report.get("generated_at") or "")
        )
        if label_generated_at.tzinfo is None:
            raise ValueError
        label_generated_at = label_generated_at.astimezone(KST)
    except (TypeError, ValueError):
        label_generated_at = None
    earliest_complete_time = datetime.combine(
        target_date,
        NXT_AFTERMARKET_END,
        tzinfo=KST,
    )
    if (
        label_report.get("schema") != "ai_decision_outcome_labels_v1"
        or label_report.get("target_date") != target_date.isoformat()
        or label_report.get("status")
        not in {"mature_label_rows_available", "partial_horizons_keep_maturing"}
        or not isinstance(label_report.get("labels"), list)
        or label_generated_at is None
        or label_generated_at < earliest_complete_time
        or label_report.get("runtime_effect") is not False
        or label_report.get("allowed_runtime_apply") is not False
        or label_report.get("actual_order_submitted") is not False
        or label_report.get("broker_order_forbidden") is not True
    ):
        issues.append("outcome_label_contract_mismatch")
    return issues


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


class WidgetExpansionRecommendationNotifier:
    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        enabled: bool | None = None,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.enabled = (
            str(os.getenv("KORSTOCKSCAN_WIDGET_EXPANSION_TELEGRAM_ENABLED", "true"))
            .strip()
            .lower()
            not in {"0", "false", "no", "off"}
            if enabled is None
            else bool(enabled)
        )

    def notify(self, report: dict[str, Any]) -> str:
        if not self.enabled:
            return "disabled"
        if (
            report.get("schema") != "widget_collector_expansion_recommendation_v1"
            or report.get("status")
            not in {"recommendations_ready", "no_qualified_candidate"}
            or report.get("metric_contract") != METRIC_CONTRACT
            or report.get("authority") != AUTHORITY
            or report.get("recommendation_only") is not True
            or report.get("widget_runtime_effect") is not False
            or report.get("trading_runtime_effect") is not False
            or report.get("runtime_effect") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
            or report.get("collector_created") is not False
            or report.get("service_started") is not False
        ):
            return "invalid_report"
        target_date = str(report.get("target_date") or "")
        try:
            date.fromisoformat(target_date)
        except ValueError:
            return "invalid_report"
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if (
            isinstance(state, dict)
            and state.get("last_sent_target_date") == target_date
        ):
            return "duplicate"
        token, admin_id = self.config_loader()
        if not token or not admin_id:
            return "missing_config"
        try:
            self.sender(token, admin_id, build_telegram_message(report))
        except Exception:
            return "send_failed"
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_file.with_name(
                f".{self.state_file.name}.{os.getpid()}.tmp"
            )
            temporary.write_text(
                json.dumps(
                    {
                        "last_sent_target_date": target_date,
                        "authority": AUTHORITY,
                        "telegram_audience": "ADMIN_ONLY",
                        "runtime_effect": False,
                        "collector_created": False,
                        "service_started": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            os.replace(temporary, self.state_file)
        except OSError:
            return "sent_state_persist_failed"
        return "sent"


def _resolve_default_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) >= NXT_AFTERMARKET_END
    ):
        return current.date()
    return previous_krx_trading_date(current.date())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--payload-dir", type=Path, default=DEFAULT_PAYLOAD_DIR)
    parser.add_argument(
        "--label-dir", type=Path, default=mechanical_replay.DEFAULT_LABEL_DIR
    )
    parser.add_argument("--replay-dir", type=Path, default=DEFAULT_REPLAY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else _resolve_default_target_date()
    )
    if not is_krx_trading_day(target_date):
        raise ValueError(
            "widget_expansion_recommendation_requires_krx_trading_date:"
            f"{target_date}"
        )
    payload_path = args.payload_dir / f"ai_decision_payloads_{target_date}.jsonl"
    label_path = args.label_dir / f"ai_decision_outcome_labels_{target_date}.json"
    source_issues = _source_artifact_issues(
        target_date=target_date,
        payload_path=payload_path,
        label_path=label_path,
    )
    if source_issues:
        raise RuntimeError(
            "widget_expansion_source_not_ready:" + ",".join(source_issues)
        )
    replay_report = mechanical_replay.build_report_for_date(
        target_date,
        payload_dir=args.payload_dir,
        label_dir=args.label_dir,
    )
    if args.write:
        mechanical_replay.write_report(replay_report, output_dir=args.replay_dir)
    report = build_recommendation_report(
        target_date=target_date,
        replay_dir=args.replay_dir,
        payload_dir=args.payload_dir,
        current_replay_report=None if args.write else replay_report,
    )
    report["telegram_status"] = "not_requested"
    output_path = args.output_dir / (
        f"widget_collector_expansion_recommendation_{target_date}.json"
    )
    if args.write:
        _atomic_write(output_path, report)
    if args.notify:
        report["telegram_status"] = WidgetExpansionRecommendationNotifier().notify(
            report
        )
        if args.write:
            _atomic_write(output_path, report)
        if report["telegram_status"] not in {
            "sent",
            "duplicate",
            "sent_state_persist_failed",
        }:
            raise RuntimeError(
                "widget_expansion_telegram_not_delivered:"
                f"{report['telegram_status']}"
            )
    if not args.write:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
