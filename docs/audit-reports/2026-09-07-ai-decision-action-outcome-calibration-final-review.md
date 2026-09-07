# #76 AI decision-quality → #82 action-outcome calibration 최종 보완 리뷰

- 최종 검토 시각: 2026-09-07 15:26 KST (최초 검사 14:18 KST)
- 범위: #76 detailed paired replay, #82 cumulative calibration, Main AI prompt optimizer offline selection, late batch/consumer wrapper, central verifier
- 구현 owner: `AIDecisionActionOutcomeFinalGateRepair0907` (최초 검사 기록: `AIDecisionActionOutcomeCalibrationRepair0907`)
- 자연 증거 owner: `AIDecisionActionOutcomeNaturalEvidence0908`

## 판정

현행 구현 owner는 `AIDecisionActionOutcomeFinalGateRepair0907`이며 아래 **최종 재점검 후 v5 보완**이 현재 판정을 소유한다. 최초 검사에서의 “결함 0건·연결 완료”는 후속 재현으로 철회했다. #82는 runtime/order/provider 권한이 없는 source-only calibration이며, 보고서 생성 성공은 실적용·실수익 성공이 아니다.

기대효과가 실제 수익으로 확인되었다고 판정하지는 않는다. 2026-09-04 기존 자료를 write 없이 재평가한 결과 hash-valid 후보는 0개, selected 후보도 0개였다. 이는 자동화 실패가 아니라 기존 detailed 자료의 자기해시 부재와 provider replay/lifecycle 근거 부족을 실적용 근거에서 제외한 결과다. 과거 hashless 행은 진단 수로만 남아 신규 hash-valid 누적을 영구 차단하지 않는다. 다음 자연 postclose에서 새 자기해시 자료가 생성되고, 기존 `MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0907`의 lifecycle custody 결손이 닫혀야 경제성 판단이 전진한다.

## 보완한 결함

1. 후보 버전만으로 KRX/NXT·세션·stage를 합산하던 누적 키를 prompt SHA, contract SHA, stage, venue, session까지 확장했다.
2. detailed source의 파일명/날짜, clean baseline, offline authority, isolated cohort/filter, prompt/contract binding, native integer counters, mature exact row를 검증한다. 잘못된 행과 충돌 duplicate는 합성하지 않고 제외 사유와 당일 상태에 남긴다.
3. #76 신규 detailed 및 reattribution 산출물에 canonical `artifact_content_sha256`를 발행한다. 2026-09-07 이후 hashless/변조 source는 #82 입력에서 거부하고, 이전 hashless source는 진단만 허용한다.
4. 기존의 “모든 exposure가 -2% 이내” 절대 veto를 `-2% 초과 최대 20%`, severe tail 최대 20%, `-5% 미만 0건`의 bounded risk budget으로 맞췄다. exposure rate 2%, tail/recovery 비교는 진단으로 내리고 EV 양수의 얇은 후보는 `thin_positive_review`로 보존한다.
5. 같은 날짜 신규 retained row가 없을 때 `updated`로 표시하지 않는다. source/report/row가 제외된 날과 단순 누적 무변경을 구분한다.
6. #82 보고서와 optimizer handoff를 각각 자기해시하고, central verifier가 schema/policy/authority/candidate identity/count/handoff hash와 semantic reference를 확인하도록 강화했다.
7. postclose 실행 순서를 `#76 → Main AI R0-R3 → #82 → prompt optimizer → consumer/runtime family`로 수정했다. Optimizer는 같은 target-date의 무결성·권한·후보 계약을 통과한 #82만 advisory로 읽으며 stale fallback과 같은 버전의 모호한 복수 identity를 거부한다.
8. 서로 다른 stage/venue/session의 review-ready 후보를 EV로 전역 순위화하지 않는다. 복수 후보는 격리 목록으로만 전달하고, 단일 후보일 때만 호환 selected 필드를 채운다.
9. pre-cutover hashless 행은 source metadata의 diagnostic count로만 보존한다. 새 hash-valid 행과 같은 prompt identity여도 EV·후보·OFI outcome 입력에 섞지 않아 과거 자료가 신규 후보를 영구 차단하지 않게 했다.

## 조건 달성 가능성

- Full review gate: 현 코드의 exact trace는 30이며 이전 문서의 40은 잘못된 설명이었다. unique symbol 10, source date 2, exposure 5와 양의 candidate/exposure/cost-adjusted EV 및 EV delta가 필요하다. 전체 모수만으로 달성 가능성을 단정하지 않으며 격리 cohort의 실제 노출 형성을 확인한다.
- Thin-positive lane: 전체 floor 전에도 양의 비용 차감 EV·EV delta와 bounded risk가 확인되면 버리지 않고 offline review에 남는다.
- R3 evidence handoff: review-ready에 더해 exposure 10, symbol 3을 요구한다. 이는 #82가 직접 runtime에 반영되는 조건이 아니라 독립 R3 후보가 검토할 수 있는 최소 근거다.
- Runtime apply: #82 단독으로 불가능하다. #81 legacy family는 `LEGACY_RUNTIME_AUTHORITY_ENABLED=False`이므로 R3 표본이 늘어도 활성화되지 않는다. V2.14/V2.15 KRX는 별도 `entry_setup_live_policy` owner의 기존 승격·PREOPEN·receipt 조건을 따라야 하며 이 작업은 그 조건을 변경하지 않는다. NXT/holding/미등록 prompt는 source-only이며, 표본 확보를 위한 실주문·threshold·수량·provider·broker/hard-safety 완화는 금지한다.

## 최초 검사 기록 (최종 검증은 아래 v5 보완 참조)

