# Main 누적 상승 추가 포착·ENTER_NOW 실패 감소·비상시감시 호가 정합성 연구 계획 — 2026-10-17

## 1. 목적과 범위

사용자 지시에 따라 누적 원천에서 놓친 상승 추가 포착(A)과 기존 ENTER_NOW 실패 감소(F)를 함께 연구한다. 후속 지시의 비상시감시 종목도 별도 분모로 분석한다. 가격 패턴의 사후 성공, 판정 당시 실행 가능한 호가, AI 이후 실제 제출 가능 여부를 구분한다.

오프라인 수동 연구다. 새 가설은 여기에서 고정하며 장후 자동 생성기의 탐색 범위를 늘리지 않는다. 원천 수집 확대, canonical 장후 재생성, 운영 후보 등록·정책 선택·배포·재기동·provider·주문·호가 안전기준 변경은 실행하지 않는다. 보조판정의 기존 입력·응답·membership·성과를 변형하지 않는다. 생산 코드와 다른 세션 작업본은 보존한다.

오늘 10/17 일일 체크리스트가 존재하지 않는다. 10/19 문서는 미래 일정이며 오늘의 실행 권한으로 대체하지 않는다. 이번 명시적 연구 지시로 오프라인 계산과 연구 문서 검증을 수행하고, 운영 후속 작업은 현재 날짜의 owner와 별도 연결해야 한다.

## 2. 비교 기준과 원천 봉인

- 현재 선택 release snapshot은 `postclose-complete-20261017-7f2552aed`, 기계 bundle은 `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`다. selector의 `actual_pid_consumed=false`를 정책 미적용이나 실제 판정 성과로 전용하지 않는다.
- 이 bundle의 누적 후보 대상 22개 scope membership은 [10/15 정정 연구](../audits/main-machine-cumulative-dual-track-research-review-2026-10-15.md)의 최종 recommendation과 일치한다. 과거 parent `1f069…` 기준의 개선을 현재 개선에 다시 더하지 않는다. 이전 봉인 sparse 확인점과 정의로 현재 membership을 정확 복구하고, 신규 날짜는 현재 native State로 재생한다.
- 기존 27개 partition에 10/15·16의 운용 route 6개를 추가한다. PRE는 NXT `_NX`, REGULAR·AFTER는 SOR `_AL`이다. 해당 원천의 row별 적격 여부와 exact item을 유지하며 invalid epoch를 가격 실패로 바꾸지 않는다.
- 새 원천은 1,269,187행이지만 적격 행은 10/15 SOR AFTER의 39,220행이다. 10/16 운용 세 route는 전부 적격 epoch 증빙이 없다. 현재 값으로 과거 종료 증빙을 생성하지 않는다. 10/15 AFTER의 epoch 검증 제외 후 39,255행에서 체결 수신 지연이 5초를 넘은 35개를 추가 제외해 39,220행이 된다. 확인점 호가 적격 검사는 별도다.
- normalized·sparse·현재 정책·완료 분봉·선택 코드와 후보를 [연구 manifest](../../tmp/main-machine-cumulative-dual-track-research-20261017/missed-rise-manifest.json)에 봉인한다. 지연 import 모듈도 [전체 scalping 코드 봉인](../../tmp/main-machine-cumulative-dual-track-research-20261017/reference-code-seal.json)으로 포함한다. 봉인 불일치·미완료 partition은 완료로 표시하지 않는다.

## 3. 추가 포착 가설

아래 8개를 결과 계산 전에 고정한다. 기존 A01~16을 다시 새 가설로 세지 않는다. 모든 특징은 확인점까지의 수신 prefix로 계산한다. `UNKNOWN→TRUE`는 새 전환으로 인정하지 않는다. hold 중 가격이 root 가격 미만이면 취소하고 확인점에서 필터를 다시 검사한다.

