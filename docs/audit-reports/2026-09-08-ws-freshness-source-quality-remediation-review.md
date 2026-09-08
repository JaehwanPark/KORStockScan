# #74 / #89 승인 검증·장후 종결 보완 리뷰

작성 기준: 2026-09-08 KST. 범위: 권장 보완 구현, self review/fix 및 직접 consumer 회귀검증. 매매 프로세스·env·operator lock·threshold·주문·provider·API 프로토콜은 변경하지 않았다. 현재 worktree의 별도 장중 작업 변경은 보존했다.

최신 판정은 아래 **2차 결함 보완·최종 재검증**이다. 1차 구현과 당시 판정은 이력으로 보존하며, 특히 당시 부분 observer receipt의 `observe` 판정은 2차 episode 전수 대사로 대체한다. 2차 최종 targeted 검증은 **1,093 passed**, 검토 범위 미해결 코드 finding 0이며 자연 소비·경제성은 별도다.

## 판정과 목적

두 작업을 유지한다. #74는 #11의 최종 원천 재검사이지 새로운 전략 승인 owner가 아니다. #89는 정상 안전 차단/거래 공백과 관측·전달 결손을 분리해 기존 source-only workorder에 연결한다. 비용 차감 후 작은 수익을 반복하는 목적에 필요한 데이터 품질·평가 기회를 보호하되, 수리 완료를 실제 수익 증가로 주장하지 않는다.

| 권장 순서 | 구현 | 권한/완료 경계 |
| --- | --- | --- |
| 1. #74 잘못된 승인 차단 | audit v2의 raw 존재·invalid JSON census·logical SHA256·검사 전후 generation. 공통 consumer의 exact date/boolean/status/gap-count/schema 검증, strict JSON read 및 원자 JSON publish | 기존 결함 행 격리와 unknown-warning 비차단 유지. 정상 legacy exact-date audit는 호환 입력이며 v2 generation 검증 완료라고 표시하지 않음 |
| 2. #89 반복 대기 종결 | main wrapper `--finalize` → 장후 causal/observer receipt 판정 → native source-contract `implement_now` 또는 `observe` | 실제 REMOVE/REG·BUY·재기동을 실행하지 않음. 과거 원천 결손은 복원/완료로 바꾸지 않음 |
| 3. 계측/경제성 분리 | `diagnostic_acceptance`와 self-hashed `daily_prune_economic_receipt`, `rolling_prune_economics`. 최근 10개 source-report 날짜에서 finalized·동일 비용/target/stop/horizon, cohort/venue/session별 독립 누적 | 20 completed / BBO 95% / right-censored 20% 기준 유지. 전체 그룹 동시 통과 조건 제거. positive-only 날짜 선택·현재 날짜 중복·미래/pre-baseline/타 계약 혼합·누락 EV의 0 대체 금지 |
| 4. 증분/보관 효율 | optional threshold mirror 부재를 캐시에서 보존, 등장/소실 때 재구축. 검증된 pipeline gzip archive identity receipt를 생성해 품질 consumer가 압축 원천을 매번 풀지 않도록 연결 | 원천 누락 자체는 숨기지 않음. 기존 압축 검증/제거 owner만 변경된 코드를 다음 정상 실행에서 사용; 수동 archive/cleanup은 실행하지 않음 |

신규 helper는 `src/engine/monitoring/ws_freshness_acceptance.py`에 배치했다. 보고서의 진단·source-only 경제성 계약 소유 패키지이며 engine root에 새 모듈을 만들거나 실매매 owner를 추가하지 않았다.

## 리뷰/수정 루프

