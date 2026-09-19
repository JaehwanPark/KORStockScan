# Compact AI 장후 원천·paired 평가·장전 소비 통합 구현계획

작성일·후속 보완일·현행 재설계일: 2026-09-19 KST. 이번 요청의 범위는 상세 개선계획 수정이다. 이전 승인으로 수행된 통합 구현은 §10·§18·§19의 완료 기록이며, 이번 계획 작성에서는 코드 변경·후보 호출·장후 재생성·배포·PREOPEN 실행을 수행하지 않는다. §20 이후의 현행 단일-owner 계획이 앞선 coordinator 유지 방침과 충돌할 때 우선한다.

목표는 구조적 원천 결손을 해결하고 실제 compact 보조판정 기회에서 비용 반영 EV·일별 순익 차이를 도출한 뒤, 검증된 정책 또는 기존 정책 보존 결정을 다음 거래일의 기존 장전 소비 경로까지 연결하는 것이다. 우선순위는 구조 결손 → 경제성 비교 → 소비 연결 → 중복 실행 감소다.

현행 결론은 `compact_auxiliary_paired_replay`를 유일한 compact AI 경제성 evaluator로 두는 것이다. `ai_action_outcome_calibration --postclose-phase prepare|evaluate|finalize|handoff`는 독립 튜닝축이 아니라 다른 owner를 재호출하는 조정 표면이며, Daily/EV 공통 튜닝 퇴역 뒤 `handoff`가 삭제된 요약과 제거된 section을 계속 요구한다. 따라서 단계 CLI·wrapper 호출·전용 summary 복제를 퇴역하고, 원천 생산자 → compact evaluator → 단일 dated publisher → 장중 loader → 직접 증거 verifier 흐름으로 축소한다. `ai_action_outcome_calibration`의 기계 action/outcome 진단과 기존 원천 schema는 필요한 범위에서 보존하되 후보 실행·정책 발행·최종 handoff owner가 되지 않는다.

## 1. 근거와 현재 상태

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). `main-only`, `normal_only`, `post_fallback_deprecation`, clean baseline `2026-06-05T00:00:00+09:00` 및 기존 hard safety를 유지한다.
- 순서: [장후 작업 목록](../audit-reports/2026-09-05-postclose-work-inventory.md). 구현 시 현행 wrapper와 설치 schedule를 다시 대조하고, 원천 준비·final 품질 감사·compact 평가·단일 최종화·직접 검증의 선후 관계로 작업목록을 갱신한다.
- 기존 기능: [compact 경제성 계획](compact-auxiliary-ai-paired-economic-tuning-and-consumer-closed-loop-improvement-plan-2026-09-18.md), [AI 원천·라벨 통합 계획](ai-decision-quality-postclose-source-label-consolidation-and-current-evaluator-plan-2026-09-18.md). 완료된 기능은 재구현하지 않는다. 이 계획은 공통 실행 순서·generation·최종 소비를 정비하는 통합 변경이다.
- 최초 계획의 분석 release는 `988baa142c9338bad9085f56f257b3422392b3b2`였다. 이번 후속 보완의 선택 release는 `compact-ai-label-admission-reviewed-20260919`, source SHA `9f814e30cbc08806750616e94f7ab099d5aa58d1`이다. 선택은 future invocations only이며 actual PID 소비는 확인되지 않았다. 작업 디렉터리와 선택 release의 코드가 다르고 다른 세션 변경도 있으므로 구현 착수 때 다시 대조한다.
- 현재 [9/19 체크리스트](../checklists/2026-09-19-stage2-todo-checklist.md)가 존재하며 통합 구현의 완료 기록을 소유한다. [9/21 체크리스트](../checklists/2026-09-21-stage2-todo-checklist.md)의 기존 stable ID `KiwoomCommonHealthOpportunityCostAcceptance0917`는 자연 수용의 현재 실행 owner다. 후속 코드 결함이 재현되면 실제 실행일 체크리스트에서 완료 기록과 분리해 보완 범위를 연결한다. 자연 표본 부족만으로 완료된 구현 전체를 재개하거나 자연 owner를 복제하지 않는다.

이번 재확인에서 2026-09-17 원천의 compact 보고서는 2026-09-19 07:48:54 KST 생성이다. 실제 screen 21건, 평가 제외 21건, 이번 후보 호출 0건, 유효 비교 0건, EV와 일별 순익 차이 null, `source_contract_blocked`, `incumbent_preserved`다. 최초 제외는 정확한 손절 거리 결손 10건, 자연 판정 계약 무효 9건(타임아웃 8·semantic reject 1), venue/session 라벨 식별 충돌 2건이다. 중첩 진단의 stop 결손 11건과 최초 제외 10건은 서로 다른 집계이며 합산하지 않는다.

운영 실행 모델은 코드가 있지만 원천 projection의 coverage가 입증되지 않았고 일별 계획 3건이 무효이며 독립 선행 model holdout이 없다. 검증된 owner journal의 비교 0건은 전체 실제 주문 0건을 뜻하지 않는다.

최신 paired 보고서·consumer·9/21 정책의 해시는 일치한다. 9/21 정책은 기존 `entry_machine_auxiliary_compact_v3`를 보존하고 승격 scope는 없다. 정책 생성·인계와 실제 PID 소비·경제성 입증은 별도다.

현재 근거: [paired 보고서](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.json), [동결 원천](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.source.json), [consumer 영수증](../../data/report/main_ai_prompt_consumer/main_ai_prompt_consumer_2026-09-19.json), [9/21 정책](../../data/runtime/mechanistic_entry_policy/policy_2026-09-21.json), [통합 구현·후속 리뷰](../audit-reports/2026-09-19-compact-ai-postclose-integration-implementation-review.md). 구현 시 재확인하며 과거 generation을 최신 것으로 바꿔 표시하지 않는다.

## 2. 통합 경계와 기존 코드 재사용

운영 흐름을 하나로 관리하되 원천 정합성, 모델 검증, 프롬프트 경제성, 정책 발행의 결과는 분리한다. 파일을 하나로 합치거나 대형 `ai_decision_quality.py`에 후보 실행·발행을 추가하지 않는다.

| 기존 owner | 통합 후 책임 | 변경 경계 |
| --- | --- | --- |
| `ai_decision_quality` | control·labels·원천 revision 준비 | 기존 materialization/reuse 함수 재사용; 후보 호출·정책 발행 책임 추가 없음 |
| `entry_split_order_plan`, `strategy_owner_replay`, 기존 pipeline writer/compactor | 당시 계획·수량·비용·exit·원천 coverage·독립 운영 CF 및 실제 실적 기반 모델 검증 | 확인된 잔여 결손만 수정; 다른 세션의 완료 기능 재구현 금지 |
| `compact_auxiliary_paired_replay` | admission·기존/후보 비교·checkpoint·scope별 학습/holdout | 기존 v6 검증 재사용; 공통 generation과 재개 계약 보완 |
| `ai_action_outcome_calibration` | 기존 machine action/outcome 진단·canonical report schema | compact 후보 실행·정책 발행·summary handoff 책임 제거. 진단은 직접 원천을 읽고 runtime 권한을 갖지 않음 |
| `mechanistic_entry_runtime_policy` | 다음 거래일 단일 정책 publisher | compact 전용 publisher 추가 금지; machine·다른 scope와 기존 정책 보존 |
| 기존 optimizer·consumer·runtime summary·tower·checklist·verifier | 동일 최종 generation의 직접 소비·closure | 평가를 재실행하거나 Daily/EV 복제 section을 요구하지 않고 canonical paired/policy/loader receipt를 참조 |
| `entry_setup_live_policy`, `ai_engine_openai`, 기존 PREOPEN | 정확한 날짜·scope 정책 해석, 실제 발행 프롬프트 사용·추적 | 기존 loader 재사용; 주문·provider·수량·cap·안전 권한 변경 없음 |

기존 `entry_setup_paired_replay_batch --compact-only`는 부분 실행·재개용 진입점으로 남긴다. 정상 main wrapper와 독립 paired wrapper는 같은 `compact_auxiliary_paired_replay` 평가·최종화 함수를 직접 사용한다. 별도 coordinator CLI나 예약을 신설하지 않는다. source-day lock과 publisher lock의 획득 순서를 고정해 재귀·이중 잠금 대기를 피한다.

기존 calibration CLI의 `--postclose-phase prepare|evaluate|finalize|handoff`는 호환 호출·wrapper·테스트와 함께 퇴역 대상이다. 평가와 발행은 compact owner의 기존 함수·lock을 재사용한다. 구형 단계 인자를 무동작 alias로 장기간 남기지 않으며 실제 호출자를 먼저 제거한 뒤 CLI를 삭제한다.

## 3. 작업 전후·생산자 소비자 순서

| 단계 | 선행 입력 | 수행·출력 | 필수 후행 소비 |
| --- | --- | --- | --- |
| P0 경제성 reference | 원천일·기존 full-cost owner | 기존 reference-only 확보 | label·운영 replay; missing을 0으로 대체하지 않음 |
| P1 준비 | performance fact·entry split·trace/payload·sealed snapshot | 기존 control·labels materialization/reuse, 원천 receipt | compact admission; source producer 위치 보존 |
| P2 admission/평가 | final source audit·P1 labels·owner operating CF·선행 model proof | 유효 scope에서만 후보 호출·paired 결과·학습/holdout | canonical paired report; 확정 정책과 구분 |
| P3 최종화 | 필요한 tail 생산자 완료·현재 의존 hash | 평가 reuse, optimizer·단일 dated 정책·consumer 확정 | runtime summary/tower/checklist의 직접 소비 |
| P4 검증 | P3 최종 generation 및 직접 소비 receipt | direct family verifier → controller DONE | 다음 거래일 기존 PREOPEN |
| P5 자연 소비 | effective-date 정책·정규 PREOPEN | loader 해석·bundle/version·실제 PID/trace receipt | 완료 실적 기반 joint applied-version 성과 |

