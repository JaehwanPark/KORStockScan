# src/engine/ai_engine_deepseek.py
"""
DeepSeek API 기반 Sniper Engine (DeepSeekSniperEngine)
- OpenAI 호환 REST 엔드포인트 사용 (openai SDK)
- GeminiSniperEngine(ai_engine.py)과 100% 동일한 퍼블릭 인터페이스
- Google Search 도구 미지원 (use_google_search 무시)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import threading
import json
import re
import hashlib
import random
from datetime import datetime, timezone
from itertools import cycle
from openai import OpenAI, RateLimitError

from src.engine.scalping_feature_packet import (
    build_scalping_feature_audit_fields,
    extract_scalping_feature_packet,
)
from src.utils.logger import log_error
from src.utils.constants import TRADING_RULES
from src.engine.macro_briefing_complete import build_scanner_data_input
from src.engine.ai_engine import (
    SCALPING_SYSTEM_PROMPT,
    SCALPING_WATCHING_SYSTEM_PROMPT,
    SCALPING_HOLDING_SYSTEM_PROMPT,
    SCALPING_EXIT_SYSTEM_PROMPT,
    SCALPING_SYSTEM_PROMPT_75_CANARY,
    SCALPING_BUY_RECOVERY_CANARY_PROMPT,
    SWING_SYSTEM_PROMPT,
    CONDITION_ENTRY_PROMPT,
    CONDITION_EXIT_PROMPT,
    ENHANCED_MARKET_ANALYSIS_PROMPT,
    REALTIME_ANALYSIS_PROMPT_SCALP,
    REALTIME_ANALYSIS_PROMPT_SWING,
    REALTIME_ANALYSIS_PROMPT_DUAL,
    SCALPING_OVERNIGHT_DECISION_PROMPT,
    EOD_TOMORROW_LEADER_PROMPT,
    EOD_TOMORROW_LEADER_JSON_PROMPT,
)


class DeepSeekSniperEngine:
    """
    DeepSeek API 기반 스나이퍼 엔진.
    GeminiSniperEngine(ai_engine.py)과 동일한 퍼블릭 인터페이스를 제공한다.
    내부적으로 OpenAI 호환 REST API(api.deepseek.com)를 호출한다.
    Google Search 도구는 지원하지 않는다.
    """

    def __init__(self, api_keys, announce_startup=True):
        if isinstance(api_keys, str):
            api_keys = [api_keys]

        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys)
        self._rotate_client()

        # 모델 티어: DeepSeek 모델명 (constants.py 오버라이드 가능)
        self.model_tier1_fast = getattr(
            TRADING_RULES, 'DEEPSEEK_MODEL_TIER1', 'deepseek-v4-flash'
        )
        self.model_tier2_balanced = getattr(
            TRADING_RULES, 'DEEPSEEK_MODEL_TIER2', 'deepseek-v4-flash'
        )
        self.model_tier3_deep = getattr(
            TRADING_RULES, 'DEEPSEEK_MODEL_TIER3', 'deepseek-v4-Pro'
        )
        self.current_model_name = self.model_tier1_fast

        self.lock = threading.Lock()
        self.api_call_lock = threading.Lock()
        self.last_call_time = 0.0
        self.min_interval = getattr(TRADING_RULES, 'DEEPSEEK_ENGINE_MIN_INTERVAL', 0.5)
        self.consecutive_failures = 0
        self.ai_disabled = False
        self.max_consecutive_failures = getattr(TRADING_RULES, 'AI_MAX_CONSECUTIVE_FAILURES', 5)
        self.current_api_key_index = 0

        self.cache_lock = threading.RLock()
        self.analysis_cache_ttl = getattr(TRADING_RULES, 'AI_ANALYZE_RESULT_CACHE_TTL_SEC', 8.0)
        self.holding_analysis_cache_ttl = getattr(
            TRADING_RULES,
            'AI_HOLDING_RESULT_CACHE_TTL_SEC',
            max(float(self.analysis_cache_ttl or 0.0), 30.0),
        )
        self.gatekeeper_cache_ttl = getattr(TRADING_RULES, 'AI_GATEKEEPER_RESULT_CACHE_TTL_SEC', 12.0)
        self._analysis_cache = {}
        self._gatekeeper_cache = {}

        if announce_startup:
            print(
                f"🧠 [DeepSeek 엔진] {len(self.api_keys)}개 키 로테이션 가동! "
                f"(T1: {self.model_tier1_fast} / T2: {self.model_tier2_balanced} / T3: {self.model_tier3_deep})"
            )

    # ==========================================
    # 클라이언트/키 관리
    # ==========================================

    def _rotate_client(self):
        """DeepSeek API 클라이언트 교체 (OpenAI SDK + base_url 변경)"""
        self.current_key = next(self.key_cycle)
        self.client = OpenAI(
            api_key=self.current_key,
            base_url="https://api.deepseek.com",
        )
        try:
            self.current_api_key_index = self.api_keys.index(self.current_key)
        except ValueError:
            self.current_api_key_index = 0

    def _get_tier1_model(self):
        return getattr(
            self,
            "model_tier1_fast",
            getattr(self, "current_model_name", "deepseek-v4-flash"),
        )

    def _get_tier2_model(self):
        return getattr(self, "model_tier2_balanced", self._get_tier1_model())

    def _get_tier3_model(self):
        return getattr(self, "model_tier3_deep", self._get_tier2_model())

    # ==========================================
    # 캐시 유틸리티 (GeminiSniperEngine 동일 복사)
    # ==========================================

    def _normalize_for_cache(self, value):
        if isinstance(value, dict):
            transient_keys = {
                "captured_at",
                "last_ws_update_ts",
                "time",
                "timestamp",
                "체결시간",
                "tm",
                "cntr_tm",
            }
            return {
                str(k): self._normalize_for_cache(v)
                for k, v in sorted(value.items())
                if str(k) not in transient_keys
            }
        if isinstance(value, list):
            return [self._normalize_for_cache(item) for item in value]
        if isinstance(value, tuple):
            return [self._normalize_for_cache(item) for item in value]
        if isinstance(value, float):
            return round(value, 4)
        if value is None or isinstance(value, (str, int, bool)):
            return value
        return str(value)

    def _build_cache_digest(self, payload):
        normalized = self._normalize_for_cache(payload)
        raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _cache_get(self, cache_name, key):
        cache = getattr(self, cache_name, None)
        lock = getattr(self, "cache_lock", None)
        if cache is None or lock is None:
            return None
        now = time.time()
        with lock:
            entry = cache.get(key)
            if not entry:
                return None
            if float(entry.get("expires_at", 0.0) or 0.0) <= now:
                cache.pop(key, None)
                return None
            value = dict(entry.get("value", {}))
            value["cache_hit"] = True
            value.setdefault("cache_mode", "hit")
            return value

    def _cache_set(self, cache_name, key, value, ttl_sec):
        cache = getattr(self, cache_name, None)
        lock = getattr(self, "cache_lock", None)
        if cache is None or lock is None or ttl_sec <= 0:
            return
        now = time.time()
        payload = dict(value or {})
        payload.pop("cache_hit", None)
        with lock:
            cache[key] = {
                "expires_at": now + float(ttl_sec),
                "value": payload,
            }
            if len(cache) > 512:
                expired = [item_key for item_key, item in cache.items() if float(item.get("expires_at", 0.0) or 0.0) <= now]
                for item_key in expired[:128]:
                    cache.pop(item_key, None)

    def _build_analysis_cache_key(self, target_name, strategy, ws_data, recent_ticks, recent_candles, program_net_qty):
        return self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=strategy,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=program_net_qty,
            cache_profile="default",
        )

    def _build_analysis_cache_key_with_profile(
        self,
        target_name,
        strategy,
        ws_data,
        recent_ticks,
        recent_candles,
        program_net_qty,
        cache_profile,
    ):
        if cache_profile == "holding":
            return self._build_cache_digest(
                {
                    "cache_profile": "holding",
                    "target_name": target_name,
                    "strategy": strategy,
                    "ws_data": self._compact_holding_ws_for_cache(ws_data),
                    "recent_ticks": self._compact_holding_ticks_for_cache(recent_ticks),
                    "recent_candles": self._compact_holding_candles_for_cache(recent_candles),
                    "program_net_qty": self._bucket_int_for_cache(program_net_qty, 1_000),
                }
            )
        return self._build_cache_digest({
            "target_name": target_name,
            "strategy": strategy,
            "ws_data": ws_data,
            "recent_ticks": recent_ticks,
            "recent_candles": recent_candles,
            "program_net_qty": program_net_qty,
        })

    def _bucket_int_for_cache(self, value, bucket):
        try:
            bucket = max(1, int(bucket))
            return int(float(value or 0) // bucket)
        except Exception:
            return 0

    def _bucket_float_for_cache(self, value, step):
        try:
            step = float(step)
            if step <= 0:
                return 0.0
            return round(float(value or 0.0) / step) * step
        except Exception:
            return 0.0

    def _price_bucket_step_for_cache(self, price):
        try:
            price = abs(int(float(price or 0)))
        except Exception:
            price = 0
        if price >= 200_000:
            return 500
        if price >= 50_000:
            return 100
        if price >= 10_000:
            return 50
        if price >= 5_000:
            return 10
        return 5

    def _get_best_levels_for_cache(self, ws_data):
        orderbook = ws_data.get("orderbook") if isinstance(ws_data, dict) else None
        if not isinstance(orderbook, dict):
            return 0, 0
        asks = orderbook.get("asks") or []
        bids = orderbook.get("bids") or []
        best_ask = asks[0].get("price", 0) if asks and isinstance(asks[0], dict) else 0
        best_bid = bids[0].get("price", 0) if bids and isinstance(bids[0], dict) else 0
        return best_ask, best_bid

    def _compact_holding_ws_for_cache(self, ws_data):
        ws_data = ws_data or {}
        best_ask, best_bid = self._get_best_levels_for_cache(ws_data)
        curr_price = ws_data.get("curr", 0) or best_ask or best_bid
        price_bucket = self._price_bucket_step_for_cache(curr_price)
        return {
            "curr": self._bucket_int_for_cache(curr_price, price_bucket),
            "fluctuation": self._bucket_float_for_cache(ws_data.get("fluctuation", 0.0), 0.25),
            "v_pw": self._bucket_float_for_cache(ws_data.get("v_pw", 0.0), 10.0),
            "buy_ratio": self._bucket_float_for_cache(ws_data.get("buy_ratio", 0.0), 4.0),
            "best_ask": self._bucket_int_for_cache(best_ask, price_bucket),
            "best_bid": self._bucket_int_for_cache(best_bid, price_bucket),
            "ask_tot": self._bucket_int_for_cache(ws_data.get("ask_tot", 0), 25_000),
            "bid_tot": self._bucket_int_for_cache(ws_data.get("bid_tot", 0), 25_000),
            "net_bid_depth": self._bucket_int_for_cache(ws_data.get("net_bid_depth", 0), 10_000),
            "net_ask_depth": self._bucket_int_for_cache(ws_data.get("net_ask_depth", 0), 10_000),
            "buy_exec_volume": self._bucket_int_for_cache(ws_data.get("buy_exec_volume", 0), 3_000),
            "sell_exec_volume": self._bucket_int_for_cache(ws_data.get("sell_exec_volume", 0), 3_000),
            "tick_trade_value": self._bucket_int_for_cache(ws_data.get("tick_trade_value", 0), 10_000),
        }

    def _compact_holding_ticks_for_cache(self, recent_ticks):
        ticks = recent_ticks or []
        if not ticks:
            return []
        latest = ticks[-1] if isinstance(ticks[-1], dict) else {}
        buy_volume = 0
        sell_volume = 0
        total_value = 0
        latest_price = 0
        for tick in ticks[-10:]:
            if not isinstance(tick, dict):
                continue
            price = tick.get("price", tick.get("현재가", tick.get("체결가", 0)))
            volume = tick.get("volume", tick.get("qty", tick.get("체결량", 0)))
            direction = str(tick.get("dir", tick.get("side", tick.get("trade_type", ""))) or "").upper()
            try:
                latest_price = int(float(price or latest_price or 0))
            except Exception:
                latest_price = 0
            try:
                volume_int = int(float(volume or 0))
            except Exception:
                volume_int = 0
            total_value += max(0, latest_price) * max(0, volume_int)
            if "SELL" in direction or "매도" in direction:
                sell_volume += volume_int
            else:
                buy_volume += volume_int
        price_bucket = self._price_bucket_step_for_cache(latest_price)
        return [{
            "latest_price": self._bucket_int_for_cache(latest.get("price", latest.get("현재가", latest_price)), price_bucket),
            "buy_volume": self._bucket_int_for_cache(buy_volume, 100),
            "sell_volume": self._bucket_int_for_cache(sell_volume, 100),
            "net_volume": self._bucket_int_for_cache(buy_volume - sell_volume, 100),
            "trade_value": self._bucket_int_for_cache(total_value, 500_000),
        }]

    def _compact_holding_candles_for_cache(self, recent_candles):
        candles = recent_candles or []
        compact = []
        for candle in candles[-3:]:
            if not isinstance(candle, dict):
                continue
            close_price = candle.get("현재가", candle.get("close", candle.get("종가", 0)))
            high_price = candle.get("고가", candle.get("high", close_price))
            low_price = candle.get("저가", candle.get("low", close_price))
            volume = candle.get("거래량", candle.get("volume", 0))
            price_bucket = self._price_bucket_step_for_cache(close_price)
            compact.append(
                {
                    "close": self._bucket_int_for_cache(close_price, price_bucket),
                    "high": self._bucket_int_for_cache(high_price, price_bucket),
                    "low": self._bucket_int_for_cache(low_price, price_bucket),
                    "volume": self._bucket_int_for_cache(volume, 5_000),
                }
            )
        return compact

    def _resolve_analysis_cache_ttl(self, cache_profile):
        if cache_profile == "holding":
            return float(self.holding_analysis_cache_ttl or 0.0)
        return float(self.analysis_cache_ttl or 0.0)

    def _annotate_analysis_result(
        self,
        result,
        *,
        prompt_type,
        prompt_version,
        response_ms,
        parse_ok,
        parse_fail,
        fallback_score_50,
        cache_hit,
        cache_mode,
        result_source,
    ):
        payload = dict(result or {})
        payload["ai_parse_ok"] = bool(parse_ok)
        payload["ai_parse_fail"] = bool(parse_fail)
        payload["ai_fallback_score_50"] = bool(fallback_score_50)
        payload["ai_response_ms"] = max(0, int(response_ms))
        payload["ai_prompt_type"] = str(prompt_type or "-")
        payload["ai_prompt_version"] = str(prompt_version or "-")
        payload["ai_result_source"] = str(result_source or "-")
        payload["cache_hit"] = bool(cache_hit)
        payload["cache_mode"] = str(cache_mode or "miss")
        return payload

    def _resolve_scalping_prompt(self, prompt_profile):
        profile = str(prompt_profile or "shared").strip().lower()
        split_enabled = bool(getattr(TRADING_RULES, "SCALPING_PROMPT_SPLIT_ENABLED", True))
        if not split_enabled:
            return SCALPING_SYSTEM_PROMPT, "scalping_shared", "split_disabled_v1", "shared"

        if profile == "watching":
            return SCALPING_WATCHING_SYSTEM_PROMPT, "scalping_entry", "split_v2", "watching"
        if profile == "holding":
            return SCALPING_HOLDING_SYSTEM_PROMPT, "scalping_holding", "split_v2", "holding"
        if profile == "exit":
            return SCALPING_EXIT_SYSTEM_PROMPT, "scalping_exit", "split_v2", "exit"
        return SCALPING_SYSTEM_PROMPT, "scalping_shared", "split_v2", "shared"

    def _normalize_scalping_action_schema(self, result, *, prompt_type):
        payload = dict(result or {}) if isinstance(result, dict) else {}
        raw_action = str(payload.get("action", "WAIT") or "WAIT").upper().strip()
        reason = str(payload.get("reason", "응답 보정") or "응답 보정").replace("\n", " ").strip()
        try:
            score = int(float(payload.get("score", 50)))
        except Exception:
            score = 50
        score = max(0, min(100, score))

        if prompt_type in {"scalping_holding", "scalping_exit"}:
            allowed = {"HOLD", "TRIM", "EXIT"}
            action_v2 = raw_action if raw_action in allowed else "HOLD"
            compat = {"HOLD": "WAIT", "TRIM": "SELL", "EXIT": "DROP"}
            payload["action_v2"] = action_v2
            payload["action"] = compat.get(action_v2, "WAIT")
            payload["action_schema"] = "holding_exit_v1"
            payload["score"] = score
            payload["reason"] = reason[:120]
            return payload

        allowed = {"BUY", "WAIT", "DROP"}
        action = raw_action if raw_action in allowed else "WAIT"
        payload["action"] = action
        payload["action_v2"] = action
        payload["action_schema"] = "entry_v1"
        payload["score"] = score
        payload["reason"] = reason[:120]
        return payload

    def _remote_buy_risk_flags(self, ws_data, recent_ticks, recent_candles):
        if hasattr(self, "_extract_scalping_features"):
            try:
                features = self._extract_scalping_features(ws_data, recent_ticks, recent_candles)
            except Exception:
                features = {}
        else:
            features = {}
        flags = 0
        if bool(features.get("large_sell_print_detected", False)):
            flags += 1
        if features.get("distance_from_day_high_pct", -99.0) >= -0.35:
            flags += 1
        if features.get("tick_acceleration_ratio", 0.0) < 1.0:
            flags += 1
        if features.get("curr_vs_micro_vwap_bp", 0.0) <= 0:
            flags += 1
        if features.get("top3_depth_ratio", 1.0) >= 1.35:
            flags += 1
        return features, flags

    def _apply_remote_entry_guard(self, result, *, prompt_type, ws_data, recent_ticks, recent_candles):
        if prompt_type not in {"scalping_entry", "scalping_watching", "scalping_shared"}:
            return result
        if str(result.get("action", "WAIT")).upper() != "BUY":
            return result

        features, risk_flags = self._remote_buy_risk_flags(ws_data, recent_ticks, recent_candles)
        if not features:
            return result
        buy_pressure = float(features.get("buy_pressure_10t", 50.0) or 50.0)
        accel = float(features.get("tick_acceleration_ratio", 0.0) or 0.0)
        latest_strength = float(features.get("latest_strength", 0.0) or 0.0)
        has_reclaim = (
            float(features.get("curr_vs_micro_vwap_bp", 0.0) or 0.0) > 0
            or int(features.get("same_price_buy_absorption", 0) or 0) >= 2
        )

        instant_strength_only = (
            buy_pressure >= 70.0
            and accel >= 1.1
            and latest_strength >= 110.0
            and not has_reclaim
        )

        if risk_flags >= 2 or instant_strength_only:
            score = int(result.get("score", 50))
            result["action"] = "WAIT"
            result["score"] = min(score, 74)
            result["reason"] = f"{result.get('reason', '')} | remote_buy_guard(risk={risk_flags})"
        return result

    # ==========================================
    # JSON 파싱 (ai_engine_openai.py 동일 복사)
    # ==========================================

    def _parse_json_response_text(self, raw_text):
        text = str(raw_text or "").strip()
        if not text:
            raise ValueError("DeepSeek 응답 텍스트가 비어 있음")

        candidates = [text]
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            candidates.append(fence_match.group(1).strip())

        block_match = re.search(r"\{.*\}", text, re.DOTALL)
        if block_match:
            candidates.append(block_match.group().strip())

        seen = set()
        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            try:
                parsed = json.loads(normalized)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue

        raise ValueError(f"JSON 형식을 찾을 수 없음: {text[:500]}...")

    # ==========================================
    # 핵심 API 호출기: _call_deepseek_safe
    # ==========================================

    def _compute_retry_sleep(self, attempt, *, live_sensitive):
        if not getattr(TRADING_RULES, "DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED", False):
            return 0.8

        base_sleep = max(0.0, float(getattr(TRADING_RULES, "DEEPSEEK_RETRY_BASE_SLEEP_SEC", 0.4) or 0.4))
        jitter_max = max(0.0, float(getattr(TRADING_RULES, "DEEPSEEK_RETRY_JITTER_MAX_SEC", 0.25) or 0.25))
        live_cap = max(0.0, float(getattr(TRADING_RULES, "DEEPSEEK_RETRY_LIVE_MAX_SLEEP_SEC", 0.8) or 0.8))
        report_cap = max(0.0, float(getattr(TRADING_RULES, "DEEPSEEK_RETRY_REPORT_MAX_SLEEP_SEC", 4.0) or 4.0))
        cap = live_cap if live_sensitive else report_cap
        backoff = base_sleep * (2 ** max(0, int(attempt)))
        return min(cap, backoff + random.uniform(0.0, jitter_max))

    def _call_deepseek_safe(
        self,
        prompt,
        user_input,
        require_json=True,
        context_name="Unknown",
        model_override=None,
        temperature_override=None,
    ):
        """키 로테이션, 예외 처리, 모델 덮어쓰기를 모두 전담하는 중앙 집중식 호출기"""
        with self.api_call_lock:
            messages = []
            if prompt:
                messages.append({"role": "system", "content": prompt})
            messages.append({"role": "user", "content": user_input})

            config_kwargs = {}
            if require_json:
                config_kwargs['response_format'] = {"type": "json_object"}

            target_model = model_override if model_override else self.current_model_name
            target_temp = temperature_override if temperature_override is not None else (0.0 if require_json else 0.7)
            live_sensitive = target_model != self._get_tier3_model()
            last_error = ""

            for attempt in range(len(self.api_keys)):
                try:
                    response = self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        temperature=target_temp,
                        **config_kwargs
                    )

                    # 성공 시 다음 호출을 위해 키 순환 (부하 분산)
                    self._rotate_client()

                    raw_text = str(response.choices[0].message.content or "").strip()
                    if require_json:
                        try:
                            parsed = json.loads(raw_text)
                            if isinstance(parsed, dict):
                                return parsed
                        except Exception:
                            pass
                        return self._parse_json_response_text(raw_text)
                    else:
                        return raw_text

                except RateLimitError as e:
                    last_error = str(e)
                    old_key = self.current_key[-5:]
                    self._rotate_client()

                    warn_msg = f"⚠️ [DeepSeek 한도 초과] {context_name} | {old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})"
                    print(warn_msg)
                    log_error(warn_msg)
                    time.sleep(self._compute_retry_sleep(attempt, live_sensitive=live_sensitive))
                    continue

                except Exception as e:
                    last_error = str(e).lower()
                    if any(x in last_error for x in ["429", "quota", "503", "unavailable", "timeout", "server", "too_many_requests"]):
                        old_key = self.current_key[-5:]
                        self._rotate_client()
                        print(f"⚠️ [DeepSeek 서버 에러] {context_name} | {old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})")
                        time.sleep(self._compute_retry_sleep(attempt, live_sensitive=live_sensitive))
                        continue
                    else:
                        raise RuntimeError(f"DeepSeek API 응답/파싱 실패: {e}")

            fatal_msg = f"🚨 [AI 고갈] 모든 DeepSeek API 키 사용 불가. 마지막 에러: {last_error}"
            log_error(fatal_msg)
            raise RuntimeError(fatal_msg)

    # ==========================================
    # 데이터 포맷팅 (ai_engine.py 동일 복사)
    # ==========================================

    def _format_market_data(self, ws_data, recent_ticks, recent_candles=None):
        if recent_candles is None:
            recent_candles = []

        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)

        imbalance_str = "데이터 없음"
        if ask_tot > 0 and bid_tot > 0:
            ratio = ask_tot / bid_tot
            if ratio >= 2.0:
                imbalance_str = f"매도벽 압도적 우위 ({ratio:.1f}배) - 돌파 시 급등 패턴"
            elif ratio <= 0.5:
                imbalance_str = f"매수벽 우위 ({1/ratio:.1f}배) - 하락 방어 또는 휩소(가짜) 패턴"
            else:
                imbalance_str = f"팽팽함 (매도 {ask_tot:,} vs 매수 {bid_tot:,})"

        high_price = curr_price
        if recent_candles:
            high_price = max(c.get('고가', curr_price) for c in recent_candles)

        drawdown_str = "0.0%"
        if high_price > 0:
            drawdown = ((curr_price - high_price) / high_price) * 100
            drawdown_str = f"{drawdown:.2f}% (당일 고가 {high_price:,}원)"

        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']:,}원 ({a['volume']:,}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']:,}원 ({b['volume']:,}주)" for i, b in enumerate(orderbook['bids'])])

        tick_summary = "틱 데이터 부족"
        tick_str = ""

        if recent_ticks and len(recent_ticks) > 0:
            buy_vol = sum(t['volume'] for t in recent_ticks if t.get('dir') == 'BUY')
            sell_vol = sum(t['volume'] for t in recent_ticks if t.get('dir') == 'SELL')
            total_vol = buy_vol + sell_vol
            buy_pressure = (buy_vol / total_vol * 100) if total_vol > 0 else 50.0

            latest_price = recent_ticks[0]['price']
            oldest_price = recent_ticks[-1]['price']
            trend_str = "상승 돌파 중 🚀" if latest_price > oldest_price else "하락 밀림 📉" if latest_price < oldest_price else "횡보 중 ➖"
            latest_strength = recent_ticks[0].get('strength', 0.0)

            time_diff_sec = 0
            try:
                from datetime import datetime
                t1_str = str(recent_ticks[-1]['time']).replace(':', '').zfill(6)
                t2_str = str(recent_ticks[0]['time']).replace(':', '').zfill(6)
                t1 = datetime.strptime(t1_str, "%H%M%S")
                t2 = datetime.strptime(t2_str, "%H%M%S")
                time_diff_sec = (t2 - t1).total_seconds()
                if time_diff_sec < 0:
                    time_diff_sec += 86400
            except:
                time_diff_sec = 999

            speed_str = f"🚀 매우 빠름 ({len(recent_ticks)}틱에 {time_diff_sec}초)" if time_diff_sec <= 2.0 else f"보통 ({time_diff_sec}초)" if time_diff_sec <= 10.0 else f"느림 ({time_diff_sec}초 - 소강상태)"

            tick_summary = (
                f"⏱️ [최근 {len(recent_ticks)}틱 정밀 브리핑]\n"
                f"- 단기 흐름: {trend_str}\n"
                f"- 틱 체결 속도(가속도): {speed_str}\n"
                f"- 🔥 매수 압도율(Buy Pressure): {buy_pressure:.1f}% (매수 {buy_vol:,}주 vs 매도 {sell_vol:,}주)\n"
                f"- 현재 체결강도: {latest_strength}%"
            )

            tick_str = "\n".join([f"[{t['time']}] {t.get('dir', 'NEUTRAL')} 체결: {t['price']:,}원 ({t['volume']:,}주) | 강도:{t.get('strength', 0)}%" for t in recent_ticks[:10]])

        candle_str = ""
        if recent_candles:
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c.get('시가', c.get('현재가', 0)):,} 고가:{c['고가']:,} 저가:{c['저가']:,} 종가:{c['현재가']:,} 거래량:{c['거래량']:,}"
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

        volume_analysis = "비교 불가 (데이터 부족)"
        if recent_candles and len(recent_candles) >= 2:
            current_volume = recent_candles[-1]['거래량']
            prev_volumes = [c['거래량'] for c in recent_candles[:-1]]
            avg_prev_volume = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0

            if avg_prev_volume > 0:
                vol_ratio = (current_volume / avg_prev_volume) * 100
                if vol_ratio >= 200:
                    volume_analysis = f"🔥 폭증! (이전 평균 대비 {vol_ratio:.0f}% 수준 / 현재 {current_volume:,}주)"
                elif vol_ratio >= 100:
                    volume_analysis = f"상승 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"
                else:
                    volume_analysis = f"감소 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"

        indicators_str = "지표 계산 불가"
        if recent_candles and len(recent_candles) >= 5:
            from src.engine.signal_radar import SniperRadar
            temp_radar = SniperRadar(token=None)
            ind = temp_radar.calculate_micro_indicators(recent_candles)

            ma5_status = "상회" if curr_price > ind['MA5'] else "하회"
            vwap_status = "상회 (수급강세)" if curr_price > ind['Micro_VWAP'] else "하회 (수급약세)"

            indicators_str = (
                f"- 단기 5-MA: {ind['MA5']:,}원 (현재가 {ma5_status})\n"
                f"- Micro-VWAP: {ind['Micro_VWAP']:,}원 (현재가 {vwap_status})\n"
                f"- 고점 대비 이격도: {drawdown_str}\n"
                f"- 호가 불균형: {imbalance_str}"
            )

        feature_packet = extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)
        quant_features_str = (
            f"- packet_version: {feature_packet['packet_version']}\n"
            f"- curr_price: {feature_packet['curr_price']}\n"
            f"- latest_strength: {feature_packet['latest_strength']}%\n"
            f"- spread_krw: {feature_packet['spread_krw']}\n"
            f"- spread_bp: {feature_packet['spread_bp']}\n"
            f"- top1_depth_ratio: {feature_packet['top1_depth_ratio']}\n"
            f"- top3_depth_ratio: {feature_packet['top3_depth_ratio']}\n"
            f"- orderbook_total_ratio: {feature_packet['orderbook_total_ratio']}\n"
            f"- micro_price: {feature_packet['micro_price']}\n"
            f"- microprice_edge_bp: {feature_packet['microprice_edge_bp']}\n"
            f"- buy_pressure_10t: {feature_packet['buy_pressure_10t']}%\n"
            f"- price_change_10t_pct: {feature_packet['price_change_10t_pct']}%\n"
            f"- recent_5tick_seconds: {feature_packet['recent_5tick_seconds']}\n"
            f"- prev_5tick_seconds: {feature_packet['prev_5tick_seconds']}\n"
            f"- distance_from_day_high_pct: {feature_packet['distance_from_day_high_pct']}%\n"
            f"- intraday_range_pct: {feature_packet['intraday_range_pct']}%\n"
            f"- tick_acceleration_ratio: {feature_packet['tick_acceleration_ratio']}\n"
            f"- same_price_buy_absorption: {feature_packet['same_price_buy_absorption']}\n"
            f"- large_sell_print_detected: {str(feature_packet['large_sell_print_detected']).lower()}\n"
            f"- large_buy_print_detected: {str(feature_packet['large_buy_print_detected']).lower()}\n"
            f"- net_aggressive_delta_10t: {feature_packet['net_aggressive_delta_10t']}\n"
            f"- volume_ratio_pct: {feature_packet['volume_ratio_pct']}%\n"
            f"- curr_vs_micro_vwap_bp: {feature_packet['curr_vs_micro_vwap_bp']}\n"
            f"- curr_vs_ma5_bp: {feature_packet['curr_vs_ma5_bp']}\n"
            f"- micro_vwap_value: {feature_packet['micro_vwap_value']}\n"
            f"- ma5_value: {feature_packet['ma5_value']}\n"
            f"- ask_depth_ratio: {feature_packet['ask_depth_ratio']}\n"
            f"- net_ask_depth: {feature_packet['net_ask_depth']}"
        )

        user_input = f"""
