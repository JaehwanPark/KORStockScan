# Main 제출 공백 우선순위 재검토·상세 보완계획 — 2026-10-06

## 1. 결정과 범위

**우선순위는 삼성전자의 평가 진입 복구 → 비삼성의 기계 통과 근거 전달 일치 → 중복 전략 차단 정리 → BLOCK/RECHECK 회수 조건 비교다.** 장후 데이터 보완·누적 비교 준비는 앞의 수리와 함께 진행할 수 있다. 데이터 완전 복구, 과거 제출 성공 보존, 새 정책의 경제성 입증을 평가 경로 수리의 선행 조건으로 삼지 않는다.

사용자의 제로베이스 검토·누적 승률 우선 지시를 이번 제안의 기준으로 삼는다. 기존 Plan Rebase의 정책 채택 문턱을 그대로 복제하지 않는다. 다만 입력의 실제 시각·종목·거래 경로, 계좌·주문·수량·custody·수동 veto·hard/protect/emergency는 전략 조건과 구분한다. 결손을 정상으로 바꾸는 방법으로 진입을 늘리지 않는다.

계획 수립 당시에는 코드·런타임을 변경하지 않았다. 이후 사용자가 구현·반복 리뷰·배포·재기동을 명시 승인했다. P0의 평가·근거 계약 수리와 P1의 A/B/C/D/E 비교·기존 장후 소비 연결을 구현했으며, 비교에서 우위가 입증되지 않은 추가 완화는 운영에 선택하지 않는다. [실행·리뷰 증거](../audits/main-submit-drought-remediation-execution-review-2026-10-06.md)를 현재 실행 결과로 읽는다. 다른 작업의 dirty 파일은 보존한다.

## 2. 판단에 사용한 동결 증거

분석 cutoff는 **2026-10-06 16:42 KST**, 선행 조사에서 제출 0의 요약 확인은 **16:55 KST**다. 이후 장중/장후 전체를 다시 조사했다는 뜻은 아니다.

- [동결 조사 결과](../../tmp/submit-drought-review-20261006-1642/review_result.json), [ENTER_NOW 후단 12건](../../tmp/submit-drought-review-20261006-1642/enter_now_downstream.csv), [미진입 상승 사례](../../tmp/submit-drought-review-20261006-1642/missed_examples.json).
- 당시 실제 소비 release: `postclose-finalization-handoff-20261006-eeccb1f4`, commit `eeccb1f4127a39d7454c8bb464f1018cb4365812`, PID `60572`. 이 receipt는 당시 소비 증거다. 구현 시작 때 selector와 실제 PID를 다시 고정한다.
- 추가 검토 시 `entry_setup_evidence.py`, `ai_engine_openai.py`는 위 release와 작업본의 전체 파일 SHA가 같았다. `sniper_state_handlers.py`는 작업본이 달라 **선택 release의 해당 분기**도 직접 대조했다. 작업본 전체를 운영 코드라고 간주하지 않는다.
- tmp 원천은 임시 재현 자료다. 구현 착수 시 사용한 행·파일 hash·offset·kernel/policy hash를 변경별 evidence manifest에 동결한다. 이 문서의 핵심 수치는 아래에도 남긴다.

| 단계 | 삼성전자 | 그 외 종목 | 해석 |
| --- | --- | --- | --- |
| discovery 기계 관측 | WATCHING과 별도 분모 | 2,510건/524종목: ENTER_NOW 74, RECHECK 1,730, BLOCK 614, 원천 무효 92 | 반복 관측이며 WATCHING 진입 성공률의 분모가 아님 |
| WATCHING 기계 캡처 | 106건: RECHECK 49, BLOCK 11, 원천 무효 46, ENTER_NOW 0 | 70건: ENTER_NOW 12, RECHECK 39, BLOCK 16, 원천 무효 3 | 비삼성에는 별도로 provider `insufficient_core_data` 24건이 있음 |
| 평가 지속성 | 마지막 기계 평가 11:30:19 | 통과 12건을 exact hash로 후단 연결 | 삼성 오후의 무평가와 오전 전략 미통과는 서로 다른 문제 |
| 보조 판정 이후 | 실제 보조 provider 호출 0 | CAUTION 7, 오전 hash 거부 3, 잘못된 PASS 응답 1, remote guard 1 | 12건 모두 최종 WAIT. 이 12건의 probe intent도 false |
| 제출 경로 | 실제 제출 0 | 실제 제출 0 | 선행 동결 자료에서 budget/latency 실행 단계 도달도 0. 제출 전 병목을 우선 수리 |

### 2.1 삼성: 호출 앞단의 가격 게이트

선택 release의 WATCHING 분기는 `get_smart_target_price(..., ai_score=75.0)`가 돌려준 가격에 대해 `curr_price <= target_buy_price * 1.015`일 때만 분석 호출을 허용한다. 약한 체결강도와 매수 잔량 우세가 함께 있으면 목표가가 9틱 낮아질 수 있다. 예를 들어 11:33:47 현재가 273,000원, VPW 96.9, 매수/매도 잔량 비율 1.696에서 목표가 상한 268,500원, 허용 상한 272,527.5원이 되어 평가를 열지 못했다.

