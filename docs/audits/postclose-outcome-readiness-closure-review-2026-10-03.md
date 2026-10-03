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

통합 커밋 `e6d4d3b9` 배포와 독립13개 경로 설정, 활성5개 서비스 재기동을 실행했다. 재기동 직전 기존 읽기 client로 KRX/NXT 잔고0·미체결0과 위젯 custody 결손0을 확인했다. 새 위젯 PID3137231은 실제 release cwd·10개 선언된 env·startup 영수증 대사를 통과했다. 아직10/6 PID 소비를 의미하지 않는다.

운영 점검에서 overview가 유효 OFF 에피소드 연구를 결손으로 처리하고 격리 준비물을 인식하지 않는 결함을 추가 보완한다. 현재 원천일·strict/controller·선택 release를 모두 재검증한 준비물만 수용하며 미래 live bootstrap을 만들지 않는다. 이 보완은 별도 리뷰·검사 후 Main/분석 경로에 배포하고, 코드가 동일한 위젯/수집 경로의 실제 PID 결속을 유지한다.

후속 검증에서 controller output 변경이 먼저 보고되어 summary input 변경이 가려지고, 실패한 최종 재결속이 stage receipt를 먼저 변경하는 결함을 확인했다. 입력·선행 세대를 쓰기 전에 별도로 검증하고 실패 이유를 controller에 보존했다. 변경된 입력으로 재결속할 때 원 영수증을 그대로 보존하는 회귀를 추가했다. 관련115 PASS. producer 복구 뒤 native summary stage를 먼저 갱신한 후 전체 최종화를 실행한다.

전체 strict/controller와 cleanup·최종 detector를 통과한 뒤 PREOPEN 준비에서 Main 영수증 불일치가 드러났다. native Main stage는 새 승계 재평가와 기존 immutable 발행을 각각 검증했지만 summary 소비자가 두 report hash의 일치만 요구했다. 동일 정책·부모·정확 날짜·원 발행 원천 및 최신 native stage 결속이 모두 확인되는 기존 승계만 수용하고 원 발행/최신 평가 hash를 구분했다. 변경 후보·stale stage·다른 target은 거부한다. summary/controller/준비 관련159 PASS이며 정책 개선·PID 소비 권한을 추가하지 않는다.

정리에서 발견한10/1 provider 예산 요약 결손은 기존 native budget owner로 복구했다. 원장40 records의20예약/20정산을 검증했고 원장·manifest SHA는 그대로 유지했다. 새 호출·예약·예산 변경0이다. 기존 정리의 미완료 판정을 보존하고 정리를 다시 실행해 storage PASS를 확인했다. 압축으로 변한 collector 이력 결속도 native collector→summary로 갱신했다.

최종 warning 대사에서 비승격 다른 시장 진단의 기본 지원 버전을 정책 오류로 표시하고, 삼성 fixed-watch7항목 identity를5항목으로만 검사하는 오탐을 보완했다. 후보 없는 source-gap 및 runtime/apply 모두 false인 보류 진단만 구분하며 승격 version 검사는 유지한다. 실제 원천 대사에서 premarket의 명시적 보류 후보도 이 경계에 포함해 재검증했다. native identity owner로 scanner5/fixed-watch7을 검증하고 잘못된 origin·generation, 중복·시간 겹침을 계속 거부한다. 실제 운영/stop 원천 결손 경고는 그대로 남긴다.

통합 커밋·immutable release 배포, 독립 systemd 경로와 실제 PID 확인,10/2 장후 재생성 및10/6 준비 검증을 이어 실행한다. 결과 receipt는 `tmp/postclose-outcome-readiness-closure-20261003/`와 `data/runtime/startup_readiness/2026-10-03/postclose_outcome_readiness/`에 보존한다. 이 문서의 현재 코드 검증은 운영 종결·미래 PREOPEN/PID를 대신하지 않는다.
