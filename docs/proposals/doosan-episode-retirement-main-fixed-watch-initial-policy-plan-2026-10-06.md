# 두산에너빌리티 에피소드 완전 제거·Main 상시감시 전환·초기 정책 연구 계획

작성일: 2026-10-06 KST. 대상: `034020` 두산에너빌리티.
상태: 작업본 구현·오프라인 연구·리뷰/회귀 검증 진행. 설치된 서비스 제거·배포·PREOPEN 적용·자연 소비는 미실행이다.
문서 역할: `docs/proposals`의 전환 설계. 운영 원칙은 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 현재 실행 소유권은 [당일 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)가 소유한다.

## 1. 목표와 범위

두산을 에피소드의 실행·연구·발행·자동 확장 모집단에서 완전히 제거한다. 삼성전자와 같은 **Main 고정감시 기반**에 두산을 추가하고, 현재 Main 비삼성 정책을 두산 초기 정책으로 지정한다. 두산 원천의 후속 연구는 향후 교체를 비교하며 정책·원천·적용일·PID에 결속한다. Main 공통 진입·보유·청산·수량·주문 소유권을 사용하며 두산 전용 독립 매매 서비스를 새로 만들지 않는다.

삭제 범위는 **두산 관련 에피소드 기능 전체**다. 다른 종목의 에피소드 프레임워크는 유지한다. 두산의 전용 파일뿐 아니라 공용 파일 안의 두산 profile·시간대·정책 override·분기·목록·테스트도 제거한다. flag OFF, 주석 처리, 실행되지 않는 alias나 compatibility wrapper를 남긴 상태는 최종 삭제로 인정하지 않는다.

두산의 가격·실제 주문·체결·custody·과거 정책 원 증거는 코드와 구분한다. 미래 Main 연구에 필요한 시장 원천은 보존하고, 과거 에피소드 원장은 audit-only로 보존한다. 과거 거래를 Main 거래로 재귀속하지 않는다. 기존 보유나 미체결을 자동으로 Main에 이관하지 않는다.

사용자는 계획 구현·코드리뷰 후 수정보완을 지시했고, 후속 지시로 **초기 정책 적격성 입증은 필요 없다**고 확정했다. 두산 초기 정책은 현재 Main 비삼성 부모 정책으로 지정하며, 별도 positive EV·native 표본·독립 검증을 최초 적용 대기 조건으로 만들지 않는다. exact-date/hash/원천 신선도와 broker·owner·수량·주문·수동 veto 안전 계약은 유지한다. 연구 `source_gap`은 초기 지정을 막지 않는다. 배포·재기동·설치 삭제·실제 owner 발행은 이번 작업본에서 실행하지 않았으며 다음 PREOPEN 전환 준비와 구분한다. 현재 체크리스트의 `DoosanEpisodeToMainFixedWatch` 한 개가 D0~D7 잔여 작업을 소유한다.

## 2. 현재 근거와 해결할 문제

| 확인 항목 | 현재 증거 | 설계에 반영할 사항 |
|---|---|---|
| 에피소드 profile | `doosan_enerbility_morning`, `doosan_enerbility_late_morning`, `doosan_enerbility_afternoon` | 3개만 지워 끝내지 않고 symbol 기반 확장·옛 profile 복구도 차단 |
| 설치 코드 | 두산 전용 timer 파일 6개, 공용 template의 live/preflight instance 각 3개 | 설치·재설치 목록과 instance별 drop-in까지 제거; 공용 template은 유지 |
| Main 고정감시 | [main_fixed_watch.py](../../src/engine/scalping/main_fixed_watch.py)가 `005930`에 고정, 예산에서 고정 slot 1개만 예약 | 두 종목을 처리하는 공용 구현과 정확한 slot 계산으로 일반화 |
| WS 수집 명세 | [10/6 수집 명세](../../data/runtime/scalp_micro_reversion_collection_targets/scalp_micro_reversion_collection_targets_2026-10-06.json)에 두산 owner `episode/widget`, 등록 item `034020`, `034020_AL` | 에피소드 제거 뒤 Main 고정감시가 현재 수집 목적·구독 책임을 승계; 퇴역 widget 귀속도 새 명세에서 제거 |
| 실제 수신과 Main quote | [12:10~12:11 점검](../../tmp/doosan-fixed-watch-source-risk-20261006/assessment.json): exact route의 0B/0D 수신, 두산 관측 전용 공용 quote 필드는 0 | 관측 route와 실제 Main quote 연결을 먼저 검증; 가격 0을 packets 부재로 단정하지 않음 |
| 데이터 신선도 | 16회 읽기 중 두산 호가 나이 최대 2.43초, 기존 WS 어댑터 2초 기준 초과 1회 | 구독 수 여유만으로 수용하지 않고 소비 시점의 age·lock·평가 지연 대사 |
| 이전 결손 | 오늘 이전 실행본에서 09:28~09:29 두산 `ws_snapshot_missing_or_zero` 3건 | 이전 실패와 현 PID를 분리하고 동일 증상을 회귀 사례로 사용 |
| 최근 처리 부하 | 위 점검 당시 Main 감시 1종목, 관측 시간대는 낮 | 두 종목 동시 평가와 장 시작 구간은 별도 자연 검증 필요 |