가격 관측 지연 0.5초 이하·호가 지연 3초 이하로 결속한 3,232개 관측 중 3,225개가 이 조건을 만족하지 못했다. 연결하지 못한 2,342개는 제외했다. 반복 관측 수를 독립 미진입 기회 수로 세지 않는다. 이 재현은 강한 앞단 병목 증거이며, 가격 게이트 해제 후 실제 BUY가 발생했을 것이라는 증거는 아니다.

`blocked_strength_momentum` 14,352건 중 7,488건은 `risk_context_only`, `blocked_vpw` 6,984건도 모두 `risk_context_only`였다. 로그 이름만으로 모두 제거할 차단 조건이라고 해석하지 않는다. 기본 score 50 역시 실제 AI의 75점 미달 판정과 구분한다.

### 2.2 비삼성: 등록 기계 규칙과 보조 AI의 확인 기준 불일치

12건 중 11건은 `MAIN_ENTRY_PULLBACK_BUY_FLOW_PASS`, `admission_recipe_trigger_pass=true`, `group_trigger_pass=false`였다. 오전 hash 거부 3건을 제외한 오후 8건도 이 경로다.

- CAUTION 7건 중 삼성전기·LG이노텍·티엠씨·LG전자·LG에너지솔루션·케이씨에스 6건은 `NO_VALID_SETUP / UNCONFIRMED`, 엘앤에프는 `PULLBACK_RECOVERY / WAIT_CONFIRMATION`이었다. 모두 `CONFIRMATION_MISSING`을 인용했고, 티엠씨는 `ADVERSE_TAPE`도 있었다.
- 한국콜마는 같은 등록 기계 규칙을 통과했지만 `WAIT_CONFIRMATION` 상태에서 `PASS + CONFIRMATION_MISSING` 응답을 반환했다. risk code와 PASS의 모순까지 있어 단순 인용 보완으로 통과시킬 수 없다.
- 현재 `validate_mechanistic_risk_screen()`은 일부 `group_trigger_pass`의 PASS에 legacy 확인 조건 예외를 두지만, 같은 위치에서 `admission_recipe_trigger_pass`는 다루지 않는다. 등록 규칙의 실제 통과 근거가 AI 입력·인용 가능한 사실·validator에 일관되게 연결되는지 먼저 수리해야 한다.
- 이 결과만으로 CAUTION 전부가 오판이라고 단정하지 않는다. 원래 규칙보다 확인을 더 요구하는 **정책 선택**과, 선택한 규칙의 증거를 소비자가 표현하지 못하는 **계약 결함**을 나누어 변경한다.

삼천당제약 1건은 정상 setup의 기계 ENTER_NOW와 AI PASS 후 `remote_buy_guard(risk=2)`로 WAIT가 됐다. 중복 전략 판정 후보로 따로 다룬다.

## 3. 재정렬한 우선순위

| 순위 | 작업 | 먼저 하는 이유 | 완료 산출물 |
| --- | --- | --- | --- |
| P0-A | WATCHING 평가를 목표 매수가 도달 조건에서 분리 | 삼성은 오후에 판단 자체가 거의 없어서 후단 임계값 완화 효과를 볼 수 없음 | 가격 게이트 재현·수정 differential, 유효 원천에서 새 기계 평가 receipt |
| P0-B | 등록 기계 규칙 → AI 사실 → 검증기 → 정상 제출/기존 probe 경로를 연결 | 비삼성 통과 12건 중 11건이 이 규칙. 표현 불일치를 둔 채 CAUTION만 완화하면 결함을 감춤 | exact 12건의 계약 재생, recipe/group/legacy 경로별 통합 회귀 |
| P1-A | 확인 부족만 있는 CAUTION의 제한적 해제, remote guard 중복 제거 비교 | P0 이후에도 남을 수 있는 직접 후단 차단 | 원응답 보존·effective 판정 비교, 최종 guard까지의 오프라인 경로 증거 |
| P1-B | RECHECK 조기 회수와 일시적 전략 BLOCK 재평가 | 실제 후속 상승 사례를 진입 가능한 후보로 연구해야 함 | 삼성/비삼성별 전수 후보·독립 기회·누적 승률 비교 |
| P1-C | 외부 가격 보완·유효 행 장후 누적 비교 | 전체 source-gap 때문에 연구가 매번 멈추는 문제 해소 | 포함/제외 원장, 동일 라벨의 누적 비교와 다음날 발행 연결 |
| P2 | 추가 freshness/AI 점수/watch cap/수량·청산 변경 | 현재 첫 병목이라는 증거가 약하고 동시 변경 시 효과를 분리하기 어려움 | P0/P1 후 새 도달 증거가 생긴 항목만 별도 구체화 |

