# 장후작업 결과 점검 지시문

역할: 활성 장후작업이 기계적으로 정상 종료했고, 비용 후 EV·순이익 개선에 필요한 의도한 분석결과를 만들었는지 판정하는 반복 점검 절차다. 문서 열람·편집은 점검 실행 요청이 아니다. 명시적인 결과 점검 요청은 기본적으로 읽기 전용이며, 단회 요청은 실제 as-of 상태를 보고하고 지속 요청은 지정된 종료조건까지 확인한다.

작업별로 **실행 정상성 / 분석 유효성 / 결손·결함 / 달성 가능성 / 직접 소비·다음 조치**를 따로 판정한다. exit 0·DONE·파일 생성·코드 존재·표본 증가를 경제성 성공으로 대체하지 않는다. 후보가 없어도 유효한 비교 끝에 incumbent carry가 나온 것은 의도한 분석결과일 수 있다.

현행 활성 목록은 [장후작업 목록](audit-reports/2026-09-05-postclose-work-inventory.md)이 소유한다. 설치 cron·systemd 유효 설정과 실제 실행 release/snapshot으로 목록을 대사한다. 과거 PID·commit·완료 이력을 지시문에 누적하지 않는다. 원칙·active/observe/OFF·rollback은 [Plan Rebase §1–§8](plan-korStockScanPerformanceOptimization.rebase.md), 실행 ID·Due·Acceptance는 현재 KST 체크리스트가 소유한다. [runbook](time-based-operations-runbook.md), [traceability](report-based-automation-traceability.md), [release routing](runtime-release-routing.md)은 필요한 해당 계약만 읽는다.

문서 자동 현행화는 [게시 계약](monitoring-instruction-refresh.md)을 따른다. 자동 문서 정비가 장후 점검·거래 실행·추천 구현을 호출하지 않는다.

## 1. 완료 목표

대상 거래일의 활성 작업마다 실제 결과와 소비 경로를 확인하고 아래 다섯 질문에 답한다. 보고서 목적이 source-quality·funnel·운영 검증이면 EV는 `not_applicable`로 두고, 유효한 경제성 입력·직접 consumer에 기여했는지 점검한다.

| 질문 | 판정에 필요한 근거 |
| --- | --- |
| 기계적으로 정상 종료했는가? | 대상일 run/PID, 시작·종료·exit/status, 최신 terminal marker, 필수 artifact와 실제 단계별 실패·skip |
| 의도한 유의미한 분석결과인가? | 작업의 primary metric·비교 모집단·비용/exit·incumbent/candidate·holdout·tail·선정/탈락 사유; 진단 작업은 자신의 입력/출력 계약 |
| 결손·결함이 있는가? | 누락/제외/미성숙/상충·join/filter·hash/date·scope·silent fail·count 보존과 영향 범위 |
| 시간이 지나면 결과를 얻을 수 있는가? | 유효 표본의 실제 유입·maturity/기한·남은 조건·가능 최대표본·다음 경계; 구조상 유입 불가능 여부 |
| 결과가 의도한 소비자까지 전달됐는가? | producer→adapter→평가기→candidate/publisher→dated loader 또는 summary/checklist의 동일 generation receipt |

점검 완료는 전수 행의 판정 완료다. 운영 성공·경제성 후보 선정·다음 거래일 정책/PID 소비·자연 실현성과는 각각 별도 상태로 남긴다. 읽기 전용 점검을 끝내기 위해 잔여 구현이나 미래 자연 표본을 완료로 바꾸지 않는다.

### 1.1 Submit drought 최우선 점검·개선 계약

#119 funnel의 exact attempt/cycle과 최초 병목을 scanner 관측→기계 `BLOCK|RECHECK|ENTER_NOW`→실제 compact AI→가격/수량 준비→최종 guard→submit/broker로 연결한다. 회복된 fallback과 terminal veto, raw event와 unique opportunity를 분리한다. 제출 0의 원인이 입력 손상·정상 정책 차단·집행 실패 중 무엇인지 확인하고, source-valid 미진입 기회의 실행가능 후행손익으로 판단한다. drought만으로 threshold·budget·guard 변경을 정당화하지 않는다.

### 1.2 위젯·에피소드 진입판단 공동 최우선 계약

원래 signal→micro checkpoint→admission→주문/leg→holding/terminal과 incumbent reject의 CF를 같은 scope에서 대사한다. actual/source-only arm, raw-only/no-seed와 실제 무신호, 분봉 touch와 executable fill을 구분한다. 같은 기회 모집단·원래 quantity/cap/exit·동시자본 아래 일별 순익·paired delta·tail을 확인한다. 실제 보유가 필요한 timing/exit의 적정 조건은 유지한다.

### 1.3 적응형 청산의 별도 후속 경계

이미 승인된 지속 보조청산은 기존 `data/runtime/machine_profit_stagnation_deployment.json` 및 실제 loader의 policy pin·persistence/유효기간·신규 entry·custody·successor 복구와 정산 receipt를 확인한다. 지속 정책에 매일 새 승인 envelope를 요구하지 않는다. 기존 위젯/episode/manual 보유를 자동 이관하지 않는다. timing 연구 성공으로 새 exit family 활성화·target/수량 변경 권한을 만들지 않고, 미승인 전체 adaptive-exit 설계를 현재 필수 작업으로 복원하지 않는다. 운영 소비와 비용 후 자연 효과는 별도다.

## 2. 권한 경계

기본 결과 점검은 로그·status·report·manifest·systemd·process·lock·소스/consumer의 읽기 전용 대사와 점검 결과 기록이다. 실제 코드 수리·분석 worker 종료/재실행·보고서 재생성·추천 구현·commit/push·release 선택·서비스 기동은 별도 사용자 지시 및 기존 승인 범위를 확인한 경우에만 수행한다. 기존 승인은 그 대상·유효 범위 안에서 유지하며 후보별 재승인 gate를 추가하지 않는다.

호출을 구분한다. `결과 점검`은 조회·판정이고, 별도로 명시한 `장후 운영 모니터링·복구·추천 구현`은 기존 Plan/runbook의 bounded source-only recovery와 §7 구현 계약을 따른다. 문서 정비는 두 실행을 모두 호출하지 않는다.

