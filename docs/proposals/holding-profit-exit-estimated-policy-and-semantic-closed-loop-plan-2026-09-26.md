# 익절 PASS/VETO 추정 정책 폐루프와 의미적 감시기 구현계획 — 2026-09-26

## 결정과 범위

자연 v10 투표·체결 표본이 아직 없어도 **생산자 → 장후 선택 → 요약·strict handoff → 장전 검증·소비 → 실제 PID 영수증 → 익절 의미 감시**의 코드 경로를 완성한다. 최초 3시장×5경로 정책은 기존 코드 기본값을 `estimated_provisional`의 보수적 시작 정책으로 명시 발행한다. 재구성·시나리오 계산으로 더 나은 값이 확인되면 정해진 안전 범위 안에서만 후보로 만든다. 비교 불능 셀은 기본값을 유지하며 공란이나 다른 시장·경로의 값을 대입하지 않는다. 자연 표본 부재는 **경제성 검증 결손**으로 표시하되 생산·선택·전달·소비 계약의 미구현 사유로 사용하지 않는다.

이 문서는 구현 명세다. 정책 적용, selector 이동, 프로세스 재기동 또는 매매 실행 영수증이 아니다. 현재 KST 2026-09-26 일일 checklist가 없어 실행 OPEN owner는 확인할 수 없다. 9/28 checklist는 미래 일정이며 오늘의 대체 owner로 쓰지 않는다. 적용 시에는 당시 checklist·release routing·동작 중 wrapper·선택 release·실제 PID를 다시 대사한다.

## 확인된 결손

| 연결 | 현재 코드 상태 | 보완 |
| --- | --- | --- |
| 신호 전 생산 | `sniper_state_handlers._collect_holding_path_votes`가 v10 경로별 입력·해시·원장을 생산한다. 첫 트레일링 crossing 직전 동기 호출 가능성이 남는다. | 비동기 선행 수집과 신호 시점 모델 대기 0건 계약. |
| 장후 재생 | `scalping/holding_path_vote_replay.py`가 15셀 단일축 후보와 기록된 표의 판단 수를 낸다. 비용 후 paired EV, 독립 검증, 선택 정책은 `null`이다. | 엄격한 실적층과 명시적 추정층을 분리한 선택 생산자. |
| 장후 전달 | `runtime_approval_summary.py`의 `holding_path_vote_lineage`는 연구용이고 `allowed_runtime_apply=False`다. | 정책 파일의 정확한 날짜·세대·해시·15셀·증거등급 전달. |
| 장전 소비 | `automation/runtime_policy_bootstrap.py`는 고정 기본값 hash만 확인하고, 런타임 `_HOLDING_PATH_POLICY`도 코드 기본값을 읽는다. | 검증된 대상일 정책을 장전 로더가 읽고 런타임 한 세대로 고정; 결손·오염 시 정확한 incumbent 유지. |
| 의미 감시 | `holding_exit_sentinel.py`는 익절 흐름의 신호·SELL 비율을 보지만 투표 원장·첫 crossing·정책·체결 의미를 연결하지 않는다. `SESSION_START=09:00`은 프리마켓 관측에 부적합하다. | 3시장 세션 범위와 익절 상태전이·수량·비용·정책/PID 연결 검사. |

현재 보존 보고서는 완료·유효 수익률 329건이더라도 엄격 BUY/SELL/비용 적격 0건, 원천 결손 날짜 82개이며 v10 자연 원장이 없다. 따라서 추정 EV를 실현 EV로 승격하거나 AI 정확도·최적값이라고 부르지 않는다. 2026-06-05 KST 이전 자료는 현재 튜닝·승격 입력에서 제외한다.

## P1. 추정 정책 생산자와 증거 계약

