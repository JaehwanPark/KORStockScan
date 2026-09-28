# S7 후속 — `S1-COM-02-A` raw→shadow→첫 reader 격리 재측정

실행일: **2026-09-28 KST**. 인계: [S7 전체 체인 검증](2026-09-28-intraday-postclose-handoff-S7.md), [3 event 재시작 경계 S6](2026-09-28-intraday-postclose-handoff-S6-S1-COM-02-A-3event-restart-drain.md). **판정: 이 경로의 격리 원천·영수증 fixture PASS; 9/23 운영 봉인·실제 `pre_submit_delay_tuning` 계산 성능·자연 소비는 blocker.** 변경 전 재시작 함수 경계와 수리 후 경계를 같은 raw byte 입력으로 비교했다. 첫 reader의 실제 평가 CLI와 정규 장후 stage는 실행하지 않았다.

## 1. 고정 원천·작업본과 격리 경계

- 시작 HEAD `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`, tracked `git diff --binary` SHA-256 `8f9a4e06ca3b5d345d84dd406cef196989ed1ab6b7ede9214afaa978631687f4`. 관련 작업본 SHA-256: `pipeline_event_logger.py` `a82d4fec3b342d61f9f3ba0e1c32774fde09d7c9572033cdb220ff2cd0f97489`, `pipeline_event_summary.py` `1589603ed6fc2051ccb001b8863b294394f5b4308018e2ada44d18a3d12e0926`, 첫 reader `postclose_summary_handoff.py` `cb3dc30103a3396fcbbc26a77ff813165dccac65f339bdd05a50a25dd83ac6cb`, `test_pipeline_event_logger.py` `ff2c2fbe9ad4b6eb180e186890161d79a8b996468c155fb481df912c7ba609b3`, checklist `c4869139e76fe49a7fef60b5fb674d3c1ea79aa1413c644999556b162fe1f6ef`. 종료 대조에서 이 다섯 파일과 HEAD는 같지만 tracked diff SHA는 `8ec44236d11eb76b79afc28d2213e7786ad312de0e2922e3d0db4335ca26e713`으로 변했다. 함께 진행된 다른 세션의 status 경로도 늘어 **작업본 전체의 불변 freeze는 성립하지 않는다**. 이 fixture는 해시로 고정된 관련 코드·체크리스트와 별도 임시 root에 한해 판정한다. 다른 미커밋 변경은 보존한다.
- 9/23 운영 gzip은 **437,234,985 bytes**, physical SHA-256 `471c327ab369d195d5374f3f2e4860966303c7d963ffe3cc1e69b26a79851e18`, 논리 SHA-256 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`. 파일 inode `1363207`, 크기·mtime은 시작/종료가 같다. 논리 SHA는 `nice -n 19 ionice -c3 /usr/bin/time -v bash -o pipefail -c 'gzip -cd "$1" | sha256sum' _ data/pipeline_events/pipeline_events_2026-09-23.jsonl.gz`로 **읽기 전용** 재계산했다. 그 실행은 봉인이나 요약 재생성이 아니다.
- 기존 S7/S6의 raw **374,864 = 요약 대상 166,643 + profile 제외 208,221 + 격리 0 + 미관측 0**, 저장 shadow **166,640 event/70,076 row**, 같은 record `47859`의 세 미수록 event와 논리 offset·canonical identity는 원 보고서의 분모·ID로 인계했다. 이번에는 6.5GB raw ledger를 다시 계산하지 않았다. scanner promotion **3,216**은 별개 분모다. 운영 manifest SHA `59ece8b1c9ee26ddb8289d4caf5d151eec0f35d1c73a268dd9f4ecbc288d27d3`와 운영 `pre_submit_delay` terminal SHA `4237e26547a5f7cc4a24093fd791127c8c8a2061abc729d7a09c18673d891a38`는 그대로다.
- 재현 harness `/tmp/kor_s7_s1com02a_isolated.py` SHA-256 `6921afcee6db63a5facab04b9d36fb159196457938526ee76ef9a8bd962ca0a3`. 9/23 14:20:33의 고정 시각, record `47859`, promotion ID `fixture-promotion`, `broker_order_forbidden=True`의 scanner 네 stage를 사용했다. `old_drain`은 **수리 전 함수가 호출하던 동일 `_flush_producer_summary_at_exit()`**을 실행하고, `new_drain`은 수리된 drain을 호출한다. 두 arm은 나머지 동일한 현재 코드에서 독립 Python process·새 `/tmp/kor_s7_s1com02a_*` root를 사용한다. 그러므로 이는 **종료 경계의 통제 비교**이지 구 릴리스 전체와 신 릴리스 전체의 비교가 아니다.
- harness는 `DATA_DIR`·stage report·manifest·lock을 각 임시 root로 돌리고, 원천 밖 쓰기와 `socket.connect`·`subprocess.Popen`을 audit hook으로 거절한다. `dir_fd` 상대 raw append는 실제 descriptor 경로를 검사한다. stage command·output validator·runner는 fixture로 대체했고, 실제 provider 호출·주문·정규 CLI는 없다. 네 실행 모두 허용된 write path는 임시 root 아래만 있고 outside-root write/provider 시도는 0이었다. 명령 형태: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /usr/bin/time -v .venv/bin/python /tmp/kor_s7_s1com02a_isolated.py --arm {old_drain|new_drain} --root /tmp/kor_s7_s1com02a_{old_first|new_first|old_repeat|new_repeat}`; 각 실행의 JSON·GNU time을 같은 prefix의 `/tmp/*.json`·`/tmp/*.time`에 보존했다.