[계획 조사 증빙](../../tmp/doosan-episode-main-fixed-watch-planning-20261006/context.json)의 source/reference census는 현재 snapshot이다. 실제 전환 직전에 selected release, 설치 unit, 실제 PID, 코드·원천·owner 정책·진행 중 worker를 다시 확인한다. 현재 문서의 숫자나 11:47의 flat receipt를 전환 시점의 승인·잔고 증거로 재사용하지 않는다.

## 3. 구현·전환 순서

| 단계 | 실행 내용 | 완료 산출물과 다음 단계 조건 |
|---|---|---|
| D0 | 현재 owner·설치·원천·소비자 census 및 전환 계약 고정 | 실행일 checklist owner 1개, immutable 코드/원천 manifest, 신규 진입 차단·잔여 관리·Main 개시의 발효 경계 |
| D1 | 두산 에피소드 신규 진입·발행·자동 확장 차단, 잔여 노출 종결 | 전송 직전 신규 BUY 거부, fresh broker/원장 대사, 잔여 수량·미체결·미확정 intent 0 또는 별도 승인 인계 |
| D2 | 두산 전용·내장 에피소드 코드와 설치·장후 의존성 완전 삭제 | 삭제 manifest, live import/dispatch·두산 episode profile·installed instance·복원 경로 0; 다른 에피소드 회귀 통과 |
| D3 | Main 두 종목 고정감시와 기존 WS 재사용·quote 연결 구현 | 종목별 identity·예산·custody·session 검증, 두산 Main source-ready receipt; 초기 정책은 현재 Main 비삼성 정책 지정; 기계/주문 공통 guard 유지 |
| D4 | 두산 초기 정책 원천 census와 유한 후보 비교 연구 | 아래 R0~R4 수행, 비용·원천·학습/검증·부모 hash 결속, 후보 또는 명시적 blocked 결과 |
| D5 | 지정 초기 정책을 기존 Main 발행·loader·PREOPEN에 연결 | 종목별 정책 bundle과 parent CAS·readback·적용일 검증; 연구 표본 부족으로 초기 정책 지정 보류 금지; 실제 원천/안전 결손은 기존 guard 유지 |
| D6 | 검토된 immutable release와 owner 설정을 허용된 시점에 적용 | selected/installed/실제 PID 대사, 정확한 정책 소비, 두산 episode 재기동·신규 진입 0 |
| D7 | 두 종목 자연 동시 감시·장후·다음 기동 및 비용 후 결과 확인 | G0~G6의 별도 상태 확정; 자연 표본 미발생은 `not_observed` |

D2~D4의 코드 작성과 오프라인 준비는 검토용 작업본에서 병행할 수 있다. 운영 삭제는 D1 노출 종결 이후, Main 초기 정책의 실제 소비는 D5·D6 이후다. 연구가 막혀도 퇴역한 에피소드를 되살려 표본을 만들지 않는다. Main 관측 경로에서 필요한 미래 원천을 기다린다.

## 4. 두산 에피소드 코드·운영 표면 삭제

### 4.1 삭제·수정 대상

| 소유 경로 | 제거할 두산 기능 | 남길 공통 기능 |
|---|---|---|
| [profiles.py](../../src/trading/low_price_two_leg/profiles.py) | `DOOSAN_ENERBILITY_*` window, `034020` episode allowlist, 3개 profile와 모든 날짜별 revision·override·지원 window 항목 | 다른 종목 profile, 공용 dataclass·가격/시간 계산 |
| [policy_runtime.py](../../src/trading/low_price_two_leg/policy_runtime.py), [preflight.py](../../src/trading/low_price_two_leg/preflight.py) | 두산 activation·logic ID·기준/승계/호환성 분기와 정책 pin 허용 | 다른 종목의 exact-date·hash·guard 검증 |
| [live wrapper](../../deploy/run_low_price_two_leg_live.sh), [preflight wrapper](../../deploy/run_low_price_two_leg_preflight.sh) | 두산 case·env flag·LIVE 확인 문자열·profile allowlist | 다른 에피소드 호출 및 공용 stop/보호 절차 |
| [installer](../../deploy/install_low_price_two_leg_systemd.sh), [uninstaller](../../deploy/uninstall_low_price_two_leg_systemd.sh), `deploy/systemd` | 두산 timer 6파일, 생성·복사·enable 목록, live/preflight instance 각 3개와 해당 drop-in·alias | 다른 instance와 공용 service template |
| [tuning](../../src/engine/monitoring/low_price_two_leg_tuning.py), [expanded research](../../src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py) | 두산 시작일·종목 catalog·episode 후보·추천·발행·승계 항목 | 다른 종목의 튜닝·검증·cost 계산 |
| [auto expansion](../../src/trading/low_price_two_leg/auto_expansion_service.py), [auto publisher](../../src/engine/automation/low_price_two_leg_auto_expansion_policy.py) | 두산을 미래 새 profile로 다시 선발·생성하는 경로 | 공용 확장 경로에 owner별 퇴역 검증 적용 |
| [episode source research](../../src/engine/monitoring/episode_source_research.py), [prospective research](../../src/engine/monitoring/episode_prospective_research.py), [research facts](../../src/engine/monitoring/research_source_facts.py), [attribution](../../src/engine/monitoring/machine_microstructure_attribution.py) | 두산 episode cohort·지표·추천·필수 보고서/원천 요구 | Main 두산 원천과 다른 episode 연구; 공용 exact cost·sequence 계산 |
| [collection_targets.py](../../src/engine/scalping/micro_reversion/collection_targets.py) | 두산 `active_episode_owner`, 퇴역 widget owner와 episode scope의 수집 사유 | `main_scalping` 고정감시 owner의 exact item·0B/0D coverage |
| [manual_control_exclusion.py](../../src/engine/risk/manual_control_exclusion.py), [owner policy](../../src/trading/config/symbol_owner_policy.py), [standing authority](../../src/trading/config/symbol_owner_standing_authority.py) | `doosan_widget_and_episode_independent_owners` 소유권 marker와 두산 episode 새 진입 권한·재승계 | 명시적 사용자 veto, manual custody, Main 권한과 다른 종목 owner |
| [run_bot.sh](../../src/run_bot.sh), bootstrap/장후/에러탐지/보고서/UI | 두산을 episode로 취급하는 기본 수집·정책·완료·화면·복구 연결 | `034020` Main 시장 원천·분봉·보고서 표시와 삼성 감시 |