현재 main의 앞단 quality materialization과 final 감사 뒤 compact 평가 순서는 유지한다. compact evaluator의 P2/P3만 단일 owner로 연결한다. 초기 labels는 provisional 원천이며 final 감사·tail 변경 후 authoritative generation을 재확인한다.

P2는 후보 평가의 유일한 정상 provider 실행 지점이다. P3는 provider를 호출하지 않는다. P3에서 새로운 원천이 발견되면 `evaluation_deferred`와 next owner를 기록하고 해당 scope 후보를 보존/차단한다. 최종화 안에서 묵시적으로 새 평가를 시작하지 않는다. machine와 compact는 각자의 proof로 독립 판단하되 최종 날짜별 정책은 하나의 publisher가 한 번 확정한다. 미지원 compact가 검증된 다른 scope/owner 결과를 지우지 않는다.

단일 최종 발행으로 전환하기 전에 policy 파일 대기·이전 bundle 참조를 가진 consumer를 식별한다. 최종 policy 의존 consumer는 P3 뒤로 이동하고, P2 결과만 필요한 consumer는 명시적으로 canonical paired report를 받는다. 이미 동결된 PREOPEN 정책은 같은 날짜의 재생성으로 덮어쓰지 않고 기존 freeze/승계 계약을 따른다. 이전 파일이 있다는 이유로 새 generation 대기를 통과시키지 않는다.

최종화는 필요한 선행 완료 후 runtime summary·tower·checklist·verifier보다 앞에 둔다. 후행 요약은 canonical family artifact를 직접 읽고 별도 section을 복제하지 않는다. verifier/controller 자신의 hash는 summary 입력에 넣지 않는다.

## 4. 최우선 구조적 결손 보완

| 결손 | producer·최소 보완 | consumer·closure |
| --- | --- | --- |
| 정확한 stop/operating plan 누락 | 기존 pre-AI observer·atomic plan에서 당시 loaded holding policy/state·stop·비용·수량·예산·owner TTL·route를 고정; 기존 지원 여부부터 점검 | 운영 replay와 compact가 같은 seed/hash로 full-cost terminal을 계산. 과거 삭제 원천은 generic stop·현재 가격으로 복원 금지 |
| timeout/semantic reject | trace/quality owner가 transport 실패와 응답 계약 실패를 보존. timeout의 실제 발생 지점·호출시간 receipt로 잔여 결함 확인 | compact에 정상 자연 screen만 공급. 과거 8 timeout·1 reject를 PASS나 후보 기준 응답으로 대체 금지; provider/timeout guard 자동 완화 없음 |
| venue/session 식별 충돌 | quality label·canonical context·trace·owner seed의 exact identity 및 증명된 route equivalence 재사용 | 올바른 조인 회귀, native 충돌은 계속 제외. identity 수리가 terminal·operating proof까지 유효해졌음을 뜻하지 않음 |
| lossy execution projection·coverage 미입증 | 기존 writer/summary compactor의 declared stage census·retained/excluded/lossless identity·원자 seed 전달 대사 | entry split 모델 검증이 source_gap과 실제 0 모집단을 구분. 전체 과거 Main 주문 census로 과장 금지 |
| 독립 운영 모델 검증 없음 | 기존 실제 제출·fill·COMPLETED valid profit/cost owner에서 scope별 actual calibration 및 선행 model holdout | 정확한 scope/route·model implementation·오차/tolerance proof가 prompt learning보다 먼저 완료. full/partial·수동 custody·CF 분리 |

다른 세션이 quality/entry split producer를 수정 중이면 producer schema·출력 path·generation·완료 테스트를 받아 공통 consumer만 연결한다. 필요한 upstream 수정이 미완료면 owner와 구체적 closure를 남기며 통합 완료로 덮지 않는다. 새 수집기·broker 조회·Kiwoom request/parser 변경은 이 통합에 기본 포함하지 않는다. 그런 수정이 필요하면 공식 API reference gate와 해당 owner 범위로 별도 검증한다.

역사적 source loss는 고정 제외로 남긴다. 이미 복구 불가능하다고 판정한 원천을 같은 raw 재조회·전수 replay로 반복하지 않는다. 향후 정상 producer 자료가 들어왔을 때만 새 평가를 연다.

## 5. 유의미한 EV 비교 계약

대상은 실제 machine `ENTER_NOW` 이후 발생한 compact screen이다. machine BLOCK/RECHECK에 AI를 합성하지 않는다. 각 screen의 broker fill을 의무화하지 않으며, VETO의 실행 가능한 기회도 동일 분모에서 비교한다. 다만 운영 CF 모델의 독립 검증은 실제 실적으로 닫아야 한다.

- 당시 exact input·prompt·attempt·scanner·venue/session/route·seed·모델·cost/exit hash를 동결한다. 비교하는 프롬프트만 다르고 기계 선택·수량·자본·holding owner·hard safety는 같다.
- 기존 v3와 등록 후보 opportunity v2의 PASS/VETO를 비교한다. 같은 판정은 Δ0으로 분모에 보존한다. CAUTION은 실제 recheck 종결 지원이 없으면 제외하며 신규 후속 모델을 억지로 만들지 않는다.
- PASS는 기존 운영 owner의 독립 terminal 순익, VETO는 진짜 미진입 결과를 사용한다. 원천/비용/terminal 결손은 null, 정상 미진입만 0이다. self comparison·baseline carry는 독립 개선 성공이 아니다.
- 평균 수익률 진단과 운영 승격 근거를 분리한다. 동일 예산 기준 순익/EV·일별 금액 Δ·자본 점유/reserve·tail·stress·모델 오차·추론비용을 표시한다. 실현 PnL과 CF PnL을 합치지 않는다.
- 현재 v6의 scope·route별 20 learning/20 forward holdout/최소 2 holdout source days/coverage 1.0, 동결·holdout 미사용·양수 paired EV/일별 순익·tail/stress 조건을 유지한다. 별도의 선행 운영 모델 표본/holdout은 prompt 표본으로 대체하지 않는다.
- 실측 모델 오차·stress envelope 차감 하한은 통계적 신뢰구간이 아니다. 회계상 reviewed zero-cost receipt는 보존하되 vendor 무료 가격이라고 해석하지 않는다. 비용 receipt가 무효면 missing으로 차단한다.
- 한 포지션의 중첩 자본 충돌은 현재 모델의 지원 범위 밖이다. 지원 범위 내 비중첩 결과를 별도 표시하고 충돌을 독립 이익 합산으로 숨기지 않는다. 현재 데이터에 충돌이 실제 병목인지 확인하기 전에 새 portfolio simulator를 만들지 않는다.

유효 입력이 있으면 learning 단계에서도 비용 반영 비교값을 산출한다. 승격 표본 미달 때문에 연구 EV까지 지우지 않는다. 반대로 운영 모델 미검증 자료는 진단으로만 남기고 비용이 드는 후보 실행에 투입하지 않는다.

## 6. Generation·조건부 실행·재개

기존 report/manifest/checkpoint 안에 source date, publication date, effective date, phase, source generation, source/code/contract/model/input/prompt/result hash, scope/route, status/reason, next owner/closure를 결속한다. 같은 개념의 새 manifest·DB·report family는 만들지 않는다.

1. 원천 receipt 동일 + 기존 결과 계약 유효: 재사용하고 provider 호출 0, source raw 재스캔 0을 확인한다.
2. code/consumer 계약만 변경: 영향받는 작은 projection/labels/summary를 재결속한다. 모델 구현 또는 실제 issued input/prompt가 바뀌면 해당 평가 proof를 무효화한다.
3. 실제 source revision 변경: 변경 producer만 새 generation 생성. 요청 키가 다른 pair만 평가; 이미 동결된 learning cutoff와 consumed holdout은 이동하지 않는다.
4. invalid rows: scope별 제외와 원인 counts를 보존. global preflight 무효 등 기존 계약에 해당할 때만 전체 차단한다.
5. pending mature: 필요한 terminal owner/조건을 기록. irrecoverable source_gap, sample 부족, valid_no_edge, provider execution error를 섞지 않는다.
6. 부분 실패/재개: 원자 result/checkpoint 뒤 receipt, 최종 publication receipt 뒤 marker. 정책 파일 존재만으로 DONE 처리하지 않는다. 공통 source-day 잠금 아래 부분 CLI·main·paired wrapper의 동시 후보 호출/발행을 방지한다.

추가 성능 framework·guard·병렬화·horizon 확대는 하지 않는다. 기존 request budget/retry/resource 상한을 유지한다. 시간이 길면 후보 수·부가 진단 깊이를 줄이되 공통 분모·불리한 결과·비용·holdout·source contract를 삭제하지 않는다.

## 7. 다음 장전 정책 생성·소비

