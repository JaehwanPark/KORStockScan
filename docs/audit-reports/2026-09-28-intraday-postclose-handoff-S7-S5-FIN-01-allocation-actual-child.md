# S7 후속 — `S5-FIN-01` 선행 영수증 재생성→allocation 실제 child 격리 gate

실행일: **2026-09-28 KST**. 인계: [선행 영수증 S6](2026-09-28-intraday-postclose-handoff-S6-S5-FIN-01-prerequisite-generation.md), [capacity→allocation S7](2026-09-28-intraday-postclose-handoff-S7-S5-FIN-01.md). **판정: BLOCKER.** 동일 절대경로의 격리 namespace에서 현재 코드로 새 `widget_policy` attempt를 실행했으나, 이미 존재하는 9/28 정책 세대의 당일 갱신이 07:30 KST 이후 금지되어 `research_same_date_publication_conflict`로 실패했다. `episode_policy` 새 attempt와 `research_allocation` 실제 child는 선행 계약을 충족하지 못해 실행하지 않았다. 이 결과는 코드 결손이나 경제성 0의 증거가 아니다.

## 1. 입력·코드 세대와 격리 경계

- 작업본 HEAD `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`의 당시 `src`·`deploy`와 9/23 원천/정책을 `/tmp/kor_s7_allocation_actual_child_20260928`에 **3,476개 파일·1,499,690,841 bytes**로 복제했다. 복제 입력 목록 SHA는 `c877d0a9670d873b3617a9869d75ada0facfdb3d129cf3b1825c1285f8d34cd1`이다. 원본 9/23 직접 입력 14개는 [직전 S7 고정 목록](2026-09-28-intraday-postclose-handoff-S7-S5-FIN-01.md)에서 byte SHA를 재검증해 복제했다. 코드는 미커밋 작업본의 **파일별 snapshot**이며 선택 릴리스나 PID 코드라는 주장은 하지 않는다. 복제 `src`·`deploy` 파일은 쓰기 권한을 제거했다.
- 복제 원천의 `widget_signal_auto_trade_state.json` SHA는 `d232a15886479cefeda35219e195d10b21678617084abfbe554c4307cfd0d43e`로 고정했다. 9/23 native capacity·cash·inventory SHA는 직전 S7 보고서와 같다. 현재일 운영 widget state가 이후 갱신돼도 이 복제 입력에 섞이지 않는다. 9/23 완료 연구 reader는 widget **100 symbol**, episode **345 profile**, missing family **0**을 읽었다. 직전 보고서의 widget eligible 97·quarantined 3과 episode eligible symbol 66·quarantined symbol 3은 각각 다른 단위의 읽기 전용 분모이며, 이번 새 stage의 평가/주문 완료 건수가 아니다.
- `postgres:15` 로컬 이미지 `sha256:c635fa3e3b7421a659d34abdfd6d492f679cbe8149e261a501237b55c5a94212`의 일회성 container에 **복제 root만** 운영 절대경로 `/home/ubuntu/KORStockScan`로 mount했다. 호스트 `/usr`와 `.venv`는 읽기 전용이다. `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000`과 별도 audit hook으로 복제 `data`·`tmp` 밖 쓰기, 임의 child, socket 생성을 차단했다. guard probe의 source write·socket·임의 subprocess 거절과 복제 `tmp` 쓰기 수용은 모두 PASS다. 운영 source/data는 mount하지 않았고 provider 연결은 발생하지 않았다.
- 실제 복구 명령은 `postclose_summary_handoff --stage widget_policy --date 2026-09-23 --recover-closed-target --timeout-sec 180`이며 child는 `machine_research_closed_loop_refresh --source-date 2026-09-23 --family widget --write --source-wait-sec 0`이다. 정규 wrapper·전체 장후작업·PREOPEN은 호출하지 않았다.

## 2. 단계별 관측과 차단 원인

