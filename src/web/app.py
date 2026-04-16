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
from src.engine.sniper_performance_tuning_report import (
    PERFORMANCE_TUNING_SCHEMA_VERSION,
    build_performance_tuning_report,
)
from src.engine.sniper_post_sell_feedback import (
    POST_SELL_REPORT_SCHEMA_VERSION,
    build_post_sell_feedback_report,
)
from src.engine.strategy_position_performance_report import build_strategy_position_performance_report
from src.engine.sniper_gatekeeper_replay import (
    find_gatekeeper_snapshot,
    load_gatekeeper_snapshots,
    rerun_gatekeeper_snapshot,
)
from src.engine.log_archive_service import load_monitor_snapshot
from src.engine.sniper_config import CONF
from src.engine.daily_report_service import (
    list_available_report_dates,
    load_or_build_daily_report,
)

_DEFAULT_DASHBOARD_LOOKBACK_MINUTES = 120
_TRUTHY_QUERY_VALUES = {"1", "true", "yes", "y"}


def _today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _request_target_date(*, fallback: str | None = None) -> str:
    target_date = str(request.args.get("date") or "").strip()
    if target_date:
        return target_date
    if fallback is not None:
        return str(fallback)
    return _today_string()


def _request_flag(name: str) -> bool:
    return str(request.args.get(name, "")).lower() in _TRUTHY_QUERY_VALUES


def _request_stripped(name: str) -> str:
    return str(request.args.get(name) or "").strip()


def _request_since(target_date: str) -> str | None:
    return _resolve_dashboard_since(target_date, request.args.get("since"))


def _request_top(default: int) -> int:
    return request.args.get("top", default=default, type=int)


def _request_scope(default: str = "entered") -> str:
    scope = _request_stripped("scope")
    return scope or default


def _report_value(report: dict | None, *path, default=None):
    current = report or {}
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _report_dict(report: dict | None, *path) -> dict:
    value = _report_value(report, *path, default={})
    return value if isinstance(value, dict) else {}


def _report_list(report: dict | None, *path) -> list:
    value = _report_value(report, *path, default=[])
    return value if isinstance(value, list) else []


def _resolve_dashboard_since(target_date: str, since: str | None) -> str | None:
    if since:
        return since
    today = _today_string()
    if str(target_date).strip() != today:
        return None
    return (datetime.now() - timedelta(minutes=_DEFAULT_DASHBOARD_LOOKBACK_MINUTES)).strftime("%H:%M:%S")


def _load_saved_performance_tuning_snapshot(target_date: str, since: str | None, refresh: bool) -> dict | None:
    if refresh or since:
        return None
    snapshot = load_monitor_snapshot("performance_tuning", target_date)
    if not snapshot:
        return None
    schema_version = int(((snapshot.get("meta") or {}).get("schema_version")) or 0)
    if schema_version != PERFORMANCE_TUNING_SCHEMA_VERSION:
        return None
    return snapshot


def _load_saved_trade_review_snapshot(
    target_date: str,
    *,
    since: str | None,
    code: str | None,
    scope: str,
    top: int,
    refresh: bool,
) -> dict | None:
    if refresh or since or code or str(scope or "entered").strip().lower() != "entered":
        return None
    snapshot = load_monitor_snapshot("trade_review", target_date)
    if not snapshot:
        return None
    snapshot["recent_trades"] = list(snapshot.get("recent_trades") or [])[: max(1, int(top or 10))]
    return snapshot


def _load_or_build_performance_tuning_report(
    *,
    target_date: str,
    since: str | None,
    refresh: bool,
) -> dict:
    report = _load_saved_performance_tuning_snapshot(target_date, since, refresh)
    if report is None:
        report = build_performance_tuning_report(target_date=target_date, since_time=since)
    return report


def _load_saved_post_sell_feedback_snapshot(target_date: str, refresh: bool) -> dict | None:
    if refresh:
        return None
    snapshot = load_monitor_snapshot("post_sell_feedback", target_date)
    if not snapshot:
        return None
    schema_version = int(((snapshot.get("meta") or {}).get("schema_version")) or 0)
    if schema_version != POST_SELL_REPORT_SCHEMA_VERSION:
        return None
    return snapshot


def _load_or_build_post_sell_feedback_report(
    *,
    target_date: str,
    top: int,
    refresh: bool,
    evaluate_now_when_build: bool = True,
) -> dict:
    report = _load_saved_post_sell_feedback_snapshot(target_date, refresh)
    if report is None:
        report = build_post_sell_feedback_report(
            target_date=target_date,
            top_n=max(1, int(top or 10)),
            evaluate_now=bool(evaluate_now_when_build),
        )
    return report


def _load_or_build_trade_review_report(
    *,
    target_date: str,
    since: str | None,
    code: str | None,
    scope: str,
    top: int,
    refresh: bool,
) -> dict:
    report = _load_saved_trade_review_snapshot(
        target_date,
        since=since,
        code=code,
        scope=scope,
        top=top,
        refresh=refresh,
    )
    if report is None:
        report = build_trade_review_report(
            target_date=target_date,
            code=code,
            since_time=since,
            top_n=max(1, int(top or 10)),
            scope=scope,
        )
    return report


def _build_post_sell_kpi_cards(post_sell_report: dict | None) -> list[dict]:
    metrics = _report_dict(post_sell_report, "metrics")
    summary = _report_dict(post_sell_report, "summary")
    evaluated = int(metrics.get("evaluated_candidates", 0) or 0)
    missed_rate = float(metrics.get("missed_upside_rate", 0.0) or 0.0)
    avg_extra = float(metrics.get("avg_extra_upside_10m_pct", 0.0) or 0.0)
    avg_close = float(metrics.get("avg_close_after_sell_10m_pct", 0.0) or 0.0)
    tuning_pressure = float(metrics.get("timing_tuning_pressure_score", 0.0) or 0.0)
    extra_krw = int(metrics.get("estimated_extra_upside_10m_krw_sum", 0) or 0)
    missed_count = int(_report_dict(summary, "outcome_counts").get("MISSED_UPSIDE", 0) or 0)
    good_count = int(_report_dict(summary, "outcome_counts").get("GOOD_EXIT", 0) or 0)

    if evaluated <= 0:
        return [
            {
                "label": "Post-sell 평가",
                "value": "0건",
                "hint": "평가 데이터 누적 후 KPI가 표시됩니다.",
                "tone_class": "tone-warn",
            }
        ]

    def _tone_by_score(score: float) -> str:
        if score >= 65.0:
            return "tone-bad"
        if score >= 50.0:
            return "tone-warn"
        return "tone-good"

    return [
        {
            "label": "Post-sell 평균 추가상승 (MFE10m)",
            "value": f"{avg_extra:+.2f}%",
            "hint": f"평가 {evaluated}건 기준, 잠재 추가수익 {extra_krw:,}원",
            "tone_class": "tone-warn" if avg_extra >= 0.8 else "tone-good",
        },
        {
            "label": "Post-sell 매도 후 10분 평균 종가",
            "value": f"{avg_close:+.2f}%",
            "hint": f"MISSED {missed_count}건 / GOOD_EXIT {good_count}건 / missed {missed_rate:.1f}%",
            "tone_class": "tone-warn" if avg_close > 0.15 else "tone-good",
        },
        {
            "label": "Post-sell 매도시점 튜닝 압력",
            "value": f"{tuning_pressure:.1f}",
            "hint": "높을수록 exit_rule 미세조정 우선순위가 높습니다.",
            "tone_class": _tone_by_score(tuning_pressure),
        },
    ]

@app.route("/api/daily-report")
def daily_report_api():
    target_date = _request_target_date()
    refresh = _request_flag("refresh")
    report = load_or_build_daily_report(target_date, refresh=refresh)
    report["available_dates"] = list_available_report_dates(limit=40)
    return jsonify(report)


