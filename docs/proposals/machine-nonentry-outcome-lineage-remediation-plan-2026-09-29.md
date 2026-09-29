# 기계 비진입 후행경로·장후 정책 보완안 — 2026-09-29

상태: **코드 구현·리뷰 검증·릴리스 배포 완료, 자연 장후 수용 대기**. 이 문서는 스캐너·감시 큐의 실제 기계판정 증가가 장후 미진입 기회비용 입력 증가로 이어지는지 확인한 결과다. 주문·정책 권한을 부여하지 않으며, 2026-09-29 장후 결과는 아직 생성 전이다.

## 판정과 근거

1. 기계판정 원본은 남는다. `zero_base_probe.py`는 `machine_only=True`로 판정하고, `capture_machine_observation()`은 `mechanistic_entry_observation_v1`을 `ai_decision_payloads`에 기록한다. 2026-09-29 12:56~13:20 KST의 정규장 원본은 201건이며 `RECHECK` 136, `BLOCK` 36, `ENTER_NOW` 11, `source_invalid` 18이다. 이는 해당 시간대의 **전체 기계 캡처** 표본이다. 현재 캡처에는 probe/watch 단계 표지가 보존되지 않아 201건 전부를 스캐너 probe라고 분류할 수 없다.
2. **BLOCK/RECHECK 172건의 후행 수집은 충분하다고 검증되지 않았다.** 같은 종목·venue·session에서 판정 뒤 10분 안에 품질 적격 파이프라인 가격이 한 번이라도 있는 것은 47건(`RECHECK` 37, `BLOCK` 10)이다. 10분 종료 시점과 마지막 가격의 차이가 90초 이하인 것은 16건(`RECHECK` 11, `BLOCK` 5)뿐이다. 16건은 경로 평가의 **상한 후보**이지 비용 결속·첫 도달 판정까지 완료된 건수가 아니다. 나머지 156건을 손실·무기회 또는 정상 `BLOCK`으로 해석하면 안 된다. 측정은 13:43 KST의 증가 중인 당일 원천을 대상으로 했고, 이후 수집이나 장후 보강 결과가 아니다.
3. 일반 AI 후행 라벨과 probe 원본은 별개다. 당일 `ai_decision_outcomes` 28행은 모두 감시 경로 `entry_screen`·기계 `ENTER_NOW`이며, probe의 `BLOCK/RECHECK` pending 라벨은 이 파일에 없다. `ai_decision_quality._default_sources()`는 이 pending 파일을 라벨 입력으로 사용하고, `ka10080` 완료 1분봉 보강도 그 pending 라벨의 적격 경로에만 적용한다. 반면 `ai_action_outcome_calibration.load_machine_observation_rows()`는 기계 캡처를 직접 읽고 **파이프라인 가격만** `mature_outcome_labels()`에 전달한다. 따라서 AI 라벨용 완료봉 보강을 기계 비진입 후행 보강으로 간주할 수 없다.
4. probe 결과와 캡처의 명시적 결속에도 결함이 있다. `capture_machine_observation()`의 반환 키는 `machine_observation_sha256`인데 `zero_base_probe.py`는 `machine_observation_id`를 읽어 결과에 넣는다. 해당 결과 필드는 `None`이 되므로 probe 결과→캡처의 digest 조인이 끊긴다. 캡처에서 `source_event_stage`도 보존하지 않으므로 단계별 분모를 정확히 재구성하기 어렵다. 해시 검증된 캡처 자체가 사라진 것은 아니다.
5. 2026-09-28 장후 `winrate_policy`는 `incumbent_carried`였다. 정규장 입력 2,072회 중 수용 487회, 수용 전 충돌 제외 72회, 후행 비용·경로 결손/불일치 1,493회, 비용 scope 불일치 20회가 보고됐다. 별도 full-machine 보고서는 구조 적격 487건에도 운영 경제성 결속 0건·`machine_operating_population_unbound`였다. 이 두 보고서의 모집단과 정책 권한은 다르다. 후행 경로 수리는 양쪽에 필요하지만 한쪽의 `PASS`로 다른 쪽을 승인하지 않는다.
6. 현 승률 후속 정책은 최근 두 개의 2026-09-23 이후 신선한 날짜를 holdout으로 떼고 train 날짜 3개·선정 기회 30개 이상 등을 요구한다. 현 후보 축은 기존 `ENTER_NOW`에 추가 veto를 거는 방향이며, `BLOCK/RECHECK → ENTER_NOW`를 직접 시험하는 후보 축으로 확인되지 않았다. 비진입 기회비용 측정과 정책 승격을 구분한다.

