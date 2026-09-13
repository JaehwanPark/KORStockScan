# Entry V2.14/V2.15 판정 균형 설계점검·보완계획

작성: `2026-09-13 KST`. 범위: main SCALPING entry의 설계점검과 후속 구현계획. 최초 작성은 문서-only였다. 이후 사용자의 구현·review/fix 지시에 따른 코드·격리 replay 결과는 §9에 추가한다. 정책 발행·배포·기동 완료를 뜻하지 않는다.

## 1. 결론과 목표

권장안은 **기존 단일 AI 호출과 setup ledger를 유지하면서, ‘위험 하나라도 찾으면 대기’ 계약을 ‘기회와 위험을 함께 판정’하는 계약으로 교정**하는 것이다. BUY 비율을 목표로 지정하거나 CAUTION을 일괄 BUY로 바꾸지 않는다. 새 매매 family, 별도 실시간 AI 심판, 신규 scheduler, 대형 학습모델은 만들지 않는다.

목표는 비용 차감 후 작은 수익을 반복적으로 실현할 수 있는 진입 기회의 적절한 참여다. 다음을 별도로 측정한다.

- 판단 품질: 당시 이용 가능했던 자료로 진입·유예·기각 사유가 타당한가.
- 참여 품질: 유효 기회가 AI·재확인·제출·체결 중 어디에서 사라졌는가.
- 경제성: 동일한 사전 고정 exit/비용 계약에서 비용 후 EV, 순익/일, 자본점유와 불리한 결과가 개선되는가.
- 운영 적용: 코드 검증, 배포, 후보 생성, PREOPEN 선택, PID 소비, 자연 실적은 각각 별도 상태다.

`순수익 +0.10% 목표 도달`은 한 경로의 사건이고, `비용 후 EV >= +0.10%`는 유효 결과 집합의 기대값 기준이다. 둘을 바꾸어 쓰지 않는다. 승률·BUY 건수·최대상승폭만으로 승격하지 않으며, 의도적으로 청산하지 않은 보유의 평가손실을 곧바로 진입판정 오답으로 사용하지 않는다. 그렇다고 실제 손절·음수 terminal·부분체결을 평가에서 제외하지도 않는다.

## 2. 점검 근거와 한계