## 2. 동일 입력의 전후 결과

네 arm의 stage 실행 **전** raw 네 line SHA와 raw ledger 논리 SHA는 모두 `d4947f7ff75fdc7f9b67fd5f9e823edcf752da9aafb48920056ab11bcabde404`이다. 각 arm은 원본 4·유효 4·제외 0·격리 0·미관측 0이다. 네 stage 각각 raw 유효 1이며 같은 arm 간 canonical identity 합이 일치한다. fixture line은 9/23 운영의 원본 세 line이 아니므로 이 숫자를 9/23 저장 shadow에 더하지 않는다.

| 비교 | old drain 첫/반복 | new drain 첫/반복 |
| --- | --- | --- |
| raw append, compactor 거절 | 4, `closed` 오류 3/3 | 4, `closed` 오류 0/0 |
| summary event·row | **1·1 / 1·1** | **4·4 / 4·4**; stage별 summary count와 raw identity **각 1** |
| 봉인·첫 reader | `producer_raw_summary_count_mismatch`, `deferred(exit=75)`, runner 0 | raw ledger 봉인, fixture reader `succeeded(exit=0)`, runner 1, 동세대 `stage_receipt_issues=[]` |
| 새 event 뒤 구세대 | 기존 성공 영수증 없음 | 새 record `47860` append 뒤 옛 영수증 `raw_source_ledger_missing`으로 거절 |

첫 실행의 출력 SHA-256: old summary body `3285d88737d446c0481a201c4cc03c959c3ebb8b944e2e737424a901581ed4a3`, manifest `abf8049b6c162f0b48735ba1ebd35c668696f0e8fab14df240e90aa9b6ff6c79`, stage terminal `cf345dc6eade143e2df0a8a83aa6eaee113904338d02ab55e7764ea0c5fb85d8`; new summary body `4dda1e6b2bfe511f312913158d84b7f6e31600a75094e2d131477c29d209a83e`, manifest `bff1ad0c0eedf08e90efdf1bfbe881f9bb80e3eb0a105c77134d282ba18d571a`, stage terminal `ad70c0d2a4db4d25a4eca337d00408be8079f314e027059de53f92c4692d531c`, sealed ledger `ac2e237b116fe308edf5e385e0133d76082fc1f7588b7023772398626b818e28`. 반복 실행에서도 old/new 각각 summary body SHA가 같았다. manifest·terminal·ledger SHA는 root 절대 경로, 시간, run ID가 달라 실행 사이에 같을 필요가 없다. **동일 세대** 판단은 각 실행 내부의 source ledger→manifest→stage 영수증 관계로 했다.

## 3. 자원 측정과 실행 blocker

GNU time의 첫 실행/반복 실행값이다. 새 root를 매번 쓰고 동일 raw fixture를 다시 생성했다. OS page cache를 비우지 않았으므로 **진정한 cold/warm 디스크 비교가 아니라 process 첫 실행/반복 관측**이다. 특히 old는 첫 stage 계산을 시작하지 못하고 new는 fixture runner까지 진행하므로 두 arm의 전체 wall 차이를 수리 코드의 순수 성능 회귀로 해석할 수 없다. `File system inputs/outputs`는 GNU time의 원시 block 수치이며 provider budget은 fixture에서 **0 호출**이다.

