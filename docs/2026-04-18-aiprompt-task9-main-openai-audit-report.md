# 2026-04-18 AIPrompt 작업 9 메인(OpenAI) 이식 감리 결과보고서

## 1) 판정

- 판정: `적합(조건부)`  
  `작업 9 정량형 수급 피처 이식 1차`는 메인 서버 스캘핑 실경로(OpenAI)까지 반영됐다.
- 범위:
  - 공통 정량 피처 패킷 helper 공유 (`Gemini/OpenAI`)
  - 메인 OpenAI `analyze_target()` 반환값에 감사 필드 직접 주입
  - HOLDING/ENTRY 파이프라인 로그 경로에서 감사 필드 노출 가능 상태 확인

## 2) 근거

### 코드 반영 근거

- OpenAI 분석 경로 감사 필드 주입:
  - `src/engine/ai_engine_openai_v2.py`
  - `result.update(build_scalping_feature_audit_fields(features))` 추가
- 공통 helper:
  - `src/engine/scalping_feature_packet.py`
  - `extract_scalping_feature_packet()`, `build_scalping_feature_audit_fields()` 사용
- 로그 필드 반영:
  - `src/engine/sniper_state_handlers.py`
  - `_build_ai_ops_log_fields()`가 `scalp_feature_packet_version`, `*_sent` 필드를 통과시킴

### 테스트/검증 근거

1. OpenAI 감사 필드 회귀 테스트
   - 명령: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_openai_v2_audit_fields.py`
   - 결과: `1 passed`
2. 기존 관련 회귀 재확인
   - 명령: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalping_feature_packet.py src/tests/test_ai_engine_cache.py src/tests/test_realtime_gatekeeper_packet.py`
   - 결과: `18 passed`
3. 컴파일 검증
   - 명령: `.venv/bin/python -m py_compile src/engine/scalping_feature_packet.py src/engine/ai_engine.py src/engine/ai_engine_openai_v2.py src/engine/sniper_state_handlers.py`
   - 결과: 통과
4. 원격 서버 반영/검증 (`2026-04-18 10:56 KST`)
   - 대상: `windy80xyt@songstockscan.ddns.net:/home/windy80xyt/KORStockScan`
   - 반영 파일: `src/engine/scalping_feature_packet.py`, `src/engine/ai_engine.py`, `src/engine/ai_engine_openai_v2.py`
   - 안전조치: `tmp/backup_task9_20260418_105552/`에 원격 원본 백업 후 파일 동기화
   - 검증: 원격 `.venv/bin/python -m py_compile ...` 통과, `bot_main.py` 실행 프로세스 없음(즉시 재기동 불필요)

## 3) 리스크 및 제한

- `main` 런타임에서 OpenAI API 키가 없거나 라우터가 `remote`로 뜨면 해당 반영은 실시간 경로에서 비활성화될 수 있다.
- 본 보고는 `코드/테스트` 기준이며, 장중 실표본에서 감사 필드 누락이 없는지 추가 확인이 필요하다.

## 4) 다음 액션

### 4-1) 실행 Plan (2026-04-20 POSTCLOSE)

1. `15:40~15:50` 라우팅/감사필드 실표본 확인
2. `15:50~16:00` OpenAI 모델 식별자 유효성 확인
3. `16:00~16:10` 작업 6/7 보류 유지 또는 착수 전환 재판정
4. `16:10~16:20` 판정 결과를 `2026-04-20-stage2-todo-checklist.md`와 본 보고서에 역기록

### 4-2) 체크리스트 (자동 파싱 대상)

- [ ] `[AuditFollowup0418] main runtime OPENAI 라우팅/감사필드 실표본 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 판정 기준: `ai_holding_review` 또는 `ai_confirmed` 이벤트에서 `scalp_feature_packet_version`, `tick_acceleration_ratio_sent`, `same_price_buy_absorption_sent`, `large_sell_print_detected_sent`, `ask_depth_ratio_sent`가 1건 이상 확인됨
  - 실행 명령 예시: `rg -n "stage=ai_confirmed|stage=ai_holding_review" logs/pipeline_event_logger_info.log* -S | rg "scalp_feature_packet_version|tick_acceleration_ratio_sent|same_price_buy_absorption_sent|large_sell_print_detected_sent|ask_depth_ratio_sent"`
  - 다음 액션: 누락 시 `RuntimeAIEngineRouter` 분기/`analyze_target` 반환 경로를 우선 점검
- [ ] `[AuditFollowup0418] main runtime OpenAI 모델 식별자 검증/수정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - 판정 기준: `kiwoom_sniper_v2.py`의 메인 OpenAI 모델명이 실제 사용 가능한 식별자로 확인되거나 수정됨
  - 실행 명령 예시: `rg -n "set_model_names\\(|gpt-5\\.4-nano|gpt-5-nano" src/engine/kiwoom_sniper_v2.py src/engine/ai_engine_openai_v2.py`
  - 다음 액션: 미확인 시 `gpt-5.4-nano` 유지 금지, 실제 호출 에러와 함께 교정
