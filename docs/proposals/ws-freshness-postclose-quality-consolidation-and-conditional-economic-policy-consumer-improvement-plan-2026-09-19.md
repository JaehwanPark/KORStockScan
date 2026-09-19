# WS 장후 품질 마감 통합·조건부 경제성 평가·장전 정책 소비 보완계획

작성일: 2026-09-19 KST. 이번 범위는 상세 구현계획 수립이다. 코드·예약·정책 변경, 장후 재생성, 배포, PREOPEN 실행은 수행하지 않는다. 우선순위는 **구조적 결손 해결 → 비용 반영 EV·일별 순익 비교 → 다음 장전 정책 발행·자연 소비 → 불필요한 실행 축소**다.

## 1. 결정과 근거

장중 WS 감시는 유지한다. 장후에는 기존 변경분·요약으로 품질을 마감하고, 유효한 경제성 입력이 있거나 해당 입력이 수정된 경우에만 평가한다. 별도 WS 튜너나 포트폴리오 시뮬레이터를 신설하지 않는다. 기존 scanner lookup-attention 통합 owner와 실행 replay를 보완한다.

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [현재 checklist](../checklists/2026-09-19-stage2-todo-checklist.md). `main-only/normal_only/post_fallback_deprecation`, clean baseline 2026-06-05 이후 자료만 사용한다.
- 선행 완료 기능: [scanner 통합 계획 §12](scanner-lookup-attention-evaluation-consolidation-and-runtime-plan-2026-09-18.md), [compact 후속 리뷰·WS 분석](../audit-reports/2026-09-19-compact-ai-postclose-integration-implementation-review.md). standalone 평가 폐기·변경분 수집·zero 정책 발행은 재구현하지 않는다.
- 검토 source: 선택 release `compact-ai-label-admission-reviewed-20260919`, SHA `9f814e30cbc08806750616e94f7ab099d5aa58d1`. 구현 착수 때 최신 release·병행 producer 변경을 다시 대조한다.
- 현재 WS source9/17의 부모 report는 intraday이고 prune/hotset finalized=false다.9/18 report는 원천 누락이다. 부모 report phase와 `lookup_attention_selection` subsection의 phase를 각각 검증하며 파일 존재로 final을 판정하지 않는다.
- KRX BBO 연결률4.7564%·검열53.2925%, aftermarket venue UNKNOWN 등은 구조적 공급 결손이다. 특정 hotset proxy의 비용 후 EV−0.68532307%는 supporting diagnostic이며 실제 정책 개선값이 아니다.
- main 정기 trigger는 앞선 조회에서 확인되지 않았고 WS 장중5분 cron은 존재한다. 코드 준비와 설치된 실행을 구분한다. 이번 계획은 cron 복원·새 timer를 지시하지 않는다.

## 2. 반드시 해결할 구조적 단절

| 단절 | 현재 코드의 실제 상태 | 최소 보완 및 closure |
| --- | --- | --- |
| 검사와 품질 개선 혼동 | 보고서는 결손을 찾지만 BBO·venue·anchor를 복구하지 않는다 | 기존 scanner/pipeline/pruned collector의 원 시점·venue·quote/epoch·완료 receipt 전달을 확인하고 실제 누락 writer만 보완. 다음 자연 generation에서 exact join 확인 |
| 평가 결과 고정 | `scanner_lookup_attention_resource.integrated_selection_evaluation`은 항상 source_gap, primary EV/순익 null과 고정 gaps를 반환 | 실제 원천/proof를 검사해 gap 목록을 계산하고, 지원되는 양측 실행 결과가 있으면 측정값과 상태를 산출. 자료가 없는 경우는 계속 null |
| 가중치0 발행만 구현 | `publish_integrated_policy`와 `validate_integrated_selection`은 zero-only 계약 | 같은 existing family 안에서 측정 hold/reject/carry/검증 ready를 공유 검증. 기존 zero-only 산출물은 non-live 호환으로 유지 |
| 양수 PREOPEN 영구 거부 | `validate_preopen_receipt`는 active receipt를 무조건 False로 반환 | 새로운 integrated proof가 모든 경제성·날짜·권한 검증을 통과할 때만 active receipt 허용. 과거 standalone active receipt는 계속 거부 |
| active 원천일 오독 | freeze의 active branch는 policy 파일 날짜로 source_report를 읽음 | payload의 실제 `source_evaluation_date`로 report를 읽고 report/subsection/proof 해시를 함께 동결. publication과 observation이 다른 경우 회귀 |
| 후행 요약 source 경로 | `selection_handoff`가 대상일과 policy 파일 날짜를 동일하게 가정 | 명시 publication/effective 결속을 기존 handoff에서 소비. 자정·휴일 successor도 exact source를 유지 |
| 상시 반복 계산 | final/refresh 경로가 입력 자격과 무관하게 경제성 호출 가능 | 작은 existing section/state의 변경 지문·지원 범위 preflight 뒤에만 실행. quality 마감·dated 정책 인계는 경제 평가 skip과 분리 |

