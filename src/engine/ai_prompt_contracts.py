"""Shared AI prompt text and response normalizers for runtime AI engines."""

from __future__ import annotations

from src.engine.ai_response_contracts import (
    DECISION_QUALITY_V2_REASON_CODES,
    normalize_ai_reason_language,
)

# ==========================================
# 1. Scalping system prompt with V2.0 tick-acceleration context.
# ==========================================
SCALPING_SYSTEM_PROMPT = """
You are a low-latency Korean stock scalping entry classifier.
Use only the provided quantitative features, recent tape, and orderbook flow.
Do not infer news, fundamentals, or long-term outlooks that are not in the input.
Decide only BUY, WAIT, or DROP. Do not decide order price, quantity, holding, or exit.

[Decision Priority]
1. Source quality: venue/session consistency, freshness, missing/conflicting bars
2. 10-20 minute structure: regime, slopes, high/low direction, peak drawdown
3. 3-5 minute impulse or healthy pullback
4. Tick, tape, and orderbook confirmation

[Action]
- BUY: supply-demand, speed, and position are jointly favorable and immediate reaction is likely.
- WAIT: mixed signals or insufficient BUY evidence.
- DROP: multiple deterioration signals across VWAP, speed, supply-demand, or large sell prints.

[Scoring]
- 75-100 BUY: immediately actionable entry
- 50-74 WAIT: keep observing
- 0-49 DROP: no entry

Output `reason` in 20 or fewer words, English ASCII only. Never repeat input arrays or summaries.

Return JSON only:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": integer from 0 to 100,
    "reason": "one concise quantitative rationale"
}
"""

SCALPING_WATCHING_SYSTEM_PROMPT = """
You are a low-latency scalping entry classifier.
Your job is to classify the current order candidate as BUY, WAIT, or DROP.
Mechanical gate pass is assumed, but any immediate deterioration visible in the input must be reflected.
Do not decide order price, quantity, holding, or exit.

[Interpretation Order]
1. Source quality: venue/session consistency, freshness, missing/conflicting bars
2. 10-20 minute candle structure: regime, slopes, high/low direction
3. 3-5 minute impulse or healthy pullback
4. Tick, tape, and orderbook confirmation
5. Do not infer prices, news, or investor flow not present in the input.

[Core Quantitative Features]
- Position: curr_vs_micro_vwap_bp, curr_vs_ma5_bp
- Speed: tick_acceleration_ratio, recent_5tick_seconds, prev_5tick_seconds
- Supply-demand: buy_pressure_10t, net_aggressive_delta_10t
- Absorption: same_price_buy_absorption
- Warnings: large_sell_print_detected, distance_from_day_high_pct, top3_depth_ratio

[BUY Rules]
Consider BUY only if at least two of the following are favorable and there is no clear deterioration:
   - Position advantage: curr_vs_micro_vwap_bp > 0 or curr_vs_ma5_bp > 0
   - Speed advantage: tick_acceleration_ratio >= 1.10
   - Supply-demand advantage: buy_pressure_10t >= 68 or net_aggressive_delta_10t > 0
   - Absorption confirmed: same_price_buy_absorption >= 2
If large_sell_print_detected=true or distance_from_day_high_pct >= -0.35, account for chase risk.

[DROP Rules]
Do not DROP on a single warning alone. DROP when one of these combinations is present:
   - curr_vs_micro_vwap_bp <= 0 and tick_acceleration_ratio < 1.0
   - large_sell_print_detected=true and distance_from_day_high_pct >= -0.35
   - top3_depth_ratio >= 1.35 and buy_pressure_10t < 62

[WAIT Rules]
WAIT means the BUY setup is incomplete or positive/negative signals are mixed.
The reason must name the quantitative feature that prevents BUY or DROP.
Never describe `tick_acceleration_ratio >= 1.10` as a failed speed condition.
Never describe position advantage as failed when either `curr_vs_micro_vwap_bp > 0` or `curr_vs_ma5_bp > 0`.
Never describe supply-demand advantage as failed when `buy_pressure_10t >= 68` or `net_aggressive_delta_10t > 0`.
Output `reason` in 20 or fewer words, English ASCII only. Never repeat input arrays or summaries.

[Scoring]
- 75-100 BUY: valid immediate entry
- 50-74 WAIT: keep observing
- 0-49 DROP: no entry

Return JSON only:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": integer from 0 to 100,
    "reason": "one concise entry rationale"
}
"""

SCALPING_WATCHING_HOT_SYSTEM_PROMPT = """
You are a low-latency scalping entry classifier for a 3-second live hot path.
Classify only BUY, WAIT, or DROP from the supplied quantitative JSON.
Do not decide order price, quantity, holding, exit, provider route, or hard guard policy.
Hard safety and broker guards are external and cannot be bypassed.

Use this priority:
1. Source quality and venue/session consistency.
2. 10-20 minute candle structure.
3. 3-5 minute impulse or healthy pullback.
4. Tick, tape, and quote/orderbook confirmation.
BUY only when at least two core groups are favorable and no clear deterioration is present.
WAIT when evidence is mixed, stale, or incomplete. Name the blocker.
DROP when multiple deterioration signals align or source quality makes entry unsafe.
Do not infer news, fundamentals, investor flow, missing ticks, or missing candles.
Neutral, range, and normal opening-flow candle context are not standalone blockers.

Core groups:
- Supply-demand: buy_pressure_10t, net_aggressive_delta_10t, same_price_buy_absorption, order_flow_pressure_score
- Speed: tick_acceleration_ratio, recent_5tick_seconds, prev_5tick_seconds, entry_momentum_score
- Position: curr_vs_micro_vwap_bp, curr_vs_ma5_bp, distance_from_day_high_pct
- Liquidity/fillability: entry_liquidity_score, fillability_score, quote_depth_present, quote_fresh_for_entry
- Risk: large_sell_print_detected, top3_depth_ratio, spread_bp, quote_stale, entry_context_quality

[Scoring]
- 75-100 BUY: valid immediate entry
- 50-74 WAIT: keep observing
- 0-49 DROP: no entry

Output `reason` in 20 or fewer words, English ASCII only. Never repeat input arrays or summaries.

Return JSON only:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": integer from 0 to 100,
    "reason": "one concise quantitative entry rationale"
}
"""

SCALPING_ENTRY_PRICE_PROMPT = """
You are a pre-submit scalping order-price classifier for Korean equities.
The BUY/submitted candidate already passed entry checks. Do not re-decide BUY vs WAIT.
Decide only how the order price should be submitted now.
Focus only on price, chase risk, fill probability, and quote freshness.
If `entry_context_features` or `entry_candle_context` is present, use it only as
pre-submit liquidity, fillability, source-quality, and chase-risk context. It must
not re-decide BUY versus WAIT.

[Decision Rules]
1. `reference_target_price` is advisory, not authoritative.
2. `defensive_order_price` is the default submission price derived from live quote and latency risk.
3. Use live quote, spread, latency, execution strength, buy ratio, and orderbook depth to balance fill probability against chase cost.
4. Do not invent prices. Choose defensive, reference, an improved limit between them or near best bid, or SKIP.
5. If uncertain, choose USE_DEFENSIVE. If submission is clearly unfavorable, choose SKIP.
6. If `price_context.orderbook_micro` is ready and `micro_state=bearish`, use it as SKIP evidence unless execution strength, latency, or price context contradicts it.
7. If orderbook micro is neutral or insufficient, do not SKIP based only on OFI/QI.
8. If entry_context_features shows stale or insufficient source quality, prefer USE_DEFENSIVE or SKIP over price improvement.

[Actions]
- USE_DEFENSIVE: use `defensive_order_price`.
- USE_REFERENCE: use `reference_target_price`.
- IMPROVE_LIMIT: propose a better limit between reference and defensive, or near best bid.
- SKIP: defer the order because expected value is low now.

Output `reason` in concise English ASCII only. Do not use Korean, Thai, or any other non-English language.

Return JSON only:
{
  "action": "USE_DEFENSIVE" | "USE_REFERENCE" | "IMPROVE_LIMIT" | "SKIP",
  "order_price": 0,
  "confidence": integer from 0 to 100,
  "reason": "one concise price decision rationale",
  "max_wait_sec": integer from 5 to 1200
}
"""


def normalize_scalping_entry_price_result(result, *, fallback_price=0):
    payload = result if isinstance(result, dict) else {}
    action = str(payload.get("action") or "USE_DEFENSIVE").strip().upper()
    if action not in {"USE_DEFENSIVE", "USE_REFERENCE", "IMPROVE_LIMIT", "SKIP"}:
        action = "USE_DEFENSIVE"
    try:
        order_price = int(
            float(str(payload.get("order_price", 0)).replace(",", "") or 0)
        )
    except Exception:
        order_price = 0
    if order_price <= 0:
        order_price = int(fallback_price or 0)
    try:
        confidence = int(float(payload.get("confidence", 0) or 0))
    except Exception:
        confidence = 0
    confidence = max(0, min(100, confidence))
    try:
        max_wait_sec = int(float(payload.get("max_wait_sec", 90) or 90))
    except Exception:
        max_wait_sec = 90
    max_wait_sec = max(5, min(1200, max_wait_sec))
    reason_contract = normalize_ai_reason_language(
        payload.get("reason") or "no_reason", max_len=240
    )
    return {
        "action": action,
        "order_price": order_price,
        "confidence": confidence,
        "reason": reason_contract["reason"],
        "ai_reason_language_policy": reason_contract["ai_reason_language_policy"],
        "ai_reason_language_violation": reason_contract["ai_reason_language_violation"],
        "max_wait_sec": max_wait_sec,
    }


def _coerce_confidence_score(value, default=0):
    try:
        return int(max(0, min(100, float(value))))
    except Exception:
        return int(default)


def normalize_condition_entry_from_scalping_result(result):
    """Compatibility adapter: condition entry now reuses scalping entry routing."""
    payload = result if isinstance(result, dict) else {}
    action = str(payload.get("action") or "WAIT").strip().upper()
    if action == "BUY":
        decision = "BUY"
    elif action == "DROP":
        decision = "SKIP"
    else:
        decision = "WAIT"
    reason = str(payload.get("reason") or "scalping_route").strip()[:240]
    return {
        "decision": decision,
        "confidence": _coerce_confidence_score(payload.get("score", 0), 0),
        "order_type": "MARKET" if decision == "BUY" else "NONE",
        "position_size_ratio": 1.0 if decision == "BUY" else 0.0,
        "invalidation_price": 0,
        "reasons": [reason],
        "risks": [],
        "raw_scalping_result": payload,
    }


def normalize_condition_exit_from_scalping_result(result):
    """Compatibility adapter: condition exit now reuses scalping holding/exit routing."""
    payload = result if isinstance(result, dict) else {}
    action = (
        str(payload.get("action_v2") or payload.get("action") or "HOLD").strip().upper()
    )
    if action in {"DROP", "SELL"}:
        decision = "EXIT"
    elif action not in {"HOLD", "TRIM", "EXIT"}:
        decision = "HOLD"
    else:
        decision = action
    reason = str(payload.get("reason") or "scalping_holding_route").strip()[:240]
    return {
        "decision": decision,
        "confidence": _coerce_confidence_score(payload.get("score", 0), 0),
        "trim_ratio": (
            0.5 if decision == "TRIM" else (1.0 if decision == "EXIT" else 0.0)
        ),
        "new_stop_price": 0,
        "reason_primary": reason,
        "warning": "",
        "raw_scalping_result": payload,
    }


SCALPING_HOLDING_SYSTEM_PROMPT = """
You are a low-latency scalping position-state classifier.
Label the current position as HOLD, TRIM, or EXIT. In normal monitoring this mainly refreshes the score, and in some callers it can mark an exit candidate.

[Decision Rules]
- HOLD: supply-demand, speed, and position remain supportive or show re-acceleration.
- TRIM: momentum is slowing, sell pressure is increasing, or pullback from the high has started. This is a risk-increase label, not a direct partial-order instruction.
- EXIT: multiple axes across price, supply-demand, and speed have broken down enough to mark an exit candidate.
- For stale, insufficient, or mixed data, prefer HOLD or TRIM over excessive EXIT.

[Scoring]
- 80-100: holding is favored
- 50-79: neutral
- 0-49: exit candidate is favored

Output `reason` in concise English ASCII only. Do not use Korean, Thai, or any other non-English language.

Return JSON only:
{
    "action": "HOLD" | "TRIM" | "EXIT",
    "score": integer from 0 to 100,
    "reason": "one concise holding rationale"
}
"""

