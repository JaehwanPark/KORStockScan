# 삼성전자 사건 직후 진입 시점 분리 연구 결과

Owner: `SamsungEventTimingIsolation1004`, [실행계획](../proposals/samsung-event-timing-isolation-and-exit-research-plan-2026-10-04.md), [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
최종 사건/비교: `tmp/samsung-event-timing-research-20261004/source`, `run-01`.

## 1. 결론과 3번 진행 판단

**1·2번을 완료했고, 3번 종료 조건 실험의 사전 진행 조건은 충족되지 않았다.** 학습9/29~30에서 고정한 `sell_decay`를10/2에 적용했을 때 동일 사건21개에서 사건 직후 진입의 가격 경로 평균은 다음 분 경계보다−0.1295%p 낮았고, 추가 목표-first0개·잃은 목표-first1개였다. 따라서 종료 조건 후보18개를 실행하지 않았다. 사후에 다른 recipe로 교체하여 진행 조건을 통과시키지 않았다.

다만 이 차이를 실제 매수 시점의 손익 차이로 해석할 수는 없다. 호가로 다시 대사하니 ‘500원 회복’ 신호 대부분이 **bid/ask 상승 없이 마지막 체결가가 bid에서 ask로 바뀐 경우**였다. 동일 사건15개·동일 종료 시각에서 양쪽 진입을 같은 ask 기준으로 맞추면 평균 차이는+0.0002%p로 거의0이었다. 이번 결과가 지지하는 결론은 **단순 체결가 최초 회복의 진입 우위가 미입증이며, 가격 변화 특징에 거래 방향과 호가 변화가 섞여 있다는 것**이다. 다음 분을 기다리면 실제 주문 수익이 개선된다는 정책 증거는 아니다.

새 원천 수집을 늘리기 전에, 기존 체결·호가에서 bid/mid 자체의 회복과 동일 가격 흡수를 구분할 근거를 확보했다. 이는 새 정책 선정이나 Main guard 변경으로 이어지지 않았다.

## 2. 사건 재구성과 입력

| 항목 |9/29|9/30|10/2|
|---|---:|---:|---:|
| 보관 체결 행 |154,165|179,675|155,605|
| 대량 매도 사건 |318|359|349|
| 최초500원 회복 신호 |299|350|318|
| 매도 약화+회복 신호 |288|336|309|
| 흡수+회복 신호 |284|337|310|
| 약화 또는 흡수+회복 신호 |293|344|315|
| recipe별 겹침 제거 선택 사건 |25|26|26|

총1,026개 원천 사건이다. recipe별77개 선택을 합쳐308개 독립 거래라고 세지 않는다. 사건 ID는 원래collector epoch·series sequence에 묶인 연구 ID이고 Main native admission/정식 지원수를 새로 만들지 않는다.

원천은 `005930_AL/SOR/SOR_REGULAR`의 normalized retained stream이다. 이를 Main KRX 전용 체결로 바꾸지 않았다. 사건은 직전60개 체결의95분위·중앙값3배 및 최소20개 이전 체결로 정의했다. 현재 SELL량은 과거 분포 계산에서 제외한다. 사건60초 동안 관측된 저점에서500원 이상 회복한 최초 수신 시점을 저장하고, 미래 저점으로 그 시점을 바꾸지 않는다.500원은 고정 연구 가격 경계이며 모든 observed price의 실제 거래소 호가단위를 인증하는 값이 아니다.

약화/흡수는 사건 이후10초와 그때까지의 연속된 두5초 창을 사용한다. 동일 사건의 즉시 진입, 다음 분 경계 이후 첫 관측, 기존 분봉 조건의 최초 확인을 비교한다. 원래 사건 시작에서842초를 예약해 최대 확인 지연과10분 결과창이 겹치지 않도록 했다. 첫 신호의 결과가 결손이어도 이후 성공 사건으로 대체하지 않았다.

원천 준비19.87초·비교 계산2.91초였다. 이전 완료봉 연구 projection과 그 원천28파일, 연구 kernel8파일을 봉인했다. 보충 호가는 이전 연구와 같은 manifest/shard reader를 사용했으며 새 API/WebSocket 호출이나 broker parser/FID 변경은 없다.

## 3. 학습 고정과 동일 사건 비교

학습9/29만 사용할 때 각 recipe의 전체10분 유효 원천에서 승패가 확인된 표본은1~2개로, 사전 최소3개를 충족한 후보가 없었다. 따라서 이 fold는 `recipe=null/insufficient_research_support`다.9/30에 실제 원천 신호가0개였다는 뜻은 아니다. 고정4개 가설의 날짜별 진단은 별도로 보존했다.

학습9/29~30에서의 `sell_decay`는51선택·전체 가격 경로30개·목표3/손절4·미도달23이며 조건부 승률3/7, 평균 순가격 CF−0.4549%였다. Wilson 하한→승률→지원수→단순성으로 이 recipe를 고정했다. 성공100%/80% 보존 veto는 없다. 후단10/2에서 recipe를 재선정하지 않았다. 세 날짜는 이미 탐색한 자료이므로 새 독립 holdout은 아니다.

|10/2 동일 사건21개 |첫 회복 즉시|다음 분 경계|
|---|---:|---:|
| 목표 먼저 |2|3|
| 손절 먼저 |1|0|
|10분 미도달 |18|18|
| 조건부 승률 |2/3|3/3|
| 전체 경로 평균 순가격 CF |−0.3987%|−0.2691%|

두 arm 모두 같은 ordered trade stream·비용0.33%·순목표+0.1%·gross stop−0.7%·각 entry 이후10분을 썼다. 첫 경계를 넘은 관측 가격 또는10분 종료 관측 가격을 가상 exit 가격으로 사용했다. 실제 fill을 추정하지 않는다. 미도달은 binary null이며, 종료 가격 CF로 승패를 다시 분류하지 않는다.

다음 분 경계의 평균 대기는25.06초다. 즉시 진입의 관측 체결가는 다음 분 관측 체결가보다 평균 약0.0647% 비쌌다. 목표 추가0·목표 상실1이지만 이것을 기존 성공 보존 veto로 쓰지 않았다. 사전 진행 조건에 요구한 평균 가격 CF 우위 및 목표 우위가 모두 없다는 판단이다.

### source 결손과 선택 분모

10/2 `sell_decay` 선택26개 중5개는 전체10분 원천이 부족했다: path eligibility1·collector epoch 변경3·저장 stream 종료1. 남은21개만 동일 사건 주 비교에 사용했다.9/29는25선택 중15개가 같은 기준에서 제외됐다: path eligibility1·epoch 변경6·exchange/receive clock7·종료 가격 freshness1.9/30은26선택 중6개가 제외됐다: epoch 변경4·clock1·stream 종료1.

전체10분 원천 검사와 경계 도달 전 검사도 구분했다. 경계 도달 뒤의 결손으로 이미 관측한 목표/손절 결과를 삭제하지 않고 `censored_known_terminal`에 남겼다. 주 비교는 결과 경계와 독립적인 전체 원천 연속성을 요구하여, 빨리 이긴 시도만 결손 창에서 살아남는 선택 편향을 막았다. 알려진 exit까지만 요구한 보충 비교에서도10/2의 차이는 같은−0.1295%p였다.

기존 고정 분봉 조건 `past_up + range_location≤0.35`를180초 안에 기다린 arm은26건 중4건에서 entry가 존재했다. 나머지는 확인 조건 미도달21건·입력 미성숙/불가1건으로 분리했다. 이를22개 broker 실패나 체결 원천 결손으로 표시하지 않는다.4개 동일 사건 비교에서 분봉 확인 대기의 평균102.30초, 즉시−확인 평균 CF−0.1813%p였지만 분봉 조건까지 추가되므로 순수 시점 변경과 동일하게 해석하지 않는다.

## 4. 호가가 보여준 체결가 회복의 의미

저점과 신호 시각의 호가는 각각 해당 수신 시각 이전·1.5초 이내·같은collector epoch·유효한 bid<ask인 마지막 normalized depth만 연결했다. 미래·stale·다른epoch 호가를 대신 사용하지 않았다.

| `sell_decay` 선택의 호가 대사 |9/29|9/30|10/2|
|---|---:|---:|---:|
| 저점/신호 호가 비교 가능 |22|19|20|
| 체결가 회복에도 bid 미회복 |21|19|20|
| 동일 bid/ask에서 bid 체결→ask 체결과 일치 |21|18|20|
| bid 회복 중앙값 |0원|0원|0원|

10/2 수치는 **전체26개 신호 중 호가 비교 가능한20개**다. 주 paired21개와 같은 분모가 아니다. 주 paired 안의 호가 비교 가능 사례는17개다. 남은 호가 결손을 성공/실패나 bid 상승으로 추정하지 않는다. 이 상태는 spread 내 체결 방향 변화와 일치한다는 근거이며, 신호의 모든 원인을 유일하게 입증하는 것은 아니다.

예를 들어09:00:20의 원천은 저점 체결273,000원·회복 체결273,500원이지만 양 시점의 bid273,000원·ask273,500원은 같았다. 가격 자체의 상승 확인 없이 마지막 체결가만500원 올랐다. 해당 신호는 주 전체10분 source-comparable 집단에는 포함되지 않았으며, 가격 특징의 의미를 설명하는 원천 예시다.

### 진입 가격 기준과 종료 시각까지 맞춘 보충 비교

| 같은10/2 사건15개·같은 절대 종료 시각 |즉시−분 경계 평균 차이|
|---|---:|
| 양쪽에 관측 체결가를 사용 |−0.0906%p|
| 양쪽 BUY는 관측 ask·공통 종료는 관측 bid |+0.0002%p|

같은15개에서 양쪽 진입 ask가 동일했던 경우는13개다. 양쪽에 같은 비용을 적용하므로 이 차이에서 비용 상수는 소거된다. 같은 종목·사건·절대 종료 가격·매수 호가 기준에서 시점 우위가 거의 사라졌다. 따라서 원래의−0.1295%p를 ‘더 빨리 실제 매수하면 그만큼 손해’라고 단정하지 않는다. 그 값에는 마지막 체결가 기준과 각 entry 이후10분 종료 시점 차이가 포함되어 있다.

이 보충 비교는 고정 시간 종료의 quote-price CF이며 순목표/손절을 새로 평가한 정책이 아니다. 연구의 주 recipe나3번 조건을 유리하게 재선정하지 않았다. 실제 매수·매도 체결량·주문 경로·net settlement는 검증하지 않았다.

![동일 사건 진입 시점 비교](../../tmp/samsung-event-timing-research-20261004/timing-comparison.png)

## 5. 종료 조건 연구의 상태와 다음 의미

사전3번 조건은 후단 paired3개 이상, 즉시 평균 CF 우위, 추가 목표 또는 더 높은 목표 도달 비율이었다.10/2는 표본 조건21개를 충족했지만 나머지가 미충족이다.9/29 학습 fold는 후보 자체가 없었다. **종료 연구 실행0·정식 후보 발행0**으로 닫는다. 설계된18개 종료 조합을 실행했다고 표시하지 않는다.

이번 연구로 삼성전자 수익 패턴이 없다고 결론내리지 않는다. 평가한 것은 대량 매도 뒤 체결가500원 회복을 먼저 포착하면 유리한지라는 가설이다. 그 신호에는 bid/ask 간 체결가 이동이 많이 섞였다. 후속 가설은 기존 호가에서 **bid/mid의 실제 상승·흡수 지속·그 뒤의 첫 적격 진입**을 과거 정보로 확인하는 방식이다. 별도 연구라면 현재4개 가설과 이번 음의/중립 결과를 보존해야 하며, 같은 자료를 새로운 독립 검증으로 부를 수 없다. 현재 코드나 실시간 정책에 이 조건을 추가하지 않았다.

## 6. 리뷰·검증과 재현

연구 producer는 [scalping의 독립 모듈](../../src/engine/scalping/samsung_event_timing_research.py), 회귀는 [표적 테스트](../../src/tests/test_samsung_event_timing_research.py)다. review-gate에 따라 구현·자체 리뷰·수정·재리뷰·표적 검증을 완료했다. 주요 보완은 동일 수신 timestamp에서 과거 sequence로 되돌아갈 수 있는 join 방지, source seal의 읽기 전/후 hash 검증, 연구 authority가 상위 writer 기본값에 덮이는 문제, 종료 조합의 동일 source population/freshness, 예약 창의 최대 수신 지연, source gap 원인을 종료 시각 이후 epoch에서 가져올 수 있는 진단 수정이다.

표적 및 인접 연구 **97 tests PASS**, compile/diff·문서 link/owner/print-only parser, 후보 재실행 결과 일치 검증을 수행했다. 원천/캐시·kernel·정책/인계 hash 검증은 [최종 영수증](../../tmp/samsung-event-timing-research-20261004/validation.json)에 남겼다. 이전 미커밋 연구와10/6 PREOPEN/자연 수용 owner를 보존했다. 실제 API/provider·정식 정책 재생성/발행·배포·재기동은 수행하지 않았다.

산출물:

- [봉인 원천·사건 캐시 manifest](../../tmp/samsung-event-timing-research-20261004/source/manifest.json)
- [학습 선정·동일 사건 주/보충 비교·조건부3번 판단](../../tmp/samsung-event-timing-research-20261004/run-01/result.json)
- [호가/동일 종료 시각/가격 기준 대사](../../tmp/samsung-event-timing-research-20261004/diagnostics.json), [보충 분석 재현](../../tmp/samsung-event-timing-research-20261004/analyze.py)
- [테스트 결과](../../tmp/samsung-event-timing-research-20261004/tests.log)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_event_timing_research prepare --output tmp/samsung-event-timing-research-20261004/reproduction/source
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_event_timing_research run --source tmp/samsung-event-timing-research-20261004/reproduction/source/manifest.json --output tmp/samsung-event-timing-research-20261004/reproduction/run
PYTHONPATH=. .venv/bin/python tmp/samsung-event-timing-research-20261004/analyze.py
PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_samsung_event_timing_research.py src/tests/test_samsung_continuous_recovery_research.py src/tests/test_entry_policy_decision_cohort_research.py src/tests/test_partitioned_pattern_research.py
```

새 재생은 별도 `reproduction` 경로를 사용한다. `analyze.py`는 고정 `source/run-01`을 재현한다. 소요시간 때문에 artifact 전체 hash가 달라질 수 있으므로 고정 사건·recipe·선정·가격 결과를 비교한다. 이번 변경은 미커밋·미배포다.