P0-A와 P0-B는 서로 완료를 기다릴 필요가 없다. P1-C의 자료 준비도 즉시 가능하다. P1-B의 정책 비교는 P0 수리 후 기준선을 사용한다. 순서를 이유로 데이터 준비나 삼성·비삼성 한쪽의 수리를 불필요하게 대기시키지 않는다.

**앞선 완화 제안의 보정:** freshness 3초→5초, AI score 일괄 하향, CAUTION 전면 PASS는 첫 조치에서 내린다. 15:13 배포 후 짧은 자연 창에서는 삼성·두산 3초 초과가 관측되지 않았고, 오후 삼성의 별도 평가 게이트가 확인됐다. 오전 hash 3건도 이미 [수리·배포된 결함](../audits/main-machine-source-refresh-and-admission-hash-remediation-2026-10-06.md)이므로 재발 증거 없이 재구현하지 않는다.

## 4. P0 상세: 판단이 실행되고 다음 소비자에 도달하게 한다

### P0-A — 평가 허용과 주문 가격 허용 분리

1. [WATCHING 처리기](../../src/engine/sniper_state_handlers.py)의 `is_vip_target`이 막는 분석·재분석 분기를 모두 조사한다. 첫 평가, 정상 cooldown 만료, 새 원천 재계산, 비동기 완료 소비가 같은 의미를 갖게 한다.
2. 유효한 원천·활성 Main 감시·평가 시점이 충족되면 **현재가가 목표가의 1.015배를 넘더라도 기계 평가를 허용**한다. `get_smart_target_price`의 가격 산식은 이 작업에서 고치지 않는다. 가격·추격·호가·주문 적정성은 해당 제출 소비자에서 판단한다.
3. 기존 machine-first 경로를 유지해 BLOCK/RECHECK는 보조 AI 전에 종료한다. 평가 허용이 매 tick provider 호출이나 주문 재시도를 뜻하지 않도록 in-flight 중복 방지, 정상 provider cooldown, 기존 예산을 유지한다. 평가를 반복해서 건너뛸 경우 원인을 한 attempt에 귀속한다.
4. 삼성만 우회하는 하드코딩을 만들지 않는다. 현재 등록 fixed-watch와 일반 Main WATCHING에 공통 의미를 적용하되, 퇴역 owner·잘못된 admission/generation·비활성 감시는 열지 않는다.
5. 기존 [원천 수리](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md)의 재계산·source clock을 재사용한다. snapshot age를 새 시각으로 바꾸거나 오래된 원천을 가격 게이트 수정으로 유효화하지 않는다.

**기술 완료:** 273,000/268,500 재현에서 기존에는 호출되지 않던 기계 평가가 허용되고, 동일 입력의 기계 결과는 평가 함수의 결과 그대로다. stale/conflict·cooldown·중복 작업·퇴역 owner 회귀가 통과한다. 유효 BLOCK/RECHECK fixture에서 provider 0·주문 0을 확인한다.

**자연 수용:** 운영 반영이 별도로 실행되면 같은 release/PID에서 유효 원천→새 기계 캡처를 연결한다. 유효 평가 기회가 없으면 `not_observed`로 끝낸다. BUY·실제 제출·양의 수익을 코드 수리 완료 조건으로 추가하지 않는다. 평가 허용 확대는 실행 동작 변경이므로 단순 로그 수정이라고 보고하지 않는다.

### P0-B — 등록 규칙의 통과 근거와 AI 계약 일치

생산·소비 owner는 [entry_setup_evidence.py](../../src/engine/scalping/entry_setup_evidence.py), [entry_strategy_policy.py](../../src/engine/scalping/entry_strategy_policy.py), [ai_engine_openai.py](../../src/engine/ai_engine_openai.py), WATCHING 최종 소비자다.

1. 12건의 원본 hash·원규칙·원setup·원응답을 동결한다. 오전 hash 3건, 오후 CAUTION 7건, invalid PASS 1건, remote guard 1건을 각각 재생한다. 미래 가격으로 과거 판정을 수정하지 않는다.
2. 등록 recipe의 ID·version·policy SHA·원천 SHA·선택 이유·실제 통과한 수치/사실을 AI의 별도 machine decision 근거로 전달한다. 원래 `NO_VALID_SETUP`을 `READY`로 위조하지 않는다. legacy family의 확인 상태와 선택 recipe의 확인 상태를 함께 표현한다.
3. schema·동적 fact enum·영문 ASCII prompt·validator·trace가 같은 근거를 읽게 한다. 기존 machine group 예외를 무조건 복사하지 말고, recipe에서 실제 검증한 사실만 인용 가능하게 한다. 다른 policy/hash/route의 통과 사실, 미래 자료, 손상된 응답은 거부한다.
4. recipe가 요구하지 않는 legacy 확인 부족만으로 자동 거부하는 규칙을 정리한다. 실제 recipe 필수 조건 미충족이나 fresh adverse evidence가 있으면 여전히 거부한다. 한국콜마의 `PASS + CONFIRMATION_MISSING` 같은 모순 응답을 자동 PASS로 고치는 규칙은 넣지 않는다.
5. `compose_mechanistic_primary_decision`의 group/recipe PASS는 내부적으로 `WAIT + entry_probe_intent=true`를 만들 수 있다. adapter는 이를 `eligible_wait_probe`로 옮기고 WATCHING은 별도 소비한다. `BUY` 경로와 이 경로를 모두 실제 후단 함수까지 재생한다. 필드가 중간에 사라지거나 정상 intent가 거부되는 결함이 확인된 경우에만 수리한다.
6. 기존 수량·probe continuation·가격·budget·latency·broker 최종 guard에 도달하는지 확인한다. WAIT를 일괄 BUY로 바꾸거나 probe를 전량 진입으로 바꾸지 않는다. [별도 probe 조건부 재생 계획](entry-probe-conditional-owner-replay-remediation-plan-2026-10-06.md)의 구현을 복제하지 않는다.

