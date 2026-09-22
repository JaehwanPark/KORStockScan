# 장중 수익극대화 모니터링 작업지시문

역할: 현재 구현된 장중 매매 경로가 실제 PID에서 의도한 효과를 내는지 확인하고, 장후 튜닝에 필요한 원천과 identity가 끊기지 않도록 감시하는 실행 지시문이다. 날짜별 PID·commit·사건·완료 이력은 당일 체크리스트와 감사 보고서에 두며 이 문서에 누적하지 않는다.

문서 자동 현행화의 owner는 [서버 스케줄·API·게시 검증](./monitoring-instruction-refresh.md)이다. 문서 열람·인용·수정 요청은 장중 모니터링, 정책 변경, 재기동 또는 주문 실행 지시가 아니다.

공통 원칙과 active/observe/OFF·rollback은 [Plan Rebase §1–§8](./plan-korStockScanPerformanceOptimization.rebase.md), 실행할 OPEN ID·시각·Acceptance는 현재 KST의 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 [runbook](./time-based-operations-runbook.md), producer/consumer 연결은 [traceability](./report-based-automation-traceability.md)를 따른다. 서로 충돌하면 `contract_drift`로 fail-closed하며 과거 receipt나 mtime으로 현행 상태를 추정하지 않는다.

명시적으로 이 지시문에 따른 모니터링을 요청받으면 도래한 체크리스트 항목을 §4.1에 따라 점검하고, 확인된 source-quality·parser/schema·계측·report 결함은 §4.3과 §7의 허용 범위에서 최소 수리한다. 그 요청만으로 실주문, bot/widget/episode process 재기동, live env·정책·threshold·provider·수량·cap·broker/order/safety 변경 권한은 생기지 않는다.

## 1. 목표와 완료 기준

최종 목표는 **비용을 차감하고 작은 수익을 빈번하게** 얻어 누적 순이익과 EV를 높이는 것이다. 주문 수나 승률을 늘리는 것 자체가 목표는 아니다. 빠른 순수익, 낮은 역행, 짧은 횡보·자본점유와 tail 손실을 함께 평가한다.

장중 점검은 기능 존재보다 다음 인과가 실제로 닫혔는지를 우선한다.

`현재 PID의 exact-date 정책 소비 → scanner promotion → 기계판정 → ENTER_NOW의 축약형 AI 보조판정 → 기존 authority/가격/submit guard → 주문·체결 또는 직접 미제출 사유 → 1/3/5/10/20/30/60분 outcome → 장후 calibration 입력`

| 우선 | 확인할 질문 | 정상 근거 | 최초 결손 owner |
| --- | --- | --- | --- |
| 1 | 선택 release·당일 정책이 현재 PID와 해당 venue/session에 적용됐는가 | root/commit·env·bundle/prompt hash·resolver·자연 decision 일치 | release/PREOPEN/loader/runtime hook |
| 2 | 기계판정기가 실행 가능한 타점을 적시에 선별했는가 | exact attempt별 배타적 action과 당시 source/BBO/micro, 후행 action-neutral outcome | scanner 또는 machine input/decision |
| 3 | AI가 기계 ENTER_NOW만 보조하고 과도하게 막거나 근거 없이 통과시키지 않았는가 | request/response/fact binding·semantic terminal과 같은 attempt의 후행 outcome | compact AI input/transport/semantic owner |
| 4 | PASS가 기존 guard와 제출 경로로 정확히 전달됐는가 | authority·가격·latency·유동성·broker terminal의 단일 최초 사유 | final authority/entry-price/submit/broker |
| 5 | 위젯·에피소드와 시장약세 차단이 각 owner 계약대로 작동하는가 | 시장별 입력 freshness·차단 receipt와 signal/order/custody lineage | market regime/widget/episode owner |
| 6 | 장후가 결손 없는 자료로 다음 정책을 만들 수 있는가 | decision→outcome→cost→calibration의 exact identity와 source hash | collector/writer/join/postclose consumer |