두산 코드가 별도 module에만 있다는 가정을 하지 않는다. 현재 문자열 census는 27개 파일이며 [원 목록](../../tmp/doosan-episode-main-fixed-watch-planning-20261006/references.txt)을 시작점으로 import, 동적 dispatch, 설정·DB catalog, 설치된 unit와 실제 profile source를 추가 대사한다. 최종 census는 실행 당시 코드 기준으로 다시 생성한다.

두산 전용 episode module/테스트가 발견되면 파일 자체를 삭제한다. 공용 파일에서는 두산 전용 함수·조건·constant·test parametrization을 실제 삭제한다. 다른 종목을 검증하는 공용 테스트는 유지한다. `034020`을 일반 broker parser나 source mismatch의 예시로 사용하는 fixture는 episode 기능 잔존과 구분하고, 실제로 퇴역 owner를 재생성하는 fixture는 다른 살아 있는 scope로 교체한다. 새 테스트는 `src/tests`에 둔다.

### 4.2 재등록·재활성화 방지

정확한 발효 시각부터 `symbol=034020, owner_type=episode`를 신규 등록 불가로 처리한다. 프로필 이름만 비교하면 자동 확장이 다른 이름으로 두산을 복원할 수 있으므로, source catalog → 연구 추천 → publisher → loader → preflight → 전송 직전 owner 검사 모두 같은 generic 퇴역 계약을 소비해야 한다.

퇴역 영수증의 종목/owner/시각/상태는 데이터 계약으로 보존할 수 있지만, 두산의 옛 실행 로직·policy alias·profile builder·wrapper는 active code에 남기지 않는다. 새 계약에서 다른 에피소드는 정상 소비한다. 현재 dated policy의 전체 profile을 빈 값으로 덮거나 episode 자동 확장 전체를 OFF로 바꾸지 않는다.

기존 frozen policy·archive·과거 recommendation·설치 backup을 넣어도 두산 episode가 돌아오지 않는 negative 검증을 수행한다. 실제 코드 롤백 때도 외부 퇴역 영수증과 설치 차단을 유지한다. 이를 강제할 수 없는 옛 릴리스는 rollback 후보에서 제외한다.

### 4.3 잔여 보유와 데이터

신규 BUY 차단을 먼저 적용하되 잔여 SELL/reconcile/cancel 관리 책임은 원 owner에 둔다. 조사 중 새로운 fill이 발생하면 flat receipt를 다시 만든다. 일반 broker 잔고만으로 owner별 terminal을 대신하지 않는다. 미확정 custody가 있으면 삭제 gate를 막고 해당 주문/상태 artifact와 closure test를 기록한다. 이름이나 owner tag만 Main으로 바꾸어 인계하지 않는다.

terminal 이후 두산 episode 상태·권한·dated/current policy·전용 raw/report/cache를 소비 census와 archive integrity 뒤 active 경로에서 제거한다. 공용 가격/호가/분봉과 mixed owner 원장은 보존한다. 기존 immutable release를 직접 편집하지 않는다. 실행 중 PID나 rollback이 참조하는 release의 제거는 별도 보존 검증 이후다.

## 5. 삼성전자와 같은 Main 상시감시 구현

### 5.1 하나의 공용 경로

[main_fixed_watch.py](../../src/engine/scalping/main_fixed_watch.py)를 종목별 specification으로 일반화하고 `005930`, `034020`을 검증된 두 항목으로 등록한다. 각 항목은 symbol, 활성 상태, 적용일, 지원 session/route, 초기 policy binding과 observation/live eligibility를 명시한다. 임의 환경 변수 문자열 목록으로 종목과 실주문 권한이 자동 확장되는 설계는 사용하지 않는다.

