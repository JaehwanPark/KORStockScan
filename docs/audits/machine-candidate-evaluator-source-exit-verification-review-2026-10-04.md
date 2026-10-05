# 기계 후보 평가·삼성전자 원천 효과·고정 진입 청산 검증 결과

작성: 2026-10-04 KST. [실행계획](../proposals/machine-candidate-evaluator-source-exit-verification-plan-2026-10-04.md)의1→2→3을 수행했다. 보조 AI는 판정 입력에서 제외했고 기존9/29·9/30·10/2 원천만 사용했다.

## 1. 결정

- **삼성전자외 후보는 실제 parent 기계 평가와 위험별 제안 처리를 거쳐도10/2 승률68.75%를 유지했다.** 원 RECHECK263관측을 ENTER로 제안하는 별도 오프라인 평가 함수를 구현했다. 이는 신규 규칙의 재생이며 운영 registry/publisher에 등록된 정책은 아니다.
- **후단 native 연결0의 주요 원인은 관측 전용 생산 경로다.** 9/30·10/2 후보는 `zero_base_probe_machine_only_v1`이 생산했고 scanner 승격 ID를 받지 않았다. 이 원천을 실제 기회나 실제 주문 실패로 해석하지 않는다. 조회 결손으로 새로운 ID를 만들지도 않았다.
- **삼성전자 최신 원천 수정의 과거 성능은 확정할 수 없다.** 원519 capture와 기존 pipeline·request를 대사했지만 완전한 Main feature 생성 입력은0건이었다. 원 capture+새 규칙은 검증했고 수정 원천의 과거 효과는 미입증으로 남긴다.
- **가격경로 평균 음수의 핵심은 이익/손실 크기의 비대칭이다.** 비교용 목표를 순이익+0.1%로 고정했는데 손절은 비용 포함 약−1.0%다. 청산12개 arm을 같은 진입으로 비교해 개선은 확인했지만 양수 평균은 확보하지 못했다. 이 결과로 승률 우선 entry 후보를 자동 탈락시키지 않았다.
- 코드·오프라인 연구·리뷰는 완료했다. 정책 발행·배포·재기동·주문·API/provider 호출·수집 확대는 수행하지 않았다.

## 2. P1 — 삼성전자외 실제 평가 함수

### 구현과 위험 계약

`src/engine/scalping/entry_pullback_buy_flow_research.py`가 기존 `mechanistic_entry_policy_decision`으로 parent와 core 위험 disposition을 계산한 뒤 제안 행동을 만든다. 입력은 원 setup과 parent이며 미래 가격·label·보조판정을 받지 않는다.

- 고정 조건: 신뢰10체결 이상·매수압력≥60%·순공격매수량>0·현재가≤microVWAP, 원 quote/tape fresh 및 VWAP available.
- 삼성전자외 KRX 정규장만 대상이며 다른 scope는 parent를 상속한다.
- `PULLBACK_BUY_FLOW`라는 별도 setup을 제안한다. 기존 breakout 재확인과 setup 사실을 통과했다고 바꾸지 않는다.
- 제안 상쇄는 `CONFIRMATION_MISSING`의 `trigger_confirmation_missing`, `volume_confirmation_missing`, `micro_continuation_unconfirmed`, `no_supported_setup` 중 원 disposition이 `RECHECKABLE`인 fact만 허용한다. 원 parent가 이미 보상한 fact는 그 disposition을 보존한다.
- ADVERSE_TAPE의 미해결 fact·liquidity·source·invalidation·parent BLOCK·선정 micro recipe·situation veto는 유지한다. 원 ledger의 모든 위험을 결과에 남긴다.
- 기존 ENTER도 조건 불일치 시 RECHECK로 바꿀 수 있다. 성공100%/80% 보존 veto는 없다. report-only schema는 live validator에서 거부된다.

### 전체6,550관측 재생

parent 행동은 **6,550/6,550 일치**했다. 조건 일치는364관측이다.

| 원 행동→제안 행동 | 관측 수 |
|---|---:|
| RECHECK→ENTER_NOW | **263** |
| ENTER_NOW→ENTER_NOW | 18 |
| ENTER_NOW→RECHECK | **289** |
| RECHECK→RECHECK | 4,243 |
| BLOCK→BLOCK | 1,737 |

