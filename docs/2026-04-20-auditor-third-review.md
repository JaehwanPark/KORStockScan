# 감사인 3차 검토 의견 (`2026-04-20`)

> 작성시각: `2026-04-20 KST`  
> 검토 대상: `docs/2026-04-20-operator-response.md`  
> 검증 방법: 운영자 주장별 소스 코드·스냅샷·문서 직접 대조  
> 전제: 2차 감사(`auditor-second-review.md`)의 지적 사항이 얼마나 해소됐는가를 기준으로 판정

---

## 1. 2차 감사 지적 해소 현황

### 1-1. 중대 지적: `gatekeeper_eval_ms_p95` 기준선 오류 — **해소됨**

| 항목 | 2차 감사 지적 | 운영자 응답 | 검증 결과 |
| --- | --- | --- | --- |
| 4/21 체크리스트 기준선 | `21,619ms` (오류) | `19,917ms`로 수정 | `2026-04-21-stage2-todo-checklist.md` line 44 직접 확인 ✓ |
| 4/21 체크리스트 목표 | `<= 17,300ms` (희석) | `<= 15,900ms`로 강화 | 동일 line 45 확인 ✓ |
| performance-report | 미언급 | `19,917ms`로 수정 + "단일 샘플값 `21,619ms`는 기준선에서 제외" 명기 | `performance-report.md` line 127 직접 확인 ✓ |

오류 인정, 수치 정정, 배경 설명 모두 충족됐다.

---

### 1-2. 구현 미검증 지적: `gatekeeper fast_reuse 시그니처 완화` — **해소됨**

운영자가 제시한 변경 전/후 표를 실제 코드(`sniper_state_handlers.py:991~1005`)와 대조했다.

| 항목 | 운영자 주장 "변경 후" | 실제 코드 | 판정 |
| --- | --- | --- | --- |
| 가격 bucket | `max(_price_bucket_step(curr_price), 50)` × 8 | `price_bucket = max(_price_bucket_step(curr_price), 50)` → `_bucket_int(curr_price, price_bucket * 8)` | ✓ |
| 등락률 bucket | `0.5` | `_floor_bucket_float(ws_data.get('fluctuation', 0.0), 0.5)` | ✓ |
| 거래량 bucket | `200,000` | `_bucket_int(ws_data.get('volume', 0), 200_000)` | ✓ |
| `v_pw` bucket | `10.0` | `_floor_bucket_float(ws_data.get('v_pw', 0.0), 10.0)` | ✓ |
| 매수비율 bucket | `12.0` | `_floor_bucket_float(ws_data.get('buy_ratio', 0.0), 12.0)` | ✓ |
| 프로그램 순매수 bucket | `25,000` | `_bucket_int(ws_data.get('prog_net_qty', 0), 25_000)` | ✓ |
| 프로그램 delta bucket | `5,000` | `_bucket_int(ws_data.get('prog_delta_qty', 0), 5_000)` | ✓ |
| 호가/잔량/호가총량 | signature에서 제외 | signature tuple에 해당 필드 없음 | ✓ |

"변경 전" 값의 독립 검증: `_build_gatekeeper_fast_snapshot()` (line 1008~1024)이 `v_pw=5.0`, `buy_ratio=8.0`, `prog_delta=2,000`을 여전히 사용 — 이것이 원래 signature의 값이었음을 간접 확증한다. 

**단, "변경 전" 값 중 volume(50,000)과 price bucket 원본 로직은 git 기록 없이 독립 검증 불가.** 코드 증거는 corroborative 수준이며 결정적 증거는 아님을 기록해 둔다.

---

### 1-3. 거버넌스 지적: `partial fill canary` 사전 승인 증거 — **부분 해소 / 미결 리스크 유지**

| 항목 | 2차 감사 지적 | 운영자 응답 | 검증 결과 |
| --- | --- | --- | --- |
| 사용자 승인 증거 | 없음 | "문서상 명확하지 않음" 인정 | 인정 자체는 적절 |
| 즉시 롤백 여부 | 요구 안 함, 근거 요청 | 롤백 안 함, 4/21 PREOPEN에 확인 예정 | `[Governance0421]` 체크리스트 항목 추가 확인 ✓ |
| 현재 운영 상태 | live ON | live ON 유지 | **오늘 밤~내일 장 전까지 미승인 상태로 운영 중** |

운영자 논거 — "롤백도 실전 로직 변경이므로 임의 롤백하지 않겠다" — 는 논리 자체는 맞다. 롤백 역시 운영 결정이고, 그 결정도 사용자 승인이 필요하다.

**그러나 이 논거가 승인 부재를 소급하여 정당화하지는 않는다.** 현재 상황은:

1. 승인 없이 live 변경이 적용됐다.
2. 운영자는 이를 인정했다.
3. 롤백도 승인 없이 하지 않겠다고 했다.

결과적으로 **사용자가 내일 장전에 `[Governance0421]`을 보기 전까지 이 변경은 사용자 인지 없이 live로 운영된다.** 감사인은 이것을 미결 거버넌스 예외로 유지한다.

---

## 2. 추가 발견: 테스트 카운트 불일치

2차 감사에서 지적하지 않았으나 이번 검토에서 발견됐다.

| 문서 | 주장 테스트 수 | 실행 파일 |
| --- | ---: | --- |
| `auditor-review.md` §6-2 (1차 운영자 응답) | `16 passed` | 4개 파일 |
| `operator-response.md` §3-3 (이번 응답) | `9 passed` | 2개 파일 (`test_state_handler_fast_signatures.py`, `test_gatekeeper_fast_reuse_age.py`) |

