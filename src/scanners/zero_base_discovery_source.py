"""Bounded Kiwoom discovery panels for the zero-base SCALPING queue.

The ranking endpoint is a discovery source, never a quote, machine decision,
whole-market denominator, or order authorization source.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time

from src.scanners.scanner_source_census import source_target_market_data_route
from src.utils import kiwoom_utils
from src.utils.kiwoom_read_request_control import REQUEST_CLASS_SOURCE_ONLY


SCHEMA = "zero_base_discovery_panel_v1"
PANEL_REQUESTS = (
    ("KOSPI", "001", "KRX", "1", "krx_only"),
    ("KOSDAQ", "101", "KRX", "1", "krx_only"),
    ("KOSPI", "001", "NXT", "2", "nxt_only"),
    ("KOSDAQ", "101", "NXT", "2", "nxt_only"),
)
MAX_ROWS_PER_PANEL = 200  # Current adapter's ten-page bound, not market coverage.


def _sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def fetch_discovery_panels(token, *, now_epoch=None, fetcher=None) -> dict:
    """Read four exact-route panels through the shared source-only rate gate."""
    fetcher = fetcher or kiwoom_utils.get_top_fluctuation_ka10027
    panels = []
    observations = []
    for market, mrkt_tp, venue, stex_tp, route in PANEL_REQUESTS:
        request_epoch = time.time() if now_epoch is None else float(now_epoch)
        try:
            rows, meta = fetcher(
                token,
                mrkt_tp=mrkt_tp,
                trde_qty_cnd="0000",
                limit=MAX_ROWS_PER_PANEL,
                stex_tp=stex_tp,
                sort_tp="1",
                stk_cnd="4",
                crd_cnd="0",
                updown_incls="1",
                pric_cnd="0",
                trde_prica_cnd="0",
                pure_equity_only=True,
                request_owner="zero_base_discovery_panel",
                request_class=REQUEST_CLASS_SOURCE_ONLY,
                read_rate_max_wait_sec=3.0,
                return_meta=True,
            )
        except Exception as exc:
            rows, meta = [], {"source_error": type(exc).__name__}
        meta = meta if isinstance(meta, dict) else {}
        received_ms = meta.get("rest_received_ts_ms")
        receive_epoch = (
            received_ms / 1000.0
            if isinstance(received_ms, int) and received_ms > 0
            else 0.0
        )
        valid_response = (
            meta.get("response_contract_status") == "verified_success"
            and meta.get("read_rate_control_status") == "admitted"
            and not meta.get("rate_limit_detected")
            and not meta.get("continuous_next_key_missing")
            and receive_epoch >= request_epoch
        )
        panel = {
            "market": market,
            "venue": venue,
            "route": route,
            "request_epoch": request_epoch,
            "received_epoch": receive_epoch,
            "status": "observed_panel" if valid_response else "source_unavailable",
            "response_page_count": meta.get("response_page_count", 0),
            "page_limit_reached": bool(meta.get("continuous_page_limit_reached")),
            "returned_count": len(rows or []),
            "eligible_count": 0,
            "rejected_count": 0,
            "source_error": meta.get("source_error", ""),
        }
        panels.append(panel)
        if not valid_response:
            continue
        for row in rows or []:
            if not isinstance(row, dict):
                panel["rejected_count"] += 1
                continue
            code = str(row.get("Code") or "").strip()
            raw_code = str(row.get("RawInstrumentCode") or code).strip()
            name = str(row.get("Name") or "").strip()
            try:
                change_rate = float(row.get("ChangeRate"))
                price = int(row.get("Price"))
                volume = int(row.get("Volume"))
            except (TypeError, ValueError):
                panel["rejected_count"] += 1
                continue
            if (
                re.fullmatch(r"\d{6}", code) is None
                or source_target_market_data_route(raw_code, route) != route
                or not name
                or not math.isfinite(change_rate)
                or change_rate <= 0
                or price <= 0
                or volume < 0
            ):
                panel["rejected_count"] += 1
                continue
            row_payload = {
                "code": code,
                "raw_instrument_code": raw_code,
                "name": name,
                "market": market,
                "venue": venue,
                "route": route,
                "price": price,
                "volume": volume,
                "change_rate": change_rate,
                "source_rank": row.get("SourceRank"),
                "request_epoch": request_epoch,
                "observed_epoch": receive_epoch,
                "source_scope": "observed_panel",
            }
            row_payload["source_sha256"] = _sha256(row_payload)
            observations.append(row_payload)
            panel["eligible_count"] += 1
    return {"schema": SCHEMA, "panels": panels, "observations": observations}