**기술 완료:** legacy/group/recipe의 정상 PASS가 각자의 의도된 후단 guard에 도달하고, 모순 응답·변조 hash·잘못된 policy·필수 source 부재는 거부된다. 원래 CAUTION 7건을 무조건 성공시키는 것이 수용 기준은 아니다. 고정 응답 회귀와 실제 provider의 향후 응답을 구분한다.

## 5. P1 상세: 과감하게 완화할 전략 조건

아래는 **비교할 소수 후보**다. 새 정책 파라미터이며 현재 live 값이 아니다. 먼저 각 후보를 수리된 기준선과 비교하고, 우수 후보만 결합해 상호작용을 한 번 더 비교한다. 모든 축의 조합 grid를 만들지 않는다.

| 후보 | 완화 조건 제안 | 적용·제외 | 우선 확인할 효과 |
| --- | --- | --- | --- |
| A: 확인 중복 제거 | source/contract 유효, 현재 등록 machine recipe ENTER_NOW, AI의 유일 risk code가 `CONFIRMATION_MISSING`이며 부족하다는 사실이 legacy 확인에만 해당하면 effective screen을 PASS로 매핑 | 원 CAUTION·인용·effective 변경 이유 모두 보존. 실제 recipe 확인 부족·추가 ADVERSE_TAPE·VETO·INSUFFICIENT·invalid 응답은 제외 | CAUTION 7건 중 추가 adverse code가 없는 6건은 **검토 대상**. 6건 전부 통과를 보장하지 않음 |
| B: remote guard 중복 제거 | 검증된 machine-primary ENTER_NOW + 유효 AI PASS 경로에서는 `remote_buy_guard`의 전략 점수 재거부를 제거하고 원인만 기록 | 기존 함수가 가진 source 검증과 최종 account/order guard는 별도 보존. legacy/nonmachine 호출에는 그대로 적용 | 삼천당제약과 같은 중복 차단 해소. 제거 후 실제 제출은 후단 결과에 따름 |
| C: 삼성 조기 흡수 | source 유효, `buy_pressure_10t >= 60`, `net_aggressive_delta_10t > 0`, `same_price_buy_absorption >= 2`, `price_change_10t_pct >= 0`이면 legacy local breakout을 기다리지 않는 recipe 비교 | source-bound 체결 방향·호가와 현재 hard guard 필요. 미지원 setup 자체를 정상으로 덮지 않고 독립 recipe로 표현 | 돌파 이후 진입 지연을 줄일 수 있는지 삼성 누적 분모에서 판단 |
| D: 비삼성 초기 회복 | source 유효, `buy_pressure_10t >= 55`, `net_aggressive_delta_10t > 0`, `price_change_10t_pct >= 0`이면 평평한 가격 반응도 초기 회복으로 인정 | 과거 `liquidity_adverse`가 현재 주문 가능 호가·깊이 guard와 중복일 때만 전략 RECHECK 해제. 실제 liquidity 부족은 제외 | TCC스틸과 같은 초기 수급 회복 회수. 현행 spread·size guard 보존 |
| E: 일시적 전략 BLOCK 재평가 | 대량매도 단일 관측 등 가역적 전략 사유로 BLOCK된 후보를 영구 폐기하지 않고, **새 체결 window에서 원 BLOCK 조건 해소 + C/D 등 등록 규칙 충족** 시 새 판정 | 단순 경과시간만으로 대량매도 위험 소거 금지. source-invalid·수동 veto·custody·hard safety BLOCK 제외 | 티엠씨처럼 뒤늦게 회복한 종목의 재진입 기회 보존 |

C/D의 숫자는 연구 시작값이다. 삼성/비삼성의 서로 다른 정책으로 평가하며 한쪽 결과를 다른 쪽의 승률로 대체하지 않는다. 원천에 해당 feature가 없으면 외부 OHLC로 만들어 채우지 않고 그 후보 비교에서 행을 제외한다.