신규 ENTER 제안은 날짜별161/54/48관측이다. 이는 반복 관측 수이며 독립 거래 수가 아니다. 조건 일치 중 남은 사유는 수치 liquidity53·미해결 risk82·parent BLOCK26·invalidation27로 중복 집계한다. 주요 미해결 fact는 liquidity57, large sell23, failed structure3, foreign/institutional joint sell2, program 순매도 충돌1, adverse distribution1이다.

### 같은 가격·비용·점유의 비교

원 비용+0.1% 목표, gross−0.7% 손절,60분 경로를 사용한다. 첫 부분 봉·동일 봉 양 경계·자료 부족/비용 결손은 확정 승률에서 제외하고 별도 표시한다.

| 날짜 | 기존 목표/손절 | 기존 승률 | 후보 목표/손절 | 후보 승률 | 후보 전체 선택 |
|---|---|---:|---|---:|---:|
| 9/29 | 49/43 | 53.26% | 50/28 | **64.10%** | 104 |
| 9/30 | 12/19 | 38.71% | 24/12 | **66.67%** | 50 |
| 10/2 | 20/13 | 60.61% | 22/10 | **68.75%** | 49 |

10/2 후보49개는 원 ENTER3·RECHECK46이다. 목표22·손절10 이외는 시간종료3·첫 봉 불확실5·비용 결손3·후속 부족6이다. 선행 단순 관측 필터와10/2 결과가 같아도 평가 경로는 다르며,9/29·9/30에서는 추가 위험 보존으로 선택이 줄었다.

민감도도 재계산했다.10/2 전체393종목을 하나씩 제외한393회 비교에서 개선은 모두 유지됐으며+6.06~+11.08%p다. 이는 **선택된39종목만의39회가 아니라 전체 관측 모집단393종목 제외**다. 조건 적용 전600초 간격 축소에서는9/29 기존62.50%→후보60.71%로 악화,9/30 37.93→69.70%,10/2 55.56→71.43%다. 반복 관측 의존성은 남는다.

### native 연결 대사

고정 조건364관측을 기존3일 pipeline **308,408행**과 원 capture에 exact attempt/snapshot/trace로 연결했다. 종목·시간 근접 연결은 사용하지 않았다.

| 원 기회 ID 상태 | 관측 수 | 확인 결과 |
|---|---:|---|
| 기존 ID 있음 | 6 | 원 ID를 유지. 확인된 값은 `ZBPROM-*`이며 실제 주문 증거는 아니다. |
| 명시적 machine-only probe | 148 | scanner 승격 ID 없이 생산된 관측이다. |
| 과거 원천에 promotion 없음 | 210 | exact 기존 이벤트에서도 추가 promotion ID를 찾지 못했다. |

새로 복원한 promotion ID는0이다.9/30·10/2의 비중복 후보50/49개는 전부 명시적 probe 경로다. `zero_base_probe.py`는 `machine_only=True`로 호출하고 scanner promotion ID를 전달하지 않으며, `ai_engine_openai.py`도 이 경로에 provider/WATCHING/order 권한이 없음을 명시한다. 따라서 이 집합의 native0을 패턴 실패나 실제 진입 실패로 집계하면 안 된다.

기록된 native 행만 다시 점유하면9/29 후보 목표1·손절2,9/30·10/2 후보0이다. 관측 전용 집합의 성과와 실제 승격 기회 성과를 섞지 않았다. 새 ID를 생성하거나 canonical projection을 덮어쓰지 않았다.

## 3. P2 — 삼성전자 원천×규칙의 분리

원519개 capture 전부와 exact pipeline 연결228개를 확인했다.519개 모두 completed bars는 남아 있지만 원 Main의 route별 tick window·전체 WS 상태·feature 생성 시 사용한 전체 입력 묶음은 없다. 별도 archive의0B/0D는 존재하나 collector epoch가 달라 Main snapshot 전체를 대신할 수 없다.

AI request에서 같은 machine ID에 연결된14건도 조사했다. 모두 `replay_context_exact=false`, `canonical_input_bundle_missing`이며 완전한 생성 입력을 제공하지 않았다. request의 bool 상태를 replay payload로 오인하지 않았다.

