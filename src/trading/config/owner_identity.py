"""Shared historical identity primitives, with no policy or order authority."""

ACTIVATION_SCHEMA = "owner_custody_policy_activation_v1"


def normalize_symbol(value: object) -> str:
    raw = str(value or "").strip().upper()
    base = raw[:-3] if raw.endswith(("_NX", "_AL")) else raw
    if len(base) == 7 and base.startswith("A") and base[1:].isdigit():
        base = base[1:]
    if len(base) == 6 and base.isascii() and base.isalnum():
        return base
    return base.zfill(6) if base.isdigit() and 1 <= len(base) <= 6 else raw
