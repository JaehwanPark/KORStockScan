# Main 전용 운영 전환: 위젯·에피소드 매매기계 완전 제거 계획

작성일: 2026-10-07 KST

상태: **계획 재리뷰·보완 완료. 구현·주문·서비스 제어·배포·데이터 삭제 미실행.**

사용자 후속 확인: **위젯은 삭제 완료. 서버에 남은 설치본까지 삭제하도록 계획을 보완한다.** 위젯 삭제를 다시 확인받거나 Windows 제거 영수증을 새 선행 조건으로 요구하지 않는다. 아래 과거 영수증의 `operator_removal_pending`은 이번 사용자 확인 이전 상태다.

## 1. 목표와 적용 범위

사용자 요청은 “위젯과 에피소드 매매기계 관련 사항을 모두 제거하고 메인봇 매매만 유지”하는 것이다. 최종 상태는 **Main만 자동매매를 수행하고, 위젯·독립 에피소드의 실행 코드·설치 경로·예약 작업·장후 튜닝·정책 적용·전용 수집·화면·알림·불필요한 파일이 남지 않는 상태**다. 단순 OFF 설정과 매일 생성하는 퇴역 보고서로 종료하지 않는다.

- [기존 위젯 퇴역 계획](widget-full-runtime-postclose-retirement-plan-2026-10-06.md)의 “에피소드 유지” 범위는 이번 목표에서 종료한다. [두산 퇴역](doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), [8종목 퇴역·Main 이관](jeju-episode-retirement-hpsp-alteogen-main-fixed-watch-initial-policy-plan-2026-10-06.md)의 과거 실행 증거는 재작성하지 않는다.
- Main의 기계·보조 AI, 연속 반전·다중 정책, 승인된 고정감시, 초기 매수수량, 보유·청산·AVG_DOWN, 주문·수량·계좌 안전장치는 유지한다. 에피소드 종목을 Main 고정감시에 자동 추가하거나 자본·슬롯을 늘리지 않는다.
- 수동 보유·운영자 잠금·명시적 매매 금지는 보존한다. 여기서 Main 전용은 **자동 주문을 생성하는 운영 주체**의 범위다. 브로커 계좌에 존재하는 수동 자산을 Main 소유로 바꾸는 지시가 아니다.
- `episode`라는 필드·파일 이름만으로 삭제하지 않는다. Main의 `position_episode_id`, AVG_DOWN 묶음, 반전 표본 구간, Main 삼성 연구의 episode는 독립 매매기계와 구분한다.
- 계획 작성은 현재 가동 중인 소유자의 청산 책임을 해제하지 않는다. 최종 제거는 아래 수량·주문 대사와 코드 이관을 마친 뒤 수행한다.

기준 문서: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [오늘 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md), [Main 다중 정책 계획](main-multi-policy-parallel-entry-and-samsung-shallow-pullback-implementation-plan-2026-10-07.md). 현재 Main의 누적 raw 승률 선택·운영 AI quota None 승인과 hard safety를 유지하며 이 정리로 EV·최소 일수·표본·holdout 등의 새 채택 문턱을 추가하지 않는다.

이 계획의 “Main 정책 보존”은 전환 직전 승인된 기계·보조 AI·초기수량·보유/청산 정책 payload와 그 부모, 수동 금지의 보존이다. Main 소유권 계약 이관으로 새로 생기는 custody schema/hash와 release·summary·PREOPEN hash는 정확히 다시 결속한다. 삭제할 에피소드 정책 hash까지 보존 대상에 넣거나 새 custody 영수증의 hash 차이를 전략 변경으로 오인하지 않는다.

## 2. 확인한 현재 상태와 조사 한계

[읽기 전용 조사 목록](../../tmp/main-only-widget-episode-retirement-plan-20261007/inventory.json)은 **2026-10-07 12:04:52 KST** 기준 파일 경로·해시, 설치 unit, loaded unit, 선택 릴리스·PID 영수증, 로컬 상태를 담는다. 경로 검색 결과는 삭제 명세가 아니며, 실제 import·호출·파일 소비·소유권을 별도로 대조한다.

| 항목 | 현재 확인 | 제거 계획에 주는 의미 |
|---|---|---|
| 관련 소스·설정·배포·테스트 후보 | 287파일 | 전용 삭제 / Main 공통 이관 / 보존을 파일별 확정해야 함 |
| 관련 설치 unit 파일 | 151개: enabled 65, masked 71, disabled 6, static 9 | 서비스의 disabled만으로 예약 중단을 판단할 수 없음 |
| enabled 구성 | low-price profile timer 62개, auto-expansion 1개, 21:15 refresh 1개, owner 자동적용 1개 | 31개 profile뿐 아니라 자동 확장·정책 적용 경로도 제거 |
| 실행 중인 관련 unit | 한화오션 late-morning 서비스와 그 timer | 실행 worker는 서비스 1개이며 timer를 매매 worker로 중복 집계하지 않음 |
| 로컬 상태 61파일 | 한화오션 `TARGET_OPEN`, `position_qty=10` 발견 | **계좌 미대사 후보**. 이미 flat이라고 판단하거나 청산 서비스를 먼저 삭제할 수 없음 |
| 위젯 퇴역 영수증/사용자 확인 | 과거 영수증은 서버 terminal, 잔량·active intent 0, Windows pending; **이후 사용자가 위젯 삭제 완료 확인** | Windows 재확인 대기는 종료. 서버 설치 잔존물과 Main 자연 실행 확인을 진행 |
| Main 선택 릴리스 | `integrated-workspace-20261007-v1`, commit `940101c8`, 기록 PID `823272` | 작업트리와 별개. 실행 때 실제 PID/cwd/UID 및 최신 selector 재확인 |
| 에피소드 service/preflight pin | `episode-eight-retired-main-five-20261006-511664f3` 계열 | Main 릴리스 교체만으로 구 에피소드가 사라지지 않음 |
| 21:15 refresh pin | `continuous-reversal-20261007-v8` | 구 릴리스의 독립 장후 writer·drop-in도 정리 필요 |

최근 native 튜닝 보고서의 잔존 집합은 31 profile, 10종목(`006800`, `010140`, `011170`, `015760`, `028050`, `028670`, `042660`, `108320`, `137310`, `475150`)이다. 이미 퇴역한 profile과 재명명·자동 확장 profile까지 전체 owner 계열을 대상으로 하며 이 31개만 하드코딩하지 않는다.

추가 발견: ubuntu crontab에 **08:59 IPO 자동실행**이 있고, [래퍼](../../deploy/run_ipo_listing_day_autorun.sh)는 dry-select 이후 [독립 runner](../../src/engine/ipo_listing_day_runner.py)의 실제 `send_buy_order` 경로를 호출한다. 오늘 실제 주문 여부는 확인하지 않았다. **Main 전용 종료 기준에는 이 독립 자동주문 경로도 포함**한다. 이름이 widget/episode가 아니어서 조사에서 빠지는 것을 방지한다. Swing OFF·오프라인 재생은 복원하지 않으며, 연구 함수와 실행 가능한 자동주문 진입점을 구분한다.

추가 서버 조사에서 `korstockscan-machine-fill-telegram.service`도 active로 확인했다. [알림 consumer](../../src/notify/machine_trade_telegram.py)는 `OWNERS={"episode"}`만 처리하므로 잔여 청산 알림 종료 후 제거 대상이다. 위 151개는 최초 이름 기반 조사 집합이며 이 별도 서비스까지 포함한 최종 설치 총수가 아니다.

