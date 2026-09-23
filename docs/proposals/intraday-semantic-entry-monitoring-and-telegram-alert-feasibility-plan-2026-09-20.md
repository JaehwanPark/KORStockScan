# 장중 제출병목 감시와 Telegram 통보

작성·범위 재확정: 2026-09-20. 사용자 후속 지시로 **메인 정상 제출 경로의 지속 병목·원천 결손**만 구현한다. 이전의 포괄적 의미 감시·EV 후처리 제안은 이번 구현 범위에서 제외한다. 위젯/에피소드, 보유/청산, 프로그램 예외는 기존 owner가 유지한다.

## 목적과 권한

기계 ENTER_NOW → compact AI → 최종 guard → 주문 owner/broker 응답을 관찰하여 사용자에게 Codex 점검 근거를 전달한다. AI VETO 또는 ENTER 부족만으로 오판·놓친 이익을 확정하지 않는다. 자동 수정·매매 판정·threshold/수량/budget/guard 변경·주문·AI/계좌 호출·서비스 시작은 하지 않는다. 실제 broker 응답은 제출 증거이며 체결·완료 손익이 아니다.

운영 기준은 기존 [메인 경제성 계획 §15](./main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md#15-변동-자본부분-체결미호출-ai의-지원-범위-보완계획)와 [장후 통합 준비 계획](./postclose-integrated-verification-recovery-and-next-preopen-readiness-plan-2026-09-20.md)이다. 이 감시는 경제성 평가나 PREOPEN의 승인자가 아니다.

## 기존 producer·consumer 통합

- `buy_funnel_sentinel`이 이미 읽은 cache/summary의 동일 events와 `_machine_primary_entry_funnel` identity/terminal 계약을 재사용한다. 새 raw parser·collector·DB·상주 서비스는 없다.
- 기존 전체 진단 JSON/MD consumer는 유지한다. 추가 계산은 최근45분 events의 exact ledger 한 번이다. 기존 전체일/baseline 집계 비용을 추가로 반복하지 않는다.
- 같은 Sentinel producer가 `data/report/buy_funnel_sentinel/submission_bottleneck_source_<date>.json`을 atomic 발행한다. 알림 consumer는 68MB급 전체 진단 보고서를 다시 읽지 않고 8MiB 상한의 작은 투영만 읽는다.
- 새 파일 `src/engine/monitoring/submission_bottleneck_monitor.py`는 감시/알림 consumer 소유이므로 기존 monitoring package에 둔다. engine root 새 모듈이나 중복 장후 producer를 만들지 않는다.
- 기존 Telegram transport/config helper만 재사용하고 error detector의 상태·중복 억제는 건드리지 않는다. 별도 state lock과 발송 성공 후 acknowledged 상태를 저장한다. 전송 실패는 토큰을 기록하지 않고 예외 종류와 retry 상태를 남긴다.

## 판정 계약

| 항목 | 구현 | 판정/해제 |
| --- | --- | --- |
| ENTER 부족 | 최근30분 유효 고유 promotion 10개 이상, ENTER0; 15분 지속 + 새 promotion 유입 | `review_required`. 기계 결함/경제적 손실 단정 금지 |
| VETO 집중 | 고유 ENTER promotion10개 이상, VETO/ENTER≥90%, 제출 응답0; 15분 지속 + 새 promotion | `review_required`. transport/미호출을 VETO로 계산하지 않음 |
| 원천/제출 연결 | exact attempt의 conflict/source-invalid/불명확 dispatch/미종결 PASS를 최초 평가10분 뒤 관찰하고 4분 이상 지속 확인 | `structural_evidence`는 관측 계약 결손 증거이며 실행 코드 원인 확정은 Codex 조사. 정상 guard/명시 거절은 미종결 아님 |
| identity 결손 | 최근10분 기계 원천 이벤트의 필수 identity 부재를 다음 정기 실행에서 즉시 확인(별도 유예·지속 없음) | 분모를 추정하지 않고 unbound 원천 hash를 보존 |

수치는 **진단 알림의 초기값**이며 튜닝으로 검증된 최적치나 매매 gate가 아니다. WINDOW/GRACE/PERSIST/MIN_PROMOTIONS는 모듈 한 곳에서 관리한다.

- venue/session/policy hash별 분리; promotion×symbol 중복 제거. 반복 RECHECK를 새 독립 기회로 세지 않는다. 정상 BLOCK/RECHECK의 `not_requested_machine_nonentry`와 ENTER의 실제 screen을 구분한다.
- 최초 평가 clock와 최신 terminal을 함께 보존한다. 늦은 제출/guard/거절은 같은 exact attempt의 미종결을 닫는다. 윈도우 밖으로 사라짐·정책 교체·분모 없음은 복구 증거가 아니다.
- 입력 date가 현재 KST와 다름, dry-run, 생성 후7분 초과, 최근 event10분 초과, 역행/중복 snapshot은 `unobservable`이며 새 경보/복구를 만들지 않는다. 멈춘 봇·원천 freshness는 기존 error detector owner가 담당한다.
- source-invalid는 해당 promotion을 정상 판단 비율 분모에서 제외한다. 유효 scope는 계속 관찰한다. 결손을 0 EV/no-edge로 바꾸지 않는다.
- 미결 사건은 날짜별 상태에 남는다. 구조 결손은 저장한 exact attempt가 명시 terminal로 닫힐 때만 복구; 비율 경보는 새로운 실제 제출 응답으로 복구한다. 옛 identity 부재는 건강한 새 이벤트만으로 과거 복구라고 선언하지 않는다.
- identity 표시 보완(9/21 승인): 최근10분 신규 기계 이벤트의 결손은 `current_gap`, 정상 식별 이벤트만 관측되면 `no_recurrence_observed`, 표본 없음/입력 stale·legacy recency 부재는 `unobservable`로 분리한다. 9/22 알림 보완 승인으로 identity 결손에만 유예·지속 기준을 제거한다. 기존 5분 정기 실행·통보 cooldown은 유지한다. 과거 사건은 `historical_unresolved`로 수량·해시·사례를 보존하며 복구로 표시하지 않는다. 신규 결손이 재발하면 이전 사건을 history에 보존하고 active 알림을 다시 허용한다.
- 발생시각 범위·종목·누락 필드는 exact identity owner의 같은 alias 규칙에서 산출한다. 구형 사건은 이미 읽힌 당일 cache의 최근 과거 표본 최대128개 중 저장 hash와 일치한 것만 보충하며 원시 로그 추가 스캔·과거 분모 재계산은 하지 않는다. 불완전한 범위/표본은 미확인으로 표시한다. Telegram은 신규 active/재발만 점검 요청으로 보내고 이벤트 수≠주문 수를 명시한다. 현재 사례·시각을 우선 표시한다. historical_unresolved만 남은 사건(정책 영수증 사건 포함)은 보고서에 보존하고 통보하지 않는다. 이전 active 통보가 성공한 identity 사건에 정상 식별 이벤트가 새로 확인되면 정상 관측 안내를 한 번만 보낸다. stale/무표본은 정상 증거가 아니며 통보 실패·cooldown은 성공 전까지 재시도한다. 정상 안내에는 추가 점검 요청을 붙이지 않으며 과거 원천 복구라고 표현하지 않는다. 기존 historical 상태의 배포 전환 알림은 만들지 않는다.

## 실행·알림·보존

기존 Buy Funnel Sentinel cron 5개를 **평일 08–19시 매5분 1개**로 대체한다. `run_runtime_release.sh buy-funnel <date>`가 선택 immutable release의 기존 wrapper를 실행한다. 다른 cron/거래 기동·주문 인자는 유지한다. 설치는 예약만 바꾸며 지금 봇/감시를 시작하지 않는다. 세션 밖/휴장/봇 중지는 관측 원천 없이 이상 비율을 만들지 않는다.

wrapper의 lock/cooldown 안에서 Sentinel 성공 후 compact source consumer를 호출한다. dry-run은 통보하지 않는다. 기존 error detector는 Sentinel 생성 실패/MD stale 감시를 유지한다. 기존 artifact freshness detector에 날짜별 감시 JSON(08:10–20:00, 최대10분 stale)과 notification_status를 등록한다. 소비자 실패/통보 실패는 기존 기술 에러 경로가 맡고, unobservable 자체는 매매 결함으로 승격하지 않는다.

- 출력: `tmp/submission_bottleneck_monitor_state.json`, 같은 report 디렉터리의 `submission_bottleneck_monitor_latest.json`과 날짜별 JSON. 매 tick 중복 raw/상세 보고서를 추가로 누적하지 않는다.
- Telegram: 활성/명시 복구의 상태 전이만 보낸다. scope·rule·근거 수·최대3개 사례·owner·closure test는 산출물에 남기고 메시지는 대표 사례/경로를 포함한다. 5분 global cooldown, 발송당 최대4개 사건, 실패시 다음 tick 재시도. 별도 시험 경보는 실채널로 보내지 않는다.
- 봇의 예외, 가격 수집 장애, 모든 scanner 누락, 관측되지 않은 AI 판정, 계좌 반사실 손익을 이 감시가 전부 탐지한다고 주장하지 않는다. 정상 guard만으로 막힌 상태는 집계로 남기고 자동 결함 경보는 억제한다.

## 검증·종결

운영 pipeline payload 저장→cache 정규화→existing exact ledger→최근 투영→지속성→Telegram mock→상태 저장을 검증한다. 프리마켓, 정상 guard, PASS 미종결/늦은 terminal, VETO/ENTER 분모, 재평가 중복, policy 분리, stale/date/dry-run, 전송 실패/중복/cooldown, wrapper 실행과 release routing이 영향 회귀 범위다.

경제성 코드는 직전 5d60b4afe의 지원 범위/검증을 대사하고 새 결함이 없으면 재구현하지 않는다. 모델·producer·policy hash가 동일한 기존 자연 평가를 이번 감시 변경의 새 경제적 성과로 보고하지 않는다. 다음 적용일 bundle은 기존 publisher/reader/summary/checklist/strict로 확인한다. 정상 PREOPEN/PID, 실제 장중 사건 통보, 독립 표본/완료 비용 손익은 자연 OPEN이다.

현재9/20 checklist는 없으므로 미래9/21 checklist의 기존 기동 owner와 별도 감시 확인 항목으로 인계한다. 최종 커밋·배포·검증 receipt는 [기존 operating evidence 리뷰](../audit-reports/2026-09-20-main-machine-operating-evidence-closure-review.md)에 기록한다.

## 생산자 결손 탐지 후속 리뷰 — 9/20

최우선은 정상 제출 여부와 독립적으로 EV 산출을 막는 생산자 결손을 찾는 것이다. 기존 경제성 owner/계산은 재구현하지 않는다.

- Sentinel cache가 버리던 `entry_ai_economic_plan_observed`/`entry_ai_economic_source_gap`을 수용한다. 큰 frozen plan/계좌 원문 대신 기존 seed validator·capital envelope 계약이 검증한 작은 진단 projection을 보존한다. raw 원본은 변경하지 않는다.
- `recorded_source_only` 표시와 실제 signed seed·plan hash·attempt/종목 결속·운영 cost/exit provenance·예산/reserve·signed capital source를 대사한다. 내부 capital source가 gap인 성공 표시도 `economic_producer_gap`이다.
- 9/21 이후 정확한 기계 attempt에 pre-AI 경제성 관측 이벤트가 없으면 첫 평가10분 유예 후 탐지한다. 과거 도입 전 부재는 historical_not_required이며 9/17 파일을 재구성하거나 원천을 추정하지 않는다.
- 정상 guard/확정 수량0은 `guard_excluded`, producer의 명시 unsupported는 `unsupported_scope`로 따로 집계한다. source_gap·모델 검증/자연 성과는 별개다. 동일 attempt의 상충하는 source proof는 gap으로 남긴다.
- 기존 구조 결손과 같은 지속성/Telegram 전이 규칙을 적용한다. 정상 제출·guard receipt만으로 경제성 결손을 해제하지 않고 같은 attempt의 유효 원천 proof를 요구한다. 통보에 첫 경제성 blocker를 우선 표시한다.
- cache version은 과거 번호와 충돌하지 않는15(raw)/16(lossless)을 사용한다. 기존11/13은 verified zero-stage census와 동일 raw generation/완료 offset이 있을 때만 재사용한다. 근거 없는 schema 덮어쓰기나 전수 raw 재스캔을 이번 리뷰에서 실행하지 않는다.
- 실제 운영 pre-AI producer→pipeline JSONL→Sentinel cache→진단을 KRX/NXT/SOR와 ENTER/BLOCK/RECHECK에서 검증한다. 합성 원천 통과는 자연 유입·유효 모델 holdout·실제 EV가 아니다.


## 9/22 기계정책 개선에 따른 감시 현행화

최신 사용자 승인 범위는 기존 Sentinel/monitor의 의미 검증 보완·리뷰·배포·감시 재검사다. 이전의 전체 운영 경제성 설명을 기계 튜닝의 필수 조건으로 적용하지 않는다. 자동 매매 변경 권한은 없다.

- 기계 튜닝은 BLOCK/RECHECK→ENTER_NOW의 독립 입력/비용 후 경로 평가이며 AI/계좌/청산 실행 재생과 분리한다. 명확한 비진입이고 이전 ENTER·제출·충돌이 없는 후단 source gap은 관측 항목으로 남긴다. 원천을 정상으로 바꾸지 않고, 과거 사건은 exact 증거 일치 시에만 observation_only_unresolved로 재분류한다.
- 기존 monitor 프로세스에서 당일 기계 관측 JSONL의 끝8MiB만 읽는다. 30분 안의 고유 관측 hash만 당시 불변 generation/scope/선택 leaf/실효 임계치와 대사한다. 부분 tail은 전수 coverage가 아니며 source-invalid와 policy mismatch를 구분한다. 당시 selector 재선택은 수행하지만 action/AI/주문/EV 재생은 수행하지 않는다. 새 collector/DB/상주 서비스 없음.
- 기존 machine report/terminal을 각8MiB 제한·hash/date binding으로 읽어 선정 버전·고유 기회 수·원 승률·보정 점수·순 경로EV·발행 상태를 표시한다. 음수EV/1기회 자체는 오류가 아니며 보정점수는 실제 승률·유의성 증명이 아니다. 보고서 존재·발행·현재 PID 영수증·변경 구간 소비를 별도로 표시한다.
- 실효 정책 mismatch는4분 지속 후 기존 알림 경로의 구조 결손이다. 새 관측에서 사라져도 과거 사건은 historical_unresolved이며 복구로 선언하지 않는다. stale/미관측/PID 종료는 현재 소비 증거가 아니다.
- `entry_submit_attempt_finished`는 판정 변경이 아닌 동일 attempt 종료 요약이다. revision 필드가 없는 과거 생산자 요약은 앞서 확인된 판정 owner/action/AI screen과 일치할 때만 같은 revision에 연결한다. 새 판정의 누락·다른 action/screen·선행 실행 후 재판정은 계속 결손으로 유지한다.
- 코드 소유자는 기존 `buy_funnel_sentinel.py`, `monitoring/submission_bottleneck_monitor.py`, 기존 해당 테스트다. 정기 buy-funnel wrapper/cron 경로를 유지한다. 수동 재검사는 notify 없이 실행하며 외부 시험 통보는 하지 않는다.

### 9/22 리뷰·실제 원천 재검사

최초282건 검증/35125396e push·고정 배포 후12:19–12:20 Sentinel과 monitor를 notify 없이 재실행했다. 당시 정책 실효값64건/PID60693 일치, source_invalid10·필수 입력 RECHECK18을 분리했다. 남은6개 revision 경보를 기존 cache 끝16MiB에서 역추적하여 `ai_confirmed`/`blocked_ai_score`가 동일 관측 hash를 재전달하지만 revision envelope를 생략한 경우를 확인했다. 선행 explicit revision과 hash·owner·action·screen이 모두 같은 echo만 결속하도록 보완했다. 다른 hash/판정/owner와 새 revision 누락은 계속 거절한다. 실원천 `aims-53deca7d3c66a14adb41`은 수리 후 single_revision/충돌0/정상 RECHECK로 재현됐으며287개 회귀검증 PASS. 원천 freshness·공급자 지연은 별도 실제 병목으로 유지한다. 증거는 `tmp/semantic-monitor-20260922/`에 보존한다.


### 최종 배포·재검사 결과 — 2026-09-22 12:27 KST

- 최종 코드 `82c31f34fba9430b989ea49340bf13ef5d8b8082` main push, 고정 release `semantic-monitor-20260922-82c31f34f` 배포. source/배포본 각각288tests, compile/bash/diff/문서 parser PASS. 동일 원천의 SOURCE_INVALID/source_invalid 표기 차이도 기존 canonical action 규칙으로 보완했다. 필수cron4개와 buy-funnel router 인계 PASS.
- 실제 배포본에서 Sentinel PID144214(12:26:37–12:27:35), monitor PID144591(12:27:35–12:27:36) 모두 exit0. 수동 notify 미실행. 메인 재기동/정책 변경/AI·주문 호출 없음. 기존 정책1114428c 유지. `final-recheck-processes.json`이 cwd/commit/실행 PID/종료를 결속한다.
- 12:27:35 감시, source12:26:51 기준 최근 투영의 revision/identity 충돌0. 기계 관측 끝8MiB의 최근30분 표본89건 중 당시 policy/scope/leaf/실효 임계치와 실제 메인 PID가 일치한62건, source_invalid10건, 필수 입력 RECHECK17건. 정책 영수증 mismatch0, 선정 report/terminal·표본 보정 계약 결손0. tail 부분 표본이며 전체일·전체 모집단 수치가 아니다. 변경된 통합시장 임계치의 세션별 사용을 정규장 receipt로 대신하지 않는다.
- 현재 실제 병목: current_price/tape stale, provider trade late, source clock skew, 일부 route provenance 및 entry_machine_input_refresh_failed. source blocker 수는 중복 가능하다. 최근30분 고유 promotion49/유효40, 최신상태 ENTER1/VETO0/제출 응답0이며 같은 윈도우의 ENTER 이력은2attempt다. 기계 ENTER 이후를 충분히 평가하기 전 AI VETO 집중이나 임계치 오판으로 단정하지 않는다.
- 최근30분 명확한 비진입 후단 관측 결손39건은 기계 튜닝 실패와 분리. 별도45분 보존·10분 유예의 원천/연결 경보17건과 후단 경제성 경보5건은 남는다. 후단5건은 RECHECK4건의 AI screen 미기록(not_reported:020000/033170/035420/064290)과043260의 이전 ENTER 이력이 있어 현재 비진입만 보고 제외하지 않은1건이다. 다음 owner는 필수 원천 freshness/입력 refresh 생산자, 명시 screen terminal 기록, ENTER revision별 경제성 proof다. closure는 fresh bound source와 동일 attempt 명시 terminal/proof이며 수익 하한·임계치 완화로 닫지 않는다.
- 기존 전체일 요약의 SUBMIT_DROUGHT_CRITICAL/UPSTREAM_AI_THRESHOLD와 최근 기계 전용 진단은 분모가 다르다. 전자는 실제 AI VETO 원인 확정이 아니다. 과거 active 사건은 현재 표본에서 사라졌다는 이유로 복구 처리하지 않았다.
- 최종 근거: `tmp/semantic-monitor-20260922/final-diagnosis.json`, `final-monitor.json`, `downstream-gap-examples.json`, `final-release-validation.json`, `final-recheck-processes.json`, `final-release-tests.log`. 구현·감시 재검사는 완료이며 원천 freshness 정상화/실제 주문·실현손익은 별도 운영 작업이다.

## 9/23 entry split·최초 제출 지연 장후 산출물 감시

감시기는 두 튜닝축의 장후 결과와 bootstrap handoff를 기존 5분 buy-funnel 실행에서 읽는다. 분할 정책과 최초 제출 지연은 별도로 표시하며 서로의 후보·증거·승격상태를 공유하지 않는다.

- Entry split은 최신 exact-date report와 짝 정책의 generation binding, clean-baseline source-date 수, economic blocker, operating 후보 수, paired EV 하한/holdout 수를 읽는다. 후보 0건이나 source gap은 유효한 장후 결과 상태이지 감시 incident가 아니다. bootstrap이 명시적으로 runtime 적용 허용 후보를 선택했다면 그 policy file/version도 같은 manifest 값과 대조한다. source gap이면 bootstrap incumbent 보존을 정상으로 표시한다.
- 최초 제출 지연은 최신 exact-date report의 intent/terminal census와 candidate/blocker 요약을 읽고 canonical `_pre_submit_delay_handoff` 결과를 당일 bootstrap manifest/environment와 비교한다. `not_published`와 `no_validated_candidate_source_gap`은 오류·EV 0으로 보지 않는다. invalid policy binding 또는 당일 handoff/environment와 현재 selector의 불일치만 결손으로 지속 관찰한다.
- 두 축 모두 `runtime_effect=false`, 주문 권한 없음이다. Bootstrap manifest 일치는 설정 handoff 증거일 뿐 실제 PID가 정책을 소비했다는 증거가 아니며, monitor 결과에도 `not_pid_proven`으로 표시한다.
- bounded exact-date JSON만 읽는다. 기존 소형 artifact 개별 8MiB 상한을 적용하며 raw pipeline/BBO 재생·전수 partition scan·tuner 재실행·새 collector/service는 추가하지 않는다. 출력은 기존 monitor incident/state/report와 Telegram 상태전이만 사용한다.
- 검증은 source-gap/미발행 정상 억제, 같은 날짜 generation/handoff mismatch 지속 사건, 과거 날짜 제한, 독립축 표시, null EV 보존, 실제 cron이 고정 release monitor를 소비하는지로 닫는다. 자동매매 프로세스/PID 재기동은 이 감시 변경의 승인 범위가 아니다.
