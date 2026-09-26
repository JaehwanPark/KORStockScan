# 보유 중 AI 경로별 PASS/VETO 완전 전환·장후 튜닝 계획 (2026-09-25)

## 목표와 경계

보유 중 AI의 **청산·추가매수에 쓰이는 숫자 점수, 점수 이력·기울기·prior·평활·score50 fallback과 HOLD/TRIM/EXIT 결론을 활성 결정 경로에서 완전히 제거**한다. 모델의 각 `PASS`/`VETO` 응답은 **한 표**일 뿐이며, 어느 경로에서도 단일 표가 AI 판정을 확정하지 못한다. 일정 시간 동안 순서대로 모인 서로 다른 유효 스냅샷의 표를 경로별로 집계한 결과만 `PASS`/`VETO`/`INSUFFICIENT`가 된다. `EXIT_TRAILING_TP.PASS`는 성립한 익절 신호의 진행 허용이고 `ADD_REBOUND.PASS`는 성립한 반등 추가매수 후보의 진행 허용이다. 두 집계는 권한·분모·안전 기본값이 다르며 서로 대신 읽거나 합산할 수 없다. PASS만으로 청산 신호·추가매수 후보·주문을 만들지 않는다. 첫 신호에는 그 이전에 확정된 같은 경로의 표만 쓴다.

이 문서의 구현 목표는 **구 점수 AI와 신호 시점 flow AI를 새 투표 AI로 완전히 교체**하는 것이다. 구 AI와 새 AI의 병행 호출·이중 관측·시장별 순차 전환은 목표 경로에서 제외한다. 현재 구현된 관측용 투표는 아직 실거래 소비자가 없고, 주기적 구 점수 호출 뒤 별도로 예약되므로 완전 전환 상태가 아니다. 기존 holding AI의 점수·HOLD/TRIM/EXIT 결론은 정합성이 검증된 교사 라벨이나 새 투표의 prior로 사용하지 않는다. 새 프롬프트는 당시 이용 가능한 실제 시세·체결·포지션 원천으로 새로 설계한다.

강제 손절, emergency, broker/account/order/quantity/cooldown, stale/conflict 및 기존 보호선은 투표로 무력화하지 않는다. 실제 AVG_DOWN은 기계식 Main 반등 신호, **그 경로의 복수 독립 표로 성립한 ADD PASS 집계**, 기존 주문·수량·원천 guard가 모두 성립해야만 허용한다. 단일 ADD PASS, 표 부재, 정족수 미달, VETO 집계는 모두 추가매수를 막고 이유를 남긴다. 반대로 청산 표가 부족하면 기계식 청산 신호를 진행한다. 기존 단일 holding AI 검토 슬롯을 사용해 한 입력 스냅샷당 공급자 호출 최대 1회 안에서 활성 경로별 **각 한 표**를 얻고, 여러 검토 주기에 걸쳐 축적한다. 별도 추가매수 AI 호출은 만들지 않는다. 코드 완결, 테스트 데이터의 기능·성능·결과 검증, 배포, 실제 PID 소비, 자연 체결 성과는 각각 별도 증거로 판단한다.

## 현재 이행 대상

