"""Read-only KRX collector for postclose-promoted widget symbol policies."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, time as clock_time, timedelta
from pathlib import Path
from statistics import median
from typing import Any

import requests

from src.engine.monitoring.samsung_widget_advisory import (
    ExternalPoint,
    KiwoomReadOnlyClient,
    MinuteBar,
    ReadOnlyRequestBudget,
    YahooExternalMarketProvider,
    _as_kst,
    _parse_bbo,
    _positive_int,
    _relative_quality_assessment,
    completed_session_bars,
    evaluate_external_risk,
)
from src.engine.monitoring.samsung_widget_contract import ADVISORY_AUTHORITY, KST
from src.engine.monitoring.widget_symbol_runtime_contract import (
    CONTRACTS,
    DEFAULT_OBSERVATION_DIR,
    METRIC_CONTRACT,
    SNAPSHOT_SCHEMA_VERSION,
)
from src.engine.monitoring.widget_auxiliary_context import (
    WIDGET_SYMBOL_AUXILIARY_PROFILES,
    WidgetAuxiliaryContextCollector,
    attach_auxiliary_summary,
)
from src.engine.monitoring.widget_symbol_runtime_policy import (
    OFFICIAL_REFERENCE,
    POLICY_AUTHORITY,
    WidgetSymbolRuntimePolicyLoader,
)
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import (
    get_tick_size,
    move_price_by_ticks,
    move_price_up_by_bps,
)
from src.utils import kiwoom_utils

COLLECTION_START = clock_time(8, 57)
COLLECTION_END = clock_time(15, 31)
CACHE_BOUNDARY_REQUEST_CAPACITY = 52
REQUESTS_PER_MINUTE = 64

ENTRY_DIAGNOSTIC_METRIC_CONTRACT = {
    "metric_role": "widget_symbol_entry_first_blocker_instrumentation",
    "decision_authority": "instrumentation_only",
    "window_policy": "exact_policy_date_completed_krx_regular_1m",
    "sample_floor": "one_source_quality_pass_evaluation",
    "primary_decision_metric": "first_blocker",
    "source_quality_gate": ("same_symbol_fresh_quote_bbo_and_contiguous_completed_1m"),
    "forbidden_uses": [
        "automatic_order_authority",
        "same_day_threshold_mutation",
        "cross_symbol_policy_transfer",
        "broker_guard_bypass",
    ],
}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _clock(value: object) -> clock_time:
    return clock_time.fromisoformat(str(value))


def _bar_clock(bar: MinuteBar) -> clock_time:
    return datetime.strptime(bar.source_time[:12], "%Y%m%d%H%M").time()


def _bbo_age_sec(bbo: dict[str, Any]) -> float:
    try:
        value = float(bbo.get("age_sec"))
    except (TypeError, ValueError):
        return 999.0
    return value if value >= 0 else 999.0


def _bars_are_contiguous(rows: list[MinuteBar]) -> bool:
    if len(rows) < 2:
        return bool(rows)
    try:
        stamps = [datetime.strptime(row.source_time[:12], "%Y%m%d%H%M") for row in rows]
    except ValueError:
        return False
    return all(
        current - previous == timedelta(minutes=1)
        for previous, current in zip(stamps, stamps[1:])
    )


def _trend_not_down(rows: list[MinuteBar], end_index: int, horizon: int) -> bool:
    if end_index < horizon:
        return False
    window = rows[end_index - horizon : end_index + 1]
    if not _bars_are_contiguous(window):
        return False
    tick = get_tick_size(window[-1].close)
    net = window[-1].close - window[0].close
    deltas = [
        current.close - previous.close for previous, current in zip(window, window[1:])
    ]
    negative = sum(value < 0 for value in deltas)
    return not (net < -tick and negative >= max(2, horizon - 1))


def _setup_feature(
    rows: list[MinuteBar],
    index: int,
    lookback: int,
    *,
    anchor_mode: str = "rolling",
    minimum_history_bars: int | None = None,
) -> tuple[float, float] | None:
    minimum_history = (
        lookback if minimum_history_bars is None else int(minimum_history_bars)
    )
    if minimum_history < 2 or minimum_history > lookback or index + 1 < minimum_history:
        return None
    if anchor_mode == "session":
        window = rows[: index + 1]
    elif anchor_mode == "rolling":
        window = rows[max(0, index - lookback + 1) : index + 1]
    else:
        return None
    if not _bars_are_contiguous(window):
        return None
    high = max(row.high for row in window)
    low = min(row.low for row in window)
    close = rows[index].close
    if high <= 0 or close <= 0:
        return None
    drawdown = (high - close) / high * 100.0
    near_low = (close - low) / low * 100.0 if low > 0 else 999.0
    return drawdown, near_low


def _volume_state(rows: list[MinuteBar], index: int) -> tuple[str, float | None]:
    prior = [row.volume for row in rows[max(0, index - 5) : index] if row.volume > 0]
    if not prior:
        return "ENTRY_CAUTION", None
    ratio = rows[index].volume / median(prior)
    return ("ENTRY_READY" if ratio >= 1.0 else "ENTRY_CAUTION"), ratio


def _advance_support_break_count(episode: "EpisodeState", latest: MinuteBar) -> None:
    """Advance confirmation once per distinct completed bar, never per poll."""
    if latest.source_time == episode.last_exit_evaluated_bar:
        return
    episode.support_break_count = (
        episode.support_break_count + 1 if latest.close < episode.support else 0
    )
    episode.last_exit_evaluated_bar = latest.source_time


def _source_quality(
    *, latest: MinuteBar | None, bbo: dict[str, Any], observed_at: datetime
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if latest is None:
        reasons.append("completed_1m_missing")
    else:
        try:
            latest_at = datetime.strptime(
                latest.source_time[:12], "%Y%m%d%H%M"
            ).replace(tzinfo=KST)
        except ValueError:
            reasons.append("completed_1m_timestamp_invalid")
        else:
            age_sec = (observed_at - latest_at).total_seconds()
            if not 0 <= age_sec <= 120:
                reasons.append("completed_1m_stale")
    bid = _positive_int(bbo.get("best_bid"))
    ask = _positive_int(bbo.get("best_ask"))
    if bid is None or ask is None or ask < bid:
        reasons.append("bbo_invalid")
    if _bbo_age_sec(bbo) > 35.0:
        reasons.append("bbo_stale")
    return ("PASS" if not reasons else "BLOCKED", tuple(reasons))


@dataclass
class EpisodeState:
    trade_date: str = ""
    active: bool = False
    sequence: int = 0
    entry_bar: str = ""
    entry_price: int = 0
    support: int = 0
    target: int = 0
    peak: int = 0
    exit_bar: str = ""
    cooldown_until: datetime | None = None
    support_break_count: int = 0
    last_exit_evaluated_bar: str = ""

    def activate_date(self, observed_at: datetime) -> None:
        day = observed_at.date().isoformat()
        if day == self.trade_date:
            return
        self.__dict__.update(EpisodeState(trade_date=day).__dict__)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "active": self.active,
            "sequence": self.sequence,
            "entry_bar": self.entry_bar or None,
            "entry_price": self.entry_price or None,
            "structural_support": self.support or None,
            "target_price": self.target or None,
            "peak_price": self.peak or None,
            "exit_bar": self.exit_bar or None,
            "cooldown_until": (
                self.cooldown_until.isoformat() if self.cooldown_until else None
            ),
            "last_exit_evaluated_bar": self.last_exit_evaluated_bar or None,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }

    @classmethod
    def from_dict(cls, payload: object, *, trade_date: str) -> "EpisodeState":
        if not isinstance(payload, dict) or payload.get("trade_date") != trade_date:
            return cls(trade_date=trade_date)
        try:
            sequence = max(0, int(payload.get("sequence") or 0))
        except (TypeError, ValueError):
            return cls(trade_date=trade_date)
        cooldown = None
        if payload.get("cooldown_until"):
            try:
                parsed = datetime.fromisoformat(str(payload["cooldown_until"]))
                cooldown = _as_kst(parsed) if parsed.tzinfo is not None else None
            except ValueError:
                cooldown = None
        return cls(
            trade_date=trade_date,
            active=payload.get("active") is True,
            sequence=sequence,
            entry_bar=str(payload.get("entry_bar") or ""),
            entry_price=_positive_int(payload.get("entry_price")) or 0,
            support=_positive_int(payload.get("structural_support")) or 0,
            target=_positive_int(payload.get("target_price")) or 0,
            peak=_positive_int(payload.get("peak_price")) or 0,
            exit_bar=str(payload.get("exit_bar") or ""),
            cooldown_until=cooldown,
            last_exit_evaluated_bar=str(payload.get("last_exit_evaluated_bar") or ""),
        )


class WidgetSymbolRuntimeCollector:
    def __init__(
        self,
        *,
        policy_loader: WidgetSymbolRuntimePolicyLoader | None = None,
        request_session: requests.Session | None = None,
        observation_dir: Path = DEFAULT_OBSERVATION_DIR,
    ) -> None:
        self.policy_loader = policy_loader or WidgetSymbolRuntimePolicyLoader()
        self.request_session = request_session
        self.observation_dir = observation_dir
        # Four primary symbols, four peer charts, two shared index charts, and
        # four flow pairs produce a bounded 52-call rolling-minute overlap at
        # cache warm-up/boundaries. The steady-state rate is lower, but 36 let
        # a required primary chart fail before the oldest calls aged out. Keep
        # limited headroom without creating an unbounded retry surface.
        self.request_budget = ReadOnlyRequestBudget(
            max_requests_per_minute=REQUESTS_PER_MINUTE
        )
        self._active_date = ""
        self._policies: dict[str, dict[str, Any]] = {}
        self._minute_cache: dict[str, tuple[str, dict[str, Any]]] = {}
        self._bbo_cache: dict[str, tuple[str, dict[str, Any], datetime]] = {}
        self._quote_cache: dict[str, tuple[str, dict[str, Any], datetime]] = {}
        self._market_cache: dict[str, tuple[str, dict[str, Any]]] = {}
        self._external_points: dict[str, ExternalPoint] = {}
        self._last_external_fetch = 0.0
        self._external_provider = YahooExternalMarketProvider(
            tickers={"USDKRW": "KRW=X"},
            thread_name_prefix="widget-symbol-shared-yahoo",
        )
        self._auxiliary_collectors = {
            symbol: WidgetAuxiliaryContextCollector(
                profile,
                external_provider=self._external_provider,
                flow_fetch_interval_sec=120,
            )
            for symbol, profile in WIDGET_SYMBOL_AUXILIARY_PROFILES.items()
        }
        self._episodes: dict[str, EpisodeState] = {}
        self._last_record_key: dict[str, str] = {}
        self._symbol_cursor = 0

    def _activate_date(self, observed_at: datetime) -> None:
        day = observed_at.date().isoformat()
        if day == self._active_date:
            return
        self._active_date = day
        self._policies = self.policy_loader.resolve_observation_all(
            observed_date=observed_at.date()
        )
        self._minute_cache.clear()
        self._bbo_cache.clear()
        self._quote_cache.clear()
        self._market_cache.clear()
        self._external_points = {}
        self._last_external_fetch = 0.0
        for collector in self._auxiliary_collectors.values():
            collector.reset()
        self._episodes = {}
        for symbol, policy in self._policies.items():
            snapshot = CONTRACTS[symbol].load_snapshot()
            if snapshot.get("policy_id") == policy["policy_id"]:
                self._episodes[symbol] = EpisodeState.from_dict(
                    snapshot.get("episode"), trade_date=day
                )
            else:
                self._episodes[symbol] = EpisodeState(trade_date=day)
        self._last_record_key.clear()
        self._symbol_cursor = 0

    def _ordered_policy_items(self) -> list[tuple[str, dict[str, Any]]]:
        """Rotate the first symbol so a temporary defer cannot starve a tail."""
        items = sorted(self._policies.items())
        if not items:
            return []
        offset = self._symbol_cursor % len(items)
        self._symbol_cursor = (self._symbol_cursor + 1) % len(items)
        return items[offset:] + items[:offset]

    def _client(self) -> KiwoomReadOnlyClient:
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        if not token:
            raise RuntimeError("shared_cached_token_unavailable")
        return KiwoomReadOnlyClient(
            token,
            session=self.request_session,
            budget=self.request_budget,
        )

    def _bars(
        self,
        *,
        client: KiwoomReadOnlyClient,
        symbol: str,
        observed_at: datetime,
        context: Any,
    ) -> list[MinuteBar]:
        minute_key = observed_at.strftime("%Y%m%d%H%M")
        cached = self._minute_cache.get(symbol)
        if cached is None or cached[0] != minute_key:
            payload = client.post(
                "/api/dostk/chart",
                "ka10080",
                {"stk_cd": symbol, "tic_scope": "1", "upd_stkpc_tp": "1"},
            )
            self._minute_cache[symbol] = (minute_key, payload)
        return completed_session_bars(
            self._minute_cache[symbol][1].get("stk_min_pole_chart_qry"),
            observed_at=observed_at,
            session_start=context.start,
            session_end=context.end,
            limit=400,
        )

    def _quote(
        self,
        *,
        client: KiwoomReadOnlyClient,
        symbol: str,
        observed_at: datetime,
    ) -> tuple[dict[str, Any], float]:
        bucket = observed_at.strftime("%Y%m%d%H%M") + str(observed_at.second // 30)
        cached = self._quote_cache.get(symbol)
        if cached is None or cached[0] != bucket:
            payload = client.post("/api/dostk/stkinfo", "ka10001", {"stk_cd": symbol})
            self._quote_cache[symbol] = (bucket, payload, observed_at)
        cached = self._quote_cache[symbol]
        return dict(cached[1]), max(0.0, (observed_at - cached[2]).total_seconds())

    def _shared_market_payload(
        self,
        *,
        client: KiwoomReadOnlyClient,
        index_code: str,
        observed_at: datetime,
    ) -> tuple[dict[str, Any], list[dict[str, str]]]:
        minute_key = observed_at.strftime("%Y%m%d%H%M")
        cached = self._market_cache.get(index_code)
        if cached is not None and cached[0] == minute_key:
            return cached[1], []
        try:
            payload = client.post(
                "/api/dostk/chart",
                "ka20005",
                {"inds_cd": index_code, "tic_scope": "1"},
                optional=True,
            )
        except Exception as exc:
            return {}, [{"source": "ka20005", "error": type(exc).__name__}]
        self._market_cache[index_code] = (minute_key, payload)
        return payload, []

    def _shared_external_points(
        self, observed_at: datetime
    ) -> tuple[dict[str, ExternalPoint], list[dict[str, str]]]:
        epoch = observed_at.timestamp()
        if epoch - self._last_external_fetch < 60 and self._external_points:
            return self._external_points, []
        try:
            points = self._external_provider.fetch(observed_at)
        except Exception as exc:
            self._last_external_fetch = epoch
            return self._external_points, [
                {"source": "USDKRW", "error": type(exc).__name__}
            ]
        if points:
            self._external_points = points
        self._last_external_fetch = epoch
        return self._external_points, []

    def _bbo(
        self,
        *,
        client: KiwoomReadOnlyClient,
        symbol: str,
        observed_at: datetime,
    ) -> dict[str, Any]:
        bucket = observed_at.strftime("%Y%m%d%H%M") + str(observed_at.second // 30)
        cached = self._bbo_cache.get(symbol)
        if cached is None or cached[0] != bucket:
            raw = client.post("/api/dostk/mrkcond", "ka10004", {"stk_cd": symbol})
            received = observed_at
            self._bbo_cache[symbol] = (bucket, _parse_bbo(raw, received), received)
        bbo = dict(self._bbo_cache[symbol][1])
        bbo["age_sec"] = max(
            0.0, (observed_at - self._bbo_cache[symbol][2]).total_seconds()
        )
        return bbo

    @staticmethod
    def _entry_candidate(
        *,
        bars: list[MinuteBar],
        current_price: int,
        bbo: dict[str, Any],
        policy: dict[str, Any],
        episode: EpisodeState,
        observed_at: datetime,
    ) -> dict[str, Any] | None:
        candidate, _diagnostic = WidgetSymbolRuntimeCollector._entry_evaluation(
            bars=bars,
            current_price=current_price,
            bbo=bbo,
            policy=policy,
            episode=episode,
            observed_at=observed_at,
        )
        return candidate

    @staticmethod
    def _entry_evaluation(
        *,
        bars: list[MinuteBar],
        current_price: int,
        bbo: dict[str, Any],
        policy: dict[str, Any],
        episode: EpisodeState,
        observed_at: datetime,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        diagnostic: dict[str, Any] = {
            "first_blocker": None,
            "evaluated_at": observed_at.isoformat(),
            "best_observed_drawdown_pct": None,
            "best_observed_near_low_pct": None,
            "metric_contract": ENTRY_DIAGNOSTIC_METRIC_CONTRACT,
            "authority": "instrumentation_only",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }

        def blocked(reason: str) -> tuple[None, dict[str, Any]]:
            diagnostic["first_blocker"] = reason
            return None, diagnostic

        if episode.active or (
            episode.cooldown_until is not None and observed_at < episode.cooldown_until
        ):
            return blocked("episode_active_or_cooldown")
        signal = policy["signal_policy"]
        latest_index = len(bars) - 1
        lookback = int(signal["lookback_bars"])
        minimum_history = int(signal.get("minimum_history_bars", lookback))
        anchor_mode = str(signal.get("anchor_mode", "rolling"))
        max_reclaim_chase_ticks = int(signal.get("max_reclaim_chase_ticks", 2))
        diagnostic.update(
            {
                "anchor_mode": anchor_mode,
                "lookback_bars": lookback,
                "minimum_history_bars": minimum_history,
                "max_reclaim_chase_ticks": max_reclaim_chase_ticks,
            }
        )
        if latest_index + 1 < minimum_history:
            return blocked("history_below_policy_minimum")
        continuity_window = (
            bars
            if anchor_mode == "session"
            else bars[
                max(
                    0,
                    latest_index - lookback - int(signal["setup_valid_bars"]) + 1,
                ) :
            ]
        )
        if not _bars_are_contiguous(continuity_window):
            return blocked("completed_bar_continuity_gap")
        latest = bars[latest_index]
        if not (
            _clock(signal["segment_start_time"])
            <= _bar_clock(latest)
            < _clock(signal["segment_end_time"])
        ):
            return blocked("outside_policy_segment")
        ask = _positive_int(bbo.get("best_ask"))
        bid = _positive_int(bbo.get("best_bid"))
        if ask is None or bid is None or ask < bid:
            return blocked("bbo_invalid")
        tick = get_tick_size(max(current_price, ask))
        if ask - bid > tick * 2:
            return blocked("spread_above_two_ticks")
        if _bbo_age_sec(bbo) > 35.0:
            return blocked("bbo_stale")
        first_setup = max(
            minimum_history - 1,
            latest_index - int(signal["setup_valid_bars"]),
        )
        saw_drawdown = False
        saw_near_low = False
        saw_reclaim = False
        saw_non_down = False
        saw_non_chasing_price = False
        for setup_index in range(first_setup, latest_index):
            feature = _setup_feature(
                bars,
                setup_index,
                lookback,
                anchor_mode=anchor_mode,
                minimum_history_bars=minimum_history,
            )
            if feature is None:
                continue
            drawdown, near_low = feature
            diagnostic["best_observed_drawdown_pct"] = round(
                max(float(diagnostic["best_observed_drawdown_pct"] or 0.0), drawdown),
                6,
            )
            if drawdown + 1e-12 < float(signal["drawdown_pct"]):
                continue
            saw_drawdown = True
            current_best_near_low = diagnostic["best_observed_near_low_pct"]
            diagnostic["best_observed_near_low_pct"] = round(
                min(
                    (
                        float(current_best_near_low)
                        if current_best_near_low is not None
                        else near_low
                    ),
                    near_low,
                ),
                6,
            )
            if near_low - 1e-12 > float(signal["near_low_pct"]):
                continue
            saw_near_low = True
            setup = bars[setup_index]
            reclaim = move_price_by_ticks(setup.close, int(signal["reclaim_ticks"]))
            if not (latest.close >= reclaim and latest.close >= latest.open):
                continue
            saw_reclaim = True
            if not (
                _trend_not_down(bars, latest_index, 3)
                and _trend_not_down(bars, latest_index, 5)
            ):
                continue
            saw_non_down = True
            if current_price > move_price_by_ticks(reclaim, max_reclaim_chase_ticks):
                continue
            saw_non_chasing_price = True
            support = min(row.low for row in bars[setup_index : latest_index + 1])
            state, volume_ratio = _volume_state(bars, latest_index)
            entry_low = max(reclaim, bid)
            entry_high = min(ask, move_price_by_ticks(reclaim, max_reclaim_chase_ticks))
            if entry_low > entry_high:
                continue
            target = move_price_up_by_bps(entry_high, int(signal["target_bps"]))
            candidate = {
                "state": state,
                "entry_price_low": entry_low,
                "entry_price_high": entry_high,
                "structural_support": support,
                "target_price": target,
                "signal_bar": latest.source_time,
                "setup_bar": setup.source_time,
                "drawdown_pct": round(drawdown, 6),
                "near_low_pct": round(near_low, 6),
                "volume_ratio": (
                    round(volume_ratio, 6) if volume_ratio is not None else None
                ),
                "reclaim_price": reclaim,
            }
            diagnostic["candidate_state"] = candidate["state"]
            return candidate, diagnostic
        if not saw_drawdown:
            return blocked("drawdown_below_threshold")
        if not saw_near_low:
            return blocked("near_low_above_threshold")
        if not saw_reclaim:
            return blocked("reclaim_not_confirmed")
        if not saw_non_down:
            return blocked("three_or_five_minute_trend_down")
        if not saw_non_chasing_price:
            return blocked("reclaim_chase_guard")
        return blocked("entry_price_range_invalid")

    def _record(self, symbol: str, payload: dict[str, Any]) -> None:
        latest = payload.get("latest_completed_bar") or {}
        event = payload.get("entry_event") or payload.get("exit_event") or {}
        key = f"{latest.get('source_time')}:{event.get('event_id', '')}:{payload.get('status')}"
        if key == self._last_record_key.get(symbol):
            return
        self._last_record_key[symbol] = key
        self.observation_dir.mkdir(parents=True, exist_ok=True)
        path = (
            self.observation_dir
            / f"widget_symbol_advisory_{symbol}_{self._active_date.replace('-', '')}.jsonl"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def _degraded_symbol_payload(
        self,
        *,
        symbol: str,
        policy: dict[str, Any],
        observed_at: datetime,
        reason: str,
    ) -> dict[str, Any]:
        """Publish a fail-closed snapshot without terminating other symbols."""
        contract = CONTRACTS[symbol]
        episode = self._episodes[symbol]
        episode.activate_date(observed_at)
        payload = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "status": "data_wait",
            "symbol": symbol,
            "name": contract.name,
            "observed_at_kst": observed_at.isoformat(),
            "current_price": None,
            "market_venue": "KRX",
            "market_cohort": "KRX",
            "market_session": "krx_regular",
            "strategy_profile": contract.STRATEGY_PROFILE,
            "policy_id": policy["policy_id"],
            "policy_effective_date": policy.get("effective_date"),
            "official_reference": OFFICIAL_REFERENCE,
            "advisory": {
                "state": "DATA_WAIT",
                "session": "KRX_REGULAR",
                "observed_at": observed_at.isoformat(),
                "source_quality": {
                    "status": "BLOCKED",
                    "reasons": [reason],
                    "auxiliary_status": "LIMITED",
                },
                "unmet_conditions": [reason],
                "entry_diagnostic": {
                    "first_blocker": "source_quality_blocked",
                    "source_reason": reason,
                    "evaluated_at": observed_at.isoformat(),
                    "metric_contract": ENTRY_DIAGNOSTIC_METRIC_CONTRACT,
                    "authority": "instrumentation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                "metric_contract": METRIC_CONTRACT,
                "strategy_profile": contract.STRATEGY_PROFILE,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
            },
            "entry_event": None,
            "exit_event": None,
            "episode": episode.as_dict(),
            "latest_completed_bar": None,
            "bbo": {},
            "request_budget": self.request_budget.snapshot(),
            "token_mode": "shared_cache_only_no_issue_no_refresh",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        _atomic_write(contract.DEFAULT_SNAPSHOT_PATH, payload)
        self._record(symbol, payload)
        return payload

    @staticmethod
    def _collection_failure_reason(exc: BaseException) -> str:
        message = str(exc)
        if message == "widget_request_budget_exhausted":
            return "request_budget_deferred"
        if message == "widget_kiwoom_429_cooldown":
            return "kiwoom_rate_limit_cooldown"
        return f"read_only_source_error:{type(exc).__name__}"

    @staticmethod
    def _carry_event(
        payload: object, *, expected_type: str, observed_at: datetime
    ) -> dict[str, Any] | None:
        if not isinstance(payload, dict) or payload.get("event_type") != expected_type:
            return None
        try:
            valid_until = datetime.fromisoformat(str(payload.get("valid_until") or ""))
        except ValueError:
            return None
        if valid_until.tzinfo is None or _as_kst(valid_until) <= observed_at:
            return None
        return dict(payload)

    def _collect_symbol(
        self,
        *,
        symbol: str,
        policy: dict[str, Any],
        client: KiwoomReadOnlyClient,
        observed_at: datetime,
    ) -> dict[str, Any]:
        contract = CONTRACTS[symbol]
        context = contract.session_context(observed_at)
        episode = self._episodes[symbol]
        episode.activate_date(observed_at)
        if not context.active:
            payload = {
                "schema_version": SNAPSHOT_SCHEMA_VERSION,
                "status": "closed",
                "symbol": symbol,
                "name": contract.name,
                "observed_at_kst": observed_at.isoformat(),
                "market_venue": "KRX",
                "market_cohort": "KRX",
                "strategy_profile": contract.STRATEGY_PROFILE,
                "policy_id": policy["policy_id"],
                "official_reference": OFFICIAL_REFERENCE,
                "entry_event": None,
                "exit_event": None,
                "episode": episode.as_dict(),
                "token_mode": "shared_cache_only_no_issue_no_refresh",
            }
            _atomic_write(contract.DEFAULT_SNAPSHOT_PATH, payload)
            return payload
        quote, quote_age_sec = self._quote(
            client=client, symbol=symbol, observed_at=observed_at
        )
        current_price = _positive_int(quote.get("cur_prc"))
        if current_price is None:
            raise RuntimeError(f"{symbol}_quote_price_missing")
        bbo = self._bbo(client=client, symbol=symbol, observed_at=observed_at)
        bars = self._bars(
            client=client,
            symbol=symbol,
            observed_at=observed_at,
            context=context,
        )
        latest = bars[-1] if bars else None
        source_quality, source_quality_reasons = _source_quality(
            latest=latest, bbo=bbo, observed_at=observed_at
        )
        auxiliary_collector = self._auxiliary_collectors[symbol]
        profile = WIDGET_SYMBOL_AUXILIARY_PROFILES[symbol]
        market_payload, market_gaps = self._shared_market_payload(
            client=client,
            index_code=profile.market_index_code,
            observed_at=observed_at,
        )
        external_points, external_gaps = self._shared_external_points(observed_at)
        auxiliary = auxiliary_collector.collect(
            client=client,
            observed_at=observed_at,
            context=context,
            primary_bars=bars,
            market_payload=market_payload,
            external_points=external_points,
            inherited_gaps=[*market_gaps, *external_gaps],
        )
        _relative_ok, _relative_issues, relative_assessment = (
            _relative_quality_assessment(auxiliary["relative"], context)
        )
        external_risk = evaluate_external_risk(
            auxiliary["external_points"],
            thresholds=auxiliary["external_thresholds"],
        )
        auxiliary_advisory = attach_auxiliary_summary(
            {
                "reasons": [],
                "unmet_conditions": [],
                "source_quality": {"status": source_quality, "issues": []},
                "provenance": {},
                "flow": auxiliary["flow"],
                "relative_assessment": relative_assessment,
                "external_risk": external_risk,
            },
            auxiliary["summary"],
        )
        previous_snapshot = contract.load_snapshot()
        same_policy_snapshot = previous_snapshot.get("policy_id") == policy["policy_id"]
        entry_event = (
            self._carry_event(
                previous_snapshot.get("entry_event"),
                expected_type="ENTRY",
                observed_at=observed_at,
            )
            if same_policy_snapshot and source_quality == "PASS"
            else None
        )
        exit_event = (
            self._carry_event(
                previous_snapshot.get("exit_event"),
                expected_type="EXIT",
                observed_at=observed_at,
            )
            if same_policy_snapshot and source_quality == "PASS"
            else None
        )
        candidate, entry_diagnostic = (
            self._entry_evaluation(
                bars=bars,
                current_price=current_price,
                bbo=bbo,
                policy=policy,
                episode=episode,
                observed_at=observed_at,
            )
            if source_quality == "PASS"
            else (
                None,
                {
                    "first_blocker": "source_quality_blocked",
                    "evaluated_at": observed_at.isoformat(),
                    "metric_contract": ENTRY_DIAGNOSTIC_METRIC_CONTRACT,
                    "authority": "instrumentation_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        )
        if candidate is not None and candidate["signal_bar"] != episode.entry_bar:
            episode.sequence += 1
            episode.active = True
            episode.entry_bar = str(candidate["signal_bar"])
            episode.entry_price = int(candidate["entry_price_high"])
            episode.support = int(candidate["structural_support"])
            episode.target = int(candidate["target_price"])
            episode.peak = current_price
            episode.support_break_count = 0
            episode.last_exit_evaluated_bar = ""
            valid_until = observed_at + timedelta(seconds=75)
            entry_event = {
                "event_id": f"{symbol}:{observed_at.date().isoformat()}:ENTRY:{episode.sequence:02d}:{candidate['signal_bar']}",
                "event_type": "ENTRY",
                "status": "ACTIVE",
                "state": candidate["state"],
                "entry_price_low": candidate["entry_price_low"],
                "entry_price_high": candidate["entry_price_high"],
                "structural_support": candidate["structural_support"],
                "target_price": candidate["target_price"],
                "observed_at": observed_at.isoformat(),
                "valid_until": valid_until.isoformat(),
                "source_quality_status": "PASS",
                "strategy_profile": contract.STRATEGY_PROFILE,
                "policy_id": policy["policy_id"],
                "policy_authority": POLICY_AUTHORITY,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "features": candidate,
            }
        if episode.active and latest is not None:
            episode.peak = max(episode.peak, current_price)
            _advance_support_break_count(episode, latest)
            reason = None
            if current_price >= episode.target:
                reason = "target_observed"
            elif episode.support_break_count >= 2 and not _trend_not_down(
                bars, len(bars) - 1, 3
            ):
                reason = "confirmed_support_break"
            if reason:
                episode.active = False
                episode.exit_bar = latest.source_time
                episode.cooldown_until = observed_at + timedelta(
                    minutes=int(policy["signal_policy"]["reentry_cooldown_bars"])
                )
                entry_event = None
                exit_event = {
                    "event_id": f"{symbol}:{observed_at.date().isoformat()}:EXIT:{episode.sequence:02d}:{latest.source_time}",
                    "event_type": "EXIT",
                    "reason": reason,
                    "reference_exit_price": _positive_int(bbo.get("best_bid"))
                    or current_price,
                    "observed_at": observed_at.isoformat(),
                    "valid_until": (observed_at + timedelta(seconds=75)).isoformat(),
                    "source_quality_status": "PASS",
                    "strategy_profile": contract.STRATEGY_PROFILE,
                    "policy_id": policy["policy_id"],
                    "policy_authority": POLICY_AUTHORITY,
                    "authority": ADVISORY_AUTHORITY,
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
        payload = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "status": "ok" if source_quality == "PASS" else "data_wait",
            "symbol": symbol,
            "name": contract.name,
            "observed_at_kst": observed_at.isoformat(),
            "current_price": current_price,
            "market_venue": "KRX",
            "market_cohort": "KRX",
            "market_session": "krx_regular",
            "strategy_profile": contract.STRATEGY_PROFILE,
            "policy_id": policy["policy_id"],
            "policy_effective_date": policy["effective_date"],
            "official_reference": OFFICIAL_REFERENCE,
            "advisory": {
                "state": candidate["state"] if candidate else "WATCH",
                "session": "KRX_REGULAR",
                "observed_at": observed_at.isoformat(),
                "source_quality": {
                    "status": source_quality,
                    "reasons": list(source_quality_reasons),
                    "auxiliary_status": auxiliary["summary"]["status"],
                },
                "auxiliary_context": auxiliary_advisory["auxiliary_context"],
                "auxiliary_unmet_conditions": auxiliary_advisory["unmet_conditions"],
                "auxiliary_decision_authority": (
                    "observation_only_no_entry_veto_or_positive_promotion"
                ),
                "metric_contract": METRIC_CONTRACT,
                "strategy_profile": contract.STRATEGY_PROFILE,
                "entry_diagnostic": entry_diagnostic,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
            },
            "entry_event": entry_event,
            "exit_event": exit_event,
            "episode": episode.as_dict(),
            "latest_completed_bar": (
                {
                    "source_time": latest.source_time,
                    "open": latest.open,
                    "high": latest.high,
                    "low": latest.low,
                    "close": latest.close,
                    "volume": latest.volume,
                }
                if latest
                else None
            ),
            "bbo": bbo,
            "quote_provenance": {
                "source": "kiwoom_ka10001_response_received_time",
                "age_sec": round(quote_age_sec, 3),
            },
            "relative_strength": auxiliary["relative"],
            "flow": auxiliary["flow"],
            "external_points": {
                key: asdict(point)
                for key, point in auxiliary["external_points"].items()
            },
            "external_risk": external_risk,
            "token_mode": "shared_cache_only_no_issue_no_refresh",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        _atomic_write(contract.DEFAULT_SNAPSHOT_PATH, payload)
        self._record(symbol, payload)
        return payload

    def collect_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        now = _as_kst(observed_at or datetime.now(KST))
        self._activate_date(now)
        if not self._policies:
            return {"status": "no_active_exact_date_policy", "symbols": {}}
        client = self._client()
        results: dict[str, dict[str, Any]] = {}
        failures: dict[str, str] = {}
        for symbol, policy in self._ordered_policy_items():
            try:
                results[symbol] = self._collect_symbol(
                    symbol=symbol,
                    policy=policy,
                    client=client,
                    observed_at=now,
                )
            except (RuntimeError, requests.RequestException) as exc:
                reason = self._collection_failure_reason(exc)
                failures[symbol] = reason
                results[symbol] = self._degraded_symbol_payload(
                    symbol=symbol,
                    policy=policy,
                    observed_at=now,
                    reason=reason,
                )
        return {
            "status": "partial_data_wait" if failures else "ok",
            "symbols": results,
            "failures": failures,
            "request_budget": self.request_budget.snapshot(),
        }

    def run_forever(self, *, interval_sec: float = 15.0) -> None:
        interval = max(10.0, float(interval_sec))
        while True:
            now = datetime.now(KST)
            if now.time() >= COLLECTION_END:
                return
            if now.time() < COLLECTION_START:
                time.sleep(min(interval, 30.0))
                continue
            started = time.monotonic()
            self.collect_once(now)
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=15.0)
    args = parser.parse_args(argv)
    collector = WidgetSymbolRuntimeCollector()
    if args.once:
        result = collector.collect_once()
        print(
            json.dumps(
                {"status": result["status"], "symbols": sorted(result["symbols"])},
                ensure_ascii=False,
            )
        )
        return 0
    collector.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
