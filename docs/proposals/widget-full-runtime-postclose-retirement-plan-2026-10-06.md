# 위젯 전체 런타임·장후작업 제거계획

작성: `2026-10-06 KST`

상태: **서버 코드·배포·정리 검증 완료; Windows 제거 및 자연 장후/기동 acceptance 대기**. 아래 §12는 최초 계획 작성 결과이며 현재 실행 결과가 아니다. 코드·서비스 변경과 원 custody 대사는 별도 실행 receipt로 기록한다.

목표: 위젯 자동·수동 매매, 가격 화면/API, 관측·알림·종목연구, 정책 생성·발행, 장후·PREOPEN·감시 연결을 운영 경로에서 완전히 제거한다. Main 및 에피소드가 소비하는 공통 기능은 해당 소유자로 분리한다. 과거 주문·보유 소유권은 원 증빙으로 추적 가능해야 한다.

실행 소유자: [현재 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)의 `WidgetFullRetirement1006`. 후속 제거 실행 지시 때 아래 순서로 진행한다. 문서의 단계를 승인 receipt나 실제 완료로 해석하지 않는다.

## 1. 현황과 조사 범위

[조사 manifest](../../tmp/widget-full-retirement-planning-20261006/inventory.json)는 `2026-10-06T07:57:54+09:00` 기준 작업공간의 파일 해시, 외부 import, 설치 unit, 로컬 상태와 dirty 목록을 기록한다. root 운영 문서와 `analysis/benchmarks`의 추가 파일 확인 시각은 `extended_at_kst`로 구분한다.

| 조사 항목 | 확인 결과 | 해석 제한 |
|---|---|---|
| `src/deploy/tools/data/config/.github` 및 root/analysis 참조 파일 | 284개 | 문자열·파일명 census다. 모두 삭제할 파일이라는 뜻이 아니다. |
| 위젯 이름 또는 전용 패키지의 표면 | 88개 | 코드·테스트·unit·클라이언트·benchmark가 포함된다. 공통 소비 여부에 따라 삭제/이관/수정한다. |
| 위젯 이름이 아닌 파일의 직접 import | 31개 연결 | 동적 import, 설정 문자열, 파일·schema 소비는 별도 확인해야 한다. |
| 설치된 위젯 전용 unit | service 7개 + timer 4개 | 실제 drop-in과 재설치 경로도 제거 대상이다. |
| 로컬 매매 상태 | 삼성전자 주문 적격, 두산·한화오션 관측 전용 | 당시 로컬 주문·이월 수량 0은 계좌 flat 증거가 아니다. 계좌 조회는 실행하지 않았다. |

systemd 경로는 `next-session-ready-20261005-e16ac48b`를 가리킨다. 선택 설정과 실제 PID 소비는 다른 증거이며, 후속 실행 직전에 원천과 진행 중 작업을 다시 고정한다. 특히 이 조사 이후 장중 주문이 발생할 수 있으므로 위 수량을 삭제 승인에 재사용하지 않는다.

## 2. 제거 범위

| 영역 | 주요 대상 | 최종 처리 |
|---|---|---|
| 자동 매매 | `src/trading/widget_auto_trade/` 전체: service, engine, gateway, policy, verification, notifications | 신규 BUY 중지와 잔여 custody 종결 후 전용 코드 제거 |
| 수동 위젯 매매·가격 API | `src/web/*price_widget_routes.py`, `src/web/app.py` blueprint 등록, widget 주문 executor | 수동 BUY 진입점 먼저 닫고 custody 종결 후 route와 등록 제거 |
| Windows 화면·설치 | `tools/windows/samsung_price_widget.py`, `Install-SamsungPriceWidget.ps1`, 관련 README/설정 | 배포 소스 제거, 실제 설치 PC의 프로세스·시작 항목·예약 작업 제거 확인 |
| 고정 관측·알림 | samsung/doosan/hanwha widget advisory, contract, entry/Telegram notify | 위젯 전용 producer·상태·알림 제거 |
| 확대 관측 | widget symbol runtime collector/contract, research watch collector/config, expansion recommendation | 위젯 구독·수집·추천을 제거. 명단을 Main/에피소드 실행 명단으로 승격하지 않음 |
| 신호·종목·보조 연구 | widget signal policy research, advisory evaluation/calibration/policy, auto-trade calibration, signal quality, mechanical/paired replay, bounded plan execution | 위젯 실행·수동 CLI·연구 후보 생성 경로 제거 |
| 정책·적용 | widget symbol runtime policy, widget auto-trade policy, observation catalog, candidate/version projection | 새 발행·승계·관측 등록·실주문 적격 복원 경로 제거 |
| 장후·PREOPEN | widget wrapper, independent producer receipt, stage registry, machine refresh의 widget 분기, summary/controller/readiness | 위젯을 필수 producer/consumer 집합에서 제거 |
| 감시·보고·배분 | process health, artifact freshness, semantic family watch, intake/tower/verifier, allocation/portfolio/census | 위젯 active owner·필수 원천·추천·배분·감시 조건 제거 |
| 운영 설치 | service/timer/drop-in, installer/router/auto-apply target, cron·boot·env·인증키 참조 | 설치 잔재와 재생성·재설치 경로 제거 |
| 데이터·cache·문서·테스트 | widget runtime/report/research/cache/tmp/log/클라이언트 설정 및 관련 항목 | 증거/공통 의존성 구분 후 정리. 운영 설명과 테스트도 목표 상태로 정리 |