| 현재 생산자·소비자 | 이행 작업 |
| --- | --- |
| `ai_engine_openai.evaluate_scalping_holding_score`, `sniper_state_handlers`의 주기적 보유 AI 호출·평활·prior | 기존 주기·가격변화 트리거와 공유 symbol budget의 **같은 호출 슬롯**에서 경로별 PASS/VETO 묶음을 1회 호출로 받는다. 구 점수·prior를 입력/결정에서 제거한다. 캐시 응답은 새 표로 세지 않는다. |
| 익절 trailing | 기계식 arm·강약 분류·되돌림 첫 crossing은 그대로 만든다. `EXIT_TRAILING_TP` 표만 집계한다. 기존 첫 crossing·고점·호가 원천을 지우지 않는다. |
| 일반 soft stop·recovery·OPEN_RECLAIM 조기 정리·`kiwoom_sniper_v2`의 청산 점수 소비 | 실제 live 소비와 hard/soft 성격을 census로 확정하고 **각 활성 soft 경로에 서로 다른 path ID**를 부여한다. 점수 임계치·score50·AI 단독 청산을 제거한다. hard/protect/emergency와 퇴역 adapter에는 신규 VETO 권한을 주지 않는다. |
| 실제 `ADD_REBOUND` AVG_DOWN | `evaluate_main_rebound_entry`는 이름과 달리 공급자 호출 없는 기계식 후보 생산자다. 그 뒤의 유효 holding 점수 `>50` 거부 조건을 **동일 경로의 ADD PASS 집계**로 교체한다. `can_consider_scale_in`과 실행 직전 주문·수량·원천 guard는 유지한다. EXIT PASS는 이 경로를 허용하지 못한다. |
| 첫 접촉 AVG_DOWN·구 점수 재호출, PYRAMID, post-probe | 첫 접촉 평가 함수는 활성 호출부가 없고 stop-line AVG_DOWN 실행은 no-op이다. PYRAMID 실주문과 기존 보정 family는 퇴역했다. 활성 경로로 복구하지 않는다. post-probe 점수/행동 진단은 별도 source-only 상태로 분류하고 live ADD 표와 섞지 않는다. |
| 신호 시점 `holding_flow` AI·OFI/시세 보정 | 동기식 모델 호출과 HOLD/TRIM/EXIT 결론 소비를 제거한다. 유효한 flow/OFI·호가와 출처는 신호 전 단일 투표의 입력으로 옮기고 신호 시점에는 저장된 표만 읽는다. |
| 현재 `_schedule_holding_exit_vote_observation` 및 관측 flag | 독립 호출 예약·관측 전용 권한·`KORSTOCKSCAN_HOLDING_EXIT_VOTE_OBSERVE_ENABLED`를 제거하고 기존 주기 슬롯의 유일한 다중 경로 생산자/원장으로 통합한다. 동일 검토 주기에 두 번째 AI 공급자 요청은 없다. |
| `evaluate_condition_exit` adapter, retired Opening Rotation·overnight, probe/sim·오프라인 replay·보고서 | live 호출 여부와 결정 권한을 명시한다. adapter가 다시 쓰이면 같은 청산 허용 의미만 사용한다. 퇴역·오프라인 경로에는 live 투표 권한을 부여하지 않고, 과거 점수를 PASS/VETO로 허위 변환하지 않는다. |

## 호출 목적과 결정 권한

활성 보유 AI 모델 호출은 입력 스냅샷마다 하나지만 판정 목적은 **경로별로 분리**한다. 요청에는 그 시점에 적격한 `path_id` 집합을 명시하고, 응답은 요청한 각 경로에 대해 독립된 `verdict`와 `conviction`을 반환한다. 이는 한 경로당 **이번 주기의 표 하나**이며 즉시 판정이 아니다. 누락·중복·알 수 없는 path ID, 경로 목적과 어긋난 이유 코드 또는 서로 다른 경로의 표 재사용은 해당 경로 `INSUFFICIENT`로 격리한다. 한 호출의 여러 표도 경로별 원장에 따로 저장한다. 한 경로의 PASS/VETO 수·강도·최신성은 다른 경로에 합산하지 않는다. 경로별 프롬프트 절과 정책 버전도 별도 관리하며, 공유 호출의 프롬프트 변경이 다른 경로 응답에 미치는 영향은 함께 회귀 검증한다.

| `path_id` | PASS의 의미 | VETO의 의미 | `INSUFFICIENT` 기본값 |
| --- | --- | --- | --- |
| `EXIT_TRAILING_TP` | 해당 trailing crossing의 기존 SELL 절차 허용 | 안전 상한 안에서 그 crossing 청산 보류 | 기존 SELL 진행 |
| `EXIT_SOFT_STOP` 및 census로 확인된 각 soft 청산 path ID | **해당** 손절 신호의 기존 SELL 절차 허용 | 해당 경로의 기존 최대 보류·가격 악화 한도 안에서 보류 | 기존 SELL 진행 |
| `ADD_REBOUND` | **해당** 기계식 Main 반등 후보가 주문 guard로 진행하는 것을 허용 | 그 추가매수 후보 차단 | ADD 차단 |

