# 장중 생산자–장후 소비자 S6 수리 보고서 — S5-FIN-01 capacity→allocation

실행일: 2026-09-27 KST. 인계: [S5 전체 체인 보고서](./2026-09-27-intraday-postclose-handoff-S5.md) `S5-FIN-01`, [S6 첫 수리 보고서](./2026-09-27-intraday-postclose-handoff-S6.md) `S5-FIN-02`. 범위는 native capacity 원천의 **과거 날짜 재검증**과 첫 소비자 stage→allocation→summary/controller 차단 계약이다. 현재 파일·로그 대사와 격리 fixture 외에 정규 장후작업을 실행하지 않았다.

## 결정과 9/23 재현 증거

원인은 capacity report의 부재가 아니다. `postclose_summary_handoff.stage_commands('research_capacity', '2026-09-23', …)`가 `research_native_capacity_source --source-date 2026-09-23 --write`를 호출했고, 9/25 재시도에서 CLI가 **현재 거래일 20:05 이후 취득만 허용**하는 검사를 먼저 수행해 `argparse` exit 2를 냈다. [stage 로그](../../data/report/postclose_stage_terminal/2026-09-23/research_capacity.log)에도 `native source acquisition requires current completed date after 20:05 KST`가 두 번 남아 있다. 같은 원천일의 보존 파일은 원래 9/23 22:51 KST에 취득됐고, read-only 재검증에서 `complete`다. 따라서 9/25에 provider를 다시 호출하거나 9/23 원천을 새 잔고로 대체할 이유가 없다.

| 생산자→artifact→첫 소비자 | 보존된 세대·상태 | 현재 마지막 terminal |
| --- | --- | --- |
| native account 취득 → `data/runtime/machine_research_closed_loop/capacity_source_2026-09-23.json` | `complete`, source date 9/23, 원본 byte SHA `fa38391e45748d429e7233f884e6434f0a53a5860db3e740bfd2b0df21c96ea8`; 내부 `receipt_sha256=78f0a73017d262a08fce335fb41fb617f99114f8e041b849566aa9fdc633040e` | `research_capacity` run `254f207750424466a32d627679425201`: `failed`, exit 2, `command_exit:2`; terminal byte SHA `2052e9afebc5596869ce8658acb8a5d52ff46fcbed5dc642046d6e0446eb0e60` |
| 동일 producer의 `native_cash.json` + `native_inventory.json` → capacity 검증 | 원천일 9/23, 같은 producer PID·계좌 scope·시계; 각각 native SHA `166aab2404dfcf4da040f07273d3e93a989d0073bffa87b81296b9243d5afb1b` / `6142583b9130d7c328350b8b83bb4fcf17543f98ec482aaacd9ea4185ed01499`, 파일 byte SHA `d7c8898fd662472705f8ead17572a39579875818bcc8610f4f84e0e972d9adf9` / `ecac1e289a00123c6672c3b9f759048ce75168a4732b566555c8be1eb1f36faa` | 기존 마지막 capacity terminal은 실패 그대로 보존 |
| widget·episode·capacity terminal → `research_allocation` | 9/23 prerequisite byte SHA 각각 `7cf54f667313ccc0af55f4531a2384e66df5a5b1c09cd362e7c55a7ad84d6e96` / `a9b123b65c2bcb514344baa08597a4269025ee8982892e02a24a2b4fdb673ef7` / `2052e9afebc5596869ce8658acb8a5d52ff46fcbed5dc642046d6e0446eb0e60`; source date 동일 | run `1931beff0ab94c87a48ad9383a9f120c`: `deferred`, exit 75, `research_capacity:failed` |
| allocation 포함 14 stage → summary/controller | summary가 실패·보류 stage SHA를 입력으로 기록 | `summary_handoff` run `d6bfce76156e4972a61b0ccd3d8740ed`: `failed`, exit 1. 마지막 controller는 `blocked_independent_producer`, final verifier `not_run`이며 `research_allocation:deferred`, `research_capacity:failed`, 별도 `main_machine_policy:output_generation_changed`를 기록 |

`S4-OTH-03`의 episode 원천 69건(유효 66·격리 3)과 345/100 입력 ledger는 변경하지 않았다. 그것은 capacity exit 2의 원인이 아니며, source gap·격리·후보 0을 경제적 no-edge 또는 자동 OFF로 합치지 않는다. 9/24 recovery `DONE`, 12개 성공 stage, main wrapper 성공은 위 9/25 마지막 세대를 대신하지 않는다.

## 수리와 코드리뷰