[kiwoom_sniper_v2.py](../../src/engine/kiwoom_sniper_v2.py)의 고정감시 admission·DB 복원·FIFO 제외·예산 예약·session 이동·WS 등록·관측 준비·EXIT 후 재무장 분기를 함께 일반화한다. 별도 두산 전용 scanner, bot, 주문 loop, systemd service는 만들지 않는다.

목표 계약은 다음과 같다.

- 실제 Main target의 `MAIN_FIXED_WATCH` origin은 유지하며 generation/admission 키에는 정확한 symbol·거래일·session·route·원 DB identity가 포함된다. 삼성과 두산의 admission, cooldown, 상태, 정책 hash를 공유하거나 덮어쓰지 않는다. 별도 관측 identity는 실제 native admission과 구분하고, 연구 편의를 위해 실매매 admission receipt를 합성하지 않는다.
- 삼성 정책과 기존 승인 override·guard를 보존한다. 두산의 관측 수·native 기회와 실제 진입·주문·체결·terminal은 종목별로 구분한다.
- 동일 종목의 일반 scanner watch·HOLDING·미체결·수동 custody·다른 owner가 있으면 duplicate target을 만들지 않는다. 재시작·날짜 변경·종료 후 재진입에서도 같은 custody/quantity/cooldown 계약을 사용한다.
- 고정 slot 예약을 `int(enabled())`에서 검증된 활성 고정감시 수로 바꾸고 일반 watch 여유를 정확히 계산한다. 정원 총량과 broker 수량/cap을 자동 상향하지 않는다. 실제 선택된 target 수·평가 지연·REST 대기를 함께 검증한다.
- 두산 초기 정책은 Main 비삼성 부모로 지정하며 별도의 연구 적격성 gate를 두지 않는다. 실제 exact-date Main policy 부재·무효는 공통 order gate가 처리한다. 실주문 가능한 일반 WATCHING row에 관측용 이름만 붙이는 구현은 금지한다. 정책 부재·wrong-date·잘못된 hash가 Main 기본 정책으로 조용히 fallback하지 않도록 한다.

### 5.2 WS와 원천 연결

기존 Main WS 연결과 정확한 item/type을 재사용한다. 삼성의 session 규칙을 공용 route resolver로 일반화하되, 두산의 현재 KRX/NXT 거래 적격성을 확인한다. 각 session에서 정확한 `_AL`, `_NX` 또는 KRX item을 사용하고 별도 route의 receipt를 서로 대신하지 않는다. 지원하지 않는 session에서는 명시적으로 관측 대기한다.

두산 episode 관측 route를 제거할 때 필요한 Main 구독을 함께 REMOVE하지 않는다. 두산 Main 준비·owner 승계와 신규 episode 차단을 한 전환 계약으로 묶고, 같은 item의 마지막 consumer가 사라질 때만 구독을 해제한다. 중복 REG/강제 repair로 quote 결손을 숨기지 않는다.

0B/0D exact-route receipt → Main quote·trade history → 기계 setup → Main 판단 → submit source 재검증까지 end-to-end 대사한다. 새 admission 이후 원천·warmup, producer PID/start ticks·transport epoch·route sequence, completed bar gap·clock, writer loss와 quote age를 보존한다. stale/conflict/missing일 때는 기존 guard로 대기/차단하며 유동성이 높다는 이유로 freshness 한도를 늘리지 않는다.

공유 스냅샷의 age·publication age·capture lock와 결정 시점 age를 따로 측정한다. 0B 체결 공백과 실제 전송·처리 지연을 구분한다. 현재 구독 예산 56 또는 30초 표본의 정상 수신을 장 시작 부하 수용 증거로 대신하지 않는다. REST 보완이 늘면 현재 shared read budget·order reserve·deadline 안에서 검증하고 새 호출량/재시도 정책을 만들지 않는다.

WS REG/REMOVE·FID·응답 파싱·재연결 또는 Kiwoom 요청을 수정하게 되면 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)에 따라 당시 공식 upstream revision·관련 `kiwoom_docs`/spec/core/realtime/Postman·조회 시각을 검토 evidence에 기록한다. 미정 semantics는 추정하지 않고 fail closed한다.

## 6. 초기 정책 연구: R0~R4

연구 목적은 **지정한 Main 비삼성 초기 정책과 향후 두산 개선 후보를 비교하는 것**이다. 초기 지정을 위한 성과 입증 절차가 아니다. 삼성전자의 수치·조건·양의 성과를 두산에 복사하지 않는다. 두산 episode 정책도 Main 주문·수량·holding/exit 계약으로 재검증하지 않은 상태에서 사용하지 않는다.

### R0 — 원천·기회·기준 정책 확정

