# S6 `DirectFamilySourceRepairLowPriceTwoLeg` 저가 2-leg 원천 계약

실행일: **2026-09-28 KST**. 범위: [S2](2026-09-27-intraday-postclose-handoff-S2.md), [S4](2026-09-27-intraday-postclose-handoff-S4.md), [직전 S6](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-04.md), [현재 checklist](../checklists/2026-09-28-stage2-todo-checklist.md)의 이 family 한 묶음. **판정: 생산자와 첫 reader의 상태 세대·profile 격리·실제 비용 계약 결손을 작업본에서 수리했다. 실제 적격 체결 표본은 여전히 부족하다.**

## 실제 경로와 owner

| 단계 | 생산자 → 원천 → 직접 소비자 | 확인한 경계 |
| --- | --- | --- |
| 장중 dispatch | enabled profile별 `korstockscan-low-price-two-leg-*.timer` → `korstockscan-low-price-two-leg@.service` → `deploy/run_low_price_two_leg_live.sh` → `src.trading.low_price_two_leg.service` → `LowPriceTwoLegMachine` | profile별 별도 state·주문 ledger; `entry_timing_owner=episode`. `--live`도 authority·정확한 정책·owner preflight를 통과해야 한다. main·widget·manual·Samsung machine의 주문 owner와 합치지 않는다. |
| 영속·raw 원천 | profile별 `data/runtime/low_price_two_leg/{profile}_state.json` 및 `pipeline_events`의 `low_price_actual_economic_observation` | signal/features, 두 leg ID, 계획/체결/잔량/owned order 번호, 보유·청산 상태, logical/source date, session·policy SHA·관측 시각을 profile별로 기록. 이벤트는 주문 자체가 아니다. |
| 최초 장후 reader | `deploy/run_threshold_cycle_postclose.sh`의 직접 `low_price_two_leg_tuning` dispatch → `src.engine.monitoring.low_price_two_leg_tuning` | 최종 source-quality audit의 논리 SHA·stage 건수와 raw 관측을 대사하고, 영속 state의 profile·2-leg·수량 보존·정책 및 broker terminal을 검사한다. 후속 candidate는 관측/선택과 런타임 적용을 별도 판정한다. |

읽기 전용으로 확인한 설치 unit의 `WorkingDirectory`/`ExecStart`는 독립 episode 릴리스 `full-workspace-20260928-30e66ae5`를 가리킨다. 예시 `cj_cgv_afternoon`, `samsung_heavy_midday` unit은 확인 당시 `inactive`, `MainPID=0`이었다. timer 등록/릴리스 경로는 dispatch 설정의 증거이며, 이번 **미커밋 작업본 코드의 선택·PID 소비**는 아니다. Samsung 동일 단계 owner는 Samsung machine 자체의 별도 order book·service이고, 저가 profile signal을 Samsung 진입 주문에 연결하지 않는다.

## 9/23 분모와 재현 결손

기존 [9/23 보고서](../../data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-23.json)는 최종 audit SHA `fd49c1dbd601e4aaba6228fed663b0a161771f2619fea635252d5ece078ff8bb` 및 raw 논리 SHA `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`에 결속한다. `low_price_actual_economic_observation` **원본 1,035 / 기존 검증 1,035 / invalid 0**은 *관측 event* 분모다. 일별 투영은 **61 profile = pass 58 + source gap 3**이며, attempted profile 20의 leg **40개 모두 `NO_FILL`**이다. 해당 투영의 completed/held leg는 각각 0이다. 1,035를 제출 주문·체결·완료 leg 또는 broker 실제 과금의 분모로 쓰지 않는다. `decision=profile_separated_actual_outcome_observation_only`, `paired_economic_search.status=incumbent_preserved`, `actual_sample_floor`를 유지한다. 9/23 영수증에는 아래 새 state SHA·real/sim 구분이 없어 `legacy_unbound`로만 표현하고 ID·비용을 소급 생성하지 않는다.

실패 회귀를 먼저 작성했을 때 **3건 실패**했다: 잘못된 profile symbol/session 관측 수용, 고정 비용 추정치를 실현손익으로 합산, 재작성된 state를 과거 raw 관측과 같은 세대로 수용. 원인은 raw reader가 event body hash·날짜·owner·profile 이름만 보고, 영속 state 세대 및 real/sim·profile symbol/session을 직접 결속하지 않은 점과 `_aggregate`의 비용 fallback 합산이었다. producer는 event에 state 영속 세대 SHA를 내지 않았다. 그 결과 구세대·혼합 profile의 체결/보유를 장후 경제성에 잘못 귀속하거나, 실제 비용 미관측을 정밀 손익으로 표시할 수 있었다.

## 작업본 수리·자가 리뷰

