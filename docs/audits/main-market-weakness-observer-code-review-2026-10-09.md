# Main 약세 관찰기 코드 리뷰·결함 수리

2026-10-09 KST. 사용자가 확인한 기존 코드 리뷰·결함 보완 범위에 따라 [계획](../proposals/main-market-weakness-observer-repair-and-postclose-research-implementation-plan-2026-10-08.md)의 **기존 MW0–MW1 관찰기 코드**를 재현·리뷰·수리·재리뷰·검증했다. MW2–MW5 신규 장후 연구 코드는 아직 없으며 이번 결과를 전체 연구 구현 완료로 표시하지 않는다.

## 작업 기준과 소비 경계

- 시작 HEAD는 `23fde69cb6e808e3eb7eab4d5586248449c020c6`. 앞선 보유청산 작업의 dirty/untracked 34개 파일을 먼저 SHA256으로 고정했다. 그 소스·리뷰 문서는 그대로 보존했고 오늘 체크리스트에는 이번 목적과 stable owner만 추가했다.
- 확인한 selected release는 `main-integrated-bottlenecks-20261009-v1`, commit `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`. selector는 `actual_pid_consumed=false`, `awaiting_scheduled_main_start_20261012`다. 이번 변경은 workspace에 있으며 selector·서버 release·PID·기동 준비를 변경하지 않았다.
- 기존 독립 wrapper → panic report 안의 source-only observation → notifier의 source gate → 시장별 latch → pending 전달 → observer health 저장을 대조했다. 기존 wrapper의 selected release 이동·flock·예약/요청 cadence는 그대로다.
- [구 entry guard](../../src/engine/risk/market_weakness_entry_guard.py)는 episode-only이고 Main 사용을 금지한다. 현재 `src/engine`의 호출자 검색에는 정의 외 실행 호출자가 없다. 이를 Main guard로 바꾸거나 퇴역 executor를 복원하지 않았다. REST receipt의 기존 `request_priority_reason` 이름도 실제 guard 활성 증거로 사용하지 않는다.
- 현행 owner는 [10/9 checklist](../checklists/2026-10-09-stage2-todo-checklist.md)의 `MainMarketWeaknessPostcloseObservation1008` 한 개다. 10/8의 stable ID·Acceptance를 인계했고 과거 봉인과 미래 10/12 checklist는 수정하지 않았다.

## 재현·반복 보완

| 발견 | 수정과 회귀 |
|---|---|
| 알림이 퇴역 widget/episode 매수 차단·잔량 취소를 주장하고 `execution_bridge_runtime_effect=true`를 기록 | 모든 약세 알림을 관찰 활성/회복/범위/상태와 매매 영향 없음으로 정정했다. 새 상태와 기존 health 저장에서 실행 flag를 false로 고정한다. |
| duplicate·60초 미만 분기는 새 formatter를 거치지 않고 저장된 legacy 문구를 재전송 | 공통 pending 전달 진입점에서 현재 source gate·같은 날짜·관측 시간·기존 검증 latch·전이/phase를 검증하고 문구를 재생성한다. invalid/malformed pending은 설정/transport 조회 전에 폐기한다. 아직 latch에 수용되지 않은 관측은 상태 안내로 낮춰 옛 활성/회복 전이를 현재 증거처럼 보내지 않는다. |
| 원천/정책/역순/report 검증 실패 뒤 옛 pending이 남을 수 있음 | 기존 health 저장 1회 안에서 pending을 폐기한다. 시장 latch, 마지막 정상 관측 시각/ID, 기존 발송 이력은 보존한다. 추가 migration 저장이나 새 상태 파일은 없다. |
| UTC host가 naive KST report 시각을 UTC로 해석해 유효 observation과 9시간 lag를 생성 | local report 시각에 KST를 부여한다. aware 시각은 유지하며 UTC host fixture로 검증했다. 정상 관측 TTL의 300초/301초와 미래 skew −30초/−31초도 검증했다. |
| 정적 `response_research_contract`에 episode·구 arms·EV 필수 결과가 남음 | 신규 관측의 기존 필드에 `source_only_observation_no_execution_bridge`와 빈 owner/arms/outcomes를 명시한다. 새 계약에서 구 목록을 섞으면 거부한다. 역사 정적 metadata와 원천 ID는 보존하고 `episode_entry_block` 등 금지 목록은 유지한다. 신규 연구가 설치/실행 중이라는 주장을 만들지 않는다. |
| TTL 회귀가 삭제된 `machine_market_weakness_response` 모듈을 import | 퇴역 모듈을 복원하지 않고 실제 독립 관찰기의 latch/last-healthy와 현재 순수 freshness 계약을 검증하도록 교체했다. |

