# 보조판정 이후 실제 제출: 전체 가드와 누적 기회·오진입 점검

점검일: 2026-10-17 KST. 범위: Main 최초 진입의 AI 결과 수신부터 첫 실제 HTTP 주문, 응답·분할 의도 정리까지. 읽기 전용 감사이며 코드 수리·정책 변경·배포·재기동을 수행하지 않았다.

## 1. 판정

**중복 약세 차단과 상시감시 증빙 연결은 최신 선택 코드에서 보완됐지만, 전체 경로가 정상이라고 결론낼 수 없다.** 실제 미전송 뒤 주문 의도와 PASS 소비 상태가 남는 결함을 재현했다. 보조판정에는 실패를 표현할 수 없는 입력·응답 계약 사례가 있고, 연구의 승리 회복이 실패 차단 개선을 의미하지도 않는다. 누적 원천 결손 때문에 모든 가드의 오차단률·오진입 방지율을 확정할 수 없다.

- 코드 기준: 최초 점검 `auxiliary-next-session-20261017-2fa874239`, 후속 selector 재확인 `auxiliary-next-session-20261017-57d4d4664` / `57d4d4664c6ce766bf0e949e6f91a4a1c0618dc7`, 선택 시각 15:01:30 KST. 두 선택 모두 `actual_pid_consumed=false`, 다음 운영일 10/19다. 코드 검증을 장중 효과 확인으로 표시하지 않는다.
- 후속 선택 릴리스의 관련 코드·시험 16개 파일 SHA가 최초 점검본과 같다. 변경은 보조 reader의 역사/현재 ancestry 준비 검증과 그 시험이며 PASS→HTTP 경로 변경은 없다. [후속 선택 코드 대사](../../tmp/post-aux-guard-audit-20261017/code-review/selected-successor-source-parity.json).
- 실행 원천: 10/12~16 기존 sentinel cache의 고정 snapshot. 보조 연구·가격 라벨은 기존 9/29~10/16 누적 연구를 재사용했다. 과거 정책과 현재 선택 코드를 분리한다.
- 근거: [집계·원천 해시](../../tmp/post-aux-guard-audit-20261017/summary.json), [캐시 manifest](../../tmp/post-aux-guard-audit-20261017/source-manifest.json), [선택 코드 상세 검토](../../tmp/post-aux-guard-audit-20261017/code-review/selected-code-findings.md), [미전송 상태 재현](../../tmp/post-aux-guard-audit-20261017/code-review/zero-wire-reproduction.json).
- 현재 작업 원칙은 Plan Rebase와 10/17 체크리스트를 확인했다. 기존 동시 작업·과거 실패·정책·주문 원천을 변경하지 않았다. 신규 수리의 완료 owner나 배포 승인을 이 감사로 만들지 않는다.

## 2. 보조판정 → 실제 제출 전체 경계

아래는 현재 활성 Main 경로의 논리 순서다. 자금·I/O·분할 계획을 사이에 두고 같은 안전조건을 재검사하는 경우도 포함한다. 과거 scout/sim/widget/episode 코드를 현재 진입 정책으로 합산하지 않는다.