manifest에 기록된 파일을 출발점으로 사용한다. 구현 시 각 참조를 `remove_widget_only / migrate_shared / update_integration / preserve_history` 중 하나로 분류하며, 미분류 참조가 있으면 최종 제거 완료로 판정하지 않는다.

## 3. 공통 기능과 잔여 소유권

### 3.1 공통 기능 분리

위젯 파일명만으로 일괄 삭제하면 다음 소비자가 깨질 수 있다.

- `widget_comparison_cost`는 Main timing, confirmation, rebound, microstructure, opportunity census, rising-missed 및 공동 경제성 계산에서도 import한다. 비용 계약과 계산을 공통 시장 계산 위치로 옮기고 소비자·fingerprint를 일괄 갱신한다. 후보 위치는 기존 역할 패키지 `src/trading/market/comparison_cost.py`다. 위젯 전용 파일과 영구 호환 wrapper는 남기지 않는다.
- `research_closed_loop`는 widget signal 연구의 `_summarize_episodes`를 가져온다. 실제 에피소드 사용 계약을 확인해 필요한 집계만 monitoring 공통 모듈로 분리하고 위젯 신호 탐색 자체를 이식하지 않는다.
- `widget_episode_source_research`, shared WS/quote/micro confirmation, entry adverse, profit stagnation, target ratchet, adaptive exit, market weakness는 호출자별로 분해한다. 에피소드·Main의 독립 사용 부분은 유지하고 widget 어댑터·owner 분기만 제거한다.
- owner registry, manual exclusion, order/fill Telegram, symbol-owner auto-apply는 위젯 신규 owner를 모집·선택하지 않도록 바꾼다. 과거 owner ID/주문을 읽는 역사 경로는 보존한다.
- 공동 allocation은 widget arm을 제거한 active-family 집합으로 계산한다. 확보되는 자본을 Main/에피소드 수량·cap 증가에 자동 배분하지 않는다.

새 Python 파일은 역할 패키지를 먼저 확인한 뒤 위치를 확정한다. `src/engine` root에 새 모듈을 만들지 않는다. 비용·시간·부호·단위·원천 제외·수량 계산은 이관 전후 동일 입력으로 대조한다. 공통 기능의 이름 변경이 source-quality나 주문 안전 조건을 약화시키면 이관을 완료하지 않는다.

### 3.2 Main·에피소드 경계

- Main 삼성전자 `005930` 고정 감시와 기계·보조판정, Main holding/exit, AVG_DOWN은 별도 owner다. 위젯 제거를 이유로 감시 종목이나 정책을 삭제하지 않는다.
- 에피소드의 삼성/두산/한화 관련 profile은 위젯과 같은 종목코드를 사용할 수 있다. widget unit와 `low-price-two-leg-*` unit를 이름 일부로 묶어서 삭제하지 않는다.
- 시장약세, REST 요청 제어, WS 구독·depth·체결 데이터, 토큰 캐시, 주문/custody registry는 살아 있는 소비자의 기능을 유지한다.
- widget 관측 pin 제거 시 동일 코드의 Main/에피소드 구독까지 `REMOVE`하지 않는다. 기존 exact item/venue/session/owner별 참조를 확인하고 widget 전용 참조만 해제한다.
- 기존 OFF·격리 에피소드를 위젯 제거 과정에서 활성화하지 않는다. 다음 기동 검증은 실제 허용된 profile 집합과 사전 격리 상태를 각각 대조한다. 위젯 제거 전부터 있던 다른 family 결손은 해당 owner에 남기고 제거 회귀와 구분한다.
- Kiwoom REST/WS/REG/REMOVE/recovery 코드를 수정하는 단계에서는 [공식 API Reference Gate](../kiwoom-api-data-contract.md)의 upstream SHA·관련 파일·조회 시각 확인을 먼저 완료한다. 이번 계획 수립은 프로토콜 변경이 아니다.