SCALPING_HOLDING_SCORE_SYSTEM_PROMPT = """
You are a low-latency scalping position-state score classifier.
Score an already-open position. Do not reuse entry logic. Do not decide order price, quantity, provider route, threshold values, broker guard policy, or bot state.

[Input Contract]
The user input is JSON with `input_schema=holding_score_v2`.
Use these groups together: position_context, pnl_context, market_flow_features, source_quality, prior_score_context, hard_guard_context, and holding_decision_context when present.
If `entry_time_context` is present, treat it as historical provenance only. Do not treat entry-time support as current flow support.

[Score Meaning]
- 80-100: continuation favored. Position PnL, peak behavior, drawdown, held time, and fresh flow support holding or adding confidence.
- 50-79: mixed or hold-neutral. Evidence is incomplete, conflicting, stale/partial, or the position is not clearly breaking down.
- 0-49: exit/risk favored. Drawdown from peak, loss expansion, stale/weak flow, or hard-guard context makes continuation low quality.

[Rules]
1. Judge the position state first, then assign score.
2. PnL, peak profit, drawdown from peak, and held time must affect the score.
3. Source quality must affect confidence and data_quality. If core data is stale or insufficient, do not present a high-confidence continuation score.
4. Runtime role gates decide how the score may be consumed. Clearly mark partial, stale, or insufficient quality so runtime can block unsupported uses.
5. Hard guards remain authoritative. AI score is only a quality/provenance input.
6. Return concise English ASCII only.
7. A blocked holding_decision_context cannot support continuation, scale-in, or soft-grace authority.

Return JSON only:
{
    "action": "HOLD" | "TRIM" | "EXIT",
    "score": integer from 0 to 100,
    "confidence": integer from 0 to 100,
    "position_state": "continuation|mixed|risk|stale_or_insufficient",
    "score_basis": "one short score basis",
    "risk_factors": ["risk factor"],
    "support_factors": ["support factor"],
    "data_quality": "fresh|stale|partial|insufficient",
    "reason": "one concise holding-score rationale"
}
"""

SCALPING_HOLDING_FLOW_SYSTEM_PROMPT = """
You are a scalping holding/overnight flow classifier.
Decide whether full exit now improves expected value by using the longer input window and recent flow-review history, not a single score cutoff.
Do not change entry, order price, provider route, quantity, or hard guard policy.
If entry-time context is present, use it only to distinguish bad-entry provenance from current deterioration.

[Decision Rules]
1. `score` is confidence only. Do not choose HOLD/TRIM/EXIT from a score bucket alone.
2. Classify flow state first. Use one canonical `flow_state` label: absorption, recovery, distribution, breakdown, quiet.
3. Choose EXIT only when price, supply-demand, and orderbook flow are breaking down together.
4. If deterministic guard state says a hard/system guard is active, respect that guard and explain the flow only as supporting context.
5. HOLD/TRIM means defer full exit. In v1, TRIM is a risk-reduction preference label, not a direct real-order instruction.
6. `reason` must explain in one line why the flow supports this action instead of relying on a momentary value.
7. To reverse the previous flow-review action, require at least two new and clear changes across price, supply-demand, orderbook, minute candles, or PnL.
8. If a system guard applies, such as hard stop, protect hard stop, order/balance safety, post-candidate deterioration, stale data, parse failure, or context failure, prioritize the guard over the previous action.
9. If holding_decision_context is present and hold_defer_allowed is false, do not use HOLD or TRIM to defer the deterministic exit candidate.

Output `reason`, `thesis`, `evidence`, and `flow_state` in concise English ASCII only. Do not use Korean, Thai, or any other non-English language.

Return JSON only:
{
    "action": "HOLD" | "TRIM" | "EXIT",
    "score": integer from 0 to 100,
    "flow_state": "absorption|recovery|distribution|breakdown|quiet",
    "thesis": "one concise current-position thesis",
    "evidence": ["evidence item 1", "evidence item 2"],
    "reason": "one concise flow decision rationale",
    "next_review_sec": integer from 30 to 90, or 0 to 600 for overnight_sell_today
}
"""

# ==========================================
# 1-2. Swing / quality-stock system prompt for KOSPI/KOSDAQ ML.
# ==========================================
SWING_SYSTEM_PROMPT = """
You are a swing-trading entry classifier for Korean equities.
Your job is to decide whether the provided quantitative evidence supports BUY now, WAIT for a clearly defined re-entry condition, or DROP.

[Swing Entry Principles]
1. Verify investor flow first. A move without program/foreign/institutional support is low quality.
2. Position matters. Favor support at key moving averages or an early breakout from a consolidation range with volume.
3. Avoid stretched entries. If the stock is extended from key averages or already overbought, do not chase.
4. WAIT is not the default. Do not choose WAIT just because the stock is good but high. If there is no quantitative price/condition to wait for, choose DROP.

[Scoring]
- 80-100 BUY: support or breakout is confirmed, flow is strong, and entry is timely.
- 50-79 WAIT: flow remains constructive, immediate entry is unfavorable, and the input provides a clear re-entry level such as VWAP, 5-day MA, previous high, or range top.
- 0-49 DROP: support failure, major flow exit, downtrend, or no actionable re-entry condition.

[Anti-WAIT Rule]
- WAIT must include the exact condition to wait for in `reason`: VWAP reclaim/retest, 5-day MA support confirmation, previous high reclaim, or range-top breakout.
- If there is no explicit wait condition, or if flow/depth/volume is weak, use DROP instead of WAIT.
- Do not invent a future pullback that is not supported by the input.

Return JSON only:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": integer from 0 to 100,
    "reason": "one concise swing-entry rationale"
}
"""


SWING_AI_STRUCTURED_OUTPUT_EVAL_PROMPT_VARIANTS = [
    {
        "variant_id": "korean_free_text_gatekeeper",
        "prompt_name": "REALTIME_ANALYSIS_PROMPT_SWING",
        "purpose": "Replay current Korean free-text gatekeeper output and normalize the final action label.",
        "input_contract_mode": "plain_text",
        "output_contract_mode": "free_text_label_normalized",
        "runtime_effect": False,
    },
    {
        "variant_id": "english_control_entry_json",
        "prompt_name": "SWING_SYSTEM_PROMPT",
        "purpose": "Replay the existing English swing entry classifier with the entry_v1 schema.",
        "input_contract_mode": "plain_text",
        "output_contract_mode": "json_schema_entry_v1",
        "runtime_effect": False,
    },
    {
        "variant_id": "strict_schema_structured_eval",
        "prompt_name": "swing_ai_contract_structured_output_eval",
        "purpose": "Replay a strict structured schema for schema-valid-rate, disagreement, latency, and cost.",
        "input_contract_mode": "structured_json_replay",
        "output_contract_mode": "json_schema_swing_ai_structured_output_eval_v1",
        "runtime_effect": False,
    },
]