검증기에서 False를 제거하거나 status만 ready로 바꾸는 수리는 금지한다. 실행 가능한 원천→측정→독립 holdout→동일 계약 publisher→PREOPEN→scanner의 경로를 함께 보완해야 한다. 단순 시간·표본 증가로 위 고정 반환문이 해소되지는 않는다.

## 3. 기존 owner·변경 위치

| 기존 owner | 책임과 변경 범위 |
| --- | --- |
| `monitoring/intraday_ws_freshness_monitor.py` | 장중 감시 보존, quality final과 economic evaluation 상태 분리, 변경분 재사용·final subsection 보존. 기존 `--refresh-lookup-selection-only` 부분 갱신 경로 재사용 |
| `monitoring/ws_freshness_acceptance.py` | 기존 prune/hotset CF·rolling 품질 계약 재사용. proxy를 primary 승격 근거로 변경하지 않음 |
| `scanners/scalping_scanner.py`, 기존 pipeline writer·pruned BBO collector | original full partition·budget/rank·venue/anchor/quote lineage 확인. 이미 지원되는 필드의 전달 결손만 수정; caller가 없는 새 수집기 없음 |
| 기존 `sniper_missed_entry_counterfactual`, `scalping/strategy_owner_replay.py`, `scalping/entry_split_order_plan.py` | 원 recipe/요청량·guard/exit/cost·실제 모델 검증. 기존 replay seed와 결과 계약을 공급하며 다른 세션의 완료 기능 재작성 금지 |
| `scalping/scanner_lookup_attention_resource.py` | same-tier/same-budget 선택 차이와 기존 실행 proof를 연결하는 작은 adapter, conditional preflight·학습/forward validation·측정 book |
| `scalping/scanner_lookup_attention_policy.py` | 단일 dated publisher·공유 검증·정확한 PREOPEN 동결/loader/캐시. 기존 bonus formula·상한·적용 venue/session 유지 |
| 기존 quality audit·Daily·EV·workorder·runtime summary·strict | quality receipt와 경제 상태의 동일 generation 소비. 검사는 품질 판정, ready 판정은 scanner 경제 owner에 유지 |
| 기존 postclose/preopen wrapper | WS quality/조건부 경제성→compact finalize→Daily/EV→tail closure의 순서 보존. 기존 PREOPEN 조건과 시간창 유지 |

새 production module·root Python·DB·report family·policy family·collector·service·cron·AI 호출·범용 튜닝 framework는 만들지 않는다. 장중 monitor CLI/주기와 source guard는 보존한다. 기존 품질 감사에는 WS source receipt/hash·final 상태·exclusion summary만 연결하고 report 전체를 중복 생성하지 않는다. 보고서 본체는 현재 소비자가 있어 즉시 삭제하지 않는다.

## 4. 조건부 실행과 품질 마감

기존 report/section/state 안에 source date·code/contract/model version·exact input/proof hash, analysis mode·skip reason·first blocker·owner/closure를 추가한다. 새 manifest 저장소는 만들지 않는다.

