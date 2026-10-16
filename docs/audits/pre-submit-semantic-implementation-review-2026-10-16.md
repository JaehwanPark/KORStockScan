# 매수 지연·의미감시 구현 리뷰 — 2026-10-16

## 범위와 권한

사용자 승인에 따라 현재 selected6c97e83f1에서 격리 구현한다. 현재 정책/PREOPEN/수동·퇴역 custody와 안전 guard를 보존하고 정확한 코드 인계 후 ordered 배포한다. 원 실패 배포·기존 source gap·원장 bytes를 보존한다.

## 확인된 원인과 수정

- native producer의 continuous_reversal matched branch와 delay reader의 필드/구 catalog가 달랐다. UNION의 primary null을 허용하고 extended catalog의 정확한 definition refs를 고정해 세 경로에 같은 helper를 적용한다. v4 hash에 matched/refs/상황/선택 시간을 포함하고 구 v2/v3 digest를 유지한다.
- sharded reader가0초 cell을 삭제해30초 상위 정책으로 떨어졌다. 지원되는0초 cell도 메모리 lookup에 유지한다.
- canonical data와 release/data symlink의 문자열 비교로 실제 같은 요약을 unobservable로 만들었다. resolved source와 동일 세대 stat을 검증한다. 원 producer가 최근20분 집계를 게시해 반복 전체 JSON decode를 줄인다.
- signal_ready의 모든 후행 호가가 있어도 주문 terminal을 요구했다. 관측 완료와 실제 price_ready 주문 terminal을 분리한다. 실제 stale/clock-invalid 호가 제외는 유지한다.
- machine/auxiliary/joint comparison, 봉인 적용일/다음 예정일을 분리한다. optional 약세 연구는 기존 감시·incident·owner에 연결하며 native calendar·scope·cursor currentness를 확인한다.
- 과거 재분류는 exact machine SHA/evaluation/symbol/parent/causal capture가 일치할 때만 수행한다. SQLite와 날짜별 단일 스트림을 사용하고 plain/gzip logical seal을 보존한다. 원 commit/quote 해시는 변경하지 않는다.

## 검증과 실행 증거

증거 디렉터리: `/home/ubuntu/KORStockScan/tmp/pre-submit-semantic-20261016/`. 초기 core904개, monitor318개 회귀가 통과했다. 추가 native join/압축 무결성·signal terminal·alias 회귀에서 발견한 catalog legacy definition hash 누락과 fixture route 표기를 보완했다. 확장 회귀와 exact 후보 인계는 진행 중이다.

코드 closure, 불변 후보 선택, 새 PID 소비, 자연 v4 생성, 장후 정책 생성, 비용 후 성과는 별도 판정한다. 현재 자연/배포 완료를 주장하지 않는다.

## 남은 수용

최종 반복 리뷰/확장 시험→exact active-policy/code handoff→ordered drain/select/start/consumed→bounded observer→영향 범위 장후 projection 및 재계산의 native terminal을 확인한다. 현행 당일0초 정책을 재기동에서 그대로 소비하며 후속19일 정책 준비는 별도 generation으로 보존한다.


## 배포 전 코드 closure

최종 core1,271개, 계약2,554개, source/인계2,316개 및 별도 호환성2,434개 묶음 PASS(중복 포함; 합산한 고유 시험 수로 표시하지 않음). 압축 전환·CRC/내용/late/충돌 alias6개 PASS. Python compile, exact reviewed source7개와 추가 dependency2개 SHA, diff 및 print-only parser를 검증했다. 리뷰 범위의 미해결 코드 finding0이며 배포·자연 수용은 아래 실제 영수증으로 별도 갱신한다.

동결된 당일 요약9,251행+fixture1개에서 producer 최근 구간118행의 count/identity parity를 확인했다. 같은 프로세스 warm 기준 full8,790,806B→manifest35,041B, native 읽기 중앙값89.081ms→bounded 읽기/해시0.253ms, 상황 조회 p95 12.324µs, 최초 writer 이관0.116초다. 실제 Main 주문 latency 개선이나 cold I/O로 해석하지 않는다. `performance.json`과 `targeted-validation.json`에 원 snapshot SHA/시험 로그를 결속했다.

후속 리뷰에서 압축 pipeline의 물리 파일명 변경을 원천 유실로 보던 delay ledger 경계를 수리했다. 원 ledger를 다시 쓰지 않고 original logical SHA/byte 수와 전체 gzip CRC를 검증한다. 검증 cache는 최대64개 metadata/digest이며 append·inode/ctime/alias 변경을 다시 검증한다. 재계산은 완결된15일 원천을 먼저 격리 생성하여19일 target으로 검증하고, 현재16일 정책/PREOPEN pointer를 보존한다.16일 당일 누적 정책과 전체 strict/controller는 정규 장후 수용이 소유한다.


## 첫 배포·원천 재생 결과와 관측 대기 보완