완료 상태는 다음을 분리한다.

- `runtime_operating`: 정책·PID·자연 decision·terminal 연결이 정상이다.
- `effect_pending_maturity`: 경로는 정상이나 필요한 후행 horizon 또는 terminal이 아직 성숙하지 않았다.
- `effect_evaluable`: executable outcome과 비용이 결속되어 적정·늦음·놓침을 비교할 수 있다.
- `defect_or_gap`: source, identity, semantic, consumer 또는 runtime 연결의 최초 결손이 확인됐다.
- `economic_candidate`: 동일 조건 반사실에서 현재 정책보다 비용 차감 EV·빈도·tail·자본효율 개선 가능성이 확인됐다.

코드 수리, 배포, 현재 PID 소비, 자연 표본, 정책 선택과 경제성은 각각 별도 상태다. 한 단계의 PASS로 다음 단계를 완료 처리하지 않는다.

## 2. 집중 모니터링 범위

### 2.1 메인 봇 매매기계

#### 2.1.1 기계 주판정과 축약형 AI 보조판정

현재 진입 decision owner는 기계판정기다. 지원 연속매매 KRX/NXT/SOR scope에서 기존 감시 평가의 같은 attempt 안에 다음 계약을 적용한다. 동시호가·시간외 단일가, widget, episode로 자동 확대하지 않는다.

1. 기계판정기는 `BLOCK|RECHECK|ENTER_NOW|source_invalid` 중 하나를 낸다.
2. `BLOCK|RECHECK`는 AI Provider를 호출하지 않으며 AI가 이를 승격할 수 없다.
3. `ENTER_NOW`만 축약형 AI 보조판정기로 간다.
4. AI `PASS`만 기존 authority·가격·latency·유동성·broker guard로 진행한다.
5. `VETO`는 해당 타점을 차단한다. `CAUTION|INSUFFICIENT`와 local/transport 미평가는 무노출 WAIT 후 fresh 다음 평가 대상으로 남긴다.
6. AI PASS, probe intent 또는 budget pass는 주문·체결이 아니다. 최종 guard와 broker terminal을 같은 attempt로 확인한다.

현재 PID에서 아래가 모두 일치해야 runtime 소비를 인정한다.

- 해당 소비자에 승인된 release root/commit과 PID root/commit. 장후 생산자만 갱신된 경우 공통 release selector와 기존 메인 PID의 commit 차이를 곧바로 소비 실패로 판정하지 않는다
- target date, source date, policy bundle hash와 selected scope/rule
- `entry_primary_decision_owner=mechanistic_entry_adjudicator`
- `entry_ai_role=auxiliary_risk_screen_pass_veto_no_promotion`
- compact prompt/schema/system prompt hash
- resolver 결과와 자연 trace의 owner/action/prompt/bundle

문자열 status, 정책 파일 존재, PREOPEN verifier PASS만으로 현재 PID 소비를 인정하지 않는다. 정책 묶음 소비와 변경된 구간·선택 규칙·실제 임계치 소비를 구분한다. 과거 판정은 당시 bundle로 검증하며 현재 임계치를 소급하지 않는다. 유효 부모 정책과 선택된 그룹·종목·micro 자식 정책을 분리하며, 자식 표본 부족을 부모 정책 부재나 추가 live 진입 gate로 만들지 않는다.

판정 분모의 canonical key는 다음과 같다.

`scanner_promotion_id × evaluation_attempt_id × symbol × venue × session × policy_bundle_hash`

scope별로 다음 보존식을 닫는다.

```text
evaluated = ENTER_NOW + RECHECK + BLOCK + source_invalid
ENTER_NOW = AI screen attempt = AI terminal
AI PASS = submitted + final_guard_blocked + broker_rejected + pending
```