**재평가 일정 제안:** 기존 scanner loop 안에서 새 source sequence가 생길 때만 로컬 기계 재계산을 허용한다. 한 기회당 최대 30초, 최소 1초 간격·추가 계산 최대 3회로 동결 비교한다. 같은 source 반복·재실패로 기한 연장·다중 pending owner는 금지한다. 30초 이후는 통상 scanner가 새 기회를 발견하는 경로로 돌아간다. 이 수치는 기존 cooldown을 바꾸는 정책 제안이므로 P0 버그 수리와 구분한다. 보조 AI 호출은 새 ENTER_NOW와 기존 provider 예산/cooldown에 따른다. 새 daemon·REST polling은 만들지 않는다.

### 놓친 상승을 평가하는 방법

| 사례 | 관측한 사실 | 이번 계획에 주는 의미 |
| --- | --- | --- |
| TCC스틸 09:14:22 RECHECK | 당시 ask 14,160원, 이후 관측 bid 15,450원(+9.11%). 내부 가격 경로 최대 공백 약 1,507초. 외부 다음 분 시가 14,180원의 20분 시나리오는 target-first | 후속 상승은 크다. 내부 자료로 연속 체결 가능 수익을 주장하지 않는다. D 후보와 재평가 지속성을 비교 |
| 코스맥스 14:17:25 RECHECK | ask 274,000→이후 bid 280,500(+2.37%), 외부 시나리오 target-first | 원시점 buy pressure 32.5·delta -28로 D 불충족. 미래 상승만 보고 원시점 진입을 정당화하지 말고 새 회복 시점의 재평가를 비교 |
| 티엠씨 09:53:47 BLOCK | ask 18,470→이후 bid 18,890(+2.27%), 외부 시나리오 target-first | 대량매도 당시 차단과 이후 위험 해소를 분리하여 E 비교 |
| 삼성 09:14:27 RECHECK | ask 276,000→이후 bid 278,000(+0.72%). 해당 비용·손절 시나리오는 adverse-first | 상승 후일담이 승리가 아님. C는 이 사례를 회수한다는 이유만으로 채택하지 않음 |

미진입 상승 사례의 검토 우선순위는 높게 두되, **모든 BLOCK/RECHECK의 실패·무상승 사례도 같은 모집단에 포함**한다. 높은 MFE 사례만 골라 누적 승률을 만들지 않는다.

## 6. P1-C: 원천 보완과 장후 작업

### 6.1 용도별 필수 필드와 제외

| 용도 | 필수 필드 | 외부 보완 가능 | 끝내 없으면 |
| --- | --- | --- | --- |
| 단계별 차단 분석 | 종목·판정 시각·stage·원인·attempt/observation·policy/원천 hash·route/session | 종목 명칭·상장/거래일 정보 | 식별되지 않는 행은 해당 연결 분석에서 제외. 원제외 수는 유지 |
| 고정 규칙 가격 CF | 위 판정 identity, 후보 판단 당시 feature, 명시된 다음 분 진입 가격·연속 후속 OHLC·가격 조정/단위·venue/session·고정 비용/종료 규칙 | 출처가 명시된 분봉/일봉·기업행사·공식 비용표 | 미확정 진입·경로 공백·동일 봉 양방향 도달·미만기 행은 승패 분모에서 제외 |
| 실제 owner 주문 재생 | 당시 주문 가능 BBO/깊이·owner plan·stop·수량/자금·native clock·주문/취소/체결/terminal·비용 | 일반 외부 차트로 복원 불가 | 이 재생만 미지원 처리. 같은 행의 가격 연구까지 전부 폐기하지 않음 |
| 실제 승률·손익 | `COMPLETED`와 유효 `profit_rate`, 비용과 실제 execution identity | broker 원천의 정식 read-only 대조 범위가 있을 때만 | 0원/0수익/패배로 대체하지 않고 제외·미확정 수 공개 |

보완 순서는 내부 원본/캐시의 exact identity 복구 → 기존 허용된 공식/공개 외부 자료 → 독립 자료로 시각·단위·가격 대조 → 잔여 결손 행 제외다. 자동 failover 수집·추가 provider 호출 권한을 만들지 않는다. 실제 Kiwoom 요청/parser를 변경해야 할 때만 구현 전에 최신 공식 reference gate를 수행한다.

외부 파일에는 URL·조회 시각·종목·세션·시간대·원 bytes SHA·변환 규칙·원행 연결을 저장한다. 원본 파일을 덮지 않는 별도 보완 자료로 관리한다. KRX 공개 분봉을 SOR/NXT의 과거 실행 호가로 변환하지 않는다. 정확한 venue가 필요한 연구와 KRX 가격 시나리오를 별도 표로 낸다.

이미 확보한 Naver KRX 정규장 자료는 454종목·162,472분봉이다. 전체 기계 관측 2,686건 중 장외/비정규장 420건, 원천/anchor 부적합 162건, 다음 분 시가 부재 17건을 제외해 2,087개 시나리오를 만들었다. 종목별 30분 중복 억제 후 1,065개 기회 중 판정 가능 984, 제외 81(동일 봉 양방향 28·경로 결손 48·기간 미완료 5)이다. 제외 행을 실패로 세지 않고 사유별로 공개한다. 이 984개는 **당일 고정 가격 시나리오**이며 누적 실제 승률이 아니다.

