# 2026-09-19 Compact AI 장후 통합 구현 리뷰

승인: 사용자의 통합 계획 구현·반복 리뷰/보완·커밋푸시·immutable 배포·제한 장후 재생성 지시. source9/17은 보존하며 publication9/19의 명시 successor를 사용한다. 주문·bot restart·조기 PREOPEN·provider/수량/비용/표본/안전 guard 변경·cron 복원은 수행하지 않는다.

## 구현·리뷰·보완

- 기존 calibration에 prepare/evaluate/finalize/handoff 공통 조정을 추가했다. quality source materialization은 최초 Daily 앞에 유지하고 prepare는 유효 control/labels를 소비한다. evaluate만 후보 실행을 허용하고 provisional 결과를 생성한다.
- 기존 main의 독립 compact execute를 공통 evaluate로 대체했다. 필수 WS 입력 뒤·최초 EV/runtime summary 전에 기존 machine+compact publisher를 단일 finalize로 호출한다. late handoff는 요약/checklist 재결속만 수행하고 provider/publisher를 호출하지 않는다. 부분 compact CLI도 공통 finalize를 소비하며 단독 wrapper는 같은 단계 조정을 사용한다.
- common lock→paired-day→publisher 순서를 유지한다. finalize는 source generation이 바뀌면 raw를 재조회하거나 후보를 호출하지 않고 재평가 요구로 차단한다. final publisher 직전 paired·labels·의존 stat 지문을 대조한다. 다음 PREOPEN freeze는 기존 publisher가 보존한다.
- 공유 data 실체 경로를 정규화해 release 경로 변경만으로 sealed raw를 전수 재스캔하지 않게 했다. 후보 입력뿐 아니라 issued candidate prompt/schema request identity와 reviewed 비용 receipt를 캐시에 결속한다. 다른 프롬프트/스키마 응답 또는 바뀐 비용을 재사용해 승격하지 않는다.
- 리뷰에서 scope 후보의 프롬프트 계약과 날짜별 response schema 지문을 분리했다. 날짜가 바뀌었다는 이유로 정상 holdout을 차단하지 않으며 동결된 프롬프트 변경은 provider 호출 전에 차단한다. 일부 응답·self comparison을 경제성 비교 완료로 기록하지 않는다.
- 원 배포본에서도 실패한 기존 fixture의 source date/terminal gate/정확한 scanner identity를 명시했다. 실제 source guard를 완화하지 않았다. 양수 후보/기존 보존의 native publisher→consumer→summary→strict 회귀를 통합 진입점에서 확인했다.

새 module/collector/DB/report family/독립 publisher를 추가하지 않았다. 기존 v6 및 운영 seed/replay·lossless census·독립 모델 검증 producer 지원은 그대로 재사용했고 확인된 회귀로 검증했다.9/17의 원 stop/plan/identity 결손과 timeout은 비가역적/실패 입력으로 남기며 자연 model holdout이 없는 상태를 코드로 합성하지 않는다.

## 검증

