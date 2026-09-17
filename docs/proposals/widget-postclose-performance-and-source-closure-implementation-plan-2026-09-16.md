# 위젯 장후 평가 원천 폐쇄·성능 개선 상세 구현계획

상태: 09-16 계획·원천 점검을 바탕으로 09-17 사용자 명시 구현·리뷰·commit/push·배포·기동 지시를 수행한다. 구현 및 검증·배포 receipt는 [09-17 구현 기록](../audit-reports/2026-09-17-widget-postclose-source-closure-implementation.md), 자연 acceptance의 현재 실행 owner는 [09-17 checklist](../checklists/2026-09-17-stage2-todo-checklist.md)의 `[WidgetPostcloseEvaluationPinAcceptance0916]`이다.

목표: 생산·소비 결손을 먼저 구분하고, 튜닝의 입력 기간·정책 탐색·비용·holdout 품질을 최대한 유지하면서 장후 CPU·메모리·재조회 비용을 줄인다. 기존 모듈 안에서 작업본을 구현·리뷰·검증하고, 통과한 동일 코드 세대만 배포본에 인계한다.

## 1. 확정된 현상과 아직 확정할 수 없는 원인

점검 기준일은 `2026-09-16`이다. 아래 census는 현재 config의 research-watch 13종목에 대해 종료된 당일 파일 약 4.28MB만 읽었다. 전체 과거 원천은 재생성하거나 전수 파싱하지 않았다.

| 항목 | 현재 근거 | 판정 |
| --- | --- | --- |
| research-watch 원천 생산 | `data/monitoring/widget_research_watch/widget_research_watch_<symbol>_20260916.jsonl` 13개 모두 존재 | 원천 생산 자체가 0인 것은 아님 |
| 당일 raw row | 1,760행: PASS 1,065 / SOURCE_ERROR 598 / SOURCE_QUALITY_BLOCKED 97 | raw 존재와 유효 source coverage는 다른 상태 |
| 원천 session | 1,760행 모두 `KRX_REGULAR` | 이 원천으로 통합 애프터마켓 coverage를 증명할 수 없음 |
| consumer가 찾는 advisory 파일 | 13개 모두 `data/report/widget_symbol_advisory_observation/widget_symbol_advisory_<symbol>_20260916.jsonl` 없음 | 서로 다른 역할·경로·schema를 소비하고 있음 |
| 당일 observation catalog | dated runtime policy의 `observation_symbols`는 기존 `006800/010140/080220/475150` 4개, 실행 `symbols`는 0개 | 미등록 research-watch는 runtime advisory collector 대상이 아님 |
| raw collector 범위 | 09:00~15:31, symbol당 quote/BBO/bar 3요청, local budget 18/min에서 headroom 3 보존 | 13종목의 nominal cycle은 156초 + 실제 요청시간. 종목별 매분 1행 계약이 아님 |
| bar 보존 | 최대 400개 completed bars를 파싱한 뒤 `latest_completed_bar` 하나만 저장 | 조회 간격 사이 OHLCV를 저장하지 않아, 이미 받아온 자료를 재사용할 기회를 잃음 |
| SOURCE_ERROR 원인 | 598행 모두 `RuntimeError` 타입만 기록 | budget/admission/HTTP/응답 등 세부 원인은 현재 receipt로 확정 불가 |
| BLOCKED 원인 | completed bar stale 93 / missing 4 | source freshness/coverage 결손은 실제로 존재 |
| local auto-policy 평가 | 22종목·24세션·55,230 후보. raw 42,789행, accepted 34,965행 | research universe 19개와 같은 분모가 아님 |
| signal research 범위 | 기존 4 + research-watch 13 + completed-daily 발견 2 = 19종목 | 모든 대상에 계산 비용이 발생 |
| 신호 연구 계산 | 정책 1,536개, cap 1~5. 72거래일 = calibration 56 + holdout 16 | 19종목 최대 145,920 policy-cap 판정; cap마다 분봉을 재생하는 것은 아니며 정책별 full replay 뒤 cap을 집계 |
| 당일 wall time | 최초 run EOD 대기 41분. 마지막 run의 연구는 21:22:26~23:35:13 동안 완료되지 못함 | 대기·분석·실패 재시도를 구분해야 함 |
| 서비스 자원 | CPUQuota 20%, MemoryMax 512MiB, TimeoutStart 무한. 마지막 run CPU 약 27분·memory peak 약 512MiB·swap peak 약 139MiB | quota로 wall time이 늘고 memory pressure도 발생 |
| 마지막 종료 | journal에 `15/TERM`, 최종 연구/apply report 없음 | 정상 평가 완료가 아님. signal 발신자와 최초 계산 hot spot은 현재 로그로 확정 불가 |