매매 bot/widget/episode의 기동·종료·재기동, 수동 env/lock/provider/model/route/threshold 변경, 실주문·취소·가격·수량·cap·cooldown 변경과 hard/protect/emergency·stale/conflict·broker/account/order guard 우회는 결과 점검 권한에 포함되지 않는다. 설치된 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop`은 기존 자동 owner의 동작이다. report 복구를 위해 main wrapper를 수동 실행하면 stop 부작용이 있으므로 단순 점검 권한으로 실행하지 않는다.

OFF·퇴역 producer, 유효 frozen policy/checkpoint, 별도 custody/override·expiry를 보존한다. source-only/sim/CF를 실제 주문·실현손익으로 전환하지 않는다. 새 collector·service·timer·cron·DB·production module·운영 stage나 표본 확보용 polling을 만들지 않는다. package 설치/변경과 API retry·호출량·동시성 상향도 포함되지 않는다.

## 3. 현재 장후 실행 owner

아래는 정기 실행 owner다. 상세 활성 producer·조건부 단계·embedded 출력·후행 소비는 [현행 목록 §4](audit-reports/2026-09-05-postclose-work-inventory.md#4-2010-main-wrapper-상세-목록)을 따른다. wrapper의 시작 예약과 내부 단계의 실제 완료 시각을 혼동하지 않는다.

| 예약 | 실행 owner | 기계적 결과와 직접 소비 확인 |
| --- | --- | --- |
| 20:05 | KOSPI EOD update | 대상일 status/log terminal·DB latest date/rows; widget 시장 연구의 EOD 선행 |
| 20:10 | main threshold-cycle postclose | status `succeeded`·최신 DONE·단계 결과·final verifier; final strict closure는 후행 단계 |
| 20:10 | DONE controller | predecessor/follower 대기·실패 reason·JSON `done`; 최신 verifier와 같은 generation |
| 20:10 | tuning monitoring | predecessor 계약·단계 exit/status `success`·Parquet/DuckDB source hash/coverage |
| 20:10 | widget evaluation systemd | advisory→auto policy→EOD wait→signal research→runtime policy의 같은 completed date·unit terminal |
| 20:50 | dashboard DB archive | 최신 대상일 DONE·검증된 archive/source generation·보존 계약 |
| 21:05 | AI entry setup paired replay follower | batch→calibration→optimizer/holding→consumer terminal 또는 근거 있는 disabled |
| 21:15 | machine final refresh systemd | expansion→attribution→hysteresis/timing→native capacity/research closure→approval→checklist·각 rc와 unit terminal |
| 21:55부터, bounded | postclose finalization | predecessor 확인→최신 summary/tower/checklist/strict closure→cleanup→final detector receipt |
| 장후 정기 5분, 21:50까지 및 finalization 후 | System Error Detector | 해당 run/stage/target의 unresolved critical·최신 terminal; 단순 이전 PASS 재사용 금지 |

### 3.1 공통 배포 경로와 독립 서비스 경계

공통 cron은 `data/runtime/runtime_release_selection.json`과 `deploy/run_runtime_release.sh`, widget/episode는 deployment manifest와 유효 systemd `ExecStart/WorkingDirectory/drop-in`을 확인한다. 실제 worker/PID의 root·commit·시작 시 immutable snapshot·source hash를 기록한다. 새 selector나 문서에 적힌 release 이름으로 진행 중인 run을 재라벨링하지 않는다. 서로 다른 owner가 검증된 독립 release를 쓰는 사실만으로 결함으로 판정하지 않는다.

선택 release의 `src/deploy/restart.sh` clean·HEAD와 공유 `data/logs/tmp/.venv/docs/restart.flag` 실체를 확인한다. 코드 고정은 공유 원천·정책·의존성 고정이 아니다. 진행 중인 chain의 코드/입력을 교체하지 않고 배포본 직접 편집·임의 workspace 실행·reset/clean으로 우회하지 않는다. 실제 PID receipt는 코드 소비 근거이며 장후 성공·다음 PREOPEN·수익 근거가 아니다.

## 4. 모니터링 시작

`TARGET_DATE`는 점검할 장후 source 거래일로 한 번 고정하고 자정 이후에도 유지한다. `AS_OF_KST`는 실제 점검시각이다. 현재 체크리스트 목적·강제 규칙, 대상일 미종결 owner, 설치 trigger와 실제 run을 읽고 활성 목록의 기대 결과를 확정한다. 날짜·owner·실행 contract가 없거나 충돌하면 `missing_context|contract_drift`로 남긴다.

조회는 canonical selector와 실제 release를 구분해 수행한다. command/status에는 private token·account 값이나 process 전체 환경을 출력하지 않는다.

```bash
TARGET_DATE="YYYY-MM-DD"
AS_OF_KST="$(TZ=Asia/Seoul date --iso-8601=seconds)"
bash deploy/run_runtime_release.sh --check-cron
bash deploy/run_runtime_release.sh postclose "$TARGET_DATE" --print-plan
bash deploy/run_runtime_release.sh finalize "$TARGET_DATE" --print-plan
```

`--print-plan`은 조회 contract다. 이를 제거하거나 예약 작업을 앞당겨 실행하지 않는다. 설치 상태 조회도 실제 장후 성공으로 세지 않는다.

우선 읽을 근거는 `logs/update_kospi.log`, `logs/threshold_cycle_postclose_cron.log`, `logs/postclose_done_controller_cron.log`, `logs/tuning_monitoring_postclose_cron.log`, `logs/ai_entry_setup_paired_replay_postclose.log`, `logs/dashboard_db_archive_cron.log`, `logs/postclose_finalization_cron.log`, `logs/run_error_detection_cron.log`의 bounded 최신 구간과 해당 대상일 status/report다.

- main status: `data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_TARGET_DATE.status.json`
- verifier: `data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_TARGET_DATE.json`
- controller: `data/report/postclose_done_controller/postclose_done_controller_TARGET_DATE.json`
- tuning: `data/report/tuning_monitoring/status/tuning_monitoring_postclose_TARGET_DATE.json`
- 독립 분석: 두 systemd unit의 Result/ExecMainStatus·journal과 활성 목록에 적힌 producer 출력

큰 원천은 stat 먼저 확인한다. 64MiB 초과 또는 증가 중이면 기존 manifest/요약·streaming index 또는 최대16MiB bounded tail을 사용하고 전체 raw를 반복 스캔하지 않는다. tail에 없는 사건을 모집단 0으로 판단하거나 bounded 관찰을 전체 EV 분모로 외삽하지 않는다. systemd 상태/journal은 bounded 재조회하고 terminal receipt의 실제 시각 순서를 확인한다.

### 4.1 모니터링 시점 체크리스트 실행·점검

현재 OPEN ID의 `Due/Slot/TimeWindow/Track`, 선행 조건·Acceptance를 실제 as-of로 분류한다. 이 절의 기본 행동은 결과 확인이며 미실행 작업을 수동 기동하지 않는다. `[x]` 이력은 해당 완료 범위의 근거이고 현재 owner가 아니다. 이관된 ID는 한 owner로 대사하고 미래·범위 밖·별도 권한 작업도 사유를 남긴다.

## 5. 상태 판정과 지속 모니터링

각 작업에 다음 축을 독립 기록한다. 운영 FAIL, 경제적 부적합과 구조적 원천 결손을 한 색으로 합치지 않는다.

| 축 | 상태와 의미 |
| --- | --- |
| 실행 | `not_yet_due`, `waiting`(유효 선행/기한), `running`(실제 progress), `succeeded`, `valid_skip`, `failed`, `unknown` |
| 분석 | `valid_candidate`, `valid_carry_or_reject`, `valid_diagnostic`, `valid_empty`, `insufficient_mature_sample`, `invalid_source_or_analysis`, `not_applicable` |
| 달성 가능성 | `ready`, `maturing`, `collecting`, `structurally_blocked`, `external_or_authority_blocked`, `unknown`, `not_applicable` |
| 소비 | `verified`, `pending_predecessor`, `not_yet_due`, `missing_or_stale`, `not_applicable` |

`valid_empty`에는 scope 관측·source-valid 분모·무신호/무기회/선정탈락 사유가 있어야 한다. raw missing·지원 scope 없음·early continue로 사라진 행은 정상 empty가 아니다. 단순 sample 0·candidate 0·all BLOCK/all VETO로 실패나 수익 부재를 단정하지 않는다. 반대로 결측 비용/손익/후행경로를 0으로 채우지 않는다.

실행 정상성은 **최신 대상일 terminal + 필수 출력 schema/date/hash/count + intended consumer**를 함께 확인한다. 이전 DONE 뒤 최신 FAIL, unit exit 0 뒤 내부 stage 실패, stale checkpoint/summary, notifier/approval/checklist의 별도 rc, allowed pending verifier를 final strict PASS로 오인하는 사례를 점검한다.

지속 점검은 실제 progress·predecessor/label maturity·owner deadline이 바뀌는 경계에서 재조회한다. 같은 입력을 반복 계산하거나 무제한 waiting으로 남기지 않는다. 단회 요청은 as-of 판정과 다음 조건을 보고하고 종료하며 필수 작업 미종결을 장후 완료로 표현하지 않는다.

### 5.1 EV 관점의 분석 유효성

1. 목적과 Metric Decision Contract의 `primary_decision_metric`, `metric_role`, source-quality/window/sample/cost/authority를 실제 함수·predicate와 대사한다. source-quality/count/운영 진단에는 양수 EV·실체결 floor를 새로 붙이지 않는다.
2. raw→deduplicated→complete/maturity waiting/censored/source gap/role-not-applicable 보존식과 stage간 expected/consumed/excluded/unmatched를 닫는다. event·attempt·unique opportunity를 분리하고 owner/venue/session/epoch/policy/prompt generation을 exact key로 join한다.
3. 실제 실현 headline은 `COMPLETED + valid profit_rate`와 확인된 비용만 쓴다. full/partial/no-fill/HELD, actual/sim/probe/CF를 분리한다. 실행가능한 fill·exit·effective cost·capital 모델이 없는 touch/MFE/분봉 proxy와 hindsight oracle은 진단이다.
4. incumbent/challenger를 같은 frozen opportunity union과 원래 quantity/cap/exit·cooldown/동시자본으로 비교한다. no-submit/no-fill·정상 BLOCK/VETO의 놓친 이익과 회피한 손실을 대칭 평가한다. 기계 BLOCK에 실제 미호출 AI PASS를 가정하지 않는다.
5. calibration에서 후보/family를 고정하고 chronological holdout·paired 개선·stress/tail·자본점유를 확인한다. 실패한 holdout을 다른 family 선택에 재사용하지 않는다. 참여 후보만의 평균·양수 날짜만의 평균·gross win rate를 선정 주근거로 쓰지 않는다.
6. 원래 family의 sample floor·가격/수량·prompt/current policy guard를 evaluator→publisher→PREOPEN/dated loader까지 같은 contract로 대사한다. 일반5/10/20일 동시 floor나 사전 candidate 실체결을 새로 요구하지 않고, 불합리하거나 불가능한 gate는 근거와 소유자를 기록한다.
7. `valid_carry_or_reject`는 유효 비교와 탈락 사유가 입증된 결과다. challenger 없음·coverage 미달·source invalid 때문에 carry된 경우는 그 부족 상태를 함께 남겨 의도한 경제성 분석 완료와 구분한다. CF 기대개선은 actual 일별 순익·R6·자연 정책 효과로 합산하지 않는다.

### 5.1.1 Microstructure의 현행 평가 결속

`microstructure_reaction_context`의 진입 평가는 기존 `ai_action_outcome_calibration`의 기계 case table과 결속한다. 원본 capture hash·snapshot·applied bundle·venue/session을 보존하고 비용/결과 제외 전 수집 분모와 중복 제거 후 결과 분모를 별도로 확인한다. Main/shared-rebound의 window source는 같은 exact snapshot의 명시적 시장데이터 route/item으로 결속하고 scope alias나 broker 비용 route를 대신 넣지 않는다. 누락·충돌은 SOURCE_UNAVAILABLE로 유지한다. 통계는 상세 행200개 export 전에 계산한다. 보조 AI는 machine `ENTER_NOW`의 exact snapshot join·실제 provider 호출·등록된 prompt/verdict·source partition만 평가하며 기계 미진입의 AI 미호출은 N/A다.

기존 비용 source producer는 main wrapper의 긴 raw/research 작업 전에 같은 날짜의 원천을 확보한다(`ai_action_outcome_calibration --write --ensure-economic-reference-only`). 비용 입력은 report 아래 private namespace로 작성하며 live provider budget/lock/env를 발행하지 않는다. 기존 검증 원천은 보존한다. 통합/프리마켓 시장데이터 scope의 비용은 검증된 snapshot의 명시적 broker route로 조회하고 scope label은 변경하지 않는다. 누락·충돌 route와 복구 불가 과거 당일 원천은 source gap/null이다.

전용 raw 재스캔·구 entry funnel·독립 누적 연구/rollup/backfill 장후작업은 폐기한다. 실시간 특징·holding/entry 안전 소비와 별도 `machine_microstructure_attribution`/정책 경로는 유지한다. legacy 통계는 N/A이며 구 보고서가 없어도 정상이다.

후행 calibration `--write`는 전체 case의 통합 진단을 날짜가 같은 microstructure 보고서에 가볍게 갱신한다. EV/runtime summary는 이 원천 계약을 직접 소비하고 부모 보고서 hash가 바뀌거나 없으면 source gap으로 표시한다. 부모의 날짜·calibration schema·diagnostic-only 권한과 기존 modern 보고서의 false apply/runtime 권한도 재검증한다. 진단 지표는 기존 labeler window·owner sample/promotion gate·source-quality 선언을 포함한다. 기존 가격 labeler의3분 window 마지막 관측값에서 검증된 full-cost estimate를 차감한 값은 관측 endpoint lag까지 명시한 CF 진단이다. 실제 completed EV/순익·인과 ΔEV와 합산하지 않으며 별도 tuner·정책 승격·런타임 권한을 만들지 않는다. 선정/발행/PREOPEN은 기존 기계·보조 AI의 source/terminal/holdout/promotion gate를 따른다.

마지막 calibration 뒤 EV report가 exact-date microstructure 원천을 직접 읽고 runtime summary가 같은 EV 계약을 소비한다. strict handoff는 원천·EV·runtime의 modern 부모 SHA와 diagnostic-only 권한을 대조하며 missing/changed parent는 active 인계 결손이다. Daily에는 microstructure 요약이나 scanner selection handoff를 복제하지 않는다. full-cost 결손은 경제성 source gap으로 보고하고 무기회/no-edge와 구분한다. 의도된 전용 작업 폐기를 delivery coverage 실패나 retired owner 복원 업무로 바꾸지 않는다.

### 5.1.2 Market weakness 원천·날짜 인계

휴장 또는 명시된 무수집일에는 새 forward partition/진입 부재를 수집 장애로 판단하지 않는다. Scheduled snapshot/observer health는 기계적 소비 증거이며 실제 거래세션의 유효 호가·자연 행동·경제성 표본과 분리한다. 운영 휴장 조건과 market-day 함수가 충돌하면 공식 거래일/운영 조건을 대사하고 실제 다음 적용일을 확정한다. 이전 source_date/target을 복사·relabel하거나 publisher 시간창을 우회하지 않는다.

Notifier의 장중 threshold 변경 차단은 유지한다. 다만 fallback→검증된 dated carry에서 policy hash·발동/해제 횟수·최소 간격이 모두 동일한 경우는 출처 복구로 인계하고 기존 latch/streak를 보존한다. Candidate promotion·역방향 fallback·값/hash 변경에는 이 예외를 쓰지 않는다.

`machine_microstructure_attribution`의 dated 원천→기존 hysteresis tuner→다음 정확 KRX 날짜의 immutable source snapshot/정책→collector/notifier 소비를 확인한다. 승인 후보가 없는2/3 carry와 baseline fallback은 hash가 같아도 source_date/source/status로 구분한다. Source-only scanner/research-watch/auto-discovery의 calibration admission은 live active owner 등록이 아니다. 기존 active execution owner의 모든 route는 보존하고 prospective budget4(상한8)은 독립 적용하되 전체200symbol/400item cap과 legacy v3 shared-budget 소비 계약을 유지한다. Integrated aftermarket는 명시된 `krx_nxt_integrated`/`KRX_NXT` 계약이 있을 때 SOR 관측 item으로 결속하며 실제 체결 venue를 추정하지 않는다.

Dated collection manifest는 Main의 기존 publisher→WS0B/0D callback에서 자연 소비해야 하며 파일 생성/시장 관측 health를 continuous depth/H30 확보로 대신하지 않는다. Main/PREOPEN block은 기존 owner가 strict 계약으로 해소하고 수동 env 우회·새 collector/cron·표본용 주문은 금지한다. Prospective signal의 planned quantity를 후행 fill에서 추정하지 않는다. 기존 후보 grid/floor/holdout/비용/guard를 유지한다. 실제 적용 버전은 observation ID와 immutable policy/source identity→owner decision/lifecycle→COMPLETED+valid cost/profit로 결속하며 model ΔEV와 실제 EV/순익을 분리한다. Missing은 null이고 source gap은 no-edge가 아니다.

장후 `panic_sell_defense_report` 재실행은 제거됐다. 사용자 승인으로 과거 standalone panic 산출물·사본은 삭제됐으며 과거 생성물 부재를 복구/재생성 작업으로 열지 않는다. 장중 current-session 결과와 runtime state/정책은 보존한다. 장후 wrapper의 호출·대기·전용 flag·DONE 필드 및 strict verifier의 panic 필수 산출물 요구가 없다. 일일 보고서는 동일 날짜에 남아 있는 장중 panic 결과를 선택적 진단으로 읽고 generated_at/as_of·analysis_status·원천 결손을 보존한다. 부재는 unavailable이며 정상 무거래·경제성0·장후 생성 성공으로 대체하지 않는다. 별도 장후 breadth 수집과 `machine_microstructure_attribution → market_weakness_entry_response → market_weakness_hysteresis_tuning` 경로는 유지한다.

장중 panic wrapper의 default scheduled 호출은 기존 strict selected-release 계약으로 reviewed source를 소비한다. Invalid selection은 작업본 fallback 없이 실패하며 명시된 PROJECT_DIR operator/test 경로와 cron은 보존한다.

기존 final-refresh service의 배포 source pin은 WorkingDirectory/ExecStart/PYTHONPATH/PROJECT_DIR/PYTHON_BIN을 동일 reviewed root로 맞춘다. 실행 중 worker를 변경/재시작하지 않고 미래 실행 binding만 갱신하며 소비 PID receipt를 별도 확인한다.

### 5.1.3 조회 관심도 scanner 평가 통합

조회 원천/점수/freshness·promotion/prune/attach·BBO 관측과 fact mart는 유지한다. 독립 lookup tuning 장후 CLI/정책 publisher/flag/DONE/wait는 폐기하고 기존 `intraday_ws_freshness_finalize`의 `scanner_unique_funnel.economic_cohorts.lookup_attention_selection`을 소비한다. 장중은 기존 native 변경분 수집만 하며, 최종은 fingerprint 변화에만 bounded 평가한다. 원본90일 재스캔·giant state migration을 새 반복 단계로 넣지 않는다. 운영 command와 구현 경계는 [LA0–LA6 계획](proposals/scanner-lookup-attention-evaluation-consolidation-and-runtime-plan-2026-09-18.md) 및 owning review를 따른다.

Exact integrated section/date/hash를 Daily→EV/summary→strict와 단일 execution policy까지 결속한다. Full same-budget 실행/청산/요청량/guard/cost/자본 원천과 독립 검증이 없으면 primary EV/순익은 null/source_gap이며 가중치0 정책만 발행한다. Sampled BBO/snapshot 및 high/low COMPLETED 평균은 diagnostic으로 유지한다. 현행 existing CF owner의 exact replay 미구현은 시간만으로 해소되지 않으며 active promotion은 fail closed다. observed source date와 expected non-collection publication/next effective date를 분리하고 실제 target PREOPEN window 밖 receipt 발행은 금지한다. Parent monitor/전체 chain terminal과 lookup section 갱신은 별개다. Frozen 원본 hash/분모/비용/경제성 및 source-only successor provenance를 보존한 manifest 뒤 불필요 standalone 출력만 삭제한다.

### 5.1.4 Scale-in 체결 실적 조건부 평가

`scale_in_split_order_plan`은 exact trade fact-sync receipt 뒤, Daily/EV 앞에서 실행한다. 최근20 report date의 Main/default custody·AVG_DOWN·EXECUTED/receipt_confirmed 실제 체결 census를 먼저 확인한다. 새 full-fill COMPLETED outcome/revision과 유효 가격·lot·기존 WS quote provenance가 있을 때만 기존 grid를 평가한다. 무체결·비대상·미성숙·변경없음은 raw/replay/grid를 열지 않으며 missing catalog/source는 blocked/null이다. 기존 fact-sync의 원본 scan에서 actual ID projection을 함께 보존하고 새 수집기/API/고빈도 capture는 추가하지 않는다.

v4는 실제 incumbent control·관측 depth의 보수적 체결 모델·공통 cohort·독립 날짜 calibration/미사용 holdout·단일 challenger 검증과 비용모델 표시를 요구한다. v3 outcome은 제외 근거 진단이며 자동 승격 근거가 아니다. 조건부 skip도 날짜별 기존 주문 보존 정책을 원 source/approval age와 함께 발행한다. `--preopen-date`는 적용 예정 개장일을 명시할 수 있으나 calendar/기존 PREOPEN·operator·hard safety를 대체하지 않는다. Report/policy hash·effective date를 확인하고 available dated unsplit와 split activation/PID/실제 경제성을 분리한다. [CS0–CS6 owner](proposals/scale-in-split-order-plan-fill-conditioned-economic-tuning-improvement-plan-2026-09-18.md)와 기존 checklist stable ID를 따른다.

### 5.1.5 Compact auxiliary의 paired 경제성 평가·마지막 consumer

등록된 current compact PASS/VETO 역할의 실제 `ENTER_NOW` screen을 기존 batch의 `--compact-only`로 평가한다. GPT-5.4 nano/provider 고정, 기존 source-quality·provider budget·등록 prompt를 유지하며 legacy BUY/WAIT/holding selector는 이 분기의 선행 조건이나 승격 근거가 아니다. `--execute-compact-candidate`는 유효 입력·비용·terminal이 있는 누락 응답만 기존 executor로 처리한다. 후보/입력 checkpoint가 같으면 응답은 재사용하고 경제성 원천만 다시 결속한다. 동일 verdict는 Δ0으로 공통 모집단에 포함하며 CAUTION 후속 routing 미확정·손절/owner plan/portfolio 결손은 null로 남긴다.

`--finalize-compact`는 기존 calibration/optimizer/Main publisher/consumer와 Daily·EV·runtime approval·tower의 해당 section 및 적용일 checklist를 결속한다. `--publication-date`는 명시적인 successor 발행일이며 관측 source date를 바꾸지 않는다. 양수 independent holdout·동일 cohort·비용 후 EV와 공통 자금 일별 순익·tail/stress·미사용 holdout 증거 없이는 기존 정책을 carry한다. Runtime inference 비용 차이/원화 환산 결손도 승격 근거에서 제외한다. 초기 canary는 KRX regular/KRX route 한 cohort이며 다른 scope의 정책은 유지한다. PREOPEN 동결 이후 해당 날짜 generation은 덮어쓰지 않는다.

Entry owner 재사용은 legacy 고정 기간 `arms`가 아니라 독립 운영 청산 `operating_arms`의 비용·budget·stress·terminal hash를 소비한다. 검증 모델 scope/구현 버전이 일치하고 actual model calibration/holdout의 완료 가용 시점이 compact 학습보다 앞서야 한다. 모델 미지원·버전 불일치·운영 청산 결손은 승격 근거에서 제외한다. 일별 순익의 한 포지션 예약은 최초 주문 관측부터 청산까지 적용하며, 정상 atomic 운영 JSON generation의 크기를 이유로 누락 입력으로 바꾸지 않는다.

Family strict 명령 `src.engine.verify_threshold_cycle_postclose_chain --date SOURCE_DATE --compact-summary-only --require-summary-handoff`는 최종 parent/정책/summary/checklist generation을 검증한다. PASS는 이 family의 연결 closure이며 전체 native DONE·실제 PID·주문·경제성 개선의 증거가 아니다. native는 Daily 뒤 family finalize/strict, 기존 21:05 follower는 bounded compact batch→finalize→strict로 실행한다. Cron/retired selector를 복원하거나 전체 native를 재실행하지 않는다. [CP0–CP5 계획](proposals/compact-auxiliary-ai-paired-economic-tuning-and-consumer-closed-loop-improvement-plan-2026-09-18.md)을 따른다.

### 5.1.6 AI quality source-label 통합

`ai_decision_quality --mode postclose --write`의 v2 current 계약은 control·outcome labels 두 artifact다. Legacy generic baseline은 라벨의 diagnostic section 및 현행 calibration machine case table에서만 평가하며 가격 proxy·WAIT/DROP 비노출0을 비용 후 EV/실제 순익/승격 근거로 승계하지 않는다. Native standalone baseline/legacy paired preparation/retired canary lifecycle의 필수 write/wait는 없다. `scalping.micro_reversion.ai_quality_cycle`의 R0–R3 독립 연구·R2/R3 인계·전용 PREOPEN/live adapter는 사용자 지시로 완전 폐기한다. 기존 환경 플래그나 과거 승인 산출물로 복원하지 않는다. Current compact finalization→dated policy→consumer→summary/family strict는 독립 실행을 유지한다. 공용 consumer는 퇴역 R0–R3 입력을 읽거나 재생성 acceptance를 발행하지 않으며 optional factorial 경로는 retired로 종결한다. 퇴역 입력을 소비하던 standalone optimizer CLI도 실행하지 않는다.

원 labels·pending/raw·원 비용·모델/후보 holdout·actual/order/custody/version evidence를 보호한다. Revision은 원 bytes/hash를 보존하고 label hash·source manifest·구현/config generation을 case table과 compact projection에 결속한다. 동일 입력은 기존 cache/checkpoint를 재사용하며 additive metadata 갱신만으로 대형 raw 재스캔/가격·provider 호출을 하지 않는다. 기존 frozen 보고서의 명시 migration은 `legacy_labels_preserved_not_revalidated`로 기록하며 원 exclusions/as-of를 보존한다. 유효 horizon 미도달은 pending, 이미 지난 고정 원 window 누락은 source gap·null·정확 owner/closure다. 잘못된 route/schema/response는 source gap이며 미래 가격/임의 stop·cost·SELL로 복구하지 않는다. 이 진단 section의 결손은 독립적으로 유효한 owner CF까지 전역 차단하지 않는다.9/21 dated 준비 policy는 검증 양수 후보가 없으면 incumbent carry다. 정규 PREOPEN·PID·자연 완료 비용 성과는 별도 OPEN이며 family strict PASS를 전체 native DONE/EV 개선으로 보고하지 않는다. [구현 review](audit-reports/2026-09-18-ai-quality-source-label-consolidation-review.md)의 exact-date receipt를 확인한다.

### 5.1.7 Entry cancel-wait 실제 제출 조건부 평가

독립 `entry_cancel_wait_runtime`의 기존 CLI 위치를 유지하며 lossless 제출/cancel projection census와 durable Main BUY 원장을 함께 확인한다. census 결손을 제출0으로, 미해결 이전 custody를 무노출 순익0으로 간주하지 않는다. 실제 제출이 있으면 frozen timeout/profile/route·native quote/trade·cancel ACK/late inventory·운영 exit/cost를 기존 entry owner에서 비교하며 미지원 상태는 null이다. 고정 제출 notional EV와 같은 자본 평균 일별 net의 보수적 하한을 함께 통과한 학습 후보 하나만 미사용 policy holdout에서 평가한다.

새 schema report 및 dated scope policy를 tower/checklist source generation에 결속하고 standalone PREOPEN과 `_resolve_buy_order_timeout_sec`에서 검증한 scope만 소비한다. 공통 timeout·명시 OFF/override·order/guard/provider 권한은 보존한다. 원 평가일을 유지한 지연 발행은 publication date/다음 거래일을 명시한다. 사용자 승인과 closed review 이후 필요한 해당 CLI만 재생성하며 `--entry-cancel-wait-summary-only --require-summary-handoff`의 PASS는 전체 native DONE·PID 소비·자연 경제성 수락이 아니다.

### 5.2 결손·결함과 달성 가능성

| 판정 | 입증할 내용 | 다음 조치·closure |
| --- | --- | --- |
| 정상 maturity 대기 | source-valid label이 선언 exit/window의 cutoff까지 아직 미성숙; 남은 수·deadline | 해당 시각의 complete/censored receipt 확인. 모든 horizon 완료를 일괄 요구하지 않음 |
| 정상 표본 축적 | producer/consumer ON·usable 유입 실제 관측·eligible floor와 denominator가 동일 | 유효 유입률·남은 표본·source day를 기록하고 다음 경계 재판정 |
| 구조적 불가능 | 지원 scope/실제 signal 없음, 불가능 join, upstream에서 필요한 행 삭제, no-submit 연구에 actual fill 강제, 비용/exit 미정의, native menu/receipt 미발급, consumer 미설치, 절대0 유입 | 직접 owner·결함 함수/predicate·필요 source/adapter/contract와 closure test. 시간 대기로 해소된다고 보고하지 않음 |
| 복구 불가 과거 결손 | 당시 packet/attempt/cost/window가 수집되지 않았고 입증 가능한 동등 원천 없음 | diagnostic/exclusion/null 보존. 새 원천으로 과거를 재라벨링하거나 동일 replay를 반복하지 않음 |
| 권한/외부 차단 | 새 live/universe/provider/exit 권한 또는 외부 원천·서비스 필요 | 해당 필요조건과 owner 명시. 기존 승인된 bounded family에 후보별 재승인을 추가하지 않음 |
| 판단 근거 부족 | 유입률·원천 보존·consumer/contract 중 미확인 항목 | `unknown`과 필요한 읽기 전용 확인. 무조건 내일·며칠 후 완료라는 ETA 금지 |

시간 경과로 성과가 날 가능성과 경제적 수익성을 분리한다. 유입률이 확인되면 남은 floor/관측 유입률로 **증거 확보 예상 구간**을 조건부 제시하고 owner 시간창·최대 유입 수·source 유효기간을 고려한다. 0유입·미설치·구조결손·계약불명은 ETA null+원인이다. 표본이 늘어도 비용 후 paired delta가 음수이거나 tail guard를 통과하지 못하면 `valid_carry_or_reject`이며 수익 개선 ETA를 약속하지 않는다.

### Source-quality final 감사 재사용과 역할별 소비

`observation_source_quality_audit` final skip은 pure `--audit-phase final --check-reusable`로 phase·구현·원 generation·machine/AI/provider/funnel content binding을 확인한다. Preflight 또는 metadata만으로 final을 대신하지 않는다. 원 raw contract aggregate와 final consumer census는 별도 계산이다. 검증된 이전 projection을 이관할 때만 `--verified-projection-source`의 원 receipt/code/관측 stage 의미를 검증하며, 실패는 blocker이고 수동 전체 raw bootstrap 근거가 아니다. Final에서 verified aggregate가 없으면 raw를 열지 않고 실패한다. 원천 contract aggregate 생성은 기존 preflight/manual owner의 별도 실행이며 final skip 해제와 혼동하지 않는다.

Source input allowed, decision CF input allowed, operational terminal reconciled, cost-adjusted economic comparison eligible을 분리한다. Submitted/guard/reject는 운영 연결이며 COMPLETED 비용 손익이 아니다. Exact gap/pending만 운영 평가에서 제외하고 유효 BLOCK/RECHECK/VETO partition은 보존한다. 역사적 terminal 부재는 원 분모·null로 유지한다. Unknown provenance는 기존 native workorder ID에 field producer/disposition/closure test를 인계한다. 이 감사는 정책 생성기가 아니며 후행 검증에서 후보가 없으면 dated incumbent carry를 유지한다. [Q0–Q5 구현 계약](proposals/observation-source-quality-final-audit-terminal-lineage-and-economic-consumer-defect-remediation-plan-2026-09-18.md)을 따른다.

## 6. 실패 대응

읽기 전용 점검에서는 최초 영향 producer, affected row/window/scope, downstream 소비·승격 영향, blocker owner/artifact, 필요한 조치와 closure test를 기록한다. identifiable bad row/window는 제외하는 계약이 기본이며 전체 block은 invalid/missing preflight·격리 실패·특정 불가능한 high-volume contract loss일 때만 인정한다.

수리·재실행이 이미 승인된 범위이면 `$korstockscan-review-gate`의 구현→review→finding 수리→re-review→targeted validation을 반복한다. 검증 후 **최초 영향 producer→직접 downstream→intended last consumer**만 같은 대상일/hash로 최소 재생성한다. stale해진 EV/summary/gap/lineage→tower→checklist→strict verifier `--require-summary-handoff`→controller/finalization을 해당 범위로 닫고, 이전 PASS로 최신 실패를 가리지 않는다.

진행 중 worker/lock은 실제 PID·시작/progress·owner deadline부터 확인한다. lock 파일 존재만으로 stale이라고 삭제하지 않는다. immutable 실행 세대·valid checkpoint·frozen published policy·원래 custody를 보존하고 끝나지 않은 HTTP/worker를 terminal로 가장하지 않는다. 매매 owner 변경이나 새 권한이 필요한 수리는 해당 근거를 보고하고 종속 mutation을 수행하지 않는다.

## 7. Implement-now 및 위젯·에피소드 추천 2-pass 구현

이 절은 **추천 구현이 별도 지시된 경우의 계약**이다. 일반 결과 점검은 원래 native ID/decision·현재 disposition·intended consumer·acceptance·권한·source hash를 확인하며 코드를 구현하지 않는다. runbook의 구현 workflow에서 이 절을 참조할 때에만 아래 closure를 수행한다.

1. terminal authoritative generation의 main/widget/episode 추천 전수를 intake한다. canonical/projection/approval ledger를 중복 합산하지 않고 `unchanged/new/removed/decision_changed`를 대사한다. 근거 없는 상충/중복과 미분류 행을 보존한다.
2. 실제 `implement_now|code_patch_required` 및 구현 위치·consumer·test·비권한 계약이 있는 objective followup만 eligible하다. `runtime_effect=false`, `allowed_runtime_apply=false`를 artifact와 실제 영향에서 확인한다. 공유 runtime kernel의 BUY/WAIT/SELL 변화는 report-only 수리가 아니다.
3. Pass 1 구현→finding0→targeted validation→최소 영향 재생성 후 Pass 2에서 새/변경 추천을 재대사한다. 반복은 횟수가 아니라 eligible new/changed0·intake/implement-now unaccounted0·eligible actionable open0·review finding0과 최신 필수 terminal로 닫는다.
4. 검증한 disposition은 기존 companion에 native ID·row/source hash·review/test/직접 consumer 근거로 기록한다. 과거 완료 일괄 복사·합성 authority·신규 live/universe/quantity/target/provider/safety 권한 상속은 금지한다. evidence/external/user-authority 차단은 구현 완료가 아니다.

## 8. Owner별 필수 확인

아래와 활성 목록의 작업별 항목을 모두 대사한다. 논리 작업이 같아도 source generation별 반복 출력은 actual callsite/receipt로 확인하며 stage 번호를 신규 실행 ID로 만들지 않는다.

### 8.1 Main threshold-cycle

입력 freeze/compact·#11/#74 품질·실제 기계/compact 사례→가격/수량·leg→Daily/calibration→EV/cumulative→candidate/publisher의 counts·비용·정책 결속을 확인한다. 기계 threshold, compact instruction, numeric price, 초기 quantity/leg와 AVG_DOWN의 공통 반등 신호 소비·holding/exit owner를 분리한다. `entry_cancel_wait_tuning`의 touch/mark proxy는 executable fill/exit/cost가 없으면 diagnostic hold이며 시간 축적으로 자동 경제성 자료가 되지 않는다.

PYRAMID 판단·주문과 intraday feedback/quality calibration, AVG_DOWN 독립 recovery calibration·budget 계좌 수집·exit replay capture는 사용자 지시로 폐기했다. 과거 paired economics 보고서는 archive-only이며 현행 필수 산출물·후보·carry·승계·복원 업무가 아니다. wrapper/직접 CLI/과거 env·lock·report가 이를 재활성화하지 않는지 실제 consumer를 확인한다. 기존 pending/체결/완료 원장은 정산·감사에 보존한다.

AVG_DOWN은 현재 Main holding bars와 WS tick/BBO로 공통 Main 기계 entry 정책의 같은 venue/session 반등 ENTER_NOW를 소비한다. 공통 entry 장후 학습/publisher→PREOPEN bundle→실제 PID→반등 source signal/version/hash·episode/decision→기존 AI/현금/수량/cap/pending/exit/가격 guard→자연 ADD/blocked→COMPLETED 비용 원장을 추적한다. 삼성/widget/episode 전용 rebound source나 sim/CF를 Main 실제 신호/이익으로 바꾸지 않는다. 별도 AVG_DOWN threshold 후보/승격을 요구하지 않는다.

실제 적용 code/machine 버전별 episode를 중복 제거하고 rolling/cumulative 비용 차감 EV·순익·tail·노출·모델 오차를 평가한다. 기존 Main entry 모델 ΔEV는 실제 AVG_DOWN 증분 이익과 별도이며 missing/censored 비용·결과는 null이다. policy/source/scope 결손·stop/pending/common guard 차단·유효 반등 부재·미성숙 결과를 구분한다. candidate0은 폐기한 독립 튜닝의 실패나 복원 사유가 아니다. 손절 직전 강제 추가매수·손절 유예를 반등 정책으로 복원하지 않는다. code/PREOPEN/selected release/PID/자연 행동/실경제성을 별도 판정하며 당일 기존 Acceptance owner를 따른다.

`RISING_MISSED_ONE_SHARE_ENTRY` 신규 scout·upgrade 주문 및 scanner async commit adapter, 전용 `one_share_threshold_opportunity`·`rising_missed_scout_workorder` 장후 생산/소비는 9/18 사용자 지시로 폐기했다. 과거 env·보고서·workorder 반복 결함 처리에서 복원하지 않는다. 일반 BUY bridge와 그 TP1 안전 판정, 공통 sizing/주문/holding/exit 및 기존 체결 정산은 계속 사용한다. 전용 산출물 삭제·검증·선택 release는 [폐기 review](audit-reports/2026-09-18-rising-missed-scout-retirement-review.md)를 따른다.

`entry_recheck_drought_controller`와 `entry_opportunity_recheck_runtime`의 전용 score/WAIT 복구 판단·pending/WS handoff·submit budget·장후 maintenance·PREOPEN 후보/승계·전용 산출물은 9/18 사용자 지시로 폐기했다. 필수 산출물·복구·source gap 대기 업무로 다시 요구하지 않는다. 정상 machine의 RECHECK와 보조 AI, 공통 `buy_funnel_sentinel` 제출병목 진단 및 source-only workorder 계약은 기존 owner가 계속 담당한다. 과거 실제 주문의 pending/체결/완료 손익 원장과 그 정산은 보존한다. 작업본 폐기와 selected release/PID 반영은 [폐기 검증](audit-reports/2026-09-18-entry-recheck-drought-retirement-review.md)에서 구분한다.

### 8.2 DONE controller와 AI replay

wrapper terminal, 21:05 follower lock/terminal과 calibration/optimizer/holding/consumer generation을 대사한다. Provider0 metadata closure와 실제 replay·current compact 연구를 분리하고 disabled 또는 legacy source를 현재 prompt 효과로 재라벨링하지 않는다. controller DONE이 latest strict summary closure를 포함하는지 확인한다.

### 8.3 Tuning monitoring과 archive

late-pass의 expected/consumed/excluded, raw/compact→Parquet/DuckDB partition/date/hash와 archive 보존·검증을 확인한다. 조회속도·중복 read 절약은 EV 개선 증거가 아니다. 정상 artifact reuse에는 source hash·cutoff·직접 consumer 검증이 필요하다.

### 8.4 Widget evaluation과 추천

네 producer의 completed date와 EOD date/rows, raw/advisory seed·before-confirmation signal/BBO·incumbent rejects·census·CF union·holdout·capital·policy/carry를 대사한다. raw-only와 no opportunity, source-valid0과 candidate0를 구분한다. source-day/actual consume/version acknowledgement가 빠졌으면 코드/발행 성공을 whole-loop 완료로 표시하지 않는다.

### 8.5 Episode machine과 추천

Samsung actual-policy tuning·low-price actual/HELD·expanded study/catalog·timing research/approval을 각각 검증한다. 실제 signal anchor와 prospective diagnostic, 실제 체결과 minute proxy를 구분하고 동일 holdout family 재선택·actual gate의 CF lane 오적용을 점검한다. profile/target·원래 수량/leg·무손절·manual custody와 별도 approved override를 보존한다.

### 8.6 Machine final refresh

expansion·attribution·hysteresis·timing·native capacity·research closed-loop·approval·checklist의 rc와 최신 artifacts를 전부 확인한다. 후행 성공으로 이전 producer 실패를 가리지 않는다. allocation/census·실제 decision/source/menu/cost/exit·next-date publication·actual consumer/version attribution의 미완료가 표본 대기인지 구조결손인지 각각 판정한다.

### 8.7 Finalization과 error detector

main/controller/tuning/widget/replay/machine/archive의 predecessor terminal을 대사하고 최종 summary generation·tower/checklist·strict verifier/controller→cleanup→final detector 순서·hash를 확인한다. generic detector PASS와 `postclose_final_detector`를 구분한다. wrapper cleanup DONE·detector handoff 시작만으로 실제 detector terminal 성공을 가정하지 않는다.

### 8.8 다음 거래일 PREOPEN·07:55 기동 handoff

각 active family의 next-trading-date candidate 또는 유효 incumbent carry·선정/탈락 사유·source/policy/hash·frozen generation을 PREOPEN resolver/독립 dated loader까지 확인한다. 아직 도래하지 않은 PREOPEN·기동·actual PID/R6·실현순익은 `not_yet_due`와 기존 Acceptance owner로 남긴다. 장후 발행 성공이나 경로 통일은 다음날 실제 기동·주문·경제성 성공이 아니다.

## 9. 최종 판정과 보고

활성 목록의 각 논리 작업에 한 행을 작성한다. 상위 owner 정상종료 표만으로 내부 분석 전수 점검을 대신하지 않는다. 반복 요약/EV 출력은 같은 작업 행에 generation별 마지막 소비 근거를 결속한다.

| 작업/기존 index·owner | target/as-of·run/source hash | 실행/terminal | 의도한 결과·primary metric/paired 근거 | 분석 판정 | 결손·결함/영향 행 | 달성 가능성·다음 경계/ETA 근거 | 직접 소비·다음 조치/closure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 활성 목록의 각 작업 | | | | | | | |

보고의 첫 문장은 **운영 종결 / 분석 유효성 / 경제성 선정 / 구조 차단**을 각각 요약한다. 운영은 `진행 중|정상종결|실패|미확인`, 분석은 유효/부족/무효 행 수, 경제성은 선정/유효 carry·reject/증거 부족, 구조 차단은 직접 owner와 원인으로 제시한다. 정상 운영 종결과 수익 개선을 한 GREEN으로 합치지 않는다.

이어 확정 결함·source exclusion·구조적 blocker부터 `판정→직접 근거→다음 조치`로 보고한다. 자연 maturity/유입 대기에는 실제 수와 다음 경계를, 불가능하거나 불명인 경로에는 ETA null과 closure test를 남긴다. 이전 완료·PID·배포 이력, 일반 원칙 반복과 무관한 후보는 나열하지 않는다. 원래 OPEN ID를 재사용하고 전체 Acceptance를 만족한 행만 닫는다. 문서/checklist 기록을 바꿨으면 print-only parser·링크/owner·diff를 검증하고 외부 sync는 실행하지 않는다.

### Daily paired 경제성 bounded 갱신

공통 `daily_threshold_cycle_report`·`threshold_cycle_ev_report`·generic PREOPEN selector는 2026-09-19부터 퇴역했다. 재평가가 승인된 경우에도 해당 CLI를 복구하거나 호출하지 않고, entry/scale-in/compact/WS/machine/low-price 등 family 소유 evaluator와 dated publisher만 제한 실행한다. `runtime_policy_bootstrap`은 검증된 incumbent·operator lock·명시 OFF와 family receipt 해시를 합성할 뿐 EV 후보를 만들지 않는다. 동일 정책/비대상 체결/미성숙/결손을 개선 검증으로 집계하지 않으며, 다음 trading date의 baseline 보존은 신규 challenger 개선이나 실제 PID 소비가 아니다. 개별 family closure는 전체 native DONE을 대신하지 않는다.


### Pipeline event verbosity 운영 진단 인계

`pipeline_event_verbosity_report`는 retained raw와 producer summary의 exact-date count/stage/blocker/전체 payload·partition hash 및 완료 watermark를 검증하는 운영 진단이다. raw suppression·threshold/provider/order/bot 권한과 매매 EV를 만들지 않는다. unchanged managed append/archive source는 integrity-bound terminal을 재사용하고 append는 last-good offset 이후 완전한 행만 처리한다. 원천 owner가 없는 mutable 입력은 streaming 계산이며 zero-read acceptance 대상이 아니다. 과거 volume checkpoint가 없으면 자동 lookback/full raw backfill을 하지 않고 `bootstrap_required`와 동일 native owner의 scoped source-day closure를 남긴다.

DONE flag가 없어도 생성된 exact-date 진단은 소비하며 명시적False만 OFF다. 진단/선언 둘 다 없으면 not_declared로 표시하고 OFF·PASS로 바꾸지 않는다. 중첩 policy/parity·producer rollup의 schema 손상은 reusable PASS나 정상 상태로 수용하지 않는다. cache miss 후 지원된 checkpoint 계산을 재사용하거나 구체 invalid/owner를 반환하고 strict는 operations OPEN을 보존한다. raw/summary 본문 전수 복구나 provider recovery를 자동 실행하지 않는다.

해당 단계의 resource wait timeout은 `resource_deferred`·null parity·원 source generation으로 기록하며 독립 후행 계산은 각자의 기존 global guard를 계속 적용한다. EV→workorder→tower/checklist→strict verifier/controller가 동일 `order_pipeline_event_compaction_v2_shadow` OPEN을 보존한다. missing/deferred/parity failure는 신규 매매 후보0/no-edge나 full-chain DONE/PREOPEN GREEN으로 바꾸지 않는다. unchanged gap 하나 때문에 provider/full-wrapper를 반복 recovery하지 않는다. BUY Funnel의 optional native summary 실패는 raw fallback이며 entry-split의 mandatory execution census 검사는 그대로 유지한다. 자연 유입·다음 완료창 parity 및 실제 consumer 비용은 구현 회귀와 별도다. [지원 범위·owning review](audit-reports/2026-09-18-pipeline-event-verbosity-incremental-review.md)를 따른다.
