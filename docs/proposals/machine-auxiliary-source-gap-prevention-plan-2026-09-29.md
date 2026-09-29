# 기계판정·보조 AI 원천결손 재발 방지 수정계획 — 2026-09-29

상태: **코드 구현·표적 리뷰 완료; 배포·재기동 미실행**. 범위는 Main 기계판정과 그 뒤의 compact 보조 AI, 두 판정의 장후 결과 결속이다. 다른 세션의 장후 모니터링과 산출물을 변경하지 않는다. 현재 실행 소유자는 [2026-09-29 체크리스트](../checklists/2026-09-29-stage2-todo-checklist.md)의 기계 비진입 자연 수용 및 compact 직접 family 항목이다.

## 1. 오늘 확인한 결손을 분리한다

| 단계 | 관측된 사실 | 현재 판정 | 수정 책임 |
| --- | --- | --- | --- |
| 프로브 → 기계 특징 | `strategy_tape_score_source_missing` 393건에서 경로별 0B·0D는 `ready`였다. 그중 388건은 관측 대기 종료 시 0B 5건 목표 미달, 5건은 목표 충족 후에도 실패했다. | 5건 미달은 정규장 10초 웜업/최대 15초, 프리·애프터 15초 웜업/최대 20초 안에 거래가 뜸하면 자연스럽다. **5건은 대기 종료 목표이지 기계판정의 필수 입장 조건이 아니다.** 대기 종료 시 5건 미만이어도 정확한 0B·0D가 있으면 기계 호출로 진행한다. 실패 원인은 실제 선택된 특징 틱과 신뢰 근거가 보존되지 않아 미확정이다. | `zero_base_probe.py`, `scalping_feature_packet.py`, `microstructure_reaction_context.py`, `entry_strategy_policy.py`, `ai_engine_openai.py` |
| 보조 AI → 후행 비용 | compact AI 시간초과 6건에서 판단 시점 입력은 있으나 `entry_conservative_execution_cost_pct`가 없다. | 비용 영수증 생성·전파가 정상 응답 경로에 결박돼 있다. | `ai_engine_openai.py`, 기존 판정 추적 생산자 |
| 판정 → 장후 가격/경계 | compact AI 38건 모두 정확 경로 캐시에 10분 가격이 있었지만 현 pending 라벨은 정확한 비용/반대 방향 경계가 없어 `entry_quality_path`를 평가하지 못했다. | 수집 자체보다 AI 라벨 생산자의 비용·경계·가격 소비 계약 결손이다. | `ai_decision_quality.py`, `ai_action_outcome_calibration.py` |
| 사전 점검 → 기계정책 | `main_machine_policy` 시작이 원천 사전 점검보다 앞서고, 원천 영수증 대기 상한은 300초다. 자원 가드 실패도 장후 생산을 멈췄다. | 실행 순서와 자원 스케줄 결손이다. | `deploy/run_threshold_cycle_postclose.sh`, source-quality audit 소비자 |

이 숫자는 9/29 읽기 전용 점검의 분모이며 실주문 실패 건수나 정책 성과가 아니다. 0B·0D 수신 성공, 신뢰 가능한 체결 방향·개별 체결수량, 기계판정 성공, 후행 가격, 비용 후 성과를 각각 구분한다. 원본이 실제로 없는 경우를 성공 또는 손실 0으로 바꾸지 않는다.

## 2. 수정 순서

### P0. 다음 장 전에: 정확 경로의 판정 입력을 하나로 결속

