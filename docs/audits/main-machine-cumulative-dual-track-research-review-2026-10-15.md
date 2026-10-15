# Main 누적 놓친 상승·ENTER_NOW 실패 감소 추가 연구 검토 — 2026-10-15

## 1. 결정과 범위

실행 계획은 [누적 두 축 추가 연구 계획](../proposals/main-machine-cumulative-dual-track-research-plan-2026-10-15.md)이다. 기존 결과 재순위에 한정하지 않고 신규 A 7개·F 6개를 수동 고정했다. 기존 비교군까지 A 16개·F 22개이며 current/A/F/J를 비교한다. 생산 코드·운영 등록·정책 pointer·보조판정·배포·재기동·provider·주문 권한을 변경하지 않는 오프라인 연구다.

이번 확인점은 실제 ask·비용률 0.0023·30분·비용 후 +0.4%/soft −3% 선도달 기준의 재생 CF다. W/STOP/TIMEOUT/U를 분리하고 누적 raw 승률을 우선한다. TIMEOUT은 실제 손실이 아니다. 성공 100%/80% 보존율, 최소 표본·일수·새 날짜 대기·추가 EV를 채택 제한으로 넣지 않는다. 연구 탐색 자료와 성능 계산 자료가 같다는 한계는 그대로 공개한다.

## 2. 기준 정책과 원천