이번 조사는 로컬 코드·설정·systemd/cron·영수증 조회다. 브로커 API는 호출하지 않았다. 위젯 삭제는 사용자 완료 통보를 근거로 반영한다. 조사 이후 다른 세션의 Main·raw 정리 작업이 진행 중이므로 실행 직전 새 manifest를 고정한다.

## 3. 제거·이관·보존 목록

| 영역 | 대상과 조치 | 남아야 하는 기능 |
|---|---|---|
| 에피소드 실행 | `src/trading/low_price_two_leg/`, `samsung_morning_one_share/`, `samsung_midday_one_share/`, `samsung_afternoon_one_share/`의 service/preflight/gateway/machine/reentry/manual-addon/auto-expansion 삭제 | Main native 진입·보유·청산, 기존 승인 고정감시 |
| 전용 주문·청산 | `regular_two_leg_machine`, `episode_quantity`, `kiwoom_episode_read_control`, `manual_episode_exit_reconciliation`, `order/adaptive_exit/`의 전용 부분을 잔여 종료 후 삭제 | 공용 broker transport·주문/체결/비용/취소·owner registry; Main native trailing·AVG_DOWN |
| 전용 정책·적용 | low-price apply/auto-expansion, Samsung one-share 정책, machine adaptive-exit activation/apply/catalog, 에피소드 timing/weakness 정책 소비 제거 | Main 기계·보조·초기수량·청산 정책 및 현재 적용 hash |
| 소유권 공존 자동화 | `symbol_owner_policy*`, standing authority, 07:32 자동적용의 에피소드 공존 정책 제거 | Main+수동 소유권 대사·명시적 manual veto; §4.2 이관 선행 |
| 위젯 잔존물 | 서버/UI/API/수동·자동 주문 버튼, collector/research/alert, installer·설정·패키지·구 릴리스/복사본의 서버 설치 잔존물 제거 | Main 웹 대시보드/Gunicorn 및 공통 API. 사용자 완료 위젯 삭제는 재요구하지 않음 |
| 정기 장후 | §5의 전용 6개 producer 및 OFF 후보/배분/closed-loop 경로 삭제 | Main 장후·공통 EOD·최종화·정상기동 연결 |
| 비정기 연구 | `episode_source_research`, `episode_prospective_research`, entry-spot/expanded-candidate, adaptive-exit study/replay/evidence/source 및 전용 CLI 삭제 | Main 소비가 입증된 순수 계산만 공용 역할로 이관 |
| 전용 재진입·진입보호 연구 | `machine_rebound_reentry`의 config/market/evaluation/source, `entry_adverse_owners`·전용 policy/summary, `machine_entry_confirmation_study`, `research_fact_archive`·cache·portfolio consumer 정리 | Main의 shared-rebound/AVG_DOWN 및 실제 공통 guard는 caller 대조 후 보존. 이름이 비슷한 기능을 함께 삭제하지 않음 |
| WS·원천 | Main의 episode 전용 writer/thread/status와 전용 seed/manifest 생성 제거 | Main exact-route WS, 호가·체결·완성봉·공통 cache/REST 읽기 제한 |
| 감시·표시 | `episode_health`, `notify.machine_trade_telegram`·전용 서비스/상태, 퇴역 family freshness/알림/추천/자동수리/대시보드 카드 제거 | Main source/submit/holding/exit 감시·Main 체결 알림과 공통 계좌 안전 |
| 실행 인프라 | 서비스·timer·template·instance·drop-in·cron·설치/복구 스크립트·release pin·재시작 allowlist 삭제 | Main 시작·PREOPEN·장후·로그 정리 및 공통 운영 |
| 독립 IPO | runner/실행 cron·installer·전용 설정/상태 소비를 소유권 확인 후 제거 | 재사용되는 Main transport·scanner 등 공통 기능 |
| 테스트·문서 | 전용 동작을 계속 요구하는 테스트·현행 운영 항목 삭제/수정 | 재활성화 방지·Main 회귀·소유권 검증, 최소 과거 종료 증거 |

삭제 후보의 이름만으로 `risk/market_weakness_*`, `research_*`, `machine_*`, `order/adaptive_exit/` 전체를 즉시 제거하지 않는다. Main 실제 consumer가 남으면 해당 기능을 먼저 이관하고 전용 구현을 제거한다. 테스트만 남은 전용 구현을 보존 이유로 삼지 않는다.

## 4. 먼저 끊어야 하는 실제 Main 의존성

### 4.1 WS의 에피소드 원천 수집

[kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)의 `_capture_episode_research_facts`, `_schedule_episode_research_capture`, `episode-native-research-facts` worker와 `episode_research_capture` 상태 노출을 제거한다. 현재 `SharedResearchFactWriter`와 `research_closed_loop`의 lock/경로를 참조한다.

- 새로운 작업 예약 차단 → 실행 중 writer 종료·flush 확인 → worker/import/config/status 제거 → 실제 Main PID의 전용 write 0 순서로 검증한다.
- Main 수신·시장 snapshot·호가/체결·완성봉·exact route는 유지한다. 구독이 공유되면 owner별 reference를 대조하고, 종목 단위 전체 REMOVE/강제 교체로 정리하지 않는다.
- Kiwoom 요청/parser/REG/REMOVE/recovery 변경이 필요할 때는 [공식 API Reference Gate](../kiwoom-api-data-contract.md)의 upstream SHA·관련 파일·조회 시각 검증을 먼저 수행한다.

### 4.2 Main 시작과 수동 잠금

[run_bot.sh](../../src/run_bot.sh)는 `data/runtime/symbol_owner_policy/owner_custody.env`를 읽으며, [manual_control_exclusion.py](../../src/engine/risk/manual_control_exclusion.py)는 `resolve_symbol_owner_policy`를 호출한다. 07:32 자동적용과 그 출력을 먼저 지우면 Main이 결손으로 차단되거나 수동 금지를 잃을 수 있다.

1. Main·수동용 custody/잠금 판단을 남길 공통 owner를 정하고 현행 consumer를 그쪽으로 이관한다. canonical Main owner 이름·계좌·주문 식별자 계약을 실제 호출자와 일치시킨다.
2. 명시적 운영자 veto와 에피소드 격리 때문에 추가된 `machine_owner_scope` 값을 출처별 구분한다. 자동 생성 제한만 종료 근거에 따라 제거하며 같은 종목의 수동 제한을 함께 지우지 않는다.
3. Main 시작이 퇴역 정책/env를 요구하지 않는 것을 확인한 뒤 공존 정책 생성기·loader·07:32 timer를 삭제한다. 유효한 원천 결손을 임의 허용으로 바꾸지 않는다.
4. [공통 owner registry](../../src/trading/order/owner_custody_registry.py)와 append-only ledger는 유지한다. 과거 owner 문자열을 Main으로 일괄 치환하지 않는다.

**시작 스크립트만 수정해서는 부족하다.** 다음 live/후행 consumer를 같은 변경 세트에서 이관한다.

