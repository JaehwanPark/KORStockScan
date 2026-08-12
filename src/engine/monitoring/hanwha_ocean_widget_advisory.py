"""Read-only Hanwha Ocean KRX intraday advisory collector.

The strategy is deliberately isolated from the trading runtime.  It reuses the
portable deterministic widget structure detector, then applies a Hanwha-Ocean-
only VWAP first-pullback profile. It consumes only the existing Kiwoom token
cache and never issues tokens, reads accounts, or submits orders.
"""

from __future__ import annotations

import argparse
import time
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from src.engine.monitoring import hanwha_ocean_widget_contract as contract
from src.engine.monitoring.hanwha_ocean_widget_telegram_notify import (
    HanwhaOceanWidgetTelegramNotifier,
)
from src.engine.monitoring.samsung_widget_advisory import (
    AdvisoryBreakRearmFilter,
    AdvisoryPromotionFilter,
    AdvisoryRecoveryEpisodeFilter,
    ExternalMarketProvider,
    KiwoomReadOnlyClient,
    MinuteBar,
    ObservationRecorder,
    ReadOnlyRequestBudget,
    _as_kst,
    _atomic_write_json,
    _current_daily_anchor,
    _parse_bbo,
    _positive_int,
    _source_quality,
    _trend_assessment,
    analyze_trends,
    completed_session_bars,
    evaluate_advisory,
)
from src.engine.monitoring.samsung_widget_contract import (
    ADVISORY_AUTHORITY,
    KRX_END,
    KST,
    snapshot_observed_at,
)
from src.engine.monitoring.widget_advisory_calibration_policy import (
    WidgetCalibrationPolicyLoader,
)
from src.engine.monitoring.widget_auxiliary_context import (
    HANWHA_OCEAN_AUXILIARY_PROFILE,
    WidgetAuxiliaryContextCollector,
    attach_auxiliary_summary,
)
from src.engine.sniper_config import CONF
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks
from src.utils import kiwoom_utils

ACTIONABLE_ENTRY_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
DETERIORATING_FLOW_SIGNALS = frozenset(
    {
        "DETERIORATING",
        "PROGRAM_DETERIORATING_FOREIGN_DELAYED",
        "PROGRAM_DETERIORATING_FOREIGN_LIMITED",
        "FOREIGN_DETERIORATING_PROGRAM_LIMITED",
    }
)


def _now_kst() -> datetime:
    return datetime.now(KST)


def _append_unique(values: object, value: str) -> list[str]:
    result = [str(item) for item in values if item] if isinstance(values, list) else []
    if value not in result:
        result.append(value)
    return result


