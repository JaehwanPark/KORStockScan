# Main 보조판정 compact 계약 운영 연결·장중 적용 구현계획 — 2026-10-08

## 1. 목적·작업 범위

실제 AI 연구에서 개선된 네 경로에 **프롬프트 + 입력 변환 + 응답 스키마 + 원 ID 복원·검증**을 묶은 보조정책을 적용한다. 구현 후 코드리뷰·수정·재검증, 정식 배포·재기동, 장중 발행, 실제 요청 소비, 다음 장후·기동 승계까지 하나의 인계 경로로 설계한다.

이번 사용자 요청은 **구현계획 수립 후 리뷰·보완**이다. 이번 문서 작성으로 코드 변경·추가 AI 호출·정책 발행·배포·재기동·장후 재생성을 실행하지 않는다. 후속 실행 시 같은 작업에 이미 주어진 배포·재기동 승인은 해당 범위에서 승계하며 불필요하게 재확인을 요구하지 않는다.

- 실행 owner: [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry`. 아래 AC0~AC7은 이 owner의 구현 단계이며 별도 OPEN을 만들지 않는다.
- 연구 기준: [연구·장중 적용 계획](main-auxiliary-prompt-research-and-intraday-adoption-plan-2026-10-08.md) §7·§13, [최종 실행 검토](../audits/main-auxiliary-prompt-research-execution-review-2026-10-08.md)의 3차 완결 비교.
- 우선 계약: 사용자가 승인한 실제 ask·비용 .0023·30분 이내 비용 후 +.4%·soft −3% 선도달의 W/F/U와 누적 PASS 승률. EV·손익비·최소 표본/일수·holdout·기존 제출 통과 조건을 새 채택 요건으로 붙이지 않는다.
- 기계의 정책 목록·독립 탐지·확인점·가격/수량/보유·청산 정책은 이 작업의 변경 대상이 아니다. `ENTER_NOW` 이후 보조판정 경로만 변경한다. 보호조건과 TTL은 현재 계약을 유지한다.
- REST/WS 절감, 평가루프 지연 개선, 원천 진단, episode 영구 OFF의 별도 작업을 보존한다. Main 배포가 퇴역 widget/episode 서비스를 복원하거나 중지된 자동 관리를 재개해서는 안 된다.

## 2. 적용 후보와 출발 증거

최종 연구 보고서:
`data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/reports/f9ba2741499504163b7a68964839b482cc8a794c4cb5178fba8d7a2cc2798e7f.json`.

연구 기준 부모는 `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`이다. 이는 착수 비교 기준이며 배포 시점의 최신 부모/PID 영수증을 대신하지 않는다. 네 경로의 개선 근거는 총 14개 확인점이고, 문구 연구 60쌍·응답 계약 연구 65쌍·AFTER 가설 연구 32쌍은 모두 유효하게 완료했다.

| 구분 | 정확 scope | 연구 후보 | 대조→후보 PASS 승률 | 함께 보존할 해석 |
| --- | --- | --- | --- | --- |
| 삼성 애프터 | `samsung\|AFTER\|ALL\|SOR` | H5 | 2/3→3/4 | 실패 차단 증가가 아니라 승리 1개 복원 |
| 기타 종목 애프터 2만~10만원 | `other_non_fixed\|AFTER\|20000_TO_100000\|SOR` | H5 | 3/4→3/3 | 승리 3개 유지, 실패 1개 차단 |
| 기타 종목 애프터 2만원 미만 | `other_non_fixed\|AFTER\|LT_20000\|SOR` | H5 | 3/4→1/1 | 실패 1개와 승리 2개를 함께 차단 |
| 기타 종목 프리 2만~10만원 | `other_non_fixed\|PRE\|20000_TO_100000\|NXT` | H4 | 1/1→2/2 | 동률 승률에서 승리 PASS 증가 |

`other_non_fixed`는 현행 종목 분류 함수가 정하는 그룹이다. 고정감시 종목을 포함한 모든 비삼성을 뜻하지 않는다. 가격대·시장·거래 경로도 현행 scope 계산을 사용하며 연구 표본 종목명 목록을 별도 allowlist로 만들지 않는다. SOR와 NXT를 서로 바꾸어 적용하지 않는다.

연구 registry 및 평가 연결:

| 키 | 연구 candidate registry SHA256 | 불변 evaluation SHA256 |
| --- | --- | --- |
| H4 기타 프리 | `27646a0bee6e844fb4bcb40ebd757a11f48e1391e6bb1380f9399a1f88c5eba6` | `90b93fc23b604691cd4eb4b151d34036c652f27e703ef60be75ca674056bc317` |
| H5 기타 애프터 두 가격대 | `3515242bd7b49160c9e14739b129812828d0ad06b9a448c4a3bebc0efaf1acd6` | `c56b4667a366d7cae27711fa62bd9eb0aefa23808235eab57cd5b5cdf1602c8d` |
| H5 삼성 애프터 | `f0fa436be38396782364392702370818bc5a803da3b2741bab25edf7246d09bf` | `01744c621c04bac8e9ac08379c656d29c0bc191707bc5626481b9379b1639869` |

기타 애프터 두 경로는 같은 문구를 쓰지만 적용/평가/되돌림은 scope별로 관리한다. 위 registry는 기존 형식으로 등록된 **연구 문구 ID**다. 이 ID만 현재 overlay에 넣으면 연구와 다른 요청이 되므로, 연구→운영 v2 registry 대응을 별도 불변 영수증으로 연결한다.

### 비교 기준을 바꾸어 설명하지 않는다

연구의 대조군은 **기존 판단 문구를 새 compact 계약으로 실행한 것**이다. 운영 중인 기존 512토큰 요청과 같은 대조군이 아니다. 응답 계약 변경만으로도 판정 분포가 달라졌으므로 이번 도입은 네 경로의 **형식과 판단 문구를 함께 전환하는 변경**으로 명시한다.

발행 근거는 `comparison_baseline_kind=incumbent_prompt_under_successor_wire`로 구분한다. 새 형식 내에서 확인한 누적 승률 개선과 원천/전송 계약 동일성을 검증하여 이 전환 경로를 구현한다. 기존 native 요청 대비 우월성 완료라고 표시하거나, compact 대조군이 이미 운영에 적용됐다고 가정하지 않는다. 기존 native 실험의 잘림·무효는 원 증거로 남기고 정상 VETO/TN으로 바꾸지 않는다.

새로운 경제성 문턱이나 구형 512토큰 반복 호출을 전환의 필수 조건으로 추가하지 않는다. 실제 구현이 연구 요청을 바꾸는 경우에는 그 변경된 범위의 정확 요청만 별도 평가한다. 변경된 요청에 옛 응답을 붙여서 동일성을 주장하지 않는다.

## 3. 실제 producer → consumer와 수정 지점

| 위치 | 현재 상태/결손 | 구현 책임 |
| --- | --- | --- |
| [연구 wire](../../src/engine/scalping/reversal_auxiliary_research_wire.py) | 연구 요청에 별칭·schema·출력 지침을 붙이고 원 union 응답으로 복원 | 검증한 순수 변환을 운영/후속 연구의 공통 codec으로 제공 |
| [registry](../../src/engine/scalping/reversal_auxiliary_registry.py) | v1은 typed 입력/schema/validator를 하나의 버전으로 취급, 문구가 원문과 같으면 기존 binding으로 환원 | v1 보존 + compact v2 registry, 형식이 다르면 문구가 같아도 별도 binding |
| [연구 호출 executor](../../src/engine/scalping/ai_decision_quality.py)의 `execute_openai_prompt_v2_candidate` | 원 provider request projection에 실제 instructions/input/schema·생성 설정 기록 | 저장 projection을 기준으로 운영 SDK 직전 요청과 비교; 재검증에 provider 호출 금지 |
| [운영 AI engine](../../src/engine/ai_engine_openai.py) | `_call_openai_safe`가 기존 projector schema와 `registry.prompt`를 직접 비교; `analyze_target`의 evidence/정규화도 기존 응답 가정 | 논리 입력과 전송 입력 분리, 정확 schema·최종 prompt 사용, raw 보존 후 decode·기존 validator·판정 소비 |
| [보조 장중 reader/publisher](../../src/engine/scalping/reversal_auxiliary_intraday.py) | compact 연구 발행 차단, reader code hash 직접 일치 요구, audit가 문구만 바꾼 호환 view 사용 | 검증된 형식 전환 발행, legacy reader 호환 영수증, mixed v1/v2 감사·되돌림 |
| [튜닝/장후](../../src/engine/scalping/reversal_auxiliary_tuning.py)·[운용 장후](../../src/engine/scalping/continuous_reversal_operating_postclose.py) | effective binding과 reader hash 승계, 비교 응답은 기존 typed validator 경로 | v2 요청/원 응답/decoded 결과 재집계, 적용 시간대·평가 근거와 다음 날짜 승계 |
| [AI trace](../../src/engine/scalping/ai_decision_trace.py)·[outbox](../../src/engine/scalping/reversal_operating_outbox.py) | 정확 요청/응답·판정 ID와 중복 방지 소유 | wire와 logical hash를 구분하고 원 요청 identity·기존 예약 상태 유지 |
| [장중 배포 인계](../../src/engine/automation/intraday_release_handoff.py) | 기존 PREOPEN·원 checklist 봉인·release/PID 인계 검증 | 최종 코드/문서 바이트의 정식 인계 및 재기동 전후 검증 |

새 운영 codec 파일은 `src/engine/scalping/reversal_auxiliary_wire.py`, 관련 테스트는 `src/tests/test_reversal_auxiliary_wire.py`를 예정 위치로 한다. 역할은 Main 보조판정의 순수 직렬화·검증이며 `src/engine` 루트에 새 모듈을 만들지 않는다. 기존 research wire의 hash를 참조하는 과거 실험은 불변으로 보존한다. 새 연구와 운영은 공통 codec을 사용하고, 과거 재현을 위한 frozen 연구 코드를 운영에서 호출하거나 계속 별도 발전시키지 않는다.

## 4. 구현 계약

### AC0. 현재 상태와 증거 고정

1. default 작업본·검토용 checkout·선택 릴리스·실제 Main PID cwd/commit, 현재 당일 bundle/overlay/기계 manifest/보조 binding을 확인한다. 기존 작업본 변경은 소유별로 구분하고 다른 세션 코드를 덮지 않는다.
2. 위 네 경로의 `current_registry`를 원 평가와 대조한다. code-only 변경은 정확한 동등성 영수증으로 인계한다. 기계 목록·typed 입력·현행 문구가 바뀐 경로만 재평가 대상으로 분리한다.
3. 최종 연구 보고서·불변 campaign/evaluation·원 snapshot/request/result object ID와 source hash, 원 연구 codec hash를 고정한다. 157쌍 전체를 무실호출 재생 대상으로, 네 경로 14점을 채택 연결 대상으로 명시한다.
4. 연구 한도 이력은 800회 중 653회 차감/640개 실제 응답/13개 미응답 예약/잔여 147회다. 실행 시 store의 최신 사용량을 다시 읽고 예약을 초기화하지 않는다. 정기 장후 100회 및 운영 호출 계약과 분리한다.
5. `research_source_date`, `operating_day`, `publication_date`, `next_target_date`, `confirmation_epoch`, `effective_from`을 구분한다. 원 연구일과 오늘 효력일이 다를 수 있으며, 자정을 넘겨 실행했다고 정책 선택 기준일을 실행 시각의 날짜로 바꾸지 않는다. 현재 부모와 대상 거래일은 실행 시 다시 검증한다.

산출물: 기존 보조정책 디렉터리 아래 내용 hash 기반의 적용 인계 manifest. 현재 부모·scope·원 평가·연구↔운영 registry·reader 호환 영수증·payload parity·code/release를 참조한다. mutable `latest`만으로 발행하지 않는다.

### AC1. 공통 codec과 v2 registry

- 논리 입력 버전은 기존 `continuous_reversal_union_auxiliary_v3`를 유지한다. 전송/응답 버전은 연구의 `auxiliary_compact_citations_v1`와 연결하되 decoder와 논리 validator 버전을 별도로 기록한다. 현재 네 후보는 v6 union 경로이며 검증 없이 v5 또는 단일 신호 구형 계약에 확장하지 않는다.
- v2 registry에 최종 system prompt, base arm, 논리 input/validator 버전, wire/response schema 버전, encoder/decoder 계약 hash, provider/model/max tokens/reasoning 설정, 연구 registry·평가 근거를 고정한다. 출력 지침은 정확히 한 번 포함한다.
- 모델 `gpt-5.4-nano`, `max_output_tokens=1024`, reasoning `none`, temperature 없음 등 실제 연구 전송값을 유지한다. 모델/route/일반 entry/holding endpoint의 전역 기본값을 바꾸지 않는다.
- 기존 v1 문서·ID·정의 hash·기본 binding의 직렬화 결과를 보존한다. `binding()`은 v2 형식을 기존 arm으로 축약하지 않는다. 네 경로 밖에는 v2 전송을 켜지 않는다.
- 모든 입력 사실·단위·시각·신호·price geometry를 보존하고 ID만 결정적으로 별칭화한다. 모든 신호 확인, 알려진 근거, 위험 코드↔근거 대응, PASS의 `observed_machine_signal`을 검증한다. 미래 label, 평가 승률, 과거 AI 응답을 입력에 섞지 않는다.
- 공통 codec의 결과는 `logical_input`, `wire_input`, `wire_schema`, `citation_map`, `final_prompt`와 각 hash를 구분한다. 연구와 같은 사실 이름(`citation_name`)·신호 순서·위험별 schema 분기 순서를 보존한다. 중복/충돌 ID·지원하지 않는 입력 버전은 해당 요청의 계약 오류로 처리하며 다른 scope까지 차단하지 않는다. 실제 연구 요청 바이트가 달라지는 수정은 단순 리팩터링 동등성으로 처리하지 않는다.
- 기존 `G.production_request()`의 논리 입력 반환 계약을 보존한다. 별도 envelope builder를 runtime과 `G.request()`가 공통으로 사용하도록 하고, 재생·검증 호출자는 원 논리 입력을 명시적으로 받는다. 구형 연구 campaign의 이미 기록된 요청 생성/복원 경로는 그대로 재현한다.
- 정상 판정은 원 ID로 복원한 뒤 기존 union validator를 통과해야 한다. 잘림/거부/필드 누락/알 수 없는 별칭/잘못된 risk binding을 임의 PASS·CAUTION으로 보충하지 않는다. confidence는 진단값이다.

### AC2. 실제 호출·응답·trace 연결

1. 기계 판정·원천 검증에는 **논리 입력**을 계속 사용한다. 별도 wire 입력으로 provider 요청을 만들고 실제 전송 prompt/schema/token 설정을 v2 registry와 대조한다. 일반 glossary나 최소형 재시도가 연구 prompt를 바꾸지 않게 한다.
2. `_call_openai_safe`의 기존 projector-schema 직접 비교는 버전별 검증으로 전환한다. v1 분기는 그대로 검증하고 v2만 공통 codec이 계산한 wire와 대조한다. `entry_setup_evidence`를 wire-only 필드로 덮어 기계 판정을 훼손하지 않는다.
3. 원 raw 응답·provider ID·request projection·receipt hash를 먼저 보존한다. decoder 결과는 별도 projection으로 기록하고 논리 validator 이후 기존 PASS/VETO/CAUTION 소비에 전달한다. raw receipt를 decoded 응답의 hash로 바꾸지 않는다.
4. cache/request identity는 실제 prompt/input/schema/model 및 wire/decoder 버전까지 구분한다. 구형 응답이 새 호출의 cache hit로 들어가면 안 된다. 연구의 과거 응답은 오프라인 검증에만 재사용하고 장중 새 신호의 AI 응답으로 사용하지 않는다.
5. 원 신호·claim·bundle·보조 registry/overlay를 provider 예약 직전과 제출 직전에 검증한다. 반환 도중 바뀐 정책을 끼워 맞추지 않는다. 기존 5초 claim·실시간 시계·지연/stale·중복 outbox 규칙을 유지한다. 연구 timeout 30초를 운영 timeout으로 복사하지 않는다.
6. 관측에는 logical input hash, wire input hash, 최종 prompt/schema hash, 원 응답 hash, decoder 버전, decoded hash, runtime registry와 연구 계보를 연결한다. 실제 서명과 다른 합성 provider provenance를 만들지 않는다.

구체적인 연결 순서는 다음으로 고정한다.

- `apply_request()`의 기존 `signal_set_hash` 검사는 원 `logical_input.signals`로 수행한다. 현재 `(assessment, input, prompt, schema)` 반환의 `input`을 별칭 신호로 바꾸면 이 검사가 실패하므로, 기계 계약에 넘기는 논리 view와 provider용 envelope를 분리한다. 원 확인점·정책 ref·대표 신호 ID를 재생성하지 않는다.
- provider 요청 동등성은 prompt/schema 객체만으로 판정하지 않는다. 저장된 연구 projection과 실제 `OpenAIResponseRequest.build_provider_payload()`의 instructions/input **직렬화 바이트**, schema name·strict·instance hash, verbosity, model·reasoning·temperature 생략·max tokens·store를 대조한다. 추적용 metadata와 HTTP/WS 포장·timeout의 허용 차이는 항목별로 기록하고 모델 입력이나 생성 설정 차이를 숨기지 않는다.
- 원 응답 receipt와 outbox `response_received` 기록 → compact 응답의 원 ID 복원 → union validator → `continuous_reversal_policy.compose`의 기존 v6 분기 순으로 연결한다. provider timing/transport metadata를 엄격한 응답 객체에 섞지 않고 별도 병합한다. compact raw, decoded union, 최종 BUY/WAIT를 서로 다른 산출물로 보존한다.
- 현재 [지연 개선계획](main-evaluation-loop-latency-remediation-plan-2026-10-08.md)의 공통 deadline/계측 경로를 사용한다. 코드의 5초 claim 기준은 원 `confirmation_epoch`이며 큐·전송·응답·decode·제출 시각까지 포함한다. 이미 만료한 요청을 provider에 보내거나 decoder 완료 시 TTL을 새로 시작하지 않는다. runtime timeout은 현재 상한과 남은 수명 범위에서 처리하고, 늦은 응답은 증거만 보존한다. 별도 지연 정책이나 추가 재시도를 만들지 않는다.

### AC3. 구형 정책·reader 호환성과 감사

**선행 결함:** `inherited()`와 `validate_record()`는 현재 I/G 파일 hash가 과거 보고서/overlay의 reader hash와 같아야 한다. registry/reader를 수정하면 새 네 경로 발행 전부터 기존 정책 읽기가 실패할 수 있다.

- 원 보고서·registry·overlay를 수정하거나 과거 hash를 최신 hash로 덮지 않는다. 검증된 이전 불변 릴리스와 새 reader 사이의 **정확 부모별 호환 영수증**을 별도로 발급한다.
- 영수증은 원 source/report 바이트 hash, 이전 reader hash 집합, 새 reader/codec hash 집합, 원 bundle/overlay, 기존 전체 binding, v1 입력·응답 해석/유효기간 동등성 검사 결과를 결속한다. 알려진 부모의 검증된 전환만 허용하며 임의의 code hash 차이를 일반 허용하지 않는다.
- `inherited`, `current`, `validate_record`, `effective_bindings`, `validate_decision`, `validate_submit`, 소비 영수증, rollback, 장후 reader가 같은 버전 규칙을 쓴다. cache도 검증한 세대/reader/registry에 묶는다.
- `audit_observation()`은 원 wire/request/response를 검증하고 codec으로 논리 view를 만든 뒤 기존 기계 감사를 호출한다. 현재의 “문구만 기본값으로 치환”하는 방식으로 compact 입력·응답까지 통과시키지 않는다. 저장된 원 관측은 변경하지 않는다.
- 과거 요청은 당시 bundle/overlay/codec으로 감사한다. 새 정책으로 옛 VETO·ready를 다시 주문 의도로 만들지 않는다. 철회된 overlay의 아직 미제출 claim은 기존 철회 규칙으로 차단한다.
- 호환 영수증은 원 자료→새 reader 검증의 단방향 연결이다. 원 보고서를 새 영수증에 다시 의존시키는 순환 hash를 만들지 않는다. registry/codec/호환 영수증 자체의 변경·소실은 실제 loader cache와 새 PID 양쪽에서 검출되어야 하며, report 파일의 stat만 같은 경우에도 검증되지 않은 registry를 허용하지 않는다.

### AC4. 연구 근거 → 운영 발행

현재 `publish()`의 compact 연구 차단을 삭제하는 방식으로 구현하지 않는다. 기존 native 비교 경로와 별도로 **검증된 응답 계약 전환** 경로를 추가한다.

발행 입력은 네 경로를 명시한 불변 인계 manifest다. 다음을 모두 검증한다.

- 평가가 `development`가 아닌 H4/H5의 불변 실제 비교이며, 원 요청/응답을 재집계한 유효 공통 쌍과 `T.improves()` 결과가 일치한다. 응답 계약 원인 분석 65점은 개발 증거로만 참조한다.
- 현재 부모/기계 manifest/해당 scope의 실제 기존 registry가 연구 기준과 맞거나 검증된 동등성 인계가 있다. 형식 전환의 대조군 종류를 명시한다.
- 원 연구 registry→신규 운영 registry mapping, 최종 prompt와 encoder/schema/decoder, 연구↔운영 payload parity, 원 응답 재검증 결과가 일치한다. 신규 ID만 생겼다는 이유로 전체 AI 재호출이나 원장 복제를 요구하지 않는다.
- 모델이 보는 요청과 결과 해석이 같다는 증명 없이 request ID·registry 이름·코드 파일명만 바꾸어 cache를 재사용하지 않는다. 추적용 metadata가 달라지는 경우에도 원 영수증과 명시 대응을 남기고 기존 정확 요청 ID를 수정하지 않는다. 동등성 증명이 없으면 해당 요청만 새 요청으로 처리한다.
- 변경 집합은 표의 네 scope에 한정한다. 비교에서 열위인 다른 scope나 기존 연구 보고서의 다른 개선 행을 함께 발행하지 않는다. 기계 목록 재선정과 제출/수량/계좌 보호 변경을 포함하지 않는다.
- 여러 evaluation을 하나의 명시 인계 manifest에 결속하여 한 번의 CAS로 발행한다. 기존 `expected_parent`는 기계 bundle이 아니라 보조 overlay predecessor라는 점을 구분하고 두 부모를 모두 확인한다. 현재값과 충돌하면 최신 값을 다시 읽고 변경된 scope만 대조한다.

동시 발행·복구 계약:

- 현재 보조 `publish()`는 `auxiliary/publisher.lock`, 기계 `activate()`는 상위 `publisher.lock`을 사용한다. 보조 lock만 잡은 동안 기계 부모가 바뀔 수 있으므로 두 current를 함께 검증·교체하는 짧은 임계구역을 둔다. 공통 순서는 기존 장후 호출 순서와 같은 **보조 lock → 기계 lock**으로 고정한다. `stage()`는 내부에서 기계 lock을 잡으므로 그 호출을 다시 같은 lock으로 감싸지 않는다. 변경한 writer 사이의 반대 순서가 없는지 검증하고 실제 AI 호출·157쌍 재생·전체 원장 조회는 lock 밖에서 끝낸다. 기계의 탐지 정의·경제성 선택·보호조건은 변경하지 않는다.
- `transition_manifest_sha256`로 중복 실행을 식별한다. 모든 불변 의존 자료 기록 → 원 부모/기존 binding 재검사 → generation 기록 → current 교체 → readback 순서로 수행한다. current 교체 후 readback 전에 프로세스가 죽어도 같은 명령이 새 세대나 새 호출을 만들지 않는다. 이미 다른 후속 세대가 있으면 과거 포인터를 덮지 않는다.
- 각 scope의 원 `current_registry`·새 registry·evaluation·before/after binding과 적용 시각을 manifest에 남긴다. 연구 부모가 같아도 현행 보조 binding이 바뀌면 그 scope를 다시 대조한다. 일부 scope만 원천/동등성 확인에 실패하면 원 네 경로의 유효 부분집합을 명시한 새 manifest로 진행할 수 있으며 제외 이유를 남긴다. 다른 경로의 개선을 무조건 대기시키거나 부적격 경로까지 자동 발행하지 않는다.

완성된 v2 registry와 호환 영수증을 먼저 기록하고 마지막에 current pointer를 원자 교체한다. 등록 실패·검증 실패·CAS 충돌 시 기존 current가 유지되어야 한다. 정확 누적 PASS 승률 개선/동률 TP 증가만 사용하며, raw 승률 우선에 따라 2만원 미만에서 승리 2개도 차단되는 사실을 함께 보관한다.

### AC5. 리뷰·회귀·성능 검증

구현→self review→수정→재리뷰→관련 검증을 반복한다. 종료 증거는 대상 diff뿐 아니라 다음 producer/consumer 계약을 포함한다.

| 검증 | 통과 조건 |
| --- | --- |
| 과거 호환성 | v1 registry IDs/요청/응답/선택 결과 보존, 현재 부모의 모든 binding 읽기 성공, v2는 명시 네 경로에서만 활성화 |
| 연구 재현 | 세 연구 157쌍의 입력·schema·원 응답 decoding/분모 재현, 네 후보 14점의 판정·승률 일치, 미래 필드 혼입 0 |
| 실제 전송 경로 | SDK 경계 fake transport로 `analyze_target`→registry→실제 요청 projection 대조, prompt suffix 중복/구형 512 복귀/잘못된 schema hash 0 |
| 논리·전송 분리 | 원 `signal_set_hash`와 기계 ref 불변, compact ID는 provider envelope에만 존재, raw/decoded/최종 판정별 hash 재현 |
| 응답 결손 | 잘림·refusal·잘못된 별칭·누락 신호·위험 인용 불일치는 진입 허용 불가, 원 receipt 보존, 정상 TN으로 집계하지 않음 |
| 세대 전환 | 구형 in-flight claim의 원 binding/남은 TTL 유지, 새 claim은 새 binding, 철회/재기동/중복 응답의 주문 의도 중복 0 |
| 발행 | 다른 scope/evaluation 또는 변조 manifest 거부, 최신 부모 CAS 충돌·부분 파일 기록 실패 시 원 current 유지 |
| 동시성·재실행 | 기계 활성화와 보조 발행/장후가 경합해도 부모 혼합·lock 교착 없음, pointer 교체 직후 crash 재시도는 같은 결과, 정상 다른 scope·새 후속 세대 보존 |
| 되돌림 | 한 scope 철회 시 다른 scope·진행 claim 유지, 공통 codec 결함은 영향받는 v2 전체 철회, 다음 부모에 상속된 v2도 현재 부모에서 복원 가능 |
| 장후/다음 날짜 | effective binding과 적용 시각별 비교, 미완료/무표본 carry, v2 재부팅 소비·구형 rollback 감사 재현 |
| 혼합 비교 | 같은 campaign의 v1/v2 양쪽 요청을 각자 전송·decode, 구형 연구 요청 ID 불변, suffix/encoder 중복 적용 0, invalid/U 제외와 TP/FP/FN/TN 분모 보존 |
| 날짜 경계 | 10/8 정책의 장후가 자정 이후 실행되어도 최종 10/8 binding 승계, 사전 생성한 장후 산출물 이후 추가 overlay 발행은 오래된 준비로 탐지, 이전 PRE/AFTER 신호 재발행 0 |
| 지연 | codec의 추가 처리시간을 기존 평가루프 계측으로 비교, 불필요한 전체 원장/WS 복사·provider 재시도 없음; 5초 claim과 운영 timeout 그대로 |

기존 `test_reversal_auxiliary_tuning.py`, `test_reversal_auxiliary_research.py`, `test_reversal_auxiliary_research_wire.py`, `test_reversal_extended_policy.py`, `test_offline_comparison_store.py`, `test_ai_engine_openai_transport.py`, `test_intraday_release_handoff.py` 및 실제 trace/submit 소비 테스트를 변경 범위에 맞게 실행한다. Python compile·`git diff --check`를 수행한다. wrapper를 바꿀 경우에만 `bash -n`과 해당 계약 검사를 추가한다.

기존 연구의 76 PASS를 새 운영 통합의 PASS로 전용하지 않는다. 관련 테스트가 통과하면 같은 검사를 이유 없이 반복하거나 무관한 거래 suite/보고서를 재생성하지 않는다.

### AC6. 정식 배포·재기동·장중 활성화

1. 리뷰가 끝난 코드와 최종 문서 바이트를 불변 릴리스로 준비한다. 동일 파일을 다른 작업이 수정했다면 최종 통합 diff에서 겹치는 producer/consumer를 다시 검토한다. 미검토된 전체 작업본을 묵시적으로 함께 배포하지 않는다.
2. 기존 reader 호환 영수증으로 새 릴리스가 **현재 정책을 그대로 읽을 수 있음**을 실제 실행 cwd와 data anchor에서 먼저 검증한다. 이 상태에서 기존 정책을 유지한 채 정식 장중 release handoff를 준비한다.
3. Main 배포·재기동은 기존 승인 범위와 현재 bootstrap/기동 조건을 승계한다. 기존 PID·outbox·진행 요청을 인계하고 중복 Main PID가 생기지 않게 한다. episode/widget 영구 OFF·mask·별도 보유 처리 상태를 건드리지 않는다.
4. 새 PID의 cwd/commit 및 기존 정책 소비를 확인한 뒤 AC4에서 검증된 대상 scope의 overlay를 당일 KST `effective_from`으로 원자 발행한다. 기본 대상은 네 경로이며 일부 제외 시 manifest의 명시 부분집합만 적용한다. 새 코드에 대한 정책 발행은 추가 재기동 없이 reader가 다음 새 확인점에서 소비한다. 데이터/registry 변경만으로 구형 PID가 새 decoder를 지원한다고 가정하지 않는다.
5. 정책 읽기, 첫 자연 provider 요청, 원 응답 복원·판정, 제출 전 검증을 각각 확인한다. 첫 신호가 없으면 `not_observed`로 남기며 강제 주문·과거 신호 재발행·shadow 신규 축을 만들지 않는다. 프리 시간이 지났으면 PRE 적용 파일의 유효성까지 확인하고 첫 자연 PRE 요청은 다음 해당 세션에서 확인한다.
6. source/code/decoder 불일치 또는 실제 정책 소비 결함 시 아래의 범위별 되돌림을 수행한다. 보조 정책 복원이 검증된 뒤 필요 시 코드 릴리스를 복구한다. 새 형식 overlay를 이해하지 못하는 구형 릴리스로 먼저 재기동하지 않는다. 원 주문/체결/청산 소유권은 유지한다.

되돌림은 현재 `rollback()` 그대로의 “전체 overlay를 바로 직전 predecessor로 복원”으로 끝내지 않는다.

- 한 scope의 결함은 **현재** 전체 binding 위에서 해당 scope만 검증된 before binding으로 돌리는 새 CAS 세대다. 이후 다른 scope에 적용한 정상 변경을 덮지 않는다. 철회도 `(overlay, scope)`에 연결하여 영향 scope의 미제출 claim만 차단한다. 공통 decoder/registry 결함이면 그 계약을 쓰는 v2 scope 전체가 복구 범위다.
- v2가 다음 날짜 부모에 상속되면 이전 날짜 overlay rollback으로 해소되지 않는다. 상속 manifest가 보존한 scope별 v1 또는 직전 검증 binding을 현재 부모에서 검증하고 새 날짜의 복구 overlay를 발행한다. 대응 자료가 없으면 과거 날짜 current를 복사하지 말고 해당 scope를 명시 오류로 유지한다.
- 코드 되돌림 후보는 배포 전 현재 전체 유효 binding을 실제 cwd에서 읽는지 검증한다. 구형 릴리스가 새로운 rollback 레코드나 상속된 v2를 읽지 못하면 **v2 reader를 지원하는 검토된 릴리스에서 정책만 복원**한다. 현재 부모와 레코드 형식을 읽을 수 있다는 증거가 있어야 구형 코드로 재기동한다. durable outbox/처리된 확인점/원 주문 기록은 되감지 않는다.

`strict_checklist_generation_stale` 방지: 오늘 checklist는 다른 작업도 변경 중이다. 배포 시 최종 바이트와 원 봉인 snapshot을 다시 확인하고 기존 `intraday_release_handoff`의 역사 snapshot·최신 인계 검증을 사용한다. 구형 strict의 hash를 수기로 바꾸거나 detector를 끄지 않는다. 실제 finalization predecessor가 바뀐 경우에만 영향을 받은 terminal을 최소 재봉인하며 EOD/장후 전체를 되돌려 실행하지 않는다. 계획 작성 중에는 재봉인·재기동을 수행하지 않는다.

### AC7. 장후·다음 기동 승계

이 절의 reader/report 구현과 회귀검증은 AC5·AC6보다 먼저 완료한다. 아래의 실제 장후 생성·다음 기동 소비 확인만 배포 이후에 수행한다.

- `auxiliary_report()`는 명시한 `operating_day`의 최종 유효 binding을 읽고 v2 registry/codec/승인·평가 인계를 source receipt로 포함한다. 현재 `effective_bindings(..., day=publication)`와 `current()`의 day 일치 조건을 그대로 쓰면 자정 후 해당 장중 overlay를 놓칠 수 있으므로, 봉인된 해당 거래일의 generation 계보와 cutoff를 조회한다. `publication_date`는 발행일의 날짜 문자열, `generated_at`은 실제 발행 시각으로 보존한다. `stage()`의 부모 조회도 실행일이 아닌 명시 operating 부모와 대조하여 날짜 불일치를 전파하지 않는다. 장중 적용 전후는 원 `confirmation_epoch`와 `effective_from`으로 구분하고 같은 기회를 두 번 합산하지 않는다.
- 장후 후보 비교와 현재 운영 binding을 분리한다. 신규 비교가 미완료라고 이미 적용한 네 경로를 원래 arm으로 덮지 않는다. 연구 잔여 147회를 정기 장후 100회 한도에 합치거나 날짜/세대로 reset하지 않는다.
- `prepare`→`G.request`→`calls`→`expected_request`/`response_projection`→`evaluate` 모두 **각 요청의 registry/wire 버전**으로 dispatch한다. 캠페인 전체의 `research.compact_wire_contract` 하나로 두 arm을 같은 형식이라 가정하지 않는다. v1/v2 혼합 비교, 이미 적용된 v2 현행과 후속 후보 비교, 과거 연구 campaign 재검증을 구분한다. 이전 연구의 특별 변환을 새 v2 요청에 다시 적용해 suffix·별칭을 이중 처리하지 않는다. 기존 누적 membership/request/object ID는 변경 없이 참조하고, 달라진 요청만 새 identity를 가진다.
- 다음 부모는 v2 binding과 지원 reader 버전을 함께 승계한다. 캐시가 없는 새 프로세스에서도 원 source·registry·codec을 모두 찾고 검증해야 한다. report/bundle/reader hash를 연결한 상태에서 기존 terminal→summary→strict/controller→PREOPEN 경로를 사용한다.
- 장후 보고서의 `evaluated_overlay_parent`와 scope별 binding을 다음 부모의 필수 source로 검증한다. 그 뒤 같은 거래일에 새 overlay/철회가 생기면 기존 다음 날짜 준비는 현행으로 인정하지 않는다. 변경된 보조 report→bundle/terminal→기존 준비 인계만 갱신하며 기계 모집단·EOD·실제 AI 전수 호출은 반복하지 않는다.
- registry 외부 참조만 승계하지 않는다. 새 registry, 공통 codec/reader 검증, 연구→운영 대응, scope별 평가·호환·되돌림 자료까지 불변 source 목록과 retention 참조에 포함한다. 공유 store의 object ID를 재사용하고 원 request/result 복제본은 만들지 않는다. 릴리스 교체 후에도 이 참조들을 동일 data anchor에서 읽을 수 있어야 한다.
- 표본이 없는 PRE/AFTER는 기존의 같은 유형 REGULAR 상속 규칙을 유지한다. 별도 표본으로 선택된 네 경로는 독립 scope로 기록하여 REGULAR 상속으로 덮지 않는다. 이번에 REGULAR 후보를 바꾸지 않았으므로 나머지 무표본 경로에 새 compact 정책을 확산시키지 않는다.
- 다음 기동일은 작업의 명시 대상 영업일을 저장소 거래일 달력으로 검증한다. 실행이 자정을 넘기면 원 연구/원천일과 의도한 `next_target_date`를 유지하고 실제 효력일·부모를 다시 확인한다. 실행일의 다음 날을 계산하여 준비 대상을 하루 미루지 않는다. 대상 기동이 이미 지났거나 부모가 전환됐으면 최신 당일 인계로 재검증하고 과거 날짜 current/PREOPEN을 강제로 재사용하지 않는다.
- 자동으로 새 프롬프트를 생성하거나 대형 비교 원장을 다시 만들지 않는다. 현재 공유 store와 정확 요청/응답을 사용하고 바뀐 요청만 증분 생성한다. 활성·되돌림·감사에서 참조하는 연구 자료와 frozen reader를 삭제하지 않는다.

## 5. 단계별 산출물·종료 기준

| 단계 | 선행 | 확인할 결과 |
| --- | --- | --- |
| AC0 | 연구 종료 | 최신 부모/reader/PID·원 평가·예산·대상 scope 고정 |
| AC1 | AC0 | v1 보존, 공통 codec·v2 registry 및 불변 연구 대응 |
| AC2 | AC1 | 실제 호출·raw/decoded·trace/outbox/최종 판정 연결 |
| AC3 | AC1 | 원 부모와 과거 관측의 reader 호환·감사·되돌림 |
| AC4 | AC0~AC3 | 네 경로만 허용하는 전환 manifest와 원자 발행 검증 |
| AC7 구현 | AC1~AC4 | 장후 reader/report·다음 날짜 승계·cold-start 회귀 준비 |
| AC5 | AC1~AC4·AC7 구현 | 미해결 in-scope 결함 0, 필요한 회귀·성능 검사 통과 |
| AC6 | AC5 | 선택 release/새 PID/overlay loaded 확인, 자연 요청은 관측 여부 구분 |
| AC7 자연 확인 | AC6 | 다음 장후와 다음 기동의 v2 승계 검증·자연 결과 별도 확인 |

코드 종료·선택 릴리스·PID 로드·첫 자연 호출·주문/체결·실현 손익을 각각 보고한다. 코드·정책 연결 검증에 실제 주문/수익이나 추가 경제성 문턱을 요구하지 않는다. 첫 요청이 아직 없는 세션은 자연 소비 완료라고 표시하지 않는다. 장애 시 owner artifact·정확 이유·복구 행동·닫힘 검사를 같은 실행 owner에 남긴다.

## 6. 계획 리뷰에서 반영한 보완

- compact 형식이 판정을 바꾸는 것을 단순 문구 교체로 취급하지 않도록 전환 범위·대조군 의미를 명시했다.
- registry/reader 수정만으로 기존 부모가 깨지는 code hash 인계를 선행 단계로 추가했다.
- 모델 전송, raw receipt, decoder, 기존 validator, audit, outbox, 장후 승계까지 연결했다. 연구 전용 decoder를 호출했다는 사실만으로 운영 연결 완료라고 판단하지 않는다.
- 세 연구 평가를 한 current pointer에 붙이는 다중 평가 manifest, 정확 네 scope 허용, 부분 실패/동시 발행/rollback 순서를 명시했다.
- 과거 연구 hash와 v1 registry ID를 보존하고, 새 codec 위치·후속 연구 공통 사용·공유 원장 재사용을 정했다.
- 연구 한도·정기 한도·운영 timeout을 분리하고, 무표본 상속·PRE 미관측·영업일 변경을 처리했다.
- 다른 세션의 REST/WS/episode 작업과 최종 checklist 봉인을 보존하는 배포 순서를 포함했다.

문서 검증은 로컬 링크·현재 단일 owner·scope/registry/evaluation 근거·권한/예산 일관성·공백 검사와 print-only backlog parser로 종료한다. 이번에는 운영 테스트·추가 모델 호출·장후 보고서 재생성·Project/Calendar 외부 동기화를 실행하지 않는다.

최초 계획 검증: 새 구현계획과 연구계획의 로컬 링크 29개 정상, 네 scope의 registry/evaluation·승률·14점 및 완료 157쌍을 불변 보고서와 대조했다. print-only parser는 21개 항목, 기존 실행 owner 1개, 경고 0건이었다. 이는 계획 문서 검증이며 운영 통합 코드나 현재 PID의 적용 완료 증거는 아니다.

### 6.1 후속 리뷰·보완 — 2026-10-08

| 발견한 계획 결손 | 코드 근거 | 보완·닫힘 검사 |
| --- | --- | --- |
| 논리 신호와 전송 별칭의 경계 불명확 | `apply_request`는 `input.signals`를 기계 hash와 비교 | AC1/AC2에 envelope 분리·raw→decode→compose 순서, AC5에 원 신호 불변 검사 |
| prompt/schema 일부 비교만으로 실제 요청 동등성 과대 주장 가능 | 연구 executor와 운영 `build_provider_payload`가 각각 전송 설정 조립 | SDK 직전 전체 모델 입력/생성 설정 및 명시 metadata 차이를 검증 |
| 기계/보조 부모 동시 교체와 재실행 공백 | 두 publisher가 서로 다른 lock, 기존 idempotency는 단일 evaluation 기준 | AC4에 공통 lock 순서·다중 평가 manifest ID·crash/CAS 반례 |
| scope별 복구 약속과 전체 rollback 구현의 불일치 | `rollback()`은 전체 `older['bindings']` 복원 | AC6에 현재 세대 위의 부분 복구·scope별 철회·상속 후 복구·구형 코드 제한 |
| 자정 후 승계 누락·준비 뒤 정책 교체 미검증 | 장후가 `day=publication` 조회, `current`는 날짜/부모 불일치 시 None | AC0/AC7에 거래일별 generation cutoff·장후 최종 overlay 검증·영향 부분 재발행 |
| 다음 릴리스에서 외부 의존 자료 누락 가능 | 장후 source 목록은 registry/evaluation/overlay 중심 | AC3/AC7에 비순환 호환 증거·codec/평가/되돌림 참조·cold-start 검사 |
| 구형·신형 혼합 비교 및 과거 재현 경로 불명확 | `prepare`의 연구 wire 변환과 `expected_request`/`response_projection`이 각기 요청 재구성 | AC1/AC7에 논리 반환 계약 보존·요청별 버전 dispatch, AC5에 이중 변환/분모 회귀 |

채택 승률 기준은 유지한다. 위 보완은 승인된 보조정책을 정확하게 전송·발행·승계하기 위한 구현 요건이며, 구현과 운영 검증은 후속 실행 범위다.

후속 문서 검증: 로컬 링크 31개 정상, 연구 네 경로/14점·완료 157쌍과 registry/evaluation 일치, 공백 검사 통과. print-only parser는 21개 항목·현재 실행 owner 1개·경고 0건이다. 이번 리뷰에서는 코드 테스트·추가 AI 호출·정책 발행·배포·재기동을 실행하지 않았다.


## 7. 승인된 구현 실행 — 2026-10-08

후속 사용자 지시로 구현·리뷰·배포·재기동을 실행한다. 배포와 재기동의 하한은 **2026-10-08 15:00 KST**이며, 그 이후 검증이 끝나면 즉시 수행한다. 위 계획 작성 당시의 “문서만 검증/운영 미실행” 문구는 당시 이력이다.

공통 codec/v2 registry, 실제 SDK 입력과 원본/해독 응답 분리, exact-source v1 reader 호환, 다중 평가 원자 전환, 경로별 복구와 다음 날짜 상속을 구현했다. 새 모듈은 기존 보조정책 소유 패키지 `src/engine/scalping`에 두며 engine root는 확장하지 않는다. 구형 outbox·기계정책의 고정 코드는 보존하고 별도 해독 영수증이 원본 outbox의 응답 binding을 참조한다.

검증·배포 결과는 [실행 리뷰](../audits/main-auxiliary-compact-intraday-adoption-review-2026-10-08.md)를 따른다. 다음 장후 생성과 다음 기동의 자연 소비는 해당 시점의 증빙이며 코드 회귀와 혼동하지 않는다. 다음 대상 영업일은 저장소 달력 기준 2026-10-12다.
