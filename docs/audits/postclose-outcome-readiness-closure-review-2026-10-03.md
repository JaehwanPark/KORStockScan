# 장후 승패 보완·배포·기동 준비 실행 리뷰 — 2026-10-03

Owner: [실행계획](../proposals/postclose-outcome-readiness-closure-plan-2026-10-03.md), checklist `PostcloseOutcomeReadinessClosure1003`.

## 코드 보완·재리뷰

- 완료 분봉 CF의 평가 상한은 기존10분이다. 180초는 속도 진단이다. 늦은 손절을 `LOSS_AFTER_PRIMARY_WINDOW`로 분리해 비용 결합 손실로 평가한다. 목표/손절이10분 밖에만 있으면 가져오지 않는다.
- 보유 v1 원천의 명시적 `exact_stop_first_outside_primary_window`는 원본을 변경하지 않고 동일10분 비용 비교에 반영한다. 비용 미결합, 동일 봉 동시 도달, 미도달은 null/exclusion을 유지한다. 비용 결손과 검열의 오류 사유를 분리했다.
- 미평가 기존 ENTER 변경은 제외·변경 수 진단이다. 비교 가능한 지원수와 변경 수 대사를 확인하고 하나의 미평가 변경 때문에 후보 전체를 거부하지 않는다. 기존 성공100%·80% 보존을 새 탈락 조건으로 사용하지 않는다.
- 새 손실 label을 분류·위험 집계와 publisher 검증에도 연결했다. stale checkpoint는 기존 경제 kernel/source hash로 무효화된다.

검증: 영향 모듈592 PASS. 확장 검사에서1,001개 통과 후 연구 원인 기대값4건의 불일치를 발견했고, 해당 원인 기대값을 보완한 나머지·관련 모듈680 PASS(겹치는 검사를 합산하지 않음). 34개 Python compile, diff, 로컬 문서 링크 및 print-only parser 통과. broker 요청/주문·provider·hard safety는 이 코드 수정 대상이 아니다.

## 동일 보유 원천의 격리 재계산

KRX 정규7,069행과 기존 정확 보조 응답을 재사용했다. canonical 정책 발행 없이338.28초에 계산했다. native 시간순 분모와 원본 SHA를 보존했다.

| 기계 refinement | 기존 | 후보 |
|---|---:|---:|
| 학습 선택 기회 |24|11|
| 학습 승률 |58.33%|72.73%|
| 학습 보정 승률 |41.77%|47.95%|
| 학습 비용 결합 경로 평균 |−0.359533%|−0.190359%|
| 후단 선택 기회 |3|1|
| 후단 승률 |33.33%|0%|
| 후단 비용 결합 경로 평균 |−0.624683%|−0.956500%|

91개 후보를 평가해 학습 후보를 선택했고 후단에서 승률 비개선·순위 하락으로 승격하지 않았다. 학습 성공 보존57.14%와 미평가 변경9건은 탈락 사유가 아니다. 늦은 손실을 반영하면서 기존 분모·승률도 바뀌었다. 실제 체결 수익 또는 새로운 독립 검증의 증거는 아니다.

등록 VWAP 생성기와 보조 all/삼성/그 외 연구 비교는 기존 정책 승계다. 삼성 전용 연구 partition을 운영 전용 selector가 적용된 것으로 표시하지 않는다.

## 승인된 운영 후속

통합 커밋·immutable release 배포, 독립 systemd 경로와 실제 PID 확인,10/2 장후 재생성 및10/6 준비 검증을 이어 실행한다. 결과 receipt는 `tmp/postclose-outcome-readiness-closure-20261003/`와 `data/runtime/startup_readiness/2026-10-03/postclose_outcome_readiness/`에 보존한다. 이 문서의 현재 코드 검증은 운영 종결·미래 PREOPEN/PID를 대신하지 않는다.
