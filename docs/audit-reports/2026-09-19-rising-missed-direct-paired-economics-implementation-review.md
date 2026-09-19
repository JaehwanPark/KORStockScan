# Rising-missed direct paired economics implementation review — 2026-09-19

## 결론

구현→자체 리뷰→보완→재리뷰를 완료했다. 기존 count prior와 퇴역 lifecycle 의존을 제거하고, source-only feedback의 exact evaluation ID를 비용 후 동일 attempt 비교로 전환했다. 새 장중 주문 경로는 만들지 않았고 기존 TP1 selector의 bounded parameter만 shared PREOPEN bootstrap을 통해 받을 수 있다.

## 리뷰에서 발견하고 보완한 결함

1. 최초 구현은 `positive_support_min`이 기존 support-reversal lane 생성 조건까지 완화해 paired 평가에 없던 population을 허용할 수 있었다. lane 생성은 기존 2개 support로 고정하고, 날짜별 값은 이미 eligibility가 성립한 lane의 최종 evidence floor에만 적용하도록 수정했다.
2. dated receipt의 self hash가 env 안의 자기 hash와 순환할 수 있었다. canonical digest에서 self field를 제외하고 publisher, bootstrap, runtime summary가 같은 계산을 사용하도록 통일했다.
3. `measured_no_edge` receipt에도 선택하지 않은 최선의 distinct 후보 calibration·holdout EV와 일별 순익 근거가 남도록 보완했다. env override는 비어 있으므로 다음 장전에서 임계값을 바꾸지 않는다.
4. 실제 9월 21일 PREOPEN 사전 조립에서 legacy selected family 검증 실패는 0건인데 퇴역 공통 handoff만 fail이라 최초 bootstrap incumbent가 없었다. 정확한 `runtime_env_handoff_missing` cutover 상태만 migration seed로 허용하고, runtime policy·dated override·selected/missing family 실패가 1건이라도 있거나 finding 종류가 다르면 차단하는 회귀를 추가했다.

재리뷰에서 unresolved in-scope defect는 없다.

## 직접 경제 결과

- clean-baseline source: 20일, 모두 date/schema/authority/hash admission 통과
- paired rows: 2,861; cost-adjusted usable 2,432; censored 429
- distinct candidate: `positive_support_min 2→1`, decision change 342
- calibration: 252건/12일, paired delta EV `-0.76333333%`, 100만원 고정 모형 일평균 `-160,300원`, 최악일 `-285,500원`
- untouched holdout: 50건/4일, paired delta EV `-0.85%`, 100만원 고정 모형 일평균 `-106,250원`, 최악일 `-296,200원`
- disposition: `measured_no_edge`; remaining five candidates are `identical_policy`
- effective 2026-09-21 receipt: `incumbent_preserved`, runtime env override 없음

100만원 값은 counterfactual 고정 notional 모형이며 실제 실현 순익이 아니다. 실제 PID 소비와 natural decision/fill/COMPLETED 비용 결과는 다음 정상 PREOPEN 이후 별도 acceptance다.

## 검증

- affected pytest: 1,013 passed, 3 deselected
- clean baseline에서 deselected 3건은 동일하게 현재 시각의 `scalping_cutoff` 선행으로 실패해 이번 diff와 무관함을 재현
- 추가 focused pytest: 191 passed 및 31 passed/72 deselected, TP1 consumer 20 passed/891 deselected; PREOPEN cutover 보완 뒤 영향 회귀 362 passed
- Python compile, affected ruff, `bash -n`, `git diff --check`: PASS
- print-only backlog parser: PASS; external Project/Calendar sync 미실행
- 실제 legacy 9월 18일 manifest를 사용한 9월 21일 bootstrap dry build: migration basis 확인, Rising `incumbent_preserved` receipt 수용, 신규 threshold override 0

9월 17일 raw pipeline은 약 5.71GB다. 명확한 음수 target/adverse 표본이 이미 sample floor를 넘으므로 과거 censored no-hit을 채우기 위한 전체 raw 재주사는 수행하지 않았다. producer의 terminal executable 필드는 이후 자연 산출물부터 채워진다.