- 최초 380개 회귀검증에서 producer→consumer와 누락 원천·잘못된 타입·원천 추가 기록·lossless gzip·증분 mirror 경계를 확인했다.
- 후속 리뷰에서 압축 후 consumer별 대용량 재검사, invalid 단일 그룹 때문에 다른 정상 그룹까지 제외되는 문제, 정상 bounded-capacity rejection 오탐, causal receipt 자체가 비어 있을 때 정상 귀속으로 판정할 가능성을 보완했다.
- producer가 발급하는 self-hash receipt로 날짜별 재생성을 교체 처리한다. 동일 group 중복·경제성 합계 결손은 해당 group으로 격리하고, report hash/authority/비용 계약 자체가 잘못되면 그 source를 제외한다. 빈 날짜·invalid/nonfinal source 날짜도 10개 날짜 window를 점유해 과거 유리한 날짜만 살아남지 않게 했다.
- v2 원천 generation이 달라지면 재감사가 필요하다. 정상 압축 전환은 archiver가 압축/복원 logical SHA256을 대조한 receipt로 연결한다. legacy 압축에는 logical digest fallback을 사용하되 실제 내용 불일치는 허용하지 않는다.
- 정상 safe-block 관측은 `observe`이며 stale 경계를 완화하지 않는다. 근거가 없는 작업은 `source_contract_gap`으로 남기고, 단순 코드 존재를 근거로 구현 완료 처리하지 않는다.

## 실제 기존 결과의 읽기 전용 재판정

9/7 21:42 WS JSON의 5개 기존 native 지시를 메모리에서 새 finalize와 실제 workorder classifier에 전달했다. 원본 canonical report·ledger·generation은 수정하지 않았다.

| 기존 ID | 새 producer → consumer | 의미 |
| --- | --- | --- |
| `order_scanner_eligible_no_heavy_closed_loop` | implement_now → implement_now | heavy-evaluation terminal 귀속 결손을 계속 표본 대기로 숨기지 않음 |
| `order_ws_decision_stage_stale_backoff_attribution` | implement_now → implement_now | stale-backoff 근거 결손을 source-contract 수리로 전달 |
| `order_ws_total_stale_escalation` | implement_now → implement_now | 복구 receipt 결손을 보고; 실제 WS 복구 권한은 없음 |
| `order_ws_trade_tick_quiet_low_liquidity_classification` | implement_now → implement_now | 누적 거래량 근거 결손을 정상 저유동성으로 단정하지 않음 |
| `order_scanner_funnel_executable_bbo_join` | observe → attach_existing_family | 수집 receipt와 경제성 부족을 분리; 해당 cohort의 연구 경제성은 아직 미달 |

이는 판정·handoff 보완 증거이며 네 종류의 과거 원천 결손을 복구했다는 결과가 아니다. 같은 과거일 재실행이나 합성으로 닫지 않고 다음 자연 원천에서 기존 owner가 확인한다. 새 실제 BBO·체결·EV 데이터는 생성하지 않았다.

합성 회귀 fixture에서는 2개 날짜의 10+10 completed outcome, 평균 비용 차감 +0.02% 그룹이 source-only 비교 가능으로 판정되고 별도 희소 NXT 그룹은 hold 상태를 유지한다. 이는 낮은 양수 순EV를 추가 uplift floor 없이 연구할 수 있다는 코드 검증이며 실수익·live promotion 증거가 아니다. 기존 gross +1.3% 기본 귀속과 별도 +0.3~1.3% hotset grid는 변경하지 않았다.

## 검증 및 남은 자연 수용

- 최종 targeted pytest **1,074 passed (17.57s)**. 대상: source-quality hard gate/audit, WS monitor/acceptance, generic workorder, PREOPEN, runtime summary, final verifier, trigger/controller/summary handoff, archive 및 wrapper 테스트. Python compile, `bash -n deploy/run_threshold_cycle_postclose.sh`, `git diff --check` 통과.
- print-only 문서 parser 통과: backlog 32개, `PostcloseSourceQualityGateReview0908` owner 1개. 외부 sync는 실행하지 않았다.
- 구현→self review→보완→재리뷰→targeted validation을 반복한 최종 **검토 범위 미해결 코드 finding 0**. 전체 시스템 무결함, 배포 완료 또는 자연 경제성 acceptance를 뜻하지 않는다.
- 검토 대상은 audit producer/common gate, WS monitor/helper, generic workorder, PREOPEN/runtime summary/final verifier, postclose wrapper 및 pipeline archive consumer다.
- full raw 재생성·장후 전체 실행·실주문·봇 재기동·수동 PREOPEN/env 적용·외부 Project/Calendar sync는 실행하지 않았다.
- 다음 자연 수용은 [기존 `PostcloseSourceQualityGateReview0908`](../checklists/2026-09-08-stage2-todo-checklist.md)에서 audit v2→EV/PREOPEN, WS finalize→workorder, rolling receipt의 날짜/hash를 확인한다. 기존 장중 `RuntimeEnvIntradayObserve0908`과 scanner owner는 실제 source/소비 확인을 계속 소유한다. 새로운 중복 OPEN 항목은 만들지 않았다.
- 이번 범위는 진단·승인 계약 수리다. 실제 운영 소비와 비용 차감 순이익 증가는 별도 미검증 상태다. 조건 미달 그룹은 실주문 후보가 아니며, source-only 비교 가능 그룹도 자체 런타임 적용 권한이 없다.