def apply_hanwha_ocean_entry_policy(
    advisory: dict[str, Any],
    *,
    current_price: int,
    bars: list[MinuteBar],
    context,
) -> dict[str, Any]:
    """Apply the Hanwha Ocean VWAP first-pullback policy before promotion."""
    result = deepcopy(advisory)
    derived = result.setdefault("derived", {})
    session_open = bars[0].open if bars else None
    session_return_pct = (
        round(((current_price - session_open) / session_open) * 100, 4)
        if session_open
        else None
    )
    volume_mode = str(derived.get("volume_confirmation_mode") or "unconfirmed")
    support_confirmation = str(derived.get("support_confirmation") or "unconfirmed")
    retest_held = derived.get("retest_held") is True
    retest_rebound_confirmed = derived.get("retest_rebound_confirmed") is True
    vwap_reclaimed = derived.get("vwap_reclaimed") is True
    resistance_reclaimed = derived.get("recent_resistance_reclaimed") is True
    first_pullback_confirmed = support_confirmation in {
        "retest_held",
        "higher_high_and_low",
    }
    high_confidence_structure = bool(
        retest_held
        and retest_rebound_confirmed
        and vwap_reclaimed
        and resistance_reclaimed
        and volume_mode == "standard_rebound"
    )
    base_state = str(result.get("raw_state") or result.get("state") or "DATA_WAIT")
    auxiliary_context = result.get("auxiliary_context")
    auxiliary_context = auxiliary_context if isinstance(auxiliary_context, dict) else {}
    flow_signal = str(auxiliary_context.get("flow_signal") or "DATA_LIMITED")
    deteriorating_flow_observed = flow_signal in DETERIORATING_FLOW_SIGNALS
    auxiliary_high_ready = bool(
        auxiliary_context.get("status") == "OBSERVED"
        and auxiliary_context.get("positive_promotion_ready") is True
        and base_state == "ENTRY_READY"
    )
    tier = "HIGH" if high_confidence_structure and auxiliary_high_ready else "STANDARD"
    policy = {
        "strategy_profile": contract.STRATEGY_PROFILE,
        "session_scope": "KRX_REGULAR_ONLY",
        "session_open": session_open,
        "session_return_pct": session_return_pct,
        "session_return_authority": "diagnostic_only_no_fixed_return_gate",
        "required_structure_confirmation": "retest_held_or_higher_high_and_low",
        "observed_structure_confirmation": support_confirmation,
        "required_reclaim": "vwap_or_recent_resistance",
        "vwap_reclaimed": vwap_reclaimed,
        "recent_resistance_reclaimed": resistance_reclaimed,
        "retest_held": retest_held,
        "retest_rebound_confirmed": retest_rebound_confirmed,
        "required_volume_confirmation_mode": "standard_rebound",
        "observed_volume_confirmation_mode": volume_mode,
        "price_structure_tier": "HIGH" if high_confidence_structure else "STANDARD",
        "signal_tier": tier,
        "relative_context_authority": "observed_negative_veto_and_recovery",
        "external_context_authority": "negative_risk_only_no_positive_promotion",
        "auxiliary_context_status": auxiliary_context.get("status") or "LIMITED",
        "auxiliary_high_ready": auxiliary_high_ready,
        "flow_signal": flow_signal,
        "deteriorating_flow_observed": deteriorating_flow_observed,
        "deteriorating_flow_resistance_reclaim_required": True,
        "episode_policy": contract.EPISODE_POLICY,
    }
    result["strategy_profile"] = contract.STRATEGY_PROFILE
    result["signal_tier"] = tier
    result["hanwha_ocean_policy"] = policy
    derived["hanwha_ocean_policy"] = policy
    result["metric_contract"] = contract.METRIC_CONTRACT
    result.setdefault("provenance", {}).update(
        {
            "symbol": contract.HANWHA_OCEAN_CODE,
            "strategy_profile": contract.STRATEGY_PROFILE,
            "relative_context": "peer_kospi_observed_or_neutral_limited",
            "external_context": "usdkrw_best_effort_negative_risk_only",
            "kiwoom_official_reference": contract.KIWOOM_OFFICIAL_REFERENCE,
        }
    )

    raw_state = base_state
    if context.name != "KRX_REGULAR" or not context.active:
        return result
    if raw_state not in ACTIONABLE_ENTRY_STATES:
        return result
    if not first_pullback_confirmed or not (vwap_reclaimed or resistance_reclaimed):
        result["state"] = result["raw_state"] = "WATCH"
        result["entry_price_low"] = None
        result["entry_price_high"] = None
        result["unmet_conditions"] = _append_unique(
            result.get("unmet_conditions"),
            "hanwha_ocean_first_pullback_reclaim_pending",
        )
        return result
    if volume_mode != "standard_rebound":
        result["state"] = result["raw_state"] = "WATCH"
        result["entry_price_low"] = None
        result["entry_price_high"] = None
        result["unmet_conditions"] = _append_unique(
            result.get("unmet_conditions"),
            "hanwha_ocean_standard_rebound_volume_required",
        )
        return result
    if deteriorating_flow_observed and not resistance_reclaimed:
        result["state"] = result["raw_state"] = "WATCH"
        result["entry_price_low"] = None
        result["entry_price_high"] = None
        policy["flow_resistance_guard_blocked"] = True
        result["unmet_conditions"] = _append_unique(
            result.get("unmet_conditions"),
            "hanwha_ocean_deteriorating_flow_requires_resistance_reclaim",
        )
        return result
    policy["flow_resistance_guard_blocked"] = False

    result["reasons"] = _append_unique(
        result.get("reasons"), "hanwha_ocean_vwap_first_pullback_profile"
    )
    result["reasons"] = _append_unique(
        result.get("reasons"), "hanwha_ocean_standard_rebound_volume"
    )
    base_caution_must_remain = bool(
        raw_state != "ENTRY_READY"
        or not auxiliary_high_ready
        or not resistance_reclaimed
        or (
            derived.get("recent_resistance_reclaimed") is True
            and derived.get("vwap_reclaimed") is not True
        )
        or isinstance(derived.get("recovery_episode"), dict)
    )
    policy["base_caution_preserved"] = base_caution_must_remain
    if not resistance_reclaimed:
        result["unmet_conditions"] = _append_unique(
            result.get("unmet_conditions"),
            "hanwha_ocean_recent_resistance_reclaim_required_for_high",
        )
    if high_confidence_structure and not auxiliary_high_ready:
        result["unmet_conditions"] = _append_unique(
            result.get("unmet_conditions"), "auxiliary_context_not_ready_for_high"
        )
    if high_confidence_structure and not base_caution_must_remain:
        result["reasons"] = _append_unique(
            result.get("reasons"), "hanwha_ocean_retest_vwap_high_confidence"
        )
        result["state"] = result["raw_state"] = "ENTRY_READY"
    else:
        result["state"] = result["raw_state"] = "ENTRY_CAUTION"
    return result


def _ceil_to_tick(price: float) -> int:
    floored = clamp_price_to_tick(price)
    return floored if floored >= price else move_price_by_ticks(floored, 1)


