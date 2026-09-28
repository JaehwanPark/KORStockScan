# S7 후속 — `pre_submit_delay` 실제 reader 격리 실행 gate

실행일: **2026-09-28 KST**. 인계: [직전 S7 격리 재측정](2026-09-28-intraday-postclose-handoff-S7-S1-COM-02-A-isolated-remeasurement.md), [재시작 경계 S6](2026-09-28-intraday-postclose-handoff-S6-S1-COM-02-A-3event-restart-drain.md). **판정: 읽기 전용 코드 snapshot의 실제 `pre_submit_delay_tuning.main()`→첫 stage 영수증 경로는 격리 입력에서 PASS, 경제성·역사적 운영 봉인·자연 수용은 미완료.** 앞선 mock runner와 달리 evaluator 본체·stage output validator를 그대로 실행했다. 단, stage subprocess 대신 같은 process에서 직접 `main()`을 호출하는 runner만 주입했으며 이 수치는 운영 child process의 총비용이 아니다.

## 1. 격리 경계와 입력 고정

- 시작 작업본 HEAD `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`, tracked diff SHA-256 `c935ea32d15aa3cab9c3cf59a96c4c451fc115afc936ff8a63723ae746b8e863`. 코드·체크리스트는 독립 snapshot `/tmp/kor_s7_actual_reader_20260928_final`에 복제했다. 측정 전에 `src`의 모든 파일 쓰기 권한을 제거했고 symlink는 0개였다. 상대 경로 포함 Python 원천 목록 SHA-256 `1e146334eb956d47f7ebe120c3effeb70a29b9b639bcdac259b0e81b5be2d1ee`는 첫 실행·반복 실행 후에도 같다. 복제본의 `pre_submit_delay_tuning.py` SHA `76297b528404543434275e5af2d11b21c30fa64f77c2a8824d5fe9f0300045a6`, `postclose_summary_handoff.py` SHA `cb3dc30103a3396fcbbc26a77ff813165dccac65f339bdd05a50a25dd83ac6cb`는 시작 작업본과 같다. checklist SHA `c4869139e76fe49a7fef60b5fb674d3c1ea79aa1413c644999556b162fe1f6ef`도 유지했다. 함께 진행 중인 다른 세션 때문에 **전체 공유 작업본**을 불변으로 선언하지 않고 이 snapshot만 이 실행의 코드 기준으로 삼았다.
- source date **2026-09-23**은 clean baseline 2026-06-05 이후다. 실제 `threshold_cycle`의 `pre_submit_delay` 및 `dynamic_entry_price_resolver` 9/23 part **469파일·7,507,493 bytes**를 복사했고 원본과 각 파일 SHA가 일치한다. 입력 목록 SHA `fecc1e4367ae4636554cc055037a6c9e3bb780a0e0e553bde9abe18796dcd047`; `clean_baseline_policy.json` SHA `dd02f8c6be231b1c4d179b5a1adb2f20b653f9a5772f25be23496391c4432931`도 동일하다. reader의 직접 `pre_submit_delay` part는 5파일·25,983 bytes, source SHA `d5d00ee808b9356e110afdf889188ec99e47b060d82662d236d4f02703954787`이다.
- 첫 stage용 pipeline 요약은 **`isolated_reconstruction`**이다. 9/23 운영 gzip의 논리 offset `3,396,345,288..3,396,353,897`에서 확인된 record `47859`의 3 raw line을 각 line SHA로 검증해 복제본에만 기록했다. 복제 raw 논리 SHA `1cbc6b0221eb0d600e3744ef819d874f48d9f6175ece076761cd86ef8c1c0196`; 별도 compactor 요약은 **raw 3 = valid 3 + excluded 0 + quarantined 0 + unobserved 0**, summary **3 event/3 row**, 논리 SHA `af67781ac674cb975a157386a8de5a34c46431d43769523f156cf50143314263`. 봉인 ledger SHA `0fbda8ea2ad9eeab6718dc52b5dcfd7fbea286796f13ed268d9391efebfde0d9`, manifest 파일 SHA `20767644a5c944bf8a13ee1cb8f92a4c95d311c488eefdcb4c003e453c0cd03e`. 이 세 건은 **9/23 전체 raw 374,864·profile 166,643·저장 shadow 166,640의 대체 모집단이 아니다.** 운영 shadow·manifest·terminal에 삽입하거나 소급 보정하지 않았다.
- `src.utils.constants.PROJECT_ROOT/DATA_DIR`, evaluator `REPORT_DIR/POLICY_DIR`, 9/23 source part, raw/요약 manifest, stage report·lock·quote cache·임시 파일은 모두 복제 root 안으로 결속했다. snapshot의 `sitecustomize.py` audit guard SHA `619d29e8410da8b53818aa2ecc3e236ce28122fd3fb91f9506ccb353c2581eab`가 root 밖 쓰기와 `socket.connect`·`subprocess.Popen`을 거절한다. 각 거절 경로를 별도 probe로 확인했고 symlink 0·읽기 전용 source tree를 확인했다. `run_stage`의 runner는 원래 생성된 `src.engine.scalping.pre_submit_delay_tuning` command만 받아 **실제 `main()`**에 같은 인자를 전달한다. evaluator 실행 중 외부 provider 연결 **0**, 차단 우회 **0**이었다. 별도 guard probe의 연결 시도는 거절됐다. 운영 파일의 manifest·stage·report·policy SHA는 실행 후에도 기존 값 그대로였다.

