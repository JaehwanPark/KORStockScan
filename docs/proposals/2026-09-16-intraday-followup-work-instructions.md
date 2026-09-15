# 2026-09-16 장중 결손 집중 작업지시문

작성 기준: `2026-09-16 08:05 KST`

## 1. 목적과 범위

이 문서는 9월 15일 장후작업에서 실제로 발생한 `FAIL`, 최종 산출물에 남은 비정상 warning, 오늘 장중 원천 결손이 의심되는 경로만 확인한다. 이미 성공한 일반 배포·기동 점검과 전략 전반의 정기 점검은 반복하지 않는다.

장중 확인 대상은 다음 다섯 가지다.

1. submit drought의 `exact_attempt_source_quality_gap`이 오늘 같은 attempt에서도 재발하는지 확인한다.
2. EOD 종목 eligibility에서 누락된 41개 코드가 오늘 scanner 분모·후보·주문 경로에 영향을 주는지 확인한다.
3. 전일 격리된 entry decision 3,508행의 `minute_candle_window_fresh_contract`와 원천 label 결손이 오늘 새 행에서도 발생하는지 확인한다.
4. microstructure 진단의 `evaluation_venue_missing_or_conflicting=64`와 위젯·episode timing의 terminal pair 결손이 오늘 자연 원천에서 해소되는지 확인한다.
5. 전일 AI replay follower의 cohort failure와 exact 비용 parent 부재가 오늘 새 자연 사례에서도 이어지는지 확인한다.

이 문서는 읽기·진단과 허용된 source/report/schema/instrumentation 수리의 우선순위를 정한다. 실주문, 수동 env·operator lock·threshold·provider·수량·target·safety 변경 또는 매매 process 재기동 권한을 추가하지 않는다. 결함이 확인되면 [장중 모니터링 지시문](../intraday-monitoring-task-instructions.md)의 권한과 review gate를 따른다.

## 2. 전일 실제 장애와 오늘의 확인 경계

| 전일 상태 | 직접 근거 | 오늘 다시 여는 조건 |
| --- | --- | --- |
| Main verifier FAIL 후 복구 | 22:14:15 `status=fail`; 23:11:21 tail repair terminal | 같은 attempt의 raw/audit/consumer 보존식, source hash 또는 필수 field 결손이 새 원천에서 재발 |
| AI replay follower FAIL | 3회 bounded attempt 뒤 exit 1; compact 5건 모두 `source_partition_not_allowed`; provider call 0 | 허용 partition의 오분류, 비-`ENTER_NOW` 행 혼입, exact 비용 parent·outcome 재결손 |
| Finalization·cleanup FAIL 후 복구 | predecessor fail 뒤 00:46 cleanup fail; 01:10·01:23 cleanup/detector 완료 | 장중 shared writer·lock·generation publish에서 같은 결함이 새로 발생 |

이미 성공한 release route, 소유권 정책, PREOPEN, main/widget 기동과 정상 liquidity 차단은 이 문서에서 재검증하지 않는다. 새 PID 종료, restart loop, route drift, custody mismatch 또는 mandatory artifact 결손이 관측될 때만 별도 장애로 다시 연다. 과거 FAIL marker나 전일 generation만으로 장중 process를 재기동하지 않는다.

## 3. 장중 결손 집중 점검

### 3.1 P0 — exact-attempt submit 경로

전일 canonical handoff는 존재하지만 root cause는 `source_quality_blocked: exact_attempt_source_quality_gap`이었다. 오늘 새 entry attempt마다 다음 보존식을 확인한다.

`scanner promotion → machine decision → compact auxiliary(해당 시) → latency/price revalidation → final authority → broker submit/receipt/fill`

필수 확인:

- 같은 `attempt_id`, symbol, venue/session, cycle와 event time으로 각 단계를 연결한다.
- 최초 terminal, retry boundary, pending/submitted 수를 보존한다.
- `WAIT|DROP|BLOCK`과 source field 결손을 분리한다.
- accepted submit이 있으면 broker order key, receipt, fill과 terminal을 연결한다.
- accepted submit이 없으면 마지막 정상 차단과 누락 field를 정확히 분리한다.

