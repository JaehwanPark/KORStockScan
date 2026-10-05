# 비삼성 지정 정책·삼성 추가연구 실행 리뷰

작성일: 2026-10-05 KST. 사용자 `계획 실행`에 따른 두 상세계획의 구현·검증 기록.

## 1. 판단과 적용 범위

비삼성 `pullback_p60_v0`의10/6 지정 발행 경로와 이후 고정 정책 비교를 구현했다. 초기 지정은 운영자 지정이며 독립 검증 통과로 표시하지 않는다. 실제 자동 재생은 학습 적격, 새 날짜 미관측, selected=false를 유지했다.

삼성 추가연구는 사전 고정한5변형과2대조 정책으로 종료했다. H2를 후속 검증용으로 권고한다. 삼성 운영 정책은 교체하지 않는다. 보조 AI·Widget·Episode·계좌/주문/수량/손절/custody 권한을 추가하지 않는다.

원본과 작업 증빙: [intake](../../tmp/designated-machine-execution-20261005/intake.json). 최종 발행·배포·준비 상태는 이 문서 §7과 실행 closure를 따른다.

## 2. 구현과 리뷰 중 보완

- `entry_designated_policy.py`: 요청·B0/C0·자동 보고서·기존 dated 세대·검토 증빙을 결속. 기존 publisher lock, parent/dated CAS, 이전 파일 원 bytes 보관, prepared/committed journal, 중단 복구와 loader 거부를 구현했다. 동일 요청은 무변경 재실행이며 다른 내용의 request 재사용·날짜 연장은 거부한다.
- 초기 지정의 새 날짜 미관측만 별도 권한으로 수용한다. 원 자동 보고서·학습 적격·추가 거부 사유 부재·고정 recipe·원천/guard를 계속 검사한다. report selected=false를 true로 고치지 않는다.
- 이후 `main_machine_designated_fixed_pair_v1`: B0/C0 비교 기준, 실제 incumbent I_t와 원 관측 P_t를 분리한다. activation·관측 당시 generation/action 증거가 있는10/6 이후 자료만 사용한다. 최신 날짜와 누적 창 모두 challenger 경계 군집≥10·incumbent binary 존재·raw 개선·지원조정+5pp를 요구한다. 양방향 교체에 같은 조건을 쓴다. 성공 보존율과 coverage는 진단이다.
- 같은 날짜 반복은 관측 manifest로 같은 날짜 집합을 재계산하며 독립 지원을 늘리지 않는다. 최신 날짜가 누적에도 포함된다는 점을 보고한다. 새 정식 전략이 등록된 pair 밖으로 이동하면 전용 pair metadata를 종료한다.
- 최종 실제 발행 전 대사에서 기존10/6 예정 정책이 보조판정 이력5세대를 거친 것을 확인했다. 직접 parent 동등성 가정을 제거하고, 각 중간 세대의 hash·원천·machine/scope 보존과 현재 부모까지의 연결을 검증하도록 보완했다. 누락/변조 이력은 거부한다. stage receipt의 `operator_designated`와 자동 계산 `incumbent_carried`도 분리했다.
- `main_machine_policy`→publisher/loader→terminal→summary→strict가 별도 지정과 원 자동 평가의 결속을 검사한다. source10/2 복구가 지정 예정 세대를 기존 정책으로 되돌리지 않는다.
- 삼성은 허용된 exclude-005930 component 차이만 인정한다. 원519관측에서 policy identity metadata와 불활성 recipe receipt를 제외한 행동/가드 payload를 비교했고 차이0이다. 원 frozen은 수정하지 않는다. 현재 코드와 원 kernel의 이력은 별도 migration에 기록한다.
- 관측별 정책 provenance 검증에 bounded cache를 추가했다. 같은 generation의 거대한 평가 보고서를 관측마다 재계산하는 비용을 제거하되 모든 원천 파일 signature를 확인하고 변경 시 거부한다.
- rollback 리뷰에서 이전 selection proof가 복원 정책과 충돌하는 결함을 보완했다. 지정 기준 B0 복귀는 KRX machine만 복원하고 최신 AI와 다른 scope를 보존하며 전용 pair 권한을 종료한다. 격리 테스트만 수행했다.
- 삼성 연구에서는 부동소수점 차이를 개선으로 오인한 H4를 수정했다. 가격경로 끝점 진단은 주 barrier label과 분리하고 구간 전체의 가격 연속성을 검사했다. H3는 원 micro window 안의 선행 호가만 허용한다.

## 3. 비삼성 실제 재생

[실제 보고서](../../tmp/designated-machine-execution-20261005/replay-final/winrate-report.json), [관측 대사](../../tmp/designated-machine-execution-20261005/replay-final/observation-parity.json), [삼성 동등성](../../tmp/designated-machine-execution-20261005/replay-final/samsung-component-parity.json).

