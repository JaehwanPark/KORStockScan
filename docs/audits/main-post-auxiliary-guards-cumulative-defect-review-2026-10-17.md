# 보조판정 이후 실제 제출: 전체 가드와 누적 기회·오진입 점검

현재 정규장 기준은 아래 **§10의 2026-10-23 재점검·연구**다. §§1–9는10/17 당시의 코드·사건·잔여 결함 기록으로 보존하며 현재 미구현 목록으로 전용하지 않는다.

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

## 10. 정규장 제출직전 가드 재점검·연구 — 2026-10-23

### 범위와 현재 기준

AGENTS.md를 다시 읽고 현행 Plan Rebase §1–8·10/23 checklist·리뷰 게이트를 적용했다. 이 절은10/17 당시의 위6~9절 미수정 상태를 현재 상태로 오인하지 않도록 별도 기준을 둔다. 운영 코드·정책·프로세스를 바꾸는 작업은 아니다.

고정 시점10:39의 실제 선택은 `926ebca82aa48119ea1ff1483ef33cd78be508ee`, PID `1982231/start36273583`이며 `/proc` cwd/start와 selector의 **actual_pid_receipt**를 대조했다. 정규장은 session `KRX_REGULAR`, 정책 cohort `KRX`, 원천 `<symbol>_AL / krx_nxt_integrated`, 요청·유효 broker route `SOR`다. 실제 실행 거래소는 matching execution receipt로 검증하지 않았으므로 미확정이다. 10/22 실제 사건은 당시 `75e0fbbf79d8842ceed159ea73166f8872b4e93e / PID1485693/start26786759`, bundle `e815509b…`로 보존했다. 현재 `1d9e5b09…`를 과거 실제 판정에 소급하지 않았다.

