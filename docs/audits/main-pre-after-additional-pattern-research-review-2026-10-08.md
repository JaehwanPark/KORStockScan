# Main 프리·통합 애프터 추가 패턴 연구 검토 — 2026-10-08

## 1. 결론과 실제 운용 범위

사용자 정정을 반영하여 **프리=NXT `_NX`, 정규·통합 애프터=SOR `_AL`**로 구분했다. 이번 연구는 프리 NXT와 통합 애프터 SOR만 수행했다. 128개 정책 계약 셀이 모두 실운용 중이라는 해석을 철회한다. 정정 전에 계산된 다른 19개 파티션은 manifest의 `out_of_scope_partitions`에 격리하고 선별/등록 인계에서 제외했다.

[연구 실행계획](../proposals/main-pre-after-additional-pattern-research-plan-2026-10-08.md)에 따라 32개 논리 범위를 확인했다. **13개 범위에서 추가 연구 후보를 확보**했다. 9개는 기준의 확정 결과가 있어 단순 확인점 합집합의 누적 승률 개선 또는 동률 추가 성공을 확인했고, 4개는 기존 기준의 확정 결과가 없어 개선 우위를 주장하지 않는다. 18개는 이번 원천에서 확인점이 없고, 알테오젠 AFTER 고가 1개는 개선 후보를 찾지 못했다.

운영 변경 없이 [13개 제안 batch](../../tmp/main-pre-after-pattern-research-20261008/proposed-registration-batch.json)를 만들었다. 실시간 등록·보조 PASS·실제 주문·실현 수익이 아니다. 사용자 지정 초기 채택이 승인되었다고 해석하지 않는다.

