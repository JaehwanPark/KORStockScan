# 스캘핑 익절 강약 기계판정 장후 튜닝·런타임 폐루프 구현계획

작성 기준: 2026-09-25 KST 작업트리. 계획 문서이며 코드 변경, 정책 선택, 릴리스 전환, 주문 실행 영수증이 아니다.

## 1. 결정과 현재 결손

정책 시장은 `PREMARKET`, `REGULAR`, `INTEGRATED_AFTERMARKET` 세 가지로 고정한다. **기존 `scalp_trailing_take_profit`의 강약 판정만** 시장별로 튜닝한다. 익절 수익축 세 개(시작·약폭·강폭)는 같은 정책 owner에 남는다. 손절·soft-stop의 AI 점수, 공유 시세 안전 기준, REST/provider, 주문 수량·가격·라우팅은 이 선택기의 조정 대상이 아니다. `UNKNOWN`은 원천 결손 상태로 유지하고 익절 폭 선택에서는 기존 약폭을 쓴다.

현재 [`trailing_mechanical_strength.py`](../../src/engine/scalping/trailing_mechanical_strength.py)는 1,000ms 체결창, 양수 OFI·호가 불균형·순매수 체결 및 반대 증거 2회가 코드 상수다. [`trailing_mechanical_replay.py`](../../src/engine/scalping/trailing_mechanical_replay.py)의 7개 변형은 시장별·약강폭별 비용 후 민감도를 계산하지만 `report_only_no_runtime_apply`, `research_candidate=None`으로 끝난다. [`trailing_mechanical_policy.py`](../../src/engine/scalping/trailing_mechanical_policy.py)와 bootstrap은 **수익축 9개 값만** 선택하고 분류기 버전·고정 파라미터 hash만 확인한다. 장후 분류기 후보 생산자, 선택 영수증, 시장별 파라미터 소비자와 적용 후 귀속이 없다.

더 앞선 원천 연결도 필요하다. 현재 `holding_exit_observation`은 정오 full monitor snapshot에서 생성되며, 장후 `runtime_approval_summary`가 그 파일을 읽는다. 2026-09-25 12:04 생성 파일은 신형 `trailing_mechanical_market_tuning` 키가 없는 이전 세대이고 완료 모수도 불완전하다. 이를 자연 M1의 성과 부재로 해석하지 않는다. 장후 최종 체결 원천의 **동일 날짜·동일 릴리스 세대 보고서**를 선행 생산해야 한다.

작업트리의 Plan Rebase §5와 시장 session contract는 프리마켓 청산 가능 시각을 현재 허용하지만, 선택된 불변 릴리스와 작업트리의 `session_contract.py`, 정책/bootstrap/보고서 내용은 다르다. 구현 시작 시 실제 선택 릴리스·정확 날짜 정책·PID와 작업트리를 별도 대사하고, 청산 가능 여부는 해당 포지션 평가시각의 **실제 적용 세대**로 재생한다. 과거 제안서의 프리마켓 청산금지 문장을 정책 사실로 재사용하지 않는다.

```text
0B/0D 원시 영수증 + BUY/SELL/비용 완료 projection
  → 장후 동일세대 청산 보고서 → 시장별 분류기×익절폭 재생
  → 봉인된 train/독립 holdout 후보 → 같은 익절 owner의 선택 영수증
  → 다음 PREOPEN bootstrap → 실제 PID 소비 → 적용 후 완료 포지션 R6
  → 다음 장후 누적 모수에 새 완료 건 추가
```

## 2. 조정축과 고정 계약

첫 정책 버전은 현행 M1의 **검증된 0B와 연속 0D를 함께 요구하는 구조**를 유지한다. 양수 지지로 STRONG 승격, 강 상태에서 연속 반대 증거로 WEAK 강등을 각각 조정한다. `queue_only`, `ofi_only`, `trade_only`는 원천 구조를 바꾸므로 별도 비교 진단으로 남기고 첫 자동 후보 격자에는 넣지 않는다.

