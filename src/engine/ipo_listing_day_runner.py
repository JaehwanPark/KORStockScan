"""IPO listing-day spread capture runner.

This module is intentionally isolated from the scalping/swing threshold
automation chain. It reuses Kiwoom transport/order utilities, but keeps its
own session state and artifacts under data/ipo_listing_day/.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, time as dt_time
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except Exception:  # pragma: no cover - dependency guard for minimal envs
    yaml = None

from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.ai_engine_openai import GPTSniperEngine
from src.utils import kiwoom_utils
from src.utils.constants import CONFIG_PATH, DEV_PATH
from src.utils.logger import log_error, log_info
from src.engine.trade_pause_control import is_buy_side_paused
from src.engine.scalping.entry_candle_context import (
    build_entry_candle_context,
    entry_candle_context_enabled,
    fetch_entry_candles_with_meta,
)

OUTPUT_ROOT = Path("data/ipo_listing_day")
STOP_FILE = OUTPUT_ROOT / "STOP"
KRX_RULE_SOURCE = "KRX first-day IPO range public offering price 60%~400%, regular-session IOC/best-limit only"
MAX_TARGET_BUDGET_CAP_KRW = 5_000_000

ENTRY_START = dt_time(9, 0, 0)
ENTRY_END = dt_time(9, 0, 30)
PREOPEN_MONITOR_START = dt_time(8, 59, 50)


@dataclass(frozen=True)
class IpoTarget:
    code: str
    name: str
    listing_date: str
    offer_price: int
    budget_cap_krw: int
    premium_guard_pct: float = 250.0
    enabled: bool = True


@dataclass(frozen=True)
class IpoRunConfig:
    trade_date: str
    global_daily_loss_cap_krw: int = 100_000
    max_order_failures: int = 2
    active_symbol_limit: int = 1
    max_ai_calls_per_symbol: int = 6
    max_ai_calls_per_run: int = 10
    targets: tuple[IpoTarget, ...] = field(default_factory=tuple)


@dataclass
class IpoPosition:
    code: str
    name: str
    qty: int = 0
    avg_price: int = 0
    entry_time: datetime | None = None
    realized_pnl_krw: int = 0
    peak_profit_pct: float = 0.0
    first_partial_taken: bool = False
    closed: bool = False
    reentry_blocked: bool = False


@dataclass
class IpoDecision:
    allowed: bool
    reason: str
    fields: dict[str, Any] = field(default_factory=dict)


class IpoArtifactWriter:
    def __init__(self, output_root: Path = OUTPUT_ROOT, trade_date: str | None = None):
        self.output_root = Path(output_root)
        self.trade_date = trade_date or date.today().isoformat()
        self.run_dir = self.output_root / self.trade_date
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.run_dir / "events.jsonl"
        self.summary_items: list[dict[str, Any]] = []

    def event(self, stage: str, **fields: Any) -> None:
        payload = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "stage": stage,
            "fields": _jsonable(fields),
        }
        with self.events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def decision(self, code: str, decision: IpoDecision) -> None:
        path = self.run_dir / f"{code}_decision.json"
        payload = {
            "code": code,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "fields": _jsonable(decision.fields),
            "krx_rule_source": KRX_RULE_SOURCE,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def add_summary(self, item: dict[str, Any]) -> None:
        self.summary_items.append(_jsonable(item))

    def write_summary(self) -> Path:
        path = self.run_dir / "summary.md"
        lines = [
            f"# IPO Listing-Day Runner Summary ({self.trade_date})",
            "",
            f"- rule_source: `{KRX_RULE_SOURCE}`",
            f"- events: `{self.events_path}`",
            "",
            "## Targets",
            "",
        ]
        if not self.summary_items:
            lines.append("- no target processed")
        for item in self.summary_items:
            lines.append(
                "- {code} {name}: status=`{status}`, realized_pnl_krw=`{pnl}`, reason=`{reason}`".format(
                    code=item.get("code", "-"),
                    name=item.get("name", "-"),
                    status=item.get("status", "-"),
                    pnl=item.get("realized_pnl_krw", 0),
                    reason=item.get("reason", "-"),
                )
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return default


def normalize_code(code: Any) -> str:
    return kiwoom_utils.normalize_stock_code(str(code or ""))


def load_ipo_config(path: str | Path) -> IpoRunConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"IPO config not found: {config_path}")
    text = config_path.read_text(encoding="utf-8")
    if yaml is not None:
        raw = yaml.safe_load(text) or {}
    else:
        raw = _load_simple_ipo_yaml(text)
    if not isinstance(raw, dict):
        raise ValueError("IPO config root must be a mapping")
    targets = []
    for item in raw.get("targets") or []:
        if not isinstance(item, dict):
            continue
        targets.append(
            IpoTarget(
                code=normalize_code(item.get("code")),
                name=str(item.get("name") or "").strip(),
                listing_date=str(
                    item.get("listing_date") or raw.get("trade_date") or ""
                ).strip(),
                offer_price=_safe_int(item.get("offer_price")),
                budget_cap_krw=_safe_int(item.get("budget_cap_krw")),
                premium_guard_pct=_safe_float(item.get("premium_guard_pct"), 250.0),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return IpoRunConfig(
        trade_date=str(raw.get("trade_date") or date.today().isoformat()),
        global_daily_loss_cap_krw=_safe_int(
            raw.get("global_daily_loss_cap_krw"), 100_000
        ),
        max_order_failures=_safe_int(raw.get("max_order_failures"), 2),
        active_symbol_limit=max(1, _safe_int(raw.get("active_symbol_limit"), 1)),
        max_ai_calls_per_symbol=max(
            0, _safe_int(raw.get("max_ai_calls_per_symbol"), 6)
        ),
        max_ai_calls_per_run=max(0, _safe_int(raw.get("max_ai_calls_per_run"), 10)),
        targets=tuple(targets),
    )


def _parse_scalar(text: str) -> Any:
    value = str(text or "").strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _load_simple_ipo_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by IPO runner configs when PyYAML is absent."""
    root: dict[str, Any] = {}
    targets: list[dict[str, Any]] = []
    current_target: dict[str, Any] | None = None
    in_targets = False
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and line == "targets:":
            in_targets = True
            root["targets"] = targets
            continue
        if not in_targets and ":" in line:
            key, value = line.split(":", 1)
            root[key.strip()] = _parse_scalar(value)
            continue
        if in_targets:
            if line.startswith("- "):
                current_target = {}
                targets.append(current_target)
                rest = line[2:].strip()
                if rest and ":" in rest:
                    key, value = rest.split(":", 1)
                    current_target[key.strip()] = _parse_scalar(value)
                continue
            if current_target is not None and ":" in line:
                key, value = line.split(":", 1)
                current_target[key.strip()] = _parse_scalar(value)
                continue
    return root