1. 현재 승인된 Main 비삼성 기계 진입 policy를 비교 기준으로 freeze하고 원 cost/stop/holding/exit/sizing/submit guard를 결속한다. 삼성은 고정감시 **구현·처리량의 대조군**이며 두산 경제성의 대체 표본이 아니다.
2. 데이터의 clean baseline은 2026-06-05 이후이며, 이 정책 연구의 successor 선정·학습 입력은 Plan Rebase의 더 엄격한 2026-09-29 이후 적격 source만 사용한다. 이전 episode 거래·20/60일 일봉 스크리닝은 archive/진단으로 분리하고 실매매 승인에 사용하지 않는다.
3. retained 체결·호가·completed bar·Main 관측/결정 trace·원래 owner plan·실제 submit/fill/cancel/terminal·cost를 날짜·symbol·venue/session·native ID·policy version별로 census한다. append 중인 파일은 byte bound와 prefix hash를 고정한다.
4. 모집단을 `MAIN_FIXED_WATCH`의 실제 native admission, 일반 scanner 원래 기회, 과거 episode 실제 거래, 원시 가격 기회로 분리한다. 보존된 raw를 새 고정감시 admission이나 실제 주문으로 합성하지 않는다. 같은 admission의 repeated WAIT/RECHECK·child leg·retry를 독립 기회로 중복 계산하지 않는다.
5. 원천 미지원·누락·검열·valid-empty를 구분하고 식별 가능한 결손 row/window만 제외한다. full native plan·cost·owner replay가 결손이면 후보 성과를 확정하지 않는다. [진행 중 conditional owner replay 수리 계획](entry-probe-conditional-owner-replay-remediation-plan-2026-10-06.md)의 결손과도 대사한다.

R0 산출물: `source_census`, frozen parent/cost/kernel/universe manifest, eligible/excluded/unresolved 합계, 복원 가능한 구간과 미래 Main 원천 대기 범위. 원천 결손을 zero EV/no-edge로 바꾸지 않는다.

### R1 — 유한 후보와 연구 계약 동결

Main 기존 feature와 action group을 사용한다. 신규 collector·provider/model·독립 service·매매 alpha pipeline을 만들지 않는다. 초기 family는 기준 정책을 포함해 **최대 4개**로 제한한다.

| 후보 family | 질문 | 고정할 비교 조건 |
|---|---|---|
| 기준 Main 정책 | 두산 고정감시 기회에 기존 비삼성 정책을 적용한 결과는 무엇인가 | 기존 guard·cost·owner·수량/자본·holding/exit |
| 연속 흐름 확인 | 지속 체결 흐름과 현재 가격 반응을 함께 확인하면 진입 구분이 개선되는가 | past-only WS 특징, causal 시계, 동일 원 기회 |
| 눌림 뒤 재개 | 확인된 눌림·회복 상태의 ENTER/RECHECK 구분이 개선되는가 | 미래 저점·고점 사용 금지, 같은 실행 가격/지연 모델 |
| 횡보·과열 회피 | 성과를 해치는 식별 가능한 구간을 제외할 수 있는가 | winner 보존/coverage는 진단; 새 임의 promotion veto로 사용하지 않음 |

기준 정책 1개와 나머지 family당 parameter set 최대 3개, 전체 **최대 10개 정책**으로 freeze한다. 이 숫자는 연구 계산 범위이며 기존 acceptance sample floor를 대체하지 않는다. 후보 정의·parameter·평가 시계·원천·cost·kernel hash·학습/검증 경계·native support 계약을 **결과를 보기 전에** 봉인한다. 모두 부적격이면 연속 threshold 확대를 멈추고 원천·기준 정책·후보별 사유를 보고한다.

초기 정책은 기존 Main 비삼성 진입 bundle을 그대로 지정하고 Main의 holding/exit·stop·수량·cost·주문 guard를 소비한다. 연구 비교에는 해당 부모 hash와 실제 source/cost 계약을 기록한다. 연구에서 변경할 축은 진입 조건과 ENTER/BLOCK/RECHECK의 기계 구분에 한정한다. 신규 exit/trailing, AVG_DOWN, 수량/slot/cap, 모델·provider, hard safety를 함께 튜닝하지 않는다. 매도/수량 개선이 필요해 보여도 별도 owner 작업으로 기록한다.

### R2 — 동일 원 기회·비용·자본으로 재생

동일한 frozen 두산 기회에 기준과 후보를 비교한다. 가격·quantity·stop owner·portfolio opportunity denominator·주문 지연·spread·수수료/거래세·slippage·holding/cancel/terminal을 같은 조건으로 결속한다. 조건부 split/probe 계획은 원래 계약을 지원하는 owner replay로만 계산하며 미지원 동적 잔여 계획을 정적 fill로 대체하지 않는다.

actual 실현 성과, 모델링된 paired CF, 단순 가격 도달을 별도 결과로 낸다. 실제 PnL은 `COMPLETED + valid profit_rate`만 사용한다. 비용·outcome 미확정은 null/unresolved로 유지한다. 분봉 안의 stop/target 선후를 알 수 없으면 success로 세지 않는다. full/partial fill, no-submit, blocked, rejected, canceled, censored와 원천 불일치를 분모와 함께 기록한다.