| 시장별 조정축 | 현행과 동등한 시작값 | 첫 봉인 후보 | 소비 의미 |
| --- | ---: | --- | --- |
| `trade_window_ms` | 1000 | 500, 1000 | 0D 시점 직전 검증된 0B 창·만료 기준. 현재 보존한 1000ms 원시 체결에서 500ms를 재계산한다. |
| `strong_queue_min` | 0 | 0, 0.1 | STRONG 승격 시 호가 수량 불균형 `>` |
| `strong_ofi_min` | 0 | 0, 0.1 | STRONG 승격 시 정규화 OFI 대용치 `>` |
| `strong_signed_qty_min` | 0 | 0, 10 | STRONG 승격 시 검증된 순매수 체결 수량 `>` |
| `weak_queue_negative_min` | 0 | 0, 0.1 | 강 상태에서 호가 불균형 `< -값` |
| `weak_ofi_negative_min` | 0 | 0, 0.1 | 강 상태에서 OFI 대용치 `< -값` |
| `weak_signed_qty_negative_min` | 0 | 0, 10 | 강 상태에서 순체결 수량 `< -값` |
| `adverse_updates_required` | 2 | 2, 3 | 서로 다른 연속 0D의 반대 증거 횟수 |

모든 시장의 시작값은 같은 현행 M1 의미다. `book_cutoff`는 현재 hash에만 있고 독립 소비가 없으므로 신 스키마에서 제거하고 `ofi`·`queue` 축으로 의미를 고정한다. `signed_qty`는 절대 수량이므로 종목·유동성 구간별 편중을 보고하고 한 종목/한 유동성 구간만의 이익으로 자동 선택하지 않는다. 1000ms보다 긴 창은 현행 journal로 완전성을 증명할 수 없어 첫 후보에서 제외한다. 이후 원시 0B 영수증 보존창·용량·watermark를 확장한 별도 증거가 생길 때만 격자에 추가한다.

동일 symbol/item·route·transport epoch, 단조 시각과 연속 시퀀스, 검증된 aggressor 부호, 유효 0D 호가, 기존 quote-consistency 및 주문 안전은 **조정하지 않는 입력 계약**이다. 원천 만료·누락·충돌은 `UNKNOWN`; 값 0이나 중립 수급으로 보간하지 않는다. 분류기는 새로운 REST/AI 호출이나 주문 소유자를 만들지 않는다. 시작·폭 세 수익축과 분류기 여덟 축은 같은 `scalp_trailing_take_profit` 단계의 **하나의 결합 정책**으로 버전 관리한다.

## 3. 모수·재생·후보 선정

