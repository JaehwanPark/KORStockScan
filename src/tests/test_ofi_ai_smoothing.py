from src.engine.ofi_ai_smoothing import (
    INSUFFICIENT,
    NEUTRAL,
    OBSERVER_UNHEALTHY,
    STABLE_BEARISH,
    STABLE_BULLISH,
    STALE,
    OfiSmoothingConfig,
    evaluate_ofi_smoothing,
    entry_skip_demotion_allowed,
    micro_score_raw,
)


def _micro(**overrides):
    payload = {
        "ready": True,
        "observer_healthy": True,
        "snapshot_age_ms": 100,
        "ofi_z": 1.8,
        "qi_ewma": 0.62,
        "micro_state": "bullish",
    }
    payload.update(overrides)
    return payload


def test_ofi_micro_score_is_bounded_and_weighted():
    score = micro_score_raw(_micro(ofi_z=20.0, qi_ewma=1.0))
    assert score is not None
    assert 0.99 <= score <= 1.0

    bearish_score = micro_score_raw(_micro(ofi_z=-20.0, qi_ewma=0.0))
    assert bearish_score is not None
    assert -1.0 <= bearish_score <= -0.99


def test_ofi_ewma_persistence_and_hysteresis_release():
    cfg = OfiSmoothingConfig(raw_weight=1.0, persistence_required=2)
    first = evaluate_ofi_smoothing(_micro(), config=cfg)
    assert first.regime == NEUTRAL
    assert first.bullish_count == 1

    second = evaluate_ofi_smoothing(_micro(), first, config=cfg)
    assert second.regime == STABLE_BULLISH
    assert second.bullish_count == 2

    still_bullish = evaluate_ofi_smoothing(
        _micro(ofi_z=0.3, qi_ewma=0.52, micro_state="neutral"), second, config=cfg
    )
    assert still_bullish.regime == STABLE_BULLISH

    released = evaluate_ofi_smoothing(
        _micro(ofi_z=0.0, qi_ewma=0.50, micro_state="neutral"),
        still_bullish,
        config=cfg,
    )
    assert released.regime == NEUTRAL


def test_ofi_bearish_persistence_and_entry_skip_demotion_guard():
    cfg = OfiSmoothingConfig(raw_weight=1.0, persistence_required=2)
    first = evaluate_ofi_smoothing(
        _micro(ofi_z=-1.8, qi_ewma=0.38, micro_state="bearish"), config=cfg
    )
    second = evaluate_ofi_smoothing(
        _micro(ofi_z=-1.8, qi_ewma=0.38, micro_state="bearish"), first, config=cfg
    )

    assert second.regime == STABLE_BEARISH
    assert (
        entry_skip_demotion_allowed(
            _micro(ofi_z=-1.8, qi_ewma=0.38, micro_state="bearish"), second
        )
        is False
    )


def test_ofi_invalid_inputs_are_not_recast_as_neutral_or_bearish():
    stale = evaluate_ofi_smoothing(_micro(snapshot_age_ms=701))
    unhealthy = evaluate_ofi_smoothing(_micro(observer_healthy=False))
    insufficient = evaluate_ofi_smoothing(
        _micro(ready=False, reason="insufficient_samples")
    )

    assert stale.regime == STALE
    assert unhealthy.regime == OBSERVER_UNHEALTHY
    assert insufficient.regime == INSUFFICIENT
    assert stale.usable is False
    assert unhealthy.usable is False
    assert insufficient.usable is False
