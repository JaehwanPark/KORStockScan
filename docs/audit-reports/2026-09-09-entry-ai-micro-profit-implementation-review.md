# Entry AI·micro 작은 순수익 개선 구현 리뷰

작성: `2026-09-09 KST`. 구현·검증: `08:19~09:02`, 마지막 정책/원천 감사 snapshot: `09:01:54`. 기준은 [실행 설계](./2026-09-09-entry-ai-micro-profit-improvement-implementation-plan.md)와 사용자의 후속 **구현·반복 리뷰·자동화 및 조건 달성 가능성 점검** 요청이다. 설계 작성 당시의 문서-only 상태와 이번 코드 구현을 구분한다.

이번 검토 범위의 코드 finding은0이다. 작은 기회를 재검토하는 연구 경로, 기존 micro context 전달, 검증된 비용 label의 후속 소비와 중복 적용 조건을 보완했다. **수익 개선은 아직 입증되지 않았다.** 현재 PID에 새 코드가 반영됐거나 새 정책이 선택됐다는 판정도 아니다. 원천·코드 hash, 기존 NXT 사례의 실제 변환 결과와 읽기 전용 정책 receipt는 [검증 JSON](./2026-09-09-entry-ai-micro-profit-implementation-validation.json)에 보존한다.

## 1. 구현과 반복 리뷰

| 발견한 결함 | 최종 수정 | 검증 결과 |
| --- | --- | --- |
| Entry hot payload가 계산된 reaction context를 허용 목록에서 누락. canonical holding context 사용 시에도 별도 reaction context가 빠짐 | `scalping_feature_packet.microstructure_reaction_model_fields`가 기존 v2 사실·품질·identity 16개 필드만 투영. `ai_engine_openai`의 Entry hot/holding payload에 연결 | 최종 직렬화 입력에서 context ID와 0값 보존. 사후 first-hit/PnL 제외. computed/included/sent 및 cache reuse 구분 |
| 참여0 후보가 실노출 floor 미달로 같은 연구 후보에 머무름 | #82의 `entry_prompt_research_progress_v1` → #78 선택. 같은 후보·계약·stage·venue/session의 최근 유효5 source일, unique parent5/종목3, 작은 execution-proxy 누락 사례, 즉시 노출0이면 다음 기존 offline 후보 탐색 | 실제 주문이 없어도 연구 교체 가능. arm을 체결로 세지 않음. 중복/다른 parent·원천 결손은 교체 근거가 아님 |
| 오래전 BUY1건이 이후의 지속 무참여를 가릴 수 있음 | 연구 창은 최근 유효5 source일로 제한. 누적 경제성 모집단은 그대로 보존 | 과거 노출이 있어도 최근5 source일의 무참여를 탐지. 연구 교체와 경제성 탈락 목록을 분리 |
| 오판 사례가 있어도 검토 가능한 구체적 prompt 수정안이 없음 | 한 유효 사례부터 English ASCII appendix 초안, parent/rollback hash, case IDs, 원인 가설, 반례, 동일 payload/outcome 평가 모집단 및 새 버전 검토 필요 상태를 출력. #80이 hash/권한/시장·세션을 검증해 소비 | 신규 Provider 호출·기존 prompt hash 변경·registry 자동 등록 없음. 변조·다른 scope 초안 격리. registry 소진 시 반복 호출 대신 기존 patch handoff |
| 검증된 micro 비용 label이 일반 Entry 상세 비교로 전달되지 않음 | 기존 상세 CLI가 당일 action-neutral label/bridge를 선택적 입력으로 읽음. 기존 deep validator와 request/trace/symbol/venue/session/시각/provider payload/envelope/exact payload hash를 검증해 `entry_cost_aware_opportunity_v1`로 결속. 상세→#82→#78 연결 | 비용/master/원본 path를 재검증. 기본 minute/proxy metric과 분리. 없는/손상된 companion은 직접 결손 사유로 남기고 정상 base 비교는 계속. 비용·spread를 재차 차감하지 않음 |
| 비용 진단의 잘못된 shape/parent/증거 hash가 집계될 여지 | #82가 schema·권한·finite 값·parent·label/path/cost/master hash를 확인하고 `input = verified + source_gap` 보존 | 누락값을 0수익으로 채우지 않음. CF의 실현손익은 null. owner 안전 적격이 결속되지 않은 actionable 분모도 null |
| #78/#80이 모든 후보에 5/10/20일·HELD·미등록을 고정 적용 조건처럼 표시 | 전역 가상 조건 제거. 현재 소비자 자체의 실적용 권한 부재와 후보별 실제 등록 owner를 명시 | KRX V2.14/V2.15의 기존 owner와 NXT/holding/V2.16의 미등록 상태를 구별. #81 legacy는 계속 OFF |
| 누적 probe-arm10/종목3을 충족해도 당일에 같은 arm floor를 다시 요구 | `entry_setup_live_policy`에서 당일 pass=False는 유효 진단으로 허용하고 누적10/3 및 기존 원천·위험·PREOPEN 조건으로 판정 | 당일2arm/1종목·누적12arm/4종목은 연구 검증 통과, 누적9arm 또는 recheck OFF는 차단. 실성과 승격·continuation 중지·주문 보호 조건 유지 |

