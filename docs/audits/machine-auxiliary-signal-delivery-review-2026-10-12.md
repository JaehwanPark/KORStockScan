# Main 기계·보조판정 전달 및 관측 보완 — 2026-10-12

## 현재 상태와 범위

사용자 승인: 기계/보조판정 결함 보완, 코드리뷰·수정 반복, 배포 및 재기동. 조사 시작 시 선택 릴리스는 `reversal-source-diagnostic-20261012-v2`, PID `851809`로 이미 복구돼 있었다. 과거 PID `815646`의 33건과 PID `841700`의 관측 오류를 현재 PID 결과로 합치지 않는다.

원천은 제한된 runtime performance 로그 tail, 기존 정확 PID 증빙 및 현재 생산자/소비자 코드다. 이번 작업은 Kiwoom/OpenAI 호출, 주문, 과거 JSONL 재작성, 정책 튜닝 또는 장후 전체 재생성을 직접 실행하지 않는다. 승인된 정상 Main 재기동 이후의 자연 동작은 구분해 기록한다.

## 재현 및 수정

1. 관측 큐는 유한 JSON 바이트만 수용하지만 deferred scanner skip 경로는 `received_types` set, 캐시 객체, 긴 이력을 포함하는 WS 객체 전체를 전달했다. 동일 구조로 admission 실패를 재현했다. skip 관측 소비자가 사용하는 현재값·수신 종류·시각·strength 이력의 전체 개수와 시각·정확한 0D 경로 증빙만 전달한다. 관측 필드/BBO 결과 일치와 실제 큐 drain을 검증했다. 실행 WS 스냅샷과 원 시각/route/deadline은 변경하지 않는다. compact stock에서 빠졌던 code/status도 보존한다.
2. 상시감시 WATCHING이 일반 WATCHING 순위로 스캐너 RECOVERY/HEAVY_EVAL 뒤에 놓였다. 주문·실보유·scanner COMMIT/FAST_PRECHECK 우선순위를 유지하며 상시감시를 무거운 스캐너 작업 앞으로 이동했다. 정렬 이후 deferred heavy flush가 다시 앞지르던 경로도 차단했다. 모든 기존 대상 수와 객체를 보존한다. 이 변경은 claim을 미리 생성하거나 5초 기한을 연장하지 않는다.
3. native claim 검증 실패 뒤 표시용 KRX와 요청용 SOR를 비교해 최종 소비 원인이 `venue_conflict`로 덮였다. native 원거부를 별도 보존하고, 기한·세대·상태 검증 뒤 해당 원인으로 거부한다. 유효한 경로의 quote/position/order/cooldown 검증은 그대로다. 과거의 기한 만료나 반전 무효화를 복구한 것으로 처리하지 않는다.
4. 관측 큐의 다른 결손이 남으면 값 없이 callback·필드 경로·자료형을 유한 범위에서 남긴다. 임의 객체 문자열화, NaN 허용 또는 queue 한도 해제는 하지 않는다. 정책 준비는 load/릴리스 검증/consumer 검증으로 시간을 분리해 다음 자연 표본에서 실제 지연 구간을 확인한다. 검증 결과나 기계/AI 결정을 캐시해 통과시키지 않는다.
5. v1 PID `908171`의 자연 큐 기록으로 실제 반복 경고의 직접 생산자를 특정했다: `main_custody_checkpoint.publish`, `unverified_open_order_codes` set. 계좌 체크포인트가 set→list 변환을 큐 통과 이후 writer에서만 수행해 admission이 먼저 실패했다. enqueue 전에 동일 정규화를 수행하고 nested inventory 복사·모든 미확인 주문 code·성공 exchange 집합을 보존한다. 원 계좌조회/주문 API, custody 판정, registry generation 및 source-gap 조건은 변경하지 않는다. real/Main/retired owner 조합을 실제 bounded queue→native writer→consumer로 추가 검증한다. v1의 WS projection 수정만으로 반복 경고가 해소됐다고 주장하지 않는다.

## 리뷰와 검증

- 기존 소유 모듈 및 기존 테스트만 수정했다. 새 engine-root 모듈은 없다.
- 관련 회귀 927건 통과, 배포/인계 회귀 227건 통과. 기존 pandas 경고 1건 외 실패 없음. Python compile과 diff 검사는 별도 완료 증빙에 기록한다.
- 전달 순서, 일반 scanner 동작 유지, 정확한 관측 필드/0D/transport epoch 보존, 유한 큐, 원 거부/기한 우선순위, stale·source·generation 및 PID 검증 경계를 리뷰했다.
- 제출지연 정책과 원 PREOPEN 세대를 재발행하지 않는다. 코드 인계 검증에 이번 리뷰의 원본/후속 파일 SHA256 쌍만 등록했다. 임의 파일 또는 큰 runtime 함수 전체를 허용하는 예외를 추가하지 않았다. 바이트 변경·dirty release·원 계약 해시 불일치는 재검증 실패다.
- 후보 코드 호환성 검사는 Main 종료 전에 실행한다. 승인된 ordered deploy가 이전 Main/launcher 정상 종료 → selector/checklist 게시 → 준비 → 새 PID 소비를 수행한다. 실패 시 기존 hold/custody 계약을 유지한다.
- v1 자연 검증의 미해소 발견 이후 계좌 체크포인트 보완 회귀 163건을 추가 수행했다. Main/retired custody를 유지하고 미확인 주문 code를 제거하지 않으며, 비동기 큐 실패를 성공으로 간주하지 않는다. 최종 v2 검증은 완료 증빙으로 대사한다.

## 수용 경계와 근거

현재 PID의 `expired_before_claim` 집계만으로 과거 33건 모두가 CPU 전달 지연 때문에 만료됐다고 확정할 수 없다. 첫 반전 무효화로 먼저 ready에서 제거됐을 가능성도 있다. 과거 원천은 그대로 보존한다. 단위/회귀 통과는 자연 신호→claim→AI 응답 또는 주문 효과의 입증이 아니다.

자연 수용은 동일 신규 PID의 관측 queue 성공/실패, warm loop, selected native/claim 및 AI 표본으로 확인한다. 신호가 없으면 자연 AI 성능은 미관측으로 남긴다. loop 지연 전체 해소·경제성 개선을 선언하지 않는다.

근거 디렉터리: [검증 및 배포 증빙](../../tmp/machine-auxiliary-signal-delivery-repair-20261012/). 최종 릴리스/PID, 보호 산출물 해시, 기동 검증 및 자연 표본은 이 디렉터리의 `completion.json`에 기록한다.