앞선 설명의 “research-watch 다수 로컬 관측행이 0개”는 **advisory consumer의 행수가 0이라는 의미로 정정**한다. KRX raw 원천은 이미 생산되었다. 따라서 raw producer가 전혀 동작하지 않았다고 결론내리거나, 경로만 바꾸면 advisory/AM input이 유효해진다고 판단하지 않는다.

### 1.1 정상 부재와 구조 결함의 경계

1. 현재 raw collector는 시장 관측 전용이며 `advisory_generated=false`, entry/exit event 없음이 정상이다. 이 schema를 advisory 행으로 위장하면 결함이다.
2. observation seed가 없어서 특정 신호·episode를 평가하지 않는 것은 정상이다. 그 경우에도 시장 원천의 존재·결손·seed 미평가를 별도로 기록해야 한다.
3. AM calibration에 research-watch 전종목을 넣으면서 producer는 KRX raw만 쓰고, advisory collector는 dated seed가 있는 4종목만 활성화하는 연결은 **prospective AM 축적 경로의 구조 결손**이다.
4. 연구 observation 등록을 실행정책 승격과 결합하면 “연구하려면 승격이 먼저 필요”한 의존성이 생길 수 있다. 관측 universe와 실행 universe를 분리하고, 유효한 frozen 연구 seed의 등록은 주문 권한 없이 수행해야 한다.
5. 598개 오류의 구체적 원인은 미확정이다. 오류 detail producer를 먼저 보완하고 다음 자연 수집에서 owner/API/admission/response 원인을 확인한다. 과거 행의 원인을 추정하여 채우지 않는다.

## 2. 설계 원칙과 품질 손실 한도

- 첫 배포는 clean baseline `2026-06-05` 이후 전체 입력, 현재 1,536개 grid, cap 1~5, 16거래일 독립 holdout을 유지한다.
- 가격 tick, 신호·entry·exit 시각, episode 순서, 비용 계약, source 제외, calibration 양 half, tail guard와 자동승격 조건을 유지한다.
- 성능 개선의 기본 목표는 유효한 기존 입력에서 **정책·episode 결과가 같은 계산**이다. 종목 수 제한, 분봉 thinning, random sampling, holdout 축소, 손실 guard 완화로 시간을 줄이지 않는다.
- source 수정 때문에 유효 모집단이 달라지는 경우 old bug와 동일성을 강요하지 않는다. 새로 포함/제외한 exact symbol/date/row와 근거를 따로 검토한다.
- source가 없으면 error/cadence/seed 이유를 기록한다. 빈 파일·null event·missing cost를 정상 표본이나 zero EV로 만들지 않는다.
- raw 및 기존 exclusion manifest를 보존한다. cache/projection은 원본을 대체하는 거래 증거가 아니며 eviction 후 재계산할 수 있어야 한다.
- 미래 후보를 과거 raw에 적용한 결과는 별도 CF 연구다. prospective 신호·BBO·체결 source와 혼합하지 않는다.
- 기간·grid 축소는 첫 배포에서 하지 않는다. 추후 필요하면 전체 기준 결과에 대한 비교 결과와 품질 손실을 수치로 제시한 후 별도 변경안으로 다룬다.

## 3. 기존 코드의 소유 경계

새 Python 모듈, CLI, collector daemon, DB, service, timer, cron, 필수 report producer를 만들지 않는다. 새로운 작은 함수/field는 아래 기존 owner 내부에 둔다. 무관한 대형 모듈 정리·이동은 함께 하지 않는다.

