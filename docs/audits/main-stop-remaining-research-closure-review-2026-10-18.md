# Main 손절 잔여 연구 종결 검토 — 2026-10-18

현재 상태: **현재 원천·등록 가설 범위의 연구와 생산소비 보완 종결. 신규 경제 선정0. P5는 사용자 별도 지시 전 보류.** 실제 성능 판정은 `blocked`이며 이 판정을 정책 수치 승인·운영 적용과 구분한다.

## 1. 코드와 권한 경계

- 손절 격리 작업본: `/home/ubuntu/KORStockScan-worktrees/main-stop-research-20261018`, base `9e78afd1194233d87c4d340ba2f1981d340d88d4` → `eb8e18cefacad23a298fd237093732e0f0977d70`.
- 최종 손절 코드 계약: `f866d881d42db285eed3248961baf702025cd47ff94e778117127408905bb5b9`. [종결 영수증](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/code-review-closure.json)에 파일별 바이트·명령·검토·최종 결과를 결속했다.
- 보유 비용은 별도 branch `d81a80778`→`3ab6916e2`, 별도 terminal 진단은 `57a4659f4`다. 이 branch들을 통합 검증했다고 주장하지 않는다. [비용 후속 검토](main-holding-research-cost-consumer-followup-review-2026-10-18.md), [가격·이력·비용 시각 후속](main-holding-exit-followup-research-execution-review-2026-10-18.md)을 각각 유지한다.
- 운영 선택900·원천10/16·실제 준비 대상10/19·원 정책/selector는 보존했다. Main 기동/재시작·배포·운영 정책 발행·계좌/API·구독·provider·주문·외부 sync·P5는 실행하지 않았다. 아래 private fixture의 source10/08·target10/09 로딩은 P5가 아니다.

새 모듈은 `src/engine/automation/main_stop_runtime_workload.py`, 새 시험은 `src/tests`에 두었다. engine root에 새 Python 모듈을 추가하지 않았다. 기존 Main의 반복문은 `_run_sniper_iterations`로 추출했고 startup/continue/break/예외/정리 경계를 역구성한 AST와 원 루프 AST를 검증했다. 원 루프 AST SHA는 `a549e790d27ed4e4b86a14cfb46187cfec7dcee51f1fa869a84195e3f3dc04a5`다.

## 2. 실제 발견한 런타임 결함과 보완

`normal`의 `exit_requested` 사전 확인 뒤 `fast`가 실제 claim·DB pending·영속 장부·격리 HTTP 경계까지 도달한 상태에서 normal dispatcher를 재개했다. **프레임 교체 없이도** normal이 새 매도 세대로 덮어써 `sell_submit_db_owner_rowcount:0`과 `FAST_EXIT_SUBMIT_RESPONSE_STALE`이 재현됐다. 원 재현은 보존했다.

수리는 `_dispatch_scalp_preset_exit`의 잠금 안 소유권 검사다. 최초 청산 정보 기록·계좌 조회 뒤 unknown/0수량의 상태/DB 변경·재시도·최종 새 세대 생성에 현재 토큰/세대/수량/상태/수동 보호를 대사한다. 새 sticky claim을 도입하지 않는다. 기존 정확한 preset 원주문 취소/정산 입장은 보존하고, old generation을 native owner가 해제하기 전 새 SELL은 금지한다. 동일 fast token의 안전한 재시도도 유지한다. 선행 소유자가 바뀌면 후발 결과는 그 세대·rule·수량·경로·수탁 장부를 변경하지 않는다.

별도 원천 경합도 재현했다. normal이 실제 평가에 진입한 뒤 quote capture 반환 사이 fast가 제출하면, 뒤의 live pending 상태로 앞선 normal 영수증을 버리던 `native_evaluation_custody_generation_changed`였다. 이제 평가 진입의 필요한 필드만 bounded snapshot으로 묶고 evaluator별 고정 quote slot·세대 원자 예약·불변 capture 직접 반환·동일 세대 cache CAS를 사용한다. 전체 stock 복사나 잠금 안 파일/queue 처리는 하지 않는다. 실제 pending 상태는 snapshot 그대로 봉인하며 replay의 pending 제외와 주문 직전 현재 소유권 guard를 유지한다. 새 BUY lifecycle에서 context slot을 초기화하고 REST evaluator 원 이름도 보존한다. 원천 envelope의 record도 해당 불변 row에 결속한다.