### 3.3 주문·보유 종료 조건

새 BUY가 완전히 닫힌 시점 이후, broker와 원 owner registry/상태를 같은 기준 시각으로 대사한다.

- 자동 ENTRY/ADD, 위젯 수동 BUY, 대기·예약 intent와 재시도까지 차단한다. 전송 직전에도 widget owner의 새 BUY를 거부해야 한다.
- 보호 SELL·cancel·체결 대사를 종료 전에 없애지 않는다. `enabled=false`가 전체 실행 루프를 멈춘다면 신규 BUY만 중지하는 전환 수단으로 사용하지 않는다.
- 미체결·부분체결·unknown/ambiguous 주문, 전일 이월 수량, adaptive/profit-stagnation 진행 상태를 포함해 widget-owned 노출을 확인한다.
- 계좌 전체 잔고와 widget-owned 수량을 혼동하지 않는다. Main/에피소드/manual 소유 수량은 종료 대상에 포함하지 않는다.
- 잔여 노출이 있으면 종료 상태는 `retired_with_residual_custody`다. 원 보호 경로로 종결하거나 명시적으로 지정된 owner에 exact 수량·주문·보호 책임을 인계하기 전까지 관련 manager를 삭제하지 않는다.
- 이번 계획은 청산 주문이나 강제 매도를 승인하지 않는다. 후속 실행 때 처분이 필요하면 종목·수량·미체결·보호 책임을 고정한 구체적인 처분안을 제시한다. 단순히 기록을 manual로 재분류해 flat으로 만들지 않는다.

전환 계약은 기존 lifecycle/owner 소유 경로에서 관리한다. `widget_retirement_transition_v1`에 실행 ID, 정확한 발효 시각, 대상 owner와 자동/수동 BUY 차단 범위, 적용 release/hash, 잔여 관리 책임자, 마지막 대사 generation, `freeze_buy / residual_custody / terminal` 상태를 고정하는 구현을 준비한다. 새 독립 매매 서비스는 만들지 않는다. 보호 manager는 기존 원 owner를 사용하며 위젯 삭제 이후에는 자동 복원할 수 없는 terminal 상태로 닫는다.

## 4. 구현·적용 순서

| 단계 | 작업 | 완료 증거 |
|---|---|---|
| W0 | 실행 시점 census·계약·snapshot 고정 | commit/dirty, selected/installed/PID, 진행 중 wrapper, timer/cron, 주문/custody, data/consumer manifest |
| W1 | 공통 코드 이관과 제거 코드 작성·리뷰 | 제거 후 Main/에피소드 import와 동일 입력 회귀 통과; staged 설정·uninstall diff 검토 |
| W2 | 신규 widget BUY·수동 BUY·정책 발행을 닫고 재진입 예약 차단 | 전송 직전 거부 테스트, 전환 receipt, 신규 BUY 0; 기존 SELL/reconcile 경로 보존 |
| W3 | 노출 종결·인계, 위젯 실행·collector 정지 | 잔여 widget 수량/미체결/ambiguity 0 또는 승인된 인계 receipt; 원 manager 책임 종료 |
| W4 | 코드·unit·장후·PREOPEN·감시·UI 연결을 동일 릴리스 계약으로 제거 | unit/cron/drop-in target 0, live import/dispatch 0, 새 날짜에서 widget 필수 의존성 0 |
| W5 | 증거 archive와 cache/data/log·Windows 설치 정리 | 파일별 정리 manifest, archive integrity, 보존 예외, 실제 Windows owner 확인 |
| W6 | 리뷰·회귀·다음 기동·장후 자연 결과 확인 | 아래 G0~G5 통과; 제거 후 Main/에피소드 정상 owner 유지 |