`EXIT_TRAILING_TP.PASS`와 `ADD_REBOUND.PASS`가 동시에 있어도 청산 신호가 이미 성립했거나 SELL이 진행 중이면 EXIT/안전 owner가 우선하며 ADD는 차단한다. PASS는 결코 주문 제출 자체의 권한이 아니다. 점수만으로 생성되던 독립 EXIT는 기계식 신호가 없으면 폐기하고, 숫자 점수의 상승·저하 이력으로 만들던 ADD 후보 상태도 폐기한다. hard/protect/emergency는 표와 무관하게 실행된다.

신호별 소비자는 별도로 닫는다. Trailing 익절과 일반 soft stop은 자기 경로의 유효 투표만 읽고 기존 기계식 신호·시장/호가·최대 보류 계약을 유지한다. ADD는 자기 경로 PASS가 유효해도 Main 반등 신호·일반 scale-in gate·실행 직전 safety를 모두 통과해야 한다. 보유 중에는 활성 청산·추가매수 경로의 표를 신호 전부터 축적하며, 경로가 아직 가능하지 않은 시장·상태에서는 그 경로 표를 만들지 않는다. 신호 시점 추가 모델 호출과 첫 신호 뒤 응답의 소급 적용은 없다.

## 투표 원장과 원천 계약

1. 포지션의 실제 BUY 체결 ID, 종목, 시장유형(`PREMARKET`, `REGULAR`, `INTEGRATED_AFTERMARKET`), `path_id`·그 경로의 명시적 PASS 의미·경로 정책 버전, AI 입력 스냅샷 hash, 모델·경로별 프롬프트 버전, 호출·응답 시각, 시세 route/epoch/sequence, 판정과 근거 코드를 한 표에 저장한다. 포지션·시장·세션·path ID·모델/프롬프트 버전이 바뀌면 이전 표를 집계하지 않는다.
2. 투표는 새롭고 유효한 시세·체결·호가 입력에 결속한다. 동일 응답/스냅샷 재사용, out-of-order 응답, 중복 호출, stale·route conflict, 파싱 오류, timeout, fallback은 `INSUFFICIENT`로 격리한다. `INSUFFICIENT`가 PASS나 VETO의 수를 늘리지 않는다. 원장 저장 실패·손상·재시작/부분 체결 identity 불일치도 숨기지 않고 보류 권한을 주지 않는다.
3. English ASCII 출력은 요청된 각 `path_id`별 `verdict`, `conviction`(`FIRM`/`TENTATIVE`), 해당 경로의 `reason_codes`, `input_snapshot_id`로 제한한다. 프롬프트는 경로별 PASS의 대상 행동과 금지된 교차 사용을 명문으로 적는다. 모델이 출구 표를 ADD 허가로 설명하거나 ADD 표를 청산 허가로 설명하면 schema 의미 오류다. 숫자 점수·확률·가중합·가격·수량·주문·임계치 변경 제안과 구 `prior_score`·평활·score50을 완전히 제거한다. `FIRM`/`TENTATIVE`도 숫자 점수로 환산하지 않는다.
4. 단일 endpoint의 목표 모델은 `gpt-5.4-nano`이다. 실제 호출 가능성·응답 schema·지연·단가를 검증하되 다른 모델을 병행 호출하지 않는다. 호출 빈도를 늘리면 기존 단일 슬롯 간격과 공유 symbol budget을 함께 검토한다. **경로×시장별** 창 길이·최근성·정족수·찬반 결정표를 따로 산출하고, 한 경로의 선택값을 전체 경로에 적용하지 않는다. 구 AI 답변이나 점수는 신규 표 또는 정답으로 변환하지 않는다.

## 연속 투표 집계 계약

