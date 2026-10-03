# 기계 정책 확인 경로 후보 연구 결과 — 2026-10-03

## 1. 결정

**실제 판정이 바뀌는 연구 후보1개를 찾았다. 정식 정책 선정은0이다.**

기존 threshold 탐색과 달리, `DEPTH_SUPPORTED` 유형에서 현재의 유효한 양의 매수 흐름·가격 반응으로 두 가지 setup 확인 부족을 대체하는 가설을 구현했다. 학습과 후단에서 각각 삼성전자1시도가 `RECHECK → ENTER_NOW`로 바뀌었고, 두 시도 모두 비용 결합 `net_target_first`였다. 원래 성공 진입은100% 보존했다.

이 결과는 **미등록 의미 규칙의 오프라인 연구**다. 10/2는 반복 사용한 후단 날짜이고, 후보 정의 확장 자체도 첫 실행을 보고 정한 사후 탐색이다. 실제 진입·체결·실현 수익, 독립 검증, live 정책 채택을 입증하지 않는다. 보조 AI는 [생산자·소비자 개선 계획](../proposals/auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md)만 작성했다. 배포 대기를 유지한다.

## 2. 원천·목적함수

- [연구계획](../proposals/main-machine-confirmation-candidate-research-plan-2026-10-03.md), 소유자 `MachineConfirmationCandidateResearch1003`.
- retained native99시도: 9/29 51, 9/30 20, 10/2 28. 기존 split의 학습71시도/59기회, 후단28시도/10기회를 유지했다. 7,069개 관측을 native 기회로 확대하지 않았다.
- 기계 parent SHA: `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`.
- `native-snapshots.json`의 content seal·parent·날짜/scope·비용 경로를 검증하고, 실제 parent kernel을 다시 실행해 incumbent action을 설정했다. source/reference/code SHA는 전후 확인했다.
- 현재 shared `machine_admission_rank`와 `promotion_errors`를 사용했다. 회수 기회의 비용 결합 target-first 승률·지원수·기존 성공 보존이 선정 기준이다. 고정10분 CF 평균으로 정책 후보를 탈락시키지 않았다. 전체 경로 순 EV는 별도 표시한다.
- 판정 입력은 당시 raw capture뿐이다. 기존 fact를 지우거나 READY로 덮어쓰지 않았다. 모델/provider 호출, 주문, canonical policy 쓰기는0이다.

## 3. 실행과 후보

| 단계 | 가설 수 | 실제 학습 행동 vector | 결과 |
|---|---:|---:|---|
| `run-01`: parent strategy 후 기존 group-trigger 결합 | 102 | 1 | 행동 변화0 |
| `run-02`: setup 대체 확인 규칙 추가 | 204 | 2 | 회수 성공을 가진 정의7개, 모두 같은 학습 행동 |
| `run-final`: 동일 성능이면 더 단순한 조건 우선으로 리뷰 보완 | 204 | 2 | 불필요한 LOW 변동성 조건 제거, 대표 후보1개 유지 |

단계별 결과와 그때의 코드는 별도 보존했다. run-01의102개가 run-final의102개 기존 recipe에 대응하므로 이를306개의 독립 아이디어로 합산하지 않는다. 유형 분기는 학습에서 관측된 family/phase/liquidity/volatility 단일·2축 조건으로만 만들고 outcome과 종목 ID를 사용하지 않았다.

최종 ID `82757208f7072742`:

1. scope는 `KRX|KRX_REGULAR`, 관측 family는 `DEPTH_SUPPORTED`.
2. parent의 `MICRO_PRICE_RESPONSE_RECHECK`/`TRIGGER_CONFIRMATION_RECHECK` 대기만 대상이다.
3. 실제 micro source가 유효하고, 순매수 delta와 가격 반응이 parent 임계값을 충족해야 한다. 원래 parent의 숫자 임계값은 바꾸지 않았다.
4. 기존 group-trigger의 trigger/volume 확인 외에 `micro_continuation_unconfirmed`, `no_supported_setup`이라는 **soft setup 확인**을 위 family+micro 증거로 대체하는 가설이다.
5. parent BLOCK·기존 ENTER·local breakout 대기·liquidity 위험·source guard·추가 micro recipe·VWAP veto를 보존한다. 다른 미해결 risk가 있으면 진입으로 바꾸지 않는다.
6. `research_confirmation_overlay`는 운영 validator가 허용하지 않는 연구 전용 필드다. live 코드·schema·승격 gate를 변경하지 않았다.

