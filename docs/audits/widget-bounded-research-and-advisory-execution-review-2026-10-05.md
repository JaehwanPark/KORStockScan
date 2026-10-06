# Widget 종목 선별 연구·자문 누적 진단 실행 리뷰

## 1. 결정과 실행 범위

사용자의 두 계획 실행 지시에 따라 R0~R4와 D0~D5의 격리 계산 및 코드 보완을 완료했다. 기존 Main/삼성 기계 연구와 다른 population이다. 새 거래 정책의 선택·발행·배포·기동은 실행하지 않았다. 동일 자료의 추가 grid 탐색은 종료한다.

- 종목 연구: seed4와 명시 등록 watch13의 합집합17만 사용했다. 기존 catalog636/연구100/관측98과 구분했다. 현재 dated 실행 정책의 `symbols={}` 및 관측 seed4는 보존했다.
- 자문 진단: 삼성005930·두산034020·한화042660만 사용했다.
- source10/2, 실제 계산·발행일10/5, effective10/6을 구분했다. 다음날 봇의 PID 소비는 사용자의 지시에 따라 검사하지 않았다.
- 다음날 정책/준비 문서10개와 기존 발행 보고서의 bytes를 보존했다. [공통 검증](../../tmp/widget-research-plan-execution-20261006/validation.json).

## 2. 종목·기간 연구 결과

[계산 원본](../../tmp/widget-symbol-profitability-redesign-20261006/final/report.json)의 manifest는 코드·비용·watch 목록·dated 관측 catalog·동결 후보·스냅샷·원천 동결 receipt를 결속한다. API를 호출하는 backfill 함수와 전체 grid는 실행하지 않았다.

계획의 forward3일은 완성 분봉 저장소의10/1 가격 및 동결 receipt를 추가 확인해 **4일**로 정정했다. 자문 WS 실패일을 완성 분봉 연구에서도 삭제하는 것은 서로 다른 원천을 혼동하는 일이다. Main 연구의 기존3일 범위는 변경하지 않았다.

| 원천 처분 | 종목수 | 내용 |
|---|---:|---|
| 같은4일과 사전 동결 kernel 지원 | 7 | 006800·010140·047810·080220·100790·138080·475150 |
| 공통 날짜 원천 불완전 | 8 | 결손일을0수익으로 채우지 않고 순위 비교에서 제외 |
| 동결 kernel 결손 | 2 | 001550·093370. 후성093370은 가격이 있어도 kernel 결손을 수익성 탈락으로 바꾸지 않음 |

비교 가능7종목에서 독립 모형 에피소드16개를 재생했다. SK이터닉스475150은 정상4일 무신호이며 일별 분모에 포함했다. kernel·청산·등록 cap·cooldown을 고정하고 종목 선별 방식2개만 비교했다. 원 BBO/체결/자본 receipt와 결속되지 않은 모형이므로 **실행 가능 KRW 순이익과 실제 손익은 null**이다.

전체 비교에 같은4개의25% 자본 slot을 사용했다. 제외된 종목의 slot은 현금으로 남는다. 학습 구간은9/29·9/30·10/1, 비교일은 이미 사용한10/2이며 새로운 독립 holdout이 아니다. 순위는 학습 결과만 사용한다. stress는 진입1틱 불리·청산1틱 불리라는 민감도이며 실제 호가라고 주장하지 않는다.

| 구성 | 학습 일평균 자본수익률 | 학습 stress | 10/2 비교 | 10/2 stress |
|---|---:|---:|---:|---:|
| 기존 seed4 | -0.0904% | -0.1774% | -0.3411% | -0.4204% |
| seed 양수 subset: 삼성중공업 | +0.0138% | -0.0032% | -0.1208% | -0.1460% |
| 등록 범위 양수 subset: 삼성중공업·한국항공우주 | +0.0497% | -0.0199% | -0.1208% | -0.1460% |