1. 공통 모수는 clean baseline 이후 진입한 실거래 포지션 중 실제 BUY 체결 수량, 모든 SELL 체결·잔량 0, DB `COMPLETED`·유효 수익률, 체결 기반 비용 증거를 모두 충족한 ID다. 다른 규칙 청산도 포함한다. 정확 SELL 시각이 없어도 완료·비용이 증명되면 공통 모수에 남기되 시점 재생에서 제외하고 사유를 기록한다. sim/probe/CF, 구 AI 세대와 정책 혼합 포지션은 M1 paired 효과에 섞지 않는다.
2. 각 포지션은 평가시각의 시장·실제 정책 hash·source item/route/epoch로 분할한다. 기본 M1의 원시 0B/0D journal, 첫 crossing, 실행 가능 bid/수량, 실제 매도 시각·경쟁 청산을 대사한다. 다음에 후보별 강약 상태를 **원시 체결 영수증으로 다시 계산**한다. 현재 구현처럼 live 1000ms에서 집계한 `signed_trade_qty`만 재사용하면 500ms 후보가 잘못 계산되므로 교체한다. 용량 초과·누락 시 후보별 `source_gap`을 남긴다.
3. 후보는 같은 포지션 경로에서 실제 청산 전 첫 신호를 재생한다. 후보 신호가 실제 청산보다 늦거나 그 뒤 실행 호가가 없는 경우는 검열한다. 최우선 매수호가 수량이 포지션 수량보다 적으면 전량 체결로 간주하지 않는다. 관측되지 않은 후속 bid·비용을 0이나 실제 체결로 대체하지 않는다. 미노출 적격 포지션은 효과 0으로 전체 분모에 남긴다.
4. 목적 함수는 **전체 적격 완료 포지션의 비용 후 paired EV와 순이익 변화**다. 0/30/100bp 실행 민감도, 큰 손실, 놓친 후속 상승, STRONG/WEAK/UNKNOWN 노출, 청산 지연·경쟁 청산을 함께 기록한다. 시장별 정책 효과와 세 시장을 합친 실제 자본 가중 효과를 모두 본다. 검열은 후보별 ID·원인·명목금액과 보수적 경계로 공개하고 유리한 후보만 남기는 분모 변경을 금지한다. train 순위는 공통 ID의 세 slippage 시나리오 중 최소 paired EV로 정하고, 동률이면 현행 정책에서 변경한 축 수가 적은 값을 우선한다.
5. 훈련 날짜에서 격자·특징·최대 후보 수를 봉인한다. 먼저 여덟 축의 단일 변경을 비교하고, STRONG 승격 3축과 WEAK 강등 3축의 소수 조합, 분류기×약폭/강폭, 필요 시 시작값과의 상호작용을 평가한다. 2⁸ 전체 조합을 무제한 탐색하지 않는다. 최신 독립 완료 날짜에서 재선택하지 않고, 비교는 후보 전체의 공통 ID와 동일 비용/검열 모델로 한다. 다중 비교 수와 우승 후보의 train/holdout 격차를 공개한다. 과최적화 위험 때문에 사전 봉인과 독립 검증을 쓰는 것은 [Bailey 등 원 논문](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)의 취지와도 맞는다.
6. 자동 후보의 최소 조건은 현행 수익축의 30 train/10 holdout 및 최신 독립 2일 검증보다 느슨하지 않게 둔다. 변경 시장에서 실제 STRONG/WEAK **상태 전환 차이**가 생긴 포지션도 train 10건·holdout 5건 이상, 각각 2종목 이상을 요구한다. 해당 시장 노출이 0이면 `unidentified_no_exposure`로 보류한다. 종목·유동성·route별 노출과 효과를 보고, 적용될 주요 route의 직접 표본이 없거나 단일 종목의 이익에만 의존하면 자동 선택을 보류한다. 보수적 비용 후 EV·worst slippage·holdout 각 날짜가 모두 양수이고 큰 손실/stop 지연 안전 veto가 없을 때만 선택 심사로 넘긴다. 부족한 자연 M1 표본은 `hold_sample`; 과거 중립 추정은 진단일 뿐 승격 근거가 아니다.

## 4. 생산자·선택기·런타임 연결

