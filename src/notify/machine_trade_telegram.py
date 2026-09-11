"""Read-only widget/episode fill journal consumer; no broker or strategy calls."""
from __future__ import annotations

import argparse
import fcntl
import json
import logging
import math
import os
from pathlib import Path
import time
from urllib import error, parse, request

from src.trading.order.owner_custody_registry import OrderOwnerRegistry
from src.utils.constants import CONFIG_PATH, PROJECT_ROOT

LOG = logging.getLogger(__name__)
SCHEMA = "machine_fill_telegram_v2"
FILL_EVENTS = {
    "FILL_RECORDED", "SELL_AMEND_RECONCILED",
    "PARTIAL_CANCEL_TARGET_FILL_REFRESHED", "SELL_PARTIAL_CANCEL_RECONCILED",
    "BUY_TERMINAL_CANCEL_RECONCILED", "SELL_TERMINAL_CANCEL_RECONCILED",
}
OWNERS = {"widget_auto_trade", "episode"}


class RejectedDelivery(Exception):
    """Telegram explicitly rejected delivery, so bounded retry is safe."""

    def __init__(self, reason: str, retry_after: int = 30):
        super().__init__(reason)
        self.retry_after = max(30, retry_after)


def telegram_config() -> tuple[str, str]:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("config_invalid")
    except (OSError, ValueError):
        raise RejectedDelivery("telegram_config_invalid") from None
    token, chat = config.get("TELEGRAM_TOKEN"), config.get("ADMIN_ID")
    if not token or not chat:
        raise RejectedDelivery("telegram_config_missing")
    return str(token), str(chat)


def send_telegram(message: str) -> int:
    token, chat = telegram_config()
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=parse.urlencode({"chat_id": chat, "text": message}).encode(),
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read())
    except error.HTTPError as exc:
        # Only an explicit API rejection is safe to retry. Do not log URLs/tokens.
        try:
            payload = json.loads(exc.read())
        except (ValueError, OSError):
            raise RuntimeError("telegram_delivery_uncertain") from None
    if payload.get("ok") is False:
        raise RejectedDelivery("telegram_api_rejected", int(payload.get("parameters", {}).get("retry_after", 30)))
    message_id = payload.get("result", {}).get("message_id")
    if payload.get("ok") is not True or type(message_id) is not int or message_id <= 0:
        raise RuntimeError("telegram_delivery_uncertain")
    return message_id


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_events(registry: OrderOwnerRegistry) -> list[dict]:
    # Existing producer lock, read-only and nonblocking. Never lock during HTTP.
    if not registry.path.is_file():
        raise RuntimeError("registry_missing")
    with registry.lock_path.open("r") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        return registry._read_locked()


def initialize(path: Path, events: list[dict], account_key: str) -> None:
    if not account_key:
        raise RuntimeError("notification_account_missing")
    if path.exists():
        raise RuntimeError("notification_state_already_exists")
    save(path, {"schema": SCHEMA, "cursor": len(events),
                "source_hash": events[-1]["event_hash"] if events else "0" * 64,
                "deliveries": {}, "account_key": account_key, "initialized_at": time.time()})


def _nonnegative_number(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and value >= 0


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def load(path: Path, *, recover_inflight: bool = True) -> dict:
    state = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(state, dict) or state.get("schema") != SCHEMA
            or type(state.get("cursor")) is not int or state["cursor"] < 0
            or not isinstance(state.get("account_key"), str) or not state["account_key"]
            or not _sha256(state.get("source_hash"))
            or not _nonnegative_number(state.get("next_delivery_at", 0))
            or not isinstance(state.get("deliveries"), dict)):
        raise RuntimeError("notification_state_invalid")
    sequences = set()
    for delivery in state["deliveries"].values():
        if (not isinstance(delivery, dict)
                or delivery.get("status") not in {"pending", "sending", "sent", "uncertain", "failed"}
                or not isinstance(delivery.get("message"), str) or not delivery["message"]
                or not _sha256(delivery.get("source_hash"))
                or type(delivery.get("sequence")) is not int
                or delivery["sequence"] < 0 or delivery["sequence"] in sequences
                or type(delivery.get("attempts")) is not int or not 0 <= delivery["attempts"] <= 3
                or not _nonnegative_number(delivery.get("next_attempt"))):
            raise RuntimeError("notification_delivery_invalid")
        sequences.add(delivery["sequence"])
        status, attempts = delivery["status"], delivery["attempts"]
        if ((status == "pending" and attempts >= 3)
                or (status != "pending" and attempts == 0)
                or (status == "sent" and (type(delivery.get("message_id")) is not int
                                           or delivery["message_id"] <= 0))):
            raise RuntimeError("notification_delivery_receipt_invalid")
        if recover_inflight and status == "sending":
            # Only the new exclusive service owner can conclude the prior sender died.
            # An unlocked read-only health check may see an active HTTP request.
            delivery["status"] = "uncertain"
    return state