1. 포지션·시장·세션·path ID·모델/프롬프트 세대별로 최근 시간창의 표를 **발생 순서대로 전부** 읽는다. 유효 표마다 독립적인 시세 generation과 provider 응답이 있어야 한다. 한 호출이 반환한 여러 path 표, 동일 시세의 재호출, 캐시, 복원된 동일 표는 한 경로에서 복수 표가 아니다. 유효한 연속 구간의 첫/마지막 시각, 표 사이 최대 간격, 최신 표 나이, 요청했으나 실패·예산 거절·원천 결손으로 빠진 주기를 기록한다. 유리한 표만 골라 다시 묶지 않는다.
2. **어느 경로·시장도 1표로 PASS나 VETO를 확정할 수 없다.** 최소 독립 유효 표 수의 시스템 하한은 2이며, 경로별 장후 후보는 2 이상에서만 탐색한다. 시간창·최신성·최대 표 간격·최소 관측 지속시간·각 방향 최소 표 수·`FIRM PASS`/`FIRM VETO` 최소 수·상충 표 허용량은 **경로×시장별 정책값**이다. `FIRM`/`TENTATIVE`는 각각 개수로 세고 숫자 점수나 가중합으로 환산하지 않는다. 중간 결손이 허용 간격을 넘으면 연속 구간을 끊고 새 구간의 정족수를 다시 채운다.
3. 집계는 `(전체 독립 표, PASS, VETO, FIRM PASS, FIRM VETO, 첫/마지막 시각, 최신 표 나이, 최대 표 간격, 결손 주기)`의 명시적 결정표를 사용한다. 전체 정족수 충족만으로 PASS가 되지 않는다. **해당 방향의 최소 표 수·강도·우세 조건도 모두 충족**해야 한다. 두 방향이 모두 조건을 만족하거나 동률·상충·짧은 관측 구간이면 `INSUFFICIENT`다. 1개의 최신 FIRM 표가 앞선 반대 표 여러 개를 덮어쓰지 못한다.
4. 첫 신호 시각에 그 이전에 **응답과 원장 저장이 완료된** 표만으로 불변 집계 snapshot을 만든다. 신호 뒤 새 표는 첫 결정을 바꾸지 않고 다음 재평가에만 쓴다. 같은 신호의 재평가가 VETO 보류 시작시각을 재설정하거나 ADD 후보의 원래 신호 ID를 재사용하지 못한다. 시장/세션/포지션/경로 버전 전환, 원장 손상, 시간이 역행한 응답에서는 이전 표를 승계하지 않는다.
5. 현재 `holding_exit_vote.py`는 표 수 snapshot과 오프라인 `research_decision`을 갖지만 `min_votes=1` 후보도 허용하고 집계의 시간 분산·결손 주기·경로 ID를 강제하지 않는다. 구현 시 이 관측 전용 계약을 경로별 원장·집계기로 바꾸고 **런타임 정책 validator와 장후 후보 모두 최소 2표 하한**을 공유한다. `signal_snapshot`의 단일 표 진단 출력은 유지할 수 있으나 `vote_count=1`이 청산 보류나 ADD 허가로 전달되는 소비자는 0이어야 한다.

## 신호 시점 결정표

기계식 청산 신호 또는 Main 반등 추가매수 후보가 확정되면 위 연속 구간의 **복수 독립 표**를 같은 포지션·시장·세션·path ID에서 고정해 집계한다. 신호 시점에 동기식 AI 호출은 하지 않는다. 0표·1표·정족수 미달·상충·원천 결손은 모두 해당 경로 `INSUFFICIENT`이며 최신 1표의 방향을 판정으로 전달하지 않는다. 앞 문서의 `180초·VETO 2표·FIRM 1표`는 익절 보류만의 미검증 초기 가설로 축소한다. 이것을 soft stop이나 ADD에 복사하지 않는다. 각 경로×시장은 자체 테스트 데이터와 장후 재생으로 호출 주기, 창, 정족수, 강도, 관측 지속시간, 표 간 최대 간격, 보류/차단 상한을 정한다. 현행 8/20초 최소·20/90초 최대 주기 및 공유 예산에서 독립 표가 실제로 만들어지는지도 경로별로 계산한다.