W0~W1의 코드·설정 검토와 targeted validation이 닫힌 뒤에 허용된 runtime 조치를 진행한다. 전환용 BUY 차단과 최종 삭제를 별도 배포해야 한다면 두 세대와 각 사용 시각을 기록한다. 기존 보호 경로가 필요한 동안 final 삭제 릴리스를 적용하지 않는다.

진행 중 장후 worker가 이전 코드를 소비하면 code/artifact를 덮어쓰지 않는다. 그 worker의 terminal 또는 명시적 중단 증거를 고정하고, 새 계약으로 새 실행 세대를 만든다. 과거 날짜의 완료 receipt를 새 날짜 제거 증거로 재라벨링하지 않는다.

## 5. 런타임·설치 제거 상세

### 5.1 위젯 전용 unit

아래 7개 service와 각 지정 timer가 기본 제거 대상이다.

- `korstockscan-widget-signal-auto-trader.service` + `.timer`
- `korstockscan-samsung-widget-collector.service`
- `korstockscan-doosan-widget-collector.service`
- `korstockscan-hanwha-ocean-widget-collector.service`
- `korstockscan-widget-symbol-runtime-collector.service` + `.timer`
- `korstockscan-widget-research-watch-collector.service` + `.timer`
- `korstockscan-samsung-widget-evaluation.service` + `.timer`

실행 직전 설치 목록을 다시 확인해 alias, 사용자 unit, 기존 expansion unit와 orphan drop-in도 분류한다. 재기동·timer 발동을 먼저 막고 W3 이후 전용 프로세스를 정지한다. unit·enable symlink·drop-in·installer/template를 제거하고 `daemon-reload` 후 등록/활성/예정 실행을 확인한다. `Restart=` 또는 deploy installer가 복원할 수 있는 경로도 닫는다.

공통 Gunicorn unit 전체를 없애지 않는다. `korstockscan-gunicorn-widget.conf` 및 실제 설치의 widget 환경/키만 분리하고 web 앱의 다른 API와 dashboard를 검증한다. router, symbol-owner installer, machine-additions/quantity/profit-stagnation 등의 widget 전용 drop-in과 서비스 allowlist를 함께 제거한다.

### 5.2 구독·REST·알림·외부 클라이언트

- `kiwoom_sniper_v2`의 boot widget observation 우선순위, `kiwoom_websocket`의 pinned observation/retained 분기 및 widget quote projection을 실제 소비자별로 제거한다. Main 고정 감시와 공통 realtime 파서는 보존한다.
- shared WS 함수는 위젯 전용만 삭제하고 공통 함수·상태 필드는 살아 있는 소비자와 동일성을 검증한 뒤 정리한다. 인증/token·공통 API 읽기 제어를 일괄 제거하지 않는다.
- price route와 manual order route 등록을 삭제하고 이전 endpoint가 주문 실행이나 계좌 조회를 발생시키지 않는지 확인한다. quote endpoint 제거만으로 manual order 제거가 완료됐다고 판단하지 않는다.
- widget 전용 Telegram 신호/진입/관측 발행을 제거한다. 공통 실제 체결 알림은 Main/에피소드 owner로 계속 동작해야 한다.
- Windows 프로세스·설치 위치·시작프로그램·Task Scheduler·shortcut·설정/키 사본을 운영자 PC에서 확인한다. 서버 census는 외부 PC 제거 증거가 아니다. 외부 확인 전에는 해당 범위 `not_observed`를 남긴다.

## 6. 장후·정책·검증 계약 제거 상세