### 최초 진단 네 항목의 오늘 반복 조건

| 결손 | 2026-09-28 확정 근거 | 2026-09-29 자료가 추가될 때 | 보완의 완료 판정 |
| --- | --- | --- | --- |
| 독립 날짜 부족 | 유효 날짜 9/22·9/23·9/28, train 3일·holdout 0일; `successor_independent_dates_insufficient` | 9/29가 유효 날짜가 되면 최근 두 신선한 날짜 9/28·9/29가 holdout이므로, 기존 날짜를 그대로 쓰는 train은 9/22·9/23의 2일이다. 오늘 접수량 증가만으로 train 3일과 holdout 2일을 동시에 충족할 수 없다. | 원본 검증을 통과한 독립 train ≥3일·holdout ≥2일을 **같은 재계산 영수증**에서 확인한다. 날짜를 중복 계산하거나 holdout을 train으로 옮겨 허들을 낮추지 않는다. |
| 학습 후보 표본 부족 | 기존 정책 train 선택 기회 19개·승리 시도 17개, 후보 0개; `successor_no_train_qualified_candidate`와 `successor_selected_sample_insufficient` | 현 후보는 기존 `ENTER_NOW`의 부분집합이고 train 선정 기회 ≥30을 요구한다. 9/29는 위 경우 holdout이라, 기존 train 19개가 그대로라면 오늘의 프로브 증가만으로 후보 30개를 만들 수 없다. | 후속 train 날짜에 비용·경로 유효한 고유 기회가 실제로 추가된 후, 후보 ≥30개와 coverage·승자 보존·승률 허들을 별도로 확인한다. 현재 19개를 중복 attempt로 부풀리지 않는다. |
| 원천·비용 결손 | 정규장 입력 2,072회 중 채택 487회; 동일 시도 충돌 72회, 경로·비용 결손/불일치 1,493회, 비용 scope 불일치 20회 | 새 판정 증가와 함께 후행 가격이 따라오지 않으면 같은 제외가 반복된다. 장중 172개 `BLOCK/RECHECK` 표본의 10분 끝 가격 적격 후보는 16개뿐이다. | 해시·route·비용·완료봉 결속 전후의 **동일 시도**별 제외 사유와 첫 도달 평가 수를 대사한다. 복구 불가 행은 그대로 제외한다. |
| 전체 기계정책의 운영 경제성 결속 | 별도 full-machine 평가에서 구조 적격 487건, 운영 경제성 결속 0건·독립 후보 0건, `machine_operating_population_unbound` | 유효 판정이나 승률 정책 날짜가 늘어도 이 직접 family의 운영 경제성 모집단 연결은 자동으로 생기지 않는다. | [현행 OPEN owner](../checklists/2026-09-29-stage2-todo-checklist.md)의 정확일자 원천·비용·운영 cohort·정책 비교 계약으로 결속 건수와 후보/제외 사유를 다시 확인한다. 승률 영수증을 direct family 경제성 승인으로 대체하지 않는다. |

근거: [`zero_base_probe.py`](../../src/engine/scalping/zero_base_probe.py), [`ai_decision_trace.py`](../../src/engine/scalping/ai_decision_trace.py), [`ai_decision_quality.py`](../../src/engine/scalping/ai_decision_quality.py), [`ai_action_outcome_calibration.py`](../../src/engine/scalping/ai_action_outcome_calibration.py), [`winrate_policy_2026-09-28.json`](../../data/report/ai_decision_action_outcome_calibration/winrate_policy_2026-09-28.json), [`ai_decision_action_outcome_calibration_2026-09-28.json`](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-28.json). 당일 표본은 `data/ai_decision_payloads/ai_decision_payloads_2026-09-29.jsonl`, `data/ai_decision_outcomes/ai_decision_outcomes_2026-09-29.jsonl`, `data/pipeline_events/pipeline_events_2026-09-29.jsonl`에서 source-only로 계산했다.

## 보완 순서

### 1. 원본 판정과 발견·감시 단계를 정확히 결속

