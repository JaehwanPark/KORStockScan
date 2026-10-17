# 누적 보조판정 문구·인과 입력 실제 연구 검토 — 2026-10-17

사용자의 상세 연구 실행 지시로 추가600회, 기존800회를 포함한 누적1,400회 상한의 독립 연구를 완료했다. 신규 실제 응답545개와 발송 전 실패18개를 대사하여 누적1,363회 차감, 잔여37회다. 정책 발행·배포·재기동·주문은 실행하지 않았다.

## 1. 연구 계약과 원천

- 승리: 확인 ask 기준 비용0.0023을 한 번 적용하고, soft −3%에 먼저 닿지 않은 채1,800초 이내 비용 후+0.4% 도달. STOP과TIMEOUT은 별도 실패, 미확정은 이진 성과에서 제외한다. 실제 보유 이관·매도·손익과 연구 라벨을 합치지 않는다.
- 지표: 같은 유효 비교 확인점의 PASS 승률 우선, 동률이면 승리 PASS 수. 손익 크기·손익비·고정 최소 일수/표본·승리 보존율을 추가 채택 문턱으로 사용하지 않는다. 분모0은null이다.
- 원천: 9/29~10/16의11개 보유 원천일,66partition,7,891,363행. 현재 선택 기계 확인점14,005개는WIN1,523/STOP276/TIMEOUT543/미확정11,663이다. 기존 연구 key343개 및 알려진 같은5분 원천 구간을 개발 격리하여 새 후보578개·101구간을 확보했다. 5분 구간은 독립 거래·통계적 독립성 증거가 아니다.
- 새 표본 명단은 승패·AI 판정을 보지 않고 고정했다. screen30개/20구간, factorial30개/20구간, final150개/61구간이다. 기존 개발9개 및 과거 연구와 새 단계의 구간은 겹치지 않는다. 같은 구간의 여러 확인점은 반복 수로 별도 표시한다.
- 10/13은 기존 보강 원천과 전체1,401개 census를 대사했다. 확정1개는 이미 연구에 사용됐으며 새 효과 표본에 넣지 않았다. 10/16은 승인 epoch의 유효 NXT_AFTER645행이 있으나 현재 확인점이 없고, 다른 경로의 원천 결손은 보존했다.

근거: [모집단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/population.json), [원천 검증](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/population-validation.json), [승패 없는 표본 목록](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/label-blind-point-index.json).

## 2. 대조군과 격리

선택 코드 기준은`nonfixed-quote-20261017-a41ebc84f`다. 실제 PID 소비는false인 다음 정규 기동용 선택이며, 주말 봇을 기동하지 않았다. 원 기계 부모는`8809c82e…`의 원 generation 파일과 SHA를 직접 사용한다. 연구 참고용으로 reseal한`parent.json`은 원 정책 파일로 사용하지 않는다.

현재128개 보조 binding은10/16의 마지막 유효 overlay`8185f257…`를 포함하여, 일치하는 불변7f2552aed reader에서 검증·고정했다. 두 개의 앞선H6 변경 범위도 대조군에 들어 있다. 실제 선택a41 reader의 직접 보조 승계 조회에서는`compatibility/de77d7d8…json` 부재를 관측했다. 이는 고정한 이전 부모에 대한 직접 조회 결과이며,10/19 전체 기동 인계 경로의 실패를 확인한 것은 아니다. 연구가 이 운영 증빙을 생성하거나 정상화하지 않았으며, 다음 운영 적용 시 정확한 reader/부모의 호환 증빙을 별도로 확인해야 한다.

연구 코드는`/home/ubuntu/KORStockScan-worktrees/auxiliary-discriminative-research-20261017`에서 격리했다. 원 DB·raw 복제 없이 공유 comparison store의 exact request/object를 재사용한다. canonical 장후 보고서·tuning 설정·선택 정책은 덮지 않았다.

근거: [고정 binding](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/binding-capture.json), [실행 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/execution-protocol.json).

## 3. 비교와 선발

모델·설정·원 입력·응답 형태를 고정한E1은 스프레드 수치와 실제 가격 진행의 함께 읽기, E2는 최근 관측을 먼저 읽고 rolling 과거 약세와 현재 상태를 구분하는 최소 문구 변경이다. 후보와 현행을 같은 확인점에서 실제 호출했다.

| 단계 | 현행 | E1 | E2 |
|---|---:|---:|---:|
| 개발9점 | TP2/FP4/FN3/TN0 | TP3/FP4/FN2/TN0 | TP3/FP4/FN2/TN0 |
| 새screen30점 | TP14/FP9/FN3/TN4 | TP13/FP8/FN4/TN5 | TP14/FP8/FN3/TN5 |
| screen PASS 승률 | 60.9% | 61.9% | 63.6% |

