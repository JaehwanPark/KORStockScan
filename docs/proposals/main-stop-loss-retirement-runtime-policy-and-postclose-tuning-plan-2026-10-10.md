# Main 손절 퇴역 제거·런타임 보완·정책화 및 장후 튜닝 계획

작성일: 2026-10-10 KST

상태: **10/11 반복 리뷰·보완 후 승인된 통합 배포와 10/12 기동 준비 PASS**. 퇴역 제거·런타임 수리·기본 정책/장후 발행/감시 연결과 격리 회귀를 구현했다. [10/11 구현·반복 리뷰](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)에 범위·실측·잔여 수용을 기록한다. 전체 Main/결합 성능·신규 보호선 생성·AI vote 경제 변경 selector·운영 인계까지 완료한 상태는 아니다. 승인된 후속 작업에서 native 장후 인계·배포·PREOPEN을 완료했다. 실제 10/12 기동·자연 소비와 신규 경제 후보는 별도 수용이다.

## 1. 목표·범위·owner

요청한 여섯 항목을 SL0–SL8로 연결한다: holding AI 점수 손절 퇴역코드 완전 삭제, 기타 비활성 코드 완전 삭제, 휩소 추가 확인 완전 삭제, 손절 런타임 결함 보완, 경로별 기준선·임계치 장후 튜닝 연구, 성능 개선·저하 방지.

후속 지시를 반영해 **현재 60초 기본 소프트 손절 유예와 보호 트레일링 확인 파라미터를 장후 튜닝 가능한 정식 정책으로 구현**한다. 현행값 초기 계승 → 공통 runtime/replay 판단 → 장후 평가 → selector/다음 PREOPEN → 포지션 pin·실제 PID 소비까지 연결한다. env 외부화나 보고서 추천만으로 정책화를 완료하지 않는다.

**시간 경과로 해소되지 않는 정책 생성 결함을 먼저 닫는다.** 실제 활성 producer가 쓰지 않는 필드, 도달 불가능한 경로, 순환 선행조건, 전역 표본 gate, 불일치한 schema/target와 누락된 caller를 단순 `hold_sample`로 미루지 않는다. §6.0의 생성 가능성 검증과 §7의 생산·소비 전체 성능을 SL0–SL6의 필수 수용으로 둔다. 정책 파일 생성·값 변경 선정·실제 소비를 각각 검증한다.

- 기타 비활성 코드는 Main 손절·보유청산의 producer/caller/state/설정/AI payload/보고서·연구·정책·검증 consumer 전체를 뜻한다. 저장소의 모든 OFF 기능 삭제로 확대하지 않는다.
- 완전 삭제는 실행 함수·분기·호출·전용 상태/설정과 신규 관측·연구·추천·발행·loader 의존 제거다. 항상 False인 wrapper, no-op, 이름만 바꾼 추가 확인 유예 또는 source-only 신규 수집으로 남기지 않는다.
- 역사적 journal·체결·수탁·비용·정책·봉인 bytes는 보존한다. 과거 schema 독자와 폐기 key 재유입 방지 denylist만 파일/이유/허용 용도를 명시해 잔존할 수 있다. 실행·튜닝 권한은 없다.
- 코드 기본 False와 실제 OFF를 구별한다. operator lock→prepared env→포지션 pin→실제 caller를 대사한다. 활성 기능, Main/manual custody·수동 veto·계좌/주문/수량/freshness·hard/protect/emergency 안전은 삭제 대상으로 간주하지 않는다.
- [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md)와 [오늘 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md)를 따른다. clean baseline은 6/5, 신규 후보 학습은 현행 9/29 forward 경계다. episode/widget·PYRAMID 등 퇴역 실행은 복원하지 않는다.

현재 owner는 10/11 checklist의 `MainStopLossRetirementRuntimeTuning1010` 하나다. 10/10 계획 기록과 수용을 보존하고 후속 구현·리뷰 결과를 이 owner에 연결한다. 기존 `MainAllScopeTrailingReplay`·`PreSubmitDelaySituationImplementation1010`의 승인과 수용을 유지하며 그 구현 결과에 손절 변경을 소급 포함하지 않는다. 공동 consumer/예산은 [잔여계획 W0–W6](main-trailing-delay-residual-work-completion-plan-2026-10-10.md)와 연결한다.

## 2. 출발점과 확인한 결함·공백

계획 작성 당시 10/10 조회의 [선택 release](../../data/runtime/runtime_release_selection.json)는 `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28`다. handler·상수·체결 receipt의 workspace와 release bytes가 같았고 Main PID는 없었다. 아래 값은 [10/12 prepared env](../../data/runtime/policy_bootstrap/prepared/2026-10-12/2026-10-08_86586b7a18072595_d61b36b00696865c/runtime_policy_bootstrap_2026-10-12.env), [manifest의 key owner](../../data/runtime/policy_bootstrap/prepared/2026-10-12/2026-10-08_86586b7a18072595_d61b36b00696865c/runtime_policy_bootstrap_2026-10-12.json), 코드 조회 근거다. SL0에서 다시 고정하며 현재 PID 적용 영수증으로 사용하지 않는다.

| 경로/설정 | 확인 기준 | 보존/정책화 경계 |
| --- | --- | --- |
| 기본 SCALP preset | 초기 체결의 `hard_stop_pct=-1.4`, 비상 `-2.4`, preset 유예 기본 0초 | `SCALP_PRESET_TP` 이름 아래 손절 state는 살아 있다. preset 익절 퇴역과 혼동해 지우지 않는다. |
| 일반 SCALPING/SCANNER | soft `-3.0`, common hard `-5.0`; SCANNER 초기 체결은 preset state를 새로 생성하지 않음 | role별 출처를 보존하고 fast에서도 같은 유효 기준을 해석한다. |
| soft 기본 유예 | 코드 기본 ON·60초, 준비된 emergency `-4.0`; 회복 시 유예 state 해제 | `soft_stop_micro_grace` 단일 타이머를 정책화한다. |
| 보호 트레일링 확인 | 보호 가격선이 있을 때 window 20초, min span 8초·sample 3개, below ratio 0.67, buffer 1.00%; exit floor override `-0.3%`, smoothing emergency 기본 `-2.0%` | 확인 파라미터를 정책화하되 보호선 생성·승계와 강제 안전선의 권한을 구분한다. |
| 수동 인계/fast | 수동 인계 ON·재시도 5초, fast safety ON·poll 250ms | 일반 루프의 인계와 fast 직접 dispatch 차이를 보완한다. |
| 기본 False지만 관측 계산 ON | profit stagnation·low-profit stagnation은 prepared env에서 ON이나 현재 caller는 `_observe_scalp_tp_alternative`에만 결과를 전달 | 독립 실매도 경로가 아니다. 관측 consumer의 필요성을 확인하고 폐기 score 의존을 정리한다. ON 설정을 live 변경 정책의 근거로 쓰지 않는다. |
| 그 외 전략 분기 | prepared env의 KOSDAQ `-5.0`, KOSPI BULL/BEAR `-6.0`, BREAKOUT `-3.0`, BOTTOM `-8.0` | 코드에 값/분기가 있다는 사실과 활성 Main 수탁·실제 도달 여부를 구분한다. Swing OFF·퇴역 owner를 복원하지 않는다. |

손익은 [trade_profit](../../src/engine/trade_profit.py)의 비용 반영 수익률·반올림 의미를 유지한다. 설정 비용은 실제 정산 비용이 아니다. `trailing_stop_price`는 가격, soft/hard는 net 수익률이며 `protect_profit_pct`, 일반 익절 `scalp_trailing_take_profit`과 합치지 않는다.

