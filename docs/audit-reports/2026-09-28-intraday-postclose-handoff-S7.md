# S7 장중 원천·장후 소비 데이터 및 성능 통합 검증

실행일: **2026-09-28 KST**. 인계: [전체 체인 계획](../proposals/intraday-producer-postclose-consumer-codebase-gap-repair-plan-2026-09-27.md), [S5](2026-09-27-intraday-postclose-handoff-S5.md), 아래 S6 묶음별 보고서. **판정: 격리 fixture 회귀와 9/23 읽기 전용 원천·영수증 검사는 통과했으나, S7 전체 체인 PASS는 차단된다.** 9/23 raw와 보존 shadow 사이 3 event 차이 및 raw 봉인 부재, capacity 실패→allocation 보류→summary 실패, 구세대 strict/checklist가 남아 있다. 같은 세대의 자연 terminal→strict→controller·finalizer·detector 완료와 변경 전후 전체 family replay는 증명되지 않았다.

## 1. 고정 범위·재현 방법

- 시작 작업본 HEAD `8e8def53c6a6f66f45c36f2c2cd479c726fe3786`, `git status --porcelain=v1` **26항목**, tracked diff SHA-256 `a6f596fcd2a51f7a4401e17663d0ac6d9f7a80732c63eb629ca9d5a031366891`, status 목록 SHA-256 `7d1e06e3579deb5c048f2999dc1220896c7b01fa9c907dff58f2439f89dd5476`. 종료 시 S7 보고서를 제외한 status 목록과 HEAD는 동일하지만 tracked diff SHA는 `58fca82858bf52032d5a0a57a7e7bee07b31c496c0a8601470e31ea8c94d18b7`으로 바뀌었다. checklist 파일 mtime은 11:51 KST이고 소스·테스트 수정 파일 mtime은 이 S7 시험 시작 전이다. 따라서 작업본의 **완전 불변 freeze는 성립하지 않았다**; 통합 전후 비교 blocker에 포함한다. S6 소스·테스트·미커밋 보고서는 이번 S7에서 수정하지 않았다. 이 검증의 코드 기준은 테스트 실행 당시 작업본이며, 이전 S6의 fixture 수리·리뷰 PASS가 선택 릴리스나 PID 소비를 뜻하지 않는다.
- 같은 clean baseline 이후 source date **2026-09-23**의 원래 `.jsonl.gz`를 읽기 전용으로 스캔했다. 논리 SHA-256 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`, 해제 크기 **6,534,993,803 bytes**, 압축 크기 **437,234,985 bytes**; late part 없음. `_producer_raw_ledger(Path("data"), "2026-09-23")`는 운영 manifest나 stage 출력에 쓰지 않는다. 저장된 shadow 요약과 15개 stage 마지막 영수증, summary·strict·controller는 원본을 읽어 대사했다.
- 재현 명령은 `nice -n 19 ionice -c3 /usr/bin/time -v .venv/bin/python -c 'from pathlib import Path; from src.engine.pipeline_event_summary import _producer_raw_ledger; print(_producer_raw_ledger(Path("data"), "2026-09-23"))'` 및 `stage_receipt_issues(report_dir, day, stage, code_hash=receipt["stage_code_sha256"])`, `current_strict_receipt_issues`, `build_threshold_cycle_postclose_verification(..., require_summary_handoff=True)`의 읽기 전용 함수 호출이다. stage 검사는 **저장 영수증의 코드 해시를 고정**한 입력·출력·선행 영수증 검사로서 선택 릴리스 코드 동일성이나 새 실행의 증거가 아니다. raw scan과 검사는 운영 파일을 변경하지 않았다.
- 정규 wrapper·controller·finalizer·detector, manifest `seal_producer_summary_source`, PREOPEN 및 전체 family CLI는 실행하지 않았다. 이 호출들은 운영 경로에 영수증·lock·정책 산출물을 쓰거나 provider/실행 상태에 접근할 수 있고, 9/23 출력과 별개의 완전한 input/output root를 갖춘 실행 계약이 확인되지 않았다. 22개 관련 파일의 pytest fixture만 임시 경로에서 반복했다. 따라서 아래 성능은 **읽기 전용 검사·fixture** 수치이며 정규 장후 stage cold/warm 성능은 `unmeasured_blocked`다.

격리 fixture 첫·두 번째 측정은 다음 **동일한 명령**을 순차 실행했다. 출력·GNU time 기록만 `/tmp/kor_s7_pytest_{cold,warm}.*`에 두었다.

```bash
PYTHONDONTWRITEBYTECODE=1 nice -n 19 ionice -c3 /usr/bin/time -v .venv/bin/python -m pytest -q -p no:cacheprovider \
  src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_summary.py \
  src/tests/test_postclose_summary_handoff.py src/tests/test_verify_threshold_cycle_postclose_chain.py \
  src/tests/test_postclose_done_controller.py src/tests/test_postclose_finalization.py \
  src/tests/test_error_detector.py src/tests/test_runtime_approval_summary.py \
  src/tests/test_runtime_policy_bootstrap.py src/tests/test_research_closed_loop.py \
  src/tests/test_pre_submit_delay_tuning.py src/tests/test_low_price_two_leg.py \
  src/tests/test_scale_in_split_order_plan.py src/tests/test_entry_execution_sizing_plan.py \
  src/tests/test_entry_split_order_plan.py src/tests/test_entry_cancel_wait_tuning.py \
  src/tests/test_main_lifecycle_receipt_integration.py src/tests/test_trade_review_report_revival.py \
  src/tests/test_strategy_position_performance_report.py src/tests/test_holding_exit_observation_report.py \
  src/tests/test_jsonl_io.py src/tests/test_threshold_cycle_wrappers.py
