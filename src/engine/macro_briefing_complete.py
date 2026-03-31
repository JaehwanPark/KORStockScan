import traceback
import json
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from itertools import cycle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from google import genai
from google.genai import types

from src.utils.constants import CONFIG_PATH, DEV_PATH, TRADING_RULES
from src.utils.logger import log_error


DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = "Mozilla/5.0 (MacroBriefingBot/2.0)"
GEMINI_MARKET_KEYS = ["sp500", "nasdaq", "vix", "us10y", "brent"]

MACRO_GEMINI_SYSTEM_PROMPT = """
너는 한국 주식시장을 위한 오버나이트 매크로 데이터 수집기다.
역할은 "요약"이 아니라 "구조화 JSON 데이터 공급"이다.

반드시 아래 규칙을 지켜라.
1. 출력은 JSON 객체 하나만 반환한다. 마크다운, 설명, 코드블록 금지.
2. 각 시장 항목(sp500, nasdaq, vix, us10y, brent)은 객체로 반환한다.
3. 각 항목에는 가능하면 아래 필드를 채운다.
   - name
   - value
   - prev_value
   - change
   - change_pct
   - as_of
   - source
4. as_of 와 bundle_as_of 는 반드시 ISO 8601 UTC 형식으로 쓴다.
   예: 2026-03-30T10:45:00Z
   ET, EDT, EST, KST 같은 약식 시간대 표기는 금지한다.
5. 모르면 추정하지 말고 null 또는 빈 문자열로 둔다.
6. headlines 는 최대 5개로 제한한다.
7. headlines 각 원소는 아래 필드를 가진다.
   - title
   - source
   - published_at
   - url
8. headlines 의 published_at 도 ISO 8601 UTC 형식으로 작성한다.
9. 미국 증시/금리/변동성/원유는 "가장 최근의 신뢰 가능한 마감 또는 최신 확인 시점" 기준으로 쓴다.
10. bundle_as_of 는 네가 이 JSON을 확정한 기준 시각이다.

반드시 아래 형태를 따른다.
{
  "bundle_as_of": "...",
  "sp500": {"name": "S&P500", "value": 0, "prev_value": 0, "change": 0, "change_pct": 0, "as_of": "...", "source": "..." },
  "nasdaq": {"name": "NASDAQ", "value": 0, "prev_value": 0, "change": 0, "change_pct": 0, "as_of": "...", "source": "..." },
  "vix": {"name": "VIX", "value": 0, "prev_value": 0, "change": 0, "change_pct": 0, "as_of": "...", "source": "..." },
  "us10y": {"name": "US10Y", "value": 0, "prev_value": 0, "change": 0, "change_pct": 0, "as_of": "...", "source": "..." },
  "brent": {"name": "BRENT", "value": 0, "prev_value": 0, "change": 0, "change_pct": 0, "as_of": "...", "source": "..." },
  "headlines": [
    {"title": "...", "source": "...", "published_at": "...", "url": "..."}
  ],
  "notes": ["..."]
}
""".strip()


def _load_system_config() -> Dict[str, Any]:
    """프로젝트 공통 규약에 맞춘 설정 로더"""
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}


def _extract_gemini_api_keys(config: Dict[str, Any]) -> List[str]:
    keys: List[str] = []

    raw = config.get("GEMINI_API_KEYS")
    if isinstance(raw, list):
        keys.extend([str(x).strip() for x in raw if str(x).strip()])
    elif isinstance(raw, str) and raw.strip():
        keys.append(raw.strip())

    legacy_names = ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(2, 11)]
    for name in legacy_names:
        v = config.get(name)
        if isinstance(v, str) and v.strip():
            keys.append(v.strip())

    deduped: List[str] = []
    seen = set()
    for key in keys:
        if key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped


@dataclass
class MarketSeriesPoint:
    name: str
    value: Optional[float] = None
    prev_value: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    as_of: Optional[str] = None
    source: Optional[str] = None