30cffe251의 active policy source1,198개와 native37파일 동일 SHA를 확인하고 fresh rising86개/holding99개 network-denied fixture를 발행했다. 정규 ordered 전이는17:01:52.935897 완료, 새PID131879/start20162156이며 original policy unchanged다. 새 producer PID의 recent projection 게시/flush error0을 확인했다.

기동 후 구 cursor 이관의10분 관측 창 확보 시간을 `raw_source_unobservable_with_summary`로 세던 추가 오경보를 발견했다. 원천이 실제 unobservable일 때만 해당 결손을 내고 partial window는 `raw_observation_window_pending`으로 표시한다. malformed/backlog 결손과 기존 incident를 보존하고 완전한 관측을 확보하기 전에는 healthy/recovered로 바꾸지 않는다. 관련3,092개 PASS 후 같은 승인/인계 절차로 후속 배포한다.

10/15 완결 원천을10/16 발행·10/19 target으로 격리 재계산했다. qualified267개/P0 220개/price pairs255개를 보존했고 상황 UNKNOWN267→29, 실제 상황15종+UNKNOWN, cell97→195, 양수 price cell0으로 초기0초를 유지한다. native capture163개에서 anchor238개를 exact join했으며 원천 날짜 전체 제외0이다. 원 호가 clock/hash169개·generation/epoch70개 제외와 native/parent 미확인 표본은 보존했다. canonical10/16 정책/과거 sealed stage를 바꾸지 않았다. 후속 cursor 코드 세대와는 같은 qualified projection을 native 검증 후 재사용해 최종 artifact를 결속한다.


## 후속 소비자 인계 결함과 수정

첫 기동의 Sentinel producer는 `summary_contract_migration_parser_predecessor_unverified`로 실패했다. Main 정책/PID 소비 성공과 감시 producer 실패를 분리하여 보존한다. pipeline_event_summary의 producer publish 메서드 변경으로 파일 SHA가8500f482…로 바뀌었지만 summary migration owner의 CURRENT pin이b1b1e59a…였다. complete AST에서 `ProducerSummaryCompactor._publish` 이외 모든 parser/aggregate/checkpoint/callback 코드는 동일함을 확인했다. 원 parser/callback 쌍과 기존 세대들의 허용 관계를 보존하면서 정확한 b1→8500 인계를 추가했다. default callback과 실제 funnel callback, archive/append-only/변조/경합 및 BUY/감시를 포함한1,095개 PASS다.

원 b1 parser owner가 기존 checkpoint1672470738부터1707394599까지 실제 suffix만 이어 읽었다(`rebuilt=false`, 원 정책/PID 변경0). 원 manifest는 증거 디렉터리에 보존했다. 추가 code handoff의 c8366cfb0 후보는 미선택이며, cursor 보완과 이 parser 수리를 함께 최종 후보로 배포한다. 최종 배포 전 실제 native migration을 기존 producer lock 아래에서 검증하고, 첫 full 감시의 새 PID/source generation을 확인한다.


## 현행 장후 capability 재대사 보완

bbb9d46b7 전이는17:18:23.838565에 완료했고PID157049/start20261178의 exact 정책 소비를 검증했다. 실제 b1→8500 parser 이관은 원 checkpoint1707394599부터1725882736까지18,488,137B만 이어 읽었으며 rebuilt=false와 원 manifest archive를 확인했다. 새 PID의 Sentinel producer는 success이며 전체 observer는 scanner 평가 모집단 미관측을 partial로 보존했다.

전체 감시에서10/15 실제 취소대기 b2a2017… 및 상승누락 dde49a… 보고서 세대가 exact successor 목록에 없음을 추가 확인했다. 원 fixture의 Git05b78a401/77eaf86fe와 현재 component bytes를 대사하여 두 origin generation을 재현했다. 취소대기 차이는 잔여 주문 source-only 귀속, 봉인 census의 plain/gzip 검증 및 bounded projection, stop release 관측과 delay bootstrap 검증 경계이며 현재 source/comparison/publication/reader fixture를 독립 검증했다. 상승누락 자체 producer/선정 모듈은 동일하고 공유 handler·delay bootstrap·공통 contract membership 파일이 변경됐다.

기존 exact preserved-source map에 두 쌍만 추가하고 원 보고서/fixture/원천 hash·comparison/handoff를 보존한다. 실제 native probe에서 두 family의 current_code_capability_verified=true, 취소대기 model_unvalidated/incumbent_carried, 상승누락 valid_empty/incumbent_carried가 유지됐다. 권한·source·receipt·보고서 경합·미등록 쌍 거부를 포함한571개 PASS, compile/diff PASS. 증거: capability-source-review.json, capability-native-probe.json, verified-capability-successor-tests.log. 기존571개 시험 대상 코드와 구 코드 시험 로그를 구분했다. 이 보완은 신규 정책 선정이나 경제성 승격이 아니다.

최종 delay 재계산은 qualified267/P0 220/price pair255와 동일한 source SHA를 유지하며 source_decode_passes=0, minimal_projection_reused=true로 완료했다. policy SHA f8c911dd…/code contract ae1aac66…이며 추가 capability map 변경은 delay contract 구성 파일을 바꾸지 않는다.