정책은 기존 `data/runtime/mechanistic_entry_policy/policy_<effective_date>.json`에 발행한다. source date는 자정 이후에도 고정하고 publication date와 effective date는 기존 거래일 계산을 사용한다. 현재 9/17 source → 9/18 publication → 9/21 effective는 역사적 인계이며 이후 실행에 하드코딩하지 않는다.

| 평가 결과 | 발행 결과 | 완료 주장 |
| --- | --- | --- |
| 유효 scope가 기존 승격 조건 통과 | 해당 scope의 검증 후보, 나머지 incumbent 보존 | selection/publication 완료. actual PID·순익 개선은 별도 |
| 유효 비교했으나 개선/위험/표본 조건 미달 | 기존 정책 carry + 측정 EV/순익과 이유 | 연구 결과 확보; 승격 없음 |
| source/model gap, 유효 비교 0 | 검증된 incumbent가 있을 때만 hash-bound carry + null/next owner | 정책 인계만 완료. 경제성 비교 완료 아님 |
| incumbent 자체도 무효/없음 | 기존 실패 계약에 따라 publication/apply 차단 | 새 기본값이나 fail-open 정책 생성 금지 |

P3는 calibration·paired·optimizer·consumer·bundle 해시가 같은 최종 결과를 가리키는지 검증한다. 기존 PREOPEN apply/resolver는 정확한 effective date/scope·bundle·prompt hash를 검증하고 source gap 후보를 적용하지 않는다. Main은 bundle의 prompt를 byte-identical하게 사용하며 attempt·version·bundle·PID 증거를 trace와 submit context에 남긴다. 실제 완료 실적은 joint machine+compact version별 rolling/cumulative/post-apply 성과로 귀속한다.

정책을 만들기 위해 양수 결과를 조작하거나 표본/비용/안전 기준을 완화하지 않는다. 다음 장전 usable 정책 생성 요구는 정상 carry까지 포함하지만 **현재 비교 0건을 모든 경제성 구현 목표 종결로 처리하지 않는다.**

## 8. 구현 패키지·검증·종결

| 순서 | 최소 변경 | 필수 증거 |
| --- | --- | --- |
| CI0 계약 확정 | 선택 release/다른 세션 producer 변경 대조, 실제 호출자·lock·후행 위치 확인 | 구현돼 있는 v6/model/labels 기능 재사용, 각 결손의 owner·test 확정 |
| CI1 구조 결손 | §4의 실제 잔여 producer/consumer 결손만 보완 | 자연 writer → compact partition → seed/replay/model admission의 lossless lineage; historical loss 제외 유지 |
| CI2 단일 evaluator | calibration phase coordinator와 wrapper 호출 제거, main/paired wrapper를 compact evaluator에 직접 연결 | 후보 한 번 호출, finalize provider0, 동일 fingerprint 재사용·동시 호출·부분 실패 회귀 |
| CI3 경제성/발행 | 기존 v6 평가·model proof·publisher·loader의 동일 generation 연결 | supported/unsupported·0/null·CAUTION·route/scope·모델 변경·holdout 오염·carry/positive fixture의 정확한 결과 |
| CI4 직접 인계 | runtime summary·tower·checklist·verifier를 canonical paired/policy receipt에 연결 | Daily/EV 부재 허용, stale/hash/date/scope 오류 차단, 복제 section 없음 |
| CI5 제한 재생성 | 리뷰·검증 후 승인된 새 유효 원천일/family만 재생성 | 기존 원천 보존, provider 사용 근거, EV/일별 순익 값 또는 첫 blocker, 최종 해시·정책·직접 소비 receipt |
| CI6 자연 수용 | 정규 PREOPEN 및 이후 자연 입력/실적 확인 | 실제 PID/issued prompt 소비·model holdout·prompt holdout·joint-version 완료 비용 후 성과 |

CI5에서 원천이 모두 결손이면 반복 재생성을 중단하고 CI1의 생산자 공급과 CI6의 자연 증거를 남긴다. 코드 통합 closure와 경제성 자연 수용 closure는 분리해 보고한다. 유효 운영 비교가 확보되면 양수 개선 또는 측정된 no-edge 모두 유의미한 결과다. 표본이나 실제 결과가 없는 상태에서 양수 개선을 보장하지 않는다.

검증은 기존 `src/tests`의 quality/entry split/strategy replay/compact batch/calibration/optimizer/consumer/policy/live resolver/wrapper/summary handoff/strict verifier 테스트 중 영향을 받는 계약만 보완한다. 합성 positive fixture는 승격 경로 검증이고 자연 EV 증거가 아니다. Python compile·해당 pytest, wrapper `bash -n`, diff check를 수행한다. 신규 root module·collector·test family·report family는 기본 금지다.

각 패키지는 구현 → self review → 보완 → re-review → targeted validation을 따른다. 배포·재생성은 별도로 승인된 범위에서만 진행한다. automation/wrapper를 바꾸는 구현 변경에서는 작업 목록·운영 문서·실제 실행일 checklist를 함께 정비한다. baseline README/runbook/Plan Rebase/prompt/AGENTS 변경은 별도 명시 요청 범위에 따른다.

전체 확인 기준:

- 최초 Daily와 후행 machine/다른 family 소비가 유지되고 원천·결과·정책 단절이 없다.
- 동일 generation 재실행은 중복 후보 호출/표본/발행을 만들지 않는다.
- 지원되는 자연 입력이 경제 평가로 들어가며 운영 모델·표본·승격 결손이 각자의 상태로 드러난다.
- 같은 예산·비용·terminal·모델 오차 기준 EV와 일별 금액 차이가 산출된다. 비교 0/source_gap은 이를 충족하지 않는다.
- 다음 거래일 검증된 후보 또는 유효 incumbent carry가 생성되고 loader가 해석한다. 실제 PID·자연 적용·실현 성과는 해당 영수증으로만 확인한다.
- final source → policy/consumer → runtime summary/tower/checklist → direct strict verifier → controller closure를 같은 generation으로 확인한다. scoped PASS를 전체 native DONE으로 주장하지 않는다.

## 9. 이번 계획 검증 범위

이번 변경은 계획 문서 한 개다. 링크·책임·선후 순서·0/null·권한·기존 stable ID 인계 기준을 review/fix/re-review하고 `git diff --check` 및 print-only backlog parser로 검증한다. runtime/source 수정, trading 테스트, AI 호출, 재생성, 외부 sync는 수행하지 않는다.


## 10. 과거 승인 구현 기록

- 당시 사용자 후속 지시가 구현·리뷰·커밋푸시·배포·제한 재생성을 승인했다. 아래 단계 coordinator 기록은 그 구현 시점의 증거이며, Daily/EV 퇴역 뒤 확인된 중복 owner·stale handoff의 현행 설계는 §20–§28이 대체한다.
- 단계 인자는 기존 calibration의 `--postclose-phase prepare|evaluate|finalize|handoff`다. 앞단 quality producer의 기존 materialization을 유지하고 prepare는 그 원천을 검증·결속한다. 새 raw reader나 collector를 만들지 않는다.
- finalize는 source 변경 시 재평가 요구로 실패하며 provider 호출·raw 재스캔을 하지 않는다. 기존 정책을 덮어 새 완료로 만들지 않는다. 정상 finalize 뒤 tail 소비 재결속은 handoff 단계로 분리하며 provider와 publisher 모두 호출하지 않는다.
- 준비/평가 단계는 provisional 보고서만 작성한다. 정상 machine+compact 발행은 필수 WS 입력 후·최초 Daily refresh/EV/runtime summary 전에 단일 확정하고, 부분 연구 재생성은 `--compact-scope-only`로 다른 machine/owner 정책을 보존한다.
- 현재일9/19 implementation owner와 다음9/21 기존 자연 acceptance owner를 분리한다. 현재21건의 비가역적 과거 결손과 선행 실제 모델 검증 부재는 코드로 표본을 합성해 해결하지 않는다. 구조 producer 지원은 기존 완료 코드/회귀로 확인하고 자연 경제성은 별도 OPEN으로 유지한다.

## 11. 후속 최적화의 판단 기준과 완료 재분류

`finalize`는 이미 평가된 machine·compact 결과를 검증해 날짜별 정책과 후행 소비에 전달하는 공통 최종화다. 독자적으로 패턴·전략을 탐색하지 않는다. 최적화 대상은 기존 machine 후보 평가와 compact paired 평가이며, 최종화에는 입력 검증·정확한 상태·재사용·소비 결속만 남긴다.

| 현재 요소 | 이번 확인의 판정 | 후속 보완의 범위 |
| --- | --- | --- |
| prepare/evaluate/finalize/handoff·단일 publisher·dated loader | 통합 코드·scoped handoff 완료 증거 있음 | 재구현하지 않고 새 입력·상태 계약의 영향만 회귀 |
| frozen plan observer·KRX/NXT/SOR admission·owner replay·모델 검증 | 지원 코드 존재; 운영 경로 전체의 자연 수용은 미입증 | 운영 producer가 만든 지원 입력이 저장·projection·계산까지 도달하는 통제 회귀부터 입증 |
| paired 순익/EV·stress/실측 오차·독립 holdout | 계산·승격 계약 존재; 자연 비교 0 | 현재 계산을 재사용하고 표본 미달 단계에서도 유효 연구값을 표시 |
| 미래 정상 생성·coverage 계약 | 코드 존재만으로 자연 대기 판정 불가 | producer→consumer 회귀 불통과는 구현·검증 미완료, 통과 후 자연 자료 부재만 자연 대기 |
| 정규 PREOPEN·실제 issued prompt/PID·완료 손익 | 자연 수용 OPEN | 미래 자연 적용 영수증으로 확인; 파일/fixture/PASS로 닫지 않음 |

