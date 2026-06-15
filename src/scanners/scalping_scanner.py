import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime
from math import log10

# 💡 Level 1 & 2 공통 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.engine.signal_radar import SniperRadar
from src.utils.constants import TRADING_RULES
from src.utils.pipeline_event_logger import emit_pipeline_event


def _resolve_scan_interval_sec(now_time):
    """장 초반/후반에는 더 자주 돌리고, 점심 구간은 약간 완화합니다."""
    hhmm = now_time.hour * 100 + now_time.minute
    if 905 <= hhmm < 1030:
        return 120
    if 1400 <= hhmm <= 1500:
        return 120
    return 180


def _source_priority(source):
    """장중 신선도는 시가대비 상위보다 최근 수급 급증 신호를 더 높게 봅니다."""
    return {
        "VI+VALUE": 0,
        "SUPERNOVA+VALUE": 1,
        "VI_TRIGGERED": 2,
        "BOTH": 3,
        "SUPERNOVA": 4,
        "BOTH+VALUE": 5,
        "VALUE_TOP": 6,
        "OPEN_TOP": 7,
    }.get(str(source or "OPEN_TOP"), 8)


def _safe_float(value, default=0.0):
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        clean_value = str(value).replace(",", "").replace("+", "").strip()
        if not clean_value:
            return default
        return int(float(clean_value))
    except (TypeError, ValueError):
        return default


def _safe_positive_int(value, default=0):
    parsed = _safe_int(value, default)
    if parsed is None:
        return default
    return abs(parsed)


def _bounded(value, low=0.0, high=9999.0):
    return max(low, min(high, float(value or 0.0)))


def _pick_first_present(payload, keys):
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            return payload.get(key)
    return None


def _extract_strength_value(payload):
    raw_value = _pick_first_present(
        payload or {},
        (
            "CntrStr",
            "cntr_str",
            "cntr_strg",
            "cntr_streng",
            "exec_strength",
            "v_pw",
        ),
    )
    if raw_value is None:
        return 0.0, False
    value = _safe_float(raw_value)
    return value, value > 0.0


def _format_strength_display(target):
    if not bool(target.get("CntrStrAvailable", False)):
        return "수신대기"
    return f"{_safe_float(target.get('CntrStr')):.1f}"


def _representative_source(source_set):
    sources = set(source_set or [])
    has_open = "OPEN_TOP" in sources
    has_supernova = "SUPERNOVA" in sources
    has_value = "VALUE_TOP" in sources
    has_vi = "VI_TRIGGERED" in sources

    if has_vi and has_value:
        return "VI+VALUE"
    if has_value and has_open and has_supernova:
        return "BOTH+VALUE"
    if has_value and has_supernova:
        return "SUPERNOVA+VALUE"
    if has_value:
        return "VALUE_TOP"
    if has_vi:
        return "VI_TRIGGERED"
    if has_open and has_supernova:
        return "BOTH"
    if has_supernova:
        return "SUPERNOVA"
    return "OPEN_TOP"


def _source_signature(target):
    return tuple(sorted(set(target.get("SourceSet") or [target.get("Source") or "OPEN_TOP"])))


def _scanner_rate_from_field(target, field_name):
    if field_name in (target or {}) and target.get(field_name) not in (None, ""):
        return _safe_float(target.get(field_name)), True
    return 0.0, False


def _scanner_flu_metric(target):
    source_set = set(_source_signature(target))

    if source_set and source_set.issubset({"OPEN_TOP", "VALUE_TOP"}):
        open_rate, has_open = _scanner_rate_from_field(target, "OpenFluRate")
        if has_open:
            return open_rate, "open_flu_rate", "OPEN_TOP"
        value_rate, has_value = _scanner_rate_from_field(target, "ValueFluRate")
        if source_set == {"VALUE_TOP"} and has_value:
            return value_rate, "day_flu_rate", "VALUE_TOP"

    if "VI_TRIGGERED" in source_set:
        vi_rate, has_vi = _scanner_rate_from_field(target, "ViFluRate")
        if has_vi:
            return vi_rate, "vi_disparity_or_open_rate", "VI_TRIGGERED"

    if "SUPERNOVA" in source_set:
        supernova_rate, has_supernova = _scanner_rate_from_field(target, "SupernovaFluRate")
        if has_supernova:
            return supernova_rate, "supernova_source_rate", "SUPERNOVA"

    value_rate, has_value = _scanner_rate_from_field(target, "ValueFluRate")
    if has_value:
        return value_rate, "day_flu_rate", "VALUE_TOP"

    legacy_rate = _safe_float(target.get("FluRate"))
    return legacy_rate, "legacy_flu_rate", str(target.get("Source") or "UNKNOWN")


