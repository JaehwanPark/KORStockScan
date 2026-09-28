# S7 후속 — `S5-FIN-01` capacity→allocation 실제 stage 격리 실행 gate

실행일: **2026-09-28 KST**. 인계: [S7 통합 보고서](2026-09-28-intraday-postclose-handoff-S7.md), [S6 capacity→allocation 수리](2026-09-27-intraday-postclose-handoff-S6-S5-FIN-01.md), [직전 실제 reader 격리](2026-09-28-intraday-postclose-handoff-S7-S1-COM-02-A-actual-reader-isolation-gate.md). **판정: `research_capacity` 실제 stage 격리 실행 PASS; 원본 widget·episode 선행 영수증을 보존한 `research_allocation`은 `deferred(exit=75)`이며 본 계산·성능 gate는 BLOCKER.** 따라서 두 stage의 동세대 완료나 전체 체인 PASS는 선언하지 않는다.

## 1. 코드·원천·권한 경계

- 작업본 HEAD `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`에서 별도 `/tmp/kor_s7_capacity_allocation_20260928` root를 만들었다. `src` Python **1,056파일**을 복사하고 쓰기 권한을 제거했다. symlink **0**, Python 원천 경로+byte SHA 목록 digest `ff6c62410275fa6815353518e734aa50f45a65b2073e664e39f7e1c0da8685a6`. `postclose_summary_handoff.py` SHA `cb3dc30103a3396fcbbc26a77ff813165dccac65f339bdd05a50a25dd83ac6cb`, `research_native_capacity_source.py` SHA `6cc4cab97d8294d44614538505fe5dbfd65c23838de90e9f91b8aa512ecb7f9b`, `machine_research_closed_loop_refresh.py` SHA `aeb99af675457e4cf26531dd4cf4dfc2e8cf077fdee65e682dc305ec3fe4730a`는 종료 시 해당 작업본 파일과 같았다. 공유 작업본 전체는 다른 세션이 수정 중이므로 불변이라고 주장하지 않는다.
- 9/23 source date의 native capacity·cash·inventory, widget·episode terminal 및 직접 artifact/연구 보고서 등 **14파일·84,760,923 bytes**를 각 byte SHA 검증 후 복제했다. 파일 목록 SHA `af74a6f74be0ff83851e8e9329b11138073c45fc50a7c3d302b0f3766c34a972`. capacity source `fa38391e45748d429e7233f884e6434f0a53a5860db3e740bfd2b0df21c96ea8`, native cash `d7c8898fd662472705f8ead17572a39579875818bcc8610f4f84e0e972d9adf9`, inventory `ecac1e289a00123c6672c3b9f759048ce75168a4732b566555c8be1eb1f36faa`는 종료 시 운영 원본과 같다. 보존 widget·episode terminal byte SHA는 각각 `7cf54f667313ccc0af55f4531a2384e66df5a5b1c09cd362e7c55a7ad84d6e96`, `a9b123b65c2bcb514344baa08597a4269025ee8982892e02a24a2b4fdb673ef7`이다. 복제본 14파일은 모두 시작 SHA를 유지했다.
- 종료 대사 때 운영 원본 14개 중 **13개**는 시작 SHA와 같았다. 예외는 현재일 `data/runtime/widget_signal_auto_trade_state.json`이며, 복제본의 시작 SHA `d232a15886479cefeda35219e195d10b21678617084abfbe554c4307cfd0d43e`에서 운영 파일이 다른 SHA로 계속 갱신됐다. 이는 9/23 native 세 파일이나 보존 선행 terminal의 변경이 아니다. Allocation 입력의 전체 공유 작업본 불변성을 주장하지 않고, 복제본의 고정 세대만 이 실행의 근거로 삼는다.
- `PROJECT_ROOT/data`를 독립 root로 결속했다. `sitecustomize.py` SHA `b1db1fe7077dfe878999b4191ddce651ca659bf02ad69fc71b4c1f0a60314258`의 audit guard는 root 밖 쓰기, 운영 `src`·`data` 읽기, socket 생성·연결, 허용된 두 Python stage child 외의 subprocess를 거절한다. root 밖 쓰기·운영 파일 읽기·socket·임의 subprocess probe는 모두 거절됐다. `strace`의 capacity 실제 dispatcher+child **2개 trace**와 allocation 선행 검사 **1개 trace**에서 운영 `data` `openat=0`, `connect=0`; capacity는 Python stage child를 실행했고 allocation은 child를 실행하지 않았다. provider 요청·인증 갱신·실주문은 0이다.
- 실제 dispatch: `postclose_summary_handoff.run_stage`의 capacity 명령은 `src.engine.monitoring.research_native_capacity_source --source-date 2026-09-23 --write`, allocation 명령은 `src.engine.automation.machine_research_closed_loop_refresh --source-date 2026-09-23 --family allocation --write --source-wait-sec 0`이다. 과거 날짜 capacity CLI는 `validate_existing`으로만 진입하며 계좌 scope SHA, 원천 3파일 세대·PID·시각·요청 횟수를 확인했다. 독립 root에서 `complete`, receipt SHA `78f0a73017d262a08fce335fb41fb617f99114f8e041b849566aa9fdc633040e`였다. 계좌 key 값은 출력하거나 변경하지 않았다.