넓힌 검증에서 V2.14 risk-only composer 테스트의 mock에 노출 비용이 없어 기존 비용 결손 제외 계약과 충돌한 사례를 발견했다. 해당 성공 fixture에 비용을 명시했고, 비용 결손을 허용하도록 엔진을 바꾸지 않았다. 마지막 리뷰에서는 잘못된 초안 ID, 과거 노출의 영향, optional label의 실제 consumer 연결, 손상 원천의 base 연구 차단 여부를 추가 보완했다.

## 2. 예상 효과를 확인한 범위

[9/8 NXT 상세 비교](../../data/report/ai_prompt_detailed_paired_replay/ai_prompt_detailed_paired_replay_2026-09-08_decision_quality_v2_14_setup_risk_adjudicator_venue_nxt_session_nxt_aftermarket.json)의 현재 byte hash와 기존 source contract를 읽기 전용으로 검증했다. 정상24 parent·7종목, 즉시 노출0·arm6, 작은 execution-proxy 누락7건에서 **실제 case ID7개를 가진 검토용 초안1개**가 출력됐다. 유효 source일은1일이므로 연구 교체는 `pending_declared_research_window`다. 코드 실행 결과를 얻기 위해 과거 report·정책을 덮어쓰거나 Provider를 호출하지 않았다.

같은 자료에 새 비용 진단이 없는24건은 `legacy_no_cost_aware_diagnostic`으로 남았다. 따라서 확인된 비용 후 기회0건이라는 뜻이 아니라 **이 자료로 확인할 수 없다는 뜻**이다. 9/8 canonical action-neutral label companion도 없으므로 과거 proxy 사례를 net-positive로 소급 변경하지 않는다. 통합 시험에서는 검증된 exact companion이 비용 값의 재차 차감 없이 상세→#82→#78에 도달하고, 다른 venue/시각/envelope/payload 또는 손상 hash는 비용 진단에서만 제외되는 것을 확인했다.

기대효과는 유효한 작은 기회에 대한 재검토 시작 지연 감소, 장기간 무참여 후보의 연구 교체, AI의 기존 미시구조 입력 누락 제거다. 회복할 실제 거래 수·순이익 금액·모델 우월성은 예측하지 않았다. 정상 경로의 순이익, false BUY/adverse-first, 비용 후 EV, p10/tail과 실주문 terminal은 각각 다음 자연 원천에서 판정한다.

## 3. 자동화 연결과 현재 적용 상태

