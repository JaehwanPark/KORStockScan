# 보유 AI 프롬프트·입력·해시·호출 주기 실행 점검 — 2026-09-25

## 결정

[실행계획](../proposals/holding-ai-prompt-input-hash-cadence-audit-plan-2026-09-25.md)의 코드 계약과 합성 검증은 보완했다. **호출 빈도 변경·배포·자연 모델 품질 수용은 하지 않았다.** 자연 `holding_path_votes` 원장이 없고 작업 셸에 OpenAI 키가 없으며 실행 중인 `kiwoom_sniper_v2` PID도 확인되지 않았다. 따라서 실제 PID의 응답 모델, v10 프롬프트의 지연 분포·timeout율, 경로×시장별 신호 전 정족수 성숙률과 비용 후 효과는 아직 증명되지 않는다. `gpt-5.4-nano` 사용은 현재 작업트리의 설정·요청 제한 및 응답 모델 검증 **코드 계약**으로만 확인했다.

2026-09-25 일일 checklist가 없어 당일 실행 소유자를 확인할 수 없다. 작업트리는 이전 청산·투표 구현을 포함해 광범위하게 미커밋이고 이 문서 역시 배포/PID 영수증이 아니다. 구 실거래 정책·주문·봇·threshold·호출 예산은 변경하지 않았다.

## 호출 census와 프롬프트 결과

| 경로 | 요청 전제/결정 목적 | 입력 확인 및 결과 |
| --- | --- | --- |
| `EXIT_TRAILING_TP` | Main SCALPING 보유 중 기본 요청; 기존 기계식 익절 SELL에 대한 PASS/VETO | 고점 되돌림, 실행 가능 bid와 비용 후 청산 수익, 테이프·flow를 명시했다. 청산 가능 순수익/호가/틱 또는 원천 preflight가 빠지면 공급자 요청 전에 경로별 결손으로 격리한다. |
| `EXIT_SOFT_STOP` | Main SCALPING 보유 중 기본 요청; 기존 soft-stop SELL | 실행 가능 청산 수익·손실 악화와 회복 증거의 방향을 별도 명시했다. 강제 손절/보호는 외부 안전 소유자다. |
| `EXIT_POST_ADD_FAIL` | `POST_ADD_EVAL` 중 조건부 요청; 추가매수 후 실패 SELL | 실제 추가매수 체결량·시각·상태를 요구한다. 제출만 되고 체결되지 않은 ADD를 판정 근거로 쓰지 않는다. 짧은 평가창에서 기본 20초 최소 간격으로 2표를 모을 수 있는지는 자연 시각 자료가 없어 미확정이다. |
| `EXIT_BAD_ENTRY_REFINED` | canary 조건부 요청; bad-entry SELL | `never_green` 또는 MAE 및 현재 시세를 요구하며 진입 당시 지지를 현재 지지로 쓰지 않도록 명시했다. |
| `ADD_REBOUND` | 기계식 rebound ADD가 가능할 때 조건부 요청 | 분봉·테이프·호가 flow를 요구한다. PASS는 ADD 후보만 통과시키고 SELL 허용 표와 혼용하지 않는다. |

활성 Main 경로의 공급자 호출은 `sniper_state_handlers._collect_holding_path_votes` 한 곳이다. 구 점수 재호출 `_retry_holding_ai_submit_authority_before_block`의 호출자는 미호출 `_evaluate_first_touch_avgdown_decision_gate` 안에 있고, `_evaluate_holding_flow_override`와 `_opening_rotation_holding_ai_once`도 현재 코드 검색상 호출자가 없다. `entry_context_intraday_probe`·`avg_down_policy_replay`는 오프라인이고 `sniper_overnight_gatekeeper`는 별도 overnight 코드다. 이는 **정적 호출 census**이며 실제 PID trace에 대한 결론은 아니다.

한 English ASCII 공통 프롬프트가 요청된 각 경로에 한 표를 반환한다. v10에서는 다섯 경로의 판단 근거와 PASS/VETO 방향을 분리하고, 기존 schema의 한 경로당 한 표·근거 접두사·`input_insufficient` 격리를 유지했다. 세 시장×다섯 경로의 입력 구조 fixture를 통과했다. 실제 모델의 경로별 판정 정확도는 자연·독립 라벨이 없어 검증하지 못했다.

## 구현·리뷰에서 확인한 결함과 수리

