# 기계·보조판정 장후 보완 구현·리뷰: 2026-10-01

## 결정과 경계

작업본 구현과 표적 검증을 완료했다. 새 장후 선택 버전의 실제 활성 경계는 원천 `2026-10-02`다. 이미 정해진 10/2 장중 정책, 프롬프트, runtime selector/PID는 이 작업에서 변경하지 않았다. 배포·재기동·정책 재발행·AI/broker 호출은 실행하지 않았다.

부모 정책/전략의 진입 하드 안전, 가격/수량/계좌/주문/제공자 권한과 기존 owner 경제성 승계 조건은 유지한다. source gap은 zero EV나 수익 기회 없음으로 해석하지 않는다. 역사 표본과 합성 부하 시험은 10/2의 독립 성과를 증명하지 않는다. 기계 계산일은 exact-date 원천 영수증의 target date를 우선한다. 당일 원천 결손이 구 순위 버전으로 되돌아가는 이유가 되지 않으며, 계산한 후보가 회복 자격을 못 얻은 결과는 `no_recovery_qualified_candidate`로 표시한다.

기준 코드는 `ffd2ec8b71bed2d39daede042cff1ab76d1bb18f`이고 격리된 baseline worktree에서 구 버전을 재생했다. 테스트/벤치 입력과 출력은 별도 보존하며 현재 장후 산출물이나 live bundle을 덮지 않았다.

## 구현 소유자

| 접점 | 구현 |
| --- | --- |
| [기계 장후 생산자](../../src/engine/scalping/ai_action_outcome_calibration.py) | v7 학습 선택·86+6+4 배치·회복 union/평균·same-day purge·train 전용 해시·동결 재개·완전 setup cache·날짜별 projection·원천 coverage/감도/후속 부모 ENTER 진단 |
| [기계 선택·발행 계약](../../src/engine/scalping/entry_strategy_policy.py) | 회복 우선 순위, 기존 성공 보존, 검증 회복 ≥3, train/held identity·관측 경계·train hash 검증; 기존 v4/v5/v6 읽기 유지 |
| [보조 장후 생산자](../../src/engine/scalping/compact_auxiliary_paired_replay.py) | v4 학습 1위 동결·영속 선택 파일·같은 prompt 목록·holdout 한 prompt·최대 32 신규 후보·full-cost 행 격리·관측되지 않은 VETO 축 보존·정확 응답 복구·누적 sealed projection |
| [기계/AI 발행기](../../src/engine/scalping/mechanistic_entry_runtime_policy.py) | M1이 먼저 발행되면 M0/A1은 보류하고 M1/A0 보존; 기존 부모 CAS·원자 쓰기·날짜/범위 검증 유지 |
| [공유 순수 검증](../../src/engine/scalping/postclose_entry_validation.py) | 정확 date/symbol/venue/session/promotion identity, duplicate/conflict 격리, 관측기간 purge, 디스크 기반 누적 projection |
| [계약 회귀](../../src/tests/test_postclose_entry_validation.py) / [부하 재생](../../src/tests/benchmarks/entry_postclose_replay.py) | 주문/provider 없는 fixture와 명시 원천·코드 해시의 구/신 버전 비교 |

신규 Python 모듈은 기존 `scalping` 패키지의 오프라인 공유 검증 소유자다. 테스트와 benchmark는 기존 `src/tests` 하위에 배치했다. engine root나 새로운 live 진입 분기를 추가하지 않았다.

## 리뷰에서 발견하고 수정한 결함