| 단계 | 주요 가드·로직 | 판단 |
|---|---|---|
| 1. AI 응답 수용 | 스키마·fact binding·PASS, 완료 상태, 원 request/generation/claim, 원 5초, WATCHING, route/venue/source, 호가·보유·pending·cooldown | PASS 문자열만으로 진입 권한을 만들지 않음 |
| 2. Main 진입 자격 | 수동·영구 제외, 매수 중지, 시장·시간·전략, 손실 재진입, 기존 알림·지연 intent, 유효 가격 | 계좌·수탁·운영 안전 경계 |
| 3. 판정·제출 신원 | machine receipt, fixed-watch/native 또는 scanner parent, 현재 revision, 같은 PASS 중복, 기존 미결 주문·다른 owner·exit 충돌 | fixed-watch 연결 수리 포함. 미전송 PASS 처리에 잔여 결함 |
| 4. 자금·최초 수량 | 계좌/현금·증거금·가용액·리스크 예산, 양수 수량, 상한가 근접, 최종 가격·cap·leg 수량 | 의도적 0주와 계산/원천 결손을 구분 |
| 5. 시세·집행 가격 | 정확 경로 WS, 허용된 원천 보강, stale/DANGER/jitter/spread/slippage, 기계 가격 영수증, 미시 원천·가격 괴리 | CAUTION 자체는 일괄 차단이 아님 |
| 6. 추가 진입 품질 | 유동성 결손+CAUTION 조합, AI BUY/source/trace, rising-missed 분기, 유동성 최소, 과열 눌림·재돌파, weak-pullback | 정확한 Main ENTER+PASS의 중복 약세 veto는 관측으로 낮춤. 결손·DANGER는 유지 |
| 7. 제출 지연 | 정책 0초는 즉시 진행, 양수는 원 인과 신호·due successor·route/가격/수량 재확인 | 새 5초를 부여해 오래된 PASS를 되살리는 경로가 아님 |
| 8. 실행 계획 | 보조 registry/overlay·기계 세대, 적용되는 AI 3초 TTL, frozen receipt, sequential/atomic 계획, 총량·즉시량·잔량, probe/defer | 계획 총량과 첫 probe 체결량은 다름 |
| 9. leg 직전 재검사 | route/order type, 수량·margin cap, late-price, weak-late, 가격 호가, generation 예약, 정책 revision, 원 deadline | 역사 weak-late 빈도와 현재 scoping을 분리 |
| 10. 주문 의도 저장 | 최초 bundle/leg/intent/owner·가격·수량 저장, BUY_ORDERED·reconciliation 진입, 거래소 적격성, 원 deadline 재검사 | 실제 전송 전 저장됨. 알려진 미전송 종료 경로가 불완전 |
| 11. adapter 로컬 검사 | 양수 수량, retired symbol/owner, pause/clock, 주문 유형·거래소 적격성, owner 예약 | 로컬 거절은 브로커 거절이 아님 |
| 12. 실제 HTTP 직전 | 정확 payload/intent/기계·AI trace/정책, 현재 신호·manual/pause, 원 5초, item/route/epoch/sequence/호가 freshness, bid/ask/current 일치 | 첫 HTTP 및 허용된 인증 재시도 직전에 검사. 3초 AI expiry 결속은 빠짐 |
| 13. 응답·종결 | 로컬 미전송, 전송 불확실, owner binding 실패, broker 거절, order ID 성공, bundle/잔량 수탁 | 로컬 미전송 상태·카운터 정리 결함. 불확실 주문은 중복 재송신 금지 |

세부 함수·선택 코드 행 번호는 [13단계 코드 목록](../../tmp/post-aux-guard-audit-20261017/code-review/selected-code-findings.md)에 있다. 후속 leg·AVG_DOWN·SELL·CANCEL에는 별도 수명/수탁 계약이 적용된다.

## 3. 누적 실제 PASS 뒤 무엇이 막았는가

`(source_date, evaluation_attempt_id)`를 묶고 실제 `async_auxiliary_status=pass` 또는 `ENTER_NOW + entry_ai_screen_status=pass`가 있는 경우만 셌다. `ai_confirmed`라는 stage 이름만으로 PASS를 추정하거나 ID가 없는 이벤트를 임의 연결하지 않았다. 같은 판정의 재시도는 한 건이다. 각 차단은 **관측된 가드 통과 실패**이며 최종 단일 원인이나 제거 시 주문 가능성을 뜻하지 않는다.

| 관측 가드 | 해당 PASS 판정 수 | 반복 로그 수 | 현재 코드와의 관계 |
|---|---:|---:|---|
| 약한 눌림 `real_weak_pullback_entry_block` | 67 | 84 | 정확한 Main ENTER+PASS 범위의 중복 veto 완화 수리 포함 |
| 지연·호가 `latency_block` | 62 | 127 | freshness·DANGER·slippage·deadline 원인 구분 필요; 일괄 해제 대상 아님 |
| 약한 문맥 늦은 진입 | 39 | 47 | 관측 이력 제외·확정 block 이력·정확 PASS scoping 수리 포함 |
| 로컬 주문 유형 preflight | 13 | 14 | 14행 모두 `ORDER_TYPE_PREFLIGHT_BLOCKED`; broker 거절로 세면 오류 |
| 실행 수량 계획 증빙 | 11 | 14 | 14행 모두 `machine_action_receipt_absent`; native fixed-watch 계약 수리 포함 |
| 제출 직전 재판정 | 2 | 2 | 해당 시점 신호·원천 재확인 |
| 최종 수량 0 | 1 | 1 | SAFE_UNKNOWN venue 미확정의 의도된 0주 사례 |

