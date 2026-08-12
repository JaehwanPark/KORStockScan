"""Read-only auxiliary market context for KRX widget advisory collectors.

This module owns only market-data observation.  It reuses the existing shared
Kiwoom token through the caller's read-only client and never issues tokens,
reads accounts, submits orders, or changes a trading runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.engine.monitoring.samsung_widget_advisory import (
    FLOW_STALE_SEC,
    ExternalMarketProvider,
    ExternalPoint,
    KiwoomReadOnlyClient,
    MinuteBar,
    YahooExternalMarketProvider,
    _age_external_points,
    _as_kst,
    _parse_flow,
    _same_window_relative_snapshot,
    completed_session_bars,
)
from src.engine.monitoring.samsung_widget_contract import KST, SessionContext

RELATIVE_MAX_AGE_SEC = 120
FOREIGN_DELAYED_ESTIMATE_MAX_AGE_SEC = 3600
EXTERNAL_THRESHOLDS = {"USDKRW": 0.25}


@dataclass(frozen=True)
class WidgetAuxiliaryProfile:
    symbol: str
    peer_symbol: str
    peer_name: str
    market_index_code: str
    market_index_name: str
    context_version: str


DOOSAN_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="034020",
    peer_symbol="267260",
    peer_name="HD현대일렉트릭",
    market_index_code="001",
    market_index_name="KOSPI_001",
    context_version="doosan_krx_auxiliary_context_v1",
)

HANWHA_OCEAN_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="042660",
    peer_symbol="010140",
    peer_name="삼성중공업",
    market_index_code="001",
    market_index_name="KOSPI_001",
    context_version="hanwha_ocean_krx_auxiliary_context_v1",
)

MIRAE_ASSET_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="006800",
    peer_symbol="005940",
    peer_name="NH투자증권",
    market_index_code="001",
    market_index_name="KOSPI_001",
    context_version="mirae_asset_krx_auxiliary_context_v1",
)

SAMSUNG_HEAVY_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="010140",
    peer_symbol="042660",
    peer_name="한화오션",
    market_index_code="001",
    market_index_name="KOSPI_001",
    context_version="samsung_heavy_krx_auxiliary_context_v1",
)

JEJU_SEMICONDUCTOR_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="080220",
    peer_symbol="000660",
    peer_name="SK하이닉스",
    market_index_code="101",
    market_index_name="KOSDAQ_101",
    context_version="jeju_semiconductor_krx_auxiliary_context_v1",
)

SK_ETERNIX_AUXILIARY_PROFILE = WidgetAuxiliaryProfile(
    symbol="475150",
    peer_symbol="322000",
    peer_name="HD현대에너지솔루션",
    market_index_code="001",
    market_index_name="KOSPI_001",
    context_version="sk_eternix_krx_auxiliary_context_v1",
)

WIDGET_SYMBOL_AUXILIARY_PROFILES = {
    profile.symbol: profile
    for profile in (
        MIRAE_ASSET_AUXILIARY_PROFILE,
        SAMSUNG_HEAVY_AUXILIARY_PROFILE,
        JEJU_SEMICONDUCTOR_AUXILIARY_PROFILE,
        SK_ETERNIX_AUXILIARY_PROFILE,
    )
}


def _session_return(bars: list[MinuteBar]) -> float | None:
    if not bars or bars[0].open <= 0:
        return None
    return round(((bars[-1].close - bars[0].open) / bars[0].open) * 100, 4)


def _bar_observed_at(bar: MinuteBar | None) -> datetime | None:
    if bar is None:
        return None
    try:
        return datetime.strptime(bar.source_time, "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except (TypeError, ValueError):
        return None


def _generic_aligned_windows(rows: object) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for horizon, row in rows.items():
        if not isinstance(row, dict):
            continue
        result[str(horizon)] = {
            "primary_return_pct": row.get("samsung_return_pct"),
            "comparison_return_pct": row.get("comparison_return_pct"),
            "relative_return_pct_point": row.get("relative_return_pct_point"),
            "window_start": row.get("window_start"),
            "window_end": row.get("window_end"),
        }
    return result


def _flow_component_status(flow: dict[str, Any], component: str) -> str:
    if flow.get(f"{component}_available") is not True:
        return "UNAVAILABLE"
    age = flow.get(f"{component}_source_age_sec")
    if not isinstance(age, (int, float)) or isinstance(age, bool):
        return "UNAVAILABLE"
    if age < 0:
        return "TIME_CONFLICT"
    if age <= FLOW_STALE_SEC:
        return "OBSERVED"
    if component == "foreign" and age <= FOREIGN_DELAYED_ESTIMATE_MAX_AGE_SEC:
        return "DELAYED_ESTIMATE"
    return "STALE"


def _combined_flow_status(foreign_status: str, program_status: str) -> str:
    statuses = {foreign_status, program_status}
    if statuses == {"OBSERVED"}:
        return "OBSERVED"
    if "OBSERVED" in statuses:
        return "OBSERVED_PARTIAL"
    if "DELAYED_ESTIMATE" in statuses:
        return "DELAYED_ESTIMATE"
    if "TIME_CONFLICT" in statuses:
        return "TIME_CONFLICT"
    if "STALE" in statuses:
        return "STALE"
    return "UNAVAILABLE"


def _neutral_relative_context(
    *,
    primary_bars: list[MinuteBar],
    observed_at: datetime,
    profile: WidgetAuxiliaryProfile,
    status: str,
) -> dict[str, Any]:
    primary_return = _session_return(primary_bars) or 0.0
    return {
        "samsung_change_pct": primary_return,
        "sk_hynix_change_pct": primary_return,
        "kospi_change_pct": primary_return,
        "primary_change_pct": primary_return,
        "peer_change_pct": None,
        "market_change_pct": None,
        "observed_at": _as_kst(observed_at).isoformat(),
        "authority": "unavailable_neutral_no_positive_or_negative_authority",
        "portable_schema_compatibility_only": True,
        "status": status,
        "primary_symbol": profile.symbol,
        "peer_symbol": profile.peer_symbol,
        "peer_name": profile.peer_name,
        "context_version": profile.context_version,
    }


class WidgetAuxiliaryContextCollector:
    """Collect aligned peer/KOSPI returns, KRX flow, and USD/KRW risk."""

    def __init__(
        self,
        profile: WidgetAuxiliaryProfile,
        *,
        external_provider: ExternalMarketProvider | None = None,
        flow_fetch_interval_sec: int = 60,
    ) -> None:
        self.profile = profile
        self.external_provider = (
            YahooExternalMarketProvider(
                tickers={"USDKRW": "KRW=X"},
                thread_name_prefix=f"{profile.symbol}-widget-yahoo",
            )
            if external_provider is None
            else external_provider
        )
        self.flow_fetch_interval_sec = max(60, int(flow_fetch_interval_sec))
        self.reset()

    def reset(self) -> None:
        self._peer_bars: list[MinuteBar] = []
        self._kospi_bars: list[MinuteBar] = []
        self._flow: dict[str, Any] = {
            "status": "UNAVAILABLE",
            "live_for_current_session": False,
            "foreign_nonworsening": False,
            "program_nonworsening": False,
        }
        self._external_points: dict[str, ExternalPoint] = {}
        self._last_relative_minute = ""
        self._last_flow_fetch = 0.0
        self._last_external_fetch = 0.0

    @staticmethod
    def _optional_post(
        client: KiwoomReadOnlyClient,
        path: str,
        api_id: str,
        payload: dict[str, str],
        gaps: list[dict[str, str]],
    ) -> dict[str, Any]:
        try:
            return client.post(path, api_id, payload, optional=True)
        except Exception as exc:
            gaps.append({"source": api_id, "error": type(exc).__name__})
            return {}

    def _relative_context(
        self,
        *,
        primary_bars: list[MinuteBar],
        observed_at: datetime,
    ) -> dict[str, Any]:
        latest_times = [
            _bar_observed_at(rows[-1] if rows else None)
            for rows in (primary_bars, self._peer_bars, self._kospi_bars)
        ]
        if any(value is None for value in latest_times):
            return _neutral_relative_context(
                primary_bars=primary_bars,
                observed_at=observed_at,
                profile=self.profile,
                status="UNAVAILABLE",
            )
        source_time = min(value for value in latest_times if value is not None)
        source_age_sec = (_as_kst(observed_at) - source_time).total_seconds()
        if source_age_sec < 0 or source_age_sec > RELATIVE_MAX_AGE_SEC:
            context = _neutral_relative_context(
                primary_bars=primary_bars,
                observed_at=observed_at,
                profile=self.profile,
                status="STALE",
            )
            context["source_observed_at"] = source_time.isoformat()
            context["source_age_sec"] = round(source_age_sec, 3)
            return context

        primary_return = _session_return(primary_bars)
        peer_return = _session_return(self._peer_bars)
        kospi_return = _session_return(self._kospi_bars)
        if None in {primary_return, peer_return, kospi_return}:
            return _neutral_relative_context(
                primary_bars=primary_bars,
                observed_at=observed_at,
                profile=self.profile,
                status="UNAVAILABLE",
            )
        aligned = _same_window_relative_snapshot(
            primary_bars, self._peer_bars, self._kospi_bars
        )
        aligned["same_window_aliases"] = {
            "samsung": self.profile.symbol,
            "sk_hynix": self.profile.peer_symbol,
            "kospi": self.profile.market_index_name,
        }
        aligned["same_window_generic"] = {
            "peer": _generic_aligned_windows(
                aligned["same_window"].get("sk_hynix", {})
            ),
            "market": _generic_aligned_windows(aligned["same_window"].get("kospi", {})),
        }
        aligned["same_window_sources_generic"] = {
            "primary": "kiwoom_ka10080_completed_1m",
            "peer": "kiwoom_ka10080_completed_1m",
            "market": "kiwoom_ka20005_completed_1m_index_x100",
        }
        return {
            "samsung_change_pct": primary_return,
            "sk_hynix_change_pct": peer_return,
            "kospi_change_pct": kospi_return,
            "primary_change_pct": primary_return,
            "peer_change_pct": peer_return,
            "market_change_pct": kospi_return,
            **aligned,
            "observed_at": _as_kst(observed_at).isoformat(),
            "source_observed_at": source_time.isoformat(),
            "source_age_sec": round(source_age_sec, 3),
            "authority": "observed_negative_veto_and_recovery_authority",
            "portable_schema_compatibility_only": False,
            "status": "OBSERVED",
            "primary_symbol": self.profile.symbol,
            "peer_symbol": self.profile.peer_symbol,
            "peer_name": self.profile.peer_name,
            "context_version": self.profile.context_version,
        }

    def collect(
        self,
        *,
        client: KiwoomReadOnlyClient,
        observed_at: datetime,
        context: SessionContext,
        primary_bars: list[MinuteBar],
        market_payload: dict[str, Any] | None = None,
        external_points: dict[str, ExternalPoint] | None = None,
        inherited_gaps: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        now = _as_kst(observed_at)
        gaps: list[dict[str, str]] = list(inherited_gaps or [])
        minute_key = now.strftime("%Y%m%d%H%M")
        if minute_key != self._last_relative_minute:
            peer_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10080",
                {
                    "stk_cd": self.profile.peer_symbol,
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
                gaps,
            )
            if market_payload is None:
                kospi_payload = self._optional_post(
                    client,
                    "/api/dostk/chart",
                    "ka20005",
                    {
                        "inds_cd": self.profile.market_index_code,
                        "tic_scope": "1",
                    },
                    gaps,
                )
            else:
                kospi_payload = market_payload
            peer_bars = completed_session_bars(
                peer_payload.get("stk_min_pole_chart_qry"),
                observed_at=now,
                session_start=context.start,
                session_end=context.end,
                limit=400,
            )
            kospi_bars = completed_session_bars(
                kospi_payload.get("inds_min_pole_qry"),
                observed_at=now,
                session_start=context.start,
                session_end=context.end,
                limit=400,
            )
            if peer_bars:
                self._peer_bars = peer_bars
            if kospi_bars:
                self._kospi_bars = kospi_bars
            self._last_relative_minute = minute_key

        epoch = now.timestamp()
        if (
            epoch - self._last_flow_fetch >= self.flow_fetch_interval_sec
            or not self._flow
        ):
            investor_payload = self._optional_post(
                client,
                "/api/dostk/chart",
                "ka10064",
                {
                    "mrkt_tp": "000",
                    "amt_qty_tp": "1",
                    "trde_tp": "0",
                    "stk_cd": self.profile.symbol,
                },
                gaps,
            )
            program_payload = self._optional_post(
                client,
                "/api/dostk/mrkcond",
                "ka90008",
                {
                    "amt_qty_tp": "1",
                    "stk_cd": self.profile.symbol,
                    "date": now.strftime("%Y%m%d"),
                },
                gaps,
            )
            self._flow = _parse_flow(
                investor_payload,
                program_payload,
                context=context,
                observed_at=now,
            )
            self._last_flow_fetch = epoch

        if external_points is not None:
            if external_points:
                self._external_points = external_points
            self._last_external_fetch = epoch
        elif epoch - self._last_external_fetch >= 60 or not self._external_points:
            try:
                external_points = self.external_provider.fetch(now)
            except Exception as exc:
                external_points = {}
                gaps.append({"source": "USDKRW", "error": type(exc).__name__})
            if external_points:
                self._external_points = external_points
            self._last_external_fetch = epoch

        relative = self._relative_context(
            primary_bars=primary_bars,
            observed_at=now,
        )
        aged_external_points = _age_external_points(self._external_points, now)
        external_point = aged_external_points.get("USDKRW")
        external_status = (
            "OBSERVED"
            if external_point is not None
            and external_point.quality in {"BEST_EFFORT_DELAYED", "MARKET_CLOSED"}
            else "LIMITED"
        )
        relative_status = str(relative.get("status") or "UNAVAILABLE")
        foreign_flow_status = _flow_component_status(self._flow, "foreign")
        program_flow_status = _flow_component_status(self._flow, "program")
        raw_flow_status = str(self._flow.get("status") or "UNAVAILABLE")
        flow_status = _combined_flow_status(foreign_flow_status, program_flow_status)
        positive_promotion_ready = bool(
            relative_status == "OBSERVED"
            and foreign_flow_status == "OBSERVED"
            and program_flow_status == "OBSERVED"
            and external_status == "OBSERVED"
        )
        negative_veto_ready = bool(
            relative_status == "OBSERVED"
            or foreign_flow_status == "OBSERVED"
            or program_flow_status == "OBSERVED"
        )
        auxiliary_status = (
            "OBSERVED"
            if positive_promotion_ready
            else (
                "OBSERVED_PARTIAL"
                if relative_status == "OBSERVED"
                and flow_status == "OBSERVED_PARTIAL"
                and external_status == "OBSERVED"
                else "LIMITED"
            )
        )
        return {
            "relative": relative,
            "flow": dict(self._flow),
            "external_points": aged_external_points,
            "external_thresholds": dict(EXTERNAL_THRESHOLDS),
            "summary": {
                "status": auxiliary_status,
                "relative_status": relative_status,
                "flow_status": flow_status,
                "raw_flow_status": raw_flow_status,
                "foreign_flow_status": foreign_flow_status,
                "program_flow_status": program_flow_status,
                "positive_promotion_ready": positive_promotion_ready,
                "negative_veto_ready": negative_veto_ready,
                "external_status": external_status,
                "primary_symbol": self.profile.symbol,
                "peer_symbol": self.profile.peer_symbol,
                "peer_name": self.profile.peer_name,
                "market_index": self.profile.market_index_name,
                "market_index_code": self.profile.market_index_code,
                "external_keys": ["USDKRW"],
                "context_version": self.profile.context_version,
                "optional_gaps": gaps,
                "authority": "widget_advisory_auxiliary_context_only",
                "runtime_effect": False,
            },
        }


def attach_auxiliary_summary(
    advisory: dict[str, Any], summary: dict[str, Any]
) -> dict[str, Any]:
    """Attach transparent auxiliary provenance without changing core quality."""
    attached_summary = dict(summary)
    relative_assessment = advisory.get("relative_assessment")
    relative_assessment = (
        relative_assessment if isinstance(relative_assessment, dict) else {}
    )
    if summary.get("relative_status") != "OBSERVED":
        relative_signal = "DATA_LIMITED"
    elif not relative_assessment:
        relative_signal = "NOT_EVALUATED"
    elif relative_assessment.get("same_window_negative_veto") or (
        relative_assessment.get("session_underperformance")
        and not relative_assessment.get("session_underperformance_cleared")
    ):
        relative_signal = "WEAK"
    else:
        relative_signal = "NOT_WEAK"
    flow = advisory.get("flow")
    flow = flow if isinstance(flow, dict) else {}
    if summary.get("flow_status") != "OBSERVED":
        if summary.get("program_flow_status") == "OBSERVED":
            foreign_suffix = (
                "FOREIGN_DELAYED"
                if summary.get("foreign_flow_status") == "DELAYED_ESTIMATE"
                else "FOREIGN_LIMITED"
            )
            flow_signal = (
                f"PROGRAM_NONWORSENING_{foreign_suffix}"
                if flow.get("program_nonworsening")
                else f"PROGRAM_DETERIORATING_{foreign_suffix}"
            )
        elif summary.get("foreign_flow_status") == "OBSERVED":
            flow_signal = (
                "FOREIGN_NONWORSENING_PROGRAM_LIMITED"
                if flow.get("foreign_nonworsening")
                else "FOREIGN_DETERIORATING_PROGRAM_LIMITED"
            )
        else:
            flow_signal = "DATA_LIMITED"
    elif flow.get("foreign_nonworsening") and flow.get("program_nonworsening"):
        flow_signal = "NONWORSENING"
    else:
        flow_signal = "DETERIORATING"
    external_risk = advisory.get("external_risk")
    external_risk = external_risk if isinstance(external_risk, dict) else {}
    attached_summary.update(
        {
            "relative_signal": relative_signal,
            "flow_signal": flow_signal,
            "external_risk_level": external_risk.get("level") or "DATA_LIMITED",
        }
    )
    advisory["auxiliary_context"] = attached_summary
    source_quality = advisory.setdefault("source_quality", {})
    source_quality["auxiliary_status"] = summary.get("status") or "LIMITED"
    reasons = [str(value) for value in advisory.get("reasons") or [] if value]
    unmet = [str(value) for value in advisory.get("unmet_conditions") or [] if value]
    if attached_summary.get("relative_status") != "OBSERVED":
        reasons = [value for value in reasons if value != "relative_strength_not_weak"]
        if "relative_strength_unavailable" not in unmet:
            unmet.append("relative_strength_unavailable")
    if attached_summary.get("flow_status") not in {
        "OBSERVED",
        "OBSERVED_PARTIAL",
    }:
        if "regular_flow_unavailable" not in unmet:
            unmet.append("regular_flow_unavailable")
    else:
        unmet = [value for value in unmet if value != "regular_flow_unavailable"]
        if (
            attached_summary.get("foreign_flow_status") == "DELAYED_ESTIMATE"
            and "foreign_flow_delayed_estimate" not in unmet
        ):
            unmet.append("foreign_flow_delayed_estimate")
    if attached_summary.get("external_status") != "OBSERVED":
        if "external_context_data_limited" not in unmet:
            unmet.append("external_context_data_limited")
    advisory["reasons"] = reasons
    advisory["unmet_conditions"] = unmet
    advisory.setdefault("provenance", {})["auxiliary_context_version"] = summary.get(
        "context_version"
    )
    return advisory
