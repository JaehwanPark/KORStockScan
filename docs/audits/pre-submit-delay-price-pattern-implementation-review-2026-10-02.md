# 첫 제출 시점 가격 패턴 계산 구현·반복 리뷰 수용

기준일: 2026-10-02 KST. 판정: **추가 리뷰·보완·불변 배포·승인 재기동·Main PID 소비 수용 완료**. 자연 가격 분석 산출물 수용: `not_observed`.
소유자: [당일 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 `PreSubmitDelayPricePatternRemediation1002`.
설계: [가격 패턴 계산 보완구현 계획](../proposals/pre-submit-delay-price-pattern-calculation-remediation-plan-2026-10-02.md).

## 결과와 범위

고정된 기계 `ENTER_NOW`, 보조 `PASS/CAUTION`, Main 최초 진입 기회의 0초 최우선 매도호가와 30/60/120/180초 호가를 직접 짝지어 `(P0-Pd)/P0*10000`을 계산한다. 실제 제출·broker 접수·체결·청산·비용·제출 terminal 없이도 유효 pair의 가격 분석을 완료할 수 있다. 결손 horizon은 해당 pair만 제외한다. 계획수량 전량을 채울 잔량을 요구하지 않으며 최우선 호가 가격 비교라는 의미를 유지한다.

`price_pattern_analysis`는 개선·악화·동일 건수, coverage, 기회별 bp 평균·median·p10/p90, cap 초과 진단, frozen venue/session/tick type과 spread 예시를 제공한다. 검증 가능한 원 기회는 최초 적격 retry만 보존하고 시간순 70/30 분할·관측 구간 purge를 적용한다. learning 공통 pair 집합에서 비교 후보 하나를 고정하고 validation 가격으로 재선정하지 않는다. `selection.validation_statistics`는 고정 후보의 validation pair만 사용한 coverage·평균·median·p10/p90이며 summary Markdown에도 검증 상태·pair 분모·tail을 표시한다. 원 기회 identity가 불명인 행도 가격 통계는 계산하며 강한 패턴 검증에서 제외한다.

가격 분석의 `computed/partial/valid_empty/source_gap`, 연구 추천과 기존 경제성·운영 terminal·정책 상태를 직접 summary/감시에서 구분한다. section/source/report/policy 결속과 의미 계약을 검증한다. 기존 비용 후 EV 필드는 null, runtime 정책 선정은 원 계약을 유지한다. 가격 연구 추천은 positive-delay env나 주문 권한을 만들지 않는다. 실제 fill/청산/경제성을 가격 계산의 종결 조건으로 추가하지 않았다.

| 변경 owner | 구현 경계 |
| --- | --- |
| [scalping 계산 생산자](../../src/engine/scalping/pre_submit_delay_tuning.py) | 같은 intent의 P0/Pd, 기회 중복, 통계·시간순 검증·새 section·공유 projection. 2026-09-29 이후에만 section을 추가한다. |
| [runtime summary](../../src/engine/runtime_approval_summary.py) | 가격 분석 상태·분모·연구 추천을 별도 소비·출력하고 잘못된 section을 검출한다. |
| [의미감시](../../src/engine/monitoring/submission_bottleneck_monitor.py) | 독립 가격 projection과 invalid 경보, 제출 함수 terminal 명칭·호환 필드의 의미를 명시한다. |
| [장후 handoff](../../src/engine/automation/postclose_summary_handoff.py) | 기존 report/policy/date 결속에 새 section의 의미 검증을 연결한다. |
| 기존 producer/consumer tests와 owning 문서 | 원천 결손·선택 누출·권한·legacy 반례, traceability/runbook/checklist 계약을 함께 검증한다. |

새 engine-root 모듈·CLI·wrapper·cron·provider 호출·원천 수집기는 만들지 않았다. Kiwoom request/parser/FID/REG/REMOVE/recovery는 이 변경에서 수정하지 않았다. 작업 시작 시 존재한 별도 계좌 여력·주문 관련 수정은 보존했고 이 수용 범위에 포함하지 않는다.

## 반복 리뷰와 보완

| 검토 | 확인한 결함 또는 경계 | 보완·재검증 |
| --- | --- | --- |
| 계산/표본 리뷰 | 서로 다른 가격대의 평균 호가 차이, P0 결손, 불완전 horizon | 같은 기회의 bp 평균·분모·분위수, P0 필수·horizon별 격리, cap/depth 진단을 손계산 반례로 확인했다. |
| 중복/누출 리뷰 | retry를 새 기회로 계산하거나 후행 source가 좋은 retry를 고를 위험 | 원 machine identity와 날짜/부모/route/session별 최초 commit을 보존한다. 불명 identity는 계산을 보존하고 검증에서 제외한다. |
| 선택 리뷰 | 후보마다 다른 learning 분모, validation 재선정·관측 구간 겹침 | 공통 learning pair·단일 후보 동결·시간순 split/purge를 적용하고 validation 2위가 더 좋아도 재선정하지 않는 반례를 확인했다. |
| consumer/호환 리뷰 | 과거 보고서 변형, 하위 그룹 권한·분모·선택 상태의 모순 | 과거 날짜의 section 추가를 제한하고 legacy projection을 유지한다. 새 section의 hash·date·authority·count·finite metric·선택 방향을 직접 검증한다. |
| 빈 원천 리뷰 | orphan quote만 있는 원천을 적격 기회 0인 정상 빈 원천으로 처리할 위험 | 검증된 empty ledger 또는 명시적 비적격 commit이 있을 때만 `valid_empty`; orphan-only는 `source_gap`으로 유지한다. |
| 최종 보완 | 반올림으로 선택 방향이 바뀌는 표현, bool 0초 horizon, 새 계산 시간 누락 | 선택 판정에는 반올림 전 평균을 기록하고 의미 모순을 검출한다. bool horizon은 P0로 받지 않는다. 보고서 elapsed에 가격 계산을 포함한다. |
| 최종 계획 대조 | validation coverage/tail 누락과 실제 기회 수를 넘는 검증 표본 count | 고정 후보의 독립 validation 통계를 추가하고 summary/감시에 전달한다. learning+validation+purge+identity 제외 count를 전체 기회 수와 대조하며 validation 통계·선택 평균의 모순을 거부한다. |

보완 후 producer→stage→summary→monitor와 기존 bootstrap/정책 승계의 영향 경로를 재검토했다. 검토 범위의 미해결 구현 결함은 0건이다. 이 판정은 아래 fixture·계약·자원 검증 범위에 한정된다.

## 최초 구현의 표적 검증

가격 계산·검증의 최종 실행 결과: **423 PASS / 15.05초**. 변경 전 기존 4개 영향 suite는 286 PASS였으며, 최종 실행은 consumer·bootstrap·strict/checklist까지 7개 suite로 확대했다. 이후 summary Markdown의 검증 상태·분모·tail 표시에 대한 영향 suite를 다시 실행해 **32 PASS / 1.30초**를 확인했다(423개에 포함된 suite이며 별도 고유 test 수로 더하지 않는다).

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  src/tests/test_pre_submit_delay_tuning.py \
  src/tests/test_runtime_approval_summary.py \
  src/tests/test_submission_bottleneck_monitor.py \
  src/tests/test_postclose_summary_handoff.py \
  src/tests/test_runtime_policy_bootstrap.py \
  src/tests/test_verify_threshold_cycle_postclose_chain.py \
  src/tests/test_build_next_stage2_checklist.py
```

손계산 +50/-50/0bp, 다른 가격대의 기회별 평균, p10/p90, terminal 0건·depth 1/계획수량 500, P0·horizon 결손, route/epoch/clock/hash/conflict, earliest retry, unknown identity, 공통 learning 분모, 독립 validation과 purge, 즉시 방향/동률/반전, rehashed 의미 모순, legacy/date/report-policy 결속, summary/monitor의 독립 상태와 runtime env 미발행을 확인했다.

최초 수정 Python 7파일의 `py_compile`은 PASS였다. `ruff --select F,E9` 차등 검토에서 신규 finding은 0건이었다. 최초 해당 검사에는 handoff `_stage_main`의 기존 unused `os` import F401 1건이 남았고 `git show HEAD`에서도 동일하게 재현됐다(원 1919행, 변경 후 1921행). 이 선행 lint 결함은 후속 추가 리뷰에서 제거했으며 최신 결과는 아래 배포 수용 기록을 따른다.

문서 link/owner/권한·`git diff --check`는 PASS다. 기존 runbook의 `YYYY-MM-DD` 산출물 경로는 원문에도 있는 template link로 구분했고 신규 missing link는 0건이다. print-only parser는 PASS이며 현재 checklist에서 `PreSubmitDelayPricePatternRemediation1002`를 정확히 1개 파싱했다. 원천 계측 wrapper를 변경하지 않아 `bash -n`은 해당하지 않는다. provider/계좌 호출, trading-process restart, 전체 거래 suite, 현재 원천의 비싼 보고서 재생성, 외부 Project/Calendar sync는 실행하지 않았다.

## 고정 입력 자원 수용

기준 코드 저장본의 HEAD 문맥은 `1930ac82393a6c5e02fa7aeaf8e569eb01f5d576`이며 producer SHA256은 `7b3d00e6fa406fd418beb7dd4ae34a0c594e2943cd6224287c5374d6b61bbac0`이다. 최초 코드 수용의 producer SHA256은 `0da4693c5ec91d7bf7ec1edb3b841a3260e9b7f9b0465c32513a23595ed0ed2b`다. 실제 시장 원천이나 생성된 정책을 성능 입력으로 사용하지 않았다.

기존 `_price_pattern_fixture`로 2026-10-02의 512개 고유 기회를 만든 고정 입력이다. 간격은 `index*10`초, 각 호가는 `0:10000, 30:9950, 60:10050, 120:9900, 180:9980`, 나머지는 fixture 기본값이다. commit+5호가 총 3,072 events, 3,368,676 bytes, 파일/source SHA256은 `c94d3c6793031a7723e09cd212348462f3a6646195ccb68ab82f5f65e8812f99`다. 실제 주문·terminal·fill/청산 event는 없다.

서로 분리된 `.venv/bin/python` subprocess에서 baseline/candidate를 번갈아 각각 3회 실행했다. 측정 구간은 동일 입력의 `build_report('2026-10-02', effective_date='2026-10-05', write=False)`다. wall은 `perf_counter`, CPU는 `process_time`, RSS는 process `ru_maxrss`로 측정했다.

| 자원 | baseline 중앙값 | candidate 중앙값 | 결과 |
| --- | --- | --- | --- |
| wall | 0.161343초 | 0.172655초 | ×1.07011, ≤1.20 PASS |
| CPU | 0.159814초 | 0.172651초 | ×1.08033, ≤1.20 PASS |
| max RSS | 44,368 KiB | 45,232 KiB | +864 KiB; 한도 114,340.8 KiB PASS |

세 실행 모두 source hash·3,072 events·horizon별 기존 quote coverage `[512,512,512,512,512]`가 일치한다. candidate의 유효 지연 pair는 2,048개이고 실제 정책 `selected_delay_sec`는 양쪽 모두 null이다. 기존 64MiB compact decode 상한과 읽기 경로를 유지한다. 신규 통계의 비용을 포함한 엔지니어링 자원 수용이며 자연 경제성 개선 수치가 아니다.

측정 당시 임시 작업 폴더는 `/tmp/korstockscan-pre-submit-price-20261002-baseline`과 `/tmp/korstockscan-pre-submit-price-20261002-benchmark`다. 저장 코드·worker·입력·6회 수치는 이 폴더에 있으며 위 SHA/입력 구성/중앙값을 영구 근거로 남긴다. 임시 파일의 보존을 배포·자연 영수증으로 가정하지 않는다.

## 남은 수용과 종결 경계

최초 코드 수용은 완료이며, 실제 거래의 체결·청산을 기다리지 않는다. 최초 코드 수용 단계에서는 배포/재시작·현재 release/PID 검증·자연 원천 보고서 생성·정책 선정·실현 순익 수용을 실행하지 않았다. 후속 사용자 승인 배포는 아래 추가 리뷰 기록을 따른다.

단일 OPEN owner `PreSubmitDelayPricePatternRemediation1002`는 후속 자연 산출물 수용을 소유한다. 다음 변경된 자연 generation을 정상 장후 경로가 만들면 해당 날짜의 source ledger와 새 section/report/policy hash, stage 검증, 직접 summary/monitor의 가격 분석 projection을 한 번 대조한다. 유효 pair가 있으면 `computed/partial`의 분석 수용을 닫을 수 있고, 검증된 비적격 모집단은 `valid_empty`다. 자연 표본 부재는 `not_observed`, 필수 원천 결손은 해당 source ledger/commit/P0/Pd owner·artifact·closure test를 명시한 `blocked`다. 동일 결손 입력을 반복 재생하지 않는다. 가격 추천의 자동 적용은 이번 구현의 수용 조건이 아니다.

## 추가 리뷰·보완과 승인 배포 수용

사용자가 후속으로 결함 해소까지 반복 코드리뷰·수정보완, 배포와 재기동을 명시 승인했다. 실제 Main PID 2948449와 선택 릴리스 `c61fefcfb8f0d5e4b6933fcd49ed0fb768fd53e0`를 확인했다. 이 부모의 계좌 원천 조회 보완은 유지하고 이번 가격 분석의 7개 source/test와 owning 문서만 격리한다. 원 workspace의 별도 변경을 일괄 커밋하거나 이전 HEAD로 runtime을 되돌리지 않는다.

추가 리뷰에서 rehashed 0초 control의 비영 값, bool horizon grid, 순서가 뒤집힌 quantile, 중복 후보와 후보 밖 comparison이 소비 검증을 통과할 수 있는 의미 계약 결함을 확인했다. 해당 통계·후보 계약을 보완하고 5개 반례를 추가했다. 변경된 handoff 모듈의 기존 unused `os` import도 제거했다. producer→직접 consumer→정책 loader·native restart handoff를 재검토한 뒤 영향 9개 suite **523 PASS / 15.89초**, F/E9 **0 findings**, 수정 Python compile PASS를 확인했다. 검토 범위의 미해결 구현 결함은 0건이다.

최신 producer SHA256은 `463fe4dedee02a899a1acb9aea5cdda8a435cc2cceac57c06b2b38a5f98c6ec1`이다. 동일 512기회·3,072 events 입력을 baseline/candidate 각 3회 재측정해 source/quote coverage·2,048 pair·runtime selected delay null을 보존했다. wall/CPU 중앙값은 0.159128/0.159008초에서 0.173917/0.173760초(×1.09294/×1.09277), RSS는 44,376→45,084 KiB(+708 KiB)로 수용 기준을 통과했다.

배포 전 당일 native bootstrap PASS·PREOPEN/prepared의 5개 봉인 파일, 독립 service pin 416개·cron·단일 ubuntu Main을 직접 대조했다. 현재 선택 릴리스를 부모로 격리 후보를 만들었고 **523 PASS / 16.98초**, compile·F/E9·shell syntax·문서/link·parser·diff를 검증한 뒤 이번 범위 12파일만 커밋했다. 공유 경로의 원 checkout bytes는 task별 backup에 보존했다.

| 배포/소비 gate | 직접 근거 |
| --- | --- |
| 불변 release | `820c7c427a74cc06fc03c21ad1052c8eb525ade3`, `/home/ubuntu/KORStockScan-runtime-releases/pre-submit-price-pattern-20261002-820c7c42`; 이 root **523 PASS / 20.42초**, source clean·source/test bytes 일치·compile/F/E9/shell syntax PASS. 부모는 `c61fefcf`이며 기존 계좌 원천 조회 수리를 보존했다. |
| Native 준비/재기동 | same-date policy-preserving handoff prepare PASS 후 **ubuntu**의 기존 `deploy/run_runtime_release.sh restart`를 사용했다. old PID 2948449 정상 종료 후 drained tmux supervisor를 교체했고 19:48:40 당일 runtime env verify PASS를 확인했다. |
| 실제 Main 소비 | PID **2957878**, supervisor **2957835**, start ticks **55895143**, UID 1000·단일 Main·tmux `bot`, cwd는 새 root의 `src`다. runtime/launcher commit 모두 `820c7c42`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`, native consumed receipt의 `actual_pid_consumed=true`다. |
| 정책/운영 보존 | 정책·PREOPEN/prepared 5파일의 SHA, 독립 pin 416개, ubuntu/root cron hash, selector UID/GID·0600 모두 before/after 동일. release-set PASS·Main PID binding 일치, Episode instance 122개와 cron router 8개를 확인했다. 독립 owner 서비스는 재기동하지 않았다. |
| 건강/WS | 19:53:22 ProcessHealthDetector **PASS / All processes and threads healthy**. 새 PID의 main/thread heartbeat를 확인했다. 교체된 tmux pane에서 WS 연결 성공·LOGIN 응답 확인 각 1개, 첫 실시간 0B 5개·0D 20개 수신을 확인했다. raw packet/token은 증거에 복사하지 않았다. |
| 직접 감시 소비 | 19:50:36 정기 monitor에서 새 `submit_call_terminal_count`·terminal 의미·가격 projection을 확인했다. 기존 report에는 section이 없어 `not_evaluated_legacy`다. monitor 전체 `unobservable`/`missing_stale_or_noncurrent_sentinel_evidence`(19:45 Sentinel 원천)는 그대로 보존한다. 이 관측을 가격 분석 성공·전체 원천 정상으로 바꾸지 않는다. |

Runtime 증거는 `data/runtime/startup_readiness/2026-10-02/pre_submit_delay_price_pattern_review/`의 `before.json`, `after.json`, `prepare.json`, `bootstrap.{before,after}.json`, `native-handoff.{verify,consumed}.json`, `release-set.{before,after}.json`, `process-health.json`, `ws-observation.json`, `scheduled-consumer.json`, `restart.log`다. 불변 코드 검증은 `tmp/pre-submit-price-pattern-release-review-20261002/immutable-validation.txt`, 원 shared checkout은 같은 task directory의 `release-checkout-shared-backups`에 보존했다.

이 수용은 코드·배포·Main PID/기존 정책 소비와 정상 운영 재개를 증명한다. 수동 broker/API/AI 호출·정책 재계산·provider/threshold/수량/가격 guard 변경·Project/Calendar sync·장후 보고서 재생성은 실행하지 않았다. 승인한 봇의 정상 초기화와 자연 WS 수신은 발생했다. 새 자연 가격 보고서와 경제성은 `not_observed`로 남기며 정상 장후 stage의 변경된 generation을 기존 단일 OPEN owner가 한 번 대조한다. 감시 원천의 stale 결손은 기존 Sentinel 원천/감시 owner에서 새 정상 snapshot으로 확인하고 동일 결손 보고서를 반복 재생하지 않는다.
