"""Main-owned fixed observation; this module has no independent order owner."""

from __future__ import annotations

import hashlib
import math
import os
import uuid
from weakref import WeakKeyDictionary
from dataclasses import dataclass
from datetime import datetime

from src.trading.market import session_contract


WATCH_ORIGIN = "MAIN_FIXED_WATCH"
SAMSUNG_CODE = "005930"
ENABLE_ENV = "KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED"
MIN_WARMUP_SEC = 10.0
_NXT_ADMISSION_CACHE = WeakKeyDictionary()


@dataclass(frozen=True)
class FixedWatchSpec:
    symbol: str
    name: str
    enable_env: str
    initial_policy_scope: str
    episode_entry_forbidden: bool = False


SPECS = (
    FixedWatchSpec(SAMSUNG_CODE, "삼성전자", ENABLE_ENV, "samsung"),
    FixedWatchSpec("034020", "두산에너빌리티",
                   "KORSTOCKSCAN_MAIN_FIXED_WATCH_034020_ENABLED", "non_samsung"),
    FixedWatchSpec("403870", "HPSP", "KORSTOCKSCAN_MAIN_FIXED_WATCH_403870_ENABLED", "non_samsung", True),
    FixedWatchSpec("196170", "알테오젠", "KORSTOCKSCAN_MAIN_FIXED_WATCH_196170_ENABLED", "non_samsung", True),
    FixedWatchSpec("036930", "주성엔지니어링", "KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED", "non_samsung", True),
)


def spec_for(symbol: str) -> FixedWatchSpec:
    for spec in SPECS:
        if spec.symbol == symbol:
            return spec
    raise ValueError("unsupported_main_fixed_watch_symbol")


def symbol_enabled(symbol: str) -> bool:
    spec = spec_for(symbol)
    if symbol == SAMSUNG_CODE:
        return enabled()
    return str(os.getenv(spec.enable_env, "false")).strip().lower() in {"1", "true", "yes", "on"}


def enabled_symbols() -> tuple[str, ...]:
    return tuple(spec.symbol for spec in SPECS if symbol_enabled(spec.symbol))


def reserved_slots() -> int:
    return len(enabled_symbols())


def enabled() -> bool:
    return str(os.getenv(ENABLE_ENV, "false")).strip().lower() in {"1", "true", "yes", "on"}


def is_fixed_watch(target) -> bool:
    return (
        str((target or {}).get("watch_origin") or "") == WATCH_ORIGIN
        and str((target or {}).get("code") or "")[:6] in {spec.symbol for spec in SPECS}
    )


def _normalize_numeric_scanner_nulls(target: dict) -> None:
    """Remove pandas numeric nulls without changing a real scanner claim."""
    for key in ("scanner_promotion_id", "scanner_promotion_reason",
                "scanner_promotion_emitted_epoch", "scanner_watch_budget_owner"):
        value = target.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(value):
            target[key] = None


def session_route(now_epoch: float, symbol: str = SAMSUNG_CODE) -> dict | None:
    spec_for(symbol)
    context = session_contract.resolve_market_session(
        datetime.fromtimestamp(now_epoch, tz=session_contract.KST)
    )
    regime = context.session_regime
    if regime == session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET:
        return {"route": "nxt_only", "symbol": symbol, "item": symbol + "_NX",
                "venue": "PREMARKET_KRX_LIKE", "bucket": "krx_like_premarket"}
    if regime in {
        session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
    }:
        return {"route": "krx_nxt_integrated", "symbol": symbol, "item": symbol + "_AL",
                "venue": "KRX" if regime == session_contract.MARKET_SESSION_REGIME_KRX_REGULAR
                else "KRX_NXT_INTEGRATED",
                "bucket": "krx_regular" if regime == session_contract.MARKET_SESSION_REGIME_KRX_REGULAR
                else regime}
    return None