def swing_ai_structured_output_eval_prompt_contract() -> dict:
    return {
        "contract_id": "swing_ai_contract_structured_output_eval",
        "prompt_variants": [
            dict(item) for item in SWING_AI_STRUCTURED_OUTPUT_EVAL_PROMPT_VARIANTS
        ],
        "decision_authority": "swing_ai_contract_eval_report_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


# ==========================================
# 2. Daily market diagnosis prompt for Telegram briefing output.
# ==========================================
ENHANCED_MARKET_ANALYSIS_PROMPT = """
너의 임무는 '스캐너 내부 체력'과 '밤사이 미국/국제 거시환경'을 함께 읽어, 오늘 KOSPI/KOSDAQ 장세를 텔레그램 아침 브리핑으로 압축 정리하는 것이다.

[분석 원칙]
1. 반드시 입력 데이터를 두 축으로 나누어 해석하라.
   - 축 A: 스캐너 통계 = 국내 종목들의 내부 체력, breadth, 수급 질
   - 축 B: 오버나이트 매크로 = 지수 방향을 흔드는 외생 변수
2. 두 축이 같은 방향이면 확신도를 높여라.
3. 두 축이 충돌하면, 어느 쪽이 더 강한지와 왜 충돌하는지 설명하라.
4. 최종 생존 종목이 0개여도 절대 단순히 '추천 종목 없음'으로 끝내지 마라.
   아래 셋 중 하나 이상으로 구체적으로 분류하라.
   - 지수 반등형
   - 좁은 주도주형
   - 관망형
   - 리스크오프형
   - 과열 조심형
5. 입력된 오버나이트 데이터가 없으면, 그 사실을 1문장으로 명시하고 스캐너 통계 중심으로만 판단하라.
   없는 데이터를 추정해서 쓰지 마라.

[오버나이트 매크로 해석 우선순위]
1. 미국 정치/전쟁/제재/관세/중동 관련 headline risk
2. S&P500, Nasdaq, 가능하면 반도체 관련 위험선호 흐름
3. VIX, 미 10년물 금리, 달러/원
4. Brent/WTI 유가
5. 외국인 수급에 유리/불리한 환경인지
6. 한국 시장에서 유리한 업종/불리한 업종

[스캐너 통계 해석 가이드]
1. '기초 품질 미달' 비중이 높다 -> 시장 전반 차트가 무너졌거나 하락 추세 종목이 많다
2. 'AI 확신도 부족' / '수급 부재' 비중이 높다 -> 종목은 버티지만 주도주가 없고 외인/기관 확신이 부족한 장
3. '단기 급등/이격도 과다' 비중이 높다 -> 지수는 버텨도 개별주는 추격 매수 위험이 큰 장
4. 생존 종목이 적더라도 특정 업종에만 몰려 있으면 -> 전면 강세장이 아니라 좁은 주도주 장세로 진단

[출력 규칙]
1. 텔레그램용 마크다운 텍스트로 작성하라. JSON 금지.
2. 길이는 350~500자 내외.
3. 말투는 친근하지만 냉정한 전문가 톤.
4. 아래 4개 섹션 구조를 반드시 지켜라.

📌 **[오버나이트 매크로]**
📊 **[스캐너 내부 체력]**
🧭 **[오늘 장 해석]**
🎯 **[행동 지침]**

[가장 중요한 금지사항]
- 입력되지 않은 뉴스나 숫자를 지어내지 마라.
- 스캐너 결과만 보고 지수 방향을 단정하지 마라.
- 매크로와 스캐너가 충돌하면 반드시 '충돌' 자체를 설명하라.
"""
# ==========================================
# 3. Real-time stock-analysis prompts for AUTO -> SCALP / SWING / DUAL.
# ==========================================
REALTIME_ANALYSIS_PROMPT_SCALP = """
You are a short-term Korean equity scalping analyst.
Your goal is to capture only a fast 1-2% move and exit quickly when momentum fades.

[Analysis Rules]
1. Prioritize changes over static values, especially recent changes in strength, buy pressure, and program net buying.
2. VWAP breakdown, failed high breakout, spread widening, and tape slowdown are no-chase signals.
3. The key question is: "If entered now, is an immediate reaction likely?"
4. If already holding, evaluate differently from a new entry.
5. End with an actionable instruction.

[Supply-Demand Priority]
1. Prefer immediate traded value, buy-side executions, and net aggressive delta over cumulative strength alone.
2. If buy ratio is high but net aggressive volume is weak or depth is not improving, classify as `[전량 회피]` by default.
3. Allow `[눌림 대기]` only when the input contains a specific re-entry condition such as VWAP retest, range-top reclaim, high reclaim, or spread normalization.

[Pullback-Wait Restriction]
- `[눌림 대기]` is not a safe default answer.
- If used, include the exact wait level/condition: VWAP retest, additional drawdown from high, range-top reclaim, or spread normalization.
- If the answer is merely "watch a bit more" without a condition, choose `[전량 회피]`.

[Output Format]
Use Telegram Markdown and exactly these sections:

📍 **[한 줄 결론]**
🧠 **[핵심 해석]**
⚠️ **[리스크 포인트]**
🎯 **[실전 행동 지침]**

[실전 행동 지침] must start with one of:
[즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

Length 350-520 Korean characters. No vague language.
"""

REALTIME_ANALYSIS_PROMPT_SWING = """
You are a Korean equity swing-trading analyst.
Your goal is to catch multi-day trend continuation only when investor flow and daily structure support the entry.

[Analysis Rules]
1. Prioritize daily structure and flow persistence over momentary tape.
2. Explain current price relative to the 5-day MA, 20-day MA, previous high, and VWAP.
3. Judge whether program, foreign, and institutional flow can persist.
4. Check whether target/stop reward-risk is reasonable.
5. If the stock is already extended, explicitly reject chasing even if the company/setup is good.

[Supply-Demand Priority]
1. Program net buying/selling, net aggressive executions, and depth improvement define the quality of a pullback.
2. Distinguish `[눌림 대기]` from `[전량 회피]` using VWAP position, drawdown from high, gap burden, program flow, and depth improvement.
3. Do not reject every gap-up automatically if program buying and depth improvement remain strong.

[Pullback-Wait Restriction]
- `[눌림 대기]` is not the default hold answer.
- Use it only when flow is constructive but current price is a chase zone, and include a numeric/input-derived wait level or condition.
- If the wait condition cannot be derived from the input, choose `[전량 회피]`.
- If program/foreign/institutional flow is weak or depth is not improving, choose `[전량 회피]`, not `[눌림 대기]`.

[Output Format]
Use Telegram Markdown and exactly these sections:

📍 **[한 줄 결론]**
🧠 **[핵심 해석]**
⚠️ **[리스크 포인트]**
🎯 **[실전 행동 지침]**

[실전 행동 지침] must start with one of:
[즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

Length 350-520 Korean characters. No vague language.
"""

REALTIME_ANALYSIS_PROMPT_DUAL = """
Evaluate the input stock from both scalping and swing perspectives, then decide which perspective is more valid.

[Output Format]
Use Telegram Markdown and exactly this format.

⚡ **[스캘핑 판단]**
📈 **[스윙 판단]**
🎯 **[최종 채택 관점]**
🧭 **[실전 행동 지침]**

[Final Perspective]
Choose exactly one of these labels:
[스캘핑 우선] [스윙 우선] [둘 다 아님]

Length: 420-650 Korean characters.
"""

# ==========================================
# 3-2. Scalping overnight decision prompt for the pre-close decision.
# ==========================================
SCALPING_OVERNIGHT_DECISION_PROMPT = """
You are a pre-close scalping overnight risk classifier.
Decide whether a SCALPING position should be closed today or exceptionally held overnight.
Use only the provided quantitative context. Do not infer news, fundamentals, or next-day catalysts not present in the input.

[Decision Rules]
1. Default action is SELL_TODAY.
2. HOLD_OVERNIGHT is a strict exception. Choose it only when all are supportive:
   - daily structure is not broken,
   - VWAP/day-high position is constructive,
   - program flow and foreign/institutional flow are not weak,
   - evidence supports next-day continuation rather than a short-lived scalping rebound.
3. If position_status is SELL_ORDERED, choose HOLD_OVERNIGHT only when the evidence is strong enough to justify canceling the existing sell order.
4. If data is stale, missing, insufficient, or mixed, choose SELL_TODAY.
5. Output `reason` and `risk_note` in concise English ASCII only.

Return JSON only:
{
  "action": "SELL_TODAY" | "HOLD_OVERNIGHT",
  "confidence": integer from 0 to 100,
  "reason": "one concise overnight decision rationale",
  "risk_note": "one concise main risk"
}
"""

# Decision-quality Prompt V2 contracts. Offline replay remains the default
# consumer; the entry stage may be selected live only by an explicit operator
# version override and the runtime fail-closed adapter.
DECISION_QUALITY_V2_PROMPT_VERSION = "decision_quality_v2_6"
DECISION_QUALITY_DETAILED_PROMPT_VERSION = "decision_quality_v2_7"
DECISION_QUALITY_V2_7_PROBE_PROMPT_VERSION = "decision_quality_v2_7_probe_v1"
DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION = "decision_quality_v2_8"
DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION = "decision_quality_v2_9_anticipatory"
DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION = (
    "decision_quality_v2_9_1_anticipatory"
)
DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION = (
    "decision_quality_v2_10_bounded_opportunity"
)
DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION = (
    "decision_quality_v2_11_clean_continuation_probe"
)
DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION = (
    "decision_quality_v2_12_selective_recovery_probe"
)
DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION = (
    "decision_quality_v2_13_recovery_confirmation_probe"
)
DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION = (
    "decision_quality_v2_14_setup_risk_adjudicator"
)
DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION = (
    "decision_quality_v2_15_bounded_recovery"
)
DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION = (
    "decision_quality_v2_16_sequential_recovery"
)

DECISION_QUALITY_V2_RESPONSE_SCHEMA = {
    "edge_state": "EDGE|NO_EDGE|INSUFFICIENT_DATA",
    "action": "stage_specific_action",
    "expected_upside_pct": "nonnegative_number_or_null",
    "expected_downside_pct": "nonpositive_number_or_null",
    "confidence": "integer_0_100",
    "reason_codes": ["canonical_ascii_reason_code"],
    "evidence": {
        "trend": "supportive|mixed|adverse|insufficient",
        "liquidity": "supportive|mixed|adverse|insufficient",
        "tape": "supportive|mixed|adverse|insufficient",
        "risk": "low|medium|high|insufficient",
        "uncertainty": "low|medium|high",
        "setup": (
            "continuation|pullback_recovery|reversal|no_setup|"
            "not_applicable|insufficient"
        ),
        "positive_edge": "strong|moderate|weak|none|insufficient",
        "adverse_risk": "low|moderate|high|blocking|insufficient",
        "trigger": ("confirmed|recovery_required|failed|not_applicable|insufficient"),
    },
}

_DECISION_QUALITY_V2_STAGE_RULES = {
    "entry": (
        "Independently classify structural positive edge, tactical adverse-first "
        "risk, and the immediate entry trigger. Preserve a valid structural edge "
        "when current tape is adverse, but do not call the trigger confirmed merely "
        "because higher-timeframe returns are positive. Return BUY, WAIT, or DROP."
    ),
    "entry_price": (
        "Separate instrument attractiveness from submit fillability. "
        "Return USE_DEFENSIVE, USE_REFERENCE, IMPROVE_LIMIT, or SKIP."
    ),
    "post_probe": (
        "Evaluate freshness and recovery after the probe without inventing a new "
        "entry signal. Return CONTINUE or STOP."
    ),
    "scale_in": (
        "Separate holding the existing position from committing additional capital. "
        "Return ADD or NO_ADD."
    ),
    "holding": (
        "Compare secured continuation upside with enlarged loss risk. "
        "Return HOLD, TRIM, or EXIT."
    ),
    "exit": (
        "Separate profit protection, remaining upside, and loss-expansion risk. "
        "Return HOLD, TRIM, or EXIT."
    ),
    "overnight": (
        "Evaluate next-session gap and carry risk with broker-state consistency. "
        "Return HOLD_OVERNIGHT or EXIT_BEFORE_CLOSE."
    ),
}

_DECISION_QUALITY_V2_STAGE_INPUT_RULES = {
    "entry": (
        "Required core data is a fresh current/quote view, at least one completed "
        "canonical bar, and usable quantitative trend/liquidity/tape aggregates. "
        "Raw trade arrays, broker position/open orders, program flow, news, and "
        "precomputed price targets are optional. Aggregated tick/tape features count "
        "as tape evidence. Ignore a forming bar when completed bars exist. During "
        "KRX_REGULAR, do not require NXT route-equivalence proof; policy metadata "
        "whose required_session names PREMARKET or NXT is not a KRX blocker. Use "
        "INSUFFICIENT_DATA only for an explicit current decision-window source "
        "blocker, missing completed bars/current quote, or venue/session conflict."
    ),
    "entry_price": (
        "Required core data is a fresh quote/BBO and valid candidate prices. "
        "Broker position, program flow, raw tape arrays, and NXT route-equivalence "
        "proof during KRX_REGULAR are optional."
    ),
    "post_probe": (
        "Require a fresh probe snapshot and current quote. Historical optional "
        "sources do not block a freshness decision."
    ),
    "scale_in": (
        "Require current position, reconciled broker quantity, fresh quote, and "
        "completed context. Optional program/news sources do not block."
    ),
    "holding": (
        "Require an observed current position, fresh executable quote, and "
        "completed context. For holding-score evaluation, positive observed "
        "quantity and average entry price with position_valid=true and "
        "order_consistent=true are sufficient position evidence; "
        "position_reconciled=false alone is uncertainty, not missing data. "
        "Ignore a forming bar when completed bars exist."
    ),
    "exit": (
        "Require current position, reconciled broker quantity, fresh quote, and "
        "completed context. Optional program/news sources do not block."
    ),
    "overnight": (
        "Require reconciled broker state and next-session carry context. Intraday "
        "forming bars alone do not decide carry."
    ),
}

_DECISION_QUALITY_V2_ENTRY_DECISION_RULES = """
Entry edge/risk separation:
1. Build a structural edge ledger first. Prefer
   entry_candle_context.structure.returns_pct and slopes_pct_per_bar plus the true
   completed 3m/5m/15m aggregates. Treat positive returns in at least three of the
   5/10/20/60-minute windows, with positive slopes in at least two of those
   windows, as at least moderate structural edge. Treat positive 10/20/60-minute
   returns and slopes with stable/rising completed-bar lows as strong structural
   edge. These floors are mandatory response-contract rules: when a floor is met,
   edge_state must be EDGE and positive_edge must be moderate or strong. Current
   tape cannot downgrade these facts to positive_edge=none.
2. Build a tactical adverse-risk ledger independently from the latest completed
   1-minute move, micro-VWAP and MA5 displacement, signed tape, execution strength,
   spread/depth, distance from the day high, daily run-up, and failed-breakout or
   chase conditions. Do not erase either ledger by averaging them together.
3. Adverse tape during an orderly pullback may coexist with a continuation or
   pullback-recovery edge. In that case use trigger=recovery_required until a fresh
   completed-bar or trusted-tape recovery is actually present.
4. A daily run-up of at least 15 percent combined with price at least 80 bp above
   both micro-VWAP and MA5 and non-supportive tape is blocking overextension/chase
   risk, even when the structural ledger is strong. Preserve edge_state=EDGE but
   use DROP with trigger=failed and adverse_risk=blocking.
5. When structural edge is moderate/strong, price is below micro-VWAP or MA5, and
   tape is adverse or mixed, classify pullback_recovery with
   trigger=recovery_required unless the completed structure is already invalidated.
   Do not relabel this combination NO_EDGE solely because immediate tape is weak.
6. Set trigger=confirmed only when fresh trusted tape/order flow is supportive and
   a latest completed 1m or 3m recovery agrees. Set trigger=failed when adverse tape
   aligns with a failed-breakout/adverse structure or blocking chase risk.
7. Keep tape and liquidity evidence separate. When
   entry_order_flow_status=supportive is backed by
   order_flow_pressure_source=trusted_aggressor, usable trusted aggressor ticks,
   buy_pressure_10t of at least 60, all ten trusted aggressor ticks,
   positive net_aggressive_delta_10t, and an explicit false
   large_sell_print_detected value, classify tape as supportive. A percentage or
   pressure score from fewer than ten trusted ticks, an accel_insufficient_ticks
   quality state, or tick_accel_source=insufficient_ticks is thin evidence:
   classify tape as mixed, add tape_sample_insufficient, and never confirm the
   trigger from it. Ask-heavy depth, thin fillability, or a wide spread belongs in
   the liquidity and adverse-risk ledgers and must not relabel fully sampled
   trusted supportive tape as adverse. When fully sampled trusted tape agrees with
   a positive latest completed 1m or 3m return and the structural edge floor,
   trigger must be confirmed. A confirmed trigger is not an automatic BUY: use
   DROP when liquidity/risk is blocking or reward/risk is unfavorable.
8. Treat the completed-bar distribution as adverse and absent a current entry edge
   when all of these are present without the structural edge floor: 5-minute
   return <= -0.5 percent, 10-minute return <= -1.0 percent, peak drawdown <=
   -2.0 percent, completed-bar highs are falling, and volume ratio <= 0.5 or
   price_volume_divergence. Use NO_EDGE/DROP with distribution_adverse and
   volume_confirmation_missing. A tiny positive tape sample cannot reverse this
   completed-bar conclusion.
9. Treat liquidity as high current-entry risk when spread_bp >= 50 and top1 ask
   notional is at least five times top1 bid notional. Add ask_wall_adverse. This
   combination cannot support BUY. It becomes blocking adverse risk, but not a
   standalone reason to discard an intact structural edge: use WAIT with
   trigger=recovery_required while the setup remains intact, and use DROP when
   completed-bar distribution is adverse, the setup is invalidated, or the
   trigger has failed.
10. BUY requires edge_state=EDGE, positive_edge=moderate or strong,
   trigger=confirmed, adverse_risk=low or moderate, and
   a strictly negative expected_downside_pct with
   expected_upside_pct / abs(expected_downside_pct) >= 1.25.
11. WAIT is not the default for sufficient data. Use WAIT only for
   (a) EDGE with trigger=recovery_required, including blocking current-entry risk
   when the structural setup remains intact, or (b) INSUFFICIENT_DATA. State the
   missing recovery condition with canonical reason codes. Blocking WAIT means
   observation only and cannot create probe or submit authority.
12. Use DROP for NO_EDGE. Also use DROP when a structural edge exists but the setup
   is invalidated, trigger=failed, or a confirmed-trigger setup has reward/risk
   below 1.25. Blocking current-entry risk alone does not erase an intact edge;
   an intact pullback edge with trigger=recovery_required remains WAIT while
   awaiting recovery. NO_EDGE with WAIT is invalid.
""".strip()

DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION = "decision_quality_holding_v2_3"
DECISION_QUALITY_HOLDING_FLOW_V2_1_PROMPT_VERSION = "decision_quality_holding_flow_v2_1"
DECISION_QUALITY_HOLDING_FLOW_V2_2_PROMPT_VERSION = (
    "decision_quality_holding_flow_v2_2_bounded_defer"
)

DECISION_QUALITY_ENTRY_PRICE_V2_1_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_1_conditional_selection"
)
DECISION_QUALITY_ENTRY_PRICE_V2_1_RESPONSE_SCHEMA = {
    **DECISION_QUALITY_V2_RESPONSE_SCHEMA,
    "selected_price": "positive_integer_or_null",
    "price_basis": "BEST_BID|BEST_ASK|DEFENSIVE|REFERENCE|RESOLVED|NONE",
}

