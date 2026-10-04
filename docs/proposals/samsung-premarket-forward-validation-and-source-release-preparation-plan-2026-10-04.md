# 삼성전자 장전 독립 검증·원천 수리 배포 준비계획

## 1. 목적과 이번 실행 범위

사용자 `다음액션 실행`에 따라 선행 [원천 수리 리뷰§6](../audits/entry-setup-family-state-source-repair-review-2026-10-04.md)의 다음 단계를 구체화한다. 운영 source 수리의 커밋·배포 대상과 rollback을 준비하고, 장전 관측 가설 두 개를 이후 날짜에 검증할 계약을 고정한다. 이번 실행은 작업본 구현·격리 검증·준비까지다. 실제 커밋·배포·재기동·정책 발행·API/provider·주문·수집 확대는 실행하지 않는다.

원래9/29·9/30·10/2는 반복 탐색한 discovery다. 새 독립 holdout으로 재사용하지 않는다. 성공100%/80% 보존 조건은 후보 탈락 기준에 넣지 않는다. 결과는 [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 완료 준비 항목과 별도 미래 검증 항목에 기록한다. 기존 정규장 두 후보와10/6 PREOPEN owner는 유지한다.

## 2. 변경 묶음과 소유 위치

| 묶음 | 파일/역할 | 적용 경계 |
| --- | --- | --- |
| C1 운영 source 수리 | `entry_setup_evidence.py`, `ai_action_outcome_calibration.py`, `entry_setup_source_repair.py` | producer grammar 수리, 역사복구는 명시적 uncached opt-in만 |
| C1 회귀 | `test_entry_setup_evidence.py`, `test_entry_setup_source_repair.py`, `test_entry_setup_source_repair_readiness.py` | strict validator·hard BLOCK·local RECHECK·실제 public loader/cache |
| C2 오프라인 검증 준비 | `samsung_premarket_forward_contract.py`, 해당 test, 본 계획·실행 리뷰·현재 checklist | frozen 계약·순수 가설 mask·원천 파일 inventory만 |

모듈은 기존 Main/scalping 연구와 producer를 소유하는 `src/engine/scalping`에 두고, test는 `src/tests`에 둔다. engine root 신규 모듈이나 runtime caller 등록은 없다. C1 patch는6개 코드/test 파일만 포함하고, [기존 수리계획](entry-setup-family-state-source-repair-plan-2026-10-04.md)과 수리 리뷰를 증빙으로 묶는다. C2와 기존 누적 연구 작업본은 운영 patch에 포함하지 않는다. C2 kernel 계약은 현재 작업본의 선행 연구 모듈까지 봉인하므로, 운영 릴리스에서 독립 실행 가능하다고 주장하지 않는다.

## 3. C1 커밋·배포 준비와 rollback

### 3.1 기준과 패키지 검증

- 선택 릴리스 기준: `a17bd6d2587e1204eacd0cd283bcbd854eb71bfc`, `postclose-tower-readiness-20261003-a17bd6d2`.
- 사용자 작업본 HEAD `5fcbea3222c206e809191100da1b33de49ffee10`과 계보가 다르므로 작업본 전체 pull/rebase/reset으로 통합하지 않는다. 정확한 선택 commit 위에 C1 파일만 적용하는 patch를 준비한다.
- `tmp/samsung-premarket-forward-preparation-20261004/package.json`에 base commit·patch SHA·정확한6개 대상 SHA와 미커밋/미배포 상태를 기록한다.
- 선택 commit의 detached `candidate-final-worktree`에서 `git apply --check`, 적용 후6개 파일 byte 일치, 관련5suite·compile·diff를 검증한다. 이전 `candidate-worktree`/449 tests는 테스트 보완 전의 역사 준비본이며 최종 package의 검증으로 사용하지 않는다.

### 3.2 마지막 소비자 검증

`ai_decision_trace.capture_machine_observation`으로 수정 producer의 새 capture를 tmp에 기록하고 `load_machine_observation_rows`의 public 경로를 cold/warm으로 소비한다. unsupported/micro/hard BLOCK의3경우에 대해 다음을 각각 확인한다.

1. 기본 모드 + 유효한 비용/가격: source validator 오류0, 원trace·action·watch identity 그대로 소비, 경제성 계약 유효, warm projection 재사용.
2. 기본 모드 + 비용 결손: source는 유효하지만 경제성 결손 규칙대로 행 제외, warm valid-empty 재사용.
3. independent 모드 + 비용/가격 결손: 경제성 미확정 행 보존, label/cost를0으로 채우지 않음, warm 재사용.

9회귀 모두 역사복구 인자/receipt 없이 수행한다. 공유 장후 report 경로의 기본 `independent_machine=False`와 active machine/winrate CLI가 사용하는 `independent_machine=True`를 각각 모사한다. 실제 다음 영업일 원천/기동 성공을 합성 fixture로 입증하지 않는다.

### 3.3 향후 운영 적용 순서

별도 운영 적용 지시를 받은 뒤 정확한 base와 package hash를 다시 대조하고, 기존 release 절차로 새 commit/immutable release를 만든다. 운영 적용 직전 현재 release route·custody·미체결·startup/PID receipts를 재검증한다. source 수리만으로 policy를 바꾸거나 역사 receipt를 자동등록하지 않는다. 배포 후 producer capture grammar→기본 장후 loader→새 projection generation을 자연 증거로 확인한다. exact-date policy/PREOPEN/handoff는 해당 owner가 별도로 검증한다.

rollback은 이번 기준 선택 릴리스 `a17bd6d2`로 code/route를 되돌리는 기존 절차다. source archive·projection·정책 파일을 과거 bytes로 덮어쓰지 않는다. 수정 kernel이 만든 projection은 이전 kernel에서 dependency hash가 다르므로 기존 invalidation 계약을 따른다. historical receipt는 kernel 변경 시 재사용하지 않는다. 기록상 이전 선택 릴리스 `e3b9510c`는 C1의 기본 rollback 대상과 구분한다. rollback 시점의 실제 PID consumption도 별도 receipt가 필요하다.

## 4. C2 고정 장전 가설

검토 bundle: `3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99`, target `2026-10-06`. exact 장전 parent SHA: `656cfd8e824f3135c8a5c7f47ece789a9c1837f53e72355d298fa2602f05b011`. KRX-only bundle을 장전 parent로 대체하지 않는다.

| 가설 | 과거에 확정된 조건 | 질문 |
| --- | --- | --- |
| `distribution_buy_absorption` | 완료 분봉 phase=`distribution`, 최근 micro 가격변화≥0, 공통 흡수 조건 | 구조 phase가 약해도 현재 매수 흡수가 이후 회복을 구분하는가 |
| `flat_price_ask_depletion` | 유효 완료 phase, 최근 micro 가격변화=0, 공통 흡수 조건 | 가격 상승 이전의 ask 소진이 이후 회복을 구분하는가 |

공통: exact `005930_NX`·NXT/NXT_PREMARKET 관측과 Main `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE`의 원identity join, 원parent guard 통과, delta≥원parent 최소값1.0, 매수체결 대응 비율≥0.5, ask 소진>0, refill ratio≤0.5, 하향 재호가false. ask 확인창1초·quote 최대 age1.5초, 같은 transport epoch/연속 경로, anchor 이전 원천만 사용한다. 동일 clock에서 anchor 이후 체결을 포함하지 않는다. `phase`는 완료 봉의 과거 계산이다. 최저/최고점을 사후에 붙여 선정하지 않는다.

숫자 null/NaN/bool·원천 join 결손·미확인 guard는 `source_gap/null`이다. 확인된 hard guard 실패는 `guard_excluded`이며 좋은 micro 수치로 뒤집지 않는다. 같은 사건에 두 가설이 겹치면 별도 비교 결과만 기록하고 독립기회로 합산하지 않는다. phase·공통 조건·threshold·비용·기간을 결과에 맞춰 재선정하지 않는다.

## 5. 독립 검증 실행 계약

### 5.1 intake와 봉인

10/6 이후 자연 생성된 날짜에서 public machine projection(`.json/.json.gz`), raw capture(`.jsonl/.jsonl.gz`), exact NXT_PREMARKET trade/depth manifest의4개 경로를 확인한다. inventory는 파일존재·physical hash만 증명한다. consumer 구현과 성능 계산은 새 원천의 exact intake 이후 미래 owner가 수행하며 이번 도구가 이미 완성한 evaluator라고 표시하지 않는다.

검증 실행 시 raw canonical/parent hash·target date·원capture action·snapshot/attempt/trace/native watch/generation·actual route/epoch·manifest와 stream의 physical/content hash를 확인한다. 당시 관측된 정책 consumption 여부도 확인한다. 서로 다른 stream의 timestamp만 같다는 이유로 연결하지 않는다. manifest만 있고 stream이 없으면 source gap이다. parent/kernel 변경은 기존 contract를 조용히 재봉인하지 않고 새 계약 검토로 전환한다.

### 5.2 두 panel

- **Main panel:** 원canonical/native를 분모로 실제 parent 판정과 두 고정 가설을 비교한다. 동일 row의 source-bound full cost와 기존 binary label owner를 사용한다. broker 비용 결손을 가격 CF 비용으로 대체하지 않는다. `RECHECK` 관측수를 새 독립기회로 만들지 않는다.
- **Archive 가격 panel:** 당시 관측 ask 진입/bid 종료,1200초·net target0.1%·gross stop−0.7%·설정비용0.23%·quote gap1.5초를 고정한다. 경로 CF로만 표시하며 Main native support·실현 PnL로 승격하지 않는다. Main 비용과는 별도다.

각 native/panel에서 첫 적격 신호만 admission한다. 원owner 기준 알려진 terminal 뒤에만 재진입한다. 최초 신호의 경로가 검열되면 뒤 성공 신호로 교체하지 않는다. 미도달/검열/원천 결손은 binary 실패0으로 채우지 않고 수·사유를 별도 기록한다.

### 5.3 판정과 중단

연구 비교의 제안 최소 증거는 같은 분석 population에서 parent/candidate 각각 확정 binary3개 및 독립 날짜2개다. 후보의 비용 반영 binary 승률이 parent보다 엄격히 높아야 한다. 기존 성공 보존율은 진단값이며 탈락 veto가 아니다. parent 적격 ENTER/binary가0이면 승률0%로 두지 않고 `comparison_not_identifiable`로 표시한다. positive-micro-only 기준은 diagnostic reference이며 현재 운영 parent를 대체하지 않는다.

처음3개 적격 자연 날짜까지만 이 계약을 검증한다. 원천 없는 날짜는 waiting이고 임의 가격/새 API로 채우지 않는다. 조건부 승률 우위가 나와도 소표본 연구 결과이며 선택 편향/불확실성·비용후 경로 결과를 함께 보고한다. 정식 publisher 최소지원·운영 경제성·계정/custody/native bridge·natural/PID 및 정책 적용은 별도다. 연구 gate PASS를 운영 승인으로 해석하지 않는다. 개선 확인 시 추가 가설 탐색을 종료하고 runtime bridge 계획으로 이동한다.3개 적격 날짜가 끝나도 우위가 미입증이면 `unproven/failed`로 종료한다.

## 6. 코드리뷰·검증·남은 owner

후속은 `SamsungPremarketForwardValidation1006`이 소유한다. 기존 `SamsungFrozenCandidateValidation1006`의 정규장 두 후보는 확대/재봉인하지 않는다. 그 계약의 옛 kernel receipt는 현재 수리 코드의 PASS 증거가 아니다. 기존 future owner 실행 시 kernel 변경을 확인하고 자신의 replan 계약을 따른다.

이번 준비 gate: C1 최종patch 정확한base 적용/byte 일치→producer/public loader9회귀→관련5suite→C2 contract/mask/null/권한/변조/gzip/원천대기 회귀→두 격리 계약 출력 bytes 일치→source/policy/selector hash 보존→compile/diff/link/owner/print-only parser. 결과와 미검증 사항은 [실행 리뷰](../audits/samsung-premarket-forward-validation-and-source-release-preparation-review-2026-10-04.md)에 남긴다.