1. **항상 필요한 품질 마감:** 기존 state/source offsets·sealed receipt·종목 master·시장상태·snapshot as-of를 대사한다. source 변경 없이 유효한 final이면 재사용한다. 부모 snapshot 당시 시각과 현재 시각을 혼용해 stale를 재분류하지 않는다.
2. **원천 preflight:** full partition conservation, baseline 실제 선택 재현, scope/route·원 recipe/요청량·ordered BBO/terminal·cost·budget 검증. 결손은 exact cohort/row에 분리한다. 미지원 cohort를 제거해 전체 budget 비교가 완성됐다고 주장하지 않는다.
3. **경제 모델 preflight:** 기존 실제 full-fill/COMPLETED valid profit·비용 자료로 independently validated model proof 확인. 표본 부족과 proof invalid를 구분한다. 매번 해당 후보의 실체결을 요구하지는 않지만 실행 모델 검증에는 실제 실적이 필요하다.
4. **선택 preflight:** complete partition의 동일 tier·slot·quota·예산에서 baseline/candidate를 재현. spare capacity 또는 동일 선택은 no_competition/no_effect로 닫는다. 가격이 좋아 보이는 종목만 사후 선정하지 않는다.
5. **평가 실행:** 새 유효 changed selection·terminal revision·model/cost/code semantic revision에만 실행. 동일 지문 재실행은 provider0·raw 전수 재스캔0·표본 증가0. migration 자료는 역사 진단으로 보존한다.
6. **평가 skip 뒤 정책 인계:** 경제성은 source_gap/pending/unsupported/reused/no_effect를 표시하고 quality·dated policy handoff는 완료한다. mandatory source 계약 실패는 정상 empty나 optional PASS로 바꾸지 않는다.

원천/모델 자격과 승격 표본은 별도다. 검증된 실행 모델과 유효 pair가 있으면 소표본도 비용 반영 연구값을 표시하고 hold_sample로 남긴다.20건 승격 floor 때문에 측정값까지 null로 지우지 않는다. 부족한 모델 proof나 source loss에는 primary를 산출하지 않는다.

historical large state가 현행 계약과 맞지 않으면 sealed report/native projection으로 필요한 subsection만 갱신한다. 보관·partition identity 확인 없이 사라진 raw를 정상0으로 처리하지 않는다. 무조건 full rebuild로5GB raw를 반복 읽지 않는다. 재사용 가능한 입력이 없으면 owner와 source gap을 남긴다.

## 5. 의미 있는 EV·일별 순익 비교

baseline은 bonus0, challenger는 기존 단일 bounded bonus formula다. 초기 적용 범위는 기존 KRX regular 안에서 owner가 재현 가능한 complete simple-capacity partition이다. universe·tier·slot/owner quota·budget·quantity/leg·가격·AI·exit·hard guard는 양측 동일하다. 신규 가중치 grid와 venue 확대는 하지 않는다.