개발 사례의 STOP4개는 두 문구 후보도 모두 PASS했다. 개발 결과를 채택 성과 분모에 더하지 않는다.

처음 범위별`improves`만으로 만든 조합은 실패만 있는 범위의FP 감소를 전체 PASS 승률에 반영하지 못했다. 같은30개 비교 표본의 누적 승률로E2를 선정하도록 검토·수정하고 명시 후계 영수증을 남겼다. 범위별 결과는 진단으로 보존하며 별도 성과 문턱으로 삼지 않는다. 기존 scope-only factorial 준비물은 무호출 상태로 보존하고`-global` 명세로 분리했다. 새 표본 명단·프롬프트 문구는 바꾸지 않았다.

## 4. E3 실제 과거 원천 입력 실험

기존 최근10체결 요약의 산술 표현 외에, 정확한 원 native epoch·sequence·item·시각에서 끝나는 최근10초와 그 이전20초의 관측 가격·매수 비중·수량·coverage를 추가했다. 새 factorial30점 및 final150점180개를 원 정규화 원천과 대조했고173개에30초 구간이 있으며7개는 부족한 파생값을null로 유지했다.

조용한 구간의 경계 직전 마지막 관측 가격은 실제 경계보다 오래될 수 있다. 실제 경계 체결 epoch·anchor age·관측 수를 함께 제공하고, 가격 진행 속도는 명목10/20초가 아닌 실제 관측 시간으로 계산한다. 관측 segment가 창을 포함한다는 사실을 시장 전체 수신 완전성으로 표현하지 않는다. 빈 창·오래된 참조를 가격 실패·API 결함으로 단정하지 않는다. v1 원천표를 보존하고 이 의미를 명시한v2를 사용했다.

새 사실은 버전·코드 SHA·정확한 인용 binding으로 구분한다. 원 snapshot/object는 그대로 두고 연구용 복사본에 evidence를 붙이며, CURRENT의 기존 wire 요청은 동일함을 검증했다. 미래 행 제거 후189개 개발/평가 원천 계산이 변하지 않음을 확인했다. 입력 실험은 운영 발행 증빙으로 사용할 수 없도록 기존 publisher의 native 비교 조건에서 차단한다.

| 별도factorial30점 | TP | FP | FN | TN | PASS 승률 |
|---|---:|---:|---:|---:|---:|
| 기존 입력·현행 문구 | 9 | 13 | 4 | 4 | 40.9% |
| 기존 입력·E2 문구 | 11 | 13 | 2 | 4 | 45.8% |
| 새 입력·현행 문구 | 10 | 17 | 3 | 0 | 37.0% |
| 새 입력·E2 문구 | 13 | 16 | 0 | 1 | 44.8% |

새 입력은 승리PASS를 늘렸지만 실패PASS도 늘었다. 다음 최종 검증 후보는 기존 입력·E2 문구로 동결한다. 이30개 표본을 다음 최종 효과 증명에 재사용하지 않는다. 원천 추가 효과와 문구 효과를 구분하며, 기존 10체결의 단순 파생값을 독립 새 정보로 주장하지 않는다.

근거: [v2 원천표](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/source-prefix-facts-v2.json), [개발 원천표](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/source-prefix-development-v2.json), [후계 실험 계약](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/input-selection-protocol-v2.json), [최종 후보 동결](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/final-selection.json).

## 5. 구현 결함 수리와 검증

- 실제 응답을 받기 전 격리 경로의 설정 파일이 없어18개 예약이 executor의 API client 생성 이전 예외로 끝났다. 원 시도·예산 차감은 보존했다. executor 코드 SHA/정확한 예외 위치/모든 시도·응답을 확인하고 기존 journal 재조정 후 요청만 재대기로 옮겼다. 실제 Timeout/불명확 전송/기존 실제 응답에는 이 복구를 허용하지 않는다. 이후 실제 SDK 호출은 자격증명을 확인한 뒤에만 예약한다.
- 새 입력 요청을 기존 입력으로 검증하던 호출 경로를 수정했다. prepare/calls/evaluate의 역할별 입력·schema·citation을 일치시키고 candidate-only 실험에서는 CURRENT를 그대로 둔다.
- protocol·driver 수정은 기존 봉인을 덮지 않고 후계 영수증으로 연결했다. 불완전 응답을 유효쌍 합계로 숨기지 않도록 완료·제외 회계를 보존하고, factorial 중복 key·정답 hash·동결 membership과 최종 준비 key를 검사한다.
- 예산1400회는 원800회 영수증과 동일 budget key에 연결한다. 날짜·분기·오류로 초기화하거나 장후 정기 한도를 변경하지 않는다.