def collect(state: dict, events: list[dict]) -> None:
    cursor = state["cursor"]
    if (cursor > len(events) or state["source_hash"] !=
            (events[cursor - 1]["event_hash"] if cursor else "0" * 64)):
        raise RuntimeError("registry_rewritten_or_truncated")
    if cursor == len(events):
        return
    origins = {}
    for event in events:
        origins.setdefault(event.get("intent_id"), event.get("event"))
    before = OrderOwnerRegistry._state(events[:cursor])
    for index in range(cursor, len(events)):
        event = events[index]
        after = OrderOwnerRegistry._state(events[:index + 1])
        if event.get("event") in FILL_EVENTS:
            ids = [event.get("intent_id")]
            if event.get("event") == "SELL_AMEND_RECONCILED":
                ids.append(event.get("amendment_parent_intent_id"))
            for intent in ids:
                row = after.get(intent, {})
                if (origins.get(intent) != "INTENT_RESERVED"
                        or row.get("owner_type") not in OWNERS
                        or row.get("account_key") != state["account_key"]
                        or row.get("action") != "NEW"
                        or row.get("side") not in {"BUY", "SELL"}
                        or not row.get("broker_order_no")):
                    continue
                old = before.get(intent, {}).get("filled_qty", 0)
                new, total = row.get("filled_qty", 0), row.get("quantity")
                if (type(old) is not int or type(new) is not int
                        or type(total) is not int or not 0 <= old <= new <= total):
                    raise RuntimeError("fill_quantity_invalid")
                if new == old:
                    continue  # amount-only refresh and replay are not fills
                side = "매수" if row["side"] == "BUY" else "매도"
                owner = "위젯" if row["owner_type"] == "widget_auto_trade" else "에피소드"
                status = "전량체결" if new == total else "부분체결"
                # Quantity is authoritative even when broker amounts arrive later.
                # Do not print a stale average or a fabricated zero fill price/PnL.
                message = (f"[{owner} {side} 체결] {row['symbol']}\n"
                           f"이번 체결 {new - old}주 · 누적 {new}/{total}주 ({status})\n"
                           f"기계: {row['owner_id']}\n주문: {row['broker_order_no']}\n"
                           f"체결 확인: {event['observed_at_kst']}")
                key = f"{intent}:{new}"
                state["deliveries"].setdefault(key, {
                    "status": "pending", "message": message, "source_hash": event["event_hash"],
                    "attempts": 0, "next_attempt": 0, "sequence": len(state["deliveries"]),
                })
        before = after
    state["cursor"] = len(events)
    state["source_hash"] = events[-1]["event_hash"] if events else "0" * 64


def deliver(path: Path, state: dict, sender=send_telegram, now=time.time) -> None:
    # One attempt per poll prevents bursts. Explicit rejections: max 3, 30s apart.
    if state.get("next_delivery_at", 0) > now():
        return
    for key, row in sorted(state["deliveries"].items(), key=lambda item: item[1]["sequence"]):
        if row["status"] != "pending" or row["next_attempt"] > now():
            continue
        row.update(status="sending", attempts=row["attempts"] + 1)
        save(path, state)
        try:
            message_id = sender(row["message"])
            if type(message_id) is not int or message_id <= 0:
                raise RuntimeError("telegram_receipt_missing")
        except RejectedDelivery as exc:
            row.update(status="pending" if row["attempts"] < 3 else "failed",
                       next_attempt=now() + exc.retry_after)
            state["next_delivery_at"] = now() + exc.retry_after
            LOG.error("fill_notification_rejected key=%s attempt=%s", key, row["attempts"])
        except Exception:
            row["status"] = "uncertain"
            LOG.error("fill_notification_delivery_uncertain key=%s", key)
        else:
            row.update(status="sent", message_id=message_id, sent_at=now())
            LOG.info("fill_notification_sent key=%s message_id=%s", key, message_id)
        save(path, state)
        break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=PROJECT_ROOT / "data/runtime/order_owner_registry.jsonl")
    parser.add_argument("--state", type=Path, default=PROJECT_ROOT / "data/runtime/machine_fill_telegram/state.json")
    parser.add_argument("--account-key", required=True, help="Exact production registry account alias, not an account number")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--initialize", action="store_true", help="Baseline existing fills without sending; never overwrite state")
    mode.add_argument("--check", action="store_true", help="Validate source/cursor without sending or writing")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    registry = OrderOwnerRegistry(args.registry)
    telegram_config()  # Local preflight only; never send a test message.
    if args.check:
        state = load(args.state, recover_inflight=False)  # active sender is not a crash
        if state["account_key"] != args.account_key:
            raise RuntimeError("notification_account_changed")
        collect(state, read_events(registry))
        print(json.dumps({"cursor": state["cursor"], "deliveries": len(state["deliveries"]),
                          "inflight": sum(d["status"] == "sending" for d in state["deliveries"].values()),
                          "unresolved": sum(d["status"] in {"uncertain", "failed"} for d in state["deliveries"].values())}))
        return
    args.state.parent.mkdir(parents=True, exist_ok=True)
    with args.state.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.initialize:
            initialize(args.state, read_events(registry), args.account_key)
            return
        state = load(args.state)  # missing/corrupt state never silently rebaselines
        if state["account_key"] != args.account_key:
            raise RuntimeError("notification_account_changed")
        save(args.state, state)
        LOG.info("fill_notification_started cursor=%s", state["cursor"])
        last_warning = 0.0
        while True:
            previous_cursor = state["cursor"]
            try:
                collect(state, read_events(registry))
            except BlockingIOError:
                time.sleep(5)
                continue
            if state["cursor"] != previous_cursor:
                save(args.state, state)
            deliver(args.state, state)
            if time.monotonic() - last_warning >= 60:
                unresolved = sum(d["status"] in {"uncertain", "failed"} for d in state["deliveries"].values())
                if unresolved:
                    LOG.error("fill_notification_delivery_unresolved count=%s", unresolved)
                last_warning = time.monotonic()
            time.sleep(5)


if __name__ == "__main__":
    main()