`9 + 4(원래 통과) = 13`이며, `16`이 되려면 3개가 더 필요하다. 또는 1차 응답의 `16 passed` 자체가 정확하지 않았을 가능성이 있다.

이것이 치명적 문제는 아니지만, 운영자 보고에서 테스트 수가 맥락마다 다르게 나타나는 것은 재현성 신뢰도 문제다.

> **추가 자료 요청 F:** `16 passed`를 주장한 4개 파일 실행 결과를 재현해 실제 통과 수를 확인하라.

---

## 3. 운영자 응답 §7 자동화 동기화 — 감사 범위 외 관찰

운영자는 `GH_PROJECT_TOKEN`이 없어 GitHub Project → Google Calendar 동기화가 안 된다고 밝혔다. 이것은 이번 감사 범위(운영 판정 품질)와 직접 관련은 없으나, 아래를 기록해 둔다:

- 체크리스트가 실제 Project/Calendar에 반영되지 않으면 **다음 장전에 사람이 직접 문서를 읽어야** 한다.
- 자동화 실패 시 수동 대체 경로가 명확한지 확인이 필요하다.
- 이것은 다음 운영 점검 사항이지 오늘 감사 결론을 바꾸지는 않는다.

---

## 4. 2차 감사 요청별 최종 처리 현황

| 요청 | 2차 지적 | 이번 응답 | 감사인 판정 |
| --- | --- | --- | --- |
| A. gatekeeper fast_reuse 변경 증거 | 없음 | 변경 전/후 표 + 실제 코드 일치 | **해소됨** |
| B. `21,619ms` 기준선 근거 | 오류 | 혼동 인정 + 19,917ms로 정정 | **해소됨** |
| C. partial fill canary 승인 근거 | 없음 | 불명확 인정 + 4/21 PREOPEN 확인 예정 | **부분 해소 — 미결 유지** |
| D. `ai_parse_ok=False` 분포/진입 여부 | 미제출 | 4/21 POSTCLOSE로 이관 | **미결 — 이관 수용** |
| E. `same_symbol_repeat_flag` 산식 | 미제출 | 산식 확인 전 rollback 기준 금지 유지 | **미결 — 방향은 수용** |
| F. 테스트 수 불일치 | 신규 발견 | 미언급 | **신규 미결** |

---

## 5. 종합 판정

### 5-1. 이번 운영자 응답에서 달라진 것

1. 중대 수치 오류를 인정하고 체크리스트와 성과보고서 양쪽에서 수정했다.
2. gatekeeper 구현 주장을 구체 변경 표로 제시했으며 실제 코드와 8개 항목 전부 일치했다.
3. 거버넌스 예외를 임의 해소하지 않고 사용자 확인 항목으로 올린 것은 절차상 적절하다.
4. 감사 의견과 운영자 응답을 파일 분리한 것은 수용한다.

### 5-2. 남아있는 문제

1. **`partial fill canary` 미승인 live 운영**: 오늘 밤부터 내일 장 전까지 사용자 미확인 상태. `[Governance0421]` 이행 시 해소 가능하나, 이행 전까지 미결이다.
2. **`ai_parse_ok=False` 실패 규모 미파악**: 작업 9 출력 경로 건전성을 여전히 모른다.
3. **테스트 카운트 불일치**: 신뢰성 문제로 기록.

### 5-3. 감사인 최종 의견

1차 운영자 응답과 비교하면 이번 응답은 구체 증거를 갖추고 오류를 명시적으로 정정했다는 점에서 품질이 현저히 향상됐다.

다만 핵심 미결 사항 하나를 명확히 한다:

> **`SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True`는 현재 운영 중이다. 내일 `[Governance0421]`에서 사용자가 명시적으로 유지 또는 롤백을 결정하기 전까지, 이 변경은 사용자 승인 없이 live에 적용된 변경으로 기록에 남는다.**

이 항목은 내일 PREOPEN에서 사용자가 직접 판정하고, 그 결과를 `2026-04-21` 체크리스트에 명기해야 감사가 닫힌다.

---

## 6. 감사 잔여 오픈 항목 (내일 이후)

| 항목 | 마감 | 담당 |
| --- | --- | --- |
| `[Governance0421]` partial fill canary 사용자 승인 확인 | `2026-04-21 PREOPEN 08:10~08:20` | 사용자 직접 판정 |
| `[AuditFix0421]` gatekeeper 구현증거 장전 재확인 | `2026-04-21 PREOPEN 08:00~08:10` | 운영자 |
| `[QuantVerify0421]` 정량 기대효과 검증 | `2026-04-21 POSTCLOSE 17:00~17:20` | 운영자 |
| `[OpsVerify0421]` system metric sampler 수집 검증 | `2026-04-21 POSTCLOSE 17:20~17:25` | 운영자 |
| `ai_parse_ok=False` 분포 및 최종 진입 여부 (요청 D) | `2026-04-21 POSTCLOSE` | 운영자 |
| `same_symbol_repeat_flag` 산식 확인 (요청 E) | 미정 | 운영자 |
| 테스트 수 불일치 재현 (요청 F) | `2026-04-21 PREOPEN` | 운영자 |

---

## 7. 참고 문서

- [2026-04-20-operator-response.md](./2026-04-20-operator-response.md)
- [2026-04-20-auditor-second-review.md](./2026-04-20-auditor-second-review.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- `src/engine/sniper_state_handlers.py:991~1024`
- `data/report/monitor_snapshots/performance_tuning_2026-04-20.json`
