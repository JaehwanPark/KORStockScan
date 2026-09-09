# 위젯·에피소드 적응형 청산 구현·재리뷰

기준일: `2026-09-09 KST`. 판정: **오프라인 부분 구현, 전체 구현 미완료·실거래 미적용**.

사용자 후속 구현 요청에 따라 [상세계획](../proposals/widget-episode-adaptive-exit-implementation-plan-2026-09-09.md)의 권한 없이 완성 가능한 순수 판정·계약 검증과 장후 source census 연결을 구현했다. 매도 주문 전환의 위험 설정은 아직 주어지지 않았으며 임의의 default로 채우지 않았다. `$korstockscan-review-gate`를 사용해 구현→리뷰→보완→재검증했다. 병행 Entry AI 코드/문서 및 자동 갱신된 운영 산출물은 이 리뷰 범위가 아니다.

## 1. 실제 구현 범위

| 영역 | 코드/연결 | 완료 경계 |
| --- | --- | --- |
| 순수 판정 | [adaptive_exit](../../src/trading/order/adaptive_exit/decision.py), [models](../../src/trading/order/adaptive_exit/models.py) | 시간·progress·회복 부진·지지 약화의 결합, 1회 유예, 명시적 hard wall/loss trigger, source/clock/quantity epoch 검증. 새 주문 권한 없음 |
| trailing 기초 | 같은 순수 판정 | 도달 전 비용 여유·기하 조건, arm intent까지만. 확인 후 high-water/stop 입력의 단조성. 실제 cancel 후 arm adapter 미구현 |
| 주문 상태전이 | [reducer](../../src/trading/order/adaptive_exit/reducer.py) | target 예약→durable intent→cancel pending→정확한 terminal→잔량 예약→sell submitting→ACK working→실제 fill/flat. 기존 registry/gateway에 연결되지 않은 순수 reducer |
| replay | [replay helper](../../src/engine/monitoring/machine_adaptive_exit_replay.py) | 동일 evaluate 함수와 유예 상태로 source path를 재생. 요청 intent를 CF fill로 바꾸지 않고 economics는 null |
| 연구 gate | [policy helper](../../src/trading/config/machine_adaptive_exit_policy.py) | 외부에서 사전 고정한 계약의 수치·hash·scope·authority, primary 절대 EV/순이익·holdout 비훼손·tail/coverage 검사. 연구 helper이며 적용 정책 loader가 아님 |
| 달성 가능성 | 같은 helper | 연속 거래일 성숙 고유 표본 수, 무유입일, rolling expiry를 포함한 조건부 ETA. 명시적 hard capacity가 floor 미만일 때만 구조적 불가능 판정 |
| 기존 장후 연결 | [attribution](../../src/engine/monitoring/machine_microstructure_attribution.py)→`rolling_policy_research_v2`→Markdown | 신규 schema는 `machine_adaptive_exit_source_census_v1`; 경제성 evidence/candidate가 아닌 결손 census. 새 cron/중복 producer 없음 |

신규 모듈은 `trading/order/adaptive_exit`, `trading/config`, 기존 `engine/monitoring` 역할 package에 배치했다. engine root 신규 모듈·호환 wrapper·신규 daemon은 없다. pure 모듈에는 broker/network/file I/O가 없다. 의도적으로 gateway/API parser/요청·등록·복구 프로토콜을 수정하지 않았으므로 Kiwoom protocol 수정 gate를 통과했다고 주장하지 않는다. WP4 착수 때 공식 revision/관련 규격 검증이 별도로 필요하다.

## 2. 실제 원천 확인과 기대효과

읽기 전용 검사 대상은 `data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json`이다. byte SHA256은 `0b15809fc5665c2bcbd22f6eefa74a90041fc8915d0b6d90b8e71c46ef5a2012`다. 운영 report는 재생성/덮어쓰지 않았다.

