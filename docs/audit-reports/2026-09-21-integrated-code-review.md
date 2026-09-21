# 2026-09-21 당일 수정 통합 코드리뷰

## 범위와 권한

- 사용자 승인: 오늘 수정분의 코드리뷰→결함 보완→재리뷰→배포·재기동. 기준은 `24b2a1ec4^..8299c7131`의 소스/테스트/런처60파일이며, 기존 개별 리뷰의 producer/consumer/cache/실제 실행 경로를 통합 대조했다. 새로운 전략·수량·provider·요청 한도·구독 확대·WS P2/P3 입력 전환은 하지 않는다.
- 검토 시작 배포본은 `34e77146c`, 메인PID141501, read-only 수집기5개이다. 위젯 주문 owner PID75952/삼성25주 custody 및 episode executor는 이번 보완의 수정 대상이 아니다. 관련 없는 생성자료 `data/threshold_cycle/date=2026-09-21/`를 보존한다.
- 기존 운영 근거: [자금/제출/중복조회 수리](2026-09-21-preflight-submit-bottleneck-repair.md), [WS 비교 수집](2026-09-21-widget-shared-ws-transport-review.md). 회귀 성공은 자연 자금 증거/주문/경제성 완료가 아니다.

## 통합 검토와 보완

| 경로 | 검토한 계약 | 이번 판정/보완 |
| --- | --- | --- |
| 기동·정책 인계 | exact date/hash, operator override, protective baseline, 실제 PID receipt, prepare/commit/abort | 마지막 tmux 세션 종료 직후 서버 소멸 경합 보완 |
| 기계/경제성 증거 | 동일 attempt/route, legacy·async 준비, 계좌/잔고 세대·2초 증거, 날짜형 직렬화, 정책 캐시 | 기존 연결 보존; 부족한 자금 원천은 OPEN |
| 감시·위젯 custody | 과거 결손/현재 재발 분리, 실패 사건 exact hash, incumbent 보존, 보유/주문 owner | 과거 결손·보유·안전 veto를 복구/경제성으로 승격하지 않음 |
| REST/WS 시장자료 | 원 시계·만료·token/route/body, 정상 요청 제한, fork·cross-process, 비교 전용 WS | 손상 캐시 예외 및 boolean epoch 허용 결함 보완 |

1. **감독 세션 재생성 경합:** 직전 승인 배포에서 `server exited unexpectedly`가 발생한 실제 사건을 보완한다. child drain 이후 최대3회, 간격1초로 세션 생성을 시도하되 매번 메인 child와 같은 tmux 세션이 모두 없는지 확인한다. 실패 후 세션/child가 나타나면 재생성을 거부하고 기존 종료·handoff 검증을 유지한다. 신규 강제 kill, 중복 bot 시작 또는 무제한 재시도는 없다. Bash mock으로 첫 성공/서버 종료 경합/3회 소진/부분 생성/기존 child를 실행 검증한다.
2. **선택 캐시 손상 격리:** 크기가 작아도 깊게 중첩된 JSON은 `RecursionError`를 내므로 read cache miss로 처리한다. 저장 직렬화의 같은 예외는 정상 원응답을 보존한다. 실제 fetch 예외는 숨기지 않으며 fallback에도 기존 공유/로컬 제한이 적용된다. 직렬화 회귀는 Python 버전별 재귀 한도 차이를 피하도록 해당 예외를 명시 주입한다.
3. **WS 세대 타입:** `True == 1` 때문에 종목 epoch가 boolean인데도 비교 증거로 수용될 수 있었다. producer/field와 동일하게 종목 epoch도 정확한 정수형만 허용한다. 잘못된 증거는 `source_gap`; 기존 REST 입력은 바뀌지 않는다.
4. **기존 테스트 계약2건:** `d7b2d3807`(9/18)에서 폐기한 dedicated recheck 플래그 기대값을 미생성 검증으로 정정했다. 9/20까지 보완된 장후 wrapper의 날짜 검증 및 시작/종료 handoff 호출을 전체 순서 기대값에 포함했다. 테스트를 맞추기 위해 폐기 runtime을 복구하거나 handoff를 생략하지 않았다.

공식 upstream HEAD 재확인: `2026-09-21T03:13:43.694810+00:00`, `953e5dbff123f437ab4d11a78a95191a685eb51f`로 동일. 같은 세션에서 확인한 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime`, packaged `kiwoom/_data/kiwoom_api_spec.json`의 ka10001/ka10004/ka10080·0B/0D 및 PRD/MOCK Postman 근거를 재사용한다. 해당 revision의 `kiwoom_docs` 부재를 보존한다. 이번 추가 변경은 local cache 예외와 checkpoint epoch 타입 검증이며 wire/FID/auth/REG/REMOVE/continuation/account/order 의미를 바꾸지 않는다.

## 검증·배포 절차

- 최초 통합 회귀: 2,612 PASS / 기존 기대값 불일치2 FAIL. 보완 후 동일 통합 범위와 추가 경계 회귀를 재검증하며 최종 결과와 배포 receipt는 아래에 기록한다.
- 최종 통합 회귀 **2,622 PASS**(236.87초), 추가 경계3-suite **122 PASS**, 재귀 예외 주입 보강 후 cache/control **49 PASS**. 세 실행은 겹치는 테스트를 포함하므로 합산하지 않는다. Python compile, Ruff F/E9, Bash 문법 및 diff 검사, print-only checklist parser PASS. pandas/fork 기존 경고4건을 보존했다. 재리뷰 결과 위 범위의 미보완 finding0; 테스트 실패를 숨기거나 운영 guard를 바꾸지 않았다.
- 운영 배포는 검증된 immutable release만 선택하며 메인 guarded restart 및 해당 reader를 사용하는 기존 read-only 수집기5개를 갱신한다. 수집 주기10/10/10/1/60초와 모든 다른 service 환경은 유지한다. 위젯/episode 주문 프로세스는 불필요하게 재시작하지 않는다.
- 백업/receipt: `/home/ubuntu/KORStockScan/tmp/integrated-review-deploy-20260921-CyGiuu`. 직전 main selection과 교체할 정확한 collector override를 보존한다. 롤백 시 그 selection/override만 복원하고 기존 guarded restart를 사용한다. 기존 drop-in·보유·원천/실패 이력은 삭제하지 않는다.
- 새 PID 소비·당일 bootstrap·정상 scheduled health·자연 수집을 별도로 확인한다. 재기동 전후 WS process-local 분모를 합산하지 않는다. 다음 완전한3×15분 창을 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`가 소유한다. 자금 결손과 같은 시도 자금/정책/계획 연결은 기존 `SubmissionBottleneckMonitorNatural0921` 및 main source owner에서 OPEN을 유지한다.
- 비수행: 실주문/수동 broker·provider probe, 광범위 장후 재생성, 외부 Project/Calendar sync, 한도·정책·hard safety 완화. 전체 저장소 전수 테스트가 아닌 오늘 변경 및 직접 영향 범위를 검증한다.
