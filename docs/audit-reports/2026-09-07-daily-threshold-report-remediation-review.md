# Daily threshold report 보완·코드리뷰

> 후속 정정: [최종 결함 보완](2026-09-07-daily-threshold-final-defect-review.md)이 아래 최초 리뷰의 source 전체 차단·표본 순환·AI 상한 및 계측 근거를 보완한다. 9.9초/274MB를 정규 CLI 전체 경로의 확정 성능으로 사용하지 않으며, 조건 달성 가능성·자연 생성·실수익을 코드 완료와 구분한다.

## 판정

Daily threshold report는 유지할 가치가 있다. POSTCLOSE의 deterministic calibration과 parsed AI correction을 다음 PREOPEN 선택에 연결하는 중앙 근거이기 때문이다. 다만 기존 구현에는 broad/sim 분모, gross counterfactual EV, `hold`의 apply 후보 혼입, 모든 family에 가까운 AI 성공 요구, 비용 미설정의 0 처리, 누적 전량 재독기 때문에 목적보다 허들이 높거나 반대로 근거가 과장될 수 있는 결함이 있었다.

이번 보완은 신규 매수를 강제하지 않는다. exact cohort의 effective-dated 비용 차감 EV와 source quality가 닫힌 `adjust_up|adjust_down`만 현재 적용 후보로 만들고, PREOPEN의 기존 safety·same-stage·bounds·rollback·owner 계약을 그대로 유지한다.

## 구현 결과

| 영역 | 보완 결과 | 목적 부합 판정 |
|---|---|---|
| 후보 목록 | `family_readiness_list`는 capability/근거 준비 상태, `apply_candidate_list`는 window policy 확정 후 현재 적용 가능한 조정만 담는다. `hold`는 신규 apply에서 제외한다. | 적용하지 않을 상태가 AI/PREOPEN 허들을 만드는 모순 제거 |
| Score recovery | score60~74이면서 probe 계약이 있는 exact cohort만 분모로 사용한다. effective-dated round-trip cost와 forward candle source-quality가 pass인 행만 경제성 표본으로 쓰며 raw/eligible/excluded를 분리한다. counterfactual net EV만 primary로 삼고 gross는 diagnostic으로 내린다. | broad WAIT 수로 표본을 부풀리거나 결손 행·gross EV를 실전 EV로 오인하는 경로 차단 |
| Entry split | sample floor를 real submit/outcome으로만 계산하고 sim count는 diagnostic으로 유지한다. | 실행 가능성 판정을 대규모 sim 건수로 통과시키는 오류 제거 |
| AI correction | 실제 비결정적 `adjust_up|adjust_down` 후보만 provider manifest와 parsed AI hard gate 대상으로 한다. 누적 snapshot·source metric도 이 검토 family로만 projection한다. `hold`와 deterministic split/recovery handoff는 제외하며, 대상 0개면 provider 호출·재시도 없이 parsed empty receipt를 남긴다. | 변경이 없거나 AI가 재결정할 수 없는 계획 때문에 비용·시간을 쓰고 전체 체인이 실패하는 과도한 허들 제거 |
| Provider budget | 실제 provider 전달 compact ASCII JSON과 같은 문자열로 char/hash를 계산하고 직렬화 후 hard cap을 확인한다. 가격 계약이 없으면 비용은 `null`이며 0으로 대체하지 않는다. | 예산 계산과 실제 payload 불일치·무료 호출 착시 제거 |
| 누적·baseline | clean baseline 2026-06-05로 clamp하고 날짜별 load를 memoize한다. Daily threshold 소비 family/stage만 partition projection으로 읽고, bounded diagnostics에 full count/hash를 남긴다. baseline 이전 daily 재생성도 감사용으로는 허용하되 적용 후보·AI 검토 권한은 차단한다. | 기다려도 끝나지 않거나 이력에 비례해 파일·메모리가 팽창하는 경로 완화, archive evidence의 런타임 재유입 차단 |
| Source read failure | 선택된 partition read 실패와 대용량 raw fallback skip을 명시적 source-quality failure로 올리고 모든 신규 적용 후보를 닫는다. | 결손 입력을 정상 0건으로 오인하는 silent-fail 차단 |
| PREOPEN·검증기 | PREOPEN의 구 gross-EV fallback을 제거하고 비용 계약/net EV/source-quality를 재검증한다. 기계 적격성 `false`는 신규 적용을 막되 operator lock은 보존한다. verifier는 현재 적용 eligible 조정만 AI coverage를 요구한다. | producer-consumer-verifier 계약 일치와 운영 override 우선권 보존 |

