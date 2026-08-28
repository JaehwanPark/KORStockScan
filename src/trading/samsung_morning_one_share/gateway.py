"""Shared-token-only Kiwoom gateway for the independent one-share machine.

This module owns no token lifecycle and imports no KORStockScan entry, holding,
exit, ADM, LDM, sizing, or strategy code. Normal machine writes remain hard
limited to one share of 005930. The separately named manual-add-on methods are
bounded to at most 50 shares and are not used by the normal machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests

from src.engine.sniper_config import CONF
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.episode_quantity import (
    EPISODE_LEG_QUANTITY,
    validate_owned_leg_quantity,
    validate_position_quantity,
)
from src.trading.order.entry_liquidity_guard import (
    REQUIRED_RECENT_PRINT_COUNT,
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
    entry_liquidity_request_code,
    parse_ka10003_entry_execution_velocity_snapshot,
    parse_ka10004_entry_liquidity_snapshot,
    unavailable_entry_execution_velocity_snapshot,
    unavailable_entry_liquidity_snapshot,
)
from src.trading.order.kiwoom_episode_read_control import (
    EPISODE_READ_API_IDS,
    KT00007_API_ID,
    KiwoomEpisodeReadPacer,
    SameMinuteSnapshotCache,
    ShortTtlSnapshotCache,
    post_kiwoom_episode_read,
    snapshot_contains_latest_completed_minute,
)
from src.trading.order.tick_utils import get_tick_size
from src.trading.samsung_morning_one_share.policy import MinuteBar
from src.utils import kiwoom_utils

OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-20T15:34:48+09:00",
    "inspected_paths": [
        "kiwoom_docs/주문.md",
        "kiwoom_docs/계좌.md",
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["ka10080", "kt10000", "kt10001", "kt10003", "kt00007"],
    "delegated_request_scope": {
        "ka10003": (
            "src.trading.order.entry_liquidity_guard."
            "KIWOOM_EXECUTION_VELOCITY_OFFICIAL_REFERENCE"
        ),
        "ka10004": "src.trading.order.entry_liquidity_guard.KIWOOM_OFFICIAL_REFERENCE",
    },
}
KST = ZoneInfo("Asia/Seoul")

TokenLoader = Callable[[], str | None]


@dataclass(frozen=True)
class SubmitResult:
    accepted: bool
    order_no: str = ""
    return_code: str = ""
    return_msg: str = ""
    ambiguous: bool = False


@dataclass(frozen=True)
class ExecutionSnapshot:
    source_ok: bool
    found: bool
    filled_qty: int
    remaining_qty: int
    order_qty: int
    fill_price: int | None = None
    error: str = ""


@dataclass(frozen=True)
class OpenPriceSnapshot:
    source_ok: bool
    price: int | None = None
    source_timestamp: str = ""
    error: str = ""


@dataclass(frozen=True)
class MinuteBarsSnapshot:
    source_ok: bool
    bars: tuple[MinuteBar, ...] = ()
    error: str = ""


def _positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, abs(int(float(str(value or "0").replace(",", "").strip()))))
    except (TypeError, ValueError):
        return 0


def _clean_order_no(value: object) -> str:
    return str(value or "").strip()


def _same_order_no(left: object, right: object) -> bool:
    left_text = _clean_order_no(left)
    right_text = _clean_order_no(right)
    return bool(
        left_text
        and right_text
        and (left_text == right_text or left_text.lstrip("0") == right_text.lstrip("0"))
    )


def _extract_rows(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    return [
        item
        for value in payload.values()
        if isinstance(value, list)
        for item in value
        if isinstance(item, dict)
    ]


class KiwoomOneShareGateway:
    """Minimal broker adapter with explicit write authority and no auth mutation."""

    def __init__(
        self,
        *,
        request_session: requests.Session | None = None,
        token_loader: TokenLoader | None = None,
        order_authority: bool = False,
        base_url: str | None = None,
        timeout_sec: float = 5.0,
        read_pacing_enabled: bool | None = None,
        read_pacer: KiwoomEpisodeReadPacer | None = None,
        read_retry_sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.session = request_session or requests.Session()
        self.token_loader = token_loader or (
            lambda: kiwoom_utils.get_cached_kiwoom_token(CONF)
        )
        self.order_authority = bool(order_authority)
        self.base_url = str(base_url or kiwoom_utils.KIWOOM_BASE_URL).rstrip("/")
        self.timeout_sec = max(1.0, float(timeout_sec))
        self.read_pacing_enabled = (
            request_session is None
            if read_pacing_enabled is None
            else bool(read_pacing_enabled)
        )
        self.read_pacer = read_pacer
        self.read_retry_sleep = read_retry_sleep
        self._minute_bars_cache = SameMinuteSnapshotCache()
        self._account_read_cache = ShortTtlSnapshotCache(ttl_sec=1.0)

    def _token(self) -> str:
        token = str(self.token_loader() or "").replace("Bearer ", "").strip()
        if not token:
            raise RuntimeError("shared_cached_token_unavailable")
        return token

    def _post(
        self,
        *,
        endpoint: str,
        api_id: str,
        payload: dict[str, str],
        cont_yn: str = "N",
        next_key: str = "",
    ) -> tuple[requests.Response, dict[str, Any]]:
        def post_once() -> tuple[requests.Response, dict[str, Any]]:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                headers={
                    "Content-Type": "application/json;charset=UTF-8",
                    "authorization": f"Bearer {self._token()}",
                    "cont-yn": cont_yn,
                    "next-key": next_key,
                    "api-id": api_id,
                },
                json=payload,
                timeout=(5, self.timeout_sec),
            )
            try:
                body = response.json()
            except ValueError:
                body = {}
            return response, body if isinstance(body, dict) else {}

        if api_id not in EPISODE_READ_API_IDS:
            return post_once()
        kwargs: dict[str, Any] = {}
        if self.read_retry_sleep is not None:
            kwargs["sleep"] = self.read_retry_sleep
        if api_id == KT00007_API_ID:
            kwargs.update(
                {
                    "cache": self._account_read_cache,
                    "cache_key": (
                        api_id,
                        tuple(sorted(payload.items())),
                        cont_yn,
                        next_key,
                    ),
                }
            )
        return post_kiwoom_episode_read(
            api_id=api_id,
            post_once=post_once,
            pacing_enabled=self.read_pacing_enabled,
            pacer=self.read_pacer,
            **kwargs,
        )

    def _require_write_authority(self) -> None:
        if not self.order_authority:
            raise PermissionError("one_share_order_authority_disabled")
        if self.base_url != "https://api.kiwoom.com":
            raise PermissionError("one_share_orders_require_production_endpoint")

    @staticmethod
    def _validate_route(route: str) -> str:
        normalized = str(route or "").strip().upper()
        if normalized not in {"NXT", "SOR"}:
            raise ValueError("invalid_order_route")
        return normalized

    @staticmethod
    def _validate_price(price: int) -> int:
        if isinstance(price, bool):
            raise ValueError("invalid_order_price")
        normalized = int(price)
        if normalized <= 0 or normalized % get_tick_size(normalized) != 0:
            raise ValueError("invalid_order_price")
        return normalized

    @staticmethod
    def _submit_result(
        response: requests.Response, body: dict[str, Any]
    ) -> SubmitResult:
        code = str(body.get("return_code", body.get("rt_cd", "")))
        order_no = _clean_order_no(body.get("ord_no"))
        accepted_code = response.status_code == 200 and code == "0"
        ambiguous = bool(
            (response.status_code == 200 and not code)
            or (accepted_code and not order_no)
        )
        return SubmitResult(
            accepted=bool(accepted_code and order_no),
            order_no=order_no,
            return_code=code or f"HTTP_{response.status_code}",
            return_msg=str(body.get("return_msg") or body.get("err_msg") or ""),
            ambiguous=ambiguous,
        )

    def opening_price(self, *, route: str, trade_date: date) -> OpenPriceSnapshot:
        route = self._validate_route(route)
        # The 09:00 SOR entry policy uses the primary-market regular-session
        # opening price as its price anchor.  SOR is the broker order route,
        # not a claim that ka10080 returns a consolidated execution stream.
        request_code = "005930_NX" if route == "NXT" else "005930"
        try:
            response, body = self._post(
                endpoint="/api/dostk/chart",
                api_id="ka10080",
                payload={
                    "stk_cd": request_code,
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
            )
        except Exception as exc:
            return OpenPriceSnapshot(False, error=type(exc).__name__)
        code = str(body.get("return_code", body.get("rt_cd", "")))
        if response.status_code != 200 or code != "0":
            return OpenPriceSnapshot(
                False,
                error=str(body.get("return_msg") or f"HTTP_{response.status_code}"),
            )
        expected = trade_date.strftime("%Y%m%d") + (
            "0800" if route == "NXT" else "0900"
        )
        rows = body.get("stk_min_pole_chart_qry", []) or []
        matches = [
            row
            for row in rows
            if isinstance(row, dict) and str(row.get("cntr_tm") or "")[:12] == expected
        ]
        if not matches:
            return OpenPriceSnapshot(True, error="session_open_not_available")
        row = matches[0]
        price = _positive_int(row.get("open_pric"))
        timestamp = str(row.get("cntr_tm") or "")[:14]
        if price <= 0:
            return OpenPriceSnapshot(False, error="invalid_session_open_price")
        return OpenPriceSnapshot(True, price, timestamp)

    def completed_sor_minute_bars(
        self, *, trade_date: date, now: datetime
    ) -> MinuteBarsSnapshot:
        minute_floor = now.astimezone(KST).replace(second=0, microsecond=0)
        cache_key = (trade_date, minute_floor)
        cached = self._minute_bars_cache.get(cache_key)
        if isinstance(cached, MinuteBarsSnapshot):
            return cached
        try:
            response, body = self._post(
                endpoint="/api/dostk/chart",
                api_id="ka10080",
                payload={"stk_cd": "005930_AL", "tic_scope": "1", "upd_stkpc_tp": "1"},
            )
        except Exception as exc:
            return MinuteBarsSnapshot(False, error=type(exc).__name__)
        code = str(body.get("return_code", body.get("rt_cd", "")))
        if response.status_code != 200 or code != "0":
            return MinuteBarsSnapshot(
                False,
                error=str(body.get("return_msg") or f"HTTP_{response.status_code}"),
            )
        rows = body.get("stk_min_pole_chart_qry")
        if not isinstance(rows, list):
            return MinuteBarsSnapshot(False, error="minute_bar_rows_contract_invalid")
        parsed: dict[datetime, MinuteBar] = {}
        for row in rows:
            if not isinstance(row, dict):
                return MinuteBarsSnapshot(
                    False, error="minute_bar_row_contract_invalid"
                )
            raw_timestamp = str(row.get("cntr_tm") or "").strip()[:14]
            try:
                timestamp = datetime.strptime(raw_timestamp, "%Y%m%d%H%M%S").replace(
                    tzinfo=KST
                )
            except ValueError:
                return MinuteBarsSnapshot(False, error="minute_bar_timestamp_invalid")
            if (
                timestamp.date() != trade_date
                or not time(9, 0) <= timestamp.time() < time(15, 30)
                or timestamp >= minute_floor
            ):
                continue
            bar = MinuteBar(
                timestamp,
                _positive_int(row.get("open_pric")),
                _positive_int(row.get("high_pric")),
                _positive_int(row.get("low_pric")),
                _positive_int(row.get("cur_prc")),
            )
            if (
                min(bar.open_price, bar.high_price, bar.low_price, bar.close_price) <= 0
                or bar.high_price < max(bar.open_price, bar.close_price, bar.low_price)
                or bar.low_price > min(bar.open_price, bar.close_price, bar.high_price)
            ):
                return MinuteBarsSnapshot(False, error="invalid_minute_bar_contract")
            if timestamp in parsed and parsed[timestamp] != bar:
                return MinuteBarsSnapshot(
                    False, error="conflicting_duplicate_minute_bar"
                )
            parsed[timestamp] = bar
        bars = tuple(parsed[key] for key in sorted(parsed))
        if not bars:
            return MinuteBarsSnapshot(True, error="completed_sor_bars_unavailable")
        snapshot = MinuteBarsSnapshot(True, bars)
        if snapshot_contains_latest_completed_minute(
            latest_timestamp=bars[-1].timestamp, minute_floor=minute_floor
        ):
            self._minute_bars_cache.put(cache_key, snapshot)
        return snapshot

    def entry_liquidity_snapshot(self, *, route: str = "SOR") -> EntryLiquiditySnapshot:
        try:
            request_code = entry_liquidity_request_code("005930", route)
            payload = kiwoom_utils.get_stock_orderbook_ka10004(
                self._token(), request_code
            )
        except Exception as exc:
            return unavailable_entry_liquidity_snapshot(
                symbol="005930", route=route, error=type(exc).__name__
            )
        return parse_ka10004_entry_liquidity_snapshot(
            payload, symbol="005930", route=route
        )

    def entry_execution_velocity_snapshot(
        self, *, route: str = "SOR"
    ) -> EntryExecutionVelocitySnapshot:
        try:
            request_code = entry_liquidity_request_code("005930", route)
            payload = kiwoom_utils.get_tick_history_ka10003(
                self._token(), request_code, limit=REQUIRED_RECENT_PRINT_COUNT
            )
        except Exception as exc:
            return unavailable_entry_execution_velocity_snapshot(
                symbol="005930", route=route, error=type(exc).__name__
            )
        return parse_ka10003_entry_execution_velocity_snapshot(
            payload, symbol="005930", route=route
        )

    def submit_limit_buy(
        self, *, price: int, quantity: int, route: str = "SOR"
    ) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        price = self._validate_price(price)
        quantity = validate_owned_leg_quantity(quantity)
        if is_buy_side_paused():
            return SubmitResult(False, return_code="TRADING_PAUSED")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10000",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": str(quantity),
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_manual_addon_limit_buy(
        self, *, price: int, quantity: int, route: str
    ) -> SubmitResult:
        """Submit one explicitly authorized manual-add-on BUY leg.

        This method is intentionally separate from ``submit_limit_buy`` so the
        normal episode quantity cannot inherit this separate override by accident.
        """

        self._require_write_authority()
        route = self._validate_route(route)
        price = self._validate_price(price)
        if isinstance(quantity, bool) or int(quantity) != quantity:
            raise ValueError("invalid_manual_addon_quantity")
        quantity = int(quantity)
        if not 1 <= quantity <= 50:
            raise ValueError("manual_addon_quantity_outside_1_to_50")
        if is_buy_side_paused():
            return SubmitResult(False, return_code="TRADING_PAUSED")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10000",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": str(quantity),
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_limit_sell(
        self, *, price: int, quantity: int, route: str = "SOR"
    ) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        price = self._validate_price(price)
        quantity = validate_position_quantity(quantity, maximum=EPISODE_LEG_QUANTITY)
        if quantity == 0:
            raise ValueError("zero_episode_sell_quantity")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": str(quantity),
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def cancel(self, *, route: str, order_no: str) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        clean_order_no = _clean_order_no(order_no)
        if not clean_order_no:
            raise ValueError("missing_original_order_number")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10003",
            payload={
                "dmst_stex_tp": route,
                "orig_ord_no": clean_order_no,
                "stk_cd": "005930",
                "cncl_qty": "0",
            },
        )
        return self._submit_result(response, body)

    def cancel_manual_addon_remaining(
        self, *, route: str, order_no: str
    ) -> SubmitResult:
        """Cancel all remaining quantity of one exact add-on order."""

        self._require_write_authority()
        route = self._validate_route(route)
        clean_order_no = _clean_order_no(order_no)
        if not clean_order_no:
            raise ValueError("missing_original_order_number")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10003",
            payload={
                "dmst_stex_tp": route,
                "orig_ord_no": clean_order_no,
                "stk_cd": "005930",
                "cncl_qty": "0",
            },
        )
        return self._submit_result(response, body)

    def cancel_buy(self, *, order_no: str) -> SubmitResult:
        return self.cancel(route="SOR", order_no=order_no)

    def _execution_snapshot_for_quantity(
        self,
        *,
        order_no: str,
        order_date: str,
        route: str,
        expected_order_qty: int,
        quantity_error: str,
    ) -> ExecutionSnapshot:
        route = self._validate_route(route)
        clean_order_no = _clean_order_no(order_no)
        clean_date = str(order_date or "").replace("-", "")
        if not clean_order_no or len(clean_date) != 8 or not clean_date.isdigit():
            return ExecutionSnapshot(False, False, 0, 0, 0, error="invalid_query")
        payload = {
            "ord_dt": clean_date,
            "qry_tp": "1",
            "stk_bond_tp": "0",
            "sell_tp": "0",
            "stk_cd": "005930",
            "fr_ord_no": "",
            "dmst_stex_tp": route,
        }
        pages: list[dict[str, Any]] = []
        cont_yn, next_key = "N", ""
        for _ in range(3):
            try:
                response, body = self._post(
                    endpoint="/api/dostk/acnt",
                    api_id="kt00007",
                    payload=payload,
                    cont_yn=cont_yn,
                    next_key=next_key,
                )
            except Exception as exc:
                return ExecutionSnapshot(
                    False, False, 0, 0, 0, error=type(exc).__name__
                )
            code = str(body.get("return_code", body.get("rt_cd", "")))
            if response.status_code != 200 or code != "0":
                return ExecutionSnapshot(
                    False,
                    False,
                    0,
                    0,
                    0,
                    error=str(body.get("return_msg") or f"HTTP_{response.status_code}"),
                )
            pages.append(body)
            cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
            next_key = str(response.headers.get("next-key", "") or "").strip()
            if cont_yn != "Y" or not next_key:
                break
        if cont_yn == "Y" and next_key:
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="execution_continuation_limit_exceeded"
            )
        matches = [
            row
            for page in pages
            for row in _extract_rows(page)
            if _same_order_no(row.get("ord_no"), clean_order_no)
            and kiwoom_utils.normalize_stock_code(str(row.get("stk_cd") or ""))
            == "005930"
        ]
        if not matches:
            return ExecutionSnapshot(True, False, 0, 0, 0)
        row = max(matches, key=lambda item: _positive_int(item.get("cntr_qty")))
        order_qty = _positive_int(row.get("ord_qty"))
        filled_qty = _positive_int(row.get("cntr_qty"))
        raw_remaining = row.get("ord_remnq", row.get("oso_qty"))
        if (
            order_qty != expected_order_qty
            or filled_qty > expected_order_qty
            or raw_remaining is None
        ):
            return ExecutionSnapshot(
                False,
                True,
                filled_qty,
                _positive_int(raw_remaining),
                order_qty,
                error=quantity_error,
            )
        remaining_qty = _positive_int(raw_remaining)
        if (
            remaining_qty > expected_order_qty
            or filled_qty + remaining_qty > expected_order_qty
        ):
            return ExecutionSnapshot(
                False,
                True,
                filled_qty,
                remaining_qty,
                order_qty,
                error=quantity_error,
            )
        return ExecutionSnapshot(
            True,
            True,
            filled_qty,
            remaining_qty,
            order_qty,
            _positive_int(row.get("cntr_uv", row.get("cntr_pric"))) or None,
        )

    def execution_snapshot(
        self,
        *,
        order_no: str,
        order_date: str,
        expected_order_qty: int,
        route: str = "SOR",
    ) -> ExecutionSnapshot:
        """Reconcile an exact order owned by the normal episode machine."""

        try:
            expected_order_qty = validate_position_quantity(
                expected_order_qty, maximum=EPISODE_LEG_QUANTITY
            )
        except ValueError:
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="invalid_expected_order_quantity"
            )
        if expected_order_qty == 0:
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="invalid_expected_order_quantity"
            )

        return self._execution_snapshot_for_quantity(
            route=route,
            order_no=order_no,
            order_date=order_date,
            expected_order_qty=expected_order_qty,
            quantity_error="invalid_episode_execution_contract",
        )

    def manual_addon_execution_snapshot(
        self,
        *,
        order_no: str,
        order_date: str,
        route: str,
        expected_order_qty: int,
    ) -> ExecutionSnapshot:
        """Reconcile one exact manual-add-on order without widening normal scope."""

        if (
            isinstance(expected_order_qty, bool)
            or int(expected_order_qty) != expected_order_qty
        ):
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="invalid_manual_addon_expected_quantity"
            )
        expected_order_qty = int(expected_order_qty)
        if not 1 <= expected_order_qty <= 50:
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="invalid_manual_addon_expected_quantity"
            )
        return self._execution_snapshot_for_quantity(
            route=route,
            order_no=order_no,
            order_date=order_date,
            expected_order_qty=expected_order_qty,
            quantity_error="invalid_manual_addon_execution_contract",
        )
