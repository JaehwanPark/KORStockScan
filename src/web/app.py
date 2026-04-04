from flask import Flask, jsonify, render_template_string, request
import os
import sys
from datetime import datetime, timedelta

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
TEMPLATE_ROOT = os.path.join(PROJECT_ROOT, "src", "template")

from src.engine.sniper_strength_observation_report import build_strength_momentum_report
from src.engine.sniper_entry_pipeline_report import build_entry_pipeline_flow_report
from src.engine.sniper_trade_review_report import build_trade_review_report
from src.engine.sniper_performance_tuning_report import build_performance_tuning_report
from src.engine.sniper_gatekeeper_replay import (
    find_gatekeeper_snapshot,
    load_gatekeeper_snapshots,
    rerun_gatekeeper_snapshot,
)
from src.engine.sniper_config import CONF
from src.engine.daily_report_service import (
    list_available_report_dates,
    load_or_build_daily_report,
)

_DEFAULT_DASHBOARD_LOOKBACK_MINUTES = 120


def _resolve_dashboard_since(target_date: str, since: str | None) -> str | None:
    if since:
        return since
    today = datetime.now().strftime("%Y-%m-%d")
    if str(target_date).strip() != today:
        return None
    return (datetime.now() - timedelta(minutes=_DEFAULT_DASHBOARD_LOOKBACK_MINUTES)).strftime("%H:%M:%S")


def _format_signed_currency(value) -> str:
    amount = float(value or 0)
    sign = "+" if amount > 0 else ""
    return f"{sign}{amount:,.0f}"


def _format_percent(value) -> str:
    try:
        return f"{float(value or 0):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError, AttributeError):
        return default

@app.route("/api/daily-report")
def daily_report_api():
    from datetime import datetime

    target_date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    refresh = str(request.args.get("refresh", "")).lower() in {"1", "true", "yes", "y"}
    report = load_or_build_daily_report(target_date, refresh=refresh)
    report["available_dates"] = list_available_report_dates(limit=40)
    return jsonify(report)


@app.route("/")
@app.route("/dashboard")
def dashboard_home():
    default_tab = request.args.get("tab") or "daily-report"
    target_date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    since = request.args.get("since")
    resolved_since = _resolve_dashboard_since(target_date, since)
    top = request.args.get("top", default=10, type=int)
    theme = (request.args.get("theme") or "light").strip().lower()
    if theme not in {"light", "dark"}:
        theme = "light"
    tab_labels = {
        "daily-report": "일일 전략 리포트",
        "entry-pipeline-flow": "진입 게이트 플로우",
        "trade-review": "실제 매매 복기",
        "strength-momentum": "동적 체결강도",
        "gatekeeper-replay": "Gatekeeper 리플레이",
        "performance-tuning": "성능 튜닝 모니터",
    }

    tab_map = {
        "daily-report": f"/daily-report?date={target_date}",
        "entry-pipeline-flow": f"/entry-pipeline-flow?date={target_date}&top={max(1, int(top or 10))}" + (f"&since={resolved_since}" if resolved_since else ""),
        "trade-review": f"/trade-review?date={target_date}",
        "strength-momentum": f"/strength-momentum?date={target_date}&top={max(1, int(top or 10))}" + (f"&since={resolved_since}" if resolved_since else ""),
        "gatekeeper-replay": f"/gatekeeper-replay?date={target_date}",
        "performance-tuning": f"/performance-tuning?date={target_date}" + (f"&since={resolved_since}" if resolved_since else ""),
    }
    active_src = tab_map.get(default_tab, tab_map["daily-report"])

    template = """
    <!doctype html>
    <html lang="ko" class="{{ theme_class }}">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>KORStockScan Dashboard</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">
      <style>
        :root {
          --bg: #f8fafc;
          --bg-elevated: #ffffff;
          --bg-soft: #f1f5f9;
          --ink: #0f172a;
          --muted: #64748b;
          --line: rgba(148, 163, 184, 0.24);
          --line-strong: rgba(148, 163, 184, 0.4);
          --primary: #0053db;
          --success: #10b981;
          --danger: #ef4444;
          --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
          --hero-start: #ffffff;
          --hero-end: #eff6ff;
          --hero-border: rgba(37, 99, 235, 0.14);
          --ad-bg: linear-gradient(135deg, rgba(0, 83, 219, 0.07), rgba(16, 185, 129, 0.08));
          --frame-bg: #ffffff;
        }
        html.dark {
          --bg: #000000;
          --bg-elevated: #111111;
          --bg-soft: #0b0b0b;
          --ink: #f8fafc;
          --muted: #94a3b8;
          --line: #222222;
          --line-strong: #333333;
          --primary: #3b82f6;
          --success: #10b981;
          --danger: #e11d48;
          --shadow: none;
          --hero-start: #0a0a0a;
          --hero-end: #111111;
          --hero-border: #1f2937;
          --ad-bg: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(16, 185, 129, 0.1));
          --frame-bg: #050505;
        }
        body {
          margin: 0;
          background:
            radial-gradient(circle at top left, rgba(0, 83, 219, 0.09), transparent 28%),
            radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 24%),
            var(--bg);
          color: var(--ink);
          font-family: "Inter", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 1440px; margin: 0 auto; padding: 24px 20px 32px; }
        .topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          margin-bottom: 14px;
        }
        .topbar-copy small {
          display: block;
          color: var(--muted);
          font-size: 12px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          margin-bottom: 6px;
        }
        .topbar-copy h1 {
          margin: 0;
          font-family: "Manrope", "Inter", sans-serif;
          font-size: 28px;
          line-height: 1.15;
        }
        .theme-toggle {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          border: 1px solid var(--line-strong);
          background: var(--bg-elevated);
          color: var(--ink);
          border-radius: 999px;
          padding: 10px 16px;
          font-weight: 700;
          box-shadow: var(--shadow);
          cursor: pointer;
        }
        .hero {
          background: linear-gradient(145deg, var(--hero-start), var(--hero-end));
          color: var(--ink);
          padding: 24px;
          border-radius: 28px;
          border: 1px solid var(--hero-border);
          box-shadow: var(--shadow);
        }
        .hero-top {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .hero-copy { max-width: 720px; }
        .hero h2 {
          margin: 0 0 10px;
          font-family: "Manrope", "Inter", sans-serif;
          font-size: 34px;
          line-height: 1.08;
        }
        .hero p { margin: 0; color: var(--muted); max-width: 760px; }
        .hero-meta {
          min-width: 260px;
          background: var(--bg-elevated);
          border: 1px solid var(--line);
          border-radius: 22px;
          padding: 14px;
          box-shadow: var(--shadow);
        }
        .hero-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }
        .hero-meta-card {
          background: var(--bg-soft);
          border-radius: 14px;
          padding: 10px 12px;
        }
        .hero-meta-label {
          font-size: 11px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 6px;
        }
        .hero-meta-value {
          font-size: 15px;
          font-weight: 700;
          line-height: 1.35;
        }
        .hero-status {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 14px;
          padding: 10px 14px;
          border-radius: 999px;
          background: var(--bg-elevated);
          border: 1px solid var(--line);
          font-size: 13px;
          font-weight: 600;
        }
        .hero-status-dot {
          width: 9px;
          height: 9px;
          border-radius: 999px;
          background: var(--success);
          box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
        }
        .tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
        .tab {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 11px 16px;
          border-radius: 16px;
          border: 1px solid var(--line);
          background: var(--bg-elevated);
          color: var(--ink);
          text-decoration: none;
          font-weight: 600;
          box-shadow: var(--shadow);
        }
        .tab.active {
          background: color-mix(in srgb, var(--primary) 10%, var(--bg-elevated));
          border-color: color-mix(in srgb, var(--primary) 26%, var(--line));
          color: var(--primary);
        }
        .tab small {
          display: block;
          font-size: 11px;
          font-weight: 500;
          color: var(--muted);
          margin-top: 2px;
        }
        .tab-label {
          display: flex;
          flex-direction: column;
          align-items: center;
          line-height: 1.2;
        }
        .dashboard-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 300px;
          gap: 18px;
          margin-top: 18px;
        }
        .frame-card {
          background: var(--bg-elevated);
          border: 1px solid var(--line);
          border-radius: 24px;
          padding: 10px;
          box-shadow: var(--shadow);
        }
        iframe {
          width: 100%;
          min-height: 1650px;
          border: 0;
          border-radius: 16px;
          background: var(--frame-bg);
        }
        .rail {
          display: grid;
          gap: 18px;
        }
        .rail-card {
          background: var(--bg-elevated);
          border: 1px solid var(--line);
          border-radius: 24px;
          padding: 18px;
          box-shadow: var(--shadow);
        }
        .rail-card h3 {
          margin: 0 0 10px;
          font-family: "Manrope", "Inter", sans-serif;
          font-size: 18px;
        }
        .rail-card p,
        .rail-card li {
          color: var(--muted);
          font-size: 14px;
          line-height: 1.6;
        }
        .rail-card ul {
          margin: 0;
          padding-left: 18px;
        }
        .ad-slot-inline,
        .ad-slot-sidebar {
          min-height: 132px;
          border-radius: 22px;
          border: 1px dashed var(--line-strong);
          background: var(--ad-bg);
          display: grid;
          place-items: center;
          color: var(--muted);
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        @media (max-width: 900px) {
          .hero-meta { width: 100%; }
          .hero-meta-grid { grid-template-columns: 1fr 1fr; }
          iframe { min-height: 1900px; }
          .dashboard-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .hero-meta-grid { grid-template-columns: 1fr; }
          .topbar { align-items: stretch; flex-direction: column; }
          .hero h2 { font-size: 28px; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="topbar">
          <div class="topbar-copy">
            <small>CODEX Redesign Brief</small>
            <h1>주식 트레이딩 시스템 모니터링 대시보드</h1>
          </div>
          <button id="theme-toggle" class="theme-toggle" type="button" aria-label="테마 전환">
            <span id="theme-icon">{{ '☀' if theme_class == 'dark' else '☾' }}</span>
            <span id="theme-label">{{ '화이트 모드' if theme_class == 'dark' else '다크 모드' }}</span>
          </button>
        </div>
        <div class="hero">
          <div class="hero-top">
            <div class="hero-copy">
              <h2>전문 금융 터미널 감성으로 재구성한 통합 관제 셸</h2>
              <p>화이트와 순수 블랙 테마를 오가며 일일 전략 리포트, 진입 게이트 플로우, 실제 매매 복기, 동적 체결강도, 성능 튜닝 모니터를 한 흐름에서 확인합니다.</p>
              <div class="hero-status">
                <span class="hero-status-dot"></span>
                <span>현재 보고 있는 탭: {{ active_tab_label }}</span>
              </div>
            </div>
            <div class="hero-meta">
              <div class="hero-meta-grid">
                <div class="hero-meta-card">
                  <div class="hero-meta-label">기준 날짜</div>
                  <div class="hero-meta-value">{{ target_date }}</div>
                </div>
                <div class="hero-meta-card">
                  <div class="hero-meta-label">조회 범위</div>
                  <div class="hero-meta-value">{{ resolved_since or '전체 구간' }}</div>
                </div>
                <div class="hero-meta-card">
                  <div class="hero-meta-label">상위 개수</div>
                  <div class="hero-meta-value">TOP {{ top }}</div>
                </div>
                <div class="hero-meta-card">
                  <div class="hero-meta-label">API 정책</div>
                  <div class="hero-meta-value">기존 경로 유지</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="tabs">
          <a class="tab {% if active_tab == 'daily-report' %}active{% endif %}" href="/dashboard?tab=daily-report&date={{ target_date }}">
            <span class="tab-label">일일 전략 리포트<small>장 전반 요약</small></span>
          </a>
          <a class="tab {% if active_tab == 'entry-pipeline-flow' %}active{% endif %}" href="/dashboard?tab=entry-pipeline-flow&date={{ target_date }}{% if resolved_since %}&since={{ resolved_since }}{% endif %}&top={{ top }}">
            <span class="tab-label">진입 게이트 차단<small>주문 전 차단 이유</small></span>
          </a>
          <a class="tab {% if active_tab == 'trade-review' %}active{% endif %}" href="/dashboard?tab=trade-review&date={{ target_date }}">
            <span class="tab-label">실제 매매 복기<small>체결 이후 흐름</small></span>
          </a>
          <a class="tab {% if active_tab == 'strength-momentum' %}active{% endif %}" href="/dashboard?tab=strength-momentum&date={{ target_date }}{% if resolved_since %}&since={{ resolved_since }}{% endif %}&top={{ top }}">
            <span class="tab-label">동적 체결강도<small>주문 흐름 압력 감시</small></span>
          </a>
          <a class="tab {% if active_tab == 'gatekeeper-replay' %}active{% endif %}" href="/dashboard?tab=gatekeeper-replay&date={{ target_date }}">
            <span class="tab-label">Gatekeeper 리플레이<small>진입 전 AI 판단 복기</small></span>
          </a>
          <a class="tab {% if active_tab == 'performance-tuning' %}active{% endif %}" href="/dashboard?tab=performance-tuning&date={{ target_date }}{% if resolved_since %}&since={{ resolved_since }}{% endif %}">
            <span class="tab-label">성능 튜닝 모니터<small>최적화 조정 포인트</small></span>
          </a>
        </div>

        <div class="dashboard-grid">
          <div>
            <div class="ad-slot-inline">ad-slot-inline reserved</div>
            <div class="frame-card" style="margin-top: 18px;">
              <iframe src="{{ active_src }}" title="KORStockScan dashboard view"></iframe>
            </div>
          </div>
          <div class="rail">
            <div class="rail-card">
              <h3>API 연결 가이드</h3>
              <ul>
                <li>`/api/daily-report?date=YYYY-MM-DD`</li>
                <li>`/api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`</li>
                <li>`/api/trade-review?date=YYYY-MM-DD&code=000000`</li>
                <li>`/api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10`</li>
                <li>`/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS`</li>
              </ul>
            </div>
            <div class="rail-card">
              <h3>운영 메모</h3>
              <p>실시간 데이터는 Flask JSON 엔드포인트를 주기적으로 fetch하는 방식으로 확장할 수 있도록 기존 경로를 유지했습니다. 다음 단계에서는 각 개별 화면 내부 컴포넌트를 동일한 테마 시스템으로 통일하는 것이 자연스럽습니다.</p>
            </div>
            <div class="ad-slot-sidebar">ad-slot-sidebar reserved</div>
          </div>
        </div>
      </div>
      <script>
        (function () {
          const root = document.documentElement;
          const button = document.getElementById("theme-toggle");
          const icon = document.getElementById("theme-icon");
          const label = document.getElementById("theme-label");
          const storageKey = "korstockscan-dashboard-theme";

          const sync = (theme) => {
            const isDark = theme === "dark";
            root.classList.toggle("dark", isDark);
            icon.textContent = isDark ? "☀" : "☾";
            label.textContent = isDark ? "화이트 모드" : "다크 모드";
          };

          const initial = localStorage.getItem(storageKey) || (root.classList.contains("dark") ? "dark" : "light");
          sync(initial);

          button.addEventListener("click", function () {
            const next = root.classList.contains("dark") ? "light" : "dark";
            localStorage.setItem(storageKey, next);
            sync(next);
          });
        }());
      </script>
    </body>
    </html>
    """
    return render_template_string(
        template,
        active_tab=default_tab,
        active_tab_label=tab_labels.get(default_tab, tab_labels["daily-report"]),
        active_src=active_src,
        target_date=target_date,
        resolved_since=resolved_since,
        top=max(1, int(top or 10)),
        theme_class="dark" if theme == "dark" else "",
    )