| 단계 | 격리 관측 | 판정 |
| --- | --- | --- |
| 입력과 과거 영수증 | `read_studies` missing `[]`; source date 9/23→publication 9/23→effective 9/28. 원본 widget·episode 영수증은 현재 코드에서 각각 `code_changed`. | 과거 두 영수증을 새 세대로 재사용하지 않음. |
| 첫 widget attempt | 격리 audit hook이 이미 열린 lock file descriptor의 `fdopen`을 새 경로 쓰기로 잘못 분류했다. run `631bf3219f6848b89ce2981d38dabf5a` `failed(exit=1)`. audit hook을 수정하고 차단 probe를 재통과시켰다. | 검증 도구의 false positive; repository 코드 결손으로 계산하지 않음. |
| 재시도 widget child | run `6d4b5a7b236b482ab6718afa7c3bfec7`, terminal `failed(exit=1)`, SHA `d51ee4f8a1b4d84131f972de4a4ce4a811b40aedafcb07e69b4171103484369a`. child는 정책 출판에서 `research_same_date_publication_conflict`를 발생시켰다. 정책 SHA는 새로 발행되지 않았다. | **실제 계약 차단.** 9/28 13:51 KST에 `_publication_update_allowed(2026-09-28)=False`. |
| episode | 복제본에 원본 9/28 publication manifest가 있고 hash가 유효하다. 동일 경로·시각에 episode와 widget의 `future_publication_parent`는 모두 `None`이다. episode의 과거 9/28 정책은 9/24 생성본이다. | 새 attempt **미실행**. 정책을 재작성/삭제해 갱신 금지를 우회하지 않음. 새 payload의 성공·실패는 미관측. |
| capacity→allocation | 이번 namespace에서 새 capacity는 미실행. 직전 S7의 별도 격리 capacity 성공을 이번 세대의 terminal로 재사용하지 않았다. 새 widget·episode 영수증이 없어 allocation child도 **미실행**. | allocation 입력·출력 SHA, 후보 grid·holdout·비용, cold/warm CPU·RSS·I/O 모두 `unobserved`/`null`. |

[`research_closed_loop.py`](../../src/engine/monitoring/research_closed_loop.py)의 `_publication_update_allowed`는 effective date가 오늘이면 07:30 KST 이후 갱신을 거절한다. widget 정책의 기존 9/28 manifest generation은 `2bc8319eff95752f52abaad2309d52ecc795b9968d23f4906a80dc499dab7462`, episode는 `38acbd1aa227cf04c809791f4a930ca812914d335ac181bc66fe5529a1e39b65`이다. 원본 두 publication manifest와 정책 파일 SHA는 복제본과 운영본에서 각각 같았다. 기존 9/28 정책을 복제 root에서 지워 새 정책이 없는 세계를 만들거나 시스템 시각·effective date를 바꾸면 **동일 입력·동일 평가 범위의 실제 gate**를 검사할 수 없으므로 하지 않았다.

복제 입력 3,476개를 실행 후 대사하니 바뀐 것은 **격리 `widget_policy` terminal과 widget 연구 JSON 두 파일뿐**이었다. 새로 생긴 것은 격리 stage attempt/log/lock, widget 연구 Markdown, `joint_inputs_widget_2026-09-23.json`, 연구 writer lock 등 8파일이다. 연구 JSON은 새 family refresh가 정책 출판에 앞서 다시 쓴 것으로 SHA가 원본 `d1485934fd38d4944e6cfa5d86e84ae3f62f1c8b897c720230869b6be0277bcf`에서 격리 `93e24a02ab5aa2a816f5d803ed70561cb48f11d0fc5b8786027ef880fabcacab`로 바뀌었다. **이 격리 root는 이후 새 시도의 clean 원천으로 재사용하면 안 된다.** 복제 코드·기존 9/28 정책·native 원천은 변경되지 않았다.

## 3. 재현·자원·닫힘 검사

복제 입력 목록과 guard/preflight 스크립트는 위 `/tmp` root에 남겼다. `preflight.py` SHA `972aa0eb5faff3b54bc81efc6be61d60d21ef467c7af8a064c396b70cbf48ae2`, 수정 후 audit hook SHA `fde4cae32d32dc6175ff2ddd7cc3614f23aca81d2b21feae790ac261be25615e`, `date_guard_preflight.py` SHA `ad9f4073a338c68fb3eae3b605b7d0b162cceb0530aa149b95a9d06ace890445`다. 같은 경로 namespace의 핵심 재현 명령은 다음과 같다.

