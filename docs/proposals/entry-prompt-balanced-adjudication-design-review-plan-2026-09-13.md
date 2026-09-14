# Entry V2.14/V2.15 판정 균형 설계점검·보완계획

작성: `2026-09-13 KST`. 범위: main SCALPING entry의 설계점검과 후속 구현계획. 최초 작성은 문서-only였다. 이후 사용자의 구현·review/fix 지시에 따른 코드·격리 replay 결과는 §9에 추가한다. 정책 발행·배포·기동 완료를 뜻하지 않는다.

최신 설계 변경: **9/14 사용자 요청에 따른 축약형 직접 전환·장후 변경 계획은 [§22](#22-보조심사-전용-축약형-직접-전환과-장후작업-변경계획)를 따른다.** 최초 전환에 기존 전체형 대조군·paired 우위·경제성 표본 대기를 요구하는 §21의 제안은 대체됐다. 과거 구현·배포 receipt는 그 당시 범위로 보존한다. §22는 계획이며 실행 receipt가 아니다.

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

## 17. 그룹·종목 보정·매도잔량 micro의 실전 연결 상세 구현안

작성: 2026-09-13. **계획 수립만 수행했으며 아래 기능의 구현·정책 발행·배포 receipt가 아니다.** §12/§14의 연구 전용 경계는 아래 구현 대상으로 연결하되, 현재 운영은 §16의 기계 primary·AI PASS/VETO 계약을 유지한다. 불필요한 신규 코드·중복 연구·Provider 호출을 최소화한다. 9/13 당일 체크리스트는 없으므로 실행 권한을 과거 날짜에서 추정하지 않는다. [9/14 체크리스트](../checklists/2026-09-14-stage2-todo-checklist.md)의 기존 장전/Runtime/CodeImprovement owner는 미래 확인 경로이지 이번 계획의 실행 receipt가 아니다.

### 17.1 확정할 구조와 현재 결손

목표는 **종목의 당시 흐름에서 빠른 타점을 기계가 찾고, AI가 반대 근거를 심사하며, 누적 장후 자료로 두 정책을 갱신하는 것**이다. 최종 익절만으로 좋은 진입을 정의하지 않는다. 비용 후 +0.10% 도달시간·그 전 역행·횡보와 실제 순익/참여/자본시간을 함께 평가한다.

| 필요한 기능 | 확인한 현재 구현 | 이번 후속의 완료 조건 |
| --- | --- | --- |
| 종목별 임계치 | `build_hierarchical_entry_quality_walk_forward`는 종목 표본과 shrinkage 계약을 보고하지만 실제 종목 보정값을 산출·적용하지 않음 | 종목별 effective threshold와 상속/독자 보정의 출처가 runtime·replay에서 같고, 적격 보정은 다음 정책에 자동 반영 |
| 유사 흐름 그룹의 타점 | hierarchical `policy_candidate=None`; flow study는 RECHECK 연구 후보이며 ENTER consumer 없음 | 검증된 그룹 규칙이 `ENTER_NOW` 후보를 발급하고 AI PASS/VETO→최종 guard로 연결 |
| 새 micro의 진입 반영 | 공통 고정 1초 kernel은 존재. `entry_adverse_flow.evaluate_snapshot`은 bid/trade veto이며 depletion/refill은 진단으로 명시 | 속도·실제 BUY 설명·refill과 반등/bid 지지를 함께 소비하는 별도 명시적 진입 variant 및 동일 계산 replay |

‘모든 종목에 서로 다른 **최적값**이 이미 있다’는 상태를 목표 receipt로 만들지 않는다. 모든 대상 종목에 유효 정책은 존재하게 하되, 자료가 부족한 종목은 그룹/공통 값을 상속한다. 독자 보정과 상속을 숨기지 않는 것이 필수다. 표본 부족은 미검증 자식 정책의 승격을 제한할 수 있지만 정책 resolver·publisher·consumer 자체를 미구현으로 남길 이유는 아니다.

### 17.2 수정 위치 — 새 판정 서비스·report producer 없이 연결

아래 기존 파일의 함수/계약을 확장한다. 구현 중 단순 import/호환 변경이 필요한 직접 consumer만 추가하며, 새 engine-root 모듈·DB·CLI·timer·병렬 장후 producer는 만들지 않는다. 기존 테스트 파일에 회귀 사례를 추가한다.

| 기존 owner | 최소 변경 |
| --- | --- |
| `src/engine/scalping/entry_setup_evidence.py` | 그룹 관측·공통 action core 재사용. 공통 hard 차단과 학습 가능한 trigger를 분리하고 하나의 계층 resolver/결정 함수로 live·replay 통일 |
| `src/trading/market/confirmation_window.py` | `build_confirmation_window` 계산은 우선 변경 없이 재사용. 새 BUY 판단을 이 순수 feature kernel에 넣지 않음 |
| `src/engine/ai_engine_openai.py` | 기존 감시 평가 지점에서 동일 frozen input으로 계층 판정. 선택 rule/threshold/micro receipt를 AI에 전달하고 AI 미호출 기계 판정도 기록 |
| `src/engine/scalping/ai_decision_trace.py` | 기존 trace/payload 저장 경로에 기계 평가 source 보존. Provider 미호출과 실제 AI 판정 분모는 계속 분리 |
| `src/engine/scalping/ai_decision_quality.py` | 기존 6종 경로 라벨·180초 primary·30/60/180/300초 진단 재사용. 필요한 경우 실제 executable 경로/기계 anchor adapter만 보완 |
| `src/engine/scalping/ai_action_outcome_calibration.py` | 기존 누적 source·walk-forward·flow/hierarchical/refinement 결과를 하나의 계층 candidate로 연결. 종목 보정 추정과 micro ablation 추가; 기존 연구를 통째로 다시 만들지 않음 |
| `src/engine/scalping/mechanistic_entry_runtime_policy.py` | 기존 bundle에 계층·micro·단일 gate contract 추가. 기존 원자 publish/immutable source/기존 정책 유지/freeze 재사용 |
| `src/engine/scalping/entry_setup_live_policy.py`, `src/engine/verify_threshold_cycle_postclose_chain.py` | 해당 bundle의 실제 선택·검증·후행 handoff를 확장. 연구 통과를 runtime 승인으로 자동 재라벨링하지 않음 |

`src/engine/scalping/micro_reversion/ai_quality_bridge.py`는 기존 원천 투영이 필요한 필드를 이미 전달하는지 먼저 확인한다. 전달 결손이 입증된 필드만 보완한다. 같은 이름의 `micro_reversion/confirmation_window.py`는 120/180초 **사후 라벨** 코드이므로 실전 1초 feature kernel로 잘못 사용하지 않는다. 기존 widget/episode adapter의 주문·custody나 adverse-flow veto 의미를 공용 수정으로 바꾸지 않는다. Kiwoom protocol/parser 변경이 실제 필요해질 때만 공식 reference gate를 수행한다.

### 17.3 단일 정책 계약과 판정 순서

기존 bundle의 후속 schema에 다음 정보를 넣는다. 필드명은 구현 시 기존 schema와 대사하되 별도 정책 원장을 새로 만들지 않는다.

- 공통: schema/feature/gate 버전, source/effective date, source hash, AI role/prompt hash, 허용 venue/session, 기존 authority와 expiry.
- 그룹: stable rule key, 사전 정의된 match 조건·우선순위·required features, 구조 trigger, threshold override, parent hash, 검증 evidence와 `inherited|initial_authorized|validated_challenger` 구분.
- 종목: symbol+venue/session+group 결속, 보정 가능한 parameter와 bounded delta, shrinkage weight, 학습 날짜·노출 수·holdout/hash. 종목명 자체를 예측 feature로 외우지 않음.
- micro: 사용하는 결합 variant, 필수 feature·단위·유효 창, 각 threshold, missing/negative 처리와 원천 도입일. threshold는 calibration에서 선택하거나 명시적으로 승인한 초기값이며 문서에서 최적값을 발명하지 않음.
- 판정 receipt: matched rule, selected level, effective threshold/hash, 상속 사유, 원천 as-of, micro completeness, machine action/reason, AI 결과, 최종 제출/미제출 사유.

실행 순서는 `유효 입력·기존 hard 차단 → 그룹 매칭 → 유효 종목 보정 → 구조+micro 타점 → AI PASS/VETO → 최종 freshness/authority/주문 guard`다.

1. 동일 입력의 계층 선택은 결정적이어야 한다. 후보 그룹이 겹치면 정책에 고정한 specificity→priority→stable key 순으로 하나를 고른다. 실시간 수익 추정에 따라 그때그때 다른 그룹을 고르지 않는다.
2. 공통 hard 차단은 어떤 자식도 덮지 못한다. 반면 **공통 `READY`를 먼저 요구한 뒤 그룹 ENTER를 허용하면 빠른 그룹 타점이 다시 막힌다.** 공통의 비위험 RECHECK와 hard invalidation을 reason별로 분리하고, 그룹은 전자에 대해 자기 trigger로 ENTER를 제안할 수 있게 한다.
3. 승인된 자식이 없거나 선택적 종목 보정이 표본 부족이면 부모 정책을 사용한다. 전체 bundle 무결성·권한 오류는 fail-closed다. 이미 선택된 규칙의 실제 불리한 증거나 필수 원천 오류를 숨기기 위해 덜 엄격한 부모로 재시도하지 않는다.
4. 그룹 ENTER는 broker BUY가 아니다. AI 유효 PASS만 후행에 전달하고 VETO는 DROP, CAUTION/INSUFFICIENT/오류는 WAIT다. 기계 RECHECK/BLOCK을 AI가 승격하지 못한다. 기존 수량·cap·cooldown·손절·청산·owner를 변경하지 않는다.
5. 기존 감시 평가 loop를 사용한다. 새 WS-tick scheduler를 만들지 않으며, 정책 계산시간과 감시 주기/AI 대기/최종 제출 지연을 각각 기록한다. ‘실시간 판정’이라는 이름만으로 첫 감시 이전 탐색 결손이나 AI 대기시간이 해결됐다고 보고하지 않는다.

### 17.4 그룹과 종목 보정 — 표본을 버리지 않고 과적합 제한

기존 가격/틱·유동성·변동성·structure phase·watch age·extension·venue/session 관측과 다중 시간축 흐름 feature를 재사용한다. 모든 차원의 Cartesian grid를 생성하지 않는다. 기존 continuation/recovery/pullback 흐름을 bounded 규칙 집합으로 먼저 평가하고, 희소 조합은 미리 선언한 부모 그룹으로 묶는다. 당일 미래 고저점·나중의 상승 종목 목록은 match 조건에 쓰지 않는다.

- calibration에서만 그룹 규칙·보정 후보를 고르고 날짜순 holdout을 한 번 평가한다. 동일 종목의 겹치는 경로/같은 움직임을 독립 15건으로 세지 않도록 기존 lifecycle/anchor identity와 시간 겹침을 대사한다.
- 종목 residual은 그룹 대비 허용된 소수 threshold만 보정한다. 기존 `n/(n+20)` 수축식을 출발점으로 사용하며 n은 중복 제거된 유효 노출 수다. `effective = clip(parent + n/(n+20) * fitted_delta, approved_bounds)`로 계산하고 fitted_delta는 calibration의 기존 bounded 후보 집합에서만 선택한다. 범위·단위와 parent 제약을 validator가 검증한다. 실제 임계치 fitting 없이 eligible symbol count만 출력하면 미완료다.
- 현재 연구의 종목 15건/5일 조건과 기계 refinement의 calibration 10노출/5종목/5일은 **서로 다른 평가 계약**이다. 이를 모든 그룹/종목/기존 정책 소비에 중첩 적용하지 않는다. 15건은 독자 최적화의 자동 증명이 아니며 부모 정책 사용을 막는 조건도 아니다.
- 초기 그룹이 아직 경제성 검증을 통과하지 못하면 기존 실행 가능한 공통 정책을 유지하면서 새 후보를 비교한다. 연구 전용 RECHECK를 이름만 ENTER로 바꾸지 않는다. 독립 그룹의 최초 live 의미 확장은 코드 검증과 명시적 초기 활성화 승인에 결속하고 이후 정상 장후 갱신은 기존 자동 계약으로 처리한다.

### 17.5 매도잔량 속도·체결 설명·refill 결합

한 시점 `t`의 판단에는 `t`까지 수신된 자료로 완결된 고정 1초 창만 사용한다. 시작 호가의 고정 ask 가격·최소 잔량·최소점 이전 같은 가격 BUY·그 뒤 cutoff까지 refill, bid 지지/반등을 같은 route/epoch/sequence로 묶는다. 120행 버퍼 존재는 1초 completeness 증명이 아니다.

1. 원시 qty/sec와 함께 초기 잔량 대비 감소율·해당 그룹/종목의 **과거** 평시 수준 대비 값을 보존한다. 절대 잔량 하나로 대형주와 얇은 종목의 임계치를 공통화하지 않는다. 정상화 기준도 정책 source에 고정한다.
2. 결합 규칙은 `구조 trigger + bid/가격 반응 + 감소속도 + 실제 BUY 설명 + refill 제약`이다. 취소 추정 감소가 대부분이거나 refill로 소진이 상쇄되는 경우를 긍정 근거로 세지 않는다. 각 feature는 독립 threshold와 단위가 있고 매도잔량 감소 하나만으로 ENTER하지 않는다.
3. `valid_supportive`, `valid_adverse`, `unavailable`을 분리한다. 아직 micro가 없는 과거 표본은 구조 정책 lane에 남기고 0값으로 메우지 않는다. 새 micro가 필수인 선택 규칙은 incomplete/UNKNOWN/cross-epoch에서 RECHECK하며 adverse를 missing으로 바꾸지 않는다. micro 비의존 부모 정책을 쓰는 경우에는 그 선택과 비사용 사유를 명시한다.
4. 기존 adverse-flow adapter는 일부 fixed-ask gap을 진단상 제외한다. 그 완화된 결과를 새 depletion BUY 근거로 전용하지 않고, 새 결합에는 공통 kernel의 **전체 필수 feature validity**를 검증한다. kernel 계약 변경이 필요하지 않으면 그대로 둔다.
5. 장후에는 baseline / bid·rebound / depletion·trade backing·refill / combined의 동일 표본·비용·exit 교집합을 비교한다. 신규 원천 도입 전 날짜를 combined 학습 표본으로 합성하지 않는다. micro 변수를 매일 무제한 추가하지 않고 기존 bounded 후보 집합으로 증분효과를 확인한다.

### 17.6 누적 데이터·라벨·승격 조건

9/11만 재사용하는 일회성 비교가 아니라 clean baseline 이후 이용 가능한 적격 날짜를 기존 누적 source loader로 읽는다. 실제 체결, 미체결 기회, AI VETO, 기계 RECHECK/BLOCK의 분모·원천 품질은 분리한다. AI 미호출 branch에도 frozen 기계 입력과 anchor/hash를 기존 저장 경로로 남겨 향후 학습 누락을 닫는다. 과거 저장되지 않은 입력을 현재 값으로 복원하지 않으며 Provider 미호출을 AI WAIT 정답으로 세지 않는다.

- 진입품질 정답은 §12의 6종 라벨과 primary 180초를 재사용한다. 오래 횡보하거나 near-stop 뒤 익절은 실현 이익으로 보존하되 clean-fast 양성으로 학습하지 않는다. 30/60/300초는 진단이며 전 구간 동시 통과를 새 gate로 붙이지 않는다.
- **비용 후 +0.10%에 닿은 사례와 평균 비용 후 EV ≥0.10%는 다르다.** 전자는 경로 라벨, 후자는 손실·미체결·비용을 포함한 선언된 평가 lane의 정책 승격 지표다. MFE/고가 touch·terminal proxy·실현 EV를 바꿔 쓰지 않는다. executable 증거가 부족하면 해당 lane의 한계를 남긴다.
- 실제 사용자 손절/청산 override는 별도 cohort로 보존한다. 그 결과의 손실을 삭제하지 않고, 진입 타점 비교에는 사전에 고정한 동일 exit/cost의 counterfactual lane을 함께 본다. 실제 lane과 CF lane의 EV를 합산하지 않는다.
- gate 수치는 한 source of truth로 정리한다. 현재 threshold-policy 요약의 3종목/2일과 producer의 5종목/5일 차이를 먼저 contract test로 고정하고, 단순히 작은 숫자에 맞춰 완화하지 않는다. 공통 refinement·그룹·종목·micro 각 후보가 통과할 계약을 명시하고 상호 무관한 gate를 누적하지 않는다.
- 후보 순위는 동일 비용 계약의 holdout EV·일별 순익/자본시간, clean-fast precision/recall·참여, adverse/tail을 함께 보고 결정한다. 순익/자본시간은 분모가 유효할 때만 계산한다. 무진입 정책이나 한 건 고수익으로 빈번한 작은 수익 목표를 달성했다고 하지 않는다.
- 초기 승인 정책 발행, 검증된 challenger 교체, 기존 정책 유지, 실제 경제성 수락을 별도 상태로 둔다. actual 체결 1건의 존재를 source-only 코드 검증 또는 이미 승인된 부모 정책 유지의 선행 gate로 만들지 않는다. 새 후보의 부정적 holdout이나 hard source 결손을 승인 편의를 위해 지우지도 않는다.

### 17.7 장후 갱신·AI 보조·다음 장전 연결

기존 `누적 calibration → candidate/activation 검증 → mechanistic bundle publisher → dated loader/PREOPEN → main PID` 한 경로를 사용한다. 그룹/종목/micro용 별도 cron과 publisher를 추가하지 않는다.

- 새 후보가 적격이면 그 계층만 교체하고 영향 없는 부모/자식의 provenance를 보존한다. 부모 변경으로 자식의 기준이 달라지면 재검증하거나 자식을 명시적으로 비선택 처리한다. 무조건 오래된 자식 delta를 새 부모에 더하지 않는다.
- 후보가 없으면 검증된 기존 정책으로 다음 거래일 bundle을 생성/유지한다. 매일 새 승자나 종목별 독자값을 강제하지 않는다. 기존 07:35 freeze·정확한 거래일·원자 발행·source snapshot·rollback generation을 보존하고, canonical report 재생성으로 이미 pin된 정책을 조용히 교체하지 않는다.
- AI에는 선택된 그룹/종목 보정·micro 근거·명시적 결손을 같은 frozen input으로 제공한다. AI는 타점 재선정기가 아닌 fact-bound PASS/VETO 심사자다. schema 오류/보수성만으로 자동 PASS시키지 않는다.
- 기존 AI prompt calibration/optimizer 경로에 그룹별 VETO 뒤 clean-fast 기회 손실과 PASS 뒤 adverse를 전달한다. 누적 통계 context 갱신과 검증된 prompt 후보 교체를 구분하며, 비교 후보가 없으면 기존 PASS/VETO prompt를 유지한다. 신규 AI 학습 서비스나 이번 기능 확인을 위한 Provider 전체 재호출은 만들지 않는다.
- 코드 배포와 정책 자동 적용은 별개다. 구현 후 검증된 main release·관련 분석 consumer의 schema 호환성을 확인한 뒤 승인 범위에서만 배포한다. 독립 widget/episode release와 최소 보조청산 pin은 변경하지 않는다. 다음 PREOPEN/PID 소비는 실제 해당 시각 receipt로만 닫는다.

### 17.8 실행 순서·테스트·종료조건

다음 W 번호는 이 계획의 작업 순서이며 native workorder ID가 아니다. 별도 구현 지시가 오면 기존 owner에 연결하고 완료된 연구/역할 교정은 새 계약에 영향받는 부분만 다시 검증한다.

| 순서 | 구현/확인 | 종료 근거 |
| --- | --- | --- |
| W1 | 기존 fixture로 3개 결손과 gate 요약/실제 불일치 재현; 누적 source·기계 미호출 census·micro 전달 대사 | 첫 결손 producer/consumer와 원천 분모 고정, 중복 구현 없음 |
| W2 | 기존 action core/그룹 resolver/종목 delta/micro variant와 trace 연결 | 같은 입력·정책 live/replay parity; 그룹이 비위험 공통 RECHECK에서 ENTER 가능하고 hard BLOCK은 불가 |
| W3 | 누적 calibration에서 실제 그룹/종목/micro 후보 추정·검증; gate 단일화 | 후보 또는 구체적인 reject/carry 사유; parameter·date split·source hash 재현 가능 |
| W4 | 기존 bundle 발행/validator/AI context/직접 verifier 확장 | candidate→다음 거래일 bundle→loader preview의 계층/role/hash 일치 |
| W5 | review→수정→재리뷰→targeted validation 반복; 격리 재생성 후 영향 consumer만 갱신 | 미해결 범위 내 finding 0, generation 일치, 현재 정책/pin 보존 |

필수 회귀 사례는 다음과 같다.

- 부모 상속/그룹 중복 매칭/종목 보정 범위 초과/부모 hash 변경/미래 데이터 혼입/겹치는 anchor 중복 집계.
- 공통 RECHECK→그룹 ENTER→AI PASS와 AI VETO 각각; hard BLOCK·malformed AI·missing source에서 probe/BUY 누출 0.
- 같은 구조에서 취소성 감소만 있는 창, BUY 설명이 있는 창, 과도 refill, 정상 반등/bid 지지, 고빈도 120행 truncation·stale 시작·route/epoch 불일치. 모든 경우 offline/runtime metric·action 동일.
- 실제 빠른 익절/횡보 후 익절/near-stop 후 익절/손실/동일 bar 순서 불명/기계 미호출/AI VETO를 각 원래 lane과 라벨로 보존.
- 다음 날짜 기존 정책 유지·유효 challenger 교체·부모 교체 시 자식 무효화·손상 bundle fail-closed·07:35 이후 동결·원자 publish 실패 시 이전 generation 보존.

검증은 변경한 기존 pytest 파일과 인접 consumer, compile, `git diff --check`, 문서 print-only parser로 제한한다. 비교 가능한 fixture/checkpoint를 우선 재사용한다. 필요한 재생성은 **최초 변경 source/label부터 calibration→policy→영향 handoff**까지 한 번 수행하고, 이후 새 결함이 있는 단계만 다시 실행한다. expensive replay/Provider·장후 전체 wrapper·매매 process는 자동으로 재실행하지 않는다. canonical 반영이 기존 verifier/controller/요약을 stale하게 만들 때만 해당 source date의 필요한 후행을 다시 닫는다.

완료 보고는 ① 세 기능 코드/계약 연결 ② 정책 생성·loader 검증 ③ 배포·실제 PID 소비 ④ 자연 clean-fast/비용 후 EV·순익/참여·tail을 분리한다. 기대효과는 **흐름별 빠른 기회 포착, 종목별 과도한 공통 threshold 감소, 취소성 잔량 감소에 속는 진입 감소, 미진입 데이터까지 누적 개선에 반영**이다. 효과의 크기와 수익 개선은 비교 결과 전에는 보장하지 않는다. 이번 문서 작성은 ①의 구현 완료나 신규 live 활성화가 아니다.

계획 자체의 리뷰에서는 공통 READY 중복 선행, adverse-flow의 완화된 fixed-ask validity 전용, 서로 다른 gate 중첩, 기계 미호출 원천 누락, 부모 변경 뒤 종목 보정 오적용을 점검해 위 실행/검증 항목에 반영했다. 문서 print-only parser 30개 task와 `git diff --check`를 통과했다. Python/Provider/replay·운영 재생성은 문서 변경 범위가 아니므로 실행하지 않았다. 코드·현재 정책·선택 release·PID는 변경하지 않았다.

## 18. §17 사용자 구현 지시 후 review/fix 결과

작성: 2026-09-13. 이 절은 workspace 구현·테스트 기록이며 새 계층 정책의 실제 발행·배포·PID 소비 receipt가 아니다. §17의 계획 수립 당시 상태는 이력으로 보존한다. 이번 실행에서 선택 release, canonical 정책/report, 주문·custody, 매매 process는 변경하지 않았다. 9/13 체크리스트 부재를 9/14의 실행 승인으로 대체하지 않았다.

### 18.1 구현한 연결

| 축 | 구현·검증한 동작 |
| --- | --- |
| 그룹·종목 | 기존 evidence owner에 단일 resolver와 bounded 계층 schema를 추가했다. 가격/틱·변동성·venue/session과 기존 흐름 family로 매칭하고 specificity→stable ID로 하나를 선택한다. 선택된 자식의 불리한 증거/필수 micro 결손 뒤 부모로 재시도하지 않는다. 종목 residual은 실제 calibration fitting 및 `n/(n+20)` 수축·범위 제한·종목별 holdout을 거친다. 자료 부족 종목은 부모 상속이지 강제 개별 최적값이 아니다. |
| 기계→AI | 그룹은 공통 hard BLOCK을 보존하면서 비위험 confirmation RECHECK를 자기 trigger+현재 BUY 체결/가격 반응으로 해소할 수 있다. selected threshold/hash·flow·micro를 frozen 입력과 AI에 결속한다. AI 유효 PASS만 기존 probe/최종 guard로 전달하고 VETO/CAUTION/오류로 실주문 권한이 새지 않음을 검증했다. |
| 새 micro | 기존 WS snapshot adapter·고정 1초 kernel을 변경 없이 읽는다. 초기 잔량 대비 감소속도·실제 BUY 설명·refill과 bid/가격 지지를 결합한다. 속도/설명/refill의 소수 one-coordinate 후보를 calibration에서만 고르며, 같은 complete-window/exit/cost 교집합의 4군 진단을 보고한다. 그룹별 정상화는 초기 잔량 대비 속도에 대한 그룹별 threshold fitting이며 별도 과거 평시 속도 모델을 구현했다고 주장하지 않는다. |
| 누적 원천 | Provider 호출 전 기계 ENTER/RECHECK/BLOCK을 기존 payload archive의 별도 schema로 보존한다. AI request/WAIT 정답을 합성하지 않는다. 최초 child가 없어도 micro를 관측하여 정책이 있어야 학습 원천이 생기는 순환 의존성을 제거했다. clean baseline 이후 기존 누적 source loader와 기존 경로 labeler를 재사용한다. |
| 정책·장후 | 기존 calibration의 `hierarchical_entry_quality.runtime_extension`→기존 publisher→dated loader→direct verifier를 연결했다. 최초 계층 채택은 기존 CLI의 명시적 `--adopt-hierarchy`; 채택 뒤 정상 장후 후보 교체/기존 정책 유지에는 매일 새 승인을 요구하지 않는다. 부모 hash 변경 시 자식을 명시적으로 재검증 대상으로 돌리며 07:35 freeze·immutable source·atomic publish를 유지한다. |

새 서비스·cron·DB·engine-root 모듈·독립 report producer는 추가하지 않았다. 공통 refinement와 그룹/종목 gate는 evidence owner의 기존 계약 상수로 연결했다. 공통 5종목/5일을 모든 그룹·종목에 중첩하지 않는다. 그룹은 기존 5노출/3일 calibration, 날짜분리 holdout 3노출/2일, 종목 residual은 15노출/5일 및 별도 holdout을 사용한다. 이미 검사한 9/11까지의 흐름 경계를 독립 holdout으로 재사용하지 않는다. 기존 실행 가능한 부모 정책을 유지하는 데 이 challenger 조건을 부과하지 않는다.

### 18.2 리뷰에서 수정한 직접 결함

- 종목 표본수만 세고 보정하지 않는 경로를 실제 delta fitting으로 연결하고, calibration 보정이 종목별 holdout에서 개선되지 않으면 탈락시켰다.
- stale 부모 hash·변조 context·일자 혼입·겹치는 300초 anchor·숫자 문자열/범위 오류와 malformed handoff를 검증했다. 그룹 PASS의 기존 공통 WAIT 중복 veto는 해당 검증된 그룹에만 한정해 보완했다.
- adapter가 진단상 허용하는 일부 fixed-ask gap을 새 BUY에 전용하지 않고 kernel 전체 validity를 요구했다. 기계 capture hash의 Unicode 직렬화 차이와 label context sanitization도 수정했다.
- `conservative_execution_cost_pct`가 기존 replay에서 half-spread+source-age penalty일 수 있음을 확인했다. 이를 수수료·세금까지 포함한 순비용으로 재라벨링하지 않는다. 기존 exact-date economic reference의 hash·원시 source·종목/venue coverage를 확인한 뒤 fee/tax/buffer와 기록된 friction을 묶고, 기존 raw 경로를 동일 비용으로 재라벨링한다. 세율·종목 상품군·누락 비용을 추정하지 않는다. 비용 profile 미검증·raw 경로 결손은 해당 행의 명시적 잔여 조건이다.
- 재라벨링은 `existing_fixed_boundary_counterfactual`이며 실제 사용자 손절/청산 override의 변경·실현수익 복원이 아니다. 원 report를 덮어쓰지 않고 새 계층 후보의 입력으로만 사용한다. 종목별 경로를 재사용하고 경제성 owner가 없는 날짜는 raw 전체를 불필요하게 다시 읽지 않는다.
- 기존 고정 target 0.30%에서 전체 비용이 0.20%를 넘으면 순 EV 0.10%가 불가능해지는 **출구/비용 평가 계약의 상한**을 별도 진단한다. 이 이유로 손실 행을 삭제하거나 수수료/목표를 임의 변경하지 않는다. 이 진단만으로 타점 로직 실패 또는 실제 전략의 음수 EV를 단정하지 않는다.

### 18.3 검증 및 남은 경계

- 변경 범위 6개 test suite **512 passed**. 그룹 ENTER→AI PASS/VETO/CAUTION, 종목 shrinkage/holdout, micro cancellation/refill/source-gap, 4군 동일 교집합, capture→기존 비용 owner→경로 라벨, 후보→최초 채택→다음 날짜 carry→loader 및 순 EV 0.10%의 부동소수점 경계를 포함한다. synthetic 후보의 비용 후 EV 통과는 코드 연결 테스트이지 실전 수익 근거가 아니다.
- `compileall`, 변경 파일 Ruff와 `git diff --check` 통과. `ai_engine_openai.py`의 기존 E402/E722는 Ruff 검사에서 제외했고 다른 변경 파일은 제외 없이 통과했다. 문서 print-only parser는 30개 task, 이번에 수정한 9/14 체크리스트는 stable ID 14개·중복0을 확인했다. 인접 OpenAI audit suite의 `computed_not_sent` 대 `not_attempted` 기대 불일치 1건은 변경 전 HEAD engine을 메모리에 로드한 재검사에서도 동일하게 재현했다. 이 기존 감사 표시 차이는 이번 계층 코드의 회귀로 세지 않았으며 전체 저장소 finding 0으로 확대하지 않는다.
- 실제 누적 detailed source는 **21개 날짜·936행**, executable reference 936행을 확인했다. 최초 비용 재평가의 중복 계산을 줄이기 위해 이번 세션이 시작한 read-only 분석만 중단·재실행했으며 운영 worker는 건드리지 않았다. 최종 읽기 전용 재평가: 경제성 owner 미검증/부재438·raw path 결손436·행별 비용/실행가능 reference 결손24·full-cost 경로 재라벨링38로 합계936이다. 이후 기존 그룹/흐름/품질 등 source contract 제외856·full-cost 또는 재라벨 필요76·계층 적격4행(9/9·9/11)으로 별도 보존된다. 두 단계의 제외 계수는 합산하지 않는다. forward holdout 날짜0, `promotion_pass=false`, `incumbent_carry_no_qualified_child`이며 자연 새 정책/양수 EV 성공으로 보고하지 않는다.
- 현재 초기 부모 정책과 새 child의 자격은 별개다. 첫 계층 활성화/배포·다음 PID 소비는 미실행이다. 기존 [9/14 Runtime owner](../checklists/2026-09-14-stage2-todo-checklist.md)에서 actual root/bundle/role/source를 확인하고, 기존 CodeImprovement owner에서 다음 누적 candidate와 cost/exit 상한·forward holdout·미관측 micro를 대사한다.
- 기대효과는 공통 threshold에 가려진 빠른 그룹 타점, 종목별 bounded 보정, 취소성 잔량 감소 오판 억제, AI 미호출 기회까지 포함한 누적 개선이다. 자연 적용 뒤 clean-fast precision/recall·참여·역행/횡보·비용 후 실현 순익을 각각 확인해야 하며 승률이나 코드 테스트만으로 효과를 확정하지 않는다.

## 19. 지원 연속매매 전체 scope 확장과 정책 작동 계약

2026-09-13 사용자 승인: 전체 변경 커밋·푸시·배포·기동, 시장 범위는 **지원 연속매매 세션 전체 우선**. 동시호가·시간외 단일가는 이번 범위가 아니다. 과거 §15~18의 KRX 한정·미배포 상태는 당시 기록이며 이번 실행 결과와 혼합하지 않는다. 독립 widget/episode 정책·service는 메인 진입 변경의 대상이 아니다.

### 19.1 적용 범위와 실제 의미

기존 `entry_setup_scalping_rollout.AUTO_PROMOTION_SCOPES`의 9개 내부 scope key를 재사용한다: `KRX|KRX_REGULAR`, `NXT|KRX_REGULAR`, `NXT|NXT_REGULAR_OVERLAP`, `NXT|NXT_REGULAR`, `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE`, `NXT|NXT_PREMARKET`, `PREMARKET_KRX_LIKE|NXT_PREMARKET`, `NXT|NXT_AFTERMARKET`, `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET`. 이는 9개 별도 시장을 뜻하지 않는다. SOR 통합 경로의 기존 종목 적격성·실제 route/receipt·수량/canary 제한은 최종 주문 owner가 계속 검사한다.

기존 KRX 한정은 초기 bundle의 단일 cohort와 resolver의 명시적 분기 때문이었다. 기존 publisher에 `--adopt-all-continuous`를 추가해 명시적 최초 채택 후에는 일별 자동승계를 유지한다. 과거 v1 KRX-only bundle은 비KRX 권한으로 해석하지 않는다. 추가 리뷰에서 통합 aftermarket의 옛 observe-only 차단과 recheck allowed-scope의 auto-promotion 누락을 발견했다. 유효한 기존 all-session pin이 있는 경우에만 두 consumer를 연결하고 운영자 OFF·변조/만료 pin 차단은 보존했다.

### 19.2 판정 순서와 예시

`기존 scanner/감시 평가 → exact venue/session 정책 → 기계 ENTER_NOW/RECHECK/BLOCK → ENTER_NOW만 AI PASS/VETO 심사 → 기존 recheck/submit·broker guard → 주문/체결`이다. 독립 고빈도 WS 주문기계나 새 AI 호출 루프를 추가하지 않았다. 원래 scanner 진입 전 놓친 구간을 이 변경으로 복원했다고 주장하지 않는다.

- **현재 공통 초기값:** micro 순공격 delta 최소1, micro 가격변화 양수, spread 100bp 미만, fillability 15 초과, top3 ask/bid 5 미만. 이 값만 충족하면 BUY라는 뜻은 아니다. 원래 setup/source·hard-risk 및 최종 가격/수량/주문 guard가 함께 작동하며 spread 100bp는 허용 체결비용이나 목표수익이 아니다.
- **예시 A — 정상 진입:** 유효 setup에서 micro delta20·가격반응 +0.10%, spread10bp·fillability60·ask/bid1.2라면 기계가 다른 필수 조건까지 검사한다. ENTER_NOW 뒤 AI가 현재 지지·불리한 사실을 함께 검토하여 PASS하면 기존 제출 경로로 진행한다. VETO면 그 타점은 거절하며, CAUTION/INSUFFICIENT/응답 오류는 노출을 허용하지 않는다. AI가 기계 RECHECK/BLOCK을 BUY로 승격할 수 없다.
- **예시 B — 종목 보정:** 자격을 갖춘 특정 그룹의 parent threshold100, 종목 calibration20건에서 delta−40이 선택되면 `100 + 20/(20+20)×(−40)=80`을 bounded 범위 내에서 검증한다. 종목별 holdout까지 통과해야 선택한다. 이는 산식 설명이며 현재 모든 종목에 해당 보정이 발행됐다는 뜻이 아니다.
- **예시 C — 취소성 감소:** 매도잔량이 빠르게 줄어도 실제 같은 가격 BUY 설명이 부족하거나 refill이 커지면 선택된 micro 조건을 통과하지 못한다. 필요한 고정1초 창이 불완전하면 RECHECK이며 부모 정책으로 재시도하지 않는다. 아직 micro child가 없는 scope에서는 해당 자료를 수집·학습하되 활성 조건으로 표시하지 않는다.

### 19.3 누적 튜닝·승계와 과도한 gate 점검

기존 calibration에서 `runtime_extensions_by_scope`로 비용·흐름·그룹·holdout을 분리하고, 기존 optimizer handoff/verifier와 publisher/loader까지 결속한다. 비KRX 초기값은 공통 seed이며 KRX에서 최적화한 값의 복사가 아니다. 경제성 owner의 exact venue/product 근거가 없는 alias는 원천 결손으로 남기고 다른 시장의 세금/비용으로 대체하지 않는다. 새 서비스·cron·DB·report producer를 추가하지 않는다.

초기정책 사용에는 challenger 표본수를 요구하지 않는다. 이후 그룹/종목/micro challenger는 §18의 날짜분리·전체 비용 후 EV 최소 +0.10% 및 빠른 수익/역행·횡보 기준을 적용한다. 표본15건이라는 이유만으로 승인하거나 거절하지 않고 날짜·비용·독립 holdout·parent binding을 함께 본다. 0.10%는 학습 평가의 목표이며 매 주문 보장수익이 아니다. source9/11의 forward holdout0·child0은 그대로 유지하며 강제 BUY·손실행 제거·비용축소로 통과시키지 않는다.

기존 calibration `--write`가 dated machine+AI bundle을 갱신하고, 다음 장전에는 기존 exact-date env·all-session pin과 policy loader가 이를 소비한다. 자격 있는 새 child가 없으면 실행 가능한 incumbent를 유지한다. AI도 기존 같은 scope의 optimizer→PREOPEN 검증을 통과한 base prompt를 선택하고 PASS/VETO 역할 부록을 유지한다. 코드 자동생성/무제한 프롬프트 수정이 아니라 등록·검증된 정책의 자동 선택이다. 07:35 이후 당일 bundle을 다시 쓰지 않는다.

### 19.4 배포·기동 검증 경계

변경 범위 테스트·소스 검증 뒤 검토 commit을 새 release로 고정하고 공통 selector를 전환한다. 기존 release/선택 원장/정책 generation은 rollback용으로 보존한다. 실제 배포 hash·정책 hash·검증 결과는 아래 실행 receipt에 기록한다. 9/13 일요일에는 main PID와 당일 runtime env가 없으므로 9/14 env를 복사해 강제 기동하지 않는다. 기존 9/14 07:35 PREOPEN·07:55 기동 예약을 유지하며 미래 PID 성공으로 보고하지 않는다.

최종 변경/인접 10개 suite **694 passed**: 9 scope resolver·운영자 OFF, legacy KRX-only 격리, 변조 pin·recheck authority, NXT 독립 fitting/비용 scope 혼입 거절, 재해시한 cross-market handoff 거절, publisher/loader·기존 recheck와 release routing을 포함한다. scoped Ruff·compile·`git diff --check`와 print-only parser(30 task)를 통과했다. §18에 기록한 기존 OpenAI audit 표시 불일치는 별도 잔여 이력이며 전체 저장소 무결함으로 확대하지 않는다. 실주문/Provider 호출·고비용 과거 전체 재생성은 이 검증에 사용하지 않았다. 기존 bundle이 보존한 source9/11 snapshot으로 초기 범위 채택만 발행하고, 누적 신규 challenger 재평가는 다음 자연 장후 owner에 연결한다.

### 19.5 실행 receipt — 2026-09-13 23:25 KST

- 구현 commit `d3cb8d44d651f20f6c3dfcde97f4ec86e9706f9b`와 시각 대사 보완 commit `6207a60cf456d77bcccb14601c25cd7d03e3583a`를 main에 커밋·push했다. 최종 공통 선택 root는 `/home/ubuntu/KORStockScan-runtime-releases/machine-all-continuous-r2-20260914`, code HEAD는 `6207a60c`다. 후속 문서 receipt commit은 source 배포 세대와 구분한다.
- 최초 별도 worktree에서도 694 tests를 재검증했다. 실제 future-env preview에서 resolver의 평가시각과 recheck 승인시각 불일치를 발견하여 `now` 전달을 보완했다. workspace 전체 694 tests 재통과, 최종 detached release의 영향/인접 228 tests 재통과이며 합산 고유 테스트 수로 표시하지 않는다. 운영자 OFF·미래 pin 활성화 경계를 유지한다.
- 23:18 기존 publisher로 `--adopt-hierarchy --adopt-all-continuous`를 실행했다. target9/14, source9/11 frozen source file SHA `c345ad4e410199f1704d82c973f5b07e1dd1a1cbf1f97f73004c2099f22d267a`, bundle SHA `3f6d353fdf930cac4ab31f6a49187a53deb667d14ac6d8be28c0058ef834d983`. **9 scopes의 초기/유지 정책을 발행했으며 자식 rule은 모두0**이다. 종목별 최적값·새 micro 실전 임계치가 이미 선택된 것으로 표현하지 않는다. old bundle `b7d45817…`는 기존 generations와 별도 backup에 보존했다.
- release 테스트가 만든 실제 `logs/tmp` 디렉터리 때문에 최초 공유 경로 검사가 실패한 것은 무시하지 않았다. 해당 테스트 출력을 backup으로 이동하고 정상 shared symlink로 수정한 뒤 router를 재검증했다. 최종 source clean, 6개 공유 경로, cron9개, PREOPEN/start/postclose print-plan 모두 PASS. 실행 중인 main/장후 worker가 없는 구간에서 전환했으며 cron·실주문·custody를 변경하지 않았다.
- 최종 release의 `threshold_cycle_preopen_apply --verify --target-date 2026-09-14`는 PASS다. 23:25 실제 저장 env의 threshold→operator→dated 순서를 읽은 정책 선택 preview는 parse error0, 9/9 scope에서 기계 주판정과 `auxiliary_risk_screen_pass_veto_no_promotion`을 확인했다. 명시적 미래 평가시각을 넣은 **정책 선택 검사**이며 해당 시각의 시장 개장·현재 PID·실제 주문 성공은 아니다.
- backup/검사 파일: `tmp/machine-all-continuous-deploy-20260913.LaNvTe/`의 `previous-selection.json`, `previous-policy.json`, `preopen-env-preview.json`, `final-policy-preview.json`. 원 release `machine-ai-pass-veto-20260914/f12a9373`와 중간 검토 release도 보존한다. rollback 시 현재 실행/정책 세대를 재대사하고 필요한 원 policy generation도 함께 선택하며 shared state를 초기화하지 않는다.
- 독립 machine profit manifest SHA `caa1e8071daf226fe4c67e0e9654e84a4ae5a7b71c9e749bcde3b2c9f01ed893`, unified manifest SHA `44382bb658ef37cafc4476cf75b3a0b40979e2a81d0b4f75523f8922d12bf12a`는 전후 동일하다. 독립 service/drop-in을 재배포·재기동하지 않았다.
- 기동 승인은 확인했으나 일요일9/13 main PID·당일 env가 없어 수동 기동은 하지 않았다. **9/14 07:35 PREOPEN→07:55 예약 기동을 유지**, 실제 PID/첫 정책 소비·장후 자동 새 generation·빠른 비용차감 순익의 자연 수용은 기존 9/14 Runtime/CodeImprovement owner에 남는다. 현재 상태는 코드·정책 발행·배포 완료 / 자연 기동·경제성 미확인이다.

## 20. 판정 시점·후속 경로 기반 장후 학습과 다음 장전 정책 — 9/14 구현계획

상태: 계획 수립. 이번 절은 코드 구현·장후 실행·정책 발행·배포 완료 기록이 아니다. 사용자의 최신 요청으로 앞선 ‘장전 후보 생성 제외’ 범위를 변경하여 **장후 자동 정책 생성→다음 거래일 장전 소비**를 완료 목표에 포함한다. 기존 §17~§18 구현을 재작성하지 않는다.

### 20.1 목적과 완료 산출물

기계가 당시 알 수 있던 정보로 빠른 수익 타점을 선택하고, AI가 PASS/VETO로 보조하며, 누적 결과가 다음 정책을 갱신하도록 한다. 비용 후 +0.10% 최초 도달은 개별 기회 라벨이고, EV는 실패를 포함한 정책별 결과 평균이다. 최종 익절만으로 좋은 타점이라고 판정하지 않는다.

필수 산출물은 기존 report 안의 판정별 사례·결손/병목 집계, 누적 incumbent/challenger 비교, 다음 거래일 정책 bundle, 장전 loader 검증과 기동 후 PID 소비 receipt다. 새 정책 파일이 발행돼도 임계치 변경 여부는 별도 필드로 설명한다. 검증 실패를 숨겨 개선 정책을 강제 발행하지 않으며, 유효 incumbent가 있으면 기존 carry 계약으로 다음날 사용할 정책을 발행한다. 유효 정책 자체가 없거나 손상됐으면 발행/적용 실패를 명시한다.

### 20.2 확인한 기존 owner와 최소 변경 위치

| 기존 파일/경로 | 재사용 범위 | 필요한 보완과 종료조건 |
| --- | --- | --- |
| `src/engine/monitoring/entry_turn_point_replay.py` | 결정시각 BBO join, pre-anchor 경로, 이후 경로와 단계별 시간차 | TP1 원천과 main 기계판정 원천의 identity 차이를 유지한 adapter. 일반 기계판정까지 이미 지원하는지 fixture로 먼저 확인하고 결손만 추가 |
| `src/engine/monitoring/rising_missed_intraday_feedback.py` | 위 replay의 기존 report owner | 사례/원천 hash를 직접 consumer로 전달. TP1 진단을 모든 기계판정의 학습 원천으로 오인하지 않음 |
| `src/engine/scalping/ai_decision_quality.py` | 기존 경로 라벨과 시간구간 평가 | 같은 anchor·비용·경로에서 목표 도달 전 역행/횡보와 검증 가능한 종료 결과를 재사용. 중복 labeler 생성 금지 |
| `src/engine/scalping/ai_action_outcome_calibration.py` | `load_machine_observation_rows`, 누적 source loader, 비용 재라벨링, `build_mechanistic_hierarchy_candidate` | AI 미호출 ENTER/RECHECK/BLOCK와 replay의 유효 행을 같은 기존 입력 계약에 연결. 종목/그룹·scope별 비교 및 최초 blocker 전달 |
| `src/engine/scalping/entry_setup_evidence.py` | live와 replay 공통 판정·계층 resolver | 정책별 재생에 같은 함수 사용. 기존 입력/판정이 충분하면 수정하지 않음 |
| `src/engine/scalping/mechanistic_entry_runtime_policy.py` | 누적 calibration의 `--write`가 호출하는 `publish`, 거래일 calendar, generation 보존, 장전 동결 | 신규 검증 정책/유효 incumbent carry 각각 발행 결과·source hash·실제 변경 내역을 downstream까지 전달 |
| `src/engine/scalping/entry_setup_live_policy.py` | `load_effective`와 scope별 소비, AI 보조 role | 다음 날짜 bundle 선택·fallback·거절의 직접 사유 검증. 자동 소비를 위해 새 수동 env 경로를 만들지 않음 |
| 기존 main postclose / paired replay follower / PREOPEN wrapper | calibration 정기 호출 및 장전 검증 | producer 순서·늦은 결과 갱신·최종 source hash·정책 검증을 연결. 새 cron/독립 학습기/보고서 producer 추가 금지 |

### 20.3 작업 순서와 수용조건

| 순서 | 구현 작업 | 수용조건 |
| --- | --- | --- |
| P1 원천 대사 | clean baseline 이후 이용 가능한 날짜를 manifest로 고정. 기존 machine archive와 TP1 replay의 실제 중복/결손 확인 | 날짜별 판정 총수=유효+제외+결손. AI 미호출 행 보존. 이미 연결된 경로는 재구현하지 않음 |
| P2 사례 연결 | source hash·evaluation/attempt·promotion·symbol·venue/session·policy hash로 당시 입력과 이후 경로 결속 | 같은 종목의 다른 시점·route·정책 join 금지. 저장되지 않은 과거 입력을 현재값으로 보충하지 않음 |
| P3 경로 평가 | 기존 라벨에 빠른 목표 도달/긴 횡보/깊은 역행/실패/미확인을 매핑하고 최초 병목 기록 | 실제 체결과 가상 ask→bid 결과 분리. 동일 bar의 선후 불명·부분체결·오래된 호가를 확정 성공으로 세지 않음 |
| P4 누적 비교 | 영향 큰 기존 조정 가능 조건 1~3개를 사전 고정하고 공통 판정기로 재생 | 과거 날짜에서 선정, 분리된 후행 날짜에서 비교. 공통→그룹→종목 기존 상속 재사용. 새 전수 grid 없음 |
| P5 정책 발행 | 선택 결과를 기존 candidate validator→publisher로 전달 | 적격 challenger는 bounded 변경, 미달은 사유 있는 incumbent carry. 지원 연속매매 scope 전체를 각자의 근거/정책으로 대사 |
| P6 자동화 closure | 최초 영향 producer부터 calibration→bundle→장후 summary/strict→장전 loader→PID 검증 | 다음 거래일 정책 파일·hash·effective date·intended consumer 확인. 파일 존재만으로 적용 완료 처리 금지 |

P1에서 누적 loader가 이미 받는 자료와 빠진 자료를 분명히 구분한다. 기존 보고서 요약 숫자를 학습 행으로 재생성하지 않으며, 추가 adapter는 가능한 기존 파일 내부에 둔다. runtime trace 수정은 해당 정보가 실제로 누락됐다는 증거가 있을 때만 수행한다.

clean baseline의 과거 학습은 detailed paired replay가 소유한다. `mechanistic_entry_observation_v1` capture는 9/13부터의 신규 원천이므로, 이전 281MB payload archive를 매일 전수 해제해 가짜 과거 capture를 찾지 않는다. capture 이전 기간의 기계 당시 입력은 확인 불가로 census에 남기고, 그 이전의 유효 paired 행과 혼합하지 않는다.

### 20.4 평가 계약

- 입력은 판정시각까지의 frozen 자료만 사용한다. 종목 유동성·변동성·흐름 그룹과 정규화 기준도 과거 구간에서 산출한다. 이후 상승은 label에만 사용한다.
- 180초를 빠른 타점의 primary 평가창으로 유지한다. 기존 30/60/180/300초 진단을 우선 재사용하고 10초는 원천이 지원할 때만 추가한다. 모든 구간 완비를 공통 승인 gate로 추가하지 않는다.
- 사례별 비용 후 +0.10% 첫 도달시간, 그 전 최대 역행, 수익 가능한 호가 지속시간, 구간 종료 결과와 관측 gap을 남긴다. 깊은 역행의 기준은 당시 유효 stop/위험 계약 또는 train에서 고정한 유형별 기준을 인용한다. 사후 stop 변경을 과거 label에 적용하지 않는다.
- 가상 결과는 검증된 fee/tax/slippage와 진입 ask·청산 bid·수량을 사용한다. 비용 중복 차감과 비용 결손의 0 대체를 금지한다. 목표 미도달 행도 사전 정의한 평가 종료 규칙으로 포함하며, 목표 성공행만의 평균을 EV로 보고하지 않는다. 실제 PnL은 기존 COMPLETED·유효 비용 계약으로 별도 집계한다.
- 모든 판정은 사례표에 남기되, 통계는 기존 promotion/attempt identity와 사전 고정한 비중첩 기회 단위로 중복을 통제한다. 실제 별개의 재진입은 보존한다. 날짜 경계에 걸친 outcome은 학습/검증 양쪽으로 새지 않게 제외하거나 경계를 분리한다.
- 감시 이전 상승→최초 감시, 감시→기계, 기계→AI, AI→제출/체결의 지연을 분리한다. 감시 밖 모집단을 확보하지 못하면 scanner 전체 recall은 미확인이다.
- 새 depletion 속도·trade backing·refill은 유효한 해당 원천 구간에서만 기존 micro variant로 평가한다. 과거 미수집 자료 때문에 공통/그룹 전체 학습을 막지 않으며, 미수집 micro를 통과값으로 채우지 않는다.

### 20.5 임계치 승인과 과도한 gate 제거 점검

적격 challenger는 **검증 집합 비용 후 EV ≥0.10%, incumbent 대비 개선, 기존 해당 family의 sample/source/tail/bounded-change 조건**을 만족해야 한다. 0.10%의 단위는 10bp이며 코드의 percent 값과 fraction을 구분한다. 기존 gate와 이 목표가 다르면 실제 validator·producer 요약·loader가 같은 계약을 쓰도록 변경 항목으로 명시한다.

기회 포착률·빠른 목표 도달률·목표 전 역행·순익/일·자본점유는 incumbent와 같은 모집단·exit 가정으로 비교한다. threshold 하나의 차이로 새로 ENTER된 사례에는 별도 증분 결과를 남겨 기존 성공 사례에 가려지는 손실을 확인한다. 실제 수량 확대·청산 정책 변경을 entry 개선에 혼합하지 않는다.

sample floor는 실제 해당 validator의 값/관측값/통과 여부를 출력한다. 그룹 연구·종목 보정·공통 정책의 서로 다른 표본 조건을 중첩하지 않는다. 종목 보정 표본 부족은 유효 부모 사용을 막지 않는다. CF 근거로 실주문 체결품질 검증 완료를 주장하지 않는다. 기존 live family가 허용하는 CF 기반 조정 범위를 넘는 후보는 명시적으로 차단한다.

AI는 기존 PASS/VETO 역할을 유지한다. 기계 ENTER 뒤 VETO로 놓친 기회는 별도 attribution하며 기계 threshold 문제로 돌리지 않는다. 기존 AI optimizer가 발급하고 승인한 prompt는 기존 경로로 갱신한다. historical context 갱신만을 prompt 최적화나 판단 향상으로 보고하지 않는다. 기계 평가를 위해 Provider를 일괄 재호출하지 않는다.

### 20.6 장후→다음 장전의 실행 계약

1. 실행 때 선택 release·실제 wrapper snapshot·calendar·source generation을 고정한다. target은 `next_target(source_date)`의 거래일로 계산한다.
2. 기존 replay/report의 필수 원천이 준비된 뒤 calibration을 실행한다. 현재 main wrapper와 follower의 호출 순서를 대사해 새 입력 producer가 늦다면 기존 owner 순서를 최소 보완한다. 원천 준비 전 성공한 빈 학습으로 닫지 않는다.
3. `ai_action_outcome_calibration --write`의 기존 publisher 호출에서 다음 날짜 bundle을 발행하고, 반환된 생성/유지/동결/오류를 report·최종 검증까지 연결한다. source가 같으면 멱등 유지한다.
4. 늦은 follower가 source를 변경하면 기존 장전 07:35 동결 이전에 필요한 bundle만 재발행하고 최종 요약 hash를 재대사한다. 실행 중 writer·발행된 pin 충돌 없이 수행하며 원 generation을 보존한다.
5. 다음날 장전 검증은 기존 loader로 날짜·scope·bundle/source hash·role·operator override·부모/종목 pin을 검증한다. 후보 없음, incumbent carry, missing update, invalid policy를 서로 다르게 표시한다.
6. 기존 예약 기동 뒤 실제 PID의 release/정책 hash 및 첫 기계→AI 소비를 확인한다. 장후 완료 시점에는 다음날 PID 성공을 미리 선언하지 않는다.

미배포 코드로만 성공하는 격리 발행은 정기 자동화 완료가 아니다. 구현 후 검토 commit을 선택 release에 반영하고 다음 예약이 동일 코드를 소비하는 것까지 배포 범위에 포함해야 한다. 장후 chain 진행 중에는 선택 코드를 교체하지 않는다.

### 20.7 검증·재작업 제한·인계

기존 `test_entry_turn_point_replay.py`, `test_ai_decision_quality.py`, `test_ai_action_outcome_calibration.py`, `test_mechanistic_entry_runtime_policy.py`, `test_entry_setup_evidence.py`와 직접 loader/wrapper 테스트 중 변경 경로만 실행한다. 필수 반례는 빠른 성공·긴 횡보 후 성공·깊은 역행 후 성공·실패·중복 판정·잘못된 route/time join·비용 결손·시간 누출·부분 관측·AI 미호출·scope 상속·publisher 재실행·장전 동결이다.

동일 fixture로 `replay→calibration→candidate→publish→다음날 loader`까지 한 번 검증하고, 실데이터는 영향 source만 재생성한다. 전체 장후 wrapper·대량 Provider 호출·새 서비스·별도 DB·거대 신규 모듈은 기본 작업에 포함하지 않는다. 기존 성공 테스트는 변경이나 새 finding이 없는 한 반복하지 않는다. 코드 리뷰 finding 수정→재리뷰→targeted validation 뒤 실제 자동화 단계로 진행한다.

실행 owner는 [9/14 체크리스트](../checklists/2026-09-14-stage2-todo-checklist.md)의 OPEN `CodeImprovementWorkorderReview0914`와 연결한다. 완료된 `RuntimeEnvIntradayObserve0914`는 이번 새 검증 owner로 재개하지 않는다. 구현 실행 시 기존 다음 거래일 장전/기동 owner를 확인해 인계하고, 없으면 그때 실제 Due/Slot/TimeWindow/Track을 가진 owner를 한 번만 생성한다. 이 계획에서는 예정 실행이나 미래 성공 receipt를 만들지 않는다.

최종 보고: 원천 유효/결손 수, 독립 기회 수, 최초 병목 상위 1~3개, 변경 전후 임계치·검증 성과, 정책 disposition·bundle hash·effective date, 자동 발행/장전 검증/PID 소비의 각각의 상태를 남긴다. **검증된 개선 정책 또는 명시적으로 유지된 유효 정책이 다음 장전 소비 가능해야 운영 인계가 완료**이며, 실제 수익 개선은 적용 후 별도 확인한다.

### 20.8 구현·리뷰 결과 — 9/14

`_mechanistic_source_rows(..., all_supported_cohorts=True)`가 report header를 KRX 정규장으로 선필터해 NXT `NXT_AFTERMARKET` 행을 scope별 extension에 전달하지 않는 결함을 수리했다. 기본 KRX 경로는 그대로 유지하며, all-scope 호출에서만 `mechanistic_scope_supported`의 지원 연속매매 scope를 통과시킨다. 9/11 원천 대사에서 기존 KRX 936행에 NXT 634행이 추가로 연결됐다. 이 수치는 source coverage이며 edge 또는 실주문 성과가 아니다.

과거 machine capture 범위를 clean baseline으로 넓히려던 초안은 철회했다. capture가 9/13부터 존재하고 과거 archive 전수 해제는 장후 I/O·메모리만 늘리기 때문이다. 180초 primary·30/60/180/300초 진단, 비용 후 0.10% 라벨, 깊은 역행/횡보 분리, group/symbol holdout과 기존 candidate→publisher→PREOPEN loader 경로는 이미 구현돼 있어 중복 구현하지 않았다.

검증은 all-scope NXT regression, calibration/policy/evidence/live-policy/decision-quality 직접 회귀 493건, compile, `git diff --check`, 문서 print-only parser로 닫는다. 정책 bundle은 current all-continuous 9 scope 정책을 유지하며, 이번 수리는 다음 장후 calibration이 NXT 자료로 별도 candidate/holdout을 평가할 수 있게 한다. 실제 새 bundle generation·다음 장전 PID 소비·비용 후 경제성은 자연 장후/장전 receipt로 확인한다.

사용자 선택 문서 외부 동기화(정책 적용/봇 기동의 선행 조건 아님):

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 21. #77 R0–R3·21:05 paired replay·#78·#80의 AI 보조심사 전환 상세 구현안

후속 정정: 아래는 최초 제안 이력이다. 현재 구현 기준은 §22이며, 특히 base+addendum 구성, A0/A1 필수 비교, §21.7의 최초 선택 gate와 §21.9의 적용 대기 조건을 그대로 구현하지 않는다. source lineage·owner 분리 원칙은 §22와 충돌하지 않는 범위에서 유지한다.

상태: 계획 수립. 이번 절은 코드·정기 wrapper·Provider 실행·정책 bundle·PID를 변경한 receipt가 아니다. 현행 런타임의 `기계 ENTER_NOW → AI PASS/VETO → final guard` 역할은 유지하고, 장후 평가와 prompt 선택 기준만 그 역할에 맞게 정정한다. 기계 threshold, 주문가격·수량·cap, provider/model/route, 최종 submit 및 hard/broker guard는 변경 대상이 아니다.

### 21.1 판정과 확인된 현재 결손

현행 코드에는 전환의 재사용 기반이 이미 있다.

- `entry_setup_evidence.compose_mechanistic_primary_decision`은 기계 `ENTER_NOW`에만 AI 심사를 요구한다. 유효 `PASS`만 기존 final guard로 전달하고, `VETO`는 해당 타점을 거절하며, `CAUTION|INSUFFICIENT|transport/schema/local 오류`는 비노출 재확인으로 닫는다. 기계 `RECHECK|BLOCK`은 AI가 승격할 수 없다.
- `ai_action_outcome_calibration.load_machine_observation_rows`와 `machine_decision_case_table_v1`은 기계 action·reason·threshold·bundle·snapshot과 AI/final-guard trace 및 후행 경로를 exact identity로 결속한다. #11/#74도 기계평가, AI 평가, 실제 provider 호출을 별도 분모로 감사한다.
- `entry_setup_live_policy`와 `ai_engine_openai`는 유효한 optimizer base prompt를 선택한 경우에도 같은 `AI_ADDENDUM`과 historical context를 붙여 기계 보조심사 prompt를 구성한다.

그러나 #77~#80의 장후 평가계약은 아직 독립 AI 진입선정의 흔적을 보존한다.

| 위치 | 현재 동작 | 보완이 필요한 이유 |
| --- | --- | --- |
| `ai_decision_quality.prepare_detailed_paired_replay_requests` | exact payload에서 entry evidence를 재구성하고 base prompt별 BUY/WAIT/DROP 또는 risk verdict를 비교 | 당시 기계 action·bundle·selected child/micro와 현행 PASS/VETO 부가 지시문을 replay 입력·prompt hash의 필수 구성요소로 요구하지 않는다 |
| `entry_setup_paired_replay_batch._cohort_result` | 과거 Entry AI control 전체를 분모로 candidate Provider replay | 실제 보조심사 대상인 기계 `ENTER_NOW`와 기계 `RECHECK|BLOCK`·기계 전환 이전 trace를 분리하지 않는다 |
| `ai_action_outcome_calibration._transition_summary` | candidate exposure, false-drop, candidate EV와 probe risk로 prompt review 여부 판정 | 보조심사는 새 BUY를 고르는 owner가 아니므로 exposure 수와 BUY/WAIT/DROP 전이를 primary metric으로 쓰면 역할이 어긋난다 |
| `main_ai_prompt_optimizer` | base prompt 후보와 micro 입력 factorial을 선택 | candidate가 **base prompt + 동일 PASS/VETO addendum + 동일 기계 context**로 평가됐음을 강제하지 않는다 |
| `main_ai_prompt_consumer` | optimizer·paired artifact·R3 source-only handoff의 hash/terminal 검증 | auxiliary role/addendum/machine-context generation과 실제 replay 결과의 결속을 검증하지 않는다 |
| `mechanistic_entry_runtime_policy` | 초기/carry bundle의 base prompt가 V2.15.2로 고정되고, runtime resolver가 별도 optimizer base를 선택하면 호출 시 addendum을 조합 | 장후 candidate가 런타임과 같은 최종 prompt를 사용했다는 공통 composer/hash receipt가 없다 |
| `entry_setup_paired_replay_batch.DEFAULT_COHORTS` / `entry_replay_cohort_contract_v1|v2` | KRX 정규장·NXT 애프터마켓과 통합 애프터마켓 observe 경로 중심 | 실제 all-continuous runtime의 9개 scope와 전수 대사가 닫히지 않아 다른 연속매매 scope의 AI 보조심사 품질이 미평가될 수 있다 |

따라서 이번 구현의 핵심은 새 AI나 collector를 만드는 것이 아니라, **기존 exact machine source를 #77 replay의 부모로 고정하고 Entry 평가·#78 선택·#80 검증을 보조심사 지표로 바꾸는 것**이다.

### 21.2 목표 체인과 owner

목표 체인은 다음 하나다.

`#11 preflight → #76 exact materialization → 기계 ENTER_NOW screenable manifest → #77 R0–R3 auxiliary paired replay → #82 action/outcome calibration → #78 base-prompt optimizer → 21:05 terminal replay/frozen rebind → #80 consumer → 기존 PREOPEN prompt candidate/loader → PID first-use → 다음 장후 귀속`

| 단계 | 기존 owner | 보완 후 책임 |
| --- | --- | --- |
| R0 | `ai_decision_quality` + `ai_action_outcome_calibration`의 machine source loader | 기계 평가 전수 보존, 그중 `ENTER_NOW`만 AI screenable 부모로 발행. `RECHECK|BLOCK`은 provider 미호출 정상 분모로 남김 |
| R1 | 당일 detailed paired report | 동일 부모에 incumbent/candidate 보조심사를 실행하고 당일 오류·판정·후행 label을 분류 |
| R2 | `ai_action_outcome_calibration` | scope별 누적 correct VETO, missed VETO, dangerous PASS, correct PASS 및 오류율·비용 후 기회손실 계산 |
| R3 | 기존 source-only candidate manifest | 등록된 base prompt 후보만 다음 검토 대상으로 투영. live 적용 권한은 계속 없음 |
| #78 | `main_ai_prompt_optimizer` | 보조심사 손실함수로 base prompt만 선택. addendum·machine context·output schema는 고정 |
| 21:05 | `entry_setup_paired_replay_batch`와 기존 wrapper | terminal detailed 생성 후 #82→#78→metadata-only rebind→#80 순서를 유지하고 동일 generation을 검증 |
| #80 | `main_ai_prompt_consumer` | 모든 Entry cohort의 terminal과 auxiliary 계약/hash/분모 보존식을 검증하여 PREOPEN owner에 전달 |
| runtime | 기존 `entry_setup_live_policy`·`ai_engine_openai` | 검증된 base prompt에 동일 addendum/context를 조합. 기계가 선택하지 않은 타점을 AI가 생성하지 못하게 유지 |

새 cron, 별도 report producer, 별도 AI endpoint, 별도 DB는 추가하지 않는다. holding/exit R0–R3 계약은 이번 Entry 역할 변경으로 재해석하지 않는다.

### 21.3 R0의 screenable manifest와 보존식

기존 machine case table 안에 `entry_auxiliary_screen_population_v1`을 추가한다. 행 key는 다음을 모두 포함한다.

`source_date + evaluation_attempt_id + stock_code + effective_venue + session_bucket + decision_snapshot_id + machine_bundle_sha256`

`evaluation_attempt_id`나 snapshot/bundle이 없으면 symbol·근접시각으로 보충하지 않고 source gap으로 남긴다. 같은 key에 action 또는 bundle이 충돌하면 해당 key만 격리한다.

필수 분모 보존식은 다음과 같다.

```text
machine_evaluation_total
  = machine_nonentry_total
  + machine_enter_screen_required_total

machine_nonentry_total
  = machine_block_total
  + machine_recheck_total

machine_enter_screen_required_total
  = ai_screen_valid_terminal_total
  + ai_screen_transport_error_total
  + ai_screen_schema_semantic_error_total
  + ai_screen_local_unavailable_total
  + ai_screen_source_gap_or_pending_total

ai_screen_valid_terminal_total
  = ai_pass_total
  + ai_veto_total
  + ai_caution_total
  + ai_insufficient_total
```

- `machine_nonentry_total`에는 replay Provider를 호출하지 않는다. 이 분모의 AI 미호출은 정상이며 `provider_failed`가 아니다.
- `machine_enter_screen_required_total`만 paired replay 부모가 될 수 있다. 전환 이전 AI-only trace나 기계 observation 없이 사후 재구성한 action은 별도 legacy diagnostic으로만 보존한다.
- `provider_called=true` 실제 호출과 cache/local/transport 미호출을 분리한다. provider0 metadata rebind를 AI 평가로 세지 않는다.
- #11 preflight와 #74 final receipt의 source manifest/hash, `tuning_input_allowed`, gap count를 R0 artifact에 결속한다. source gap은 식별 가능한 행만 제외하고 나머지 scope를 계속 평가한다.
- action-neutral outcome은 replay 입력에서 제거하고 응답 terminal 뒤에만 join한다. 기계 context 자체에도 미래 first-hit·MFE/MAE·실현손익을 넣지 않는다.

scope 계약은 `entry_replay_cohort_contract_v3`로 올린다. `entry_setup_scalping_rollout.AUTO_PROMOTION_SCOPES`의 9개 exact scope를 단일 registry로 읽고, target-date machine bundle에 실제 존재하는 scope·role/hash를 함께 고정한다. 각 scope는 `LIVE_AUXILIARY|OBSERVE_ONLY|INACTIVE_EXPLICIT` 중 하나를 가져야 한다. `LIVE_AUXILIARY`라도 screenable ENTER가 0이면 Provider를 호출하지 않고 valid-empty terminal로 닫는다. 통합 애프터마켓의 기존 observe-only 권한은 이 census 보완으로 live가 되지 않는다. v1/v2 artifact는 historical read만 허용하고 v3 평가에 표본을 합치지 않는다.

### 21.4 런타임과 동일한 paired replay 입력·prompt 계약

`prepare_detailed_paired_replay_requests`에 Entry 전용 `entry_auxiliary_screen_replay_contract_v1`을 추가한다. 각 request는 다음을 hash로 고정한다.

1. 당시 exact payload와 `entry_setup_evidence_v1`.
2. 당시 기계 `assessment`: action=`ENTER_NOW`, reason, applied thresholds, hierarchy selection, selected child rule, flow/micro observation, policy version과 bundle SHA256.
3. base prompt의 version과 SHA256.
4. `machine_first_pass_veto_v2` addendum의 version과 SHA256.
5. scope별 historical context의 SHA256.
6. strict risk-verdict response schema와 semantic validator version.
7. 최종 합성 prompt의 SHA256과 `candidate_input_sha256`.

공통 composer를 `mechanistic_entry_runtime_policy`에 두고 runtime과 offline replay가 함께 사용한다. 형태는 `compose_auxiliary_prompt(base_prompt, historical_context, hierarchy_role)`이며, 현재 `auxiliary_prompt`는 호환 wrapper로 유지한다. runtime과 replay의 최종 prompt bytes가 다르면 해당 pair를 경제성 비교에서 제외하고 `auxiliary_prompt_composition_mismatch`로 차단한다.

paired arm은 다음처럼 제한한다.

| arm | 구성 | 용도 |
| --- | --- | --- |
| `A0_incumbent_auxiliary` | 해당 parent의 실제 런타임 trace/bundle에 기록된 base prompt + 고정 addendum + 동일 machine context/schema | Control |
| `A1_candidate_auxiliary` | #78이 제안한 등록된 base prompt + **같은** addendum + 동일 machine context/schema | Candidate |
| `L0_legacy_independent_selector` | 기존 AI-only prompt/action | 이력 진단만; A0/A1 paired 분모와 승격 gate에 합치지 않음 |

A0/A1은 parent, provider/model, reasoning, timeout, token cap, 입력, response schema를 같게 하고 base prompt만 바꾼다. retry는 같은 contract 위반을 고치는 bounded schema retry만 허용하며, 한 arm의 transport 실패를 다른 arm의 경제성 0으로 보간하지 않는다. 두 arm 모두 유효 terminal인 pair만 비교 지표에 쓰되, 실패한 arm은 오류율 분모에는 반드시 남긴다.

### 21.5 보조심사 결과 taxonomy

Entry 결과는 AI action이 아니라 `risk_verdict`와 런타임 합성 결과로 판정한다. `PASS|VETO|CAUTION|INSUFFICIENT` 외 값은 schema/semantic 오류다.

| 분류 | 필요 조건 | 경제성 처리 |
| --- | --- | --- |
| `correct_profitable_pass` | 유효 PASS, fresh executable 진입 가능, 비용 후 목표가 adverse보다 먼저 도달 | 기회 보존으로 집계 |
| `dangerous_pass` | 유효 PASS, adverse-first·비용 후 손실·catastrophic/tail 계약 위반 중 하나 | 위험 통과 손실로 집계 |
| `correct_risk_veto` | 유효 VETO, 비경제적/실행불가 또는 adverse-first·비양수 비용 후 outcome | 회피 손실로 집계 |
| `missed_profitable_veto` | 유효 VETO, fill-feasible이며 비용 후 목표-first인 clean-fast 기회 | 놓친 기회손실로 집계 |
| `risk_justified_but_eventually_profitable_veto` | VETO 뒤 최종 수익 가능성이 있으나 목표 전 깊은 역행·긴 횡보 또는 기존 위험 budget 위반 | correct/missed로 강제 합치지 않고 별도 진단 |
| `pass_with_slow_or_ambiguous_outcome` | PASS 뒤 늦은 수익·횡보·동일 bar 선후 불명·right-censored | primary precision에서 제외, 자본점유/불확실 분모 보존 |
| `valid_nonbinary_no_exposure` | CAUTION 또는 INSUFFICIENT | VETO로 세지 않으며 후속 재확인 결과와 별도 결속 |
| `transport_not_evaluated` | timeout/network/provider receipt 실패 | 판정품질이 아닌 호출품질 결손; 경제성 null |
| `schema_semantic_not_evaluated` | parse/schema/fact binding/role 오류 | 판단과 분리; 경제성 null |
| `source_or_lineage_gap` | 비용·BBO·bundle·snapshot·후행 path 결손 | 해당 행 제외와 직접 사유, 0원/0EV 금지 |

`missed_profitable_veto`는 단순 사후 고가가 아니라 동일 route/session의 executable ask→bid, 비용, target/adverse 선후, fill feasibility가 모두 유효해야 한다. `dangerous_pass`도 실제 최종 submit 여부와 무관하게 screen 판단 품질을 평가할 수 있지만, counterfactual과 실제 실현손익을 합산하지 않는다. final guard가 PASS를 차단한 경우 `ai_dangerous_pass_final_guard_saved`를 별도로 세어 AI와 최종 guard의 공을 바꾸지 않는다.

### 21.6 R1·R2 지표와 작은 순익 목적함수

Entry의 기존 `candidate_exposure_count`, `false_drop_rate`, BUY/WAIT/DROP transition을 primary prompt gate에서 제거하고 호환 diagnostic으로만 남긴다. 새 primary 지표는 다음이다.

- `correct_profitable_pass_rate`: 유효·성숙한 수익기회 중 PASS 비율.
- `missed_profitable_veto_rate`: 유효·성숙한 수익기회 중 VETO 비율.
- `dangerous_pass_rate`: 유효 PASS 중 adverse-first/비용 후 손실 비율.
- `correct_risk_veto_rate`: 유효 위험기회 중 VETO 비율.
- `screen_transport_error_rate`와 `screen_schema_semantic_error_rate`: 별도 운영 지표.
- `net_opportunity_preservation_pct`: PASS로 보존한 비용 후 양수 기회값 − VETO/오류로 놓친 비용 후 양수 기회값.
- `net_risk_avoidance_pct`: VETO로 피한 비용 후 손실값 − PASS로 통과시킨 비용 후 손실값.
- `auxiliary_screen_utility_pct`: 위 두 값을 같은 비중첩 opportunity parent에서 합산한 paired A1−A0 차이.
- `fast_net_profit_frequency_per_100_screens`, `median_time_to_net_target_sec`, `capital_occupancy_sec`, p10/worst loss를 별도 보존한다.

작은 수익 목표는 PASS 건수나 veto 정확도 하나를 키우는 것이 아니다. **비용 후 양수인 빠른 기회를 보존하면서 위험한 PASS와 긴 자본점유를 늘리지 않는 것**이다. 수수료·세금·spread/slippage 결손은 null이며 gross 상승률로 대체하지 않는다. `+0.10%`는 사례 label/목표일 뿐 모든 PASS의 보장수익이나 prompt 승격을 위한 단일 절대조건이 아니다.

R2는 scope별·prompt contract별로 누적하고, 날짜·symbol·parent가 겹치지 않는 chronological holdout을 사용한다. KRX/NXT/PREMARKET/통합 route를 합치지 않는다. 결과 수가 0인 scope도 유효 empty 또는 source gap으로 명시하며 다른 scope 표본으로 채우지 않는다.

### 21.7 #78 선택조건과 과도한 gate 정정

#78은 **base prompt만** 고른다. PASS/VETO addendum, machine role, output schema, threshold, provider/model 및 final guard는 최적화 축이 아니다. entry cohort의 `selected_challenger`는 다음을 모두 만족할 때만 바뀐다.

1. A0/A1 exact parent와 prompt-composition hash가 완전히 paired.
2. source-quality-valid·cost-bound·mature outcome만 경제성 분모에 사용.
3. candidate의 `auxiliary_screen_utility_pct > incumbent`.
4. `missed_profitable_veto_rate`가 악화되지 않고 `dangerous_pass_rate`·p10/worst loss가 악화되지 않음.
5. transport/schema 오류율이 incumbent보다 악화되지 않으며 선언 ceiling 이내.
6. 해당 scope의 최소 유효 screen 수·unique symbol·독립 source date와 chronological holdout 충족.

현행 30 trace/10 symbol/2일, candidate exposure5, positive candidate EV·probe EV·EV delta의 동시 gate는 독립 선정자용이다. 구현 시 실제 screenable `ENTER_NOW` 분모의 유입률을 먼저 출력하고 다음처럼 정정한다.

- source/schema 수리와 일일 learning update에는 유효 1행을 허용하되 승격 권한은 주지 않는다.
- bounded candidate의 최소분모는 기존 R3 계약을 역할에 맞게 재사용한 `10 paired screens / 3 symbols / 3 source dates`로 시작한다. 세 날짜 중 마지막 날짜를 holdout으로 분리하고 holdout에 유효 binary screen이 없으면 교체하지 않는다. `20 screens / 5 symbols / 5 source dates`는 강한 근거 상태를 표시하는 진단 floor이지 bounded 적용의 중복 선행 gate가 아니다.
- 단, 자연 유입률상 위 floor의 최대 관측 가능 수가 선언 horizon 안에서 충족 불가능하면 숫자를 자동 하향하지 않고 `structural_population_exhaustion|blocked_missing_evidence`로 재판정한다.
- 모든 scope 동시 통과, 모든 1/3/5/10/20/30/60분 horizon 완비, `candidate EV>0`와 `probe EV>0`의 중복 gate는 요구하지 않는다. primary 180초와 tail/cost 계약을 만족하는 해당 scope만 평가한다.
- 실제 비용, source integrity, exact pairing, no-future-leak, tail 비열화, 오류율 ceiling은 유지한다. 이들은 과도한 조건이 아니라 역할상 필수 안전조건이다.

초기 floor는 코드 상수와 report `policy/observed/pass`에 모두 노출한다. 자연 3거래일 후 유입·censoring을 보고 합리성을 재검토하되, 결과를 좋게 만들기 위한 사후 floor 변경은 금지한다.

### 21.8 21:05 follower와 #80 closure

기존 순서는 유지한다.

`terminal detailed → #82 calibration → #78 optimizer(그날 실행 선택 동결) → provider0 metadata-only rebind → #79 holding manifest → #80 consumer`

wrapper와 batch에는 다음 assertion만 추가한다. 기존 controller가 소비하는 `status=completed_offline_only|hold_*|failed`는 호환 유지하고, Entry 역할은 별도 `entry_evaluation_role=auxiliary_screen`과 `entry_evaluation_status`로 표현한다.

- Entry batch의 각 cohort가 role별로 `completed_auxiliary_screen|hold_no_screenable_machine_enter|blocked_source_contract` 중 하나이며 상위 기존 terminal status와 모순이 없음.
- `machine_enter_screen_required_total = evaluated + terminal error/gap` 보존식 통과.
- 실행 당시 A0/A1 base/addendum/context/input hash와 최종 prompt hash가 detailed report에 존재하고 동일 generation의 #82/#78/#80에 결속.
- `--preserve-entry-batch-selection`은 그날 실제 Provider 실행 candidate를 바꾸지 않음. 새 #78 선택은 다음 source date batch용이다.
- `--refresh-optimizer-binding-only`는 provider 호출0, 판정 row/경제성/오류 taxonomy 불변, optimizer hash만 재결속.
- 이미 terminal인 exact parent·prompt pair는 checkpoint를 재사용하고, 새 source나 candidate hash가 없으면 Provider를 반복 호출하지 않음.
- provider/schema terminal rejection은 성공으로 바꾸지 않고 retry exhaustion 뒤 wrapper가 non-zero로 닫힘.

#80은 `entry_auxiliary_screen_consumer_contract_v1`을 발행하고 다음을 검증한다.

- auxiliary role=`auxiliary_risk_screen_pass_veto_no_promotion`, variant=`machine_first_pass_veto_v2`.
- machine ENTER-only replay, non-entry no-provider census, scope 격리와 분모 보존식.
- optimizer base prompt version/hash와 addendum/context/final prompt hash.
- R1/R2 taxonomy 전수 합계, transport/schema/source gap의 비경제성 분리.
- R3 candidate의 source-only authority와 기존 PREOPEN owner 경로.

한 항목이라도 불일치하면 Entry handoff는 `blocked_auxiliary_screen_contract`; holding/exit의 독립 정상 closure는 보존한다. #80이 prompt registry·env·PID를 직접 변경하지 않는 현재 권한도 유지한다.

### 21.9 실제 런타임 자동적용과 판정 경계

자동화는 새로 만들지 않고 기존 경로를 검증·보완한다.

1. 장후 #78이 검증된 base prompt candidate를 source-only로 고른다.
2. 21:05 follower가 terminal 결과에 #78 hash를 재결속하고 #80이 handoff를 닫는다.
3. 기존 `entry_setup_live_policy` candidate/activation validator가 exact-date PREOPEN 후보를 검증한다.
4. 기존 PREOPEN wrapper가 env/activation을 생성하고, 봇 기동 시 이를 읽는다.
5. `ai_engine_openai`는 기계 `ENTER_NOW`에서만 선택 base + 동일 addendum/context로 호출하고 prompt hash를 trace에 기록한다.

구현 완료 판정은 다음 층을 분리한다.

| 층 | 완료조건 |
| --- | --- |
| 코드/계약 | review finding 0, 회귀 테스트·compile·wrapper syntax·diff check 통과 |
| 장후 자동화 | exact-date #77/#82/#78/#80 동일 generation terminal, provider0 rebind 검증 |
| 다음 장전 | candidate 또는 유효 incumbent carry의 날짜/hash/role 검증과 PREOPEN activation 성공 |
| PID 소비 | 새 PID trace에서 machine-before-provider, ENTER-only 호출, 최종 prompt hash 일치 |
| 자연 품질 | correct/missed VETO, dangerous/correct PASS와 오류 taxonomy에 미분류 0 |
| 경제성 | 비용 후 기회보존·위험회피·빠른 순익 빈도·tail·자본점유가 incumbent 대비 수용 가능 |

코드와 장후 terminal만으로 실제 적용이나 순익 개선을 완료 처리하지 않는다. 반대로 자연 표본 부족을 source/schema 수리 실패로 바꾸지 않는다. 정책 교체가 없더라도 유효 incumbent carry와 직접 사유가 다음 장전에 전달되면 자동화 closure는 가능하다.

### 21.10 구현 순서·변경 파일·검증

| Pass | 변경 위치 | 구현 내용 |
| --- | --- | --- |
| P1 source/schema | `ai_action_outcome_calibration.py`, `ai_decision_quality.py` | ENTER-only screenable manifest, exact machine context, 보존식과 taxonomy 추가 |
| P2 shared composition | `mechanistic_entry_runtime_policy.py`, `ai_engine_openai.py` | runtime/offline 공통 auxiliary prompt composer와 최종 hash 검증. 기존 public wrapper 유지 |
| P3 replay | `entry_setup_paired_replay_batch.py`, `ai_decision_quality.py` | A0/A1 동일 부모 replay, legacy selector 격리, 오류 terminal 분리 |
| P4 selection/consumer | `main_ai_prompt_optimizer.py`, `main_ai_prompt_consumer.py` | screen utility·missed VETO·dangerous PASS gate, auxiliary handoff 검증 |
| P5 automation/verifier | `run_ai_entry_setup_paired_replay_postclose.sh`, `verify_threshold_cycle_postclose_chain.py` | 기존 순서에 terminal/hash/보존식 assertion 추가 |
| P6 docs | `report-based-automation-traceability.md`, `time-based-operations-runbook.md`, 장후 지시문, 실제 실행일 checklist | 새 Entry 평가계약·terminal/owner·receipt를 현행화. 운영 절차가 바뀐 문서만 수정하고 같은 stable owner 중복 생성 금지 |

최소 테스트 범위는 다음이다.

- `test_ai_decision_quality.py`: machine context/future label 분리, A0/A1 prompt bytes/hash, ENTER-only materialization, transport/schema terminal.
- `test_ai_action_outcome_calibration.py`: 네 핵심 분류와 ambiguity/source gap, exact attempt dedup, scope별 보존식, final-guard saved case.
- `test_entry_setup_paired_replay_batch.py`: non-entry provider0, terminal empty, frozen selection, metadata-only rebind와 checkpoint 멱등성.
- `test_main_ai_prompt_optimizer.py`: base-only change, auxiliary gate, missed VETO/dangerous PASS/tail/오류율, 9-scope v3 census와 다른 scope 표본 차용 금지.
- `test_main_ai_prompt_consumer.py`: role/addendum/context/prompt hash·generation 불일치 fail-closed, holding 독립 closure.
- `test_mechanistic_entry_runtime_policy.py`, `test_entry_setup_live_policy.py`, `test_ai_engine_openai_transport.py`: runtime/offline composer parity, ENTER-only provider, PASS/VETO/CAUTION/error 동작 불변.
- wrapper `bash -n`과 follower/controller/verifier contract test, 변경 Python compile, scoped lint/format 및 `git diff --check`.

필수 synthetic 반례는 correct PASS, missed VETO, correct VETO, dangerous PASS, 깊은 역행 뒤 수익, 긴 횡보 뒤 수익, final guard saved, CAUTION/INSUFFICIENT, timeout, schema/semantic 오류, 기계 BLOCK/RECHECK 미호출, bundle/snapshot/route 충돌, 비용 결손, 동일 parent 중복, 다음날 candidate 교체·incumbent carry다. Provider unit test는 fake runner만 사용한다.

구현 뒤 영향 재생성은 최초 변경 producer부터 #77→#82→#78→batch metadata rebind→#80→verifier까지만 수행한다. 장후 wrapper가 이미 진행 중이면 그 snapshot을 교체하지 않는다. 실 Provider replay는 새 exact ENTER parent와 검증된 candidate hash가 있고 기존 budget/checkpoint가 허용할 때만 21:05 owner로 실행한다. bot 재기동, 수동 env/lock, threshold/order/수량 변경은 이 계획의 권한이 아니다.

현재 source-lineage 선행은 [9/14 체크리스트](../checklists/2026-09-14-stage2-todo-checklist.md)의 `MainAIQualitySourceGapMainAIAllocatorSubmittedTraceCustodyRepair0914`, 구현 판정·지시는 `CodeImprovementWorkorderReview0914`와 대사한다. 전자는 제출 trace/custody 원천 수리 owner이지 이번 prompt 평가 구현 전체의 대체 owner가 아니다. 구현 지시 시 실제 OPEN owner가 달라졌으면 현행 체크리스트를 다시 읽고 같은 owner를 이관하며, 이 계획만으로 미래 작업이나 성공 receipt를 생성하지 않는다.

예상 효과는 AI가 이미 기계가 고른 타점을 다시 독립 선정하는 것처럼 평가되어 생기는 잘못된 최적화를 제거하고, **위험한 ENTER를 막는 능력과 비용 후 작은 수익기회를 과도하게 VETO하지 않는 능력**을 같은 모집단에서 직접 비교하는 것이다. 효과 크기, 실제 제출 증가, 비용 후 순익 개선은 자연 적용 후 별도 acceptance이며 이 계획에서 추정하지 않는다.

## 22. 보조심사 전용 축약형 직접 전환과 장후작업 변경계획

작성 기준: `2026-09-14 KST`. 사용자 결정은 **대조군 없이 축약형으로 직접 전환하는 구현계획**이며 장후작업 변경도 포함한다. 이번 실행은 이 문서의 계획·리뷰·print-only 검증만 수행한다. 코드 구현, Provider 호출, 정책 발행, 커밋/푸시, 배포·기동은 수행하지 않는다. 과거 다른 실행의 재기동 승인을 이번 계획 수립에 포괄 승계하지 않는다.

### 22.1 확정 방향과 기존 계획 대체 범위

목표 계약은 `기계 ENTER_NOW → 축약형 AI 보조심사 → 기존 합성기 → 최종 실행 guard`다. 기계 타점을 다시 독립 선정시키거나 AI를 무조건 동의하는 장치로 만들지 않는다. **현재 타점의 지지·반대 증거를 함께 읽어 작은 비용 후 수익기회를 보존하면서 실질적인 위험을 거부**하는 역할로 한정한다.

| 기존 제안/동작 | 이번 구현 기준 |
| --- | --- |
| balanced base + PASS/VETO addendum + hierarchy 예외 누적 | 단일 English ASCII 보조심사 prompt와 명시적 역할 계약 |
| 전체형 A0와 축약형 A1의 Provider paired 비교 | 최초 전환에서 실행하지 않음. 단일 축약형 계약의 구조·의미·경로 검증으로 전환 |
| A1>A0, paired 10건/3종목/3일 등 §21.7 gate | 최초 전환에서 제거. 없는 Control을 만들거나 비교 통과로 표시하지 않음 |
| 기존 base optimizer가 과거 V2.14/15를 다시 선택 | compact 역할/version allowlist 안에서만 소비. legacy base 재유입 차단 |
| 경제성 미관측이면 전체형 유지 | 검증된 compact 정책으로 전환·carry하고 자연 경제성은 별도 OPEN |
| 문서의 9-scope 예시를 새 실전 승인으로 사용 | 실제 적용 시 기존 target-date 승인 registry와 bundle scope를 대사. 현재 승인 scope만 전환 |

대조군을 사용하지 않는 것은 테스트·리뷰를 생략하는 뜻이 아니다. **새 prompt를 기존 출력·권한 계약에 결속하는 검증은 필수**, 과거 prompt 대비 우수성 증명은 선행조건이 아니다. 동일 응답의 validator/composer 회귀검사는 A/B 모델 비교가 아니며 계속 수행한다. 미래 별도 prompt 실험의 대조군 운영은 이번 전환의 필수 후속으로 생성하지 않는다.

### 22.2 코드에서 확인한 변경 지점

- `ai_prompt_contracts.py`의 balanced 본문은 legacy READY/WAIT_CONFIRMATION와 bounded-risk VETO 제한을 갖고, `mechanistic_entry_runtime_policy.auxiliary_prompt`는 이를 뒤의 AI_ADDENDUM/hierarchy 지시로 정정한다. 단일 계약으로 통합할 이유는 문자 수뿐 아니라 상충하는 규칙 우선순위를 제거하는 데 있다.
- 현재 9/14 저장 bundle의 scope별 시스템 문자열은 약 5,900~6,800자다. 이는 당시 파일 측정치이며 토큰 수·현재 PID 실제 전송량·전체 user payload 크기의 증거는 아니다. 시스템 지시문 길이, user payload 길이, response schema 길이를 각각 측정한다.
- `ai_engine_openai._resolve_scalping_prompt`, risk-response adapter의 version별 evidence/composer 분기, schema 선택, 최종 machine-first 조합을 함께 바꿔야 한다. 새 문자열만 교체하면 `entry_setup_prompt_evidence_generation_mismatch` 또는 legacy fallback이 발생할 수 있다.
- `mechanistic_entry_runtime_policy.validate`는 AI_VERSION·variant·scope별 prompt 재계산 결과를 엄격히 확인한다. 상수만 바꾸면 기존 정상 bundle까지 invalid가 되므로 버전별 reader와 명시적 successor 발행이 필요하다.
- `entry_setup_live_policy`의 `validated_optimized_base_prompt` 경로와 `ai_engine_openai`의 addendum 재조합도 함께 전환해야 한다. 초기 bundle만 축약해도 optimizer 경로가 전체형을 복원하면 완료가 아니다.
- `ai_decision_quality`의 schema-correction 지시도 legacy bounded-risk VETO 제한을 갖는다. 첫 호출과 correction/retry가 서로 다른 역할을 지시하지 않도록 같은 compact 계약을 사용한다.

### 22.3 새 prompt·입력·응답 계약

제안 version은 `entry_machine_auxiliary_compact_v1`, role은 기존 `auxiliary_risk_screen_pass_veto_no_promotion` 유지, variant는 `machine_first_compact_pass_veto_v1`이다. 이 이름은 **계획상 새 등록값**이지 이미 지원되는 runtime 값이 아니다. prompt/evidence/schema/composer/validator 조합을 하나의 명시적 registry entry로 관리한다. 기존 V2.15.2 이름에 새 bytes를 덮어씌우지 않는다.

아래를 단일 시스템 prompt 초안으로 삼고, 구현 시 실제 validator와 반례 테스트로 문구를 확정한다. 약 250~400 English words는 설계 예산일 뿐 통과 숫자·품질 보증이 아니다. 안전·근거 의미를 삭제해 글자 수를 맞추지 않는다.

```text
You are the binding risk reviewer of a machine-selected entry point.
The validated machine assessment owns setup selection and entry timing.
Review its current supporting and adverse evidence; do not reselect stocks,
invent another setup, or promote machine RECHECK/BLOCK to entry.

Seek repeated small cost-adjusted profits, not a PASS quota, perfect certainty,
or permanent abstention. Do not invent returns, costs, facts, or future data.
Use the exact supplied fact ledger and machine assessment. Treat correlated
facts as related evidence, not independent votes. Missing optional context is
neither support nor adverse evidence.

PASS preserves the selected point for final guards when current support
adequately addresses its bound risks. Cite valid setup/trigger support and
the required adverse facts. A validated hierarchy trigger can resolve legacy
WAIT_CONFIRMATION; do not demand READY again or another pullback by default.

VETO rejects this point, not the symbol permanently. Cite exact adverse facts
and matching risk codes. Bound liquidity, tape, or reward-risk weakness may
justify VETO after weighing available support, but a bounded risk alone is
not automatically a veto. Missing confirmation alone does not justify VETO.
Hard invalidation and unusable required source retain their blocking roles.

CAUTION means a specific unresolved issue merits the existing bounded recheck.
INSUFFICIENT means required source evidence is unusable. Neither permits entry.
Never infer exposure permission from missing, invalid, or failed responses.

Return only the supplied risk-adjudication JSON schema. Copy fact IDs and risk
codes exactly from their allowed bindings. Confidence is an integer 0..100,
not a trading threshold. You cannot change price, quantity, policy thresholds,
provider, or safety. Fresh quote, cost, account, order, cooldown, broker, and
hard-safety guards remain authoritative after PASS.
```

입력은 다음처럼 분리한다.

| 입력 | 설계 |
| --- | --- |
| 현재 기계평가 | exact action/reason, group/child, 실효 threshold, policy hash, scope와 평가시각을 유지 |
| 근거 ledger | setup/trigger, 지지·반대 fact와 risk binding, micro window/route/epoch/completeness 및 필요한 가격·비용·시각을 유지 |
| 현행 시장 context | 현재 live payload를 원칙적으로 유지하고 중복 지시와 구 role 문장만 제거. 시계열·숫자 축약은 별도 축으로 두고 이번에 동시에 최적화하지 않음 |
| 과거 정책·연구 context | 성과, holdout 결과와 연구 이력은 감사 metadata에 유지하고 전송 prompt에서는 제외. 현재 판정에 필요한 유효 정책값·scope는 기계평가에 한 번만 투영 |
| 후행 outcome | 당시 모델 입력에는 절대 넣지 않고 응답 terminal 뒤 평가 join에만 사용 |

출력은 기존 `entry_setup_risk_adjudication_v1`의 `risk_verdict`, `risk_codes`, `supporting_fact_ids`, `contradicting_fact_ids`, `confidence`와 `schema`를 유지한다. enum·fact ID별 허용 위치·개수 상한은 기존 schema/semantic validator가 소유한다. 단순 `PASS/VETO` 문자열이나 자유 설명으로 바꾸지 않는다. 공통 composer는 시스템 bytes와 input projection/version을 반환하고 live·offline·correction이 같은 계약 registry를 읽는다.

### 22.4 런타임·validator·정책 전환

1. 기존 `src/engine/ai_prompt_contracts.py`에 compact prompt/version을 등록하고, machine 보조심사 owner에만 배정한다. holding/exit·entry_price·legacy 독립 AI 평가에는 적용하지 않는다. 새 engine-root Python 모듈이나 collector를 만들지 않는다.
2. `validate_mechanistic_risk_screen`과 `compose_mechanistic_primary_decision`을 의미상 단일 owner로 사용한다. legacy 규칙을 전체적으로 완화하지 않는다. ENTER+유효 PASS만 기존 노출 가능 경로를 보존하고, VETO는 해당 타점 DROP, CAUTION/INSUFFICIENT/오류는 현재 비노출 재확인을 유지한다. machine RECHECK/BLOCK은 Provider 미호출이다.
3. 현재 합성 결과의 `WAIT + entry_probe_intent=true`가 유효 진입 전달인 호환 경로를 보존한다. 문자열 WAIT만 보고 실패/미참여로 집계하거나 실제 주문수량을 바꾸지 않는다.
4. 새 version을 prompt resolver, response-schema selector, evidence builder, semantic adapter, retry/correction, cache/checkpoint identity에 끝까지 등록한다. machine assessment와 setup ledger의 같은 parent/scope/policy 결속을 검증한다. hierarchy PASS는 검증된 group trigger와 필요한 micro fact가 있을 때만 기존 예외를 사용한다.
5. bundle의 새 AI 계약은 version-dispatch reader로 지원한다. migration 준비 중 old bundle은 old 의미로 읽되 compact로 재라벨링하지 않는다. successor는 원본 path/hash를 보존하고 같은 machine threshold/hierarchy/scope/cost·order guard를 carry한 채 AI 계약만 바꾼다. bundle 전체 hash 변경과 기계정책 자체 불변 hash를 따로 기록한다.
6. 전환 manifest에 실제 effective 시각·target date·source parent·scope·새 prompt/schema/input-projection/validator hash와 rollback predecessor를 기록한다. 오늘 날짜를 문서 날짜로 고정하거나 과거 source를 새 날짜로 가장하지 않는다. 날짜 규칙과 기존 publisher 검증을 우회하지 않는다.
7. resolver는 compact 전환 scope에서 compact-compatible 정책만 선택한다. 구형 optimizer candidate는 명시적 `incompatible_legacy_prompt_role`로 제외하고 **유효 compact incumbent carry**로 닫는다. 구형 base+addendum 또는 독립 selector로 조용히 fallback하지 않는다. 유효 compact 정책 자체가 없으면 기존 비노출/error 계약으로 닫고 owner에 명시한다.
8. hash는 기존 필드별 canonical serializer/`digest` 계약을 유지한다. raw UTF-8 bytes SHA256을 새로 추가할 경우 별도 이름·algorithm을 사용하며 기존 JSON-string digest와 섞지 않는다. 선택 정책→실제 전송 prompt→저장 request/response가 같은 hash인지 확인한다.

### 22.5 장후작업별 필수 변경

설치된 producer 실행 순서와 단일 owner를 유지한다. 다음 표는 **변경 영향 지도이지 새로운 실행 순서가 아니다**. 정확한 source date와 실행 snapshot은 실제 구현·재생성 때 다시 고정한다.

| 작업 | 수정 내용 | 직접 수용조건 |
| --- | --- | --- |
| #11 preflight / #74 final audit | compact role/version·prompt/schema/input hash 허용 계약 추가. 기계평가 전수, ENTER 심사대상, 실제 AI 호출을 별도 분모로 감사 | 미호출 RECHECK/BLOCK은 정상, ENTER 뒤 호출/응답 결손은 직접 사유. unknown compact를 통째 정상/legacy로 정규화하지 않음 |
| #76 materialization | 기존 machine case/trace를 전수 소비하고 compact 요청과 원 응답의 exact parent/hash를 유지 | machine action·선정 이유·정책·micro 창 결속, old/new generation 분리, 새 collector 없음 |
| #77 R0 | ENTER-only 단일계약 평가 manifest 발행 | required/valid/error/pending/gap 보존식. AI-only 과거 자료나 사후 machine 추정은 별도 diagnostic |
| #77 R1/R2 | 실제 compact 응답과 성숙 outcome을 join해 scope별 품질·운영·경제성을 집계 | correct/missed VETO, correct/dangerous PASS, CAUTION/INSUFFICIENT, 오류/미성숙/비용 결손을 상호배타적으로 대사 |
| #77 R3 | compact 계약·source·품질 finding과 개선 필요사항을 source-only manifest에 전달 | 최초 전환을 paired 승격 후보로 만들지 않음. 정상 부분행 학습은 유지하고 live 권한은 만들지 않음 |
| #82 calibration | 단일 compact screen 품질과 실제 submit/fill/terminal을 별도 평가 | 기계 전체·AI 심사·실호출·경제성 eligible 분모 불혼합. 품질 미관측과 수집 결함 분리 |
| #78 optimizer | compact를 직접 전환 incumbent로 인식; legacy prompt 후보 및 old BUY/WAIT/DROP gate의 재유입 차단 | 최초 채택 사유는 검증된 contract migration, `paired_improvement_pass` 아님. 후보 없으면 compact carry; holding 최적화는 기존 계약 유지 |
| 21:05 runner | 기존 batch에 `evaluation_mode=single_contract_auxiliary`를 명시해 compact 단일 평가로 실행 | old/new A0/A1 호출 없음. 동일 exact request terminal 재사용, mode별 완료 검증, empty/gap/error 분리 |
| #79 holding manifest | Entry 관련 변경 hash를 필요한 metadata에서만 참조 | holding Provider/정책/경제성의 기존 독립 의미 유지 |
| #80 consumer | compact role·generation·단일평가 mode·source/input/output hash·분모를 검증 | nonexistent pair를 요구하지 않으며 구형 terminal을 compact terminal로 인정하지 않음 |
| PREOPEN publisher/loader | 전환 이후 compact 정책 승계와 소비를 기존 자동경로에 연결 | exact date/scope/hash·권한 유효, legacy 자동복귀 없음, 적용/현재 PID 증거 분리 |
| verifier→tower→checklist→strict/controller | 변경된 평가 mode와 fresh summary source를 대사 | 비교 미실시를 FAIL로 만들지 않고, 실제 필수 source/hash 오류는 차단. 원 wrapper terminal과 갱신 시각 분리 |

새 cron·timer·AI endpoint·정기 collector는 추가하지 않는다. `deploy/run_ai_entry_setup_paired_replay_postclose.sh`의 파일명은 호환상 유지할 수 있으나 JSON/report에는 단일평가 mode를 명시한다. A0/A1을 동일 응답으로 복제하거나 `paired_count=1`을 합성해서 구 consumer를 통과시키지 않는다. 동작 변경 시 traceability·장후 지시문·실제 checklist를 함께 갱신하고, 운영 runbook 수정은 그 구현 요청의 명시 범위를 확인한다.

### 22.6 단일평가·오류·경제성의 정확한 분모

기존 §21.3의 의미를 보존하되 malformed/unknown machine 행도 누락하지 않도록 다음을 출력한다.

```text
raw_machine_rows = unique_machine_cases + duplicate_rows + quarantined_rows
unique_machine_cases = machine_nonentry + machine_enter_screen_required
machine_nonentry = machine_recheck + machine_block
machine_enter_screen_required = valid_screen + transport_terminal_error
  + schema_semantic_terminal_error + local_unavailable + pending + source_gap
valid_screen = pass + veto + caution + insufficient
valid_screen = economic_eligible + pending_maturity + excluded_outcome_or_cost
```

각 행의 terminal 분류는 서로 배타적이며 retries는 attempt provenance로 별도 센다. transport 오류 후 정상 응답으로 복구된 요청은 valid_screen 1건과 recovered-warning으로 기록하며 최종 실패에 중복하지 않는다. unresolved pending은 deadline과 owner를 가진다. source gap/unknown action은 quarantine 원천 위치·사유로 추적하고 분모 밖으로 소거하지 않는다.

- 실제 compact 자연 응답은 이미 호출한 증거를 재사용한다. 같은 prompt/input/schema의 유효 terminal을 얻기 위해 밤에 다시 Provider를 부르지 않는다. live cache receipt도 원 response/hash가 검증될 때만 valid_screen이며 `provider_called=false`는 별도 유지한다.
- 단일 offline replay가 필요한 미평가 exact ENTER는 기존 source-quality·budget·bounded resume 계약에서만 실행한다. old prompt response를 compact response로 바꾸지 않으며, old source 재평가가 허용돼 실행된 경우에도 `offline_compact_replay`이지 당일 실제 compact 호출/적용은 아니다. 무변경 과거 원천의 반복 호출은 금지한다.
- 21:05 순서 `terminal detailed → #82 → #78 frozen binding → provider0 metadata rebind → #79 → #80`를 유지한다. mode별 consumer가 실제 결과를 확인한 뒤 terminal을 발행한다. 비교 불필요는 valid-empty이며 mandatory source invalid·실제 terminal 실행 오류를 성공으로 바꾸는 예외가 아니다.
- #78의 frozen selection은 그 run이 사용한 compact version/hash를 고정한다. metadata-only rebind는 판정 row·경제성·원 응답·mode를 변경하지 않으며 Provider 0이다.
- outcome 분류는 먼저 source/maturity/cost·선후 불명을 제외한 뒤 기존 owner의 executable/target/adverse 계약으로 수행한다. 위험이 먼저였고 나중에 수익이 난 사례를 동시에 correct와 missed VETO로 세지 않는다. 원래 VETO 근거의 당시 타당성과 사후 outcome label도 별도로 남긴다.
- primary는 source-quality-valid·성숙한 단일 contract cohort의 비용 후 opportunity 보존/손실, dangerous PASS·missed VETO, 빠른 순익 빈도·tail·자본점유다. 분자/분모·비용·exit·관찰창을 명시하고 CF와 실제 순익을 합산하지 않는다. 실패/비용 결손은 null, CAUTION/INSUFFICIENT는 VETO가 아니다.
- 비교 arm이 없으므로 §21.6의 `A1−A0 utility`, superiority, non-inferiority는 **not_applicable_no_control**이다. 전환 전후 관측 변화는 날짜/시장/기계정책 차이를 명시한 기술통계일 뿐 인과적 개선량이 아니다. 작은 순익 목표를 이유로 PASS quota·양수 결과만의 집계·고정 수익 보장을 추가하지 않는다.

### 22.7 직접 전환 gate와 자동화 경계

**최초 전환의 필수 gate**는 (a) prompt/registry/schema/validator 정합성, (b) fake 응답 기반 결정론적 회귀검사, (c) source/hash/날짜/scope와 권한 확인, (d) 배포본 코드와 정책 호환·rollback 준비다. 기존 전체형 replay, 비교 우위, 추가 3/5/10/20일 관측, 양수 EV·실체결·새 표본 floor는 최초 전환의 선행조건이 아니다.

후속 구현이 지시되면 검증된 compact를 기존 승인 scope에 직접 전환하는 release를 준비한다. 실제 배포·기동은 그 실행의 명시 권한과 운영계약을 확인한 뒤 수행한다. 이번 계획 요청만으로 실행하지 않는다. 검증/권한이 닫힌 뒤에도 대조군 수집을 이유로 추가 canary·다음 PREOPEN 대기를 발명하지 않는다. 다만 실제 loader가 기동 시에만 정책을 읽는다면 파일 수정/타이머 start를 적용으로 주장하지 않고 승인된 전환·기동 경계를 따른다.

전환 이후 일별 승계는 **기존 publisher→exact-date PREOPEN/dated loader**를 재사용한다. 기계 threshold/hierarchy의 기존 경제성·승격 gate는 이번 prompt 전환과 별개로 유지한다. #78에 compact-compatible 신규 후보가 없어도 유효 compact incumbent가 계속 전달되어야 하며, 미지원 candidate로 nightly rollback하거나 무표본 때문에 전체형을 재활성화하지 않는다. 9/14 후속 사용자 권한에 따라 #82는 exact compact version의 source-quality 유효 ENTER 20건, semantic 미분류 0건과 missed-VETO/dangerous-PASS 차이 `max(2, 분모의 10%)`를 충족할 때만 사전 등록된 opportunity-preserving/risk-specific variant를 자동 선정한다. publisher는 incumbent/version/count 보존식을 재검증해 다음 거래일 bundle에 적용한다. 자유형 prompt 생성과 registry 밖 변경은 자동권한이 아니다.

rollback은 배포/정책/validator 불일치·출력계약 장애·기존 safety 사고 대응 계약에 따라 **검증된 이전 release+policy 묶음**으로 수행한다. old generation을 compact로 표기하거나 reader 내부 silent fallback으로 우회하지 않는다. 무표본·하루 낮은 수익만으로 자동 전체형 복귀를 만들지 않는다. 경제성은 미관측으로 남길 수 있지만 필수 입력/권한 오류는 미관측으로 숨길 수 없다.

### 22.8 첨부 자연 관측의 사용 경계

첨부 계획은 `2,960`개 기계 관측, `ENTER_NOW 30`, AI 호출 `27` 중 semantic invalid `12`, micro complete/gap `10/20`, `common/no_matching_valid_child 2,960`, AI 중앙 지연 약 `2.9초`, AI 뒤 제출까지 `40~49초`, 구 release와 PID/commit 경계를 제시한다. 이 값은 **첨부 작성 시점의 비종결 자연 관측과 문제 재현 후보**다. 이 문서가 현재 runtime receipt로 재인증하지 않는다.

구현 시작 시 다음처럼 취급한다.

- source timestamp, release commit, bundle SHA256, PID start time으로 원 관측 generation을 고정한다. 이후 append·재기동·release 전환 표본과 합치지 않는다.
- 숫자는 P0 fixture 선정과 재현 대상이며 새 코드의 결함 수나 현재 PID 상태로 고정하지 않는다. 현행 release에서 이미 해소됐으면 생산코드를 다시 고치지 않고 회귀 테스트와 원 generation disposition만 추가한다.
- 자연 표본이 없으면 exact synthetic fixture로 contract만 검증한다. 이를 자연 source 회복, semantic 오류율 개선, 정책 선택 또는 순익 개선으로 보고하지 않는다.
- 기존 [#76·#82 / #11·#74 자연 원천 전수 소비 계획](./main-ai-natural-source-consumption-verification-plan-2026-09-14.md)은 raw source와 분모 보존의 직접 설계 근거로 재사용한다. 이번 §22는 그 원천을 compact AI 전환·비용·타점·장후 정책까지 연결하는 상위 실행계획이며 새 collector를 만들지 않는다.

### 22.9 통합 목표 체인과 두 개의 독립 변경축

```text
exact 기계판정
→ compact AI PASS/VETO/CAUTION/INSUFFICIENT
→ 기존 최종 제출 guard
→ submit/broker/fill terminal
→ 30/60/180/300초 primary·1/3/5/10/20/30/60분 diagnostic outcome
→ exact round-trip 비용 결속
→ (A) compact AI 자연 품질 귀속
→ (B) 공통/그룹/종목/micro 기계 challenger 평가
→ 다음 거래일 compact incumbent + machine challenger 또는 carry bundle
→ 07:35 PREOPEN 검증
→ 07:55 이후 PID load/first-use 확인
```

두 변경축의 승인조건을 합치지 않는다.

| 축 | 최초 변경 | 필요한 gate |
| --- | --- | --- |
| A. AI prompt contract migration | 전체형+부록을 compact 단일계약으로 직접 교체 | schema/semantic/composer/source/hash/scope/권한, 결정론적 반례, release-policy 호환과 rollback. 구 prompt 대조군·EV 우위·새 자연 표본은 선행조건 아님 |
| B. 기계 판정 threshold/hierarchy | 기존 bounded 공통·그룹·종목·micro challenger만 선택적으로 갱신 | exact 비용, no-future-leak, 같은 scope, chronological holdout, incumbent 대비 비용 후 EV 개선과 해당 family의 `>=+0.10%`, tail/깊은 역행 비열화 금지 |

다음 장전 bundle에는 항상 `compact incumbent + 검증된 machine challenger` 또는 `compact incumbent + machine incumbent carry와 직접 사유` 중 하나가 있어야 한다. challenger·child·자연 AI 호출이 0이라는 이유로 정책 파일이나 compact AI 계약이 사라지면 자동화 결함이다. 유효 incumbent 자체가 손상되거나 권한·hash가 맞지 않을 때만 fail-closed로 정책 발행/적용 실패를 명시한다.

### 22.10 P0 — 실행 generation·release 재현

1. 첨부 관측의 15:28 전후를 실제 artifact의 release commit, bundle SHA256, PID/start time, capture/trace timestamp로 다시 분리한다. `d89b4749`, PID `611623`은 첨부 provenance 주장으로만 시작하며 현재 상태를 다시 읽는다.
2. action mismatch 3건, semantic invalid 사례, 비용 미결속, micro gap과 제출 지연 사례를 각각 immutable fixture manifest로 고정한다. 원본 파일은 수정하지 않는다.
3. 현행 selected release에서 같은 defect가 재현되는지 먼저 검사한다. 이미 수정된 항목은 regression test만 추가하고 생산코드 변경 목록에서 제거한다.
4. active main/postclose/21:05 wrapper가 있으면 그 run의 immutable snapshot을 바꾸지 않는다. 해당 generation terminal 뒤 검증된 새 release를 적용 대상으로 삼는다.

수용조건은 `old_generation + current_generation + unresolved_or_unattributed = captured_scope_total`, generation 미분류 0, 현재 코드에서 재현되지 않는 구 결함의 중복 구현 0이다.

### 22.11 P1 — exact attempt·자연 원천·사례표

기존 `ai_decision_trace.py`, `ai_decision_quality.py`, `ai_action_outcome_calibration.py`, #11/#74 `observation_source_quality_audit` 안에서 보완한다. identity는 다음 결합을 우선한다.

```text
source_date + evaluation_attempt_id + snapshot_id
+ machine_observation_sha256 + stock_code
+ effective_venue + session_bucket + machine_bundle_sha256
```

- `evaluation_attempt_id`가 없는 이전 generation은 `snapshot_id` fallback을 `diagnostic_fallback_only`로 표시하며 원 attempt로 재라벨링하거나 policy learning에 사용하지 않는다.
- scanner promotion ID가 실제 frozen input에 있으면 보존한다. promotion 집합 hash나 symbol/근접시각으로 현재 promotion ID를 발명하지 않는다.
- machine/AI join은 exact attempt→snapshot→action→bundle→scope 순서로 검증한다. 허용 120초 창은 보조 무결성 검사일 뿐 identity가 아니다.
- 실패 사유는 `trace_action_missing`, `action_mismatch`, `duplicate_snapshot_conflict`, `bundle_mismatch`, `join_window_exceeded`, `screen_trace_missing`, `unsupported_scope`, `other_explicit_exclusion`으로 나눈다.
- `diagnostic_case_table`은 모든 gross 경로와 source gap을, `economic_case_table`은 exact 비용과 executable ask→bid path가 유효한 행만 가진다. 최근 200행 sample과 full population count/content digest를 별도 저장한다.

보존식은 §22.6과 자연 원천 계획의 machine/AI/provider 3분모를 사용한다. `captured_total = exact_joined + action_mismatch + identity_gap + unsupported_scope + other_explicit_exclusion`, `unclassified=0`을 전체·scope별로 닫는다. 분석 artifact의 `actual_order_submitted=false`와 원 lifecycle의 `observed_actual_order_submitted`도 다른 필드로 유지한다.

### 22.12 P2 — exact 비용 계약 결속

장중 observation에는 당시 알 수 있었던 executable ask/bid, spread, venue/session, 상품구분, 실제 주문가격·수량, 기록된 friction/slippage 입력과 source timestamp/hash만 보존한다. 미래 장후 비용이나 사후 outcome을 prompt·machine input으로 역류시키지 않는다.

장후에는 기존 `micro_reversion_economic_reference`와 `_hierarchy_cost_profiles()`→`_hierarchy_cost_contract()` owner를 사용하여 매수·매도 수수료, 세금, 검증된 slippage/uncertainty, venue/product/date/hash를 결속한다. 유효 행은 `entry_round_trip_cost_v1`과 `cost_contract_sha256`을 사례표에 가진다.

`full_round_trip_cost_missing`은 최소 다음으로 분해한다.

- `cost_producer_not_terminal`
- `venue_or_product_coverage_missing`
- `cost_source_hash_mismatch`
- `cost_date_not_mature`
- `actual_cost_unavailable`
- `friction_only_full_cost_missing`
- `cost_contract_invalid_or_duplicate_application`

half-spread·gross MFE·다른 venue profile을 전체 비용으로 승격하거나 결손을 0으로 채우지 않는다. 같은 비용을 path label과 aggregation에서 두 번 차감하지 않는다. 비용 결손 행은 diagnostic table과 결손 분모에는 남고 machine challenger/AI 경제성 분모에서는 제외된다. 자연 source loader 0행이 비용 때문이라는 첨부 가설은 이 reason별 census와 source hash로 재현돼야 확정한다.

### 22.13 P3 — outcome·진입 타점 분류

새 labeler를 만들지 않고 `ai_decision_quality.mature_outcome_labels()`와 기존 entry path 계약을 재사용한다. 사례표에는 first-watch/기계/AI/submit-revalidation/order/broker/fill 시각과 가격, 30/60/180/300초 primary-compatible path, 1/3/5/10/20/30/60분 diagnostic MFE/MAE/end, 비용 후 `+0.10%` 최초 도달, 목표 전 MAE·underwater/횡보, target/adverse first-hit, route/source completeness를 결속한다.

| 타점 분류 | 계약 |
| --- | --- |
| `GOOD_ENTRY` | 180초 primary에서 executable 비용 후 target-first이고 목표 전 역행·자본점유가 frozen 유형 한도 이내 |
| `LATE_ENTRY` | 최종 수익 가능성과 별개로 target 전 깊은 역행·긴 횡보·unreset extension 또는 과도한 first-watch 경과가 있음 |
| `MISSED_ENTRY` | machine BLOCK/RECHECK 또는 AI VETO 뒤 동일 scope의 fill-feasible 비용 후 target-first 기회 |
| `CORRECT_BLOCK` | 같은 고정 exit에서 비용 후 비경제적·adverse-first 또는 유효 hard/structural block |
| `CENSORED_OR_SOURCE_GAP` | maturity, endpoint, 비용, route 또는 BBO가 불완전 |
| `AMBIGUOUS_SAME_BAR` | target/adverse 선후 확정 불가 |

AI 평가에서는 이를 §22.6의 correct/missed VETO, correct/dangerous PASS, CAUTION/INSUFFICIENT/error taxonomy로 투영한다. 위험이 먼저였고 나중에 수익이 난 행은 `risk_justified_but_eventually_profitable`로 분리한다. 모든 horizon 완비를 요구하지 않고 180초 primary가 유효하면 평가하며, 나머지는 tail·자본점유 진단이다. 실제 fill/PnL과 CF ask→bid는 절대 합산하지 않는다.

### 22.14 P4 — compact prompt·semantic invalid 직접 전환

§22.3 초안을 기존 prompt/schema registry에 `entry_machine_auxiliary_compact_v1`으로 등록하고 다음 순서로 전환한다.

1. 허용 supporting/adverse fact ID와 `risk_fact_bindings`를 입력 projection에 명시하고, 기계 action/reason/group/child/effective threshold/policy/micro receipt를 정확히 한 번 포함한다.
2. 과거 연구성과·holdout 설명·중복 safety 문구는 runtime metadata에 보존하되 모델 입력에서 제거한다. 현재 판정에 필요한 effective policy 값만 machine assessment에 투영한다.
3. first call, correction/retry, offline materialization, live runtime이 같은 compact composer와 output schema를 사용하게 한다. 구 balanced base나 AI_ADDENDUM을 뒤에 다시 붙이지 않는다.
4. 모델이 입력에 없는 fact를 만들거나 risk code만 반환하면 계속 fail-closed한다. deterministic normalization은 frozen input에 실제 존재하는 ID의 공백/대소문자 등 의미 불변 정규화에만 허용하고 원 response와 repair code를 모두 보존한다.
5. `response_invalid` 원문의 PASS를 authoritative PASS에 넣지 않는다. invalid·CAUTION·INSUFFICIENT는 해당 타점 무노출 RECHECK, 유효 VETO는 해당 타점 DROP, 유효 PASS만 기존 final guard로 전달한다. machine BLOCK/RECHECK는 AI가 승격하지 못한다.
6. hierarchy의 validated group trigger가 legacy WAIT_CONFIRMATION을 해소하는 경우는 exact selected rule과 필수 micro/support fact가 있을 때만 PASS 가능하다. optional missing 하나를 blanket VETO로 만들지 않는다.

첨부의 semantic invalid `12/27`은 old-generation 재현 fixture다. 완료조건은 fixture expected semantic result 전수 일치, 새 compact contract 자체가 만든 schema/semantic invalid 0, invented fact acceptance 0, legacy correction/addendum 재유입 0이다. **구 prompt 대비 자연 invalid-rate 비열화나 dangerous/missed 지표 우위는 최초 직접 전환 gate가 아니다.** 전환 후 자연 결과는 운영/경제성 acceptance로 별도 관찰한다.

### 22.15 P5 — micro source·계층 선택

micro source gap을 `exact_route_missing`, `duplicate_route`, `fixed_1s_window_incomplete`, `stale_start_quote`, `epoch_or_sequence_mismatch`, `buy_trade_backing_missing`, `collector_restart_boundary`로 분해한다. 기존 `machine_confirmation_fixed_price_window_v1`과 네 요소 `bid support/rebound + ask depletion velocity + actual BUY trade backing + refill`을 재사용한다.

- selected child는 micro contract가 필수이면 결손 시 RECHECK한다. adverse/invalid micro 뒤 common 부모로 fallback해 ENTER시키지 않는다.
- 아직 child가 없는 유효 common incumbent는 중단하지 않고 `selected_level=common`, `micro_policy_selected=false`, `micro_observed`, `micro_not_used_reason=no_qualified_child|source_gap`을 출력한다.
- 비용/outcome이 유효해진 뒤 기존 calibration이 bounded group/symbol/micro machine challenger를 만든다. `child=0` 또는 첨부의 `common/no_matching_valid_child`는 그 자체로 code defect나 강제 child 생성 근거가 아니다.
- micro raw depth를 사례표에 복제하지 않고 version/status/hash/route/epoch/completeness와 네 derived feature만 투영한다. 결손은 0이나 neutral PASS로 보간하지 않는다.

### 22.16 P6 — 기계 타점 bounded 재평가

AI compact migration과 분리하여 기존 조정 가능축 중 영향이 큰 1~3개만 사전 고정한다. 후보는 first-watch 경과, first-watch 이후 누적상승, trigger/structure confirmation, micro combined condition, spread/fillability, 그룹·종목 bounded residual이다.

첨부의 종목 `256840` 사례쌍 `11:17 BLOCK → 1분 내 낮은 MAE 상승`, `11:52 ENTER_NOW → 이미 +11.55%, 직후 adverse-first`를 generation-bound regression fixture로 둔다. 목표는 이른 기회를 BLOCK 대신 보존/RECHECK하고 소진된 후행 타점을 ENTER로 재선택하지 않는 것이며, 단순 threshold 완화가 아니다.

종목 residual은 기존 `clip(parent + n/(n+20) × fitted_delta, approved_bounds)`를 재사용한다. 공통·그룹·종목 floor를 한 후보에 누적 적용하지 않고, child 표본 부족은 유효 parent를 막지 않는다. challenger 승인에는 §22.9 B축의 exact-cost/holdout/incumbent/EV/tail 계약을 적용한다. 모든 9개 scope가 동시에 통과할 필요는 없으며 통과 scope만 바꾸고 나머지는 incumbent carry한다.

### 22.17 P7 — AI 이후 제출지연 attribution

기존 pipeline event를 같은 attempt에 결속해 다음 구간을 분리한다.

```text
machine decision → AI request → AI response → budget
→ orderbook stability → price AI/resolver → freshness revalidation
→ order send → broker receipt → fill
```

각 accepted machine+AI decision에 최초 병목 하나를 `UPSTREAM_GATE|AI_TRANSPORT|BUDGET|ORDERBOOK_STABILITY|ENTRY_PRICE|FRESHNESS_REVALIDATION|ORDER_SEND|BROKER_RECEIPT|FILL` 중 하나로 부여하고 secondary reason을 별도 보존한다. 반복 attempt/retry를 신규 기회로 세지 않는다. phase별 p50/p95는 같은 scope와 valid timestamps에서만 계산한다.

보완 범위는 timestamp/lineage와 입증된 중복 계산 제거다. stale/DANGER, broker/account/order, quantity/cap/cooldown, price freshness를 완화하지 않는다. 첨부의 AI 약 2.9초·submit 40~49초는 재현할 가설이며 exact phase가 닫힌 뒤에만 원인을 확정한다. prompt 축약으로 줄어든 system/input token과 AI latency는 별도 측정하고 전체 submit 지연 감소를 자동 귀속하지 않는다.

### 22.18 P8 — 장후 source·평가·정책 발행 변경

설치된 실행 순서는 유지하고 변경 producer의 실제 위치만 보완한다.

```text
20:10 main snapshot:
#11 source-quality preflight
→ #76 machine/AI/provider 분모·compact request materialization
→ #77 single-contract compact R0–R3
→ 기존 cost/economic source terminal과 #74 final raw generation audit
→ #82 outcome/semantic/machine calibration과 mechanistic policy publisher
→ main verifier/tower/checklist/strict

21:05 late follower:
terminal detailed compact evaluation
→ #82 refresh
→ #78 compact incumbent frozen binding + machine policy selection
→ provider0 metadata-only rebind
→ #79 holding manifest
→ #80 consumer
→ 늦은 source summary handoff와 strict/controller/finalization 재확인
```

실제 wrapper가 위 논리 의존과 다른 순서를 갖고 있으면 설치 상태·runbook·traceability를 먼저 대사해 최소 수정한다. 문서의 순서만으로 producer를 중복 실행하거나 비용 producer를 앞당기지 않는다.

장후 owner별 변경과 수용조건은 다음과 같다.

| Owner | 변경 | terminal 수용조건 |
| --- | --- | --- |
| #11/#74 | pipeline과 기존 AI raw archives의 generation/hash, exclusion, compact role/schema를 감사 | active writer는 waiting, final stable generation과 #76 digest 일치; 식별 결손 row만 격리 |
| #76 | machine evaluation·AI screen·provider attempt를 별도 manifest/digest로 materialize | action/reason/policy/micro/prompt parent 결속, non-entry no-provider 정상, ENTER screen gap 명시 |
| #77 | `evaluation_mode=single_contract_auxiliary`; compact 단일계약 R0–R3 | A0/A1 호출·가짜 pair 없음, valid/empty/gap/error terminal, old AI-only generation 격리 |
| #82 | exact cost/outcome를 join하고 AI 품질과 machine challenger를 별도 section으로 산출; exact compact version의 missed-VETO/dangerous-PASS 차이로 bounded registry successor를 자동 선정 | semantic/error/경제성 null 분리, case full digest와 scope 보존식, 기계/AI·legacy/current-version 분모 불혼합, 20건·미분류0·`max(2,10%)` gate |
| #78 | compact incumbent 또는 #82가 선정한 registered successor를 frozen binding하고 machine challenger는 기존 경제 gate로 선택 | prompt migration을 `paired_improvement_pass`로 표시하지 않음; legacy prompt 자동 선택·자유형 live 편집 차단 |
| 21:05/#80 | single-contract terminal·same-generation hash·provider0 metadata rebind 확인 | nonexistent control 요구 없음, old terminal 재라벨링 없음, holding/#79 독립 closure |
| verifier/tower/checklist | compact generation과 machine candidate/carry disposition을 전달 | source/hash/보존식·필수 terminal 오류는 차단, 대조군 미실시 자체는 PASS 가능한 N/A |

machine policy 발행 disposition은 `bounded_challenger`, `incumbent_carry_sample_or_no_edge`, `scope_partial_replace_with_other_scope_carry`, `incumbent_carry_source_or_cost_gap`, `fail_closed_invalid_incumbent`로 명시한다. valid incumbent인데 challenger/child가 없다는 이유로 파일을 누락하지 않는다. prompt disposition은 별도로 `compact_contract_migration|compact_incumbent_carry|compact_registered_successor_auto_selected|fail_closed_compact_contract_invalid`를 사용한다.

### 22.19 P9 — 다음 PREOPEN·PID 수용

07:35 PREOPEN은 실제 next KRX trading date, bundle/source/cost/calibration hash, 승인된 지원 scope 전수, selected level/child count, compact prompt/input/schema/validator hash, machine candidate/carry disposition, operator override·expiry와 rollback predecessor를 검증한다. 이전의 `base prompt + addendum hash`는 old-generation audit field일 뿐 compact generation의 필수 두 조각으로 요구하지 않는다.

07:55 이후 실제 기동이 승인·수행된 경우에만 PID root/release commit, loaded bundle/hash, 최초 기계판정 이전 policy-load receipt, ENTER_NOW에서만 AI 호출, PASS/VETO/CAUTION/INSUFFICIENT/error mapping, KRX/NXT/SOR exact venue/session first use를 확인한다. policy 파일 생성·timer start·unit start 성공만으로 PID 소비나 자연 판단을 완료 처리하지 않는다.

compact 전환이 restart 없이 날짜 경계 loader로 반영되는지, 새 release가 필요한지 실제 consumer를 먼저 확인한다. 재기동이 필요하면 그 구현 실행의 승인 범위에서 main/widget/episode/manual 미체결·custody를 사전 대사한 뒤 기존 절차를 따른다. 이 계획 작성은 재기동·배포 승인이 아니다.

### 22.20 과도한 gate 제거와 유지 경계

제거하거나 최초 compact 전환에 적용하지 않는다.

- 구 전체형과 축약형의 A/B Provider 비교, A1>A0, paired 10/3/3 또는 30 trace/10 symbol/2일
- 모든 1/3/5/10/20/30/60분 outcome 완비와 9개 scope 전체 동시 통과
- 공통·그룹·종목 sample floor 누적 적용, child 부족에 따른 유효 parent 차단
- 실제 fill 부족에 따른 source-only CF 진단 차단
- challenger 부재에 따른 다음날 policy 미발행
- AI PASS/BUY 수 증가, 짧아진 문자열 또는 schema 성공만을 품질 승인으로 사용
- prompt contract migration에 기계 challenger의 EV `>=+0.10%`를 중복 선행조건으로 사용

유지한다.

- exact identity/source hash/generation, no-future-leak, 동일 venue/session/scope
- prompt/input/schema/validator/composer와 실제 request/response hash 결속
- full round-trip cost; 결손 null·원인 분류와 이중차감 방지
- AI semantic 오류 fail-closed, 기계 non-entry 승격 금지, final hard/order guard
- 기계 threshold challenger에만 chronological holdout, incumbent 대비 비용 후 EV 개선, 해당 family 최소 EV `+0.10%`, tail·깊은 역행 비열화 금지
- valid incumbent carry와 invalid incumbent fail-closed의 구분

### 22.21 구현 위치와 review/fix 검증

새 서비스·DB·cron·판정기·Provider endpoint·무제한 grid를 만들지 않는다. 신규 Python 모듈도 기본 불필요하며 기존 owner 안에서 보완한다.

| 범위 | 기존 파일 |
| --- | --- |
| prompt/response | `src/engine/ai_prompt_contracts.py`, `src/engine/ai_engine_openai.py` |
| trace/identity | `src/engine/scalping/ai_decision_trace.py` |
| machine composer/validator | `src/engine/scalping/entry_setup_evidence.py` |
| bundle/policy | `src/engine/scalping/mechanistic_entry_runtime_policy.py`, `src/engine/scalping/entry_setup_live_policy.py` |
| #76/#77/#82 | `src/engine/scalping/ai_decision_quality.py`, `src/engine/scalping/ai_action_outcome_calibration.py`, `src/engine/scalping/entry_setup_paired_replay_batch.py` |
| #78/#80 | `src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py`, `src/engine/scalping/main_ai_prompt_consumer.py` |
| #11/#74/verifier | `src/engine/observation_source_quality_audit.py`, `src/engine/verify_threshold_cycle_postclose_chain.py` |
| wrapper | `deploy/run_ai_entry_setup_paired_replay_postclose.sh`와 실제 호출하는 기존 main/postclose wrapper |

구현 순서는 `P0 재현 → P1 identity/전수원천 → P2 비용 → P3 outcome → P4 compact prompt/semantic → P5 micro → P6 machine challenger → P7 submit attribution → P8 장후 소비/발행 → P9 PREOPEN/PID`다. 각 P단계는 구현→self review→finding 수정→재리뷰→targeted validation을 통과한 뒤 다음 단계로 간다. 이미 정상인 owner는 테스트 근거만 남기고 불필요하게 수정하지 않는다.

필수 테스트는 기존 인접 파일에 추가한다.

1. `test_ai_engine_openai_transport.py`, `test_mechanistic_entry_runtime_policy.py`, `test_entry_setup_live_policy.py`: compact bytes/hash, old/new version reader, resolver/correction/cache parity, ENTER-only Provider, mapping과 fail-closed.
2. `test_ai_decision_quality.py`, `test_ai_action_outcome_calibration.py`: exact attempt/action/bundle, semantic fixtures, gross/economic table, 비용 원인·이중차감, mature taxonomy, micro states, 256840 pair와 submit phase.
3. `test_entry_setup_paired_replay_batch.py`, `test_main_ai_prompt_optimizer.py`, `test_main_ai_prompt_consumer.py`: single-contract mode, control N/A, legacy 격리, compact carry, machine challenger gate, provider0 rebind, holding 독립 closure.
4. `test_observation_source_quality_audit.py`, `test_verify_threshold_cycle_postclose_chain.py`, wrapper contract tests: preflight/final generation drift, row exclusion/whole block, full digest/scope 보존, fresh summary handoff와 가짜 pair 금지.

Python 변경은 관련 pytest와 compile, shell은 `bash -n`과 wrapper contract test, 모든 변경은 `git diff --check`를 수행한다. 문서/체크리스트 변경은 print-only parser로 검증하고 외부 Project/Calendar sync는 실행하지 않는다. Provider unit test는 fake runner만 쓴다.

### 22.22 최소 재생성·배포·완료 판정

- 원본 canonical report/checkpoint/policy와 old generation을 보존한다. source/evidence가 변하지 않았으면 #76 원천이나 과거 Provider replay를 전량 다시 실행하지 않는다.
- 변경된 최초 producer부터 직접 last consumer까지만 재생성한다. raw generation drift면 Provider 없이 #11→#76→#74→#82를 최신 generation으로 닫고, compact single-contract의 새 Provider 요청은 기존 owner·budget·checkpoint가 허용하는 필요한 exact ENTER에만 한정한다.
- 이미 terminal인 동일 prompt/input/schema request는 재사용하고, metadata-only rebind는 Provider 0·판정/경제성 불변을 검증한다. 실패한 producer와 영향 consumer만 재실행한다.
- 장후 closure는 fresh verifier→tower→checklist→strict/controller까지 확인한다. finalization/cleanup/detector는 실제 영향 계약만 해당 runbook으로 재확인하며 무관한 성공 단계를 새 실행으로 표시하지 않는다.
- 배포가 별도 승인돼 수행되면 worktree와 selected release diff, commit, policy/version registry, activation, rollback bundle을 대사한다. runtime code와 정책이 서로 다른 generation인 부분 배포는 금지한다.

완료 상태는 다음처럼 별도 보고한다.

| 층 | 완료조건 |
| --- | --- |
| 계획 | §22 통합안, owner·권한·수용조건과 충돌 0 |
| 코드/계약 | review P0~P2 finding 0, targeted test/compile/syntax/diff 통과 |
| 장후 handoff | #11→#76→#74→#77/#82→#78→21:05/#80→strict 같은 generation terminal |
| policy/deployment | compact successor와 machine challenger/carry bundle, release·rollback 검증 |
| PID 소비 | 실제 current PID의 load/first-use와 ENTER-only AI receipt |
| 자연 품질 | semantic invalid, correct/missed VETO, dangerous/correct PASS, micro·submit 최초 결손 미분류 0 |
| 경제성 | 같은 scope에서 실제/CF 분리, 비용 후 EV·순익 빈도·tail·자본점유 확인 |

compact migration은 코드/정책 gate가 닫히면 대조군 없이 직접 전환할 수 있다. 경제성 미관측은 그 전환을 취소하지 않지만 경제성 완료도 아니다. 예상 효과는 상충 지시 제거, system prompt 축소, semantic binding 명료화, legacy 독립 선정 역할의 재유입 방지와 장후 책임분모 정정이다. 실제 입력 토큰·AI 지연·submit 지연·VETO/PASS 품질·비용 후 작은 순익 빈도는 PID first-use와 후행 natural receipt로 확인한다. 호출량·retry/model·threshold·수량·hard guard 변경으로 효과를 가장하지 않는다.

## 23. 축약형 인용 계약 수리

2026-09-14 재점검에서 PASS의 adverse 배열 누락은 `entry_risk_pass_residual_risk_not_considered`, bounded VETO의 positive 배열 누락은 `entry_risk_veto_requires_blocking_risk`를 재현했다. JSON schema와 의미 검증을 모두 만족하도록 compact v3는 각 risk-code당 최소 한 adverse ID를 `contradicting_fact_ids`에, bounded VETO의 positive ID를 `supporting_fact_ids`에 명시적으로 요구한다. 각 code의 모든 중복 fact 인용을 요구하지 않는다. 기존 검증기·주문 guard는 그대로 유지한다.

v2/opportunity v1/risk v1은 frozen reader와 이전 SHA256을 보존한다. 새 writer는 compact v3/opportunity v2/risk v2를 발행한다. 기존 publisher가 다음 거래일에 semantic 수리로 자동 이행하며 당일 frozen 정책을 교체하지 않는다. 형식 수리에 20건·양수 EV를 요구하지 않고, 이후 #82의 자동 성과 변형 선정은 exact incumbent 분모와 기존 gate를 사용한다. 개별 사용자 승인은 필요 없다.

프롬프트에는 기계 ENTER 보조 역할, 비용 차감 작은 수익 목표, 선택적 결측의 중립 처리, 위험/긍정 근거와 출력 규칙을 유지한다. 원장 metadata 축소는 별도 최적화 여지이며 이번 필수 인용 수리에 payload/hash 재설계를 추가하지 않는다. 기대 효과는 모델이 정상 근거를 갖고도 인용 형식 때문에 재확인으로 이탈하는 비율의 감소다. 실제 순익 증가·AI latency 감소는 이번 코드 검증으로 확정하지 않는다.

검증은 누락 인용의 차단/정상 인용 수용, frozen 세 버전 SHA256과 로딩, 다음 거래일 자동 이행·당일 bytes 불변, 기계 정책 불변, live adapter·source audit·calibration·optimizer/consumer 회귀를 포함한다. 미래 자연 확인은 기존 `CodeImprovementWorkorderReview0914`에서 prompt version/hash·semantic error·PASS/VETO·submit/실제 비용 후 outcome을 대사한다. 자동 선정의 20건/오류 차이는 경제적 개선의 증명이 아니며 후행 비용 후 EV·순익 빈도·tail 관찰이 필요하다.

검증 receipt: 관련 회귀 661 PASS, 최종 suffix의 code별 표현 보완 후 compact/machine-screen 회귀 21 PASS, compile·diff 검사 PASS, print-only parser 26항목. 기본 본문은 248 words/1951 chars다. 검토 범위의 필수 인용·버전 보존·자동 이행에서 미해결 finding 0이며, 실제 provider의 인용 오류율 감소와 자연 경제성은 미관측이다.

## 24. 장후 전환 통합 작업지시서 연결

[장후 전환 통합 작업지시서](machine-compact-auxiliary-postclose-implementation-workorder-2026-09-14.md)는 #11/#74·#76, #82, #77/#78/21:05, #80/verifier, #119/#23, 최종 요약의 추가 보완을 WP0~WP7로 분할한다. 한 번의 구현 실행 지시로 전체 작업을 진행하고 각 WP의 코드리뷰·수리·재검증 뒤 통합한다. §23의 완료된 인용 수리는 보존한다. 작업지시서 작성 자체는 운영 실행이나 새 구현 완료를 뜻하지 않는다.
