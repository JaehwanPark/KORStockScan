# 감사인 2차 검토 의견 (`2026-04-20`)

> 작성시각: `2026-04-20 KST`  
> 검토 대상: `docs/2026-04-20-auditor-review.md` §6 "감사 의견에 대한 운영 응답"  
> 검증 방법: 주장된 구현 내용을 소스 코드·스냅샷·크론 설정과 직접 대조  
> 작성 원칙: 주장(claim) vs. 검증 결과(evidence)를 분리 기록

---

## 0. 검토 범위 및 구조 선결 문제

### 0-1. 이 문서가 가진 구조적 결함

`2026-04-20-auditor-review.md`는 §1~5(감사인 의견)와 §6(운영자 응답)이 **단일 파일**에 혼재한다.

| 문제 | 내용 |
| --- | --- |
| 감사 독립성 훼손 | 피감사자 응답이 감사 의견서 내부에 포함되어, 어디까지가 감사인 의견이고 어디부터가 운영자 응답인지 독립적으로 추적 불가 |
| 버전 관리 불명확 | §6이 언제, 누구에 의해 추가됐는지 파일 내 증거 없음. git log 외에는 판별 불가 |
| 향후 참조 혼란 | 다음 체크리스트와 보고서에서 이 파일을 참조할 때 운영자 주장이 감사 결론처럼 읽힐 위험 |

**권고:** 운영자 응답은 별도 파일(`2026-04-20-operator-response.md`)로 분리해야 한다. 이번 2차 검토는 §6 내용을 운영자 응답으로 간주하고 진행한다.

---

## 1. 구현 주장 vs. 실제 코드 검증

### 1-1. `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED` — **확인됨**

| 항목 | 주장 | 실제 |
| --- | --- | --- |
| 상수 존재 | `True` | `constants.py:147` `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED: bool = True` ✓ |
| `default=0.20` | 기준값 | `constants.py:148` `SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT: float = 0.20` ✓ |
| `strong_absolute_override=0.10` | 예외 | `constants.py:149` `SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE: float = 0.10` ✓ |

구현 자체는 확인됐다. 단, **거버넌스 문제**가 남는다(§2 참조).

---

### 1-2. `gatekeeper fast_reuse 시그니처 완화` — **구현 내용 불명확**

운영자는 "gatekeeper fast_reuse 시그니처 완화"를 오늘 구현했다고 주장했다.

**실제 코드 확인 결과:**

- `_build_gatekeeper_fast_signature()`: `sniper_state_handlers.py:991`에 존재하나 오늘 변경된 흔적을 확인할 수 없음
- `_resolve_gatekeeper_fast_reuse_sec()`: `sniper_state_handlers.py:986` — `max(configured_sec, 20.0)` 하한이 하드코딩되어 있음
- `constants.py`에서 `gatekeeper_fast_reuse` 관련 신규 상수: **없음** (grep 결과 0건)

**결론:** "시그니처 완화"가 어디에 어떻게 적용됐는지 코드 증거가 없다. 운영자는 구체적으로 어떤 파라미터 또는 로직을 변경했는지 제시해야 한다.

> **추가 자료 요청 A:** gatekeeper fast_reuse 시그니처 완화의 구체적 변경 내용(파일명, 변경 전/후 코드)을 제출하라.

---

### 1-3. `system_metric_sampler` — **파일 존재, cron 설치 확인, 실제 수집 미검증**

| 항목 | 주장 | 실제 |
| --- | --- | --- |
| `src/engine/system_metric_sampler.py` 존재 | ✓ | 확인됨 ✓ |
| 1분 주기 cron 설치 | ✓ | `crontab -l` 결과 `* * * * 1-5 ...run_system_metric_sampler_cron.sh` 확인됨 ✓ |
| 오늘 09:00~15:30 수집 여부 | 묵시적 주장 | **불가능**: 장후 설치 시 오늘 장중 데이터는 없음 |
| 내일 장중 수집 여부 | 내일 검증 예정 | 미검증 — 4/21 POSTCLOSE에서 `[OpsVerify0421]` 항목으로 확인 예정 ✓ |

cron 설치 자체는 확인됐다. 단, 4/21 체크리스트의 `[OpsVerify0421]` 판정 기준 (`09:00~15:30 >= 360건, 최대 간격 <= 180초`)으로 실제 수집 완전성을 내일 검증해야 한다.

---