1. `deploy/run_widget_evaluation.sh`와 평가 unit, `widget_policy` stage, stage code/source fingerprint, 필수 producer/terminal owner 목록, EOD wait/timeout/recovery/reuse 분기를 제거한다.
2. `machine_research_closed_loop_refresh --family widget`, widget candidate 등록·승계·runtime policy publish, version outcome projection, observation/catalog·expansion recommendation을 제거한다. Main/에피소드 실행이 widget source를 생성하거나 기다리지 않도록 한다.
3. `postclose_summary_handoff`의 widget owner와 machine `upstream_widget/refreshed_widget_sources` 의존성을 제거한다. machine refresh에서 실제 살아 있는 attribution/weakness/timing/episode 기능만 남긴다.
4. `postclose_done_controller`, 최종 wrapper, terminal gate, readiness/bootstrap, recommendation intake, tower/checklist/strict verifier가 공유하는 active stage/source/owner 계약을 같은 변경 세트에서 갱신한다. widget 보고서 부재가 신규 `source_gap`, OPEN 복구, timeout을 만들면 실패다.
5. 의미감시·artifact freshness·process health에서 widget 정책/collector/PID 필수 조건을 없앤다. Main/에피소드의 실패를 widget 제거 성공으로 덮지 않는다. 기존 baseline/override/expiry/custody 검사는 유지한다.
6. portfolio/allocation/market census는 widget denominator와 arm을 제외하고, owner별 미해결 과거 노출은 감사 입력으로 별도 보존한다. 과거 widget 수익을 에피소드 성과로 재귀속하지 않는다.
7. 실제 적용 시각을 `retired_from_at_kst`로 고정하고 새 active 계약 세대를 발행한다. 그 이후 날짜에는 widget 보고서/PREOPEN 승계/정책 복원을 허용하지 않는다. 과거 report/receipt와 그 schema/hash는 변경하지 않는다.
8. code/schema/input hash가 바뀐 stage는 새 세대로 검증한다. 수정 전 strict PASS나 prepared readiness를 그대로 사용하지 않는다. 새 strict → controller → PREOPEN 계약 순서로 닫고 자연 실행 증거는 따로 기록한다.

## 7. 데이터·디스크 정리

| 유형 | 처리 |
|---|---|
| 주문·체결·cancel·custody·수동 인계·운영 승인 원 증거 | hash-bound archive에 보존. 공통 registry/DB의 위젯 행을 일괄 삭제하지 않음 |
| widget runtime 정책·상태·관측 catalog·research candidate/version/approval | 소비자 종료와 archive 검증 후 active directory에서 제거. loader가 archive를 탐색하지 않아야 함 |
| widget raw/report/분봉/cache | Main/에피소드/감사 소비 census 후 분류. 공통 입력이면 재소유 또는 보존; 재현 가능한 전용 cache부터 삭제 |
| 임시 replay·benchmark·이중 보고서·전용 로그 | lock/open FD/활성 worker/보존 필요 확인 후 삭제; 삭제 bytes와 남은 사용량 기록 |
| 옛 release/worktree | 실제 PID·systemd·selector·rollback·외부 실행 참조가 없는 대상만 제거. 실행 중 릴리스와 보호된 복구본은 보존 |
| 키·env·Windows 설정 | widget 전용 사용처를 대사해 제거/폐기. 공통 Telegram·broker 토큰·web 인증은 유지 |

`widget*` wildcard로 data/release를 지우지 않는다. 삭제 manifest에 경로·bytes·hash·마지막 소비자·결정 사유를 기록한다. 보존·소유권·원천 재현 여부가 불명확하면 `retained_unverified`로 남긴다. 과거 증거 보존은 runtime widget 기능 잔존과 구분하며, archive를 새 튜닝·발행 입력으로 다시 읽지 않는다.

## 8. 문서·체크리스트·테스트 정리

후속 구현 변경 세트에는 Plan Rebase §5/§7/§8, 실제 관련 README/runbook/prompt/AGENTS 규칙, monitoring/postclose 지시문, traceability, Windows README, 설치·복구 문서를 목표 상태에 맞게 갱신하는 작업을 포함한다. 이번 계획 작성에서는 해당 운영 기준을 먼저 퇴역 상태로 바꾸지 않는다.

- 진행 중 widget-only OPEN은 실제 제거 시각에 퇴역 종결하고 재생성 규칙에서도 제외한다. 완료 연구 기록·과거 승인은 역사 증거로 보존한다.
- widget/episode 결합 OPEN은 에피소드 부분의 stable ID·Acceptance·Due를 유지한다. 위젯 항목을 없애며 에피소드 미완료 작업까지 완료 처리하지 않는다.
- 삭제된 widget 기능의 전용 테스트는 제거하고 공유·통합 테스트는 surviving owner 계약으로 보완한다.
- `analysis/benchmarks/widget_episode_completion_statistics.py`와 `widget_episode_incremental_scale.py`도 widget arm·입력·CLI를 제거하고 에피소드 부분의 필요 여부에 따라 재소유 또는 삭제한다. 수동 benchmark로 widget 생산자를 다시 실행하는 경로를 남기지 않는다.
- 새 테스트는 `src/tests`에 두고 위치 gate를 따른다. live imports, 주문·custody, 구독·원천, 장후 terminal, PREOPEN/감시, web 등록, 재설치 차단을 검증한다.
- 문서 변경마다 print-only backlog parser와 링크·owner·권한 검증을 수행한다. 외부 Project/Calendar sync는 실행하지 않는다.

