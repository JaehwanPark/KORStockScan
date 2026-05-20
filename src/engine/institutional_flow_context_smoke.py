"""Live Kiwoom smoke test for institutional flow sources."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.institutional_flow_context import normalize_institutional_flow_context
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.utils import kiwoom_utils


SMOKE_DIR = REPORT_DIR / "institutional_flow_context" / "smoke"


def _market_hours_now() -> bool:
    now = datetime.now().time()
    return dtime(9, 0) <= now <= dtime(15, 30)


def _ok_rows(payload: dict[str, Any] | None) -> int:
    if not isinstance(payload, dict):
        return 0
    return int(payload.get("row_count") or 0)


def _sample_ws(token: str, code: str, sample_sec: float) -> tuple[dict[str, Any], str]:
    if sample_sec <= 0:
        return {}, "WS_NOT_REQUESTED"
    manager = KiwoomWSManager(token)
    try:
        manager.start()
        deadline = time.time() + min(max(float(sample_sec), 1.0), 20.0)
        while time.time() < deadline and not manager._session_ready.is_set():
            time.sleep(0.1)
        manager.execute_subscribe([code])
        latest: dict[str, Any] = {}
        while time.time() < deadline:
            latest = manager.get_latest_data(code) or {}
            received = latest.get("received_types") or set()
            if "0F" in received or "0w" in received:
                return latest, "PASS"
            time.sleep(0.2)
        return latest, "WS_NOT_AVAILABLE"
    except Exception as exc:
        return {"error": str(exc)}, "WS_ERROR"
    finally:
        manager.stop()


def run_smoke(code: str, target_date: str, *, live_kiwoom: bool, ws_sample_sec: float = 5.0) -> dict[str, Any]:
    code = str(code or "").strip().lstrip("A")
    target_compact = str(target_date).replace("-", "")
    result: dict[str, Any] = {
        "date": target_date,
        "code": code,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "live_kiwoom": bool(live_kiwoom),
        "token_ok": False,
        "endpoint_status": {},
        "warnings": [],
        "errors": [],
    }
    if not live_kiwoom:
        result["errors"].append("live_kiwoom_flag_required")
        return result
    try:
        token = kiwoom_utils.get_kiwoom_token()
        result["token_ok"] = bool(token)
        result["token_source"] = "kiwoom_utils.get_kiwoom_token"
    except Exception as exc:
        result["errors"].append(f"token_error:{exc}")
        token = None
    if not token:
        return result

    try:
        ka10059 = kiwoom_utils.get_investor_flow_summary_ka10059(token, code, base_dt=target_compact)
        result["endpoint_status"]["ka10059"] = {
            "pass": bool(ka10059),
            "row_count": 1 if ka10059 else 0,
            "smart_money_net": (ka10059 or {}).get("smart_money_net"),
        }
    except Exception as exc:
        result["endpoint_status"]["ka10059"] = {"pass": False, "error": str(exc), "row_count": 0}
        ka10059 = {}

    try:
        start_dt = target_compact
        ka10061 = kiwoom_utils.get_investor_period_total_ka10061(token, code, start_dt, target_compact)
        result["endpoint_status"]["ka10061"] = {
            "pass": _ok_rows(ka10061) > 0,
            "row_count": _ok_rows(ka10061),
            "smart_money_net": (ka10061 or {}).get("smart_money_net"),
        }
    except Exception as exc:
        result["endpoint_status"]["ka10061"] = {"pass": False, "error": str(exc), "row_count": 0}
        ka10061 = {}

    ka10064 = {}
    ws_data = {}
    if _market_hours_now():
        try:
            ka10064 = kiwoom_utils.get_intraday_investor_chart_ka10064(token, code, amt_qty_tp="2")
            result["endpoint_status"]["ka10064"] = {
                "pass": _ok_rows(ka10064) > 0,
                "row_count": _ok_rows(ka10064),
                "latest_time": (ka10064 or {}).get("latest_time"),
            }
        except Exception as exc:
            result["endpoint_status"]["ka10064"] = {"pass": False, "error": str(exc), "row_count": 0}
        ws_data, ws_status = _sample_ws(token, code, ws_sample_sec)
        received_types = sorted(list(ws_data.get("received_types") or [])) if isinstance(ws_data, dict) else []
        result["endpoint_status"]["WS_0F_0w"] = {
            "pass": ws_status == "PASS",
            "status": ws_status,
            "received_types": received_types,
            "foreign_broker_net_est_qty": (ws_data or {}).get("foreign_broker_net_est_qty") if isinstance(ws_data, dict) else None,
            "program_net_qty": (ws_data or {}).get("prog_net_qty") if isinstance(ws_data, dict) else None,
        }
        if ws_status != "PASS":
            result["warnings"].append(f"ws_sample_{ws_status.lower()}")
    else:
        result["endpoint_status"]["ka10064"] = {"pass": False, "row_count": 0, "status": "WS_NOT_AVAILABLE_OR_MARKET_CLOSED"}
        result["endpoint_status"]["WS_0F_0w"] = {"pass": False, "status": "WS_NOT_AVAILABLE_OR_MARKET_CLOSED"}
        result["warnings"].append("intraday_source_market_closed")

    context = normalize_institutional_flow_context(
        code,
        daily_summary=ka10059,
        period_summary=ka10061,
        intraday_chart_qty=ka10064,
        ws_data=ws_data,
    )
    result["normalized_context"] = context

    required = ["ka10059", "ka10061"]
    for endpoint in required:
        if not result["endpoint_status"].get(endpoint, {}).get("pass"):
            result["errors"].append(f"{endpoint}_required_parse_failed")
    if _market_hours_now() and not result["endpoint_status"].get("ka10064", {}).get("pass"):
        result["errors"].append("ka10064_intraday_required_during_market_failed")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run live Kiwoom institutional flow smoke test.")
    parser.add_argument("--code", required=True)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--live-kiwoom", action="store_true")
    parser.add_argument("--ws-sample-sec", type=float, default=5.0)
    args = parser.parse_args(argv)
    result = run_smoke(args.code, args.date, live_kiwoom=bool(args.live_kiwoom), ws_sample_sec=args.ws_sample_sec)
    SMOKE_DIR.mkdir(parents=True, exist_ok=True)
    out = SMOKE_DIR / f"institutional_flow_context_smoke_{args.date}_{str(args.code).lstrip('A')}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out), "endpoint_status": result.get("endpoint_status"), "warnings": result.get("warnings"), "errors": result.get("errors")}, ensure_ascii=False))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