| 경로 | 설치/consumer 확인 | 현재 판정 |
| --- | --- | --- |
| Main 장후 비교 | 평일21:05 cron → `run_ai_entry_setup_paired_replay_postclose.sh` → 상세/누적 calibration → 같은 날 선택을 고정한 optimizer → metadata rebind/consumer. 기존 batch는 새/변경 parent만 기존 budget으로 실행 | 이번 새 연구 진단·초안·비용 companion 소비는 해당 Python producer의 다음 정상 실행에서 자연 반영. 새 cron이나 추가 Provider budget 불필요 |
| Main 지원 후보의 실적용 | 평일07:35 `auto_bounded_live` PREOPEN cron → `entry_setup_live_policy --write` → 당일 activation → AI loader | 등록된 **KRX V2.14/V2.15**만 기존 조건부 자동 적용. 9/9 실제 activation은 `inactive_fallback_v2_13`, source KRX Control 결손 및 recheck OFF를 포함한 차단 유지 |
| 위젯·에피소드 timing | system timer `korstockscan-machine-microstructure-final-refresh.timer` active/enabled, 직전9/8 21:15, 다음9/9 21:15 → attribution/timing → PREOPEN → 기존 widget/two-leg/Samsung consumer | target9/9 `scopes={}`. 원래 즉시진입 baseline이며 새 micro timing 효과 없음. 선택된 scope만 기존 signal 후0/1/3/5초의 past-only snapshot과 전체 진입 guard 재검증을 사용 |
| 실행 코드 반영 | 평일07:55 정상 launcher cron 존재. 기존 main은 이미 import한 코드로 실행 | 읽은 verify는 PID24260 PASS. 이번 수정의 현재 PID load receipt는 없음. 다음 정상 새 프로세스의 import/실제 payload receipt가 필요하며 cron 존재를 재기동 성공으로 간주하지 않음 |
| 임의 새 prompt·raw ask-depletion 입력 | 초안/sidecar/optional2×2 연구는 존재. 새 schema/actuator와 적용 owner의 검토가 필요 | 초안→임의 live prompt의 무인 승격을 구현했다고 보고하지 않음. V2.16/NXT/holding이 지원 KRX 권한을 상속하지 않음 |

Entry hot 경로와 canonical holding payload에 복구한 것은 기존 reaction의 sweep/replenishment/품질 context다. **raw ask 감소속도·top1/3/5·체결 backing/refill의 신규 입력축과 동일하지 않다.** V2.14/V2.15의 최종 Provider 입력은 deterministic setup ledger만 보내는 기존 계약을 유지하므로 replay context에 존재하는 원자료 전체가 해당 AI에 전달됐다고 하지 않는다. raw ask-depletion은 기존 `ask_depletion.py`/`ai_quality_bridge.py`의 source-only feature 및 optional 비교 경로로 남는다.

P0-A의 exact 저장/action-layer, P0-C의 machine signal/checkpoint/fallback, P1-C의 독립 census/최초 미도달 구분은 기존 구현과 관련 테스트를 검증했다. 같은 코드를 중복 구현하지 않았다. source9/8 machine anchor108/matched0는 새 코드로 복원되지 않으며, [현재 continuity owner](../checklists/2026-09-09-stage2-todo-checklist.md)의9/9 08:51 관찰도 source exclusion/Provider hold를 OPEN으로 보존한다. KRX 정규장 새 exact Control 및 through-close machine 결속의 자연 acceptance는 별도다.

## 4. 목적 부합성·조건 달성 가능성 최종 판정