- [ ] `[AuditFollowup0418] 작업 6/7 보류 유지 또는 착수 전환 재판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 판정 기준: `HOLDING action schema shadow-only` 선행 범위와 충돌 없이 착수 가능 여부 확정
  - 다음 액션: 보류 유지 시 `다음 실행시각`을 같은 문서와 `2026-04-20-stage2-todo-checklist.md`에 동시에 기록

### 4-3) 사이징 리스크 단일축 기록 (자동 파싱 대상)

- [ ] `[RiskSize0420] SCALPING_MAX_BUY_BUDGET_KRW=1,600,000 단일축 canary 적용` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`)
  - 판정 기준: `src/utils/constants.py` 반영 + 런타임 기동 후 신규 진입 예산 계산에서 cap 값이 1,600,000으로 확인됨
  - 다음 액션: 미반영 시 배포 경로/재기동 순서를 먼저 점검하고, 추정 손익 비교는 반영 확인 후 진행
- [ ] `[RiskSize0420] 비중/예산 상수 동적 튜닝 대상화 여부 확정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:35`, `Track: Plan`)
  - 판정 기준: `INVEST_RATIO_SCALPING_MIN/MAX`, `SCALPING_MAX_BUY_BUDGET_KRW`를 동적 튜닝 큐에 올릴지 승격/보류 중 하나로 확정
  - 다음 액션: 보류 시 원인과 재시각을 `2026-04-20-stage2-todo-checklist.md`에 동시 기록

## 5) 코드베이스 실측 리뷰 (2026-04-18)

> 실제 소스 파일을 직접 열람하여 작업 9 이식 정확도를 검증한 결과다.

### 5-0) 메인 런타임 라우팅 확인 — **조건부 타당 (재검토 반영)**

- `src/engine/kiwoom_sniper_v2.py:1085`에서 메인 런타임은 `RuntimeAIEngineRouter`를 구성한다.
- `src/engine/runtime_ai_router.py:56~70` 기준 아래 **3개 조건 동시 충족 시** `openai_scalping_engine.analyze_target()` 로 라우팅된다:
  1. `runtime_role == "main"`
  2. `strategy in {"SCALPING", "SCALP"}`
  3. **`openai_scalping_engine is not None`** ← 재검토에서 추가 확인된 필수 조건

- `openai_scalping_engine` 초기화 분기 (`kiwoom_sniper_v2.py:1058~1070`):
  - `OPENAI_API_KEY` 미설정 → `openai_scalping_engine = None` → **Gemini로 silent fallback**
  - `GPTSniperEngine` 초기화 예외 발생 → 동일하게 `None` → Gemini fallback

> **판정 (수정)**: 라우팅 전제는 `OPENAI_API_KEY 설정 완료 + GPTSniperEngine 초기화 성공` 시에 한해 타당하다.  
> 미충족 시 Gemini 경로에서 감사 필드가 생성되며, OpenAI 이식 효과는 비활성화된다.  
> 이는 섹션 3) 리스크와 동일 사항으로, 기존 `AuditFollowup0418` 실표본 확인 액션으로 커버된다.

#### 추가 관찰: OpenAI 모델명 검증 필요 ℹ️

`kiwoom_sniper_v2.py:1062`에서 fast/deep/report 모두 `gpt-5.4-nano`로 고정.  
`2026-04-18` 공식 OpenAI 모델 문서 기준 공개 식별자에는 `gpt-5-nano`가 보이며 `gpt-5.4-nano`는 확인되지 않았다.  
따라서 실제 OpenAI API 호출 시 모델 인식 실패 가능성이 있다.  
`AuditFollowup0418` 실표본 확인 시 **API 오류 여부와 모델명 교정 필요성**을 함께 점검해야 한다.

### 5-1) 감사 필드 이식 — **정확**