- 원 capture8,793건을 읽고 기존 연구의7,069관측 identity/raw/action/path를 대사했다. 차이0.
- 비삼성 학습 군집 승률45.75→70.20%, 고정 후보 학습 적격 유지. 독립 검증 미관측, 자동 선정false.
- 최초 지정이 연구 이력을 지우거나9/29·9/30·10/2를 새 holdout으로 바꾸지 않는다.
- synthetic10/6 fixture는 코드 회귀다. 실제 적용 후 성능 증거로 사용하지 않는다.

## 4. 삼성 유한 연구 결과

[연구 산출물](../../tmp/samsung-absorption-differential-research-20261005/final/recommendation.json), [비교](../../tmp/samsung-absorption-differential-research-20261005/final/comparisons.json), [가설별 원천](../../tmp/samsung-absorption-differential-research-20261005/final/hypothesis-registry.json).

| 전체 origin, 날짜 동일 가중 | 기존 정책 | 원흡수 | H2 |
|---|---:|---:|---:|
| 완전 경로 수 |10|17|16|
| 목표/손절 확정 승률 |21.43%|55.56%|61.11%|
| 완전 경로 비용 후 양수 비율 |30.95%|46.67%|50.00%|
| 목표 수 / 손절 수 |3 /5|8 /6|8 /5|
| 완전 미도달 양수 / 음수 |1 /1|0 /3|0 /3|

각 날짜의 비율을 같은 가중으로 평균한 값이다. 전체 건수로 단순 나눈 승률과 다르며 실제 체결/실현 손익이 아니다. 원흡수와 H2에 각각 추가 미확정1건이 있어 완전 경로 분모에 넣지 않았다.

H2는 원5초 TTL 내 같은 epoch의 직전 적격 capture에서 pressure<60, 현재≥60인 전환을 수용한다. 추가 조건을 알 수 없으면 원흡수 행동을 승계하고, 알려진 실패일 때만 원흡수 ENTER를 RECHECK로 바꾼다. 원흡수 BLOCK/RECHECK를 ENTER로 바꾸지 않는다.

효과는9/29 손절1건 감소다.9/29를 제외하면 개선이 사라진다. H2 조건은 전체519건 중43건에서 식별됐고, 원흡수 ENTER59건 중55건은 조건 unknown으로 승계했다. 이 때문에 강한 일반화 증거로 해석하지 않는다.

상시감시206건 하위집합에서 원흡수/H2의 비용 후 양수 비율은 모두50%, H2의 직전 capture 조건 식별은0건이다. 따라서 상시감시에 특화된 개선은 입증되지 않았다. H1은 악화, H3는 같은 선택, H4는 주지표 개선 없음, H12는 H2와 같은 결과로 더 복잡하다. 가장 단순한 H2 하나만 `recommend_register_for_forward`로 동결했다. 세 날짜는 모두 기존 탐색 자료다.

[원 판정별 결과](../../tmp/samsung-absorption-differential-research-20261005/final/outcome-census.json), [원천 분포](../../tmp/samsung-absorption-differential-research-20261005/final/feature-differences.json), [공통 사건/같은 종료시각](../../tmp/samsung-absorption-differential-research-20261005/final/paired-events.json)에서 목표·손절·완전 미도달±·가격 결손을 분리한다. 모르는 watch identity는 명시하며 native watch로 합성하지 않는다. 손절 뒤 반등을 승리로 바꾸지 않는다.

## 5. 삼성 후속 인계와 원천 한계

- 최신 원흡수 frozen은 보존했고 원 kernel archive와519행 행동/guard 동일성을 결속한 migration을 발행했다. H2는 [별도 frozen](../../tmp/samsung-absorption-differential-research-20261005/final/frozen-candidate.json)과 기존 원천만 읽는 future adapter로 연결했다.10/6 원천이 없어 둘 다 `waiting_new_source_date`다.
- 과거 foreign/program veto2개의 frozen에는 테스트 파일 원본 SHA `c165a509…`가 포함돼 있다. 현재 파일·Git 이력·보호된 release에서 해당 원본 bytes를 찾지 못했다. 원 frozen을 수정하거나 test hash를 현재 것으로 치환하지 않았다. **이2개는 `blocked_historical_kernel_source_gap`이며 migration 완료를 주장하지 않는다.** 기존 `SamsungFrozenCandidateValidation1006`가 원본 복구 또는 별도 재동결 검토를 소유한다. 코드 검증과 역사 테스트 원본의 부재를 구분한다.
- 장전 삼성 계약은 기존 불변 코드로 source inventory를 다시 확인했다.4경로가 없어 `waiting_new_source_date`다. KRX 외 machine component는 지정 전후 동일해야 하며 이를 발행 readback에서 대사한다. 현재 검증은 장전 성능이나 향후 소비 완료가 아니다.

