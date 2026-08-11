"""Walk-forward entry-spot research for additional lower-price symbols.

This source-only module deliberately keeps its candidate universe separate from
the live profile allowlist. It reuses the completed integrated-SOR minute-bar
research contract and cannot issue or refresh tokens, access accounts, submit
orders, or mutate runtime policy.
"""

from __future__ import annotations

import argparse
import json
import os
import time as time_module
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib import parse, request

import requests

from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    CLEAN_BASELINE_DATE,
    COST_PCT,
    CALIBRATION_DAYS,
    HOLDOUT_DAYS,
    OFFICIAL_REFERENCE,
    Bar,
    ResearchError,
    _atomic_write,
    build_day_contexts,
    fetch_sor_history,
    select_profile_spot,
)
from src.trading.order.regular_two_leg_machine import KST
from src.utils import kiwoom_utils
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH, PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

REPORT_SCHEMA = "low_price_two_leg_expanded_candidate_research_v2"
REPORT_TYPE = "low_price_two_leg_expanded_candidate_research"
AUTHORITY = "lower_price_machine_candidate_recommendation_only"
OUTPUT_DIR = DATA_DIR / "report" / "low_price_two_leg_expanded_candidate_research"
DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "low_price_two_leg_candidate_telegram_state.json"
)
ROLLING_WINDOW_DAYS = CALIBRATION_DAYS + HOLDOUT_DAYS
MAX_RECOMMENDATIONS = 5
MAX_LATEST_CLOSE_PRICE = 100_000
MIDDAY_WINDOW = (time(13, 15), time(13, 54))
AFTERNOON_WINDOW = (time(14, 0), time(14, 40))
CANDIDATE_SYMBOLS = {
    "006800": "미래에셋증권",
    "007660": "이수페타시스",
    "015760": "한국전력",
    "017670": "SK텔레콤",
    "028050": "삼성E&A",
    "034020": "두산에너빌리티",
    "035720": "카카오",
    "042660": "한화오션",
    "080220": "제주반도체",
}

METRIC_CONTRACT = {
    "metric_role": "lower_price_machine_candidate_recommendation",
    "decision_authority": AUTHORITY,
    "window_policy": "rolling_46_trading_days_30_calibration_16_untouched_holdout",
    "sample_floor": {
        "calibration_signal_episodes": 6,
        "calibration_completed_legs": 8,
        "each_calibration_half_completed_legs": 3,
        "holdout_signal_episodes": 3,
        "holdout_completed_legs": 4,
        "full_window_completed_legs": 10,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "official_ka10080_success",
        "requested_start_date_fully_bracketed",
        "46_matching_clean_baseline_trading_dates_for_every_symbol",
        "valid_unique_completed_sor_regular_ohlc",
        "calibration_and_holdout_held_legs_zero",
        "latest_close_at_or_below_100000_krw",
    ],
    "forbidden_uses": [
        "automatic_machine_implementation_or_service_start",
        "automatic_live_symbol_or_runtime_policy_promotion",
        "account_or_order_api",
        "real_order_submission",
        "token_issue_refresh_invalidation_or_replacement",
        "provider_bot_cap_threshold_or_broker_guard_change",
        "stop_loss_or_forced_exit_creation",
    ],
}

Sender = Callable[[str, str, str], None]
ConfigLoader = Callable[[], tuple[str, str]]


@dataclass(frozen=True)
class ResearchPolicy:
    scan_start: time
    scan_last_bar: time
    lookback_bars: int = 30
    rolling_high_drawdown_pct: float = 1.25
    rolling_low_proximity_pct: float = 0.20


@dataclass(frozen=True)
class ResearchProfile:
    profile_id: str
    symbol: str
    name: str
    session: str
    policy: ResearchPolicy


def _profiles() -> dict[str, ResearchProfile]:
    result: dict[str, ResearchProfile] = {}
    for symbol, name in CANDIDATE_SYMBOLS.items():
        for session, window in (
            ("midday", MIDDAY_WINDOW),
            ("afternoon", AFTERNOON_WINDOW),
        ):
            profile_id = f"candidate_{symbol}_{session}"
            result[profile_id] = ResearchProfile(
                profile_id=profile_id,
                symbol=symbol,
                name=name,
                session=session,
                policy=ResearchPolicy(window[0], window[1]),
            )
    return result


