# Main 가격 전진·한 호가 반등·회복 유형 추가 연구 — 2026-10-15

## 1. 범위와 선행조건

사용자 “연구를 진행하라. 수리 완료 확인이 필요할 경우 문의하라”에 따른 독립 진입 연구다. [주성 하드스톱 조사](/home/ubuntu/KORStockScan/docs/audits/main-jusung-hard-stop-pattern-and-full-flow-research-2026-10-15.md)에서 확인한 가격 무진전·정보 전달 차이를 모든 적격 종목·시장에 비교한다. 보유·장후 재생 계약 수리는 다른 세션의 소유이며 이 연구가 수정하지 않는다. 실제 preset/트레일링/수동 이관 이후 순손익을 결합해야 하는 단계에서 그 수리의 완료 증거가 필요하다. 기존 진입 label 연구는 기다리지 않고 수행한다.

작업 소유 위치는 [격리 연구 디렉터리](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/)다. production 모듈·정책 pointer·보조 프롬프트/응답·수동관리·provider·주문·배포·재기동은 변경하지 않는다. 미래 자동 작업이나 중복 checklist owner를 만들지 않는다.

## 2. 동결한 기준

[manifest](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/manifest.json)는 기존 [누적 두 축 연구](main-machine-cumulative-dual-track-research-plan-2026-10-15.md)의 27개 불변 partition, source/feature/label/code hash와 38개 가설을 이어받는다. 새 가설은 A17~A20, F23~F30의 12개이며 실행 결과를 보기 전에 고정했다.

