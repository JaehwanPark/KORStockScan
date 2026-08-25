"""Forensic comparison of scalping AI inputs with independent market sources.

The report produced here is observation-only.  It never feeds a live prompt,
changes a provider route, mutates a threshold, or submits an order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import requests

from src.engine.scalping.ai_decision_trace import (
    replay_source_input,
    sanitize_ai_trace_value,
)
from src.engine.scalping.market_context_observation import (
    OBSERVATION_CONTRACT,
    build_market_context_observation,
)
from src.utils.jsonl_io import iter_jsonl_objects_strict

KST = ZoneInfo("Asia/Seoul")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "ai_input_external_validation"
PAYLOAD_DIR = PROJECT_ROOT / "data" / "ai_decision_payloads"
TRACE_DIR = PROJECT_ROOT / "data" / "ai_decision_trace"
REQUEST_DIR = PROJECT_ROOT / "data" / "ai_decision_requests"
SCHEMA = "ai_input_external_validation_v1"
STRICT_STATUSES = {"MATCH", "MISMATCH"}
KRX_OPEN_API_BASE_URL = "https://data-dbg.krx.co.kr/svc/apis/sto"
KRX_OPEN_API_AUTH_ENV = "KRX_OPEN_API_AUTH_KEY"
KRX_OPEN_API_CONFIG_KEY = "KRX_OPEN_API_KEY"
KRX_OPEN_API_CONFIG_PATH = PROJECT_ROOT / "data" / "config_prod.json"
KRX_OPEN_API_ENDPOINTS = ("stk_bydd_trd", "ksq_bydd_trd")
NAVER_CHART_URL = "https://fchart.stock.naver.com/sise.nhn"
NAVER_MINUTE_PUBLICATION_LAG = timedelta(minutes=3)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _sanitize_metadata(value: Any) -> Any:
    sanitized, _redacted = sanitize_ai_trace_value(value)
    return sanitized


def _resolve_krx_open_api_auth_key(
    *,
    auth_key: str | None = None,
    config_path: Path = KRX_OPEN_API_CONFIG_PATH,
) -> tuple[str, str]:
    """Resolve KRX authentication without exposing a credential in artifacts.

    ``auth_key`` is intentionally authoritative even when empty, so tests and
    callers can explicitly request a no-network fail-closed path.  Production
    uses the established auth env first, then the user-facing config key.
    """

    if auth_key is not None:
        return str(auth_key).strip(), "explicit_argument"
    for key in (KRX_OPEN_API_AUTH_ENV, KRX_OPEN_API_CONFIG_KEY):
        value = os.getenv(key, "").strip()
        if value:
            return value, f"environment:{key}"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}
    if isinstance(config, dict):
        for key in (KRX_OPEN_API_AUTH_ENV, KRX_OPEN_API_CONFIG_KEY):
            value = str(config.get(key) or "").strip()
            if value:
                return value, f"config:{key}"
    return "", "not_configured"


def _validated_provenance_date(
    target_date: str,
    provenance_date: str | None,
) -> str:
    try:
        market_date = date.fromisoformat(str(target_date))
        capture_date = date.fromisoformat(str(provenance_date or target_date))
    except ValueError as exc:
        raise ValueError("target/provenance date must use YYYY-MM-DD") from exc
    if capture_date < market_date:
        raise ValueError("provenance capture date cannot precede the market date")
    if capture_date > datetime.now(KST).date():
        raise ValueError("provenance capture date cannot be in the future")
    return capture_date.isoformat()


def _int(value: Any) -> int | None:
    try:
        if value in (None, "", "-", "null"):
            return None
        return abs(int(float(str(value).replace(",", "").replace("+", ""))))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "null"):
            return None
        return float(str(value).replace(",", "").replace("+", ""))
    except (TypeError, ValueError):
        return None


def compare_value(
    *,
    field: str,
    api_raw_value: Any,
    normalized_value: Any,
    ai_payload_value: Any,
    external_value: Any,
    value_type: str,
    comparable: bool = True,
    reason: str = "",
    source: str,
    basis: dict[str, Any],
) -> dict[str, Any]:
    if not comparable:
        status = "NOT_COMPARABLE"
    elif external_value is None:
        status = "SOURCE_UNAVAILABLE"
        reason = reason or "external_value_missing"
    elif normalized_value is None:
        status = "SOURCE_UNAVAILABLE"
        reason = reason or "api_value_missing"
    elif value_type == "integer":
        status = (
            "MATCH" if _int(normalized_value) == _int(external_value) else "MISMATCH"
        )
    else:
        left = _float(normalized_value)
        right = _float(external_value)
        status = (
            "MATCH"
            if left is not None and right is not None and abs(left - right) <= 1e-6
            else "MISMATCH"
        )
    ai_matches_normalized = None
    if ai_payload_value is not None and normalized_value is not None:
        if value_type == "integer":
            ai_matches_normalized = _int(ai_payload_value) == _int(normalized_value)
        else:
            ai_left = _float(ai_payload_value)
            normalized_right = _float(normalized_value)
            ai_matches_normalized = bool(
                ai_left is not None
                and normalized_right is not None
                and abs(ai_left - normalized_right) <= 1e-6
            )
    return {
        "field": field,
        "api_raw_value": api_raw_value,
        "normalized_or_derived_value": normalized_value,
        "ai_payload_value": ai_payload_value,
        "external_value": external_value,
        "value_type": value_type,
        "status": status,
        "reason": reason or None,
        "external_source": source,
        "comparison_basis": dict(basis),
        "ai_payload_matches_normalized": ai_matches_normalized,
    }


def parse_naver_chart_xml(text: str, *, timeframe: str) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(text)
    rows: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        raw = str(item.attrib.get("data") or "")
        parts = raw.split("|")
        if len(parts) < 6:
            continue
        stamp = parts[0].strip()
        if timeframe == "minute" and len(stamp) >= 12:
            timestamp = (
                f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T"
                f"{stamp[8:10]}:{stamp[10:12]}:00+09:00"
            )
        elif len(stamp) >= 8:
            timestamp = f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}"
        else:
            continue
        rows.append(
            {
                "timestamp": timestamp,
                "open": _int(parts[1]),
                "high": _int(parts[2]),
                "low": _int(parts[3]),
                "close": _int(parts[4]),
                "volume": _int(parts[5]),
                "raw": raw,
            }
        )
    return sorted(rows, key=lambda row: str(row["timestamp"]))


def naver_minute_volume_deltas(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    previous: dict[str, Any] | None = None
    for row in sorted(rows, key=lambda item: str(item.get("timestamp") or "")):
        timestamp = str(row.get("timestamp") or "")
        minute = timestamp[:16]
        current_volume = _int(row.get("volume"))
        comparable = False
        delta = None
        reason = "first_cumulative_sample"
        if timestamp[11:16] == "09:00" and current_volume is not None:
            delta = current_volume
            comparable = True
            reason = ""
        elif previous is not None:
            previous_stamp = str(previous.get("timestamp") or "")
            try:
                current_dt = datetime.fromisoformat(timestamp)
                previous_dt = datetime.fromisoformat(previous_stamp)
                consecutive = int((current_dt - previous_dt).total_seconds()) == 60
            except ValueError:
                consecutive = False
            previous_volume = _int(previous.get("volume"))
            if (
                consecutive
                and current_volume is not None
                and previous_volume is not None
                and current_volume >= previous_volume
            ):
                delta = current_volume - previous_volume
                comparable = True
                reason = ""
            else:
                reason = "non_consecutive_or_reset_cumulative_volume"
        output[minute[11:16] if len(minute) >= 16 else minute] = {
            "delta": delta,
            "comparable": comparable,
            "reason": reason,
            "cumulative_volume": current_volume,
        }
        previous = row
    return output


def _fetch_naver_chart(
    symbol: str,
    timeframe: str,
    *,
    count: int,
    get: Callable[..., Any] = requests.get,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params = {
        "symbol": symbol[:6],
        "timeframe": timeframe,
        "count": str(count),
        "requestType": "0",
    }
    response = get(NAVER_CHART_URL, params=params, timeout=15)
    response.raise_for_status()
    text = response.text
    return parse_naver_chart_xml(text, timeframe=timeframe), {
        "url": NAVER_CHART_URL,
        "timeframe": timeframe,
        "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "retrieved_at": datetime.now(KST).isoformat(),
    }


def _fetch_krx_daily(
    target_date: str,
    *,
    auth_key: str | None = None,
    get: Callable[..., Any] = requests.get,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Fetch official KOSPI/KOSDAQ daily rows through the authenticated KRX API.

    The unauthenticated Data Marketplace web JSON backend returns ``LOGOUT`` and
    is intentionally not used here.  Authentication material is request-only
    and never included in returned report metadata.
    """

    resolved_auth_key, auth_source = _resolve_krx_open_api_auth_key(auth_key=auth_key)
    metadata: dict[str, Any] = {
        "source": "KRX_OPEN_API_STOCK_DAILY",
        "base_url": KRX_OPEN_API_BASE_URL,
        "api_ids": list(KRX_OPEN_API_ENDPOINTS),
        "auth_env": f"{KRX_OPEN_API_AUTH_ENV}|{KRX_OPEN_API_CONFIG_KEY}",
        "auth_source": auth_source,
        "auth_configured": bool(resolved_auth_key),
        "auth_value_recorded": False,
        "legacy_mdc_endpoint_called": False,
        "retrieved_at": datetime.now(KST).isoformat(),
    }
    if not resolved_auth_key:
        metadata.update(
            {
                "status": "source_unavailable",
                "error": "krx_open_api_auth_key_not_configured",
                "response_sha256": None,
            }
        )
        return {}, metadata

    request_date = date.fromisoformat(target_date).strftime("%Y%m%d")
    output: dict[str, dict[str, Any]] = {}
    payloads: dict[str, Any] = {}
    endpoint_errors: dict[str, str] = {}
    endpoint_http_statuses: dict[str, int] = {}
    for api_id in KRX_OPEN_API_ENDPOINTS:
        url = f"{KRX_OPEN_API_BASE_URL}/{api_id}"
        try:
            response = get(
                url,
                params={"basDd": request_date},
                headers={
                    "AUTH_KEY": resolved_auth_key,
                    "Accept": "application/json",
                    "User-Agent": "KORStockScan-source-quality-audit/1.0",
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            response_rows = payload.get("OutBlock_1")
            if not isinstance(response_rows, list) or not response_rows:
                raise ValueError("krx_open_api_outblock_missing_or_empty")
            response_dates = {
                str(row.get("BAS_DD") or "").strip()
                for row in response_rows
                if isinstance(row, dict)
            }
            if response_dates != {request_date}:
                raise ValueError("krx_open_api_response_date_mismatch")
            payloads[api_id] = payload
        except Exception as exc:
            endpoint_errors[api_id] = f"{type(exc).__name__}:{exc}"
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if isinstance(status_code, int):
                endpoint_http_statuses[api_id] = status_code
            continue
        for row in response_rows:
            symbol = str(row.get("ISU_CD") or "").strip()
            if not symbol:
                continue
            output[symbol] = {
                "open": _int(row.get("TDD_OPNPRC")),
                "high": _int(row.get("TDD_HGPRC")),
                "low": _int(row.get("TDD_LWPRC")),
                "close": _int(row.get("TDD_CLSPRC")),
                "volume": _int(row.get("ACC_TRDVOL")),
                "raw": row,
            }
    metadata.update(
        {
            "status": (
                "pass"
                if not endpoint_errors
                else ("partial" if payloads else "source_unavailable")
            ),
            "error": (
                "krx_open_api_unauthorized"
                if endpoint_errors
                and endpoint_http_statuses
                and len(endpoint_http_statuses) == len(endpoint_errors)
                and all(
                    status in {401, 403} for status in endpoint_http_statuses.values()
                )
                else ("krx_open_api_endpoint_failure" if endpoint_errors else None)
            ),
            "endpoint_errors": endpoint_errors,
            "endpoint_http_statuses": endpoint_http_statuses,
            "response_sha256": _sha256_json(payloads) if payloads else None,
            "row_count": len(output),
        }
    )
    return output, metadata


def _krx_daily_verification_observation(
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Describe KRX daily API availability without making it an intraday gate.

    The approved KRX Open API daily services currently return an empty outblock
    for this workflow.  Preserve that external defect as operational
    provenance, but it is neither a completed intraday bar nor a reliable
    external equality source for the AI-context contract.  Keep the evidence
    visible while ensuring it cannot turn an otherwise valid minute/payload
    comparison into a verification failure.
    """

    fields = metadata if isinstance(metadata, dict) else {}
    status = str(fields.get("status") or "source_unavailable").strip()
    error = str(fields.get("error") or "").strip() or None
    return {
        "source": "KRX_OPEN_API_STOCK_DAILY",
        "availability_status": status,
        "error": error,
        "verification_role": "non_blocking_external_daily_observation",
        "required_source_match_gate": False,
        "runtime_promotion_gate": False,
        "reason": (
            "krx_open_api_daily_response_not_a_completed_intraday_validation_basis"
            if status != "pass"
            else "available_non_blocking_external_daily_observation"
        ),
    }


def _find_nested(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = _find_nested(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_nested(child, key)
            if found is not None:
                return found
    return None


def _payload_context(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    exact = payload.get("exact_payload")
    source = exact if isinstance(exact, dict) else payload
    entry = source.get("entry_candle_context")
    if isinstance(entry, dict):
        return {
            "context_type": "entry",
            "venue": entry.get("venue"),
            "session": entry.get("session"),
            "request_code": entry.get("request_code"),
            "rest_route": entry.get("rest_route"),
            "bars": entry.get("bars"),
        }
    holding = source.get("holding_decision_context")
    if isinstance(holding, dict):
        candle = holding.get("candle")
        return {
            "context_type": "holding",
            "venue": holding.get("venue"),
            "session": holding.get("session"),
            "request_code": holding.get("request_code"),
            "rest_route": holding.get("rest_route"),
            "bars": candle.get("bars") if isinstance(candle, dict) else None,
        }
    return {}


def _payload_symbol(row: dict[str, Any]) -> str:
    payload = replay_source_input(row)
    context = _payload_context(payload)
    request_code = str(context.get("request_code") or "").strip()
    return str(
        row.get("symbol")
        or _find_nested(payload, "stock_code")
        or _find_nested(payload, "symbol")
        or request_code[:6]
        or ""
    ).strip()


def load_ai_payloads(target_date: str) -> dict[str, list[dict[str, Any]]]:
    path = PAYLOAD_DIR / f"ai_decision_payloads_{target_date}.jsonl"
    output: dict[str, list[dict[str, Any]]] = {}
    try:
        for row in iter_jsonl_objects_strict(path):
            symbol = _payload_symbol(row)
            if symbol:
                output.setdefault(symbol, []).append(row)
    except FileNotFoundError:
        return output
    return output


def enrich_payloads_with_response_provenance(
    target_date: str, payloads: dict[str, list[dict[str, Any]]]
) -> dict[str, list[dict[str, Any]]]:
    path = TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl"
    try:
        rows = list(iter_jsonl_objects_strict(path))
    except FileNotFoundError:
        return payloads
    by_request: dict[str, dict[str, Any]] = {}
    by_payload_hash: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        request_id = str(
            row.get("request_id") or row.get("decision_trace_id") or ""
        ).strip()
        if request_id:
            by_request[request_id] = row
        payload_hash = str(row.get("payload_sha256") or "").strip()
        if payload_hash:
            by_payload_hash.setdefault(payload_hash, []).append(row)
    output: dict[str, list[dict[str, Any]]] = {}
    for symbol, symbol_payloads in payloads.items():
        output[symbol] = []
        for payload in symbol_payloads:
            request_id = str(payload.get("request_id") or "").strip()
            response = by_request.get(request_id, {})
            if not response:
                payload_hash = str(payload.get("payload_sha256") or "").strip()
                hash_matches = by_payload_hash.get(payload_hash, [])
                if len(hash_matches) == 1:
                    response = hash_matches[0]
            output[symbol].append(
                {
                    **payload,
                    "_response_provenance": response,
                }
            )
    return output


def load_request_provenance(
    target_date: str,
) -> dict[str, list[dict[str, Any]]]:
    request_path = REQUEST_DIR / f"ai_decision_requests_{target_date}.jsonl"
    trace_path = TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl"
    traces: dict[str, dict[str, Any]] = {}
    try:
        for row in iter_jsonl_objects_strict(trace_path):
            request_id = str(
                row.get("request_id") or row.get("decision_trace_id") or ""
            ).strip()
            if request_id:
                traces[request_id] = row
    except FileNotFoundError:
        pass
    output: dict[str, list[dict[str, Any]]] = {}
    try:
        request_rows = list(iter_jsonl_objects_strict(request_path))
    except FileNotFoundError:
        return output
    for request in request_rows:
        request_id = str(request.get("request_id") or "").strip()
        response = traces.get(request_id, {})
        symbol = str(request.get("symbol") or "").strip()
        if not symbol:
            continue
        output.setdefault(symbol, []).append(
            {
                **request,
                "provider": response.get("provider_actual"),
                "model_id": response.get("model_id"),
                "transport": response.get("transport"),
                "provider_response_id": response.get("provider_response_id"),
                "response_sha256": response.get("response_sha256"),
                "response_ms": response.get("response_ms"),
                "input_tokens": response.get("input_tokens"),
                "output_tokens": response.get("output_tokens"),
                "total_tokens": response.get("total_tokens"),
                "failback_chain": response.get("failback_chain", []),
            }
        )
    return output


def _daily_from_kiwoom(df: Any, target_date: str) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {}
    target = target_date.replace("-", "")
    for index, row in df.iterrows():
        if getattr(index, "strftime", lambda _fmt: "")("%Y%m%d") != target:
            continue
        return {
            "open": _int(row.get("Open")),
            "high": _int(row.get("High")),
            "low": _int(row.get("Low")),
            "close": _int(row.get("Close")),
            "volume": _int(row.get("Volume")),
        }
    return {}


def _minute_by_time(
    rows: list[dict[str, Any]], target_date: str
) -> dict[str, dict[str, Any]]:
    target = target_date.replace("-", "")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        stamp = str(row.get("source_timestamp") or "")
        if not stamp.startswith(target) or len(stamp) < 12:
            continue
        output[f"{stamp[8:10]}:{stamp[10:12]}"] = row
    return output


def _ai_nested_value(payload: Any, key: str, child: str | None = None) -> Any:
    value = _find_nested(payload, key)
    if child and isinstance(value, dict):
        return value.get(child)
    return value


def _naver_observation_rows(
    rows: list[dict[str, Any]], target_date: str
) -> list[dict[str, Any]]:
    target_rows = [
        row for row in rows if str(row.get("timestamp") or "").startswith(target_date)
    ]
    deltas = naver_minute_volume_deltas(target_rows)
    output = []
    for row in target_rows:
        timestamp = str(row.get("timestamp") or "")
        if not timestamp.startswith(target_date):
            continue
        if any(
            _int(row.get(field)) is None for field in ("open", "high", "low", "close")
        ):
            continue
        minute = timestamp[11:16]
        volume_meta = deltas.get(minute, {})
        output.append(
            {
                "source_timestamp": (
                    target_date.replace("-", "") + minute.replace(":", "") + "00"
                ),
                "o": row.get("open"),
                "h": row.get("high"),
                "l": row.get("low"),
                "c": row.get("close"),
                "v": volume_meta.get("delta"),
                "partial_volume": not bool(volume_meta.get("comparable")),
            }
        )
    return output


def _independent_api_observation(
    rows: list[dict[str, Any]],
    *,
    target_date: str,
    venue: str,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    target = target_date.replace("-", "")
    session_start = "1600" if venue == "NXT" else "0900"
    session_end = "2359" if venue == "NXT" else "1519"
    normalized = []
    for row in rows:
        stamp = str(row.get("source_timestamp") or "")
        hhmm = stamp[8:12] if len(stamp) >= 12 else ""
        if not stamp.startswith(target) or not (session_start <= hhmm <= session_end):
            continue
        values = {
            "o": _int(row.get("시가", row.get("o"))),
            "h": _int(row.get("고가", row.get("h"))),
            "l": _int(row.get("저가", row.get("l"))),
            "c": _int(row.get("현재가", row.get("c"))),
            "v": _int(row.get("거래량", row.get("v"))),
        }
        if any(values[key] is None for key in ("o", "h", "l", "c", "v")):
            continue
        moment = datetime.strptime(stamp[:12], "%Y%m%d%H%M").replace(tzinfo=KST)
        if (
            as_of is not None
            and moment.date() == as_of.date()
            and moment + timedelta(minutes=1) > as_of
        ):
            continue
        normalized.append({"minute": moment, **values})
    normalized.sort(key=lambda item: item["minute"])
    missing = []
    for previous, current in zip(normalized, normalized[1:]):
        delta = int((current["minute"] - previous["minute"]).total_seconds() / 60)
        if delta > 1:
            missing.extend(
                (previous["minute"] + timedelta(minutes=offset)).strftime("%H:%M")
                for offset in range(1, delta)
            )
    quality = "pass" if normalized and not missing else "source_quality_blocked"
    total_volume = sum(row["v"] for row in normalized)
    vwap = (
        round(
            sum(
                ((row["h"] + row["l"] + row["c"]) / 3.0) * row["v"]
                for row in normalized
            )
            / total_volume,
            6,
        )
        if quality == "pass"
        and normalized[0]["minute"].strftime("%H%M") == session_start
        and total_volume > 0
        else None
    )
    opening_ranges = {}
    by_minute = {row["minute"]: row for row in normalized}
    if normalized:
        anchor = datetime.strptime(target + session_start, "%Y%m%d%H%M").replace(
            tzinfo=KST
        )
    else:
        anchor = None
    for minutes in (5, 15):
        expected = (
            [anchor + timedelta(minutes=index) for index in range(minutes)]
            if anchor
            else []
        )
        selected = [by_minute[item] for item in expected if item in by_minute]
        if len(selected) != minutes:
            opening_ranges[f"{minutes}m"] = {}
            continue
        opening_ranges[f"{minutes}m"] = {
            "open": selected[0]["o"],
            "high": max(row["h"] for row in selected),
            "low": min(row["l"] for row in selected),
            "close": selected[-1]["c"],
        }
    multi: dict[str, list[dict[str, Any]]] = {}
    for interval in (3, 5, 15):
        grouped: dict[int, list[dict[str, Any]]] = {}
        if anchor:
            for row in normalized:
                offset = int((row["minute"] - anchor).total_seconds() // 60)
                if offset >= 0:
                    grouped.setdefault(offset // interval, []).append(row)
        interval_rows = []
        for bucket, bucket_rows in sorted(grouped.items()):
            start = anchor + timedelta(minutes=bucket * interval)
            expected = {start + timedelta(minutes=index) for index in range(interval)}
            observed = {row["minute"] for row in bucket_rows}
            if expected != observed:
                continue
            interval_rows.append(
                {
                    "start": start.isoformat(),
                    "o": bucket_rows[0]["o"],
                    "h": max(row["h"] for row in bucket_rows),
                    "l": min(row["l"] for row in bucket_rows),
                    "c": bucket_rows[-1]["c"],
                    "v": sum(row["v"] for row in bucket_rows),
                    "source_quality": "pass",
                }
            )
        multi[f"{interval}m"] = interval_rows
    return {
        "source_quality": {"status": quality, "missing_minutes": missing[:60]},
        "session_bar_vwap": {"value": vwap},
        "opening_range_5m": opening_ranges["5m"],
        "opening_range_15m": opening_ranges["15m"],
        "multi_timeframe_bars": multi,
    }


def _append_derived_comparisons(
    rows: list[dict[str, Any]],
    *,
    api_observation: dict[str, Any],
    independent_observation: dict[str, Any],
    ai_payload: Any,
    venue: str,
    basis: dict[str, Any],
) -> None:
    api_quality = (api_observation.get("source_quality") or {}).get("status") == "pass"
    independent_quality = (independent_observation.get("source_quality") or {}).get(
        "status"
    ) == "pass"
    comparable = api_quality and independent_quality
    reason = "" if comparable else "derived_source_quality_not_comparable"
    rows.append(
        compare_value(
            field="derived.session_bar_vwap",
            api_raw_value=None,
            normalized_value=(api_observation.get("session_bar_vwap") or {}).get(
                "value"
            ),
            ai_payload_value=_ai_nested_value(ai_payload, "session_bar_vwap", "value"),
            external_value=(independent_observation.get("session_bar_vwap") or {}).get(
                "value"
            ),
            value_type="float",
            comparable=comparable,
            reason=reason,
            source="KIWOOM_RAW_INDEPENDENT_RECALCULATION",
            basis=basis,
        )
    )
    for minutes in (5, 15):
        api_range = api_observation.get(f"opening_range_{minutes}m") or {}
        external_range = independent_observation.get(f"opening_range_{minutes}m") or {}
        for field in ("open", "high", "low", "close"):
            rows.append(
                compare_value(
                    field=f"derived.opening_range_{minutes}m.{field}",
                    api_raw_value=None,
                    normalized_value=api_range.get(field),
                    ai_payload_value=_ai_nested_value(
                        ai_payload, f"opening_range_{minutes}m", field
                    ),
                    external_value=external_range.get(field),
                    value_type="integer",
                    comparable=comparable,
                    reason=reason,
                    source="KIWOOM_RAW_INDEPENDENT_RECALCULATION",
                    basis=basis,
                )
            )
    for interval in (3, 5, 15):
        api_bars = {
            str(item.get("start")): item
            for item in (
                (api_observation.get("multi_timeframe_bars") or {}).get(
                    f"{interval}m", []
                )
                or []
            )
            if item.get("source_quality") == "pass"
        }
        external_bars = {
            str(item.get("start")): item
            for item in (
                (independent_observation.get("multi_timeframe_bars") or {}).get(
                    f"{interval}m", []
                )
                or []
            )
            if item.get("source_quality") == "pass"
        }
        common = sorted(set(api_bars) & set(external_bars))
        if not common:
            continue
        start = common[-1]
        for field in ("o", "h", "l", "c", "v"):
            rows.append(
                compare_value(
                    field=f"derived.{interval}m.{start}.{field}",
                    api_raw_value=None,
                    normalized_value=api_bars[start].get(field),
                    ai_payload_value=None,
                    external_value=external_bars[start].get(field),
                    value_type="integer",
                    comparable=comparable,
                    reason=reason,
                    source="KIWOOM_RAW_INDEPENDENT_AGGREGATION",
                    basis=basis,
                )
            )


def _payload_rows_for_venue(
    payload_rows: list[dict[str, Any]],
    *,
    venue: str,
) -> list[dict[str, Any]]:
    selected = []
    expected = str(venue or "").upper()
    for row in payload_rows:
        context = _payload_context(replay_source_input(row))
        request_code = str(context.get("request_code") or "").upper()
        observed = str(context.get("venue") or row.get("effective_venue") or "").upper()
        if expected == "NXT":
            if request_code.endswith("_NX") or observed in {
                "NXT",
                "PREMARKET_KRX_LIKE",
            }:
                selected.append(row)
        elif not request_code.endswith("_NX") and observed not in {
            "NXT",
            "PREMARKET_KRX_LIKE",
        }:
            selected.append(row)
    return selected


def _payload_request_code(
    row: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> str:
    resolved = context or _payload_context(replay_source_input(row))
    explicit = str(resolved.get("request_code") or "").strip()
    if explicit:
        return explicit
    symbol = _payload_symbol(row)
    rest_route = str(resolved.get("rest_route") or "").strip().upper()
    return f"{symbol}{rest_route}" if symbol and rest_route.startswith("_") else symbol


def _payload_provider(row: dict[str, Any]) -> str:
    provenance = row.get("_response_provenance")
    if not isinstance(provenance, dict):
        return "none"
    return str(provenance.get("provider_actual") or "none").strip().lower()


def build_exact_payload_comparisons(
    *,
    payload_rows: list[dict[str, Any]],
    route_minutes: dict[str, list[dict[str, Any]]],
    target_date: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    observed_request_count = 0
    valid_exact_request_count = 0
    endpoint_counts: Counter[str] = Counter()
    observed_endpoint_counts: Counter[str] = Counter()
    provider_none_count = 0
    non_exact_payload_count = 0
    request_capture_missing_count = 0
    response_hash_missing_count = 0
    forming_bar_count = 0
    for payload_row in payload_rows:
        context = _payload_context(replay_source_input(payload_row))
        bars = context.get("bars")
        if not isinstance(bars, list) or not bars:
            continue
        observed_request_count += 1
        endpoint = str(payload_row.get("endpoint") or "unknown")
        observed_endpoint_counts[endpoint] += 1
        provenance = payload_row.get("_response_provenance")
        provenance = provenance if isinstance(provenance, dict) else {}
        provider = _payload_provider(payload_row)
        if provider == "none":
            provider_none_count += 1
        payload_exact = (
            payload_row.get("replay_exact") is True
            and payload_row.get("redacted") is not True
            and provenance.get("payload_replay_exact") is True
        )
        if not payload_exact:
            non_exact_payload_count += 1
        request_captured = provenance.get("request_capture_status") == "captured"
        if not request_captured:
            request_capture_missing_count += 1
        response_hash_present = bool(provenance.get("response_sha256"))
        if not response_hash_present:
            response_hash_missing_count += 1
        if not (
            payload_exact
            and request_captured
            and response_hash_present
            and provider != "none"
        ):
            continue
        valid_exact_request_count += 1
        endpoint_counts[endpoint] += 1
        request_code = _payload_request_code(payload_row, context)
        api_by_time = _minute_by_time(
            route_minutes.get(request_code, []),
            target_date,
        )
        request_id = str(
            payload_row.get("request_id")
            or provenance.get("request_id")
            or provenance.get("decision_trace_id")
            or ""
        ).strip()
        for bar in bars:
            if not isinstance(bar, dict):
                continue
            minute = str(bar.get("t") or bar.get("time") or bar.get("minute") or "")[:5]
            forming = bool(bar.get("forming", bar.get("is_forming", False)))
            partial = bool(
                bar.get(
                    "partial_volume",
                    bar.get("volume_is_partial", False),
                )
            )
            if forming or partial:
                forming_bar_count += 1
                continue
            api_row = api_by_time.get(minute)
            values = {
                "o": bar.get("o", bar.get("open")),
                "h": bar.get("h", bar.get("high")),
                "l": bar.get("l", bar.get("low")),
                "c": bar.get("c", bar.get("close")),
                "v": bar.get("v", bar.get("volume")),
            }
            api_values = {
                "o": (api_row or {}).get("시가", (api_row or {}).get("o")),
                "h": (api_row or {}).get("고가", (api_row or {}).get("h")),
                "l": (api_row or {}).get("저가", (api_row or {}).get("l")),
                "c": (api_row or {}).get("현재가", (api_row or {}).get("c")),
                "v": (api_row or {}).get("거래량", (api_row or {}).get("v")),
            }
            for field in ("o", "h", "l", "c", "v"):
                if api_row is None or _int(api_values[field]) is None:
                    status = "SOURCE_UNAVAILABLE"
                    reason = "same_route_api_minute_missing"
                elif _int(values[field]) == _int(api_values[field]):
                    status = "MATCH"
                    reason = None
                else:
                    status = "MISMATCH"
                    reason = "api_to_ai_payload_value_mismatch"
                rows.append(
                    {
                        "request_id": request_id or None,
                        "payload_sha256": payload_row.get("payload_sha256"),
                        "endpoint": payload_row.get("endpoint"),
                        "provider": provider,
                        "context_type": context.get("context_type"),
                        "request_code": request_code,
                        "venue": context.get("venue"),
                        "session": context.get("session"),
                        "minute": minute,
                        "field": field,
                        "api_raw_value": api_values[field],
                        "normalized_or_derived_value": _int(api_values[field]),
                        "ai_payload_value": values[field],
                        "status": status,
                        "reason": reason,
                        "comparison_basis": {
                            "target_date": target_date,
                            "request_code": request_code,
                            "venue": context.get("venue"),
                            "session": context.get("session"),
                            "completed_bar_only": True,
                        },
                    }
                )
    mismatches = [row for row in rows if row["status"] == "MISMATCH"]
    unavailable = [row for row in rows if row["status"] == "SOURCE_UNAVAILABLE"]
    return {
        "comparison_rows": rows,
        "summary": {
            "request_count": valid_exact_request_count,
            "observed_request_count": observed_request_count,
            "valid_exact_request_count": valid_exact_request_count,
            "endpoint_counts": dict(sorted(endpoint_counts.items())),
            "observed_endpoint_counts": dict(sorted(observed_endpoint_counts.items())),
            "comparable_field_count": sum(
                row["status"] in STRICT_STATUSES for row in rows
            ),
            "match_count": sum(row["status"] == "MATCH" for row in rows),
            "mismatch_count": len(mismatches),
            "source_unavailable_count": len(unavailable),
            "forming_bar_excluded_count": forming_bar_count,
            "forming_bar_included_count": 0,
            "provider_none_count": provider_none_count,
            "non_exact_payload_count": non_exact_payload_count,
            "request_capture_missing_count": request_capture_missing_count,
            "response_hash_missing_count": response_hash_missing_count,
            "required_payload_match_status": (
                "pass"
                if valid_exact_request_count
                and not mismatches
                and not unavailable
                and provider_none_count == 0
                else "fail"
            ),
        },
    }


def build_symbol_comparison(
    *,
    symbol: str,
    venue: str,
    target_date: str,
    kiwoom_daily: dict[str, Any],
    kiwoom_minutes: list[dict[str, Any]],
    external_daily: dict[str, Any] | None,
    naver_minutes: list[dict[str, Any]] | None,
    ai_payload_row: dict[str, Any] | None,
    ai_payload_rows: list[dict[str, Any]] | None = None,
    payload_route_minutes: dict[str, list[dict[str, Any]]] | None = None,
    source_meta: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, Any]:
    comparison_as_of = as_of or datetime.now(KST)
    if comparison_as_of.tzinfo is None:
        comparison_as_of = comparison_as_of.replace(tzinfo=KST)
    else:
        comparison_as_of = comparison_as_of.astimezone(KST)
    captured_at = comparison_as_of.isoformat()
    session = "aftermarket" if venue == "NXT" else "regular"
    basis = {
        "target_date": target_date,
        "venue": venue,
        "session": session,
        "adjusted_price": True,
        "completed_bar_only": True,
    }
    selected_payload_rows = list(ai_payload_rows or [])
    if not selected_payload_rows and ai_payload_row:
        selected_payload_rows = [ai_payload_row]
    representative_payload = selected_payload_rows[0] if selected_payload_rows else {}
    ai_payload = replay_source_input(representative_payload)
    observation = build_market_context_observation(
        kiwoom_minutes,
        symbol=symbol,
        venue=venue,
        session=session,
        target_date=target_date,
        captured_at=captured_at,
        previous_day={},
    )
    external_observation = build_market_context_observation(
        _naver_observation_rows(naver_minutes or [], target_date),
        symbol=symbol,
        venue=venue,
        session=session,
        target_date=target_date,
        captured_at=captured_at,
        previous_day={},
    )
    independent_observation = _independent_api_observation(
        kiwoom_minutes,
        target_date=target_date,
        venue=venue,
        as_of=comparison_as_of,
    )
    rows: list[dict[str, Any]] = []
    daily_source = str(
        source_meta.get("daily_external_source") or "KRX_OPEN_API_STOCK_DAILY"
    )
    daily_comparable_fields = set(
        source_meta.get(
            "daily_external_comparable_fields",
            ("open", "high", "low", "close", "volume"),
        )
    )
    target_day = date.fromisoformat(target_date)
    current_day_daily_final = target_day < comparison_as_of.date() or (
        target_day == comparison_as_of.date()
        and comparison_as_of.time() >= datetime.strptime("15:31", "%H:%M").time()
    )
    comparable_daily = venue == "KRX" and current_day_daily_final
    for field in ("open", "high", "low", "close", "volume"):
        field_comparable = comparable_daily and field in daily_comparable_fields
        rows.append(
            compare_value(
                field=f"daily.{field}",
                api_raw_value=kiwoom_daily.get(field),
                normalized_value=kiwoom_daily.get(field),
                ai_payload_value=_find_nested(ai_payload, f"previous_day_{field}"),
                external_value=(external_daily or {}).get(field),
                value_type="integer",
                comparable=field_comparable,
                reason=(
                    ""
                    if field_comparable
                    else (
                        "current_trading_day_daily_bar_not_final"
                        if venue == "KRX" and not current_day_daily_final
                        else (
                            "naver_daily_volume_snapshot_not_final_krx_basis"
                            if comparable_daily and field == "volume"
                            else "nxt_or_integrated_value_not_compared_with_krx_only"
                        )
                    )
                ),
                source=daily_source,
                basis=basis,
            )
        )

    target_naver_minutes = [
        row
        for row in (naver_minutes or [])
        if str(row.get("timestamp") or "").startswith(target_date)
    ]
    naver_by_time = {
        str(row.get("timestamp") or "")[11:16]: row for row in target_naver_minutes
    }
    naver_deltas = naver_minute_volume_deltas(target_naver_minutes)
    kiwoom_by_time = _minute_by_time(kiwoom_minutes, target_date)
    representative_context = _payload_context(ai_payload)
    representative_request_code = (
        _payload_request_code(
            representative_payload,
            representative_context,
        )
        if representative_payload
        else ""
    )
    same_report_route = representative_request_code in {
        "",
        symbol,
        symbol[:6],
    }
    ai_bars = representative_context.get("bars") if same_report_route else []
    ai_by_time = {
        str(row.get("t") or row.get("time") or row.get("minute") or "")[:5]: row
        for row in (ai_bars or [])
        if isinstance(row, dict)
    }
    completed_api_minutes = {
        str(row.get("t") or "")[:5]
        for row in observation.get("bars_1m_completed", [])
        if isinstance(row, dict)
    }
    for minute in sorted(set(kiwoom_by_time) & set(naver_by_time)):
        api_row = kiwoom_by_time[minute]
        external_row = naver_by_time[minute]
        call_auction = minute == "15:30" and venue == "KRX"
        completed_minute = minute in completed_api_minutes or call_auction
        minute_moment = datetime.combine(
            target_day,
            datetime.strptime(minute, "%H:%M").time(),
            tzinfo=KST,
        )
        external_minute_stable = (
            target_day < comparison_as_of.date()
            or minute_moment + NAVER_MINUTE_PUBLICATION_LAG <= comparison_as_of
        )
        minute_comparable = (
            venue == "KRX"
            and completed_minute
            and external_minute_stable
            and not call_auction
        )
        if not completed_minute:
            minute_reason = "forming_minute_excluded_exact_capture_cutoff"
        elif call_auction:
            minute_reason = "krx_closing_call_auction_separate_aggregation"
        elif not external_minute_stable:
            minute_reason = "naver_minute_publication_lag_window"
        elif venue != "KRX":
            minute_reason = "naver_integrated_or_unknown_venue_basis"
        else:
            minute_reason = ""
        rows.append(
            compare_value(
                field=f"minute.{minute}.close",
                api_raw_value=api_row.get("현재가"),
                normalized_value=_int(api_row.get("현재가")),
                ai_payload_value=(
                    (ai_by_time.get(minute) or {}).get(
                        "c",
                        (ai_by_time.get(minute) or {}).get("close"),
                    )
                ),
                external_value=external_row.get("close"),
                value_type="integer",
                comparable=minute_comparable,
                reason=minute_reason,
                source="NAVER_FCHART_MINUTE",
                basis={**basis, "minute": minute},
            )
        )
        delta = naver_deltas.get(minute, {})
        opening_call_auction = minute == "09:00" and venue == "KRX"
        if not completed_minute:
            volume_reason = "forming_minute_excluded_exact_capture_cutoff"
        elif opening_call_auction:
            volume_reason = "krx_opening_call_auction_cumulative_basis"
        elif call_auction:
            volume_reason = "krx_closing_call_auction_separate_aggregation"
        elif not external_minute_stable:
            volume_reason = "naver_minute_publication_lag_window"
        else:
            volume_reason = str(delta.get("reason") or "")
        rows.append(
            compare_value(
                field=f"minute.{minute}.volume",
                api_raw_value=api_row.get("거래량"),
                normalized_value=_int(api_row.get("거래량")),
                ai_payload_value=(
                    (ai_by_time.get(minute) or {}).get(
                        "v",
                        (ai_by_time.get(minute) or {}).get("volume"),
                    )
                ),
                external_value=delta.get("delta"),
                value_type="integer",
                comparable=bool(
                    venue == "KRX"
                    and completed_minute
                    and external_minute_stable
                    and not opening_call_auction
                    and not call_auction
                    and delta.get("comparable")
                ),
                reason=volume_reason,
                source="NAVER_FCHART_CUMULATIVE_VOLUME_DELTA",
                basis={**basis, "minute": minute},
            )
        )
    _append_derived_comparisons(
        rows,
        api_observation=observation,
        independent_observation=independent_observation,
        ai_payload=ai_payload,
        venue=venue,
        basis=basis,
    )
    comparable_rows = [row for row in rows if row["status"] in STRICT_STATUSES]
    mismatches = [row for row in comparable_rows if row["status"] == "MISMATCH"]
    exact_payload = build_exact_payload_comparisons(
        payload_rows=selected_payload_rows,
        route_minutes=dict(payload_route_minutes or {}),
        target_date=target_date,
    )
    source_quality_pass = (observation.get("source_quality") or {}).get(
        "status"
    ) == "pass"
    return {
        "symbol": symbol,
        "venue": venue,
        "comparison_rows": rows,
        "summary": {
            "row_count": len(rows),
            "comparable_count": len(comparable_rows),
            "match_count": sum(row["status"] == "MATCH" for row in rows),
            "mismatch_count": len(mismatches),
            "not_comparable_count": sum(
                row["status"] == "NOT_COMPARABLE" for row in rows
            ),
            "source_unavailable_count": sum(
                row["status"] == "SOURCE_UNAVAILABLE" for row in rows
            ),
            "required_source_field_match_status": (
                "pass"
                if comparable_rows and not mismatches and source_quality_pass
                else "fail"
            ),
            "source_quality_gate_status": (
                "pass" if source_quality_pass else "source_quality_blocked"
            ),
        },
        "market_context_observation": observation,
        "external_recalculation_observation": external_observation,
        "independent_api_recalculation": independent_observation,
        "ai_payload_exact_validation": exact_payload,
        "source_meta": _sanitize_metadata(source_meta),
        "ai_request_provenance": {
            "request_id": representative_payload.get("request_id"),
            "request_envelope_sha256": representative_payload.get(
                "request_envelope_sha256"
            ),
            "payload_sha256": representative_payload.get("payload_sha256"),
            "prompt_sha256": representative_payload.get("prompt_sha256"),
            "endpoint": representative_payload.get("endpoint"),
            "model": representative_payload.get("model"),
            "provider": (representative_payload.get("_response_provenance") or {}).get(
                "provider_actual"
            ),
            "model_id": (representative_payload.get("_response_provenance") or {}).get(
                "model_id"
            ),
            "transport": (representative_payload.get("_response_provenance") or {}).get(
                "transport"
            ),
            "provider_response_id": (
                representative_payload.get("_response_provenance") or {}
            ).get("provider_response_id"),
            "response_sha256": (
                representative_payload.get("_response_provenance") or {}
            ).get("response_sha256"),
            "response_ms": (
                representative_payload.get("_response_provenance") or {}
            ).get("response_ms"),
            "input_tokens": (
                representative_payload.get("_response_provenance") or {}
            ).get("input_tokens"),
            "output_tokens": (
                representative_payload.get("_response_provenance") or {}
            ).get("output_tokens"),
            "total_tokens": (
                representative_payload.get("_response_provenance") or {}
            ).get("total_tokens"),
            "failback_chain": (
                representative_payload.get("_response_provenance") or {}
            ).get("failback_chain", []),
        },
        "ai_request_provenance_rows": source_meta.get("ai_request_provenance_rows", []),
    }


def build_live_report(
    target_date: str,
    symbols: list[str],
    *,
    provenance_date: str | None = None,
) -> dict[str, Any]:
    from src.utils import kiwoom_utils

    capture_date = _validated_provenance_date(target_date, provenance_date)
    comparison_as_of = datetime.now(KST)
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        raise RuntimeError("Kiwoom token unavailable")
    payloads = enrich_payloads_with_response_provenance(
        capture_date, load_ai_payloads(capture_date)
    )
    request_provenance = load_request_provenance(capture_date)
    try:
        krx_daily, krx_meta = _fetch_krx_daily(target_date)
        krx_error = krx_meta.get("error")
    except Exception as exc:
        krx_daily, krx_meta = {}, {}
        krx_error = f"{type(exc).__name__}:{exc}"
    krx_daily_observation = _krx_daily_verification_observation(krx_meta)
    results = []
    minute_route_cache: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}

    def _route_minutes(
        request_code: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        cached = minute_route_cache.get(request_code)
        if cached is not None:
            return cached
        fetched = kiwoom_utils.get_minute_candles_ka10080_with_meta(
            token,
            request_code,
            limit=1200,
            explicit_request_code=True,
        )
        resolved = (list(fetched[0] or []), dict(fetched[1] or {}))
        minute_route_cache[request_code] = resolved
        return resolved

    for request_symbol in symbols:
        venue = "NXT" if request_symbol.upper().endswith("_NX") else "KRX"
        symbol = request_symbol[:6]
        daily = _daily_from_kiwoom(
            kiwoom_utils.get_daily_data_ka10005_df(token, request_symbol),
            target_date,
        )
        minutes, minute_meta = _route_minutes(request_symbol)
        symbol_payload_rows = payloads.get(symbol, [])
        selected_payload_rows = _payload_rows_for_venue(
            symbol_payload_rows,
            venue=venue,
        )
        payload_route_minutes: dict[str, list[dict[str, Any]]] = {}
        for payload_row in selected_payload_rows:
            context = _payload_context(replay_source_input(payload_row))
            payload_request_code = _payload_request_code(
                payload_row,
                context,
            )
            route_rows, _route_meta = _route_minutes(payload_request_code)
            payload_route_minutes[payload_request_code] = route_rows
        try:
            naver_minutes, naver_meta = _fetch_naver_chart(symbol, "minute", count=1200)
            naver_daily_rows, naver_daily_meta = _fetch_naver_chart(
                symbol, "day", count=20
            )
            naver_error = None
        except Exception as exc:
            naver_minutes, naver_meta = [], {}
            naver_daily_rows, naver_daily_meta = [], {}
            naver_error = f"{type(exc).__name__}:{exc}"
        naver_daily = next(
            (
                row
                for row in naver_daily_rows
                if str(row.get("timestamp") or "") == target_date
            ),
            None,
        )
        external_daily = krx_daily.get(symbol) or naver_daily
        daily_source = (
            "KRX_OPEN_API_STOCK_DAILY"
            if krx_daily.get(symbol)
            else "NAVER_FCHART_DAILY"
        )
        daily_external_comparable_fields = (
            ("open", "high", "low", "close", "volume")
            if krx_daily.get(symbol)
            else ("open", "high", "low", "close")
        )
        results.append(
            build_symbol_comparison(
                symbol=request_symbol,
                venue=venue,
                target_date=target_date,
                kiwoom_daily=daily,
                kiwoom_minutes=minutes,
                external_daily=external_daily,
                naver_minutes=naver_minutes,
                ai_payload_row=(
                    selected_payload_rows[0] if selected_payload_rows else None
                ),
                ai_payload_rows=selected_payload_rows,
                payload_route_minutes=payload_route_minutes,
                source_meta={
                    "kiwoom": minute_meta,
                    "krx": krx_meta,
                    "krx_error": krx_error,
                    "krx_daily_verification_observation": krx_daily_observation,
                    "naver": naver_meta,
                    "naver_daily": naver_daily_meta,
                    "daily_external_source": daily_source,
                    "daily_external_comparable_fields": (
                        daily_external_comparable_fields
                    ),
                    "naver_error": naver_error,
                    "ai_request_provenance_rows": request_provenance.get(
                        request_symbol,
                        request_provenance.get(symbol, []),
                    ),
                },
                as_of=comparison_as_of,
            )
        )
    mismatch_count = sum(item["summary"]["mismatch_count"] for item in results)
    payload_mismatch_count = sum(
        (item.get("ai_payload_exact_validation", {}).get("summary", {})).get(
            "mismatch_count", 0
        )
        for item in results
    )
    payload_source_unavailable_count = sum(
        (item.get("ai_payload_exact_validation", {}).get("summary", {})).get(
            "source_unavailable_count", 0
        )
        for item in results
    )
    provider_none = []
    for item in results:
        exact_summary = item.get("ai_payload_exact_validation", {}).get("summary", {})
        if exact_summary.get("provider_none_count", 0):
            provider_none.append(item["symbol"])
            continue
        provenance_rows = item.get("ai_request_provenance_rows") or []
        if provenance_rows:
            if any(
                str(row.get("provider") or "none").lower() == "none"
                for row in provenance_rows
            ):
                provider_none.append(item["symbol"])
            continue
        if (
            item["ai_request_provenance"].get("endpoint")
            and str(item["ai_request_provenance"].get("provider") or "none").lower()
            == "none"
        ):
            provider_none.append(item["symbol"])
    # This is the KRX *intraday source/payload* gate.  It deliberately does
    # not consume the KRX daily Open API observation above.
    krx_intraday_required_failed = any(
        item["venue"] == "KRX"
        and item["summary"]["required_source_field_match_status"] != "pass"
        for item in results
    )
    payload_required_failed = any(
        (item.get("ai_payload_exact_validation", {}).get("summary", {})).get(
            "required_payload_match_status"
        )
        != "pass"
        for item in results
    )
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(KST).isoformat(),
        "comparison_as_of": comparison_as_of.isoformat(),
        "date": target_date,
        "provenance_capture_date": capture_date,
        "provenance_join_policy": (
            "explicit_forensic_replay_market_date_to_capture_date"
            if capture_date != target_date
            else "same_date_natural_capture"
        ),
        "status": (
            "pass"
            if mismatch_count == 0
            and payload_mismatch_count == 0
            and payload_source_unavailable_count == 0
            and not provider_none
            and not krx_intraday_required_failed
            and not payload_required_failed
            else "fail"
        ),
        "summary": {
            "symbol_count": len(results),
            "mismatch_count": mismatch_count,
            "payload_mismatch_count": payload_mismatch_count,
            "payload_source_unavailable_count": (payload_source_unavailable_count),
            "provider_none_count": len(provider_none),
            "krx_daily_non_blocking_unavailable": (
                krx_daily_observation["availability_status"] != "pass"
            ),
        },
        "results": results,
        "external_source_policy": {
            "daily_stock_preferred_when_available": "KRX_OPEN_API_STOCK_DAILY_AUTH_KEY",
            "daily_stock_intraday_verification": "NAVER_FCHART_DAILY_OHLC_ONLY",
            "krx_open_api_daily_unavailable": "non_blocking_external_daily_observation",
            "krx_open_api_daily_required_source_match_gate": False,
            "krx_open_api_daily_runtime_promotion_gate": False,
            "legacy_krx_mdc_web_json": "disabled_logout_session_dependency",
            "minute_close_volume_secondary": "NAVER_FCHART",
            "nxt_integrated_not_equal_to_krx": True,
            "closing_call_auction_separate": True,
        },
        **OBSERVATION_CONTRACT,
    }


def _write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report["date"])
    json_path = REPORT_DIR / f"ai_input_external_validation_{target_date}.json"
    md_path = REPORT_DIR / f"ai_input_external_validation_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# AI input external validation — {target_date}",
        "",
        f"- Status: `{report['status']}`",
        f"- Mismatch: `{report['summary']['mismatch_count']}`",
        (
            "- Exact payload mismatch: "
            f"`{report['summary'].get('payload_mismatch_count', 0)}`"
        ),
        (
            "- KRX daily Open API unavailable (non-blocking): "
            f"`{str(report['summary'].get('krx_daily_non_blocking_unavailable', False)).lower()}`"
        ),
        f"- Runtime effect: `{str(report['runtime_effect']).lower()}`",
        "",
        (
            "| Symbol | Venue | Comparable | Match | Mismatch | "
            "Not comparable | Payload requests | Payload fields | "
            "Payload mismatch |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["results"]:
        summary = item["summary"]
        payload_summary = item.get("ai_payload_exact_validation", {}).get("summary", {})
        lines.append(
            f"| {item['symbol']} | {item['venue']} | {summary['comparable_count']} | "
            f"{summary['match_count']} | {summary['mismatch_count']} | "
            f"{summary['not_comparable_count']} | "
            f"{payload_summary.get('request_count', 0)} | "
            f"{payload_summary.get('comparable_field_count', 0)} | "
            f"{payload_summary.get('mismatch_count', 0)} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare observation-only scalping AI inputs with external data."
    )
    parser.add_argument("--date", dest="target_date", required=True)
    parser.add_argument(
        "--provenance-date",
        help=(
            "Date of the immutable request/trace/payload ledger. "
            "Defaults to --date; use a later date only for explicit forensic replay."
        ),
    )
    parser.add_argument(
        "--symbols",
        default=("005930,096770,100090," "005930_NX,096770_NX,100090_NX"),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    report = build_live_report(
        args.target_date,
        symbols,
        provenance_date=args.provenance_date,
    )
    if args.write:
        json_path, md_path = _write_report(report)
        report["artifacts"] = [str(json_path), str(md_path)]
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