### 1-4. `execution-delta.md` TRADING_RULES 통제 규칙 추가 — **확인됨**

`plan-korStockScanPerformanceOptimization.execution-delta.md` 기준:

- §1 (판정) line 6: `TRADING_RULES 운영 상수, 특히 모델명/투자비율/주문한도/실전 canary 스위치는 요청 범위를 넘겨 바꾸지 않는다. 변경 필요 시 사용자 명시 승인과 롤백 조건을 먼저 기록한다.` ✓
- §2 (변경사항 표) line 37: `운영 상수 변경 통제` 항목 추가됨 ✓

이것은 운영자 주장대로 반영됐다.

---

### 1-5. `2026-04-21-stage2-todo-checklist.md` 감사 응답 검증 항목 추가 — **확인됨**

- `[AuditResponse0421]`: 감사 응답 반영 상태 검증 ✓
- `[QuantVerify0421]`: 정량 기대효과 검증 ✓
- `[OpsVerify0421]`: system metric sampler 장중 coverage 검증 ✓

추가됐다. 단, **`[QuantVerify0421]`의 기준선 수치 오류**가 그대로 전파됐다(§2 참조).

---

## 2. 중대 지적: `gatekeeper_eval_ms_p95` 기준선 수치 오류

### 2-1. 사실 관계

운영자 응답 §6-3과 `2026-04-21-stage2-todo-checklist.md` `[QuantVerify0421]` 항목에 다음 기준선이 사용됐다:

> `gatekeeper_eval_ms_p95=21,619ms`

**실제 `performance_tuning_2026-04-20.json` 공식 집계 p95:**

```json
"gatekeeper_eval_ms_p95": 19917.0   ← 공식 집계값
```

**21,619ms의 출처:**

```json
# performance_tuning_2026-04-20.json 내 개별 거래 로그 (종목코드 192400)
"gatekeeper_eval_ms": 21619         ← 단일 거래 샘플값
```

### 2-2. 오류의 영향

운영자는 p95 집계값(`19,917ms`) 대신 특정 종목의 단일 샘플 최댓값(`21,619ms`)을 기준선으로 썼다.

| 항목 | 올바른 기준선 | 잘못된 기준선 | 차이 |
| --- | ---: | ---: | ---: |
| 기준선 | `19,917ms` | `21,619ms` | `+1,702ms` (+8.5%) |
| 20% 개선 목표 | `~15,934ms` | `17,300ms` | 목표 `1,366ms` 완화 |

**왜 중요한가:** 기준선을 높게 잡으면 동일한 구현으로도 목표를 더 쉽게 달성한 것처럼 보인다. 이것이 의도적이든 실수든, 성과 측정 기준이 잘못됐다.

### 2-3. 즉시 조치 요구

1. `2026-04-21-stage2-todo-checklist.md` `[QuantVerify0421]` 항목의 `gatekeeper_eval_ms_p95=21619ms`를 `19917ms`로 수정해야 한다.
2. 따라서 목표값도 `<= 17,300ms` → `<= 15,900ms` (또는 타당한 임계값으로)로 재설정해야 한다.

> **추가 자료 요청 B:** 21,619ms를 기준선으로 선택한 근거를 설명하라. 개별 샘플값과 p95 집계값을 혼동한 것이라면 해당 오류를 인정하고 체크리스트를 수정하라.

---

## 3. 거버넌스 지적: partial fill canary 사용자 승인 증거 없음

원래 `2026-04-20-postclose-audit-result-report.md` §3-5 RCA 섹션의 "제한" 항목:

> "workorder에 따라 이 결론은 사용자 승인 전 자동 반영 완료로 보면 안 된다."

그러나 `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True`는 이미 `constants.py`에 반영되어 있고, 이를 운영자가 오늘 구현했다고 기술하고 있다.

**문제:** 이 변경이 운영자 자신이 판단하여 독자적으로 반영한 것인지, 아니면 사용자(시스템 오너)의 명시적 승인을 받은 것인지 문서상 증거가 없다.

감사인 1차 의견에서 지적한 "TRADING_RULES 변경 시 명시적 사용자 확인 필수" 원칙이, 정작 이번 운영자 응답에서 지켜졌는지 불분명하다.

> **추가 자료 요청 C:** `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True` 반영 전 사용자 승인을 어떤 형태로 받았는지 기록 또는 대화 맥락을 제시하라.

---

## 4. 운영자 응답 항목별 최종 검증 판정