| Main 소비자 | 현행 의존·실패 가능성 | 이관·검증 계약 |
|---|---|---|
| [kiwoom_orders.py](../../src/engine/kiwoom_orders.py)의 `_reserve_owner_registry_intent` | 매수·매도·취소 예약에서 정책을 직접 조회. 등록된 종목은 정책만 지우면 `registered_coexistence_symbol_requires_exact_date_policy` | `main_scalping`·`manual_operator`의 native 소유권 계약으로 대체. 정상 Main 주문과 기존 pending 주문의 취소/매도 허용을 각각 확인 |
| [sniper_execution_receipts.py](../../src/engine/sniper_execution_receipts.py) | 정책 조회 실패 시 체결 callback이 return. 등록된 종목은 원 order owner·activation에 결속 | 기존 주문 ID의 체결·부분체결·금액 정정·지연 callback이 동일 owner/position에 반영. 삭제한 정책을 이유로 실제 체결을 버리지 않음 |
| [sniper_sync.py](../../src/engine/sniper_sync.py), [sniper_s15_fast_track.py](../../src/engine/sniper_s15_fast_track.py) | 계좌 집계 수량과 Main 소유 수량의 대사·회복에서 정책 조회 | 동일 종목 수동 자산을 Main 수량/평단으로 덮어쓰지 않음. registry 관리 종목을 일반 계좌 합산 경로로 되돌리지 않음 |
| `owner_custody_registry` | 삭제 후보 모듈에서 `ACTIVATION_SCHEMA`·`normalize_symbol`을 import | 필요한 schema/정규화·과거 event reader를 공통 소유권 위치로 이관. 기존 ledger bytes/hash chain 유지 |
| [avg_down_replay_capture.py](../../src/engine/scalping/avg_down_replay_capture.py) | 날짜별 공존 정책 파일을 정책 snapshot에 포함 | 신규 snapshot은 Main 소유권 계약을 정확히 고정. 과거 snapshot은 옛 schema/hash를 읽기 전용 해석하며 새 상태로 다시 라벨링하지 않음 |
| [entry_cancel_wait_tuning.py](../../src/engine/automation/entry_cancel_wait_tuning.py), [sniper_trade_review_report.py](../../src/engine/sniper_trade_review_report.py) | `single_owner_unregistered`의 부모 증거를 옛 정책 reason/hash로 검증 | 구·신 source 계약별 검증기를 구분. 이관 이후 정상 Main 표본이 일괄 source_gap/제외되지 않는지 검증 |

후속 구현의 Main 소유권 계약은 계좌·종목·native Main/수동 owner·registry generation/활성화 근거·유효 시작 시각을 명시한다. 옛 공존 정책의 매일 발행을 제거하더라도 **현재 Main 수량/미체결 소유권 검증은 생략하지 않는다.** 기존 `registry_managed`와 `single_owner_unregistered`를 그대로 구분하고, 등록 이력만 지워서 단일 소유자로 꾸미지 않는다. 과거 event parser와 신규 주문 허가를 분리해 역사적 episode event 해석은 유지하되 새 episode 주문은 열지 않는다.

### 4.3 공통 hash·비용·시장 방어

`compact_auxiliary_paired_replay`와 `strategy_owner_replay`는 [research_closed_loop.py](../../src/engine/monitoring/research_closed_loop.py)의 `digest`를 import한다. Main에 필요한 순수 함수를 기존 공용 역할 package로 옮긴 후 전용 closed-loop를 제거한다. JSON 정규화·hash bytes·부모/정책 식별자는 동일하게 유지하며 모듈 이동 때문에 현재 정책을 새로 생성하지 않는다.

`comparison_cost`, tick 계산, WS/cache, broker/order/custody, shared-read 예산은 Main 호출자를 보존한다. `market_weakness_threshold_policy`를 참조하는 panic breadth/알림 등도 먼저 Main 요구를 분리한다. 새 모듈은 기존 `src/utils`, `src/trading/market`, `src/engine/risk` 등 실제 역할에 배치하고 `src/engine` root에 새 구현을 추가하지 않는다.

[market_opportunity_census.py](../../src/engine/monitoring/market_opportunity_census.py)의 보고서 저장 마지막에는 `research_closed_loop.write_admissions(report)`가 호출된다. 해당 catalog의 현재 연구 lane은 episode다. **에피소드 admission/index 생성과 import를 먼저 제거**하고, Main 공통 census JSON·Markdown·`.admission.json` projection과 publication lock/hash 검증은 보존한다. 삭제 모듈을 import한 뒤 실패하거나 퇴역 디렉터리를 다시 만드는 경로가 없어야 한다. Main 기능에서 `ImportError`를 삼키는 방식으로 정리하지 않는다.

### 4.4 이름이 비슷한 Main 기능과 21:15의 Main 단계

- [samsung_policy_episode_research.py](../../src/engine/scalping/samsung_policy_episode_research.py)는 Main 삼성 pattern/runtime/trailing 연구 소비자와 연결된다. Main 기능을 보존하고 필요하면 Main 역할이 드러나는 이름으로 이관한다.
- `scalping/risky_micro_episode`와 Main의 관련 observer는 source-only 반사실적 관측이다. 독립 매매기계로 오인하지 않는다. 현재 Main consumer가 요구하는 부분을 유지하며 새 주문 권한을 부여하지 않는다.
- [21:15 wrapper](../../deploy/run_machine_microstructure_final_refresh.sh)는 에피소드 단계 외에 [samsung_frozen_postclose_validation](../../src/engine/automation/samsung_frozen_postclose_validation.py)을 호출한다. 필요한 Main 삼성 source-only 검증을 **기존 Main 장후의 선택적 진단 실행부로 이관한 뒤** wrapper/timer를 삭제한다. exact source date·입력 hash·단일 writer를 보존한다. 현재 `report_only`, `policy_publication=false`이며 실패도 추가 기동 요건이 아니다. 이관 후에도 결손/대기/실패를 기록하되 Main 정책 발행·strict/controller 완료·PREOPEN/기동을 막는 필수 predecessor로 승격하지 않는다.

## 5. 장후·정책 적용·최종화에서 삭제할 계약

현재 정기 호출과 전용 목적은 아래와 같다. [postclose_summary_handoff.py](../../src/engine/automation/postclose_summary_handoff.py), wrapper의 실제 실행 분기와 함께 확인한다.

| 시각/그룹 | producer | 제거 범위 |
|---|---|---|
| 20:10 Main wrapper 내 | `monitoring.low_price_two_leg_tuning` | profile 정책·leg/비용·version/paired search 보고 및 발행 |
| 21:15 refresh | `monitoring.research_native_capacity_source` | 에피소드 연구용 여력 원천. Main 여력 조회는 보존 |
| 21:15 refresh | `monitoring.machine_microstructure_attribution` | 전용 미시구조 귀속·분모/후행 비교 |
| 21:15 refresh | `automation.machine_entry_timing_tuning` | 독립 매매기계 timing 후보 |
| 21:15 refresh | `automation.market_weakness_hysteresis_tuning` | 전용 약세 hysteresis 후보. 공통 panic 분리 선행 |
| 21:15 refresh | `automation.machine_microstructure_policy_approval` | 전용 정책 승인·승계 |

현재 OFF인 `episode_policy`의 expanded-candidate/`machine_research_closed_loop_refresh --family episode`, `research_allocation` 및 구 Samsung one-share 튜닝도 코드·CLI·환경변수·installer·문서에서 제거한다. `research_version_outcomes.episode_feedback`, 전용 policy semantics 발행, adaptive-exit 후행 분석·승인까지 연결된 소비자를 정리한다. 현재 dispatcher에 없는 옛 단계 목록을 새 실행 대상으로 복원하지 않는다.