관측된 잔여 결함은 `natural_contract_invalid`의 timeout/semantic 오류를 일괄 `unsupported_scope`로 분류하는 점과, `phase=finalize` 뒤에도 calibration 최상위 `status=source_prepared`가 남는 점이다. 이는 blocker 판단·완료 표시의 결함이며 EV 결손을 직접 해결한 것으로 보고하지 않는다. 현재 재생성은 compact scope only라서 machine의 전체 경제성까지 갱신·완료됐다는 주장을 하지 않는다.

프리마켓 NXT, 정규장·애프터마켓 KRX/NXT 관측과 SOR 주문 경로는 별개 필드다. 현재 route admission은 SOR를 지원한다. SOR라는 이유만으로 미래 입력을 제외하지 않는다. 결정 venue/session·관측 feed·주문 route·실제 체결 venue를 각각 원천 그대로 보존하고, 체결 venue를 관측 feed에서 추정하지 않는다.

## 12. 운영 입력 공급을 먼저 닫는 보완

다음 비교값을 얻기 위한 첫 목표는 지원 입력의 미래 생성·저장·admission을 닫는 것이다. 과거 21건의 추정 복원은 목표가 아니다. 기존 `_observe_entry_economics_before_ai`와 실제 호출 경로, trace/quality, pipeline writer/compactor, sizing plan, custody registry, entry split model owner를 사용한다.

| 경계·기존 owner | 필요한 증거·최소 수리 | 종료 검사 |
| --- | --- | --- |
| machine ENTER_NOW→pre-AI observer | 당시 승인 sizing/budget, 정확한 stop·loaded exit state, 비용 provenance·route·가격/TTL·reserve 규칙의 frozen seed; source-only 실패 receipt | 기존 운영 함수로 지원 seed 생성. observer가 live state·주문·실제 reserve를 변경하지 않고 불충족 입력만 구체 제외 |
| request/response→정규화·labels | 동일 request/attempt/prompt identity와 정상 PASS/VETO·transport/semantic 상태 보존 | 정상 입력의 stop/cost/route가 변환에서 사라지지 않음. timeout8·reject1은 실제 오류로 유지; PASS 대체 금지 |
| 저장→execution partition/projection | declared stage census와 retained/excluded IDs·source location/hash·plan 전달 | expected=retained+명시 제외를 identity로 대사. missing census는 source_gap, 정상 원천 0은 별도 valid-empty |
| parent/attempt→order owner→broker/fill/terminal | 기존 native identity 및 owner custody와 full/partial/pending/COMPLETED valid costs 결속 | retry·부분체결·중복 projection을 한 episode로 귀속. 미제출 screen도 screen 분모에서 삭제하지 않음 |
| seed→owner replay→operating model | frozen exit/cost 상태와 시간순 actual calibration/model holdout | 지원 입력의 모델 순익·reserve·보유 노출 계산과 실제 완료 손익 대사, scope 일치 검증. 다른 CF 경로에 실제 SELL 붙이기 금지 |

운영 producer 회귀는 기존 함수·serializer·writer·compactor·reader를 통과시킨 통제 입력으로 작성한다. 완성된 evaluator row를 수동 주입하는 테스트만으로 공급 계약을 닫지 않는다. KRX/NXT/SOR와 등록된 프리마켓/정규장/통합 애프터마켓 scope를 검사하고, 한 route의 성공을 다른 scope 지원 증거로 대신하지 않는다. 실제 Kiwoom 요청/파서 변경이 필요하면 공식 reference gate를 먼저 수행한다. 본 계획 자체는 새 broker 조회를 요구하지 않는다.

기존 운영 모델 proof가 없는 이유를 원천 소실·지원 입력 없음·미완료 terminal·표본 부족·오차 검증 실패로 나눈다. production chain을 검증하지 못한 상태는 단순 자연 표본 대기가 아니다. 과거 불가역 자료와 미래 정상 생성은 독립 판정한다.

## 13. 탐색 가설·판단 차이·예산 집중

후보는 기존 등록 공간만 사용한다. 새 전략·임의 score hurdle·수량 증가·추가 collector를 만들지 않는다. 먼저 incumbent/candidate가 어떤 입력에서 다른 행동을 내리는지 기존 evaluator로 확인한다.

| evaluator | 검증할 가설 | 비교 범위·비용 |
| --- | --- | --- |
| machine | 기존 bounded threshold/hierarchy의 변경이 비용 후 손실 진입을 줄이거나 수익 기회를 더 선택하는가 | 자신의 전체 보존 attempt 분모에서 BLOCK/RECHECK/ENTER_NOW 차이. 실제 실행 가능한 frozen plan·동일 후행 guard로 비교; compact screen 모집단과 혼합하지 않음 |
| compact | machine ENTER_NOW 이후 incumbent PASS→candidate VETO가 손실을 줄이고, incumbent VETO→candidate PASS가 순수익 기회를 늘리는가 | 같은 frozen screen/quantity/budget/holding owner. 오판 회피 이익과 놓친 수익을 모두 포함; VETO를 실제 무손실 성과로 오인하지 않음 |

compact의 `PASS/PASS`, `VETO/VETO`는 동일 판정으로 분모에 보존하고 경제적 선택 Δ는 0이다. 추론비용 차이는 계속 차감한다. `PASS/VETO`, `VETO/PASS`는 별도 순익·tail·노출·체결 참여율 진단으로 표시하되, 변경 사례만 뽑아 전체 EV나 승격 분모를 만들지 않는다. CAUTION/RECHECK는 당시 후속 결정·시간/상태 계약이 지원되는 경우에만 비교하고, 지원되지 않으면 명시 scope 제외한다. 가상의 즉시 진입으로 바꾸지 않는다.

machine 비진입에서 새 compact 호출을 합성하지 않는다. machine 변경에 의해 처음 ENTER_NOW가 되는 기회는 기존 후행 compact 계약까지 검증 가능한 경우에만 전체 경로 경제성으로 평가한다. AI 결과가 없거나 미래 AI 상태가 미정인 경로는 stage 진단/unsupported로 남기고 전체 매매 EV로 승격하지 않는다.

초기 후보는 이미 등록된 compact v3 대비 opportunity v2 및 기존 machine 후보로 한정한다. 별도 후보 확대는 기존 learning에서 실제 판단 차이와 지원 coverage가 확인된 뒤에만 검토한다. 의미가 같은 rule·prompt의 중복 평가는 재사용한다. 과거 지원 결손만 있는 scope는 provider 평가를 건너뛰고 source/model blocker만 갱신한다.

후보를 바꾸는 근거는 learning의 판단 차이·양/음수 비용 후 결과·지원 coverage다. holdout 결과를 본 뒤 후보·컷오프·scope를 바꾸지 않는다. 중복 판단만 반복되면 이번 결과를 `no_decision_change` 진단으로 남기며, 표본/모델 조건을 채우지 못한 상태를 `valid_no_edge`로 바꾸지 않는다. 기존 provider request budget·retry·resource 상한은 유지한다.

## 14. 연구값·모델 검증·승격을 분리하는 계산

1. **모집단과 admission:** 전체 관측·정상 응답·지원 계획·운영 모델 유효·paired comparable·독립 holdout·승격 scope 수를 단계별 표시한다. 각 제외는 first blocker 한 건으로 세고 중첩 진단은 별도다. 비교가 없는 지표는 null이다.
2. **동일 자본:** 각 pair는 같은 frozen 총수량·예산·owner·후행 guard를 사용한다. owner 승인 자본을 변경하거나 서로 다른 owner 자본을 임의 합산하지 않는다. PASS/VETO 비교의 정상 미진입 arm만 순익/노출 0으로 계산한다.
3. **경제성:** arm별 비용 후 순익 KRW·EV와 paired Δ, 일별 순익 Δ, worst/ES10 tail, reserve/보유 KRW-minutes, 체결 참여율을 기존 계산으로 산출한다. 금액 순익과 예산 정규화 EV를 나란히 표시하며 단순 수익률 합계를 EV로 쓰지 않는다.
4. **자본 충돌:** 전체 eligible 시간순 기회를 기존 owner allocation으로 대사한다. 현재 비중첩 one-position 모델에서 overlap은 일별 자본 비교 불가로 표시하고, 충돌한 기회를 몰래 삭제해 승격하지 않는다. 비중첩 subset 값은 범위가 한정된 진단이며 전체 일별 이익이 아니다. 충돌 빈도·차단 금액/coverage가 실제 병목으로 확인될 때만 기존 owner의 allocation replay를 보완한다.
5. **모델:** actual calibration→선행 chronological model holdout→후속 candidate learning→candidate freeze→별도 forward holdout 순서를 유지한다. tolerance는 기존 실제 calibration 오차에서 고정하고 holdout 실패 후 늘리지 않는다. model hash·exit/cost scope 변화는 해당 proof를 무효화한다. scope key는 경제·실행 차이에 영향을 주는 기존 계약을 보존하며 표본을 늘리기 위해 route/owner를 합치지 않는다.
6. **보수적 하한:** 기존 `min(base Δ, stress Δ) − changed-decision 두 arm 실측 오차 penalty − 추론비용`의 평균을 사용한다. 이는 관측 오차/stress envelope이며 통계적 신뢰구간·실현 이익·인과적 개선이 아니다. inference의 reviewed operator zero-cost receipt가 현재 근거이며 무료 vendor 가격으로 해석하지 않는다. 비영 비용은 측정 token·승인 환산 provenance가 있어야 지원한다.
7. **연구와 승격:** 독립 운영 모델이 검증된 지원 pair는 candidate 표본 미달이어도 계산값·표본·coverage를 표시하고 `promotion_ready=false`로 남긴다. 운영 모델 미검증 path return은 별도 진단이며 승격용 EV가 아니다. model/sample/source gap과 측정된 음수 결과를 섞지 않는다.