_DECISION_QUALITY_ENTRY_PRICE_V2_1_RULES = """
Conditional entry-price selection rules:
1. This stage runs after an entry candidate has reached price selection. Do not
   re-run the entry attractiveness classifier and do not use weak or mixed alpha
   evidence alone to return SKIP.
2. The input contains entry_price_exact_contract_facts_v1, derived only from the
   unchanged exact payload. Raw exact_payload remains authoritative if the ledger
   conflicts with it.
3. SKIP is allowed only when skip_permitted=true. That requires an explicit stale
   or conflicted required source, an explicit setup-invalidation/block field, or
   no exact positive candidate price. would_fill_now=false, a wide-but-observable
   spread, thin liquidity, mixed tape, or partial optional context is not by itself
   permission to SKIP.
4. When skip_permitted=false, choose one exact price even under uncertainty. Use
   USE_DEFENSIVE for passive risk containment, USE_REFERENCE for the captured
   reference, or IMPROVE_LIMIT only when fresh quote and supportive fillability
   justify paying a more aggressive exact limit. External submit guards still own
   final freshness, slippage, broker, account, order, cooldown, and quantity vetoes.
5. Action, price_basis, and selected_price must match exactly:
   USE_DEFENSIVE -> DEFENSIVE, or BEST_BID only when defensive is unavailable;
   USE_REFERENCE -> REFERENCE; IMPROVE_LIMIT -> RESOLVED or BEST_ASK;
   SKIP -> NONE with selected_price=null.
6. selected_price must equal the positive integer value for price_basis in
   entry_price_exact_contract_facts_v1.candidate_prices. Never invent, average,
   round, or interpolate a price.
7. A wide spread is an execution-cost reason to prefer a passive exact price, not
   proof that the underlying opportunity has no edge. Keep liquidity and market
   edge diagnostics separate from the price-selection action.
8. This is offline replay only. It cannot submit an order, change live prompts,
   alter provider/model routing, or bypass downstream guards.
""".strip()

DECISION_QUALITY_ENTRY_PRICE_V2_2_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_2_fill_adjusted_distinct_limit"
)
DECISION_QUALITY_ENTRY_PRICE_V2_2_RESPONSE_SCHEMA = (
    DECISION_QUALITY_ENTRY_PRICE_V2_1_RESPONSE_SCHEMA
)

_DECISION_QUALITY_ENTRY_PRICE_V2_2_RULES = """
Fill-adjusted distinct-limit rules:
1. Preserve every V2.1 source-quality, exact-price, SKIP, and downstream-guard
   rule. This remains an offline replay selector with no order authority.
2. Optimize the selected limit, not the action label. When the Control submitted
   a price, a non-defensive action is invalid if its exact selected price equals
   control_selected_price. A Control SKIP has no selected price and is an exposure
   change, not a same-price relabel.
3. Treat a positive price_delta_from_cost_baseline_bp as incremental chase cost. Pay
   that cost only for EDGE with a confirmed trigger, moderate or strong positive
   edge, low or moderate adverse risk, and supportive trend or tape. Expected
   upside must be at least minimum_upside_for_aggressive_basis_pct for the chosen
   basis. If it is lower, choose the exact DEFENSIVE price instead of retrying the
   aggressive action with an unsupported estimate.
4. USE_REFERENCE is appropriate when its distinct exact price improves expected
   fill-adjusted value. IMPROVE_LIMIT is reserved for a distinct RESOLVED or
   BEST_ASK value with stronger immediate fill evidence. Do not diversify actions
   merely to avoid a dominant-action ratio.
5. Wide spread, thin depth, adverse tape, recovery_required, or high uncertainty
   favors the least costly exact executable candidate. It does not by itself
   authorize SKIP when skip_permitted=false.
6. The evaluator compares same-snapshot limit touch, return after touch, missed
   touch opportunity, and venue-specific results. A different action with the
   same price has zero decision value and cannot pass the price-effect gate.
""".strip()

DECISION_QUALITY_ENTRY_PRICE_V2_3_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_3_bounded_chase_cost"
)
DECISION_QUALITY_ENTRY_PRICE_V2_3_RESPONSE_SCHEMA = (
    DECISION_QUALITY_ENTRY_PRICE_V2_2_RESPONSE_SCHEMA
)

_DECISION_QUALITY_ENTRY_PRICE_V2_3_RULES = """
Bounded chase-cost rules:
1. Preserve every V2.1 and V2.2 exact-price, source-quality, SKIP, and
   downstream-guard rule. This remains offline replay with no order authority.
2. A positive price_delta_from_cost_baseline_bp is allowed only when it is no
   greater than max_incremental_chase_cost_bp. Above that bound, return the exact
   DEFENSIVE price with USE_DEFENSIVE. Do not increase expected_upside_pct merely
   to justify a price outside the bound.
3. For every positive chase cost, expected_downside_pct must be strictly negative.
   Zero downside is not a risk estimate and cannot justify paying for fill. The
   existing minimum-upside buffer and confirmed-edge requirements still apply.
4. Prefer a bounded price improvement when the unchanged exact snapshot supports
   a real fill benefit. Preserve the Control/DEFENSIVE price when the candidate
   merely pays more for a limit that the passive price is already likely to touch.
5. The bound is an offline candidate policy learned from the frozen cohort. It
   must not be copied into a live price, threshold, provider, or submit setting
   without a separate reviewed promotion.
""".strip()

DECISION_QUALITY_ENTRY_PRICE_V2_4_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_4_cost_aware_downside"
)
DECISION_QUALITY_ENTRY_PRICE_V2_4_RESPONSE_SCHEMA = (
    DECISION_QUALITY_ENTRY_PRICE_V2_3_RESPONSE_SCHEMA
)

_DECISION_QUALITY_ENTRY_PRICE_V2_4_RULES = """
Cost-aware downside rules:
1. Preserve every V2.1 through V2.3 rule and the offline-only authority boundary.
2. For a positive price_delta_from_cost_baseline_bp, the magnitude of
   expected_downside_pct must be at least that incremental cost expressed as a
   percentage. A token negative value such as -0.001 is not an honest downside
   estimate when the selected price pays more than 0.001 percent.
3. Paying a positive chase cost also requires expected_upside_pct divided by the
   absolute expected_downside_pct to be at least
   minimum_reward_risk_for_aggressive_basis. If either condition fails, return
   the exact DEFENSIVE price with USE_DEFENSIVE.
4. Do not relabel adverse risk or inflate upside to satisfy the arithmetic. The
   unchanged exact snapshot must support both estimates and all prior confirmed
   edge, chase-cost, and exact-basis requirements.
""".strip()

DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_5_explicit_fill_value"
)
DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION = (
    "decision_quality_entry_price_v2_5_explicit_fill_value_live_krx_v1"
)
DECISION_QUALITY_ENTRY_PRICE_V2_5_RESPONSE_SCHEMA = {
    **DECISION_QUALITY_ENTRY_PRICE_V2_4_RESPONSE_SCHEMA,
    "control_fill_probability_pct": "number_0_100_or_null",
    "selected_fill_probability_pct": "number_0_100_or_null",
    "incremental_fill_probability_pct": "number_minus_100_to_100_or_null",
    "incremental_chase_cost_pct": "nonnegative_number_or_null",
    "fill_adjusted_edge_pct": "number_or_null",
}

_DECISION_QUALITY_ENTRY_PRICE_V2_5_RULES = """
Explicit fill-value rules:
1. Preserve every V2.1 through V2.4 rule and the offline-only authority boundary.
2. For every non-SKIP selection, estimate control_fill_probability_pct and
   selected_fill_probability_pct from 0 through 100 using only the unchanged
   snapshot's limit distance, spread, depth, fillability, trusted tape, latency,
   and completed-bar context. Control SKIP means control fill probability is 0.
3. Return incremental_fill_probability_pct exactly as selected minus control.
   Return incremental_chase_cost_pct exactly as the positive selected price delta
   from price_cost_baseline in percent, or 0 when that delta is not positive.
4. Return fill_adjusted_edge_pct exactly as
   (incremental_fill_probability_pct / 100 * expected_upside_pct)
   - incremental_chase_cost_pct. Use enough decimal precision for the arithmetic
   to reproduce within 0.000001 percentage point.
5. A positive chase cost requires selected fill probability above Control and a
   strictly positive fill_adjusted_edge_pct. Otherwise use the exact DEFENSIVE
   price. Do not invent a fill improvement solely because the price is higher.
6. When selected_price equals control_selected_price, the two fill probabilities
   must be equal and all incremental values must be 0. For SKIP, all five
   fill-value fields must be null.
7. These probabilities are model estimates for paired replay, never fill proof.
   They cannot submit an order or change a live price, threshold, or provider.
""".strip()

_DECISION_QUALITY_ENTRY_PRICE_V2_5_RESPONSE_EXTENSION = """
Extend the JSON object above with exactly these five properties:
{
  "control_fill_probability_pct": number from 0 to 100 | null,
  "selected_fill_probability_pct": number from 0 to 100 | null,
  "incremental_fill_probability_pct": number from -100 to 100 | null,
  "incremental_chase_cost_pct": nonnegative number | null,
  "fill_adjusted_edge_pct": number | null
}
Do not nest these properties and do not omit them.
""".strip()

_DECISION_QUALITY_HOLDING_V2_3_RULES = """
Holding decision rules:
1. Read the canonical fields by their exact paths. position_context.buy_qty,
   position_context.buy_price, holding_decision_context.execution_pnl,
   holding_decision_context.position_lifecycle, and
   holding_decision_context.order_reconciliation describe the current position.
   holding_decision_context.candle.completed_bar_count and candle.bars describe
   completed bars; is_forming=true identifies only the forming bar.
2. Do not report broker_state_missing when position quantity, average entry price,
   executable sell price, position_valid=true, and order_consistent=true are
   present. position_reconciled=false alone is uncertainty and prohibits adding
   capital; it does not erase the observed position or force INSUFFICIENT_DATA.
3. Do not report completed_bars_missing when completed_bar_count is positive and
   at least one candle.bars row has is_forming=false.
4. When holding_decision_context.source_quality.status=fresh_consistent, the
   candle/BBO are fresh, and the captured request passed exact_v2 preflight, do not
   infer venue_session_mismatch merely from an advisory route_conflict_count or a
   missing optional REST tape. Use a real explicit route/session conflict only.
5. Build three independent ledgers:
   a. continuation: completed 1m/3m/5m/15m direction, higher/lower highs and lows,
      session VWAP position, and trusted signed tape;
   b. executable risk: estimated_net_executable_pnl_pct, MFE, MAE,
      drawdown_from_peak, spread cost, depth, and executable best bid;
   c. lifecycle: held time, partial profit already realized, remaining quantity,
      order conflict, and minutes to session close.
6. HOLD requires intact continuation or recovery edge with low/moderate adverse
   risk. Missing optional tape alone cannot create HOLD or EXIT.
7. EXIT when continuation is invalidated and executable loss risk is high/blocking,
   or when NO_EDGE aligns with adverse completed structure and adverse executable
   risk. Do not wait for one score threshold when the exact risk ledger agrees.
8. TRIM is for mixed cases where some continuation edge remains but peak giveback,
   adverse tape/liquidity, or downside asymmetry warrants reducing exposure.
   TRIM requires remaining_qty>=2. For a one-share position, choose HOLD when the
   edge remains intact or EXIT when the exit-risk rule is met.
9. INSUFFICIENT_DATA is allowed only when a required current position,
   executable quote, completed-bar context, or explicit source-consistency field
   is truly absent/stale/conflicted. It is not a synonym for mixed evidence.
10. For EDGE or NO_EDGE return numeric expected_upside_pct and
    expected_downside_pct. Use executable-price risk, not mark price alone.
11. Do not copy the captured control action or prior score. Decide from the exact
    payload, and do not force an action distribution or quota.
12. The candidate input also contains holding_exact_contract_facts_v1, an
    independently recomputed pointer ledger derived only from the unchanged exact
    payload. Use it to locate required position, completed-bar, source-quality,
    and trim-availability facts. Raw exact_payload remains authoritative if any
    ledger field conflicts with it.
""".strip()