| ID | root와 확인 | 추가 조건 요약 |
|---|---|---|
| A17 | 완만한 상승 조건 전환 후 3초 유지 | 180초 +0.08% 이상, 60초 0~0.15%, 5분 낙폭 ≤0.15%, VWAP 이상, spread ≤0.1% |
| A18 | 얕은 눌림 회복 조건 전환 후 3초 | 180초 고점 대비 낙폭 0.1~0.4%, 60초 저점 대비 +0.05% 이상, 60초 수익률·VWAP ≥0, 매수 비중 ≥50%, spread ≤0.1% |
| A19 | 직전 120초 고점 돌파 후 3초 | 60초 0~0.2% 미만, 거래량 비율 ≥1, 매수 ≥50%, spread ≤0.1% |
| A20 | 거래량 비율 1.5 상향 전환 후 1초 | 60초 +0.03~0.3%, VWAP 이상, 매수 ≥60%, 동반 하락 구조 아님, spread ≤0.1% |
| A21 | VWAP 회복 후 5초 | 180초·60초 수익률 ≥0, 60초 <0.2%, 낙폭 ≤0.4%, 거래량 ≥1, spread ≤0.1% |
| A22 | 고점·저점 동반 상승 전환 후 3초 | 180초 +0.05% 이상, 60초 0~0.15% 미만, VWAP 이상, 매수 ≥50%, spread ≤0.1% |
| A23 | 첫 반전 후 1초 | 180초 +0.1% 이상, 5분 낙폭 0.1~0.6%, 60초 −0.1~+0.1%, VWAP 이상, 매수 ≥50%, 거래량 ≥1 |
| A24 | 60초 +0.02% 상향 전환 후 3초 | 180초 ≥0, 60초 <0.15%, VWAP 이상, 낙폭 <0.2%, 거래량 ≥1, spread ≤0.1% |

8개 각각과 256개 OR 조합을 scope별로 실제 합집합 계산한다. 각 고정 F(current)에 이 OR 조합을 붙이는 결합 비교도 수행한다. 같은 확인점만 dedup하고, 다른 시각의 신호는 독립 거래 횟수로 부르지 않는다. 추가 W/STOP/TIMEOUT/U, distinct target clock, 날짜 편중을 함께 보고한다.

## 4. 기존 ENTER_NOW 실패 감소

실제 `main_live` 캡처와 현재 정책의 native 재생 CF를 분리한다. 실제로 관측된 기계판정의 exact native epoch/sequence/item/관측 ask와 미래 가격을 연결한 사후 CF 라벨이며 실제 체결가·손익이 아니다. 결손은 SOURCE_GAP으로 남긴다. 주문 거절·수량 0·submit false를 가격 패턴 실패로 세지 않는다.

F23~28은 [별도 봉인 정의](../../tmp/main-machine-cumulative-dual-track-research-20261017/refinements/hypotheses-frozen.json)로 과열 추격, 동반 하락·약매수, 약세 회복, 중립 VWAP·구조, 거래량 증가 함정, 거래량 축소 구간을 시험한다. F UNKNOWN은 기존 신호를 보존하고 branch 정제는 다른 정상 OR 경로를 제거하지 않는다.

실제 캡처 연구에서 발견한 후발 F29는 별도 시간·정의를 봉인한다. 종목 세션 변화 −0.4~+0.4%에서만 `60초 수익률 − spread ≥0.05%`를 요구하고 그 밖/UNKNOWN은 유지한다. 실제 표본의 개선을 전체 CF에 일반화하지 않고 별도 검증한다. 후발 F30은 중립 F26과 약세 F25를 결합하여 같은 하락 경로를 다른 국면에서 재허용하는지 확인한다. 결과를 본 뒤 추가한 가설이라는 탐색 편향을 명시한다. 위 약세/중립/강세는 종목 자체 세션 변화이며 시장 지수 regime가 아니다.

## 5. 비상시감시 종목의 호가 정합성

기존 연구의 `good_quote`는 age 미기록 또는 최대 5,000ms를 허용한다. 실제 AI 입력 전의 canonical quote 기준과 Main 제출 시의 더 엄격한 quote·출처·동일 route·현재 시각 재검증을 코드로 대조한다. 연구의 허용 범위가 넓다는 사실과 실제 선택 표본에 stale가 섞였다는 판단을 구분한다.