**분모는 AI PASS 반환 176개이며 표의 가드끼리 중복된다.** 그중 실제 record 연결이 확인된 것은 155개다. 나머지 21개는 PASS가 반환됐지만 Main 인수 단계에서 거절됐다. 따라서 행을 합산해 주문 실패 수나 실패율을 계산하지 않는다. broker accepted 관측은 15개 판정으로, 14개 판정의 1leg와 한 판정의 3legs에서 주문번호 17개가 확인됐다. 체결·완료 건수와 다르다. accepted 15개는 가드 차단 관측 사례와 겹치지 않는다.

| 일자 | PASS 판정 | broker accepted 관측 |
|---|---:|---:|
| 10/12 | 27 | 0 |
| 10/13 | 31 | 0 |
| 10/14 | 29 | 0 |
| 10/15 | 77 | 7 |
| 10/16 | 12 | 8 |

삼성전자: PASS 14개, accepted 4개; latency 4·로컬 preflight 4·약한 눌림 1·약한 문맥 1. 비삼성: PASS 162개, accepted 11개; 약한 눌림 66·latency 58·약한 문맥 38·수량 증빙 11·로컬 preflight 9·재판정 2·수량 0 한 건. 이 역시 중복되는 가드 노출 수다. 종목별 PASS는 주성 90, 알테오젠 39, HPSP 23, 삼성전자 14, 두산 9, 삼성전기 1이다.

캐시 5일 866,486행을 한 번 읽고 관련 이벤트 14,464행만 투영했다. 원천 해시·byte offset·행 해시를 보존했으며 수량 계획/로컬 preflight 원행을 다시 대조했다. 10/16 캐시는 raw 말미 전체를 포함하지 않고 과거 schema 확장도 소급 채워지지 않는다. 따라서 **이 176개를 과거 전체 AI 호출 또는 전체 PASS 모수라고 부르지 않는다.**

원 deadline이 있는 175개를 대조했다. 가드 로그 기록시각이 이미 기한을 넘긴 평가가 약한 눌림 9/67, latency 11/62, 약한 문맥 5/39, sizing 1/11, 재판정 1/2였다. 가드끼리 중복되며 monotonic 조건 평가 시각이 아닌 로그 시각이다. latency 127행의 사유는 `latency_state_danger` 124행, `signal_deadline_exceeded` 3행이다. **local latency 예산과 원 신호 deadline을 동일한 시계로 해석하거나, 앞선 가드 제거만으로 정상 제출을 보장하면 안 된다.**

## 4. 놓친 기회: 확인한 것과 확인하지 못한 것

누적 실제 Main ENTER 연구 2,927개 중 가격 연결 적격은 295개뿐이다: WIN 75, STOP 0, TIMEOUT 126, 미확정 94, source gap 2,632. 적격 자료는 10/12·15 AFTER에 치우쳤고 WIN 75개는 목표 도달 시각 8개에 집중돼 있다. [누적 연구 원천·독립 라벨 검증](main-cumulative-opportunity-failure-and-nonfixed-quote-review-2026-10-17.md)을 재사용했다.

이번 PASS 176개를 capture SHA 또는 정확한 native event/date/symbol로 연결한 결과:

| 연결 결과 | 수 |
|---|---:|
| WIN | 2 |
| 30분 목표 미도달 TIMEOUT | 24 |
| 미확정 | 6 |
| 연구 원천 결손 | 139 |
| 같은 판정에서 복수 capture가 연결돼 제외 | 5 |

5개 충돌은 서로 다른 PID의 capture가 같은 native event 문자열을 재사용한 경우다. 4개에는 명시적 capture SHA 하나가 있지만 fallback까지 결합한 이번 집계에서는 보수적으로 제외했다. 두 후보 라벨은 모두 SOURCE_GAP이며 임의로 최신 capture를 선택하지 않았다. 단일 연결 171개는 관측된 PID/start ticks/policy bundle 대조에서 불일치 0이었다. 확정 가격 라벨은 26개뿐이며, 나머지 150개를 실패·0%로 채우지 않는다. TIMEOUT도 실제 금전 손실이 아니다.

