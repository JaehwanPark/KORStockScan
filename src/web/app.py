from flask import Flask, jsonify, render_template_string, request
import os
import sys

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.engine.sniper_strength_observation_report import build_strength_momentum_report
from src.engine.sniper_entry_pipeline_report import build_entry_pipeline_flow_report
from src.engine.daily_report_service import (
    list_available_report_dates,
    load_or_build_daily_report,
)

@app.route("/api/daily-report")
def daily_report_api():
    from datetime import datetime

    target_date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    refresh = str(request.args.get("refresh", "")).lower() in {"1", "true", "yes", "y"}
    report = load_or_build_daily_report(target_date, refresh=refresh)
    report["available_dates"] = list_available_report_dates(limit=40)
    return jsonify(report)


@app.route("/")
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
        from datetime import datetime

        target_date = datetime.now().strftime('%Y-%m-%d')
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
        from datetime import datetime

        target_date = datetime.now().strftime('%Y-%m-%d')

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
        from datetime import datetime

        target_date = datetime.now().strftime('%Y-%m-%d')
    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    return jsonify(report)


@app.route('/entry-pipeline-flow')
def entry_pipeline_flow_preview():
    target_date = request.args.get('date')
    since = request.args.get('since')
    top = request.args.get('top', default=10, type=int)
    if not target_date:
        from datetime import datetime

        target_date = datetime.now().strftime('%Y-%m-%d')

    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    metrics = report.get('metrics', {}) or {}
    blockers = report.get('blocker_breakdown', []) or []
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
        .flow { margin-top: 10px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
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
            <div class="chip">date: {{ report.date }}</div>
            <div class="chip">since: {{ report.since or '전체' }}</div>
            <div class="chip">추적 종목 {{ metrics.tracked_stocks }}개</div>
            <div class="chip">차단 {{ metrics.blocked_stocks }}개</div>
            <div class="chip">주문 제출 {{ metrics.submitted_stocks }}개</div>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="label">총 이벤트</div><div class="value">{{ metrics.total_events }}</div></div>
          <div class="card"><div class="label">추적 종목</div><div class="value">{{ metrics.tracked_stocks }}</div></div>
          <div class="card"><div class="label">차단 종목</div><div class="value blocked">{{ metrics.blocked_stocks }}</div></div>
          <div class="card"><div class="label">대기 종목</div><div class="value waiting">{{ metrics.waiting_stocks }}</div></div>
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
          <h2>종목별 최신 플로우</h2>
          <div class="stock-list">
            {% for row in recent_stocks %}
              <div class="row">
                <div class="title">{{ row.name }} ({{ row.code }})</div>
                <div class="meta">
                  최신 상태:
                  <span class="{{ row.latest_status.kind }}">{{ row.latest_status.label }}</span>
                  {% if row.latest_status.reason %}/ {{ row.latest_status.reason }}{% endif %}
                  / {{ row.latest_status.timestamp }}
                </div>
                <div class="meta" style="margin-top: 8px;">누적 통과 단계</div>
                <div class="flow">
                  {% for item in row.pass_flow %}
                    <span class="tag {{ item.kind }}">{{ item.label }}</span>
                    {% if not loop.last %}
                      <span class="arrow">→</span>
                    {% endif %}
                  {% endfor %}
                </div>
                {% if row.latest_status.kind in ['blocked', 'waiting'] %}
                  <div class="meta" style="margin-top: 10px;">마지막 차단/대기</div>
                  <div class="flow">
                    <span class="tag {{ row.latest_status.kind }}">{{ row.latest_status.label }}</span>
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
        recent_stocks=recent_stocks,
    )

if __name__ == '__main__':
    # 외부(EC2 퍼블릭 IP)에서 접속할 수 있도록 host를 0.0.0.0으로 설정합니다.
    debug_enabled = str(os.environ.get("KORSTOCKSCAN_WEB_DEBUG", "")).lower() in {"1", "true", "yes", "y"}
    app.run(host='0.0.0.0', port=5000, debug=debug_enabled)
