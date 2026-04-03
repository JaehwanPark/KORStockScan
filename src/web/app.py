from flask import Flask, jsonify, render_template_string, request
import os
import sys
from datetime import datetime, timedelta

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

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
    tab_labels = {
        "daily-report": "일일 전략 리포트",
        "entry-pipeline-flow": "진입 게이트 차단",
        "trade-review": "실제 매매 복기",
        "gatekeeper-replay": "Gatekeeper 리플레이",
        "performance-tuning": "성능 튜닝 모니터",
    }

    tab_map = {
        "daily-report": f"/daily-report?date={target_date}",
        "entry-pipeline-flow": f"/entry-pipeline-flow?date={target_date}&top={max(1, int(top or 10))}" + (f"&since={resolved_since}" if resolved_since else ""),
        "trade-review": f"/trade-review?date={target_date}",
        "gatekeeper-replay": f"/gatekeeper-replay?date={target_date}",
        "performance-tuning": f"/performance-tuning?date={target_date}" + (f"&since={resolved_since}" if resolved_since else ""),
    }
    active_src = tab_map.get(default_tab, tab_map["daily-report"])

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>KORStockScan Dashboard</title>
      <style>
        :root {
          --bg: #eef4ee;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --navy: #183153;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 1240px; margin: 0 auto; padding: 20px 16px 28px; }
        .hero {
          background: linear-gradient(135deg, var(--navy), var(--accent));
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero-top {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .hero-copy { max-width: 720px; }
        .hero h1 { margin: 0 0 8px; font-size: 26px; }
        .hero p { margin: 0; opacity: 0.92; }
        .hero-meta {
          min-width: 260px;
          background: rgba(255,255,255,0.12);
          border: 1px solid rgba(255,255,255,0.16);
          border-radius: 18px;
          padding: 14px;
          backdrop-filter: blur(8px);
        }
        .hero-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }
        .hero-meta-card {
          background: rgba(255,255,255,0.08);
          border-radius: 14px;
          padding: 10px 12px;
        }
        .hero-meta-label {
          font-size: 11px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          opacity: 0.72;
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
          background: rgba(255,255,255,0.16);
          border: 1px solid rgba(255,255,255,0.18);
          font-size: 13px;
          font-weight: 600;
        }
        .hero-status-dot {
          width: 9px;
          height: 9px;
          border-radius: 999px;
          background: #9ef3c3;
          box-shadow: 0 0 0 4px rgba(158,243,195,0.16);
        }
        .tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
        .tab {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 11px 16px;
          border-radius: 14px;
          border: 1px solid var(--line);
          background: white;
          color: var(--ink);
          text-decoration: none;
          font-weight: 600;
        }
        .tab.active {
          background: #e7f6ee;
          border-color: #b8dfc8;
          color: #176942;
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
        .frame-card {
          margin-top: 16px;
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 10px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        iframe {
          width: 100%;
          min-height: 1650px;
          border: 0;
          border-radius: 12px;
          background: white;
        }
        @media (max-width: 900px) {
          .hero-meta { width: 100%; }
          .hero-meta-grid { grid-template-columns: 1fr 1fr; }
          iframe { min-height: 1900px; }
        }
        @media (max-width: 640px) {
          .hero-meta-grid { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div class="hero-top">
            <div class="hero-copy">
              <h1>KORStockScan 통합 대시보드</h1>
              <p>일일 전략 리포트, 진입 게이트 차단, 실제 매매 복기를 한 화면에서 전환합니다.</p>
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
          <a class="tab {% if active_tab == 'gatekeeper-replay' %}active{% endif %}" href="/dashboard?tab=gatekeeper-replay&date={{ target_date }}">
            <span class="tab-label">Gatekeeper 리플레이<small>진입 전 AI 판단 복기</small></span>
          </a>
          <a class="tab {% if active_tab == 'performance-tuning' %}active{% endif %}" href="/dashboard?tab=performance-tuning&date={{ target_date }}{% if resolved_since %}&since={{ resolved_since }}{% endif %}">
            <span class="tab-label">성능 튜닝 모니터<small>최적화 조정 포인트</small></span>
          </a>
        </div>

        <div class="frame-card">
          <iframe src="{{ active_src }}" title="KORStockScan dashboard view"></iframe>
        </div>
      </div>
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

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>KORStockScan Daily Report</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --warn: #b7791f;
          --bad: #b83232;
          --navy: #183153;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 1160px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero {
          background: linear-gradient(135deg, var(--navy), var(--accent));
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero-top {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .hero h1 { margin: 0 0 8px; font-size: 26px; }
        .hero p { margin: 0; opacity: 0.92; }
        .toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .toolbar select, .toolbar button {
          border: 0;
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
        }
        .toolbar select { min-width: 180px; }
        .toolbar button {
          background: rgba(255,255,255,0.18);
          color: white;
          cursor: pointer;
        }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { background: rgba(255,255,255,0.16); padding: 8px 12px; border-radius: 999px; font-size: 13px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 18px; }
        .card {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .value { font-size: 24px; font-weight: 700; }
        .value.good { color: var(--accent); }
        .value.warn { color: var(--warn); }
        .value.bad { color: var(--bad); }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .two-col { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
        .list { display: grid; gap: 10px; }
        .row { border-top: 1px solid var(--line); padding-top: 10px; }
        .row:first-child { border-top: 0; padding-top: 0; }
        .title { font-weight: 700; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .bars { display: grid; gap: 10px; }
        .bar-row { display: grid; grid-template-columns: 130px 1fr 64px; gap: 10px; align-items: center; }
        .bar { background: #e7efe5; border-radius: 999px; overflow: hidden; height: 12px; }
        .fill { background: linear-gradient(90deg, #1d7a52, #4ea974); height: 100%; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px 8px; border-top: 1px solid var(--line); text-align: left; font-size: 14px; }
        th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.02em; }
        tbody tr:first-child td { border-top: 0; }
        .badge {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 12px;
          border: 1px solid var(--line);
          background: #f2f6f3;
        }
        .badge.good { color: #176942; background: #e7f6ee; border-color: #b8dfc8; }
        .badge.warn { color: #9a5b10; background: #fff3df; border-color: #f1d29d; }
        .badge.bad { color: #a12b2b; background: #fdeaea; border-color: #efb8b8; }
        .warning-box {
          margin-top: 16px;
          background: #fff5e8;
          color: #8a5418;
          border: 1px solid #f2d4a9;
          border-radius: 16px;
          padding: 14px 16px;
        }
        @media (max-width: 900px) {
          .two-col { grid-template-columns: 1fr; }
          .hero-top { flex-direction: column; }
          .toolbar select { min-width: 0; width: 100%; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div class="hero-top">
            <div>
              <h1>일일 전략 리포트</h1>
              <p>시장 진단과 직전 매매일 성적을 한 화면에서 확인합니다.</p>
            </div>
            <form method="GET" action="/" class="toolbar">
              <select name="date" onchange="this.form.submit()">
                {% for d in dates %}
                  <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>{{ d }}</option>
                {% endfor %}
              </select>
              <button type="submit" name="refresh" value="1">새로 생성</button>
            </form>
          </div>
          <div class="chips">
            <div class="chip">기준일: {{ data.date }}</div>
            <div class="chip">시세 기준일: {{ stats.quote_date or data.date }}</div>
            <div class="chip">직전 매매일: {{ performance.date or '없음' }}</div>
            <div class="chip">진단 종목 {{ stats.total_valid }}개</div>
            <div class="chip">합격 후보 {{ stats.qualified_count }}개</div>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="label">시장 상태</div><div class="value {{ stats.tone }}">{{ stats.status_text }}</div></div>
          <div class="card"><div class="label">20일선 위 비율</div><div class="value">{{ stats.ma20_ratio }}%</div></div>
          <div class="card"><div class="label">평균 RSI</div><div class="value">{{ stats.avg_rsi }}</div></div>
          <div class="card"><div class="label">평균 AI 확신도</div><div class="value">{{ stats.avg_prob }}%</div></div>
          <div class="card"><div class="label">전일 실현손익</div><div class="value {% if perf_summary.realized_pnl_krw > 0 %}good{% elif perf_summary.realized_pnl_krw < 0 %}bad{% endif %}">{{ "{:,}".format(perf_summary.realized_pnl_krw) }}원</div></div>
          <div class="card"><div class="label">전일 승률</div><div class="value">{{ perf_summary.win_rate }}%</div></div>
          <div class="card"><div class="label">종료 거래</div><div class="value">{{ perf_summary.completed_records }}</div></div>
          <div class="card"><div class="label">미청산 보유</div><div class="value warn">{{ perf_summary.open_records }}</div></div>
        </div>

        {% if warnings %}
          <div class="warning-box">
            <strong>리포트 생성 경고</strong>
            <div class="list" style="margin-top: 8px;">
              {% for item in warnings %}
                <div>{{ item }}</div>
              {% endfor %}
            </div>
          </div>
        {% endif %}

        <div class="section two-col">
          <div class="card">
            <h2>시장 해석</h2>
            <div class="list">
              <div class="row">
                <div class="title">데이터 대시보드</div>
                <div class="meta">{{ insights.dashboard }}</div>
              </div>
              <div class="row">
                <div class="title">모델 심리</div>
                <div class="meta">{{ insights.psychology }}</div>
              </div>
              <div class="row">
                <div class="title">운영 전략</div>
                <div class="meta">{{ insights.strategy }}</div>
              </div>
              <div class="row">
                <div class="title">직전 매매일 피드백</div>
                <div class="meta">{{ insights.execution_feedback }}</div>
              </div>
            </div>
          </div>

          <div class="card">
            <h2>직전 매매일 성적 요약</h2>
            <div class="grid" style="margin-top: 0;">
              <div><div class="label">총 레코드</div><div class="value">{{ perf_summary.total_records }}</div></div>
              <div><div class="label">체결 진입</div><div class="value">{{ perf_summary.filled_records }}</div></div>
              <div><div class="label">진입 체결률</div><div class="value">{{ perf_summary.fill_rate }}%</div></div>
              <div><div class="label">평균 손익률</div><div class="value">{{ perf_summary.avg_profit_rate }}%</div></div>
            </div>
            <div class="meta" style="margin-top: 12px;">{{ performance.insight }}</div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>전략별 성과</h2>
            <div class="bars">
              {% for item in strategy_breakdown %}
                <div class="bar-row">
                  <div>{{ item.strategy }}</div>
                  <div class="bar"><div class="fill" style="width: {{ (item.completed_records / strategy_breakdown[0].completed_records * 100) if strategy_breakdown and strategy_breakdown[0].completed_records else 0 }}%"></div></div>
                  <div>{{ item.completed_records }}건</div>
                </div>
              {% else %}
                <div class="meta">전략별 집계 데이터가 없습니다.</div>
              {% endfor %}
            </div>
            <div class="list" style="margin-top: 12px;">
              {% for item in strategy_breakdown[:5] %}
                <div class="row">
                  <div class="title">{{ item.strategy }}</div>
                  <div class="meta">승률 {{ item.win_rate }}% / 평균 {{ item.avg_profit_rate }}% / 실현손익 {{ "{:,}".format(item.realized_pnl_krw) }}원</div>
                </div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>상하위 성적</h2>
            <div class="list">
              {% for item in top_winners[:3] %}
                <div class="row">
                  <div class="title">{{ item.name }} ({{ item.code }}) <span class="badge good">{{ item.profit_rate }}%</span></div>
                  <div class="meta">{{ item.strategy }} / 실현손익 {{ "{:,}".format(item.realized_pnl_krw) }}원</div>
                </div>
              {% endfor %}
              {% for item in top_losers[:3] %}
                <div class="row">
                  <div class="title">{{ item.name }} ({{ item.code }}) <span class="badge bad">{{ item.profit_rate }}%</span></div>
                  <div class="meta">{{ item.strategy }} / 실현손익 {{ "{:,}".format(item.realized_pnl_krw) }}원</div>
                </div>
              {% endfor %}
              {% if not top_winners and not top_losers %}
                <div class="meta">아직 종료 거래 데이터가 없습니다.</div>
              {% endif %}
            </div>
          </div>
        </div>

        <div class="section card">
          <h2>우량주 진단 후보</h2>
          <table>
            <thead>
              <tr>
                <th>종목</th>
                <th>현재가</th>
                <th>20일선</th>
                <th>AI 확신도</th>
                <th>수급</th>
                <th>결론</th>
              </tr>
            </thead>
            <tbody>
              {% for stock in stocks %}
                <tr>
                  <td><strong>{{ stock.name }}</strong> ({{ stock.code }})</td>
                  <td>{{ stock.price_text }}</td>
                  <td>{{ stock.ma20_icon }} {{ stock.ma20_state }}</td>
                  <td>{{ stock.ai_prob_text }}</td>
                  <td>외인 {{ stock.supply.foreign }} / 기관 {{ stock.supply.institution }}</td>
                  <td><span class="badge {{ stock.result_tone }}">{{ stock.result }}</span></td>
                </tr>
              {% else %}
                <tr><td colspan="6" class="meta">후보 데이터가 없습니다.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        data=report_data,
        dates=available_dates,
        selected_date=selected_date,
        stats=stats,
        insights=insights,
        performance=performance,
        perf_summary=perf_summary,
        strategy_breakdown=strategy_breakdown,
        top_winners=top_winners,
        top_losers=top_losers,
        stocks=stocks,
        warnings=warnings,
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

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Strength Momentum Dashboard</title>
      <style>
        :root {
          --bg: #f3efe6;
          --card: #fffdf8;
          --ink: #1e2a2f;
          --muted: #607075;
          --line: #dfd5c4;
          --accent: #0f766e;
          --warn: #b45309;
          --bad: #b91c1c;
        }
        body {
          margin: 0;
          background: radial-gradient(circle at top, #fff8eb 0%, var(--bg) 55%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 980px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero {
          background: linear-gradient(135deg, #133c55, #0f766e);
          color: white;
          padding: 20px;
          border-radius: 20px;
          box-shadow: 0 20px 40px rgba(19, 60, 85, 0.18);
        }
        .hero h1 { margin: 0 0 8px; font-size: 24px; }
        .hero p { margin: 0; opacity: 0.9; }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { background: rgba(255,255,255,0.16); padding: 8px 12px; border-radius: 999px; font-size: 13px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 18px; }
        .card {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 10px 25px rgba(80, 60, 20, 0.06);
        }
        .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .value { font-size: 24px; font-weight: 700; }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .list { display: grid; gap: 10px; }
        .row { border-top: 1px solid var(--line); padding-top: 10px; }
        .row:first-child { border-top: 0; padding-top: 0; }
        .title { font-weight: 700; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .good { color: var(--accent); }
        .warn { color: var(--warn); }
        .bad { color: var(--bad); }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>동적 체결강도 모니터</h1>
          <p>{{ report.date }} 기준 실시간 집계</p>
          <div class="chips">
            <div class="chip">since: {{ report.since or '전체' }}</div>
            <div class="chip">총 이벤트 {{ metrics.total_events }}건</div>
            <div class="chip">통과 {{ metrics.passes }}건</div>
            <div class="chip">오버라이드 {{ metrics.dynamic_override_pass }}건</div>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="label">관측 실패</div><div class="value bad">{{ metrics.observed_failures }}</div></div>
          <div class="card"><div class="label">동적 통과</div><div class="value good">{{ metrics.passes }}</div></div>
          <div class="card"><div class="label">동적 직접 차단</div><div class="value warn">{{ metrics.blocked_strength_momentum }}</div></div>
          <div class="card"><div class="label">정적 120 오버라이드</div><div class="value">{{ metrics.dynamic_override_pass }}</div></div>
        </div>

        <div class="section card">
          <h2>주요 실패 사유</h2>
          <div class="list">
            {% for item in observed_reasons[:5] %}
              <div class="row">
                <div class="title">{{ item.reason }}</div>
                <div class="meta">{{ item.count }}건</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>동적 통과 상위 사례</h2>
          <div class="list">
            {% for item in top_passes %}
              <div class="row">
                <div class="title">{{ item.name }} ({{ item.code }})</div>
                <div class="meta">base {{ item.fields.base_vpw }} / curr {{ item.fields.current_vpw }} / buy_value {{ item.fields.buy_value }} / buy_ratio {{ item.fields.buy_ratio }}</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>정적 120 구간 통과 후보</h2>
          <div class="list">
            {% for item in override_candidates %}
              <div class="row">
                <div class="title">{{ item.name }} ({{ item.code }})</div>
                <div class="meta">vpw {{ item.fields.current_vpw }} / buy_value {{ item.fields.dynamic_buy_value or item.fields.buy_value }} / reason {{ item.fields.dynamic_reason or item.fields.reason }}</div>
              </div>
            {% else %}
              <div class="meta">아직 오버라이드 통과 후보가 없습니다.</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>Near-miss</h2>
          <div class="list">
            {% for item in near_misses %}
              <div class="row">
                <div class="title">{{ item.name }} ({{ item.code }})</div>
                <div class="meta">reason {{ item.fields.reason }} / buy_value {{ item.fields.buy_value }} / buy_ratio {{ item.fields.buy_ratio }}</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        top_passes=top_passes,
        near_misses=near_misses,
        override_candidates=override_candidates,
        observed_reasons=observed_reasons,
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

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Entry Pipeline Flow</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --warn: #b7791f;
          --bad: #b83232;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 1040px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero {
          background: linear-gradient(135deg, #183153, #1d7a52);
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero h1 { margin: 0 0 8px; font-size: 24px; }
        .hero p { margin: 0; opacity: 0.92; }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { background: rgba(255,255,255,0.16); padding: 8px 12px; border-radius: 999px; font-size: 13px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 18px; }
        .card {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .value { font-size: 24px; font-weight: 700; }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .bars { display: grid; gap: 10px; }
        .bar-row { display: grid; grid-template-columns: 140px 1fr 52px; gap: 10px; align-items: center; }
        .bar { background: #e7efe5; border-radius: 999px; overflow: hidden; height: 12px; }
        .fill { background: linear-gradient(90deg, #1d7a52, #4ea974); height: 100%; }
        .stock-list { display: grid; gap: 10px; }
        .row { border-top: 1px solid var(--line); padding-top: 10px; }
        .row:first-child { border-top: 0; padding-top: 0; }
        .title { font-weight: 700; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .guide-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .guide-table th, .guide-table td { padding: 9px 10px; border-top: 1px solid var(--line); text-align: left; vertical-align: top; }
        .guide-table th { color: var(--muted); font-weight: 600; font-size: 12px; }
        .guide-table tr:first-child th, .guide-table tr:first-child td { border-top: 0; }
        .flow { margin-top: 10px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
        .detail-flow { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
        .detail-chip { border-radius: 999px; padding: 4px 9px; font-size: 12px; background: #f3f7f2; border: 1px solid var(--line); color: var(--ink); }
        .tag { border-radius: 999px; padding: 5px 10px; font-size: 12px; background: #edf5ee; border: 1px solid var(--line); }
        .tag.start { background: #f2f6f3; }
        .tag.pass { background: #e7f6ee; border-color: #b8dfc8; color: #176942; }
        .tag.waiting { background: #fff3df; border-color: #f1d29d; color: #9a5b10; }
        .tag.blocked { background: #fdeaea; border-color: #efb8b8; color: #a12b2b; font-weight: 700; }
        .tag.submitted { background: #e2f5ee; border-color: #9fd6bf; color: #0f6d53; font-weight: 700; }
        .arrow { color: var(--muted); font-size: 12px; }
        .blocked { color: var(--bad); }
        .waiting { color: var(--warn); }
        .submitted { color: var(--accent); }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>주문 진입 게이트 플로우</h1>
          <p>종목별 누적 통과 단계와 최신 차단 상태를 분리해 주문 흐름을 추적합니다.</p>
          <div class="chips">
            <div class="chip">기준일: {{ report.date }}</div>
            <div class="chip">조회 시작: {{ report.since or '전체' }}</div>
            <div class="chip">추적 종목 {{ metrics.tracked_stocks }}개</div>
            <div class="chip">차단 {{ metrics.blocked_stocks }}개</div>
            <div class="chip">주문 제출 {{ metrics.submitted_stocks }}개</div>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="label">추적 종목</div><div class="value">{{ metrics.tracked_stocks }}</div></div>
          <div class="card"><div class="label">차단 종목</div><div class="value blocked">{{ metrics.blocked_stocks }}</div></div>
          <div class="card"><div class="label">첫 AI 대기 종목</div><div class="value waiting">{{ metrics.waiting_stocks }}</div></div>
          <div class="card"><div class="label">주문 제출 종목</div><div class="value submitted">{{ metrics.submitted_stocks }}</div></div>
        </div>

        <div class="section card">
          <h2>최신 차단 사유 분포</h2>
          <div class="bars">
            {% for item in blockers %}
              <div class="bar-row">
                <div>{{ item.gate }}</div>
                <div class="bar"><div class="fill" style="width: {{ (item.count / blockers[0].count * 100) if blockers and blockers[0].count else 0 }}%"></div></div>
                <div>{{ item.count }}</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>게이트별 차단 설명</h2>
          <table class="guide-table">
            <tr>
              <th>게이트</th>
              <th>설명</th>
              <th>우선 확인</th>
            </tr>
            {% for item in blocker_guide %}
              <tr>
                <td>{{ item.gate }}</td>
                <td>{{ item.description }}</td>
                <td>{{ item.check }}</td>
              </tr>
            {% else %}
              <tr>
                <td colspan="3" class="meta">데이터 없음</td>
              </tr>
            {% endfor %}
          </table>
        </div>

        <div class="section card">
          <h2>종목별 최신 플로우</h2>
          <div class="stock-list">
            {% for row in recent_stocks %}
              <div class="row">
                <div class="title">{{ row.name }} ({{ row.code }})</div>
                <div class="meta">
                  최신 상태:
                  <span class="{{ row.latest_status.kind }}">{{ row.latest_status.label }}</span>
                  {% if row.latest_status.reason_label %}/ {{ row.latest_status.reason_label }}{% endif %}
                  / {{ row.latest_status.timestamp }}
                </div>
                <div class="meta" style="margin-top: 8px;">확정 통과 단계</div>
                <div class="flow">
                  {% for item in row.pass_flow %}
                    <span class="tag {{ item.kind }}">{{ item.label }}</span>
                    {% if not loop.last %}
                      <span class="arrow">→</span>
                    {% endif %}
                  {% endfor %}
                </div>
                {% if row.precheck_passes %}
                  <div class="meta" style="margin-top: 10px;">예비 통과 이력</div>
                  <div class="flow">
                    {% for item in row.precheck_passes %}
                      <span class="tag {{ item.kind }}">{{ item.label }}</span>
                      {% if not loop.last %}
                        <span class="arrow">→</span>
                      {% endif %}
                    {% endfor %}
                  </div>
                {% endif %}
                {% if row.confirmed_failure %}
                  <div class="meta" style="margin-top: 10px;">마지막 확정 진입 실패</div>
                  <div class="flow">
                    <span class="tag blocked">{{ row.confirmed_failure.label }}</span>
                    {% if row.confirmed_failure.reason_label %}
                      <span class="tag blocked">{{ row.confirmed_failure.reason_label }}</span>
                    {% endif %}
                    <span class="meta">{{ row.confirmed_failure.timestamp }}</span>
                  </div>
                  {% if row.confirmed_failure.details %}
                    <div class="detail-flow">
                      {% for item in row.confirmed_failure.details %}
                        <span class="detail-chip">{{ item.label }}: {{ item.value }}</span>
                      {% endfor %}
                    </div>
                  {% endif %}
                {% endif %}
                {% if row.latest_status.kind in ['blocked', 'waiting'] %}
                  <div class="meta" style="margin-top: 10px;">마지막 차단/대기</div>
                  <div class="flow">
                    <span class="tag {{ row.latest_status.kind }}">{{ row.latest_status.label }}</span>
                  </div>
                {% endif %}
                {% if row.gatekeeper_replay %}
                  <div class="meta" style="margin-top: 10px;">게이트키퍼 리플레이</div>
                  <div class="flow">
                    <a class="tag pass" href="{{ row.gatekeeper_replay.url }}" target="_blank" rel="noopener">
                      리플레이 보기
                    </a>
                    {% if row.gatekeeper_replay.action %}
                      <span class="tag">{{ row.gatekeeper_replay.action }}</span>
                    {% endif %}
                    <span class="meta">{{ row.gatekeeper_replay.timestamp }}</span>
                  </div>
                {% endif %}
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        blockers=blockers,
        blocker_guide=blocker_guide,
        recent_stocks=recent_stocks,
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

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Performance Tuning Monitor</title>
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
        .wrap { max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }
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
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 18px; }
        .card {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .value { font-size: 24px; font-weight: 700; }
        .hint { color: var(--muted); font-size: 12px; margin-top: 6px; }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .list { display: grid; gap: 10px; }
        .row { border-top: 1px solid var(--line); padding-top: 10px; }
        .row:first-child { border-top: 0; padding-top: 0; }
        .title { font-weight: 700; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .tone-good { color: var(--accent); }
        .tone-warn { color: var(--warn); }
        .tone-bad { color: var(--bad); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px 8px; border-top: 1px solid var(--line); text-align: left; font-size: 14px; vertical-align: top; }
        th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.02em; }
        tbody tr:first-child td { border-top: 0; }
        .pill {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 12px;
          border: 1px solid var(--line);
          background: #f2f6f3;
        }
        .pill.tone-good { background: #e7f6ee; border-color: #b8dfc8; }
        .pill.tone-warn { background: #fff3df; border-color: #f1d29d; }
        .pill.tone-bad { background: #fdeaea; border-color: #efb8b8; }
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .three-col { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .comment-row {
          display: grid;
          gap: 8px;
          padding: 12px 0;
          border-top: 1px solid var(--line);
        }
        .comment-row:first-child { border-top: 0; padding-top: 0; }
        .comment-head {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }
        .comment-title { font-weight: 700; }
        .mini-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
          margin-top: 12px;
        }
        .mini-card {
          background: #f5faf6;
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 12px;
        }
        .mini-label { color: var(--muted); font-size: 11px; margin-bottom: 4px; }
        .mini-value { font-size: 18px; font-weight: 700; }
        .subsection-title { font-size: 14px; font-weight: 700; margin: 14px 0 8px; }
        .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        @media (max-width: 900px) {
          .two-col { grid-template-columns: 1fr; }
          .three-col { grid-template-columns: 1fr; }
          .mini-grid { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 640px) {
          .mini-grid { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>성능 튜닝 모니터</h1>
          <p>최적화 효과를 과시하기보다, stale 위험과 재평가 빈도를 함께 보면서 조정 포인트를 찾는 화면입니다.</p>
          <div class="chips">
            <div class="chip">기준일: {{ report.date }}</div>
            <div class="chip">조회 시작: {{ report.since or '전체 구간' }}</div>
            <div class="chip">보유 AI 리뷰 {{ metrics.holding_reviews }}건</div>
            <div class="chip">Gatekeeper 결정 {{ metrics.gatekeeper_decisions }}건</div>
            <div class="chip">성과 기준: {{ meta_info.outcome_basis or '기준일 누적 성과' }}</div>
            <div class="chip">추세 기준: {{ meta_info.trend_basis or '최근 거래일 rolling 성과' }}</div>
          </div>
        </div>

        <div class="grid">
          {% for item in cards %}
            <div class="card">
              <div class="label">{{ item.label }}</div>
              <div class="value">{{ item.value }}</div>
              {% if item.hint %}<div class="hint">{{ item.hint }}</div>{% endif %}
            </div>
          {% endfor %}
        </div>

        {% if auto_comments %}
        <div class="section card">
          <h2>자동 권장 코멘트</h2>
          {% for item in auto_comments %}
            <div class="comment-row">
              <div class="comment-head">
                <span class="pill {{ 'tone-' + item.tone }}">{{ item.strategy }}</span>
                <span class="comment-title">{{ item.title }}</span>
              </div>
              <div class="meta">{{ item.comment }}</div>
            </div>
          {% endfor %}
        </div>
        {% endif %}

        <div class="section two-col">
          {% for item in strategy_rows %}
            <div class="card">
              <h2>{{ item.label }} 성과 연결</h2>
              <div class="meta">{{ meta_info.engine_basis or '조회 구간 엔진 지표' }}와 {{ meta_info.outcome_basis or '기준일 누적 성과' }}를 함께 봅니다.</div>

              <div class="subsection-title">전환 흐름</div>
              <div class="mini-grid">
                <div class="mini-card">
                  <div class="mini-label">감시 종목</div>
                  <div class="mini-value">{{ item.pipeline.candidates }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">AI 확답</div>
                  <div class="mini-value">{{ item.pipeline.ai_confirmed }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">진입 자격 확보</div>
                  <div class="mini-value">{{ item.pipeline.entry_armed }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">주문 제출</div>
                  <div class="mini-value">{{ item.pipeline.submitted }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">AI 확답률</div>
                  <div class="mini-value">{{ item.pipeline.ai_confirm_rate }}%</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">주문 제출률</div>
                  <div class="mini-value">{{ item.pipeline.submitted_rate }}%</div>
                </div>
              </div>

              <div class="subsection-title">결과 품질</div>
              <div class="mini-grid">
                <div class="mini-card">
                  <div class="mini-label">실제 진입</div>
                  <div class="mini-value">{{ item.outcomes.entered_rows }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">종료 거래</div>
                  <div class="mini-value">{{ item.outcomes.completed_rows }}</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">승률</div>
                  <div class="mini-value">{{ item.outcomes.win_rate }}%</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">평균 손익률</div>
                  <div class="mini-value">{{ "%+.2f"|format(item.outcomes.avg_profit_rate) }}%</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">실현손익</div>
                  <div class="mini-value" style="font-size:16px;">{{ "{:,}".format(item.outcomes.realized_pnl_krw) }}원</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">AI 조기청산</div>
                  <div class="mini-value">{{ item.outcomes.early_exit_ratio }}%</div>
                </div>
              </div>

              <div class="subsection-title">성과 추세</div>
              <div class="mini-grid">
                <div class="mini-card">
                  <div class="mini-label">최근 5거래일</div>
                  <div class="mini-value">{{ "%+.2f"|format(item.trends.summary_5d.avg_profit_rate if item.trends.summary_5d else 0.0) }}%</div>
                  <div class="hint">승률 {{ item.trends.summary_5d.win_rate if item.trends.summary_5d else 0.0 }}% / 종료 {{ item.trends.summary_5d.completed_rows if item.trends.summary_5d else 0 }}건</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">최근 20거래일</div>
                  <div class="mini-value">{{ "%+.2f"|format(item.trends.summary_20d.avg_profit_rate if item.trends.summary_20d else 0.0) }}%</div>
                  <div class="hint">승률 {{ item.trends.summary_20d.win_rate if item.trends.summary_20d else 0.0 }}% / 종료 {{ item.trends.summary_20d.completed_rows if item.trends.summary_20d else 0 }}건</div>
                </div>
                <div class="mini-card">
                  <div class="mini-label">추세 시그널</div>
                  <div class="mini-value {% if item.trends.signal and item.trends.signal.tone == 'good' %}good{% elif item.trends.signal and item.trends.signal.tone == 'bad' %}bad{% else %}warn{% endif %}" style="font-size:16px;">
                    {{ item.trends.signal.label if item.trends.signal else '추세 없음' }}
                  </div>
                  <div class="hint">{{ item.trends.signal.comment if item.trends.signal else '최근-장기 추세 비교 데이터가 없습니다.' }}</div>
                </div>
              </div>

              <div class="subsection-title">최신 차단 분포</div>
              <div class="pill-row">
                {% for blocker in item.pipeline.latest_blockers %}
                  <span class="pill">{{ blocker.label }} {{ blocker.count }}건 / {{ blocker.ratio }}%</span>
                {% else %}
                  <span class="meta">최신 차단 데이터가 없습니다.</span>
                {% endfor %}
              </div>

              <div class="subsection-title">청산 규칙 분포</div>
              <div class="pill-row">
                {% for exit_item in item.outcomes.top_exit_rules %}
                  <span class="pill">{{ exit_item.label }} {{ exit_item.count }}건 / {{ exit_item.ratio }}%</span>
                {% else %}
                  <span class="meta">청산 규칙 데이터가 없습니다.</span>
                {% endfor %}
              </div>

              <div class="subsection-title">최근 5거래일 성과 흐름</div>
              <table>
                <thead>
                  <tr>
                    <th>기준일</th>
                    <th>실제 진입</th>
                    <th>종료</th>
                    <th>승률</th>
                    <th>평균 손익률</th>
                  </tr>
                </thead>
                <tbody>
                  {% for point in item.trends.recent_points %}
                    <tr>
                      <td>{{ point.date }}</td>
                      <td>{{ point.entered_rows }}</td>
                      <td>{{ point.completed_rows }}</td>
                      <td>{{ point.win_rate }}%</td>
                      <td>{{ "%+.2f"|format(point.avg_profit_rate) }}%</td>
                    </tr>
                  {% else %}
                    <tr>
                      <td colspan="5" class="meta">최근 거래일 추세 데이터가 없습니다.</td>
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          {% endfor %}
        </div>

        <div class="section card">
          <h2>조정 관찰 포인트</h2>
          <table>
            <thead>
              <tr>
                <th>지표</th>
                <th>현재값</th>
                <th>권장범위</th>
                <th>해석</th>
              </tr>
            </thead>
            <tbody>
              {% for item in watch_items %}
                <tr>
                  <td><strong>{{ item.label }}</strong></td>
                  <td><span class="pill {{ 'tone-' + item.tone }}">{{ item.value }}</span></td>
                  <td>{{ item.target }}</td>
                  <td>{{ item.comment }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>보유 AI 경로 분포</h2>
            <div class="list">
              {% for item in breakdowns.holding_ai_cache_modes %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
            <div class="meta" style="margin-top: 12px;">
              skip 비율 {{ metrics.holding_skip_ratio }}% / AI cache hit {{ metrics.holding_ai_cache_hit_ratio }}% / review p95 {{ metrics.holding_review_ms_p95 }}ms
            </div>
          </div>

          <div class="card">
            <h2>Gatekeeper 경로 분포</h2>
            <div class="list">
              {% for item in breakdowns.gatekeeper_cache_modes %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
            <div class="meta" style="margin-top: 12px;">
              fast reuse {{ metrics.gatekeeper_fast_reuse_ratio }}% / AI cache hit {{ metrics.gatekeeper_ai_cache_hit_ratio }}% / eval p95 {{ metrics.gatekeeper_eval_ms_p95 }}ms
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Gatekeeper 보류 액션 분포</h2>
            <div class="list">
              {% for item in breakdowns.gatekeeper_actions %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 Gatekeeper 보류 액션 데이터가 없습니다.</div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>청산 규칙 분포</h2>
            <div class="list">
              {% for item in breakdowns.exit_rules %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 청산 시그널 데이터가 없습니다.</div>
              {% endfor %}
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>느린 보유 AI 리뷰 상위</h2>
            <div class="list">
              {% for item in top_holding_slow %}
                <div class="row">
                  <div class="title">{{ item.name }} ({{ item.code }})</div>
                  <div class="meta">{{ item.timestamp }} / {{ item.review_ms }}ms / profit {{ item.profit_rate }} / ai_cache {{ item.ai_cache }}</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>느린 Gatekeeper 평가 상위</h2>
            <div class="list">
              {% for item in top_gatekeeper_slow %}
                <div class="row">
                  <div class="title">{{ item.name }} ({{ item.code }})</div>
                  <div class="meta">{{ item.timestamp }} / {{ item.gatekeeper_eval_ms }}ms / cache {{ item.cache }} / {{ item.action or '-' }}</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
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

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Trade Review</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
          --warn: #b7791f;
          --bad: #b83232;
          --navy: #183153;
        }
        body {
          margin: 0;
          background: linear-gradient(180deg, #eef6ef 0%, var(--bg) 100%);
          color: var(--ink);
          font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }
        .wrap { max-width: 1080px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero {
          background: linear-gradient(135deg, var(--navy), var(--accent));
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero-top {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .hero h1 { margin: 0 0 8px; font-size: 24px; }
        .hero p { margin: 0; opacity: 0.92; }
        .toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .toolbar input, .toolbar select, .toolbar button {
          border: 0;
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
        }
        .toolbar button {
          background: rgba(255,255,255,0.18);
          color: white;
          cursor: pointer;
        }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .chip { background: rgba(255,255,255,0.16); padding: 8px 12px; border-radius: 999px; font-size: 13px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 18px; }
        .card {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 16px;
          box-shadow: 0 12px 26px rgba(27, 42, 34, 0.05);
        }
        .label { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
        .value { font-size: 24px; font-weight: 700; }
        .good { color: var(--accent); }
        .warn { color: var(--warn); }
        .bad { color: var(--bad); }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .row { border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }
        .row:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
        .title { font-weight: 700; font-size: 16px; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .bars { display: grid; gap: 10px; }
        .bar-row { display: grid; grid-template-columns: 150px 1fr 52px; gap: 10px; align-items: center; }
        .bar { background: #e7efe5; border-radius: 999px; overflow: hidden; height: 12px; }
        .fill { background: linear-gradient(90deg, #1d7a52, #4ea974); height: 100%; }
        .flow { margin-top: 10px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
        .tag { border-radius: 999px; padding: 5px 10px; font-size: 12px; background: #edf5ee; border: 1px solid var(--line); }
        .tag.good { background: #e7f6ee; border-color: #b8dfc8; color: #176942; }
        .tag.warn { background: #fff3df; border-color: #f1d29d; color: #9a5b10; }
        .tag.bad { background: #fdeaea; border-color: #efb8b8; color: #a12b2b; }
        .arrow { color: var(--muted); font-size: 12px; }
        .detail-flow { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
        .detail-chip { border-radius: 999px; padding: 4px 9px; font-size: 12px; background: #f3f7f2; border: 1px solid var(--line); color: var(--ink); }
        .warning-box {
          margin-top: 16px;
          background: #fff5e8;
          color: #8a5418;
          border: 1px solid #f2d4a9;
          border-radius: 16px;
          padding: 14px 16px;
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <div class="hero-top">
            <div>
              <h1>실제 매매 복기</h1>
              <p>보유감시에서 청산 체결까지 한 종목의 실제 매매 흐름을 복기합니다.</p>
            </div>
            <form method="GET" action="/trade-review" class="toolbar">
              <input type="date" name="date" value="{{ report.date }}">
              <input type="text" name="code" placeholder="종목코드 6자리" value="{{ report.code or '' }}">
              <input type="text" name="since" placeholder="HH:MM:SS" value="{{ request.args.get('since', '') }}">
              <select name="scope">
                <option value="entered" {% if report.scope != 'all' %}selected{% endif %}>실제 진입/주문만</option>
                <option value="all" {% if report.scope == 'all' %}selected{% endif %}>전체 레코드</option>
              </select>
              <button type="submit">조회</button>
            </form>
          </div>
          <div class="chips">
            <div class="chip">기준일: {{ report.date }}</div>
            <div class="chip">조회 시작: {{ report.since or '전체' }}</div>
            <div class="chip">종목: {{ report.code or '전체' }}</div>
            <div class="chip">표시 기준: {{ '전체 레코드' if report.scope == 'all' else '실제 진입/주문 이력' }}</div>
            <div class="chip">복기 로그 {{ metrics.holding_events }}건</div>
          </div>
        </div>

        {% if warnings %}
          <div class="warning-box">
            <strong>리포트 경고</strong>
            {% for item in warnings %}
              <div class="meta" style="color: inherit;">{{ item }}</div>
            {% endfor %}
          </div>
        {% endif %}

        <div class="grid">
          <div class="card"><div class="label">총 거래</div><div class="value">{{ metrics.total_trades }}</div></div>
          <div class="card"><div class="label">종료 거래</div><div class="value">{{ metrics.completed_trades }}</div></div>
          <div class="card"><div class="label">미종료 거래</div><div class="value warn">{{ metrics.open_trades }}</div></div>
          <div class="card"><div class="label">실현손익</div><div class="value {% if metrics.realized_pnl_krw > 0 %}good{% elif metrics.realized_pnl_krw < 0 %}bad{% endif %}">{{ "{:,}".format(metrics.realized_pnl_krw) }}원</div></div>
          <div class="card"><div class="label">평균 손익률</div><div class="value">{{ metrics.avg_profit_rate }}%</div></div>
          <div class="card"><div class="label">승 / 패</div><div class="value">{{ metrics.win_trades }} / {{ metrics.loss_trades }}</div></div>
        </div>

        {% if available_stocks %}
          <div class="section card">
            <h2>당일 거래 종목</h2>
            <div class="flow">
              {% for item in available_stocks[:20] %}
                <a class="tag" href="/trade-review?date={{ report.date }}&code={{ item.code }}&scope={{ report.scope }}">{{ item.label }}</a>
              {% endfor %}
            </div>
          </div>
        {% endif %}

        {% if report.scope != 'all' %}
          <div class="section card">
            <h2>표시 기준</h2>
            <div class="meta">이 화면은 기본적으로 실제 진입/주문 이력이 있는 건만 표시합니다. 즉 `buy_time`이 있거나, `buy_qty > 0`, 또는 상태가 `BUY_ORDERED / HOLDING / SELL_ORDERED / COMPLETED`인 레코드만 포함합니다.</div>
            <div class="meta" style="margin-top: 8px;">`EXPIRED`처럼 감시만 하다가 진입 없이 종료된 후보는 기본 제외하며, 필요하면 우측 상단에서 `전체 레코드`로 바꿔 확인할 수 있습니다.</div>
          </div>
        {% endif %}

        <div class="section card">
          <h2>보유 이벤트 분포</h2>
          <div class="bars">
            {% for item in event_breakdown %}
              <div class="bar-row">
                <div>{{ item.label }}</div>
                <div class="bar"><div class="fill" style="width: {{ (item.count / event_breakdown[0].count * 100) if event_breakdown and event_breakdown[0].count else 0 }}%"></div></div>
                <div>{{ item.count }}</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>거래별 복기</h2>
          {% for row in recent_trades %}
            <div class="row">
              <div class="title">{{ row.name }} ({{ row.code }}) / ID {{ row.id }}</div>
              <div class="meta">
                {{ row.strategy }} · {{ row.status }} · 매수 {{ "{:,}".format(row.buy_price|int) }}원 x {{ row.buy_qty }}주
                {% if row.sell_time %}
                  · 매도 {{ "{:,}".format(row.sell_price|int) }}원 · {{ row.sell_time }}
                {% endif %}
              </div>
              <div class="meta">
                손익률 <span class="{{ row.tone }}">{{ "%+.2f"|format(row.profit_rate) }}%</span>
                / 실현손익 {{ "{:,}".format(row.realized_pnl_krw) }}원
                / 보유시간 {{ row.holding_duration_text }}
              </div>
              {% if row.gatekeeper_replay %}
                <div class="meta" style="margin-top: 10px;">진입 전 Gatekeeper 판단</div>
                <div class="flow">
                  <a class="tag good" href="{{ row.gatekeeper_replay.url }}" target="_blank" rel="noopener">리플레이 보기</a>
                  {% if row.gatekeeper_replay.action %}
                    <span class="tag {% if row.gatekeeper_replay.allow_entry %}good{% else %}warn{% endif %}">
                      {{ row.gatekeeper_replay.action }}
                    </span>
                  {% endif %}
                  <span class="meta">{{ row.gatekeeper_replay.timestamp }}</span>
                </div>
                {% if row.gatekeeper_replay.report_preview %}
                  <div class="detail-flow">
                    <span class="detail-chip">{{ row.gatekeeper_replay.report_preview }}</span>
                  </div>
                {% endif %}
              {% endif %}
              {% if row.exit_signal %}
                <div class="meta" style="margin-top: 10px;">마지막 청산 시그널</div>
                <div class="flow">
                  <span class="tag bad">{{ row.exit_signal.label }}</span>
                  {% if row.exit_signal.sell_reason_type %}
                    <span class="tag bad">{{ row.exit_signal.sell_reason_type }}</span>
                  {% endif %}
                  {% if row.exit_signal.exit_rule %}
                    <span class="tag bad">{{ row.exit_signal.exit_rule }}</span>
                  {% endif %}
                  {% if row.exit_signal.reason %}
                    <span class="tag bad">{{ row.exit_signal.reason }}</span>
                  {% endif %}
                  <span class="meta">{{ row.exit_signal.timestamp }}</span>
                </div>
              {% endif %}
              {% if row.timeline %}
                <div class="meta" style="margin-top: 10px;">핵심 흐름</div>
                <div class="flow">
                  {% for item in row.timeline %}
                    <span class="tag {% if item.stage == 'sell_completed' %}good{% elif item.stage in ['exit_signal','sell_order_failed'] %}bad{% elif item.stage == 'ai_holding_review' %}warn{% endif %}">{{ item.label }}</span>
                    {% if not loop.last %}
                      <span class="arrow">→</span>
                    {% endif %}
                  {% endfor %}
                </div>
              {% endif %}
              {% if row.ai_reviews %}
                <div class="meta" style="margin-top: 10px;">최근 AI 보유감시</div>
                <div class="detail-flow">
                  {% for item in row.ai_reviews %}
                    <span class="detail-chip">{{ item.timestamp }} / AI {{ item.ai_score }} / 수익 {{ item.profit_rate }}% / 카운트 {{ item.low_score_hits }}</span>
                  {% endfor %}
                </div>
              {% endif %}
              {% if row.latest_event and row.latest_event.details %}
                <div class="meta" style="margin-top: 10px;">최신 이벤트 세부값</div>
                <div class="detail-flow">
                  {% for item in row.latest_event.details %}
                    <span class="detail-chip">{{ item.label }}: {{ item.value }}</span>
                  {% endfor %}
                </div>
              {% endif %}
            </div>
          {% else %}
            <div class="meta">표시할 거래가 없습니다.</div>
          {% endfor %}
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        report=report,
        metrics=metrics,
        recent_trades=recent_trades,
        event_breakdown=event_breakdown,
        warnings=warnings,
        available_stocks=available_stocks,
        request=request,
    )

if __name__ == '__main__':
    # 외부(EC2 퍼블릭 IP)에서 접속할 수 있도록 host를 0.0.0.0으로 설정합니다.
    debug_enabled = str(os.environ.get("KORSTOCKSCAN_WEB_DEBUG", "")).lower() in {"1", "true", "yes", "y"}
    app.run(host='0.0.0.0', port=5000, debug=debug_enabled)