### 6.2 기존 장후 생산자 안에서 할 일

1. [ai_action_outcome_calibration](../../src/engine/scalping/ai_action_outcome_calibration.py)에 당일 Main 기계 판정의 전수 identity를 연결한다. 실제 제출 이벤트가 없어도 BLOCK/RECHECK/ENTER_NOW의 가격 연구 모집단은 생성할 수 있어야 한다.
2. 삼성/비삼성, discovery/WATCHING, 정책 세대·venue/session을 유지한다. 재평가·같은 watch의 반복·child leg를 독립 승리로 늘리지 않는다. 고정 30분 억제는 가격 연구용 규칙이며 실제 owner lifecycle과 혼합하지 않는다.
3. 누락을 값 0으로 채우지 않는다. 전역 preflight·isolation이 정상이라면 식별 가능한 결손 행만 제외하고 나머지로 진행한다. 총수=포함+제외+미만기 대기의 합계를 검증하고, 후보별 유효 분모 차이를 보여준다.
4. 가격 연구는 공통으로 유효한 관측에서 후보들을 비교한다. 후보가 필요한 feature를 읽지 못한 행을 음성 판정으로 바꾸지 않는다. 추가 제외가 후보에 유리한 종목·시간에 몰리는지도 별도 표시한다.
5. [compact_auxiliary_paired_replay](../../src/engine/scalping/compact_auxiliary_paired_replay.py)는 P0의 새 근거 계약과 A/B의 원/effective 판정을 읽는다. 과거 원응답을 그대로 쓰는 결정적 비교와 새 prompt에 대한 provider 응답 추정은 구분한다. 새로운 AI 답변을 합성하여 승률을 계산하지 않는다.
6. 하루 증분 자료를 유효한 누적 자료에 합친다. cache key에 source/보완 manifest·policy/kernel·가격/비용/종료 라벨·분모 규칙을 포함한다. 이미 본 10/6 사례는 설계 자료로 표기하고 독립 미래 검증이라고 부르지 않는다. 복원 불가 과거를 같은 입력으로 반복 재생하지 않는다.
7. [submission_bottleneck_monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py)는 `평가 없음 → 기계 결과 → 보조 결과 → 정상 제출 후보/probe intent → 최종 guard → 제출 → 체결 → terminal` 연결을 기존 identity로 보여준다. taxonomy를 새로 계속 쪼개는 별도 보고서보다 한 정상 제출 경로의 단절 확인을 우선한다.
8. [postclose_summary_handoff](../../src/engine/automation/postclose_summary_handoff.py)의 기존 Main/compact 하위 결과와 strict/controller가 같은 목표일·generation·hash를 읽게 한다. 가격 연구만 완료됐으면 실제 owner 경제성 source-gap은 그대로 남긴다. 퇴역 Widget stage·collector·연구·발행을 재활성화하지 않는다.

기존 장후 보고서 전체를 설계 단계에서 재생성하지 않는다. 구현 후 영향받는 당일 stage와 한 비교 날짜의 증분 결과로 먼저 확인한다. wrapper/cron/자동화 순서 변경이 실제 필요해지면 해당 운영 문서와 실행 체크리스트를 같은 구현 범위에서 갱신한다.

## 7. 정책 채택 기준: 누적 승률 한 가지를 주목적으로

**후보 순위와 선택은 동일한 정의로 계산한 누적 승률 개선을 주기준으로 한다.** 기존 제출 성공 100%/80% 보존, 모든 날짜 승리, 모든 개별 거래 개선, 특정 과거 제출 이벤트 통과는 필수 조건에서 제외한다. 앞선 제안의 신뢰구간 하한도 새 필수 채택 게이트로 추가하지 않는다.

### 분모와 승리 정의

- 실제 ledger: `COMPLETED + valid profit_rate` 중 비용 차감 `profit_rate > 0`인 건 / 유효 완료 건. 0수익은 승리에서 제외한다. partial/full·owner·venue/session과 삼성/비삼성을 분리한다.
- 가격 CF ledger: 고정한 진입·비용·종료 규칙으로 만기 판정된 독립 기회 중 net return > 0인 건 / 유효 판정 건. 같은 source·기회 기준에서 candidate와 incumbent를 평가하되 각 정책이 선택한 거래 수·승/패/0을 함께 적는다. 미진입은 손실이나 승리로 간주하지 않는다.
- 실제 ledger와 CF ledger는 합산하지 않는다. target-first율·MFE·호가 개선율은 별도 진단이며 위 승률을 대체하지 않는다. 현재 주문 계획의 replay와 고정 20분 가격 시나리오도 서로 합치지 않는다.
- 누적은 날짜별 승률의 단순 평균이 아니라 유효 승리 합계/유효 판정 합계다. 2026-06-05 이후라도 원정책·특징·비용·종료 정의를 비교 가능하게 복원할 수 있는 범위만 사용한다. 변환할 수 없는 과거 세대는 별도 ledger로 둔다.

### 단순 선택 규칙 제안