| 단계 | 구현 위치와 산출물 | 필수 연결·차단 |
| --- | --- | --- |
| 장후 원천 | 기존 `log_archive_service.py` / `run_monitor_snapshot.py`에 **청산 전용 postclose profile**을 두어 최종 trade review → post-sell → holding-exit 보고서를 같은 날짜·세대 순서로 생성. `run_threshold_cycle_postclose.sh`에서 최종 체결 projection 이후, `runtime_approval_summary` 이전에 실행. | 정오 파일 재사용 금지. 원천 경로·byte SHA256, 완료 census, terminal/비용 품질, 보고서 종료 영수증을 검증. 새 wrapper 단계는 운영 문서·현재 checklist owner와 함께 등록. |
| 재생 계산 | `src/engine/scalping/trailing_mechanical_strength.py`의 순수 상태기계를 파라미터 입력형으로 만들고 live/replay 공용으로 사용. `trailing_mechanical_replay.py`는 원시 journal에서 후보별 상태·첫 crossing 재생. | 코드와 보고서의 판정식 중복 제거. 시장·route·epoch·정책 hash별 reset, 결손 ID 격리, 비용/검열 동일성 검사. |
| 장후 후보 생산 | `holding_exit_observation_report.py`에 시장별 상태전환·공통분모·상호작용·독립 검증을 보고. `src/engine/automation/`의 별도 익절 정책 publisher가 최종 보고서의 봉인된 hash·후보를 소비. | 보고서 자체는 `report_only`. publisher만 `hold_sample|hold_source_gap|hold_no_edge|candidate_review_ready`를 만들고 검토 게이트 통과 후 단일 `allowed_runtime_apply` 영수증을 낸다. 파서 성공만으로 적용 허가 금지. |
| 선택 영수증 | 기존 `scalp_trailing_mechanical_three_axis_selector`를 **동일 owner의 결합 정책 v2**로 확장. 세 시장의 수익축 9개+분류기 8×3 값, classifier 코드 버전, 부모 결합 hash, 보고서 raw hash, 후보 grid/model hash, source/holdout/안전/동일 단계 검토, rollback을 기록. | 별도 분류기 family를 만들지 않는다. 같은 단계의 수익축 후보와 동시 canary 금지. 한 번에 **한 시장만** 기준선에서 변경하고 다른 두 시장은 이전 적용값을 보존. 명시적 operator lock 우선. |
| 다음 PREOPEN | `runtime_policy_bootstrap.py`와 `deploy/run_threshold_cycle_preopen.sh`가 정확 날짜 정책 receipt를 포함하고 부모 hash CAS, 값 범위, 시장 완전성, report source bytes, 한 단계 canary, 모든 env owner를 확인. content-addressed 적용 정책 파일과 SHA256을 launcher에 pin. | 미선택·표본 부족이면 직전 유효 정책 carry. 선택 영수증이 있는데 hash/세대가 틀리면 조용히 기본값 적용하지 않고 fail closed. 수익축 env와 분류기 파일 값이 다르면 기동 전 실패. |
| 실거래 소비 | fast/normal의 공용 loader가 검증된 시장별 분류기 파라미터를 **기동 시 1회** 읽고 같은 position state에 적용. 이벤트 로그에 적용 정책 hash·시장·판정 입력·상태·선택 폭·첫 crossing 기록. | 평가 이벤트마다 env/파일 재읽기 금지. 현재 프로세스에 중간 적용 금지. 새 적용 세대에서 기존 보유분은 arm/peak 유지, 분류기 상태는 UNKNOWN으로 reset; 혼합 세대는 장후 paired 효과에서 분리. 선택된 정책에는 런타임 날짜 만료를 두지 않고 후속 선택/원복까지 유지. |
| R6 귀속·원복 | `runtime_approval_summary.py`, `holding_exit_sentinel.py`, 사후 outcome 집계가 선택→PREOPEN→PID 정책 소비→자연 완료·비용 후 EV를 개별 필드로 연결. | 심각한 손실·stop 지연·주문 오류·원천 손상·동일 단계 충돌은 기존 안전 원복 절차. 일일 성과 부재는 자동 원복 사유가 아니며 다음 후보는 보류. 이전 결합 정책 파일과 selector/receipt를 보존. |

최초 구현·배포 승인 이후의 적격 변경만 기존 `auto_bounded_live` 경계에서 **다음 PREOPEN 한 단계 canary**로 적용한다. canary 결과를 근거로 한 전 시장 전체 적용은 Plan Rebase의 별도 full-live 승인 조건을 따른다. 이 계획 문서는 최초 배포나 자동 승인 권한 자체를 부여하지 않는다.

분류기 코드의 현재 `CLASSIFIER_PARAMS` 해시와 실제 하드코딩 값이 이원화되어 있다. 신 버전에서는 **실제로 소비한 typed config의 정규화 바이트**를 해시한다. 숫자 문자열·bool·NaN·음수·중복 키·시장 누락·강폭<약폭·창이 보존 가능 범위를 벗어난 값을 거절한다. 정책 generation이 바뀌면 동일 포지션의 source path에 hash를 남기고 혼합을 검열한다.

