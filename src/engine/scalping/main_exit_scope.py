"""As-of Main exit/replay scope. Registration is never execution authority."""
from collections import Counter
import re
import hashlib
import json

from .pre_submit_delay_initial_policy import digest, number
from .reversal_registered_catalog import ROUTES

SCHEMA = "main_exit_scope_snapshot_v1"
MARKETS = {"PRE": "PREMARKET", "REGULAR": "REGULAR", "AFTER": "INTEGRATED_AFTERMARKET"}
DISPOSITIONS = frozenset({"operating_observed", "operating_no_opportunity", "operating_unobserved",
                          "registered_nonoperating", "not_tradable", "custody_excluded"})
MAX_SYMBOLS = 10000


def scope_digest(value):
    sha = hashlib.sha256()
    for block in json.JSONEncoder(sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                                  allow_nan=False).iterencode(value):
        sha.update(block.encode())
    return sha.hexdigest()


def build_scope(universe, *, as_of, universe_source_sha256, coverage=None, operating=None, custody=None):
    as_of = number(as_of)
    if (as_of is None or as_of <= 0 or not isinstance(universe, list)
            or len(universe) > MAX_SYMBOLS or not isinstance(universe_source_sha256, str)
            or not re.fullmatch('[0-9a-f]{64}', universe_source_sha256)):
        raise ValueError("main_exit_scope_global_contract_invalid")
    coverage, operating, custody = coverage or {}, set(operating or []), custody or {}
    rows, excluded, seen = [], [], set()
    for source in universe:
        code = str(source.get("symbol") or source.get("code") or "")
        if not re.fullmatch(r"\d{6}", code) or code in seen:
            raise ValueError("main_exit_scope_universe_identity_invalid")
        seen.add(code)
        known = number(source.get("known_at"))
        if known is None or known > as_of:
            excluded.append({"symbol": code, "reason": "universe_as_of_unverified"})
        for bucket, routes in ROUTES.items():
            market = MARKETS[bucket]
            for route in routes:
                key = "|".join((code, market, route))
                receipt = coverage.get(key) or {}
                management = custody.get(code) or {}
                reason = None
                if management.get("automatic_management_allowed") is False:
                    state, reason = "custody_excluded", management.get("reason", "operator_managed")
                elif source.get("tradable") is False and known is not None and known <= as_of:
                    state, reason = "not_tradable", source.get("reason", "symbol_not_tradable_as_of")
                elif key not in operating:
                    state, reason = "registered_nonoperating", "registration_has_no_execution_authority"
                elif (known is None or known > as_of or number(receipt.get("known_at")) is None
                      or number(receipt.get('known_at')) > as_of or source.get('tradable') is not True
                      or not re.fullmatch('[0-9a-f]{64}', str(receipt.get('generation_sha256') or ''))):
                    state, reason = "operating_unobserved", "as_of_source_gap"
                elif receipt.get("continuous_complete") is not True:
                    state, reason = "operating_unobserved", receipt.get("reason", "coverage_interval_incomplete")
                elif type(receipt.get("opportunity_count")) is int and receipt['opportunity_count'] == 0:
                    state = "operating_no_opportunity"
                elif type(receipt.get("opportunity_count")) is int and receipt["opportunity_count"] > 0:
                    state = "operating_observed"
                else:
                    state, reason = "operating_unobserved", "opportunity_census_unverified"
                rows.append({"scope_key": key, "symbol": code, "market": market, "route": route,
                             "disposition": state, "reason": reason,
                             "coverage_generation_sha256": receipt.get("generation_sha256")})
    body = {"schema": SCHEMA, "as_of": as_of, "universe_source_sha256": universe_source_sha256,
            "symbol_count": len(seen), "scope_count": len(rows), "scopes": rows,
            "source_exclusions": excluded, "counts": dict(Counter(row["disposition"] for row in rows)),
            "runtime_effect": False, "allowed_runtime_apply": False}
    return {**body, "universe_snapshot_sha256": scope_digest(body)}


def validate_scope(scope):
    body = {k: v for k, v in scope.items() if k != "universe_snapshot_sha256"}
    keys = [row["scope_key"] for row in scope["scopes"]]
    if (scope.get("schema") != SCHEMA or scope.get("universe_snapshot_sha256") != scope_digest(body)
        or len(keys) != len(set(keys)) or len(keys) != scope["scope_count"]
        or scope.get('counts') != dict(Counter(row['disposition'] for row in scope['scopes']))
        or any(row["disposition"] not in DISPOSITIONS for row in scope["scopes"])):
        raise ValueError("main_exit_scope_snapshot_invalid")