- baseline 전체 선택과 candidate 전체 선택을 비교한다. unchanged도 분모에 보존하고 incoming 기회와 outgoing 기회비용·회피손실을 모두 반영한다. 같은 선택은 Δ0이며 별도 개선 성공이 아니다.
- CF는 당시 원 seed·guard·ordered depth/trade·cost/exit/version을 기존 replay에 넣어 재현한다. 원 요청량/진입 recipe/guard가 없는 unselected 후보는 임의1주·미호출 AI PASS·미래 실제 체결수량으로 보충하지 않는다.
- 지원 모델은 기존 기능과 독립 actual validation으로 입증된 범위만 사용한다. 단순 quote touch를 확정 fill로 사용하지 않는다. partial·취소 race·수동 custody·carry·상호 중첩 자본이 미지원이면 명시 unsupported다.
- 기존 replay 결과와 frozen cash/reservation 경로로 양측 예산 보존을 증명한다. initial 지원은 비중첩 complete partition으로 한정한다. 새 포트폴리오 엔진 없이 재현할 수 없으면 해당 scope primary는 source_gap이고 별도 최소 입력 계약을 남긴다. 정상 종료되지 않은 결과를 합산하지 않는다.
- 동일 frozen eligible budget을 분모로 비용 후 `notional_weighted_ev_pct`와 paired Δ, 날짜별 baseline/candidate 순익(원)·일별 Δ를 산출한다. 두 결과의 cash·reserve·노출시간·tail·stress·model error envelope를 함께 비교한다. 미진입/무체결0은 해당 terminal이 source-valid일 때만 사용한다.
- 실제 완료 `COMPLETED + valid profit_rate` 손익, full/partial, proxy·CF·realized는 별도 book이다. gross/high-low 수익·단순 수익률 합·고관심/저관심 체결 평균 차이는 primary나 인과 uplift가 아니다.
- 기존 비용 계약·model tolerance·rolling/cumulative·source-quality/coverage·family sample floor·tail/stress를 유지한다. prune/hotset의 resolved20/BBO95%/censored≤20%는 해당 proxy 계약이며 그대로 두되 scanner 실행 모델 승격의 대체 조건으로 쓰지 않는다.
- 현행 scanner 상수는 관심도 cutoff0.60·bonus 상한200·source freshness120초, completed total20/5거래일·cohort10/3거래일·paired3/2날짜, EV uplift floor0.10%p·tail degradation 상한0.25%p·worst floor−5%다. 이를 확대/완화하지 않는다. 실제 causal paired 측정·독립 holdout에서 비용 후 candidate EV와 EV Δ·일별 순익 Δ가 양수이고 모델 오차/stress 반영과 기존 위험 조건도 통과해야 ready다. completed cohort 평균 차이로 해당 paired gate를 충족했다고 보지 않는다.
- 실제 모델 holdout은 prompt/selection learning보다 먼저 완료한다. 후보 formula·cohort·cutoff·baseline을 동결하고 독립 미래 holdout을 기존 helper로 검증한다. 과거 archive90일을 새 forward 표본으로 복제하지 않는다.

supported 연구값과 promotion-eligible 비교값은 구분한다. 양수 개선·측정된 no-edge/위험 악화 모두 유의미한 결과다. 자료가 없는 null/source_gap은 비교 완료가 아니다.

## 6. 정책 생성과 장중의 정확한 변화

existing `data/threshold_cycle/scanner_lookup_attention_policy/scanner_lookup_attention_policy_<policy_date>.json`를 유일한 후보 출력으로 사용한다. source report는 기존 WS subsection에 유지한다. 계약 버전만 증가시키고 별도 policy namespace를 만들지 않는다.

| 결과 | 다음 장전 정책 | 완료 주장 |
| --- | --- | --- |
| supported 비교·독립 holdout·EV와 일별 순익/위험 모두 family gate 통과 | 기존 bounded formula의 ready 정책 | 측정·선정·발행 완료. PID/자연 성과는 별도 |
| supported 측정값은 있지만 sample/holdout 부족 또는 no-edge/위험 악화 | incumbent/baseline 유지, 측정 book과 hold/reject 이유 결속 | 경제 연구 결과 확보; challenger 미적용 |
| source/model gap·미지원·비교0 | source-valid zero-bonus baseline 또는 existing carry 계약상 유효한 incumbent 보존 | 다음 장전 사용 가능한 보존 결정만 완료, 경제성은 OPEN |
| 기존 정책·global source 계약도 invalid | apply 차단 및 실패 receipt | 임의 default나 fail-open carry 생성 금지 |

정책 생성기는 ready proof와 source/exit/cost/model/learning/holdout hash를 묶고 source section과 공유 validator로 대조한다. observation report는 주문 권한이 없고, ready policy만 기존 scanner 정렬 소비 권한을 가진다. broker order authority는 항상 별도다. 자기해시만 맞는 forged ready·legacy active는 거부한다.

**실제 런타임 변화는 같은 priority tier 안에서 fresh 관심도 점수의 bounded bonus가 candidate 순서를 바꾸는 것뿐이다.** 선정된 후보는 기존 machine→compact→가격/수량/submit guard를 다시 통과한다. 이 정책이 BUY를 직접 지시하거나 시세 freshness·계좌·주문·cooldown·cap·reserved slot을 우회하지 않는다. stale/unknown venue/invalid receipt는 bonus0이며 rollback도 기존0이다.

