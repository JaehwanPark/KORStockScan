# 삼성전자 호가 회복·흡수 지속 후속 연구 결과

Owner: `SamsungQuoteRecovery1004`, [실행계획](../proposals/samsung-quote-recovery-and-absorption-research-plan-2026-10-04.md), [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [진입 시점 분리](samsung-event-timing-isolation-and-exit-research-review-2026-10-04.md).
최종 원천/결과: `tmp/samsung-quote-recovery-research-20261004/{strict,locked}-{source,run}`.

## 1. 결론

**기존 원천의 활용을 막던 연구 소비자 조건을 발견했고, 가격 연구의 소비 범위를 넓혀 새 가설을 검증했다. 정식 정책으로 선택한 후보는 없다.**

- 보관 데이터489,445체결·334,124호가·원래1,026매도 충격 사건을 사용했다. 추가 수집/API/provider 호출은 없다.
- 관측 생산자와 로컬 계약은 bid==ask를 허용하지만 이전 연구 reader는 bid<ask만 허용한다. 잠금호가가 이어지는 구간을 제외하면서 모든 새 신호의 자체600초 호가 경로가 결손으로 분류됐다. 이것은 상승 패턴 부재가 아니다.
- 원천 시계·순번·epoch 계약을 유지하고 **잠금호가를 관측 가격으로만** 포함한 별도 민감도 연구에서 bid 회복498개·흡수 후 지속 회복398개를 확인했다. 실제 매수 가능한 호가/수량/venue는 입증하지 않는다.
-10/2 흡수 신호는 겹침 제거23개 중 자체600초 full path17개에서 비용 차감 목표 도달1개·손절0개·미도달16개다. 이1/1을 정책 승률100%로 일반화하지 않는다.
- 같은 절대 종료 시각과 같은 사건으로 맞추면 목표-first 증가가 없었다. 일부 평균 가격 차이는 개선됐지만 학습 승률 우위·충분한 승패 비교를 입증한 후보는 없다. EXIT grid·정식 정책 발행·Main 실시간 조건 변경·배포·재기동은0이다.

## 2. 원천 소비 조건의 차이

현재 workspace [producer](../../src/engine/scalping/micro_reversion/forward_collector.py)는 asks/bids의 첫 가격을 저장하고 `best_ask < best_bid`만 거부한다. [MarketDepthPoint](../../src/engine/scalping/micro_reversion/path_journal.py), [coverage_tier_for](../../src/engine/scalping/micro_reversion/contracts.py)도 equality를 허용한다. 반면 [기존 연구 reader](../../src/engine/scalping/samsung_continuous_recovery_research.py)의 depth valid는 `0<bid<ask`다. 실행 안전 guard와 관측 가격 연구의 용도가 달라 생긴 제외 조건이다. producer/WS parser가 잘못된 가격을 만들었다거나 잠금호가가 주문 가능한 가격이라고 단정하지 않는다.

| 원천 품질 대사 |9/29|9/30|10/2|
|---|---:|---:|---:|
| 보관 호가 |102,450|116,231|115,443|
| strict 유효 가격 관측 |93,141|95,648|98,091|
| clock 유효 equality 가격 관측 추가 |8,253|20,509|17,348|
| 추가 후 유효 가격 관측 |101,394|116,157|115,439|
| strict 유효 관측 간1.5초 초과 구간 |255|170|131|
| 추가 후 같은 긴 구간 |112|12|18|

추가된46,110행은 새 데이터가 아니다. bid==ask이지만 receive/exchange clock이 나쁜 행은 계속 제외했다. crossed/nonpositive·collector sequence/epoch·10초 trade gap·입력 freshness 계약도 유지했다. `_AL/SOR/SOR_REGULAR` normalized 원천을 KRX 전용 Main 실행 증거로 바꾸지 않는다. 현재 PID/선택 release의 소비 현황을 새로 검증한 작업도 아니다.

artifact의 `strict_complete`/`strict_paired`는 **각 모드가 선언한 가격 유효성에서 중간 제외 행도 없었음**을 뜻한다. 잠금호가 포함 모드의 이 필드도 equality 가격을 포함하며, 원래 bid<ask 모드나 주문 가능성 인증을 뜻하지 않는다.

strict 신호 순서의 bid600초 경로 첫 결손 원인 중 순수 잠금호가 제외는9/29 13/18·9/30 16/17·10/2 6/8이었다. 예시9/29는 유효 관측 사이3.98초·8.94초·20.69초가 잠금호가 제외 때문에 생겼다. 나머지 시계·receive gap·epoch 구간은 원천 결손으로 남긴다. 원인별 최종 수치는 [대사 artifact](../../tmp/samsung-quote-recovery-research-20261004/diagnostics.json)에 있다.

Kiwoom request/response/FID/authentication/REG/continuation 코드는 수정하지 않았다. 가격 연구에 로컬 normalized 관측을 포함하는 조건만 별도 선언했다. 실제 protocol/주문 가능성 변경은 이번 연구 범위가 아니다.

## 3. 가설과 분모

첫 적격 수신까지 과거 정보만 사용한다. bid 저점+500원, midpoint 저점+500원과 bid 동반 상승/비확대 spread, bid 회복2초 지속, SELL 우세·동일 bid5초 관측 이후 지속 회복의4가설이다.500원은 고정 연구 경계다. 서로 다른 stream의 timestamp가 같으면 common sequence를 가정하지 않고 엄격히 이전 quote만 연결한다.

| 전체 원래 사건에서 신호 발생 |strict 합계|잠금호가 가격 포함 합계|
|---|---:|---:|
| bid 회복 |174|498|
| midpoint 회복 |174|368|
| bid 회복2초 지속 |152|451|
| 흡수 이후 지속 회복 |96|398|

전체 사건 결과는 겹치는 창을 포함한 반복 진단이다. 여러 recipe가 같은 사건을 잡거나 결과창이 겹쳐도 독립 지원수로 합치지 않는다.

주 비교는 결과/신호 유무를 보기 전에 shock 기준842초 예약으로 고른 같은78개 anchor다. 신호 발생 census 후, 결과 계산 전에 적격 신호 수신 순서로 진입을 고르는 보충 비교도 고정했다. 보충은 기준/새 entry의 전체600초 결과창을 예약하고 결손 시도를 나중의 성공으로 대체하지 않는다. 이 두 선택 방법의 차이는 모두 남겼다.

기준은 선행 연구의 **체결가 최초500원 회복 가설**이며 현재 Main 기계정책을 재생한 기준이 아니다. 모든 BUY는 과거 ask, 가격 exit는 관측 bid, 비용0.33%·net 목표+0.1%·gross stop−0.7%다. 잠금호가 가격은 indicative quote CF이며 실제 fill/PnL/수량 승률이 아니다.

## 4. 결과: 시점 효과와 종료 시각 효과

###10/2 잠금호가 가격 포함·보충 신호 순서

| 가설 |선택 신호|자체600초 full path|자체 목표/손절/미도달|같은 절대 종료 시각 paired|
|---|---:|---:|---|---:|
| bid 회복 |25|16|0/0/16|14|
| midpoint 회복 |21|14|0/1/13|13|
| bid2초 지속 |24|16|0/0/16|15|
| 흡수 이후 지속 |23|17|1/0/16|15|

같은 절대 종료 시각·전체 quote 경로를 만족하는 흡수15개에서는 기준 목표0/손절1·새 신호 목표0/손절0이다. 새 신호의 나머지는 미도달이다. 평균 순가격 CF는 기준−0.4025%·새 신호−0.3904%, 차이+0.0121%p다. 개선됐지만 평균 자체는 음수이고 새 목표 우위가 없다.

전체 quote 경로 대신 양쪽 ask entry·공통 bid 종료·trade 경로만 요구한 **지점 가격 진단**에서는 흡수17개·차이+0.0426%p, 양쪽 고정 종료 순가격 CF 양수0개다. 이17개를15개 target-first 지원으로 바꾸지 않는다. 나머지 가설의 같은 지점 진단은 bid19개−0.0097%p·mid14개−0.0909%p·지속20개−0.0001%p다. 일반적인 ‘회복 확인 후 매수’의 가격 우위는 확인되지 않았다.

### 비용 차감 상승 사례가 실제로 관측됐다

-9/30 14:32:31.534 ask269,500원→14:35:25.192 bid271,000원: 가정 비용 차감 가격 CF+0.2266%. 기준도 같은 가격으로 같은 목표를 관측했다. 새 진입 우위는 아니다.
-10/2 09:13:38.377 ask274,000원→09:23:33.949 bid275,500원: 가격 CF+0.2174%. 새 entry 자체600초에서는 목표에 도달했다. 기준 entry는09:13:13.012이며 BUY 가격은 똑같이274,000원이다.

두 번째 사례의 공통 종료는09:23:13.012다. 그때 bid274,500원·가격 CF−0.1475%였고 양쪽 모두 미도달이었다. 새 entry+600초는25.365초 뒤 끝나므로09:23:33.949의 상승을 더 관측했다. **양수1건의 차이를 더 좋은 entry 가격/신호의 효과라고 계산하면 종료 시각 효과가 섞인다.** 같은 절대 종료 시각 결과와 각 entry 이후 같은600초 결과를 둘 다 보존한 이유다.

따라서 보관 원천에 비용을 넘는 상승 경로가 있다는 사용자 관찰은 가격 연구에서도 확인했다. 상승이 없어서 후보가0이라는 설명은 맞지 않는다. 이번 가설의 진입 우위와 학습 선택은 별개의 문제다.

## 5. 실제 선택 결과와 미선정 원인

9/29→9/30,9/29~30→10/2의 각 학습/후단을 고정했다. 세 날짜는 이미 탐색한 자료이므로 독립 holdout이 아니다. 순위는 승률→Wilson 하한→지원수→단순성이고 성공100%/80% 보존 veto나 양수 mean CF gate는 없다. 기준/후속 모두 승패 판별3개 이상, paired3개 이상과 학습 승률 우위가 연구 선택의 조건이다.

- strict에서는 전체600초 quote path0으로 비교 승률을 계산할 수 없었다. 가격 CF3지점 진단은 존재하지만 target-first 지원이 아니다.
- 잠금호가 가격 포함 주 anchor 학습9/29는 recipe별 paired4개였으나 양쪽 모두 승패 판별0이었다.9/29~30에서 bid/지속은 기준0승3패·새0승2패, mid/흡수는 기준0승2패·새0승1패였다. 승률 우위가 없거나 binary 지원이 부족해 모두 미선정이다.
- 보충 신호 순서의9/29~30 bid는 기준1승1패·새2승1패로50% 대66.7%를 보였지만 기준 binary 지원2개이고, 각 entry 이후600초로 다시 정합하면9/29의 해당 추가 목표는 사라지고9/30은 양쪽1승1패로 같았다. 이를 정식 승률 개선이라고 주장하지 않는다.
- 보충 흡수 학습9/30의 동일 자체600초 사건19개는 기준1승1패·새1승2패였다.10/2의 단일 양수 사례만 보고 후단에서 recipe를 재선정하지 않았다.

주/보충·strict/잠금호가 가격 포함의 모든 fold에서 선택0이다. 새 Main 정책·EXIT 후보·성공 보존율 veto 제거의 추가 런타임 변경을 발행하지 않았다.

## 6. 다음 연구의 방향과 코드베이스 의미

확정한 개선점은 **관측 가격 품질과 실행 가능 quote 품질을 분리해 기존 원천을 소비하는 것**이다. 이번 [독립 연구 모듈](../../src/engine/scalping/samsung_quote_recovery_research.py)에 가격 민감도 옵션을 구현했다. 기존 Main submit/quote 안전 guard와 기존 연구 reader는 변경하지 않았다.

다음 가설은 회복이 끝난 뒤의 확인을 늘리는 방향보다, 기존 원천의 **흡수 관측 구간에서 breakout 이전의 ask entry**와 그 뒤 bid 이동을 구분하는 것이 적합하다. 별도 연구에서 낮은 변동/시간대/회복 전 spread 상태를 학습으로만 나누고, 같은 사건·같은 절대 종료 시각 비교와 기간별 결과를 유지해야 한다. 원래3일을 새 독립 검증으로 부를 수 없다. 잠금호가의 실제 실행 가능성은 보관된 depth levels/route/raw packet 대사로 별도 확인할 사안이며 신규 수집 확대를 결론으로 요구하지 않는다.

## 7. 리뷰·검증·재현

구현→자체 리뷰→수정→재리뷰→표적 검증을 완료했다. quote join의 같은 timestamp 순서, invalid/epoch/flow 이후 과거 저점/흡수 상태 재사용, signal 없는 shock 분모와 실제 신호 순서, writer 재봉인 시 이전 content hash 제거, entry ask 원천 바인딩, invalid endpoint 뒤 epoch 단절, 잠금호가 포함 때 crossed/clock 유지, 미도달null·known terminal·입력 결손, 학습 전용 선택과 승률 우선/기존 성공 상실 허용을 검증했다. 흡수는 주체의 실제 보충을 증명하는 용어가 아니라 SELL 우세에도 같은 bid가 유지된 관측 특징이다.

**123 tests PASS**, compile/diff·문서 parser/link/owner, strict/잠금호가 결과 재실행 일치, 원천·kernel·캐시와 이전 정책/인계 파일hash 보존을 [최종 검증](../../tmp/samsung-quote-recovery-research-20261004/validation.json)에 남긴다. trading/provider suite·정식 장후 재생성·PID 확인은 수행하지 않았다. 이번 결과는 운영 정책의 적용/경제성 승인이나 다음 영업일 기동 증명이 아니다. 미커밋·미배포다.

산출물:

- [strict 결과](../../tmp/samsung-quote-recovery-research-20261004/strict-run/result.json), [잠금호가 가격 포함 결과](../../tmp/samsung-quote-recovery-research-20261004/locked-run/result.json)
- [원천 품질·동일600초 민감도·양수 사례](../../tmp/samsung-quote-recovery-research-20261004/diagnostics.json), [재현 분석](../../tmp/samsung-quote-recovery-research-20261004/analyze.py), [tests](../../tmp/samsung-quote-recovery-research-20261004/tests.log)

![원천 소비 범위와 같은 종료 시각 가격 비교](../../tmp/samsung-quote-recovery-research-20261004/quote-research.png)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_quote_recovery_research prepare --source tmp/samsung-event-timing-research-20261004/source/manifest.json --output tmp/samsung-quote-recovery-research-20261004/reproduction/strict-source
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_quote_recovery_research prepare --include-locked-price-context --source tmp/samsung-event-timing-research-20261004/source/manifest.json --output tmp/samsung-quote-recovery-research-20261004/reproduction/locked-source
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_quote_recovery_research run --source tmp/samsung-quote-recovery-research-20261004/reproduction/strict-source/manifest.json --output tmp/samsung-quote-recovery-research-20261004/reproduction/strict-run
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_quote_recovery_research run --source tmp/samsung-quote-recovery-research-20261004/reproduction/locked-source/manifest.json --output tmp/samsung-quote-recovery-research-20261004/reproduction/locked-run
```

소요시간/hash 자체보다 고정 사건·신호·선정·비용/가격 결과를 비교한다. `analyze.py`는 최종 strict/locked 고정 경로를 재현한다. 최초4가설 결과 계산 후의 source 계약 대사와 지점 진단/잠금호가 민감도 추가는 계획§6~§7에 구분했다.