| 항목 | Gemini (`ai_engine.py:1374`) | OpenAI (`ai_engine_openai_v2.py:695`) |
|---|---|---|
| 감사 필드 주입 | `result.update(build_scalping_feature_audit_fields(...))` | `result.update(build_scalping_feature_audit_fields(features))` |
| 공통 helper | ✅ `scalping_feature_packet.py` | ✅ `scalping_feature_packet.py` |
| `4개 *_sent + packet_version` 포함 | ✅ | ✅ |

- `scalp_feature_packet_version` 1개와 `tick_acceleration_ratio_sent`, `same_price_buy_absorption_sent`, `large_sell_print_detected_sent`, `ask_depth_ratio_sent` 4개가 양쪽 동일하게 주입된다.

### 5-2) 프롬프트 내 정량 피처 노출 — **OpenAI가 더 풍부 (비대칭)**

**Gemini** `[정량형 수급 피처]` 섹션 (`ai_engine.py:1172~1183`) — **10개 필드**:

```
packet_version, buy_pressure_10t, distance_from_day_high_pct, intraday_range_pct,
tick_acceleration_ratio, same_price_buy_absorption, large_sell_print_detected,
net_aggressive_delta_10t, ask_depth_ratio, net_ask_depth
```

**OpenAI** `[정량 피처]` 섹션 (`ai_engine_openai_v2.py:453~480`) — **27개 필드**:

위 10개 + `spread_krw`, `spread_bp`, `top1_depth_ratio`, `top3_depth_ratio`, `total_depth_ratio`,
`micro_price`, `microprice_edge_bp`, `price_change_10t_pct`, `recent_5tick_seconds`,
`prev_5tick_seconds`, `large_buy_print_detected`, `volume_ratio_pct`,
`curr_vs_micro_vwap_bp`, `curr_vs_ma5_bp`, `micro_vwap_value`, `ma5_value`, `latest_strength`

> **판정**: `프롬프트에 텍스트로 노출되는 필드 수`는 OpenAI가 더 많다. 다만 이것을 곧바로 `작업 9 이식 실패`로 해석하면 과하다.  
> 현재 핵심 이식 포인트였던 `공통 helper 공유`와 `메인 OpenAI 감사 필드 주입`은 정상이다.  
> 별도 후속축으로 보면, Gemini `_format_market_data()` 의 `[정량형 수급 피처]` 섹션은 OpenAI 수준으로 확장할 여지가 있다.

### 5-3) `extract_scalping_feature_packet()` 이중 호출 — **비효율, 정확성 무해**

`ai_engine_openai_v2.py` `analyze_target()` 내에서:

- **Line 649**: `features = self._extract_scalping_features(ws_data, recent_ticks, recent_candles)`
- **Line 650**: `formatted_data = self._format_market_data(...)` → 내부 **Line 343**에서 `self._extract_scalping_features()` 재호출

동일 `ws_data`에 대해 패킷 계산이 2회 발생한다. 버그는 아니나 중복 계산이다.  
→ `_format_market_data(features=None)` 형태로 시그니처를 확장하거나, `_format_market_data()` 내부 자체 호출을 제거하고 외부에서 주입하는 방식으로 개선 가능.

### 5-4) 사후 보정 로직 비대칭 — **의도 확인 필요**

| 엔진 | 사후 보정 방식 |
|---|---|
| Gemini | `_apply_remote_entry_guard()` — feature 기반 BUY 억제 (risk_flags ≥ 임계) |
| OpenAI | `_apply_main_entry_bias_relief()` + `_should_run_deep_recheck()` — 경계구간 deep 재판정 |

두 엔진이 서로 다른 철학으로 동작 중. 의도된 설계 분기라면 문서화 권장.

### 5-5) 실측 종합 판정

| 점검 항목 | 결과 |
|---|---|
| 감사 필드 주입 이식 | ✅ 정확 |
| 공통 helper 공유 | ✅ 정확 |
| 메인 런타임 OpenAI 라우팅 | ⚠️ 조건부 (`openai_scalping_engine != None`) |
| OpenAI 프롬프트 정량 피처 포함 | ✅ 풍부 (27개) |
| Gemini 프롬프트 정량 피처 확장 여지 | ⚠️ 존재 (현재 10개 노출) |
| 이중 호출 비효율 | ⚠️ 존재 (정확성 영향 없음) |
| 사후 보정 로직 일관성 | ℹ️ 의도 확인 필요 |

---

## 6) 참고 문서

- [2026-04-18-stage2-todo-checklist.md](./2026-04-18-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