| 놓친 WIN 확인점 | 실제 미제출 가드 | 해석 |
|---|---|---|
| 주성 10/12 AFTER native 17:49:04.549684, `aims-aa15087d48ea0bc88607` | 약한 눌림 `weak_momentum_caution_without_micro_confirmation` | 목표 도달 18:18:40.749. 차단 시각 17:49:09.624는 원 deadline 09.549보다 약75ms 늦다. **약한 눌림만 제거하면 제출 가능했다는 증거는 아님** |
| 주성 10/12 AFTER native 17:52:33.751021, `aims-55d9c2e147fdd209984f` | 수량 계획 `machine_action_receipt_absent` | 목표 도달 18:09:52.050. 첫 차단 17:52:37.889, 재시도 38.058, 원 deadline 38.751. 당시 시간 여유는 있었으나 다른 최종 guard·체결 가능성은 미입증 |

두 점은 확인 시점 ask·비용 0.23%·30분·비용 후 +0.4%/soft −3% 선도달 기준이다. 목표 시각은 서로 다르지만 동일 종목의 30분 창이 겹친다. **독립 실거래 이익 두 건이나 회수 가능한 확정 수익으로 세지 않는다.**

비상시감시 삼성전기 009150의 10/16 PASS 뒤 미제출은 pre-cap 1주→SAFE_UNKNOWN 최종 0주였다. 확인점 호가 age 약290ms는 그 시점 자료이며 약2초 뒤 최종 주문 시세까지 신선했다는 뜻은 아니다. 사후 라벨은 SOURCE_GAP이므로 놓친 승리로 확정하지 않는다.

accepted 15개는 SOURCE_GAP 13·미확정 1·TIMEOUT 1이다. 유일한 TIMEOUT은 알테오젠 10/15 16:59 `aims-872fa3742b6f38238929`, 주문번호 `0058723` 1주다. AI PASS와 제출을 통과했으나 원 확인 ask 기준 30분 목표에 미도달한 것은 확인된다. 실제 체결 가격·청산 수익률을 뜻하지 않는다.

## 5. 오진입 방지 실패: 보조판정의 실제 한계

### 5.1 연구에서 WIN 회복과 실패 차단은 다른 결과

기존 실제 AI 호출 원응답을 재사용했다. 새 호출은 없다. 양성=WIN, 예측 양성=PASS다.

| 비교 | 현행 TP / FP / FN / TN | 후보 TP / FP / FN / TN | 의미 |
|---|---|---|---|
| 사실 역할 계약 150쌍 | 61 / 36 / 46 / 7 | 73 / 34 / 34 / 9 | WIN 회복·실패 차단 소폭 개선. STOP 9개 중 6개는 여전히 PASS |
| 실제 현행 입력·문구 대 최종 조합 50쌍 | 20 / 10 / 18 / 2 | 32 / 12 / 6 / 0 | WIN 오차단은 감소했지만 STOP 3·TIMEOUT 9 모두 PASS |

두 비교의 분모·개선폭을 더하지 않는다. 50점은 앞서 본 연구 자료이며 독립 holdout이 아니다. [직접 비교 보고서](main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md).

현재 10/19 채택 범위는 두산·알테오젠 PRE/NXT 두 경로다. 이 20점은 모두 WIN, 두 원천 구간·6개 목표 시각에 집중된다. 해당 채택이 실패 차단 능력을 입증한 것은 아니다. 다른 126개 연결과 삼성·REGULAR·AFTER는 승계한다. [최신 선택·준비 상태](main-auxiliary-next-session-deployment-review-2026-10-17.md).

### 5.2 의미적 결함: 위험을 보지 못하거나 표현할 수 없음

1. 기존 확장형 입력은 `spread>0`이면 `ENTRY_SPREAD_CONCERN`으로 만든다. 정상적인 양수 spread의 존재와 거래를 무효화할 정도의 spread 위험이 같은 역할이다. legacy 쪽의 spread 임계 역할과도 다르다. 사실 역할 보완은 일부 경로에만 선택됐으므로 전 범위 해결로 볼 수 없다.
2. 확장형/UNION 응답 계약은 non-PASS에 입력의 `risk_fact_bindings` 결속을 요구하지만 PASS에는 `observed_machine_signal` 지지만 허용한다. 실제 137310 AFTER 표본에서 binding이 비어 있고 결과는 TIMEOUT인데, CAUTION/VETO 대조 6가지가 모두 `union_nonpass_risk_unbound`였다. **입력에 위험 표현이 없으면 AI가 기계 오판을 거르는 관문 역할을 수행하기 어렵다.** 이 한 사례를 모든 실패 표본의 강제 PASS로 일반화하지 않는다.
3. 보완은 validator 우회나 근거 없는 VETO 허용이 아니다. 그 시점에 알려진 세션·가격 진전·호가 대비 상승 여유·구조 사실을 versioned 입력과 실제 결속 가능한 위험으로 전달하고 동일 원천에서 실패 차단과 WIN 회복을 함께 비교해야 한다. 원 입력·응답·라벨·membership은 보존한다.