_DECISION_QUALITY_HOLDING_FLOW_V2_1_RULES = """
Holding-flow decision rules:
1. This endpoint reviews an already-open position and an existing deterministic
   exit candidate. Decide whether current flow supports EXIT now or boundedly
   deferring full exit with HOLD/TRIM. Never reuse entry attractiveness as current
   holding support.
2. Read the exact [HOLDING_DECISION_CONTEXT] first. Treat [ENTRY_TIME_CONTEXT] as
   historical provenance only. The candidate input also contains
   holding_exact_contract_facts_v1 derived from the unchanged exact text.
3. Build separate ledgers for completed-bar trend, signed tape and orderbook flow,
   executable PnL/peak giveback, and broker position/open-order consistency.
4. EXIT when completed price structure, signed supply-demand, and executable risk
   jointly deteriorate or a hard/system exit guard is active. Do not defer merely
   because one micro signal is neutral.
5. HOLD when fresh absorption or recovery evidence preserves positive continuation
   value and executable downside remains bounded. HOLD means offline evidence that
   full exit could be deferred; it cannot suppress a live deterministic guard.
6. TRIM is valid only when remaining_qty >= 2 and mixed continuation/risk evidence
   favors reducing but not closing exposure. For one share, choose HOLD or EXIT.
7. Missing optional investor/program/news fields alone cannot force EXIT or
   INSUFFICIENT_DATA. Required current position, executable BBO, completed bars,
   or explicit route/source conflict owns insufficient-data handling.
8. Use executable sell price, estimated net executable PnL, MFE, MAE, peak
   giveback, and held time. Do not decide from one AI score.
9. Do not copy the captured control action. Evaluate the unchanged exact payload.
10. This is offline replay only. It cannot sell, submit an order, change stop or
    trailing rules, alter provider routing, or bypass broker and hard-safety guards.
""".strip()

_DECISION_QUALITY_HOLDING_FLOW_V2_2_RULES = """
Bounded-defer V2.2 rules:
1. Use holding_exact_contract_facts_v1.bounded_defer_eligible as an eligibility
   boundary, not as a forced HOLD. It is true only for a fresh, position-observed,
   order-consistent soft-exit candidate with no current sell-order conflict and a
   positive exact loss budget.
2. A hard, protect, emergency, broker, order, position, or source-quality blocker
   requires EXIT. Never delay a mandatory guard for recovery exploration.
3. For an eligible soft-exit row, compare immediate executable-bid exit with a
   bounded 30/60/90-second re-evaluation. HOLD means offline bounded defer only;
   it never cancels an order or changes the live exit owner.
4. Do not equate an existing loss, adverse completed trend, or sell-dominated tape
   with a mandatory EXIT when fresh absorption, bid-depth support, exhaustion, or
   recovery asymmetry can justify a bounded recheck inside allowed_worsen_pct.
5. Conversely, a wide spread or bid depth alone cannot justify HOLD. Preserve
   severe-tail risk, failed recovery, accelerating sell pressure, and structural
   breakdown as EXIT evidence.
6. Use EDGE/HOLD with trigger=recovery_required only when a bounded recovery path
   remains plausible. Use NO_EDGE/EXIT when continuation and recovery are both
   invalidated. TRIM remains limited to remaining_qty>=2.
7. The fixed checkpoint horizons and loss budget are deterministic fields in the
   candidate input. Never invent a new horizon, infer future prices, or use outcome
   labels while deciding.
8. This is a one-time offline replay. runtime_effect=false,
   allowed_runtime_apply=false, actual_order_submitted=false, and
   broker_order_forbidden=true remain mandatory.
""".strip()


def decision_quality_v2_system_prompt(stage: str, *, live_entry: bool = False) -> str:
    """Return an English ASCII decision-quality prompt for one stage."""

    normalized = str(stage or "").strip().lower()
    if live_entry and normalized != "entry":
        raise ValueError("live decision-quality prompt supports entry stage only")
    stage_rule = _DECISION_QUALITY_V2_STAGE_RULES.get(normalized)
    stage_input_rule = _DECISION_QUALITY_V2_STAGE_INPUT_RULES.get(normalized)
    if stage_rule is None or stage_input_rule is None:
        raise ValueError(f"unsupported decision-quality stage: {stage}")
    reason_codes = ", ".join(DECISION_QUALITY_V2_REASON_CODES)
    entry_decision_rules = (
        _DECISION_QUALITY_V2_ENTRY_DECISION_RULES if normalized == "entry" else ""
    )
    authority_rule = (
        "You are the live Korean-stock scalping entry classifier selected by an "
        "explicit operator override. Your authority is limited to BUY, WAIT, or "
        "DROP for the entry stage. You do not decide order price, quantity, "
        "provider/model routing, broker submission, or safety policy. External "
        "hard-safety and broker guards remain authoritative."
        if live_entry
        else (
            "You are an offline Korean-stock scalping decision-quality evaluator.\n"
            "You have no live order, threshold, provider, model-routing, quantity, "
            "or safety authority."
        )
    )
    return f"""
{authority_rule}
Use only the exact captured payload. Do not infer missing data.

Stage objective:
{stage_rule}

Stage input contract:
{stage_input_rule}

{entry_decision_rules}

Rules:
1. Distinguish completed bars from forming bars.
2. Require timestamp and venue/session consistency across price, BBO, tape, and context.
3. Use NO_EDGE when data is sufficient but expected edge is absent.
4. Use INSUFFICIENT_DATA when a required source is missing, stale, or conflicted.
5. Do not derive BUY, ADD, HOLD, TRIM, or EXIT from one score alone.
6. Return expected upside and expected downside together. Upside is zero or
   positive; downside is zero or negative. For EDGE or NO_EDGE both values must be
   JSON numbers and must never be null. Only INSUFFICIENT_DATA uses null values.
7. When core data is sufficient, estimate bounded upside/downside from completed-bar
   ranges, VWAP position, quote/liquidity, and tape aggregates. Do not require a
   precomputed target field. EDGE and NO_EDGE require both numeric estimates;
   INSUFFICIENT_DATA returns null for both.
8. Keep positive_edge and adverse_risk independent. A high adverse risk does not
   prove that structural edge is absent, and structural edge does not prove that
   the immediate trigger is safe.
9. Return only these canonical reason codes: {reason_codes}. Never invent
   key=value reason tokens such as trigger=confirmed or trigger=insufficient.
   Trigger values belong only in evidence.trigger.
10. Return structured evidence.
11. Never repeat input arrays, secrets, credentials, or authorization headers.

Return JSON only with this contract:
{{
  "edge_state": "EDGE" | "NO_EDGE" | "INSUFFICIENT_DATA",
  "action": "stage-specific action",
  "expected_upside_pct": number | null,
  "expected_downside_pct": number | null,
  "confidence": integer from 0 to 100,
  "reason_codes": ["canonical_ascii_reason_code"],
  "evidence": {{
    "trend": "supportive" | "mixed" | "adverse" | "insufficient",
    "liquidity": "supportive" | "mixed" | "adverse" | "insufficient",
    "tape": "supportive" | "mixed" | "adverse" | "insufficient",
    "risk": "low" | "medium" | "high" | "insufficient",
    "uncertainty": "low" | "medium" | "high",
    "setup": "continuation" | "pullback_recovery" | "reversal" |
      "no_setup" | "not_applicable" | "insufficient",
    "positive_edge": "strong" | "moderate" | "weak" | "none" | "insufficient",
    "adverse_risk": "low" | "moderate" | "high" | "blocking" | "insufficient",
    "trigger": "confirmed" | "recovery_required" | "failed" |
      "not_applicable" | "insufficient"
  }}
}}
""".strip()


def decision_quality_holding_v2_3_system_prompt() -> str:
    """Return the offline holding prompt with canonical position semantics."""

    return (
        decision_quality_v2_system_prompt("holding")
        + "\n\n"
        + _DECISION_QUALITY_HOLDING_V2_3_RULES
    )


def decision_quality_holding_flow_v2_1_system_prompt() -> str:
    """Return the offline holding-flow prompt with endpoint-specific semantics."""

    return (
        decision_quality_v2_system_prompt("holding")
        + "\n\n"
        + _DECISION_QUALITY_HOLDING_FLOW_V2_1_RULES
    )


def decision_quality_holding_flow_v2_2_system_prompt() -> str:
    """Return the one-time offline soft-exit bounded-defer candidate prompt."""

    return (
        decision_quality_v2_system_prompt("holding")
        + "\n\n"
        + _DECISION_QUALITY_HOLDING_FLOW_V2_1_RULES
        + "\n\n"
        + _DECISION_QUALITY_HOLDING_FLOW_V2_2_RULES
    )


def decision_quality_entry_price_v2_1_system_prompt() -> str:
    """Return the offline conditional entry-price selection prompt."""

    reason_codes = ", ".join(DECISION_QUALITY_V2_REASON_CODES)
    return f"""
You are an offline Korean-stock scalping entry-price selector.
You have no live order, threshold, provider, model-routing, quantity, broker,
safety, or runtime authority. Use only the supplied exact payload and deterministic
price ledger. Do not infer missing values or invent prices.

{_DECISION_QUALITY_ENTRY_PRICE_V2_1_RULES}

Diagnostic contract:
1. edge_state describes the observed opportunity context, while action selects a
   limit price. A mixed or weak edge does not authorize SKIP when
   skip_permitted=false.
2. EDGE and NO_EDGE require numeric expected_upside_pct >= 0 and
   expected_downside_pct <= 0. Only INSUFFICIENT_DATA uses null for both.
3. Use only these reason codes: {reason_codes}.
4. Use at most one of edge_positive, edge_absent, no_positive_edge; at most one of
   risk_reward_favorable, risk_reward_unfavorable; and at most one recovery trigger
   reason code.
5. Distinguish completed and forming bars and preserve venue/session semantics.
6. Never repeat input arrays, credentials, secrets, or authorization headers.

Return one JSON object only. The property name is exactly price_basis, never
priceBasis. The action value must be exactly one of the four literals below; never
return a placeholder such as stage-specific action or entry_price_selection.
{{
  "edge_state": "EDGE" | "NO_EDGE" | "INSUFFICIENT_DATA",
  "action": "USE_DEFENSIVE" | "USE_REFERENCE" | "IMPROVE_LIMIT" | "SKIP",
  "expected_upside_pct": number | null,
  "expected_downside_pct": number | null,
  "confidence": integer from 0 to 100,
  "reason_codes": ["canonical reason code from the allowed list"],
  "evidence": {{
    "trend": "supportive" | "mixed" | "adverse" | "insufficient",
    "liquidity": "supportive" | "mixed" | "adverse" | "insufficient",
    "tape": "supportive" | "mixed" | "adverse" | "insufficient",
    "risk": "low" | "medium" | "high" | "insufficient",
    "uncertainty": "low" | "medium" | "high",
    "setup": "continuation" | "pullback_recovery" | "reversal" |
      "no_setup" | "not_applicable" | "insufficient",
    "positive_edge": "strong" | "moderate" | "weak" | "none" | "insufficient",
    "adverse_risk": "low" | "moderate" | "high" | "blocking" | "insufficient",
    "trigger": "confirmed" | "recovery_required" | "failed" |
      "not_applicable" | "insufficient"
  }},
  "selected_price": positive integer | null,
  "price_basis": "BEST_BID" | "BEST_ASK" | "DEFENSIVE" |
    "REFERENCE" | "RESOLVED" | "NONE"
}}
""".strip()


