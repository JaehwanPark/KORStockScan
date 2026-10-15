# Main 가격 전진·회복 유형 누적 연구 결과 — 2026-10-15

## 1. 결정

보유·장후 재생 수리와 독립적으로 **새 가설 12개를 실제 계산하고 기존 후보까지 재비교했다.** 이전 연구 최선안보다 나아진 범위는 두산 AFTER 중가, HPSP REGULAR 중가, 일반 비고정 PRE 중가의 3곳이다. 주성 REGULAR의 기존 연구 제안 `J:A07+F09`는 유지된다. 주성 사례의 매수 압력 대비 가격 무진전·한 호가 왕복·약세 문맥을 모든 종목에 일괄 veto하는 안은 이번 누적 결과로 지지되지 않는다.

원천에 있는 모든 종목과 48개 정책 scope를 검사했다. 실제 유효 원천은 8개 날짜·1,809종목·3,831,217행이다. 전 상장종목·모든 거래소 route·모든 날짜의 완전한 관측을 확보했다는 뜻은 아니다. 이번 연구는 기존 ask/30분/+0.4%/-3% 진입 label의 비교이며, 보유 수리 이후 실제 preset·trailing·수동 이관·실현 비용 결과를 검증한 작업이 아니다. 따라서 이 연구 실행에는 수리 완료 확인이 필요하지 않았다.

[사전 고정 계획](../proposals/main-entry-price-progress-and-situation-research-plan-2026-10-15.md)에 따라 임시 오프라인 연구 디렉터리에서 실행했다. 운영 코드·정책·보조 입력/응답·provider·주문·수동관리·선택 릴리스·PID를 변경하지 않았다. 연구 완료는 후보 등록·발행·자연 소비 완료와 별개다.

## 2. 신원과 재현 근거

