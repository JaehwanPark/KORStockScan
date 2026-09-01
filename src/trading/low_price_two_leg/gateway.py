"""Official-contract Kiwoom SOR gateway for selected lower-price machines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests

from src.engine.sniper_config import CONF
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.low_price_two_leg.profiles import ALLOWED_SYMBOLS, MinuteBar
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
    KA10075_API_ID,
    KT00007_API_ID,
    KiwoomEpisodeReadPacer,
    SameMinuteSnapshotCache,
    ShortTtlSnapshotCache,
    post_kiwoom_episode_read,
    snapshot_contains_latest_completed_minute,
)
from src.trading.order.tick_utils import get_tick_size
from src.utils import kiwoom_utils

KST = ZoneInfo("Asia/Seoul")
OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-20T15:34:48+09:00",
    "inspected_paths": [
        "kiwoom_docs/차트.md",
        "kiwoom_docs/주문.md",
        "kiwoom_docs/계좌.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core",
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
CURRENT_OPEN_ORDER_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "e24843fc82a78fe7b6ec68625b57f267eda95e77",
    "retrieved_at_kst": "2026-09-01T11:21:56+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json:ka10075,kt00007",
        "kiwoom/specs.py:common REST headers",
        "kiwoom/core/client.py:continuation headers",
        "postman/kiwoom-openapi.postman_collection.json:ka10075,kt00007",
    ],
    "request_scope": ["ka10075", "kt00007"],
    "authority": "read_only_exact_owner_target_reconciliation",
}

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
class CurrentOpenOrderSnapshot:
    source_ok: bool
    found: bool
    exact_order_no: str = ""
    successor_order_no: str = ""
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


def _strict_nonnegative_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).replace(",", "").strip()
    if text.startswith("+"):
        text = text[1:]
    if not text.isdigit():
        return None
    return int(text)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _same_order_no(left: object, right: object) -> bool:
    left_text, right_text = _clean(left), _clean(right)
    return bool(
        left_text
        and right_text
        and (left_text == right_text or left_text.lstrip("0") == right_text.lstrip("0"))
    )


class KiwoomLowPriceTwoLegGateway:
    """Symbol-bound SOR adapter with shared-token reads and explicit writes."""

    def __init__(
        self,
        *,
        symbol: str,
        request_session: requests.Session | None = None,
        token_loader: TokenLoader | None = None,
        order_authority: bool = False,
        base_url: str | None = None,
        timeout_sec: float = 5.0,
        read_pacing_enabled: bool | None = None,
        read_pacer: KiwoomEpisodeReadPacer | None = None,
        read_retry_sleep: Callable[[float], None] | None = None,
    ) -> None:
        normalized_symbol = kiwoom_utils.normalize_stock_code(symbol)
        if normalized_symbol not in ALLOWED_SYMBOLS:
            raise ValueError("symbol_not_in_low_price_machine_allowlist")
        self.symbol = normalized_symbol
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
        self._current_open_read_cache = ShortTtlSnapshotCache(ttl_sec=1.0)

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
        if api_id in {KA10075_API_ID, KT00007_API_ID}:
            kwargs.update(
                {
                    "cache": (
                        self._current_open_read_cache
                        if api_id == KA10075_API_ID
                        else self._account_read_cache
                    ),
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
            raise PermissionError("low_price_two_leg_order_authority_disabled")
        if self.base_url != "https://api.kiwoom.com":
            raise PermissionError(
                "low_price_two_leg_orders_require_production_endpoint"
            )

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
        order_no = _clean(body.get("ord_no"))
        accepted_code = response.status_code == 200 and code == "0"
        ambiguous = bool(
            (response.status_code == 200 and not code)
            or (accepted_code and not order_no)
        )
        return SubmitResult(
            bool(accepted_code and order_no),
            order_no,
            code or f"HTTP_{response.status_code}",
            str(body.get("return_msg") or body.get("err_msg") or ""),
            ambiguous,
        )

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
                payload={
                    "stk_cd": f"{self.symbol}_AL",
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1",
                },
            )
        except Exception as exc:
            return MinuteBarsSnapshot(False, error=type(exc).__name__)
        code = str(body.get("return_code", body.get("rt_cd", "")))
        if response.status_code != 200 or code != "0":
            return MinuteBarsSnapshot(
                False,
                error=str(body.get("return_msg") or f"HTTP_{response.status_code}"),
            )
        parsed: dict[datetime, MinuteBar] = {}
        rows = body.get("stk_min_pole_chart_qry")
        if not isinstance(rows, list):
            return MinuteBarsSnapshot(False, error="minute_bar_rows_contract_invalid")
        for row in rows:
            if not isinstance(row, dict):
                return MinuteBarsSnapshot(
                    False, error="minute_bar_row_contract_invalid"
                )
            raw_ts = _clean(row.get("cntr_tm"))[:14]
            try:
                timestamp = datetime.strptime(raw_ts, "%Y%m%d%H%M%S").replace(
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
            request_code = entry_liquidity_request_code(self.symbol, route)
            payload = kiwoom_utils.get_stock_orderbook_ka10004(
                self._token(), request_code
            )
        except Exception as exc:
            return unavailable_entry_liquidity_snapshot(
                symbol=self.symbol, route=route, error=type(exc).__name__
            )
        return parse_ka10004_entry_liquidity_snapshot(
            payload, symbol=self.symbol, route=route
        )

    def entry_execution_velocity_snapshot(
        self, *, route: str = "SOR"
    ) -> EntryExecutionVelocitySnapshot:
        try:
            request_code = entry_liquidity_request_code(self.symbol, route)
            payload = kiwoom_utils.get_tick_history_ka10003(
                self._token(), request_code, limit=REQUIRED_RECENT_PRINT_COUNT
            )
        except Exception as exc:
            return unavailable_entry_execution_velocity_snapshot(
                symbol=self.symbol, route=route, error=type(exc).__name__
            )
        return parse_ka10003_entry_execution_velocity_snapshot(
            payload, symbol=self.symbol, route=route
        )

    def submit_limit_buy(self, *, price: int, quantity: int) -> SubmitResult:
        self._require_write_authority()
        price = self._validate_price(price)
        quantity = validate_owned_leg_quantity(quantity)
        if is_buy_side_paused():
            return SubmitResult(False, return_code="TRADING_PAUSED")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10000",
            payload={
                "dmst_stex_tp": "SOR",
                "stk_cd": self.symbol,
                "ord_qty": str(quantity),
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_limit_sell(self, *, price: int, quantity: int) -> SubmitResult:
        self._require_write_authority()
        price = self._validate_price(price)
        quantity = validate_position_quantity(quantity, maximum=EPISODE_LEG_QUANTITY)
        if quantity == 0:
            raise ValueError("zero_episode_sell_quantity")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": "SOR",
                "stk_cd": self.symbol,
                "ord_qty": str(quantity),
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def cancel_buy(self, *, order_no: str) -> SubmitResult:
        self._require_write_authority()
        clean_order_no = _clean(order_no)
        if not clean_order_no:
            raise ValueError("missing_original_order_number")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10003",
            payload={
                "dmst_stex_tp": "SOR",
                "orig_ord_no": clean_order_no,
                "stk_cd": self.symbol,
                "cncl_qty": "0",
            },
        )
        return self._submit_result(response, body)

    def execution_snapshot(
        self, *, order_no: str, order_date: str, expected_order_qty: int
    ) -> ExecutionSnapshot:
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
        clean_order_no = _clean(order_no)
        clean_date = _clean(order_date).replace("-", "")
        if not clean_order_no or len(clean_date) != 8 or not clean_date.isdigit():
            return ExecutionSnapshot(False, False, 0, 0, 0, error="invalid_query")
        payload = {
            "ord_dt": clean_date,
            "qry_tp": "1",
            "stk_bond_tp": "0",
            "sell_tp": "0",
            "stk_cd": self.symbol,
            "fr_ord_no": "",
            "dmst_stex_tp": "SOR",
        }
        rows: list[dict[str, Any]] = []
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
            page_rows = body.get("acnt_ord_cntr_prps_dtl")
            if not isinstance(page_rows, list) or any(
                not isinstance(item, dict) for item in page_rows
            ):
                return ExecutionSnapshot(
                    False,
                    False,
                    0,
                    0,
                    0,
                    error="execution_response_contract_invalid",
                )
            rows.extend(page_rows)
            cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
            next_key = str(response.headers.get("next-key", "") or "").strip()
            if cont_yn not in {"N", "Y"}:
                return ExecutionSnapshot(
                    False,
                    False,
                    0,
                    0,
                    0,
                    error="execution_continuation_header_invalid",
                )
            if cont_yn == "Y" and not next_key:
                return ExecutionSnapshot(
                    False,
                    False,
                    0,
                    0,
                    0,
                    error="execution_continuation_header_invalid",
                )
            if cont_yn != "Y":
                break
        if cont_yn == "Y" and next_key:
            return ExecutionSnapshot(
                False,
                False,
                0,
                0,
                0,
                error="execution_continuation_limit_exceeded",
            )
        matches = [
            row
            for row in rows
            if _same_order_no(row.get("ord_no"), clean_order_no)
            and kiwoom_utils.normalize_stock_code(str(row.get("stk_cd") or ""))
            == self.symbol
        ]
        if not matches:
            return ExecutionSnapshot(True, False, 0, 0, 0)
        row = max(matches, key=lambda item: _positive_int(item.get("cntr_qty")))
        parsed_order_qty = _strict_nonnegative_int(row.get("ord_qty"))
        parsed_filled_qty = _strict_nonnegative_int(row.get("cntr_qty"))
        raw_remaining = row.get("ord_remnq", row.get("oso_qty"))
        parsed_remaining_qty = _strict_nonnegative_int(raw_remaining)
        order_qty = int(parsed_order_qty or 0)
        filled_qty = int(parsed_filled_qty or 0)
        remaining_qty = int(parsed_remaining_qty or 0)
        if (
            parsed_order_qty is None
            or parsed_filled_qty is None
            or parsed_remaining_qty is None
            or order_qty != expected_order_qty
            or filled_qty > expected_order_qty
            or remaining_qty > expected_order_qty
            or filled_qty + remaining_qty > expected_order_qty
        ):
            return ExecutionSnapshot(
                False,
                True,
                filled_qty,
                remaining_qty,
                order_qty,
                error="invalid_episode_execution_contract",
            )
        return ExecutionSnapshot(
            True,
            True,
            filled_qty,
            remaining_qty,
            order_qty,
            _positive_int(row.get("cntr_uv", row.get("cntr_pric"))) or None,
        )

    def current_open_sell_snapshot(
        self, *, order_no: str, order_date: str, observed_date: str
    ) -> CurrentOpenOrderSnapshot:
        """Confirm whether one owned SELL order is in the current open ledger.

        ``kt00007`` is the dated order/execution history owner.  A historical
        row can retain a non-zero ``ord_remnq`` after the day order is no
        longer active, so terminal absence must come from the current
        ``ka10075`` unfilled-order ledger.  This read never submits, cancels,
        replaces, or adopts an order.
        """

        clean_order_no = _clean(order_no)
        if not clean_order_no.isdigit():
            return CurrentOpenOrderSnapshot(False, False, error="invalid_order_no")
        try:
            target_date = date.fromisoformat(_clean(order_date))
            ledger_date = date.fromisoformat(_clean(observed_date))
        except ValueError:
            return CurrentOpenOrderSnapshot(
                False, False, error="invalid_order_date_contract"
            )
        if target_date > ledger_date:
            return CurrentOpenOrderSnapshot(
                False, False, error="future_order_date_contract"
            )
        payload = {
            "all_stk_tp": "1",
            "trde_tp": "1",
            "stk_cd": self.symbol,
            "stex_tp": "0",
        }
        rows: list[dict[str, Any]] = []
        cont_yn, next_key = "N", ""
        for _ in range(3):
            try:
                response, body = self._post(
                    endpoint="/api/dostk/acnt",
                    api_id=KA10075_API_ID,
                    payload=payload,
                    cont_yn=cont_yn,
                    next_key=next_key,
                )
            except Exception as exc:
                return CurrentOpenOrderSnapshot(
                    False,
                    False,
                    error=f"current_unfilled_read_failed:{type(exc).__name__}",
                )
            code = str(body.get("return_code", body.get("rt_cd", "")))
            page_rows = body.get("oso")
            if response.status_code != 200 or code != "0":
                return CurrentOpenOrderSnapshot(
                    False,
                    False,
                    error=str(body.get("return_msg") or f"HTTP_{response.status_code}"),
                )
            if not isinstance(page_rows, list) or any(
                not isinstance(item, dict) for item in page_rows
            ):
                return CurrentOpenOrderSnapshot(
                    False, False, error="current_unfilled_response_contract_invalid"
                )
            rows.extend(page_rows)
            cont_yn = str(response.headers.get("cont-yn", "N") or "N").upper()
            next_key = str(response.headers.get("next-key", "") or "").strip()
            if cont_yn not in {"N", "Y"}:
                return CurrentOpenOrderSnapshot(
                    False,
                    False,
                    error="current_unfilled_continuation_header_invalid",
                )
            if cont_yn == "Y" and not next_key:
                return CurrentOpenOrderSnapshot(
                    False,
                    False,
                    error="current_unfilled_continuation_header_invalid",
                )
            if cont_yn != "Y":
                break
        if cont_yn == "Y" and next_key:
            return CurrentOpenOrderSnapshot(
                False,
                False,
                error="current_unfilled_continuation_limit_exceeded",
            )

        exact_order_no = ""
        successor_order_no = ""
        for row in rows:
            row_order_no = _clean(row.get("ord_no"))
            row_original_order_no = _clean(row.get("orig_ord_no"))
            row_symbol = kiwoom_utils.normalize_stock_code(
                str(row.get("stk_cd") or "")
            )
            remaining_qty = _strict_nonnegative_int(row.get("oso_qty"))
            if (
                not row_order_no.isdigit()
                or (row_original_order_no and not row_original_order_no.isdigit())
                or row_symbol != self.symbol
                or remaining_qty is None
                or remaining_qty <= 0
            ):
                return CurrentOpenOrderSnapshot(
                    False, False, error="current_unfilled_row_contract_invalid"
                )
            if target_date != ledger_date:
                continue
            if _same_order_no(row_order_no, clean_order_no):
                exact_order_no = row_order_no
            elif _same_order_no(row_original_order_no, clean_order_no):
                successor_order_no = row_order_no
        return CurrentOpenOrderSnapshot(
            True,
            bool(exact_order_no or successor_order_no),
            exact_order_no=exact_order_no,
            successor_order_no=successor_order_no,
        )
