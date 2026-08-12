"""Admin-only Telegram delivery for accepted widget auto-trade BUY actions.

The notifier consumes an already broker-accepted order record.  It does not
evaluate signals, submit orders, query accounts, or alter execution state.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib import parse, request

from src.engine.monitoring.samsung_widget_contract import KST
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_PATH = (
    PROJECT_ROOT / "tmp" / "widget_auto_trade_entry_telegram_state.json"
)
DEFAULT_RETRY_SEC = 30
DEFAULT_ACTION_MAX_AGE_SEC = 300
MAX_DELIVERY_ROWS = 200
SUPPORTED_BUY_ROLES = frozenset({"ENTRY_BUY", "SCALE_IN_BUY"})
DEFAULT_ALLOWED_SYMBOLS = frozenset(
    {"005930", "034020", "042660", "006800", "010140", "080220", "475150"}
)

ConfigLoader = Callable[[], tuple[str, str]]
Sender = Callable[[str, str, str], None]


def _env_enabled() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_TELEGRAM_ENABLED", "false")
    ).strip().lower() in {"1", "true", "yes", "on"}


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=5) as response:
        response.read()


def _as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=KST)
    return value.astimezone(KST)


def _parse_timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return _as_kst(parsed)


def _load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def build_buy_action_message(
    *,
    symbol: str,
    name: str,
    order: dict[str, Any],
    execution_policy_id: str | None,
    observed_at: datetime,
) -> str:
    """Render an accepted-order notice without claiming that it filled."""
    order_role = str(order.get("order_role") or "")
    leg_index = int(order.get("scale_in_leg_index") or 0)
    action_label = (
        f"추가매수 {leg_index}차" if order_role == "SCALE_IN_BUY" else "최초 진입"
    )
    order_type = "시장가" if order.get("limit_price") in {None, "", 0} else "지정가"
    submitted_at = _parse_timestamp(order.get("submitted_at")) or _as_kst(observed_at)
    lines = [
        f"🟠 [{name} 자동매매 매수 주문 접수]",
        f"구분: {action_label}",
        f"종목: {name} ({symbol})",
        f"주문수량: {int(order.get('requested_qty') or 0)}주",
        f"주문방식: {order_type}",
        (
            f"시장/라우팅: {order.get('market_venue') or '-'} / "
            f"{order.get('broker_route') or order.get('route') or '-'}"
        ),
        f"주문번호: {order.get('order_no') or '-'}",
        f"원천상태: {order.get('source_advisory_state') or '-'}",
        f"원천신호: {order.get('signal_id') or '-'}",
        f"실행정책: {execution_policy_id or '-'}",
        f"접수시각: {submitted_at.strftime('%H:%M:%S')}",
        "권한: 실주문 접수 · 체결 여부는 broker reconciliation 기준",
    ]
    return "\n".join(lines)


class WidgetAutoTradeEntryTelegramNotifier:
    """Deliver each accepted widget BUY order once, with bounded retries."""

    def __init__(
        self,
        *,
        state_path: Path = DEFAULT_STATE_PATH,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        retry_sec: int = DEFAULT_RETRY_SEC,
        action_max_age_sec: int = DEFAULT_ACTION_MAX_AGE_SEC,
        enabled: bool | None = None,
        allowed_symbols: frozenset[str] = DEFAULT_ALLOWED_SYMBOLS,
    ) -> None:
        self.state_path = state_path
        self.config_loader = config_loader
        self.sender = sender
        self.retry_sec = max(1, int(retry_sec))
        self.action_max_age_sec = max(1, int(action_max_age_sec))
        self.enabled = _env_enabled() if enabled is None else bool(enabled)
        self.allowed_symbols = allowed_symbols
        self._state = _load_state(state_path)
        if self._state.get("schema_version") != 1:
            self._state = {"schema_version": 1, "deliveries": {}}
        deliveries = self._state.get("deliveries")
        if not isinstance(deliveries, dict):
            self._state["deliveries"] = {}
        else:
            self._state["deliveries"] = {
                str(key): value
                for key, value in deliveries.items()
                if isinstance(value, dict)
            }

    @staticmethod
    def _delivery_key(symbol: str, order: dict[str, Any]) -> str:
        return ":".join(
            [
                str(order.get("order_date") or "unknown_date"),
                symbol,
                str(order.get("order_role") or "unknown_role"),
                str(order.get("order_no") or "missing_order_no"),
            ]
        )

    def _save(self) -> None:
        deliveries = self._state.get("deliveries")
        if isinstance(deliveries, dict) and len(deliveries) > MAX_DELIVERY_ROWS:
            ordered = sorted(
                deliveries.items(),
                key=lambda item: str((item[1] or {}).get("last_attempt_at") or ""),
            )
            self._state["deliveries"] = dict(ordered[-MAX_DELIVERY_ROWS:])
        _atomic_write(self.state_path, self._state)

    def notify_order_accepted(
        self,
        *,
        symbol: str,
        name: str,
        order: dict[str, Any],
        execution_policy_id: str | None,
        observed_at: datetime,
    ) -> str:
        if not self.enabled:
            return "disabled"
        if symbol not in self.allowed_symbols:
            return "symbol_not_enabled"
        if (
            order.get("side") != "BUY"
            or order.get("broker_accepted") is not True
            or str(order.get("order_role") or "") not in SUPPORTED_BUY_ROLES
            or not str(order.get("order_no") or "").strip()
        ):
            return "not_accepted_buy_action"

        now = _as_kst(observed_at)
        submitted_at = _parse_timestamp(order.get("submitted_at"))
        action_age_sec = (
            (now - submitted_at).total_seconds() if submitted_at is not None else None
        )
        if (
            action_age_sec is None
            or action_age_sec < 0
            or action_age_sec > self.action_max_age_sec
        ):
            return "stale_action_not_notified"
        delivery_key = self._delivery_key(symbol, order)
        deliveries = self._state.setdefault("deliveries", {})
        delivery = deliveries.get(delivery_key)
        delivery = delivery if isinstance(delivery, dict) else {}
        if delivery.get("status") == "sent":
            return "duplicate"
        last_attempt_at = _parse_timestamp(delivery.get("last_attempt_at"))
        if (
            last_attempt_at is not None
            and (now - last_attempt_at).total_seconds() < self.retry_sec
        ):
            return "retry_wait"

        delivery.update(
            {
                "last_attempt_at": now.isoformat(),
                "symbol": symbol,
                "order_no": order.get("order_no"),
                "order_role": order.get("order_role"),
                "execution_authority": "operator_directed_widget_auto_trade_v1",
                "actual_order_submitted": True,
                "telegram_audience": "ADMIN_ONLY",
            }
        )
        token, admin_id = self.config_loader()
        if not token or not admin_id:
            delivery["status"] = "missing_config"
            deliveries[delivery_key] = delivery
            self._save()
            return "missing_config"
        try:
            self.sender(
                token,
                admin_id,
                build_buy_action_message(
                    symbol=symbol,
                    name=name,
                    order=order,
                    execution_policy_id=execution_policy_id,
                    observed_at=now,
                ),
            )
        except Exception as exc:
            delivery["status"] = "failed"
            delivery["error"] = type(exc).__name__
            deliveries[delivery_key] = delivery
            self._save()
            return "send_failed"

        delivery.update(
            {
                "status": "sent",
                "sent_at": now.isoformat(),
                "error": None,
            }
        )
        deliveries[delivery_key] = delivery
        self._save()
        return "sent"