| ID | 확인 근거 / owner artifact | 영향·종료 시험 |
| --- | --- | --- |
| SL-F1 | [handler](../../src/engine/sniper_state_handlers.py)의 일반 루프는 `_handoff_hard_stop_to_manual_control_if_enabled`를 호출하지만 `evaluate_and_dispatch_fast_scalp_exit`→`_dispatch_scalp_preset_exit`에는 신규 인계 호출이 없음 | 비상 미도달 hard stop의 인계/SELL이 루프 순서에 따라 달라질 수 있다. 동시 실행·등록 실패·재시도에서 승인 disposition 1개, 중복 주문 0을 검증한다. 자연 오주문 발생을 확인한 것은 아니다. |
| SL-F2 | fast는 포지션 hard/emergency/protect field를 읽고 일반 SCALPING은 공통 규칙도 사용. [초기 체결](../../src/engine/sniper_execution_receipts.py)의 SCANNER는 preset field를 생성하지 않음 | pin 없는 role·복구 시 fast 안전 coverage를 재현한다. role별 출처·결과를 대사하고 preset 수치를 SCANNER에 임의 주입하지 않는다. |
| SL-F3 | `_holding_path_exit_proceeds`의 safety는 공통 hard와 보호 smoothing emergency를 참조; soft 유예 emergency는 별도 | 현재 `-3.0` soft 신호는 기본 `-2.0` 조건으로 AI VETO 유예가 해제된다. 현행 fixture와 역할별 출처를 먼저 고정한다. `-2.0`을 `-4.0`으로 바꿔 유예를 늘리는 변경을 단순 정합성 수리로 처리하지 않는다. |
| SL-F4 | normal 하드 스톱의 REST 재확인과 fast quote/route 판단, preset grace·판단시각이 분리됨 | 동일 quote/role/pin/시각의 first crossing·disposition을 대조한다. 응답을 요청 전 시각으로 평가하거나 다른 venue 가격을 쓰는지 시험한다. 미재현 차이는 확정 장애로 집계하지 않는다. |
| SL-F5 | [holding report](../../src/engine/holding_exit_observation_report.py)는 whipsaw canary를 추천, [Sentinel](../../src/engine/holding_exit_sentinel.py)은 해당 owner로 인계, [registry](../../src/utils/threshold_cycle_registry.py)는 source-only 신규 수집 허용 | 실행만 삭제해도 추천·수집·필수 artifact가 남는다. 신규 추천/수집/연구/발행 요구 0과 역사적 귀속 보존을 검증한다. |
| SL-F6 | `PATH_IDS`/prompt/baseline에 OFF bad-entry 등이 있고 [vote policy](../../src/engine/scalping/holding_path_vote_policy.py)는 전체 path×market cell set 검증 | 삭제와 함께 surviving path의 versioned migration·옛 live bundle 거부·새 bootstrap hash 검증이 필요하다. |
| SL-F7 | `_append_holding_price_sample`은 window와 60개 cap을 사용; 확인기는 해당 sample의 중앙값·span·비율 사용 | window만 확대하면 고빈도 입력에서 지원 span이 부족할 수 있다. window/cadence/cap 계약을 함께 검증하며 결손을 정상 HOLD/후보 열위로 숨기지 않는다. |
| SL-F8 | `_apply_scale_in_protection`의 보호선 생성 예시에 퇴역 PYRAMID 분기와 기존 DB/pin 복구가 공존 | 현재 Main의 적법한 보호선 provenance를 대사한다. 연구 표본을 만들기 위해 PYRAMID를 복원하거나 없는 보호선을 합성하지 않는다. |
| SL-F9 | holding report의 `_build_soft_stop_rebound`는 post-sell 반등 집계이며 기존 operational replay는 입력 민감도 전용이다. 이들 존재만으로 grace/protect 정책용 sample·pin·평가→selector 연결이 증명되지 않음 | 정확 필드의 실제 producer→snapshot→adapter→replay→publisher→loader 대사를 SL0 산출물로 만들고 누락 연결을 구현한다. 단순 일수 경과·기존 보고서 반복 실행으로 해결되는 공백으로 분류하지 않는다. |
| SL-F10 | soft가 `max(SCALP_STOP, SCALP_HARD_STOP)`, hard가 `min(...)`으로 재배치됨. preset가 일반 soft보다 먼저 평가되며 ADD 상태는 유예를 0으로 만듦 | raw 값만 튜닝하면 hard가 함께 변하거나 적용 기회가 없는 cell을 선정할 수 있다. §5.1/5.2의 실효 기준·도달 경로·순서 불변 검사를 구현한다. |
| SL-F11 | [vote replay](../../src/engine/scalping/holding_path_vote_replay.py)는 후보 판단 횟수만 계산하고 paired EV/selected policy를 항상 null로 남김. [vote policy](../../src/engine/scalping/holding_path_vote_policy.py)의 `create_bundle`은 `PATH_POLICY_BY_MARKET` 기본값만 발행 | 기존 family에 selector가 완비됐다는 가정을 제거한다. 해당 owner의 bounded 경제 비교/선정 consumer를 보완하거나 baseline-only를 명시한다. 충분한 fixture를 넣으면 changed-policy가 실제 loader까지 도달하는 시험으로 닫는다. |
| SL-F12 | 보호 가격선 확인기는 normal에 있고 fast는 별도 `protect_profit_pct`만 읽음. preset grace는 normal의 보유시간 조건이며 fast hard trigger에는 같은 조건이 없음 | 동일 이름의 보호 경로를 합치지 않는다. §5.2의 경로별 binding을 고정하고 미래 튜닝값이 소비되지 않거나 fast에서 우회되는 조합을 거부한다. |
| SL-F13 | stagnation 두 함수의 `should_exit`는 현재 관측 receipt에만 쓰임. `profit_stagnation_exit_runtime` schema/ON env가 있어도 독립 SELL consumer는 아님 | 기존 계획의 운영 ON 표현을 관측 ON으로 정정했다. 별도 실매도 부활·생기지 않을 실제 경로 경제표본 대기를 금지한다. |
| SL-F14 | `_defensive_avg_down_unfilled_recheck_decision`은 항상 inactive지만 caller·전용 30초/비상값·취소 후 timer 생산 분기가 잔존 | OFF/no-op 삭제 목록에 추가한다. 주문 취소·미체결 확인·사용량 rollback은 생존시키고 손절 추가 유예 전용 state/설정만 제거한다. |
| SL-F15 | stop bundle의 장후 caller·exact key succession·summary/strict·bootstrap receipt·typed runtime lookup은 현재 없음. registry와 guard 관측 계약의 존재는 정책 연결 증거가 아님 | §6.5의 실제 파일/함수별 이행표와 source/target·byte/semantic hash·rollback 세트로 구현 공백을 닫는다. 현재 stage registry에 holding/stop stage가 설치됐다고 가정하지 않는다. |

## 3. 완전 삭제 목록과 생존 경계

SL0에서 각 묶음의 definition/caller/import/env/lock/state/prompt/report/replay/selector/loader/test와 실효 활성 근거를 전수 목록화한다. 아래는 시작 목록이며 단순 문자열 삭제 목록이 아니다.

| 묶음 | 삭제 대상 | 연결 소비처·생존 경계 |
| --- | --- | --- |
| holding AI 점수 손절 | `_holding_strong_trailing_enabled` 손절 확대, 중립 50 대입·가짜 usable context, 전용 score gate/TTL/preflight/reason/log | `_holding_score_*`, `_legacy_holding_score_role_context`, fast 관측, [operational replay](../../src/engine/scalping/trailing_operational_replay.py), stagnation 관측의 공유 의존을 대사. PASS/VETO vote·ADD_REBOUND·시세 품질은 유지 |
| whipsaw 추가 확인 | `_build_soft_stop_whipsaw_confirmation_decision`, touch/used/timer, env/loader, 실행·로그·source-only arm/후행 수집·추천·튜닝 | 해당 family의 registry/ingestion/checkpoint/audit/workorder/Sentinel/strict 요구도 제거. 공용 smoothing journal과 활성 OFI는 유지 |
| OFF 추가 유예 | `SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_*`, expert absorption extension, 비활성 dynamic grace modifier와 score prior | 기본 유예 하나만 생존. 폐기된 보조 10/20/45/90초 타이머를 새 정책에 병렬 부활시키지 않음 |
| 손절 우회 no-op | stop-line mandatory AVG_DOWN·defer, late-loss retry/quote-recovery, `_defensive_avg_down_unfilled_recheck_decision`·caller·전용 state와 `SCALP_DEFENSIVE_AVG_DOWN_UNFILLED_RECHECK_*` | [공유 rebound](../../src/engine/sniper_scale_in.py), 현재 AVG_DOWN 체결/수량/안전·미체결 확인/취소·사용량 rollback 보존. 손절 intercept를 반등 BUY 권한으로 바꾸지 않음 |
| 기타 OFF 손절 분기·관측 | bad-entry refined OFF actuator·score·전용 관측, soft-stop cooldown shadow, 소비 없는 near-AI stop/hard-time-stop 관측 등 | SL0의 실제 활성 대사로 확정. 활성 same-symbol loss-reentry guard와 profit/low-profit stagnation을 혼동하지 않음 |
| 설정·정책 잔여 | 전용 env parser/dataclass/serialization, 폐기 path cell/prompt/schema, operator succession 재생 hook | 원 operator 파일은 보존하고 successor에서 정확 key retirement. 공용 fingerprint·strict consumer 동시 migration |

공유 helper가 활성 기능에도 쓰이면 폐기 helper 전체를 남기지 않고 생존 책임을 기존 역할 package로 분리한다. 현재 stagnation 관측은 constant-neutral 경로와 행동 동등성을 검증하고 점수 제거를 새 ON/OFF나 시간청산 임계값 변경에 사용하지 않는다. 생존 feature에 retired score를 0/50으로 대체하여 계속 전달하지 않는다. `SCALP_TIME_LIMIT_MIN`, `MIN_PROFIT_PRESERVE` 등 deprecated 상수도 실제 caller 0 확인 후 설정/serialization까지 제거하며 활성 장마감 terminal 시간이나 역사적 보유 복구와 혼동하지 않는다.

과거 family를 미등록 오류로 만들면 raw/written/partition 대사가 깨진다. 과거 schema 독자 또는 `historical_retired` disposition으로 귀속을 읽되 신규 튜닝에서는 제외한다. 퇴역 적용 세대 이후 폐기 event의 신규 생산은 계약 위반이다. 역사적 reader·denylist·부활 금지 시험 이외 이름 잔존은 owner와 제거 근거를 확인한다. 과거 raw·정책 원본 삭제는 이 작업에 포함하지 않는다.

## 4. 단계와 공통 런타임 보완

새 파일은 location gate 후 순수 판단/정책/replay는 `src/engine/scalping`, 장후 caller/publisher/handoff는 `src/engine/automation`, 체결 pin은 기존 receipt/lifecycle, 테스트는 `src/tests`에 둔다. engine root 신규 모듈·영구 호환 wrapper는 만들지 않는다.