근거: 선택 코드 `scalping/reversal_extended_auxiliary.py`의 production_request/validate_response, [역할 계약 연구](main-auxiliary-risk-role-contract-research-review-2026-10-17.md), [실패 진단](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/discriminative-20261017/completed-error-diagnostic.json).

### 5.3 실제 주성 49294: 약한 가격 진전을 기계·AI가 함께 통과

10/15 14:06:31 ENTER → 14:06:34 AI PASS 84 → 14:06:35 210,000원 1주 BUY_DEFENSIVE 체결. 목표 총량 5주 중 잔량 4주는 재확인 timeout으로 **미제출**이었다. 4주 취소나 5주 손실로 세지 않는다.

당시 매수 비중 92.58%지만 10틱·60초 가격 진전은 0, 반등 약0.2387%는 spread 한 호가 수준이었다. 기계 원천의 세션 −4.328%, DOWN/MIXED, 고점·저점 상승 부재가 compact AI 입력에 빠졌고, AI는 `observed_machine_signal`만 지지했다. 기계의 매수 비중과 AI의 신호 재승인이 독립 확인처럼 작동한 사례다.

14:15 hard-stop 경로는 운영자 수동 이관에서 종료했다. 이후 자동매도 부재를 broker 실패로 해석하지 않는다. 10/15 당시 미종결 보고 이후 **10/16 09:23:48, 206,500원 1주 매도로 COMPLETED**가 확인됐다. 실제 거래별 비용은 여전히 없어 추정 수익률을 순실현 성과로 쓰지 않는다. [사건 당시 전체 경로](main-jusung-hard-stop-pattern-and-full-flow-research-2026-10-15.md)의 미종결 서술은 당시 시점의 상태다.

또한 연구 입력은 30분/soft −3%였지만 당시 실행 영수증은 preset hard −1.4%·grace 0초·emergency −2.4%였다. 연구 label 성공과 실제 집행 결과는 같지 않다. 연구 −3%를 운영 안전선에 덮거나 과거 라벨을 바꾸지 않고 별도 execution-path 결과를 붙여야 한다. 이 과거 preset 값을 현재 전 종목 정책으로 단정하지 않는다.

## 6. 최신 선택 코드의 잔여 결함

### G171 P1 — 알려진 미전송이 주문 의도와 PASS를 점유

- 생산자/소비자: `sniper_state_handlers._initial_quantity_prepare_first_submit` → `kiwoom_orders` final physical guard → submit-response / timeout / owner recovery.
- 첫 leg는 adapter 전에 `SUBMIT_INTENT`, stock `BUY_ORDERED`를 저장한다. 물리 전송 가드가 0회 전송으로 반환하면 attempt counter만 되돌리고 break하여 `_initial_quantity_record_submit_response`를 건너뛴다. owner는 `INTENT_REJECTED`지만 bundle은 미결로 남는다.
- 실함수 격리 재현에서 +1초와 +61초 모두 `RECONCILE`, 기한 후에도 `budget_breached=true`일 뿐이다. recovery는 `ORDER_BOUND/ORDER_TERMINAL + broker number`를 요구해 알려진 미전송 owner를 거부했다.
- 별도 scanner/fixed-watch handler 2개 fixture에서 `_async_entry_submission_identity`가 전송 0회에도 유지됐다. 다음 동일 PASS는 이미 제출한 것으로 처리한다. sequential 전체 종단 테스트가 아니라 handler fixture와 상태함수·source 분기 검증을 조합한 근거다.
- 조치/종료: 정확한 intent의 미전송 종료를 멱등 기록하고 bundle·owner·PASS 소비 상태를 대사한다. 원 deadline을 연장하지 않으며 불확실한 POST의 잠금을 풀지 않는다. context 생성 실패·intent 뒤 만료·0회 로컬 거절·인증 실패·불확실 전송을 각각 재기동까지 검증해야 한다.

### G172 P2 — 재가격이 필요하다는 반환에 실제 처리 경로가 없음