compact의 scope/route별 learning20·holdout20·holdout source days2·response coverage1.0 및 양수 paired/일별 순익·stress·tail 조건은 유지한다. machine은 자신의 기존 source/전체 분모·chronological holdout·full-cost 및 paired/tail 승격 계약을 유지한다. compact 기준으로 machine 기준을 대체하지 않는다. 모델과 후보 holdout 날짜·unique evaluation keys·consumed 상태를 기존 보고서에서 함께 검증한다.

## 15. 후보 0의 설명·최종화·실제 성과

기존 상태 계약을 사용하되 reason/owner/closure가 첫 탈락 경계와 일치하도록 보완한다. 새로운 상태명을 도입할 때는 현재 모든 reader/verifier와 함께 변경하고, 원천 이벤트 보존 없이 표시만 바꾸지 않는다.

| 결과 | 판단·next owner | closure test |
| --- | --- | --- |
| source_gap | plan/stop/cost/census/identity 전달 결함 → 해당 기존 producer | 지원 운영 입력이 writer/consumer를 거쳐 계산까지 도달 |
| transport/semantic invalid | 정상 screen 비교가 없는 응답 오류 → AI trace/quality owner | 정상 응답 admission·오류 보존·retry/fallback 계약; 시장 scope 부족으로 오표기 금지 |
| unsupported_scope | 실제 모델 미지원 exit/partial/queue/state 또는 미지원 자본 충돌 → replay/allocation owner | 근거 있는 지원 계약·실측 검증 또는 범위 한정 제외 |
| pending | 유효 owner path가 있으나 terminal/평가 receipt가 미완료 → 해당 terminal/evaluation owner | native terminal·완료 비용 또는 정상 평가 receipt 도착 |
| insufficient_sample | 미래 생성 계약과 지원 모델은 정상이나 독립 표본 미달 → 기존 자연 acceptance owner | 기존 표본·coverage·chronology 충족 |
| valid_no_edge / risk failure | 독립 비교가 완성됐으나 비용 후 하한≤0 또는 기존 tail/stress 실패 | 계산값·검증 분모·조건별 실패를 보고하고 incumbent 유지; 결손과 구분 |

AI 오류는 기존 taxonomy가 허용하는 `source_gap` 하위의 구체 transport/semantic reason 등으로 표현할 수 있다. 오류만으로 broker route가 unsupported라고 보고하지 않는다. blocker owner를 모두 실행 모델 owner로 뭉치지 않고 최초 누락 writer/normalizer/model owner로 지정한다.

calibration은 phase·execution/handoff 상태·경제성 상태를 별도 표시한다. finalize 완료 뒤 `source_prepared`라는 준비 상태를 완료 headline으로 사용하지 않는다. exit0은 인계 성공이며 EV 성공이 아니다. compact-only 결과는 machine 평가가 갱신되지 않았음을 계속 표시한다.

검증 후보는 기존 dated publisher→consumer/Daily→PREOPEN reader→intraday loader로 전달한다. source/hash/date/scope/holdout 오류는 기존 안전 계약으로 차단하며 유효 incumbent만 carry한다. 발행된 후보와 실제 issued version이 다르면 실적 귀속은 issued version을 따른다. 기존 joint machine+compact 적용 버전·owner·episode dedup, rolling20 completed source days/cumulative completed 비용 손익을 재사용한다. partial/held/source-invalid는 완료 손익에 넣지 않는다. 실제 순익은 성과이고, 동시 시장·자본·선택 차이를 통제하지 않은 전후 순익 차이를 인과적 개선이라고 부르지 않는다.

## 16. 실행 순서·최소 검증·다음 장전 준비

| 순서 | 기존 모듈의 최소 보완 | 필수 회귀·증거 | 종료 구분 |
| --- | --- | --- | --- |
| O0 현재 계약 대조 | 최신 selected release·관련 producer 세션·CI 완료 증거 확인 | 코드/자연/선택/적용 상태 표, 실제 잔여 결함 목록 | 완료 부분 재작업 없음 |
| O1 공급·분류 | §12의 first-boundary 결함과 §15 오류 분류/상태만 수리 | 운영 producer→serialization→writer→projection→admission; 정상 route/scope와 손절/비용/census 누락 negative | 통제 계약 완료와 자연 유입 대기 분리 |
| O2 계산·연구표시 | 기존 metric의 지원 pair·판단 차이·표본 미달 표시 연결 | PASS↔VETO, 동일 판정, inference 비용, frozen budget/qty·reserve, overlap null, 실제 비용 계산 | 계산 가능/모델 미검증/표본 미달 구분 |
| O3 독립 후보 선정 | 기존 model/candidate chronology·scope/hash 검증 | 선행 model holdout, 독립 candidate holdout, 오염·모델 변경·tail/stress negative, 조건 충족 active positive | fixture는 경로 검증만 |
| O4 정책·소비 | finalize headline과 기존 소비 receipt 결속 | active/carry/invalid incumbent, stale/hash/scope/holdout 실패, dated PREOPEN/loader·후행 strict | 코드 인계와 실제 PID 분리 |
| O5 제한 갱신 | 리뷰 통과 후 승인된 실행 범위에서 변경 family/summary만 재생성 | 같은 입력 재사용·provider0·raw 재스캔0, 보호 원천/다른 정책 불변, 새로운 정책과 최종 해시 | 준비 정책과 신규 후보 여부 명시 |
| O6 자연 수용 | 기존9/21 stable owner에서 향후 운영 자료 확인 | 새 plan/census·model proof·경제값→독립 후보→실제 소비→완료 비용 손익 | 미래 자연 OPEN |

O1–O4는 데이터가 없는 휴장에도 통제 회귀로 닫아야 한다. 실제 운영 함수가 생성한 지원 입력으로 계산·상태 전이·활성 정책 생성·loader 소비가 작동해야 하며, 모든 입력을 unsupported/inactive로 만드는 구현은 통과가 아니다. 합성 broker/fill/terminal evidence로 정상 writer/조인 계약을 검증할 수 있지만 자연 수익·실제 주문 실적으로 보고하지 않는다.

기존 테스트 중 quality/trace·sizing plan·entry split/strategy replay·compact·calibration·policy/consumer/live loader·wrapper/strict의 영향 계약만 선택한다. 별도 benchmark·전수 raw replay·새 테스트 family를 만들지 않는다. 코드 구현 때 필요한 compile/pytest·wrapper bash syntax·diff check, 문서 parser만 실행한다. provider 호출 없이 계산/소비 fixture를 검증하고 실제 유료 후보 실행은 기존 admission과 승인된 예산을 따른다.

9/21 장전에는 현재 확인된 incumbent carry를 기본 준비 결과로 둔다. 휴장 중 자연 자료·독립 holdout이 새로 생겼다고 가정하지 않는다. 수리만으로 양수 후보나 그날의 EV 개선을 보장하지 않는다. 이후 자연 입력에서 지원 계산값이 먼저 나오고, 독립 검증을 통과하면 기존 거래일 계산에 따른 다음 effective date 정책을 발행한다. 조기 PREOPEN 확정·bot 재시작·주문은 이 계획 작성에서 수행하지 않는다.

## 17. 유지 가치·완료 기준·불필요한 누적 방지

공통 finalize는 정책 발행·소비의 필수 경로로 유지한다. machine/compact 탐색의 가치는 판단 차이의 비용 후 결과로 평가한다. 유효 비교에서 음수/no-edge가 확인되어 불리한 변경을 막는 것도 결과이며, 양수 정책 개수만으로 가치를 판단하지 않는다.

동일 source/code/model/contract/prompt/input hash에서는 기존 평가를 재사용한다. 새 지원 입력·model proof·candidate revision·필수 consumer 변경이 있을 때만 영향 scope를 평가한다. 같은 결손21건의 반복 실행·새 history 파일·반복 workorder는 만들지 않는다. 상위 요약은 기존 날짜별 결과와 owner/closure를 참조한다. 무조건 주기 확대·후보 확대·비싼 병렬 탐색은 하지 않는다.

후속 구현 완료 조건은 지원 운영 producer의 미래 저장·소비 계약, 실제 경제성 계산, 독립 선정과 active/carry 소비, 정확한 후보0 분류가 의미 있는 회귀로 검증되는 것이다. 자연 acceptance OPEN은 새 자연 입력·운영 모델 독립 실측·후속 후보 표본·정규 적용·완료 비용 손익에 한정한다. 실행 가능한 미완료 코드나 입증되지 않은 공급 계약을 자연 대기로 숨기지 않는다.