검증 이력: 기존 통합85PASS, 예산·복구·연구·초기 입력 통합71PASS, 실제 과거 원천 입력·candidate-only 최신36PASS, Python compile·diff 검증. 실제 연구 호출과 테스트의 주입 transport는 구분한다. 최종 종료 검증은 결과와 함께 보강한다.

근거: [18건 발송 전 실패 복구](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/pre-send-recovery.json).

## 6. 최종 결과와 종료 상태

최종 후보는 기존 입력에E2 문구를 더한 것으로 동결하고, 앞선 단계와 구간을 분리한150개 확인점을 실제 paired 호출했다.150쌍 모두 유효하며 응답·원천 결손으로 제외한 쌍은0개다. 전체 단계297쌍은 개발·선발·최종 비교를 합한 실행 수이며, 효과 평가 분모는 최종150쌍만 사용한다. 고유 확인점은219개다.

| 최종150점 | TP | FP | FN | TN | PASS 승률 |
|---|---:|---:|---:|---:|---:|
| 현행 | 14 | 95 | 23 | 18 | 14/109 = 12.8% |
| E2 후보 | 17 | 96 | 20 | 17 | 17/113 = 15.0% |
| 기계 통과 전체, 진단 기준 | 37 | 113 | 0 | 0 | 37/150 = 24.7% |

사용자가 정한 최종 비교 지표에서는E2가+2.2%p다. 정확한 변경은 승리6개를 새로 PASS하고 기존 승리3개를 놓쳐TP가 순3개 늘었으며, TIMEOUT6개를 새로 PASS하고 기존 TIMEOUT5개를 막아FP는 순1개 늘었다. **실패 PASS를 줄였다는 결과는 아니다.** 기계만의 진단 승률보다 보조 PASS 승률이 낮으므로, 보조 관문이 유효 승리를 과하게 막는 문제는 현행·후보 모두 남아 있다. 기계 기준을 이번 비교에 없던 추가 채택 문턱으로 만들지는 않는다.

### 삼성·비삼성 시장별

| 구분 | 최종점 | 현행 승리/PASS | 후보 승리/PASS | 해석 |
|---|---:|---:|---:|---|
| 삼성 PRE | 0 | 0/0, null | 0/0, null | 새 최종 표본 없음 |
| 삼성 REGULAR | 2 | 0/0, null | 1/1, 100% | 승리1개 회복; 현행 승률과의 수치 비교는 불가 |
| 삼성 AFTER | 12 | 0/12, 0% | 0/11, 0% | TIMEOUT1개 감소, 승률·TP 개선 없음 |
| 비삼성 PRE | 25 | 9/23, 39.1% | 8/22, 36.4% | 승리1개 손실 |
| 비삼성 REGULAR | 9 | 1/3, 33.3% | 4/6, 66.7% | 승리3개 회복, FP2개 동일 |
| 비삼성 AFTER | 102 | 4/71, 5.6% | 4/73, 5.5% | TP 동일, FP2개 증가 |

세부 15scope의 TP/FP/FN/TN·route·가격대·반복 구간은 최종 분석 JSON에 보존했다. HPSP REGULAR/2만~10만원/SOR는 승리 5점에서 PASS 0→3, 삼성 REGULAR/SOR는 승리 2점에서 PASS 0→1이었다. 각기 1개 5분 구간의 회복 진단이며 실패 차단 효과를 입증하지 않는다. 기타 비상시 AFTER/2만~10만원/SOR는 2점에서 TP 1→2, FP 0 유지다. 반대로 주성 AFTER/10만원 이상/SOR는 1/3→1/5, 두산 AFTER/2만~10만원/SOR는 1/4→1/5로 악화했다. 이 최종 결과를 보고 유리한 scope만 다시 조합하여 같은 최종 표본의 사전 선정 정책 성과로 제시하지 않는다.

최종 표본의 실제 정답은WIN37/TIMEOUT112/STOP1이다. STOP1개는 현행·후보 모두 비PASS였으므로 새 손절 구별 효과는 아니다.8개 원천일·61개5분 구간이며, WIN37개의 익절 최초 도달 시각은28개다. 알테오젠 AFTER61점은 전체의40.7%이고 전부TIMEOUT이다. 따라서12.8%·15.0%는 고정한scope별 표본의 비가중 수치이며, 누적2,342개 확정점 전체의 승률이나 독립 거래150건의 결과로 일반화하지 않는다. screen·factorial의 정답 구성과 다르므로 앞선63.6%와 최종15.0%를 정책의 시계열 성과 악화로 읽지도 않는다.

