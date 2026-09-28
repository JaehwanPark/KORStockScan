# S6 후속 — `S5-FIN-01` 선행 영수증의 격리 세대 전이 계약

실행일: **2026-09-28 KST**. 인계: [직전 S7 capacity→allocation 격리 gate](2026-09-28-intraday-postclose-handoff-S7-S5-FIN-01.md), [원래 S6 수리](2026-09-27-intraday-postclose-handoff-S6-S5-FIN-01.md). **판정: `no_code_repair`.** 복제 경로의 실패는 의도된 절대경로·내용 결속이며, 동일 절대경로를 제공하는 읽기 전용 격리 namespace에서 원본 widget·episode 영수증의 저장 코드 세대가 모두 검증됐다. 현재 작업본 코드 세대는 원본 9/23 영수증과 실제로 달라 `code_changed`가 남는다. 과거 영수증을 현재 코드의 성공으로 전이하지 않았고 allocation 실제 child는 실행하지 않았다.

## 1. 생산자→첫 reader와 실패 fixture

| 연결 | 원본 SHA·첫 소비 | 복제 경로 fixture | 동일 절대경로 fixture |
| --- | --- | --- | --- |
| widget 연구·정책 → `widget_policy` terminal → `research_allocation` prerequisite | 원본 terminal byte SHA `7cf54f667313ccc0af55f4531a2384e66df5a5b1c09cd362e7c55a7ad84d6e96`; 저장 stage code SHA `5632823732f38d4818f5fcb19c81cb25b1dc8122c2db0661162c9b46833a3621` | 현재 코드 검사 `code_changed`, 저장 코드 SHA를 강제한 진단 검사 `output_generation_changed` | 저장 코드 SHA 검사 `[]`; **현재** 코드 검사 `code_changed`, 현재 SHA `0384d9213396e81fa43906156fd57645f35fb7c0d058d03e9c7e5271c74cdcff` |
| episode 연구·정책 → `episode_policy` terminal → `research_allocation` prerequisite | 원본 terminal byte SHA `a9b123b65c2bcb514344baa08597a4269025ee8982892e02a24a2b4fdb673ef7`; 저장 stage code SHA `6e0b898ece52e1f47550ea867b1d63c457a9c0a4183e3b0ac2328b8048da0082` | 현재 코드 검사 `code_changed`, 저장 코드 SHA 강제 진단 `output_generation_changed` | 저장 코드 SHA 검사 `[]`; **현재** 코드 검사 `code_changed`, 현재 SHA `f8eaacba94791fbb1860a36f54bbad41dcea8cedfcf76bebb72944aeeacc9f3f` |

재현 fixture는 복제 경로 `/tmp/kor_s7_capacity_allocation_20260928/s6_relocated_fixture.py`(SHA `465d023274e80a6519d010a702317cd62296014b2a9971521d1f96702b538828`)와 동일 절대경로 `/tmp/kor_s6_prerequisite_namespace_20260928/s6_prereq_fixture.py`(SHA `22f3fa128eb4717edbe0c327469028d057fc93d2418263eaa40a010a9cba2f53`)에 남겼다. 두 fixture 모두 기대한 거절·수용을 assert하고 종료 0이었다. 동일 절대경로 fixture는 로컬 `postgres:15` 이미지 ID `sha256:c635fa3e3b7421a659d34abdfd6d492f679cbe8149e261a501237b55c5a94212`의 일회성 컨테이너를 사용했다. 호스트 `/usr`·프로젝트 `.venv`·독립 코드/데이터 복제본만 **읽기 전용**으로 mount하고 `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000`으로 실행했다. 운영 source/data는 mount하지 않았고 컨테이너는 `--rm`으로 종료했다. `unshare`는 이 계정에서 `Operation not permitted`였지만, 컨테이너의 안전한 같은 경로 namespace는 실제로 동작했다.

재현 명령의 핵심은 아래와 같다. 첫 명령은 복제 root에서 기대한 실패를, 둘째는 동일 절대경로 namespace에서 저장 코드 세대 수용과 현재 코드 세대 거절을 확인한다.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kor_s7_capacity_allocation_20260928 \
TMPDIR=/tmp/kor_s7_capacity_allocation_20260928 \
.venv/bin/python /tmp/kor_s7_capacity_allocation_20260928/s6_relocated_fixture.py

docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 1000:1000 \
  --mount type=bind,source=/usr,target=/usr,readonly \
  --mount type=bind,source=/home/ubuntu/KORStockScan/.venv,target=/home/ubuntu/KORStockScan/.venv,readonly \
  --mount type=bind,source=/tmp/kor_s6_prerequisite_namespace_20260928,target=/home/ubuntu/KORStockScan,readonly \
  --workdir /home/ubuntu/KORStockScan \
  -e PYTHONPATH=/home/ubuntu/KORStockScan -e PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint /home/ubuntu/KORStockScan/.venv/bin/python postgres:15 \
  /home/ubuntu/KORStockScan/s6_prereq_fixture.py