AI raw verdict `PASS|VETO|CAUTION|INSUFFICIENT`와 screen terminal status `pass|veto|caution|insufficient|response_invalid|not_evaluated_transport|not_evaluated_local|not_requested_machine_nonentry`를 분리한다. semantic rejection·transport/timeout·local unavailable을 VETO나 정상 WAIT로 덮지 않는다. request/response/trace/snapshot·prompt/payload/response hash, provider/model/latency/parse와 dynamic fact binding을 연결한다.

#### 2.1.2 판정 정확도와 놓친 기회

`ENTER_NOW 0건`이나 낮은 비율만으로 gate가 과도하다고 결론내리지 않는다. 반대로 process와 보존식이 정상이라는 이유로 수익기회를 잘 선별했다고 결론내리지 않는다. 판정 시점에 이용 가능했던 입력과 이후 action-neutral outcome을 같은 attempt로 비교한다.

각 attempt에 다음을 남긴다.

- symbol, 유사 흐름 group, venue/session, bundle/parent/selected rule
- 추세 시작은 원천이 있을 때의 사후 진단값으로만 기록
- 최초 시장 source/fetch, 최초 감시, promotion, 기계판정, AI, final guard, submit, fill 시각과 구간별 gap
- 판정 당시 executable BBO·spread·depth·quote age, 가격/거래량/속도/분봉/수급과 사용된 micro feature
- action/reason, 임계치와 결손·위험 상쇄 근거
- 1·3·5·10·20·30·60분 fill feasibility, target/adverse first-hit, 비용 차감 MFE/MAE, terminal/censored

사례는 다음처럼 배타적으로 분류한다.

| 분류 | 핵심 기준 |
| --- | --- |
| 좋은 타점 | 실행 가능했고 짧은 시간 안에 총비용을 넘는 양수 순익에 도달하며 역행·점유가 제한됨 |
| 늦은 타점 | 상승 episode를 감시·판정보다 상당히 늦게 따라가 기대 잔여폭·체결품질이 악화됨 |
| 놓친 타점 | RECHECK/BLOCK/VETO 또는 후단 차단 뒤 같은 조건의 실행 가능한 비용 후 양수 기회가 성숙함 |
| 과제출 후보 | ENTER_NOW/PASS 뒤 adverse-first·tail loss·비경제적 횡보가 반복됨 |
| 적정 차단 | 차단 뒤 비용 후 기회가 없거나 adverse/tail 위험이 우세함 |
| 미성숙/결손 | horizon, executable BBO, identity, cost 또는 terminal이 없어 판정 불가 |

익절했더라도 깊은 역행이나 장시간 횡보 뒤 회복한 사례는 좋은 타점으로 세지 않는다. 손절선·청산 override 때문에 실현 EV가 왜곡된 경우 타점 품질과 exit 결과를 분리한다. 미래 first-hit·사후 고가를 당시 feature에 역류시키거나 체결을 합성하지 않는다.

임계치 변경 시뮬레이션은 성숙한 동일 attempt 집합에서만 수행한다. incumbent와 후보가 같은 source-quality, 비용, venue/session, chronological holdout과 tail 계약을 사용해야 한다. 후보 선정 기준은 해당 family의 현재 승인된 계약을 따른다. 메인 기계 BLOCK/RECHECK→ENTER_NOW 튜닝은 사용자 승인된 `support_adjusted_win_rate_preserve_entries_v3`를 사용하며 표본 보정 승률, 평균 순 경로 EV 순으로 비교하고 음수 EV도 허용한다. 기계 튜닝에 AI/자금/청산 재생 또는 `+0.10%` 수익 하한을 추가하지 않는다. 다른 family의 비용·paired 개선·tail 계약은 별도로 유지한다. source/identity 결함 수리에도 경제성 floor를 추가하지 않는다.

#### 2.1.3 탐색부터 제출까지의 최초 병목

기계판정 정확도 분모에 도달하지 못한 상승기회는 scanner 결손으로 분리한다. 공식 보통주 master에 결속된 독립 `as_of rising benchmark`와 후행 `ex_post executable opportunity`를 사용해 다음 흐름의 최초 미도달 지점을 찾는다.