| 단계 | 산출물 | 종료 기준 |
| --- | --- | --- |
| SL0 기준·inventory | release/PID·lock/pin·호출/설정/consumer 목록, SL-F fixture, 생성 가능성 대사, 연구/성능 예산 manifest | 모호한 삭제 대상·threshold owner 미정 0, 현행 의미와 의도한 delta 및 구조 결함/표본 부족 구분 |
| SL1 점수·OFF 제거 | §3 score/no-op/OFF actuator·관측·설정·caller 삭제와 생존 consumer 분리 | 폐기 실행/신규 score 손절 판단 0, 생존 기능 회귀 |
| SL2 whipsaw 퇴역 | 실행·신규 수집·추천·workorder·정책/strict 의존 제거, path/schema migration | 재유입 0, 역사적 귀속·활성 OFI 정상 |
| SL3 공통 손절 보완 | 순수 판단, claim/수동 인계/기존 dispatch adapter, SL-F1–F4/7/8/10/12 해결 | role×fast/normal×manual×emergency의 기대 결과, 동시성/부분체결/재기동 안전 |
| SL4 정책화 | §5.1 키 대사·typed policy·soft 기준선/유예/보호 확인의 현행값 계승·preload/lookup·position pin·공통 runtime/replay·validator | 경로별 값 소비·실효 상한/우선순위 동등, missing/invalid/expired/rollback·exact key succession 처리 |
| SL5 장후 연구 | 전수 census·causal replay·비용/검열·split·bounded 후보·부모 유지·정상 caller 연결 | §6.0 실제 producer부터 loader까지 부모/선정 성공·부분 결손·정정·상한 초과/재개 시험 통과. 미구현 consumer를 source gap으로 대체하지 않음 |
| SL6 성능·리뷰 | §7 최적화·단독/결합 benchmark, §8 표적 회귀·재리뷰 | 미해결 구현 finding 0, 승인 delta 외 의미 차이 0, 성능 gate PASS |
| SL7 정식 인계 | report/policy→summary/checklist/strict/controller→PREOPEN→불변 release 전환 세트 | 후속 허용 범위에서 새 세대 발행/검증, 구세대 원본 보존 |
| SL8 자연 수용 | 적용일 실제 PID/pin/hash, disposition→intent/submit/fill/terminal/실제 비용 | 관측된 경로만 완료. 미래/표본 없음/manual 인계를 SELL 완료로 보지 않음 |

SL0→SL1/SL2→SL3→SL4→SL5→SL6→SL7→SL8 순서다. 삭제와 정책화의 공용 helper/스키마를 최종 통합 상태에서 재리뷰한다. 초기 부모 계승에 새 양의 EV gate를 붙이지 않는다. 변경 경제값은 §6의 별도 선정 계약을 통과해야 한다.

공통 순수 판단기는 role, position/buy generation, policy pin, fresh quote receipt, 보호선 provenance, 원 touch/elapsed, pending ADD/SELL/잔량, custody/manual 상태를 입력받는다. 결과는 `hold`, `defer_until`, `manual_handoff`, `exit_candidate`, `source_unusable`과 원 rule·threshold 출처·해제 이유다. 모델/REST/DB/파일/주문 I/O는 외부 adapter에 둔다.

1. 비상 미도달 hard stop의 승인된 수동 인계를 fast/normal에 공통 적용한다. emergency/protect와 기존 manual 제외의 우선순위를 명시한다. 이미 수동관리인 물량은 비상이라는 이유로 Main이 채택하지 않는다.
2. 같은 position/buy generation의 인계 또는 SELL claim을 동일 lock/세대 검사로 중재한다. 등록 I/O는 lock 밖에서 예약→등록→세대 재검증으로 완료한다. 등록 실패는 정해진 pending/retry이며 SELL fallback·250ms 등록 폭주를 만들지 않는다.
3. 기존 강제 안전조건은 soft 유예보다 우선한다. 목적이 다른 emergency 값을 하나로 합치지 않는다. SL-F3의 현재 유예 해제를 바꾸는 변경은 `behavior_change/safety_authority_required`로 분리하고 초기 동등 정책 구현은 계속한다.
4. fast에서 pin이 없으면 검증된 동일 role/scope의 loaded baseline만 사용한다. NaN/bool/단위·세대·출처 불일치는 거부한다. preset default 임의 주입·기존 보유 신규 초기화를 금지하고 남아 있는 독립 안전경로·수탁을 보존한다.
5. quote 재확인의 route/item/관측·수신시각을 유지하고 응답 후 현재 세대·시각으로 판단한다. 기존 bounded 재확인과 freshness/conflict 검사를 성능 개선 명목으로 제거하지 않는다.
6. pending SELL을 새 주문으로 만들지 않는다. ADD/partial fill은 원 policy와 실제 평단/잔량 generation을 대사한다. 기존 ADD 후 reset은 golden fixture로 고정하며 reload·재시작이 새 유예를 추가하지 않게 한다.

## 5. 기본 유예·보호 트레일링의 정식 정책

제안 schema는 `main_stop_confirmation_policy_v1`이다. 기존 손절/보호 consumer에 값만 공급하며 새 executor를 만들지 않는다. `soft_stop_micro_grace`와 `protect_trailing_smoothing`을 별도 route cell로 두고 한 holding/exit stage의 정책 세대/변경 중재를 사용한다. 일반 익절 trailing canary와 stage 충돌을 검사한다.

| 영역 | 초기 계승·장후 조정 대상 | 권한 경계 |
| --- | --- | --- |
| soft 기준선·기본 유예 | 실효 `SCALP_STOP=-3.0%`와 60초 계승; `soft_stop_pct`, 단일 `grace_sec`를 별도 축으로 조정 | soft 기준선도 정식 schema/consumer에 포함한다. exact key 승계가 닫힌 범위만 변경 선정하며 hard/emergency를 함께 변경하지 않는다. 추가 whipsaw 타이머 없음 |
| 보호 확인 | 실효 window/span/min samples/below ratio/buffer 계승·조정 | 가격 보호선 생성·단조성·수탁은 기존 owner. sample cadence/cap은 검증된 수집 계약 |
| 보호 exit floor | 실효 `-0.3%`와 출처를 receipt에 결속 | 보호 강도 변경이므로 초기 자동 후보 allowlist 밖. 원 lock 승계 권한·tail/안전 조건을 갖춘 별도 연구로 취급 |
| AI EXIT VETO | 기존 vote family의 quorum/유효창/간격/최대 유예와 runtime worsen·상한을 대사 | 현재 변경 selector가 없음을 SL-F11로 보완. stop bundle은 기존 family와 실효 cap 참조를 결속하며 중복 발행하지 않는다. score 재도입·60초+90초 합산 금지 |
| hard/emergency/manual/quote | 원 실효값·authority hash 참조 | 자동 튜닝 키 아님. poll·REST timeout/freshness·주문/수량/provider 변경도 불가 |

필수 metadata는 schema/algorithm, source/target/effective/expiry, parent/byte SHA, source/cost generation, route·role·시장/세션 scope, values/units, `baseline_carry|selected|hold_sample|source_gap|hold_no_edge`, evidence grade, allowed keys/bounds, authority, rollback pointer다. 폐기 path·unknown key·중복 cell·날짜/부모/출처 불일치를 거부한다.

- **초기값:** 검증된 operator override·포지션 의미를 그대로 계승한다. 정상 baseline 채택에 새 경제 gate를 붙이지 않는다. 단순 값 이동을 신규 임계값 승인으로 표시하지 않는다.
- **preload:** PREOPEN에서 schema/hash/허용범위·부모/target를 검증하고 typed immutable map을 준비한다. hot path는 메모리 lookup만 한다. 모든 Main role/지원 시장에 동작하며 no-sample scope는 같은 scope 승인 부모를 계승한다.
- **position pin:** 새 매수 체결 때 id/hash/값/role을 고정한다. 기존 보유·익일 보유는 복구한 원 정책을 유지한다. AVG_DOWN은 policy identity를 승계하고 평단/수량 generation만 정확히 갱신한다. 정책의 신규 채택 기한과 기존 position pin의 유효기간을 구분하며 날짜 전환·정책 만료만으로 열린 포지션을 새 정책으로 바꾸지 않는다. 원 pin 복구 실패를 현재 후보의 정상 채택으로 숨기지 않는다.
- **시계:** monotonic elapsed와 영속 event timestamp의 역할을 분리한다. 원 touch/defer 시작을 보존하며 clock 역전·duplicate tick·reconnect·날짜/reload로 연장하지 않는다. AI VETO의 경로별 누적 유예도 원 crossing에 결속하고 기본 유예 종료/투표 도착을 새 시작으로 삼지 않는다. 회복→새 crossing reset은 기존 의미를 명시한다. `grace_sec=0`은 해당 soft 경로의 기본 유예 생략이며 강제 SELL 명령이 아니다. preset 손절에 soft 유예를 새로 적용하지 않는다.
- **samples:** 한 receipt를 한 sample로 처리하고 duplicate/late/out-of-order/stale를 검증한다. `min_span<=window`, cadence/cap으로 지원 가능한 span·min samples·ratio/buffer를 사전 검사한다. source 부족은 명시하며 독립 비상 처리는 유지한다.
- **실패:** 잘못된 challenger는 검증된 동일 scope incumbent로 복원하고 기존 pin을 보존한다. 출처 없는 기본값을 유효 정책이라고 보고하지 않는다. rollback은 퇴역 score/whipsaw/OFF 실행을 복구하지 않는 검증 버전으로 제한한다.

window/span/sample/ratio/buffer는 조정 대상이지만 지연을 무한 늘리거나 보호선 아래 더 큰 손실을 허용하는 것을 단순 성능 튜닝으로 취급하지 않는다. SL0에서 incumbent 대비 허용 방향/일일 변화폭·보호/비상 종료 한도를 동결하고 한도 밖 후보는 오프라인 sensitivity로만 남긴다. 보호선 자체의 생성 방식을 바꾸거나 새로운 보유에 선을 추가하는 것은 이 확인 정책의 권한이 아니다.

### 5.1 기준선·런타임 임계치 전수 대사

아래 값은 앞의 prepared env 또는 코드 기본값이며 실제 PID 채택 증거가 아니다. `직접 정책`은 이번 구현안의 값/loader/consumer 대상, `기존 owner`는 해당 family 보완 대상, `안전 계승`은 값을 기록하되 자동 탐색/변경하지 않는 항목이다. enable·수탁·시세 품질·주문 권한을 경제 최적화 키로 바꾸지 않는다. 각 키의 caller·실효값·출처·허용 변경 범위가 없는 행은 SL4 완료로 판정하지 않는다.