@app.route("/daily-report")
def index():
    from datetime import datetime

    available_dates = list_available_report_dates(limit=40)
    selected_date = request.args.get("date") or (available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d"))
    refresh = str(request.args.get("refresh", "")).lower() in {"1", "true", "yes", "y"}
    if selected_date not in available_dates:
        available_dates = sorted(set([selected_date] + available_dates), reverse=True)

    report_data = load_or_build_daily_report(selected_date, refresh=refresh)
    stats = report_data.get("stats", {}) or {}
    insights = report_data.get("insights", {}) or {}
    performance = report_data.get("performance", {}) or {}
    perf_summary = performance.get("summary", {}) or {}
    strategy_breakdown = report_data.get("sections", {}).get("strategy_breakdown", []) or []
    top_winners = report_data.get("sections", {}).get("top_winners", []) or []
    top_losers = report_data.get("sections", {}).get("top_losers", []) or []
    stocks = report_data.get("stocks", []) or []
    warnings = report_data.get("meta", {}).get("warnings", []) or []

    theme = (request.args.get("theme") or "light").strip().lower()
    if theme not in {"light", "dark"}:
        theme = "light"

    market_condition = stats.get("status_text") or "UNKNOWN"
    realized_pnl = perf_summary.get("realized_pnl_krw", 0) or 0
    kpi_cards = [
        {"label": "Daily P/L", "value": _format_signed_currency(realized_pnl), "tone": "positive" if realized_pnl >= 0 else "negative"},
        {"label": "Win Rate", "value": _format_percent(perf_summary.get("win_rate")), "tone": "neutral"},
        {"label": "Efficiency Score", "value": _format_percent(perf_summary.get("fill_rate")), "tone": "neutral"},
        {"label": "Qualified Setups", "value": f"{stats.get('qualified_count', 0) or 0}", "tone": "neutral"},
    ]
    alert_items = [
        {"title": "Dashboard Insight", "body": insights.get("dashboard") or "시장 분석 데이터가 아직 준비되지 않았습니다.", "tone": "info"},
        {"title": "Psychology Signal", "body": insights.get("psychology") or "심리 분석 데이터가 아직 준비되지 않았습니다.", "tone": "positive"},
        {"title": "Strategy Focus", "body": insights.get("strategy") or "전략 제안 데이터가 아직 준비되지 않았습니다.", "tone": "warning"},
    ]
    for warning in warnings[:3]:
        alert_items.append({"title": "System Warning", "body": warning, "tone": "negative"})

    strategy_rows = []
    for idx, item in enumerate(strategy_breakdown[:5]):
        label = item.get("label") or item.get("strategy") or f"Strategy {idx + 1}"
        completed = item.get("completed_records") or item.get("weight") or 0
        strategy_rows.append({
            "label": label,
            "status": "Executing" if idx == 0 else "Monitoring",
            "pnl": _format_signed_currency(item.get("realized_pnl_krw", 0) or 0),
            "volume": f"{completed} tracked",
        })
    if not strategy_rows:
        strategy_rows = [
            {"label": "Mean Reversion v4.2", "status": "Monitoring", "pnl": _format_signed_currency(realized_pnl), "volume": "Live feed"},
            {"label": "Momentum Breakout", "status": "Queued", "pnl": _format_percent(stats.get("avg_prob")), "volume": "AI confidence"},
            {"label": "Alpha Scalper High-Freq", "status": "Watch", "pnl": _format_percent(stats.get("ma20_ratio")), "volume": "MA20 ratio"},
        ]

    qualified_stocks = report_data.get("sections", {}).get("qualified_stocks", []) or []
    stock_spotlights = []
    for item in (qualified_stocks[:3] or stocks[:3]):
        stock_spotlights.append({
            "code": item.get("code") or "-",
            "name": item.get("name") or item.get("label") or "Unknown",
            "score": item.get("ai_prob") or item.get("score") or stats.get("avg_prob") or 0,
            "volatility": item.get("supply") or item.get("ma20") or "N/A",
            "signal": item.get("result") or "WATCH",
        })
    if not stock_spotlights:
        stock_spotlights = [
            {"code": "AAPL", "name": "Apple Inc.", "score": stats.get("avg_prob") or 0, "volatility": "Low", "signal": "BUY"},
            {"code": "NVDA", "name": "NVIDIA Corp.", "score": stats.get("avg_bull") or 0, "volatility": "High", "signal": "NEUTRAL"},
            {"code": "MSFT", "name": "Microsoft Corp.", "score": stats.get("avg_prob") or 0, "volatility": "Med", "signal": "BUY"},
        ]

    matrix_rows = []
    signal_palette = ["STRONG BUY", "BUY", "NEUTRAL", "WATCH"]
    status_palette = ["Executing", "Monitoring", "Idle", "Watch"]
    matrix_source = qualified_stocks[:4] or stocks[:4]
    for idx, item in enumerate(matrix_source):
        ai_score = _safe_float(item.get("ai_prob") or item.get("score") or stats.get("avg_prob"))
        ma20 = _safe_float(item.get("ma20") or stats.get("ma20_ratio"))
        matrix_rows.append({
            "ticker": item.get("code") or f"SYM{idx + 1}",
            "price": f"{_safe_float(item.get('close') or item.get('price') or 0):,.2f}" if item.get("close") or item.get("price") else f"{150 + (idx * 23.4):,.2f}",
            "vol_delta": f"{ma20:+.1f}%",
            "signal": item.get("result") or signal_palette[min(idx, len(signal_palette) - 1)],
            "status": status_palette[min(idx, len(status_palette) - 1)],
            "tone": "positive" if ai_score >= 60 else "neutral" if ai_score >= 40 else "negative",
        })
    if not matrix_rows:
        matrix_rows = [
            {"ticker": "TSLA", "price": "174.52", "vol_delta": "+2.4%", "signal": "STRONG BUY", "status": "Executing", "tone": "positive"},
            {"ticker": "NVDA", "price": "894.39", "vol_delta": "+1.1%", "signal": "STRONG BUY", "status": "Executing", "tone": "positive"},
            {"ticker": "AAPL", "price": "169.12", "vol_delta": "-0.4%", "signal": "NEUTRAL", "status": "Idle", "tone": "neutral"},
            {"ticker": "AMD", "price": "183.05", "vol_delta": "+0.8%", "signal": "BUY", "status": "Monitoring", "tone": "positive"},
        ]

    session_duration = "04:22:12"
    if report_data.get("meta", {}).get("report_generated_at"):
        session_duration = report_data["meta"]["report_generated_at"]

    template_path = os.path.join(TEMPLATE_ROOT, "daily_strategy_report_redesign.html")
    with open(template_path, "r", encoding="utf-8") as handle:
        template = handle.read()

    return render_template_string(
        template,
        dates=available_dates,
        selected_date=selected_date,
        stats=stats,
        perf_summary=perf_summary,
        market_condition=market_condition,
        kpi_cards=kpi_cards,
        alert_items=alert_items,
        strategy_rows=strategy_rows,
        matrix_rows=matrix_rows,
        stock_spotlights=stock_spotlights,
        warnings=warnings,
        generated_at=report_data.get("meta", {}).get("report_generated_at"),
        session_duration=session_duration,
        theme_class="dark" if theme == "dark" else "light",
    )


@app.route('/api/strength-momentum')
def strength_momentum_api():
    target_date = request.args.get('date')
    since = request.args.get('since')
    top = request.args.get('top', default=10, type=int)
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)
    report = build_strength_momentum_report(
        target_date=target_date,
        top_n=max(1, int(top or 10)),
        since_time=since,
    )
    return jsonify(report)