v1 수익축 적용값은 정확한 부모 hash로 v2의 첫 incumbent에 이관한다. 이전 v1 후보 영수증을 새 분류기 정책으로 재해석하거나 재적용하지 않는다. 적용 중인 operator lock과 별도 승인 override는 이관 전후 동일한 우선순위를 갖는다.

## 5. 테스트 데이터 기반 결과·성능 결함 점검

### 5.1 입력 세트와 판정 기준

테스트 생성기는 고정 seed·고정 event-time으로 원시 0B/0D, BUY/SELL 체결, 비용, 정책 영수증을 만든다. 각 세트는 입력 파일 SHA256, 기대한 포지션 ID 집합, 시장·route·epoch·정책 hash, 기대 상태열·첫 crossing·익절 폭·검열 사유를 manifest에 봉인한다. 세 시장에 **동일한 경계 사례**를 각각 만들고, 시장별 값만 바꾼 사례를 별도로 둔다. 테스트용 주문·REST는 실제 계좌에 닿지 않는 fixture/모의 경계에서 실행한다. 기존 [`test_scalp_trailing_mechanical_strength.py`](../../src/tests/test_scalp_trailing_mechanical_strength.py)와 [`test_scalp_trailing_four_axis_replay.py`](../../src/tests/test_scalp_trailing_four_axis_replay.py)의 회귀를 확장하되, 새 M1 세대에 맞지 않는 구 4축 결과를 새 정책의 정답이나 속도 기준으로 쓰지 않는다.

| 데이터 세트 | 반드시 포함할 경계·결손 | 독립 정답과 실패 판정 |
| --- | --- | --- |
| **E: 이벤트/상태** | 500/1000ms 창 안팎, 각 임계값과 정확히 같은 값 및 바로 위/아래 값, 0D 유효·만료 경계, 동일 ms의 0B/0D 순번, 중복·역전·누락 시퀀스, 120행 이력 상한, route/epoch/시장/포지션 전환, 강 승격·유지·2/3회 강등 | 캐시 없는 단순 event-time 참조 판정기가 각 0D까지의 원시 0B만 재집계한다. **같은 후보 설정**의 fast/normal/장후 상태열과 `UNKNOWN` 사유가 ID·이벤트별 정확히 같아야 한다. 500ms 후보는 live 1000ms 합계를 재사용하면 실패한다. |
| **X: 신호/경쟁 청산** | arm 전 강약 갱신, batch 내 첫 약폭 crossing 뒤 강 승격, 고점 갱신과 같은 0D, 세션 경계·닫힌 시간, 경쟁 손절이 먼저 발생, 실제 청산 이후의 후보 신호 | 첫 crossing 시각·당시 폭 latch·실행 가능 bid/수량을 독립 참조 경로와 대사한다. 뒤 이벤트가 첫 신호를 소급 변경하거나 stop보다 늦은 TP가 체결로 계산되면 실패한다. 세션 가능 여부는 이벤트의 실제 적용 정책 세대로 판정한다. |
| **C: 완료 모수/경제성** | 복수 BUY·부분 SELL 후 최종 잔량 0, 다른 청산 owner, 정확 SELL 시각 없음, `COMPLETED`/수익률/체결 비용 각각 결손, 최우선 bid 수량 부족·bid 자체 결손, 미노출 포지션, 완료일과 진입일 불일치, 중복·불일치 ID | BUY=SELL·잔량0·완료·유효 수익률·비용 충족 ID만 공통 분모에 넣는다. 시각 없는 완료 건은 분모에 남기고 직접 시점 재생에서만 제외한다. 부분 수량은 검열, bid 원천 부재는 `source_gap`, 미노출은 효과 0, 불일치 ID는 사유와 함께 격리한다. 0/30/100bp 비용 후 결과·공통 ID·검열 명목금액을 독립 계산과 대사한다. |
| **P: 선택/소비** | v1→v2 정확 부모 hash 이관, 세 시장 중 한 시장만 변경, 선택 후보 없음, 정오/전일 보고서, report raw hash 변조, 비용 미완료, 정책 숫자·시장 누락, lock/CAS 충돌, 혼합 정책 세대, report-only 후보 | 동일 owner의 선택 영수증→정확 날짜 PREOPEN→정확 hash PID 소비를 단계별 확인한다. 무효 선택은 조용한 기본값 적용 없이 차단하고, 표본 부족은 기존 유효값을 carry한다. report-only 변형은 어느 단계에서도 선택되지 않아야 한다. |
| **L: 부하/확장** | 0·1·80건 완료 fixture, 실제 크기를 닮은 봉인된 익명화 완료 자료, 여러 보유종목의 0B/0D burst, 120행 포화, 두 스레드 lock 경합, 후보 격자·세 시장 전체 | 작은 세트와 큰 세트의 **동일 ID별 결과**가 같아야 한다. 입력 이벤트 수·후보 수·검열/결손 ID가 빠짐없이 보존되어야 하며, 처리 지연·메모리·lock 대기를 아래 기준으로 판정한다. |