[현재 상태]
- 현재가: {curr_price:,}원
- 전일대비 등락률: {fluctuation}%
- 웹소켓 체결강도: {v_pw}%

[정량형 수급 피처]
{quant_features_str}

[초단타 수급/위치 지표]
{indicators_str}

[거래량 분석]
- {volume_analysis}

{tick_summary}

[최근 1분봉 흐름 (과거 -> 최신순)]
{candle_str}

[실시간 호가창]
{ask_str}
-------------------------
{bid_str}

[최근 10틱 상세 내역 (최신순)]
{tick_str}
"""
        return user_input

    def _extract_scalping_features(self, ws_data, recent_ticks, recent_candles=None):
        return extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)

    def _format_swing_market_data(self, ws_data, recent_candles, program_net_qty=0):
        curr_price = ws_data.get('curr', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        v_pw = ws_data.get('v_pw', 0)
        today_vol = ws_data.get('volume', 0)

        candle_str = "분봉 데이터 없음"
        ma5, ma20 = 0, 0
        if recent_candles and len(recent_candles) >= 20:
            closes = [c['현재가'] for c in recent_candles]
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20

            trend = "정배열 (상승세)" if ma5 > ma20 else "역배열 (하락세)"
            position = "MA5 위 (강세)" if curr_price > ma5 else "MA5 아래 (조정)"

            candle_str = (
                f"- 현재 단기 추세: {trend}\n"
                f"- MA5: {ma5:,.0f}원 / MA20: {ma20:,.0f}원\n"
                f"- 주가 위치: {position}\n"
                f"- 최근 5봉 흐름: " + " -> ".join([f"{c['현재가']:,}" for c in recent_candles[-5:]])
            )

        prog_sign = "🔴 순매수" if program_net_qty > 0 else "🔵 순매도"

        user_input = f"""