- 정책·compact·calibration·optimizer·consumer·summary·strict 영향7개 suite:550 passed.
- entry split/strategy owner의 operating/model/source/coverage/census 관련 회귀:54 passed,179 deselected.
- 마지막 source binding·self comparison/coverage 보완 후 compact/calibration:241 passed.
- Python compile, 변경 wrapper `bash -n`, `git diff --check`, print-only parser 통과.
- print-only parser에서 기존 자연 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`는9/21 한 곳이다.9/18 표시 변경은 이관 완료이며 자연 성과 완료가 아니다.9/19 통합 implementation owner를 새 current checklist에 기록했다.

## 제한 재생성·배포

소스 커밋·푸시·immutable release·선택 CAS 및 source9/17/publication9/19/effective9/21 제한 재생성 결과는 `tmp/compact-ai-integration-20260919/`의 실행 영수증과 아래 최종 closure에 기록한다. 광역 main/다른 worker·서비스는 재실행하지 않는다. 보고서 상태/source gap과 scoped 검증, 전체 chain DONE, 정책 선택, PID·자연 비용 후 성과를 구분한다.

## 자연 수용 결손과 다음 owner

현재 frozen 실제 compact screen21건은 stop10·timeout/semantic9·venue/session identity2로 모두 제외다. 실제 비교·후보 호출0, 비용 후 EV 및 일별 순익 Δ는 null이다. 선행 실제 모델 검증도 source gap/holdout missing이다. 이는 measured no-edge 또는 개선0이 아니다.

다음 owner는9/21 체크리스트의 기존 stable ID다. 기존 Main pre-AI observer→atomic plan/stop→lossless execution census→독립 운영 replay→실제 scope별 선행 모델 proof→compact 학습/forward holdout→정규 PREOPEN/PID→joint applied-version completed-cost 성과를 확인한다. 다음 자연 입력이 없으면 계속 source/sample 상태로 남으며 과거자료 반복 재생성이나 generic stop·현재 가격·broker fill 합성으로 닫지 않는다. CI0–CI4 코드/인계 closure와 CI5 자연 EV closure를 혼동하지 않는다.


## 최종 closure

- Source commit `0e86f5d20909221904478a1aa2ec21ea72003c78`을 main 및 review branch에 atomic push하고 관리 root `compact-ai-integrated-reviewed-20260919`를 selector CAS로 선택했다. root/HEAD·src/deploy clean·공유 data/docs/tmp/logs/.venv/restart.flag를 확인했다. router print-plan으로 future main 호출 경로를 확인했으며 bot/service/cron은 재시작·복원하지 않았다.
- prepare/evaluate는 각각1초 이내였고 기존 sealed source projection을 재사용했다. finalize는 candidate/model admission을 재확인하고 publication9/19→effective9/21 정책을 생성했다. late handoff는 재발행 없이 최종 summary/checklist를 결속했다. 독립 strict 명령 `--compact-summary-only --require-summary-handoff`는 exit0/PASS, issues[]다. whole_native_chain_done_claimed=false다.
- Bundle `833053c38872f05269cf1d0fd24c2d777d3133eb2f2a07163fa304633344f07b`; paired `99699f197de1f530d8f77d5363e95a31bebb6dfbc2196aa53c03e11b4b90be4e`. Calibration·optimizer·consumer19·정책21이 같은 proof를 소비한다. 기존 bundle015d의 machine 정책 및9개 scope의 machine/AI 전체를 비교해 unchanged를 확인했다. 보호 원 trace/payload의 inode/size/mtime도 unchanged다.
- 실제 결과는 screen21/excluded21/comparable0/provider0, 비용 후 EV·일별 순익 Δ null이다. economic_comparison_complete=false, candidate_improvement_proven=false, incumbent_preserved다. 선행 실제 모델 proof source_gap/holdout missing과9/17 irrecoverable stop/plan/identity·timeout은 기존 자연 owner의 OPEN acceptance다. 복구 불가능한 자료를 추가 재실행하지 않는다.
- 실제 PID 소비와 자연 적용·실현 순익 개선은 확인되지 않았다. scoped family PASS는 원 native chain의 외부 resource/다른 family·PREOPEN 결손을 해소하거나 DONE으로 덮지 않는다.
- 영수증: [validation](../../tmp/compact-ai-integration-20260919/validation.json), [regeneration](../../tmp/compact-ai-integration-20260919/regeneration.json), [deployment](../../tmp/compact-ai-integration-20260919/deployment.json), [strict](../../tmp/compact-ai-integration-20260919/strict.txt). 자연 owner는 다음9/21 체크리스트의 동일 stable ID 한 곳으로 parser 확인한다.

- Concurrent successor: 완료 기록 push 도중 다른 승인 세션이 `fcfd7b8e5` / `limit-down-retirement-reviewed-20260919-fcfd7b8e5`를 선택했다. source `0e86f5d20`의 descendant이며 compact 구현 3개 모듈과 paired wrapper는 동일하고 main wrapper 변경은 limit-down 폐기뿐이다. prepare/evaluate/finalize/handoff 호출을 실제 successor root에서 확인했다. 최신 선택을 되돌리지 않으며 미래 호출에 통합 구현이 포함됨을 확인했다. 실제 PID·자연 EV 수용 미완료는 동일하다.

## 후속 경제성·구조 리뷰 (2026-09-19)

- 새 finding: additive label revision 재사용이 10m entry_quality_path만 비교해 venue/session primary exclusion 변경·관련 label 삭제/중복을 덮을 수 있었다. 이전 writer가 이미 새 stat/hash를 결속한 cache도 문제였다. 해당 frozen compact 모집단의 exact label 1:1·path·identity exclusion을 재사용 전에 대조하도록 보완했다. 불일치는 원 producer 평가가 필요하며 finalize는 raw 재스캔/provider/정책 발행 없이 차단한다. 다른 cohort의 중복 label은 현재 모집단을 전역 차단하지 않는다.
- 반복 review/fix/re-review: cached projection의 실제 21개 row는 현행 label과 모두 일치(불일치0). stop/timeout/identity 원천 제외21·비교0·EV/일별 Δ null은 그대로이며 이 수정이 실현 이익을 생성했다고 기록하지 않는다. 역사 결손을 다시 계산하지 않고 기존9/21 carry 정책을 보존한다.
- 검증: compact/calibration 244 passed; 최종 cohort-isolation 보완 후 label/source-upgrade7 passed,76 deselected. Python compile·diff check PASS. 회귀는 identity 수정/삭제/관련 중복, 예전 hash-only masking, finalize 원천 재조회 금지, evaluate의 producer 재진입, 무관 cohort 격리를 포함한다.
- 자연 model/holdout/PREOPEN/PID/COMPLETED 성과는 기존9/21 OPEN owner다. 새 sample·원 stop/plan/route가 실제 producer에서 생성되고 선행 실행 모델 검증이 닫혀야 비교가 시작된다. 단순 시간 경과는9/17의 비가역 결손을 고치지 않는다.

## 다음 활성 장후작업: WS 최종화 (코드 변경 없는 분석)

선택 main wrapper에서 evaluate 다음 소스상 분기는 codebase_performance_workorder_report다. 그러나 기본 OFF이며9/17·18 report도 없다. time_window_regime_counterfactual/producer_gap/stage_hook 계열도 기본 OFF다. 현재 Main 기준 다음 활성 producer는 `monitoring.intraday_ws_freshness_monitor --finalize --monitor-only` (#89)다. 이후 compact finalize→Daily machine refresh→EV/코드 작업지시로 이어진다. 정기 main cron은 이번 조회에서 없고 WS 장중5분 cron만 확인됐다. 후속 코드 선택과 설치된 자동 실행을 구분한다. 예약을 복원하지 않았다.

WS 최종화는 원 clock·type/route/session/epoch·시장 상태에 따라 stale/subscription/backoff를 재분류하고 scanner funnel, BBO 경로·비용·prune/hotset CF와 rolling 비교를 만든다. 과거 snapshot은 당시 freshness로만 해석하고 즉시 repair를 권고하지 않는다. monitor-only는 별도 workorder 파일 생성을 생략하지만 report의 workorder_directives를 기존 build_code_improvement_workorder가 소비한다. 현행 final branch는 기존 integrated lookup-attention 평가·정책 producer에도 연결된다. zero-bonus/실행권한 없는 후보 disposition이며 본 작업 단독으로 PREOPEN freeze·주문·실현EV 권한을 만들지 않는다. EV report는 existing selection_handoff를 참조한다.

| 축 | 기존 실제 결과 및 해석 |
| --- | --- |
| 실행 |9/17 최신 report19:45:02, evaluation_phase=intraday; daily prune/hotset finalized=false. native main status는9/18 00:44 command_failed다. 장중 파일을 장후 final/rolling 완료로 간주할 수 없다.9/18 report도 intraday·원천2종 missing·diagnostic source_quality_gap이다.|
| 운영 분모 |9/17 event343,662, decision-stage stale/backoff26,979(7.8504%), both-WS stale971, trade quiet4,039. 이벤트 비율은 경제 손실·개선값이 아니다. unique promotion2,509, eligible-heavy1,525, eligible-no-heavy42; attach lineage2,258/2,258, missing lineage0, immutable metadata conflict0이다.|
| 경제 분모 |실행 BBO CF 후보45,967; 보통주 eligible39,810; exact BBO684; resolved322. KRX coverage4.7564%/resolved305/censored53.2925%; premarket2.4701%/17/45.1613%; aftermarket UNKNOWN24,826/BBO0. 부족하거나 검열된 모집단 EV는 null; cross-venue aggregate도 금지다. 서로 다른 분모를 전부 한 손실률로 합치지 않는다.|
| 있는 EV 진단 |hotset proxy 중 KRX capacity1/target0.3/stop-0.3/20분 한 그룹: resolved114, 비용0.23% 후 EV-0.68532307%, BBO coverage96.319%, censored27.3885%. 검열 상한20% 초과로 비교 ready=false다. 해당 CF 조건 진단값이며 전체 EV·실현 손실·개선 입증이 아니다. 420개 proxy group의 좋은 값을 골라 실제 scheduler 개선으로 해석할 수 없다.|
| 후행 소비 |9/17에는 workorder7(implement_now1/defer6)가 있으나 report는 장중 generation이다. 해당 report에 현행 integrated selection·rolling final receipt가 없으므로 최신 코드에 consumer가 있다는 것과 자연 final 소비 완료는 별도다.|

| 대기/결함 | 해소 조건·owner |
| --- | --- |
| 시간·새 표본으로 해소 가능 |20분 path·timeout BBO가 실제 원천에 계속 기록되는 진행 중 episode와 독립 forward 날짜/완료 거래 부족. 종료 이후 관측 자체가 없으면 maturation이 아니며 검열로 남는다. existing pruned BBO collector/WS final/rolling owner에서20 resolved·검열≤20%·정확한 coverage를 대사한다.|
| 현재 공급/실행 연결 문제 |장후 final receipt 부재와 main installed trigger 부재는 기다리기만 해서는 해소되지 않는다. existing main/controller 실행 owner의 설치·승인·원천/status/final verifier 계약을 확인해야 한다. 이번 read-only next 작업 분석에서는 실행·예약 복원·재생성하지 않는다.|
| 역사 원천 결손 |당시 BBO/venue 누락, prune0s anchor 누락, REST schedule lag417은 이후 시세로 복원할 수 없다. 기존 pipeline/scanner/pruned collector의 다음 자연 generation에서 정밀 venue/anchor/quote freshness를 검증한다. canonical9/17 threshold JSONL은 현재 없다; 보관·partition 실체의 완전성은 별도 owner 확인 전 unknown이며 data 전체 부재로 단정하지 않는다.|
| 모델 한계 |hotset은 first queue-rank capacity proxy, prune은 bounded selected episodes다. 실제 scheduler/capital/비중첩 운용 모델·대조군 검증 없이 전체 prune·실현 순익 또는 최적 capacity로 외삽할 수 없다. 최초 적절한 native pair를 확보한 뒤 기존 lookup-attention owner의 지원 범위로만 경제 비교한다.|

판정: WS 최종화는 원천 품질과 기존 scanner 경제성 후행 연결을 위한 유지 가치가 있다. 현재는 장후 final 공급·BBO coverage/route·censored 원인이 우선이며 성능이나 capacity grid 확장을 먼저 할 근거는 없다. 전체 EV·일별 순익 동시 개선은 미입증이다. 다음 작업 소스·정책·산출물은 변경/재생성하지 않았다.
