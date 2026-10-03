# 삼성전자 전용 연구·보조 원천 소비자 실행 리뷰 — 2026-10-03

## 1. 결정

[실행 계획](../proposals/main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)의 삼성전자 S0~S5와 공통 보조 원천/삼성전자 제외 소비자 A0~A5를 구현·리뷰·보완·격리 검증했다. live 삼성전자 정책은 선정하지 않았다. 배포·재기동·provider/브로커 호출·새 원천 수집·정책 활성화·커밋은 실행하지 않았다.

| 대상 | 실행 결과 | 남은 판단 |
|---|---|---|
| 삼성전자 기계 | fixed-watch 31시도/2기회, 30조합 비교, 날짜별1시도 회수 | 정식 gate 미통과. [전용 구현계획](../proposals/samsung-fixed-watch-machine-auxiliary-implementation-plan-2026-10-03.md) 확정, live schema/selector 등록 대기 |
| 삼성전자 보조 | 기존 PASS9와 별도 CAUTION1 확인, fixed-watch PASS2·CAUTION1 | 새 기계 ENTER2건의 exact AI 응답0. 결합 성과 null, 공통 parent 상속 |
| 그 외 기계 | 기존64시도/63기회 및 204후보 회수0 근거 유지 | 새로운 규칙·임계값 변경계획 보류 |
| 그 외 보조 | operating source42, 유효 응답34, pre-AI 연결12, 독립 stage15기회 | count/materiality12조합의 행동 변화0. 원천 코드 수리 완료와 정책 개선 미입증을 구분 |

## 2. 삼성전자 연구 결과

원천은 기존99개 native snapshot, 기존 parent/분할 증빙, 날짜별 v9 보조 projection, 작은 pre-AI observation projection, 정확한 trace metadata 및 날짜별 검증된 비용 자료다. 큰 machine raw payload를 다시 스캔하지 않았다.

- 대상: `005930 + MAIN_FIXED_WATCH + KRX|KRX_REGULAR`.
- 학습9/30: 12시도/1기회. 후단10/2: 19시도/1기회. 삼성전자9/29 다른 origin 4시도는 분리했다.
- 후보: 학습 phase의 공통/continuation/distribution/range_or_no_setup/rebound_attempt × 시간대 전체/10시 전/10시 이후 × 연속 확인1/2 =30개. 연속2회는 같은 admission·phase에서60초 이내이며 다른 admission·오래된 확인을 재사용하지 않는다.
- 선택: `a93cb33ba2a71581`, `DEPTH_SUPPORTED + family_setup_confirmation`, 추가 phase/시간대 제한 없음. 학습 동률에서는 불필요한 제한이 적은 쪽을 선택했다.
- 회수:9/30 trace `1f41811269a7da7b93345bc9d00ea09d3bac3d55a1ff562b709cfba8b5269826`,10/2 trace `47bc3705a4b1113ed4f2b58630bfc836588d5fe22e9b1971967589a4d983c60f`. 각1기회, 비용 결합 목표-first, 경로 순수익률 +0.1%다. 목표 label의 경로 평가이며 실제 주문/수익이 아니다.
- 시간대 전체와10시 전의 행동이 같았다. phase를 제한하면 `range_or_no_setup`은 학습만 회수하고 `distribution`은 후단만 회수했다. 후단을 보고 phase를 다시 선정하지 않았다. 연속2회와10시 이후 조건은 양쪽 회수0이다.
- 사전 관측 action/reason/phase 전이27구간을 기록했지만 독립 종료/재시작 episode 계약은 미입증이다. 승격 분모는 native2기회를 유지했다.
- 정식 gate 실패4개: `train_machine_support_insufficient`, `holdout_machine_support_insufficient`, `holdout_machine_recovery_support_insufficient`, `mechanistic_entry_threshold_policy_fields_invalid`. 희소성을 해결하려고 기준이나 schema를 완화하지 않았다.
-10/2는 이전 연구에 반복 사용한 후단이다. 독립 검증 성능이나 향후 수익률을 주장하지 않는다.

## 3. 보조 응답 분모와 CAUTION

| 분모 | 삼성전자 | 그 외 |
|---|---:|---:|
| 기존 v9 운영 원천 | 17 | 42 |
| 기존 KRX PASS 연구 집합 | 9 | 34 |
| 이번 원응답 계약 검사: KRX PASS+CAUTION | 10 | 34 |
| exact pre-AI 연결 | 2 | 12 |
| fixed-watch로 확인된 KRX 응답 | PASS2·CAUTION1 | 대상 외 |
| native 중복 제거 후 KRX stage 기회 | 4 (모든 Samsung origin) | 15 |
| 전용 fixed-watch stage 기회 | 2 | 대상 외 |