[현재 상태 (스윙 관점)]
- 현재가: {curr_price:,}원 (전일대비 {fluctuation:+.2f}%)
- 당일 누적 거래량: {today_vol:,}주
- 당일 체결강도: {v_pw}%

[메이저 수급 지표]
- 프로그램 동향: {prog_sign} ({program_net_qty:,}주)

[차트/위치 분석]
{candle_str}
"""
        return user_input

    def _infer_realtime_mode(self, realtime_ctx):
        strat_label = str(realtime_ctx.get("strat_label", "")).upper()
        position_status = str(realtime_ctx.get("position_status", "NONE")).upper()
        fluctuation = float(realtime_ctx.get("fluctuation", 0.0) or 0.0)
        vol_ratio = float(realtime_ctx.get("vol_ratio", 0.0) or 0.0)
        v_pw_now = float(realtime_ctx.get("v_pw_now", 0.0) or 0.0)
        v_pw_3m = float(realtime_ctx.get("v_pw_3m", 0.0) or 0.0)
        prog_delta_qty = int(realtime_ctx.get("prog_delta_qty", 0) or 0)
        curr_price = int(realtime_ctx.get("curr_price", 0) or 0)
        vwap_price = int(realtime_ctx.get("vwap_price", 0) or 0)
        high_breakout_status = str(realtime_ctx.get("high_breakout_status", ""))
        daily_setup_desc = str(realtime_ctx.get("daily_setup_desc", ""))
        session_stage = str(realtime_ctx.get("session_stage", "REGULAR")).upper()
        captured_at = str(realtime_ctx.get("captured_at", ""))

        if strat_label in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "MIDTERM", "POSITION"}:
            return "SWING"

        scalp_score = 0
        swing_score = 0

        if position_status == "HOLDING":
            swing_score += 2

        hhmm = ""
        if captured_at and len(captured_at) >= 16:
            hhmm = captured_at[11:16].replace(":", "")
        if not hhmm:
            hhmm = time.strftime("%H%M")

        if session_stage in {"PREOPEN", "OPENING"} or "0900" <= hhmm <= "1030":
            scalp_score += 2
        elif "1300" <= hhmm <= "1500":
            swing_score += 1

        if abs(fluctuation) >= 3.0:
            scalp_score += 1
        if vol_ratio >= 150:
            scalp_score += 2
        elif 70 <= vol_ratio <= 130:
            swing_score += 1

        if v_pw_now >= 120 and (v_pw_now - v_pw_3m) >= 10:
            scalp_score += 2

        if prog_delta_qty > 0:
            scalp_score += 1
            swing_score += 1

        if curr_price > 0 and vwap_price > 0 and curr_price >= vwap_price:
            scalp_score += 1
        if "돌파" in high_breakout_status:
            scalp_score += 1

        if any(k in daily_setup_desc for k in ["정배열", "눌림", "전고점", "추세", "돌파"]):
            swing_score += 2
        if any(k in daily_setup_desc for k in ["급등후", "과열", "이격", "장대음봉"]):
            swing_score -= 1

        if abs(scalp_score - swing_score) <= 1:
            return "DUAL"
        return "SCALP" if scalp_score > swing_score else "SWING"

    def _get_realtime_prompt(self, selected_mode):
        if selected_mode == "SCALP":
            return REALTIME_ANALYSIS_PROMPT_SCALP
        if selected_mode == "SWING":
            return REALTIME_ANALYSIS_PROMPT_SWING
        return REALTIME_ANALYSIS_PROMPT_DUAL

    def _build_realtime_quant_packet(self, stock_name, stock_code, realtime_ctx, selected_mode):
        def i(key, default=0):
            try:
                return int(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        def f(key, default=0.0):
            try:
                return float(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        curr_price = i("curr_price")
        vwap_price = i("vwap_price")
        ask_tot = i("ask_tot")
        bid_tot = i("bid_tot")
        orderbook_imbalance = f("orderbook_imbalance")
        best_ask = i("best_ask")
        best_bid = i("best_bid")
        tick_trade_value = i("tick_trade_value")
        cum_trade_value = i("cum_trade_value")
        buy_exec_volume = i("buy_exec_volume")
        sell_exec_volume = i("sell_exec_volume")
        net_buy_exec_volume = i("net_buy_exec_volume")
        buy_exec_single = i("buy_exec_single")
        sell_exec_single = i("sell_exec_single")
        prog_buy_qty = i("prog_buy_qty")
        prog_sell_qty = i("prog_sell_qty")
        prog_buy_amt = i("prog_buy_amt")
        prog_sell_amt = i("prog_sell_amt")

        common_block = f"""[기본]