현재 owner는 [오늘 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry`를 재사용한다. 기존 체크리스트/봉인/다른 세션의 작업본은 수정하지 않았다.

## 2. 원천·계산 계약

- 프리 NXT 6개 날짜, 통합 AFTER SOR 9개 날짜의 **15개 파티션, 1,040,713개 가격 행**. 기간은 9/21~10/7의 실제 보유 원천이며 9/21 item 미입증 자료를 정상으로 복원하지 않았다. [원천·코드 manifest](../../tmp/main-pre-after-pattern-research-20261008/manifest.json), [scope별 원천 census](../../tmp/main-pre-after-pattern-research-20261008/source-coverage.json).
- 기준은 오늘 활성 bundle `cdacf6eed9d77e95d0bdf1a417ec2549323ea2491b91e41b8f948b900434895f`의 정확 group/session/price-band/route 정책이다. 당시 실제 적용 버전 전체의 성과를 합친 것이 아니라 오늘 기준 정책을 누적 원천에 재생한 비교다.
- 첫 반전·회복 유지·재시험·고점 회복과 선행 하락을 요구하지 않는 고점 돌파·모멘텀·고저 동반 상승 총 **44개 확인 정의**를 사용했다. 종목 흐름·속도·고저 구조·낙폭 및 호가/거래량/BUY/VWAP 필터를 수동 연구의 유한 조합으로 비교했다. 외부 지수 국면으로 표현하지 않는다.
- 실제 확인 ask, 새 1,800초, 비용률 .0023, 순 목표 +.4%, soft stop -3% 선도달. WIN, FAIL_STOP, 완전 미도달 FAIL_TIMEOUT, 불완전 관측 UNRESOLVED를 분리한다. 성공 100%/80% 보존·최소 표본/일수·EV/holdout gate를 추가하지 않았다.
- 10분 이후 가격도 평가한다. 마지막 tick 이후에 보유한 동일 item 완성 분봉을 버리지 않고 native의 명시 cutoff만 적용한다. 신호 특징의 과거 접두와 결과 평가의 이후 경로를 구분한다. 리뷰 중 임의 last-tick cap을 제거하여 U 261개를 WIN 23·STOP 31·TIMEOUT 207로 정정했다.
- 신규/기준을 합쳐 확인점 285,975개를 라벨링했다. **270,120개 유한 조합을 확인, 126,623개 비어 있지 않은 후보**를 보존했다. 10/7 매칭 여부로 과거 후보를 배제하지 않았다. 많은 가설을 같은 자료로 탐색한 결과이며 독립 미래 성과가 아니다.

## 3. 범위별 우선 후보

다음은 **각 범위의 후보 1개**를 기존 정책에 추가한 단순 확인점 합집합이다. 목표 시각 수는 `(날짜, 종목, item, 목표 도달 시각)` 중복을 제거한 집중도 진단이며 독립 매매 수는 아니다. W/F/U는 추가된 확인점의 결과다. 기존 비매칭의 FALSE/UNKNOWN에 따른 기여도 한계는 §5에 따로 남긴다.

| 종목군·가격대 | 세션 | 기존 → 후보 1개 추가 합집합 | 추가 W / F / U | 추가 목표 시각 수 |
|---|---|---|---:|---:|
| 삼성전자·전체 | PRE NXT | 미확정 → 100.00% (13/13) | 13 / 0 / 861 | 2 |
| 삼성전자·전체 | AFTER SOR | 30.17% (207/686) → 44.32% (745/1681) | 538 / 457 / 814 | 7 |
| 두산·2만~10만원 미만 | PRE NXT | 69.12% (47/68) → 70.83% (51/72) | 4 / 0 / 77 | 3 |
| 두산·2만~10만원 미만 | AFTER SOR | 100.00% (32/32) → 100.00% (39/39) | 7 / 0 / 6 | 2 |
| HPSP·2만~10만원 미만 | AFTER SOR | 미확정 → 100.00% (9/9) | 9 / 0 / 0 | 3 |
| 알테오젠·10만원 이상 | PRE NXT | 미확정 → 100.00% (60/60) | 60 / 0 / 571 | 2 |
| 주성·10만원 이상 | AFTER SOR | 19.88% (34/171) → 37.17% (113/304) | 79 / 54 / 10 | 9 |
| 일반 비삼성·2만원 미만 | PRE NXT | 35.29% (24/68) → 72.51% (153/211) | 129 / 14 / 14 | 25 |
| 일반 비삼성·2만~10만원 미만 | PRE NXT | 87.50% (7/8) → 96.67% (29/30) | 22 / 0 / 2 | 4 |
| 일반 비삼성·10만원 이상 | PRE NXT | 미확정 → 100.00% (6/6) | 6 / 0 / 1 | 3 |
| 일반 비삼성·2만원 미만 | AFTER SOR | 62.53% (272/435) → 71.62% (434/606) | 162 / 9 / 265 | 18 |
| 일반 비삼성·2만~10만원 미만 | AFTER SOR | 81.71% (143/175) → 84.91% (180/212) | 37 / 0 / 5 | 4 |
| 일반 비삼성·10만원 이상 | AFTER SOR | 54.70% (221/404) → 58.32% (277/475) | 56 / 15 / 238 | 7 |

4개 `baseline_unresolved`는 삼성 PRE, HPSP AFTER, 알테오젠 PRE, 일반 고가 PRE다. 기존 미확정을 0%로 치환하지 않는다. 삼성 AFTER의 추가 538 WIN은 **9/22 한 날짜의 7개 목표 시각**에 집중된다. 알테오젠 PRE 추가 60 WIN도 10/7의 2개 목표 시각이다. 반복 확인점을 독립 성공 사례로 과장하지 않는다.

### 정확 후보 정의

`FIRST`는 첫 반전, `PEAK`는 원 고점 회복, `RETEST_FIRST/PEAK`는 저점 재접촉 후 원 FIRST/고점 회복, `MOMENTUM`은 60초 수익률 전환이다. 모든 유형/필터는 실제 확인 시점에 판정한다. `dd`는 이 연구에서 `100*(이전 300초 고점/확인가격-1)`이며 기존 legacy FIRST의 저점 기준 DD와 다르다. 포함/제외 경계와 숫자 계약은 제안 batch에 고정했다.

- `samsung|PRE|ALL|NXT`: `FIRST::dd=GE1.2::ANY`. 추가 확인점 발생 날짜: 2026-10-07.
- `samsung|AFTER|ALL|SOR`: `MOMENTUM_0.05::trend=DOWN&dd=LT0.2::VWAP_GE0`. 추가 확인점 발생 날짜: 2026-09-22.
- `034020|PRE|20000_TO_100000|NXT`: `PEAK_WAIT120_TOL0.2::ALL::ANY`. 추가 확인점 발생 날짜: 2026-10-07.
- `034020|AFTER|20000_TO_100000|SOR`: `FIRST::trend=DOWN&dd=0.2-0.4::BUY10_GE60`. 추가 확인점 발생 날짜: 2026-09-22, 2026-10-07.
- `403870|AFTER|20000_TO_100000|SOR`: `FIRST::trend=DOWN&dd=0.2-0.4::BUY10_GE60`. 추가 확인점 발생 날짜: 2026-10-07.
- `196170|PRE|GE_100000|NXT`: `PEAK_WAIT120_TOL0.2::trend=UP::ANY`. 추가 확인점 발생 날짜: 2026-10-07.
- `036930|AFTER|GE_100000|SOR`: `FIRST::speed=FAST::ANY`. 추가 확인점 발생 날짜: 2026-09-23, 2026-09-29, 2026-09-30, 2026-10-07.
- `other_non_fixed|PRE|LT_20000|NXT`: `FIRST::trend=NEUTRAL&dd=0.4-0.8::ANY`. 추가 확인점 발생 날짜: 2026-09-29, 2026-09-30, 2026-10-02, 2026-10-06, 2026-10-07.
- `other_non_fixed|PRE|20000_TO_100000|NXT`: `RETEST_PEAK_WAIT120_TOL0.2::trend=UP&dd=0.2-0.4::BUY10_GE60`. 추가 확인점 발생 날짜: 2026-09-30, 2026-10-02, 2026-10-07.
- `other_non_fixed|PRE|GE_100000|NXT`: `MOMENTUM_0.2::trend=NEUTRAL&speed=FAST&shape=RISING::ANY`. 추가 확인점 발생 날짜: 2026-09-29.
- `other_non_fixed|AFTER|LT_20000|SOR`: `RETEST_FIRST_WAIT30_TOL0::trend=DOWN&speed=SLOW&shape=MIXED::ANY`. 추가 확인점 발생 날짜: 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-28, 2026-09-29, 2026-10-07.
- `other_non_fixed|AFTER|20000_TO_100000|SOR`: `MOMENTUM_0.2::trend=DOWN&dd=0.4-0.8::VOL_GE1`. 추가 확인점 발생 날짜: 2026-09-22.
- `other_non_fixed|AFTER|GE_100000|SOR`: `RETEST_FIRST_WAIT30_TOL0.2::trend=NEUTRAL&speed=SLOW&shape=MIXED::ANY`. 추가 확인점 발생 날짜: 2026-09-21, 2026-09-22, 2026-09-23.

특히 삼성 AFTER는 하락 흐름에서 낙폭이 0.2% 미만으로 줄고 60초 수익률이 +0.05%를 상향 통과하며 VWAP 위에 있는 상승지속 경로다. 첫 반전을 선행 조건으로 요구하지 않는다. 두산 PRE는 원 고점 회복, 일반 저가 AFTER는 저점 재시험 후 회복이 우선 후보다.

큰 탐색 합집합/대체 상위 3개는 [전체 결과](../../tmp/main-pre-after-pattern-research-20261008/result.json)에 남겼다. 큰 합집합의 수백 정의를 일괄 등록하도록 제안하지 않는다. 구현 인계 batch는 위 13개로 제한하며 중복·기여도·실시간 비용을 후보별로 검토한다. 알테오젠 AFTER는 이번 가설에서 새로운 WIN이 없어 실패/미확정을 없애서 후보를 만들지 않았다.

## 4. 원천 재생과 결과 검증

- 기존 native 장후 확인점 **6,603개**와 이번 기준 재생의 canonical identity가 전부 일치한다. 추가/누락 0, 결과 라벨 불일치 0. [native 대사](../../tmp/main-pre-after-pattern-research-20261008/validation-native.json).
- native store는 `readonly=True`로만 열었다. 해당 records/mask의 해시를 검증하고 연구 receipt를 별도 고정했다. 공유 provider 원장/예약/응답을 변경하지 않았다.
- 15개 파티션 중 확인점이 있는 14개에서 분산 표본 **3,500개**를 독립 선형 선도달 계산으로 대조했다. 불일치 0. 보조 분봉의 clock/양 장벽 처리는 기존 native Bars 함수를 재사용했다. 따라서 분봉 라벨 구현까지 완전히 독립 검증했다고 주장하지 않는다. [라벨 검증](../../tmp/main-pre-after-pattern-research-20261008/validation-labels.json).
- 실제 가격 행이 있는 운용 scope는 14개다. HPSP·주성의 PRE NXT는 이번 보유 원천 census에 없다. 이들의 정규장/애프터 자료를 프리 결과로 치환하지 않았으며, 나머지 비어 있는 논리 가격대도 임의 정책으로 채우지 않았다.
- 미래 접두 불변, 무하락 상승 탐지, UNKNOWN 재무장 방지, 순번 단절, 확인 ask, 동일점 union, 이후 보유 분봉 사용과 기존 경로 계약의 targeted **19 pytest PASS**. 연구 스크립트 compile 및 문서 link/parser/diff 검사는 closure receipt로 남긴다.

## 5. 추가 발견: 기여도 UNKNOWN의 생산자·소비자 불일치

현재 native coverage mask와 대조하면 다수 후보의 추가점이 `exclusive_unproven`이다. 이를 모두 실제 원천 결손으로 해석하면 안 된다. [실제 source 재현](../../tmp/main-pre-after-pattern-research-20261008/coverage-defect-reproduction.json)에서 다음을 확인했다.

- 9/22 삼성 AFTER 17:27:18.198: native 연속성·호가 정상.
- 기존 `legacy_dd5_ge_0_4_v1`의 FIRST 원 낙폭은 **0.3656307129798919%**로 조건 `.4`를 충족하지 않아 native `matches=False`다.
- 같은 점의 `coverage()`는 **UNKNOWN**을 반환한다. `State.features()` 반환에는 `dd`/`volume`이 없고 observe 안의 별도 지역 사본에만 보강되기 때문이다. 소비자는 없는 alias를 가격 원천 부족처럼 해석한다.

따라서 이 결함은 **기여도 보고서의 FALSE/UNKNOWN 분류 보완 대상**이다. 이 한 사례를 모든 UNKNOWN에 일반화하거나 기존 report를 임의 성공으로 덮지 않았다. 실제 단절/미확정은 그대로 남긴다. 현재 mask 기준으로 두산 PRE와 일반 저가 AFTER는 후보의 추가점이 모두 관측 가능하며 합집합 개선이 확인된다. 삼성 PRE도 추가점 자체는 관측 가능하지만 기준 결과가 미확정이다. 나머지는 PA11을 보완한 정확 phase coverage 재집계와 함께 단독 기여도를 확정해야 한다.

이 문제는 새 패턴 연구를 무효로 만들거나 현재 ENTER 권한을 바꾸는 근거가 아니다. 연구 단독 결과·단순 합집합과 native 공통 관측 범위의 기여도 결과를 나누어 제시한다.

## 6. 후속 인계

[등록·상태 정합성 별도 구현계획](../proposals/main-pre-after-pattern-registration-and-status-consistency-remediation-plan-2026-10-08.md)에 PA0~PA14를 정리했다. 핵심 순서는 **PA0/PA13 실제 기동 cwd·동일 정책 코드 복구 → PA11 특징/coverage 연결 → 버전별 registry와 root parity → PA12 typed 보조 계약·정확 PRE NXT/AFTER SOR ADD → 공통 AI/영속 중복 방지 → 등록/비교/활성/PID/hold 표시 분리**다. 후속 계획 리뷰에서는 P0를 독립 복구 단위로 구분하고 실제 추천 13개에 필요한 다섯 root 계열, 보조 입력까지의 완결성, 상태 기준을 보완했다. 연구 결과 수치는 바꾸지 않았다.

사용자 후속 요청의 `active_machine_policy_invalid` 원인도 확인했다. PID 1304291 cwd가 release/src이며 frozen 원천 7개의 상대 `data/...` 경로는 그 cwd에서 존재하지 않았다. canonical workspace에서는 7개 모두 존재하고 해시도 일치한다. [경로 대조 증거](../../tmp/main-pre-after-pattern-research-20261008/relative-source-path-defect.json)를 추가하고 신규 등록보다 먼저 처리할 P0로 계획에 반영했다. 이번에는 계획·원인 재현까지 수행했으며 운영 validator를 수정하거나 봇을 재기동하지 않았다.

후속 구현은 새 후보를 명시적으로 등록하며 정규장 8개를 시간외로 자동 복제하지 않는다. NXT PRE는 `_NX` 계약 지원이 필요하고 통합 AFTER는 기존 SOR `_AL` 경로를 사용한다. 보조 AI 새 호출/새 배포/재기동/정책 발행은 이번에 실행하지 않았다. 기동 준비 문서의 과거 pending을 고치기 위해 현재 봉인·원천을 덮어쓰지도 않았다.

연구 중 다른 세션의 보조 registry/tuning/intraday 변경을 확인했다. 이를 덮어쓰지 않았고 후속 구현의 최신 소비자 재확인 항목으로 계획에 반영했다. 검증 범위는 이번 격리 연구 코드와 새 문서 3개이며 다른 세션 변경의 코드 종료·배포·PID 소비를 주장하지 않는다.
