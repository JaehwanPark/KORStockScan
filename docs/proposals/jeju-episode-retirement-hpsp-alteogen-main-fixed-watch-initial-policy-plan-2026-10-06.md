# 에피소드 8종목 완전 제거·HPSP/알테오젠/주성엔지니어링 Main 상시감시·초기 정책 연구 계획

작성일: 2026-10-06 KST.
대상: 에피소드 제거 `080220` 제주반도체·`002900` TYM·`079160` CJ CGV·`111770` 영원무역·`017670` SK텔레콤·`105630` 한세실업·`181710` NHN·`035720` 카카오, Main 상시감시 추가 `403870` HPSP·`196170` 알테오젠·`036930` 주성엔지니어링.
상태: 계획 수립·문서 검토 완료. 구현·연구 계산·운영 적용은 후속 실행 대상이다.
문서 위치: `docs/proposals`. 운영 원칙은 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 owner는 [당일 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)가 소유한다.

## 1. 요청 해석과 전환 계약

사용자가 적은 `HSPS`는 앞서 추천한 HPSP의 오기로 해석하며 실제 종목 코드는 `403870`으로 고정한다. 알테오젠은 `196170`, 주성엔지니어링은 `036930`이다. 제주반도체를 에피소드에서 완전히 삭제하고, HPSP·알테오젠·주성엔지니어링을 삼성전자와 같은 **Main 고정감시·판단·주문·보유·청산 경로**에 추가한다.

2026-10-06 보완 요청을 합쳐 제주반도체·TYM·CJ CGV·영원무역·SK텔레콤·한세실업·NHN·카카오를 **퇴역 8종목**으로 정의한다. 모든 시간대 profile·전용 코드·정책 발행/소비·설치/재설치·자동 확장을 제거한다. 이번 추가분은 한세실업·NHN·카카오이며, 이 8종목을 Main 고정감시 spec이나 별도 초기 정책 연구 대상으로 추가하지 않는다. Main 고정감시 신규 대상은 HPSP·알테오젠·주성엔지니어링 3종목이다. 주성엔지니어링은 현재 episode profile에 없으며 Main에 새로 편입한다.

사용자의 **“정책 적격성 입증은 필요없어”**를 이 계획의 우선 지시로 적용한다. 이번 요청은 같은 계획의 종목 추가로 해석하여 주성엔지니어링에도 동일한 초기 정책 지정·연구·적격성 입증 면제 계약을 적용한다. 세 종목의 상시감시 등록과 초기 정책 채택에는 수익성·승률 향상·최소 표본·독립 holdout·canary 성과 또는 적격성 증명 artifact를 선행 조건으로 요구하지 않는다. 초기 정책 연구는 수행하지만, 표본 부족이나 경제성 미입증을 이유로 기술 전환을 관측 전용 상태에 묶어두지 않는다.

원천 신선도·정확한 symbol/date/session/route·정책 schema/hash·원 owner custody·중복 주문 방지·실행 가능한 수량·broker/account/order/cooldown·hard/protect/emergency safety는 기술 및 주문 계약이다. 적격성 입증 면제는 이 계약의 해제가 아니다. 실제 Main 판단이 `BLOCK`/`RECHECK`이거나 주문 guard가 막으면 기존 경로대로 대기한다. 상시감시는 매수 의무가 아니다.

이번 요청은 계획 보완이다. 이번 변경은 이 문서와 로컬 조사·검증 증빙에 한정한다. 이후 실행을 지시하면 당시 checklist에 `JejuEpisodeRetirementHpspAlteogenMainFixedWatch` stable ID를 정확히 한 개 등록하고 실행일 Due·Slot·TimeWindow·Track·Acceptance를 연결한다. 기존 stable ID를 유지하면서 Acceptance에 퇴역 8종목을 모두 포함하며 종목별 중복 실행 owner를 만들지 않는다. 지금 코드 삭제·정책 발행·broker 조회/주문·서비스 제어·배포/재기동·데이터 정리를 실행하지 않는다.

## 2. 현행 근거와 공통 구현의 소유권

| 조사 항목 | 2026-10-06 조사 증거 | 계획에 반영할 사항 |
|---|---|---|
| 제주 에피소드 | [profiles.py](../../src/trading/low_price_two_leg/profiles.py)의 `jeju_semiconductor_morning`, `JEJU_SEMICONDUCTOR_MORNING_WINDOW`; 오전 09:10~09:49 | profile뿐 아니라 전용 window·정책·분기·목록·설치·연구 소비자까지 제거 |
| 설치 예약 | 제주 live/preflight timer 2파일, service instance 2개. 조회 당시 timer는 enabled/active(waiting), service는 inactive·마지막 exit 0 | 실제 설치 unit/drop-in·재설치 경로까지 정리; exit 0을 잔고/체결/owner terminal로 사용하지 않음 |
| 추가 4종목 | 보완 조사에서 TYM 4개·CJ CGV 4개·영원무역 3개·SK텔레콤 4개, 총 15개 profile | 실행 제외 profile도 포함하여 시간대·revision 전체를 제거; 정확한 목록은 §4.3 |
| 이전 5종목 설치·정책 조사 | 13:55 KST snapshot의 당일 applied policy에 당시 대상 16개 profile, 설치 timer 32개 enabled, 조회한 service instance 32개 inactive; episode service pin은 `machine-source-recovery-20261006-1667abb9` | 당시 5종목 증거로 보존하며 현재 확대된 8종목 수량이나 현재 PID 상태로 사용하지 않음 |
| 이번 추가 3종목 | 16:44 KST census의 한세실업 4개·NHN 4개·카카오 3개, 총 11개 profile; 전용 live/preflight timer 22파일 및 service instance 22개 | §4.3에 정확한 ID·전용 window/revision·정책/설치 제거를 연결 |
| 확대된 전체 대상 | 같은 census에서 native registry 18종목·58개 중 퇴역 8종목·27개 profile; repo timer 54파일, 설치 timer 54개 enabled/active; service instance 51개 inactive·3개 failed; raw 당일 applied에는 두산을 포함한 61개 profile이 남음 | raw bundle 수와 두산 퇴역을 반영한 runtime projection을 구분; 공용 bundle을 직접 절단하거나 service 상태를 custody terminal로 사용하지 않음 |
| 주성엔지니어링 편입 | 로컬 선별 자료의 `036930` 주성엔지니어링; native episode profile에는 없음, 공용 Main spec은 삼성·두산 2개 | 신규 Main spec·symbol별 초기 parent·연구·5종목 공용 dispatch/WS 회귀에 추가; 실제 session/route 적격성 별도 확인 |
| 실행 제외 3개 | `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday`가 `runtime_profile_exclusions`에 남음; 설치 preflight instance 3개가 failed/exit 4 | 3개 모두 퇴역 대상; exit 상태와 제외의 인과는 별도 확인하고 current quarantine·release 조건·재검증 요구는 terminal 뒤 제거; 과거 증거 보존 |
| Main 배제 marker | [manual_control_exclusion.py](../../src/engine/risk/manual_control_exclusion.py)에 `080220: jeju_semiconductor_low_price_two_leg_owner` | episode 전용 marker를 제거하되 명시적 사용자 veto와 manual custody는 보존 |
| Main 공용 구현 | [main_fixed_watch.py](../../src/engine/scalping/main_fixed_watch.py)의 삼성/두산 `FixedWatchSpec`, `enabled_symbols()`·`reserved_slots()` 일반화와 두산 운영 전환 기록 | HPSP/알테오젠/주성엔지니어링을 같은 spec·reconcile에 추가하고 실제 정책 선택까지 확인; 삼성 전용 구현을 다시 복제하지 않음 |
| 퇴역 공용 구현 | `src/trading/config/owner_retirement.py`의 symbol/owner 신규 진입 차단과 두산 archive projection 구현 | 해당 공용 계약에 퇴역 8종목의 `symbol/episode`를 연결; 종목별 퇴역 실행 서비스를 새로 만들지 않음 |
| 두산 정책 선택 누락 | [sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)의 `_entry_ai_policy_position_tag()`가 종전에는 `005930`과 삼성 admission prefix만 허용; 두산은 `SCALP_BASE`를 그대로 전달해 기존 AI 경로로 분기 | spec/admission 기반 공용 dispatch, 종목별 resolver·기계 판단·compact AI 역할과 실제 소비 hash 검증을 §5.3에 추가 |
| WS 발행/연구 저장 결합 | [kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)의 종전 snapshot worker가 `_capture_episode_research_facts()` 완료까지 publication inflight를 유지 | snapshot 발행과 연구 저장을 별도 singleton 작업으로 분리; 연구 정지 중 다음 frame 발행 검증을 §5.4에 추가 |
| 실제 수집 영수증 | [10/6 source-only receipt](../../data/runtime/scalp_micro_reversion_registration_receipt/scalp_micro_reversion_registration_receipt_2026-10-06.json)의 12:51 조사 snapshot에는 `080220`, `080220_AL`; 당시 HPSP/알테오젠은 이 명세에 없음 | 특정 영수증의 부재를 전체 WS 구독 부재로 단정하지 않음; 주성엔지니어링을 포함한 신규 3종목 Main의 실제 연결/소비는 실행일 별도 조사 |
| 종목 선별 | [코스닥 비교 자료](../../tmp/kosdaq-fixed-watch-recommendation-20261006/screen.json)는 완료 10일의 공개 일봉/거래대금 진단 | 후보 선택 참고 자료이며 초기 정책 학습·실제 비용/체결·WS 지연 증거로 사용하지 않음 |

