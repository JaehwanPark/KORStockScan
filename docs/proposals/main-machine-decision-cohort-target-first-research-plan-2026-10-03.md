# 기계판정 집단별 목표-first 재검증 계획

## 범위

사용자가 승인한 후속1·2·3번을 수행한다. [이전 분리 연구](../audits/partitioned-continuous-pattern-research-review-2026-10-03.md)의 원천과 동일 parent를 사용한다. 삼성전자/그 외를 조건 생성 전에 분리한다. 이후 사용자가 기계·보조 모두 **기존 정책보다 높은 승률 우선, 기존 성공100% 보존을 후보 탈락 조건으로 사용 금지**를 명시했다. 보조 연구 selector와 개선계획을 이 목적에 맞추고 보유 응답을 재계산한다. 보조 production 통합·배포 대기는 유지한다.

### 최종 선정 목적

- 같은 비교 분모에서 기존보다 높은 비용 결합 승률을 연구 적격 조건으로 삼고, 기존 owner의 표본 수 보정 승률로 순위를 정한다. 후단 자료로 재선정하지 않는다.
- 기존 성공 제외 수·실패 회피 수·보존율·paired EV·절대 순수익은 진단이다. 성공100%·80% 보존이나 양의 EV를 연구 후보의 숨은 탈락 조건으로 사용하지 않는다. 비용 결손은0수익으로 만들지 않는다.
- 기존 절반 이상 선택 기회/PASS를 남기는 탐색 coverage 조건과 표본 수를 공개한다. 이는 정식 지원수 충족을 뜻하지 않는다. 적격 결과가 없는 후단은 승률0이 아니라 `not_evaluable`이다.
- 기계는 비용 결합 target-first, 보조는 기존 비용 결합10분 PASS CF 승률이다. 서로 다른 성공 정의를 합산하지 않는다. 보조1/3/5분은 사전에 고정한 민감도다.
- 운영 publisher의 기존 성공 보존/EV 조건은 이번 연구 selector 변경과 구분한다. 변경 대상과 evidence schema/cache 이행은 [보조 개선계획 A6](auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md#a6-승률-우선-정책-선정-계약-이행--사용자-후속-기준)과 실행 리뷰에 명시한다.

## 1. 전체 판정·평가 분모 재구성

- 보유7,069행 원본을 날짜별1회 순차 읽어 동일 parent kernel로 재생한다. 기록된 행동과 재생 행동·남은 risk·source/liquidity/local-breakout·micro 확인 상태를 함께 보존한다.
- 집단: `parent_enter`, `soft_confirmation_only`, `other_guard_or_wait`, `source_invalid`. 확인 대기는 명시적 soft fact만 남고 기존 source/liquidity/local/parent guard를 통과한 경우다. 요약 reason만으로 판단하지 않는다.
- 비용 결손, scope/cost 불일치, 경로 결손, 같은 봉 모호성, 미도달, 늦은 손절, 유효 target/stop을 별도 진단한다. 정식 `_machine_path_value` 결과와 제외 여부를 그대로 보존한다. 결손·검열을0수익/실패로 만들지 않는다.
- native 신원·평가 가능 경로·관측 시도는 별도 분모다. 새 native ID를 생성하지 않는다.

## 2. 삼성전자 후보 검증

- 기존 `DEPTH_SUPPORTED + family_setup_confirmation`을 먼저 고정해519관측 및 fixed-watch206관측 전부에 재생한다. 두 성공 사례만 선택하지 않는다.
- parent ENTER와 다른 guard를 보존한다. 후보가 바꾸는 모든 시도에 target-first·실패·미도달·결손을 붙인다. native당 선행/후행 parent ENTER와 시각 차이를 기록한다. 관측 순서를 실제 주문·보유 상태로 해석하지 않는다.
- 60/120/180/300초 안의 같은 native·phase 연속2회 조건을 고정 민감도로 비교한다. 대상 관측 전체에서 상태를 갱신하고 현재 guard 통과를 다시 요구한다.
- 선택 기준은 기존 대비 비용 결합 목표-first 승률이다. 기존 성공 보존은 부작용 지표다.3/5/10분 종가 CF는 보조 지표이며 선정 기준에 넣지 않는다.

## 3. 삼성전자 제외 집단 내부 연구

- 실제 재생 parent ENTER 내부에서 실패를 줄이는 veto 가설과 `soft_confirmation_only` 내부에서 진입을 회수하는 가설을 따로 학습한다.
- 학습에 있는 family/phase/liquidity/volatility 및 현재 수치의 분위수로 작은 단일·유형+수치 조건을 생성한다. 안전/원천/local/liquidity guard의 임계값·fact는 바꾸지 않는다.
- 9/29→9/30,9/29~30→10/2에서 학습 선택을 먼저 동결한다. 이미 사용한 날짜이므로 탐색 검증이다. 표본이 없으면 `not_evaluable`로 남긴다.
- native 기회 단위 정식 kernel 지표와 관측 집단 지표를 병기한다. 승률 개선·성공/실패 제외·선택 coverage·비용 경로·미평가 행동 변경·종목 집중도·후단 노출을 검증한다. 형식 등록이나 지원수 기준을 낮춰 통과시키지 않는다.

## 지표·권한·완료

`metric_role=offline_cost_bound_machine_path`, `decision_authority=offline_only`, `window_policy=frozen_20260929_20261002`, `sample_floor=연구 지원수 명시 및 정식 owner gate 별도`, `primary_decision_metric=cost_bound_target_first_native_opportunity`, `source_quality_gate=exact parent/source/cost/identity 및 검열 분리`, `forbidden_uses=live 승격·실현수익·synthetic native·안전완화·provider/주문`.

새 연구 producer는 `src/engine/scalping`, 테스트는 `src/tests`가 소유한다. 기존 매매/보조 producer 작업본을 보존한다. 구현→리뷰→수정→재리뷰→표적회귀/compile/diff→격리 계산→문서 링크/owner/print-only parser로 닫는다. 기존10/6 자연 수용 owner를 닫지 않는다.

실행 owner: 오늘 checklist `MachineDecisionCohortTargetFirstResearch1003`.

실행 결과: [전체 판정·승률 우선 재검증 리뷰](../audits/main-machine-decision-cohort-target-first-research-review-2026-10-03.md). 최종 기계 선정은 `run-04`, 보조는 `auxiliary-winrate-02`다. 이전100% 보존 실험은 최종 기준이 아니다.