1. **비교 가능한 누적 기준선이 있으면 `후보 누적 승률 > 기준선 누적 승률`인 후보 중 최고를 선택**한다. 동률은 기준선을 유지한다. 당일 제출 0은 누적 기준선 소멸이 아니다.
2. 비교 가능한 기준선 거래가 정말 0이면 기준선 승률을 0으로 만들지 않는다. 고정 exit·비용 모델에서 순이익 크기 G, 순손실 크기 L이 정의되는 범위에 한해 **승/패 중 승률** `W_decisive > L / (G + L)`을 대체 기준으로 제안한다. 이 예외 계산에서 0수익은 제외하며, 전체 유효 건 기준 승률과 0수익 건수를 계속 공개한다. G/L이나 승패 분모도 없으면 비교 우위 미입증으로 표시한다. 여러 종료 결과를 가진 모델은 해당 모델의 누적 평균 이익/손실을 사용하며 추정값임을 밝힌다. 임의 50%나 서로 다른 모델의 과거 70%를 가져오지 않는다.
3. 각 비교표에 유효 N·승/패/0·종목/거래일 수·분모 coverage·불확실성·평균 이익/손실·누적 net return·최대 손실을 함께 공개한다. 승률은 높지만 손실 규모가 커 순성과가 나쁜 후보임을 숨기지 않는다. 비용·hard risk는 유지하되 이 공개 지표들을 새 다중 경제성 veto로 복제하지 않는다.
4. 가설/라벨/비용/후보를 먼저 동결하고 이후 관측은 계속 누적한다. 시간순 검증의 의미는 보존하되 고정 표본 수 30/10, 의무 대기 일수, 일률적 +5pp, 의무 노출 50%를 이번 제안의 추가 필수 조건으로 복사하지 않는다. 지원수가 적으면 그 불확실성을 수치로 드러낸다.
5. 사용자 지정 **초기 정책 채택**과 평가·증거 전달 결함 수리는 이 경제성 비교를 기다리지 않는다. 초기 정책에 새 승률·EV·holdout·canary 요건을 붙이지 않는다. 일반적인 후속 정책 선택과 구분한다.

현재 [10/2 누적 보고서](../../data/report/ai_decision_action_outcome_calibration/winrate_policy_2026-10-02.json)의 `pullback_p60_v0`는 9/29·9/30·10/2 자료에서 cluster 승률 약 70.20%, 해당 모델 평균 가격 CF 약 -0.228%였다. validation 표본은 0이고 incumbent carried였다. 이를 현재 배포 정책의 누적 성과 또는 실제 수익이라고 사용하지 않는다. 이번 10/6 시나리오의 비용 0.23%+추가 slippage 0.10%, net ±0.5%, 20분 종료는 별도 임시 정의다. 정의를 먼저 통일하지 않고 기존 보고서와 합산하지 않는다.

## 8. 기존 작업과 소유 경계

| 기존 소유자/계획 | 이번 연결 | 하지 않을 중복 작업 |
| --- | --- | --- |
| `FixedWatchSourceAndCleanupRepair1006` | 이미 배포한 source 수정의 자연 판정 수용. P0-A 반영 뒤 새 trace와 연결 | snapshot 수리를 다시 구현하거나 A3 미관측을 경제성 실패로 판정 |
| `DirectFamilySourceRepairMainMechanisticEntry` | 장후 `machine_operating_population_unbound`와 P1-C의 실제 identity 연결 | 가격 CF만으로 기존 실제 owner 경제성 source-gap 완료 처리 |
| `DirectFamilySourceRepairCompactAuxiliary` | 보조 근거/응답 계약과 장후 소비 연결 | exact stop 결손을 임의 0으로 채우거나 CAUTION 전면 허용 |
| `DirectFamilySourceRepairEntrySplit` / probe 조건부 계획 | P0-B의 intent 소비 이후 기존 continuation owner에 인계 | 별도 수량·잔여 주문 모델 신규 구현 |
| `DoosanEpisodeToMainFixedWatch` | 두산의 기존 전환·다음 PREOPEN 소비를 보존 | 두산 초기 정책에 새 경제성 게이트 부과 |
| [제주 등 8종목 retirement·고정감시 3종목 계획](jeju-episode-retirement-hpsp-alteogen-main-fixed-watch-initial-policy-plan-2026-10-06.md) | 현재 문서에서 제안된 HPSP·알테오젠·주성의 공통 평가 경로 호환성 검토 | 본 계획으로 3종목을 활성화하거나 cap을 늘리기. 초기 채택에 누적 연구 완료를 요구하기 |
| `FixedWatchBudgetSummaryPostcloseAcceptance1006` | 기존 장후 companion 발행 수용 보존 | 제출 0 해소 계획으로 해당 별도 수용 작업 재구현 |

위 stable ID의 현재 실행 소유는 [10/6 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)에 있다. 이 문서는 새 실행 일정을 등록하거나 기존 OPEN의 수용 기준을 몰래 교체하지 않는다. 실제 구현 지시가 이어지면 P0의 새 코드 작업에 한 개의 실행 owner를 등록하고, P1-C의 원천 수용은 기존 Main/compact owner에 연결한다. 완료된 hash 수리는 재발 회귀만 수행한다.

