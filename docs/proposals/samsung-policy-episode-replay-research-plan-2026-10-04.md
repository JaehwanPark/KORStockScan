# 삼성전자 정책 직접 비교·연속 기회 재생 연구 실행계획

Owner: `SamsungPolicyEpisodeReplay1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행 근거: [기존 원천 연구](../audits/samsung-pattern-campaign-research-review-2026-10-04.md).

## 1. 질문과 실행 범위

사용자의 실행 지시에 따라 기존 원천에서 다음 질문을 실제 계산한다. 비용을 넘는 가격 왕복이 관측됐는가, 현재 Main보다 승률이 높은 진입 조건이 있는가, 종료 방식과 조기 청산 후 재진입이 결과를 바꾸는가. 가설별 음성 결과 뒤에도 다음 가설을 실행하며, 아래 의미가 다른 가설과 소비 한계 대사를 완료하거나 유효한 정책 후보를 확보하면 멈춘다. 수치만 추가해 무한 재최적화하지 않는다.

9/29·9/30·10/2 삼성전자 retained 체결/호가와 captured Main setup/판정·Widget 실제 fill 문맥·원래 비용 owner를 사용한다. 신규 원천 수집이나 API/provider 호출을 요청하지 않는다. 오프라인 정책 연구·코드리뷰·수정보완·재생은 승인됐으며 정책 publisher·실제 주문·배포·재기동은 이 연구의 실행 범위에 없다. 기존 성공100%/80% 보존 veto를 두지 않는다. 기존10/6 기동 소유 항목을 보존한다.

## 2. 위치·원천·비교 정책

독립 producer와 CLI는 `src/engine/scalping/samsung_policy_episode_research.py`, 회귀는 `src/tests/test_samsung_policy_episode_research.py`에 둔다. 기존 scalping offline 연구 package의 소유 범위이며 engine root나 live caller를 추가하지 않는다. Kiwoom protocol/parser/FID를 변경하지 않고 봉인된 normalized cache를 읽는다.

선행 verified regular/session manifests와 그 원천·kernel hash를 검증한다. 현재 selector 및 next-date machine bundle을 읽어 frozen parent machine hash `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`와 같은지 확인한다. captured setup을 그 정책으로 다시 판정해 선행 projection과 비교한다. 정책이 다르면 그 차이를 명시하고 동일 정책 비교를 주장하지 않는다. 계획/새 kernel/표적 test, current·dated machine bundle, 원래98개 정책/인계 hash를 봉인하고 실행 종료 후 대사한다.

`005930_AL/SOR_REGULAR` 및 다른4 exact 관측 scope를 날짜별로 유지한다. AL/NX의 같은 사건을 독립 지원으로 합산하거나 세션 사이 결손을 연결하지 않는다. 실제 실행 route·account/capacity·custody 상태가 없는 새 stream 신호는 가격 연구이며 주문 가능한 기회로 승격하지 않는다.

## 3. 단계별 연구

### R1: 가격 기회와 계산 단위

- 엄격한 유효 prefix에서 2/10/20/60분 내 비용+순0.1% 이상 미래 bid가 관측되는지 계산한다. 최대 관측 MFE, 충분한 종료창, 미도달과 검열을 각각 보고한다. 미래 최대값은 기회 존재의 진단 전용이며 학습 feature나 진입 selector로 사용하지 않는다.
- native ID, 고유 decision trace, 가격 재생 episode를 분리한다. 고정 감시의 하루 ID가 여러 판정을 한 기회로 축약하는 효과를 실제 집계한다. 새로운 가격 episode ID를 native promotion 지원수로 사용하지 않는다.
- 조건부 목표 선도달 승률을 유지한다. 유효한 시간 종료도 포함한 비용 후 양수 비율을 별도 계산해 성공 정의와 분모 차이를 보여준다. 결과 결손은 null이며 실패0·손익0으로 대체하지 않는다.

### R2: 현재 Main과 직접 비교

- 현재와 동일 hash 정책으로 captured Main 판정을 재생한다. original full-cost binary label을 보존해 `기존 ENTER만 조건부 veto`와 `기존 soft-confirmation 적격 판정에서 추가 진입`을 비교한다. source/liquidity 및 원래 hard guard·recoverable 조건을 지킨다. 전략 위험 gate와 실제 broker safety 증빙의 차이도 표시한다.
- trace 단위 진단, 기존 native 첫 admission 단위, 가격 terminal/cooldown에 따른 비중첩 단위를 따로 계산한다. 동일 attempt의 원래 label을 새로운 ask/bid 가격 CF로 대체하지 않는다.
- `veto`, `soft_add`, 두 동작을 함께 평가하는 `replace_soft`를 고정한다. 상태 신호는60초 이내·같은 유효 prefix·현재 ask가 신호 ask+500원 이내인 captured 판정에만 연결한다. 이 조건은 과거 정보만 사용한 연구 adapter이며 현재 runtime에 등록하지 않는다.
- 단순 첫-ENTER label, 무조건 시계 benchmark, 실제 broker 체결 성능은 서로 다른 비교이므로 이름과 분모를 명시한다.

### R3: 과거 상태 변화와 진입·청산·재진입

신호는 과거 frame과 당시 quote만 사용한다. 아래6개 상태 가설을 과거 창300/900초, 확인기간5/15초로 사전 고정한다. 신호는 각 상태 사이의 시간 순서를 확인하고 새 episode당 최초 신호만 발행한다. 미래 terminal 결과에 따라 신호를 고르지 않는다.

| 가설 | 상태의 순서 |
|---|---|
| base_recovery | 과거 고점 대비 하락 → 저점 안정 → bid 회복 및 매수 우세 |
| absorption_release | 저점에서 매도 우세·bid 유지 → 매도량 감소 및 매수 전환 |
| failed_breakdown | 과거 지지선 하향 이탈 → 과거 지지선 재회복 |
| higher_low_sequence | 저점 → 반등 → 더 높은 저점 재시험 → 재반등 |
| pullback_resume | 과거 고점 회복 → 눌림 → 매수 우세 재상승 |
| range_return | 비용을 넘는 과거 range → 하단 방문·안정 → 하단 탈출 |

순목표+0.1%/gross stop−0.7%/20분 barrier를 기준으로 진입 효과를 계산한다. 같은 captured ENTER와 같은 새 신호에6종 종료 모델을 적용해 청산 효과를 비교한다: barrier, 10분 시간 종료, 20분 시간 종료, live pure trailing 공식의 start0.4/width0.4, start0.4/width0.8 민감도, start0.1/width0.2 연구. trailing은 기존 pure kernel을 쓰되 bid peak 기반·고정 width 민감도임을 표시한다. 실제 Main의 trade peak/strength state/hard stop/order를 전부 재현했다고 주장하지 않는다.

두 비용 표현은 exact-date quote fee/tax/buffer0.23% 및 stress0.33%다. ask 진입·bid 종료로 spread를 가격에 반영한다. 추가 impact0인 비교 비용과 실제 broker 대사 비용을 구분한다. gross stop−0.7%는 연구 boundary이며 실제 hard stop을 재튜닝하지 않는다.

재진입은 관측 terminal+5/60초 뒤만 허용한다. terminal을 모르면 가상 보유 상태를 유지하고 그 scope/day의 후속 admission을 차단한다. 결손 직후 성공 신호로 교체하지 않는다. 기존 horizon 전체 예약과의 차이를 같은 신호/종료 모델로 대사한다. 어느 모델도 겹치는 보유를 독립 거래로 세지 않는다.

## 4. 선택·검증·종료

R1의 겹치는 frame 수와 실제 구별되는 가격 움직임을 함께 확인한다. 과거 최저 ask에서 이후 bid가 비용+순0/0.1/0.4%를 회복한 비중첩 사건을60초 간격으로 집계한다. 최저 ask를 실제로 미리 선택할 수 있었다고 가정하지 않으며, 이 사후 가격 사건은 신호 학습이나 native 지원에 사용하지 않는다.

기존 자료 census에서9/28 Samsung 정규장 체결278,975·호가111,625행도 발견했다. 추가 수집 없이 같은 normalized domain reader와 exact-date 비용을 검증해 이미 선정한 조건을 변경 없이 적용한다. 현재 machine의 실제 활성 generation hash는9/28부터 동일하지만 이날 captured Main projection은 보관되지 않았으므로 가격 안정성 확인으로 한정한다. 학습보다 앞선 날짜를 새 chronological holdout이라고 부르지 않고 후단 조건을 다시 고르지 않는다. 가격 데이터만으로 이날 Main 판정을 합성하지 않는다.

첫6종 종료 재생의 후속 단계로 두 가지 정보가 다른 종료 가설을 추가한다. `state_failure`는 진입 당시 bid보다500원 하락해 회복의 가격 약속이 깨졌을 때 추가 soft exit를 관측한다. `past_ceiling`은 진입 이전900초(없으면300초) 저항 가격과 비용+순0.1% 중 큰 가격에 도달하면 종료한다. 둘 다 기존−0.7% 연구 stop은 우선 유지하며 실제 hard stop을 수정하지 않는다. 매개변수 숫자 확장 대신 진입 이후 구조와 과거 저항 정보를 사용한 종료 효과를 확인하는 단계다.

기존 관측 간격3/10초 진단을 같은 신호·원래 native label에 적용한다. 입력 신호와 captured adapter는 계속 엄격한1.5초 과거 prefix를 사용하고, 미래 가격 경로의 관측 간격 모델만 바꾼다. 간격 사이 경로를 보간하거나 공식 label/freshness를 변경하지 않는다. 기본 모형에서 고른 후보를 같은 조건으로 민감도 검증하고 각 모형의 학습 선택도 별도로 표시한다. 큰 간격에서만 좋은 결과는 운영 후보로 인정하지 않는다.

- 9/29 학습→9/30 및9/29~30 학습→10/2 순서를 고정한다. 후보는 각 가설군의 학습 기준에서 고정하며 후단을 보고 다시 선정하지 않는다. 이미 반복 탐색한 날짜이므로 `pristine_holdout=false`다.
- original Main binary 비교는 native 및 trace 지원을 별도 공개한다. 연구 선택은 원래 비용 후 target-first 승률 우선이고, 시간 종료 포함 양수 비율·평균CF·최악CF·검열/coverage를 함께 보고한다. 성공 보존율이나 평균CF양수를 새로운 machine 선택 veto로 넣지 않는다.
- 종료 방식이 다른 가격 replay의 선택은 별도의 시간 종료 포함 양수 비율로 수행하고 original machine target-first 선택과 구분한다. 비용은 selectable knob가 아니며0.23% 시나리오에서 고른 동일 조건을0.33% stress로 다시 평가한다. 실제 Main exit 전체를 재현하지 못한 민감도에서 formal machine 정책을 발행하지 않는다.
- 최소3개의 비교 가능한 학습 결과와3개의 후단 결과는 연구 후보의 지원 확인에만 쓴다. 공식 publisher의 date/opportunity/source/guard 계약을 낮추지 않는다. 가격 연구, 현재 정책 대비 연구 후보, 정식 생성기의 유효 후보, 실제 적용을 각각 표시한다.
- 첫 양성에서 결과를 확대 해석하지 않고 지연250/1000ms, 비용 stress, 기존 native·soft admission 연결, 전체 원천과 누락 상태를 확인한다. 운영에 적용할 만한 후보가 확보되면 추가 가설 탐색을 멈춘다.
- R1~R3의 모든 구별되는 가설을 평가하고 남은 실패가 원천/provenance 한계인지 측정된 낮은 승률인지 대사한 후에만 가설 소진으로 종료한다. 동일3일의 새 숫자 조합, 이미 검열된 경로의 반복 재생, 후단 승자 재선정은 후속 가설로 인정하지 않는다.
- 현재 실제 publisher의 `native_scanner_or_fixed_watch_v2` 및 학습30·후단10 selected opportunity floor도 직접 읽어 확인한다. 모든 source-valid 판정을 허용하는 가장 넓은 후보라도 확보할 수 있는 native 그룹 상한을 계산한다. 신호 개선만으로 이 상한을 넘을 수 없다면 추가 조건 탐색의 정식 정책 생성 가능성은 닫힌다. 이를 시장 edge 부재나 모든 연구 방향 소진으로 표현하지 않고, producer/consumer 기회 단위 보완의 근거와 후속 계약을 기록한다.

## 5. 리뷰와 검증

구현→리뷰→수정→재리뷰→표적 pytest·compile·diff 체크 뒤 최소 재생을 실행한다. 회귀는 terminal 이전 invalid/gap·epoch/sequence, 시간 종료 수익 분모, 과거 state와 prefix 불변성, 조기 종료 후 admission, 미해결 포지션 후 재진입 차단, native/trace 분모와 학습 전용 선택을 검증한다. 결과를 동일 source/code generation으로 재실행해 내용 hash/metric을 대사하고 현재 정책/인계 보존을 확인한다. 문서·stable owner·링크 검증과 print-only parser를 실행하며 외부 sync는 사용자 표준 명령만 남긴다.

결과 기록은 [연구 리뷰](../audits/samsung-policy-episode-replay-research-review-2026-10-04.md)에 남긴다. 그 기록의 완료 수치와 실패/보류 원인을 확인하기 전에는 유효 정책 확보나 운영 성능 개선으로 종료하지 않는다.
