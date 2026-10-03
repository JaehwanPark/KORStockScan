# Main 기계·보조 정책 원천 결함 보완 및 격리 재생성 계획 (2026-10-03)

## 목적과 권한

기존 작업본은 24a4658d로 통합·배포하고 6d72c44d 문서 완료 commit에서 clean 기준선을 확인했다. 사용자 지시에 따라 기계·보조 정책 생성 결함을 보완하고 계산 결과·성능을 검증한다. 이번 신규 코드·정책 보완분 배포, 매매 재기동, provider/threshold/quantity/cap 변경과 주문은 별도 지시까지 대기한다.

대상 source date는 2026-10-02, 학습 source는 현행 forward 경계 9/29 이후, holdout은 10/2다. 과거 원천을 현재 정책값·가짜 ID·가짜 비용으로 채우지 않는다. 신규 코드 위치는 기존 scalping producer/validation 및 기존 tests 소유자로 한정한다.

## 원인과 작업 단위

| 작업 | 실제 원인 | 보완 | 완료 검증 |
|---|---|---|---|
| R1 기회 lineage | v7 2976행 중 2877행 scanner ID 결손 제외. accepted99에 fixed-watch 31행의 문자열 None placeholder가 포함됨 | producer/loader placeholder·비문자 identity 제거; fixed-watch는 native admission+generation+origin으로 독립 기회 식별. attempt ID를 기회 대용으로 사용하지 않음 | None/null/list/공백/누락 실패; 같은 admission의 반복 평가 한 기회; generation/venue 변경 분리; 실제 cache 재계산 counts |
| R2 완료 검색 재개 | cursor96 완료 checkpoint에서 iterator가 0개를 yield하면 search progress가 누락되어 미완료/재검색으로 돌아감 | 동일 input·선정 version·parent·scope·search domain의 progress와 train checkpoint를 보존; 결손/변경 상태는 fresh search | 완료 후 후보 없음 재개가 완료 유지; 변경 input 재검색; 중단/재개와 uninterrupted 결과 동일; holdout 선정 전 누설 없음 |
| R3 계산 설명 | winrate 후보8개 모두 학습 hurdle 실패. 실제 train109/89, hold19/14인데 빈 최종 후보가 홀드아웃 부족으로만 오인됨 | 후보별 원시/보정 승률·coverage·기존승자 보존·정확 실패 이유를 격리 계산 산출물로 발행. 기존 기준은 유지 | 기존 baseline 수치 및 8 thresholds 재현, 계산값과 사유 산식 대조 |
| R4 pre-AI probe 원천 | 15개 중12개가 observation_only의 probe reservation 금지에서 plan 미기록. 나머지 capacity2/guard1 | live reservation과 분리된 pure 관측 probe 계획의 허용 계약을 먼저 확인. 실제 consumer가 observation plan을 제출할 수 없게 하고 conditional residual·capacity/exit/cost 원천을 보존 | 예약/registry/stock/order 호출 없음; seed/plan hash 정확 join; 실제 제출 경로는 기존 reserved bundle 필요. 과거 없는 plan·stop·full cost는 gap 유지 |
| R5 경제성/stop 복구 | aux 59중17개 진단 적격이나 exact stop/full cost 없음, actual completed owner outcomes0 | 날짜별 retained source와 정확 native receipt 존재 여부 확인, lossless 연결만 복구. 동적 exit를 고정 stop으로 대체하지 않음 | source absent/unsupported를 명시, EV null 유지. 현재 코드로 과거 plan·비용을 backfill하지 않음 |

R1/R2는 코드 결함이다. R1의 compact projection native watch 세 필드 유실도 함께 수리하고 retained exact trace와의 lossless metadata 복구를 격리 출력에서 검증한다. R4의 관측 표현이 현행 owner replay에서 지원되지 않거나 R5의 과거 원천이 유실되었다면 해당 모수의 최종 상태는 source_gap/unsupported이며 다음 자연 source 수집 소유자로 인계한다. 결손을 해결했다는 허위 통과나 동일 무변경 재생성 반복은 하지 않는다.

## 실행 순서

1. 기존 원천/정책 JSON·cache의 SHA256과 10/2 보고서/9/29~10/2 모수 census를 동결한다. 출력은 `tmp/main-machine-auxiliary-source-remediation-20261003/` 및 독립 audit에만 저장한다. canonical report/policy pointer는 변경하지 않는다.
2. R1/R2 구현, R4 계약/권한 검토, R3/R5 계산·원천 진단. 자체 리뷰 → 수정 → 재리뷰 → 영향 pytest/compile/diff 검증을 통과시킨다.
3. 보존된 machine cache를 bounded gzip streaming으로 읽는다. 원래 제외된 4094행이 없는 filtered cache라는 한계를 receipt에 기록한다. 옛 kernel cache를 새 원천 봉인으로 재라벨링하지 않고 비교 실험 입력으로 명시한다.
4. 동일 동결 입력으로 기존/수정 lineage 및 검색을 비교한다. baseline/후보/배제수·source hash와 CPU/wall/RSS를 기록한다. candidate가 없거나 경제 source가 없으면 기존 정책 승계를 정상적으로 유지한다.
5. compact aux는 retained 정확 source·diagnostic stage와 full economic gate를 분리한다. provider 호출 없이 보존된 exact prompt/response와 가격·비용 원천만 재검증한다. actual EV/변경 정책이 없으면 null/carry를 보고한다.
6. 격리 결과와 변경사항을 audit 및 당일 checklist에 기록한다. 기존 10/6 PREOPEN/natural owner는 유지한다. 신규 보완분 배포는 대기한다.

## 판정 경계

코드/검증 완료, 원천 복구, 새 정책 선정, 배포, PID 소비, 자연 체결과 비용 후 성능을 각각 보고한다. 정책 변경 가능성은 유효 candidate/독립 holdout/owner·full-cost 완료로 결정한다. 원천 행 증가·CF 승률 개선·테스트 PASS만으로 실매매 개선을 주장하지 않는다.

실행 결과: [보완·격리 계산 리뷰](../audits/main-machine-auxiliary-source-remediation-review-2026-10-03.md). 코드/계산 수리는 완료, Main 후보0/보조 carry 유지, 신규 보완분 배포 대기이며 stop/full cost/조건부 replay의 자연 원천 결손은 인계한다.