`독립 기회 → source fetch/normalize → candidate rank/limit → eligibility → watch slot → promotion → runtime attach → fast/heavy evaluation → 기계 action → AI screen → authority/price/submit guard → broker`

최초 감시→기계, 기계 ENTER_NOW→AI, AI PASS→submit/fill을 분리한다. “감시→AI”를 추세 시작→진입 전체 지연으로 해석하지 않는다. benchmark가 없으면 scanner recall을 정상으로 판정하지 말고 `insufficient_evidence_scanner_recall`로 남긴다.

submit drought는 `UPSTREAM_GATE|LATENCY_PRE_SUBMIT|ENTRY_AI_AUTHORITY_REVALIDATION|PRICE_REVALIDATION|BROKER_RECEIPT`를 동일 attempt의 최초 terminal로 분리한다. 정상 기계 BLOCK/RECHECK, AI VETO, 후단 safety block을 중복 차단으로 세지 않는다. 한 건 제출이나 경보 해제로 drought 해소·경제성 개선을 확정하지 않는다.

#### 2.1.4 장후 튜닝 입력 준비

장중 source chain은 다음 identity를 보존해야 한다.

`raw promotion → watch/runtime attach → machine capture → compact AI request/response/trace → final guard/order/broker → action-neutral horizon outcome → terminal/cost → calibration`

각 단계에서 target date, promotion/attempt, symbol, venue/session, policy/prompt/source hash, event time을 보존한다. raw 행 수나 파일 크기를 유효 경제 표본으로 세지 않는다. 다음 funnel의 최초 0을 찾는다.

`captured → source-quality-valid → identity-bound → mature outcome → lifecycle terminal → effective cost-bound → net-economic eligible`

장후 owner는 기존 `ai_action_outcome_calibration`과 연결된 기계 threshold·compact prompt optimizer/consumer, dated policy publisher, PREOPEN resolver다. 장중에는 입력의 생성·결속과 예정 handoff를 점검하고 무거운 장후 producer를 조기 실행하지 않는다. 새 후보가 없더라도 유효 incumbent 유지 경로를 차단하지 않으며, 초기 정책 사용에 challenger의 표본 floor를 다시 요구하지 않는다.

### 2.2 시장약세·위젯·에피소드 매매기계

시장약세 판정기는 KOSPI/KOSDAQ별 widget/episode 신규 매매를 실제 차단하는 runtime guard다. 단순 참고지표로 취급하지 않는다. 다음을 확인한다.

- 시장별 source timestamp/hash·freshness, 계산 window와 canonical state
- symbol의 시장 매핑, venue/session과 적용 policy hash
- 약세 전환 시 신규 entry block receipt와 비약세 복귀 시 정상 해제 receipt
- 이미 보유한 position의 custody·target/exit가 신규 entry block과 혼동되지 않았는지
- stale/UNKNOWN/source gap이 계약대로 fail-closed됐으며 임의의 다른 시장 값으로 대체되지 않았는지
- 동일 signal에서 market guard와 다른 guard의 최초 차단 owner가 중복 집계되지 않았는지

위젯 흐름은 다음과 같다.

`signal → source-quality/policy → market weakness/global safety → episode lock → entry order/fill → target → terminal/custody`

에피소드 흐름은 다음과 같다.

`exact-date profile/승인 override → preflight/timer → leg별 submit/fill → target → COMPLETE|NO_TRADE|HELD|BLOCKED → custody reconciliation`

공통 확인 항목:

- service/timer·WorkingDirectory/ExecStart와 실제 PID/code generation, policy/profile hash. 위젯 auto-trader는 startup receipt의 `release_root`와 같은 PID의 systemd `WorkingDirectory`가 일치해야 하며, 08:05 이후 `unit_process_release_mismatch`는 runtime incident로 판정한다.
- signal·episode·leg·order ID와 symbol/venue/session의 exact lineage
- 중복 episode, partial fill, 취소·재제출, target과 잔여 수량의 owner 정합성
- main/widget/episode/manual 보유와 주문을 합치거나 대신 매도하지 않았는지
- `HELD`, right-censored, 미체결, source gap을 완료/손익 0으로 바꾸지 않았는지
- 비용 차감 EV, 목표 완료시간, adverse/sideways, tail, 자본점유와 반복 가능성
- 승인된 보조청산이 있으면 신규 entry 범위·policy pin·원 target 취소확정→보호 주문→TTL/부분체결 잔량 원복과 terminal 정산

widget/episode의 signal, micro confirmation, entry price/target, holding/exit를 한 변경 효과로 합치지 않는다. 매도잔량 감소속도는 실제 매수체결 설명·refill·bid 지지·가격반응과 함께 평가하며 단독 BUY 근거로 쓰지 않는다. source-only 연구·recommendation·catalog refresh·timer start는 live 적용이나 경제성 성공이 아니다.

### 2.3 원천·운영 건전성

효과 판정을 무효화할 수 있는 다음 항목만 집중 확인한다.

- Kiwoom REST/WS LOGIN·REG, required realtime type, route/epoch, first data, freshness, reconnect/resubscribe, queue/drop/writer/disk
- 분봉은 완성봉만 사용하고 BBO·0B/0D·체결은 동일 symbol/venue/session/epoch로 결속
- broker 잔고·미체결·주문가능금액과 owner별 ledger/custody reconciliation
- main/widget/episode process의 PID·heartbeat·중복·restart-loop와 실제 consumer
- clean baseline 이전 자료, real/sim/probe, full/partial fill, completed/HELD/censored의 혼입 여부
- source-quality preflight와 `raw_row_exclusion`; 식별 가능한 결손은 행/창만 제외하고 전체 날짜 차단은 전역 계약 결손 또는 격리 실패에 한정
- OFF/retired producer의 runtime 권한 누출·자원 간섭. 누출이 없으면 세부 성과 연구를 다시 열지 않음

대용량 장중 원천은 먼저 `stat`으로 크기와 증가 여부를 확인한다. 64MiB를 넘거나 writer가 계속 쓰는 파일은 전체 scan하지 않고 기존 요약·인덱스 또는 최대 16MiB tail만 읽는다. 진단 I/O pressure가 커지면 중단하고 원천 writer나 safety/resource guard를 완화하지 않는다.

## 3. 관찰 시점과 반복 기준

당일 체크리스트의 실제 `TimeWindow`가 우선이다. 아래는 별도 cron이나 owner를 만들지 않는 기본 관찰 경계다.

| 경계 | 집중 점검 | 아직 완료로 만들지 않을 상태 |
| --- | --- | --- |
| PREOPEN/기동 직후 | release→policy/env→resolver→PID, 시장약세·widget/episode policy/preflight | policy 파일이나 PID만 존재 |
| 연속매매 재개 후 첫 15분 | 첫 자연 machine action, ENTER_NOW의 AI terminal, final guard와 supported scope | 자연 대상 없음 또는 expected market quiet |
| 장중 중간 점검 | 성숙한 1/3/5/10/20/30/60분 사례표, 최초 감시·판정·submit 지연, source chain | 최근 attempt의 미성숙 horizon |
| KRX 마감 전후 | 정규장 false-negative/false-positive, 주문·custody·시장약세 block/해제 | 미종결 주문·HELD를 완료 처리 |
| 지원 연속매매 종료 전 | KRX/NXT/SOR별 전체 분모, late-session outcome과 장후 저장/join 준비 | venue/session을 합산하거나 장후 producer 조기 실행 |

지속 모니터링은 상태 변화·slot 경계·horizon 성숙 때 다시 점검한다. 같은 상태가 길어지면 최대 60초 간격으로 현재 단계, 대기 사유와 다음 확인 조건을 알린다. 중복 Provider 호출이나 worker 실행으로 표본을 만들지 않는다.