def generation_id(now_epoch: float, route: dict) -> str:
    trade_date = datetime.fromtimestamp(now_epoch, tz=session_contract.KST).date().isoformat()
    symbol = str(route.get("symbol") or route.get("item") or SAMSUNG_CODE)[:6]
    spec_for(symbol)
    raw = f"{trade_date}|{symbol}|{route['bucket']}|{route['route']}"
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def new_admission_id(now_epoch: float, route: dict) -> str:
    trade_date = datetime.fromtimestamp(now_epoch, tz=session_contract.KST).date()
    symbol = str(route.get("symbol") or route.get("item") or SAMSUNG_CODE)[:6]
    spec_for(symbol)
    return f"FIXED-{trade_date}-{symbol}-{route['bucket']}-{route['route']}-{uuid.uuid4().hex[:12]}"


def broker_and_owner_clear(now_epoch: float, route: dict) -> tuple[bool, str]:
    """Admission requires a recent verified flat account and no unbound intent."""
    from src.engine.scalping.ai_market_snapshot import broker_symbol_verified_flat
    from src.trading.order.owner_custody_registry import default_order_owner_registry

    symbol = str(route.get("symbol") or route.get("item") or SAMSUNG_CODE)[:6]
    spec_for(symbol)
    clear, reason = broker_symbol_verified_flat(symbol, now_ts=now_epoch)
    if not clear:
        return False, reason
    try:
        summary = default_order_owner_registry().unresolved_intent_summary(
            symbol=symbol,
            active_date=None,
        )
    except Exception:
        return False, "owner_registry_unreadable"
    if int(summary.get("unresolved_intent_count") or 0):
        return False, "owner_registry_unresolved_intent"
    return True, "verified_flat"


def _new_symbol_session_eligible(db, spec, route, now_epoch):
    """Use existing exact-date listing evidence for the new Main-only symbols.

    KRX regular admission keeps the existing Main contract. NXT evidence is
    read locally, never inferred from exchange/volume or fetched by this loop.
    """
    if not spec.episode_entry_forbidden or route["bucket"] == "krx_regular":
        return True, "existing_main_session_contract"
    day = datetime.fromtimestamp(now_epoch, tz=session_contract.KST).date()
    key = (spec.symbol, day)
    try:
        per_db = _NXT_ADMISSION_CACHE.setdefault(db, {})
    except TypeError:
        per_db = {}  # Non-weak-referenceable adapters keep the same fail-closed read.
    cached = per_db.get(key)
    if cached and 0 <= now_epoch - cached[0] < 30:
        return cached[1]
    try:
        from src.trading.market.aftermarket_eligibility import resolve_symbol_venue_eligibility
        snapshot = db.get_security_market_eligibility(spec.symbol, day)
        evidence = resolve_symbol_venue_eligibility(spec.symbol, day, snapshot)
        ready = (evidence.nxt_eligible is True and evidence.quality_state in {"VALID", "PARTIAL"}
                 and "NXT" in evidence.eligible_venues
                 and "aftermarket_eligibility_provenance_partial" not in evidence.blockers
                 and evidence.observed_at_kst is not None
                 and evidence.observed_at_kst.date() == day
                 and evidence.observed_at_kst.timestamp() <= now_epoch)
        result = (ready, "exact_date_nxt_eligible" if ready else "fixed_watch_nxt_eligibility_unproven")
    except (AttributeError, OSError, ValueError, TypeError):
        result = (False, "fixed_watch_nxt_eligibility_unproven")
    # At most one current-day cached result per fixed symbol and DB instance.
    for old in tuple(per_db):
        if old[0] == spec.symbol:
            per_db.pop(old)
    per_db[key] = (now_epoch, result)
    return result