| 대상/정확 key | 기준값·현재 소비 | 정책화/누락 보완 |
| --- | --- | --- |
| `SCALP_STOP` | prepared -3.0%; normal 일반 SCALPING soft | **직접 정책**. `soft_stop_pct` 필드·초기 계승·적격 후보·runtime/replay lookup을 구현한다. 현 lock을 이유로 영구 sensitivity-only에 두지 않고 exact successor 계약을 SL4에서 닫는다. 승인되지 않은 실제 값 변경은 보류 |
| `SCALP_SOFT_STOP_MICRO_GRACE_SEC` | 코드 60초; 원 soft touch부터 경과, ADD 상태에서 실효 0 | **직접 정책**. `grace_sec`; `..._ENABLED=True`는 계승된 동작 mode. 0초 의미·reset·effective duration을 검증. 추가 extend/whipsaw/dynamic timer는 삭제 |
| `SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC`, `..._MIN_SPAN_SEC`, `..._MIN_SAMPLES`, `..._BELOW_RATIO`, `..._BUFFER_PCT` | 20초/8초/3개/0.67/1.00%; normal `_protect_trailing_break_confirmed` | **직접 정책**. window/span/count/ratio/buffer 각각 typed field와 단위/유효조합·retention envelope·실효 소비 시험. `..._ENABLED=True`는 자동 탐색 밖 |
| `SCALP_PROTECT_TRAILING_MIN_EXIT_PROFIT_PCT` | prepared -0.3%; 이보다 수익이 높으면 확인 매도 억제 | **안전 계승+별도 제한 연구**. 보호선 가격과 다른 net exit floor를 누락 없이 receipt/정책 참조에 포함. 변경 방향·lock 승계·최악 지연/손실 조건이 닫힐 때만 exact allowlist 확대 |
| `SCALP_HARD_STOP`, `SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT`, `SCALP_PROTECT_TRAILING_EMERGENCY_PCT` | -5.0/-4.0/-2.0%; 서로 다른 안전/유예 종료 consumer | **안전 계승**. typed safety reference 및 hash·출처를 각각 결속. soft 튜닝으로 min/max 재배치되거나 VETO가 새로 연장되지 않도록 검사 |
| `SCALP_PRESET_HARD_STOP_PCT`, `..._EMERGENCY_PCT`, `..._GRACE_SEC` | prepared -1.4/-2.4%, 코드 0초; initial receipt→position field→normal/fast | **안전 계승**. preset grace는 매수 이후 보유시간이며 soft touch 이후 60초와 다름. 현재 constants에 grace env parser가 없고 fast는 grace를 읽지 않으므로 이름만 env로 발행해도 조정되지 않음. 비영(非零) grace 연구는 hard 안전 권한·양쪽 소비가 닫히기 전 적용 제외 |
| `trailing_stop_price`, `protect_profit_pct` | 전자는 가격선 확인; 후자는 pinned net floor로 preset/fast에서 직접 검사. initial receipt는 후자를 None으로 설정 | **서로 다른 source/pin 참조**. 일반 익절 giveback과도 구분. 신규 생성 없는 legacy field는 기본값을 합성해 활성화하지 않음. 보호선 생성 연구는 SL-F8의 별도 owner 설계 |
| vote `min_votes/pass_votes/veto_votes/firm_pass_votes/firm_veto_votes` | 기본 2/2/2/EXIT 경로 0/1; 기존 [AI vote](../../src/engine/ai/holding_exit_vote.py) schema | **기존 owner**. 해당 경로·시장별 검증과 후보 연구에 포함. quorum 최저값을 무시하거나 model 호출을 늘려 표본을 만들지 않음 |
| vote `window_sec/max_latest_age_sec/max_gap_sec/min_duration_sec/max_defer_sec` | 기본 180/40/100/8초; soft max defer 90초, post-ADD 10초, trailing 45초 | **기존 owner**. path별 hard cap·quote freshness·same generation/market과 함께 재생. 기존 replay/기본값 전용 publisher의 구조 공백을 SL-F11로 해결 |
| `HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC`, `HOLDING_FLOW_OVERRIDE_WORSEN_PCT` | 코드 90초/0.80%p; runtime defer=`min(rule,90,path_policy)`; trailing worsen은 별도 0.40%p 상수 | **기존 owner의 실효 cap 참조**. vote policy의 10개 필드에는 worsen이 없으므로 env/global cap을 무시한 candidate는 선정 금지. 자동 변경하려면 해당 owner의 versioned schema/소비 연결까지 확장; 이번 초기 carry는 기존값 유지 |
| `SCALP_SAFE_PROFIT`, `AI_HOLDING_CRITICAL_MIN_COOLDOWN/MIN_COOLDOWN/CRITICAL_COOLDOWN/MAX_COOLDOWN`, review 가격변동 literal 0.20/0.40%p·near-safe band 0.20%p | 현재 점수 계산과 별개로 path vote의 실제 호출 시점을 결정. quote age 3초·동시 review 4개 등 입력/자원 제한도 존재 | **생존 review cadence/품질 참조**. 폐기 score 이름 때문에 함께 삭제하지 않음. 자동 후보는 관측된 투표 시퀀스의 지원 범위를 넘지 않아야 하며 provider cadence/동시성/freshness 확대는 이번 경제 조정 축에서 제외 |
| `REVERSAL_ADD_POST_EVAL_SEC`, `reversal_add_profit_floor`, 0.05%p 악화 buffer, tick acceleration 0.90·large sell 조건 | 25초, floor fallback -1.0%; 특정 AVG_DOWN 사유 receipt가 `POST_ADD_EVAL` 생성→normal 손절→EXIT_POST_ADD_FAIL vote | **기존 ADD/보유 안전 owner**. env 상수 외 literal도 대사. surviving Main 생산자가 실제 도달하는지 확인하고 ADD 실패 방어를 soft 확인 grid에 합치지 않음. 이미 승인된 BUY/수량/평단 의미 보존 |
| `SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT/MIN_SEC/MAX_PROFIT_MOVE_PCT/MAX_PEAK_IMPROVE_PCT` | 1.0%/180초/0.15%p/0.10%p; 현재 alternative 관측만 | **관측 유지/기존 owner 정합성**. 독립 실매도 연구로 선정하지 않음. component가 허용하는 변경 키와 실제 함수가 읽는 키를 대사. `MIN_AI_SCORE`는 퇴역 제거 |
| `SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT/MAX_ADJUSTED_PROFIT_PCT/MIN_HOLD_SEC/ASSUMED_EXIT_SLIPPAGE_BPS` | 0.20/1.00%·1800초·15bps; 위 stagnation window 공유, 현재 관측만 | **관측 유지/기존 owner**. 15bps는 비용 가정으로 exact cost와 구분하고 최적화 대상에서 제외. ON flag·관측 `would_exit`를 SELL 권한으로 바꾸지 않음 |
| `KOSDAQ_STOP`, `STOP_LOSS_BULL/BEAR/BREAKOUT/BOTTOM` | prepared -5/-6/-6/-3/-8%; normal KOSDAQ_ML/KOSPI_ML 및 manual open-loss 기준 helper | **조건부 역할 기준선/초기 carry**. 활성 Main 수탁/도달 여부와 태그·regime별 owner를 먼저 확인. 정책 schema의 명시적 `not_applicable` 또는 같은 역할 기준 참조를 남기며 SCALP 값을 대신 넣지 않음. Swing OFF 경로의 튜닝·실행 복원은 제외 |
| `HOLDING_DAYS/KOSDAQ_HOLDING_DAYS`, same-session terminal 시각·manual handoff retry/open-loss window, quote freshness/REST budget/poll | 시간청산·수탁·시세/주문 안전 경계 | **운영·안전 참조**. 필수 영향 회귀/성능에는 포함하되 손절 경제 후보 키에서 제외. 영업일/세션 계산 변경을 임계값 튜닝으로 처리하지 않음 |
| expert/dynamic/extend/whipsaw·defensive unfilled recheck·retired score·deprecated 시간손절 | OFF/no-op/퇴역 | **삭제**. 새 typed schema·후보 grid·selector 필수 cell에 포함하지 않음. 상태/설정 삭제와 생존 주문 reconciliation을 구분 |

### 5.2 값이 실제 판단을 바꾸는 범위·우선권