### 실제 변경2건

| 구분 | 날짜·종목 | 해소를 가정한 확인 항목 | 원래→연구 판정 | 경로 결과 |
|---|---|---|---|---|
| 학습 | 9/30 005930 | `micro_continuation_unconfirmed` | RECHECK→ENTER_NOW | 비용 결합 목표 먼저, 경로 순수익률 +0.1% |
| 후단 | 10/2 005930 | `no_supported_setup` | RECHECK→ENTER_NOW | 비용 결합 목표 먼저, 경로 순수익률 +0.1% |

이 +0.1%는 정식 machine path label의 비용 차감 목표 도달값이다. 실제 주문의 실현 수익률이나 종가 수익률이 아니다. 원본 trace/native opportunity, 대체한 soft fact와 적용 임계값은 `run-final/result.json.changed`에 보존했다.

## 4. 동일 기회 비교

| 지표 | 학습 기존 | 학습 후보 | 후단 기존 | 후단 후보 |
|---|---:|---:|---:|---:|
| 선택 기회/시도 | 17/17 | 18/18 | 1/1 | 2/2 |
| 비용 결합 목표-first 승률 | 82.3529% | 83.3333% | 100% | 100% |
| 지원수 보정 점수 | 63.1033 | 64.8196 | 26.9866 | 42.5031 |
| 추가 회수 기회 | — | 1 | — | 1 |
| 회수 기회 승률 | — | 100% | — | 100% |
| 기존 성공 보존 | — | 100% | — | 100% |
| 전체 선택 경로 평균 순 EV | −0.088447% | −0.077978% | +0.1% | +0.1% |

지원수 보정 점수는 현행 ranking penalty이며 통계적 신뢰구간 보장으로 해석하지 않는다. 학습의 전체 경로 EV는 개선되어도 여전히 음수다. 높은 목표 도달률만으로 지속 수익성을 입증하지 못한다.

공통 전체 기회에 대한 paired admission delta는 학습 `+0.000141243%p`, 후단 `+0.000526316%p`다. 같은 기회 안의 여러 관측을 평균하므로 한 시도의 +0.1%를 기회 전체·기간 전체 이익으로 확대하지 않는다.

### 실제 선정 불가 원인

shared gate의 최종 오류는 정확히 다음3개다.

- `mechanistic_entry_threshold_policy_fields_invalid`: 새 확인 규칙이 등록된 runtime schema/kernel이 아니다.
- `holdout_machine_support_insufficient`: 후단 변경 기회1, 요구3에 미달.
- `holdout_machine_recovery_support_insufficient`: 후단 회수 기회1, 요구3에 미달.

그 외에도 이번 실행은 이미 사용한 후단 날짜를 다시 보았으므로 독립 확인을 주장할 수 없다. gate의 hash/수치 검사가 과거 연구에서 해당 날짜를 얼마나 봤는지까지 보증하지 않으므로, 결과에 `pristine_holdout=false`, `live_promotion_forbidden=true`를 강제했다.

### 민감도

- 학습30종목 중 하나씩 제외하고 조건부터 다시 생성해 재선정했다. 29종목 제외 때는 같은 후보지만 **삼성전자 제외 때 후보가 사라진다**. 이를29/30의 강건성 성공으로 해석하지 않는다.
- 9/29만 학습해 9/30을 진단하는 순차 fold에서는 후보0이다. 전체 학습에서 나온1건을 더 이른 날짜부터 찾았다고 주장할 수 없다.
- 타입 정의7개가 같은 행동 vector를 낸 것이며, 독립적인7개 수익 패턴을 발견한 것이 아니다.

## 5. 무엇이 여전히 막고 있는가

native 전체99 중 parent 행동은 ENTER18, RECHECK66, BLOCK15다. non-entry81의 표시 사유는 micro-price46, local-breakout15, hard/source14, trigger5, VWAP1이다.

이 가운데 실제로 유효한 양의 micro 가격·순매수 흐름이 있는 RECHECK는10개다. 이10개에는 local-breakout3개가 있고, 그 밖의5개에는 liquidity 위험이 남으며, 나머지2개가 이번 setup 대체 가설의 대상이다. unresolved fact별로 집계한 liquidity6에는 local-breakout과 중복인1개가 포함된다.