1. `scalping/holding_path_vote_replay.py`의 15셀 `(path_id, market)` 중 `EXIT_TRAILING_TP` 익절 셀 3개를 우선 경제 평가하되, 같은 원장·선택·소비 계약을 나머지 EXIT 3경로와 ADD 1경로에도 적용한다. PASS는 EXIT에서는 *청산 허용*, ADD에서는 *추가매수 허용*이며 경로를 섞지 않는다. 시장은 `PREMARKET`, `REGULAR`, `INTEGRATED_AFTERMARKET` 셋으로 고정한다.
2. 한 셀에 `strict_realized`, `reconstructed_estimate`, `stress_scenario`, `baseline_prior`의 증거층과 분모·제외 사유를 별도 저장한다. 정확한 체결·비용을 가진 `COMPLETED` 포지션만 `strict_realized` 비용 후 paired EV에 넣는다. 과거 가격 경로의 누락은 출처가 있는 필드만 재구성하고, 절대 추정할 수 없는 투표·체결·비용은 `INSUFFICIENT` 또는 구간 추정으로 둔다. 과거 점수를 v10 PASS/VETO로 변환하지 않는다. 추정 매도·NO_ADD는 실제 체결로 계상하지 않는다.
3. 재구성 시 기준 정책과 후보를 동일 포지션·동일 시세 경로에서 짝지어 실행 가능 bid, 지연, 수수료·세금·슬리피지 범위, 미체결 검열, 후속 상승과 큰 손실을 함께 계산한다. 원천 관측 당시 시점 이후 정보가 신호 입력에 새지 않도록 as-of를 고정한다. AI 표가 없으면 `all PASS`, `all VETO`, 혼합, 늦은 응답, 원천 결손을 **시나리오**로만 계산하고 모델의 실제 승률로 해석하지 않는다.
4. 정책 선택은 셀별 독립이다. 단일축 후보부터 비교하고 `min_votes/pass_votes/veto_votes`, 최신성·간격·관측 기간·`max_defer_sec`처럼 상호작용하는 값은 제한된 복합축으로 검사한다. 엄격 경제 증거가 없으면 어떤 후보도 `validated_edge`가 아니다. 추정 구간 전반에서 개선이 분명하지 않으면 현행 기준값을 발행한다. 최초 발행값은 `min_votes=2`, `pass_votes=2`, `veto_votes=2`, `firm_veto_votes=1`, `window=180s`, `latest_age=40s`, `max_gap=100s`, `min_duration=8s`, TP `max_defer=45s`이며 다른 경로의 현행 값도 그대로 복제해 15셀을 완성한다. 이 값은 최적값 주장 없이 운영 기준선의 명시적 선택이다.
5. 출력은 대상일·원천일·시장·경로·정책값/해시·기준 정책 해시·모델 ID·prompt/schema 버전·원천 해시·가정 버전·추정 구간·자연 표본 수·실현 EV(`null` 가능)·추정 EV·선택 사유·rollback hash·증거등급·만료일을 가진 불변 policy bundle이다. `estimated_provisional`과 `validated_real`을 별도 상태로 둔다. 전자는 이 요청의 한정된 **operator-directed initial policy** 경로로 발행·검증·소비할 수 있어야 하며, 승인 근거·값·범위·rollback을 영수증에 넣는다. 기존 일반 `live_auto_apply_ready`나 검증된 경제 우위로 표시하지 않는다. `allowed_runtime_apply`는 **완전한 15셀·날짜/해시·안전범위·release/장전 검증**을 통과할 때만 참이다. 이것은 자연 경제성에 근거한 자동 승격과 별도 권한이며 실제 적용은 release/PID 영수증으로 판정한다. `source_gap`은 결측 사유이고 `no_edge`가 아니다. 정책 변경은 임계치/투표 집계만 소유하며 provider, 호출 빈도, 주문 가격·수량, hard/protect/emergency에 권한이 없다.

## P2. 장후부터 런타임까지 직접 소비

1. `holding_exit_observation_report.py`는 공통 기초 모수의 BUY 체결 수량 → 모든 SELL 체결/잔량 0 → DB `COMPLETED`·유효 수익률 → 체결 기반 비용 증거를 먼저 확정하고, 그 위에 익절 규칙·정확한 매도시각·후행가격 관측층을 분리한다. 각 층의 ID·결손 사유·분모를 정책 생산자에게 전달한다. 정확한 매도시각이 없어도 기초 모수에는 남기되 후행 관측·정확 시점 재생에서는 제외한다.
2. `runtime_approval_summary.py`는 생성된 bundle의 정확한 해시·15셀·증거등급·실현/추정 경제성 구분을 인용한다. `postclose_summary_handoff.py`는 동일 원천일/대상일, 최신 stage terminal, bundle·summary 해시, 완전한 15셀, 허용 모델·prompt·시장 enum, 결손 ID와 각 셀 fallback을 의미적으로 검증한다. 단순 파일 존재나 전체 summary PASS는 이 검사를 대신하지 않는다.
3. `runtime_policy_bootstrap.py`는 해당 대상일 bundle을 검증한 후 불변 manifest에 포함한다. 실제 런타임 로더는 실행 시작 때 **한 번** bundle을 고정하고, 신호 시점에는 그 고정 세대만 읽는다. `PATH_POLICY_BY_MARKET`은 코드 기본값이자 정확한 fallback이다. bundle 누락·손상·다른 날짜·부분 셀·parent/hash 불일치·만료·안전범위 위반은 거부하고 이전에 검증된 정확한 incumbent 또는 코드 기본값으로 복귀하며 이유를 영수증에 남긴다. 시장·경로 사이 대체는 금지한다.
4. `validate_path_policy()`에 누락된 `max_defer_sec`의 숫자·유한성·하한/경로별 상한 검사와 정책 키 완전성 검사를 추가한다. EXIT VETO의 보류는 기존 TP 최대 45초를 초과하지 않으며, 불충분/저장 실패/원천 실패는 EXIT 진행, ADD 차단으로 유지한다. hard/protect/emergency, 중복 SELL, 브로커·시세 안전 검사는 우선한다. 장전 receipt, runtime 선택 hash, `holding_path_signal_snapshot.policy_sha256`, 실제 PID의 로드 hash를 같은 세대로 묶는다.
5. 배포 전 합성·재구성 데이터로 15셀 생성→장후 보고서→summary→strict→bootstrap→런타임 로더→신호 판단을 실제 인터페이스로 통과시킨다. 자연 표본 0건 fixture도 15셀 정책을 소비해야 하며 `realized_ev=null`, `evidence_grade=estimated_provisional`이 유지되어야 한다. 이는 코드 폐루프 검증이고 실제 PID 소비 영수증은 아니다.