완료 조건은 오늘 새 attempt에서 필수 source field가 채워지고 terminal까지 연결되거나, 최초 결손 producer·field·consumer가 특정되는 것이다. 한 건 submit이나 경보 해제만으로 drought 해소를 선언하지 않는다.

### 3.2 P0 — EOD eligibility 41개 결손

`data/runtime/update_kospi_status/update_kospi_2026-09-15.json`은 `requested=2673`, `received=2632`, `missing=41`, `status=completed_with_warnings`다. final detector warning의 직접 원인도 이 상태다.

필수 확인:

- 41개 코드가 상장폐지·관리용·비거래 코드인지, 정상 거래 가능 종목인지 official master와 대사한다.
- 오늘 scanner universe, promotion, watch 또는 주문 candidate에 포함돼야 했던 코드가 있는지 확인한다.
- 정상 거래 가능 코드가 누락됐다면 `ka10099` page/market identity, 저장 단계와 scanner consumer 중 최초 결손을 찾는다.
- 결손 코드가 모두 비거래 대상이면 false warning을 만드는 producer/status 계약을 보완 대상으로 분류한다.

누락 종목을 임의로 수동 추가하거나 scanner threshold를 완화하지 않는다. 완료 판정은 `benign_master_difference | active_symbol_source_gap | detector_contract_false_warning` 중 하나로 고정한다.

### 3.3 P0 — entry decision 3,508행 원천 계약

전일 source audit는 총 3,511행을 격리했다. 이 중 3,508행은 `scalp_entry_action_decision_snapshot`의 `minute_candle_window_fresh_contract` 결손이며, 별도로 holding 2행과 scale-in 1행의 `aftermarket_market_axes_contract` 결손이 있었다.

오늘 새 `scalp_entry_action_decision_snapshot` 행에서 다음을 점검한다.

- completed-bar window, 기준 시각, venue/session과 source age가 실제 값으로 기록되는지 확인한다.
- 정상 `not_evaluated`와 `invalid_label|unknown_token|source_quality_blocker`를 구분한다.
- 같은 runtime decision이 raw event와 source audit에서 다른 label로 투영되지 않는지 확인한다.
- 결손 행은 해당 row/window만 격리하고 정상 행까지 날짜 전체 차단하지 않는다.

첫 20개 새 decision 또는 10:30 KST 중 먼저 도래하는 시점에 중간 판정한다. 새 행에서 같은 결손이 1건이라도 재발하면 producer·schema·consumer를 결함 범위로 고정하고 source-only 최소 수리를 검토한다.

### 3.4 P1 — microstructure venue 충돌 64건

전일 `microstructure_diagnostic_handoff`에는 `evaluation_venue_missing_or_conflicting=64`가 남았다. 오늘 micro checkpoint가 생성된 symbol에 대해 다음 필드를 같은 event에서 확인한다.

- effective venue와 market session
- request symbol suffix와 실제 route
- stream epoch와 sequence
- signal time, checkpoint 0/1/3/5초와 fixed-price window completeness

`UNKNOWN`, KRX/NXT 충돌 또는 cross-epoch join은 유효 micro 표본으로 사용하지 않는다. 오늘 새 충돌이 없으면 전일 64건을 과거 결손으로 격리한다. 새 충돌이 있으면 최초 writer와 downstream evaluation 사이의 변환 지점을 특정한다.

### 3.5 P1 — 위젯·episode terminal pair 결손

전일 machine timing은 `baseline_immediate=true`였지만 `terminal_or_right_censored_gap`, `classification_evidence_incomplete`가 남았다. 모든 위젯·episode를 일반 점검하지 않고 오늘 자연 signal이 발생한 lifecycle만 확인한다.

필수 연결:

`signal → micro checkpoint → submit 또는 정상 미제출 → full/partial/no fill → target·보조익절 successor → terminal/custody → 비용`

