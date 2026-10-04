# 삼성전자 기회 계약 복구·고정 후보 재검증 리뷰

Owner: `SamsungOpportunityContract1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
계획: [실행계획](../proposals/samsung-opportunity-contract-reconciliation-plan-2026-10-04.md).

## 1. 결론과 범위

원천 대사와 오프라인 계약 보완을 구현했고 고정한 회복·흡수 후보를 재검증했다. 운영 정책은 선정하지 않았으며 기존 machine parent는 유지한다. 원래의 승리 100%/80% 보존율은 탈락 조건으로 추가하지 않았다.

이번 결과는 `상승 패턴 없음`을 뜻하지 않는다. 10/2의 두 상승 구간은 재현되지만, 가격 연구의 진입과 Main의 당시 판정은 서로 다른 진입·목표·분모다. 또한 삼성전자 전용 fixed-watch에 공통 publisher의 기회 단위를 그대로 적용하면 반복 160관측이 1기회로 묶여 검증 지원 10기회를 충족하지 못한다. 해당 기준을 임의로 낮추거나 가짜 admission을 발행하지 않았다.

범위는 보관 9/29·9/30·10/2 원천의 격리 연구·구현·코드리뷰다. 실제 주문, provider/API 호출, 수집 확대, runtime 정책 publication, 배포 및 재기동은 0이다. Main·Widget·manual custody를 분리했다. 실현 PnL 및 실제 PID 소비를 주장하지 않는다.

## 2. 구현과 원천 연결

- 구현: [오프라인 생산자/소비자](../../src/engine/scalping/samsung_opportunity_contract_research.py), [회귀](../../src/tests/test_samsung_opportunity_contract_research.py).
- 원생산자: `ai_decision_trace.capture_machine_observation`, pipeline 및 AI trace의 정확한 machine hash/attempt/원 snapshot 연결, append-only `OrderOwnerRegistry`.
- 기존 projection·원 capture·정책·선행 연구 kernel을 변경하지 않는다. 새 `lineage.json`이 별도 sidecar로 원 native와 복구 판정을 남긴다.
- 새 source adapter는 전체 캡슐이 JSON 문자열인 경우도 보존한다. 원 machine hash, `original_machine_observation_sha256`, `recheck_first_machine_observation_sha256`, 원 machine parent snapshot을 포함한다. 갱신된 AI snapshot을 원 machine snapshot으로 대체하지 않는다.
- 캡슐은 canonical capture의 trace·attempt·snapshot·시각·bundle·종목·venue/session과 대사한다. 늦게 append된 캡슐도 원 as-of identity가 정확해야 한다. 다른 시각·현재 DB·근접 종목/날짜로 metadata를 채우지 않는다. malformed/authority/conflict는 명시적으로 제외한다.
- 종료/재진입 검증 계약은 실제 Main 소유권·동일 position/native cluster·행 단위 source·시각 순서·잔량 0·pending/late fill 해결·다음 진입 guard를 요구한다. 파일 hash만 맞거나 Widget 종료가 있다는 이유로 Main flat을 만들지 않는다. 현재 원천에 이 새 계약을 발행하는 native episode producer가 등록되어 있지 않아 실제 episode 지원을 새로 발행하지 않는다.
- child selector는 `005930 + MAIN_FIXED_WATCH + KRX + KRX_REGULAR`, 대상 날짜·정상 admission/generation·parent hash·15:30 expiry를 확인한다. 해당하지 않거나 입력이 부족하면 parent다. 이는 오프라인 검증 계약이고 실제 loader/publisher 등록은 없다.

## 3. C1 — 결손 298건 처분

검사 대상은 canonical mechanical capture 519행, 삼성전자 pipeline 209,908행 및 AI trace 496행이다. 날짜별 pipeline/trace는 아래와 같으며 다른 venue/session의 행도 원 census에서 제외하지 않았다. 최종 분석 대사는 기존 KRX regular 519행으로 제한한다.

| 원천 날짜 | Pipeline | AI trace | KRX regular capture | 보존된 native 판정 | 복구된 native |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9/29 | 26,332 | 128 | 313 | 15 | 0 |
| 9/30 | 107,401 | 90 | 46 | 46 | 0 |
| 10/2 | 76,175 | 278 | 160 | 160 | 0 |

9/29의 298행에는 원 `label_context`·capture top-level·exact payload에 당시 watch admission/generation 또는 scanner promotion이 없다. 12행은 `zero_base_probe_result`에서 원 machine hash 7건·first-recheck hash 5건으로 정확히 연결된다. 이 12행도 native watch/scanner ID를 갖고 있지 않다. 나머지 286행은 검사한 정확한 참조에서 native 보완 증거를 찾지 못했다. 298행 전체를 사전 승격 probe라고 추정하지 않는다.

따라서 298행은 `native_not_recorded_in_original_capture_and_exact_receipts`로 유지한다. 새 native 0, 충돌로 제외된 native 0이다. 각 판정에는 원 capture 경로/hash/행, 연결된 receipt, 원·해결 native, 제외 사유를 남긴다. 캡슐이 원천에 없다는 사실을 캡슐 검증 오류와 혼동하지 않는다.

## 4. C2 — 실제 Main과 Widget 구간

Order-owner journal 전체 체인을 검증한 뒤 삼성전자 3일의 owner/order 기록을 별도로 추출한다. 확인된 매수·매도 체결 2건 및 terminal 2건은 10/2의 Widget 소유다. Main의 실제 체결/flat/rearmed를 증명하는 삼성전자 receipt 및 새 native episode proof는 발견하지 못했다. 실제 Main closed episode 지원은 0이다.

Read-only DB snapshot의 삼성전자 recommendation 26행은 `buy_qty>0` 및 `buy_time`이 모두 0이다. 이는 현재 inventory이며 과거의 무주문/flat 증명으로 쓰지 않는다. fixed-watch 3행의 admission/generation은 현재 AFTERMARKET 값으로 갱신되어 있어 9/30·10/2 KRX regular capture의 당시 ID와 다르다. `main_fixed_watch`는 session generation 변화 때 DB admission을 갱신한다. 이 현재 값을 과거에 소급하면 잘못된 native가 된다.

현재 buy-fill receipt 디렉터리의 2개 파일은 047040/066570이며 삼성전자의 Main 실체결 지원으로 사용하지 않았다. Widget coexistence policy가 있다는 이유로 Widget 보유를 Main의 일괄 금지 조건으로 추정하지도 않았다.

가격 replay의 modeled terminal/cooldown으로 재진입 사건을 계산하는 연구는 계속 허용한다. 그 사건을 실제 flat/custody 또는 새로운 독립 native 기회로 바꾸지 않는다. 여러 사건이 같은 watch admission이면 원 native cluster와 fold를 보존한다.

## 5. C3 — 고정 후보의 재검증

### 5.1 가격 경로

원 signal, 비잠금 ask 진입/bid 종료, 비용 0.23%, net target +0.1%, gross stop −0.7%, 20분 관측, terminal 후 cooldown 60초를 고정했다. 이번 identity 복구 여부로 신호·비용·종료를 바꾸지 않았다.

| 날짜 | 회복: 확정 양수/확정 전체, 검열 | 회복 평균 net CF | 흡수: 확정 양수/확정 전체, 검열 | 흡수 평균 net CF |
| --- | --- | ---: | --- | ---: |
| 9/29 | 2/2, 검열 1 | +0.13866% | 1/1, 검열 1 | +0.13900% |
| 9/30 | 1/2, 검열 1 | −0.40984% | 1/2, 검열 1 | −0.41016% |
| 10/2 | 2/2, 검열 1 | +0.13530% | 2/2, 검열 1 | +0.13563% |

10/2 회복·흡수는 같은 두 상승 구간이다. 두 후보를 더해 4개의 독립 성공으로 세지 않는다. 9/30에는 손절-first가 있어, 10/2의 조건부 100%만으로 모든 날 성능 우위를 주장할 수 없다. 검열은 실패 0으로 채우지 않는다. 모든 가격 metric은 선행 frozen-strict와 같으며 실제 fill/PnL이 아니다.

### 5.2 당시 Main 판정과 고정 adapter

`base_recovery:300:5:soft_add`와 `absorption_release:900:5:soft_add`를 고정한다. 원 binary label·hard guard·cost binding을 유지해 현재 publisher가 사용하는 동일 native-group metric으로 계산한다.

삼성전자 전체 원 origin 비교에서는 기존·두 후보 모두 학습의 유효 native 6기회/6시도·승리 3건·승률 50%가 유지됐다. 회복은 유효 binary가 아닌 추가 미확정 관측 1개, 흡수는 native 없는 관측 1개를 더한다. 이는 새로운 검증 승리가 아니다. 기존 Main의 10/2 ENTER 3건은 모두 `neither_boundary_hit`, binary=null이므로 기존·후보의 후단 승률은 null이다.

삼성전자 전용 child의 분모에서는 9/29 scanner 및 unknown origin을 제외한다. fixed-watch 206행은 학습 9/30의 1native, 검증 10/2의 1native다. 기존 ENTER의 학습은 확정 stop-first 1건, 검증은 위의 미도달 3건이다. 회복 adapter는 학습의 미확정 1행을 추가하지만 기존·두 adapter 모두 확정 학습 승률은 0/1=0%, 후단은 null로 같다. 전체 origin의 승률을 전용 child 승률이라고 보고하지 않는다. 가격 후보의 2/2와 Main의 0/1 또는 null은 진입과 목표·분모가 달라 직접적인 우열 수치가 아니다.

### 5.3 발행 계약의 구조적 제약

현재 `_winrate_successor_hurdles_valid`는 학습 native ≥30, 후단 native ≥10, raw 승률 개선, support-adjusted +5%p 개선, coverage ≥50% 및 시간순 분리를 요구한다. 승리 보존율 veto는 없다. 날짜는 최소 1학습 날짜+1후단 날짜 계약이며 과거 문서의 3/2일·80% 보존 문구를 재도입하지 않았다.

삼성전자 전체 원 origin의 native 상한은 학습 16/후단 1, 전용 fixed-watch는 학습 1/후단 1이다. 실제 유효 binary 지원은 더 작다. **같은 admission/generation을 유지하는 삼성전자 fixed-watch는 한 후단 날짜에 1native로 묶이므로, 해당 관측 횟수만 늘려 후단 10기회를 충족할 수 없다.** 실제 재진입 episode가 발견돼도 같은 cluster의 독립 지원을 자동으로 10개로 만들지 않는다.

이것은 데이터의 가격 패턴 결손과 별개의 policy contract 적합성 문제다. 삼성전자 전용 정책은 실제 사용할 관측 기회·episode·상관 cluster·학습/후단·guard/cost 단위를 정한 별도 계약이 필요하다. 공통 전체종목 publisher 기준을 이번 코드에서 임의로 바꾸지 않았다. 현재 child selector는 미등록, 이미 탐색한 날짜들은 pristine holdout이 아니며 공식 candidate=null이다.

## 6. 리뷰와 검증

리뷰에서 문자열 캡슐 누락, first-recheck 및 원 machine snapshot 연결 누락, 새 authority가 선행 writer 값에 덮이는 문제, 행 hash만으로 실제 종료를 인정할 위험, 동일 종목 scanner/fixed-watch 비교 분모 혼합, 빈 selector/과거 날짜/불완전 admission 허용, malformed receipt 처리와 코드 freeze 시각 문제를 보완했다.

- 표적 회귀: 새 연구 계약, 선행 policy-episode, native validator, auxiliary source contract의 **205 tests PASS**. 개선 후보가 기존 승리의 80% 미만을 보존해도 현재 승률/support/coverage 기준을 통과하는 회귀를 포함한다.
- Python compile·tracked 및 신규 파일 whitespace 검증을 시행했다.
- 최종 격리 cold/warm의 `result.json`, `lineage.json`, `price-revalidation.json` 세 파일 content가 모두 일치한다. 새 source/kernel 155hash 및 기존 정책/인계 98hash, 선행 strict 131hash·prior-day 142hash를 각각 검증했다. 가격 metric은 기존 frozen-strict와 날짜/조건별로 일치한다.
- local link·단일 owner·print-only parser와 최종 receipt는 `tmp/samsung-opportunity-contract-20261004/validation/closure.json`에 기록한다. 기존 10/6 checklist와 정책/인계 artifact는 보존한다.
- 선행 연구의 `validation/closure.json`에 봉인했던 10/4 checklist hash는 새 owner 추가 이후 과거 검증 기록이다. 이번 완료 문서의 hash는 새 closure에서 검증한다. 이를 현재 strict/PREOPEN/PID 증명으로 사용하지 않으며 10/6 trading handoff를 재생하지 않았다.
- 실제 publisher 호출, 광범위 장후 automation, trading suite, provider/API 및 Project/Calendar sync는 실행하지 않았다. 테스트 PASS가 자연 원천·정책 선정·배포/PID·경제성 PASS를 뜻하지 않는다.

## 7. 결과 owner와 종료 기준

이번 원천 대사·오프라인 계약 구현 owner는 `SamsungOpportunityContract1004`다. 원 native 결손은 새 lineage sidecar, source provenance는 sealed manifest, 고정 후보 비교는 result/price-revalidation에 소유된다. 기존 10/6 PREOPEN 및 자연 수용 owner는 그대로 보존한다.

현재 3일의 원 receipt로 새 native/실제 Main episode를 복구하지 못했고 고정 후보의 Main 승률 분모도 개선되지 않았다. 같은 데이터에 임의 시간 bucket을 붙이거나 동일 조건을 반복해 후보를 발행하는 연구는 종료한다. 후속은 추가 raw 수집 요구가 아니라 **삼성전자 fixed-watch 전용 평가 단위와 발행 계약의 설계**다. 그 계약에는 반복 episode와 상관 cluster를 함께 공개하고, 관측 가격 CF와 실제 Main guard/진입·비용을 같은 비교 분모로 연결해야 한다. 현 자료에서 실제 손익 우위를 이미 확보했다고 간주하지 않는다.

## 8. 실행 및 재현 receipt

최종 source: `tmp/samsung-opportunity-contract-20261004/accepted-source/manifest.json`.
최종 비교: `accepted-cold/result.json`, `accepted-warm/result.json`, 같은 디렉터리의 `lineage.json` 및 `price-revalidation.json`.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_opportunity_contract_research --prepare --db-snapshot tmp/samsung-opportunity-contract-20261004/intake/db-recommendation.json --output tmp/samsung-opportunity-contract-20261004/accepted-source
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_opportunity_contract_research --intake tmp/samsung-opportunity-contract-20261004/accepted-source --output tmp/samsung-opportunity-contract-20261004/accepted-cold
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.samsung_opportunity_contract_research --intake tmp/samsung-opportunity-contract-20261004/accepted-source --output tmp/samsung-opportunity-contract-20261004/accepted-warm
```

이는 실제 실행 receipt의 명령이다. 같은 output을 덮어쓰지 않는 gate가 있으므로 재현 시 새 격리 output 이름을 사용한다. DB snapshot은 읽기 전용 트랜잭션으로 해당 종목/날짜만 조회한 inventory이며 위 CLI는 DB 접속을 수행하지 않는다. 임시 최초/중간 계산은 최종 판정 owner가 아니다.

현재 선택물의 KRX regular machine parent 및 10/6 dated parent는 모두 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`다. effective bundle은 `6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87`, dated bundle은 `3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99`다. bundle과 machine parent를 구분하며 현재 PID 소비는 이번 연구에서 점검하지 않았다.