**집계 결과**가 PASS인 청산 경로는 해당 SELL 절차를 진행하고, 집계 VETO만 해당 soft 신호의 기존 안전 상한 안에서 보류할 수 있다. 집계 `INSUFFICIENT`에서는 해당 SELL을 진행한다. ADD는 **집계 PASS**일 때에만 기계식 후보·주문 guard를 재검증하고, 집계 VETO/INSUFFICIENT에서는 그 시도의 ADD를 차단한다. 익절은 보류 중 고점·bid·청산 가능 순수익과 첫 crossing을 보존한다. 일반 soft stop은 기존 `HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC` 90초와 해당 신호의 더 짧은 상한을 넘지 않으며 hard/protect/emergency·즉시 보호 신호에는 VETO가 적용되지 않는다. 시장 전환, 포지션 교체, 원천/quote 악화, 최대 보류 도달 시 기존 청산 절차를 재개한다. 보류 시작시각은 재시작·다음 루프에서도 유지해 무한 보류를 막는다. 신호 후 표는 다음 재평가에만 사용한다. 다른 경로의 PASS/VETO를 가져와 결손을 채우는 경로는 없다.

## 장후 생산자·소비자 연결 계획

공통 기초 모수는 clean baseline 이후의 실제 BUY 체결 수량→모든 SELL 체결·최종 잔량 0→DB `COMPLETED`·유효 수익률→체결 기반 비용 증거를 충족한 포지션이다. 그 위에서 경로별 신호·투표·후행 가격·기회 분모를 분리한다. **투표 정책은 경로×시장별 산출물**이며, 어느 한 경로의 PASS/VETO 정족수·창·프롬프트·EV를 다른 경로에 복사하지 않는다.

| 현재 장후 경로 | 확인된 역할 | PASS/VETO 개선 작업 |
| --- | --- | --- |
| `sniper_trade_review_report` → `holding_exit_observation_report` → `runtime_approval_summary` | 완료 포지션·비용·청산/후행 관측과 trailing 4축/운영 재생의 현행 연결. 아직 경로별 투표 정책 생산자는 없음 | 실제 position/BUY/SELL/원장 vote/signal/market/path ID와 source hash를 대사하는 공통 투표 기초 모수·결손 분모를 추가한다. 보고서와 요약은 TP·각 soft stop·ADD를 서로 다른 section으로 전달한다. |
| `trailing_four_axis_replay`, `trailing_mechanical_replay`, `holding_exit_observation_report` | 기계식 TP 임계치와 상황 분류 연구 | 네 익절 임계치와 기계 강약을 고정한 동일 포지션 경로에서 `EXIT_TRAILING_TP`의 PASS/VETO 프롬프트·창·정족수·보류 상한만 paired 재생한다. first crossing, bid·비용·후속 상승·검열을 기록하고 기존 4축 정책 후보와 별도 owner/hash로 발행한다. |
| `holding_exit_observation_report`, `holding_exit_sentinel`, `stop_loss_recovery_backtest` | 손절/회복 관측; sentinel은 report-only, backtest는 별도 오프라인 자료 | `EXIT_SOFT_STOP`과 census로 확인된 각 soft 경로를 별도 replay·tail-risk 구간으로 추가한다. VETO 후 가격 악화·hard stop 진입·실제 SELL 지연을 검증한다. sentinel은 결손/위험 진단만 소비하고 보류 정책을 직접 발행하지 않는다. 기존 오프라인 backtest를 자동 정책 승인자로 승격하지 않는다. |
| `avg_down_replay_capture`, `avg_down_policy_replay`, `strategy_owner_replay`, `scale_in_split_order_plan` | ADD 시점/상태 원천·격리 재생, 실제 추가매수 체결/분할 실행 경제성 | `ADD_REBOUND` 전용 PASS/VETO 장후 평가를 추가한다. 같은 Main 반등 후보의 ADD 허용·차단을 비교하고 실제 BUY 체결/미체결·수량·비용·최종 SELL을 묶는다. `scale_in_split_order_plan`은 주문형태·체결 owner로 유지하고 투표 정책의 선택값을 소유하지 않는다. NO_ADD 결과가 미관측이면 검열/CF로 격리한다. |
| `runtime_approval_summary` → 장후 summary/strict → `runtime_policy_bootstrap` | 현행 trailing 자료의 상태·정책 hash 전달; 투표 selector는 아직 없음 | 경로×시장별 `source_date`, model/prompt/path version, 공통 ID, 독립 검증, 비용 후 EV, tail, 호출 비용, 정책 hash, `allowed_runtime_apply`를 전달한다. 선택·PREOPEN·실제 PID는 같은 path hash를 검증하며 누락 경로를 다른 경로 정책으로 채우지 않는다. |
| `scalping_avg_down_recovery_calibration`, `scale_in_incremental_counterfactual`, PYRAMID 보정 family | 퇴역된 장후 보고서/정책 | PASS/VETO를 위해 복구하지 않는다. 필요한 원천은 활성 capture/체결/완료 자료에서만 읽고 과거 출력은 archive/audit로 분리한다. |