- 기존 attribution anchor에서 owner/scope/symbol/session/lifecycle 기준 고유 30개, malformed 0개를 확인했다. entry/exit/leg anchor 반복은 lifecycle 분모로 중복 집계하지 않았다.
- 이는 계좌의 전체 episode census나 신규 exit 유효 표본 30개가 아니다. 새 first-fill/lot/position epoch·ordered exit path normalizer가 아직 없으므로 신규 계약의 eligible 0, source-invalid/unbound 30이다. 기존 원천이 모두 손상됐다는 판정도 아니다.
- `counterfactual_exit_resolved=false`, `actual_broker_terminal=false`, `net_ev_pct=null`을 유지한다. 가격 touch·호가 VWAP·exit intent는 실제 주문 체결이나 순익이 아니다.
- 예상 기전은 느리고 지지가 약한 보유의 자본점유/손실 확대 억제, 빠른 접근 잔량의 추가 상승 참여다. 반등 직전 조기매도, 목표 취소 중 가격 되돌림, 추가 비용·미체결의 역효과도 가능하다. 이번 테스트는 분기/보호 계약만 검증했으며 이 기전의 순수익 개선은 미입증이다.

## 3. 승인 조건과 자동화 판정

기존 v1 승인 producer와 공통 approval consumer의 기준은 변경하지 않았다. 새 연구 helper에만 다음 차이를 둔다.

- baseline EV가 0/음수여도 primary의 비용 후 절대 EV 증분·순이익 차이로 비교한다. relative 1% 분모 조건을 요구하지 않는다.
- 5/10/20일 동시 양수 조건을 신규 연구에 복사하지 않는다. 사전 계약의 primary/chronological holdout을 사용한다. 단, 실제 paired 집계·purge 계산은 아직 구현되지 않았고 helper는 그 결과의 필수 계약을 검사하는 단계다.
- holdout은 주 평가창과 같은 최소 개선폭을 반복 요구하지 않고 EV·순익 비훼손을 확인한다. candidate 평균 net EV 양수·tail 보호는 유지한다. 모든 조기매도 거래가 이익이어야 한다는 조건은 없다.
- floor·window·tail·거래 범위는 candidate가 정하지 못하고 별도 `EvaluationContract` 입력으로 고정한다. 테스트의 숫자는 fixture이지 운영 추천값이 아니다. helper 결과는 `research_ready`까지이며 항상 `eligible_for_next_preopen=false`다.
- 성숙 표본 0건에 양수 유입일만 고른 ETA를 붙이지 않는다. 관측 유입률로 rolling floor에 도달하지 못하면 근거 대기로 두며, 이것만으로 hard safety를 낮추거나 시장 기회 부재를 선언하지 않는다.

| 경로 | 현 상태 |
| --- | --- |
| 기존 21:15 wrapper→attribution→v2 child→Markdown | 코드 연결·fixture 검증. 자연 당일 실행 미확인; 설치/재시작 변경 없음 |
| v2→경제성 execution replay→candidate/승인 dispatch | 미완료. legacy timeout EV로 대체하지 않음 |
| 승인→새 exit PREOPEN publisher→owner loader | 미등록/미구현. 자동 실거래 적용은 아직 없음 |
| 현재 owner PID→exit intent/취소/매도 | 연결되지 않음. 기존 target 유지 |

따라서 현재 적용을 막는 주된 이유는 과도한 EV floor가 아니라 **미결정 위험 계약과 미완성 source/주문 전환/적용 경로**다. 조건을 삭제해 우회할 대상이 아니다. 이후 명시적 envelope 안에서만 PREOPEN 자동 조정 연결을 구현하며 매일 수동 승인을 새 gate로 추가하지 않는 설계를 유지한다.

## 4. 리뷰·수정보완