## 9. 검증과 최종 종료 조건

| Gate | 통과 조건 |
|---|---|
| G0 소유권 종료 | 차단 이후 fresh broker/원장 대사에서 widget 신규 BUY 0, 잔여 수량·미체결·ambiguity 0 또는 정확한 승인 인계; 관리 책임 공백 0 |
| G1 운영 표면 제거 | widget 자동/수동 주문 진입점, collector/연구/알림 producer, installed unit/timer/cron/installer dispatch 0; 이전 web route 호출이 주문을 만들지 않음 |
| G2 장후 소비 제거 | 새 active contract의 widget stage/필수 source/terminal/PREOPEN/정책승계/추천/배분 0; widget 자료 없이 Main·에피소드 chain 검증 통과 |
| G3 공통 기능 보존 | Main 삼성 고정 감시·다른 종목 판정·에피소드 owner/quantity/custody/guard와 공통 비용·WS 계산 회귀 통과; import/동적 호출 실패 0 |
| G4 정리·외부 경계 | 삭제/보존 manifest와 archive integrity 완료; 실제 설치된 Windows client의 제거 또는 설치 없음 확인; 보호 release 참조 유실 0. 외부 미확인은 gate 대기 |
| G5 실제 실행 | 배포 뒤 widget 새 이벤트·보고서·구독·주문 발생 0, 정상 장후·다음 PREOPEN·Main/에피소드 실제 기동 receipt 확인 |

### 필수 검증 사례

- widget BUY/ADD 및 수동 주문 재호출은 거부되고 기존 부분체결 SELL/cancel 대사는 종결 전에 유지된다.
- 조사 후 새로운 체결이 생기면 stale flat receipt로 W3를 통과하지 않는다. owner 잠금·전송 직전 차단 뒤 snapshot을 재생성한다.
- 같은 종목의 Main/에피소드 보유·구독은 widget 제거에 따라 취소·해제되지 않는다.
- widget data 디렉터리가 없어도 Main/에피소드 import, EOD/장후/strict/controller/bootstrap와 감시기가 정상 동작한다. 다른 active source 결손은 계속 실패한다.
- 만료·옛 widget policy/archive/drop-in을 넣어도 active owner와 unit를 복원하지 않는다.
- 분리한 비용/집계가 같은 frozen 입력에서 이관 전 값과 같고 missing/censored를 0으로 바꾸지 않는다.
- 위젯을 제외한 active family 분모·hash·prepared generation을 검증하며 old PASS를 새 결과로 사용하지 않는다.

코드 변경은 구현 → self review → 수정 → 재리뷰 → targeted pytest/compile/bash 검증 → `git diff --check` 순서로 반복한다. 장후 재생성·배포·서비스 제어는 리뷰·대상 회귀 통과 후 허용된 단계에서 실행한다.

최종 종료는 G0~G5 모두 닫힌 때다. runtime만 제거했고 외부 Windows 확인이나 다음 자연 장후/기동이 남으면 각각 `external_not_observed` / `natural_acceptance_pending`으로 보고한다. 에피소드나 Main 오류, 미확정 custody가 남으면 해당 artifact·다음 조치·closure test를 명시하고 완료 처리하지 않는다.

## 10. 복구·재활성화 경계

공통 기능 회귀가 발생하면 Main/에피소드의 검증된 코드·설정을 복구하되 widget 신규 BUY 차단과 timer/installer 제거는 유지한다. 옛 릴리스 복구가 widget 실행을 함께 복원하지 않도록 배포·router·설치 acceptance에서 확인한다.

이번 제거 후 운영 계약에 widget 자동 재발견·승계·관측 복구 경로를 남기지 않는다. 과거 owner/schema를 읽는 감사 경로는 새 주문 권한이 없다. 현재 widget 정책을 다른 family 이름으로 바꾸어 존속시키지 않는다.