Main 진입 선택은 현재 승인된 scope의 cost-bound binary target-first 승률 및 지원 조정 계약을 따른다. 현재 `KRX|KRX_REGULAR`의 승인된 선택 계약을 다른 venue/session으로 확장 적용하지 않으며, 다른 session은 검증된 부모 정책과 해당 원천·적용 계약을 따로 대사한다. 실현 net profit·paired EV·tail·coverage·기회 비용은 별도 보고한다. 높은 승률만으로 실제 수익 향상이나 다른 family의 승격을 주장하지 않는다. 두산의 `MAIN_FIXED_WATCH` scope를 기존 validator가 처리하지 못하면 해당 등록·검증 계약을 먼저 구현·리뷰하고 승격은 대기한다.

### R3 — 시간순 검증과 부족 표본 처리

학습과 검증은 원 admission/date/기회 cluster가 겹치지 않게 시간순 분리한다. 같은 날에서 분리가 허용되는 기존 Main 계약을 사용할 경우 distinct opportunity를 엄격히 분리하고 clustered support를 공개한다. 이미 후보 선정에 사용한 날짜를 새로운 독립 holdout으로 표시하지 않는다. 아직 미소비한 후속 날짜는 후보 freeze 뒤 평가한다.

offline raw 가격 기회와 신규 Main 고정감시 native 지원은 별도다. 기존 에피소드 주문을 고정감시 성과로 바꾸지 않는다. 표본이 없으면 `insufficient_sample`/`source_gap`과 필요한 producer·artifact·closure test를 기록하고 초기 지정은 유지하고 후속 개선 비교를 위한 미래 Main 자연 원천을 기다린다. fixed day-count를 새 임의 gate로 만들지 않으며, 실제 support/원천/비용/독립 검증 조건은 기존 acceptance owner에 결속한다.

### R4 — 초기 정책 산출·장후 반복·적용 연결