1. v9 프롬프트 입력은 `best_bid_qty`·`best_ask_qty`를 요청했으나 `_extract_quote_snapshot`이 만들지 않아 두 값이 항상 null이었다. v10은 기존 시세 영수증의 최우선 매수/매도 가격과 실제 수집된 양쪽 총 호가 잔량을 보낸다. flow의 별도 최우선 잔량과 가격이 충돌하면 경로별 입력 결손으로 처리한다. Kiwoom 요청/파서/FID는 변경하지 않았다.
2. 호출 전 중복 차단이 시세 세대만 보던 상태에서 실제 전송 JSON 해시, 실질 판단 입력 해시, path별 판단 입력 해시로 나눴다. 단순 시세 관측 시각·raw snapshot capture clock·age 갱신만으로 새 표를 만들지 않는다. 변경된 path만 한 요청에 묶고, 동일 입력은 공급자 호출을 건너뛴다. 같은 시세 세대를 다시 검토해도 실패 표를 인위적으로 넣지 않는다. 신선한 독립 generation, BUY 체결 세대, 시장, 원천 preflight는 계속 요구한다.
3. path별 마지막 호출 입력은 포지션별 `*.claims.jsonl`에 공급자 호출 **전** 원자적으로 선점·fsync한다. 재시작·동시 접근 후에도 같은 path 입력으로 이중 호출하지 않는다. 공급자를 실제 호출하지 않은 정상 결과는 정확한 claim만 해제한다. 응답 실패·timeout 또는 호출 여부가 불명확하면 보수적으로 claim을 유지한다. `unchanged_input_skip`은 과거 표의 시각이나 정족수를 늘리지 않는다.
4. `OPENAI_HOLDING_EXIT_VOTE_MODEL`을 명시적으로 `gpt-5.4-nano`로 설정했다. 요청이 다른 모델이면 호출 전 차단하고, Responses SDK의 전송 메타데이터에 기록된 실제 `model`과 HTTP 경로가 nano alias 또는 문서화된 날짜 snapshot인지 확인한다. 모델 출력 JSON이 같은 이름의 필드를 위조해도 유효 표가 되지 않으며, 이전 호출의 전송 메타데이터는 새 호출 전에 제거한다. 응답 모델 결손·불일치는 유효 표에서 제외한다. [공식 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.4-nano)는 nano의 Responses/structured outputs와 `gpt-5.4-nano-2026-03-17` snapshot을 열거한다. 문서 지원 여부는 운영 PID 사용 증거가 아니다.
5. 구 점수 timeout과 공유하던 필드를 분리해 `OPENAI_HOLDING_EXIT_VOTE_TIMEOUT_MS=7000`을 전용 설정으로 뒀다. deadline 뒤 응답, 잘못된 모델/전송, 입력 해시 경합은 `INSUFFICIENT`다. 리뷰 시각·예약·실제 호출·유효 표 저장 시각과 tick/candle/quote/preflight/context/engine/원장 시간을 구분해 기록한다.
6. 리뷰 중 상수 로더의 기존 미선언 `SCALP_TRAILING_LIMIT_*` 환경값 교체 결함을 발견했다. 한때 필드 선언으로 고쳤으나 이는 이번 범위를 넘어 트레일링 임계치 적용 권한을 바꿀 수 있어 **되돌렸다**. 관련 구 테스트 실패는 별도 기존 결함으로 남겼다.

## 성능·주기 실험

현재 작업 셸의 effective 값은 일반 최소/최대 **45/180초**, 임계 구간 **20/45초**, 종목별 전체 **4회/60초**, 보유 투표 그룹 **2회/60초**, vote timeout **7초**다. 실제 PID 값은 미확인이다. `gpt-5.4-nano`가 빠르고 저렴하다는 일반 모델 설명만으로 간격을 줄이지 않았다.

300회·두 경로의 합성 해시 계산 + 마지막 claim 읽기 + durable claim 쓰기: **p50 3.910ms, p95 4.922ms, p99 6.918ms, 최대 9.692ms**, claim 파일 100,200 bytes, 프로세스 최대 RSS 18,056 KiB. 이 수치는 원천 REST 조회·공급자 지연·실제 전체 리뷰 루프를 포함하지 않는다.

기본 공유 예산을 유지하고 **5초마다 실질 입력이 바뀌며 공급자 완료에 3초가 걸린다는 합성 가정**에서 60초당 보유 호출은 최대 두 번이다. 5초 최소 간격은 t=0·5초 표가 8초 최소 관측 지속시간을 못 채워 t=15초 신호에서 불충분했고, t=50초에는 최근 표가 45초 전이라 40초 최신성도 실패했다. 10초 간격은 같은 가정의 t=15·50초에서 모두 정족수를 채웠다. 입력이 30초마다 바뀌면 5/10/20초 후보 모두 t=0·30초 호출로 같았고, 입력이 안 바뀌면 어떤 후보도 1표를 넘지 못했다. 이는 호출 예산·정족수의 **기계적 설명용 합성 결과**이며 세 시장의 실제 최적 주기나 EV가 아니다. [OpenAI 지연 가이드](https://developers.openai.com/api/docs/guides/latency-optimization)는 입력/출력 토큰, 요청 수 등 전체 경로를 함께 줄이도록 안내한다.

## 검증과 남은 수용

- 코드 리뷰→수정→재리뷰에서 path별 입력 결손, 중복 generation, 해시/claim 경합, SDK 응답 모델·위조된 출력 필드·늦은 응답, 범위 밖 threshold authority를 점검했다. 최종 대상 suite **1,158건 통과**, Python compile, `git diff --check`, 16개 동시 claim 중 1개만 성공하는 회귀를 확인했다.
- 전체 `test_constants.py` 포함 첫 확장 실행은 기존 미선언 트레일링 필드로 13 실패·11 teardown 오류였다. 범위 밖 임계치 권한 변경을 되돌린 상태에서 보유 AI 전용 상수 테스트를 포함한 대상 1,158건은 통과했다. 전체 구 상수 suite의 퇴역/legacy 환경변수 기대는 이번 변경의 수용 근거로 사용하지 않는다.
- 자연 v10 원장, 독립 날짜별 경로×시장 모델 응답 품질, 실제 키를 이용한 v10 p95/p99·timeout율, 실제 PID 모델 소비, 공유 예산에서 다른 entry AI 영향, 비용 후 완료 포지션 paired EV는 **미확인**이다. 셸에는 OpenAI API 키가 없어 공급자 요청을 실행하지 않았다. 작업 날짜의 당일 checklist와 배포 release/PID 영수증도 없다.
- 다음 수용은 유효한 실행 소유자·immutable release/PID를 확인한 뒤, 주문 없이 자연 입력/호출 funnel을 모아 `검토→입력 적격→해시 변화→예산→요청→정시 응답→유효 표→첫 신호 전 정족수`와 p99·비용을 시장×경로별로 대사하는 것이다. 그때에만 후보 간격/예산 변경과 경제성 판단을 별도로 결정한다. 현재 baseline 주기와 공유 예산은 유지한다.
