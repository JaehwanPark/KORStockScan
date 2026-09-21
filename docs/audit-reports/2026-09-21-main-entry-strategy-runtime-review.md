# 메인 전략 임계치 즉시 적용 구현 리뷰 — 2026-09-21

사용자 범위: 계획 구현, 반복 리뷰·수정, 장후 재생성, 커밋·푸시·배포·기동. 후속 지시로 다음 PREOPEN 대기를 제거한다. 이 기록은 실주문이나 자연 수익 증거가 아니다.

## 구현 경계

- 기존 fact producer·calibration·publisher·loader를 확장한다. 신규 Python owner는 `src/engine/scalping/entry_strategy_policy.py` 하나이며 순수 전략 registry/selector 계약을 소유한다. 별도 DB/report family/daemon/cron 및 engine-root 모듈은 추가하지 않는다.
- 82개 전략 좌표를 등록했다. 가격/tick·유동성·변동성·수익률/시간·검증된 as-of 시총에 따라 하나의 정책 내부 profile을 고른다. 시총 미지원은 parent이며 최신 DB 값을 과거로 소급하지 않는다.
- 당시 원시 입력에서 전략 사실·risk/action을 재계산한다. 완료봉 원시는 별도 hash로 보존하고 future/forming/coverage 손상을 거부한다. 원시 재생 증거는 보조 AI compact 입력에서 제외한다.
- 후보 탐색은 유한 joint domain과 train에서 정한 유형 경계를 함께 순회한다. cursor/domain hash, 미완료 여부, 원천 미지원 좌표를 기록한다. 소규모 완전열거와 세 축 동시 변경이 필요한 실제 kernel fixture로 검증한다. 96개 기본 batch를 전역 최적이라고 주장하지 않는다.
- 승격은 동일 기회 비용·운영경로 검증, train 고유기회10/holdout 변경 고유기회3, 날짜 분리, 양수 순익·paired 개선 및 기존 catastrophic guard를 요구한다. 새 정책에 10bp·5종목/5일·실체결 선행 floor를 추가하지 않는다. 후보 AI 입력/owner replay 미지원은 null/source gap이다.
- 적격 후보는 immutable generation·parent CAS·fsync/원자 current 선택을 통해 즉시 적용한다. 날짜별 handoff와 current를 분리하고 current를 다음 적격 정책까지 승계한다. 실패 후보는 current를 유지하고 손상된 active는 진입 차단한다. 초기진입 v2 임계치는 보유 추가매수 owner에 적용하지 않는다.
- 기존 postclose 명령에 `--activate-now`를 연결했다. summary/verifier는 dated handoff와 current 유효성을 따로 표시하며, 로드만으로 PID 소비를 주장하지 않는다.

## 반복 리뷰·검증

- 보호된 source/order/custody 조건과 v1 의미 보존, raw/hash 일치, 유형 UNKNOWN·그래프 순환, 3축 상호작용, 작은 양수 EV의 승격, 날짜 승계·잘못된 후보·손상된 current, provider 원시 중복을 확인했다.
- 수정: rate의 `_sec` 접미사를 시간 하한으로 오인한 registry bounds, raw 결손 한 행이 전체를 막던 경로, source-invalid 경로에 잘못 위치한 rebuilt setup 인계, active 손상 후 legacy AI fallback, 보유 owner에 v2 profile이 전달되는 경로, provider raw 중복을 보완했다.
- 배포 기준 source `90dd032e34efb36fb0ace5d9022fc7bcecb1eaf6` 위 별도 체크아웃에서 관련 11개 suite 955 PASS. 후속 행별 제외/경계 보완의 targeted 검사199 PASS. 추가 검증 및 최종 commit/release 영수증은 아래 실행 결과에 기록한다.
- 작업공간의 다른 수정은 stage하지 않는다. Kiwoom 요청/response/FID/auth/order protocol은 변경하지 않는다. 외부 sync·검증용 주문·후보 AI PASS 합성은 실행하지 않는다.

## 원천 지원 및 열린 완료 조건