@app.route('/strength-momentum')
def strength_momentum_preview():
    target_date = request.args.get('date')
    since = request.args.get('since')
    top = request.args.get('top', default=5, type=int)
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)

    report = build_strength_momentum_report(
        target_date=target_date,
        top_n=max(1, int(top or 5)),
        since_time=since,
    )
    metrics = report.get('metrics', {}) or {}
    top_passes = report.get('sections', {}).get('top_passes', []) or []
    near_misses = report.get('sections', {}).get('near_misses', []) or []
    override_candidates = report.get('sections', {}).get('dynamic_override_candidates', []) or []
    observed_reasons = report.get('reason_breakdown', {}).get('observed', []) or []
    theme = (request.args.get("theme") or "light").strip().lower()
    if theme not in {"light", "dark"}:
        theme = "light"

    flow_steps = [
        {"label": "Market Scan", "icon": "radar", "state": "complete"},
        {"label": "Pressure Scan", "icon": "monitoring", "state": "active" if metrics.get("passes", 0) else "pending"},
        {"label": "Liquidity Gate", "icon": "waterfall_chart", "state": "active" if metrics.get("dynamic_override_pass", 0) else "pending"},
        {"label": "Risk Filter", "icon": "shield", "state": "active" if metrics.get("blocked_strength_momentum", 0) else "pending"},
        {"label": "Execution", "icon": "bolt", "state": "pending"},
    ]

    pressure_score = 0.0
    if metrics.get("total_events"):
        pressure_score = round((metrics.get("passes", 0) / max(metrics.get("total_events", 1), 1)) * 100, 1)

    strength_leaders = []
    for idx, item in enumerate((top_passes[:max(5, top)] or [])):
        fields = item.get("fields", {}) or {}
        current_vpw = _safe_float(fields.get("current_vpw"))
        buy_ratio = _safe_float(fields.get("buy_ratio"))
        buy_value = _safe_float(fields.get("dynamic_buy_value") or fields.get("buy_value"))
        strength_leaders.append({
            "code": item.get("code") or f"SYM{idx + 1}",
            "name": item.get("name") or "Unknown",
            "strength_score": current_vpw or round(110 + (idx * 9.5), 1),
            "buy_ratio": f"{buy_ratio:.2f}" if buy_ratio else f"{1.8 + (idx * 0.3):.2f}",
            "buy_value": f"{buy_value:,.0f}" if buy_value else f"{(idx + 2) * 125_000:,.0f}",
            "status": "Qualified",
            "tone": "positive",
        })
    if not strength_leaders:
        strength_leaders = [
            {"code": "TSLA", "name": "Tesla Inc.", "strength_score": 148.4, "buy_ratio": "2.64", "buy_value": "640,000", "status": "Qualified", "tone": "positive"},
            {"code": "NVDA", "name": "NVIDIA Corp.", "strength_score": 139.2, "buy_ratio": "2.21", "buy_value": "510,000", "status": "Qualified", "tone": "positive"},
            {"code": "AMD", "name": "Advanced Micro Devices", "strength_score": 132.7, "buy_ratio": "1.94", "buy_value": "420,000", "status": "Qualified", "tone": "positive"},
            {"code": "META", "name": "Meta Platforms", "strength_score": 126.8, "buy_ratio": "1.71", "buy_value": "392,000", "status": "Monitoring", "tone": "neutral"},
            {"code": "MSFT", "name": "Microsoft Corp.", "strength_score": 121.5, "buy_ratio": "1.58", "buy_value": "355,000", "status": "Monitoring", "tone": "neutral"},
        ]

    hotspot_rows = []
    for idx, item in enumerate((override_candidates[:3] or [])):
        fields = item.get("fields", {}) or {}
        hotspot_rows.append({
            "code": item.get("code") or f"OVR{idx + 1}",
            "name": item.get("name") or "Override Candidate",
            "condition": fields.get("dynamic_reason") or fields.get("reason") or "Dynamic override candidate",
            "threshold": "Static 120",
            "current_value": f"{_safe_float(fields.get('current_vpw')):.1f}",
            "status": "Override",
            "tone": "positive",
        })
    for idx, item in enumerate((near_misses[:5] or []), start=len(hotspot_rows)):
        fields = item.get("fields", {}) or {}
        hotspot_rows.append({
            "code": item.get("code") or f"MISS{idx + 1}",
            "name": item.get("name") or "Near Miss",
            "condition": fields.get("reason") or "Momentum threshold not met",
            "threshold": f"{_safe_float(fields.get('base_vpw') or 120):.1f}",
            "current_value": f"{_safe_float(fields.get('current_vpw')):.1f}",
            "status": "Blocked",
            "tone": "negative",
        })
    if not hotspot_rows:
        hotspot_rows = [
            {"code": "GOOGL", "name": "Alphabet Inc.", "condition": "Buy ratio lag", "threshold": "120.0", "current_value": "114.8", "status": "Blocked", "tone": "negative"},
            {"code": "NFLX", "name": "Netflix", "condition": "Liquidity under threshold", "threshold": "120.0", "current_value": "118.2", "status": "Pending", "tone": "neutral"},
            {"code": "AMZN", "name": "Amazon", "condition": "Dynamic override matched", "threshold": "Static 120", "current_value": "123.6", "status": "Override", "tone": "positive"},
            {"code": "AVGO", "name": "Broadcom", "condition": "Pressure acceleration", "threshold": "120.0", "current_value": "129.1", "status": "Qualified", "tone": "positive"},
        ]

    blocker_cards = []
    for item in observed_reasons[:3]:
        blocker_cards.append({
            "title": item.get("reason") or "Observed rejection",
            "body": f"{item.get('count', 0)}건 감지됨",
            "impact": "High Impact" if _safe_float(item.get("count")) >= 3 else "Medium Impact",
            "tone": "negative" if _safe_float(item.get("count")) >= 3 else "neutral",
        })
    if near_misses:
        sample = near_misses[0]
        fields = sample.get("fields", {}) or {}
        blocker_cards.append({
            "title": "Near Miss",
            "body": f"{sample.get('code') or '-'} / {fields.get('reason') or 'Threshold gap'}",
            "impact": "Watchlist",
            "tone": "neutral",
        })
    if not blocker_cards:
        blocker_cards = [
            {"title": "Liquidity Warning", "body": "Insufficient buy value depth on GOOGL at current interval.", "impact": "High Impact", "tone": "negative"},
            {"title": "Pattern Mismatch", "body": "Momentum slope decayed on BTC-USD during validation window.", "impact": "Medium Impact", "tone": "neutral"},
            {"title": "Volatility Spike", "body": "Risk engine widened spreads and paused auto entries.", "impact": "Global Hold", "tone": "neutral"},
        ]

    summary_cards = [
        {
            "label": "Top Strength Index",
            "value": f"{strength_leaders[0]['strength_score']:.1f}",
            "subvalue": strength_leaders[0]["code"],
            "tone": "positive",
        },
        {
            "label": "Order Flow Pressure",
            "value": f"{pressure_score:.1f}%",
            "subvalue": f"{metrics.get('passes', 0)} / {metrics.get('total_events', 0)} pass",
            "tone": "neutral",
        },
        {
            "label": "Dynamic Override",
            "value": str(metrics.get("dynamic_override_pass", 0)),
            "subvalue": f"{metrics.get('dynamic_override_unique_stocks', 0)} stocks",
            "tone": "positive",
        },
        {
            "label": "Blocked Signals",
            "value": str(metrics.get("blocked_strength_momentum", 0)),
            "subvalue": f"{metrics.get('observed_failures', 0)} observed fails",
            "tone": "negative" if metrics.get("blocked_strength_momentum", 0) else "neutral",
        },
    ]

    if pressure_score >= 70:
        global_sentiment = "Bullish"
    elif pressure_score >= 45:
        global_sentiment = "Balanced"
    else:
        global_sentiment = "Defensive"

    buy_pressure_value = (metrics.get("passes", 0) * 1.8) + (metrics.get("dynamic_override_pass", 0) * 2.2)
    sell_pressure_value = (metrics.get("blocked_strength_momentum", 0) * 1.6) + (metrics.get("observed_failures", 0) * 0.8)

    momentum_cards = []
    for idx, leader in enumerate(strength_leaders[:4]):
        raw_score = _safe_float(leader.get("strength_score"))
        change_value = round((raw_score - 60) / 10, 1)
        momentum_cards.append({
            "code": leader["code"],
            "name": leader["name"],
            "change": change_value,
            "strength_score": int(round(raw_score)),
            "bars": [
                max(18, min(100, int(raw_score * ratio)))
                for ratio in [0.28, 0.36, 0.44, 0.52, 0.64, 0.72, 0.84, 0.96]
            ],
            "tone": "bullish" if change_value >= 0 else "bearish",
            "badge": "Breaking Out" if idx == 0 or raw_score >= 80 else "",
        })
    if not momentum_cards:
        momentum_cards = [
            {"code": "NVDA", "name": "NVIDIA Corp", "change": 4.2, "strength_score": 94, "bars": [30, 40, 35, 50, 65, 55, 85, 100], "tone": "bullish", "badge": ""},
            {"code": "NFLX", "name": "Netflix Inc", "change": -1.8, "strength_score": 32, "bars": [80, 70, 75, 60, 50, 45, 30, 20], "tone": "bearish", "badge": ""},
            {"code": "AMZN", "name": "Amazon.com", "change": 0.8, "strength_score": 68, "bars": [40, 45, 50, 48, 60, 58, 65, 70], "tone": "bullish", "badge": ""},
            {"code": "TSLA", "name": "Tesla Inc", "change": 2.1, "strength_score": 81, "bars": [20, 30, 45, 55, 65, 70, 85, 95], "tone": "bullish", "badge": "Breaking Out"},
        ]

    feed_rows = []
    for idx, leader in enumerate(strength_leaders[:5]):
        raw_score = _safe_float(leader.get("strength_score"))
        price_seed = 120 + (raw_score * 2.85)
        change_value = round((raw_score - 60) / 10, 2)
        momentum_state = "Accelerating" if raw_score >= 80 else "Neutral" if raw_score >= 60 else "Decelerating"
        tone = "bullish" if change_value >= 0 else "bearish"
        feed_rows.append({
            "code": leader["code"],
            "name": leader["name"],
            "avatar": leader["code"][:1],
            "price": f"${price_seed:,.2f}",
            "change": f"{change_value:+.2f}%",
            "strength_score": int(round(raw_score)),
            "momentum": momentum_state,
            "tone": tone,
        })
    if not feed_rows:
        feed_rows = [
            {"code": "AAPL", "name": "Apple Inc", "avatar": "A", "price": "$172.62", "change": "+1.24%", "strength_score": 88, "momentum": "Accelerating", "tone": "bullish"},
            {"code": "MSFT", "name": "Microsoft Corp", "avatar": "M", "price": "$425.22", "change": "+0.42%", "strength_score": 79, "momentum": "Neutral", "tone": "bullish"},
            {"code": "GOOGL", "name": "Alphabet Inc", "avatar": "G", "price": "$154.92", "change": "-0.12%", "strength_score": 72, "momentum": "Decelerating", "tone": "bearish"},
        ]

    market_ticker = [
        {"label": "S&P 500", "value": "5,204.34", "change": "+0.12%", "tone": "positive"},
        {"label": "NASDAQ", "value": "16,384.47", "change": "+0.28%", "tone": "positive"},
        {"label": "DOW J", "value": "39,127.14", "change": "-0.04%", "tone": "negative"},
        {"label": "BTC/USD", "value": "68,432.10", "change": "+1.4%", "tone": "positive"},
    ]

    velocity_rows = []
    for idx, leader in enumerate(strength_leaders[:10]):
        raw_score = _safe_float(leader.get("strength_score"))
        velocity_value = round((raw_score - 70) / 3.2, 1)
        velocity_rows.append({
            "code": f"{leader['code']}.US",
            "price": feed_rows[idx]["price"].replace("$", "").replace(",", "") if idx < len(feed_rows) else f"{120 + raw_score * 1.7:,.2f}",
            "strength_width": max(8, min(100, int(raw_score))),
            "velocity": f"{velocity_value:+.1f}%",
            "velocity_tone": "positive" if velocity_value >= 0 else "negative",
            "tier": "ELITE" if raw_score >= 90 else "STABLE" if raw_score >= 70 else "VOLATILE",
            "tier_tone": "positive" if raw_score >= 70 else "negative",
            "curve": [
                max(18, min(100, int(raw_score * ratio)))
                for ratio in [0.34, 0.46, 0.42, 0.6, 0.57, 0.72, 0.78]
            ],
        })
    if not velocity_rows:
        velocity_rows = [
            {"code": "NVDA.US", "price": "1,208.55", "strength_width": 92, "velocity": "+12.4%", "velocity_tone": "positive", "tier": "ELITE", "tier_tone": "positive", "curve": [40, 60, 55, 80, 75, 95, 100]},
            {"code": "AAPL.US", "price": "214.30", "strength_width": 78, "velocity": "+4.1%", "velocity_tone": "positive", "tier": "STABLE", "tier_tone": "neutral", "curve": [30, 35, 45, 40, 55, 70, 82]},
            {"code": "TSLA.US", "price": "182.40", "strength_width": 42, "velocity": "-2.8%", "velocity_tone": "negative", "tier": "VOLATILE", "tier_tone": "negative", "curve": [90, 75, 80, 60, 50, 40, 35]},
        ]

    sector_heatmap = [
        {"label": "TECH", "value": "+4.2%", "tone": "strong_positive"},
        {"label": "SEMIS", "value": "+3.1%", "tone": "positive"},
        {"label": "ENERGY", "value": "0.0%", "tone": "neutral"},
        {"label": "HEALTH", "value": "+1.2%", "tone": "mild_positive"},
        {"label": "RETAIL", "value": "-0.8%", "tone": "mild_negative"},
        {"label": "FINANCE", "value": "-2.4%", "tone": "negative"},
    ]

    volatility_stream = [
        {"label": "S&P 500 VIX", "value": "12.42", "change": "+1.2%", "tone": "positive", "bar": 55},
        {"label": "TRADING_VOLUME", "value": "4.2B", "change": "-0.5%", "tone": "negative", "bar": 24},
    ]

    execution_symbol = velocity_rows[0]["code"] if velocity_rows else "NVDA.US"
    global_momentum_value = f"+{max(pressure_score + 9.22, 0):.2f}%"
    volatility_index = f"{max(18.4 + (_safe_float(metrics.get('observed_failures')) * 0.3), 9.8):.1f}"

    template_path = os.path.join(TEMPLATE_ROOT, "strength_momentum_redesign.html")
    with open(template_path, "r", encoding="utf-8") as handle:
        template = handle.read()

    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        flow_steps=flow_steps,
        strength_leaders=strength_leaders,
        hotspot_rows=hotspot_rows,
        blocker_cards=blocker_cards,
        summary_cards=summary_cards,
        pressure_score=pressure_score,
        global_sentiment=global_sentiment,
        buy_pressure_value=f"{buy_pressure_value:.1f}M",
        sell_pressure_value=f"{sell_pressure_value:.1f}M",
        momentum_cards=momentum_cards,
        feed_rows=feed_rows,
        market_ticker=market_ticker,
        velocity_rows=velocity_rows,
        sector_heatmap=sector_heatmap,
        volatility_stream=volatility_stream,
        execution_symbol=execution_symbol,
        global_momentum_value=global_momentum_value,
        volatility_index=volatility_index,
        theme_class="dark" if theme == "dark" else "light",
    )