현재 bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`은 parent와 같다. 선택본 `451b6c1ec84fafa563d95381e95c814ac2b2b18b`의 관련 기계 의존 코드 28개가 기존 연구 실행본 `bb4808c77087231b072efbd3ea12271fbb3889c6`와 byte 동일함을 확인했다. 따라서 **검증된 과거 current 신호·기존 A membership·라벨을 재사용**하고, 새 특징·root·확인점만 계산한다. 기존 특징을 재계산해 cached 값과 대조하며 모든 기존 대안을 남긴다. 새 기계 전수 재생이나 현재 PID 소비를 수행한 것으로 부르지 않는다.

원천 창은 9/29·9/30·10/2·10/6·10/7·10/8·10/12·10/13·10/14다. 원천에 있는 모든 종목·행을 census하고 기존 valid/제외를 보존한다. PRE=NXT `_NX`, REGULAR/AFTER=SOR `_AL`의 운용 route를 구분한다. 별도 KRX/NXT route 자료를 SOR로 복제하지 않는다. 정책의 48개 종목군·시장·가격대 scope를 전부 보고하되 적격 확인점이 없는 scope는 `no_eligible_confirmation`으로 남긴다. 일반 비고정 종목은 먼저 개별 symbol로 계산하고 기존 group으로 집계한다.

10/14·10/15의 기존 epoch 자격 결손을 이번 연구가 수리하거나 해제하지 않는다. 오늘 주성 사건은 진단·조건 대조 fixture이며 학습 W/STOP에 추가하지 않는다. 전 시장 실행 가능성과 원천이 실제 전 시장을 완전히 덮는다는 주장은 구분한다.

## 3. 특징과 인과 시각

- `return10_pct`: 연속 유효 10체결의 첫 가격→마지막 가격 변화율. 시작 가격은 9개 전 row다.
- `bid_return10_pct`: 같은 10행 동안 유효 quote와 native 연속성이 모두 확인될 때의 첫 bid→마지막 bid 변화율.
- `bid_return30_pct`: 같은 연속 quote 구간에서 현재 수신 시각보다 30초 이전 또는 같은 마지막 row의 bid 대비 변화율. 중간 quote 결손을 건너뛰지 않는다.
- `range_spread10`: 최근 10체결의 최고−최저 가격을 현재 유효 ask−bid로 나눈 값. spread 0/결손은 UNKNOWN이다.
- `price_progress_spreads10`: 마지막−첫 체결 가격을 현재 spread로 나눈 값. 현재 quote만으로 과거 bid 이동을 추정하지 않는다.
- 기존 `buy10`, 60초 수익률/VWAP/거래량, 최근·직전 30초 고점·저점, 세션 앵커 변화는 원 정의를 유지한다. 세션 등락은 개별 종목 기준이며 KOSPI/KOSDAQ 분류가 아니다.

모든 특징은 확인점 수신 prefix에서 계산한다. UNKNOWN은 F에서 원 신호 보존, A에서 불일치다. quote 결손으로 bid 특징이 UNKNOWN이어도 입증된 체결 가격 특징까지 0으로 바꾸지 않는다.

## 4. 사전 고정 가설

| ID | 기존 확인점 정제 F |
|---|---|
| F23 | 최근 10체결 가격 변화 >0 |
| F24 | 매수 비중 ≥60%일 때만 최근 10체결 가격 변화 >0 요구 |
| F25 | 최근 10체결 가격 범위가 현재 spread보다 큼 |
| F26 | 최근 10체결 가격 전진 ≥현재 spread, 같은 창 bid 상승 |
| F27 | 세션 −0.4% 미만에서만 고점·저점 동반 상승 AND 10행 bid 상승 요구 |
| F28 | 최근 10체결 가격 범위 ≤현재 spread일 때만 10행 bid 상승 요구 |
| F29 | 매수 비중 ≥60% AND 10체결 가격 변화 ≤0일 때만 고점·저점 동반 상승 AND 60초 수익률 >0 요구 |
| F30 | 세션 −0.4% 미만에서만 30초 bid 상승 AND 60초 수익률 ≥0.05% 요구 |

F는 scope 전체와 기존 각 branch replacement를 모두 비교한다. 다른 정상 OR branch가 허용한 기회를 덮어 차단하지 않는다. 조건부 F의 적용 조건이 UNKNOWN이면 원 확인점을 보존한다.

| ID | 별도 확인점 추가 A |
|---|---|
| A17 | FIRST_UPTICK 이후 최초 bid 상승, 그때 체결가가 최초 반등가 이상, 이후 체결가·bid 1초 유지, 확인점 VWAP 이상 |
| A18 | A17과 같은 root에서 체결가·bid 3초 유지, 확인점 VWAP 이상·매수 비중 ≥60% |
| A19 | 고점·저점 동반 상승 전환 후 기존 3초 체결가 유지 root, 확인점 bid 10행 상승·매수 비중 ≥60%·60초 수익률 ≥0 |
| A20 | 기존 VWAP 회복 전환 후 1초 체결가 유지 root, 확인점 10체결 가격·bid 모두 상승 |

A17/A18은 최초 반등부터 30초 이내 확인해야 하고 native/quote 단절 또는 기존 저점 이탈이면 해당 시도를 폐기한다. 최초 bid 상승 이후 가격/유지 조건에 실패하면 같은 root를 나중에 재사용하지 않는다. 별도 새 반등 root는 독립이다. 최초 bid 상승 시각의 bid와 체결가 아래로 유지 구간 중 한 번이라도 내려가면 실패다. 미래 경로로 anchor나 조건을 재선택하지 않는다.

## 5. 상황 유형과 비교 기준

진단 유형은 `DOWN_UNCONFIRMED`, `DOWN_RECOVERED`, `NEUTRAL`, `UP_CONTINUATION`, `UP_UNCONFIRMED`, `UNKNOWN` 6개다. 세션 ±0.4%를 기준으로 구분하고, 하락/상승에서 회복·지속 확인은 고점·저점 동반 상승 AND 60초 수익률 >0 AND bid 10행 상승이다. 필수 특징이 없으면 UNKNOWN이다. 유형은 연구 설명 축이며 자동 veto가 아니다. 매수 압력 대비 무진전과 한 spread 범위 태그도 별도 W/STOP/TIMEOUT/U로 집계한다.

기존 실제 ask·비용률 0.0023·30분·비용 후 +0.4% 목표/-3% 손절 선도달 label을 유지한다. actual ENTER_NOW, 현재 정책의 과거 재생 CF, 실제 체결·실현 손익을 구분한다. TIMEOUT은 실제 손실이 아니며 U는 실패에 합치지 않는다. 동일 item 완료 분봉 보조는 이전 동결 계약을 그대로 재사용한다.

current/A-only/F-only/J(`F(current) OR A`) 전체를 누적 `W/(W+STOP+TIMEOUT)` → W 수 → 동일 membership current canonical → 고정 ID 순으로 비교한다. 동률에서 실패/U만 더한 후보는 개선 제안으로 삼지 않는다. 성공 보존율·최소 표본/일수·새 holdout·추가 EV를 제한 조건으로 넣지 않는다. 새 후보의 개선은 current뿐 아니라 이전 38가설의 최고 대안과도 비교한다. 새 A가 기존 모든 A/current에도 없던 기회를 포착했는지 별도 표시한다.

## 6. 자원·검증·인계

단일 worker·낮은 우선순위, partition별 address space 2GiB·CPU480초·wall600초를 사용한다. 원천은 partition당 한 번 decode하고 후보 조합마다 반복 읽지 않는다. hash가 맞는 완료 checkpoint만 재사용하며 실패/미완료를 완료로 세지 않는다. 기존 신호·라벨 재사용 수, 새 label 계산 수, bytes·시간·RSS·전체 census를 기록한다.

필수 검증은 quote/native 단절, bid 상승 없는 가격 왕복, 유지 중 bid 후퇴, 저점 이탈, 미래 suffix 불변, UNKNOWN·OR, 승률 선택 반례다. 원천의 독립 선형 가격/quote 특징·라벨 oracle, 기존 모든 대안 수치 보존, scope48·partition27 census와 봉인을 검사한다. 결과·한계는 별도 audit와 기존 [정책 반영 계획](main-cumulative-research-policy-adoption-plan-2026-10-14.md)에 연결한다. 보조 입력·응답 변경이나 수리 완료를 전제로 하는 전체 매매 성과 결론은 내리지 않는다.

## 7. 실행 결과 연결

[실행 검토](../audits/main-entry-price-progress-and-situation-research-review-2026-10-15.md)와 [검증 receipt](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/validation.json)에 결과를 남겼다. 27개 partition·48 scope·전체35,558개 대안을 비교했고 이전 최선안이 바뀐 범위는 세 곳이다. 13개 표적 시험과 독립 원천 대조가 통과했다. 주성의 무진전·약세를 일괄 차단할 근거는 확인되지 않았다. 기존 가설·임계값은 결과를 보고 변경하지 않았다.

진입 연구의 완료는 보유·재생 수리 완료를 전제로 하지 않는다. 수리 인계가 필요한 실제 종료·비용 축은 별도로 남겼다. 최신 제안은 [정책 반영 계획 §10](main-cumulative-research-policy-adoption-plan-2026-10-14.md#10-1015-가격-전진회복-유형-연구-반영)을 소비하며 연구 결과를 운영 등록 영수증으로 사용하지 않는다.
