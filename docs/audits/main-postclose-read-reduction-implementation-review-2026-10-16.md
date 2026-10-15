# 장후 반복 원천 읽기 개선 구현·반복 리뷰 — 2026-10-16

사용자 지시에 따라 반복 읽기 개선을 구현했다. **동일 실행 내 원천 digest 공유와 delay 단일 패스 검증이 대상이며, 운영 배포·실제 장후 소요시간 수용은 별개다.** 이전 [의미 점검](/home/ubuntu/KORStockScan/docs/audits/main-postclose-semantic-review-and-repeated-read-findings-2026-10-16.md)의 인계 경보 복구를 영구 수리로 바꾸어 표시하지 않는다.

## 범위와 작업본

기준은 실제 선택 release commit `23a13aba62884a5d3a0d48a3f91ebff4262571f6`이다. 원 작업공간 main `c938ace06`과 코드 기준이 달라, `/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016`, branch `codex/postclose-read-reduction-20261016`에서 구현했다. 기존 source-only release·정책·원천·controller/prepared·현재 체크리스트와 사용자 동시 변경을 보존한다.

위치는 기존 `infrastructure`의 검증 비용 계층, `scalping`의 delay 원천 검증, `automation`의 실제 CLI 진입점이다. 새 engine-root 모듈이나 중복 구현은 만들지 않았다. 두 기존 test 파일을 확장했다. API 요청/응답·실시간 FID·계좌·주문 코드는 변경하지 않았다.

## 구현과 소비 경로

| 변경 | 실제 동작 / 유지한 계약 |
| --- | --- |
| [validation_digest_session.py](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/engine/infrastructure/validation_digest_session.py) | 기존 digest 엔진에 메모리 전용 `postclose` 역할 추가. 프로세스/호출마다 cold, 최대4096항목·600초 비연장 수명. observer/transition disk store를 읽거나 쓰지 않으며 정상/예외 종료에 메모리를 비운다 |
| [postclose_done_controller.py](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/engine/automation/postclose_done_controller.py) | 실제 controller CLI에서 summary→strict→current strict/각 native consumer가 같은 실행의 실제 파일 해시만 공유. predecessor 대기/summary worker dispatch는 원 위치와 의미 유지 |
| [next_preopen_readiness.py](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/engine/automation/next_preopen_readiness.py) | `--prepare`의 native source/terminal/bootstrap 검사 안에서 공유. `--verify`, `--verify-completion` 및 기본 library 호출은 기존 full 경로 유지 |
| [pre_submit_delay_initial_policy.py](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/engine/scalping/pre_submit_delay_initial_policy.py) | compact 파일별 SHA, ordered 전체 SHA, 날짜별 cumulative prefix SHA를 한 스트림으로 계산. descriptor/path의 전후 dev/inode/size/mtime/ctime·실제 byte 수와 마지막 inventory/identity 확인. 원 raw/compact ledger 검증 유지 |

파일 digest만 재사용한다. native validator 판정·정책 선택·기대 SHA 비교·현재 source/discovery·날짜·selector/PID·부재/격리·hard safety 검사는 계속 실행된다. 판정 실패 후 같은 해시가 있어도 다음 의미 검사가 다시 실패하며 PASS를 승계하지 않는다. 파일 교체/append/truncate/ctime 변경·alias/late 입력 유입은 원 currentness 검사에서 검출한다.

부모 observer/transition cache를 postclose에 상속하지 않는다. 같은 root/date/PID의 중첩 호출만 공유하고, fork가 상속한 ContextVar의 원 PID가 다르면 full 경로로 돌아간다. missing root·nonlocal/부적격 저장소는 캐시를 만들지 않고 native 기본 검증을 유지한다. live guard나 provider·수량·cap·원 stage deadline을 바꾸지 않는다.

계측 `validation_io`는 CLI stdout에만 더했다. canonical controller/prepared의 해시 입력은 바꾸지 않는다. 완료한 digest 읽기/재사용량과 thread I/O delta를 구분하며, 프로세스 전체 비용이나 경제성으로 해석하지 않는다.

## 리뷰와 수정보완

1. 1차 구현 뒤 source/ledger·현재성·예외·최종 소비를 검토했다. 기존 표적에서162 PASS/1 FAIL이었다. 실패한 consumer fixture는 수정 전 선택본에서도 동일하게1 FAIL/6 PASS로 재현됐다. current와 consumed 영수증에 같은 파일을 지정해 의도와 다른 consumed 분기를 실행하고 있었다. 해당 fixture에 별도 미존재 consumed 경로를 주어 원 pre-consumption 수용/거부 검증을 복구했다. runtime handoff 검사는 완화하지 않았다.
2. 재리뷰에서 fork의 ContextVar 상속과 missing data root에 대한 신규 cache 진입 실패를 보완했다. PID 불일치 시 full fallback, 없는 root의 기본 경로 보존, 부모 cache 격리/복원, 종료 시 메모리 폐기를 검증했다. 명시적인 observer/transition이 postclose의600초 수명을 상속하지 않도록 역방향 역할 재진입도 격리했다. 의미 판정이 재실행돼 두 번째 호출을 거부하는 CLI 시험도 포함했다.
3. native raw/compact ledger를 실제 seal한 뒤 같은 호출에서 재검사했다. raw 변경·gzip alias 추가·native late 입력·ledger 손상·새 compact partition을 모두 거부했다. 추가 late 시험의 초기 경로 오타는 실제 `_source_part_path`로 교정했으며 runtime guard를 변경해 시험을 통과시키지 않았다. 같은 bytes로 open 직후 파일 교체, ledger 검사 중 이전 compact 변경·symlink·late 유입, 비연장 TTL도 검증했다.

