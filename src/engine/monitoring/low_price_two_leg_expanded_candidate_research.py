"""Walk-forward entry-spot research for additional lower-price symbols.

This source-only module deliberately keeps its candidate universe separate from
the live profile allowlist. It reuses the completed integrated-SOR minute-bar
research contract and cannot issue or refresh tokens, access accounts, submit
orders, or mutate runtime policy.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Any

from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    CLEAN_BASELINE_DATE,
    COST_PCT,
    DEFAULT_END_DATE,
    METRIC_CONTRACT,
    OFFICIAL_REFERENCE,
    Bar,
    ResearchError,
    _atomic_write,
    build_day_contexts,
    fetch_sor_history,
    select_profile_spot,
)
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

REPORT_SCHEMA = "low_price_two_leg_expanded_candidate_research_v1"
OUTPUT_DIR = DATA_DIR / "report" / "low_price_two_leg_expanded_candidate_research"
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


def build_report(
    *,
    sources: dict[str, tuple[list[Bar], dict[str, Any]]],
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    if start_date != CLEAN_BASELINE_DATE or end_date != DEFAULT_END_DATE:
        raise ValueError("research_window_must_match_clean_baseline_46_day_contract")
    if set(sources) != set(CANDIDATE_SYMBOLS):
        raise ResearchError("expanded_candidate_source_set_mismatch")
    contexts_by_symbol = {
        symbol: build_day_contexts(bars) for symbol, (bars, _) in sources.items()
    }
    date_sets = [tuple(sorted(contexts)) for contexts in contexts_by_symbol.values()]
    if not date_sets or any(dates != date_sets[0] for dates in date_sets[1:]):
        raise ResearchError("cross_symbol_trading_dates_mismatch")
    profiles = {
        profile_id: select_profile_spot(profile, contexts_by_symbol[profile.symbol])
        for profile_id, profile in RESEARCH_PROFILES.items()
    }
    return {
        "schema": REPORT_SCHEMA,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "cost_pct": COST_PCT,
        "official_reference": OFFICIAL_REFERENCE,
        "metric_contract": METRIC_CONTRACT,
        "candidate_universe_source": (
            "2026-08-10_lower_price_scan_non_live_symbols_below_100000_krw"
        ),
        "source_meta": {symbol: meta for symbol, (_, meta) in sources.items()},
        "profiles": profiles,
        "decision": "expanded_candidates_source_only_no_runtime_promotion",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Expanded lower-price entry-spot research — {report['end_date']}",
        "",
        "Source-only 30-day calibration / 16-day untouched holdout. No live symbol was added.",
        "",
        "| Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
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
    parser.add_argument("--start-date", default=CLEAN_BASELINE_DATE.isoformat())
    parser.add_argument("--end-date", default=DEFAULT_END_DATE.isoformat())
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--page-delay-sec", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
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
    paths = write_report(report, args.output_dir) if args.write else (None, None)
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