보존 자료의 완료·유효 수익률 329건이나 기존 정오 보고서는 원천 필드가 부족하면 **원천 결손·처리량 점검**에만 쓴다. 합성 80건에서 계산된 양의 EV나 상태전환은 참조식 검증용이며 자연 성과·독립 날짜 holdout의 대체물이 아니다. 실자료 fixture는 민감 식별자를 제거해 읽기 전용으로 봉인하고, 누락 필드를 임의로 채워 직접 M1 적격 건으로 승격하지 않는다.

### 5.2 결과 결함 대사와 반복 절차

1. **두 계산기 대사:** 단순 참조 구현은 각 후보·각 0D에서 원시 journal을 처음부터 재생하고, 최적화 구현과 코드 경로·캐시를 공유하지 않는다. **현행 기본 설정은 구 M1과**, 새 후보 설정은 독립 참조식과 비교한다. 이벤트별 `UNKNOWN/WEAK/STRONG`, 전환 횟수, 첫 crossing 시각·가격·폭, stop 선행 여부, 후보별 완료/검열/원천 결손 ID 집합을 정확 일치로 비교한다. 수량은 정수 체결 단위, 금액은 체결 영수증의 통화 최소 단위에서 일치시키고, 반올림은 **최종 비용 후 합계에서 한 번만** 적용한다. 허용 오차를 만들기 위해 원천 결손을 0으로 바꾸지 않는다.
2. **분모 보존:** 원천 완료 ID = 직접 재생 가능 ∪ 시각/호가 검열 ∪ 원천 결손/격리 ID로 중복 없이 대사하고, 후보마다 공통 비교 ID와 제외 사유를 출력한다. 결손 이벤트를 주입하면 해당 경로의 직접 적격 건수가 늘지 않아야 하고, ID 중복은 성과를 두 번 더하지 않아야 한다. 임계값 경계의 `>`·`<` 방향, strong 승격 경계를 높였을 때 같은 원시 경로에서 새 STRONG 승격이 생기지 않는 성질도 검사한다.
3. **경제성/선택:** train·holdout 분리는 **최종 SELL 완료일**로 결정하고 holdout을 후보 탐색에 재사용하지 않는다. 0/30/100bp 모두 같은 포지션과 비용 영수증을 사용한다. 여러 후보가 동일한 paired EV를 내면 변경 축 수가 적은 후보를 선택한다. 후보가 0개인 날짜, 한 시장만 바뀐 날짜, 검열 비중이 큰 날짜의 `hold_*`·carry 및 veto 사유까지 예상 manifest와 일치해야 한다.
4. **결함 분류와 수정:** 불일치는 `판정식/시각`, `분모·비용`, `원천 결손`, `안전 검열`, `선택·세대`, `fixture 오류`, `성능`으로 분류하고 처음 실패한 ID·이벤트·후보·hash를 재현 자료로 남긴다. 원천 결손은 수익성 0이나 정책 열위로 해석하지 않는다. 수정 뒤 최초 실패 fixture와 인접 시장·fast/normal·장후 소비자를 함께 재실행하고 코드 리뷰→수정보완→재검토를 반복한다.