따라서 `MICRO_PRICE_RESPONSE_RECHECK`라는 요약 문구만으로 가격 반응이 없었다고 단정하면 안 된다. 원래 표시 사유와 남은 risk fact를 함께 봐야 한다. 이번 연구는 유동성 위험을 해제하거나 돌파 재확인을 건너뛰어 후보 수를 늘리지 않았다.

## 6. 등록된 VWAP successor도 재계산

`build_winrate_policy_report`를 동일 native99행에 직접 호출해 `registered-vwap-report.json`으로 저장했다. full-source census를 다시 실행한 결과가 아니라 **고정된 native subset의 후보 gate 재현**이다. 적격99행, threshold 후보9개, 정식 후보0·기존 정책 승계다.

- 학습의 parent ENTER는17기회라 필터만으로 successor 최저30기회를 채울 수 없다.
- 예를 들어44.71bp 조건은 학습11기회 전부 목표-first, 보정80.2595로 개선되지만 기존 승자14개 중11개만 보존한다. 78.57%로 요구80%보다 낮고, 30기회에도 미달한다.
- 54.95bp 조건은14기회/승자12개로 승자 보존은85.71%지만, 보정64.7063은 baseline63.1033 대비+1.6030점이라 요구+5점에 미달한다.
- 후단 parent ENTER는1기회이고 승률100%다. 현행 veto successor의 raw 승률 엄격 개선 조건을 이 표본에서 달성할 수 없으며 선택10기회 조건도 불가능하다.
- `successor_holdout_date_coverage_insufficient`는 학습 적격 후보0으로 후보의 후단 날짜 목록이 비면서 함께 나온 파생 오류다. 과거3학습/2후단 날짜 규칙이 이번에 다시 적용됐다는 뜻은 아니다.

현재 자료에서 **진입 후보를 늘리는 setup 확인 연구**와 **기존 진입을 줄이는 VWAP veto 연구**의 가능성이 다르다. 본 결과는 상승 패턴이 없다는 결론이 아니다.

## 7. 리뷰·수정 및 검증

- 위치 gate: 새 연구 모듈은 `src/engine/scalping/entry_policy_confirmation_research.py`, 시험은 기존 `src/tests`다. engine root·live caller·자동화 등록을 추가하지 않았다.
- 첫 리뷰에서 hierarchy rule의 scalar threshold 필드 집합을 기존 validator 계약에 맞춰 수정했다. parent leaf의 값은 그대로 유지한다.
- VWAP veto fixture의 raw SHA 결속을 보완했다. 잘못된 raw provenance로 veto를 통과시키지 않는다.
- 확장 recipe의 허용 범위를 명시적인 soft fact와 RECHECKABLE disposition으로 제한했다. 유동성/미상 risk/BLOCKING은 제외하며 입력 fact는 불변이다.
- 동점 후보의 hash 순서가 불필요한 LOW 변동성 조건을 선택하는 점을 발견하고, 현행 ranking의 complexity 항목에 조건 수를 연결했다. 결과행동은 동일하며 더 단순한 flow-family 후보로 고정했다.
- **241 tests PASS**: 신규 연구 + 기존 hypothesis/strategy/group kernel 회귀. compile 및 diff PASS. 보조 AI 계획의 링크·owner·권한 경계를 검토했다. 문서 parser와 기존 작업본/정책 hash 검증 결과는 `review-receipt.json`에 기록한다.
- 최종 격리 계산25.58초, peak RSS208,644KiB(약203.75MiB). run-01 16.94초, run-02 25.72초. 같은 입력이나 서로 다른 연구 코드 단계이며 전체 장후 실행 성능 개선을 입증하는 benchmark는 아니다.
- 현재 연구 소스 SHA `222bba8ca4ceb6c8b45987b1c18c3861075300a1ae7dc1493db285d141a35542`; 최종 실행의 kernel manifest와 `reviewed-source.py`가 결속된다.
- 범위 밖 미실행: 새 provider/broker 데이터 호출, 보조 AI 추가 구현·regeneration, canonical 장후 재생성, 정책 발행/commit/배포/재기동, 실제 수익 검증. 10/6 자연 owner는 그대로 OPEN이다.