```bash
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 1000:1000 --memory 4g --pids-limit 128 \
  --mount type=bind,source=/usr,target=/usr,readonly \
  --mount type=bind,source=/tmp/kor_s7_allocation_actual_child_20260928,target=/home/ubuntu/KORStockScan \
  --mount type=bind,source=/home/ubuntu/KORStockScan/.venv,target=/home/ubuntu/KORStockScan/.venv,readonly \
  --workdir /home/ubuntu/KORStockScan -e PYTHONPATH=/home/ubuntu/KORStockScan \
  -e PYTHONDONTWRITEBYTECODE=1 -e TMPDIR=/home/ubuntu/KORStockScan/tmp \
  -e HOME=/home/ubuntu/KORStockScan/tmp \
  --entrypoint /home/ubuntu/KORStockScan/.venv/bin/python postgres:15 \
  -m src.engine.automation.postclose_summary_handoff \
  --stage widget_policy --date 2026-09-23 --recover-closed-target --timeout-sec 180
```

이 명령은 **이미 연구 JSON과 terminal이 바뀐 격리 root**에 다시 쓰므로, 최초 실패를 재현할 때는 입력 manifest로 **새 root를 다시 만들어야** 한다. 재시도 명령의 외부 `/usr/bin/time` wall은 **4.71초**이고 container 내부 child CPU·peak RSS·I/O를 분리하지 못했다. 이 수치를 widget 계산이나 allocation 성능 PASS로 사용하지 않는다. allocation 실제 child의 cold/warm 측정은 **미실행**이다. provider budget은 이 경로에서 허용 **0**, 연결 **0**이며 실제 API 비용은 발생하지 않았다.

닫힘 검사/owner: `S5-FIN-01`의 widget·episode producer와 allocation reader owner는 **다음 자연 source date의 아직 갱신 가능한 effective date**에서 clean 연구·정책·native capacity 입력을 먼저 고정하고, 같은 절대경로 격리 namespace에서 현 코드 세 stage의 새 run ID·입출력 SHA·source date를 대사해야 한다. 새 widget·episode·capacity 영수증이 모두 유효할 때에만 allocation 실제 child와 원천 변경→재보류를 측정한다. 9/23→9/28의 이미 종료된 정책 세대는 9/28 07:30 이후 원래 입력·정책을 유지한 채 현재 코드로 자연 재출판할 수 없다. 이는 **역사적 격리 평가 blocker**이며, 우회용 코드 수리나 운영 정책 갱신 사유가 아니다. 다음 자연일의 stage가 실패하면 해당 producer/첫 reader의 S6 결손으로 되돌린다.

운영 9/23 capacity `failed(exit=2)`·allocation `deferred(exit=75)`·summary 실패·controller 차단은 그대로다. 이번 격리 실패와 직전 capacity 격리 성공을 합쳐 15 stage, strict, finalizer/detector, 선택 릴리스, PREOPEN, PID 소비 또는 자연 비용 조정 수익성을 주장하지 않는다. `S5-FIN-05`도 새 자연 장후 source date의 별도 조건부 결손이다.

자가 리뷰: stage 코드의 날짜·동일 세대·출판 보존 가드와 격리 root의 수정 범위를 재대사했다. audit 도구의 첫 오탐은 수정 후 source write/socket/임의 child 거절을 다시 검증했으며, 위 결과에 실패 원인을 분리했다. 영향 회귀 **9 passed** (`test_stage_prerequisites_and_changed_generation`, `test_overnight_publication_recovery_stops_before_preopen`, `test_family_source_read_does_not_require_peer`, `test_allocation_stage_does_not_rewrite_family_studies_or_policies`). 문서 상대 링크 **4개 유효**, trailing whitespace **0**, `git diff --check` **PASS**, print-only checklist parser **PASS(32 task)**다. repository Python·wrapper·정책·서비스·provider·threshold는 수정하지 않았으므로 compile·`bash -n`/wrapper 계약 검사는 해당 없음이다. 외부 Project/Calendar 동기화는 실행하지 않았다.