- 대량매도 event 이후 회복 tick의 순서를 입증하는 원천은 아직 지원하지 않는다. 과거 boolean을 지워서 진입시키지 않으며 이 축을 전수 튜닝 완료로 보고하지 않는다.
- 시총 known-at·단위·기업행사 provenance가 없는 입력은 UNKNOWN parent다. 완료봉 전체 원시 또는 micro window가 없는 역사 입력의 관련 좌표는 유지하고 미지원 목록을 남긴다.
- BLOCK/RECHECK가 새로운 ENTER_NOW가 되는 후보에는 그 변경된 사실을 소비한 auxiliary/실행/비용 replay가 필요하다. 기존 PASS를 다른 candidate에 재표시하지 않는다. 이 결손이 남으면 정책 선정/경제성 완료가 아니다.
- 전체 계획 P0–P6·모든 시장 유형의 자연 적용·비용 후 실성과를 이 코드 리뷰로 일괄 완료 처리하지 않는다. 기존 `DirectFamilySourceRepairMainMechanisticEntry` OPEN owner를 유지한다.

## 실행 결과

- 초기 배포 commit: `77b6beb51542b1f91621cab6a6543c10d7282eca`, branch `codex/main-entry-strategy-20260921`, origin push 확인. 당시 최신 위젯 릴리스 `d6b26e455`를 부모로 통합해 동시 변경을 보존했다.
- 18:00 KST 정상 재기동: PID `346701`, runtime bootstrap PID 검증 PASS, 해당 릴리스 `src` cwd 일치. 실제 release/PID 영수증은 `data/runtime/runtime_release_selection.json`, 검증 및 이전 selection은 `tmp/main-entry-strategy-20260921/`에 보존한다.
- 최종 관련 계약 360 PASS, 최신 운영 source 통합 후 268 PASS, 후속 verifier 수정 15 PASS. compile/bash syntax/diff/print-only parser 통과. 중복 검사를 합산해 고유 테스트 수로 표시하지 않는다.
- 18:08 KST 장후 재생성 완료: source date `2026-09-17`(현재 보존된 최신 완결 label 자료), publication `2026-09-21`, `--machine-only --write --require-policy-publication --activate-now`. 오늘의 미래 결과를 합성하지 않았다. 첫 재생성에서 발견한 legacy 구조 필터 연결 결함을 수정한 후 한 번 재실행했다.
- 새 전략 KRX 모집단 1,712건, raw 재판정 지원 1,708건, raw 누락 제외 4건. 실행·비용 비교 연결 `operating_population_count=0`, `strategy_operating_population_unbound`, 평가 후보/승격 0. 다른 8 scope는 빈 원천·당일만 존재하는 holdout 결손·raw 결손으로 유지한다. 이는 `evaluated_no_edge`나 임계치 최적 탐색 완료가 아니다.
- **새 임계치 정책은 생성·적용되지 않았다.** 즉시 publisher 결과 `incumbent_carry`; 현재 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7` 유지. 9/22 dated carry bundle은 `876fd067e62a477622b683ae8b6ebb376674452cba89eaa5019e84936069950a`; 새 전략 `current.json` 승격 세대는 없다.
- 메인 scoped verifier는 처음 전체 모집단과 구조 유효 모집단을 같다고 요구하여 실패했다. 원 모집단·유효 모집단·제외 수의 보존식으로 수정하고 불일치 거부 회귀검증 후 PASS. 이 보완은 오프라인 verifier뿐이므로 이미 정상 기동한 메인 PID는 유지하며, 후속 선택 릴리스의 main runtime 파일이 초기 배포와 동일함을 hash로 검증한다.
- 전체 runtime summary는 `direct_evidence_incomplete`; 전체 postclose terminal/자연 제출/실현 순익 완료로 보고하지 않는다. 비용 후 EV·일별 순익은 null이다. 장후 재생성의 `full_evaluation_complete`는 작업 종료 상태이며 전수 경제성 성공이 아니다.
- 남은 구현/원천 owner: `entry_setup_paired_replay_batch/strategy_owner_replay`. 후보별 재계산한 setup을 소비한 실제 offline auxiliary verdict, 그 가용시각에 묶인 실행·비용·자본 replay, RECHECK 종료 증거를 같은 기회로 생산·검증해야 한다. 현재 compact `prepare`는 실제 ENTER_NOW 화면만, nonentry replay는 `nonentry_plan_only`만 생산하므로 후보 전환의 이 연결은 아직 미구현이다. 이 결손은 갱신 임계치를 낮추는 것으로 해소되지 않는다. 그 연결이 없는 상태에서는 탐색이 economic preflight에서 중단되며 모든 설정 조합의 학습 완료가 아니다.
- 사용자가 요구한 전체 완료 조건 중 **새 수익성 정책 생성·즉시 적용은 미완료**다. 기존 OPEN owner를 유지하고, 정책 강제 승격/AI PASS 합성/검증 주문/외부 sync는 하지 않았다.

## 후속 코드리뷰 — 연구 차단·비교·재사용 계약 수리

- 연구용 원시 재판정 앞에 있던 holdout/표본/운영경제성 early-return을 제거했다. 유효 원시 입력 한 기회부터 동일 kernel로 후보를 재판정하고, 실적용 후보와 분리한 `research_candidates`(최대 3개)에 원시 hash·변경 attempt·전환·정책 hash를 보존한다. 연구 후보는 `runtime_effect=false`, `allowed_runtime_apply=false`, `metric_role=funnel_count`; 변경 건수는 수익성 순위나 승격 근거가 아니다.
- 기존 정책 비교는 원시 사실을 복원한 뒤 실제 parent 정책으로 판정한다. seed가 기존 hierarchy를 제거해 대조군까지 바꾸던 결함을 수리했다. 원천 미지원 좌표도 registry 기본값으로 되돌리지 않고 incumbent 값을 유지한다.
- cache identity에 trace ID만이 아니라 원시 입력·결과·운영재생을 포함한 전체 비교행을 결속했다. 같은 holdout에 고정된 후보를 재검증할 때 train/holdout 모두 현재 원천으로 다시 평가한다. holdout 재생 실패는 명시적 unsupported이며 보고서 전체의 조용한 실패나 이전 PASS 재사용이 아니다.
- 보조 AI 재사용은 setup 사실과 provider에 전달한 기계판정이 모두 같아야 한다. setup만 같고 action/threshold/policy 판정이 다른 입력에 기존 AI verdict를 재표시하지 않는다.
- 완료봉 전체 재생은 OHLC 범위·음수 거래량·다른 거래일을 거부한다. 재생 자료를 임의 수치로 보정하지 않는다.
- 회귀검증: 한 기회의 BLOCK→ENTER_NOW 연구(비용/holdout 없으면 미승격), 기존 hierarchy 보존, 같은 trace ID의 raw 변경 시 cache 무효화, 다른 AI 기계판정 재사용 차단, 잘못된 완료봉 거부. 관련 pytest 210 PASS, py_compile/diff 검사 통과. 신규 module/CLI/cron/provider 또는 broker 요청은 없다.
- 범위 한계: 실제 후보별 offline auxiliary 호출 및 그 가용시각에 결속한 실행·비용 owner 재생 producer는 여전히 미구현이다. 이번 수리는 그 결손이 **기계 연구까지 중단시키던 경로**를 제거하며, 완전한 경제성·정책 승격 완료를 뜻하지 않는다.

- 18:39 KST 장후 재생성 완료(source 9/17, publication 9/21): KRX raw 지원 1,708/1,712건, 실제 재판정 후보 6개, 연구 후보 3개 보존. PREMARKET 40개, 통합 aftermarket 24개 재판정. 탐색은 96개 cursor 예산 내 실행이며 전역 탐색 완료가 아니다.
- KRX 저장 연구 후보에는 BLOCK→RECHECK와 RECHECK→BLOCK 등의 전환이 있지만 새 ENTER_NOW 전환·양수 비용 후 순익을 확정하지 못했다. 기존 미지원 실행·비용 연결 0건으로 `unsupported_downstream`; 장전/aftermarket는 분리된 holdout 부족으로 `hold_sample`이다. 모든 scope 승격 false, 현재 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7` 유지.
- runtime summary 재생성 및 메인 scoped verifier PASS. 전체 terminal/자연 비용 후 실성과를 PASS로 확장하지 않는다. 연구에서 발견한 판정 변화는 주문 또는 수익성 증거가 아니다.
- 동시 위젯 배포 `fbe11c5f9`를 보존해 통합한다. 최종 배포·기동 결과는 `tmp/main-entry-review2-20260921/validation.json`, `selection-before.json`, `deployment-result.json`과 `data/runtime/runtime_release_selection.json`의 실제 PID 영수증으로 판정한다.