@app.route("/")
@app.route("/dashboard")
def dashboard_home():
    default_tab = request.args.get("tab") or "daily-report"
    target_date = _request_target_date()
    resolved_since = _request_since(target_date)
    top = _request_top(10)
    theme = (request.args.get("theme") or "light").strip().lower()
    if theme not in {"light", "dark"}:
        theme = "light"
    tab_labels = {
        "daily-report": "일일 전략 리포트",
        "entry-pipeline-flow": "진입 게이트 차단",
        "trade-review": "실제 매매 복기",
        "post-sell-feedback": "Post-sell 피드백",
        "strategy-performance": "전략 성과 분석",
        "gatekeeper-replay": "Gatekeeper 리플레이",
        "performance-tuning": "성능 튜닝 모니터",
    }

    tab_map = {
        "daily-report": f"/daily-report?date={target_date}",
        "entry-pipeline-flow": f"/entry-pipeline-flow?date={target_date}&top={max(1, int(top or 10))}" + (f"&since={resolved_since}" if resolved_since else ""),
        "trade-review": f"/trade-review?date={target_date}",
        "post-sell-feedback": f"/post-sell-feedback?date={target_date}&top={max(1, int(top or 10))}&refresh=0",
        "strategy-performance": f"/strategy-performance?date={target_date}",
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
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
      <title>KORStockScan Dashboard</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">
      <style>
        :root {
          --bg: #f8fafc;
          --bg-elevated: #ffffff;
          --bg-soft: #f1f5f9;
          --card: #ffffff;
          --ink: #0f172a;
          --muted: #64748b;
          --line: rgba(148, 163, 184, 0.24);
          --line-strong: rgba(148, 163, 184, 0.4);
          --accent: #0053db;
          --accent-strong: #0b57d0;
          --success: #10b981;
          --navy: #0f172a;
          --hero-start: #ffffff;
          --hero-end: #eff6ff;
          --hero-border: rgba(37, 99, 235, 0.14);
          --frame-bg: #ffffff;
          --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        }
        html.dark {
          --bg: #000000;
          --bg-elevated: #111111;
          --bg-soft: #0b0b0b;
          --card: #111111;
          --ink: #f8fafc;
          --muted: #94a3b8;
          --line: #222222;
          --line-strong: #333333;
          --accent: #3b82f6;
          --accent-strong: #60a5fa;
          --success: #10b981;
          --navy: #000000;
          --hero-start: #0a0a0a;
          --hero-end: #111111;
          --hero-border: #1f2937;
          --frame-bg: #050505;
          --shadow: none;
        }
        body {
          margin: 0;
          background:
            radial-gradient(circle at top left, rgba(0, 83, 219, 0.09), transparent 28%),
            radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 24%),
            var(--bg);
          color: var(--ink);
          font-family: "Inter", "Pretendard", "Noto Sans KR", sans-serif;
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
        .telegram-cta {
          margin-top: 18px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          padding: 16px 18px;
          border-radius: 20px;
          border: 1px solid color-mix(in srgb, var(--accent) 18%, var(--line));
          background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 8%, var(--bg-elevated)), var(--bg-elevated));
          box-shadow: var(--shadow);
        }
        .telegram-copy {
          min-width: 0;
        }
        .telegram-copy small {
          display: block;
          color: var(--accent-strong);
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 6px;
        }
        .telegram-copy strong {
          display: block;
          font-size: 17px;
          line-height: 1.35;
        }
        .telegram-copy span {
          display: block;
          margin-top: 5px;
          color: var(--muted);
          font-size: 13px;
          line-height: 1.5;
        }
        .telegram-link {
          flex-shrink: 0;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 11px 16px;
          border-radius: 999px;
          background: var(--accent);
          color: #fff;
          text-decoration: none;
          font-weight: 800;
          white-space: nowrap;
        }
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
          background: color-mix(in srgb, var(--accent) 10%, var(--bg-elevated));
          border-color: color-mix(in srgb, var(--accent) 26%, var(--line));
          color: var(--accent-strong);
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
          background: var(--card);
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
        .rail-kpi {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 14px;
        }
        .rail-kpi-item {
          background: var(--bg-soft);
          border-radius: 16px;
          padding: 12px;
        }
        .rail-kpi-label {
          color: var(--muted);
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 6px;
        }
        .rail-kpi-value {
          font-size: 15px;
          font-weight: 800;
        }
        @media (max-width: 900px) {
          .hero-meta { width: 100%; }
          .hero-meta-grid { grid-template-columns: 1fr 1fr; }
          iframe { min-height: 1900px; }
          .dashboard-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .telegram-cta { align-items: stretch; flex-direction: column; }
          .telegram-link { width: 100%; }
          .hero-meta-grid { grid-template-columns: 1fr; }
          .topbar { align-items: stretch; flex-direction: column; }
          .hero h2 { font-size: 28px; }
          .rail-kpi { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="topbar">
          <div class="topbar-copy">
            <small>Integrated Monitor Shell</small>
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
              <h2>운영 화면을 한 셸에서 읽는 통합 대시보드</h2>
              <p>일일 전략 리포트, 진입 게이트 차단, 실제 매매 복기, post-sell 피드백, 전략 성과 분석, Gatekeeper 리플레이, 성능 튜닝 모니터를 같은 관제 흐름에서 넘겨보도록 정리했습니다.</p>
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
          <a class="tab {% if active_tab == 'post-sell-feedback' %}active{% endif %}" href="/dashboard?tab=post-sell-feedback&date={{ target_date }}&top={{ top }}">
            <span class="tab-label">Post-sell 피드백<small>매도시점 정밀 점검</small></span>
          </a>
          <a class="tab {% if active_tab == 'strategy-performance' %}active{% endif %}" href="/dashboard?tab=strategy-performance&date={{ target_date }}">
            <span class="tab-label">전략 성과 분석<small>전략·태그 성과 비교</small></span>
          </a>
          <a class="tab {% if active_tab == 'gatekeeper-replay' %}active{% endif %}" href="/dashboard?tab=gatekeeper-replay&date={{ target_date }}">
            <span class="tab-label">Gatekeeper 리플레이<small>진입 전 AI 판단 복기</small></span>
          </a>
          <a class="tab {% if active_tab == 'performance-tuning' %}active{% endif %}" href="/dashboard?tab=performance-tuning&date={{ target_date }}{% if resolved_since %}&since={{ resolved_since }}{% endif %}">
            <span class="tab-label">성능 튜닝 모니터<small>최적화 조정 포인트</small></span>
          </a>
        </div>

        <div class="telegram-cta">
          <div class="telegram-copy">
            <small>Telegram Bot</small>
            <strong>실시간 체결·보유감시 알림은 <code>@KORStockScan_bot</code>에서 받아보세요.</strong>
            <span>대시보드 복기와 함께 텔레그램으로 즉시 흐름을 확인할 수 있도록 운영 알림 채널을 연결했습니다.</span>
          </div>
          <a class="telegram-link" href="https://t.me/KORStockScan_bot" target="_blank" rel="noopener noreferrer">텔레그램 열기</a>
        </div>

        <div class="dashboard-grid">
          <div>
            <div class="frame-card">
              <iframe src="{{ active_src }}" title="KORStockScan dashboard view"></iframe>
            </div>
          </div>
          <div class="rail">
            <div class="rail-card">
              <h3>텔레그램 알림</h3>
              <p>실시간 체결, 보유감시, 주요 상태 변화를 텔레그램에서 바로 확인하려면 <code>@KORStockScan_bot</code>을 이용하면 됩니다.</p>
              <ul>
                <li>실매매 이벤트를 대시보드보다 빠르게 확인</li>
                <li>보유감시·청산 신호 흐름을 모바일에서 바로 추적</li>
                <li>운영 중 이슈를 즉시 점검할 수 있는 보조 채널</li>
              </ul>
              <p style="margin-top: 12px;"><a class="telegram-link" href="https://t.me/KORStockScan_bot" target="_blank" rel="noopener noreferrer">봇 바로가기</a></p>
            </div>
            <div class="rail-card">
              <h3>운영 포인트</h3>
              <p>최근에 추가된 복기 정규화, 전략 성과, 성능 튜닝 화면까지 같은 셸에서 확인할 수 있도록 `main` 기준 기능셋을 유지한 채 레이아웃을 재구성했습니다.</p>
              <div class="rail-kpi">
                <div class="rail-kpi-item">
                  <div class="rail-kpi-label">활성 탭</div>
                  <div class="rail-kpi-value">{{ active_tab_label }}</div>
                </div>
                <div class="rail-kpi-item">
                  <div class="rail-kpi-label">탭 개수</div>
                  <div class="rail-kpi-value">7개</div>
                </div>
                <div class="rail-kpi-item">
                  <div class="rail-kpi-label">조회 범위</div>
                  <div class="rail-kpi-value">{{ resolved_since or '전체 구간' }}</div>
                </div>
                <div class="rail-kpi-item">
                  <div class="rail-kpi-label">상위 표시</div>
                  <div class="rail-kpi-value">TOP {{ top }}</div>
                </div>
              </div>
            </div>
            <div class="rail-card">
              <h3>API 바로가기</h3>
              <ul>
                <li>`/api/daily-report?date=YYYY-MM-DD`</li>
                <li>`/api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`</li>
                <li>`/api/trade-review?date=YYYY-MM-DD&code=000000`</li>
                <li>`/api/post-sell-feedback?date=YYYY-MM-DD&top=10`</li>
                <li>`/api/strategy-performance?date=YYYY-MM-DD`</li>
                <li>`/api/gatekeeper-replay?date=YYYY-MM-DD`</li>
                <li>`/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS`</li>
              </ul>
            </div>
            <div class="rail-card">
              <h3>디자인 메모</h3>
              <p>`develop` 브랜치에서 진행했던 topbar, 테마 전환, 넓은 셸 레이아웃을 `main`의 최신 대시보드 기능과 합쳐 반영했습니다. 기존 데이터 경로와 라우팅은 그대로 유지합니다.</p>
            </div>
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

          const sync = (nextTheme) => {
            const isDark = nextTheme === "dark";
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
    available_dates = list_available_report_dates(limit=40)
    selected_date = _request_target_date(
        fallback=available_dates[0] if available_dates else _today_string()
    )
    refresh = _request_flag("refresh")
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
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
    target_date = _request_target_date()
    since = _request_since(target_date)
    top = _request_top(10)
    report = build_strength_momentum_report(
        target_date=target_date,
        top_n=max(1, int(top or 10)),
        since_time=since,
    )
    return jsonify(report)


@app.route('/strength-momentum')
def strength_momentum_preview():
    target_date = _request_target_date()
    since = _request_since(target_date)
    top = _request_top(5)

    report = build_strength_momentum_report(
        target_date=target_date,
        top_n=max(1, int(top or 5)),
        since_time=since,
    )
    metrics = _report_dict(report, 'metrics')
    top_passes = _report_list(report, 'sections', 'top_passes')
    near_misses = _report_list(report, 'sections', 'near_misses')
    override_candidates = _report_list(report, 'sections', 'dynamic_override_candidates')
    observed_reasons = _report_list(report, 'reason_breakdown', 'observed')

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
    target_date = _request_target_date()
    since = _request_since(target_date)
    top = _request_top(10)
    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    return jsonify(report)


@app.route('/api/gatekeeper-replay')
def gatekeeper_replay_api():
    target_date = _request_target_date()
    code = _request_stripped("code")
    target_time = _request_stripped("time") or None
    rerun = _request_flag("rerun")

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
    target_date = _request_target_date()
    since = _request_since(target_date)
    refresh = _request_flag("refresh")
    report = _load_or_build_performance_tuning_report(
        target_date=target_date,
        since=since,
        refresh=refresh,
    )
    return jsonify(report)


@app.route('/api/post-sell-feedback')
def post_sell_feedback_api():
    target_date = _request_target_date()
    top = _request_top(10)
    refresh = _request_flag("refresh")
    report = _load_or_build_post_sell_feedback_report(
        target_date=target_date,
        top=top,
        refresh=refresh,
    )
    return jsonify(report)


@app.route('/api/strategy-performance')
def strategy_performance_api():
    target_date = _request_target_date()
    refresh = _request_flag("refresh")
    report = build_strategy_position_performance_report(target_date=target_date, refresh=refresh)
    return jsonify(report)


@app.route('/entry-pipeline-flow')
def entry_pipeline_flow_preview():
    target_date = _request_target_date()
    since = _request_since(target_date)
    top = _request_top(10)

    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=since,
        top_n=max(1, int(top or 10)),
    )
    metrics = _report_dict(report, 'metrics')
    blockers = _report_list(report, 'blocker_breakdown')
    blocker_guide = _report_list(report, 'blocker_guide')
    latency_reason_breakdown = _report_list(report, 'latency_reason_breakdown')
    expired_armed_breakdown = _report_list(report, 'expired_armed_breakdown')
    recent_stocks = _report_list(report, 'sections', 'recent_stocks')

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
            <div class="chip">최신 시도 예산통과→제출 {{ metrics.budget_pass_to_submitted_rate or 0 }}%</div>
            <div class="chip">이벤트 예산통과→제출 {{ metrics.budget_pass_event_to_submitted_rate or 0 }}%</div>
            <div class="chip">Fresh quote latency pass {{ metrics.quote_fresh_latency_pass_rate or 0 }}%</div>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="label">추적 종목</div><div class="value">{{ metrics.tracked_stocks }}</div></div>
          <div class="card"><div class="label">차단 종목</div><div class="value blocked">{{ metrics.blocked_stocks }}</div></div>
          <div class="card"><div class="label">첫 AI 대기 종목</div><div class="value waiting">{{ metrics.waiting_stocks }}</div></div>
          <div class="card"><div class="label">주문 제출 종목</div><div class="value submitted">{{ metrics.submitted_stocks }}</div></div>
          <div class="card"><div class="label">최신 시도 예산통과 종목</div><div class="value">{{ metrics.budget_pass_stocks or 0 }}</div></div>
          <div class="card"><div class="label">최신 시도 예산통과→제출 전환율</div><div class="value submitted">{{ metrics.budget_pass_to_submitted_rate or 0 }}%</div></div>
          <div class="card"><div class="label">누적 budget_pass 이벤트</div><div class="value">{{ metrics.budget_pass_events or 0 }}</div></div>
          <div class="card"><div class="label">누적 이벤트 예산통과→제출 전환율</div><div class="value submitted">{{ metrics.budget_pass_event_to_submitted_rate or 0 }}%</div></div>
          <div class="card"><div class="label">Fresh quote latency pass율</div><div class="value">{{ metrics.quote_fresh_latency_pass_rate or 0 }}%</div></div>
          <div class="card"><div class="label">entry_armed 만료</div><div class="value waiting">{{ metrics.expired_armed_total or 0 }}</div></div>
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
          <h2>Latency 차단 사유 분포</h2>
          <div class="bars">
            {% for item in latency_reason_breakdown %}
              <div class="bar-row">
                <div>{{ item.reason }}</div>
                <div class="bar"><div class="fill" style="width: {{ (item.count / latency_reason_breakdown[0].count * 100) if latency_reason_breakdown and latency_reason_breakdown[0].count else 0 }}%"></div></div>
                <div>{{ item.count }}</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>entry_armed 만료 분포</h2>
          <div class="bars">
            {% for item in expired_armed_breakdown %}
              <div class="bar-row">
                <div>{{ item.label }}</div>
                <div class="bar"><div class="fill" style="width: {{ (item.count / expired_armed_breakdown[0].count * 100) if expired_armed_breakdown and expired_armed_breakdown[0].count else 0 }}%"></div></div>
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
        latency_reason_breakdown=latency_reason_breakdown,
        expired_armed_breakdown=expired_armed_breakdown,
        recent_stocks=recent_stocks,
    )


@app.route('/gatekeeper-replay')
def gatekeeper_replay_preview():
    target_date = _request_target_date()
    code = _request_stripped("code")
    target_time = _request_stripped("time") or None
    rerun = _request_flag("rerun")
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
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
    target_date = _request_target_date()
    since = _request_since(target_date)
    refresh = _request_flag("refresh")
    top = _request_top(10)

    report = _load_or_build_performance_tuning_report(
        target_date=target_date,
        since=since,
        refresh=refresh,
    )
    metrics = _report_dict(report, 'metrics')
    cards = _report_list(report, 'cards')
    watch_items = _report_list(report, 'watch_items')
    strategy_rows = _report_list(report, 'strategy_rows')
    auto_comments = _report_list(report, 'auto_comments')
    meta_info = _report_dict(report, 'meta')
    breakdowns = _report_dict(report, 'breakdowns')
    swing_daily_summary = _report_dict(report, 'sections', 'swing_daily_summary')
    top_holding_slow = _report_list(report, 'sections', 'top_holding_slow')
    top_gatekeeper_slow = _report_list(report, 'sections', 'top_gatekeeper_slow')
    top_dual_persona_slow = _report_list(report, 'sections', 'top_dual_persona_slow')
    post_sell_report = _load_or_build_post_sell_feedback_report(
        target_date=target_date,
        top=max(1, int(top or 10)),
        refresh=refresh,
        evaluate_now_when_build=False,
    )
    post_sell_kpi_cards = _build_post_sell_kpi_cards(post_sell_report)

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
            <div class="chip">Dual Persona shadow {{ metrics.dual_persona_shadow_samples or 0 }}건</div>
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

        <div class="section">
          <h2>스캘핑 퍼널/체결 품질</h2>
          <div class="grid">
            <div class="card">
              <div class="label">budget_pass 이벤트</div>
              <div class="value">{{ metrics.budget_pass_events or 0 }}</div>
            </div>
            <div class="card">
              <div class="label">order_bundle_submitted 이벤트</div>
              <div class="value">{{ metrics.order_bundle_submitted_events or 0 }}</div>
            </div>
            <div class="card">
              <div class="label">budget_pass→submitted 전환율</div>
              <div class="value">{{ metrics.budget_pass_to_submitted_rate or 0 }}%</div>
            </div>
            <div class="card">
              <div class="label">fresh quote latency pass율</div>
              <div class="value">{{ metrics.quote_fresh_latency_pass_rate or 0 }}%</div>
            </div>
            <div class="card">
              <div class="label">entry_armed 만료 이벤트</div>
              <div class="value">{{ metrics.expired_armed_events or 0 }}</div>
            </div>
            <div class="card">
              <div class="label">preset sync mismatch율</div>
              <div class="value">{{ metrics.preset_exit_sync_mismatch_rate or 0 }}%</div>
            </div>
            <div class="card">
              <div class="label">FULL_FILL 평균 손익률</div>
              <div class="value">{{ "%+.2f"|format(metrics.full_fill_completed_avg_profit_rate or 0.0) }}%</div>
            </div>
            <div class="card">
              <div class="label">PARTIAL_FILL 평균 손익률</div>
              <div class="value">{{ "%+.2f"|format(metrics.partial_fill_completed_avg_profit_rate or 0.0) }}%</div>
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Latency 차단 사유 분포</h2>
            <div class="list">
              {% for item in breakdowns.latency_reason_breakdown %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>
          <div class="card">
            <h2>Fill Quality Cohort 성과</h2>
            <div class="list">
              {% for item in breakdowns.fill_quality_cohorts %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건 / 평균 {{ "%+.2f"|format(item.avg_profit_rate or 0.0) }}%</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Preset Exit 동기화 상태</h2>
            <div class="list">
              {% for item in breakdowns.preset_exit_sync_status %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>
          <div class="card">
            <h2>AI Overlap 차단 stage</h2>
            <div class="list">
              {% for item in breakdowns.ai_overlap_blocked_stages %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
            <div class="meta" style="margin-top: 10px;">
              overbought_blocked 이벤트 {{ metrics.ai_overlap_overbought_blocked_events or 0 }}건
            </div>
          </div>
        </div>

        <div class="section">
          <h2>Post-sell 핵심 KPI</h2>
          <div class="grid">
            {% for item in post_sell_kpi_cards %}
              <div class="card">
                <div class="label">{{ item.label }}</div>
                <div class="value {{ item.tone_class }}">{{ item.value }}</div>
                {% if item.hint %}<div class="hint">{{ item.hint }}</div>{% endif %}
              </div>
            {% endfor %}
          </div>
          <div class="meta" style="margin-top: 8px;">
            상세 분석은 <code>/post-sell-feedback?date={{ report.date }}&top={{ top }}{% if refresh %}&refresh=1{% endif %}</code>에서 확인할 수 있습니다.
          </div>
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

        {% if swing_daily_summary %}
        <div class="section two-col">
          <div class="card">
            <h2>스윙 blocker 일일 요약</h2>
            <div class="comment-head">
              <span class="pill {{ 'tone-' + (swing_daily_summary.day_type.tone or 'warn') }}">{{ swing_daily_summary.day_type.label or '데이터 부족' }}</span>
              <span class="pill {{ 'tone-' + (swing_daily_summary.market_regime.status_tone or 'warn') }}">{{ swing_daily_summary.market_regime.status_text or '데이터 부족' }}</span>
              <span class="pill">
                swing {{ '허용' if swing_daily_summary.market_regime.allow_swing_entry else '보류' }}
                / score {{ swing_daily_summary.market_regime.swing_score or 0 }}
              </span>
            </div>
            <div class="meta" style="margin-top: 10px;">{{ swing_daily_summary.day_type.comment or '스윙 요약 코멘트가 없습니다.' }}</div>

            <div class="mini-grid">
              <div class="mini-card">
                <div class="mini-label">스윙 감시 종목</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.candidates or 0 }}</div>
              </div>
              <div class="mini-card">
                <div class="mini-label">실제 진입</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.entered_rows or 0 }}</div>
              </div>
              <div class="mini-card">
                <div class="mini-label">주문 제출</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.submitted or 0 }}</div>
              </div>
              <div class="mini-card">
                <div class="mini-label">최신 차단 종목</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.blocked_latest or 0 }}</div>
              </div>
              <div class="mini-card">
                <div class="mini-label">blocker 이벤트</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.blocker_event_count or 0 }}</div>
              </div>
              <div class="mini-card">
                <div class="mini-label">차단 종목 수</div>
                <div class="mini-value">{{ swing_daily_summary.metrics.blocked_stock_count or 0 }}</div>
              </div>
            </div>

            <div class="subsection-title">하루 blocker 분포</div>
            <div class="list">
              {% for item in swing_daily_summary.blocker_families %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건 / {{ item.stock_count }}종목 / {{ item.ratio }}%</div>
                </div>
              {% else %}
                <div class="meta">스윙 blocker 이벤트가 없습니다.</div>
              {% endfor %}
            </div>

            <div class="subsection-title">최신 blocker 분포</div>
            <div class="pill-row">
              {% for item in swing_daily_summary.latest_blockers %}
                <span class="pill">{{ item.label }} {{ item.count }}건 / {{ item.ratio }}%</span>
              {% else %}
                <span class="meta">최신 blocker 데이터가 없습니다.</span>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>스윙 Gatekeeper 액션 요약</h2>
            <div class="list">
              {% for item in swing_daily_summary.gatekeeper_actions %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건 / {{ item.ratio }}%</div>
                </div>
              {% else %}
                <div class="meta">아직 스윙 Gatekeeper 거부 액션 표본이 없습니다.</div>
              {% endfor %}
            </div>
            <div class="subsection-title">시장 국면 메모</div>
            <div class="meta">
              risk {{ swing_daily_summary.market_regime.risk_state or 'UNKNOWN' }}
              / regime {{ swing_daily_summary.market_regime.regime_code or 'UNKNOWN' }}
              / swing {{ '허용' if swing_daily_summary.market_regime.allow_swing_entry else '보류' }}
            </div>
            <div class="meta" style="margin-top: 10px;">
              `allow_swing_entry=false`인 날은 threshold 완화 근거일과 분리해서 해석하는 것이 plan 기준과 맞습니다.
            </div>
          </div>
        </div>
        {% endif %}

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
            <div class="meta" style="margin-top: 8px; font-size: 0.85em; color: #999;">
              action_age p95 {{ metrics.gatekeeper_action_age_p95 }}s / allow_entry_age p95 {{ metrics.gatekeeper_allow_entry_age_p95 }}s
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>보유 AI 재사용 차단 사유</h2>
            <div class="list">
              {% for item in breakdowns.holding_reuse_blockers %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>보유 AI 시그니처 변경 필드</h2>
            <div class="list">
              {% for item in breakdowns.holding_sig_deltas %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}회</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Dual Persona 결정 타입</h2>
            <div class="list">
              {% for item in breakdowns.dual_persona_decision_types %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 shadow 표본이 없습니다.</div>
              {% endfor %}
            </div>
            <div class="meta" style="margin-top: 12px;">
              Gatekeeper {{ metrics.dual_persona_gatekeeper_samples or 0 }}건 / Overnight {{ metrics.dual_persona_overnight_samples or 0 }}건
            </div>
          </div>

          <div class="card">
            <h2>Dual Persona 합의도</h2>
            <div class="list">
              {% for item in breakdowns.dual_persona_agreement %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 shadow 표본이 없습니다.</div>
              {% endfor %}
            </div>
            <div class="meta" style="margin-top: 12px;">
              충돌률 {{ metrics.dual_persona_conflict_ratio or 0 }}% / 보수 veto {{ metrics.dual_persona_conservative_veto_ratio or 0 }}% / override {{ metrics.dual_persona_fused_override_ratio or 0 }}%
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Dual Persona winner 분포</h2>
            <div class="list">
              {% for item in breakdowns.dual_persona_winners %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 shadow 표본이 없습니다.</div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>Dual Persona hard flag 분포</h2>
            <div class="list">
              {% for item in breakdowns.dual_persona_hard_flags %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">아직 hard flag 데이터가 없습니다.</div>
              {% endfor %}
            </div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Gatekeeper 재사용 차단 사유</h2>
            <div class="list">
              {% for item in breakdowns.gatekeeper_reuse_blockers %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}건</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
            </div>
          </div>

          <div class="card">
            <h2>Gatekeeper 시그니처 변경 필드</h2>
            <div class="list">
              {% for item in breakdowns.gatekeeper_sig_deltas %}
                <div class="row">
                  <div class="title">{{ item.label }}</div>
                  <div class="meta">{{ item.count }}회</div>
                </div>
              {% else %}
                <div class="meta">데이터 없음</div>
              {% endfor %}
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

        <div class="section card">
          <h2>느린 Dual Persona shadow 상위</h2>
          <div class="list">
            {% for item in top_dual_persona_slow %}
              <div class="row">
                <div class="title">{{ item.name }} ({{ item.code }})</div>
                <div class="meta">{{ item.timestamp }} / {{ item.decision_type }} / {{ item.shadow_extra_ms }}ms / {{ item.winner }} / {{ item.agreement_bucket }}</div>
              </div>
            {% else %}
              <div class="meta">아직 shadow 표본이 없습니다.</div>
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
        cards=cards,
        watch_items=watch_items,
        strategy_rows=strategy_rows,
        auto_comments=auto_comments,
        meta_info=meta_info,
        breakdowns=breakdowns,
        swing_daily_summary=swing_daily_summary,
        top_holding_slow=top_holding_slow,
        top_gatekeeper_slow=top_gatekeeper_slow,
        top_dual_persona_slow=top_dual_persona_slow,
        post_sell_kpi_cards=post_sell_kpi_cards,
        top=max(1, int(top or 10)),
        refresh=refresh,
    )


@app.route('/post-sell-feedback')
def post_sell_feedback_preview():
    target_date = _request_target_date()
    top = _request_top(10)
    refresh = _request_flag("refresh")

    report = _load_or_build_post_sell_feedback_report(
        target_date=target_date,
        top=top,
        refresh=refresh,
    )
    summary = _report_dict(report, "summary")
    metrics = _report_dict(report, "metrics")
    insight = _report_dict(report, "insight")
    exit_rule_rows = _report_list(report, "exit_rule_tuning")
    tag_rows = _report_list(report, "tag_tuning")
    priority_actions = _report_list(report, "priority_actions")
    top_missed = _report_list(report, "top_missed_upside")
    top_good = _report_list(report, "top_good_exit")
    meta_info = _report_dict(report, "meta")

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
      <title>Post-sell Feedback</title>
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
          background: linear-gradient(135deg, var(--navy), #227a53);
          color: white;
          padding: 22px;
          border-radius: 20px;
          box-shadow: 0 18px 44px rgba(24, 49, 83, 0.16);
        }
        .hero h1 { margin: 0 0 8px; font-size: 24px; }
        .hero p { margin: 0; opacity: 0.92; }
        .toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 14px; }
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
        .hint { color: var(--muted); font-size: 12px; margin-top: 6px; }
        .section { margin-top: 20px; }
        .section h2 { margin: 0 0 10px; font-size: 18px; }
        .row { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 10px; }
        .row:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
        .title { font-weight: 700; }
        .meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .good { color: var(--accent); }
        .warn { color: var(--warn); }
        .bad { color: var(--bad); }
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 9px 7px; border-top: 1px solid var(--line); vertical-align: top; }
        th { color: var(--muted); font-weight: 600; border-top: 0; }
        .tone-good { color: var(--accent); font-weight: 700; }
        .tone-warn { color: var(--warn); font-weight: 700; }
        .tone-bad { color: var(--bad); font-weight: 700; }
        @media (max-width: 960px) {
          .two-col { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Post-sell 피드백</h1>
          <p>핵심 목표: 1) 수익 극대화 여지 확인 2) 매도시점 미세조정 필요 지점 선별</p>
          <form method="GET" action="/post-sell-feedback" class="toolbar">
            <input type="date" name="date" value="{{ report.date }}">
            <label>
              <select name="top">
                {% for n in [5, 10, 20, 30] %}
                  <option value="{{ n }}" {% if n == top %}selected{% endif %}>TOP {{ n }}</option>
                {% endfor %}
              </select>
            </label>
            <label>
              <select name="refresh">
                <option value="0" {% if not refresh %}selected{% endif %}>snapshot 우선</option>
                <option value="1" {% if refresh %}selected{% endif %}>즉시 재평가</option>
              </select>
            </label>
            <button type="submit">조회</button>
          </form>
          <div class="chips">
            <span class="chip">후보 {{ metrics.total_candidates or 0 }}건</span>
            <span class="chip">평가 {{ metrics.evaluated_candidates or 0 }}건</span>
            <span class="chip">MISSED_UPSIDE {{ summary.outcome_counts.MISSED_UPSIDE if summary.outcome_counts else 0 }}건</span>
            <span class="chip">GOOD_EXIT {{ summary.outcome_counts.GOOD_EXIT if summary.outcome_counts else 0 }}건</span>
          </div>
        </div>

        <div class="grid">
          <div class="card">
            <div class="label">수익 극대화 여지</div>
            <div class="value">{{ metrics.avg_extra_upside_10m_pct or 0 }}%</div>
            <div class="hint">매도 후 10분 내 추가 고점 평균 (MFE)</div>
          </div>
          <div class="card">
            <div class="label">매도 후 10분 종가</div>
            <div class="value {% if (metrics.avg_close_after_sell_10m_pct or 0) > 0 %}warn{% endif %}">{{ metrics.avg_close_after_sell_10m_pct or 0 }}%</div>
            <div class="hint">양수면 매도 후에도 상승 지속 가능성이 큼</div>
          </div>
          <div class="card">
            <div class="label">추정 추가수익(10분)</div>
            <div class="value">{{ "{:,}".format(metrics.estimated_extra_upside_10m_krw_sum or 0) }}원</div>
            <div class="hint">sell_price x qty x MFE(+) 기준 추정치</div>
          </div>
          <div class="card">
            <div class="label">매도시점 튜닝 압력</div>
            <div class="value {% if (metrics.timing_tuning_pressure_score or 0) >= 65 %}bad{% elif (metrics.timing_tuning_pressure_score or 0) >= 50 %}warn{% else %}good{% endif %}">
              {{ metrics.timing_tuning_pressure_score or 0 }}
            </div>
            <div class="hint">높을수록 매도 규칙 미세조정 우선순위가 높음</div>
          </div>
        </div>

        <div class="section card">
          <h2>요약 인사이트</h2>
          <div class="title">{{ insight.headline or '-' }}</div>
          <div class="meta">{{ insight.comment or '-' }}</div>
          <div class="meta">capture 효율 평균 {{ metrics.capture_efficiency_avg_pct or 0 }}% / 실현 평균 {{ metrics.avg_realized_profit_rate or 0 }}%</div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>즉시 점검 우선순위</h2>
            {% for item in priority_actions %}
              <div class="row">
                <div class="title">{{ item.exit_rule }} (score {{ item.tuning_pressure_score }})</div>
                <div class="meta">{{ item.reason }}</div>
                <div class="meta">{{ item.suggested_test }}</div>
              </div>
            {% else %}
              <div class="meta">우선순위 항목 없음</div>
            {% endfor %}
          </div>
          <div class="card">
            <h2>전략/태그별 히트맵</h2>
            {% for item in tag_rows[:top] %}
              <div class="row">
                <div class="title">{{ item.strategy }} / {{ item.position_tag }}</div>
                <div class="meta">
                  trades {{ item.trades }} /
                  missed {{ item.missed_upside_rate }}% /
                  close10m {{ item.avg_close_10m_pct }}% /
                  예상추가수익 {{ "{:,}".format(item.estimated_extra_upside_10m_krw or 0) }}원
                </div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>매도 규칙별 튜닝 후보</h2>
          <table>
            <thead>
              <tr>
                <th>exit_rule</th>
                <th>표본</th>
                <th>missed%</th>
                <th>good%</th>
                <th>avg ret%</th>
                <th>close10m%</th>
                <th>추정추가수익</th>
                <th>score</th>
                <th>hint</th>
              </tr>
            </thead>
            <tbody>
              {% for item in exit_rule_rows %}
                <tr>
                  <td>{{ item.exit_rule }}</td>
                  <td>{{ item.trades }}</td>
                  <td>{{ item.missed_upside_rate }}</td>
                  <td>{{ item.good_exit_rate }}</td>
                  <td>{{ item.avg_profit_rate }}</td>
                  <td>{{ item.avg_close_10m_pct }}</td>
                  <td>{{ "{:,}".format(item.estimated_extra_upside_10m_krw or 0) }}원</td>
                  <td class="{% if item.tuning_pressure_score >= 65 %}tone-bad{% elif item.tuning_pressure_score >= 50 %}tone-warn{% else %}tone-good{% endif %}">
                    {{ item.tuning_pressure_score }}
                  </td>
                  <td>{{ item.tuning_hint }}</td>
                </tr>
              {% else %}
                <tr><td colspan="9" class="meta">데이터 없음</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>상위 Missed Upside</h2>
            {% for item in top_missed %}
              <div class="row">
                <div class="title">{{ item.stock_name }} ({{ item.stock_code }})</div>
                <div class="meta">exit {{ item.exit_rule }} / ret {{ item.profit_rate }}%</div>
                <div class="meta">MFE10m {{ item.mfe_10m_pct }}% / Close10m {{ item.close_10m_pct }}% / 추가 {{ "{:,}".format(item.extra_upside_10m_krw_est or 0) }}원</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
          <div class="card">
            <h2>상위 Good Exit</h2>
            {% for item in top_good %}
              <div class="row">
                <div class="title">{{ item.stock_name }} ({{ item.stock_code }})</div>
                <div class="meta">exit {{ item.exit_rule }} / ret {{ item.profit_rate }}%</div>
                <div class="meta">MAE10m {{ item.mae_10m_pct }}% / Close10m {{ item.close_10m_pct }}%</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
        </div>

        <div class="section card">
          <h2>메타</h2>
          <div class="meta">schema v{{ meta_info.schema_version or '-' }} / generated {{ meta_info.generated_at or '-' }}</div>
          <div class="meta">평가 기준: 10분 윈도우 기반 MFE/MAE/Close</div>
          <div class="meta">API: <code>/api/post-sell-feedback?date={{ report.date }}&top={{ top }}</code></div>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(
        template,
        report=report,
        summary=summary,
        metrics=metrics,
        insight=insight,
        exit_rule_rows=exit_rule_rows,
        tag_rows=tag_rows,
        priority_actions=priority_actions,
        top_missed=top_missed,
        top_good=top_good,
        meta_info=meta_info,
        top=max(1, int(top or 10)),
        refresh=refresh,
    )


@app.route('/strategy-performance')
def strategy_performance_preview():
    target_date = _request_target_date()
    refresh = _request_flag("refresh")

    report = build_strategy_position_performance_report(target_date=target_date, refresh=refresh)
    summary = _report_dict(report, 'summary')
    kpis = _report_list(report, 'kpis')
    strategy_totals = _report_list(report, 'strategy_totals')
    rows = _report_list(report, 'rows')
    top_winners = _report_list(report, 'sections', 'top_winners')
    top_losers = _report_list(report, 'sections', 'top_losers')

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
      <title>Strategy Performance</title>
      <style>
        :root {
          --bg: #f4f7ef;
          --card: #fcfffa;
          --ink: #1b2a22;
          --muted: #6c7f73;
          --line: #d7e2d5;
          --accent: #1d7a52;
        }
        body { margin: 0; background: var(--bg); color: var(--ink); font-family: "Pretendard", "Noto Sans KR", sans-serif; }
        .wrap { max-width: 1180px; margin: 0 auto; padding: 24px 16px 48px; }
        .hero { background: linear-gradient(135deg, #1c3d31, #2d7a57); color: white; padding: 22px; border-radius: 20px; }
        .hero h1 { margin: 0 0 8px; font-size: 28px; }
        .hero p { margin: 0; opacity: 0.9; }
        .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
        .stat { background: rgba(255,255,255,0.12); border-radius: 16px; padding: 12px 14px; }
        .stat .label { font-size: 12px; opacity: 0.72; margin-bottom: 4px; }
        .stat .value { font-size: 22px; font-weight: 700; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
        .kpi-card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 16px; box-shadow: 0 10px 24px rgba(27,42,34,0.05); }
        .kpi-card.good { background: #edf8f0; border-color: #cde6d4; }
        .kpi-card.warn { background: #fff8ea; border-color: #f0dbb0; }
        .kpi-card.bad { background: #fff0f0; border-color: #efcaca; }
        .kpi-card.muted { background: #f5f7f4; border-color: #dde4da; }
        .kpi-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
        .kpi-value { font-size: 20px; font-weight: 800; line-height: 1.25; }
        .kpi-detail { margin-top: 6px; font-size: 12px; color: var(--muted); }
        .grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-top: 18px; }
        .card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 10px 24px rgba(27,42,34,0.05); }
        .card h2 { margin: 0 0 12px; font-size: 18px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 10px 8px; border-top: 1px solid var(--line); font-size: 13px; vertical-align: top; }
        th { color: var(--muted); font-weight: 600; border-top: 0; }
        .good { color: #176942; font-weight: 700; }
        .bad { color: #a12b2b; font-weight: 700; }
        .muted { color: var(--muted); }
        .chips { display: flex; flex-wrap: wrap; gap: 8px; }
        .chip { border: 1px solid var(--line); background: #f4f8f2; border-radius: 999px; padding: 6px 10px; font-size: 12px; }
        @media (max-width: 920px) {
          .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .kpi-grid { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>전략/포지션태그 성과</h1>
          <p>{{ target_date }} 기준 실제 매매 복기를 정규화한 성과 집계입니다.</p>
          <div class="stats">
            <div class="stat"><div class="label">전략 수</div><div class="value">{{ summary.strategy_count }}</div></div>
            <div class="stat"><div class="label">태그 그룹</div><div class="value">{{ summary.tag_group_count }}</div></div>
            <div class="stat"><div class="label">종료 거래</div><div class="value">{{ summary.completed_count }}</div></div>
            <div class="stat"><div class="label">실현손익</div><div class="value">{{ "{:,}".format(summary.realized_pnl_krw) }}원</div></div>
          </div>
        </div>

        <div class="kpi-grid">
          {% for item in kpis %}
            <div class="kpi-card {{ item.tone }}">
              <div class="kpi-label">{{ item.label }}</div>
              <div class="kpi-value">{{ item.value }}</div>
              <div class="kpi-detail">{{ item.detail }}</div>
            </div>
          {% else %}
            <div class="kpi-card muted">
              <div class="kpi-label">KPI</div>
              <div class="kpi-value">데이터 없음</div>
              <div class="kpi-detail">종료 거래가 쌓이면 KPI가 생성됩니다.</div>
            </div>
          {% endfor %}
        </div>

        <div class="grid">
          <div class="card">
            <h2>전략별 합산</h2>
            <table>
              <thead>
                <tr>
                  <th>전략</th>
                  <th>진입</th>
                  <th>종료</th>
                  <th>미종료</th>
                  <th>승/패</th>
                  <th>실현손익</th>
                </tr>
              </thead>
              <tbody>
                {% for row in strategy_totals %}
                  <tr>
                    <td>{{ row.strategy }}</td>
                    <td>{{ row.entered_count }}</td>
                    <td>{{ row.completed_count }}</td>
                    <td>{{ row.open_count }}</td>
                    <td>{{ row.win_count }}/{{ row.loss_count }}</td>
                    <td class="{% if row.realized_pnl_krw > 0 %}good{% elif row.realized_pnl_krw < 0 %}bad{% endif %}">{{ "{:,}".format(row.realized_pnl_krw) }}원</td>
                  </tr>
                {% else %}
                  <tr><td colspan="6" class="muted">데이터 없음</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>

          <div class="card">
            <h2>상위 인사이트</h2>
            <div class="chips">
              {% for row in rows[:8] %}
                <span class="chip">
                  {{ row.strategy }} / {{ row.position_tag }} · {{ row.completed_count }}건 ·
                  <span class="{% if row.realized_pnl_krw > 0 %}good{% elif row.realized_pnl_krw < 0 %}bad{% endif %}">
                    {{ "{:,}".format(row.realized_pnl_krw) }}원
                  </span>
                </span>
              {% else %}
                <span class="muted">요약 데이터가 없습니다.</span>
              {% endfor %}
            </div>
          </div>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h2>전략 × 포지션태그 상세</h2>
          <table>
            <thead>
              <tr>
                <th>전략</th>
                <th>포지션태그</th>
                <th>진입</th>
                <th>종료</th>
                <th>승/패/보합</th>
                <th>평균 손익률</th>
                <th>평균 보유</th>
                <th>실현손익</th>
                <th>최고/최저</th>
              </tr>
            </thead>
            <tbody>
              {% for row in rows %}
                <tr>
                  <td>{{ row.strategy }}</td>
                  <td>{{ row.position_tag }}</td>
                  <td>{{ row.entered_count }}</td>
                  <td>{{ row.completed_count }} / 미종료 {{ row.open_count }}</td>
                  <td>{{ row.win_count }} / {{ row.loss_count }} / {{ row.flat_count }}</td>
                  <td class="{% if row.avg_profit_rate > 0 %}good{% elif row.avg_profit_rate < 0 %}bad{% endif %}">{{ "%+.2f"|format(row.avg_profit_rate) }}%</td>
                  <td>{{ row.avg_holding_seconds }}초</td>
                  <td class="{% if row.realized_pnl_krw > 0 %}good{% elif row.realized_pnl_krw < 0 %}bad{% endif %}">{{ "{:,}".format(row.realized_pnl_krw) }}원</td>
                  <td>
                    {% if row.best_trade_code %}
                      최고 {{ row.best_trade_name }}({{ row.best_trade_code }}) {{ "%+.2f"|format(row.best_profit_rate) }}%<br>
                    {% endif %}
                    {% if row.worst_trade_code %}
                      최저 {{ row.worst_trade_name }}({{ row.worst_trade_code }}) {{ "%+.2f"|format(row.worst_profit_rate) }}%
                    {% endif %}
                  </td>
                </tr>
              {% else %}
                <tr><td colspan="9" class="muted">상세 데이터가 없습니다.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>

        <div class="grid" style="margin-top: 16px;">
          <div class="card">
            <h2>상위 익절 거래</h2>
            <table>
              <thead><tr><th>종목</th><th>전략</th><th>손익률</th><th>실현손익</th></tr></thead>
              <tbody>
                {% for row in top_winners %}
                  <tr>
                    <td>{{ row.stock_name }}({{ row.stock_code }})</td>
                    <td>{{ row.strategy }} / {{ row.position_tag }}</td>
                    <td class="good">{{ "%+.2f"|format(row.profit_rate) }}%</td>
                    <td class="good">{{ "{:,}".format(row.realized_pnl_krw) }}원</td>
                  </tr>
                {% else %}
                  <tr><td colspan="4" class="muted">데이터 없음</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          <div class="card">
            <h2>상위 손실 거래</h2>
            <table>
              <thead><tr><th>종목</th><th>전략</th><th>손익률</th><th>실현손익</th></tr></thead>
              <tbody>
                {% for row in top_losers %}
                  <tr>
                    <td>{{ row.stock_name }}({{ row.stock_code }})</td>
                    <td>{{ row.strategy }} / {{ row.position_tag }}</td>
                    <td class="bad">{{ "%+.2f"|format(row.profit_rate) }}%</td>
                    <td class="bad">{{ "{:,}".format(row.realized_pnl_krw) }}원</td>
                  </tr>
                {% else %}
                  <tr><td colspan="4" class="muted">데이터 없음</td></tr>
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
        target_date=target_date,
        summary=summary,
        kpis=kpis,
        strategy_totals=strategy_totals,
        rows=rows,
        top_winners=top_winners,
        top_losers=top_losers,
    )


@app.route('/api/trade-review')
def trade_review_api():
    target_date = _request_target_date()
    since = _request_since(target_date)
    code = _request_stripped("code") or None
    scope = _request_scope("entered")
    top = _request_top(10)
    refresh = _request_flag("refresh")
    report = _load_or_build_trade_review_report(
        target_date=target_date,
        since=since,
        code=code,
        scope=scope,
        top=top,
        refresh=refresh,
    )
    return jsonify(report)


@app.route('/trade-review')
def trade_review_preview():
    target_date = _request_target_date()
    since = _request_since(target_date)
    code = _request_stripped("code") or None
    scope = _request_scope("entered")
    top = _request_top(10)
    refresh = _request_flag("refresh")

    report = _load_or_build_trade_review_report(
        target_date=target_date,
        since=since,
        code=code,
        scope=scope,
        top=top,
        refresh=refresh,
    )
    metrics = _report_dict(report, 'metrics')
    recent_trades = _report_list(report, 'sections', 'recent_trades')
    event_breakdown = _report_list(report, 'event_breakdown')
    warnings = _report_list(report, 'meta', 'warnings')
    available_stocks = _report_list(report, 'meta', 'available_stocks')
    fill_quality_summary = _report_dict(report, 'sections', 'fill_quality_summary')
    hard_stop_taxonomy = _report_dict(report, 'sections', 'hard_stop_taxonomy')

    template = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta name="google-adsense-account" content="ca-pub-9559810990033158">
      <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9559810990033158" crossorigin="anonymous"></script>
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
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .row { border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }
        .row:first-child { border-top: 0; padding-top: 0; margin-top: 0; }
        .title { font-weight: 700; font-size: 16px; }
        .title-line {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
        }
        .result-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border-radius: 999px;
          padding: 5px 10px;
          font-size: 12px;
          font-weight: 700;
          border: 1px solid var(--line);
          background: #edf5ee;
        }
        .result-badge.good { background: #e7f6ee; border-color: #b8dfc8; color: #176942; }
        .result-badge.warn { background: #fff3df; border-color: #f1d29d; color: #9a5b10; }
        .result-badge.bad { background: #fdeaea; border-color: #efb8b8; color: #a12b2b; }
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
        .tag.muted { background: #f2f5f1; border-color: #dbe4d7; color: #6c7f73; }
        .arrow { color: var(--muted); font-size: 12px; }
        .detail-flow { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
        .detail-chip { border-radius: 999px; padding: 4px 9px; font-size: 12px; background: #f3f7f2; border: 1px solid var(--line); color: var(--ink); }
        .insight-box {
          margin-top: 8px;
          border-radius: 14px;
          border: 1px solid var(--line);
          background: #f7fbf6;
          padding: 12px 13px;
        }
        .insight-box.good { background: #edf8f0; border-color: #cde6d4; }
        .insight-box.warn { background: #fff8ea; border-color: #f0dbb0; }
        .insight-box.bad { background: #fff0f0; border-color: #efcaca; }
        .insight-box.muted { background: #f5f7f4; border-color: #dde4da; }
        .insight-title { font-size: 13px; font-weight: 700; }
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

        <div class="section">
          <h2>체결 품질 / Hard Stop 감사</h2>
          <div class="grid">
            <div class="card"><div class="label">FULL_FILL 이벤트</div><div class="value">{{ metrics.full_fill_events or 0 }}</div></div>
            <div class="card"><div class="label">PARTIAL_FILL 이벤트</div><div class="value">{{ metrics.partial_fill_events or 0 }}</div></div>
            <div class="card"><div class="label">Preset sync mismatch</div><div class="value bad">{{ metrics.preset_exit_sync_mismatch_events or 0 }}</div></div>
            <div class="card"><div class="label">Hard Time Stop Shadow</div><div class="value warn">{{ metrics.hard_time_stop_shadow_events or 0 }}</div></div>
            <div class="card"><div class="label">Preset sync mismatch율</div><div class="value">{{ (fill_quality_summary.metrics or {}).get('preset_exit_sync_mismatch_rate', 0) }}%</div></div>
            <div class="card"><div class="label">Live hard stop 이벤트</div><div class="value">{{ (hard_stop_taxonomy.metrics or {}).get('live_hard_stop_events', 0) }}</div></div>
          </div>
        </div>

        <div class="section two-col">
          <div class="card">
            <h2>Fill Quality 분포</h2>
            {% for item in fill_quality_summary.fill_quality_breakdown %}
              <div class="row">
                <div class="title">{{ item.label }}</div>
                <div class="meta">{{ item.count }}건</div>
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}

            <h2 style="margin-top:16px;">최근 Sync Mismatch</h2>
            {% for item in fill_quality_summary.recent_mismatches %}
              <div class="row">
                <div class="title">{{ item.name }} ({{ item.code }})</div>
                <div class="meta">{{ item.timestamp }} / {{ item.sync_status }} / {{ item.sync_reason }}</div>
                <div class="meta">ord_no {{ item.preset_tp_ord_no_before }} → {{ item.preset_tp_ord_no_after }}</div>
              </div>
            {% else %}
              <div class="meta">불일치 표본 없음</div>
            {% endfor %}
          </div>
          <div class="card">
            <h2>Hard Stop Taxonomy</h2>
            {% for item in hard_stop_taxonomy.rows %}
              <div class="row">
                <div class="title">{{ item.label }}</div>
                <div class="meta">{{ item.mode }} / stage {{ item.stage }} / {{ item.count }}건</div>
                {% if item.entry_mode_position_tag_top %}
                  <div class="meta">top pair:
                    {% for pair in item.entry_mode_position_tag_top %}
                      {{ pair.label }} {{ pair.count }}건{% if not loop.last %}, {% endif %}
                    {% endfor %}
                  </div>
                {% endif %}
              </div>
            {% else %}
              <div class="meta">데이터 없음</div>
            {% endfor %}
          </div>
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
              <div class="title-line">
                <span class="result-badge {{ row.result_tone }}">{{ row.result_icon }} {{ row.result_label }}</span>
                <div class="title">{{ row.name }} ({{ row.code }}) / ID {{ row.id }}</div>
              </div>
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
                  {% for item in row.compact_timeline %}
                    <span class="tag {% if item.is_omitted %}muted{% elif item.stage == 'sell_completed' %}good{% elif item.stage in ['exit_signal','sell_order_failed'] %}bad{% elif item.stage == 'ai_holding_review' %}warn{% endif %}">{{ item.label }}</span>
                    {% if not loop.last %}
                      <span class="arrow">→</span>
                    {% endif %}
                  {% endfor %}
                </div>
                {% if row.timeline_hidden_count > 0 %}
                  <div class="meta">전체 {{ row.timeline|length }}단계 중 중간 {{ row.timeline_hidden_count }}단계를 접어서 표시합니다.</div>
                {% endif %}
              {% endif %}
              {% if row.ai_review_summary %}
                <div class="meta" style="margin-top: 10px;">최근 AI 보유감시 요약</div>
                <div class="insight-box {{ row.ai_review_summary.tone }}">
                  <div class="insight-title">{{ row.ai_review_summary.headline }}</div>
                  <div class="meta">{{ row.ai_review_summary.summary }}</div>
                  <div class="detail-flow">
                    {% for item in row.ai_review_summary.chips %}
                      <span class="detail-chip">{{ item.label }}: {{ item.value }}</span>
                    {% endfor %}
                  </div>
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
        fill_quality_summary=fill_quality_summary,
        hard_stop_taxonomy=hard_stop_taxonomy,
        request=request,
    )

if __name__ == '__main__':
    # 외부(EC2 퍼블릭 IP)에서 접속할 수 있도록 host를 0.0.0.0으로 설정합니다.
    debug_enabled = str(os.environ.get("KORSTOCKSCAN_WEB_DEBUG", "")).lower() in {"1", "true", "yes", "y"}
    app.run(host='0.0.0.0', port=5000, debug=debug_enabled)