**consumer 변경은 producer 삭제와 같은 변경 세트에 포함한다.**

1. `runtime_approval_summary`, recommendation intake, family catalog/semantics, tuning/parquet의 전용 입력·표시·성공 분모 제거.
2. summary handoff, stage registry, strict verifier, done controller, finalization generation, bootstrap/PREOPEN에서 전용 source·stage·정책·terminal 요구 제거.
3. artifact freshness, cron completion, release router, workorder/checklist 생성기에서 에피소드 재생성·수리·설치·기동 요구 제거. `OFF` 보고서를 계속 요구하거나 파일 결손을 복원 과제로 만들지 않는다.
4. **새 계약의 적용 시점/버전을 고정**한다. 과거 에피소드 실패를 Main-only 성공으로 바꾸지 않고, 이전 generation은 원래 scope의 역사로 남긴다. 구 증거를 읽기 위해 삭제한 매매모듈을 import하지 않는다.
5. Main active family·source·terminal만으로 summary → strict → controller/finalization → 다음 영업일 PREOPEN 준비를 새로 봉인한다. Main 정책 payload를 보존하더라도 source/checklist/release가 바뀐 이전 prepared 영수증은 재사용하지 않는다.
6. 장후 writer가 실행 중이면 해당 generation을 끝내거나 정식 중단 영수증을 남긴 뒤 교체한다. 구·신 writer가 공유 출력에 동시에 기록하지 않는다. source date와 다음 실제 영업일을 명시하며 과거 전체 기간을 다시 계산하지 않는다.

## 6. 보유·미체결 처리와 단계별 제거 순서

### 6.1 제거 전 소유권 종료 조건

대상 owner별 **보유 수량 0 + 소유 미체결/부분체결 잔량 0 + 미해결 intent/취소·정정/체결 callback 0 + broker/registry 일치**를 요구한다. 실제 체결 비용·종료 증거가 결손이면 null/결손으로 보존하며 0 손익으로 채우지 않는다.

계좌 전체 또는 같은 종목 전체의 flat을 요구하지 않는다. 현재 [owner_retirement_transition.py](../../src/engine/automation/owner_retirement_transition.py)의 symbol-wide `require_flat`을 그대로 재사용하면 Main/수동 보유까지 잘못 제한할 수 있다. 계좌·종목·venue·order ID별 소유자 수량을 대조하고 **퇴역 owner 몫만 종료**한다. 귀속 불명 수량이 있으면 해당 owner의 terminal 판정이 미완료다.

한화오션 로컬 10주는 첫 대사 대상이다. 실제 잔량이 남으면 신규 BUY/재진입/자동 확장만 차단하고 기존 소유자의 cancel/SELL·보호·체결 처리는 유한한 잔여 목록에 한해 유지한다. 현재 소유자의 정상 종료 후 삭제하며, 계획 수립 자체로 강제 매도·주문 취소·Main 이관을 실행하지 않는다. 소유권 이관을 택할 경우에는 수량·미체결·원가·보호 상태의 native 인수 영수증과 이전 owner 종료를 검증해야 하며 label만 바꿔 종료시키지 않는다.

평가·AI 요청·제출 예약·브로커 응답을 기다리는 작업도 전환 경계에 포함한다. 신규 진입 fence를 실제 consumer에 적용한 뒤 in-flight BUY를 주문 ID/intent별로 확인한다. **보유 0·미체결 조회 0만으로 응답 불명 BUY를 종료 처리하지 않는다.** 취소 요청 성공은 취소 완료가 아니며 부분체결·뒤늦은 체결을 최종 대사에 반영한다. terminal ledger의 마지막 sequence/hash, broker snapshot 시각·모든 해당 venue의 주문/잔량, 처리한 callback 경계와 PID를 함께 기록한다. 처리 결과가 불명확한 intent는 `source_gap`으로 남기고 해당 소유자 삭제를 보류한다.

신규 진입 차단은 [owner_retirement.py](../../src/trading/config/owner_retirement.py)의 특정 종목 퇴역 목록을 **위젯·에피소드 owner 계열 전체의 영구 차단**으로 확장한다. profile 이름 변경·새 종목·자동 확장·구 env가 이를 우회할 수 없어야 한다. 공용 주문 경계에서 **신규 노출을 만드는 BUY와 기존 주문 cancel/SELL·체결 귀속을 분리**한다. 남은 exit 처리는 정확한 기존 owner/order/position/잔량으로 제한하고, BUY 정정으로 노출을 늘리거나 신규 intent로 우회하지 못하게 한다.

신규 자동 BUY는 검증된 Main 진입점과 native `main_scalping` context를 결속한다. 문자열만 Main으로 덧씌우는 변환은 금지한다. 현재 IPO는 owner context 없이 공용 주문 함수를 호출하므로 `context=None`을 Main으로 간주하는 우회까지 점검한다. 정상 Main 호출자가 context 없는 경로를 사용한다면 실제 Main native ID를 producer에서 결속한 후 guard를 적용한다. 관측 전용 Main 기능·실제 Main 단일 소유자/registry 경로를 같은 fixture로 대조한다. 최종 IPO runner/cron 삭제와 공용 주문 경계 테스트를 모두 통과해야 Main-only로 판정한다.

### 6.2 실행 단계

| 단계 | 수행 작업 | 통과 증거/다음 단계 |
|---|---|---|
| R0 대상 확정 | 최신 작업트리·selector·PID·unit/drop-in/cron·프로세스·열린 파일·소유권·출력 참조 재조사. 경로별 제거/이관/보존 manifest와 hash 고정 | 미분류 소비자 0. 삭제 bytes는 이때 계산. 다른 배포·writer·파일 변경 감지 시 해당 명세 재고정 |
| R1 Main 의존성 이관 | §4의 주문/체결/동기화/후행 consumer·공통 hash/비용/custody/시장방어와 Main 선택 진단 이관. Main 정책·잠금 before hash 고정 | 동일 입력의 Main 판정/수량/보호/정책 선택 동일. 신규 단일소유/등록소유와 과거 snapshot 검증 |
| R2 신규 진입 종료 | 신규 예약 timer/확장 경로 중단과 진입 fence를 검증된 전환 릴리스의 실제 PID에 적용. in-flight BUY·broker/소유권 대사, 잔여 exit owner와 다음 점검 조건 고정 | 새 퇴역 BUY 0. 잔여 목록이면 `residual_custody_pending`; exit에 필요한 기존 공통 코드/구독/상태만 한시 유지 |
| R3 코드·예약 제거 | terminal owner의 전용 패키지·UI·설치/복구·timer/서비스·drop-in·cron·pin 및 장후 계약 제거. Main-only 릴리스 작성·리뷰 | production import/호출/신규 write 경로 0. §8 회귀 통과 |
| R4 배포·다음 기동 연결 | **전체 G1 충족 후** Main-only 최종 릴리스로 전환. ubuntu Main PID/웹·구독·정책 소비 확인. 새 Main 장후/최종화/PREOPEN 연결 검증 | code/release/prepared/실제 PID 영수증 각각 확인. 구 exit worker/연구 writer/PID 0 |
| R5 파일 영구 정리 | 참조·FD·소유권 종료 확인 후 전용 raw/cache/policy/상태·불필요한 보고/로그/백업/구 릴리스 삭제 | 실제 제거 명세·보존 hash·회수 용량, 삭제한 경로의 재생성 0 |
| R6 자연·서버 제거 종료 | 다음 자연 Main 장후와 영업일 기동, 서버 설치본·구 릴리스·복사본 최종 재검사 | §9 모든 gate 충족 시 완료. 사용자 완료 위젯 삭제는 재확인 gate에서 제외 |