동결 시각은 **2026-10-15 15:22:36 KST**다. 당시 선택본은 `hpsp-peak-outbox-source-recovery-20261015-v1`, commit `451b6c1ec84fafa563d95381e95c814ac2b2b18b`이고 parent bundle은 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`이다. 기존 재생 실행본 `bb4808c77087231b072efbd3ea12271fbb3889c6`와 관련 기계 의존 파일 28개가 byte 동일함을 확인했다.

그에 따라 기존 current 신호·A01~A16 membership·라벨 236,597개를 재사용하고 기존 feature를 재계산해 비교했다. 새 feature/root가 만든 **10,687개 확인점만 추가 label 계산**했다. 현재 native State 전수를 다시 실행했거나 현재 PID를 확인한 것으로 표현하지 않는다. parent·의존 코드·원천·라벨 계약이 달라지는 후속 연구는 이 캐시의 유효성을 다시 검증해야 한다.

| 근거 | 내용 |
|---|---|
| [manifest](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/manifest.json) | 원천·코드·과거 결과 봉인 283개, SHA256 `8f60c9f3f894650cf0841a49f971a047386553849adfd73bf68ed98bfd6b09a7` |
| [결과](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/result.json) | 48 scope, 50가설·35,558대안, SHA256 `5210ddad3d5ec1c74b942cbf6b49b65d2ecd9c44d8d963644487e4f4654b8363` |
| [전체 대안 ledger](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/variants.jsonl.gz) | current/A/F/J, scope 및 branch F, membership hash와 추가·제거 수 |
| [유형 진단](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/diagnostics.json) | 종목군·시장·가격대별 상황/매수 압력/한 spread 범위 분할 |
| [이전 제안 대비 차이](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/supplement.json) | 같은 key 기준 이전 제안→새 제안, 신규 A 순수 추가분, 날짜·종목·자원 |
| [실제 ENTER_NOW 대조](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/actual-enter-check.json) | 원천으로 연결되는 과거 실제 기계 캡처 240개; 보조 PASS·체결과 구분 |
| [독립 검증](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/validation.json) | 원천/feature/root/label/기존 대안/선택/범위 검증, errors 0 |

비교 기준은 기존 누적 `W/(W+STOP+TIMEOUT)` → W 수 → 동일 membership current canonical → 고정 ID다. 비용률 0.0023, 실제 entry ask, 비용 후 +0.4% 목표/-3% 손절의 1,800초 선도달 label을 유지했다. TIMEOUT은 실제 손실이 아니며 U는 실패·0원으로 채우지 않았다. 성공 보존율·최소 표본/일수·새 holdout·추가 EV를 선정 조건에 넣지 않았다. 같은 자료에서 탐색·선택했으므로 독립 미래 성능 검증은 아니다.

## 3. 이전 연구 최선안보다 개선된 세 범위

표의 수치는 실제 거래가 아닌 과거 확인점 CF이며, 비교 대상은 current가 아니라 **직전 38가설 연구의 recommendation**이다. 중가는 기존 코드의 `20000_TO_100000`이다.

| scope | 이전 최선 → 새 제안 | W/확정 변화 | U 변화 | 실제 membership 차이 |
|---|---|---|---|---|
| 두산 `034020`, SOR AFTER 중가 | `F:F02@manual_extended_b3f20a28786bbd4e` → scope `F:F23` | 40/48 (83.33%) → **24/28 (85.71%)** | 91→48 | W16·TIMEOUT5·U44 제거, TIMEOUT1·U1 추가 |
| HPSP `403870`, SOR REGULAR 중가 | `F:F05@manual_type_ae4445459dc942c8` → `J:A19+F05@manual_type_ae4445459dc942c8` | 392/392 → **394/394 (100%)** | 656→664 | 기존 확인점 전부 보존, W2·U8 추가 |
| 일반 비고정, NXT PRE 중가 | scope `J:A09+F06` → `J:A09+F25@legacy_dd5_0_8_vol_up_v1` | 28/28 → **30/30 (100%)** | 2→2 | 기존 제안 확인점 전부 보존, W2 추가 |

F23은 연속 유효 10체결의 가격 전진 >0이다. 두산의 원 extended branch만 정제하던 제안에서 scope 전체 정제로 바뀌므로 단순히 기존 제안에 조건 하나를 덧붙인 결과가 아니다. 확정 결과는 전부 10/8이며 서로 다른 목표 도달 clock은 전후 3개다. 승률 우선에서는 개선이지만 성공 16개를 포기했다.

A19는 고점·저점 동반 상승으로 전환한 뒤 3초 체결가 유지 root에, 확인 시점 bid 10행 상승·매수 비중 ≥60%·60초 수익률 ≥0을 요구한다. HPSP의 기존 F05는 원 type branch에만 남기고 A19는 독립 OR로 추가한다. 새 W는 10/7·10/8 각 1개이며 서로 다른 목표 clock은 34→36이다. 두 W는 기존 모든 A/current에도 없던 신규 확인점이다. U8 증가도 함께 공개한다.

F25는 최근 10체결 가격 범위가 현재 spread보다 큰 조건이다. 일반 PRE 중가에서는 원 legacy branch만 정제하고 다른 OR branch와 기존 A09를 보존한다. 이전 제안보다 복구한 W2는 **9/29의 `455900` 두 확인점·동일 목표 clock 하나**다. 새 독립 거래 두 건이나 새 A root 두 건이 아니다. 전체 제안의 목표 clock은 8→9다.

48개 중 22개 scope에 적격 확인점이 있고, 나머지 26개는 `no_eligible_confirmation`이다. current 대비 변경 검토는 15개(A2/F7/J6), 관측됐으나 개선 미확인인 7개와 무확인 26개는 current를 유지하는 제안이다. 이전 제안과 비교하면 위 세 곳 외의 membership은 그대로다.

| 확인점 집계 | W | STOP | TIMEOUT | 확정 승률 | U | 목표 clock |
|---|---:|---:|---:|---:|---:|---:|
| 동결 current | 2,579 | 165 | 1,060 | 67.80% | 11,187 | 288 |
| 직전 연구 제안 합계 | 905 | 3 | 232 | 79.39% | 8,362 | 117 |
| 이번 연구 제안 합계 | 893 | 3 | 228 | 79.45% | 8,327 | 120 |

scope별 승률 우선 선택의 집계다. 직전 대비 승률은 약 0.062%p 높지만 W12개가 줄었다. 이를 제출 증가·총이익 증가로 부르지 않는다. 목표 clock 역시 독립 체결 수가 아니다.

새 A17~A20을 모두 합치면 기존 모든 A/current에 없던 확인점은 W2,381·STOP150·TIMEOUT4,108·U4,048이다. 확정 승률 **35.86% (2,381/6,639)**이므로 모든 scope에 무차별 OR하는 근거가 없다. 넓은 신규 탐지와 특정 scope에서 검증한 선택 대안은 구분한다.

## 4. 주성 사례가 지지하지 않은 일반화

주성 REGULAR 고가의 전체 current는 914/1,292 (70.74%), U2,033이다. 이번 추가 가설로도 이전 최고 `J:A07+F09`의 24/24·U7을 넘지 못했다. 신규 가설을 포함한 대안 중 최고 `J:A03+F26`은 299/344 (86.92%)·U214로 current보다 높지만, 기존 선정 기준에서는 24/24를 대체하지 않는다. 기존 24 W가 10/8의 목표 clock 두 개에 집중하고 기존 W914개를 모두 제거한다는 한계도 유지한다.

| 주성 REGULAR current의 관측 태그 | W/확정 | 승률 | U |
|---|---:|---:|---:|
| 매수 비중 ≥60% AND 10체결 가격 전진 ≤0 | 230/306 | **75.16%** | 279 |
| 위 조건이 아닌 확인점 | 684/986 | 69.37% | 1,754 |
| 최근 10체결 가격 범위 ≤현재 spread | 801/1,138 | 70.39% | 1,829 |
| 최근 10체결 가격 범위 >현재 spread | 113/154 | 73.38% | 204 |
| 세션 하락·회복 미확인 | 63/83 | 75.90% | 906 |
| 세션 하락·회복 확인 | 0/0 | null | 1 |
| 세션 상승·지속 확인 | 37/43 | 86.05% | 17 |
| 세션 상승·지속 미확인 | 814/1,166 | 69.81% | 909 |

매수 압력 대비 가격 무진전군의 승률이 오히려 높다. 이 관측이 무진전의 인과적 우월성을 뜻하지도 않는다. 한 spread 범위군은 소폭 낮지만 표본·날짜·U가 다르며, 한 사건만으로 범용 차단을 정당화할 수 없다. 세션 하락·회복 확인군에는 확정 결과가 없어 회복 확인의 우월성을 비교할 수 없다. HPSP REGULAR도 무진전군 71/72 (98.61%) 대 나머지 366/380 (96.32%)여서 동일한 일괄 차단 논리를 지지하지 않는다.

상황 유형은 `DOWN_UNCONFIRMED`, `DOWN_RECOVERED`, `NEUTRAL`, `UP_CONTINUATION`, `UP_UNCONFIRMED`, `UNKNOWN`으로 산출했다. 세션 ±0.4%와 당시 고점/저점·60초 수익률·bid 전진을 사용한다. 개별 종목의 세션 상태이지 KOSPI/KOSDAQ 시장유형이 아니며, 진입 시점 유형과 보유 중 동적 weak/strong은 다르다. 유형별 설명·고정 조건 비교는 가능하지만 이번 결과가 새 일괄 veto나 트레일링 수치를 결정하지는 않는다.

## 5. 실제 ENTER_NOW·보조판정과의 경계

기존 수집된 실제 기계 ENTER_NOW 2,438개 중 exact source row가 적격인 것은 240개다. 나머지 2,198개는 `exact_source_row_ineligible`로 유지했다. 240개는 모두 **10/12 AFTER**, 주성·알테오젠·HPSP·삼성의 4 scope이며 W74·TIMEOUT97·U69다. 원 source item/native epoch/sequence/ask/시각을 다시 대조하고 새 특징을 독립 선형 계산으로 추가했다.

실제 캡처에 scope 전체 정제 조건을 가상 적용한 진단은 다음과 같다. 과거의 다른 branch 정책에 현재 branch replacement를 적용했다고 주장하지 않는다.

| 가상 scope 정제 | 남은 W/확정 | 남은 U | 제거 W/TIMEOUT/U |
|---|---:|---:|---|
| 없음 | 74/171 (43.27%) | 69 | 0/0/0 |
| F23 가격 전진 | 25/52 (48.08%) | 24 | 49/70/45 |
| F25 한 spread 초과 범위 | 5/12 (41.67%) | 0 | 69/90/69 |
| F26 한 spread 이상 전진 AND bid 상승 | 6/11 (54.55%) | 2 | 68/92/67 |
| F27 세션 하락 시 회복 구조·bid 확인 | 4/23 (17.39%) | 2 | 70/78/67 |

실제 기계 캡처라고 해도 후행 결과는 **가정한 ask 진입의 CF label**이다. 보조 PASS, 제출·체결, 실제 preset 종료·실현 순손익은 아니다. 좁은 날짜·세션과 많은 원천 제외 때문에 위 표를 전 시장 실거래 성능으로 확대할 수 없다. ENTER_NOW뿐 아니라 추가 탐지·미체결 경로도 연구할 수 있음을 확인했으나, 보조 PASS 모집단 전체의 경제성은 이번에 새로 입증하지 않았다.

[주성 전체 흐름 조사](/home/ubuntu/KORStockScan/docs/audits/main-jusung-hard-stop-pattern-and-full-flow-research-2026-10-15.md)에서 확인한 compact 보조 입력의 정보 차이는 유지된다. 당시 보조는 매수 비중·10체결 수익률·spread를 받았지만 세션 하락·고점/저점 구조·완료봉 문맥은 받지 않았다. 이번 연구는 원 보조 prompt/input/response·membership·지표를 보존한 별도 비교다. 기존 PASS를 새 문맥을 본 PASS로 재해석하지 않고, 입력 확장이 필요하다면 별도 version과 같은 입력 원천의 paired 비교로 다룬다. provider 호출은 0이다.

## 6. 전 범위 실행·성능·원천 한계

9/29·9/30·10/2·10/6·10/7·10/8·10/12·10/13·10/14의 27개 partition, 5,587,427행을 모두 검사했다. 원천 등장 종목은 1,876개, 유효 행이 한 개 이상인 종목은 1,809개다. 종목×날짜×시장 series 9,053개 중 1,419개는 전체 행이 부적격이었다. 유효 3,831,217행과 제외 1,756,210행을 분리했다. 동결 10/14 입력 전체와 10/15 튜닝 제외를 유지했으며, 이후 다른 세션의 수리가 과거 동결 원천까지 적격으로 바꿨다고 가정하지 않는다.

| 운용 route/세션 | 원천 행 | 유효 행 |
|---|---:|---:|
| NXT PRE `_NX` | 307,277 | 196,693 |
| SOR REGULAR `_AL` | 4,544,963 | 3,100,479 |
| SOR AFTER `_AL` | 735,187 | 534,045 |

SOR를 별도 KRX·NXT 관측으로 복제하지 않았다. 26개 무확인 scope를 정상 성공·기회 없음으로 합치지 않는다. 원천에 없는 symbol/route/기간의 효과는 미확정이다. 별도의 시장/종목 allowlist로 연구 입력을 줄이지 않았으며 고정/비고정 모두 같은 계산을 적용했다.

단일 낮은 우선순위 worker, partition당 address space 2GiB·CPU480초·wall600초로 실행했다. 계산 단계의 raw 압축 읽기 70,652,589 bytes, 기존 point cache 압축 읽기 11,541,399 bytes다. 동결 해시 검사·독립 검증·실제 캡처 재대조 읽기는 이 숫자와 별도다. 가설 조합마다 raw를 재독해하지 않고 동일 feature/label을 재사용했다.

partition 계산 합계 96.87초, 최장 partition 11.86초, 집계 16.04초다. 최대 RSS는 partition 817,776 KiB, 집계 1,238,572 KiB (약 1.18GiB)였다. 기존 236,597 label 및 검증된 native 결과를 재사용해 추가 label 계산을 10,687개로 제한했다. 동일 자료의 전후 paired 속도 benchmark는 없으므로 배수 단위 가속이나 live p99 개선을 주장하지 않는다. 장중 추가 API·디스크 계산을 넣지 않은 오프라인 실행이다.

## 7. 리뷰·검증 및 수리 세션과의 인계

13개 표적 시험이 통과했다. quote/native 단절, bid 상승 없는 왕복, 유지 중 bid 후퇴, 저점 이탈 후 재사용 금지, 미래 suffix 불변, 조건부 UNKNOWN·AND·OR 보존, 승률 선택을 검사했다. 독립 검증은 feature 값 1,236,420개, point identity 247,284개, bid root series 203개, 선형 label 430개, 동일 item 완료봉 보조 93개를 대조했다. 모든 미래 경로를 독립 label oracle로 다시 계산한 것은 아니다.

기존 19,892개 대안의 counts·추가/제거·동일 membership이 전부 보존됐고, 전체 35,558개 대안의 분수 순위, scope48·partition27·봉인283 검증에서 errors 0이다. 계산 정확성·계약 검증과 runtime 탐지 구현의 parity는 구분한다. 운영 typed definition/등록 archive/selector/CAS/PID 소비는 아직 수행하지 않았다.

[최종 리뷰 receipt](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/final-review.json)는 세 문서의 링크43개·표13개, 현재 보유 수리/장전 handoff owner 각각1개, 결과 해시·추가/제거 산술·실제 캡처 census를 확인했다. Python compile·`git diff --check`·print-only parser가 통과했고 parser 출력은25개 작업이다. 생산 코드 변경이 없어 거래 suite·장후 전체 재생성·provider·외부 동기화·재기동은 실행하지 않았다. runtime 신규 탐지와 실제 보유·청산 결과는 별도 미검증이다.

리뷰에서 두산의 순 TIMEOUT4 감소를 “TIMEOUT4만 제거”로 단순화하지 않고 제거5·추가1로 분리했다. 일반 PRE 중가의 이전 제안은 scope F06이고 새 F25는 branch 정제임을 명시했다. 실제 캡처 240개의 범위를 10/12 AFTER로 한정하고, 신규 A 전체 합집합과 기존 모든 후보에도 없던 순수 추가분을 구분했다. 전체 승률과 W 수 감소를 함께 공개했다.

후속 정책 반영은 [기존 소유 계획 §10](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md#10-1015-가격-전진회복-유형-연구-반영)을 따른다. 기존 F23/F25 feature 및 A19 root의 runtime 동등성·원 branch 교체·OR·UNKNOWN·중복 방지 검증은 보유 수리와 독립적으로 진행 가능하다. 운영 등록/정책 적용은 별도 작업이며 이 연구로 승인 영수증을 만들지 않는다.

보유 수리 완료 확인은 **진입 label과 실제 운영 종료를 같은 position에 결합하는 단계**에서 필요하다. 기존 `HoldingProfitExitSourceContractRepair` owner가 제공할 증거는 (1) context→path input의 신원·결손 구분, (2) cost known_at/preset/common/emergency 실효값과 first crossing, (3) trailing 전이·peak·entry situation pin의 완전성, (4) manual handoff 전후 custody·실제 fill/terminal이다. 수정 commit·선택/PID·원본 재생·자연 receipt를 구분해 받으며 원천이 사라진 과거 구간은 source gap으로 남긴다. 이 인계가 필요해질 때 사용자에게 완료 증거를 문의한다. 현재 연구 때문에 다른 세션의 수리 완료를 요구하거나 중복 수리를 시작하지 않는다.