장전 기존 wrapper→`freeze_preopen_policy`→immutable target-date receipt→`load_active_policy`→scanner priority profile의 양수·보존 양쪽 경로를 검증한다. `validate_preopen_receipt`의 active=False 고정 한계를 proof 기반 검증으로 바꾸고 새 integrated ready만 허용한다. 당일 receipt는09:00 이전 정상 PREOPEN에서만 동결하고 다시 덮지 않는다. 이번 계획에서 조기 freeze는 실행하지 않는다.

기존 `_validate_payload`/`_evidence_valid`가 사용하는 standalone observational evidence와 새 integrated causal proof를 혼합하지 않는다. 새 계약은 같은 공유 predicate로 ready를 검증하고 구형 positive 경로는 계속 닫는다. inactive 보존 receipt에도 source-evaluation/policy/effective date·source/policy hash·disposition을 metadata로 남겨 장전이 어느 보존 결정을 소비했는지 추적한다. active=False를 정책 미확인 상태와 동일하게 표시하지 않는다.

## 7. 날짜·generation·전후 소비 연결

`source_evaluation_date`, `publication_date`, 기존 loader가 사용하는 직전 거래일 `policy_date`, 실제 다음 거래일 `effective_date`를 분리한다. 현재 source9/17·작성/발행9/19·예정 effective9/21을 하드코딩하지 않는다. 휴장과 단순 미적재를 구분하고 calendar는 기존 공식 owner를 소비한다. 비거래일 publication 파일이 loader의 직전 거래일 검증을 우회하게 만들지 않는다. 기존 policy_date에 frozen 증거가 있으면 original을 보존하고 generation successor/기존 충돌 계약을 따른다.

| 순서 | 출력/소비 계약 |
| --- | --- |
| 기존 장중 source | type/route/epoch·quote timestamp·scan generation·partition/rank·recipe/plan·terminal 변경분 receipt |
| final quality audit/WS 품질 마감 | exact source-generation·검사/exclusion 요약; 감사가 scanner 선정권을 갖지 않음 |
| WS 조건부 경제성 | preflight→기존 model/replay→측정/holdout 또는 skip/reused receipt |
| 단일 existing scanner publisher | ready/carry/reject/gap의 dated policy·원 evaluation proof 결속 |
| 기존 compact finalize·Daily refresh·EV/workorder | WS/scanner 최종 subsection·policy generation을 소비. compact 정책·다른 machine scope 변경 없음 |
| tail summary/tower/checklist/strict/controller | 마지막 소비 해시 대사. 같은 raw/source를 재평가하지 않고 recommendation·요약만 재결속 |
| 정규 다음 PREOPEN→scanner | source와 publication이 달라도 exact evaluation report 동결, target-date receipt→loader/cache→실제 PID/순서 변화 receipt |
| post-apply | 동일 machine/compact/selection version의 completed/cost 성과·자본/노출·기간을 기존 owner로 귀속 |

quality phase와 economic subsection phase를 각각 기록한다. 기존 partial refresh는 경제 subsection만 final일 수 있으므로 부모 report 전체를 final로 바꿔 표시하지 않는다. 늦은 장중 writer/부분 재시도는 이미 발행된 final proof를 같은 입력의 provisional section으로 덮지 못하도록 existing generation lock/순서 계약을 대사한다. PREOPEN이 동결한 source는 current file drift와 분리해 원 proof를 보존한다.

## 8. 최소 구현 순서와 종결 테스트

