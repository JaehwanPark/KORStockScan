"""Shared historical identity primitives, with no policy or order authority."""

ACTIVATION_SCHEMA = "owner_custody_policy_activation_v1"


def normalize_symbol(value: object) -> str:
    raw = str(value or "").strip().upper()
    base = raw[:-3] if raw.endswith(("_NX", "_AL")) else raw
    if base.startswith("A"):
        base = base[1:]
    return base.zfill(6) if base.isdigit() and 1 <= len(base) <= 6 else raw