1. `zero_base_probe.py`의 경로별 `recent_trade_ticks_by_route`에서 item, 시장 route/접미사, transport epoch, 등록 시점 이후 수신 시각을 모두 확인한 틱만 특징 입력 후보로 전달한다. 프리마켓 `_NX`, 정규장·통합 애프터마켓 `_AL`을 각각 실제 요청·수신 route와 대사한다. 정규장/애프터마켓에서 NXT 후보를 별도 모집단으로 만들지 않는다.
2. `scalping_feature_packet.py`의 WS/REST 선택은 **최종 판정에 사용한 틱 묶음**을 반환하고, 선택 이유를 남긴다. 기존 REST `ka10003` 틱은 같은 route·시각·수량 출처가 검증될 때만 체결 압력의 대체 입력이 된다. 경로가 불명확하거나 신뢰할 개별 체결수량이 없으면 `required_feature_insufficient`로 끝낸다. WS 등록 대기, 감시 슬롯, 진입 정책 임계값을 임의로 늘리거나 완화하지 않는다.
3. `microstructure_reaction_context.py`의 현재 10틱 중 한 건의 명시적 비신뢰 수량이 전체 체결 압력을 비우는 동작은 별도 회귀로 고정한다. **충분한 신뢰 틱이 따로 있는 경우** 그 틱만으로 현재 정책의 최소 표본과 신선도를 만족할 수 있는지 오프라인으로 먼저 검증한다. 통과하지 못하면 기존 fail-closed 판정을 유지한다. 이 단계에서 신뢰 기준이나 정책 임계값을 낮추지 않는다. 0B 5건 미달만으로 `source_insufficient`를 확정하지 않는다.
4. `strategy_tape_score_source_missing`을 포괄적인 `assessment_contract_invalid`로만 남기지 않는다. 기존 probe 결과와 판정 추적에 attempt ID, 종목, venue/session, route/item, transport·등록 epoch, 0B/0D 수신 수, 선택한 WS/REST 틱의 출처와 해시, 신뢰 방향·수량 건수 및 실패 사유를 같은 identity로 기록한다. 실패한 경우 재현 가능한 최소 정규화 틱 창을 기존 추적 저장 경로에 보존하고 토큰·계좌 값은 제외한다. 판정 캡처가 생성되지 않은 시도도 이 추적에 남긴다.
5. 검증된 WS와 같은 경로의 REST를 모두 대조한 뒤에도 **현행 정책에 필요한 신뢰 표본**이 모자란 경우만 `source_insufficient_sparse_trade`, route/epoch 불일치는 `source_route_conflict`, 선택 경로에서 충분한 신뢰 틱을 잃은 경우는 `feature_tick_selection_gap`처럼 원인별로 분리한다. 이는 **진단 상태**이며 기계 `ENTER_NOW`나 주문 권한이 아니다. 393건 전부의 세부 원인을 사후 추정으로 일괄 재분류하지 않는다.

### P1. 다음 장 전에: 보조 AI 호출 전에 분석 원천을 고정

1. 기계 `ENTER_NOW`와 동일 attempt의 보조 AI 호출 직전에 가격 기준시각, 정확 broker/market-data route, 적용 비용 계약 종류·해시, 현재 보조 AI의 반사실 체결 마찰비용, compact 입력 해시를 기존 trace/pending 원천에 고정한다. 이 값은 반 스프레드와 제한된 자료 지연 가산으로 계산되며 실제 수수료·세금이 포함된 왕복비용이 아니다. 실제 운영 순손익 비교에는 별도의 정확한 비용 영수증이 필요하다. broker 조회를 추가하지 않는다.
2. 정상 응답, `PASS`/`VETO`, 시간초과, transport 오류, schema reject가 **같은 사전 영수증**을 참조하도록 응답 조립과 예외 경로를 통합한다. 비용 원천 자체가 없으면 null과 정확한 원인을 유지한다. 시간초과를 AI PASS나 실제 주문 실패로 바꾸지 않는다.
3. 별도의 운영 경제성 관찰에서 나온 `unsupported_pre_ai_probe_reservation_scope`, `exact_broker_capacity_missing`, 공통 지연 가드를 한 `cost_missing`으로 합치지 않는다. broker capacity cache가 없으면 그 출처·관측 시각을 남기고, 고정 300만 원 예산이나 가상 주문 수량으로 채우지 않는다.

### P2. 장후 소비: 같은 attempt의 후행 가격·비용·경계를 결속