| 패키지 | 최소 변경 | closure |
| --- | --- | --- |
| WS0 원천 계약 | 최신 source·기존 writer/replay/model 출력·원 budget/full partition 지원 범위 고정 | natural source 결손의 exact owner·필드·first depleted stage, 역사 손실과 미지원 분리 |
| WS1 공급 보완 | 필요한 기존 venue/anchor/quote/plan/terminal 전달 수리만 수행 | source→compact retained/excluded census→execution seed/proof join. API parser 수정 시 공식 Kiwoom reference gate 필수 |
| WS2 조건부 통합 | existing final/refresh에 quality와 economic mode 분리·source fingerprint 재사용 | 동일입력 raw rescan0·새 표본0, supported source에서 평가 진입, unrelated cohort 격리, source_gap/valid_empty 구분 |
| WS3 경제 비교 | existing resource helper에 owner replay/proof adapter와 실제 metric/holdout 상태 추가 | 같은 선택Δ0, incoming/outgoing·정상 no-fill0/null·capital/tail/cost/model revision·forward 오염 회귀 |
| WS4 소비 완결 | publisher/validator/source handoff/PREOPEN/loader의 ready/carry/reject 공유 계약 | 양수 native fixture가 final source→policy→PREOPEN receipt→scanner bonus까지 도달; zero/forged ready/legacy active·date/source mismatch는 차단 |
| WS5 제한 재생성 | 리뷰·검증·승인 후 original source/family만 기존 partial refresh로 재생성 | 다음 거래일 dated usable 정책 또는 명시 apply-blocked; Daily/EV/runtime summary/tower/checklist/strict의 최종 해시 일치 |
| WS6 자연 수용 | 정상 source/model/독립 holdout·정규 PREOPEN/PID·실제 완료 성과 확인 | selection order 변화 또는 baseline 보존의 자연 receipt, full-cost EV/일별 순익·tail/자본·joint-version 추적 |

새 테스트 family 대신 기존 intraday WS/acceptance/pruned BBO/scanner resource/net approval/policy/consumer/wrapper/summary strict 테스트에 필요한 회귀만 추가한다. Python compile·pytest 영향 범위·wrapper 변경 bash syntax·diff check를 수행한다. 양수 fixture는 경로 구현 검증이며 자연 EV가 아니다. 자동화/wrapper 변경 시 owning 운영 문서·당일 checklist를 같은 change set에서 갱신한다.

구현은 implementation→self review→fix→re-review→targeted validation을 반복한다. 원천 전체 결손이면 WS5에서 같은 raw 재실행을 멈추고 WS1 공급/WS6 자연 owner를 OPEN으로 남긴다. quality/조건부 실행만 구현한 상태를 WS3/WS4 경제성 루프 완료로 닫지 않는다.

## 9. 삭제·운영·실행 범위

420개 hotset proxy 반복 출력과 중복 workorder rendering은 소비 계약을 먼저 확인해 필요한 cohort/기존 요약만 유지한다. 현행 scanner integrated section·원 raw·incremental checkpoint·model proof·정책 generation·PREOPEN/custody·rolling 원분모는 보존한다. 과거 intraday 파일을 final 승격 근거로 복구하지 않는다. 새로운 cleanup framework·성능 guard·benchmark·병렬화를 추가하지 않는다.

main 설치 trigger 부재는 코드 최적화 문제가 아니다. 기존 운영 owner가 실제 설치·실행 조건을 확인할 때까지 자동 재생성 완료로 주장하지 않는다. source 계약과 후행 단계가 닫힌 뒤 승인된 기존 실행 경로에서 WS5를 수행하며 새 cron과 polling을 신설하지 않는다. 당일 주문·재기동·수동 env/provider/cap/threshold 변경은 이번 계획 실행 범위가 아니다.

