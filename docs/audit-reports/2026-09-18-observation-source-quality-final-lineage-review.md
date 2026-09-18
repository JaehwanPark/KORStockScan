# Observation source-quality final lineage 구현 리뷰

대상 source: 2026-09-17. Publication: 2026-09-18. Prepared effective: 2026-09-21. 사용자 승인 범위는 Q0–Q5 구현/반복 리뷰/제한 재생성/commit/push/immutable 배포이며 조기 PREOPEN·주문·bot restart·guard/env/provider 변경은 실행하지 않는다.

## 구조 결손과 수리

- 기존 retry 경로가 신뢰된 machine evaluation provenance를 stock/call context에 재결속하지 않았다. 현재 평가 identity만 기록하며 원 call parent와 다른 새 평가를 섞지 않는다. 통합 route는 execution venue 확정으로 쓰지 않는다.
- 불명확 leg dispatch·registry reconciliation·예외는 pending, 동일 call의 상충 terminal은 exact gap으로 유지한다. 실제 later ACK만 동일 call/tag로 pending을 해소한다. 서로 다른 call의 guard→retry submit은 상충으로 오인하지 않는다.
- Raw aggregate는 관측 stage의 AST 의미·원 receipt/code/body/generation을 검증해 재사용한다. Final은 별도로 machine/AI/provider/funnel을 읽고 content/implementation/phase를 결속한다. Pure reusable check와 wrapper/trigger/strict가 preflight 또는 stale binding을 거절한다.
- Source 허용·CF 입력·운영 terminal·완료 비용 경제성을 분리했다. 무관한 PASS gap은 유효 VETO/BLOCK CF를 전역 차단하지 않는다. 비용 후 EV 및 comparison eligible은 evaluator 증거 없이는 null/false다.
- Unknown 28 stage warning은 제거하지 않고 동일 native workorder에 field count/rate/producer/disposition/closure test를 남긴다. 사전 scanner의 실제 execution venue 부재는 정상 unavailable이다. 불명확 producer는 추정하지 않는다.

## Q0 원천 대사

PASS4의 exact evaluation/promotion/bundle key는 기존 funnel과 `tmp/observation-source-quality-20260918/q0-gap-source-generation.json`에 있다. 마지막 증명 사건은 `pre_submit_entry_ai_authority_retry`의 ai_confirmed이며 4 key/5 사건이다. Signed registry에서 exact ID 증거를 찾지 못했다. 현재 terminal 미복구 4개를 no-submit/순익0으로 바꾸지 않는다. 미래 capture 수리와 과거 복구는 별도다.

Machine capture4508 중 exact trace4507·미연결1(snapshot aims-53d448364dcc3f943eec, RECHECK)은 `q0-machine-trace-identity.json`에 보존한다. Entry-screen capture/trace publication 사이 부재로 남으며 원 예외 receipt가 없어 세부 원인을 확정하지 않는다. Health companion present993/missing3585는 optional diagnostic이며 필수 economic gate로 쓰지 않는다.

## 리뷰와 제한 검증

초기 리뷰에서 distinct-call retry를 terminal conflict로 오인하는 조건, lossless cache의 leg stage 누락, 이후 retry가 이전 machine identity를 빌리는 경우, final consumer gate의 운영/economic 혼용을 수정했다. 원 raw stage census가 새 stage0임을 증명할 때만 기존 cache schema의 lossless population 이관이 허용된다. 대형 funnel은 native gate section과 전체 byte hash만 streaming으로 읽고 archive census도 필요 field projection만 유지한다.

최종 검증/재생성/선택 receipt는 `tmp/observation-source-quality-20260918/` 아래에 기록한다. 기존 원 audit/funnel은 `original/`, raw/signed ledger 보호 기준은 `protected-source-before.json`이다. Source tests488 PASS, wrapper126 PASS 및 실제 retry/late/ambiguous 추가 회귀를 통과했다. 마지막 source 변경 관련 회귀·parser/compile/bash/diff 확인을 추가한다.

## 마지막 소비·배포와 잔여 경계

Final audit→workorder/EV/runtime summary→tower/checklist→strict/controller→compact dated carry를 같은 원 source에서 갱신한다. 이 단계의 실행 receipt와 global strict의 외부 blocker를 별도로 기록한다. Whole native DONE, 정책의 실제 PREOPEN/PID 소비, 양수 ΔEV 및 실현순익은 별도 증거가 필요하다. 자연 정상 PASS의 exact terminal/COMPLETED costs와 미사용 holdout의 경제성은 기존 checklist Acceptance로 OPEN이다.