def _rank_jump(target):
    rank_now = _safe_int(target.get("RankNow"))
    rank_prev = _safe_int(target.get("RankPrev"))
    if rank_now > 0 and rank_prev > rank_now:
        return rank_prev - rank_now
    return 0


def _scanner_candidate_role(target):
    source_set = set(_source_signature(target))
    if source_set in ({"VALUE_TOP"}, {"OPEN_TOP"}, {"OPEN_TOP", "VALUE_TOP"}):
        return "late_confirmation"
    return "early_discovery"


def _price_delta_pct(first_price, current_price):
    first = _safe_positive_int(first_price)
    current = _safe_positive_int(current_price)
    if first <= 0 or current <= 0:
        return 0.0
    return ((current - first) / first) * 100.0


def _late_confirmation_probe_block_reason(*, probe_age, min_probe_sec, max_probe_sec, price_declined, flu_metric_changed=False):
    if probe_age < min_probe_sec:
        return "late_confirmation_probe_waiting"
    if probe_age > max_probe_sec:
        return "late_confirmation_probe_expired"
    if price_declined:
        return "late_confirmation_price_declined"
    if flu_metric_changed:
        return "late_confirmation_flu_metric_changed"
    return "late_confirmation_probe_no_acceleration"


def _acceleration_reason(target, previous=None):
    source_set = set(_source_signature(target))
    previous_sources = set((previous or {}).get("last_source_signature") or [])
    if "VI_TRIGGERED" in source_set and "VI_TRIGGERED" not in previous_sources:
        return "new_vi_triggered_source"
    if "SUPERNOVA" in source_set and "SUPERNOVA" not in previous_sources:
        return "new_supernova_source"

    rank_jump = _rank_jump(target)
    min_rank_jump = int(getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_RANK_JUMP", 10) or 10)
    if rank_jump >= min_rank_jump:
        return "rank_jump_acceleration"

    spike_rate = _safe_float(target.get("SpikeRate"))
    min_spike = float(getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE", 80.0) or 80.0)
    if spike_rate >= min_spike:
        return "spike_rate_acceleration"

    priority_score = _safe_float(target.get("PriorityScore"))
    min_priority = float(getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE", 80.0) or 80.0)
    if priority_score >= min_priority:
        return "priority_score_acceleration"

    cntr_str = _safe_float(target.get("CntrStr"))
    min_cntr = float(getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_CNTR_STR", 110.0) or 110.0)
    if bool(target.get("CntrStrAvailable", False)) and cntr_str >= min_cntr:
        return "execution_strength_acceleration"

    return ""


def _freshness_score(target):
    """
    `OPEN_TOP`은 하루 종일 순위가 고착되기 쉬워 보조 신호로만 쓰고,
    최근 거래량 급증/체결강도/등락률이 함께 살아난 종목을 앞세웁니다.
    """
    source_bias = {
        "VI+VALUE": 650.0,
        "SUPERNOVA+VALUE": 620.0,
        "VI_TRIGGERED": 560.0,
        "BOTH": 520.0,
        "SUPERNOVA": 460.0,
        "BOTH+VALUE": 430.0,
        "VALUE_TOP": 180.0,
        "OPEN_TOP": 0.0,
    }.get(str(target.get("Source") or "OPEN_TOP"), 0.0)
    priority_score = _bounded(target.get("PriorityScore"), 0.0, 300.0)
    spike_rate = _bounded(target.get("SpikeRate"), 0.0, 350.0)
    flu_rate, _, _ = _scanner_flu_metric(target)
    cntr_str = _bounded(target.get("CntrStr"), 0.0, 180.0)
    trade_value = _safe_positive_int(target.get("TradeValue"))
    source_set = set(target.get("SourceSet") or [])

    trade_value_score = 0.0
    if trade_value > 0:
        trade_value_score = min(220.0, log10(max(trade_value, 1)) * 30.0)

    rank_jump_score = min(260.0, _rank_jump(target) * 5.0)

    vi_score = 0.0
    if "VI_TRIGGERED" in source_set:
        vi_score = 320.0 + min(_safe_positive_int(target.get("VIMotionCount")), 5) * 30.0

    source_count_score = min(320.0, max(0, len(source_set) - 1) * 100.0)
    flu_score = _bounded(flu_rate * 8.0, 0.0, 220.0)

    return (
        source_bias
        + priority_score
        + spike_rate
        + flu_score
        + cntr_str
        + trade_value_score
        + rank_jump_score
        + vi_score
        + source_count_score
    )


def _merge_candidate(candidate_pool, raw_target, source):
    code = kiwoom_utils.normalize_stock_code(raw_target.get("Code", raw_target.get("code", "")))
    if not code:
        return

    name = raw_target.get("Name", raw_target.get("name", ""))
    current = candidate_pool.setdefault(
        code,
        {
            "Code": code,
            "Name": name,
            "FluRate": 0.0,
            "LegacyMaxFluRate": 0.0,
            "CntrStr": 0.0,
            "Price": 0,
            "Source": source,
            "SourceSet": set(),
            "PriorityScore": 0.0,
            "SpikeRate": 0.0,
            "TradeValue": 0,
            "RankNow": 0,
            "RankPrev": 0,
            "VIMotionCount": 0,
            "VIReleaseTime": "",
            "CntrStrAvailable": False,
        },
    )

    current["SourceSet"].add(source)
    if name:
        current["Name"] = name

    raw_flu_value = raw_target.get("FluRate", raw_target.get("flu_rate"))
    raw_flu_present = raw_flu_value not in (None, "")
    raw_flu_rate = _safe_float(raw_flu_value)
    current["LegacyMaxFluRate"] = max(current.get("LegacyMaxFluRate", 0.0), raw_flu_rate)
    if source == "OPEN_TOP":
        open_flu_value = raw_target.get("OpenFluRate", raw_flu_value)
        if open_flu_value not in (None, ""):
            current["OpenFluRate"] = _safe_float(open_flu_value)
        if "DayFluRate" in raw_target:
            current["DayFluRate"] = _safe_float(raw_target.get("DayFluRate"))
        if "OpenPrice" in raw_target:
            current["OpenPrice"] = _safe_positive_int(raw_target.get("OpenPrice"))
    elif source == "VALUE_TOP":
        if raw_flu_present:
            current["ValueFluRate"] = raw_flu_rate
            current.setdefault("DayFluRate", raw_flu_rate)
    elif source == "VI_TRIGGERED":
        if raw_flu_present:
            current["ViFluRate"] = raw_flu_rate
    elif source == "SUPERNOVA":
        if raw_flu_present:
            current["SupernovaFluRate"] = raw_flu_rate
    strength_value, strength_available = _extract_strength_value(raw_target)
    if strength_available:
        current["CntrStr"] = max(current.get("CntrStr", 0.0), strength_value)
        current["CntrStrAvailable"] = True
    current["PriorityScore"] = max(current.get("PriorityScore", 0.0), _safe_float(raw_target.get("PriorityScore", raw_target.get("priority_score"))))
    current["SpikeRate"] = max(current.get("SpikeRate", 0.0), _safe_float(raw_target.get("SpikeRate", raw_target.get("spike_rate"))))
    current["TradeValue"] = max(current.get("TradeValue", 0), _safe_positive_int(raw_target.get("TradeValue", raw_target.get("trade_value"))))
    current["VIMotionCount"] = max(current.get("VIMotionCount", 0), _safe_positive_int(raw_target.get("VIMotionCount")))

    price = _safe_positive_int(raw_target.get("Price", raw_target.get("cur_prc")))
    if price > 0:
        current["Price"] = price
    if "OPEN_TOP" in current["SourceSet"]:
        open_price = _safe_positive_int(current.get("OpenPrice"))
        current_price = _safe_positive_int(current.get("Price"))
        if open_price > 0 and current_price > 0:
            current["OpenFluRate"] = round(((current_price - open_price) / open_price) * 100.0, 2)

    rank_now = _safe_int(raw_target.get("RankNow"))
    rank_prev = _safe_int(raw_target.get("RankPrev"))
    if rank_now > 0:
        current["RankNow"] = rank_now
    if rank_prev > 0:
        current["RankPrev"] = rank_prev
    vi_release_time = str(raw_target.get("VIReleaseTime") or "").strip()
    if vi_release_time:
        current["VIReleaseTime"] = max(str(current.get("VIReleaseTime") or ""), vi_release_time)

    current["Source"] = _representative_source(current["SourceSet"])
    scanner_flu_rate, scanner_flu_metric, scanner_flu_source = _scanner_flu_metric(current)
    current["FluRate"] = scanner_flu_rate
    current["ScannerFluRate"] = scanner_flu_rate
    current["ScannerFluRateMetric"] = scanner_flu_metric
    current["ScannerFluRateSource"] = scanner_flu_source


def build_candidate_pool(
    soaring_targets=None,
    supernova_targets=None,
    value_targets=None,
    vi_targets=None,
):
    candidate_pool = {}
    for target in soaring_targets or []:
        _merge_candidate(candidate_pool, target, "OPEN_TOP")
    for target in supernova_targets or []:
        _merge_candidate(candidate_pool, target, "SUPERNOVA")
    for target in value_targets or []:
        _merge_candidate(candidate_pool, target, "VALUE_TOP")
    for target in vi_targets or []:
        _merge_candidate(candidate_pool, target, "VI_TRIGGERED")
    return candidate_pool


def rank_candidates(candidate_pool):
    return sorted(
        candidate_pool.values(),
        key=lambda item: (
            _source_priority(item.get("Source")),
            -_freshness_score(item),
            -_safe_float(item.get("FluRate")),
        ),
    )


def _filter_picks_within_cooldown(recent_picks, now_ts, reentry_cooldown_sec):
    max_probe_sec = int(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MAX_SEC", 300) or 300)
    return {
        code: meta
        for code, meta in (recent_picks or {}).items()
        if (
            (now_ts - float(meta.get("last_promoted_at", 0.0) or 0.0)) < reentry_cooldown_sec
            or (
                str(meta.get("scanner_probe_state") or "") == "first_seen_probe"
                and (now_ts - float(meta.get("first_seen_at", 0.0) or 0.0)) <= max_probe_sec
            )
        )
    }


def _should_promote_candidate(target, recent_picks, now_ts, reentry_cooldown_sec):
    code = target.get("Code")
    previous = (recent_picks or {}).get(code)
    if not previous:
        return True
    if str(previous.get("scanner_probe_state") or "") == "first_seen_probe":
        return True
    if (now_ts - float(previous.get("last_promoted_at", 0.0) or 0.0)) >= reentry_cooldown_sec:
        return True

    current_sources = set(_source_signature(target))
    previous_sources = set(previous.get("last_source_signature") or [])
    if len(current_sources) > len(previous_sources):
        return True
    if "VALUE_TOP" in current_sources and "VALUE_TOP" not in previous_sources:
        return True
    if "VI_TRIGGERED" in current_sources and "VI_TRIGGERED" not in previous_sources:
        return True

    current_score = _freshness_score(target)
    previous_score = float(previous.get("last_score", 0.0) or 0.0)
    return previous_score > 0 and current_score >= previous_score * 1.2


def _scanner_real_source_guard_decision(target, recent_picks, now_ts):
    if not bool(getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED", False)):
        return {"blocked": False, "reason": "guard_disabled"}

    source_signature = _source_signature(target)
    source_set = set(source_signature)
    previous = (recent_picks or {}).get(target.get("Code")) or {}
    candidate_role = _scanner_candidate_role(target)
    acceleration_reason = _acceleration_reason(target, previous)
    first_price = _safe_positive_int(previous.get("first_price"))
    current_price = _safe_positive_int(target.get("Price"))
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    legacy_unknown_flu_anchor = bool(previous) and previous.get("first_flu_rate") not in (None, "") and (
        not previous.get("first_flu_rate_metric") or not previous.get("first_flu_rate_source")
    )
    previous_flu_metric = str(
        previous.get("first_flu_rate_metric") or ("legacy_unknown_flu_rate" if legacy_unknown_flu_anchor else current_flu_metric)
    )
    previous_flu_source = str(
        previous.get("first_flu_rate_source") or ("legacy_unknown" if legacy_unknown_flu_anchor else current_flu_source)
    )
    first_flu = _safe_float(previous.get("first_flu_rate"), current_flu)
    flu_metric_changed = bool(previous) and (
        previous_flu_metric != current_flu_metric or previous_flu_source != current_flu_source
    )
    price_delta = _price_delta_pct(first_price, current_price)
    flu_delta = current_flu - first_flu
    comparable_flu_delta = 0.0 if flu_metric_changed else flu_delta
    observed_context = {
        "first_seen_flu_rate": f"{first_flu:.2f}",
        "current_flu_rate": f"{current_flu:.2f}",
        "first_flu_rate_metric": previous_flu_metric,
        "current_flu_rate_metric": current_flu_metric,
        "first_flu_rate_source": previous_flu_source,
        "current_flu_rate_source": current_flu_source,
        "flu_metric_changed": flu_metric_changed,
        "first_price": str(first_price or current_price or "-"),
        "current_price": str(current_price or "-"),
        "price_delta_since_first_seen_pct": f"{price_delta:.2f}",
        "flu_delta_since_first_seen": f"{flu_delta:.2f}",
        "comparable_flu_delta_since_first_seen": f"{comparable_flu_delta:.2f}",
        "last_promoted_at": str(previous.get("last_promoted_at") or "-"),
    }

    if candidate_role == "early_discovery":
        return {
            "blocked": False,
            "reason": acceleration_reason or "early_discovery_source_present",
            "candidate_role": candidate_role,
            "acceleration_reason": acceleration_reason,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if acceleration_reason:
        return {
            "blocked": False,
            "reason": acceleration_reason,
            "candidate_role": candidate_role,
            "acceleration_reason": acceleration_reason,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if not bool(getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN", True)):
        return {
            "blocked": False,
            "reason": "late_first_seen_guard_disabled",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    min_probe_sec = int(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_SEC", 30) or 30)
    max_probe_sec = int(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MAX_SEC", 300) or 300)
    min_price_delta = float(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT", 0.15) or 0.15)
    min_flu_delta = float(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT", 0.30) or 0.30)

    if not previous:
        return {
            "blocked": True,
            "reason": "late_confirmation_first_seen_probe",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            "first_seen_flu_rate": f"{current_flu:.2f}",
            "current_flu_rate": f"{current_flu:.2f}",
            "first_flu_rate_metric": current_flu_metric,
            "current_flu_rate_metric": current_flu_metric,
            "first_flu_rate_source": current_flu_source,
            "current_flu_rate_source": current_flu_source,
            "flu_metric_changed": False,
            "first_price": str(current_price or "-"),
            "current_price": str(current_price or "-"),
            "price_delta_since_first_seen_pct": "0.00",
            "flu_delta_since_first_seen": "0.00",
            "comparable_flu_delta_since_first_seen": "0.00",
            "probe_age_sec": "0.0",
            "last_promoted_at": "-",
        }

    first_seen_at = float(previous.get("first_seen_at", 0.0) or 0.0)
    probe_age = max(0.0, now_ts - first_seen_at) if first_seen_at > 0 else 0.0
    observed_context["probe_age_sec"] = f"{probe_age:.1f}"
    price_declined = first_price > 0 and current_price > 0 and current_price < first_price
    probe_confirmed = (
        min_probe_sec <= probe_age <= max_probe_sec
        and not price_declined
        and (price_delta >= min_price_delta or comparable_flu_delta >= min_flu_delta)
    )
    if probe_confirmed:
        return {
            "blocked": False,
            "reason": "probe_acceleration_confirmed",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if source_set != {"VALUE_TOP"}:
        reason = _late_confirmation_probe_block_reason(
            probe_age=probe_age,
            min_probe_sec=min_probe_sec,
            max_probe_sec=max_probe_sec,
            price_declined=price_declined,
            flu_metric_changed=flu_metric_changed,
        )
        return {
            "blocked": True,
            "reason": reason,
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if not bool(getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY", True)):
        return {
            "blocked": False,
            "reason": "value_top_only_guard_disabled",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }
    if bool(target.get("CntrStrAvailable", False)):
        return {
            "blocked": False,
            "reason": "strength_available",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    max_decline = float(getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT", 0.0) or 0.0)
    flu_declined = False if flu_metric_changed else current_flu < (first_flu - max_decline)

    price_declined = first_price > 0 and current_price > 0 and current_price < first_price

    previous_signature = tuple(previous.get("last_source_signature") or ())
    same_source_family = previous_signature == source_signature

    if same_source_family and (flu_declined or price_declined):
        return {
            "blocked": True,
            "reason": "value_top_only_repeat_deteriorating_without_strength",
            "source_signature": ",".join(source_signature),
            "first_seen_flu_rate": f"{first_flu:.2f}",
            "current_flu_rate": f"{current_flu:.2f}",
            "first_flu_rate_metric": previous_flu_metric,
            "current_flu_rate_metric": current_flu_metric,
            "first_flu_rate_source": previous_flu_source,
            "current_flu_rate_source": current_flu_source,
            "flu_metric_changed": flu_metric_changed,
            "first_price": str(first_price or "-"),
            "current_price": str(current_price or "-"),
            "price_delta_since_first_seen_pct": f"{price_delta:.2f}",
            "flu_delta_since_first_seen": f"{flu_delta:.2f}",
            "comparable_flu_delta_since_first_seen": f"{comparable_flu_delta:.2f}",
            "last_promoted_at": str(previous.get("last_promoted_at") or "-"),
        }

    reason = _late_confirmation_probe_block_reason(
        probe_age=probe_age,
        min_probe_sec=min_probe_sec,
        max_probe_sec=max_probe_sec,
        price_declined=price_declined,
        flu_metric_changed=flu_metric_changed,
    )
    return {
        "blocked": True,
        "reason": reason,
        "candidate_role": candidate_role,
        "source_signature": ",".join(source_signature),
        **observed_context,
    }


def _remember_pick(recent_picks, target, now_ts):
    previous = recent_picks.get(target["Code"]) or {}
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    recent_picks[target["Code"]] = {
        "last_promoted_at": now_ts,
        "last_source_signature": _source_signature(target),
        "last_score": _freshness_score(target),
        "first_seen_at": previous.get("first_seen_at", now_ts),
        "first_flu_rate": previous.get("first_flu_rate", current_flu),
        "first_flu_rate_metric": previous.get("first_flu_rate_metric", current_flu_metric),
        "first_flu_rate_source": previous.get("first_flu_rate_source", current_flu_source),
        "first_price": previous.get("first_price", _safe_positive_int(target.get("Price"))),
        "last_flu_rate": current_flu,
        "last_flu_rate_metric": current_flu_metric,
        "last_flu_rate_source": current_flu_source,
        "last_price": _safe_positive_int(target.get("Price")),
        "scanner_probe_state": "promoted",
    }


def _remember_guard_block(recent_picks, target, now_ts, reason):
    previous = recent_picks.get(target["Code"]) or {}
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    reset_probe_anchor = reason == "late_confirmation_flu_metric_changed"
    first_seen_at = now_ts if reset_probe_anchor else previous.get("first_seen_at", now_ts)
    first_flu_rate = current_flu if reset_probe_anchor else previous.get("first_flu_rate", current_flu)
    first_flu_metric = (
        current_flu_metric if reset_probe_anchor else previous.get("first_flu_rate_metric", current_flu_metric)
    )
    first_flu_source = (
        current_flu_source if reset_probe_anchor else previous.get("first_flu_rate_source", current_flu_source)
    )
    first_price = (
        _safe_positive_int(target.get("Price"))
        if reset_probe_anchor
        else previous.get("first_price", _safe_positive_int(target.get("Price")))
    )
    recent_picks[target["Code"]] = {
        **previous,
        "last_guard_blocked_at": now_ts,
        "last_guard_block_reason": reason,
        "last_source_signature": _source_signature(target),
        "last_score": _freshness_score(target),
        "first_seen_at": first_seen_at,
        "first_flu_rate": first_flu_rate,
        "first_flu_rate_metric": first_flu_metric,
        "first_flu_rate_source": first_flu_source,
        "first_price": first_price,
        "last_flu_rate": current_flu,
        "last_flu_rate_metric": current_flu_metric,
        "last_flu_rate_source": current_flu_source,
        "last_price": _safe_positive_int(target.get("Price")),
        "scanner_probe_state": "first_seen_probe",
        "last_observed_at": now_ts,
    }


def _scanner_event_fields(target, source_guard=None):
    source_guard = source_guard or {}
    source_signature = source_guard.get("source_signature") or ",".join(_source_signature(target))
    first_price = source_guard.get("first_price")
    current_price = source_guard.get("current_price") or str(_safe_positive_int(target.get("Price")) or "-")
    first_flu = source_guard.get("first_seen_flu_rate")
    current_flu_value, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    current_flu = source_guard.get("current_flu_rate") or f"{current_flu_value:.2f}"
    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "real_scalping_scanner_source_guard_only",
        "source_quality_gate": "scalping_scanner_real_source_guard",
        "window_policy": "intraday_operational_guard",
        "sample_floor": "not_applicable_runtime_guard",
        "primary_decision_metric": "funnel_count",
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,bot_restart_authority,"
            "ai_score_smoothing_live_gate,real_execution_quality_approval"
        ),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_signature": source_signature,
        "scanner_candidate_role": source_guard.get("candidate_role") or _scanner_candidate_role(target),
        "scanner_block_reason": source_guard.get("reason") if source_guard.get("blocked") else "",
        "scanner_promotion_reason": "" if source_guard.get("blocked") else source_guard.get("reason"),
        "first_seen_price": first_price,
        "current_price": current_price,
        "price_delta_since_first_seen_pct": source_guard.get("price_delta_since_first_seen_pct"),
        "first_seen_flu_rate": first_flu,
        "current_flu_rate": current_flu,
        "first_flu_rate_metric": source_guard.get("first_flu_rate_metric"),
        "current_flu_rate_metric": source_guard.get("current_flu_rate_metric") or current_flu_metric,
        "first_flu_rate_source": source_guard.get("first_flu_rate_source"),
        "current_flu_rate_source": source_guard.get("current_flu_rate_source") or current_flu_source,
        "flu_metric_changed": source_guard.get("flu_metric_changed"),
        "flu_delta_since_first_seen": source_guard.get("flu_delta_since_first_seen"),
        "comparable_flu_delta_since_first_seen": source_guard.get("comparable_flu_delta_since_first_seen"),
        "probe_age_sec": source_guard.get("probe_age_sec"),
        "rank_jump": _rank_jump(target),
        "spike_rate": _safe_float(target.get("SpikeRate")),
        "priority_score": _safe_float(target.get("PriorityScore")),
        "cntr_str_available": bool(target.get("CntrStrAvailable", False)),
        "cntr_str": _safe_float(target.get("CntrStr")),
        "current_price_observed": _safe_positive_int(target.get("Price")),
        "current_source": target.get("Source"),
    }


def _log_scanner_candidate_event(stage, target, source_guard=None):
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        str(target.get("Name") or "-"),
        str(target.get("Code") or ""),
        stage,
        fields=_scanner_event_fields(target, source_guard),
    )


def _log_scanner_real_source_guard_block(target, source_guard, now_ts):
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        str(target.get("Name") or "-"),
        str(target.get("Code") or ""),
        "scalping_scanner_real_source_guard_block",
        fields={
            **_scanner_event_fields(target, {**source_guard, "blocked": True}),
            "scanner_real_source_guard_applied": True,
            "scanner_real_source_guard_skip_reason": source_guard.get("reason"),
            "scanner_real_source_guard_block_event_emitted": True,
            "last_promoted_at": source_guard.get("last_promoted_at"),
            "current_cntr_str_available": bool(target.get("CntrStrAvailable", False)),
            "guard_blocked_at_ts": now_ts,
        },
    )


def promote_candidates(db, event_bus, ranked_targets, recent_picks, *, max_new_codes, reentry_cooldown_sec, token=None, now_ts=None):
    now_ts = time.time() if now_ts is None else now_ts
    new_codes_found = []
    recent_picks = _filter_picks_within_cooldown(recent_picks, now_ts, reentry_cooldown_sec)

    for target in ranked_targets:
        code = target["Code"]
        if not _should_promote_candidate(target, recent_picks, now_ts, reentry_cooldown_sec):
            continue

        source_guard = _scanner_real_source_guard_decision(target, recent_picks, now_ts)
        if source_guard.get("blocked"):
            _log_scanner_candidate_event("scalping_scanner_candidate_observed", target, {**source_guard, "blocked": True})
            _log_scanner_real_source_guard_block(target, source_guard, now_ts)
            print(
                "🧯 [SCALPING 스캐너 guard] "
                f"{target['Name']}({code}) real WATCHING 승격 차단 "
                f"reason={source_guard.get('reason')} "
                f"source_signature={source_guard.get('source_signature')} "
                f"first_flu={source_guard.get('first_seen_flu_rate')} "
                f"current_flu={source_guard.get('current_flu_rate')} "
                f"flu_delta={source_guard.get('flu_delta_since_first_seen')} "
                f"flu_metric={source_guard.get('current_flu_rate_metric')} "
                f"flu_source={source_guard.get('current_flu_rate_source')} "
                f"price_delta={source_guard.get('price_delta_since_first_seen_pct')} "
                f"probe_age={source_guard.get('probe_age_sec')} "
                f"last_promoted_at={source_guard.get('last_promoted_at')}"
            )
            _remember_guard_block(recent_picks, target, now_ts, source_guard.get("reason"))
            continue

        curr_p = float(target.get("Price", 0))
        if not kiwoom_utils.is_valid_stock(code, target["Name"], token=token, current_price=curr_p):
            _remember_pick(recent_picks, target, now_ts)
            continue

        score = _freshness_score(target)
        source_sig = ",".join(_source_signature(target))
        print(
            f"🎯 [타겟 포착] {target['Name']} "
            f"(등락률: +{target['FluRate']}%, 체결강도: {_format_strength_display(target)}, "
            f"신선도점수: {score:.1f} | 출처: {target['Source']} [{source_sig}])"
        )
        try:
            with db.get_session() as session:
                today_date = datetime.now().date()

                record = db.find_reusable_watching_record(
                    session,
                    rec_date=today_date,
                    stock_code=code,
                    strategy='SCALPING',
                )

                if record:
                    record.stock_name = target['Name']
                    if record.status in ('WATCHING', 'COMPLETED', 'EXPIRED'):
                        record.strategy = 'SCALPING'
                        record.buy_price = curr_p
                        record.entry_armed_at_epoch = now_ts
                        record.status = 'WATCHING'
                        record.position_tag = 'SCANNER'
                else:
                    new_record = RecommendationHistory(
                        rec_date=today_date,
                        stock_code=code,
                        stock_name=target['Name'],
                        buy_price=curr_p,
                        trade_type='SCALP',
                        strategy='SCALPING',
                        status='WATCHING',
                        position_tag='SCANNER',
                        entry_armed_at_epoch=now_ts,
                    )
                    session.add(new_record)
        except Exception as e:
            log_error(f"⚠️ DB 저장 실패 ({code}): {e}")
            continue

        if bool(getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED", False)):
            _log_scanner_candidate_event("scalping_scanner_candidate_promoted", target, source_guard)
        _remember_pick(recent_picks, target, now_ts)
        new_codes_found.append(code)

        if len(new_codes_found) >= max_new_codes:
            break

    if new_codes_found:
        event_bus.publish("COMMAND_WS_REG", {"codes": new_codes_found})
        print(f"📡 웹소켓 감시 등록 요청 완료: {len(new_codes_found)} 종목")

    return new_codes_found, recent_picks


def _fetch_scan_source(source_name, fetcher, *args, **kwargs):
    try:
        return fetcher(*args, **kwargs) or []
    except Exception as exc:
        log_error(f"🚨 [SCALPING 스캐너] {source_name} 조회 실패: {exc}")
        return []


def run_scalper_iteration(
    *,
    token,
    radar,
    db,
    event_bus,
    recent_picks,
    reentry_cooldown_sec,
    max_new_codes,
    open_top_limit,
    supernova_limit,
):
    soaring_targets = _fetch_scan_source(
        "ka10028 시가대비 상위",
        kiwoom_utils.get_top_open_fluctuation_ka10028,
        token,
        mrkt_tp="000",
        limit=open_top_limit,
    )
    supernova_targets = _fetch_scan_source(
        "Supernova 수급 급증",
        radar.find_supernova_targets,
        mrkt_tp="000",
        candidate_limit=supernova_limit,
    )
    value_targets = _fetch_scan_source(
        "ka10032 거래대금 상위",
        kiwoom_utils.get_value_top_ka10032,
        token,
        mrkt_tp="000",
        limit=30,
    )
    vi_targets = _fetch_scan_source(
        "ka10054 VI 발동",
        kiwoom_utils.get_vi_triggered_ka10054,
        token,
        mrkt_tp="000",
        limit=30,
    )

    candidate_pool = build_candidate_pool(
        soaring_targets=soaring_targets,
        supernova_targets=supernova_targets,
        value_targets=value_targets,
        vi_targets=vi_targets,
    )
    ranked_targets = rank_candidates(candidate_pool)
    return promote_candidates(
        db,
        event_bus,
        ranked_targets,
        recent_picks,
        max_new_codes=max_new_codes,
        reentry_cooldown_sec=reentry_cooldown_sec,
        token=token,
    )


# ==========================================
# 🦅 스캘핑 스캐너 (전방 탐색조)
# ==========================================
def run_scalper(is_test_mode=False):
    """
    [역할] 
    2~3분 주기로 시장을 스캔하여 당일 수급이 폭발하거나 급등 전조가 보이는
    '초단타(Scalping)' 타겟을 발굴합니다.
    
    [아키텍처 흐름]
    1. 데이터 수집: kiwoom_utils/signal_radar(REST API)를 호출하여 등락률 상위 및 거래량 급증 종목을 가져옵니다.
    2. 필터링: is_valid_stock을 통해 동전주, ETF, 스팩주 등의 불순물을 걸러냅니다.
    3. DB 저장: 발굴된 종목을 SQLAlchemy ORM을 사용하여 안전하게 Upsert(삽입/업데이트) 합니다.
    4. 이벤트 발행: 'COMMAND_WS_REG' 이벤트를 EventBus에 쏘아, 웹소켓 모듈이 해당 종목의 실시간 틱 데이터 감시를 즉각 시작하도록 지시합니다.
    """
    print("⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (장초반/후반 2분, 그 외 3분 주기)...")
    db = DBManager()
    event_bus = EventBus() # 💡 전역 싱글톤 이벤트 버스
    
    # 같은 종목을 하루 종일 영구 제외하면 초반에 잡힌 이름만 오래 남게 됩니다.
    # 그래서 `already_picked` 대신 재등록 cooldown을 둬서, 한동안은 쉬게 하되
    # 다시 거래가 살아난 종목은 같은 날에도 재포착할 수 있게 만듭니다.
    recent_picks = {}
    last_closed_msg_time = 0 # 💡 장 마감 도배 방지용 타이머 추가
    reentry_cooldown_sec = 25 * 60
    max_new_codes = 12
    open_top_limit = 60
    supernova_limit = 30

    # 💡 무한 루프 밖에서 토큰과 레이더를 한 번만 초기화하여 부하 감소
    # (실제 운영 시에는 토큰 만료를 대비한 갱신 로직이 추가로 필요할 수 있음)
    
    token = kiwoom_utils.get_kiwoom_token()
    
    if not token:
        log_error("❌ 키움 토큰 발급 실패. 스캐너를 종료합니다.")
        return

    radar = SniperRadar(token)

    while True:
        now = datetime.now()
        now_time = now.time()

        from src.engine.error_detectors.process_health import write_heartbeat as _sc_whb
        _sc_whb("scalping_scanner")

        # 장 운영 시간 체크 (09:05 ~ 15:00) - 장 초반 감시 5분 후부터 장 마감 1시간 전까지 가동
        market_open = datetime.strptime("09:05:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:00:00", "%H:%M:%S").time()
        
        if not is_test_mode and not (market_open <= now_time <= market_close):
            if time.time() - last_closed_msg_time > 3600:
                print("🌙 신규 스캘핑 후보 스캔 시간이 아닙니다. 보유/청산 감시는 계속됩니다.")
                last_closed_msg_time = time.time()
            time.sleep(60)
            continue

        scan_interval_sec = _resolve_scan_interval_sec(now_time)
        _, recent_picks = run_scalper_iteration(
            token=token,
            radar=radar,
            db=db,
            event_bus=event_bus,
            recent_picks=recent_picks,
            reentry_cooldown_sec=reentry_cooldown_sec,
            max_new_codes=max_new_codes,
            open_top_limit=open_top_limit,
            supernova_limit=supernova_limit,
        )

        time.sleep(scan_interval_sec)

if __name__ == "__main__":
    run_scalper(is_test_mode=True)
