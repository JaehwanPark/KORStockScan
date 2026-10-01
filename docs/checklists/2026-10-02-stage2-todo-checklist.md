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

- [ ] `[FinalPolicyStartupAcceptance1002] 최종 재생성 정책의 Main·Episode·Widget 당일 소비 확인` (`Due: 2026-10-02`, `Slot: PREOPEN`, `TimeWindow: 07:32~09:10`, `Track: RuntimeStability`)
  - Source: [10/1 기동 준비·동일 정책 승계 리뷰](../audits/next-startup-final-policy-readiness-2026-10-01.md), [준비본](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json), [Episode 승계·로더 검증](../../data/runtime/startup_readiness/2026-10-02/policy_validation.json).
  - 준비 근거: Main 선택 릴리스 `459d718f`의 준비본 검증 pass. Episode 61개 실행값/정책 hash 불변으로 미래일 applied 발행, 58 ready·기존 격리 3 유지. Widget 10/2 로더 3종목·4session 유효, 실행값 불변. Episode timer 122개 10/2 예약 확인. 코드/릴리스/cron/systemd 변경과 현재 Main 기동은 없다.
  - 통합 배포 후속: [10/1 통합 릴리스·다음 기동 인계](../audits/integrated-release-next-startup-handoff-2026-10-01.md)에 따라 새 선택 릴리스와 서비스 pin, 재생성한 10/2 준비본, 현재 active Widget/collector 소비를 검증한다. 위 `459d718f`는 배포 이전 준비 근거이며 최종 릴리스는 deployment receipt를 따른다. 당일 Main/Episode 자연 기동 수용은 OPEN을 유지한다.
  - 배포 종결 근거: `0a8fa0a0` 불변 릴리스 733 PASS; 공통 selector·13 service/template pin 전환, Episode instance 122개·policy pin 366개 및 cron 8개 검증 통과. Widget/collector/notifier 5개 실제 PID cwd 일치, Widget 기동 필드 검증 pass. 같은 릴리스의 10/2 prepared 재생성·verify pass. Main은 오늘 기동하지 않았다. 당일 자연 수용을 완료로 표시하지 않는다.
  - Acceptance: 07:32 exact-date custody, 07:35 PREOPEN succeeded·선택 릴리스, 07:55 Main 실제 PID cwd/commit/bootstrap 소비, Widget 날짜 전환 정책 소비, 최초 Episode 당일 preflight·서비스 정책 hash를 확인한다. 이후 profile은 자신의 예약 시각에 같은 당일 영수증으로 확인한다. 준비 PASS만으로 PID/체결/순이익을 완료 처리하지 않는다. 10/1 원천 결손의 05시 finalization 실패를 9/30 기반 10/2 준비 실패로 혼동하거나 성공으로 덮지 않는다. 정당한 custody/broker/quote safety 차단과 장애를 구분하고 실제 결손이 있으면 artifact·첫 실패 단계·수리 범위·재검증을 기록한다.

- [ ] `[EntryDecisionSourcePreopen1002] 기계·보조 원천 기록과 현행 정책 장전 결속 확인` (`Due: 2026-10-02`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:30`, `Track: MainEntry`)
  - Source: [두 계획의 공통 계약](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md), [보조 원천 보완](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 전일 `DirectFamilySourceRepairCompactAuxiliary`는 기록 생산자 구현 소유자이며 이 항목은 장전 소비 확인만 소유한다.
  - Acceptance: 첫 판정 전 선택 릴리스·기록 producer 버전·정확일자 정책 hash를 대조한다. source-only 기록 때문에 기계/AI 판정·제출·수량·provider가 달라지지 않는 표적 시험 영수증과 실패 시 기존 경로를 확인한다. 장중 자연 원천은 이후 정확 attempt로 따로 확인하고 과거 결손을 복원했다고 주장하지 않는다.
- [ ] `[MainMachineMissedEntryLogicReady1002] 미진입 상승 회복 우선 로직·샘플 검증 완료` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:20`, `Track: MainEntry`)
  - Implementation evidence (10/1): [작업본 구현·리뷰·샘플 검증](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md). 코드 수용과 실제 10/2 릴리스 소비·전체 자연 원천 수용을 구분하며 이 항목은 OPEN을 유지한다.
  - Source: [10/2 장후 적용 계획](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md). 현재 장중 선정 정책·PID를 건드리지 않고, 새 버전의 리뷰·수정·재검토·샘플 재생·wall/CPU/RSS 비교를 격리된 작업 경로에서 완료한다.
  - Acceptance: 86+6+4 슬롯에서 single 회복이 없는 결합 blocker fixture, 고유 기회 중복/성공·실패 집합 겹침, train seed의 holdout 불변, 같은 날 시간순 분할·관측기간 purge, 발행 readback·부모 CAS를 검증한다. 동일 입력 3회 wall/CPU 중앙값 ≤구버전×1.20, RSS ≤구버전×1.10+64MiB와 기존 절대 가드를 통과한다. 불합격이면 기존 장후 경로·정책을 유지한다.