| 입력/규칙 | 기존 규칙 | 새 보합 수급 규칙 |
|---|---|---|
| 원 전체 captured feature | 원519행 재현,10/2 비중복 시간종료2 | 고정 후보10/2 목표4·손절2·시간종료2 |
| 수정 원천으로 feature 전체 재생성 | **미입증: 완전한 원 Main 생성 입력 없음** | **미입증: 동일 결손** |

기존 `entry_candle_context`와 completed bars가 없다는 뜻은 아니다. 보관된 축약·정규화 입력만으로 원 `ws_data/recent_ticks/recent_candles/candle_context` 전체와 같은 feature 값을 보장할 수 없다는 뜻이다. 없는 입력을 추정하거나 외부 epoch를 Main 것으로 바꾸지 않았다.

구현한 selector→실제 feature window→receipt의 동일 입력 재현, prepared-entry 소비자, locked 관측/제출 구분은 표적 테스트로 검증했다. 이는 합성 입력의 코드 계약 검증이며 수정 원천의 과거 수익/승률 증거가 아니다. 이 단계는 복원 가능성 점검 완료, 과거 효과 미입증으로 종료한다.

## 4. P3 — 고정 진입의 비용·청산 분해

기존 및 후보의60분 비중복 진입 ID를 고정했다. 목표 net0.1/0.2/0.3%와20/30/60분/세션종료의 **12개 arm**을 동일 진입별로 계산했다. 손절 gross−0.7%는 고정했다. 청산 arm에 유리한 진입을 다시 선택하지 않았다.

### 기본0.1%/60분의 음수 평균

| 10/2 후보 | 완전 평가 | 목표 평균 net | 손절 평균 net | 시간종료 평균 net | 전체 평균 가격CF |
|---|---:|---:|---:|---:|---:|
| 삼성전자외 | 35/49 | +0.1000% (22) | −1.0083% (10) | −0.4903% (3) | **−0.2672%** |
| 삼성전자 | 8/8 | +0.1000% (4) | −1.0204% (2) | −0.4112% (2) | **−0.3079%** |

비삼성 평균의 gross 기여는 목표+0.2517·손절−0.2000·시간종료−0.0174%p, 원 왕복 비용−0.3016%p이며 합계−0.2672%다. 삼성은 목표+0.1764·손절−0.1750·시간종료−0.0340·비용−0.2753%p로 합계−0.3079%다. target gross에 포함된 원 비용을 따로 차감하므로 중복 비용 계산이 아니다.

이익 한 번+0.1% 대 손실 한 번 약−1.0%의 비교 모델에서는 경계 확정 승률이 약91%여야 해당 두 종료만의 평균이0 부근이다. **91%를 후보 승인/탈락 기준으로 추가하지 않았다.** 이는 이번 고정 청산 가정의 산술 설명이며, 목표 선도달이라는 entry label이 실제 운영 청산 규칙을 뜻하지도 않는다. 운영의 trailing 등과 결속하기 전에는 실제 수익성 결론을 낼 수 없다.

### 청산 비교와 분모 리뷰

처음에는 arm별 양쪽 평가 가능한 paired 집합을 비교했고, 리뷰에서 arm마다 결손 제외량이 달라지는 영향을 점검했다. **12개 arm 모두 완전한 공통 진입**으로 순위를 다시 계산했다.9/29·9/30만으로 진단용 순위를 산출하고10/2를 선택에 사용하지 않았다.

| 집합 | 공통 비교에서 학습 선택한 청산 | 날짜 | 공통 진입 수 | 기본0.1%/60분 평균 | 대안 평균 |
|---|---|---|---:|---:|---:|
| 비삼성 | net0.3%/60분 | 9/29 | 75 | −0.3083% | −0.2364% |
| 비삼성 | 동일 | 9/30 | 35 | −0.2891% | −0.2340% |
| 비삼성 | 동일 | 10/2 | 31 | **−0.2981%** | **−0.2199%** |
| 삼성 | net0.2%/20분 | 9/29 | 7 | −0.4277% | −0.2762% |
| 삼성 | 동일 | 9/30 | 4 | −0.4378% | −0.2586% |
| 삼성 | 동일 | 10/2 | 6 | **−0.4438%** | **−0.3349%** |