경로 대사: capacity 입력은 독립 root의 `data/runtime/machine_research_closed_loop/{capacity_source_2026-09-23.json,native_capacity/2026-09-23/native_cash.json,native_capacity/2026-09-23/native_inventory.json}`; 출력은 `data/report/postclose_stage_terminal/2026-09-23/research_capacity.{json,log,lock}`와 `attempts/`, 공통 자원 잠금은 `data/runtime/postclose_stage_slots/`이다. Allocation 선행 입력은 같은 root의 widget·episode·capacity stage terminal이다. 본 계산이 실행되면 두 연구 보고서 외에 widget state, research 후보·joint bundle, allocator, owner policy, 비교 비용·관측 결과, `machine_research_closed_loop` 보고서·`refresh` lock을 읽거나 쓸 수 있다. 이 후속 입력의 **완전한 동일 세대·경로 격리는 이번에 입증되지 않아** allocation child를 시작하지 않았다. 독립 root의 `data/config_dev.json`도 없으며 연구 보고서 reader import 시 설정 로드 실패 경고가 났다. 실제 provider 접속은 guard와 syscall 추적으로 차단·미관측이다.

## 2. 실제 stage 결과와 세대 차단

| 검사 | 격리 결과 | 판정 경계 |
| --- | --- | --- |
| Capacity producer→terminal | 실제 child의 과거 원천 재검증 성공. 마지막 새 run `33dc55348b944e47ae6b1c8c57adde76`, `succeeded(exit=0)`, receipt SHA `7fdbaaee3f54737c43b7b4387c72e541cd0786295d12dfc650747d5d26cf92c4`. 입력 native cash·inventory SHA가 위 원본과 같고 출력 capacity source SHA도 `fa38391e…` 그대로다. | 새 **격리** attempt만 성공. 운영 9/23 capacity 마지막 run `254f207750424466a32d627679425201`은 `failed(exit=2)`, byte SHA `2052e9afebc5596869ce8658acb8a5d52ff46fcbed5dc642046d6e0446eb0e60`로 유지. |
| Widget·episode→allocation prerequisite | 원본 byte 영수증 **각 1건**, capacity 새 영수증 1건이 allocation 선행 목록에 기록됐다. 현재 코드 검사는 widget·episode 각각 `code_changed`; 저장 코드 해시로 강제 검사해도 각각 `output_generation_changed`. 영수증 내부의 운영 절대경로가 독립 root 경로와 다르다. | 원본 영수증 byte를 수정해 적격으로 만들지 않았다. 이는 원본 연구 결과의 실패 판정이 아니라 **경로 재배치 후 원본 세대를 검증할 수 없는 격리 한계**다. |
| Allocation stage | 마지막 격리 run `e68f435d2abb4a4690be823ac67f2cbd`, `deferred(exit=75)`, issues `widget_policy:code_changed`, `episode_policy:code_changed`; receipt SHA `bffa0d935d34885f11f1ca282a1b053960605e9ad9c179864dcedd25ed99d6ac`. 본 계산 child, 후보 선택, 비용 복구와 정책 출판은 **미실행**. | 운영 마지막 run `1931beff0ab94c87a48ad9383a9f120c`도 `deferred(exit=75)`이지만 사유는 당시 `research_capacity:failed`였다. 두 보류를 동일 원인이나 같은 세대로 합치지 않는다. |
| 연구 보고서 read-only census | 복제 보고서 2개는 reader 계약상 missing 0. Widget 행 **100**, 그 보고서의 eligible 97·quarantined 3; episode profile **345**, 그 보고서의 eligible symbol 66·quarantined symbol 3. 각 profile mapping **445**, lifecycle `unaccounted_count=0`이다. | **읽을 수 있는 원천 분모**이지 allocation이 실제 소비·평가한 분모가 아니다. episode의 profile 345와 symbol 69=66+3을 합치지 않는다. |