- probe 결과의 `machine_observation_id`를 실제 반환된 `machine_observation_sha256`으로 결속하고, 캡처에도 `source_event_stage`, 발견 claim/source SHA, route, 평가 attempt ID를 보존한다. 원본 digest 계산 규칙과 append-only 보관을 유지한다. WATCHING의 재판정은 별개 attempt로 남기고, 동일 probe 결과를 중복 기회로 합산하지 않는다.
- 당일 분모를 `발견 claim → probe 결과 → 기계 캡처 → BLOCK/RECHECK/ENTER_NOW → 감시 편입 → 후행 경로`로 대사한다. 유실·중복·해시 불일치·source-invalid는 각각 독립 사유로 남긴다. 단순 동일 종목·시간 근접 조인으로 결손을 메우지 않는다.

### 2. BLOCK/RECHECK 후행 가격을 장후에 완성

- 현재의 짧은 probe WS 구독·감시 슬롯 정책은 가격 경로의 보존 기간과 분리한다. 기존 `ka10080` 완료 1분봉 경로를 **기계 캡처에도** 적용하는 방안을 먼저 시험한다. 동일 거래일·정확 종목·venue·session·완료 시각만 사용하고, `(날짜, 종목, 요청 route)`별로 한 번 조회/재사용한다. 파이프라인 가격은 완료봉이 없는 구간의 품질 적격 보조 자료로만 합친다. 추가 상시 WS 구독이나 주문 시점 REST 호출을 만들지 않는다.
- 프리마켓 `_NX`, 정규장 및 통합 애프터마켓 `_AL` 원천의 실제 API route·bar 세션 커버리지를 각각 검증한다. 세션 교차·미완성봉·지연/빈 응답·continuation 절단을 `source_gap`으로 남기고 다른 route 가격으로 대체하지 않는다. 특히 정규장 캡처의 `KRX` 세션 라벨과 `_AL` 통합 시장자료 route의 의미가 같은지 원본 provenance로 검증한 뒤 소비한다.
- 캡처의 executable ask, 해시 검증된 비용 원천, **고정 반사실 stop 거리와 그 소유자**, 완료봉의 target-first/stop-first를 결속한다. 현행 입력에는 해당 주문의 실제 stop 거리가 없으므로 기존 반사실 경계 `ENTRY_PATH_ADVERSE_PCT=-0.70%`를 실제 손절로 서술하지 않는다. 비용 원천은 현행 검증된 장후 economic owner를 사용하고, 당일 장중에 아직 생성되지 않은 비용 문서를 임의 값으로 채우지 않는다. 도달 전 종료·동일 봉 양방향 터치·가격 공백은 `CENSORED_OR_SOURCE_GAP`으로 유지한다. +1% MFE는 진단이며 비용 후 미진입 수익으로 승격하지 않는다.

### 3. 보고서와 정책 소비를 나눠 닫기

- 장후 보고서에 기계 행동별 `capture_count`, 유효 비용 수, 10분·30분·60분 가격 커버리지, 첫 도달 판정 가능 수, censored/source-gap 사유와 고유 기회 수를 추가한다. 기존 AI pending 라벨과 직접 기계 캡처의 분모를 섞지 않는다. 오래된 날짜는 원본·비용·route가 검증된 경우만 제한적으로 다시 계산하고, 회복 불가 결손은 그대로 제외한다.
- 승률 후속은 원천 복구 후에도 날짜 분할을 먼저 다시 계산한다. 9/29의 새 결과가 holdout으로만 들어가면 `train 2일`과 `후보 선택 ≥30개` 결손을 그대로 기록한다. 이후 독립 날짜가 쌓이거나 검증 가능한 과거 원천이 복구된 경우에만 train/holdout·고유 기회·coverage·승자 보존·비용 후 승률을 다시 평가한다. 허들·날짜 경계를 완화하는 것을 자료 수리로 포장하지 않는다.
- direct full-machine의 `machine_operating_population_unbound`는 별도 owner인 [현행 체크리스트의 OPEN 항목](../checklists/2026-09-29-stage2-todo-checklist.md)에서 원천→운영 경제성 결속으로 닫는다. 구조 적격 행과 경제성 owner의 날짜·venue/session·비용·운영 cohort·정책 identity를 순서대로 대사하고 첫 결손을 남긴다. 유효 counterfactual 경로와 실제 주문/체결의 경제성을 분리하며, 독립 비교 후보 0건을 임의 성과로 채우지 않는다.
- `BLOCK/RECHECK → ENTER_NOW` 전환 후보가 필요하면 그 축의 generator·publisher·PREOPEN loader·PID 수신과 비용 후 paired/holdout 증거를 **별도 설계·검증**한다. 비진입 결과를 수집했다는 사실만으로 현재 veto 축이 전환을 학습했다고 표시하지 않는다.