@dataclass
class NewsHeadline:
    title: str
    source: str = ""
    published_at: str = ""
    url: str = ""
    score: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class MacroSnapshot:
    created_at: str
    sp500: Optional[MarketSeriesPoint] = None
    nasdaq: Optional[MarketSeriesPoint] = None
    vix: Optional[MarketSeriesPoint] = None
    us10y: Optional[MarketSeriesPoint] = None
    usdkrw: Optional[MarketSeriesPoint] = None
    kr3y: Optional[MarketSeriesPoint] = None
    kr10y: Optional[MarketSeriesPoint] = None
    brent: Optional[MarketSeriesPoint] = None
    headlines: List[NewsHeadline] = field(default_factory=list)
    regime_tag: str = "neutral"
    confidence: int = 50
    notes: List[str] = field(default_factory=list)
    missing_sources: List[str] = field(default_factory=list)


ECOS_SERIES: Dict[str, Dict[str, str]] = {
    "usdkrw": {
        "name": "USD/KRW",
        "stat_code": "731Y001",
        "cycle": "D",
        "item_code": "0000001",
    },
    "kr3y": {
        "name": "KR 3Y",
        "stat_code": "817Y001",
        "cycle": "D",
        "item_code": "010200000",
    },
    "kr10y": {
        "name": "KR 10Y",
        "stat_code": "817Y001",
        "cycle": "D",
        "item_code": "010210000",
    },
}


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v in ("", ".", "-", "null", "None"):
                return None
        return float(v)
    except Exception:
        return None


def _pct_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev in (None, 0):
        return None
    return ((curr - prev) / prev) * 100.0


def _abs_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None:
        return None
    return curr - prev


def _fmt_signed(v: Optional[float], unit: str = "%", digits: int = 2) -> str:
    if v is None:
        return "N/A"
    return f"{v:+.{digits}f}{unit}"


def _clean_time_text(time_text: str, cycle: str) -> str:
    if not time_text:
        return ""
    if cycle == "D" and len(time_text) == 8:
        return f"{time_text[:4]}-{time_text[4:6]}-{time_text[6:8]}"
    return time_text


_TZ_REPLACEMENTS = {
    " ET": "-0500",
    " EDT": "-0400",
    " EST": "-0500",
    " CT": "-0600",
    " CDT": "-0500",
    " CST": "-0600",
    " PT": "-0800",
    " PDT": "-0700",
    " PST": "-0800",
    " KST": "+0900",
    " JST": "+0900",
    " UTC": "+0000",
    " GMT": "+0000",
}