| 항목 | 운영자 주장 | 감사인 검증 | 판정 |
| --- | --- | --- | --- |
| partial fill canary 상수 구현 | 확인 | `constants.py:147~149` 확인 | **확인됨** — 거버넌스 문제 별도 |
| gatekeeper fast_reuse 시그니처 완화 | 구현 완료 | 관련 상수 변경 없음, 코드 변경 증거 불명 | **미검증 — 근거 요청** |
| OpenAI parse fallback 강건화 | 구현 완료 | 파일 존재 확인이나 오늘 변경 여부 별도 검증 필요 | **부분 확인** |
| system_metric_sampler cron 설치 | 1분 주기 수집 | cron 설치 확인, 실제 수집은 4/21에 검증 예정 | **설치 확인, 수집 미검증** |
| execution-delta TRADING_RULES 통제 추가 | 추가 완료 | 문서 확인됨 | **확인됨** |
| 4/21 체크리스트 감사 응답 검증 항목 추가 | 추가 완료 | 항목 존재 확인됨 — 단, 기준선 수치 오류 전파 | **확인됨 — 수치 오류 수정 필요** |
| gatekeeper_eval_ms_p95 기준선 | `21,619ms` | 공식 p95는 `19,917ms`. 단일 샘플 최댓값 사용 | **오류 — 즉시 수정 요구** |
| 타임스탬프 분리 약속 | 4/21부터 적용 | 수용 선언, 이행 여부는 4/21 검증 | **약속만 확인** |

---

## 5. 추가 자료 요청 (종합)

| # | 요청 자료 | 사유 |
| --- | --- | --- |
| A | gatekeeper fast_reuse 시그니처 완화의 구체적 변경 내용 (파일·라인·전후 비교) | 구현 주장 미검증 |
| B | `gatekeeper_eval_ms_p95=21,619ms`를 기준선으로 선택한 근거 | p95 집계값과 단일 샘플값 혼동 여부 확인 |
| C | `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True` 반영 전 사용자 승인 기록 또는 근거 | 운영 통제 원칙 준수 여부 |
| D | *(기존 1차 요청 유지)* `ai_parse_ok=False` 표본 시간대별 분포 및 해당 케이스 최종 진입 여부 | 작업 9 출력 경로 실패 규모 판정 |
| E | *(기존 1차 요청 유지)* `same_symbol_repeat_flag` 계산 원본 쿼리 또는 산식 | hard KPI 복귀 여부 재판정 |

---

## 6. 총평

운영자 응답은 감사 지적을 형식적으로는 수용했고, 일부 항목(TRADING_RULES 통제 문서화, 4/21 체크리스트 갱신)은 실제로 반영됐다.

그러나 두 가지 본질적 문제가 남는다.

**첫째**, `gatekeeper_eval_ms_p95` 기준선 수치 오류는 단순 실수라면 즉시 수정해야 하고, 만약 의도적으로 달성 용이한 목표를 설정한 것이라면 성과 측정 체계 전반의 신뢰도 문제로 번진다. 어느 쪽이든 4/21 체크리스트가 이 오류를 품은 채 실행되면 내일 검증 결과의 의미가 없다.

**둘째**, gatekeeper fast_reuse 시그니처 완화의 구현 근거가 없다. 이 변경이 없다면 내일 `gatekeeper_fast_reuse_ratio >= 10.0%` 목표는 달성 불가다.

감사인 권고는 다음 두 가지로 요약한다:

1. **즉시:** `2026-04-21-stage2-todo-checklist.md` `[QuantVerify0421]` 기준선을 `gatekeeper_eval_ms_p95=19,917ms`로 수정한다.
2. **내일 장전 전:** gatekeeper fast_reuse 완화 구현 내용을 확인하거나, 미구현이면 해당 목표(`>= 10.0%`)를 `2026-04-21` 판정 대상에서 제외하고 보류 사유를 기록한다.

---

## 7. 참고 문서

- [2026-04-20-auditor-review.md](./2026-04-20-auditor-review.md)
- [2026-04-20-postclose-audit-result-report.md](./2026-04-20-postclose-audit-result-report.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- `data/report/monitor_snapshots/performance_tuning_2026-04-20.json`
- `src/utils/constants.py`
- `src/engine/sniper_state_handlers.py`
- `src/engine/system_metric_sampler.py`
- `deploy/install_stage2_ops_cron.sh`