- 자연 signal이 없으면 `no_natural_sample`로 종료한다.
- 미제출은 정확한 guard reason과 fresh source를 함께 보존한다.
- terminal 전이면 right-censored로 남기며 성공·실패 pair로 만들지 않는다.
- 보조익절 정체 전환과 목표가 1호가 상향을 서로 다른 action으로 기록한다.

삼성 오전의 08:00 liquidity 차단은 source age·route·best bid/ask qty가 정확히 기록된 정상 미제출 사례다. 이후 사례에서 source가 누락되거나 같은 snapshot으로 다른 판단이 나올 때만 결함으로 재개한다.

### 3.6 P2 — exact 비용 parent와 Pattern Lab propagation audit FAIL

`order_entry-prompt-revision-087251275cfaeb3c0da19f54`는 세 exact 비용 parent가 모두 `source_unavailable`이라 차단됐다. 오늘 새 자연 결과가 생긴 경우에만 parent/hash·비용·outcome을 확인한다. source가 없으면 새 prompt를 작성하거나 offline replay를 반복하지 않는다.

Pattern Lab은 currentness fail 6건, AI review workorder 4건과 `pattern_lab_propagation_audit_fail`이 있었지만 새 `implement_now`는 없었다. 오늘 fresh currentness 또는 AI review가 stable native ID, 구현 위치, 직접 consumer와 acceptance를 모두 발급할 때만 구현 검토 대상으로 올린다. 그 외에는 장중 필수 작업으로 실행하지 않는다.

## 4. 제외한 일반 점검

다음 항목은 이 문서의 필수 작업에서 제외한다.

- selector·cron·전체 systemd route·모든 PID의 반복 전수 점검
- 07:32 policy, 07:35 PREOPEN, 07:55 main 기동의 재검증
- 정상 OFF/retired family, sim/probe 전체 coverage와 Swing 상태 확인
- 알려진 low-price research quarantine 3건의 단순 재확인
- 후보 0건, 자연 signal 0건, liquidity·hard safety 정상 차단을 만들기 위한 재실행
- 모든 위젯·episode symbol의 신호·수익·정책을 표본 없이 전수 평가
- 전일 Pattern Lab propagation audit FAIL만을 이유로 한 producer 재실행
- 장기 EV, 전략 전체 재평가 또는 비용 결손을 0으로 채우는 계산

새 `FAIL`, PID 종료, duplicate order, custody mismatch, source writer 중단 또는 mandatory artifact 결손이 실제로 관측되면 이 제외보다 장애 대응을 우선한다.

## 5. 판정과 보고

각 항목은 다음 표로만 보고한다.

| 항목 | 오늘 새 표본 | 직접 결손 | 최초 owner | 영향 consumer | 판정 | 다음 조건 |
| --- | ---: | --- | --- | --- | --- | --- |
| exact-attempt submit | | | | | | |
| EOD eligibility 41 | | | | | | |
| entry decision contract | | | | | | |
| micro venue identity | | | | | | |
| widget·episode terminal pair | | | | | | |
| compact/exact 비용 parent | | | | | | |

판정값은 다음으로 제한한다.

- `closed_no_recurrence`: 오늘 새 원천에서 재발하지 않았고 직접 consumer까지 정상이다.
- `failed_reproduced`: 같은 결손이 새 원천에서 재현됐다.
- `source_gap_isolated`: producer·field·consumer를 특정했고 영향 row/window를 격리했다.
- `waiting_natural_sample`: 필요한 자연 event가 아직 없다.
- `historical_only`: 전일 결손이며 오늘 runtime 영향이 없다.
- `user_authority`: 수리에 주문·threshold·provider·bot·safety 권한이 필요하다.

보고 순서는 `판정 → 직접 증거 → 최초 결손 → 허용 조치 → 남은 종료 조건`이다. 코드 수리, 배포, PID 소비, 자연 action, 주문과 비용 차감 경제성을 각각 별도 상태로 유지한다.
