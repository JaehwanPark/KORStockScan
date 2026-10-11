# 2026-10-10 Stage2 To-Do Checklist

## 오늘 목적

- Main 전체 trailing/replay와 제출 지연 v2의 잔여계획 W0–W5의 구현·반복 리뷰·정식 인계와 10/12 기동 준비를 완료한다.
- 완료된 PASS 제출 경로 개선, 두 구현 owner의 완료 기록, 손절 후속 계획 owner와 적용일 자연 기동 수용을 구분한다.
- Main 손절 퇴역 제거·런타임 보완과 기본 유예·보호 트레일링 정책화/장후 튜닝 계획을 수립·검증한다.

## 오늘 강제 규칙

- 기존 trailing/delay 요청은 잔여계획 실행이다. 구현→리뷰→수정→재검증으로 닫은 뒤 기존 승인 범위의 정식 발행·affected 장후 인계·배포를 수행한다. 미래 자연 PID 수용은 적용일 owner로 분리한다.
- 원 요청·native claim·deadline·정책 identity 및 주문·수량·자금·freshness·Main/manual 소유권 guard를 보존한다. 퇴역 episode/widget 실행을 복원하지 않는다.
- 진단 저장 결손은 미확정으로 보고하며 주문 재전송이나 broker 거절로 합성하지 않는다. 기존 10/9 기록과 봉인된 10/12 checklist를 보존한다.
- Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다.
- 손절 신규 요청은 계획 수립 범위다. 기존 trailing/delay 실행과 구분해 코드 삭제·정책 발행·장후 재생·배포·기동은 후속 손절 구현 요청 때 착수한다.
- 기존 두 상세계획의 구현·반복 리뷰·배포·다음 영업일 기동 점검 승인을 유지한다. 전체 구현/성능 완료 후 정식 발행·장후/PREOPEN 인계까지 수행하는 계획이며, 부분 코드 배포로 전체 완료를 대체하지 않는다. 부모 계승·0초 baseline에 추가 경제 gate를 만들지 않고 봉인된 기록은 정식 successor로 승계한다.

## 실행 항목

- [x] `[InitialQuantityProducerConsumerRepair1010] 최초 수량 보완 작업의 10/11 이전` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - 자정에 같은 ID·Q0–Q8 수용·미완료 상태를 [10/11 현행 owner](2026-10-11-stage2-todo-checklist.md)로 이전했다. 이 체크는 작업 완료가 아닌 이전 완료다.