Capacity 원천 파일 분모는 원본 3·검증 적격 3·제외 0·격리 0·미관측 0이다. Allocation은 선행 terminal 원본 **3건**을 관측했지만 이 격리 세대에서 유효 **1건(capacity)**·경로/코드 세대 미검증 **2건(widget·episode)**이어서 **본 계산의 원본·유효·제외·격리·미관측 행과 grid·holdout·비용은 `unobserved`/`null`**이다. 이를 적격 결과 0, no-edge 또는 의도된 OFF·valid-empty로 바꾸지 않는다.

독립 `stage_receipt_issues` 재검사 결과는 capacity `[]`, allocation `['research_allocation:deferred']`이다. Capacity의 stage 성공과 allocation의 소비 가능 여부를 분리한다.

9/23 운영 summary terminal은 `failed(exit=1, run=d6bfce76156e4972a61b0ccd3d8740ed)`, controller는 `blocked_independent_producer`, final verifier는 `not_run`이다. 이번에 summary/controller를 새로 실행하거나 과거 9/24 recovery `DONE`을 재사용하지 않았다. S6 fixture에서는 실패→allocation 보류→controller 차단, 수리 후 동세대 수용, native file drift→재보류를 별도 검증했고, 이번 영향 회귀 **10 passed**였다. Fixture 성공은 이번 원본 prerequisite을 동세대에 재배치했다는 증거가 아니다.

## 3. 재현 명령·자원 측정

독립 root를 `PYTHONPATH`·`TMPDIR`로 고정하고 `PYTHONDONTWRITEBYTECODE=1`을 사용했다. 아래 명령은 각각 별도 process로 두 번 측정했다. 기록은 `/tmp/kor_s7_capacity_allocation_20260928/{capacity,allocation}_{first,repeat}.{time,stdout}`이며 입력 복제·guard·syscall probe 기록도 같은 root에 있다.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kor_s7_capacity_allocation_20260928 \
TMPDIR=/tmp/kor_s7_capacity_allocation_20260928 \
/home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.automation.postclose_summary_handoff \
  --stage research_capacity --date 2026-09-23 --timeout-sec 30

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kor_s7_capacity_allocation_20260928 \
TMPDIR=/tmp/kor_s7_capacity_allocation_20260928 \
/home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.automation.postclose_summary_handoff \
  --stage research_allocation --date 2026-09-23 --timeout-sec 30