지원 분모에서 실제 판단 차이가 없으면 해당 후보의 추가 호출은 진단/재사용으로 제한한다. 지원 자료가 쌓였는데 독립 검증이 no-edge라면 incumbent를 보존하고 learning 가설만 재검토한다. source/model gap이 계속되면 최초 producer 수리를 남기고 provider 반복 평가를 중단한다. 표본 수·기준을 임의 완화하거나 지원 밖 경로의 손익을 섞어 유지 가치를 만들지 않는다.

장후 산출물 정리는 구현·소비 검증 이후 별도 승인 범위에서 한다. 현재 reference/model/holdout·정책/PREOPEN·실제 버전 손익·raw/custody·rollback 증거는 보존한다. 현재 consumer가 읽지 않고 regeneration lineage에서도 필요하지 않은 중복 provisional/실패 임시물만 path/hash 목록을 확인해 삭제한다. 본 계획 변경에서는 산출물을 삭제하지 않는다.

이번 수정의 검증 범위는 문서 link/owner/권한·계산/승격 분리·날짜/원천 근거 review/fix/re-review와 print-only parser·diff check다. 코드 테스트·provider 호출·재생성·배포·외부 sync는 수행하지 않는다.

## 18. 후속 구현·배포·제한 재생성 결과

사용자의 후속 구현 승인에 따라 §11–§17의 실행 가능한 항목을 기존 모듈에서 종결했다. 최종 코드 commit은 `411ec0efdf993ec11e36b3fc79b78a5a7a36a6e1`, 선택 release는 `compact-economic-optimized-reviewed-20260919-411ec0efd`다. 이 release는 앞서 배포된 WS 경제성 보완 commit을 포함한다. selector 전환은 future invocations only이며 bot 재기동·주문·조기 PREOPEN은 수행하지 않았다.

- `natural_contract_invalid`를 시장 scope 결손으로 분류하던 오류를 수리했다. 미래 정상 producer는 provider/model·transport·semantic first blocker를 보존하고, 과거 v4/v5 projection은 frozen `natural_contract_evidence`만 사용해 v6로 제한 migration한다. raw trace/payload를 다시 읽거나 과거 응답을 복원하지 않는다.
- 후보 비교는 전체 paired 분모의 changed/unchanged count·rate를 표시하고, 독립 운영 모델이 지원되는 경우 표본 미달이어도 비용 차감 연구 비교와 보수적 ΔEV 하한을 표시한다. 승격 primary는 기존 `robust_paired_delta_ev_lower_bound_pct`이며 모델 ΔEV가 실제 이익이 아님을 명시한다.
- prepare/evaluate/finalize artifact state와 경제 상태를 분리했다. 최종 calibration headline은 `postclose_finalize_ready`, 경제 상태는 `source_contract_blocked`다. terminal handoff 성공은 consumer receipt가 소유한다.
- blocker별 첫 owner/closure를 response contract, label identity, route scope, execution model, sizing/owner replay로 분리했다. SOR 자체는 지원 route이며 이번 결과에 route unsupported가 없다.

검증은 운영 pre-AI producer→pipeline census→owner replay→compact projection/비용 비교, 독립 model/candidate holdout, active/carry policy와 loader, stale/hash/scope failure를 포함한 영향 범위 590건 PASS를 기준으로 했다. 다른 세션의 후속 commit을 재배치한 뒤 관련 295건 PASS, 최종 분류·migration·물리 release 반복 검증도 PASS했다. Python compile, wrapper syntax와 diff check를 통과했다. 합성 fixture는 경로 검증이며 자연 수익 증거가 아니다.

source9/17→publication9/19→effective9/21의 제한 재생성 결과는 screen21, source gap21, eligible0, comparable0, provider 호출0이다. 배타적 first blocker는 stop10·transport8·semantic1·label identity2다. projection v6 migration은 `raw_not_read=true`이며 보호 raw의 size/mtime은 불변이다. 후보0 상태는 `source_gap`; ΔEV·일별 순익·보수적 하한·실제 이익은 null이고 승격 scope는 없다.

9/21 dated policy는 `entry_machine_auxiliary_compact_v3` incumbent carry다. machine 정책과 비compact scope9를 보존했고 bundle은 `fb4870b8ab479897c7580d79a92acb2595889c2d7c95b75087bcef6cfb6f74c5`다. consumer는 같은 bundle/effective date를 연결했고 compact scoped strict verifier는 PASS, whole native chain DONE은 false다.

O0–O5의 실행 가능한 구현·검증·배포·제한 재생성은 완료했다. O6은 기존 stable owner `KiwoomCommonHealthOpportunityCostAcceptance0917`에 남긴다. 남은 사실은 다음 영업일의 정상 plan/stop/cost/census 생성, 실제 scope의 선행 운영 model holdout, 독립 prompt 표본, 정규 PREOPEN/PID issued version, joint-version COMPLETED valid cost/profit다. 과거21건을 반복 실행하지 않으며 미래 정상 입력이 들어오면 기존 evaluator가 비용 후 연구값을 먼저 산출한다.

증거는 [구현 리뷰](../audit-reports/2026-09-19-compact-economic-optimization-implementation-review.md), `tmp/compact-economic-optimization-20260919/deployment.json`, `regeneration.json`, `before-regeneration/manifest.json`이다. 배포·scoped PASS·carry 정책은 양수 EV나 실제 이익을 증명하지 않는다.

## 19. 후속 재리뷰·산출물 정리

후속 재리뷰에서 계산·승격 코드의 새 결함은 없었다. 실제 consumer와 Git checklist 사이의 이전 bundle handoff만 현재 `fb4870b8…`로 재결속했다. 현재 v6가 직접 가리키는 v5·v4 generation, 원천·정책·consumer·rollback·검증 증거를 보존하고 미참조 generation 및 중복 임시 로그 25개를 삭제했다. 삭제 뒤 영향 범위 333건과 compact scoped strict/consumer 검증을 통과했다. commit `8143121b6005b908520fc3c8dca5160f82c50d2f`, immutable release `compact-economic-cleanup-reviewed-20260919-8143121b6`를 future invocation으로 선택했다. 상세 목록과 hash는 [구현 리뷰](../audit-reports/2026-09-19-compact-economic-optimization-implementation-review.md) 및 `tmp/compact-artifact-cleanup-20260919/manifest.json`, `deployment.json`이 소유한다.

## 20. 현행 재설계 판단과 기준선

현재 선택 영수증 기준 release는 `rising-missed-economic-authority-20260919-8dea83503`, source commit `8dea83503d7a18659af34212e61784c5e95593db`다. 실제 PID 소비는 다음 정상 기동 대기 상태다. 작업공간은 다른 세션 변경이 누적돼 있으므로 구현은 선택 release와 `origin/main`의 실제 호출자를 기준으로 별도 worktree에서 시작한다.

2026-09-17 원천의 현행 compact 결과는 screen21·source 제외21·경제성 적격0·paired 비교0·provider 호출0·EV/일별 순익 차이 null·incumbent 보존이다. 가격경로 진단14건의 source-quality-adjusted return `-0.25559409535%`는 `diagnostic_price_path`이며 실제 비용 후 paired EV가 아니다.

과거 `handoff` receipt는 존재하지만 현재 scoped verifier는 네 final summary를 stale로 판정한다. 구형 `threshold_cycle_2026-09-17.json`과 `threshold_cycle_ev_2026-09-17.json`은 없고, 현행 `runtime_approval_summary`와 control tower에는 복제 section `compact_auxiliary_economic_tuning`이 없다. 이는 기다리면 채워질 표본 문제가 아니라 Daily/EV 공통 튜닝 퇴역 뒤 coordinator·verifier가 옛 소비 계약을 유지한 구조 결함이다. 과거 PASS를 현재 closure로 재사용하지 않는다.

재설계 결정은 다음과 같다.

1. compact AI 경제성 탐색 owner는 `compact_auxiliary_paired_replay` 하나다.
2. `ai_decision_quality`는 source label producer이며 후보 선택 권한이 없다.
3. `ai_action_outcome_calibration`은 필요한 기계 action/outcome 진단과 비용 reference 기능만 보존한다.
4. `--postclose-phase` 네 단계와 `compact_summary_handoff` 복제 계약은 퇴역한다.
5. 정책 발행은 기존 `mechanistic_entry_runtime_policy` 한 곳, 장중 소비는 기존 `entry_setup_live_policy` 한 곳을 유지한다.
6. runtime summary·tower·checklist·verifier는 canonical paired report·dated policy·PREOPEN/PID receipt를 직접 읽는다.
7. 구조 원천이 닫히기 전에는 candidate provider 호출을 하지 않는다.

## 21. 목표 흐름과 단일 책임

```text
ai_decision_trace/payload + atomic plan/stop + owner execution facts
                              │
                              ▼
                    ai_decision_quality
                  (label/source receipt only)
                              │
                    admission state machine
                              │ eligible generation changed
                              ▼
              compact_auxiliary_paired_replay
         (only prompt candidate evaluator and selector)
                              │
             ┌────────────────┴────────────────┐
             │ gap/pending/no-edge             │ validated edge
             ▼                                 ▼
       incumbent carry             mechanistic_entry_runtime_policy
             └────────────────┬────────────────┘
                              ▼
                 PREOPEN/bootstrap exact-date check
                              ▼
                    entry_setup_live_policy
                              ▼
             issued prompt/PID/order/fill/cost outcome
                              │
                              ▼
       runtime_approval_summary/tower/checklist/verifier
                    (direct receipt projection)
```