1. `ai_decision_quality.py`의 compact pending 라벨은 기계 캡처와 동일한 종목·attempt·venue/session·route 및 판정 기준시각으로 기존 완료봉 캐시를 먼저 검증·재사용한다. 충분한 가격이 없으면 기존 source-only 보강의 정확 route·완료봉 계약을 적용하고, 장 마감으로 관측 구간이 잘린 경우 `censored`로 남긴다. 1/3/5/10분 가격 경로를 확인하되 현재 승인된 정책 목표·기간을 몰래 바꾸지 않는다.
2. 보조 AI의 진입 품질 반사실 평가에도 기계 장후 경로에서 이미 쓰는 **명시적** `fixed_counterfactual_entry_boundary`와 동일 비용 owner를 사용한다. 이는 분석용 경계이지 실제 주문 stop, 체결 또는 실현 손익이 아니다. 실제 진입은 별도의 체결·stop owner 영수증이 있을 때만 실제 경로로 평가한다.
3. 동일 attempt의 가격 경로·비용·경계 중 하나라도 불명확하면 `entry_quality_path`는 `source_gap`/`censored`로 남긴다. 누락 비용을 0으로, 시간초과를 VETO로, 미진입을 실제 손실로 환산하지 않는다. 기계 `BLOCK/RECHECK`와 compact `PASS/VETO/transport_unavailable`의 분모를 분리한다.
4. source-quality audit은 식별 가능한 결손 attempt를 행 단위로 제외하고 적격 모집단을 계속 평가한다. 사전 점검 부재·무효, 행 격리 실패, 식별 불가능한 대량 계약 손실은 전체 입력을 차단한다. `assessment_contract_invalid`라는 포괄 분류만으로 정상 행 전체를 정지시키지 않는다.

### P3. 장후 실행 순서와 자원 가드

1. `deploy/run_threshold_cycle_postclose.sh`에서 해당 날짜 원천 사전 점검의 완료·해시 영수증과 자원 가드를 확인한 **뒤** `main_machine_policy`를 시작한다. 단순 300초 대기로 선행 생산자 완성을 추측하지 않는다. 사전 점검 실패 시 해당 stage는 명시적 `source_quality_blocked`이며 오래된 영수증을 재사용하지 않는다.
2. 자원 부족 때에는 기존 4 GiB 메모리 가드를 낮추지 않고, 선행 중복 작업의 종료를 기다리거나 stage를 직렬화한다. 제한 시간 안에 자원이 회복되지 않으면 날짜·stage·필요/가용 메모리와 재실행 소유자를 terminal에 남긴다. 성공하지 않은 장후 작업을 `valid-empty`로 표시하지 않는다.

## 3. 구현·리뷰·검증 게이트

| 단계 | 표적 검증 | 통과 조건 |
| --- | --- | --- |
| 입력 재현 | 9/29의 0B 5건 목표를 채운 실패 사례 5건을 우선 대조하고, 5건 미만이어도 기계 호출이 계속되는 사례, 정규장 `_AL`, 프리 `_NX`, 통합 애프터 `_AL`, 경로 혼합·재연결 epoch, WS/REST 불일치, 신뢰/비신뢰 수량 혼합 및 희소 체결 fixture를 검사한다. | **어떤 틱**이 특징·정책으로 들어갔는지 같은 attempt와 해시로 재현된다. 5건 목표 미달 자체는 결함이나 판정 실패로 세지 않고, 현행 정책에 필요한 적격 신뢰 자료가 충분하면 기계판정까지 도달하며, 부족하면 구체적 원인으로 fail closed 한다. |
| 보조 AI 종료 경로 | 정상 PASS/VETO, provider timeout, schema reject, 비용 원천 없음의 동일 입력 쌍을 비교한다. | 원천이 있는 timeout에서도 비용·route·해시가 보존된다. 원천이 없을 때 값은 null이다. 주문·AI 판정 결과는 비용 관측 보강 때문에 바뀌지 않는다. |
| 장후 결속 | 같은 attempt의 기계 `ENTER_NOW/BLOCK/RECHECK` 및 compact PASS/VETO/timeout, 동일 봉 target/경계 충돌, 세션 종료 censor, 캐시 변조를 검사한다. | 1/3/5/10분 후행 상태와 정확 비용·반사실 경계가 분리 기록된다. 실제 경제성과 반사실 경제성이 섞이지 않는다. |
| 실행 순서 | 사전 점검 지연·부재·행 격리·4 GiB 미만 가용 메모리 fixture 및 `--print-plan`을 검사한다. | 선행 영수증 없이 소비자가 성공하지 않는다. 유효 행은 식별 가능한 결손 행 때문에 전체 차단되지 않으며, 자원 부족은 명시적 terminal을 남긴다. |

