# 2026-10-02 Stage2 To-Do Checklist

## 오늘 목적

- 전일 family별 원천·경제성·정책·런타임 직접 소비 결과와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- 공통 Daily/EV 튜닝 및 generic workorder는 퇴역 상태를 유지하고 family owner의 직접 근거만 사용한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- 이번 기계·보조판정 계획의 학습·승계에는 사용자 지정 9/29 이후 적격 원천과 same-day 예외를 우선 적용한다. 일반 clean-baseline 하한을 근거로 6~8월이나 9/28 이전 자료를 다시 포함하지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:3ecdbc530a2a13eefe3a65c4feafd2f87444ca639fc4b5e97cbd9098f970dc71 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-30; 발행 2026-10-01; 적용 2026-10-02. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `8e7ec7785b1d589ac434bed628ea034462c52120d855389dce5b033968fa72e2`; 정책 bundle `59578675dd705ac9f955d8333e9bd858d63d6cbc9fb0375c9fed1a597fe653c8`; consumer `04fd01bcd9b5896aa02366970edab84a387eee504ddad68dd55e451738809eb8`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->

## Main 기계판정 미진입 회복 우선순위

- [x] `[ErrorDetectorDaemonLogDedup1002] 동일 장후 실패의 daemon 반복 ERROR 기록 수리` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 08:20~09:30`, `Track: RuntimeStability`)
  - Source: [daemon 반복 경보 수리](../audits/error-detector-daemon-incident-dedup-review-2026-10-02.md), [운영 출력 계약](../time-based-operations-runbook.md).
  - Acceptance: bot/standalone 매 주기 health FAIL·검사/heartbeat 유지, 동일 사고 로그·ADMIN 알림 1회, 새 원천/사유/심각도·실제 PASS/재발·날짜 전환·handler 실패 회귀를 검증한다. 기존 사용자 배포/재기동 승인 아래 정책 실행값·원천 FAIL·독립 owner를 보존하고 원래 준비/PREOPEN 보존·별도 당일 인계·guarded restart/PID 소비를 각각 대사한다. 검증된 당일 인계 또는 정확일자 launcher gate 미충족이면 현재 PID를 중단하지 않는다.
  - 구현 수용: `24bf9ab6` 불변 root 76 PASS/4.64초, source clean. 당일 새 prepare가 `preopen_target_not_next_operating_day`로 차단돼 selector `9dcbd482` 복구, 기존 PID/정책 env/manifest/PREOPEN/준비본 불변과 08:12 PID verify PASS 확인. 08:12 당시 daemon 소비는 pending이었고 원 finalization FAIL을 유지했다.
  - 사용자 후속 승인·종결: 장중 교체 불가라는 해석을 철회하고 원래 PREOPEN/정책 bytes를 보존하는 별도 당일 코드 인계를 구현했다. `1ac3fc80` 불변 root 434 PASS/17.27초, 기존 PID와 보존 prepared/당일 completion 검증 PASS 뒤 08:54 guarded restart 완료. PID 2764995/native env PASS·mismatch 0·별도 소비 영수증 확인. 정책/PREOPEN/준비본 5파일·독립 설정 407개·cron 불변. 08:54:26 최초 ERROR 1회 뒤 08:55:28/08:56:30 health tick 반복 출력 없음; 원 finalization FAIL 보존. [통합 리뷰·배포](../audits/intraday-exact-route-policy-preserving-handoff-review-2026-10-02.md).

- [ ] `[ExactProbeIntradayRouteLeaseRepair1002] 기존 AL 보존과 누락 NX 관측 item 추가` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 08:20~09:30`, `Track: MainEntry`)
  - Source: [당일 인계·정확 경로 수리 리뷰](../audits/intraday-exact-route-policy-preserving-handoff-review-2026-10-02.md), [운영 원천 계약](../time-based-operations-runbook.md#intraday-exact-route-observation-augmentation).
  - Acceptance: 공식 upstream SHA/경로/시간, refresh=1·0B/0D·기존 item cap, AL와 매매 view 보존, same epoch의 새 정확 수신만 평가, borrowed/adopted/reconnect/지연 및 불확실 send·정확 item cleanup 회귀를 검증한다. 과거 실패는 유지하고 새 attempt 원천/기계 결과를 따로 남긴다. 위 daemon owner와 한 불변 root로 인계·배포하되 Widget/Episode pin/정책/예약·hard safety·주문 권한은 유지한다. 자연 해당 route 표본 없으면 not_observed로 남긴다.
  - 구현·배포 수용: `1ac3fc80`/PID 2764995와 위 당일 인계·434 회귀 PASS 확인. 08:56 실제 WS epoch 1·27 item/cap 56·010140_AL 보존·정상 수신. 재기동 후 새 zero-base attempt가 없어 NX 추가→새 정확 0B/0D→기계판정→개별 cleanup 자연 수용은 `not_observed`; 과거 결손은 보존한다.

- [x] `[CronFinalizationDependencyRepair1002] 아침 최종화 실패와 cleanup 미실행 원인 분리` (`Due: 2026-10-02`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:30`, `Track: RuntimeStability`)
  - Source: [아침 경보 원인·수리](../audits/morning-finalization-dependency-alert-review-2026-10-02.md), [운영 복구 계약](../time-based-operations-runbook.md).
  - Acceptance: exact-source 최신 pre-cleanup FAIL에서만 cleanup을 `blocked_by_finalization`으로 분리하고 실제 parent FAIL·이미 실행한 cleanup FAIL을 유지한다. 다른 날짜/owner·recovery START·세대 변경 반례, 표적 회귀·compile/diff·parser와 선택 릴리스의 실제 순수 감시 결과를 검증한다. 배포 후 승인된 9/30 기반 10/2 prepared를 정식 재생성·전체 verify하며 정책/독립 서비스 pin/예약을 보존한다.
  - 10/1 장후 계산은 raw/archive 결손과 scale-in source block으로 미종결이다. 성공 마커 합성·Main wrapper 재실행·정책 재계산·API/실주문 호출 없이 보존하며, 기동/새 장후 자연 수용은 기존 각 owner가 맡는다.
  - 완료 근거: `9dcbd482` 불변 릴리스 표적 84 PASS. 삭제돼 검증에 필요했던 historical release 3개를 원 archive Git SHA와 동일한 경로로 복원하고 정책/닫힌 controller·summary는 보존했다. 정식 10/2 prepared 재생성·전체 verify PASS, env/정책 불변, cron 8개·release-set/122 Episode/366 pin 검증 PASS. 07:15 자연 full detector의 artifact PASS·새 code 소비와 cleanup `blocked_by_finalization`, 원 finalization FAIL 보존을 확인했다. 매매 서비스 재기동은 없다.

- [x] `[PostcloseSemanticMonitorContractRepair1002] 새 장후 계약의 의미감시·알림 호환성 보완` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:00~19:50`, `Track: RuntimeStability`)
  - Source: [10/1 의미감시 연계 보완계획](../proposals/semantic-monitor-postclose-integration-repair-plan-2026-10-01.md), [구현·배포 기록](../audits/semantic-monitor-postclose-integration-implementation-2026-10-01.md). 사용자 후속 승인은 감시기 구현·배포와 내일 기동 준비까지이며 오늘 Main 선행 기동·매매 권한 변경은 포함하지 않는다.
  - Acceptance: P0~P3의 버전·same-day split/purge·기계 v7/보조 v4 선정·full-cost 분모·현재 stage generation·준비/소비 구분·조치 warning mock 알림과 중복/recovery 계약을 리뷰·보완·재리뷰한다. 기존 owner 함수를 재사용하고 표적 회귀·compile/diff, wrapper 변경 시 bash/계약 시험, 실제 감시 root/selector 및 bounded 성능을 확인한다. 코드 완료와 선택 릴리스·자연 소비·정책 성과를 분리한다. 자연 장후 수용은 아래 기존 기계/보조 Postclose owner가 맡으며, 기동은 `FinalPolicyStartupAcceptance1002`를 유지한다.
  - 코드 수용: 10/1~10/2 구현·반복 리뷰 및 최종 표적 회귀 602 PASS(기존 자금/holding·별도 bootstrap 11개 분리), 초기 추가 bootstrap/wrapper 127 PASS. 실제 실행 report의 selector/root/hash 소비와 당일/누적·purge 전후 분모 분리, 세대 교체 중 unobservable·자정 후 장전 준비·동일 정책의 봉인 승계 검증 경계를 확인했다. 배포와 정식 10/2 준비 결과는 위 감사 기록·selector 및 준비본이 소유한다. 미래 자연 기동·v7/v4 생성 수용은 기존 OPEN owner에 남긴다.

- [ ] `[FinalPolicyStartupAcceptance1002] 최종 재생성 정책의 Main·Episode·Widget 당일 소비 확인` (`Due: 2026-10-02`, `Slot: PREOPEN`, `TimeWindow: 07:32~09:10`, `Track: RuntimeStability`)
  - Source: [10/1 기동 준비·동일 정책 승계 리뷰](../audits/next-startup-final-policy-readiness-2026-10-01.md), [준비본](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json), [Episode 승계·로더 검증](../../data/runtime/startup_readiness/2026-10-02/policy_validation.json).
  - 준비 근거: Main 선택 릴리스 `459d718f`의 준비본 검증 pass. Episode 61개 실행값/정책 hash 불변으로 미래일 applied 발행, 58 ready·기존 격리 3 유지. Widget 10/2 로더 3종목·4session 유효, 실행값 불변. Episode timer 122개 10/2 예약 확인. 코드/릴리스/cron/systemd 변경과 현재 Main 기동은 없다.
  - 통합 배포 후속: [10/1 통합 릴리스·다음 기동 인계](../audits/integrated-release-next-startup-handoff-2026-10-01.md)에 따라 새 선택 릴리스와 서비스 pin, 재생성한 10/2 준비본, 현재 active Widget/collector 소비를 검증한다. 위 `459d718f`는 배포 이전 준비 근거이며 최종 릴리스는 deployment receipt를 따른다. 당일 Main/Episode 자연 기동 수용은 OPEN을 유지한다.
  - 배포 종결 근거: `0a8fa0a0` 불변 릴리스 733 PASS; 공통 selector·13 service/template pin 전환, Episode instance 122개·policy pin 366개 및 cron 8개 검증 통과. Widget/collector/notifier 5개 실제 PID cwd 일치, Widget 기동 필드 검증 pass. 같은 릴리스의 10/2 prepared 재생성·verify pass. Main은 오늘 기동하지 않았다. 당일 자연 수용을 완료로 표시하지 않는다.
  - 감시 배포 후속: [최종 의미감시 배포](../audits/semantic-monitor-postclose-integration-implementation-2026-10-01.md)의 `c6453530` selector·10/2 정식 prepared/전체 verify PASS, 표적 602 PASS와 실제 감시 code 소비를 확인했다. Main/매매 코드는 `0a8fa0a0`와 같고 독립 서비스 pin/PID·정책·예약은 유지한다. 자정 이후에도 10/2 기동 대상을 유지했으며 Main은 07:55 예약 전에 시작하지 않았다. 아래 실제 PREOPEN/PID/당일 소비 수용은 OPEN이다.
  - 07시 경보 후속: [원인 분리·배포](../audits/morning-finalization-dependency-alert-review-2026-10-02.md)의 `9dcbd482`가 최신 selector다. 바뀐 runtime 코드는 cron 감시기뿐이고 정식 10/2 prepared·전체 verify PASS, 동일 env·주정책·독립 owner pin을 확인했다. 초기 준비 실패는 삭제된 historical release 3개 복원으로 해소했으며 과거 stage/hash를 덮지 않았다. 현재 예정 07:35 PREOPEN/07:55 Main print-plan은 이 최신 릴리스를 소비한다.
  - Acceptance: 07:32 exact-date custody, 07:35 PREOPEN succeeded·선택 릴리스, 07:55 Main 실제 PID cwd/commit/bootstrap 소비, Widget 날짜 전환 정책 소비, 최초 Episode 당일 preflight·서비스 정책 hash를 확인한다. 이후 profile은 자신의 예약 시각에 같은 당일 영수증으로 확인한다. 준비 PASS만으로 PID/체결/순이익을 완료 처리하지 않는다. 10/1 원천 결손의 05시 finalization 실패를 9/30 기반 10/2 준비 실패로 혼동하거나 성공으로 덮지 않는다. 정당한 custody/broker/quote safety 차단과 장애를 구분하고 실제 결손이 있으면 artifact·첫 실패 단계·수리 범위·재검증을 기록한다.

- [ ] `[EntryDecisionSourcePreopen1002] 기계·보조 원천 기록과 현행 정책 장전 결속 확인` (`Due: 2026-10-02`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:30`, `Track: MainEntry`)
  - Source: [두 계획의 공통 계약](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md), [보조 원천 보완](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 전일 `DirectFamilySourceRepairCompactAuxiliary`는 기록 생산자 구현 소유자이며 이 항목은 장전 소비 확인만 소유한다.
  - Acceptance: 첫 판정 전 선택 릴리스·기록 producer 버전·정확일자 정책 hash를 대조한다. source-only 기록 때문에 기계/AI 판정·제출·수량·provider가 달라지지 않는 표적 시험 영수증과 실패 시 기존 경로를 확인한다. 장중 자연 원천은 이후 정확 attempt로 따로 확인하고 과거 결손을 복원했다고 주장하지 않는다.
- [ ] `[MainMachineMissedEntryLogicReady1002] 미진입 상승 회복 우선 로직·샘플 검증 완료` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:20`, `Track: MainEntry`)
  - Implementation evidence (10/1): [작업본 구현·리뷰·샘플 검증](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md). 코드 수용과 실제 10/2 릴리스 소비·전체 자연 원천 수용을 구분하며 이 항목은 OPEN을 유지한다.
  - Source: [10/2 장후 적용 계획](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md). 현재 장중 선정 정책·PID를 건드리지 않고, 새 버전의 리뷰·수정·재검토·샘플 재생·wall/CPU/RSS 비교를 격리된 작업 경로에서 완료한다.
  - Acceptance: 86+6+4 슬롯에서 single 회복이 없는 결합 blocker fixture, 고유 기회 중복/성공·실패 집합 겹침, train seed의 holdout 불변, 같은 날 시간순 분할·관측기간 purge, 발행 readback·부모 CAS를 검증한다. 동일 입력 3회 wall/CPU 중앙값 ≤구버전×1.20, RSS ≤구버전×1.10+64MiB와 기존 절대 가드를 통과한다. 불합격이면 기존 장후 경로·정책을 유지한다.
- [ ] `[MainMachineMissedEntryPriority1002] 미진입 상승 회복 우선 순위 장후 적용` (`Due: 2026-10-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~23:50`, `Track: MainEntry`)
  - Semantic acceptance: [의미감시 연계 계획](../proposals/semantic-monitor-postclose-integration-repair-plan-2026-10-01.md)에 따라 실제 감시 코드·원천일·generation을 대사하고 winrate stage와 full v7 scope의 정상 carry/원천 실패·발행 결과를 각각 확인한다. 감시 보완 미반영은 별도 미수용으로 남기며 생산자의 기존 source/발행/strict 안전 계약을 우회하지 않는다.
  - Source: [10/2 장후 적용 계획](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md). 위 로직·샘플 검증을 통과한 릴리스의 장후 생산자만 새 버전을 소비한다. 10/2 장중 선정 정책과 PID 판정은 유지한다.
  - Acceptance: 실제 세션/예약 stage 경계를 확인한다. 10/2의 사전 봉인된 검증 구간에서 후보 1개만 판정하고 미진입 회복 고유 기회 ≥3, 회복 성공 양수, 기존 성공 보존·전체 모집단·비용·부모/범위·발행 조건을 대조한다. M1/A1 합성은 같은 부모·입력 근거 없이 발행하지 않는다. 성공/실패/유효 carry, summary·strict·controller·finalization 세대를 확인하며 부족하면 원인과 기존 정책 승계를 남긴다. 적용일은 거래일 캘린더로 산출한다.

- [x] `[CandleRequestRouteBindingRepair1002] Main 캔들 요청과 정확 WS 경로 결속 수리` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:30~15:20`, `Track: MainEntry`)
  - Source: [캔들 요청 경로 결속 수리](../audits/candle-request-route-binding-repair-2026-10-02.md). 사용자 구현·반복 리뷰·배포·재기동 승인을 따른다.
  - Acceptance: 요청 코드/연결 epoch를 REST 전에 고정하고 scanner venue·정확 0B/0D 경로·receive clock을 대사한다. 양방향 aggregate 전환, missing/stale/future·다른 종목/경로·bool/split/reconnect epoch·metadata 충돌, probe 등록 필터와 neutral holding 보존 회귀를 통과한다. 기존 정책/PREOPEN/준비본·독립 서비스 pin을 보존한 불변 배포와 guarded Main restart/PID 소비를 검증한다. 새 자연 원천만 인정하고 과거 결손·주문 없음·경제성 미검증을 보존한다.
  - 종결 근거: 반복 리뷰·보완 후 작업본 522 PASS/9.10초, 불변 `2f67e36c` 522 PASS/14.72초; 구 릴리스에서도 재현된 historical rebound PREOPEN 3개만 분리. 로컬 결속 중앙값 0.01149ms/건. 당일 봉인 정책/인계 검증 뒤 09:56:42 guarded restart·PID 2792150/native env PASS·불일치 0·single Main 확인. 정책/PREOPEN/준비본 5파일·독립 service pin 416개·cron 불변. 005930/000660의 새 Main 원천에서 요청/공급 코드·정확 AL epoch 1 결속과 fresh_consistent·정상 RECHECK를 확인했다. 일반 current-full-contract의 과거 summary 세대 실패는 보존하며, 원 086520 결손 복구·수익 개선을 주장하지 않는다.

## 보조 AI PASS/VETO 원천·선택 보완

- [x] `[SharedCandleCustodyRepair1002] 공용 분봉 캐시의 혼합 사용자 소유권 보완·배포` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 16:17~17:00`, `Track: RuntimeStability`)
  - Source: [분봉 캐시 소유권 수리](../audits/shared-candle-cache-custody-repair-2026-10-02.md). 사용자 보완·반복 리뷰·배포·재기동 승인.
  - Acceptance: directory UID/GID·0600·기존 lock inode와 원 receive-clock 보존, 권한 실패의 정상 admission/원자 발행 미수행·FD/temp cleanup·symlink 차단, 실제 root producer→ubuntu consumer 단일 합성 fetch를 검증한다. 정책/독립 pin/cron 보존과 immutable gate·guarded restart·exact-date PID 소비 뒤 기존 슬롯만 소유권 복구하고 다음 정기 report를 확인한다. 실물 동일 요청 join·budget 감소율·경제성은 자연 분모가 없으면 not_observed로 남긴다.
  - 코드 수용: 144+95=239 PASS, compile/diff PASS, 실제 혼합 UID fixture의 원 lock inode/0600/수신시각과 consumer 추가 fetch 0 확인. 배포·현재 자연 소비는 아래 감사 기록에서 별도로 종결한다.
  - 1차 소비·보완: aa6b0123/PID 2901939 bootstrap·consumed PASS, 정책 5파일/pin 416개/cron 불변. 368 슬롯 중 365 소유권 복구·새 PID cache writes ubuntu/0600, 16:30 정기 report DONE 확인. Ubuntu cron이 root PID의 EPERM을 종료로 오판한 consumer 결함을 추가 수리(원천 heartbeat/thread guard 유지), process-health 88 PASS; 이 보완을 포함한 최종 배포는 아래 감사 기록에서 확인한다.
  - 최종 종결: b096f7ca 불변 root 327 PASS/13.67s, guarded restart/PID 2904478/start ticks 54744253/당일 bootstrap·native consumed PASS. 정책 5파일/pin 416개/cron 보존, Ubuntu 직접 process health PASS, 16:40 정기 detector process/freshness PASS·sentinel/monitor 16:40:28 DONE. 캐시/lock 전부 ubuntu/0600, WS PID/commit 연결 확인. Monitor의 no_identified_machine_evaluation과 전일 postclose FAIL은 보존하며 자연 join·전체 감소율·경제성은 미확인으로 남긴다. 소유권/감시 결함 수리와 승인된 배포 수용을 종결한다.