| 기존 owner | 변경할 역할 |
| --- | --- |
| `src/engine/monitoring/widget_research_watch_collector.py` | raw universe/session census, detail error, 받은 completed bars의 delta 보존, existing snapshot/raw writer 개선 |
| `src/engine/monitoring/widget_symbol_runtime_collector.py` | observation-only universe·seed 처리, 공통 raw 재사용, prospective advisory/lifecycle·compact projection 생산 |
| `src/engine/monitoring/widget_symbol_runtime_policy.py` | 관측 catalog와 실행 catalog의 분리 검증, frozen seed provenance, report source census·hash 소비 |
| `src/engine/monitoring/widget_symbol_signal_policy_research.py` | 종목별 source snapshot/cache, fingerprint, 순차 처리·feature 선계산·day replay 재사용 |
| `src/engine/monitoring/widget_auto_trade_policy_calibration.py` | source inventory, empty/invalid 처리, compact input 소비, 중복 replay와 후보 보존량 축소 |
| `src/engine/monitoring/widget_advisory_calibration.py` 및 기존 paired replay | 같은 raw의 중복 parsing/grouping 제거, 기존 cumulative/paired 의미 유지 |
| `src/engine/monitoring/machine_candidate_lifecycle.py` | 기존 completed-daily discovery·pruning 함수를 재사용; universe 판정을 복제하지 않음 |
| `src/trading/market/session_contract.py` 및 기존 read client/cache | route/session 사실·기존 admission/cache를 재사용; 별 판정기/예산 확대를 만들지 않음 |
| `deploy/run_widget_evaluation.sh` | stage timing/progress, target-date 유지, 재개·실패 상태 기록 |
| 기존 verifier/controller/summary handoff | source census와 새로운 optional cache metadata 호환, final publication ordering·실패 custody 검증 |
| `src/tests` 기존 widget·wrapper·verifier 테스트 파일 | producer→consumer 연결, 결과 동등성·cache 무효화·memory/시간 회귀 검증 |

cache와 projection은 기존 `data/cache`/기존 widget raw·snapshot 영역의 **데이터 산출물**로 둔다. 별 운영 실행 owner나 mandatory report를 추가하지 않는다. 구현 전 현재 IO/helper 구조를 확인하여 기존 파일 포맷·writer를 재사용한다.

## 4. P0 — 원천 생산·소비 폐쇄

### 4.1 source census를 먼저 소비

기존 calibration/research report 안에 symbol × trading_date × session × input-role census를 넣는다. 새로운 독립 audit job은 만들지 않는다.

필드: expected universe/origin, producer 및 실제 code SHA, source path/schema/hash, active collection window, raw/unique-bar/advisory/seeded-episode/eligible row 수, rejected 이유, 누락 시간대, 최초·최종 source time, expected cadence와 실제 cadence, observation seed ID/hash/생성·적용 시각, 소비자 선택 이유.

상태를 `not_enrolled`, `not_yet_effective`, `outside_collection_window`, `raw_only_no_seed`, `producer_missing`, `producer_error`, `route_or_session_mismatch`, `consumer_path_or_schema_mismatch`, `source_valid`, `valid_empty_no_signal` 등으로 분해한다. 이름은 구현 시 기존 canonical labels와 합치며 필요한 parser도 같은 변경에서 수정한다.

계수 계약은 `expected = source_valid + classified_not_applicable + explicit_source_gap`이고, `unclassified=0`이어야 한다. PASS row 0을 자동 정상화하지 않는다. 미수집이 정당한 scope는 사전 universe/window/seed 근거가 있어야 한다.

### 4.2 raw 생산 보완

- 현재 `_collect_symbol_safely`에서 예외 타입만 남기는 대신 endpoint/API ID, source stage, 요청 symbol/route, admission 이유/대기, HTTP/응답 코드, local/shared budget 상태를 기록한다. token·header·계좌정보는 기록하지 않는다.
- nominal 156초 cycle은 sampling cadence로 보존하고, 이를 매분 완전 coverage라고 표시하지 않는다. 예산 확대보다 기존 common market source와 이미 받은 response를 우선 재사용한다.
- ka10080 응답에서 받은 completed bars를 버리지 않고 route/date별 신규 bar delta와 content hash를 보존한다. overlap dedup는 `(symbol, route, session, bar_time, adjustment contract)` 기준이며 conflicting OHLCV는 격리한다.
- 새로 받은 과거 completed bars는 OHLCV 공백 보충에 사용할 수 있다. 당시 quote/BBO·realtime continuity·신호 수신시각은 복원하지 않는다.
- 기존 collector의 수집 scope를 실제 research universe·등록일·거래가능 session에 맞춰 확장한다. current KRX-only raw를 AL/AM으로 재라벨하지 않는다. AM source는 기존 authoritative integrated route로 실제 생산한다.
- REST/WS 요청·parser·REG 또는 recovery 변경 전에는 [Kiwoom API Data Contract](../kiwoom-api-data-contract.md)의 Official Kiwoom Reference Gate를 수행하고 upstream SHA·경로·조회시각을 기록한다. 현재 계획 작성은 요청 변경을 실행하지 않는다.

