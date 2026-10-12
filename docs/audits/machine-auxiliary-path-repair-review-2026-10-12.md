# 기계·보조판정 연결 결함 보완 — 2026-10-12

## 범위와 원천

사용자의 기계/보조판정 결함 보완·반복 리뷰·배포·재기동 승인을 따른다. 기계 정책, 보조 프롬프트, 5초 신호 기한, 보호조건, 수량, 주문 및 Main/manual 소유권은 보존한다. 실제 주문을 검증 목적으로 발생시키지 않는다.

점검 시작 시 selected release는 `nonfixed-dispatch-readiness-repair-20261012-v2`, PID `644191`, start ticks `1977854`였다. 원천은 오늘 `ai_decision_trace`, `ai_decision_payloads`, 정확 요청 ID의 `pipeline_events`이다. 이전 PID의 결과와 합치지 않았다.

- 주성 `analyze_target:036930:1791770768190:366f6a9f`: AI PASS와 Main `commit_allowed`가 관측됐다. 이후 `real_weak_pullback_entry_block` 및 반복 `latency_block`이 있었다. 11:13 무렵까지 읽은 제한 구간에서 같은 요청에 `budget_pass` 15회와 `ai_confirmed_terminal_no_budget` 35회가 있었으며, 35개 독립 주문 실패가 아니다.
- 주성 `analyze_target:036930:1791770761909:89bdbc8a`, HPSP `analyze_target:403870:1791770808841:ee494cff`: 모델 PASS가 `response_invalid`로 정규화됐으나 공통 trace에 구체적 contract errors가 누락됐다. 당시 정확한 거부 이유를 새로 만들어 내거나 정상 PASS로 재분류하지 않는다.
- 실제 transport timeout도 별도로 관측됐다. 정책 조회 준비 시간은 약 66~356ms였으며 provider 잠금 대기는 0ms였다. 거부·시간초과·보호조건 차단을 서로 구분한다.

## 수정과 재검토

1. `sniper_state_handlers`: 원래 기한이 지난 native 기계/AI 응답으로 오래된 entry arm을 재사용하지 않는다. 새로운 native claim 탐색이 먼저 수행되고, 새 claim이 없으면 이전 PASS를 다시 제출 검사에 사용하지 않는다. 원래 시각·attempt/trace ID·결과·cooldown을 덮어쓰지 않는다. 비native 기존 경로 및 새 응답 소비 경계는 보존한다.
2. `entry_setup_live_policy`: 매 조회에서 전체 정책 그래프를 복제하는 대신, native loader가 모든 원천 의존성을 검증한 불변 정책을 참조한다. 요청별 결과 envelope와 assessment만 소유하며 기존 검증·원천 변경 감지는 유지한다.
3. `ai_decision_trace`: native 보조판정의 contract valid/errors를 trace와 pending 결과에 보존한다. legacy adapter가 없는 실제 continuous-reversal 경로도 포함한다. 추가 필드에도 기존 비밀정보 제거를 적용한다.
4. `intraday_release_handoff`, bootstrap 및 delay/holding reader: 공통 진입 파일 수정으로 기존 제출지연·보유 incumbent 정책이 무효 처리되던 코드 해시 연계를 보완한다. 최초 v1 배포 전 인계 검사는 이 문제로 실패했고 selector를 정확히 원복했으며 기존 PID는 계속 가동했다. 원 PREOPEN 정책/코드 commit과 실제 predecessor 소비·PID를 검증하고, 인계 후에는 native handoff를 검증한다. 정책에 포함된 모든 Git 파일과 현재 불변 release를 대조한다. 변경 허용은 검토한 WATCHING/arm 및 호환성 검증 함수이며, 그 밖의 AST와 producer·projection·selector는 동일해야 한다. holding은 기존 incumbent carry만 허용하고 numerical successor 비교에는 전체 코드 일치를 요구한다. 새 발행/연구의 전체 코드 해시는 유지한다. 원천·권한 결손, 다른 함수 변경 및 dirty release는 차단한다.

첫 테스트의 새 신호 fixture에서 정책 family가 비어 있던 문제를 수정했고, 실제 v6 새 claim 회귀도 추가했다. 리뷰에서 비native 경로의 불필요한 대기를 막도록 적용 범위를 좁혔다. trace의 뒤늦게 추가되는 필드가 sanitizer 이후 덮어쓰지 않도록 추가 보완했다.

## 검증과 적용 증거

- 정책 조회 동일 입력 비교: 현재 bundle `f7c1454a71b284a25c40a157ea4f42f390ecc5c21f362d76f497c49bf41ec2b1`, 3회 교대 × arm별 15회. 기존 중앙값 34.26/35.15/35.14ms, 변경 12.37/12.34/12.43ms. 같은 정책 출력과 원천 검증을 유지한다. 전체 AI/주문 경로 성능 또는 수익 개선을 입증하는 수치는 아니다.
- targeted pytest, compile, diff 및 checklist print-only parser를 수행한다. 배포/재기동 완료는 아래 완료 영수증의 실제 상태로 판정한다.
- [범위별 원천·성능·테스트·배포 영수증](../../tmp/machine-auxiliary-path-repair-20261012/) / [완료 영수증](../../tmp/machine-auxiliary-path-repair-20261012/completion.json).

기존 장후 compact auxiliary 연구 OPEN owner를 완료 처리하지 않는다. 경제성·실제 주문·모든 시점의 AI 시간초과 해소는 별도 근거 없이 주장하지 않는다.
