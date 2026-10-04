# 삼성전자 연속 회복 패턴·보유 원천 소비 연구 결과

Owner: `SamsungContinuousRecoverySourceResearch1003`.
계획: [R0–R4](../proposals/samsung-continuous-recovery-source-research-plan-2026-10-03.md).
최종 계산: `tmp/samsung-continuous-recovery-research-20261003/source-02`, `run-02`.

## 1. 결론

**삼성전자 패턴을 더 연구하기 위해 새 종류의 수집 원천부터 늘려야 하는 상황은 아니다.** 별도 collector가 이미 보관한 3일의 체결489,445행·호가334,124행을 발견하여 연구 입력에 연결했다. 10/2는 체결155,605행·호가115,443행이며, Main의160개 판정 중154개에 유효한 직전30초 체결 흐름을 연결할 수 있었다. 기존 판정 snapshot만으로 연구 범위를 판단하면 이 자료를 놓친다.

이 원천으로 지지선·재시험·거래량·매도 뒤 회복·매수 비중·bid 회복을 시험했다. 가격 회복 조건은 일부 목표-first 경로를 선별했고 단순 비교 조건보다 결과가 개선됐다. 그러나 추가 체결 특징이 후단에서도 더 나은 결과를 만드는지는 입증되지 않았고, 고정10분 종료까지 포함한 평균 순가격 경로는 음수였다. **연구 소비 개선의 근거는 확보했지만, 기존 Main보다 낫다고 확정할 새 삼성전자 정책은 확보하지 못했다.**