비삼성의 arm별 paired 분모에서는0.3%/세션종료가 학습상 선두였으나, 공통 분모에서는0.3%/60분이 선두다. 결손 분모 민감도가 있으므로 첫 순위를 최종 정책으로 채택하지 않았다. 삼성0.2%/20분의 전체8개 paired 비교는−0.3079→−0.2860%이며,12개 arm 공통6개 비교와 혼용하지 않는다.

10/2 비삼성에서 단순20/30분 단축은 기본보다 악화했다. 삼성은 같은0.1% 목표의20분 종료가 전체8개에서−0.2315%로 개선됐으나, 이를 보고 학습 선택을 바꾸지 않았다. 개선 arm에서도 평균은 음수다.

고정 진입을 유지한 청산 비교는 **개별 진입의 paired CF**다. 목표를 높이거나 시간을 늘리면 다음 고정 진입과 보유가 겹칠 수 있다. 공통 리뷰에 보수적 중첩 건수를 기록했으며, 불확실한 종료는 horizon까지 점유한 것으로 계산했다. 따라서 이 수치는 실제 포트폴리오 순손익·독립 거래 수가 아니다. 예를 들어10/2 비삼성0.3%/60분은 고정49개 중 중첩1개, 삼성0.2%/20분은 고정8개 중 중첩1개다.

## 5. 리뷰·검증·남은 경계

- 표적 **223 tests PASS**, 영향 Python compile, engine location gate, `git diff --check`, 문서 링크/owner와 print-only parser를 검증했다.
- 위험별 disposition 보존, 다른 종목/scope 상속, 원 ENTER 제외 허용, live validator 거부, raw hash 손상, liquidity/source/BLOCK/micro/situation 보존을 회귀했다.
- 청산의 첫 부분 봉·동일 봉 양 경계·가격 간격·hit 이후 gap·비용 결손·세션 경계·paired 분모·gross−cost=net을 회귀했다.
- 리뷰에서 arm별 결손 분모 차이와 고정 진입 중첩을 추가 대사했다. 선행 리뷰의 종목제외 민감도 표기39회를 실제393회로 정정했다.
- 신규 오프라인 모듈/테스트만 추가했고, 이번 턴에 기존 runtime 소스·Kiwoom 요청/파서·원 정책을 변경하지 않았다. 기존 작업본은 보존했다. 전체 매매 suite·canonical 장후 재생성·외부 문서 동기화는 실행하지 않았다.

비삼성 후보는 **실제 parent guard를 포함한 연구 후보**로 유지한다. 반복 관측 축소 시9/29 악화·관측 전용과 실제 승격의 다른 분모·독립 날짜 미검증은 남아 있다. 삼성 source 수정의 과거 성능은 보관 입력으로 확정할 수 없다. 이 제한을 성공 보존 veto나 새 수집 확대 요구로 바꾸지 않는다.

## 6. 재현 자료

- [고정 계약](../../tmp/machine-candidate-next-actions-20261004/frozen-contract.json), [기계 재생 결과](../../tmp/machine-candidate-next-actions-20261004/candidate-result.json), [6,550 위험별 원장](../../tmp/machine-candidate-next-actions-20261004/machine-decisions.json).
- [원 ID 연결 대사](../../tmp/machine-candidate-next-actions-20261004/lineage-result.json), [이벤트 근거](../../tmp/machine-candidate-next-actions-20261004/lineage-events.json), [삼성 입력 census](../../tmp/machine-candidate-next-actions-20261004/samsung-input-census.json), [삼성 request census](../../tmp/machine-candidate-next-actions-20261004/samsung-request-census.json).
- [고정 진입 ID](../../tmp/machine-candidate-next-actions-20261004/fixed-entry-ids.json), [청산 결과](../../tmp/machine-candidate-next-actions-20261004/exit-result.json), [청산 경로](../../tmp/machine-candidate-next-actions-20261004/exit-paths.json), [공통 분모·중첩·기계 민감도 리뷰](../../tmp/machine-candidate-next-actions-20261004/review-result.json), [최종 검증](../../tmp/machine-candidate-next-actions-20261004/validation.json).
- 실행 owner: [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `MachineCandidateEvaluatorSourceExit1004`.10/6 준비·자연 수용 owner는 그대로다.