def load_json_config() -> dict[str, Any]:
    path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        log_error(f"IPO runner config load failed: {exc}")
        return {}


def select_enabled_targets(
    config: IpoRunConfig, today: str | None = None
) -> list[IpoTarget]:
    trade_date = today or config.trade_date
    selected = [
        target
        for target in config.targets
        if target.enabled
        and target.code
        and target.listing_date == trade_date
        and target.offer_price > 0
    ]
    return selected[: config.active_symbol_limit]


def best_levels(
    ws_data: dict[str, Any] | None,
) -> tuple[int, int, list[dict[str, Any]], list[dict[str, Any]]]:
    orderbook = (ws_data or {}).get("orderbook") or {}
    asks = list(orderbook.get("asks") or [])
    bids = list(orderbook.get("bids") or [])
    best_ask = _safe_int(
        (asks[0] or {}).get("price") if asks else (ws_data or {}).get("best_ask"), 0
    )
    best_bid = _safe_int(
        (bids[0] or {}).get("price") if bids else (ws_data or {}).get("best_bid"), 0
    )
    return best_ask, best_bid, asks, bids


def planned_entry_price(ws_data: dict[str, Any], *, retry: bool = False) -> int:
    curr = _safe_int(ws_data.get("curr") or ws_data.get("open"), 0)
    best_ask, best_bid, _, _ = best_levels(ws_data)
    if retry and best_ask > 0:
        tick = max(1, int(kiwoom_utils.get_tick_size(best_ask) or 1))
        return int(best_ask + tick)
    if best_ask > 0:
        return best_ask
    if curr > 0:
        return curr
    return best_bid


