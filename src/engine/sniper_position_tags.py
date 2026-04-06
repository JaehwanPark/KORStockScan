"""Helpers for strategy-aware position tag defaults and normalization."""

LEGACY_DEFAULT_POSITION_TAG = "MIDDLE"
SCALP_BASE_POSITION_TAG = "SCALP_BASE"
KOSPI_BASE_POSITION_TAG = "KOSPI_BASE"
KOSDAQ_BASE_POSITION_TAG = "KOSDAQ_BASE"


def normalize_strategy(strategy) -> str:
    raw = str(strategy or "KOSPI_ML").strip().upper()
    if raw in {"SCALPING", "SCALP"}:
        return "SCALPING"
    return raw or "KOSPI_ML"


def default_position_tag_for_strategy(strategy) -> str:
    normalized = normalize_strategy(strategy)
    if normalized == "SCALPING":
        return SCALP_BASE_POSITION_TAG
    if normalized == "KOSDAQ_ML":
        return KOSDAQ_BASE_POSITION_TAG
    return KOSPI_BASE_POSITION_TAG


def normalize_position_tag(strategy, position_tag) -> str:
    raw = str(position_tag or "").strip().upper()
    if raw in {"", LEGACY_DEFAULT_POSITION_TAG}:
        return default_position_tag_for_strategy(strategy)
    return raw


def is_default_position_tag(strategy, position_tag) -> bool:
    return normalize_position_tag(strategy, position_tag) == default_position_tag_for_strategy(strategy)


def target_identity(code, strategy) -> tuple[str, str]:
    return (str(code or "").strip()[:6], normalize_strategy(strategy))