## 작업본·배포본 통합 정리

- 사용자 작업본/배포본 통합·불필요 파일 제거 요청에 따라 main 기준을 기존 `ea4788788`에서 실제 배포된 후손 `ea21e9dcc`로 맞췄다. 사전 분류한 93개 작업 파일의 바이트는 모두 보존했고, 소스·테스트·배포 스크립트 차이는 0이다. 작업본에만 남았던 리뷰/배포 이력과 계획·체크리스트 문서는 보존하여 함께 버전 관리한다.
- 현재 메인 `ea21e9dcc`/PID `367246`와 직전 롤백 `fbe11c5f9`는 유지한다. 해당 프로세스·selector·정책을 변경하거나 재기동하지 않았다. 기존 실제 비용 재생 결손과 새 정책 미승격 상태도 그대로다.
- `/proc` cwd·명령 인수·열린 파일, systemd와 cron의 참조가 없고 커밋이 현재 배포의 조상인 중복 작업트리 3개를 제거했다: `KORStockScan-nonentry-review`, `main-entry-strategy-20260921-77b6beb51`, `main-entry-strategy-20260921-f40bbf482`. 삭제 전 공유 data/docs/logs/tmp/venv 링크의 대상을 확인했고 실제 공유 디렉터리는 건드리지 않았다. 약 245 MB의 중복 체크아웃·캐시를 정리했다. 원 커밋·배포/검증 영수증은 남아 있어 과거 경로는 당시 체크아웃 이력으로 해석한다.
- `/tmp/nonentry-*` 임시 항목 56개는 고유 원본·실패/검증 증거를 잃지 않도록 약 1.2 MB의 단일 복구 압축본으로 모으고 느슨한 복사본을 제거했다. 기존 작업본 문서/패치/인덱스와 selector도 먼저 보존했다. [통합·삭제 목록 및 복구 자료](../../tmp/workspace-release-consolidation-20260921/cleanup-result.json), [사전 통합 분류](../../tmp/workspace-release-consolidation-20260921/integration.json).
- 이 정리는 코드·정책 변경이 없어 trading pytest·장후 재생성·외부 Project/Calendar sync를 반복하지 않는다. 문서 owner/링크·print-only parser·diff 및 운영 소스/selector/PID 불변 검증 결과는 같은 증거 디렉터리의 `final-validation.json`에 기록한다. 실행 중이거나 다른 작업에 속한 릴리스·거래 원장·당일 생성 자료는 삭제하지 않는다.