추가1개는 새 수집 결과가 아니라 기존 PASS 집합 밖에 있던 `2026-10-02T11:34:59.088877+09:00` CAUTION이다. 같은 native watch의13:04 후속 응답은 `entry_risk_pass_residual_risk_not_considered`로 의미 검증에 실패했다. CAUTION 해소·실제 재진입·terminal 성공으로 계산하지 않았다. 그 외 종목의 유효 CAUTION은0이다.

고정 감시3응답은 연구 기계 후보가 새로 ENTER로 바꾼2시도와 정확히 연결되지 않는다. 같은 날짜/종목의 PASS를 빌려 결합 성과를 채우지 않았다. 응답 없는 새 prompt 성능은 `not_evaluated_new_prompt_response_absent`다.

trace metadata는9/30 1행,10/2 5행을 exact 복원했다.9/29 1행은 저장 형태/세대 signature가 달라 복원하지 않았다. 일치하지 않는 archive에서 가까운 시각으로 추정하지 않았다.

## 4. 확인한 결함과 수정

| 경계 | 발견/수정 | 검증 |
|---|---|---|
| 기계 관측→경제 관측→AI trace | plan 실패와 무관하게 native ID/기계 관측·정책 hash/clock을 nullable capsule에 보존. append receipt를 capsule hash와 결합. 기존 capacity 영수증도 guard/plan 실패 전에 보존 | 원 stock 불변, 기존 source-only 용량 호출 횟수 동일, 실패한 plan의 입력 보존 |
| 요청/응답→projection | envelope/payload/attempt 충돌을 격리하고 capsule·conditional probe·guard/capacity 영수증을 전달. 실제 trace의 존재와 append 전 선언을 구분 | partial JSONL/gzip를 빈 원천으로 발표하지 않음, 잘못된 hash/시점/scope/receipt 제외 |
| 단계별 ledger | 기계 미호출, 실제 provider 시도, timeout, semantic 실패, stage 적격성과 operating 결손 분리 | 주사유 합=record 분모, 보조사유 중복 가산 금지, 없는 historical machine census=null |
| 독립 stage | operating unsupported가 유효 stage 결과를 숨기지 않도록 주사유 우선순위 수정. 경제 pipeline append 실패만으로 다른 exact AI 입력을 삭제하지 않음 | source 실패와 plan/stop 실패의 독립성 회귀 |
| **비용 연결** | trace의 `krx_regular`과 비용 validator의 `KRX_REGULAR` 차이로 실제 비용 자료가 모두 탈락. 등록된 scope의 대소문자만 비용 계약에서 정규화 | native identity 원문 유지, 비용 +0.23%p 결합, suffix/UNKNOWN/다른 날짜는 거부 |
| 위험 근거/후속 경로 | 원응답·수선 응답 SHA, 중복 인용·validation/materiality, predecision phase/flow/liquidity 셀, 동일 기회의 CAUTION 후속 응답을 기록 | 알려지지 않은 유형은 UNKNOWN, 비용 결손은 null, 무기록 terminal 복원 없음 |
| cache/발행 | source/code/cost/parent/partition 결속, 미완성 checkpoint·변경된 generation 재사용 차단. 연구 분리 결과를 selection freeze와 publisher 양쪽에서 차단 | 전체/삼성전자/그 외 결과 교차 발행 불가; cold/warm 내용 hash 동일 |

변경 소유자는 `src/engine/scalping/auxiliary_source_contract.py`, `samsung_auxiliary_scope_research.py`, 기존 `ai_decision_trace.py`, `compact_auxiliary_paired_replay.py`, `mechanistic_entry_runtime_policy.py`, `src/engine/sniper_state_handlers.py`다. 새 Python은 scalping 역할 패키지에 두었다. Kiwoom 요청/응답 protocol이나 주문 규칙을 수정하지 않았다.

## 5. 결함 수정 후 정책 재계산

비용 표기 결함 수정 전, 이번 독립 stage의 KRX 비용 적격은 삼성전자0·그 외0이었다. 수정 후 삼성전자4·그 외15가 같은 날짜의 수수료/세금/기록된 friction에 연결됐다. scope가 다른 aftermarket1행은 비용 미지원으로 남았다.