수정 범위의 producer/consumer와 예외·silent-failure·정책/주문 권한 누출을 자체 리뷰한 뒤 보완·재리뷰하고, 표적 pytest, Python compile, wrapper의 `bash -n` 및 계약 테스트, `git diff --check`를 통과시킨다. Kiwoom REST/WS 요청·파서·FID·REG/REMOVE 자체를 수정해야 한다는 증거가 나오면 변경 전 [공식 참조 게이트](../kiwoom-api-data-contract.md)에 따라 현행 upstream revision과 관련 경로를 별도로 대사한다.

## 4. 배포와 다음 자연 수용의 경계

- 코드 검증 후에는 현재 선택 릴리스, 다른 세션 작업본, 실동작 PID, 장후 timer/cron을 대조한 단일 불변 릴리스를 준비한다. **이 계획 자체는 배포·재기동 또는 주문을 수행하지 않는다.**
- 다음 장의 프리마켓, 정규장, 통합 애프터마켓에서 같은 attempt의 `source → exact ticks → feature → machine action → compact result/timeout → pending label` 영수증을 각각 확인한다. `strategy_tape_score_source_missing`이 포괄 contract-invalid로 남는 건은 0이어야 한다. 진짜 희소 체결은 별도 source-insufficient로 남을 수 있다.
- 장후에는 그 attempt의 1/3/5/10분 가격, 비용·반사실 경계, `entry_quality_path`, 원천 격리 및 machine/auxiliary stage terminal을 대사한다. 자연 표본 수, holdout, 운영 경제성, 정책 후보, PREOPEN 선택, PID 소비, 실제 주문·체결·순익은 각각 독립적으로 판정한다. 한 단계의 PASS로 다른 단계를 완료 처리하지 않는다.

## 5. 이번 구현의 코드 범위