장후 판정은 **매 표의 시각·원천·경로와 호출 예정/성공/결손 주기를 순서대로 재생**한다. 경로×시장별 **단일축**(프롬프트, 시간창, 최소 독립 표 수, PASS/VETO 및 FIRM 각 최소 수, 관측 지속시간, 표 간 최대 간격, 최신성, 최대 보류/차단)을 먼저 비교하고 효과가 상호작용할 때에만 해당 경로 내부의 복합축을 검토한다. 후보마다 0표·1표·집계 성립·상충·예산 거절의 분모와 첫 신호까지 집계가 성숙한 비율을 기록한다. 표 한 개의 적중률이나 마지막 표의 정확도로 정책을 고르지 않는다. TP와 soft stop과 ADD를 하나의 승률 또는 공통 최적값으로 묶지 않는다. 청산은 다른 청산 규칙까지 포함한 전체 적격 완료 포지션의 비용 후 paired EV와 큰 손실을 보고, ADD는 후보 전체의 실제 제출·체결·NO_ADD/검열을 분리한 비용 후 증분 EV와 자본 사용을 본다. 승률은 진단값이다. 역사적 모델 점수와 응답을 PASS/VETO 정답으로 재사용하지 않는다.

## 테스트 데이터·성능·결과 검증

1. clean-baseline 실제 완료·체결/비용 영수증과 시점별 quote/flow를 읽어 **경로×세 시장별 동결 테스트 세트**를 만든다. 독립 날짜·포지션 분할과 source hash를 고정한다. 정확 입력이 없는 과거 건은 추정 시나리오로 분리하고 엄격 EV 분모에 넣지 않는다. 자연 표본이 부족한 path/market은 인공 경계 fixture를 보강하되 그것으로 수익성 개선을 주장하지 않는다.
2. 모든 경로에 0표·**단일 FIRM PASS/VETO 1표**·복수 독립 표·동일 스냅샷 복제·한 호출의 타 경로 표·상충/동률·표 간 과대 간격·중간 결손·예산 거절·늦은 응답 fixture를 만든다. 1표에서는 **집계 PASS/VETO가 모두 0건**이어야 한다. 누락·중복 path ID, 모델 오류, 포지션/시장 전환, 부분 체결, pending SELL/ADD, hard/protect/emergency, VETO 만료도 검증한다. 기대 결과는 구 AI가 아니라 기계식 신호·소유권·안전 계약으로 고정한다. 특히 `EXIT*.PASS`로 ADD 제출 0건, `ADD_REBOUND.PASS`로 SELL 허용/보류 변경 0건, 경로 간 표 차용 0건을 확인한다.
3. 실제와 같은 동결 입력량에서 호출당 경로 수, 공급자 요청 수(스냅샷당 최대 1), p50/p95/p99 지연, 신호 시점 대기(0), 공유 budget 거절·표 결손률, CPU/RSS, 토큰/비용을 계측한다. 장후는 기존 full snapshot과 같은 workload에서 wall/CPU/RSS·출력 크기·stage 완료를 비교한다. 공급자 오류 주입 시 hard stop 지연·중복 주문은 0이어야 한다.
4. 재생은 경로별 신호·허가·보류/차단·주문 결과를 기대 결과와 대조하고, 적격 실제 완료 포지션이 있으면 시장별 비용 후 paired EV·tail·missed upside·독립 holdout을 계산한다. 필드가 복원 불가능한 과거 사례도 가정별 중립/보수 시나리오를 따로 실행해 **시나리오 결과와 구현 오차**를 검증한다. 실체결/비용/후행 경로가 부족하면 엄격 경제성은 `null/source_gap`으로 남기되 기능·시나리오 결과·성능 검증은 동결 테스트 데이터로 끝낸다. 시나리오 EV나 경제성 null을 실제 개선 PASS 또는 자동 실거래 정책 선택 근거로 쓰지 않는다.

