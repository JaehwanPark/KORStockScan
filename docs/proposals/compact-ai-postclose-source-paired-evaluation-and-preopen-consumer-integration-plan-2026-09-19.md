# Compact AI 장후 원천·paired 평가·장전 소비 통합 구현계획

작성일·후속 보완일: 2026-09-19 KST. 이번 요청의 범위는 상세 개선계획 수정이다. 이전 승인으로 수행된 통합 구현은 §10의 기록이며, 이번 계획 작성에서는 코드 변경·후보 호출·장후 재생성·배포·PREOPEN 실행을 수행하지 않는다. §11–§17은 기존 evaluator의 후속 최적화 계획이며 별도 producer나 중복 계획을 신설하지 않는다.

목표는 구조적 원천 결손을 해결하고 실제 compact 보조판정 기회에서 비용 반영 EV·일별 순익 차이를 도출한 뒤, 검증된 정책 또는 기존 정책 보존 결정을 다음 거래일의 기존 장전 소비 경로까지 연결하는 것이다. 우선순위는 구조 결손 → 경제성 비교 → 소비 연결 → 중복 실행 감소다.

## 1. 근거와 현재 상태

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). `main-only`, `normal_only`, `post_fallback_deprecation`, clean baseline `2026-06-05T00:00:00+09:00` 및 기존 hard safety를 유지한다.
- 순서: [장후 작업 목록](../audit-reports/2026-09-05-postclose-work-inventory.md). 원천 준비·최초 Daily·final 품질 감사·compact 평가·최종화의 선후 관계를 보존한다.
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
| `ai_action_outcome_calibration` | 준비/평가/최종화의 공통 조정, 기존 machine 평가 및 최종 정책 발행 | 기존 CLI/함수 안에서 단계 선택·receipt 연결; 새 coordinator 모듈 없음 |
| `mechanistic_entry_runtime_policy` | 다음 거래일 단일 정책 publisher | compact 전용 publisher 추가 금지; machine·다른 scope와 기존 정책 보존 |
| 기존 optimizer·consumer·Daily·EV·tower·checklist·verifier | 동일 최종 generation의 소비·closure | 평가를 재실행하지 않고 기존 결과를 참조 |
| `entry_setup_live_policy`, `ai_engine_openai`, 기존 PREOPEN | 정확한 날짜·scope 정책 해석, 실제 발행 프롬프트 사용·추적 | 기존 loader 재사용; 주문·provider·수량·cap·안전 권한 변경 없음 |

기존 `entry_setup_paired_replay_batch --compact-only`는 부분 실행·재개용 진입점으로 남긴다. 정상 main wrapper의 독립 compact execute/finalize 호출은 공통 조정 경로로 대체한다. 독립 paired wrapper도 같은 조정 함수를 사용하며 별도 예약을 신설하지 않는다. 조정 함수는 기능 함수만 호출하고 상대 CLI/main을 다시 호출하지 않는다. 공통 lock과 내부 artifact lock의 획득 순서를 고정해 재귀·이중 잠금 대기를 피한다.

통합 구현 후 기존 calibration CLI의 단계 인자는 `--postclose-phase prepare|evaluate|finalize|handoff`다. 후속 보완은 이 진입점과 기존 함수·lock을 재사용하며 새 coordinator를 만들지 않는다.

## 3. 작업 전후·생산자 소비자 순서

| 단계 | 선행 입력 | 수행·출력 | 필수 후행 소비 |
| --- | --- | --- | --- |
| P0 경제성 reference | 원천일·기존 full-cost owner | 기존 reference-only 확보 | label·운영 replay; missing을 0으로 대체하지 않음 |
| P1 준비 | performance fact·entry split·trace/payload·sealed snapshot | 기존 control·labels materialization/reuse, 원천 receipt | 최초 Daily; 기존 앞단 위치 보존 |
| P2 admission/평가 | final source audit·P1 labels·owner operating CF·선행 model proof | 유효 scope에서만 후보 호출·paired 결과·학습/holdout, machine 기존 평가 | 잠정 calibration/후행 보고서; 확정 정책과 구분 |
| P3 최종화 | 필요한 tail 생산자 완료·현재 의존 hash | 변경된 라벨/메타데이터만 재결속, 평가 reuse, calibration·정책·optimizer·consumer 확정 | 최종 Daily/EV/runtime summary/workorder/tower/checklist |
| P4 검증 | P3 최종 generation 및 필수 handoff | 기존 strict verifier → controller DONE | 다음 거래일 기존 PREOPEN |
| P5 자연 소비 | effective-date 정책·정규 PREOPEN | loader 해석·bundle/version·실제 PID/trace receipt | 완료 실적 기반 joint applied-version 성과 |

현재 main은 앞단 quality materialization, final 감사 후 compact execute/calibration, 뒤쪽 compact finalize를 호출한다. 이를 P1/P2/P3의 한 실행 계약으로 바꾼다. **최초 Daily가 필요한 labels를 final 감사 뒤로 옮기지 않는다.** 초기 labels는 provisional 원천이며 final 감사·tail 변경 후 authoritative generation을 재확인한다.

P2는 후보 평가의 유일한 정상 provider 실행 지점이다. P3는 provider를 호출하지 않는다. P3에서 새로운 원천이 발견되면 `evaluation_deferred`와 next owner를 기록하고 해당 scope 후보를 보존/차단한다. 최종화 안에서 묵시적으로 새 평가를 시작하지 않는다. machine와 compact는 각자의 proof로 독립 판단하되 최종 날짜별 정책은 하나의 publisher가 한 번 확정한다. 미지원 compact가 검증된 다른 scope/owner 결과를 지우지 않는다.