## 완료 판정과 검증

1. 회귀 입력은 정규장·프리마켓·통합 애프터마켓의 `BLOCK/RECHECK/ENTER_NOW`, 동일 종목 다중 attempt, WS REMOVE 직후 완성되는 가격, 완료봉 누락, 세션 불일치, 동일 봉 target/stop 충돌을 포함한다. source gap 행은 분모에 남고 수익/손실 값은 null이어야 한다.
2. 장후 source date별로 probe result의 캡처 digest와 캡처 해시가 attempt별로 대사되고, 기계 `BLOCK/RECHECK`에 대해 완료봉 provenance와 10/30/60분 커버리지·비용 결속·첫 도달 상태가 재현 가능해야 한다. 첫 `RECHECK` 뒤 재판정된 경우 결과 1건에 검증된 캡처 2건이 결속될 수 있으므로 1:1 건수 강제는 하지 않는다. 오늘 12:56~13:20 표본은 장후 완료봉 보강 전후의 **동일 172건**에서 재측정한다. 후행 경로가 끝내 없는 건은 누락 사유로 남기며 정상 판정으로 포장하지 않는다.
3. 최초 네 결손을 각각 닫는다. 승률 후속은 train/holdout 날짜와 고유 선정 기회·후보 허들을 같은 대상일 영수증으로 확인하고, 원천·비용은 제외 사유 감소와 평가 가능 경로를 동일 시도 기준으로 확인한다. direct full-machine은 운영 경제성 결속 모집단·독립 후보·해당 family closure 영수증으로 판정한다. 어느 하나만 개선되어도 나머지를 완료로 표시하지 않는다.
4. 정책 출력은 수집 완성도, 후보 선별, holdout, staging, 다음 PREOPEN 및 실제 PID 소비를 독립 영수증으로 확인한다. 실제 주문·체결·순익은 이 반사실 기회 측정과 별개로 판정한다.

## 2026-09-29 구현·리뷰 기록

- 발견 claim을 발행 시점에 source-only 영수증으로 남기고 기존 스캐너 probe 결과·감시 편입 영수증에 해시 검증된 기계 캡처 digest를 보존했다. 캡처에도 단계·발견 원천 SHA·route를 넣었다. 장후 파이프라인 가격 단일 스캔에서 claim·결과·편입 영수증을 함께 수집하여 exact digest·종목·발견 원천·route·claim count·action으로 대사한다. 첫 `RECHECK`와 재판정은 별개 캡처이고 결과 1건의 중복 기회로 합산하지 않는다.
- 장후 `main_machine_policy`의 독립 기계 모집단에 기존 `ka10080` 완료 1분봉을 연결했다. 캡처의 snapshot과 broker/market-data route가 일치할 때만 프리마켓 `_NX`, 정규장/통합 애프터마켓 `_AL`, KRX 단독 접미사 없는 요청을 사용한다. source-only 조회는 일자별 최대 512개 고유 경로로 제한하고 초과, route 불명, 빈 응답, 잘린 continuation은 명시적 source gap으로 남긴다. 완료봉 캐시는 캡처 집합 해시·가격 원천·세션·요청 코드로 검증하며 승률 보고서와 장후 단계 verifier가 동일 생성 해시를 확인한다.
- 실제 9/29 원본에는 `ai_market_snapshot_v1`이 `exact_payload` 안에 중첩된 형식과 `exact_payload` 자체인 형식이 공존한다. 두 형식 모두 snapshot ID·종목·venue/session·broker/market-data route가 캡처 문맥과 일치할 때만 사용한다. 14:21 KST까지 증가 중인 원본 4,375건을 읽기 전용으로 점검했을 때, 정확한 요청 route가 확인된 고유 종목·세션 경로는 347개였다. 이 숫자는 장후 완료봉 수신이나 경제성 결속의 성공 건수가 아니다.
- 파이프라인 가격은 정확한 요청 코드가 없으면 이 기계 완료봉 모집단을 완성하지 못한다. 첫 판정 뒤 가격 공백, 세션 불일치, 미완성봉, 비용 결손은 `CENSORED_OR_SOURCE_GAP`으로 보존한다. 보고서는 행동별 캡처·10/30/60분 경로 커버리지·첫 도달 가능 수와 캐시 상태를 분리 집계한다. 코드 수리는 독립 날짜, train 후보 30개, direct full-machine 운영 경제성 결속을 충족했다고 뜻하지 않는다.
- 현재 기계 캡처에는 실제 주문 stop 거리가 없으므로 결과 행의 `outcome_stop_owner=fixed_counterfactual_entry_boundary`, `outcome_stop_distance_pct=-0.70`으로 기존 반사실 경계를 명시했다. 이는 실제 체결·실제 stop·실현손익 영수증이 아니다.
- Kiwoom 공식 참조 확인: 2026-09-29 13:52 KST에 [Kiwoom 공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API) commit `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json` `ka10080`, `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime`, Postman을 확인했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없었다. 실제 REST 요청 구성은 기존 공용 client를 재사용하며 이번 변경은 요청 route 선택·완료봉 후행 소비에 한정한다.
- 남은 수용: 배포된 producer/PID에서 새 digest 영수증이 자연 생성되고 9/29 장후 완료봉 캐시·`main_machine_policy` stage가 생성된 뒤, 위 172건을 동일 시도 기준으로 재측정한다. [오늘 체크리스트](../checklists/2026-09-29-stage2-todo-checklist.md)의 `[MachineNonentryOutcomeLineageNaturalAcceptance0929]`가 수용 owner다. 배포·재기동, 과거 장후 재실행, 실주문·정책 변경은 이 코드 작업의 완료 주장에 포함하지 않는다.
- 리뷰·검증: 결과 이중 기록 위험을 기존 스캐너 `zero_base_probe_result` 영수증 보강으로 해소했고, source-invalid 캡처, 동일 요청 코드의 세션별 빈 응답, 완료봉 응답의 요청 코드·기준일 불일치, 512경로 초과, 캐시 변조, 중복 캡처, 후행 첫 가격 공백을 회귀 대상으로 추가했다. 관련 877개 pytest, 수정 후 장후 캐시 검증 1개 pytest, Python compile, `git diff --check`, 문서 링크 확인 및 체크리스트 print-only parser를 통과했다. 테스트 중 실제 Kiwoom REST 조회, 주문, 장후 작업 재실행은 수행하지 않았다.