## 구현·검증 순서

과거 자료 검사는 프롬프트 입력·누출·원천 결손을 확인한다. 과거 AI 답변과의 일치율을 품질 기준으로 두지 않는다. 테스트 데이터의 **기능·성능·결과 검증과 경로별 장후 생산자/소비자 연결**을 코드 전환 완료 조건으로 둔다. 엄격한 경제성 표본이 없다면 `null/source_gap`과 임시 보수 정책을 구분해 기록하고 자동 승격하지 않는다. 구 점수 AI를 병행 호출해 결손을 메우지 않는다.

1. **경로 census·등록부**: 주기적 holding score, 신호 시점 holding flow, near AI exit, OPEN_RECLAIM, soft grace, reversal ADD 점수 이력, POST_ADD_EVAL, 실제 `ADD_REBOUND`, AI decay/stagnation 관측, `evaluate_condition_exit`, retired Opening Rotation·overnight, legacy swing/probe, 알림·보고서·bootstrap을 검색한다. 각 분기를 활성 결정·source-only·퇴역으로 표시한다. 활성 soft 경로마다 고유 path ID와 기계식 신호·안전 상한을 확정하고 AI 점수만 있는 신호는 제거한다. 첫 접촉 AVG_DOWN 재호출과 PYRAMID는 활성 ADD로 오인하지 않는다.
2. **과거 자료 가용성**: 깨끗한 튜닝 모수는 `2026-06-05T00:00:00+09:00` 이후의 실제 BUY 수량, 모든 SELL·최종 잔량 0, DB `COMPLETED`·유효 수익률, 체결 기반 비용 증거를 요구한다. 이전 자료는 archive/audit에만 사용한다. 신호 전 AI 입력·시세 경로가 복원 불가능한 포지션은 투표 정책 EV에 포함하지 않고 결손 사유를 보존한다. 추정 가능한 가격 경로는 별도 시뮬레이션 층에서만 사용한다. **구 holding AI 응답은 교사 라벨이 아니라 제거 대상 호출량의 진단 자료**로만 취급한다.
3. **경로별 프롬프트·동결 세트**: English ASCII 프롬프트에서 각 path ID의 PASS 대상 행동·VETO 결과·교차 사용 금지를 별도 절로 작성한다. 실제 시점별 입력만 보여주는 chronological replay를 만들고 포지션/날짜 독립 분할을 고정한다. 구 점수/행동을 정답으로 사용하지 않는다. 세 시장×각 활성 경로의 결손·경계·교차 목적 fixture와 후행 체결/비용 세트를 준비한다.
4. **단일 생산자·연속 원장 구현**: 현재 관측 전용 `_schedule_holding_exit_vote_observation`·`_observe_holding_exit_vote_signal`과 `holding_exit_vote.py`를 실제 경로별 투표 생산자·원장·연속 집계기로 전환한다. 기존 주기 점수 호출 자리에서 요청된 경로 묶음만 새 endpoint 1회로 평가하고 별도 예약 worker·observe flag·`observation_only` 권한을 제거한다. 모델 응답의 경로 완전성·의미·원천을 검증하고 요청/결손 주기·표 순서·독립성·간격을 저장한다. 공통 집계 validator는 `min_votes >= 2`를 강제한다.
5. **소비자 원자 전환**: TP와 각 활성 soft exit는 자기 경로 사전 표만 읽고, ADD는 `ADD_REBOUND` PASS만 읽게 한다. 동기식 `holding_flow` 모델 호출을 제거하고 flow/OFI 원천은 단일 입력에 연결한다. 기계식 신호가 없는 구 점수 EXIT와 숫자 점수 이력 기반 reversal ADD 후보 상태를 제거한다. `can_consider_scale_in`·주문 guard·SELL 우선권을 유지한다.
6. **장후 경로별 집계 튜닝 연결**: 공통 적격 원천을 각 path ID로 분기하고 각 표의 연속 재생·첫 신호 시점 불변 snapshot을 TP, 개별 soft stop, ADD에서 계산한다. 경로별 독립 정책/보고서/hash와 3시장 후보를 발행하며 최소 2표 하한·간격·관측 지속시간을 런타임과 같은 validator로 확인한다. 기존 trailing 4축, 주문분할, source-only sentinel과 소유권을 섞지 않는다. runtime summary·strict handoff·bootstrap의 경로별 생산자/소비자 결손을 닫고, 퇴역 family는 되살리지 않는다.
7. **잔여 수거·반복 검증**: 활성 점수 prompt/schema/normalizer/prior/평활/threshold/env/보고서 소비를 제거한다. 테스트 데이터로 경로별 기대 결과와 호출·지연·장후 wall/CPU/RSS·비용을 검증하고 코드리뷰→수리→재리뷰를 반복한다. 과거 영수증은 `legacy_diagnostic_only`로 보존한다. 배포·PID·자연 경제성은 별도 수용하며, 문제가 생기면 구·신 AI를 병행 호출하지 않고 검증된 이전 immutable release로 전체 원자 롤백한다.