R1~R3는 리뷰 가능한 코드 변경으로 준비하되, 실제 서비스 제어는 검증된 순서로 수행한다. 잔여 owner 하나 때문에 무관한 전용 연구·화면 정리를 멈출 필요는 없지만, 잔여 청산 코드까지 지우고 완료로 표시하지 않는다. 배포 후 문제가 나면 **퇴역 차단을 포함한 Main 호환 복구 릴리스**로 회복하며 옛 위젯·에피소드 실행 기능을 통째로 복구하지 않는다.

**전환 릴리스와 최종 제거 릴리스를 구분한다.** R2에서 필요한 전환 릴리스는 신규 진입을 금지하면서 잔여 청산을 보존한다. selector만 바꾸면 이미 떠 있는 구 PID·하드코딩된 episode unit에는 적용되지 않는다. 각 실제 consumer의 fence 적용 영수증을 확인한다. R3에서 제거 변경을 준비하더라도 R4 전체 제거 배포는 G1 이후다. 전환 중 잔여 exit worker가 사용하는 import·WS 공급·상태/잠금·알림은 그 consumer 종료 전까지 삭제하지 않는다. 전환 릴리스는 최종 G1 이후 제거 명세에 다시 포함한다.

배포 시작 시 Main code/policy generation·selector·checklist·수동 잠금의 비교 기준을 고정하고, 동시 Main 배포 또는 raw 삭제로 값이 바뀌면 덮어쓰지 않고 변경된 대상부터 재검증한다. 배포/삭제는 같은 실행 소유자의 배타 lock과 compare-and-swap 조건으로 진행한다. 실패 시 신규 퇴역 진입 fence는 유지하고 Main 호환 복구본 또는 잔여 exit 전환본으로 복구한다. 데이터는 consumer 참조를 모두 끊은 뒤 삭제하므로 복구본도 삭제 예정 전용 raw를 요구하지 않아야 한다.

## 7. 설치·프로세스·파일을 깨끗하게 정리하는 방법

### 7.1 실행 가능한 잔존 경로

- systemd template/instance와 user/system unit, wants 링크, override/drop-in의 실제 `ExecStart`·`EnvironmentFile`·재시작 설정을 조사한다. lexical 순서가 뒤인 과거 pin도 포함한다. **신규 기동 timer/확장 예약 차단 → 잔여 service의 fence·exit 보호 유지 → owner terminal 확인 → service 종료 → unit/drop-in/installer 삭제 → daemon reload** 순서다. timer 차단과 보유 관리 service 중단을 한 번에 묶지 않는다.
- masked 71개도 영구 방치하지 않는다. 구 installer·payload·복구 경로가 사라지고 owner-wide 차단이 적용된 뒤 불필요한 mask까지 정리한다. **최소 재활성화 방지 규칙과 terminal 증거만 허용**하며 실행 코드나 일일 퇴역 보고서는 남기지 않는다.
- ubuntu뿐 아니라 기존 root/user systemd·cron·tmux·nohup/transient 작업의 잔존 실행을 조사한다. Main 실제 프로세스는 ubuntu여야 한다. 공통 Main cron 전체를 덮어쓰지 않고 해당 항목만 제거한다.
- 사용자가 위젯 삭제를 완료했으므로 Windows 재설치/제거 확인 작업은 남기지 않는다. 서버에 보관한 클라이언트 빌드·배포 패키지·installer·다운로드 경로·위젯 전용 키 사본은 §7.3에 따라 정리하고, 서버 API/인증 scope/구 클라이언트 재연결이 퇴역 주문·수집을 열 수 없게 한다. 공용 broker/web 자격 증명은 보존한다.
- 전용 dependency는 lockfile/전체 import와 Main UI 사용을 확인한 것만 제거한다. 공통 Python·웹 패키지를 일괄 삭제하지 않는다. 패키지 설치/제거가 필요한 실제 단계는 환경 규칙에 따른다.

### 7.2 파일 삭제와 남길 증거

[9월 이전 raw 삭제 계획](pre-september-source-data-permanent-deletion-plan-2026-10-07.md), [추가 미사용 raw 계획](additional-unused-raw-file-deletion-plan-2026-10-07.md)과 경로·SHA·실행 manifest를 대조해 중복 삭제를 피한다. **DB 본체·행·index·WAL·volume·dump는 이번에도 삭제 대상이 아니다.** Main 보고서·초기 매수수량 부모 보고서와 해당 347행 등 현재 계보도 유지한다.

| 파일 종류 | 처리 |
|---|---|
| 위젯·에피소드 전용 raw/압축본/cache/research/관측 로그 | writer·consumer 종료 후 원본·복사본·백업을 함께 영구 삭제. 대체 백업이나 과거 raw 자동 복원 없음 |
| 전용 active 정책/env/잠금/profile·상태/보고서 | terminal·Main 이관 확인 후 제거. 명시적 manual veto·Main 초기수량/부모 보고서·공통 잠금은 제외 |
| 공통 ledger·혼합 raw/report | **append-only custody ledger와 그 hash chain은 파일 그대로 보존하며 행을 잘라내거나 재해시하지 않음.** 그 외 혼합 파일은 Main/manual·현재 정책 계보·주문 종료 증거의 참조를 먼저 대조. 부모 전체 bytes/hash를 요구하면 원 파일 보존; 독립 분리가 입증된 경우만 전용 잔여 제거 |
| 최소 terminal 감사 증거 | 퇴역 owner ID·기준 시각·종료 수량/주문 대사·해시·삭제 목록·Main 보존 목록만 유지. 대량 원천의 별도 archive가 아님 |
| 구 릴리스/checkout/임시 복사본 | selector·rollback·systemd/cron·PID/cwd/FD·symlink/shared mount 참조 해소 후 전용 실행 사본 제거. Main 지원 복구본과 공유 `.venv`/데이터를 따라가서 삭제하지 않음 |
| 기존 Git 역사·완료 문서 | 실행 트리·설치본 정리와 구분. 공용 Git 이력 강제 재작성은 계획 범위 밖. 과거 문서의 종목·owner를 거짓으로 지우지 않고 현행 절차에서 분리 |

manifest에는 canonical path, device/inode·type·size·SHA, 소유자, producer/consumer, 참조 해소 증거, 처리 방식, 보존 이유를 넣는다. glob만으로 삭제하지 않으며 symlink/hardlink·변경된 hash·열린 FD·새 writer를 재검증한다. 삭제 직전 durable intent, 삭제 후 terminal 및 `df` 차이를 기록한다. 287파일/151unit은 용량 추정치도 최종 삭제 수량도 아니다.

디렉터리·tar/zip 삭제도 **내부 파일 전체에 같은 보호 규칙**을 적용한다. DB/dump·공통 ledger·Main 정책·부모·다른 세션의 dirty 파일이 하위 경로나 압축 멤버에 하나라도 있으면 컨테이너 단위 삭제를 금지한다. 보호 자료를 정확 bytes로 별도 보존하는 검증된 절차가 없는 한 원 컨테이너를 유지한다. 대상 밖으로 나가는 symlink/hardlink/중첩 mount는 따라가지 않는다. `source_data_retirement` 작업의 nonraw 보존 사본·진행 중 durable intent도 최신 manifest에서 보호 여부를 대조한다. 실행 파일은 전용 코드를 제거한 새 릴리스로 옮겨 참조를 해소하며, 보호 컨테이너 잔존을 삭제 완료로 숨기지 않는다.