| 실행 | wall | user+system CPU | peak RSS | I/O inputs/outputs |
| --- | ---: | ---: | ---: | ---: |
| old 첫 실행 | 0.35 s | 0.29+0.02 s | 43,016 KiB | 0 / 56 |
| new 첫 실행 | 0.40 s | 0.31+0.02 s | 42,856 KiB | 0 / 184 |
| old 반복 | 0.35 s | 0.30+0.02 s | 42,896 KiB | 0 / 56 |
| new 반복 | 0.41 s | 0.31+0.03 s | 42,932 KiB | 0 / 184 |
| 9/23 gzip 논리 SHA 읽기 전용 | 23.50 s | 24.24+1.89 s | 3,208 KiB | 6,192 / 8 |

**실제 9/23 raw 봉인과 `pre_submit_delay_tuning` CLI는 실행하지 않았다.** 역사적 shadow가 3건 작으므로 현재 seal은 정상적으로 거절해야 한다. 6.5GB 원천을 요약 재생성해 과거 영수증에 덮어쓸 수 없고, 실제 평가 모듈의 `REPORT_DIR`·`POLICY_DIR`·`_source_rows`는 `src.utils.constants.DATA_DIR = PROJECT_ROOT/data`에 결속돼 있다. stage runner의 `report_dir`만 임시 root로 바꿔도 이 직접 reader의 출력·lock·기타 source/provider 경로 전체 격리가 증명되지 않는다. 따라서 실제 stage cold/warm wall·CPU·RSS·I/O 및 전체 후보 grid·holdout·비용 parity는 **`unmeasured_blocked`**다. 독립된 복제 source tree/data root와 모든 writer/provider 경로 검사 없이는 재시도하지 않는다.

## 4. 판정·owner·닫힘 검사

- **PASS (격리 계약):** 동일 raw SHA·날짜의 restart fixture에서 source count/identity→summary manifest→첫 stage 영수증이 new 경로에서만 동세대로 닫히고, 후착 event가 과거 영수증을 stale로 만든다. 이 fixture의 `succeeded`는 stage runner와 output validator를 대체한 **원천·영수증 계약 결과**이며 실제 가격 경로, 비용, 후보 grid, holdout 성능이 아니다.
- **BLOCKER (역사·자연):** 9/23 저장 summary 166,640과 profile raw 166,643의 차이 3, 역사적 raw ledger 없는 manifest, 과거 stage terminal은 그대로다. `pipeline_event_logger`/`ProducerSummaryCompactor` owner는 다음 자연 source date에서 재시작 전후 event ID, partition·offset·논리 SHA와 stage별 원본·유효·제외·격리·미관측 및 canonical identity 합을 새 manifest와 첫 reader 입력·terminal SHA에 결속해 닫는다. 로그의 per-event error와 원본 ID의 1:1 historical mapping은 여전히 `historical_unbound`다.
- **BLOCKER (실제 성능):** `pre_submit_delay_tuning` 및 stage runner owner는 운영과 분리된 source tree·data/output·lock·provider budget 경로를 고정한 뒤 같은 clean 입력의 실제 stage cold/warm 계산·결과·grid·holdout·비용을 측정한다. 값 또는 성능 결손이 나오면 해당 owner의 **S6 재수리**에 돌리고 이 S7을 재측정한다. 격리 fixture의 wall 차이로 운영 성능 PASS를 선언하지 않는다.
- **BLOCKER (전체 작업본 freeze):** 다른 세션의 status 경로 추가 때문에 통합 비교용 작업본 전체는 불변이라고 할 수 없다. 다음 S7 실제 계산은 독립 checkout 또는 읽기 전용 snapshot으로 code·checklist·source 전체를 고정하고 시작/종료 SHA를 일치시킨다.
- 9/23 `research_capacity=failed(exit=2)`→`research_allocation=deferred(exit=75)`→summary 실패, 과거 `main_terminal` strict PASS, 전체 15 stage→controller·finalizer·detector 성능은 별도 blocker다. `S5-FIN-05`는 새 자연 source date 조건부 결손이다. 릴리스 선택·PREOPEN·PID·자연 비용 조정 경제성은 S8에 남긴다. 이 S7은 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포·정규 장후작업·PREOPEN을 변경하거나 실행하지 않았다.

자가 검토: 수리 전 함수만 교체한 통제 비교를 과거 릴리스 전체 비교로, fixture runner의 `succeeded`를 실제 계산으로, 단일 raw SHA를 9/23 운영 봉인으로 승격하지 않았다. 다른 세션의 파일·운영 산출물은 변경하지 않았다. 보고서 상대 링크 **2개 존재**, trailing whitespace **0**, print-only backlog parser `--print-backlog-only --limit 500` **exit 0·32 task**, `git diff --check` **exit 0**. Python 소스·wrapper는 이번 S7에서 수정하지 않아 compile/`bash -n` 대상이 아니다. 외부 Project/Calendar 동기화는 실행하지 않았다.