- [x] `[SemanticMonitorLatestReleaseRepair1010] 의미적 감시기 최신 릴리스 연계 보완` (`Due: 2026-10-10`, `Slot: DOCUMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [상세 보완계획 M0–M8](../proposals/semantic-monitor-latest-release-followup-repair-plan-2026-10-10.md).
  - 현재 범위: 상세 계획 수립·문서 검증만 수행한다. 감시 코드 구현·정책 발행·장후 재실행·Telegram 발송·배포·재기동은 이번 요청에 포함하지 않는다. 구현 착수 시 같은 stable ID와 수용을 실제 실행일로 이전하고 current parsed owner는 하나로 유지한다.
  - 수용: 청산/초기수량 구조화 알림, 정책 등록·승계의 정확 복구, 현행 담당 작업 연결, 상태별 producer→notifier→recovery 교차 회귀를 닫는다. 원천·lifecycle·경제성 및 역사적 미복구를 분리하고 state 삭제·가짜 종결·추가 매매 gate를 금지한다.
  - 연계: 제출 지연의 선택 due·원 PASS/claim/deadline, 전수 trailing/delay 장후 source/shard/global census·정책/준비/PID를 실제 설치 범위로 검사한다. 손절 정책화는 해당 owner 구현 후 연결하며 episode/widget 전체 자동 퇴역·수동 수탁을 보존한다. 기존 trailing/delay 승인과 자연 수용 owner를 대체하지 않는다.
  - 종료: M0 기준 고정→F1–F4 수리→영향 기능/성능 검증→반복 리뷰 후 승인된 배포 인계. 미배포 의존성·10/12 미래 자연 수용은 별도 표시하고 봉인된 체크리스트/준비는 지금 변경하지 않는다. 이번 문서 수용은 코드 수리 완료가 아니다.
  - 계획 검증: 생산자/마지막 소비자 10경로·M0–M8·알림/복구 상태·owner 이전·성능/배포 수용을 재리뷰했다. 보조 AI의 기존 10/12 owner와 기계 owner 부재를 구분하고 유효 ancestor pin을 보존하도록 보완했다. 로컬 링크 23개 결손 0, 공백 검사·print-only parser PASS, 현재 owner 1건. 코드/운영 수리는 미착수다.
  - 계획 재리뷰 보완: R1–R6로 findings 공백과 비교 source gap 분리, 기한 후 관측 불능, 비기계 stage 복구·state 128건 상한, 필요 incident에만 current owner 요구, 읽기 세대·결손 identity를 구체화했다. 즉시 수리 A와 기능 연계 B의 성능/배포 gate를 분리해 전체 W4·미래 표본이 알림 수리를 막지 않도록 했으며, 기존 봉인·권한·퇴역 경계를 유지한다.

  - 이전: 10/11 같은 stable ID의 현행 OPEN으로 수용·역사를 이전했다. 구현 완료 표시는 아니다.

- [x] `[MainStopLossRetirementRuntimeTuning1010] Main 손절 퇴역 제거·런타임 보완·정책화 및 장후 튜닝 후속 구현` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [손절 구현·보완 및 연구계획 SL0–SL8](../proposals/main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md).
  - 현재 범위: 계획 수립·문서 검증만 수행한다. 후속 구현 요청 전에는 코드 삭제·정책 발행·장후 재생·배포·기동을 실행하지 않는다. 실제 착수일에 같은 stable ID와 수용·진척을 이전하고 current parsed owner는 하나로 유지한다.
  - 수용: holding score 손절·기타 OFF 전용 코드·whipsaw 실행/관측/추천/정책 의존을 전수 제거하고, fast/normal 수동 인계·role별 기준·quote/clock·pin/claim 결함을 보완한다. 기본 False지만 관측 계산 ON인 기능을 실매도와 구분하고 Main/manual 수탁·hard/protect/emergency 안전을 보존한다.
  - 정책/연구: 소프트 손절 기준선·60초 기본 유예·보호 트레일링 확인 파라미터를 현행값 계승 정책으로 구현한다. runtime/replay 공통 판단·forward train/holdout·실제 비용/검열·bounded 후보·부모 유지·exact key 승계·정식 장후/selector/PREOPEN/pin을 연결한다. whipsaw 추가 유예를 재도입하거나 hard safety·operator veto의 자동 변경 권한을 만들지 않는다.
  - 생성/성능: 시간 경과로 해소되지 않는 producer 부재·필드 누락·도달 불가능 경로·순환 선행조건·전역 표본 gate·schema/target 불일치를 SL0에서 대사하고 SL5에서 실제 producer→loader 성공/부분 결손/정정/재개 시험으로 닫는다. 정책 생성·경제값 변경·실제 소비를 구분하며 capture부터 발행/strict/PREOPEN/pin까지 구간별·전체 성능, 증분 재사용·합산 자원/기한을 검증한다.
  - 누락 재점검: 계획 §5.1의 17개 임계치 묶음·§5.2 실효 우선권·§6.5 생산/소비 이행표를 따른다. vote replay의 경제값 null/기본값 전용 publisher, preset·fast 차이, 선행 crossing/30초 원천, defensive unfilled no-op 잔여와 관측 ON 오해를 SL-F10–SL-F15로 반영한다. 새 stop stage/발행/strict/bootstrap/lookup이 현재 설치됐다고 간주하지 않는다.
  - 계획 검증: 후속 재점검의 임계치 17개 묶음·로컬 링크 62개 결손 0·공백/문서 재리뷰·diff·print-only parser PASS, 손절 현재 owner 1건. 계획 보완 완료이며 손절 코드 구현·정책 발행·성능 실측은 미착수다.
  - 종료: 삭제·consumer migration·런타임 회귀·단독/결합 성능·반복 리뷰의 미해결 구현 finding 0. 초기 부모 계승에 추가 경제 gate를 붙이지 않으며 정식 인계·실제 PID·자연 terminal/경제성은 각각 증거를 기록한다. 기존 trailing/delay owner의 승인·완료 범위를 소급 변경하지 않는다.

  - 이전: 10/11 같은 stable ID의 현행 OPEN으로 수용·역사를 이전했다. 구현 완료 표시는 아니다.

- [x] `[MainAllScopeTrailingReplay] Main 전체 종목·시장 trailing 및 replay 구현·반복 리뷰` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [전체 범위 구현계획 AT0–AT7](../proposals/main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md), [잔여작업 W0–W5](../proposals/main-trailing-delay-residual-work-completion-plan-2026-10-10.md).
  - 수용: 누적 입력창 비용/projection 세대, 공통 scope와 실제/CF 분리, runtime/replay 공통 판단, causal situation pin·부모 계승, 격리 초기 생성·consumer migration·합산 예산을 구현하고 영향 회귀·성능 비교·재리뷰로 닫는다. 원천 미관측·경제 적격·자연 소비를 코드 완료와 분리한다.
  - 구현 근거: [공통 구현·반복 리뷰](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md). 누적 과거 비용 무효화, 전체 scope/공통 재생·ADD/익일 pin 승계, 12-cell 승인 부모 계승, bounded checkpoint/공통 cohort 집계를 구현했다. 변경 없는 원천의 cost-only 정정은 원천 JSON decode 없이 실제 손익을 미확정으로 전환하며 clean recompute와 같다. 계산 부분의 절감은 전체 장중·장후 성능 수용과 구별한다.
  - 후속 보완: 등록된 유한 classifier grid의 train 선택·holdout 고정, 원 AI crossing 입력의 후보별 결속, selector 실제 byte SHA 참조·원 classifier/시장/부모와 one-market canary 결속을 검증했다. source/cost/code를 최종 집계 뒤 다시 검증하며 변경 시 report/policy를 발행하지 않는다.
  - 자원 보완: numeric 후보/부모와 독립인 source-feature spool을 구현했다. 기존 경로를 source hash로 결속한 여러 input segment에서 이어 재생하고, M1 상태·원 quote/AI 입력·ADD를 보존한다. 4MiB 초과 경로의 결과/상태·cached 결과 사용 시 원 leaf byte 검증·손상 feature 재구축을 검사했다. source-feature spool은 64MiB의 별도 저장 상한을 명시하며 이를 무제한 temp 허용으로 사용하지 않는다.
  - 잔여 구현 전 공통 코드 배포 기록: 후속 리뷰 1,079 passed, 불변 릴리스 262 passed. `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28` 선택과 웹 PID 48969 전환 완료. 부모 동등 12 cell, 기존 기계·보조 원본 보존, 10/12 PREOPEN 전체 계약·finalization·cron 8경로 PASS. [기동 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-readiness.json); 자연 Main 기동은 07:55 future_due이며 전체 연구 수용은 OPEN이다.
  - 잔여 구현 전 기록(이후 W0–W5로 완료): 전수 native/forward/실제 비용 연결 producer와 대사, 적격 실제 유형 후보 선정, source/feature spool 상한을 넘는 job의 전수 분할·재개와 cache eviction/전체 candidate block, 전체 workload 성능 gate. 원천 결손·미구현을 초기 부모 계승의 추가 경제 승인 요건으로 바꾸지 않는다. 신규 경제 정책 발행·전수 연구 수용과 검증된 공통 코드의 승인 배포·PREOPEN/PID 수용을 분리한다.
  - 잔여 실행: W0 기준/예산 고정→W1 실제 source 자동 manifest·정상 장후 caller 연결→W2 상한 초과 전수 분할/재개·전역 cohort→W3 부모 계승/적격 후보·소비→W4 전체 Main/due/보유보호/장후 성능→W5 최종 release·정식 chain/PREOPEN. 실제 비용 미배분은 census에 남기고 해당 actual 경제 평가에서 제외한다. 전체 source-gap을 구현 공백의 이유로 사용하지 않는다.
  - 종료: 전수 처리·consumer migration·전체 성능의 미해결 구현 finding 0과 formal 부모 계승/적격 정책의 strict/finalization/PREOPEN 수용. 후보 0·미래 PID를 추가 구현 종료 조건으로 삼지 않는다. W6 자연 수용은 적용일 기존 owner에 인계한다.
  - 잔여계획 재리뷰: 실제 profile snapshot→holding report→selector caller, process-local 예산/2-slot heavy admission, 6개 scope disposition·기회/실제 거래 분모, 논리/물리 hash, 참조 중 cache/old-new 출력 peak, W5 전체 전환 세트·실패 복구를 필수 구현·시험 대사표에 포함한다. 기존 실패 시간으로 전체 성공 작업의 성능을 판정하지 않는다.
  - 완료: [실제 구현·반복 리뷰](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md). 전수 자동 source/tree·초과 분할/재개·전역 cohort·부모/0초·기존 selector/due와 전체 성능을 검증했다. 통합 1,371 passed(이전 릴리스에서도 실패한 historical 2건 제외), 최종 불변 릴리스 영향 215 passed. `main-trailing-delay-residual-20261010-v6` / `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`의 정식 발행과 native finalization DONE을 완료했다. [최종 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-residual-readiness.json): source 10/8, target 10/12, PREOPEN `current_full_contract=pass`, finalization issues=[], 설치 cron 8경로 PASS. 기계/보조 원본·EOD bytes 보존, Main은 10/12 07:55 future_due다. W6는 봉인된 10/12 기존 `DirectFamilyPreopenPolicyHandoff` 한 owner가 확인한다.

  - 구조 결함 재개: P1–P5 상세계획의 현재 PASS/identity·pre-signal holding-AI·classifier 인과성·후보별 적격 pair/대용량 bridge·일반 악화/horizon 조건을 구현→리뷰→보완→회귀로 수리한다. 위 완료 기록은 당시 부모/0초 발행 근거로 보존한다. 10/12 봉인 checklist는 변경하지 않는다.
  - 후속 운영 승인 완료: source 10/8·publication 10/10·effective 10/12로 [운영 장후 재생성·정식 인계](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md)를 수행했다. `main-trailing-delay-structural-20261010-v1` / `c66488df8d428ecda57ee3c052c630c3e68f74b2` 선택, 불변 릴리스 114 passed, summary/strict/controller·23:33:47 native finalization DONE·[PREOPEN 전체 계약 PASS](../../data/report/main_trailing_delay_deployment/2026-10-10/final-structural-readiness.json), cron 8경로와 웹 ubuntu/PID 227302/HTTP 200을 확인했다. trailing 12 cell 부모·지연 0초이며 EOD·원 기계/보조 bytes 불변, 원 봉인 checklist는 snapshot 보존/정식 successor 인계다. 이번 코드 수리·정식 운영 인계는 완료하며, Main은 중지 상태를 유지해 10/12 기존 DirectFamilyPreopenPolicyHandoff에서 자연 PID 소비를 확인한다. 새 자료·성과와 전체 운영 성능은 별도 미측정 수용이다. 기존 독립 warning은 숨기지 않고 audit에 기록한다.
  - 구조 수리 코드 완료 당시 기록: [P1–P5 구현·반복 리뷰](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md). 통합 606 passed, alias/normalizer 보완 후 215 passed, 최종 train generation 결속 후 71 passed. 새 anchor v3·지연 pair 알고리즘 v3·원 holding 요청/coverage·원 pin 불변·후보별 pair/대용량 bridge·기존 손실 guard를 검증했다. 운영 재생성·배포·PREOPEN·자연 PID 소비는 미실행이며 OPEN을 유지한다. 이전 v6 발행 기록과 봉인 10/12 owner는 보존한다.

- [x] `[PreSubmitDelaySituationImplementation1010] Main pre-submit delay v2 초기정책·관측·due 재점검 구현` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [제출 지연 상세계획 S0–S6](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md), [잔여작업 W0–W5](../proposals/main-trailing-delay-residual-work-completion-plan-2026-10-10.md).
  - 수용: 원 PASS 관측·두 anchor·shared split/purge·cell/fallback·committed generation·준비된 lookup·현재 scheduler successor·단일 decode/증분 감시를 연결한다. v1 의미·원 deadline·주문 guard와 Main/manual 경계를 보존하고 격리 재생·반복 리뷰·단독/결합 성능을 검증한다. S6 정식 정책 발행·장후 인계·PREOPEN까지 수행하고 실제 PID 자연 수용만 적용일의 별도 단계로 분리한다.
  - 구현 근거: [격리 계산·반복 리뷰](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md). 실제 제출 함수의 scanner/fixed-watch × auxiliary v1/v2 경계, 원 발생 시각·queue 접수/append 구별, v2 durable generation/CAS·warm lookup을 검증했다. 실자료 commit 31/PASS 진단 29/P0 6/가격쌍 21, 정책 부모 해시 결손 29건이므로 격리 초기값 0초·양수 cell 0; 동일 세대 재계산 source JSON decode 0. 계산 부분 절감은 운영 성능 증거가 아니다.
  - 자원 보완: v2 원천은 원 record identity를 검증한 뒤 필요한 필드와 full-field conflict SHA만 보관한다. 최대 2GiB의 명시적 scan-job 상한과 64KiB record buffer, 같은 공유 resident-data budget의 동적 admission을 적용한다. legacy의 전체 decode를 조용히 무제한으로 바꾸지 않는다. 최소 projection과 원 projection의 qualification/census 동등성을 검증했다.
  - 잔여 구현 전 리뷰·공통 코드 배포 기록: 활성일/enable cache·만료 manifest 제거·관측 snapshot 공유·공통 writer 중복 mkdir를 보완했다. 정상/burst/slow writer의 동일 입력 3회 비교에서 의미 동일·누락 0·비악화 PASS. 위 최종 릴리스에 포함됐으며 신규 v2 운영 정책은 선택하지 않았다. 원 PASS의 부모 결손을 실제 가격쌍이나 실현손익으로 대체하지 않는다.
  - 잔여 구현 전 기록(이후 W0–W5로 완료): retained index/기회·최종 artifact 상한을 넘는 전수 입력의 분할·재개·global census/split 발행과 전체 due/burst/청산·장후 결합 성능 gate. S6 운영 장후 재생성과 신규 v2 정책 선택은 미실행이다. 후속 승인된 공통 코드 배포는 기존 지연 기본값과 부모 경제값을 유지하며 10/12 준비를 신규 세대로 검증한다.
  - 잔여 실행: W1 exact 부모/native 복원·불가 행 제외→W2 shard/전역 시간순 split·183초 purge·versioned verifier/publisher/loader→W3 price_ready 초기정책·due 새 증거→W4 통합 gate→W5 기존 dispatcher로 formal v2·summary/checklist/strict/finalization·신규 PREOPEN. 제출 지연 가격 비교에 actual fill/cost/청산을 추가 필수 조건으로 붙이지 않는다.
  - 종료: 유효 가격 비교와 근거가 정확한 0초 baseline도 정식 발행 가능. 전체 원천 무효는 blocked family/owner/artifact/다음 조건을 남기고 기존 즉시 동작을 유지한다. 자연 주문을 만들기 위한 호출·주문 및 원 PASS TTL 연장은 금지한다. 현재 선택 release에 v2 loader가 없다는 과거 설명은 적용하지 않으며 full-plan 완료는 W4/W5 근거로 판정한다.
  - 잔여계획 재리뷰: shard 간 뒤늦은 conflict의 전역 무효화, price_ready pair와 signal_ready 진단 구분, 전역 0초 baseline/개별 cell 실행 불가, successor 자체 deadline과 due+budget을 검증한다. release만 복구하고 신규 committed pointer를 남기는 실패를 W5 주입시험으로 잡고 source/정책/준비 세트 전체로 복구한다.
  - 완료: [실제 구현·반복 리뷰](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md). 전수 자동 source/tree·초과 분할/재개·전역 cohort·부모/0초·기존 selector/due와 전체 성능을 검증했다. 통합 1,371 passed(이전 릴리스에서도 실패한 historical 2건 제외), 최종 불변 릴리스 영향 215 passed. `main-trailing-delay-residual-20261010-v6` / `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`의 정식 발행과 native finalization DONE을 완료했다. [최종 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-residual-readiness.json): source 10/8, target 10/12, PREOPEN `current_full_contract=pass`, finalization issues=[], 설치 cron 8경로 PASS. 기계/보조 원본·EOD bytes 보존, Main은 10/12 07:55 future_due다. W6는 봉인된 10/12 기존 `DirectFamilyPreopenPolicyHandoff` 한 owner가 확인한다.

  - 구조 결함 재개: P1–P5 상세계획의 현재 PASS/identity·pre-signal holding-AI·classifier 인과성·후보별 적격 pair/대용량 bridge·일반 악화/horizon 조건을 구현→리뷰→보완→회귀로 수리한다. 위 완료 기록은 당시 부모/0초 발행 근거로 보존한다. 10/12 봉인 checklist는 변경하지 않는다.
  - 후속 운영 승인 완료: source 10/8·publication 10/10·effective 10/12로 [운영 장후 재생성·정식 인계](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md)를 수행했다. `main-trailing-delay-structural-20261010-v1` / `c66488df8d428ecda57ee3c052c630c3e68f74b2` 선택, 불변 릴리스 114 passed, summary/strict/controller·23:33:47 native finalization DONE·[PREOPEN 전체 계약 PASS](../../data/report/main_trailing_delay_deployment/2026-10-10/final-structural-readiness.json), cron 8경로와 웹 ubuntu/PID 227302/HTTP 200을 확인했다. trailing 12 cell 부모·지연 0초이며 EOD·원 기계/보조 bytes 불변, 원 봉인 checklist는 snapshot 보존/정식 successor 인계다. 이번 코드 수리·정식 운영 인계는 완료하며, Main은 중지 상태를 유지해 10/12 기존 DirectFamilyPreopenPolicyHandoff에서 자연 PID 소비를 확인한다. 새 자료·성과와 전체 운영 성능은 별도 미측정 수용이다. 기존 독립 warning은 숨기지 않고 audit에 기록한다.
  - 구조 수리 코드 완료 당시 기록: [P1–P5 구현·반복 리뷰](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md). 통합 606 passed, alias/normalizer 보완 후 215 passed, 최종 train generation 결속 후 71 passed. 새 anchor v3·지연 pair 알고리즘 v3·원 holding 요청/coverage·원 pin 불변·후보별 pair/대용량 bridge·기존 손실 guard를 검증했다. 운영 재생성·배포·PREOPEN·자연 PID 소비는 미실행이며 OPEN을 유지한다. 이전 v6 발행 기록과 봉인 10/12 owner는 보존한다.

- [x] `[MainPassSubmitRecheckLatency1010] Main PASS 인수·제출 연결 및 진단 지연 보완·승인 배포` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [구현계획 S1–S4](../proposals/main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md).
  - 수용: take/discard 이후 원 객체 종료·후속 claim 보존, 직접 종료 사유와 전이 identity·PASS 분모 연결, 기존 단일 관측 executor의 유한 접수·원 발생 시각, bounded trace 준비 진척, 실제 제출 함수 내부부터 격리 adapter까지 검증한다. 반복 리뷰·회귀·compile·diff·print-only parser 및 동일 입력 성능 비교를 기록한다.
  - 배포 수용: 재리뷰·회귀 후 불변 릴리스와 web pin을 통합 선택하고 원 10/8 장후 세대·10/12 checklist를 보존한다. 새 릴리스의 동일 정책 code refresh, 10/12 PREOPEN 전체 계약, strict/finalization 세대 및 설치 예약 경로를 확인한다.
  - 자연 수용: 10/12 기존 DirectFamilyPreopenPolicyHandoff에서 실제 PID의 정책 소비와 관측된 PASS→제출 또는 기존 guard 종료를 확인한다. 준비 검증과 자연 기동·체결·경제성을 구분한다.
  - 완료 근거: [반복 리뷰·구현 결과](../audits/main-pass-submit-recheck-latency-implementation-review-2026-10-10.md). 최종 고정 코드 19개 suite 2,424 passed / 139.65초, 기존 Pandas 경고 1건. 동일 부하 3회 비교에서 정상 전달 261.943→185.142ms·동시 전달 60.596→49.021ms; 진단 지연과 필수 저장 지연의 만료 의미를 분리 검증했다. compile·diff·문서 검증 결과는 audit에 기록한다. 구현 수용 완료이며 배포·자연 기동 수용을 뜻하지 않는다.
  - 후속 배포 완료: 재리뷰 2,424 passed / 139.44초, 불변 릴리스 326 passed / 9.25초. `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06` 선택, runtime 1,072파일 대사 결손 0, web PID 22143·ubuntu·새 cwd/commit·HTTP 200. 기존 정책 code hash가 일치해 정책 재발행 없이 새 격리 PREOPEN을 생성했다. [최종 기동 준비](../../data/report/main_pass_submit_deployment/2026-10-10/final-readiness.json)는 10/12 `current_full_contract=pass`, finalization issues=[], cron 8개 PASS, 07:35/07:55 예약 정상이며 Main PID 자연 소비는 future_due다.

- [x] `[PreSubmitDelayInitialPolicyPlan1010] Pre-submit delay 상황별 초기정책·장후 재생성 상세 계획` (`Due: 2026-10-10`, `Slot: DOCUMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [상세 개선계획](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md).
  - 수용: 전체 PASS·두 anchor·원천 복원·시간순 분할·상황별 cell과 0초 fallback, v2 생성/소비·due 재평가, 장후 재생성부터 PREOPEN까지의 owner·순서·유한 종결을 구체화한다. 계획 리뷰·보완·링크·공백·print-only parser를 검증한다.
  - 후속 성능 리뷰: 상세 계획 D10–D16·§4.4/4.5·§6.3·§9·§11에 정책 사전 로딩, snapshot/hash 공유, due/queue 예산·공정성, 장후 단일 decode와 cache 무효화, 증분 감시·재점검 owner 인계 및 성능 실패 시 발행 중단을 명시한다. 문서 수용이며 실측 성능 개선·코드 구현 완료를 뜻하지 않는다.
  - 범위: 문서 계획 완료만 기록한다. 신규 코드 구현·실제 정책 선정/발행·장후 재생성·release 선택·기동·실주문은 미실행이며 기존 10/12 준비 세대는 보존한다. 후속 구현 시 실제 날짜의 실행 owner에 S0–S6와 검증 기준을 연결한다.
