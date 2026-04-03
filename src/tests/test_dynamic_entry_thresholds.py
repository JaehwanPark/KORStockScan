from src.engine.sniper_dynamic_thresholds import (
    classify_market_cap_bucket,
    get_dynamic_scalp_thresholds,
    get_dynamic_swing_gap_threshold,
)


def test_market_cap_bucket_classification():
    assert classify_market_cap_bucket(3_000_000_000_000) == "large"
    assert classify_market_cap_bucket(700_000_000_000) == "mid"
    assert classify_market_cap_bucket(120_000_000_000) == "small"


def test_large_cap_relaxes_gap_and_overbought_more_than_small_cap():
    large_scalp = get_dynamic_scalp_thresholds(3_000_000_000_000, turnover_hint=200_000_000_000)
    small_scalp = get_dynamic_scalp_thresholds(120_000_000_000, turnover_hint=10_000_000_000)

    assert large_scalp["max_intraday_surge"] > small_scalp["max_intraday_surge"]
    assert large_scalp["max_surge"] > small_scalp["max_surge"]

    large_gap = get_dynamic_swing_gap_threshold("KOSPI_ML", 3_000_000_000_000, turnover_hint=200_000_000_000)
    small_gap = get_dynamic_swing_gap_threshold("KOSPI_ML", 120_000_000_000, turnover_hint=10_000_000_000)

    assert large_gap["threshold"] > small_gap["threshold"]


def test_kospi_gap_threshold_is_more_permissive_than_kosdaq_for_same_cap():
    marcap = 700_000_000_000
    kospi_gap = get_dynamic_swing_gap_threshold("KOSPI_ML", marcap, turnover_hint=50_000_000_000)
    kosdaq_gap = get_dynamic_swing_gap_threshold("KOSDAQ_ML", marcap, turnover_hint=50_000_000_000)

    assert kospi_gap["threshold"] > kosdaq_gap["threshold"]