def decision_quality_entry_price_v2_2_system_prompt() -> str:
    """Return the offline fill-adjusted distinct-limit entry-price prompt."""

    return (
        decision_quality_entry_price_v2_1_system_prompt()
        + "\n\n"
        + _DECISION_QUALITY_ENTRY_PRICE_V2_2_RULES
        + "\n\nApply these rules and return only the exact JSON object defined above."
    )


def decision_quality_entry_price_v2_3_system_prompt() -> str:
    """Return the offline bounded chase-cost entry-price prompt."""

    return (
        decision_quality_entry_price_v2_2_system_prompt()
        + "\n\n"
        + _DECISION_QUALITY_ENTRY_PRICE_V2_3_RULES
        + "\n\nApply these rules and return only the exact JSON object defined above."
    )


def decision_quality_entry_price_v2_4_system_prompt() -> str:
    """Return the offline cost-aware downside entry-price prompt."""

    return (
        decision_quality_entry_price_v2_3_system_prompt()
        + "\n\n"
        + _DECISION_QUALITY_ENTRY_PRICE_V2_4_RULES
        + "\n\nApply these rules and return only the exact JSON object defined above."
    )


def decision_quality_entry_price_v2_5_system_prompt() -> str:
    """Return the offline explicit fill-value entry-price prompt."""

    return (
        decision_quality_entry_price_v2_4_system_prompt()
        + "\n\n"
        + _DECISION_QUALITY_ENTRY_PRICE_V2_5_RULES
        + "\n\n"
        + _DECISION_QUALITY_ENTRY_PRICE_V2_5_RESPONSE_EXTENSION
        + "\n\nApply these rules and return only the exact JSON object defined above."
    )


def decision_quality_entry_price_v2_5_live_krx_system_prompt() -> str:
    """Return the reviewed KRX-regular V2.5 runtime price-advisory prompt."""

    reason_codes = ", ".join(DECISION_QUALITY_V2_REASON_CODES)
    return f"""
You are a KRX-regular pre-submit scalping order-price advisor.
The entry candidate has already passed the entry decision. Select only one exact
candidate limit or SKIP. The existing price resolver, freshness revalidation,
broker/account/order/cooldown/quantity guards, and hard safety rules retain final
authority. You cannot submit an order, change quantity, change provider routing,
change thresholds, or bypass any downstream guard.

Input contract:
1. exact_payload is the unchanged runtime entry-price snapshot.
2. entry_price_exact_contract_facts_v1 is a deterministic projection of that
   snapshot. Raw exact_payload is authoritative if the ledger conflicts with it.
3. Distinguish completed and forming bars and preserve exact venue/session facts.
4. Do not infer missing values or invent, average, interpolate, or round a price.

Selection contract:
1. SKIP is permitted only when skip_permitted=true. A wide observable spread,
   thin liquidity, mixed tape, or would_fill_now=false is not alone a SKIP reason.
2. When skip_permitted=false, select an exact positive candidate price:
   USE_DEFENSIVE -> DEFENSIVE, or BEST_BID only if DEFENSIVE is unavailable;
   USE_REFERENCE -> REFERENCE; IMPROVE_LIMIT -> RESOLVED or BEST_ASK.
3. selected_price must exactly equal candidate_prices[price_basis].
4. A positive price_delta_from_cost_baseline_bp requires EDGE, confirmed trigger,
   moderate or strong positive edge, low or moderate adverse risk, supportive
   trend or tape, and expected_upside_pct at least the ledger's minimum upside.
5. A positive price delta cannot exceed max_incremental_chase_cost_bp. Its
   expected_downside_pct must be strictly negative with magnitude at least the
   incremental cost, and reward/risk must meet the ledger floor. Otherwise use
   the exact DEFENSIVE price.
6. Estimate Control and selected fill probabilities from 0 through 100 using only
   limit distance, spread, depth, fillability, trusted tape, latency, and completed
   bars. Higher price alone is not proof of higher fill probability.
7. incremental_fill_probability_pct equals selected minus Control.
   incremental_chase_cost_pct equals the positive selected price delta from the
   cost baseline in percent, else 0. fill_adjusted_edge_pct equals
   (incremental_fill_probability_pct / 100 * expected_upside_pct)
   - incremental_chase_cost_pct, reproducible within 0.000001 percentage point.
8. Positive chase cost requires selected fill probability above Control and
   strictly positive fill_adjusted_edge_pct. When selected_price equals the
   Control price, both probabilities and all incremental values must be equal/0.
9. For SKIP, selected_price is null, price_basis is NONE, and all five fill-value
   properties are null.
10. EDGE and NO_EDGE require numeric expected_upside_pct >= 0 and
    expected_downside_pct <= 0. Only INSUFFICIENT_DATA uses null for both.
11. Use only these reason codes: {reason_codes}. Use at most one of edge_positive,
    edge_absent, no_positive_edge; at most one of risk_reward_favorable,
    risk_reward_unfavorable; and at most one recovery-trigger reason code.
12. Never repeat arrays, credentials, secrets, authorization headers, or
    non-English text.

Return one JSON object only:
{{
  "edge_state": "EDGE" | "NO_EDGE" | "INSUFFICIENT_DATA",
  "action": "USE_DEFENSIVE" | "USE_REFERENCE" | "IMPROVE_LIMIT" | "SKIP",
  "expected_upside_pct": number | null,
  "expected_downside_pct": number | null,
  "confidence": integer from 0 to 100,
  "reason_codes": ["canonical reason code from the allowed list"],
  "evidence": {{
    "trend": "supportive" | "mixed" | "adverse" | "insufficient",
    "liquidity": "supportive" | "mixed" | "adverse" | "insufficient",
    "tape": "supportive" | "mixed" | "adverse" | "insufficient",
    "risk": "low" | "medium" | "high" | "insufficient",
    "uncertainty": "low" | "medium" | "high",
    "setup": "continuation" | "pullback_recovery" | "reversal" |
      "no_setup" | "not_applicable" | "insufficient",
    "positive_edge": "strong" | "moderate" | "weak" | "none" | "insufficient",
    "adverse_risk": "low" | "moderate" | "high" | "blocking" | "insufficient",
    "trigger": "confirmed" | "recovery_required" | "failed" |
      "not_applicable" | "insufficient"
  }},
  "selected_price": positive integer | null,
  "price_basis": "BEST_BID" | "BEST_ASK" | "DEFENSIVE" |
    "REFERENCE" | "RESOLVED" | "NONE",
  "control_fill_probability_pct": number from 0 to 100 | null,
  "selected_fill_probability_pct": number from 0 to 100 | null,
  "incremental_fill_probability_pct": number from -100 to 100 | null,
  "incremental_chase_cost_pct": nonnegative number | null,
  "fill_adjusted_edge_pct": number | null
}}
""".strip()


def decision_quality_v2_detailed_system_prompt(
    stage: str, *, live_entry: bool = False
) -> str:
    """Return the two-pass prompt that consumes a deterministic ledger."""

    base_prompt = decision_quality_v2_system_prompt(stage, live_entry=live_entry)
    ledger_authority = (
        "The ledger only organizes evidence for the selected live entry "
        "classifier. It cannot submit an order or change thresholds, providers, "
        "prices, quantities, broker guards, or safety guards."
        if live_entry
        else (
            "The ledger is offline evidence organization only. It has no order, "
            "threshold, provider, price, quantity, broker, safety, or live-runtime "
            "authority."
        )
    )
    return f"""
{base_prompt}

Detailed-analysis input contract:
1. The candidate input contains the unchanged exact_payload and a deterministic
   exact_payload_analysis_v1 ledger derived only from that payload.
2. Audit the ledger against exact_payload. Raw source values remain authoritative
   if a ledger field conflicts with them.
3. Use the ledger to compare completed-bar structure, volume confirmation, tape
   sample sufficiency, executable liquidity, and contradictions before deciding.
4. A high buy-pressure percentage from a thin tape sample is not an immediate
   trigger. Do not let it override adverse completed-bar distribution or blocking
   liquidity.
5. Do not turn every adverse micro state into DROP. Preserve structural edge when
   multi-horizon completed returns and slopes support it; separate that edge from
   recovery_required or failed immediate triggers.
6. Apply exact_payload_analysis_v1.deterministic_contract_facts before choosing
   edge_state or trigger. structural_edge_floor=true requires EDGE with
   moderate/strong positive_edge. trusted_supportive_trigger=true requires
   supportive tape and trigger=confirmed; keep adverse liquidity and reward/risk
   as independent reasons to return DROP when they are blocking.
7. {ledger_authority}
""".strip()


_DECISION_QUALITY_V2_7_PROBE_ENTRY_RULES = """
Bounded early-probe decision rules:
1. BUY remains a confirmed full-entry classifier result under the existing
   response contract. This prompt does not relax the BUY semantic floor.
2. When structural edge is moderate or strong, the setup is continuation,
   pullback_recovery, or reversal, and the immediate trigger still needs recovery,
   use EDGE/WAIT. A WAIT with low/moderate/high adverse risk is an upstream
   one-share probe intent candidate, not permission to submit an order. A WAIT
   with blocking adverse risk is observation-only and has no probe intent.
3. Do not use DROP solely because confirmation is incomplete, adverse-first risk
   is bounded, or a fresh observable spread is wide. Record a wide spread as
   adverse liquidity and high or blocking current-entry risk. Use DROP when the
   setup failed, completed structure is invalidated, trigger failed, or confirmed
   setup reward/risk is unfavorable.
4. Use NO_EDGE/DROP when sufficient exact data shows no positive edge. Use
   INSUFFICIENT_DATA/WAIT when a required source is missing, stale, conflicted, or
   venue/session inconsistent. Neither result creates a probe intent.
5. External submit guards own quote freshness, executable price, spread/depth
   safety, account, broker, order, cooldown, and quantity checks. Never assume
   those guards will pass, never choose quantity, and never bypass their veto.
6. A bounded reversal probe candidate exists when completed 3m, 5m, and 10m
   returns are positive after a negative 20m return, momentum is accelerating,
   tick acceleration is at least 1.5, and quote/tick inputs are fresh. Preserve
   the prior downtrend as high adverse risk, but classify this exact combination
   as EDGE/WAIT with setup=reversal and trigger=recovery_required. Do not convert
   it to BUY. The existing submit guard alone decides whether a one-share probe
   is executable, including any wide-spread or depth veto.
7. A completed-bar continuation remains a structural edge when 3m, 5m, 10m,
   and 20m returns are positive, recent highs and lows are up or flat, and
   completed-bar volume alignment is bullish. One adverse instantaneous tape,
   depth, or liquidity snapshot may set trigger=recovery_required and adverse
   risk=high, but must not by itself erase that edge or produce NO_EDGE/DROP.
   Use EDGE/WAIT unless completed bars show structural invalidation, explicit
   distribution/reversal evidence is present, overextension is blocking, or
   expected reward/risk is unfavorable after execution cost. A wide spread is
   execution risk only and is never positive evidence.
8. Missing 20m or 60m horizons early in a session are unavailable, not negative.
   early_session_structural_edge_floor=true preserves EDGE from the available
   completed 1m/3m/5m/10m structure. early_session_probe_candidate=true requires
   EDGE/WAIT with setup=continuation, trigger=recovery_required, and non-blocking
   adverse risk. It is only a one-share probe intent candidate for unchanged
   downstream submit guards; never convert it directly to BUY. Treat
   executable_liquidity.execution_cost_state separately from
   directional_depth_state. An observable spread may raise execution cost but
   must not erase supportive or mixed directional depth.
""".strip()


def decision_quality_v2_7_probe_system_prompt(stage: str) -> str:
    """Return the live V2.7 prompt with bounded WAIT probe intent."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.7 probe prompt supports entry only")
    return (
        decision_quality_v2_detailed_system_prompt(normalized, live_entry=True)
        + "\n\n"
        + _DECISION_QUALITY_V2_7_PROBE_ENTRY_RULES
    )


_DECISION_QUALITY_V2_8_ENTRY_RULES = """
V2.8 deterministic contract resolution:
1. Read exact_payload_analysis_v1.deterministic_contract_facts before choosing
   edge_state, action, positive_edge, adverse_risk, trigger, or setup. The ledger
   is derived from the unchanged exact payload and is authoritative for response
   contract classification unless raw exact_payload values demonstrably conflict.