새 입력의 과거 개발 9점 진단도 완료했다. 현행 4/8=50.0%, E2 5/9=55.6%였으나, 기존 STOP 4점은 두 문구 모두 4개 전부 PASS했다. 개발점을 최종 효과에 더하지 않는다. 새 원천 입력은 factorial에서 기존 입력보다 낮은 PASS 승률이었으므로 최종 후보에 넣지 않았고 운영 입력으로도 발행하지 않는다.

### 결론과 후속 적용 경계

- 연구 지표의 전역 비교에서는 E2 문구 후보가 우세했다. 효과는 정규장 승리 회복에 집중되어 있으며 PRE·AFTER 일괄 변경의 개선 근거는 없다. 최종 평가 뒤 후보·선정 규칙은 바꾸지 않았다.
- 다음 연구의 우선 대상은 AFTER의 TIMEOUT PASS다. 알테오젠의 반복 TIMEOUT, 현재 반전과 정체의 구분, 실제 ask와 목표 도달 거리·최근 가격 진행을 같이 읽는 가설을 개발해야 한다. 이번 결과로 임의의 새 수치 차단선이나 전 종목 공통 차단을 추가하지 않는다.
- STOP 4개는 추가 과거 원천을 주어도 구분하지 못했다. 해당 prefix에서 당시 관측 가능한 구별 정보가 있는지 먼저 대사하고, 미래 결과를 입력에 넣거나 무리하게 외워 막는 문구는 만들지 않는다. 새 가설에는 별도 검증 집합이 필요하며 이번 최종 150점을 다시 미사용 검증으로 부르지 않는다.
- 이번에 정책 발행·배포·재기동은 실행하지 않았다. 적용 시에는 현재 부모/binding·동일 wire/model·명시 evaluation의 일치를 기존 인계 경로에서 확인해야 하며, 이 연구 결과만으로 현재 PID 소비나 실제 주문 효과를 주장하지 않는다.

최종 오류 대사에서는 기존 입력과 확장 패턴 입력의 위험 근거 분류가 다른 점도 확인했다. [기존 입력 생성](../../src/engine/scalping/continuous_reversal.py)은 `spread_pct > .3`에서만 `observable_wide_spread`를 위험 근거로 만들지만, [확장 입력 생성](../../src/engine/scalping/reversal_extended_auxiliary.py)은 `spread_pct > 0`이면 `observed_spread`를 `contradicting_facts`에 넣고 `ENTRY_SPREAD_CONCERN`을 허용한다. 단순 수치가 없는 문제와 입력의 위험 역할·허용 근거가 다른 문제를 구분해야 한다.

이는 다른 패턴·정답 분포가 함께 섞인 관찰이므로, 이 분류 차이가 모든 오판의 원인이라고 확정하지 않는다. 후속 입력 연구는 동일 원 수치·모델·문구를 유지하고 스프레드 사실의 역할과 위험 근거 가용성만 비교하는 실험을 우선한다. 최신 가격·현재 반전·실제 ask·목표 거리와 함께 판단할 수 있는 공통 수치 사실을 보존하고, 양수라는 사실을 실패 확정이나 안전 확정으로 바꾸지 않는다. 이번 연구 중 대조군 projector를 수정하거나 최종 E2 비교를 다른 입력 비교로 바꾸지는 않았다.

실제 응답을 대조하면 후보가 막은 승리20개 모두 확장 입력의 `ENTRY_SPREAD_CONCERN` 근거를 사용할 수 있었으며, 실제 답변은 그 코드15개·`EARLY_SIGNAL_FRAGILE`5개였다. 후보의 실패 PASS96개 중92개는 숫자 spread가 있지만 이 확장 위험 근거는 없었다. 그92개는 기존 입력91개와 spread0인 확장 입력1개이며, 숫자 spread가 양수인 것은90개,0인 것은2개다. 나머지 실패 PASS4개에는 확장 위험 근거가 있었다. 알테오젠의 약0.208% spread TIMEOUT은 기존 입력에서PASS, 비슷한 약0.209% spread의 정규장WIN은 확장 입력에서CAUTION인 사례도 있다. 시장·패턴이 다르므로 이를 같은 확인점의 인과 비교라고 부르지 않는다. 해당 위험 코드가 없더라도 다른 문맥 위험 근거로CAUTION을 낼 수 있으며, PASS가 신호 하나만 인용했다는 사실만으로 다른 수치를 읽지 않았다고 단정하지 않는다.