1. `SCALP_STOP > SCALP_HARD_STOP` 및 경로별 emergency 순서를 사전 검증한다. 예를 들어 soft 후보가 hard 아래로 내려가 기존 `min/max`가 hard를 더 낮추는 조합은 거부한다. raw→normalized→effective 값과 clamp/override 출처를 기록하고 묵시적 정규화로 잘못된 후보를 고치지 않는다. 서로 목적이 다른 emergency들을 하나의 공통 순서로 재배치하지 않는다.
2. preset -1.4%가 먼저 처리되는 포지션에서 -3% soft/60초까지 도달하지 않는 것은 소비 경로 특성이다. 역할·선행 종료에 의해 도달하지 않은 cell은 실제 유예 표본으로 세지 않는다. 유예 차단 ADD 상태·manual 인계·기존 pending SELL도 같은 census에 사유를 남긴다. 이를 해결하려고 preset/hard를 자동 완화하지 않는다.
3. 보호 가격선의 normal 확인과 fast `protect_profit_pct` 직접 검사를 구분한다. 새 policy는 기존 normal 확인 consumer에 연결하고 fast/normal 공통 안전 중재와 호환시킨다. fast에 가격선 확인을 새로 추가하는 경우 원천/sample/cadence·중복 claim·처리시점 변경을 명시적 behavior delta로 검증하며 기존 direct protect/emergency에 smoothing을 삽입하지 않는다.
4. 보호 가격선 분기가 실행되면 뒤의 `elif strategy == SCALPING`이 건너뛰어질 수 있다. 확인 HOLD가 다른 soft/hard 안전 판단을 삼키는 조합을 검사한다. 현행 값에서의 경로와 새 후보에서의 경로를 각각 재생하고 독립 hard/emergency 우선 평가로 정리한다. 현재 자연 사고가 확인됐다는 뜻은 아니다.
5. 승인된 position pin의 튜닝값 → 동일 scope의 검증된 loaded baseline → 보존된 legacy compatibility의 순서를 명시한다. explicit veto/안전 참조가 최우선이다. env를 바꿔도 포지션의 옛 field·상수·component가 덮어쓰는 경우를 거부하고, `_manual_control_open_loss_stop_context` 같은 보조 consumer도 동일 실효 기준/출처를 읽게 한다. 새 정책은 새 포지션 적용, 기존 pin은 검증된 동일 의미 migration 외 임의 교체 금지다.
6. old path schema에서 폐기 cell을 제거할 때 생존 포지션까지 pin을 잃지 않게 한다. 원 bundle bytes는 보존하고 생존 cell의 값/권한 동등성을 검증한 일회성 successor mapping을 만든다. 미검증 old bundle을 새 live 입력으로 받지는 않으며 퇴역 cell·caller는 복원하지 않는다.
7. exact key 승계는 원 lock hash·key subset·before/after·source/target·권한·rollback을 결속한다. soft/grace/확인값의 승인 범위를 구현하면서 hard/protect floor·manual/enable을 prefix 단위로 열지 않는다. 구현된 selector가 늘 `unclassified_protected`에 막히는 상태를 정책화 완료로 보고하지 않는다. 계약 밖 값 변경은 해당 owner 항목으로 남기고 현행값 carry·독립 구현은 완료한다.

## 6. 경로별 장후 튜닝 연구

### 6.0 시간이 지나도 생성되지 않는 구조 방지

SL0에서 각 조정 키/route/role/market에 대해 **필요 입력 → 현재 값을 쓰는 함수·event·저장 위치 → snapshot 필드 → adapter → 재생/적격 판단 → 정책 cell → loader/분기**를 한 대사표로 작성한다. 원 known-at/단위/native identity/정책 출처, 최소 지원 horizon·cadence, 쓰기·저장·보존 기한, 실행 profile/caller, source/target date도 함께 고정한다. 단순 변수명 검색이나 수동 JSON 주입으로 연결 완료를 증명하지 않는다.

| 구조적 실패 | 선행 보완과 종료 기준 |
| --- | --- |
| 활성 producer가 없거나 제거 대상 관측만 입력을 생산 | 새 시세/모델/연구 worker를 늘리기 전에 생존 Main producer에 최소 receipt를 연결한다. 실제 caller를 통과한 입력이 snapshot·adapter까지 도달해야 한다. 필수 원천이 생기지 않는 상태를 일수/표본 대기로 표시하지 않는다. |
| 보호선이 퇴역 PYRAMID에서만 만들어져 신규 기회가 영구 0 | SL-F8에서 Main 소유의 유효 기존 선과 신규 생성 가능성을 구분한다. 유효 generator가 없다면 `source_gap`에 해당 producer·구조 원인을 명시하고 보호선 생성/승계의 별도 설계 결정을 SL0에서 남긴다. arm 조건·선 산식·단조성·수탁·손절 우선순위·provenance를 갖춘 Main owner 보완안과 회귀 기준을 제시한다. 이를 확인 정책의 암묵적 신규 보호선/주문 권한으로 실행하거나 PYRAMID 복원으로 해결하지 않는다. 기본 정책 계승은 가능하지만 변경 정책 연구 완료로 보고하지 않는다. |
| 매도 완료 행만 모아 유예 후 회복·다른 경로 종료가 누락 | 실제 SELL 여부와 별도로 원 stop touch/유예/회복/보호 확인 기회를 census에 보존한다. 동일 기회의 분모·종료·검열을 연결해 survivor bias를 검사한다. 퇴역 whipsaw 신규 수집을 이 이름으로 복원하지 않는다. |
| 신규 정책에 그 정책의 실제 PID/체결 실적을 선행 요구 | 초기 incumbent 계승·오프라인 후보 평가·canary/후속 자연 수용의 선행조건을 분리한다. 초기 정책 생성에 미래 소비 실적을 요구하는 순환 의존이 없어야 한다. 기존 live 변경의 경제·안전 조건은 유지한다. |
| 모든 종목/시장/cell의 N 충족을 전역 요구 | 적격 scope만 평가하고 미충족 scope는 동일 scope 검증 부모를 계승한다. 전수 census와 전수 후보 선정은 다르다. 임의 시장 통합·표본 기준 완화 없이 부분 적격 정책도 publisher/loader가 처리해야 한다. |
| 정확한 미래 체결/실제 비용을 모든 CF 후보에 요구 | 실제 경로 비용은 실제 성과 요건, CF는 근거 있는 모형·지원 horizon·검열의 별도 요건으로 둔다. 생성될 수 없는 후보 실제 체결 영수증을 요구하지 않고 CF를 실현 이익으로 승격하지 않는다. |
| 삭제 후 필수 path cell·date·hash·schema가 consumer와 불일치 | active path set/validator/publisher/selector/bootstrap를 같은 세대로 이행한다. OFF/retired artifact는 새 필수 목록에서 제거하고 target/date rollover·cache invalidation까지 실제 consumer로 검사한다. |
| 입력 증가/잔존 cache 때문에 매일 timeout·메모리 초과 | 총 모집단을 보존한 shard/재개·후보 block·증분 계산을 정상 caller에 연결한다. 동일 손상/동일 원천을 매일 full replay하지 않고 변경 generation에서 영향 계산만 재개한다. |

상태는 기존 `baseline_carry`, `selected`, `hold_sample`, `source_gap`, `hold_no_edge`를 사용하되 source gap에는 **과거 복구 불가인지, 향후 정상 producer로 생성 가능한지, 미구현 연결인지**를 구별하는 근거와 owner/다음 조치를 남긴다. 필수 생산자가 없는 항목은 수정 전 `hold_sample`로 바꾸지 않는다. 충분하고 유효한 자료를 넣어도 정책 생성에 실패하면 구현 결함이며 경제 후보 부재로 종결하지 않는다.

SL5 수용 시험은 실제 생산/소비 함수를 격리 adapter로 이어 아래 사례를 고정한다. fixture 성공은 구조 검증이며 자연 자료의 수익성 증명이 아니다.

1. 현행값·유효 부모만 있고 경제 표본이 없는 입력 → 정식 `baseline_carry` 발행/검증/lookup 성공. 유효 부모까지 없으면 정확 owner/source gap을 남기며 임의 기준을 합성하지 않는다.
2. 유한한 적격 학습/holdout 입력과 사전 정의된 개선 후보 → 실제 selector가 `selected` 값을 만들고 publisher→bootstrap→pin/lookup이 같은 값을 읽음. loader를 우회해 직접 값을 넣지 않는다.
3. 일부 cell/날짜의 결손·표본 부족·수익성 없음 → 적격 부분만 선정하고 나머지는 해당 부모 유지. 전역 계약 무효만 전체 발행을 막음.
4. source/cost 정정·다른 shard/순서·중단 재개·한도 초과 → 전수 분모와 선택 결과가 독립 기준 계산과 같음. 재생산 후 consumer의 구세대 cache가 남지 않음.
5. 정상 장후 profile의 유효 source가 snapshot→연구→정책→PREOPEN까지 실제 호출 순서로 도달하고, 실패·기한 종료도 한 번의 유한 terminal disposition으로 남음. 후속 소비가 없는데 파일만 생긴 상태를 완료로 보지 않음.

### 6.1 원천·비교 단위

[holding report](../../src/engine/holding_exit_observation_report.py)의 census, [receipt](../../src/engine/sniper_execution_receipts.py), [실제 비용 대사](../../src/engine/lifecycle/broker_cost_reconciliation.py), 기존 quote/path archive를 재사용한다. 별도 실시간 연구 worker·broker/model 호출을 전제하지 않는다. 부족한 보호선 provenance/stop touch/sample은 기존 producer의 다음 자연 원천으로 수집할 위치를 명시한다.

단위는 exact position/buy generation/stop episode다. 반복 tick·fast/normal·retry를 기회로 증식하지 않는다. 모든 Main 종목, PREMARKET/REGULAR/INTEGRATED_AFTERMARKET, fixed/scanner, preset/general, 신규/ADD/익일 보유를 census에 포함한다. 관측 route와 실제 체결 venue, 실제/CF·full/partial·manual·검열을 구분한다.

원 crossing/known-at·정책 pin·source hash·executable bid/depth·보호선/생성 근거·sample history·pending order/잔량·실제 체결·비용 coverage가 입력이다. 비용 결손의 net EV는 null이다. 수동관리 전환은 Main SELL terminal이 아니며 이후 operator 거래 성과를 Main 손절 성과에 합치지 않는다.

**후보가 현재 기준보다 먼저 발동하는 구간도 생산한다.** 현재 -3% soft touch나 SELL 이후 로그만 있으면 -2.5% 후보의 최초 crossing·이후 회복을 재생할 수 없다. 기존 Main holding 원천에서 후보 envelope의 선행 구간·원 quote receipt·가격/시각 sequence를 확보하고, 관측할 수 없는 과거 구간은 검열한다. 유예를 실제 사용한 행만 모으지 않으며 grace=0/선행 hard/manual/다른 exit로 끝난 기회도 원 분모에 남긴다.