- 그 외: native15기회=학습7·후단8. count/materiality12조합 모두 실제 행동 변화0, 성공 제외0, paired delta0이다. 선정 결과는 `incumbent_carry`, 비교 상태는 `valid_no_change`다.
- 그 외 parent의10분 고정 경로 CF 평균은 비용 결합 전 약−0.1613%, 결합 후 약−0.3913%다. 학습 긍정0·부정7, 후단 긍정1·부정7이다. 운영 실현 손실 통계가 아니며 모델 개선 이익을 뜻하지 않는다.
- 삼성전자 KRX 모든 origin:4기회,6조합 모두 행동 변화0. 전용 fixed-watch에서는3응답 중 같은 admission 반복을 제거해2기회만 평가한다.
- 타입 셀의 그 외15기회 중 비용 후 음의 PASS 경로는14개다. 셀당1~4기회라 세분화 자체가 충분한 학습 지원수를 제공하지 않는다. 이는 이미 결정 시점에 알 수 있던 유형 안의 CF 진단이며 새 매매 규칙으로 선정하지 않았다.
- 과거 stop/fill/capacity 계약을 새로 만들어 운영 replay를 완성하지 않았다. independent operating 비교와 실제 `COMPLETED + valid profit_rate` 실현 결과는 여전히 별도 원천을 요구한다.

## 6. 검증·성능·불변성

실행 근거 디렉터리: `tmp/samsung-auxiliary-plan-execution-20261003/`. 최종 원천 manifest·후보 정의·학습 동결·변경 시도·분모·원응답 진단·stage 재생 결과와 cold/warm 측정 receipt를 보존한다.

최종 artifact는 `reviewed-final/`의 `frozen-candidates.json`, `frozen-selection.json`, `result.json`, `auxiliary-population.json`, `auxiliary-stage-results.json`이다. 결과 hash는 cold/warm 모두 `d075d2d3d309eb2f1bb8aa8be8570bc8cef59fc931c9f1290f4e4e477b1e22c0`이다. 측정 wall/CPU는 모듈 import 이후 연구 함수 구간이며 peak RSS는 해당 프로세스 전체다. cold는 exact trace metadata 복원을 포함하므로 그 작업이 없던 최초 진단2.616초와 동일 작업량 성능 비교로 해석하지 않는다.

| 실제 측정 | cold | warm |
|---|---:|---:|
| wall | 5.276초 | 0.179초 |
| CPU | 5.353초 | 0.289초 |
| peak RSS | 233,576 KiB | 73,372 KiB |
| 원천 파일 byte hash 검증 | 44회(전후22개) | 22회 |
| retained projection JSON decode | 7 | 0 |
| 작은 비용 dependency manifest 읽기 | 3 | 3 |
| 비용 profile load | 5 | 0 |
| bounded trace metadata 보완 시도 | 3 | 0 |
| 큰 raw payload scan | 0 | 0 |

`cold-reviewed-final.log`/`warm-reviewed-final.log`가 측정 영수증이다. warm도 원천 byte hash와 비용 backing-file binding을 검증하며, 큰 projection의 JSON 재분석과 trace 재스캔을 생략한다.

검증은 통합319 tests PASS(`closed-regression.log`, 경고1), 후속 scope/timeout 분리 보완258 tests PASS(`final-source-scope-regression.log`), 마지막 diagnostic authority/cache 보완145 tests PASS(`metadata-closure-regression.log`)다. 이들은 중복되는 표적 회귀 실행이며 합산한 고유 테스트 수가 아니다. compile·`git diff --check`·문서 링크·stable owner 검사·print-only backlog parser도 통과했다.

그 외 응답42행의 최종 배타적 주사유는 stage comparable15, source gap10, operating unsupported9, transport invalid6, semantic invalid2로 합42다. 별도 전이 집계는 provider attempted42→response received36→semantic valid34→stage eligible15다. 오래된 v9에 없는 전체 machine census는0으로 채우지 않고 null로 남겼다.

운영 정책541개 hash는 시작 전과 동일하다. 기존 작업본은 별도로 보존했고 이 작업의 승인 범위에 해당하는 파일만 덧붙여 수정했다. 코드 검사·격리 재생성 완료는 배포·PREOPEN·PID 소비·자연 원천 수용·실현 성능 증거가 아니다.

## 7. 종료와 남은 결손의 소유자

- `SamsungDedicatedMachineAuxiliaryResearch1003`: 연구/설계 범위 종료. live child 구현은 현재 정식 지원수·schema·결합응답 근거 미충족으로 보류한다.
- `NonSamsungAuxiliarySourceConsumerImplementation1003`: 코드·분모·원천 연결·격리 검증 범위 종료. 과거 미기록 원천은 `historical_source_gap`으로 명시한다.
- 자연 source 수용은10/6 `DirectFamilySourceRepairCompactAuxiliary`, 기계 관련 수용은 `DirectFamilySourceRepairMainMechanisticEntry`, PREOPEN/PID는 `DirectFamilyPreopenPolicyHandoff`가 계속 소유한다. 이 세 항목을 완료 처리하지 않았다.
- canonical 장후 재생성·summary/strict/controller·운영 배포·재기동·전체 매매 suite·새 prompt 실험·외부 동기화는 실행하지 않았다. 이번 실행 범위와 이후 실제 운영 수용을 구분한다.