## 자동화 연결과 조건 달성 가능성

자동화 연결은 유지된다. POSTCLOSE wrapper가 daily/cumulative report와 AI review를 생성하고 verifier가 실제 적용 후보의 review 계약을 확인하며, 다음 PREOPEN이 calibration candidate와 parsed review를 same-stage/bounds/source-quality guard 아래 선택한다. 기존 승인값의 `hold` carry-forward는 가능하지만 `hold`가 새 변경 후보로 위장하지 않는다.

조건은 달성 가능하도록 정정했다. 표본 floor나 양의 net EV 자체는 안전·경제성 조건이므로 제거하지 않았다. 대신 표본 분모를 실제 해당 cohort로 맞추고, 변경이 없는 family와 deterministic plan에 불필요한 AI 승인 요구를 제거했다. 비용 계약이 없는 counterfactual은 표본이 쌓여도 자동 승격되지 않으며 이는 불합리한 허들이 아니라 수익 과장 방지선이다. sim/counterfactual은 탐색 근거이고 실체결 품질 또는 broker authority가 아니다.

Score recovery의 submit drought는 `submitted_to_budget_unique_pct <= 10%`를 우선 판정하고, 그 비율이 없을 때만 `order_bundle_submitted == 0`을 대체 조건으로 쓴다. 따라서 제출 1건이 있다는 이유만으로 비율상 명백한 drought 후보를 영구 차단하던 중복 허들은 제거했지만, 10%를 넘으면 확대하지 않는다.

## 읽기 전용 실데이터 검증

2026-09-04 기준 산출물로 파일을 쓰지 않고 메모리에서 재구성했다.

- 최종 재검증에서 daily build 약 2.4초, cumulative build 약 7.5초, AI context 구성까지 전체 약 9.9초였다.
- 최대 RSS는 약 274MB였다. 보완 전 동일 경로는 146초가 지나도 종료되지 않았고 약 2.16GB RSS까지 증가해 중단했다.
- cumulative compact JSON은 약 0.99M chars였다. 원 source artifact와 다른 consumer용 partition은 삭제하지 않고 이 consumer의 projection만 줄였다.
- 기존 9/4 근거에서는 적용 조정 후보와 AI 검토 대상이 모두 0개이므로 실제 운영 실행 시 threshold AI provider를 호출하지 않는 대상이다. 무기록 context 검증은 26,953 chars로 120,000 hard cap 이하였다.
- 선택 partition projection은 완전했고, context hash가 실제 전송 ASCII 바이트 hash와 일치했다.
- Entry split 표본은 real 179건으로 판정하고 sim 410,133건은 diagnostic으로만 남겼다. 구 9/4 WAIT artifact에는 새 effective-dated cost 계약과 exact/economic 필드가 없어 score recovery 적격 표본은 0건이고 `source_quality_blocked`인 것이 정상이다. 이를 기다리면 저절로 통과하는 현재 근거로 해석하지 않는다.

이 검증은 무기록·무Provider·무런타임 실행이다. 새 schema의 자연 POSTCLOSE 생성, 9/8 PREOPEN 선택, PID 소비와 post-apply 비용 차감 EV는 아직 입증하지 않는다.

## 코드리뷰와 검증

- producer/consumer, PREOPEN carry-forward, postclose verifier, source-quality·비용·분모·권한 누출 경로를 교차 검토했다.
- Daily/WAIT/PREOPEN/verifier/EV/wrapper/backfill 관련 회귀는 **777 passed**다.
- 문서 회귀 **50 passed**, 변경 Python Black·Ruff·compile, target diff check와 checklist print-only parser가 모두 PASS했다.

## 다음 액션

`DailyThresholdNaturalAcceptance0908`에서 새 9/7 POSTCLOSE schema와 effective-dated 비용 계약, exact 분모, 실제 adjust 후보의 parsed AI review, 9/8 PREOPEN selection/receipt/PID 소비를 확인한다. code PASS나 report 생성 자체를 수익개선으로 판정하지 않고, 실제 적용 이후 동일 version cohort의 비용 차감 EV와 순이익으로 유지·보완·제거를 결정한다.