RESEARCH_PROFILES = _profiles()


def rolling_window_start(end_date: date) -> date:
    if not is_krx_trading_day(end_date):
        raise ValueError(f"target_date_not_krx_trading_day:{end_date}")
    current = end_date
    selected: list[date] = []
    while len(selected) < ROLLING_WINDOW_DAYS:
        if is_krx_trading_day(current):
            selected.append(current)
        current -= timedelta(days=1)
        if current < CLEAN_BASELINE_DATE - timedelta(days=1):
            raise ValueError("rolling_window_reaches_before_clean_baseline")
    return selected[-1]


def _previous_krx_trading_date(value: date) -> date:
    current = value - timedelta(days=1)
    while not is_krx_trading_day(current):
        current -= timedelta(days=1)
    return current


def _default_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if is_krx_trading_day(current.date()) and current.time().replace(
        tzinfo=None
    ) >= time(15, 30):
        return current.date()
    return _previous_krx_trading_date(current.date())


def _price_band(latest_close_price: int) -> str:
    if latest_close_price <= 50_000:
        return "under_50000_krw"
    if latest_close_price <= MAX_LATEST_CLOSE_PRICE:
        return "50000_to_100000_krw"
    return "above_100000_krw_excluded"


def _recommendation_rows(
    profiles: dict[str, dict[str, Any]], source_meta: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for profile_id, item in profiles.items():
        if item.get("decision") != "holdout_pass_source_only_early_candidate":
            continue
        meta = source_meta.get(str(item.get("symbol") or ""), {})
        latest_close = int(meta.get("latest_close_price", 0) or 0)
        if latest_close <= 0 or latest_close > MAX_LATEST_CLOSE_PRICE:
            continue
        holdout = (item.get("selected") or {}).get("holdout") or {}
        baseline_holdout = (item.get("baseline") or {}).get("holdout") or {}
        candidate_ev = float(holdout.get("notional_weighted_ev_pct") or 0.0)
        baseline_ev_raw = baseline_holdout.get("notional_weighted_ev_pct")
        baseline_ev = float(baseline_ev_raw) if baseline_ev_raw is not None else None
        rows.append(
            {
                "profile_id": profile_id,
                "symbol": item["symbol"],
                "name": item["name"],
                "session": item["session"],
                "latest_close_price": latest_close,
                "price_band": _price_band(latest_close),
                "recommended_spot": item["recommended_spot"],
                "holdout_signal_episodes": int(holdout.get("signal_episodes", 0) or 0),
                "holdout_completed_legs": int(holdout.get("completed_legs", 0) or 0),
                "holdout_held_legs": int(holdout.get("held_legs", 0) or 0),
                "notional_weighted_ev_pct": candidate_ev,
                "baseline_notional_weighted_ev_pct": baseline_ev,
                "ev_uplift_pct_point": (
                    round(candidate_ev - baseline_ev, 6)
                    if baseline_ev is not None
                    else None
                ),
                "implementation_status": "source_only_requires_review_and_user_approval",
                "runtime_effect": False,
            }
        )
    rows.sort(
        key=lambda row: (
            float(row["notional_weighted_ev_pct"]),
            int(row["holdout_completed_legs"]),
            -int(row["latest_close_price"]),
        ),
        reverse=True,
    )
    return rows


def build_report(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    if start_date < CLEAN_BASELINE_DATE or end_date < start_date:
        raise ValueError("research_window_outside_clean_baseline")
    if set(sources) != set(CANDIDATE_SYMBOLS):
        raise ResearchError("expanded_candidate_source_set_mismatch")
    contexts_by_symbol = {
        symbol: build_day_contexts(bars) for symbol, (bars, _) in sources.items()
    }
    date_sets = [tuple(sorted(contexts)) for contexts in contexts_by_symbol.values()]
    if not date_sets or any(dates != date_sets[0] for dates in date_sets[1:]):
        raise ResearchError("cross_symbol_trading_dates_mismatch")
    if (
        len(date_sets[0]) != ROLLING_WINDOW_DAYS
        or date_sets[0][0] != start_date
        or date_sets[0][-1] != end_date
    ):
        raise ResearchError("rolling_46_trading_date_window_mismatch")
    source_meta: dict[str, dict[str, Any]] = {}
    for symbol, (bars, raw_meta) in sources.items():
        if not bars or raw_meta.get("source_quality_status") != "PASS":
            raise ResearchError(f"{symbol}_source_quality_not_pass")
        meta = dict(raw_meta)
        meta["latest_close_price"] = int(bars[-1].close_price)
        meta["latest_price_band"] = _price_band(int(bars[-1].close_price))
        source_meta[symbol] = meta
    profiles = {
        profile_id: select_profile_spot(profile, contexts_by_symbol[profile.symbol])
        for profile_id, profile in RESEARCH_PROFILES.items()
    }
    recommendations = _recommendation_rows(profiles, source_meta)
    return {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "target_date": end_date.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "candidate_universe_source": "reviewed_lower_price_research_universe_v1",
        "candidate_universe_size": len(CANDIDATE_SYMBOLS),
        "source_meta": source_meta,
        "profiles": profiles,
        "recommendations": recommendations,
        "recommendation_count": len(recommendations),
        "status": (
            "recommendations_ready" if recommendations else "no_qualified_candidate"
        ),
        "decision": "expanded_candidates_source_only_no_runtime_promotion",
        "authority": AUTHORITY,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_source_quality_blocked_report(
    *, start_date: date, end_date: date, reason: str
) -> dict[str, Any]:
    return {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "target_date": end_date.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "candidate_universe_source": "reviewed_lower_price_research_universe_v1",
        "candidate_universe_size": len(CANDIDATE_SYMBOLS),
        "source_meta": {},
        "profiles": {},
        "recommendations": [],
        "recommendation_count": 0,
        "status": "source_quality_blocked",
        "source_quality_reasons": [str(reason)],
        "decision": "source_quality_blocked_no_recommendation",
        "authority": AUTHORITY,
        "recommendation_only": True,
        "machine_created": False,
        "service_started": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Expanded lower-price entry-spot research — {report['end_date']}",
        "",
        "Source-only rolling 30-day calibration / 16-day untouched holdout. No live symbol was added.",
        "",
        f"Recommendation status: `{report['status']}`; profiles: `{report['recommendation_count']}`.",
        "",
    ]
    if report["status"] == "source_quality_blocked":
        lines.extend(
            [
                "Source quality blocked recommendation generation:",
                *[f"- `{reason}`" for reason in report["source_quality_reasons"]],
                "",
            ]
        )
    lines.extend(
        [
            "| Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for item in report["profiles"].values():
        recommended = item["recommended_spot"]
        if recommended is None:
            spot = "N/A"
            holdout = item["baseline"]["holdout"]
            candidate_ev = None
        else:
            spot = (
                f"{recommended['scan_start']}~{recommended['scan_end']}; "
                f"L{recommended['lookback_bars']}; "
                f"DD{recommended['rolling_high_drawdown_pct']}; "
                f"NL{recommended['rolling_low_proximity_pct']}"
            )
            holdout = item["selected"]["holdout"]
            candidate_ev = holdout["notional_weighted_ev_pct"]
        baseline_ev = item["baseline"]["holdout"]["notional_weighted_ev_pct"]
        lines.append(
            f"| {item['symbol']} | {item['name']} | {item['session']} | "
            f"{item['decision']} | {spot} | {holdout['signal_episodes']} | "
            f"{holdout['completed_legs']} | {holdout['held_legs']} | "
            f"{candidate_ev} | {baseline_ev} |"
        )
    lines.extend(
        [
            "",
            "Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.",
            "",
        ]
    )
    return "\n".join(lines)


def build_telegram_message(report: dict[str, Any]) -> str:
    recommendations = list(report.get("recommendations") or [])
    unique_symbols = {str(row.get("symbol") or "") for row in recommendations}
    lines = [
        f"[장후 기계후보 추천] {report['target_date']}",
        f"분석기간: {report['start_date']}~{report['end_date']} (30일 보정+16일 OOS)",
        f"후보군: {report['candidate_universe_size']}종목 / 통과: {len(recommendations)}프로필·{len(unique_symbols)}종목",
    ]
    if report["status"] == "source_quality_blocked":
        reasons = ", ".join(str(item) for item in report["source_quality_reasons"])
        lines.append(f"분석 차단: {reasons}")
        lines.append("오늘은 source-quality 문제로 신규 추천을 산출하지 않았습니다.")
    elif not recommendations:
        lines.append("오늘 신규 구현 추천 기준을 통과한 종목·시간대가 없습니다.")
    for index, row in enumerate(recommendations[:MAX_RECOMMENDATIONS], start=1):
        spot = row["recommended_spot"]
        band = "5만원 이하" if row["price_band"] == "under_50000_krw" else "10만원 이하"
        lines.extend(
            [
                (
                    f"{index}. {row['name']}({row['symbol']}) {row['session']} "
                    f"{spot['scan_start']}~{spot['scan_end']}"
                ),
                (
                    f"   종가 {row['latest_close_price']:,}원({band}) / "
                    f"L{spot['lookback_bars']} DD{spot['rolling_high_drawdown_pct']} "
                    f"NL{spot['rolling_low_proximity_pct']}"
                ),
                (
                    f"   OOS {row['holdout_signal_episodes']}회·완료 {row['holdout_completed_legs']}leg / "
                    f"EV {row['notional_weighted_ev_pct']:+.4f}% / 보유 {row['holdout_held_legs']}"
                ),
            ]
        )
    if len(recommendations) > MAX_RECOMMENDATIONS:
        lines.append(
            f"외 {len(recommendations) - MAX_RECOMMENDATIONS}개 프로필은 보고서 참조"
        )
    lines.extend(
        [
            "판정: source-only 추천이며 자동 기계 구현·기동·실주문 권한 없음",
            "다음: 코드리뷰와 사용자 승인 후에만 별도 실기계 구현",
        ]
    )
    return "\n".join(lines)


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
        f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"
    )
    with request.urlopen(req, timeout=10) as response:
        raw_response = response.read()
    try:
        payload = json.loads(raw_response.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError("telegram_response_invalid") from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError("telegram_send_not_ok")


class CandidateRecommendationNotifier:
    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        enabled: bool | None = None,
        max_attempts: int = 3,
        retry_delay_sec: float = 2.0,
        sleeper: Callable[[float], None] = time_module.sleep,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.enabled = (
            str(os.getenv("KORSTOCKSCAN_LOW_PRICE_CANDIDATE_TELEGRAM_ENABLED", "true"))
            .strip()
            .lower()
            not in {"0", "false", "no", "off"}
            if enabled is None
            else bool(enabled)
        )
        self.max_attempts = max(1, int(max_attempts))
        self.retry_delay_sec = max(0.0, float(retry_delay_sec))
        self.sleeper = sleeper

    @staticmethod
    def _valid_report(report: dict[str, Any]) -> bool:
        recommendations = report.get("recommendations")
        basic_valid = bool(
            report.get("schema") == REPORT_SCHEMA
            and report.get("report_type") == REPORT_TYPE
            and report.get("status")
            in {
                "recommendations_ready",
                "no_qualified_candidate",
                "source_quality_blocked",
            }
            and report.get("metric_contract") == METRIC_CONTRACT
            and report.get("authority") == AUTHORITY
            and report.get("recommendation_only") is True
            and report.get("machine_created") is False
            and report.get("service_started") is False
            and report.get("runtime_effect") is False
            and report.get("allowed_runtime_apply") is False
            and report.get("actual_order_submitted") is False
            and report.get("broker_order_forbidden") is True
            and isinstance(recommendations, list)
            and report.get("candidate_universe_size") == len(CANDIDATE_SYMBOLS)
            and report.get("recommendation_count") == len(recommendations or [])
        )
        if not basic_valid:
            return False
        try:
            start_date = date.fromisoformat(str(report.get("start_date") or ""))
            end_date = date.fromisoformat(str(report.get("end_date") or ""))
            target_date = date.fromisoformat(str(report.get("target_date") or ""))
        except ValueError:
            return False
        if (
            end_date != target_date
            or start_date < CLEAN_BASELINE_DATE
            or not is_krx_trading_day(target_date)
        ):
            return False
        try:
            if start_date != rolling_window_start(end_date):
                return False
        except ValueError:
            return False
        if report.get("status") == "source_quality_blocked":
            return not recommendations and bool(report.get("source_quality_reasons"))
        if bool(recommendations) != (report.get("status") == "recommendations_ready"):
            return False
        profile_ids = [str(row.get("profile_id") or "") for row in recommendations]
        if len(profile_ids) != len(set(profile_ids)):
            return False
        return all(
            isinstance(row, dict)
            and row.get("profile_id") in RESEARCH_PROFILES
            and row.get("symbol")
            == RESEARCH_PROFILES[str(row.get("profile_id"))].symbol
            and row.get("session")
            == RESEARCH_PROFILES[str(row.get("profile_id"))].session
            and isinstance(row.get("recommended_spot"), dict)
            and 0 < int(row.get("latest_close_price", 0) or 0) <= MAX_LATEST_CLOSE_PRICE
            and row.get("price_band") in {"under_50000_krw", "50000_to_100000_krw"}
            and int(row.get("holdout_held_legs", -1)) == 0
            and float(row.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and row.get("implementation_status")
            == "source_only_requires_review_and_user_approval"
            and row.get("runtime_effect") is False
            for row in recommendations
        )

    def notify(self, report: dict[str, Any]) -> str:
        if not self.enabled:
            return "disabled"
        if not self._valid_report(report):
            return "invalid_report"
        target_date = str(report.get("target_date") or "")
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
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.sender(token, admin_id, build_telegram_message(report))
                break
            except Exception:
                if attempt >= self.max_attempts:
                    return "send_failed"
                self.sleeper(self.retry_delay_sec)
        try:
            _atomic_write(
                self.state_file,
                json.dumps(
                    {
                        "last_sent_target_date": target_date,
                        "authority": AUTHORITY,
                        "telegram_audience": "ADMIN_ONLY",
                        "runtime_effect": False,
                        "machine_created": False,
                        "service_started": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
            )
        except OSError:
            return "sent_state_persist_failed"
        return "sent"


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"low_price_two_leg_expanded_candidate_research_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else (
            date.fromisoformat(args.end_date)
            if args.end_date
            else _default_target_date()
        )
    )
    end_date = date.fromisoformat(args.end_date) if args.end_date else target_date
    if end_date != target_date:
        raise ValueError("end_date_must_equal_target_date")
    start_date = (
        date.fromisoformat(args.start_date)
        if args.start_date
        else rolling_window_start(end_date)
    )
    if args.notify and not args.write:
        raise ValueError("telegram_notification_requires_written_report")
    try:
        token = kiwoom_utils.get_cached_kiwoom_token()
        if not token:
            raise ResearchError("cached_token_missing_no_issue_or_refresh_allowed")
        allowlist = frozenset(CANDIDATE_SYMBOLS)
        sources = {
            symbol: fetch_sor_history(
                symbol=symbol,
                token=token,
                start_date=start_date,
                end_date=end_date,
                max_pages=args.max_pages,
                page_delay_sec=args.page_delay_sec,
                allowed_symbols=allowlist,
            )
            for symbol in CANDIDATE_SYMBOLS
        }
        report = build_report(sources=sources, start_date=start_date, end_date=end_date)
    except (ResearchError, requests.RequestException) as exc:
        report = build_source_quality_blocked_report(
            start_date=start_date, end_date=end_date, reason=str(exc)
        )
    report["telegram_status"] = "not_requested"
    paths = write_report(report, args.output_dir) if args.write else (None, None)
    if args.notify:
        report["telegram_status"] = CandidateRecommendationNotifier().notify(report)
        paths = write_report(report, args.output_dir)
        if report["telegram_status"] not in {
            "sent",
            "duplicate",
            "sent_state_persist_failed",
        }:
            raise RuntimeError(
                "candidate_recommendation_telegram_not_delivered:"
                f"{report['telegram_status']}"
            )
    if args.print_summary:
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "holdout_pass_profiles": [
                        profile_id
                        for profile_id, item in report["profiles"].items()
                        if item["decision"]
                        == "holdout_pass_source_only_early_candidate"
                    ],
                    "recommendation_count": report["recommendation_count"],
                    "telegram_status": report["telegram_status"],
                    "json_path": str(paths[0]) if paths[0] else None,
                    "markdown_path": str(paths[1]) if paths[1] else None,
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