## 후속 범위 정정 — 기계 미진입 기회비용 정책

- 최신 사용자 지시로 현재 선정 목적을 BLOCK/RECHECK→ENTER_NOW 기회비용에 한정했다. 기존 ENTER_NOW를 줄인 이익은 제외하고, 보조 AI VETO→PASS·다른 하드 가드·scale-in·청산 튜닝은 후속으로 분리한다. 기계정책 생성·즉시 적용·재기동·장후 연결·승계는 현재 승인 범위다.
- 후보 AI 결과/운영 owner 재생을 기계정책의 필수조건에서 제거했다. 기존 source-valid raw/실행가능 ask/고정 target-adverse 선착순 label/왕복 비용을 재사용한다. 미도달·동시 도달·비용 결손을 이익0으로 채우지 않으며, RECHECK 전체 수명·실제 체결·portfolio 원화 손익을 이 가격경로 실험으로 주장하지 않는다.
- 사용자 기준: **비용 후 평균이익 0 이상인 후보에서 승률 우선**, 같은 승률이면 평균이익·기회비용 회복·유일 기회 수로 비교한다. 비용 후0은 허용하지만 승리로 세지 않는다. 반복 attempt는 같은 기회 내 평균으로 가중치를 제한한다. train에서 선택하고 holdout이 있으면 이후 검증하며 음수 경로 이익을 숨겨 적용하지 않는다.
- 기존 함수/CLI에 `--machine-policy-only --write [--activate-now]`를 추가했다. 기존 장후 `--machine-only --activate-now` 경로도 동일 기계 선정 함수를 사용하므로 별도 scheduler나 producer를 만들지 않는다. publisher·current generation·동일 validator·재시작/다음 날짜 승계는 재사용한다. AI 정책·주문/자금·guard는 그대로다.
- 탐색 보완: 원천 없는 구조/tape 좌표를 보존하고, 다수 좌표를 한꺼번에 흔들기 전 현재 정책 주변의 단일좌표 후보를 우선 평가한다. 전체 joint frontier/cursor는 유지하며 전역 최적이나 전수 탐색 완료를 주장하지 않는다.
- 검증: 관련3개 suite **285 PASS**, compile/diff 및 print-only parser 통과. 비용0 허용·승률 우선·반복기회 가중치·AI 결과 무시·기존 ENTER_NOW 제외·음수 경로/holdout 거부·current 적용 및 다음 날짜 승계를 회귀했다. 가격경로 원천2,330건은 한 번 추출해 이번 비교에서 재사용한다. 최초24 budget 탐색은 새 비음수 후보를 찾지 못했으며, 우선순위를 보완한96 budget 실행이 진행 중이다. 최종 정책·배포/PID 결과는 후속 영수증으로 구분한다.