- 종목명: {stock_name}
- 종목코드: {stock_code}
- 시가총액: {i('market_cap'):,}원
- 분석모드: {selected_mode}
- 감시전략: {realtime_ctx.get('strat_label', 'AUTO')}
- 보유상태: {realtime_ctx.get('position_status', 'NONE')}
- 평균단가: {i('avg_price'):,}원
- 현재손익률: {f('pnl_pct'):+.2f}%
- 현재가격: {curr_price:,}원 (전일비 {f('fluctuation'):+.2f}%)
- 기계목표가: {i('target_price'):,}원 (사유: {realtime_ctx.get('target_reason', '')})
- 익절/손절: {f('trailing_pct'):.2f}% / {f('stop_pct'):.2f}%
- 퀀트 점수: 추세 {f('trend_score'):.1f} / 수급 {f('flow_score'):.1f} / 호가 {f('orderbook_score'):.1f} / 타점 {f('timing_score'):.1f} / 종합 {f('score'):.1f}
- 퀀트 엔진 결론: {realtime_ctx.get('conclusion', '')}

[수급/체결]
- 누적거래량: {i('today_vol'):,}주 (20일 평균대비 {f('vol_ratio'):.1f}%)
- 거래대금: {i('today_turnover'):,}원
- 체결강도 현재/1분/3분/5분: {f('v_pw_now'):.1f} / {f('v_pw_1m'):.1f} / {f('v_pw_3m'):.1f} / {f('v_pw_5m'):.1f}
- 매수세 현재/1분/3분: {f('buy_ratio_now'):.1f}% / {f('buy_ratio_1m'):.1f}% / {f('buy_ratio_3m'):.1f}%
- 프로그램 순매수 현재/증감: {i('prog_net_qty'):+,}주 / {i('prog_delta_qty'):+,}주
- 프로그램 절대 매수/매도: {prog_buy_qty:+,}주 / {prog_sell_qty:+,}주 | {prog_buy_amt:+,} / {prog_sell_amt:+,}
- 외인/기관 당일 가집계: 외인 {i('foreign_net'):+,}주 / 기관 {i('inst_net'):+,}주
- 외인+기관 합산: {i('smart_money_net'):+,}주
- 순간 체결대금/누적: {tick_trade_value:,} / {cum_trade_value:,}
- 매수/매도 체결량: {buy_exec_volume:+,} / {sell_exec_volume:+,} (순매수 {net_buy_exec_volume:+,})
- 체결 매수비율(WS): {f('buy_ratio_ws'):.1f}% / 체결량 기준 {f('exec_buy_ratio'):.1f}%
- 단건 체결: 매수 {buy_exec_single:+,} / 매도 {sell_exec_single:+,}
- 수급 요약: {realtime_ctx.get('micro_flow_desc', '')} / {realtime_ctx.get('program_flow_desc', '')}