## 9. 실행 묶음·검증·종료

| 묶음 | 구현 순서/산출물 | 핵심 검증 | 종료·다음 행동 |
| --- | --- | --- | --- |
| 0: 기준선 | 실제 release/PID·dirty diff·12건·삼성 가격 게이트 재현·정책/원천 manifest | 원본 불변, 구현 대상과 운영 코드 차이 확인 | 유효 재현을 확보. 결손 행은 제외 목록으로 확정하고 나머지 진행 |
| 1: P0 경로 수리 | 평가 gate 분리 + machine recipe 근거 계약 + 후단 intent 통합 | `test_main_fixed_watch`, `test_entry_setup_evidence`, `test_ai_engine_cache` 및 WATCHING 소비 회귀 | 코드·계약 결함 0으로 닫음. 수익·실제 주문 발생은 요구하지 않음 |
| 2: P1-A/B 정책 비교 | A/B부터 단독 비교, C/D/E의 제한된 후보 비교 | 원응답/새 policy 분리, BLOCK/RECHECK 승격의 정확한 원인, source/hard guard 보존 | 후보별 유효 N·누적 승률·추가/제외 기회·손익·불확실성 표. 미검증을 통과로 표현하지 않음 |
| 3: P1-C 장후 연결 | 행 단위 source 보완 + 중복 제거 + 누적 ledger + 기존 publisher/consumer | `test_ai_action_outcome_calibration`, `test_entry_setup_paired_replay_batch`, `test_submission_bottleneck_monitor`, policy consumer 회귀 | 유효행만으로 보고 가능, 제외 합계 일치, exact target date/hash 소비 |
| 4: 리뷰·운영 인계 | 변경별 self review→수정보완→재리뷰, 영향받는 표적 검사 | Python pytest/compile, diff, 문서 parser. 외부 API 변경 시 공식 계약 추가 | 별도 권한에 따른 release/정책 발행·PID 확인. 계획 수립만으로 실행하지 않음 |
| 5: 자연 수용 | 삼성/비삼성에서 평가→기계→보조→guard→제출/명시 거부 연결 | 정상 broker 호출 전까지 offline fake 실행 검증, 이후 자연 receipt | 기회 없음은 `not_observed`, 결손은 제외, 정상 미통과는 판정 결과. 실제 제출·fill·PnL은 각각 별도 기록 |

기존 패키지를 사용한다. 실시간 판단은 `src/engine/scalping` 및 기존 상태 처리기, 장후 조인은 기존 scalping producer, 모니터는 `src/engine/monitoring`, 테스트는 `src/tests`가 소유한다. 새로운 engine-root 모듈·collector·daemon·별도 장후 전체 runner는 계획하지 않는다. 새 파일이 꼭 필요하면 구현 전에 실제 producer/consumer를 확인하고 위치를 정한다.

운영 검증에서 주문이 없다는 사실만으로 다시 모든 threshold를 낮추지 않는다. 새 trace에서 **최초로 실제 진입을 차단한 단계**를 확인해 해당 변경만 후속 처리한다. 서로 다른 의미의 보조 `CAUTION`과 latency `CAUTION`은 구분한다. stale/conflict 허용, 중복 주문, 잘못된 owner/수량, 과거 BUY 재사용이 발생하면 해당 변경의 운영 반영을 중단하고 이전 정상 release/정책으로 복귀한다. 전략 성과 비교가 열세이면 해당 후보를 선택하지 않는다.

## 10. 이번 문서의 리뷰·검증

검토 과정에서 우선순위를 보완했다. CAUTION 일괄 해제보다 recipe 근거 전달을 앞세웠고, WAIT/probe intent를 제출 차단과 구분했으며, 이미 배포한 오전 hash/source 수리와 새 결함을 분리했다. 실제 승률·가격 CF·target-first의 분모 혼합, 외부 분봉의 SOR 실행 호가 대체, 초기 정책에 대한 추가 경제성 게이트를 배제했다.

리뷰 보완으로 기준선 0건일 때의 대체 승률 계산에서 0수익 분모를 명시했다. 실제 누적 승률의 분모를 이 예외 계산으로 바꾸지 않는다.

검증 완료: 로컬 링크 17개 정상, 관련 stable ID 6개가 현재 체크리스트에서 각각 OPEN 1개, `git diff --check`와 신규 파일 whitespace 검사 정상, print-only backlog parser exit 0·26개 항목. 새 제안 문서가 실행 owner로 자동 등록되지 않은 것도 확인했다. parser 출력은 `/tmp/main-submit-drought-plan-backlog-20261006.txt`에 보관했다. 문서만 추가했으므로 trading pytest·provider 호출·장후 보고서 재생성·배포 검증은 실행하지 않았다. 코드 변화 후의 자연 제출 증가와 누적 승률 개선은 아직 미검증이다.