실행 착수 시 기존 `CodeImprovementWorkorderReview0918`에 구조/consumer 구현을 연결하고, 자연 건강·모델/PREOPEN/성과는 [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`에 유지한다. 새 중복 OPEN owner·예약은 만들지 않는다. 구현 acceptance 인계 시 원 stable ID·history를 보존하고 parsed owner 하나를 확인한다.

## 10. 이번 계획의 검증과 완료 정의

이번 변경은 계획 문서1개다. 실제 코드에 존재하는 unconditional source_gap·zero-only publisher/validator·active PREOPEN 거부·active source date 분기를 점검한 근거로 작성했다. 문서 review/fix/re-review·링크/owner/authority·`git diff --check` 및 print-only backlog parser만 실행한다. 거래 테스트·장후 재생성·AI/API 호출·정책 발행·배포·외부 sync는 이번 작성에서 수행하지 않는다.

최종 목표는 **지원되는 원천의 비용 후 EV·일별 순익 비교값과 위험을 산출하고, 검증된 후보 또는 보존 정책을 다음 장전에서 자동 소비하는 것**이다. 양수 결과는 보장하지 않는다. source/model gap과 null만 남았다면 코드/보존 인계 범위만 닫으며 경제성 목표는 미종결이다. 구조 공급·모델 또는 실제 scheduler 지원이 최소 보완 범위를 넘으면 해당 owner/미지원 계약을 명시하고 추가 엔진 개발로 범위를 확대하지 않는다.

## 11. 구현 상태 및 종결 판정 정정 (2026-09-19)

사용자의 후속 구현 지시로 complete 입력이 이미 존재하는 경우의 same-tier 선택, 기존 owner replay, 비용·tail·자본·독립 model/learning/forward holdout, 실제 동결 시점 cutoff, 입력 지문 재사용, post-apply exact PREOPEN policy hash 귀속 경로를 구현했다. 선택이 같으면 delta0/no_effect로 남기며 절대 EV는 null이고, 변경 선택인데 원 plan·terminal·reviewed pricing·독립 모델 중 하나라도 없으면 primary는 null/source_gap이다.

publisher는 source evaluation/publication/policy/effective date를 분리하고 v2 ready 또는 zero-bonus hold/gap을 같은 기존 policy family에 발행한다. PREOPEN은 v2 shared proof만 동결하며 legacy active·위조 self-hash·날짜/hash 불일치를 거부한다. 실제 효과는 기존 same-tier score bonus뿐이며 tier/slot/quota/수량/AI/주문/안전 guard는 바꾸지 않는다. late intraday writer는 final subsection을 지우지 못하고, Daily·EV·runtime summary·control tower·checklist·scoped strict가 동일 section/policy hash를 소비한다.

재검토 결과 이전의 WS0–WS5 종결 표시는 잘못이었다. `execution_inputs()`는 compact source projection에 이미 존재하는 `scanner_promotion_id`별 자연 compact 판정·owner replay만 읽는다. 그러나 순위 변경으로 candidate에 들어오는 capacity-pruned 후보는 compact AI, entry recipe, 요청 수량, guard와 terminal을 생산하는 장중 경로를 통과하지 않는다. 따라서 현재 producer 계약에서는 다음 자연 generation을 기다려도 변경 선택의 양측 실행 입력이 자동으로 완성되지 않는다. fixture의 양수 경로는 evaluator 동작 검증일 뿐 producer 도달 가능성 증거가 아니다.

완료 범위는 기존 입력이 있을 때의 evaluator·fail-closed policy·PREOPEN/후행 hash 전달과 배포까지다. WS1 공급 보완, WS3 실제 비교값, WS5의 경제성 있는 재생성은 OPEN이다. 역사 결손을 합성하거나 탈락 후보를 장중 provider에 추가 호출하지 않는다. 기존 `CodeImprovementWorkorderReview0918`가 prospective 탈락 후보의 source-only 실행 계약을 설계·검증하고, `KiwoomCommonHealthOpportunityCostAcceptance0917`는 그 계약이 생성된 뒤 정상 PREOPEN/PID와 COMPLETED full-cost 성과만 소유한다.

배포와 source9/17 제한 재생성은 [구현 리뷰](../audit-reports/2026-09-19-ws-freshness-conditional-economics-implementation-review.md)에 기록했다. WS 경제 subsection `02afcf30577e8fa290e00fe9d62e1e624adcb8ce2217dbfaec418a010ece49d2`와 다음 장전용 policy `5cb82631ef6674c80a5154737ccdca70b6d6ac75fad0194d2cc883e5ef45bf51`가 기존 consumer에 결속됐지만, 현재 상태는 `source_gap/source_contract_blocked`, bonus0이고 실제 EV·일별 순익은 null이다. 이는 안전한 보존·차단 배포 receipt이며 구조적 경제성 구현 종결이 아니다.