### 4.3 observation 등록과 prospective seed

- runtime collector는 기존 실행정책 목록만으로 research source 기대집합을 결정하지 않는다. validated research-watch config와 completed-daily discovery를 같은 기존 universe helper로 읽는다.
- 모든 등록 종목은 market observation을 생산하거나 명시적인 비대상/결손 receipt를 남긴다. seed가 없을 때도 raw 수집 대상에서 조용히 빠지지 않는다.
- advisory/episode는 기존 검증된 observation seed가 있을 때만 기존 kernel로 평가한다. seed가 없으면 `raw_only_no_seed`, `entry_event=null`, `exit_event=null`을 남기고 주문 대상으로 추가하지 않는다.
- bootstrap은 기존 연구 producer의 검증 가능한 diagnostic/incumbent seed를 observation-only catalog로 고정한다. 실행 승격은 원래 full-cost/holdout/source 기준을 따로 통과해야 한다. seed 등록에 실행 승인 결과를 요구하여 축적이 영구 차단되는 연결을 제거한다.
- seed schema에 source report hash, parameters hash, 등록·effective date/time, session별 prospective authority를 결속한다. KRX economics를 AM 경제성으로 복사하지 않는다. AM reference seed가 현재 설계에서 허용되는 범위는 기존 prospective policy 계약 안에서 확인한다.
- collector date activation 뒤 universe/seed 변경을 처리할 때는 reviewed effective boundary에서만 reload하고, 기존 episode/holding custody를 유지한다. 같은 날 재기동으로 seed의 과거 적용시각을 바꾸지 않는다.

### 4.4 consumer 입력 연결

`widget_auto_trade_policy_calibration._load_rows`는 raw market과 advisory 두 role을 명확하게 구분한다. raw만 존재하는 경우 “advisory 0”과 “market source 0”을 같은 값으로 취급하지 않는다. AM coverage는 실제 AM raw로, 신호·episode 성과는 해당 AM frozen seed 이후의 prospective event로 계산한다.

현재 established 4종목의 `invalid_optional_lifecycle_event_count`도 별도로 분해한다. bad optional event만 식별 가능한 경우 event 경제성 입력에서 제외하되 유효 OHLCV를 함께 버릴 필요가 있는지 소비 계약별로 판단한다. global/identity 필수 결손은 계속 차단한다. raw row를 단순 삭제하거나 validation을 완화하지 않는다.

P0 종료 조건: registered producer source와 consumer source의 전종목 census가 대사되고, KRX raw 13개를 missing으로 오인하지 않으며, AM 실제 결손·seed 미평가를 정확하게 기록한다. detail producer repair 뒤 다음 자연 수집의 error 원인과 개선 여부까지 확인한 후에만 producer-gap을 닫는다.

## 5. P1 — 원격 조회·fingerprint·메모리 개선

### 5.1 exact-date source snapshot와 재개

- 현재 `main`의 전종목 원격 조회를 먼저 하는 흐름을 종목별 snapshot validation → missing/changed source만 조회 → atomic publish 순서로 바꾼다.
- key에는 symbol/date/route/session/adjustment/schema와 필요한 API parsing contract를 포함한다. checksum·target date·coverage·source generation을 모두 검증한다.
- 최초 import 또는 content 변경은 기존 fetch validation을 실행한다. cache miss·불완전·충돌·코드 contract 변경은 재조회/재계산 대상이다.
- postclose 완료된 날의 frozen source만 durable reuse한다. 성장 중인 file/응답에 완료 marker가 없으면 tail/mtime만으로 completed snapshot을 승인하지 않는다.
- completed snapshot을 재사용할 때 원래 retrieved_at/source time을 보존한다. cache read 시각으로 freshness를 갱신하지 않는다.
- symbol checkpoint에는 source hash/producer contract/parameters/results completion을 기록한다. 실패 재개 시 이미 완료한 동일 source의 symbol만 재사용한다. 오래된 결과를 오늘 PASS로 쓰지 않는다.