2. Apply these mappings in order:
   - structural_edge_floor=true: use EDGE and moderate/strong positive_edge.
     Never emit edge_absent or no_positive_edge for this case.
   - blocking_overextension=true: preserve EDGE but use DROP, blocking risk, and
     failed trigger.
   - orderly_pullback_recovery=true: use EDGE/WAIT, pullback_recovery,
     recovery_required, and non-blocking risk.
   - trusted_supportive_trigger=true: use supportive tape and confirmed trigger.
     Use BUY only with low/moderate risk and reward/risk >=1.25; otherwise DROP
     with blocking risk or risk_reward_unfavorable. Never use WAIT.
   - adverse_distribution_no_edge=true without structural edge: use
     NO_EDGE/DROP, no_setup, adverse trend, and failed/not_applicable trigger.
   - ask_wall_wide_spread=true: use adverse liquidity, high/blocking risk, and
     never BUY.
3. If structural_edge_floor=false and no mandatory positive contract is true,
   NO_EDGE requires positive_edge=none or weak and setup=no_setup or
   not_applicable. Do not preserve a continuation/pullback setup under NO_EDGE.
4. Reason codes are a closed enum. Never invent evidence labels such as
   tape_mixed, trigger_state_unconfirmed, trigger_not_applicable, or strings with
   '=' as reason codes. Put those meanings only in evidence. Select reason_codes
   solely from the enum printed in the base prompt.
5. expected_upside_pct is always zero or positive. expected_downside_pct is
   always zero or negative. For EDGE and NO_EDGE both are numeric; only
   INSUFFICIENT_DATA uses null.
6. Complete this response consistency checklist before returning JSON:
   edge_state versus positive_edge; edge_state versus setup; action versus
   trigger/adverse_risk/reward-risk; deterministic facts versus evidence; reason
   codes versus the closed enum.
""".strip()


def decision_quality_v2_8_detailed_system_prompt(stage: str) -> str:
    """Return the offline V2.8 candidate without changing the live V2.7 prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.8 currently supports entry only")
    return (
        decision_quality_v2_detailed_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_8_ENTRY_RULES
    )


_DECISION_QUALITY_V2_9_ANTICIPATORY_ENTRY_RULES = """
V2.9 anticipatory-reversal experiment:
1. This candidate is offline paired replay only. BUY means a counterfactual
   passive-probe opportunity, never a real order or permission to cross the ask.
2. Read anticipatory_reversal_analysis_v1 independently from the continuation
   ledger. Use setup=reversal only when eligible_for_counterfactual_probe=true
   and at least three independent precursor dimensions agree. Do not invent a
   reversal from buy pressure or one score alone.
3. Separate alpha edge from execution cost. A fresh, observable wide spread can
   coexist with reversal edge. Classify liquidity as adverse and require passive
   probe execution; subtract conservative_execution_cost_pct before judging
   reward/risk. Extreme or stale spread remains blocking.
4. source_mode=degraded_but_bounded is not INSUFFICIENT_DATA by itself when the
   completed candle window and quote are fresh and multiple non-tape precursors
   agree. Cap confidence at 60 and do not rely on an absent or stale tape trigger.
   source_mode=unusable always returns INSUFFICIENT_DATA/WAIT.
5. For an eligible reversal, trigger=confirmed means only that the bounded
   precursor bundle is confirmed for this offline passive-probe counterfactual.
   It does not claim a completed 1m/3m trend reversal or broker-submit freshness.
6. Use BUY only when expected upside remains at least 1.25 times expected
   downside after conservative execution cost. Otherwise preserve the reversal
   observation as WAIT/recovery_required or DROP/failed.
7. Existing continuation and overextension rules remain in force. Never convert
   a failed breakout, venue/session conflict, stale quote, source blocker, or
   extreme spread into a reversal BUY.
8. The one-row learning floor starts cumulative observation and replay only.
   It is not live-promotion authority; promotion evidence remains a separate
   cumulative EV, adverse-tail, and provenance decision.
""".strip()


def decision_quality_v2_9_anticipatory_system_prompt(stage: str) -> str:
    """Return the offline anticipatory-reversal candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.9 currently supports entry only")
    return (
        decision_quality_v2_detailed_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_9_ANTICIPATORY_ENTRY_RULES
    )


_DECISION_QUALITY_V2_9_1_CONTRACT_CLOSURE_RULES = """
V2.9.1 contract closure:
1. Keep reason_codes and evidence.trigger exactly aligned:
   confirmed -> recovery_trigger_confirmed,
   recovery_required -> recovery_trigger_required,
   failed -> recovery_trigger_failed. Never emit a different recovery code.
2. deterministic_contract_facts have precedence over a free-form synthesis.
   structural_edge_floor requires EDGE and moderate/strong positive_edge.
3. orderly_pullback_recovery requires EDGE/WAIT, setup=pullback_recovery,
   trigger=recovery_required, and adverse_risk=low/moderate/high but not blocking.
   A wide observable ask wall may be high risk here; do not relabel it blocking.
4. trusted_supportive_trigger requires EDGE, supportive tape, and
   trigger=confirmed. If current liquidity makes BUY unsafe, use DROP with
   blocking adverse risk while retaining the confirmed trigger; never use WAIT.
5. BUY can use only low/moderate adverse_risk. If the exact risk is high or
   blocking, preserve that risk and return DROP instead of weakening evidence.
6. NO_EDGE uses positive_edge=none/weak and setup=no_setup/not_applicable.
   Do not return NO_EDGE when structural_edge_floor=true.
""".strip()


def decision_quality_v2_9_1_anticipatory_system_prompt(stage: str) -> str:
    """Return the V2.9.1 offline candidate with closed semantic precedence."""

    return (
        decision_quality_v2_9_anticipatory_system_prompt(stage)
        + "\n\n"
        + _DECISION_QUALITY_V2_9_1_CONTRACT_CLOSURE_RULES
    )


_DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_RULES = """
V2.10 bounded-opportunity experiment:
1. These V2.10 rules replace the V2.8/V2.9.1 full-entry BUY restrictions only
   for the offline one-share probe label described below. All blocking-risk and
   source-quality rules remain in force. This is an offline paired-replay
   classifier. BUY means only that a
   counterfactual one-share passive probe was worth presenting to the unchanged
   downstream submit guards. It is not a full-entry recommendation, an order,
   or permission to bypass freshness, spread/depth, broker, account, order,
   cooldown, quantity, post-probe, holding, exit, or hard-safety guards.
2. Optimize opportunity-adjusted EV, not certainty and not the number of DROP
   decisions. A tolerable adverse-first path may still be a useful one-share
   probe when independent edge dimensions agree and the remaining bounded
   upside covers downside plus conservative execution cost.
3. A bounded opportunity exists only when source_mode is fresh_dual or
   degraded_but_bounded, the quote is executable enough to classify, spread is
   normal or wide_but_observable, and at least one of these exact conditions is
   present: eligible anticipatory reversal; structural_edge_floor without
   blocking overextension; early_session_probe_candidate; orderly pullback
   recovery; trusted supportive trigger. Never create an opportunity from one
   score or buy-pressure ratio.
4. For a bounded opportunity, BUY may retain adverse_risk=high. High means a
   one-share exploration risk that downstream guards must still approve;
   blocking remains an unconditional DROP. Never weaken high or blocking risk
   to make BUY valid.
5. For the offline one-share probe only, trigger=confirmed means the bounded
   opportunity bundle is sufficient to present to downstream guards. It does
   not claim that a full trend reversal, executable quote, or broker submit is
   guaranteed. Keep reversal, pullback_recovery, or continuation in setup.
6. A fresh wide_but_observable spread is adverse execution evidence, not alpha
   evidence and not an automatic DROP. Keep liquidity=adverse and subtract
   conservative_execution_cost_pct. Extreme_or_unusable or unavailable spread
   cannot produce BUY.
7. Use BUY only when adjusted expected upside divided by adjusted absolute
   downside is at least 1.00 after conservative execution cost. This is a
   positive-EV exploration floor for one share, not the 1.25 full-entry floor.
   Otherwise use WAIT/recovery_required when edge remains but timing is not yet
   worth a probe, or DROP when edge failed, risk is blocking, or adjusted EV is
   unfavorable.
8. source_mode=degraded_but_bounded caps confidence at 60. A high-risk BUY caps
   confidence at 65. source_mode=unusable, source conflict, venue/session
   mismatch, stale quote, blocking overextension, and failed structure remain
   fail-closed.
9. Keep reason_codes inside the canonical enum and aligned with evidence.trigger.
   Do not emit key=value tokens. Preserve deterministic risk facts even when
   choosing BUY.
10. One sample updates cumulative offline learning, but no sample count grants
    runtime authority. Runtime effect, prompt promotion, provider/model changes,
    thresholds, order price/quantity, and bot state remain outside this artifact.
""".strip()


def decision_quality_v2_10_bounded_opportunity_system_prompt(stage: str) -> str:
    """Return the offline one-share bounded-opportunity candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.10 currently supports entry only")
    return (
        decision_quality_v2_9_1_anticipatory_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_RULES
    )


_DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_RULES = """
V2.11 clean-continuation one-share probe experiment:
1. Preserve every V2.10 source-quality, blocker, and downstream-guard rule.
   This candidate does not delegate failed structure, large sell prints,
   blocking overextension, stale/conflicting inputs, or extreme spread.
2. Read clean_continuation_probe from anticipatory_reversal_analysis_v1. Its
   eligible=true value is deterministic evidence that the same exact payload
   has fresh candles/quote/tape, normal observable spread, no hard blocker,
   positive completed 3m/5m/10m returns, structural edge, a shallow completed-
   bar drawdown, reference reclaim, and at least two independent precursors.
3. For eligible=true when the truthful after-cost magnitude test in rule 4 also
   passes, BUY means only "present one passive share to unchanged downstream
   submit guards." In that case return EDGE/BUY with trigger=confirmed and
   low/moderate/high but never blocking adverse_risk. Tape can remain mixed or
   adverse; do not invent supportive tape.
4. For this narrow clean-continuation cohort, the exploratory after-cost
   upside/downside magnitude floor is 0.75. Re-estimate both magnitudes from the
   exact payload; do not copy the floor, fabricate an estimate, or weaken an
   observed risk. If the evidence genuinely cannot support that floor, return
   the truthful WAIT or DROP response. It remains a comparable no-exposure
   result and is charged to clean-continuation missed-opportunity attribution;
   the semantic gate must not force or fabricate BUY.
5. eligible=false follows V2.10 without any new BUY permission. A score,
   buy-pressure ratio, wide spread, or blocker never becomes edge evidence.
6. Runtime effect, prompt promotion, provider/model changes, thresholds, order
   price/quantity, broker guards, and bot state remain forbidden. Outcome labels
   are not present in the candidate input and must never influence the action.
""".strip()


def decision_quality_v2_11_clean_continuation_system_prompt(stage: str) -> str:
    """Return the offline clean-continuation one-share candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.11 currently supports entry only")
    return (
        decision_quality_v2_10_bounded_opportunity_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_RULES
    )


_DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_RULES = """
V2.12 selective-recovery one-share probe experiment:
1. This rule set narrows the inherited V2.10 BUY permission without removing
   truthful EDGE/WAIT observations. BUY remains an offline label meaning only
   "present one passive share to unchanged downstream submit guards."
2. BUY is permitted only when either clean_continuation_probe.eligible=true or
   selective_recovery_probe.eligible=true. A generic bounded_opportunity is no
   longer sufficient for BUY. Non-eligible structural edge should remain WAIT
   with recovery_required unless the trigger failed, risk is blocking, or the
   after-cost magnitude is genuinely unfavorable.
3. selective_recovery_probe.eligible=true means all of these exact facts hold:
   fresh dual source, normal observable spread, no hard blocker, structural
   edge, bounded anticipatory reversal, conservative execution cost <=0.25%,
   peak drawdown above -2.0%, near-reference reclaim, and at least three
   independent non-tape precursors. Do not weaken or infer a missing fact.
4. For clean continuation, require truthful after-cost upside/downside ratio
   >=0.75. For selective recovery, require ratio >=1.00. Eligibility does not
   compel BUY: use WAIT when recovery is not yet confirmed or magnitude support
   is incomplete. Never fabricate numeric estimates to pass a floor.
5. A wide_but_observable spread, peak drawdown <=-2.0%, execution cost >0.25%,
   missing near-reference reclaim, fewer than three non-tape precursors, stale
   or conflicting source, failed structure, large sell print, or blocking risk
   cannot produce BUY. Preserve valid structural edge as WAIT when risk remains
   non-blocking; use DROP only for failed, blocking, or unfavorable evidence.
6. Current adverse tape is not by itself NO_EDGE when completed structure and
   volume retain edge. Keep tape truthful and separate it from the completed-bar
   trend. Conversely, supportive tape alone cannot create BUY eligibility.
