"""Build a read-only daily summary for scalping and swing runtime decisions."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.approval_contracts import approval_contract_for
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.threshold_cycle_ev_report import ev_report_paths


SUMMARY_DIR = REPORT_DIR / "runtime_approval_summary"
SWING_RUNTIME_APPROVAL_DIR = REPORT_DIR / "swing_runtime_approval"
PATTERN_LAB_CURRENTNESS_AUDIT_DIR = REPORT_DIR / "pattern_lab_currentness_audit"
PATTERN_LAB_PROPAGATION_AUDIT_DIR = REPORT_DIR / "pattern_lab_propagation_audit"
SWING_RUNTIME_APPROVAL_ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "data" / "threshold_cycle" / "approvals"
BOT_HISTORY_LOG = Path(__file__).resolve().parents[2] / "logs" / "bot_history.log"


_REASON_LABELS = {
    "critical_instrumentation_gap": "계측 gap",
    "db_load_gap": "DB gap",
    "runtime_family_guard_missing": "runtime guard 없음",
    "family_sample_floor_not_met": "표본 부족",
    "sample_floor_not_met": "표본 부족",
    "source_quality_blocker": "소스 품질 차단",
    "missing_action_bucket": "ADM action bucket 누락",
    "prompt_context_not_loaded": "ADM prompt context 미적재",
    "pyramid_sample_floor_not_met": "PYRAMID 표본 부족",
    "post_add_outcome_field_missing": "추가매수 outcome 누락",
    "final_exit_return_missing": "최종 exit 수익률 누락",
    "exit_only_delta_missing": "exit-only 비교 누락",
    "post_add_mae_missing": "추가매수 MAE 누락",
    "approval_artifact_missing": "approval artifact 없음",
    "approval_request_not_approved": "approval request 미승인",
    "approval_contract_missing": "approval 계약 미준비",
    "one_share_real_canary_approval_artifact_missing": "1주 real canary approval artifact 없음",
    "scale_in_real_canary_approval_artifact_missing": "scale-in approval artifact 없음",
    "selected_auto_bounded_live": "auto_bounded_live 선택",
    "hold": "유지",
    "hold_no_edge": "edge 부족",
    "freeze": "동결",
}

_FAMILY_DESCRIPTIONS = {
    "soft_stop_whipsaw_confirmation": "soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축",
    "holding_flow_ofi_smoothing": "보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축",
    "protect_trailing_smoothing": "protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축",
    "trailing_continuation": "trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축",
    "pre_submit_price_guard": "주문 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 진입 안전축",
    "score65_74_recovery_probe": "AI 점수 65~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 1주/소액 canary로 회수하는 축",
    "liquidity_gate_refined_candidate": "유동성 gate가 막은 후보의 후행 EV를 보고 gate 완화/유지 필요성을 판단하는 축",
    "overbought_gate_refined_candidate": "과열 gate가 막은 후보의 후행 EV를 보고 과열 차단 기준을 다듬는 축",
    "bad_entry_refined_canary": "진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축",
    "holding_exit_decision_matrix_advisory": "보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축",
    "scalp_entry_action_decision_matrix_advisory": "스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축",
    "lifecycle_decision_matrix_runtime": "개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축",
    "scale_in_price_guard": "추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축",
    "position_sizing_cap_release": "신규/추가매수 1주 cap을 풀 수 있는지 EV와 downside 기준으로 보는 축",
    "swing_model_floor": "스윙 추천 모델 floor 값을 올리거나 낮출 수 있는지 보는 선택 기준 축",
    "swing_selection_top_k": "스윙 추천 후보 수(top-k)를 늘리거나 줄일 수 있는지 보는 선택 폭 축",
    "swing_gatekeeper_accept_reject": "스윙 gatekeeper가 accept/reject한 후보의 후행 성과를 비교하는 진입 판단 축",
    "swing_gatekeeper_reject_cooldown": "gatekeeper reject 이후 같은 후보를 다시 볼 cooldown 시간을 조정하는 축",
    "swing_market_regime_sensitivity": "시장 regime에 따라 스윙 진입 민감도를 완화/강화할지 보는 축",
    "swing_pyramid_trigger": "스윙 보유 후 불타기(PYRAMID) 조건이 유효한지 보는 추가매수 축",
    "swing_avg_down_eligibility": "스윙 보유 후 물타기(AVG_DOWN) 조건이 유효한지 보는 추가매수 축",
    "swing_trailing_stop_time_stop": "스윙 trailing/time stop 청산 조건의 적정성을 보는 exit 축",
    "swing_holding_flow_defer": "스윙 보유/청산 AI가 청산 보류를 결정한 뒤 성과가 개선되는지 보는 축",
    "swing_entry_ofi_qi_execution_quality": "스윙 진입 시 OFI/QI와 주문품질이 실제 성과에 도움이 되는지 보는 축",
    "swing_scale_in_ofi_qi_confirmation": "스윙 추가매수 직전 OFI/QI 확인 신호가 유효한지 보는 축",
    "swing_exit_ofi_qi_smoothing": "스윙 청산 직전 OFI/QI로 EXIT 확정/보류를 다듬을 수 있는지 보는 축",
    "swing_scale_in_real_canary_phase0": "승인된 실제 스윙 보유분에 한해 PYRAMID/AVG_DOWN 1주 추가매수 canary를 열 수 있는지 보는 정책 축",
    "swing_one_share_real_canary_phase0": "승인된 스윙 후보에 한해 초기 BUY/SELL 1주 real canary execution 품질을 수집하는 정책 축",
    "panic_sell_defense": "패닉셀 구간의 stop/rebound simulation 결과로 방어 guard와 rollback 조건을 설계하는 축",
    "panic_entry_freeze_guard": "패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축",
    "panic_buy_runner_tp_canary": "패닉바잉 구간에서 fixed TP 전량청산 대비 runner 유지가 missed upside를 줄이는지 보는 축",
    "scalp_sim_overnight_ai_carry": "장마감 후 open 스캘핑 sim 포지션을 overnight_v1로 SELL_TODAY/HOLD_OVERNIGHT 분리해 다음날 lifecycle/EV label로 연결하는 source-only 축",
    "swing_strategy_discovery_sim": "스윙 safe pool 전체를 공격적 sim-only lifecycle arm으로 전개하고 label/EV를 축적하는 source-only 탐색 축",
    "institutional_flow_context": "외인/기관 수급 REST/WS 원천을 lifecycle matrix 공통 feature로 붙이는 source-only provenance 축",
}

_BASELINE_APPLICATION = {
    "holding_flow_ofi_smoothing": "기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON",
    "scale_in_price_guard": "기존 적용 유지: 추가매수 가격품질 guard ON",
    "pre_submit_price_guard": "기존 적용/검증 유지: 제출 직전 가격품질 guard 계열",
    "holding_exit_decision_matrix_advisory": "관찰/리포트 only: advisory live 적용 아님",
    "scalp_entry_action_decision_matrix_advisory": "운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선",
    "lifecycle_decision_matrix_runtime": "기본 OFF: 선택 시 micro canary env로 policy file/version만 연결, hard safety/submit guard 우선",
    "protect_trailing_smoothing": "관찰/리포트 only: protect/trailing live smoothing 미적용",
    "trailing_continuation": "관찰/리포트 only: trailing 연장 live 미적용",
    "bad_entry_refined_canary": "OFF/관찰 only: refined canary live 미적용",
    "liquidity_gate_refined_candidate": "관찰/리포트 only: gate 기준 변경 없음",
    "overbought_gate_refined_candidate": "관찰/리포트 only: gate 기준 변경 없음",
    "position_sizing_cap_release": "미적용: 1주 cap 유지",
    "swing_one_share_real_canary_phase0": "미적용: approval artifact 없이는 초기 BUY 실주문 금지",
    "swing_scale_in_real_canary_phase0": "미적용: approval artifact 없이는 실주문 추가매수 금지",
    "panic_sell_defense": "report-only: 주문/청산/threshold/runtime env 변경 없음",
    "panic_entry_freeze_guard": "계약 미준비: approval artifact를 만들어도 pre-submit freeze runtime 반영 불가",
    "panic_buy_runner_tp_canary": "report-only: TP/trailing/live exit 변경 없음",
    "scalp_sim_overnight_ai_carry": "source-only: sim 가상 청산/carry 기록만 수행, runtime threshold apply 권한 없음",
    "swing_strategy_discovery_sim": "source-only: 가상 후보/arm/label/EV 분석만 수행, runtime threshold apply 권한 없음",
    "institutional_flow_context": "source-only: lifecycle matrix feature/provenance 입력만 수행, 단독 BUY/scale-in/runtime apply 권한 없음",
}

_STATE_INTERPRETATIONS = {
    "adjust_up": "자동 반영 후보로 선택되면 PREOPEN env에 적용된다",
    "adjust_down": "자동 반영 후보로 선택되면 PREOPEN env에 적용된다",
    "hold": "현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다",
    "hold_sample": "축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다",
    "hold_no_edge": "명확한 edge가 없어 runtime 변경은 하지 않는다",
    "freeze": "계측/DB/safety 문제로 runtime 변경을 금지한다",
    "approval_required": "approval artifact가 있어야 다음 PREOPEN env 반영 후보가 된다",
    "approval_contract_missing": "approval artifact를 만들어도 소비할 코드 계약이 없어 live 반영할 수 없다",
}

_SCALPING_GATE_REVIEW = {
    "soft_stop_whipsaw_confirmation": {
        "gate_review_class": "selected_runtime_canary",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "보유/청산 canary로, 진입 hard gate 잔존 이슈가 아니다",
        "tuning_route": "threshold-cycle selected family attribution",
        "analysis_coverage": "runtime applied cohort",
    },
    "holding_flow_ofi_smoothing": {
        "gate_review_class": "existing_runtime_guard",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "기존 보유/청산 smoothing guard이며 진입 병목 gate가 아니다",
        "tuning_route": "holding/exit EV attribution",
        "analysis_coverage": "holding_flow_override events",
    },
    "protect_trailing_smoothing": {
        "gate_review_class": "report_only_holding_exit_candidate",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "보호/트레일링 청산 후보이며 BUY 전단 hard gate가 아니다",
        "tuning_route": "report-only until approval/rollback guard",
        "analysis_coverage": "holding/exit report source bundle",
    },
    "trailing_continuation": {
        "gate_review_class": "holding_exit_safety_freeze",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "trailing 이후 보유 연장축으로, 진입 튜닝 병목이 아니다",
        "tuning_route": "source-quality and GOOD_EXIT risk review",
        "analysis_coverage": "post-sell/holding-exit source bundle",
    },
    "pre_submit_price_guard": {
        "gate_review_class": "intentional_pre_submit_safety_guard",
        "legacy_hard_gate_risk": "intentional_safety_guard",
        "hard_gate_review": "quote stale/spread/passive probe 가격품질 차단은 의도적 submit safety guard다",
        "tuning_route": "pre_submit_price_guard EV/source-quality only",
        "analysis_coverage": "pre-submit guard events and missed-entry counterfactual",
    },
    "score65_74_recovery_probe": {
        "gate_review_class": "entry_unlock_probe",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "AI 점수 WAIT 구간 회수축이며 hard gate 잔존으로 닫힌 축이 아니다",
        "tuning_route": "runtime env/operator lock plus post-apply attribution",
        "analysis_coverage": "score65_74 cohort and submitted/probe split",
    },
    "liquidity_gate_refined_candidate": {
        "gate_review_class": "superseded_legacy_pre_ai_gate",
        "legacy_hard_gate_risk": "legacy_summary_superseded",
        "hard_gate_review": "legacy 유동성 pre-AI gate 항목이다. active route는 liquidity_pre_submit_guard_p1로 대체한다",
        "tuning_route": "pre-AI risk context + broker submit 직전 liquidity guard",
        "analysis_coverage": "blocked_liquidity counterfactual and pre_submit_liquidity_guard_block",
    },
    "overbought_gate_refined_candidate": {
        "gate_review_class": "superseded_legacy_pre_ai_gate",
        "legacy_hard_gate_risk": "legacy_summary_superseded",
        "hard_gate_review": "legacy 과열 pre-AI gate 항목이다. active route는 overbought_pullback_guard_p1로 대체한다",
        "tuning_route": "chase risk context + pullback/rebreak pre-submit guard",
        "analysis_coverage": "blocked_overbought counterfactual and pre_submit_overbought_pullback_guard_block",
    },
    "strength_momentum_soft_gate_p1": {
        "gate_review_class": "softened_pre_ai_gate",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "strength/momentum hard pre-AI block을 risk context로 내린 active route다",
        "tuning_route": "AI/counterfactual risk context, source-quality exception only",
        "analysis_coverage": "blocked_strength_momentum/blocked_vpw risk-context events",
    },
    "overbought_pullback_guard_p1": {
        "gate_review_class": "softened_pre_ai_plus_pre_submit_guard",
        "legacy_hard_gate_risk": "intentional_safety_guard",
        "hard_gate_review": "과열은 AI 평가를 허용하고 submit 직전 pullback/rebreak guard로만 막는다",
        "tuning_route": "overbought risk bucket EV and pre-submit guard attribution",
        "analysis_coverage": "blocked_overbought risk context + pre_submit_overbought_pullback_guard_block",
    },
    "liquidity_pre_submit_guard_p1": {
        "gate_review_class": "softened_pre_ai_plus_pre_submit_guard",
        "legacy_hard_gate_risk": "intentional_safety_guard",
        "hard_gate_review": "유동성은 AI/counterfactual을 허용하고 broker submit 직전 safety guard로 유지한다",
        "tuning_route": "liquidity risk bucket EV and real submit guard attribution",
        "analysis_coverage": "blocked_liquidity risk context + pre_submit_liquidity_guard_block",
    },
    "bad_entry_refined_canary": {
        "gate_review_class": "entry_quality_canary",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "진입 후 품질 canary이며 BUY 전단 hard gate 잔존 이슈가 아니다",
        "tuning_route": "bad-entry cohort EV and rollback guard",
        "analysis_coverage": "bad_entry_refined_candidate events",
    },
    "holding_exit_decision_matrix_advisory": {
        "gate_review_class": "advisory_report_only",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "advisory layer라 runtime hard gate가 아니다",
        "tuning_route": "report-only decision support contract",
        "analysis_coverage": "holding_exit_decision_matrix report",
    },
    "scalp_entry_action_decision_matrix_advisory": {
        "gate_review_class": "entry_adm_runtime_bias_operator_override",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "entry ADM은 bad-entry blacklist가 아니라 BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/NO_BUY action policy를 daily EV로 조정한다",
        "tuning_route": "daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env",
        "analysis_coverage": "entry snapshots, sim post-sell join, action bucket EV, runtime forced_action provenance",
    },
    "lifecycle_decision_matrix_runtime": {
        "gate_review_class": "umbrella_weighted_adm_runtime_policy",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "matrix policy는 hard safety veto, account/order/broker guard 뒤에서만 runtime action proposal을 낸다",
        "tuning_route": "postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env",
        "analysis_coverage": "candidate lifecycle rows, stage feature matrix, post-decision labels, fixed threshold role attribution",
    },
    "scale_in_price_guard": {
        "gate_review_class": "intentional_pre_submit_safety_guard",
        "legacy_hard_gate_risk": "intentional_safety_guard",
        "hard_gate_review": "추가매수 직전 가격품질 safety guard로 유지해야 한다",
        "tuning_route": "scale-in price quality EV/source-quality only",
        "analysis_coverage": "scale-in resolver and guard events",
    },
    "position_sizing_cap_release": {
        "gate_review_class": "policy_approval_or_contract_gap",
        "legacy_hard_gate_risk": "approval_or_contract_required",
        "hard_gate_review": "1주 cap은 legacy pre-AI gate가 아니라 position-size policy approval 문제다",
        "tuning_route": "separate approval artifact/workorder before runtime size change",
        "analysis_coverage": "position sizing EV and downside source bundle",
    },
    "position_sizing_dynamic_formula": {
        "gate_review_class": "policy_contract_gap",
        "legacy_hard_gate_risk": "approval_or_contract_required",
        "hard_gate_review": "수량 산식 owner이며 BUY hard gate 잔존 이슈가 아니다",
        "tuning_route": "notional/source-quality adjusted EV plus approval contract",
        "analysis_coverage": "position sizing source bundle",
    },
}

_SWING_GATE_REVIEW = {
    "swing_model_floor": {
        "gate_review_class": "approval_route_available",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "모델 floor는 approval/env route가 있는 선택축이다",
        "tuning_route": "swing_runtime_approvals artifact -> next PREOPEN dry-run env",
        "analysis_coverage": "model selection + combined real/sim EV",
    },
    "swing_selection_top_k": {
        "gate_review_class": "same_stage_deferred_selection_axis",
        "legacy_hard_gate_risk": "same_stage_deferred",
        "hard_gate_review": "top-k는 runtime guard가 있으며 현재는 model_floor와 같은 selection stage 충돌로 보류됐다",
        "tuning_route": "same-stage owner conflict 해소 후 approval route",
        "analysis_coverage": "recommendation CSV/DB load + simulation opportunity",
    },
    "swing_gatekeeper_accept_reject": {
        "gate_review_class": "legacy_hard_gate_contract_gap",
        "legacy_hard_gate_risk": "contract_gap",
        "hard_gate_review": "gatekeeper accept/reject 자체는 분석 표본은 있으나 runtime env guard가 없어 직접 튜닝 적용은 막혀 있다",
        "tuning_route": "workorder로 accept/reject policy guard를 만들거나 reject cooldown family로 우회 조정",
        "analysis_coverage": "blocked_gatekeeper_reject + swing_probe_entry_candidate",
    },
    "swing_gatekeeper_reject_cooldown": {
        "gate_review_class": "approval_route_available",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "reject 판단 자체가 아니라 cooldown 값을 조정하는 승인 가능 축이다",
        "tuning_route": "ML_GATEKEEPER_REJECT_COOLDOWN approval/env route",
        "analysis_coverage": "blocked_gatekeeper_reject + cooldown policy distribution",
    },
    "swing_market_regime_sensitivity": {
        "gate_review_class": "same_stage_deferred_entry_axis",
        "legacy_hard_gate_risk": "same_stage_deferred",
        "hard_gate_review": "market regime/gap 계열은 분석 표본이 있으나 오늘은 gatekeeper cooldown과 entry stage owner 충돌로 보류됐다",
        "tuning_route": "same-stage owner conflict 해소 후 SWING_MARKET_REGIME_SENSITIVITY route",
        "analysis_coverage": "blocked_swing_gap/blocked_swing_score_vpw + swing probe/counterfactual",
    },
    "swing_pyramid_trigger": {
        "gate_review_class": "runtime_contract_gap_scale_in_axis",
        "legacy_hard_gate_risk": "contract_gap",
        "hard_gate_review": "scale-in trigger 분석 표본은 있으나 runtime family guard가 없어 직접 적용은 막혀 있다",
        "tuning_route": "scale-in runtime guard/workorder before approval",
        "analysis_coverage": "scale_in observation and simulated add outcomes",
    },
    "swing_avg_down_eligibility": {
        "gate_review_class": "runtime_contract_gap_scale_in_axis",
        "legacy_hard_gate_risk": "contract_gap",
        "hard_gate_review": "AVG_DOWN은 의도적으로 실주문 차단 중이며 runtime family guard가 없다",
        "tuning_route": "policy/workorder first, real canary approval later",
        "analysis_coverage": "scale_in observation and simulated add outcomes",
    },
    "swing_trailing_stop_time_stop": {
        "gate_review_class": "runtime_contract_gap_exit_axis",
        "legacy_hard_gate_risk": "contract_gap",
        "hard_gate_review": "exit rule 분석축이나 live guard 계약이 없어 직접 튜닝 적용은 막혀 있다",
        "tuning_route": "exit runtime guard/workorder before approval",
        "analysis_coverage": "exit source + post-sell rebound",
    },
    "swing_holding_flow_defer": {
        "gate_review_class": "sample_or_contract_gap_holding_axis",
        "legacy_hard_gate_risk": "sample_or_contract_gap",
        "hard_gate_review": "보유/청산 defer 축으로 표본과 runtime guard가 아직 부족하다",
        "tuning_route": "sample floor + runtime guard contract",
        "analysis_coverage": "holding flow defer fields",
    },
    "swing_entry_ofi_qi_execution_quality": {
        "gate_review_class": "sample_or_contract_gap_entry_quality_axis",
        "legacy_hard_gate_risk": "sample_or_contract_gap",
        "hard_gate_review": "entry OFI/QI 품질축이며 stale/missing source와 runtime guard 계약이 먼저다",
        "tuning_route": "OFI/QI source-quality close, then approval/workorder",
        "analysis_coverage": "swing_entry_micro_context_observed",
    },
    "swing_scale_in_ofi_qi_confirmation": {
        "gate_review_class": "source_quality_contract_gap_scale_in_axis",
        "legacy_hard_gate_risk": "source_quality_or_contract_gap",
        "hard_gate_review": "scale-in OFI/QI source-quality blocker와 runtime guard 부재가 동시에 있다",
        "tuning_route": "source-quality blocker close, then scale-in guard contract",
        "analysis_coverage": "swing_scale_in_micro_context_observed",
    },
    "swing_exit_ofi_qi_smoothing": {
        "gate_review_class": "sample_or_contract_gap_exit_quality_axis",
        "legacy_hard_gate_risk": "sample_or_contract_gap",
        "hard_gate_review": "exit smoothing 품질축이며 표본과 runtime guard 계약이 먼저다",
        "tuning_route": "exit smoothing sample floor + guard contract",
        "analysis_coverage": "holding_flow_ofi_smoothing_applied",
    },
    "swing_scale_in_real_canary_phase0": {
        "gate_review_class": "policy_source_quality_block",
        "legacy_hard_gate_risk": "source_quality_or_approval_required",
        "hard_gate_review": "실제 추가매수 canary 정책축이며 OFI/QI source-quality와 별도 approval이 필요하다",
        "tuning_route": "scale-in approval artifact after source-quality pass",
        "analysis_coverage": "scale-in arm decisions + real-only execution quality",
    },
    "swing_one_share_real_canary_phase0": {
        "gate_review_class": "approval_route_available_policy_axis",
        "legacy_hard_gate_risk": "no_unreviewed_hard_gate",
        "hard_gate_review": "1주 real canary 정책축이며 승인 artifact로만 열린다",
        "tuning_route": "one-share approval artifact, global dry-run guard retained",
        "analysis_coverage": "approved target code provenance + real-only receipt",
    },
}


def _description(family: str) -> str:
    return _FAMILY_DESCRIPTIONS.get(family, "설명 미등록")


def _current_application(family: str, state: str, selected: bool) -> str:
    if selected:
        return "PREOPEN env 적용: 당일 runtime 변경 대상"
    if state == "approval_contract_missing":
        return "계약 미준비: approval artifact를 만들어도 live 반영 불가"
    baseline = _BASELINE_APPLICATION.get(family)
    if baseline:
        return baseline
    if family.startswith("swing_"):
        return "스윙 dry-run/probe 관찰: 실주문 변경 없음"
    if state in {"hold_sample", "freeze", "hold_no_edge"}:
        return "관찰/리포트 only: runtime 변경 없음"
    return "기존 상태 유지: runtime 변경 없음"


def _state_interpretation(state: str, selected: bool) -> str:
    if selected:
        return "threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨"
    return _STATE_INTERPRETATIONS.get(state, "판정 해석 미등록")


def _gate_review(domain: str, family: str, reasons: list[Any] | None = None) -> dict[str, Any]:
    reasons = [str(reason or "").strip() for reason in (reasons or []) if str(reason or "").strip()]
    if domain == "scalping":
        annotation = dict(_SCALPING_GATE_REVIEW.get(family) or {})
    elif domain == "swing":
        annotation = dict(_SWING_GATE_REVIEW.get(family) or {})
    else:
        annotation = {}
    if not annotation:
        annotation = {
            "gate_review_class": "not_classified",
            "legacy_hard_gate_risk": "manual_review_required",
            "hard_gate_review": "hard gate 분류 미등록",
            "tuning_route": "manual runtime approval review",
            "analysis_coverage": "unknown",
        }
    if any(reason.startswith("same_stage_owner_conflict:") for reason in reasons):
        annotation.setdefault("legacy_hard_gate_risk", "same_stage_deferred")
        annotation["gate_review_class"] = annotation.get("gate_review_class") or "same_stage_deferred"
    if "runtime_family_guard_missing" in reasons:
        annotation.setdefault("legacy_hard_gate_risk", "contract_gap")
    return annotation


def summary_paths(target_date: str) -> tuple[Path, Path]:
    base = SUMMARY_DIR / f"runtime_approval_summary_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


_JSON_LOAD_DIAGNOSTICS: list[dict[str, Any]] = []


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        _JSON_LOAD_DIAGNOSTICS.append(
            {
                "path": str(path),
                "status": "parse_error",
                "error": str(exc),
            }
        )
        return {}
    if not isinstance(payload, dict):
        _JSON_LOAD_DIAGNOSTICS.append(
            {
                "path": str(path),
                "status": "non_dict_json",
                "type": type(payload).__name__,
            }
        )
        return {}
    return payload


def _format_score(value: Any) -> str:
    if value is None:
        return "없음"
    try:
        return f"{float(value):.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        text = str(value).strip()
        return text or "없음"


def _as_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _reason_text(reasons: Any) -> str:
    if not isinstance(reasons, list):
        return "-"
    labels: list[str] = []
    for reason in reasons:
        text = str(reason or "").strip()
        if not text:
            continue
        label = _REASON_LABELS.get(text, text)
        if label not in labels:
            labels.append(label)
    return ", ".join(labels) if labels else "-"


def _candidate_by_family(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("family") or ""): item
        for item in items
        if isinstance(item, dict) and item.get("family")
    }


def _count_field(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field) or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _scalping_rows(ev_report: dict[str, Any], calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    candidates = _candidate_by_family(calibration_report.get("calibration_candidates"))
    selected = set((ev_report.get("runtime_apply") or {}).get("selected_families") or [])
    rows: list[dict[str, Any]] = []
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        if not family:
            continue
        candidate = candidates.get(family, {})
        state = str(item.get("calibration_state") or "-")
        reasons: list[str] = []
        if state == "hold_sample":
            reasons.append("family_sample_floor_not_met")
        if state == "freeze":
            reasons.append(str(item.get("calibration_reason") or "freeze"))
        if family in selected:
            reasons.append("selected_auto_bounded_live")
        elif state in {"hold", "hold_no_edge"}:
            reasons.append(str(item.get("calibration_reason") or state))
        row = {
            "domain": "scalping",
            "family": family,
            "description": _description(family),
            "state": state,
            "current_application": _current_application(family, state, family in selected),
            "state_interpretation": _state_interpretation(state, family in selected),
            "score": item.get("tradeoff_score", item.get("confidence", candidate.get("confidence"))),
            "score_label": _format_score(
                item.get("tradeoff_score", item.get("confidence", candidate.get("confidence")))
            ),
            "sample": {
                "count": item.get("sample_count"),
                "floor": item.get("sample_floor"),
            },
            "reasons": reasons,
            "reason_label": _reason_text(reasons),
            "selected_auto_bounded_live": family in selected,
        }
        row.update(_gate_review("scalping", family, reasons))
        rows.append(row)
    entry_adm = (
        ev_report.get("scalp_entry_action_decision_matrix")
        if isinstance(ev_report.get("scalp_entry_action_decision_matrix"), dict)
        else {}
    )
    if entry_adm:
        joined = _as_int(entry_adm.get("joined_sample"))
        floor = _as_int(entry_adm.get("sample_floor")) or 20
        state = "hold_sample" if joined < floor else "hold"
        reasons = []
        if not entry_adm.get("available"):
            reasons.append("source_quality_blocker")
        elif joined < floor:
            reasons.append("sample_floor_not_met")
        if entry_adm.get("missing_actions"):
            reasons.append("missing_action_bucket")
        if _as_int(entry_adm.get("prompt_applied_count")) == 0:
            reasons.append("prompt_context_not_loaded")
        row = {
            "domain": "scalping",
            "family": "scalp_entry_action_decision_matrix_advisory",
            "description": _description("scalp_entry_action_decision_matrix_advisory"),
            "state": state,
            "current_application": _current_application("scalp_entry_action_decision_matrix_advisory", state, False),
            "state_interpretation": "운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다",
            "score": entry_adm.get("source_quality_adjusted_ev_pct"),
            "score_label": _format_score(entry_adm.get("source_quality_adjusted_ev_pct")),
            "sample": {"count": joined, "floor": floor},
            "reasons": reasons or ["hold"],
            "reason_label": _reason_text(reasons or ["hold"]),
            "selected_auto_bounded_live": False,
            "runtime_bias_scope": "force_wait_force_drop_buy_defensive_bias",
        }
        row.update(_gate_review("scalping", "scalp_entry_action_decision_matrix_advisory", reasons))
        row["state_interpretation"] = (
            "운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. "
            "daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다."
        )
        rows.append(row)
    lifecycle_matrix = (
        ev_report.get("lifecycle_decision_matrix")
        if isinstance(ev_report.get("lifecycle_decision_matrix"), dict)
        else {}
    )
    if lifecycle_matrix:
        metrics = lifecycle_matrix.get("metrics") if isinstance(lifecycle_matrix.get("metrics"), dict) else {}
        total_rows = _as_int(metrics.get("total_rows", lifecycle_matrix.get("total_rows")))
        joined = _as_int(metrics.get("joined_rows", lifecycle_matrix.get("joined_rows")))
        floor = _as_int(lifecycle_matrix.get("sample_floor")) or 20
        pass_count = _as_int(metrics.get("policy_pass_count", lifecycle_matrix.get("policy_pass_count")))
        promote_ready = _as_int(metrics.get("promote_ready_count", lifecycle_matrix.get("promote_ready_count")))
        selected_family = "lifecycle_decision_matrix_runtime" in selected
        if not lifecycle_matrix.get("available"):
            state = "freeze"
            reasons = ["source_quality_blocker"]
        elif total_rows < floor or joined < 10:
            state = "hold_sample"
            reasons = ["sample_floor_not_met"]
        elif pass_count <= 0:
            state = "hold_no_edge"
            reasons = ["hold_no_edge"]
        else:
            state = "adjust_up" if selected_family else "hold"
            reasons = ["selected_auto_bounded_live"] if selected_family else ["hold"]
        policy_entries = (
            lifecycle_matrix.get("policy_entries")
            if isinstance(lifecycle_matrix.get("policy_entries"), list)
            else []
        )
        first_ev = next(
            (
                item.get("stage_ev_composite_pct")
                for item in policy_entries
                if isinstance(item, dict) and item.get("stage_ev_composite_pct") is not None
            ),
            None,
        )
        row = {
            "domain": "scalping",
            "family": "lifecycle_decision_matrix_runtime",
            "description": _description("lifecycle_decision_matrix_runtime"),
            "state": state,
            "current_application": _current_application(
                "lifecycle_decision_matrix_runtime", state, selected_family
            ),
            "state_interpretation": (
                "선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 "
                "항상 matrix proposal보다 우선한다."
            ),
            "score": first_ev,
            "score_label": _format_score(first_ev),
            "sample": {"count": total_rows, "floor": floor, "joined": joined},
            "reasons": reasons,
            "reason_label": _reason_text(reasons),
            "selected_auto_bounded_live": selected_family,
            "runtime_bias_scope": lifecycle_matrix.get("runtime_bias_scope") or "stage_action_proposal_micro_canary",
            "fixed_threshold_roles": lifecycle_matrix.get("fixed_threshold_roles") or {},
            "policy_pass_count": pass_count,
            "promote_ready_count": promote_ready,
        }
        row.update(_gate_review("scalping", "lifecycle_decision_matrix_runtime", reasons))
        rows.append(row)
    target_date = str(ev_report.get("date") or "").strip()
    overnight_path = REPORT_DIR / "scalp_sim_overnight" / f"scalp_sim_overnight_{target_date}.json"
    overnight_report = _load_json(overnight_path)
    if overnight_report:
        summary = overnight_report.get("summary") if isinstance(overnight_report.get("summary"), dict) else {}
        sample = _as_int(summary.get("decision_target"))
        row = {
            "domain": "scalping",
            "family": "scalp_sim_overnight_ai_carry",
            "description": _description("scalp_sim_overnight_ai_carry"),
            "state": "observe_only",
            "current_application": _current_application("scalp_sim_overnight_ai_carry", "observe_only", False),
            "state_interpretation": "runtime_effect=false source다. SELL_TODAY는 sim 가상 청산, HOLD_OVERNIGHT는 active_unrealized carry로만 남긴다.",
            "score": None,
            "score_label": "-",
            "sample": {
                "count": sample,
                "sell_today": _as_int(summary.get("sell_today")),
                "hold_overnight": _as_int(summary.get("hold_overnight")),
                "carry_open_count": _as_int(summary.get("carry_open_count")),
            },
            "reasons": ["observe_only"],
            "reason_label": "관찰 전용",
            "selected_auto_bounded_live": False,
            "runtime_effect": bool(overnight_report.get("runtime_effect")),
            "decision_authority": overnight_report.get("decision_authority"),
            "artifact": str(overnight_path),
        }
        row.update(_gate_review("scalping", "scalp_sim_overnight_ai_carry", ["observe_only"]))
        rows.append(row)
    return rows


def _approved_swing_request_ids(target_date: str) -> set[str]:
    if not target_date:
        return set()

    approved_ids: set[str] = set()
    artifact = _load_json(SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_runtime_approvals_{target_date}.json")
    for item in artifact.get("approved_requests") or []:
        if isinstance(item, dict) and bool(item.get("approved", True)) and item.get("approval_id"):
            approved_ids.add(str(item.get("approval_id")))

    one_share = _load_json(SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_one_share_real_canary_{target_date}.json")
    if bool(one_share.get("approved")) and str(one_share.get("policy_id") or "") == "swing_one_share_real_canary_phase0":
        approved_ids.update(str(value) for value in one_share.get("approved_request_ids") or [] if value)

    scale_in = _load_json(SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_scale_in_real_canary_{target_date}.json")
    if bool(scale_in.get("approved")) and str(scale_in.get("policy_id") or "") == "swing_scale_in_real_canary_phase0":
        approved_ids.update(str(value) for value in scale_in.get("approved_request_ids") or [] if value)

    return approved_ids


def _swing_rows(swing_report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = _candidate_by_family(swing_report.get("candidates"))
    rows: list[dict[str, Any]] = []
    blocked = swing_report.get("blocked_requests") if isinstance(swing_report.get("blocked_requests"), list) else []
    target_date = str(swing_report.get("date") or "").strip()
    for item in blocked:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        if not family:
            continue
        candidate = candidates.get(family, {})
        reasons = list(item.get("block_reasons") or [])
        row = {
            "domain": "swing",
            "family": family,
            "description": _description(family),
            "state": item.get("calibration_state") or candidate.get("calibration_state") or "-",
            "current_application": _current_application(
                family,
                str(item.get("calibration_state") or candidate.get("calibration_state") or "-"),
                False,
            ),
            "state_interpretation": _state_interpretation(
                str(item.get("calibration_state") or candidate.get("calibration_state") or "-"),
                False,
            ),
            "score": item.get("tradeoff_score"),
            "score_label": _format_score(item.get("tradeoff_score")),
            "sample": {
                "count": candidate.get("sample_count"),
                "floor": candidate.get("sample_floor"),
            },
            "reasons": reasons,
            "reason_label": _reason_text(reasons),
            "selected_auto_bounded_live": False,
        }
        row.update(_gate_review("swing", family, reasons))
        rows.append(row)
    requests = swing_report.get("approval_requests") if isinstance(swing_report.get("approval_requests"), list) else []
    blocked_families = {row["family"] for row in rows}
    approved_ids = _approved_swing_request_ids(target_date)
    for item in requests:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or item.get("policy_id") or "").strip()
        if not family or family in blocked_families:
            continue
        contract = approval_contract_for(family, target_date)
        approval_id = str(item.get("approval_id") or "")
        artifact_missing_reason = _swing_approval_artifact_reason(family, target_date)
        approval_reason = "" if approval_id and approval_id in approved_ids else artifact_missing_reason or "approval_request_not_approved"
        reasons = [approval_reason] if approval_reason else []
        row = {
            "domain": "swing",
            "family": family,
            "description": _description(family),
            "state": item.get("calibration_state") or "approval_required",
            "current_application": _current_application(family, str(item.get("calibration_state") or "approval_required"), False),
            "state_interpretation": _state_interpretation(str(item.get("calibration_state") or "approval_required"), False),
            "score": item.get("tradeoff_score"),
            "score_label": _format_score(item.get("tradeoff_score")),
            "sample": {
                "count": item.get("sample_count"),
                "floor": item.get("sample_floor"),
            },
            "reasons": reasons,
            "reason_label": _reason_text(reasons),
            "approval_id": item.get("approval_id"),
            "approval_artifact_approved": bool(approval_id and approval_id in approved_ids),
            "approval_contract_status": item.get("approval_contract_status") or contract.get("approval_contract_status"),
            "approval_live_ready": bool(item.get("approval_live_ready") or contract.get("approval_live_ready")),
            "approval_artifact_path": item.get("approval_artifact_path") or contract.get("approval_artifact_path"),
            "approval_contract_missing_components": item.get("approval_contract_missing_components")
            or contract.get("missing_components")
            or [],
            "selected_auto_bounded_live": False,
        }
        row.update(_gate_review("swing", family, reasons))
        rows.append(row)
    return rows


def _swing_approval_artifact_reason(family: str, target_date: str) -> str:
    if not target_date:
        return "approval_artifact_missing"
    if family == "swing_one_share_real_canary_phase0":
        artifact = SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_one_share_real_canary_{target_date}.json"
        return "" if artifact.exists() else "one_share_real_canary_approval_artifact_missing"
    if family == "swing_scale_in_real_canary_phase0":
        artifact = SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_scale_in_real_canary_{target_date}.json"
        return "" if artifact.exists() else "scale_in_real_canary_approval_artifact_missing"
    artifact = SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_runtime_approvals_{target_date}.json"
    return "" if artifact.exists() else "approval_artifact_missing"


def _panic_request_state(
    has_candidate: bool,
    sample_count: int,
    runtime_effect: Any,
    source_quality_blockers: list[Any] | None = None,
    approval_live_ready: bool = False,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if runtime_effect != "report_only_no_mutation":
        reasons.append("runtime_effect_not_report_only")
        return "freeze", reasons
    blockers = [str(item) for item in (source_quality_blockers or []) if str(item)]
    if blockers:
        reasons.append("source_quality_blocker")
        reasons.extend(blockers)
        return "freeze", reasons
    if sample_count <= 0:
        reasons.append("sample_floor_not_met")
        return "hold_sample", reasons
    if has_candidate:
        if not approval_live_ready:
            reasons.append("approval_contract_missing")
            return "approval_contract_missing", reasons
        reasons.append("approval_artifact_missing")
        return "approval_required", reasons
    reasons.append("hold")
    return "hold", reasons


def _has_report_only_candidate(candidate_status: dict[str, Any]) -> bool:
    return any(str(value or "") == "report_only_candidate" for value in candidate_status.values())


def _panic_rows(calibration_report: dict[str, Any], target_date: str) -> list[dict[str, Any]]:
    bundle = (
        calibration_report.get("calibration_source_bundle")
        if isinstance(calibration_report.get("calibration_source_bundle"), dict)
        else {}
    )
    source_metrics = bundle.get("source_metrics") if isinstance(bundle.get("source_metrics"), dict) else {}
    rows: list[dict[str, Any]] = []

    panic_sell = source_metrics.get("panic_sell_defense") if isinstance(source_metrics.get("panic_sell_defense"), dict) else {}
    if panic_sell:
        candidate_status = panic_sell.get("candidate_status") if isinstance(panic_sell.get("candidate_status"), dict) else {}
        sample_count = max(
            _as_int(panic_sell.get("stop_loss_exit_count")),
            _as_int(panic_sell.get("confirmation_eligible_exit_count")),
            _as_int(panic_sell.get("active_sim_probe_positions")),
        )
        source_quality_blockers = (
            panic_sell.get("source_quality_blockers")
            if isinstance(panic_sell.get("source_quality_blockers"), list)
            else []
        )
        contract = approval_contract_for("panic_entry_freeze_guard", target_date)
        state, reasons = _panic_request_state(
            _has_report_only_candidate(candidate_status),
            sample_count,
            panic_sell.get("runtime_effect"),
            source_quality_blockers,
            bool(contract.get("approval_live_ready")),
        )
        rows.append(
            {
                "domain": "panic_sell",
                "family": "panic_entry_freeze_guard",
                "description": _description("panic_entry_freeze_guard"),
                "state": state,
                "current_application": _current_application("panic_entry_freeze_guard", state, False),
                "state_interpretation": (
                    "simulation/counterfactual 기반 runtime 전환 승인요청 후보이며 approval artifact 전 live 반영 없음"
                    if state == "approval_required"
                    else _state_interpretation(state, False)
                ),
                "score": panic_sell.get("microstructure_max_panic_score"),
                "score_label": _format_score(panic_sell.get("microstructure_max_panic_score")),
                "sample": {"count": sample_count, "floor": 1},
                "reasons": reasons,
                "reason_label": _reason_text(reasons),
                "panic_regime_mode": panic_sell.get("panic_regime_mode"),
                "panic_regime_decision_authority": panic_sell.get("panic_regime_decision_authority"),
                "panic_regime_runtime_effect": panic_sell.get("panic_regime_runtime_effect"),
                "selected_auto_bounded_live": False,
                "candidate_status": candidate_status,
                "source_quality_blockers": source_quality_blockers,
                "market_breadth_followup_candidate": bool(panic_sell.get("market_breadth_followup_candidate")),
                "approval_contract_status": contract.get("approval_contract_status"),
                "approval_live_ready": bool(contract.get("approval_live_ready")),
                "approval_artifact_path": contract.get("approval_artifact_path"),
                "approval_contract_missing_components": contract.get("missing_components") or [],
            }
        )

    panic_buy = source_metrics.get("panic_buying") if isinstance(source_metrics.get("panic_buying"), dict) else {}
    if panic_buy:
        candidate_status = panic_buy.get("candidate_status") if isinstance(panic_buy.get("candidate_status"), dict) else {}
        source_quality_blockers = (
            panic_buy.get("source_quality_blockers")
            if isinstance(panic_buy.get("source_quality_blockers"), list)
            else []
        )
        sample_count = max(
            _as_int(panic_buy.get("panic_buy_active_count")),
            _as_int(panic_buy.get("tp_counterfactual_count")),
            _as_int(panic_buy.get("trailing_winner_count")),
        )
        contract = approval_contract_for("panic_buy_runner_tp_canary", target_date)
        state, reasons = _panic_request_state(
            _has_report_only_candidate(candidate_status),
            sample_count,
            panic_buy.get("runtime_effect"),
            source_quality_blockers,
            bool(contract.get("approval_live_ready")),
        )
        rows.append(
            {
                "domain": "panic_buying",
                "family": "panic_buy_runner_tp_canary",
                "description": _description("panic_buy_runner_tp_canary"),
                "state": state,
                "current_application": _current_application("panic_buy_runner_tp_canary", state, False),
                "state_interpretation": (
                    "TP counterfactual 기반 runtime 전환 승인요청 후보이며 approval artifact 전 live TP 변경 없음"
                    if state == "approval_required"
                    else _state_interpretation(state, False)
                ),
                "score": panic_buy.get("max_panic_buy_score"),
                "score_label": _format_score(panic_buy.get("max_panic_buy_score")),
                "sample": {"count": sample_count, "floor": 1},
                "reasons": reasons,
                "reason_label": _reason_text(reasons),
                "panic_buy_regime_mode": panic_buy.get("panic_buy_regime_mode"),
                "panic_buy_regime_decision_authority": panic_buy.get("panic_buy_regime_decision_authority"),
                "panic_buy_regime_runtime_effect": panic_buy.get("panic_buy_regime_runtime_effect"),
                "market_wide_panic_buy_confirmed": bool(panic_buy.get("market_wide_panic_buy_confirmed")),
                "market_breadth_risk_on_advisory": bool(panic_buy.get("market_breadth_risk_on_advisory")),
                "source_quality_blockers": source_quality_blockers,
                "selected_auto_bounded_live": False,
                "candidate_status": candidate_status,
                "approval_contract_status": contract.get("approval_contract_status"),
                "approval_live_ready": bool(contract.get("approval_live_ready")),
                "approval_artifact_path": contract.get("approval_artifact_path"),
                "approval_contract_missing_components": contract.get("missing_components") or [],
            }
        )
    return rows


def _parse_kst_log_time(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _bot_start_times(target_date: str) -> list[datetime]:
    if not BOT_HISTORY_LOG.exists():
        return []
    pattern = re.compile(rf"^\[{re.escape(target_date)} (\d{{2}}:\d{{2}}:\d{{2}})\].*KORStockScan v")
    starts: list[datetime] = []
    try:
        for line in BOT_HISTORY_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            parsed = _parse_kst_log_time(f"{target_date} {match.group(1)}")
            if parsed:
                starts.append(parsed)
    except OSError:
        return []
    return starts


def _application_timing(target_date: str, ev_report: dict[str, Any]) -> dict[str, Any]:
    runtime = ev_report.get("runtime_apply") if isinstance(ev_report.get("runtime_apply"), dict) else {}
    runtime_env_file = runtime.get("runtime_env_file")
    env_path = Path(str(runtime_env_file)) if runtime_env_file else None
    env_generated_at = None
    if env_path and env_path.exists():
        env_generated_at = datetime.fromtimestamp(env_path.stat().st_mtime).isoformat(timespec="seconds")
    starts = _bot_start_times(target_date)
    env_dt = datetime.fromisoformat(env_generated_at) if env_generated_at else None
    first_start = starts[0] if starts else None
    first_after_env = next((item for item in starts if env_dt and item >= env_dt.replace(tzinfo=None)), None)
    pre_env_boot_gap = bool(first_start and env_dt and first_start < env_dt.replace(tzinfo=None))
    return {
        "runtime_env_file": str(env_path) if env_path else None,
        "env_generated_at": env_generated_at,
        "first_bot_start_at": first_start.isoformat(timespec="seconds") if first_start else None,
        "first_bot_start_after_env_at": first_after_env.isoformat(timespec="seconds") if first_after_env else None,
        "pre_env_boot_gap": pre_env_boot_gap,
    }


def _audit_summary(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "available": bool(payload),
        "artifact": str(path) if path.exists() else None,
        "status": payload.get("status") if payload else "missing",
        "fail_count": _as_int(summary.get("fail_count")),
        "warning_count": _as_int(summary.get("warning_count")),
        "runtime_effect": bool(payload.get("runtime_effect")) if payload else False,
        "decision_authority": payload.get("decision_authority") if payload else None,
    }


def _entry_adm_summary(ev_report: dict[str, Any], source_path: str | None) -> dict[str, Any]:
    adm = (
        ev_report.get("scalp_entry_action_decision_matrix")
        if isinstance(ev_report.get("scalp_entry_action_decision_matrix"), dict)
        else {}
    )
    expected_actions = [
        "BUY_NOW",
        "WAIT_REQUOTE",
        "SKIP_STALE",
        "BUY_DEFENSIVE",
        "NO_BUY_AI",
        "SKIP_SOURCE_QUALITY",
        "SKIP_PRE_SUBMIT_SAFETY",
    ]
    if not adm:
        return {
            "available": False,
            "artifact": source_path,
            "status": "missing",
            "runtime_effect": False,
            "decision_authority": "entry_adm_runtime_bias_operator_override",
            "runtime_bias_scope": "force_wait_force_drop_buy_defensive_bias",
            "expected_actions": expected_actions,
            "warnings": ["scalp_entry_action_decision_matrix_missing"],
            "ready_for_daily_policy_tuning": False,
        }

    joined = _as_int(adm.get("joined_sample"))
    floor = _as_int(adm.get("sample_floor")) or 20
    missing_actions = adm.get("missing_actions") if isinstance(adm.get("missing_actions"), list) else []
    prompt_applied_count = _as_int(adm.get("prompt_applied_count"))
    top_actions = adm.get("top_actions") if isinstance(adm.get("top_actions"), list) else []
    joined_action_ev_pct = None
    for action in top_actions:
        if not isinstance(action, dict):
            continue
        if _as_int(action.get("joined_sample")) > 0:
            joined_action_ev_pct = action.get("source_quality_adjusted_ev_pct")
            break
    warnings: list[str] = []
    if not adm.get("available", True):
        warnings.append("source_quality_blocker")
    if joined < floor:
        warnings.append("joined_sample_below_sample_floor")
    if missing_actions:
        warnings.append("missing_action_bucket")
    if prompt_applied_count == 0:
        warnings.append("prompt_context_not_loaded")

    return {
        "available": bool(adm.get("available", True)),
        "artifact": source_path or adm.get("artifact"),
        "status": adm.get("status"),
        "runtime_effect": False,
        "decision_authority": "entry_adm_runtime_bias_operator_override",
        "runtime_bias_scope": "force_wait_force_drop_buy_defensive_bias",
        "application_mode": "operator_override_runtime_bias",
        "primary_decision_metric": adm.get("primary_decision_metric") or "source_quality_adjusted_ev_pct",
        "source_quality_adjusted_ev_pct": adm.get("source_quality_adjusted_ev_pct"),
        "joined_action_ev_pct": joined_action_ev_pct,
        "top_actions": top_actions,
        "joined_sample": joined,
        "sample_floor": floor,
        "prompt_applied_count": prompt_applied_count,
        "missing_actions": missing_actions,
        "expected_actions": expected_actions,
        "tuning_cycle": "scalp_entry_action_decision_matrix -> threshold_cycle_ev -> runtime_approval_summary -> code_improvement_workorder -> pattern_lab source bundle -> next runtime env",
        "warnings": warnings,
        "ready_for_daily_policy_tuning": not warnings,
    }


def _lifecycle_matrix_summary(ev_report: dict[str, Any], source_path: str | None) -> dict[str, Any]:
    matrix = (
        ev_report.get("lifecycle_decision_matrix")
        if isinstance(ev_report.get("lifecycle_decision_matrix"), dict)
        else {}
    )
    if not matrix:
        return {
            "available": False,
            "artifact": source_path,
            "status": "missing",
            "runtime_effect": False,
            "decision_authority": "lifecycle_weighted_adm_runtime_policy",
            "runtime_bias_scope": "stage_action_proposal_micro_canary",
            "warnings": ["lifecycle_decision_matrix_missing"],
            "ready_for_bounded_apply": False,
        }

    total_rows = _as_int(matrix.get("total_rows"))
    joined_rows = _as_int(matrix.get("joined_rows"))
    policy_pass_count = _as_int(matrix.get("policy_pass_count"))
    promote_ready_count = _as_int(matrix.get("promote_ready_count"))
    warnings: list[str] = []
    if not matrix.get("available", True):
        warnings.append("source_quality_blocker")
    if total_rows < 20 or joined_rows < 10:
        warnings.append("joined_sample_below_sample_floor")
    if policy_pass_count <= 0:
        warnings.append("policy_pass_arm_missing")

    return {
        "available": bool(matrix.get("available", True)),
        "artifact": source_path or matrix.get("artifact"),
        "status": matrix.get("status"),
        "matrix_version": matrix.get("matrix_version"),
        "runtime_effect": bool(matrix.get("runtime_effect")),
        "decision_authority": matrix.get("decision_authority") or "lifecycle_weighted_adm_runtime_policy",
        "runtime_bias_scope": "stage_action_proposal_micro_canary",
        "application_mode": "auto_bounded_micro_canary",
        "primary_decision_metric": matrix.get("primary_decision_metric") or "stage_ev_composite_pct",
        "total_rows": total_rows,
        "joined_rows": joined_rows,
        "sample_floor": 20,
        "policy_pass_count": policy_pass_count,
        "promote_ready_count": promote_ready_count,
        "policy_entries": matrix.get("policy_entries") if isinstance(matrix.get("policy_entries"), list) else [],
        "fixed_threshold_roles": matrix.get("fixed_threshold_roles") if isinstance(matrix.get("fixed_threshold_roles"), dict) else {},
        "tuning_cycle": "lifecycle_decision_matrix -> threshold_cycle_ev -> runtime_approval_summary -> next preopen bounded env",
        "warnings": warnings,
        "ready_for_bounded_apply": not warnings,
    }


def _swing_strategy_discovery_summary(ev_report: dict[str, Any]) -> dict[str, Any]:
    payload = ev_report.get("swing_strategy_discovery") if isinstance(ev_report.get("swing_strategy_discovery"), dict) else {}
    available = bool(payload.get("available"))
    warnings = []
    if not available:
        warnings.append("swing_strategy_discovery_ev_missing")
    if int(payload.get("pending_future_quote_count") or 0) > 0:
        warnings.append("pending_future_quotes")
    return {
        "family": "swing_strategy_discovery_sim",
        "available": available,
        "artifact": payload.get("artifact"),
        "description": _FAMILY_DESCRIPTIONS["swing_strategy_discovery_sim"],
        "baseline_application": _BASELINE_APPLICATION["swing_strategy_discovery_sim"],
        "runtime_effect": False,
        "runtime_mutation_allowed": False,
        "decision_authority": payload.get("decision_authority") or "swing_sim_exploration_only",
        "candidate_count": int(payload.get("candidate_count") or 0),
        "arm_count": int(payload.get("arm_count") or 0),
        "labeled_sample_count": int(payload.get("labeled_sample_count") or 0),
        "pending_future_quote_count": int(payload.get("pending_future_quote_count") or 0),
        "top_surviving_arm": payload.get("top_surviving_arm"),
        "avoid_bucket_count": int(payload.get("avoid_bucket_count") or 0),
        "state_interpretation": "source-only exploration. Surviving arms can create future source-quality/workorder inputs but cannot apply runtime env.",
        "warnings": warnings,
    }


def _institutional_flow_context_summary(ev_report: dict[str, Any]) -> dict[str, Any]:
    payload = ev_report.get("institutional_flow_context") if isinstance(ev_report.get("institutional_flow_context"), dict) else {}
    available = bool(payload.get("available"))
    warnings = []
    if not available:
        warnings.append("institutional_flow_context_missing")
    if int(payload.get("token_error_count") or 0) > 0:
        warnings.append("kiwoom_token_error")
    return {
        "family": "institutional_flow_context",
        "available": available,
        "artifact": payload.get("artifact"),
        "description": _FAMILY_DESCRIPTIONS["institutional_flow_context"],
        "baseline_application": _BASELINE_APPLICATION["institutional_flow_context"],
        "runtime_effect": False,
        "runtime_mutation_allowed": False,
        "decision_authority": payload.get("decision_authority") or "source_only_lifecycle_feature",
        "row_count": int(payload.get("row_count") or 0),
        "ok_count": int(payload.get("ok_count") or 0),
        "partial_count": int(payload.get("partial_count") or 0),
        "missing_count": int(payload.get("missing_count") or 0),
        "token_error_count": int(payload.get("token_error_count") or 0),
        "join_rate_pct": payload.get("join_rate_pct"),
        "source_mix": payload.get("source_mix") or {},
        "top_net_buy": payload.get("top_net_buy") or [],
        "state_interpretation": "source-only feature. Missing/stale data cannot change lifecycle runtime action.",
        "warnings": warnings,
    }


def build_runtime_approval_summary(target_date: str) -> dict[str, Any]:
    _JSON_LOAD_DIAGNOSTICS.clear()
    target_date = str(target_date).strip()
    ev_json, _ = ev_report_paths(target_date)
    swing_path = SWING_RUNTIME_APPROVAL_DIR / f"swing_runtime_approval_{target_date}.json"
    ev_report = _load_json(ev_json)
    swing_report = _load_json(swing_path)
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    calibration_source = sources.get("calibration")
    scalp_entry_adm_path = sources.get("scalp_entry_action_decision_matrix")
    lifecycle_matrix_path = sources.get("lifecycle_decision_matrix")
    lifecycle_ai_context_path = sources.get("lifecycle_ai_context")
    lifecycle_ai_context_attribution_path = sources.get("lifecycle_ai_context_attribution")
    institutional_flow_path = sources.get("institutional_flow_context")
    calibration_report = _load_json(Path(str(calibration_source))) if calibration_source else {}
    currentness_path = Path(str(sources.get("pattern_lab_currentness_audit"))) if sources.get("pattern_lab_currentness_audit") else PATTERN_LAB_CURRENTNESS_AUDIT_DIR / f"pattern_lab_currentness_audit_{target_date}.json"
    propagation_path = Path(str(sources.get("pattern_lab_propagation_audit"))) if sources.get("pattern_lab_propagation_audit") else PATTERN_LAB_PROPAGATION_AUDIT_DIR / f"pattern_lab_propagation_audit_{target_date}.json"
    currentness_audit = _audit_summary(currentness_path)
    propagation_audit = _audit_summary(propagation_path)
    scalping_rows = _scalping_rows(ev_report, calibration_report)
    swing_rows = _swing_rows(swing_report)
    panic_rows = _panic_rows(calibration_report, target_date)
    scalp_entry_adm_summary = _entry_adm_summary(ev_report, scalp_entry_adm_path)
    lifecycle_matrix_summary = _lifecycle_matrix_summary(ev_report, lifecycle_matrix_path)
    swing_discovery_summary = _swing_strategy_discovery_summary(ev_report)
    institutional_flow_summary = _institutional_flow_context_summary(ev_report)
    source_load_warnings = [
        f"source_load_{item.get('status')}:{Path(str(item.get('path') or '')).name}"
        for item in _JSON_LOAD_DIAGNOSTICS
    ]
    report = {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "runtime_approval_summary",
        "purpose": "read_only_summary_only_no_runtime_mutation",
        "runtime_mutation_allowed": False,
        "sources": {
            "threshold_cycle_ev": str(ev_json) if ev_json.exists() else None,
            "swing_runtime_approval": str(swing_path) if swing_path.exists() else None,
            "scalp_entry_action_decision_matrix": scalp_entry_adm_path,
            "lifecycle_decision_matrix": lifecycle_matrix_path,
            "lifecycle_ai_context": lifecycle_ai_context_path,
            "lifecycle_ai_context_attribution": lifecycle_ai_context_attribution_path,
            "institutional_flow_context": institutional_flow_path,
            "pattern_lab_currentness_audit": str(currentness_path) if currentness_path.exists() else None,
            "pattern_lab_propagation_audit": str(propagation_path) if propagation_path.exists() else None,
        },
        "source_load_diagnostics": _JSON_LOAD_DIAGNOSTICS.copy(),
        "summary": {
            "scalping_items": len(scalping_rows),
            "scalping_selected_auto_bounded_live": sum(1 for row in scalping_rows if row["selected_auto_bounded_live"]),
            "scalping_legacy_hard_gate_risk_counts": _count_field(scalping_rows, "legacy_hard_gate_risk"),
            "swing_blocked": len(swing_rows),
            "swing_legacy_hard_gate_risk_counts": _count_field(swing_rows, "legacy_hard_gate_risk"),
            "panic_approval_requested": sum(1 for row in panic_rows if row.get("state") == "approval_required"),
            "swing_requested": int((swing_report.get("summary") or {}).get("requested") or 0)
            if isinstance(swing_report.get("summary"), dict)
            else 0,
            "swing_approved": sum(
                1
                for row in swing_rows
                if row.get("state") == "approval_required" and bool(row.get("approval_artifact_approved"))
            ),
            "pattern_lab_currentness_status": currentness_audit.get("status"),
            "pattern_lab_propagation_status": propagation_audit.get("status"),
            "scalp_entry_adm_status": (
                (ev_report.get("scalp_entry_action_decision_matrix") or {}).get("status")
                if isinstance(ev_report.get("scalp_entry_action_decision_matrix"), dict)
                else None
            ),
            "scalp_entry_adm_ready_for_daily_policy_tuning": scalp_entry_adm_summary.get(
                "ready_for_daily_policy_tuning"
            ),
            "scalp_entry_adm_warnings": scalp_entry_adm_summary.get("warnings"),
            "lifecycle_matrix_status": (
                (ev_report.get("lifecycle_decision_matrix") or {}).get("status")
                if isinstance(ev_report.get("lifecycle_decision_matrix"), dict)
                else None
            ),
            "lifecycle_matrix_ready_for_bounded_apply": lifecycle_matrix_summary.get("ready_for_bounded_apply"),
            "lifecycle_matrix_warnings": lifecycle_matrix_summary.get("warnings"),
            "lifecycle_ai_context_applied_count": (
                (ev_report.get("lifecycle_ai_context_attribution") or {}).get("context_applied_count")
                if isinstance(ev_report.get("lifecycle_ai_context_attribution"), dict)
                else 0
            ),
            "lifecycle_ai_context_prompt_stage_count": (
                (ev_report.get("lifecycle_ai_context") or {}).get("prompt_stage_count")
                if isinstance(ev_report.get("lifecycle_ai_context"), dict)
                else 0
            ),
            "swing_strategy_discovery_available": swing_discovery_summary.get("available"),
            "swing_strategy_discovery_labeled_sample_count": swing_discovery_summary.get("labeled_sample_count"),
            "swing_strategy_discovery_pending_future_quote_count": swing_discovery_summary.get("pending_future_quote_count"),
            "institutional_flow_available": institutional_flow_summary.get("available"),
            "institutional_flow_join_rate_pct": institutional_flow_summary.get("join_rate_pct"),
        },
        "application_timing": _application_timing(target_date, ev_report),
        "scalp_entry_action_decision_matrix": scalp_entry_adm_summary,
        "lifecycle_decision_matrix": lifecycle_matrix_summary,
        "lifecycle_ai_context": ev_report.get("lifecycle_ai_context")
        if isinstance(ev_report.get("lifecycle_ai_context"), dict)
        else {},
        "lifecycle_ai_context_attribution": ev_report.get("lifecycle_ai_context_attribution")
        if isinstance(ev_report.get("lifecycle_ai_context_attribution"), dict)
        else {},
        "swing_strategy_discovery": swing_discovery_summary,
        "institutional_flow_context": institutional_flow_summary,
        "pattern_lab_currentness_audit": currentness_audit,
        "pattern_lab_propagation_audit": propagation_audit,
        "scalping": scalping_rows,
        "swing": swing_rows,
        "panic": panic_rows,
        "warnings": [
            message
            for message in [
                "threshold_cycle_ev_missing" if not ev_json.exists() else "",
                "swing_runtime_approval_missing" if not swing_path.exists() else "",
                "scalp_entry_action_decision_matrix_missing" if not scalp_entry_adm_path else "",
                "lifecycle_decision_matrix_missing" if not lifecycle_matrix_path else "",
                "institutional_flow_context_missing" if not institutional_flow_path else "",
                "pattern_lab_currentness_audit_missing" if not currentness_path.exists() else "",
                "pattern_lab_propagation_audit_missing" if not propagation_path.exists() else "",
                *source_load_warnings,
            ]
            if message
        ],
    }
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = summary_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_runtime_approval_summary_markdown(report), encoding="utf-8")
    return report


def _render_rows(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    if not rows:
        lines.append("| - | - | - | - | - | - | - | - | - | - |")
        return lines
    for row in rows:
        contract_status = row.get("approval_contract_status") or "-"
        if row.get("approval_live_ready") is True:
            contract_status = "ready"
        lines.append(
            f"| `{row.get('family')}` | {row.get('description') or '-'} | {row.get('current_application') or '-'} | `{row.get('state')}` | `{row.get('gate_review_class') or '-'}` | {row.get('tuning_route') or '-'} | {row.get('state_interpretation') or '-'} | {row.get('score_label')} | `{contract_status}` | {row.get('reason_label')} |"
        )
    return lines


def render_runtime_approval_summary_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    timing = report.get("application_timing") if isinstance(report.get("application_timing"), dict) else {}
    scalping = report.get("scalping") if isinstance(report.get("scalping"), list) else []
    swing = report.get("swing") if isinstance(report.get("swing"), list) else []
    panic = report.get("panic") if isinstance(report.get("panic"), list) else []
    entry_adm = (
        report.get("scalp_entry_action_decision_matrix")
        if isinstance(report.get("scalp_entry_action_decision_matrix"), dict)
        else {}
    )
    lifecycle_matrix = (
        report.get("lifecycle_decision_matrix")
        if isinstance(report.get("lifecycle_decision_matrix"), dict)
        else {}
    )
    lifecycle_ai_context = (
        report.get("lifecycle_ai_context")
        if isinstance(report.get("lifecycle_ai_context"), dict)
        else {}
    )
    lifecycle_ai_context_attribution = (
        report.get("lifecycle_ai_context_attribution")
        if isinstance(report.get("lifecycle_ai_context_attribution"), dict)
        else {}
    )
    swing_discovery = (
        report.get("swing_strategy_discovery")
        if isinstance(report.get("swing_strategy_discovery"), dict)
        else {}
    )
    institutional_flow = (
        report.get("institutional_flow_context")
        if isinstance(report.get("institutional_flow_context"), dict)
        else {}
    )
    currentness = report.get("pattern_lab_currentness_audit") if isinstance(report.get("pattern_lab_currentness_audit"), dict) else {}
    propagation = report.get("pattern_lab_propagation_audit") if isinstance(report.get("pattern_lab_propagation_audit"), dict) else {}
    source_load_diagnostics = (
        report.get("source_load_diagnostics") if isinstance(report.get("source_load_diagnostics"), list) else []
    )
    lines = [
        f"# Runtime Approval Summary - {report.get('date')}",
        "",
        "- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.",
        "- runtime_mutation_allowed: `False`",
        f"- scalping_items/selected: `{summary.get('scalping_items')}` / `{summary.get('scalping_selected_auto_bounded_live')}`",
        f"- scalping_legacy_hard_gate_risk_counts: `{summary.get('scalping_legacy_hard_gate_risk_counts')}`",
        f"- swing_blocked/requested/approved: `{summary.get('swing_blocked')}` / `{summary.get('swing_requested')}` / `{summary.get('swing_approved')}`",
        f"- swing_legacy_hard_gate_risk_counts: `{summary.get('swing_legacy_hard_gate_risk_counts')}`",
        f"- panic_approval_requested: `{summary.get('panic_approval_requested')}`",
        f"- scalp_entry_adm_status: `{summary.get('scalp_entry_adm_status')}`",
        f"- lifecycle_matrix_status: `{summary.get('lifecycle_matrix_status')}`",
        f"- lifecycle_ai_context prompt/applied: `{summary.get('lifecycle_ai_context_prompt_stage_count')}` / `{summary.get('lifecycle_ai_context_applied_count')}`",
        f"- swing_strategy_discovery_labeled/pending: `{summary.get('swing_strategy_discovery_labeled_sample_count')}` / `{summary.get('swing_strategy_discovery_pending_future_quote_count')}`",
        f"- institutional_flow_available/join_rate: `{summary.get('institutional_flow_available')}` / `{summary.get('institutional_flow_join_rate_pct')}`",
        f"- pattern_lab_currentness_status: `{summary.get('pattern_lab_currentness_status')}`",
        f"- pattern_lab_propagation_status: `{summary.get('pattern_lab_propagation_status')}`",
        f"- env_generated_at: `{timing.get('env_generated_at') or '-'}`",
        f"- first_bot_start_at: `{timing.get('first_bot_start_at') or '-'}`",
        f"- first_bot_start_after_env_at: `{timing.get('first_bot_start_after_env_at') or '-'}`",
        f"- pre_env_boot_gap: `{timing.get('pre_env_boot_gap')}`",
        "",
        "## Scalping",
        *_render_rows(scalping),
        "",
        "## Scalp Entry ADM",
        f"- status: `{entry_adm.get('status')}`",
        f"- runtime_bias_scope: `{entry_adm.get('runtime_bias_scope')}`",
        f"- joined_action_ev_pct: `{entry_adm.get('joined_action_ev_pct')}`",
        f"- joined_sample/sample_floor: `{entry_adm.get('joined_sample')}` / `{entry_adm.get('sample_floor')}`",
        f"- prompt_applied_count: `{entry_adm.get('prompt_applied_count')}`",
        f"- missing_actions: `{entry_adm.get('missing_actions') or []}`",
        f"- top_actions: `{entry_adm.get('top_actions') or []}`",
        f"- ready_for_daily_policy_tuning: `{entry_adm.get('ready_for_daily_policy_tuning')}`",
        f"- warnings: `{entry_adm.get('warnings') or []}`",
        "",
        "## Institutional Flow Context",
        f"- artifact: `{institutional_flow.get('artifact') or '-'}`",
        f"- authority: `{institutional_flow.get('decision_authority') or '-'}`",
        f"- rows ok/partial/missing/token_error: `{institutional_flow.get('ok_count')}` / `{institutional_flow.get('partial_count')}` / `{institutional_flow.get('missing_count')}` / `{institutional_flow.get('token_error_count')}`",
        f"- join_rate_pct: `{institutional_flow.get('join_rate_pct')}`",
        f"- source_mix: `{institutional_flow.get('source_mix') or {}}`",
        f"- top_net_buy: `{institutional_flow.get('top_net_buy') or []}`",
        f"- warnings: `{institutional_flow.get('warnings') or []}`",
        "",
        "## Lifecycle Decision Matrix",
        f"- status: `{lifecycle_matrix.get('status')}`",
        f"- matrix_version: `{lifecycle_matrix.get('matrix_version') or '-'}`",
        f"- runtime_bias_scope: `{lifecycle_matrix.get('runtime_bias_scope')}`",
        f"- total/joined/floor: `{lifecycle_matrix.get('total_rows')}` / `{lifecycle_matrix.get('joined_rows')}` / `{lifecycle_matrix.get('sample_floor')}`",
        f"- policy_pass/promote_ready: `{lifecycle_matrix.get('policy_pass_count')}` / `{lifecycle_matrix.get('promote_ready_count')}`",
        f"- fixed_threshold_roles: `{lifecycle_matrix.get('fixed_threshold_roles') or {}}`",
        f"- ready_for_bounded_apply: `{lifecycle_matrix.get('ready_for_bounded_apply')}`",
        f"- warnings: `{lifecycle_matrix.get('warnings') or []}`",
        "",
        "## Lifecycle AI Context",
        f"- context_artifact: `{lifecycle_ai_context.get('artifact') or '-'}`",
        f"- context_version: `{lifecycle_ai_context.get('context_version') or '-'}`",
        f"- prompt_stage_count: `{lifecycle_ai_context.get('prompt_stage_count')}`",
        f"- attribution_artifact: `{lifecycle_ai_context_attribution.get('artifact') or '-'}`",
        f"- attribution eligible/applied/skipped: `{lifecycle_ai_context_attribution.get('context_eligible_count')}` / `{lifecycle_ai_context_attribution.get('context_applied_count')}` / `{lifecycle_ai_context_attribution.get('context_skipped_count')}`",
        f"- stage_attribution: `{lifecycle_ai_context_attribution.get('stage_attribution') or {}}`",
        "",
        "## Swing",
        *_render_rows(swing),
        "",
        "## Swing Strategy Discovery Sim",
        f"- artifact: `{swing_discovery.get('artifact') or '-'}`",
        f"- available: `{swing_discovery.get('available')}`",
        f"- candidate/arm/labeled: `{swing_discovery.get('candidate_count')}` / `{swing_discovery.get('arm_count')}` / `{swing_discovery.get('labeled_sample_count')}`",
        f"- pending_future_quote_count: `{swing_discovery.get('pending_future_quote_count')}`",
        f"- top_surviving_arm: `{swing_discovery.get('top_surviving_arm') or '-'}`",
        f"- avoid_bucket_count: `{swing_discovery.get('avoid_bucket_count')}`",
        f"- runtime_effect: `{swing_discovery.get('runtime_effect')}`",
        f"- interpretation: {swing_discovery.get('state_interpretation') or '-'}",
        f"- warnings: `{swing_discovery.get('warnings') or []}`",
        "",
        "## Panic",
        *_render_rows(panic),
        "",
        "## Pattern Lab Audits",
        f"- currentness: status=`{currentness.get('status')}` fail=`{currentness.get('fail_count')}` artifact=`{currentness.get('artifact') or '-'}`",
        f"- propagation: status=`{propagation.get('status')}` fail=`{propagation.get('fail_count')}` warnings=`{propagation.get('warning_count')}` artifact=`{propagation.get('artifact') or '-'}`",
    ]
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{warning}`" for warning in warnings)
    if source_load_diagnostics:
        lines.extend(["", "## Source Load Diagnostics"])
        for item in source_load_diagnostics:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{Path(str(item.get('path') or '')).name}`: `{item.get('status')}` "
                f"error=`{item.get('error') or item.get('type') or '-'}`"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build read-only runtime approval summary report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_runtime_approval_summary(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