### 5.2 hash와 순차 처리

현재 fingerprint는 전종목 분봉 tuple·JSON 복사와 encoding을 수행하며 main과 report에서 반복 계산된다. 순서가 고정된 canonical bar hash를 source snapshot 생성 시 한 번 계산하고, report fingerprint는 per-symbol hash + universe/origin + baseline + cost/grid/session/feature dependency hash로 합성한다.

`meta.source_content_sha256`는 현재 fetch에서 생산하지 않으므로 먼저 실제 digest와 검증 계약을 구현한다. 필드가 있다는 가정으로 raw hashing을 삭제하지 않는다. hash schema 변경 시 old report/cache는 명시적으로 무효화한다.

종목별 조회→검증→평가→compact result 저장→raw 객체 해제로 바꿔 모든 symbol history를 동시에 보관하지 않는다. 최종 report는 per-symbol result/meta만 합친다. 필요한 incumbent/challenger comparison도 동일 symbol 안에서 끝낸다.

### 5.3 compact projection

기존 observation writer가 consumer 필수 bar/advisory/source/event/seed/owner identity만 담은 projection을 함께 남긴다. raw path/hash/row identity 및 field preservation receipt를 결속하고, projection 누락·version 변경·hash mismatch 시 원본에서 재구성한다.

projection은 optional speed path다. 원본보다 source 검사를 느슨하게 하거나 가격·시간·비용·event identity를 생략하지 않는다. 사용자 표시용 전체 chart/context/history 중 calibration이 소비하지 않는 값만 제외한다. 기존 schema를 읽는 caller의 호환성을 유지한다.

## 6. P2 — 같은 결과를 빠르게 계산

1. `_setup_feature`의 rolling 15/30/45와 session anchor high/low, continuity, trend·volume state를 symbol/date별 한 번 선계산한다. session prefix scan을 매 index·policy마다 반복하지 않는다.
2. entry 조건을 공유하는 policy family의 setup/reclaim trace와 target별 exit 결과를 재사용한다. target/exit에 따라 cooldown·다음 entry 경로가 달라지므로 entry 전체를 독립적으로 고정하지 않는다. cache key에 이 의존성을 포함하고 old replay와 exact episode 비교로 검증한다.
3. grouping/sorting과 calibration first/second half 집계를 재사용한다. component replay의 같은 window를 다시 계산하지 않고 day 결과로 집계한다.
4. candidates에 모든 episode dict/comparison을 반복 저장하지 않는다. full/half/cap 집계와 deterministic rank를 유지하고 최종 선택·필수 diagnostic 후보의 detail만 보존한다. 기존 tie-break/iteration order를 그대로 재현한다.
5. auto-policy의 empty input 또는 필수 source-invalid scope는 census/audit을 남긴 뒤 grid를 생략한다. 유효 signal 없음과 producer missing을 서로 다른 상태로 반환한다. candidate_count 변화가 downstream 요구사항에 주는 영향도 검토한다.
6. day replay cache는 canonical source hash + algorithm/grid/cost/seed contract를 key로 한다. 다음 날 holdout 이동·half 재분할은 원래 dates로 다시 집계한다. cumulative scalar만 저장하여 chronology를 잃지 않는다.
7. day cache가 source보다 커지지 않도록 크기 상한·eviction을 둔다. optional cache 제거는 재계산만 유발하고 raw/정책/receipt를 삭제하지 않는다. DB/daemon을 만들지 않는다.

초기 full bootstrap과 daily incremental run을 별도로 측정한다. incremental 성능을 full bootstrap 성능이라고 보고하지 않는다. source가 같은 재시도, 새 하루 추가, 과거 하루 수정, seed/cost 변경을 모두 측정한다.