## 4. 실행 절차

### 4.1 모니터링 시점 체크리스트 실행·점검

1. 현재 KST 체크리스트의 목적·강제 규칙과 모든 OPEN을 읽는다. 자정 이후라면 원 target date의 미종결 owner를 함께 대사한다.
2. ID별 `Due/Slot/TimeWindow`, Source/Acceptance, 선행 조건, 권한, 최신 receipt, 현재 상태와 다음 확인 시각을 기록한다.
3. 미래는 `not_yet_due`, 정상 선행 대기는 `waiting`, 진행 중은 `running`, 도래했으나 미확인은 `overdue_unresolved`, 권한·증거 결손은 `user_authority|blocked_missing_evidence|external_dependency`로 분리한다.
4. 허용되고 due인 점검·source-only 수리만 실행한다. 미래 producer, 진행 중 producer, Provider replay와 장후 heavy producer를 앞당기거나 중복 실행하지 않는다.
5. 전체 Acceptance가 충족된 항목만 완료한다. 같은 stable ID를 재사용하고 과거 완료 ID를 새 OPEN으로 복제하지 않는다.
6. 단회 요청은 as-of snapshot과 남은 조건을 보고하고, 지속 요청은 지정 종료조건까지 갱신한다.

### 4.2 현재 owner·원천 공통 확인

다음 순서로 최소 증거를 확인한다.

1. release selector, PREOPEN apply/verify와 현재 PID root/commit/env/policy 소비
2. broker inventory·미체결·custody와 hard safety
3. supported scope별 promotion→machine→AI→final guard/submit의 exact 보존식
4. 시장약세·widget/episode의 실제 service/policy/signal/block/order terminal
5. WS/source-quality/writer/disk와 장후 calibration identity 준비
6. mature outcome 사례표와 threshold/prompt 반사실 후보

process 이름이나 exit 0만으로 정상이라고 하지 않는다. `owner → installed trigger → expected window → PID/terminal → artifact 또는 valid-empty → registered consumer → consumed field`를 연결한다. artifact를 계속 만들지만 consumer가 없으면 `orphan_producer|unconsumed_artifact`, 성공 exit인데 필수 산출물·consumer receipt가 없으면 `no_op_success`다.

### 4.2.1 동시호가·NXT 휴장 구간의 수신 기대

정상 평일 `08:50~09:00 KST`의 연속매매 0B/0D 무수신과 age 증가는 단독 subscription 장애가 아니다. 명시적으로 확인된 NXT-only route는 `09:00:30`까지 `expected_market_quiet`로 분리한다.

- LOGIN/REG ACK 오류, 미등록, route 불일치, queue/drop·writer/disk/parser 실패는 quiet로 덮지 않는다.
- stale/price/broker guard는 유지하며 과거 호가를 fresh 실행 자료로 승격하지 않는다.
- KRX 09:00, NXT-only 09:00:30 이후 first-data와 기존 freshness SLA를 다시 확인한다.
- quiet marker는 원래 event 시각과 route를 기준으로 판단하며 장후 as-of로 과거 상태를 바꾸지 않는다.
- 이 예외에서 REMOVE/REG, 재연결, process 재기동 권한을 추론하지 않는다.

### 4.3 장중 수집 결손 즉시 대응

실제 signal/attempt/episode가 있는데 필요한 원천이나 downstream join이 끊겼으면 장후까지 기다리지 않고 다음 순서로 처리한다.