## 2026-09-29 14:53 KST 배포·기동 영수증

- 리뷰 후 추가 결함 없이 후행자료·스캐너·캡처·장후 단계 및 인접 런타임 1,314개 pytest, 영향 Python compile, `git diff --check`, 체크리스트 print-only parser를 재검증했다. 공식 Kiwoom HEAD는 `953e5dbff123f437ab4d11a78a95191a685eb51f`로 기존 검토 revision과 같았다. 실제 REST 조회나 주문은 테스트에 포함되지 않았다.
- 검증한 17개 코드·테스트·문서 파일을 commit `5aa9eca96747a5f0bf68a68d25b939db6bd8487d`에 봉인했다. 미추적 9/28 원천 재구축 전 백업 2개와 별도 세션의 새 `test_sniper_scale_in.py` 수정은 이 릴리스에 포함하지 않았다. 불변 릴리스는 `/home/ubuntu/KORStockScan-runtime-releases/machine-nonentry-lineage-20260929-5aa9eca9`이며 이전 선택 영수증은 `tmp/machine-nonentry-selection-before-20260929T1450.json`에 보존했다.
- `restart --print-plan`과 9/29 `postclose --print-plan`, 8개 cron 경로를 확인하고 승인된 Main 재기동을 수행했다. 새 PID `1372580`의 `/proc` cwd와 정책 bootstrap 검증이 선택 릴리스와 일치하며 `--check-release-set`이 PASS다. 두 비활성 장후 systemd 서비스도 이 릴리스로 pin을 갱신했고 timer는 active이며 수동 장후 계산은 실행하지 않았다.
- 재기동 뒤 14:53:17~19 KST의 PID `1372580` 기계 캡처에서 `zero_base_probe_machine_only_v1` 단계와 해시가 실제 기록됐고, 14:53:21까지 probe 결과 `assessed` 2건에 캡처 digest가 붙었다. 기동 직후 `runtime_dependency_missing` 5건 이후 평가가 진행됐지만, 이 짧은 창은 장후 완료봉 수신·비용 결속·정책 승격·실현손익의 증거가 아니다. 다음 수용은 체크리스트 `[MachineNonentryOutcomeLineageNaturalAcceptance0929]`에 남는다.
