# Main 보유청산 공식 비용 원천 보완·통합 배포 리뷰

2026-10-09 KST. 사용자 후속 지시인 공식 키움 원천결손 해소, 반복 코드리뷰·수정보완, 보유청산 포함 미커밋 통합 배포를 수행했다. [초기 구현 리뷰](holding-profit-exit-runtime-and-postclose-implementation-review-2026-10-09.md)의 “공식 수집 원천 미확정·미배포”는 초기 회차의 기록이다. 이번 리뷰는 그 이후의 생산·소비 연결과 배포를 다룬다.

## 원천 재확인과 구현

공식 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`를 22:14:47 KST에 재확인했다. 이 revision에는 `kiwoom_docs`가 없으며, `kiwoom/specs.py`, `_data/kiwoom_api_spec.json`, `core/client.py`, `realtime/decoders.py`, `realtime/schemas.py`, Postman과 공식 portal의 `ka10076`·`kt00015`·`ka10170` 문서를 교차 확인했다. 이전 검토는 이 세 API를 충분히 확인하지 못했다. [공식 확인·원문 해시·실제 조회 근거](../../data/report/holding_profit_exit_deployment/2026-10-09/official-cost-followup-review.json).

- 새 producer [broker_cost_source.py](../../src/engine/lifecycle/broker_cost_source.py)는 장후 lifecycle 소유다. 실서버 계좌 확인 `ka00001`, 특정일 종목별 매매일지 `ka10170`, 결제 거래내역 `kt00015` 매수/매도, 원천일이 당일인 경우 주문체결 `ka10076`을 읽는다. 기존 인증·읽기 예산을 사용하며 주문을 호출하지 않는다.
- 최대 4페이지·유한 재시도·wrapper 180초·원장 4MiB 한도다. 완결 연속조회와 요청 날짜/계좌/실서버/응답을 검증한 뒤 원자적으로 보관한다. 같은 닫힌 원천의 재실행은 조회와 원장 복제 없이 재사용한다.
- 원천은 `data/runtime/holding_broker_cost_sources/YYYY-MM-DD.json`이다. 계좌번호와 인증 정보는 원장에 쓰지 않고 계좌 결속은 해시로 기록한다. 수집 실패는 이전 유효 원천을 보존하고 `source_gap`으로 보고한다.
- 검증된 Main 수탁·모든 체결 leg·수량/대금·유일한 당일 전체 포지션이 일치할 때만 실제 비용을 귀속한다. `kt00015` 거래번호를 주문/체결번호로 간주하지 않고 체결일과 결제 거래일을 분리한다. 원천 합계는 전체 포지션 비용이며 개별 체결에 임의 배분하지 않는다.
- 실제 비용과 configured 추정 비용은 별도다. 혼합 수탁·복수 포지션·익일 보유·부분 배분 미확정은 `actual_cost_unallocated/null`로 남긴다. 수동/퇴역 보유를 Main으로 인수하지 않는다.
- 원천 hash → trade review/census/projection → holding report → postclose manifest와 summary code pin을 연결했다. 비용 정정 또는 새 원천은 과거 캐시 재사용을 거부한다. 후일 결제 자료 재조회는 명시적 `--refresh`이며 자동 과거 보고서 재생성이나 과거 가용 시각 변경은 없다.

실제 10/8 원천에서 SK이터닉스 매수 20주·대금 926,500원·비용 130원을 확인했다. 매도는 0주이며 수동관리 보유이므로 Main 완료 손익으로 사용하지 않는다. 이번 조회의 결제 내역은 비어 있다. 실제 Main 비용귀속 표본 또는 수익 개선이 발생했다고 선언하지 않는다.

## 리뷰·보완·검증

수집뿐 아니라 계좌/소유권·보고서·캐시·장후 wrapper·bootstrap·의미 감시 소비자를 검토했다. 연속조회가 조기 종료됐는데 완결로 인정하는 문제, 앱/계좌 설정 변경 뒤 이전 캐시 재사용, 결제일/체결일 혼동과 중복 거래 식별, 미래 비용의 과거 cutoff 유입, 새 비용 원천에 대한 기존 snapshot 재사용을 보완하고 회귀검증했다. 네이티브 HTTP 처리에는 완결 헤더 수신 metadata만 추가했다.

최종 탐지의 22:36 `ka10080` 인증 경고를 추적하면서 기존 unit test의 HTTP·로그 격리 결함을 발견했다. 일부 mock 없는 보완 조회와 테스트 뒤까지 살아 있는 worker가 실제 HTTP 경로·운영 로그에 도달할 수 있었다. `src/tests/conftest.py`의 세션 수명 기본 HTTP 차단과 세션 전용 로그 root를 추가했다. 명시한 response mock은 그대로 검증하고, mock 없는 요청은 네이티브 transport-failure 경로로 종료한다. 늦게 발견한 conftest에도 실행되는 `pytest_configure` hook을 사용하며 회귀와 별도 1건 smoke 검증을 통과했다. 두 후속 통합 검증에서 운영 키움 로그 SHA/mtime가 변하지 않았다. 기존 경고 기록을 삭제하거나 현재 운영 인증 실패로 재분류하지 않았다. [격리 확인](../../data/report/holding_profit_exit_deployment/2026-10-09/isolated-test-runtime-log-check.json), [늦은 conftest 검증](../../data/report/holding_profit_exit_deployment/2026-10-09/late-conftest-smoke.log).

- 최종 30개 모듈 통합 회귀: 작업본 **2,238 passed / 56.93초**, 최종 불변 릴리스 **2,238 passed / 65.79초**. 두 수치는 같은 회귀군이며 합산하지 않는다. Python multiprocessing 테스트의 기존 fork 경고 1건이 각각 있고 실패는 없다. [작업본 로그](../../data/report/holding_profit_exit_deployment/2026-10-09/isolated-full-integration-tests.log), [릴리스 로그](../../data/report/holding_profit_exit_deployment/2026-10-09/release-isolated-v4-tests.log).
- 변경 Python compile, wrapper `bash -n`, `git diff --check`, 문서 print-only parser를 확인했다. 최종 configure hook 보완 뒤 작업본의 비용 원천 회귀 30건과 늦은 conftest smoke 1건을 추가 통과했다. 전체 매매/경제성 검증이나 자연 실거래 성공을 대신하지 않는다.
- 검토 범위의 미해결 구현 지적은 없다. 혼합/익일 비용 배분과 실제 PID·자연 청산/비용 수용은 위에 명시한 관측·지원 범위다. 초기 정책에 새 경제성 배포 조건을 추가하지 않았다.

## 통합 배포와 원래 날짜 보존

최종 릴리스는 `main-holding-profit-exit-20261009-v4`, commit `70945c53181320d9149ed95167c1e21a42be23d2`이다. v2로 먼저 보유청산·비용 코드를 배포했으며 최종 검증에서 발견한 테스트 격리 결함만 v4에 추가 보완했다. 거래 코드는 v2와 같다. 기존 `main-archive-calendar-20261009-v1` (`9773aefb1fb8`)의 시장원천·약세·archive 수리에 보유청산과 공식 비용 원천을 통합했다. 검증한 35개 runtime/test 파일은 작업본과 릴리스 bytes가 같다. [build](../../data/report/holding_profit_exit_deployment/2026-10-09/build.json), [selector](../../data/report/holding_profit_exit_deployment/2026-10-09/selection-after.json).

10/12 기계·보조 candidate는 내용이 같은 code refresh `5038d3aa4d11e3285f51ea4c876d15ba2d14b48f5502b4ab8a247ac89cb16cc1`로 연결했다. 현재 활성 포인터는 바꾸지 않았고 정책 재선정·AI 연구 호출은 없다. [동일 정책 검증](../../data/report/holding_profit_exit_deployment/2026-10-09/policy-refresh.json).

원 source date 10/8의 trade review와 holding report만 네이티브 builder로 갱신했다. pipeline 원천은 그대로이며 post-sell feedback/missed-entry 결과는 원래 as-of와 SHA를 검증해 재사용했다. 별도 대형 AI 원장을 복제하지 않았다. holding report는 약 1.3MB이며 원 manifest와 영향받은 산출물만 압축 백업했다. [snapshot 검증](../../data/report/holding_profit_exit_deployment/2026-10-09/exit-snapshot-refresh.json).

23:03:48 KST 원 source 10/8의 summary·strict·controller·cleanup·finalization·최종 detector가 종료됐다. 23:04:25 재검증에서 10/12 PREOPEN은 `current_full_contract/pass`, findings 0이다. finalization chain은 `c30b20a239bcdce970280f4ea31c8ceedee7486f2b8e0db13b4a61fa92c37383`이며 `strict_checklist_generation_stale`와 generation mismatch가 없다. 1,072개 runtime 파일의 작업본/배포본 내용이 같고 필수 cron 라우팅 8개도 통과했다. [최종 준비 증빙](../../data/report/holding_profit_exit_deployment/2026-10-09/final-readiness.json), [예약 검증](../../data/report/holding_profit_exit_deployment/2026-10-09/cron-check.json).

10/12의 기존 봉인본·수동 구간은 보존하고 네이티브 builder의 자동 구간만 갱신했다. 예약은 07:35 PREOPEN·07:55 Main이며 휴장일 강제 기동은 하지 않았다. 실제 PID 소비와 자연 청산/비용/수익은 아직 미관측이다.

최종 detector 7개에 fail은 없지만 전체 색상은 warning이다. 기존 작업지시서 미생성·EOD `completed_with_warnings`, 테스트 실행 시각의 8005 기록, 과거 로그가 남는다. detector 내부의 finalization ancestor 대기는 후속 DONE과 원천 generation 대사로 닫혔다. 경고 원문을 삭제하거나 전체 운영 경고가 0이라고 선언하지 않는다. 테스트 격리 보완 뒤 운영 키움 로그는 변하지 않았고 강제 restart 또는 토큰 무효화는 하지 않았다.

## Source Control 정리

완료된 배포 코드 57개를 로컬 commit `ff9c53a5663a5aa3ae00a33294ab517174513d37`로 정리하고, 보유청산·공식 비용 34개를 `fa028f24c5d9e1da1313128c2568fe9ed41e964b`로 정리했다. 겹치는 state handler는 기존 배포 blob을 먼저 커밋한 뒤 보유청산 차이를 별도 반영하여 작업을 유실하지 않았다. [첫 commit 근거](../../data/report/source_control_cleanup/2026-10-09/commit-deployed.json), [보유청산 commit 근거](../../data/report/source_control_cleanup/2026-10-09/commit-holding-cost.json). 테스트 격리는 `72a4b75896dc8291bab19ed2b4106d42db000b38`로 별도 커밋했다. 문서 17개도 링크·현재 owner·print-only parser 검증 후 별도 로컬 commit으로 정리했다. Source Control 잔여 변경은 0개이며 처음 제시된 102개를 버리거나 숨기지 않았다. push·stash·reset·미검증 원천 삭제는 하지 않는다.