[호가/구조]
- 최우선 매도/매수호가: {best_ask:,} / {best_bid:,}
- 매도잔량/매수잔량: {ask_tot:,} / {bid_tot:,}
- 호가 불균형비: {orderbook_imbalance:.2f}
- 스프레드: {i('spread_tick')}틱
- 체결 편향: {realtime_ctx.get('tape_bias', '중립')}
- 매도벽 소화 여부: {realtime_ctx.get('ask_absorption_status', '')}
- 잔량 개선: 매수 {i('net_bid_depth'):+,} ({f('bid_depth_ratio'):.1f}%) / 매도 {i('net_ask_depth'):+,} ({f('ask_depth_ratio'):.1f}%)
- 잔량 요약: {realtime_ctx.get('depth_flow_desc', '')}
- VWAP: {vwap_price:,}원 ({realtime_ctx.get('vwap_status', '정보없음')})
- 시가 위치: {realtime_ctx.get('open_position_desc', '')}
- 고가 돌파 여부: {realtime_ctx.get('high_breakout_status', '')}
- 최근 5분 박스 상단/하단: {i('box_high'):,} / {i('box_low'):,}
"""

        scalp_block = f"""
[스캘핑 관점]
- 체결강도 가속도: {f('v_pw_now') - f('v_pw_3m'):+.1f}
- 체결 signed 수량: {i('trade_qty_signed_now'):+,}주
- 프로그램 delta: {i('prog_delta_qty'):+,}주
- 눌림/돌파 즉시성 체크: VWAP / 고가 / 스프레드 / 테이프 편향
"""

        swing_block = f"""