| Owner | 단일 책임 | 금지 책임 |
| --- | --- | --- |
| trace·quality producer | exact input/response/identity/label 보존 | 후보 생성·경제성 승인 |
| plan·execution producer | 당시 stop·수량·비용·route·attempt/order/fill/terminal 보존 | 결손을 현재값 또는 0으로 합성 |
| compact evaluator | 동일 frozen input의 incumbent/candidate paired 계산·chronology·선정 | runtime env·주문·PID 권한 |
| dated publisher | 통과 scope만 발행하고 나머지 incumbent 보존 | EV 재계산·표본 기준 변경 |
| live loader | exact effective date·scope·bundle·prompt 검증과 issued-version trace | 장후 후보 선택 |
| direct summaries/verifier | 원 결과·정책·소비 receipt 대조 | section 복제·후보 재평가·공통 정책 생성 |

## 22. 구조 원천 보완 순서

구조 수리는 provider 탐색보다 먼저 수행한다. 과거 2026-09-17 결손21건은 고정 제외하고 미래 writer 계약만 보완한다.

| 우선순위 | 결손과 현재 수량 | 최소 producer 보완 | closure test |
| --- | --- | --- | --- |
| S0 | exact stop/plan 결손10 | pre-AI 시점의 loaded holding/exit policy, stop distance, 진입가, 수량, 예산, owner, route와 atomic seed/hash를 기존 plan writer에 함께 기록 | 한 자연 screen이 writer→projection→owner replay→paired cost 계산까지 같은 seed/hash로 도달 |
| S1 | transport invalid8·semantic invalid1 | 실제 provider request/response receipt, timeout 지점·elapsed, schema/version, parse disposition을 lossless trace에 보존 | 정상 응답은 admission되고 실패 응답은 정확한 reason으로 제외되며 PASS/VETO로 합성되지 않음 |
| S2 | venue/session identity 충돌2 | canonical context·trace·label·owner seed의 code/venue/session/route key를 일대일 결속 | 중복·충돌 negative와 정상 KRX/NXT positive join 모두 통과 |
| S3 | execution projection coverage 미입증 | initial owner parent→attempt→broker order→full/partial/no-fill→terminal의 retained/excluded census와 원자 plan receipt 보존 | source_gap과 실제 zero opportunity를 구분하고 census conservation PASS |
| S4 | 선행 운영 모델 holdout 없음 | 실제 제출·체결·COMPLETED valid cost/profit에서 scope별 model calibration과 독립 holdout 생성 | prompt learning보다 이른 model version·holdout·오차/tolerance·tail receipt가 유효 |

S0–S4 중 필요한 필드가 이미 생산되는데 중간 projection에서 손실되는지 먼저 확인한다. 기존 writer 보완으로 끝낼 수 있으면 새 collector·DB·report family를 만들지 않는다. Kiwoom 요청·응답 자체를 바꿔야 하는 결함이 발견된 경우에만 공식 API reference gate를 별도 적용한다.

## 23. EV 탐색 로직 최적화

탐색은 넓은 grid가 아니라 경제적 의사결정 차이를 만드는 등록 후보에 집중한다.

### 23.1 탐색 전 admission

provider 호출 전 다음 조건을 모두 확인한다.

- exact natural machine `ENTER_NOW` screen이며 AI 비호출 BLOCK/RECHECK가 아님
- source label·input/prompt/schema·venue/session/route·plan/stop·cost hash 유효
- incumbent issued response가 transport/semantic contract를 통과
- 운영 execution model이 해당 scope와 exit/cost/capital 계약을 지원
- 같은 evaluation key·prompt·model·cost generation의 기존 결과가 없음

하나라도 실패하면 candidate를 호출하지 않고 최초 blocker와 owner를 기록한다. 현재처럼 경제성 적격0이면 provider0이 정상 결과다.

### 23.2 후보 생성과 예산 집중

- 후보는 기존 optimizer registry에 등록된 distinct prompt revision만 사용한다.
- incumbent와 byte-identical하거나 판단이 항상 같은 self-comparison은 후보 예산에서 제외한다.
- scope별 한 번에 하나의 challenger만 동결한다. 같은 scope에서 병렬 후보를 늘리지 않는다.
- deterministic schema·prompt rendering·기존 response cache 검증을 먼저 하고, 실제 판단 차이가 가능한 row에만 provider budget을 사용한다.
- 새 eligible generation·candidate hash·model hash·cost hash가 없으면 평가를 재사용한다.
- 기존 `max_new`, timeout, retry, provider budget을 유지한다. 속도를 이유로 source/holdout/cost gate를 완화하지 않는다.

### 23.3 비교 분모와 목적함수

동일 frozen row에서 incumbent와 challenger의 PASS/VETO를 비교한다. 동일 판정은 Δ0으로 분모에 남기고 판단이 달라진 row만 별도 효과 분해를 제공한다. partial·custody censored·unsupported exit·source gap은 0손익으로 넣지 않는다.

연구 표시는 다음을 모두 제공한다.

- incumbent/candidate cost-adjusted paired EV와 ΔEV
- robust paired ΔEV lower bound와 model-error penalty
- 동일 자본·수량 계약의 관측일별 순익 차이와 worst-day 차이
- fill participation·capital exposure/reserve 차이
- tail/severe-loss/stress 차이
- runtime inference cost 차이
- learning/holdout별 표본·source-day·response coverage

KRW 일별 순익은 수량·자본·동시 노출 계약이 있을 때만 계산한다. 없으면 수익률 진단과 `null + reason`을 보존한다. 승격 primary는 기존 `robust_paired_delta_ev_lower_bound_pct`를 유지하며 양수 paired EV·양수 일별 순익·tail/stress 비악화·독립 holdout·운영 모델 검증을 모두 요구한다.

### 23.4 중단 규칙

- source/model gap: 즉시 평가 중단, producer owner로 반환
- eligible은 있으나 learning/holdout 미달: `insufficient_sample`, 추가 자연 입력 대기
- 독립 holdout에서 lower bound≤0 또는 tail 악화: `measured_no_edge`, incumbent 보존 후 같은 후보 재호출 중단
- validated edge: 해당 scope만 dated publisher로 전달
- 후보가 판단 차이를 만들지 않음: `no_decision_delta`, 새 가설 전까지 휴면

## 24. 이벤트 기반 실행과 상태 계약

정기 wrapper가 매일 후보 탐색을 강제하지 않는다. 저비용 source/label materialization은 유지하고, evaluator는 다음 fingerprint가 바뀔 때만 실행한다.

`source_generation + eligible_population_hash + incumbent_prompt_hash + candidate_prompt_hash + execution_model_hash + cost_contract_hash + promotion_contract_hash`

상태는 다음 다섯 단계로 제한한다.

| 상태 | 의미 | 허용 동작 |
| --- | --- | --- |
| `blocked_source` | exact plan/response/identity/census 결손 | producer receipt 갱신만; provider 금지 |
| `waiting_model_or_sample` | source는 유효하지만 model proof·maturity·표본 미달 | 자연 누적·terminal 갱신; 후보 재호출 금지 |
| `ready_to_evaluate` | 새 독립 eligible generation과 동결 후보 존재 | bounded candidate evaluation 한 번 |
| `evaluated_hold` | no-edge/risk/no-decision-delta | incumbent 유지, 같은 fingerprint 재실행 금지 |
| `validated_edge` | 모든 승격 gate 통과 | 해당 scope 정책 발행·다음 PREOPEN 인계 |

부분 실패는 기존 atomic checkpoint를 사용한다. 성공한 pair를 중복 호출하지 않고 실패 key만 다음 허용 실행에서 재개한다. source generation이 바뀌면 기존 learning cutoff와 consumed holdout을 이동하지 않는다.

## 25. 정책·장중 소비·최종 인계 단순화

`compact_auxiliary_paired_replay.finalize`는 평가 결과를 다시 계산하지 않고 canonical paired artifact를 검증한 뒤 기존 optimizer·`mechanistic_entry_runtime_policy`·consumer를 한 번 호출한다. 정책은 `data/runtime/mechanistic_entry_policy/policy_<effective_date>.json` 한 곳에 발행한다.

- `validated_edge`: 통과 scope만 후보 prompt로 변경
- `evaluated_hold`·`waiting_model_or_sample`·`blocked_source`: 유효 incumbent carry
- incumbent도 무효: publication/apply 차단

incumbent carry는 새 EV 개선이나 runtime mutation으로 집계하지 않는다. PREOPEN/bootstrap은 effective date·source hash·bundle·scope·prompt hash를 검증하고, 장중 loader는 실제 issued prompt/version/bundle/PID를 trace에 남긴다. 실제 성과는 이 issued version을 기준으로 COMPLETED valid cost/profit에 귀속한다.

별도 `--postclose-phase handoff`와 `compact_summary_handoff_<source-date>.json` 신규 생성은 제거한다. runtime approval summary와 control tower는 canonical paired artifact·dated policy·PREOPEN/PID receipt를 직접 읽고 자신의 schema 안에서 상태만 투영한다. verifier는 원 artifact의 content hash와 직접 소비 receipt를 대조하며 삭제된 Daily/EV 파일이나 복제 section을 요구하지 않는다. verifier는 어떠한 summary도 수정하지 않는다.