def reconcile(db, targets: list[dict], *, now_epoch: float, watch_cap: int,
              symbol: str = SAMSUNG_CODE) -> tuple[str, dict | None]:
    """Atomically own one zero-fill WATCHING row; do not submit an order."""
    from sqlalchemy import and_, or_
    from src.database.models import RecommendationHistory

    spec = spec_for(symbol)
    active_statuses = ("WATCHING", "BUY_ORDERED", "HOLDING", "SELL_ORDERED")
    memory_rows = [t for t in targets if str(t.get("code") or "")[:6] == symbol
                   and str(t.get("status") or "").upper() in active_statuses]
    if not symbol_enabled(symbol):
        with db.get_session() as session:
            fixed_rows = session.query(RecommendationHistory).filter(
                RecommendationHistory.stock_code == symbol,
                RecommendationHistory.watch_origin == WATCH_ORIGIN,
                RecommendationHistory.status == "WATCHING",
                RecommendationHistory.buy_time.is_(None),
                RecommendationHistory.buy_qty == 0,
            ).all()
            if fixed_rows:
                clear, reason = broker_and_owner_clear(now_epoch, {"symbol": symbol})
                if not clear:
                    return f"disabled_custody_wait:{reason}", None
            for row in fixed_rows:
                row.status = "EXPIRED"
        targets[:] = [t for t in targets if not (is_fixed_watch(t) and str(t.get("code") or "")[:6] == symbol and t.get("status") == "WATCHING")]
        return "disabled", None

    route = session_route(now_epoch, symbol)
    if route is None:
        return "outside_supported_session", None
    eligible, reason = _new_symbol_session_eligible(db, spec, route, now_epoch)
    if not eligible:
        return reason, None
    generation = generation_id(now_epoch, route)
    trade_date = datetime.fromtimestamp(now_epoch, tz=session_contract.KST).date()
    fixed_memory = [t for t in memory_rows if is_fixed_watch(t) and str(t.get("code") or "")[:6] == symbol and t.get("status") == "WATCHING"]
    if len(memory_rows) > 1 or (memory_rows and len(fixed_memory) != 1):
        return "same_symbol_runtime_conflict", None
    if fixed_memory:
        _normalize_numeric_scanner_nulls(fixed_memory[0])
    if (fixed_memory and fixed_memory[0].get("watch_generation_id") == generation
        and str(fixed_memory[0].get("watch_admission_id") or "").strip()
        and float(fixed_memory[0].get("entry_armed_at_epoch") or 0) > 0):
        target = fixed_memory[0]
        # DB restoration does not persist the execution/WS route fields.
        # Rebind them on every idempotent reconciliation before evaluation.
        target.update({
            "source_signature": f"MAIN_FIXED_WATCH:{target['watch_admission_id']}",
            "market_session_bucket": route["bucket"],
            "effective_venue": route["venue"],
            "venue_resolution": "main_fixed_watch_session_route",
            "market_data_route": route["route"],
            "initial_policy_scope": spec.initial_policy_scope,
            "broker_route": "NXT" if route["route"] == "nxt_only" else "SOR",
        })
        return "already_watching", target

    clear, reason = broker_and_owner_clear(now_epoch, route)
    if not clear:
        return reason, None
    with db.get_session() as session:
        rows = session.query(RecommendationHistory).filter(
            RecommendationHistory.stock_code == symbol,
            or_(
                RecommendationHistory.status.in_(
                    ("BUY_ORDERED", "HOLDING", "SELL_ORDERED")
                ),
                and_(
                    RecommendationHistory.status == "WATCHING",
                    or_(
                        RecommendationHistory.rec_date == trade_date,
                        RecommendationHistory.watch_origin == WATCH_ORIGIN,
                    ),
                ),
            ),
        ).with_for_update().all()
        if len(rows) > 1:
            return "same_symbol_db_conflict", None
        row = rows[0] if rows else None
        if row is not None and not (
            row.watch_origin == WATCH_ORIGIN and row.status == "WATCHING"
            and row.buy_time is None and int(row.buy_qty or 0) == 0
        ):
            return "same_symbol_db_position_or_watch", None
        # A previous day's unfilled fixed watch can survive a stopped bot.
        # Keep its admission history and create a fresh dated row instead of
        # silently rearming an old memory id against a new database id.
        if row is not None and row.rec_date != trade_date:
            row.status = "EXPIRED"
            row = None
            targets[:] = [
                target for target in targets
                if not (is_fixed_watch(target) and str(target.get("code") or "")[:6] == symbol and target.get("status") == "WATCHING")
            ]
            fixed_memory = []
        if row is None:
            active_watches = sum(
                t.get("status") == "WATCHING"
                and str(t.get("strategy") or "").upper() == "SCALPING"
                for t in targets
            )
            if active_watches >= watch_cap:
                return "fixed_watch_slot_wait", None
            row = RecommendationHistory(
                rec_date=datetime.fromtimestamp(now_epoch, tz=session_contract.KST).date(),
                stock_code=symbol, stock_name=spec.name, trade_type="SCALP",
                status="WATCHING", strategy="SCALPING", position_tag="SCALP_BASE",
                prob=0.5, buy_price=0, buy_qty=0, watch_origin=WATCH_ORIGIN,
            )
            session.add(row)
            session.flush()
        if row.watch_generation_id != generation or not row.watch_admission_id:
            row.watch_admission_id = new_admission_id(now_epoch, route)
        row.watch_generation_id = generation
        row.entry_armed_at_epoch = now_epoch
        row.market_session_bucket = route["bucket"]
        row.effective_venue = route["venue"]
        row.venue_resolution = "main_fixed_watch_session_route"
        record_id = row.id
        admission_id = row.watch_admission_id

    target = fixed_memory[0] if fixed_memory else None
    if target is None:
        recovered = [t for t in db.get_active_targets() if t.get("id") == record_id]
        if len(recovered) != 1:
            return "fixed_watch_db_reload_missing", None
        target = recovered[0]
        _normalize_numeric_scanner_nulls(target)
        targets.append(target)
    target.update({
        "watch_origin": WATCH_ORIGIN, "watch_admission_id": admission_id,
        "watch_generation_id": generation, "entry_armed_at_epoch": now_epoch,
        "source_signature": f"MAIN_FIXED_WATCH:{admission_id}",
        "market_session_bucket": route["bucket"], "effective_venue": route["venue"],
        "venue_resolution": "main_fixed_watch_session_route",
        "market_data_route": route["route"],
        "initial_policy_scope": spec.initial_policy_scope,
        "broker_route": "NXT" if route["route"] == "nxt_only" else "SOR",
        "_fixed_first_exact_receipt_epoch": 0.0,
    })
    return "armed", target