초기 새 결함 재현 5건은 수정 전 모두 실패했다. 첫 전체 관련 회귀에서 위 stale import와 3개 구 문구 assertion도 발견하여 수정했다. 이후 기본 78건, 확장 160건이 통과했고 마지막 malformed market 표시 보완 후 같은 확장 세트 **161건이 통과**했다. 이 숫자는 거래 수·연구 승률·경제적 성과가 아니다.

## 검증 근거

- [최종 pytest 로그](../../tmp/market-weakness-code-review-20261009/pytest-final.log): **161 passed / 2.76초**. notifier, breadth source, 구 guard의 Main 금지 계약, panic report/state detector, wrapper, engine location gate를 검증했다. 모두 로컬 fixture/fake transport이며 실제 Telegram·provider·broker 호출은 없다.
- [구조 리뷰](../../tmp/market-weakness-code-review-20261009/structural-review.json): source의 변경 함수는 observation builder와 source 계약 validator뿐이다. Kiwoom 요청/응답 parser·REST fetch·원천 ID 계산 및 module import가 불변이다. 상태 전이·hysteresis reader·구 guard·wrapper도 바이트가 불변이다. 요청/인증/FID/REG/REMOVE/continuation을 변경하지 않았으므로 공식 API protocol 변경 gate를 실행할 변경은 없다.
- 새 Main/WS/scanner/AI/order hook·import·thread·파일/큐·provider 호출을 만들지 않았다. 기존 전달+health 저장 2회와 실패 health 저장 1회 경로에서 migration으로 쓰기가 늘지 않는 회귀를 추가했다. 자연 latency·요청량 개선을 측정한 결과는 아니다.
- 변경 Python 4개 compile, 기존 wrapper `bash -n`, `git diff --check` 통과. [print-only parser](../../tmp/market-weakness-code-review-20261009/backlog.log) exit 0, backlog 22개 중 현재 owner는 오늘 checklist에 1개다. Project/Calendar 동기화나 token 조회는 하지 않았다.
- 시작 dirty 34개에서 오늘 checklist의 목적·owner 추가 외 바이트 변경 0. 미래 10/12 checklist SHA256은 `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9`로 유지했다. 수정 문서 로컬 링크 33개 모두 정상이다.

## 완료와 후속 인계

검토 범위의 코드 지적을 수리하고 재검증했다. 현재 알림은 단순 source-only 상태 관찰이며 구 전송 코드의 `sent_count`를 수신자별 receipt·exactly-once 전달로 주장하지 않는다. 실패/불확실 전달의 새 연구 outbox는 MW5 후속 계약이다.

배포·재기동·다음 자연 observer 소비, MW2 census/join, MW3 일별/누적 연구, MW4 optional 야간 예약, MW5 후보 안내 및 MW6 자연 수용은 이번에 수행하지 않았다. 대규모 보고서 재생성·실호출·운영 성능 실험도 생략했다. 기존 정책의 승률·EV·매매 안전성 개선이나 실제 매매 적용을 이 코드 검증으로 증명하지 않는다.
