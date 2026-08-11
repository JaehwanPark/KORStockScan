"""Shared-token-only Kiwoom gateway for the independent one-share machine.

This module owns no token lifecycle and imports no KORStockScan entry, holding,
exit, ADM, LDM, sizing, or strategy code. Broker writes require an explicit
constructor authority and are hard-limited to one share of 005930.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

import requests

from src.engine.sniper_config import CONF
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.tick_utils import get_tick_size
from src.utils import kiwoom_utils

OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-11T10:16:56+09:00",
    "inspected_paths": [
        "kiwoom_docs/주문.md",
        "kiwoom_docs/계좌.md",
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["ka10080", "kt10000", "kt10001", "kt10003", "kt00007"],
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
class OpenPriceSnapshot:
    source_ok: bool
    price: int | None = None
    source_timestamp: str = ""
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
    ) -> None:
        self.session = request_session or requests.Session()
        self.token_loader = token_loader or (
            lambda: kiwoom_utils.get_cached_kiwoom_token(CONF)
        )
        self.order_authority = bool(order_authority)
        self.base_url = str(base_url or kiwoom_utils.KIWOOM_BASE_URL).rstrip("/")
        self.timeout_sec = max(1.0, float(timeout_sec))

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

    def _require_write_authority(self) -> None:
        if not self.order_authority:
            raise PermissionError("one_share_order_authority_disabled")
        if self.base_url != "https://api.kiwoom.com":
            raise PermissionError("one_share_orders_require_production_endpoint")

    @staticmethod
    def _validate_route(route: str) -> str:
        normalized = str(route or "").strip().upper()
        if normalized not in {"KRX", "NXT"}:
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

    def submit_limit_buy(self, *, route: str, price: int) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        price = self._validate_price(price)
        if is_buy_side_paused():
            return SubmitResult(False, return_code="TRADING_PAUSED")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10000",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": "1",
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_limit_sell(self, *, route: str, price: int) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        price = self._validate_price(price)
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": "1",
                "ord_uv": str(price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_best_sell(self, *, route: str) -> SubmitResult:
        self._require_write_authority()
        route = self._validate_route(route)
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": route,
                "stk_cd": "005930",
                "ord_qty": "1",
                "ord_uv": "",
                "trde_tp": "6",
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
                "cncl_qty": "1",
            },
        )
        return self._submit_result(response, body)

    def execution_snapshot(
        self, *, route: str, order_no: str, order_date: str
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
        if order_qty != 1 or filled_qty > 1 or raw_remaining is None:
            return ExecutionSnapshot(
                False,
                True,
                filled_qty,
                _positive_int(raw_remaining),
                order_qty,
                error="invalid_one_share_execution_contract",
            )
        remaining_qty = _positive_int(raw_remaining)
        if remaining_qty > 1 or filled_qty + remaining_qty > 1:
            return ExecutionSnapshot(
                False,
                True,
                filled_qty,
                remaining_qty,
                order_qty,
                error="invalid_one_share_execution_contract",
            )
        return ExecutionSnapshot(
            True,
            True,
            filled_qty,
            remaining_qty,
            order_qty,
            _positive_int(row.get("cntr_uv", row.get("cntr_pric"))) or None,
        )