[manifest](../../tmp/main-machine-cumulative-research-20261015/frozen-manifest.json)에 정책 bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`, release `policy-custody-incident-integrated-20261015-bb4808c77`/commit `bb4808c77087231b072efbd3ea12271fbb3889c6`를 고정했다. 이는 연구 baseline의 선택 snapshot이지 현재 PID 정상 소비를 새로 입증한 결과가 아니다.

이전 연구 parent 대비 주성 AFTER 고가의 `manual_joint_84fb6096d1459969`와 일반 PRE 저가의 `manual_joint_8008535bc6aa2678`가 제거된 실제 current를 전체 native State에 재생했다. 옛 후보에서 이미 줄어든 확인점을 새 정제 효과에 다시 더하지 않는다. PRE는 NXT `_NX`, 정규·AFTER는 SOR `_AL`만 사용한다.

### 2.1 10/14 자료가 성능 분모를 늘리지 못한 이유

검토 대상은 9개 날짜·27개 partition·5,587,427행이다. 그러나 10/14의 추가 325,775행은 모두 `valid=0`이므로 적격 날짜는 기존 8개다. 10/13도 기존 입증된 늦은 AFTER 구간만 포함한다. 날짜 이름이 추가됐다고 독립 새 검증일을 확보한 것은 아니다.

| 10/14 시장 | 원천 행 | 적격 | 일치하는 epoch 종료 증빙 없음 | 종료 증빙은 있으나 거부 |
|---|---:|---:|---:|---:|
| NXT PRE | 14,787 | 0 | 14,787 | 0 |
| SOR REGULAR | 251,823 | 0 | 251,823 | 0 |
| SOR AFTER | 59,165 | 0 | 42,649 | 16,516 |
| 합계 | 325,775 | 0 | 309,259 | 16,516 |

AFTER epoch `1791973328668305412`의 종료 receipt는 enqueue·persist 16,516건이 일치하고 raw 대사도 완료됐지만 `unaccounted_raw_row_exclusion`이다. timestamp 사전 거절 receipt는 기대 150건 중 tail 64건이며 `exact_rejected_row_exclusion_proven=false`다. 적격으로 기록된 두 다른 epoch에는 해당 장중 raw가 없다. `source_epoch_unverified`를 종목 상승 실패나 전체 가격 오염으로 해석하지 않는다.

10/15는 연구 봉인 시점 `main_raw_epoch_receipt_missing_or_invalid`여서 재수집·정규화하지 않았다. 원천 확대 없이 현재 적격 자료로 신규 가설 검증을 수행한다. [원천 제외 진단](../../tmp/main-machine-cumulative-research-20261015/source-exclusion-diagnosis.json)이 원 receipt hash와 시장/epoch별 행수를 소유한다.

원천 결손의 후속 owner는 기존 collector 종료 증빙 생산자와 `micro_reversion/observer_source_quality.py`·`continuous_reversal_source.py` 소비 연결이다. 후속 수리에서는 원 raw를 보존하고 epoch별 종료·enqueue/처리/persist 대사와 사전 거절의 정확한 제외 증빙을 검증해야 한다. 현재 값으로 과거 종료 receipt를 만들어 적격 처리하지 않는다. 이번 연구는 그 운영 경로를 수정하지 않았다.

## 3. 실제 발행 ENTER_NOW 별도 확인

[실제 캡처 결과](../../tmp/main-machine-cumulative-research-20261015/actual-enter-result.json)는 historical `main_live` 기계 판정 2,438건이다. 과거 파일의 plain→gzip 전환은 10/13 원문 SHA와 현재 gzip 해제 SHA를 대조해 동일 bytes임을 확인했다. 10/14에는 ENTER_NOW 513개 중 main_live 아닌 15개를 제외한 498개를 추가했다.

| 상태 | 건수 |
|---|---:|
| 원천 적격성 결손 | 2,198 |
| 목표 선도달 W | 74 |
| 손절 선도달 STOP | 0 |
| 30분 목표·손절 미도달 TIMEOUT | 97 |
| 검열·미확정 U | 69 |

정확한 가격 경로를 연결한 240건은 모두 10/12 자료다. 10/14의 498건은 모두 원천 적격성 결손이다. 연결 가능한 실제 판정 표본의 승률은 `74/171=43.27%`이며, 이를 현재 정책의 전체 누적 재생 성과와 섞지 않는다. TIMEOUT 97개 중 30분 말미 관측 체결가를 비용 차감한 대용치는 음수 83개·0 이상 14개다. ask 대비 −1.2317~+0.3710%이며 매도 체결·실현 PnL이 아니다.

주성 AFTER 고가의 실제 연결 표본은 W74/TIMEOUT81/U24다. 신규 F18(수익률≥0.05%·VWAP 이상·거래량 비율≥1)은 W26/TIMEOUT9/U14를 남겨 `47.74%→74.29%`다. 성공 48개·TIMEOUT72개·U10개를 제외한다. **이 실제 표본에서 F18은 기존 F16과 membership이 같아 새 추가 효과라고 부르지 않는다.** 조건부 신규 F20은 성공11개·TIMEOUT20개를 제외해 W63/TIMEOUT61의 50.81%다. F21은 TIMEOUT1개만 제외해 W74/TIMEOUT80의 48.05%다. 날짜가 하나이므로 여러 날짜에 일반화됐다고 표현하지 않는다.

알테오젠·HPSP AFTER의 실제 연결 표본은 확정 W가 없다. 실패를 전부 없애 분모도 0이 되는 F를 100% 성공으로 보고하지 않는다. 위 조건 검사는 과거 실제 기계 입력의 진단이며, 당시 정책별 branch replacement가 실제 적용된 결과는 아니다.

## 4. 누적 재생과 추가 포착 결과

전체 27개 partition을 완료했다. 원천 5,587,427행 중 유효 3,831,217행·제외 1,756,210행, 확인점 236,597개를 처리했다. 낮은 우선순위 단일 worker의 partition 합산 wall은 909초, pending overload는 0이다. 22개 scope에서 current/A/F/J **19,892개 대안**을 비교했다. 서로 같은 membership의 별칭도 있어 이 수를 독립 통계 검정 횟수로 해석하지 않는다.

최종 소비 대상은 [result-reviewed.json](../../tmp/main-machine-cumulative-research-20261015/result-reviewed.json)이다. `winner`는 분수·W 수·고정 ID 순위의 최고 대안이고, **`recommendation`은 current보다 높은 비율 또는 같은 비율에서 더 많은 W가 확인됐을 때만 변경 제안**이다. 추가 실패/U만 생기는 동률을 개선으로 제안하지 않는다. `recommendation`도 연구상 등록 검토 대상이며 실제 운영 정책 선택 receipt가 아니다.

### 4.1 새 가설이 기존 연구의 최고 대안보다 나아진 4개 scope

아래 `W/확정`의 확정 분모는 W+STOP+TIMEOUT이다. 새 F는 해당 scope/branch를 교체하는 정제이고, J는 `F(current) OR A`다.

| scope | 새 대안 | 현재 정책 | 기존 가설 최고 | 새 결과 | 해석 |
|---|---|---:|---:|---:|---|
| 두산 PRE 중가 | 조건부 F21 | 51/72 (70.83%) | 51/72 | **48/48 (100%)** | 종목 중립 구간에서 거래량·매수세·spread 확인. W3·TIMEOUT21·U8 제외. U3,943개 유지 |
| 일반 비고정 AFTER 저가 | F18 / `legacy_drop_0_4_rebound_le_0_3_v1` | 36/111 (32.43%) | F16: 17/44 (38.64%) | **16/37 (43.24%)** | 기존 F16에 VWAP 확인을 더해 W1·STOP1·TIMEOUT5·U1 추가 제외. 현재 대비는 W20·STOP5·TIMEOUT49·U63 제외 |
| 일반 비고정 PRE 고가 | A10 추가 | 10/10 (100%) | 10/10 | **11/11 (100%)** | 작은 낙폭·느린 첫 반전에 거래량 증가 확인. 새 W1·U1 추가 |
| 일반 비고정 PRE 저가 | A14 + scope F10 | 157/204 (76.96%) | F10: 1/1 | **2/2 (100%)** | 고점·저점 상승 전환 후 3초 유지 1승 추가. 현재 대비 W156·STOP45·TIMEOUT2·U26 제외 |

두산 PRE의 48승은 10/7 하루·distinct target clock 4개다. 일반 PRE 고가의 11승과 저가의 2승도 확정 표본은 9/29 하루에 있다. AFTER 저가의 새 F18 확정 결과는 6개 날짜에 걸쳐 있고, 10/12가 W10/18로 가장 크다. **48/48·2/2를 48회·2회의 독립적인 실제 수익 거래로 부르지 않는다.** 성공 감소는 탈락 조건이 아니지만 수치에서 숨기지 않는다.

### 4.2 현재 정책 기준 나머지 변경 제안

| scope | 대안 | 현재 W/확정 → 제안 W/확정 |
|---|---|---:|
| 두산 AFTER 중가 | F02 / extended 원 branch | 40/54 → 40/48 |
| 주성 AFTER 고가 | scope F11 | 250/589 → 54/89 |
| 주성 REGULAR 고가 | A07 + scope F09 | 914/1292 → 24/24 |
| 알테오젠 PRE 고가 | A03 + scope F03 | 404/483 → 78/78 |
| 알테오젠 REGULAR 고가 | A07 + scope F04 | 20/81 → 22/22 |
| HPSP AFTER 중가 | F09 / legacy 원 branch | 10/20 → 10/10 |
| HPSP REGULAR 중가 | F05 / type 원 branch | 438/453 → 392/392 |
| 일반 비고정 AFTER 중가 | scope F09 | 21/30 → 3/3 |
| 일반 비고정 AFTER 고가 | A05 추가 | 2/2 → 3/3 |
| 일반 비고정 PRE 중가 | A09 + scope F06 | 29/30 → 28/28 |
| 일반 비고정 REGULAR 중가 | F16 / path 원 branch | 30/35 → 7/7 |

이 11개는 기존 가설의 현재 baseline 재비교 결과다. 새로운 패턴 발견으로 다시 세지 않는다. 최고 비율·W 수가 같은 대안의 고정 ID 동률 처리 때문에 10/14 대표 표와 F 번호가 다를 수 있다. exact branch·조건·membership·날짜별/U 비교는 reviewed JSON을 소비한다.

총 22개 중 15개 scope에 변경 검토 대안이 있다(A-only 2·F-only 8·J 5). 7개는 개선 미확인 current 유지다. 삼성 3시장, 두산 REGULAR, 알테오젠 AFTER, 일반 REGULAR 저가·고가가 해당한다. 삼성 AFTER·알테오젠 AFTER에서 0% 동률에 실패만 추가한 raw 순위 대안은 변경 제안에서 제외했다. 삼성 PRE의 U만 추가된 동률도 current 유지다.

범위별 승률 우선 제안을 합한 CF 진단은 **2,579/3,804=67.80% → 905/1,140=79.39%**다. 기존 W1,712·STOP162·TIMEOUT828을 제외하고 새 W38을 추가했다. U는 11,187→8,362, distinct target clock은 288→117이다. 승률은 높아졌지만 포착 성공·관측 기회는 크게 감소한다. 실현 순이익이나 제출 횟수가 늘었다는 증거로 전용하지 않는다.

별도의 기회 확대 대안 합집합은 W2,965/4,378=67.72%로 current 67.80%보다 낮다. scope별 비율을 유지해도 서로 다른 scope의 비중이 변하면 전체 비율은 낮아질 수 있다. 이를 전체 운영 winner로 제안하지 않는다.

### 4.3 놓친 상승 연구의 새 발견과 실패

[신규 가설별 중복 분석](../../tmp/main-machine-cumulative-research-20261015/novelty.json)과 [신규 합집합](../../tmp/main-machine-cumulative-research-20261015/novel-union.json)을 별도로 작성했다. 아래는 현재 정책뿐 아니라 **기존 A01~A09와 current의 전체 합집합에 없던 확인점**이다.

| 새 가설 | 새 W | 새 STOP+TIMEOUT | U | 기존 연구 전체에도 없던 목표 clock |
|---|---:|---:|---:|---:|
| A10 작은 낙폭·느린 첫 반전 | 77 | 1,752 | 923 | 2 |
| A11 느린 상승률 전환+3초 유지 | 657 | 5,010 | 4,232 | 4 |
| A12 고점 돌파+1초 유지 | 16 | 25 | 18 | 1 |
| A13 VWAP 회복+1초 유지 | 322 | 1,706 | 1,552 | 44 |
| A14 고점·저점 상승 전환+3초 유지 | 69 | 171 | 169 | 7 |
| A15 약세 종목 저점 재확인 | 2,031 | 12,106 | 13,165 | 23 |
| A16 느린 상승률 전환+5초 유지 | 144 | 905 | 798 | 4 |

7개 신규 가설을 중복 제거하면 **기존 연구에 없던 W3,276·STOP28·TIMEOUT21,484·U20,677**, 기존 연구 전체에도 없던 목표 clock 79개다. 서로 다른 가설의 W·clock을 단순 합산하지 않는다. 상승 지점은 추가로 찾았으나 실패까지 포함한 확정 승률은 13.22%여서 전부 OR로 켜는 방법은 부적절하다. §4.1처럼 유형·시장별 검증이 된 좁은 대안을 골라야 한다.

삼성 REGULAR에서도 신규 A15가 current 밖의 W902개를 포착했지만 TIMEOUT5,969·U3,860개가 함께 발생했다. A11은 W108/TIMEOUT689/U342, A13은 W64/TIMEOUT432/U276, A14는 W5/TIMEOUT10/U3이다. **놓친 상승이 없어서 삼성 정책을 유지하는 것이 아니다.** 이번 조건 그대로 추가하면 current의 88/88보다 비율이 낮아진다. 삼성 PRE·AFTER는 이번 신규 A에서 확정 W가 없었다. 이 결론은 적격 원천/고정 가설 범위에 한정하며 결손 10/14·10/15 전체 시장을 대표하지 않는다.

## 5. 검토·수정·검증

- 오프라인 Python 소유 위치는 `tmp/main-machine-cumulative-research-20261015/`다. 엔진 루트나 production 코드를 새로 만들지 않았다.
- 신규 root의 UNKNOWN→TRUE 오승격, source break를 넘는 hold, 미래 suffix가 prefix 신호를 바꾸는 문제를 반례로 검사했다. 조건부 regime UNKNOWN·알려진 FALSE AND UNKNOWN·다른 OR branch 허용·성공 제거 후 비율 개선·미확정 분모도 검사했다.
- 초기 비교기의 '성과가 같으면 무조건 current 우대'를 별도 reviewed selector에서 수정했다. 동일 membership alias만 current canonical ID로 묶고 다른 membership은 고정 ID로 동률을 해소한다. 분모가 모두 없는 경우 current를 유지한다. 초기 결과는 보존하고 reviewed 결과를 최종 소비한다.
- 연구 및 기존 계약 시험은 최종 38개가 통과했다. 실제 연결 ENTER_NOW 240건은 독립 선형 tick oracle과 exact native epoch/sequence/item/ask 대조에서 불일치 0건이다.
- 검증기의 최초 실행은 legacy 정규화 행에도 확장 native 열이 있다고 가정하여 중단됐다. 원 행을 바꾸지 않고 기존 collector key 검사와 확장 native key 검사를 분리해 수정했다. 실패 log와 재실행 log를 모두 보존했다. legacy CF를 실제 native 판정 연결 증거로 승격하지 않는다.
- [최종 검증 receipt](../../tmp/main-machine-cumulative-research-20261015/validation.json): 시계열 단조 9,053개, exact 정규화 신원+선형 tick oracle 214개(legacy key 195·native namespace 19), 동일 item 완료 분봉 재검사 48개, 신규 가설 필터 134개, 대안 분수 순위 19,892개·scope22개·봉인 hash224개를 확인했다. 오류0이다. 실제 ENTER_NOW의 별도 native key+선형 oracle 240개와 구분한다.
- 신규 수동 root의 운영 native 구현 동등성과 자연 판정은 후속 등록 구현의 검증이며 이번 완료를 의미하지 않는다. production trading suite·canonical 장후 재생성·provider·정책 등록/적용·배포/재기동은 실행하지 않았다.
- 문서 3개의 로컬 링크33개·표11개와 공백 검사를 통과했고 print-only parser는 기존 작업25개를 출력했다. `git diff --check`·관련 Python compile도 통과했다. current checklist와 baseline 지침은 수정하지 않았으며 외부 Project/Calendar 동기화는 실행하지 않았다.

## 6. 다음 소비와 결론

기존 [정책 반영 계획](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md)에 현재 parent·새 가설·15개 등록 검토 범위를 인계한다. local A/F 번호를 운영 definition ID로 재사용하지 않고 canonical 조건·root·scope·UNKNOWN·parent hash로 versioned 등록한다. F는 원 branch replacement/내부 dependency로 처리하여 기존 OR 원형이 정제를 우회하지 않게 한다. A는 독립 root이며 같은 확인점에서만 AI/intent를 dedup한다. 기존 보조판정 입력·응답·정책과 hard safety·Main/manual custody·퇴역 경계는 보존한다.

이번 작업은 **새로운 상승 포착 연구와 기존 ENTER_NOW 실패 감소 연구를 모두 실행·검증한 완료**다. 성과를 입증한 후보만으로 운영 적용됐다는 뜻은 아니다. 원천 결손은 원천 계약으로 남고, 신규 root/조건부 F의 runtime parity 및 적용은 후속 구현에서 확인한다.