- [`research_native_capacity_source.py`](../../src/engine/monitoring/research_native_capacity_source.py): 당일 20:05 이전·미래 날짜의 취득 차단은 유지한다. 과거 날짜는 **read-only** `validate_existing`으로만 처리한다. receipt 자체 SHA·source date·status·role·권한·요청 횟수, 현재 설정과 일치하는 계좌 scope, 두 native 파일의 SHA·같은 PID·venue scope·수량/현금 기본 계약·KST 날짜/30초 시계를 검사한다. 유효 `complete`만 exit 0, 부재·`source_gap`·손상·다른 날짜·다른 계좌는 exit 1이다. provider·인증·주문 호출이나 원천 재작성은 없다.
- [`postclose_summary_handoff.py`](../../src/engine/automation/postclose_summary_handoff.py): capacity stage는 취득 명령 이후 native cash/inventory의 **파일 byte SHA**를 `input_sources`에 묶고, 재검증 때 위 독립 원천 계약을 다시 확인한다. 이 stage의 새 receipt SHA를 allocation이 widget·episode prerequisite SHA와 함께 소비한다. native 파일이 바뀌면 capacity가 `input_generation_changed`이고 다음 allocation은 보류한다. 기존 실패/명시적 OFF와 다른 family의 입력 계약은 유지한다.
- 실패 회귀를 먼저 만들었을 때 9/23 fixture의 9/25 CLI 호출은 `SystemExit: 2`였다. 구현 후 같은 fixture는 provider 호출 0·exit 0이며, native 유효 빈 inventory도 유지한다. 별도 fixture는 `capacity failed → allocation deferred → controller blocked / verifier not_run → 새 capacity attempt succeeded → 동세대 allocation succeeded → native drift 후 allocation 재보류`를 검증하고 이전 attempt 파일을 보존한다. 수리된 두 stage는 controller blocker 목록에서 빠지지만 다른 독립 stage가 없으므로 전체 controller는 계속 차단된다. native 변조 뒤에는 두 stage가 다시 blocker로 나타난다.

자가 리뷰에서 테스트 경로가 함수 기본값에 고정되어 실제 자료를 읽던 결함을 발견해 명시적 directory 전달로 고쳤다. 이어 계좌 scope의 형식만 검사하면 다른 계좌의 보존 원천을 받아들일 수 있는 결함을 발견해 현재 설정과 정확히 비교하도록 고쳤다. 변조 receipt, 다른 날짜/계좌, native SHA·파일 부재·PID·시계, 완전한 `source_gap`, 당일 조기·미래 호출, OFF의 회귀를 추가해 재리뷰했다. **이 묶음의 미해결 코드 결함은 0**이다.

## 검증·성능·권한 인계

| 검증 | 결과 |
| --- | --- |
| 영향 pytest: `test_research_closed_loop.py`, `test_postclose_summary_handoff.py`, `test_postclose_done_controller.py` | **152 passed** |
| 변경 Python 파일 `py_compile`; `git diff --check` | 통과 |
| 9/23 현재 native 원천 read-only 검증 | `complete`; 10회 호출 0.157–2.230 ms, 평균 0.392 ms. 전체 장후 cold/warm 성능 판단은 S7 |
| wrapper `bash -n`·계약 | wrapper 변경 없음. 선택 릴리스·설치 스케줄·서비스 변경 없음 |

선택 릴리스 `integrated-workspace-20260927-fcc57536`는 이 **미배포 작업본 수리**를 포함하지 않으며 selector `actual_pid_consumed=false`다. 실제 9/23 capacity/allocation/summary terminal은 각각 `failed/deferred/failed`로 **그대로 남아 있다**. 수리 후 fixture 통과를 새 자연 attempt, strict pass, controller DONE, detector, 다음 PREOPEN/PID 또는 비용 후 성과로 승격하지 않는다. S5-FIN-01의 운영 체인 닫힘은 OPEN이다.

**S7 인계:** 승인된 별도 실행 범위에서 같은 clean 원천·고정 source date로 새 capacity→allocation→summary attempt와 입력/제외/출력 건수, cold/warm wall·CPU·RSS·I/O를 측정하고 `S5-FIN-03`의 stale strict/checklist와 다른 독립 결손을 분리한다. **S8 인계:** 검증된 릴리스 선택 후 자연 controller/strict/detector, PREOPEN 및 실제 PID 소비를 별도 영수증으로 확인한다. `S1-COM-01-A` scanner reader, SOR→KRX 작업본, SELL 경제성·episode family 수리는 이 묶음 밖에 남긴다. 실주문·정책·서비스·provider·threshold·정규 장후·PREOPEN·배포는 변경하거나 실행하지 않았다.