## 2차 결함 보완·최종 재검증

최종 목적 리뷰에서 발견한 결함과 후속 review finding을 권장 순서로 보완했다. 다음이 현행 코드 판정이며 위 1차 결과를 확장·교정한다.

| 순서 | 발견된 문제 | 보완 및 재검증 |
| --- | --- | --- |
| 1 | 최종 verifier가 공통 검증 loader 대신 raw audit의 승인 값을 직접 사용 | 실제 builder가 EV/PREOPEN과 같은 `load_source_quality_preflight(target_date, artifact_path=...)`를 호출한다. 날짜·boolean·v2 raw generation 검증 결과를 `validated_preflight`로 보존한다. 미검증 v2를 직접 전달하는 helper 호출도 승인을 허용하지 않는다. gzip audit의 격리 handoff는 strict reader로 읽고 결손/손상은 공통 검증 사유로 남긴다. pre-baseline archive 검토에 현재 tuning gate를 소급하지 않는다. |
| 2 | `repair_required_without_cycle_state`를 정상 안전 귀속으로 닫을 수 있음 | missing/unknown/해당 상태는 native source-contract `implement_now`다. 보고서의 원인·receipt 수리일 뿐 WS 재등록·재기동·BUY 권한이 아니다. |
| 3 | observer 객체 결손 또는 20개 episode 중 일부 receipt만 있어도 정상 관측으로 종결 가능 | 설정 receipt, 명시적 eligible census, stable episode별 예정 10개 index와 유효 terminal·owner/route 충돌을 대사한다. 명시적 source-gap receipt는 수집 설명 근거지만 정상 BBO나 0 EV가 아니다. bounded 비선정과 실제 누락을 분리한다. 무표본은 설정/명시적 empty census가 있어야 정상이다. |
| 4 | 당일의 수시간 전 snapshot이 저장된 짧은 tick age 때문에 현재 fresh로 보임 | 장중 snapshot 생성시각·30초 유효성·미래시각을 검증하고 경과시간을 event age에 더한다. 장후는 `*_at_snapshot`, as-of 시각, `current_freshness_usable=false`로 별도 표시한다. 과거 stale 건수는 보존하되 현재 복구 추천으로 바꾸지 않는다. 30초 기준은 보고서 입력 기준이며 매매 freshness guard 변경이 아니다. |
| 5 | WS finalize가 무관한 Main AI R0–R3 flag의 기본값에 종속 | WS finalize 독립 기본 ON. 명시적 OFF는 보존한다. 기존 main wrapper의 master binding → `--finalize --monitor-only` → EV/workorder 순서를 유지한다. |
| 6 | 최근 10개 날짜 rolling 비교에 기존 소목표 hotset grid가 연결되지 않음 | `daily_hotset_economic_receipt` → `rolling_hotset_economics`를 추가했다. 기존 +0.3/0.4/0.5/0.7/1.3% target·stop·capacity proxy·venue/session별 비용 차감 평균 결과, 관측 보유시간, 양수 outcome 수와 날짜당 resolved 관측 빈도를 분리해 보존한다. 겹치는 시나리오 합산·실거래 빈도 해석·자동 정책 선택은 금지한다. |