- [x] `[SharedReadSelectorCustodyRepair1002] 배포 후 ubuntu cron의 릴리스 선택 파일 접근 복구` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 14:53~15:10`, `Track: RuntimeStability`)
  - Source: [선택 파일 소유권 사고·수리](../audits/shared-read-contention-repair-2026-10-02.md#selector-custody-incident-and-repair). 사용자 오류 복구 지시와 기존 보완·배포 승인.
  - Acceptance: root publication/PID 기록 후 원 selector UID/GID·0600과 정책/릴리스 보존, 이전 bytes 보존·임시파일 cleanup 회귀, ubuntu 직접 router 소비와 다음 자연 cron/monitor/daemon freshness 복구를 확인한다. mtime 합성·알림 억제·freshness 완화로 종결하지 않는다.
  - 종결: 파일만 ubuntu 소유권 복구(내용 SHA 불변); canonical PID writer와 local publisher/rollback custody 보완. 95 PASS·compile/diff PASS, 실제 root PID 영수증 기록 후 ubuntu 읽기 PASS. 15:00 자연 sentinel/monitor DONE, 15:01:33 artifact_freshness/process_health PASS·recovered 로그. PID 2877334/매매 릴리스·정책 유지, 추가 재기동 없음. 전일 postclose terminal FAIL은 별도 보존한다.

- [x] `[SharedReadContentionRepair1002] 공용 읽기 예산 경쟁·불필요한 probe 조회 보완` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 12:34~15:20`, `Track: MainEntry`)
  - Source: [원천 읽기 경쟁 보완](../audits/shared-read-contention-repair-2026-10-02.md). 사용자 구현·반복 리뷰·배포·기동 승인.
  - Acceptance: 분봉 결손 후 틱 미조회, 실제 feature owner의 정확 WS 선택/변경 시 gap, source-only FIFO/timeout cleanup/required slot 보호, 동일 분봉의 프로세스 간 원 receive-clock·TTL·실물 요청 수·권한 격리 회귀를 통과한다. 기존 동시 probe·발견 범위·한도·정책을 보존하고 guarded restart·정확일자 PID·WS 소비를 확인한다. 새 원천 영수증/판정과 비교 가능한 admission 감소는 별도 자연 수용으로 남기며, 표본 부재는 not_observed이고 과거 결손은 유지한다.
  - 진행 근거: source/cache/feature/queue/monitor 320 PASS, native machine 3 PASS. 103590 원천·정책·주문 권한 소급 없음.
  - 종결 근거: 최종 작업본·불변 `8d055923` 각각 722 PASS. 첫 restart는 기존 PID 종료 후 tmux 부재로 중단했으며, singleton 부재 확인 후 승인된 native supervisor를 복구했다. 14:35:24 PID 2877334 exact-date 소비/PID bootstrap·sealed generation PASS. 정책 5파일·독립 pin 416개·cron 불변. 새 PID WS 정상, 정확 WS 재사용→기계판정 captured 13건 확인(BLOCK/ENTER_NOW, 원 bundle 유지). 짧은 관측에서 새 PID admission 보류 0이나 비교 분모 부족으로 전체 감소율·경제성 개선 미주장. Live cross-process join은 not_observed, 독립 프로세스 fixture 수용 PASS. 코드·배포·직접 소비 수용을 종결하며 과거 103590 결손과 별도 historical postclose 실패는 유지한다.