원천 raw 삭제는 기존 typed manifest와 `data/source_quality/file_source_retirement.apply.lock` 규칙을 준수한다. 코드·unit·installer·정책/env·릴리스 삭제는 서로 다른 처리 명세다. 이를 raw 삭제 도구에 억지로 넣거나 그 도구의 정책/env/lock 보호 검사를 해제하지 않는다. 잠금 파일은 실제 writer가 끝나 lock을 놓은 뒤 정리하며 실행 중인 lock inode를 unlink해 중복 writer를 열지 않는다.

### 7.3 서버 설치본까지 제거하는 추가 작업

[서버 잔존 경로 조사](../../tmp/main-only-widget-episode-retirement-plan-20261007/server-widget-installation-census.json)는 저장소 밖 8개 경로에서 이름에 widget이 포함된 파일 **3,893개**를 확인했다. 소스·테스트·문서가 섞인 경로 수이며, 압축 내부·data/logs/tmp·`.git`·`.venv`·node_modules·`__pycache__`는 이 경로 조사에서 제외했다. 이 수를 실행 설치본 수나 회수 가능한 용량으로 해석하지 않는다.

| 서버 위치 | 확인한 잔존물 / 후속 처리 |
|---|---|
| `/etc/systemd/system` | 위젯 전용 service 7개와 timer 4개의 `/dev/null` mask, 에피소드 등에 적용된 `~zz-widget-retirement-20261006.conf` 등 확인. 전용 unit/mask 제거와 살아 있는 공통 unit의 drop-in 정리를 구분 |
| `/home/ubuntu/KORStockScan-runtime-releases` | widget 이름 파일 3,370개. 구 실행 소스·설치 스크립트·웹 route·테스트/문서가 포함됨. 참조가 끝난 구 릴리스는 디렉터리 단위 제거; 참조 중이면 Main 호환 깨끗한 릴리스로 먼저 교체 |
| `/home/ubuntu/KORStockScan-worktrees` | 438개. 작업 중인 다른 세션/branch·dirty 파일 소유자를 확인하고 전용 잔존 코드 제거를 해당 작업본에 반영. 사용 중인 worktree를 일괄 삭제하지 않음 |
| `/home/ubuntu/KORStockScan-release-mount-backups` | 42개. shared mount/symlink와 실제 원본을 대조한 뒤 불필요 설치 복사본 제거 |
| `/home/ubuntu/KORStockScan-review-all-uncommitted-20260925-data-checkout` / `...-docs-checkout` | 각각 1개/42개. 역사 문서와 설치 payload를 구분하고 미사용 checkout의 참조 해소 후 정리 |
| `/home/ubuntu/KORStockScan-runtime-archives`, `...-storage-archives` | 이름 검색 결과 0이지만 압축 내부는 미검사. archive의 멤버 목록을 읽어 위젯/에피소드 실행 payload·전용 raw/백업 포함 여부 판정. 원천을 복원하지 않음 |
| `/home/ubuntu/KORStockScan2`, 현재 작업트리 및 OS 설치 경로 | 별도 checkout, `/opt`·`/srv`·`/usr/local` wrapper, user systemd/cron, 웹 static/download·reverse-proxy 등록, 패키지 entrypoint·빌드/bytecode/cache를 R0의 실제 참조 census에 포함 |

서버 삭제 순서는 다음과 같다.

1. 활성 selector·rollback·unit/cron·웹 worker·PID/cwd/FD·사용 중 worktree의 참조 집합을 확정한다. 일반 이름의 `.tar/.zip/.whl` 등도 멤버 목록으로 확인하고, 압축본이 없다는 결론을 파일명 검색만으로 내리지 않는다.
2. Main 의존성을 이관한 깨끗한 릴리스와 필요한 Main 복구본을 확보한 뒤 구 설치 경로의 실행 참조를 끊는다. **immutable 릴리스에서 위젯 파일만 임의 삭제해 manifest/hash를 깨뜨리지 않는다.**
3. 사용하지 않는 구 릴리스·전용 패키지/복사본·서버에 보관한 위젯 배포물을 제거한다. 혼합 백업에 Main 자료가 있으면 보호 목록을 먼저 분리 검증한다. Main 자료를 보존하기 위해 위젯 설치 사본 전체를 새 archive로 옮기지 않는다.
4. `__pycache__`/standalone bytecode, console entrypoint, web route/asset, 환경변수·전용 config·키, startup/복구 hook까지 재검사한다. 공통 키·venv·DB·Main 웹앱은 보존한다.
5. 서버의 **위젯 실행 설치본/재설치 payload/활성 route/예약 작업/프로세스 0**을 검증한다. 남긴 문서·Git 역사·최소 퇴역 guard/test·공통 custody 증거는 경로와 이유를 별도 허용 목록에 기록한다. 문자열 잔존과 실행 설치본을 구분한다.

기존 `tools/windows/README.md`와 위젯 퇴역 OPEN 항목의 “운영자 삭제 대기”는 후속 문서 현행화 때 **사용자 삭제 완료·서버 잔존 설치 정리**로 바로잡는다. 과거 terminal 원본을 성공으로 덮어쓰는 대신 이번 사용자 확인과 서버 제거 결과를 별도 기록한다.

## 8. 코드리뷰·회귀·성능 검증

구현 → 자체 리뷰 → 발견 결함 수정 → 재리뷰 → 대상 검증을 반복한다. 리뷰에는 producer뿐 아니라 loader·runtime·재시작·장후·PREOPEN·감시·설치자를 포함한다. 수정이 없는 이번 계획 단계에서는 아래 실행 검증을 통과했다고 주장하지 않는다.

| 검증 묶음 | 필수 사례와 합격 기준 |
|---|---|
| 재활성화 차단 | 구 CLI/HTTP/환경변수/profile rename/새 종목·자동 확장/구 installer/복구 릴리스로 퇴역 BUY가 생성되지 않음. broker 호출 직전 owner 검사 포함 |
| Main 동일성 | 보존 fixture에 대해 기계·보조·수량·cap·AVG_DOWN·청산·manual veto 동일. 이관 함수 hash/비용 bytes 동일. Main 정책 payload·승인 override 불변 |
| 잔여 소유권 | 한화오션 10주 후보, 부분체결·늦은 fill·미체결 취소/정정·재기동·Main/수동 동일 종목 보유·귀속 불명 각각 검증. 잔여 관리 중 신규 BUY 금지와 기존 보호 유지 |
| import/입출력 | Main 실제 import graph·dynamic CLI·entrypoint에서 삭제 모듈 참조 0. 퇴역 디렉터리가 없는 fixture로 Main 부팅·웹·감시·장후·PREOPEN 통과. 퇴역 경로 read/write/open 재시도 0 |
| 장후 세대 | Main-only stage 분모, exact-date/source/release/hash·단일 writer 검증. 누락한 퇴역 보고서를 source_gap으로 오인하지 않음. Main 실제 결손은 여전히 차단. 삼성 선택 진단 missing/failed가 기동 gate로 번지지 않음. 과거 실패 PASS 재작성 0 |
| 배포·재설치 | 새 checkout 설치, reboot/start와 timer reload 후 전용 unit·cron·PID 0. selector와 실제 Main ubuntu PID 일치. Web/WS 공유 기능 유지 |
| 저장공간 | manifest 외 삭제 0, **삭제 프로세스의** DB 접근/변경 0, 고정 Main 정책/부모/잠금 hash 일치, 공통 ledger 원 prefix/hash chain 보존과 정상 append 허용, 삭제 경로 재생성 0 |
| 부하 개선 | 같은 입력·기간의 샘플로 REST 호출 수·shared-read wait·WS 처리 지연·CPU/RSS·write bytes·장후 wall time 비교. episode 전용 API/worker/write/장후 단계는 0, Main 샘플 누락/timeout/지연 악화 없음 |