window 30초 후보에 현재 20초/60개 메모리 sample을 그대로 쓰지 않는다. SL0에서 동결한 최대 후보 horizon/cadence를 지원하는 bounded 원천을 재사용하고 필요 시 생존 capture의 최소 필드를 보완한다. runtime의 현재 판단 window와 연구용 보존 envelope를 분리하며 원천 확대 비용도 §7 gate에 포함한다. 준비되지 않은 horizon/cell만 제외하고 지원되는 후보·검증 부모 계승을 함께 막지 않는다. 연구용 retention/cache eviction은 미완료 label·pin·source 참조 수명을 알고 처리한다.

### 6.2 후보·권한

| 연구군 | 유한 탐색 설계 | 결과/적용 경계 |
| --- | --- | --- |
| soft 기본 유예 | incumbent + 0/15/30/45/60초를 예비 grid로 제안. 현행값이 다르면 SL0에서 상대 범위/상한 확정 | 하나의 유예 정책. 60초 초과 또는 기존 안전 종료 한도 밖은 자동 후보 제외 |
| 보호 확인 | 한 축씩 시작. 예비 grid: window 10/20/30초, span 4/8/12초, samples 3/5, ratio 0.67/0.80/1.00, buffer 0.50/0.75/1.00% | 부모 포함·유효 조합만 평가. 승인된 보호/지연 한도 안만 selector 자격, 밖은 sensitivity-only |
| soft 기준선 | role별 incumbent와 ±0.25/0.50%p 등 작은 상대폭의 후보. 선행 crossing 원천과 raw→effective safety 순서 검증 | §5.1의 정식 조정 축으로 포함. SL4에서 exact key succession·selector→실효값 계약을 구현하며 해당 범위를 넘는 후보는 sensitivity-only. 원 lock 파일 직접 수정 불가 |
| preset/common hard·emergency·보호 강제선 | 현행 first breach·늦은 감지/매도·manual 인계 재현과 tail 민감도 | hard safety 연구. 자동 완화·수동관리 해제·신규 SELL 권한 없음 |
| AI VETO | §5.1의 기존 path policy 10개 필드·global cap/worsen을 경로별 검증 | 기존 owner에서 SL-F11의 경제 비교/변경 selector 공백을 보완. 후보를 만든다는 사실과 현재 baseline-only 발행을 구분 |
| stagnation 관측·일반 익절 trailing | 관측 임계치·기존 단일 익절 owner와 상호작용 검증 | stagnation을 독립 SELL로 부활시키지 않음. trailing/delay 기존 owner와 중복 후보/발행 금지 |

예비 grid는 운영값 권고가 아니다. SL0에서 scope별 후보 수/계산 예산을 고정하고 결과를 보고 늘리지 않는다. 한 route·한 축씩 시작하고 제한된 상호작용 시험도 holdout 전에 동결한다. 강제 안전·원 lock 권한 밖은 `allowed_runtime_apply=false`와 부족 authority를 기록한다.

### 6.3 인과 재생·선정

1. 공통 순수 판단기로 sample eviction, first crossing, 단일 유예, manual/SELL claim·잔량·비상 우선권까지 재생한다. entry/ADD/익절 경로는 후보 간 고정한다. 후보 때문에 이후 경로가 달라져 식별할 수 없으면 검열한다.
2. 후보 crossing 이전 원 투표만 사용한다. 호출 시점/입력이 달라진 가상 AI 응답, 실제 매도 후 없는 가격·체결/depth를 합성하지 않는다. partial/residual·미관측 비용은 별도 상태다.
3. 9/29 이후 적격 source day의 시간순 train→후행 holdout을 고정한다. 같은 position·중첩 stop episode/후행 label이 양쪽에 들어가지 않게 한다. purge/embargo는 horizon·최대 유예·포지션 중첩의 실제 필요 범위로 계산해 manifest에 고정한다. shard별 split/승자 선정 금지.
4. train에서 한 후보를 정하고 holdout에서 고정 검증한다. primary는 동일 적격 분모의 cost-adjusted paired EV/net KRW, win rate는 진단이다. EV는 Plan Rebase의 명명된 지표 중 사용한 가중/품질 정의를 기록하고 단순 수익률 합계와 구분한다. 실제 COMPLETED+valid exact-cost, CF·partial·censored·manual을 분리한다. CF의 체결/비용 가정·모형 오차는 별도 기록하고 실제 비용/수익으로 표시하지 않는다. 손절 후 반등률이나 CF 비교만으로 real execution/broker 권한을 승인하지 않는다.
5. tail loss/MAE, 미청산 노출시간·잔량, 감지→disposition/submit, 추가 손실/missed upside, turnover/비용, coverage·검열 비율을 비교한다. 실행 스트레스는 frozen source가 지원하는 범위만 평가한다. 안전 breach·중복 주문·보호 지연을 평균 EV로 상쇄하지 않는다.
6. sample floor·최소 개선폭·불확실성/검열 한도·일일 변화폭은 기존 활성 family 계약을 먼저 확인하고 신규 정책은 SL0에서 source/검정력·tail을 근거로 동결한다. 미정이면 challenger 발행 불가다. 공통 20건/1%를 임의 부과하거나 부모 계승·결함 수리에 경제 floor를 적용하지 않는다.
7. 부족하면 `hold_sample/source_gap`, 유효 비교에서 개선 없음이면 `hold_no_edge`로 부모 유지. 다른 시장 값을 빌리지 않는다. 초기 정책화는 완료할 수 있으며 실제 경제 개선은 별도 미확인으로 남긴다.

### 6.4 정식 producer→consumer

[정상 postclose wrapper](../../deploy/run_threshold_cycle_postclose.sh)의 `MONITOR_SNAPSHOT_PROFILE=postclose_exit` 호출 → [log archive](../../src/engine/log_archive_service.py)의 `save_monitor_snapshots_for_date_with_profile` → holding report source adapter → `scalping` stop replay → `automation` bounded selector/정책 producer → [runtime summary](../../src/engine/runtime_approval_summary.py)·[checklist generator](../../src/engine/build_next_stage2_checklist.py) → [summary handoff](../../src/engine/automation/postclose_summary_handoff.py)·strict/controller → [bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py)·[PREOPEN](../../src/engine/automation/next_preopen_readiness.py) → preload/pin으로 연결한다. caller report 자체를 입력으로 다시 요구하는 순환을 만들지 않는다.

publisher/validator/loader·retired-key scrub·active family requirement·운영문서/체크리스트를 같은 구현 변경으로 연결한다. 현재 없는 stop selector나 cron을 설치된 것으로 가정하지 않는다. 현재 dispatcher에는 holding/stop stage가 없으므로 정상 wrapper의 exit snapshot 이후 실행하는 bounded substep을 등록하고 같은 dispatcher에 stage/산출물/terminal receipt를 연결한다. 별도 cron·서비스는 추가하지 않는다. 산출물은 전수 census·scope별 적격/제외, 후보/부모 값·source/cost/code/policy hash, 변경 key authority·성능 gate·target를 포함한다.

경제값 변경은 기존 holding/exit canary와 충돌하지 않는 정확 scope·한 축으로 제한한다. 새 이름으로 whipsaw 추가 유예를 재등록하지 않는다. source/cost revision은 영향 report/census/projection/selection/manifest를 새 세대로 봉인한다. 원본을 수정하거나 자연 표본용 주문을 생성하지 않는다.

### 6.5 생산자·소비자 결손과 실제 연결 작업

이번 조회에서는 stop 전용 정책 producer/loader가 아직 없고, 보호 확인 event에는 `allowed_runtime_apply=false`인 관측 계약만 있다. 이를 연구 또는 guard 자체의 퇴역으로 해석하지 않는다. **관측 권한과 새 정책 변경 receipt는 서로 다른 계약**으로 유지한다.

| 구간 / 현재 파일·함수 | 확인된 공백·보완 | 통과 증거 |
| --- | --- | --- |
| handler/receipt: soft touch·보호 sample·초기/ADD pin | 현재 `holding_price_samples` 메모리와 일부 guard 로그만으로 후보별 선행 경로·원 가격/시각·pin의 durable 연결은 보장되지 않음 | §6.1 필드의 actual capture→archive 대사; 원 touch/recovery/ADD/claim·retention label을 같은 position/buy generation으로 복원 |
| [registry](../../src/utils/threshold_cycle_registry.py)→[backfill](../../src/engine/backfill_threshold_cycle_events.py)→[source audit](../../src/engine/observation_source_quality_audit.py) | 기존 grace/보호 stage 등록만 존재. 신규 source field/schema·회복/종료·탈락 분모·삭제 family/historical disposition은 동시 이행 필요 | raw→written→partition/census의 ID·행수·hash 대사. 누락을 unknown family로 조용히 버리지 않고 과거 whipsaw 행은 별도 귀속 |
| log archive·holding report·cost/projection | report의 post-sell rebound 및 strict completed vote 모집단을 전체 stop opportunity 모집단으로 재사용하면 회복/open/manual 행이 사라짐 | source opportunity census와 실제 COMPLETED cost cohort 분리. 동일 `as_of`·projection/cost/source revision으로 sealed snapshot 생성 |
| stop replay/selector: 새 역할 모듈 | 현재 없음. report 상위 함수가 다시 자신을 호출하거나 직접 source가 없는데 기존 report의 성공만 넘기면 안 됨 | `src/engine/scalping` 순수 source/replay/policy, `src/engine/automation` bounded producer에서 §6.0 성공/hold/부분 결손/정정 시험 |
| AI vote replay→`create_bundle`→runtime | 기존 replay는 `cost_after_paired_ev_krw=None`, publisher는 항상 baseline. max-defer 후보의 손절 시간·worsen·safety 실제 경로 비교도 별도 필요 | 기존 owner에 식별 가능한 path/경제 비교와 train/holdout selector 추가. 후보 인과성 없으면 명시적으로 baseline-only. 생성기 고정값을 제거하지 않은 상태에서 표본 축적만 기다리지 않음 |
| [operator succession](../../src/engine/automation/operator_policy_succession.py)·key owner | `POLICY_KEYS`에 새 stop family가 없음. SCALP_STOP 등의 준비 값은 persistent operator lock 소유. 새 bundle이 발행돼도 old env/pin 우선이면 무효 | exact key subset·원 lock/source SHA·변경값·target·승계 receipt 검증; 원 lock 보존. 새 consumer가 최종 실효값을 읽고 안전/수동 veto는 유지 |
| wrapper/dispatcher→summary/checklist→strict/controller | stop stage·source-path·output·code fingerprint·필수 receipt가 없음. 현재 vote bundle은 summary 생성 중 발행됨 | source date/다음 거래일 target로 stop substep·terminal/status·source hash를 등록. summary와 strict는 검증된 receipt를 소비하고 checker 호출만으로 연구/재발행하지 않음. shared pending/timeout 처리와 단일 owner 확인 |
| bootstrap/PREOPEN→runtime lookup·DB/receipt 복구 | 새 정책 env/manifest receipt·validator·pin durable 복구가 없음. 일부 preset grace/mode는 env parser 자체가 없으며 오래된 position field가 우선할 수 있음 | 아래 제안 handoff의 file/byte SHA/active date→typed map→실제 normal/fast 및 보조 consumer→복원 pin 일치. 구세대 cache·부분 전환·주말/익일·rollback 실패 주입 |