- [ ] `[MainEntryEconomicLineageRepair1002] 계좌 여력 원천 준비와 후단 guard·residual 결속 수리` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 11:20~15:20`, `Track: MainEntry`)
  - Source: [108490 원천·후단 결속 보완 근거](../audits/main-entry-economic-source-lineage-repair-2026-10-02.md). 사용자 보완·반복 리뷰·배포·재기동 승인을 따른다.
  - Acceptance: 기존 source-only 한도 내 최종 가격 준비·동일 종목 오래된 queue 병합, 정확 계좌/가격/재고/freshness, guard와 bundle 귀속 residual 영수증·JSON 결속을 검증한다. 새 guard 두 단계의 forward 캐시 전환은 기존 raw prefix를 재로딩하거나 과거 복구를 주장하지 않는다. 기존 정책 5파일·독립 service pin·cron을 보존하고 guarded restart·정확일자 PID 소비를 확인한다. 새 자연 경제성/guard·residual 원천은 exact identity로 별도 수용하며 없으면 not_observed로 남긴다.
  - 진행 근거: 생산자·캐시·소비자 448 PASS/24.83초, 후단 guard·residual 23 PASS/2.99초, startup/router/handoff/warmup 148 PASS/3.39초. 정상 계좌 조회가 뒤에 왔어도 10:58 원 pre-AI 결손은 유지한다. 정책·guard·주문 권한 변경 없음.
  - 배포·기동 근거: 불변 `a6014346`에서 동일 619 PASS 재검증 후 11:56:46 guarded Main restart·PID 2831000/정확일자 consumed PASS. 정책 5파일·독립 service pin 416개·cron 불변, single Main·새 PID WS 연결/원천 정상. 12:00 정기 sentinel/monitor 완료, lossless cache 16→18 forward 전환·rebuilt=false·decode 오류 0·과거 신규 guard 구간 미복원 명시. 새 005930 RECHECK 3건은 nonentry capacity gap을 보존한다. 남은 수용: 새 ENTER_NOW 정확 계좌 여력과 guard·bundle residual 영수증의 exact identity/freshness 자연 검증은 not_observed이며 해당 영수증 발생 시 대사한다. 과거 108490 복구·주문·경제성 개선이나 별도 historical postclose 종결을 주장하지 않는다.

- [x] `[MainAiPeriodicWarmup1002] Main AI 주기 호출과 연결 재사용 적용` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 10:30~15:20`, `Track: MainEntry`)
  - Source: [주기 비교·운영·리뷰 근거](../audits/main-ai-periodic-warmup-2026-10-02.md). 사용자의 주기 호출 요청과 최적 주기 점검을 따른다. 기존 구현·반복 리뷰·배포·재기동 승인을 적용하며 기존 정책과 독립 소비자 pin을 보존한다.
  - Acceptance: 120/180/240초 비매매 비교와 300초 연결 유지의 직접 영수증, 키별 240초 초기값·최대 15회/시간, 실제 호출 우선·유휴/disabled/test/date 차단·late queue 경계·실패/캐시 불변을 검증한다. 불변 릴리스와 guarded Main handoff 후 새 PID의 키별 워밍업 영수증을 확인한다. 진단 호출은 AI 판정/원천/장후 학습 분모에 포함하지 않는다. 실제 판정 응답 회복과 통계적 최적 주기는 별도 관측이며 작은 진단 표본으로 종결했다고 주장하지 않는다.
  - 종결 근거: 작업본 410 PASS/5.28초, 불변 c124f476 410 PASS/9.15초. 10:49:58 guarded restart/PID 2809235·정확 정책 인계 PASS, 정책/PREOPEN/준비본 5파일·독립 pin 416개·cron·single Main 불변. 키별 최초 및 두 번째 주기의 자연 진단 4건 모두 정상; 간격 244.146/242.929초, 두 번째 응답 1.079/0.930초. 기존 실제 판정 분모와 실패 상태는 보존하며 실제 판정 응답 회복은 미관측이다.
  - 추가 리뷰 재개 (11:06): 지연 SDK 초기화의 5초 외 대기, 종료 오류의 Main cleanup 전파, 시작/종료·중복 tick 경합, 실패 startup 잔류를 수정했다. 422 PASS/5.82초. 재종결: 불변 09a6a2df 422 PASS/9.09초, 11:07:56 guarded restart/PID 2815486·native env/정책 소비 PASS. 정책 5파일·독립 pin 416개·cron·single Main 보존. 새 PID 키 0/1 진단 2.020/2.433초 정상, WS 연결·writer loss 0 확인. 새 PID 두 번째 주기는 미관측이며 전 릴리스의 반복 주기 근거와 분리한다. 10:58 108490 실제 판정은 2.718초에 성공했으며 단일 사례의 인과·경제성은 주장하지 않는다.