- 공식 참조 확인: 2026-09-29 22:41 KST, Kiwoom upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json` 내 `ka10080`, `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/packets.py`, `postman/kiwoom-openapi.postman_collection.json`의 운영/모의 요청을 대사했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없다. 공식 `ka10080` 요청은 `/api/dostk/chart`, `api-id: ka10080`, `stk_cd`의 접미사 없는 KRX·`_NX` NXT·`_AL` SOR, 1분 `tic_scope=1`, 선택적 `base_dt`, `cont-yn`/`next-key` 이어받기를 명시한다. 이번 변경은 이미 검증된 완료봉 캐시를 우선 소비할 뿐 wire 요청·응답 파서·FID·REG/REMOVE·실제 계좌/주문 호출은 바꾸지 않는다.
- 정확 경로·item·transport epoch·등록 이후 시각을 모두 만족한 WS 틱만 기계 특징으로 전달하고, 선택된 틱의 출처·해시·제한된 진단 창을 attempt 추적에 남긴다. 정확한 WS 틱과 검증된 candle이 있으면 REST 체결 이력이 빈 응답이어도 기계 특징 판정으로 진행한다. 0B 5건 미달은 단독 차단 사유가 아니다. `strategy_tape_score_source_missing`은 남은 신뢰 체결 방향·수량의 결손, 경로/epoch 불일치, 선택 후 압력 불일치를 별도 진단 필드에 기록한다. 체결이 실제로 없었다고 단정하지 않는다.
- 하나의 명시적 비신뢰 수량이 섞인 창의 압력이 닫히는 기존 정책은 회귀로 확인해 유지했다. 신뢰 틱만 별도로 추려 정책 입력으로 쓰는 변경은 독립 오프라인 비교가 필요하므로 이번 구현에 포함하지 않았다.
- 보조 AI 호출 전 replay 입력에서 반사실 체결 마찰비용과 입력 해시를 생성해 정상·시간초과 경로의 trace/pending에 함께 보존한다. 비용 원천이 없거나 계약 종류가 다르면 수치 대신 `source_gap`으로 남긴다. 이 비용은 실제 수수료·세금과 체결 손익을 증명하지 않는다.
- 보조 AI 장후 라벨은 해시 검증된 동일 날짜 기계 완료봉 캐시의 정확 경로만 재사용하고 부분 결손 경로는 기존 정확 경로 보강으로 보낸다. 기계 `ENTER_NOW`의 미체결 평가에만 명시적 고정 반사실 경계를 적용하며 실제 체결 손익과 구분한다.
- 장후 wrapper는 원천 preflight 이후 기존 4 GiB 자원 대기 뒤 기계정책을 시작한다. 단계 소비자는 정확 날짜·해시·입력 허용을 검사하며 결손 시 `source_quality_blocked` terminal을 남긴다. preflight의 생성 해시는 단계 실행 중 대조하되 이후 최종 감사가 같은 파일을 갱신해도 이미 닫힌 단계 영수증은 무효화하지 않는다.
- incumbent carry 검증은 장전/별도 정책 refresh가 staged generation을 같은 machine policy와 승계 증거를 유지한 bounded generation ancestry로 감싼 경우도 확인한다. source report의 최신 해시·parent, 각 generation의 날짜·원천·승계 proof·machine policy가 대조되지 않으면 계속 fail closed 한다.
- 재리뷰 검증: 관련 표적 pytest 522건 통과, 앞선 완료봉·시장 경로 추가 표적 7건 통과, Python compile, wrapper `bash -n`, `git diff --check`, 체크리스트 print-only parser 통과. 명시적 손절 값의 형식 오류는 고정 반사실 경계로 덮지 않으며, 진단 틱 창에는 방향·수량·호가 신뢰도 계산 필드를 포함한다. 자연 시장 데이터의 다음 실행, 정책 표본·holdout, 릴리스/PID 소비 및 비용 후 성과는 이 코드 검증만으로 확인되지 않는다.
- 9/30 KST 재복구에서는 incumbent carry ancestry 회귀를 추가하고 postclose summary/verifier 표적 110건을 통과시켰다. 실제 9/29 machine report와 terminal의 staged hash, 9/30 current generation의 bounded ancestry를 재검증했다. machine 후보 없음과 auxiliary 경제 모집단 0/38은 승계/정책 승격이 아님을 유지하며, 최종 종결 검증은 아직 남아 있다.

## 6. 장중 의미적 원천 감시 보강

Sentinel 본체가 실패해도 같은 wrapper는 독립 원천 감시를 실행하고 원래 실패 코드를 유지한다. 이때 기존 제출 분류는 유효하지 않다.

- 기존 5분 BUY Funnel Sentinel의 `submission_bottleneck_monitor`가 당일 pipeline probe 결과, 진입 AI trace, pending label의 최근 10분 완전한 JSONL 끝부분을 별도 원천으로 읽는다. 읽기 한도는 원천별 32 MiB이며 해당 10분을 덮지 못한 부분 tail·파일 부재는 `unobservable`이다. 기존 제출병목 분모와 원천 이벤트 수를 합산하지 않는다.
- 기계 입력은 정확 route의 `source_unavailable`, 필수 특징 결손의 원인, 판정 성공 후 캡처 영수증을 구분한다. `assessment_contract_invalid`의 원인이 누락되면 생산 결손으로 표시하고, 신뢰 가능한 체결 표본 부족은 진단으로 분리한다. 단일 0B 희소·노후와 `route_snapshot_missing`은 자연 저유동 가능성을 보존해 진단으로 남긴다. 완전한 원천 구간에서 같은 route의 원천 관측 10건 이상 중 판정 도달이 20% 미만이면 커버리지 점검을 알린다. 정확 route 충돌·선택 틱 결손·캡처 실패는 별도 조치 대상이다.
- 보조 AI는 실제 호출된 기계 `ENTER_NOW`의 사전 비용 상태·계약 해시·attempt, 판정시점 기준가격/route, pending 영수증 결속을 확인한다. 시간초과는 보조 AI 판단 결과와 분리해 기록하며 비용 null을 0으로 만들지 않는다. `outcome_label_eligible`인데 60초 뒤에도 정확한 pending 영수증이 없으면 생산 결손으로 분류한다.
- 알림은 원인·경로·종목·attempt와 기존 원천 보강 소유자를 제시한다. 자동 REST 재조회, WS 재등록, 매매·정책·provider 변경은 하지 않는다. 복구 표시는 과거 결손 복원이 아니라 같은 단계·venue·session·route의 새 정상 영수증과 완전한 최근 관측 구간을 뜻한다. 다른 경로의 정상 영수증은 결손 경로를 복구 처리하지 않는다. 실제 가격 후행 충족과 비용 후 정책 성과는 장후 별도 검증한다.