1. 학습/검증 전체 해시가 탐색 seed에 섞이고 회복 집합의 성공/실패가 중복되는 문제를 분리했다. 검증 label 변경은 학습 후보를 바꾸지 못한다.
2. 일자 수가 하나일 때의 시간순 독립 검증과 관측기간 purge를 구현했다. identity 없는 promotion을 trace로 대체하지 않는다.
3. 단일 축 회복이 0일 때도 등록된 두 blocker의 결합 완화를 평가할 슬롯을 확보했다. 탐색 cursor/anchor 재개와 기존 readback을 회귀로 확인했다.
4. 재시도 중 보조 학습 1위를 다시 고르거나 부모/학습 원천이 바뀐 선택을 승계할 수 있는 문제를 고쳤다. 일자/scope 선택 파일은 hash·schema·날짜를 검증하고 손상된 기존 파일을 덮어 새 선택을 만들지 않는다.
5. 완전 비용과 마찰비용을 구분하고 식별 가능한 비용 결손 행이 다른 full-cost 행을 막지 않게 했다. 같은 봉 선후 불명, 검열, 정확 stop/owner 미확인을 임의값으로 메우지 않는다.
6. VETO 관측이 없는 PASS-only 자료에서 VETO 전용 문턱을 바꾸는 문제를 막았다. 후보의 VETO→PASS 방향에는 후행 방향 지원이 필요하다. CAUTION은 즉시 checkpoint CF이며 후속 재진입의 운영 EV가 아니다.
7. settlement 뒤 checkpoint 응답이 없을 때 정확 응답 파일만 재사용한다. 예약만 있고 원본 응답이 없으면 해당 변형은 미완료로 남긴다. 기존 ledger의 390회/1 USD와 max_new guard를 우회하지 않는다.
8. 서로 다른 기계 부모를 가진 A1이 M1에 섞이는 경로는 승계를 보류한다. 발행의 부모 conflict는 기존처럼 차단한다.
9. projection census 집계, 없는 gzip 후보 파일 처리, 비용 hash/date/scope/sum 검증, split dependency 초기화, 실제 가격 fetcher 호출 시 incremental 경로 우회 및 과거 날짜에 당일 fetcher 전달 가능성을 수정했다. 원천/비용 파일의 변경 시각·inode/ctime과 producer 코드가 달라지면 해당 projection을 다시 구축한다.
10. 보조 평가의 반복된 부모 policy 직렬화가 20% 성능 상한을 초과했다. 완전 policy 표현이 동일한 경우에만 정규 SHA를 재사용하고 최대 16개 cache로 제한했다. 서로 다른 표현은 정규 hash로 다시 검증한다. 1/1.0·부호·부모 hash를 뭉개는 cache를 쓰지 않는다.
11. 가격/비용 결손인 후속 부모 ENTER_NOW도 판정 관측에는 남긴다. 이 행을 경제성 분모에 넣거나 실제 fill로 간주하지 않는다. 실제 terminal owner가 없으면 `terminal_nonentry_proven=false`다.

## 검증 영수증

- 관련 8개 suite: **729 PASS**, 148.64초. `pandas_ta`의 기존 pandas copy-on-write 폐기 경고 1건; 테스트 실패 없음.
- 최종 코드의 해당 계약 4개 suite와 개별 회귀 파일에서 숫자 문자열 비용·후속 미평가 ENTER·원천 격리를 재검증했다. 개별 회귀 파일 **16 PASS**, 2.20초; 이후 날짜 결손 회귀를 추가한 최종 4개 suite는 **272 PASS**, 25.98초다.
- `compileall`, `git diff --check`, 문서 링크·현재 stable owner·print-only backlog parser는 최종 파일에서 검증한다. shell wrapper를 변경하지 않아 `bash -n`은 생략한다. broad trading suite·실 provider/broker·live 배포·비싼 운영 보고서 재생성은 실행하지 않는다.

```bash
.venv/bin/python -m pytest -q src/tests/test_postclose_entry_validation.py src/tests/test_entry_strategy_policy.py src/tests/test_entry_setup_paired_replay_batch.py src/tests/test_mechanistic_entry_runtime_policy.py src/tests/test_ai_action_outcome_calibration.py src/tests/test_entry_execution_sizing_plan.py src/tests/test_ai_decision_trace.py src/tests/test_postclose_summary_handoff.py
.venv/bin/python src/tests/benchmarks/entry_postclose_replay.py --workspace WORKSPACE --input FROZEN_INPUT --version baseline --family machine
```

benchmark는 `--version new`/`--family auxiliary`로 같은 입력을 재생한다. 각 비교는 별도 프로세스 3회이며 JSON에 wall/CPU/RSS·코드/입력 hash·후보/선정/원천·provider 0·정책 쓰기 false를 기록한다. 역사 샘플의 새 알고리즘 활성 날짜 변경은 benchmark 프로세스 메모리 안에서만 한다. 원천/실행/정책 파일을 수정하지 않으며 생산 코드의 10/2 경계는 유지한다.

## 성능 표본과 한계

- 원천 9/29~30의 감사/capture hash가 정확히 맞는 기계 입력은 **14행**, 보조 frozen 입력은 **44행**이다. 예전 보고서의 400개 case 모두를 새 feature 모집단에 결속했다고 주장하지 않는다. 적은 원천 결속 coverage는 전체 날짜 경제성 비교의 한계다.
- 기계 250행 부하는 이 14행을 서로 다른 합성 trace/promotion으로 반복한 **자원 시험**이다. 250개의 실제 독립 수익 기회나 승계 지원으로 사용하지 않는다. 반복 setup cache의 효과를 확인하며 고유 실제 행에서도 별도 비교한다.
- 보조 44행은 구 버전 10개 가격 진단, 새 버전 9개 진단(시간순 관측기간 purge 1개)이다. 조회 시 검증된 full-cost 결속은 **0/44**였으며 주 비교/정책 승계 근거가 아니다. missing cost를 0으로 채우지 않았다.
- 비용 완전 보조 250행 fixture는 실제 비용 receipt가 아닌 사전 지정된 테스트 계약이다. full-cost 후보 계산의 부하를 별도로 확인하며 `economic_support_forbidden=true`를 입력에 남긴다.
- 학습/후행 기회와 선택은 synthetic 계약 회귀로 검증한다. 기존 pre-AI source-only 경제 recorder/trace는 이번에 새로 쓰지 않고 producer/label/sizing/trace suite로 소비 불변을 검증했다.