1. scope/수량 epoch·첫 fill 시계가 재시작/부분체결로 바뀌면 다시 초기화하는 대신 recovery로 분리했다. source sequence/epoch·future quote·깊이 부족·crossed BBO·support 결측을 정상/약세로 정규화하지 않는다.
2. 유예 종료시각만 저장하면 비정상적으로 늘릴 수 있어 grant 시각+frozen extension 길이 일치와 future grant 차단을 추가했다.
3. 취소 ACK→residual ready, SELL ACK→flat의 잘못된 전이를 금지했다. 취소 중 target 전량 체결은 flat이고 새 SELL/re-entry가 없다. 잔량 예약은 submitting/recovery에도 보존한다.
4. malformed persisted bool/state·다른 dated order/owner/intent·중복 event ID의 payload 충돌을 거절한다. blind retry 대신 adapter의 exact broker reconciliation이 필요하다.
5. VWAP와 최악 depth bid를 별도 반환한다. VWAP를 전량 체결 limit 가격으로 사용하는 코드는 만들지 않았다.
6. holdout에 primary 최소 증분을 중복 요구하던 초안 gate를 비훼손 기준으로 보완했다. 요약의 holdout count가 전체 unique count를 초과하는 반례도 차단했다.
7. optional census의 legacy 원천 NaN/비정상 collection은 해당 child의 명시적 gap으로 격리한다. parent hash를 child에 넣는 순환 참조를 피하고 source projection/canonical child/외부 byte hash를 구분했다.

최종 영향 회귀는 **348 PASS**다. 신규 4개 test module과 기존 turnover research/attribution/approval/checklist builder를 함께 실행했다. Black·Ruff·compile·`git diff --check`, print-only 문서 parser(36개, 기존 owner 1개)도 통과했다. 최초 55/284/343 테스트는 중간의 중복 집합이며 합산하지 않는다. crossed BBO 보완 중 원인 분류 우선순위 테스트 1건이 실패해 invalid depth 우선으로 수정했고 최종 재검증에서 통과했다. 구현된 순수 로직·진단 child 범위의 미해결 review finding은 0이며, 아래 미완료 기능을 이 수치에 포함해 닫지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  src/tests/test_machine_adaptive_exit_decision.py \
  src/tests/test_machine_adaptive_exit_reducer.py \
  src/tests/test_machine_adaptive_exit_policy.py \
  src/tests/test_machine_adaptive_exit_replay.py \
  src/tests/test_machine_lifecycle_turnover_policy_research.py \
  src/tests/test_machine_microstructure_attribution.py \
  src/tests/test_machine_microstructure_policy_approval.py \
  src/tests/test_build_next_stage2_checklist.py
```

## 5. 미완료 작업과 다음 입력

- WP0 부분: schema/권한/location/census 연결 완료, 실제 지원률 및 위험 envelope는 미정.
- WP1 미완료: 전체 owner episode denominator, 첫 actual fill/lot clock·target epoch·동일 horizon post-target 관측과 직접 정규화. 현재 anchor census를 완성된 자연 source로 세지 않는다.
- WP2 순수 로직 구현/검증: 실제 owner adapter·상태 영속화 E2E 완료와 구별한다.
- WP3 부분: decision replay/연구 gate/census만. cancel latency·queue·partial fill을 포함한 execution base/stress 모델, paired 경제성·purge·uncertainty와 native candidate/승인 consumer는 미완료다.
- WP4/5/6 미완료: 실제 SELL 취소·잔량·pending BUY 중재, source EXIT와 단일 owner 중재, frozen policy/loader·서비스 생존성, 취소확인 뒤 trailing arm/잔량 종료. 순수 reducer 회귀를 실제 gateway 회귀로 대체하지 않는다.
- WP7/8/9 미완료: trusted family 등록·PREOPEN atomic publish·정책 실제 소비, 최초 적용과 actual R6. 현재 거래 프로세스·정책·주문 변경 없음.

후속 주문 adapter 동작을 고정하려면 **첫 owner/profile, 최대 보유시간/손실·source-loss/세션 정책, 취소 후 SELL 가격/TTL/시도 한도/최종 잔량 처리**가 필요하다. 일부 trailing의 runner scope는 후속 모드에서 따로 확정한다. 사용자에게 이 설정을 요청했으며 미응답 상태를 임의 승인으로 취급하지 않는다.

실행/자연 확인 owner는 오늘 checklist의 기존 `MachineLifecycleTurnoverObjectiveFollowup0909` 하나다. 코드·문서 검증 범위의 미해결 finding과 위 전체 미완료 기능을 구분하며 전체 계획의 finding 0/구현 완료·경제성 성공을 선언하지 않는다. Project/Calendar sync·운영 재생성·기동·주문은 실행하지 않았다.