### 기계 정책 비용 경로 및 탐색 재개 보완

- 96개 후 잔여40개를 이어 평가해 시장별 cursor136까지 진행했다. 해당 비교에서는 새 비음수 후보가 없었다. 같은 입력 재실행은 cursor와 누적 평가 건수를 이어받고, 원시 입력/결과/parent/목적함수가 바뀌면 새 탐색으로 시작한다. 후보별 비용 지표와 임계치 변경을 남겼다.
- 추가 리뷰에서 기존 gross 0.3% 목표가 원천 왕복 비용보다 작아 KRX 학습 경로997건 모두 비용 후 음수인 평가 오류를 확인했다. 기계단계는 이미 저장된 `entry_quality_path_v1`의 비용 포함 목표·정확 손실 경계 선착순을 사용하도록 수정했다. AI 판정·새 청산 전략·미래 고점 체결을 추가하지 않았다. 원 경로·비용 불일치/결손은 제외하며 낮은 gross 목표로 fallback하지 않는다.
- 회귀검증 **287 PASS**: 비용 포함 경로/기존 낮은 gross 목표 구분, 비용 불일치·경로 결손 제외, 비용 후0 허용, 승률 우선, AI 독립, 반복기회 가중치, 정책 활성화와 다음 날짜 승계, 탐색 재개/입력 변경 무효화를 포함한다. 비용 경로 변경으로 이전 점수는 재사용하지 않고 새 목적함수 hash로 정책 생성 중이다. 최종 배포·정책 결과는 별도 영수증으로 확정한다.


### 최종 배포·기계정책 평가 결과