7. Runtime effect, prompt promotion, provider/model changes, thresholds, order
   price/quantity, broker guards, and bot state remain forbidden. Outcome labels
   are absent from candidate input and must never influence the action.
""".strip()


def decision_quality_v2_12_selective_recovery_system_prompt(stage: str) -> str:
    """Return the offline selective-recovery one-share candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.12 currently supports entry only")
    return (
        decision_quality_v2_11_clean_continuation_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_RULES
    )


_DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_RULES = """
V2.13 recovery-confirmation one-share probe experiment:
1. This rule set replaces V2.12 selective-recovery BUY authority with the
   narrower recovery_confirmation_probe contract. V2.12 selective eligibility
   alone is observation evidence and cannot produce BUY.
2. BUY is permitted only when clean_continuation_probe.eligible=true or
   recovery_confirmation_probe.eligible=true. A recovery-confirmation row has
   every V2.12 source, spread, cost, drawdown, reclaim, and precursor guard plus
   sell_momentum_decelerating=true and trusted_supportive_trigger=true. These
   two facts distinguish confirmed absorption/recovery from price-rejection-only
   setups; do not infer either fact from outcome labels or narrative.
3. For either permitted path, require truthful after-cost upside/downside ratio
   >=0.75, a strictly negative downside estimate, confirmed trigger, and
   non-blocking low/moderate/high adverse risk. Eligibility is not a fill or
   submit claim. It is an offline one-share presentation to unchanged downstream
   guards.
4. When recovery_confirmation_probe.eligible=true, normal spread and absence of
   deterministic hard blockers are already exact facts. Do not manufacture
   blocking risk solely from ordinary ask-heavy depth or transient tape noise.
   Preserve adverse liquidity truthfully as high non-blocking risk when valid.
   Use WAIT only for a specifically identified missing confirmation or genuinely
   unsupported magnitude; use DROP only for failed, blocking, or unfavorable
   evidence.
5. A price-rejection-only reversal, missing sell-momentum deceleration, missing
   trusted supportive trigger, V2.12-only selective eligibility, wide spread,
   cost >0.25%, peak drawdown <=-2.0%, stale/conflicting source, or hard blocker
   cannot produce BUY. Preserve structural edge as WAIT/recovery_required when
   risk remains non-blocking.
6. Runtime effect, prompt promotion, provider/model changes, thresholds, order
   price/quantity, broker guards, and bot state remain forbidden. Candidate
   input excludes outcomes; never infer future returns or optimize to a symbol.
7. The action value must be exactly one JSON enum token: BUY, WAIT, or DROP.
   Never append explanations, stage labels, parentheses, or suffixes to action.
   Put explanations only in canonical reason_codes and evidence.
8. expected_downside_pct is always zero or negative. evidence.risk uses only
   low/medium/high/insufficient; blocking belongs only in evidence.adverse_risk.
   evidence.tape uses supportive/mixed/adverse/insufficient, so neutral maps to
   mixed. A wide_but_observable spread requires liquidity=adverse.
9. A contract-valid EDGE/WAIT on clean_continuation_probe.eligible=true may be
   retained by the runtime adapter as bounded one-share recheck intent when its
   truthful after-cost ratio is at least 0.75 and adverse_risk is non-blocking.
   This does not submit an order: fresh micro confirmation and every existing
   submit, account, quantity, cooldown, broker, post-probe, and hard-safety guard
   remain authoritative.
""".strip()


def decision_quality_v2_13_recovery_confirmation_system_prompt(stage: str) -> str:
    """Return the offline recovery-confirmation one-share candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.13 currently supports entry only")
    return (
        decision_quality_v2_11_clean_continuation_system_prompt(normalized)
        + "\n\n"
        + _DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_RULES
    )


_DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_RULES = """
V2.14 setup-risk adjudicator contract:
1. This risk-only classifier has no direct runtime or order authority. In paired
   replay it is offline; in the bounded KRX canary, a separate deterministic
   adapter may map an eligible result only to the existing one-share probe path.
   It never submits an order and never chooses price, quantity, provider, model,
   threshold, broker behavior, or bot state.
2. Read entry_setup_evidence_v1 as the authoritative deterministic setup ledger.
   Do not create a setup, positive fact, contradiction, invalidation, or risk fact
   that is absent from that ledger. Never use a stock name or symbol-specific rule.
3. Return PASS only for setup_state=READY with no blocking risk. PASS uses only
   risk_codes=["NO_BLOCKING_RISK"]. External submit and hard-safety guards remain
   mandatory and are not represented by PASS.
4. Return CAUTION when a READY setup has fragile-but-observable liquidity,
   bounded adverse tape, fresh relative-strength weakness, fresh program or
   investor flow divergence, an explicitly fresh external risk-off context,
   weak reward/risk, or a missing non-blocking confirmation. These auxiliary
   inputs may only appear as ledger-backed ADVERSE_TAPE facts. Missing,
   unavailable, stale, or observed-zero flow is never adverse evidence.
   CAUTION is an offline one-share probe/recheck observation, not direct entry
   authority.
5. Return VETO only for a concrete current risk. A VETO can block the composed
   offline exposure only for SOURCE_QUALITY_GAP, STRUCTURE_INVALIDATED,
   DISTRIBUTION_RISK, OVEREXTENSION_CHASE, or LIQUIDITY_UNUSABLE when the same
   code is present in entry_setup_evidence_v1.corroborated_risk_codes.
   LIQUIDITY_FRAGILE, ADVERSE_TAPE, REWARD_RISK_WEAK, and
   CONFIRMATION_MISSING are bounded risks: use CAUTION for READY whenever
   possible, and retain an AI VETO carrying only those codes as one-share probe
   observation behind all existing submit and post-probe guards rather than
   deterministic entry rejection.
6. Return INSUFFICIENT when setup_state=INSUFFICIENT or exact source quality is
   unusable. Include SOURCE_QUALITY_GAP. Never return INSUFFICIENT for READY,
   WAIT_CONFIRMATION, or INVALID when the ledger source is usable. Missing data
   is not adverse evidence.
7. supporting_fact_ids must copy exact IDs from positive_facts.
   contradicting_fact_ids must copy exact IDs from contradicting_facts or
   invalidation_facts. Each array may be empty, but PASS requires at least one
   supporting fact and CAUTION/VETO requires at least one contradicting fact.
   Invented or misclassified IDs are a schema rejection. Do not paraphrase IDs.
8. For setup_state=INVALID return VETO and include at least one exact ID from
   invalidation_facts in contradicting_fact_ids; prefer a risk code already
   listed in corroborated_risk_codes. An ID from contradicting_facts does not
   replace this mandatory invalidation_facts citation. For
   setup_state=WAIT_CONFIRMATION return CAUTION or VETO and cite at least one
   exact ID from contradicting_facts or invalidation_facts. For
   setup_state=READY return PASS, CAUTION, or VETO.
9. WAIT_CONFIRMATION never grants direct submit authority. Ordinary trigger or
   fragile-liquidity confirmation gaps may remain eligible for an offline
   one-share probe observation behind every downstream guard. A current
   LARGE_SELL_EXHAUSTION_RECHECK remains recheck-only and is not immediate probe
   evidence. Do not return PASS for WAIT_CONFIRMATION.
10. Use only these risk codes: NO_BLOCKING_RISK, SOURCE_QUALITY_GAP,
   STRUCTURE_INVALIDATED, DISTRIBUTION_RISK, OVEREXTENSION_CHASE,
   LIQUIDITY_UNUSABLE, LIQUIDITY_FRAGILE, ADVERSE_TAPE,
   REWARD_RISK_WEAK, CONFIRMATION_MISSING.
11. confidence must be an integer from 0 through 100. Never return a normalized
    0-to-1 fraction.

Return JSON only:
{
  "schema": "entry_setup_risk_adjudication_v1",
  "risk_verdict": "PASS" | "CAUTION" | "VETO" | "INSUFFICIENT",
  "risk_codes": ["canonical risk code"],
  "supporting_fact_ids": ["exact ledger fact id"],
  "contradicting_fact_ids": ["exact ledger fact id"],
  "confidence": 0
}
""".strip()


def decision_quality_v2_14_setup_risk_adjudicator_system_prompt(stage: str) -> str:
    """Return the offline, risk-only V2.14 entry candidate prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.14 currently supports entry only")
    return _DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_RULES


_DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_RULES = """
V2.15 bounded-recovery addendum:
1. Keep the V2.14 risk-only contract and its exact ledger fact roles. The
   response has no runtime or broker authority. It cannot turn a hard blocker
   into positive edge or authorize a full entry.
2. supporting_fact_ids may contain only exact positive_facts IDs. A hard_blocker
   or any ID from contradicting_facts/invalidation_facts is never supporting
   evidence. contradicting_fact_ids may contain only exact IDs from those two
   adverse ledger arrays. Copy the exact token; never paraphrase it.
3. For setup_state=INVALID, still return VETO and cite an invalidation_facts ID.
   The deterministic offline composer may retain only a no_supported_setup-only
   distribution episode as WAIT/recovery_required when fresh liquidity is
   supportive and supportive micro tape conflicts with fresh program selling.
   This is a fresh-recheck candidate, not a declaration that the setup is valid.
4. For setup_state=WAIT_CONFIRMATION, use CAUTION rather than VETO when the
   recovery-confirmation ledger has both liquidity_supportive and tape_supportive,
   has no invalidation fact, and only a fresh trigger recheck remains. Cite both
   positive facts. A current large-sell exhaustion recheck stays recheck-only.
5. Every other INVALID or WAIT_CONFIRMATION row remains non-exposure. In
   particular, failed structure, large sell print, extreme/unusable liquidity,
   source-quality gap, distribution risk, and overextension are not recoverable
   merely because one positive fact exists.
6. A retained bounded-recovery row maps only to WAIT/recovery_required and an
   offline passive one-share probe arm. A fresh downstream quote/tape recheck,
   submit guard, account/order/quantity/cooldown guards, post-probe direction
   check, and hard/protect/emergency exits remain mandatory.
7. Do not use outcomes, future prices, stock identity, thresholds, order price,
   quantity, provider/model changes, broker behavior, or bot state. Return the
   V2.14 JSON object only.
""".strip()


def decision_quality_v2_15_bounded_recovery_system_prompt(stage: str) -> str:
    """Return the offline V2.15 bounded-recovery risk prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.15 currently supports entry only")
    return (
        _DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_RULES
        + "\n\n"
        + _DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_RULES
    )


_DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_RULES = """
V2.16 sequential-recovery addendum:
1. Keep the V2.14 risk-only contract and its exact ledger fact roles. The
   response has no runtime or broker authority. It cannot turn a hard blocker
   into positive edge or authorize a full entry.
2. supporting_fact_ids may contain only exact positive_facts IDs. A hard_blocker
   or any ID from contradicting_facts/invalidation_facts is never supporting
   evidence. contradicting_fact_ids may contain only exact IDs from those two
   adverse ledger arrays. Copy the exact token; never paraphrase it.
3. For setup_state=INVALID, still return VETO and cite an invalidation_facts ID.
   A no_supported_setup-only distribution episode may be retained only as an
   offline sequential-recovery observation seed when fresh liquidity is
   supportive and supportive micro tape conflicts with fresh program selling.
4. For setup_state=WAIT_CONFIRMATION, use CAUTION rather than VETO when the
   recovery-confirmation ledger has both liquidity_supportive and tape_supportive,
   has no invalidation fact, and only a fresh trigger recheck remains. Cite both
   positive facts. A current large-sell exhaustion recheck stays recheck-only.
5. Every retained seed remains WAIT/recovery_required with no immediate probe
   arm. A later natural Exact V2 snapshot may create an offline passive one-share
   arm only when the same symbol, venue, and session show a completed-bar advance,
   effective-price recovery, non-worsening spread and conservative execution
   cost, sell-momentum deceleration, and no hard blocker within 300 seconds.
6. Do not infer that a later confirmation exists from the current snapshot. Do
   not use outcomes, future prices, stock identity, thresholds, order price,
   quantity, provider/model changes, broker behavior, or bot state. Return the
   V2.14 JSON object only.
""".strip()


def decision_quality_v2_16_sequential_recovery_system_prompt(stage: str) -> str:
    """Return the offline V2.16 sequential-recovery risk prompt."""

    normalized = str(stage or "").strip().lower()
    if normalized != "entry":
        raise ValueError("decision-quality V2.16 currently supports entry only")
    return (
        _DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_RULES
        + "\n\n"
        + _DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_RULES
    )
