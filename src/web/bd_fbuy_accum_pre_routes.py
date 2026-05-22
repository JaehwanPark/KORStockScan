"""BD_FBUY_ACCUM_PRE_V1 dashboard routes.

The route is query-only. It exposes DB-first accumulation candidates and does
not submit orders, mutate runtime thresholds, change providers, or create
approval/workorder artifacts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, render_template_string, request

from src.engine.bd_fbuy_accum_pre_scanner import load_or_build_report


bd_fbuy_accum_pre_bp = Blueprint("bd_fbuy_accum_pre", __name__)


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_number(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "-"


def _format_won_eok(value: Any) -> str:
    try:
        return f"{float(value) / 100_000_000:.1f}억"
    except (TypeError, ValueError):
        return "-"


def _format_ratio(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _sparkline_points(rows: list[dict[str, Any]], key: str, width: int = 260, height: int = 58) -> str:
    values = [_to_float(row.get(key)) for row in rows if row.get(key) is not None]
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo if hi != lo else 1.0
    denom = max(1, len(values) - 1)
    return " ".join(
        f"{idx * width / denom:.1f},{height - ((value - lo) / span * height):.1f}"
        for idx, value in enumerate(values)
    )


def _enrich_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in report.get("candidates") or []:
        item = dict(row)
        live = item.get("live_confirmation") if isinstance(item.get("live_confirmation"), dict) else {}
        history = item.get("history") if isinstance(item.get("history"), dict) else {}
        item.update(
            {
                "star_score_display": _format_ratio(item.get("star_score"), 2),
                "close_display": _format_number(item.get("close_price")),
                "dist_low20_display": _format_ratio(item.get("dist_low20_pct"), 2),
                "dist_ma5_display": _format_ratio(item.get("dist_ma5_pct"), 2),
                "vol_ratio_display": _format_ratio(item.get("vol_med20_ratio"), 2),
                "foreign_qty_ratio_display": _format_ratio(item.get("foreign_qty_medvol20_ratio")),
                "foreign_amt_ratio_display": _format_ratio(item.get("foreign_amt_medvalue20_ratio")),
                "traded_value_display": _format_won_eok(item.get("traded_value")),
                "med_value_display": _format_won_eok(item.get("med_value20")),
                "live_foreign_display": _format_number(live.get("today_foreign_broker_est_net_qty")),
                "live_source_label": "DB 외인" if live.get("source") == "daily_stock_quotes" else "WS 외국계",
                "live_quality": live.get("source_quality") or "missing",
                "spread_display": _format_ratio(live.get("spread_bps"), 1) if live.get("spread_bps") else "-",
                "price_points": _sparkline_points(history.get("price") or [], "close"),
                "volume_points": _sparkline_points(history.get("volume") or [], "volume"),
                "foreign_points": _sparkline_points(history.get("foreign") or [], "foreign_net"),
            }
        )
        rows.append(item)
    return rows


def _load_request_report() -> tuple[dict[str, Any], bool]:
    target_date = (request.values.get("date") or datetime.now().strftime("%Y-%m-%d")).strip()
    refresh = str(request.values.get("refresh") or "0").lower() in {"1", "true", "yes", "on"}
    live_intraday = str(request.values.get("live") or "1").lower() in {"1", "true", "yes", "on"}
    return load_or_build_report(target_date, refresh=refresh, live_intraday=live_intraday), live_intraday


@bd_fbuy_accum_pre_bp.route("/api/investor-margin")
def bd_fbuy_accum_pre_api():
    report, _ = _load_request_report()
    return jsonify({"ok": True, "mode": "bd_fbuy_accum_pre", **report})


@bd_fbuy_accum_pre_bp.route("/investor-margin")
def bd_fbuy_accum_pre_view():
    report, live_intraday = _load_request_report()
    rows = _enrich_rows(report)
    rebound_rows = _enrich_rows({"candidates": report.get("rebound_expansion_candidates") or []})
    summary = report.get("summary") or {}
    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>BD_FBUY_ACCUM_PRE_V1</title>
      <style>
        :root { --bg:#f6f7f8; --panel:#fff; --ink:#18212b; --muted:#657282; --line:#d9e0e7; --accent:#0f766e; --warn:#a16207; --good:#047857; }
        body { margin:0; background:var(--bg); color:var(--ink); font-family:"Pretendard","Noto Sans KR",sans-serif; }
        .wrap { max-width:1440px; margin:0 auto; padding:18px 14px 36px; }
        .top { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:14px; }
        h1 { margin:0 0 4px; font-size:24px; }
        .sub { color:var(--muted); font-size:13px; }
        .actions { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
        .btn { border:1px solid var(--line); background:#fff; color:var(--ink); text-decoration:none; padding:8px 11px; border-radius:8px; font-size:13px; }
        .btn.primary { background:var(--accent); color:#fff; border-color:var(--accent); }
        .summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:8px; margin-bottom:12px; }
        .metric { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:10px; }
        .metric .k { color:var(--muted); font-size:12px; }
        .metric .v { font-size:20px; font-weight:800; margin-top:3px; }
        .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; }
        .section-title { display:flex; justify-content:space-between; gap:12px; align-items:baseline; padding:14px 12px 6px; }
        .section-title h2 { margin:0; font-size:18px; }
        .section-title .desc { color:var(--muted); font-size:12px; }
        table { width:100%; border-collapse:collapse; }
        th,td { border-bottom:1px solid var(--line); padding:8px 7px; text-align:left; font-size:12px; vertical-align:middle; white-space:nowrap; }
        th { color:var(--muted); font-weight:700; background:#f9fafb; position:sticky; top:0; z-index:1; }
        tr:hover td { background:#fbfcfd; }
        .stars { color:#b7791f; font-weight:800; letter-spacing:0; }
        .score { color:var(--muted); font-size:11px; margin-left:4px; }
        .code { font-weight:800; }
        .name { color:var(--muted); margin-left:4px; }
        .bucket { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:2px 7px; background:#f8fafc; }
        .live-ok { color:var(--good); font-weight:700; }
        .live-miss,.live-stale { color:var(--warn); }
        .spark svg { display:block; width:128px; height:34px; }
        .spark polyline { fill:none; stroke-width:2; }
        .price { stroke:#0f766e; } .ma5 { stroke:#2563eb; } .low20 { stroke:#94a3b8; } .vol { stroke:#64748b; } .foreign { stroke:#b7791f; }
        .meta { color:var(--muted); font-size:12px; padding:10px 12px; border-top:1px solid var(--line); }
        .scroll { overflow:auto; max-height:calc(100vh - 190px); }
        @media (max-width:900px) { .top { display:block; } .actions { justify-content:flex-start; margin-top:10px; } th,td { font-size:11px; padding:7px 6px; } }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="top">
          <div>
            <h1>BD_FBUY_ACCUM_PRE_V1</h1>
            <div class="sub">바닥다지기 + 적정 거래량 + 전일/금일 외인 유입 후보 조회</div>
          </div>
          <div class="actions">
            <a class="btn primary" href="/investor-margin?date={{ report.target_date }}&refresh=1&live={{ 1 if live_intraday else 0 }}">새로고침</a>
            <a class="btn" href="/investor-margin?date={{ report.target_date }}&live={{ 0 if live_intraday else 1 }}">live {{ 'OFF' if live_intraday else 'ON' }}</a>
          </div>
        </div>
        <div class="summary">
          <div class="metric"><div class="k">기준일</div><div class="v">{{ report.effective_db_date }}</div></div>
          <div class="metric"><div class="k">DB PASS</div><div class="v">{{ summary.db_pass_count }}</div></div>
          <div class="metric"><div class="k">반등 확장</div><div class="v">{{ summary.rebound_expansion_count }}</div></div>
          <div class="metric"><div class="k">live-confirmed</div><div class="v">{{ (summary.live_confirmed_count or 0) + (summary.rebound_live_confirmed_count or 0) }}</div></div>
          <div class="metric"><div class="k">갱신</div><div class="v">10분</div></div>
          <div class="metric"><div class="k">생성시각</div><div class="v" style="font-size:14px">{{ report.generated_at }}</div></div>
        </div>
        <div class="panel">
          <div class="section-title">
            <div>
              <h2>바닥다지기 + 적정 거래량 + 외인 유입 후보</h2>
              <div class="desc">20일 저점 근처에서 외인 유입이 누적되는 DB-first 후보</div>
            </div>
            <div class="desc">{{ rows|length }}개</div>
          </div>
          <div class="scroll">
            <table>
              <thead>
                <tr>
                  <th>별점</th><th>종목</th><th>현재가</th><th>저점%</th><th>5MA%</th><th>streak</th>
                  <th>외인 수량비</th><th>외인 금액비</th><th>vol20x</th><th>거래대금</th><th>유동성</th>
                  <th>금일 외국계</th><th>spread</th><th>가격</th><th>거래량</th><th>외인60</th>
                </tr>
              </thead>
              <tbody>
                {% for row in rows %}
                <tr>
                  <td><span class="stars">{{ row.star_display }}</span><span class="score">{{ row.star_score_display }}</span></td>
                  <td><span class="code">{{ row.stock_code }}</span><span class="name">{{ row.stock_name }}</span></td>
                  <td>{{ row.close_display }}</td>
                  <td>{{ row.dist_low20_display }}</td>
                  <td>{{ row.dist_ma5_display }}</td>
                  <td>{{ row.foreign_positive_streak }}</td>
                  <td>{{ row.foreign_qty_ratio_display }}</td>
                  <td>{{ row.foreign_amt_ratio_display }}</td>
                  <td>{{ row.vol_ratio_display }} <span class="bucket">{{ row.volume_bucket }}</span></td>
                  <td>{{ row.traded_value_display }} / {{ row.med_value_display }}</td>
                  <td><span class="bucket">{{ row.liquidity_bucket }}</span></td>
                  <td class="{% if row.live_confirmed %}live-ok{% elif row.live_quality == 'stale_ws_snapshot' %}live-stale{% else %}live-miss{% endif %}">{{ row.live_foreign_display }}<br><span class="score">{{ row.live_source_label }} · {{ row.live_quality }}</span></td>
                  <td>{{ row.spread_display }}</td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="price" points="{{ row.price_points }}"/></svg></td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="vol" points="{{ row.volume_points }}"/></svg></td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="foreign" points="{{ row.foreign_points }}"/></svg></td>
                </tr>
                {% else %}
                <tr><td colspan="16">조건을 만족한 후보가 없습니다.</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel" style="margin-top:14px;">
          <div class="section-title">
            <div>
              <h2>이미 반등이 시작됐고 외인이 거래량을 동반해 따라붙는 후보</h2>
              <div class="desc">저점권을 벗어난 뒤 외인 유입과 거래량 확장이 같이 나온 후보</div>
            </div>
            <div class="desc">{{ rebound_rows|length }}개</div>
          </div>
          <div class="scroll">
            <table>
              <thead>
                <tr>
                  <th>별점</th><th>종목</th><th>현재가</th><th>저점%</th><th>5MA%</th><th>streak</th>
                  <th>외인 수량비</th><th>외인 금액비</th><th>vol20x</th><th>거래대금</th><th>유동성</th>
                  <th>금일 외국계</th><th>spread</th><th>가격</th><th>거래량</th><th>외인60</th>
                </tr>
              </thead>
              <tbody>
                {% for row in rebound_rows %}
                <tr>
                  <td><span class="stars">{{ row.star_display }}</span><span class="score">{{ row.star_score_display }}</span></td>
                  <td><span class="code">{{ row.stock_code }}</span><span class="name">{{ row.stock_name }}</span></td>
                  <td>{{ row.close_display }}</td>
                  <td>{{ row.dist_low20_display }}</td>
                  <td>{{ row.dist_ma5_display }}</td>
                  <td>{{ row.foreign_positive_streak }}</td>
                  <td>{{ row.foreign_qty_ratio_display }}</td>
                  <td>{{ row.foreign_amt_ratio_display }}</td>
                  <td>{{ row.vol_ratio_display }} <span class="bucket">{{ row.volume_bucket }}</span></td>
                  <td>{{ row.traded_value_display }} / {{ row.med_value_display }}</td>
                  <td><span class="bucket">{{ row.liquidity_bucket }}</span></td>
                  <td class="{% if row.live_confirmed %}live-ok{% elif row.live_quality == 'stale_ws_snapshot' %}live-stale{% else %}live-miss{% endif %}">{{ row.live_foreign_display }}<br><span class="score">{{ row.live_source_label }} · {{ row.live_quality }}</span></td>
                  <td>{{ row.spread_display }}</td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="price" points="{{ row.price_points }}"/></svg></td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="vol" points="{{ row.volume_points }}"/></svg></td>
                  <td class="spark"><svg viewBox="0 0 260 58"><polyline class="foreign" points="{{ row.foreign_points }}"/></svg></td>
                </tr>
                {% else %}
              <tr><td colspan="16">조건을 만족한 후보가 없습니다.</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        report=report,
        summary=summary,
        rows=rows,
        rebound_rows=rebound_rows,
        live_intraday=live_intraday,
    )