```

## 2. S6 묶음 리뷰·회귀 고정과 S7 판정

각 S6 보고서의 범위 내 자가 재리뷰는 미해결 0으로 기록돼 있다. 아래 회귀 수는 **서로 겹치는 파일을 포함하므로 합산하지 않는다.** 이번 S7의 동일 명령 통합 fixture는 별도로 1,198건을 검사했다. `fixture PASS`는 원천·세대·비용의 계약 회귀가 통과했다는 뜻이고 `통합 blocker`는 9/23 전체 재생과 자연 체인 미닫힘을 뜻한다.

| 수리 owner·인계 보고서 | 기존 최종 회귀 | S7 직접 확인·판정 |
| --- | ---: | --- |
| `S5-FIN-02` AI 압축 [S6](2026-09-27-intraday-postclose-handoff-S6.md) | 167 pass | `outcome_labels`·`collector_recommendation`의 저장 코드 세대 입력/출력 검사 PASS; 전체 체인은 blocker. |
| `S5-FIN-01` capacity→allocation [S6](2026-09-27-intraday-postclose-handoff-S6-S5-FIN-01.md) | 152 pass | 저장 terminal은 failed/deferred 그대로; 동세대 성공 영수증 부재로 blocker. |
| `S5-FIN-03` strict·checklist [S6](2026-09-27-intraday-postclose-handoff-S6-S5-FIN-03.md) | 163+35 pass | 옛 strict 현재 세대 거절, fresh summary 검증 실패; blocker. |
| `S5-FIN-04` 미래 pointer [S6](2026-09-27-intraday-postclose-handoff-S6-S5-FIN-04.md) | 245 pass | 9/23 summary의 미래 PREOPEN 세대 stale; PID 수용은 S8. |
| `S1-COM-01-A` scanner 압축 [S6](2026-09-27-intraday-postclose-handoff-S6-S1-COM-01-A.md) | 158 pass | scanner trace 3 event의 raw/shadow 차이 조사 필요; 역사적 promotion 3,216과 raw 전체를 합산하지 않음. |
| `S1-COM-02-A` raw→요약→첫 stage [S6](2026-09-28-intraday-postclose-handoff-S6-S1-COM-02-A.md) | 215 pass | 아래 3 event 차이와 legacy ledger 부재로 실제 9/23 봉인 blocker. |
| `S2-ENT-03`·`S3-EXIT-02` BUY parent→보유 [S6](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-03-S3-EXIT-02.md) | 214+222 pass | 9/23 10 parent 미분류 유지; terminal·비용 보증 아님. |
| `S2-ENT-02` sizing 행 [S6](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-02.md) | 253 pass | 19 plan과 20 submit event 별개, 운영 paired/holdout 부재. |
| `S2-ENT-05` 순차 첫 BUY [S6](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-05.md) | 342 pass | 변경형 첫 leg fixture PASS; 9/23 10건의 원인으로 소급하지 않음. |
| `S3-EXIT-01` SELL terminal·비용 [S6](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-01.md) | 274 pass | 2 record의 execution·실제 비용 미관측 유지. |
| `S3-EXIT-03` 판단→SELL 신호 [S6](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-03.md) | 382 pass, 1 deselected | 옛 inferred 신호를 직접 신호로 승격하지 않음; 자연 정확 ID closure 대기. |
| `S3-EXIT-05` 완료 모집단·경제성 [S6](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-05.md) | 321 pass | strict 비용 원천 없는 323건은 실현손익 null·경제성 비적격. |
| 추가매수 [S6](2026-09-28-intraday-postclose-handoff-S6-DirectFamilySourceRepairScaleInSplit.md) | 134+907 pass | 9/23 적격 시도 0, 자연 경제성·독립 holdout 부족. |
| `S2-ENT-04` pre-submit [S6](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-04.md) | 92 pass | 0초 quote 2건 source-invalid, raw ledger 없는 옛 stage 영수증 거절. |
| 저가 2-leg [S6](2026-09-28-intraday-postclose-handoff-S6-DirectFamilySourceRepairLowPriceTwoLeg.md) | 241 pass | 1,035 observation event·40 NO_FILL leg만 확인, 실제 완료·비용 표본 없음. |

## 3. 원천·분모·ID·grid·비용 대사

| family·단위 | 원본 → 유효·제외·격리·미관측 | ID·평가 경계 |
| --- | --- | --- |
| `pipeline_events` raw event → `producer_summary` profile | **374,864 = 166,643 + 208,221 + 0 + 0**; 중복 0. `outside_producer_summary_profile=208,221`. | base part 논리 offset `0..6,534,993,803`, SHA `4db035…`. 기존 shadow는 **166,640 event / 70,076 summary row**이며 같은 원모수로 합치지 않는다. 당시 manifest에는 raw ledger·offset·partition 결속이 없다. |
| raw와 shadow 차이 | raw 유효가 shadow보다 **3 event 많음**: `scalping_scanner_heavy_eval_completion` 12,681 대 12,680; `scalping_scanner_heavy_eval_lag` 11,623 대 11,622; `scalping_scanner_promotion_latency_trace` 49,736 대 49,735. | 단일 raw SHA와 shadow manifest SHA `59ece8b1c9ee26ddb8289d4caf5d151eec0f35d1c73a268dd9f4ecbc288d27d3`. 각 stage raw event와 9/23 scanner promotion 3,216은 다른 단위다. 새 봉인의 `raw.valid_count == manifest.summary_event_count` 조건은 이 역사적 집합을 거절한다. 세 건의 원인·ID는 아직 미확인이다. |
| main BUY sizing·parent | plan 19 = 유효 17 + invalid 2; `real_submit_with_plan` **20 event**는 다른 분모. `order_leg_sent` 10 → 확인된 parent→보유 0, 격리 10. | record·attempt·parent·child·intent·broker order·execution의 정확 join이 부족하다. `entry_split_order_plan` grid 4개, 운영 paired/holdout 없음. 10 제출 event와 trade-review 10 record/8 terminal을 건수로 연결하지 않는다. |
| pre-submit | committed/eligible 각 2; 0초 quote 유효 0·source-invalid 2, 30~180초 후행 horizon 누락/무효. | route/session·transport epoch·intent/order/terminal clock 및 실제 비용 불완전. grid 5개 모두 candidate 통과 없음; holdout EV null. 거래 기회 0이나 0초 우수성 아님. |
| SELL 완료·비용 | 9/23 완료 표시 8 = 적격 투영 6 + 원천 결손 2 (`47531` 주문 `0012375`, `47515` 주문 `0011689`). 누적 유효 완료 **329 = strict 6 + 비용 결손 323**은 별도 기간. | 두 주문은 정확 execution·누적 수량·시각·broker 실제 과금이 없으며 손익 null. inferred exit 신호·부분 1/3/5/10분 관측은 직접·완전 결과 아님. SOR→KRX 기준 venue 오버라이드는 실제 체결 시장 증거가 아님. |
| 추가매수 | 9/23 `daily_unique_attempt_count=0`; 원본 적격 체결·비용·terminal 분모는 미관측. | record/position/attempt/order/execution의 새 계약은 fixture에서만 검증. candidate grid 0, 독립 holdout 없음; `insufficient_sample`. |
| 저가 2-leg | 관측 event **1,035 = 기존 검증 1,035 + invalid 0**. 일별 투영 profile 61 = pass 58 + source gap 3. attempted profile 20의 leg 40은 모두 `NO_FILL`; 완료/보유 leg 0. | profile/leg/order/execution의 영속 state 세대·real/sim 격리는 작업본 fixture. 관측 event는 주문이 아니다. `actual_sample_floor` 유지, broker 실제 과금 없으면 손익 null. grid/paired search는 `incumbent_preserved`, 런타임 적용 불가. |

`observation_source_quality_audit`의 별도 hard-blocking 제외 11 row는 위 raw producer-summary의 격리 0과 다른 감사 단위다. 각 family의 전수 `record/attempt/leg/order/execution` 행과 원본·유효·제외·격리·미관측 분모는 9/23 역사적 영수증에 없거나 독립 owner/real·sim·probe 증거가 부족하다. 누락 ID를 생성하거나 서로 다른 기간·owner·단위를 합산하지 않았다. 이 항목은 새 자연 source date의 동세대 영수증으로 닫아야 한다.

## 4. 15 stage→summary→strict→마지막 소비 세대

- 마지막 15 terminal은 상태상 `succeeded` 12, `research_capacity=failed(exit=2, run=254f207750424466a32d627679425201)`, `research_allocation=deferred(exit=75, run=1931beff0ab94c87a48ad9383a9f120c)`, `summary_handoff=failed(exit=1, run=d6bfce76156e4972a61b0ccd3d8740ed)`이다. 저장 코드 해시 기준 직접 reader 검사에서는 성공 12개 중 **11개 통과**, `pre_submit_delay:raw_source_ledger_missing` 1개다. 15개 영수증의 run ID·입력/선행/출력 SHA는 [각 terminal 원문](../../data/report/postclose_stage_terminal/2026-09-23/)에 보존했다. 영수증 성공 11개가 전체 체인 성공은 아니다.
- 9/23 runtime summary SHA `ecd8024afbd75025c2d9204cf8452bee806b285d084f280d620db79837aecea0`; main terminal SHA `8512acc65be4c7abe406e78d50e817fe80d67d4f7ca275778d2bc6e3f8938dc9`, run `ac4316e2b39c42d4b5f8a026559935d0`. 현재 읽기 전용 summary handoff 검증은 `future_preopen_generation_stale`, `checklist:source_generation_mismatch`, `checklist:future_handoff_semantics_mismatch`, `direct_checklist_task_projection_mismatch`로 **fail**이다. 작업본 코드의 `whole_native_chain` strict를 **출력 없이 생성**해도 `fail`, issue 9개: 위 4개와 `pre_submit_delay`, `widget_policy`, `episode_policy`, `research_capacity`, `research_allocation`의 stage invalid다. widget·episode는 저장 코드 해시 고정 검사에서는 유효하지만 현재 작업본 코드 기준 `code_changed`다. 기존 9/24 strict 파일 SHA `e17ca8e02b0027416b5853657a577273dd188051f305779f1b7a806c15242512`는 `main_terminal` scope PASS일 뿐 `whole_native_chain_done_claimed=false`; 현재 세대 검사 `strict_receipt_missing_or_invalid_generation`.
- 마지막 controller SHA `91eb01d4957a384424654e56c69ad5df35987f7420e23d03e9c2e7ee7bb53d05`, `blocked_independent_producer`, final verifier `not_run`. 9/24 recovery의 finalizer/cleanup/detector DONE은 당시 세대이며, 현재 fresh strict/controller에서 이어진 결과가 아니다. 이번 S7에서는 finalizer·detector를 재실행하지 않았다. 실패·보류·OFF·valid-empty를 성공으로 치환하지 않았다.

## 5. 격리 실행 성능과 차단된 비교

| 실행 | wall | user+system CPU | peak RSS | 파일 I/O (`/usr/bin/time -v` 원값) | provider |
| --- | ---: | ---: | ---: | --- | --- |
| 9/23 raw ledger 읽기 전용 첫 스캔 | 57.61 s | 56.81+0.22 s | 69,868 KiB | inputs 26,576 / outputs 16 | 호출 경로 없음 |
| 저장 코드 해시 고정 stage 15개+summary/strict 읽기 전용 검사 | 7.02 s | 5.79+0.40 s | 246,460 KiB | inputs 544,128 / outputs 8 | 호출 경로 없음 |
| 작업본 코드 전체 strict 읽기 전용 구성 | 6.71 s | 5.03+0.32 s | 93,608 KiB | inputs 677,528 / outputs 8 | 호출 경로 없음 |
| 통합 fixture 22파일 첫 실행 | 191.59 s | 155.21+14.83 s | 759,132 KiB | inputs 3,403,608 / outputs 287,112 | 실 provider 미사용 fixture |
| 같은 fixture 두 번째 실행 | 205.55 s | 156.28+15.49 s | 751,712 KiB | inputs 2,219,232 / outputs 287,144 | 실 provider 미사용 fixture |

두 fixture 실행은 동일 명령·동일 22파일, 각각 **1,198 pass·1 기존 pandas_ta warning**이었다. `File system inputs/outputs`는 GNU time의 원시 block 수치다. OS page cache를 비우지 않았고 활성 거래 프로세스가 함께 있어 첫/두 번째를 엄격한 cold/warm stage 벤치마크로 일반화할 수 없다. 실제로 두 번째 wall이 더 길었다. 전체 postclose stage의 wall·CPU·RSS·I/O·provider budget 및 변경 전후 동일 원천 full replay는 **운영과 분리된 모든 출력/lock/provider 계약이 준비되지 않아 미측정**이다. raw ledger/fixture PASS로 성능 개선이나 결과 parity를 주장하지 않는다.

## 6. blocker·owner·닫힘 검사와 S8 인계

| blocker | 영향·수리 owner | 닫힘 검사 |
| --- | --- | --- |
| 9/23 raw/shadow **3 event 차이**·역사적 ledger 부재 | `S1-COM-02-A`: `pipeline_event_logger`·`pipeline_event_summary` owner. 세 scanner stage의 누락 시각/ID·flush/late 원인을 조사한다. 역사적 manifest를 소급 조작하지 않는다. 새 clean source에서도 재현되는 계약 결함이면 해당 S6 묶음으로 수리한다. | 새 자연 source date의 raw SHA/partition/offset·stage count/identity = 봉인 manifest = 첫 `pre_submit_delay` 입력 SHA, 원본/제외/격리/미관측 보존. |
| 9/23 capacity 실패·allocation 보류·summary 실패와 구세대 strict/checklist | `S5-FIN-01/03` 생산자·첫 소비자와 controller/finalizer owner. S6 fixture 수리와 실제 terminal은 별개. | 격리 root에서 동일 세대 15 stage의 source/effective date·run·input/output/prerequisite SHA → runtime summary → `whole_native_chain` strict → fresh controller·finalizer·detector를 재현하고 cold/warm 자원을 측정. 실패/OFF/valid-empty·재시도/복구를 개별 행으로 확인. |
| BUY parent 10 미분류, SELL 2 실제 terminal·비용 부재, 추가매수·저가·pre-submit 적격 표본 부족 | 각 S2/S3 및 저가/추가매수 S6 owner. source-quality 행을 경제성 0으로 치환하면 grid·holdout이 왜곡된다. | 다음 자연일의 동일 record/attempt/parent/leg/order/execution·owner·account·route/session과 실제 비용/clock을 연결하고 원본·유효·제외·격리·미관측, full/partial/open/censored, 비용 후 holdout을 family별로 대사. 결손이면 S6 재수리 후 S7 재측정. |
| 완전한 isolated before/after 출력 root·provider budget 계측 부재 | S7 검증 harness/각 stage owner. 운영 wrapper 직접 실행은 허용 범위 밖. | 원본 clean 데이터 snapshot과 두 코드 세대를 별도 root에 고정하고 모든 stage 출력·lock·provider 호출을 격리하는 명령을 마련한 뒤 동일 원모수·ID·grid·holdout·비용·hash 및 cold/warm 자원 수치를 비교한다. |
| 시험 중 checklist tracked diff 변화 | S7 작업본 관리 owner. status 경로 목록은 같으나 byte diff hash가 바뀌어 완전 불변 run으로 취급할 수 없다. | 다음 replay는 source·code·checklist 전체를 읽기 전용 snapshot으로 고정하고 시작/종료 SHA 일치를 확인한다. |

`S5-FIN-05`는 **새 자연 장후 source date**에서 postclose_exit snapshot profile·세 파일 SHA와 fresh controller→cleanup→detector 시간축 결손이 재현될 때만 별도 S6 수리로 인계한다. 이번 S7은 이를 재현하거나 해결한 것으로 간주하지 않는다. S8은 릴리스 선택·PREOPEN·실제 PID·자연 소비·비용 조정 수익성을 각각 독립적으로 수용한다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포·정규 장후·PREOPEN은 변경하거나 실행하지 않았다.

자가 검토: 저장된 9/23 과거 success/DONE과 현재 terminal·strict 세대를 분리하고, 이벤트·요약 row·주문·leg·완료와 서로 다른 기간의 분모를 섞지 않았다. S7 문서 상대 링크 **18개 모두 존재**, trailing whitespace 0, print-only backlog parser `--print-backlog-only --limit 500` exit 0·현재 32 task 파싱, `git diff --check` exit 0. Python 소스·wrapper는 수정하지 않아 별도 compile/`bash -n`은 이번 S7 문서 변경의 대상이 아니다. 외부 Project/Calendar 동기화는 실행하지 않았다.
