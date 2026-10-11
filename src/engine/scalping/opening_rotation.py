"""Retired Opening Rotation metadata and compatibility readers.

Entry and exit evaluators are permanently inert. Historical profile and source
metadata remain readable without granting execution or publication authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from src.engine.sniper_time import (
    is_scalping_buy_time_allowed,
    is_scalping_prewarm_time_allowed,
)

POSITION_TAG = "OPENING_ROTATION_1PCT"
WATCH_POSITION_TAG = "SCANNER"
STATE_KEY = "opening_rotation_1pct_state"
RETIRED = True
RETIREMENT_ID = "opening_rotation_full_retirement_20260814"
WINDOW_VERSION = "opening_rotation_common_0903_1140_v2"
POLICY_SCHEMA_VERSION = "opening_rotation_runtime_policy_v2"
ENTRY_TIME_BUCKET_MINUTES = 30
RUNTIME_POLICY_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "runtime" / "opening_rotation"
)

PRIMARY_SOURCES = frozenset(
    {
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
    }
)
EXCLUDED_ENTRY_OWNER_SOURCES = frozenset()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_source_signature(value: Any) -> frozenset[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        values = value
    else:
        values = str(value or "").replace("|", ",").split(",")
    return frozenset(str(item).strip().upper() for item in values if str(item).strip())


def is_krx_regular_scope(*, effective_venue: Any, market_session_bucket: Any) -> bool:
    """Require explicit KRX regular provenance for Opening authority."""

    return bool(
        str(effective_venue or "").strip().upper() == "KRX"
        and str(market_session_bucket or "").strip().lower() == "krx_regular"
    )


@dataclass(frozen=True)
class OpeningRotationEntryProfile:
    enabled: bool = False
    observe_start: time = time(9, 0)
    entry_start: time = time(9, 3)
    entry_end: time = time(11, 40)
    min_day_change_pct: float = 1.5
    max_day_change_pct: float = 5.0
    min_pullback_pct: float = 0.25
    max_pullback_pct: float = 1.0
    max_quote_age_ms: float = 1000.0
    max_tick_age_ms: float = 1000.0
    max_spread_ticks: int = 2
    max_spread_bp: float = 50.0
    min_buy_pressure_pct: float = 58.0
    min_trusted_ticks: int = 5
    min_tick_acceleration: float = 1.15
    min_tick_price_change_pct: float = 0.03
    min_volume_ratio_pct: float = 80.0
    min_vwap_distance_bp: float = -5.0
    max_vwap_distance_bp: float = 60.0
    min_ask_sweep_score: float = 65.0
    min_post_sweep_hold_score: float = 60.0
    min_bid_replenishment_score: float = 55.0
    max_wall_risk_score: float = 69.0
    max_vi_risk_score: float = 69.0
    min_confirmation_count: int = 2
    promotion_ttl_sec: int = 60
    buy_wait_sec: int = 10
    quantity: int = 1
    budget_ratio: float = 0.10
    mechanical_signal_strength: float = 0.80


@dataclass(frozen=True)
class OpeningRotationExitProfile:
    net_take_profit_floor_pct: float = 0.30
    slippage_budget_rate: float = 0.001
    holding_ai_trigger_pct: float = -0.5
    stagnation_sec: int = 300
    stagnation_max_profit_pct: float = 0.20
    max_hold_sec: int = 600
    ratchet_shadow_enabled: bool = True
    ratchet_max_ticks: int = 1


@dataclass
class OpeningRotationEpisodeState:
    episode_id: str
    promotion_id: str
    stock_code: str
    phase: str = "WAIT"
    created_at: str = ""
    buy_order_no: str = ""
    buy_fill_price: int = 0
    buy_filled_at: str = ""
    target_price: int = 0
    target_order_no: str = ""
    holding_ai_called: bool = False
    ratchet_shadow_price: int = 0
    ratchet_shadow_recorded: bool = False
    terminal_reason: str = ""


@dataclass(frozen=True)
class OpeningRotationRuntimePolicy:
    schema_version: str = POLICY_SCHEMA_VERSION
    profile_id: str = "opening_rotation_default_v2"
    entry: OpeningRotationEntryProfile = field(
        default_factory=OpeningRotationEntryProfile
    )
    exit: OpeningRotationExitProfile = field(default_factory=OpeningRotationExitProfile)
    watch_slots: int = 2
    scale_in_allowed: bool = False
    target_date: str = ""
    applied_at_preopen: str = ""
    profile_activated_at_preopen: str = ""
    source_quality_status: str = "runtime_default"
    source_report_path: str = ""
    selected_axis: str = "baseline"
    previous_policy_hash: str = ""

    def canonical_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        for section in ("entry", "exit"):
            values = payload.get(section)
            if not isinstance(values, dict):
                continue
            for key, value in tuple(values.items()):
                if isinstance(value, time):
                    values[key] = value.isoformat()
        return payload

    @property
    def policy_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def as_artifact(self) -> dict[str, Any]:
        return {**self.canonical_payload(), "policy_hash": self.policy_hash}


# Compatibility imports used by the existing runtime and reports.
EntryConfig = OpeningRotationEntryProfile
ExitConfig = OpeningRotationExitProfile


def _validate_bounded_profile(policy: OpeningRotationRuntimePolicy) -> None:
    """Reject policy fields outside the predeclared PREOPEN profile catalog."""

    baseline_entry = OpeningRotationEntryProfile(enabled=policy.entry.enabled)
    tunable_entry_fields = {
        "min_day_change_pct",
        "max_day_change_pct",
        "min_pullback_pct",
        "max_pullback_pct",
        "min_confirmation_count",
    }
    for key, baseline_value in asdict(baseline_entry).items():
        if key in tunable_entry_fields:
            continue
        if getattr(policy.entry, key) != baseline_value:
            raise ValueError(f"opening rotation non-tunable entry field changed: {key}")
    if policy.entry.min_day_change_pct not in {0.5, 1.0, 1.5, 2.0}:
        raise ValueError("opening rotation day-change lower bound outside catalog")
    if policy.entry.max_day_change_pct not in {4.0, 5.0, 6.0, 8.0}:
        raise ValueError("opening rotation day-change upper bound outside catalog")
    if policy.entry.min_day_change_pct > policy.entry.max_day_change_pct:
        raise ValueError("opening rotation day-change range is inverted")
    if (policy.entry.min_pullback_pct, policy.entry.max_pullback_pct) not in {
        (0.15, 0.8),
        (0.25, 1.0),
        (0.4, 1.2),
    }:
        raise ValueError("opening rotation pullback range outside catalog")
    if policy.entry.min_confirmation_count not in {2, 3}:
        raise ValueError("opening rotation confirmation count outside catalog")

    baseline_exit = OpeningRotationExitProfile()
    tunable_exit_fields = {"holding_ai_trigger_pct", "stagnation_sec", "max_hold_sec"}
    for key, baseline_value in asdict(baseline_exit).items():
        if key in tunable_exit_fields:
            continue
        if getattr(policy.exit, key) != baseline_value:
            raise ValueError(f"opening rotation non-tunable exit field changed: {key}")
    if policy.exit.holding_ai_trigger_pct not in {-0.3, -0.5, -0.7}:
        raise ValueError("opening rotation holding-AI trigger outside catalog")
    if (policy.exit.stagnation_sec, policy.exit.max_hold_sec) not in {
        (240, 480),
        (300, 600),
        (360, 720),
    }:
        raise ValueError("opening rotation timeout pair outside catalog")


def entry_window_version(config: EntryConfig | None = None) -> str:
    """Return a stable cohort version for the effective entry window."""

    config = config or EntryConfig()
    if config.entry_start == time(9, 3) and config.entry_end == time(11, 40):
        return WINDOW_VERSION
    return (
        "opening_rotation_"
        f"{config.entry_start.strftime('%H%M')}_"
        f"{config.entry_end.strftime('%H%M')}_custom"
    )


def entry_time_bucket(
    value: datetime | time,
    config: EntryConfig | None = None,
) -> str:
    """Map an in-window entry to its clock-aligned 30-minute cohort.

    The inclusive end boundary belongs to the final bucket so a fill stamped
    exactly at the configured cutoff is not reported as out of window.
    """

    config = config or EntryConfig()
    value_time = value.time() if isinstance(value, datetime) else value
    if value_time < config.entry_start or value_time > config.entry_end:
        return "outside_entry_window"

    minute_of_day = (value_time.hour * 60) + value_time.minute
    end_minute = (config.entry_end.hour * 60) + config.entry_end.minute
    if value_time == config.entry_end:
        minute_of_day = max(0, end_minute - 1)
    bucket_start = (
        minute_of_day // ENTRY_TIME_BUCKET_MINUTES
    ) * ENTRY_TIME_BUCKET_MINUTES
    bucket_end = bucket_start + ENTRY_TIME_BUCKET_MINUTES
    return (
        f"{bucket_start // 60:02d}:{bucket_start % 60:02d}-"
        f"{bucket_end // 60:02d}:{bucket_end % 60:02d}"
    )


def entry_time_bucket_labels(config: EntryConfig | None = None) -> tuple[str, ...]:
    """Return every clock-aligned cohort intersecting the entry window."""

    config = config or EntryConfig()
    start_minute = (config.entry_start.hour * 60) + config.entry_start.minute
    end_minute = (config.entry_end.hour * 60) + config.entry_end.minute
    bucket_start = (
        start_minute // ENTRY_TIME_BUCKET_MINUTES
    ) * ENTRY_TIME_BUCKET_MINUTES
    labels: list[str] = []
    while bucket_start < end_minute:
        bucket_end = bucket_start + ENTRY_TIME_BUCKET_MINUTES
        labels.append(
            f"{bucket_start // 60:02d}:{bucket_start % 60:02d}-"
            f"{bucket_end // 60:02d}:{bucket_end % 60:02d}"
        )
        bucket_start = bucket_end
    return tuple(labels)


def is_strategy_position(position_tag: Any) -> bool:
    return str(position_tag or "").strip().upper() == POSITION_TAG


def is_watch_source_scope(
    *,
    position_tag: Any,
    source_signature: Any,
    now_dt: datetime,
    config: EntryConfig,
) -> bool:
    """Return the source/time scope before a live day-change value is available.

    Scanner upstream skips can happen before a usable WS snapshot reaches the
    strategy.  Keeping this predicate separate lets those gaps be attributed
    without pretending that a source-scoped row passed the full entry screen.
    """

    if not config.enabled:
        return False
    normalized_tag = str(position_tag or "").strip().upper()
    if normalized_tag not in {WATCH_POSITION_TAG, POSITION_TAG}:
        return False
    if not is_observation_time_allowed(now_dt, config):
        return False
    if normalized_tag == POSITION_TAG:
        return True
    source_tokens = parse_source_signature(source_signature)
    # Every regular-scanner promotion is eligible.  Specialist ownership is
    # resolved by the caller; source/lineage tokens are not strategy vetoes.
    return bool(source_tokens)


def is_observation_time_allowed(now_dt: datetime, config: EntryConfig) -> bool:
    if now_dt.time() < config.observe_start or now_dt.time() > config.entry_end:
        return False
    if time(9, 0) <= now_dt.time() < config.entry_start:
        return is_scalping_prewarm_time_allowed(now_dt)
    return is_scalping_buy_time_allowed(now_dt)


def is_entry_time_allowed(now_dt: datetime, config: EntryConfig) -> bool:
    return bool(
        time(9, 0) <= now_dt.time() <= config.entry_end
        and now_dt.time() >= config.entry_start
        and is_scalping_buy_time_allowed(now_dt)
    )


def is_watch_candidate(
    *,
    position_tag: Any,
    source_signature: Any,
    day_change_pct: float,
    now_dt: datetime,
    config: EntryConfig,
) -> bool:
    if not is_watch_source_scope(
        position_tag=position_tag,
        source_signature=source_signature,
        now_dt=now_dt,
        config=config,
    ):
        return False
    if not is_observation_time_allowed(now_dt, config):
        return False
    if not (
        config.min_day_change_pct <= float(day_change_pct) <= config.max_day_change_pct
    ):
        return False
    return True


def _blocked(reason: str, state: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {
        "in_scope": True,
        "qualified": False,
        "reason": reason,
        "state": state,
        "position_tag": POSITION_TAG,
        "ai_score_hard_gate": False,
        "ai_score_decision_authority": "feature_only_not_evaluated",
        **fields,
    }


def _entry_micro_gate_preview(
    packet: dict[str, Any],
    config: EntryConfig,
    *,
    source_quality_ready: bool = True,
) -> tuple[dict[str, Any], tuple[tuple[bool, str], ...]]:
    """Expose downstream gate readiness before the pullback state is complete."""

    spread_bp = _number(packet.get("spread_bp"), 999.0)
    spread_ticks = _number(packet.get("spread_ticks"), 999.0)
    buy_pressure = _number(packet.get("buy_pressure_10t"), 0.0)
    trusted_ticks = int(_number(packet.get("tick_aggressor_trusted_count"), 0.0))
    tick_acceleration = _number(packet.get("tick_acceleration_ratio"), 0.0)
    tick_price_change = _number(packet.get("price_change_10t_pct"), 0.0)
    volume_ratio = _number(packet.get("volume_ratio_pct"), 0.0)
    vwap_available = _boolean(packet.get("micro_vwap_available"))
    vwap_distance = _number(packet.get("curr_vs_micro_vwap_bp"), -999.0)
    ask_sweep = _number(packet.get("microstructure_reaction_ask_sweep_score"), 0.0)
    post_sweep_hold = _number(
        packet.get("microstructure_reaction_post_sweep_hold_score"), 0.0
    )
    bid_replenishment = _number(
        packet.get("microstructure_reaction_bid_replenishment_score"), 0.0
    )
    wall_risk = _number(
        packet.get("microstructure_reaction_wall_replenishment_risk_score"), 100.0
    )
    vi_risk = _number(packet.get("microstructure_reaction_vi_proximity_risk"), 100.0)
    hard_checks = (
        (
            0.0 <= spread_bp <= config.max_spread_bp
            and 0.0 <= spread_ticks <= config.max_spread_ticks,
            "spread_too_wide",
        ),
        (buy_pressure >= config.min_buy_pressure_pct, "buy_pressure_below_min"),
        (trusted_ticks >= config.min_trusted_ticks, "trusted_tick_sample_below_min"),
        (wall_risk <= config.max_wall_risk_score, "wall_replenishment_risk"),
        (vi_risk <= config.max_vi_risk_score, "vi_proximity_risk"),
    )
    confirmations = (
        (tick_acceleration >= config.min_tick_acceleration, "tick_acceleration"),
        (tick_price_change >= config.min_tick_price_change_pct, "tick_price_change"),
        (volume_ratio >= config.min_volume_ratio_pct, "volume_reacceleration"),
        (
            bid_replenishment >= config.min_bid_replenishment_score,
            "bid_replenishment",
        ),
        (
            vwap_available
            and config.min_vwap_distance_bp
            <= vwap_distance
            <= config.max_vwap_distance_bp,
            "micro_vwap_distance",
        ),
    )
    confirmation_count = sum(1 for passed, _name in confirmations if passed)
    checks = hard_checks + (
        (
            confirmation_count >= config.min_confirmation_count,
            "confirmation_count_below_min",
        ),
    )
    failed_reasons = [reason for passed, reason in checks if not passed]
    preview_blockers = (
        failed_reasons if source_quality_ready else ["trusted_tick_context_unavailable"]
    )
    metrics = {
        "spread_bp": spread_bp,
        "spread_ticks": spread_ticks,
        "buy_pressure_10t": buy_pressure,
        "tick_aggressor_trusted_count": trusted_ticks,
        "tick_acceleration_ratio": tick_acceleration,
        "price_change_10t_pct": tick_price_change,
        "volume_ratio_pct": volume_ratio,
        "micro_vwap_available": vwap_available,
        "curr_vs_micro_vwap_bp": vwap_distance,
        "microstructure_reaction_ask_sweep_score": ask_sweep,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment,
        "microstructure_reaction_wall_replenishment_risk_score": wall_risk,
        "microstructure_reaction_vi_proximity_risk": vi_risk,
        "opening_rotation_confirmation_count": confirmation_count,
        "opening_rotation_confirmation_required": config.min_confirmation_count,
        "opening_rotation_confirmations": ",".join(
            name for passed, name in confirmations if passed
        )
        or "-",
        "opening_rotation_ask_sweep_diagnostic": ask_sweep,
        "opening_rotation_post_sweep_hold_diagnostic": post_sweep_hold,
        "opening_rotation_downstream_preview_evaluated": source_quality_ready,
        "opening_rotation_downstream_preview_source_quality": (
            "ready" if source_quality_ready else "trusted_tick_context_unavailable"
        ),
        "opening_rotation_downstream_preview_passed": (
            source_quality_ready and not failed_reasons
        ),
        "opening_rotation_downstream_preview_pass_count": (
            len(checks) - len(failed_reasons) if source_quality_ready else 0
        ),
        "opening_rotation_downstream_preview_total_count": len(checks),
        "opening_rotation_downstream_preview_first_blocker": (
            preview_blockers[0] if preview_blockers else "all_downstream_gates_ready"
        ),
        "opening_rotation_downstream_preview_blockers": (
            ",".join(preview_blockers) if preview_blockers else "-"
        ),
        "opening_rotation_downstream_preview_decision_authority": (
            "observation_only_no_pattern_or_submit_bypass"
        ),
        "opening_rotation_downstream_preview_metric_role": "diagnostic",
        "opening_rotation_downstream_preview_window_policy": (
            "same_symbol_same_day_opening_rotation_state"
        ),
        "opening_rotation_downstream_preview_sample_floor": (
            "one_fresh_quote_observation_trusted_tape_required_for_evaluated_true"
        ),
        "opening_rotation_downstream_preview_primary_decision_metric": (
            "first_blocker_after_source_quality"
        ),
        "opening_rotation_downstream_preview_source_quality_gate": (
            "fresh_quote_and_trusted_ws_aggressor_context"
        ),
        "opening_rotation_downstream_preview_forbidden_uses": (
            "standalone_buy,pattern_bypass,submit_safety_bypass,broker_guard_bypass,"
            "threshold_mutation,quantity_or_cap_change,provider_route_change"
        ),
    }
    return metrics, checks


def evaluate_entry(**kwargs):
    return {"decision":"WATCH", "action":"WATCH", "reason":"opening_rotation_permanently_retired", "next_state":dict(kwargs.get("previous_state") or {}), "allowed_runtime_apply":False}


def evaluate_exit(**kwargs):
    return {"decision":"HOLD", "action":"HOLD", "reason":"opening_rotation_permanently_retired", "allowed_runtime_apply":False}


def make_episode_id(stock_code: str, promotion_id: str, now_dt: datetime) -> str:
    seed = f"{stock_code}|{promotion_id}|{now_dt.isoformat()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"OREP-{now_dt.strftime('%Y%m%d')}-{stock_code}-{digest}"


def ceil_to_tick(price: float, tick_size: int) -> int:
    tick = max(1, int(tick_size or 1))
    return int(math.ceil(float(price) / tick) * tick)


def profit_target_price(
    buy_fill_price: int,
    *,
    trade_cost_rate: float,
    tick_size: int,
    config: ExitConfig | None = None,
) -> int:
    config = config or ExitConfig()
    denominator = 1.0 - float(trade_cost_rate) - config.slippage_budget_rate
    if buy_fill_price <= 0 or denominator <= 0:
        return 0
    raw = (
        float(buy_fill_price)
        * (1.0 + config.net_take_profit_floor_pct / 100.0)
        / denominator
    )
    return ceil_to_tick(raw, tick_size)


def shadow_ratchet_price(initial_target_price: int, *, tick_size: int) -> int:
    if initial_target_price <= 0:
        return 0
    return initial_target_price + max(1, int(tick_size or 1))


def load_runtime_policy(path: str | Path) -> OpeningRotationRuntimePolicy:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("opening rotation policy payload must be an object")
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ValueError("opening rotation policy schema mismatch")
    supplied_hash = str(payload.get("policy_hash", "") or "").strip()

    def _profile_time(values: dict[str, Any], key: str, fallback: time) -> None:
        value = values.get(key)
        if isinstance(value, time):
            return
        if value in (None, ""):
            values[key] = fallback
            return
        try:
            values[key] = time.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"opening rotation policy invalid time: {key}") from exc

    entry_payload = dict(payload.get("entry") or {})
    _profile_time(entry_payload, "observe_start", time(9, 0))
    _profile_time(entry_payload, "entry_start", time(9, 3))
    _profile_time(entry_payload, "entry_end", time(11, 40))
    policy = OpeningRotationRuntimePolicy(
        schema_version=payload.get("schema_version", POLICY_SCHEMA_VERSION),
        profile_id=str(payload.get("profile_id") or ""),
        entry=OpeningRotationEntryProfile(**entry_payload),
        exit=OpeningRotationExitProfile(**(payload.get("exit") or {})),
        watch_slots=int(payload.get("watch_slots", 2) or 2),
        scale_in_allowed=bool(payload.get("scale_in_allowed", False)),
        target_date=str(payload.get("target_date") or ""),
        applied_at_preopen=str(payload.get("applied_at_preopen") or ""),
        profile_activated_at_preopen=str(
            payload.get("profile_activated_at_preopen") or ""
        ),
        source_quality_status=str(payload.get("source_quality_status") or ""),
        source_report_path=str(payload.get("source_report_path") or ""),
        selected_axis=str(payload.get("selected_axis") or ""),
        previous_policy_hash=str(payload.get("previous_policy_hash") or ""),
    )
    if supplied_hash != policy.policy_hash:
        raise ValueError("opening rotation policy hash mismatch")
    if policy.profile_activated_at_preopen:
        try:
            datetime.fromisoformat(
                policy.profile_activated_at_preopen.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "opening rotation profile activation provenance is invalid"
            ) from exc
    if (
        policy.watch_slots != 2
        or policy.scale_in_allowed
        or policy.entry.quantity != 1
        or policy.entry.observe_start != time(9, 0)
        or policy.entry.entry_start != time(9, 3)
        or policy.entry.entry_end != time(11, 40)
        or policy.entry.buy_wait_sec != 10
        or policy.exit.net_take_profit_floor_pct != 0.30
        or policy.exit.slippage_budget_rate != 0.001
        or policy.exit.stagnation_max_profit_pct != 0.20
    ):
        raise ValueError("opening rotation fixed safety invariant mismatch")
    _validate_bounded_profile(policy)
    if policy.source_quality_status.strip().upper() not in {"PASS", "RUNTIME_DEFAULT"}:
        raise ValueError("opening rotation policy source quality is not PASS")
    return policy


def runtime_policy_path(target_date: str, *, root: Path = RUNTIME_POLICY_DIR) -> Path:
    return root / f"opening_rotation_runtime_policy_{target_date}.json"


def load_active_runtime_policy(
    *,
    now_dt: datetime | None = None,
    path: str | Path | None = None,
) -> OpeningRotationRuntimePolicy:
    """Load only a same-date PREOPEN artifact; otherwise keep the fixed baseline.

    This function deliberately does not search older files.  Carry-forward is
    materialized by the PREOPEN producer so a stale artifact cannot silently
    mutate an intraday profile.
    """

    observed_at = now_dt or datetime.now().astimezone()
    target_date = observed_at.strftime("%Y-%m-%d")
    configured_path = str(
        path or os.getenv("KORSTOCKSCAN_OPENING_ROTATION_RUNTIME_POLICY_PATH", "") or ""
    ).strip()
    candidate_path = (
        Path(configured_path) if configured_path else runtime_policy_path(target_date)
    )
    if not candidate_path.exists():
        # Code presence is not runtime authority. Opening becomes active only
        # after the target-date PREOPEN producer materializes and hashes the
        # policy artifact that can be verified before a process start.
        return OpeningRotationRuntimePolicy(
            target_date=target_date,
            entry=OpeningRotationEntryProfile(enabled=False),
        )
    policy = load_runtime_policy(candidate_path)
    if policy.target_date != target_date:
        raise ValueError("opening rotation runtime policy target date mismatch")
    if not policy.applied_at_preopen:
        raise ValueError("opening rotation runtime policy PREOPEN provenance missing")
    return policy
