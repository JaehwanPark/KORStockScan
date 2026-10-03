# Main BLOCK 상승 경로와 정책 탐색 범위 점검 (2026-10-03)

## 판정

**후보 0은 상승 패턴 0의 증거가 아니다.** 9/29 이후 보존 KRX 자료에는 BLOCK 뒤 목표에 먼저 도달한 관측이 있다. 정책 학습의 큰 원천 제외, `NO_VALID_SETUP`으로 압축되는 유형, 제한된 조합 탐색을 함께 점검해야 한다. 유형별 연구를 진행할 근거는 확인했으나 새 정책의 독립 검증이나 실매매 성능 개선은 입증하지 않았다.

근거는 `tmp/main-machine-auxiliary-source-remediation-20261003/block-pattern-census.json`과 `after-machine.json`이다. 앞선 [격리 재계산 리뷰](main-machine-auxiliary-source-remediation-review-2026-10-03.md)의 후보0 설명을 보완한다. cache SHA 3개를 기존 격리 입력과 대조했다. stream 1회와 incumbent 재판정으로 5.17초에 집계했다. canonical report/policy 변경, provider/broker 호출, 배포/재기동은 없다.

## 1. 실제 상승 관측

9/29·9/30·10/2 보존 cache의 KRX/REGULAR 2976행을 조사했다. 다른 venue/session은 제외했다. 이는 가격 경로가 있는 filtered cache이며 원 보고서 전체7069 입력이나 시장 전체 BLOCK의 전수 분모가 아니다.

아래 “목표 먼저”는 기존 round-trip cost를 반영한 `net_target_first` CF bar 경로다. 실제 체결·실현 수익·지연 후 회수·지속 상승을 뜻하지 않는다. 행은 반복 시도를 포함하며 독립 기회 수나 승률로 해석하지 않는다. lineage 적격99행은 같은 incumbent으로 재판정했고 나머지는 당시 캡처 판정이다.

| 날짜 | BLOCK 시도 | 목표 먼저 | stop 먼저 |
|---|---:|---:|---:|
| 9/29 | 540 | 352 | 188 |
| 9/30 | 145 | 99 | 46 |
| 10/2 | 164 | 113 | 51 |
| 합계 | 849 | 564 | 285 |

BLOCK849 중 lineage 제외834(목표555/stop279), 적격15(학습8/검증7)다. 학습 BLOCK8 중 목표5이며 **2개 독립 기회**에 속한다. 삼성전자 같은 fixed-watch admission의 4회 목표 도달을 독립 성공4개로 세지 않는다. 학습 RECHECK46 중 목표33, 목표 관측이 있는 기회28이다. BLOCK/RECHECK 합쳐 목표38시도/29기회다. 판정별 기회 집합은 재평가에서 겹칠 수 있으므로 합산하지 않는다.

전체2976 중 v7 적격99(3.33%), lineage 제외2877(96.67%)다. 따라서 현재59학습/10검증 기회로 시장에서 관측한 대량 BLOCK을 대표한다고 볼 수 없다. 제외행은 연구 관측으로 보존할 수 있지만 native opportunity가 없는 행을 stock/date/attempt로 가짜 독립 기회에 편입할 수 없다.

## 2. 유형별 차이와 현재 분류의 압축

BLOCK849 중 `NO_VALID_SETUP`820, CLEAN_CONTINUATION18, RECOVERY_CONFIRMATION11이다. `NO_VALID_SETUP` 하나만으로 묶으면 내부의 continuation/pullback/distribution/rebound 차이를 보지 못한다.

| 판정 당시 structure phase | BLOCK 시도 | 목표 먼저 |
|---|---:|---:|
| pullback | 120 | 97 |
| continuation | 215 | 153 |
| distribution | 197 | 133 |
| recovery_continuation | 117 | 58 |
| rebound_attempt | 59 | 33 |

이 표는 유형별 차이를 찾는 출발점이다. 반복 관측, 종목·시간 편중, 이미 가격 경로가 있는 행만 남은 선택 편향이 있어 수치만으로 우수 유형을 선정하지 않는다.

학습 적격 RECHECK에서도 RECOVERY_CONFIRMATION은 11시도 중 목표10(10기회 중 목표 관측9), CLEAN_CONTINUATION은 28시도 중 목표18(27기회 중 목표 관측17)로 다르다. 다만 표본이 작고 중복 결과·복합 차단이 있어 확정 패턴이 아니다. 유형별로 source usability, phase, liquidity, 현재 차단 사실을 함께 봐야 한다.

