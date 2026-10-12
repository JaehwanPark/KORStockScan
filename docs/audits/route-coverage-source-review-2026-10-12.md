# 경로 커버리지 원천 분류 보완 — 2026-10-12

## 범위와 재현

사용자 승인: 남은 경로 커버리지 경고 해소, 코드리뷰·보완, 배포 및 재기동. 시작 시 선택 릴리스는 `machine-aux-delivery-20261012-v2`, Main PID `920532`다. 인용된 PID `851809` 결과는 과거 근거로 구분한다.

14:01 감시 보고서는 SOR 경로 53건/기계평가 0건을 이유로 `machine_probe:coverage_degraded:krx_nxt_integrated`를 냈다. 이후 같은 PID의 14:02:11~14:07:07 원천 42건을 16MiB 이내 tail에서 동결했다. 이 42건은 전체 10분 모집단이 아닌 동일 입력 재현용 코호트다.

- 9건: 정확한 SOR 체결·호가와 native scope/family/epoch/sequence가 있고 등록 branch 전부 FALSE. 기계·AI 호출 없이 관측을 정상 종료했다.
- 3건: native 관측기간이 부족하고 UNKNOWN branch가 남았다.
- 30건: route snapshot 없음 14, 오래된 0B 12, 0B 없음 4. 미수신/체결 희소 관측이며 증권사 API 결함으로 단정하지 않는다.

기존 감시기는 패턴 충족 이후의 `assessed`만 수신 커버리지 성공으로 계산했다. 이 때문에 정상적인 패턴 부재를 원천 부족에 합산했다.

## 수정 계약

1. 원 `probe_route_assessed_counts`를 보존하고, 별도 `probe_route_source_covered_counts`에 유효 capture가 있는 기계평가 또는 정확한 native 전부 FALSE 증빙만 더한다. `probe_route_native_no_match_counts`로 기여도를 구분한다. 기존 10건·20% 경고 기준은 유지한다.
2. native 증빙은 schema/role, symbol/item/route/venue, 생산 PID/start ticks, 발생시각, family/scope hash 형식, branch truth, epoch/sequence, 정확 체결·호가 수신을 검증한다. UNKNOWN, 결손, 다른 경로·PID, 잘못된 시각/해시, ready 신호는 정상 부재로 처리하지 않는다. Python literal로 직렬화된 기존 필드는 8KiB 이내에서 안전하게 해석하며 신규 원장을 만들지 않는다.
3. 초기 WS warmup의 목표 5건 달성 여부를 최종 native 관측의 추가 승인 조건으로 쓰지 않는다. 실제 원천에는 초기 3건으로 출발해 141초/sequence 33까지 관측한 정상 FALSE가 있다. 시작 시 정확한 수신 존재와 최종 native 판정을 검증한다. 거래 입력 유효기간과 기계판정 최소 표본은 수정하지 않는다.
4. 동일 PID·종목·경로·물리 lease의 중복 보고는 한 건으로 센다. lease가 없는 과거 행은 발생시각과 결과/사유로만 구분한다. 유효 capture 없는 `assessed`는 성공 분자에 넣지 않는다.
5. native FALSE는 **커버리지 경고만** 회복할 수 있다. 기계 capture 결손·AI 결손을 회복한 것으로 표시하지 않는다. 완전한 최근 원천과 동일 경로 회복 기준을 유지하고 과거 raw 행을 고치지 않는다.

수정 위치는 기존 report owner와 기존 배포 호환성 모듈/테스트다. Kiwoom 요청·응답 parser·WS 등록/복구·호출량은 변경하지 않으므로 새 API 참조 게이트 대상은 없다. 주문, 정책, 5초 기한, 원천 freshness/custody/보호조건은 유지한다.

## 리뷰·검증·운영 인계

- 같은 동결 코호트의 이전/수정 분모는 모두 42건, 기계평가는 0건이다. 수정 후 정상 원천 관측 9건(21.4%)으로 분리하며 수신 결손 30건과 관측기간 부족 3건은 남긴다. 전체 시장 또는 실제 진입 개선 근거가 아니다.
- 관련 회귀 **594건 통과**(기존 pandas 경고 1건). Python compile, diff 및 print-only 문서 parser를 별도 검증한다.
- 음성 회귀: 경로/PID/해시/시각 불일치, UNKNOWN/TRUE/빈 branch, 잘못된 literal, 중복 lease, 실패 capture, 다른 결손의 잘못된 회복, 부분 tail. 정상 FALSE를 ENTER/PASS로 바꾸는 경로는 없다.
- 인계는 리뷰한 원본/후속 monitor 파일의 정확 SHA256 쌍만 허용한다. 원 정책 해시 및 dirty/임의 변경 거부를 유지한다. 후보 사전검사 이후 이전 PID/launcher 정상 종료 → selector/checklist 게시 → 정책 보존 인계 → 새 PID 증빙 순서로 수행한다.
- 실제 배포/PID, 검증 건수, 자연 감시 결과는 [완료 영수증](../../tmp/route-coverage-repair-20261012/completion.json)에 기록한다. 코드 리뷰 종료만으로 자연 경고 해소·거래 효과를 주장하지 않는다. 진짜 수신 결손이 커버리지 기준 아래로 떨어지면 경고는 계속 유효하다.