def observation_ready(target: dict, snapshot: dict, *, now_epoch: float) -> tuple[bool, str]:
    route = session_route(now_epoch, str(target.get("code") or SAMSUNG_CODE)[:6])
    if route is None or target.get("watch_generation_id") != generation_id(now_epoch, route):
        return False, "session_generation_mismatch"
    armed = float(target.get("entry_armed_at_epoch") or 0)
    if armed <= 0 or now_epoch - armed < MIN_WARMUP_SEC:
        return False, "fixed_watch_warmup"
    if not isinstance(snapshot, dict) or not snapshot:
        return False, "route_snapshot_missing"
    if snapshot.get("last_ws_item") != route["item"]:
        return False, "exact_route_item_missing"
    type_times = snapshot.get("last_realtime_type_ts") or {}
    type_items = snapshot.get("last_realtime_type_item") or {}
    for real_type in ("0B", "0D"):
        if type_items.get(real_type) != route["item"]:
            return False, f"exact_{real_type}_missing"
        if float(type_times.get(real_type) or 0) < armed:
            return False, f"post_admission_{real_type}_missing"
    if float(snapshot.get("curr") or 0) <= 0:
        return False, "price_missing"
    first = float(target.get("_fixed_first_exact_receipt_epoch") or 0)
    if first <= 0:
        target["_fixed_first_exact_receipt_epoch"] = now_epoch
        return False, "fixed_watch_post_receipt_warmup"
    if now_epoch - first < MIN_WARMUP_SEC:
        return False, "fixed_watch_post_receipt_warmup"
    return True, "ready"
