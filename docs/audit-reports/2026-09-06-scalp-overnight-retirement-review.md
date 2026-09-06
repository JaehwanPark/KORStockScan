# Scalping overnight 폐기·당일 종결 구현 최종 리뷰 (2026-09-06)

## 1. 최종 판정

- **구현 판정: PASS.** 실제 scalping이 overnight 보유를 하지 않는 운영 목적에 맞춰 `Scalp-sim overnight`와 `Overnight OpenAI recovery`의 scheduled/current-runtime 경로를 영구 폐기했다.
- **대체 경로 판정: PASS.** 별도 튜닝축이나 AI 청산 판단을 추가하지 않고, 기존 보유 루프와 공통 SELL custody 경계 안에 `scalp_same_session_terminal_exit`를 추가했다. KRX는 신규 BUY 15:10 종료·15:15 당일 종결, NXT와 sim은 신규 BUY 19:40 종료·19:45 당일 종결을 사용한다.
- **자동화 판정: PREOPEN handoff PASS, 자연 런타임 증거 대기.** 2026-09-07 PREOPEN manifest/env 검증은 `status=pass`, finding 0건이다. 런처는 exact-date env 뒤에 영구·날짜별 operator override를 순서대로 적용하므로 유효 신규 BUY 마감은 KRX 15:10/NXT 19:40이다. 코드의 broker pre-call hard cutoff도 동일 경계를 독립적으로 강제한다.
- **권한 판정: 안전 경계 유지.** terminal decision은 quote/account/order/receipt/venue, hard/protect/emergency stop, 기존 SELL pending-generation/CAS/journal 경계를 우회하지 않는다. 20:00까지 남은 상태는 성공으로 합성하거나 overnight로 넘기지 않고 reconciliation incident로 남긴다.
- **미해결 구현 finding: 0건.** 다만 2026-09-07 실제 PID가 정책을 소비하고 자연 포지션의 terminal decision→주문→exact receipt→post-sell 귀속을 닫았는지는 아직 미래 관측 항목이다. 표본 0건은 성공이나 결함으로 간주하지 않는다.

## 2. 목적·기대효과 정합성

| 항목 | 종전 문제 | 구현 후 계약 | 기대효과 판정 |
| --- | --- | --- | --- |
| Scalp-sim overnight | 당일매매 전략인데 별도 15:10 overnight 분류와 artifact를 유지 | scheduled producer/current report·EV·verifier 소비 폐기, archive/offline replay만 허용 | 중복 상태·허위 carry label과 장후 산출물 비용 제거 |
| Overnight OpenAI recovery | 미결 sim 상태를 장후 OpenAI로 보완 | postclose provider 호출 제거, 잔존 CLI/wrapper는 `retired` no-op | 불필요한 호출 비용과 AI 기반 사후 상태 합성 제거 |
| 당일 포지션 종결 | 마감 직전 신규 BUY와 unresolved 상태가 분리되어 있지 않음 | venue별 hard BUY cutoff 뒤 5분 terminal SELL 신호, 20:00 unresolved incident | 당일 종결 기회 확보와 실패 원인의 명시적 관측 |
| sim source quality | 과거·합성 상태가 현재 session feedback에 섞일 가능성 | current KST session·비합성 상태만 restore/persist/join | post-sell/EV 오염 방지 |

Clean-baseline scalp-sim overnight 자료 327건이 모두 `SELL_TODAY`, `HOLD_OVERNIGHT=0`이었던 점도 별도 overnight 판정축 유지의 실익이 없다는 결론과 일치한다. 이 수치는 폐기 결정의 보조 증거이며, 당일 종결 구현의 실거래 수익 개선을 입증하는 값으로 사용하지 않는다.

## 3. 구현 범위

1. `src.engine.lifecycle.retirement`
   - overnight report/family/stage/env namespace를 공통 retirement 계약에 등록했다.
   - `KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=false`, `KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED=false`를 PREOPEN 산출물에 강제한다.
2. runtime·order
   - main engine의 overnight gatekeeper import/bind/call을 제거했다.
   - `src.engine.sniper_state_handlers`에 venue별 same-session terminal decision과 20:00 unresolved 상태 수집을 연결했다.
   - `src.engine.kiwoom_orders`의 신규 BUY pre-call hard cutoff는 일반 time-block 설정으로 우회할 수 없다.