Main guard를 유지하는 연결에서는10/2 09:43:06의 RECHECK1건을 회수했고 비용 차감 목표에 먼저 도달했다. 이 시도는 [이전 연구 §4](main-machine-decision-cohort-target-first-research-review-2026-10-03.md#4-삼성전자-전체-감시-검증)에도 있던 성공 사례다. 이번에 새 독립 성공으로 늘리지 않는다. 기존 ENTER3건은 모두 미도달이어서 기존 승률은 계산 불가이며, `0%→100%`라고 표현할 수 없다.

## 2. 실제로 추가 소비한 원천

| 원천/연구 단위 | 9/29 | 9/30 | 10/2 |
|---|---:|---:|---:|
| Main 원본 판정 |313|46|160|
| 완료 AL 분봉 |381|381|381|
| 같은 OHLC와 일치하는 보관 거래량 봉 |371|143|368|
| 거래량 또는 OHLC 충돌 봉 |2|0|0|
| 별도 collector 체결 행 |154,165|179,675|155,605|
| 별도 collector 호가 행 |102,450|116,231|115,443|
| 직전 체결 흐름 유효한 분 단위 시점 |310|373|372|
| 직전 체결 흐름 유효한 Main 판정 |257|44|154|
| 직전 호가 흐름 유효한 Main 판정 |221|34|117|
| 과거 정보로 확정한 연구 setup 구간 |22|15|16|

원천 소유자는 다음과 같다.

- Main: `data/report/machine_observation_projection/machine_observation_projection_{date}_0_1.json`. 원본3개 SHA 및 현재 parent `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`를 고정하여 재생했다.
- 완료봉: `data/report/machine_completed_price_source/machine_completed_price_source_{date}.json`. `005930/KRX/KRX_REGULAR/005930_AL` 및 content seal을 검증했다.09:00–15:19의380봉과15:30 종가 봉이며,15:20–29를 보간하지 않는다.
- 체결/호가: `data/observations/scalp_micro_reversion_forward/trade_date={date}/venue=SOR/session=SOR_REGULAR/market{_depth}_stream*.jsonl[.gz]`. manifest의 shard 목록과 실측 파일 hash를 검증했다. manifest byte는 생성/회전 때 기록된 증분 값일 수 있어 파일 전체 크기로 오해하지 않는다.
- 체결·호가의 정확한 계약은 `005930_AL/SOR/SOR_REGULAR`다. Main KRX 정규장 연구에 동일 AL 시장 문맥을 붙인 것이며 KRX 전용 개별 체결로 변환하지 않았다. collector 내부의 동일 epoch만 join했다. 이를 Main runtime epoch의 입력 영수증이나 당시 실제 소비 증거로 대신하지 않는다.
- 위젯3일의 품질·신호와10/2 매매 receipt를 별도 문맥으로 보존했다. NXT 장전 매수10주275,500원·매도10주277,000원의 가격 차이는 존재하지만 실제 net settlement를 새로 입증하지 않았고 Main KRX 학습 성공으로 합산하지 않았다.

### 원천 품질과 결손

10/2 체결12행과 호가17,352행은 연구 품질 조건에서 제외됐다. 체결의 교환/수신 시각 차이 조건 위반은1행이며 나머지는 path eligibility 등의 조건이다. 호가는 bid=ask인 locked 상태17,349행, 시각 조건4행이 포함되고 서로 중복될 수 있다. 정상적인 locked 시장 상태일 가능성을 배제하지 않으며 broker 장애 건수로 해석하지 않는다. 이 연구의 bid 회복 조건은 양의 spread를 요구한다.

9/29는 collector epoch가 체결15개·호가16개로 나뉘었고,9/30과10/2는 각각6개다. epoch 변경과 수신 간격 결손을 넘어 흐름을 이어 붙이지 않았다. 각 epoch 내부 저장 series sequence에는 검출된 건너뜀이 없었다. 이는 **collector 저장 순서 검증**이지 거래소의 모든 체결이 손실 없이 수신됐다는 입증은 아니다.

9/30 Main 관측은11:23 부근에 끝나 보관 Main 완료봉에서 회수 가능한 거래량도143봉뿐이다. 따라서 완료봉 거래량 특징에는 오후 결손이 남는다. 반면 독립 체결 스트림은 종일 존재하여 과거10초/30초 체결량 비율은 별도로 평가할 수 있었다. 두 값을 서로 대체하지 않았다.

Main의 유효한 adverse 수치를 복원한 대량 매도 표시 행은9/29 106·9/30 13·10/2 54개다. 원천 freshness/trusted count와 adverse 상태를 분리한 연구 입력이다. 기존 `source_usable`/대량 매도 실행 guard는 바꾸지 않았다. 프로그램 변화는 같은 유효한 watch admission과180초 이내의 과거 판정에서만 계산한다.

9/29의313판정 중 원래 native identity가 완성된 것은15개뿐이며298개는 결손이다.9/30·10/2는46·160판정이 각각 하나의 fixed-watch admission에 속한다. 연구 가격 구간53개로 native 지원수를 만들어 채우지 않았다. Main 학습 통계에 포함되는 identity 결손 행은 **관측 진단**이며 정식 승격 지원수가 아니다.

## 3. 계산 방법과 비교 범위

1. 완료봉 저점을 오른쪽2개 완료봉 이후에만 확인한다. 당시 과거20분 저항을 고정하고 지지선 이탈·저항 도달·30분 경과·가격 원천 단절에서 구간을 닫는다. 같은 구간의 최초 적격 신호만 채택하고10분 겹침을 제거했다. 결과가 미도달/결손이어도 다음 성공 신호로 갈아 끼우지 않는다.
2. 분 단위 시장 연구는 당시 봉 종가를 가상 시작 가격으로 사용한다. 비용0.33%는 수수료·세금0.23%와 고정 가격 마찰0.10%의 가정이다. 순목표+0.1%와 gross stop−0.7%의10분 선도달을 구분한다. 동일 봉 양 경계 도달은 평가 제외, 미도달의 승패는 null이다. 표의 평균 순경로에는 미도달 시10분 종료 가격 CF를 포함한다. 체결·슬리피지·실현 손익의 검증은 아니다.
3. Main 비교는 현재 정식 경로 계산기와 당시 source-bound 비용을 유지한다. Main 평균은 승패 평가 가능 경로에 한정되고 미도달 값은 null이다. 시장 연구의 전체 종료 평균과 Main 평균을 같은 지표로 합치지 않는다.
4. 후보는 고정 가격 조건에 최대2개 특징을 추가한다.9/29 학습→9/30 후단,9/29~30 학습→10/2 후단을 실행하고, 첫 fold의 선정 조건을10/2에도 바꾸지 않고 적용했다. 최소 연구 학습 승패3개, Wilson 하한→승률→지원수→단순성으로 선정했다. 성공100%/80% 보존 veto는 없다.
5. 시장 연구의 baseline은 **지지선 재시험+직전 완료봉 상승**이라는 연구 비교 조건이다. 실제 Main 기본정책이 아니다. Main 비교의 baseline만 현재 parent ENTER다. 세 날짜는 기존 연구에서 이미 본 자료이므로 시간순 후단도 독립적으로 처음 보는 검증 세트는 아니다.
6. 가격·거래량·복원 Main 특징·연속 시장 특징의24개 fold/방식 비교를 실행했다. 시장 분 단위 입력에는 당시 Main snapshot을 새로 만들지 않았으므로 `restored` 단계는 거래량 단계와 같다. 별도로, 고정된 후보 목록 중 새 특징이 반드시 들어간 후보만 학습으로 선정하여16개 기여도 비교를 추가했다. 후단 결과로 원래 후보를 교체하지 않았다.

## 4. 가격 패턴 결과

| 학습 고정 조건/후단 | 선택 | 목표 먼저 | 손절 먼저 | 미도달/결손 | 조건부 승률 | 평균 순가격 경로 |
|---|---:|---:|---:|---:|---:|---:|
| 비교 조건,9/30 |11|3|1|7/0|75.0%|−0.3181%|
|9/29 선정: 범위 하단35%+직전 상승,9/30 |13|4|1|7/1|80.0%|−0.3068%|
| 위 조건 그대로10/2 |8|2|0|6/0|2/2|−0.2337%|
| 비교 조건,10/2 |7|0|1|5/1|0/1|−0.5219%|
|9/29~30 선정: 고점 대비−0.4% 이하·범위 하단50%·직전 상승,10/2 |6|1|0|5/0|1/1|−0.2279%|

두 후단 모두 가격 회복 조건으로 일부 개선 경로를 골랐다. 그러나 `1/1`, `2/2`는 표본이 매우 적고 나머지 미도달을 제외한 승률이다. 전체 선택의 평가 coverage는 마지막 조건에서1/6이다. 높은 조건부 승률과 전체 선택의 순가격 평균 음수가 동시에 나오는 이유다. 미도달을 실패로 강제 변경하지 않았으며, 비용과10분 종료 결과를 별도로 드러냈다.

추가 원천을 허용한 최종 최상위 후보도 위 가격 조건과 같았다. 새 특징을 **반드시 포함**시킨 별도 비교는 다음과 같다.

| 추가 특징을 포함한 학습 선정 조건 | 후단 | 선택·결과 | 평균 순가격 경로 |
|---|---|---|---:|
| 저점 상승+직전 상승+반등 거래량 비율≥1 |9/30|0선택|계산 불가|
| 같은 거래량 조건 |10/2|3선택,0목표·1손절·2미도달|−0.6842%|
| 확인된 구간+직전 상승+과거 대량 매도 이후1틱 이상 회복 |9/30|10선택,1목표·9미도달|−0.4253%|
| 확인된 구간+직전 상승+직전10초 매수 비중≥65% |10/2|7선택,2목표·1손절·4미도달|−0.3329%|

따라서 현재 후보 문법/관측 시점/비용/10분 결과에서는 **자료를 추가하는 것만으로 가격 조건을 넘어서는 개선을 확인하지 못했다.** 체결·호가가 쓸모없다거나 삼성전자에 수익 패턴이 없다는 결론은 아니다. 이번 계산은 Main 판정 시점과 분 단위 anchor이며, 매도 사건 직후 수초 단위 최초 회복 시점을 별도 진입 anchor로 검색한 연구는 아니다.

![10/2 가격 경로와 고정 연구 조건](../../tmp/samsung-continuous-recovery-research-20261003/samsung-research-comparison.png)

## 5. Main 기계판정으로 연결 가능한 부분

현재 parent 재생에서10/2는 ENTER3·RECHECK111·BLOCK46이다. 모든 원본 경로는 목표-first16·stop-first8·미도달136이며, 이160개는 독립 거래160개가 아니다.

기존 soft-confirmation 회수 prototype의 다른 guard를 모두 통과한 후보는9/29 9·9/30 2·10/2 2시도다. 여기에 학습으로 고정한 `직전 봉 상승 + 과거 범위 하단50%` 조건을 붙이면10/2 09:43:06 한 시도가 추가된다.

- 당시 parent는 RECHECK, 미해결 위험은 `CONFIRMATION_MISSING/no_supported_setup`였고 다른 guard blocker는 없었다. micro 가격 반응+0.091%, 순공격 매수+88이며 기존 유효성/가격 확인 조건을 통과했다.
- source-bound 경로는 비용 차감 목표 먼저, 순경로+0.1%다. trace는 `47bc3705a4b1113ed4f2b58630bfc836588d5fe22e9b1971967589a4d983c60f`.
- 비교 결과는 parent3선택/미도달3 → 후보4선택/목표1·미도달3이다. 원래 fixed-watch admission은 동일1개다. 기존 승률 분모0이므로 승률 개선폭은 null이다.
- 위 성공은 기존 DEPTH_SUPPORTED 연구에서 확인한 동일 시도다. 별도 연구에서 다시 확인되었다고 독립 성공 수를 늘리지 않는다.
- ENTER 필터는9/30의 손절1건을 제외했지만10/2에는 가격 필터가 미도달1건만 남기고, 거래량/체결 필터는0선택이었다. 진입을 모두 없앤 결과를 승률 개선으로 인정하지 않았다.
- 복원 absorption을 추가한 후보도 같은09:43만 회수했고, 연속 체결 특징이 반드시 있는 회수 후보는10/2 추가 회수0이었다.

시장 가격 신호마다120초 이내의 **과거** Main 판정 문맥을 연결한 결과도 `diagnostics.json`에 남겼다. 정확히 같은 시점의 Main 판단·주문 권한이 아니므로 가까운 RECHECK를 임의로 ENTER로 바꾸는 근거로 사용하지 않는다. 위젯 custody 및09:26 이전 Main admission 공백은 [선행 조사](../../tmp/samsung-source-consumption-exploration-20261003/findings.md)의 사실/미입증 구분을 유지한다.

## 6. 다음 접근에서 바꿀 지점

새 API 수집보다 **기존 연속 원천의 소비 시점과 가격 경로 목표 설계**를 먼저 다룰 근거가 생겼다. 삼성전자처럼 틱 단위로 반복 회복하는 자료에서 분봉 확인을 기다리면 이미 이동한 가격과 비용 때문에 남은 이익이 작을 수 있다. 이는 이번 결과에서 나온 후속 가설이며 아직 검증된 원인이 아니다.

다음 실험은 보관된 stream에서 `대량 매도 사건 → 첫 매도 약화/흡수 → 첫1틱 회복`을 과거 정보로 확정한 시점 자체를 anchor로 삼는 방식이 적절하다. 현재의 분 단위 신호와 같은 조건/비용으로 비교하고, 사건 이후 이미 지나간 저점을 진입 가격으로 사용하지 않아야 한다. 이후 고정된 신호에 대한 종료 시점/목표·손절 가정을 별도로 비교해야 진입 조건과 출구 조건 중 어디서 성과가 사라지는지 구분할 수 있다. 이는 이번 R0–R4 이후의 연구 제안이며 현재 정책/OPEN 실행 지시를 추가하지 않는다.

남는 한계는 날짜3일, 반복 탐색으로 사용된 자료, Main의 원래 lineage 결손,9/30 오후 완료봉 거래량 결손, Main runtime에 묶이지 않은 별도 collector epoch, 실제 체결/비용/포지션 종료 증거다. 초기 가격 가설 검증을 위해 이 모두를 새로 수집할 필요는 없지만, 이번 결과를 실제 운영 성능으로 승격할 때 각각의 소유 계약을 건너뛸 수는 없다.

## 7. 리뷰·수정·검증 및 재현

연구 producer는 [scalping의 독립 오프라인 모듈](../../src/engine/scalping/samsung_continuous_recovery_research.py), 회귀는 [표적 테스트](../../src/tests/test_samsung_continuous_recovery_research.py)에 배치했다. 실시간 caller·정책 publisher 연결은 없다.

자체 리뷰 후 다음을 수정하고 전체 연구를 다시 계산했다.

- 오래된 원천의 gzip shard를 읽지 못한 문제: 압축/비압축 동일 파서 회귀 추가.
- admission 결손끼리 프로그램 변화를 연결할 수 있던 문제: 유효한 같은 admission 요구.
- 가격 원천 단절 이전 봉을 저항 구간에 섞을 수 있던 문제: 연속 구간 경계 적용.
- 나중에 회수한 거래량/충돌이 과거 Main 특징을 결정할 수 있던 문제: Main은 자신의 as-of raw capture의 완료봉만 소비. 시장 재구성의 사후 완료봉 원천과 분리.
- 경계 도달 뒤의 원천 결손으로 이미 확정된 결과까지 잃거나,10분 뒤 부분 봉의 경계를 포함할 수 있던 문제: 선도달 이전 연속성 및 완료 시각 경계 적용.
- 중복 수치 조건을 후보 복잡도로 셀 수 있던 문제: 같은 특징/비교의 가장 강한 조건만 남겨 단순성 순위를 정규화. `run-01`은 수정 전 이력이고 `run-02`가 최종이다.

표적 및 인접 연구 회귀 **80 PASS**, compile/diff 검증, 문서 링크/owner/print-only parser를 수행했다. 최종 검증 영수증은 아래 `validation.json`에 남겼다. 원천27파일·연구 kernel7파일 및 보존 대상 정책/인계98파일의 hash를 검사했으며 현재 변경0이다. 마지막 재계산은 원천 준비55.87초·후보 계산2.64초였다.

주요 산출물:

- [고정 입력/특징/원천 census](../../tmp/samsung-continuous-recovery-research-20261003/source-02/projection.json)
- [고정 후보 목록](../../tmp/samsung-continuous-recovery-research-20261003/run-02/frozen-candidates.json), [최종24개 비교](../../tmp/samsung-continuous-recovery-research-20261003/run-02/result.json)
- [특징 기여도16개·선택 시점·Main 문맥](../../tmp/samsung-continuous-recovery-research-20261003/diagnostics.json), [분석 재현 코드](../../tmp/samsung-continuous-recovery-research-20261003/analyze.py)
- [최종 검증](../../tmp/samsung-continuous-recovery-research-20261003/validation.json)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_continuous_recovery_research prepare --output tmp/samsung-continuous-recovery-research-20261003/reproduction/source
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_continuous_recovery_research run --source tmp/samsung-continuous-recovery-research-20261003/reproduction/source/projection.json --output tmp/samsung-continuous-recovery-research-20261003/reproduction/run
PYTHONPATH=. .venv/bin/python tmp/samsung-continuous-recovery-research-20261003/analyze.py
PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_samsung_continuous_recovery_research.py src/tests/test_entry_policy_decision_cohort_research.py src/tests/test_partitioned_pattern_research.py
```

위 재생 명령은 별도 `reproduction` 경로를 사용한다. `analyze.py`는 확정된 `source-02/run-02`의 보충 분석을 재현하며, 원천 준비 소요시간이 들어간 파일 전체 hash 대신 고정 후보·선정·경로 결과를 비교한다.

실제 API/provider 호출·수집 변경·정식 장후 전체 재생성·정책 발행·배포·재기동은 수행하지 않았다. 실현 수익 및 다음 거래일 PID 소비를 새로 검증하지 않았다. 기존10/6 PREOPEN/자연 수용 owner를 닫지 않았다. 코드·계획·연구 결과 범위 완료이며 이번 변경은 미커밋·미배포다.