### 2.1 기준 코드·일정

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [진행표 §4.4](../audit-reports/2026-09-05-postclose-work-inventory.md#44-ev승인최종검증-단계).
- 현재 KST `2026-09-13` 체크리스트는 없다. [9/14 체크리스트](../checklists/2026-09-14-stage2-todo-checklist.md)는 다음 거래일 owner 확인용이며 오늘의 실행권한으로 대체하지 않았다.
- workspace HEAD `b1891f9cd0c6acd4f086c64c030493bebe28da60` 위에 기존 미커밋 prompt/timing 변경 16개 파일이 있다. 이번 설계는 이 작업본을 점검한 것이며 전부 배포됐다는 뜻이 아니다.
- 선택 release 조회: `/home/ubuntu/KORStockScan-runtime-releases/entry-split-ai-policy-20260914`, 같은 `b1891f9c…` commit. `--check-cron`은 예약 routing 9개 정상, `preopen 2026-09-14 --print-plan`은 이 root를 가리켰다. 실제 PREOPEN/PID 소비는 확인하지 않았다.
- 기존 [prompt·수량 분리 리뷰](../audit-reports/2026-09-12-prompt-quantity-aftermarket-sor-policy-review.md)를 유지한다. prompt 선택은 수량·분할·scale-in owner를 가져오지 않는다.

### 2.2 동결된 비교 표본

source `2026-09-11`, KRX/KRX_REGULAR, 동일한 10개 request에 대한 다음 두 report를 출발점으로 삼는다.

- [V2.14.1 report](../../data/report/ai_prompt_detailed_paired_replay/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_14_1_timing_aware_setup_risk_adjudicator_venue_krx_session_krx_regular.json): 생성 `9/13 13:14:50`, `artifact_content_sha256=c9edf0ff69213440217aea2b6dd6f94b428201a42d2a6a2fb2fcf298d2a793b0`.
- [V2.15.1 report](../../data/report/ai_prompt_detailed_paired_replay/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_15_1_timing_aware_bounded_recovery_venue_krx_session_krx_regular.json): 생성 `9/13 13:12:06`, `artifact_content_sha256=beb4bbeeb94f1ee944c85ba61b07b5c995b64a2f02f56c61ad86e379f2385690`; 당시 composer는 `entry_decision_composer_policy_v10_timing_aware`. 현재 작업본의 후속 composer와 다르므로 최신 코드 replay라고 표시하지 않는다.

| 측정 | V2.14.1 | V2.15.1 |
| --- | ---: | ---: |
| 원 AI verdict | CAUTION 9 / VETO 1 | CAUTION 8 / VETO 2 |
| report composed action | WAIT 9 / DROP 1 | WAIT 8 / DROP 2 |
| setup READY | 6 | 동일한 6 |
| READY에 가상 PASS를 넣은 읽기 전용 검증에서 거절 | 6 | 동일한 6 |
| 그중 blocking-code 없이 bounded risk만 존재 | 2 | 동일한 2 |

실제 AI가 PASS를 냈다가 검증기에 의해 변경된 사례는 아니다. 가상 PASS 검사는 허용 가능한 판정 공간을 점검한 것이며 실주문·경제성 표본으로 세지 않는다. 두 버전의 10건은 20개 고유 기회가 아니다. eligible 148건 중 10건(6.76%)을 평가했으므로 시장 전체의 편향 정도나 수익성을 확정할 수 없다. 이미 사후 결과를 읽은 이 10건은 개발/회귀 표본이지 독립 holdout이 아니다.

두 report 모두 `candidate_execution_cost_observed_count=0`, `candidate_probe_cost_adjusted_ev_pct=null`이다. 기존 자료만으로 새 후보가 +0.10% 승격 조건을 충족한다고 주장할 수 없다. 정확한 entry 비용·실행가능 경로를 기존 label owner에서 확보하거나 결손 사유를 유지해야 한다. 위 digest는 report가 선언한 content hash이며 파일 byte hash와 혼동하지 않는다. 재생성 전에는 둘 다 publisher 계약으로 다시 검증·보존한다.

### 2.3 확인된 결함·설계 위험

| 항목 | 근거/판정 | 보완 범위 |
| --- | --- | --- |
| F1 PASS 계약 불일치 | [prompt](../../src/engine/ai_prompt_contracts.py)의 ‘no blocking risk’와 [validator](../../src/engine/scalping/entry_setup_evidence.py)의 `PASS && any corroborated_risk_codes => reject`가 다름. bounded risk도 PASS를 불가능하게 함 | 최우선. hard/source 차단과 판단상 주의사항을 구분하고 prompt/validator/composer를 동시에 맞춤 |
| F2 보조 수급의 단방향 사용 | 같은 evidence builder에서 프로그램·외국인·기관 매도는 adverse fact가 되지만 반대 방향은 대응하는 supportive fact가 되지 않음 | 긍정/부정/중립/결측의 동일 freshness·기간·단위 계약. 긍정 수급의 단독 BUY 권한은 금지 |
| F3 WAIT 의미 혼합 | [runtime adapter](../../src/engine/ai_engine_openai.py)는 probe intent가 있으면 composed BUY도 WAIT로 투영. CAUTION·arm·미제출을 동일 실패로 집계하면 오판 | raw AI/composed/runtime/recheck/accepted submit을 따로 집계. 표시 수정과 실주문 경로 변경을 분리 |
| F4 timing의 의미·과잉차단 위험 | `first_watch_epoch`가 실제로 첫 promotion 시각. `completed_uptrend_horizon_min`과 return의 최댓값을 각각 고르면 서로 다른 horizon이 합쳐짐. 양의 endpoint return은 연속 상승시간이 아님 | 시간/가격 짝과 정확한 event 역할 교정. 600초·3회·1% 조합을 경제적으로 검증된 추격 차단으로 취급하지 않음 |
| F5 목표와 primary outcome 불일치 | [full-cost aggregate](../../src/engine/scalping/ai_decision_quality.py)의 primary는 `cost_adjusted_end_return_pct`. 작은 수익 first-hit 진단은 execution proxy이며 그 자체로 fee/tax net EV가 아님 | 동일 비용·exit 계약의 terminal 경로를 평가. MFE나 target touch를 실현수익으로 바꾸지 않음 |
| F6 실행·검증 세대 불일치 | V2.15.1 저장 report와 현재 composer가 다름. workspace 신규 버전과 선택 배포도 별도 | 원본 보존 후 prompt/evidence/composer/label/consumer 전체 hash를 결속 |
| F7 risk-code와 fact의 연결 부족 | validator는 canonical code와 fact 집합 소속은 검사하지만 모든 code의 해당 adverse fact 연결을 요구하지 않음. 001450의 V2.14.1은 ledger risk가 LIQUIDITY_FRAGILE뿐인데 ADVERSE_TAPE도 응답 | 기존 모듈 안에서 작은 code-to-fact mapping으로 의미 검증. 근거 없는 code를 조용히 삭제해 BUY로 수리하지 않음 |

F4의 예: `1m=+1.1%, 60m=+0.01%`에서 최댓값을 따로 취하면 ‘60분 구간·1.1% 상승’처럼 사용될 수 있다. 이는 정적 로직 반례이며 실제 장중 오주문 발생을 주장하는 것이 아니다. `first_seen_price`도 promotion 시각과 같은 관측인지 확인하기 전에는 first-watch 가격으로 결속하지 않는다.

## 3. 외부 전문지식의 적용

조회일 `2026-09-13 KST`. 아래는 열람한 1차 자료와 이 프로젝트에 대한 설계적 적용이며, 외부 전문가에게 실제 검토를 의뢰한 기록은 아니다.

| 자료 | 확인한 내용 | 여기서 채택/배제할 것 |
| --- | --- | --- |
| [OpenAI Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) | task-specific 평가, 실제 입력분포, 단계별 평가, 사람의 기준과 대사, pairwise/블라인드 평가의 활용 | raw verdict와 각 adapter를 따로 평가. 답변 순서·길이 편향을 통제. 새 평가 플랫폼이나 상시 다중 AI는 도입하지 않음 |
| [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) | few-shot 예시는 다양한 입력과 원하는 출력 유형을 포함 | 진입 가능·실제 위험·일시 유예·근거 부족을 고르게 예시화. 출력 BUY 할당량을 정하지 않음 |
| [Cont, Kukanov, Stoikov: The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402) | 미국주식 표본에서 짧은 구간 가격변화와 주문흐름 불균형·깊이의 관계를 연구. 거래량만의 관계보다 견고한 설명을 제시 | 기존 신뢰 가능한 체결·호가·가격반응을 함께 해석. 원천 없는 OFI를 새로 만들거나 취소잔량 감소를 매수체결로 간주하지 않음 |
| [Gould, Bonart: Queue Imbalance as a One-Tick-Ahead Price Predictor](https://arxiv.org/abs/1512.03492) | Nasdaq 10종목의 다음 mid-price 방향 예측에서 queue imbalance의 유용성과 tick 크기에 따른 차이를 확인 | 단기 방향 증거와 수분 후 실행가능 순이익을 분리. 미국시장 계수·임계값을 KRX/NXT에 복사하지 않음 |
| [Bailey 외: The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | 후보 선택 과정 자체가 out-of-sample 성과에 미치는 과적합 위험과 평가 방법을 다룸 | 버전·시행 횟수·개발 표본을 기록하고 미사용 날짜/episode를 별도 검증. 같은 10건에 BUY가 나올 때까지 수정하지 않음. 새 대형 교차검증 framework는 만들지 않음 |

외부 지식은 판단 rubric과 검증 설계에 활용한다. 뉴스·인터넷의 현재 평가를 과거 request에 넣지 않으며 계좌·원장·원본 prompt/payload를 외부 서비스에 업로드하지 않는다. Provider/model/route 변경은 이번 안에 없다.

선택적 전문가 검토는 구현 후 판단이 갈리는 기존 사례의 짧은 블라인드 packet으로 제한한다. 시장미시구조/집행 경험자는 ‘당시 체결 가능한 기회인가’, 평가 경험자는 ‘질문·label·표본이 답을 유도하는가’를 검토한다. 버전명·미래 차트·사후 PnL을 숨긴 판단 검토와, 사후 결과를 보는 성과 검토를 분리한다. 사람 검토·고성능 모델 비교가 필요해도 별도 의뢰/데이터 제공/비용 권한을 먼저 확인하며 일별 PREOPEN의 새 필수 승인 gate로 만들지 않는다.

## 4. 권장 판정 계약

### 4.1 기회·주의·차단 분리

기존 `entry_setup_evidence_v1`과 AI 응답의 6개 필드를 우선 재사용한다. 단순 점수 합계, 찬성 fact 개수, LLM confidence를 수익확률로 쓰지 않는다.

| 입력 상태 | 허용 판정 | 필수 근거 |
| --- | --- | --- |
| source unusable / 실제 INVALID | INSUFFICIENT / VETO | 현행 source·invalidation 근거. 좋은 수급으로 상쇄 불가 |
| READY + 실제 blocking risk 없음 + setup/trigger 지지 | PASS 가능 | setup과 trigger에 해당하는 정확한 supportive ID. bounded contradiction이 있으면 그것도 인용하고 무시하지 않았음을 검증 |
| READY + 해소되지 않은 실행상 주의사항 | CAUTION | 해당 adverse fact와 기존 owner가 확인 가능한 recheck 조건 연결 |
| WAIT_CONFIRMATION | CAUTION 또는 근거 있는 VETO | 기존 trigger·micro·source 재확인. 모든 선택 입력이 완벽해질 때까지의 무기한 대기를 요구하지 않음 |
| UNCONFIRMED | 현행 discovery/recheck 또는 종료 | setup을 발명하지 않음. 새 신호가 오면 새 identity로 평가 |

PASS의 의미는 ‘검토한 entry 위험이 이 setup을 막을 정도는 아님’이다. 주문 허가나 수익 보증이 아니다. 새 계약에서는 `NO_BLOCKING_RISK`와 bounded contradiction의 동시 존재가 가능하되, 실제 blocking code/invalidation이 있으면 PASS가 불가능해야 한다. risk code-to-fact mapping을 공유해 근거 없는 ADVERSE_TAPE 등의 출력은 명시 오류로 남긴다.

READY 자체를 BUY 정답 label로 삼지 않는다. 특히 실제 liquidity unusable·대량매도·구조붕괴는 유지한다. F4처럼 새로 만들어진 timing proxy와 이 기존 차단을 분리한다.

### 4.2 입력 균형과 시간축

- 수급은 동일한 source/as-of/기간에서 supportive/adverse/neutral/unavailable을 구분한다. 금액·수량·누적량·증분을 섞지 않으며 observed zero와 missing을 구별한다.
- 긍정 수급은 이미 유효한 setup의 판단 근거다. 부정 수급을 무조건 취소하거나 없던 setup을 만들지 않는다. 여러 수급 지표가 같은 거래를 반영하면 독립 증거처럼 여러 번 가산하지 않는다.
- 현재 신뢰 가능한 tape와 실제 가격반응을 완료 분봉의 구조·회복과 함께 읽는다. 모든 1/5/15/60분 방향 일치를 추가 필수조건으로 삼지 않는다.
- `first_detected`, `first_watch`, `first_promotion`, `current_promotion`, `ai_request`, `ai_response`, `submit`을 존재하는 원 event에만 연결한다. 없는 최초 감시시각은 null/직접 사유다.
- horizon과 수익률은 같은 쌍으로 사용한다. 연속 추세 시작이 별도로 입증되지 않으면 ‘구간 수익률’이라고 부른다. 감시가 오래됐다는 이유만으로 과열·진입 실패를 단정하지 않는다.
- timing 보완은 늦은 추격을 판별할 근거를 정리하는 작업이지 600초/3회/1%를 새 hard gate로 확정하는 작업이 아니다. 새 `.1` proxy는 근거 수준에 맞춰 관찰/주의로 낮추는 안을 검증하고, 현행 실제 overextension/price guard는 그대로 둔다.

### 4.3 WAIT 종료와 실제 소비

새 scheduler나 별도 무한 감시 queue 대신 기존 [entry_opportunity_recheck](../../src/engine/scalping/entry_opportunity_recheck.py)와 [sniper state handler](../../src/engine/sniper_state_handlers.py)의 pending/expiry 소비를 재사용한다.

각 WAIT은 `reason/fact → existing recheck condition → 기존 policy의 기한·시도 상한 → terminal`을 연결한다. 기존 `recheck_reasons`, `entry_probe_intent`, attempt ID, arm 시각 및 expiry 사유를 먼저 활용한다. 기존 코드에서 consumer가 없는 조건만 좁게 보완하며 새 TTL 숫자를 AI가 만들지 않는다. 실행 가능한 기한 owner가 없는 경우는 구현 착수 시 명시적 계약 결손으로 남기고 임의 시간을 주입하지 않는다.

로그/보고는 `raw verdict → composed action → runtime action → recheck pending/confirmed/expired → submit accepted/rejected → fill/terminal`로 나눈다. 모든 WAIT이 새 AI 호출을 요구하지 않으며, 같은 입력의 반복호출·retry/cap 상향은 금지다. 이전 정책의 미제출 arm과 제출된 custody를 구분해 정책 전환 시 stale arm이 살아남거나 진행 주문의 복구가 사라지지 않게 한다.

## 5. 목적에 맞는 replay·경제성 설계

### 5.1 세 가지 평가를 분리

1. **시점 판단 검사**: 판단시점 이전의 completed bar·WS·수급만 본다. prompt가 상반된 근거를 읽는지, PASS/CAUTION/VETO가 계약상 가능한지 검사한다. 미래 수익률은 입력·fact 생성에 금지한다.
2. **고정 exit의 entry 품질 비교**: 동일한 신호·entry execution 가정·exit/시간종료·비용 프로필로 incumbent와 challenger를 비교한다. 수정은 entry 축 하나다. 순수익 +10bps 도달, 도달 전 adverse excursion, time-to-target, 미도달/시간종료 손익, tail을 함께 본다.
3. **실제 운영 실적**: broker 완료금액·비용이 대사된 terminal, 실제 손절 사유, 의도적 보유/수동 개입, 부분체결·HELD를 별도 cohort로 읽는다. 실현손실은 포함하고, 미종결 PnL은 null/미실현으로 유지한다.

기존 `ENTRY_PATH_PRIMARY_HORIZON=10m`, gross `+0.30%/-0.70%` first-hit는 tight-stop 진단 계약이다. 실제 사용자 손절선으로 가장하지 않고, optional full-cost label의 `primary_horizon_sec`와도 혼합하지 않는다. 보완 net-target 경로는 기존 실행가능 label producer의 선언된 primary horizon H를 사용하며, 비교 전에 H·순목표10bps·기존 exit/invalidation·비용/체결 가정을 동결한다. 다른 horizon은 설명용이며 모든 horizon 양수를 새 gate로 요구하지 않는다.

### 5.2 비용·미체결·시간종료

- `순손익 = 실제/CF 계약의 청산대금 - 매수대금 - 해당 비용`. 실행가격에 이미 반영된 spread/slippage를 다시 빼지 않는다. 실현 비용과 검증된 추정 비용 프로필은 표시를 달리한다.
- net +10bps 목표를 계산할 때 거래세·수수료·실행비용을 포함한다. 현재 gross +30bps에서 execution proxy만 뺀 값을 순수익으로 부르지 않는다.
- 목표 가격 touch나 MFE는 체결 증거가 아니다. bid/ask·depth·시점·route·fillability와 기존 체결 모델이 있어야 실행가능 CF로 계산한다. 같은 분봉 안 target/adverse 선후가 불명확하면 ambiguous로 남긴다.
- 목표 미도달·시간종료·음수 terminal도 동일 exit 규칙으로 포함한다. 자료가 H까지 있어야 하는 것은 미종결 경로이고, 실제 계약상 양쪽 결과가 이미 terminal이면 이후 전체 자료를 추가 요구하지 않는다.
- WAIT→재확인→지연 진입은 그 시점의 가격과 같은 exit 규칙으로 계산한다. arm에 즉시진입의 수익률을 붙이지 않는다. 확인된 미진입의 노출값 0과 미관측 결과 null을 분리한다.
- 동일 종목의 겹치는 attempt를 독립 이익 기회로 합산하지 않는다. trade/episode 수준 집계와 capital-time/일별 집계를 함께 남긴다. 정책 승격의 현행 분모를 늘리기 위해 단순 promotion 횟수를 사용하지 않는다.

기존 full-cost companion에 정확한 entry 경로가 없으면 `source_gap`이다. code/판정 검증은 계속할 수 있지만 정책에 유리한 비용0·사후 임의 exit·수익 표본만으로 경제성을 채우지 않는다. 보완 primary는 기존 `entry_cost_aware_opportunity`/full-cost 집계 안에서 versioned exit-contract를 연결한다. raw end-return은 진단으로 보존하며, 새 terminal 경제성에 더해 end-return도 양수여야 한다는 이중 gate는 만들지 않는다.

### 5.3 적은 호출로 검증하는 순서

- 먼저 기존 eligible 148건의 deterministic 상태·위험 유형·PASS 허용 가능성을 Provider 없이 전수 대사한다. 이는 계획된 다음 작업이며 이번에 148건을 전부 재평가했다는 뜻이 아니다.
- 이미 본 10건은 A/B 회귀용으로 고정한다. 두 계열의 개선안은 각 1개만 만들고 기존 모델/route·호출 상한으로 비교한다. 예산을 늘리려고 명령을 나누거나 버전을 반복 발급하지 않는다.
- provider 호출 전 prompt/evidence/schema/composer를 고정한다. 바뀐 prompt의 응답을 과거 응답으로 대체하지 않는다. 동일 계약/입력의 유효 checkpoint만 재사용한다.
- 별도 미사용 날짜/episode는 기존 replay budget 안에서 outcome-blind로 선정한다. 관련 trade/episode가 개발·검증 양쪽에 걸리지 않게 하고 label 관측창이 겹치면 경계를 분리한다. 표본 부족을 설계 실패로 부르거나 9/11 개발 표본을 holdout으로 재라벨링하지 않는다.
- 모든 paired 실행은 긍정·부정 판정 변화와 schema failure, Provider failure, 비용 결손을 함께 보존한다. BUY가 없으면 입력·규칙·실제 기회 부재 중 어느 원인인지 설명하고, BUY가 나올 때까지 같은 자료를 반복 호출하지 않는다.

## 6. 최소 구현 작업과 종료조건

아래 W1–W6은 이 계획의 작업 순서이며 native recommendation ID나 새 운영 owner가 아니다. 현재 변경 16개 파일을 먼저 대사하고 기존 구현·테스트를 재사용한다.

| 순서 | 기존 수정 위치/consumer | 최소 작업 | 종료조건 |
| --- | --- | --- | --- |
| W1 계약 동결·분모 | `ai_decision_quality.py`, 기존 report | old hash/버전/10개 ID/148개 eligibility·실제 선택 root를 고정. F1/F4/F7 반례 및 경계 fixtures 추가 | 입력·fact·위험·output·배포 세대가 구분되고 미래자료 누출 0 |
| W2 양방향 판정 | `entry_setup_evidence.py`, `ai_prompt_contracts.py`, `ai_engine_openai.py` | bounded PASS 계약, 긍정 수급 fact, risk↔fact mapping, timing 의미 보정. 두 계열 공통 builder 재사용 | hard/invalid PASS 0, 필수 입력 결손 fail-closed, bounded risk만으로 일괄 PASS 거절하지 않음. old 버전 회귀 보존 |
| W3 WAIT consumer | 위 adapter, `entry_opportunity_recheck.py`, 필요한 handler 부분만 | 이유→기존 recheck/expiry 연결, raw/composed/runtime/submit 분리, stale arm 정책 전환 검사 | 모든 테스트 WAIT에 직접 consumer 또는 명시 terminal/결손이 있음. 중복 호출·중복 submit·quantity 권한 변경 0 |
| W4 목표 일치 평가 | `ai_decision_quality.py`, 필요 시 기존 `micro_reversion/ai_quality_bridge.py`의 label producer | 기존 비용/exit 경로를 연결하고 terminal-based 경제성과 raw end-return 진단 분리. 손절/HELD/partial/CF 구분 | 같은 입력·비용·exit에서 결과 재현, null·분모 보존. target touch를 체결·수익으로 승격하지 않음 |
| W5 재평가·선정 | 기존 `entry_setup_paired_replay_batch.py`, `ai_action_outcome_calibration.py`, `micro_reversion/main_ai_prompt_optimizer.py`, `main_ai_prompt_consumer.py` | bounded paired 실행, 버전별 집계·calibration·당일 고정 selection·후행 hash 갱신 | 원 generation 보존, 사용한/미사용 표본 분리, schema/consumer 결함 0. 경제성 충족/미달/미관측 별도 판정 |
| W6 정책·PREOPEN 연결 | `entry_setup_live_policy.py`, 기존 rollout/activation/launcher 및 summary | 새 계약 registration·검증, exact-date 발행/선정 및 예상 fallback 대사 | 비용 후 +0.10% 경계 통과와 적법한 blocked/hold가 테스트로 재현. 배포/PID는 별도 receipt |

새 Python 파일·새 CLI·새 report producer·새 cron은 기본 0개다. 필요한 필드는 기존 artifact의 작은 versioned section으로 넣는다. shared evidence·validator의 의미가 바뀌므로 기존 2.14/2.15 또는 동결된 `.1` hash를 그대로 덮어쓰지 않는다. 제안 명칭은 `V2.14.2 / V2.15.2`이며 실제 등록은 구현 시 충돌 검증 후 각각 한 번 한다. 버전 문자열만 늘리는 것이 아니라 지원 registry·composer·evidence·consumer 검증을 함께 연결한다.

## 7. 정책 자동화와 과도한 조건의 처리

### 7.1 현재 경로와 범위

현재 코드에는 `entry_setup_paired_replay_batch → publish_live_candidate → 다음 PREOPEN entry_setup_live_policy → runtime loader/AI adapter` 경로가 있다. 설치 routing 조회도 정상이다. 새 설계는 아직 이 경로에 배포/선택되지 않았다.

기존 [auto-promotion manifest](../../data/runtime/scalping_prompt_auto_promotion_20260914_407fb92c.json)는 `2026-09-14 07:35`부터 V2.15+ 후보, V2.14 fallback, 기존 수량 owner를 선언한다. 이는 새 버전 번호만 등록하면 무조건 적용한다는 뜻이 아니다. **V2.14 계열 개선은 fallback 유지보수 경로, V2.15+는 기존 candidate 자동 승격 경로**를 각각 대사한다. V2.14.2를 V2.15 floor를 우회해 자동 선택하지 않으며, fallback 교체가 immutable pin의 의미 변경이면 해당 범위의 배포 승인/receipt를 연결한다. 기존 승인된 일별 소비에 반복 수동승인을 추가하지 않는다.

### 7.2 유지할 조건과 제거/수리할 조건

| 유지 | 제거·수리 또는 별도 진단 |
| --- | --- |
| source/identity/date/hash·실행가능 비용, 실제 hard safety, owner/custody, 정상 rollback | source 수리에 양수 EV나 실체결을 요구하는 것 |
| normal candidate의 비용 후 EV `>=+0.10%`, 현행 누적 exposure 10건·3종목, paired delta >0, 해당 tail guard | optional 결측/약한 risk 하나로 PASS를 불가능하게 만드는 것 |
| 현행 누적/버전 분리·검증 창. 표본은 통계적 확실성 보증이 아니라 최소 floor | 임의 20/30일 추가, 모든 horizon 양수, 모든 지표 동시 일치, BUY 할당량 |
| 상대적으로 더 좋은 incumbent의 정상 carry | 후보가 +0.10%라도 incumbent보다 열등한데 강제 교체하는 것. 개선 delta 미달은 적법한 hold이지 handoff 장애가 아님 |
| exploration의 실제 runtime 권한·기존 cap과 별도 promotion 경계 | `one_share_exploration`을 source-only라고 부르거나 normal 승격에 불필요한 1주/수량 gate를 붙이는 것 |
| policy별 실제 fresh recheck와 최종 submit guard | 같은 조건을 이름만 바꿔 중복 요구하는 것. 동일 최신 입력 증거의 재사용 가능 여부는 owner별로 확인 |

`_full_cost_economics_pass`의 ‘source-only learning’ 설명과 실제 exploration caller는 구분해 문구/테스트를 바로잡는다. 정상 승격의 +0.10% floor를 지우지 않는다. 경계 테스트는 `0.099/0.100/0.101`, delta `음수/0/양수`, 비용 `유효/null/중복차감`, 날짜·pin 불일치로 나눈다. +0.10%라는 숫자만 충족하면 무조건 발행한다는 계약은 아니다.

### 7.3 최소 재생성과 다음 장전

review/fix/targeted validation 뒤, 변경된 최초 producer부터 마지막 consumer까지만 재생성한다. 입력 label이 바뀌지 않았다면 거대한 bridge·EOD·holding·widget·episode report는 다시 만들지 않는다. 미래 outcome을 candidate 입력으로 역류시키지 않으며, 구 prompt checkpoint를 새 prompt 결과로 재사용하지 않는다.

기본 순서는 `필요한 entry label/evidence → 두 계열 detailed replay → 기존 batch/candidate → calibration → 당일 실행 선택을 보존한 optimizer → metadata rebind → entry consumer → 영향받은 summary/checklist/strict`다. 설치 wrapper 전체를 실행하면 holding Provider 등 무관한 부작용이 있으므로 부분 명령과 root/output을 먼저 검토한다. metadata-only rebind로 live candidate가 재발행됐다고 주장하지 않는다. 후보 재발행이 필요하면 해당 publisher의 기존 contract로 명시 수행한다.

선택 release는 직접 수정하지 않는다. 별도 검토 commit으로 수리하고 공유 writer/consumer와 source pin을 대사한 뒤 승인된 안전 구간에서만 배포한다. 다음 장전 기한까지 증거/배포/정책이 닫히면 기존 예약이 exact-date 정책을 소비한다. 기한을 넘으면 기존 거래일 calendar와 07:35 cutoff 계약으로 다음 유효일로 이관하고, 전일 env 복사·과거 PASS·수동 강제선택으로 내일 적용을 가장하지 않는다.

따라서 `9/14 적용 가능 여부`는 W1에서 비용/경로와 현재 selection·배포의 최초 결손을 확인한 뒤 판정한다. 이 계획만으로 다음 장전 새 정책 생성을 보장하지 않는다. code/판정 검증이 끝났지만 경제성 또는 배포가 남으면 각각 `code_review_closed / economics_pending / deployment_pending`으로 구분한다.

## 8. 검증·handoff

후속 구현의 targeted tests는 기존 `test_entry_setup_evidence.py`, `test_ai_engine_openai_transport.py`, `test_ai_decision_quality.py`, `test_entry_opportunity_recheck.py`, `test_entry_setup_live_policy.py`, `test_entry_setup_paired_replay_batch.py`, `test_main_ai_prompt_optimizer.py`와 영향받은 activation/rollout/handler 테스트만 사용한다. 전체 매매 suite 재실행·Provider 추가호출을 코드 리뷰의 형식적 조건으로 삼지 않는다.

필수 반례: bounded PASS 허용/실제 blocking PASS 금지, 위험 code↔fact 불일치, 선택 입력 결측·0·stale, 긍정/부정 수급 같은 source gate, 다른 horizon 혼합, 첫 watch/promotion 구분, reset 부재와 미관측 구분, WAIT 해소/만료·정책교체·중복 submit, 목표 도달 후 하락·목표 전 손절·동일 bar 선후불명·미체결·비용결손·중복 비용, 구버전 hash와 신규 schema 거부, 정확히 +0.10% 정책 경계.

의미 보완에는 내부 English ASCII prompt, compile/import, 관련 pytest, `git diff --check`를 적용한다. 문서에는 owner·링크·print-only parser를 적용한다. 디자인 검증 통과를 code/replay/deployment/economics 완료로 대체하지 않는다.

후속 실행 시 기존 9/14 owner를 사용한다: `CodeImprovementWorkorderReview0914`(허용 구현), `MainAIQualitySourceGapMainAIAllocatorSubmittedTraceCustodyRepair0914`(AI→제출 귀속), `ThresholdEnvAutoApplyPreopen0914`(정책), `RuntimeEnvIntradayObserve0914`(실제 소비). 각 항목의 실제 Source/Acceptance·권한을 다시 읽고 연결하며 이 계획 때문에 체크박스를 완료 처리하거나 별도 중복 owner를 만들지 않는다.

기대효과는 선택적 주의사항 때문에 막힌 유효 후보를 다시 판단할 수 있게 하고, 끝없이 기다리다 늦게 진입하는 경로와 실제 기회 부재를 구분하는 것이다. BUY 증가·순이익 증가를 수치로 보장하지 않는다. 개선 수용은 기존 대비 순기회 포착·참여/체결·비용 후 terminal/자본시간을 함께 검증한 뒤 판정한다.

### 최초 문서-only 작업의 검증 결과

- self review → 보완 → 재리뷰: 근거 digest를 원 report와 대사하고, 비용 결과 0건과 9/14 적용 미보장, 구 checkpoint 재사용 금지를 명확히 했다. 문서의 owner/권한/세대 구분에서 잔여 finding 0이며 F1–F7의 코드 수리가 끝났다는 뜻은 아니다.
- 로컬 링크 13개 존재 확인. print-only parser 성공(`count=30`), 위에서 참조한 4개 기존 ID는 각각 현재 parsed owner 1개다. 과거 참조 항목을 오늘 OPEN으로 이관하지 않았다.
- `git diff --check` 및 새 문서의 whitespace 검사에서 오류 0. 새 문서는 untracked이므로 `--no-index --check`도 사용했고 exit 1은 새 파일 차이이며 whitespace 출력은 없었다.
- OpenAI Docs는 실제 분포/블라인드/단계별 평가 원칙에, review-gate는 문서 검증과 코드·배포·경제성의 분리 및 최소 재생성 범위에 반영했다.
- 문서-only 범위이므로 Python trading pytest/compile, Provider replay, 장후 재생성은 수행하지 않았다. 런타임 코드·정책·PID·선택 원장·cron 변경, commit/push 및 외부 sync도 미실행이다. 기존 미커밋 코드 변경은 보존했다.

## 9. 사용자 구현 지시 후 실행·리뷰 결과

실행일 `2026-09-13 KST`, replay source date `2026-09-11`. **코드 계약 보완은 검증됐지만 실제 AI의 WAIT 편향 해소와 수익 개선은 미입증**이다. 아래 모델 응답 오류 1건·entry 비용 근거 결손·미배포를 포함해 종합 완료/GREEN 또는 다음 장전 새 정책 적용으로 보고하지 않는다.

### 9.1 구현과 직접 consumer

| 작업 | 실제 변경·검증 | 남은 조건 |
| --- | --- | --- |
| W1 | verified payload journal에서 KRX regular 적격 148개 입력을 Provider 없이 재구성. 각 계열 READY 8 / WAIT_CONFIRMATION 41 / UNCONFIRMED 32 / INVALID 67, evidence 검증 오류 0. 기존과 같은 10개 trace를 outcome-blind 선택 계약으로 재사용 | 10개는 개발/회귀 표본이며 독립 holdout 아님 |
| W2 | V2.14.2/V2.15.2 공통 English ASCII prompt·balanced evidence·composer 등록. bounded risk의 PASS 허용, 위험별 fact 결속, 수급 양방향·neutral/freshness, promotion/first-watch와 horizon 의미 교정 | 실제 모델이 PASS를 선택하는지는 별도. 기존 hard/source/INVALID 차단 유지 |
| W3 | READY/CAUTION에 기존 `MICRO_PRICE_RESPONSE_RECHECK` 연결. raw PASS → composed BUY → runtime guarded WAIT/probe intent를 테스트. 기존 recheck/expiry·최종 authority·수량 owner 유지 | 실제 accepted submit/PID 소비 미관측. arm 수는 BUY·수익 표본 아님 |
| W4 | 기존 bridge 안에 `entry_terminal_exit_net10bps_v1` 추가. 검증된 수량별 bid sweep·비용을 소비하는 +10bps net / 기존 adverse / 선언된 primary H의 최초 terminal 평가. terminal 이전 MAE/점유시간과 raw end-return을 분리 | 실제 entry 비용/실행가능 원천 필요. CF는 실제 체결 아님 |
| W5 | 기존 detailed publisher로 두 버전 각 10개 격리 재평가. batch 기본 candidate를 V2.15.2, optimizer 순서를 V2.15.2→V2.14.2→기존 V2.16으로 등록하고 calibration/consumer 회귀 검증 | canonical batch/candidate/calibration/optimizer/consumer/strict 재생성은 하지 않음. 아래 upstream integrity·경제성 결손 때문에 승격 불가 |
| W6 | 새 evidence/composer/version registry와 기존 exact-date candidate→PREOPEN→loader 연결. 비용 후 0.099/0.100/0.101%·null 및 delta 음수/0/양수 경계 검증 | selected release 미갱신, 실제 정책 발행·PREOPEN·PID 소비 없음 |

새 Python 파일·CLI·report producer·cron은 0개다. 기존 16개 변경을 보존·보완했고 source-only bridge와 그 기존 테스트를 포함해 현재 코드/테스트 변경은 18개 파일이다. shared builder의 live 판단 영향은 runtime 변경으로 분류했으며 source-only 수리라고 위장하지 않았다. 실제 선택 배포본은 변경하지 않았다.

비용 평가는 이미 net인 값을 다시 차감하지 않고 `target touch`를 체결로 보지 않는다. 부분/미체결·원천 공백·동일 timestamp의 모호한 순서·비용 미검증은 제외/결손이다. 현행 `BridgeConfig.target_liquidation_sec`의 기본 H=10초와 기존 adverse 값을 사용하며 새 실전 손절/청산시간을 설정하지 않았다. 따라서 이 비교 exit가 경제적 최적값이거나 의도적 장기 HELD의 실제 손실을 없앤다는 뜻도 아니다. 구 rebuild source에 새 exit flag가 없으면 구 결과를 그대로 재구성해 과거 hash를 조용히 바꾸지 않는다.

### 9.2 동결된 실제 재평가

기존 모델 `gpt-5.4-nano`, 기존 HTTP offline transport, `candidate-workers=2`, timeout 180초, 계열별 distinct request 상한 10을 사용했다. 기존 bounded schema retry를 포함한 실제 Provider attempt는 16+12=28회다. 총 20개 버전별 request는 고유 기회 10개이며, BUY가 나올 때까지 반복 호출하거나 retry/cap을 올리지 않았다.

기존 `ai_decision_quality.main`의 detailed 실행을 사용하되 `DETAILED_PAIRED_REPORT_DIR`만 `tmp/entry-balanced-adjudication-20260913/detailed`로 격리했다. 인자는 `--date 2026-09-11 --mode detailed --as-of 2026-09-12T21:30:00+09:00 --outcome-price-source auto --execute-candidate --venue KRX --session-bucket KRX_REGULAR --candidate-timeout-sec 180 --candidate-workers 2 --candidate-max-new-requests 10 --detailed-candidate-version <각 신규 버전> --write`다. 두 계열 모두 프로세스 exit 0이지만 report 판정은 아래와 같이 다르다.

| 결과 | V2.14.2 | V2.15.2 |
| --- | --- | --- |
| 생성시각 KST | 14:22:00 | 14:24:11 |
| 최종 raw 응답 | CAUTION 9 / 검증 거절 VETO 1 | CAUTION 10 |
| 유효 composed action | WAIT 9 | WAIT 10 |
| 최종 schema rejection / provider failure | 1 / 0 | 0 / 0 |
| report integrity | false | true |
| 기존 재확인 intent / probe arm | 9 / 9 | 9 / 7 |
| 검증된 entry 비용 pair / net EV | 0 / null | 0 / null |

- [V2.14.2 격리 report](../../tmp/entry-balanced-adjudication-20260913/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_14_2_balanced_setup_risk_adjudicator_venue_krx_session_krx_regular.json): byte SHA256 `015969113e46720500ef2842defc1b74ebc10373a940fd395bd340029e5f46e5`, content SHA256 `31c5d2527f392e831cd466e898e4aac265018252411548a52a024b24fabefb6a`, contract `35311eeae181807a8a0d3a4c1f5b7bc6f88fb78611a534e8b9cc64e63537aeae`.
- [V2.15.2 격리 report](../../tmp/entry-balanced-adjudication-20260913/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_15_2_balanced_bounded_recovery_venue_krx_session_krx_regular.json): byte SHA256 `fc96dc41b33be245b3744273d4d066c745943db663c25fa7cee0abe688c77e29`, content SHA256 `eb3497616d980a8710c1d67246da4bd12ad90abb97ba2ada99d3b533e6e7e110`, contract `043d76dd8be2e2c94431a2693d1290f9b29caa737010917b728d9ab81c60132c`.

동일 입력의 두 신규 계열 모두 READY 6건에 ledger 근거를 갖춘 가상 PASS를 넣으면 검증 오류 0·composed BUY 6건이었다. 이는 판정 가능한 범위의 확인일 뿐 실제 AI 응답·제출·수익이 아니다.

실제 AI는 READY 6개에도 CAUTION을 선택했다. 252990/019210은 반복 promotion 뒤 reset 부재, 475040은 늦은 timing과 프로그램 매도, 443670/001450은 유동성, 459510은 volume 확인 결손을 인용했다. 예전처럼 PASS가 코드상 불가능한 구조는 해소됐지만, 약한 위험을 AI가 얼마나 과대평가하는지는 이 결과만으로 닫히지 않는다. 분봉 상승추세가 있었다는 이유로 이 CAUTION을 자동 오답/BUY로 바꾸지도 않는다.

V2.14.2의 007540은 UNCONFIRMED인데 `VETO/STRUCTURE_INVALIDATED`와 `no_supported_setup`을 연결한 잘못된 응답이다. 실제 구조 무효 근거가 없어 `entry_risk_code_fact_binding_invalid`로 거절됐고, 앞선 INSUFFICIENT 오분류 retry도 보존했다. 검증기를 완화하거나 응답을 CAUTION/BUY로 고치지 않았다. 동일 오류 거절과 유효 `CAUTION/CONFIRMATION_MISSING` 수용을 회귀 테스트로 추가했다. 이 모델 준수 실패 1건을 코드 review finding 0에 포함해 지우지 않는다.

### 9.3 검증·자동화·잔여 handoff

- self review/fix/re-review에서 신규 prompt resolver 반환 계약, canonical JSON prompt hash 등록, source-only 수량의 경제성 승격 혼입, 종료 뒤 하락의 risk 재혼입, 초기 terminal의 raw horizon 완료 오표시와 malformed fact 입력을 보완했다. provider 실행 뒤에는 위 007540 반례 테스트와 의미 변화 없는 validator 줄바꿈만 추가했으며 prompt/evidence/composer 의미와 report 원본을 다시 바꾸지 않았다.
- 최종 targeted pytest **988 passed**, 기존 `pandas_ta` Pandas4 deprecation warning 1개. evidence/runtime transport/quality/recheck/bridge/live policy/batch/optimizer/activation/rollout/consumer/calibration 및 기존 restart/trace contract 15개 suite를 검사했다. 관련 compile 통과. 코드·직접 consumer의 검토 범위 잔여 finding 0이며 모델 준수·자연 경제성 완료는 아니다.
- 문서 print-only parser 성공(`count=30`), 연결한 기존 4개 owner는 각각 1개이며 체크박스는 OPEN을 유지했다. 이번 proposal/추가 handoff 링크는 존재 확인했고, 체크리스트의 기존 9/14 미래 source 링크 7회(6개 파일)는 `not_yet_due`로 분리했다. 이를 현재 링크 결함으로 고치거나 원천 파일을 합성하지 않았다. `git diff --check`와 untracked proposal의 `--no-index --check`에서 whitespace 오류 0이다. 외부 sync는 하지 않았다.
- 최종 engine 변경 10개 파일의 `relative path → 파일 byte SHA256` map을 key 정렬·ASCII compact JSON으로 직렬화한 bundle digest는 `911d133c3d2a011707d8c6a317bb4ee291af7059a0a9ecf53c57d08d34820bd1`이다. 대상은 §6의 기존 구현 파일들과 `ai_action_outcome_calibration.py`, `entry_setup_live_policy.py`, `entry_setup_paired_replay_batch.py`, `sniper_state_handlers.py`를 포함한 현재 `git diff --name-only`의 `src/engine/` 10개다. HEAD는 여전히 `b1891f9c…`이고 이 digest는 commit/배포 receipt가 아니다.
- 비용 후 EV **0.100% 이상 + paired delta 양수 + 기존 10 exposure/3종목·source/tail/pin**이면 normal candidate가 기존 자동 경로로 발행·로딩되는 것을 격리 테스트로 확인했다. 0.099%/null·delta 비양수는 정상 hold다. end-return 음수나 임의 20/30일·모든 horizon 양수·매번 사람 승인은 새 추가 gate가 아니다. V2.14.2는 fallback 계열이며 V2.15 floor 우회 후보가 아니다.
- 실제 원천 [action-neutral labels](../../data/report/ai_micro_reversion_materialized_replay_requests/ai_micro_reversion_action_neutral_outcome_labels_2026-09-11.json)는 holding 5개, entry 0개다(byte SHA256 `af6c507b9d803f2edb7d87db4faab371ca803b8dc997a73cc0a42a13dd3174e3`). 과거 bridge의 route/source 계약 결손도 새 비용 근거로 재라벨링하지 않는다. holding 자료를 entry에 이식하거나 동일 날짜 거대 bridge 재실행으로 없는 원천을 만들지 않았다.
- `9/13 14:20 KST` 읽기 전용 routing 확인은 선택 root `/home/ubuntu/KORStockScan-runtime-releases/entry-split-ai-policy-20260914`, commit `b1891f9cd0c6acd4f086c64c030493bebe28da60`, cron 9개 정상, 다음날 PREOPEN print-plan 동일 root였다. 따라서 **자동화 코드 연결은 확인, 새 코드의 실운영 자동 적용은 미배포·미승격**이다. 현재 PID·미래 기동은 검사/실행하지 않았다.

| 잔여 조건 | 기존 owner / 다음 안전한 작업 | 종료 검사 |
| --- | --- | --- |
| 모델의 잔여 CAUTION 편향·V2.14.2 준수 실패 | `CodeImprovementWorkorderReview0914`: 현재 10개를 개발표본으로 동결하고 미사용 날짜/episode의 outcome-blind 평가·필요 시 블라인드 사람 rubric 대사. 별도 모델/전문가 호출은 권한 확인 후 | 오류 원인별 분류, 독립 표본에서 기회·위험 판단과 불리한 결과를 함께 확인. BUY 할당량 없음 |
| exact entry 비용·실행가능 경로 | `MainAIQualitySourceGapMainAIAllocatorSubmittedTraceCustodyRepair0914`의 기존 제출 receipt 귀속과 source-quality owner에서 실제 제출만 exact join. 비제출은 N/A | 검증된 entry terminal label과 비용이 동일 trace/venue/session/수량/source로 연결. 결손은 null |
| 새 release/정책/PID | `ThresholdEnvAutoApplyPreopen0914`, `RuntimeEnvIntradayObserve0914` | 검토 commit의 별도 배포 승인·receipt 뒤 기존 candidate/PREOPEN/loader·PID 소비 확인. 그 전에는 기존 선택·fallback 유지 |

canonical report·batch·policy·요약은 변경하지 않아 이번 격리 결과로 운영 strict를 stale하게 만들지 않았다. W5의 실제 canonical 후행 재생성은 upstream schema/경제성 근거와 배포 경계를 해결한 뒤 필요한 consumer만 수행한다. 이번 지시에 포함되지 않은 배포·재기동·수동 env/주문·commit/push·외부 sync는 실행하지 않았다. 새 Provider 호출·거대한 전체 장후 재생성으로 이 잔여를 감추지 않는다.

## 10. 비교판정·기계론적 challenger 후속 시도

실행일 `2026-09-13 KST`, 동일 replay source date `2026-09-11`, 동일 KRX regular 10개 trace를 사용했다. 목적은 BUY 수를 강제로 늘리는 것이 아니라 `ENTER_NOW / RECHECK / BLOCK`의 기회비용을 직접 비교하고, 같은 evidence ledger를 Provider 없이 읽는 기계론적 판정기를 병행할 수 있는지 확인하는 것이다. 원본 입력·control·outcome join과 비용 proxy는 기존 detailed pipeline을 재사용했으며 새 모듈·CLI·report producer·cron은 추가하지 않았다.

### 10.1 비교형 prompt와 발견·수리한 결함

V2.14.3/V2.15.3은 위험을 `COMPENSATED / RECHECKABLE / BLOCKING`으로 나눠 판정했다. 실제 응답은 각각 `BUY 3 / WAIT 7`, `BUY 4 / WAIT 6`으로 WAIT-only 상태를 벗어났지만 비용 조정 노출 EV는 각각 `-0.971669%`, `-1.114980%`였고 paired delta·tail gate도 실패했다. 특히 모델이 `repeated_repromotion_without_reset`, `late_unreset_entry_timing`, 수급 divergence와 volume 결손 같은 부정 fact를 그 위험의 보상 근거로 다시 인용했다. 이는 보수성 완화가 아니라 근거 방향성 결함이므로 두 버전은 승격하지 않는다.

V2.14.4/V2.15.4에는 risk code별 `entry_action_counterweight_bindings_v1`을 추가했다. `COMPENSATED`는 producer가 정한 현재 positive fact 전체를 정확히 복사해야 하고, negative fact의 자기상쇄·일반적인 setup 문구 대체·부분상쇄를 모두 거절한다. 최초 V2.14.4 실행은 fact별 binding을 만들면서 risk code별 한 행을 요구하는 validator와 cardinality가 어긋나 3건을 schema rejection했다. 이 원본 report는 실패 근거로 보존하고 binding을 risk code당 한 행으로 고친 뒤 같은 10개를 한 번 재평가했다.

| 후보 | 최종 action | schema/provider 오류 | 노출 수/종목 | 비용 조정 노출 EV | 판정 |
| --- | --- | --- | --- | --- | --- |
| V2.14.3 | BUY 3 / WAIT 7 | 0 / 0 | 3 / 3 | -0.971669% | 근거 방향 결함·경제성/tail 실패, reject |
| V2.15.3 | BUY 4 / WAIT 6 | 0 / 0 | 4 / 4 | -1.114980% | 근거 방향 결함·경제성/tail 실패, reject |
| V2.14.4 repaired | BUY 1 / WAIT 9 | 0 / 0 | 1 / 1 | -0.340085% | 자기상쇄 제거, 표본·경제성/tail 실패, hold |
| V2.15.4 repaired | WAIT 10 | 0 / 0 | 0 / 0 | null | 유효 응답이나 노출/경제성 없음, hold |

- [V2.14.3 report](../../tmp/entry-comparative-adjudication-20260913/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_14_3_comparative_entry_adjudicator_venue_krx_session_krx_regular.json): file SHA256 `5fbde90a78c34d680b30598de53c8b3c14369d1d85f0884ebf35cb5f5f76b088`, contract `a510efd703450300b34ca3b444a2d6d917c99988d74f41ca45c310a0a997870a`.
- [V2.15.3 report](../../tmp/entry-comparative-adjudication-20260913/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_15_3_comparative_bounded_recovery_venue_krx_session_krx_regular.json): file SHA256 `7f7989eff5057c750e32fcc9a10c4223516c2338ddceebeec33a5ce127cd91f5`, contract `6c5fd39ee709e75c3cc81e349628d5d7a38dea8ca6d264524012cecc70101b1b`.
- [최초 실패 V2.14.4 report](../../tmp/entry-counterweight-adjudication-20260913/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_14_4_counterweight_bound_comparative_venue_krx_session_krx_regular.json): file SHA256 `9dc3cd1ab432d8718ea8e28192130e3f13f3000d4dcbcc742c01e94b5b5a9b18`, schema rejection 3.
- [수리 후 V2.14.4 report](../../tmp/entry-counterweight-adjudication-20260913-repaired/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_14_4_counterweight_bound_comparative_venue_krx_session_krx_regular.json): file SHA256 `12caca065750b640f4e09029f810e3309ec5e39bb3e2febe8a3f01de4f42e292`, contract `21ee4f749b8a46c45d23fd2c1558070c1499393b9d1602dd9f8b841328363043`.
- [수리 후 V2.15.4 report](../../tmp/entry-counterweight-adjudication-20260913-repaired/detailed/ai_prompt_detailed_paired_replay_2026-09-11_decision_quality_v2_15_4_counterweight_bound_bounded_recovery_venue_krx_session_krx_regular.json): file SHA256 `239ebbe169409d85c10c8e4fdf224993850d1e37c21508fe712cc268f56e1b09`, contract `3339f24d468437ffe433cba3a79f81673ba7e88eca8653f446c6bb715de8cf63`.

V2.14.4와 V2.15.4의 차이는 schema 실패가 아니다. 둘 다 같은 READY `459510`에서 결손 volume을 신뢰 가능한 micro 매수흐름·양의 가격반응·확인된 trigger로 상쇄할 수 있었지만, V2.14.4는 `ENTER_NOW`, V2.15.4는 유효한 `RECHECKABLE/RECHECK`를 선택했다. 즉 판정 자유도와 모델 변동성이 아직 남아 있다. 같은 표본을 BUY가 나올 때까지 다시 호출하지 않고 기계론적 challenger와 독립 날짜로 비교한다.

### 10.2 최초 기계론적 판정기

기존 [entry_setup_evidence.py](../../src/engine/scalping/entry_setup_evidence.py)에 `mechanistic_entry_thresholds_initial_v1`을 추가했다. 같은 `entry_setup_evidence_v1`, risk-to-fact binding, micro observation, liquidity/tail 입력만 소비하며 Provider·broker·account·order를 호출하지 않는다. 초기 규칙은 다음과 같다.

- source/구조/hard risk 또는 `INVALID/INSUFFICIENT`는 `BLOCK`한다.
- READY이고 모든 bounded risk에 위험별 정확한 counterweight가 있으며 micro·liquidity threshold를 통과할 때만 `ENTER_NOW`한다.
- 늦고 reset되지 않은 진입, 근거가 덜 갖춰진 READY, WAIT_CONFIRMATION/UNCONFIRMED는 기존 reason의 `RECHECK`로 돌린다.
- 경계값에서 이미 fragile risk가 발생하는 spread/fillability/ask-bid ratio는 동일 경계에서 상쇄하지 않도록 strict inequality를 사용한다.
- 정책은 `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true`가 아니면 validator가 거절한다. 빈 정책을 기본값으로 조용히 대체하지 않는다.

동일 10개 request에 적용한 최초 결과는 `ENTER_NOW 1 / RECHECK 9 / BLOCK 0`이다. 유일한 진입 후보도 `459510`이며 기존 10분 completed-bar 경로와 보수적 실행비용 proxy로 계산한 값은 `-0.340085%`다. 이는 실제 broker 실현손익이나 사용자가 의도적으로 오래 보유한 포지션의 평가가 아니며, 이 한 날짜의 negative proxy만으로 장기 전략을 부정하지 않는다. 다만 최소 `+0.10%` 정책 발행 근거로는 사용할 수 없으므로 이 초기 임계치는 live candidate가 아니다. 정책 content SHA256은 `a11c7325a4b0abebc1c5f6b3c44b47ff02c1a9e6c615626af3f585b6f5d3c6f7`이다.

### 10.3 장후 조정·자동적용 경계

기계론적 threshold policy에 다음 최소 승격 계약을 명시했다: 비용 조정 EV `>=+0.10%`, incumbent 대비 paired delta 양수, exposure 10건 이상, 3종목 이상, 독립 source date 2일 이상, bounded probe risk budget 통과, chronological holdout 필수. 이 조건은 0.1%보다 높은 확실성을 요구하는 임의 장벽이 아니라 한 날짜·한 종목·같은 개발표본 과적합을 막는 최소선이다. `+0.10%`에 미달하거나 비용이 null이면 정책을 만들기 위해 floor를 낮추지 않는다.

장후 튜닝은 새 파이프라인을 만들지 않고 기존 `detailed replay → cumulative calibration/optimizer → candidate → PREOPEN loader`를 재사용한다. calibration 구간에서 미리 제한한 작은 threshold 후보 집합 중 비용 후 순이익/일과 유효 참여를 우선 비교하고, 선택된 한 후보만 이후 chronological holdout으로 판정한다. holdout을 보고 후보를 다시 고르는 반복, 같은 날 튜닝·검증, BUY 비율 목표, threshold별 Provider 재호출은 금지한다. 실제 terminal 비용·부분/미체결·capital-time이 없으면 경제성은 null로 남긴다.

현재 상태는 `code_review_closed / offline_challenger_created / economic_gate_failed / deployment_not_authorized`다. 신규 `.3/.4`와 mechanistic policy는 live registry·batch 기본 후보·optimizer·PREOPEN loader에 등록하지 않았고 canonical 장후 산출물도 재생성하지 않았다. 선택 release는 여전히 `/home/ubuntu/KORStockScan-runtime-releases/entry-split-ai-policy-20260914`의 `b1891f9cd0c6acd4f086c64c030493bebe28da60`이다. 따라서 기존 자동화 경로는 존재하지만, 이 challenger의 **장후 자동 조정·정책 발행·실제 런타임 소비는 아직 자동화됐다고 볼 수 없다**. 독립 날짜에서 위 gate를 통과한 뒤 기존 W5/W6 consumer에 최소 등록하고 별도 배포/PREOPEN/PID receipt로 확인한다.

### 10.4 리뷰·검증 결과

- 비교 prompt/binding/validator/composer와 기계론적 policy/action을 다시 검토했다. 최초 binding cardinality 결함, numeric `0`을 missing으로 오인할 수 있던 threshold 읽기, fragile 경계값의 자기상쇄 가능성, 빈/권한 보유 policy의 묵시적 수용을 수정했다. 이 범위의 잔여 P0~P2 finding은 0이다.
- 직접 consumer 7개 suite는 **701 passed**다. `entry_setup_evidence` 단독은 **74 passed**이며 counterweight 방향성, 같은 evidence 소비, threshold 변화, `+0.10%` 이상 promotion metadata, offline authority와 fragile 경계를 검사한다. 관련 Python compile과 이번 변경 4개 파일 Black 검사, `git diff --check`, 문서 print-only parser(`count=30`)가 통과했다.
- 더 넓게 `test_sniper_scale_in.py`까지 합친 실행은 **1706 passed / 53 failed**로 전체 GREEN이 아니다. 실패는 주문 route·holding exit·기존 exploration state 등 이번 `.3/.4`/mechanistic 판정기 밖의 대형 legacy suite에만 있었다. 대표 실패 7개는 깨끗한 현재 HEAD `b1891f9c…` archive에서도 동일하게 재현해 이번 challenger 회귀와 분리했다. 이 기록은 해당 결함을 해결했다고 뜻하지 않으며, 이번 경제성 미달 후보를 승격하지 않는 이유와 별개로 기존 owner에서 수리해야 한다.
- Provider 재호출, canonical 장후 재생성, candidate 발행, PREOPEN 적용, commit/push, 배포·기동·주문은 수행하지 않았다.

## 11. 클린 베이스라인 누적자료 기반 기계판정기 정교화

사용자 후속 지시에 따라 기존 `ai_action_outcome_calibration.py` 안에 `mechanistic_entry_clean_baseline_refinement_v1`을 추가했다. 새 모듈·CLI·report producer·cron은 만들지 않았다. 작업폴더 코드에서는 기존 장후 calibration이 실행될 때 같은 detailed replay 원천에서 이 section을 다시 계산하고 `optimizer_handoff.mechanistic_entry_refinement`로 전달한다. 이 handoff는 source-only이며 자체로 runtime policy를 선택하거나 주문하지 않는다. 현재 선택 release에는 아직 배포되지 않았으므로 실제 예약 실행 receipt는 아니다.

### 11.1 학습 계약과 실제 분모

- 기준은 `2026-06-05T00:00:00+09:00` 이후 `entry / KRX / KRX_REGULAR`이다. evidence self-hash, request 결속, fresh-consistent source, offline authority와 보수적 비용이 모두 유효한 행만 사용한다.
- canonical detailed report 26개에서 동일 exact trace를 대사해 고유 936개를 유지했다. 동일 중복 281개는 한 번만 세고, evidence/outcome fingerprint가 충돌한 trace 10개는 전부 제외했다. request-comparison/evidence join 결손 1개도 제외했다.
- 9/7 self-hash cutover 전 report 21개는 행별 evidence self-hash·request 결속에 더해 calibration이 읽은 원본 파일 SHA256을 source contract에 고정해 사용한다. 과거 schema에 없던 내부 content-hash를 영구 승격 veto로 두지 않되, 9/7 이후 report는 기존 계약대로 내부 content-hash가 없거나 불일치하면 제외한다. candidate는 선택 trace fingerprint와 전체 accepted source-file SHA 목록을 함께 결속한다.
- evidence version은 v7 30개, v9 856개, v10 50개다. v11로 재계산되어 기존 generation과 충돌한 10개 trace는 이번 공통 분모에서 양쪽 모두 제외됐다. 과거에 없던 micro 필드를 0이나 정상으로 보간하지 않았고, 실제 micro observation이 있는 행은 50개로 별도 표시했다.
- 버전 공통 의미가 유지되는 `READY`, invalidation 없음, spread, fillability, top3 ask/bid ratio만 threshold 학습 입력으로 썼다. 미래 outcome·first-hit·MFE/MAE는 입력 feature가 아니라 평가 label로만 사용했다.
- 마지막 산출물 거래일 3개 `2026-09-09 / 09-10 / 09-11`을 holdout으로 고정했다. 9/11 유효 행이 충돌로 0개가 되어도 날짜 자체를 지워 9/4를 holdout으로 당기는 결함은 자체 리뷰에서 수정했다.

### 11.2 목적함수와 결과

기존 paired replay의 같은 경로 계약인 `target_first +0.3% / adverse_first -0.7%`에 `conservative_execution_cost_pct`를 정확히 한 번 차감했다. `same_bar_ambiguous`와 `neither_hit`는 0원으로 채우지 않고 censored 처리했다. 이는 분봉 경로 기반 counterfactual proxy이며 broker 체결·실현손익이 아니다. 별도로 `probe_cost_adjusted_mfe_pct >= +0.10%` 기회 빈도를 기록하되 target touch를 체결이나 순익으로 승격하지 않는다. 후보 자체 EV뿐 아니라 같은 trace의 기존 control action 대비 paired terminal delta가 calibration과 holdout에서 모두 양수여야 한다.

사전 고정한 80개 공통 threshold 조합 중 중복 선택집합과 최소분모 미달을 제거한 47개를 비교했다. calibration에서 비용 후 `+0.10%`를 통과한 후보는 0개였다. 최선의 진단 조합은 `spread <=40bp`, `fillability >=30`, `top3 ask/bid <=3`이었으나 결과는 다음과 같다.

| 구간 | 노출/종목/날짜 | terminal 평가 | 비용 차감 proxy EV | net +10bp 경로기회 | 판정 |
| --- | --- | --- | --- | --- | --- |
| calibration 8/6~9/4 | 29 / 23 / 15 | 24, censored 5 | `-0.459831%` | 13/29, `44.83%` | +0.10% 미달 |
| sealed holdout 9/9~9/11 | 2 / 2 / 2 | 2 | `-0.861735%` | 0/2 | EV·표본 모두 미달 |

전체 control action과 비교한 paired terminal delta도 calibration 769건에서 `-0.014351%`, holdout 75건에서 `-0.022980%`였다. 따라서 현재 결과는 `no_common_feature_candidate_meets_cost_adjusted_10bp_holdout_gate`, `policy_candidate=null`이다. 기회 경로가 44.83% 있었다는 사실은 작은 수익을 실제로 실현할 수 있다는 뜻이 아니다. 현재 +0.3/-0.7 비대칭과 보수적 비용에서는 target-first 빈도가 손실 경로를 상쇄하지 못했다. 사용자 의도의 장기 보유 손익 왜곡은 terminal first-hit로 분리했지만, 그 분리 뒤에도 단순 유동성 threshold만으로 +0.10% EV는 입증되지 않았다.

### 11.3 리뷰·자동화·다음 경계

- 자체 review에서 음수 비용의 censored 오분류, 사라진 최신 날짜 때문에 holdout이 이동하는 문제, 서로 다른 target/adverse 경로 계약 혼합 가능성, same-bar 0원 대입 가능성을 수정했다. 또한 cutover 전 report 내부 hash 부재가 좋은 후보도 영구 차단하던 과도한 gate를 행 self-hash+관측 원본 파일 SHA256 결속으로 대체했다. 경로 경계가 하나로 격리되지 않으면 promotion을 차단한다.
- synthetic 양수 자료에서는 calibration 10건/5일과 holdout 6건/3일이 각각 비용 후 +0.20%일 때만 hash-bound offline candidate가 생성되고, conflict 1건 또는 ambiguous-only 자료에서는 생성되지 않는 반례를 추가했다.
- calibration·optimizer·verifier와 기존 entry prompt/정책 직접 consumer 15개 suite는 최종 `1284 passed`, 기존 `pandas_ta` deprecation warning 1개다. 최종 verifier는 top-level refinement와 optimizer handoff의 동일성, `promotion_pass` boolean, candidate content hash·schema·offline authority 및 모든 promotion check의 명시적 PASS까지 검사한다. 관련 compile, Black, Ruff, `git diff --check`와 문서 print-only parser(`count=30`)도 통과했다.
- 작업폴더의 계산 경로는 기존 postclose calibration에 연결돼 배포 후 별도 새 cron 없이 지속 갱신될 구조다. 다만 현재 선택 release 미배포이고 candidate도 없으며 live registry/loader에 기계판정 family를 새로 연결하지 않았다. 따라서 **자동화 코드 연결은 검증됐지만 실제 예약 지속 튜닝과 런타임 적용은 아직 발생하지 않는다**. 정책 미생성은 과도한 gate가 아니라 현재 관측 EV·paired delta·holdout 표본 미달의 직접 결과다.
- 다음 정교화는 micro가 실제 존재하는 새 날짜를 누적해 공통-feature arm과 micro-enhanced arm을 같은 날짜/동일 terminal·비용으로 비교하는 것이다. 과거 886개에 micro 값을 합성하거나 threshold를 낮춰 BUY를 만들지 않는다. 기존 장후 owner가 +0.10%와 최소분모를 통과한 hash-bound candidate를 만들기 전에는 현재 기계판정기를 `RECHECK/BLOCK` 진단 challenger로 유지한다.

## 12. 종목군·진입경로 품질을 반영한 계층형 기계판정 구현안

현재 공통 판정기는 비교 기준으로 유지하되 최종 판정기로 승격하지 않는다. 고유 936개가 366종목에 분산되어 종목별 전체 row 중앙값이 1개이고, `READY`는 199개/134종목·종목별 중앙값 1개다. READY 5개 이상은 한 종목뿐이고 10개 이상은 0종목이며, micro가 관측된 READY는 6개/6종목이다. 이 상태에서 종목별 threshold를 직접 최적화하면 과적합이고, 반대로 공통 liquidity 3축만 쓰면 종목의 틱·변동성·평소 깊이·상승 지속시간을 잃는다. 따라서 **공통 safety → 종목군 prior → 충분한 경우에만 종목 residual → 실제 micro 확인**의 계층 구조로 구현한다.

### 12.1 진입품질 라벨: 최종 익절과 좋은 진입을 분리

실현 익절 여부는 경제성 사실로 보존하되 진입품질 정답으로 그대로 사용하지 않는다. 같은 entry anchor에서 비용 후 순수익 `+0.10%`에 처음 도달한 시각, 그 전 최대 역행폭과 체류시간을 결속해 다음 상호배타 라벨을 만든다.

| 라벨 | 의미 | 판정기 학습 역할 |
| --- | --- | --- |
| `CLEAN_FAST_PROFIT` | 실제 fill 뒤 bounded short window 안에 비용 후 +0.10%에 먼저 도달하고, target 전 near-stop·긴 underwater/sideways가 없음 | `ENTER`의 양성 정답 |
| `PROFITABLE_BUT_LATE` | 최종 비용 후 익절이지만 +0.10% 도달이 short window 밖이거나 자본 점유가 김 | 수익은 보존하되 진입시점은 `RECHECK` 정답 |
| `PROFIT_AFTER_DEEP_ADVERSE` | 최종 익절 또는 target-first라도 target 전에 손절거리의 큰 부분을 소진하거나 adverse threshold를 먼저 침범 | 진입시점 오류; `RECHECK|BLOCK` 정답 |
| `PROFIT_AFTER_SIDEWAYS` | target 전 neutral band 체류가 길고 유효 방향성이 늦게 나타남 | 진입시점 오류; `RECHECK` 정답 |
| `CLEAN_FAST_LOSS_OR_ADVERSE` | short window에서 adverse-first 또는 비용 후 손실 terminal | `BLOCK` 정답 |
| `CENSORED_OR_SOURCE_GAP` | horizon 미성숙, 동일 bar target/adverse, 비용·fill·route·price path 결손 | 학습·EV에서 제외하고 결손 사유 유지 |

`PROFITABLE_BUT_LATE`, `PROFIT_AFTER_DEEP_ADVERSE`, `PROFIT_AFTER_SIDEWAYS`를 손실 거래로 재라벨링하지 않는다. 이들은 **실현 PnL은 양수지만 entry timing precision에는 실패**한 별도 class다. 반대로 counterfactual target touch를 실제 fill·익절로 승격하지 않는다.

### 12.2 경로 metric 계약

고정된 단일 10분 end return 대신 기존 `1/3/5/10/20/30/60분` 경로에서 먼저 `30/60/180/300초` 진입품질 checkpoint를 생성한다. primary short window는 최초 구현 시 180초로 두되, 30/60/180/300초 결과를 모두 보존하여 180초를 맞추기 위한 사후 선택을 금지한다.

- `net_target_pct = conservative_execution_cost_pct + 0.10%`로 각 trace의 gross target을 계산한다. 비용을 다시 빼거나 고정 +0.3%가 항상 net +0.1%라고 가정하지 않는다.
- `time_to_net_target_sec`: entry anchor 뒤 net target을 처음 만족한 executable bid/동일 route 시각. bar high만 있으면 `counterfactual_touch`로 분리한다.
- `pre_target_mae_pct`: net target 전 low 기준 최대 역행폭. initial spread 영향과 방향성 하락 추정을 기존 `probe_path_risk` 방식으로 별도 기록한다.
- `stop_proximity_ratio = abs(pre_target_mae_pct) / abs(exact_stop_distance_pct)`를 기록한다. `>=0.8`은 최초 near-stop 진단값이지만 최적값으로 고정하지 않고 `0.6/0.8/1.0`의 작은 사전 grid에서만 비교한다. exact stop이 없으면 ratio는 null이며 임의 stop을 만들지 않는다.
- `underwater_duration_sec`: entry reference 아래에 있었던 관측 구간 합계, `neutral_dwell_sec`: `max(2*tick_pct, 0.5*round_trip_cost_pct, 0.05%)` 안에 머문 구간 합계다. snapshot 간격이 불완전하면 단순 row 수로 시간을 만들지 않고 coverage gap으로 제외한다.
- `pre_target_underwater_ratio`, `pre_target_neutral_dwell_ratio`, `capital_time_to_net_target_krw_sec`를 함께 기록한다. final holding duration을 target 도달시간으로 대체하지 않는다.
- target/adverse가 같은 bar에서 모두 보이면 순서를 추정하지 않고 `same_bar_ambiguous`로 유지한다.

### 12.3 실제 체결 lane과 counterfactual lane

두 lane은 같은 feature snapshot과 날짜 split을 쓰되 분모와 authority를 합치지 않는다.

1. **Actual-entry lane**: `main_lifecycle_paired`의 exact `first_fill_at`, fill VWAP·수량, route/session, `final_exit_at`, 실제 비용·순손익을 AI `decision_trace_id`와 결속한다. 실제 fill 이후 price path로 위 진입품질 라벨을 계산한다. `COMPLETED + valid profit_rate/cost`만 경제성 분모이며 partial fill은 별도 cohort다.
2. **Decision-opportunity lane**: 기존 detailed paired replay의 동일 decision anchor·executable ask proxy로 BUY/WAIT/DROP 전체를 평가한다. 이는 false WAIT/DROP과 놓친 clean-fast opportunity를 찾는 경로이며 실제 주문·실현손익 주장이 아니다.
3. Actual lane은 `ENTER precision`과 실제 비용·회전 품질, counterfactual lane은 `clean-fast recall`과 과잉 차단을 담당한다. 두 값을 하나의 EV로 평균하지 않는다.

### 12.4 계층형 feature와 판정 순서

runtime action 계산 전에 알 수 있었던 값만 feature로 쓴다. future target hit·MAE·holding duration은 label 전용이다.

1. `common_safety`: source freshness, route/session, invalidation, stale/conflict와 broker hard safety. 이 계층은 학습으로 완화하지 않는다.
2. `group_prior`: 다음 사전 정의 key로 묶는다.
   - 가격/틱 비율 band
   - 당일 이전까지 계산한 유동성·거래대금·top-depth band
   - completed-bar realized volatility/ATR band
   - `structure_phase` (`continuation`, `recovery_continuation`, `pullback`, `rebound_attempt`, failure/distribution 계열 분리)
   - 최초 감시 age와 첫 감시 대비 가격상승률 band
   - KRX venue/session
3. `group_policy`: 공통 spread/fillability/depth 기준에 group별 작은 residual을 더한다. 절대 threshold 전체를 그룹마다 독립 학습하지 않는다.
4. `symbol_residual`: 한 종목에 terminal 진입품질 표본 15개 이상·독립 5거래일 이상이 있을 때만 `n/(n+20)` shrinkage로 group prior에서 제한된 보정을 허용한다. 현재는 qualifying symbol 0이므로 자동 OFF다.
5. `micro_confirmation`: 실제 source가 있는 경우에만 bid support/rebound와 depletion·BUY trade backing·refill 결합을 평가한다. micro 결손은 양성/음성으로 보간하지 않고 group policy까지만 사용한다.

최종 action은 `ENTER / RECHECK / BLOCK`이다. hard invalidation만 `BLOCK`을 직접 만든다. 기대 clean-fast 확률은 있으나 timing/confirmation이 덜 갖춰지면 `RECHECK`; 단순히 BUY 비율을 맞추기 위해 `ENTER`를 만들지 않는다.

### 12.5 학습 목적과 과도한 WAIT 방지

정확도 하나를 최적화하면 전부 WAIT하는 판정기가 다시 선택될 수 있으므로 다음을 별도 metric으로 유지한다.

- `enter_clean_fast_precision`: ENTER 중 `CLEAN_FAST_PROFIT` 비율
- `clean_fast_recall`: 전체 clean-fast opportunity 중 ENTER가 포착한 비율
- `dirty_profit_enter_rate`: ENTER 중 세 가지 늦은/회복성 익절 비율
- `adverse_enter_rate`와 tail loss
- 실제 비용 차감 EV·순이익/일
- 180초 내 비용 후 +0.10% 달성 빈도
- fill rate, partial/unfilled, 평균 capital time
- action 분포와 `RECHECK→후속 ENTER/BLOCK` 전환율

승격은 비용 차감 EV `>=+0.10%`를 유지하면서 incumbent 대비 `enter_clean_fast_precision`과 `clean_fast_recall` 중 하나가 개선되고 다른 하나가 사전 고정한 materiality margin 밖으로 악화되지 않아야 한다. `dirty_profit_enter_rate`, adverse/tail, capital time도 같은 방식으로 판정한다. 한 건 차이나 raw 비율 0을 절대 veto로 쓰지 않고, 거래일 cluster 단위 불확실성과 최소분모를 함께 보고 margin은 calibration 전에 고정한다. 최소 참여 floor는 분모 붕괴 탐지용이지 목표 BUY 비율이 아니다.

### 12.6 기존 코드에 넣는 최소 변경 순서

새 독립 분석기나 cron을 만들지 않는다.

1. `ai_decision_quality.py`: 기존 horizon loop에서 dynamic net target hit, pre-target MAE, underwater/neutral dwell와 coverage를 계산하고 detailed comparison에 exact timestamps·metric을 투영한다.
2. `main_lifecycle_paired.py`: actual `first_fill_at→final_exit_at` lifecycle에 동일 경로 metric을 결속하고 actual/counterfactual authority를 명시한다. AI trace join 불가 행은 일반 종목·시각 근접 join으로 대체하지 않는다.
3. `entry_setup_evidence.py`: 가격/틱·사전 유동성/변동성·structure·watch age/extension의 pre-decision group key와 source hash를 evidence에 추가한다. 과거 결손값은 재구성 가능한 completed-bar 원천만 backfill하고 micro는 보간하지 않는다.
4. `ai_action_outcome_calibration.py`: 현재 common candidate를 incumbent로 두고 `group_prior/group_residual/micro_optional` challenger를 expanding-window walk-forward로 평가한다. 마지막 3일 한 번뿐 아니라 가능한 과거 fold를 순차 검증하되 미래 자료를 이전 fold에 사용하지 않는다.
5. `entry_setup_live_policy.py`: hash-bound candidate가 모든 gate를 통과한 뒤에만 기존 dated PREOPEN loader가 읽을 수 있는 family projection을 추가한다. 빈/거절 candidate의 baseline 대체는 금지한다.
6. `verify_threshold_cycle_postclose_chain.py`: actual/counterfactual 분모, label 보존식, group/symbol shrinkage, fold 날짜, source hash, optimizer handoff 및 offline authority를 검증한다.

### 12.7 테스트·승격·롤백 수용조건

- 단위 반례: 빠른 무역행 익절은 `CLEAN_FAST_PROFIT`, 늦은 익절·near-stop 후 반등·긴 횡보 뒤 익절은 각각 timing-failure class여야 한다.
- 동일 bar ambiguity, 불완전 cadence, missing cost/stop/fill, route/session mismatch는 0이나 성공으로 채워지지 않아야 한다.
- 같은 입력을 actual/counterfactual로 중복 집계하거나 최종 익절만 보고 clean-fast로 바꾸면 테스트가 실패해야 한다.
- symbol residual은 floor 미달 시 정확히 group prior와 같아야 하고, micro 결손 시 micro arm이 아니라 명시적 fallback이어야 한다.
- calibration 선택 후 sealed fold를 보고 threshold/group을 다시 고르면 verifier가 실패해야 한다.
- 승격 candidate는 `runtime_effect=false`, `allowed_runtime_apply=false`로 발행되고 review finding 0 뒤 기존 PREOPEN 계약만 소비한다. 배포·PREOPEN 선택·PID 소비·실제 자연 성과는 각각 별도 receipt다.
- post-apply source coverage·schema·hash·route 계약이 깨지면 신규 선택을 즉시 중단한다. 경제성 rollback은 catastrophic hard-safety 사건이 아니면 사전 고정한 canary terminal 분모와 독립 거래일 floor가 충족된 뒤 dirty-profit/adverse/capital-time이 materiality margin 밖으로 악화된 경우에만 수행한다. 단순히 이틀이 지났거나 한 건이 불리하다는 이유로 rollback하지 않으며, 진행 중 주문·custody와 hard safety는 변경하지 않는다.

### 12.8 현재 판정과 다음 실행 범위

현재 common candidate의 `policy_candidate=null`은 유지한다. 이번 설계는 익절을 무조건 양성으로 세던 문제와 종목 공통화 문제를 함께 해소하지만, 현재 micro READY 6개와 종목별 희소 표본으로 live 승격을 즉시 정당화하지 않는다. 최초 구현 pass는 **경로 metric·라벨·group key·offline walk-forward·verifier**까지이며 주문, threshold 수동 변경, live family 등록, PREOPEN env 작성과 bot 재기동은 포함하지 않는다. 최초 재생성 뒤 실제 `CLEAN_FAST / DIRTY_RECOVERY / SIDEWAYS / ADVERSE / CENSORED` 분모를 확인하고, 그 결과에 따라 group grid를 한 번만 축소·보완한다.

### 12.9 최초 구현·review/fix receipt

`2026-09-13 KST`에 §12.8의 첫 구현 범위를 기존 producer 안에서 완료했다. 새 Python 모듈·CLI·cron은 만들지 않았다. canonical 장후 산출물은 재발행하지 않았고, 선택 release·PREOPEN env·매매 PID도 변경하지 않았다.

- `ai_decision_quality.py`는 decision/fill anchor별 비용 후 `+0.10%` gross target, `30/60/180/300초` checkpoint, target/stop 최초 touch, target 전 MAE·near-stop, cadence가 완전한 underwater/neutral dwell, capital-time 진단과 여섯 상호배타 진입품질 라벨을 생성한다. 같은 bar touch, 비용·stop·cadence 결손과 180초 밖의 단순 stop touch는 성공/손실 라벨로 합성하지 않는다.
- `ai_decision_trace.py`와 `ai_engine_openai.py`는 판정 당시 conservative entry cost를 관찰 필드로 보존한다. action·submit guard는 바꾸지 않는다.
- `main_lifecycle_paired.py`는 실제 fill이 있는데 exact 후행 경로가 없으면 이를 `source_gap`으로 명시한다. holding duration을 target 도달시간으로 대체하지 않는다.
- `entry_setup_evidence.py`는 가격/틱·유동성·completed-bar 변동성·structure·watch age/extension·venue/session으로 hash-bound group observation을 계산한다. 리뷰 중 이 값을 live `entry_setup_evidence_v1`에 넣으면 Provider 입력이 바뀌는 권한 누출을 발견해, 최종 구현에서는 **offline detailed replay의 별도 메타데이터**로 분리했다. 따라서 기존 live 프롬프트 input/hash/action에는 이 group field가 들어가지 않는다.
- `ai_action_outcome_calibration.py`는 완전한 group dimension과 진입품질 라벨이 있는 행만 expanding-window fold에 사용한다. 미래 날짜 사용·sealed fold 재선정·결측 보간을 금지하고, 종목 residual은 15 terminal/5거래일 floor를 만족해도 reviewed candidate 전까지 OFF다. actual과 counterfactual 분모는 합치지 않는다.
- `verify_threshold_cycle_postclose_chain.py`는 라벨 보존식, group dimension 완전성, fold 날짜 순서, symbol residual OFF, actual/counterfactual 분리, optimizer handoff와 offline authority를 검증한다.

Review/fix에서 다음 네 결함을 수정했고 현재 범위의 잔여 P0~P2 finding은 0이다.

1. actual fill 기준 completed-bar touch를 actual 경제성 증거로 오인해 승격 check를 열 수 있던 경로를 차단했다. executable bid path와 realized cost가 모두 결속된 경우만 `economic_acceptance_eligible`로 센다.
2. `UNKNOWN` dimension을 가진 과거 종목군이 하나의 유효 group처럼 학습될 수 있던 경로를 제외했다. 결측은 group fallback 사실로 남기며 threshold를 학습하지 않는다.
3. group observation이 live AI evidence에 포함될 수 있던 입력 변경을 제거하고 offline replay metadata로 격리했다.
4. primary 180초 뒤의 단순 stop touch가 `CLEAN_FAST_LOSS_OR_ADVERSE`로 분류될 수 있던 경계를 censored/source-gap으로 수정했다.

최초 검증 결과는 관련 테스트 묶음 `840 passed`, live 입력/정책 consumer 회귀 묶음 `240 passed`로 총 `1080 passed`이고, Python compile·Black·Ruff(기존 파일의 E402/E722만 제외)·`git diff --check`를 통과했다. 당시 in-memory 결과의 `accepted_unique_trace=936`과 실제 fill36에도 새 진입품질 evaluable이0인 것을 신규 generation 대기라고만 종결한 것은 부적절했다. 원인은 과거 시장경로·실제 lifecycle을 새 라벨로 재투영하지 않은 것과 actual audit가 canonical `lifecycles` 배열 대신 `rows`만 읽은 구현 결함이었다.

후속 보완은 과거 자료를 버리지 않고 두 lane으로 복원한다.

- 시장경로 lane은 clean baseline 이후 hash-검증된 detailed replay의 기존 `kiwoom_completed_1m_with_pipeline_fallback` projection을 재사용한다. 21거래일·고유936 trace 중 비용 proxy 차감 후 MFE `>=+0.10%`이고 target-first인 anchor가169건/118종목이다. 전부 당시 incumbent가 `WAIT|DROP`한 비진입 사례이며, target 전 경로가 확인된 반등53건·직접 지속상승50건·세부경로 결손66건으로 분리했다. 날짜별 exact trace/target-first/반등/지속상승/결손과 first-hit 분모를 함께 발행하며 adverse-first는 음성, same-bar/neither는 censored로 유지한다.
- 실제 체결 lane은 lifecycle36건을 정상 인식한다. `FINAL_EXIT_RECONCILED`와 유효 entry notional/realized net PnL이 있는16건 중 비용 반영 순익률 `>=+0.10%`가11건이고, 180초 이내는 `003350`72초·`064550`50초·`001210`41초의3건, 나머지8건은 늦은 수익이다. 다만 기존 row의 lifecycle-window source-quality gate가 모두 false이므로 이 3건을 곧바로 clean-entry 정답이나 승격 경제성 분모로 사용하지 않는다. exact entry trace와 기존 시장경로 projection이 결합되는 fill은10건이며 나머지는 gap으로 보존한다.
- pipeline raw direct 검사는 9/11 하루가 아니라 위 21거래일 전체로 확장했다. 936 exact trace 대상 usable event260,667행을 same-route/fresh 조건으로 재구성했고, decision 뒤300초 raw window가 있는746건 중 target-first56·stop-first367·neither323, raw window 없음190건이었다. 현 라벨의 cadence·180초 경계를 충족한 판정 가능 경로는389건이다. 이 56건은 direct raw 기준점이고 위 169건은 공식1분봉+raw fallback의 시장경로 기준점이므로 서로 합산하지 않는다. 실제 fill 종목 별도 direct 검사에서는 exact holding bid로 `003350`65초와 `062970`76초 target touch를 확인했지만, route/cadence 결손은 그대로 남겨 realized PnL 또는 clean-entry 증명으로 확대하지 않는다.

현재 누적 학습은 9/11 한 날짜가 아니라 위 21거래일 전체를 사용한다. 날짜별 새 exact report가 추가되면 과거 raw archive를 매일 전수 재스캔하지 않고 검증된 일별 projection을 append하고, 기존 mechanistic common-feature search가 expanding-window/sealed-holdout으로 양성 target-first·음성 adverse-first·censored를 계속 소비한다. group prior는 완전한 group evidence가 생긴 뒤 같은 누적 source를 소비한다. 이 보완으로 “기준점0” 결론은 폐기됐지만 `policy_candidate=null`, live family 미등록, actual economic eligible0은 유지한다. 169개 counterfactual 기회와 11개 실제 순익 기준점은 판정기 개선 학습자료이고, executable actual path·비용·source-quality까지 충족한 승격 증거는 아니다.

후속 review/fix에서는 날짜별 분모·anchor 보존식, actual fill/realized/fast-late 보존식, counterfactual authority와 누적학습 계약을 strict verifier에 추가했다. 관련 producer/consumer 회귀는 `1224 passed`, Black·Ruff·Python compile·`git diff --check`와 문서 print-only parser가 통과했다. 별도 광범위 `test_sniper_scale_in.py` 전수 실행에는 이 학습 producer 변경과 분리해 원인 확인이 필요한 기존 runtime/order 경로 실패52건이 남아 있으므로 repository 전체 finding0 또는 배포 가능 상태로 확대하지 않는다.

## 13. 기계판정 주·AI 보조 전환 구현/review/fix receipt

이 절의 비구속 AI 역할은 사용자 확인 후 §16의 **기계 타점 선정 + AI PASS/VETO**로 정정했다. 당시 수치와 검토 기록은 보존하며 현행 권한으로 사용하지 않는다.

사용자 후속 지시에 따라 진입 역할을 `기계판정 주 / AI 비구속 보조 / 기존 runtime guard 최종 실행권한`으로 명시했다. 새 모듈·CLI·cron을 만들지 않고 기존 evidence, calibration, PREOPEN loader와 live adapter만 연결했다.

- `entry_setup_evidence.py`의 `mechanistic_entry_policy_decision`이 `ENTER_NOW / RECHECK / BLOCK`을 단일 계산한다. setup state·invalidation·risk-to-fact binding·micro counterweight와 spread/fillability/top3 ask-to-bid threshold를 같은 함수에서 판정한다. `compose_mechanistic_primary_decision`은 AI PASS/CAUTION/VETO와 schema 오류를 disagreement 관찰로만 보존하며 기계 action을 변경하지 않는다. AI는 hard/source block도 해제할 수 없다.
- `ai_action_outcome_calibration.py`는 과거의 별도 3조건 필터를 제거하고 위 주 판정 함수를 그대로 호출한다. 과거 evidence의 `no_supported_setup`, liquidity fragility, repeated promotion/late timing fact가 이미 선언된 risk code에 결속되지 않던 호환 결함을 고쳤으며 값을 합성하지 않았다. 21거래일·고유936 trace가 유지되고 충돌10·join 결손1은 제외된다.
- 비용 차감 +0.10%, positive paired delta, calibration/holdout 표본·날짜·terminal, source provenance와 catastrophic tail 조건을 모두 통과할 때만 hash-bound mechanistic candidate가 생긴다. `entry_setup_live_policy.py`는 다음 PREOPEN에 exact source-date calibration file/report/candidate/policy hash를 재검증하고 activation에 결속한다. 그 activation이 있을 때만 `GPTSniperEngine`이 기계를 주 owner로 사용한다. 후보 없음은 incumbent 유지, 후보가 있다고 주장하면서 계약이 깨지면 fail closed다.
- 기계의 `ENTER_NOW`도 즉시 full BUY가 아니라 기존 bounded WAIT/probe handoff로 들어간다. `RECHECK`는 비노출이고 `BLOCK`은 AI가 뒤집지 못한다. account/order/quantity/cooldown, fresh submit, broker와 hard/protect/emergency guard는 그대로 최종 실행권한을 가진다.

동일 누적자료 재평가 결과 nominal grid80개가 실제 서로 다른 selection21개로 분리됐다. +0.10% calibration passer는0개였다. best diagnostic threshold는 spread `<40bp`, fillability `>30`, top3 ask/bid `<3`이었지만 calibration exposure11의 terminal proxy EV는 `-0.466968%`, 마지막3거래일 holdout exposure1의 EV는 `-0.92964%`였다. calibration/holdout paired delta도 음수이고 holdout 표본도 미달이다. 따라서 현재 `policy_candidate=null`은 과도한 조건 때문이 아니라 경제성 방향 자체와 독립 holdout이 함께 실패한 결과다. 169개 target-first 기회를 이유로 불리한 adverse-first를 삭제하거나 +0.10% floor를 낮추지 않았다.

코드리뷰에서 별도 필터와 실제 판정 함수의 경계 불일치, 과거 risk fact 빈 binding으로 인한 producer 예외, AI advisory 오류 제거 시 setup schema 오류까지 지울 수 있던 authority 결함, threshold가 위험 보상에만 쓰이고 일반 READY entry에는 적용되지 않아 nominal grid80개가 selection1개로 붕괴하던 결함을 발견해 수정했다. 현재 관련 범위 테스트와 정적 검증 결과는 아래 최종 실행 receipt를 따른다. 이 코드는 workspace 구현이며 선택 release 배포·canonical 장후 재생성·PREOPEN activation·현재 PID 소비를 뜻하지 않는다.

최종 review/fix에서 one-share exploration의 durable marker만 남은 경우에도 잔여 주문과 추가매수를 차단하도록 owner 판정을 통합했고, broker 제출 직전에 수량이 정확히 1주인지와 일일 durable cap을 함께 재검증하도록 보완했다. 기계판정 producer·PREOPEN projection·live adapter·verifier와 직접 탐색 반례를 합친 회귀는 `1231 passed`, Python compile·Black·Ruff(기존 E402/E722 제외)·`git diff --check`와 문서 print-only parser를 통과했다. 광범위 `test_sniper_scale_in.py`는 `1014 passed / 45 failed`이며, 남은 45건은 이번 기계판정 직접 반례가 아니라 기존 AI retry·주문 route·holding/exit·soft-stop 경로다. 따라서 기계판정 구현 범위의 finding은 닫혔지만 repository 전체 finding0이나 배포 가능 상태로 확대하지 않는다.

## 14. 다중 시간축 흐름군 복원과 기계 RECHECK 기준점 구현

공통 liquidity 3개 값만으로 `ENTER`를 찾던 이전 결론을 최종 기준으로 사용하지 않는다. canonical detailed replay의 모든 request에는 판정시점의 `exact_payload_analysis.completed_structure`가 있었고, 여기에는 `1/3/5/10/20/60분` 수익률·기울기, phase/regime/alignment, 고점·저점 경과 bar, 20분 drawdown/rebound, volume/tape/program/liquidity가 포함돼 있었다. 그러나 기존 `_mechanistic_source_rows`는 spread·fillability·top3 ask/bid만 남기고 이 시계열 구조를 버렸다. 이는 “기준점이 없다”가 아니라 **학습 입력 투영이 지나치게 축약된 결함**이었다.

`entry_setup_evidence.py`에 공용 `mechanistic_entry_flow_observation_v1`을 추가하고, `ai_action_outcome_calibration.py`가 기존 exact-analysis self-hash와 request hash를 모두 검증한 뒤 이 투영을 누적 소비하도록 보완했다. 새 모듈·CLI·cron은 만들지 않았다. 미래 outcome·target hit·MFE/MAE는 flow feature에 들어가지 않으며 label 계산에서만 사용한다. 현재 936개 고유 trace 전부에서 flow observation이 유효했고, terminal 844개·censored 92개로 분리됐다.

### 14.1 고정한 흐름군과 후향적 분리력

조합 폭증을 막기 위해 의미가 설명되는 단일 6개와 상호작용 2개만 고정했다. 이는 live BUY threshold가 아니라 이후 micro 확인을 받을 `RECHECK` 모집단 정의다.

- `DEPTH_SUPPORTED`: top3 ask/bid `<=0.5`
- `HIGH_VELOCITY_CONTINUATION`: 5분 수익률 `>=5%`이면서 5분 기울기 양수
- `MID_HORIZON_STAIRCASE`: 10분 수익률 `1~2%`이면서 10분 기울기 양수
- `REBOUND_DECELERATION`: 20분 기울기 `-0.5~-0.1%/bar`
- `VOLUME_EXPANSION`: volume ratio `1.5~2.0`
- `RECENT_SESSION_HIGH`: session high 이후 경과 bar 0
- `DEPTH_SUPPORTED_STAIRCASE`: depth support와 mid-horizon staircase의 교집합
- `STAIRCASE_RECENT_HIGH`: mid-horizon staircase와 recent high의 교집합

양성은 비용 차감 MFE `>=+0.10%`이면서 target-first, adverse-first는 음성, same-bar/neither와 비용 결손은 censored다. 8/6~9/4의 769 terminal 기준 양성률은 `20.29%`, 9/9~9/11의 75 terminal은 `17.33%`다. 다음은 두 구간에서 모두 base 대비 lift가 유지된 흐름이다.

| 흐름군 | 8/6~9/4 양성/terminal·lift | 9/9~9/11 양성/terminal·lift | 현재 판정 |
| --- | --- | --- | --- |
| DEPTH_SUPPORTED | 41/131, 31.30%·1.54x | 4/17, 23.53%·1.36x | 후향 지원 |
| MID_HORIZON_STAIRCASE | 37/153, 24.18%·1.19x | 6/16, 37.50%·2.16x | 후향 지원 |
| RECENT_SESSION_HIGH | 34/134, 25.37%·1.25x | 5/20, 25.00%·1.44x | 후향 지원 |
| STAIRCASE_RECENT_HIGH | 10/34, 29.41%·1.45x | 3/6, 50.00%·2.88x | 후향 지원 |
| VOLUME_EXPANSION | 20/77, 25.97%·1.28x | 2/5, 40.00%·2.31x | 후향 지원 |
| DEPTH_SUPPORTED_STAIRCASE | 8/15, 53.33%·2.63x | 3/6, 50.00%·2.88x | 강한 기준점이나 calibration 20건 floor 미달 |

`REBOUND_DECELERATION`은 calibration 13/35·1.83x였지만 최근 구간이 1/4라 5건 floor 미달이고, `HIGH_VELOCITY_CONTINUATION`도 4/13 뒤 최근 0/1이라 탈락했다. 좋은 모양만 골라 분모를 낮추지 않았다. 가장 강한 `DEPTH_SUPPORTED_STAIRCASE`도 50%대라는 이유로 표본 floor를 완화하지 않는다.

통과한 5개 흐름군의 양성은 calibration에서 각각 9~15개 독립 거래일, 최근 구간에서 2~3개 거래일에 분산돼 특정 하루의 급등 표본만으로 만들어진 결과가 아니다. 이 분산 조건을 `minimum_calibration_positive_source_date_count=3`, `minimum_holdout_positive_source_date_count=2`로 명시해 행 수와 lift가 높아도 양성이 하루에 몰리면 통과하지 못하게 했다.

### 14.2 후향 기준과 전향 승격을 분리한 review fix

최초 구현은 최근 3일을 sealed holdout이라고 표현했다. 하지만 이번 설계 과정에서 전체 자료를 보며 흐름 경계를 정했으므로 그 3일은 진정한 미관측 자료가 아니다. 코드리뷰에서 이를 과대판정으로 잡아 `retrospective_validation`으로 고쳤다. 경계는 source date `2026-09-11`에 고정하며, 그 이후 최소 3개 독립 거래일에서 같은 count/date/positive/lift 조건을 통과해야만 `forward_accepted_recheck_families`와 hash-bound `recheck_candidate`가 생긴다. 현재는 `research_candidate`만 있고 `recheck_candidate=null`, `enter_policy_candidate=null`이다.

흐름군의 고정 +0.3/-0.7 terminal proxy EV는 최근 구간에서도 `-0.517452~-0.803471%`이고, 가장 강한 depth+staircase도 `-0.555362%`다. 이는 흐름군이 **놓친 상승·반등 후보를 줄이는 1단계 분류기**로는 유용하지만 직접 ENTER로 쓰면 안 된다는 근거다. 비용 후 `+0.10%` ENTER 기준은 낮추지 않았다.

### 14.3 매도잔량 속도와 지속 장후 고도화 경로

최종 순서는 `FLOW_FAMILY → RECHECK(비노출) → MICRO_CONFIRMATION → ENTER`로 고정한다. 새 거래일의 동일 trace에서 bid 지지·반등, 매도잔량 감소속도, 같은 가격 실제 BUY 체결 설명, refill을 결속하고 `baseline / bid·rebound / depletion·trade backing·refill / combined` 4군을 같은 lifecycle·비용·exit 계약으로 비교한다. 매도잔량 감소만으로 ENTER하지 않고, cross-epoch·late·UNKNOWN·누락 level을 보간하지 않는다. flow family별 actual fill·partial/unfilled·terminal 비용과 `+0.10%` EV가 완성되기 전에는 direct ENTER candidate가 없다.

기존 `micro_reversion_ai_quality_bridge`를 새 수집기 없이 직접 소비하도록 source audit도 연결했다. 일회성 과거 감사에서 row-level ask-depletion sidecar와 flow trace 교집합 후보는 8건이었지만, 현재 validator로 parent report 전체를 재검증하면 19개 report 모두 계약을 통과하지 못해 eligible same-trace join은 0건이었다. 오류는 `micro_context_route_provenance_invalid` 8개 report, bridge contract invalid 6개, row binding invalid 5개다. 8건은 diagnostic 근거로 보존하되 threshold 학습·4군 EV·ENTER 근거에는 소급 투입하지 않는다. 자동 source audit은 동결일 `2026-09-11` 이후 자연 generation만 읽고, parent report와 row가 함께 유효해진 교집합부터 누적한다. 이로써 과거 전체 bridge를 장후마다 재검증하는 비용과 경계 설계에 사용한 자료의 backfill 누수를 막는다.

일별 갱신은 기존 `ai_decision_action_outcome_calibration` 장후 producer와 optimizer handoff를 재사용한다. 배포된 뒤 새 exact report를 읽어 같은 경계를 전향 평가하도록 구현됐으며 raw archive를 새 producer로 재스캔하지 않는다. central verifier는 source 보존식, 후향/전향 구분, candidate hash, RECHECK ceiling, micro 미보간, direct ENTER 금지를 검사한다. 작업폴더 in-memory report는 verifier PASS였지만 canonical report 재생성·선택 release 배포·PREOPEN/runtime 연결·PID 소비는 수행하지 않았다.

이 범위의 targeted 테스트는 `entry_setup_evidence + ai_action_outcome_calibration + postclose verifier` **342 passed**다. 직접 소비자 전체 회귀는 **1236 passed**다. 실제 9/11 in-memory report도 `accepted trace=936`, flow valid=936, terminal=844, censored=92, contract error 0으로 통과했다. 광범위 `test_sniper_scale_in.py`는 이전과 같은 `1014 passed / 45 failed`이며 실패는 이번 flow projection/study가 아닌 기존 주문 route·holding/exit·soft-stop 경로다. Python compile·Black·Ruff·`git diff --check`와 문서 print-only parser를 최종 검증한다. canonical 재생성·배포 전환·기동은 수행하지 않는다.

## 15. 초기 기계·AI 정책 발행과 지속 갱신 — 9/13 추가 사용자 지시

이 절의 20:45 초기 bundle과 비구속 AI 설명은 최초 발행 이력이다. 현행 역할·정책 교체는 §16을 따른다.

사용자는 기계가 먼저 타점을 잡고 AI가 보조하는 구조로, **오늘 두 초기 정책을 발행하고 그 정책을 유지하며 누적 최적화**하도록 명시했다. 따라서 §13~§14의 성과 승격 후보 부재를 초기 정책 부재로 연결하던 운영 방식은 이 절로 대체한다. 과거 연구 결과·후향/전향 구분은 지우지 않는다. 15건을 성과 PASS로 바꾸거나 기준을 낮춘 것이 아니라, **사용자 지정 초기 채택과 성과 검증 후 교체**를 분리한 변경이다.

### 15.1 오늘 생성한 정책

- 발행물: `data/runtime/mechanistic_entry_policy/policy_2026-09-14.json`. 기계정책과 AI정책을 한 bundle로 결속했다. 9/13 20:45:56 KST 발행, source 9/11, effective 9/14, KRX regular의 main SCALPING만 대상이다. NXT·위젯·에피소드·보유 청산에는 적용하지 않는다.
- bundle SHA256: `ccf51d5e3a02b86e8ee9f4e9f31086f70ff1ecb862cd3626b352f6e7b78d33d7`.
- 기계: 기존 `mechanistic_entry_thresholds_initial_v1` 그대로다. 구조·현재 trigger·위험 상쇄·유동성을 동일 `mechanistic_entry_policy_decision`으로 판정한다. spread `<100bp`, fillability `>15`, top3 ask/bid `<5`는 기존 기계 경계이며 새로 완화하지 않았다. 실제 quote/cost/주문 guard는 별도로 더 엄격할 수 있다. 유효 micro의 10-tick 순매수·가격 반응을 위험 상쇄에 쓰며, 새 ask-depletion 자료가 없다는 이유만으로 초기 발행을 막지 않는다.
- AI: `decision_quality_v2_15_2_balanced_bounded_recovery` + `machine_first_auxiliary_v1`. 현재 기계 action·reason·flow observation과 누적 연구 context를 받는다. JSON risk schema는 유지하고 AI 설명은 기계 타점을 승격하거나 veto하지 않는다. 실제 system prompt 전체와 hash를 저장한다. base version만으로 같은 프롬프트라고 판정하지 않는다.
- 누적 근거: 21거래일, exact trace936·terminal844·censored92. 별도 검증 출력 `tmp/machine-initial-policy-20260913/calibration_2026-09-11.json`에서 source content SHA `e6889213f425a60f18fe871d0c43861d156ff0d45f778d4546a32e9b22e2b13d`를 확인했다. bundle의 `sources/`에 immutable copy를 보존하므로 canonical 재생성으로 발행 근거가 사라지지 않는다. 기존 canonical 장후 체인은 재실행/덮어쓰지 않았다.

### 15.2 실행·갱신 경로

`기존 감시 평가 호출 → source preflight → 현재 snapshot 기계판정 → ENTER_NOW인 타점만 AI 보조 → 기존 final authority·quote·주문 guard`다. RECHECK/BLOCK은 provider cache·lock·min-interval 앞에서 반환한다. ENTER_NOW에는 같은 frozen 입력/기계 근거를 AI에 전달하고 기계 결과를 AI 캐시에 저장하거나 재사용하지 않는다. 재확인과 차단 시 정상 비노출 상태를 보존한다. 현재 감시 scheduler 자체를 모든 WS tick 판정으로 바꾸거나 AI의 provider budget/timeout·수량·cap을 변경한 작업은 아니다. 선택된 타점의 AI 응답 대기와 최종 quote 재검증은 남아 있으므로 실행 지연 감소의 실측은 별도다.

정책 owner는 역할상 `src/engine/scalping/mechanistic_entry_runtime_policy.py`다. engine root에 새 모듈을 만들거나 별도 market-data producer·cron·학습기를 추가하지 않았다. 기존 `ai_action_outcome_calibration --write`가 bootstrap 이후 publisher를 호출한다. 누적 검증을 통과한 기계 challenger는 기존 projection validator로 threshold를 교체하고, 없으면 incumbent를 유지한다. 누적 원천/flow 연구 context는 AI bundle에 갱신되며, 검증된 AI 최적화 candidate가 기존 PREOPEN activation을 통과하면 그 base prompt를 우선 소비하고 보조 역할을 유지한다. 데이터 context 갱신 자체를 AI 판단 성능 향상으로 보고하지 않는다.

늦은 replay follower의 새 source도 다음날07:35 전에는 반영할 수 있다. 각 generation/source는 보존하고 날짜별 pointer만 원자 갱신한다. PREOPEN 경계 이후에는 당일 정책을 조용히 바꾸지 않는다. 새 날짜 산출물이 빠지면 마지막 유효 정책을 유지하되 원 effective date·`machine_policy_update_missing=true`를 기록한다. 손상된 당일 정책을 정상 carry로 숨기지 않는다. 기존 operator 비활성화·유효 승인·당일 runtime env·owner·source/주문 safety는 계속 적용된다.

### 15.3 리뷰·검증과 실제 적용 상태

`korstockscan-review-gate`로 직접 producer·consumer와 권한을 검토하며 다음을 보완했다: 초기 정책이 이후 AI 승격을 가리는 문제, 기계 결과 캐시 재사용/다른 mode로의 누출, 새 scope-authority 이름이 downstream에서 거절되는 문제, 늦은 장후 결과를 최초 발행이 영구 차단하는 문제, 반복 snapshot hashing의 I/O 비용.

실제9/14 env를 launcher 순서로 **읽기 전용 해석**한 첫 검사에서는 `fallback_operator_rollout_invalid`였다. 이전9/11 V2.14 rollout의 수량/잔량/scale-in 계약은 과거값이고, 새9/14 auto-promotion pin은 유효했다. 동일 scope에 유효한 새 승인이 있을 때만 그 승인을 우선하도록 수리했다. 새 승인까지 불량이면 기존 fail-closed를 유지한다. 재검사: env parse errors0, `enabled=true`, `active_bounded_krx_canary`, 기계 primary, AI auxiliary, 위 bundle hash 일치. 이는 미래 날짜 consumer preview이지 PREOPEN 실행/PID receipt가 아니다.

직접 영향 회귀 **443 passed**: 초기 후보0/15건에서도 정책 발행, 성과 gate 유지, 누락 시 carry, 원 날짜 보존, source/hash 손상 거절, 늦은 갱신과 PREOPEN 동결, 기계→AI 호출 순서, 기존 승인·recheck·lifecycle 계약을 검증했다. 코드 검토와 초기 발행은 실수익 검증과 구분한다. 초기 정책은 `initial_policy_not_performance_promotion`; 비용 후 +0.10% EV나 빈번한 순익이 입증됐다는 뜻이 아니다. 기존 best-observed 연구의 음수 고정 exit proxy도 실제 운영 손절/수익과 혼합하지 않는다.

현재 선택 release는 여전히 `entry-split-ai-policy-20260914` / `b1891f9cd0c6acd4f086c64c030493bebe28da60`이다. 작업폴더 새 consumer·초기 발행물 존재와 선택 release 배포는 별개이며, 이 절은 배포/기동 receipt가 아니다. 다음 적용 확인은9/14 체크리스트 기존 owner에 연결한다.9/13 체크리스트는 현재 존재하지 않아 과거 체크리스트로 대체하지 않았다. 선택 코드에 이번 검증 변경이 포함되는지, PREOPEN 실제 소비·main PID·첫 기계/AI 판정·체결 이후 비용과 조기 익절/횡보/불리한 excursion은 아직 미확인이다.

최종 확장 회귀는 초기 publisher·live policy·AI transport·누적 calibration·기계 evidence·rollout·recheck·lifecycle·기존 prompt optimizer·decision trace·paired batch **564 passed**다. Python compile, 해당 파일 Black, 새 publisher/직접 policy/tests Ruff, `git diff --check`, 문서 print-only parser도 확인한다. `ai_engine_openai.py` 전체 Ruff의 기존 E402/E722 27건은 이번 범위에서 일괄 재작성하지 않았으며 lint 전역0으로 보고하지 않는다. Provider 재호출·실주문·매매 기동·canonical 전체 장후 재생성·외부 sync는 수행하지 않았다.

## 16. 기계 타점 선정·AI PASS/VETO 역할 정정

9/13 사용자의 역할 확인과 재구현 지시에 따라 비구속 AI를 철회했다. 이번 변경은 기계 threshold·수량·손절·목표·cap을 낮추는 변경이 아니다.

| 기계 판정 | AI 결과 | 결합 결과 |
| --- | --- | --- |
| ENTER_NOW | 유효 PASS | 기존 최종 authority·quote·주문 검증으로 전달 |
| ENTER_NOW | 현재 fact에 결속된 유효 VETO | 해당 타점 DROP, probe 의도 없음; 영구 종목 금지 아님 |
| ENTER_NOW | CAUTION·INSUFFICIENT·누락·계약 오류 | 무진입 WAIT, probe 의도 없음; 기존 후속 관찰/호출 제한 유지 |
| RECHECK/BLOCK | 미호출 또는 어떤 AI 결과 | 기계의 무진입 상태 유지; AI PASS로 승격 불가 |

`compose_mechanistic_primary_decision` v2가 역할을 소유하며 `ai_role=auxiliary_risk_screen_pass_veto_no_promotion`, `ai_can_veto_entry=true`다. legacy AI-only validator는 그대로 두고 machine screen에서만 fact-bound `LIQUIDITY_FRAGILE / ADVERSE_TAPE / REWARD_RISK_WEAK`와 긍정 근거를 함께 인용한 VETO를 수용한다. 기계가 이미 차단한 hard risk만 AI VETO로 허용하는 형식적 심사를 피한다. 선택 입력 결측·확인 결손 하나로 VETO하지 않으며 유효한 반대 근거도 자동 무시하지 않는다. 잘못된 VETO는 PASS가 아니라 오류/재확인으로 분리한다.

AI prompt variant는 `machine_first_pass_veto_v2`다. 실제 English ASCII prompt, role, threshold, source hash를 bundle로 결속한다. invalid-prompt retry에서도 role metadata를 우선 보존하고 동일 PASS/VETO addendum을 유지한다. 현재 threshold와 별개인 AI confidence를 새 진입 점수 gate로 만들지 않는다. 실전 adapter의 호환 `WAIT + entry_probe_intent` 표시는 PASS에만 가능하며 최종 실행 guard를 통과했다는 뜻이 아니다.

최종 리뷰에서 두 결함을 추가 수리했다. (1) 기계 RECHECK가 과거 comparative composer의 probe 의도를 남기던 경로를 제거했다. (2) 이전 변경분이 복원했던 1주 고정·exploration identity만으로 잔량/추가매수를 막는 로직을 원래 HEAD의 중앙 sizing/lifecycle owner로 되돌렸다. 기존 position의 실제 terminal 금지 flag·일일 cap·주문 guard는 보존한다.

### 16.1 장후·정책 연결 및 검증 범위

기존 calibration candidate→activation validator→central verifier를 같은 AI role로 맞췄다. 기존 누적 기계 threshold 검증과 AI base prompt 자동 선택을 유지하며, 후보 부재는 초기 정책 부재로 바꾸지 않는다. PASS/VETO별 기계 action·bundle·raw risk/fact·최종 action을 decision trace와 pending outcome에 함께 보존한다. final-response digest 및 기존 offline control consumer 검증으로 VETO 무진입이 성공 진입으로 바뀌지 않는지 확인한다. 이후 자연 label/replay로 빠른 순익·횡보·깊은 adverse와 VETO 뒤 놓친 기회를 대사해야 한다. 누락 경제성은 null이며 이번 회귀 테스트를 실제 AI 편향 해소/수익 개선으로 보고하지 않는다.

기존 초기 role의 교체는 명시적 `--replace-initial-role`로만 허용한다. 최초 미활성 seed·원 bundle/source hash·다음날07:35 전 조건을 검증하고 이전 generation을 보존한다. 일별 자동 publisher는 권한이 다른 구 bundle을 조용히 승계하지 않는다. 자동 정책 소비에는 기존 exact-date owner/승인·PREOPEN 계약이 필요하고, 별도 widget/episode 배포는 이 변경 대상이 아니다.

광범위 sniper suite의 기준 HEAD `b1891f9c`를 별도 `/tmp/korstockscan-review-baseline-20260913`에서 실제 실행한 결과 **1006 passed / 53 failed**였다. 과거 route mock·holding/exit·exploration 구 계약 기대치의 실패를 새 AI 심사 결함으로 바꾸거나, 테스트 통과를 위해 현재 주문/수량 계약을 되돌리지 않는다. 최종 검증·정책 발행·배포 receipt는 아래 후속에 분리 기록한다.

### 16.2 최종 코드 검증·초기 정책 정정 receipt

- 최종 직접/인접 12 suite **1274 passed**. 이후 광범위 sniper suite는 **1006 passed / 53 failed**로 위 baseline과 실패 ID 전수가 같았다. 이 차이를 숨겨 전역 테스트 PASS로 보고하지 않는다. 이번 역할 교정·publisher·consumer 범위의 미해결 finding은 0이다.
- Python compile, scoped Ruff, Black, `git diff --check` 통과. 문서 print-only parser는30개 task이며 외부 sync는 실행하지 않았다. Provider 재호출·비용 큰 장후 전체 재생성·실주문은 하지 않았다.
- 기존 publisher에 `--source tmp/machine-initial-policy-20260913/calibration_2026-09-11.json --replace-initial-role`을 명시해9/14 초기 정책을 정정했다. 새 bundle SHA256 `b7d4581761fad24a8f680a4842fda407fc337d587bad6d03254c7cf1eb1e8d73`; 이전 `ccf51d5e…` generation과 source snapshot은 보존됐다. disposition은 `initial_role_corrected_not_performance_promotion`, 기계 threshold는 동일하다.
- 실제9/14 threshold→operator→dated env의 읽기 전용 resolver preview: parse errors0, `enabled=true`, `active_bounded_krx_canary`, V2.15.2, 기계 primary, AI PASS/VETO role, 새 bundle hash 일치. 이는 정책 로딩 사전 검증이지 실제 미래 PREOPEN/PID receipt가 아니다.
- 승인된 배포는 main/common routing 대상이다. 독립 widget/episode unit·custody·정책 pin은 변경하지 않는다.9/13 일요일 main PID와 장후 chain이 없으며9/13 exact-date env도 없어 주말 수동 기동이나9/14 env 복사로 우회하지 않는다.9/14 기존07:35 PREOPEN→07:55 예약 기동에서 실제 소비를 확인한다.

### 16.3 승인된 커밋·푸시·메인 배포

- 코드 commit `f12a9373ea6d9465b9144311f33e202f3c23c16b`를 origin/main에 push 완료했다. 이 작업의 누적30개 파일 변경을 포함하며 ignored runtime state·정책 원장을 Git에 일괄 포함하지 않았다.
- 선택 release: `/home/ubuntu/KORStockScan-runtime-releases/machine-ai-pass-veto-20260914`. 별도 detached worktree에 검토 commit을 고정하고 공유6개 경로를 연결했다. 선택 source `src/deploy/restart.sh` clean, 핵심 evidence/publisher 테스트 **105 passed**를 배포 root에서 다시 확인했다.
- main PID/장후 worker가 없는 상태에서 selector를 원자 전환했다. 원 selector SHA `037fc6de49afb7155789e428755b99ff5994985d683bcdc2fa9ab0799e2af6eb`와 `tmp/machine-ai-pass-veto-deploy-20260913/previous-selection.json`, 이전 `entry-split-ai-policy-20260914`/`b1891f9c` release를 보존했다. 기계 초기 policy의 이전 generation도 그대로 있다.
- `--check-cron`9개 PASS, 다음 거래일 preopen/start/postclose `--print-plan`이 새 root/commit으로 일치했다. cron 시각·env는 변경하지 않았다. 독립 machine manifest SHA `caa1e8071daf226fe4c67e0e9654e84a4ae5a7b71c9e749bcde3b2c9f01ed893` 전후 동일하며 해당 unit/drop-in/PID는 변경하지 않았다.
- 배포 root의 실제 `entry_setup_live_policy.__file__`를 확인한9/14 읽기 전용 preview도 enabled/PASS-VETO role/새 bundle 일치다. **실제 주말 기동은 수행하지 않았다.** 당일 env 없는9/13 실행을9/14 env로 가장하지 않으며, 기존 다음 거래일07:35/07:55 예약을 그대로 둔다. PID 소비·자연 판정·비용 후 성과 미확인은9/14 기존 PREOPEN/Runtime owner에서 확인한다. 이후 문서 receipt commit과 선택된 코드 commit은 별개다.

사용자 선택 문서 외부 동기화(정책 적용/봇 기동의 선행 조건 아님):

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