## P3. 익절 흐름 의미적 감시기

기존 `holding_exit_sentinel.py`를 **장중 보고 전용 흐름 감시 owner**로 확장한다. `error_detectors/artifact_freshness.py`와 strict handoff는 **장후 artifact 의미/세대 검증 owner**로 연결한다. 같은 판정을 두 감시기에 중복 구현하지 말고 공통의 순수 검증 함수는 기존 `scalping` 또는 `monitoring` 역할 패키지에 둔다. `src/engine` 루트에 새 Python 파일을 만들지 않는다.

| 상태 전이 | 검사할 의미 | 결손/위반 처리 |
| --- | --- | --- |
| 실매수 → 보유 세대 | broker BUY 주문·체결번호와 누적 수량, position key, 추가매수 뒤 buy-fill identity 변화 | 연결 안 되는 표는 격리; 이전 세대 투표 재사용 금지 |
| 시세 → arm/강약 → 첫 crossing | 유효 route/epoch/시세시각, 실행 가능 bid와 순수익, +0.4% peak arm, 기계 강·약 분류, normal/`trailing_peak_worsen_floor` trigger kind | 고정 익절 owner `scalp_trailing_take_profit`의 상태 전이를 역순·중복 없이 확인; 프리마켓 시계 허용과 독립 실행 가능 조건 분리 |
| 신호 전 호출 → 표 원장 | due/hash 변경/선점/공급자 호출/유효표/저장, 중복 입력·동시 선점, v10 모델·prompt·purpose·경로·시장·route·epoch·buy identity | 유효하지 않은 표는 정족수에서 제외; provider/parse/저장 결손을 명시 |
| 첫 crossing → 동결 신호 → 투표 집계 | 모든 반영 표의 `persisted_at < first_crossing`, 서로 다른 입력 세대, 같은 시장·경로·세션·정책 hash, 2표 이상과 시간 조건; 1회 동결한 신호 ID 재사용 | 신호 시점 모델 대기 0건; 후착 표로 동결 판단 소급 변경 금지; ADD 표로 SELL 허용 금지 |
| PASS/VETO/INSUFFICIENT → 청산 | EXIT PASS는 청산 허용, VETO는 경로별 제한 시간 이내 보류, INSUFFICIENT는 청산 진행. 악화·만료·하드 안전 시 재검사 후 진행 | 보류 시작시각 리셋·45초 초과·hard/protect/emergency 지연은 의미 위반 |
| SELL 요청 → terminal → 비용 | 동일 position/신호/order ID, 제출·부분/전체 체결, SELL 합계≤BUY 합계, 잔량 0, DB `COMPLETED`, 수수료·세금과 유효 수익률 | 미제출/미체결/부분/완료를 별도 표시; 결손 비용을 0으로 대체하지 않음 |
| 청산 후 가격 | 정확한 최종 SELL 체결시각을 기준으로 1/3/5/10분 관측의 시세 출처·검열 | 시각 없으면 기초 완료 모수 보존, 후행층만 제외 |

감시 분모는 3시장×`normal/trailing_peak_worsen_floor`×position/attempt 단위로 `active → source_ready → due → hash_changed → claim → provider_called → valid/persisted vote → arm → first_crossing → signal snapshot → PASS/VETO/INSUFFICIENT → defer/recheck → SELL intent/submitted → partial/full fill → completed/cost → forward-price observed`를 노출한다. main 실거래와 widget/episode/sim/probe/CF는 분리한다. `source_gap`, `semantic_contract_invalid`, `policy_binding_gap`, `runtime_not_consumed`, `pending_terminal`, `economics_null`, `valid_empty`를 구별한다. 표본 0건 자체는 실패가 아니지만 **그때도 정책·검증기·소비자 경로가 동작하는지** 별도 검증한다. 잘못된 해시·역전된 시간·수량 불일치·안전 지연은 실패, 자연 표본 부족은 관측 대기로 처리한다.