```

## 2. 계약 원인·변조 거절·수리 판정

- [`postclose_summary_handoff.py`](../../src/engine/automation/postclose_summary_handoff.py)의 `_stage_sources`는 각 source의 **절대경로와 byte SHA**를 함께 기록한다. `_stage_code`도 dispatcher/module 경로·내용과 family `code_contract`를 해시한다. `stage_receipt_issues`는 원본 영수증 본문 SHA, 코드 세대, 출력, 선행·입력 경로/SHA, family refresh의 source·policy digest를 순서대로 검사한다. [`machine_research_closed_loop_refresh.py`](../../src/engine/automation/machine_research_closed_loop_refresh.py)의 직접 allocation reader는 stage가 통과한 뒤에도 자기 `code_sources`·`dependency_catalog`·각 파일 세대와 정책 publication을 확인한다. 경로 문자열을 바꾸고 receipt hash만 다시 계산하는 행위는 같은 원본 세대의 증명이 아니다.
- 원본 widget·episode terminal과 9/23 capacity source는 시작·종료 SHA가 같았다. 같은 절대경로 namespace에서는 원본 terminal을 **byte 수정 없이** 사용했고 family 정책 파일도 원본 byte와 일치했다. 격리 widget 정책 파일만 의미 있는 필드를 추가한 negative fixture에서는 저장 코드 SHA 검사조차 `widget_policy:family_publication_invalid`로 거절했다. 정책 파일을 원본 SHA `0466240a15afe4347712c7a4edf10483de167bc0f5985f043e0f05316137333f`로 복구했다. 잘못된 날짜·누락 파일·중복 전이에 대한 **새 전이 계약**은 만들지 않았으므로 수용 경로도 없다.
- 동일 절대경로로 relocation 오류를 제거해도 현재 코드 검사는 원본 운영 경로와 격리 namespace에서 모두 `code_changed`다. 이는 현재 코드가 원본 생산 코드와 달라진 실제 세대 차이다. 현재 `stage_receipt_issues`의 선택 릴리스 호환 검사도 원본 운영 경로에서 이를 수용하지 않았다. 저장 코드 SHA를 인자로 전달한 검사는 **진단용**이며, 현재 allocation stage의 선행 PASS나 새 런타임 권한이 아니다.
- 따라서 이번 범위에 **수리할 생산자·직접 reader 코드 결손은 확인되지 않았다**. 원본 내용이 검증된다고 해서 현재 코드 세대의 선행 stage를 성공 처리하는 전이 영수증을 추가하면 의도된 코드 세대 거절을 약화한다. widget·episode 원본 영수증과 정책을 재작성하거나 새로운 경로·영수증을 소급 생성하지 않았다. repository Python·wrapper·정책은 변경하지 않았다.

## 3. 닫힘 검사와 S7/S8 인계

`S5-FIN-01`의 **수리 owner는 기존 widget·episode 생산자 및 allocation 첫 reader**다. 현재 코드의 실제 allocation child를 평가하려면, 동일 절대경로를 갖는 별도 격리 namespace에서 widget·episode의 **현재 코드 세대**를 새 stage attempt로 생성·검증해야 한다. 그 사전 작업은 source date·연구 입력·정책 출력·lock·config·provider 경로의 운영 분리와 widget 현재일 state의 고정 SHA를 먼저 증명해야 한다. 그 뒤 새 capacity attempt와 정확히 같은 source date의 세 선행 terminal SHA를 allocation이 자연 소비하는지, source 변경 시 보류하는지 확인하고 별도 S7에서 cold/warm 자원·원본/유효/격리 분모를 측정하라. 원본 9/23 widget·episode attempt를 새 코드 영수증으로 승격하지 마라. 새 격리 producer 실행의 출력이나 provider 경로를 모두 격리할 수 없다면 allocation 실행을 계속 막고 그 경로를 blocker로 기록하라.

9/23 **운영** capacity `failed(exit=2)`·allocation `deferred(exit=75)`·summary 실패·controller 차단은 그대로다. 9/24 `DONE`, 과거 `main_terminal` PASS, 이 read-only fixture의 수용을 현재 15 stage→strict→detector 성공으로 승격하지 않는다. `S5-FIN-05`는 새 자연 장후 source date에서 재현할 별도 묶음이다. 릴리스·PREOPEN·PID·자연 비용 후 경제성은 S8에 남긴다.

자가 리뷰: 같은 경로에서 저장 코드 기준 유효함을 확인했고, 현재 코드 세대 차이를 경로 결손으로 잘못 분류하지 않았다. policy byte 변조 거절 후 원본을 복구했으며 선행 receipt의 임의 hash 강제는 현재 실행에 적용하지 않았다. 영향 회귀 `test_stage_prerequisites_and_changed_generation`, `test_closed_capacity_failure_blocks_allocation_and_controller_then_binds_native_generation`, `test_allocation_stage_does_not_rewrite_family_studies_or_policies`, `test_unchanged_stage_accepts_exact_selected_release_code_hash` **4 passed**. 실제 allocation child·성능은 미검증으로 유지한다. 문서 링크·parser·diff 종료 검증은 아래에 기록한다.

종료 검증: 상대 링크 **4개 유효**, trailing whitespace **0**, 두 임시 fixture SHA 재확인, `git diff --check` **PASS**. `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` **PASS**, 현재 32 task 파싱. repository Python·wrapper 변경이 없어 별도 Python compile과 `bash -n`/wrapper 계약 검사는 해당 없음이다. 정규 장후작업·PREOPEN·배포·실주문·취소·provider 연결을 실행하지 않았고 정책·수량·timeout·서비스·threshold를 변경하지 않았다. 외부 Project/Calendar 동기화도 실행하지 않았다.