### 5.3 성능 측정과 합격선

같은 호스트·같은 봉인 입력·같은 환경에서 **현행 고정 M1의 봉인된 코드 버전**과 신 파라미터형 M1의 **현행값 설정**을 각각 5회 이상, cold/warm 상태로 측정하고 각 반복의 p99 중앙값을 비교한다. 선택 릴리스나 실제 PID는 성능 fixture 실행을 위해 변경하지 않는다. CPU 부하·동시 보유 수·입력 이벤트 수·후보 격자·코드 hash를 manifest에 적고, `perf_counter` 구간시간과 `/usr/bin/time -v`의 wall/CPU/최대 RSS·swap을 함께 저장한다. 재생 경로는 1/80건과 현행 보존자료 크기, 이후 관측 최고 부하의 2배 이벤트 burst를 실행한다. fast 경로는 분류만, lock 포함 0B/0D 처리, 구조화 로그 실제 쓰기, 첫 신호→청산 호출까지 **각각** 측정한다. 모의 I/O 수치와 실제 파일 I/O 수치를 합쳐 평균 내지 않는다.

| 범위 | 기록할 성능·정합 지표 | 합격/중단 조건 |
| --- | --- | --- |
| fast/normal 실시간 | 이벤트 수·유실/병합·대기열 최대치, 분류/전체 경로 p50·p95·p99·최대 지연, lock 대기 p99, CPU/RSS/swap, 추가 REST·AI·주문 호출, 신호→청산 호출 지연 | 현행값 설정의 상태·첫 신호는 구 M1과, 후보 설정은 참조식과 정확 일치하고 이벤트 유실·추가 API/AI·중복 주문이 0. **모의 I/O fast 분류 p99는 같은 환경의 현행 M1 대비 25% 초과 악화 또는 절대 5ms 초과 중 하나라도 발생하면 성능 결함**으로 중단·원인 분석. 실제 I/O·경합 측정에서도 stop 경로 p99와 최대 지연이 기준선보다 반복 악화되면 선택/배포 전에 수리한다. |
| 장후 재생/후보 | 입력 완료·직접·검열·결손 ID 수, 원시 이벤트 수, 시장별 후보 수, 전처리/후보 계산/보고서 쓰기별 wall·CPU, 최대 RSS/swap, 후보당·이벤트당 처리시간 | 후보 전수·ID 집합·비용 결과가 참조 구현과 일치하고 OOM·swap thrash·단계 시간창 초과가 0. 동일 입력에서 후보 수를 늘릴 때 반복 전처리·초선형 메모리 증가를 원인 분석한다. 예정 장후 종료시각 안에 완료되지 않으면 후보를 임의 삭제하지 않고 계산 구조와 실행 슬롯을 조정한다. |
| 정책 적용 | 선택→bootstrap→PID 소비 시간, hash 검증 실패율, 세대/시장 불일치, 원복 소요 | 무효 입력의 부분 적용 0, PID hash 오인 0, lock/CAS 우회 0. 성능 최적화가 검증·안전 분기를 생략하면 실패. |

위 5ms·25%는 **합성 모의 I/O fast 경로의 사전 회귀 한계**이며 실제 거래 지연 보증이나 수익 기준이 아니다. 과거 합성 기록의 분류 120행 p99 0.587ms, 수정 후 fast pre-arm 1,000쌍 p99 1.003ms, 두 스레드 2,000건 p99 1.356ms, 완료 80건 장후 0.824~0.957초는 [기존 구현 검토](../audit-reports/2026-09-25-scalp-trailing-mechanical-strength-implementation-review.md)와 [재검토](../audit-reports/2026-09-25-scalp-trailing-full-uncommitted-rereview.md)의 **환경이 다른 참고값**이다. 각 값을 서로 직접 비교하거나 현재 구현의 합격 영수증으로 쓰지 않는다. 후보 수가 늘어난 장후 전체 시간에는 구 4축의 source-gap 80건 실행을 기준선으로 삼지 않고 같은 신 M1 후보 격자의 참조 계산 및 허용 장후 슬롯과 비교한다.

