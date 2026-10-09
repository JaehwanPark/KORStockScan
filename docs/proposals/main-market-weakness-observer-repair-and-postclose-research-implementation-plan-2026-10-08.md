# Main 약세 관찰 결함 수리·기존 자료 장후 연결 연구 구현계획 — 2026-10-08

## 1. 목적과 승인 범위

사용자 지시에 따라 **관찰기 결함을 먼저 수리하고, 장중 로깅 없이 기존 자료를 장후에 연결하여 약세에 따른 Main 매매 조정 후보를 누적 연구**한다. 연결 정확도·표본 완전성을 일부 포기하더라도 장중 성능에 새 부담을 만들지 않는다. 충분히 일관된 조정 수치가 나오면 텔레그램으로 근거와 함께 안내한다.

이번 요청은 **구현계획 작성·리뷰**다. 이 문서 작성으로 코드 수리, 장후 재생성, cron 등록, provider 호출, 텔레그램 전송, 정책 발행, 배포·재기동을 실행하지 않는다. 아래 단계는 후속 구현의 실행 순서이며 별도 compact/지연 개선 작업에 주어진 승인을 이 기능에 전용하지 않는다.

- 현재 실행 인계 owner: [10/8 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `MainMarketWeaknessPostcloseObservation1008`. 기존 보조 튜닝·지연 개선 owner와 분리한다.
- 최우선 불변식: **새 장중 hook·로깅·메타데이터 필드·파일 읽기·해시 계산·큐·thread·daemon·REST/WS 구독·AI 호출을 추가하지 않는다.** 기존 trace를 더 자주/더 자세히 쓰거나 보존 정책을 장중에 바꾸는 것도 제외한다.
- P0 관찰기 수리는 기존 독립 관찰기의 잘못된 문구·상태 의미·검증을 고치는 범위다. 기존 실행 횟수·요청량·저장 횟수·원천 계약을 늘리지 않으며 Main/WS/AI hot path에 연결하지 않는다.
- 기계 목록·탐지·확인점·보조 입력/문구/응답·compact codec·운영 호출 수·주문/가격/수량·holding/exit·provider·bot state는 유지한다. 새 후단 live 평가도 만들지 않는다.
- 결과는 `decision_authority=postclose_research_advisory_only`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`다. 텔레그램 안내는 정책 적용·주문 권한이 아니다.
- 연구 판정은 현행 실제 ask·비용률 `0.0023`·1800초 이내 비용 후 `+0.4%`와 soft `−3%` 선도달의 W/F/U 및 누적 raw 승률을 따른다. 실제 손익·체결·경제성은 별도 표시한다. 기존 Main 채택에 EV·손익비·최소 일수/표본·holdout·제출 보존 gate를 추가하지 않는다.

## 2. 확인한 결함과 재사용 경로

| 대상 | 확인한 사실 | 계획상 처리 |
|---|---|---|
| [약세 notifier](../../src/engine/notify_panic_state_transition.py) | `_market_weakness_message`는 latch 활성만으로 퇴역한 위젯·에피소드 매수 차단·잔량 취소 문구를 출력한다. `next_state`도 `execution_bridge_runtime_effect=True`를 고정 기록한다. | **확정 P0**: 관찰과 실행 의미를 정정하고 과거 pending 문구 재전송도 차단한다. |
| [구 guard](../../src/engine/risk/market_weakness_entry_guard.py) | 지원 owner는 `episode`이고 Main 사용은 금지된다. 이전 검토에서 selected Main-only release의 실호출자가 없음을 확인했다. | 구현 착수 때 호출자를 재검증한다. owner를 Main으로 바꾸거나 취소 권한을 되살리지 않는다. |
| [약세 원천](../../src/engine/market_panic_breadth_collector.py) | `market_weakness_observations/<date>/`에 snapshot별 JSON을 저장한다. 점검한 10/8 원천에는 `as_of`가 있고 배포/가용 시각은 없다. | 기존 이력만 사용한다. 연구를 위해 관찰기 저장 필드를 늘리지 않는다. 실제 가용 시각 없는 연결은 근사 등급으로 표시한다. |
| 같은 원천의 `response_research_contract` | 현재 정적 계약에 `owner_isolation_required=[main, episode]`와 과거 delay/skip/exception arms·EV 계열 필수 결과가 남아 있다. | **확정 계약 잔재**: 원천 관찰값의 유효성과 구 연구 계약을 분리한다. 새 연구가 episode·구 arms·EV 채택 조건을 승계하지 않도록 기존 정적 문구/목록과 reader를 정정한다. |
| [상태 전이](../../src/engine/risk/market_weakness_state.py)·[hysteresis reader](../../src/engine/risk/market_weakness_threshold_policy.py) | 2/3회 기본값·최소 60초 간격·300초 신선도 계약과 날짜별 정책 계보가 있다. [퇴역 목록](../../src/engine/lifecycle/retirement.py)은 전용 hysteresis 튜닝을 포함한다. | 상태 전이 자체와 퇴역 보고서 의존성을 분리 검토한다. 새 tuning/publisher 복구 없이 관찰용 계약을 명시한다. |
| [기존 trace](../../src/engine/scalping/ai_decision_trace.py) | 판정 시각·기계/보조 결과·일부 native 소비 receipt가 있다. 10/8 점검 시 trace 파일은 약 378 MB였다. 이는 시점별 파일 크기이며 현재 성능 측정값이 아니다. | Main에 새 기록을 추가하지 않는다. 장후 streaming projection으로 필요한 작은 필드만 추출한다. |
| [기존 운용 장후](../../src/engine/scalping/continuous_reversal_operating_postclose.py) | 기계 comparison·snapshot object·정답/원천 hash를 보존한다. 호출 실행·정책 발행 함수도 같은 모듈에 있다. | 완료된 산출물/검증된 순수 reader만 소비한다. `calls`, `machine_report`, `auxiliary_report`를 재실행하여 원 연구나 정책을 덮지 않는다. |
| [stage/handoff](../../src/engine/automation/postclose_summary_handoff.py)·[controller](../../src/engine/automation/postclose_done_controller.py) | 날짜별 단계·완료 상태·최종 소비를 관리한다. | 새 연구는 독립 report-only owner로 연결한다. 퇴역 `market_weakness` 단계를 복원하지 않는다. |
| [Telegram manager](../../src/notify/telegram_manager.py) | import 시 bot/DB/event bus 초기화가 있다. | 장후 알림용 순수 발송 경계를 사용한다. Main manager import/기동이나 broadcast를 새로 만들지 않는다. |
| [기존 관찰 wrapper](../../deploy/run_panic_sell_defense_intraday.sh) | 기본 예약 호출은 release selector가 지정한 사본으로 이동한다. workspace 수정만으로 예약 소비가 바뀌지 않는다. | MW1 코드 검증·선택 release 반영·다음 자연 관찰을 따로 확인한다. 연구 설치 때문에 Main을 재기동하지 않는다. |

위 경로는 계획 검토 시 읽은 workspace 근거다. 후속 구현은 실제 selected release·현재 호출자·변경 파일을 다시 고정한다. [compact 도입](main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md), [지연 개선](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md), [기존 증분 저장 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)의 동시 변경을 덮어쓰지 않는다.

## 3. 실행 순서: 결함 수리 우선

| 단계 | 선행 조건 | 산출물·종료 조건 |
|---|---|---|
| MW0 기준 고정·P0 재현 | 후속 구현 착수 | 실제 observer/consumer/정책·release 경로, 재현 fixture, 변경 전 상태·문구 hash. 연구 코드 연결보다 먼저 수행 |
| MW1 관찰 결함 수리 | MW0 | 알림/상태/과거 pending·정적 연구 계약 정정, 회귀·재리뷰 통과. Main 경로·호출·저장 횟수 증가 0. 배치·자연 소비 증거는 별도 상태 |
| MW2 장후 원천 census·근사 연결 | MW1 코드 수리·검증 종료 | 원천 manifest, 연결 등급·결손 분모, 읽기 전용 증분 projection. 수리 전후 세대를 구분하며, 수리 전 유효 raw 관찰값은 근사 연구에만 사용하고 수리된 notifier의 자연 소비로 표시하지 않음 |
| MW3 일별·누적 연구 | MW2 | 동일 기회의 기계/보조 W/F/U·후보 수치·근사 민감도·불확실성. 원 연구 불변 |
| MW4 장후 자동화·운영 문서 | MW3와 자체 재실행 검증 | 야간 실행/자원 제한/중단·재개/날짜별 terminal·마지막 소비 연결 |
| MW5 텔레그램 후보 안내 | MW3의 안내 조건, MW4 | 관리자 전용 preview·중복 방지·전송 receipt·실패/불확실 전송 상태 |
| MW6 자연 수용 | MW1~MW5 검증 및 허용된 후속 배치 | 자연 장후 1회 전체 연결, 동일 원천 재실행 delta 0, 비적격 무발송, 첫 적격 후보의 실제 발송은 별도 관찰 |

### 3.1 MW1의 구체적 수리·회귀

1. 활성/해제 알림을 `시장 약세 관찰 활성/회복`, `매매 영향 없음`, `기존 자료의 장후 연구 대상`으로 정정한다. 아직 연구 단계가 설치되지 않았으면 연구 수행 중이라고 표시하지 않는다. 임계치·streak·breadth 수치를 임의 변경하지 않는다.
2. `execution_bridge_runtime_effect`는 false/retired 의미로 정정한다. 기존 source-only 필드와 모순되지 않게 하고 기존 version 필드가 있으면 의미 변경을 반영한다. 연구용 필드·새 저장을 추가하거나 역사 파일을 소급 수정하지 않는다.
3. 저장된 `pending_notification`에 구 실행 문구가 있으면 그대로 재발송하지 않는다. 공통 전송 진입점에서 확인하여 동일 snapshot·짧은 간격 재호출 분기도 빠뜨리지 않는다. 같은 날짜의 검증된 현행 관측·전이로 새 문구를 만들 수 있을 때만 재생성하고, 불가능하면 pending을 폐기한다. 기존 상태 저장 경로 안에서 처리하고 이행 전용 추가 쓰기/전송은 만들지 않는다. 현재 구현의 `sent_count`는 수신자별 receipt가 아니며 한 명 성공 후 pending을 지운다. 없는 부분 발송 이력을 복원하거나 exactly-once라고 주장하지 않고 기존 이력과 중복 판정을 보존한다. 새 장후 연구 outbox는 §9의 독립 계약을 따른다.
4. 이미 있는 코드로 시장별 독립 streak, 60초 미만 중복, 역순 관측, 날짜 전환, UNKNOWN, 원천 만료, 부분 회복·재약세, restart를 재현한다. **실제 실패가 확인된 경우에만** 수리한다. 현재 상태의 마지막 정상 latch와 현재 원천 health를 섞지 않고, stale/UNKNOWN을 새 약세 또는 회복으로 세지 않는다.
5. exact-date hysteresis 정책 부재를 이유로 퇴역 보고서·publisher를 재생성하지 않는다. 유효한 현재 관찰 정책/기존 기본값의 선택 이유를 기존 계약에 따라 보존한다. MW1은 활성/해제 수치를 경제적으로 튜닝하지 않는다. 같은 날 동일 임계치의 정책 출처만 바뀌는 경우와 실제 threshold 변경을 구분한다.
6. 알림의 KOSPI/KOSDAQ 범위와 aggregate breadth를 구분한다. 전체시장 지표로 양 시장을 지정하는 기존 판정 의미는 별도 검증하고, 표시 수리만으로 해당 판정 의미를 바꾸지 않는다.
7. `response_research_contract`의 퇴역 owner/arms를 현행 관찰 전용 의미로 정리한다. 새 연구의 후보·W/F/U 계약은 장후 manifest가 소유한다. 기존 `control`·권한 false·금지 용도 검증과 observation identity는 보존하며 `episode_entry_block` 같은 **금지 항목**은 삭제하지 않는다. 과거 snapshot은 수정하지 않고 read-only adapter가 구 계약 잔재를 표시한다. 정적 계약 정정 때문에 Kiwoom 요청/파서나 raw 판정·임계치·streak를 변경하지 않는다.

MW1 종료 보고는 코드/회귀 통과, 실제 예약이 선택하는 release, 다음 자연 관찰 문구·상태를 각각 기록한다. 연구 작업을 먼저 배치하거나 Main 매매에 연결하여 결함을 우회하지 않는다. 관찰기 수리 반영 전 자료의 사용 가능 여부는 원천 계약으로 판단하며 잘못된 실행 문구만을 이유로 유효한 raw snapshot 전체를 버리지 않는다.

## 4. 장중 성능 무추가 계약

연구 reader·집계·알림 모듈은 Main bot, WS callback, scanner, 기계 탐지, AI request/response, 주문 경로에서 import/call되지 않는다. **추가 metadata 몇 개, 비동기 queue, 저빈도 heartbeat라는 예외도 두지 않는다.** 기존 durable 주문/체결/필수 원천 기록은 유지한다.

관찰기의 기존 주기 외에 별도 장중 프로세스/재시도/폴링을 만들지 않는다. 시장 상태 연결은 저장된 시각을 사용하는 장후 as-of join으로 끝낸다. 자료가 부족하면 `approximate`, `unmatched`, `not_evaluated`, U로 남기며 이를 보완하기 위한 장중 수집 workorder를 자동 생성하지 않는다.

장후라는 명칭만으로 장중 영향이 없어지지 않는다. 16시대 regular 장후에도 NXT 등 Main 거래가 남을 수 있으므로 **모든 활성 거래 세션이 끝난 뒤에만** 새 디스크 scan·집계·전송을 실행한다. §8의 자원·시간 제한을 실행 코드에서도 적용한다. 성능 인수는 장중 추가 경로/작업 0이라는 구조 검증과 기존 성능계수 비교로 하며, 측정 없이 자연 성능 영향 0을 주장하지 않는다.

## 5. 기존 자료와 연결 정확도

### 5.1 원천 우선순위·모집단

장후 시작 시 `source_date`, 원천 cutoff, 원 producer 버전/완료 상태, read-only 경로·크기·세대/hash를 manifest로 고정한다. active release cwd와 공유 data anchor를 혼동하지 않는다.

1. 기존 `data/report/market_weakness_observations/<date>/`의 source-valid snapshot, 기존 observer 상태/로그에 **이미 존재하는** 관측 수용 증거.
2. 기존 기계 판정 trace·pipeline 및 완료된 운용 장후 comparison의 기회/정의/snapshot 참조. 실제 자연 판정과 사후 replay는 별도 `decision_origin`으로 보존한다.
3. 기존 AI request/response/trace의 실제 보조 결과·정확 버전. legacy/compact 논리 결과는 각각 검증된 decoder/reader로 읽고 새 provider 호출은 0회다.
4. 기존 정답 산출물·해당 시점 ask·이미 보관된 동일 item/route 가격 경로. 이미 계산된 유효 라벨을 우선 재사용한다. 그 외는 있는 범위만 장후 계산한다.

누적 범위는 현행 policy/source manifest의 더 좁은 유효 시작일을 따른다. clean baseline `2026-06-05`와 현재 forward 경계보다 이른 archive를 복원해 채우지 않는다. 최초 설치 전 자료도 **현재 적격·잔존·버전 확인이 되는 원천만** 제한된 장후 예산 안에서 사용하고 실제 포함 일수를 표시한다.

기계 ENTER_NOW·RECHECK·BLOCK, 보조 PASS·CAUTION·VETO·실패·미호출을 구분한다. AI 미호출은 VETO가 아니다. 기존 기계 비진입 기록에 유효 ask/결과 연결점이 없으면 판정 count만 집계하고 승률 모집단에 넣지 않는다. 전체시장/미감시 종목의 결과를 관측했다고 주장하지 않는다.

원천 census는 라벨 확인·AI 표본 선별 **이전**의 trace/기계 partition에서 시작한다. 기존 `prepare_inputs`는 UNRESOLVED를 제외한 실제 비교 요청 집합이므로 전체 기회 분모로 사용하지 않는다. `census → identity 유효 → 시장 연결 → 후보 조건 식별 → outcome 확인` 단계별 수와 제외 사유를 남기며, 저장 응답이 있는 집합만으로 원 기계/보조 전체 성능을 대표하지 않는다.

`canonical opportunity`가 있으면 원 ID를 보존한다. 없으면 검증된 trace/attempt/source stage로 별도 ID를 만들고 `identity_grade=trace_only`로 표시한다. 가까운 시각/가격이라는 이유로 서로 다른 기회를 합치지 않는다. 동일 기회의 여러 패턴·재평가·재시도는 원행을 남기되 outcome 단위로 중복 합산하지 않는다. identity 불명 자료는 집계 count와 추천 비교 모집단을 분리한다.

MW2는 다음 schema adapter를 먼저 고정한다. 존재하지 않는 공통 필드를 가정하거나 ID 종류를 서로 바꿔 쓰지 않는다.

| 입력 종류 | 확인할 실제 필드·의미 | 연결 실패 시 처리 |
|---|---|---|
| 자연 decision trace | 점검한 원행은 `stock_code`, `decision_trace_id`, `evaluation_attempt_id`, `decision_ts`, `source_event_stage`, `entry_mechanistic_action`, `entry_ai_risk_verdict`를 사용한다. `code/symbol`이 항상 존재한다고 가정하지 않는다. | 버전별 mapping을 검증하고 필수 필드 결손을 표시 |
| native 소비 receipt | `event_id/signal_id`, `snapshot_cutoff/read_at`, `captured_at`, machine/auxiliary/bundle hash, provider 상태는 서로 다른 증거다. | 원 trace와 exact binding 없으면 판정 시각·실제 AI 응답을 대신하지 못함 |
| 장후 comparison·정답 | 원 opportunity/snapshot/label 참조와 label 계약·ask·시각을 함께 검증한다. trace의 일반 target/outcome 필드가 이 연구의 30분 계약과 같다고 가정하지 않는다. | 계약 불일치는 U/미평가, 원 producer 재실행 금지 |

기계 확인 시각, 보조 응답 완료 시각, 실제 제출 시각을 한 `decision_ts`로 덮어쓰지 않는다. 보조 이후 보류 연구에서 응답 완료 시각이 없으면 기록된 결정 시각 기준의 사후 분류라고 범위를 제한한다. 늦게 생성된 feature를 이전 기계 확인점에 붙이지 않는다. 기존 timestamp의 timezone이 불명하면 KST로 추측하지 않고 제외한다.

### 5.2 정확도 등급과 허용 손실

| 등급 | 연결 방식 | 사용할 수 있는 판단 |
|---|---|---|
| A `observed_available` | 기존 receipt/log로 해당 시장 snapshot/latch가 판정 전에 사용 가능했음을 확인. 같은 날짜·상장시장·source/정책 버전과 시각 검증 | 당시 이용 가능했던 시장 정보에 따른 관측 비교. Main이 실제 소비했다는 뜻은 아님 |
| B `source_time_proxy` | `as_of <= decision_ts`인 가장 최근 유효 snapshot. 실제 배포시각 미보유. 기본 최대 age는 기존 신선도 계약 300초 | 사용자 허용 근사. 원천시각 기반 연구 추정이며 당시 가용성·인과 효과를 확정하지 않음 |
| C `bucket_proxy` | 판정 시각 자체가 기존 로그의 분 단위 bucket까지만 확인되면 **bucket 시작보다 늦지 않은** snapshot만 사용. 동일 300초 제한 | 분 단위 근사 통계. A/B와 분리하고 조정 수치 안내의 직접 근거로 사용하지 않음 |
| U `unmatched` | 날짜/상장시장/정책·원천 품질 불명, 300초 초과, 미래 snapshot만 존재, 잘린 원행/불명 시각 | 결손 분모. 정상·약세·회복이나 W/F로 대체하지 않음 |

KOSPI/KOSDAQ 상장시장은 이미 있는 검증 metadata로만 결정한다. KRX/NXT/SOR 실행 경로·PRE/REGULAR/AFTER와 다른 축이다. 상장시장 불명 시 추가 API 없이 unmatched 처리한다. PRE/AFTER에 정규장 마지막 상태를 TTL 이상 연장하지 않는다.

B 등급은 `availability_assumed=true`를 남긴다. 기본 join과 snapshot이 각각 60초/180초 늦게 가용해졌다고 가정한 지연 join을 함께 계산한다. 후보가 바뀌거나 개선 부호가 바뀌면 안내하지 않고 `join_sensitive`로 남긴다. 이미 알려진 source 지연이 180초를 넘는다면 이 근사 범위로 정당화하지 않고 해당 구간을 제외한다. 이 민감도는 실제 배포 지연 상한의 증명이 아니다.

각 지연 join은 원 `as_of` 기준 300초 age를 계속 적용하고 가정한 가용 시각이 결정 시각 이하여야 한다. 지연 조건마다 표본이 달라지면 세 조건 공통 기회에서 방향을 비교하고, 전체 eligible 분모·각 조건 탈락·공통 교집합 비율을 별도로 표시한다. 결손 때문에 약세 기회가 사라진 것을 후보의 성공적 보류로 세지 않는다.

raw snapshot으로 2/3회 latch를 재구성할 수는 있지만 notifier의 실제 누락/순서/재기동을 모두 알 수 없다. 이를 `reconstructed_latch`로 별도 보존하고 실제 수용 상태와 동일시하지 않는다. 관찰 버전·임계치 변경 지점에서 계보를 끊고, 판정 시각 뒤의 약세 확정/회복을 앞당겨 붙이지 않는다. frozen baseline snapshot이 있어도 과거 원천 손실은 복구된 것으로 표시하지 않는다.

### 5.3 정답·연구 오염 방지

- 원 보조 입력·문구·wire·응답·registry·기계 manifest·연구 membership/라벨은 변경하지 않는다. 새 연구는 작은 참조/파생 결과만 자체 namespace에 저장한다.
- 유효한 원 actual ask와 기존 라벨 계약이 없으면 비용 후 W/F를 만들지 않는다. 거래가 없던 관측의 가격 경로 결과는 CF 연구 결과이며 실제 fill/PnL이 아니다.
- 이미 보관된 완성봉은 기존 라벨 owner가 허용하는 범위에서만 사용한다. 동일 봉에서 목표/stop 순서가 불명하거나 필수 구간이 비면 U다. 선도달을 유리하게 추정하거나 미래 세션 가격으로 미완료 30분 경로를 채우지 않는다.
- W/F/U, full/partial fill, real/replay/CF, 비용 확정/미확정을 분리한다. `raw_win_rate = W / (W + F)`와 U·미연결·미평가 수를 함께 제시한다. 분모가 없으면 null이다.

## 6. 일별·누적 연구와 조정 후보 수치

### 6.1 먼저 계산할 관측값

동일 정책/보조 버전·symbol 또는 검증된 group·상장시장·세션·route별로 약세/회복/비약세/UNKNOWN을 분리한다. `NEAR_WEAKNESS_BOUNDARY`는 경계 상태로 따로 두며 회복/정상 대조군으로 자동 편입하지 않는다. 실제 latch·재구성 latch·단일 raw 상태도 서로 다른 classification kind다. 해당 시장의 index 하락률·industry/stock breadth·지속 관측 횟수와 join grade를 보존한다. aggregate 최대 breadth를 해당 시장의 값으로 전용하지 않는다.

기계 신호별 W/F/U, 보조 PASS 승률, 비PASS에서 놓친 W, PASS에서 남긴 F, 약세 시 차이를 계산한다. 같은 하락 구간의 반복 기회를 독립 시장 사건으로 세지 않도록 원 기회 수와 **거래일×연속 약세 구간 수**를 함께 표시한다. 약세·비약세 표본의 구성 차이를 드러내고 관측 차이를 인과 효과로 단정하지 않는다.

### 6.2 후보 생성·평가 범위

새 실시간 전략·새 AI 평가기는 만들지 않는다. 장후 작은 후보 manifest에 **무조정 baseline과 한 번에 한 조정점**을 고정한다.

1. **기계 후보**: 기존 등록 정의의 관측 가능한 숫자 조건 중 해당 owner가 `baseline_prior/bounded_tunable`로 분류하고 기존 원천으로 재평가할 수 있는 항목만 대상으로 한다. 원천/quote/account/quantity/cooldown/수동 veto/hard safety는 후보에서 제외한다. 조건의 단위·연산자·현행값·변경값·정확 scope를 기록한다. 수치 정의가 없는 scope는 `numeric_adjustment_unidentifiable`다.
2. **보조 이후 후보**: 실제 유효 PASS 기회에 한정하여, 이미 저장된 해당 시장 약세 강도와 종목 feature를 사용하는 조건부 추가 보류의 수치를 오프라인 평가한다. 예: `시장 하락률 <= x`이고 `기존 종목 지표 < y`일 때 보류. 기존 보조 PASS를 VETO로 덮어쓰지 않고 `research_overlay_disposition`으로만 계산한다. 여기서 보류는 이번 기회 제출 제외 CF이며 나중에 더 좋은 가격으로 매수했다고 가정하지 않는다. confidence·과거 numeric Score를 새 문턱으로 사용하지 않는다.
3. 기계 완화로 새로 포함되는 기회는 **기계 단독 CF**로만 계산한다. 원래 호출하지 않은 보조가 PASS할 것이라고 가정하지 않는다. 저장된 exact 요청/응답이 없으면 기계+보조 최종 개선은 `not_evaluated`다. 보조 비PASS를 PASS로 바꾼 성과도 새 실제 응답 없이 만들지 않는다.
4. 후보 생성 규칙은 결과를 보기 전에 config/hash로 고정한다. 지원되는 기존 값·단위 범위에서 이전 봉인 세대의 관측 feature 분포 25/50/75 분위값을 중복 제거해 제한된 cutpoint로 쓴다. 첫 세대는 후보를 고정하고 다음 자연 장후부터 비교한다. 기계 조건은 기존 허용 범위·방향·정밀도에 맞지 않는 분위값을 제외한다. scope당 baseline 외 최대 6개, cross-product 자동 확대 금지. 같은 세대 결과로 후보를 재탐색하지 않는다.
5. 후보를 변경하면 새 research version으로 비교한다. 재현 가능한 동일 기회/라벨에서만 baseline과 비교하고, missing row를 제거해 가짜 개선을 만들지 않는다. 후보가 일부 기회를 제외하는 효과와 입력 결손으로 비교에서 빠진 효과를 분리한다.
6. 조건 변경이 확인 시각·재무장·신호 union을 바꾸면 기존 확인점의 단순 필터로 그 효과를 주장하지 않는다. 이미 존재하는 충분한 normalized 원천과 순수 evaluator로 야간 예산 안에서 재현 가능할 때만 기계 단독 CF로 평가한다. 그렇지 않으면 `existing_confirmation_filter_cf`로 범위를 좁히거나 미식별 처리한다. 달라진 확인 ask에는 원래 라벨을 붙이지 않는다. 변경된 신호 union/입력에 원 보조 응답을 재사용하지 않는다.

수치 결과는 `scope / weakness_condition / adjustment_axis / before / after / unit / operator / candidate_version`, baseline·후보 W/F/U·raw 승률·Δ%p, 제외/추가 기회 수·놓친 W·제거한 F, join grade·범위·오차 민감도를 포함한다. 적격 기계 숫자 조건이 없으면 보조 이후 조건부 보류 후보만 낼 수 있으며 모든 scope에 억지로 두 종류를 만들지 않는다.

### 6.3 '충분히 유의미'한 안내 조건

아래는 **이번 연구의 Telegram 후보 안내 조건**이며 Main 기존 정책의 채택/기동 조건이 아니다. '충분히 유의미'는 아래의 자료 품질·반복 관측·방향 안정성을 통과한 **수치 조정 검토 후보**를 뜻한다. 통계적 유의수준 95% 달성이나 향후 개선 확정으로 안내하지 않는다. 수치 기준을 사후 완화해 발송하지 않는다.

- 추천 가능한 A/B·동일 outcome 계약에서 누적 paired 비교가 성립하고 `Δraw_win_rate > 0`이다. 후보 ranking은 raw 승률을 유지한다. 현행 유지가 가장 좋으면 유지로 기록하고 새 조정 알림은 보내지 않는다.
- 후보가 baseline과 실제로 다른 기회를 선택하고, W/F/U·coverage·놓친 W/제거한 F가 모두 산출된다. 분모 0·원천 충돌·조정값 미식별은 안내 불가다.
- 거래일 단위 paired cluster 재표집으로 baseline/후보를 **같은 추출 기회 집합**에서 계산한다. 후보 고정 뒤의 새 자연 자료에서 비교를 시작하며, 전체 누적 순위와 이 전향적 안내 평가창을 따로 표시한다. 아래 고정 예산에서 산출한 **경험적 하위 5% Δ**가 0보다 커야 한다. 군집 간 변동을 평가할 수 없거나 재표집 분모가 정의되지 않으면 `uncertainty_unresolved`다.
- 하루 또는 연속 약세 구간 하나를 제외하는 민감도에서 개선이 역전되지 않아야 한다. 데이터가 너무 얇아 계산할 수 없으면 관측을 계속한다. 고정 최소 거래일/표본 수를 별도 정책 gate로 추가하지 않는다.
- B 자료를 포함한 안내는 §5.2 지연 join에서도 동일 수치 후보의 개선 방향이 유지돼야 한다. 메시지에 `근사 연결 연구 추정`과 grade 비율을 반드시 쓴다. C·U를 정상 자료로 넣어 하한을 통과시키지 않는다.
- 조건/선택 여부를 식별할 수 있는 공통 기회 안에서 outcome U를 후보에 가장 불리하게 W/F로 배치한 민감도도 별도로 계산한다. 동일 기회의 라벨은 baseline과 후보에 동일하게 배치하며 이 경우 개선이 사라지면 `outcome_sensitive`로 관측을 계속한다. 이는 U를 실제 W/F로 바꾸는 집계가 아니다. 조건 자체 불명/미연결 자료는 이 계산으로 복구하지 않고 coverage 분모에 남긴다. 식별 가능한 결손 scope 때문에 다른 유효 scope 전체를 차단하지 않는다.

재표집은 **세대당 1,000회 고정**으로 하고 원 manifest·통계 버전의 deterministic seed와 거래일 추출열을 공유한다. baseline과 각 후보의 일별 W/F/U·선택 수를 먼저 한 번 집계한 뒤 작은 통계만 재표집한다. 매 반복마다 원 trace를 재읽거나 전체 joined 원행을 메모리에 올리지 않는다. scope의 선언 후보가 모두 비교되기 전에는 일부 결과만으로 해당 scope의 승자를 발송하지 않는다. 유효 반복 부족·분모 0·변동 평가 불가·자원 상한 도달 시 계산을 미완료로 남기며 반복 수/재시드/후보 수를 결과에 맞춰 늘리지 않는다. 동일 입력 재실행은 같은 결과다.

연구 원장에는 누적 관측 회차, 사전 고정 후보 전체와 실제 비교 수, seed·유효 반복 수를 보존한다. 초안의 무한 회차 alpha 배분과 작은 tail 추정은 제거한다. 회차/후보 증가에 따라 필요한 반복 수가 커져 야간 예산을 잠식할 수 있고, 단순 percentile bootstrap에 다중·반복 검정의 95% 보장을 붙일 수 없기 때문이다. **경험적 하위 5% Δ는 방향 안정성 진단이며 동시 신뢰하한/p-value가 아니다.** 같은 자료로 후보를 재탐색한 결과는 전향 비교로 표시하지 않는다.

자료가 한 날짜/약세 구간에 몰리거나 전부 같은 값이라 변동을 평가할 수 없으면 안정성을 입증한 것으로 처리하지 않는다. 가용 시각 부재·미감시 종목·누락된 약세 구간의 구조적 편향도 남는다. 기준 미달은 `hold_observation`, `uncertainty_unresolved`, `join_sensitive/outcome_sensitive/source_gap`이며 수익성 없음이나 조정 필요 없음으로 해석하지 않는다. 고정 최소 일수/표본·holdout을 기존 Main 정책 조건에 추가하지 않는다.

## 7. 저장·증분 처리

예정 출력 namespace는 `data/report/main_market_weakness_research/<source_date>/<generation>/`이며 `source_manifest.json`, 작은 `joined_observations` partition, `daily.json/md`, `candidate_comparison.json`, `terminal.json`을 둔다. 누적 manifest는 일별 불변 partition을 참조하며 원 trace·AI 본문·snapshot 복사본을 만들지 않는다.

- 기본 처리 key: 원 source identity/hash + source date + projection/join/label/research version. 요청 ID와 기회 ID는 원래 의미를 유지한다. research namespace 때문에 동일 요청을 다시 저장/호출하지 않는다.
- trace JSONL은 1회 streaming으로 필요한 열만 추출한다. 정상 newline offset까지만 읽고 미완성 tail은 다음 허용 야간 처리로 남긴다. 날짜/원천별 완료 offset·파일 identity·prefix 검증을 장후 원장에 기록한다. cutoff·읽기 전후 identity/크기/수정 상태와 읽은 범위의 digest를 묶고, cutoff 안의 rewrite를 검증할 수 없으면 해당 세대를 봉인하지 않는다. truncate/rotation/내용 변경은 영향 partition만 새 generation으로 재계산한다. 전체 과거 대용량 파일을 매일 재해시하지 않고 기존 producer 세대/manifest와 변경된 원천만 점검하며, 원천 삭제 후 재검증 불가도 명시한다.
- 큰 압축 원천은 매 후보마다 반복 scan하지 않는다. 필요한 해당 날짜 projection을 한 번 생성하고 공유한다. 원 라벨/선행 projection이 아직 없으면 기다리거나 결손을 기록하며 자동 full replay를 호출하지 않는다.
- 누적 갱신은 새 partition 또는 바뀐 라벨/원천 세대만 교체한다. 과거 generation은 불변으로 보존하고 current manifest를 원자 교체한다. 누적합에 구/신 세대를 동시에 더하지 않는다.
- crash 복구는 `partition 작성·검증 → manifest/cursor 함께 commit` 순서다. cursor만 앞서 저장해 원행을 건너뛰지 않으며 commit에 참조되지 않은 임시 partition은 합산하지 않는다. 부분 일자는 `in_progress`로 두고 완료된 것으로 누적/안내하지 않는다. 기존 완료 일자도 작은 선행 manifest의 세대 변경이 확인되면 영향 partition·누적·pending 안내를 무효화하여 재계산한다.
- 새 단계는 기존 AI shared store에 읽기 참조만 한다. 호출 예약·quota·원 비교 membership·정책 current를 쓰지 않는다. 필요한 읽기 snapshot이 잠겨 있으면 bounded defer하고 긴 read transaction으로 기존 writer를 막지 않는다.
- 보존 가능한 기존 근거가 없어진 partition은 `source_unavailable`로 남긴다. 기다리면 나올 미완료 원천과 영구 손실을 구분하고 후자는 source gap으로 닫아 같은 재처리를 무한 반복하지 않는다. 새 원천 재수집·archive 복원·장중 retention 변경으로 메우지 않는다. 향후 일반 retention과의 연결은 연구 manifest 참조를 읽는 **장후 범위**에서만 설계한다. 현재 누적을 원 근거로 검증할 수 없으면 과거 보고는 보존하되 새 적격 안내 근거로 재사용하지 않는다.

## 8. 장후 자동 실행·시간·자원 경계

### 8.1 실행 시점과 중단

정규장 종료 시점에는 시작하지 않는다. **기본 야간 시도는 매일 21:40 KST, 미완료 시 한 시간 간격으로 익일 05:40까지 최대 9회**의 별도 report-only 예약으로 한다. 현재 [controller cron installer](../../deploy/install_postclose_done_controller_cron.sh)는 평일 20:10 한 번 시작하므로, controller가 나중에도 살아 있거나 재호출될 것이라고 가정하지 않는다. 자정 전에 장후 작업이 끝나지 않는 경우도 처리하되 계속 충돌하면 다음 야간으로 이월하고 지연 일수/사유를 보고한다. 주말/휴일에는 이미 등록된 pending source date만 재개하고 새 거래일을 만들지 않는다. 실행 전에 저장소의 현재 거래일/세션 계약으로 모든 활성 시장 종료를 확인하고, 해당 source date의 필요한 원천이 안정된 상태인지 확인한다. source-date별 마지막 기회의 1800초 결과는 관측된 가격 범위로만 평가한다. 이미 장이 끝나 경로가 끊긴 기회는 다음 날 가격으로 완성하지 않는다.

첫 구현의 연구 예산은 `worker=1`, **한 야간 전체의 누적 실행 wall budget=10분**, `연구 프로세스 집합 메모리 상한=512MiB`로 시작한다. `night_id`는 해당 허용 창이 시작된 KST 날짜이며 자정 이후 시도도 전날 night_id를 쓴다. 최대 9회 시도·source date 교대·crash/재실행으로 예산을 초기화하지 않는다. 작업 전 실행 구간 예산을 예약하고 소비가 불명인 구간은 보수적으로 차감한다. 자원 선점 실패 시 무거운 입력 scan 없이 defer하며, 같은 야간 잔여 예산이 없으면 후속 예약은 작은 상태 확인만 하고 끝낸다. 원천 census·hash·projection·집계·통계·알림을 모두 이 예산에 포함한다.

기본 허용 창은 21:40~익일 06:30이며 실제 다음 Main 준비/거래 시작이 더 이르면 **그 준비 시작 전**으로 deadline을 줄인다. 이것은 작업의 최대 허용 경계이지 상시 실행/폴링 창이 아니다. 세션/준비 시각을 확인할 수 없거나 동시 EOD/정규 장후 owner가 자원을 점유하면 defer한다. wrapper supervisor가 wall/메모리 상한·deadline을 집행하고 자식 process group 전체를 종료·회수하며 제한 원인을 terminal에 남긴다. worker 단독 RSS 검사나 `nice`만으로 상한을 대신하지 않는다. 각 bounded chunk 시작과 전송 직전에 창을 다시 확인한다. 중간에 허용 상태가 바뀌어도 supervisor가 회수할 수 있어야 하며 장중으로 일을 넘기지 않는다.

서로 다른 작업의 '장후' 이름이나 단순 `nice`만으로 성능 무영향을 주장하지 않는다. CPU/I/O 예산·실행 창·단일 실행 lock을 모두 적용하고 야간 작업이 끝나지 않으면 다음 허용 창에 **원 source date/cursor**로 재개한다. 추가 장중 wakeup·polling은 없다. 5일/10일은 초기 검토 제안이며 자동 적용일/고정 표본 gate가 아니다. 일별 보고서가 매번 관측 일수·약세 사건 수를 표시한다.

### 8.2 현재 chain과의 연결

- 예정 CLI owner는 `src/engine/automation/main_market_weakness_research.py`, 순수 연결/집계 owner는 `src/engine/scalping/market_weakness_research.py`, 순수 알림/outbox owner는 `src/engine/automation/main_market_weakness_research_notify.py`다. 이들은 **아직 존재하지 않는 계획 경로**다. source/test 생성 시 역할·기존 유사 구현을 다시 확인하고 engine root 새 모듈은 만들지 않는다.
- 예정 wrapper `deploy/run_main_market_weakness_research_postclose.sh`와 [기존 운영 cron installer](../../deploy/install_stage2_ops_cron.sh)에 owner tag `MAIN_MARKET_WEAKNESS_RESEARCH_NIGHT` 한 개, 기본 `40 0-5,21-23 * * *` 한 줄을 등록한다. host cron의 timezone을 확인하고 실제 KST 슬롯을 검증한다. 설치 시 이미 알려진 더 이른 Main 준비 시각 이후 슬롯은 제외하고 실행 시에도 deadline을 재확인한다. installer 재실행은 해당 tag만 교체하며 다른 cron/퇴역 상태를 바꾸지 않는다. 현재 구현/설치된 것으로 표시하지 않는다. [release router](../../src/engine/infrastructure/runtime_release_router.py)의 검증된 selected release 실행 규칙을 연결하고 한 실행 중 release/code를 교체하지 않는다. root cron과 user cron, systemd 중 실제 등록 위치를 하나로 고정하며 이중 예약을 검사한다.
- router의 기존 `CRON_TARGETS`는 `REQUIRED_CRON_TARGETS`와 같으므로 여기에 연구를 단순 추가하지 않는다. 연구 실행 경로·설치 확인은 optional owner로 분리하여 미설치/OFF/지연이 기존 start/restart/PREOPEN의 필수 cron 검증 실패가 되지 않도록 한다. 연구의 비활성화/롤백은 자체 예약·보고 current에 한정하고 퇴역 consumer를 복원하지 않는다.
- `main_market_weakness_research`는 **별도 report-only catalog/terminal**로 두고, 현행 mandatory `STAGE_REGISTRY`에 단순 추가하지 않는다. 마지막 소비는 자체 야간 요약·notification disposition이다. 기존 controller/summary가 상태를 표시할 경우 그 실행 시점의 비차단 참고값으로만 읽고 strict/finalization 입력 hash·필수 완료 판정에는 넣지 않는다. 늦게 나온 연구 때문에 봉인된 controller/요약/과거 체크리스트를 다시 생성하지 않는다. 기존 main machine/auxiliary 정책 stage의 필수 선행 단계나 PREOPEN 후보로 넣지 않는다. 설치일부터 enabled 상태·스케줄을 명시하여 이전 날짜에 absent 실패를 소급 생성하지 않는다.
- scheduler는 설치일 이후의 완료 거래일에서 미처리 날짜와 영속 pending cursor를 장후에 대조한다. wall-clock 오늘만 처리하지 않으며 자정/휴일에도 저장한 source date를 유지한다. 야간 전체 10분 예산 내 현재 날짜와 오래된 pending을 번갈아 한 chunk씩 진행하여 한 결손 날짜가 후속 날짜를 영구 막지 않게 한다. 이미 완료된 **같은 원천 세대**에는 재계산/재전송하지 않으며 upstream 세대 변경은 §7에 따라 처리한다. 동일 namespace lock은 선점 실패 시 대기열 없이 종료한다.
- 입력은 해당 날짜의 **이미 안정된 cutoff까지의** trace/원천 및 사용 가능한 comparison/label 결과다. append-only trace 전체가 영구 종료되어야 한다고 요구하지 않는다. 기존 정책 단계가 실패했더라도 독립적으로 유효한 자연 trace는 별도 subset으로 분석할 수 있다. 아직 생성 중인 라벨만 pending으로 남기고, 선행 owner가 종료했거나 영구 손실이면 명시적 source gap으로 완료한다. 후일 새 세대가 나오면 영향 partition만 갱신한다. 결손 때문에 기존 producer·provider·정책 publisher를 실행하지 않는다.
- terminal은 `completed`, `valid_empty`, `completed_with_source_gaps`, `deferred_resource_or_window`, `failed_contract`를 구분한다. 계산 완료와 유의미한 후보 없음도 구분한다. 필요한 선행 원천이 아직 실행 중이면 bounded defer이며 이전 PASS를 재사용하지 않는다.
- 단계별 `source_date/run_id/code/source_manifest_sha256/daily_sha256/cumulative_sha256/candidate_sha256`를 봉인한다. 운영 요약/현재 owner는 이 stage의 상태를 참조한다. 연구 단계 실패는 해당 owner에 남기고 기존 Main 정책·기동을 차단하지 않는다. 전체 연구 완료를 주장하려면 terminal→누적→알림 disposition까지 검증한다.
- notifier 전송 receipt는 terminal/report의 source hash에 역으로 넣지 않는다. `원천→일별→누적→추천→알림 receipt` 단방향으로 두고 controller/verifier 자기 hash 순환을 만들지 않는다.
- 실제 controller/wrapper/cron을 변경하는 후속 구현에서는 [시간 운영 runbook](../time-based-operations-runbook.md)의 관련 observer/야간 실행 항목과 현재 checklist를 같은 변경 세트로 갱신할 범위를 인계한다. 현재 계획 작성에서는 baseline 문서를 수정하지 않는다. 기존 strict/PREOPEN 봉인은 최신 checklist 세대에 따라 기존 handoff owner가 재검증하며 과거 PASS를 현행으로 전용하지 않는다.

## 9. 텔레그램 안내 계약

사용자가 이번 계획에서 요구한 자동 안내 대상은 **누적 장후 결과에서 §6.3을 통과한 구체적인 조정 수치**다. 수신자는 기존 설정의 관리자이며 공개/broadcast 수신자 조회를 추가하지 않는다. 첫 구현은 장후에만 전송하고, 이번 문서 작성 중에는 preview·실발송을 수행하지 않는다.

예정 메시지 양식은 다음과 같다. 아래 값은 placeholder이며 실제 추천 수치가 아니다.

> Main 약세 대응 연구 — 조정 후보 발견 / 자동 적용 없음
>
> 대상: {상장시장·종목/정책·세션·route·현재 정책 버전}
>
> 약세 조건: {지수/breadth/지속 조건과 단위}
>
> 검토할 조정: {axis} {before} → {after} {unit}, {operator}
>
> 누적 비교: {기간}, {기회 수}, {거래일/약세 구간 수}, W/F/U {baseline} → {candidate}
>
> raw 승률: {before}% → {after}% (Δ {pp}%p), 재표집 경험적 하위 5% Δ {lower}%p
>
> 안정성: {날짜/약세 구간 제외·지연 join·outcome U 민감도}. 통계적 95% 보장을 뜻하지 않음.
>
> 제외/추가 기회 {counts}, 놓친 W {count}, 제거한 F {count}
>
> 근거 품질: {A/B 비율}, {근사 연결 여부·지연 민감도·결손}. 연구 추정이며 실제 체결/수익 보장이 아님.
>
> 보고서: {source_date/generation/경로 또는 설정된 접근 가능한 링크}, 후보 ID {id}

각 알림은 기계 단독 후보인지 실제 보조 PASS 이후 후보인지 명시한다. 수량·손절/트레일링·보유 매도 조정값으로 오해할 표현을 사용하지 않는다. 기존 요청에서 원한 '어느 정도 조정'은 위 before/after와 Δ로 답하고, 단순 약세 발견 알림을 추천 수치 안내로 대체하지 않는다.

### 9.1 전송·중복·정정

- 별도 research outbox의 `recommendation_id`는 관리자 scope + 대상 정책의 관련 parent/정의 + 약세 조건 + axis/before/after/unit/operator의 정규화된 **의미**로 만든다. report 날짜/hash, 실행 ID, formatter/research 코드 버전만 바뀌면 같은 ID다. 최초 적격, 실제 조정 조건/수치 변경, 근거 무효화/상태 변경 정정 때만 새 알림을 만든다. 동일 정책 scope에서 후보가 바뀌면 이전 후보를 명시적으로 superseded 처리하고 동시에 둘 다 현행 추천으로 남기지 않는다.
- `prepared → sending → sent`와 `failed_definite / delivery_uncertain / suppressed`를 영속화한다. 영속 outbox의 원자 claim 후 발송하며 모든 유형에서 원 receipt binding·야간 예산을 검증한다. **새 추천**은 현재 적격 candidate·봉인 hash와 이미 존재하는 현행 정책 자료의 해당 scope before/parent를 재검증한다. 정책이 바뀌었거나 확인할 수 없으면 `stale_parent`로 보류하고 역사 연구 결과로만 남긴다. **정정/철회**는 이전 sent receipt와 무효화/철회 사유를 검증하며 현재 후보의 적격성이나 옛 parent의 현행 유지를 요구하지 않는다. 현재 PID가 사용한다고 추정하지 않는다. Telegram 성공 응답의 message ID가 있어야 sent다. 실패를 성공으로 덮지 않는다.
- 명백한 미전송/429는 서버 지시와 야간 deadline 안에서만 bounded retry한다. 전송 후 timeout/crash처럼 전달 여부를 알 수 없으면 `delivery_uncertain`으로 남기고 자동 재전송하지 않는다. restart에서 receipt 없는 `sending`도 이 상태로 회수하며 claim 만료를 이유로 다시 보내지 않는다. 네트워크 API에서 exactly-once 수신을 보장한다고 주장하지 않는다.
- 이미 보낸 후보의 source가 무효화되면 오류 정정, 정상적인 새 자료 누적으로 적격성이 사라지면 관측 갱신/추천 철회로 구분한다. 이전 발송이 없으면 정정 메시지를 만들지 않는다. 알림 key는 recommendation ID + 전이 유형 + 이전 발송/효력 전이 ID이며 같은 전이를 재실행해도 한 번만 보낸다. 철회 뒤 동일 수치 재적격은 반복 알림 대신 보고서에만 갱신하고, 수치/조건이 실제 바뀔 때 새 후보를 안내한다. 과거 발송 근거·receipt를 소급 덮지 않고 실제 정책 rollback을 하지 않는다.
- 환경설정/수신자 누락·전송 실패는 연구 완료와 별도로 `notification_blocked`를 남긴다. 후보가 없으면 `not_eligible`가 정상 상태다. 자동 테스트는 fake transport만 사용하고 token·수신자 값을 출력하지 않는다.

## 10. 검증·완료 기준

| 범위 | 필수 검증 |
|---|---|
| 관찰 결함 | 모든 전이/상태 알림·저장 필드·legacy pending에 퇴역 실행 주장 0; duplicate/짧은 간격 재발송 분기 포함; 정적 연구 계약 잔재/기존 금지 항목 분리; 원 판정/호출·저장 cadence 보존; 결손/역순/부분 회복/restart·selected wrapper 소비 회귀 |
| 장중 무추가 | Main/WS/scanner/AI/order import/caller diff 0, 신규 장중 file/queue/thread/REST/AI/구독 0; observer 수리의 요청·저장 횟수 비증가 |
| 장후 join | A/B/C/U 분리, 실제 schema별 stock_code/ID/시각 mapping, 라벨 선별 전 census, 미래 snapshot 금지, 300초 경계, 분 bucket 시작, 정책 전환·상장시장/route 분리, 60/180초 공통 기회·결손 분모, 재구성 latch의 출처 표시 |
| 연구 | 기존 prompt/input/response/정책/원 연구 membership hash 불변, 실제/CF/미호출 분리, W/F/U·ask·비용·30분·동일 봉 순서 불명, 후보 범위/paired 분모/U 민감도, 1,000회 고정 재표집/군집 변동 불가/분모 0, 가짜 95% 보장 문구 0 |
| 자원·재실행 | 큰 fixture streaming, truncate/rotation/tail, process group 메모리·야간 총 wall budget·source lock defer, partition/cursor commit 중 crash, 원천 세대 교체/영구 손실, 동일 입력 delta 0, 다음 Main 준비 전에 자식까지 종료 |
| 자동화 | 21:40 defer 후 자정 이후 포함 최대 9회·합산 10분·예산 비초기화, KST/night_id/source-date 보존, OFF/설치 전/valid-empty/부족/실패/deferred 분리, optional cron·stage, 기존 strict/finalization/기동 비차단, 자체 야간 요약/알림 disposition 소비 |
| Telegram | 부적격 새 추천 0, 코드 버전만 달라져도 동일 수치 중복 0, stale parent 새 추천 보류, 원자 claim·sent에는 message ID, restart의 sending/모호한 전송 재시도 0, 현재 부적격이어도 원 sent/사유가 검증된 정정·철회 전이별 1회, 누락 설정·실패가 성공으로 표시되지 않음 |

후속 구현은 `구현→자체 리뷰→보완→재리뷰→관련 pytest/compile·wrapper bash -n·git diff --check→결과 보고`로 닫는다. 검증을 위한 broker/provider 실호출·실주문·장중 부하 실험·대규모 재보고를 수행하지 않는다. 자연 성능은 기존 계측을 읽어 전후 release/입력률/세션 차이를 함께 표시한다.

코드 종료, observer 배치, 자연 일별/누적 생성, 적격 후보 발견, Telegram 전달, 실제 매매 적용은 각각 다른 상태다. 이 계획의 완료에는 실제 매매 적용이 포함되지 않는다. 적격 후보가 아직 없으면 자동화 연결 검증을 완료할 수 있지만 '첫 유의미 후보 안내 완료'로 표시하지 않는다.

## 11. 계획 리뷰·문서 검증

초안 자체 리뷰에서 추가 장중 metadata/비동기 writer 예외를 제거했고, 원천시각과 실제 가용시각의 차이·C 등급 비추천·future join 금지·동일 원 연구 보존·새 보조 응답 추정 금지를 명시했다. 또한 정규장 종료 후에도 거래가 남는 시간, 큰 trace 반복 scan, notifier import 부작용, 퇴역 stage 복원, 모호한 Telegram 재전송과 source 무효화 정정을 보완했다.

이번 문서 변경은 로컬 링크, 계획/구현 권한, 현재 단일 owner, 기존 checklist AUTO 봉인 블록 보존, `git diff --check` 및 print-only backlog parser로 검증한다. 코드/매매 테스트·provider 호출·장후 실행·Telegram 발송·외부 Project/Calendar 동기화는 실행하지 않는다.

재리뷰에서 controller의 20:10 단발 예약을 확인하여 독립 21:40 예약·pending 재개를 명시했고, mandatory native stage에 연구를 추가해 Main 기동을 막는 경로를 제외했다. 기계 조건 변경의 확인시각/union 변화, 근사 구간의 경계 상태, 후보 반복 탐색과 반복 통계 점검의 불확실성도 보완했다.

초안 문서 검증 이력: 로컬 링크 18개 정상, print-only parser 22개 항목 중 새 stable ID의 현재 owner 1개, 기존 AUTO 블록 SHA256 보존, 기존 checklist 내용에 계획 인계만 추가한 것을 확인했다. 공백 검사 통과. 이는 계획 문서 검증이며 P0 수리·연구 자동화·Telegram 전달 완료 증거가 아니다.

### 11.1 사용자 요청에 따른 후속 리뷰·보완

| 발견한 계획 결함 | 반영한 보완 |
|---|---|
| 현 notifier에 없는 수신자별 부분 발송 receipt를 보존 가능한 것으로 서술하고, 원천의 퇴역 연구 계약 잔재를 누락 | MW1 공통 pending 전송 진입점·기존 sent_count 한계·정적 계약 수정/역사 보존·실제 selected wrapper 소비 분리 |
| generic trace 필드·확정 라벨/AI 표본만 사용하면 원 기회 분모와 시각이 잘못 연결될 수 있음 | 실제 stock_code/trace/attempt/receipt mapping, 라벨 선별 전 census, 결정/응답/제출 시각 분리, 지연 join의 공통 기회/결손 분모 |
| alpha 배분의 작은 tail과 무제한 재표집은 야간 예산을 초과하며 95% 보장을 과장할 수 있음 | 1,000회 고정 경험적 안정성 진단·U 민감도·사전 고정 후보·안내 문구 정정. 연구 안내와 정책 채택 조건 분리 |
| 21:40 단발 충돌·재실행 예산 reset·영구 손실 날짜 반복·worker OOM/자식 잔존 가능 | 21:40~05:40 최대 9회 합산 10분·영속 night_id/예산·감독 프로세스 회수·fair cursor·손실 종료·partition/cursor commit |
| router 필수 cron 추가나 늦은 summary 갱신이 Main 기동/봉인을 간접 차단할 수 있음 | optional 설치/검증·독립 마지막 소비, 기존 mandatory stage/strict/finalization 입력에서 분리 |
| 코드 버전/날짜로 같은 수치를 중복 안내하거나 옛 parent 추천을 현행처럼 발송할 수 있음 | 의미 기반 recommendation ID·현재 parent 확인·전송 claim/불확실 보존·정정/철회/후보 교체 구분 |

보완 후 문서 검증: 로컬 링크 20개 정상, print-only backlog 22개 중 `MainMarketWeaknessPostcloseObservation1008` owner 1개, 기존 AUTO 블록 SHA256 일치, 이번 인계 section 밖 checklist 바이트 보존, 공백 검사 통과. 계획/체크리스트 두 문서만 수정했으며 Python/거래 테스트·provider·장후 작업·예약 설치·Telegram 전송·외부 동기화는 실행하지 않았다. 후속 코드 구현에서 필수 검증을 통과하기 전에는 이 표를 실제 결함 수리 완료 증거로 사용하지 않는다.