## 11. 계획 자체 검토

- 확인: 자동매매 외 수동 주문 API·Windows 클라이언트·collector·Telegram·연구·발행·stage·PREOPEN·감시·설치·cache까지 범위 포함.
- 보완: 공통 비용 import와 연구 집계, machine의 upstream widget terminal, 동적 owner 자동 적용, WS 같은 코드의 구독, 거래 날짜 rollover custody를 삭제 선행조건으로 분리.
- 검증 범위: 저장 코드·unit 설정·로컬 상태의 계획 검토다. broker flat, 실제 PID 정책 소비, 외부 PC, 제거 후 자연 기동/장후는 아직 검증하지 않았다.
- 완료 기록은 문서 parser·링크·stable owner·diff 검증 뒤 본 문서의 작성 결과로 남긴다. 제거 실행 완료나 runtime PASS로 표시하지 않는다.

## 12. 계획 작성 검증 결과

- self review → 보완 → 재리뷰: 수동 BUY 차단과 기존 SELL 보존을 분리했고, fresh 대사 이전 snapshot 재사용을 금지했다. 외부 Windows 미확인은 완료 gate 대기로 명시했다. 기존 격리 에피소드와 공통 비용·집계·WS·장후 terminal도 별도 처리했다.
- 문서 print-only parser: exit 0, parsed task 24개, 현재 `WidgetFullRetirement1006` owner 1개 확인. [parser 출력](../../tmp/widget-full-retirement-planning-20261006/backlog.txt).
- 로컬 문서 링크 검사: 오류 0. `git diff --check`: 통과.
- 이번 변경은 계획·체크리스트·조사 증빙이다. Python/runtime 코드를 수정하지 않아 pytest/compile/bash 검증·장후 재생성·배포·서비스 정지·broker API·주문·삭제는 실행하지 않았다. W0~W6 및 G0~G5는 후속 실행의 검증 대상이다.

## 13. 실행 진행과 잔여 acceptance

- 신규 widget BUY 차단 후 broker 잔고·미체결·당일 주문 완전조회가 정상 빈 결과였고, 원 registry의 과거 cancel 2건은 exact 과거 주문의 취소확인으로 terminal append했다. 새 매도·취소 주문은 실행하지 않았다.
- 전용 service/timer 11개를 중지·설치 제거 후 mask로 재기동을 차단했다. Gunicorn의 위젯 route 등록을 제거하고 이전 endpoint 404 및 다른 화면 200을 확인했다. Main/에피소드 서비스는 이 전환 중 재기동하지 않았다.
- 비용 계약과 에피소드 연구를 살아 있는 역할 package로 이관했다. Main 비동기 WS 저장 worker가 받은 에피소드 seed 원천을 기록하며 추가 API/구독은 없다. 기존 수량·cost·custody·hard safety를 보존해 최종 대상 회귀 3,382건과 compile/lint/bash 검증을 통과했다.
- Windows는 **설치되어 있으며 운영자가 직접 제거 예정**이다. 실제 제거 확인 전까지 G4 외부 경계는 대기다. 자연 장후·다음 Main/에피소드 실제 기동 증거도 G5 대기다.
- 실행 증거 위치: `tmp/widget-retirement-execution-20261006/`. 최종 리뷰·배포·정리 결과는 해당 manifest 및 후속 감사 기록에 적고 이전 PASS를 새 세대에 재사용하지 않는다.

- 최종 코드 커밋 `b53a3835`를 `widget-retired-20261006-b53a3835`로 배포했다. 설치 경로 13개, 에피소드 정책 pin 366개를 검증했고 웹 실제 PID를 대조했다. Main/에피소드 매매 프로세스는 재기동하지 않았다.
- 전용 데이터·연구 2,668파일과 임시 전환 릴리스를 archive 검증 후 정리했다. 정리 실행 전후 약 639MiB 확보. 과거 가격/주문 원천·공통 custody·에피소드 및 혼합 역사 receipt는 보존했다.
- 오늘 실제 Main/에피소드 정책 로더는 통과했다. 내일 dated 정책은 자연 장후에서 생성되어야 하며, 새 Main WS worker의 episode fact 소비와 정상 기동은 G5 대기다. [최종 실행 감사](../audits/widget-full-retirement-execution-review-2026-10-06.md).
