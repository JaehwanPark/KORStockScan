import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.utils.constants import CONFIG_PATH, DEV_PATH
from src.utils.logger import log_error

DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = "Mozilla/5.0 (MacroBriefingBot/1.0)"


def _load_system_config() -> Dict[str, Any]:
    """프로젝트 공통 규약에 맞춘 설정 로더"""
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}


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


FRED_SERIES: Dict[str, Tuple[str, str]] = {
    "sp500": ("SP500", "S&P500"),
    "nasdaq": ("NASDAQCOM", "NASDAQ"),
    "vix": ("VIXCLS", "VIX"),
    "us10y": ("DGS10", "US10Y"),
    "brent": ("DCOILBRENTEU", "BRENT"),
}

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
            if v in ("", ".", "-"):
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


class BaseHttpClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self.timeout = timeout


class FredClient(BaseHttpClient):
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str, session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT):
        super().__init__(session=session, timeout=timeout)
        self.api_key = api_key

    def get_latest_series_point(self, series_id: str, name: str) -> MarketSeriesPoint:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 10,
        }
        r = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
        r.raise_for_status()
        observations = r.json().get("observations", [])

        valid_rows: List[Dict[str, Any]] = []
        for row in observations:
            if _safe_float(row.get("value")) is not None:
                valid_rows.append(row)
            if len(valid_rows) >= 2:
                break

        latest = valid_rows[0] if len(valid_rows) >= 1 else {}
        prev = valid_rows[1] if len(valid_rows) >= 2 else {}
        curr_value = _safe_float(latest.get("value"))
        prev_value = _safe_float(prev.get("value"))

        return MarketSeriesPoint(
            name=name,
            value=curr_value,
            prev_value=prev_value,
            change=_abs_change(curr_value, prev_value),
            change_pct=_pct_change(curr_value, prev_value),
            as_of=latest.get("date"),
            source="FRED",
        )


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


class GdeltClient(BaseHttpClient):
    DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search_headlines(self, query: str, max_records: int = 10) -> List[NewsHeadline]:
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": max_records,
            "sort": "DateDesc",
        }
        r = self.session.get(self.DOC_API, params=params, timeout=self.timeout)
        r.raise_for_status()
        articles = r.json().get("articles", [])

        results: List[NewsHeadline] = []
        for article in articles:
            title = (article.get("title") or "").strip()
            if not title:
                continue
            results.append(
                NewsHeadline(
                    title=title,
                    source=article.get("domain", "") or article.get("sourcecountry", ""),
                    published_at=article.get("seendate", ""),
                    url=article.get("url", ""),
                )
            )
        return results


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

        fred_key = self.config.get("FRED_API_KEY", "")
        ecos_key = self.config.get("ECOS_API_KEY", "")

        self.fred: Optional[FredClient] = FredClient(fred_key, session=self.session) if fred_key else None
        self.ecos: Optional[EcosClient] = EcosClient(ecos_key, session=self.session) if ecos_key else None
        self.gdelt = GdeltClient(session=self.session)

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

    def collect_snapshot(self) -> MacroSnapshot:
        snap = MacroSnapshot(created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if self.fred:
            for key, (series_id, name) in FRED_SERIES.items():
                try:
                    setattr(snap, key, self.fred.get_latest_series_point(series_id, name))
                except Exception as e:
                    snap.missing_sources.append(f"FRED:{key}:{e}")
        else:
            snap.missing_sources.append("FRED_API_KEY 없음")

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
        else:
            snap.missing_sources.append("ECOS_API_KEY 없음")

        queries = [
            '(iran OR israel OR "middle east") AND (oil OR strike OR conflict)',
            '(us politics OR tariff OR congress OR trump OR biden) AND (market OR stocks OR economy)',
        ]
        headlines: List[NewsHeadline] = []
        for query in queries:
            try:
                headlines.extend(self.gdelt.search_headlines(query, max_records=5))
            except Exception as e:
                snap.missing_sources.append(f"GDELT:{e}")

        snap.headlines = self._dedupe_headlines(headlines)[:5]
        snap.regime_tag, snap.confidence, snap.notes = self.signal_engine.score_snapshot(snap)
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

        lines.append(f"- 해석: {self._make_kospi_interpretation(snap)}")

        if include_debug and snap.missing_sources:
            lines.append("- 디버그: " + " | ".join(snap.missing_sources[:3]))

        return "\n".join(lines)

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


# 현재 ai_engine.py 구조를 크게 흔들지 않기 위한 helper
# 프롬프트 정의는 ai_engine.py 쪽에 두고, 입력 포맷 helper만 여기 둡니다.
def build_scanner_data_input(total_count: int, survived_count: int, stats_text: str, macro_text: str = "") -> str:
    macro_block = macro_text.strip() if macro_text else "오버나이트 매크로 데이터 없음"
    return (
        f"[오버나이트 매크로]\n{macro_block}\n\n"
        f"[스캐너 통계 데이터]\n"
        f"총 탐색: {total_count}개\n"
        f"최종 생존: {survived_count}개\n\n"
        f"[상세 탈락 사유]\n{stats_text}"
    )
