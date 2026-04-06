from src.engine.sniper_position_tags import (
    KOSDAQ_BASE_POSITION_TAG,
    KOSPI_BASE_POSITION_TAG,
    SCALP_BASE_POSITION_TAG,
    default_position_tag_for_strategy,
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
)


def test_default_position_tags_are_strategy_specific():
    assert default_position_tag_for_strategy("SCALPING") == SCALP_BASE_POSITION_TAG
    assert default_position_tag_for_strategy("SCALP") == SCALP_BASE_POSITION_TAG
    assert default_position_tag_for_strategy("KOSPI_ML") == KOSPI_BASE_POSITION_TAG
    assert default_position_tag_for_strategy("KOSDAQ_ML") == KOSDAQ_BASE_POSITION_TAG


def test_legacy_middle_is_normalized_by_strategy():
    assert normalize_position_tag("SCALPING", "MIDDLE") == SCALP_BASE_POSITION_TAG
    assert normalize_position_tag("KOSPI_ML", "MIDDLE") == KOSPI_BASE_POSITION_TAG
    assert normalize_position_tag("KOSDAQ_ML", "MIDDLE") == KOSDAQ_BASE_POSITION_TAG


def test_default_position_tag_detection_supports_legacy_middle():
    assert is_default_position_tag("SCALPING", "MIDDLE") is True
    assert is_default_position_tag("SCALPING", "SCALP_BASE") is True
    assert is_default_position_tag("KOSPI_ML", "BREAKOUT") is False
    assert normalize_strategy("scalp") == "SCALPING"