## 완료 조건

세 시장 모두에서 신호 전 **경로별 연속 표와 집계**가 포지션·시세·시장·모델·path ID에 묶여야 한다. `vote_count`가 0 또는 1일 때 AI 집계 PASS/VETO는 **0건**이어야 하며, 2표 이상이어도 시간·독립성·방향·강도 조건을 못 채우면 `INSUFFICIENT`다. `EXIT*.PASS`는 해당 청산만, `ADD_REBOUND.PASS`는 해당 기계식 ADD 후보만 진행시켜야 한다. 교차 목적 표 사용·경로 간 공통 튜닝값 적용·신호 뒤 응답 소급·같은 스냅샷 중복 표는 **0건**이어야 한다. 유효 검토당 공급자 호출 최대 1회, 구 점수 AI·신호 시점 flow AI·추가매수 구 점수 재호출 0회를 trace로 확인한다. 활성 청산·ADD에서 숫자 holding 점수·점수 이력·HOLD/TRIM/EXIT·score50이 결정을 바꾸는 경로는 0개여야 한다. EXIT 집계 결손은 기존 청산, ADD 집계 결손은 차단으로 기록되고 hard/protect/emergency·주문·수량·원천 안전과 보류 상한이 유지되어야 한다.

완료 보고서는 **각 path ID×세 시장**의 동결 테스트 세트 수·제외 이유, 기능 결과 PASS/FAIL, 공급자/장후 성능 수치, 비용 후 paired EV/검열/holdout 상태, 산출물 hash와 마지막 소비자를 표기한다. 엄격한 경제성 표본이 부족하면 그 셀은 `null/source_gap`이며 자동 정책 적용은 금지한다. 테스트 데이터의 기능·성능·결과 검증이 완료되기 전에는 코드 전환을 완료로 선언하지 않는다. 코드 검증, 선택 정책, 배포, 실제 PID 소비, 자연 실적의 성과는 별도로 보고한다.
