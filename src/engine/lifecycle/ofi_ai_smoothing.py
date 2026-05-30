"""Deterministic OFI/QI smoothing helpers for AI action overrides."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any


STABLE_BULLISH = "stable_bullish"
STABLE_BEARISH = "stable_bearish"
NEUTRAL = "neutral"
STALE = "stale"
OBSERVER_UNHEALTHY = "observer_unhealthy"
INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class OfiSmoothingConfig:
    raw_weight: float = 0.30
    bullish_threshold: float = 0.45
    bearish_threshold: float = -0.45
    release_threshold: float = 0.15
    persistence_required: int = 2
    stale_threshold_ms: int = 700


@dataclass(frozen=True)
class OfiSmoothingState:
    micro_score_raw: float | None = None
    micro_score_smooth: float = 0.0
    regime: str = NEUTRAL
    bullish_count: int = 0
    bearish_count: int = 0
    snapshot_age_ms: float | None = None
    reason: str = "ready"

    @property
    def usable(self) -> bool:
        return self.regime not in {STALE, OBSERVER_UNHEALTHY, INSUFFICIENT}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _clip(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def snapshot_age_ms(micro: dict[str, Any] | None, *, now_ms: int | None = None) -> float | None:
    if not isinstance(micro, dict):
        return None
    captured_at_ms = _safe_float(micro.get("captured_at_ms"), None)
    if captured_at_ms is not None and captured_at_ms > 0:
        current_ms = int(round(time.time() * 1000)) if now_ms is None else int(now_ms)
        return max(0.0, float(current_ms) - float(captured_at_ms))
    return _safe_float(micro.get("snapshot_age_ms"), None)


def micro_score_raw(micro: dict[str, Any]) -> float | None:
    ofi_z = _safe_float(micro.get("ofi_z"), None)
    qi_value = _safe_float(micro.get("qi_ewma"), None)
    if qi_value is None:
        qi_value = _safe_float(micro.get("qi"), None)
    if ofi_z is None or qi_value is None:
        return None
    ofi_component = math.tanh(float(ofi_z) / 2.0)
    qi_component = _clip((float(qi_value) - 0.50) / 0.10)
    return (0.65 * ofi_component) + (0.35 * qi_component)


def _invalid_state(regime: str, *, age_ms: float | None, reason: str) -> OfiSmoothingState:
    return OfiSmoothingState(regime=regime, snapshot_age_ms=age_ms, reason=reason)


def evaluate_ofi_smoothing(
    micro: dict[str, Any] | None,
    previous: OfiSmoothingState | None = None,
    *,
    config: OfiSmoothingConfig | None = None,
    now_ms: int | None = None,
) -> OfiSmoothingState:
    cfg = config or OfiSmoothingConfig()
    if not isinstance(micro, dict):
        return _invalid_state(OBSERVER_UNHEALTHY, age_ms=None, reason="missing_snapshot")

    age_ms = snapshot_age_ms(micro, now_ms=now_ms)
    if micro.get("observer_healthy") is not True:
        return _invalid_state(OBSERVER_UNHEALTHY, age_ms=age_ms, reason="observer_unhealthy")
    if age_ms is not None and age_ms > float(cfg.stale_threshold_ms):
        return _invalid_state(STALE, age_ms=age_ms, reason="snapshot_stale")
    if not bool(micro.get("ready")):
        return _invalid_state(INSUFFICIENT, age_ms=age_ms, reason=str(micro.get("reason") or "insufficient"))

    raw_score = micro_score_raw(micro)
    if raw_score is None:
        return _invalid_state(INSUFFICIENT, age_ms=age_ms, reason="missing_score_inputs")

    prev = previous or OfiSmoothingState()
    raw_weight = _clip(float(cfg.raw_weight), 0.0, 1.0)
    previous_smooth = prev.micro_score_smooth if prev.usable else 0.0
    smooth = (previous_smooth * (1.0 - raw_weight)) + (float(raw_score) * raw_weight)
    bullish_count = prev.bullish_count if prev.usable else 0
    bearish_count = prev.bearish_count if prev.usable else 0
    regime = prev.regime if prev.usable else NEUTRAL

    if smooth >= float(cfg.bullish_threshold):
        bullish_count += 1
        bearish_count = 0
        if bullish_count >= max(1, int(cfg.persistence_required)):
            regime = STABLE_BULLISH
    elif smooth <= float(cfg.bearish_threshold):
        bearish_count += 1
        bullish_count = 0
        if bearish_count >= max(1, int(cfg.persistence_required)):
            regime = STABLE_BEARISH
    else:
        bullish_count = 0
        bearish_count = 0
        if regime == STABLE_BULLISH and smooth < float(cfg.release_threshold):
            regime = NEUTRAL
        elif regime == STABLE_BEARISH and smooth > -float(cfg.release_threshold):
            regime = NEUTRAL

    return OfiSmoothingState(
        micro_score_raw=round(float(raw_score), 6),
        micro_score_smooth=round(float(smooth), 6),
        regime=regime,
        bullish_count=int(bullish_count),
        bearish_count=int(bearish_count),
        snapshot_age_ms=round(float(age_ms), 3) if age_ms is not None else None,
        reason="ready",
    )


def ofi_smoothing_log_fields(state: OfiSmoothingState | None, *, prefix: str = "ofi_smoothing") -> dict[str, Any]:
    if state is None:
        return {
            f"{prefix}_usable": False,
            f"{prefix}_regime": "missing",
        }
    return {
        f"{prefix}_usable": bool(state.usable),
        f"{prefix}_regime": state.regime,
        f"{prefix}_reason": state.reason,
        f"{prefix}_micro_score_raw": "-" if state.micro_score_raw is None else state.micro_score_raw,
        f"{prefix}_micro_score_smooth": state.micro_score_smooth,
        f"{prefix}_bullish_count": state.bullish_count,
        f"{prefix}_bearish_count": state.bearish_count,
        f"{prefix}_snapshot_age_ms": "-" if state.snapshot_age_ms is None else state.snapshot_age_ms,
    }


def entry_skip_demotion_allowed(
    micro: dict[str, Any] | None,
    state: OfiSmoothingState,
) -> bool:
    if not state.usable:
        return False
    if state.regime == STABLE_BEARISH:
        return False
    source_state = str((micro or {}).get("micro_state") or "").strip().lower()
    return source_state in {"neutral", "bullish"}
