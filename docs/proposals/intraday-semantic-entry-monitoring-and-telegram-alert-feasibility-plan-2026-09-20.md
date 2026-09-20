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
| identity 결손 | 기계 원천 이벤트의 필수 identity 부재를 동일 유예·지속 기준으로 확인 | 분모를 추정하지 않고 unbound 원천 hash를 보존 |

수치는 **진단 알림의 초기값**이며 튜닝으로 검증된 최적치나 매매 gate가 아니다. WINDOW/GRACE/PERSIST/MIN_PROMOTIONS는 모듈 한 곳에서 관리한다.

- venue/session/policy hash별 분리; promotion×symbol 중복 제거. 반복 RECHECK를 새 독립 기회로 세지 않는다. 정상 BLOCK/RECHECK의 `not_requested_machine_nonentry`와 ENTER의 실제 screen을 구분한다.
- 최초 평가 clock와 최신 terminal을 함께 보존한다. 늦은 제출/guard/거절은 같은 exact attempt의 미종결을 닫는다. 윈도우 밖으로 사라짐·정책 교체·분모 없음은 복구 증거가 아니다.
- 입력 date가 현재 KST와 다름, dry-run, 생성 후7분 초과, 최근 event10분 초과, 역행/중복 snapshot은 `unobservable`이며 새 경보/복구를 만들지 않는다. 멈춘 봇·원천 freshness는 기존 error detector owner가 담당한다.
- source-invalid는 해당 promotion을 정상 판단 비율 분모에서 제외한다. 유효 scope는 계속 관찰한다. 결손을 0 EV/no-edge로 바꾸지 않는다.
- 미결 사건은 날짜별 상태에 남는다. 구조 결손은 저장한 exact attempt가 명시 terminal로 닫힐 때만 복구; 비율 경보는 새로운 실제 제출 응답으로 복구한다. 옛 identity 부재는 건강한 새 이벤트만으로 과거 복구라고 선언하지 않는다.

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