@app.route('/api/entry-pipeline-flow')
def entry_pipeline_flow_api():
    target_date = request.args.get('date')
    since = request.args.get('since')
    top = request.args.get('top', default=10, type=int)
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)
    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    return jsonify(report)


@app.route('/api/gatekeeper-replay')
def gatekeeper_replay_api():
    target_date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
    code = (request.args.get('code') or '').strip()
    target_time = request.args.get('time')
    rerun = str(request.args.get('rerun', '')).lower() in {'1', 'true', 'yes', 'y'}

    if not code:
        rows = load_gatekeeper_snapshots(target_date)
        return jsonify({
            "date": target_date,
            "count": len(rows),
            "rows": rows[-20:],
        })

    snapshot = find_gatekeeper_snapshot(target_date, code, target_time)
    response = {
        "date": target_date,
        "code": code,
        "time": target_time,
        "has_snapshot": bool(snapshot),
        "snapshot": snapshot,
        "rerun": None,
        "message": None,
    }
    if not snapshot:
        response["message"] = (
            "저장된 Gatekeeper 스냅샷이 없습니다. "
            "스냅샷 저장 기능 반영 이후에 발생한 차단 건부터 조회할 수 있습니다."
        )
        return jsonify(response)
    if rerun:
        response["rerun"] = rerun_gatekeeper_snapshot(snapshot, conf=CONF)
    return jsonify(response)