- `machine.py` 생산자는 기존 영속 state 저장 후 안정적인 경제성 투영과 `state_source_sha256`, `execution_mode=real|sim`을 기존 raw event에 추가한다. 주문·취소·수량·timeout·threshold·broker API 호출은 수정하지 않았다. profile ID·symbol/session·owner·정책 SHA·원천 bar SHA·시각·leg/position/order 상태를 기존 body에 보존한다.
- 첫 reader는 논리 source SHA·stage 건수·파일 안정성과 event body SHA를 대사한다. 2026-09-28 이후 원천은 profile symbol/session, policy SHA, logical/observed date, real/sim, state 투영 SHA와 leg/position 동일성을 검사한다. 동일 관측의 중복과 같은 clock의 상충 state를 격리하고, profile별 `real_events`·`sim_events`·유효·격리 건수 및 최신 **real** state SHA를 남긴다. 정상 raw와 동일 논리 내용의 `.gz`를 읽으며 손상·누락·SHA 불일치와 `valid_empty`를 별도로 판정한다. 식별 가능한 단일 profile의 invalid event는 해당 profile만 source gap으로 두고 다른 profile의 원천을 유지한다. profile별 state·event 원본/유효/격리/미관측과 leg별 원본/유효/격리/미관측/경제성 제외를 별도 census에 기록한다. 감사 원천이 profile별 기대 event 수를 제공하지 않으면 profile event 미관측은 `null`이다.
- reader는 attempted state의 SHA가 해당 profile의 최신 real event SHA와 같을 때만 그 세대를 적격으로 남긴다. no-attempt profile도 원천 관측이 invalid/누락이면 정상 무거래로 세지 않는다. 기존 leg 보존식(계획 수량, BUY 체결, SELL 체결, 보유 잔량)과 full/partial/open/terminal·정책 SHA 검사에 이 세대 검사를 결합했다. 주문/체결 ID가 영속 원천에 없으면 미관측이며 생성하지 않는다. 과거 날짜는 새 세대를 강제하지 않아 당시 보고서를 재해석하지 않는다.
- 실제 broker 과금이 없는 `fixed_cost_fallback`의 선택 효과와 실현손익은 `false`·`null`로 고정한다. `_aggregate`는 모든 broker 가격 완료 leg에 실제 과금 귀속이 있을 때만 전체 실현손익/EV를 낸다. 고정 비용 추정치와 target-price proxy는 별도 진단 필드로 유지한다. manual operator exit receipt도 정확한 과금이 없으면 `null`이다. terminal 시각이나 실제 비용이 빠진 행을 수익성 승인으로 승격하지 않는다.

자가 리뷰에서 오래된 영수증에 신규 세대를 강제하던 회귀, mixed exact/fallback의 추정치 분모, 손상 gzip 예외, profile별 invalid 격리, malformed event·leg의 격리 건수, 수동 청산의 fallback 필드를 고쳐 재검토했다. 현재 범위의 미해결 코드 결함은 0이다. Broker request/response parser는 변경하지 않아 Kiwoom 공식 reference gate 대상은 아니다.

## 검증과 인계

- 실패 재현 3건을 유지하고 정상 raw·동일 논리 `.gz`·real/sim 분리·중복·손상·누락·valid-empty·구세대 거절·profile 격리·leg별 NO_FILL 경제성 제외를 fixture로 검사했다. 영향 `src/tests/test_low_price_two_leg.py` **241 passed**. Python compile 및 `git diff --check` 통과. wrapper 미수정으로 `bash -n`/wrapper 계약 검사는 해당 없음. Ruff 전체에는 이 테스트 파일의 기존 E701 7건이 남지만 이번 수정 줄의 지적은 0건이다.
- 닫힘 검사 owner: `LowPriceTwoLegMachine` 장중 원천과 `low_price_two_leg_tuning` 첫 reader. 다음 자연 source date에 profile/leg별 raw = valid + quarantined + unobserved를 맞추고, 동일 정책·state SHA의 real BUY/SELL broker order·execution·취소 terminal 및 보유 잔량을 확인한다. 실제 과금·terminal clock이 없으면 경제성은 계속 `null`, 적격 표본이 없으면 `insufficient_sample`이다. paired source·독립 holdout·비용 조정 수익성과 전체 자연 terminal은 S7에서 별도 판정한다.
- 이 수리는 작업본 fixture 검증이다. 선택 릴리스, profile PID 소비, 자연 장중 생성, 장후 성공, 정책 채택, 실주문·체결을 뜻하지 않는다. 릴리스·PREOPEN·PID 수용은 S8에, 새 자연일 조건부 `S5-FIN-05`는 별도 묶음으로 인계한다. 정규 장후작업·PREOPEN·배포·주문·취소는 실행하지 않았다.
