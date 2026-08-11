"""Kiwoom shared-token-only gateway for the widget auto-trade owner.

This gateway deliberately does not call the deposit/orderable-cash endpoints
and never issues or refreshes an access token.  The broker remains the final
authority for account eligibility, margin/misu availability, and order
acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import requests

from src.engine.sniper_config import CONF
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.tick_utils import get_tick_size
from src.utils import kiwoom_utils

KIWOOM_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-12T07:19:36+09:00",
    "inspected_paths": [
        "kiwoom_docs/주문.md",
        "kiwoom_docs/계좌.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["kt10000", "kt10001", "kt10003", "kt00007"],
}

TokenLoader = Callable[[], str | None]


@dataclass(frozen=True)
class SubmitResult:
    accepted: bool
    order_no: str
    return_code: str
    return_msg: str
    ambiguous: bool = False


@dataclass(frozen=True)
class ExecutionSnapshot:
    source_ok: bool
    found: bool
    filled_qty: int
    remaining_qty: int
    order_qty: int
    fill_price: int | None = None
    source_api: str = "kt00007"
    error: str = ""


def _positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(float(str(value or "0").replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0


def _clean_code(value: object) -> str:
    return kiwoom_utils.normalize_stock_code(str(value or ""))


def _order_no(value: object) -> str:
    return str(value or "").strip()


def _same_order_no(left: object, right: object) -> bool:
    left_text = _order_no(left)
    right_text = _order_no(right)
    if left_text == right_text:
        return bool(left_text)
    return bool(
        left_text and right_text and left_text.lstrip("0") == right_text.lstrip("0")
    )


def resolve_widget_broker_route(route: str) -> str:
    """Resolve a market venue to the broker route used for a new order.

    KRX observations retain KRX as their market-data venue, but regular-market
    orders use Kiwoom SOR. NXT observations are the only path that submits to
    NXT directly. Accepting SOR makes the function idempotent for callers that
    already resolved the route.
    """

    clean_route = str(route or "").strip().upper()
    if clean_route in {"KRX", "SOR"}:
        return "SOR"
    if clean_route == "NXT":
        return "NXT"
    raise ValueError("invalid_order_route")


def _validated_order_inputs(*, code: str, qty: int, route: str) -> tuple[str, int, str]:
    clean_code = _clean_code(code)
    clean_route = resolve_widget_broker_route(route)
    if isinstance(qty, bool):
        raise ValueError("invalid_order_quantity")
    clean_qty = int(qty)
    if not clean_code or len(clean_code) != 6:
        raise ValueError("invalid_stock_code")
    if clean_qty <= 0:
        raise ValueError("invalid_order_quantity")
    return clean_code, clean_qty, clean_route


def _validated_existing_order_inputs(
    *, code: str, qty: int, route: str
) -> tuple[str, int, str]:
    """Validate a cancel/reconcile route without rewriting legacy orders.

    Orders submitted before the SOR migration can still be open on the direct
    KRX route. New orders persist SOR, while this compatibility path ensures an
    older KRX order can still be reconciled or cancelled on its original route.
    """

    clean_code = _clean_code(code)
    clean_route = str(route or "").strip().upper()
    if isinstance(qty, bool):
        raise ValueError("invalid_order_quantity")
    clean_qty = int(qty)
    if not clean_code or len(clean_code) != 6:
        raise ValueError("invalid_stock_code")
    if clean_qty <= 0:
        raise ValueError("invalid_order_quantity")
    if clean_route not in {"KRX", "SOR", "NXT"}:
        raise ValueError("invalid_order_route")
    return clean_code, clean_qty, clean_route


def _extract_rows(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, Any]] = []
    for value in payload.values():
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return rows


class KiwoomSharedTokenOrderGateway:
    """Minimal real-order gateway with no token issuance or cash precheck."""

    def __init__(
        self,
        *,
        request_session: requests.Session | None = None,
        token_loader: TokenLoader | None = None,
        timeout_sec: float = 5.0,
    ) -> None:
        self.session = request_session or requests.Session()
        self.token_loader = token_loader or (
            lambda: kiwoom_utils.get_cached_kiwoom_token(CONF)
        )
        self.timeout_sec = max(1.0, float(timeout_sec))

    def _token(self) -> str:
        token = str(self.token_loader() or "").strip()
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
            kiwoom_utils.get_api_url(endpoint),
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {self._token()}",
                "cont-yn": cont_yn,
                "next-key": next_key,
                "api-id": api_id,
            },
            json=payload,
            timeout=self.timeout_sec,
        )
        try:
            body = response.json()
        except Exception:
            body = {}
        return response, body if isinstance(body, dict) else {}

    @staticmethod
    def _submit_result(
        response: requests.Response, body: dict[str, Any]
    ) -> SubmitResult:
        return_code = str(body.get("return_code", body.get("rt_cd", "")))
        accepted = response.status_code == 200 and return_code == "0"
        order_no = _order_no(body.get("ord_no"))
        ambiguous = bool(
            (response.status_code == 200 and not return_code)
            or (accepted and not order_no)
        )
        return SubmitResult(
            accepted=bool(accepted and order_no),
            order_no=order_no,
            return_code=return_code or f"HTTP_{response.status_code}",
            return_msg=str(body.get("return_msg") or body.get("err_msg") or ""),
            ambiguous=ambiguous,
        )

    def submit_buy(self, *, code: str, qty: int, route: str) -> SubmitResult:
        clean_code, clean_qty, clean_route = _validated_order_inputs(
            code=code, qty=qty, route=route
        )
        if is_buy_side_paused():
            return SubmitResult(
                accepted=False,
                order_no="",
                return_code="TRADING_PAUSED",
                return_msg="persistent buy-side pause is active",
            )
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10000",
            payload={
                "dmst_stex_tp": clean_route,
                "stk_cd": clean_code,
                "ord_qty": str(clean_qty),
                "ord_uv": "",
                "trde_tp": "6",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_sell(self, *, code: str, qty: int, route: str) -> SubmitResult:
        clean_code, clean_qty, clean_route = _validated_order_inputs(
            code=code, qty=qty, route=route
        )
        # NXT does not reliably accept market orders. Use best-limit only for
        # NXT; a KRX observation resolves to SOR and keeps an execution-oriented
        # market order for the final exit.
        order_type = "6" if clean_route == "NXT" else "3"
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": clean_route,
                "stk_cd": clean_code,
                "ord_qty": str(clean_qty),
                "ord_uv": "",
                "trde_tp": order_type,
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def submit_limit_sell(
        self, *, code: str, qty: int, route: str, price: int
    ) -> SubmitResult:
        clean_code, clean_qty, clean_route = _validated_order_inputs(
            code=code, qty=qty, route=route
        )
        if isinstance(price, bool):
            raise ValueError("invalid_order_price")
        try:
            clean_price = int(price)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_order_price") from exc
        if clean_price <= 0 or clean_price % get_tick_size(clean_price) != 0:
            raise ValueError("invalid_order_price")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10001",
            payload={
                "dmst_stex_tp": clean_route,
                "stk_cd": clean_code,
                "ord_qty": str(clean_qty),
                "ord_uv": str(clean_price),
                "trde_tp": "0",
                "cond_uv": "",
            },
        )
        return self._submit_result(response, body)

    def cancel(self, *, code: str, order_no: str, qty: int, route: str) -> SubmitResult:
        clean_code, clean_qty, clean_route = _validated_existing_order_inputs(
            code=code, qty=qty, route=route
        )
        clean_order_no = _order_no(order_no)
        if not clean_order_no:
            raise ValueError("missing_original_order_number")
        response, body = self._post(
            endpoint="/api/dostk/ordr",
            api_id="kt10003",
            payload={
                "dmst_stex_tp": clean_route,
                "orig_ord_no": clean_order_no,
                "stk_cd": clean_code,
                "cncl_qty": str(clean_qty),
            },
        )
        return self._submit_result(response, body)

    def execution_snapshot(
        self,
        *,
        code: str,
        order_no: str,
        route: str,
        order_date: str,
    ) -> ExecutionSnapshot:
        clean_code = _clean_code(code)
        clean_order_no = _order_no(order_no)
        clean_route = str(route or "").strip().upper()
        clean_order_date = str(order_date or "").replace("-", "")
        if (
            not clean_code
            or len(clean_code) != 6
            or not clean_order_no
            or clean_route not in {"KRX", "SOR", "NXT"}
            or len(clean_order_date) != 8
            or not clean_order_date.isdigit()
        ):
            return ExecutionSnapshot(
                False, False, 0, 0, 0, error="invalid_execution_query_input"
            )
        payload = {
            "ord_dt": clean_order_date,
            "qry_tp": "1",
            "stk_bond_tp": "0",
            "sell_tp": "0",
            "stk_cd": clean_code,
            "fr_ord_no": "",
            "dmst_stex_tp": clean_route,
        }
        pages: list[dict[str, Any]] = []
        cont_yn = "N"
        next_key = ""
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
            return_code = str(body.get("return_code", body.get("rt_cd", "")))
            if response.status_code != 200 or return_code != "0":
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
            and _clean_code(row.get("stk_cd")) == clean_code
        ]
        if not matches:
            return ExecutionSnapshot(True, False, 0, 0, 0)

        # The queried order number is immutable for this executor; retain the
        # row with the greatest confirmed fill in case the broker returns more
        # than one status representation.
        row = max(matches, key=lambda item: _positive_int(item.get("cntr_qty")))
        order_qty = _positive_int(row.get("ord_qty"))
        if order_qty <= 0:
            return ExecutionSnapshot(
                source_ok=False,
                found=True,
                filled_qty=0,
                remaining_qty=0,
                order_qty=0,
                error="missing_or_invalid_order_qty",
            )
        filled_qty = min(order_qty, _positive_int(row.get("cntr_qty")))
        remaining_qty = min(
            max(0, order_qty - filled_qty),
            _positive_int(row.get("ord_remnq", row.get("oso_qty"))),
        )
        if order_qty > 0 and filled_qty + remaining_qty < order_qty:
            # A zero remainder is authoritative only when the response reports
            # it explicitly.  Missing fields remain unresolved.
            raw_remaining = row.get("ord_remnq", row.get("oso_qty"))
            if raw_remaining is None or str(raw_remaining).strip() == "":
                remaining_qty = order_qty - filled_qty
        return ExecutionSnapshot(
            source_ok=True,
            found=True,
            filled_qty=filled_qty,
            remaining_qty=remaining_qty,
            order_qty=order_qty,
            fill_price=_positive_int(row.get("cntr_uv", row.get("cntr_pric"))) or None,
        )