### 목적·허들·자동화 판정

- 계측 수리 완료에는 양수 EV, 실제 체결, 20개 경제 outcome을 요구하지 않는다. observer의 10개 index 대사는 원래 예약한 수집 receipt의 완결성이지 10개 horizon 모두에서 수익을 요구하는 조건이 아니다. explicit gap/정상 bounded rejection은 정상적으로 설명할 수 있고, 설명되지 않은 누락만 수리 대상으로 남긴다.
- 기존 연구 비교 floor인 그룹별 resolved 20·BBO coverage 95%·right-censor 20%는 유지한다. 95% 미달이어도 정확한 resolved subset은 `diagnostic_resolved_subset_equal_weight_avg_profit_pct`로 검토할 수 있다. 이 값은 전체 모집단 EV·full-fill 품질·실전 승인 근거가 아니다. 비용/원천 결손을 낮은 수익목표로 정당화하지 않는다.
- 모든 그룹 동시 통과, 추가 큰 양수 uplift, Main AI 실행을 WS 진단 종결 조건으로 요구하지 않는다. 작은 순수익도 source-only 비교할 수 있다. 합성 2개 날짜의 10+10개 표본은 평균 net +0.02%, 평균 관측 보유시간 3초, 날짜당 resolved 관측 10개를 보존한다. 이는 코드 수용 테스트이지 실제 빈번한 수익이나 수익률 예상치가 아니다.
- #74는 기존 자동 품질 gate의 검증 일관성을 보완했고, #89는 기존 자동 장후 report→workorder 경로를 보완했다. 두 작업 자체는 신규 실매매 정책을 승인·적용하는 owner가 아니다. `source_only_comparison_ready`가 자동 매수나 PREOPEN 적용을 뜻하지 않으며, 실제 정책 변경은 기존 해당 family의 별도 승인/자동 PREOPEN 소비 계약을 따른다.
- 비용 차감 소수익·반복 기회를 검토할 입력 경로는 보완됐지만 실제 EV 개선은 아직 미입증이다. coverage가 낮거나 새 exact receipt가 부족한 경우 source gap·그룹별 blocker를 그대로 보고하며, 시간이 해결한다고 단정하거나 과거 원천을 합성하지 않는다.

### 추가 self review와 검증

- producer→최종 verifier 연결, raw/gzip 읽기 실패, pre-baseline 격리, incremental cache v13의 receipt 집계·mirror 중복 제거, 정상 no-sample과 누락, snapshot 현재/과거 구분, 동일 target-date 교체, 비용/경제 계약별 rolling 분리 및 source-only 권한을 재검토했다.
- 재리뷰에서 snapshot 과거 stale 건수 소실, current receipt의 pre-baseline 경제 입력, gzip truncate/deflate 손상으로 전체 rolling이 종료될 수 있는 경계를 추가 보완했다. invalid historical source는 해당 날짜를 window에 남겨 둔 채 제외하고 정상 현재 그룹을 보존한다.
- 최종 **1,093 passed (18.38s)**: 1차와 동일한 13개 producer/consumer/automation 테스트 파일 전체. Ruff(이번 변경 경로), Python compile, shell syntax, `git diff --check` 통과. 문서 print-only parser 통과: backlog 32개, 기존 `PostcloseSourceQualityGateReview0908` owner 1개로 중복 없음.
- source-only synthetic fixture에서 producer→report→workorder·verifier까지 검증했으며 운영 canonical report를 수동 재생성하지 않았다. 실행 중인 자연 장중 report 변경은 이 작업의 수동 재생성·경제성 검증 증거가 아니다.
- 코드 repair는 검토 범위 finding 0으로 종결한다. 자연 장후 finalize→workorder, audit v2→실제 최종 verifier/PREOPEN, 새 rolling receipt의 누적은 기존 `PostcloseSourceQualityGateReview0908` 한 항목에서 확인한다. 새 중복 OPEN owner는 생성하지 않았다. 프로세스 재기동·수동 env/lock 변경·주문·외부 sync·commit/push는 수행하지 않았다.