- `trading/entry/physical_send_guard.py`는 bid/ask/current 중 하나라도 바뀌면 `execution_price_changed_reprice_required`로 차단한다. 허용 slippage·가격·수량 경계 안의 변화도 동일하다.
- exact equality 자체는 보수적 계약이다. 문제는 이름과 달리 bounded reprice 처리 없이 G171 경로로 종료한다는 점이다. 자연 손실 건수는 아직 없다.
- 조치/종료: 같은 intent·원 deadline 안의 재가격/수량 재검증 또는 명확한 미전송 종결을 선택한다. stale·epoch·price cap을 완화하지 않는다. 변화가 없는 경우/허용 한 호가/상한 초과/기한 만료/동시 신규 intent를 구분한다.

### G173 P2 — 적용되는 AI 3초 TTL이 최종 HTTP 검사에 없음

- 분할계획 앞에서 3초를 확인하지만 이후 durable intent·venue·token/auth refresh 시간을 거친다. 최종 physical context는 원 5초와 quote를 검사하고 AI confirmed epoch/expiry는 보유하지 않는다.
- 코드상 계약 공백이며 실제 TTL 초과 주문이나 손실을 관측한 것은 아니다.
- 조치/종료: 적용 범위의 기존 AI expiry를 최종 callback에 전달한다. fresh quote + 원5초 이내 + AI3.1초인 지연 인증 사례를 검사한다. TTL 값을 변경하거나 후속 leg·SELL에 최초 진입 TTL을 적용하지 않는다.

### G174 P2 — 로컬 거절이 broker attempt로 집계

- adapter는 `ORDER_TYPE_PREFLIGHT_BLOCKED`, `broker_order_attempted=false`를 반환한다. Main은 호출 전 카운터를 올리고 새 physical-guard 반환 형태만 차감한다. 일반 로컬 거절은 `order_leg_fail`과 bundle submit failure에 남는다.
- 누적 13개 PASS/14행의 로컬 preflight를 증권사 주문 거절로 해석하면 안 된다. `nxt_market_to_best_limit`는 정상 변환 metadata다. 10/14 정확 사건의 원인은 `eligibility_unknown`으로 확인·수리됐지만 14행 전부의 상세 원인을 같은 값으로 추정하지 않는다.
- 조치/종료: adapter의 알려진 physical-attempt 상태를 공통 반환 계약으로 소비한다. 로컬 거절/실제 broker 거절/전송 불확실/성공을 각 counter·terminal·owner에서 대사한다.

## 7. 이미 보완된 부분과 관측·평가 구조 결함

### 이미 보완된 코드

- weak-pullback·weak-late 환경 설정은 **ON**이다. default OFF와 실제 유효값을 혼동하면 안 된다. 정확한 Main ENTER+PASS의 신원·revision·AI 권한·SAFE/CAUTION이 맞을 때만 중복 alpha veto를 `risk_context_only`로 낮추는 수리가 적용됐다.
- `risk_context_only`와 확인되지 않은 이력은 weak-late의 실제 block 횟수에서 제외된다. 관측 폭주가 실제 차단 이력을 밀어내지 않도록 분리됐다.
- fixed-watch native parent와 scanner promotion을 구분한 receipt, explicit NXT의 당일 적격성 전달 수리가 있다. 과거 `machine_action_receipt_absent` 11건 전부가 자동 해결됐다는 exact replay 증거는 아니다.
- 최종 native/quote/원 deadline 검사가 실제 HTTP 및 제한된 인증 재시도 직전으로 이동했다. 중간 단계 통과만으로 늦은 주문을 전송하던 위험을 줄이는 수리다. G171~174는 이 보완 이후 남은 경계다.

관련 표적 테스트 71개 통과. 이는 과거 누적 가드의 자연 개선율 증명이 아니다.

### 관측·사후평가 구조