시험은 [delay 회귀](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/tests/test_pre_submit_delay_initial_policy.py)와 [digest/CLI 회귀](/home/ubuntu/KORStockScan-worktrees/postclose-read-reduction-20261016/src/tests/test_validation_digest_session.py)에 있다. 원 실패 로그와 수정 전 재현은 `/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-*-20261016.log`에 보존했다.

## 동일 입력의 읽기량 검증

[재현 스크립트](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-20261016/benchmark.py)는 기준 commit의 원 `verify_source` 함수를 가져와 격리 고정 bytes로 비교했다. [결과](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-20261016/benchmark-result.json)는 다음과 같다.

| 대상 | 수정 전 실제 읽기 | 수정 후 실제 읽기 | 수용 |
| --- | ---: | ---: | --- |
| compact 원천48MiB, 3파일/2날짜 |144MiB·9회 open |48MiB·3회 open | 읽기66.7% 감소, 개별·전체·날짜별 prefix SHA 일치 |
| 같은 native 원천16MiB의3회 byte 검증 |48MiB·3회 open |16MiB·1회 open | 읽기66.7% 감소, full1/reuse2·원 byte_generation 결과 동일 |

페이지 캐시를 제거하지 않았고 wall time은 순서/캐시 영향을 받으므로 읽기량을 주 수용 기준으로 삼았다. production 원천이나 전체 장후 보고서는 재실행하지 않았다. native raw/compact 의미 검사는 위 별도 실제 ledger 회귀로 확인하며, 성능용 stub을 의미 PASS 증거로 사용하지 않는다. 이 수치는 controller 전체600초 이내 여유나 실제 디스크 읽기66.7% 감소를 증명하지 않는다.

## 운영 인계와 검증

[기존 I/O 계획의 운영 계약](../proposals/main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md#장후-cli-실행-내-재사용-보완--2026-10-16)을 함께 갱신했다. 작업본의10/16 체크리스트에는 원 OPEN11개·Acceptance·AUTO 원문을 보존한 채 기존 `DirectFamilyPreopenPolicyHandoff`의 인계 메모를 추가한다. 이는 적용 전 검토 초안이며 운영 작업공간의 봉인된 체크리스트는 수정하지 않는다. 중복 OPEN ID나 새 매매 승인 조건을 만들지 않는다.

최종 검증은 다음과 같다. 중간216 PASS·76 PASS 및 마지막 역할 경계 보완 전280+1640 PASS는 최종 수에 더하지 않는다.

- [최종12개 suite](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-20261016/review-final-tests.log): **1922 PASS**. delay source/selection/partitioned research, digest/CLI/양방향 역할 경계, holding dependency, controller/readiness/finalization 및 strict/bootstrap/intraday handoff 소비 계약을 함께 검증했다.
- 변경한 Python6개 compile, `git diff --check`, 새 링크/owner·체크리스트 AUTO 원문/OPEN11개 단일성, 양 작업공간 print-only parser를 확인한다. [최종 기록](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-20261016/validation.json)이 상태와 보호 파일 대사를 소유한다.

변경 범위의 자체 리뷰 미해결 결함은0이다. 대규모 운영 보고서 재생성·외부 동기화·provider·매매 프로세스 실행은 하지 않았다. shell/wrapper 변경이 없어 새 `bash -n` 대상은 없으며 기존 finalization 계약 시험은 통과했다.

## 남은 수용 경계

이번 수리는 invocation 안의 비용을 줄인다. 별도 프로세스의 finalizer terminal recheck와 준비 작업 사이에서는 첫 full hash를 각각 수행한다. origin subprocess의 독립 검증, compact의 서로 다른 native 의미 검사도 그대로다. 프로세스 간 cache·전체 산출물의 일괄 generation 게시·원 finalization 종료코드 계측·별도 summary 표현 결함은 이 변경에 넣지 않았다.

원 delay 코드 계약에 구현 파일 hash가 포함되므로 새 코드가 이전 준비 정책을 자동 소비할 수 있다고 주장하지 않는다. 실제 적용 시 source/code/date/native handoff를 정상 검증해야 하며 기존 보고서/정책의 원 해시나 code pin을 고쳐 맞추지 않는다. 배포·정규 장후 cold/warm 전체 비용·실제 PREOPEN/PID 소비·자연 주문·비용 후 성과는 미수행이다. 이번 코드 검증이 과거 source gap이나 경제성 결손을 해소하지 않는다.