직전 5종목 조사의 `src`·`deploy` reference census는 55개 파일이며 [이전 manifest](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/retirement-supplement/context.json)에 보존한다. 이번 8종목 code/profile census는 83개 파일, 추가 3종목만의 census는 44개 파일이다. [현재 보완 manifest](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/context.json), [전체 reference 목록](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/episode-references.txt), [설치 timer 목록](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/installed-timers.txt), [실제 service binding](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/installed-service-bindings.txt)을 실행 직전 갱신한다. 검색 결과에는 일반 시장 표시·broker fixture·다른 owner도 포함되므로 파일 전체 삭제 목록으로 사용하지 않는다.

[두산 전환 계획](doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md)의 공용 fixed-watch·퇴역·연구 kernel을 재사용한다. [두산 구현·운영 전환 기록](../audits/doosan-main-fixed-watch-implementation-review-2026-10-06.md#최종-운영-전환-완료)은 admission·원천·release/PID 소비와 다음 자연 수용을 구분한다. 이 결과만으로 후속 발견된 정책 선택/WS 저장 결함까지 수정·배포됐다고 판단하지 않는다. 두산 변경과 충돌하는 별도 watcher/retirement registry/연구 producer를 만들지 않고 두 결함의 수리까지 검토된 공용 revision 위에서 변경한다. 기존 삼성·두산의 승인 override·초기 정책·소유권 범위는 이 요청으로 확대하거나 덮어쓰지 않는다.

최신 Plan Rebase §7과 당일 checklist는 두산 배포·퇴역 receipt와 기존 owner `DoosanEpisodeToMainFixedWatch`의 10/7 PREOPEN 인계를 소유한다. 해당 owner·Acceptance를 보존한다. 이 문서의 8종목 제거/HPSP·알테오젠·주성엔지니어링 작업은 두산의 3개 profile 제거와 중복 집계하지 않는다. 최초 13:55 제거 census는 당시 snapshot이며 현재 배포 상태로 사용하지 않는다.

15:11 KST 보완의 [context](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/doosan-implementation-lessons/context.json)와 [작업본 diff](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/doosan-implementation-lessons/reviewed-working-copy.diff)는 당시 수정 표면의 증거다. 이번에는 [후속 수리 감사](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md#배포자연-관찰-완료-기록)도 확인했다. 감사에는 `af780d9b`/15:13:54 bootstrap·PID handoff PASS 및 실제 삼성/두산 target의 machine resolver 연결이 기록돼 있다. 이는 이번 작업의 새 live 검증이 아니다. 15:15~15:17의 121개 snapshot 관찰 최대 age 1.471초는 유한 시간창 증거이며 자연 기계 trace는 미관측이다. capture lock 최대 535.411ms·한 core CPU 약 100.53%가 남으므로 신규 3종목의 처리 여유를 이미 입증했다고 보지 않는다. 기존 `FixedWatchSourceAndCleanupRepair1006`의 자연 수용과 `FixedWatchBudgetSummaryPostcloseAcceptance1006`의 장후 수용 owner를 보존하고 새로 중복 등록하지 않는다.

## 3. 실행 단계와 순서

| 단계 | 작업 | 완료 산출물 / 후속 조건 |
|---|---|---|
| J0 | 실행일 context·Main/episode 각각의 release/PID·owner·설치/worker·원천/consumer census; 공용 두산 작업과 통합 기준 고정 | current checklist owner 1개, 퇴역 8종목·27개 profile 및 동적/역사 identity manifest, 신규 Main 3종목과 기존 2종목의 spec·예산 manifest, retirement 발효 시각과 실제 변경 범위 |
| J1 | 퇴역 8종목 episode 신규 BUY·등록·발행·자동 확장 차단; 종목별 기존 보유/미체결/intent의 책임 종결 | fresh broker/원장/custody 대사; 종목별 원 episode 잔여 책임 0 또는 명시적으로 승인된 인계 완료 |
| J2 | 퇴역 8종목 전용·공용 파일 내 episode 로직 및 설치/장후 의존성 완전 삭제 | 삭제 manifest, live import/dispatch·profile/override·installed unit·재설치/복구 경로 0; quarantine/전용 연구 선택 잔재 0 |
| J3 | 공용 Main spec에 HPSP/알테오젠/주성엔지니어링 추가, admission→정책 dispatch→기계 판단 연결 및 WS 발행/연구 저장 분리 | 종목별 singleton identity·parent/기계 hash·primary owner/AI role·route/원천 receipt, 연구 정지 중 연속 frame 발행; 기존 삼성/두산 및 다른 episode 회귀 PASS |
| J4 | 세 종목의 기존 Main 기준 초기 정책을 명시적으로 지정하고 공용 연구 R0~R3 수행 | 기술적으로 유효한 초기 bundle 및 유한 연구 결과; 경제성 증명·최소 표본 대기 없음 |
| J5 | owning 운영 문서/checklist·장후/loader/PREOPEN·immutable release 인계 | exact-date/hash·parent CAS/readback·installed/selected/실제 PID 대사; 기술 gate만 적용 |
| J6 | 다음 정상 기동과 자연 session/admission/기계 판단·snapshot 발행·장후 수집 확인 | 퇴역 8종목 신규 episode 등록/진입/BUY 이벤트 0, 세 종목 Main 고정감시·실제 정책 dispatch/기계 소비 receipt, WS publication/연구 저장의 별도 상태; 주문·체결·성과는 별도 기록 |

J2~J4의 코드·오프라인 준비는 검토용 작업본에서 병행할 수 있다. 운영 코드 삭제는 해당 종목의 J1 잔여 책임 종료 뒤 수행하며, 종목별로 `entry_retired`, `custody_pending`, `terminal_verified`, `code_removed`, `runtime_removed` 상태와 근거를 기록한다. 한 종목의 미확정 책임을 다른 종목의 terminal로 대체하지 않는다. HPSP/알테오젠/주성엔지니어링의 Main owner/source 기술 계약을 충족하면 다른 퇴역 종목의 종결 대기와 독립적으로 등록을 준비한다. 세 종목의 초기 baseline 지정은 연구 결과를 기다리지 않고 준비한다. 연구 입력 부족이면 baseline을 명시적으로 채택하여 기술 인계를 진행하고 연구 결과를 `data_limited`/`source_gap`으로 보고한다. 연구 종료 후 초기 설정 보완이 필요하면 같은 scope의 초기 채택 계약과 기술 검증으로 연결한다.

## 4. 퇴역 8종목 에피소드 전체 삭제

### 4.1 코드·설치·발행·소비자 제거

| 소유 경로 | 제거할 퇴역 8종목 episode 표면 | 유지할 기능 |
|---|---|---|
| [profiles.py](../../src/trading/low_price_two_leg/profiles.py) | §4.3의 27개 profile·종목별 전용 window·episode allowlist·지원 window·모든 revision/override·전용 constant/함수 | 다른 종목 profile와 공용 dataclass/가격·시간 계산; 공유 window는 남은 실제 consumer를 확인 |
| [policy_runtime.py](../../src/trading/low_price_two_leg/policy_runtime.py), [preflight.py](../../src/trading/low_price_two_leg/preflight.py), 공용 gateway/service | 8종목 activation/logic ID·policy pin·기준/승계/호환 분기·시작/복구 dispatch·전용 transition/quarantine | 다른 episode exact-date/hash·guard 및 공유 주문 안전 |
| [live wrapper](../../deploy/run_low_price_two_leg_live.sh), [preflight wrapper](../../deploy/run_low_price_two_leg_preflight.sh) | 27개 profile case·`KORSTOCKSCAN_LOW_PRICE_TWO_LEG_<PROFILE_ID>_ENABLED`·각 live confirmation·allowlist | 다른 episode 호출과 공용 보호 절차 |
| [installer](../../deploy/install_low_price_two_leg_systemd.sh), [uninstaller](../../deploy/uninstall_low_price_two_leg_systemd.sh), `deploy/systemd` | live/preflight timer 54파일과 생성/복사/enable 목록, 54개 instance의 실행 정의/drop-in/symlink/alias·8종목 owner marker 주입 | 공용 service template와 다른 episode instance; 퇴역 instance의 최소 mask는 재실행 방지 metadata로 보존 |
| [tuning](../../src/engine/monitoring/low_price_two_leg_tuning.py), [expanded research](../../src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py) | 8종목 시작일·symbol catalog·episode 후보·추천/승계/발행 분기·영원무역/카카오 전용 paired 연구 선발 조건 | 남은 실제 consumer의 공용 source/cost·tuning/replay kernel; 새 종목으로 전용 연구를 자동 대체하지 않음 |
| [auto expansion](../../src/trading/low_price_two_leg/auto_expansion_service.py), [auto publisher](../../src/engine/automation/low_price_two_leg_auto_expansion_policy.py) | 8종목을 다른 이름/시간대로 다시 생성하는 진입 경로 | 다른 종목 확장과 공용 symbol/owner 퇴역 검증 |
| [episode source](../../src/engine/monitoring/episode_source_research.py), [prospective research](../../src/engine/monitoring/episode_prospective_research.py), [research facts](../../src/engine/monitoring/research_source_facts.py), [attribution](../../src/engine/monitoring/machine_microstructure_attribution.py) | 8종목 episode cohort·연구/정책/원천 필수 요구와 추천·복구 연결 | 다른 episode와 Main의 공용 원천/원가 계산 |
| [collection_targets.py](../../src/engine/scalping/micro_reversion/collection_targets.py), [run_bot.sh](../../src/run_bot.sh) | 8종목 episode/퇴역 widget의 수집·completed-bar 기본 목록 등 전용 consumer 연결 | HPSP/알테오젠/주성엔지니어링 및 실제 남아 있는 Main/episode consumer에 필요한 시장 원천 |
| [manual exclusion](../../src/engine/risk/manual_control_exclusion.py), [owner policy](../../src/trading/config/symbol_owner_policy.py), [standing authority](../../src/trading/config/symbol_owner_standing_authority.py) | 8종목 episode compatibility marker·신규 진입 권한·자동 재승계 | 명시적 manual veto·custody·다른 owner 권한 |
| bootstrap/장후/summary/strict/controller/에러탐지/보고서/UI·테스트 | 8종목 episode 필수 stage·완료 요구·display/복구·전용 실행 테스트/parametrization | Main 시장 표시/원천과 다른 episode 계약; generic 퇴역 negative 테스트 |

퇴역 8종목 전용 episode 파일이 있으면 파일을 삭제하고, 공용 파일에서는 전용 함수·분기·constant·목록·override를 실제 삭제한다. flag OFF, 주석 처리, alias·compatibility wrapper, 실행되지 않는 전용 module을 남긴 상태는 완료가 아니다. 다른 종목의 공용 파일·테스트를 삭제하지 않는다. 일반 broker parser·source mismatch fixture의 종목 코드와 전용 episode 실행 로직은 구분한다.

현재 reference 목록만으로 끝내지 않고 import·동적 dispatch·config/DB catalog·진행 worker·설치된 unit·dated/current policy·장후 producer/consumer를 대사한다. 제거 후 8종목 코드 검색 결과에는 공용 시장 자료·역사 원장·퇴역 데이터가 남을 수 있으나 **각 종목의 episode 신규 실행 기능은 0**이어야 한다.

### 4.2 재등록·잔여 책임·데이터

발효 시각부터 `symbol in {080220, 002900, 079160, 111770, 017670, 105630, 181710, 035720}, owner_type=episode` 신규 등록을 generic 퇴역 계약으로 차단한다. source catalog → 연구 추천 → publisher → loader → preflight → 전송 직전 owner gate가 같은 계약을 소비한다. profile 이름이 바뀌어도 막히도록 symbol 기준을 사용한다. 옛 archive/current policy·재설치·rollback으로 어느 퇴역 종목의 episode라도 복원되면 실패다. 외부 퇴역 계약을 보존할 수 없는 옛 release는 rollback 대상으로 쓰지 않는다.

이 퇴역 계약의 symbol/owner/시각 및 역사 profile identity는 데이터/소유권 검증에 필요한 최소 정보다. 퇴역 종목의 매매 window·signal·entry/exit builder·policy alias·specialized recovery code를 남기는 근거로 사용하지 않는다. 모든 episode를 일괄 OFF하거나 공용 dated policy를 빈 내용으로 덮지 않는다.

신규 BUY는 먼저 차단하고 잔여 SELL/reconcile/cancel은 원 owner가 책임진다. 과거 fill·미확정 intent·custody를 Main으로 이름만 바꾸어 이관하지 않는다. 새로운 fill이 생기면 terminal을 다시 대사한다. 실제 청산 주문이나 소유권 이전은 이 계획 작성으로 실행되지 않으며, 후속 실행 때 별도 명시 권한이 있는 경로만 사용한다. 잔여 책임이 남으면 삭제의 운영 완료를 보류하고 해당 artifact·owner·closure test를 기록한다.

종목별 terminal 뒤 해당 episode의 active 상태·전용 정책/report/cache를 소비 census와 archive integrity 확인 후 active 경로에서 제거한다. 공용 가격/호가/분봉, mixed owner 원장, 실제 주문/체결/custody·과거 policy 원 증거는 audit-only로 보존한다. 데이터 정리는 코드 삭제와 별도 manifest로 관리하고 실행 중 PID/rollback이 참조하는 immutable release를 직접 편집하거나 제거하지 않는다.

퇴역 8종목은 새 고정감시 spec에 추가하지 않는다. 일반 Main scanner 허용 여부는 기존 owner·manual veto 계약으로 처리하며, episode 퇴역 영수증을 Main의 새 매매 승인이나 보유 이관으로 해석하지 않는다.

### 4.3 퇴역 8종목의 정확한 제거 목록과 공용 정책 정리

| 종목/코드 | 제거할 profile ID 전체 | profile 수 | live/preflight timer 및 service instance 수 |
|---|---|---:|---:|
| TYM `002900` | `tym_morning`, `tym_late_morning`, `tym_midday`, `tym_afternoon` | 4 | 각각 8 |
| CJ CGV `079160` | `cj_cgv_morning`, `cj_cgv_late_morning`, `cj_cgv_midday`, `cj_cgv_afternoon` | 4 | 각각 8 |
| 영원무역 `111770` | `youngone_morning`, `youngone_midday`, `youngone_afternoon` | 3 | 각각 6 |
| SK텔레콤 `017670` | `sk_telecom_morning`, `sk_telecom_late_morning`, `sk_telecom_midday`, `sk_telecom_afternoon` | 4 | 각각 8 |
| 기존 제주반도체 `080220` | `jeju_semiconductor_morning` | 1 | 각각 2 |
| 한세실업 `105630` | `hanse_morning`, `hanse_late_morning`, `hanse_midday`, `hanse_afternoon` | 4 | 각각 8 |
| NHN `181710` | `nhn_morning`, `nhn_late_morning`, `nhn_midday`, `nhn_afternoon` | 4 | 각각 8 |
| 카카오 `035720` | `kakao_morning`, `kakao_late_morning`, `kakao_midday` | 3 | 각각 6 |
| 이 계획 합계 | 8종목 | 27 | 각각 54 |

이번 추가 3종목만의 제거량은 11개 profile·22개 timer·22개 service instance다. 기존 5종목과 합친 8종목 전체 instance는 27개 live와 27개 preflight이며, 공용 template 두 개를 삭제하는 수량이 아니다. timer 파일명은 profile의 underscore를 hyphen으로 바꾼 `korstockscan-low-price-two-leg-<profile>.timer`와 `-preflight.timer`다. instance는 `korstockscan-low-price-two-leg@<profile_id>.service`와 `korstockscan-low-price-two-leg-preflight@<profile_id>.service`다. source 파일뿐 아니라 `/etc/systemd/system`의 실제 설치 파일·enable symlink·실행용 instance drop-in·남은 worker/callback을 함께 닫는다. 두산의 실제 퇴역 결과처럼 잔여 책임 종료 후 전용 instance는 inactive·masked로 readback하여 공용 template로 재기동되지 않게 한다. 최소 mask/퇴역 identity는 실행 코드 잔재와 구분한다. 실행 전 census에서 같은 symbol의 다른 이름/추가 시간대 profile나 unit이 발견되면 동일 퇴역 manifest에 포함한다.

8종목의 window/override 정리는 `JEJU_SEMICONDUCTOR_*`, `TYM_*`, `CJ_CGV_*`, `YOUNGONE_*`, `SK_TELECOM_*`, `HANSE_*`, `NHN_*`, `KAKAO_*`와 날짜별 `PROFILES_*_PRIOR`·`PRE_RECOMMENDATION_PROFILES`·transition 승인 목록까지 추적한다. 현재 날짜의 `PROFILES`에서만 지우고 옛 target date lookup·override·carry로 복원되는 구현은 실패다. 공용 시간값이나 revision 구조는 다른 실제 consumer가 있으면 유지하고 전용 참조만 삭제한다. 순수 archive 재생이 필요한 과거 정책은 live import/dispatch와 분리된 원 증거로 보존한다.

`cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday`의 current `runtime_profile_exclusions`·release condition·cost 재검증 의존성을 제거한다. 이 3개는 이미 실행 제외되어 있지만 완전 퇴역 상태가 아니며, 성과 회복이나 적격성 재입증을 제거의 조건으로 요구하지 않는다. 다른 profile의 quarantine은 그대로 유지한다.

이번 카카오 추가로 `low_price_two_leg_tuning.py`의 `youngone_morning`과 `kakao_late_morning` 전용 paired 연구 admission·frozen selection·candidate/revision 캐시·current successor·필수 artifact 요구를 모두 정리한다. 직전 계획의 카카오 연구 유지 조건은 폐기한다. 현재 bounded selector는 이 두 profile와 별도 fixed selection을 허용하므로 실제 fixed selection·producer/consumer를 확인한다. 남은 승인 profile가 소비하는 공용 tuning/replay kernel은 유지하고, 퇴역 전용 분기/stage가 sole consumer이면 제거한다. 다른 종목을 자동 대체 선발하거나 연구 권한을 새로 부여하지 않는다. 옛 selection이 어느 퇴역 종목을 가리켜도 producer가 retirement disposition을 기록하여 active selection에서 제외하고, 없는 profile를 index하여 KeyError를 내거나 타 종목에 후보를 재결속하지 않는다. 카카오/영원무역 artifact 부재는 restoration/source-gap 요구가 아니다.

installer와 `manual_control_exclusion.py`의 `tym_low_price_two_leg_owner`, `cj_cgv_low_price_two_leg_owner`, `youngone_low_price_two_leg_owner`, `sk_telecom_low_price_two_leg_owner`, `hanse_low_price_two_leg_owner`, `nhn_low_price_two_leg_owner`, `kakao_low_price_two_leg_owner` 및 제주 marker를 제거한다. episode 때문에 생성된 compatibility exclusion만 정확한 provenance로 제거하며, 사용자 수동 lock/veto를 문자열 일치만으로 지우지 않는다. symbol owner policy·standing authority·custody registry·auto apply는 퇴역 계약을 소비하여 `episode` 재승계를 거부하고 원 수동/다른 owner 책임을 보존한다.

공용 정책은 remaining active profile 집합에 맞춰 baseline·candidate·applied/prepared·override·exclusion·profile count·hash·schema 검증·summary source generation을 함께 갱신한다. 이미 소비된 10/6 applied/PREOPEN 및 과거 transition receipt는 원 증거로 보존하고, 다음 적용일의 producer-issued 새 bundle을 만든다. 옛 bundle에서 27개 항목만 직접 잘라 원 hash나 PASS를 재사용하지 않는다. 불변 parent와 retirement 처분을 결속하여 남은 종목의 policy 값이 의도치 않게 변하지 않았음을 검증한다.

raw applied의 역사 집합 19종목·61개에서 이 계획의 8종목·27개만 빼면 **11종목·34개 profile**이다. 별도 [두산 퇴역](doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md)의 1종목·3개를 반영한 현행 native registry는 18종목·58개이며, 여기서 8종목·27개를 제거한 기대값은 **10종목·31개 profile**이다. 조사 시점의 실행 제외 3개는 모두 제거 대상이다. raw/applied 원 hash와 runtime projection을 구분하며 이 수량은 새로운 확장이 없는 snapshot의 기대값이다. 실행 시 실제 current/installed/remaining 집합으로 다시 계산하고 두산 제거를 중복 집계하거나 남은 episode를 일괄 비활성화하지 않는다.

## 5. HPSP·알테오젠·주성엔지니어링 Main 상시감시 구현

### 5.1 공용 spec와 lifecycle

[main_fixed_watch.py](../../src/engine/scalping/main_fixed_watch.py)의 `FixedWatchSpec`·`spec_for()`·`enabled_symbols()`·`reserved_slots()`에 `403870`, `196170`, `036930`을 추가한다. 두산 후속 수리까지 닫힌 공용 revision을 통합 기준으로 사용한다. 현재 살아 있는 삼성·두산의 spec/flag/hash/override를 보존하고, 신규 3종목의 활성 설정은 별도 symbol 키에 결속한다. 제안 env 이름은 `KORSTOCKSCAN_MAIN_FIXED_WATCH_403870_ENABLED`, `KORSTOCKSCAN_MAIN_FIXED_WATCH_196170_ENABLED`, `KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED`이며 기존 표준 launcher에서 명시적으로 관리한다. 신규 spec의 `initial_policy_scope="non_samsung"`을 실제 resolver에 결속하고 주문 소유권은 기존 `main_scalping` 계약을 사용한다.

[kiwoom_sniper_v2.py](../../src/engine/kiwoom_sniper_v2.py)의 admission·DB 복원·FIFO 제외·예산 예약·session 이동·WS 등록·관측 준비·EXIT 후 재무장에 같은 spec을 사용한다. 독립 HPSP/알테오젠/주성엔지니어링 bot·scanner·주문 loop·systemd service는 만들지 않는다. 모든 활성 spec의 종목별 outcome을 반환·집계하여 삼성 결과만 성공으로 보이는 silent failure를 없앤다.

- `MAIN_FIXED_WATCH` origin을 유지한다. generation/admission은 정확한 symbol·거래일·session·route·원 DB identity를 포함하며 종목 간 상태·cooldown·정책 hash를 섞지 않는다.
- 각 종목의 실제 활성 target은 최대 1개다. 적격 session·flat custody·감시 예산 조건에서 정상 Main WATCHING을 생성하고 WS를 등록한다. admission 이후 warmup·fresh source가 준비되면 Main machine/compact auxiliary/주문/holding/exit를 그대로 사용한다. 아직 source가 준비되지 않은 WATCHING은 기존 source WAIT로 처리하며, 관측용 신규 매매 owner로 만들지 않는다.
- 일반 scanner의 같은 종목 WATCHING/HOLDING, 미체결·미확정 intent·manual custody가 있으면 duplicate admission을 만들지 않는다. 실제 정책 적격성 증명은 면제하되 custody/계정/수량/주문 계약은 재사용한다.
- HPSP/알테오젠/주성엔지니어링의 자동 매매 owner는 `main_scalping`으로 지정하고 manual custody/veto를 보존한다. Main 고정감시 등록을 episode 자동 확장·새 독립 owner의 등록 사유로 사용하지 않는다. 공용 owner 명세와 expansion 선발이 Main 고정감시 spec을 소비하여 같은 종목의 새 episode 생성을 막는다. 기존 다른 owner 노출을 발견하면 정확한 인계/종결 없이 이름을 바꾸지 않는다.
- 고정 slot은 실제 활성 spec 수로 예약한다. 삼성·두산과 신규 3종목이 모두 활성이라면 총 5개이고, 다른 활성 상태에서는 그 수로 계산한다. 기존 총 cap을 상향하지 않고 일반 FIFO 여유를 줄여 반영한다. 실제 effective cap·동적 감축·다른 watcher의 처리 예산을 대사하고, 예산 부족 시 종목별 명시적 대기/실패를 반환한다. 예약만 늘리고 target가 사라지거나 한 종목만 성공으로 보이는 상태, 일반 watcher의 무한 지연을 허용하지 않는다. 재시작·날짜/session 전환·비활성화·EXIT/cooldown 후 재무장도 함께 검증한다.
- 현재 Main의 승인된 진입·보유/청산·수량/stop/AVG_DOWN·provider/model·hard safety를 기본값으로 결속한다. 제주 episode의 4-tick target이나 삼성 전용 frozen 후보를 세 종목에 복사하지 않는다. spec의 `initial_policy_scope` 지정이 실제 resolver의 기계정책 선택과 일치하는지는 §5.3에서 별도로 검증한다.

### 5.2 기존 WS와 실제 Main 소비

기존 Main WS 연결에서 필요한 exact item·0B 체결·0D 호가를 재사용한다. 현재 종목별 KRX/NXT 거래 적격성과 session contract를 확인하고 공용 resolver가 해당 session에서 지원하는 KRX item/`_AL`/`_NX`를 사용한다. 코스닥 상장 또는 높은 거래량만으로 NXT 지원을 추정하지 않는다. 미지원 session은 명시적으로 대기한다.

퇴역 8종목 episode 구독 정리에서 다른 남은 consumer의 같은 item을 함께 REMOVE하지 않는다. 종목/route/type별 마지막 consumer가 사라질 때만 해제한다. 새 종목도 중복 REG나 별도 연결을 만들어 결손을 숨기지 않고 등록 manifest·실제 receipt·Main quote·completed bar·기계 trace·최종 submit source를 차례로 결속한다.

producer PID/start ticks·transport epoch·정확한 route/type·post-admission warmup·clock/sequence·writer loss를 보존한다. 관측 전용 raw route의 packets가 있다는 이유로 Main quote ready로 표시하지 않는다. [entry_ws_snapshot.py](../../src/trading/market/entry_ws_snapshot.py)와 [entry_liquidity_guard.py](../../src/trading/order/entry_liquidity_guard.py)의 기존 stale/conflict 기준을 유지한다. 조사 당시 호가 2초·체결 5초 기준이며 실행 때 현행 contract를 다시 확인한다.

활성 spec 전체와 일반 watcher를 같은 시간대에서 비교하여 snapshot publication/read-time age·capture lock·loop p50/p95/max·eval/defer·REST reserve/deadline을 계측한다. 거래량·구독 예산 여유로 freshness·평가 지연을 면제하지 않는다. 수용 검증에 문제가 생기면 기존 source/processing 계약을 수리하며 cap·provider·guard를 임의로 바꾸지 않는다.

Kiwoom REG/REMOVE·FID/응답 parser·재연결·REST/WS 호출을 수정할 경우 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)의 당시 공식 upstream SHA·관련 `kiwoom_docs`/spec/core/realtime/Postman·조회 시각을 검토 증거에 기록한다. 이번 문서 작성은 protocol 수정이나 API 실행이 아니다.

### 5.3 admission 이후 실제 기계정책 선택까지 공용화

두산의 결함은 상시감시 등록은 일반화했지만 **정책을 선택하는 호출 경로가 삼성에 한정된 것**이다. 실제 저장 tag는 `SCALP_BASE`이고, 검증된 fixed-watch 호출만 `_entry_ai_policy_position_tag()`에서 resolver용 `SCANNER` tag를 전달하는 기존 계약이 있었다. 종전 `005930` 조건과 삼성 admission prefix 때문에 두산은 이 계약에 진입하지 못했다. target 등록·WS 수신·정책 bundle 존재만으로 기계정책 소비 완료를 판정하지 않는다.

[sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)의 `_entry_ai_policy_position_tag()`와 실제 호출 metadata, [entry_setup_live_policy.py](../../src/engine/scalping/entry_setup_live_policy.py)의 `resolve_live_prompt_policy()`·`verify_machine_primary_runtime_contract()`, [ai_engine_openai.py](../../src/engine/ai_engine_openai.py)의 정책 resolve·기계 평가·compact auxiliary dispatch를 하나의 producer→consumer 경로로 검토한다. 기존 WATCHING/재평가·재무장·복원·cache 경로가 같은 계약을 전달하는지 확인하며 정상 최초 호출만 수리하고 다른 호출이 옛 tag를 전달하는 누락을 허용하지 않는다.

- symbol 판정은 공용 `FixedWatchSpec`/`is_fixed_watch()`를 소비한다. `005930`에 두산·HPSP·알테오젠·주성엔지니어링을 직접 덧붙인 별도 allowlist를 만들지 않는다. future spec은 검증된 등록 절차를 통해 추가하며 임의 row의 `watch_origin`만으로 기계 owner를 획득하지 않는다.
- 정확한 symbol·당일 KST admission·generation·session/route binding을 검증한다. 다른 symbol의 admission, stale 날짜, 빈/충돌 generation, 미지원 session이면 명시적 기술 WAIT/실패를 남긴다. 정상 등록 종목의 dispatch 결손이나 invalid policy를 기존 AI 경로로 조용히 우회하지 않는다.
- resolver용 tag 변환을 실제 DB `position_tag`·scanner promotion ID·scanner 예산/모집단 변경으로 확대하지 않는다. 정상 fixed-watch 저장 tag와 native admission identity는 그대로 유지하고 일반 `SCALP_BASE`/수동/미등록 종목에 이 변환을 적용하지 않는다.
- 삼성은 기존 `samsung` scope·정책/override를 유지한다. 두산·HPSP·알테오젠·주성엔지니어링은 각 symbol의 명시적 `non_samsung` 초기 parent를 선택하며 삼성 전용 recipe/threshold/연구값을 상속하지 않는다. bundle hash뿐 아니라 실제 machine component hash·policy group·effective venue/session까지 확인한다.
- 유효한 정책과 fresh source에서는 `primary_decision_owner=mechanistic_entry_adjudicator` 및 현행 compact auxiliary 역할로 연결한다. machine `BLOCK`/`RECHECK`은 기존 규칙대로 대기하고 독립 entry AI의 BUY로 승격하지 않는다. `ENTER_NOW`만 compact auxiliary와 기존 최종 submit guard로 진행한다. provider/model·가격·수량·holding/AVG_DOWN 권한은 변경하지 않는다.

실행 전 기술 검증 matrix는 삼성·두산·HPSP·알테오젠·주성엔지니어링 각각의 적격 continuous scope와 일반 scanner/비고정감시 대조군을 포함한다. 정상 및 손상된 native target metadata를 실제 helper→resolver→기계 dispatch에 전달한다. `verify_machine_primary_runtime_contract()`에서 synthetic `position_tag=SCANNER`만 검사하는 것은 충분하지 않다. 테스트는 [test_main_fixed_watch.py](../../src/tests/test_main_fixed_watch.py), [test_entry_setup_live_policy.py](../../src/tests/test_entry_setup_live_policy.py)와 기존 AI dispatch 계약 테스트에 확장하며 외부 provider/broker를 호출하지 않는다.

종목·적용일·session·admission/generation·actual/effective tag·policy group·parent/bundle/machine hash·primary owner·AI role·resolve status·machine action을 검증 영수증에 결속한다. policy hash가 다른 종목이나 session의 것인데 등록 성공만으로 통과하면 실패다. source WAIT와 정책 dispatch 결손을 구분하고, 실제 PID의 첫 유효 기계 평가까지 소비를 확인한다. 적격 session의 자연 기회가 아직 없으면 그 수용만 `not_observed`로 남기며 경제성 표본/실제 fill을 새 통과 조건으로 요구하지 않는다.

### 5.4 WS 스냅샷 발행과 에피소드 연구 저장의 대기 분리

종전 snapshot worker는 frame을 발행한 뒤 같은 worker에서 `_capture_episode_research_facts()`를 실행했고 연구 저장이 끝나야 `_dashboard_snapshot_write_inflight`를 해제했다. 따라서 첫 frame이 저장되어도 느린 연구 I/O·writer lock이 다음 frame 발행을 지연시킬 수 있었다. packet 수신 age·capture lock·frame 발행 age·연구 저장 lag를 서로 다른 지표로 기록한다.

[kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)의 `_maybe_write_dashboard_snapshot()`는 WS lock 안에서 필요한 route/type·원 timestamp/sequence/epoch·등록 receipt를 bounded immutable frame으로 봉인하고 serialization/I/O를 lock 밖에서 수행한다. 현행 snapshot writer가 소비하는 필드·history 상한을 재사용하고 live getter/history의 원 데이터는 축소하지 않는다. `now_ts`는 frame capture 시각을 유지하며 worker 시작/연구 완료 시각으로 바꾸어 오래된 frame을 신선하게 표시하지 않는다.

snapshot 발행이 끝나면 publication inflight를 해제하고 연구 저장은 별도 singleton worker에서 진행한다. snapshot worker·WS callback·Main quote/기계 판단이 연구 저장의 완료·future/result·join을 기다리게 하지 않는다. [research_source_facts.py](../../src/engine/monitoring/research_source_facts.py)의 `SharedResearchFactWriter`와 native cross-process writer lock을 재사용하며 종목별 writer·추가 REST/WS 연결·구독·polling을 만들지 않는다. 두산 작업본의 `_schedule_episode_research_capture()` 경로를 통합 기준으로 검토한다.

process 안에는 연구 worker 최대 1개만 허용하고 native cross-process writer ownership을 보존한다. busy/lock contention에서 callback을 block하거나 무제한 thread·queue를 쌓지 않는다. 지연 중 추가 trigger는 bounded defer/coalesce로 처리하되 실제 누락/미수집 구간과 capture precision·저장 lag를 연구 원천 계약에 기록한다. 연구 write 실패를 성공으로 표시하거나 lost row를 합성하지 않는다. 퇴역 종목/OFF 모집단의 정상 부재와 남은 episode의 저장 결손을 구분한다.

연구 worker가 frozen frame을 소비한다면 해당 frame identity/hash를 보존한다. 별도 worker에서 최신 snapshot을 다시 읽는 현행 방식이면 실제 읽은 frame의 generation·capture 시각과 저장 시각을 기록한다. trigger 당시 frame과 뒤에 읽은 frame을 같은 원천으로 결속하지 않는다. publication 성공이 연구 fact 영속화까지 증명하지 않으며 연구 지연이 quote/주문 freshness 완화의 사유도 아니다.

연구 exception·writer lock busy·thread 시작 실패·stop/reconnect·날짜 변경에서 각 worker의 inflight/lock을 반드시 복구한다. publication failure와 research failure를 독립 상태로 보고하고 다른 worker의 성공으로 덮지 않는다. latest frame 공유 때문에 CPU/GIL/디스크 경쟁이 사라졌다고 가정하지 않으며 실제 publication interval·lock/loop/read budget을 검증한다.

필수 회귀는 연구 writer를 의도적으로 멈춘 상태에서 **다음 snapshot frame이 연구 해제 전에 발행되고 연구 writer 수는 1개인 것**이다. [test_kiwoom_websocket.py](../../src/tests/test_kiwoom_websocket.py)의 기존 `test_research_capture_cannot_block_next_dashboard_or_start_second_writer`, worker 시작 실패·capture clock·bounded projection 회귀를 삼성/두산/HPSP/알테오젠/주성엔지니어링 및 남은 episode fixture로 확장한다. 연구 정상/지연/예외 각각에서 exact-route payload 의미·source timestamp/hash·consumer readiness와 publication age·capture lock/loop p50/p95/max를 비교한다. 등록 종목의 stale guard를 늘리거나 원 timestamp를 재기록하여 PASS를 만들지 않는다.

## 6. 초기 정책 지정과 연구 — 적격성 입증 면제

### 6.1 초기 정책을 먼저 지정

HPSP·알테오젠·주성엔지니어링은 **현재 Main 비삼성 기준 정책**을 각 종목의 초기 정책으로 명시적으로 채택하도록 준비한다. 각 venue/session의 실제 부모 정책·진입 feature/action·holding/exit·stop·sizing·cost·auxiliary·submit guard의 원 hash를 freeze한다. 선택된 초기 parent는 적용일과 symbol에 결속하고 경제성 증명을 기다리지 않는다. §5.3의 실제 resolver/기계 소비 hash까지 같은 parent에 결속하며 spec의 문자열 지정이나 파일 생성만으로 초기 정책 적용 완료를 선언하지 않는다.

`policy_qualification_required=false`, `qualification_status=not_required_by_user`, `selection_basis=operator_directed_initial_adoption`를 초기 채택의 보고/인계 계약으로 제안한다. 이는 구현 때 현행 schema에 맞춰 정의하며, 같은 symbol/date/session의 초기 채택에만 적용한다. 모든 Main publisher의 자격 검사를 전역 boolean으로 우회하지 않는다.

현재 publisher/loader가 successor의 minimum support·holdout·수익성 gate를 초기 채택에도 강제한다면 **해당 세 종목의 초기 채택**을 구분하도록 필요한 범위의 계약을 수정한다. 기존 symbol/date/hash·잘못된 원천/입력·parameter 범위·원 parent binding 검증은 유지한다. baseline 지정 누락이나 잘못된 정책을 조용히 fallback하는 구현은 금지하지만, 연구 결손 시 baseline carry는 명시적으로 기록하여 허용한다.

이 면제 범위는 이번 세 종목 등록·초기 정책 연구/선정과 그 초기 설정 보완이다. 다른 owner/family 또는 후속 자동 successor의 기존 승격 계약을 이 지시로 전역 변경하지 않는다. 삼성/두산 bundle과 기존 승인 override를 덮지 않는다.

### 6.2 R0 — 원천·기준 계약과 누락 census

정책 변경을 연구하는 source는 clean baseline과 Plan Rebase의 더 엄격한 **2026-09-29 이후** 적격 원천을 사용한다. 이전 공개 10/20/60일 일봉은 종목 선별/진단으로 분리한다. 기존 삼성 research와 제주 episode 거래를 HPSP/알테오젠/주성엔지니어링의 native fixed-watch 거래로 바꾸지 않는다.

각 종목별 체결·호가·completed bar·Main machine/decision trace·원래 admission/plan·submit/fill/cancel/terminal·cost를 source date·venue/session·policy version별로 census한다. 실제 `MAIN_FIXED_WATCH`, 일반 scanner 원래 기회, raw 가격 기회, actual 주문/체결을 서로 다른 모집단으로 보존한다. 반복 WAIT/RECHECK·retry·child leg를 독립 기회로 중복 세지 않는다. append 중인 source는 byte bound/prefix hash로 봉인한다.

식별 가능한 결손 row/window만 제외하며, 누락·미지원·검열·valid-empty를 구분한다. 표본이 없으면 `data_limited`/`source_gap`과 producer/artifact/원인을 보고하고 baseline 초기 지정은 유지한다. 결과를 계산할 수 없다는 이유로 세 종목의 등록이나 기술적으로 정상인 초기 정책 채택을 막지 않는다.

### 6.3 R1 — 종목별 유한 후보 비교

동일 Main 기계 feature와 기존 action group 안에서 진입 조건·ENTER/BLOCK/RECHECK 구분을 비교한다. initial baseline 1개와 최대 3개 family에 각각 parameter set 최대 3개를 사용하여 **종목당 최대 10개, 세 종목 합계 최대 30개 정책**으로 연구 범위를 고정한다. 주성엔지니어링도 별도 symbol/date/session/parent/source/cost binding과 R0~R3 결과를 산출한다.

| family | 연구 질문 | 고정하는 축 |
|---|---|---|
| 기존 Main baseline | 각 종목의 원 기회에서 초기 기준 동작은 무엇인가 | owner·가격/지연 모델·holding/exit·수량·자본·cost·guard |
| 연속 흐름 확인 | 체결 흐름과 현재 가격 반응으로 ENTER/RECHECK 구분을 보완할 수 있는가 | past-only WS 특징·causal 시계 |
| 눌림 뒤 재개 | 확인된 눌림/회복 상태에서 기계 판단을 보완할 수 있는가 | 미래 저점/고점 금지·동일 원 기회 |
| 횡보/과열 구분 | 식별 가능한 불리한 구간을 구분할 수 있는가 | 동일 비용·기회 분모; 새 hard gate 생성 금지 |

후보·parameter·parent/source/cost/kernel hash·평가 시계·학습/검증 경계를 결과를 보기 전에 freeze한다. holding/exit·trailing·AVG_DOWN·수량/slot/cap·모델/provider·hard safety를 같이 sweep하지 않는다. HPSP·알테오젠·주성엔지니어링을 한 모집단으로 합쳐 서로의 빈 표본을 채우거나 한 종목의 수치를 다른 종목에 복사하지 않는다.

### 6.4 R2 — 동일 기회·자본·비용 재생과 시간순 진단

기준과 후보를 동일 frozen opportunity·capital·원 owner plan·정확한 spread/수수료/거래세/slippage·execution delay·holding/cancel/terminal로 재생한다. split/probe·조건부 잔여 주문은 해당 native owner replay가 지원하는 경우에만 계산하고, 미지원 동적 잔여 계획을 정적 fill로 바꾸지 않는다.

actual 실현 결과, 모델링된 paired CF, 단순 가격 도달을 분리한다. 실제 PnL은 `COMPLETED + valid profit_rate`만 사용한다. missing cost/outcome은 null/unresolved이며 zero EV나 no-edge로 바꾸지 않는다. full/partial fill·no-submit·blocked/rejected/canceled/censored와 원천 불일치를 분모와 함께 공개한다. 분봉 안의 target/stop 선후가 모호하면 success로 단정하지 않는다.

현재 승인된 Main `KRX|KRX_REGULAR` 비교는 cost-bound binary target-first 선택 지표를 사용하고, net profit·paired EV·tail·coverage·기회 비용은 별도 보고한다. 다른 venue/session에 KRX 선택 계약을 자동 확대하지 않는다. 시간순 분리와 opportunity clustering·미사용 후속 구간 비교는 연구 결과의 설명 수단으로 수행하지만 **독립 holdout 입증·최소 날짜/표본·개선률 통과를 전환 gate로 요구하지 않는다**. 관측하지 않은 개선/성공을 적격성 면제에서 추론하지 않는다.

### 6.5 R3 — 초기 설정 산출과 부족 원천 처리

종목별 산출물은 `initial_baseline_adopted`, `initial_settings_selected`, `baseline_retained`, `data_limited`, `source_gap`, `measured_no_improvement` 중 실제 결과에 맞게 기록한다. 연구에서 계산 가능한 초기 설정을 선택하거나, 계산할 원천이 없으면 명시적 baseline을 유지한다. 어떤 결과에도 positive EV/유의한 승률 향상/표본 성숙 증명이 없다는 이유만으로 등록 완료를 보류하지 않는다.

artifact는 최소한 다음을 결속한다.

`symbol`, `owner_type`, `watch_origin`, `source_date`, `publication_date`, `target_date`, `venue`, `session`, `initial_parent_policy_sha256`, `selected_policy_sha256`, `source_manifest_sha256`, `cost_model_sha256`, `kernel_sha256`, `candidate_count`, `population_counts`, `research_status`, `selection_basis`, `policy_qualification_required`, `qualification_status`, `rollback_parent_sha256`.

보고서의 `metric_contract`에는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 명시한다. `sample_floor`는 이번 초기 채택의 통과 문턱을 만들지 않고 actual comparable/opportunity/cluster counts와 계산 가능 여부를 공개한다. 권한은 종목별 초기 설정의 연구·제안이며 실주문·provider·quantity/cap·hard safety 변경 권한을 부여하지 않는다. 내부 schema/field/fallback text는 English ASCII로 작성한다.

연구 CLI가 필요하면 두산 계획과 같은 `src/engine/monitoring/main_fixed_watch_policy_research.py` 하나를 사용한다. 책임은 offline Main 고정감시 정책 보고서이며 주문 소유권은 없다. 결과 위치는 `data/report/main_fixed_watch_policy_research/`, 테스트는 `src/tests/test_main_fixed_watch_policy_research.py`를 제안한다. 실제 생성 전 nearby producer/consumer·역할 package·공용 작업 상태를 다시 확인하고 engine root에 module을 추가하지 않는다.

[삼성 고정감시 연구](../../src/engine/scalping/samsung_fixed_watch_evaluation_research.py)의 identity/causal clock/cost 방법만 참고한다. `005930` frozen 후보와 source/path/cost 계약은 종목 코드 치환으로 재사용하지 않는다. 순수 계산을 재사용하면 역할 package의 단일 kernel과 삼성/두산/HPSP/알테오젠/주성엔지니어링 fixture를 유지한다. 종목별 독립 연구 wrapper·cron·장후 stage를 늘리지 않는다.

[Main runtime policy](../../src/engine/scalping/mechanistic_entry_runtime_policy.py)의 기존 발행/loader/장후 경로에서 종목별 초기 binding과 적용일을 관리한다. 보고서는 `runtime_effect=false`이며 실제 적용은 별도 dated bundle/PREOPEN/PID receipt로 기록한다. 향후 자연 Main 원천이 생성되면 같은 고정 후보/초기 설정의 cumulative/rolling/version 결과를 기존 Main 경로에서 누적한다. 경제성 관측은 계속하되 초기 적용의 추가 승인 조건으로 바꾸지 않는다.

## 7. 지표의 역할과 완료 판정

| 지표/검증 | 역할 | 전환을 막는 조건 |
|---|---|---|
| 퇴역 8종목 각각의 owner/custody terminal·재등록 차단 | 삭제의 실행/소유권 검증 | 해당 종목의 미확정 보유/주문/intent·원 owner 책임 공백 또는 episode 신규 실행 가능 |
| symbol/date/hash/schema·초기 parent binding | 초기 설정의 기술 정확성 | 잘못된 종목/적용일/부모/parameter·내용 변조·명시적 baseline 누락 |
| native target→정책 dispatch→기계 owner/AI role·실제 machine hash | 초기 정책의 producer/consumer 기술 검증 | 정상 fixed-watch가 기존 독립 AI로 silent fallback, 잘못된 symbol/group/session parent 소비, DB/scanner identity 변조 |
| WS/clock/sequence·quote/bar·submit source | `source_quality_gate`; 실제 판단/주문 원천 | 기존 stale/conflict/missing guard에 해당하는 해당 판단/주문; 전체 등록을 경제성 미입증으로 막지 않음 |
| snapshot publication age·capture lock와 연구 저장 lag/status | 기존 `source_quality_gate`/처리 계약의 진단; 주문·threshold 권한 없음 | 연구 저장 때문에 다음 frame 발행 대기, 무제한 worker/queue, 원 시각 변조·false ready·저장 결손 은폐 |
| loop/slot/read budget·duplicate admission | `funnel_count`; 공용 처리와 lifecycle 진단 | 기존 cap/처리 계약 위반·중복 owner/주문 위험 |
| Main binary target-first 비교 | `main_entry_win_rate_selection`; 승인된 KRX 비교 및 초기 설정 설명 | 최소 표본/개선률/독립 holdout 미입증은 이번 초기 전환의 blocker 아님 |
| net profit·paired EV·tail·cost/coverage | `primary_ev`; 실제/CF 경제성 관측 | 미계산/불충분/개선 미입증은 이번 초기 전환의 blocker 아님; real hard safety는 기존 owner가 적용 |

등록·원천 준비·machine decision·submit·fill·terminal·정책 소비·경제성 관측을 별도 receipt로 보고한다. 초기 채택은 `operator_directed_initial_adoption`이며 evidence-qualified policy 또는 수익성 입증으로 보고하지 않는다. 실제 주문이나 fill이 발생하지 않아도 상시감시 등록 자체는 완료할 수 있다.

## 8. 운영 문서·장후·배포와 복구

후속 실행에서는 변경한 owning 운영 문서·설치/제거 절차·traceability·실행일 checklist를 목표 계약에 맞춰 인계한다. README·Plan Rebase §5/§7/§8·prompt·AGENTS 등의 기준 문서 정비는 명시적으로 요청된 유지보수 범위에서 수행한다. 이 계획 보완은 해당 기준 문서나 현재 checklist를 수정하지 않는다. 퇴역 8종목 episode 전용 OPEN/필수 정책은 실제 retirement/각 종목 잔여 책임 종료 뒤 종결하고 다른 episode의 source repair owner·Acceptance는 유지한다. HPSP/알테오젠/주성엔지니어링 초기 정책 적격성 증명 면제는 정확한 세 종목 scope의 운영 계약에 기록한다.

episode catalog/research/collection population·policy apply·bootstrap·summary/tower/checklist/strict/controller·artifact detector가 같은 8종목 retirement 발효 경계를 사용하도록 한다. 폐기된 episode artifact·3개 quarantine 증거·영원무역/카카오 전용 paired selection·successor 부재를 복구 작업이나 source-gap으로 요구하면 실패다. 퇴역 종목의 미종결 custody와 남은 episode/HPSP/알테오젠/주성엔지니어링의 실제 원천·정책 기술 결손은 계속 정확히 경고한다. 변경된 code/source/schema에 맞춰 summary/checklist freeze → strict → controller → 다음 PREOPEN 준비를 새 세대로 닫는다.

다음 PREOPEN 전환을 기본 경로로 준비한다. 후속 실행에서 당일 적용을 명시적으로 지시한 경우에는 [기존 intraday handoff](../runtime-release-routing.md#authorized-intraday-policy-preserving-code-handoff)를 사용하고 이미 소비된 bootstrap/env/prepared receipt를 덮지 않는다. reviewed immutable release·설치/router·selected·실제 Main/남은 episode PID·exact-date 정책을 각각 대사한다. 이 문서 작성이나 경제성 면제가 배포/재기동/실주문 실행을 자동 수행하지 않는다.

release 준비에서는 §5.3 정책 dispatch와 §5.4 발행/저장 분리 코드·회귀가 모두 포함된 실제 revision을 pin한다. 두산 최초 전환 receipt를 후속 결함 수리 receipt로 재사용하지 않는다. PREOPEN은 실제 symbol/admission metadata로 resolver matrix를 검증하고, 기동 뒤 PID/epoch별 기계 평가 hash·primary owner/AI role·연속 snapshot publication을 확인한다. 연구 저장 상태는 별도로 확인하며 frame 갱신 성공으로 fact 영속화 성공을 대신하지 않는다. 복구 revision도 이 두 기술 계약과 퇴역 경계를 검증한다.

복구는 마지막 검증 공용 Main 코드/초기 parent 및 해당 종목의 활성 설정으로 수행한다. HPSP/알테오젠/주성엔지니어링 등록 문제를 복구해도 퇴역 8종목 episode 신규 BUY·재등록·timer/installer 복원은 허용하지 않는다. 공용 두산 퇴역 계약도 보존하며 삼성/두산 Main·남은 episode와 수동 veto·quantity/custody·hard safety를 보존한다.

## 9. 유한 종료 조건과 회귀 검증

| Gate | 완료 기준 |
|---|---|
| G0 퇴역 8종목 owner 종료 | 종목별 fresh 원 episode broker/원장/custody terminal 또는 별도 승인 인계 완료; 잔여 책임 공백 0 |
| G1 퇴역 8종목 코드 완전 삭제 | snapshot의 27개 및 실행 census의 추가 profile와 전용 실행 module/분기/window/override/wrapper/테스트·active dispatch·installed timer/실행 정의/drop-in·재설치 경로 0; timer 54개 및 추가분 제거, 54개 및 추가 퇴역 instance는 inactive·masked readback; current quarantine 3개·영원무역/카카오 전용 연구 선택 잔재 0; 최소 mask/퇴역 데이터와 audit 증거는 구분 |
| G2 퇴역 8종목 재등록 차단 | static/auto expansion·prospective 연구·policy carry·옛 target date/archive/설치/rollback에서 8개 `symbol/episode` 신규 실행 0; 다른 episode 회귀 정상 |
| G3 세 종목 Main 고정감시 | 종목별 최대 1 target·독립 native identity, 적격 session/flat/예산 조건에서 정상 WATCHING/WS 등록; 실제 helper→resolver→기계 dispatch에서 비삼성 parent/기계 hash·primary owner/compact AI role 일치 및 silent fallback 0; DB tag/일반 scanner 모집단 보존; 날짜/restart/session/EXIT/cooldown·slot 계산과 삼성/두산 회귀 PASS |
| G4 원천/초기 정책 기술 연결 | exact route 0B/0D → Main quote/bar/기계/최종 source gate 대사; 연구 writer 정지 중 다음 frame 발행·연구 singleton·exception/start failure cleanup·원 capture clock/route 의미 보존; symbol/date/schema/hash/parent/기술 parameter 검증; 경제성 적격 증명 gate 0 |
| G5 연구 수행 | 신규 3종목별 baseline freeze·종목당 최대 10개/합계 최대 30개 후보·동일 비용/자본·원 모집단 대사 및 R0~R3 결과/한계; 원천 부족 시 baseline과 정확한 `data_limited`/`source_gap` 처분 |
| G6 정상 기동/소비 | dated 초기 bundle/PREOPEN/실제 PID·종목별 native fixed-watch 생성→실제 기계 평가/hash/역할 receipt와 연속 WS 발행·별도 연구 저장 상태, 퇴역 8종목 신규 episode 등록/진입/BUY 이벤트 0; 남은 episode policy/서비스 소비 receipt; submit/fill/PnL 입증은 등록 완료 조건에서 제외 |

G0~G4는 기술 전환, G5는 연구 작업의 수행/처분, G6는 실제 기동/소비 상태를 닫는다. 연구 source가 없을 때 동일 replay를 반복하거나 표본이 성숙할 때까지 등록을 지연하지 않는다. 자연 기동/대상 session을 아직 보지 못하면 그 receipt만 `not_observed`로 남긴다. 정책 적격성·수익성·실제 fill 증명은 별도 완료 gate를 생성하지 않는다.

필수 회귀 사례는 다음과 같다.

- 제거된 27개 profile·이름/시간대를 바꾼 8종목 episode·옛 target date/policy/설치 입력이 startup/publisher/전송 직전 모두 거부되며 다른 episode는 정상 동작한다.
- 3개 실행 제외 profile의 quarantine/release 조건을 current 검증에서 제거해도 archived 증거는 보존된다. 영원무역/카카오 전용 paired/frozen selection·candidate·캐시가 없는 live profile를 조회하거나 타 종목에 결속되지 않으며 sole-consumer 전용 stage 부재는 source-gap/복구 요구가 되지 않는다. 별도 승인된 남은 fixed selection·공용 연구/정책·profile 집합과 count/hash/schema를 검증한다.
- 8종목 각각 보유·부분 fill·미체결·미확정 intent·종결 후 늦은 callback을 주입하여 신규 BUY 차단과 원 owner cancel/SELL/reconcile 책임을 분리한다. 다른 종목의 terminal로 삭제 완료를 대신하지 않는다.
- HPSP/알테오젠/주성엔지니어링 spec을 각각 켜고 끄거나 한 종목에 custody/미확정 intent가 생겨도 다른 고정감시의 identity/hash/구독/기존 수량 계약은 바뀌지 않는다. 활성 5종목·비활성 조합·동적 예산 부족에서 실제 slot 수와 종목별 admission/defer 결과가 일치하며 silent drop/중복·일반 watcher 무한 지연이 없다. 퇴역 8종목의 고정감시 spec은 이 변경에서 생성되지 않는다.
- 삼성·두산·HPSP·알테오젠·주성엔지니어링의 정상 native target metadata로 helper→resolver→기계 평가를 적격 scope별 검사한다. 삼성은 삼성 parent, 나머지는 symbol별 비삼성 parent/hash와 compact AI 역할을 소비한다. 기존 AI 경로로 silent fallback하지 않으며 일반 scanner·미등록/수동 target과 실제 DB `SCALP_BASE` tag는 바뀌지 않는다.
- 다른 symbol admission·stale 날짜·빈/충돌 generation·wrong route/session·missing/invalid policy에서 명시적 기술 실패를 기록한다. machine `BLOCK`/`RECHECK`이 legacy AI BUY로 승격되지 않으며 `ENTER_NOW`의 auxiliary/최종 guard는 기존 계약을 유지한다. 복원/재무장/cache/재평가 호출도 같은 기계 hash와 native identity를 사용한다.
- HPSP/알테오젠/주성엔지니어링의 고정감시 spec을 episode auto expansion에 넣어도 새 episode owner가 생성되지 않는다. admission 직후 source가 아직 없으면 WATCHING과 등록은 유지되고 기존 source WAIT가 동작하며, fresh post-admission evidence 이후에만 실제 기계 판단으로 진행한다.
- 경제성 표본 0·holdout 없음·개선 미입증에서 명시적 baseline을 소비하여 정상 Main WATCHING/판단까지 도달한다. qualification waiver가 기존 source/submit/주문 safety gate를 우회하지 않는다.
- 잘못된 symbol/date/hash/schema/parent·silent fallback은 initial adoption에서도 실패한다. 초기 면제 flag를 다른 symbol/family 또는 전역 successor 우회에 사용할 수 없다.
- source-only packet만 있거나 Main quote 0·post-admission/warmup/clock/sequence 결손이면 false ready가 없다. stale/disconnect/reconnect·늦은 callback·epoch/route/date 변경·no-tick/VI/거래정지에서 기존 guard가 유지된다.
- 연구 writer를 Event로 정지해도 publication inflight가 해제되고 연구 해제 전에 다음 frame이 발행된다. 동시 trigger·cross-process lock busy·write exception·thread 시작 실패·stop/reconnect에서 연구 worker 최대 1개와 inflight/lock cleanup을 검증하고 정상 재개 뒤 다음 frame을 발행한다. 무제한 queue·추가 source 요청은 없다.
- bounded dashboard projection이 실제 writer의 exact-route payload 의미를 보존하고 원 live history는 변하지 않는다. serialization/연구 지연 중 capture 시각과 원 packet 시각을 다시 쓰지 않으며, 늦게 읽은 연구 frame을 이전 trigger generation에 결속하지 않는다. publication PASS와 연구 persistence 실패를 독립적으로 보고한다.
- 퇴역 8종목 구독 정리가 남은 consumer의 같은 item을 제거하지 않으며 HPSP/알테오젠/주성엔지니어링은 정확한 session eligibility로 등록한다. slot/read budget·일반 watcher·Main loop 부하를 같은 session에서 검증한다.
- 연구 population·actual/CF·비용·종목/date/native identity를 혼합하지 않고 malformed source·중복 opportunity·미지원 split replay·미확정 outcome을 성공으로 계산하지 않는다.
- 새 장후 계약에서 퇴역 8종목 episode artifact/quarantine/영원무역·카카오 전용 paired selection/successor가 없어도 전체 필수 검증은 정상이며 남은 episode와 신규 3종목 Main의 실제 기술 결손·미종결 custody는 별도로 실패한다.
- 재설치·wrapper 직접 호출·자동 확장·rollback 뒤에도 54개 timer/실행용 instance/drop-in과 27개 profile가 복원되지 않는다. 퇴역 instance mask와 외부 신규 BUY 차단은 유지된다. 기대 remaining 집합은 raw 역사 집합에서 다른 확장이 없으면 11종목·34개, 두산 퇴역을 반영한 현행 집합에서는 10종목·31개이며 남은 정책 값·source/cost·주문 guard를 보존한다.

각 수정은 구현 → self review → 보완 → 재리뷰 → targeted pytest/compile/`bash -n`·계약 검증 → 결과 보고로 닫는다. 문서는 링크/owner/authority·print-only parser·`git diff --check`로 검증한다. 관련 회귀가 닫히기 전 broad automation·비싼 보고서 재생성·서비스 제어를 실행하지 않는다.

## 10. 계획 작성 검토와 실행 분리

계획 검토 범위는 퇴역 8종목의 제거 완결성·공용 producer/consumer·symbol/owner·정책 적격성 면제와 기술 guard의 분리, 두산 구현 후 발견된 정책 dispatch/WS 연구 저장 결합의 재발 방지다. 현재 8종목의 잔고/미체결 terminal, HPSP/알테오젠/주성엔지니어링 Main WS·기계정책 소비·정책 성과·실제 배포/PID 전환은 검증하지 않았다.

문서 검토는 27개 profile·54개 timer/instance의 정확한 목록, 실행 제외 3개의 완전 퇴역, 영원무역/카카오 paired/frozen 연구 소비자, 공용 정책 count/hash/schema, 종목별 잔여 책임, 남은 episode·두산 작업과의 통합을 확인한다. 이번 보완은 한세실업·NHN·카카오 제거와 주성엔지니어링의 native Main spec·실제 비삼성 기계정책·초기 정책 연구를 연결하고, 모든 활성 5종목의 정책 dispatch·slot/WS publication·연구 singleton·capture clock·loss/실패 검증으로 확대한다. 기존 초기 정책 연구와 적격성 면제 계약은 신규 3종목 범위에 유지한다.

문서 self review → 보완 → 재리뷰의 최종 결과와 링크/anchor·현재 print-only backlog parser·owner·공백 검증은 [이번 검증 기록](../../tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/validation.json)에 보존한다. 기존 두산/원천 후속/장후 수용 owner와 이 proposal의 미등록 상태를 각각 확인하며, 과거 parser의 OPEN 수를 현재 증거로 재사용하지 않는다. 문서 검증은 코드 수리·운영 적용 완료를 뜻하지 않는다.

직전 제거 범위 보완 당시 Plan Rebase·checklist의 바이트가 두산 인계 변경으로 달라져 최신 diff/owner를 재확인했다. 이번에는 최신 두산 후속 수리 감사·current profile/설치·raw applied와 Main spec·전용 paired selector를 읽고 조사 시각·code/document hash를 별도 context로 보존한다. 이 작업에서 기준 문서·checklist·코드·applied policy를 수정하거나 새 실행 항목을 등록하지 않았다.

이 proposal에는 실행 checkbox를 추가하지 않으며 현재 checklist에 새 실행 owner를 등록하지 않는다. 실제 실행 지시 때 당시 owner와 expanded Acceptance를 연결한다. 전체 dirty workspace의 다른 변경은 보존하고 이 문서 변경의 검증과 구분한다.

직전 제거 범위 증빙은 `tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/retirement-supplement/`, 두산 구현 결과 반영 증빙은 `tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/doosan-implementation-lessons/`, 이번 추가 3종목 제거·주성 편입 증빙은 `tmp/jeju-episode-hpsp-alteogen-main-watch-planning-20261006/hanse-nhn-kakao-jusung-supplement/`에 보존한다. 문서 작업이므로 pytest/compile/`bash -n`·broker/provider 요청·연구/장후 보고서 재생성·서비스 제어·정책/배포 변경은 실행하지 않았다. 코드·운영 기록의 읽기 전용 검토와 계획 검증은 코드 삭제·연구 수행·실제 기동 성공을 뜻하지 않는다.

## 11. 실행 상태 인계

[실행 검토](../audits/episode-eight-retirement-main-five-execution-review-2026-10-06.md)에서 구현·리뷰 수정·1,304건 통합 검증과 종목별 제한 연구 결과를 기록했다. 초기 정책의 경제성 사전 입증은 요구하지 않는다. 설치된 54개 timer와 54개 service instance의 native 퇴역·검토 release 배포·Main 재기동을 사용자 승인 범위에서 진행하며, 완료 receipt와 자연 관측 대기는 같은 검토 기록 및 현재 checklist owner로 인계한다. 과거 소비 정책/PREOPEN 원본과 남은 정책 값은 보존한다.