1. target date/as-of, owner/symbol/venue/session, promotion·attempt·episode ID, PID/code/config, 마지막 정상 receipt와 최초 실패를 고정한다.
2. `대상 선정/REG → REST/WS 수신 → callback → queue/worker → writer → parser/projection → exact join → intended consumer`에서 최초 단절을 찾는다.
3. 원천 미수집, parser/schema·identity 유실, consumer/handoff 결함, 외부 제한·권한 결손을 분리한다.
4. 허용된 source-only 결함은 최소 수정하고 review/fix/re-review와 targeted validation을 finding 0까지 반복한다.
5. 실제 process 반영·재기동·live 설정 변경은 별도 권한을 확인한다. 권한이 없으면 `code_review_closed / deployment_pending`으로 분리한다.
6. 새 자연 receipt가 같은 identity/hash로 저장되고 직접 consumer까지 도달했는지 확인한다. 과거 미수집 tick이나 체결시각은 합성하지 않는다.

Kiwoom request/parser/FID/REG·재연결을 수정할 때는 [공식 API reference gate](./kiwoom-api-data-contract.md)를 먼저 적용한다. 호출량·retry·동시성 상향, source-only budget 침해나 safety 완화로 복구하지 않는다.

## 5. 당일 runtime과 효과 판정

| 상태 | 판정 기준 |
| --- | --- |
| `effect_observed_pending_maturity` | current PID와 exact bundle, 자연 machine→AI→final terminal은 정상이고 outcome만 미성숙 |
| `effect_observed_cost_evaluable` | executable outcome·terminal·비용이 결속되어 좋은/늦은/놓친 타점을 비교 가능 |
| `policy_present_effect_unverified` | 정책은 있으나 PID 소비·자연 action·직접 consumer 중 하나가 없음 |
| `on_no_natural_sample` | loader/PID/source-quality는 정상이나 해당 scope에 자연 대상이 없음 |
| `decision_or_conversion_gap` | machine input/action, AI terminal, final guard, submit/broker 중 최초 연결이 끊김 |
| `economic_quality_candidate` | 같은 attempt의 후행값에서 과차단·과제출·지연·tail 또는 자본점유 문제가 반복됨 |
| `deployment_or_authority_gap` | 구현은 있으나 선택 release/PID/process/policy에 미반영 또는 source-only |
| `runtime_incident` | dead/hung/restart-loop/duplicate/no-op/orphan/contract drift가 실제 consumer에 영향 |
| `not_applicable_or_waiting` | OFF/retired/valid-empty/not_yet_due/bounded wait |

blocked 사유는 `source_quality|identity_projection|env_mapping|runtime_hook|AI_semantic|post_promotion_handoff|submit_drought|market_regime|widget_episode_custody|postclose_calibration|safety_or_broker_guard|external_dependency|user_authority` 중 최초 owner로 기록한다.

정상작동 판정은 다음 세 층을 모두 별도 보고한다.

- 기능: runtime과 보존식이 정상인가.
- 판단: 후행 outcome을 기준으로 false-negative/false-positive와 timing이 합리적인가.
- 경제성: 비용 후 양수 EV·작은 순익 빈도·tail·자본효율이 개선됐는가.

## 6. 표본 부족과 과도한 gate 판정

표본 0이나 floor 미달을 단순히 기다림으로 끝내지 않는다. 다음 funnel의 최초 고갈을 stable `shortage_id`로 기록한다.

`raw opportunity → source-quality-valid → policy matched → runtime evaluated → machine action → AI screened(ENTER_NOW만) → submit/fill → mature/terminal → net-economic`

- 신규 unique 표본이 선언 horizon 안에 유입될 근거가 있으면 `time_resolvable_shortage`다.
- key/policy mismatch, join/exclusion 오류, missing hook/consumer, 계약상 최대 가능 수가 floor 미만이면 `structural_population_exhaustion`이다.
- 필요한 census/window가 없으면 `blocked_missing_evidence`, 최초 관찰창 전이면 `pending_declared_window`다.
- OFF/retired/비우선 family의 0건은 `not_applicable_retired_or_deprioritized`다.