def _normalize_dt_text(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = cleaned.replace(",", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    for src, dst in _TZ_REPLACEMENTS.items():
        if cleaned.endswith(src):
            cleaned = cleaned[: -len(src)] + dst
            break
    return cleaned


def _parse_dt_maybe(text: str) -> Optional[datetime]:
    if not text:
        return None

    cleaned = _normalize_dt_text(text)
    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y%m%d%H%M%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            continue

    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _is_stale(as_of: str, max_age_hours: int) -> bool:
    dt = _parse_dt_maybe(as_of)
    if dt is None:
        return True
    now_utc = datetime.utcnow()
    delta = now_utc - dt
    if delta.total_seconds() < 0:
        if abs(delta.total_seconds()) <= 12 * 3600:
            return False
        return True
    return delta > timedelta(hours=max_age_hours)


class BaseHttpClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self.timeout = timeout


class EcosClient(BaseHttpClient):
    BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"

    def __init__(self, api_key: str, session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT):
        super().__init__(session=session, timeout=timeout)
        self.api_key = api_key

    def get_latest_stat(
        self,
        *,
        stat_code: str,
        cycle: str,
        item_code: str,
        name: str,
        lookback_days: int = 14,
    ) -> MarketSeriesPoint:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=lookback_days)
        start_str, end_str = self._format_date_range(cycle, start_dt, end_dt)

        url = (
            f"{self.BASE_URL}/{self.api_key}/json/kr/1/100/"
            f"{stat_code}/{cycle}/{start_str}/{end_str}/{item_code}"
        )

        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        rows = r.json().get("StatisticSearch", {}).get("row", [])

        rows = sorted(rows, key=lambda x: x.get("TIME", ""), reverse=True)
        valid_rows: List[Dict[str, Any]] = []
        for row in rows:
            if _safe_float(row.get("DATA_VALUE")) is not None:
                valid_rows.append(row)
            if len(valid_rows) >= 2:
                break

        latest = valid_rows[0] if len(valid_rows) >= 1 else {}
        prev = valid_rows[1] if len(valid_rows) >= 2 else {}
        curr_value = _safe_float(latest.get("DATA_VALUE"))
        prev_value = _safe_float(prev.get("DATA_VALUE"))

        return MarketSeriesPoint(
            name=name,
            value=curr_value,
            prev_value=prev_value,
            change=_abs_change(curr_value, prev_value),
            change_pct=_pct_change(curr_value, prev_value),
            as_of=_clean_time_text(latest.get("TIME", ""), cycle),
            source="ECOS",
        )

    @staticmethod
    def _format_date_range(cycle: str, start_dt: datetime, end_dt: datetime) -> Tuple[str, str]:
        if cycle == "D":
            return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")
        if cycle == "M":
            return start_dt.strftime("%Y%m"), end_dt.strftime("%Y%m")
        if cycle == "A":
            return start_dt.strftime("%Y"), end_dt.strftime("%Y")
        return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")


class MacroSignalEngine:
    def score_snapshot(self, snap: MacroSnapshot) -> Tuple[str, int, List[str]]:
        score = 0
        notes: List[str] = []

        if snap.nasdaq and snap.nasdaq.change_pct is not None:
            if snap.nasdaq.change_pct >= 1.0:
                score += 2
                notes.append("나스닥 강세")
            elif snap.nasdaq.change_pct <= -1.0:
                score -= 2
                notes.append("나스닥 약세")

        if snap.sp500 and snap.sp500.change_pct is not None:
            if snap.sp500.change_pct >= 0.7:
                score += 1
                notes.append("S&P500 우호적")
            elif snap.sp500.change_pct <= -0.7:
                score -= 1
                notes.append("S&P500 부담")

        if snap.vix and snap.vix.change_pct is not None:
            if snap.vix.change_pct >= 8.0:
                score -= 2
                notes.append("VIX 급등")
            elif snap.vix.change_pct <= -5.0:
                score += 1
                notes.append("VIX 안정")

        if snap.us10y and snap.us10y.change is not None:
            if snap.us10y.change >= 0.07:
                score -= 1
                notes.append("미 10년물 금리 상승")
            elif snap.us10y.change <= -0.07:
                score += 1
                notes.append("미 10년물 금리 하락")

        if snap.usdkrw and snap.usdkrw.change_pct is not None:
            if snap.usdkrw.change_pct >= 0.5:
                score -= 2
                notes.append("원화 약세")
            elif snap.usdkrw.change_pct <= -0.5:
                score += 1
                notes.append("원화 강세")

        if snap.brent and snap.brent.change_pct is not None:
            if snap.brent.change_pct >= 2.0:
                score -= 1
                notes.append("유가 급등")
            elif snap.brent.change_pct <= -2.0:
                score += 1
                notes.append("유가 안정")

        geo_risk_words = ["iran", "israel", "war", "strike", "sanction", "tariff", "middle east"]
        for h in snap.headlines[:5]:
            title_lower = h.title.lower()
            if any(word in title_lower for word in geo_risk_words):
                score -= 1
                notes.append("지정학/정책 헤드라인 리스크")
                break

        confidence = min(95, max(30, 50 + score * 10))
        if score >= 2:
            regime = "risk_on"
        elif score <= -2:
            regime = "risk_off"
        else:
            regime = "neutral"

        return regime, confidence, notes


class MacroBriefingBuilder:
    def __init__(self, config: Optional[Dict[str, Any]] = None, session: Optional[requests.Session] = None):
        self.config = config or _load_system_config()
        self.session = session or requests.Session()
        self.signal_engine = MacroSignalEngine()

        ecos_key = self.config.get("ECOS_API_KEY", "")
        self.ecos: Optional[EcosClient] = EcosClient(ecos_key, session=self.session) if ecos_key else None

        self.market_max_age_hours = int(self.config.get("MACRO_GEMINI_MARKET_MAX_AGE_HOURS", 96) or 96)
        self.headline_max_age_hours = int(self.config.get("MACRO_GEMINI_HEADLINE_MAX_AGE_HOURS", 36) or 36)
        self.cache_path = self._resolve_cache_path()
        self.current_model_name = str("gemini-pro-latest")

        api_keys = _extract_gemini_api_keys(self.config)
        if isinstance(api_keys, str):
            api_keys = [api_keys]

        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys) if self.api_keys else None
        self.client = None
        self.current_key = ""
        self.current_api_key_index = 0

        self.lock = threading.Lock()
        self.last_call_time = 0.0
        self.min_interval = getattr(TRADING_RULES, "GEMINI_ENGINE_MIN_INTERVAL", 0.5)
        self.consecutive_failures = 0
        self.ai_disabled = False
        self.max_consecutive_failures = getattr(TRADING_RULES, "AI_MAX_CONSECUTIVE_FAILURES", 5)

        if self.api_keys:
            self._rotate_client()

    def _resolve_cache_path(self) -> Path:
        base_dir = CONFIG_PATH.parent if CONFIG_PATH.parent.exists() else DEV_PATH.parent
        return base_dir / "macro_gemini_cache.json"

    def _rotate_client(self):
        if not self.key_cycle:
            return
        self.current_key = next(self.key_cycle)
        self.client = genai.Client(api_key=self.current_key)
        try:
            self.current_api_key_index = self.api_keys.index(self.current_key)
        except ValueError:
            self.current_api_key_index = 0

    def _call_gemini_safe(
        self,
        prompt,
        user_input,
        require_json=True,
        context_name="Unknown",
        model_override=None,
        extra_config=None,
    ):
        """Gemini 호출 + JSON 파싱을 최대한 안전하게 처리"""
        if not self.api_keys or not self.client:
            raise RuntimeError("GEMINI_API_KEY 계열 설정이 없습니다.")

        contents = [prompt, user_input] if prompt else [user_input]

        config_kwargs = {}
        if require_json:
            config_kwargs["response_mime_type"] = "application/json"
        if extra_config:
            config_kwargs.update(extra_config)

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        target_model = model_override if model_override else self.current_model_name
        last_error = ""

        max_attempts = max(len(self.api_keys), 1) * 2

        for attempt in range(max_attempts):
            try:
                elapsed = time.time() - self.last_call_time
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)

                response = self.client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=config,
                )

                raw_text = self._extract_response_text(response).strip()
                self.last_call_time = time.time()

                if require_json:
                    if not raw_text:
                        raise ValueError("Gemini 응답 텍스트가 비어 있음")

                    # 1차: 응답 전체가 JSON이라고 가정
                    try:
                        parsed = json.loads(raw_text)
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass

                    # 2차: 혹시 앞뒤에 설명이 섞였으면 JSON 블록만 추출
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        clean_json = match.group()
                        parsed = json.loads(clean_json)
                        if isinstance(parsed, dict):
                            return parsed

                    raise ValueError(f"JSON 형식을 찾을 수 없음: {raw_text[:500]}...")

                return raw_text

            except Exception as e:
                last_error = str(e).lower()

                retriable_tokens = [
                    "429", "quota", "503", "500", "502", "504",
                    "unavailable", "high demand", "too_many_requests",
                    "read timed out", "timed out", "timeout",
                    "deadline exceeded", "connection aborted", "connection reset",
                ]

                if any(token in last_error for token in retriable_tokens):
                    old_key = self.current_key[-5:] if self.current_key else "none"
                    if len(self.api_keys) > 1:
                        self._rotate_client()
                    new_key = self.current_key[-5:] if self.current_key else "none"

                    warn_msg = (
                        f"⚠️ [Macro Gemini 재시도] {context_name} | "
                        f"{old_key} -> {new_key} ({attempt + 1}/{max_attempts}) | {e}"
                    )
                    log_error(warn_msg)
                    time.sleep(min(0.8 + attempt * 0.4, 3.0))
                    continue

                raise RuntimeError(f"API 응답/파싱 실패: {e}")

        fatal_msg = f"🚨 [Macro Gemini 고갈] 모든 API 키 사용 불가. 마지막 에러: {last_error}"
        log_error(fatal_msg)
        raise RuntimeError(fatal_msg)
    
    @staticmethod
    def _extract_response_text(response: Any) -> str:
        """
        Gemini Python SDK 응답에서 text를 최대한 안전하게 추출한다.
        웹 UI에서는 정상인데 SDK에서는 response.text가 비는 경우를 대비.
        """
        try:
            txt = getattr(response, "text", None)
            if isinstance(txt, str) and txt.strip():
                return txt
        except Exception:
            pass

        chunks: List[str] = []
        try:
            candidates = getattr(response, "candidates", None) or []
            for cand in candidates:
                content = getattr(cand, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    part_text = getattr(part, "text", None)
                    if isinstance(part_text, str) and part_text.strip():
                        chunks.append(part_text)
        except Exception:
            pass

        if chunks:
            return "\n".join(chunks).strip()

        try:
            return str(response)
        except Exception:
            return ""

    @classmethod
    def from_system_config(cls) -> "MacroBriefingBuilder":
        return cls(_load_system_config())

    @classmethod
    def from_json(cls, config_path: str) -> "MacroBriefingBuilder":
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return cls(json.load(f))
        except Exception as e:
            log_error(f"🚨 설정 로드 실패({config_path}): {e}")
            return cls({})

    def _build_macro_user_input(self) -> str:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"""
현재 UTC 시각은 {now_utc} 이다.

이 시각 기준으로 가장 최근에 확인 가능한 신뢰할 수 있는 오버나이트 매크로 데이터를
반드시 Google Search를 사용해 조회하고 JSON 객체 하나만 반환하라.

[수집 대상]
1. S&P500
2. NASDAQ
3. VIX
4. US 10Y Treasury Yield
5. Brent Crude
6. 미국 정치/전쟁/관세/중동/시장 관련 핵심 headline 5개 이내

[엄격 규칙]
- 각 시장 항목의 as_of를 반드시 채워라.
- 개별 as_of가 확실하지 않으면 bundle_as_of와 같은 시각을 넣어라.
- 시간은 반드시 ISO 8601 UTC 형식으로 작성하라.
- ET, EDT, EST, KST 같은 약식 시간대는 절대 쓰지 마라.
- 숫자를 추정하지 마라. 불확실하면 null 로 둬라.
- 최신 웹 검색 결과에 근거하지 않은 값은 쓰지 마라.
- 출력은 JSON 객체 하나만 반환하라.
""".strip()

    def _load_cached_bundle(self) -> Optional[Dict[str, Any]]:
        try:
            if not self.cache_path.exists():
                log_error(f"[MACRO CACHE LOAD] no file: {self.cache_path}")
                return None

            with open(self.cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            if isinstance(payload, dict):
                log_error(
                    f"[MACRO CACHE LOAD] loaded from {self.cache_path}, "
                    f"bundle_as_of={payload.get('bundle_as_of')}"
                )
                return payload

            log_error(f"[MACRO CACHE LOAD] invalid payload type: {type(payload).__name__}")
            return None

        except Exception as e:
            log_error(f"macro cache load failed: {e}")
            return None


    def _save_cached_bundle(self, bundle: Dict[str, Any]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)

            log_error(
                f"[MACRO CACHE SAVE] saved to {self.cache_path}, "
                f"bundle_as_of={bundle.get('bundle_as_of') if isinstance(bundle, dict) else None}"
            )
        except Exception as e:
            log_error(f"macro cache save failed: {e}")

    def _fetch_live_bundle(self) -> Dict[str, Any]:
        return self._call_gemini_safe(
            MACRO_GEMINI_SYSTEM_PROMPT,
            self._build_macro_user_input(),
            require_json=True,
            context_name="macro_briefing",
            model_override=self.current_model_name,
            extra_config={
                "tools": [
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ]
            },
        )

    def _is_bundle_stale(self, bundle: Dict[str, Any]) -> bool:
        if not isinstance(bundle, dict):
            return True

        bundle_as_of = str(bundle.get("bundle_as_of", "") or bundle.get("as_of", "") or "").strip()
        if not bundle_as_of:
            return True

        return _is_stale(bundle_as_of, self.market_max_age_hours)

    def _to_market_series_point(
        self,
        key: str,
        raw: Any,
        *,
        bundle_as_of: str = "",
        source_label: str = "GEMINI",
    ) -> Optional[MarketSeriesPoint]:
        if not isinstance(raw, dict):
            return None

        as_of = str(raw.get("as_of", "") or "").strip() or str(bundle_as_of or "").strip()
        if not as_of or _is_stale(as_of, self.market_max_age_hours):
            return None

        value = _safe_float(raw.get("value"))
        prev_value = _safe_float(raw.get("prev_value"))
        change = _safe_float(raw.get("change"))
        change_pct = _safe_float(raw.get("change_pct"))

        if change is None and value is not None and prev_value is not None:
            change = _abs_change(value, prev_value)
        if change_pct is None and value is not None and prev_value not in (None, 0):
            change_pct = _pct_change(value, prev_value)

        if value is None and change is None and change_pct is None:
            return None

        name_map = {
            "sp500": "S&P500",
            "nasdaq": "NASDAQ",
            "vix": "VIX",
            "us10y": "US10Y",
            "brent": "BRENT",
        }

        return MarketSeriesPoint(
            name=str(raw.get("name", name_map.get(key, key.upper())) or name_map.get(key, key.upper())),
            value=value,
            prev_value=prev_value,
            change=change,
            change_pct=change_pct,
            as_of=as_of,
            source=str(raw.get("source", source_label) or source_label),
        )

    def _to_headlines(self, raw_headlines: Any, *, bundle_as_of: str = "", source_label: str = "GEMINI") -> List[NewsHeadline]:
        results: List[NewsHeadline] = []
        if not isinstance(raw_headlines, list):
            return results

        for row in raw_headlines[:10]:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title", "") or "").strip()
            if not title:
                continue

            published_at = str(row.get("published_at", "") or "").strip() or str(bundle_as_of or "").strip()
            if published_at and _is_stale(published_at, self.headline_max_age_hours):
                continue

            results.append(
                NewsHeadline(
                    title=title,
                    source=str(row.get("source", source_label) or source_label),
                    published_at=published_at,
                    url=str(row.get("url", "") or "").strip(),
                )
            )
            if len(results) >= 5:
                break

        return self._dedupe_headlines(results)

    def _apply_gemini_bundle(self, snap: MacroSnapshot, bundle: Dict[str, Any], *, source_label: str) -> None:
        bundle_as_of = str(bundle.get("bundle_as_of", "") or bundle.get("as_of", "") or "").strip()

        for key in GEMINI_MARKET_KEYS:
            point = self._to_market_series_point(
                key,
                bundle.get(key),
                bundle_as_of=bundle_as_of,
                source_label=source_label,
            )
            if point is not None:
                setattr(snap, key, point)
            else:
                snap.missing_sources.append(f"{source_label}:{key}:stale_or_missing")

        headlines = self._to_headlines(
            bundle.get("headlines", []),
            bundle_as_of=bundle_as_of,
            source_label=source_label,
        )
        if headlines:
            snap.headlines = headlines
        else:
            snap.missing_sources.append(f"{source_label}:headlines:stale_or_missing")

        bundle_notes = bundle.get("notes")
        if isinstance(bundle_notes, list):
            for note in bundle_notes[:3]:
                note_text = str(note or "").strip()
                if note_text:
                    snap.notes.append(note_text)

        if bundle_as_of:
            snap.notes.append(f"{source_label} bundle_as_of={bundle_as_of}")

    def collect_snapshot(self) -> MacroSnapshot:
        snap = MacroSnapshot(created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if self.ecos:
            for key, meta in ECOS_SERIES.items():
                try:
                    setattr(
                        snap,
                        key,
                        self.ecos.get_latest_stat(
                            stat_code=meta["stat_code"],
                            cycle=meta["cycle"],
                            item_code=meta["item_code"],
                            name=meta["name"],
                        ),
                    )
                except Exception as e:
                    snap.missing_sources.append(f"ECOS:{key}:{e}")
                    log_error(f"ECOS series {key} failed: {e}")
        else:
            snap.missing_sources.append("ECOS_API_KEY 없음")
            log_error("ECOS_API_KEY missing")

        live_bundle: Optional[Dict[str, Any]] = None

        if self.api_keys:
            try:
                live_bundle = self._fetch_live_bundle()
                log_error(f"[MACRO] live_bundle fetched: type={type(live_bundle).__name__}")

                if isinstance(live_bundle, dict):
                    bundle_as_of = live_bundle.get('bundle_as_of')
                    log_error(
                        f"[MACRO] LIVE bundle_as_of={bundle_as_of} "
                        f"path={self.cache_path}"
                    )

                    if self._is_bundle_stale(live_bundle):
                        snap.missing_sources.append(f"GEMINI:bundle:stale:{bundle_as_of}")
                        snap.notes.append(f"Gemini live bundle stale 폐기: {bundle_as_of}")
                        log_error(f"[MACRO] LIVE bundle rejected as stale: {bundle_as_of}")
                    else:
                        self._save_cached_bundle(live_bundle)
                        log_error("[MACRO] applying LIVE bundle with source_label=GEMINI")
                        self._apply_gemini_bundle(snap, live_bundle, source_label="GEMINI")
                        self.consecutive_failures = 0
                else:
                    snap.missing_sources.append("GEMINI:live:not_dict")
                    snap.notes.append("live Gemini 응답이 dict 아님")
                    log_error("[MACRO] live_bundle is not dict, cache fallback not used")
            except Exception as e:
                self.consecutive_failures += 1
                snap.missing_sources.append(f"GEMINI:live:{e}")
                log_error(f"Gemini 데이터 수집 실패: {e}")

                cached_bundle = self._load_cached_bundle()
                log_error(
                    f"[MACRO] CACHE fallback path={self.cache_path}, "
                    f"exists={isinstance(cached_bundle, dict)}"
                )

                if isinstance(cached_bundle, dict) and not self._is_bundle_stale(cached_bundle):
                    log_error(
                        f"[MACRO] applying CACHE bundle bundle_as_of={cached_bundle.get('bundle_as_of')} "
                        f"with source_label=GEMINI_CACHE"
                    )
                    self._apply_gemini_bundle(snap, cached_bundle, source_label="GEMINI_CACHE")
                    snap.notes.append("live Gemini 실패로 cache fallback 사용")
                else:
                    snap.notes.append("live Gemini 실패 및 사용 가능한 cache 없음")
                    log_error("[MACRO] cache fallback unavailable or stale")

        else:
            snap.missing_sources.append("GEMINI_API_KEY 없음")
            log_error("GEMINI_API_KEY missing")

        snap.regime_tag, snap.confidence, scored_notes = self.signal_engine.score_snapshot(snap)
        if scored_notes:
            snap.notes.extend(scored_notes)

        log_error(
            f"[MACRO] collect_snapshot done | regime={snap.regime_tag} | confidence={snap.confidence} | "
            f"missing_sources={snap.missing_sources}"
        )
        return snap

    def build_macro_text(self, snap: MacroSnapshot, include_debug: bool = False) -> str:
        lines: List[str] = []

        us_parts: List[str] = []
        if snap.sp500 and snap.sp500.change_pct is not None:
            us_parts.append(f"S&P500 {_fmt_signed(snap.sp500.change_pct)}")
        if snap.nasdaq and snap.nasdaq.change_pct is not None:
            us_parts.append(f"Nasdaq {_fmt_signed(snap.nasdaq.change_pct)}")
        if us_parts:
            lines.append("- 미국장: " + ", ".join(us_parts))

        rv_parts: List[str] = []
        if snap.us10y and snap.us10y.change is not None:
            rv_parts.append(f"미 10년물 {_fmt_signed(snap.us10y.change, unit='', digits=2)}")
        if snap.vix and snap.vix.change_pct is not None:
            rv_parts.append(f"VIX {_fmt_signed(snap.vix.change_pct)}")
        if rv_parts:
            lines.append("- 금리/변동성: " + ", ".join(rv_parts))

        fx_parts: List[str] = []
        if snap.usdkrw and snap.usdkrw.change_pct is not None:
            fx_parts.append(f"달러/원 {_fmt_signed(snap.usdkrw.change_pct)}")
        if snap.brent and snap.brent.change_pct is not None:
            fx_parts.append(f"Brent {_fmt_signed(snap.brent.change_pct)}")
        if fx_parts:
            lines.append("- 환율/원자재: " + ", ".join(fx_parts))

        kr_parts: List[str] = []
        if snap.kr3y and snap.kr3y.value is not None:
            kr_parts.append(f"국고3년 {snap.kr3y.value:.2f}%")
        if snap.kr10y and snap.kr10y.value is not None:
            kr_parts.append(f"국고10년 {snap.kr10y.value:.2f}%")
        if kr_parts:
            lines.append("- 국내금리: " + ", ".join(kr_parts))

        if snap.headlines:
            titles = [h.title for h in snap.headlines[:2]]
            lines.append("- 이벤트: " + " / ".join(titles))

        has_any_macro = any([
            snap.sp500 is not None,
            snap.nasdaq is not None,
            snap.vix is not None,
            snap.us10y is not None,
            snap.usdkrw is not None,
            snap.kr3y is not None,
            snap.kr10y is not None,
            snap.brent is not None,
            bool(snap.headlines),
        ])

        if has_any_macro:
            lines.append(f"- 해석: {self._make_kospi_interpretation(snap)}")
        else:
            lines.append("- 해석: 유효한 오버나이트 매크로 수집값이 없어 보수적으로 중립 처리")

        if snap.notes:
            note_preview = [n for n in snap.notes if n][:3]
            if note_preview:
                lines.append("- 참고: " + " / ".join(note_preview))

        if include_debug and snap.missing_sources:
            lines.append("- 디버그: " + " | ".join(snap.missing_sources[:8]))

        text = "\n".join([x for x in lines if str(x).strip()]).strip()
        if not text:
            return "- 해석: 오버나이트 매크로 수집 결과가 비어 있음"
        return text

    def build_macro_context(self, include_debug: bool = False) -> Tuple[MacroSnapshot, str]:
        snap = self.collect_snapshot()
        return snap, self.build_macro_text(snap, include_debug=include_debug)

    @staticmethod
    def _dedupe_headlines(headlines: List[NewsHeadline]) -> List[NewsHeadline]:
        seen = set()
        result: List[NewsHeadline] = []
        for h in headlines:
            key = h.title.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(h)
        return result

    @staticmethod
    def _make_kospi_interpretation(snap: MacroSnapshot) -> str:
        if snap.regime_tag == "risk_on":
            return "외국인 수급과 대형주에는 우호적. 반도체/성장주 시초 강세 확인 가능"
        if snap.regime_tag == "risk_off":
            return "외국인 수급에는 다소 불리. 시초 추격보다 변동성 소화 확인이 우선"
        return "방향성은 중립. 강한 업종만 압축 대응하는 편이 유리"


def build_scanner_data_input(total_count: int, survived_count: int, stats_text: str, macro_text: str = "") -> str:
    cleaned_macro = str(macro_text or "").strip()
    macro_block = cleaned_macro if cleaned_macro else "- 오버나이트 매크로 데이터 수집 실패 또는 빈 결과"

    return (
        f"[오버나이트 매크로]\n{macro_block}\n\n"
        f"[스캐너 통계 데이터]\n"
        f"총 탐색: {total_count}개\n"
        f"최종 생존: {survived_count}개\n\n"
        f"[상세 탈락 사유]\n{stats_text}"
    )