[연구 봉인](../../tmp/post-aux-guard-audit-20261017/followup-20261023/freeze.json), [실제 사건·가격 연결 결과](../../tmp/post-aux-guard-audit-20261017/followup-20261023/result.json), [가드·약세 대조](../../tmp/post-aux-guard-audit-20261017/followup-20261023/supplement.json)가 이 절의 근거다. 기존 원장·라벨·AI 원 입력/응답을 복제하거나 새 Provider를 호출하지 않았다. 기존 Source22 기계연구는 [별도 owner](./main-machine-pattern-dual-track-research-review-2026-10-21.md#정규장-점검과-source22-반등-후속-연구--2026-10-23)의 결과를 해시 대조 후 재사용했다.

### 현재 제출 경로의 가드

| 순서 | 여전히 적용되는 검사 | 현재 코드·해석 |
|---|---|---|
| 1 | 정확한 Main ENTER_NOW·유효 AI PASS, 원 attempt/revision/trace/정책 부모 | raw PASS 문구·CAUTION·transport 미평가는 제출 authority가 아니다. fixed-watch 증빙을 scanner ID로 대체하지 않는다. |
| 2 | Main/manual/퇴역 owner, 중복·arm·cooldown·동시 intent·계좌/미체결 | 기존 운영·custody 안전검사 유지. 퇴역 owner 잔여분으로 Main을 차단하거나 인수하지 않는다. |
| 3 | 실시간 원 item/route/transport epoch·BBO·현재가·신선도/상충·가격/수량 | regular `_AL`/SOR를 cohort `KRX`와 혼동하지 않는다. source-quality 실패와 alpha 판단을 분리한다. |
| 4 | latency·signal reference 기한·SAFE/CAUTION의 slippage, DANGER | [latency owner](/home/ubuntu/KORStockScan-runtime-releases/sentinel-integrated-20261023-926ebca82/src/engine/sniper_entry_latency.py:4970)와 [EntryPolicy](/home/ubuntu/KORStockScan-runtime-releases/sentinel-integrated-20261023-926ebca82/src/trading/entry/entry_policy.py:22)의 별도 clock. 원 native 신호5초·AI3초와 동일한 타이머로 합치지 않는다. |
| 5 | 유동성·overbought/pullback, weak pullback/micro source | 동일 exact Main ENTER_NOW+PASS의 **중복 약세 alpha veto**는 이미 risk context로 전환하는 scope가 있다. source-invalid micro·DANGER는 그대로 차단한다. |
| 6 | 자금·초기수량·기존 한도·분할계획·원 AI TTL | 양수 수량·자금 PASS가 broker 전송을 보증하지 않는다. |
| 7 | delay 정책·fresh successor, native/보조 generation·revocation·revision 재검증 | delay를 이유로 과거 PASS·원 deadline을 갱신하지 않는다. |
| 8 | 첫 leg 가격 drift·weak late context·실행계획 | fresh quote와 기존 가격 안전 내에서만 진행한다. 미래 고가가 당일 입력이 되지 않는다. |
| 9 | owner intent 생성·기록, 마지막 source/기한/AI TTL 재검증 | [physical send guard](/home/ubuntu/KORStockScan-runtime-releases/sentinel-integrated-20261023-926ebca82/src/trading/entry/physical_send_guard.py:78)는 원 native deadline과 `ai_authority_expires_epoch/perf`를 모두 보유한다. |
| 10 | adapter의 broker/account/route/주문유형·가격/수량·시간 검사, 첫 HTTP 및 허용 auth retry 전 guard | 로컬0회 거절과 broker/transport 불확실을 구분한다. 불확실 전송을 새 주문으로 재시도하지 않는다. |
| 11 | response/주문번호·접수/미전송 종료·같은 intent 상태 소비 | 현재 `_initial_entry_known_not_sent`와 `is_verified_local_buy_no_call_response` 경로가 존재한다. 위10/17 G171/G173/G174를 그대로 현재 미구현이라고 재신고하지 않는다. 자연 소비와 fill/실현손익은 별도다. |

현재 PID의 두 약세 가드 enable 값은 모두 true이며, 코드 default OFF를 운영 OFF로 보고하지 않았다. 다만 [정확 PASS scope](/home/ubuntu/KORStockScan-runtime-releases/sentinel-integrated-20261023-926ebca82/src/engine/sniper_state_handlers.py:34840)가 중복 veto를 context로 바꾸므로 enable만으로 실제 veto 여부도 판단하지 않는다. 최신 PID에는 아직 이 branch의 유효 PASS 자연 표본이 없다. 기존 G172 재가격은 pending-order reprice 함수의 존재만으로 첫 전송 전 무전송 재가격 수용까지 닫지 않는다.

### 실제 정규장 분모와 차단 결과

10/22·23의 기존 Sentinel compact index를 read-only로 한 번씩 읽었다. 동일 evaluation ID라도 PID/start/release/request가 다르면 격리했고, session은 명시 필드로 구분했다. 감시 보고서의 scanner0을 Main 전체0으로 해석하지 않았다.

| 대상 | 유효 AI PASS | 자금 통과 | broker 제출 관측 | 나머지 종료 |
|---|---:|---:|---:|---|
| 10/22 정규장·당시 PID | 7 | 6 | 1 | 보조 재검증3, latency1, 물리 전송 전1, Main 소비 전 기한 만료1 |
| 10/23 정규장·고정 index prefix | 0 | 0 | 0 | identified async21건: 기계 원천무효16·보조 원천미평가2·응답무효1·transport미평가1·CAUTION1 |
| 위10/23 중 최신 PID1982231 | 0 | 0 | 0 | identified async1건. 구PID 사건을 합쳐 현재 가드의 차단 실적으로 세지 않는다. |

10/23 별도 evaluation ID 없는 async4행은 표본에 붙이지 않았다. 10/22는 같은 결손8행이 있다. 이는 완전한 시장·전체 주문 census가 아니라 해당 native cache가 보존한 원천 범위다. 알테오젠09:51 raw PASS는 `response_invalid`여서 유효 PASS에 포함하지 않았고, 삼성10:08은 transport timeout, HPSP10:11은 CAUTION이었다. 최신 PID 원천무효1건은 post-aux guard 차단이 아니다.

10/22 유효 PASS7건은 전부 원 machine capture의 exact hash·attempt·PID/start·native event와 정규화 행의 **원 transport epoch/sequence**까지 연결했다. 정규화 collector epoch와 live transport epoch를 같은 필드로 간주하지 않았다. 목표는 실제 confirmation ask부터 **비용0.0023을 한 번 반영해 +0.4%, soft−3% 선도달 없이30분**이며, 7건 모두 native tick에서 확정됐다. 비용은 설정값이며 broker 대사 실현 비용·체결 손익이 아니다.

| 종목·attempt 끝자리 | 실제 종료 | 후행 라벨 |
|---|---|---|
| HPSP `9f5af511a1f7a56d2699` | auxiliary_binding_submit_recheck | TIMEOUT |
| 주성 `57409fdaf19a7a47682b` | order_bundle_submitted | TIMEOUT |
| 두산 `ff47c4591d720a4a1e16` | auxiliary_binding_submit_recheck | **WIN** |
| 알테오젠 `f652f53aa886f0a51167` | auxiliary_binding_submit_recheck | TIMEOUT |
| HPSP `a2fe5bab71982b7e69b8` | latency_block | TIMEOUT |
| HPSP `44a86d424dcc18758ca5` | entry_physical_send_guard_block | TIMEOUT |
| HPSP `a614ef8237b8a3b08702` | result_deadline_expired | TIMEOUT |

이 실제 PASS 집합에는 삼성 표본이 없다. 미제출6건을 모두 통과시키는 단순안은 가격 라벨 기준 **W1/TIMEOUT5(16.7%)**를 추가한다. 이를 실제 제출 가능성·실현 승률로 해석하거나 TIMEOUT을 실제 손실로 바꾸지 않는다. 제출된 주성1건의 TIMEOUT도 실제 손절·손익을 뜻하지 않는다. 10/12~16의 기존 정규장79건은 SOURCE_GAP으로 남아 이번 승률 분모에서 제외했다. 그 결손을0승으로 채우거나 현재 source22로 소급 보완하지 않았다.

### 확실한 가격 기회와 아직 입증하지 못한 실행 가능성

**실제 PASS 후 놓친 기회 후보는 두산 10/22 09:20:30.324이다.** 원 ask62,800원 이후 같은 source의 bid63,200원이09:26:20.707에 관측돼 설정 비용 후 **+0.4055%, 350.383초**다. soft stop 선도달은 없다. worker PASS 후 첫 관측 가능한 fresh ask62,800원(09:20:34.949)에서도 후속 bid까지345.758초로 목표에 도달했다. 다만 그 ask까지 기다리는 데785ms가 소모됐으며, 수량7주의 실제 체결·depth·다른 hard guard 통과는 입증하지 않았다.

원 raw5.07GB 전체를 재주사하지 않고 세 사건의 약22.7MB byte window만 읽어 callback 이유를 확인·원행을 보존했다. 두산 callback은09:20:35.621554의 `auxiliary_decision_generation_changed`다. **이 문자열만으로 실제 정책 세대가 바뀌었다고 단정할 수 없다.** 당시와 현행 validator는 registry/binding/base/overlay 불일치와 원 신호5초 초과를 같은 오류로 반환한다. 두산의 자금 로그에는69.051ms가 남았지만 callback 로그는 신호 후5,296.833ms다. validator에 넘긴 `now`가 내부 읽기보다 앞서 고정되므로 callback 시각만으로 어느 predicate가 처음 실패했는지도 확정하지 않았다. HPSP 재검증 건은 이미 자금 로그에서 원 deadline을192.993ms 초과했다. 알테오젠은 자금 때652.899ms가 남았다. 따라서 단순 기한 연장·세대검사 삭제가 아닌 **실제 검사 시각·부모 비교·critical path**가 우선 연구 대상이다.

**약세장에도 상승 기회는 존재했다.** 기존 source22 정규장269개 진단 상승 창에서 현행 기계 재생 미포착은264개, 그중 원 ask→후속 bid 비용 후 목표 관측135개다. 원천 연속 관측120초 이상인41개 중, 진입 전120초 이내의 source-ready `BROAD_WEAKNESS` 지수 관측이 연결되는 창은 **29개(모두 비삼성, 종목 자체도 하락한 경우12개)**다. 120초는 원천 성숙도·시장 관측 나이를 공개하기 위한 연구 slice이며 새 live 가드나 보편적 freshness 허용값이 아니다.

29개를 전부 당시 ENTER해야 했다고 주장하지 않는다. 대부분 창 시작은 하락 중이고 반전 확인은 나중이다. 이미 동결된 A33/A36의 prefix 확인점과 같은 ask→bid 검증까지 이어지고, 확인 시점에도120초 이내 약세 지수 관측이 있는 대표4개는 아래와 같다. 미래 outcome으로 새 신호를 생성하지 않았다.

| 10/22 종목 | prefix 반전 확인 | 관측 ask→bid | 목표까지 | 비용 후 |
|---|---|---|---:|---:|
| 비상시감시003010 | 14:04:58.845 A33 | 11,120→11,210 | 214.699초 | +0.5775% |
| 두산034020 | 09:34:30.933 A33 | 62,800→63,200 | 351.176초 | +0.4055% |
| 주성036930 | 11:08:36.104 A33 | 189,100→190,300 | 161.300초 | +0.4031% |
| 비상시감시290720 | 14:32:07.244 A36 | 1,679→1,690 | 12.600초 | +0.4236% |

종목은 원 코드로 식별한다. 이들은 **현재 정책으로 과거 원천을 재생한 pattern 기회**이며 실제 AI PASS·제출직전 가드 차단 건으로 합산하지 않는다. 138360·357880도 pattern 이후 bid 목표가 있었지만 확인 시점 시장 관측 나이174.9/132.1초라 같은120초 연구 slice에서는 제외했다. 삼성의 이번29개 분모는0개이지 삼성 상승 기회 전체0개라는 뜻이 아니다. 삼성09:03:00 ask223,000→bid224,500,147.619초/+0.4411% 가격 창은 있지만 연결할 사전 지수 snapshot이 없어 약세장 증거로 사용하지 않았다.

### 방향 갱신과 다음 구현 우선순위

1. **P0: 정확한 유효 PASS의 남은 시간을 제출에 쓰는 경로.** 두산 WIN과 나머지 실패를 같은 표로 유지한다. 기존 request/evaluation/capture·trace·timestamp를 재사용해 PASS완료→Main소비→자금/수량→native/보조 재검증→첫 HTTP의 구간 시간을 비교한다. 중복 policy/registry 읽기·재계산·동기 I/O의 현재 코드 개선이 이 branch를 실제 단축했는지 검증하며, 개선 전 구PID를 현PID 성과로 합치지 않는다. 기존 generation 오류에 실제 검사 clock·비교값을 결속해 원인 혼동을 줄이며 새 분류 체계·별도 감시기/원장은 만들지 않는다.
2. **P1: 만료·가격/세대 변화 뒤 fresh 재평가의 생존성.** 기존 bounded successor 경로에서 새 native 반전과 새 유효 보조 결과·정상 source/계좌/가격/수량으로만 재진입하는지 검증한다. 원 PASS 재사용·deadline 초기화·불확실 broker 재전송은 제외한다. 단순 가드 제거가 추가하는 W1/TIMEOUT5를 대조군으로 유지하고, 확정 기회 복원과 실패 통과 증가를 함께 보고한다.
3. **P2: 약세를 일률 veto로 바꾸지 않는 패턴별 비교.** 별도 CF에서 current source22 정규 확인160개(W127/TIMEOUT30/STOP1/U2)에 source-ready·120초 이내 BROAD_WEAKNESS 전면 veto를 대입하면 W1/TIMEOUT4가 제거돼 확정 비율80.38%→82.35%, 서로 다른 target clock11→10이다. 효과5점 중 삼성4개는 TIMEOUT, 비삼성1개는WIN이며 시장미연결/오래된49개는 그대로 뒀다. 이 작은 날짜·반복 확인점에서 비율 개선이 있는 사실도 공개한다. **이 분모는 기계 확인점이며 유효 PASS 분모가 아니므로 제출직전 정책의 효과라고 이전하지 않는다.** 해당 stage의 동일 누적 표본·날짜별 효과와 놓친 반전 복원을 비교한 뒤 기존 family 계약으로 판단한다. 별도 EV·최소표본·승리 전부 보존이라는 새 채택요건을 추가하지 않는다.

전역 가드 해제나 반등 패턴 일괄 추가를 채택하지 않았다. 현재 입력·AI 응답·정책·주문 안전은 보존한다. 10/23 정규장 유효 PASS0으로 현재 post-aux 개선의 자연 효과는 아직 평가할 수 없다. 이후 자연 수용은 기존 `MainEntrySourceTerminalRepair1022`, 패턴 신규 종료 원천 검증은 `MachinePatternOpportunityResearch1023`가 각각 소유하며 이번 연구를 배포·정책 적용 권한으로 바꾸지 않는다.

### 검증·교체·자원

- 원 index compressed header SHA·payload SHA·population/cursor, 원 capture hash·정확 PID/start/attempt/native event, normalized source SHA·ask·행 적격성과 시장 source SHA를 대조했다. 미래 source·다른 item/sequence·unknown quote·raw PASS/무효 응답·재사용 ID의 PID/request 충돌15개와 실제7개 라벨의 독립 순차 oracle·원 code/원행 보존9개, 총24개 회귀가 통과했다. 누적 연구의 원 스크립트/산출물·실패 시도는 보존했다.
- 첫 집계는 selector top-level `pid`를 가정해 마지막 summary에서 `KeyError`로 실패했다. `actual_pid_receipt`와 실제 `/proc` start/cwd를 읽는 원 계약으로 수정하고 회귀를 추가한 뒤 재실행했다. 원 failed log/freeze/case와 성공 집계에 쓰인 원 code SHA를 보존했으며 실패를 성공으로 덮지 않았다. `--supplement`는 기존 완료 case/가격 연구만 재사용하며 native tick replay·index census를 반복하지 않는다.
- 집계3.79초·peak377.8MiB, 기존 compressed index 읽기 약101.5MB·capture27MB·normalized5.7MiB, 원 raw의 제한 읽기22.7MB다. 수백MB 원장·DB 복제나 canonical 장후 재생성은 없었다. 실행 제한은 CPU480초/메모리2GiB다.
- 교체 disposition: 위10/17 결과·원장·희소 라벨은 **retained**(당시 사실과 결손 증거); 그 당시 미수정 상태를 현재에 전용하던 해석은 본절로 **consolidated**. 원 read-only census/가격·시장 관측 owner와 현재 native validator는 **retained**(현 소비자 존재); 새 producer/validator/runtime entrypoint는 **none**. production source/tests 추가·삭제0이며 오프라인 연구 코드·회귀와 기존3개 owner 문서만 보완했다.


### P0/P1 구현·통합본 준비 — 2026-10-23

이번 별도 지시는 구현·리뷰·검증과 통합 배포본 **준비까지**다. 기반은 실제 선택926ebca82이며 오래된 canonical workspace609cdcf의 소스로 덮지 않았다. `codex/pre-submit-fresh-repair-20261023` 격리 작업본에서 최신 선택본의 기존 수리를 이어받는다. selector·Main PID·운영 정책·provider/주문은 변경하지 않는다. 정규장 identity는 위의 `KRX_REGULAR / KRX / _AL·krx_nxt_integrated / SOR`를 유지하며 실제 거래소는 미검증이다.

- **P0:** 물리 전송 직전 `read_binding`에서 보조 검증 종료 후 다시 전체 정책을 로드하던 generation 검사를 `reversal_evaluation_context.validate_submit(check_generation=True)`의 한 fresh 불변 뷰로 통합했다. 원 native generation validator·보조 registry/revocation 검사·뷰 종료 pointer 재검사는 모두 실행하며 provider/HTTP를 뷰 안에서 호출하지 않는다. 원 정책의 mutable 복사만 제거하고 AI PASS나 검증 verdict를 캐시하지 않는다.
- **실제 검사 clock:** 입장 wall clock에 해당 동기 검증의 monotonic 경과를 더해 느린 로드 후의 시각으로 원5초 조건을 검사한다. 원 오류 문자열은 유지하며 기존 pipeline 종료와 물리 전송 guard receipt에 입장/검사시각·원 signal epoch·bundle hash·load/총 경과를 전달한다. `runtime_performance`의 기존 bounded timing owner에 누락된 submit load/auxiliary/generation 이름을 등록한다.
- **P1:** `handle_watching_state` 완료 후 successor 재방문 연결을 fixed-watch에서 **scanner 비상시감시 Main까지** 확장한다. 기존 `rearm_native_watch_after_completion`만 재사용하며, exact item/route/native epoch/scope generation의 이미 관측된 미claim 새 신호와 원 wall/perf5초가 모두 유효해야 한다. WATCHING·pending/arm·COMMIT·custody 검사를 유지한다. 새 claim→새 AI 판정 경로를 다시 거치며 과거 PASS/원 deadline을 갱신하지 않는다. 퇴역 `entry_opportunity_recheck*` 경로는 복원하지 않는다.

**회귀와 성능 근거:** [기존 코드의 실패 재현](../../tmp/pre-submit-fresh-repair-20261023/original-defect-red.log)은 동일 새 비상시감시 정규장 통합 테스트가 successor 재방문에서 실패함을 보인다. 변경 후 원 claim/trace 유지와 새 신호의 독립 기한·cooldown 이전 새 claim을 검증했다. 누락/만료/세대·route/epoch 변경·revocation·뷰 종료 pointer 변경과 hard guard의 거절도 유지한다. 물리 영수증 테스트는 첫 작성에서 native 예외 반환형을 잘못 기대해 실패했으며 실제 `EntrySendGuardBlocked.receipt`를 검증하도록 테스트를 수정했다. guard 완화로 통과시키지 않았다.

[복사 구간 모의 측정](../../tmp/pre-submit-fresh-repair-20261023/copy-benchmark.json)은 현재6,073,747-byte bundle25회에서 중복 mutable 복사25→0, 해당 구간 중앙값47.18ms→0.017ms다. source validator/provider/order I/O를 mock한 **로컬 복사 비용 비교**이며 전체 실운영 지연·두산69ms 창 복원 또는 수익 개선을 증명하지 않는다. 새 원장·DB 복제·paid AI 호출은 없다.

| 기존 구현 | disposition | 현 소비자와 교체 |
|---|---|---|
| physical `read_binding`의 별도 전체-policy generation load | consolidated/removed | 동일 native validator를 fresh 불변 뷰 안에서 실행; 중복 load callsite 제거 |
| fixed-watch 전용 완료 후 successor 연결 | consolidated | 기존 scheduling owner를 fixed-watch/scanner가 공유; 새 queue/entrypoint 없음 |
| 기존 native/aux/source/TTL/owner/계좌/가격·수량/HTTP retry guards | retained | 첫 전송과 허용 retry의 기존 consumer 유지 |
| 기존 pipeline/physical receipt와 bounded stage timing | retained/extended | 원 오류/영수증 안에 검사 clock 보존; 별도 report producer 없음 |
| 원 정책·PREOPEN/strict 원문·과거 실패와 immutable release | retained | native 인계와 역사 재현에 필요; 새 정책 승격·기한 연장 없음 |

배포 준비는 Main preparation의 **독립 reviewed-code inventory**와 원본→현재 exact hash pairs도 함께 갱신한다. 지연·손절·보유 native 인계의 부분 혼합/변조는 허용하지 않는다. 최종 코드/문서 증감과 테스트·native parity·candidate P5·선택/PID 보존 결과는 [동일 실행 결과](../../tmp/pre-submit-fresh-repair-20261023/result.json)에 기록한다. candidate P5는 격리 정책 load/exit 증거이며 배포·새 PID 소비·자연 제출은 아니다.

자연 수용은 기존 `MainEntrySourceTerminalRepair1022` OPEN에서 이어간다. 실제 배포 후 정규장 exact `_AL`/SOR의 PASS→Main→자금→검증→첫HTTP/무전송 종료와, 새 native successor의 새 보조 결과 연결을 확인한다. 오늘 정규장 창을 넘기면 다음 거래일10/26 09:00~15:20에 확인하며 기존 AFTER 통합 경로 및 프리 명시 `_NX`/NXT 수용과 구분한다. 이 준비 작업은 배포/재기동이나 실제 주문을 요구하는 자연 수용을 닫지 않는다.

추가 리뷰에서 선택926 자체의 capability 회귀4건 실패도 [기존 릴리스에서 재현](../../tmp/pre-submit-fresh-repair-20261023/incumbent-capability-baseline.log)했다. 원 보고서와 현재 fixture는 적법하지만 latest reviewed generation 목록이 뒤처져 있었다. 기존 `policy_generation_code_handoff`의 original/source/consumed exact pairs를 현 fingerprint로 갱신하고, 실제 선택본의 상승·보유 fingerprint→후보만 추가로 허용했다. 현재 fixture와 원 fixture/report·원 source hash는 모두 필수다. 현재 프롬프트·임계값이나 역사 보고서 verdict를 바꾸지 않는다.

최종 회귀: 진입/스케줄러/물리/기동887 PASS, capability/격리 관련1691 PASS(12 deselected), 인계30 PASS(5584 deselected), 독립 inventory9 PASS. 중복 포함 수치를 한 개의 고유 테스트 합계로 제시하지 않는다. 원 stale-clock 결함도 [기존 함수 주입으로 실패 재현](../../tmp/pre-submit-fresh-repair-20261023/original-clock-red.log)했다. compile/diff와 문서 parser는 후보 고정 시 확인한다. 선택926 대비 비테스트 소스+108/-24, 테스트+166/-14이며 신규 Python 모듈·runtime entrypoint·report producer는0이다. 이 구현 자체의 owner 문서 증가는 audit·계획·checklist에 한정되고, 함께 들어가는 그전 canonical 진행 이력은 구현 성장과 구분한다. native 인계의 코드 목록과 terminal clock 전파 때문에 순증했으며 중복 전체-policy load와 전용 scanner 누락 분기는 제거/통합했다.


### 실제 부모 변경 후 통합 재리뷰 — 2026-10-23

준비 중 별도 ordered owner가11:55 실제 선택을 `a2ca8e7d8d6b77456b509f6f7133a6ba2911e562`로 전환했고 PID2333464/start36885727이 기동했다. 이 세션의 배포/재기동은0이다. 첫 후보766a1c3b3는 새 observer/P5·digest-cache·연구 저장소 수리를 포함하지 않으므로 **superseded/non-deployable**로 보존한다. 새 통합본은 a2의 실제 소스·코드 계약·회귀를 이어받는다.

첫 후보 P5는 원 intake에서 `entry_consumer_operator_market_generation_mixed:src/engine/sniper_state_handlers.py`로 실패했다. 후보 hash를 기존 현재 profile에 덮어써 Main preparation이 이전 소비 root를 재검증할 수 없었던 준비 코드 결함이다. 기존926와 a2의 완전한 profile은 **retained**하고, 새 제출 수리의 exact4-file 존재가 한 완전한 successor inventory를 선택하도록 기존 인계 owner에 연결했다. 부분 혼합은 거절한다. [원 후보 결함의 재현](../../tmp/pre-submit-fresh-repair-20261023/original-profile-red.log)과 이전 소비본/부분 혼합 회귀42 PASS로 검증했다. 원 P5 실패와 candidate receipt는 보존하며 임계값·경고 해제·stale PASS로 수리하지 않았다.

capability 통합도 a2의 현행 계약으로 정리했다. native `verified` 계열에는 오래된 historical successor 목록을 최신값으로 강제할 필요가 없으며, 원 소스22 보고서가 `unverified`인 상승/보유 계열만 정확한 original/source/실제 소비 세대→후보 쌍과 독립 current fixture를 검증한다. 첫 단계의4건 회귀 실패는 목록/테스트 기대의 불일치이며 현재 원 보고서의 훼손 증거가 아니다. 앞선 blanket latest-map 교체는 새 통합본에서 제거했다. `REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS`와 실제 소비 parent만 보완했고 unknown pair는 계속 unverified다.

a2 통합 회귀2301 PASS(진입/물리·native successor·capability·독립 기동·ordered 흐름), 인계42 PASS다. compile/diff·print-only backlog parser와 단일 current owner를 확인한다. 원 native5초/AI TTL·계좌/가격/수량·세대/revocation/포인터·Main/manual/retired custody는 동일하며 Main 변경을 허용하는 조건은 추가하지 않았다. 기존 code-only 인계는 native parity와 후보 P5로 다시 발급·확인한다.

공용 handler byte 변경에 따른 장후 trailing code-contract 불일치는 예상된 보고서 유효성 차단으로 남긴다. 원 source22/PREOPEN/holding/policy를 보존하고 기존 `main_trailing_source_reuse`의17,996,003-byte 미증명 범위(32MiB 상한) preflight를 통과했다. 필요한 재생성은 해당 봉인 입력/새 report namespace/독립 currentness 영수증에 한정한다. 새로운 원장 복제·AI/주문 호출·EOD/장후 전체 재실행은 없다. 후보 최종 검증·준비 상태와 정확한 commit/root는 같은 result.json에 기록한다.


### KRX listing eligibility and SOR preflight repair - 2026-10-23

- Scope/authority: user requested official KRX target/exclusion source repair, removal of obsolete trial approval gates, review and an integrated candidate. The subsequent instruction assigns non-NXT stocks to KRX. This does not change explicit source items/routes or assert a broker-verified actual venue. No deploy/restart/order is performed by this work.
- Incident: selected97a72d632/PID3606961/start38501423 inherited five fixed-watch ka10099 rows with KRX aftermarket=null. HPSP AI PASS `aims-98f0db4c82561ad1aff0` (16:34:12) reached Main but ended local `eligibility_unknown`, broker_order_attempted=false. A local request was not a broker rejection. The original diagnosis, rows and terminal hashes remain in `tmp/pre-submit-fresh-repair-20261023/integrated/aftermarket-eligibility-diagnosis-20261023.json`.
- First broken contract: ka10099 collection unconditionally wrote KRX aftermarket=null; the submit adapter additionally required a dated trial approval/runtime-policy file. Neither is the official KRX listing contract. The current producer/adapter now derive KRX product/reported-exclusion eligibility independently of NXT membership and let SOR consume a positively eligible venue without requiring both axes to be known. Unknown NXT stays null; explicit NXT still needs NXT=true.
- Official reference: Kiwoom HEAD953e5dbff123f437ab4d11a78a95191a685eb51f was rechecked before coding, including specs.py, core/client.py, packaged ka10099/ka10100/kt10000 and PRD/MOCK Postman requests. Retrieval16:56:44KST, exact paths/hashes: `tmp/aftermarket-eligibility-repair-20261023/official-reference.json`. No request schema, FID, continuation, auth or provider call changed. `nxtEnable` is NXT membership, not a KRX permission flag.
- [KRX official target/exclusion rules](https://regulation.krx.co.kr/contents/RGL/03/03010301/RGL03010301.jsp): current KOSPI/KOSDAQ stock listing scope is admitted; reported management, suspension, liquidation, 30-minute/overheat, warning/risk, abnormal-surge, very-low-liquidity, caution/attention states are excluded. ETF/ETN/out-of-scope markets and missing required source fields do not become permission. This is a local product/reported-status check, not certification of unreported dynamic close-time halts or no-regular-trade status; broker restrictions remain authoritative. Raw source hash/revision, current quote/account/quantity/custody/hard guards are preserved. Pre-2026-09-14 source contracts are not rewritten.
- Market identities: AFTER=`KRX_NXT_AFTERMARKET`; policy cohort=`KRX_NXT_INTEGRATED`; quote item=`<code>_AL`, route=`krx_nxt_integrated`; requested/effective broker route remainsSOR. NXT=false ordinary KRX stocks use KRX eligibility through SOR. Native actual execution venue remains unverified without an execution receipt. No extra subscription/reroute is used to manufacture acceptance.
- Integration: a separate session selected428f7ece3/PID3714195/start38663232 at16:52. This repair was rebased onto that deployed descendant, retaining its auxiliary-capability dependency group and every issued predecessor profile. The new complete reviewed inventory binds listing producer, adapter, handler, session contract and independent Main preparation; missing/dirty/mixed generations must fail. Native parity/P5 and final candidate reference are recorded below after validation.
- Replacement/removal: six obsolete canary/runtime-policy approval functions, four constants and their Main submit/provenance dispatches are removed (replacement: existing canonical listing source + native route preflight). No compatibility wrapper remains. Existing env-key retirement scrubbing is retained to prevent old shell authority from returning. Historical immutable approval/journal/release bytes are retained as evidence; no runtime approval file is read or generated by the new submit path.
- Validation so far:269 source/DB/session/order tests pass, including mocked collector->ORM->Main adapter->SOR request and exclusion/incomplete/wrong-symbol/stale/future negatives. New native-profile regressions and immutable startup validation are in progress; failed original attempts are retained. EOD test module's pre-existing import-time notifier/config/log initialization is not bypassed in production. No new report producer, provider budget or trading threshold is introduced. Code closure, candidate validation, actual deployment/PID consumption and natural terminal acceptance remain distinct.
- Existing owner:MainEntrySourceTerminalRepair1022. Following a separately authorized transition, verify the exact new PID's first listing-source receipt and same AFTER/_AL/SOR PASS->preflight->physical-send or local terminal; explicit _NX/NXT natural acceptance remains separate in the existing next-business-day window. No fill/profit is required to close this diagnostic repair.

- Review closure before candidate: core269 PASS; focused source/order/environment245 PASS; exact native successor/predecessor/independent-preparation81 PASS, with original9 failing profile attempts retained and repaired. Compile14 changed Python files, diff whitespace and print-only backlog parser PASS (one current owner). Non-test source192 additions/413 deletions (net-221); tests197 additions/193 deletions (net+4); docs23 additions before final receipt. No source/test module or new entrypoint was added. The old trial approval path is fully displaced.


### Current-release KRX/SOR integration and authorized deployment - 2026-10-23

User explicitly authorized integration over the current deployed release, iterative review/fixes, final deployment and restart. The new baseline is b7aeb7efcbeb6fdd0a0c4cd204d155ea804d7fcf, source-numeric-integrated-20261023-b7aeb7efc, PID3983639/start39020808. Its actual source flush, completed-bar, numeric/replay and interrupted-consumption repairs are retained. The former a12b56117 candidate, failed P5ffd34514 and absent old PID3714195 remain historical evidence; their failure is not assigned to this current PID. The complete AFTER listing inventory now extends REVIEWED_NUMERIC_REPLAY_PROFILE and independent Main preparation binds the exact merged handler and other source bytes. No policy, provider, quote/deadline/quantity/custody/hard-safety values are changed.

The merge was reviewed at each producer/consumer boundary. Business source changes retain the existing canonical listing collector and DB reader; no per-entry provider call or trial approval file is introduced. NXT=false ordinary KRX stocks use independent KRX product/reported-exclusion eligibility via unchanged SOR; unknown NXT remains null, direct NXT requires its own source, and actual exchange remains unverified without broker evidence. Removed six legacy SOR trial/runtime-policy functions and four constants remain removed; env retirement scrubbing and original historical artifacts remain retained. There is no new module, wrapper, report producer or order entrypoint. Exact missing/dirty/mixed code generations remain blocked while all consumed numeric/auxiliary/REST/holding profiles are retained.

Core source/session/order/environment/numeric tests387 PASS; actual ordered workflow/P5/boundary/deadline tests749 PASS, including lock/CAS, preparation callback, failure unwind and interruption negatives. Native full-generation and independent Main-inventory tests continue before immutable candidate creation. The final exact candidate then needs native parity, newly affected capability fixtures, active/delay/stop/holding gates and candidate P5; selected prepared P5 is a separate execute hook. Only after these pass will the approved ordered owner request graceful termination, publish selection, prepare, validate, start and attest. Current observer must be published before full health. Evidence: `tmp/aftermarket-eligibility-repair-20261023/integrated/`. Final commit/root, source/test/docs deltas, transition, PID and remaining natural acceptance are appended after actual verification.

Review closure for this integration: native generation/independent preparation/interrupted-consumption291 PASS; core387 PASS; ordered workflow/P5/deadline749 PASS; AST proves only the two intended Main handler functions changed versus b7aeb7efc, including unchanged physical-send context and WATCHING dispatch. Compile14 changed Python files, diff whitespace and one-current-owner print parser PASS. The seven non-test source owners consolidate the original gate rather than add a parallel path. No unresolved in-scope code finding remains before immutable candidate validation.

Supplemental review: candidate96a0c66a2 exposed deployment_trailing_report_not_current before any hold/drain. The unchanged-policy source-reuse owner admits only five preserved native proofs plus17,996,003 unproved bytes under its unchanged32MiB cap. Regeneration is limited to source22/target23 trailing in a fresh input/report namespace, with no AI, order, EOD or whole-postclose rerun. The shared handler also needs two exact historical-source/current-capability pairs; these are added to the existing successor table, preserving original reports/states and mandatory independent fixtures. Full source, contract, missing/modified code and authority negatives104 PASS; complete inventory expands to seven dependencies over the same numeric parent. Candidate96 and its evidence remain superseded/not deployable. Final validation runs against the new immutable commit.

### Submission monitor legacy preflight lineage repair - 2026-10-23

- Incident pin: selected `ea8a9ba85d36a3d2e262a36ffe137b0aa20c336b`, Main4156253/start39264285, actual release cwd and immutable selector confirmed. Original18:37:44 observer SHA `a57a0c1a413e131e89ddd2718a97056b22c7dfecf633d63afa597f1efb4aa793` and later18:56 observer are preserved in `tmp/submission-lineage-repair-20261023/`. Five identities for the affected attempt: AFTER / `KRX_NXT_INTEGRATED` / `000660_AL` integrated source / requested-effectiveSOR / broker execution venue unverified; it never submitted.
- First broken contract: `_historical_scanner_incident` accepted only `evaluation_role=main_live`, although the existing preflight producer (`ai_engine_openai.analyze_target` source-invalid branch -> `ai_decision_trace.capture_machine_observation`) deliberately captures a safe pre-adjudication legacy observation without a continuous-reversal consumption claim. Exact `aims-b3bb87cf6fca428c8c7b`, captured18:22:22.181719 by previous Main3983639/start39020808, has a valid original observation hash, six-field identity, same bundle and native process clock. Its original budget0.166ms expired during input copy (after-freeze−20.746ms). The deadline guard correctly stopped before provider/order; optional `program/investor` missing fields do not prove the cause. Monitor first_seen18:36 is aggregation time, not current-PID decision time.
- Repair: extend the existing historical membership reader to this exact source-invalid schema/action/reason and legacy role, requiring false provider/order/runtime/apply flags, true broker prohibition, no native consumption claim, same-date immutable hash/identity/bundle and strictly older actor/birth. Preserve every original incident, status, source error and null economics. No forced recovery, native policy-consumption receipt, timeout/guard/threshold change or new provider/order call. The18:37 frozen reproduction changes FAIL eligibility to bounded WARNING only; current observation and full coverage remain false. The natural19:03 scheduled health already had FAIL0 after report coverage advanced, confirming recurrence depends on partial report state rather than persistent current broker failure.
- Replacement/removal: existing role-only predicate is replaced in place; capture producer, six-field identity reader, source alert, health consumer and original historical evidence are retained with their current consumers. No new module, producer, validator, wrapper or duplicate tracking owner. The new exact reviewed profile extends the complete consumed KRX/listing generation; independent Main preparation binds the same original/current source pair. Earlier profiles remain usable only as complete issued generations.
- Review and validation: focused historical/negative218PASS; full affected monitor/detector/handoff/preparation suites and ordered/P5 sequence validation are recorded below when complete. Original failure, source bytes and failed invocation (private worktree DATA_DIR rather than native selected root) remain preserved; selected-native checklist preservation succeeded. Test and natural deployment/PID evidence remain distinct. Source-only diagnosis reads small frozen reports and the existing bounded native observation; no raw pipeline whole-file scan.
- Baseline/scope: actual selected commit `ea8a9ba85`; source changes are existing monitoring historical membership and exact deployment/preparation inventories, tests reuse current fixtures. Additions/deletions and final immutable candidate/PID/health are recorded in this same review after validation.

- Re-review: only `_historical_scanner_incident` changed in the monitor AST; trading producer/guards and the health consumer are unchanged. Source3files +67/−3 (net64, mostly exact source-generation registration); tests3files +82/−3 (existing fixture matrix and negative safety/current-actor cases); docs3files initially +12/−0. Net source growth is explicit legacy membership support and complete native handoff inventory, with no new runtime entrypoint. Broad four-file validation stopped after4,677PASS/zero failures because old profile cross-products wrote6.9GB of private test data; this is an interrupted run, not a full-suite PASS. The complete monitor+detector population is1,903tests, collected separately and executed before that interruption. Bounded current/consumed-listing/negative handoff validation35PASS; four unchanged native capability fixtures independently verify. Remaining selected startup/P5/ordered failure-sequence tests are recorded below.

- Closed code review: bounded handoff35PASS; independent Main preparation/P5/ordered transition and lock/failure-unwind928PASS. Monitor/detector1,903tests had completed in the preserved interrupted broad run. Six changed Python files compile, diff check passes, current parsed checklist owner is exactly1, four unchanged capability fixtures pass. No unresolved in-scope code finding; candidate native parity/P5 and authorized actual deployment/consumption follow separately.