[스윙 관점]
- 일봉 구조: {realtime_ctx.get('daily_setup_desc', '')}
- 5/20/60일선 상태: {realtime_ctx.get('ma5_status', '')}, {realtime_ctx.get('ma20_status', '')}, {realtime_ctx.get('ma60_status', '')}
- 전일 고점/저점: {i('prev_high'):,} / {i('prev_low'):,}
- 최근 20일 신고가 근접도: {f('near_20d_high_pct'):.2f}%
- 고가 대비 눌림폭: {f('drawdown_from_high_pct'):.2f}%
"""

        if selected_mode == "SCALP":
            return common_block + scalp_block
        if selected_mode == "SWING":
            return common_block + swing_block
        return common_block + scalp_block + swing_block

    # ==========================================
    # 게이트키퍼 캐시 (ai_engine.py 동일 복사)
    # ==========================================

    def _compact_gatekeeper_ctx_for_cache(self, realtime_ctx):
        ctx = realtime_ctx or {}
        curr_price = ctx.get("curr_price", 0)
        target_price = ctx.get("target_price", 0)
        vwap_price = ctx.get("vwap_price", 0)
        prev_high = ctx.get("prev_high", 0)
        price_bucket = self._price_bucket_step_for_cache(curr_price)
        return {
            "strat_label": str(ctx.get("strat_label", "") or ""),
            "position_status": str(ctx.get("position_status", "") or ""),
            "curr_price": self._bucket_int_for_cache(curr_price, price_bucket),
            "target_price": self._bucket_int_for_cache(target_price, price_bucket),
            "vwap_price": self._bucket_int_for_cache(vwap_price, price_bucket),
            "prev_high": self._bucket_int_for_cache(prev_high, price_bucket),
            "market_cap": self._bucket_int_for_cache(ctx.get("market_cap", 0), 50_000_000_000),
            "fluctuation": self._bucket_float_for_cache(ctx.get("fluctuation", 0.0), 0.3),
            "score": self._bucket_float_for_cache(ctx.get("score", 0.0), 10.0),
            "v_pw_now": self._bucket_float_for_cache(ctx.get("v_pw_now", 0.0), 5.0),
            "buy_ratio_ws": self._bucket_float_for_cache(ctx.get("buy_ratio_ws", 0.0), 4.0),
            "exec_buy_ratio": self._bucket_float_for_cache(ctx.get("exec_buy_ratio", 0.0), 8.0),
            "prog_net_qty": self._bucket_int_for_cache(ctx.get("prog_net_qty", 0), 10_000),
            "prog_delta_qty": self._bucket_int_for_cache(ctx.get("prog_delta_qty", 0), 2_000),
            "tick_trade_value": self._bucket_int_for_cache(ctx.get("tick_trade_value", 0), 25_000),
            "net_buy_exec_volume": self._bucket_int_for_cache(ctx.get("net_buy_exec_volume", 0), 500),
            "net_bid_depth": self._bucket_int_for_cache(ctx.get("net_bid_depth", 0), 10_000),
            "net_ask_depth": self._bucket_int_for_cache(ctx.get("net_ask_depth", 0), 10_000),
            "spread_tick": self._bucket_int_for_cache(ctx.get("spread_tick", 0), 1),
            "vol_ratio": self._bucket_float_for_cache(ctx.get("vol_ratio", 0.0), 25.0),
            "today_vol": self._bucket_int_for_cache(ctx.get("today_vol", 0), 100_000),
        }

    def _build_gatekeeper_cache_key(self, stock_name, stock_code, realtime_ctx, analysis_mode):
        return self._build_cache_digest({
            "stock_name": stock_name,
            "stock_code": stock_code,
            "analysis_mode": analysis_mode,
            "realtime_ctx": self._compact_gatekeeper_ctx_for_cache(realtime_ctx),
        })

    def _prepare_realtime_report_request(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        selected_mode = (analysis_mode or "AUTO").upper()
        realtime_ctx = input_data_text if isinstance(input_data_text, dict) else None

        if realtime_ctx is not None:
            if selected_mode == "AUTO":
                selected_mode = self._infer_realtime_mode(realtime_ctx)
            prompt = self._get_realtime_prompt(selected_mode)
            packet_text = self._build_realtime_quant_packet(stock_name, stock_code, realtime_ctx, selected_mode)
            user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 전술 패킷]
{packet_text}"""
            context_name = f"실시간 분석({selected_mode})"
        else:
            if selected_mode == "AUTO":
                selected_mode = "DUAL"
            prompt = self._get_realtime_prompt(selected_mode)
            user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 분석 입력]
{str(input_data_text)}"""
            context_name = f"실시간 분석(LEGACY:{selected_mode})"

        return {
            "selected_mode": selected_mode,
            "prompt": prompt,
            "user_input": user_input,
            "context_name": context_name,
        }

    def _generate_realtime_report_payload(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        total_started_at = time.perf_counter()
        lock_started_at = time.perf_counter()
        with self.lock:
            lock_wait_ms = int((time.perf_counter() - lock_started_at) * 1000)

            build_started_at = time.perf_counter()
            request = self._prepare_realtime_report_request(
                stock_name=stock_name,
                stock_code=stock_code,
                input_data_text=input_data_text,
                analysis_mode=analysis_mode,
            )
            packet_build_ms = int((time.perf_counter() - build_started_at) * 1000)

            model_started_at = time.perf_counter()
            report_error = ""
            try:
                report = self._call_deepseek_safe(
                    request["prompt"],
                    request["user_input"],
                    require_json=False,
                    context_name=request["context_name"],
                    model_override=self._get_tier2_model(),
                )
            except Exception as e:
                report_error = str(e)
                log_error(f"🚨 [{request['context_name']}] DeepSeek 에러: {e}")
                report = f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
            model_call_ms = int((time.perf_counter() - model_started_at) * 1000)

        total_ms = int((time.perf_counter() - total_started_at) * 1000)
        return {
            "report": report,
            "selected_mode": request["selected_mode"],
            "context_name": request["context_name"],
            "lock_wait_ms": lock_wait_ms,
            "packet_build_ms": packet_build_ms,
            "model_call_ms": model_call_ms,
            "total_ms": total_ms,
            "error": report_error,
        }

    # ==========================================
    # 퍼블릭 메서드: analyze_target (핵심 실시간 분석)
    # ==========================================

    def analyze_target(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        program_net_qty=0,
        cache_profile="default",
        prompt_profile="shared",
    ):
        analysis_started = time.perf_counter()
        prompt_version = "default_v1"
        cache_strategy = strategy
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            prompt_type = "swing"
            prompt = SWING_SYSTEM_PROMPT
        else:
            prompt, prompt_type, prompt_version, normalized_profile = self._resolve_scalping_prompt(prompt_profile)
            if normalized_profile != "shared":
                cache_strategy = f"{strategy}:{normalized_profile}"
        cache_key = self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=cache_strategy,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=program_net_qty,
            cache_profile=cache_profile,
        )
        cached_result = self._cache_get("_analysis_cache", cache_key)
        if cached_result is not None:
            return self._annotate_analysis_result(
                cached_result,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                cache_hit=True,
                cache_mode="hit",
                result_source="cache",
            )

        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "AI 경합 (다른 종목 분석 중)"},
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="lock_contention",
            )

        try:
            cached_result = self._cache_get("_analysis_cache", cache_key)
            if cached_result is not None:
                return self._annotate_analysis_result(
                    cached_result,
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                    parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                    fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                    cache_hit=True,
                    cache_mode="hit",
                    result_source="cache",
                )

            if self.ai_disabled:
                return self._annotate_analysis_result(
                    {"action": "DROP", "score": 0, "reason": "AI 엔진 일시 중단 (연속 실패)"},
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=False,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="engine_disabled",
                )

            if time.time() - self.last_call_time < self.min_interval:
                return self._annotate_analysis_result(
                    {"action": "WAIT", "score": 50, "reason": "AI 쿨타임"},
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=True,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="cooldown",
                )

            if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
                formatted_data = self._format_swing_market_data(ws_data, recent_candles, program_net_qty)
                target_model = self._get_tier2_model()
                feature_audit_fields = {}
            else:
                formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
                target_model = self._get_tier1_model()
                feature_audit_fields = build_scalping_feature_audit_fields(
                    extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)
                )

            # DeepSeek API 호출 (use_google_search 제거)
            result = self._call_deepseek_safe(
                prompt,
                formatted_data,
                require_json=True,
                context_name=f"{target_name}({strategy}:{prompt_type})",
                model_override=target_model,
            )

            if strategy not in ["KOSPI_ML", "KOSDAQ_ML"]:
                result = self._apply_remote_entry_guard(
                    result,
                    prompt_type=prompt_type,
                    ws_data=ws_data,
                    recent_ticks=recent_ticks,
                    recent_candles=recent_candles,
                )
                result = self._normalize_scalping_action_schema(result, prompt_type=prompt_type)
                result.update(feature_audit_fields)

            self.consecutive_failures = 0
            self.last_call_time = time.time()
            self._cache_set(
                "_analysis_cache",
                cache_key,
                result,
                self._resolve_analysis_cache_ttl(cache_profile),
            )
            return self._annotate_analysis_result(
                result,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
            )

        except Exception as e:
            self.consecutive_failures += 1
            log_error(f"🚨 [{target_name}][{strategy}] DeepSeek 실시간 분석 에러 (연속 실패 {self.consecutive_failures}회, API키 인덱스 {self.current_api_key_index}): {e}")

            if self.consecutive_failures >= self.max_consecutive_failures:
                self.ai_disabled = True
                log_error(f"🚨 DeepSeek 엔진 비활성화 (연속 실패 {self.consecutive_failures}회 초과, API키 인덱스 {self.current_api_key_index})")

            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": f"에러: {e}"},
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="exception",
            )
        finally:
            self.lock.release()

    # ==========================================
    # 퍼블릭 메서드: analyze_target_shadow_prompt (그림자 프롬프트)
    # ==========================================

    def analyze_target_shadow_prompt(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        *,
        strategy="SCALPING",
        prompt_override=None,
        prompt_type="scalping_shadow",
        cache_profile="shadow",
    ):
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "shadow unsupported for swing"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=0,
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_unsupported",
            )

        analysis_started = time.perf_counter()
        cache_key = self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=f"{strategy}:{prompt_type}",
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=0,
            cache_profile=cache_profile,
        )
        cached_result = self._cache_get("_analysis_cache", cache_key)
        if cached_result is not None:
            return self._annotate_analysis_result(
                cached_result,
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                cache_hit=True,
                cache_mode="hit",
                result_source="shadow_cache",
            )

        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "AI shadow 경합"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_lock_contention",
            )

        try:
            cached_result = self._cache_get("_analysis_cache", cache_key)
            if cached_result is not None:
                return self._annotate_analysis_result(
                    cached_result,
                    prompt_type=prompt_type,
                    prompt_version="shadow_v1",
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                    parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                    fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                    cache_hit=True,
                    cache_mode="hit",
                    result_source="shadow_cache",
                )

            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            active_prompt = prompt_override if prompt_override else SCALPING_SYSTEM_PROMPT_75_CANARY

            result = self._call_deepseek_safe(
                active_prompt,
                formatted_data,
                require_json=True,
                context_name=f"{target_name}(shadow:{prompt_type})",
                model_override=self._get_tier1_model(),
            )

            self._cache_set(
                "_analysis_cache",
                cache_key,
                result,
                self._resolve_analysis_cache_ttl(cache_profile),
            )
            return self._annotate_analysis_result(
                result,
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_live",
            )
        except Exception as e:
            log_error(f"🚨 [{target_name}] DeepSeek shadow 분석 에러: {e}")
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": f"shadow 에러: {e}"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_exception",
            )
        finally:
            self.lock.release()

    # ==========================================
    # 퍼블릭 메서드: analyze_scanner_results (시장 브리핑)
    # ==========================================

    def analyze_scanner_results(self, total_count, survived_count, stats_text, macro_text=""):
        """텔레그램 아침 브리핑 (Macro + Scanner 통합) - DeepSeek Tier3 사용"""
        with self.lock:
            data_input = build_scanner_data_input(
                total_count=total_count,
                survived_count=survived_count,
                stats_text=stats_text,
                macro_text=macro_text,
            )

            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            enriched_input = f"""현재 UTC 시각: {now_utc}

    {data_input}"""

            try:
                # DeepSeek은 Google Search 미지원 → use_google_search 제거
                return self._call_deepseek_safe(
                    ENHANCED_MARKET_ANALYSIS_PROMPT,
                    enriched_input,
                    require_json=False,
                    context_name="시장 브리핑",
                    model_override=self._get_tier3_model(),
                )
            except Exception as e:
                log_error(f"🚨 [시장 브리핑] DeepSeek 에러: {e}")
                return f"⚠️ AI 시장 진단 생성 중 에러 발생: {e}"

    # ==========================================
    # 퍼블릭 메서드: 실시간 리포트/게이트키퍼
    # ==========================================

    def generate_realtime_report(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        """실시간 종목 분석 리포트 생성"""
        return self._generate_realtime_report_payload(
            stock_name=stock_name,
            stock_code=stock_code,
            input_data_text=input_data_text,
            analysis_mode=analysis_mode,
        )["report"]

    def extract_realtime_gatekeeper_action(self, report_text):
        """실시간 리포트 본문에서 최종 행동 라벨을 추출합니다."""
        if not isinstance(report_text, str) or not report_text:
            return "UNKNOWN"

        action_labels = [
            "[즉시 매수]",
            "[눌림 대기]",
            "[보유 지속]",
            "[일부 익절]",
            "[전량 회피]",
            "[스캘핑 우선]",
            "[스윙 우선]",
            "[둘 다 아님]",
        ]
        for label in action_labels:
            if label in report_text:
                return label.strip("[]")
        return "UNKNOWN"

    def evaluate_realtime_gatekeeper(self, stock_name, stock_code, realtime_ctx, analysis_mode="AUTO"):
        """generate_realtime_report 결과를 마지막 진입 게이트 판단용으로 정규화합니다."""
        cache_key = self._build_gatekeeper_cache_key(
            stock_name=stock_name,
            stock_code=stock_code,
            realtime_ctx=realtime_ctx,
            analysis_mode=analysis_mode,
        )
        cached_gatekeeper = self._cache_get("_gatekeeper_cache", cache_key)
        if cached_gatekeeper is not None:
            return cached_gatekeeper

        report_payload = self._generate_realtime_report_payload(
            stock_name=stock_name,
            stock_code=stock_code,
            input_data_text=realtime_ctx,
            analysis_mode=analysis_mode,
        )
        report = report_payload["report"]
        action_label = self.extract_realtime_gatekeeper_action(report)
        allow_entry = action_label == "즉시 매수"
        result = {
            "allow_entry": allow_entry,
            "action_label": action_label,
            "report": report,
            "selected_mode": report_payload.get("selected_mode", ""),
            "lock_wait_ms": int(report_payload.get("lock_wait_ms", 0) or 0),
            "packet_build_ms": int(report_payload.get("packet_build_ms", 0) or 0),
            "model_call_ms": int(report_payload.get("model_call_ms", 0) or 0),
            "total_internal_ms": int(report_payload.get("total_ms", 0) or 0),
            "cache_hit": False,
            "cache_mode": "miss",
        }
        self._cache_set("_gatekeeper_cache", cache_key, result, self.gatekeeper_cache_ttl)
        return result

    # ==========================================
    # 퍼블릭 메서드: 오버나이트 의사결정
    # ==========================================

    def _format_scalping_overnight_context(self, realtime_ctx):
        ctx = realtime_ctx or {}
        lines = [
            f"- 포지션상태: {ctx.get('position_status', 'UNKNOWN')}",
            f"- 평균단가: {int(ctx.get('avg_price', 0) or 0):,}원",
            f"- 현재가: {int(ctx.get('curr_price', 0) or 0):,}원 (손익 {float(ctx.get('pnl_pct', 0.0) or 0.0):+.2f}%)",
            f"- 보유분수: {float(ctx.get('held_minutes', 0.0) or 0.0):.1f}분",
            f"- 현재 전략라벨: {ctx.get('strat_label', 'SCALPING')}",
            f"- VWAP: {int(ctx.get('vwap_price', 0) or 0):,}원 / 상태: {ctx.get('vwap_status', '')}",
            f"- 체결강도 현재/3분전/5분전: {float(ctx.get('v_pw_now', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_3m', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_5m', 0.0) or 0.0):.1f}",
            f"- 프로그램 순매수 현재/증감: {int(ctx.get('prog_net_qty', 0) or 0):,}주 / {int(ctx.get('prog_delta_qty', 0) or 0):+,}주",
            f"- 외인/기관 순매수: {int(ctx.get('foreign_net', 0) or 0):,}주 / {int(ctx.get('inst_net', 0) or 0):,}주",
            f"- 고가돌파 상태: {ctx.get('high_breakout_status', '')}",
            f"- 일봉 구조: {ctx.get('daily_setup_desc', '')}",
            f"- 5/20/60일선 상태: {ctx.get('ma5_status', '')}, {ctx.get('ma20_status', '')}, {ctx.get('ma60_status', '')}",
            f"- 전일 고점/저점: {int(ctx.get('prev_high', 0) or 0):,} / {int(ctx.get('prev_low', 0) or 0):,}",
            f"- 최근 20일 신고가 근접도: {float(ctx.get('near_20d_high_pct', 0.0) or 0.0):+.2f}%",
            f"- 퀀트 종합점수/결론: {float(ctx.get('score', 0.0) or 0.0):.1f} / {ctx.get('conclusion', '')}",
            f"- 주문상태 참고: {ctx.get('order_status_note', '')}",
        ]
        return "\n".join(lines)

    def evaluate_scalping_overnight_decision(self, stock_name, stock_code, realtime_ctx):
        """15:30 SCALPING 포지션의 오버나이트/당일청산 의사결정을 JSON으로 반환합니다."""
        with self.lock:
            user_input = (
                f"🚨 [15:30 SCALPING 오버나이트 판정 요청]\n"
                f"종목명: {stock_name}\n종목코드: {stock_code}\n\n"
                f"📊 [판정 입력 데이터]\n{self._format_scalping_overnight_context(realtime_ctx)}"
            )
            try:
                result = self._call_deepseek_safe(
                    SCALPING_OVERNIGHT_DECISION_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"SCALP_OVERNIGHT:{stock_name}",
                    model_override=self._get_tier2_model(),
                )
                action = str(result.get('action', 'SELL_TODAY') or 'SELL_TODAY').upper()
                if action not in {'SELL_TODAY', 'HOLD_OVERNIGHT'}:
                    action = 'SELL_TODAY'
                return {
                    'action': action,
                    'confidence': int(result.get('confidence', 0) or 0),
                    'reason': str(result.get('reason', '') or ''),
                    'risk_note': str(result.get('risk_note', '') or ''),
                    'raw': result,
                }
            except Exception as e:
                log_error(f"🚨 [SCALPING 오버나이트 판정] DeepSeek 에러: {e}")
                return {
                    'action': 'SELL_TODAY',
                    'confidence': 0,
                    'reason': f'AI 판정 실패로 보수적 청산 폴백: {e}',
                    'risk_note': '데이터 부족 또는 AI 응답 오류',
                    'raw': {},
                }

    # ==========================================
    # 퍼블릭 메서드: 조건검색식 진입/청산 판단
    # ==========================================

    def evaluate_condition_entry(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile):
        """조건검색식 진입 판단"""
        with self.lock:
            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            profile_text = f"조건검색식 프로필: {condition_profile}"
            user_input = f"{stock_name}({stock_code}) - 조건검색식 진입 판단 요청\n{profile_text}\n\n{formatted_data}"
            try:
                result = self._call_deepseek_safe(
                    CONDITION_ENTRY_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"COND_ENTRY:{stock_name}",
                    model_override=self._get_tier1_model(),
                )
                return result
            except Exception as e:
                log_error(f"🚨 [조건검색식 진입 판단] DeepSeek 에러: {e}")
                return {
                    "decision": "SKIP",
                    "confidence": 0,
                    "order_type": "NONE",
                    "position_size_ratio": 0.0,
                    "invalidation_price": 0,
                    "reasons": [f"AI 판정 실패: {e}"],
                    "risks": ["데이터 부족 또는 AI 응답 오류"],
                }

    def evaluate_condition_exit(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile, profit_rate, peak_profit, current_ai_score):
        """조건검색식 청산 판단"""
        with self.lock:
            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            profile_text = f"조건검색식 프로필: {condition_profile}, 수익률: {profit_rate:.2f}%, 최고수익률: {peak_profit:.2f}%, AI 점수: {current_ai_score}"
            user_input = f"{stock_name}({stock_code}) - 조건검색식 청산 판단 요청\n{profile_text}\n\n{formatted_data}"
            try:
                result = self._call_deepseek_safe(
                    CONDITION_EXIT_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"COND_EXIT:{stock_name}",
                    model_override=self._get_tier1_model(),
                )
                return result
            except Exception as e:
                log_error(f"🚨 [조건검색식 청산 판단] DeepSeek 에러: {e}")
                return {
                    "decision": "HOLD",
                    "confidence": 0,
                    "trim_ratio": 0.0,
                    "new_stop_price": 0,
                    "reason_primary": f"AI 판정 실패: {e}",
                    "warning": "데이터 부족 또는 AI 응답 오류",
                }

    # ==========================================
    # 퍼블릭 메서드: EOD 주도주 분석
    # ==========================================

    def _render_eod_tomorrow_markdown(self, market_summary, one_point_lesson, top5):
        medals = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}
        lines = [
            "📊 **[여의도 프랍 데스크] 내일의 주도주 TOP 5 마감 브리핑**",
            str(market_summary or "").strip(),
            ""
        ]

        for item in top5[:5]:
            rank = int(item.get("rank", 0) or 0)
            medal = medals.get(rank, "⭐")
            stock_name = str(item.get("stock_name", "") or "")
            stock_code = str(item.get("stock_code", "") or "").zfill(6)

            try:
                close_price = int(float(item.get("close_price", 0) or 0))
            except Exception:
                close_price = 0

            reason = str(item.get("reason", "") or "").strip()
            entry_plan = str(item.get("entry_plan", "") or "").strip()
            target_guide = str(item.get("target_price_guide", "") or "").strip()
            stop_guide = str(item.get("stop_price_guide", "") or "").strip()

            lines.extend([
                f"{medal} **{rank}. {stock_name} ({stock_code})**",
                f"- 💰 종가: {close_price:,}원",
                f"- 🧠 선정 사유: {reason}",
                f"- 🎯 타점 전략: {entry_plan} / 목표가 가이드: {target_guide} / 손절가 가이드: {stop_guide}",
                ""
            ])

        lines.extend([
            "💡 **[수석 트레이더의 내일 장 원포인트 레슨]**",
            str(one_point_lesson or "").strip()
        ])
        return "\n".join(lines)

    def generate_eod_tomorrow_bundle(self, candidates_text):
        """
        장 마감 후 내일의 주도주 TOP5를
        1) 구조화 JSON
        2) 동일 데이터 기반 Markdown 리포트
        로 함께 반환
        """
        with self.lock:
            user_input = (
                f"🚨 [1차 필터링 완료: 내일의 주도주 후보군 15선]\n\n"
                f"{candidates_text}"
            )
            try:
                # DeepSeek은 Google Search 미지원 → use_google_search 제거
                result = self._call_deepseek_safe(
                    EOD_TOMORROW_LEADER_JSON_PROMPT,
                    user_input,
                    require_json=True,
                    context_name="종가베팅 TOP5 JSON",
                    model_override=self._get_tier3_model(),
                )

                raw_top5 = result.get("top5", []) or []
                normalized = []

                for idx, item in enumerate(raw_top5[:5], start=1):
                    code = str(item.get("stock_code", "")).replace(".0", "").strip().zfill(6)
                    name = str(item.get("stock_name", "")).strip()
                    if not code or not name:
                        continue

                    try:
                        close_price = int(float(item.get("close_price", 0) or 0))
                    except Exception:
                        close_price = 0

                    try:
                        confidence = float(item.get("confidence", 0.0) or 0.0)
                    except Exception:
                        confidence = 0.0

                    try:
                        rank = int(item.get("rank", idx) or idx)
                    except Exception:
                        rank = idx

                    normalized.append({
                        "rank": rank,
                        "stock_name": name,
                        "stock_code": code,
                        "close_price": close_price,
                        "reason": str(item.get("reason", "") or "").strip(),
                        "entry_plan": str(item.get("entry_plan", "") or "").strip(),
                        "target_price_guide": str(item.get("target_price_guide", "") or "").strip(),
                        "stop_price_guide": str(item.get("stop_price_guide", "") or "").strip(),
                        "confidence": max(0.0, min(1.0, confidence)),
                    })

                market_summary = str(result.get("market_summary", "") or "").strip()
                one_point_lesson = str(result.get("one_point_lesson", "") or "").strip()
                report = self._render_eod_tomorrow_markdown(
                    market_summary=market_summary,
                    one_point_lesson=one_point_lesson,
                    top5=normalized,
                )

                return {
                    "market_summary": market_summary,
                    "one_point_lesson": one_point_lesson,
                    "top5": normalized,
                    "report": report,
                }

            except Exception as e:
                log_error(f"🚨 [종가베팅 번들] DeepSeek 에러: {e}")
                return {
                    "market_summary": "",
                    "one_point_lesson": "",
                    "top5": [],
                    "report": f"⚠️ AI 종가베팅 분석 생성 중 에러 발생: {e}",
                }

    def generate_eod_tomorrow_report(self, candidates_text):
        """장 마감 후 내일의 주도주 TOP 5 리포트 생성 (호환용)"""
        bundle = self.generate_eod_tomorrow_bundle(candidates_text)
        return bundle.get("report", "⚠️ EOD 리포트 생성 실패")