프리마켓·정규장·통합애프터마켓의 정책 분류는 현재 익절 소비자의 `scalp_trailing_market_type_at`과 일치시키고 실행 venue/route는 `src/trading/market/session_contract.py`의 공통 계약으로 확인한다. 기존 감시기의 09:00 고정 시작/venue별 하드코딩으로 프리마켓 신호를 누락하지 않도록 한다. 5/10/30분 창은 해당 시장의 관측 시작과 종료에 맞춰 계산한다. 감시 보고서는 읽기 전용이며 SELL, threshold, provider, bot restart를 실행하지 않는다.

## P4. 신호 전 호출 지연 제거

`sniper_state_handlers.py`의 보유 AI 수집은 보유 중 유효 입력 변경 시 선행 작업으로 예약한다. 수집 작업은 불변 입력·position/buy-fill/시장/route/epoch/모델·prompt/정책 세대를 동결하고, 원자 claim으로 중복 호출을 막는다. 결과 저장 시에도 같은 세대와 최신 상태를 다시 비교해 늦은 응답은 격리한다. 보유 루프·첫 crossing·SELL 경로는 REST/모델 결과를 동기 대기하지 않는다. 큐 포화, timeout, 원천 결손, 종료/재시작 시 기존 EXIT 진행·ADD 차단 계약을 유지한다. 단계별 wait, provider latency, timeout, budget 사용량과 신호 전 유효 정족수 성숙률을 감시기에 제공한다. 호출 빈도 증가는 실제 모델 ID·p95/p99·공유 예산 결과를 확인한 뒤 별도 튜닝 대상으로 둔다.

## 검증과 적용 순서

1. **계약/자료:** 15셀 기준 정책·증거등급·안전 경계와 보존 자료/자연 자료의 가용 필드, 제외 ID를 고정한다. 현행 dirty 작업은 보존하고 대상 파일만 변경한다.
2. **생산자/선택:** 엄격 실적과 추정 시나리오를 분리해 불변 bundle을 발행한다. 자연 0건에도 기본값 선택과 구체적 결손 사유가 있어야 한다.
3. **장후·장전 소비:** observation → summary → strict handoff → bootstrap → 런타임 loader의 날짜/해시/15셀 결합을 구현하고, 누락·손상·stale·부분 bundle을 거부한다.
4. **실시간 의미 감시/비동기 수집:** 프리마켓 포함 시장별 상태전이와 비동기 선행 표 수집을 연결한다. 최초 신호 시점 동기 모델 대기 0건, 보류 상한/안전 우선권을 확인한다.
5. **리뷰·결과·성능:** 경로×시장 15셀, normal/fast 익절, 0/1/2표, 중복 해시, 뒤늦은 표, 부분 체결, 비용 결손, 정확한 매도시각 결손, 재시작·세대 변경, 3시장 경계, 실패한 stage/정책 롤백 fixture를 검토한다. 장후 전체 계산 wall/CPU/RSS와 후보 수/분모, 장중 claim·모델·store p50/p95/p99 및 SELL 신호 대기 시간을 측정한다. 변경→자체 리뷰→결함 수정→재리뷰→대상 회귀/compile/diff/문서 parser 순으로 닫는다.
6. **운영 수용:** 코드·합성 폐루프와 release/장전 policy 소비를 각각 영수증으로 남긴다. 다음 영업일에는 실제 PID의 정책 hash, 자연 v10 표와 정족수, 첫 crossing, SELL terminal/비용, 장후 재생과 감시기 결과를 추가 대사한다. 자연 경제성·모델 정확도·최적값 평가는 그 후에만 판정한다.

## 완료 기준

- 자연 표본 0건에서 15셀 추정 기준 정책이 유효한 대상일 artifact로 생성되어 summary/strict/bootstrap/런타임 로더까지 **같은 해시**로 연결된다. 실현 EV는 `null`, 추정치와 가정·분모는 별도다.
- 익절 normal/fast 두 trigger에서 첫 crossing 전의 같은 세대 표만 집계하고, 신호 시점 외부 호출 대기 0건이며 PASS/VETO/INSUFFICIENT·보류 상한·안전 우선권이 일관된다.
- 감시기는 프리마켓까지 포함한 3시장별 흐름, terminal/비용 결손, 의미적 역전·정책 결합 오류를 탐지하고 실제 청산·PID·경제성의 증거 단계를 구별한다.
- 실제 정책 적용·PID 소비·자연 성과는 각각 별도 수용 영수증으로 남는다. 그 전에는 구현 완료를 운영 성과로 표시하지 않는다.
