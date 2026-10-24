# Main 약세 장후 연구 원천 연결·누적·조정 후보 결함보완계획 — 2026-10-13

## 1. 결정과 범위

**압축 원천 선택과 기존 native 판정 연결을 먼저 수리하고, 같은 정의의 날짜 간 누적을 복구한 뒤 기계 단독·보조 이후 조정 후보를 평가한다.** 유효한 입력이 계속 들어오는지 확인하기 전에는 후보 0을 조정 효과 없음으로 판단하지 않는다.

이번 지시는 결함보완 **계획 수립·리뷰**다. 코드 수정·배포·예약 재설치·연구 재실행·Telegram 전송·정책 발행은 후속 실행 단계다. [원 계획](main-market-weakness-observer-repair-and-postclose-research-implementation-plan-2026-10-08.md)의 MW0–MW6와 10/9 구현·배포 이력은 보존하고 이번에 확인한 새 결함만 연다. 실행 인계는 [오늘 체크리스트](../checklists/2026-10-13-stage2-todo-checklist.md)의 기존 stable ID `MainMarketWeaknessPostcloseObservation1008`을 재사용한다.

- 새 장중 hook·로깅·metadata·파일 조회/해시·queue·thread·worker·API/AI 호출은 0이다. `ai_decision_trace`의 생산 형식·본문·주기·쓰기 횟수와 기존 기계/보조 판정·주문은 바꾸지 않는다. 자료가 없으면 정확도를 포기하고 미연결/U로 남긴다.
- 연구는 `postclose_research_advisory_only`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`다. 기존 보조 패턴연구의 요청·응답·라벨·membership·shared store와 Main/manual custody·퇴역 경계를 보존한다.
- 기존 야간 예약·worker 1개·감독자 포함 메모리 512MiB·야간 총 예약 wall 600초 이하·최대 9회·회당 60초를 유지한다. KST 21:40~05:40 슬롯과 더 이른 Main 준비 deadline을 따르며 EOD/일반 장후 owner에 양보한다. 자료 연결 수리 때문에 예산·빈도·동시성을 확대하지 않는다.
- 실제 ask·비용률 .0023·1800초·비용 후 +.4%와 soft −3% 선도달의 W/F/U와 누적 raw 승률 계약을 유지한다. 비용 설정을 사용한 가격 경로 CF와 실제 체결/PnL은 다르다. 기존 Main 채택에 EV·손익비·최소 일수/표본·holdout·성공 보존율 gate를 추가하지 않는다.
- IDE의 [joint 적용 계획](main-joint-research-operating-adoption-and-scope-replacement-plan-2026-10-13.md)은 별도 owner다. 그 후보/승인/등록 수치를 약세 연구의 후보나 배포 승인으로 전용하지 않는다.

## 2. 점검 증거와 결함 분류

아래는 10/13 점검 시 기존 산출물과 코드의 상태다. 후속 구현 착수 때 selector·원천 세대·파일 형태를 다시 고정한다. 사본 압축/교체가 진행될 수 있으므로 이 표를 현재 원천 불변의 증거로 사용하지 않는다.

| 원천일 | 집계 기록 | 자연 trace 기록 | 약세 연결 성공 | terminal |
|---|---:|---:|---:|---|
| 10/7 | 8,673 | 0 | 0 | completed_with_source_gaps |
| 10/8 | 6,425 | 799 | 0 | completed_with_source_gaps |
| 10/12 | 1,624 | 735 | 0 | completed_with_source_gaps |
| 합계 | 16,722 | 1,534 | 0 | 후보 0·not_eligible |

집계 기록은 자연 판정과 재생/저장된 장후 실제 보조 응답 cohort를 포함한다. 이를 고유 실거래 수로 해석하지 않는다. W/F/U는 4,676/1,585/10,461이나 모든 시장 연결이 UNKNOWN이므로 이 승률로 약세 영향을 주장할 수 없다. 자연 trace 1,534개는 전부 `exact_label_binding_missing` U다.

- [누적 포인터](../../data/report/main_market_weakness_research/cumulative/current.json)의 점검 세대는 `792e39d76036dc8a232a88538545c010335a3d120f3c26b7dc0c72b861fd7494`다. [고정 비교 결과](../../data/report/main_market_weakness_research/cumulative/792e39d76036dc8a232a88538545c010335a3d120f3c26b7dc0c72b861fd7494/candidate_comparison.json)의 `candidate_count=0`, `comparisons=[]`, `candidate_manifest_sha256=null`이다.
- [야간 요약](../../data/report/main_market_weakness_research/night_summary.json)은 night_id 10/12, 마지막 원천일 10/12, 10/13 04:40 생성의 `completed_with_source_gaps / not_eligible`다. 설치 설정은 enabled·notify_enabled=true이고 실제 cron/설치 calendar 검증은 통과했다. 13개 작은 산출물의 seal·날짜·세대 연결을 검증했으며 대용량 raw 원천의 현재성 전체를 재검증한 결과는 아니다.
- 점검 selector는 `main-entry-deadline-20261013-v7`; 연구 3개 모듈과 wrapper는 작업본과 같고 설치의 code hash `77332207cbe25c8be3991b1b601023d9266554a6fed70fd59fb785748fc804af`와 일치했다. 이는 연구 코드 선택/예약 소비 증거이며 연구 효과나 Main 매매 개선 증거는 아니다.

| 결함 | 직접 producer → consumer 근거 | 영향·우선순위 |
|---|---|---|
| 종목 마스터 압축본 누락 | [listing_lookup](../../src/engine/automation/main_market_weakness_research.py)의 glob/read/date 추출이 `.json`만 지원. [보관 마스터](../../data/report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-09-16.json.gz)는 canonical 검증 통과·2,604종목이며 세 날짜의 집계 종목을 전부 조회 가능 | **P0 확정 reader 결함**. 16,722개가 `scope_or_listing_market_missing`, listing receipt=null |
| 자연 trace 압축본 누락 | 같은 모듈 `source_plan`은 `.jsonl`만 선택. 계획 작성 시 10/7·10/8 trace는 `.jsonl.gz`만 존재 | **P0 확정 원천 census 결함**. 기존 집계 모집단이 파일 형태에 따라 불완전해짐 |
| 실제 native 판정 본문을 연결하지 않음 | [project_trace](../../src/engine/scalping/market_weakness_research.py)는 trace의 `entry_mechanistic_policy_decision.event`를 기대. 표본에는 해당 본문이 없고 native receipt만 있음. [기존 writer](../../src/engine/scalping/ai_decision_trace.py)는 별도 기존 payload 행에 `source.assessment/exact_payload`와 해시를 기록 | **P0 연결 결함·잔존 원천 확인 필요**. canonical/ask/feature/label 미연결. 없어진 본문을 추정하지 않음 |
| 날짜마다 scope key가 끊길 가능성 | 순수 연구 `scope_key`가 global machine/auxiliary hash를 포함. 세 날짜의 exact scope key 교집합은 모두 0. 같은 symbol/session/route/origin/policy scope/관련 machine payload의 날짜 간 공통 조합은 17개 | **P1 누적 계약 결손**. 같은 정의인지 추가 검증 필요하며 17개를 즉시 비교 가능하다고 주장하지 않음 |
| 기계 숫자 조정 경로 없음 | `freeze_candidates`는 `post_auxiliary_withhold_cf`만 생성하고 machine_status를 `numeric_adjustment_unidentifiable`로 고정. 기존 회귀도 이 고정값을 요구 | **P1 기능 결손**. 기계 단독 연구의 지원 범위/미식별 사유를 구체적으로 선언해야 함 |
| 기계 후보를 소비할 평가/알림 경로 없음 | 순수 연구 `selection`과 `Aggregator._add`는 kind/보조 PASS를 고정 요구. `pair_delta`는 selected/excluded만 지원. notifier `advisory_eligible`는 제외 수>0, formatter는 보조 PASS 보류 문구, parent checker는 auxiliary binding을 요구 | **P1 연결 결손**. 후보 manifest 추가만으로 기계 강화/완화·신규 확인점의 비교/안내가 완성되지 않음 |
| 확인 약세와 단일 raw 약세 혼용 | `attach_joins/join_snapshot`은 classification을 raw_market_snapshot으로 고정하고 reconstructed_active를 부가값으로만 저장. 현재 selection은 raw WEAKNESS를 사용 | **P1 연구 기준 결손**. 2회 활성/3회 회복 latch에 따른 조정 연구와 단일 raw 진단을 구분해야 함 |
| terminal 결손 설명·현행 인계 부족 | 10/12 terminal의 gaps={}인데 join 전부 U. 오늘 checklist에 기존 연구 stable ID가 없음 | **P1 소비/인계 결손**. 계산 종료와 분석 가능성을 구분하고 원 ID로 현재 owner 복구 |

## 3. 순서와 종료 조건

| 단계 | 작업 | 종료 조건 |
|---|---|---|
| WR0 기준 고정 | 실제 selector/공유 anchor·원 모듈 hash·설치·세 날짜 cursor/manifest·원천 alias·label/후보 계약 고정 | 기존 dirty 변경·원 연구·정책/봉인 보존 목록과 결함 fixture 확보 |
| WR1 압축 원천 수리 | 종목 마스터와 trace의 날짜 발견·논리 원천 선택·bounded decode·receipt/세대 검증 | 운영 comparison이 없는 gzip-only 날짜도 발견·선택·census 성공. 순수 reader만 변경 |
| WR2 native 연결 수리 | 기존 machine observation → natural trace → 원 event/ask/feature/정답 연결 | 동일 실제 계약의 양성 fixture에서 연결 성공, mismatch·누락·충돌은 명시적 U. 장중 producer 변경 0 |
| WR3 누적·상태 수리 | scope 의미 식별, 확인 약세·raw 분리, 단계별 재개, 원 분모/결손·capability·마지막 소비 정합 | 같은 검증 정의는 날짜 간 누적, 실제 정의 변경은 분리. 입력 변화만 영향 날짜 갱신·미완료 단계 재개 |
| WR4 조정 후보 보완 | 연구 kind별 모집단/평가/안내 분기, 보조 이후·기계 단독 manifest와 before/after mask | 원 확인점/재생 범위·W/F/U·추가/제외 비교가 notifier까지 연결, 불가능한 축은 이유 명시 |
| WR5 검증·후속 운영 인계 | 회귀/재리뷰 후 허용된 release/optional code rebind와 자연 예약 소비 | terminal→일별→누적→후보→notification disposition→night summary 연결; unchanged delta 0·비적격 무발송 |

WR1–WR3의 원천 복구를 WR4 전체 지원 완료까지 묶지 않는다. 재생 cohort만 먼저 복구돼도 그 범위의 시장 연결을 검증하며 자연 cohort의 미연결은 계속 표시한다. 실제 후보 1개 이상·첫 Telegram 발송을 source 수리 종료 조건으로 요구하지 않는다.

## 4. WR1: 압축 원천·원천 세대

### 4.1 종목 마스터

1. `.json/.json.gz`에서 논리 날짜를 명시적으로 파싱한다. `Path.stem[-10:]`을 gzip 이름에 적용하지 않는다. 최신 **source_date 이하** canonical 마스터를 선택하고 symbol별 effective window·conflict·verified_at·schema·권한·content hash를 검증한다. 9/16 instrument metadata의 유효기간을 확인해 쓰는 것은 9/16 매매 결과를 forward 연구로 복원하는 행위가 아니다.
2. 같은 논리 날짜의 plain/gzip은 한 원천이다. 둘 다 있으면 canonical payload 동일성을 bounded 검증한 뒤 원본 우선으로 한 번 소비한다. 충돌·가장 최신 후보의 잘못된 계약은 과거 파일로 조용히 우회하지 않고 해당 입력 결손을 표시한다. 깨진 gzip·CRC/EOF·읽는 중 교체를 정상 빈 master로 바꾸지 않는다. 크기 상한은 **읽기/해제 중** 적용한다.
3. 기존 [symbol master validator](../../src/engine/scalping/micro_reversion/symbol_master.py)와 [공통 JSON reader](../../src/utils/jsonl_io.py)의 안전한 순수 읽기 계약을 재사용할 수 있는지 확인한다. 복원/write/장시간 원천 lock을 호출하는 helper는 사용하지 않는다. 작은 master는 해제 후 크기를 먼저 제한하고 hash와 physical stat·선택 정책을 receipt에 담는다.
4. source date·논리 ID·semantic hash와 실제 소비한 physical 경로/stat/hash를 함께 기록한다. 압축 전환이 의미를 바꾸지 않았다는 검증 없이는 예전 plain receipt를 새 gzip에 그대로 붙이지 않는다. listing receipt 변화는 영향 일별 generation을 새로 계산하고 누적에 구/신을 함께 넣지 않는다.

### 4.2 자연 trace와 연결용 기존 payload

`source_plan`의 logical stream은 plain 원본이 있으면 원본 한 개, 원본 부재 시 이미 보관된 gzip을 읽는다. prefix/date/schema/alias 정책과 physical receipt를 manifest에 넣는다. 기존 trace·payload를 무조건 unarchive하거나 새 원본 파일을 만들지 않는다. mixed JSONL의 unrelated row도 원 census의 제외 사유로 보존한다.

`discover_dates`, scheduler의 pending/currentness 검사, 실제 `source_plan`, reader·dependency/cursor 검증이 **같은 논리 파일 선택 계약**을 사용해야 한다. `.jsonl.gz`만 있고 운영 comparison directory는 없는 날짜를 발견→작업 선정→reader 소비까지 통합 검증한다. source_plan만 수정하고 날짜 발견을 기존 plain glob으로 남기지 않는다. clean/forward 경계와 실제 거래일을 확인하며 market observation만 있는 날짜는 decision 원천 결손으로 남긴다. helper별로 gzip 날짜를 다르게 파싱하지 않는다.

- plain은 기존 newline byte cursor를 유지한다. gzip의 cursor는 **해제된 행/offset**과 물리 compressed generation을 구분한다. gzip에서 임의 byte offset으로 재시작하거나 `.seek()`의 숨은 prefix 재해제를 상수 비용으로 취급하지 않는다.
- gzip-only 큰 원천은 한 예약의 **잔여** 시간 안에서 순차 streaming을 우선한다. listing·census·native index·다른 처리에 쓴 시간을 뺀 실제 stop_at과 감독자 종료 여유를 따른다. 행 크기·해제량·CPU/wall·resident memory를 제한하며 필요한 작은 projection/index만 저장한다. gzip EOF/CRC와 전체 frozen stream 검증이 끝난 뒤 source-complete를 commit한다. 모든 원문을 메모리/별도 디스크 원본에 복사하지 않는다.
- 기존 검증된 압축 member/index 또는 sealed 장후 projection으로 중간 재개가 가능한 경우에만 재사용한다. 그런 경계가 없어 잔여 예약 안에 논리 원천을 끝내지 못하면 `compressed_resume_unavailable`로 그 원천을 결손 종료한다. 그 gzip에서 아직 검증되지 않은 partial partition은 current census/집계/안내에 넣지 않고 commit되지 않은 임시 결과로 격리한다. 완료된 다른 원천 subset은 보고하되 해당 gzip의 일부 prefix를 전체 모집단으로 봉인하지 않는다. supervisor hard kill로 사유를 쓰기 전에 끝나도 다음 진입에서 저장된 gzip in-progress ticket/세대/reader version을 보고 동일 무재개 원천을 다시 처음부터 읽지 않는다. 더 큰 예산·새 index/package 설치를 자동 요청/실행하지 않고 현재 자연 날짜부터 우선한다.
- plain/gzip 동일성 검증도 야간 예산에 포함한다. 동일성을 증명하지 못한 alias는 이중 합산하지 않고 결손으로 남긴다. 원천 변경·압축 전환·삭제는 새 세대 intake의 이유이며 crash나 재시도로 wall 예산을 reset하지 않는다.

일반 `iter_jsonl`은 decode 오류 행을 건너뛰며 기본 encoding errors가 replace인 경로가 있으므로 결손 분모·strict provenance가 필요한 이 연구에 그대로 사용하지 않는다. 재사용 helper의 strict 옵션/크기/lock/쓰기 부작용을 확인하고, 사전 검증된 범위에서만 reader를 선택한다.

## 5. WR2: 자연 판정 → 기존 native 본문 → 정답

장중 trace에 본문을 추가하는 대신, 이미 있는 `mechanistic_entry_observation_v1` payload를 **장후에만** 연결한다. [writer의 기존 capture](../../src/engine/scalping/ai_decision_trace.py)와 [v6 observation 검증 계약](../../src/engine/scalping/continuous_reversal_policy_v6.py)이 원 필드 의미의 근거다. 필요한 순수 decoder/verifier와 기존 정책의 읽기 전용 reader만 소비하고 기동/정책 적용 loader·주문 평가 경로·publisher는 실행하지 않는다.

| 연결 단계 | 검증할 증거 | 부족/충돌 시 |
|---|---|---|
| trace → machine observation | 기존 `machine_observation_sha256`, native `exact_payload_sha256/assessment_sha256`, evaluation_attempt_id·symbol·source date·PID/start·소비 bundle/관련 scope | 해시 필드만으로 다른 날짜/다른 attempt 본문을 채택하지 않음. exact receipt 없으면 trace_only |
| observation → 원 확인점 | `source.assessment.event`와 원 assessment action, native event_id/signal_id/token, canonical/opportunity의 기존 schema별 정의·source item·native epoch/sequence·venue/session | signal_id를 임의 canonical ID로 복사하지 않음. 실제 decoder/원 신원 계약으로만 해석 |
| 확인점 → feature/actual ask | 원 확인 시각의 `entry_ask`, volume_ratio_60s·drawdown_5m_pct 및 해당 definition의 수치 특징·원 proof | 현재 가격·다른 route·미래 특징/봉으로 보충하지 않음. SOURCE_INVALID/BLOCK/RECHECK를 ENTER_NOW로 바꾸지 않음 |
| 확인점 → 가격 경로 label | exact canonical/opportunity 또는 입증된 alias, 동일 event/time/ask·item/route/session·label 계약·기존 normalized source/price-path receipt | original bundle와 label producer parent를 따로 보존. 현재/후속 정책의 결과를 원 판정으로 전용하지 않음 |
| trace → 실제 보조 응답 | 원 prompt/input/schema/model/validator·auxiliary component와 실제 request/response·decoder binding | 준비된 request를 provider 호출/유효 PASS로 표시하지 않음. probe/offline actual/natural/미호출 분리 |

source.assessment와 exact_payload의 sanitize 이후 bytes/hash 의미를 원 writer와 맞춘다. 별도 observation body hash·source provenance·redacted 상태를 확인하며 복원 불가능한 원문을 새로 만들지 않는다. original trace 필드를 변경하지 않고 연구 projection에 binding ref/grade·실패 사유만 넣는다.

기존 계약상 `no_current_operating_signal` BLOCK은 event 자체가 없는 정상 판정일 수 있다. 이를 본문 연결 실패나 확인점/ask를 가진 거래 기회로 바꾸지 않는다. 원 native 평가·probe 관측·재시도·정규 AI 실행을 구분하고, event 없는 판정은 count-only/결과 미평가로 남긴다. 결과 라벨은 유효한 event/ask가 있는 subset에서만 만든다.

확인/응답/decision 시각은 별도 보존한다. 기계 단독 연구는 원 기계 확인 시각, 보조 이후 연구는 기존 응답 완료 시각을 사용하고 후자가 없으면 recorded decision proxy로 한계를 표시한다. schema가 명시한 session/route/item 변환만 허용하며 KOSPI/KOSDAQ 상장시장을 SOR/NXT 같은 실행 경로에서 추정하지 않는다. native 판정 origin의 probe observation과 실제 운용도 별도 cohort다.

장후 자체 작은 인덱스는 기존 payload를 한 번 순차 읽어 필요한 hash·typed ID·offset·작은 event/feature projection만 담는다. hot `trace_dedup` 준비/전역 인덱스·AI store writer/migration을 호출하지 않는다. 자체 index·cursor·lookup 비용을 총 예산에 포함하고 충돌을 식별된 row/scope에 격리한다. sqlite scratch는 원천이 아니며 durable commit은 원 검증 ref에 결속한 작은 partition/manifest다.

정답은 이미 유효한 label을 우선 재사용한다. 동일 확인점 label이 없을 때 **이미 보관된 충분한 가격 경로**로 같은 계약을 순수 장후 계산할 수 있는 subset만 평가한다. 그것도 불가능하면 U이며 원 producer/API/AI를 호출하지 않는다. 시간/가격 근접 매칭·미호출 AI PASS 가정·실제 fill/PnL 대체는 금지한다. 마지막 30분 경로 결손/동일 봉 순서 불명은 복구 실패가 아니라 잔존 U다.

## 6. WR3: 날짜 간 누적·분모·상태

### 6.1 scope 의미와 provenance

global bundle/component hash를 원 증거에서 제거하지 않는다. 비교용 `research_cohort_key`는 exact policy scope·symbol 또는 기존 선언 group·상장시장·session·route·origin·classification/outcome kind, 관련 machine payload/branch definition/feature-kernel/label 계약으로 구성한다. 보조 이후 연구는 해당 scope의 actual arm·prompt/input/schema/validator/decoder binding도 포함한다.

날짜/발행/다른 scope/무관한 코드 변경으로 전체 bundle hash만 달라도 **관련 정의가 동일하다는 원 receipt 검증**이 있을 때만 같은 비교 cohort에 넣는다. source release/full bundle는 각 row provenance로 남긴다. 같은 payload 문자열만으로 feature 의미·코드 계약·보조 정책의 동일성을 추정하지 않는다. 실제 정의·root/확인점·numeric before·보조 입력/응답 계약이 바뀌면 새 cohort이고 raw 승률을 합산해 winner를 만들지 않는다.

현재 17개 공통 조합은 조사 시작점일 뿐이다. 어느 cohort도 충분히 입증되지 않으면 `cohort_definition_unproven`으로 남긴다. 후보를 만들기 위해 서로 다른 시장/정책/origin을 합치지 않는다. snapshot/latch 재구성 버전도 유지한다.

원 `scope_key`와 비교 `research_cohort_key`의 검증된 mapping을 작은 manifest로 보존한다. 합쳐진 cohort에서도 같은 canonical 기회의 재시도/중복을 한 번만 outcome으로 집계한다. 정의 의미를 입증할 수 없는 split/merge는 보류한다. 이 mapping 없이 기존 outbox의 scope가 사라졌다고 정정 알림을 보내지 않는다.

### 6.2 확인 약세 연구의 기준

이번 조정 연구의 primary basis는 **해당 상장시장의 2회 활성/3회 회복 계약에 따른 확인 약세**다. 기존 receipt로 같은 observation ID의 실제 수용 latch가 검증되는 subset은 `observed_confirmed_latch`, 그 외는 기존 snapshot 순서로 재구성한 `reconstructed_confirmed_latch`로 표시한다. A/B/C/U는 snapshot의 가용/연결 품질이고 실제 latch 수용 증명과 별개다. 가용 시각 receipt만으로 실제 latch를 소비했다고 표시하지 않는다. 단일 `raw_market_snapshot`은 진단 view로 유지하며 확인 약세 후보 안내 근거로 전용하지 않는다.

시장별 유효 snapshot·unique ID·최소 간격60초·TTL300초·관찰 정책 epoch를 검증한다. 최초 raw 약세1회는 확인 약세가 아니다. 회복 evidence1/2회와 활성 latch 유지, 3회 해제, UNKNOWN/stale·날짜 전환을 원 상태 계약대로 재구성한다. 신선한 현재 관측이 없으면 마지막 active latch를 현재 확인 약세로 연장하지 않는다. 원천 누락/역순으로 연속 수용 여부를 입증할 수 없으면 latch_unknown이며 실제 notifier 이력으로 추정하지 않는다.

`confirmed_weakness_episode_id`는 시장별 inactive→active에서 시작하여 검증된 release/정책 epoch·날짜 종료 경계까지 유지한다. 회복 evidence1회 뒤 다시 raw 약세가 나온 것을 자동 새 사건으로 세지 않는다. raw 하락 구간 ID는 별도 진단이다. 기계/보조 이후 평가 시각의 확인 상태를 각각 as-of join하며 뒤의 두 번째 약세를 첫 약세 시점에 앞당겨 붙이지 않는다. 60/180초 가용 지연도 이 확인 상태로 다시 연결한다.

raw와 확인 latch는 같은 원 기록의 서로 다른 view다. 원 census와 W/F/U 총수에 두 view를 중복 더하지 않고 후보 manifest에 classification basis/version·hysteresis contract를 고정한다. 재구성 근거만 있는 안내는 그 사실을 Telegram에 명시한다. observer의 임계치·cadence·저장·실제 전이 코드는 바꾸지 않는다.

### 6.3 분모·결손·마지막 소비

`전체 원행 → projected → identity 검증 → listing 유효 → 시장 as-of join → exact feature/label → 후보 비교`마다 count와 제외 사유를 산출한다. attempt census, scope별 canonical 중복 제거 수, replay/장후 실제 보조/natural/probe 기록 수를 분리하고 원 연구의 표본 선별을 원 분모로 사용하지 않는다.

일별 terminal과 누적에는 `listing_missing/invalid`, 압축 원천 결손, native binding 결손/충돌, join A/B/C/U·reason, label W/F/U·reason, cohort/candidate capability를 작은 요약으로 넣는다. `completed_with_source_gaps`와 gaps={}의 모순은 입력 오류뿐 아니라 join/label 결손이 어느 단계의 분모인지 설명하는 것으로 수리한다. 미래 snapshot·300초 TTL·60/180초 지연·분 bucket·재구성 latch를 기존 계약대로 유지하며, PRE/AFTER에 정규장 약세를 TTL 이상 연장하지 않는다.

worker의 완료·현재 분석 가능성·후보 없음·알림 비적격을 `night_summary.json`까지 전달한다. **검증된 허용 야간 안**에서 worker 시작 전 자원/calendar/code 이유로 defer하는 경우도 작은 상태에 최신 시도/사유를 남긴다. `latest_attempt`와 원 generation을 가진 `last_completed_computation`을 구분하고 실패/defer가 이전 계산의 원 receipt를 덮어쓰지 않게 한다. 설정/원 namespace가 미검증이거나 장중 `outside_night_window`인 호출은 기존 owned wrapper 로그/반환 상태로만 기록하며 새로운 연구 상태 쓰기를 추가하지 않는다. 모든 상태는 advisory 권한을 유지하고 추가 heartbeat·장중 조회는 없다.

WR1–WR3의 reader/join/cohort/label version과 code hash가 바뀌면 이전 partition을 그대로 current로 재사용하지 않는다. 원 immutable 세대는 보존하고 영향 날짜 새 partition→cursor commit→일별→누적을 갱신한다. source가 이미 사라져 재검증할 수 없으면 이전 숫자를 새 추천에 쓰지 않고 결손을 표시한다. 동일 입력 재실행 delta 0, crash의 cursor 선행 저장 금지, 구/신 generation 이중 합산 금지를 검증한다.

### 6.4 시간 제한 뒤 단계별 재개

현 worker는 한 60초 안에 process_date→cumulative→reconcile을 순서대로 실행하므로, source 완료 뒤 누적/알림이 시간 초과하면 source cursor만으로 후속 완료를 증명할 수 없다. 자기 namespace의 작은 phase receipt로 `source/native_index → projection → daily_ready → cumulative_pending/ready → notification_pending/terminal`을 구분한다. source 처리에 예산을 썼다면 이미 검증된 daily를 재읽는 작은 단계부터 다음 허용 예약에서 이어간다.

큰 gzip 순차 source가 완료되고 EOF/CRC·source seal이 검증된 compact projection은 후속 phase timeout 때문에 다시 해제하지 않는다. 반대로 source가 미완료였던 임시 partition은 재사용 가능한 완료 세대가 아니다. phase commit은 원 source/code·실제 generation refs에 결속하고 worker crash에도 이전 cursor보다 앞선 결과를 합산하지 않는다.

scheduler는 새 날짜, 영향 날짜 projection, 미완료 cumulative/notification을 함께 발견한다. `completed_with_source_gaps` 일별 status만 보고 후속 phase를 영구 무시하지 않는다. 누적 갱신도 일별 aggregate와 사전 선언 candidate 묶음별로 checkpoint하되 모든 필수 comparison이 완료된 scope만 안내 대상으로 게시한다. 한 후보만 계산된 partial scope에서 승자를 고르지 않는다. 기존 야간 budget·fair cursor 안에서 재개하고 source/일별/누적 current의 서로 다른 세대를 결합하지 않는다.

## 7. WR4: 기계 단독·보조 이후 숫자 조정 연구

WR1–WR3 복구 뒤 기존 후보 생성의 capability를 scope/axis별로 먼저 검사한다. 미식별 문자열을 전체에 고정하지 않고 `supported / role_unverified / feature_missing / confirmation_replay_unavailable / auxiliary_not_observed / not_applicable` 등 실제 이유를 보고한다. 원 등록 정의 자체의 변경·라이브 membership 등록은 이 계획의 실행 범위가 아니다.

| 연구 종류 | 비교 방법 | 권한·정확도 경계 |
|---|---|---|
| 보조 이후 보류 CF | 실제 유효 PASS에서 기존 약세 강도와 원 확인점 특징에 따른 조건부 제외. 기존 두 특징의 지원 조건을 검증하고 무조정 baseline과 paired W/F/U 비교 | 원 PASS를 VETO로 덮지 않음. 다음 좋은 가격 재진입/새 AI 평가 없음 |
| 기계 원 확인점 필터 CF | 등록 정의의 기존 수치 축/단위/연산자와 owner의 `baseline_prior/bounded_tunable` 역할이 확인되고 원 확인점 선택 효과로 한정 가능한 경우만 비교 | 원 root/FSM/확인 ask 불변. tightening의 관측 확인점 선택 효과이며 완전한 정책 재생으로 표시하지 않음 |
| 기계 확인점 변경 CF | 허용된 기존 숫자 축이 root/재무장/확인시각/union을 바꾸면 이미 보관된 같은 normalized source와 원 순수 kernel로 재생 가능한 subset만 평가 | 새로운 확인 ask에 맞는 가격 경로를 다시 평가. 보조 응답은 변경 입력에 재사용하지 않으며 기계 단독 CF로 제한 |
| 미지원 축 | 역할·정의·특징·원천·예산을 충족하지 못하면 axis별 미식별 사유와 원 판정 count만 보고 | stale/conflict/quote/account/order/수량/cooldown/manual veto/hard safety/provider·가격/수량/holding/exit 축을 후보로 만들지 않음 |

기계 역할을 research config에서 임의로 `bounded_tunable`이라고 선언해 live 수정을 허용하지 않는다. 확인된 원 owner 계약이 없으면 그 축은 `role_unverified`이며 원 계획의 기계 연구 종료 범위를 미지원으로 명시한다. 적격 축 0이어도 보조 이후 연구의 정상 입력/후보 복구를 진행한다. 숫자 정의와 원천이 있는 범위의 연구를 넓힌다는 이유로 새로운 실시간 전략·원 registry rewrite·AI calls/publisher를 호출하지 않는다.

후보 manifest에는 scope/관련 parent·axis/unit/operator·before/after·weakness condition·evaluation mode·feature/definition refs·원천 cutoff를 넣는다. 결과를 보기 전에 작은 후보 집합을 고정하고 baseline 외 **scope당 두 종류 합계 최대 6개**로 제한한다. 기존 분위값/허용 범위·정밀도를 따르며 cross-product 탐색을 하지 않는다. 동일 원 기회의 baseline과 후보 양쪽에서 판정/feature가 식별된 공통 집합을 비교하고 선택 제외와 입력 결손을 분리한다.

원천 수리 뒤 새 후보가 과거 데이터를 처음 읽더라도 이미 존재한 날짜를 새 전향 증거로 표시하지 않는다. 복구 시점까지 확보한 날짜로 후보를 고정하고 **고정 cutoff 이후 새 자연 자료**의 비교 창을 별도로 둔다. 복구된 과거 누적 Δ는 기술 통계다. 이는 안내 안정성 계약이며 기존 Main 채택에 추가 holdout/최소 날짜 gate를 거는 의미가 아니다. 원천/정의 의미가 바뀌면 이전 후보 seed를 무효화·별도 version으로 보존하고 동일 결과로 cutpoint를 재탐색하지 않는다.

안내는 원 계획 §6.3의 paired raw 승률 개선·W/F/U/coverage·U 민감도·날짜/확인 약세 사건 제외·지연 join 방향 안정성·고정 1,000회 경험적 진단을 유지한다. 통계적 95% 보장으로 표시하지 않는다. 실제 기계 단독 CF와 보조 이후 CF의 모집단/불확실성을 각각 안내하고 미래 AI/실체결 성공을 가정하지 않는다.

### 7.1 candidate부터 notifier까지의 typed 계약

후보 manifest만 늘리지 않고 `freeze_candidates → selection → Aggregator._add/comparison → advisory_eligible → preview/current_parent_matches → recommendation_id/reconcile`의 실제 소비 분기를 함께 보완한다. 연구 kind/evaluation mode별 모집단·필수 binding·출력 schema를 고정한다.

| 분기 | 평가 모집단·필수 증거 | 알림/parent 검증 |
|---|---|---|
| post_auxiliary_withhold_cf | 실제 유효 보조 PASS·exact 응답 binding이 있는 같은 정책 cohort | 관련 machine payload와 원 보조 binding을 함께 확인. 보조 이후 이번 기회 보류 문구 |
| machine_confirmation_filter_cf | 원 기계 확인점·관측된 특징·기계 조건 역할/정의가 식별된 cohort. 보조 미호출/비PASS를 제외 이유로 삼지 않음 | 관련 기계 parent/숫자 before/정의/원천 계약 확인. actual auxiliary는 필수 조건이 아님. 기계 단독 원 확인점 필터 효과라고 표시 |
| machine_confirmation_replay_cf | 동일 frozen source interval에서 baseline/candidate의 원 순수 kernel 재생 및 각각의 실제 확인 ask/outcome | 현재 기계 parent만 확인하고 완화/강화·추가/제외/시각 변경을 표시. 새 입력의 보조 결과·실제 주문 개선은 미평가 |

현재 evaluator의 PASS-only 및 notifier의 `excluded_opportunities>0`는 보조 보류 분기에만 적용한다. 기계 비교는 `added+excluded>0` 또는 검증된 확인점/ask 변경을 요구하고 추가만 있는 후보를 제외0이라는 이유로 비적격 처리하지 않는다. baseline/candidate 확정 분모가 없으면 raw Δ는 null로 유지한다. 부모·기계 조건 역할·label/원천 guard는 보조가 없다는 이유로 생략하지 않는다.

서로 다른 모집단인 기계 단독과 보조 이후를 하나의 raw 승률로 경쟁시키지 않는다. winner_group은 검증된 cohort＋연구 kind＋evaluation mode＋동일 비교 모집단 계약이다. scope당 합계 최대6을 유지하며, 해당 winner_group의 사전 선언 후보 모두가 완료된 뒤 그 그룹의 winner를 선택한다. 두 종류의 후보가 발견돼도 동시에 결합 적용한 효과나 중복 개선분을 합산하지 않는다.

recommendation ID는 연구 kind·확인 약세 basis·관련 정책 정의·수치/단위/연산자의 정규화된 의미에 결속한다. global bundle/date/physical 압축/코드 버전만 바뀌어도 의미 ID가 달라지지 않도록 하고, 이전 scope key/ID는 검증된 migration mapping과 원 sent receipt를 보존한다. schema/key 이행 중 pending 비교만으로 과거 추천을 정정/철회하거나 같은 수치를 재발송하지 않는다. 실제 원천 무효화·완료된 새 평가의 부적격은 기존 정정/철회 계약을 따른다.

### 7.2 추가·제외를 함께 비교하는 분모

같은 frozen eligible source 집합에서 baseline과 candidate 선택을 각각 계산한다. 결과를 본 뒤 선택된 기회만 모집단으로 다시 만들지 않는다. 비교 row는 다음 네 영역으로 분리한다.

| 영역 | baseline 선택 | candidate 선택 | W/F/U 소비 |
|---|---|---|---|
| K 공통 | TRUE | TRUE | baseline과 candidate에 같은 확인점/ask label 한 번씩 |
| R 제외 | TRUE | FALSE | baseline에만 포함; 놓친 W·제거한 F·제외 U |
| A 추가 | FALSE | TRUE | candidate에만 포함; 추가 W/F/U |
| N 둘 다 비선택 | FALSE | FALSE | eligible/coverage 분모에 남기고 선택 승률에는 넣지 않음 |

baseline W/F/U=K＋R, candidate W/F/U=K＋A다. TRUE/FALSE가 아닌 조건 UNKNOWN과 label U를 구분한다. selection UNKNOWN은 W/F/U를 보고 유리하게 선택/제외하지 않고 공통 비교 범위 밖의 식별 결손으로 보고한다. 같은 확인 event/ask가 입증된 경우만 K 라벨을 공유한다. 실제 확인 시각/ask가 달라지면 별도의 R/A 기회로 두고 label과 ID를 새 확인점에 결속한다. 원 source window의 paired 날짜/확인 약세 사건 집계는 유지하며 입력 변경에 원 AI 응답을 붙이지 않는다.

U 민감도는 R의 U를 W, A의 U를 F로 두고, K의 U는 양쪽에 같은 결과를 배치했을 때의 두 끝값 중 더 불리한 Δ를 쓴다. 이 작은 계산은 실제 U를 집계 W/F로 바꾸는 것이 아니다. baseline/candidate 분모가 없는 경우는 null이다. 이 네 영역의 일별 작은 통계로 raw Δ·날짜/사건 제외·1,000회 진단·60/180초 공통 join을 계산하며 raw 원천을 후보별로 재읽지 않는다. 가격 경로가 없는 추가 확인점은 A의 U로 남기고 실제 보조/주문 성과로 해석하지 않는다.

## 8. WR5: 검증·배포·예약·Telegram 인계

### 8.1 코드 위치와 변경 경계

기존 순수 연구와 독립 자동화 모듈, [기존 outbox](../../src/engine/automation/main_market_weakness_research_notify.py), 기존 세 테스트 suite에서 보완한다. 기능을 root Python module이나 새 runtime worker로 옮기지 않는다. native source adapter가 커지면 location gate를 거쳐 같은 role package 안으로 분리하되 중복 구현/wrapper를 남기지 않는다. `ai_decision_trace`, native kernel/registry·보조 codec·정책 producer의 생산 동작은 이번 수리의 변경 대상이 아니다.

### 8.2 필수 회귀

| 영역 | 종료 검증 |
|---|---|
| 마스터 | 실제 형태의 gzip-only·plain-only·동일/충돌 alias, 미래 파일 배제, artifact_id/날짜 파싱, effective window/conflict/권한/hash, 깨진 gzip/크기 초과/읽는 중 교체 |
| stream | 운영 comparison 없는 gzip-only 날짜의 discover→pending→source_plan→reader→currentness, 원본 우선/원본 부재 대체, 미래/다른 날짜 제외, mixed row·malformed/tail·해제 중 크기 상한/CRC·alias 충돌, supervisor kill 뒤 무재개 원천 prefix 반복 억제 |
| native binding | 현재 capture의 **실제 필드 배치** fixture에서 본문/typed ID/event/ask/feature/정답 연결; trace에 assessment를 인위적으로 추가한 fixture만으로 종료 금지. attempt/date/PID/start/hash/item/route/time·redacted/충돌/본문 누락 음성 회귀, 정상 event 없는 BLOCK의 count-only |
| 확인 약세 | 원 최초 약세1회 비확인, 2회 활성·회복1/2회 유지·3회 해제, UNKNOWN/stale/역순/날짜/epoch 전환, raw/확인 view 비합산, episode 유지, 실제 가용과 실제 latch receipt 분리·미래 확정 전용0 |
| 누적 | 동일 검증 scope의 날짜/bundle 변경 누적, 무관 scope 변경, 실제 numeric/definition/feature/보조 버전 변경 분리, raw key→cohort mapping·중복, source generation 변경·삭제·crash·delta 0, daily 완료 후 cumulative timeout·다음 phase만 재개 |
| 후보 | kind별 machine/보조 모집단·미지원 사유, 원 확인점 필터/시각 변경 재생 차이, K/R/A/N·추가만 있는 후보·공통/U 최악 배치·selection UNKNOWN, 새로운 ask label·미래 AI 차용0, 과거/전향 cutoff·최대6·winner_group 전체 완료 |
| 운영/알림 | 회당/야간 budget·512MiB·자식 회수·날짜 유지, outside window 신규 연구 쓰기0·야간 latest_attempt/원 계산 receipt 분리, optional code rebind의 notify/start/history 보존, kind별 preview/parent/semantic ID·midnight active와 staged 구분·이행 중 오정정0·uncertain 보존 |
| 장중 무추가 | 실제 Main/WS/scanner/AI/order producer import/caller·기록 횟수·payload/정책 diff 0. 원 raw 자료 연결이 어려워도 writer 필드를 추가하지 않음 |

후속 코드 작업은 구현→자체 리뷰→보완→재리뷰→관련 pytest·compile·wrapper 변경 시 bash -n/계약 회귀→diff 검사로 종료한다. fixture/fake transport만 사용한다. 자연 16,722개 전체가 반드시 매칭될 것이라고 요구하지 않으며 적격 구간의 양성 연결과 나머지 결손 사유 보존을 확인한다. 연구 가격 경로 W/F/U를 실제 손익 검사로 대체하지 않는다.

### 8.3 실제 예약 소비와 마지막 소비

검증된 후속 배치가 허용되면 착수 시 최신 selected release를 부모로 **수리 파일만** 고정한다. 동시 joint/지연 작업의 dirty 소스·정책 parent·운영 승인·PID를 덮지 않는다. 연구 code hash가 바뀌면 현재 `verify_installed_calendar`가 실행을 보류하므로, 기존 optional installer의 자기 tag/code/calendar binding을 검증된 사본에 재결속하는 작업까지 배포 인계에 포함한다. 스케줄·notify_enabled·관리자 scope·기존 다른 cron bytes를 보존하고 `installation.json` 실제 재조회가 맞아야 설치 수용이다. 연구 때문에 Main을 재기동하지 않는다.

현 installer는 재호출 기본 `notify_enabled=False`이고 installed_at/source_date·evidence_start_date를 새로 산출한다. 따라서 일반 configure 재실행을 무조건 code rebind로 사용하지 않는다. 기존 설정/초기 설치 이력·source 경계와 새 rebind 시각/코드만 구분한 변경을 prepare→자기 tag 및 configuration 재조회로 검증한다. 원 source 경계는 current clean/forward 계약이 명시적으로 좁아지는 경우에만 별도 generation·제외 사유로 반영하며 일별/후보 history를 지우지 않는다. rebind 실패 시 유효한 이전 설정/cron bytes를 복구하거나 명시적 blocked로 남기고 새 설치 성공을 주장하지 않는다. 미래 실제 installer 변경은 관련 운영 문서/체크리스트와 같은 변경 세트로 수행한다.

알림 직전 parent는 **발송 당시 유효한 active current receipt**를 기준으로 읽기 전용 검증한다. night_id/source_date/자정 후 calendar date/다음 PREOPEN apply_date를 혼동하지 않는다. 다음 날짜의 staged policy 파일 존재만으로 parent를 교체하지 않으며 현재 파일을 actual PID 소비로 표시하지 않는다. 검사 중 pointer가 바뀌면 그 안내는 보류하고 새 active parent로 재검증한다. 기계 종류는 관련 기계 정의/before, 보조 이후 종류는 여기에 원 보조 binding까지 요구한다. frozen comparison과 해당 scope parent/current pointer의 작은 receipt를 사용하고 매 후보마다 전체 raw 원천/모든 역사 정책을 다시 scan하지 않는다.

일별/누적 보정은 다음 허용 야간에서 원 source date·영속 cursor로 작은 영향 범위만 처리한다. 현행 날짜와 오래된 pending을 교대하고 동일 원천 손실을 매일 반복하지 않는다. controller·원 producer·원 AI 비교·전체 과거 wrapper를 수동 재실행하지 않는다. 지연 작업의 예산 소모로 미완료면 `deferred`와 원 날짜를 남긴다.

생산 hash는 `source/projection → daily → terminal`, `daily/terminal → candidate_comparison → cumulative manifest/current → notification_disposition → attempt/night_summary`로 흐른다. 소비는 terminal에서 원 daily와 generation을 검증한 뒤 누적/후보·알림 disposition·야간 요약을 대사한다. current 포인터와 알림 receipt를 일별/비교 source hash에 역으로 넣지 않고 immutable 비교→누적 manifest의 자기 순환을 만들지 않는다. 예전 요약의 성공을 최신 시도의 성공으로 전용하지 않는다. 자체 optional 연구의 상태를 mandatory `STAGE_REGISTRY`, required cron, strict/finalization/PREOPEN 입력/기동 gate에 넣지 않는다. 늦은 결과 때문에 기존 controller/봉인/checklist를 재생성하지 않는다. **이번 현재 checklist 문서 변경의 기존 strict/PREOPEN 영향은 원 handoff owner가 최종 바이트 기준으로 검증**하며 과거 PASS를 현재로 주장하지 않는다.

Telegram은 현재 의미 기반 recommendation ID·현행 관련 parent·원 sent receipt·불확실 배송 계약을 유지한다. 후보 미적격은 정상 무발송이고, 코드/날짜/압축 형태 변경만으로 같은 수치를 새로 보내지 않는다. old outbox를 reset하지 않는다. source 복구·과거 연구 재생을 이유로 새 provider/Telegram 발송을 수동 시험하지 않는다. 향후 적격 수치는 before/after·Δ·W/F/U·근거 품질·연구 종류를 포함하며 정책 자동 적용은 없다.

## 9. 계획 리뷰와 문서 완료

자체 리뷰에서 종목 마스터뿐 아니라 압축 trace 누락, native 원 본문의 실제 저장 위치, 날짜별 global hash로 인한 누적 단절 가능성, 기계 후보의 고정 미식별, terminal의 join/label 결손 설명을 보완했다. gzip 재개가 prefix 반복 해제를 만들 수 있는 비용, code 변경 후 optional 설치 binding 미갱신, 복구된 역사 자료를 전향 결과로 오인하는 경로도 명시했다.

이번 수정은 이 계획과 원 계획의 후속 pointer, 현재 checklist의 **기존 stable ID 인계**에 한정한다. baseline 문서·코드·산출물·cron·외부 Project/Calendar는 변경하지 않는다. 검증은 로컬 링크·owner/authority·기존 checklist/AUTO 봉인 보존·공백 검사·print-only backlog parser다. 후속 구현에서는 실제 reader/API 권한 누출·부하·정답 연결을 위 회귀로 검증하기 전 수리 완료를 선언하지 않는다.

초안 문서 검증 이력: 새/원 계획의 실재 로컬 링크 45개와 인계 section의 링크 정상, print-only backlog 24개 중 현행 stable ID owner 1개, 원 checklist 인계 section 밖 바이트와 AUTO 봉인 SHA256 보존, 원 계획은 후속 pointer만 append, 공백 검사 통과. Python/거래 테스트·원천 재계산·운영 예약/전송 검사는 문서 작업 범위에서 실행하지 않았다.

### 9.1 실제 소비 경로에 대조한 계획 리뷰·보완

| 계획에서 부족했던 부분 | 실제 코드 근거 | 보완·수용 |
|---|---|---|
| gzip reader만 고쳐도 압축 날짜를 scheduler가 발견한다고 가정 | `discover_dates`는 plain glob만 사용 | discovery/pending/source_plan/reader/currentness의 공통 논리 원천 계약·comparison 없는 gzip-only 통합 회귀 |
| 60초 전체를 decode 시간으로 보고 hard kill/CRC 미완료 prefix 재실행이 모호 | 실제 worker는 preflight/process_date/cumulative/reconcile을 같은 reservation에서 실행 | 잔여 budget·EOF/CRC 선행 source commit·무재개 in-progress 처리·후속 phase 재개·장중 신규 상태 쓰기0 |
| 후보 manifest의 종류 추가가 실제 기계 평가/안내까지 이어지는지 불명 | selection/Aggregator는 PASS-only, notifier는 excluded-only·보조 문구/부모 고정 | kind별 모집단/parent/preview·추가/제외4영역·U 최악 배치·winner_group 완료·새 기계 후보의 끝 소비 회귀 |
| raw 약세를 사용자의 연속 확인 약세와 혼동할 수 있음 | attach_joins/selection은 raw WEAKNESS를 사용하고 reconstructed_active는 부가값 | 확인 latch를 primary로 고정·raw 진단 분리·2/3회/UNKNOWN/TTL·확인 사건 ID·실제/재구성 근거 표시 |
| semantic cohort 이행으로 기존 scope가 사라지면 잘못된 정정/재추천 가능 | recommendation_id와 reconcile은 기존 scope 키/부재에 의존 | 검증된 key/ID mapping·원 sent receipt 보존·미완료 이행과 실제 무효화 구분 |
| code rebind가 알림/이력/source 경계를 보존한다고만 서술 | configure_optional_cron은 기본 notify=false·설치 날짜/source 경계 재산출 | 자기 tag만 재결속·원 설정/history 보존·prepare/readback·실패 복구·source 경계 변경 별도 세대 |
| 자정의 current와 다음 PREOPEN 정책, source→consumer hash 순서가 모호 | parent 검사에서 calendar date로 reader 호출, 실제 비교 뒤 cumulative manifest 작성 | active current receipt·staged 구분·pointer 변경 보류·비교 종류별 parent·단방향 hash/receipt 연결 |

이번 재리뷰는 새 계획과 현행 owner의 인계 문서만 보완한다. 실제 수리·설치/코드 소비·자연 산출물·첫 적격 수치 안내는 WR0–WR5의 후속 검증 상태로 남긴다.

재리뷰 문서 검증: 새/원 계획 로컬 링크45개 정상, print-only backlog24개 중 현행 owner1개, 이번 owner section 밖 checklist 바이트·원 AUTO 봉인 SHA256 보존, 공백 검사 통과. 이번 회차는 두 문서만 수정했고 원 계획의 이전 pointer는 유지했다. 코드/거래 테스트·provider/Telegram 호출·보고서 재계산·예약/정책/배포 변경은 수행하지 않았다. native 본문 잔존·숫자 축 역할·큰 압축 원천의 허용 예산 내 완료 여부는 후속 WR0/표적 회귀로 확인할 항목이며 현재 해결됐다고 표시하지 않는다.

## 10. 2026-10-14 승인 구현과 수용 인계

사용자의 구현·반복 코드리뷰·수정보완 지시에 따라 WR1–WR4의 기존 장후 reader/순수 평가/outbox를 수리했다. 결과는 [구현 리뷰](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md), 후속 실행 owner는 [10/14 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 동일 `MainMarketWeaknessPostcloseObservation1008`이다. §1/§9의 계획 전용 범위는 10/13 이력이며 이번 코드 수정 권한과 구분한다.

gzip-only 날짜/종목 마스터·엄격한 alias 검증, 원 native 본문과 trace/label의 정확 연결, 확인 latch 기준, 검증된 scope 의미 누적, 역사 cutoff·후보별 계산 checkpoint, daily/cumulative/notification phase 재개, typed 후보/안내·의미 ID/설치 설정 보존을 구현했다. gzip은 한 연속 해제에서 physical/decoded hash와 EOF/CRC를 검증하며 완료 전에 만든 partition은 자기 staging에 둔다. 예산 중단/CRC 실패 시 부분 결과를 폐기하고 해당 세대의 무재개 원천은 건너뛰므로 같은 prefix를 계속 해제하지 않는다. accuracy/coverage 손실은 결손 사유로 남긴다.

실제 기존 Main/probe 표본의 `redacted=true`는 원 `signal_token`에만 해당하며 event/ask/본문 해시는 일치했다. 전체 redaction flag를 이유로 버리지 않고 필요한 필드와 각 해시를 독립 검증한다. 가려진 event/ask/identity는 복원하지 않는다. 보조 요청 input/prompt/schema와 원 component가 확인된 경우에만 scope binding hash로 정규화하며 기존 요청/응답을 수정하지 않는다.

기계 수치 연구는 원 정책에 검증된 역할/정의/unit/연산자/원 수치 계약이 있는 **원 확인점 tightening 필터**를 지원한다. 읽기 전용으로 확인한 현재 원 정책 표본에는 이 numeric role 계약이 없으므로 실제 기계 수치를 만들지 않고 `role_unverified`로 남긴다. root/FSM/재무장/확인 ask를 변경하는 완전 재생은 현재 producer가 없으며 `confirmation_replay_unavailable`이다. typed 분모의 추가/제외 통계 지원을 이 producer의 구현 완료나 실제 후보 발견으로 해석하지 않는다. 보조 이후 실제 PASS subset의 연구는 별도 분기로 계속 가능하다.

후속 코드 재리뷰에서 [8종 추가 결함과 수정 회귀](../audits/main-market-weakness-postclose-source-binding-implementation-review-2026-10-14.md#후속-코드-재리뷰와-수정보완)를 확인했다. 미지원 확인점 재생은 selection/알림에서 명시적으로 거부하고, 현재 두 필터의 추가 모집단은 0이어야 한다. 미완료 날짜·scope conflict를 비교/currentness/cache에 결속하며 오래된 철회/정정, 비교→manifest 중단과 projection 저장 실패의 재개 경로를 보완했다. probe BLOCK의 원 분류와 역할/특징/cutpoint별 capability 사유도 보존한다.

작업본 코드·fixture 검증의 완료와 실제 selected release 배포, optional code rebind, 다음 자연 예약의 원천 연결/phase/마지막 소비, 적격 수치 안내 및 실제 매매 효과는 별도다. 이번에는 배포·재기동·cron 수정·원 운영 보고서 재계산·provider/Telegram 발송·정책 발행을 수행하지 않았다. 후속 rebind는 기존 enable/notify/설치 이력/source 경계를 보존하는 수리된 installer를 사용하며 실패 시 원 cron/config 재조회까지 확인한다. 연구를 mandatory stage/PREOPEN/기동 gate로 추가하지 않는다.

## 11. 2026-10-15 처리 정체·근거 보존 보완 운영 계약

10/14 승인 배포 후 실제 야간에서 날짜 선택 정체와 원천 결손이 확인되어 사용자 후속 지시로 [처리 순서·관찰 근거 고정 구현 리뷰](../audits/main-market-weakness-night-progress-and-evidence-review-2026-10-15.md)의 보완을 수행했다. 현재 실행 owner는 [10/15 동일 stable ID](../checklists/2026-10-15-stage2-todo-checklist.md)다. 아래 규칙은 종전 latest/oldest 양 끝 선택 규칙을 대체한다.

- 원천 미완료/무효 날짜를 누적·알림 phase 재시도보다 먼저 순환 처리한다. `schedule_cursor.json`의 봉인된 위치는 밤 사이에도 유지한다. 실패한 날짜를 다음 시도의 독점 대상으로 삼지 않으며, 기존 cursor 날짜도 원천 소실의 명시적 결손 처리 대상으로 보존한다. 자정 이후 새 달력 날짜는 `night_id`를 넘어 처리하지 않는다.
- 정확한 기존 event/time/ask와 비용·성과 label 계약이 연결된 표본만 W/F로 평가한다. 빈 재생 partition과 상위 epoch 결손은 daily/terminal의 원천 사유로 전달한다. 보존된 종료·대사 영수증이 없는 과거는 U이며, 날짜 처리 수리나 진단 수리를 역사 성과 복구로 간주하지 않는다.
- 장후에 사용한 exact observer 상태 원 bytes/SHA를 자기 `observer_receipts`에 고정한다. 현재 관찰 상태의 이후 변경은 과거 세대를 무효화하지 않지만 실제 원 observation 변경·삭제와 고정 증거 손상은 계속 거부한다. archive 날짜는 snapshot 쓰기 전에 차단한다.
- 시간창 밖 쓰기0, 기존 9회/60초/600초/worker1/512MiB, 후보 동결·안내 기준, 장중 추가 부하0을 유지한다. 후속 배포에서는 자기 optional code binding만 새 검토본에 재결속하고 기존 설정/이력을 보존한다. 실제 야간의 중간 날짜 진전과 migration 종료·알림 disposition 확인 전 자연 수용 owner를 닫지 않는다.

## 12. 2026-10-16 날짜 완전성·최신 원천 처리·보고 보완 운영 계약

사용자 1~4번 구현·반복 리뷰·커밋 지시에 따른 보완이다. [구현 리뷰와 배포 인계](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md)가 검증 결과를 소유하고, [10/16 동일 stable ID](../checklists/2026-10-16-stage2-todo-checklist.md)의 자연 수용 OPEN을 유지한다. 이 절은 §11의 순환 규칙에 최신 원천 처리 기회를 추가하며, source-only·optional 권한과 원 evidence/후보/outbox 이력을 유지한다.

- scheduler·누적·현행성 검사는 설치 원천 시작일, clean/forward 정책 시작일 중 가장 늦은 시작일과 `night_id` 이하의 발견 날짜를 공유한다. `source_scope`에 시작일·상한일·대상 날짜를 봉인하고 아직 cursor가 없는 날도 `not_started`/`pending_source_dates`에 포함한다. 발견 후 원천이 사라져도 현행 manifest에 보존된 날짜는 남겨 다음 처리에서 명시적 source gap으로 종결한다. 새 원천 날짜·시작일·cursor 변경은 이전 비교를 무효화하며, 계산 중 대상 목록이 바뀌면 publish를 보류한다. 예전 `source_scope` 없는 비교는 현행으로 재사용하지 않는다.
- 최신 마감일이 원천 미완료이면 야간 첫 가용 처리 기회를 부여한다. 이후 현재 원천 결속을 통과한 in-progress 커서의 위치/partition/native 색인과 기존 label DB의 커밋된 loaded marker에 실제 진전이 있을 때만 backlog 한 번 뒤 최신일을 재개한다. 선택 직전 checkpoint를 기존 schedule cursor에 봉인하며 최신 재개는 `last_source_date`를 이동하지 않는다. 진전 없음·crash·원천/코드 변경·잘못된 checkpoint/index에는 우선 재개권을 주지 않으며 기존 backlog 순환을 유지한다. 과거일 처리 기회와 최신일 완주를 같은 야간 예산 안에서 교대로 보장한다. 자정의 다음 날짜는 대상에 넣지 않는다. 슬롯·예약 상한이나 EOD/정규 장후 우선권을 늘리거나 우회하지 않는다.
- 검증 가능한 야간 창 안에서 code/calendar 불일치·EOD 실행·야간 예산 소진·deadline 여유 부족으로 worker 시작 전에 보류한 결과도 lock 아래 `night_summary.latest_attempt`에 시각·사유·`worker_started=false`로 기록한다. 이 보류는 worker 예약 횟수·예약초·순환 위치·원 마지막 계산 bytes를 바꾸지 않는다. 최초 검사부터 시간창 밖이면 신규 lock/연구 상태 쓰기는 0이다. 다른 worker가 lock을 보유한 경우 그 writer의 요약을 덮지 않는다.
- `source_census.native_observations`는 native 색인에 공급한 유효 행 수로 바로잡고, 독립 분석행 수는 `source_projection_census`로 분리한다. `native_indexed_rows`는 중복 입력을 포함한 행 수이며 고유 관측/매매 기회 수가 아니다. daily JSON/Markdown과 terminal에 두 census·색인 수·`analysis_coverage.native_binding_verified`를 제공한다. gzip 중단/CRC 실패 시 색인·두 census를 같은 checkpoint로 되돌린다. 분석/재생/보조 모집단이나 W/F/U·후보 정의를 변경하지 않는다.
- 배포 전용 세션은 검토 커밋을 통합한 selected release에서 기존 자기 optional code/calendar binding을 재결속하고 설정·cron 재조회를 확인한다. 기존 enabled/notify·설치 역사·source floor·후보/outbox를 보존한다. 코드 hash 변경으로 기완료 날짜도 재처리 대상이 될 수 있으므로 한 야간의 전체 완료를 보장하지 않는다. 다음 허용 야간에서 최신 마감일 기회→기존 backlog 진전→migration/누적→알림 disposition을 수용한다. 연구 때문에 Main을 재기동하거나 과거 원천/보조 응답을 다시 생성하지 않는다. 후보의 새 전향 근거 부재는 알림 보류이며 실주문/정책 적용 권한이 아니다.


## 13. 2026-10-21 압축 이후 재결속과 일일 인계

기존 `process_date`가 완료된 projection의 원 source manifest·terminal·daily 해시와 집계 수치, 코드·관찰·정책 의존성을 먼저 검증한다. gzip 전환만 달라졌으면 원 전체 읽기 해시 또는 연속된 전체 byte-range 해시를 새 압축본의 해제 원문·EOF/CRC와 대조한다. 기존 `verified_sources`에 물리 세대별 증명을 캐시하고, 같은 증명은 재독하지 않는다. 검증된 projection ID와 원문 참조는 그대로 두고 부모 manifest를 명시한 후속 generation을 발행한 뒤 기존 cumulative→notification 경로가 소비한다. 원 비교는 후속 누적 발행 전까지 current=false다. 종목마스터는 native 검증을 거친 같은 논리 경로·semantic hash인 경우에만 재사용한다.

해시가 없는 과거 입력, 코드·내용·원천·의존성 변경, 불완전 coverage는 기존 제한된 재처리 경로를 사용한다. CRC/세대 변경·budget 실패는 원 cursor를 보존하며 완료로 발행하지 않는다. 원문 수집기는 앞으로 plain native stream도 기존 읽기 중 전체 해시를 남긴다. 별도 raw 재스캔, 크기·시간 한도 확대, 상위 원천 생성 또는 매매 기준 변경은 없다.

`MainMarketWeaknessPostcloseObservation1008`은 기존 checklist builder의 OPEN 인계 대상이다. 전일 OPEN의 stable ID·Acceptance·History를 보존하며 target의 명시적 종료/기존 항목이 우선한다. 현재 owner는 한 건이어야 하며 completed/absent는 다시 만들지 않는다. 수집 종료 증빙은 기존 collector→canary closed→normalized source→operating replay→weakness consumer가 소유한다. 종료 증빙 없는 과거 epoch를 소급 승인하지 않는다.

이번 권한은 배포본 준비까지다. 실제 전환 시 기존 설치 enabled/notify/calendar/예산을 유지한 optional code binding 갱신이 필요하다. 이후 기존 야간 worker가 최신 마감일→backlog→누적 currentness→알림 disposition을 확인한다. 지금 재기동·selector 변경·cron 변경·보고서 재발행·Telegram 호출을 실행하지 않는다. [검토 기록](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md#압축-재결속수집-증빙일일-인계-배포-후보--2026-10-21).

후속 장후 복구의 installer는 canonical workspace를 공유 원천·예약 owner로만 사용하고, 실제 실행 중인 연구 코드의 기존7개 의존 파일과 launch wrapper를 선택된 불변 release와 대조한다. mutable workspace가 이전 코드라는 이유로 검토된 selected installer를 거부하지 않으며, 실제 실행/선택 코드·의존성·wrapper 불일치는 계속 거부한다. 기존 installer의 자기 tag 재결속·readback/rollback과 enabled/notify·설치 이력·source floor·예산·후보/outbox 보존을 유지한다. 알림은 코드 결속 불일치와 calendar 불일치를 구분하고, 개별 작업 source 역할·마지막 완료 source·누적 through-date/거래일 수를 함께 전달한다. 누적 처리 범위와 원천 결손 해소·새 코드 재계산·경제 적격은 별도 판정이다. 실제 반영과 원천일10/21의 재생성·최종 소비는 [현재 장후 복구 기록](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md#장후-모니터링-확장과-설치날짜-표현-수리--2026-10-21)의 미종결 수용을 따른다.


### 10/21 장후의 부분 partition 제외 집계와 지정일 복구

유효 replay point가 남은 partition도 normalized source의 원 제외 수를 daily/terminal에 전달한다. 원 raw 행 제외 수와 projected opportunity 수는 다른 단위이며 서로 차감하지 않는다. partition의 마지막 chunk에서만 원 제외 수를 commit하여 중간 재개와 다중 chunk에서 중복 집계하지 않는다. 원 source epoch 결손과 비용/정답 null은 유지한다.

명시적으로 지시한 장후 지정일 보고서 복구는 기존 supervisor의 `--scheduled --source-date YYYY-MM-DD`로 수행한다. 설치/calendar·야간 창·정규 장후 우선권·동일 worker lock·9회/600초 야간 예약·60초 child·512MiB·retained source 범위/마감일 이하 검사를 그대로 적용한다. 자동 cron의 backlog 순환은 변경하지 않으며 예약/최신 우선권 cursor를 수동 수정하거나 child 예약을 따로 만들지 않는다. worker 직접 CLI는 기존 supervisor parent/예약 검증을 유지한다. 지정일 재생성은 원천/정책/주문 권한을 부여하지 않는다.

## 14. 2026-10-22 실제 판정의 장후 경로 라벨과 제한 복구

사용자는 장중 추가 로깅 없이 실제 판정과 라벨의 연결 원인 수리·반복 리뷰, 과거7거래일 재처리와 누적/알림 판정 재검증을 지시했다. §13의 당시 준비 범위와 구분해 이 단회 닫힌 원천 복구를 실행한다. Main selector/재기동·cron/설치 설정·주문/정책 변경 및 Telegram 시험 발송은 포함하지 않는다.

기존 `label_index`는 저장된 확인 리플레이 기회만 색인했다. 실제 WS 이벤트의 epoch/route sequence와 collector의 epoch/series sequence는 서로 다른 namespace이며, 같은 사건이 리플레이 FSM에서 재확인된다는 보장도 없다. 기존 native observation으로 검증한 사건을 frozen normalized source의 선언된 `native_transport_epoch/native_route_sequence`·종목·item·venue/session·기록 시각·actual ask에 정확히 연결한다. 시간의 근접 매칭이나 collector namespace의 대입은 금지한다. 같은 기존 `continuous_reversal.label`과 비용.0023·목표 순+.4%·soft stop 순-3%·1800초 계약으로 CF 라벨을 계산하며 실체결/손익으로 표시하지 않는다.

기존 JSON streaming owner가 해시 결속된 partition의 gzip EOF/CRC와 metadata를 확인한 뒤 한 종목씩 공급한다. 연구 generation 안에서 partition 완료를 기존 SQLite label index에 checkpoint하여 trace chunk마다 다시 읽지 않는다. 신원 충돌·변경 ask·제외 row·경로 단절/부족은 U이고, WS namespace가 기록되지 않은10/9 이전의 확인된11열 역사 형식은 U로 보존한다. 현재/알 수 없는 schema와 신원·시간·출처 변경은 계속 거부한다. 새 source reader와 경로 label kernel도 기존 code binding에 포함한다.

라벨 의존성 실패는 trace 원천 불량으로 분류하거나 압축 trace를 다음 source로 이동시키지 않는다. 해당 압축 source의 미확정 staging을 되돌리고 같은 source에서 pending을 유지한다. 원 실패와 이전 산출물은 보존하며 결정적 실패의 동일 재시도를 중단한다.

기존 selected producer로9/29·9/30·10/2·10/6·10/7·10/8·10/12를 worker1/512MiB·단계60초·전체600초 이내 단회 재처리한다. 수리본의 code binding 변경으로 나머지7일도 무효화되므로 기존 canonical 연구 namespace에서9/29~10/21의14일까지만 단회 복구·검증한다(전체900초, worker1/512MiB, 단계60초). 장중10/22 원천 본문은 읽지 않는다. 외부 source anchor·동결 observer 출처 검증이 거부한 격리 입력 root를 허용하도록 guard를 바꾸지 않는다. 원 실패와 중간 시도를 보존하고, 이 실행을 정기 야간·선택본 교체·설치 재결속으로 표시하지 않는다. 정기 소비는 통합 배포 후 native optional installer의 code/calendar 결속과 다음 야간을 별도 수용한다. 결과·대체/제거·회귀·원천 결손은 [기존 리뷰](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md#실제-판정의-경로-라벨-수리와-제한-재처리--2026-10-22)에 기록한다.


## 15. 2026-10-22 effective registry·과거 제한 복구 계약

registry가 선언된 자연 판정은 원 native request/hash와 실제 G registry binding, logical schema, v2 wire/decoder 및 원 overlay/inheritance의 scope·확인 시점으로 검증한다. 기본 binding fallback은 미선언 자료에만 남긴다. immutable provenance는 검증된 파일 identity/coverage로 cache하고 행별 request/wire/시점 검증은 유지한다. 공통 source dependency는 cursor에서 경로별로 한 번 소유하며 index/projection에 반복 복제하지 않는다. missing/수정된 dependency는 다음 검증을 무효화하되 해당 row의 증거 결손을 전체 입력의 임의 PASS나 실행 허용으로 바꾸지 않는다.

raw auxiliary response 계약과 응답 후 실행 guard 계약을 분리한다. 실제 raw PASS를 보존하면서 기존 실행 rejected/unknown은 post-auxiliary 효과 분모에서 제외한다. registry 검증 실패, `historical_reader_compatibility_missing`, epoch/path/horizon의 label U 및 `role_unverified`를 같은 표본 부족으로 표시하지 않는다. 과거 호환 증빙이 없으면 original reader/source SHA로 native owner에서 먼저 검증하며 임의 compatibility receipt/강제 PASS를 만들지 않는다.

사용자 승인 단회 closed-source 복구는 기존 namespace lock·nice/resource supervisor와 native custody context에서 지정7일만 처리한다. `cumulative(from_date=...)`는 recovery_from_date/configured 시작일을 source scope에 함께 봉인하고 currentness/notifier가 같은 범위를 소비한다. 이전 기간은 immutable 진단으로 보존하며 검증하지 않은 이전 날짜를 새코드 current로 합산하지 않는다. 변경된 잘못된 binding의 후보는 재동결하고 이미 보유한 날짜 이후 cutoff를 적용한다. 장중 logger/판정/provider/주문·정기 cron/selector/PID 변경 권한은 이 단회 복구에서 발생하지 않는다.

구현·실제7일 소비와 남은 과거 증빙/원천·기계 capability는 [원 owner의 10/22 수용](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md#effective-registry-결속-수리와-7거래일-제한-복구--2026-10-22)에 기록한다.


### 라벨 색인의 제한 시간과 진행 보존

`MainMarketWeaknessPostcloseObservation1008`은 기존 native projection→label_bindings.sqlite→daily/cumulative/notifier 경로를 소유한다. 각 봉인된 projection partition의 라벨과 loaded marker는 한 transaction으로 커밋한다. 제한 시간·중단·다음 partition의 손상은 이미 검증된 partition을 되돌리지 않으며, 재개는 그 marker 이후만 읽는다. 부분 partition은 marker 없이 rollback하고 원 SHA/새 generation/원천 currentness 검증은 유지한다. native path 라벨의 정확한 WS identity·clock·ask·누락/충돌 판정은 바꾸지 않는다.

정기 예약의 60초 회차·야간 총600초·회차 수·06:30 종료 제한과 기존 source-date 회전은 유지한다. 동일 결정적 실패의 전체 재실행 대신 기존 cursor/SQLite의 실제 진행을 확인한 뒤 남은 원천만 재개한다. 코드 변경으로 무효화된 이전 날짜는 migration pending으로 남기며 원 U/null이나 과거 세대를 새 코드 current로 재표시하지 않는다. 장후 수용은 daily의 실제 라벨 결속·정확 날짜와 cumulative/notifier의 같은 세대 소비를 구분한다. Main 발행·기동 권한은 이 advisory 보고서에서 발생하지 않는다.


### 최신 원천의 검증된 checkpoint 재개

최신일 1회 뒤 다른 결손일이 하나라도 있으면 최신일을 모든 후속 슬롯에서 제외하던 조건은, 새 label writer가 partition을 커밋해도 그 야간에 이를 소비하지 못했다. 기존 label_index 실제 writer와 scheduler를 함께 검증해 이 실패를 재현했다. 기존 source selector에서 위 §12의 교대 규칙으로 대체한다. checkpoint는 read-only SQLite의 작은 loaded 표만 조회하며 labels/full source를 재조회하거나 writer를 열지 않는다. 첫 생성·새 generation의 실제 진전, 동일 generation의 커밋 증가, 무진전·stale·alias·잘못된 형식과 예산 만료를 구분한다.

최대9회/예약600초·회차60초·512MiB·EOD/정규 장후 우선권·06:30 종료·원 자식 회수·동일한 cron과 source-only 권한은 유지한다. 코드 hash 변경에 따른 기존 보고서 재처리는 정상 migration이며, 이미 소진한 야간 quota를 초기화하거나 worker를 직접 호출하지 않는다. source22의04:39 계산은 원 generation/as-of와 결손을 보존한다. 다음 허용 야간 source23→10/24의 최신일 다회 checkpoint 재개와 backlog 교대·daily/누적/notification 실제 소비를 기존 MainMarketWeaknessPostcloseObservation1008에서 자연 수용한다.


## 16. 2026-10-23 과거 15거래일의 제한 복구와 역사 검증

사용자는 현재 코드로9/29~10/22의15거래일을 제한 재처리하고 누적 비교·알림 판정을 재검증하도록 승인했다. 이 단회 source-only 복구는 기존 namespace lock·native custody context·nice19·worker1/512MiB·단계60초·누적 연구 실행600초(검토·읽기 전용 대사 경과시간과 구분)를 사용한다. 원천일10/23은 읽거나 생성하지 않는다. 이미 소진한 정기 야간9회/예약540초, 설치/cron·selector·Main PID/정책·수동 veto·outbox를 보존한다. checkpoint가 진전할 때만 남은 입력을 재개하며, source/코드 변경·결정적 실패·자원 한도에서는 중단한다. 예산 초기화나 무변경 전체 재시도는 하지 않는다.

과거 source의 reader hash가 현재와 다르면 기존 native compatibility owner의 exact bundle/source/old/new-reader 증빙을 요구한다. 그 증빙은 원 hash의 코드 inventory 아래에서 실제 실행한 원 native overlay/inheritance 검증, 원 lineage·registry/binding 결과와 물리 SHA를 연결한다. 연구 reader는 이 원 검증과 현재 registry·실제 request/schema/wire·scope/시점을 확인한다. 현재 매매를 시작할 수 있는지 확인하는 native 실행 검사를 역사적 연구 기록에 대신 적용하지 않는다. 원 현재 실행 검사·provider·주문·hard guard는 변경하지 않으며, missing/수정된 코드·증빙·원천·미확정 가격경로는 계속 unverified/U다.

입력 사전검사 차단과 판정 전 계약 거부는 `not_adjudicated`로 보존하고 원 오류를 기록한다. 원 사건/ask가 없으므로 라벨을 만들지 않는다. 명시된 machine-only probe stage는 probe로 구분한다. 알 수 없는 native 결속 누락은 기존 오류를 유지한다. 이번 수용과 정기 선택 코드/설치 재결속·다음 source23→10/24 자연 수용은 별개이며 [기존 리뷰](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md#2026-10-23-15거래일-제한-복구와-역사-reader-결속)와 `MainMarketWeaknessPostcloseObservation1008`에서 관리한다.