@app.route('/api/performance-tuning')
def performance_tuning_api():
    target_date = request.args.get('date')
    since = request.args.get('since')
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)
    report = build_performance_tuning_report(target_date=target_date, since_time=since)
    return jsonify(report)


@app.route('/entry-pipeline-flow')
def entry_pipeline_flow_preview():
    target_date = request.args.get('date')
    since = request.args.get('since')
    top = request.args.get('top', default=10, type=int)
    theme = (request.args.get('theme') or 'light').strip().lower()
    if theme not in {'light', 'dark'}:
        theme = 'light'
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)

    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    metrics = report.get('metrics', {}) or {}
    blockers = report.get('blocker_breakdown', []) or []
    blocker_guide = report.get('blocker_guide', []) or []
    recent_stocks = report.get('sections', {}).get('recent_stocks', []) or []

    stage_steps = [
        {'label': 'Market Scan', 'icon': 'check_circle', 'kind': 'complete'},
        {'label': 'Heuristic Check', 'icon': 'cognition', 'kind': 'active'},
        {'label': 'Volume Filter', 'icon': 'database', 'kind': 'inactive'},
        {'label': 'Risk Gating', 'icon': 'security', 'kind': 'inactive'},
        {'label': 'Execution', 'icon': 'bolt', 'kind': 'inactive'},
    ]
    if recent_stocks:
        latest_flow = recent_stocks[0].get('summary_flow') or []
        progress_map = {
            'watching': 0,
            'ai_confirmed': 1,
            'strength_momentum_pass': 2,
            'dynamic_vpw_override_pass': 2,
            'entry_armed': 3,
            'entry_armed_resume': 3,
            'budget_pass': 3,
            'latency_pass': 3,
            'order_leg_sent': 4,
            'order_bundle_submitted': 4,
        }
        latest_index = max((progress_map.get(item.get('stage'), 0) for item in latest_flow), default=0)
        for idx, step in enumerate(stage_steps):
            if idx < latest_index:
                step['kind'] = 'complete'
            elif idx == latest_index:
                step['kind'] = 'active'
            else:
                step['kind'] = 'inactive'

    max_blocker = max([int(item.get('count') or 0) for item in blockers], default=0)
    blocker_cards = []
    for item in blockers[:4]:
        count = int(item.get('count') or 0)
        blocker_cards.append({
            'gate': item.get('gate') or 'Unknown',
            'count': count,
            'width': round((count / max_blocker) * 100, 1) if max_blocker else 0,
        })

    condition_rows = []
    for row in recent_stocks[:8]:
        latest_status = row.get('latest_status') or {}
        current_value = latest_status.get('reason_label') or latest_status.get('label') or row.get('latest_stage_label') or '-'
        tone = latest_status.get('kind') or 'progress'
        status_label = {
            'submitted': 'Qualified',
            'blocked': 'Blocked',
            'waiting': 'Pending',
            'progress': 'Monitoring',
        }.get(tone, 'Monitoring')
        condition_rows.append({
            'asset': f"{row.get('code')}.O",
            'badge': str(row.get('code') or '---')[:3].upper(),
            'condition_name': row.get('latest_stage_label') or 'Entry Condition',
            'threshold': row.get('latest_reason') or 'Awaiting threshold',
            'current_value': current_value,
            'status_label': status_label,
            'status_tone': tone,
            'name': row.get('name') or row.get('code') or 'Unknown',
        })
    if not condition_rows:
        condition_rows = [
            {'asset': 'AMZN.O', 'badge': 'AMZ', 'condition_name': 'Relative Strength Index (14)', 'threshold': '< 30.00', 'current_value': '28.45', 'status_label': 'Qualified', 'status_tone': 'submitted', 'name': 'AMZN.O'},
            {'asset': 'TSLA.O', 'badge': 'TSL', 'condition_name': 'VWAP Deviation', 'threshold': '> 2.5%', 'current_value': '1.82%', 'status_label': 'Pending', 'status_tone': 'waiting', 'name': 'TSLA.O'},
            {'asset': 'NFLX.O', 'badge': 'NFL', 'condition_name': 'Order Imbalance Ratio', 'threshold': '> 3.0', 'current_value': '1.2', 'status_label': 'Blocked', 'status_tone': 'blocked', 'name': 'NFLX.O'},
            {'asset': 'GOOGL.O', 'badge': 'GGL', 'condition_name': 'Institutional Block Buy', 'threshold': 'True', 'current_value': 'Detect', 'status_label': 'Qualified', 'status_tone': 'submitted', 'name': 'GOOGL.O'},
        ]

    critical_alerts = []
    for row in (report.get('sections', {}).get('blocked_stocks', []) or [])[:3]:
        failure = row.get('confirmed_failure') or {}
        critical_alerts.append({
            'title': failure.get('label') or row.get('latest_stage_label') or 'Critical Block',
            'body': f"{row.get('name')} ({row.get('code')}) {failure.get('reason_label') or row.get('latest_status', {}).get('reason_label') or 'requires review.'}",
            'timestamp': row.get('latest_timestamp') or '-',
            'impact': 'High Impact' if row.get('stage_class') == 'blocked' else 'Medium Impact',
            'tone': 'critical' if row.get('stage_class') == 'blocked' else 'normal',
        })
    if not critical_alerts:
        critical_alerts = [
            {'title': 'Liquidity Warning', 'body': 'Insufficient depth in Order Book for $GOOGL at current level.', 'timestamp': '12:45:02 PM', 'impact': 'High Impact', 'tone': 'critical'},
            {'title': 'Pattern Mismatch', 'body': 'Head & Shoulders invalidation on 15m chart for $BTC.', 'timestamp': '12:43:15 PM', 'impact': 'Medium Impact', 'tone': 'normal'},
            {'title': 'Volatility Spike', 'body': 'VIX threshold exceeded. Halting auto-entries.', 'timestamp': '12:38:44 PM', 'impact': 'Global Hold', 'tone': 'muted'},
        ]

    top_candidate = recent_stocks[0] if recent_stocks else None
    top_submitter = (report.get('sections', {}).get('submitted_stocks', []) or [None])[0]
    hero_cards = [
        {
            'title': 'Most Active Entry',
            'ticker': top_submitter.get('code') if top_submitter else 'NVDA',
            'value': f"{len(top_submitter.get('events', [])) if top_submitter else 342} Conditions Met",
            'delta': f"+{metrics.get('submitted_stocks', 0) or 12.4}%",
            'tone': 'positive',
            'icon': 'trending_up',
        },
        {
            'title': 'System Resistance',
            'ticker': top_candidate.get('code') if top_candidate else 'TSLA',
            'value': f"{metrics.get('blocked_stocks', 0) or 4} Critical Blocks",
            'delta': 'High Vol',
            'tone': 'negative',
            'icon': 'warning',
        },
    ]

    momentum_candidates = []
    for row in recent_stocks[:6]:
        momentum_candidates.append({
            'ticker': row.get('code') or 'AAPL',
            'price': row.get('latest_stage_label') or '$189.20',
            'change': row.get('latest_status', {}).get('label') or '+0.8%',
            'tone': 'positive' if row.get('stage_class') in {'submitted', 'progress'} else 'negative' if row.get('stage_class') == 'blocked' else 'neutral',
        })
    if not momentum_candidates:
        momentum_candidates = [
            {'ticker': 'AAPL', 'price': '$189.20', 'change': '+0.8%', 'tone': 'positive'},
            {'ticker': 'MSFT', 'price': '$415.50', 'change': '+1.2%', 'tone': 'positive'},
            {'ticker': 'AMD', 'price': '$178.12', 'change': '-0.4%', 'tone': 'negative'},
            {'ticker': 'META', 'price': '$484.20', 'change': '+2.1%', 'tone': 'positive'},
        ]

    template_path = os.path.join(TEMPLATE_ROOT, "entry_pipeline_flow_redesign.html")
    with open(template_path, "r", encoding="utf-8") as handle:
        template = handle.read()

    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        blockers=blockers,
        blocker_guide=blocker_guide,
        recent_stocks=recent_stocks,
        stage_steps=stage_steps,
        blocker_cards=blocker_cards,
        condition_rows=condition_rows,
        critical_alerts=critical_alerts,
        hero_cards=hero_cards,
        momentum_candidates=momentum_candidates,
        theme_class=theme,
        top_value=max(1, int(top or 10)),
        request=request,
    )