연구 결과는 `candidate_ready`, `insufficient_sample`, `source_gap`, `measured_no_improvement` 중 증거와 맞게 기록한다. 초기 지정은 `initial_policy_designation=current_main_non_samsung`, `initial_policy_preproof_required=false`, `entry_runtime_eligible=true`로 분리한다. 이 true는 사용자 지정이며 수익성 입증이나 현재 PID 적용을 뜻하지 않는다. 보고서는 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`다. 연구 후보는 기존 Main 비교/발행 계약을 통해 향후 교체 대상으로 검토하며 보고서 자체는 정책 발행을 하지 않는다.

초기 artifact에는 다음을 반드시 포함한다.

`symbol`, `owner_type`, `watch_origin`, `source_date`, `publication_date`, `target_date`, `venue`, `session`, `parent_policy_sha256`, `candidate_policy_sha256`, `source_manifest_sha256`, `cost_model_sha256`, `kernel_sha256`, `training_scope`, `validation_scope`, `native_support`, `selection_status`, `entry_runtime_eligible`, `rollback_parent_sha256`.

새 CLI/보고서가 필요하면 제안 위치는 `src/engine/monitoring/main_fixed_watch_policy_research.py`다. 책임은 Main 고정감시의 offline 보고서 생산이며 runtime 주문 소유권은 없다. 결과 디렉터리는 `data/report/main_fixed_watch_policy_research/`로 제안한다. 테스트는 `src/tests/test_main_fixed_watch_policy_research.py`가 제안 위치다. 실행 구현 때 위치 gate와 nearby caller/consumer를 재확인하고 `src/engine` root에 새 module을 만들지 않는다.

[삼성 고정감시 연구](../../src/engine/scalping/samsung_fixed_watch_evaluation_research.py)는 audit 방법·identity/시계 검증을 참고할 수 있으나 `005930`, frozen 후보·비용·원천 경로에 묶여 있다. 종목 코드만 바꿔 실행하지 않는다. 재사용할 순수 계산은 역할 package에 하나의 구현으로 두고 삼성 fixture와 두산 fixture를 각각 회귀 검증한다. 삼성 연구를 새 이름의 wrapper로 복제하지 않는다.

정책 선택·publisher/loader는 기존 [Main runtime policy](../../src/engine/scalping/mechanistic_entry_runtime_policy.py)와 Main 장후 stage에 연결한다. 두산 정책 scope를 구분하며 삼성 선택값과 원 hash를 보존한다. 독립 두산 cron/stage나 episode publisher로 Main 정책을 발행하는 경로를 추가하지 않는다. 미래 eligible source의 장후 재평가는 원 후보와 native 소비 결과를 기존 Main cumulative/rolling/version receipt로 누적한다.

## 7. 연구·운영 지표 계약

| 지표 | role / 권한 | window와 support / 금지 용도 |
|---|---|---|
| 기계 정책 선택 | `main_entry_win_rate_selection`; 검증된 두산 Main scope의 후보 비교 | frozen 적격 source·native opportunity/cluster, 기존 지원 조정 validator; 다른 owner 승격·주문/수량/provider 변경 금지 |
| net profit·paired EV | `primary_ev`; 실현/CF를 구분한 경제성 평가 | exact cost·terminal·동일 자본/기회 분모; missing cost/outcome을 0/gross로 대체 금지 |
| WS/source 준비 | `source_quality_gate`; 원천 준비/대기 판정 | 종목/route/type/producer generation별 결정 시점 age·sequence·coverage; 거래량으로 결손 면제 금지 |
| loop·read budget·평가율 | `funnel_count`; 처리량과 고정 slot 진단 | 같은 session의 두 종목과 일반 watcher, p50/p95/max·REST defer·stale/recheck; broker/quantity/cap 상향 권한 없음 |

source-ready, 상시감시 target 생성, machine decision, provider 호출, submit, fill, terminal, 정책 PID 소비, 비용 후 성과를 서로 다른 receipt로 보고한다. 연구 report의 `runtime_effect=false`와 실제 policy 적용 receipt를 혼용하지 않는다.

## 8. 문서·배포·장후·복구

후속 구현에서 owning 문서부터 README·runbook·Plan Rebase §5/§7/§8·prompt·AGENTS·traceability·설치/제거 문서·현재 checklist를 목표 계약에 맞춰 갱신한다. 두산 에피소드 전용 OPEN은 실제 retirement와 잔여 책임 종료 후 종결하며, 다른 episode와 공통 source 수리 stable ID·Acceptance는 유지한다. 삭제된 기능의 완료 상태를 Main 정책 연구 완료로 재사용하지 않는다.

장후의 episode catalog·policy apply·research/collection population·summary/tower/checklist/strict/controller·artifact detector가 같은 발효 경계를 사용하도록 한다. 두산 episode 보고서 부재가 필수 source-gap/복구 loop를 만들면 실패다. Main 두산 source/policy 결손은 계속 정확하게 경고한다. 변경된 code/source/schema는 새 세대로 검증하고 summary/checklist freeze → strict → controller → 다음 PREOPEN 준비를 닫는다. 과거 controller/PASS를 새 계약의 승인으로 사용하지 않는다.

배포는 reviewed immutable release와 설치된 service/router, exact-date policy/PREOPEN, 실제 Main PID 및 살아 있는 에피소드 pin을 대사한다. 다음 PREOPEN 전환을 기본 경로로 준비한다. 당일 적용 지시가 따로 있는 경우 기존 [intraday release handoff](../runtime-release-routing.md#authorized-intraday-policy-preserving-code-handoff)를 사용하며 이미 소비된 bootstrap/env/prepared receipt를 덮어쓰지 않는다. 단순 selector 교체를 PID 소비로 주장하지 않는다.

복구 시에는 마지막 검증 Main 코드와 지정한 Main 부모 정책 또는 원천/안전 결손 대기 상태으로 되돌린다. 두산 episode 신규 BUY 차단·재등록 금지·timer/installer 제거는 유지한다. 복구가 다른 에피소드의 owner·quantity·정책과 수동 veto를 바꾸지 않아야 한다.

## 9. 검증과 종료 조건

| Gate | 통과 기준 |
|---|---|
| G0 owner 종료 | fresh 두산 episode broker/원장/custody terminal, 잔여 책임 공백 0; Main admission은 같은 종목 미확정 intent를 계속 차단 |
| G1 코드 완전 삭제 | active 두산 episode profile·전용 실행/분기/override/wrapper/test·installed instance·timer/drop-in·installer 복원 0; generic 퇴역 영수증과 audit-only 원장은 별도 보존 |
| G2 재등록 차단 | static/auto expansion·prospective 연구·policy carry·옛 archive·옛 설치/롤백으로 `034020/episode` 신규 실행 0; 다른 episode 회귀 통과 |
| G3 Main 상시감시 | 삼성/두산 각각 실매매 target 최대 1개, owner·custody·source-ready 상태에서 1개 생성; 관측 identity와 실제 native admission 구분, 날짜/session/restart/EXIT/cooldown 정상, duplicate owner 0, slot 계산·기존 삼성 행동 회귀 통과 |
| G4 원천 소비 | exact route 0B/0D → Main quote/기계/최종 source gate 대사 통과, 종목별 stale·lock·writer/sequence·평가 지연의 원천과 결과 일치 |
| G5 초기 지정·후속 연구 | 지정 부모 hash와 초기 preproof 불필요 기준, frozen 원천/후보/비용·시간순 비교·support·R0~R4 결과; source_gap도 연구 폐쇄 상태이며 초기 지정 veto 아님 |
| G6 실제 적용·자연 결과 | 지정 두산 초기 정책의 exact-date loader·PREOPEN·현재 PID 소비, 두 종목 동시 감시/장 시작·장후 자연 receipt, 신규 episode 이벤트 0; 실제 비용 후 결과 별도 |

필수 회귀 사례:

- 삭제된 두산 profile·unknown renamed profile·`034020` 자동 확장 입력이 startup/publisher/전송 직전 모두 거부된다. 다른 종목은 기존 정책과 수량으로 동작한다.
- 둘 중 한 종목을 비활성화하거나 custody가 생겨도 다른 고정감시 identity/정책/구독이 바뀌지 않는다. 삼성 단독 모드는 기존 결과와 같다.
- 두산 source-only receipt가 존재하더라도 Main quote 연결·post-admission evidence가 없으면 ready로 표시하지 않는다. packets 수신과 실제 Main 소비를 구분한다.
- session route 전환, disconnect/reconnect, 늦게 도착한 callback, transport epoch 변경, snapshot stale, no-tick/VI/거래정지, 날짜 rollover에서 원천 혼합과 false ready가 없다.
- episode 구독 정리 중 Main의 같은 item 구독이 유지된다. 폐기 item의 필요 consumer가 없는 경우에만 REMOVE된다.
- 잘못된 종목/date/source/cost/parent/hash 또는 duplicate train/holdout admission은 연구·발행·loader에서 실패한다. stale 정책·episode 정책·삼성 후보가 두산 fallback으로 적용되지 않는다.
- 관측 정책 또는 연구 결손일 때 Main의 두산 실제 주문은 차단된다. operator veto와 broker/account/order/quantity/cooldown·hard safety가 그대로 유지된다.
- 새 장후 계약에서 두산 episode data가 없어도 다른 episode·Main 전체 검증이 통과하고 두산 Main 결손은 별도로 실패한다.

각 수정은 구현 → self review → 보완 → 재리뷰 → targeted pytest/compile/bash/계약 검증 → 결과 보고로 닫는다. 설치 변경은 staged diff와 `bash -n`, 영향받은 계약 테스트, `git diff --check`를 요구한다. 문서 변경은 링크·owner·권한 검사와 print-only backlog parser를 사용한다. 리뷰·관련 회귀가 닫히기 전 broad wrapper·보고서 재생성·서비스 제어를 실행하지 않는다.

G0~G4는 삭제·상시감시 기술 전환의 완료 기준이다. G5는 연구 결과의 폐쇄, G6는 실매매 정책 적용·자연 검증의 완료 기준이다. 연구가 `source_gap`으로 닫혔다는 이유로 G6를 완료 처리하지 않는다. 전체 이행 완료는 모든 gate가 실제 증거로 닫힌 때이며, 각 `blocked`/`not_observed`/`natural_acceptance_pending`의 artifact·책임 owner·다음 조치·closure test를 명시한다.

## 10. 계획 작성 검토·검증

검토 범위는 현행 코드·설치 목록·원천 조사 결과에 대한 계획의 producer/consumer·권한·삭제 완결성이다. 이번 계획에서는 broker flat, 두 종목 실부하, 두산 초기 정책 성과, 코드 삭제·배포·PID 전환을 검증하지 않았다.

문서 자체의 self review → 보완 → 재리뷰를 완료했다. 보완 사항은 관측 identity와 실제 native admission 구분, custody 조건에 따른 target 수, 기준 1개+후보 최대 9개의 계산 범위, 초기 holding/exit·수량·guard 결속, KRX 선택 계약의 다른 session 확대 금지다. 계획 범위의 미해결 지적은 0이다.

로컬 링크 34개와 anchor 존재 검사 PASS, proposal 공백 검사와 workspace `git diff --check` PASS, print-only backlog parser exit 0·기존 OPEN 23개를 확인했다. 이 proposal의 실행 checkbox와 새 checklist stable owner는 각각 0개이며, 실제 실행 지시 때 당시 checklist에 등록한다. 조사 시작 이후 checklist의 외부 변경은 관측됐으나 이 작업에서는 proposal 이외 문서를 수정하지 않았다.

조사·검증 증빙은 `tmp/doosan-episode-main-fixed-watch-planning-20261006/`에 둔다. 문서 작업이므로 pytest/compile/`bash -n`, broker/provider 요청, 보고서 재생성, 서비스·정책·배포 검증은 실행하지 않았다. 실제 제거·연구·운영 성공과 계획 검증 PASS를 분리한다.

## 11. 구현 기록과 다음 전환

[구현·검토 결과](../audits/doosan-main-fixed-watch-implementation-review-2026-10-06.md)를 따른다. 코드 완료, 설치 삭제, 정책/PREOPEN 발행, PID 소비와 자연 경제성은 별도 상태다. 연구의 원천 ID 결손은 초기 정책 지정의 탈락 조건으로 사용하지 않는다.

## 승인된 당일 전환 보완

반복 코드리뷰·보완 후 배포 및 재기동을 사용자가 승인했다. 퇴역은 두산 episode와 식별되지 않는 주문 프로세스의 quiescence를 요구하며, 확인된 Main/다른 종목 에피소드는 각자의 권한을 유지한다. 모든 날짜의 두산 intent·전체 venue broker/원장 flat·두산 exit service inactive를 전환 시점에 다시 확인한다. 두산 timer 6개의 미래 trigger를 먼저 막고, 검토된 immutable release에서 native installed retirement를 완료한다. 당일 Main owner 권한이 이미 있으므로 현재 owner policy/PREOPEN/bootstrap을 변조하지 않고 intraday code handoff를 실행한다. 다음 정상 PREOPEN producer부터 Main·수동 owner만 발행한다. 미래 장후/PREOPEN과 비용 후 성과는 실제 산출 후 별도 수용한다.