실제 정상 보유에서도 다른 경로의 완료 순서와 native caller 시각의 순서가 달라 global 번호를 누락으로 오인하는 생산소비 결함을 재현했다. 신규 원천은 normal/fast 두 lane의 순번·현재 process PID/incarnation·lifecycle ticket과 원 global 번호/vector를 함께 봉인한다. 소비자는 lane 순서와 global 전체 존재·중복을 분리하고 조기 후보 계산 뒤에도 신규 scope의 무결성을 확인한다. Claim 예산을 적용하며 원 시각을 고쳐 쓰지 않는다. 기존 lane marker가 없는 자료의 global 분기와 경제 판단 함수는 유지한다. [원 실패](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/source-order-diagnosis-attempt-02/index-replay-result.json)와 [수리 후 실제 재현](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/source-order-diagnosis-attempt-03/index-replay-result.json)을 보존했다. 실제 수리 후 normal2/fast3·global5/5·결속 gap0이며 비용은 `cost_model_source_missing`/null로 남겼다. 이를 경제 지원이나 손실0으로 비용을 보정한 결과로 삼지 않는다.

공식 reference gate는 공개 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`의 specs/core/client·auth/packaged `kt10001`·`kt10003` 및 Postman PRD/MOCK를 대사했다. 해당 tree에 `kiwoom_docs`가 없다는 사실을 남겼다. [조회 시각·경로·해시](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/official-reference/inspection.json)와 [취소 대사](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/official-reference/cancel-protocol-inspection.json)를 보존한다. wire·parser·auth·route·수량/가격 단위·양수 취소 guard·threshold·우선순위는 변경하지 않았다. 공개 문서 조회는 실제 broker 호출이 아니다.

## 3. 성능 생산자와 소비자 계약

| 경계 | 실제 구현 | 실패 시 처리 |
| --- | --- | --- |
| native Main·fast → 측정 | 실제 Main 회차·holding·native monitor WS wake/주기 poll·claim·등록·최종 주문 guard·private SQLite/장부. 최종 HTTP와 계좌 응답·시계/파일시스템만 명시적 adapter | 외부 통신/쓰기·원 DB 접근 거부. actual 주문/체결 증거로 사용하지 않음 |
| frame 생산 → 소비 | DB commit 후 입력 공개, 이전 배치 drain·frame generation 대사. 측정 Main은 frame gate 밖에서 실제 fast와 경합 | 사전 priming을 방문/단계/lock 증거에서 제외. 오래된 배치를 새 WS 완료로 인정하지 않음 |
| WS wake | native event set으로 accepted를 관측하고 같은 세대의 실제 배치 반환을 확인 | SELL_ORDERED의 무시만 정상 진단. HOLDING 등 다른 미수용 wake는 `wake_unavailable` loss |
| cell 입력 | `measurement_cell`은 기존 ROLES×MARKETS의 명시적 typed 값. 실제 stock role·native session/매도 시각·호가와 대사 | label만 재기록하지 않음. 원천/시각/경로 미지원은 explicit unsupported |
| 성능 receipt → 실험/발행 | 실제 모든 arm의 stage·같은 cell의 guard/전송·장후 cold/warm 선정 cell 교집합, exact parent·등록 grid·실제 winner 값 대사 | 다른 cell/부모/후보의 PASS 재사용 금지. 누락/양수 loss·가짜 v1 label·capture-only v2로 신규 발행 금지 |
| 동시 장후 | native prepare/재생/선정 + private all-carry publish→handoff→loader의 cold1/warm1 | 성능 측정 중 신규 수치 정책을 먼저 발행해 자기 증명을 순환시키지 않음 |

장전 SCANNER·정규 preset·통합 장후 SCALPING의 실제 guard/장부 양성과 잘못된 role/시각·매도 불가 시각·장후 route 충돌 음성을 검증했다. 이를 전셀 full 성능 PASS로 확대하지 않는다. 본 측정 cell은 `SCANNER|REGULAR`, certified cells는 `['SCANNER|REGULAR']`다.

## 4. 고정 예산 본 측정

[실제 성능 receipt](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/performance-attempt-03.json)와 [실제 소비 검증](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/private-consumer-attempt-01/consumer-receipt.json)를 사용했다. 3회 교대 paired run, arm/run당 reset frame512개·warmup32개, **측정3072 frame**을 완료했다. 각 frame의 원 포지션/장부 identity는 새로 만들고 같은 입력을 재사용한 synthetic 관측이다. 독립 자연 거래3072건이나 과거 실체결로 부르지 않는다. 8개 scenario에는 복수3종목·hard/emergency·수동 veto·미확인 계좌 수량·5주 전량·보유 경로를 포함한다. 동시 장후는 등록된256개 synthetic position·4608 source row를 사용했다.

예산은 측정 전에 고정했다. p95/p99 악화 허용은 baseline의5%와1ms 중 작은 값, 손절 도메인 p99 연구 상한250ms, CPU/논리 rchar·wchar5%, process RSS1GiB·warm growth64MiB·job temp2GiB·receipt1MiB다. 큐/공유 managed64MiB 계약은 유지했다. 기준을 넓히거나 동일 결과를 반복해 PASS를 만들지 않았다.

| arm/run | p50 ms | p95 ms | p99 ms | max ms | process CPU s | 동시 frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline1 | 26.672 | 98.460 | 113.872 | 325.291 | 60.542 | 512 |
| baseline2 | 26.620 | 101.135 | 110.823 | 393.773 | 70.829 | 512 |
| baseline3 | 25.966 | 99.354 | 113.180 | 470.478 | 71.668 | 512 |
| candidate1 | 26.681 | 99.179 | 113.969 | 472.390 | 65.331 | 512 |
| candidate2 | 26.800 | 99.510 | 110.414 | 480.394 | 68.826 | 512 |
| candidate3 | 26.935 | 98.883 | 110.756 | 474.110 | 72.862 | 512 |

최종 판정: **`blocked`**. findings: `cpu_regression:0`. `cpu_regression:0`은 첫 pair의 전체 process CPU `60.542143739`→`65.330956086`초, **+7.909882% > 허용5%** 한 건이다. 지연·I/O·RSS·temp와 원천/안전 기준은 통과했다. 원인을 grace 값 자체로 단정하지 않으며 전체 process·측정 부하를 포함한 비악화 입증 실패다. 실제 소비 결과: `blocked_consumption_verified`. 확정 실험 `0`·수치 정책 `0`·committed pointer `0`로 발행 차단을 확인했다. loss 합계: `{"duplicate": 0, "evaluation_rejected": 0, "missing": 0, "new_expiry": 0, "queue_rejected": 0, "source_rejected": 0, "source_superseded_rejected": 0, "wake_unavailable": 0}`. 고정 성능 기준 미충족을 경제적 무개선이나 승인으로 바꾸지 않는다.

baseline/candidate는 **같은 최종 코드의 다른 정책값(grace60/0)**이다. 기존 선택 릴리스 대비 speedup·Main 전체·entry PASS/due·scanner/다른 장후 heavy job·live provider·운영 PID·자연 손익을 증명하지 않는다. native 처리 지연은 ordinary1초 idle adapter를 제외하며 setup/전체 process CPU·RSS/I/O는 따로 보존한다. lock 통계는 frame별 native acquisition 최대/합계/횟수다.250ms는 실제 monitor poll의 지연 보장이 아니다. cold/warm은 application 작업 구분이며 OS page cache cold 보장은 아니다.

고정 workload의 common-soft는 실제 평가 단계에 진입하는 보유 사례다. soft 기준선 이탈 뒤 유예·AI 판단·실제 soft 주문의 모든 분기를 측정했다고 확대하지 않는다. hard/emergency·수량·현재 수탁·최종 guard/격리 전송 경로는 해당 고정 scenario에서 실제 실행했다.

## 5. 현재 연구의 종료 판정

| 단계 | 현재 종결 근거·한계 |
| --- | --- |
| S0 계약 | 실제 이름·타입·단위·시각/known-at·BUY/record/cell·공식 능력 registry와 source/consumer 대사. 로컬 미수집과 API 미제공·복구 불가를 구분 |
| S1 원천 | native 평가/수량·terminal·전체 coverage·원 AI 결속 및 별도 holding 비용 adapter 수리. 과거 없던 depth/AI/fill을 생성하지 않음 |
| S2 경로 | 지원되는 preset/common·정상 청산/회복·수탁/부분결손 분모 및 native 경쟁 보호. preset 선행의 조건부 비도달과 실제 관측을 구분. 활성 보호선 generator가 없는 R4는 `source_unsupported` |
| S3 비용 | stop 비용 적격4와 holding 엄격 provenance5, 별도 terminal 참고8의 서로 다른 분모 유지. exact/allocated/model·actual/CF 분리. 공통 경제 paired0 |
| S4 생산 | native Main+동시 장후 실측 producer·typed cell·실제 성능 소비를 연결. 결과의 pass/block을 실제 숫자로 봉인하며 미측정 셀로 확대하지 않음 |
| S5 유한 연구 | 현재 historical cohort의 source gap/검열·지원 판단0 및 미선정 결론 종결. R3/R4/R5·E4/E5/E7 새 전략을 모두 구현·실행했다고 처리하지 않음. 새 가설/입력은 별도 등록 |
| S6 인계 | native 준비/선정·private carry 발행/로딩과 selected 발행의 실제 승인/차단 계약 검증. 기존 초기 부모 승계에 새 경제·자연 주문 허들을 붙이지 않음 |
| S7 자연 수용 | 현재 연구 종결과 구분해 기존10/19 `HoldingProfitExitSourceContractRepair`·`DirectFamilyPreopenPolicyHandoff`가 자연 source/PREOPEN/PID/종결·비용을 수용. 이 단계의 운영 성공을 주장하지 않음 |

과거56,980관측/15포지션·source gap15·지원 판단0은 원 세대의 결과로 보존했다. [의미 재사용 bridge](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/historical-result-reuse-bridge-v2.json)는 변경 없는6개 의존파일·기존 순수 builder/경제 판단 AST·live producer/dispatcher 비소비 경계 및 새 marker가 없는 legacy 분기의 회귀 근거를 구분한다. 신규 lane 소비자 `evaluation_binding`·`bound_evaluations`·`replay` wrapper는 변경됐으므로 전체 reader AST 불변으로 설명하지 않는다. 전체12GB fresh replay·현재 전체 raw 재해시나 새 코드 세대에서의 자연 경제 비교를 수행했다고 주장하지 않는다.

[원 census 범위 bridge](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/historical-legacy-cohort-census-bridge.json)는 원 census의 `evaluator_census={}`/지원0과 당시 두 native producer가 새 lane/incarnation marker를 생산하지 않는 원 bytes를 대사했다. 이는 원 세대의 미지원 결론 유지 근거이며 현 raw에 대한 새 전수 marker 검색·재해시는 아니다.

## 6. 검증·실패 보존·다음 경계

최종 통합 회귀는 **1653 PASS·경고1·191.08초**, 동결 파일28개 바이트 불변이다. 정확한 명령은 [validation](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/validation-attempt-04/final-validation.json)를 따른다. Python28파일 compile·Ruff·diffcheck·독립 리뷰→추가 발견→수리→재리뷰를 완료했다. 최종 실제 성능·소비 영수증의 독립 readback에서도 미해결 지적0을 확인했다. 이전1526 PASS는87cad 세대, 그 뒤301 PASS는cold adapter e6a4 세대이며 최종 회귀와 합산하지 않는다. 첫1504 PASS/동시 code변경 예외, cold import 차단, warmup DB/소유권 실패 및 원 native 경합 재현·중간 성공은 별도 원문으로 보존했다. 예비 실패를 p95/p99 결과로 부르지 않는다.

이전100frame stress는 제출·수탁100건을 확인했으나 loss assertion 하나가 실패했고 당시 counter가 출력되지 않아 정확한 원인을 확정하지 못했다. 세 번의 private100frame 재시도 및 이후1558개 회귀는 통과했으나 이를 원 실패 원인 입증으로 삼지 않는다. 별도 scheduling-only 재현으로 위 원천 경합을 확정·수리했으며 해당 실패/성공 원문을 유지한다. 1558 회귀 중 시험파일의 진단 출력·assert 메시지만 바뀌어 원 freeze 불변 판정은 false였고, [원 SHA/동일 시험 AST bridge](/home/ubuntu/KORStockScan/tmp/main-stop-full-runtime-research-20261018/test-diagnostics-bridge/receipt.json)를 남겼다. 최종 검증은 그 기록을 덮어쓰지 않는 새 고정 세대다.

현재 `MainStopResearchExecution1018`과 `MainAllScopeTrailingReplay`의 이 입력 범위 연구를 종결한다. 자연 추가 표본으로 같은 과거가 복구될 것이라는 영구 대기 조건은 두지 않는다. 새 정책 우위·운영 배포/PID·실제 fill/손익은 미입증이다. 이미 따로 승인된 코드 통합·선택 전 후보 준비는 그 owner의 범위이며, 이 결과가 이후 commit의 자동 포함이나 P5 실행을 승인하지 않는다.

**P5는 모든 연구 종료 뒤에도 사용자의 별도 실행 지시 후 진행한다.** 그때 최종 통합 코드·원천·정책·선택본을 다시 고정하고 기존 native code-handoff/loader 절차를 따른다. 원 정책과 과거 receipt의 해시를 바꿔 쓰거나 현재 코드 검증에서 제외하지 않는다.