## 26. 구현 패키지와 리뷰 순서

| 패키지 | 변경 범위 | 핵심 검증 |
| --- | --- | --- |
| T0 기준선 | 선택 release, 실제 wrapper 호출자, artifact consumer, 현행 FAIL 재현 | 현재 네 stale summary issue와 전체 terminal 결손을 별도 기록 |
| T1 owner 통합 | wrapper의 네 `--postclose-phase` 호출과 CLI/phase coordinator 제거; 비용 reference·기계 진단 보존 | 호출 잔여0, retired alias 복원 불가, source label 순서 유지 |
| T2 direct finalize | paired evaluator의 조건부 run/finalize를 유일 진입점으로 연결 | provider는 evaluation에서만, finalize provider0, 동일 fingerprint 재사용 |
| T3 direct handoff | runtime summary·tower·checklist·verifier를 canonical paired/policy/consumer receipt로 축소 | Daily/EV 부재 정상, stale/잘못된 hash/date/scope/PID negative 차단 |
| T4 source closure | S0–S4의 실제 첫 손실 경계만 보완 | 자연 writer→projection→model→paired lossless positive/negative |
| T5 economic selection | §23 admission·목적함수·상태·중단 규칙 연결 | source gap/표본/no-edge/edge·same decision·tail·cost·holdout 회귀 |
| T6 runtime consumer | dated policy·PREOPEN·loader·issued trace 결속 | active/carry/invalid incumbent, scope별 변경, 실제 PID 미소비 분리 |
| T7 제한 재생성 | 별도 승인 후 새 유효 generation과 직접 summaries만 갱신 | 보호 원천 불변, 과거21 재실행0, provider 사용량·최종 hash·정책 명시 |

각 패키지는 구현 → self review → finding 보완 → re-review → targeted validation을 수행한다. T1–T3을 먼저 닫아 중복 실행과 깨진 handoff를 제거한 뒤 T4–T6을 진행한다. 원천 결손을 닫기 전에 후보·grid·병렬화·horizon 확대를 하지 않는다.

영향 테스트는 기존 quality/trace, plan·entry split·owner replay, compact evaluator, optimizer/publisher/consumer/live loader, wrapper, runtime summary/tower/checklist/verifier 테스트를 재사용한다. 새 테스트 family·root module·report family는 만들지 않는다. Python compile, targeted pytest, wrapper `bash -n`, `git diff --check`, 문서 print-only parser를 수행한다. provider·broker·주문·bot restart·조기 PREOPEN은 테스트하지 않는다.

## 27. 완료 기준과 자연 수용

### 27.1 코드·계약 closure

- postclose phase CLI와 wrapper 호출 잔여0
- compact evaluator 하나만 candidate provider를 호출
- Daily/EV 복제 section과 `compact_summary_handoff` 요구 잔여0
- source gap 상태에서 provider0·정책 mutation0
- 같은 fingerprint 재실행에서 pair/provider/policy 중복0
- valid edge fixture에서 해당 scope만 정책 변경, 다른9개 scope·machine policy·hard safety 보존
- direct verifier가 paired→policy→consumer→checklist를 동일 날짜·hash로 PASS

### 27.2 경제성 연구 closure

- 경제성 적격 paired count>0
- incumbent/candidate EV·ΔEV와 일별 순익 또는 명시적 null reason 산출
- learning과 forward holdout 및 source-day 분리
- 모델 오차·tail·stress·추론비용 포함
- no-edge와 source gap·표본 부족을 구분

### 27.3 자연 runtime acceptance

- 정상 PREOPEN exact-date 정책 선택
- 실제 PID가 선택 release·bundle을 소비
- 실제 issued prompt/version trace
- 적용 버전별 주문·체결·COMPLETED valid cost/profit
- rolling/cumulative 또는 post-apply window에서 비용 후 성과 확인

코드 closure, 연구 비교, 정책 발행, PID 소비, 자연 EV 개선은 각각 별도 상태다. validated edge가 없으면 incumbent 보존이 정상 결과이며 양수 후보를 만들기 위해 기준을 완화하지 않는다.

## 28. 작업목록·산출물 정리 계획

구현 시 [장후 작업목록](../audit-reports/2026-09-05-postclose-work-inventory.md)의 prepare/evaluate/finalize/handoff 네 행을 다음 실제 순서로 축소한다.

1. `ai_decision_quality` source/label materialization
2. `compact_auxiliary_paired_replay` 조건부 평가와 단일 finalize
3. `runtime_approval_summary` 직접 증거 요약
4. direct family verifier
5. 다음 checklist 및 전체 controller/finalization

`ai_action_outcome_calibration`의 남은 진단·경제성 reference 호출은 실제 호출 위치와 소비자가 있을 때만 별도 기재한다. 코드만 남고 wrapper·schedule·consumer가 없으면 활성 작업이 아니라 잔여 코드 표로 이동한다.

코드·소비자 제거와 검증이 끝난 뒤에만 regenerable `compact_summary_handoff` receipt와 미참조 provisional generation을 삭제한다. dated policy, source/paired report, optimizer/consumer lineage, PREOPEN/PID, rollback, 실제 주문·체결·custody·비용 증거는 보존한다. 삭제된 작업은 활성 목록에 이력을 남기지 않고 구현 리뷰가 삭제 manifest를 소유한다.

이번 계획 수정은 문서 변경만 수행한다. 코드·wrapper·테스트·산출물·작업목록·runtime selection은 변경하지 않으며, T0–T7 실행에는 별도 구현 지시가 필요하다.

## 29. 2026-09-20 구현·제한 재생성 결과

후속 사용자 승인으로 T0–T7의 코드·계약 구현을 완료했다. compact 후보 평가 owner를 `compact_auxiliary_paired_replay` 하나로 통합하고, main wrapper의 `prepare/evaluate/finalize/handoff` coordinator와 CLI, 복제 `compact_summary_handoff`, 21:05 전용 schedule, DONE-controller follower를 제거했다. 수동 호환 wrapper도 같은 단일 evaluator/finalizer만 호출한다. canonical paired artifact는 기존 mechanistic dated publisher, main consumer, 다음 거래일 checklist와 직접 결속되고 runtime summary·tower·scoped verifier는 이 직접 증거를 읽는다.

S0–S4는 기존 plan writer·owner replay·route admission·execution model/holdout 계약을 재사용했다. 지원 필드가 projection에서 손실되거나 정상 route가 일괄 제외되는 새 결함은 회귀에서 재현되지 않아 새 collector나 report family를 만들지 않았다. 과거 2026-09-17의 21건은 원천을 합성하지 않고 그대로 보존했다. 새 fingerprint와 `blocked_source|waiting_model_or_sample|ready_to_evaluate|evaluated_hold|validated_edge` 상태, source/model gap의 provider 0, 동일 fingerprint 재사용, scope별 승격·incumbent 보존을 evaluator와 publisher에 결속했다. 기존 live loader는 exact-date bundle/prompt/scope 검증을 유지하며 direct policy 회귀를 통과했다.

제한 재생성 결과는 다음과 같다.

| 구분 | 결과 |
| --- | --- |
| source/publication/effective | `2026-09-17` / `2026-09-20` / `2026-09-21` |
| evaluator | `blocked_source`, fingerprint `13b6f9396704900921eb6a174b93835e3ff7b17bbe20b91b92321d5ae269db67` |
| 분모 | screen21, source 제외21, 경제성 적격0, paired0 |
| 최초 blocker | exact stop/plan10, transport8, venue/session identity2, semantic response1 |
| 경제성 | incumbent/candidate/ΔEV와 일별 순익 모두 `null`; `not_available_without_owner_plan_and_portfolio_replay` |
| provider | candidate 요청0, 평가 provider 비용 USD0 |
| 정책 | 9/21 incumbent carry, 승격 scope0, bundle `6b44aaaed394f3f1835be78b2bbed828278caf0e975b1187a0812a45c88f3717` |
| 직접 소비 | paired→policy→consumer→checklist scoped verifier `PASS`; runtime summary direct evidence complete; tower pass |
| 자연 수용 | 실제 PID 소비·issued prompt·주문/체결·COMPLETED 비용 손익 미확인 |

따라서 구조적 coordinator·복제 handoff·중복 schedule 결함과 다음 장전용 정책 생성은 닫혔다. 유효 비교나 양수 EV는 도출되지 않았으며, 이는 측정된 no-edge가 아니라 과거 원천 결손이다. 양수 결과를 만들기 위해 비용·holdout·tail·표본 기준을 완화하지 않았다. 미래 자연 writer가 동일 plan/stop/response/identity와 선행 운영 model holdout을 생성한 뒤 경제성 적격 paired 분모가 생기는지는 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917` owner에서 확인한다.

검증은 관련 quality/plan/owner replay/evaluator/publisher/consumer/live loader/wrapper/summary/tower/checklist/verifier 1,015건 PASS, 별도 live-loader 경계 73건 PASS, Python compile, wrapper `bash -n`, `git diff --check`, print-only backlog parser를 통과했다. 보호 원천 `.source.json`은 재생성 전후 동일했다. 재생성 전 manifest와 결과 receipt는 `tmp/compact-ai-single-owner-20260920/before-regeneration/manifest.json`, `tmp/compact-ai-single-owner-20260920/regeneration.json`이 소유한다. 배포 commit·불변 release·선택 영수증은 최종 deployment receipt에 기록한다.