구성 축소가 이 자료에서 손실을 줄였지만, 비용 민감도와 비교일에서 수익 패턴을 확보하지 못했다. **운영 교체 권고 없음, 지원 부족/기간 효과 미식별**로 종료한다. 최근20/40 상한은 현재 같은4일로 축약된다. 기존25일/독립 holdout16일 조건을 제거하지 않았으며 성공100%/80% 보존 veto도 추가하지 않았다.

## 3. 자문 원천·누적 대사

[격리 진단](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/report.json)에서4일×3종목의 원 JSONL을 재생했다. 저장 평가와 source/candidate/actionable/중복/성숙 행수 및 전체 outcomes의 차이는0이다. 여러 horizon의 outcome 행수를 독립 사건 수로 합하지 않았다.

| 종목 | 역사 누적의10분 선도달 | 8월 | 9/29 이후 확정 | 10/2 독립10분 기회: 목표/손절/미도달 |
|---|---:|---:|---:|---|
| 삼성 | 80 | 59 | 6 | 9: 2/2/5 |
| 두산 | 8 | 5 | 0 | 3: 0/0/3 |
| 한화 | 24 | 15 | 1 | 1: 0/0/1 |

누적112건·8월79건과 삼성 target 제외76+target4=80이 일치한다. 이는 저장된10분 가격 평가의 통계다. 일부 과거 raw는 owner 디렉터리에 없어 모든 역사 결과를 원 raw에서 재현했다고 주장하지 않는다. identity가 없는 과거 행도 native 독립성 입증과 구분한다.

10/1은 삼성680·두산390·한화390, **1460개 DATA_WAIT**, `current_price=null`이며 WS 이슈는 `widget_ws_input_unavailable:widget_ws_source_unavailable:snapshot_stale_or_future`다. evaluator의 가격·시각 조건을 통과한 행0은 **유효한 무신호일이 아니라 가격 원천 결손**이다. 그날의 별도 완성 분봉은 종목 가격 연구에 사용할 수 있다. WS의 과거 epoch를 새 분봉으로 합성하지 않는다.

누적 proxy에서 손절 선도달 뒤 MFE가 목표에 도달하면 복구 수익을 표시할 수 있다. 이는10분 가격 proxy이며 실제 손절·fill·청산 손익이 아니다. 새 confirmation 선택은 이 proxy와 분리된 exact BBO paired 계약을 사용한다.

| session | 새 후보 비교의 원천 | 처분 |
|---|---|---|
| 삼성 정규장 | forward5219행, last-trade/초기·leg fill/틱 add trigger/guard/평균가/terminal 완전행0 | `scale_in_runtime_trigger_source_missing`, confirmation3 승계 |
| 삼성 장전 | 역사4경로 중9/29 이후10/2의1경로만 적격 시대로 남음. 2/3 양 arm이 base/stress 모두 검열 | `paired_outcome_incomplete`, confirmation3 승계. 수익0 아님 |
| 두산 정규장 | 가격 자문 평가는 실행되지만 trading baseline 없음 | 의도된 관측 전용, confirmation3 승계 |
| 한화 정규장 | 같은 baseline 부재 | 의도된 관측 전용, confirmation3 승계 |

10/6 dated loader는 네 session 모두 `dated_policy_loaded`, confirmation3을 반환했다. 이는 read-only loader 검증이다. 실제 다음날 PID 적용이나 자연 주문의 증거가 아니다. confirmation은 표시뿐 아니라 actionable 상태 승격 및 entry eligibility에 간접 영향을 주므로 무권한 표시값이라고 축소하지 않는다.

## 4. 실행 세대·연결·보완

[실행 세대 대사](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/execution-context.json), [연결 표](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/connection-table.json).

20:10 자연 attempt와21:22 recovery는 다른 run ID/code SHA다. 두 receipt의 seal과5개 원 산출물 해시가 현재 파일과 일치했다. 20:10 자연 attempt가 publication10/2를 기록한 반면 실제 수행·발행은10/5였다. 원 receipt는 보존하고 새 wrapper가 publication을 별도 전달하도록 수정했다. 현재 unit의 ExecStart로 과거 실행 코드를 추정하지 않았다.