## 7. wrapper·운영 연결

- 기존 wrapper에 stage start/end·wall/CPU/RSS, symbol/page/grid 진행률, cache hit/miss, EOD wait를 기록한다. child 진행 receipt는 symbol 또는 제한된 grid chunk 단위로 내고 bar별 logging을 하지 않는다.
- target date는 시작 시 고정하고 자정 이후 재개에도 유지한다. 실패 단계만 재개할 때 앞 단계의 source hash 및 dated output을 확인한다.
- EOD 대기는 오늘 41분이었다. 동일 source에서 polling을 바꾸는 것만으로 계산 비용이 크게 줄지는 않는다. 먼저 기존 early calibration/EOD overlap을 유지하고, census/timing에서 wait를 명시한다.
- measured worst-case를 얻은 뒤 phase budget을 정한다. budget 만료는 partial checkpoint + 명시적 failed/deferred 상태를 내고 strict final completion을 막는다. 무한 대기 또는 silent signal 종료를 정상 empty 결과로 처리하지 않는다.
- CPUQuota/MemoryMax 증설은 기본 개선수단으로 쓰지 않는다. 현재 20%/512MiB에서 먼저 측정하고, resource 조정은 host 병행부하 근거가 필요한 후속 운영 선택으로 둔다.
- final sources → tower → checklist → strict verifier `--require-summary-handoff` → controller DONE/finalization 순서를 검증한다. optional cache 파일을 summary 필수 source hash에 넣어 eviction으로 최종 계약이 흔들리게 하지 않는다.

### 7.1 09-17 구현 운영 계약

- 기존 raw collector는 동일 validated universe helper의 19종목을 정규장·실제 integrated AM route에서 관측한다. 18/min local budget·headroom 3을 유지하고 명목 cycle은 228초 이상이다. 10초 이내의 검증된 공통 quote/BBO는 원래 수신시각을 보존하여 재사용하며 chart는 실제 조회한다.
- 실행 canonical policy는 기존 trader가 재구성할 수 있는 기존 형식을 유지한다. 확대 관측 seed는 동일 writer의 `widget_symbol_observation_catalog_<effective_date>.json` companion에만 고정하며 `symbols={}`, `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true`이다. observer는 exact-date evidence로 재구성한 companion만 우선 소비한다. seed가 없는 종목은 raw-only receipt이며 주문·episode를 만들지 않는다.
- source snapshot은 EOD terminal·exact date·checksum·parser contract·coverage로 검증한다. `data/cache/widget_signal_research_sources`의 symbol/date 파일과 bounded day replay cache, 기존 research output의 symbol checkpoint는 optional 재개 입력이다. growing/unmarked source는 durable snapshot으로 승인하지 않으며 cache read로 source time을 갱신하지 않는다.
- 기존 observation `.calibration.jsonl` projection은 원본 경로·행 digest·contract·payload checksum을 검증하고 실패하면 raw를 소비한다. 실제 BBO/quantity·paired trace·event·cost identity를 보존한다. 종료되지 않은 당일 입력과 64MiB 초과 입력은 full scan하지 않고 명시적인 source gap을 반환한다.
- wrapper의 각 분석 단계 default budget은 5,400초, EOD wait는 별도 최대 5,400초다. engineering 합성 full bootstrap 측정에 여유를 둔 상한이며 실제 API acquisition의 완료 보장은 아니다. `KORSTOCKSCAN_WIDGET_EVALUATION_PHASE_BUDGET_SEC`의 0은 명시적으로 상한을 끄는 값이다. 실패 시 target date·stage·exit code를 기록하고 completed symbol checkpoint 및 TERM 때 bounded partial day cache를 남기며 final completed/apply receipt를 만들지 않는다.
- 배포는 새 immutable release에 raw/runtime collectors와 evaluation unit만 pin한다. runtime collector condition은 validated raw scope를 허용하는 `--check-observation-scope`; seeded 평가와 execution policy는 각각 기존 exact-date 검증을 유지한다. timer 20:10·CPU/memory·admission·trading PID·holding/order custody는 기존 계약을 유지한다. rollback은 저장된 이전 drop-in으로 세 unit만 복원한다.

## 8. 작업본 구현·검증 순서

