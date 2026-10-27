# 정규장 비상시 원천·기계 선택·추가 패턴 기여 검토 — 2026-10-27

## 결정

우선 보완 대상은 **비상시 원천의 판정 도달과 극소수 100% 정책에 고정되는 기계 선택 방식**이다. 보조 프롬프트만 바꾸어 해결할 상황은 아니다. 적격 등록 패턴 WIN 구간820개 중 현행이 포착한7개를 재현했다. 820개는 이미 원천·후행 라벨이 있는 연구 구간이므로 그 안의 미선택813개를 오늘 원천 수신 결손 때문이라고 설명해서도 안 된다.

새 패턴을 추가하면 승리 포착은 늘지만 실패도 늘어난다. 따라서 이번 결과로 전면 적용하지 않는다. 저가형의 반전 유지 A05/A09, 고가형의 돌파 유지 A12/상승구조 A14를 대조할 가치가 있다. 중가형은 가장 높은 단일 추가 후보도 누적36.3%여서 광범위 완화 근거가 약하다. 모두 회고적 탐색 결과이며 수익 보장·실제 놓친 주문 수가 아니다.

실행 owner는 기존 [MachinePatternOpportunityResearch1023·MainEntrySourceTerminalRepair1022](../checklists/2026-10-27-stage2-todo-checklist.md)다. [보완계획 §8](../proposals/main-auxiliary-spread-liquidity-and-deadline-remediation-plan-2026-10-27.md#8-정규장-비상시-추가-패턴-비교-완료와-보완안)으로 연결한다. 운영 코드·정책·provider·주문·배포·재기동 변경 및 신규 AI 호출은 모두0건이다.

## 1. 오늘 원천과 판정 도달

[13:50:14 KST 관측](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/live-review.json), [집계](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/live-summary.json): 릴리스 `6d0d197562c67ebdf5cd3524e71001c5257eb603`, PID670131/start71972259, cwd `probe-latency-20261027-6d0d19756/src`다. 읽기 전후 selector와 start ticks가 같다. 이후 운영 상태를 이 시각에 소급하지 않는다.

현재 PID에 consumer/native receipt로 연결된 비상시59탐침·58종목·59고유 lease를 대조했다. 모두 해당 소비자의 상시5종목 밖이며 exact item `_AL`, session `KRX_REGULAR`, 자료 route `krx_nxt_integrated`/native SOR다. 종목별 broker ACK는59건 모두 unknown이다. 로컬 REG 송신 또는 연결 단위 success를 종목별 수신 보장으로 쓰지 않는다. 실제 주문 요청·체결 거래소는 여기서 확인한 것이 아니다.

| 단계·결과 | 현 PID 관측 |
|---|---:|
| 비상시 탐침 종료·consumer 결속 | 59 |
| exact lease에 0B 수신 | 39 |
| exact lease에 0D 수신 | 40 |
| 0B·0D 모두 미수신 | 19 |
| native 기계 조건 평가 receipt 도달 | 35 |
| 선택 branch의 이력 TRUE / ready | 0 / 0 |
| 당일 보존 prefix의 정규장 비상시 기계 capture / AI trace | 0 / 0 |

0B39와0D40은 같은59건에서 본 서로 겹치는 수치다. native35건의 관측 구간은61.6~148.5초다. native receipt 도달은 ENTER 또는 전체 필수 입력 충족과 같지 않다.

| 원 종료 이유 | 건수 | 구분 |
|---|---:|---|
| route_snapshot_missing | 19 | 같은 lease의0B·0D 모두 미관측 |
| 0B_age_exceeded | 4 | 수신했으나 현재성 부족 |
| 0B_missing | 1 | 0D 수신, 0B 미관측 |
| native_history_observed_current_source_stale | 16 | 과거 native 이력 있음, 종료시 현재성 부족 |
| native_history_observed_with_source_gap | 3 | 이력 중 원천 공백 |
| native_source_stale_or_absent | 1 | native 원천 미충족 |
| native_observation_no_matching_pattern | 13 | 선택 패턴 불일치 |
| confirmation_pending_at_residence_end | 2 | 관측 종료까지 확인 미완료 |

분류로는 source_unavailable25, observation_incomplete21, pattern_not_matched13이다. 이를59건의 AI 오차단이나 놓친 승리로 세지 않는다. 현재 선택 조건으로 실제 TRUE가 없다는 증거와, 미선택 패턴을 켰으면 TRUE/후행 WIN이었을지의 증거는 다르다. 후자는 이59건에 아직 결속하지 않았다.

09:00 이후 전체 PID 탐침584건은 native bounded window reader로 읽었으며 요청 창 covered, malformed0, tail truncation0이다. 원 source1.215GB 전체를 재스캔하지 않고 index 약11.35MB와 tail0.51MB를 읽었다. 당일 비상시 AI3건은 모두 PRE/NXT이며 정규장 성과에 합치지 않는다.

동일 PID의 별도 [timestamp 원본 대사](../../tmp/probe-latency-integration-20261027/capability-complete/timestamp-delay-reconciliation.json)는13:28:04~05의350거부행에서 거래소 시각→앱 수신10.309~18.560초, 수신→정규화0~120ms를 보여준다. 이것은 그350행의 근거이며59탐침 전부의 원인을 설명하지 않는다. 상류·네트워크·수신 스케줄링 중 책임 지점은 미확정이다. 원 stale guard/5초 기한을 늘려 덮지 않는다.

## 2. 누적 모집단·분모와 정확한 연결

- [source26 machine](../../data/report/continuous_reversal_operating/2026-10-26/machine.json) content SHA `de3fb27fc5a0845f39090db31202fe5ab1309931914fbfbfd2334cd674d712b4`를 사용했다. 현재 bundle `6b93eb6a16efc2a7a349fcdbd347146200830034d5697564a6500e3ed2472f92`의 operating manifest와 같고, 현 PID consumer의 family `232d15a673780559864f0e5adbae1d13deb184f3b11162a0e2a50c309e3a4ef0`와도 같다. [결속 영수증](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/policy-binding.json)을 보존했다.
- 범위는 원 계약의 `other_non_fixed|REGULAR|가격유형|SOR`다. 가격유형은2만원 미만/2만~10만원/10만원 이상이다. 이것을 업종·유동성 유형으로 바꾸지 않았다. 과거 전체 행의 실제 watch/attachment 이력 전수 검증은 별도이며, 원 정책 cohort 귀속과 오늘59건의 실제 consumer 귀속을 구분한다.
- 09/29 이후 적격10일, 91,435개 고유 확인점: WIN12,659 / STOP647 / TIMEOUT46,290 / 미확정31,839. 확정분모59,596이다. 동일 key의 패턴 중복을 합집합으로 제거하고 conflict0을 확인했다.
- 유효 날짜:09/29·30,10/02·06·07·08·21·22·23·26. 10/12·14·15·16·19·20의 정규장2,491,728행은 원 생산자의 `source_epoch_unverified`로 제외됐고10/13은 현 normalized manifest에 없다. 이 범위에 기회가 없었다고 판단하지 않는다. [기존 원천 점검](main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#1-원천과-모집단의-한계)을 유지한다.
- 라벨은 원 계약의 entry ask→후행 거래가격, 비용0.0023, 비용 후+0.4%, −3% 선도달 없음,1800초다. native tick71,576점과 원 생산자가 허용한 same-item completed-bar 보강19,859점을 구분했다. 유형·후보별 원천종류별 성적도 verification에 보존했다. 실제 bid 청산·체결·실현손익의 증명으로 바꾸지 않는다.
- 820은 종목·날짜·route별 첫 WIN부터1800초 미만인 WIN 확인점 묶음이다. FAIL을 배제한 기회 포착 지표이므로 이 구간 자체로 승률을 계산하지 않는다. 구간 시작 시점의 가격유형 귀속을 유지하면332/345/143이다. 010140의09/30 두 구간은 저가→중가 경계를 넘는다. 중가 접촉 구간347을 독립 중가345와 혼동하지 않도록 추가 검산했다.

## 3. 820구간 중7개만 선택된 이유

### 선택 조건이 매우 좁다

현재 저가는 G4(첫 반등, 당일UP·60초수익률≥0.2%·FALLING·낙폭0.2~0.4%·spread≤0.1%), 중가는 G1(당일UP·60초수익률<0·RISING·낙폭0.4~0.8%)와 등록 momentum refinement, 고가는 G2(당일DOWN·60초수익률≥0.2%·MIXED·낙폭0.8~1.2%)다. 경계의 정확한 포함 여부는 [native 정의](../../src/engine/scalping/reversal_registered_catalog.py:126)를 따른다. 현재 독립적으로 평가되는 패턴에는 아래 미선택 A01~A16 전체가 포함돼 있지 않다.

| 가격유형 | 전체 WIN 구간 | 현 선택 구간 | 현 선택 확정 승률 | 30분 중복 제외 시 승리/확정 | 선택 미확정 확인점 |
|---|---:|---:|---:|---:|---:|
| 저가 | 332 | 2 | 4/4,100% | 2/2 | 0 |
| 중가 | 345 | 4 | 8/8,100% | 4/4 | 6 |
| 고가 | 143 | 1 | 2/2,100% | 1/1 | 4 |
| 합계 | 820 | 7 | 14/14,100% | 7/7 | 10 |

### 작은 100% 정책이 선택기에서 계속 유지된다

[select_variant](../../src/engine/scalping/reversal_cumulative_registration.py:122)는 동일 원천·비교 완료 후보 중 **누적 승률 우선, 승률이 같을 때 승리 수**를 비교한다. 이 가족의 현행 계약은 sample_floor=none이다. 따라서4/4·8/8·2/2 대비 실패가1건이라도 있는 합집합은 추가 승리가 수백 건이어도 승격되지 않는다. 산술 오류는 아니지만 기회 확장 목적에 대해 극소수 완승 정책이 유지되는 구조다. 그100%를 일반화된 우월성으로 해석하면 안 된다.

원 보고서의 `fixed_proposals` 두 항목은 CURRENT/SELECTED의 압축 projection이다. 실제 전체 비교는 원 hash에 연결된 gzip archive에 있고 저가766·중가1,140·고가766, 합계2,672조합이다. 이 비교를 모두 독립 재계산해 일치시켰다. “2개만 비교했다”거나 “AI 비교가 없어서 기계 등록이 막혔다”는 원인이 아니다.

### 비교 목록에도 범위 제한이 있다

[valid_membership](../../src/engine/scalping/reversal_cumulative_catalog.py:271)는 이번 누적 등록 문법에서 **새 additive root를 하나까지만** 허용한다. 기존 패턴의 refinement와 한 개 추가 패턴은 비교하지만 새로운 추가 패턴 두 개의 독립 합집합은 현 선택 후보가 아니다. runtime 전체가 정책2개로 제한된다는 뜻은 아니다. 다만 이번 연구의2개 추가 조합도 최고 단일 후보보다 누적 승률이 낮으므로 이 제한만 풀면 선택이 달라진다고 주장할 수 없다.

## 4. 미선택 패턴 추가 비교

[동결 protocol](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/protocol.json)의 기존 root A01~A16을 사용했다. 각 가격유형에서 현행+단일16개, 추가2개 조합120개, root family6개, 전체16개를 비교했다. threshold를 결과에 맞춰 새로 탐색하지 않았다. A 별칭은 research batch `2a0663bcf24378574d101371855266dd2bd6f9810dc80599f2aae68002eef956`의 정의다. 다른 연구의 A42~A44와 혼용하지 않는다.

주요 후보: A05=첫 반등1초 유지(낙폭0.4~1.2%,spread≤0.1%), A09=첫 반등5초 유지(매수비중≥60,낙폭0.2~1.2%,VWAP≥0), A08=60초 고점 돌파(매수비중≥60,낙폭≤0.4%,수익률≥0), A12=고점 돌파1초 유지(매수비중≥60,0≤수익률<0.4%,당일수익률>0.4%,spread≤0.1%), A14=상승구조3초 유지(수익률≥0,spread≤0.1%,VWAP≥0). 단위·누락 처리·root 발생 조건은 protocol의 원 정의를 따른다.

### 단일 추가 후보

모든 행은 **현행∪후보**다. 추가 WIN/STOP/TIMEOUT은 현행 exact key를 제외한 증가분이다. 누적 승률에는 확정점만 넣고 반복 확인점이 포함된다.

| 유형·추가 후보 | 누적 승리/확정·승률 | 추가 WIN | 추가 STOP | 추가30분 미달 | 미확정 | 포착 WIN 구간 |
|---|---:|---:|---:|---:|---:|---:|
| 저가 A05 | 321/484 ·66.3% | 317 | 29 | 134 | 302 | 2→44 |
| 저가 A09 | 411/774 ·53.1% | 407 | 54 | 309 | 285 | 2→119 |
| 중가 A08 | 1,041/2,867 ·36.3% | 1,033 | 30 | 1,796 | 1,563 | 4→246 |
| 고가 A14 | 44/67 ·65.7% | 42 | 1 | 22 | 42 | 1→16 |
| 고가 A12 | 16/25 ·64.0% | 14 | 1 | 8 | 23 | 1→12 |

### 추가2개 및 전체16개 합집합

| 유형·추가 후보 | 누적 승리/확정·승률 | 추가 WIN | 추가 STOP | 추가30분 미달 | 미확정 | 포착 WIN 구간 |
|---|---:|---:|---:|---:|---:|---:|
| 저가 A05+A12 | 336/517 ·65.0% | 332 | 29 | 152 | 323 | 50 |
| 중가 A08+A12 | 1,044/2,888 ·36.1% | 1,036 | 30 | 1,814 | 1,570 | 246 |
| 고가 A12+A14 | 58/90 ·64.4% | 56 | 2 | 30 | 61 | 25 |
| 저가 전체16개 | 4,461/18,998 ·23.5% | 4,457 | 452 | 14,085 | 9,476 | 332 |
| 중가 전체16개 | 6,113/35,857 ·17.0% | 6,105 | 175 | 29,569 | 19,479 | 345 |
| 고가 전체16개 | 2,066/4,719 ·43.8% | 2,064 | 20 | 2,633 | 2,866 | 143 |

위2개 추가 조합은 각 유형의120쌍 중 누적 승률 최상위다. 기존 선택 문법은 이를 허용하지 않으므로 연구만 했다. 중가 전체16개가 전체 원천 WIN6,132점과 다른 이유는 현행+16additions 밖의 기존 branch/refinement 확인점이 남기 때문이다. 구간 포착은345로 동일하다. 일부 범위의 전체구간 포착이 각 구간에서 첫 실제 진입 성공을 뜻하지 않는다.

### 반복 진입·날짜·원천 민감도

각 종목/날짜/route에서 **처음 충족한 확인점**을 선택하고1800초 뒤까지 재진입하지 않는 진단을 추가했다. 첫 미확정/실패를 건너뛰고 뒤의 승리를 택하지 않는다. 이1800초는 연구용 중첩 제거이며 live cooldown 변경안이 아니다. 서로 다른 가격유형 분석을 동시에 주문하는 portfolio 재생도 아니다.

| 후보 | 전체 순차 선택 승리/확정 | 최근10/23·26 순차 선택 승리/확정 | 10/26 반복 확인점 승리/확정 |
|---|---:|---:|---:|
| 저가 A05 | 36/62 ·58.1% | 8/14 ·57.1% | 3/18 |
| 저가 A09 | 102/188 ·54.3% | 42/57 ·73.7% | 65/82 |
| 중가 A08 | 166/534 ·31.1% | 19/31 ·61.3% | 41/70 |
| 고가 A14 | 13/29 ·44.8% | 3/7 ·42.9% | 1/5 |
| 고가 A12 | 12/20 ·60.0% | 1/1 ·100% | 0/0 |

최근 날짜도 이미 연구·선택에 사용된 원천이므로 독립 holdout이라고 부르지 않는다. 고가 A12의 최근1승은 확대 근거가 부족하다. 저가 A05는10/23에100/127이지만10/26에3/18로 악화했고, A09는10/23 104/143·10/26 65/82다. 누적을 유지하면서 이러한 차이를 다음 검증 가설로 삼는다.

보강 bar를 제외한 native-tick 확인점만 보면 저가 A05 272/372(73.1%), 중가 A08 894/2,103(42.5%), 고가 A14 39/54(72.2%)다. 허용된 bar 결과를 마음대로 버려 순위를 개선하지 않는다. 원천 종류가 결과를 바꾸므로 새 날짜 재생에서는 동일 item·가격/호가 시각·비용 결속을 분리 확인한다.

## 5. 보완 순서

1. **원천 도달:** 기존 MainEntrySourceTerminalRepair1022에서 미수신19 lease와 수신 후 현재성/연속성 미충족을 분리한다. REG송신→정확 item 0B/0D→정규화 sequence→native→branch→AI를 같은 PID·epoch로 대조한다. 과거6일 epoch와10/13 보강 이력도 원 receipt로 복구 가능성을 확인한다. 복구 불가 행은 제외/미확정으로 남기고 전체 원천을 막지 않는다. 수신 공백을 바로 API 결함으로 판정하거나 감시 연장·새 구독·stale 허용으로 덮지 않는다.
2. **선택 기준의 함정 보완:** 승률을 주지표로 유지하되 반복 확인점과 구간 단위를 함께 공개한다. 소표본100% 현행의 우월성이 입증됐다는 전제를 제거한다. 독립 추가 패턴의 자체 누적 승률·추가 WIN/FAIL을 먼저 비교하고, 기존 정책과 합친 효과를 별도로 평가하는 설계를 권한다. ‘현행에 없는 기회’의 대조군은 미진입이므로 승률0 또는100으로 채우지 않는다. 이 설계는 현재의 무조건 합집합 승률 우월 규칙 변경이므로 후속 구현·채택을 통해 명시적으로 정해야 하며 이번에 바꾸지 않았다. 손익비·EV나 임의의 새 표본 하한을 도입하지 않았다.
3. **유형별 후속:** 저가 A05/A09의 승리·손절·30분 미달을 같은 시각의 가격/체결/호가 사실로 대조하고, 특히10/26의 차이를 설명할 가설을 동결한다. 고가 A12/A14는 표본·중복 의존성을 먼저 확인한다. 중가 A08은 추가 실패1,826건 중1,796건이 시간 미달이므로 단순 반등 존재와30분 목표 도달 흐름을 구분하는 데 집중한다. 전체16개 활성화는 권하지 않는다.
4. **보조판정 연구:** 위 우선 후보의 실제 원천 유효점에서 현행 native/A/유형별 프롬프트를 같은 입력으로 비교한다. 기존 응답을 먼저 재사용한다. 현재 선택14승리만 반복하지 말고 각 후보의 추가 WIN/STOP/TIMEOUT을 다루며, diagnostic 균형 표본의 PASS율을 모집단 승률처럼 쓰지 않는다. 미래 결과는 평가에만 사용하고 입력에는 넣지 않는다. 실패 PASS 감소와 승리 복원 유지, 그리고 source/기한 이후 terminal을 별도 제시한다.
5. **운영 연결:** 후속 채택 후보가 정해지면 기존 registry·부모 정책·AI 연결·ANY_MATCH 중복방지·현재 guard를 검토한다. 새 additive root 복수 조합이 필요할 때만 기존 grammar/승인 계약을 확장한다. 원 신호→AI→제출 기한 문제는 별도 지연 owner를 이어받는다. 연구 수치가 배포·PID 소비·실제 체결을 대신하지 않는다.

## 6. 검토·검증·보존

- canonical baseline `1756de1d9d7943739d539d5207cc55484185bff5`; offline import root `factorial-tail-aux-research-20261023`/`8c41c37c1f761a5c4e55ab1207eada38a0f9f86f86f`를 고정했다. 기존 불변 Store를 read-only로 읽었다. source machine, partition record SHA, snapshot symbol/item/route, 중복/conflict를 검사했다.
- [비교 전체](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/comparison.json), [432설정 CSV](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/comparison-table.csv), [독립 검산](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-pattern-contribution-20261027/verification.json)을 보존했다. bitset와 별도 set 집계를 대조하고 원 압축archive2,672변형을 포함해3,968개 metric 검사를 통과했다.
- 리뷰에서 전체비교 archive와 CURRENT/SELECTED projection을 구분했고, 가격유형 경계의2중 접촉 구간을 별도 기록했다. 820개와 유형별 첫 시점 귀속332/345/143을 보존했다. 기존 표본 unknown-refinement 보존 계약도 확인했으며 unknown을 새 root TRUE로 바꾸지 않았다.
- 연구 회귀11건: 첫 미확정/실패를 건너뛰지 않음,1800초 경계,종목/날짜/route 분리,합집합 중복 제거,미확정 분모 제외,소표본100% selector·원천/비교 불완전 음성,단일/복수 root grammar. 운영 trading suite·provider 호출·장후 재생은 범위 밖이라 실행하지 않았다.
- 변경은 새 연구용 driver3개·회귀1개와 보고서/기존 계획 보완이다. 운영 source/tests 추가·삭제0, 원 owner/selector/collector/prompt는 retained다. 연구 driver는 live dispatch가 없는 독립 검산 도구이며 원장 복제·신규 운영 validator를 만들지 않았다. 기존 dirty 작업·strict-bound checklist·원 raw/응답/실패 증거는 변경하지 않았다.
- 최종 검증: 연구 회귀11PASS, 독립 metric검사3,968PASS, compile·git diff --check 통과, 두 문서의24개 링크 실재 확인, print-only backlog 경고/오류0 및 기존 두 owner 각1개 파싱 확인. 외부 sync는 실행하지 않는다. 사용자 실행 sync 명령은 기존 [연구 검토서](main-auxiliary-spread-liquidity-research-review-2026-10-27.md)의 단일 안내를 따른다.

## 7. 선택구조 구체화와 추가 검증 — 14:02 후속

사용자의 후속 지시에 따라 [소표본 선택 보완계획](../proposals/main-regular-nonfixed-small-sample-selection-remediation-plan-2026-10-27.md)을 구체화했다. 기존 WIN/STOP/TIMEOUT·비용·원천 경계를 유지하고, 시간 중복 제거 누적 승률의 Wilson 하한을 순위 점수로 쓰는 **새 선택 계약안**이다. 현 raw-fraction 계약이나 운영 정책을 바꾸지는 않았다. 추가 AI 호출0이다.

### 실행·원천

[동결 후속 protocol](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/protocol.json)은 저가 A05/A09·고가 A12/A14·중가 A08,1800초 중복 제거,사전 특징 구간,Wilson z=1.959963984540054를 고정했다. 동일 자료의 탐색·민감도 분석이며 미래 독립 성과로 표시하지 않는다.

원 Store에서 해당 후보/현행의6,416확인점을 재사용했다. native-tick5,359점은 원 normalized10개 파일의 정확 epoch/sequence/item/ask와 연결해 원30분 라벨을 전부 재현했다. 후행1/5/10/30/60분 경로는 평가용이며 AI 입력이나 당시 진입 판정으로 쓰지 않았다. 보강 bar1,057점은 원 라벨 유지·tick 세부경로 미확정이다. 실행88.5초,후행 승패 불일치0. [전체 분석](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/analysis.json), [확인점별 참조·진단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/point-diagnostics.json)을 보존했다. 새 raw 원장·provider 응답을 복제하지 않았다.

### 순위 변화와 편중

| 범위 | 현행 중복 제외 W/N ·보정 점수 | 단일 추가 후보 W/N ·보정 점수 | 연구 우선순위 |
|---|---|---|---|
| 저가 | 2/2 ·34.24% | A05 36/62 ·45.67%; A09 102/188 ·47.12% | A09 우선 |
| 중가 | 4/4 ·51.01% | A08 166/534 ·27.31% | carry, 원인 보완 |
| 고가 | 1/1 ·20.65% | A12 12/20 ·38.66%; A14 13/29 ·28.41% | A12 우선 |

보정 점수는 원 승률 자체가 아니며 표본 수의 불확실성을 반영한 순위 제안이다. 시계열 상관·다중 후보 탐색 때문에95% 실제 성과 보장을 주장하지 않는다. 원 기간에서 사용자가 지정한 후보의 비교이지 전체 등록 패턴의 새 전역 최적화는 아니다.

- 저가 A05:10/26 순차2/4,U5. 반복 확인점3/18과 다르다. 최다 승리 종목138360을 빼면30/54,날짜 한 개씩 제외하면52.5~62.5%다.
- 저가 A09:10/26 순차16/24,U15. 최다 승리 종목028670을 빼면90/160,날짜 한 개씩 제외하면49.0~59.9%다. A05+A09는112/210·53.3%로 A09 단독 추가102/188·54.3%보다 낮다. 순차상 승리10개가 늘지만 실패도12개 늘어난다.
- 고가 A12:12승 중10승이09/29다. 10/26은 확정0,U3이다. 가장 많은 승리 종목353200을 빼면8/15다.
- 고가 A14:13승 중7승이031980이다. 이를 빼면6/21,10/26은1/5,U5다. 원 raw44/67만으로 우선 확대하지 않는다.
- 고가 A12+A14는22/41·보정38.75%다. 단일 A12의38.66%와 차이가0.088pp이고 현 추가-root 문법에서 허용되지 않아 보고용으로 유지한다. 미래 날짜·등록 변경이 이미 완료된 것으로 표시하지 않는다.

조합의 단순 key 합집합과 실제 시간순 첫 진입은 다르다. 순차 진단에서 저가 A05는 현행 WIN2key를, A09는1key를,중가 A08은WIN3/U1key를,고가 A14 및 A12+A14는WIN1key를 앞선 다른 진입으로 대체했다. 고가 A12는 현행 key를 모두 유지했다. 이는1800초 연구 스케줄의 대체이며 실제 주문 손실이나 전략 cooldown 변경이 아니다. 추가/제거 목록을 결과에 남겼고 승리100% 보존이라는 새 gate를 추가하지 않았다.

### 중가30분 목표 미달

현행∪A08의 순차 성적은166WIN/4STOP/364TIMEOUT/U359다. 10/26 원 확인점41/70은 순차3/9,U8로 내려간다. 반복되는 뒤쪽 승리 확인점을 각각 진입기회로 세면 성과가 커 보이는 문제를 확인했다.

미달364 중 원 tick 경로246건은 비용 후 최대 진전0 이하132,양의 진전 뒤30분 말 음수90,양수 유지했으나목표 미달24다. 나머지118건은 bar 라벨로 세부 tick 형태 미확정이다. 원 tick 미달의 최대 비용 후 수익률 중앙값−0.0267%,30분 말−0.3924%다. 후행60분까지22WIN/2STOP/109TIMEOUT/U113이며30분 승패를 바꾸지 않는다.

[거리 진단과 정확 사례](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/mid-timeout-supplement.json):246건 중44건은 비용 차감 전 상승률이+0.4%에 도달했어도 비용 후 목표는 미달했다. entry ask를 당시 거래가격으로 가정했을 때만 목표가 될 수 있는 경우는2건이다. 이 반사실 가격은 실제 매수 가능 가격이 아니므로 가격/비용 조건을 바꾸는 근거로 쓰지 않는다.

WIN/미달의 사전 spread 중앙값은0.1479%/0.1386%,매수비중93.28/89.77,거래량비율1.63/1.51이다. 보편적인 큰 spread·매수 부재가 실패 원인이라는 주장은 지지되지 않는다.60초수익률은0.2974%/0.1952%로 차이가 있고,고정 구간에서0.4% 이상56/112 대0.1~0.2%44/196,구조RISING48/105 대MIXED76/300이다. 연관성이므로 바로 조건 강화하지 않는다. **작은 고점 돌파를 포착한 사실과30분 목표까지 갈 거래가격 진전을 분리하는 입력**을 다음 가설로 삼는다. 사후 경로는 라벨 진단으로만 사용한다.

### 현재 원천 도달

[14:02:26 재점검](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/live-summary.json)은 같은6d0d19756/PID670131/start71972259다. selector/start 읽기 전후 불변,원 window coverage유효·malformed0·tail truncation0이다. 비상시87고유 lease·81종목,0B수신62/0D64,둘 다 미수신23,native도달56,현재 선택이력 TRUE/ready0,당일 정규장 비상시 AI/capture0이다. native56건의 마지막0B collector sequence는 모두 native sequence와 일치했다. 중간 모든 raw 패킷의 완전성까지 검증한 것은 아니다.

13:50 이후 새28lease는 미수신4,0B age2,0B없음1,현재성 stale16,패턴불일치5다. 새 결손이 계속되므로 원천 문제가 해결된 것은 아니다. 기존 `MainEntrySourceTerminalRepair1022`에서 정확한 미수신·수신후 현재성 경계를 이어서 점검한다. 과거6일 epoch/10/13의 원 자료 복구,원천의 상류 책임 단정,실제 정책·배포·주문 변경은 이번에 수행하지 않았다.

### 검토와 검증

연구용 Python2개·회귀1개를 추가하고 기존 검토서와 계획 연결을 보완했다. 운영 Python/tests·selector·registry·원장·strict-bound checklist 수정0이며 원 owner는 retained다. 교체/삭제되는 운영 경로는 없다. 기존 dirty 작업은 보존했다. 추가 파일은 평가값과 원 source 참조만 저장하며 raw 전체 또는 기존 AI 원장을 새로 만들지 않았다.

회귀8PASS:소표본/분모0/동일분모 Wilson 순서,첫U·1800초경계,30분 미달 뒤60분 WIN,손절선 선도달 뒤 반등,sequence 결손의미확정,특징 구간/결손값,실제5,359개 native label 결속·10개 조합의 순차 집계를 재확인했다. 계획의 운영 구현·선택 권한 부여·새 날짜 성과 검증은 미완료이며 원 owner의 source27 장후 창으로 연결한다. compile·git diff --check 통과,세 문서35개 local link 실재 확인,print-only backlog 경고/오류0 및 기존 두 owner 각1개를 확인했다. [검증 receipt](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/regular-nonfixed-selection-followup-20261027/validation.json)를 보존했다.


## 8. 선택구조 구현과 원천 소비 재점검 — 14:39

**코드 구현·검증은 완료했으며, source27 종료 검증과 운영 채택은 OPEN이다.** 10/27 14시대에는 source27 machine report/native machine terminal이 없다. source26 재현을 source27 결과로 대체하지 않는다. 원 owner는 `MachinePatternOpportunityResearch1023`와 `MainEntrySourceTerminalRepair1022`이며 기존20:05~23:59 및 장중 원천 창을 유지한다.

### 구현·리뷰

격리 작업본 `/home/ubuntu/KORStockScan-worktrees/regular-selection-score-20261027`, 기준 commit `6d0d197562c67ebdf5cd3524e71001c5257eb603`에서 기존 registration/postclose/v6 family owner를 확장했다. 실행 중인 같은6d0/PID670131/start71972259 및 기본 workspace의 다른 미커밋 변경을 보존했다. 생성 전 registered worktree261/managed release149/dev111·free60GiB를 확인했으며 개발 작업본1개만 추가했다. 운영 후보/selector는 생성·교체하지 않았다.

1. 선택은 정확한3scope에서 승인된 새 계약만 사용한다. 고정 z,1800초 통계 구간, cost-bound label, 후보/부모/source/code hash를 결속했다. 그 외 scope·역사 raw-v2·기존 단일 additive-root 문법을 유지했다.
2. 첫 U/STOP을 후속 WIN으로 바꾸지 않고, 같은 key의 복수 branch는 한 번만 세며, 추가 후보가 먼저 들어가 대체한 기존 WIN/U key를 남긴다. 식별 가능한 잘못된 clock/item row를 제외하고 유효 row는 계속 집계한다.
3. 리뷰 보완: 초안의 잘못된 timestamp1행이 scope 전체의 비교를 막는 구조를 row 격리로 수정했다. 제외 뒤 raw metric과 delta도 같은 적격 집합으로 맞췄다. 요청이 다른 등록과 경쟁하거나 parent/source/registry가 변하는 경우를 막았다.
4. 소비자 리뷰에서 family 생성부가 새 결과에도 `cumulative_raw_win_fraction`을 쓰던 위치를 보완했다. 새 manifest의 계약·선택 영수증, family 선택 지표/부모/source가 일치해야 한다. 초기 등록에 AI 비교 우월성을 새 조건으로 추가하지 않았다.
5. 연구용 비교에는 `research_only`와 operator receipt=null을 사용한다. 연구 결과는 실제 승인 계약으로 소비되지 않는다. 준비→명시 intake→기존 postclose/정책 publisher의 경로만 운영 선택 요청을 받는다. 이번 실행은 신규 AI0/정책 게시0/주문0/배포0이다.

검증: cumulative·extended family·auxiliary tuning·probe **265 PASS**, pandas의 기존 deprecation warning1. 마지막 row delta/등록 충돌 보완 뒤 cumulative **74 PASS**를 별도 확인했다. compile·diff 및 문서 검증은 아래 최종 기록에 결속한다. 완전한 운영 후보 P5·실제 정책 발행·PID 소비를 수행했다는 뜻은 아니다.

교체/제거: `select_variant`와 native build는 기존 owner 안에서 통합 확장했다. 별도 selector/root Python module/worker/dispatcher는 추가하지 않았다. raw-v2는 범위 밖 정책과 역사 reader의 현재 소비자가 있어 retained다. native probe receipt 수리는6d0에 이미 포함되어 있어 복제하지 않았다. 연구 실행기는 같은 집계/선택 함수를 호출하며 임시 도구를 live dispatch에 등록하지 않는다. 원 큰 비교표와 point Store는 보존한다.

### source26 재현과 적용 판단

[최종 대조 영수증](../../tmp/regular-selection-score-20261027/parity.json): 앞선 연구와8조합의 W/N/U·선택 key32개 대조, 불일치0. 전체8조합 중 지정 후보5개를 아래에 표시한다. 원천 raw/point Store는 읽기 전용이며 종료 이후 날짜는 혼합하지 않는다.

| 후보 | 시간 중복 제거 W/N | STOP / TIMEOUT / U | 점수 L | 현재 판단 |
|---|---:|---:|---:|---|
| 저가 A05 |36/62 ·58.1%|2 /24 /50|45.67%|A09 대비 후순위 검증|
| 저가 A09 |102/188 ·54.3%|9 /77 /113|47.12%|source27 우선 재검증 후보|
| 고가 A12 |12/20 ·60.0%|1 /7 /17|38.66%|source27 새 날짜 확인 필요|
| 고가 A14 |13/29 ·44.8%|0 /16 /23|28.41%|A12 대비 후순위 검증|
| 중가 A08 |166/534 ·31.1%|4 /364 /359|27.31%|현행4/4·L51.01% 유지|

저가 현행2/2·L34.24%,고가 현행1/1·L20.65%다. 단순100%와 비교하는 고착은 해소되지만 추가 후보의 실패가 없어지는 것은 아니다. source26 결과는 이미 후보 선정에 쓴 자료로 독립 holdout이 아니다. 중가 미달의 원 경로246건(비용 후 양의 진전 없음132/진전 뒤 음수90/양수이나 목표 미달24)과 나머지bar118의 미확정 tick 경로는 §7 그대로 보존한다. 새 날짜로 재현하기 전 A08 임계값이나 prompt를 임의로 변경하지 않는다.

### 원천 도달

[14:39:42 exact lease·clock 대조](../../tmp/regular-selection-score-20261027/source-clock-review.json): 동일6d0/PID670131의 **186고유 lease/171종목**, 0B128·0D134, 양쪽 무수신52이다. native 영수증114개는 마지막 정규화 snapshot/native epoch·sequence가114/114 일치한다. 전체 패킷의 완전성 보증은 아니다. 이력 TRUE/ready0이며14:32의 당일 비상시 정규장 AI/capture0도 별도 원 prefix로 확인했다.

종료 사유: snapshot 없음52,0B age초과14,0B없음6,이력 뒤 현재 source stale67,이력 source gap3,현재 source absent1,유효 패턴 불일치41,확인 대기2. 무수신52의 종목별 ACK는 미확정으로 남기며 API 결함/정상 무체결 어느 쪽도 단정하지 않는다.

확인 가능한 **마지막0B128개**의 거래소시각→앱수신은 중앙0.468초/최대1.096초, 앱수신→정규화1.53ms/최대32.58ms, 정규화→native 호출 반환0.47ms/최대11.70ms다. 마지막 수신→terminal은 중앙6.86초/최대147.95초다. 이 자료에서 오래된 마지막 체결과 빠른 로컬 전달을 구별할 수 있으나, 13:28의350거부·10.3~18.6초 수신지연이나 이후 모든 패킷까지 해소된 것으로 볼 수 없다.

현재 source 계약의 최초 미관측 경계는 정확 normalized snapshot58(무수신52+0B없음6), native receipt14(초기 age guard 뒤 미관측), 결손 경계 없음114다. native 호출 반환 자체를 평가 준비/승리로 취급하지 않는다. 기존 receipt 수리가 active release에 있음을 코드/45개 음성·양성 회귀/현재114개 영수증으로 확인했으며, 추가 입증된 내부 전달 결함은 발견하지 못했다. 구독 추가·관측 기한 연장·stale guard 완화로 원천 결손을 가리지 않았다. 무수신과 체결 간격의 상류 원인은 원 source owner에서 exact lease/전체 수신창·동일 item 공식 증거를 더 확보해야 한다.

### source27 잔여 작업

[미생성 상태 영수증](../../tmp/regular-selection-score-20261027/2026-10-27-pending.json)에 machine/native terminal 부재를 기록했다. 다음 원 창20:05~23:59에 같은 [재검증 도구](../../tmp/regular-selection-score-20261027/revalidate.py)를 `--source-date 2026-10-27`로 실행해 stage→봉인 source→Store hash→선택결과를 연결한다. source27 당일·누적 W/S/T/U/L,추가/제거 WIN과 중가30분 후행 경로를 확인한 후 운영 채택 여부를 확정한다. 자료 미완료/원천 부적격이면 정확한 row 제외/미확정과 owner를 유지한다. 운영 채택과 배포는 이번 연구 코드 완료와 별개이며 재기동을 수행하지 않았다.


최종 검증 보강: source26의 새 날짜 순차 확인점78개 중 native76개의 원 epoch/sequence/item/ask→30분 라벨을 bounded 재검증해 불일치0을 확인했다. bar2건은 tick 경로를 만들지 않았다. 중가 source26의6개 native TIMEOUT은 진전 없음2/진전 뒤 음수2/양수 목표 미달2였으며60분은WIN2/TIMEOUT2/U2다. 기존30분 실패 라벨은 유지한다. [parity](../../tmp/regular-selection-score-20261027/parity.json), [문서·owner 검증](../../tmp/regular-selection-score-20261027/doc-validation.json). 최초 자체 검증기의 `:line` 링크 및 backlog title 필드 처리 오류는 검증기에서 수정했고 문서/운영 데이터를 바꾸지 않았다.

변경량(기준6d0): non-test source3개 +642/−11, test1개 +514/−0, 신규 관리 문서2개는 기존 연구 이력과 이번 구현 절을 함께 추적한다. 새 source module/worker/entry root는0이며 새 CLI subcommand2개는 기존 등록 owner의 준비/명시 intake다. 분량 증가는 새 버전 계약·통계/원천 결속과 음성 회귀에서 발생했다. 원 raw 판정은 현재 소비자가 있어 제거하지 않았다. 실제 변경 내역과 code hash는 [구현 검증 영수증](../../tmp/regular-selection-score-20261027/implementation-validation.json)에 기록한다.