제안 artifact는 source `main_stop_source_v1`, research `main_stop_research_v1`, 정책 `main_stop_confirmation_policy_v1`이며 아직 설치된 계약이 아니다. 정책 위치는 `data/threshold_cycle/main_stop_confirmation/main_stop_confirmation_policy_<TARGET>.json`, bootstrap 전달 키는 `KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_FILE`, `KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_SHA256`, `KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_ACTIVE_DATE`로 정한다. source/평가 artifact는 source date와 run generation을, policy/receipt는 target date와 승인 parent를 결속한다. 실제 serializer의 byte SHA와 canonical semantic SHA는 구별하고 validator·summary·loader가 같은 뜻으로 읽는다.

발행은 bounded leaf 준비→모든 consumer 검증→committed generation 전환 순서다. bootstrap env/manifest·prepared index·selector/release·policy pointer의 전환/복원을 한 목록으로 관리하며 정책만 먼저 바꾸지 않는다. active pin이 참조하는 이전 generation은 보존한다. 신규 stop family의 정상 무표본·부모 계승·권한 미충족을 적절한 terminal receipt로 기록하고 OFF/retired artifact를 완료 필수물로 다시 요구하지 않는다.

연구 입력은 당시 실제 적용된 source-date stop/vote pin을 사용하며 같은 장후 작업이 만들 다음 target-date 후보를 입력의 선행조건으로 요구하지 않는다. stop·vote·일반 trailing 후보는 공통 holding/exit stage의 한 축 변경 중재를 거친다. 각 생성기가 서로의 미래 산출물을 기다리거나 여러 family의 독립 승자를 동시에 적용하지 않으며, 승계만 하는 나머지 family는 검증 부모를 유지한다.

AI vote 변경 policy는 관측된 같은 입력/시점의 투표 재집계 범위만 사용한다. 후보가 모델 호출·입력·known-at를 바꾸면 가상 응답을 만들지 않는다. 가격/손절 시간 재생과 fill/cost 모델의 식별 가능 구간·실제 성과·CF를 분리한다. 기존 `create_bundle`의 기본값 강제 검사, replay의 baseline hash 비교, consumer의 path cap을 함께 바꾸지 않으면 changed-policy가 도달할 수 없으므로 세 지점을 동일한 versioned migration 시험으로 닫는다.

## 7. 성능 개선·저하 방지

기존 trailing/delay 잔여계획 W4의 workload·합산 예산을 재사용한다. 손절용 무제한 cache/thread/temp budget을 추가하지 않는다. SL0에서 코드 SHA·동일 입력/host·보유 수/quote cadence·cap·동시 job·지연/RSS/disk 한도를 수치로 봉인한다.

현재 Claim은 process-local이므로 family별 64MiB 설정만으로 host 합산 제한을 충족했다고 보지 않는다. trailing/delay에서 보완 중인 공통 heavy-job admission을 정상 장후 caller·직접 CLI·profile 경로에 재사용한다. 예약 identity/PID/start generation, writer→slot lock 순서, 유한 대기·중단 반환을 공유하고 새 손절 job도 전체 프로세스/RSS·temp·old/new 출력 peak 측정에 포함한다. 공통 admission이 아직 검증되지 않았다면 SL5/SL6에서 먼저 통합·검증하며 손절 전용 우회 경로를 만들지 않는다.

| 개선 | 구체 변경 | 보존/실패 기준 |
| --- | --- | --- |
| 폐기 계산 | score context·OFF expert/dynamic/whipsaw·전용 log dict·source-only arm·state 갱신을 caller부터 제거 | 생존 OFI/시세 source·필수 거래 receipt 누락 0 |
| 정책/입력 공유 | PREOPEN preload+pin, 같은 quote/position generation의 immutable 평가 입력 공유 | hot path 정책 파일 I/O·전체 JSON/hash 0. 다른 세대·stale 결과 cache 사용 금지 |
| 보호 sample | 유한 ring/deque·receipt 중복 제거·sample/유효 시간창 변경 때만 bounded 중앙값/비율 계산·시간창 eviction | 복사/정렬 감소 실측. 가격이 같아도 시간 만료/회복/정책·평단 세대 변경은 재평가. sampling으로 breach·coverage를 숨기지 않음 |
| claim/등록/관측 | lock은 identity/state 전이만; 등록/fsync/집계는 기존 bounded 경로 | mandatory durability 보존. 등록 실패를 주문 가능 상태로 되돌리거나 queue 무제한 확대 금지 |
| 장후 재사용 | raw→feature→replay→cost/selection 의존 분리, 후보 block·증분 재생 | source/algorithm/pin/cost/cutoff 영향 재계산. no-change full JSON decode 0 목표, 필수 byte 검증 보존 |
| 전수 대용량 | 공통 spool/shard/checkpoint·전역 dedup/split/census | 기존 2GiB job/64MiB resident 등 합산 한도를 SL0 재확인. 초과 모집단 절단 금지 |
| 발행·검증·소비 | 정책에는 고정 scope cell·요약·leaf hash 참조만 두고 raw/후보 경로는 별도 bounded artifact로 보관. 동일 봉인 입력의 파싱/정규화 결과를 세대별 재사용 | strict가 필요한 byte 검증을 생략하지 않음. serializer/validator/loader의 반복 full decode와 시장별 전체 정책 복제를 제거 |
| 준비·runtime 전환 | PREOPEN에서 준비한 불변 lookup을 세대 단위로 전달하고 position은 pin 참조 사용. source/target 변경 시 한 번만 원자적 전환 | 장중 매 tick 디스크 감시·loader warm-up 금지. 이전 map의 활성 pin 참조와 메모리 회수 한도를 함께 검사 |

[runtime performance](../../src/engine/monitoring/runtime_performance.py)와 [exit monitor](../../src/engine/scalping/exit_safety_monitor.py)로 baseline/후보 각 3회부터 교대 측정한다. N·p50/p95/p99/max·변동폭, 보호 평가 간격, WS wake→평가→claim/disposition→격리 submit, Main/PASS/due 만료·lock wait/hold, CPU·총 peak RSS·I/O·queue/thread를 기록한다. 250ms는 poll 설정이지 latency 보장이 아니다.

복수 보유 정상/burst, fast/normal 동시 breach, ADD/partial SELL, manual 등록 실패/지연, 느린 writer·queue full, restart/reload·시장 변경, trailing/delay heavy job 동시 실행, cold/warm/source-delta/cost-only·중단 재개를 포함한다. model/broker adapter는 격리한다. 성공 작업의 동일 분모를 비교하며 예전 상한 초과 실패 시간을 성공 baseline으로 삼지 않는다.

생산·소비 구간별로 capture/enqueue·snapshot·scan/feature·replay/selector·serialize/publish·strict/handoff·bootstrap/PREOPEN·startup/pin/lookup의 실제 호출 수·decode/hash/bytes·시간·peak 자원을 계측한다. 최초 end-to-end 실행은 전체 비용을, 무변경 재실행은 재사용 효과를, 원천/비용 증분은 영향 범위의 재계산 비용을 각각 비교한다. 생성 시간을 줄인 대신 strict·startup·hot path에 같은 작업을 떠넘기는 변경은 개선으로 인정하지 않는다. 보존 기간 증가와 candidate/scope 증가에서도 처리량·재개·소비 시간이 유한한지 확인하며 장후 기한을 초과하면 새 후보 발행을 멈추고 유효 부모 계승 상태와 재개 위치를 남긴다. 같은 날 자동으로 예산을 늘리거나 무한 재시도하지 않는다.

gate는 승인된 결함 delta 외 의미 차이 0, 설명되지 않은 누락/중복·새 deadline 만료 0, hard/protect/emergency 처리 tail·Main p95/p99 비악화, 합산 자원 한도 준수다. 개선은 호출·할당/bytes 감소와 CPU/시간 감소로 입증한다. 평균 CPU만으로 보호 지연 악화를 통과시키지 않는다. 작은 N/잡음은 `performance_unresolved`다. 실패 원인을 보완한 뒤 영향 workload만 재측정한다.

## 8. 회귀·반복 리뷰

구현→producer/consumer·권한 self-review→보완→재리뷰→표적 검증을 반복한다. SL-F별 evidence/owner/next action/closure test를 기록하고 코드상 차이·합성 재현·자연 결과를 구분한다.

