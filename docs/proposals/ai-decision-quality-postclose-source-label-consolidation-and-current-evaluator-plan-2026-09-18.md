# AI decision quality 장후 원천·라벨 보존 및 현행 evaluator 통합 상세개선계획

작성: 2026-09-18 KST. 당초 사용자 요청은 **상세계획 수립**이었으며 아래 문서 수립 경계는 당시 이력이다. 후속 사용자 구현/리뷰/수정/검증·commit/push·배포·제한 재생성 승인에 따른 완료 evidence는 [구현 review](../audit-reports/2026-09-18-ai-quality-source-label-consolidation-review.md)가 소유한다. 당초 문서 변경은 문서만 작성하며 코드·wrapper·정책·env·cron·원천·과거 산출물을 변경하거나 provider 호출·재생성·배포·기동을 수행하지 않는다.

실행 owner는 [당일 체크리스트](../checklists/2026-09-18-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`을 유지한다. 별도 튜너/스케줄/OPEN owner를 만들지 않는다. 기존 [compact CP0–CP5 계획](compact-auxiliary-ai-paired-economic-tuning-and-consumer-closed-loop-improvement-plan-2026-09-18.md) 및 [U8→U11→U12 계획](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md)을 대체 재구현하지 않고 **원천·라벨 공급과 중복 평가의 통합**을 보완한다.

## 1. 목표와 착수 기준

운영 원칙은 main-only·normal_only·post_fallback_deprecation, clean tuning 시작은 `2026-06-05T00:00:00+09:00`다. 이전 자료는 archive/audit이며 후보/승격 근거로 사용하지 않는다. source-quality preflight의 식별 가능 행/window 제외를 적용하고 hard safety·stale/conflict·주문/계좌/수량/cooldown·custody·operator override·승인 expiry를 보존한다.

오판 분석에 필요한 원본과 라벨은 보존한다. 경제성 탐색·후보 선정은 현행 기계판정기 및 machine ENTER_NOW 뒤의 compact 보조 AI evaluator에 집중한다. `scalping.ai_decision_quality --mode postclose --write`는 이 탐색의 원천/라벨 materialization을 담당하며 legacy generic BUY/WAIT/DROP 연구의 독립 승격 경로가 되지 않는다.

현재 확인한 selected release는 `entry-execution-model-revalidated-20260918`, source `f3d7dca1c7181134e9941532e6caafb92322aae1`이다. 이 값은 계획 작성 시점의 확인 기록이며 구현 시 selector/실제 consumer를 다시 확인한다. [최신 운영 모델 재검증 review](../audit-reports/2026-09-18-entry-execution-model-revalidation-and-ai-quality-cleanup.md)와 [compact 구현 review](../audit-reports/2026-09-18-compact-auxiliary-paired-economic-implementation-review.md)를 함께 적용한다. compact review의 과거 “운영 모델 미구현” 설명은 당시 이력이고, 현재 모델은 지원 범위의 실행 코드가 있으나 자연 validated scope0/source_gap이라는 상태다. 재구현과 자연 실증 대기를 혼동하지 않는다.

이미 구현된 `compact_auxiliary_paired_replay.prepare/evaluate/run/finalize`, model scope 검증, operating_arms 경제성, checkpoint·sealed holdout, 현대적 dated publisher/consumer, family summaries/strict 연결은 새 결함이 없는 한 재작업하지 않는다. model/candidate/성과 contract의 수리 대상은 정확 owner 경계에서만 수정한다. 다른 세션의 entry split source·quantity·budget·holding interpreter·검증은 보존한다.

완료 목표는 다음 네 가지다.

1. 기계 전체 판단과 실제 compact 호출의 분모·원본·라벨이 대사되고, 오판을 근거 있는 사례로 조사할 수 있다.
2. 지원 입력에서 기존 evaluator가 비용 차감 paired 결과와 독립 holdout을 계산해 선정 또는 기존 정책 보존을 완료한다.
3. 동일 최종 generation이 다음 적용일 policy→PREOPEN→장중 소비와 실제 적용 버전 성과까지 연결된다.
4. legacy 반복 출력은 실제 소비 계약 전환 뒤 제거하며 원천·경제성/holdout·rollback 증거는 보존한다.

## 2. 확인된 현황과 해석

[개별 분석](../audit-reports/2026-09-18-entry-split-final-review-and-ai-decision-quality-analysis.md)과 최신 재검증 receipt를 기준으로 한다. source9/17, publication9/18, effective9/21은 서로 다른 날짜다.

| 사실 | 해석·보완 대상 |
|---|---|
| native materialization exit0·52.893초, 기존5개 artifact 계약 PASS | 실행 정상/준비 완료. 양수 EV 탐색 성공이나 실제 적용 완료 아님. 성능 수치는 기존 로그 증거이며 새 benchmark 목표를 만들지 않음. |
| trace4578/provider63/현행 compact21(KRX11·통합 애프터마켓10)/control10/baseline14 | 서로 다른 scope/role 분모. machine non-entry 때문에 provider not called인 행을 전부 AI source gap으로 세지 않음. |
| baseline −0.25559409535%, paired 요청10/결과0 | baseline은 판단 후10분 가격 경로 proxy, WAIT/DROP 비노출0. 후보 ΔEV·실제 순익 null. 준비 단계의 결과0 자체가 실행 누락 결함은 아님. |
| generic pending25는 모두 source_quality_blocked | 단순 시간 대기로 닫을 수 없음. 원천 부적격과 horizon 미도달을 분리. |
| 098460 10:38:37의1/3/5/10분누락·20/30/60분존재, 원 가격 coverage10:51부터 | 고정 과거 window 결손. 다음 날 가격으로 채우지 않음. 원 경로 제한 backfill 또는 source-gap 제외. |
| context 시장/세션 불일치32 및 semantic/schema 실패 | overlapping exclusions이며 합산금지. original payload·정규화 projection·role 변환을 대조해 실제 불량과 false exclusion 구분. |
| latest compact21 전부 경제성 제외, 비교0/calls0/후보0, 운영 model validated scope0 | 손절/응답/경로·모델 근거 결손. valid no-edge가 아님. 코드가 있다는 이유로 자연 검증 완료로 닫지 않음. |
| AI_PASS4의 terminal lineage_gap4/admitted0/pending0 | 단순 체결 성숙 대기가 아님. 실제 final guard/submit/broker terminal owner 연결 조사. 다른 기회의 유효 CF 판단까지 전역 차단하지 않음. |
| 현행 compact9scope의9/21 dated incumbent carry 생성/family strict PASS | 준비 정책 보존을 확인한 상태. 신규 경제성 승격·PREOPEN 동결·PID/자연성과는 별도. |

이전 세션에서 참조 없는 entry Markdown30개와 과거 diagnostic baseline35개는 이미 정리됐다. 반복 삭제하지 않는다. 각 cleanup manifest와 보존 receipt를 재사용하고 이번 통합으로 새롭게 불필요해진 출력만 심사한다.

## 3. 보존·통합·제거 범위

| 대상 | 처리 | 원칙/실제 consumer 확인 |
|---|---|---|
| ai_decision_trace/payload/request/prompt/outcome 원본 | 보존 | exact bytes/hash·provider/schema/model·source time·canonical identity·custody를 유지. 기계 non-entry도 분모 보존. |
| pending 및 ai_decision_outcome_labels | 보존·필요 contract 보완 | 진단 경로와 비용/실행 가능한 economic label을 구분. 기존 raw/version을 제자리 덮어쓰지 않고 revision 및 원 provenance 보존. |
| ai_decision_quality_control | compact 원천/품질 receipt로 역할 축소 | 현재 prompt/variant/venue/session/bundle의 signature와 exclusions를 전달. report만으로 prompt/model/provider 교체 권한 없음. |
| generic baseline | 현행 case table의 진단 section으로 통합 | 기존 수익률 숫자의 의미/분모 보존, primary net metric으로 사용금지. 중복 standalone producer/write/wait는 consumer 전환 후 제거. |
| legacy ai_prompt_paired_replay 준비 | native 일상 경로에서 생산/필수 wait 제거 | `ai_quality_cycle` 등 실제 legacy reader가 존재함을 먼저 확인. surviving 명시적 offline 연구는 필요한 prepared 자료를 그 실행 경계에서 만들며 retired 권한 복원 없음. 원 labels를 기존 compact evaluator가 직접 소비. |
| retired canary candidate lifecycle materialization | 현행 native 필수 경로에서 분리 | legacy event의 history/provenance는 먼저보존. current Main 주문/완료 lifecycle은 기존 sniper/owner journal/post-sell receipt를 사용. 퇴역 adapter의0건을 새 전역 blocker로 만들지 않음. |
| compact paired/model/policy/generation/holdout ledger | 기존 owner 유지 | 현재 구현의 의미 있는 regression 및 immutable proof 재사용. 중복 producer/publisher/DB/collector 추가 없음. |
| summary/tower/checklist/strict | 같은 generation의 상태 전파 | raw counts/진단/economic/선정/carry/PID/actual을 분리. unrelated family 상태와 원 native FAIL/DONE 보존. |

정상 도달 가능한 entry-price/holding/overnight source는 필요 owner가 별도로 평가한다. 단순히 control에 없다는 이유로 퇴역 AI endpoint나 legacy lifecycle을 복원하지 않는다.

## 4. 원천·분모·라벨 계약

### 4.1 원본에서 평가까지의 대사

기존 source-quality audit가 소유하는 machine census와 attempt conservation을 사용한다. 평가 단위는 canonical evaluation attempt/decision trace이며 수집 stage 중복·재시도·같은 episode의 독립 의사결정을 구분한다. episode collapse는 경제성/성과 owner의 기존 규칙으로 수행하고 raw 시도를 삭제하지 않는다.

`machine census → source eligible/excluded → ENTER_NOW → compact provider called/not called → valid response/timeout/invalid → actual router action → final guard/submit/reject/pending → full/partial/no-fill → completed cost or open`

각 단계에 expected/observed/excluded/conflicting/unaccounted counts 및 원 근거 key를 둔다. 기계 BLOCK/RECHECK의 정상 AI 미호출, ENTER_NOW 후 합법적 preflight veto, provider timeout, 실제 수집 유실은 배타적으로 표시한다. compact 모집단을 provider 전체63 또는 generic label14와 같게 맞추려고 가짜 호출/누락을 만들지 않는다. scope별 `incumbent prompt/variant/provider/model/schema`, machine bundle·venue/session/route를 partition key로 고정한다.

### 4.2 라벨 역할과 결손 표현

원 label의 decision/payload/price-source identity를 유지하며 역할은 별도 section 또는 additive metadata로 명시한다. 이름은 구현 시 기존 schema owner의 field에 맞춘다.

- `diagnostic_price_path`: 이후 가격/MFE/MAE/first-hit/판단 taxonomy. 실제 fill/stop/cost/순익 근거로 자동 승계하지 않음.
- `economic_counterfactual`: 당시 frozen plan·route·운영 청산·비용 provenance·검증된 모델·capital 조건에서 실행 가능하게 계산한 CF. actual SELL을 다른 CF 보유 상태에 재사용하지 않음.
- `actual_completed`: real Main COMPLETED+유효 profit/cost+정확 주문/custody/version receipt. 실제 순익과 모델 ΔEV를 분리.

available horizon과 required economic/diagnostic horizon, price-window coverage/as-of/censoring, contract/result/source hashes 및 exclusion reason을 기록한다. missing cost/stop/notional/outcome/exposure는 null과 owner/closure로 남긴다. 합법적 미진입0은 router/order absence로 신규 노출0이 확정된 경우이며 미청산·원천 결손을0으로 채우지 않는다. 동일 action/verdict의 Δ0도 필요한 실행/비용 근거 없이 자동 확정하지 않는다.

원 metadata의 trace KRX와 canonical integrated venue가 충돌하면 원 request/route/equivalence contract로 판단한다. 빈 context placeholder를 유효 canonical source로 잘못 검사하는지 확인하되 null을 임의 KRX로 채우지 않는다. semantic/response schema validation 실패와 legacy→현재 역할 mapping 실패를 분리한다. prompt system-only hash와 전체 envelope hash는 서로 다른 필드이며 숫자가 다르다는 이유만으로 drift를 판정하지 않는다.

### 4.3 기존 결손의 수리 순서

1. 정확 original payload/response/hash/context와 소비 projection을 대조해 첫 탈락 경계를 찾는다. producer 또는 reader의 확인된 누락/false exclusion만 수리한다.
2. pre-veto plan/stop/quantity/budget 및 원 cost/exit 계약의 자연 생성 가능성을 검사한다. CF를 위해 guard를 우회하거나 private cache에 입력을 주입하지 않는다. 기존 Main plan/projection owner를 재사용한다.
3. AI_PASS4의 후속 owner journal/guard evidence를 대사한다. 실제 주문 증거 없는 행을 submit/reject로 추정하지 않는다. 실제 PnL attribution은 차단하고 지원 가능한 독립 CF는 별도 심사한다.
4. 고정 과거 가격창은 원 source owner에서 known missing interval만 제한 복구하거나 irrecoverable gap으로 제외한다. Kiwoom parser/continuation 수정이 필요하면 공식 API reference gate를 먼저 통과한다. 전수 재조회/현재 master·다른 route/다음날 가격 대체 금지.

## 5. 탐색·경제성·선정: 현행 evaluator 재사용

기계 전체 BLOCK/RECHECK/ENTER_NOW의 비용 후 missed-opportunity 연구와 ENTER_NOW 뒤 AI의 PASS/VETO/CAUTION/INSUFFICIENT 연구를 분리한다. AI 후보가 기계 non-entry를 승격할 수 없다. 가격·수량·budget/custody·공통 주문/손절 guard는 기존 owner의 frozen 조건이다.

기존 compact `CONTRACT` v3의 learning episode20, holdout episode20, holdout source day2, response coverage1.0 및 same-cohort/positive net Δ/positive portfolio daily Δ/tail nonworse/stress positive/runtime inference cost Δ/validated operating model/선행 model holdout 계약을 재사용한다. 계획에서 임의 tolerance·수수료·가격·승격 숫자나 새 공통 hurdle을 만들지 않는다. 구현 착수 때 실제 contract hash·별도 승인 override를 대조한다. 기계 evaluator의 기존 holdout/floor는 compact 숫자로 덮어쓰지 않는다.

비교는 동일 frozen 총수량/가격/예산·동일 후행 guard에서 판정만 변경한다. 공통 eligible 모집단에서 비용 차감 paired net/EV·금액 portfolio 일별 순익·tail·노출/reserve·full/partial/no-fill 및 참여율을 계산한다. changed-action subset은 원인 진단이며 primary 분모를 바꾸지 않는다. 겹치는 기회에 동일 자본을 중복 사용하지 않고 기존 allocation/holding/reservation owner가 지원하는 portfolio scope만 금액 성과로 표시한다. inference 비용 차이는 기존 reviewed provenance를 소비하고 미정이면 후보 선정 보류한다.

owner의 operating_arms와 exact implementation/scope/calibration/model holdout 및 완료 가용 시점을 검증한 뒤 prompt learning을 시작한다. legacy 고정 기간/고정 비용 arms는 supporting diagnostic이다. 현재 지원 모델 범위인 초기 full fill→독립 full SELL을 먼저 사용하며 partial/no-fill cancel/late fill·후속 ADD/partial SELL·누락 AI/시장 입력은 근거 없이 확장하지 않는다. 실증 모델 표본 부족은 natural validation OPEN이지 기존 executable evaluator 재구현/모든 입력 unsupported로 차단할 이유가 아니다.

학습에서 후보·prompt/input hash·scope를 고정하고 sealed chronological holdout을 한 번 소비한다. 같은 holdout을 보고 다음 후보로 재시도하거나 모델 재보정 후 fresh 검증으로 재표기하지 않는다. 실측 model error/stress·portfolio 순익·tail이 반영된 기존 proof를 그대로 재검증한다. 응답 재사용 key는 outcome-blind input/prompt/provider/model/schema이며 terminal/cost revision은 경제성만 재평가한다. inference 비용/모델 근거/현재 role이 미정이면 exact blocker와 기존 owner를 반환한다.

## 6. 실행 순서와 consumer 계약 전환

`source-quality manifest → 기존 quality source/label materialization → machine/compact case table → 기존 compact batch.prepare/run/evaluate → final calibration/optimizer/consumer → 미래 날짜 mechanistic policy → 영향 summary/tower/checklist/family strict → 정규 PREOPEN → 실제 Main/PID → 자연 결과`

첫 candidate plan을 고정하는 learning generation과 결과가 결속된 final generation을 구분한다. finalization 때문에 당일 후보 선택을 되돌려 outcome leakage를 만들지 않는다. 기존 native/follower/source-ready·checkpoint·budget·lock·publisher freeze를 그대로 사용한다. 별도 cron/서비스/collector/DB/중복 producer·engine-root module을 추가하지 않는다.

| 소유 모듈 | 제한 보완 |
|---|---|
| `scalping.ai_decision_quality` | 기존 postclose entrypoint에서 source/control/labels 공급을 유지. generic proxy는 진단 역할로 한정. ordinary current path의 legacy preparation/canary lifecycle 부수 생산을 분리하고 contract version/compatibility 명시. |
| `scalping.ai_action_outcome_calibration` | source/date/prompt partition과 machine/AI case 분모·원 label revision 결속. 통합 baseline/taxonomy diagnostics와 비용 후 primary 별도 유지. |
| `scalping.compact_auxiliary_paired_replay` 및 기존 batch | 현재 implementation 재사용. source projection/revision과 original label hash 결속·late outcome 재평가/불필요 원천 반복 읽기만 확인. |
| `scalping.micro_reversion.ai_quality_cycle` 및 surviving legacy readers | legacy 준비 artifact를 current 일상 작업 필수조건으로 요구하는 실제 reader만 분리. 명시적 offline 연구의 기존 입력/권한·checkpoint 보존. |
| optimizer/modern publisher/consumer/PREOPEN loader | 현재 proof·scope/hash/날짜/freeze/carry 경로 재검증. legacy baseline/retired lifecycle로 후보 승격 또는 기존 policy 무효화 금지. |
| wrapper/summary/strict/tests |5개 artifact를 무조건 요구하는 wait/schema contract를 source-label 역할에 맞게 같은 change set으로 전환. stale old PASS 재사용·retired output 필수화·unrelated family 성공 덮어쓰기 차단. |

실제 runtime reader까지 확인한 후 producer write를 제거한다. 호환 entrypoint는 현재 caller가 요구할 때만 유지하고 legacy builder는 surviving 명시적 offline caller가 있을 때만 그 용도로 남긴다. consumer 없이 stub/empty 성공 파일을 남겨5개 wait를 통과시키는 방식은 금지한다. 필요한 새 metadata는 기존 보고서 section/projection/cache에서 관리하고 별도 영구 저장 체계를 만들지 않는다.

자동화 변경 구현 때는 영향 운영 문서·inventory·당일 checklist를 함께 정합화한다. README/Plan Rebase/prompt/AGENTS baseline 수정은 별도 명시적 요청 범위에서만 수행한다. 이번 문서 작성은 모니터링 절차 실행이 아니다.

## 7. 상태·준비 정책·실제 성과

| 상태 | 의미와 다음 owner/closure |
|---|---|
| `valid_empty` | 대사된 모집단에 실제 eligible 기회 없음. expected/observed/conservation 일치 후 carry/fallback 소비 확인. |
| `source_gap` | payload/가격창/plan/stop/cost/terminal/hash 결손. 첫 탈락 owner의 exact 계약 수리/제외 및 producer→consumer 자연 valid proof. |
| `unsupported_scope` | 기존 운영 모델이 지원하지 않는 보유/체결/청산 scope. null과 지원 범위 명시; 임의 모델 확장으로 닫지 않음. |
| `pending` | 유효 원천에서 요구 horizon/실제 terminal만 아직미도달. fixed window end·source as-of·next owner 명시. irreversible gap을 기다림으로 숨기지 않음. |
| `insufficient_sample` | source/model/pair 계약은 유효하나 독립 episode/날짜/coverage floor 부족. existing accumulator/holdout owner로 자연 유입 대기. ETA근거없으면null. |
| `execution_deferred` / `execution_failed` | 필요한 지원 요청의 provider budget/권한/timeout/response 상태. checkpoint와 누락 key만 재개. 준비0·결과0을 유효 no-edge로 분류하지 않음. |
| `valid_no_edge` | 모델·경제성·독립 검증이 유효하고 승격 이익이 없는 경우. measured net/Δ/tail/stress와 incumbent carry 사유를 전달. |
| `candidate_selected` / `incumbent_preserved` | 동일 final proof 또는 보존 사유를 dated policy에 결속. publish/PREOPEN/PID/자연 행동/actual cost 성과는 각각 별도 receipt. |

구현 시 기존 section의 canonical status에 mapping하며 동의어 state machine을 중복 추가하지 않는다. 단계/role별 status·reason·source/effective/publication date·generation/source/label/result/model/contract/policy hash·blocker owner·closure를 함께 전달한다.

9/21 준비 정책은 장후 전체 보완 후 기존 dated publisher가 생성하는 effective policy다. 양수 proof가 없으면 유효 incumbent carry/기존 주문 fallback을 준비한다. 날짜를 현재로 바꿔 source 결손을 우회하거나 full PREOPEN을 미리 동결하지 않는다. family strict PASS가 전체 native DONE이나 PID 수용을 의미하지 않는다.

실제 적용 평가는 기존 Main journal/post-sell/평가 section에서 policy/bundle/prompt/version·scope·episode를 중복 제거하고 rolling/cumulative cost EV·순익·tail·participation·capital/reserve·model error를 구분한다. 동일 episode가 여러 label/horizon/finalization에 나타나도 순익을 반복 합산하지 않는다. partial/full·미청산·real/sim/probe/CF를 분리하고 cost-valid 실제 순익은 exposure/model error가 없다고 함께 버리지 않는다. missing 노출/오차는 field별 null·coverage·source gap으로 남긴다. 관찰 actual net은 모델 ΔEV나 인과 uplift로 부르지 않는다. 미래 자연 PID/완료 비용 성과는 별도 OPEN이다.

## 8. 구현 패키지와 의미 있는 회귀

| 패키지 | 기존 파일 중심 실행 | 완료 증거 |
|---|---|---|
| ADQ0 현황·dependency 확정 | selected release/실제 call graph/5 artifact readers·source/control/compact21 reconciliation·현재 contract snapshot | 유지·제거 consumer 목록과 owner, source/generation hashes. 이미 구현 CP0–CP5 재사용 범위 확정. |
| ADQ1 원천/라벨 결손 | exact context/schema/semantic/pre-veto/terminal journal의 확인된 최초 결손만 수리·label role/coverage/revision | 대표 불량·빈 projection·동일 route/다른 route·AFTERMARKET 사례, 원 raw 불변·exclusion 보존·public producer→consumer 회귀. |
| ADQ2 materialization 전환 | quality source/labels 유지·baseline 진단 통합·legacy/canary write/wait 분리·actual surviving reader 이행 | current source-label path 완료·legacy 직접 연구 필요 입력 보존·stale/empty stub 거부·retired stage 없는 정상 인계. |
| ADQ3 기존 evaluator 공급 | original label/source manifest→machine/compact partition·operating model 소비·revision reuse 보완 | 지원 입력 실제 계산·partial/unsupported/null·같은 verdict/changed verdict·guard block·예산/노출 conflict·CF와 actual 분리. |
| ADQ4 선정/런타임 회귀 | 기존 proof→dated policy→Daily/PREOPEN reader/장중 loader→summary/family strict | 합성 지원 양수 조건의 활성 선정/발행/소비, proof/hash/scope/holdout/freeze 실패의 carry/safety fallback. 새 publisher 없음. |
| ADQ5 과거 정리 | consumer 전환·원천 라벨 보존·policy/outcome/rollback 참조·active FD/lock 확인 | 삭제 manifest/경로/이유/SHA/원 라벨 재생성 근거와 보호 SHA 불변. 이미 정리된 자료 재작업0. |
| ADQ6 제한 결과·자연 OPEN | 승인된 source date의 영향을 받는 projection/family section만 재생성·후행 receipt | 실제 비교/후보/carry 상태·null/owner/closure·같은 final generation. 미래9/21 정규 PREOPEN/PID/자연 완료 비용 성과는OPEN. |

기존 `test_ai_decision_quality`, `test_ai_action_outcome_calibration`, `test_entry_setup_paired_replay_batch`, `test_main_ai_prompt_optimizer/consumer`, `test_mechanistic_entry_runtime_policy`, `test_postclose_summary_handoff`, affected wrapper/strict tests 중 실제 바뀐 계약만 보강한다. 새 mirror test suite/성능 framework나 모든 trading suite 반복은 만들지 않는다.

필수 integration은 public producer→source/control/label→case table→기존 compact orchestration→policy→dated PREOPEN reader→장중 loader를 통과한다. supported fixture 계산을 무조건 unsupported로 차단한 구현은 실패다. source gap과 empty/pending/unsupported/sample/no-edge를 각각 검증하고 누락/timeout/잘못된 response를 유리한 분모만 남겨 승격하지 못하게 한다. 합성 fixture PASS는 코드 연결 증거이며 자연 표본/양수 EV 실적으로 보고하지 않는다.

변경마다 implementation→self review→보완→re-review→영향 pytest/compile/bash-n/diff 및 문서 print-only parser로 닫는다. 적절한 검증 후 새 defect/변경/계약상 필수 확인이 없으면 완료 부분을 반복 재작업하지 않는다. release 및 재생성은 그 후속 사용자 승인 범위와 실행 중 wrapper custody를 확인한 뒤 immutable successor에서 수행한다.

## 9. 실행 비용과 과거 삭제 조건

기존 manifest·source projection·immutable labels·응답 checkpoint·cache를 재사용한다. source/control 날짜·content hash·role/config/code identity·label/cost/terminal revision으로 readiness를 검사한다. 동일 입력에서는 provider·가격 API·label 재계산·economics/summary full refresh를 반복하지 않는다. late response/terminal/cost/coverage revision은 영향 cohort/economic section만 갱신하고 unaffected family와 기존 response/input bytes는 유지한다.

커다란/증가 중 JSONL은 stat/generation 확인 후 기존 streaming/manifest projection을 사용한다. 큰 정상 atomic JSON/gzip generation은 f3d 재검증의 지원 reader를 유지하며 임의16MiB cap/빈 데이터 fallback으로 되돌리지 않는다. 전체 raw 재스캔·전체 history 조회·새 performance guard·provider 예산 확대·물리적인 source gap 반복 replay를 하지 않는다. 경제성에 불리한 행/필수 holdout/cost/기회 분모를 줄여 속도를 얻지 않는다.

삭제 후보는 이행 완료 뒤 참조 없는 standalone generic baseline/legacy 준비/retired lifecycle 출력과 중복 Markdown이다. 날짜별 raw trace/payload/request/prompt/outcome·원 label/pending·source-quality exclusion 및 verified model/경제성/holdout/policy/release/PID/custody/order ledger·실제 완료 비용 원장은 먼저 보존한다. 현 current/next-date·source-age/expiry/최근 평가 window/rollback/참조 artifact와 active process/lock 사용 중 파일은 삭제하지 않는다. JSON도 consumer 참조와 재생성 원천이 입증될 때만 심사하며 오래됐다는 이유로 일괄 삭제하지 않는다. 기간은 기존 owner/window를 따르고 임의 보존기한을 새로 만들지 않는다.

## 10. 완료 판정과 이번 문서 검증

ADQ0–ADQ5 코드 closure는 원천/라벨 공급·legacy consumer 전환·지원 경제성 계산·후보 선정/정책 소비·fallback·안전 차단·보존/삭제 계약의 executable 회귀와 실제 producer/consumer receipt로 판정한다. 실제 유효 data에서 no-edge/carry가 나오는 것도 정상이며 모든 입력을 무조건 inactive로 만들거나 prepared/result0을 성과 완료로 보고하지 않는다.

ADQ6 결과 closure는 승인된 bounded regeneration의 exact date/generation/경제성 상태/최종 consumer receipt다. 자연 표본/model 검증·forward candidate holdout·9/21 PREOPEN/PID·actual rolling/cumulative completed cost 수용은 별도 OPEN이며 양수 정책/EV 개선을 보장하지 않는다. blocker마다 기존 owner artifact·증거·수리 또는 natural 다음 행동·closure test를 남긴다.

이번 문서는 source/consumer/role/지원 범위 및 링크·단일 stable owner·권한을 self review→보완→re-review하고 `git diff --check`와 문서 print-only parser로 검증한다. Python/runtime/automation 구현이 없으므로 trading/provider pytest·가격 backfill·보고서 재생성·서비스/봇 기동·배포·외부 Project/Calendar sync는 실행하지 않는다.

## 8. 후속 보완: 미래 원천 계약과 primary 경제성 closure

후속 사용자 지시로 ADQ1의 기존 완료 판정을 재개방한다. 원본/v2 라벨 보존과 reader 전환은 완료된 부분이며 재작업하지 않는다. 반면 pre-AI 실행 계약 생성, lossless execution projection의 모집단 대사, 원화 추론비용 결속, 실측 모델 오차 차감은 당시 구현·검증 미완료였으며 자연 표본 대기가 아니었다. 이번 보완의 최종 증거는 [원천 생성·경제성 후속 review](../audit-reports/2026-09-18-ai-quality-source-attainability-and-economic-followup-review.md)가 소유한다. 실행 owner는 위 stable ID를 그대로 유지한다.

### 8.1 첫 결손과 과거 복구 경계

- 자연 compact21의 배타적 첫 blocker는 `exact_stop_distance_missing_or_invalid`11, `natural_contract_invalid`9, `terminal_path_not_evaluable`1이다. 이는 valid no-edge가 아니다.
- stop11: 현행 compact hot payload는 과거 fixed first-hit 연구가 요구하는 exact stop 필드를 생성하지 않았다. 주문 뒤에만 작성되던 atomic execution plan도 AI VETO의 pre-AI 계약이 될 수 없었다. retired `hard_stop_price`/TTL, 사후 고저가 또는 다른 보유 경로 SELL로 복구하지 않는다. 미래에는 당시 loaded holding policy/state·비용·수량·자본·owner TTL을 기존 atomic plan producer가 pre-AI 관측으로 고정하고 기존 full holding interpreter가 독립 청산을 계산한다. fixed-window label은 진단으로 보존한다.
- contract9: materialized labels와 한 건의 exact 원 raw 대조 결과 timeout8, live PASS의 실제 `entry_risk_pass_residual_risk_not_considered` semantic reject1이다. false exclusion 근거가 없어 그대로 제외한다. transport 실패를 PASS로 바꾸거나 semantic guard를 완화하지 않는다.
- path1: 098460의10:38:37 판단에 가격 원천이10:51부터 있으므로 고정 과거 window 결손이다. 미래 정상 수집과 구분하며 현재 가격으로 채우지 않는다.
- 운영 모델: 기존 empty execution projection은 실제 Main 주문0의 근거가 아니었다. 기존 producer census에 stage별 lossless identity와 기존 threshold family partition을 결속한다. 원 broker/order/fill/terminal과 original post-sell completed-cost receipt가 없는 과거 모델 행은 제외한다. 기존 모델 검증 코드와 완료 손익 producer/consumer는 재사용한다.

### 8.2 최소 구현 순서와 계약

1. Main의 기존 live `analyze_target` 호출5경로에 optional source-only observer를 연결한다. 원 request의 machine assessment/capture 직후, provider 전에서 기존 capacity·중앙 allocator·공통 guard·P1 가격 owner·split/TTL·frozen holding/cost context를 사용한다. 실제 BUY receipt의 초기 손절/exit-mode 설정을 같은 pure helper로 frozen CF에 전달하고, loaded micro estimator 초기 상태와 native quote 변화로 정책 상태를 재생한다. watched stock을 복사하며 broker 주문·probe reserve·수량/예산 변경 권한은 없다. capacity 불명, 공통 guard 차단, probe reserve 필요, 보유/비실제/미지원 venue는 정확 blocker를 기록한다.
2. 당시 관측 계획과 최종 AI trace의 실제 availability clock을 별도로 저장한다. CF의 실행 시작은 incumbent AI 응답 이후이며 응답 전 체결을 만들지 않는다. 양쪽은 같은 frozen 수량·자본·후행 guard·availability를 사용한다. 후보 latency 개선은 이 frozen-clock 비교의 지원 대상이 아니다.
3. 기존 pipeline writer/summary compactor/threshold projection만 보완한다. pre-AI seed는 기존 decoder 상한2MiB 안에서 lossless 저장하고, 일반 필드는 기존16KiB를 유지한다. stage별 expected/observed count와 identity sum을 대사한다. Main이 이미 확보한 현재 시장 국면을 existing process-local cache에 기록하고 같은 프로세스의 기존 WS observer가 depth cutoff/MAX_FRAME_GAP_SEC 안의 값만 결속한다. 새 request/collector를 만들지 않는다. scope는 declared execution-stage producer census이며 과거 전체 raw/Main order coverage로 확대해 해석하지 않는다.
4. 기존 compact projection은 source contract 버전과 owner subsection을 결속한다. 코드-only/동일 sealed raw generation 변경은 작은 materialized label·owner report만 재결속하며 전수 trace/payload 재스캔을 피한다. 실제 raw/path 변화는 기존 producer가 새 generation을 작성한다. 과거 제외 행의 삭제된 input은 재구성하지 않는다.
5. 기존 운영 모델의 선행 actual calibration/model holdout을 검증하고 동일 frozen 자본의 paired 순익·EV·tail·보유 자본·reserve·체결 참여율을 계산한다. 겹치는 단일 포지션 기회는 별도 allocation 모델 없이 독립 이익을 더하지 않고 unsupported/null로 처리한다. 지원 범위가 생겼다는 것과 자연 모델 검증 완료를 구분한다. 운영 arm·선행 모델·reviewed 비용 결손인 진단 행은 provider-funded 후보 탐색에서 제외한다.
6. 기존 reviewed provider pricing owner를 재사용한다. 현재 `operator_accounting_zero_cost`는 유효기간·원천 bytes/hash·정확 모델을 검증한 경우만 Δcost0이다. nonzero USD 가격은 measured token delta와 reviewed KRW conversion 계약이 없으면 source gap/null이며 임의 환율을 만들지 않는다.
7. compact 승격 v4는 v3의20 learning/20 holdout/2 held dates/coverage1.0 및 기존 scope·tail·일별 순익·holdout 미사용 조건을 유지하고 실측 오차/stress 하한을 추가한다. 하한은 같은 pair의 base/stress Δ 최소값에서 changed-decision 두 arm의 empirical error envelope와 추론비용을 차감한 평균이다. unchanged decision은 모델 오차가 상쇄된다. 이는 통계적 신뢰하한이나 실제 이익이 아니다.
8. 기존 dated publisher/Daily/PREOPEN reader/Main loader 및 적용 버전 performance owner를 재사용한다. 실제 submit에서 validated machine/compact 판단 버전·bundle·attempt·trace·PID를 frozen context에 기록하고 기존 완료 비용/주문 journal owner로 joint applied version별 중복 제거·rolling/cumulative EV/순익/tail/노출/model error를 계산한다. Split 정책 적용만으로 machine/compact 소비를 주장하지 않는다. active 조건 통과, fail carry, hash/stale/scope/holdout 차단을 회귀 검증하고9/17 source→9/18 publication→9/21 effective로 제한 갱신한다. 정규 PREOPEN 동결/PID·자연 완료 경제성은 수행하지 않는다.

### 8.3 탐색 가설과 지원 범위

| owner | 검증 가능한 판단 변경 | primary 지원·제외 경계 |
|---|---|---|
| 현행 machine | 기존 spread/fillability/book ratio grid 안에서 위험한 현재 ENTER_NOW를 필터링하여 실제 비용 후 손실·노출을 줄이는가 | 실제 downstream compact 판단과 기존 guard를 고정한 current ENTER_NOW filter 비교. 기존 grid/guard를 보존하되 완화 후보의 신규 non-entry 승격은 uncalled downstream AI를 PASS로 가정할 수 없어 primary unsupported; 기존 missed-opportunity 연구는 별도 진단이다. supported owner CF가 source population에 공급된 경우만 비용·모델/stress·별도 chronological holdout gate로 평가한다. |
| compact | 같은 machine ENTER_NOW/plan에서 불필요 VETO를 PASS로 바꾸거나 손실 PASS를 VETO로 바꾸는가 | 현행 등록 prompt만 비교. PASS/VETO 완료 경로 지원, CAUTION의 실제 recheck 종결 부재는 제외. 판정 불변/self comparison은 Δ0 진단이며 독립 승격이 아니다. |

현재 operating execution 모델의 지원 venue는 KRX/NXT 초기 Main real, native full-depth·full fill·독립 full holding exit다. `KRX_NXT_INTEGRATED`/SOR는 source observer에서 명시적 unsupported이며 공통 venue를 추정하지 않는다. partial/no-fill의 cancel acknowledgement·late-fill inventory, 후행 ADD, 미지원 holding service/시장 입력도 null·구체 owner/closure를 유지한다. 지원 범위 확정은 추가 모델이나 collector 생성 승인이 아니다. 자연21 중 통합 애프터마켓10을 지원 KRX11로 합치지 않는다.

### 8.4 판정과 자연 OPEN

| 구분 | closure |
|---|---|
| 구현·검증 완료 | 운영 producer 지원 입력→lossless 저장/분모→independent operating CF→실측 model/stress 계산, 기존 선정/dated consumer·fail carry 회귀를 증거로 판정한다. 합성 fixture는 연결 검증이며 자연 EV가 아니다. |
| 과거 source gap | 원 pre-AI 계약/stop/path/order/completed-cost 부재는 복구 가능 원 bytes가 있을 때만 수리한다. 원천이 없으면 고정 exclusion이며 기다림으로 닫지 않는다. |
| unsupported scope | venue/session·partial/no-fill·uncalled downstream AI·겹친 자본 등의 모델 지원 계약 밖. null과 정확 owner/closure; 단순 표본 대기가 아니다. |
| 자연 실증 대기 | 배포 코드의 지원 기회 관측/actual owner ledger/완료 비용 receipt 유입, 선행 독립 actual 모델 표본 축적, 이후 별도 후보 holdout,9/21 정규 PREOPEN/PID·자연 적용·적용 버전별 rolling/cumulative 완료 손익. 미래 원천 회귀가 PASS인 지원 scope에만 적용한다. |
| valid no-edge | 모든 필수 source/model/coverage/independent holdout 계약이 유효한 비교에서 양수 조건 불충족. 모델 미검증 또는 null을 no-edge로 바꾸지 않는다. |