| 단계 | 작업본 변경 | 검증과 종료 기준 |
| --- | --- | --- |
| W0 baseline | 현재 source/PID/pin·universe·fixtures·기존 code SHA 고정 | 실행 중 wrapper를 수정하지 않음. 유효 legacy input과 결함 input을 별도 고정 |
| W1 P0 census/detail | 기존 producer/consumer에 role·scope·seed·error 설명 추가 | 13종목 raw/advisory 경로 대사, 598행 원인 미확정 보존, 새 error detail tests |
| W2 P0 collection/seed | 받은 bars 보존, 연구 관측 등록·seed 의존성 연결 | frozen seed/seed 없음/신규등록/AM route/degraded 원천에서 실제 writer→loader 연결 테스트 |
| W3 P1 snapshot/memory | exact-date cache/hash/순차 symbol 처리 | 재시도 0 remote read, corruption miss, 중단·동시 publish·코드/cost/seed 변경 tests |
| W4 P2 replay | precompute·deterministic rank·day cache·empty skip | old/new full replay의 정책·episode·집계 비교와 incremental/full 비교 |
| W5 end-to-end | wrapper/progress/strict downstream 호환 | local frozen sources로 wrapper→report→policy→dated loader→verifier contract 통과 |
| W6 code closure | self review→finding 수리→re-review | scope 내 미해결 finding 0, 관련 pytest·compile/bash/diff·문서 parser 통과 |
| W7 release handoff | 검증한 동일 code generation을 managed release에 전달 | 아래 §10 충족. deployment는 source-only tests와 다른 receipt |

새 production Python 파일이나 test 파일이 꼭 필요하다고 주장하기 전에 기존 파일로 해결할 수 없는 ownership 이유를 제시한다. 이 계획의 기본 구현은 기존 파일 수정이다.

## 9. 검증·성능 acceptance

### 9.1 품질

- 실제 기존 파일 format으로 producer `_record`→raw/projection→consumer loader를 연결한다. hand-made normalized dict 테스트만으로 종료하지 않는다.
- 13 watch + 2 discovered + established의 raw 기대집합을 대사한다. auto-policy 22-symbol legacy specs와 research 19-symbol universe의 차이도 설명한다.
- regular/integrated/unknown venue, stale/future/conflict, sparse bars, missing seed, restart, date change, manual custody, exclusion/cost null을 검증한다.
- valid old input에서는 selected parameters·pass/reject·trade date/time·entry/exit price·daily ordinal·episode count·cost identity·full/half/holdout/cap 판정이 동일해야 한다. JSON metadata와 계산 시간을 제외하고 경제 필드의 기존 rounding 결과도 일치시킨다.
- deterministic tie와 negative/zero/missing EV를 검사한다. `or default`로 zero를 missing/negative와 섞는 기존 문제가 발견되면 별도 correctness diff로 처리한다.
- corrected source input의 증감은 exact row/date/role delta로 검토한다. remote OHLCV 보충이 BBO/실시간 event 복원으로 표시되지 않아야 한다.
- cache hit/full recompute와 day incremental/full replay를 같은 fixture에서 비교한다. 종목 순서·input 순서·동시 publication이 정책 선택을 바꾸지 않아야 한다.
- guard/owner/수량/자동승격 기준과 실제 거래 authority의 회귀를 기존 테스트에서 검증한다.

### 9.2 성능 제안 목표

아래 수치는 측정할 engineering 목표이며 현재 달성 결과가 아니다. 정확도 기준을 충족한 경우에만 인정한다.

| 시나리오 | 측정 목표 |
| --- | --- |
| full 19-symbol frozen-source bootstrap | CPU ≥50% 감소, EOD/원격 대기 제외 wall ≤60분을 20% quota 기준으로 확인 |
| 다음 하루 추가 daily run | EOD 대기 제외 평가 wall ≤20분, 기존 source remote 재조회 0 |
| 동일 날짜·동일 input 재시도 | completed source/replay 재사용, 원격 요청 0, wall ≤2분 목표 |
| 메모리 | 전체 service peak RSS ≤384MiB 목표, swap 사용 0 목표 |
| raw/projection | consumer 필수 field 보존율 100%, input bytes/parse CPU 감소량 보고 |
| source coverage | expected scope 미분류 0, producer/consumer 누락은 exact receipt로 100% 식별 |