| 검증군 | 반례 / 우선 기존 시험 |
| --- | --- |
| 삭제·부활 | imports/callers/env/prompt/cell/신규 event/추천/필수 artifact 0; stale env/old policy 부활 불가. [retirement](../../src/tests/test_main_only_retirement.py), [constants](../../src/tests/test_constants.py), [succession](../../src/tests/test_operator_policy_succession.py) |
| fast/normal·manual | 같은 quote/pin, 비상 미도달/도달, 신규 인계/기존 manual/등록 실패, concurrent claim/pending·잔량. [exit monitor](../../src/tests/test_scalp_exit_safety_monitor.py), [manual](../../src/tests/test_manual_control_exclusion.py), [handler](../../src/tests/test_sniper_scale_in.py) |
| 정책/시간/sample | baseline 동등, 만료/오염/scope·clock, 회복/재터치, window/span/cap, stale/중복, ADD/익일/restart. 새 시험은 `src/tests` |
| 실효 키·도달성 | raw soft 변경이 hard를 낮추는 반례, preset 선행/ADD 유예 0, 보호 확인 HOLD 뒤 hard 평가, normal/fast 보호 구분·preset grace, env/parser/stock pin 우선순위, 양수/음수·0/None/bool/NaN, §5.1 literal/상한 참조 |
| 정책 생성 구조 | 충분한 fixture에서 AI vote 기본값 강제 발행을 벗어나 승인 후보가 loader에 도달, 현재 threshold 이전 crossing·30초 window 원천, cell 일부 적격, old schema 생존 pin 이행, 삭제 timer 잔존 0 |
| 생존 AI/공유 | no score, PASS/VETO/INSUFFICIENT·cell migration·review cadence, stagnation 관측·활성 OFI/rebound. [votes](../../src/tests/test_holding_exit_vote.py), [replay](../../src/tests/test_holding_path_vote_replay.py), [stagnation](../../src/tests/test_profit_stagnation.py), [smoothing](../../src/tests/test_smoothing_source_only_path_journal.py) |
| 장후·경제 | 독립 손계산, source-gap/검열/partial/manual/실제 비용, split 누수, 부모 유지/allowlist, revision/shard 동등. [holding report](../../src/tests/test_holding_exit_observation_report.py), [Sentinel](../../src/tests/test_holding_exit_sentinel.py) |
| 생성 가능성·전체 비용 | §6.0의 실제 producer→loader 성공·부분 결손·source/cost 정정·재개 시험, 미래 실적/전역 표본의 순환 gate 부재, §7 구간별·end-to-end 성능과 장후 기한 종료 |
| 인계 | historical/retired checkpoint·source→summary→strict→bootstrap→pin 세대 일치와 실패 주입. [backfill](../../src/tests/test_backfill_threshold_cycle_events.py), [strict](../../src/tests/test_verify_threshold_cycle_postclose_chain.py), [wrappers](../../src/tests/test_threshold_cycle_wrappers.py) |

Python은 영향 pytest·compile, wrapper는 `bash -n`·contract tests, 모든 변경은 diff 검사로 닫는다. 10/10 문서 검증과 10/11 코드/회귀/성능 검증은 별도 근거로 기록한다. 향후 Kiwoom request/parser/FID/auth/order/continuation을 수정하면 변경 전에 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)의 upstream SHA·관련 파일·조회시각·protocol 대조를 기록한다. 이번 계획 작성으로 그 gate를 수행했다고 표시하지 않는다.

## 9. 운영 인계·완료 조건

후속 운영 변경은 해당 실행 요청/owner가 허용한 범위에서 수행한다. 10/11 요청은 계획 실행·반복 코드리뷰이며 봉인된 10/12 checklist/PREOPEN과 operator 파일은 보존했다. path set·정책·code hash 변경 시 기존 prepared PASS를 재사용하지 않고 정식 successor와 full-contract 검증을 수행한다.

- 삭제 완료: 전수 inventory의 실행·신규 수집/추천/튜닝 권한 0, 허용한 역사 독자/denylist만 잔존. rollback/env로 복구 불가.
- 런타임 완료: role/quote/pin·수동 인계·안전 우선권·동시성/restart 회귀와 성능 gate, 승인 delta, 미해결 구현 finding 0.
- 정책화 완료: 현행 유예·보호값 계승과 후보 생성/검증/selector/loader/PREOPEN/pin·consumer migration 연결. 후보 0은 부모 유지로 완료 가능하지만 미구현 consumer는 완료가 아니다. 유효 입력의 생성 성공과 자연 표본의 실제 적격성은 별도로 증명하며 도달 불가능한 producer를 장기 표본 대기로 넘기지 않는다.
- 경제 선정: forward train/holdout·실제 비용/tail/coverage·stage/lock 권한을 통과한 범위만 변경. hard safety/수동 veto는 연구 결과만으로 변경하지 않는다.
- 운영 준비: 허용된 발행 후 affected source→tower/checklist→strict `--require-summary-handoff`→controller/finalization, 정확 날짜 PREOPEN/release 같은 세대. 실패 후 옛 PASS 재사용 금지.
- 자연 수용: 적용일 `DirectFamilyPreopenPolicyHandoff`에 새 release/policy/pin 검사를 인계한다. 실제 PID·관측 disposition·terminal/비용을 별도 확인하며 미래 시점을 현재 성공/구현 gate로 쓰지 않는다.

차단마다 owner artifact·영향 route/scope·증거·다음 수정/자료/권한·종료 시험을 남긴다. 복구 불가 source는 해당 경제 평가에서 제외하고 독립 수리를 계속한다. 보호/비상 지연·custody 침범·중복 주문·stale/conflict 허용·unbounded 작업은 적용 중단 사유다. 복원 대상도 새 퇴역 계약을 만족해야 하며 이전 release 전체 복원으로 폐기 실행을 되살리지 않는다.

## 10. 문서 검토 기록

caller·설정·장후 대조로 stagnation 관측 보존, whipsaw 추천/수집 잔여, fast 수동 인계, path cell/hash migration, sample cap·보호선 provenance를 반영했다. 후속 지시의 60초 유예·보호 트레일링 정책화를 SL4–SL5와 §5–§7의 실제 producer/consumer·성능 수용으로 연결했다. 동시에 진행 중인 다른 trailing/delay 구현 변경은 이 문서의 완료 근거에 포함하지 않는다.

추가 지시를 반영해 §6.0에 시간이 지나도 풀리지 않는 생산자/경로 부재·생성/소비 순환·전역 표본 gate·schema/기한 문제와 실제 producer→loader 성공 시험을 추가했다. §7에는 capture부터 strict/PREOPEN/pin까지 구간별 비용과 전체 비용, 증분 재사용·자원 합산·장후 기한 검증을 연결했다. 신규 보호선 생성이 필요하면 독립 설계/권한 결정을 명시하며 기본 확인 정책에서 암묵적으로 실행하지 않는다.

2026-10-10 후속 재점검은 handler의 실제 분기와 rule/상수, receipt의 초기/ADD pin, prepared key owner, vote replay/publisher, registry/audit, 정상 postclose wrapper/profile, summary/dispatcher/bootstrap까지 대조했다. 17개 기준/임계치 묶음을 §5.1에 분류하고 SL-F10–SL-F15를 보완했다. 소프트 기준선의 정식 조정 축 누락, effective cap/선행 경로, 기본값만 생성하는 vote publisher, 관측 ON의 실매도 오해, defensive unfilled no-op 잔여, stop 전용 handoff 부재가 주요 수정이다. §6.5에 producer/consumer별 이행과 실제 전달 키/세대 계약을 추가했다.

후속 문서 재리뷰·검증: 계획/오늘 checklist의 로컬 링크 62개·anchor 결손 0, 17개 기준/임계치 묶음·SL-F1–SL-F15의 보완/종료 조건 대사, fence/후행 공백·`git diff --check` PASS. print-only parser는 23건, 손절 현재 owner 1건이다. 10/12 checklist·Plan Rebase·runtime selector의 조회 전후 SHA는 동일하다. 검토한 문서 범위의 미해결 finding은 0이며 SL-F1–SL-F15의 실제 구현/재현은 후속 작업이다. 문서 전용 작업이므로 pytest·성능 benchmark·provider 호출·장후 재생·배포·기동은 수행하지 않았다. 이 결과는 구현·정책 선정·자연 손절 성과 확인이 아니다.

## 11. 10/11 구현 인계

[10/11 구현·반복 리뷰](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)를 현재 구현 근거로 사용한다. 기존 wrapper의 verified postclose-exit 뒤 native `main_stop_confirmation` stage를 source10/12부터 연결했으며, 이전 날짜 stage 부재는 장애가 아니다. 새 cron·실시간 연구 worker·provider 호출은 없다. 원장 위치 참조 분할·position checkpoint·무변경/비용 정정 재사용, 2GiB durable/2GiB temporary 예산 및 기존 stage4시간 상한/재개 receipt를 적용했다. 기본값 계승은 표본 부족과 분리하며 변경 후보에는 원 owner·exact key/자료/성능 계약을 요구한다. SL-F8 보호선 provenance 부재와 SL-F11 baseline-only를 원천 결손/구현 잔여로 구분했다. §7 전체 성능과 §9 운영·자연 수용을 축소하거나 완료 처리하지 않았다.


### 10/11 후속 승인 배포

[구현 리뷰 §7–§8](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)의 추가 지연 보완·1057/187개 회귀(중복 포함)와 실제 인계 검증 후 `main-stop-semantic-20261011-v1` / `91edc62844180be6a279e761f32996c3c76ce72e`를 선택했다. source10/8의 정식 finalization은11:33:05 KST DONE이며 target10/12 준비는 전체 계약 PASS다. 기존 임계값·수량·EOD를 보존했고 신규 stop 장후 stage는source10/12부터 연결한다. 실제 PID/자연 청산·경제성과 전체 Main/동시 연구 성능은 이 배포 영수증으로 완료 처리하지 않는다.