gate의 과도함은 action count가 아니라 성숙 outcome으로 판정한다. RECHECK/BLOCK/VETO 뒤 실행 가능한 비용 후 양수 기회의 비율·크기·도달시간과, ENTER_NOW/PASS 뒤 adverse-first·tail·비경제적 횡보를 함께 비교한다. 표본을 맞추기 위한 row 복제, venue/session/owner 병합, censored의 completed 변환, pre-baseline 자료 재사용, sample floor 하향이나 hard safety 완화는 금지한다.

## 7. 보완·권한·검증 원칙

결함은 다음 루프로 닫는다.

`최초 원인 → 단일 owner·권한 → 최소 보완 → self review → 수정 → 재리뷰 → targeted validation → 직접 consumer → 배포/PID → 자연·경제성`

코드·문서 변경에는 `$korstockscan-review-gate`를 적용한다. Python은 관련 pytest와 compile, shell은 `bash -n`과 wrapper 계약, 문서는 owner·link·authority와 print-only parser, 모든 변경은 `git diff --check`를 확인한다.

허용 범위:

- source-quality, parser/schema, identity projection, writer/report/test/instrumentation의 최소 보완
- 현재 승인 정책의 기존 handoff/consumer 결함 보완
- 수정과 직접 관련된 source-only producer·consumer의 bounded validation

일반 모니터링에서 금지되는 범위:

- 실주문·취소, 수량·가격·target·cap·cooldown과 broker/account/order guard 변경
- live threshold/prompt/provider/model/route/env/operator lock 수동 변경
- bot/widget/episode process 기동·종료·재기동
- stale/conflict·price freshness·hard/protect/emergency safety 완화
- source-only/sim 결과를 실주문 권한으로 전환

사용자가 별도로 배포·재기동을 승인한 경우에도 review finding 0과 targeted validation 뒤에만 수행하고, 전후 release/PID/env, broker 미체결·전시장 inventory, WS first-data, 중복주문 0을 확인한다. 현재 PID에 반영되지 않은 코드를 런타임 정상화로 보고하지 않는다.

문서/checklist 변경 후에는 다음 print-only parser만 실행한다. Project/Calendar 외부 sync와 token 검사는 실행하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 8. 보고 형식

항상 `판정 → 근거 → 다음 액션` 순서로 간결하게 보고한다.

1. `Intraday Control State: 진행 중|GREEN|YELLOW|RED`, target date와 as-of KST
2. 체크리스트 OPEN 전수 분류와 미분류 0건
3. release/PREOPEN/PID와 exact policy·bundle·prompt·scope 소비
4. scope별 machine `ENTER_NOW|RECHECK|BLOCK|source_invalid` 및 AI terminal 보존식
5. scanner→machine→AI→final guard→submit/broker의 최초 결손과 지연
6. 성숙 사례의 좋은 타점·늦은 타점·놓친 타점·과제출·적정 차단·미성숙 표
7. 시장약세, widget/episode signal·block·order·terminal·custody 상태
8. source/identity/outcome/cost→장후 calibration handoff와 다음 확인 시각
9. 수정·review finding·targeted validation·배포/PID 반영을 각각 분리
10. 남은 source warning, external dependency, user authority와 경제성 acceptance

최종 색상은 다음과 같다.

- `GREEN`: due 필수 owner의 runtime·source chain이 정상이며 현재 성숙한 범위에서 미해결 결함이 없다. 경제적 장기 개선을 자동 의미하지 않는다.
- `YELLOW`: runtime은 정상이나 outcome 미성숙, 자연 무표본, source-only warning, 다음 장후/PREOPEN 확인 또는 경제성 acceptance가 남는다.
- `RED`: due 필수 owner의 runtime/identity/source/consumer 결함, 확정 hang, custody·safety 문제 또는 허용된 actionable 수리 누락이 있다.
- `진행 중`: 정상 running/waiting 또는 예정된 필수 장중 owner가 아직 남아 있다.

정책 preview·코드 구현·배포·PID 소비·자연 판정·주문·비용 차감 경제성은 끝까지 서로 다른 상태로 유지한다.