추가로 spread0인 확장 입력의 실패1점(`d8c8334a…`)은 `risk_fact_bindings={}`이며, 허용 위험 코드가 `NO_BLOCKING_RISK` 하나뿐이었다. 해당 입력에서 CAUTION/VETO를 내는6개 변형을 기존 validator가 모두 거절하는 것도 확인했다. 이1점에는 유효한 비PASS를 표현할 수 없는 구조적 제약이 있다. 다른91개를 같은 구조라고 일반화하지 않는다. 후속 계약 연구에서는 패턴별 사실 역할과 함께, 관측 사실은 있으나 현재 위험 어휘로 표현할 수 없는 경우를 분리해야 한다. 이번 연구에서 허용 코드나 운영 fallback을 변경하지 않았다.

개발STOP4점은 모두 관측30초 창이 확보되고 새 가격·수급 위험 근거도 제공됐지만 여전히PASS했다.3점은 최근10초 수익률이 음수였으나, 나머지 알테오젠1점은 약+0.204%와 매수수량 비중91.3%였다. 따라서 단순 약한 수급 차단 하나로 모두 해결된다는 결론은 낼 수 없다. 이 원천·요청·입력 SHA와 실제 답변, 코드 역할 차이는 [완료 표본 오류 진단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/completed-error-diagnostic.json)에 보존했다. 최종 진단 SHA:`83f2bbdbab39d01d855e6695c9f4c9cb8bc252e584a0597f075ab65573075f78`. 앞선 진단·문서의 기존/확장 구분 보정 전 증빙도 보존했다. 이 분석은 추가 AI 호출 없이 수행했고 최종 선정은 변경하지 않았다.

### 호출·원장·검증 종료 회계

- 원 예산 800회를 유지한 신규 차감 563회 = 실제 provider 응답 545개 + 발송 전 실패 18개다. 실제 응답 ID 545개가 모두 서로 다르고, 새 불명확 시도는 0개다. 기존 정확 요청 10개를 재사용했다. 누적 1,363/1,400회, 잔여 37회이며 잔여량 소진을 목적으로 추가 호출하지 않는다.
- 실제 응답의 입력 1,222,514/출력 25,910/합계 1,248,424tokens. 지연 중앙값 1,027ms, p95 1,411ms, 최대 3,156ms다. 이는 오프라인 provider 시간으로 장중 전체 경로 지연이 아니다.
- 중복 제거 후 이번 비교가 참조한 고유 2,079개 object의 압축 구간 합계 4,997,500B, 논리 크기 12,718,108B다. 접촉한 공유 pack 파일 합계 19,688,016B에는 다른 참조가 포함되므로 신규 연구 전용 증가량으로 세지 않는다. 전체 공유 DB의 사전 크기 스냅샷은 없어 이번 연구의 배타적 디스크 증가량은 확정하지 않았다. raw/DB 복제는 없다. 종료 시 디스크 85%, 가용 32,113,930,240B다.
- 독립 재계산에서 6개 stage의 완료·membership·원 population 라벨·원 입력 불변·594개 역할별 요청 계약·actual response·발송 전 실패·누적 예산을 대사했다. 최종 150쌍 제외 0, 새 미분류 시도 0이다. 검증 이력의 중복 테스트 수를 합산하지 않는다.
- 최종 독립 코드·보고서 리뷰의 미해결 범위 내 지적은0개다. 선택 릴리스 부모 위 격리 소스 커밋은 `3bac6258e`이며, 본 작업본·선택 릴리스에 자동 통합하지 않았다. 실행 스크립트5개(78,844B)는 [불변 스크립트 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/script-archive.json)에 SHA와 함께 보존했다. Python compile·범위별 diff·로컬 링크와 print-only parser를 검증했고, 장중/장후 전체 자동화·배포·거래 suite는 이 연구의 범위 밖이라 실행하지 않았다.

근거: [독립 최종 분석](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/final-analysis.json), [최종150쌍 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/final-global-campaigns.json), [최종150쌍 평가](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/final-global-results.json), [개발 입력 실험](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/development-prefix-results.json). 최종 분석 SHA:`466052ee8e49b13c6693f9876bd36a47dcbe0e00a84d290568428df55ab21874`. 앞선 분석 봉인은 이력으로 보존했다. 현행 binding과 최종 선정 binding, E2 문구 외 요청 조건 불변, 고유 요청555개=신규응답545개+기존재사용10개의 배타적 대사도 확인했다.