3. simulator·feedback
   - `src.engine.scalping.sim_source_quality`에서 synthetic/test identity와 비현재 session을 제외한다.
   - sim restore/persist, daily/midcheck, post-sell candidate/evaluation/backfill이 같은 source-quality 계약을 사용한다.
4. automation·consumer
   - preclose cron installer와 postclose OpenAI recovery 호출을 제거했다.
   - current verifier/runtime summary/key-lineage/EV/Pattern Lab에서 retired artifact를 요구하거나 결손으로 판정하지 않도록 정리했다.
   - 과거 preclose wrapper와 public overnight CLI는 artifact를 생성하지 않는 명시적 retired no-op으로 남겨 기존 호출자의 안전한 종료만 보장한다.

## 4. 반복 리뷰에서 발견·보완한 결함

1. terminal SELL 신호가 뒤쪽 일반 scalping 분기에서 다시 덮이는 결함을 `not is_sell_signal` 경계로 차단했다.
2. main engine에 남아 있던 gatekeeper import/bind/call을 제거했다.
3. 폐기된 overnight holding-flow revert hook과 runtime 분기를 제거했다.
4. sim 상태 timestamp가 `NaN`, 무한대 또는 비정상적으로 큰 값일 때 restore가 예외를 내거나 오염 상태를 수용할 가능성을 fail-closed 처리했다.
5. retired LDM/bucket 산출물을 Pattern Lab이 계속 current prerequisite로 요구해 허위 source gap을 만들던 연쇄 소비를 제거했다.
6. 실제 crontab에 남아 있던 `SCALP_SIM_OVERNIGHT_PRECLOSE` 15:10 trigger를 제거했다. PREOPEN 07:35, POSTCLOSE 20:10, finalization 21:55 trigger는 유지했다.
7. 점검 과정에서 잘못 생성된 `threshold_cycle_preopen_--help.status.json`은 삭제하지 않고 `data/archive/runtime_state_quarantine/threshold_cycle_preopen_invalid-help-status_20260906.json`으로 격리했다. 현재 simulator state의 active position은 0건이다.

## 5. 검증 증거

- 전체 회귀: **10,817 passed, 36 skipped, 0 failed** (`pytest`, 387.93초).
- targeted 회귀: 623 passed/18 skipped, 1,037 passed, 662 passed, 연쇄 결함 보완 subset 139 passed.
- 정적 검증: 변경 대상 Ruff PASS, Python compile PASS, shell `bash -n` PASS, `git diff --check` PASS.
- PREOPEN handoff: `data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-07.json`의 `passed=true`, `status=pass`, `findings=[]`, runtime-policy/missing/unverified/retired blocker 0건.
- 운영 스케줄: 실제 crontab에서 `SCALP_SIM_OVERNIGHT_PRECLOSE`와 wrapper 호출이 모두 부재함을 재확인했다.
- 테스트 skip은 폐기된 compatibility fixture 및 기존 선택적 경로이며 failure가 아니다. 경고 19건은 기존 pandas-ta, multiprocessing fork deprecation, bool 반환 테스트 경고로 이번 변경 finding과 무관하다.

## 6. 런타임 적용과 남은 자연 확인

다음 거래일 런처는 PREOPEN exact-date env와 operator overlay를 자동 로드하고 handoff verifier 실패 시 기동을 차단한다. 별도 사용자 명시 개입으로 overnight job을 실행하거나 OpenAI recovery를 호출할 필요가 없다. bot 재기동과 실주문은 이번 작업에서 수행하지 않았다.

자연 적용 확인 owner는 checklist의 `ScalpSameSessionTerminalNaturalEvidence0907`이다. 다음 POSTCLOSE에는 다음 순서로 판정한다.

1. 정상 PID의 effective BUY cutoff와 retirement OFF 값을 runtime provenance로 확인한다.
2. 자연 대상이 있으면 venue별 terminal decision과 공통 SELL journal/order/fill receipt를 동일 symbol/session/generation으로 대사한다.
3. exact receipt 뒤 sim post-sell candidate/evaluation join을 확인한다.
4. 20:00 unresolved가 있으면 합성 완료하지 않고 quote stale, venue conflict, 주문 불명확, custody/reconciliation blocker로 분리해 보완한다.

이 자연 관측은 구현 완료의 재개 조건이 아니라 실제 효과·운영 귀속의 후속 증거 수집이다. 구현 및 자동화 연결 자체에는 현재 미해결 결함이 없다.
