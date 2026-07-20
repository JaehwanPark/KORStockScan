import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import feedparser
from deep_translator import GoogleTranslator

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.utils.logger import log_error
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus

# 설정 상수 (수정 없음)
SOURCES = {
    "AlJazeera_War": "https://www.aljazeera.com/xml/rss/all.xml",
    "NYT_World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "ReliefWeb_Disaster": "https://reliefweb.int/updates/rss.xml",
    "WHO_Pandemic": "https://www.who.int/feeds/entity/csr/don/en/rss.xml",
}
WAR_KEYWORDS = [
    "war",
    "missile",
    "strike",
    "invasion",
    "military",
    "conflict",
    "nuclear",
    "attack",
]
PANDEMIC_KEYWORDS = [
    "outbreak",
    "virus",
    "pandemic",
    "epidemic",
    "disease",
    "quarantine",
    "ebola",
    "covid",
    "h5n1",
]
KST = ZoneInfo("Asia/Seoul")
ALERT_STATE_PATH = PROJECT_ROOT / "data" / "runtime" / "crisis_monitor_alert_state.json"
CRISIS_ALERT_WINDOWS = {
    "preopen": ("08:00", "09:30"),
    "noon": ("11:30", "12:30"),
    "postclose": ("15:30", "16:30"),
}


def calculate_severity(title):
    title_lower = title.lower()
    is_war = any(kw in title_lower for kw in WAR_KEYWORDS)
    is_pandemic = any(kw in title_lower for kw in PANDEMIC_KEYWORDS)
    if not (is_war or is_pandemic):
        return None, 0
    category = "WAR" if is_war else "PANDEMIC"
    score = sum(1 for kw in WAR_KEYWORDS + PANDEMIC_KEYWORDS if kw in title_lower)
    return category, min(score, 5)


def is_telegram_send_allowed(now=None):
    """
    텔레그램 브로드캐스트가 허용된 시간인지 확인
    9PM(21:00) ~ 8AM(08:00) 사이는 텔레그램 전송 차단
    """
    current_hour = _coerce_kst(now).hour
    # 21시 이상 또는 8시 미만이면 전송 불가 (9PM ~ 8AM)
    if current_hour >= 21 or current_hour < 8:
        return False
    return True


def _env_bool(name, default=True):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _minute_of_day(value):
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def crisis_alert_slot_for(now):
    now_kst = _coerce_kst(now)
    minute = now_kst.hour * 60 + now_kst.minute
    for slot, (start, end) in CRISIS_ALERT_WINDOWS.items():
        if _minute_of_day(start) <= minute < _minute_of_day(end):
            return slot
    return None


def _coerce_kst(now=None):
    current = now or datetime.now(KST)
    return current.astimezone(KST) if current.tzinfo else current.replace(tzinfo=KST)


def _load_alert_state(path=ALERT_STATE_PATH):
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        log_error(f"위기 경보 throttle 상태 파일 로드 실패: {exc}")
        return {}


def _save_alert_state(state, path=ALERT_STATE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def should_send_crisis_risk_alert(
    now=None, path=ALERT_STATE_PATH, throttle_enabled=None
):
    now_kst = _coerce_kst(now)
    if throttle_enabled is None:
        throttle_enabled = _env_bool(
            "KORSTOCKSCAN_CRISIS_ALERT_SLOT_THROTTLE_ENABLED", True
        )

    if not throttle_enabled:
        if is_telegram_send_allowed(now_kst):
            return True, "legacy_time_allowed", None
        return False, "legacy_quiet_hours", None

    slot = crisis_alert_slot_for(now_kst)
    if slot is None:
        return False, "outside_alert_slot", None

    date_key = now_kst.strftime("%Y-%m-%d")
    state = _load_alert_state(path)
    sent_slots = state.get("sent_slots_by_date", {}).get(date_key, [])
    if slot in sent_slots:
        return False, f"slot_already_sent:{slot}", slot
    return True, f"slot_allowed:{slot}", slot


def mark_crisis_risk_alert_sent(
    now=None, slot=None, risk_count=None, path=ALERT_STATE_PATH
):
    now_kst = _coerce_kst(now)
    slot = slot or crisis_alert_slot_for(now_kst) or "legacy"
    date_key = now_kst.strftime("%Y-%m-%d")
    state = _load_alert_state(path)
    sent_by_date = state.setdefault("sent_slots_by_date", {})
    sent_slots = sent_by_date.setdefault(date_key, [])
    if slot not in sent_slots:
        sent_slots.append(slot)
    state["last_sent"] = {
        "sent_at": now_kst.isoformat(timespec="seconds"),
        "slot": slot,
        "risk_count": risk_count,
    }
    _save_alert_state(state, path)


def run_crisis_monitor(db_manager=None, event_bus=None):
    db_manager = db_manager or DBManager()
    event_bus = event_bus or EventBus()
    now = datetime.now(KST)
    print(f"🌍 [{now.strftime('%Y-%m-%d %H:%M:%S')}] 글로벌 위기 감지 스캐너 가동...")

    new_severe_alerts = []

    # 1. RSS 스캔 및 DB 저장 (DBManager 위임)
    for source_name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                category, severity = calculate_severity(entry.title)
                if severity > 0:
                    alert_data = {
                        "alert_time": now,  # 💡 PostgreSQL timestamp 형식 호환
                        "category": category,
                        "source": source_name,
                        "title": entry.title,
                        "link": entry.link,
                        "severity_score": severity,
                    }
                    if db_manager.save_macro_alert(alert_data):
                        if severity >= 2:
                            new_severe_alerts.append(
                                {
                                    "category": category,
                                    "severity": severity,
                                    "en_title": entry.title,
                                }
                            )
        except Exception as e:
            log_error(f"RSS 스크래핑 에러 ({source_name}): {e}")
        time.sleep(1)

    # 2. 리스크 평가 및 알림 (DBManager 위임)
    if new_severe_alerts:
        risk_count = db_manager.get_recent_risk_count(hours=12, min_severity=2)

        if risk_count >= 4:
            # 💡 [우아한 개선] 번역 및 메시지 조립 로직
            translator = GoogleTranslator(source="auto", target="ko")
            msg = f"🚨 *[시스템 경보: 매매 리스크 감지]*\n최근 12시간 내 심각한 위기 경보가 **{risk_count}건** 누적되었습니다.\n\n"

            for alert in new_severe_alerts[:3]:
                try:
                    ko_title = translator.translate(alert["en_title"])
                except:
                    ko_title = alert["en_title"]
                msg += f"▪️ **[{alert['category']}]** {ko_title}\n"

            # ⏰ 수집은 계속하되 Telegram 경보는 장전/정오/장후 슬롯당 1회로 제한한다.
            allowed, throttle_reason, alert_slot = should_send_crisis_risk_alert(now)
            if allowed:
                event_bus.publish(
                    "TELEGRAM_BROADCAST",
                    {
                        "message": msg,
                        "audience": "ADMIN_ONLY",
                        "parse_mode": "Markdown",
                    },
                )
                mark_crisis_risk_alert_sent(now, alert_slot, risk_count)
                print(
                    f"📢 위기 경보 브로드캐스트 완료 (slot={alert_slot or 'legacy'}, 누적: {risk_count}건)"
                )
            else:
                print(f"⏸️ 위기 경보 텔레그램 전송 차단 ({throttle_reason})")


if __name__ == "__main__":
    run_crisis_monitor()