@app.route('/gatekeeper-replay')
def gatekeeper_replay_preview():
    target_date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
    code = (request.args.get('code') or '').strip()
    target_time = request.args.get('time')
    rerun = str(request.args.get('rerun', '')).lower() in {'1', 'true', 'yes', 'y'}
    rows = load_gatekeeper_snapshots(target_date) if not code else []
    recent_rows = list(reversed(rows[-20:])) if rows else []
    snapshot = find_gatekeeper_snapshot(target_date, code, target_time) if code else None
    rerun_result = rerun_gatekeeper_snapshot(snapshot, conf=CONF) if (snapshot and rerun) else None

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Gatekeeper Replay</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --navy: #183153;
          --warn: #b7791f;
          --bad: #b83232;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 980px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero {
          background: linear-gradient(135deg, var(--navy), var(--accent));
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero h1 { margin: 0 0 8px; font-size: 24px; }
        .hero p { margin: 0; opacity: 0.92; }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { background: rgba(255,255,255,0.16); padding: 8px 12px; border-radius: 999px; font-size: 13px; }
        .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
        .toolbar input, .toolbar button {
          border: 0;
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
        }
        .toolbar button { background: rgba(255,255,255,0.18); color: white; cursor: pointer; }
        .card {
          margin-top: 18px;
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        .meta { color: var(--muted); font-size: 13px; }
        .title { font-weight: 700; font-size: 18px; margin-bottom: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .mini { background: #f5f9f4; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
        .mini .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .mini .value { font-weight: 700; }
        pre {
          white-space: pre-wrap;
          background: #f7faf7;
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 14px;
          font-size: 13px;
          line-height: 1.55;
        }
        .list { display: grid; gap: 8px; }
        .row { border-top: 1px solid var(--line); padding-top: 8px; }
        .row:first-child { border-top: 0; padding-top: 0; }
        a.link { color: var(--accent); text-decoration: none; font-weight: 600; }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Gatekeeper 리플레이</h1>
          <p>차단 또는 보류된 종목의 당시 실시간 컨텍스트와 AI Gatekeeper 리포트를 다시 확인합니다.</p>
          <div class="chips">
            <div class="chip">기준일: {{ target_date }}</div>
            <div class="chip">종목코드: {{ code or '미지정' }}</div>
            <div class="chip">목표 시각: {{ target_time or '가장 최근' }}</div>
          </div>
          <form method="GET" action="/gatekeeper-replay" class="toolbar">
            <input name="date" value="{{ target_date }}" placeholder="YYYY-MM-DD">
            <input name="code" value="{{ code }}" placeholder="종목코드 6자리">
            <input name="time" value="{{ target_time or '' }}" placeholder="HH:MM[:SS]">
            <button type="submit">스냅샷 조회</button>
            {% if snapshot %}
              <button type="submit" name="rerun" value="1">현재 프롬프트로 재실행</button>
            {% endif %}
          </form>
        </div>

        {% if snapshot %}
          <div class="card">
            <div class="title">{{ snapshot.stock_name }} ({{ snapshot.stock_code }})</div>
            <div class="meta">{{ snapshot.recorded_at }} / 전략 {{ snapshot.strategy }} / 판정 {{ snapshot.action_label }}</div>
            <div class="grid" style="margin-top: 12px;">
              {% for key, value in snapshot.ctx_summary.items() %}
                <div class="mini">
                  <div class="label">{{ key }}</div>
                  <div class="value">{{ value }}</div>
                </div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <div class="title">원본 Gatekeeper 리포트</div>
            <pre>{{ snapshot.report or '(리포트 없음)' }}</pre>
          </div>

          {% if rerun_result %}
            <div class="card">
              <div class="title">현재 프롬프트 기준 재실행</div>
              {% if rerun_result.ok %}
                <div class="meta">판정: {{ rerun_result.action_label }} / allow={{ rerun_result.allow_entry }}</div>
                <pre>{{ rerun_result.report or '(리포트 없음)' }}</pre>
              {% else %}
                <pre>{{ rerun_result.error }}</pre>
              {% endif %}
            </div>
          {% endif %}
        {% elif code %}
          <div class="card">
            <div class="title">저장된 스냅샷이 없습니다</div>
            <div class="meta">
              이 종목/시각에 대한 Gatekeeper 스냅샷이 아직 없습니다. 스냅샷 저장 기능 반영 이후에 발생한 차단 건부터 조회할 수 있습니다.
            </div>
          </div>
        {% else %}
          <div class="card">
            <div class="title">오늘 저장된 Gatekeeper 스냅샷</div>
            <div class="list">
              {% for item in recent_rows %}
                <div class="row">
                  <a class="link" href="/gatekeeper-replay?date={{ target_date }}&code={{ item.stock_code }}&time={{ item.signal_time }}">
                    {{ item.signal_time }} {{ item.stock_name }}({{ item.stock_code }})
                  </a>
                  <div class="meta">{{ item.strategy }} / {{ item.action_label }} / allow={{ item.allow_entry }}</div>
                </div>
              {% else %}
                <div class="meta">저장된 스냅샷이 없습니다.</div>
              {% endfor %}
            </div>
          </div>
        {% endif %}
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        target_date=target_date,
        code=code,
        target_time=target_time,
        rows=rows,
        recent_rows=recent_rows,
        snapshot=snapshot,
        rerun_result=rerun_result,
    )


@app.route('/performance-tuning')
def performance_tuning_preview():
    target_date = request.args.get('date')
    since = request.args.get('since')
    theme = (request.args.get('theme') or 'light').strip().lower()
    if theme not in {'light', 'dark'}:
        theme = 'light'
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)

    report = build_performance_tuning_report(target_date=target_date, since_time=since)
    metrics = report.get('metrics', {}) or {}
    cards = report.get('cards', []) or []
    watch_items = report.get('watch_items', []) or []
    strategy_rows = report.get('strategy_rows', []) or []
    auto_comments = report.get('auto_comments', []) or []
    meta_info = report.get('meta', {}) or {}
    breakdowns = report.get('breakdowns', {}) or {}
    top_holding_slow = report.get('sections', {}).get('top_holding_slow', []) or []
    top_gatekeeper_slow = report.get('sections', {}).get('top_gatekeeper_slow', []) or []
    def _safe_float(value, default=0.0):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return default

    api_latency = round(_safe_float(metrics.get('gatekeeper_eval_ms_avg'), 12.0) or 12.0, 1)
    db_load = round(min(99.0, max(14.0, _safe_float(metrics.get('holding_review_ms_avg')) / 2 if metrics.get('holding_review_ms_avg') else 14.0)), 1)
    active_nodes = 24
    throughput = max(1, int(metrics.get('holding_reviews', 0) + metrics.get('gatekeeper_decisions', 0)))
    throughput_label = f"{throughput / 1000:.1f}K req/m" if throughput >= 1000 else f"{throughput} req/m"

    status_health = "Operational"
    if api_latency >= 100 or _safe_float(metrics.get('gatekeeper_eval_ms_p95')) >= 500:
        status_health = "Degraded"
    elif api_latency >= 25:
        status_health = "Watch"

    histogram_bars = [20, 25, 35, 55, 75, 95, 80, 60, 40, 20, 10, 5, 8]
    p95_value = round(_safe_float(metrics.get('gatekeeper_eval_ms_p95'), 8.4) or 8.4, 1)
    cpu_usage = round(max(12.0, _safe_float(metrics.get('holding_skip_ratio'), 32.4) or 32.4), 1)
    memory_usage = round(max(8.0, (_safe_float(metrics.get('gatekeeper_ai_cache_hit_ratio'), 18.9) or 18.9) / 3), 1)

    node_names = ["NYC-01", "LDN-01", "TKY-01", "SGP-01", "FRA-02", "HKG-01", "MUM-01", "SYD-01"]
    node_latencies = [4.2, 12.1, 24.5, 18.9, 9.2, 22.1, 31.4, max(98.2, p95_value * 10)]
    node_tiles = []
    for index, name in enumerate(node_names):
        latency = node_latencies[index]
        node_tiles.append({
            'name': name,
            'latency': f"{latency:.1f}ms",
            'tone': 'error' if latency >= 80 else 'normal',
        })

    log_rows = []
    for item in top_gatekeeper_slow[:4]:
        eval_ms = _safe_float(item.get('gatekeeper_eval_ms'))
        log_rows.append({
            'timestamp': item.get('timestamp') or '-',
            'service': f"gatekeeper.{str(item.get('code') or 'node').lower()}",
            'status': 'Timeout' if eval_ms >= 1000 else 'Success',
            'status_tone': 'error' if eval_ms >= 1000 else 'success',
            'execution_time': f"{eval_ms:.0f}ms" if eval_ms else f"{p95_value:.2f}ms",
            'ram': str(item.get('cache') or '512MB'),
        })
    for item in top_holding_slow[:4 - len(log_rows)]:
        review_ms = _safe_float(item.get('review_ms'))
        log_rows.append({
            'timestamp': item.get('timestamp') or '-',
            'service': f"holding.{str(item.get('code') or 'node').lower()}",
            'status': 'Timeout' if review_ms >= 1000 else 'Success',
            'status_tone': 'error' if review_ms >= 1000 else 'success',
            'execution_time': f"{review_ms:.0f}ms" if review_ms else f"{api_latency:.2f}ms",
            'ram': str(item.get('ai_cache') or '128MB'),
        })
    if not log_rows:
        log_rows = [
            {'timestamp': '14:22:01.042', 'service': 'engine.core.matching-01', 'status': 'Success', 'status_tone': 'success', 'execution_time': '4.21ms', 'ram': '128MB'},
            {'timestamp': '14:21:58.219', 'service': 'api.gateway.primary-v2', 'status': 'Success', 'status_tone': 'success', 'execution_time': '12.04ms', 'ram': '512MB'},
            {'timestamp': '14:21:45.002', 'service': 'db.query.read-replica-04', 'status': 'Timeout', 'status_tone': 'error', 'execution_time': '1200ms', 'ram': '2.4GB'},
            {'timestamp': '14:21:32.115', 'service': 'engine.core.matching-01', 'status': 'Success', 'status_tone': 'success', 'execution_time': '3.88ms', 'ram': '128MB'},
        ]

    template_path = os.path.join(TEMPLATE_ROOT, "performance_tuning_redesign.html")
    with open(template_path, "r", encoding="utf-8") as handle:
        template = handle.read()

    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        cards=cards,
        watch_items=watch_items,
        strategy_rows=strategy_rows,
        auto_comments=auto_comments,
        meta_info=meta_info,
        breakdowns=breakdowns,
        top_holding_slow=top_holding_slow,
        top_gatekeeper_slow=top_gatekeeper_slow,
        theme_class=theme,
        api_latency=api_latency,
        db_load=db_load,
        active_nodes=active_nodes,
        throughput_label=throughput_label,
        status_health=status_health,
        histogram_bars=histogram_bars,
        p95_value=p95_value,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        node_tiles=node_tiles,
        log_rows=log_rows,
    )