def indicative_open_snapshot(ws_data: dict[str, Any]) -> dict[str, Any]:
    expected = (ws_data or {}).get("expected_open") or {}
    expected_price = _safe_int(
        expected.get("price")
        or expected.get("expected_price")
        or (ws_data or {}).get("expected_open_price")
        or (ws_data or {}).get("indicative_open_price"),
        0,
    )
    expected_qty = _safe_int(
        expected.get("qty")
        or expected.get("expected_qty")
        or (ws_data or {}).get("expected_open_qty"),
        0,
    )
    if expected_price > 0:
        return {
            "indicative_open_price": expected_price,
            "indicative_open_source": expected.get("source") or "0D_expected_open",
            "explicit_expected_open_available": True,
            "expected_open_qty": expected_qty,
            "expected_open_meta": {
                "price_vs_prev": expected.get("price_vs_prev"),
                "price_vs_prev_rate": expected.get("price_vs_prev_rate"),
                "sign": expected.get("sign"),
                "volume_vs_prev_rate": expected.get("volume_vs_prev_rate"),
                "valid_during_expected_session": expected.get(
                    "valid_during_expected_session"
                ),
            },
        }
    return {
        "indicative_open_price": _safe_int((ws_data or {}).get("curr"), 0),
        "indicative_open_source": "ws_curr",
        "explicit_expected_open_available": False,
        "expected_open_qty": 0,
        "expected_open_meta": {},
    }