성능 합격선은 wall/CPU 중앙값 ≤ 구 버전×1.20, peak RSS ≤ 구 버전×1.10+64MiB 및 기존 절대 guard다. 동일 입력·최종 코드 해시의 3회 별도 프로세스 결과는 아래와 같으며 **네 비교 모두 합격**했다.

| 동일 입력 | wall 구→신 | CPU 구→신 | peak RSS 구→신 (KiB) | 해석 |
| --- | --- | --- | --- | --- |
| 기계 실제 결속 14행 | 26.510→25.390초 | 26.690→25.549초 | 130,796→135,780 | 고유 원천의 후보 재생; 작은 coverage이며 경제 승인 아님 |
| 기계 합성 반복 250행 | 400.832→27.155초 | 400.976→27.332초 | 233,108→242,520 | 완전 동일 setup cache의 부하 효과; 경제 지원 수 아님 |
| 보조 실제 frozen 44행 | 79.374→93.207ms | 79.369→93.209ms | 141,632→141,596 | 상한 +20% 이내; full-cost 결손으로 carry |
| 보조 full-cost 합성 250행 | 155.086→113.030ms | 155.068→113.035ms | 51,188→48,736 | 비용 계약 fixture의 후보 계산 부하; 실제 정책 우위 아님 |

[기계 판독 검증 영수증](../../data/report/entry_postclose_validation/2026-10-01/validation.json) SHA `f2c0ef55b8b576d2df141a589567b5caaf32af2d3462f32fbe7f71efcc77ad10`. 모든 입력/원출력은 `data/report/entry_postclose_validation/2026-10-01`에 보존했다. 구 버전은 동결 baseline 코드, 새 버전은 현재 파일 SHA와 일치함을 확인했다. 같은 비교의 입력 SHA는 6회 모두 같다. 슬롯 상한은 96이며 유효·고유 후보 수는 표본/분기/중복에 따라 다르다. 실제 14행에서는 구/신 각각 92/89, 반복 기계는 90/90이었다. 새 버전이 더 많은 후보를 탐색해 시간을 줄였다는 주장은 하지 않는다.

## 남은 자연 수용과 실행 소유자

[10/2 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 5개 stable OPEN owner를 유지한다. 로직 준비 항목에 이 구현 영수증을 연결하고 완료 표시로 실제 릴리스/원천/PID를 대신하지 않는다.

- PREOPEN owner: 원천 기록 producer와 기존 정확일자 정책/선택 release/PID 일치.
- 기계·보조 LogicReady owner: 새 장후 릴리스 검증 및 처음 보는 전체 10/2 원천의 자원/coverage.
- 각 Postclose owner: 감사→후행 label/비용→선택→발행→summary/strict/controller/finalization의 동일 세대 종결과 실제 다음 거래일 산출.
- 이후 실제 다음 거래일 PREOPEN/PID·native submit/fill/terminal·비용 후 순이익은 별도 영수증이다.

projection raw 재독과 큰 병렬 보관을 줄였지만 재생의 eligible 특징·기회 인덱스·결과는 모집단에 비례한다. 전체 RSS가 상수라고 주장하지 않는다. 자연 전체 입력에서 기존 메모리/시간 보호를 넘거나 비용/부모/독립 지원이 부족하면 그 scope를 carry하고 원인을 보고한다. 보호 기준을 낮추거나 작은 시험을 실제 수익 우위로 바꾸지 않는다.

## 최종 문서·검증 종결

- 최종 코드의 4개 계약 suite **272 PASS / 25.98초**, 기존 8개 통합 suite **729 PASS / 148.64초**, 최종 compile/import 및 diff 공백 검사 PASS다.
- 4개 owning 문서의 파일 링크 검사 PASS다. print-only parser가 27개 항목을 파싱했고 이 변경의 5개 stable ID는 각 1개 현재 owner인 10/2 checklist에만 존재한다. Project/Calendar 동기화는 실행하지 않았다.
- 최종 반복 출력의 새 코드 SHA와 현재 4개 관련 파일 SHA, 같은 비교의 입력 SHA를 대조했다. wall/CPU/RSS 네 비교가 사전 상한을 통과한다. 원출력/입력/검증 JSON은 별도 report namespace에 보존한다.
- 이 리뷰의 코드 수용은 닫혔다. 10/2 자연 전체 원천·장후 소비 릴리스·발행/종결·다음 거래일 PID 및 실제 비용 후 성과 수용은 OPEN이며 코드 시험으로 대신하지 않는다.
