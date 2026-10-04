# 삼성전자 기존 원천 가설 소진 연구계획

Owner: `SamsungPatternCampaign1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [호가 회복 연구](../audits/samsung-quote-recovery-and-absorption-research-review-2026-10-04.md).

## 1. 종료 기준과 권한

사용자의 연속 연구 지시에 따라 단일 음성 결과에서 멈추지 않는다. 기존 원천에서 의미가 다른 가설을 차례로 검증하고, 운영 적용을 검토할 근거가 충분한 패턴을 확보하거나 아래 가설군의 검증 및 원천 한계 대사를 마친 뒤 종료한다. 임의의 모든 수치 조합을 무한 탐색하지 않는다. 같은 정보의 숫자만 바꾼 조합은 새 가설로 보지 않는다. 연구 후보, 구현 검토 가능성, 현재 생성기의 정식 선정, 실제 배포/기동/실현 손익을 구분한다.

기존9/29·9/30·10/2 보관 체결/호가·captured Main 판정·Widget 문맥만 사용한다. 수집 확대·API/provider 호출·정책 발행·배포·재기동·주문은 실행하지 않는다. 삼성전자외 데이터는 섞지 않는다. 기존 성공100%/80% 보존을 탈락 조건으로 두지 않는다. Plan Rebase의 과거 retention 문구보다 이번 사용자 지시를 우선한다.

## 2. 위치와 봉인

독립 오프라인 producer는 `src/engine/scalping/samsung_pattern_campaign.py`, 회귀는 `src/tests/test_samsung_pattern_campaign.py`에 둔다. 기존 runtime이나 publisher의 입력/호출을 변경하지 않는다. 선행 연구 kernel과 결과를 보존한다. normalized retained cache를 소비하며 Kiwoom request/parser/FID/REG/auth/order를 변경하지 않는다.

선행 locked-price 캐시3개, 원천/선행 kernel/계획 hash, Main projection, 본 계획/신규 kernel, 기존 정책/인계98개 hash를 실행 전에 봉인하고 종료 후 대사한다. `_AL/SOR_REGULAR` 관측은 실제 KRX/NXT 주문 경로 인증이 아니다.

## 3. 순차 검증할 가설군

신호는 수신 순서의 과거 정보만 소비한다. 대형 매도 shock에만 한정한 선행 모집단을 넘어, 종일 보관 stream의 고정1초 관측에서 가설을 확인한다. 관측 주기는 연구 샘플링이며 운영/API 관측주기 변경이 아니다.

| 가설군 | 인과적으로 확인할 내용 |
|---|---|
| absorption | 최근3/5초 bid 유지·SELL 우세·SELL3개 이상, rolling 저점 근처에서 회복 이전 진입 |
| sell_decay | 최근5초 매도량이 직전5초의 절반 이하, BUY 우세, 저점 근처 |
| flow_flip | 직전5초 BUY 비중≤40%, 최근5초≥60%, 저점 근처 |
| range_retest | 과거 저점의 시간 분리된 재시험 뒤500원 회복, 추격 거리 제한 |
| range_reclaim | rolling 고점 대비 하락 후 저점보다500원 회복, 저점과 거리 제한 |
| vwap_reclaim | 과거 rolling 체결량 가중 가격을 아래에서 위로 회복, BUY 우세 |
| trend_pullback | 뒤 절반의 저점이 앞 절반보다 높고, 고점에서 눌린 최근 저점 근처, BUY 우세 |
| breakout | 과거 rolling 고점 회복, BUY≥60%·최근 체결량 증가 |

과거 창60/180/300초, 보수 수준1/2, 시각 그룹전체/09~10시/10시 이후를 미리 고정한다.500원은 연구 가격 거리이며 공식 tick 단위 인증이 아니다. 실행 가능한 가격 진단은 최신 과거 bid<ask·양수 잔량의 ask 진입, 이후 bid<ask·양수 잔량의 bid 종료를 쓴다. 잠금호가는 연속 관측 문맥에만 허용하고 진입/목표/손절 실행 가격으로 쓰지 않는다. crossed/bad clock/epoch/sequence/freshness 결손을 보간하지 않는다.

## 4. 결과 계산·비교

- 비용0.33%·순목표+0.1%·gross stop−0.7%를 고정한다.600/1200/1800초의 동일한 자체 보유창으로 duration 가설을 연구한다. 종료창을 늘린 추가 목표를 조기 진입 효과라고 부르지 않는다. 실제 Main trailing의+0.4% arming과 연구 목표+0.1%가 다름을 별도로 표시한다.
- 목표/손절이 유효한 연속 경로에서 먼저 관측되면 그 시점에 흡수 종료한다. 이후 결손은 그 결과를 취소하지 않는다. 결손 뒤 관측 목표는 지원수에 넣지 않는다. 창 끝까지 유효하지만 미도달한 결과 binary는null이고 시간 종료 quote CF를 따로 남긴다. 결손 CF/PnL은null이다.
- 신호 시간순 첫 적격 신호를 선택하며 entry+보유창+1.5초를 예약한다. 결과가 결손이어도 뒤 성공 신호로 교체하지 않는다. 같은 원천 가격 창의 겹치는 거래를 독립 지원수로 세지 않는다.
- 비교 기준은 같은 날짜/시각그룹/창에서 고정시계 bucket의 최초 source-valid nonlocked quote 진입이다. 이는 무조건 감시 가격 기준이며 현재 Main 정책과 구분한다. Main 판정은 원래 native identity·cost-bound label·hard guard가 있는 별도 bridge로 평가한다.
- 조건부 target-first 승률을 먼저 비교하되, binary 지원수·목표/전체진입 비율·미도달·censored·시간 종료 포함 CF·손실 tail·coverage를 함께 보고한다. 연구 후보 선택에 성공 보존율이나 평균 CF 양수 veto를 두지 않는다. 운영 적합성은 시간 종료 포함 경제성과 source/guard 적합성을 별도로 확인한다.

## 5. 학습·재검토와 후속 단계

9/29 학습→9/30,9/29~30 학습→10/2의 순서를 고정한다. 결과를 이미 탐색한3일이므로 새 pristine holdout을 주장하지 않는다. 각 fold에서 학습 binary≥3, 기준 binary≥3, 기준보다 높은 승률인 후보를 승률→Wilson 하한→지원수→단순성으로 고정하고 후단에서 재선정하지 않는다. 시각/보유창/조건 숫자 탐색을 포함한 전체 후보 수를 공개한다.

선정 후보가 있으면 이웃 조건·250/1000ms 지연·Main+0.4% arming 가격 도달·같은 시간 종료 비교·원래 Main soft-confirmation admissible 집단에서 보존된 hard guard·native 지원수를 확인한다. 표본1/1, 동일 진입가격의 종료창 이동, 음수 시간 종료 CF, 강한 hard guard 위반만으로 생긴 이익은 운영 패턴 확보로 닫지 않는다. 후단 결과를 보고 후보를 다시 고른 연구는 탐색이라고 표시한다.

후보가 없거나 불안정하면 다음 가설군을 계속 실행한다.8개 가설군·시간 그룹·창·종료 전 원천 결손 대사·Main bridge·Widget 성공 경로의 route/session 차이까지 확인한 뒤, 남은 가설이 동일 정보의 추가 숫자 탐색인지 기존 원천에 없는 식별 정보/독립 검증을 요구하는지 설명한다. 부족한 provenance를 no edge나 net0으로 바꾸지 않는다. 새 검증 원천을 확보하라는 작업은 만들지 않는다.

## 6. 코드·문서 완료

구현→자체 리뷰→보완→재리뷰→표적 pytest/compile/diff, 실제 cache prefix 인과성·재실행 일치·hash 보존·link/owner·print-only 문서 parser를 완료한다. 실시간 정책 소비와10/6 기동 owner는 변경하지 않는다. 최종 audit는 실행한 가설·결과·중단 이유·운영 적용 가능성의 근거와 한계를 포함한다.

## 7. 단기 결과 후 고정한 비용 폭·장주기 단계

첫432개 조합에서 단기 매도 감소 후보는9/29~30 학습3/3·10/2 확인1/1 목표였다. 후단 기준도1/1이며 native 신규 진입0건으로 운영 패턴을 확보한 것으로 닫지 않았다. 해당 결과를 보존하고 다음 단계는 학습에서 새로 선택한다. 이미 본10/2를 새로운 독립 holdout으로 취급하지 않는다.

- 장주기 가설: 과거300/900/1800초의 가격 폭과1200/1800/3600초 보유창. 매도/흡수·range·VWAP·눌림목7가설군을 사용한다. 과거 고점 위 진입인 breakout에는 저항까지 회복 여유 조건을 섞지 않는다.
- 비용 폭 가설: 과거 창 고점에서 현재 ask까지의 여유가 비용0.33%를 차감하고도+0.1% 또는+0.4% 이상인 경우만 진입한다. 미래 MFE가 아닌 과거 저항 가격이다. 좁은 진동의 저점은 비용을 못 이길 수 있다는 가설을 분리한다.
- level1/2·시각3그룹·과거 창3·비용 폭2·보유창3의756개 추가 조합이다. 단기432개와 별도 단계로 선택하고 총1,188개 탐색을 공개한다. 후단 성과를 보고 학습 우승자를 바꾸지 않는다.
- 개선된 코드로 기존 단기432개 일별 metric과 선정이 재현되는지 대사한다. 첫 kernel을 보존하며, 신규 봉인 캐시에 전체 원천·코드·계획 hash를 다시 고정한다.

## 8. 가격 폭 단계 후의 잔량·비용 표현 단계

장주기756개는 학습 binary3개 이상을 확보하지 못해 미선정이었다. 아직 소비하지 않은 보관3단 잔량을 기존 local depth-v1 domain record에서 가져온다. API/FID/response parser를 변경하지 않는다. 캐시의 원래epoch/sequence/수신 timestamp/best price/qty를 전수 대사하고 부적격3단은 missing으로 둔다.

- `book_support`: 저점 근처 BUY 우세와3단 bid/ask 잔량비≥1.5/2.
- `bid_replenish`: SELL 우세·5초 bid 유지 중 best bid 잔량이5초 전의1.2배 이상.
- `ask_depletion`: 저점 근처 BUY 우세 중 같은 ask의 잔량이5초 전의70% 이하.
- `book_flip`:5초 전3단 잔량비≤1에서 현재≥1.5로 전환, 저점 근처 BUY 우세.

60/180/300초·level1/2·시각3그룹·600/1200/1800초의216개 잔량 조합을 추가한다. 정적 잔량 또는 그 변화는 실제 주문 주체/보충/체결 가능성 인증이 아니다.

비용 표현을 분리한다. 기존0.33%를 보수 마찰 stress로 유지한다. 별도로 exact-date verified KRX/NXT profile의 buy fee+sell fee+sell tax+uncertainty buffer를 사용한다. 양 venue/날짜의 값이 같지 않거나 source hash/provenance가 없으면 이 모델은 실행하지 않는다. 현재 보관 profile 값은0.23%다. spread는 실제 관측 ask 진입/bid 종료에 이미 들어가고 추가 sweep/impact는0으로 가정한 **가격 비교**다. 실제 broker 비용/실현 EV라고 표시하지 않는다. source fee/tax/master/reference hash를 함께 봉인한다. captured Main full-cost label과 현재 runtime 비용 계약은 변경하지 않는다.

두 비용 표현에서 단기432·장주기756·잔량216의 총2,808개 조합을 별도 단계별로 학습 선택한다.0.23%에서만 보이는 신호를 실행 마찰에 강한 운영 패턴으로 판정하지 않는다. 지연과+0.4% arming 가격 도달을 함께 대사한다.

## 9. 기존 장전·장후 세션의 분리 검증

정규장2,808개에서 잔량 후보 미선정·비용 비교 후보의 후단 악화가 확인됐다. 보관 inventory에서 장전/장후 partition도 확인되어 종료하지 않고 이를 추가 소비한다. 사용자 지시는 원천 수집 확대가 아닌 기존 원천 추가 소비를 허용한다.

`src/engine/scalping/samsung_session_pattern_research.py`는 기존 local domain stream의 exact `005930_AL|SOR|SOR_PREMARKET` 및 `SOR_AFTERMARKET`를 별도 producer로 읽는다. request/response/FID/REG와 runtime을 변경하지 않는다. stock·schema·route·day·clock·sequence·shard/hash를 확인하며 세션 사이 결손을 연결하지 않는다. 위젯의08:19 진입·09:24 종료 수익을 정규장 단기 pattern의 학습 성공으로 넣지 않는다.

동일12가설군·두 비용 표현·과거 창·보유창을 사용하되 시각 그룹은 각 partition 전체로 고정한다. 장전936개·장후936개를 별도 학습 선택하고 전체 총4,680개 탐색을 공개한다. native Main 정규장 기회 수와 이 연구의 가격 사건 수를 합산하지 않는다. 시간대 관찰 그 자체는 해당 시장에서 주문할 권한이 아니다. 이미 본3일의 추가 탐색이며 신규 독립 검증이라고 부르지 않는다.

추가 venue census에서9/30·10/2 `005930_NX|NXT|NXT_PREMARKET`의 각18,794/22,449체결 및17,840/18,552호가, `NXT_REGULAR_OVERLAP`의3,104/20,845체결·1,724/17,254호가도 확인됐다. `_AL` 자료로 대체하지 않고 이 두 exact scope의 같은936개 조합도 분리 검증한다.9/29 NX source absent/valid-empty는0손익·실패로 넣지 않는다. 전체5개 exact scope의 조합 수는6,552개다. 직접KRX partition의 삼성전자 행은 census에서0건이므로 KRX 실행 증빙으로 만들지 않는다.