- 코드 `b9be2da6e5e03bb1f5b89d67360ff1230129d436` 커밋·푸시 후 immutable release `main-machine-policy-20260921-b9be2da6e` 배포, 19:50 KST graceful 재기동으로 PID **401859**의 실제 release cwd/launcher 영수증과 runtime env handoff PASS를 확인했다. 직전 `ea21e9dcc` 릴리스·selector 원본을 롤백용으로 보존했다. 미선택 중간 배포본 `11cfe2686`만 참조 없음 확인 후 제거했다.
- 수정한 비용 경로로 원천2,330건을 재사용해 scope별96 cursor/95 유효 후보를 평가했다. KRX에서 `momentum_accelerating_score` 68→54 후보가 선택됐다. 학습 진입 기회2개는 승률100%, 비용 후 평균 +0.10%; 독립 검증 진입 기회5개는 승률60%, 비용 후 평균 **−0.40682%**, 최악 −1.18225%였다. `holdout_machine_selected_path_invalid`로 미적용했다. 다른 두 scope는 비음수 학습 후보가 없었다.
- 공식 publisher의 실제 실행 결과는 `incumbent_carry / no_qualified_strategy_successor`; 기존 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7` 유지다. **새 기계정책 후보 생성은 완료, 새 임계치의 기본 정책 적용은 미완료**이며 원인은 AI/후단 구현 결손이 아니라 이번 후보의 검증구간 비용 후 음수 이익이다. 같은 검증구간을 보고 다른 후보를 다시 고르는 작업은 하지 않았다.
- 추가로 train만 사용한 구조 확인 수치의 조합3개와 중복 유동성/trigger 조건 조합4개를 진단했다. 새 진입0 또는 비용 후 음수였으며 runtime 후보를 별도로 강제하지 않았다. 전체 joint domain은 탐색 미완료로 남긴다. 다음 정상 장후에는 새 원천에 같은 비음수·승률 우선 기준을 적용한다.
- 기존 postclose wrapper가 새 release의 `--machine-only --write --require-policy-publication --activate-now` 경로를 사용함을 print-plan과 consumer 연결로 확인했다. 새 scheduler는 없다. 이미 발행된 9/22 dated bundle은 별도 hash지만 9개 scope의 기계정책은 현재와 동일했다. 기계 전용 current 활성화·재시작/다음 날짜 승계는 회귀검증에 포함됐으며, 이번에 새 임계치의 자연 PID 소비나 실제 수익을 주장하지 않는다.
- workspace/최종 release 모두 관련3개 suite **287 PASS**, compile/diff 통과. 문서·checklist는 print-only parser로 검증하며 외부 sync/검증 주문/provider 호출/다른 하드 가드·scale-in·청산 변경은 실행하지 않았다. 실제 자료: [정책 결과](../../tmp/main-machine-policy-20260921/policy-result.json), [배포/PID 결과](../../tmp/main-machine-policy-20260921/deployment-result.json), [장후 라우팅](../../tmp/main-machine-policy-20260921/postclose-routing.json).


### 최신 사용자 변경 — 손익 하한 없이 최상위 기계정책 적용

- 사용자가 기존 비음수 조건을 철회하고, 음수 후보 중에서도 승률 우선 최상위 정책을 매번 갱신·적용하도록 지시했다. 승률60%·평균이익−0.40682%는 현재 후보의 관측값이며 미래 갱신 문턱이 아니다.
- 기계단계 evaluator/scope selector/publisher·current loader의 공통 validator에서 평균이익·paired delta·최악 평가손익의 절대 하한을 제거했다. 원천·전체 비용·정책/부모/scope hash·유효한 실제 비교 기회·시간순 분리는 유지한다. 이 변경은 기계정책 평가 계약이며 broker/주문/qty/cap/source freshness/protect/emergency 또는 다른 단계 정책을 바꾸지 않는다.
- 비용 후 음수 후보·음수 holdout 활성화/다음 날짜 승계·동률 손실 비교·기존 손실 하한보다 낮은 평가값 허용까지 관련3개 suite **289 PASS**. 이미 고른 현재 후보는 동일 임계치/hash를 유지하여 재검증하고, 같은 holdout을 사용한 재탐색은 하지 않는다.

- 최종 적용: `ada8a07d48feba5186bb7aeb2c7e2175eb579580` 커밋·푸시/배포. 20:11:58 KST current bundle **`1c5c13eda101eb787b6b208c834ad58cb2b44316878da605bd294026c7d5fedb`** 활성화 후 PID **408651** 기동. 이전 프로세스가 이미 종료되어 restart의 no-running 응답 후 표준 router start를 사용했다. 현재 KRX 후보의 `momentum_accelerating_score`는 **68→54**, 후보 정책 hash는 `533d74c319e39adb9a1d6233125e959fd77c450dfb198a12a2a1941bc0d7c81b`로 재탐색 없이 동일하다.
- 실제 PID cwd/env 인계 PASS, 실제 PID 환경으로 실행한 live resolver의9개 scope 모두 새 bundle hash 일치. 새 기계 임계치는 KRX scope만 변경되며8개 다른 scope·모든 AI 정책·기존 runtime hard guards는 동일하다. 9/22에 기존 dated bundle이 있어도 current가 우선되어 동일 정책을 다음 적격 generation까지 승계함을 확인했다. 장후 print-plan도 새 release를 가리킨다.
- 코드/기계정책 생성·현재 기본값 활성화·기동·장후 호출 연결·다음 날짜 승계까지 완료했다. 실제 새 장중 판정/주문/실현 손익을 관측했다고 주장하지 않는다. 비용 후 음수는 알려진 현재 평가값으로 유지하며 새 정책의 절대 갱신 문턱이 아니다. 최종 release 정책 suite101 PASS, workspace 관련3개 suite289 PASS. [활성화·PID 영수증](../../tmp/main-machine-policy-win-first-20260921/deployment-result.json), [실제 PID 환경 live resolver](../../tmp/main-machine-policy-win-first-20260921/pid-live-resolver.json), [다음 날짜 승계](../../tmp/main-machine-policy-win-first-20260921/policy-verification.json). 롤백은 직전 코드와 current 포인터의 쌍으로 수행해야 하며 [롤백 연결](../../tmp/main-machine-policy-win-first-20260921/rollback-binding.json)을 보존했다.