```

| 격리 명령 | 첫 회 wall / CPU(user+sys) | 반복 wall / CPU | 첫 회 / 반복 peak RSS | GNU time I/O inputs/outputs 첫 회 / 반복 | provider |
| --- | ---: | ---: | ---: | ---: | --- |
| Capacity **실제 stage+child** | 1.55 s / 0.50+0.05 s | 1.48 s / 0.49+0.05 s | 41,560 / 41,424 KiB | 7,864/48 · 0/40 | 연결 0 |
| Allocation **선행 검사만** | 0.44 s / 0.36+0.04 s | 0.40 s / 0.35+0.04 s | 41,540 / 41,756 KiB | 72/24 · 0/24 | child·연결 0 |

GNU time I/O는 원시 block 수치다. OS page cache와 공유 호스트 부하는 통제하지 않았으므로 엄격한 cold/warm 또는 운영 성능 개선으로 일반화하지 않는다. Allocation의 수치는 **평가 성능이 아닌 보류 gate 비용**이다. 수리 전후 두 코드 세대의 동일 입력 비교도 원본 prerequisite을 독립 root에서 재현하지 못해 `unmeasured_blocked`다.

## 4. 닫힘 검사·인계

1. `S5-FIN-01` / widget·episode stage owner: 운영 영수증은 원본 SHA로 보존하고, 독립 root에서 **새로운 명시적 path/세대 전이 영수증** 또는 동일 절대경로를 갖는 안전한 namespace로 widget·episode의 코드·출력·입력 SHA를 모두 검증하라. 단순 경로 문자열 재작성이나 저장 코드 해시 강제만으로 승인하지 마라. 그 뒤 같은 고정 9/23 원천의 새 capacity attempt→allocation 실제 child→출력·선행 SHA·원본/유효/격리 건수를 재측정하고 native file drift 시 보류를 확인하라. 격리할 수 없는 후속 파일·config/provider 경로가 남으면 실행하지 말고 해당 경로를 기록하라.
2. S7 전체 체인 owner: 위 gate가 닫힌 뒤 별도 범위에서 15 stage→summary→`whole_native_chain` strict→fresh controller·finalizer·detector의 동일 세대를 확인하라. 9/23 역사적 실패/보류, 과거 `main_terminal` PASS와 9/24 `DONE`은 현재 성공으로 승격하지 않는다. `S5-FIN-05`는 새 자연 장후 source date에서 재현할 때까지 별도다.
3. 이번 작업은 격리 root·보고서만 작성했다. 운영 capacity·allocation·summary terminal 및 native 원천의 SHA를 보존했고, 정규 장후작업·PREOPEN·배포·실주문·취소를 실행하지 않았으며 정책·수량·timeout·서비스·provider·threshold를 변경하지 않았다. 릴리스 선택·실제 PID·자연 terminal·비용 후 경제성은 S8에서 개별 수용한다.

자가 리뷰에서 원본 선행 receipt의 `code_changed`와 저장 코드 해시 검사에서도 남는 `output_generation_changed`를 구분했고, 그 영수증을 재작성하거나 allocation CLI를 stage 밖에서 직접 호출하지 않았다. 현재일 widget state의 운영 갱신을 복제 입력의 drift로 오인하지 않았으며 9/23 원천·terminal과 별개로 표시했다. 이번 범위의 미해결 **코드** 결함은 확인되지 않았으나 allocation 실제 child 격리·동세대 소비·성능은 열린 blocker다.

종료 검증: 보고서 상대 링크 **3개 유효**, trailing whitespace **0**, 복제 입력 **14/14 시작 SHA 유지**, 복제 `src` 쓰기 가능 파일 **0**, `git diff --check` **PASS**. `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` **PASS**, 현재 32 task 파싱. 영향 fixture pytest **10 passed**. 이번 repository 변경은 보고서 문서만이므로 Python compile·wrapper `bash -n`/계약 검사는 해당 없음이다. 외부 Project/Calendar 동기화는 실행하지 않았다.