- [ ] `[CompactAuxiliaryPassVetoLogicReady1002] 보조 AI 원천·판정 후보 로직과 샘플 성능 검증` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:20`, `Track: MainEntry`)
  - Implementation evidence (10/1): [작업본 구현·리뷰·샘플 검증](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md). 코드 수용과 실제 10/2 릴리스 소비·전체 자연 원천 수용을 구분하며 이 항목은 OPEN을 유지한다.
  - Source: [보조 AI 장후 보완 계획](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 장중 현행 프롬프트·정책·PID를 유지한다. 전일의 `DirectFamilySourceRepairCompactAuxiliary` 기록 전용 생산자 수리가 장전 선택 릴리스에 포함됐는지 확인한다. 장후 후보·발행 계산은 격리된 작업본에서 원천 생산자→라벨→선택→발행기·기존 번들 readback까지 리뷰·수정·재리뷰한다.
  - Acceptance: 0/6 주 비교 결손·10개 진단 PASS·23 trial 중 미응답 8개를 재현한다. risk/opportunity 변형의 생산·완료·재생 목록 일치, 학습 1위 holdout 실패/2위 통과여도 carry, 같은 날 독립 split, CAUTION 후 재진입, VETO 없는 PASS-only 평가, 비용 종류/plan hash 충돌, 중복 예약·응답 소실 회귀를 통과한다. 5일 초과 누적 projection fixture에서 초기 날짜 보존·검증일 격리·raw 전체 재로딩 방지를 확인한다. 동일 입력 3회 wall/CPU ≤구버전×1.20, RSS ≤구버전×1.10+64MiB와 원래 provider 예산을 지킨다. source 수리·독립 CF·owner 경제성을 구분하고 마찰비용 진단을 full-cost 정책 근거로 발행하지 않는다.
- [ ] `[CompactAuxiliaryPassVetoPostclose1002] 보조 AI 새 로직의 10/2 장후 실행·승계 확인` (`Due: 2026-10-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~23:50`, `Track: MainEntry`)
  - Semantic acceptance: [의미감시 연계 계획](../proposals/semantic-monitor-postclose-integration-repair-plan-2026-10-01.md)의 same-day/full-cost/동결 선택·정확 응답·분모·report-terminal 결속과 조치 알림을 같은 자연 generation에서 확인한다. 후보 미발생은 `not_observed`, 필수 원천·실행 결손은 owner/artifact/closure test와 함께 `blocked`로 남기며 과거 결손을 복구로 표시하지 않는다.
  - Source: [보조 AI 장후 보완 계획](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 위 검증을 통과한 선택 릴리스의 장후 생산자에만 새 로직을 적용한다.
  - Acceptance: 실제 세션/예약 stage 경계와 10/2 exact source, 비용 유형별 적격성, PASS/VETO/CAUTION 전이, 동결 후보 하나의 검증 및 기계 부모 결속을 대조한다. 해당 후보가 바꾸는 방향의 지원·비용·후보 응답·독립 검증이 부족하면 그 scope를 carry하고 연구·진단은 별도 완료 처리한다. 정책·summary·strict·controller·finalization 종결을 확인하며 다음 거래일 PID와 실현 순이익은 별도 확인한다.