## 8. 산출물과 다음 판단

- 최종 결과: `tmp/machine-confirmation-candidate-research-20261003/run-final/result.json`.
- 후보/학습 동결: `frozen-candidates.json`, `frozen-selection.json`, `selected-candidate.json`.
- 근거: `nonentry-fact-diagnostics.json`, `registered-vwap-report.json`, source/kernel manifest.
- 재현: `.venv/bin/python -m src.engine.scalping.entry_policy_confirmation_research --extend-setup-confirmation --output tmp/<새로운-연구-디렉터리>` (`PYTHONPATH=.`). 기존 frozen 결과 덮어쓰기는 거부한다. source/reference/parent가 바뀌면 같은 실행으로 간주하지 않는다.

다음 기계 연구에서는 이 후보를 기준으로 **같은 보유 원천의 native 연결·유동성 적격성 안에서 다른 종목에도 대체 확인 근거가 성립하는지** 확인하는 것이 우선이다. 현재10개의 양의 micro 사례 중 나머지를 hard/liquidity/local guard 해제로 채우지 않는다. 현 보유 적격 자료 안에서 추가 지지가 없으면 여기까지를 가설의 한계로 남긴다. schema만 등록해 운영 후보를 만들거나 기준을 낮춰 통과시키지 않는다.

보조 AI는 별도 계획의 A0 분모 ledger → A1 lossless identity capsule → A2 조건부 plan/stop → A3 stage/operating 분리 → A4 작은 판단 가설 → A5 격리 재생성 순으로 진행하도록 구체화했다. 지금 실행한 것은 기계 후보 연구와 보조 AI 계획 수립이다.

## 9. 후속 질문: 삼성전자 전용 정책 가능성

사용자가 삼성전자 상시 감시와 별도 정책 가능성을 물어 설정·selector·native 분모를 추가 확인했다.

- `src/run_bot.sh`는 `KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED` 기본값을true로 설정하고 명시적false rollback을 보존한다. `main_fixed_watch`는 지원 세션에 scanner와 독립적인 삼성전자 Main watch를 배치하되 계정/owner flat 및 정원·route 조건을 지킨다. 기존 삼성전자 독립 매매 gateway 복구를 뜻하지 않는다.
- 10/3 프로세스 조회에서는 Main 매매 Python PID는 보이지 않았고 삼성전자 widget advisory collector PID2729721은 실행 중이었다. 설정상 상시 감시와 현재 Main PID 동작은 별도다. 연구에는9/30·10/2의 실제 `MAIN_FIXED_WATCH` 원천이 있다.
- native99행 중 삼성전자는35시도/6기회다. 9/29 일반 원천4시도/4기회, 9/30 fixed watch12시도/1기회, 10/2 fixed watch19시도/1기회다. 현재 기회 계약이 admission/generation 단위이므로 fixed watch의31시도를31개의 독립 기회로 볼 수 없다.
- **삼성전자 전용 정책을 설계하는 것은 가능하다.** 제안 범위는 `005930 + MAIN_FIXED_WATCH + exact venue/session`의 Main 하위 기계 정책이다. 공통 owner·주문/수량/holding/exit와 hard safety는 유지하고 대상 외·미확정 입력은 parent를 상속한다.
- 현재 raw strategy selector는 수치 feature 분기만 지원하고 live bundle은 venue/session별 정책을 선택한다. 종목/감시 origin별 새 selector, parent 결속, 장후 분모, publisher/loader 검증이 필요하며 설정값 하나로 이미 지원되는 기능이라고 볼 수 없다. legacy hierarchy의 symbol residual은 현재 strategy와 함께 사용할 수 없다.
- 범용 후보의 삼성전자 의존성은 확인된 한계다. **삼성전자를 명시적으로 목표로 정한 연구에서는 날짜·시간대·독립 setup episode의 반복성으로 검증 설계를 바꿀 수 있다.** 두 성공 사례만으로 채택할 수는 없다. 기존 저장 원천에서 episode 전이를 연구하더라도 synthetic native ID를 만들어 현재 승격 지원수를 늘리지 않는다.
- 본 질문에 따라 live selector/정책을 변경하거나 별도 삼성전자 주문 owner를 만들지는 않았다.
