"""Source-quality guards shared by scalp simulator producers and consumers."""

from __future__ import annotations

from typing import Any


_GENERIC_TEST_NAMES = frozenset({"TEST", "DUMMY", "MOCK"})
_KNOWN_TEST_IDENTITIES = frozenset(
    {
        ("123456", "ARMED"),
        ("123123", "LOWLIQ"),
        ("456456", "HOT"),
        ("555555", "RELIEF"),
    }
)


def _fields(value: dict[str, Any]) -> dict[str, Any]:
    nested = value.get("fields")
    return nested if isinstance(nested, dict) else {}


def synthetic_scalp_sim_reason(value: Any) -> str | None:
    """Return a stable exclusion reason for known synthetic simulator rows."""

    if not isinstance(value, dict):
        return None
    fields = _fields(value)
    for key in ("synthetic", "is_synthetic", "test_record", "is_test"):
        marker = fields.get(key, value.get(key))
        if marker is True or str(marker or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "test",
            "synthetic",
        }:
            return f"explicit_{key}"

    code = str(
        fields.get("stock_code")
        or fields.get("code")
        or value.get("stock_code")
        or value.get("code")
        or ""
    ).strip()[:6]
    name = str(
        fields.get("stock_name")
        or fields.get("name")
        or value.get("stock_name")
        or value.get("name")
        or ""
    ).strip().upper()
    if name in _GENERIC_TEST_NAMES or any(
        name.startswith(f"{prefix}_") or name.startswith(f"{prefix}-")
        for prefix in _GENERIC_TEST_NAMES
    ):
        return "synthetic_name"
    if code == "123456":
        return "reserved_test_code"
    if (code, name) in _KNOWN_TEST_IDENTITIES:
        return "known_test_identity"
    return None


def is_synthetic_scalp_sim(value: Any) -> bool:
    return synthetic_scalp_sim_reason(value) is not None