추가로 과거 widget stage 지문은 shell이 간접 호출한 자문 계산 모듈을 포함하지 않았다. 따라서 과거 stage hash만으로 모든 producer bytes를 증명할 수 없다. 새 stage 지문은 관련 producer/consumer11개를 포함하며 코드 변경 시 stale 재사용을 거부한다. 기존 episode stage의 결속은 이 변경으로 늘리지 않았다.

| 리뷰 finding | 보완·회귀 |
|---|---|
| 최근20일 안의9/29 이전 pair가 새 후보에 유입 | 새 loader/study/selector의 forward 하한. 구 receipt는 read-only 검증만 허용, 신규 selection 재사용 금지 |
| 복사·misdated 보고서가 누적에 중복 가능 | JSON 읽기 전 filename 날짜 범위 및 payload target 일치 검증 |
| 격리 재생이 canonical `.incumbents`에 쓰기 | snapshot directory를 명시 지정하는 격리 인자 |
| 역사 proxy와 신규 후보 분모 혼동 | 보고서의 역사 metric role와 candidate 최소 날짜 명시 |
| source 날짜가 publication receipt를 대신함 | wrapper의 별도 publication 인자 및 실행형 stub 회귀 |
| 간접 producer 변경이 stage 지문에 누락 | stage 코드 dependency 결속 및 widget/episode 범위 반례 |
| 원천 읽기 atime 갱신을 데이터 변경으로 오판 | inode/size/mtime/ctime generation 검사, atime 회귀 |
| malformed 자문 shape에서 진단 중단 | invalid/duplicate/shape 행수 보존 반례 |

## 5. 재사용·보관·후속 소유자

같은 universe/원천/parent/cost/window/code 지문일 때만 checksum으로 봉인된 보고서를 재사용한다. 새 날짜에는 사전 검증된 kernel/day별 계산을 재사용하고 변경된 입력은 다시 계산한다. 실패·손상 cache는 carry PASS로 처리하지 않는다. 일별 계산은32개, 새로운 grid 평가0이다. [cold](../../tmp/widget-symbol-profitability-redesign-20261006/final/report.json)와 [reuse](../../tmp/widget-symbol-profitability-redesign-20261006/final/reuse.json)의 wall/CPU/RSS/실제 process read chars를 별도로 측정했다. import 이후의 진단 실행 구간 측정이며20:10 전체 nightly 실행과 동일 작업의 속도 비교는 아니다.

[보관 dry-run](../../tmp/widget-symbol-profitability-redesign-20261006/final/storage-dry-run.json): 현재6~8월 스냅샷5869개 **133.03MiB**다. 계획의 약146MiB 추정은 현재 실측으로 정정했다. frozen prefix/source hash·rollback/audit·다른 consumer에서 미참조가 입증되지 않아 삭제 적격0이며 실제 삭제0이다. 저장소 owner가 archive SHA와 동결 재현을 입증한 뒤 판단한다.

- `WidgetEpisodeMachineResearchContract1006`: 삼성 정규장 exact leg/guard 결손. 기존 source로 완전 재생 불가 처분을 유지하며 BBO 합성으로 해결하지 않는다.
- `SemanticPolicyCoverageRemediation1006`: source 결손/valid-empty/paired 검열의 운영 감시 projection 및10/1 WS 원천 결손. closure는 자연 collector receipt의 정확한 route/epoch/가격·시각 유효성이다.
- `WidgetEpisodeNextSessionStartup1006`: 현재 준비된 dated 정책의 다음날 자연 PID 소비. tonight PID 확인·재기동 없음.
- 저장소 owner: snapshot dry-run을 인계한다. 참조/보관 증거 없이 삭제하지 않는다.

## 6. 최종 검증

코드리뷰→보완→반례 회귀→재리뷰를 반복했다. 최종361개 관련 pytest, affected Python compile, wrapper `bash -n`, `git diff --check`, 링크/단일 owner 및 print-only backlog parser를 검증한다. 검증 receipt에 실측 결과와 보호 파일 해시를 저장한다. 광범위 전체 거래 suite, API/provider 호출, stage 실행/publisher, PREOPEN 재생성, 배포·기동·외부 sync는 실행 범위가 아니므로 생략했다.