- `test_ai_action_outcome_calibration.py`: 23 PASS
- `test_ai_decision_quality.py`: 207 PASS
- `test_main_ai_prompt_optimizer.py`: 11 PASS
- `test_verify_threshold_cycle_postclose_chain.py`: 196 PASS
- threshold-cycle wrapper 전체: 112 PASS
- 변경 Python Ruff: PASS
- Python compile 및 postclose wrapper `bash -n`: PASS
- `git diff --check`: PASS
- 2026-09-04 read-only dry run: hash-valid candidate 0, selected 0, `sample_floor_keep_collecting`, 운영 artifact write 없음

## 남은 자연 증거

자연 확인은 `AIDecisionActionOutcomeNaturalEvidence0908`이 소유한다. 21:05 terminal detailed generation과 #82 재갱신, optimizer offline 선택/당일 freeze, provider0 batch binding refresh, consumer hash를 대사한다. 별도 활성 runtime owner의 실제 receipt 확인 전에는 “자동 적용 완료”나 “기대 수익 실현”으로 보고하지 않는다.

## 최종 재점검 후 v5 보완

### 구현과 재현

1. **불가능한 후속 경로 정정**: #81 legacy OFF를 명시하고 지원되는 KRX V2.14/V2.15만 별도 entry_setup_live_policy 검토 owner로 표시한다. `r3_handoff_evidence`는 호환 연구 floor이며 실적용 대기열/권한이 아니다.
2. **당일 결과 자동 재갱신**: late follower를 `terminal detailed -> #82 v5 -> optimizer (당일 선택 고정, #82 필수) -> batch metadata-only binding -> holding manifest -> consumer`로 연결한다. 재결속은 원본 detailed generation과 runtime owner의 batch evidence 불변을 검증하며 provider 재호출·live candidate 재발행이 없다.
3. **실제 offline 소비**: 같은 prompt/contract/stage/venue/session의 positive/thin 후보는 새 exact parent 검증을 유지하고, 충분한 표본에서 비양의 비용 EV·delta 또는 위험예산 실패가 확인되면 기존 registry의 다음 후보를 평가한다. 당일 실행 선택과 다음 세션 권고를 분리한다. 모든 등록 후보가 소진되면 기본 후보로 되돌아가 재호출하지 않고 source-only prompt-patch 필요 상태를 소비자까지 전달한다.
4. **부분 실패 국소화**: #76은 `ai_paired_calibration_source_v1`로 정상 paired rows hash, request/retained/excluded 보존식과 전역 무결성을 발행한다. 실패1/정상39는 정상행 학습을 허용하되 기존 full-report live promotion은 계속 실패다. 전역 contract/selection/provenance 결손은 전체 차단한다. 충돌 행을 제외한 정상40행은 충돌 이력 때문에 영구 차단하지 않는다. 누적 provider 오류 수는 진단으로 분리하며 schema 품질과 경제성·위험 gate는 유지한다.
5. **정렬/직렬화 계약**: 보고서와 handoff는 같은 identity 순서를 사용한다. #82/optimizer는 생산자의 ASCII canonical SHA를 공유하고 비ASCII 진단은 정상 처리하되 변조는 거부한다. optimizer는 현재 detailed source hash와 소비 report의 generation이 일치하는지도 확인한다.
6. **추가 자체리뷰 보완**: 부분 성공 계약의 hash를 최종 enrichment/재귀속 후 다시 결속하고, 빈 retained cohort는 integrity-pass로 표시하지 않는다. `thin_positive_review`는 sample floor만 부족할 때 사용하며 schema/risk/economic 실패를 숨기지 않는다. 누락·bool·NaN 경제성 필드는 충분한 평가 근거로 쓰지 않는다. 필수 #82 부재·오염은 late follower의 성공으로 종결하지 않는다. terminal provider 실패 배치도 #82 정상행 학습은 보존하되 원래 실패 exit를 유지한다. consumer가 optimizer에 결속된 #82 hash를 재검증해 후속 generation 교체를 탐지한다.
7. **경제성 결손의 오판 방지**: 비용 차감 primary 값 누락 시 gross 값으로 대체하지 않는다. exposure의 실제 비용 필드가 누락·bool·NaN·음수이면 cost contract 미완료로 판정한다. 위험 자료 부족만으로 위험예산 실패 후보를 탈락시키지 않는다. 부분 실패 producer의 실제 누적 metadata와 최종 detailed schema/hash가 #82 source contract를 통과하는 연결 테스트도 추가했다.

### 검증과 권한 경계

- 1차 확대 회귀: calibration/optimizer/batch/decision-quality/verifier/wrapper 569 PASS. 이후 보완분은 최종 재검증에 포함한다.
- 최종 통합 회귀: calibration/optimizer/batch/decision-quality/verifier/wrapper/consumer/entry_setup_live_policy/main_ai_quality_runtime_family **636 PASS** (23.51초).
- Python Ruff, compile, 두 postclose wrapper `bash -n`, `git diff --check`: PASS. 체크리스트 parser PASS (OPEN47건); 보완 구현 완료 항목은 제외되고 자연 증거 OPEN owner는 유지된다.
- 구현 → 자체리뷰 → 추가 결함 보완 → 재리뷰 → 최종 회귀 완료. 위 변경 및 직접 연결 계약 범위에서 미해결 finding **0건**이며 전체 저장소 무결함이나 실제 수익을 보장하는 판정은 아니다.
- 봇/PID/env, 실주문, quantity/provider/cap/broker/hard-safety 및 활성 PREOPEN 승격 조건은 변경하지 않는다. 기존 더티 작업과 live 생성 산출물은 보존한다.
- 이번 턴은 운영 report 재생성이나 실제 provider replay를 실행하지 않는다. 실제 기대 수익과 자연 자동화 성과는 OPEN 증거 항목으로 남긴다.