부하 기준값은 R0에서 수집한다. 같은 원천·장비·측정 구간으로 baseline/candidate를 반복 비교하고 잡음 범위를 함께 남긴다. 비용 절감이나 수익 향상을 샘플 없이 확정하지 않는다. 성능 저하가 나오면 원인과 대상 회귀를 닫은 뒤 배포한다.

검증 명령은 영향을 받는 pytest/import/compile, shell의 `bash -n`, 웹 변경 시 해당 build/route test, 문서 링크/owner 검사와 `git diff --check`다. 퇴역 전용 테스트를 삭제할 때는 공통 안전·재활성화 방지 coverage를 살아 있는 test에 먼저 이관한다. 실주문이나 새로운 provider 호출은 회귀 테스트 수단으로 사용하지 않는다.

### 8.1 구현 시 사용할 구체적 회귀·샘플 범위

| 묶음 | 기존 테스트 소유 위치 | 추가해야 할 사례 |
|---|---|---|
| 주문·수량·소유권 | `test_kiwoom_orders.py`, `test_symbol_owner_coexistence.py`, `test_manual_control_exclusion.py`, `test_s15_custody_recovery.py` | 신규 episode BUY 거절과 잔여 SELL/CANCEL 허용; context 없는 IPO 거절; Main 단일소유·등록소유·수동 공존 정상 처리; 늦은 fill 정확 귀속 |
| Main 후행·회복 | `test_entry_cancel_wait_tuning.py`, `test_entry_cancel_wait_attribution.py`, `test_avg_down_replay.py`, `test_strategy_owner_replay.py` | 구/신 소유권 snapshot·reason/hash와 실제 부모 결속; 정책 제거 후 Main 표본이 0건/source_gap으로 바뀌는 회귀 방지 |
| 공통 관측·장후 | `test_market_opportunity_census.py`, `test_samsung_tick_transition_forward_validation.py`, `test_postclose_summary_handoff.py`, `test_postclose_done_controller.py`, `test_verify_threshold_cycle_postclose_chain.py` | census 공통 출력 유지·episode admission write 0; 선택 진단 실패의 비차단성; episode 입력 없는 실제 Main 단계 의존성 검증 |
| 릴리스·기동·삭제 | `test_runtime_release_router.py`, `test_next_preopen_readiness.py`, `test_postclose_finalization_generation.py`, `test_source_data_retirement.py` | 구 PID/fence 미적용 탐지, 잔여 exit 전환본/최종본 구분, 정책/selector 변경 시 재검증, 보호 하위 파일·archive 멤버·진행 중 삭제 intent 보존 |

위 파일은 `src/tests/` 아래의 기존 검증 위치다. 삭제되는 전용 테스트에서 필요한 공통 case는 이 소유자들로 이관한다. 이름만 통과하는 테스트 대신 실제 native 호출·파일 소비를 검증한다.

샘플은 (1) 정상 Main 신규 진입/추가 매수/청산, (2) Main+수동 동일 종목, (3) episode 잔여·부분체결·응답 불명, (4) manual veto/결손, (5) 전용 자료가 전혀 없는 Main 장후를 포함한다. 저장된 broker/provider 응답과 synthetic receipt를 격리 경로에서 재생하고 네트워크·운영 DB·실제 systemd/cron mutation은 차단한다. baseline/candidate는 같은 최신 승인 Main 정책과 같은 원천/시각으로 3회 이상 대조하고 판정·주문 의도·수량·source 분모를 비교한다. API/쓰기 호출 수, CPU/RSS, wall time·지연 분포와 반복 간 편차를 남긴다. 단기 무체결이나 표본 부재를 기능/성능 PASS로 대체하지 않는다. 새 수익성 gate는 추가하지 않는다.

## 9. 완료 기준과 남을 수 있는 제한

| Gate | 완료 기준 | 미완료 시 owner·다음 확인 |
|---|---|---|
| G0 범위 | 새 manifest의 전용/공통/보존 분류 완료, Main 외 자동주문 진입점 누락 0 | 제거 manifest의 미분류 행·실제 caller 대조 |
| G1 소유권 | 퇴역 owner qty/orders/intents 0, broker/native 대사 완료 | owner별 잔여 관리 receipt. 한화오션 후보 우선; source_gap은 종료로 간주하지 않음 |
| G2 실행 제거 | 전용 production 코드·실행 경로·설치/복구·unit/cron/PID·재생성 writer 0 | code/import·systemd/cron/PID census 재확인 |
| G3 Main 연결 | Main 정책/잠금/수량·보호 동일, shared helper 이관 완료, 선택 릴리스와 실제 PID 소비 일치 | Main regression 및 exact policy/PID receipt |
| G4 장후/기동 | Main-only summary/strict/controller/finalization/PREOPEN 성공, 다음 자연 Main 장후·기동 확인 | exact-date finalization/prepared/PID. 예정 시점 전에는 `not_observed` |
| G5 서버 설치본 | §7.3 전체 서버 경로에서 위젯 실행 설치본·재설치 payload·불필요 복사본 0 | 서버 삭제 manifest·구 릴리스 참조·unit/route/PID 재검사. Windows는 사용자 삭제 완료로 반영 |
| G6 데이터/문서 | 전용 불필요 파일·백업 정리, Main/DB 보호 검증, 현행 문서·미래 작업에서 복구 요구 0 | 삭제 terminal/보존 hash 및 parsed owner 목록 |

G1은 주문·보유 안전 종료, G2/G5는 코드·설치 삭제, G3/G4는 Main 소비·자연 실행으로 각각 검증한다. 과거의 정확한 비용 결손은 최소 원천/종료 증거에 남기되 **회계 결손만으로 이미 broker terminal인 전용 매매 프로세스를 계속 가동하지 않는다.** 수량·주문 귀속이 미해결이면 G1을 닫을 수 없다. 삭제 명세가 이후에도 필요로 하는 원 증거를 지워 스스로 검증 불가능해지지 않도록, 남길 native 종료 증거와 content hash는 R5 전에 확정한다.

최소 owner-wide 퇴역 차단, 수동/과거 custody ledger, 삭제·종료 감사 증거는 기능 잔재가 아닌 **재활성화 방지와 계좌 해석에 필요한 보존 목록**으로 명시한다. `episode` 문자열 0건을 완료 기준으로 삼지 않는다. 잔여 exit manager나 서버 실행 설치본이 남으면 전체 완전 제거를 완료로 표시하지 않는다. 장후/자연 기동을 무기한 기다리는 대신 다음 실제 예정 시각과 정확한 receipt를 잔여 owner에 명시한다.

## 10. 운영 문서·실행 owner 반영