- [ ] `[MainMachineMissedEntryPriority1002] 미진입 상승 회복 우선 순위 장후 적용` (`Due: 2026-10-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~23:50`, `Track: MainEntry`)
  - Source: [10/2 장후 적용 계획](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md). 위 로직·샘플 검증을 통과한 릴리스의 장후 생산자만 새 버전을 소비한다. 10/2 장중 선정 정책과 PID 판정은 유지한다.
  - Acceptance: 실제 세션/예약 stage 경계를 확인한다. 10/2의 사전 봉인된 검증 구간에서 후보 1개만 판정하고 미진입 회복 고유 기회 ≥3, 회복 성공 양수, 기존 성공 보존·전체 모집단·비용·부모/범위·발행 조건을 대조한다. M1/A1 합성은 같은 부모·입력 근거 없이 발행하지 않는다. 성공/실패/유효 carry, summary·strict·controller·finalization 세대를 확인하며 부족하면 원인과 기존 정책 승계를 남긴다. 적용일은 거래일 캘린더로 산출한다.

## 보조 AI PASS/VETO 원천·선택 보완

- [ ] `[CompactAuxiliaryPassVetoLogicReady1002] 보조 AI 원천·판정 후보 로직과 샘플 성능 검증` (`Due: 2026-10-02`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:20`, `Track: MainEntry`)
  - Implementation evidence (10/1): [작업본 구현·리뷰·샘플 검증](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md). 코드 수용과 실제 10/2 릴리스 소비·전체 자연 원천 수용을 구분하며 이 항목은 OPEN을 유지한다.
  - Source: [보조 AI 장후 보완 계획](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 장중 현행 프롬프트·정책·PID를 유지한다. 전일의 `DirectFamilySourceRepairCompactAuxiliary` 기록 전용 생산자 수리가 장전 선택 릴리스에 포함됐는지 확인한다. 장후 후보·발행 계산은 격리된 작업본에서 원천 생산자→라벨→선택→발행기·기존 번들 readback까지 리뷰·수정·재리뷰한다.
  - Acceptance: 0/6 주 비교 결손·10개 진단 PASS·23 trial 중 미응답 8개를 재현한다. risk/opportunity 변형의 생산·완료·재생 목록 일치, 학습 1위 holdout 실패/2위 통과여도 carry, 같은 날 독립 split, CAUTION 후 재진입, VETO 없는 PASS-only 평가, 비용 종류/plan hash 충돌, 중복 예약·응답 소실 회귀를 통과한다. 5일 초과 누적 projection fixture에서 초기 날짜 보존·검증일 격리·raw 전체 재로딩 방지를 확인한다. 동일 입력 3회 wall/CPU ≤구버전×1.20, RSS ≤구버전×1.10+64MiB와 원래 provider 예산을 지킨다. source 수리·독립 CF·owner 경제성을 구분하고 마찰비용 진단을 full-cost 정책 근거로 발행하지 않는다.
- [ ] `[CompactAuxiliaryPassVetoPostclose1002] 보조 AI 새 로직의 10/2 장후 실행·승계 확인` (`Due: 2026-10-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~23:50`, `Track: MainEntry`)
  - Source: [보조 AI 장후 보완 계획](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md). 위 검증을 통과한 선택 릴리스의 장후 생산자에만 새 로직을 적용한다.
  - Acceptance: 실제 세션/예약 stage 경계와 10/2 exact source, 비용 유형별 적격성, PASS/VETO/CAUTION 전이, 동결 후보 하나의 검증 및 기계 부모 결속을 대조한다. 해당 후보가 바꾸는 방향의 지원·비용·후보 응답·독립 검증이 부족하면 그 scope를 carry하고 연구·진단은 별도 완료 처리한다. 정책·summary·strict·controller·finalization 종결을 확인하며 다음 거래일 PID와 실현 순이익은 별도 확인한다.