먼저 종료된 4-symbol run과 bounded fixtures로 비교하고, 최종 19-symbol 전체 benchmark는 작업본의 frozen source로 수행한다. 현재 실패한 19-symbol run의 2시간 13분을 완료 baseline으로 사용하지 않는다. 원격 acquisition 시간, cold/warm cache, CPU quota와 병행부하를 각각 공개한다. 목표 미달이면 원인을 수리하며 기간/grid를 조용히 줄이지 않는다.

## 10. 배포본 인계와 자연 폐쇄

1. 작업본 code closure와 W5/W6 완료 전에는 배포본을 수정하지 않는다. source-only output을 live canonical 정책에 publish하지 않는 isolated output paths를 사용한다.
2. workspace의 기존 dirty docs/data/verifier 변경은 보존한다. 이번 scope만 인계하고 review evidence에 exact commit·file hash·dependency contract를 남긴다.
3. 기존 managed release를 새 검증 commit으로 구성한다. 이전 immutable release를 직접 편집하지 않는다. data/docs/logs/tmp/.venv 및 기존 shared mount 계약, clean source, wrapper executable을 확인한다.
4. 영향받는 기존 widget raw/runtime collectors와 evaluation unit만 dependency inventory에 따라 인계한다. observer universe 확대가 실제 trader execution enrollment로 새지 않는지 확인한다. collector 변경은 source-only 계획 항목과 별도 PID receipt를 남긴다.
5. inactive/quiescent 경계에서 effective WorkingDirectory/PYTHONPATH/KORSTOCKSCAN_PROJECT_DIR/Python/ExecStart와 실제 Python import origin을 확인한다. 기존 pin 문자열 비교만으로 종료하지 않는다.
6. 이전 config/selector/release를 보존한다. rollback은 output/seed generation과 source date를 기록하며 새 원천을 삭제하지 않는다. 실행 중 holding/episode를 다른 owner로 넘기지 않는다.
7. 자연 acceptance는 새 raw 생산→all-scope census→유효 seeded advisory→완료된 full-cost/holdout 연구→dated policy 소비→strict final chain으로 확인한다. raw-only/seed 없음/지원되지 않는 venue는 설명된 상태로 유지한다.
8. 오류 detail repair의 다음 자연 표본에서 원인과 recurrence를 확인한다. 과거 RuntimeError 598행은 원래 receipt로 보존한다. audit exclusion이나 cache hit만으로 producer-gap을 닫지 않는다.

09-16 요청의 deliverable은 상세계획과 원천 점검이었다. 09-17의 별도 사용자 지시는 실제 구현·반복 리뷰·보완·검증·commit/push·배포·기동까지 허용한다. 합성 성능·code closure·설정 설치·actual collector PID와 장후 자연 완료·정책 소비·경제성을 분리해 기록한다. 기존 stable ID `[WidgetPostcloseEvaluationPinAcceptance0916]`는 과거 실패·acceptance를 보존하여 09-17 daily의 단일 OPEN owner로 이관한다.

## 11. 참조

- [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1~§8: clean baseline·경제성·source·authority 원칙.
- [09-16 checklist](../checklists/2026-09-16-stage2-todo-checklist.md): 현재 OPEN owner 및 이전 설정 receipt.
- [기존 pin/import 보완 기록](../audit-reports/2026-09-16-widget-evaluation-release-pin-repair.md): 설정 설치와 실제 import 검증의 구분.
- [Kiwoom 공통 data health 계획](kiwoom-intraday-common-data-health-implementation-plan-2026-09-16.md): 기존 market source·route·metadata 재사용 경계. 이 문서의 기능이 이미 구현됐다고 가정하지 않는다.
- [raw producer](../../src/engine/monitoring/widget_research_watch_collector.py), [advisory producer](../../src/engine/monitoring/widget_symbol_runtime_collector.py), [local calibration](../../src/engine/monitoring/widget_auto_trade_policy_calibration.py), [signal research](../../src/engine/monitoring/widget_symbol_signal_policy_research.py), [observation/execution policy loader](../../src/engine/monitoring/widget_symbol_runtime_policy.py).