def calculate_entry_qty(budget_cap_krw: int, guarded_entry_price: int) -> int:
    if budget_cap_krw <= 0 or guarded_entry_price <= 0:
        return 0
    return max(1, int(budget_cap_krw // guarded_entry_price))


def effective_budget_cap_krw(budget_cap_krw: int) -> int:
    return max(0, min(_safe_int(budget_cap_krw), MAX_TARGET_BUDGET_CAP_KRW))


def top_depth_notional(ws_data: dict[str, Any], levels: int = 3) -> int:
    best_ask, _, asks, _ = best_levels(ws_data)
    if not asks and best_ask <= 0:
        return 0
    depth = 0
    for level in asks[: max(1, int(levels))]:
        price = _safe_int(level.get("price"), 0)
        qty = _safe_int(level.get("volume"), 0)
        depth += max(0, price * qty)
    return depth


def quote_age_sec(ws_data: dict[str, Any], now_ts: float | None = None) -> float | None:
    raw_ts = ws_data.get("last_ws_update_ts")
    if raw_ts in (None, "", 0):
        return None
    try:
        return max(0.0, float(now_ts or time.time()) - float(raw_ts))
    except (TypeError, ValueError):
        return None


def suspected_quote_vacuum(ws_data: dict[str, Any]) -> bool:
    curr = _safe_int(ws_data.get("curr"), 0)
    best_ask, best_bid, asks, bids = best_levels(ws_data)
    if curr <= 0 or best_ask <= 0 or best_bid <= 0:
        return True
    if not asks or not bids:
        return True
    tick = max(1, int(kiwoom_utils.get_tick_size(curr) or 1))
    spread_ticks = max(0, int(round((best_ask - best_bid) / tick)))
    return spread_ticks >= 8


def evaluate_entry_gate(
    target: IpoTarget,
    ws_data: dict[str, Any],
    *,
    now_ts: float | None = None,
    ai_result: dict[str, Any] | None = None,
) -> IpoDecision:
    price = planned_entry_price(ws_data)
    if price <= 0:
        return IpoDecision(False, "unpriced", {"entry_price": price})
    premium_pct = (
        (price / target.offer_price) * 100.0 if target.offer_price > 0 else 9999.0
    )
    if premium_pct > float(target.premium_guard_pct):
        return IpoDecision(
            False,
            "premium_guard",
            {
                "entry_price": price,
                "offer_price": target.offer_price,
                "premium_pct": round(premium_pct, 2),
            },
        )
    age = quote_age_sec(ws_data, now_ts=now_ts)
    if age is not None and age > 2.0:
        return IpoDecision(False, "quote_stale", {"quote_age_sec": round(age, 3)})
    if suspected_quote_vacuum(ws_data):
        return IpoDecision(
            False, "quote_vacuum_or_vi_suspected", {"entry_price": price}
        )
    effective_budget = effective_budget_cap_krw(target.budget_cap_krw)
    qty = calculate_entry_qty(effective_budget, price)
    if qty <= 0:
        return IpoDecision(
            False,
            "zero_qty",
            {
                "budget_cap_krw": target.budget_cap_krw,
                "effective_budget_cap_krw": effective_budget,
                "max_budget_cap_krw": MAX_TARGET_BUDGET_CAP_KRW,
                "entry_price": price,
            },
        )
    required_depth = effective_budget * 3
    observed_depth = top_depth_notional(ws_data, levels=3)
    if observed_depth < required_depth:
        return IpoDecision(
            False,
            "depth_gate",
            {
                "observed_depth_krw": observed_depth,
                "required_depth_krw": required_depth,
                "qty": qty,
                "budget_cap_krw": target.budget_cap_krw,
                "effective_budget_cap_krw": effective_budget,
                "max_budget_cap_krw": MAX_TARGET_BUDGET_CAP_KRW,
            },
        )
    risk_score = _safe_float((ai_result or {}).get("risk_score"), 0.0)
    if risk_score >= 80.0:
        return IpoDecision(
            False,
            "ai_risk_block",
            {"risk_score": risk_score, "ai_result": ai_result or {}},
        )
    return IpoDecision(
        True,
        "entry_allowed",
        {
            "entry_price": price,
            "qty": qty,
            "budget_cap_krw": target.budget_cap_krw,
            "effective_budget_cap_krw": effective_budget,
            "max_budget_cap_krw": MAX_TARGET_BUDGET_CAP_KRW,
            "premium_pct": round(premium_pct, 2),
            "observed_depth_krw": observed_depth,
            "quote_age_sec": None if age is None else round(age, 3),
            "ai_result": ai_result or {},
        },
    )


def current_profit_pct(position: IpoPosition, curr_price: int) -> float:
    if position.avg_price <= 0 or curr_price <= 0:
        return 0.0
    return ((curr_price / position.avg_price) - 1.0) * 100.0


def partial_take_profit_qty(qty: int, ratio: float = 0.30) -> int:
    if qty <= 0:
        return 0
    return max(1, int(math.ceil(qty * ratio)))


def evaluate_exit_action(
    position: IpoPosition,
    ws_data: dict[str, Any],
    *,
    now_dt: datetime,
    ai_result: dict[str, Any] | None = None,
) -> IpoDecision:
    curr = _safe_int(ws_data.get("curr"), 0)
    profit = current_profit_pct(position, curr)
    position.peak_profit_pct = max(position.peak_profit_pct, profit)
    held_sec = (
        0
        if position.entry_time is None
        else max(0, int((now_dt - position.entry_time).total_seconds()))
    )
    if profit <= -10.0:
        return IpoDecision(
            True,
            "hard_stop",
            {"sell_qty": position.qty, "profit_pct": round(profit, 3)},
        )
    if held_sec >= 30 * 60:
        return IpoDecision(
            True, "max_hold_time", {"sell_qty": position.qty, "held_sec": held_sec}
        )
    if position.first_partial_taken and profit <= position.peak_profit_pct - 8.0:
        return IpoDecision(
            True,
            "post_tp_trailing",
            {
                "sell_qty": position.qty,
                "profit_pct": round(profit, 3),
                "peak_profit_pct": round(position.peak_profit_pct, 3),
            },
        )
    if not position.first_partial_taken and profit >= 20.0:
        hold_confidence = _safe_float((ai_result or {}).get("hold_confidence"), 0.0)
        reasons = (
            ai_result.get("continuation_reasons") if isinstance(ai_result, dict) else []
        )
        reason_count = len(reasons) if isinstance(reasons, list) else 0
        if hold_confidence >= 75.0 and reason_count >= 2:
            return IpoDecision(
                False,
                "ai_defer_partial_tp",
                {"profit_pct": round(profit, 3), "ai_result": ai_result},
            )
        return IpoDecision(
            True,
            "partial_take_profit_20pct",
            {
                "sell_qty": partial_take_profit_qty(position.qty),
                "profit_pct": round(profit, 3),
                "ai_result": ai_result or {},
            },
        )
    return IpoDecision(
        False, "hold", {"profit_pct": round(profit, 3), "held_sec": held_sec}
    )


class IpoAiAdvisor:
    def __init__(
        self,
        engine: Any | None = None,
        *,
        max_calls_per_symbol: int = 6,
        max_calls_per_run: int = 10,
    ):
        self.engine = engine
        self.max_calls_per_symbol = max(0, int(max_calls_per_symbol))
        self.max_calls_per_run = max(0, int(max_calls_per_run))
        self.calls_by_symbol: dict[str, int] = {}
        self.total_calls = 0

    def _can_call(self, code: str) -> bool:
        return (
            self.engine is not None
            and self.total_calls < self.max_calls_per_run
            and self.calls_by_symbol.get(code, 0) < self.max_calls_per_symbol
        )

    def review_entry(
        self,
        target: IpoTarget,
        ws_data: dict[str, Any],
        candle_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._call(
            "ipo_entry_risk",
            target,
            ws_data,
            {"entry_candle_context": candle_context or {}},
        )

    def review_exit(
        self, target: IpoTarget, ws_data: dict[str, Any], position: IpoPosition
    ) -> dict[str, Any]:
        return self._call(
            "ipo_exit_hold", target, ws_data, {"position": position.__dict__}
        )

    def _call(
        self,
        mode: str,
        target: IpoTarget,
        ws_data: dict[str, Any],
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._can_call(target.code):
            return {"ai_status": "skipped", "reason": "call_cap_or_unavailable"}
        self.total_calls += 1
        self.calls_by_symbol[target.code] = self.calls_by_symbol.get(target.code, 0) + 1
        payload = {
            "mode": mode,
            "target": target.__dict__,
            "ws_data": ws_data,
            "extra": extra or {},
            "required_output": {
                "entry": {
                    "risk_score": "0-100",
                    "risk_flags": ["string"],
                    "reason": "string",
                },
                "exit": {
                    "hold_confidence": "0-100",
                    "continuation_reasons": ["string"],
                    "reason": "string",
                },
            },
        }
        prompt = (
            "You are an IPO listing-day risk reviewer. Return JSON only. "
            "For entry, block only clear tail-risk situations via risk_score. "
            "For exit, defer 20% partial take-profit only with strong continuation evidence."
        )
        try:
            if hasattr(self.engine, "_call_openai_safe"):
                result = self.engine._call_openai_safe(
                    prompt,
                    json.dumps(payload, ensure_ascii=False),
                    require_json=True,
                    context_name=f"ipo_listing_day_{mode}",
                    model_override=getattr(self.engine, "report_model_name", None),
                    endpoint_name="ipo_listing_day",
                    symbol=target.code,
                    cache_key=f"{mode}:{target.code}",
                )
                return (
                    result if isinstance(result, dict) else {"ai_status": "parse_fail"}
                )
        except Exception as exc:
            return {"ai_status": "error", "error": str(exc)[:180]}
        return {"ai_status": "unavailable"}


class IpoListingDayEngine:
    def __init__(
        self,
        config: IpoRunConfig,
        *,
        token: str,
        ws_manager: Any,
        ai_advisor: IpoAiAdvisor | None = None,
        artifact_writer: IpoArtifactWriter | None = None,
        stop_file: Path = STOP_FILE,
        now_func: Callable[[], datetime] | None = None,
    ):
        self.config = config
        self.token = token
        self.ws_manager = ws_manager
        self.ai_advisor = ai_advisor or IpoAiAdvisor(None)
        self.artifacts = artifact_writer or IpoArtifactWriter(
            trade_date=config.trade_date
        )
        self.stop_file = Path(stop_file)
        self.now_func = now_func or datetime.now
        self.order_failures = 0
        self.daily_realized_pnl_krw = 0
        self.positions: dict[str, IpoPosition] = {}
        self.completed_codes: set[str] = set()
        self.completed_pnl_by_code: dict[str, int] = {}

    def kill_switch_active(self) -> IpoDecision:
        if self.stop_file.exists():
            return IpoDecision(
                True, "manual_stop_file", {"stop_file": str(self.stop_file)}
            )
        if self.daily_realized_pnl_krw <= -abs(
            int(self.config.global_daily_loss_cap_krw)
        ):
            return IpoDecision(
                True,
                "daily_loss_cap",
                {"daily_realized_pnl_krw": self.daily_realized_pnl_krw},
            )
        if self.order_failures >= int(self.config.max_order_failures):
            return IpoDecision(
                True, "order_failure_cap", {"order_failures": self.order_failures}
            )
        return IpoDecision(False, "ok", {})

    def subscribe_targets(self, targets: list[IpoTarget]) -> None:
        codes = [target.code for target in targets]
        if hasattr(self.ws_manager, "execute_subscribe"):
            self.ws_manager.execute_subscribe(codes)
        self.artifacts.event("ipo_ws_subscribe_requested", codes=codes)

    def maybe_enter(
        self,
        target: IpoTarget,
        ws_data: dict[str, Any],
        *,
        now_dt: datetime | None = None,
    ) -> IpoDecision:
        now_dt = now_dt or self.now_func()
        if target.code in self.completed_codes or target.code in self.positions:
            return IpoDecision(False, "reentry_blocked", {"code": target.code})
        kill = self.kill_switch_active()
        if kill.allowed:
            return IpoDecision(False, kill.reason, kill.fields)
        if is_buy_side_paused():
            return IpoDecision(False, "global_buy_pause", {})
        if not (ENTRY_START <= now_dt.time() <= ENTRY_END):
            return IpoDecision(
                False, "outside_entry_window", {"now": now_dt.isoformat()}
            )
        candle_context = {}
        if entry_candle_context_enabled(
            venue="KRX",
            session="krx_regular",
            now_ts=now_dt,
        ):
            try:
                candles, candle_source_meta = fetch_entry_candles_with_meta(
                    self.token,
                    target.code,
                    ws_data,
                    venue="KRX",
                    session="krx_regular",
                    limit=40,
                    now_ts=now_dt,
                )
                candle_context = build_entry_candle_context(
                    self.token,
                    target.code,
                    ws_data,
                    venue="KRX",
                    session="krx_regular",
                    limit=40,
                    model_bar_limit=20,
                    now_ts=now_dt,
                    recent_candles=candles,
                    source_meta=candle_source_meta,
                )
            except Exception:
                candle_context = {}
        review_entry = self.ai_advisor.review_entry
        if "candle_context" in inspect.signature(review_entry).parameters:
            ai_result = review_entry(target, ws_data, candle_context=candle_context)
        else:
            ai_result = review_entry(target, ws_data)
        decision = evaluate_entry_gate(
            target, ws_data, now_ts=now_dt.timestamp(), ai_result=ai_result
        )
        self.artifacts.decision(target.code, decision)
        self.artifacts.event(
            "ipo_entry_gate",
            code=target.code,
            allowed=decision.allowed,
            reason=decision.reason,
            **decision.fields,
        )
        if not decision.allowed:
            if decision.reason in {
                "premium_guard",
                "ai_risk_block",
                "quote_vacuum_or_vi_suspected",
            }:
                self.completed_codes.add(target.code)
            return decision
        qty = int(decision.fields.get("qty", 0) or 0)
        price = int(decision.fields.get("entry_price", 0) or 0)
        order_decision = self._send_entry_order(
            target, qty=qty, price=price, retry=False, ws_data=ws_data
        )
        if order_decision.allowed:
            return order_decision
        retry_price = planned_entry_price(ws_data, retry=True)
        if retry_price > 0:
            return self._send_entry_order(
                target, qty=qty, price=retry_price, retry=True, ws_data=ws_data
            )
        return order_decision

    def _send_entry_order(
        self,
        target: IpoTarget,
        *,
        qty: int,
        price: int,
        retry: bool,
        ws_data: dict[str, Any],
    ) -> IpoDecision:
        res = kiwoom_orders.send_buy_order(
            target.code,
            qty,
            price,
            "16" if retry else "6",
            token=self.token,
            order_type_desc="IPO_LISTING_DAY_ENTRY",
            tif="IOC" if retry else None,
        )
        if (
            not isinstance(res, dict)
            or str(res.get("return_code", res.get("rt_cd", ""))) != "0"
        ):
            self.order_failures += 1
            reason = (
                "entry_order_failed"
                if isinstance(res, dict)
                else "entry_order_no_response"
            )
            self.artifacts.event(
                "ipo_entry_order_failed",
                code=target.code,
                qty=qty,
                price=price,
                retry=retry,
                response=res,
            )
            if not retry:
                return IpoDecision(
                    False, reason, {"retry_allowed": True, "response": res or {}}
                )
            self.completed_codes.add(target.code)
            return IpoDecision(
                False, reason, {"retry_allowed": False, "response": res or {}}
            )
        fill_price = _safe_int(ws_data.get("curr"), price) or price
        position = IpoPosition(
            code=target.code,
            name=target.name,
            qty=qty,
            avg_price=fill_price,
            entry_time=self.now_func(),
            peak_profit_pct=0.0,
            reentry_blocked=True,
        )
        self.positions[target.code] = position
        self.artifacts.event(
            "ipo_entry_order_submitted",
            code=target.code,
            qty=qty,
            price=price,
            assumed_fill_price=fill_price,
            retry=retry,
            response=res,
            actual_order_submitted=True,
        )
        return IpoDecision(
            True, "entry_submitted", {"qty": qty, "price": price, "response": res}
        )

    def evaluate_and_exit(
        self,
        target: IpoTarget,
        ws_data: dict[str, Any],
        *,
        now_dt: datetime | None = None,
    ) -> IpoDecision:
        now_dt = now_dt or self.now_func()
        position = self.positions.get(target.code)
        if position is None or position.closed or position.qty <= 0:
            return IpoDecision(False, "no_open_position", {})
        profit = current_profit_pct(position, _safe_int(ws_data.get("curr"), 0))
        ai_result: dict[str, Any] | None = None
        if profit >= 20.0 and not position.first_partial_taken:
            ai_result = self.ai_advisor.review_exit(target, ws_data, position)
        decision = evaluate_exit_action(
            position, ws_data, now_dt=now_dt, ai_result=ai_result
        )
        self.artifacts.event(
            "ipo_exit_gate",
            code=target.code,
            allowed=decision.allowed,
            reason=decision.reason,
            **decision.fields,
        )
        if not decision.allowed:
            return decision
        sell_qty = min(
            position.qty,
            int(decision.fields.get("sell_qty", position.qty) or position.qty),
        )
        return self._send_exit_order(
            target, position, ws_data, sell_qty=sell_qty, reason=decision.reason
        )

    def _send_exit_order(
        self,
        target: IpoTarget,
        position: IpoPosition,
        ws_data: dict[str, Any],
        *,
        sell_qty: int,
        reason: str,
    ) -> IpoDecision:
        res = kiwoom_orders.send_smart_sell_order(
            target.code, sell_qty, self.token, ws_data, reason
        )
        if (
            not isinstance(res, dict)
            or str(res.get("return_code", res.get("rt_cd", ""))) != "0"
        ):
            self.order_failures += 1
            self.artifacts.event(
                "ipo_exit_order_failed",
                code=target.code,
                qty=sell_qty,
                reason=reason,
                response=res,
            )
            return IpoDecision(False, "exit_order_failed", {"response": res or {}})
        sell_price = _safe_int(ws_data.get("curr"), position.avg_price)
        realized = int((sell_price - position.avg_price) * sell_qty)
        position.realized_pnl_krw += realized
        self.daily_realized_pnl_krw += realized
        position.qty -= sell_qty
        if reason == "partial_take_profit_20pct" and position.qty > 0:
            position.first_partial_taken = True
        if position.qty <= 0:
            position.closed = True
            self.completed_pnl_by_code[target.code] = position.realized_pnl_krw
            self.completed_codes.add(target.code)
            self.positions.pop(target.code, None)
        self.artifacts.event(
            "ipo_exit_order_submitted",
            code=target.code,
            qty=sell_qty,
            reason=reason,
            sell_price=sell_price,
            realized_pnl_krw=realized,
            remaining_qty=position.qty,
            actual_order_submitted=True,
            response=res,
        )
        return IpoDecision(
            True,
            "exit_submitted",
            {"sell_qty": sell_qty, "reason": reason, "realized_pnl_krw": realized},
        )

    def run_until_done(
        self, targets: list[IpoTarget], *, poll_sec: float = 0.2
    ) -> None:
        self.subscribe_targets(targets)
        active = targets[:1]
        try:
            while active:
                now_dt = self.now_func()
                if now_dt.time() < PREOPEN_MONITOR_START:
                    time.sleep(min(poll_sec, 1.0))
                    continue
                target = active[0]
                ws_data = (
                    self.ws_manager.get_latest_data(target.code)
                    if hasattr(self.ws_manager, "get_latest_data")
                    else {}
                )
                self.artifacts.event(
                    "ipo_preopen_or_live_snapshot",
                    code=target.code,
                    **indicative_open_snapshot(ws_data),
                    session_state=ws_data.get("market_session_state", ""),
                )
                if (
                    target.code not in self.positions
                    and target.code not in self.completed_codes
                ):
                    self.maybe_enter(target, ws_data, now_dt=now_dt)
                if target.code in self.positions:
                    self.evaluate_and_exit(target, ws_data, now_dt=now_dt)
                if (
                    target.code in self.completed_codes
                    or self.kill_switch_active().allowed
                ):
                    position = self.positions.get(target.code)
                    self.artifacts.add_summary(
                        {
                            "code": target.code,
                            "name": target.name,
                            "status": (
                                "completed"
                                if target.code in self.completed_codes
                                else "stopped"
                            ),
                            "realized_pnl_krw": self.completed_pnl_by_code.get(
                                target.code,
                                0 if position is None else position.realized_pnl_krw,
                            ),
                            "reason": self.kill_switch_active().reason,
                        }
                    )
                    active.pop(0)
                if (
                    now_dt.time() > dt_time(9, 31, 0)
                    and target.code not in self.positions
                ):
                    self.completed_codes.add(target.code)
                time.sleep(poll_sec)
        finally:
            self.artifacts.write_summary()


def build_openai_advisor(conf: dict[str, Any], config: IpoRunConfig) -> IpoAiAdvisor:
    keys = [v for k, v in conf.items() if str(k).startswith("OPENAI_API_KEY") and v]
    if not keys:
        return IpoAiAdvisor(
            None,
            max_calls_per_symbol=config.max_ai_calls_per_symbol,
            max_calls_per_run=config.max_ai_calls_per_run,
        )
    engine = GPTSniperEngine(api_keys=keys, announce_startup=False)
    return IpoAiAdvisor(
        engine,
        max_calls_per_symbol=config.max_ai_calls_per_symbol,
        max_calls_per_run=config.max_ai_calls_per_run,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IPO listing-day spread capture runner."
    )
    parser.add_argument(
        "--config", required=True, help="Path to IPO listing-day YAML config."
    )
    parser.add_argument("--poll-sec", type=float, default=0.2)
    parser.add_argument(
        "--dry-select",
        action="store_true",
        help="Validate config and selected targets without starting WS/orders.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_ipo_config(args.config)
    targets = select_enabled_targets(config)
    if args.dry_select:
        print(
            json.dumps(
                {
                    "trade_date": config.trade_date,
                    "targets": [target.__dict__ for target in targets],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if targets else 1
    if not targets:
        log_info("IPO runner: no enabled target for trade_date")
        return 1
    conf = load_json_config()
    token = kiwoom_utils.get_kiwoom_token(conf)
    if not token:
        log_error("IPO runner: Kiwoom token unavailable")
        return 2
    ws_manager = KiwoomWSManager(token)
    ws_manager.start()
    try:
        advisor = build_openai_advisor(conf, config)
        engine = IpoListingDayEngine(
            config,
            token=token,
            ws_manager=ws_manager,
            ai_advisor=advisor,
            artifact_writer=IpoArtifactWriter(trade_date=config.trade_date),
        )
        engine.run_until_done(targets, poll_sec=max(0.05, float(args.poll_sec)))
    finally:
        try:
            ws_manager.stop()
        except Exception as exc:
            log_error(f"IPO runner WS stop failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