## 3. 89개 후보가 회수하지 못한 이유

`entry_strategy_policy._balanced_candidates`와 `ai_action_outcome_calibration.build_main_strategy_refinement`의 실제 v7 경로를 확인했다.

- 할당은 control4 + 단일 좌표82 + recovery neighborhood6 + independent joint4 =96이다. invalid6/dedup1 뒤 평가89이며 모든 후보의 회수 기회는0이다. 11개 후보는 기존 진입을 줄이는 변경만 만들었다.
- 28개 숫자 selector 후보를 계산했지만 **이번 recovery budget에는 selector_leaf 할당이 없다**. 기존10-node tree를 계승해 profile를 변경하며 새 유형별 분기 후보를 생성하지 않았다. 기존 계층 분류까지 없다는 뜻은 아니다.
- phase/family/차단 사실의 범주별 새 분기를 이 탐색에서 학습하지 않았다. 조합은 소수의 2~3좌표 template 중심이며 `cartesian_exhausted=false`다. “검색 완료”는96할당 완료이고 전체 패턴 공간 탐색 완료가 아니다.
- 학습 BLOCK 목표5시도 모두 `large_sell_print_present`의 STRUCTURE_INVALIDATED/BLOCKING 사실과 micro `source_usable=false`를 갖는다. 사후 상승만으로 당시 veto/source를 풀 수 없다. 대량 매도 이후 신선한 회복 snapshot이 있었는지 순서 재생해야 한다.
- 학습 RECHECK 목표33 중 MICRO_PRICE_RESPONSE25, local_breakout confirmation5, trigger confirmation3이다. 먼저 유형·복합 blocker별로 어떤 원천/조건이 끝까지 남는지 확인해야 한다. 단일 threshold 변경이 다른 차단도 해소한다는 가정은 성립하지 않는다.

따라서 현재 결과는 “이 원천과 좁은 변경 집합에서 회수 가능한 후보를 선정하지 못했다”로 읽어야 한다. 유형별 탐색을 추가하면 개선될 **가능성**이 있지만 이번 집계만으로 원인이나 개선 크기를 확정할 수 없다.

## 4. 다음 연구 설계

1. **모수와 linkage:** 전 BLOCK/RECHECK raw→가격/비용/stop 경로→native admission→학습 편입까지 날짜·유형별 누락률을 만든다. 제외2877행은 비승격 연구 관측으로 유지하고 exact native receipt가 있는 행만 적격에 복구한다. 재시도·시간 중첩·같은 watch generation은 분리해서 집계한다.
2. **사전 유형:** 판정 전 phase(추세 지속/눌림/회복/돌파 실패 등)를 먼저 나누고 liquidity·변동성·시간대·차단 사실을 보조 축으로 쓴다. `NO_VALID_SETUP` 내부 source-invalid/구조 veto/확인 대기를 구분한다. 결과가 오른 뒤 유형을 붙이지 않는다. 적은 셀은 상위 그룹에 묶어 부분 pooling한다.
3. **변경 가능성 재생:** hard/source blocker와 튜닝 가능한 조건을 분리한다. 회복 후 새 snapshot을 기준으로 BLOCK→RECHECK→ENTER 경로를 재생한다. 하드 안전 조건이 유지된 상태에서 유형별 복합 soft 조건 후보와 전역 후보를 같은 모수로 비교한다. 이 단계는 기존 budget을 그대로 재실행하는 것과 다르다.
4. **독립 평가:** 먼저 label을 가리고 유형·후보·budget을 동결한다. 날짜·종목·중복 기회를 분리하고 전체 유형 탐색 수를 기록해 다중 탐색 선택 편향을 검증한다. 10/2는 이번 진단에 이미 열람했으므로 새 연구의 미사용 최종 holdout으로 주장하지 않는다. 다음 독립 forward 자료로 확인한다.
5. **성능 검사:** 목표-first뿐 아니라 stop-first/미도달/censoring, 회수율과 실패 회수, 기존 성공 보존, 예상 기회 빈도, 체결·지연·원금/점유·동일 owner/전 비용을 함께 비교한다. actual COMPLETED 비용 후 수익은 별도 분모다. 모수/경제성 결손은0 EV로 메우지 않는다.

현재 작업은 연구 필요성과 탐색 한계 진단이다. 유형별 정책 생성 로직 변경·새 정책 선정·배포는 수행하지 않았다. 기존 원천 보완의 자연 수용 소유자는 [10/6 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)에 남는다.