- **제거/보완한 과도 조건:** 연구에 live 노출을 먼저 요구하는 순환 대기, 과거 한 번의 노출이 최근 무참여를 가리는 누적 판정, 당일+누적 probe-arm 중복 요구, 다른 owner의5/10/20일·HELD 조건을 전역 적용 조건처럼 표시하는 문제다. 단일 사례의 초안 생성에는 이 승격 floor를 붙이지 않는다.
- **연구 유지 조건:** 최근 유효5 source일·unique parent5·종목3은 주문 없이 달성 가능하다. 이미 지원하는 offline 후보 탐색을 위한 창이며 실수익·live 승격 승인이 아니다. proxy 사례는 연구 가설로만 사용하도록 설계 §3.3의 net 근거 대기를 조정했다. 같은 parent 반복·calendar 경과만으로 진행하지 않는다. source0이면 달력 ETA를 붙이지 않는다.
- **보존한 실적용 조건:** exact cost/master/source·same-stage owner·rollback·PREOPEN·broker/hard safety, 성과 승격의 누적 노출10/종목3·양수 비용 후 EV·위험 예산은 유지한다. 작은 gross 수익을 수수료·세금이 소진하는 거래를 늘리는 것은 목표에 맞지 않는다. 기존 one-share exploration의 한도/수량을 바꾸지 않았다.
- **Machine 조건의 역할:** 동적5 observed dates·8 unique/8 completed·coverage85%·right-censored35% 이하·최근 신호·양수/개선 net 및 자본효율·0.005%p uplift·p10은 검증된 timing 변경의 선택 조건이다. `0.005%p`는0.5bps이며 큰 절대수익 목표를 요구하는 조건은 아니다. 선택되지 않아도 원래 즉시진입 매매가 계속되므로 이 floor가 기존 작은 수익 거래를 막는 원인은 아니다. 현재 matched0의 첫 결손은 원천 결속이라 floor를 낮춰 해결하지 않는다. 자연 유입률이 입증되지 않아 달성일/확률은 산정하지 않는다.
- **진단 수리와 성과 승인 분리:** context 전달 수리/초안 생성/비용 companion 결속에 양수 실현손익·전체 horizon·20일 실거래를 추가 완료조건으로 붙이지 않았다. 대신 실제 선택·PID 소비와 비용 후 성과를 아래 기존 owner에서 확인한다.

## 5. 검증과 남은 acceptance

`korstockscan-review-gate`로 구현→리뷰→보완→재리뷰를 수행했다. 관련19개 모듈 **996 tests PASS**, 마지막 비용 증거 보강 후 영향4개 모듈 **302 tests PASS**. 두 집합은 중복이므로1,298개 고유 테스트로 합산하지 않는다. Python compile, `git diff --check`, 문서 링크/anchor57개 및 print-only parser PASS(확인 시점38 tasks, 연결한 기존 owner6개 각각1회)다. 전체 시험에 기존 multiprocessing fork DeprecationWarning2건이 있었고 실패는 없었다. 운영 Provider replay, broker 조회/주문, canonical report 재생성, bot 재기동, 수동 env/lock/threshold 변경은 실행하지 않았다.

| 기존 owner | 남은 확인과 종료조건 |
| --- | --- |
| `AIDecisionActionOutcomeNaturalEvidence0908` | 9/9 20:10~21:55. 새 exact Control, optional 비용 companion의 유효/결손 분모, #82 연구 진단→#78 초안/다음 후보→#80 동일 hash의 자연 소비. 코드 완료와 순이익 효과 분리 |
| `EntryRecheckNaturalAttribution0907` | 9/9 20:10~21:50. arm/recheck/submit/terminal 분리 및 다음 PREOPEN의 실제 누적 arm 조건/선택/receipt. 오늘 OFF를 수동으로 해제하지 않음 |
| `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908` | 기존08:40~08:45 확인 이후 through-close 원천·exact exclusion과 다음 정상 PID의 실제 reaction payload/전송 receipt |
| `MachineLifecycleTurnoverObjectiveFollowup0909` | 9/9 21:30~21:40. 새 exact signal/epoch/checkpoint/terminal → baseline 유지 또는 검증된 단일 timing scope와 비용·자본점유 |
| `ScannerLookupAttentionNaturalEvidence0908` | 9/9 20:10~20:40. 독립 상승 모집단과 독립 machine 감사 사례를 분리한 최초 미도달 stage. 다른 owner의 수익을 Main AI DROP 오류로 치환하지 않음 |
| `MainAIQualitySourceGapArtifactContract0909` | 9/9 21:40~21:50. 진단/초안/source gap을 기존 native workorder의 정확한 generation과 연결. 초안 ID를 적용 승인 ID로 만들지 않음 |

위 자연 확인은 [기존 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)에 연결했다. `repair_status=reviewed`, `deployment_status=pending_natural_consumer_or_new_PID`, `natural_acceptance=open`, `economic_acceptance=unproven`이다. 일반 장중 모니터링이나 야간 전체 작업을 이 구현 리뷰로 대신 완료 처리하지 않는다.
