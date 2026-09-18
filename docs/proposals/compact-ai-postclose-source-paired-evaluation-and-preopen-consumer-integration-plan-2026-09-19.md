# Compact AI 장후 원천·paired 평가·장전 소비 통합 구현계획

작성일: 2026-09-19 KST. 범위: 구현계획 문서. 이번 작성은 코드 변경·후보 호출·장후 재생성·배포·PREOPEN 실행을 승인하거나 수행하지 않는다.

목표는 구조적 원천 결손을 해결하고 실제 compact 보조판정 기회에서 비용 반영 EV·일별 순익 차이를 도출한 뒤, 검증된 정책 또는 기존 정책 보존 결정을 다음 거래일의 기존 장전 소비 경로까지 연결하는 것이다. 우선순위는 구조 결손 → 경제성 비교 → 소비 연결 → 중복 실행 감소다.

## 1. 근거와 현재 상태

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). `main-only`, `normal_only`, `post_fallback_deprecation`, clean baseline `2026-06-05T00:00:00+09:00` 및 기존 hard safety를 유지한다.
- 순서: [장후 작업 목록](../audit-reports/2026-09-05-postclose-work-inventory.md). 원천 준비·최초 Daily·final 품질 감사·compact 평가·최종화의 선후 관계를 보존한다.
- 기존 기능: [compact 경제성 계획](compact-auxiliary-ai-paired-economic-tuning-and-consumer-closed-loop-improvement-plan-2026-09-18.md), [AI 원천·라벨 통합 계획](ai-decision-quality-postclose-source-label-consolidation-and-current-evaluator-plan-2026-09-18.md). 완료된 기능은 재구현하지 않는다. 이 계획은 공통 실행 순서·generation·최종 소비를 정비하는 통합 변경이다.
- 분석 기준은 선택된 release `low-price-exploration-manual-close-reviewed-20260919`, source SHA `988baa142c9338bad9085f56f257b3422392b3b2`다. 작업 디렉터리는 관련 코드가 다르고 다른 세션 변경도 있으므로 구현 착수 때 최신 선택 release와 담당 변경을 다시 대조한다.
- 현재 날짜의 `2026-09-19-stage2-todo-checklist.md`는 없다. [9/21 체크리스트](../checklists/2026-09-21-stage2-todo-checklist.md)는 다음 거래일 인계 근거이며 현재 실행 권한을 대신하지 않는다. 구현 인계 시 실제 실행일 체크리스트에 기존 stable ID `KiwoomCommonHealthOpportunityCostAcceptance0917`의 자연 수용 기준을 보존하고 통합 변경의 실행 항목을 한 번만 연결한다. 이 문서는 새 실행 owner를 만들지 않는다.

2026-09-17 원천의 최신 compact 보고서는 2026-09-19 00:03 KST 생성이다. 실제 screen 21건, 평가 제외 21건, 이번 후보 호출 0건, 유효 비교 0건, EV와 일별 순익 차이 null, `source_contract_blocked`, `incumbent_preserved`다. 제외는 정확한 손절 거리 결손 10건, 자연 판정 계약 무효 9건(타임아웃 8·semantic reject 1), venue/session 라벨 식별 충돌 2건이다.

운영 실행 모델은 코드가 있지만 원천 projection의 coverage가 입증되지 않았고 일별 계획 3건이 무효이며 독립 선행 model holdout이 없다. 검증된 owner journal의 비교 0건은 전체 실제 주문 0건을 뜻하지 않는다.

최신 paired 보고서·consumer·9/21 정책의 해시는 일치한다. 9/21 정책은 기존 `entry_machine_auxiliary_compact_v3`를 보존하고 승격 scope는 없다. 정책 생성·인계와 실제 PID 소비·경제성 입증은 별도다.

현재 근거: [paired 보고서](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.json), [동결 원천](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.source.json), [consumer 영수증](../../data/report/main_ai_prompt_consumer/main_ai_prompt_consumer_2026-09-18.json), [9/21 정책](../../data/runtime/mechanistic_entry_policy/policy_2026-09-21.json). 구현 시 재확인하며 과거 generation을 최신 것으로 바꿔 표시하지 않는다.

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

제안할 단계 인자는 기존 calibration CLI의 `prepare|evaluate|finalize` 선택이다. 정확한 이름은 구현 시 기존 인자와 충돌하지 않게 확정한다. 기존 명령 기본 동작은 보존하고 main wrapper에서 통합 단계를 명시적으로 선택한다. 이 단계 인자는 현재 구현된 명령이 아니다.

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