단일 최종 발행으로 전환하기 전에 P2 이후 `--require-policy-publication`·policy 파일 대기·이전 bundle 참조를 가진 consumer를 식별한다. 최종 policy 의존 consumer는 P3 뒤로 이동하고, P2 결과만 필요한 consumer는 명시적으로 provisional report를 받는다. 이미 동결된 PREOPEN 정책은 같은 날짜의 재생성으로 덮어쓰지 않고 기존 freeze/승계 계약을 따른다. 이전 파일이 있다는 이유로 새 generation 대기를 통과시키지 않는다.

최종화는 필요한 선행 완료 후, 해당 family를 포함하는 최종 summary·workorder·tower·checklist·verifier보다 앞에 둔다. 이미 생성한 후행 요약은 해당 section/hash만 제한 갱신한다. verifier/controller 자신의 hash는 summary 입력에 넣지 않는다.

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
| CI0 계약 확정 | 선택 release/다른 세션 producer 변경 대조, P1/P2/P3 호출·lock·후행 위치 확인 | 구현돼 있는 v6/model/labels 기능 재사용, 각 결손의 owner·test 확정 |
| CI1 구조 결손 | §4의 실제 잔여 producer/consumer 결손만 보완 | 자연 writer → compact partition → seed/replay/model admission의 lossless lineage; historical loss 제외 유지 |
| CI2 공통 조정 | 기존 calibration의 단계 조정, main/paired wrapper와 부분 CLI 연결 | 초기 Daily inputs 유지, 후보 한 번 호출, finalize provider 0, 재개·동시 호출·부분 실패 회귀 |
| CI3 경제성/발행 | 기존 v6 평가·model proof·publisher·loader의 동일 generation 연결 | supported/unsupported·0/null·CAUTION·route/scope·모델 변경·holdout 오염·carry/positive fixture의 정확한 결과 |
| CI4 제한 재생성 | 리뷰·검증 후 승인된 원천일/family만 재생성, 필수 요약·strict 갱신 | 기존 원천 보존, provider 사용 근거, native EV/일별 순익 값 또는 첫 blocker, 최종 해시·정책·handoff |
| CI5 자연 수용 | 정규 PREOPEN 및 이후 자연 입력/실적 확인 | 실제 PID/issued prompt 소비·model holdout·prompt holdout·joint-version 완료 비용 후 성과 |

CI4에서 원천이 모두 결손이면 반복 재생성을 중단하고 CI1의 생산자 공급과 CI5의 자연 증거를 남긴다. 코드 통합 closure와 경제성 자연 수용 closure는 분리해 보고한다. 유효 운영 비교가 확보되면 양수 개선 또는 측정된 no-edge 모두 유의미한 결과다. 표본이나 실제 결과가 없는 상태에서 양수 개선을 보장하지 않는다.

검증은 기존 `src/tests`의 quality/entry split/strategy replay/compact batch/calibration/optimizer/consumer/policy/live resolver/wrapper/summary handoff/strict verifier 테스트 중 영향을 받는 계약만 보완한다. 합성 positive fixture는 승격 경로 검증이고 자연 EV 증거가 아니다. Python compile·해당 pytest, wrapper `bash -n`, diff check를 수행한다. 신규 root module·collector·test family·report family는 기본 금지다.

각 패키지는 구현 → self review → 보완 → re-review → targeted validation을 따른다. 배포·재생성은 별도로 승인된 범위에서만 진행한다. automation/wrapper를 바꾸는 구현 변경에서는 작업 목록·운영 문서·실제 실행일 checklist를 함께 정비한다. baseline README/runbook/Plan Rebase/prompt/AGENTS 변경은 별도 명시 요청 범위에 따른다.

전체 확인 기준:

- 최초 Daily와 후행 machine/다른 family 소비가 유지되고 원천·결과·정책 단절이 없다.
- 동일 generation 재실행은 중복 후보 호출/표본/발행을 만들지 않는다.
- 지원되는 자연 입력이 경제 평가로 들어가며 운영 모델·표본·승격 결손이 각자의 상태로 드러난다.
- 같은 예산·비용·terminal·모델 오차 기준 EV와 일별 금액 차이가 산출된다. 비교 0/source_gap은 이를 충족하지 않는다.
- 다음 거래일 검증된 후보 또는 유효 incumbent carry가 생성되고 loader가 해석한다. 실제 PID·자연 적용·실현 성과는 해당 영수증으로만 확인한다.
- final source → policy/consumer → Daily/EV/workorder/runtime summary/tower/checklist → strict verifier → controller closure를 같은 generation으로 확인한다. scoped PASS를 전체 native DONE으로 주장하지 않는다.

## 9. 이번 계획 검증 범위

이번 변경은 계획 문서 한 개다. 링크·책임·선후 순서·0/null·권한·기존 stable ID 인계 기준을 review/fix/re-review하고 `git diff --check` 및 print-only backlog parser로 검증한다. runtime/source 수정, trading 테스트, AI 호출, 재생성, 외부 sync는 수행하지 않는다.


## 10. 승인된 구현 조정

- 사용자 후속 지시가 구현·리뷰·커밋푸시·배포·제한 재생성을 승인했다. §9의 문서-only 범위는 최초 계획 작성 당시 기록이며 현재 승인 범위를 제한하지 않는다.
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
