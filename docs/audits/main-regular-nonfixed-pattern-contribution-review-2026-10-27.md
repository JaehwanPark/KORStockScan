# 정규장 비상시 원천·기계 선택·추가 패턴 기여 검토 — 2026-10-27

## 결정

**17:41 준비 범위 정정:** 통계상 A09 권고와 현행 정책의 코드 인계/P5 통과는 유효하다. 신규 scoring을 쓰는 장후 전체 경로는 미검증이며, §12의 포괄적인 배포 준비 PASS는 그 범위에서 철회한다. 아래 §13이 실행 순서와 OPEN 사항을 소유한다.

**17:16 후속 결론:** 원천 보강 후 저가A09의 정규장 비상시 SOR 범위 채택을 권고한다. 당일11/16승·누적113/204승이며, 미확정86점 중75점을 확정했다. 최종 코드 후보 `a1b1b0f8a`의 현행 정책 인계·격리 기동은 통과했다. 정식 A09 정책 생성·게시와 실제 PID 소비는 아직 미실행이며 §12가 최신 결과를 소유한다. 아래 초기 판단과 각 시각의 원본은 보존한다.

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


## 9. source27 조건부 재검증과 원 무수신52건 추가 대사 — 15:13

사용자 후속 지시에 따라 원52개 lease를 고정하고 source27 봉인 후 같은 후보를 다시 비교하는 단회 연구를 준비했다. 현재 source27 machine·native machine terminal·source manifest는 아직 없다. 52건 대사 시각15:13의 기준은6d0d19756/PID670131/start71972259다. 이번 작업이 실행한 운영 정책/등록·배포·재기동·provider·주문 변경은0이다. 15:17:56 별도 운영 전환으로 selector가d5ddc0ae0으로 바뀌고 원PID는 종료됐다. 새PID 소비는 이52건 연구의 수용 증거에 합치지 않는다. 기존 `MachinePatternOpportunityResearch1023`와 `MainEntrySourceTerminalRepair1022`를 유지한다.

### 원52건의 추가 확인

[정확52건 재대사](../../tmp/regular-selection-score-20261027/original52-followup-151304.json)는 [14:39 원 집합](../../tmp/regular-selection-score-20261027/source-clock-review.json)의 SHA·52lease ID를 고정했다. 나중에 새로 생긴 무수신을 이 분모에 섞지 않았다. 원 sentinel의 검증된 시간 index와 bounded suffix만 사용했으며 새로운 구독/REST 보강 호출은 없다.

| 확인점 | 결과·해석 |
|---|---|
| 정확 item/lease/연결·등록 세대 |52/52 일치, 전부 SOR 관측 `_AL`, 로컬 REG `sent`,0B/0D 요청 |
| 로컬 send 소요 |중앙0.217ms,최대4.990ms; 원 서버 승인 시간은 아님 |
| 첫 수신 없는 관측 길이 |10.151~10.333초, 기존 empty-source10초 종료. 일반 source wait15초/전체 residence150초를 모두 쓴 것이 아님 |
| 최초 결손 경계 |52/52 `wire_receive`; 파서/정규화 이후 유실로 확정할 근거 없음 |
| 같은 연결·같은 구간의 다른 종목 수신 |34/52에서 다른 lease의 원 첫/마지막 wire 시각이 해당 구간 안에 있음. 이34건은 연결 전체 무수신이 아님. 나머지18건은 연결 중단으로 판정하지 않음 |
| 이후 별도 lease에서 수신한 원 종목 |014990 한 종목. 첫 무수신 이후 다른4lease에서0B/0D 수신. 원 lease의 소급 복구/당시 판정 성공은 아님 |
| NXT listing 여부 |원52건 N46/Y6. 원186lease의 수신134건에도 N62/Y72가 있어 `_AL`의 NXT 비대상 일괄 차단 가설은 성립하지 않음 |
| 종목별 서버 ACK |52건 모두 unknown. 연결 단위 success를 개별 승인으로 대체하지 않음 |

원 listing snapshot은 같은PID의13:26:27 native ka10099 receipt다.52종목 모두 KRX 정규장 listing이며067630·092190은 별도 `audit_info_excluded`가 있다. 일반 보통주 관측 대상 여부와 매매 eligible을 구별한다. 이2건을 실제 진입 가능한 기회로 세지 않고, 감사 제외가 WS 무수신을 일으켰다고 단정하지 않는다. 기존 execution guard는 유지한다.

**확정한 직접 종료 원인은 최초 wire 미수신으로 empty-source 종료된 것이다.** 시장에서 해당10초 동안 실제 갱신이 없었는지, 상류가 전달하지 않았는지의 구분은 아직 불가하다. 소켓 전체 중단·NXT 비대상·로컬 송신 지연이라는 단일 가설로52건을 설명할 수 없다. 자료가 없는 구간을 실패 매매/정상 무체결로 바꾸거나 기다리는 시간을 늘려 해결된 것으로 표시하지 않는다. 원천 owner의 남은 수용은 정상 다음 lease에서 동일item/epoch/수신→native→유효 terminal이며 원52건의 역사 결손은 보존한다.

### 연구 실행기 보완·리뷰

[기존 재검증 도구](../../tmp/regular-selection-score-20261027/revalidate.py)를 다음과 같이 보완했다.

