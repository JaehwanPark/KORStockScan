# 메인 제출병목 인과 복원 — 작업본 구현·리뷰

- 범위: [수리계획](../proposals/main-submit-bottleneck-causal-repair-plan-2026-09-21.md)의 확인된 판정/관측 연결 결함. 사용자 후속 구현·반복 리뷰 승인에 따른 작업본 변경이며 커밋푸시·배포·재기동·주문은 실행하지 않았다.
- 자연 검증 owner: [당일 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 `SubmissionBottleneckMonitorNatural0921`. WS P2/P3와 비용 경제성은 기존 별도 owner를 유지한다.
- 운영 재확인: 14:35 KST PID174887의 cwd는 `capital-coverage-repaired-20260921-4b3b4080c/src`, 시작12:57:39. 작업본 HEAD=`ea4788788`이며 이 변경의 배포 영수증이 아니다. 기존 dirty WS/문서/테스트 변경을 보존했다.

## 구현과 반복 리뷰

1. **S1 판정 이력:** 기존 capture hash를 경제성 관측·AI 결과·terminal까지 전달한다. 관찰 중인 종목당 하나의 process/정책/시도 식별 receipt로 명시적 부모 hash를 연결한다. Sentinel은 같은 six-field attempt, 순서·parent·owner·revision 내 action/screen을 검증한 전이만 최종 revision으로 집계한다. 구형·누락·fork·역순·같은 시각의 순서 불명·동일 revision 충돌·이전 실행 흔적은 계속 contract gap이다. 최초 ENTER_NOW와 전체 경제성 이력을 별도 보존하며 attempt/submit 분모를 늘리지 않는다.
2. **경제성 소급 금지:** revision별 proof를 분리해 다른 입력의 정상 proof를 충돌로 오인하지 않는다. 후속 성공이 최초 ENTER_NOW의 결손을 메우거나 앞선 proof가 최신 revision의 누락을 채우지 못하게 했다. 비진입 cache-only 관측 제외를 과거 ENTER_NOW가 있는 시도에 적용하지 않는다. 캐시 schema 재구축/과거 incident 삭제는 없다.
3. **S2 제한적 RECHECK 복원:** 기존 setup producer가 단독 large-sell·정상 source/완료봉·유효 setup·구조 edge·확인 volume·tail risk 없음으로 WAIT_CONFIRMATION을 만든 경우에만 실제 main core/policy도 RECHECK다. 매도 위험을 COMPENSATED/ENTER_NOW로 바꾸지 않는다. 구조 실패·불량 source·극단 스프레드 등 복합 위험은 BLOCK을 유지한다. main composer는 WAIT/no probe/기존 scanner 재평가를 유지한다.
4. **판정 원본과 로그:** 구형 feature probe 필드를 덮지 않고 `entry_decision_large_sell_print_detected`를 exact payload/hash에서 전달한다. terminal 중복 억제도 attempt뿐 아니라 revision을 구분하여 후속 재확인 종료가 사라지지 않게 했다.
5. **guard 원인:** 기존 guard 결과의 WS age/jitter·spread·stale·분류 상세/적용 한도·시각을 `pre_ai_observation_only` 영수증에 보존한다. 실제 제출 guard 실행 증거로 사용하지 않는다. 분류 로직·한도·추가 계좌 요청은 바꾸지 않았다. 현 evaluate_live_buy_entry 경로는 RTT 입력을0으로 전달하므로 과거 DANGER를 오래된 실제 주문 RTT의 영향이라고 추정하지 않는다.
6. **후보 경로:** `returned/partial_adapter_return`은 탈락 사유가 아니다. 동일 scanner generation의 후속 prune receipt가 확인되면 실제 사유를 연결하고, cycle가 명시적으로 충돌하거나 세대가 없으면 `candidate_disposition_missing`으로 남긴다. source_seen의 다른 cycle 사유를 전용하지 않는다. 후보·slot/cap/cooldown을 변경하지 않았다.

보완 리뷰에서 발견·수정한 문제:

- 관측 guard dict가 기존 문자열 wire contract에서 Python repr로 변환되어 파서에서 누락됨 → 명시적 JSON 직렬화 및 실제 logger→slim cache 회귀로 보완.
- process-local revision receipt가 경제성 operating snapshot에 섞여 replay digest에 영향을 줌 → 거래 상태 snapshot에서 진단 receipt만 제외. 원본·기계 hash·경제성 연결은 별도 identity에 유지.
- 동일 attempt의 후속 revision terminal이 기존 중복 억제에 걸림 → revision별 terminal 기록, 동일 revision 중복은 계속 억제.
- 경제성 이벤트 자체가 없는 revision에 다른 revision proof가 전용될 수 있음 → 각 revision의 존재 여부까지 검사.

## S0 원천 고정·실제 표본 재현

`data/ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl` 읽은 prefix 21,596,569 bytes, SHA256=`cf668c5d27da17ccc76443f2a98eb470a07554f57420db5a4a5cb26427b2fc32`. 13:20:11–13:50:11의 저장된 BLOCK39행을 기존 기본 policy/core로 재현했다. 보고서의 확정 BLOCK37과 분모가 다르며 충돌 시도에 포함된 후속 BLOCK2도 포함한다. 변경은 아래4행의 BLOCK→RECHECK뿐, 나머지35행 BLOCK 유지, 새 ENTER_NOW0. 아래4행의 comparison validator 오류0, main policy RECHECK도 확인했다. 원본을 복제/수정하지 않고 byte range와 line hash로 고정한다.

| Snapshot ID | Byte offset / length | 원본 행 SHA256 |
| --- | --- | --- |
| aims-66d3e5f8c1c07233e752 | 15222594 / 39912 | cd3b4a3201ec19e7d088d534b5680ed3627fc5b200ae0c0f4bc11ac27a8a563b |
| aims-c64ab5cea08621d3a5e5 | 15469143 / 36418 | bdb5a60b0c739c16a2f5bdcf349e5efe50ee7e383530989632ca48b4e05179e8 |
| aims-382eefbf0d05278cb7fa | 16950648 / 36128 | 305acf9d688a82a428046b5aa124b07052328a95b966fa894dc2f983d3129711 |
| aims-4426caf5c08d6fe53215 | 17638812 / 36064 | 8039967452a0bf735423617066dbf7f5d85ba12fbcf586df5342ad1737a95068 |

증분 cache의 bounded range `[27503729,61058161)`에서 두 시도의9event를 읽어 순수 snapshot 함수로 재현했다. 추출 `{offset,bytes,sha256}` 목록의 sorted-key JSON SHA256=`1661f9fd692df416d53c0d028fc1e1010ea3b00f8d7bf1095e359b801cec9af7`. 두 시도 모두 initial ENTER_NOW/latest BLOCK/legacy_unverified/UNKNOWN을 보존한다. latest 운영 산출물은 쓰지 않았다.

- 078350: 최초13:39:32.114134 `common_guard_block:latency_state_danger`, 후속13:39:36.708197 비진입 cache miss.
- **계획 진단 정정:** 085910의 최초13:43:11.236436은 `exact_broker_capacity_missing / kt00011_empty`이며 DANGER가 아니다. 후속13:43:14.742266 비진입 cache miss와 분리한다. 두 사례를 같은 원인으로 묶었던 설명을 수정했다. 과거 `kt00011_empty`의 상세 HTTP 원인이나 자금 부족을 이 표본만으로 확정하지 않는다.

## 검증과 미완료 경계

- 1차 affected4file 회귀305 PASS. 추가 revision/소급 금지/세대 결합/guard 직렬화/terminal 검증을 보완했다.
- guard 실제 producer/logger/cache 경로42 PASS(7 route/session × 2 position tag × 3 machine action). 이 검증 중 발견된 JSON 직렬화 누락은 수정 후 통과했다.
- 확장 합집합666 PASS, 관측 receipt를 추가한 producer1case에서 replay digest 실패를 발견했다. 진단 상태를 운영 snapshot에서 제외한 뒤 동일 case와 receipt 단위검증2 PASS로 재검증했다. 실패를 기존 문제로 제외하지 않았다.
- 최종 affected core/monitor/census244 PASS, main nonentry/revision terminal2 PASS, 최종 guard 차단 producer/receipt2 PASS. 중복 포함 개수이며 실주문/자연 수익성 검증 개수가 아니다.
- Python compile·git diff --check PASS. 로컬 문서 링크28개 결손0, print-only parser29task/기존 제출 owner1개 확인. 전체 trading suite·유료 provider/API 재호출·대용량 report 재생성·외부 sync는 하지 않았다. API 요청/응답/FID/구독/계좌 호출 구현은 수정하지 않아 공식 protocol 변경 검증을 수행했다는 주장도 하지 않는다.
- 최종 worktree에서 동시 작업의 WS/위젯 gateway/liquidity guard 변경도 확인했다. 이 수리에서 생성·수정한 코드가 아니므로 보존하며, 해당 변경의 전체 리뷰/배포 gate를 이 테스트 결과로 대신하지 않는다.
- pandas_ta의 기존 pandas copy_on_write deprecation warning은 별도다.

남은 자연 검증: 배포 후 명시적 revision의 producer→cache→report 소비, 신선한 후속 재평가, 실제 제출 직전 기존 자금 연결(S4), 정상 제출/정당 guard의 end-to-end. 이 turn에는 배포/재기동 권한이 없으므로 운영 효과·ENTER_NOW 증가를 주장하지 않는다. 과거 DANGER와 I/O의 직접 인과, 미기록 AI 실패 상세, failed_breakout 차단의 비용 후 적정성은 미확정이다. S3 WS 성능 수리/P2·P3와 S4 자금 재구현을 근거 없이 추가하지 않았다.