## 6. 구현 순서와 검증 완료 조건

1. **기준선 대사:** 선택 릴리스, 작업트리, Plan Rebase의 프리마켓·시작값·구 정책을 대조한다. 현재 날짜 9/25 checklist가 없으므로 구현 시점의 실제 KST checklist OPEN owner를 먼저 확인한다. 이전 시각 보고서가 당일 최신 장후 자료로 오인되는 경로와 실행 순서를 문서화한다.
2. **원천·수학 계약:** 완료 census의 BUY→SELL·잔량0·`COMPLETED`·비용 대사, 0B/0D 원시창/시퀀스, 후보별 재계산, 검열·경쟁 청산을 수리한다. 원시 이벤트를 잃은 구세대는 직접 M1 효과에 승격하지 않는다.
3. **시장별 pure classifier v2:** 현행 0/1000ms/2회 config와 v1의 event-time 결과가 일치하는 회귀를 만든 뒤 여덟 축을 typed config로 이동한다. 같은 quote/position/route/market·fast/normal 결과가 동일해야 한다.
4. **장후 재생·후보:** 3시장 단일축 → 봉인 소수 복합축 → 전체 포지션 공통분모 → 독립 날짜 holdout/보수 비용 경계 순으로 계산한다. 시장별 상태전환 사례, 검열 비율, 수익축과의 상호작용, 후보 0 이유를 보고한다.
5. **publisher·bootstrap·PID:** 동일 owner v2 선택기와 정확 날짜 보고서 hash, rollback/lock/CAS를 연결한다. stale noon 파일, 잘못된 market, 미완료 비용, 구 AI 정책, 부모 hash 충돌, 이중 canary, 깨진 정책 파일은 적용되지 않아야 한다.
6. **장후 wrapper·소비자:** 청산 전용 report 생성, publisher, approval summary, strict handoff/finalizer의 동일 세대·종료 상태를 연결한다. 자동화 변경과 동시에 소유 운영 문서와 현재 checklist를 갱신한다. report-only 변형은 `runtime_selected=false`로 끝까지 유지한다.
7. **반복 리뷰·결과·성능:** §5의 봉인 fixture·독립 참조식·동일환경 기준선으로 단일축과 복합축을 검증한다. 최초 실패를 보존해 수리·재검토한 뒤 affected pytest/compile, wrapper `bash -n`·계약 테스트, `git diff --check`, 문서 print-only parser를 수행한다. 성능 때문에 불리한 후보나 적격 ID를 버리거나 hard safety를 우회하지 않는다.
8. **배포 후 관측:** 별도 배포 승인 아래 불변 릴리스·선택기·정확 날짜 PREOPEN·실제 PID 영수증을 대사한다. 첫 자연 장후에서 적용 시장의 상태전환·TP/경쟁 청산·원천 결손·비용 후 결과를 기존 정책과 구분해 R6에 기록한다. 후보가 없어도 원천/계산 상태를 매일 산출해 다음 완료 건을 누적 반영한다.

완료 판정은 **(a) §5의 독립 정답과 live/replay 상태·첫 신호·분모·비용 일치 및 성능 게이트 통과, (b) 독립 검증을 통과한 시장별 후보만 하나의 선택 영수증으로 다음 PREOPEN에 도달, (c) PID가 선택 hash를 소비, (d) 자연 완료 이후 비용 후 귀속과 안전 원복 영수증이 분리 기록**되는 것이다. (a)~(c)의 코드 검증이 끝나도 (d)의 자연 경제성은 별도 사후 수용이다.

참고: [호가 이벤트와 OFI의 원 연구](https://arxiv.org/abs/1011.6402)는 OFI가 단기 가격변화와 관련될 수 있다는 근거다. 이 연구가 KRX/NXT의 위 숫자 격자나 수익성을 검증한 것으로 해석하지 않는다.