- 원 source26의3scope·현행 branch·A05/A09/A08/A12/A14·batch/registry·score 및 code hash를 [동결 protocol](../../tmp/regular-selection-score-20261027/source27-frozen-protocol.json)에 고정했다. source27의 현행 구성이 달라져도 비교 기준을 몰래 바꾸지 않고 실제 구성과 차이를 별도 표시한다.
- native stage의 `stage_code_root`에 기록된 원 생산자 reader로 검증한다. 봇 종료/재기동 후 남은 `actual_pid_receipt`를 장후 검증 코드의 권위로 쓰지 않는다. 원 reader 부재·native binding 실패는 미완료로 남긴다.
- 파일이 일부만 생성될 때 pending receipt가 서로 충돌하던 고정 파일명을 내용 hash별 불변 출력으로 바꿨다. 원 pending 파일은 보존한다. source27 적격 SOR/REGULAR partition 자체가 없으면 source26 누적 수치만으로 완료하지 않는다.
- 기존 Store readonly 원장을 재사용하며 source27 raw/순차 W/STOP/TIMEOUT/U와 누적값, 추가·제거 WIN, 중가 A08의30분/60분 경로를 분리한다. 봉인 source·stage SHA를 계산 전후 확인하며 raw·AI 원장 복제는 없다.
- [단회 대기 실행기](../../tmp/regular-selection-score-20261027/await_source27.py)는 기존 owner의20:05~23:59 창에서60초 간격으로 작은 manifest 상태만 확인한다. 같은 안정된 세대의 native 봉인 검증 후 한 번 연구하고 결과를 남긴다. 실패한 동일 세대는 반복하지 않으며 관련 native 입력 세대가 달라질 때만 다시 검증한다. 단일 프로세스 lock·실패 이력·재개 시 중복 실행 차단·창 종료 시 명시적 미완료를 갖는다. cron/systemd·장후 dispatch에는 등록하지 않는다.
- 원52건 추적 도구의 경로 메타데이터 변수 충돌도 리뷰 중 고쳤다. 최종 재대사의 `original_population.path`가 실제 원 파일을 가리킴을 확인했다. 앞선 중간 출력은 수치를 소급 변경하지 않고 보존했다.

최종 회귀15PASS: 부분 생성/다른 날짜/진행중 stage, 원 producer reader, code/원본 변경, 불변 출력 충돌, 미완료 자료 실행 방지, 동일 실패 세대1회, native dependency 복구 감지, 완료 후 중복 실행 방지, 동시 프로세스 차단을 포함한다. 시간 진행은 격리 fixture이며 실제20:05 관측이 아니다. 변경 실행기로 source26의8조합 metrics/effect key와 native76경로를 재현했고 차이0이다. compile·문서 링크/owner·print-only parser·diff 검증을 별도 receipt에 남긴다.

교체/제거: 운영 Python/dispatch 변경0, 기존 native reader·Store·선택 owner retained. 임시 연구 `revalidate.py`를 직접 보완하고 새 운영 wrapper는 만들지 않았다. 단회 wait runner와 회귀는 이 연구 디렉터리에만 있다. 원 source26 결과·52lease 원본·이전 pending은 역사 증거로 retained이며 현재 소비자는 동결 protocol이다. 대기 프로세스 종료 및 최종 산출물 보존 확인 전 연구 작업본/참조 파일을 삭제하지 않는다.

### 현재 적용 판단과 후속 결과

source26 기준 연구 순위는 저가 A09, 고가 A12, 중가 현행 유지다. 이 순위를 source27 검증으로 표시하지 않는다. source27 후보별 확정 표본이0이면 그 후보의 새 날짜 효과는 미확정으로 보고한다. 새 최소표본/임의 승률 문턱·손익비 조건을 추가하지 않는다. 연구 비교 완료, 운영 채택 승인/등록, native 정책 인계/배포, 실제 PID 소비·자연 제출은 각각 별도다.

현재는 **source27 종료 자료 대기이므로 최종 운영 적용 판단 OPEN**이다. 사용자가 지시한 조건부 연구 결과와 미완료 사유는 [단회 연구 진행·결과](../../tmp/regular-selection-score-20261027/source27-continuation-report.md)와 [상태 영수증](../../tmp/regular-selection-score-20261027/source27-continuation-status.json)에 기록한다. 이 자동 생성 연구 표를 실제 정책 채택 또는 최종 운영 리뷰 완료로 선언하지 않는다.

단회 연구 대기 실행은15:18경 PID1255988/start72644010으로 시작했고 실제 `waiting_window` 상태·cwd·start ticks·중복 lock을 확인했다. 진행창은20:05~23:59이며 원 bot PID와 별개다. 원 생산자 reader를 쓰므로 bot PID receipt가 전환 중 없는 상황에서도 그 값을 임의 보완하지 않는다. [실행·검증 영수증](../../tmp/regular-selection-score-20261027/source27-followup-validation.json)을 보존한다.

## 10. 정규장 분리 검증과 장후 terminal 의존성 정정 — 15:36