class HanwhaOceanDailyEpisodeTracker:
    """Own non-overlapping, rearmed entry/exit episodes within one trade date."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.scope_date = ""
        self.daily_entry_count = 0
        self.entry_issued = False
        self.active = False
        self.completed = False
        self.rearm_required = False
        self.rearm_after_bar = ""
        self.entry_reference_price: int | None = None
        self.structural_support: int | None = None
        self.target_price: int | None = None
        self.entry_observed_at = ""
        self.entry_last_completed_bar = ""
        self.peak_price: int | None = None
        self.entry_event: dict[str, Any] | None = None
        self.exit_event: dict[str, Any] | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "scope_date": self.scope_date or None,
            "episode_policy": contract.EPISODE_POLICY,
            "daily_entry_count": self.daily_entry_count,
            "entry_issued": self.entry_issued,
            "active": self.active,
            "completed": self.completed,
            "rearm_required": self.rearm_required,
            "rearm_after_bar": self.rearm_after_bar or None,
            "entry_reference_price": self.entry_reference_price,
            "structural_support": self.structural_support,
            "target_price": self.target_price,
            "entry_observed_at": self.entry_observed_at or None,
            "entry_last_completed_bar": self.entry_last_completed_bar or None,
            "peak_price": self.peak_price,
            "entry_event": self.entry_event,
            "exit_event": self.exit_event,
            "strategy_profile": contract.STRATEGY_PROFILE,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }

    def restore(self, value: object, *, observed_at: datetime) -> bool:
        if not isinstance(value, dict):
            return False
        today = _as_kst(observed_at).date().isoformat()
        if (
            value.get("scope_date") != today
            or value.get("strategy_profile") != contract.STRATEGY_PROFILE
            or value.get("authority") != ADVISORY_AUTHORITY
            or value.get("runtime_effect") is not False
            or value.get("actual_order_submitted") is not False
            or value.get("broker_order_forbidden") is not True
        ):
            return False
        try:
            entry_reference = int(value.get("entry_reference_price") or 0) or None
            structural_support = int(value.get("structural_support") or 0) or None
            target_price = int(value.get("target_price") or 0) or None
            peak_price = int(value.get("peak_price") or 0) or None
        except (TypeError, ValueError):
            return False
        if (
            "episode_policy" in value
            and value.get("episode_policy") != contract.EPISODE_POLICY
        ):
            return False
        entry_issued = value.get("entry_issued") is True
        active = value.get("active") is True
        completed = value.get("completed") is True
        raw_daily_entry_count = value.get("daily_entry_count")
        if raw_daily_entry_count is None:
            daily_entry_count = 1 if entry_issued else 0
        elif isinstance(raw_daily_entry_count, int) and not isinstance(
            raw_daily_entry_count, bool
        ):
            daily_entry_count = raw_daily_entry_count
        elif isinstance(raw_daily_entry_count, str) and raw_daily_entry_count.isdigit():
            daily_entry_count = int(raw_daily_entry_count)
        else:
            return False
        if daily_entry_count < 0 or (entry_issued and daily_entry_count < 1):
            return False
        if "rearm_required" in value and not isinstance(
            value.get("rearm_required"), bool
        ):
            return False
        rearm_required = (
            completed if "rearm_required" not in value else value["rearm_required"]
        )
        raw_rearm_after_bar = value.get("rearm_after_bar")
        if raw_rearm_after_bar is not None and not isinstance(raw_rearm_after_bar, str):
            return False
        rearm_after_bar = raw_rearm_after_bar or ""
        if entry_issued and active == completed:
            return False
        if completed != rearm_required:
            return False
        if active and (
            not entry_issued
            or completed
            or rearm_required
            or not all((entry_reference, structural_support, target_price))
        ):
            return False
        if rearm_required and (not entry_issued or not completed or active):
            return False
        entry_event = value.get("entry_event")
        exit_event = value.get("exit_event")
        if isinstance(entry_event, dict) and "episode_sequence" in entry_event:
            if _positive_int(entry_event.get("episode_sequence")) != daily_entry_count:
                return False
        if isinstance(exit_event, dict) and "episode_sequence" in exit_event:
            if _positive_int(exit_event.get("episode_sequence")) != daily_entry_count:
                return False
        entry_observed_at = str(value.get("entry_observed_at") or "")
        entry_last_completed_bar = str(value.get("entry_last_completed_bar") or "")
        try:
            parsed_entry_observed_at = datetime.fromisoformat(entry_observed_at)
        except (TypeError, ValueError):
            parsed_entry_observed_at = None
        entry_event_observed_at = None
        entry_event_valid_until = None
        if isinstance(entry_event, dict):
            try:
                entry_event_observed_at = datetime.fromisoformat(
                    str(entry_event.get("observed_at") or "")
                )
                entry_event_valid_until = datetime.fromisoformat(
                    str(entry_event.get("valid_until") or "")
                )
            except (TypeError, ValueError):
                pass
        event_prefix = f"{contract.HANWHA_OCEAN_CODE}:{today}:"
        if entry_issued:
            if not (
                isinstance(entry_event, dict)
                and all((entry_reference, structural_support, target_price, peak_price))
                and structural_support <= entry_reference < target_price
                and target_price
                == _ceil_to_tick(
                    entry_reference * (1 + contract.ENTRY_TARGET_PCT / 100)
                )
                and peak_price >= entry_reference
                and parsed_entry_observed_at is not None
                and parsed_entry_observed_at.tzinfo is not None
                and _as_kst(parsed_entry_observed_at).date().isoformat() == today
                and len(entry_last_completed_bar) == 14
                and entry_last_completed_bar.isdigit()
                and entry_last_completed_bar.startswith(today.replace("-", ""))
                and str(entry_event.get("event_id") or "").startswith(
                    f"{event_prefix}ENTRY:"
                )
                and entry_event.get("event_type") == "ENTRY"
                and entry_event.get("state") in {"ENTRY_CAUTION", "ENTRY_READY"}
                and entry_event.get("signal_tier") in {"STANDARD", "HIGH"}
                and entry_event.get("source_quality_status") == "PASS"
                and entry_event.get("strategy_profile") == contract.STRATEGY_PROFILE
                and entry_event.get("authority") == ADVISORY_AUTHORITY
                and entry_event.get("runtime_effect") is False
                and entry_event.get("actual_order_submitted") is False
                and entry_event.get("broker_order_forbidden") is True
                and _positive_int(entry_event.get("entry_reference_price"))
                == entry_reference
                and _positive_int(entry_event.get("structural_support"))
                == structural_support
                and _positive_int(entry_event.get("target_price")) == target_price
                and entry_event_observed_at is not None
                and entry_event_observed_at.tzinfo is not None
                and _as_kst(entry_event_observed_at)
                == _as_kst(parsed_entry_observed_at)
                and entry_event_valid_until is not None
                and entry_event_valid_until.tzinfo is not None
                and entry_event_valid_until > entry_event_observed_at
                and entry_event.get("status")
                == ("ACTIVE" if active else "CLOSED" if completed else "ACTIVE")
            ):
                return False
        elif any(
            (
                active,
                completed,
                entry_reference,
                structural_support,
                target_price,
                peak_price,
                entry_event,
                exit_event,
            )
        ):
            return False
        if completed:
            exit_observed_at = None
            exit_valid_until = None
            if isinstance(exit_event, dict):
                try:
                    exit_observed_at = datetime.fromisoformat(
                        str(exit_event.get("observed_at") or "")
                    )
                    exit_valid_until = datetime.fromisoformat(
                        str(exit_event.get("valid_until") or "")
                    )
                except (TypeError, ValueError):
                    pass
            if not (
                isinstance(exit_event, dict)
                and str(exit_event.get("event_id") or "").startswith(
                    f"{event_prefix}EXIT:"
                )
                and exit_event.get("event_type") == "EXIT"
                and exit_event.get("reason") in contract.EXIT_EVENT_REASONS
                and exit_event.get("source_quality_status") == "PASS"
                and exit_event.get("strategy_profile") == contract.STRATEGY_PROFILE
                and exit_event.get("authority") == ADVISORY_AUTHORITY
                and exit_event.get("runtime_effect") is False
                and exit_event.get("actual_order_submitted") is False
                and exit_event.get("broker_order_forbidden") is True
                and _positive_int(exit_event.get("reference_exit_price")) is not None
                and _positive_int(exit_event.get("entry_reference_price"))
                == entry_reference
                and _positive_int(exit_event.get("structural_support"))
                == structural_support
                and _positive_int(exit_event.get("target_price")) == target_price
                and exit_observed_at is not None
                and exit_observed_at.tzinfo is not None
                and _as_kst(exit_observed_at).date().isoformat() == today
                and exit_valid_until is not None
                and exit_valid_until.tzinfo is not None
                and exit_valid_until > exit_observed_at
            ):
                return False
            if not rearm_after_bar and exit_observed_at is not None:
                rearm_after_bar = _as_kst(exit_observed_at).strftime("%Y%m%d%H%M00")
            if not (
                len(rearm_after_bar) == 14
                and rearm_after_bar.isdigit()
                and rearm_after_bar.startswith(today.replace("-", ""))
            ):
                return False
        elif rearm_required or rearm_after_bar:
            return False
        self.scope_date = today
        self.daily_entry_count = daily_entry_count
        self.entry_issued = entry_issued
        self.active = active
        self.completed = completed
        self.rearm_required = rearm_required
        self.rearm_after_bar = rearm_after_bar
        self.entry_reference_price = entry_reference
        self.structural_support = structural_support
        self.target_price = target_price
        self.entry_observed_at = entry_observed_at
        self.entry_last_completed_bar = entry_last_completed_bar
        self.peak_price = peak_price
        self.entry_event = (
            deepcopy(entry_event) if isinstance(entry_event, dict) else None
        )
        self.exit_event = deepcopy(exit_event) if isinstance(exit_event, dict) else None
        return True

    @staticmethod
    def _valid_until(observed_at: datetime) -> str:
        now = _as_kst(observed_at)
        session_end = now.replace(
            hour=KRX_END.hour,
            minute=KRX_END.minute,
            second=0,
            microsecond=0,
        )
        return min(now + timedelta(seconds=60), session_end).isoformat()

    def _reset_for_date(self, observed_at: datetime) -> None:
        today = _as_kst(observed_at).date().isoformat()
        if self.scope_date != today:
            self.reset()
            self.scope_date = today

    def _clear_current_episode(self) -> None:
        self.entry_issued = False
        self.active = False
        self.completed = False
        self.rearm_required = False
        self.rearm_after_bar = ""
        self.entry_reference_price = None
        self.structural_support = None
        self.target_price = None
        self.entry_observed_at = ""
        self.entry_last_completed_bar = ""
        self.peak_price = None
        self.entry_event = None
        self.exit_event = None

    def _maybe_rearm(
        self,
        advisory: dict[str, Any],
        *,
        observed_at: datetime,
        bars: list[MinuteBar],
        source_quality: dict[str, Any],
    ) -> bool:
        advisory_source_quality = advisory.get("source_quality")
        advisory_source_quality = (
            advisory_source_quality if isinstance(advisory_source_quality, dict) else {}
        )
        if not (
            self.entry_issued
            and self.completed
            and self.rearm_required
            and isinstance(self.exit_event, dict)
            and source_quality.get("status") == "PASS"
            and advisory_source_quality.get("status") == "PASS"
            and advisory.get("state") not in ACTIONABLE_ENTRY_STATES
            and advisory.get("raw_state", advisory.get("state"))
            not in ACTIONABLE_ENTRY_STATES
        ):
            return False
        try:
            exit_valid_until = datetime.fromisoformat(
                str(self.exit_event.get("valid_until") or "")
            )
        except (TypeError, ValueError):
            return False
        latest_bar = bars[-1] if bars else None
        if (
            exit_valid_until.tzinfo is None
            or exit_valid_until > _as_kst(observed_at)
            or latest_bar is None
            or latest_bar.source_time <= self.rearm_after_bar
        ):
            return False
        self._clear_current_episode()
        return True

    def _capture_entry(
        self,
        advisory: dict[str, Any],
        *,
        observed_at: datetime,
        bars: list[MinuteBar],
    ) -> bool:
        if (
            self.entry_issued
            or self.rearm_required
            or advisory.get("state") not in ACTIONABLE_ENTRY_STATES
        ):
            return False
        now = _as_kst(observed_at)
        context = contract.session_context(now)
        if len(bars) < context.minimum_bars or not contract.advisory_contract_is_valid(
            advisory,
            snapshot_time=now,
            context=context,
            evaluated_at=now,
        ):
            return False
        entry_low = _positive_int(advisory.get("entry_price_low"))
        entry_high = _positive_int(advisory.get("entry_price_high"))
        derived = advisory.get("derived")
        derived = derived if isinstance(derived, dict) else {}
        support = _positive_int(
            derived.get("structural_support") or derived.get("confirmed_support")
        )
        if (
            entry_low is None
            or entry_high is None
            or entry_high < entry_low
            or not support
            or support > entry_high
        ):
            return False
        self.entry_issued = True
        self.active = True
        self.completed = False
        self.rearm_required = False
        self.rearm_after_bar = ""
        self.daily_entry_count += 1
        self.entry_reference_price = entry_high
        self.structural_support = support
        self.target_price = _ceil_to_tick(
            entry_high * (1 + contract.ENTRY_TARGET_PCT / 100)
        )
        self.entry_observed_at = now.isoformat()
        self.entry_last_completed_bar = bars[-1].source_time if bars else ""
        self.peak_price = entry_high
        event_id = (
            f"{contract.HANWHA_OCEAN_CODE}:{self.scope_date}:ENTRY:"
            f"{self.daily_entry_count:02d}:{now.strftime('%H%M%S')}"
        )
        policy = advisory.get("hanwha_ocean_policy") or {}
        auxiliary = advisory.get("auxiliary_context") or {}
        external_risk = advisory.get("external_risk") or {}
        self.entry_event = {
            "event_id": event_id,
            "event_type": "ENTRY",
            "episode_sequence": self.daily_entry_count,
            "status": "ACTIVE",
            "state": advisory.get("state"),
            "signal_tier": advisory.get("signal_tier"),
            "entry_price_low": entry_low,
            "entry_price_high": entry_high,
            "entry_reference_price": entry_high,
            "structural_support": support,
            "target_price": self.target_price,
            "session_return_pct": policy.get("session_return_pct"),
            "auxiliary_status": auxiliary.get("status"),
            "relative_status": auxiliary.get("relative_status"),
            "relative_signal": auxiliary.get("relative_signal"),
            "flow_status": auxiliary.get("flow_status"),
            "flow_signal": auxiliary.get("flow_signal"),
            "external_risk_level": external_risk.get("level"),
            "observed_at": now.isoformat(),
            "valid_until": advisory.get("valid_until") or self._valid_until(now),
            "source_quality_status": (
                (advisory.get("source_quality") or {}).get("status")
            ),
            "strategy_profile": contract.STRATEGY_PROFILE,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        return True

    def _exit_payload(
        self,
        *,
        observed_at: datetime,
        source_quality: dict[str, Any],
        state: str,
        reason: str | None = None,
        reference_exit_price: int | None = None,
    ) -> dict[str, Any]:
        return {
            "state": state,
            "raw_state": state,
            "session": "KRX_REGULAR",
            "reference_exit_price": reference_exit_price,
            "peak_price": self.peak_price,
            "peak_drawdown_pct": (
                round(
                    ((self.peak_price - reference_exit_price) / self.peak_price) * 100,
                    4,
                )
                if self.peak_price and reference_exit_price
                else None
            ),
            "broken_support": self.structural_support,
            "entry_reference_price": self.entry_reference_price,
            "target_price": self.target_price,
            "reasons": [reason] if reason else [],
            "unmet_conditions": (
                []
                if self.active
                else [
                    (
                        "hanwha_ocean_entry_episode_not_active"
                        if not self.entry_issued
                        else "hanwha_ocean_entry_episode_rearm_pending"
                    )
                ]
            ),
            "observed_at": _as_kst(observed_at).isoformat(),
            "valid_until": self._valid_until(observed_at),
            "source_quality": source_quality,
            "holding_independent": True,
            "future_prediction": False,
            "strategy_profile": contract.STRATEGY_PROFILE,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "metric_contract": contract.METRIC_CONTRACT,
            "continuity": self.snapshot(),
        }

    def apply(
        self,
        advisory: dict[str, Any],
        *,
        observed_at: datetime,
        current_price: int,
        bars: list[MinuteBar],
        bbo: dict[str, Any],
        source_quality: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        self._reset_for_date(observed_at)
        rearmed = self._maybe_rearm(
            advisory,
            observed_at=observed_at,
            bars=bars,
            source_quality=source_quality,
        )
        capture_attempted = bool(
            not self.entry_issued and advisory.get("state") in ACTIONABLE_ENTRY_STATES
        )
        captured = self._capture_entry(advisory, observed_at=observed_at, bars=bars)
        current_advisory = deepcopy(advisory)
        if rearmed:
            current_advisory["reasons"] = _append_unique(
                current_advisory.get("reasons"),
                "hanwha_ocean_entry_episode_rearmed",
            )
        if capture_attempted and not captured:
            source_status = str(
                (current_advisory.get("source_quality") or {}).get("status") or ""
            )
            fallback_state = "DATA_WAIT" if source_status != "PASS" else "WATCH"
            current_advisory["state"] = current_advisory["raw_state"] = fallback_state
            current_advisory["entry_price_low"] = None
            current_advisory["entry_price_high"] = None
            current_advisory["unmet_conditions"] = _append_unique(
                current_advisory.get("unmet_conditions"),
                "hanwha_ocean_entry_episode_contract_invalid",
            )
        if self.active:
            self.peak_price = max(self.peak_price or current_price, current_price)

        reason = None
        if self.active and source_quality.get("status") == "PASS":
            latest_bar = bars[-1] if bars else None
            if self.target_price and current_price >= self.target_price:
                reason = "hanwha_ocean_target_1pct_reached"
            elif (
                latest_bar is not None
                and latest_bar.source_time > self.entry_last_completed_bar
                and self.structural_support is not None
                and latest_bar.close < self.structural_support
            ):
                reason = "hanwha_ocean_completed_close_below_entry_support"

        if reason and self.exit_event is None:
            now = _as_kst(observed_at)
            reference_exit_price = _positive_int(bbo.get("best_bid")) or current_price
            self.active = False
            self.completed = True
            self.rearm_required = True
            self.rearm_after_bar = (
                bars[-1].source_time if bars else self.entry_last_completed_bar
            )
            if self.entry_event is not None:
                self.entry_event["status"] = "CLOSED"
                self.entry_event["closed_at"] = now.isoformat()
            self.exit_event = {
                "event_id": (
                    f"{contract.HANWHA_OCEAN_CODE}:{self.scope_date}:EXIT:"
                    f"{self.daily_entry_count:02d}:{now.strftime('%H%M%S')}"
                ),
                "event_type": "EXIT",
                "episode_sequence": self.daily_entry_count,
                "reason": reason,
                "reference_exit_price": reference_exit_price,
                "entry_reference_price": self.entry_reference_price,
                "structural_support": self.structural_support,
                "target_price": self.target_price,
                "observed_at": now.isoformat(),
                "valid_until": self._valid_until(now),
                "source_quality_status": source_quality.get("status"),
                "strategy_profile": contract.STRATEGY_PROFILE,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }

        exit_event_valid = False
        if self.exit_event:
            try:
                exit_event_valid = datetime.fromisoformat(
                    str(self.exit_event.get("valid_until") or "")
                ) > _as_kst(observed_at)
            except (TypeError, ValueError):
                exit_event_valid = False
        if self.exit_event and exit_event_valid:
            exit_advisory = self._exit_payload(
                observed_at=observed_at,
                source_quality=source_quality,
                state="EXIT_READY",
                reason=str(self.exit_event.get("reason") or ""),
                reference_exit_price=_positive_int(
                    self.exit_event.get("reference_exit_price")
                ),
            )
        elif source_quality.get("status") != "PASS":
            exit_advisory = self._exit_payload(
                observed_at=observed_at,
                source_quality=source_quality,
                state="DATA_WAIT",
            )
        else:
            exit_advisory = self._exit_payload(
                observed_at=observed_at,
                source_quality=source_quality,
                state="EXIT_WATCH",
            )

        if self.entry_issued and not captured:
            current_advisory["state"] = current_advisory["raw_state"] = "WATCH"
            current_advisory["entry_price_low"] = None
            current_advisory["entry_price_high"] = None
            current_advisory["unmet_conditions"] = _append_unique(
                current_advisory.get("unmet_conditions"),
                (
                    "hanwha_ocean_entry_episode_active"
                    if self.active
                    else "hanwha_ocean_entry_episode_rearm_pending"
                ),
            )
        return current_advisory, exit_advisory


class HanwhaOceanWidgetCollector:
    def __init__(
        self,
        *,
        snapshot_path: Path = contract.DEFAULT_SNAPSHOT_PATH,
        observation_dir: Path = contract.DEFAULT_OBSERVATION_DIR,
        external_provider: ExternalMarketProvider | None = None,
        request_session: requests.Session | None = None,
        notifier: HanwhaOceanWidgetTelegramNotifier | None = None,
        calibration_policy_loader: WidgetCalibrationPolicyLoader | None = None,
    ) -> None:
        self.snapshot_path = snapshot_path
        self.request_session = request_session
        self.notifier = notifier
        self.calibration_policy_loader = (
            calibration_policy_loader or WidgetCalibrationPolicyLoader()
        )
        self.request_budget = ReadOnlyRequestBudget()
        self.auxiliary_context = WidgetAuxiliaryContextCollector(
            HANWHA_OCEAN_AUXILIARY_PROFILE,
            external_provider=external_provider,
        )
        self.break_rearm_filter = AdvisoryBreakRearmFilter()
        self.recovery_episode_filter = AdvisoryRecoveryEpisodeFilter()
        self.promotion_filter = AdvisoryPromotionFilter()
        self.episode_tracker = HanwhaOceanDailyEpisodeTracker()
        self.recorder = ObservationRecorder(
            observation_dir, file_prefix="hanwha_ocean_widget_advisory"
        )
        self._minute_cache: dict[str, Any] = {}
        self._daily_cache: dict[str, Any] = {}
        self._last_minute_fetch = ""
        self._last_daily_fetch = ""
        self._active_date = ""
        self._restore_attempted = False

    def _read_only_client(self) -> KiwoomReadOnlyClient:
        token = kiwoom_utils.get_cached_kiwoom_token(CONF)
        if not token:
            raise RuntimeError("shared_token_unavailable")
        return KiwoomReadOnlyClient(
            token, session=self.request_session, budget=self.request_budget
        )

    def _activate_date(self, observed_at: datetime) -> None:
        day = _as_kst(observed_at).date().isoformat()
        if day == self._active_date:
            return
        self._active_date = day
        self._minute_cache = {}
        self._daily_cache = {}
        self._last_minute_fetch = ""
        self._last_daily_fetch = ""
        self._restore_attempted = False
        self.auxiliary_context.reset()
        self.break_rearm_filter.reset()
        self.recovery_episode_filter.reset()
        self.promotion_filter.reset()
        self.episode_tracker.reset()

    def _restore_state(self, observed_at: datetime, context) -> None:
        if self._restore_attempted:
            return
        self._restore_attempted = True
        payload = contract.load_snapshot(self.snapshot_path)
        if (
            payload.get("schema_version") != contract.SNAPSHOT_SCHEMA_VERSION
            or payload.get("symbol") != contract.HANWHA_OCEAN_CODE
            or payload.get("token_mode") != "shared_cache_only"
            or payload.get("quote_request_code") != contract.HANWHA_OCEAN_CODE
            or payload.get("market_venue") != "KRX"
            or payload.get("market_cohort") != "KRX"
            or payload.get("strategy_profile") != contract.STRATEGY_PROFILE
        ):
            return
        persisted = snapshot_observed_at(payload)
        if persisted is None or persisted.date() != _as_kst(observed_at).date():
            return
        self.episode_tracker.restore(
            payload.get("hanwha_ocean_episode"), observed_at=observed_at
        )
        advisory = payload.get("advisory")
        if not isinstance(advisory, dict):
            return
        self.break_rearm_filter.restore(advisory)
        self.recovery_episode_filter.restore(advisory)
        if contract.snapshot_is_fresh(payload, now=observed_at) and (
            contract.advisory_contract_is_valid(
                advisory,
                snapshot_time=persisted,
                context=context,
                evaluated_at=observed_at,
            )
        ):
            self.promotion_filter.restore(advisory)

    def _notify(self, payload: dict[str, Any], observed_at: datetime) -> None:
        if self.notifier is None:
            return
        try:
            self.notifier.observe(payload, observed_at)
        except Exception as exc:
            print(
                "[WARN] Hanwha Ocean widget Telegram notification isolated: "
                f"{type(exc).__name__}"
            )

    @staticmethod
    def _public_event(
        event: dict[str, Any] | None,
        *,
        expected_type: str,
        observed_at: datetime,
    ) -> dict[str, Any] | None:
        if not contract.advisory_event_contract_is_valid(
            event, expected_type=expected_type, evaluated_at=observed_at
        ):
            return None
        return deepcopy(event)

    @staticmethod
    def _closed_advisory(observed_at: datetime) -> dict[str, Any]:
        return {
            "state": "DATA_WAIT",
            "raw_state": "DATA_WAIT",
            "session": "CLOSED",
            "entry_price_low": None,
            "entry_price_high": None,
            "reasons": [],
            "unmet_conditions": ["krx_regular_session_not_active"],
            "observed_at": _as_kst(observed_at).isoformat(),
            "valid_until": _as_kst(observed_at).isoformat(),
            "source_quality": {
                "status": "BLOCKED",
                "issues": ["krx_regular_session_not_active"],
            },
            "strategy_profile": contract.STRATEGY_PROFILE,
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "metric_contract": contract.METRIC_CONTRACT,
        }

    def collect_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        cycle_started = time.monotonic()
        request_count_before = self.request_budget.total_request_count
        now = _as_kst(observed_at or _now_kst())
        context = contract.session_context(now)
        self._activate_date(now)
        self._restore_state(now, context)
        if not context.active:
            advisory = self._closed_advisory(now)
            payload = {
                "schema_version": contract.SNAPSHOT_SCHEMA_VERSION,
                "status": "closed",
                "symbol": contract.HANWHA_OCEAN_CODE,
                "name": contract.HANWHA_OCEAN_NAME,
                "observed_at_kst": now.isoformat(),
                "market_venue": "KRX",
                "market_cohort": "KRX",
                "market_session": "closed",
                "quote_request_code": contract.HANWHA_OCEAN_CODE,
                "token_mode": "shared_cache_only",
                "strategy_profile": contract.STRATEGY_PROFILE,
                "advisory": advisory,
                "exit_advisory": {
                    **advisory,
                    "state": "DATA_WAIT",
                    "raw_state": "DATA_WAIT",
                    "reference_exit_price": None,
                    "holding_independent": True,
                    "future_prediction": False,
                },
                "hanwha_ocean_episode": self.episode_tracker.snapshot(),
                "entry_event": None,
                "exit_event": None,
            }
            _atomic_write_json(self.snapshot_path, payload)
            return payload

        client = self._read_only_client()
        quote = client.post(
            "/api/dostk/stkinfo", "ka10001", {"stk_cd": contract.HANWHA_OCEAN_CODE}
        )
        quote_received_at = now if observed_at is not None else _now_kst()
        current_price = _positive_int(quote.get("cur_prc"))
        if current_price is None:
            raise RuntimeError("kiwoom_price_missing")
        bbo_payload = client.post(
            "/api/dostk/mrkcond", "ka10004", {"stk_cd": contract.HANWHA_OCEAN_CODE}
        )
        bbo_received_at = now if observed_at is not None else _now_kst()
        bbo = _parse_bbo(bbo_payload, bbo_received_at)

        minute_key = now.strftime("%Y%m%d%H%M")
        if minute_key != self._last_minute_fetch or not self._minute_cache:
            self._minute_cache = client.post(
                "/api/dostk/chart",
                "ka10080",
                {
                    "stk_cd": contract.HANWHA_OCEAN_CODE,
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
            )
            self._last_minute_fetch = minute_key
        bars = completed_session_bars(
            self._minute_cache.get("stk_min_pole_chart_qry"),
            observed_at=now,
            session_start=context.start,
            session_end=context.end,
            limit=400,
        )

        day_key = now.strftime("%Y%m%d")
        if day_key != self._last_daily_fetch or not self._daily_cache:
            self._daily_cache = client.post(
                "/api/dostk/chart",
                "ka10081",
                {
                    "stk_cd": contract.HANWHA_OCEAN_CODE,
                    "base_dt": day_key,
                    "upd_stkpc_tp": "1",
                },
            )
            self._last_daily_fetch = day_key
        previous_day = _current_daily_anchor(
            self._daily_cache.get("stk_dt_pole_chart_qry"),
            observed_at=now,
            cache_fetch_day=self._last_daily_fetch,
        )

        auxiliary = self.auxiliary_context.collect(
            client=client,
            observed_at=now,
            context=context,
            primary_bars=bars,
        )

        decision_now = now if observed_at is not None else _now_kst()
        quote_age_sec = max(
            0.0, (decision_now - _as_kst(quote_received_at)).total_seconds()
        )
        bbo["age_sec"] = max(
            0.0, (decision_now - _as_kst(bbo_received_at)).total_seconds()
        )
        self._restore_state(decision_now, context)
        advisory = evaluate_advisory(
            observed_at=decision_now,
            context=context,
            current_price=current_price,
            bars=bars,
            bbo=bbo,
            previous_day=previous_day,
            relative=auxiliary["relative"],
            external_points=auxiliary["external_points"],
            flow=auxiliary["flow"],
            quote_age_sec=quote_age_sec,
            quote_received_at=_as_kst(quote_received_at).isoformat(),
            external_thresholds=auxiliary["external_thresholds"],
        )
        advisory = attach_auxiliary_summary(advisory, auxiliary["summary"])
        advisory = self.break_rearm_filter.apply(
            advisory, latest_bar=bars[-1] if bars else None
        )
        advisory = self.recovery_episode_filter.apply(
            advisory,
            current_price=current_price,
            bbo=bbo,
            latest_bar=bars[-1] if bars else None,
        )
        advisory = apply_hanwha_ocean_entry_policy(
            advisory,
            current_price=current_price,
            bars=bars,
            context=context,
        )
        calibration_policy = self.calibration_policy_loader.resolve(
            symbol=contract.HANWHA_OCEAN_CODE,
            session=context.name,
            observed_date=decision_now.date(),
        )
        advisory = self.promotion_filter.apply(
            advisory,
            required_confirmations=int(
                calibration_policy["required_actionable_confirmations"]
            ),
            calibration_policy=calibration_policy,
        )
        advisory["metric_contract"] = contract.METRIC_CONTRACT
        advisory.setdefault("provenance", {})["cache_scope"] = [
            now.date().isoformat(),
            "KRX_REGULAR",
            contract.HANWHA_OCEAN_CODE,
        ]
        exit_source_quality = _source_quality(
            observed_at=decision_now,
            context=context,
            bars=bars,
            bbo=bbo,
            previous_day=None,
            quote_age_sec=quote_age_sec,
            current_price=current_price,
        )
        advisory, exit_advisory = self.episode_tracker.apply(
            advisory,
            observed_at=decision_now,
            current_price=current_price,
            bars=bars,
            bbo=bbo,
            source_quality=exit_source_quality,
        )

        day_low = _positive_int(quote.get("low_pric"))
        day_low_delta = (
            current_price - day_low
            if day_low is not None and current_price >= day_low
            else None
        )
        trend_details = analyze_trends(bars, session_name="KRX_REGULAR")
        trends = {
            key: str(value.get("state") or "unavailable")
            for key, value in trend_details.items()
        }
        payload = {
            "schema_version": contract.SNAPSHOT_SCHEMA_VERSION,
            "status": "ok",
            "symbol": contract.HANWHA_OCEAN_CODE,
            "name": contract.HANWHA_OCEAN_NAME,
            "current_price": current_price,
            "day_low_price": day_low,
            "day_low_delta": day_low_delta,
            "day_low_delta_pct": (
                round((day_low_delta / day_low) * 100, 2)
                if day_low_delta is not None and day_low
                else None
            ),
            "minute_trend": trends.get("1m", "unavailable"),
            "minute_trends": trends,
            "minute_trend_details": trend_details,
            "trend_assessment": _trend_assessment(trends),
            "minute_chart": [
                {
                    "time_kst": f"{bar.source_time[8:10]}:{bar.source_time[10:12]}",
                    "close": bar.close,
                }
                for bar in bars[-20:]
            ],
            "observed_at_kst": decision_now.isoformat(),
            "market_venue": "KRX",
            "market_cohort": "KRX",
            "market_session": "krx_regular",
            "minute_session_start_kst": "09:00",
            "quote_request_code": contract.HANWHA_OCEAN_CODE,
            "source": "hanwha_ocean_widget_collector_kiwoom_krx",
            "token_mode": "shared_cache_only",
            "strategy_profile": contract.STRATEGY_PROFILE,
            "observation": {
                "latest_completed_bar": asdict(bars[-1]) if bars else None,
                "raw_10s_persistence_forbidden": True,
            },
            "collector_metrics": {
                "cycle_elapsed_ms": round((time.monotonic() - cycle_started) * 1000, 3),
                "cycle_kiwoom_request_count": (
                    self.request_budget.total_request_count - request_count_before
                ),
                **self.request_budget.snapshot(),
                "authority": "widget_collector_local_only",
            },
            "advisory": advisory,
            "exit_advisory": exit_advisory,
            "hanwha_ocean_episode": self.episode_tracker.snapshot(),
            "entry_event": self._public_event(
                self.episode_tracker.entry_event,
                expected_type="ENTRY",
                observed_at=decision_now,
            ),
            "exit_event": self._public_event(
                self.episode_tracker.exit_event,
                expected_type="EXIT",
                observed_at=decision_now,
            ),
            "kiwoom_official_reference": contract.KIWOOM_OFFICIAL_REFERENCE,
        }
        _atomic_write_json(self.snapshot_path, payload)
        self.recorder.record(payload, decision_now)
        self._notify(payload, decision_now)
        return payload

    def write_failure(self, reason: str, observed_at: datetime | None = None) -> None:
        now = _as_kst(observed_at or _now_kst())
        advisory = self._closed_advisory(now)
        advisory["unmet_conditions"] = [reason]
        advisory["source_quality"] = {"status": "BLOCKED", "issues": [reason]}
        payload = {
            "schema_version": contract.SNAPSHOT_SCHEMA_VERSION,
            "status": "unavailable",
            "symbol": contract.HANWHA_OCEAN_CODE,
            "name": contract.HANWHA_OCEAN_NAME,
            "observed_at_kst": now.isoformat(),
            "market_venue": "KRX",
            "market_cohort": "KRX",
            "quote_request_code": contract.HANWHA_OCEAN_CODE,
            "token_mode": "shared_cache_only",
            "strategy_profile": contract.STRATEGY_PROFILE,
            "reason": reason,
            "advisory": advisory,
            "exit_advisory": {
                **advisory,
                "reference_exit_price": None,
                "holding_independent": True,
                "future_prediction": False,
            },
            "hanwha_ocean_episode": self.episode_tracker.snapshot(),
            "entry_event": None,
            "exit_event": None,
        }
        _atomic_write_json(self.snapshot_path, payload)

    def run_forever(self, *, interval_sec: float = 10.0) -> None:
        interval = max(1.0, float(interval_sec))
        while True:
            started = time.monotonic()
            try:
                self.collect_once()
            except Exception as exc:
                self.write_failure(str(exc)[:160])
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-sec", type=float, default=10.0)
    parser.add_argument(
        "--snapshot-path", type=Path, default=contract.DEFAULT_SNAPSHOT_PATH
    )
    parser.add_argument(
        "--observation-dir", type=Path, default=contract.DEFAULT_OBSERVATION_DIR
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    collector = HanwhaOceanWidgetCollector(
        snapshot_path=args.snapshot_path,
        observation_dir=args.observation_dir,
        notifier=HanwhaOceanWidgetTelegramNotifier(entry_messages_enabled=False),
    )
    if args.once:
        collector.collect_once()
        return 0
    collector.run_forever(interval_sec=args.interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