1. **전체 funnel처럼 보이는 지표의 분모 불일치.** `buy_funnel_sentinel._machine_primary_entry_funnel`은 MAIN_FIXED_WATCH를 별도 식별 후 scanner grouped funnel에서 제외한다. 10/15·16 요약의 AI PASS 0과 같은 날 order bundle 7·8이 공존할 수 있다. scanner 모수를 전체 Main으로 읽으면 거짓 0이다. fixed-watch/scanner를 각각 exact attempt로 보여주고 전체 합집합을 별도로 대사해야 한다.
2. **원천 결손이 커서 가드별 성능을 비교할 수 없는 구간이 많다.** PASS 176개 중 확정 가격 라벨 26개. ID 미기록·복수 capture 충돌·route invalid를 보존하고 결손을 승패에 넣지 않는다. 수신 prefix·정확 quote·원 intent를 재결속하는 기존 제한된 경로가 우선이다.
3. **완료 거래와 실제 비용의 결속 부족.** 9/29~10/16 실제 Main 매수 기록 16개 중 DB COMPLETED 13·HOLDING 3이며, 완료 시각/수익률이 없는 한 건을 제외한 latest 완료 projection은 12개다. 12개 모두 `broker_actual_cost_observed=false`, 실제 순손익 NULL이다. 고정 비용 추정치로 actual을 채우지 않는다.
4. **주문·종결 이벤트 반복과 세션 축 혼용.** 주성 49294의 sell_completed 1,411행은 실제 매도 1회의 반복 전달이며 1,411거래가 아니다. 10/15 AFTER 진입한 3건이 10/16 PRE 청산 context의 bucket을 갖는다. 진입 가드 평가에는 entry session을 써야 한다.
5. **기존 수량 장후 소비 결함은 별도 후속이다.** [IQ171~175 감사](initial-quantity-runtime-postclose-result-review-2026-10-17.md)에 큰 projection과 reader 상한, emitted 날짜 누락, producer 양수/consumer 0의 ready, source gap의 valid-empty, 실제 비용 미배분이 기록돼 있다. 이번 감사에서 최신 릴리스의 모든 IQ 항목을 재실행하지 않았으므로 과거 선택 코드 재현과 현재 완료 상태를 혼동하지 않는다. 해당 owner를 중복 생성하지 않는다.

## 8. 우선순위와 검증 종료 조건

| 순서 | 보완 | 필요한 증거 |
|---|---|---|
| 1 | G171 미전송 상태 정리 + G174 실제 전송 분류 | same intent/원 deadline, owner/bundle/소비 상태 대사, 로컬0회와 불확실 전송을 분리한 재시작 회귀 |
| 2 | 위험 표현 가능성·실패 사실 전달 | 원 보조 입력/응답 보존, 빈 binding 실패 사례와 WIN 회복 사례의 paired 검증. 단순 PASS 확대와 실패 veto 개선을 각각 공개 |
| 3 | G172 재가격 경로 + G173 최종 TTL | 기존 가격·수량·freshness·5초 안전 안에서 허용/거절/종결 검증. 실제 단계별 시간 분포로 비용 확인 |
| 4 | fixed/scanner 관측 합집합과 가격·실거래 결과 연결 | producer=소비+사유별 제외+미관측 보존식, entry session/고유 주문·고유 종결/실제 비용 구분 |

승패 연구의 기준은 기존 비용 후 +0.4%·30분·soft −3%와 누적 승률을 유지한다. 이번 감사가 EV·최소 표본·성공 전부 보존 같은 새 채택 문턱을 추가하지 않는다. 동시에 반복 확인점 승률을 독립 거래 손익으로 바꾸지도 않는다. 과거 최다 차단 67개를 일괄 해제하는 것보다 **이미 승인된 정확 PASS의 불필요한 중복 차단 제거, 미전송 종료 보완, AI가 실제 실패 사실을 표현할 수 있는 입력 계약**이 우선이다.

## 9. 검증 범위

- 누적 캐시 한 번의 읽기 전용 집계, exact attempt/capture 연결, 원행 해시 재대조. 독립 리뷰로 원행 중복 0·동일 평가의 PID 충돌 0·최초 PASS보다 앞선 가드 0과 약한 눌림 WIN 사건의 로그 deadline 초과를 확인했다. [독립 집계 검토](../../tmp/post-aux-guard-audit-20261017/independent-census-review.md).
- 선택 코드의 기존 보완 계약 71개 표적 테스트, 로컬 0회 handler fixture 2개, 실제 sequential prepare/timeout/recovery 함수 재현. 모의 broker만 사용했다.
- 문서 링크·서술·분모 검토, print-only parser, 문서 diff 검사. broad 거래 suite·새 AI·provider·broker 요청·장후 재생은 수행하지 않았다.
- 새 audit와 작은 재현/집계 산출물만 작성했다. 운영 코드·환경·정책·프로세스·원장·DB는 변경하지 않았다. 잔여 결함 G171~174는 **미수정**이다.