구현 변경과 함께 Plan Rebase §5/§7/§8, 해당 README/runbook/prompt/AGENTS, 장중·장후 지시문, [장후 작업 목록](../audit-reports/2026-09-05-postclose-work-inventory.md), 설치·복구·Windows 문서를 Main-only 상태로 현행화하는 작업을 포함한다. 이번에는 운영 중인 상태를 미리 삭제 완료로 변경하지 않는다.

실행 시점의 일일 체크리스트에 하나의 통합 owner를 두고 Due/Slot/TimeWindow/Track과 R0~R6/G0~G6를 연결한다. 기존 `WidgetFullRetirement1006`, `DirectFamilySourceRepairLowPriceTwoLeg`, `EpisodeCaptureSequence1006`는 과거 Acceptance·증거를 남기고 **이 계획에 따른 제거로 대체되는 작업/남은 서버 설치·custody 작업**을 구분해 인계한다. 에피소드 수익 튜닝·원천 복구를 더 실행해서 제거 허가를 얻도록 만들지 않는다. 현재 Main 구현·raw 정리 OPEN owner와 작업본은 보존한다.

이번 문서 변경에서는 기존 `WidgetFullRetirement1006`의 사용자 위젯 삭제 완료·서버 잔존 정리 계획 연결을 갱신한다. 에피소드 실행 종료를 완료로 처리하거나 중복 실행 owner를 추가하지 않는다. print-only parser로 기존 owner의 단일 등록을 확인하고, 후속 구현에서 미래 에피소드 작업 재생성 0을 검증한다. 외부 Project/Calendar 동기화는 수행하지 않는다.

## 11. 계획 작성 검토 기록

- 1차 검토에서 단순 디렉터리 삭제로 끊기는 Main WS writer, 공통 digest, Main 수동 잠금 consumer, 21:15의 Main 삼성 검증 단계를 찾아 선행 이관에 반영했다.
- 2차 검토에서 잔여 한화오션 로컬 10주, symbol 전체 flat 조건의 과잉 제한, enabled timer와 disabled service 차이, 독립 IPO 주문 경로를 보완했다.
- 사용자 위젯 삭제 완료 통보를 반영해 Windows 재확인 조건을 제거하고 서버 unit/mask·구 릴리스·worktree/checkout·복사본/압축본·설치 payload까지 범위를 확장했다. 별도 active 체결 알림 service도 전용 consumer로 확인해 추가했다.
- 실행 계획과 현재 완료를 구분했다. DB 제외·Main 보고/정책/수동 잠금 보존·전용 파일 및 백업 영구 정리·이전 raw 작업과 중복 방지를 명시했다.
- 문서 링크·owner·parser·diff 검증을 완료했다. 브로커·실거래·장후 재생성·배포·삭제 검증은 후속 구현의 gate이며 이번 작성으로 대체하지 않는다.

작성 검증 결과: [검증 기록](../../tmp/main-only-widget-episode-retirement-plan-20261007/plan-validation.json).

- print-only parser exit 0, parsed task 29개. 위젯·에피소드 원천/튜닝·Main·raw 정리 관련 기존 owner 5개의 등록이 각각 1개임을 확인했다. 위젯 항목의 외부 제거 대기 문구를 서버 잔존 정리 계획으로 수정했다.
- 로컬 링크 검사 누락 0. `git diff --check` 및 새 문서의 독립 whitespace 검사 통과. 최초 검사의 줄 끝 공백 1건은 수정 후 재검증했다.
- 이번 변경은 새 계획 문서, 기존 체크리스트의 해당 위젯 항목, 읽기 전용 조사/검증 기록이다. 다른 세션의 Main·raw 구현 작업본을 보존했다. Python/shell 구현 변경이 없어 pytest/compile/bash 및 실거래·장후 재실행·서비스 제어·배포·삭제는 실행하지 않았다.

## 12. 추가 계획 리뷰와 보완 결과

2026-10-07 사용자 계획 리뷰 요청에 따라 실제 호출자를 다시 대조했다. 아래는 **계획 결함의 수정 내역**이며 해당 runtime 코드가 이미 수정됐다는 뜻이 아니다.

| ID | 발견한 미비점 | 반영한 보완·검증 위치 |
|---|---|---|
| PR1 | 소유권 정책을 시작/manual veto 수준으로만 다뤄 Main 주문·체결·보유 동기화·후행 소비자가 누락됨 | §4.2에 직접 호출자 8개 역할과 registry schema 이관, 구/신 snapshot·부모 검증 명시 |
| PR2 | 공통 census가 에피소드 admissions를 계속 쓰는 경로 누락 | §4.3에서 전용 writer/import 제거와 공통 census/projection 보존 명시 |
| PR3 | 삼성 선택 진단을 Main 필수 장후/기동 조건으로 올릴 여지 | §4.4·§8에서 report-only·발행 권한 없음·실패 비차단 유지 |
| PR4 | 신규 BUY 차단과 잔여 cancel/SELL, in-flight 응답 불명·늦은 fill의 경계 부족 | §6.1에 실제 consumer fence, 신규 노출/기존 주문 처리 구분, native terminal 증거 추가 |
| PR5 | 잔여가 있는 상태의 전환 배포와 전체 삭제 배포가 혼재; service stop이 terminal보다 앞설 수 있음 | §6.2·§7.1에 두 릴리스, G1 선행, timer 차단→잔여 보호→terminal→service 제거 순서 확정 |
| PR6 | 디렉터리/압축본 안의 보호 자료, shared ledger 분할, 동시 raw 삭제·lock inode 경쟁 보호 부족 | §6.2·§7.2에 CAS/배타 실행, 내부 보호 목록, ledger 전체 보존, raw 도구와 설치 제거 명세 분리 |
| PR7 | rebound/adverse 연구·캐시/사실 archive의 별도 전용 구현 누락 | §3에 삭제 후보 추가, Main shared-rebound/공통 guard와 caller 경계 지정 |
| PR8 | 구체적 sample/test 소유 위치와 성능 비교 절차 부족; live ledger 정상 append를 변조로 오인 가능 | §8.1의 격리 표본·대상 테스트·3회 비교, §8의 원 prefix/hash chain 보호와 정상 append 허용 |
| PR9 | 정확 비용 결손만으로 퇴역 매매 프로세스를 계속 유지할 가능성 | §9에서 broker/소유권 terminal과 역사적 회계 결손 분리. 증거 보존 후 실행부는 제거 |

재리뷰에서는 Main 보호 정책 payload와 새 custody/release/PREOPEN hash의 의미를 분리했고, 사용자 위젯 삭제 완료를 다시 미확인으로 돌리는 조건이 없는지 확인했다. 계획·체크리스트 검증 결과는 별도 리뷰 증빙에 기록한다. 실행 단계에서만 확인 가능한 broker terminal·배포/PID·설치 삭제·자연 수용은 G0~G6의 잔여 검증이다.

**추가 리뷰 검증:** [검증 기록](../../tmp/main-only-widget-episode-retirement-plan-20261007/plan-review-validation.json). PR1~PR9 계획 반영 후 재리뷰에서 미반영 계획 결함 0. 링크 누락 0, 명시한 기존 테스트 파일 17개 존재, print-only parser exit 0/29개 task·관련 owner 5개 각 1개, diff/새 문서 whitespace 검사 통과. 이는 문서 검증 결과이며 회귀 테스트 실행 결과가 아니다. 이번 추가 리뷰에서 runtime 코드·설치·정책·DB·주문·파일 삭제는 변경하지 않았다.