재현 명령(복제본과 입력 고정 뒤):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kor_s7_actual_reader_20260928_final \
TMPDIR=/tmp/kor_s7_actual_reader_20260928_final/tmp \
/usr/bin/time -v /home/ubuntu/KORStockScan/.venv/bin/python \
/tmp/kor_s7_actual_reader_20260928_final/s7_run_actual.py --label first

# 같은 snapshot·입력에서 별도 process로 반복한다.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kor_s7_actual_reader_20260928_final \
TMPDIR=/tmp/kor_s7_actual_reader_20260928_final/tmp \
/usr/bin/time -v /home/ubuntu/KORStockScan/.venv/bin/python \
/tmp/kor_s7_actual_reader_20260928_final/s7_run_actual.py --label repeat
```

복제 root의 준비 스크립트 `s7_prepare_source.py`는 3건을 별도 compactor로 봉인한 다음 같은 ledger의 `producer_source_ledger_issues=[]`를 확인한다. 두 실행의 terminal·input·report·policy SHA와 GNU time 기록은 `/tmp/kor_s7_actual_reader_final_{first,repeat}.{jsonl,time}`에 남겼다. 이 `/tmp` 스크립트·측정 산출물은 임시 증거이며 정규 장후 명령이나 배포물이 아니다.

## 2. 실제 reader 결과와 분모

두 실행의 stage input manifest SHA는 모두 `20767644a5c944bf8a13ee1cb8f92a4c95d311c488eefdcb4c003e453c0cd03e`; 시작·종료 입력 SHA가 같았다. 실제 reader 호출 **각 1회**, stage terminal **각 `succeeded(exit=0)`**, 현재 `stage_receipt_issues=[]`였다. 이는 producer 원천·영수증·산출물 연결의 **격리 수용**이다. evaluator의 결과 자체는 두 번 모두 **`source_gap`**, `first_blocker=fresh_route_bound_horizon_quote_missing`, `runtime_apply_allowed=false`다.

| reader 단위 | 첫 실행·반복 실행 공통 결과 |
| --- | --- |
| 직접 part census | raw event **10 = committed 2 + quote 6 + intent terminal 2**, deduplicated 10, duplicate 0; eligible attempt **2** |
| 0초 quote horizon | eligible 2, observed 2, **quarantined 2**, valid 0, unobserved 0 |
| 30·60·120·180초 각각 | eligible 2, observed 1, **quarantined 1**, valid 0, unobserved 1 |
| terminal·품질 | 유효 terminal 0, `terminal_unbound_or_clock_invalid=2`, `quote_generation_or_epoch_mismatch=6`, `quote_unobserved_or_conflicted=4` |
| grid·경제성 | 후보 **0/30/60/120/180초 5개 모두 미통과**. 모든 후보 paired EV·holdout·실제 비용 기반 수익성 **`null`**, 선택 지연 `null`; 거래 기회 0 또는 0초 우수성으로 판정하지 않음 |

평가 필드만 고정한 논리 결과 SHA는 두 번 모두 `c1be058032dc7cb1043d342b96c091f196a0d0d4bffc9b357f36336a497fec00`이다. 생성 시각·cache 상태·terminal run ID 등의 실행 메타데이터가 달라 파일 byte SHA는 일치하지 않는다: 첫 실행 report `77201a39c35cae7f2dbc63575c48105c16ae08faf7dff7732e491380cfb0e173`, policy `057fb28383bdecec2beedfdcca5b657ade9e1e35be46b170c6740c7432af32ec`, terminal `54c1b38f4b2e7e606801a0a385c5ebac357f0e04643963afa136967f74b26244`; 반복 report `862b9d743d83119ca1eb98edf26a8dd7feb4efb8f8a5d401e5c8313f5c3f7d98`, policy `ba3dc7ba8e6d303e86b7674395c7364efffb75e70e05332ede238640dce514d7`, terminal `994d090a10f46ce277dfa317c79e443048b2042bc2f02a780992a3d62e7d827e`. 평가 결과의 동일성과 파일 byte 동일성은 구분한다.

9/23 저장 운영 report SHA `c52f9d469a981966be7133493c3fdfb59c4c093d6c90048924189dc1b1d49d6e`는 당시 terminal 관측 2건을 표시한다. 이 격리 reader의 **유효 terminal 0**은 현재 엄격한 identity·clock 평가와 부분 원천 재구성의 결과다. 두 보고서를 같은 생성물이나 자연 결과로 합치지 않는다. 운영 비용·완전한 후행 quote가 없으므로 실현 PnL을 생성하지 않는다.

## 3. 첫 실행·반복 자원과 한계

| 동일 입력의 실제 reader stage | wall | user+system CPU | peak RSS | GNU time I/O inputs/outputs | quote census cache |
| --- | ---: | ---: | ---: | ---: | --- |
| 첫 process | **0.38 s** | 0.33+0.03 s | 42,620 KiB | 0 / 72 | miss |
| 반복 process | **0.39 s** | 0.33+0.03 s | 42,492 KiB | 0 / 72 | hit |

첫 process에는 앱 cache가 없고 두 번째에는 동일 입력의 `existing_quote_census` cache가 있다. OS page cache는 통제하지 않아 이 수치를 엄격한 디스크 cold/warm으로 일반화할 수 없다. GNU time I/O는 원시 block 수치다. `subprocess.Popen`을 금지하고 직접 runner를 사용했으므로 child 시작 비용과 전체 운영 wrapper 자원은 미측정이다. 입력 또한 9/23 전체 6.5GB가 아니라 **scanner 3건의 재구성 요약 + 실제 pre-submit part 복제**다. 이를 전체 raw 봉인·자연 stage 성능, 새 정책·경제성 승인 또는 변경 전/후 **코드 세대**의 성능 비교로 승격하지 않는다. 구세대에는 동일하고 봉인된 9/23 운영 입력이 없어 cross-code 동일 범위 비교를 실행하지 않았다.

## 4. 판정·blocker·인계

- **PASS — 격리 gate:** 읽기 전용 코드 snapshot, 원본과 byte 동일한 직접 part, `isolated_reconstruction`으로 봉인한 같은 날짜·논리 세대, root 밖 쓰기·network·subprocess 차단, 실제 reader `main()`과 stage output/영수증의 동세대 수용을 확인했다. 이번 실행은 공유 작업본의 코드·체크리스트·원천 또는 운영 manifest/terminal/report/policy를 변경하지 않았다.
- **BLOCKER — 실제 9/23 전체 원천:** raw 374,864/profile 166,643과 역사적 shadow 166,640의 3 event 차이, raw ledger 없는 운영 영수증은 그대로다. 새 자연 source date에서 재시작 전후 ID·partition·offset·논리 SHA, stage별 원본·유효·제외·격리·미관측·canonical identity 합, manifest→첫 stage 입력 SHA가 일치해야 닫힌다. 원천 ID가 없는 terminal·비용은 `unknown`·`null`이다.
- **BLOCKER — 전수 성능·경제성:** 전체 source를 운영과 분리한 동일 세대 snapshot으로 봉인하고 실제 child process·provider 예산을 포함한 stage cold/warm, grid·holdout·broker 실제 비용을 대사해야 한다. 지금은 후보 미통과·비용 `null`을 유지한다. 결손이 재현되면 해당 `S1-COM-02-A` 또는 `S2-ENT-04` owner의 S6 재수리 후 S7을 다시 측정한다.
- 9/23 capacity 실패→allocation 보류, 과거 `main_terminal` strict PASS, 나머지 15 stage 전체 성능과 `S5-FIN-05`는 별도다. 릴리스·PREOPEN·PID·자연 경제성은 S8의 별도 수용이다. **정규 장후작업·PREOPEN·배포·실주문·취소를 실행하지 않았고 정책·수량·timeout·서비스·provider·threshold를 변경하지 않았다.**

## 5. 종료 검증

- 복제 part **469파일·7,507,493 bytes**의 원본 대비 파일별 SHA 및 inventory SHA `fecc1e4367ae4636554cc055037a6c9e3bb780a0e0e553bde9abe18796dcd047` 재확인. snapshot Python 원천 목록 SHA `1e146334eb956d47f7ebe120c3effeb70a29b9b639bcdac259b0e81b5be2d1ee` 불변. 관련 코드·체크리스트 파일 SHA도 시작값과 동일했다.
- 보고서 상대 링크 **2개 유효**, trailing whitespace **0**, `git diff --check` **PASS**. `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` **PASS**, 32개 task 출력. 이번 변경은 보고서 문서만이므로 Python compile·wrapper 계약 검사는 해당 없음이다.
- 공유 작업본의 **전체** tracked diff SHA는 종료 시 `19c2e80fb420bb462a9f9507eaf038b06e83e283970c20cd6445e6799a5b8eb3`로 시작값과 달랐다. 다른 세션의 동시 변경이므로 전체 작업본 불변성은 주장하지 않는다. 이 실행의 독립 snapshot 및 관련 코드·체크리스트·운영 입력은 위 SHA로 고정했다.