[Migration 기록](../../tmp/designated-machine-execution-20261005/migrations.json), [최신 원흡수 준비](../../tmp/designated-machine-execution-20261005/samsung-absorption-forward-readiness.json), [H2 준비](../../tmp/samsung-absorption-differential-research-20261005/final/forward-readiness.json), [장전 원천 inventory](../../tmp/designated-machine-execution-20261005/premarket-inventory.json).

## 6. 검증 범위

기존 계약281건, 생성기/장전 전달264건, 기존 fixed-watch54건을 통과했고, 리뷰 수정마다 지정·migration·summary 등 영향을 받은 테스트를 재실행했다. 중복된 실행 건수를 독립 테스트로 합산하지 않는다. 마지막 테스트 목록·로그·commit 입력 SHA·compile/diff/parser 결과는 `tmp/designated-machine-execution-20261005/review-gate.json`에 봉인한다.

회귀는 지정 거부·CAS·중단 journal 복구·초기 자동 미선정 유지·양방향 재선택·실제 incumbent 승계·P_t/action·서명 cache 변경·안전 복귀·삼성 미래 원천 누출/TTL/epoch·unknown 승계·기존 guard 보존을 포함한다. 검토 범위의 코드 결함과 위 역사 원천 결손을 분리한다. 실제 주문/API·미래 날짜 자연 성능 검증은 실행하지 않았다.

## 7. 발행·배포·장전 준비

- 코드 통합 `ee4b19db`, stage 표기 보완 `875de2b6`, 실제 dated 이력 보완 `3d0e5106`를 커밋했다. 선택된 불변 release는 `designated-machine-policy-20261005-3d0e5106`, 전체 commit은 `3d0e5106f6a9ce708d1701835198da46d3a831c5`다. 두 유휴 장후 분석 service도 이 경로로 대사했고 즉시 재기동하지 않았다.
- 10/6 신규 지정 bundle은 `8fb91f19722f0eb3ebd71066e3813f0f892da23ab960604a5a5298427c437f7d`, KRX machine component는 `6b6fb2040270dab41a05e2a84bda0baed9c06714aa0b587997b2982a87df2b4a`다. 대상은 비삼성·KRX 정규장이다. 원 자동 보고서는 `candidate_selected=false`, stage는 `operator_designated`, 독립 검증은 `not_observed`다.
- 원10/6 세대 `3c500f6a…`의 JSON bytes·원천·5단계 이력을 보관했다. 동일 요청 재실행은 `already_staged`, 원 장후 보고서 재소비는 `operator_designation_preserved`다. 현재 운영 포인터 `6785d52e…`는 불변이며9개 scope의 보조판정, KRX 정규장 외 machine도 불변이다. 삼성은519관측 행동/guard 차이0 근거를 유지했다.
- source10/2 machine stage·summary stage succeeded, strict **PASS·issues0**, controller **DONE·whole_native_chain**,10/6 준비 **prepared_verified**를 확인했다. 준비 시각은10/5 16:09:42 KST, manifest content hash는 `fdeaf06c1b71a121bf84cc0cf77a0da7d387e946bee8bbefa972ba173dac8e43`다. [발행 결과](../../tmp/designated-machine-execution-20261005/designation-result.json), [최종 closure](../../tmp/designated-machine-execution-20261005/closure.json)를 따른다.
- 검토 범위의 미해결 코드 결함0, 중복 제외606개 표적 회귀를 확인했다. 실제 재생·원천 대사 및 불변 release의 발행/loader 테스트도 통과했다. 향후10/6 자연 자료·실제 체결/수익 검증과 전체 거래 suite/API 호출은 이 작업에서 수행하지 않았다.
- Main의10/6 실제 activation/PID 소비는 `DirectFamilyPreopenPolicyHandoff`, 적용 후 B0↔C0 비교는 `NonSamsungMachineForwardComparison1006`가 소유한다. 신규 지정은 당일 적용 준비 완료이며 현재 PID 적용/수익 검증 완료가 아니다. Widget PID3614517의 실제 cwd와 Episode unit은 기존 `e6d4d3b9` 승인 경로를 보존했다.
- 삼성 H2/원흡수의 자연 검증은 기존 `SamsungFrozenCandidateValidation1006`로 인계한다. 과거 foreign/program veto2개의 역사 kernel 원본 결손은 §5대로 남아 있다. 이 결손을 삼성 후보 실전 적격이나 비삼성 지정 실패로 바꾸지 않는다.