**정규장 비상시 연구는 애프터마켓 종료를 기다릴 필요가 없다.** 이전 실행기가 정식 하루 전체 machine report/terminal을 요구하도록 구성되어 있었으며, 이를 연구 자체의 불가피한 조건으로 설명한 부분을 정정한다. 운영용 `prepare-scoring`/등록의 native 증빙 요건과 별도 source-only 연구 입력을 구분한다. [계획 §7](../proposals/main-regular-nonfixed-small-sample-selection-remediation-plan-2026-10-27.md#7-정규장-종료-후-선행-연구--1536)에 선행 경로를 반영했다.

15:36에 기존 정규화기를 실제 호출해 `SOR/SOR_REGULAR`만 별도로 고정했다. raw308,560,346바이트를 복제하지 않고 읽기 참조와 약4.4MB의 gzip/receipt를 생성했다. 원 parser·source-quality 판정·row 필터는 변경하지 않았다. 294,926행 중265,920행이 유효,29,006행이 부적격이다. 부적격 중28,838행은 원 종료 검증에서 제외된 epoch1793057003153794049이며 나머지168행은 native 행 유효성 검증에서 제외됐다. 원 날짜 전체를 차단하지 않았다. [원천·epoch·시간·종목유형별 근거](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-feasibility/feasibility.json).

| 연구 범위 | 전체 체결 관측 행 | 적격 행 | 제외 행 | 적격 종목 수 |
|---|---:|---:|---:|---:|
| 비상시 저가 |30,211|21,120|9,091|321|
| 비상시 중가 |20,220|16,841|3,379|164|
| 비상시 고가 |9,392|8,512|880|52|

유형 분류는 동결 후보와 같은 native `cell_key/group`을 사용했다. 종목이 가격대 경계를 넘으면 유형별 종목 수가 중복될 수 있으며, 관측 행을 독립 기회나 승패로 세지 않는다. 원 실제 감시 이력의 검증 범위를 이 표만으로 확대하지 않는다.

정규화 SHA=`821a493d2b5b0cb4b9e856a1a9ecfa685d6b8e50b1435e2bcea3ae45e2179f7a`. 원 종료 영수증8개를 hash로 연결했고7개는 native 적격·1개는 제외다. running collector의 미봉인 상태를 `closed`로 바꾸지 않았으며 이번 SOR 정규장 파일에는 새 running epoch 행이 없었다. 정규장 마지막 체결 수신은15:17:43.168이므로15:30까지의 완전 수신을 주장하지 않는다. SOR는 관측 item `_AL`의 자료 분류이며 실제 체결 거래소 증거가 아니다.

30분 관측 전에 WIN 또는 STOP이 먼저 확인되면 기존 결과를 사용한다. 둘 다 없고 연속 경로가 부족하면 U로 유지한다. 정규장 마지막30분을 무조건 제외하거나 실패로 세지 않으며, AFTER의 다른 시계열을 연결해 완전한 정규장 경로로 만들지 않는다. 동일 item의 정규장 완성봉 revision 보강은 별도 출처와 순서 검증이 필요하다.

결론은 **지정5후보의 선행 재검증 입력 준비 가능**이다. 이번 확인에서 후보별 승패 재집계·새 순위·운영 적용은 수행하지 않았다. 기존 원장/후보 정의/20:05 정식 세대 대기 실행기는 보존하고 선행 연구의 prerequisite에서만 full-day terminal을 분리했다. 원천·운영 Python·provider·bot·정책·주문 변경은0이다. 문서2개만 수정했으며 삭제/교체할 운영 구현은 없다.

## 11. 정규장 5후보 당일·누적 재검증 완료 — 15:52

**재검증은 완료했고 새 선택 규칙의 연구 순위는 저가A09·고가A12·중가현행 유지다. 운영 등록·배포는 미실행이다.** 사용자 지시대로15:36 고정 정규장 입력으로 즉시 실행했으며 하루 전체 장후 terminal을 요구하지 않았다. 아래 N은 WIN+FAIL_STOP+FAIL_TIMEOUT, U는 미확정이다. 비용0.0023·진입ask·30분 비용후+0.4%·소프트손절−3% 선도달 없음과 첫 U/실패도1800초 통계창을 점유하는 사전 정의를 유지했다.

근거: [전체 비교 결과](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-revalidation/comparison-a838936731e5.json), [원천 보강 한계](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-revalidation/unresolved-diagnostics.json), [활성 코드·등록 대조](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-revalidation/operating-applicability.json).

### 당일 결과

비상시 정규장 적격46,473행을 기존 native detector로 재생했다. 지정 현행/후보에 해당하는174확인점을 만들고 시간 중복 제거 후93개 고유 확인점을 검증했다. 모든 후보는 현행∪추가 단일패턴이다. 같은 원천에서 고정 현행 규칙은3유형 모두0확인점이며, 이를 운영 전체의 실제 기계·AI·주문 이벤트0건으로 확대하지 않는다.

| 종목유형·추가 후보 | 반복 확인점 W/STOP/TIMEOUT/U | 시간중복 제외 W/STOP/TIMEOUT/U | 확정 승률 | 당일 추가 승리/실패 |
|---|---:|---:|---:|---:|
| 저가 A05 |0/1/0/20|0/1/0/9|0/1,0%|+0/+1 |
| 저가 A09 |1/0/0/28|1/0/0/20|1/1,100%|+1/+0 |
| 고가 A12 |0/0/0/1|0/0/0/1|미확정|+0/+0, U1 |
| 고가 A14 |0/0/0/10|0/0/0/10|미확정|+0/+0, U10 |
| 중가 A08 |21/0/0/92|5/0/0/46|5/5,100%|+5/+0 |

당일의1/1·5/5는 빠르게 장벽에 도달한 확정 결과다.93점 중86점이 U이므로 미관측 실패가 없다는 뜻이 아니다. 새 최소 표본수나 임의 승률 문턱은 추가하지 않았고, 확정 분모와 관측 한계를 함께 보고한다. 당일 추가 승리6개는 저가192650 1개, 중가437730 2개·457190/468670/448900 각1개다. A05의 손절은451760이다. 모두 반사실적 관측 판정이며 주문·체결 수익 증거가 아니다.

### 누적 결과와 추가 기회

09/29 이후 기존 적격10일 집계에10/27을 추가했다. 제외된 역사 원천일/행을 복구된 것으로 바꾸지 않았다. 합산은 통계창이 날짜별로 초기화되는 성질을 사용하며 기존 확인점/AI 원장을 새로 복제하지 않았다. 아래 추가는 **시간순 합집합에서 새로 선택된 key**이고, 기존 나중 확인점이 먼저 발생한 추가 후보에 대체된 경우 별도 제거 칸에 표시한다.

| 후보 | 현행 누적 W/N | 후보 누적 W/N(승률) | STOP/TIMEOUT/U | 추가 WIN/실패 | 제거된 기존 WIN | 새 점수 L |
|---|---:|---:|---:|---:|---:|---:|
| 저가 A05 |2/2|36/63(57.1%)|3/24/59|+36/+27|2|44.86%|
| 저가 A09 |2/2|103/189(54.5%)|9/77/133|+102/+86|1|47.38%|
| 고가 A12 |1/1|12/20(60.0%)|1/7/18|+11/+8|0|38.66%|
| 고가 A14 |1/1|13/29(44.8%)|0/16/33|+13/+16|1|28.41%|
| 중가 A08 |4/4|171/539(31.7%)|4/364/405|+170/+368|3|27.94%|

승리 순증은 차례로+34/+101/+11/+12/+167이다. 추가 실패에는 STOP과30분 목표 미달 TIMEOUT을 포함한다. 중가A08은 U도 기존1개가 제거되고 새403개가 추가되어 누적U405다. 나머지 후보의 상세 U 이동은 원 비교 JSON에 보존한다. 기존 WIN100% 보존을 새 채택 조건으로 넣지 않았다.

반복 확인점 기준 누적은 A05=321/485(66.2%), A09=412/775(53.2%), A12=16/25(64.0%), A14=44/67(65.7%), A08=1062/2888(36.8%)다. 시간 중복을 제거한 표와 구별하며 높은 반복 확인점 승률을 독립 기회 승률로 해석하지 않는다.

### 미확정과 중가 해석

[원 후행 경로 대조](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-revalidation/unresolved-diagnostics.json): U86은 종목 경로 자체의 끝75·collector epoch 변경9·다음 행 부적격2다. 관측 길이 중앙값41.27초다. 경로 끝을 거래소 무체결·구독 종료·API 결함 중 하나로 단정하지 않는다. 이는 앞선 무수신52lease와 별도 분모다.

보관된 WS/REST 완성봉23개 원천을 native revision/hash로 고정하고 정규장 시간창만 읽었으나 U86의 동일 item 완성봉은 전부 없었다. 신규 REST/provider 호출은 하지 않았다. 원천 없음은0원·TIMEOUT으로 채우지 않았으며 AFTER 가격을 연결하지 않았다. 당일 확정7개와 통계 확인점93개는 모두 native tick 경로이며 완성봉으로 승패가 바뀐 점은0이다.

중가A08의 오늘5승은 누적 승리를166→171로 늘렸지만 누적 실패368개(STOP4/TIMEOUT364)는 그대로다. 따라서 30분 목표 미달이 해소됐다고 판단할 수 없다. 오늘 TIMEOUT 확정은0이므로 새로운 당일 미달 원인 분해를 꾸며내지 않는다. 앞선 미달246개 native 경로의 진전없음132·진전후음수90·양수목표미달24 분석은 유지한다. 이후60분 결과를30분 WIN으로 승격하지 않았다.

### 운영 적용 판단

- **저가A09:** 새 점수47.38%로 현행34.24%, A05 44.86%보다 높다. 다음 운영 적용을 검토할 우선 후보로 제안한다. 오늘 추가 승리1개는 확인했으나 U20을 포함하므로 당일 우월성이 확정됐다고 말하지 않는다. A05는 당일 손절1개가 추가되어 후순위다.
- **고가A12:** 점수38.66%로 현행20.65%, A14 28.41%보다 높아 누적 추천은 유지한다. 그러나 오늘 N=0이고 누적12승 중10승은09/29에 집중돼 새 날짜 효과 검증은 미확정이다. A14도 오늘 N=0이며 순위를 뒤집을 근거가 없다.
- **중가A08:** 오늘5승에도 누적31.7%·점수27.94%로 현행4/4·점수51.01%에 못 미친다. 적용하지 않고 현행을 유지한다.

15:52 활성d5ddc0ae0/정책6b93eb6a의3scope는 동결한 비교 현행과 정확히 일치했다. 선택 릴리스에는 새 점수 코드가 없고 활성·대기 scoring 계약도 없다. 따라서 현재 연구 결과가 운영에 자동 반영되거나 즉시 활성화할 준비까지 완료된 상태는 아니다. 명시적 채택 범위의 선택 계약, 정식 source·부모/code 인계, 검토본 통합 배포와 실제 PID 소비 확인이 남는다. 이 점검은 policy 구조 대조이며 실제 PID 재기동/소비 검증을 수행한 것으로 표시하지 않는다.

후속은 기존 owner에서 U86의 동일 item 정규장 후행 자료를 보강할 수 있는지 확인하고 정식 source27 생성 시 같은 key/라벨 차이를 대조한다. A09를 우선 채택 검토 대상으로 하고 고가의 새 날짜 효과 미확정을 명시한다. 관측 결손을 가리기 위한 새 임계값·기한 확대·guard 완화는 제안하지 않는다.

### 구현·리뷰·검증 경계

임시 연구 실행기 [regular_revalidation.py](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular_revalidation.py)는 기존 native `State/snapshot/label/scoring_metrics/select_variant`를 사용하며 운영 등록/CLI/dispatch를 추가하지 않았다. 원 stage 기반 실행기와20:05 대기 프로세스는 정식 장후 세대 대조용으로 retained다. 기존 source26 집계는 hash 참조, 새27일 확인점은 약식 관측 identity/특징만 gzip으로 보존하며 AI 입력 원장은 복제하지 않는다.

검증: source26의6종목157점에서 원 native key·입력 특징·라벨 parity 불일치0; 당일 통계93점 exact native 경로 재검증 불일치0; 관련 테스트156 PASS; compile PASS. 테스트 cache 쓰기 권한 경고1건은 결과 캐시 저장 경고이며 테스트 실패는 없다. 불변 파일 충돌·당일 중복 합산·첫 U/STOP 통계창 점유·PRE/AFTER 배제·완성봉 revision/부적격 보존·N0/null을 확인했다. 실제 재생13.35초, 신규 연구 산출물 약4MB이며 원 정규화4.4MB는 재사용했다. 운영 소스 변경0, provider 호출0, 주문·등록·배포·재기동0이다.

## 12. 미확정86점 원천 보강과 A09 운영 준비 — 17:16

**판단:** 저가A09 한 범위의 채택을 권고하며 코드 배포 준비는 완료했다. 정식 정책 게시에는 source27 native 장후 입력과 명시적 채택·배포 지시가 남아 있다. 현재 정책을 바꾸거나 봇을 재기동하지 않았다. 이번 요청은 준비·검증과 가능 여부 보고이며 실제 정책 활성화·배포 승인으로 해석하지 않았다.

근거: [재집계 원본](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/comparison-supplemented-2e673a929812.json), [최종 준비 검증](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/readiness-review.json).

### 원천 보강과 제외

- 원86개 key·174개 반복 확인점·93개 시간순 확인점과 기존 source26 누적 집계를 고정했다. 새 source의 미래 승패로 확인점이나 후보를 다시 선정하지 않았다. 비용0.0023·실제 진입ask·1800초 내 비용후+0.4%·비용후−3% 선도달 없음의 원 라벨을 유지한다. WIN/STOP/TIMEOUT을 확정 분모로, U를 별도로 보고하며 손익비·EV를 선택 조건으로 쓰지 않는다.
- 기존78개 동일 `symbol_AL` item에 기존 SOURCE_ONLY 분봉 수집 경로를 사용해78개 모두 응답을 보강했다. 공식 참조 revision `953e5dbff123f437ab4d11a78a95191a685eb51f`와 실제 ka10080 consumer를 먼저 대조했다. 기존 인증 cache·request owner/rate cap을 사용했고 토큰 발급·구독 추가·주문·신규 AI 호출은0이다. [참조와 조회 기록](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/official-reference.json), [보강 receipt](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/supplement-status.json).
- WS/REST 완성봉101개 원천 revision을 hash로 고정했다. 원 정규화 partition을 재사용하고 정규장 종료15:30까지 완성된 동일 item 봉만 썼다. 서로 다른 revision을 이어 붙이거나 AFTER를30분 경로에 넣지 않았다. 첫 봉 경계·두 장벽 동시 접촉·시각 해석 충돌은 기존 native 보수 판정을 유지했다.
- 원 U86은 **WIN32/FAIL_TIMEOUT42/FAIL_STOP1/U11**로 바뀌었다. 원 확정7점을 포함한 고유93점은 WIN38/TIMEOUT42/STOP2/U11이다. 이93점은 여러 대안 정책의 확인점 집합이므로 하나의 운영정책 승률로 합산하지 않는다.
- 잔여11점은 populated REST revision의 **중간 결손5점·종료 구간 부족3점·시각 해석 불일치3점**이다. 빈 primary WS 경로의 외부 reason `completed_bar_start_missing`을 실제 REST도 전부 없다는 뜻으로 해석하지 않는다. [revision별 진단](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/residual-revision-diagnostics.json)의 원 label과 각 clock 결과를 보존했고11점은 승률 분모에서 제외한다. 같은 요청 반복·결손 봉 보간은 하지 않는다.

시장 identity는 session=REGULAR, 정책 cohort=비상시·가격유형·SOR, data item=`_AL`/정규장 partition이다. 논리 SOR와 실제 체결 거래소는 별개다. 이번에는 주문 요청·체결 receipt가 없으므로 effective broker route/actual execution venue를 체결 사실로 추정하지 않는다. 원 무수신52lease와 이86점은 별도 분모다.

### 당일·누적 재집계

각 후보는 **현행∪추가 단일패턴**이다. 종목·날짜·route별 첫 확인점이1800초 통계창을 점유하며 첫 U/실패를 나중 WIN으로 교체하지 않는다. 실거래 cooldown을1800초로 변경하는 뜻이 아니다. 누적은09/29 이후 기존 적격10일과10/27이며 역사 제외 원천일/행의 자격을 바꾸지 않았다. 당일 고정 현행은 세 유형 모두 확인점0이며 운영 전체 이벤트0건을 뜻하지 않는다.

| 유형·후보 | 당일 W/STOP/TIMEOUT/U | 당일 W/N | 누적 W/N·승률 | 누적 STOP/TIMEOUT/U | 누적 L |
|---|---:|---:|---:|---:|---:|
| 저가 A05 |4/1/4/1|4/9 ·44.4%|40/71 ·56.3%|3/28/51|44.77%|
| **저가 A09** |**11/0/5/5**|**11/16 ·68.8%**|**113/204 ·55.4%**|**9/82/118**|**48.53%**|
| 고가 A12 |0/0/1/0|0/1 ·0%|12/21 ·57.1%|1/8/17|36.55%|
| 고가 A14 |2/0/7/1|2/9 ·22.2%|15/38 ·39.5%|0/23/24|25.60%|
| 중가 A08 |21/1/25/4|21/47 ·44.7%|187/581 ·32.2%|5/389/363|28.51%|

| 후보 | 누적 시간순 추가 WIN/실패 | 제거된 기존 WIN | 승리 순증 |
|---|---:|---:|---:|
| 저가 A05 |+40/+31|2|+38|
| **저가 A09** |**+112/+91**|**1**|**+111**|
| 고가 A12 |+11/+9|0|+11|
| 고가 A14 |+15/+23|1|+14|
| 중가 A08 |+186/+394|3|+183|

추가/제거는 합집합의 시간순 재선택에 의한 key 변화다. A09의 최종113승은 현행2승에112승이 추가되고1승이 대체된 결과다. 중가A08의 U는 기존1점 제거·신규361점 추가로363점이다. 추가 승리·실패는 주문 또는 실현 손익이 아니다.

현행 L은 저가2/2=34.24%, 고가1/1=20.65%, 중가4/4=51.01%다. A09는 raw 승률이 현행100%보다 높다는 주장이 아니라 사전 고정된 표본 보정 점수로 가장 높은 저가 후보라는 판단이다. A09의 누적 U118점·날짜/종목 상관은 남는다. 최근10/22~27은75/102승이고 초기 날짜의 낮은 성적도 누적에 그대로 포함한다. 새 최소 N·추가 승률 문턱·기존 WIN 전부 보존 조건을 만들지 않았다.

고가A12는 누적 연구 순위가 앞서지만 오늘 새 확인점은 TIMEOUT1점이다. 이번 준비 범위에 포함하지 않는다. 중가A08은 당일 미달25점이 새로 확정됐고 누적 TIMEOUT389점으로 여전히 현행보다 L이 낮아 carry한다. 늦은60분 회복을30분 WIN으로 승격하지 않았다.

### A09만 바꾸는 정책 준비와 소비자 검증

기존 cumulative owner에 exact-scope/candidate 준비를 추가했다. `prepare-scoring --scope other_non_fixed|REGULAR|LT_20000|SOR --candidate A09`는 저가A09 대안만 만든다. 부분 범위 계약은 `unscored_scope_policy=carry_parent`와 전체128개 부모 membership을 고정한다. 적용 시 다른127개 scope를 원 승률 선택기로 다시 고르지 않고 그대로 승계한다. 부모·날짜·원천·registry·code·정의·범위 불일치는 거부한다.

[저장된 제안](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/a09-unapproved-proposal.json)은 `operator_receipt=null`이며 활성/대기 정책 경로에 쓰지 않았다. 메모리 안의 테스트 authority로 실제 `apply_selection → machine_cells → validate_family → assess`를 실행한 [격리 검증](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/a09-policy-input-validation.json)에서 변경 scope1·승계127·A09 확인점29건/보조 입력29건을 확인했다. 보조 프롬프트·binding은 유지했고 실제 AI를 호출하거나 PASS를 강제하지 않았다. 이 검증은 정식 A09 정책 receipt나 실제 기동 증거를 대신하지 않는다.

최종 불변 코드 후보는 `/home/ubuntu/KORStockScan-runtime-releases/regular-a09-ready-20261027-a1b1b0f8a`, commit `a1b1b0f8a54aaad8b1ac5546824329b4e958cdd8`다. 준비 중 운영이 d5→2b→3178→3a로 바뀌어 마지막 기준 `3a989b283446805cf5c2e5523b9d986228175b1a`의 canonical identifier 진단 수정까지 통합했다. 각 이전 후보/실패/통과를 보존하고 selector 기준을 새로 고정했다.

- 현행 bundle `6b93eb6a16efc2a7a349fcdbd347146200830034d5697564a6500e3ed2472f92`의 fixed workload128scope/76,800행/569신호는 전후 동일하며 signal hash도 같다. [최종 parity](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/active-policy-handoff-a1b1b0f8a/active-policy-parity.json).
- native unchanged-policy [code handoff](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/active-code-handoff-a1b1b0f8a.json)와 [제출 지연·손절·보유·활성정책·현행 report 검증](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/native-read-only-candidate-closure.json) 모두 PASS다.
- 최종 native [P5](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-27/3df8bb88c9144f588cd1923b094df299/final.json)는 network/filesystem 격리 load/exit PASS·findings0·child 종료를 확인했다. 기존 활성 정책을 새 코드로 읽는 기동 검증이며 아직 게시하지 않은 A09 정책의 P5는 아니다. 실행 전후 selector/정책 pointer는 같고 실제 Main 전환은0이다.
- 검토 시각 운영3a/PID1781860의 실제 start/cwd를 native receipt와 `/proc`로 대조했다. 이 PID는 다른 승인 작업이 배포한 현행이며 A09 후보의 PID 소비로 표시하지 않는다.

### 발견 결함·수리·교체·검증

첫 후보 afd40c94b의 P5는 `entry_consumer_reviewed_dependency_unreviewed:...continuous_reversal_policy_v6.py`로 intake에서 차단됐다. 새 선택 코드3개가 준비 consumer의 완전한 의존 세대와 독립 preparation reader에 연결되지 않은 것이 첫 결손이었다. 기존 handoff/profile owner에 정확한3개 파일과 독립 reader의 전체 세대를 결속했고, 원 부모 digest와 기존 승인 세대는 보존했다. unknown·missing·dirty·committed mutation·parent mix의 거부를 계속 검증했다. 오류 문자열 허용 확대나 stale PASS 재사용으로 통과시키지 않았다. [원 실패](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/candidate-p5-reference.json), [최종 통과](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/candidate-p5-reference-a1b1b0f8a.json).

임시 점검 실행기에서 active receipt 발급 전 병렬 읽기1회는 FileNotFound로 남겼다. 발급 후 그 의존 consumer만 재검증해 closure에 원 실패 hash를 연결했다. 운영 제품의 receipt/상태를 수작업으로 바꾸지 않았다. 다른 운영 전환의 lock 보유 중 resource check1회도 대기 실패로 보존하고 실제 전환/lock 종료 확인 후 정상 native 검증을 수행했다.

교체/보존 disposition은 다음과 같다.

| 기존 owner/경로 | disposition | 최종 소비자/이유 |
|---|---|---|
| `reversal_cumulative_registration.select_variant`의 raw 비율 전용 선택 | consolidated | 같은 함수가 승인 scoring 범위에는 시간순 L을 적용하고 승인 없는 기존 범위·역사 계약에는 원 비교를 유지 |
| `reversal_cumulative_postclose`의 반복 집계 | consolidated | 같은 incremental snapshot/store와 원 metric에 chronological projection을 함께 산출; AI 원장 복제 없음 |
| `continuous_reversal_policy_v6`의 manifest/cell 검증 | retained/extended | 동일 runtime assessor가 선택 계약·실행 metric 결속을 검증 |
| native handoff/독립 preparation reader | retained/extended | 기존 정확 세대·역사 reader 유지, 새 complete generation 추가; 별도 우회 validator/실행 wrapper 없음 |
| 원 source26/source27 실행기·20:05 waiter·이전 불변 후보 | retained | 원 hash·실패·다음 native 대조의 실제 소비자; 이번에 삭제하거나 핀을 변경하지 않음 |

최신 운영3a→후보a1 비교에는 선행 b226 선택구조 구현도 포함한다. 비테스트 source **+779/−12**, tests **+656/−4**, docs **+367/−1**이며 후속 결과 문서 갱신은 별도다. 새 engine-root 모듈·새 런타임 dispatch·새 schedule은0이다. 순증은 선택 계약/통계 projection과 scoped 준비·정확 세대 호환 검증이며 단순 이동·축약을 개선으로 세지 않았다.

검증은 관련 cumulative/보조입력134 PASS(포함된 cumulative83 PASS와 중복 합산하지 않음), 최종 native generation/손상 회귀69 PASS, 독립 preparation131 PASS, 통합된 canonical receipt 진단43 PASS다. compile과`git diff --check`도 PASS다. 이전 broad preparation 전체 묶음은 반복 clone 비용 때문에 중단한 원 로그를 남겼고 전체 PASS로 보고하지 않는다. source26의157점 parity와 source27 확인점 검증은 §11의 고정 결과를 재사용했다. 이번 보강은 실제 원천 read만78item, AI0·주문0이다.

후보 생성 전 native release-set/PID 검증 PASS, 관리 릴리스164→165·등록 worktree275→276·추가 recovery1개 및 작업 공간2GiB를 예약했다. 여유 약57.9GB였고256 제한은 systemd unit census 한도이며 디렉터리 개수 상한으로 적용하지 않았다. [자원 근거](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/capacity-inventory-observer.json). 새 AI 비교 원장·누적 raw 복제는 만들지 않았고 unreferenced 판정 없는 삭제도 하지 않았다.

### 남은 정식 게시와 다음 실행 경계

1. 현재 source27 `main_machine_policy` native terminal이 없으므로 정식 `prepare_scoring`은 `cumulative_scoring_source_terminal_invalid:main_machine_policy:terminal_missing_or_invalid`로 차단된다. [원 경계](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/formal-preparation-boundary.json)와 최종 read-only stage 점검이 일치한다. 정규장 연구는 이 gate와 무관하게 위 결과까지 완료했다.
2. 기존20:05~23:59 연구 waiter는 pinned 원 코드/프로토콜을 그대로 유지한다. 정상 EOD20:05 이후20:10 장후 흐름에서 실제 source27 machine terminal이 유효해지면 같은 확인점·보강 라벨과 native 결과의 차이를 대조하고, 최신 부모에서 **저가A09 단독 범위**로 정식 prepared-scoring을 생성한다. source/date/부모가 달라졌으면 새 근거로 준비하며 옛 JSON을 승인 receipt로 바꾸지 않는다.
3. 명시적 채택·배포 지시 후에만 native `intake-scoring`과 대상 machine/하위 정책 준비를 수행한다. 바뀐 세대의 직접 의존 단계만 재생성하고 EOD나 변경 없는 전체 원장을 재생성하지 않는다. A09가 선택된 실제 정책의 인계·P5와 최종 prepared-generation 검증을 별도로 수행한 뒤 native ordered transition으로 배포·재기동하고 exact PID 소비를 확인한다. 코드 배포만 먼저 승인되면 현행 정책 유지 범위로 가능하다.
4. 실제 정책 적용 후 기존 owner의 **2026-10-28 09:30~10:00 KST REGULAR/SOR/_AL**에서 A09 native 확인점→AI 입력→판정 receipt 소비를 관찰한다. 표본 없으면 자연 수용 OPEN을 유지하며 실제 주문을 만들어 수용시키지 않는다. 실제 체결 venue·경제적 성과는 별도 증빙이다.

따라서 **코드 후보 배포 준비 PASS / 저가A09 채택 권고 / 정식 A09 게시·실제 기동 수용 OPEN**이다. 새 bootstrap/PREOPEN/PID 증거를 만들지 않았고 현재 릴리스·정책을 유지했다.

## 13. 장후 적용 순서와 준비 완료 범위 정정

사용자의 재검토 요청에 따라 실제 wrapper·producer·stage reader를 대조했다. **이전 준비 PASS는 현행 부모 정책을 새 코드로 읽는 검증이며 신규 A09 scoring의 장후 전체 완주 증거가 아니다.** 연구 수치와 원 P5는 변경하지 않는다. [추가 검토](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/postclose-integration-review.json)가 이전 readiness 보고서의 판단 범위를 정정한다. 기존 native receipt를 수정하지 않았다.

확인한 첫 결손과 미검증은 세 가지다.

1. 후보 `reversal_cumulative_registration.prepare_scoring`은 native `main_machine_policy` 완료를 먼저 요구한다. 이후 `intake_scoring`이 producer 입력 `cumulative-scoring.json`을 바꾸므로 기계 보고서와 terminal을 다시 만들어야 한다. 정상 wrapper는 기계 stage 뒤 다른 작업과 보조 stage를 진행하며 신규 intake를 기다리는 적용 barrier가 없다. 따라서 이전의 '기계 완료→신규 계약 intake→일부 재생성'을 자동 작업과 병행할 수 있는 안전한 실행 순서로 제시한 것은 잘못이다. bound 출력·선행 receipt·입력이 바뀌면 native reader는 각각 `output_generation_changed`·`prerequisite_generation_changed`·`input_generation_changed`로 거부한다. 이번에 실제 장후 실패를 발생시키거나 재실행하지는 않았다.
2. 새 CP 보고서는 `scope_bound_chronological_wilson_and_raw_fraction`을 선언하지만 CP terminal의 `selection_basis`와 stage reader는 `cumulative_raw_win_fraction`에 고정돼 있다. 실제 source26의 유효 report/terminal을 메모리에 복사해 metric만 새 값으로 바꾸고 hash를 일관되게 계산한 격리 reader 대조에서도 raw terminal이 accepted됐다. 이는 producer/consumer의 의미 불일치이며 경고가 없어도 준비 완료로 볼 수 없다. 단순히 허용 문자열을 늘리거나 기존 terminal을 수작업으로 바꾸어 해결하지 않는다.
3. 현재 운영은 auxiliary tuning enabled·128개 union_v6 scope다. 기존 검증의 A09 private family/29개 입력과 현행 정책 P5는 실제 설정의 기계→보조 campaign→정책 게시→native stage→summary/strict/controller→PREOPEN→새 정책 P5를 함께 검증하지 않았다. 이 마지막 소비자 연결은 OPEN이다.

'무조건 에러'를 실제 관측 결과로 단정하지는 않는다. 최초 검토 기준은 운영3a/활성6b93였다. 검토 중 별도 작업이 운영 릴리스를f14f42989로 전환했고 활성 정책6b93는 같았다. 최신 실제 stage reader로 같은 격리 대조를 수행해 raw/scoped 불일치 수용과 scoped terminal 거부를 다시 확인했다. [최신 consumer 대조](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/postclose-integration-current-consumer.json). 미승인 A09 제안은 이번 작업에서 native pending/active에 등록하지 않았다. 이번 결손은 신규 A09 적용 절차와 의미적 연결에 대한 것이다.

### 수정한 구현·검증 순서

- 기존 `prepare_scoring` owner의 준비 입력을 **검증된 native 원천·preflight·현재 부모/registry/code**로 먼저 고정할 수 있도록 보완한다. 새 선택 계약의 준비를 그 계약으로 재생성할 완료 보고서에 의존시키지 않는다. 새 stage/우회 wrapper/가짜 terminal을 만들지 않으며 원 source·제외·실행 권한 검증은 유지한다. 이 source-first 경로는 아직 구현되지 않았다.
- 비교 완료된 A09 범위의 미승인 준비 계약과 채택/배포 근거를 검토하고, 승인된 경우에만 **첫 기계 stage 전에** native intake를 끝낸다. 승인·정식 원천·코드가 준비되지 않았으면 현행 정책으로 통상 장후를 완료한다. 작업 중 승인 대기나 신규 계약 삽입을 하지 않는다.
- 기계 보고서/terminal/manifest가 동일한 실제 metric·통계 계약·source/parent를 선언하고, native stage reader가 그 결속을 확인하도록 기존 producer/consumer를 함께 보완한다. 역사 raw 계약 reader는 유지한다.
- 고정된 입력과 같은 코드로 최종 기계→실제 설정의 보조→정책/각 stage→summary/checklist/strict/controller→다음 PREOPEN을 순서대로 닫는다. 전체 EOD/raw/AI 원장을 반복 생성하지 않는다. 기존 봉인 세대를 사후 변경하는 경우에는 현재 native recovery owner가 무효화된 마지막 소비자까지 재봉인해야 한다.
- 위 실제 경로를 동일 원천의 격리 환경에서 실행하고 missing/stale/conflict/새 세대/실패 unwind를 검증한다. 새 A09 정책 load/exit와 최종 prepared-generation 검증 뒤에만 승인된 ordered transition으로 배포·재기동한다. 이를 통과하기 전 포괄적인 '장후 포함 배포 준비 완료'를 주장하지 않는다.

현재 결론은 **A09 통계상 채택 권고 유지 / 현행 정책 코드 로드 PASS 유지 / 신규 scoring 장후 통합·의미 결속 수리 및 배포 준비 OPEN**이다. 기존 stable owner `MachinePatternOpportunityResearch1023`에 이어가며 런타임·스케줄·provider·정책 변경은0이다.

## 14. Source-first 수리·최신 운영 통합·배포 승인

사용자는 10/27 배포·재기동을 명시 승인했다. §13의 결함을 기존 준비/선택/장후 owner에서 수리하고 최신 운영 `6d48e76e5`를 통합했다. source-first 준비는 native EOD/preflight/binding/원천·부모·registry·code를 고정하고 기존 stage writer와 CAS한다. wrapper의 신규 준비 연결은 명시 승인된 exact-date 요청이 있는 경우에만 첫 machine launch 전에 동작한다. 요청 부재는 기존 장후 경로를 그대로 진행하며, 오류 요청은 실행 전에 차단한다.

terminal·stage reader의 metric/hash 결속과 실제 탐지 membership cache key를 함께 수리했다. 최초 stage fixture는 호환 projection만 바꾸고 실제 native report를 바꾸지 않아 실패했으며, 두 실제 소비 입력을 함께 연결한 뒤 통과했다. 원 실패 로그를 유지한다. 요청 fixture의 원천 원본 변경과 불변 archived 증거 변경은 첫 build와 exact resume의 서로 다른 검증 경계로 구분했다.

- 원천 준비·기계·enabled 보조튜닝 회귀: `source-first-reviewed-tests.log`, 296 PASS.
- 실제 wrapper 분기: `source-first-wrapper-tests.log`, 2 PASS. preflight 뒤·첫 launch 전 순서, 승인 요청 부재 시 정상 진행, 잘못된 요청의 launch 차단을 검증했다.
- 독립 Main 준비 reader: `source-first-independent-reader-tests.log`, 28 PASS. 원본/후속 hash·unknown 경로 및 changed generation 차단을 포함한다.
- 광범위 역사 profile 전수 회귀는 불필요하게 큰 조합이어서 176 PASS 후 중지했다. 이 중지 실행은 전체 PASS로 표시하지 않으며 `source-first-integration-gates.log`를 보존한다. 변경된 실제 profile·owner 및 원래 guard에 집중한 회귀로 대체한다.

교체: 완료 machine을 선행 요구한 준비 의존은 제거하고 source-first 준비로 대체했다. raw metric 중복 판정은 G의 단일 metadata owner로 통합했다. 기존 역사 raw/scoped profile·immutable receipts·현재 Main/보조/게시/주문 owner는 소비자 증거 보존을 위해 유지한다. 새로운 engine-root 모듈·원장·stage·cron은 추가하지 않았다.

전체 source27 장후의 새 A09 마지막 소비자 수용은 아직 OPEN이다. 코드 배포·현행 정책 P5·실제 PID 소비와 신규 A09 채택·전체 장후/PREOPEN·자연 REGULAR/SOR/_AL 수용·실현 경제성을 각각 기록한다. 신규 선택 계약 또는 정책을 수동 작성하거나 과거 PASS/terminal을 재사용해 이 경계를 닫지 않는다.

후속 causal review에서 enabled 보조튜닝이 `machine.json`을 게시용 generation으로 교체한 뒤 기계 stage reader가 원 terminal과 비교하는 결함도 확인했다. H는 이제 원래 immutable `machine-comparison.json`과 stage에 결속된 호환 projection의 동일성을 검사한다. 보조 게시본은 보조/정책 소비자가 검증하며, 원 comparison/projection 변조는 계속 차단한다. 수리 후 stage141 PASS와 실제 enabled T campaign→issue 경로1 PASS를 확인했다. 이 1건은 무호출 private fixture이며 새 A09 전체 장후·정책 게시/P5의 운영 증거가 아니다.