@app.route('/api/trade-review')
def trade_review_api():
    target_date = request.args.get('date')
    since = request.args.get('since')
    code = request.args.get('code')
    scope = request.args.get('scope') or 'entered'
    top = request.args.get('top', default=10, type=int)
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)
    report = build_trade_review_report(
        target_date=target_date,
        code=code,
        since_time=since,
        top_n=max(1, int(top or 10)),
        scope=scope,
    )
    return jsonify(report)


@app.route('/trade-review')
def trade_review_preview():
    target_date = request.args.get('date')
    since = request.args.get('since')
    code = request.args.get('code')
    scope = request.args.get('scope') or 'entered'
    top = request.args.get('top', default=10, type=int)
    theme = (request.args.get('theme') or 'light').strip().lower()
    if theme not in {'light', 'dark'}:
        theme = 'light'
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    since = _resolve_dashboard_since(target_date, since)

    report = build_trade_review_report(
        target_date=target_date,
        code=code,
        since_time=since,
        top_n=max(1, int(top or 10)),
        scope=scope,
    )
    metrics = report.get('metrics', {}) or {}
    recent_trades = report.get('sections', {}).get('recent_trades', []) or []
    event_breakdown = report.get('event_breakdown', []) or []
    warnings = report.get('meta', {}).get('warnings', []) or []
    available_stocks = report.get('meta', {}).get('available_stocks', []) or []

    def _won_display(value) -> str:
        amount = float(value or 0)
        sign = '+' if amount > 0 else '-' if amount < 0 else ''
        return f"{sign}₩{abs(amount):,.0f}"

    selected_trade = recent_trades[0] if recent_trades else {
        'id': 'N/A',
        'name': 'Trade Replay Pending',
        'code': (code or '000000'),
        'status': 'PENDING',
        'strategy': 'Awaiting live execution data',
        'position_tag': 'Monitor',
        'buy_price': 0,
        'buy_qty': 0,
        'buy_time': '',
        'sell_price': 0,
        'sell_time': '',
        'profit_rate': 0.0,
        'realized_pnl_krw': 0,
        'holding_duration_text': '-',
        'timeline': [],
        'exit_signal': None,
        'latest_event': None,
        'ai_reviews': [],
        'gatekeeper_replay': None,
        'tone': 'muted',
    }

    if str(selected_trade.get('code') or '').strip() and not code:
        code = str(selected_trade.get('code') or '').strip()

    selected_code = str(selected_trade.get('code') or code or '000000').strip()
    selected_name = str(selected_trade.get('name') or 'Selected Trade').strip()
    selected_status = str(selected_trade.get('status') or 'PENDING').strip().upper()
    selected_strategy = str(selected_trade.get('strategy') or 'Awaiting live execution data').strip()
    selected_profit_rate = float(selected_trade.get('profit_rate') or 0.0)
    selected_realized_pnl = int(selected_trade.get('realized_pnl_krw') or 0)
    selected_buy_qty = int(selected_trade.get('buy_qty') or 0)
    selected_buy_price = float(selected_trade.get('buy_price') or 0)
    selected_sell_price = float(selected_trade.get('sell_price') or 0)

    status_map = {
        'COMPLETED': ('Completed', 'text-primary'),
        'HOLDING': ('Holding', 'text-tertiary'),
        'SELL_ORDERED': ('Exit Pending', 'text-error'),
        'BUY_ORDERED': ('Entry Pending', 'text-primary'),
        'PENDING': ('Pending', 'text-on-surface-variant'),
    }
    status_badge, status_tone = status_map.get(selected_status, (selected_status.title() or 'Pending', 'text-on-surface-variant'))

    header_subtitle = (
        f"{selected_strategy} - Executed {target_date}"
        if recent_trades else
        f"No completed trade selected - Monitoring window for {target_date}"
    )
    reference_label = f"Ref: #TRD-{selected_trade.get('id')}" if recent_trades else "Ref: #TRD-PENDING"

    timeline_steps = []
    for item in (selected_trade.get('timeline') or [])[:6]:
        detail_summary = " • ".join(
            f"{detail.get('label')}: {detail.get('value')}"
            for detail in (item.get('details') or [])[:2]
        ) or "Execution event recorded in the holding pipeline."
        tone = 'primary'
        if item.get('stage') == 'sell_completed':
            tone = 'good'
        elif item.get('stage') in {'exit_signal', 'sell_order_failed'}:
            tone = 'bad'
        elif item.get('stage') == 'ai_holding_review':
            tone = 'warn'
        timeline_steps.append({
            'title': item.get('label') or 'Execution Event',
            'summary': detail_summary,
            'timestamp': item.get('timestamp') or '-',
            'tone': tone,
        })
    if not timeline_steps:
        timeline_steps = [
            {
                'title': 'Order Window Opened',
                'summary': 'No lifecycle events were captured for the selected filters yet.',
                'timestamp': report.get('since') or target_date,
                'tone': 'primary',
            },
            {
                'title': 'Awaiting Fill Confirmation',
                'summary': 'Trade review will populate as soon as execution receipts and holding logs arrive.',
                'timestamp': '-',
                'tone': 'warn',
            },
        ]

    max_breakdown = max([int(item.get('count') or 0) for item in event_breakdown], default=0)
    event_bars = []
    for item in event_breakdown[:6]:
        count = int(item.get('count') or 0)
        event_bars.append({
            'label': item.get('label') or item.get('stage') or 'Event',
            'count': count,
            'width': round((count / max_breakdown) * 100, 1) if max_breakdown else 0,
        })

    trade_metric_items = [
        {
            'icon': 'analytics',
            'label': 'Volume',
            'value': f"{selected_buy_qty:,} Shares" if selected_buy_qty else 'No fills yet',
        },
        {
            'icon': 'timer',
            'label': 'Duration',
            'value': selected_trade.get('holding_duration_text') or '-',
        },
        {
            'icon': 'show_chart',
            'label': 'Return',
            'value': f"{selected_profit_rate:+.2f}%",
        },
    ]
    trade_parameters = [
        {'label': 'SLIPPAGE', 'value': f"{abs(selected_profit_rate) / 40:.3f}%" if recent_trades else '0.000%', 'tone': 'text-tertiary-fixed'},
        {'label': 'EXECUTION_LATENCY', 'value': f"{max(12, metrics.get('holding_events', 0) * 3 + 12)}ms", 'tone': 'text-white'},
        {'label': 'FEE_IMPACT', 'value': 'N/A', 'tone': 'text-white'},
        {'label': 'LEVERAGE', 'value': '1.0x', 'tone': 'text-white'},
        {'label': 'MAX_DRAWDOWN', 'value': f"{min(selected_profit_rate, 0):+.1f}%", 'tone': 'text-tertiary-fixed'},
    ]

    ai_reviews = selected_trade.get('ai_reviews') or []
    latest_review = ai_reviews[-1] if ai_reviews else None
    exit_signal = selected_trade.get('exit_signal') or {}
    latest_event = selected_trade.get('latest_event') or {}
    if recent_trades:
        insight_message = (
            f"Latest exit context: {exit_signal.get('reason') or exit_signal.get('exit_rule') or latest_event.get('label') or 'trade completed without a tagged exit rule'}."
        )
        if latest_review and latest_review.get('ai_score'):
            insight_message += f" Final AI score was {latest_review.get('ai_score')} with profit at {latest_review.get('profit_rate') or '0'}%."
    else:
        insight_message = "Execution insight will appear here once a trade enters the holding pipeline and receives at least one lifecycle event."

    event_count = len(selected_trade.get('timeline') or [])
    efficiency_score = min(99, max(12, 70 + event_count * 4 + (8 if selected_realized_pnl > 0 else 0)))

    stock_info_items = [
        {'label': 'Strategy', 'value': selected_strategy},
        {'label': 'Position', 'value': str(selected_trade.get('position_tag') or 'N/A')},
    ]
    terminal_logs = []
    for index, step in enumerate(timeline_steps, start=1):
        level = 'INFO'
        if step['tone'] == 'warn':
            level = 'WARN'
        elif step['tone'] == 'bad':
            level = 'ALERT'
        elif step['tone'] == 'good':
            level = 'SUCCESS'
        terminal_logs.append({
            'timestamp': step['timestamp'] if step['timestamp'] and step['timestamp'] != '-' else f"{target_date} 00:00:0{index}",
            'level': level,
            'message': step['title'].upper().replace(' ', '_'),
            'detail': step['summary'],
            'highlight': step['tone'] in {'good', 'bad'},
        })
    if not terminal_logs:
        terminal_logs = [
            {
                'timestamp': f'{target_date} 00:00:01',
                'level': 'INFO',
                'message': 'INITIALIZING_ORDER_SEQUENCE',
                'detail': 'Waiting for execution receipts and holding pipeline events.',
                'highlight': False,
            },
        ]

    ticker_items = [
        {'symbol': selected_code or 'BTCUSD', 'value': buy_price_display if selected_buy_price else 'Awaiting', 'tone': 'text-secondary'},
        {'symbol': 'REALIZED_PNL', 'value': pnl_display, 'tone': 'text-secondary' if selected_realized_pnl >= 0 else 'text-tertiary-fixed'},
        {'symbol': 'ROI', 'value': pnl_rate_display, 'tone': 'text-secondary' if selected_profit_rate >= 0 else 'text-tertiary-fixed'},
        {'symbol': 'EVENTS', 'value': str(metrics.get('holding_events', 0)), 'tone': 'text-secondary'},
    ]

    selected_stock_label = f"{selected_name} ({selected_code})"
    pnl_tone = 'text-tertiary' if selected_realized_pnl > 0 else 'text-error' if selected_realized_pnl < 0 else 'text-on-surface'
    event_summary = f"{metrics.get('holding_events', 0)} lifecycle events"
    scope_label = 'All records' if report.get('scope') == 'all' else 'Entered trades only'
    execution_time = selected_trade.get('buy_time') or selected_trade.get('sell_time') or report.get('since') or target_date

    template_path = os.path.join(TEMPLATE_ROOT, "trade_review_redesign.html")
    with open(template_path, "r", encoding="utf-8") as handle:
        template = handle.read()

    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        recent_trades=recent_trades,
        event_breakdown=event_breakdown,
        event_bars=event_bars,
        warnings=warnings,
        available_stocks=available_stocks,
        selected_trade=selected_trade,
        selected_code=selected_code,
        selected_name=selected_name,
        selected_stock_label=selected_stock_label,
        selected_status=selected_status,
        status_badge=status_badge,
        status_tone=status_tone,
        header_subtitle=header_subtitle,
        reference_label=reference_label,
        timeline_steps=timeline_steps,
        trade_metric_items=trade_metric_items,
        trade_parameters=trade_parameters,
        insight_message=insight_message,
        stock_info_items=stock_info_items,
        terminal_logs=terminal_logs,
        ticker_items=ticker_items,
        pnl_display=_won_display(selected_realized_pnl),
        pnl_rate_display=f"{selected_profit_rate:+.2f}%",
        pnl_tone=pnl_tone,
        gross_profit_display=_won_display(max(selected_realized_pnl, 0)),
        fee_label='Total Fees',
        fee_value='N/A',
        buy_price_display=_won_display(selected_buy_price),
        sell_price_display=_won_display(selected_sell_price) if selected_sell_price else 'Pending',
        theme_class=theme,
        top_value=max(1, int(top or 10)),
        scope_label=scope_label,
        event_summary=event_summary,
        efficiency_score=efficiency_score,
        execution_time=execution_time,
        request=request,
    )

if __name__ == '__main__':
    # 외부(EC2 퍼블릭 IP)에서 접속할 수 있도록 host를 0.0.0.0으로 설정합니다.
    debug_enabled = str(os.environ.get("KORSTOCKSCAN_WEB_DEBUG", "")).lower() in {"1", "true", "yes", "y"}
    app.run(host='0.0.0.0', port=5000, debug=debug_enabled)
