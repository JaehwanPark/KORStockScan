# Entry setup family/state 원천 결함 보완 계획

## 1. 목적·범위

사용자 「다음액션 실행하라」에 따라 [선행 리뷰§7](../audits/samsung-premarket-confirmation-component-research-review-2026-10-04.md)의 producer 정합성 수리와 별도 역사 복구 증빙을 실행한다. 소유자는 `src/engine/scalping/entry_setup_evidence.py`의 패턴 증거 생성기와 `ai_action_outcome_calibration.py`의 오프라인 machine archive 소비자다. 새 helper는 같은 scalping 패키지에 두고 engine root/실시간 프로토콜을 추가하지 않는다.

원archive, 기존 projection, 기존 연구 generation, 정책·PREOPEN 원본은 덮어쓰지 않는다. 선행 receipt의 180개 seal 중 이번에 승인된 코드 변경만 before snapshot/old-new ledger로 기록하고 나머지 원천 및 98개 정책·handoff를 보존한다. 과거 코드 검증 receipt를 현재 코드의 PASS로 재사용하지 않는다.

## 2. 결함과 수리 계약

- 10/2 08:33:18.566416 삼성전자 장전 canonical capture는 hash 정상이나 `NO_VALID_SETUP / WAIT_CONFIRMATION`으로 `entry_setup_family_state_inconsistent`에 탈락했다.
- local-breakout 확인 요청은 패턴 family를 성립시키지 않는다. `NO_VALID_SETUP`은 `UNCONFIRMED / SETUP_DISCOVERY_RECHECK`, `MICRO_RECOVERY`는 기존 단일 `MICRO_PRICE_RESPONSE_RECHECK` grammar를 유지한다. 지원 family는 `WAIT_CONFIRMATION / TRIGGER_CONFIRMATION_RECHECK`를 유지한다.
- machine 판정의 hard BLOCK 우선순위와 `local_breakout_confirmation_required` RECHECK를 보존한다. 검증기를 느슨하게 하거나 임계값을 변경하지 않는다.
- 역사 복구는 위 단일 family/state 오류만 가진 원본에 한정한다. 원canonical/raw/원bundle의 exact scope parent/current kernel/source file hash를 묶어 재계산하고, 새 evidence 검증 정상·원판정 RECHECK 불변을 증명한다. 추가 오류, 식별·parent·hash 충돌, ENTER 승격은 거부한다.
- 별도 repair receipt는 uncached 오프라인 소비자의 명시적 인자로만 사용한다. 기본 장후 loader 및 기존 cache의 원천 인정 규칙을 자동 변경하지 않는다. 복구 row에는 원오류·receipt hash를 남기고 원trace/watch/attempt/route/cost를 유지한다.
- 부분군을 intake할 때 전체 관측용 기존 가격 cache의 manifest가 달라지는 효과를 실제 원천 결손으로 해석하지 않는다. 원전체 canonical 유효분모를 재현하고 기존 cache owner 검증을 통과한 배치에서 exact symbol/venue/session/request-code 가격만 가져오는 CLI 전용 report-only adapter로 비교한다. 원cache를 재봉인하지 않으며 새로운 population의 운영 cache 증빙으로 취급하지 않는다. 원capture 비용 null과 기존 장후 경제성 원천으로 계산한 source-bound 비용을 분리한다.

## 3. 순서와 유한 종료 기준

1. 선행 seal과 정책·10/3 dirty/10/6 checklist hash 검증, 승인 코드 before 보관.
2. producer 수정, unsupported/micro/supported/invalid/insufficient 회귀 및 엄격한 validator 유지.
3. 별도 receipt 생성·검증과 명시적 오프라인 소비 경로 구현; 변조·scope·kernel·추가 오류·판정 승격 거부 회귀.
4. 리뷰→보완→재리뷰→표적 pytest/compile/diff 통과 후 보유9/29·9/30·10/2의 삼성전자 장전 6개를 격리 intake한다. 기본5개와 복구포함6개를 대조하며 기존5개 내용 불변·원watch2개 불변·복구관측의 source-bound 비용/가격 결과와 실현 경제성 미입증 여부를 확인한다.
5. 별도 cold/warm receipt·소비 결과 일치, 미변경 seal/hash 검증, 문서 링크·현재 owner·print-only parser로 닫는다. 수리 결과 및 남은 source/성과 결손을 audit에 기록한다.

종료는 producer/receipt/마지막 archive consumer의 인과·정합성 검증 완료다. 복구관측1개를 독립 기회나 새로운 수익/정책 후보로 세지 않는다. 과거 결손 경제성을 0으로 채우거나 실현 손익을 추정하지 않는다.

## 4. 권한·후속

이번 작업은 코드 보완·리뷰 및 보유 원천의 격리 재생이다. 정책 발행·배포·재기동·주문·API/provider 호출·수집 확대·전장후 자동화·외부 sync는 실행하지 않는다. 기존10/6 `SamsungFrozenCandidateValidation1006`과 PREOPEN/자연 수용 owner를 확대하지 않는다. 성공100%/80% 보존 veto를 도입하지 않는다.

결과: [실행 리뷰](../audits/entry-setup-family-state-source-repair-review-2026-10-04.md). 현재 실행 소유자는 [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `EntrySetupSourceRepair1004`다.