1. 고정 5종목과 비상시감시를 분리하여 raw·현재 CF·신규 A·실제 ENTER 표본의 quote age/UNKNOWN, W/STOP/TIMEOUT/U를 집계한다. 실제 `main_live` ENTER 중 비상시감시는 1건뿐이며 연결한 실제 판정 표본의 적격 손절 선도달은 0건이라는 관측 범위도 명시한다.
2. 제출 latency 분류 기본 SAFE 250ms·CAUTION 상한 700ms, AI 입력 전 3,000ms, 연구 5,000ms를 별도 표기한다. 환경별 override와 실제 PID의 유효 값은 별도 증빙이며 확인 당시 700ms 이내여도 AI·Main 전달 후 제출 적격을 입증한 것은 아니다.
3. 연구상 상승과 확인점 호가 필수조건을 충족한 CF의 교집합을 보고한다. 실제 제출 가능 여부는 이후 동일 intent의 재검증 증빙이 있을 때만 판정한다. 가격 틱 수만으로 0D 수신 연속성, 미래 재호가 가능성, 실제 주문 가격·수량·체결을 입증하지 않는다.
4. 실시간 거절 사례는 동일 evaluation/intent의 quote 수신→기계 확인→AI→Main 소비 시각과 사유를 연결한다. 해당 자료가 없으면 지연/수신 희소/감시 편입 문제를 임의로 확정하지 않는다.
5. 개선안은 기존 감시 편입 준비, 동일 route 호가의 재사용, 신선한 호가 도착 시 신호 재평가·현재 ask 재계산·중복 intent 방지, 시간 예산 안의 제한된 재검증을 우선 검토한다. quote TTL 완화·UNKNOWN 허용·현재 호가로 과거 ask 대체는 하지 않는다.

## 6. 비교 지표와 검증

라벨은 actual ask·30분·비용률 0.0023·비용 후 목표 +0.4%와 soft −3% 선도달이다. W/STOP/TIMEOUT/U를 분리하며 TIMEOUT은 실제 금전 손실이 아니다. 동일 item의 봉인된 완료 분봉은 원 계약의 검열·경계·동시 접촉 조건을 유지하며 장기 가격을 보조한다. 미래 가격은 라벨에만 사용한다.

scope 자체 분모 `W/(W+STOP+TIMEOUT)`을 우선하고 동률은 W 수와 current·고정 ID 순서를 사용한다. 성공 보존 100%/80%, 최소 일수·표본·별도 EV를 새 탈락 조건으로 넣지 않는다. 분모 없음은 100%가 아니다. 더 높은 비율에서 성공 기회가 줄어든 정도와 승률을 유지하며 W를 최대화한 대안도 공개한다.

검증은 prefix 불변·source break·hold 취소·UNKNOWN·OR, exact key/ask, 독립 선형 가격 라벨, 원 코드/원천 SHA, 기존 current 합계 복원을 포함한다. 낮은 우선순위 최대 2 worker, 각 2GiB/CPU 480초/wall 600초, 불변 partition receipt로 진행한다. 동일 누적 원천에서 가설을 탐색·비교하므로 독립 미래 성과를 입증하지 않는다.

## 7. 완료와 후속 인계

두 연구와 호가 정합성의 수치·반례·관측 한계를 [최종 연구 검토](../audits/main-cumulative-opportunity-failure-and-nonfixed-quote-review-2026-10-17.md)에 기록한다. 운영 적용 가능한 최종 정책이나 배포 완료를 뜻하지 않는다. 연구 후보와 비상시감시 source/consume 계약 개선을 분리하여 기존 [정책 반영 계획](main-cumulative-research-policy-adoption-plan-2026-10-14.md)의 다음 구현에 인계한다. 문서·링크·print-only parser를 검증하고 외부 동기화는 실행하지 않는다.
